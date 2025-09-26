"""
Test suite for the Enhanced User Journey Testing Framework

This module tests the enhanced framework capabilities including Playwright integration,
monitoring system, and CI/CD features.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sqlite3

# Import the enhanced framework components
from enhanced_user_journey_framework import (
    EnhancedUserJourneyTestFramework,
    AutomationMode,
    PerformanceMetrics,
    ScreenshotComparison,
    EnhancedTestResult,
    TestStatus,
    TestPriority
)
from monitoring_system import (
    MonitoringSystem,
    MonitoringIntegration,
    AlertLevel,
    SessionMetric,
    Alert
)
from user_journey_testing_framework import TestScenario, UserAction


class TestEnhancedFramework:
    """Test cases for enhanced user journey framework."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def enhanced_framework(self, temp_dir):
        """Create enhanced framework instance for testing."""
        framework = EnhancedUserJourneyTestFramework(
            base_url="http://localhost:8501",
            headless=True,
            browser_type="chromium",
            screenshots_dir=str(temp_dir / "screenshots"),
            baseline_screenshots_dir=str(temp_dir / "baselines")
        )
        return framework

    @pytest.fixture
    def sample_scenario(self):
        """Create a sample test scenario for testing."""
        return TestScenario(
            scenario_id="test_001",
            title="Sample Test Scenario",
            description="A test scenario for framework validation",
            priority=TestPriority.HIGH,
            user_persona="Test User",
            preconditions=["Application is running"],
            actions=[
                UserAction("navigate", "Application homepage"),
                UserAction("validate", "Page loaded successfully")
            ],
            success_criteria=["Page loads without errors"],
            estimated_duration=2,
            data_requirements=["Test data"],
            tags=["test", "validation"]
        )

    def test_framework_initialization(self, temp_dir):
        """Test enhanced framework initialization."""
        framework = EnhancedUserJourneyTestFramework(
            base_url="http://test.example.com",
            headless=True,
            browser_type="firefox",
            screenshots_dir=str(temp_dir / "screenshots"),
            baseline_screenshots_dir=str(temp_dir / "baselines")
        )

        assert framework.base_url == "http://test.example.com"
        assert framework.headless is True
        assert framework.browser_type == "firefox"
        assert framework.screenshots_dir == temp_dir / "screenshots"
        assert framework.baseline_screenshots_dir == temp_dir / "baselines"

        # Check directories were created
        assert framework.screenshots_dir.exists()
        assert framework.baseline_screenshots_dir.exists()

    def test_performance_thresholds(self, enhanced_framework):
        """Test performance thresholds configuration."""
        thresholds = enhanced_framework.performance_thresholds

        assert "page_load_time" in thresholds
        assert "memory_usage_mb" in thresholds
        assert "cpu_usage_percent" in thresholds

        assert thresholds["page_load_time"] > 0
        assert thresholds["memory_usage_mb"] > 0
        assert thresholds["cpu_usage_percent"] > 0

    @pytest.mark.asyncio
    async def test_browser_setup_fallback(self, enhanced_framework):
        """Test browser setup fallback when Playwright unavailable."""
        with patch('enhanced_user_journey_framework.PLAYWRIGHT_AVAILABLE', False):
            result = await enhanced_framework.setup_browser()
            assert result is False

    def test_automation_mode_execution(self, enhanced_framework, sample_scenario):
        """Test different automation modes."""
        # Test manual mode
        result = enhanced_framework.execute_scenario_with_mode(
            sample_scenario, AutomationMode.MANUAL
        )
        assert isinstance(result, EnhancedTestResult)

        # Test semi-automated mode
        result = enhanced_framework.execute_scenario_with_mode(
            sample_scenario, AutomationMode.SEMI_AUTOMATED
        )
        assert isinstance(result, EnhancedTestResult)

    def test_performance_metrics_creation(self):
        """Test performance metrics data structure."""
        metrics = PerformanceMetrics(
            page_load_time=2.5,
            memory_usage_mb=150.0,
            cpu_usage_percent=45.0,
            network_requests=10,
            javascript_errors=["Sample error"]
        )

        assert metrics.page_load_time == 2.5
        assert metrics.memory_usage_mb == 150.0
        assert metrics.cpu_usage_percent == 45.0
        assert metrics.network_requests == 10
        assert len(metrics.javascript_errors) == 1

    def test_screenshot_comparison_creation(self):
        """Test screenshot comparison data structure."""
        comparison = ScreenshotComparison(
            baseline_path="/path/to/baseline.png",
            current_path="/path/to/current.png",
            diff_path="/path/to/diff.png",
            similarity_score=0.95,
            pixel_diff_count=1000,
            total_pixels=1920000,
            is_match=True
        )

        assert comparison.baseline_path == "/path/to/baseline.png"
        assert comparison.similarity_score == 0.95
        assert comparison.is_match is True

    def test_enhanced_test_result(self, sample_scenario):
        """Test enhanced test result with additional data."""
        performance_metrics = PerformanceMetrics(
            page_load_time=3.0,
            memory_usage_mb=200.0
        )

        result = EnhancedTestResult(
            scenario_id=sample_scenario.scenario_id,
            status=TestStatus.PASSED,
            start_time=datetime.now(),
            performance_metrics=performance_metrics
        )

        assert result.scenario_id == sample_scenario.scenario_id
        assert result.status == TestStatus.PASSED
        assert result.performance_metrics.page_load_time == 3.0
        assert len(result.screenshot_comparisons) == 0
        assert len(result.automation_log) == 0

    def test_ci_cd_config_generation(self, enhanced_framework, temp_dir):
        """Test CI/CD configuration generation."""
        config_file = temp_dir / "test_config.yml"
        enhanced_framework.generate_ci_cd_config(str(config_file))

        assert config_file.exists()

        # Check config content
        with open(config_file, 'r') as f:
            content = f.read()

        assert "User Acceptance Test Automation" in content
        assert "playwright install" in content
        assert "pytest tests/user_acceptance/" in content

    def test_enhanced_report_generation(self, enhanced_framework, sample_scenario):
        """Test enhanced report generation with automation data."""
        # Create sample enhanced results
        results = [
            EnhancedTestResult(
                scenario_id=sample_scenario.scenario_id,
                status=TestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                performance_metrics=PerformanceMetrics(
                    page_load_time=2.5,
                    memory_usage_mb=150.0,
                    javascript_errors=[]
                )
            )
        ]

        report = enhanced_framework.generate_enhanced_test_report(results)

        assert "Enhanced User Acceptance Testing Report" in report
        assert "Performance Summary" in report
        assert "Automation Statistics" in report
        assert "2.50s" in report  # Page load time
        assert "150.0 MB" in report  # Memory usage


class TestMonitoringSystem:
    """Test cases for the monitoring system."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_monitoring.db"
        return str(db_path)

    @pytest.fixture
    def monitoring_system(self, temp_db):
        """Create monitoring system instance for testing."""
        return MonitoringSystem(
            db_path=temp_db,
            metrics_retention_days=7,
            alert_thresholds={
                "page_load_time": 5.0,
                "memory_usage_mb": 500.0,
                "cpu_usage_percent": 80.0
            }
        )

    def test_monitoring_system_initialization(self, temp_db):
        """Test monitoring system initialization."""
        system = MonitoringSystem(db_path=temp_db)

        assert system.db_path == temp_db
        assert system.metrics_retention_days == 30
        assert isinstance(system.alert_thresholds, dict)

        # Check database was created
        assert Path(temp_db).exists()

        # Check tables were created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        assert "session_metrics" in tables
        assert "alerts" in tables
        assert "sessions" in tables

    def test_session_management(self, monitoring_system):
        """Test session start and end functionality."""
        session_id = "test_session_001"
        metadata = {"user_type": "test", "browser": "chrome"}

        # Start session
        monitoring_system.start_session(session_id, metadata)
        assert session_id in monitoring_system.active_sessions

        session_data = monitoring_system.active_sessions[session_id]
        assert session_data["metadata"] == metadata
        assert session_data["metrics_count"] == 0

        # End session
        monitoring_system.end_session(session_id)
        assert session_id not in monitoring_system.active_sessions

    def test_metric_recording(self, monitoring_system):
        """Test metric recording functionality."""
        session_id = "test_session_002"
        monitoring_system.start_session(session_id)

        # Record metrics
        monitoring_system.record_metric(session_id, "page_load_time", 3.5)
        monitoring_system.record_metric(session_id, "memory_usage_mb", 200.0, {"test": "data"})

        # Allow time for processing
        import time
        time.sleep(1)

        # Check metrics were stored
        metrics = monitoring_system.get_session_metrics(session_id, hours=1)
        assert len(metrics) >= 2

        page_load_metrics = [m for m in metrics if m.metric_type == "page_load_time"]
        assert len(page_load_metrics) >= 1
        assert page_load_metrics[0].value == 3.5

    def test_alert_generation(self, monitoring_system):
        """Test alert generation from metrics."""
        session_id = "test_session_003"
        monitoring_system.start_session(session_id)

        # Record metric that should trigger alert (threshold is 5.0)
        monitoring_system.record_metric(session_id, "page_load_time", 8.0)

        # Allow time for processing
        import time
        time.sleep(2)

        # Check alerts were generated
        recent_alerts = monitoring_system.get_recent_alerts(hours=1)
        page_load_alerts = [a for a in recent_alerts if "page_load_time" in a.title]

        assert len(page_load_alerts) >= 1
        alert = page_load_alerts[0]
        assert alert.level in [AlertLevel.WARNING, AlertLevel.ERROR]
        assert "8.00" in alert.description

    def test_monitoring_integration(self, monitoring_system):
        """Test monitoring integration class."""
        integration = MonitoringIntegration(monitoring_system)

        # Start test session
        session_id = integration.start_test_session(
            "test_integration",
            {"test_type": "integration"}
        )

        assert integration.current_session_id == session_id
        assert session_id in monitoring_system.active_sessions

        # Record test metrics
        integration.record_test_metric("test_duration", 45.0)
        integration.record_test_metric("assertions_passed", 10.0)

        # End session
        integration.end_test_session()
        assert integration.current_session_id is None

    def test_monitoring_report_generation(self, monitoring_system):
        """Test monitoring report generation."""
        session_id = "test_session_report"
        monitoring_system.start_session(session_id)

        # Record sample metrics
        monitoring_system.record_metric(session_id, "page_load_time", 2.5)
        monitoring_system.record_metric(session_id, "memory_usage_mb", 150.0)
        monitoring_system.record_metric(session_id, "cpu_usage_percent", 45.0)

        # Allow processing
        import time
        time.sleep(1)

        # Generate report
        report = monitoring_system.generate_monitoring_report(hours=1)

        assert "report_period" in report
        assert "session_statistics" in report
        assert "metric_statistics" in report
        assert "alert_statistics" in report
        assert "system_health" in report

        # Check session statistics
        session_stats = report["session_statistics"]
        assert session_stats["total_sessions"] >= 1
        assert session_stats["active_sessions"] >= 1

    def test_session_metrics_retrieval(self, monitoring_system):
        """Test retrieving metrics for specific sessions."""
        session_id = "test_metrics_retrieval"
        monitoring_system.start_session(session_id)

        # Record different types of metrics
        monitoring_system.record_metric(session_id, "page_load_time", 2.0)
        monitoring_system.record_metric(session_id, "api_response_time", 500.0)
        monitoring_system.record_metric(session_id, "memory_usage_mb", 100.0)

        # Allow processing
        import time
        time.sleep(1)

        # Test retrieving all metrics
        all_metrics = monitoring_system.get_session_metrics(session_id, hours=1)
        assert len(all_metrics) >= 3

        # Test filtering by metric type
        page_load_metrics = monitoring_system.get_session_metrics(
            session_id, metric_types=["page_load_time"], hours=1
        )
        assert len(page_load_metrics) >= 1
        assert all(m.metric_type == "page_load_time" for m in page_load_metrics)


class TestFrameworkIntegration:
    """Integration tests for enhanced framework with monitoring."""

    @pytest.fixture
    def integrated_system(self, tmp_path):
        """Create integrated framework and monitoring system."""
        framework = EnhancedUserJourneyTestFramework(
            base_url="http://localhost:8501",
            screenshots_dir=str(tmp_path / "screenshots"),
            baseline_screenshots_dir=str(tmp_path / "baselines")
        )

        monitoring = MonitoringSystem(db_path=str(tmp_path / "monitoring.db"))
        integration = MonitoringIntegration(monitoring)

        return framework, integration

    def test_integrated_scenario_execution(self, integrated_system):
        """Test scenario execution with integrated monitoring."""
        framework, monitoring_integration = integrated_system

        # Create a sample scenario for testing
        sample_scenario = TestScenario(
            scenario_id="integration_test_001",
            title="Integration Test Scenario",
            description="Test scenario for integration testing",
            priority=TestPriority.HIGH,
            user_persona="Test User",
            preconditions=["System ready"],
            actions=[UserAction("validate", "System works")],
            success_criteria=["Test passes"],
            estimated_duration=1,
            data_requirements=[],
            tags=["integration"]
        )

        # Start monitoring session
        session_id = monitoring_integration.start_test_session(
            sample_scenario.scenario_id,
            {"scenario_title": sample_scenario.title}
        )

        # Record start metric
        monitoring_integration.record_test_metric("scenario_started", 1.0)

        # Execute scenario
        result = framework.execute_scenario_with_mode(
            sample_scenario, AutomationMode.MANUAL
        )

        # Record completion metric
        monitoring_integration.record_test_metric(
            "scenario_completed",
            1.0,
            {"status": result.status.value if hasattr(result.status, 'value') else str(result.status)}
        )

        # End monitoring session
        monitoring_integration.end_test_session()

        # Verify integration worked
        assert isinstance(result, EnhancedTestResult)
        assert session_id is not None


@pytest.mark.integration
class TestRealApplicationIntegration:
    """Integration tests with real application (if available)."""

    @pytest.fixture
    def app_available(self):
        """Check if application is available for testing."""
        import requests
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            return response.status_code == 200
        except:
            return False

    @pytest.mark.skipif(True, reason="Application not available for testing")
    def test_real_app_navigation(self, enhanced_framework):
        """Test navigation to real application."""
        # This test would only run if the Streamlit app is running
        # It's marked as integration and can be skipped in unit testing

        async def test_navigation():
            if await enhanced_framework.setup_browser():
                try:
                    await enhanced_framework.page.goto("http://localhost:8501")
                    title = await enhanced_framework.page.title()
                    assert title is not None
                    return True
                finally:
                    await enhanced_framework.cleanup_browser()
            return False

        # Only run if Playwright is available
        if enhanced_framework.playwright:
            result = asyncio.run(test_navigation())
            assert result is True


def test_framework_compatibility():
    """Test that enhanced framework maintains compatibility with base framework."""
    from user_journey_testing_framework import UserJourneyTestFramework

    # Test that enhanced framework inherits properly
    enhanced = EnhancedUserJourneyTestFramework()
    base = UserJourneyTestFramework()

    # Check that enhanced has all base methods
    base_methods = [method for method in dir(base) if not method.startswith('_')]
    enhanced_methods = [method for method in dir(enhanced) if not method.startswith('_')]

    for method in base_methods:
        assert method in enhanced_methods, f"Enhanced framework missing base method: {method}"

    # Check scenario compatibility
    assert len(enhanced.test_scenarios) == len(base.test_scenarios)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])