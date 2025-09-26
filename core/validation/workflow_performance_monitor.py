"""
Workflow Performance Monitoring System

This module provides performance monitoring for the 6 validated UAT scenarios,
tracking execution times, resource usage, and user interaction patterns
to ensure optimal performance in production.
"""

import os
import sys
import time
import psutil
import json
import pandas as pd
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import traceback
from functools import wraps

# Import logging utilities
try:
    from utils.logging_config import get_streamlit_logger
    logger = get_streamlit_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a workflow execution."""
    workflow_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    user_session: Optional[str]
    input_size: Optional[int]
    output_size: Optional[int]


@dataclass
class WorkflowBenchmark:
    """Performance benchmark for a specific workflow."""
    workflow_name: str
    target_execution_time: float  # seconds
    max_memory_usage_mb: float
    max_cpu_usage_percent: float
    success_rate_threshold: float  # percentage


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations."""
    alert_id: str
    workflow_name: str
    alert_type: str  # "slow_execution", "high_memory", "high_cpu", "failure_rate"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime


class WorkflowPerformanceMonitor:
    """
    Comprehensive performance monitoring system for the 6 validated UAT workflows:
    1. FCF Analysis
    2. DCF Valuation
    3. DDM Analysis
    4. P/B Analysis
    5. Portfolio Analysis
    6. Watch List Management
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the workflow performance monitor."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.monitoring_db_path = self.project_root / "data" / "workflow_performance.db"
        self.reports_dir = self.project_root / "reports" / "performance"

        # Ensure directories exist
        self.monitoring_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Define workflow benchmarks based on UAT validation
        self._init_workflow_benchmarks()

        # Performance monitoring state
        self._monitoring_active = False
        self._current_metrics = {}
        self._alerts = []

    def _init_database(self):
        """Initialize SQLite database for performance monitoring."""

        with sqlite3.connect(self.monitoring_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workflow_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    memory_usage_mb REAL NOT NULL,
                    cpu_usage_percent REAL NOT NULL,
                    success INTEGER NOT NULL,
                    error_message TEXT,
                    timestamp TEXT NOT NULL,
                    user_session TEXT,
                    input_size INTEGER,
                    output_size INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    workflow_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_workflow_timestamp ON workflow_performance(workflow_name, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON workflow_performance(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)')

    def _init_workflow_benchmarks(self):
        """Initialize performance benchmarks for each validated workflow."""

        # Benchmarks based on UAT success criteria and expected performance
        self.workflow_benchmarks = {
            "fcf_analysis": WorkflowBenchmark(
                workflow_name="fcf_analysis",
                target_execution_time=3.0,  # seconds
                max_memory_usage_mb=100.0,
                max_cpu_usage_percent=50.0,
                success_rate_threshold=95.0
            ),
            "dcf_valuation": WorkflowBenchmark(
                workflow_name="dcf_valuation",
                target_execution_time=5.0,  # More complex calculations
                max_memory_usage_mb=150.0,
                max_cpu_usage_percent=60.0,
                success_rate_threshold=95.0
            ),
            "ddm_analysis": WorkflowBenchmark(
                workflow_name="ddm_analysis",
                target_execution_time=4.0,
                max_memory_usage_mb=120.0,
                max_cpu_usage_percent=55.0,
                success_rate_threshold=95.0
            ),
            "pb_analysis": WorkflowBenchmark(
                workflow_name="pb_analysis",
                target_execution_time=3.5,
                max_memory_usage_mb=110.0,
                max_cpu_usage_percent=50.0,
                success_rate_threshold=95.0
            ),
            "portfolio_analysis": WorkflowBenchmark(
                workflow_name="portfolio_analysis",
                target_execution_time=8.0,  # Multi-company analysis
                max_memory_usage_mb=250.0,
                max_cpu_usage_percent=70.0,
                success_rate_threshold=92.0
            ),
            "watchlist_management": WorkflowBenchmark(
                workflow_name="watchlist_management",
                target_execution_time=2.0,  # Simple CRUD operations
                max_memory_usage_mb=50.0,
                max_cpu_usage_percent=30.0,
                success_rate_threshold=98.0
            )
        }

    @contextmanager
    def monitor_workflow(self, workflow_name: str, user_session: Optional[str] = None,
                         input_size: Optional[int] = None):
        """Context manager to monitor workflow performance."""

        if workflow_name not in self.workflow_benchmarks:
            logger.warning(f"Unknown workflow: {workflow_name}")
            yield None
            return

        # Start monitoring
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu_percent = psutil.cpu_percent(interval=None)

        success = False
        error_message = None
        output_size = None

        try:
            yield self
            success = True
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Workflow {workflow_name} failed: {e}")
        finally:
            # Calculate metrics
            end_time = time.time()
            execution_time = end_time - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_usage = end_memory - start_memory
            cpu_usage = psutil.cpu_percent(interval=0.1)  # Quick sample

            # Create performance metrics
            metrics = PerformanceMetrics(
                workflow_name=workflow_name,
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(),
                user_session=user_session,
                input_size=input_size,
                output_size=output_size
            )

            # Store metrics
            self._store_performance_metrics(metrics)

            # Check for performance alerts
            self._check_performance_thresholds(metrics)

    def performance_decorator(self, workflow_name: str):
        """Decorator to automatically monitor function performance."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract session info if available
                user_session = kwargs.get('session_id') or kwargs.get('user_session')

                with self.monitor_workflow(workflow_name, user_session):
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def _store_performance_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics in the database."""

        with sqlite3.connect(self.monitoring_db_path) as conn:
            conn.execute('''
                INSERT INTO workflow_performance
                (workflow_name, execution_time, memory_usage_mb, cpu_usage_percent,
                 success, error_message, timestamp, user_session, input_size, output_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.workflow_name,
                metrics.execution_time,
                metrics.memory_usage_mb,
                metrics.cpu_usage_percent,
                1 if metrics.success else 0,
                metrics.error_message,
                metrics.timestamp.isoformat(),
                metrics.user_session,
                metrics.input_size,
                metrics.output_size
            ))

        logger.info(f"Stored performance metrics for {metrics.workflow_name}: "
                   f"{metrics.execution_time:.2f}s, {metrics.memory_usage_mb:.1f}MB")

    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check performance metrics against benchmarks and generate alerts."""

        benchmark = self.workflow_benchmarks[metrics.workflow_name]
        alerts = []

        # Check execution time
        if metrics.execution_time > benchmark.target_execution_time * 1.5:  # 50% over target
            severity = "high" if metrics.execution_time > benchmark.target_execution_time * 2 else "medium"
            alerts.append(PerformanceAlert(
                alert_id=f"{metrics.workflow_name}_slow_{int(time.time())}",
                workflow_name=metrics.workflow_name,
                alert_type="slow_execution",
                severity=severity,
                message=f"Slow execution: {metrics.execution_time:.2f}s (target: {benchmark.target_execution_time:.1f}s)",
                current_value=metrics.execution_time,
                threshold_value=benchmark.target_execution_time,
                timestamp=metrics.timestamp
            ))

        # Check memory usage
        if metrics.memory_usage_mb > benchmark.max_memory_usage_mb:
            severity = "critical" if metrics.memory_usage_mb > benchmark.max_memory_usage_mb * 2 else "high"
            alerts.append(PerformanceAlert(
                alert_id=f"{metrics.workflow_name}_memory_{int(time.time())}",
                workflow_name=metrics.workflow_name,
                alert_type="high_memory",
                severity=severity,
                message=f"High memory usage: {metrics.memory_usage_mb:.1f}MB (max: {benchmark.max_memory_usage_mb:.1f}MB)",
                current_value=metrics.memory_usage_mb,
                threshold_value=benchmark.max_memory_usage_mb,
                timestamp=metrics.timestamp
            ))

        # Check CPU usage
        if metrics.cpu_usage_percent > benchmark.max_cpu_usage_percent:
            severity = "medium" if metrics.cpu_usage_percent < 90 else "high"
            alerts.append(PerformanceAlert(
                alert_id=f"{metrics.workflow_name}_cpu_{int(time.time())}",
                workflow_name=metrics.workflow_name,
                alert_type="high_cpu",
                severity=severity,
                message=f"High CPU usage: {metrics.cpu_usage_percent:.1f}% (max: {benchmark.max_cpu_usage_percent:.1f}%)",
                current_value=metrics.cpu_usage_percent,
                threshold_value=benchmark.max_cpu_usage_percent,
                timestamp=metrics.timestamp
            ))

        # Store alerts
        for alert in alerts:
            self._store_performance_alert(alert)

    def _store_performance_alert(self, alert: PerformanceAlert):
        """Store performance alert in the database."""

        with sqlite3.connect(self.monitoring_db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO performance_alerts
                    (alert_id, workflow_name, alert_type, severity, message,
                     current_value, threshold_value, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.alert_id,
                    alert.workflow_name,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    alert.current_value,
                    alert.threshold_value,
                    alert.timestamp.isoformat()
                ))
                logger.warning(f"Performance alert: {alert.message}")
            except sqlite3.IntegrityError:
                # Alert already exists
                pass

    def get_performance_data(self, workflow_name: Optional[str] = None,
                            days: int = 7) -> pd.DataFrame:
        """Retrieve performance data from the database."""

        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.monitoring_db_path) as conn:
            if workflow_name:
                query = '''
                    SELECT * FROM workflow_performance
                    WHERE workflow_name = ? AND timestamp >= ?
                    ORDER BY timestamp
                '''
                params = (workflow_name, cutoff_date.isoformat())
            else:
                query = '''
                    SELECT * FROM workflow_performance
                    WHERE timestamp >= ?
                    ORDER BY timestamp
                '''
                params = (cutoff_date.isoformat(),)

            df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['success'] = df['success'].astype(bool)

            return df

    def get_workflow_statistics(self, workflow_name: str, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific workflow."""

        df = self.get_performance_data(workflow_name, days)

        if df.empty:
            return {
                "workflow_name": workflow_name,
                "data_points": 0,
                "statistics": {}
            }

        benchmark = self.workflow_benchmarks[workflow_name]

        stats = {
            "workflow_name": workflow_name,
            "data_points": len(df),
            "period_days": days,
            "benchmark": asdict(benchmark),
            "statistics": {
                "execution_time": {
                    "mean": df['execution_time'].mean(),
                    "median": df['execution_time'].median(),
                    "std": df['execution_time'].std(),
                    "min": df['execution_time'].min(),
                    "max": df['execution_time'].max(),
                    "p95": df['execution_time'].quantile(0.95),
                    "benchmark_compliance": (df['execution_time'] <= benchmark.target_execution_time).mean() * 100
                },
                "memory_usage": {
                    "mean": df['memory_usage_mb'].mean(),
                    "median": df['memory_usage_mb'].median(),
                    "std": df['memory_usage_mb'].std(),
                    "max": df['memory_usage_mb'].max(),
                    "benchmark_compliance": (df['memory_usage_mb'] <= benchmark.max_memory_usage_mb).mean() * 100
                },
                "cpu_usage": {
                    "mean": df['cpu_usage_percent'].mean(),
                    "median": df['cpu_usage_percent'].median(),
                    "std": df['cpu_usage_percent'].std(),
                    "max": df['cpu_usage_percent'].max(),
                    "benchmark_compliance": (df['cpu_usage_percent'] <= benchmark.max_cpu_usage_percent).mean() * 100
                },
                "success_rate": df['success'].mean() * 100,
                "total_executions": len(df),
                "failed_executions": (df['success'] == False).sum()
            }
        }

        # Add trend analysis
        if len(df) > 1:
            df_sorted = df.sort_values('timestamp')
            first_half = df_sorted[:len(df_sorted)//2]
            second_half = df_sorted[len(df_sorted)//2:]

            stats["trends"] = {
                "execution_time_trend": "improving" if second_half['execution_time'].mean() < first_half['execution_time'].mean() else "degrading",
                "memory_usage_trend": "improving" if second_half['memory_usage_mb'].mean() < first_half['memory_usage_mb'].mean() else "degrading",
                "success_rate_trend": "improving" if second_half['success'].mean() > first_half['success'].mean() else "degrading"
            }

        return stats

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active performance alerts."""

        with sqlite3.connect(self.monitoring_db_path) as conn:
            if severity:
                query = '''
                    SELECT * FROM performance_alerts
                    WHERE resolved = 0 AND severity = ?
                    ORDER BY timestamp DESC
                '''
                params = (severity,)
            else:
                query = '''
                    SELECT * FROM performance_alerts
                    WHERE resolved = 0
                    ORDER BY timestamp DESC
                '''
                params = ()

            df = pd.read_sql_query(query, conn, params=params)

            if df.empty:
                return []

            return df.to_dict('records')

    def generate_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive performance report for all workflows."""

        report = {
            "report_id": f"WORKFLOW_PERF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "workflows": {},
            "overall_summary": {},
            "active_alerts": self.get_active_alerts(),
            "recommendations": []
        }

        # Analyze each workflow
        all_workflow_stats = []
        for workflow_name in self.workflow_benchmarks.keys():
            stats = self.get_workflow_statistics(workflow_name, days)
            report["workflows"][workflow_name] = stats
            if stats["data_points"] > 0:
                all_workflow_stats.append(stats)

        # Overall summary
        if all_workflow_stats:
            total_executions = sum(s["statistics"]["total_executions"] for s in all_workflow_stats)
            total_failures = sum(s["statistics"]["failed_executions"] for s in all_workflow_stats)
            overall_success_rate = ((total_executions - total_failures) / total_executions * 100) if total_executions > 0 else 0

            avg_execution_times = {name: stats["statistics"]["execution_time"]["mean"]
                                 for name, stats in report["workflows"].items()
                                 if stats["data_points"] > 0}

            report["overall_summary"] = {
                "total_workflow_executions": total_executions,
                "overall_success_rate": overall_success_rate,
                "average_execution_times": avg_execution_times,
                "workflows_monitored": len(all_workflow_stats),
                "active_alerts_count": len(report["active_alerts"]),
                "performance_status": "healthy" if overall_success_rate >= 95 and len(report["active_alerts"]) == 0 else "needs_attention"
            }

        # Generate recommendations
        recommendations = []

        if len(report["active_alerts"]) > 0:
            high_severity_alerts = [a for a in report["active_alerts"] if a["severity"] in ["high", "critical"]]
            if high_severity_alerts:
                recommendations.append("Address high-severity performance alerts immediately")

        for workflow_name, stats in report["workflows"].items():
            if stats["data_points"] > 0:
                success_rate = stats["statistics"]["success_rate"]
                benchmark = stats["benchmark"]["success_rate_threshold"]

                if success_rate < benchmark:
                    recommendations.append(f"Improve {workflow_name} reliability (current: {success_rate:.1f}%, target: {benchmark:.1f}%)")

                exec_compliance = stats["statistics"]["execution_time"]["benchmark_compliance"]
                if exec_compliance < 80:
                    recommendations.append(f"Optimize {workflow_name} performance (only {exec_compliance:.1f}% meet timing targets)")

        if not recommendations:
            recommendations.append("All workflows performing within expected parameters")

        report["recommendations"] = recommendations

        # Save report
        report_file = self.reports_dir / f"workflow_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Workflow performance report generated: {report_file}")
        return report

    # Example usage methods for the 6 validated workflows

    def monitor_fcf_analysis(self, company_data: Dict[str, Any], session_id: Optional[str] = None):
        """Example: Monitor FCF analysis workflow."""
        with self.monitor_workflow("fcf_analysis", session_id, len(str(company_data))):
            # Simulate FCF analysis work
            time.sleep(0.1)  # Placeholder for actual analysis
            return {"fcf_result": "success"}

    def monitor_dcf_valuation(self, valuation_params: Dict[str, Any], session_id: Optional[str] = None):
        """Example: Monitor DCF valuation workflow."""
        with self.monitor_workflow("dcf_valuation", session_id, len(str(valuation_params))):
            # Simulate DCF valuation work
            time.sleep(0.2)  # Placeholder for actual valuation
            return {"dcv_result": "success"}


if __name__ == "__main__":
    monitor = WorkflowPerformanceMonitor()

    # Example usage
    print("Testing workflow performance monitoring...")

    # Simulate some workflow executions
    monitor.monitor_fcf_analysis({"company": "TEST", "data": [1, 2, 3]}, "user_123")
    monitor.monitor_dcf_valuation({"discount_rate": 0.1, "growth_rate": 0.05}, "user_123")

    # Generate performance report
    report = monitor.generate_performance_report(days=1)
    print(f"Generated performance report: {report['report_id']}")
    print(f"Overall status: {report['overall_summary'].get('performance_status', 'unknown')}")