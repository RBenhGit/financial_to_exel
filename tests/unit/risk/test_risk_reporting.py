"""
Unit Tests for Risk Reporting Module
====================================

This module contains comprehensive unit tests for the risk reporting
components, including report generation, export functionality,
and integration with visualization components.

Test Coverage:
- RiskReporter class methods
- Report generation and formatting
- Export functionality (JSON, Excel, HTML)
- Summary metrics calculation
- Executive summary generation
- Recommendations engine
"""

import pytest
import numpy as np
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from core.analysis.risk.risk_reporting import (
    RiskReporter,
    RiskReport,
    RiskSummaryMetrics,
    ReportMetadata
)

# Import risk analysis components for testing
from core.analysis.risk.var_calculations import VaRResult


class TestReportMetadata:
    """Test cases for ReportMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating report metadata."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        metadata = ReportMetadata(
            report_id="test_report_001",
            title="Test Risk Report",
            generated_date=datetime.now(),
            analysis_period=(start_date, end_date),
            confidence_levels=[0.95, 0.99],
            methodologies=["parametric", "historical"],
            data_source="test_data",
            report_type="comprehensive"
        )

        assert metadata.report_id == "test_report_001"
        assert metadata.title == "Test Risk Report"
        assert metadata.confidence_levels == [0.95, 0.99]
        assert metadata.methodologies == ["parametric", "historical"]

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        generated_date = datetime(2023, 6, 15)

        metadata = ReportMetadata(
            report_id="test_report_001",
            title="Test Risk Report",
            generated_date=generated_date,
            analysis_period=(start_date, end_date),
            confidence_levels=[0.95, 0.99],
            methodologies=["parametric", "historical"],
            data_source="test_data",
            report_type="comprehensive"
        )

        metadata_dict = metadata.to_dict()

        assert metadata_dict['report_id'] == "test_report_001"
        assert metadata_dict['title'] == "Test Risk Report"
        assert metadata_dict['generated_date'] == generated_date.isoformat()
        assert len(metadata_dict['analysis_period']) == 2
        assert metadata_dict['confidence_levels'] == [0.95, 0.99]


class TestRiskSummaryMetrics:
    """Test cases for RiskSummaryMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating summary metrics."""
        metrics = RiskSummaryMetrics(
            portfolio_volatility=0.20,
            mean_return=0.08,
            sharpe_ratio=0.4,
            max_drawdown=-0.15,
            skewness=-0.5,
            kurtosis=3.2,
            var_95_best=-0.025,
            var_95_worst=-0.035,
            var_99_best=-0.040,
            var_99_worst=-0.050,
            backtesting_passed=True,
            violation_rate=0.04,
            model_accuracy=0.96
        )

        assert metrics.portfolio_volatility == 0.20
        assert metrics.mean_return == 0.08
        assert metrics.sharpe_ratio == 0.4
        assert metrics.max_drawdown == -0.15
        assert metrics.backtesting_passed is True

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = RiskSummaryMetrics(
            portfolio_volatility=0.20,
            mean_return=0.08,
            sharpe_ratio=0.4,
            max_drawdown=-0.15,
            skewness=-0.5,
            kurtosis=3.2,
            var_95_best=-0.025,
            var_95_worst=-0.035,
            var_99_best=-0.040,
            var_99_worst=-0.050,
            backtesting_passed=True,
            violation_rate=0.04,
            model_accuracy=0.96
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict['portfolio_volatility'] == 0.20
        assert metrics_dict['mean_return'] == 0.08
        assert metrics_dict['backtesting_passed'] is True
        assert len(metrics_dict) >= 13  # Should have all required fields


class TestRiskReport:
    """Test cases for RiskReport container class."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return ReportMetadata(
            report_id="test_001",
            title="Test Report",
            generated_date=datetime.now(),
            analysis_period=(datetime(2023, 1, 1), datetime(2023, 12, 31)),
            confidence_levels=[0.95, 0.99],
            methodologies=["parametric"],
            data_source="test",
            report_type="test"
        )

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing."""
        return RiskSummaryMetrics(
            portfolio_volatility=0.20,
            mean_return=0.08,
            sharpe_ratio=0.4,
            max_drawdown=-0.15,
            skewness=-0.5,
            kurtosis=3.2,
            var_95_best=-0.025,
            var_95_worst=-0.035,
            var_99_best=-0.040,
            var_99_worst=-0.050,
            backtesting_passed=True,
            violation_rate=0.04,
            model_accuracy=0.96
        )

    @pytest.fixture
    def sample_var_results(self):
        """Create sample VaR results for testing."""
        from core.analysis.risk.var_calculations import VaRMethodology
        result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.025,
            cvar_estimate=0.030
        )
        result.var_95 = result.var_estimate
        result.var_99 = 0.035
        result.method = "parametric"
        result.distribution = "normal"

        return {
            'parametric': result
        }

    def test_report_creation(self, sample_metadata, sample_metrics, sample_var_results):
        """Test creating a risk report."""
        report = RiskReport(
            metadata=sample_metadata,
            executive_summary="Test summary",
            summary_metrics=sample_metrics,
            var_results=sample_var_results,
            detailed_analysis={},
            recommendations=["Test recommendation"]
        )

        assert report.metadata.report_id == "test_001"
        assert report.executive_summary == "Test summary"
        assert len(report.recommendations) == 1
        assert "parametric" in report.var_results

    def test_report_to_dict(self, sample_metadata, sample_metrics, sample_var_results):
        """Test converting report to dictionary."""
        report = RiskReport(
            metadata=sample_metadata,
            executive_summary="Test summary",
            summary_metrics=sample_metrics,
            var_results=sample_var_results,
            detailed_analysis={"test": "data"},
            recommendations=["Test recommendation"]
        )

        report_dict = report.to_dict()

        assert isinstance(report_dict, dict)
        assert 'metadata' in report_dict
        assert 'executive_summary' in report_dict
        assert 'summary_metrics' in report_dict
        assert 'var_results' in report_dict
        assert report_dict['executive_summary'] == "Test summary"


class TestRiskReporter:
    """Test cases for RiskReporter class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        returns = pd.Series(
            np.random.normal(0.0005, 0.015, len(dates)),
            index=dates,
            name='returns'
        )
        return returns

    @pytest.fixture
    def sample_var_results(self):
        """Create sample VaR results for testing."""
        from core.analysis.risk.var_calculations import VaRMethodology

        param_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.0247,
            cvar_estimate=0.0280
        )
        param_result.var_95 = param_result.var_estimate
        param_result.var_99 = 0.0347
        param_result.cvar_95 = param_result.cvar_estimate
        param_result.cvar_99 = 0.0380
        param_result.method = "parametric_normal"
        param_result.distribution = "normal"

        hist_result = VaRResult(
            methodology=VaRMethodology.HISTORICAL_SIMULATION,
            confidence_level=0.95,
            var_estimate=0.0251,
            cvar_estimate=0.0281
        )
        hist_result.var_95 = hist_result.var_estimate
        hist_result.var_99 = 0.0351
        hist_result.method = "historical_simulation"
        hist_result.distribution = None

        mc_result = VaRResult(
            methodology=VaRMethodology.MONTE_CARLO,
            confidence_level=0.95,
            var_estimate=0.0248,
            cvar_estimate=0.0278
        )
        mc_result.var_95 = mc_result.var_estimate
        mc_result.var_99 = 0.0348
        mc_result.method = "monte_carlo"
        mc_result.distribution = None

        return {
            'Parametric (Normal)': param_result,
            'Historical Simulation': hist_result,
            'Monte Carlo': mc_result
        }

    def test_reporter_initialization(self, temp_dir):
        """Test RiskReporter initialization."""
        reporter = RiskReporter(output_dir=temp_dir)

        assert reporter.output_dir == Path(temp_dir)
        assert reporter.output_dir.exists()

    def test_reporter_initialization_default_dir(self):
        """Test RiskReporter initialization with default directory."""
        reporter = RiskReporter()

        # Check for both Windows and Unix path separators
        output_dir_str = str(reporter.output_dir)
        assert "reports" in output_dir_str and "risk_analysis" in output_dir_str

    def test_generate_comprehensive_report(self, temp_dir, sample_var_results, sample_returns):
        """Test generating comprehensive risk report."""
        reporter = RiskReporter(output_dir=temp_dir)

        report = reporter.generate_comprehensive_report(
            var_results=sample_var_results,
            returns=sample_returns,
            portfolio_value=1000000,
            analysis_id="test_analysis",
            title="Test Risk Report"
        )

        assert isinstance(report, RiskReport)
        assert report.metadata.report_id == "test_analysis"
        assert report.metadata.title == "Test Risk Report"
        assert len(report.var_results) == 3
        assert len(report.recommendations) > 0
        assert report.executive_summary is not None

    def test_generate_comprehensive_report_no_var_results(self, temp_dir, sample_returns):
        """Test generating report with no VaR results raises error."""
        reporter = RiskReporter(output_dir=temp_dir)

        with pytest.raises(ValueError, match="VaR results are required"):
            reporter.generate_comprehensive_report(
                var_results={},
                returns=sample_returns
            )

    def test_calculate_summary_metrics(self, temp_dir, sample_var_results, sample_returns):
        """Test calculation of summary metrics."""
        reporter = RiskReporter(output_dir=temp_dir)

        metrics = reporter._calculate_summary_metrics(
            sample_var_results,
            sample_returns,
            portfolio_value=1000000
        )

        assert isinstance(metrics, RiskSummaryMetrics)
        assert metrics.portfolio_volatility > 0
        assert metrics.mean_return is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.max_drawdown <= 0
        assert metrics.var_95_best is not None
        assert metrics.var_95_worst is not None

    def test_generate_executive_summary(self, temp_dir, sample_var_results, sample_returns):
        """Test executive summary generation."""
        reporter = RiskReporter(output_dir=temp_dir)

        metrics = reporter._calculate_summary_metrics(sample_var_results, sample_returns, None)
        summary = reporter._generate_executive_summary(metrics, sample_var_results, sample_returns)

        assert isinstance(summary, str)
        assert len(summary) > 100  # Should be substantial
        assert "EXECUTIVE SUMMARY" in summary
        assert "Risk Analysis Period" in summary
        assert "KEY FINDINGS" in summary

    def test_generate_recommendations(self, temp_dir, sample_var_results, sample_returns):
        """Test recommendations generation."""
        reporter = RiskReporter(output_dir=temp_dir)

        metrics = reporter._calculate_summary_metrics(sample_var_results, sample_returns, None)
        recommendations = reporter._generate_recommendations(metrics, sample_var_results)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)

    def test_generate_detailed_analysis(self, temp_dir, sample_var_results, sample_returns):
        """Test detailed analysis generation."""
        reporter = RiskReporter(output_dir=temp_dir)

        analysis = reporter._generate_detailed_analysis(sample_var_results, sample_returns, None)

        assert isinstance(analysis, dict)
        assert 'methodology_comparison' in analysis
        assert 'model_performance' in analysis
        assert 'risk_decomposition' in analysis

        # Check methodology comparison
        method_comp = analysis['methodology_comparison']
        assert len(method_comp) == len(sample_var_results)

    def test_export_report_json(self, temp_dir, sample_var_results, sample_returns):
        """Test exporting report to JSON format."""
        reporter = RiskReporter(output_dir=temp_dir)

        report = reporter.generate_comprehensive_report(sample_var_results, sample_returns)
        output_path = reporter.export_report(report, "test_report.json", format="json")

        assert Path(output_path).exists()
        assert output_path.endswith("test_report.json")

        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'executive_summary' in data
        assert 'var_results' in data

    def test_export_report_excel(self, temp_dir, sample_var_results, sample_returns):
        """Test exporting report to Excel format."""
        reporter = RiskReporter(output_dir=temp_dir)

        report = reporter.generate_comprehensive_report(sample_var_results, sample_returns)
        output_path = reporter.export_report(report, "test_report.xlsx", format="excel")

        assert Path(output_path).exists()
        assert output_path.endswith("test_report.xlsx")

        # Verify Excel file can be read
        summary_df = pd.read_excel(output_path, sheet_name='Summary')
        assert len(summary_df) > 0

    def test_export_report_html(self, temp_dir, sample_var_results, sample_returns):
        """Test exporting report to HTML format."""
        reporter = RiskReporter(output_dir=temp_dir)

        report = reporter.generate_comprehensive_report(sample_var_results, sample_returns)
        output_path = reporter.export_report(report, "test_report.html", format="html")

        assert Path(output_path).exists()
        assert output_path.endswith("test_report.html")

        # Verify HTML content
        with open(output_path, 'r') as f:
            html_content = f.read()

        assert "<html>" in html_content
        assert "Risk Report" in html_content
        assert "Executive Summary" in html_content

    def test_export_report_unsupported_format(self, temp_dir, sample_var_results, sample_returns):
        """Test exporting report with unsupported format raises error."""
        reporter = RiskReporter(output_dir=temp_dir)

        report = reporter.generate_comprehensive_report(sample_var_results, sample_returns)

        with pytest.raises(ValueError, match="Unsupported format"):
            reporter.export_report(report, "test_report.txt", format="txt")

    def test_generate_executive_summary_only(self, temp_dir, sample_var_results, sample_returns):
        """Test generating executive summary only."""
        reporter = RiskReporter(output_dir=temp_dir)

        summary = reporter.generate_executive_summary_only(sample_var_results, sample_returns)

        assert isinstance(summary, str)
        assert len(summary) > 100
        assert "EXECUTIVE SUMMARY" in summary

    @patch('ui.visualization.risk_visualizer.RiskVisualizer')
    def test_create_risk_dashboard_report(self, mock_visualizer, temp_dir, sample_var_results, sample_returns):
        """Test creating risk dashboard report."""
        # Mock the visualizer
        mock_viz_instance = Mock()
        mock_visualizer.return_value = mock_viz_instance

        reporter = RiskReporter(output_dir=temp_dir)

        dashboard_data = reporter.create_risk_dashboard_report(
            sample_var_results,
            sample_returns,
            portfolio_value=1000000
        )

        assert isinstance(dashboard_data, dict)
        assert 'summary_metrics' in dashboard_data
        assert 'var_comparison' in dashboard_data
        assert 'generated_at' in dashboard_data

    def test_get_methodology_notes(self, temp_dir):
        """Test methodology notes generation."""
        reporter = RiskReporter(output_dir=temp_dir)

        parametric_notes = reporter._get_methodology_notes('parametric_normal')
        historical_notes = reporter._get_methodology_notes('historical_simulation')
        unknown_notes = reporter._get_methodology_notes('unknown_method')

        assert isinstance(parametric_notes, str)
        assert isinstance(historical_notes, str)
        assert isinstance(unknown_notes, str)
        assert len(parametric_notes) > 20
        assert "distribution" in parametric_notes.lower()


class TestRiskReportingEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_reporter_with_missing_visualizer(self, temp_dir):
        """Test reporter behavior when visualizer is not available."""
        with patch('ui.visualization.risk_visualizer.RiskVisualizer', None):
            reporter = RiskReporter(output_dir=temp_dir)
            assert reporter.visualizer is None

    def test_report_with_extreme_metrics(self, temp_dir):
        """Test report generation with extreme metric values."""
        reporter = RiskReporter(output_dir=temp_dir)

        # Create extreme returns
        extreme_returns = pd.Series([
            -0.5, 0.5, -0.8, 0.8, 0.0, -0.9, 0.9, -0.1, 0.1
        ])

        from core.analysis.risk.var_calculations import VaRMethodology
        test_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.9,
            cvar_estimate=0.95
        )
        test_result.var_95 = test_result.var_estimate
        test_result.var_99 = 0.95
        test_result.method = "test"
        test_result.distribution = "extreme"

        var_results = {
            'Test': test_result
        }

        # Should handle extreme values gracefully
        report = reporter.generate_comprehensive_report(var_results, extreme_returns)

        assert isinstance(report, RiskReport)
        assert report.summary_metrics.portfolio_volatility > 0
        assert len(report.recommendations) > 0

    def test_report_with_single_observation(self, temp_dir):
        """Test report generation with single observation."""
        reporter = RiskReporter(output_dir=temp_dir)

        single_return = pd.Series([0.01])
        from core.analysis.risk.var_calculations import VaRMethodology
        test_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.05,
            cvar_estimate=0.06
        )
        test_result.var_95 = test_result.var_estimate
        test_result.var_99 = 0.08
        test_result.method = "test"
        test_result.distribution = "test"

        var_results = {
            'Test': test_result
        }

        # Should handle single observation gracefully or raise informative error
        try:
            report = reporter.generate_comprehensive_report(var_results, single_return)
            assert isinstance(report, RiskReport)
        except Exception as e:
            # Some statistical calculations might fail with single observation
            assert "variance" in str(e).lower() or "insufficient" in str(e).lower()

    def test_recommendations_for_different_risk_profiles(self, temp_dir):
        """Test recommendations generation for different risk profiles."""
        reporter = RiskReporter(output_dir=temp_dir)

        # Low volatility scenario
        low_vol_metrics = RiskSummaryMetrics(
            portfolio_volatility=0.03,  # Very low
            mean_return=0.02,
            sharpe_ratio=0.6,
            max_drawdown=-0.02,
            skewness=0.1,
            kurtosis=0.5,
            var_95_best=-0.01,
            var_95_worst=-0.015,
            var_99_best=-0.02,
            var_99_worst=-0.025,
            backtesting_passed=True,
            violation_rate=0.05,
            model_accuracy=0.95
        )

        # High volatility scenario
        high_vol_metrics = RiskSummaryMetrics(
            portfolio_volatility=0.30,  # Very high
            mean_return=0.10,
            sharpe_ratio=0.3,
            max_drawdown=-0.25,
            skewness=-1.5,  # Negative skew
            kurtosis=5.0,   # Fat tails
            var_95_best=-0.05,
            var_95_worst=-0.08,
            var_99_best=-0.10,
            var_99_worst=-0.15,
            backtesting_passed=False,
            violation_rate=0.08,
            model_accuracy=0.85
        )

        low_vol_recs = reporter._generate_recommendations(low_vol_metrics, {})
        high_vol_recs = reporter._generate_recommendations(high_vol_metrics, {})

        # Should generate appropriate recommendations for each scenario
        assert len(low_vol_recs) > 0
        assert len(high_vol_recs) > 0

        # High volatility should generate more and different recommendations
        low_vol_text = " ".join(low_vol_recs).lower()
        high_vol_text = " ".join(high_vol_recs).lower()

        assert "volatility" in high_vol_text or "diversification" in high_vol_text
        assert "skew" in high_vol_text or "tail" in high_vol_text


class TestRiskReportingIntegration:
    """Test cases for integration with other modules."""

    @patch('core.analysis.risk.var_calculations.VaRCalculator')
    def test_integration_with_var_calculator(self, mock_calculator, temp_dir):
        """Test integration with VaR calculator."""
        # Mock VaR calculator
        mock_calc_instance = Mock()
        mock_calculator.return_value = mock_calc_instance

        reporter = RiskReporter(output_dir=temp_dir)

        # Test would involve actual integration
        # This is a placeholder for integration testing
        assert reporter is not None

    @patch('ui.visualization.risk_visualizer.RiskVisualizer')
    def test_integration_with_visualizer(self, mock_visualizer, temp_dir):
        """Test integration with risk visualizer."""
        # Mock visualizer
        mock_viz_instance = Mock()
        mock_viz_instance.create_risk_dashboard.return_value = Mock()
        mock_visualizer.return_value = mock_viz_instance

        reporter = RiskReporter(output_dir=temp_dir)

        # Test chart generation integration
        returns = pd.Series([0.01, -0.02, 0.015])
        from core.analysis.risk.var_calculations import VaRMethodology
        test_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.025,
            cvar_estimate=0.030
        )
        test_result.var_95 = test_result.var_estimate
        test_result.var_99 = 0.035
        test_result.method = "test"
        test_result.distribution = "normal"

        var_results = {
            'Test': test_result
        }

        charts = reporter._generate_charts(var_results, returns, None)

        assert isinstance(charts, dict)


if __name__ == "__main__":
    pytest.main([__file__])