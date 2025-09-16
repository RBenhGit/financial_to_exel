"""
Data Source Health Monitoring System
===================================

Comprehensive health monitoring for all data sources with performance tracking,
quality scoring, and failure detection capabilities.
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from pathlib import Path
from enum import Enum

from core.data_sources.interfaces.data_source_interfaces import DataSourceInterface, DataSourceType
from utils.performance_monitor import PerformanceMonitor, PerformanceMetric


class HealthStatus(Enum):
    """Health status levels for data sources"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


@dataclass
class HealthMetrics:
    """Container for data source health metrics"""

    source_type: DataSourceType
    source_name: str
    timestamp: datetime

    # Performance metrics
    response_time_ms: float
    success_rate: float
    error_rate: float

    # Quality metrics
    data_quality_score: float
    data_completeness: float

    # Availability metrics
    availability_percentage: float
    consecutive_failures: int

    # Request statistics
    total_requests: int
    successful_requests: int
    failed_requests: int

    # Error information
    last_error: Optional[str] = None
    error_types: Dict[str, int] = field(default_factory=dict)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def health_status(self) -> HealthStatus:
        """Determine overall health status based on metrics"""
        if self.availability_percentage < 50 or self.consecutive_failures > 10:
            return HealthStatus.UNAVAILABLE
        elif self.success_rate < 0.7 or self.response_time_ms > 10000:
            return HealthStatus.CRITICAL
        elif self.success_rate < 0.9 or self.response_time_ms > 5000:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    @property
    def overall_score(self) -> float:
        """Calculate overall health score (0-100)"""
        weights = {
            'availability': 0.3,
            'success_rate': 0.25,
            'response_time': 0.2,
            'data_quality': 0.25
        }

        # Normalize response time (0-100 scale, where 100ms = 100, 10s = 0)
        response_score = max(0, 100 - (self.response_time_ms / 100))

        score = (
            weights['availability'] * self.availability_percentage +
            weights['success_rate'] * (self.success_rate * 100) +
            weights['response_time'] * response_score +
            weights['data_quality'] * (self.data_quality_score * 100)
        )

        return min(100, max(0, score))


class DataSourceHealthMonitor:
    """
    Central health monitoring system for all data sources.

    Tracks performance, availability, and data quality across all configured
    data sources and provides real-time health status and alerting.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the health monitor.

        Args:
            config: Configuration dictionary with monitoring settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.DataSourceHealthMonitor")

        # Storage for health metrics
        self.current_metrics: Dict[str, HealthMetrics] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Performance monitoring integration
        self.performance_monitor = PerformanceMonitor()

        # Source tracking
        self.monitored_sources: Dict[str, DataSourceInterface] = {}
        self.source_response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.source_quality_scores: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # Failure tracking
        self.consecutive_failures: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Configuration
        self.health_check_interval = self.config.get('health_check_interval', 300)  # 5 minutes
        self.metrics_retention_days = self.config.get('metrics_retention_days', 7)
        self.quality_threshold = self.config.get('quality_threshold', 0.8)
        self.response_time_threshold = self.config.get('response_time_threshold', 5000)  # 5 seconds

        # Storage
        self.metrics_file = Path(self.config.get('metrics_file', 'data/cache/health_metrics.json'))
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("Data Source Health Monitor initialized")

    def register_data_source(self, source: DataSourceInterface, source_name: str) -> None:
        """
        Register a data source for monitoring.

        Args:
            source: Data source interface to monitor
            source_name: Unique name for the data source
        """
        self.monitored_sources[source_name] = source
        self.logger.info(f"Registered data source for monitoring: {source_name}")

    def record_request_start(self, source_name: str, operation: str = "fetch_data") -> str:
        """
        Record the start of a data source request.

        Args:
            source_name: Name of the data source
            operation: Type of operation being performed

        Returns:
            Timer ID for stopping the timer
        """
        timer_id = f"{source_name}_{operation}_{int(time.time() * 1000)}"
        self.performance_monitor.start_timer(timer_id, {'source': source_name, 'operation': operation})
        return timer_id

    def record_request_end(
        self,
        timer_id: str,
        success: bool,
        error: Optional[Exception] = None,
        data_quality_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record the end of a data source request and update metrics.

        Args:
            timer_id: Timer ID from record_request_start
            success: Whether the request was successful
            error: Error information if request failed
            data_quality_score: Quality score of returned data (0-1)
            metadata: Additional metadata about the request
        """
        try:
            # Stop the performance timer
            metric = self.performance_monitor.stop_timer(timer_id, {
                'success': success,
                'error': str(error) if error else None,
                'data_quality_score': data_quality_score,
                **(metadata or {})
            })

            # Extract source name from timer ID
            source_name = timer_id.split('_')[0]

            # Update response time tracking
            self.source_response_times[source_name].append(metric.duration_ms)

            # Update quality tracking
            if data_quality_score is not None:
                self.source_quality_scores[source_name].append(data_quality_score)

            # Update failure tracking
            if success:
                self.consecutive_failures[source_name] = 0
            else:
                self.consecutive_failures[source_name] += 1
                if error:
                    error_type = type(error).__name__
                    self.error_counts[source_name][error_type] += 1

            # Update current metrics
            self._update_source_metrics(source_name)

        except Exception as e:
            self.logger.error(f"Failed to record request end: {e}")

    def _update_source_metrics(self, source_name: str) -> None:
        """Update current metrics for a data source"""
        try:
            source = self.monitored_sources.get(source_name)
            if not source:
                return

            # Get basic health check from source
            source_health = source.health_check()

            # Calculate metrics from tracked data
            response_times = list(self.source_response_times[source_name])
            quality_scores = list(self.source_quality_scores[source_name])

            # Response time metrics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            # Quality metrics
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            completeness = len(quality_scores) / max(1, len(response_times))

            # Availability calculation (last 24 hours)
            total_requests = source_health.get('request_count', 0)
            successful_requests = source_health.get('success_count', 0)
            failed_requests = total_requests - successful_requests

            success_rate = successful_requests / max(1, total_requests)
            error_rate = failed_requests / max(1, total_requests)
            availability = success_rate * 100

            # Create updated metrics
            metrics = HealthMetrics(
                source_type=source.get_source_type(),
                source_name=source_name,
                timestamp=datetime.now(),
                response_time_ms=avg_response_time,
                success_rate=success_rate,
                error_rate=error_rate,
                data_quality_score=avg_quality,
                data_completeness=completeness,
                availability_percentage=availability,
                consecutive_failures=self.consecutive_failures[source_name],
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                last_error=source_health.get('last_error'),
                error_types=dict(self.error_counts[source_name]),
                metadata={
                    'last_updated': datetime.now().isoformat(),
                    'monitoring_duration': len(response_times)
                }
            )

            # Store current metrics
            self.current_metrics[source_name] = metrics

            # Add to history
            self.metrics_history[source_name].append(metrics)

            self.logger.debug(f"Updated metrics for {source_name}: {metrics.health_status.value}")

        except Exception as e:
            self.logger.error(f"Failed to update metrics for {source_name}: {e}")

    def get_source_health(self, source_name: str) -> Optional[HealthMetrics]:
        """
        Get current health metrics for a specific data source.

        Args:
            source_name: Name of the data source

        Returns:
            Current health metrics or None if not found
        """
        return self.current_metrics.get(source_name)

    def get_all_health_metrics(self) -> Dict[str, HealthMetrics]:
        """Get current health metrics for all monitored sources"""
        return self.current_metrics.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of overall system health.

        Returns:
            Dictionary with overall health statistics
        """
        if not self.current_metrics:
            return {'status': 'no_data', 'sources': 0}

        statuses = [metrics.health_status for metrics in self.current_metrics.values()]
        scores = [metrics.overall_score for metrics in self.current_metrics.values()]

        status_counts = {status.value: statuses.count(status) for status in HealthStatus}

        return {
            'overall_status': self._determine_overall_status(statuses),
            'average_score': sum(scores) / len(scores),
            'sources_count': len(self.current_metrics),
            'status_breakdown': status_counts,
            'healthy_sources': status_counts[HealthStatus.HEALTHY.value],
            'degraded_sources': status_counts[HealthStatus.DEGRADED.value],
            'critical_sources': status_counts[HealthStatus.CRITICAL.value],
            'unavailable_sources': status_counts[HealthStatus.UNAVAILABLE.value],
            'last_updated': datetime.now().isoformat()
        }

    def _determine_overall_status(self, statuses: List[HealthStatus]) -> str:
        """Determine overall system status from individual source statuses"""
        if HealthStatus.UNAVAILABLE in statuses:
            return HealthStatus.CRITICAL.value
        elif HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL.value
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED.value
        else:
            return HealthStatus.HEALTHY.value

    def perform_health_checks(self) -> Dict[str, HealthMetrics]:
        """
        Perform health checks on all monitored data sources.

        Returns:
            Dictionary of current health metrics for all sources
        """
        self.logger.info("Performing health checks on all data sources")

        for source_name in self.monitored_sources:
            self._update_source_metrics(source_name)

        # Save metrics to file
        self._save_metrics()

        return self.get_all_health_metrics()

    def _save_metrics(self) -> None:
        """Save current metrics to persistent storage"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    name: asdict(metrics)
                    for name, metrics in self.current_metrics.items()
                },
                'summary': self.get_health_summary()
            }

            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self.logger.debug(f"Saved health metrics to {self.metrics_file}")

        except Exception as e:
            self.logger.error(f"Failed to save health metrics: {e}")

    def load_metrics(self) -> bool:
        """
        Load previously saved metrics from storage.

        Returns:
            True if metrics were loaded successfully
        """
        try:
            if not self.metrics_file.exists():
                return False

            with open(self.metrics_file, 'r') as f:
                data = json.load(f)

            # Restore metrics
            for name, metrics_data in data.get('metrics', {}).items():
                # Convert back to HealthMetrics object
                metrics_data['timestamp'] = datetime.fromisoformat(metrics_data['timestamp'])
                metrics_data['source_type'] = DataSourceType(metrics_data['source_type'])

                metrics = HealthMetrics(**metrics_data)
                self.current_metrics[name] = metrics
                self.metrics_history[name].append(metrics)

            self.logger.info(f"Loaded health metrics for {len(self.current_metrics)} sources")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load health metrics: {e}")
            return False

    def get_metrics_history(self, source_name: str, hours: int = 24) -> List[HealthMetrics]:
        """
        Get historical metrics for a data source.

        Args:
            source_name: Name of the data source
            hours: Number of hours of history to retrieve

        Returns:
            List of historical metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = self.metrics_history.get(source_name, [])

        return [metrics for metrics in history if metrics.timestamp >= cutoff_time]

    def clear_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(days=self.metrics_retention_days)

        for source_name in self.metrics_history:
            history = self.metrics_history[source_name]
            # Keep only recent metrics
            while history and history[0].timestamp < cutoff_time:
                history.popleft()

        self.logger.info(f"Cleared metrics older than {self.metrics_retention_days} days")


# Global health monitor instance
_health_monitor = None


def get_health_monitor(config: Optional[Dict[str, Any]] = None) -> DataSourceHealthMonitor:
    """Get or create the global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = DataSourceHealthMonitor(config)
    return _health_monitor


def reset_health_monitor() -> None:
    """Reset the global health monitor (useful for testing)"""
    global _health_monitor
    _health_monitor = None