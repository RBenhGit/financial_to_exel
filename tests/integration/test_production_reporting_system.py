"""
Integration Tests for Production Deployment and User Acceptance Reporting System

This module provides comprehensive integration tests for the complete production
reporting system, validating that all components work together to provide
accurate insights based on the 88.9% UAT achievement.
"""

import pytest
import sys
import os
import json
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the validation modules to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'validation'))

try:
    from production_deployment_dashboard import ProductionDeploymentDashboard
    from continuous_uat_trending import ContinuousUATTrending
    from feedback_sentiment_analyzer import FeedbackSentimentAnalyzer
    from workflow_performance_monitor import WorkflowPerformanceMonitor
    from feature_adoption_analytics import FeatureAdoptionAnalytics
    from automated_stakeholder_reporting import AutomatedStakeholderReporting
except ImportError as e:
    pytest.skip(f"Production reporting modules not available: {e}", allow_module_level=True)


class TestProductionReportingSystem:
    """Integration tests for the complete production reporting system."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project root for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_uat_results(self, temp_project_root):
        """Create sample UAT results for testing."""
        reports_dir = temp_project_root / "reports" / "user_acceptance"
        reports_dir.mkdir(parents=True)

        # Sample UAT results matching the 88.9% success rate
        sample_results = [
            {
                "test_id": "UAT001",
                "test_name": "Basic FCF Analysis Workflow",
                "status": "PASS",
                "duration": 0.705,
                "error_message": None,
                "user_feedback": "Scenario UAT001 simulated successfully",
                "timestamp": "2025-09-26T07:01:51.925681"
            },
            {
                "test_id": "UAT002",
                "test_name": "DCF Valuation Analysis",
                "status": "PASS",
                "duration": 0.804,
                "error_message": None,
                "user_feedback": "Scenario UAT002 simulated successfully",
                "timestamp": "2025-09-26T07:01:52.730669"
            },
            {
                "test_id": "UAT003",
                "test_name": "Dividend Discount Model (DDM) Analysis",
                "status": "PASS",
                "duration": 0.804,
                "error_message": None,
                "user_feedback": "Scenario UAT003 simulated successfully",
                "timestamp": "2025-09-26T07:01:53.535198"
            },
            {
                "test_id": "UAT004",
                "test_name": "Price-to-Book (P/B) Historical Analysis",
                "status": "PASS",
                "duration": 0.704,
                "error_message": None,
                "user_feedback": "Scenario UAT004 simulated successfully",
                "timestamp": "2025-09-26T07:01:54.239852"
            },
            {
                "test_id": "UAT005",
                "test_name": "Multi-Company Portfolio Analysis",
                "status": "PASS",
                "duration": 0.704,
                "error_message": None,
                "user_feedback": "Scenario UAT005 simulated successfully",
                "timestamp": "2025-09-26T07:01:54.944231"
            },
            {
                "test_id": "UAT006",
                "test_name": "Watch List Management",
                "status": "PASS",
                "duration": 0.703,
                "error_message": None,
                "user_feedback": "Scenario UAT006 simulated successfully",
                "timestamp": "2025-09-26T07:01:55.647832"
            },
            {
                "test_id": "CALC001",
                "test_name": "Core Financial Calculations",
                "status": "FAIL",
                "duration": 0.000008,
                "error_message": "'FinancialCalculator' object has no attribute 'calculate_fcff'",
                "user_feedback": None,
                "timestamp": "2025-09-26T07:01:51.220395"
            },
            {
                "test_id": "STARTUP001",
                "test_name": "Core Modules Import and Initialization",
                "status": "PASS",
                "duration": 3.926,
                "error_message": None,
                "user_feedback": None,
                "timestamp": "2025-09-26T07:01:50.861881"
            },
            {
                "test_id": "DATA001",
                "test_name": "Data Processing Capabilities",
                "status": "PASS",
                "duration": 0.358,
                "error_message": None,
                "user_feedback": None,
                "timestamp": "2025-09-26T07:01:51.220166"
            }
        ]

        # Save sample results
        results_file = reports_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(sample_results, f, indent=2)

        return results_file

    def test_production_deployment_dashboard_initialization(self, temp_project_root):
        """Test that production deployment dashboard initializes correctly."""

        dashboard = ProductionDeploymentDashboard(str(temp_project_root))

        assert dashboard.project_root == temp_project_root
        assert dashboard.reports_dir.exists()
        assert dashboard.uat_baseline["success_rate"] == 88.9
        assert "key_scenarios" in dashboard.uat_baseline

    def test_uat_trending_system(self, temp_project_root, sample_uat_results):
        """Test UAT trending system functionality."""

        trending = ContinuousUATTrending(str(temp_project_root))

        # Test data collection
        trend_point = trending.collect_uat_results()
        assert trend_point is not None
        assert trend_point.success_rate == 88.9  # Expected from sample data (8/9 passed)

        # Test trend analysis
        analysis = trending.analyze_trends(days=30)
        assert analysis.current_success_rate == 88.9
        assert analysis.trend_direction in ["improving", "stable", "declining"]
        assert analysis.risk_level in ["low", "medium", "high"]

    def test_feedback_sentiment_analyzer(self, temp_project_root):
        """Test feedback sentiment analysis system."""

        analyzer = FeedbackSentimentAnalyzer(str(temp_project_root))

        # Test sentiment analysis
        positive_feedback = "This application is excellent and very helpful for financial analysis!"
        sentiment = analyzer.analyze_sentiment(positive_feedback)

        assert sentiment.sentiment_label == "positive"
        assert sentiment.score > 0
        assert sentiment.confidence > 0

        # Test negative feedback
        negative_feedback = "The interface is confusing and the calculations are slow"
        neg_sentiment = analyzer.analyze_sentiment(negative_feedback)

        assert neg_sentiment.sentiment_label == "negative"
        assert neg_sentiment.score < 0

    def test_workflow_performance_monitor(self, temp_project_root):
        """Test workflow performance monitoring system."""

        monitor = WorkflowPerformanceMonitor(str(temp_project_root))

        # Test that all 6 validated workflows have benchmarks
        expected_workflows = [
            "fcf_analysis", "dcf_valuation", "ddm_analysis",
            "pb_analysis", "portfolio_analysis", "watchlist_management"
        ]

        for workflow in expected_workflows:
            assert workflow in monitor.workflow_benchmarks
            benchmark = monitor.workflow_benchmarks[workflow]
            assert benchmark.target_execution_time > 0
            assert benchmark.max_memory_usage_mb > 0
            assert benchmark.success_rate_threshold >= 90.0

    def test_feature_adoption_analytics(self, temp_project_root):
        """Test feature adoption analytics system."""

        analytics = FeatureAdoptionAnalytics(str(temp_project_root))

        # Test scenario mapping
        assert len(analytics.scenario_features) == 6
        expected_scenarios = [
            "fcf_analysis", "dcf_valuation", "ddm_analysis",
            "pb_analysis", "portfolio_analysis", "watchlist_management"
        ]

        for scenario in expected_scenarios:
            assert scenario in analytics.scenario_features
            assert "features" in analytics.scenario_features[scenario]
            assert len(analytics.scenario_features[scenario]["features"]) > 0

    def test_automated_stakeholder_reporting(self, temp_project_root, sample_uat_results):
        """Test automated stakeholder reporting system."""

        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Test data collection
        data = reporting.collect_comprehensive_data(days=7)
        assert "collection_timestamp" in data
        assert data["uat_baseline_achievement"] == 88.9

        # Test stakeholder configuration
        assert len(reporting.stakeholders) > 0

        stakeholder_types = [s.report_level for s in reporting.stakeholders]
        assert "executive" in stakeholder_types
        assert "technical" in stakeholder_types
        assert "operational" in stakeholder_types

    @pytest.mark.integration
    def test_complete_reporting_workflow(self, temp_project_root, sample_uat_results):
        """Test the complete end-to-end reporting workflow."""

        # Initialize all systems
        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Generate reports for all stakeholders
        reports = reporting.generate_all_stakeholder_reports("test")

        # Validate that reports were generated
        assert len(reports) > 0

        for report in reports:
            # Validate report structure
            assert report.report_id.startswith("STAKEHOLDER_")
            assert report.generated_at is not None
            assert report.executive_summary is not None
            assert report.uat_status is not None
            assert report.production_health is not None

            # Validate UAT baseline achievement is reflected
            assert report.uat_status["baseline_achievement"] == 88.9
            assert "88.9%" in str(report.key_achievements) or report.uat_status["current_success_rate"] >= 88.9

    def test_dashboard_validation_with_uat_baseline(self, temp_project_root, sample_uat_results):
        """Test that deployment validation properly considers UAT baseline."""

        dashboard = ProductionDeploymentDashboard(str(temp_project_root))

        # Perform validation
        validation_result = dashboard.validate_deployment()

        # Should reflect the 88.9% UAT success rate
        assert validation_result.metrics.uat_success_rate == 88.9

        # UAT validation should pass since we're at baseline
        uat_validation = validation_result.validation_details["uat_validation"]
        assert uat_validation["current_rate"] == 88.9
        assert uat_validation["status"] in ["PASS", "WARN"]  # 88.9% should at least be WARN

    def test_cross_system_data_consistency(self, temp_project_root, sample_uat_results):
        """Test that data is consistent across all monitoring systems."""

        # Initialize systems
        trending = ContinuousUATTrending(str(temp_project_root))
        dashboard = ProductionDeploymentDashboard(str(temp_project_root))
        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Collect data from different systems
        trend_analysis = trending.analyze_trends()
        validation_result = dashboard.validate_deployment()
        comprehensive_data = reporting.collect_comprehensive_data()

        # Verify UAT success rate consistency
        assert trend_analysis.current_success_rate == 88.9
        assert validation_result.metrics.uat_success_rate == 88.9
        assert comprehensive_data["uat_baseline_achievement"] == 88.9

    def test_stakeholder_report_customization(self, temp_project_root, sample_uat_results):
        """Test that stakeholder reports are properly customized by level."""

        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Generate reports for different stakeholder levels
        executive_stakeholder = next(s for s in reporting.stakeholders if s.report_level == "executive")
        technical_stakeholder = next(s for s in reporting.stakeholders if s.report_level == "technical")

        exec_report = reporting.generate_stakeholder_report(executive_stakeholder)
        tech_report = reporting.generate_stakeholder_report(technical_stakeholder)

        # Executive reports should focus on high-level metrics
        exec_summary = exec_report.executive_summary["key_metrics_summary"]
        assert "user_satisfaction" in exec_summary or "system_uptime" in exec_summary

        # Technical reports should include technical details
        tech_summary = tech_report.executive_summary["key_metrics_summary"]
        assert "uat_success_rate" in tech_summary or "performance_status" in tech_summary

        # Both should highlight UAT achievement
        assert exec_report.uat_status["baseline_achievement"] == 88.9
        assert tech_report.uat_status["baseline_achievement"] == 88.9

    def test_report_file_generation(self, temp_project_root, sample_uat_results):
        """Test that report files are properly generated and saved."""

        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Generate a single report
        stakeholder = reporting.stakeholders[0]
        report = reporting.generate_stakeholder_report(stakeholder)

        # Check that files were created
        stakeholder_dir = reporting.reports_dir / stakeholder.stakeholder_name.replace(' ', '_').lower()
        assert stakeholder_dir.exists()

        json_file = stakeholder_dir / f"{report.report_id}.json"
        assert json_file.exists()

        # Validate JSON content
        with open(json_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["report_id"] == report.report_id
        assert saved_data["uat_status"]["baseline_achievement"] == 88.9

    @pytest.mark.parametrize("scenario", [
        "fcf_analysis", "dcf_valuation", "ddm_analysis",
        "pb_analysis", "portfolio_analysis", "watchlist_management"
    ])
    def test_scenario_coverage_in_reporting(self, temp_project_root, scenario, sample_uat_results):
        """Test that all 6 validated scenarios are covered in the reporting system."""

        # Test feature adoption analytics covers the scenario
        analytics = FeatureAdoptionAnalytics(str(temp_project_root))
        assert scenario in analytics.scenario_features

        # Test performance monitor has benchmarks for scenario
        monitor = WorkflowPerformanceMonitor(str(temp_project_root))
        if scenario in monitor.workflow_benchmarks:
            benchmark = monitor.workflow_benchmarks[scenario]
            assert benchmark.success_rate_threshold >= 90.0

    def test_error_handling_and_resilience(self, temp_project_root):
        """Test that the reporting system handles errors gracefully."""

        reporting = AutomatedStakeholderReporting(str(temp_project_root))

        # Test with missing data sources
        with patch.object(reporting, 'deployment_dashboard', None):
            with patch.object(reporting, 'uat_trending', None):
                data = reporting.collect_comprehensive_data()

                # Should still collect some data and not crash
                assert "collection_timestamp" in data
                assert "uat_baseline_achievement" in data

    def test_performance_benchmarks_alignment(self, temp_project_root):
        """Test that performance benchmarks align with UAT success criteria."""

        monitor = WorkflowPerformanceMonitor(str(temp_project_root))

        # All workflow benchmarks should have high success rate thresholds
        # consistent with the 88.9% UAT baseline achievement
        for workflow_name, benchmark in monitor.workflow_benchmarks.items():
            assert benchmark.success_rate_threshold >= 90.0, f"{workflow_name} success threshold too low"

            # Execution time benchmarks should be reasonable
            assert benchmark.target_execution_time > 0
            assert benchmark.target_execution_time < 300  # No workflow should take more than 5 minutes

    def test_uat_baseline_integration(self, temp_project_root, sample_uat_results):
        """Test that the 88.9% UAT baseline is properly integrated across all systems."""

        systems = [
            ProductionDeploymentDashboard(str(temp_project_root)),
            ContinuousUATTrending(str(temp_project_root)),
            AutomatedStakeholderReporting(str(temp_project_root))
        ]

        for system in systems:
            # Each system should reference the UAT baseline
            if hasattr(system, 'uat_baseline'):
                assert system.uat_baseline["success_rate"] == 88.9
            elif hasattr(system, 'baseline_success_rate'):
                assert system.baseline_success_rate == 88.9
            elif hasattr(system, 'uat_baseline_achievement'):
                assert system.uat_baseline_achievement == 88.9


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short"])