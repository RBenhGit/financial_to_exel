"""
Comprehensive tests for the data source health monitoring system.

Tests cover health metrics collection, alerting, reporting, and integration
with existing data management systems.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from core.data_processing.monitoring.health_monitor import (
    DataSourceHealthMonitor,
    HealthMetrics,
    HealthStatus,
    get_health_monitor,
    reset_health_monitor
)
from core.data_processing.monitoring.alerting_system import (
    AlertingSystem,
    Alert,
    AlertSeverity,
    AlertType,
    LogAlertChannel,
    EmailAlertChannel
)
from core.data_processing.monitoring.health_reporter import (
    HealthReporter,
    HealthDashboard
)
from core.data_processing.monitoring.integration_adapter import (
    MonitoringIntegration,
    MonitoredDataManagerMixin,
    MonitoringContext,
    add_monitoring_to_function
)
from core.data_sources.interfaces.data_source_interfaces import (
    DataSourceInterface,
    DataSourceType,
    ExcelDataSource,
    YahooFinanceDataSource
)


class TestDataSourceHealthMonitor:
    """Test the core health monitoring functionality"""

    def setup_method(self):
        """Setup for each test"""
        reset_health_monitor()
        self.monitor = DataSourceHealthMonitor()

        # Create mock data source
        self.mock_source = Mock(spec=DataSourceInterface)
        self.mock_source.get_source_type.return_value = DataSourceType.API_YAHOO
        self.mock_source.health_check.return_value = {
            'available': True,
            'request_count': 10,
            'success_count': 9,
            'success_rate': 0.9,
            'last_error': None
        }

    def test_register_data_source(self):
        """Test registering a data source for monitoring"""
        source_name = "test_source"
        self.monitor.register_data_source(self.mock_source, source_name)

        assert source_name in self.monitor.monitored_sources
        assert self.monitor.monitored_sources[source_name] == self.mock_source

    def test_record_request_cycle(self):
        """Test the complete request recording cycle"""
        source_name = "test_source"
        self.monitor.register_data_source(self.mock_source, source_name)

        # Start request
        timer_id = self.monitor.record_request_start(source_name, "fetch_data")
        assert timer_id.startswith(source_name)

        # Simulate some processing time
        time.sleep(0.01)

        # End request successfully
        self.monitor.record_request_end(
            timer_id=timer_id,
            success=True,
            error=None,
            data_quality_score=0.85,
            metadata={'test': 'data'}
        )

        # Check metrics were updated
        metrics = self.monitor.get_source_health(source_name)
        assert metrics is not None
        assert metrics.source_name == source_name
        assert metrics.data_quality_score == 0.85

    def test_record_failed_request(self):
        """Test recording a failed request"""
        source_name = "test_source"
        self.monitor.register_data_source(self.mock_source, source_name)

        timer_id = self.monitor.record_request_start(source_name)
        test_error = Exception("Test error")

        self.monitor.record_request_end(
            timer_id=timer_id,
            success=False,
            error=test_error,
            data_quality_score=None
        )

        metrics = self.monitor.get_source_health(source_name)
        assert metrics.consecutive_failures > 0
        assert "Exception" in metrics.error_types

    def test_health_status_calculation(self):
        """Test health status determination"""
        # Test healthy status
        metrics = HealthMetrics(
            source_type=DataSourceType.API_YAHOO,
            source_name="test",
            timestamp=datetime.now(),
            response_time_ms=1000,
            success_rate=0.95,
            error_rate=0.05,
            data_quality_score=0.9,
            data_completeness=0.95,
            availability_percentage=98.0,
            consecutive_failures=0,
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )
        assert metrics.health_status == HealthStatus.HEALTHY

        # Test degraded status
        metrics.success_rate = 0.85
        assert metrics.health_status == HealthStatus.DEGRADED

        # Test critical status
        metrics.success_rate = 0.65
        assert metrics.health_status == HealthStatus.CRITICAL

        # Test unavailable status
        metrics.availability_percentage = 40.0
        assert metrics.health_status == HealthStatus.UNAVAILABLE

    def test_health_summary(self):
        """Test overall health summary generation"""
        # Add multiple sources with different health statuses
        sources = {
            "healthy_source": HealthMetrics(
                source_type=DataSourceType.API_YAHOO,
                source_name="healthy_source",
                timestamp=datetime.now(),
                response_time_ms=1000,
                success_rate=0.95,
                error_rate=0.05,
                data_quality_score=0.9,
                data_completeness=0.95,
                availability_percentage=98.0,
                consecutive_failures=0,
                total_requests=100,
                successful_requests=95,
                failed_requests=5
            ),
            "degraded_source": HealthMetrics(
                source_type=DataSourceType.API_FMP,
                source_name="degraded_source",
                timestamp=datetime.now(),
                response_time_ms=6000,
                success_rate=0.85,
                error_rate=0.15,
                data_quality_score=0.7,
                data_completeness=0.8,
                availability_percentage=85.0,
                consecutive_failures=2,
                total_requests=100,
                successful_requests=85,
                failed_requests=15
            )
        }

        self.monitor.current_metrics = sources
        summary = self.monitor.get_health_summary()

        assert summary['sources_count'] == 2
        assert summary['healthy_sources'] == 1
        assert summary['degraded_sources'] == 1
        assert summary['overall_status'] == HealthStatus.DEGRADED.value

    def test_metrics_persistence(self):
        """Test saving and loading metrics"""
        source_name = "test_source"
        self.monitor.register_data_source(self.mock_source, source_name)

        # Create some metrics
        timer_id = self.monitor.record_request_start(source_name)
        self.monitor.record_request_end(timer_id, True, data_quality_score=0.8)

        # Save metrics
        self.monitor._save_metrics()
        assert self.monitor.metrics_file.exists()

        # Create new monitor and load metrics
        new_monitor = DataSourceHealthMonitor()
        success = new_monitor.load_metrics()
        assert success
        assert source_name in new_monitor.current_metrics


class TestAlertingSystem:
    """Test the alerting system functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.alerting_system = AlertingSystem({
            'channels': {
                'log': {'enabled': True},
                'email': {'enabled': False}
            },
            'thresholds': {
                'response_time_ms': 3000,
                'success_rate_min': 0.8,
                'data_quality_min': 0.7
            }
        })

    def test_alert_creation(self):
        """Test alert creation from metrics"""
        metrics = HealthMetrics(
            source_type=DataSourceType.API_YAHOO,
            source_name="slow_source",
            timestamp=datetime.now(),
            response_time_ms=5000,  # Above threshold
            success_rate=0.95,
            error_rate=0.05,
            data_quality_score=0.9,
            data_completeness=0.95,
            availability_percentage=98.0,
            consecutive_failures=0,
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )

        alerts = self.alerting_system.check_metrics_for_alerts(metrics)
        assert len(alerts) > 0

        # Check for response time alert
        response_time_alerts = [
            a for a in alerts if a.alert_type == AlertType.RESPONSE_TIME_HIGH
        ]
        assert len(response_time_alerts) > 0

    def test_alert_suppression(self):
        """Test alert suppression to prevent spam"""
        metrics = HealthMetrics(
            source_type=DataSourceType.API_YAHOO,
            source_name="failing_source",
            timestamp=datetime.now(),
            response_time_ms=1000,
            success_rate=0.5,  # Below threshold
            error_rate=0.5,
            data_quality_score=0.9,
            data_completeness=0.95,
            availability_percentage=50.0,
            consecutive_failures=0,
            total_requests=100,
            successful_requests=50,
            failed_requests=50
        )

        # First check should generate alerts
        alerts1 = self.alerting_system.check_metrics_for_alerts(metrics)
        assert len(alerts1) > 0

        # Second check should be suppressed
        alerts2 = self.alerting_system.check_metrics_for_alerts(metrics)
        assert len(alerts2) == 0

    def test_alert_resolution(self):
        """Test alert resolution"""
        metrics = HealthMetrics(
            source_type=DataSourceType.API_YAHOO,
            source_name="test_source",
            timestamp=datetime.now(),
            response_time_ms=6000,
            success_rate=0.95,
            error_rate=0.05,
            data_quality_score=0.9,
            data_completeness=0.95,
            availability_percentage=98.0,
            consecutive_failures=0,
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )

        alerts = self.alerting_system.check_metrics_for_alerts(metrics)
        assert len(alerts) > 0

        alert_id = alerts[0].alert_id
        success = self.alerting_system.resolve_alert(alert_id, "Fixed by optimization")
        assert success

        # Alert should no longer be active
        active_alerts = self.alerting_system.get_active_alerts()
        active_ids = [a.alert_id for a in active_alerts]
        assert alert_id not in active_ids

    def test_log_alert_channel(self):
        """Test log alert channel"""
        channel = LogAlertChannel({'enabled': True})

        alert = Alert(
            alert_id="test_alert",
            alert_type=AlertType.RESPONSE_TIME_HIGH,
            severity=AlertSeverity.WARNING,
            source_name="test_source",
            message="Test alert message",
            timestamp=datetime.now(),
            metrics=Mock()
        )

        with patch('logging.Logger.log') as mock_log:
            success = channel.send_alert(alert)
            assert success
            mock_log.assert_called_once()

    def test_email_alert_channel(self):
        """Test email alert channel"""
        config = {
            'enabled': True,
            'smtp_server': 'localhost',
            'smtp_port': 587,
            'to_emails': ['test@example.com'],
            'from_email': 'alerts@test.com'
        }
        channel = EmailAlertChannel(config)

        alert = Alert(
            alert_id="test_alert",
            alert_type=AlertType.RESPONSE_TIME_HIGH,
            severity=AlertSeverity.CRITICAL,
            source_name="test_source",
            message="Test critical alert",
            timestamp=datetime.now(),
            metrics=Mock()
        )

        # Mock SMTP to avoid actual email sending
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            success = channel.send_alert(alert)
            assert success
            mock_server.send_message.assert_called_once()


class TestHealthReporter:
    """Test health reporting functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.health_monitor = Mock(spec=DataSourceHealthMonitor)
        self.alerting_system = Mock(spec=AlertingSystem)
        self.reporter = HealthReporter(self.health_monitor, self.alerting_system)

        # Setup mock data
        self.mock_metrics = {
            'test_source': HealthMetrics(
                source_type=DataSourceType.API_YAHOO,
                source_name="test_source",
                timestamp=datetime.now(),
                response_time_ms=1500,
                success_rate=0.92,
                error_rate=0.08,
                data_quality_score=0.85,
                data_completeness=0.9,
                availability_percentage=92.0,
                consecutive_failures=1,
                total_requests=100,
                successful_requests=92,
                failed_requests=8
            )
        }

        self.health_monitor.get_all_health_metrics.return_value = self.mock_metrics
        self.health_monitor.get_health_summary.return_value = {
            'overall_status': 'healthy',
            'average_score': 85.5,
            'sources_count': 1,
            'healthy_sources': 1,
            'degraded_sources': 0,
            'critical_sources': 0
        }
        self.alerting_system.get_active_alerts.return_value = []
        self.alerting_system.get_alert_summary.return_value = {
            'total_active_alerts': 0,
            'severity_breakdown': {}
        }

    def test_generate_json_report(self):
        """Test JSON report generation"""
        report = self.reporter.generate_health_report(format='json', hours=24)

        assert 'report_metadata' in report
        assert 'system_health_summary' in report
        assert 'data_sources' in report
        assert 'active_alerts' in report
        assert report['report_metadata']['format'] == 'json'

    def test_generate_html_report(self):
        """Test HTML report generation"""
        report = self.reporter.generate_health_report(format='html', hours=24)

        assert isinstance(report, str)
        assert '<html>' in report
        assert 'Data Source Health Report' in report
        assert 'test_source' in report

    def test_performance_insights(self):
        """Test performance insights generation"""
        insights = self.reporter._generate_performance_insights(self.mock_metrics)

        assert 'avg_response_time_ms' in insights
        assert 'avg_success_rate' in insights
        assert 'best_performing_source' in insights
        assert insights['sources_healthy'] >= 0

    def test_recommendations_generation(self):
        """Test recommendations generation"""
        # Create metrics with issues to trigger recommendations
        problematic_metrics = {
            'slow_source': HealthMetrics(
                source_type=DataSourceType.API_YAHOO,
                source_name="slow_source",
                timestamp=datetime.now(),
                response_time_ms=8000,  # Slow
                success_rate=0.7,  # Low success rate
                error_rate=0.3,
                data_quality_score=0.6,  # Poor quality
                data_completeness=0.7,
                availability_percentage=70.0,
                consecutive_failures=5,  # Many failures
                total_requests=100,
                successful_requests=70,
                failed_requests=30
            )
        }

        recommendations = self.reporter._generate_recommendations(problematic_metrics, [])
        assert len(recommendations) > 0
        assert any('slow' in rec.lower() for rec in recommendations)

    def test_export_report(self):
        """Test report export functionality"""
        temp_file = Path("/tmp/test_health_report.json")

        # Clean up any existing file
        if temp_file.exists():
            temp_file.unlink()

        try:
            success = self.reporter.export_report(str(temp_file), format='json')
            assert success
            assert temp_file.exists()

            # Verify content
            with open(temp_file, 'r') as f:
                data = json.load(f)
            assert 'report_metadata' in data

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()


class TestMonitoringIntegration:
    """Test monitoring integration with data managers"""

    def setup_method(self):
        """Setup for each test"""
        reset_health_monitor()
        self.integration = MonitoringIntegration()

    def test_monitoring_decorator(self):
        """Test the monitoring decorator"""
        call_count = 0

        @self.integration.monitor_data_source_call("test_source", "test_operation")
        def test_function(data):
            nonlocal call_count
            call_count += 1
            return {"processed": True, "data": data}

        result = test_function("test_data")
        assert result["processed"] is True
        assert call_count == 1

        # Check that metrics were recorded
        metrics = self.integration.health_monitor.get_source_health("test_source")
        assert metrics is not None

    def test_monitoring_decorator_with_exception(self):
        """Test monitoring decorator handles exceptions"""
        @self.integration.monitor_data_source_call("failing_source", "test_operation")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Check that failure was recorded
        metrics = self.integration.health_monitor.get_source_health("failing_source")
        assert metrics is not None
        assert metrics.consecutive_failures > 0

    def test_monitoring_context_manager(self):
        """Test monitoring context manager"""
        with MonitoringContext("context_source", "test_operation") as monitor:
            monitor.set_data_quality(0.85)
            monitor.add_metadata("test_key", "test_value")
            # Simulate some work
            time.sleep(0.01)

        # Check that metrics were recorded
        health_monitor = get_health_monitor()
        metrics = health_monitor.get_source_health("context_source")
        assert metrics is not None

    def test_monitoring_context_with_exception(self):
        """Test monitoring context manager with exception"""
        try:
            with MonitoringContext("failing_context_source", "test_operation"):
                raise RuntimeError("Context test error")
        except RuntimeError:
            pass

        # Check that failure was recorded
        health_monitor = get_health_monitor()
        metrics = health_monitor.get_source_health("failing_context_source")
        assert metrics is not None
        assert metrics.consecutive_failures > 0

    def test_monitored_data_manager_mixin(self):
        """Test the monitored data manager mixin"""

        class TestDataManager(MonitoredDataManagerMixin):
            def __init__(self):
                super().__init__()

        manager = TestDataManager()

        # Test source registration
        manager.register_data_source_for_monitoring(
            "test_source",
            DataSourceType.API_YAHOO
        )

        assert "test_source" in manager._registered_sources

        # Test health status retrieval
        status = manager.get_health_status("test_source")
        assert isinstance(status, dict)

    def test_standalone_monitoring_decorator(self):
        """Test standalone monitoring decorator"""
        @add_monitoring_to_function("standalone_source", "standalone_operation")
        def standalone_function(x, y):
            return x + y

        result = standalone_function(2, 3)
        assert result == 5

        # Check that metrics were recorded
        health_monitor = get_health_monitor()
        metrics = health_monitor.get_source_health("standalone_source")
        assert metrics is not None


class TestIntegrationWithExistingCode:
    """Test integration with existing data management code"""

    def test_enhanced_data_manager_integration(self):
        """Test that enhanced data manager can be monitored"""
        # This test would require the actual EnhancedDataManager class
        # and would test that it properly integrates with monitoring
        pass

    def test_financial_calculator_integration(self):
        """Test monitoring integration with financial calculator"""
        # This would test integration with the FinancialCalculator class
        pass


# Integration test that requires actual components
@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world monitoring scenarios"""

    def test_complete_monitoring_workflow(self):
        """Test complete monitoring workflow from data fetch to alerting"""
        # This would test the complete workflow:
        # 1. Data source registration
        # 2. Data fetching with monitoring
        # 3. Health metrics collection
        # 4. Alert generation
        # 5. Report generation
        pass

    def test_multiple_data_sources_monitoring(self):
        """Test monitoring multiple data sources simultaneously"""
        pass

    def test_alert_escalation_workflow(self):
        """Test alert escalation and resolution workflow"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])