"""
Excel Processing Performance Monitor and Profiler
================================================

This module provides comprehensive performance monitoring and profiling
capabilities for Excel processing operations.

Features:
- Real-time performance monitoring
- Memory usage tracking and alerts
- Processing time profiling
- Throughput analysis
- Resource utilization monitoring
- Performance report generation
- Bottleneck identification
- Historical performance tracking

Usage:
    # Basic monitoring
    with ExcelPerformanceMonitor() as monitor:
        # Process Excel files
        pass

    # Get performance report
    report = monitor.generate_report()

    # Advanced monitoring with custom metrics
    monitor = ExcelPerformanceMonitor(
        track_memory=True,
        track_cpu=True,
        alert_thresholds={'memory_mb': 1024, 'processing_time_s': 30}
    )
"""

import os
import time
import logging
import threading
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import psutil
import json
import pickle
from datetime import datetime, timedelta
import statistics
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance measurement"""
    timestamp: float
    memory_rss_mb: float
    memory_vms_mb: float
    cpu_percent: float
    threads_count: int
    file_handles: int
    processing_active: bool = False
    current_operation: str = ""


@dataclass
class ProcessingEvent:
    """Record of a single processing event"""
    event_id: str
    operation_type: str
    file_path: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    file_size_mb: float = 0.0
    rows_processed: int = 0
    memory_peak_mb: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def duration_seconds(self) -> float:
        """Get event duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def processing_rate_rows_per_second(self) -> float:
        """Get processing rate in rows per second"""
        duration = self.duration_seconds()
        if duration > 0 and self.rows_processed > 0:
            return self.rows_processed / duration
        return 0.0


@dataclass
class AlertConfig:
    """Configuration for performance alerts"""
    memory_mb_threshold: float = 2048.0
    processing_time_s_threshold: float = 60.0
    cpu_percent_threshold: float = 95.0
    error_rate_threshold: float = 0.2
    memory_growth_mb_threshold: float = 500.0
    enable_email_alerts: bool = False
    enable_log_alerts: bool = True


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    report_id: str
    generation_time: datetime
    monitoring_duration_hours: float

    # Summary statistics
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_files_processed: int
    total_rows_processed: int

    # Timing statistics
    avg_processing_time_s: float
    median_processing_time_s: float
    max_processing_time_s: float
    total_processing_time_s: float

    # Memory statistics
    peak_memory_mb: float
    avg_memory_mb: float
    max_memory_growth_mb: float

    # Throughput statistics
    avg_throughput_files_per_hour: float
    avg_throughput_rows_per_second: float

    # Error analysis
    error_rate: float
    common_errors: Dict[str, int] = field(default_factory=dict)

    # Performance trends
    performance_trend: str = "stable"  # improving, stable, degrading
    bottlenecks_identified: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ExcelPerformanceMonitor:
    """Comprehensive performance monitor for Excel processing"""

    def __init__(
        self,
        track_memory: bool = True,
        track_cpu: bool = True,
        track_file_handles: bool = True,
        monitoring_interval_s: float = 1.0,
        alert_config: Optional[AlertConfig] = None,
        max_snapshots: int = 1000,
        enable_detailed_logging: bool = False
    ):
        self.track_memory = track_memory
        self.track_cpu = track_cpu
        self.track_file_handles = track_file_handles
        self.monitoring_interval_s = monitoring_interval_s
        self.alert_config = alert_config or AlertConfig()
        self.max_snapshots = max_snapshots
        self.enable_detailed_logging = enable_detailed_logging

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.start_time = None
        self.stop_event = threading.Event()

        # Data storage
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.processing_events: List[ProcessingEvent] = []
        self.alerts_triggered: List[Dict[str, Any]] = []

        # Current state tracking
        self.current_operations: Dict[str, ProcessingEvent] = {}
        self.baseline_memory_mb = 0.0

        # Performance caches
        self._cached_reports: Dict[str, PerformanceReport] = {}

    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()

    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return

        self.start_time = time.time()
        self.baseline_memory_mb = self._get_memory_usage()
        self.monitoring_active = True
        self.stop_event.clear()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Excel performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        self.stop_event.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        logger.info("Excel performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active and not self.stop_event.wait(self.monitoring_interval_s):
            try:
                snapshot = self._capture_snapshot()
                self.snapshots.append(snapshot)

                # Check for alerts
                self._check_alerts(snapshot)

                # Detailed logging if enabled
                if self.enable_detailed_logging:
                    self._log_snapshot(snapshot)

            except Exception as e:
                logger.debug(f"Error in monitoring loop: {e}")

    def _capture_snapshot(self) -> PerformanceSnapshot:
        """Capture current performance snapshot"""
        process = psutil.Process()

        # Memory information
        memory_info = process.memory_info()
        memory_rss_mb = memory_info.rss / 1024 / 1024
        memory_vms_mb = memory_info.vms / 1024 / 1024

        # CPU usage (if tracking enabled)
        cpu_percent = process.cpu_percent() if self.track_cpu else 0.0

        # Thread count
        threads_count = process.num_threads()

        # File handles (if tracking enabled)
        try:
            file_handles = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            file_handles = 0

        # Current processing state
        processing_active = len(self.current_operations) > 0
        current_operation = ", ".join(self.current_operations.keys()) if processing_active else ""

        return PerformanceSnapshot(
            timestamp=time.time(),
            memory_rss_mb=memory_rss_mb,
            memory_vms_mb=memory_vms_mb,
            cpu_percent=cpu_percent,
            threads_count=threads_count,
            file_handles=file_handles,
            processing_active=processing_active,
            current_operation=current_operation
        )

    def _check_alerts(self, snapshot: PerformanceSnapshot):
        """Check for alert conditions"""
        alerts = []

        # Memory threshold
        if snapshot.memory_rss_mb > self.alert_config.memory_mb_threshold:
            alerts.append({
                'type': 'memory_threshold',
                'message': f"Memory usage ({snapshot.memory_rss_mb:.0f}MB) exceeds threshold ({self.alert_config.memory_mb_threshold:.0f}MB)",
                'severity': 'warning',
                'timestamp': snapshot.timestamp,
                'value': snapshot.memory_rss_mb
            })

        # CPU threshold
        if snapshot.cpu_percent > self.alert_config.cpu_percent_threshold:
            alerts.append({
                'type': 'cpu_threshold',
                'message': f"CPU usage ({snapshot.cpu_percent:.1f}%) exceeds threshold ({self.alert_config.cpu_percent_threshold:.1f}%)",
                'severity': 'warning',
                'timestamp': snapshot.timestamp,
                'value': snapshot.cpu_percent
            })

        # Memory growth check
        memory_growth = snapshot.memory_rss_mb - self.baseline_memory_mb
        if memory_growth > self.alert_config.memory_growth_mb_threshold:
            alerts.append({
                'type': 'memory_growth',
                'message': f"Memory growth ({memory_growth:.0f}MB) exceeds threshold ({self.alert_config.memory_growth_mb_threshold:.0f}MB)",
                'severity': 'warning',
                'timestamp': snapshot.timestamp,
                'value': memory_growth
            })

        # Process alerts
        for alert in alerts:
            self.alerts_triggered.append(alert)

            if self.alert_config.enable_log_alerts:
                logger.warning(f"Performance Alert: {alert['message']}")

    def _log_snapshot(self, snapshot: PerformanceSnapshot):
        """Log detailed snapshot information"""
        logger.debug(
            f"Performance Snapshot: "
            f"Memory: {snapshot.memory_rss_mb:.0f}MB, "
            f"CPU: {snapshot.cpu_percent:.1f}%, "
            f"Threads: {snapshot.threads_count}, "
            f"Active: {snapshot.processing_active}"
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return psutil.Process().memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def start_operation(
        self,
        operation_id: str,
        operation_type: str,
        file_path: str,
        file_size_mb: float = 0.0
    ) -> ProcessingEvent:
        """Start tracking a processing operation"""
        event = ProcessingEvent(
            event_id=operation_id,
            operation_type=operation_type,
            file_path=file_path,
            start_time=time.time(),
            file_size_mb=file_size_mb
        )

        self.current_operations[operation_id] = event

        if self.enable_detailed_logging:
            logger.debug(f"Started operation {operation_id}: {operation_type} on {os.path.basename(file_path)}")

        return event

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        rows_processed: int = 0,
        cache_hits: int = 0,
        cache_misses: int = 0
    ):
        """End tracking a processing operation"""
        if operation_id not in self.current_operations:
            logger.warning(f"Attempted to end unknown operation: {operation_id}")
            return

        event = self.current_operations.pop(operation_id)
        event.end_time = time.time()
        event.success = success
        event.error_message = error_message
        event.rows_processed = rows_processed
        event.cache_hits = cache_hits
        event.cache_misses = cache_misses
        event.memory_peak_mb = self._get_memory_usage()

        self.processing_events.append(event)

        if self.enable_detailed_logging:
            duration = event.duration_seconds()
            status = "succeeded" if success else "failed"
            logger.debug(
                f"Completed operation {operation_id}: {status} in {duration:.2f}s, "
                f"processed {rows_processed} rows"
            )

        # Check for long-running operation alert
        if event.duration_seconds() > self.alert_config.processing_time_s_threshold:
            self.alerts_triggered.append({
                'type': 'long_operation',
                'message': f"Operation {operation_id} took {event.duration_seconds():.1f}s (threshold: {self.alert_config.processing_time_s_threshold:.1f}s)",
                'severity': 'warning',
                'timestamp': event.end_time,
                'value': event.duration_seconds()
            })

    @contextmanager
    def track_operation(
        self,
        operation_type: str,
        file_path: str,
        file_size_mb: float = 0.0
    ):
        """Context manager for tracking operations"""
        operation_id = f"{operation_type}_{int(time.time() * 1000)}"

        try:
            event = self.start_operation(operation_id, operation_type, file_path, file_size_mb)
            yield event
            self.end_operation(operation_id, success=True)
        except Exception as e:
            self.end_operation(operation_id, success=False, error_message=str(e))
            raise

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.snapshots:
            return {}

        latest_snapshot = self.snapshots[-1]

        return {
            'monitoring_duration_s': time.time() - (self.start_time or time.time()),
            'current_memory_mb': latest_snapshot.memory_rss_mb,
            'memory_growth_mb': latest_snapshot.memory_rss_mb - self.baseline_memory_mb,
            'current_cpu_percent': latest_snapshot.cpu_percent,
            'thread_count': latest_snapshot.threads_count,
            'file_handles': latest_snapshot.file_handles,
            'active_operations': len(self.current_operations),
            'total_operations': len(self.processing_events),
            'successful_operations': len([e for e in self.processing_events if e.success]),
            'failed_operations': len([e for e in self.processing_events if not e.success]),
            'alerts_triggered': len(self.alerts_triggered)
        }

    def generate_report(self, include_trends: bool = True) -> PerformanceReport:
        """Generate comprehensive performance report"""
        if not self.start_time:
            raise ValueError("Cannot generate report - monitoring not started")

        current_time = datetime.now()
        monitoring_duration = (time.time() - self.start_time) / 3600  # hours

        # Calculate statistics
        total_operations = len(self.processing_events)
        successful_operations = len([e for e in self.processing_events if e.success])
        failed_operations = total_operations - successful_operations

        # Processing time statistics
        durations = [e.duration_seconds() for e in self.processing_events if e.end_time]
        avg_processing_time = statistics.mean(durations) if durations else 0.0
        median_processing_time = statistics.median(durations) if durations else 0.0
        max_processing_time = max(durations) if durations else 0.0
        total_processing_time = sum(durations)

        # Memory statistics
        memory_values = [s.memory_rss_mb for s in self.snapshots]
        peak_memory = max(memory_values) if memory_values else 0.0
        avg_memory = statistics.mean(memory_values) if memory_values else 0.0
        max_memory_growth = peak_memory - self.baseline_memory_mb

        # Throughput statistics
        total_files = len(self.processing_events)
        total_rows = sum(e.rows_processed for e in self.processing_events)

        avg_throughput_files = (total_files / monitoring_duration) if monitoring_duration > 0 else 0.0
        avg_throughput_rows = (total_rows / total_processing_time) if total_processing_time > 0 else 0.0

        # Error analysis
        error_rate = (failed_operations / total_operations) if total_operations > 0 else 0.0
        error_messages = [e.error_message for e in self.processing_events if e.error_message]
        common_errors = {}
        for error in error_messages:
            # Simplify error message for grouping
            error_key = error.split(':')[0] if error else 'Unknown'
            common_errors[error_key] = common_errors.get(error_key, 0) + 1

        # Performance trend analysis
        performance_trend = "stable"
        bottlenecks = []
        recommendations = []

        if include_trends:
            performance_trend, bottlenecks, recommendations = self._analyze_performance_trends()

        report = PerformanceReport(
            report_id=f"report_{int(time.time())}",
            generation_time=current_time,
            monitoring_duration_hours=monitoring_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            total_files_processed=total_files,
            total_rows_processed=total_rows,
            avg_processing_time_s=avg_processing_time,
            median_processing_time_s=median_processing_time,
            max_processing_time_s=max_processing_time,
            total_processing_time_s=total_processing_time,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            max_memory_growth_mb=max_memory_growth,
            avg_throughput_files_per_hour=avg_throughput_files,
            avg_throughput_rows_per_second=avg_throughput_rows,
            error_rate=error_rate,
            common_errors=common_errors,
            performance_trend=performance_trend,
            bottlenecks_identified=bottlenecks,
            recommendations=recommendations
        )

        return report

    def _analyze_performance_trends(self) -> Tuple[str, List[str], List[str]]:
        """Analyze performance trends and identify bottlenecks"""
        if len(self.processing_events) < 5:
            return "insufficient_data", [], ["Collect more data for trend analysis"]

        bottlenecks = []
        recommendations = []

        # Analyze processing time trends
        recent_events = self.processing_events[-10:]  # Last 10 operations
        older_events = self.processing_events[:-10] if len(self.processing_events) > 10 else []

        if older_events:
            recent_avg_time = statistics.mean([e.duration_seconds() for e in recent_events if e.end_time])
            older_avg_time = statistics.mean([e.duration_seconds() for e in older_events if e.end_time])

            time_change_ratio = recent_avg_time / older_avg_time if older_avg_time > 0 else 1.0

            if time_change_ratio > 1.2:
                trend = "degrading"
                bottlenecks.append("Processing time increasing over time")
                recommendations.append("Consider optimizing processing algorithms or increasing resources")
            elif time_change_ratio < 0.8:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Memory usage analysis
        if self.snapshots:
            memory_growth_rate = (self.snapshots[-1].memory_rss_mb - self.baseline_memory_mb) / len(self.snapshots)

            if memory_growth_rate > 1.0:  # More than 1MB per snapshot
                bottlenecks.append("High memory growth rate detected")
                recommendations.append("Enable streaming processing and check for memory leaks")

        # Error rate analysis
        error_rate = len([e for e in self.processing_events if not e.success]) / len(self.processing_events)

        if error_rate > self.alert_config.error_rate_threshold:
            bottlenecks.append(f"High error rate: {error_rate:.1%}")
            recommendations.append("Review error patterns and improve error handling")

        # Cache effectiveness analysis
        total_cache_requests = sum(e.cache_hits + e.cache_misses for e in self.processing_events)
        total_cache_hits = sum(e.cache_hits for e in self.processing_events)

        if total_cache_requests > 0:
            cache_hit_rate = total_cache_hits / total_cache_requests
            if cache_hit_rate < 0.3:
                bottlenecks.append(f"Low cache hit rate: {cache_hit_rate:.1%}")
                recommendations.append("Increase cache size or review caching strategy")

        # Throughput analysis
        if len(recent_events) >= 5:
            throughput_rates = [e.processing_rate_rows_per_second() for e in recent_events if e.rows_processed > 0]

            if throughput_rates:
                avg_throughput = statistics.mean(throughput_rates)
                if avg_throughput < 100:  # Less than 100 rows/second
                    bottlenecks.append(f"Low processing throughput: {avg_throughput:.0f} rows/sec")
                    recommendations.append("Consider parallel processing or performance optimizations")

        return trend, bottlenecks, recommendations

    def export_report(self, report: PerformanceReport, file_path: str, format: str = 'json'):
        """Export performance report to file"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == 'json':
            # Convert dataclass to dict for JSON serialization
            report_dict = {
                'report_id': report.report_id,
                'generation_time': report.generation_time.isoformat(),
                'monitoring_duration_hours': report.monitoring_duration_hours,
                'summary': {
                    'total_operations': report.total_operations,
                    'successful_operations': report.successful_operations,
                    'failed_operations': report.failed_operations,
                    'error_rate': report.error_rate
                },
                'performance': {
                    'avg_processing_time_s': report.avg_processing_time_s,
                    'median_processing_time_s': report.median_processing_time_s,
                    'max_processing_time_s': report.max_processing_time_s,
                    'peak_memory_mb': report.peak_memory_mb,
                    'avg_memory_mb': report.avg_memory_mb,
                    'avg_throughput_files_per_hour': report.avg_throughput_files_per_hour,
                    'avg_throughput_rows_per_second': report.avg_throughput_rows_per_second
                },
                'analysis': {
                    'performance_trend': report.performance_trend,
                    'bottlenecks_identified': report.bottlenecks_identified,
                    'recommendations': report.recommendations,
                    'common_errors': report.common_errors
                }
            }

            with open(file_path, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)

        elif format.lower() == 'pickle':
            with open(file_path, 'wb') as f:
                pickle.dump(report, f)

        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Performance report exported to {file_path}")

    def get_alerts(self, severity: Optional[str] = None, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get triggered alerts with optional filtering"""
        alerts = self.alerts_triggered

        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]

        if last_n:
            alerts = alerts[-last_n:]

        return alerts

    def clear_alerts(self):
        """Clear all triggered alerts"""
        self.alerts_triggered.clear()
        logger.info("Performance alerts cleared")


# Convenience functions and decorators

def monitor_excel_performance(
    operation_type: str = "excel_processing",
    track_memory: bool = True,
    track_cpu: bool = True
):
    """Decorator to monitor Excel processing function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = ExcelPerformanceMonitor(
                track_memory=track_memory,
                track_cpu=track_cpu,
                enable_detailed_logging=True
            )

            with monitor:
                file_path = "unknown"
                if args and hasattr(args[0], '__str__'):
                    file_path = str(args[0])

                with monitor.track_operation(operation_type, file_path):
                    result = func(*args, **kwargs)

                # Log performance summary
                stats = monitor.get_current_stats()
                logger.info(
                    f"Performance Summary - {operation_type}: "
                    f"Duration: {stats.get('monitoring_duration_s', 0):.2f}s, "
                    f"Memory: {stats.get('current_memory_mb', 0):.0f}MB, "
                    f"Success: {stats.get('successful_operations', 0)}/{stats.get('total_operations', 0)}"
                )

                return result
        return wrapper
    return decorator


@contextmanager
def excel_performance_context(
    monitor_config: Optional[Dict[str, Any]] = None,
    operation_type: str = "excel_batch_processing"
):
    """Context manager for Excel performance monitoring"""
    config = monitor_config or {}

    monitor = ExcelPerformanceMonitor(**config)

    try:
        with monitor:
            yield monitor
    finally:
        # Generate final report
        try:
            report = monitor.generate_report()
            logger.info(
                f"Performance Report - {operation_type}: "
                f"Operations: {report.successful_operations}/{report.total_operations}, "
                f"Avg Time: {report.avg_processing_time_s:.2f}s, "
                f"Peak Memory: {report.peak_memory_mb:.0f}MB, "
                f"Throughput: {report.avg_throughput_files_per_hour:.1f} files/hour"
            )
        except Exception as e:
            logger.warning(f"Failed to generate final performance report: {e}")


if __name__ == "__main__":
    # Example usage and testing
    import sys

    print("Excel Performance Monitor Test")

    # Test basic monitoring
    with ExcelPerformanceMonitor(enable_detailed_logging=True) as monitor:
        print("Starting test operations...")

        # Simulate some operations
        for i in range(3):
            file_path = f"test_file_{i}.xlsx"

            with monitor.track_operation("test_processing", file_path, file_size_mb=10.0):
                # Simulate processing time
                time.sleep(1.0)

                # Simulate some memory allocation
                data = [random.random() for _ in range(100000)]
                del data

        print("\nCurrent Stats:")
        stats = monitor.get_current_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\nGenerating Report...")
        report = monitor.generate_report()

        print(f"\nPerformance Report Summary:")
        print(f"  Operations: {report.successful_operations}/{report.total_operations}")
        print(f"  Avg Processing Time: {report.avg_processing_time_s:.2f}s")
        print(f"  Peak Memory: {report.peak_memory_mb:.0f}MB")
        print(f"  Performance Trend: {report.performance_trend}")

        if report.recommendations:
            print(f"  Recommendations:")
            for rec in report.recommendations:
                print(f"    - {rec}")

    print("\nMonitoring test completed.")