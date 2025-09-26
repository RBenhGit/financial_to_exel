"""
Integration Tests for UX Validation Framework

Tests the integration of the UX Validation Framework with the existing
user journey testing framework and application components.

Task 156.2: Implement User Experience Validation Framework - Integration Testing
"""

import os
import sys
import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.validation.ux_validation_framework import (
    UXValidationFramework,
    ValidationStatus,
    ValidationSeverity,
    UXMetric,
    ValidationResult
)
from tests.user_acceptance.user_journey_testing_framework import (
    UserJourneyTestFramework,
    TestStatus
)


@pytest.fixture
def ux_framework():
    """Fixture for UX Validation Framework"""
    return UXValidationFramework(
        base_url="http://localhost:8501",
        report_dir="tests/temp_reports"
    )


@pytest.fixture
def user_journey_framework():
    """Fixture for User Journey Testing Framework"""
    return UserJourneyTestFramework(base_url="http://localhost:8501")


class TestUXValidationFrameworkIntegration:
    """Test suite for UX Validation Framework integration"""

    def test_framework_initialization(self, ux_framework):
        """Test that the UX validation framework initializes correctly"""
        assert ux_framework.base_url == "http://localhost:8501"
        assert ux_framework.report_dir.name == "temp_reports"
        assert len(ux_framework.validation_results) == 0
        assert ux_framework.performance_thresholds['page_load_time'] == 10.0
        assert ux_framework.accessibility_standards['wcag_level'] == 'AA'

    def test_performance_metrics_validation(self, ux_framework):
        """Test performance metrics validation execution"""
        result = ux_framework.validate_performance_metrics()

        assert result.validation_id == "perf_001"
        assert result.validation_name == "Performance Metrics Validation"
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING, ValidationStatus.FAILED]
        assert len(result.metrics) >= 3  # page_load_time, tab_switch_time, calculation_time
        assert result.execution_time is not None
        assert result.timestamp is not None

        # Check specific metrics exist
        metric_names = [m.metric_name for m in result.metrics]
        assert "page_load_time" in metric_names
        assert "tab_switch_time" in metric_names
        assert "calculation_time" in metric_names

    def test_accessibility_compliance_validation(self, ux_framework):
        """Test accessibility compliance validation"""
        result = ux_framework.validate_accessibility_compliance()

        assert result.validation_id == "acc_001"
        assert result.validation_name == "Accessibility Compliance Validation"
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING, ValidationStatus.FAILED]
        assert len(result.metrics) >= 3  # contrast, alt_text, keyboard_nav

        # Check specific accessibility metrics
        metric_names = [m.metric_name for m in result.metrics]
        assert "color_contrast_ratio" in metric_names
        assert "alt_text_coverage" in metric_names
        assert "keyboard_navigation_score" in metric_names

    def test_ui_consistency_validation(self, ux_framework):
        """Test UI consistency validation"""
        result = ux_framework.validate_ui_consistency()

        assert result.validation_id == "ui_001"
        assert result.validation_name == "UI Consistency Validation"
        assert len(result.metrics) >= 3  # styling, layout, interaction consistency

        # Check consistency metrics
        metric_names = [m.metric_name for m in result.metrics]
        assert "styling_consistency_score" in metric_names
        assert "layout_consistency_score" in metric_names
        assert "interaction_consistency_score" in metric_names

    def test_responsive_design_validation(self, ux_framework):
        """Test responsive design validation"""
        result = ux_framework.validate_responsive_design()

        assert result.validation_id == "resp_001"
        assert result.validation_name == "Responsive Design Validation"
        assert len(result.metrics) >= 3  # mobile, breakpoints, readability

        # Check responsive design metrics
        metric_names = [m.metric_name for m in result.metrics]
        assert "mobile_compatibility_score" in metric_names
        assert "breakpoint_handling_score" in metric_names
        assert "content_readability_score" in metric_names

    def test_error_handling_validation(self, ux_framework):
        """Test error handling validation"""
        result = ux_framework.validate_error_handling()

        assert result.validation_id == "err_001"
        assert result.validation_name == "Error Handling Validation"
        assert len(result.metrics) >= 3  # error clarity, degradation, recovery

        # Check error handling metrics
        metric_names = [m.metric_name for m in result.metrics]
        assert "error_message_clarity_score" in metric_names
        assert "graceful_degradation_score" in metric_names
        assert "recovery_effectiveness_score" in metric_names

    def test_comprehensive_validation_execution(self, ux_framework):
        """Test comprehensive validation suite execution"""
        results = ux_framework.run_comprehensive_validation()

        # Check structure of results
        assert 'execution_summary' in results
        assert 'results_summary' in results
        assert 'ux_score' in results
        assert 'validation_results' in results
        assert 'all_metrics' in results
        assert 'recommendations' in results
        assert 'next_steps' in results

        # Check execution summary
        exec_summary = results['execution_summary']
        assert 'start_time' in exec_summary
        assert 'end_time' in exec_summary
        assert 'duration' in exec_summary
        assert exec_summary['total_validations'] == 5

        # Check results summary
        results_summary = results['results_summary']
        total_validations = (results_summary['passed'] + results_summary['warnings'] +
                           results_summary['failed'] + results_summary['errors'])
        assert total_validations == 5
        assert 0 <= results_summary['success_rate'] <= 100

        # Check UX score
        ux_score = results['ux_score']
        assert 0 <= ux_score['overall_score'] <= 100
        assert ux_score['grade'] in ['A', 'B', 'C', 'D', 'F']
        assert ux_score['total_metrics'] > 0
        assert isinstance(ux_score['total_recommendations'], int)

        # Check validation results
        assert len(results['validation_results']) == 5
        validation_ids = [vr['validation_id'] for vr in results['validation_results']]
        expected_ids = ['perf_001', 'acc_001', 'ui_001', 'resp_001', 'err_001']
        for expected_id in expected_ids:
            assert expected_id in validation_ids

    def test_ux_score_calculation(self, ux_framework):
        """Test UX score calculation logic"""
        # Create mock validation results with known statuses
        mock_validations = [
            ValidationResult("perf_001", "Performance", ValidationStatus.PASSED, ValidationSeverity.INFO, []),
            ValidationResult("acc_001", "Accessibility", ValidationStatus.WARNING, ValidationSeverity.MEDIUM, []),
            ValidationResult("ui_001", "UI Consistency", ValidationStatus.FAILED, ValidationSeverity.HIGH, []),
            ValidationResult("resp_001", "Responsive Design", ValidationStatus.PASSED, ValidationSeverity.INFO, []),
            ValidationResult("err_001", "Error Handling", ValidationStatus.ERROR, ValidationSeverity.CRITICAL, [])
        ]

        score = ux_framework._calculate_overall_ux_score(mock_validations)
        assert 0 <= score <= 100

        # Test grade conversion
        grade_a = ux_framework._get_ux_grade(95.0)
        grade_b = ux_framework._get_ux_grade(85.0)
        grade_c = ux_framework._get_ux_grade(75.0)
        grade_d = ux_framework._get_ux_grade(65.0)
        grade_f = ux_framework._get_ux_grade(45.0)

        assert grade_a == "A"
        assert grade_b == "B"
        assert grade_c == "C"
        assert grade_d == "D"
        assert grade_f == "F"

    def test_report_generation(self, ux_framework, tmp_path):
        """Test report generation functionality"""
        # Override report directory to use temporary path
        ux_framework.report_dir = tmp_path

        # Run comprehensive validation to generate results
        results = ux_framework.run_comprehensive_validation()

        # Check that reports were generated
        json_files = list(tmp_path.glob("ux_validation_report_*.json"))
        md_files = list(tmp_path.glob("ux_validation_report_*.md"))
        log_files = list(tmp_path.glob("ux_validation.log"))

        assert len(json_files) == 1, f"Expected 1 JSON report, found {len(json_files)}"
        assert len(md_files) == 1, f"Expected 1 Markdown report, found {len(md_files)}"
        # Log file may be created in different location depending on setup, so check is optional
        # assert len(log_files) >= 0, f"Log files found: {len(log_files)}"

        # Validate JSON report content
        json_report = json_files[0]
        with open(json_report, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        assert 'execution_summary' in json_data
        assert 'ux_score' in json_data
        assert 'validation_results' in json_data

        # Validate Markdown report content
        md_report = md_files[0]
        with open(md_report, 'r', encoding='utf-8') as f:
            md_content = f.read()

        assert "# UX Validation Report" in md_content
        assert "Overall UX Score" in md_content
        assert "Validation Results" in md_content
        assert "Priority Next Steps" in md_content

    def test_integration_with_user_journey_framework(self, ux_framework, user_journey_framework):
        """Test integration capabilities with existing user journey framework"""
        # Get scenarios from user journey framework
        journey_scenarios = user_journey_framework.test_scenarios
        assert len(journey_scenarios) > 0

        # Run UX validation
        ux_results = ux_framework.run_comprehensive_validation()

        # Verify both frameworks can work together
        assert len(ux_results['validation_results']) == 5
        assert len(journey_scenarios) >= 8  # Should have multiple user scenarios

        # Test that UX framework results can provide insights for journey testing
        critical_issues = []
        for validation in ux_results['validation_results']:
            if validation['status'] in ['failed', 'error']:
                critical_issues.append(validation['validation_name'])

        # UX framework should identify areas that might affect user journeys
        assert isinstance(critical_issues, list)

    def test_metric_thresholds_and_configuration(self, ux_framework):
        """Test that metric thresholds can be configured and work correctly"""
        # Test default thresholds
        assert ux_framework.performance_thresholds['page_load_time'] == 10.0
        assert ux_framework.performance_thresholds['tab_switch_time'] == 2.0

        # Test accessibility standards
        assert ux_framework.accessibility_standards['wcag_level'] == 'AA'
        assert ux_framework.accessibility_standards['contrast_ratio'] == 4.5

        # Modify thresholds and test validation
        ux_framework.performance_thresholds['page_load_time'] = 1.0  # Very strict

        result = ux_framework.validate_performance_metrics()

        # Should likely fail with such a strict threshold
        page_load_metrics = [m for m in result.metrics if m.metric_name == "page_load_time"]
        assert len(page_load_metrics) == 1
        assert page_load_metrics[0].threshold == 1.0

    def test_error_handling_in_validations(self, ux_framework):
        """Test error handling within the validation framework"""
        # Mock a validation method to raise an exception
        original_method = ux_framework._measure_page_load_time

        def mock_failing_method():
            raise Exception("Simulated measurement failure")

        ux_framework._measure_page_load_time = mock_failing_method

        result = ux_framework.validate_performance_metrics()

        # Restore original method
        ux_framework._measure_page_load_time = original_method

        # Should handle the error gracefully
        assert result.status == ValidationStatus.ERROR
        assert result.error_message is not None
        assert "Simulated measurement failure" in result.error_message

    def test_metric_data_structure(self, ux_framework):
        """Test UX metric data structure integrity"""
        result = ux_framework.validate_performance_metrics()

        for metric in result.metrics:
            # Check required fields
            assert hasattr(metric, 'metric_name')
            assert hasattr(metric, 'category')
            assert hasattr(metric, 'value')
            assert hasattr(metric, 'threshold')
            assert hasattr(metric, 'unit')
            assert hasattr(metric, 'severity')
            assert hasattr(metric, 'status')
            assert hasattr(metric, 'timestamp')

            # Check data types
            assert isinstance(metric.metric_name, str)
            assert isinstance(metric.category, str)
            assert isinstance(metric.value, (int, float))
            assert isinstance(metric.threshold, (int, float))
            assert isinstance(metric.unit, str)
            assert isinstance(metric.severity, ValidationSeverity)
            assert isinstance(metric.status, ValidationStatus)
            assert isinstance(metric.timestamp, datetime)

    def test_recommendations_generation(self, ux_framework):
        """Test that validation results generate appropriate recommendations"""
        results = ux_framework.run_comprehensive_validation()

        all_recommendations = results['recommendations']
        assert isinstance(all_recommendations, list)

        # Check that recommendations are non-empty strings
        for rec in all_recommendations:
            assert isinstance(rec, str)
            assert len(rec.strip()) > 0

        # Check next steps generation
        next_steps = results['next_steps']
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0

        # Should include integration recommendations
        integration_steps = [step for step in next_steps if 'CI/CD' in step or 'pipeline' in step]
        assert len(integration_steps) > 0

    def test_concurrent_validation_execution(self, ux_framework):
        """Test that multiple validations can run without interference"""
        # Run two validation cycles back-to-back
        results1 = ux_framework.run_comprehensive_validation()
        results2 = ux_framework.run_comprehensive_validation()

        # Both should succeed
        assert results1['ux_score']['overall_score'] > 0
        assert results2['ux_score']['overall_score'] > 0

        # Results should be consistent (allowing for small variations in timing)
        score_diff = abs(results1['ux_score']['overall_score'] - results2['ux_score']['overall_score'])
        assert score_diff < 10.0, "UX scores should be relatively consistent between runs"

    @pytest.mark.slow
    def test_full_integration_workflow(self, ux_framework, user_journey_framework):
        """
        Test full integration workflow combining UX validation with user journey testing.
        This is a comprehensive end-to-end test.
        """
        # Step 1: Run UX validation
        ux_results = ux_framework.run_comprehensive_validation()

        # Step 2: Identify critical UX issues
        critical_validations = [
            v for v in ux_results['validation_results']
            if v['status'] in ['failed', 'error']
        ]

        # Step 3: Get user journey scenarios that might be affected
        affected_scenarios = []
        if critical_validations:
            # Performance issues might affect all scenarios
            perf_failures = [v for v in critical_validations if v['validation_id'] == 'perf_001']
            if perf_failures:
                # All scenarios could be affected by performance issues
                affected_scenarios = user_journey_framework.get_scenarios_by_priority(
                    user_journey_framework.test_scenarios[0].priority.__class__.CRITICAL
                )

        # Step 4: Verify integration data consistency
        assert len(ux_results['validation_results']) == 5
        assert ux_results['ux_score']['overall_score'] >= 0
        assert len(ux_results['next_steps']) > 0

        # Step 5: Verify user journey scenarios exist
        all_scenarios = user_journey_framework.test_scenarios
        assert len(all_scenarios) >= 8

        # Integration should work smoothly
        assert True  # If we reach here, integration is working


class TestUXValidationFrameworkConfiguration:
    """Test configuration and customization aspects of the framework"""

    def test_custom_thresholds_configuration(self):
        """Test custom threshold configuration"""
        custom_framework = UXValidationFramework(
            base_url="http://test:9000",
            report_dir="custom_reports"
        )

        # Modify thresholds
        custom_framework.performance_thresholds.update({
            'page_load_time': 5.0,
            'calculation_time': 10.0
        })

        custom_framework.accessibility_standards.update({
            'contrast_ratio': 7.0,  # AAA standard
            'wcag_level': 'AAA'
        })

        # Run validation with custom thresholds
        result = custom_framework.validate_performance_metrics()

        # Verify custom thresholds are used
        page_load_metrics = [m for m in result.metrics if m.metric_name == "page_load_time"]
        assert len(page_load_metrics) == 1
        assert page_load_metrics[0].threshold == 5.0

        acc_result = custom_framework.validate_accessibility_compliance()
        contrast_metrics = [m for m in acc_result.metrics if m.metric_name == "color_contrast_ratio"]
        assert len(contrast_metrics) == 1
        assert contrast_metrics[0].threshold == 7.0

    def test_custom_report_directory(self, tmp_path):
        """Test custom report directory configuration"""
        custom_dir = tmp_path / "custom_ux_reports"

        framework = UXValidationFramework(report_dir=str(custom_dir))

        # Run validation to generate reports
        framework.run_comprehensive_validation()

        # Check that reports are created in custom directory
        assert custom_dir.exists()
        json_files = list(custom_dir.glob("*.json"))
        md_files = list(custom_dir.glob("*.md"))

        assert len(json_files) >= 1
        assert len(md_files) >= 1


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])