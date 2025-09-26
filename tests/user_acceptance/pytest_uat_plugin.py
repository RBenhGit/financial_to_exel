"""
Pytest Plugin for Enhanced User Acceptance Testing

This pytest plugin integrates the enhanced user journey testing framework
with pytest for seamless CI/CD pipeline integration.
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from enhanced_user_journey_framework import (
    EnhancedUserJourneyTestFramework,
    AutomationMode,
    EnhancedTestResult,
    TestStatus,
    TestPriority
)
from monitoring_system import MonitoringSystem, MonitoringIntegration


def pytest_addoption(parser):
    """Add custom command line options for UAT."""
    group = parser.getgroup("uat", "User Acceptance Testing")

    group.addoption(
        "--uat-automated",
        action="store_true",
        default=False,
        help="Run UAT tests in fully automated mode using Playwright"
    )

    group.addoption(
        "--uat-semi-automated",
        action="store_true",
        default=False,
        help="Run UAT tests in semi-automated mode"
    )

    group.addoption(
        "--uat-priority",
        action="store",
        default=None,
        choices=["critical", "high", "medium", "low"],
        help="Only run UAT tests with specified priority"
    )

    group.addoption(
        "--uat-tags",
        action="store",
        default=None,
        help="Run UAT tests matching specified tags (comma-separated)"
    )

    group.addoption(
        "--uat-base-url",
        action="store",
        default="http://localhost:8501",
        help="Base URL for the application under test"
    )

    group.addoption(
        "--uat-headless",
        action="store_true",
        default=True,
        help="Run browser tests in headless mode"
    )

    group.addoption(
        "--uat-browser",
        action="store",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use for automated testing"
    )

    group.addoption(
        "--uat-monitoring",
        action="store_true",
        default=False,
        help="Enable real-time monitoring during tests"
    )

    group.addoption(
        "--uat-screenshots",
        action="store_true",
        default=False,
        help="Capture screenshots during test execution"
    )


def pytest_configure(config):
    """Configure pytest with UAT-specific settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "uat: mark test as a user acceptance test"
    )
    config.addinivalue_line(
        "markers", "uat_critical: mark UAT test as critical priority"
    )
    config.addinivalue_line(
        "markers", "uat_automated: mark UAT test for automation"
    )
    config.addinivalue_line(
        "markers", "uat_manual: mark UAT test as manual only"
    )


@pytest.fixture(scope="session")
def uat_framework(request):
    """Create UAT framework instance for the test session."""
    config = request.config

    framework = EnhancedUserJourneyTestFramework(
        base_url=config.getoption("--uat-base-url"),
        headless=config.getoption("--uat-headless"),
        browser_type=config.getoption("--uat-browser"),
        screenshots_dir="test_results/screenshots",
        baseline_screenshots_dir="test_baselines/screenshots"
    )

    return framework


@pytest.fixture(scope="session")
def uat_monitoring(request):
    """Create monitoring system for UAT tests."""
    if not request.config.getoption("--uat-monitoring"):
        return None

    monitoring = MonitoringSystem(
        db_path="test_results/uat_monitoring.db",
        metrics_retention_days=7
    )

    return MonitoringIntegration(monitoring)


@pytest.fixture
def uat_session(uat_monitoring, request):
    """Create monitoring session for individual UAT test."""
    if not uat_monitoring:
        yield None
        return

    test_name = request.node.name
    session_id = uat_monitoring.start_test_session(
        test_name,
        {
            "test_module": request.node.module.__name__ if request.node.module else "unknown",
            "test_class": request.node.cls.__name__ if request.node.cls else None,
            "pytest_markers": [mark.name for mark in request.node.iter_markers()]
        }
    )

    yield uat_monitoring

    uat_monitoring.end_test_session()


class UATTestCollector:
    """Collect and run UAT scenarios as pytest tests."""

    def __init__(self, framework: EnhancedUserJourneyTestFramework, config):
        self.framework = framework
        self.config = config

    def collect_uat_scenarios(self):
        """Collect UAT scenarios based on configuration."""
        scenarios = self.framework.test_scenarios

        # Filter by priority
        priority_filter = self.config.getoption("--uat-priority")
        if priority_filter:
            priority_enum = TestPriority(priority_filter)
            scenarios = [s for s in scenarios if s.priority == priority_enum]

        # Filter by tags
        tags_filter = self.config.getoption("--uat-tags")
        if tags_filter:
            tags = [tag.strip() for tag in tags_filter.split(",")]
            scenarios = [s for s in scenarios if any(tag in s.tags for tag in tags)]

        return scenarios

    def create_test_function(self, scenario, automation_mode: AutomationMode):
        """Create a pytest test function for a UAT scenario."""

        def test_scenario(uat_framework, uat_session):
            """Execute UAT scenario."""
            # Record test start if monitoring enabled
            if uat_session:
                uat_session.record_test_metric("test_started", 1.0, {
                    "scenario_id": scenario.scenario_id,
                    "scenario_title": scenario.title,
                    "automation_mode": automation_mode.value
                })

            # Execute the scenario
            if automation_mode == AutomationMode.FULLY_AUTOMATED:
                result = asyncio.run(uat_framework.execute_automated_scenario(scenario))
            else:
                result = uat_framework.execute_scenario_with_mode(scenario, automation_mode)

            # Record test completion
            if uat_session:
                uat_session.record_test_metric("test_completed", 1.0, {
                    "scenario_id": scenario.scenario_id,
                    "test_status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                    "execution_time": (result.end_time - result.start_time).total_seconds() if result.end_time else None
                })

                # Record performance metrics if available
                if hasattr(result, 'performance_metrics') and result.performance_metrics:
                    pm = result.performance_metrics
                    if pm.page_load_time:
                        uat_session.record_test_metric("page_load_time", pm.page_load_time)
                    if pm.memory_usage_mb:
                        uat_session.record_test_metric("memory_usage_mb", pm.memory_usage_mb)

            # Assert test passed
            assert result.status == TestStatus.PASSED, f"UAT scenario failed: {result.error_message or 'Unknown error'}"

            # Store result for reporting
            if not hasattr(test_scenario, '_uat_results'):
                test_scenario._uat_results = []
            test_scenario._uat_results.append(result)

        # Set test metadata
        test_scenario.__name__ = f"test_uat_{scenario.scenario_id}_{scenario.title.lower().replace(' ', '_')}"
        test_scenario.__doc__ = f"UAT: {scenario.title}\n\n{scenario.description}"

        # Add pytest markers
        markers = [
            pytest.mark.uat,
            pytest.mark.uat_automated if automation_mode == AutomationMode.FULLY_AUTOMATED else pytest.mark.uat_manual
        ]

        if scenario.priority == TestPriority.CRITICAL:
            markers.append(pytest.mark.uat_critical)

        for tag in scenario.tags:
            markers.append(getattr(pytest.mark, f"uat_{tag}"))

        for marker in markers:
            test_scenario = marker(test_scenario)

        return test_scenario


def pytest_generate_tests(metafunc):
    """Generate parametrized tests for UAT scenarios."""
    if "uat_scenario" in metafunc.fixturenames:
        # Get framework and collect scenarios
        framework = EnhancedUserJourneyTestFramework()
        collector = UATTestCollector(framework, metafunc.config)
        scenarios = collector.collect_uat_scenarios()

        # Determine automation mode
        if metafunc.config.getoption("--uat-automated"):
            automation_mode = AutomationMode.FULLY_AUTOMATED
        elif metafunc.config.getoption("--uat-semi-automated"):
            automation_mode = AutomationMode.SEMI_AUTOMATED
        else:
            automation_mode = AutomationMode.MANUAL

        # Parametrize with scenarios
        metafunc.parametrize(
            "uat_scenario,automation_mode",
            [(scenario, automation_mode) for scenario in scenarios],
            ids=[f"{s.scenario_id}_{s.title}" for s in scenarios]
        )


def pytest_runtest_setup(item):
    """Set up individual test runs."""
    # Create test results directory
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)

    # Set up logging for UAT tests
    if "uat" in [mark.name for mark in item.iter_markers()]:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(results_dir / "uat_test.log"),
                logging.StreamHandler()
            ]
        )


def pytest_runtest_teardown(item, nextitem):
    """Clean up after test runs."""
    # Save screenshots if test failed and screenshots were captured
    if item.session.config.getoption("--uat-screenshots"):
        if hasattr(item, 'rep_call') and item.rep_call.failed:
            # Additional cleanup for failed tests
            pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate terminal summary for UAT tests."""
    if not any(config.getoption(opt) for opt in ["--uat-automated", "--uat-semi-automated"]):
        return

    # Collect UAT test results
    uat_results = []
    for item in terminalreporter.stats.get('passed', []):
        if hasattr(item, '_uat_results'):
            uat_results.extend(item._uat_results)

    for item in terminalreporter.stats.get('failed', []):
        if hasattr(item, '_uat_results'):
            uat_results.extend(item._uat_results)

    if not uat_results:
        return

    # Generate summary
    terminalreporter.write_sep("=", "User Acceptance Testing Summary")

    total_scenarios = len(uat_results)
    passed_scenarios = len([r for r in uat_results if r.status == TestStatus.PASSED])
    success_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0

    terminalreporter.write_line(f"Total UAT Scenarios: {total_scenarios}")
    terminalreporter.write_line(f"Passed: {passed_scenarios}")
    terminalreporter.write_line(f"Success Rate: {success_rate:.1f}%")

    # Performance summary
    if any(hasattr(r, 'performance_metrics') for r in uat_results):
        avg_load_time = sum(
            r.performance_metrics.page_load_time or 0
            for r in uat_results if hasattr(r, 'performance_metrics')
        ) / len(uat_results)

        terminalreporter.write_line(f"Average Page Load Time: {avg_load_time:.2f}s")

    # Save detailed report
    report_path = Path("test_results") / f"uat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    detailed_report = {
        "summary": {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "success_rate": success_rate,
            "execution_time": datetime.now().isoformat()
        },
        "scenarios": [
            {
                "scenario_id": r.scenario_id,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "start_time": r.start_time.isoformat(),
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "error_message": r.error_message,
                "performance_metrics": {
                    "page_load_time": r.performance_metrics.page_load_time,
                    "memory_usage_mb": r.performance_metrics.memory_usage_mb,
                    "javascript_errors": len(r.performance_metrics.javascript_errors or [])
                } if hasattr(r, 'performance_metrics') and r.performance_metrics else None
            }
            for r in uat_results
        ]
    }

    with open(report_path, 'w') as f:
        json.dump(detailed_report, f, indent=2)

    terminalreporter.write_line(f"Detailed report saved to: {report_path}")


# Test function that uses the parametrized scenarios
def test_uat_scenario_execution(uat_framework, uat_session, uat_scenario, automation_mode):
    """
    Execute a UAT scenario with specified automation mode.

    This function is parametrized by pytest_generate_tests to create
    individual tests for each UAT scenario.
    """
    # Record test start if monitoring enabled
    if uat_session:
        uat_session.record_test_metric("test_started", 1.0, {
            "scenario_id": uat_scenario.scenario_id,
            "scenario_title": uat_scenario.title,
            "automation_mode": automation_mode.value
        })

    # Execute the scenario
    result = uat_framework.execute_scenario_with_mode(uat_scenario, automation_mode)

    # Record test completion
    if uat_session:
        uat_session.record_test_metric("test_completed", 1.0, {
            "scenario_id": uat_scenario.scenario_id,
            "test_status": result.status.value if hasattr(result.status, 'value') else str(result.status),
            "execution_time": (result.end_time - result.start_time).total_seconds() if result.end_time else None
        })

        # Record performance metrics if available
        if hasattr(result, 'performance_metrics') and result.performance_metrics:
            pm = result.performance_metrics
            if pm.page_load_time:
                uat_session.record_test_metric("page_load_time", pm.page_load_time)
            if pm.memory_usage_mb:
                uat_session.record_test_metric("memory_usage_mb", pm.memory_usage_mb)

    # Assert test passed
    assert result.status == TestStatus.PASSED, f"UAT scenario failed: {result.error_message or 'Unknown error'}"

    return result


# Standalone test class for backwards compatibility
class TestUserAcceptanceScenarios:
    """Test class containing all UAT scenarios."""

    @pytest.mark.uat
    @pytest.mark.uat_critical
    def test_critical_user_journeys(self, uat_framework, uat_session):
        """Run all critical UAT scenarios."""
        critical_scenarios = uat_framework.get_scenarios_by_priority(TestPriority.CRITICAL)

        results = []
        for scenario in critical_scenarios:
            if uat_session:
                uat_session.record_test_metric("scenario_started", 1.0, {"scenario_id": scenario.scenario_id})

            result = uat_framework.execute_scenario(scenario, automated=False)
            results.append(result)

            if uat_session:
                uat_session.record_test_metric("scenario_completed", 1.0, {
                    "scenario_id": scenario.scenario_id,
                    "status": result.status.value if hasattr(result.status, 'value') else str(result.status)
                })

        # Assert all critical scenarios passed
        failed_scenarios = [r for r in results if r.status != TestStatus.PASSED]
        assert not failed_scenarios, f"Critical scenarios failed: {[r.scenario_id for r in failed_scenarios]}"

    @pytest.mark.uat
    @pytest.mark.uat_automated
    @pytest.mark.skipif(not EnhancedUserJourneyTestFramework().playwright, reason="Playwright not available")
    def test_automated_user_journeys(self, uat_framework, uat_session):
        """Run automated UAT scenarios using Playwright."""
        scenarios = uat_framework.get_scenarios_by_tags(["core_functionality"])

        async def run_automated_scenarios():
            results = []
            for scenario in scenarios:
                if uat_session:
                    uat_session.record_test_metric("automated_scenario_started", 1.0, {"scenario_id": scenario.scenario_id})

                result = await uat_framework.execute_automated_scenario(scenario)
                results.append(result)

                if uat_session:
                    uat_session.record_test_metric("automated_scenario_completed", 1.0, {
                        "scenario_id": scenario.scenario_id,
                        "status": result.status.value if hasattr(result.status, 'value') else str(result.status)
                    })

            return results

        results = asyncio.run(run_automated_scenarios())

        # Assert all automated scenarios passed
        failed_scenarios = [r for r in results if r.status != TestStatus.PASSED]
        assert not failed_scenarios, f"Automated scenarios failed: {[r.scenario_id for r in failed_scenarios]}"


if __name__ == "__main__":
    # Allow running as standalone script for testing
    pytest.main([__file__, "-v", "--uat-automated"])