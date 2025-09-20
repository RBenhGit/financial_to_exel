"""
User Journey Testing Framework for Financial Analysis Application

This module provides comprehensive user acceptance testing capabilities
for the FCF Analysis Streamlit application, covering all major user workflows
and interaction patterns.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Test scenario and validation framework
class TestPriority(Enum):
    CRITICAL = "critical"  # Core functionality that must work
    HIGH = "high"         # Important features most users need
    MEDIUM = "medium"     # Useful features some users need
    LOW = "low"           # Nice-to-have features

class TestStatus(Enum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

@dataclass
class UserAction:
    """Represents a single user action in a test scenario."""
    action_type: str  # click, input, select, wait, validate
    target: str       # UI element or description
    value: Optional[str] = None
    expected_result: Optional[str] = None
    timeout: int = 10
    optional: bool = False

@dataclass
class TestScenario:
    """Represents a complete user journey test scenario."""
    scenario_id: str
    title: str
    description: str
    priority: TestPriority
    user_persona: str
    preconditions: List[str]
    actions: List[UserAction]
    success_criteria: List[str]
    estimated_duration: int  # minutes
    data_requirements: List[str]
    tags: List[str]

@dataclass
class TestResult:
    """Results from executing a test scenario."""
    scenario_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    screenshots: List[str] = None
    user_feedback: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

class UserJourneyTestFramework:
    """
    Comprehensive testing framework for user acceptance testing.

    This framework defines and manages user journey tests for the financial
    analysis application, covering all major workflows and user interactions.
    """

    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.test_scenarios = []
        self.results = []
        self.logger = self._setup_logging()
        self._initialize_test_scenarios()

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for test framework."""
        logger = logging.getLogger("user_journey_tests")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_test_scenarios(self):
        """Initialize all test scenarios for the application."""

        # Core Data Loading Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="data_load_excel_001",
                title="Load Company Data from Excel Files",
                description="User loads financial data from Excel files for analysis",
                priority=TestPriority.CRITICAL,
                user_persona="Financial Analyst",
                preconditions=[
                    "Application is running",
                    "Excel files exist in data/companies/MSFT/ folder",
                    "Files include Income Statement.xlsx, Balance Sheet.xlsx, Cash Flow Statement.xlsx"
                ],
                actions=[
                    UserAction("navigate", "Streamlit application homepage"),
                    UserAction("click", "Company folder selection in sidebar"),
                    UserAction("select", "MSFT company folder", "data/companies/MSFT"),
                    UserAction("wait", "Data loading to complete", timeout=30),
                    UserAction("validate", "Company name appears", "Microsoft Corporation"),
                    UserAction("validate", "Financial data loaded successfully")
                ],
                success_criteria=[
                    "Company data loads without errors",
                    "All three financial statements are processed",
                    "Financial metrics are calculated and displayed",
                    "User receives confirmation of successful data load"
                ],
                estimated_duration=3,
                data_requirements=["Excel files for MSFT"],
                tags=["data_loading", "excel", "core_functionality"]
            ),

            TestScenario(
                scenario_id="data_load_api_002",
                title="Load Company Data from API Sources",
                description="User loads financial data from API when Excel is unavailable",
                priority=TestPriority.HIGH,
                user_persona="Financial Analyst",
                preconditions=[
                    "Application is running",
                    "API keys are configured",
                    "Internet connection available"
                ],
                actions=[
                    UserAction("navigate", "Streamlit application homepage"),
                    UserAction("input", "Ticker symbol input field", "AAPL"),
                    UserAction("select", "Data source priority", "API First"),
                    UserAction("click", "Load data button"),
                    UserAction("wait", "API data loading", timeout=45),
                    UserAction("validate", "Company data loaded from API"),
                    UserAction("validate", "Data source indicator shows API")
                ],
                success_criteria=[
                    "API data loads successfully",
                    "Financial metrics calculated from API data",
                    "Data source clearly indicated to user",
                    "Fallback mechanism works if primary API fails"
                ],
                estimated_duration=4,
                data_requirements=["API access", "Valid ticker symbols"],
                tags=["data_loading", "api", "fallback"]
            )
        ])

        # FCF Analysis Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="fcf_analysis_001",
                title="Complete FCF Analysis Workflow",
                description="User performs comprehensive FCF analysis",
                priority=TestPriority.CRITICAL,
                user_persona="Investment Analyst",
                preconditions=[
                    "Company data is loaded (MSFT)",
                    "FCF Analysis tab is accessible"
                ],
                actions=[
                    UserAction("click", "FCF Analysis tab"),
                    UserAction("wait", "FCF calculations to complete"),
                    UserAction("validate", "FCF chart displays three types"),
                    UserAction("validate", "FCFE value is calculated"),
                    UserAction("validate", "FCFF value is calculated"),
                    UserAction("validate", "Levered FCF value is calculated"),
                    UserAction("click", "Export FCF data button"),
                    UserAction("validate", "Export completes successfully")
                ],
                success_criteria=[
                    "All three FCF types calculate correctly",
                    "Visual chart displays properly",
                    "FCF values are reasonable and non-zero",
                    "Export functionality works",
                    "User can understand the FCF analysis"
                ],
                estimated_duration=5,
                data_requirements=["Company with cash flow data"],
                tags=["fcf", "analysis", "core_functionality"]
            )
        ])

        # DCF Valuation Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="dcf_valuation_001",
                title="Complete DCF Valuation Workflow",
                description="User performs DCF valuation with custom assumptions",
                priority=TestPriority.CRITICAL,
                user_persona="Equity Analyst",
                preconditions=[
                    "Company data is loaded with FCF calculated",
                    "DCF Valuation tab is accessible"
                ],
                actions=[
                    UserAction("click", "DCF Valuation tab"),
                    UserAction("input", "Growth rate assumption", "5.0"),
                    UserAction("input", "Terminal growth rate", "2.5"),
                    UserAction("input", "Discount rate", "8.0"),
                    UserAction("click", "Calculate DCF valuation"),
                    UserAction("wait", "DCF calculation", timeout=20),
                    UserAction("validate", "Enterprise value calculated"),
                    UserAction("validate", "Equity value calculated"),
                    UserAction("validate", "Fair value per share calculated"),
                    UserAction("validate", "Upside/downside percentage shown")
                ],
                success_criteria=[
                    "DCF calculation completes without errors",
                    "All valuation metrics are calculated",
                    "Results are reasonable and non-zero",
                    "User can modify assumptions",
                    "Sensitivity analysis available"
                ],
                estimated_duration=6,
                data_requirements=["Company with complete financial data"],
                tags=["dcf", "valuation", "core_functionality"]
            )
        ])

        # DDM Valuation Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="ddm_analysis_001",
                title="Dividend Discount Model Analysis",
                description="User analyzes dividend-paying stock with DDM",
                priority=TestPriority.HIGH,
                user_persona="Income Investor",
                preconditions=[
                    "Company data loaded for dividend-paying stock",
                    "DDM Valuation tab accessible"
                ],
                actions=[
                    UserAction("click", "DDM Valuation tab"),
                    UserAction("validate", "Dividend history chart displays first"),
                    UserAction("input", "Expected dividend growth rate", "3.0"),
                    UserAction("input", "Required rate of return", "7.0"),
                    UserAction("click", "Calculate DDM valuation"),
                    UserAction("validate", "DDM fair value calculated"),
                    UserAction("validate", "Dividend yield information shown"),
                    UserAction("validate", "Growth sustainability analysis")
                ],
                success_criteria=[
                    "Dividend history shows before calculations",
                    "DDM calculation completes successfully",
                    "Fair value based on dividends calculated",
                    "User understands dividend sustainability",
                    "Historical dividend trend visible"
                ],
                estimated_duration=4,
                data_requirements=["Dividend-paying company data"],
                tags=["ddm", "dividends", "valuation"]
            )
        ])

        # P/B Analysis Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="pb_analysis_001",
                title="Price-to-Book Historical Analysis",
                description="User analyzes stock using P/B historical methodology",
                priority=TestPriority.HIGH,
                user_persona="Value Investor",
                preconditions=[
                    "Company data loaded with historical book values",
                    "P/B Analysis tab accessible"
                ],
                actions=[
                    UserAction("click", "P/B Analysis tab"),
                    UserAction("wait", "Historical P/B calculation"),
                    UserAction("validate", "Historical P/B trend chart"),
                    UserAction("validate", "Current P/B vs historical average"),
                    UserAction("validate", "Statistical analysis displayed"),
                    UserAction("validate", "Implied fair value based on P/B"),
                    UserAction("click", "View data quality indicators")
                ],
                success_criteria=[
                    "Historical P/B analysis completes",
                    "Statistical metrics calculated",
                    "Data quality transparently shown",
                    "Fair value estimate provided",
                    "User understands P/B methodology"
                ],
                estimated_duration=4,
                data_requirements=["Company with multi-year book value data"],
                tags=["pb", "historical", "valuation"]
            )
        ])

        # Watch Lists Scenarios
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="watchlist_001",
                title="Create and Manage Watch Lists",
                description="User creates watch list and tracks analysis results",
                priority=TestPriority.MEDIUM,
                user_persona="Portfolio Manager",
                preconditions=[
                    "Application running",
                    "Multiple companies analyzed",
                    "Watch Lists tab accessible"
                ],
                actions=[
                    UserAction("click", "Watch Lists tab"),
                    UserAction("click", "Create new watch list"),
                    UserAction("input", "Watch list name", "Tech Growth Stocks"),
                    UserAction("click", "Add current analysis to watch list"),
                    UserAction("validate", "Company added to watch list"),
                    UserAction("click", "View watch list analysis"),
                    UserAction("validate", "Historical vs current view toggle"),
                    UserAction("validate", "Performance metrics displayed")
                ],
                success_criteria=[
                    "Watch list created successfully",
                    "Companies can be added/removed",
                    "Analysis results are saved",
                    "Performance tracking works",
                    "Export functionality available"
                ],
                estimated_duration=5,
                data_requirements=["Multiple analyzed companies"],
                tags=["watchlist", "portfolio", "tracking"]
            )
        ])

        # Error Handling and Edge Cases
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="error_handling_001",
                title="Graceful Error Handling",
                description="Application handles errors gracefully and provides useful feedback",
                priority=TestPriority.HIGH,
                user_persona="New User",
                preconditions=[
                    "Application running"
                ],
                actions=[
                    UserAction("input", "Invalid ticker symbol", "INVALID123"),
                    UserAction("click", "Load data"),
                    UserAction("validate", "Helpful error message displayed"),
                    UserAction("click", "Load Excel with missing files"),
                    UserAction("validate", "Clear error explanation"),
                    UserAction("input", "Extreme valuation parameters", "1000"),
                    UserAction("validate", "Parameter validation works")
                ],
                success_criteria=[
                    "Errors are caught and handled gracefully",
                    "User receives helpful error messages",
                    "Application doesn't crash",
                    "User can recover from errors",
                    "Guidance provided for fixing issues"
                ],
                estimated_duration=3,
                data_requirements=["Invalid data for testing"],
                tags=["error_handling", "robustness", "user_experience"]
            )
        ])

        # Performance and Responsiveness
        self.test_scenarios.extend([
            TestScenario(
                scenario_id="performance_001",
                title="Application Performance and Responsiveness",
                description="Application performs well under normal usage",
                priority=TestPriority.MEDIUM,
                user_persona="Frequent User",
                preconditions=[
                    "Application running",
                    "Large dataset available for testing"
                ],
                actions=[
                    UserAction("measure", "Initial app load time"),
                    UserAction("measure", "Data loading time for large company"),
                    UserAction("measure", "FCF calculation time"),
                    UserAction("measure", "Tab switching responsiveness"),
                    UserAction("validate", "All operations complete within acceptable time"),
                    UserAction("validate", "UI remains responsive during calculations")
                ],
                success_criteria=[
                    "App loads within 10 seconds",
                    "Data loading completes within 30 seconds",
                    "Calculations complete within 15 seconds",
                    "UI remains responsive throughout",
                    "No memory leaks or performance degradation"
                ],
                estimated_duration=4,
                data_requirements=["Large company dataset"],
                tags=["performance", "responsiveness", "scalability"]
            )
        ])

    def get_scenarios_by_priority(self, priority: TestPriority) -> List[TestScenario]:
        """Get all test scenarios with specified priority."""
        return [s for s in self.test_scenarios if s.priority == priority]

    def get_scenarios_by_tags(self, tags: List[str]) -> List[TestScenario]:
        """Get all test scenarios containing any of the specified tags."""
        return [s for s in self.test_scenarios if any(tag in s.tags for tag in tags)]

    def validate_preconditions(self, scenario: TestScenario) -> bool:
        """Check if preconditions for a scenario are met."""
        # This would be implemented with actual checks
        # For now, return True as placeholder
        return True

    def execute_scenario(self, scenario: TestScenario, automated: bool = False) -> TestResult:
        """
        Execute a test scenario.

        Args:
            scenario: The test scenario to execute
            automated: Whether to run automated checks (True) or manual verification (False)
        """
        result = TestResult(
            scenario_id=scenario.scenario_id,
            status=TestStatus.NOT_RUN,
            start_time=datetime.now()
        )

        try:
            self.logger.info(f"Starting scenario: {scenario.title}")

            # Check preconditions
            if not self.validate_preconditions(scenario):
                result.status = TestStatus.BLOCKED
                result.error_message = "Preconditions not met"
                return result

            if automated:
                result = self._execute_automated(scenario, result)
            else:
                result = self._execute_manual(scenario, result)

        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            self.logger.error(f"Scenario {scenario.scenario_id} failed: {e}")

        finally:
            result.end_time = datetime.now()
            self.results.append(result)

        return result

    def _execute_automated(self, scenario: TestScenario, result: TestResult) -> TestResult:
        """Execute scenario with automated testing tools."""
        # Placeholder for automated execution
        # Would integrate with tools like Selenium, Playwright, etc.
        result.status = TestStatus.PASSED
        return result

    def _execute_manual(self, scenario: TestScenario, result: TestResult) -> TestResult:
        """Execute scenario with manual verification."""
        print(f"\n{'='*60}")
        print(f"MANUAL TEST: {scenario.title}")
        print(f"{'='*60}")
        print(f"Description: {scenario.description}")
        print(f"User Persona: {scenario.user_persona}")
        print(f"Priority: {scenario.priority.value}")
        print(f"Estimated Duration: {scenario.estimated_duration} minutes")

        print(f"\nPreconditions:")
        for i, condition in enumerate(scenario.preconditions, 1):
            print(f"  {i}. {condition}")

        print(f"\nTest Steps:")
        for i, action in enumerate(scenario.actions, 1):
            print(f"  {i}. {action.action_type.upper()}: {action.target}")
            if action.value:
                print(f"     Value: {action.value}")
            if action.expected_result:
                print(f"     Expected: {action.expected_result}")

            # Wait for user confirmation
            user_input = input(f"     Step completed successfully? (y/n/s for skip): ").lower()

            if user_input == 'n':
                result.status = TestStatus.FAILED
                result.error_message = f"Step {i} failed: {action.target}"
                return result
            elif user_input == 's':
                print(f"     Step {i} skipped")
                continue

        print(f"\nSuccess Criteria:")
        for i, criteria in enumerate(scenario.success_criteria, 1):
            print(f"  {i}. {criteria}")

        # Final validation
        final_result = input(f"\nAll success criteria met? (y/n): ").lower()
        if final_result == 'y':
            result.status = TestStatus.PASSED
        else:
            result.status = TestStatus.FAILED
            result.error_message = "Success criteria not met"

        # Collect user feedback
        feedback = input("Any additional feedback or issues? (optional): ")
        if feedback.strip():
            result.user_feedback = feedback

        return result

    def run_test_suite(self, priority_filter: Optional[TestPriority] = None,
                      tag_filter: Optional[List[str]] = None,
                      automated: bool = False) -> Dict[str, Any]:
        """
        Run a complete test suite with optional filters.

        Args:
            priority_filter: Only run scenarios with this priority
            tag_filter: Only run scenarios with these tags
            automated: Use automated testing tools
        """
        scenarios_to_run = self.test_scenarios

        if priority_filter:
            scenarios_to_run = [s for s in scenarios_to_run if s.priority == priority_filter]

        if tag_filter:
            scenarios_to_run = [s for s in scenarios_to_run if
                              any(tag in s.tags for tag in tag_filter)]

        print(f"\nRunning {len(scenarios_to_run)} test scenarios...")

        suite_results = {
            "total_scenarios": len(scenarios_to_run),
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "skipped": 0,
            "start_time": datetime.now(),
            "scenarios": []
        }

        for scenario in scenarios_to_run:
            result = self.execute_scenario(scenario, automated)
            suite_results["scenarios"].append(asdict(result))

            if result.status == TestStatus.PASSED:
                suite_results["passed"] += 1
            elif result.status == TestStatus.FAILED:
                suite_results["failed"] += 1
            elif result.status == TestStatus.BLOCKED:
                suite_results["blocked"] += 1
            elif result.status == TestStatus.SKIPPED:
                suite_results["skipped"] += 1

        suite_results["end_time"] = datetime.now()
        suite_results["success_rate"] = (
            suite_results["passed"] / suite_results["total_scenarios"] * 100
            if suite_results["total_scenarios"] > 0 else 0
        )

        return suite_results

    def generate_test_report(self, results: Dict[str, Any],
                           output_file: Optional[str] = None) -> str:
        """Generate comprehensive test report."""

        report = f"""
# User Acceptance Testing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Scenarios**: {results['total_scenarios']}
- **Success Rate**: {results['success_rate']:.1f}%
- **Passed**: {results['passed']}
- **Failed**: {results['failed']}
- **Blocked**: {results['blocked']}
- **Skipped**: {results['skipped']}

## Test Results by Priority
"""

        # Group results by priority
        priority_stats = {}
        for scenario_result in results['scenarios']:
            scenario_id = scenario_result['scenario_id']
            scenario = next(s for s in self.test_scenarios if s.scenario_id == scenario_id)
            priority = scenario.priority.value

            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "passed": 0}

            priority_stats[priority]["total"] += 1
            if scenario_result['status'] == TestStatus.PASSED.value:
                priority_stats[priority]["passed"] += 1

        for priority, stats in priority_stats.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            report += f"- **{priority.upper()}**: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)\n"

        report += "\n## Detailed Results\n"

        for scenario_result in results['scenarios']:
            scenario_id = scenario_result['scenario_id']
            scenario = next(s for s in self.test_scenarios if s.scenario_id == scenario_id)

            status_icon = {
                TestStatus.PASSED.value: "✅",
                TestStatus.FAILED.value: "❌",
                TestStatus.BLOCKED.value: "🚫",
                TestStatus.SKIPPED.value: "⏭️"
            }.get(scenario_result['status'], "❓")

            report += f"\n### {status_icon} {scenario.title}\n"
            report += f"- **Scenario ID**: {scenario_id}\n"
            report += f"- **Status**: {scenario_result['status']}\n"
            report += f"- **Priority**: {scenario.priority.value}\n"

            if scenario_result.get('error_message'):
                report += f"- **Error**: {scenario_result['error_message']}\n"

            if scenario_result.get('user_feedback'):
                report += f"- **Feedback**: {scenario_result['user_feedback']}\n"

        report += "\n## Recommendations\n"

        failed_critical = [r for r in results['scenarios']
                          if r['status'] == TestStatus.FAILED.value and
                          next(s for s in self.test_scenarios
                               if s.scenario_id == r['scenario_id']).priority == TestPriority.CRITICAL]

        if failed_critical:
            report += "### Critical Issues\n"
            for result in failed_critical:
                scenario = next(s for s in self.test_scenarios if s.scenario_id == result['scenario_id'])
                report += f"- **{scenario.title}**: {result.get('error_message', 'Critical failure')}\n"

        if results['success_rate'] < 80:
            report += "### Overall Assessment\n"
            report += "- Success rate below 80% indicates significant usability issues\n"
            report += "- Recommend addressing all failed test scenarios before release\n"

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)

        return report


def main():
    """Example usage of the User Journey Testing Framework."""

    framework = UserJourneyTestFramework()

    print("User Journey Testing Framework for Financial Analysis Application")
    print("=" * 60)

    while True:
        print("\nOptions:")
        print("1. List all test scenarios")
        print("2. Run critical scenarios only")
        print("3. Run scenarios by tags")
        print("4. Run full test suite")
        print("5. Generate test report")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ")

        if choice == "1":
            print(f"\nTotal scenarios: {len(framework.test_scenarios)}")
            for scenario in framework.test_scenarios:
                print(f"- {scenario.scenario_id}: {scenario.title} ({scenario.priority.value})")

        elif choice == "2":
            results = framework.run_test_suite(priority_filter=TestPriority.CRITICAL)
            print(f"\nCritical scenarios complete. Success rate: {results['success_rate']:.1f}%")

        elif choice == "3":
            available_tags = set()
            for scenario in framework.test_scenarios:
                available_tags.update(scenario.tags)

            print(f"\nAvailable tags: {', '.join(sorted(available_tags))}")
            tags_input = input("Enter tags (comma-separated): ")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

            if tags:
                results = framework.run_test_suite(tag_filter=tags)
                print(f"\nTagged scenarios complete. Success rate: {results['success_rate']:.1f}%")

        elif choice == "4":
            results = framework.run_test_suite()
            print(f"\nFull test suite complete. Success rate: {results['success_rate']:.1f}%")

        elif choice == "5":
            if framework.results:
                # Use the most recent test suite results
                latest_results = {
                    "total_scenarios": len(framework.results),
                    "passed": len([r for r in framework.results if r.status == TestStatus.PASSED]),
                    "failed": len([r for r in framework.results if r.status == TestStatus.FAILED]),
                    "blocked": len([r for r in framework.results if r.status == TestStatus.BLOCKED]),
                    "skipped": len([r for r in framework.results if r.status == TestStatus.SKIPPED]),
                    "scenarios": [asdict(r) for r in framework.results],
                    "start_time": min(r.start_time for r in framework.results),
                    "end_time": max(r.end_time for r in framework.results if r.end_time),
                    "success_rate": len([r for r in framework.results if r.status == TestStatus.PASSED]) / len(framework.results) * 100
                }

                report = framework.generate_test_report(latest_results)
                print("\n" + report)

                save = input("\nSave report to file? (y/n): ")
                if save.lower() == 'y':
                    filename = f"user_acceptance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    framework.generate_test_report(latest_results, filename)
                    print(f"Report saved to {filename}")
            else:
                print("No test results available. Run tests first.")

        elif choice == "6":
            break

        else:
            print("Invalid option. Please select 1-6.")


if __name__ == "__main__":
    main()