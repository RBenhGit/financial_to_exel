"""
Production Reporting System Validation Script

This script validates that the complete production deployment and user acceptance
reporting system is working correctly, leveraging the 88.9% UAT achievement.
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from pathlib import Path

# Add the validation modules to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core', 'validation'))

try:
    from production_deployment_dashboard import ProductionDeploymentDashboard
    from continuous_uat_trending import ContinuousUATTrending
    from feedback_sentiment_analyzer import FeedbackSentimentAnalyzer
    from workflow_performance_monitor import WorkflowPerformanceMonitor
    from feature_adoption_analytics import FeatureAdoptionAnalytics
    from automated_stakeholder_reporting import AutomatedStakeholderReporting
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing reporting modules: {e}")
    MODULES_AVAILABLE = False


def create_sample_uat_data(project_root):
    """Create sample UAT data for validation."""
    reports_dir = project_root / "reports" / "user_acceptance"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Sample results matching 88.9% success rate (8/9 passed)
    sample_results = [
        {"test_id": "UAT001", "test_name": "Basic FCF Analysis Workflow", "status": "PASS", "duration": 0.705},
        {"test_id": "UAT002", "test_name": "DCF Valuation Analysis", "status": "PASS", "duration": 0.804},
        {"test_id": "UAT003", "test_name": "Dividend Discount Model (DDM) Analysis", "status": "PASS", "duration": 0.804},
        {"test_id": "UAT004", "test_name": "Price-to-Book (P/B) Historical Analysis", "status": "PASS", "duration": 0.704},
        {"test_id": "UAT005", "test_name": "Multi-Company Portfolio Analysis", "status": "PASS", "duration": 0.704},
        {"test_id": "UAT006", "test_name": "Watch List Management", "status": "PASS", "duration": 0.703},
        {"test_id": "STARTUP001", "test_name": "Core Modules Import and Initialization", "status": "PASS", "duration": 3.926},
        {"test_id": "DATA001", "test_name": "Data Processing Capabilities", "status": "PASS", "duration": 0.358},
        {"test_id": "CALC001", "test_name": "Core Financial Calculations", "status": "FAIL", "duration": 0.000008}
    ]

    results_file = reports_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(sample_results, f, indent=2)

    return results_file


def validate_production_dashboard(project_root):
    """Validate production deployment dashboard."""
    print("🔍 Testing Production Deployment Dashboard...")

    try:
        dashboard = ProductionDeploymentDashboard(str(project_root))

        # Test initialization
        assert dashboard.uat_baseline["success_rate"] == 88.9, "UAT baseline should be 88.9%"
        print("  ✅ Dashboard initialized with correct UAT baseline (88.9%)")

        # Test validation
        validation_result = dashboard.validate_deployment()
        assert validation_result.metrics.uat_success_rate == 88.9, "UAT success rate should match baseline"
        print(f"  ✅ Validation complete - Status: {validation_result.validation_status}, Score: {validation_result.overall_score:.1f}")

        return True

    except Exception as e:
        print(f"  ❌ Dashboard validation failed: {e}")
        return False


def validate_uat_trending(project_root):
    """Validate UAT trending system."""
    print("📈 Testing UAT Trending System...")

    try:
        trending = ContinuousUATTrending(str(project_root))

        # Test trend analysis
        analysis = trending.analyze_trends(days=30)
        print(f"  ✅ Trend analysis complete - Current: {analysis.current_success_rate:.1f}%, Trend: {analysis.trend_direction}")

        # Test data collection (if sample data exists)
        trend_point = trending.collect_uat_results()
        if trend_point:
            print(f"  ✅ Data collection working - Success rate: {trend_point.success_rate:.1f}%")
        else:
            print("  ℹ️ No UAT results found for trending (expected in test environment)")

        return True

    except Exception as e:
        print(f"  ❌ UAT trending validation failed: {e}")
        return False


def validate_feedback_analyzer(project_root):
    """Validate feedback sentiment analyzer."""
    print("💬 Testing Feedback Sentiment Analyzer...")

    try:
        analyzer = FeedbackSentimentAnalyzer(str(project_root))

        # Test sentiment analysis
        positive_text = "This financial analysis tool is excellent and very helpful!"
        sentiment = analyzer.analyze_sentiment(positive_text)

        assert sentiment.sentiment_label == "positive", "Should detect positive sentiment"
        assert sentiment.score > 0, "Positive sentiment should have score > 0"
        print(f"  ✅ Sentiment analysis working - Detected: {sentiment.sentiment_label} (score: {sentiment.score:.2f})")

        # Test report generation
        report = analyzer.generate_analysis_report(days=7)
        print(f"  ✅ Analysis report generated - Report ID: {report.report_id}")

        return True

    except Exception as e:
        print(f"  ❌ Feedback analyzer validation failed: {e}")
        return False


def validate_performance_monitor(project_root):
    """Validate workflow performance monitor."""
    print("⚡ Testing Workflow Performance Monitor...")

    try:
        monitor = WorkflowPerformanceMonitor(str(project_root))

        # Test workflow benchmarks for all 6 scenarios
        expected_workflows = [
            "fcf_analysis", "dcf_valuation", "ddm_analysis",
            "pb_analysis", "portfolio_analysis", "watchlist_management"
        ]

        for workflow in expected_workflows:
            assert workflow in monitor.workflow_benchmarks, f"Missing benchmark for {workflow}"
            benchmark = monitor.workflow_benchmarks[workflow]
            assert benchmark.success_rate_threshold >= 90.0, f"{workflow} threshold too low"

        print(f"  ✅ All 6 workflow benchmarks configured correctly")

        # Test performance report
        report = monitor.generate_performance_report(days=7)
        print(f"  ✅ Performance report generated - Status: {report['overall_summary'].get('performance_status', 'unknown')}")

        return True

    except Exception as e:
        print(f"  ❌ Performance monitor validation failed: {e}")
        return False


def validate_adoption_analytics(project_root):
    """Validate feature adoption analytics."""
    print("📊 Testing Feature Adoption Analytics...")

    try:
        analytics = FeatureAdoptionAnalytics(str(project_root))

        # Test scenario coverage
        expected_scenarios = [
            "fcf_analysis", "dcf_valuation", "ddm_analysis",
            "pb_analysis", "portfolio_analysis", "watchlist_management"
        ]

        for scenario in expected_scenarios:
            assert scenario in analytics.scenario_features, f"Missing scenario: {scenario}"
            features = analytics.scenario_features[scenario]["features"]
            assert len(features) > 0, f"No features defined for {scenario}"

        print(f"  ✅ All 6 UAT scenarios mapped with features")

        # Test report generation
        report = analytics.generate_comprehensive_adoption_report(days=30)
        scenarios_analyzed = report["overall_analytics"]["scenarios_analyzed"]
        print(f"  ✅ Adoption report generated - {scenarios_analyzed} scenarios analyzed")

        return True

    except Exception as e:
        print(f"  ❌ Adoption analytics validation failed: {e}")
        return False


def validate_stakeholder_reporting(project_root):
    """Validate automated stakeholder reporting."""
    print("📋 Testing Automated Stakeholder Reporting...")

    try:
        reporting = AutomatedStakeholderReporting(str(project_root))

        # Test data collection
        data = reporting.collect_comprehensive_data(days=7)
        assert data["uat_baseline_achievement"] == 88.9, "UAT baseline not correctly reflected"
        print(f"  ✅ Comprehensive data collection working")

        # Test stakeholder configuration
        assert len(reporting.stakeholders) > 0, "No stakeholders configured"
        stakeholder_levels = {s.report_level for s in reporting.stakeholders}
        expected_levels = {"executive", "technical", "operational"}
        assert expected_levels.issubset(stakeholder_levels), "Missing stakeholder levels"
        print(f"  ✅ Stakeholder configuration complete - {len(reporting.stakeholders)} stakeholders")

        # Test report generation
        reports = reporting.generate_all_stakeholder_reports("validation")
        assert len(reports) > 0, "No reports generated"

        for report in reports:
            assert report.uat_status["baseline_achievement"] == 88.9, "UAT baseline missing from report"

        print(f"  ✅ Generated {len(reports)} stakeholder reports with UAT achievement")

        return True

    except Exception as e:
        print(f"  ❌ Stakeholder reporting validation failed: {e}")
        return False


def run_comprehensive_validation():
    """Run comprehensive validation of the entire reporting system."""
    print("🚀 Production Deployment & UAT Reporting System Validation")
    print("=" * 65)

    if not MODULES_AVAILABLE:
        print("❌ Cannot run validation - required modules not available")
        return False

    # Create temporary project for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        print(f"📁 Using temporary project directory: {project_root}")

        # Create sample data
        sample_file = create_sample_uat_data(project_root)
        print(f"📊 Created sample UAT data: {sample_file.name}")
        print()

        # Run validation tests
        validation_results = {
            "Production Dashboard": validate_production_dashboard(project_root),
            "UAT Trending": validate_uat_trending(project_root),
            "Feedback Analyzer": validate_feedback_analyzer(project_root),
            "Performance Monitor": validate_performance_monitor(project_root),
            "Adoption Analytics": validate_adoption_analytics(project_root),
            "Stakeholder Reporting": validate_stakeholder_reporting(project_root)
        }

        # Summary
        print()
        print("📋 Validation Summary")
        print("-" * 30)

        passed = 0
        total = len(validation_results)

        for component, result in validation_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{component:<25} {status}")
            if result:
                passed += 1

        print()
        print(f"Overall Result: {passed}/{total} components passed validation")

        if passed == total:
            print("🎉 SUCCESS: Complete production reporting system validated!")
            print("   🎯 88.9% UAT achievement properly integrated across all components")
            print("   📊 All 6 validated scenarios covered in monitoring")
            print("   📈 Comprehensive stakeholder reporting operational")
            return True
        else:
            print("⚠️ PARTIAL: Some components need attention")
            return False


if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)