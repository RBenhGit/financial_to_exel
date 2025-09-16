"""
Health Monitoring Integration Adapter
===================================

Provides seamless integration of health monitoring capabilities into existing
data managers and processing systems without breaking existing functionality.
"""

import logging
import functools
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from datetime import datetime

from .health_monitor import DataSourceHealthMonitor, get_health_monitor
from .alerting_system import AlertingSystem
from core.data_sources.interfaces.data_source_interfaces import DataSourceInterface, DataSourceType

# Type variable for decorator return types
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class MonitoringIntegration:
    """
    Integration layer that adds health monitoring to existing data management systems.

    This class provides decorators and mixins to add monitoring capabilities
    to existing data managers without requiring significant code changes.
    """

    def __init__(self, health_monitor: Optional[DataSourceHealthMonitor] = None):
        """
        Initialize monitoring integration.

        Args:
            health_monitor: Optional health monitor instance, creates one if not provided
        """
        self.health_monitor = health_monitor or get_health_monitor()
        self.alerting_system = AlertingSystem()
        self.logger = logging.getLogger(f"{__name__}.MonitoringIntegration")

    def monitor_data_source_call(
        self,
        source_name: str,
        operation: str = "data_fetch",
        track_quality: bool = True
    ):
        """
        Decorator to monitor data source calls and collect health metrics.

        Args:
            source_name: Name of the data source being monitored
            operation: Type of operation being performed
            track_quality: Whether to track data quality metrics

        Example:
            @monitor_data_source_call("yfinance", "fetch_market_data")
            def fetch_market_data(self, ticker: str):
                # Your existing code here
                return data
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Start monitoring
                timer_id = self.health_monitor.record_request_start(source_name, operation)

                success = False
                error = None
                result = None
                data_quality_score = None

                try:
                    # Execute the original function
                    result = func(*args, **kwargs)
                    success = True

                    # Calculate data quality if requested and data is available
                    if track_quality and result:
                        data_quality_score = self._calculate_data_quality(result)

                except Exception as e:
                    error = e
                    success = False
                    raise  # Re-raise the exception

                finally:
                    # Record the request completion
                    self.health_monitor.record_request_end(
                        timer_id=timer_id,
                        success=success,
                        error=error,
                        data_quality_score=data_quality_score,
                        metadata={
                            'function_name': func.__name__,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                    )

                    # Check for alerts if we have updated metrics
                    if source_name in self.health_monitor.current_metrics:
                        metrics = self.health_monitor.current_metrics[source_name]
                        self.alerting_system.check_metrics_for_alerts(metrics)

                return result

            return wrapper
        return decorator

    def _calculate_data_quality(self, data: Any) -> float:
        """
        Calculate data quality score for returned data.

        Args:
            data: Data returned from the data source

        Returns:
            Quality score between 0 and 1
        """
        if not data:
            return 0.0

        try:
            if isinstance(data, dict):
                # Check dictionary completeness
                total_fields = len(data)
                filled_fields = sum(1 for value in data.values() if value is not None)
                completeness = filled_fields / max(1, total_fields)

                # Check for error indicators
                has_errors = any(
                    key.lower() in ['error', 'errors', 'message']
                    for key in data.keys()
                )

                quality_score = completeness * (0.5 if has_errors else 1.0)
                return min(1.0, max(0.0, quality_score))

            elif isinstance(data, (list, tuple)):
                # For lists, check if there's data
                return 1.0 if len(data) > 0 else 0.0

            elif data is not None:
                # For other non-None data, assume good quality
                return 0.9

            return 0.0

        except Exception as e:
            self.logger.warning(f"Failed to calculate data quality: {e}")
            return 0.5  # Default to moderate quality if calculation fails


class MonitoredDataManagerMixin:
    """
    Mixin class that adds health monitoring capabilities to existing data managers.

    This mixin can be added to existing data manager classes to automatically
    provide health monitoring without changing the core functionality.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the monitoring mixin"""
        super().__init__(*args, **kwargs)

        # Initialize monitoring if not already present
        if not hasattr(self, '_monitoring_integration'):
            self._monitoring_integration = MonitoringIntegration()
            self._registered_sources = set()

        self.logger = logging.getLogger(f"{__name__}.MonitoredDataManagerMixin")

    def register_data_source_for_monitoring(
        self,
        source_name: str,
        source_type: DataSourceType,
        source_instance: Optional[DataSourceInterface] = None
    ) -> None:
        """
        Register a data source for health monitoring.

        Args:
            source_name: Unique name for the data source
            source_type: Type of data source
            source_instance: Optional data source instance
        """
        if source_name not in self._registered_sources:
            # Create a dummy source interface if none provided
            if source_instance is None:
                source_instance = self._create_dummy_source_interface(source_name, source_type)

            self._monitoring_integration.health_monitor.register_data_source(
                source_instance, source_name
            )
            self._registered_sources.add(source_name)

            self.logger.info(f"Registered {source_name} for health monitoring")

    def _create_dummy_source_interface(self, name: str, source_type: DataSourceType) -> DataSourceInterface:
        """Create a minimal data source interface for monitoring"""

        class DummyDataSource(DataSourceInterface):
            def __init__(self, name: str, source_type: DataSourceType):
                super().__init__()
                self.name = name
                self.source_type = source_type

            def fetch_data(self, request):
                # This won't be called directly
                raise NotImplementedError("Dummy source for monitoring only")

            def supports_request(self, request) -> bool:
                return True

            def get_source_type(self) -> DataSourceType:
                return self.source_type

        return DummyDataSource(name, source_type)

    def get_health_status(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get health status for data sources.

        Args:
            source_name: Optional specific source name

        Returns:
            Health status information
        """
        if source_name:
            metrics = self._monitoring_integration.health_monitor.get_source_health(source_name)
            return metrics.__dict__ if metrics else {}
        else:
            return self._monitoring_integration.health_monitor.get_health_summary()

    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for rendering monitoring dashboard"""
        return {
            'health_metrics': self._monitoring_integration.health_monitor.get_all_health_metrics(),
            'health_summary': self._monitoring_integration.health_monitor.get_health_summary(),
            'active_alerts': self._monitoring_integration.alerting_system.get_active_alerts(),
            'alert_summary': self._monitoring_integration.alerting_system.get_alert_summary()
        }

    def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all monitored sources"""
        return self._monitoring_integration.health_monitor.perform_health_checks()


def add_monitoring_to_function(
    source_name: str,
    operation: str = "operation",
    monitor_instance: Optional[MonitoringIntegration] = None
):
    """
    Standalone decorator to add monitoring to any function.

    Args:
        source_name: Name of the data source
        operation: Operation being performed
        monitor_instance: Optional monitoring instance

    Example:
        @add_monitoring_to_function("excel_reader", "read_financial_statements")
        def read_financial_statements(file_path):
            # Your code here
            return data
    """
    if monitor_instance is None:
        monitor_instance = MonitoringIntegration()

    return monitor_instance.monitor_data_source_call(source_name, operation, track_quality=True)


class MonitoringContext:
    """
    Context manager for monitoring data source operations.

    Provides a context manager approach to monitoring that can be used
    around existing code blocks without decorators.

    Example:
        with MonitoringContext("api_source", "fetch_data") as monitor:
            data = fetch_some_data()
            monitor.set_data_quality(calculate_quality(data))
    """

    def __init__(
        self,
        source_name: str,
        operation: str,
        monitor_instance: Optional[MonitoringIntegration] = None
    ):
        """
        Initialize monitoring context.

        Args:
            source_name: Name of the data source
            operation: Operation being performed
            monitor_instance: Optional monitoring instance
        """
        self.source_name = source_name
        self.operation = operation
        self.monitor_instance = monitor_instance or MonitoringIntegration()
        self.timer_id = None
        self.data_quality_score = None
        self.metadata = {}

    def __enter__(self):
        """Start monitoring"""
        self.timer_id = self.monitor_instance.health_monitor.record_request_start(
            self.source_name, self.operation
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End monitoring and record results"""
        success = exc_type is None
        error = exc_val if exc_type else None

        self.monitor_instance.health_monitor.record_request_end(
            timer_id=self.timer_id,
            success=success,
            error=error,
            data_quality_score=self.data_quality_score,
            metadata=self.metadata
        )

        # Check for alerts
        if self.source_name in self.monitor_instance.health_monitor.current_metrics:
            metrics = self.monitor_instance.health_monitor.current_metrics[self.source_name]
            self.monitor_instance.alerting_system.check_metrics_for_alerts(metrics)

    def set_data_quality(self, quality_score: float) -> None:
        """Set data quality score for this operation"""
        self.data_quality_score = quality_score

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to this operation"""
        self.metadata[key] = value


def create_monitored_data_manager(base_class, monitoring_config: Optional[Dict[str, Any]] = None):
    """
    Factory function to create a monitored version of any data manager class.

    Args:
        base_class: The base data manager class to enhance
        monitoring_config: Optional monitoring configuration

    Returns:
        Enhanced class with monitoring capabilities

    Example:
        MonitoredEnhancedDataManager = create_monitored_data_manager(
            EnhancedDataManager,
            {'enable_alerts': True, 'health_check_interval': 300}
        )

        manager = MonitoredEnhancedDataManager(base_path="./data")
    """

    class MonitoredDataManager(MonitoredDataManagerMixin, base_class):
        """Dynamically created monitored data manager"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Apply monitoring configuration
            if monitoring_config:
                self._monitoring_integration = MonitoringIntegration(
                    get_health_monitor(monitoring_config)
                )

            # Auto-register common data source types
            self._auto_register_sources()

        def _auto_register_sources(self):
            """Automatically register common data sources based on class attributes"""
            # Register yfinance if available
            if hasattr(self, 'yfinance_enabled') or hasattr(self, '_yfinance'):
                self.register_data_source_for_monitoring("yfinance", DataSourceType.API_YAHOO)

            # Register unified adapter sources if available
            if hasattr(self, 'unified_adapter'):
                for source_type in [DataSourceType.API_FMP, DataSourceType.API_ALPHA_VANTAGE,
                                  DataSourceType.API_POLYGON]:
                    self.register_data_source_for_monitoring(
                        source_type.value, source_type
                    )

            # Register Excel source
            self.register_data_source_for_monitoring("excel", DataSourceType.EXCEL)

    return MonitoredDataManager