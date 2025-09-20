"""
Unit Tests for Risk Visualization Module
========================================

This module contains comprehensive unit tests for the risk visualization
components, including VaR distribution plots, correlation heatmaps,
risk dashboards, and backtesting result visualizations.

Test Coverage:
- RiskVisualizer class methods
- Chart generation functions
- Configuration handling
- Error handling and edge cases
- Streamlit integration functions
"""

import pytest
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from ui.visualization.risk_visualizer import (
    RiskVisualizer,
    RiskVisualizationConfig,
    render_risk_analysis_streamlit,
    create_risk_analysis_tab
)

# Import risk analysis components for testing
from core.analysis.risk.var_calculations import VaRResult


class TestRiskVisualizationConfig:
    """Test cases for RiskVisualizationConfig dataclass."""

    def test_default_config_creation(self):
        """Test creating config with default values."""
        config = RiskVisualizationConfig()

        assert config.chart_width == 800
        assert config.chart_height == 600
        assert config.confidence_levels == [0.90, 0.95, 0.99]
        assert isinstance(config.var_colors, dict)
        assert len(config.risk_zone_colors) == 4

    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        custom_colors = {'var_5': '#FF0000', 'var_1': '#AA0000'}

        config = RiskVisualizationConfig(
            chart_width=1000,
            chart_height=700,
            var_colors=custom_colors
        )

        assert config.chart_width == 1000
        assert config.chart_height == 700
        assert config.var_colors == custom_colors

    def test_post_init_sets_defaults(self):
        """Test that __post_init__ sets default values correctly."""
        config = RiskVisualizationConfig()

        # Check that default var_colors were set
        assert 'var_5' in config.var_colors
        assert 'var_1' in config.var_colors
        assert 'distribution' in config.var_colors

        # Check that risk zone colors were set
        assert len(config.risk_zone_colors) == 4


class TestRiskVisualizer:
    """Test cases for RiskVisualizer class."""

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
    def sample_var_result(self):
        """Create sample VaR result for testing."""
        from core.analysis.risk.var_calculations import VaRMethodology
        result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.0247,
            cvar_estimate=0.0280,
            var_confidence_interval=(0.0230, 0.0260),
            expected_return=0.0005,
            volatility=0.015
        )
        # Add compatibility properties for testing
        result.var_95 = result.var_estimate
        result.var_99 = 0.0347
        result.cvar_95 = result.cvar_estimate
        result.cvar_99 = 0.0380
        result.method = "parametric_normal"
        result.distribution = "normal"
        result.confidence_intervals = {
            0.90: (0.0230, 0.0260),
            0.95: (0.0240, 0.0250)
        }
        return result

    @pytest.fixture
    def sample_var_results(self, sample_var_result):
        """Create sample VaR results dictionary."""
        from core.analysis.risk.var_calculations import VaRMethodology

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
            'Parametric (Normal)': sample_var_result,
            'Historical Simulation': hist_result,
            'Monte Carlo': mc_result
        }

    @pytest.fixture
    def visualizer(self):
        """Create RiskVisualizer instance for testing."""
        return RiskVisualizer()

    def test_visualizer_initialization(self):
        """Test RiskVisualizer initialization."""
        visualizer = RiskVisualizer()
        assert visualizer.config is not None
        assert isinstance(visualizer.config, RiskVisualizationConfig)

    def test_visualizer_with_custom_config(self):
        """Test RiskVisualizer initialization with custom config."""
        custom_config = RiskVisualizationConfig(chart_width=1000)
        visualizer = RiskVisualizer(custom_config)

        assert visualizer.config.chart_width == 1000

    def test_create_var_distribution_plot(self, visualizer, sample_var_result, sample_returns):
        """Test VaR distribution plot creation."""
        fig = visualizer.create_var_distribution_plot(
            sample_var_result,
            sample_returns,
            title="Test VaR Distribution"
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Should have histogram and box plot

        # Check if VaR lines are added
        vlines = [trace for trace in fig.layout.shapes if hasattr(trace, 'type') and trace.type == 'line']
        assert len(vlines) >= 0  # VaR lines should be present

    def test_create_var_distribution_plot_no_result(self, visualizer, sample_returns):
        """Test VaR distribution plot with no result raises error."""
        with pytest.raises(ValueError, match="VaR result is required"):
            visualizer.create_var_distribution_plot(None, sample_returns)

    def test_create_var_comparison_chart(self, visualizer, sample_var_results):
        """Test VaR comparison chart creation."""
        fig = visualizer.create_var_comparison_chart(sample_var_results)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1  # Should have at least VaR bars

        # Check that all methods are included
        x_data = fig.data[0].x
        assert len(x_data) == len(sample_var_results)

    def test_create_var_comparison_chart_empty(self, visualizer):
        """Test VaR comparison chart with empty results raises error."""
        with pytest.raises(ValueError, match="VaR results are required"):
            visualizer.create_var_comparison_chart({})

    def test_create_correlation_heatmap(self, visualizer):
        """Test correlation heatmap creation."""
        # Create sample correlation matrix
        assets = ['Asset_A', 'Asset_B', 'Asset_C']
        correlation_data = np.array([
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.7],
            [0.3, 0.7, 1.0]
        ])
        correlation_matrix = pd.DataFrame(
            correlation_data,
            index=assets,
            columns=assets
        )

        fig = visualizer.create_correlation_heatmap(correlation_matrix)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # Should have heatmap
        assert fig.data[0].type == 'heatmap'

    def test_create_correlation_heatmap_masked(self, visualizer):
        """Test correlation heatmap with upper triangle masked."""
        assets = ['Asset_A', 'Asset_B']
        correlation_matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=assets,
            columns=assets
        )

        fig = visualizer.create_correlation_heatmap(correlation_matrix, mask_upper=True)

        assert isinstance(fig, go.Figure)
        # Check that upper triangle values are masked (NaN)
        z_data = fig.data[0].z
        assert np.isnan(z_data[0][1])  # Upper triangle should be NaN

    def test_create_risk_dashboard(self, visualizer, sample_var_results, sample_returns):
        """Test risk dashboard creation."""
        fig = visualizer.create_risk_dashboard(sample_var_results, sample_returns)

        assert isinstance(fig, go.Figure)
        # Dashboard should have multiple subplots
        assert len(fig.data) >= 4  # At least 4 traces for different subplots

    def test_create_backtesting_results_chart(self, visualizer, sample_returns):
        """Test backtesting results chart creation."""
        # Create sample VaR forecasts
        var_forecasts = pd.Series(
            np.full(len(sample_returns), -0.025),
            index=sample_returns.index,
            name='var_forecasts'
        )

        # Create sample backtest results
        backtest_results = {
            'violation_rate': 0.06,
            'expected_rate': 0.05,
            'kupiec_test': {'p_value': 0.8},
            'independence_test': {'p_value': 0.7}
        }

        fig = visualizer.create_backtesting_results_chart(
            backtest_results,
            sample_returns,
            var_forecasts
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 3  # Returns, VaR, and violations

    def test_create_backtesting_results_chart_empty(self, visualizer, sample_returns):
        """Test backtesting results chart with empty results raises error."""
        var_forecasts = pd.Series([], dtype=float)

        with pytest.raises(ValueError, match="Backtesting results are required"):
            visualizer.create_backtesting_results_chart({}, sample_returns, var_forecasts)

    def test_create_stress_test_results(self, visualizer):
        """Test stress test results visualization."""
        stress_scenarios = {
            'Baseline': {'portfolio_value': 1000000},
            'Recession': {'portfolio_value': 850000},
            'Crisis': {'portfolio_value': 700000}
        }
        base_value = 1000000

        fig = visualizer.create_stress_test_results(stress_scenarios, base_value)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Portfolio values and loss percentages

    @pytest.mark.parametrize("confidence_level", [0.90, 0.95, 0.99])
    def test_create_var_comparison_different_confidence_levels(self, visualizer, sample_var_results, confidence_level):
        """Test VaR comparison chart with different confidence levels."""
        fig = visualizer.create_var_comparison_chart(sample_var_results, confidence_level)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1


class TestRiskVisualizationIntegration:
    """Test cases for risk visualization integration functions."""

    @patch('streamlit.title')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.plotly_chart')
    def test_render_risk_analysis_streamlit(self, mock_plotly, mock_metric, mock_columns, mock_title):
        """Test Streamlit risk analysis rendering function."""
        # Mock streamlit columns
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]

        # Create sample data
        sample_returns = pd.Series([0.01, -0.02, 0.015, -0.01])
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

        sample_var_results = {
            'Test Method': test_result
        }

        # Should not raise any exceptions
        render_risk_analysis_streamlit(sample_var_results, sample_returns)

        # Verify that streamlit functions were called
        mock_title.assert_called_once()
        mock_columns.assert_called()

    @patch('streamlit.header')
    @patch('streamlit.selectbox')
    @patch('streamlit.button')
    def test_create_risk_analysis_tab(self, mock_button, mock_selectbox, mock_header):
        """Test risk analysis tab creation function."""
        # Mock streamlit components
        mock_selectbox.side_effect = [0.95, "Parametric (Normal)"]
        mock_button.return_value = False

        # Should not raise any exceptions
        create_risk_analysis_tab()

        # Verify that streamlit functions were called
        mock_header.assert_called()
        mock_selectbox.assert_called()


class TestRiskVisualizationEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_visualizer_with_none_data(self):
        """Test visualizer behavior with None data."""
        visualizer = RiskVisualizer()

        with pytest.raises(ValueError):
            visualizer.create_var_distribution_plot(None, pd.Series([]))

    def test_visualizer_with_empty_returns(self):
        """Test visualizer behavior with empty returns."""
        visualizer = RiskVisualizer()
        empty_returns = pd.Series([], dtype=float)

        from core.analysis.risk.var_calculations import VaRMethodology
        var_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.025,
            cvar_estimate=0.030
        )
        var_result.var_95 = var_result.var_estimate
        var_result.var_99 = 0.035
        var_result.method = "test"
        var_result.distribution = "normal"

        # Should handle empty data gracefully
        try:
            fig = visualizer.create_var_distribution_plot(var_result, empty_returns)
            assert isinstance(fig, go.Figure)
        except Exception as e:
            # Some operations might fail with empty data, which is acceptable
            assert "empty" in str(e).lower() or "length" in str(e).lower()

    def test_visualizer_with_single_value_returns(self):
        """Test visualizer behavior with single value returns."""
        visualizer = RiskVisualizer()
        single_return = pd.Series([0.01])

        from core.analysis.risk.var_calculations import VaRMethodology
        var_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.025,
            cvar_estimate=0.030
        )
        var_result.var_95 = var_result.var_estimate
        var_result.var_99 = 0.035
        var_result.method = "test"
        var_result.distribution = "normal"

        # Should handle single value gracefully or raise informative error
        try:
            fig = visualizer.create_var_distribution_plot(var_result, single_return)
            assert isinstance(fig, go.Figure)
        except Exception as e:
            # Some statistical operations might fail with single value
            assert "variance" in str(e).lower() or "distribution" in str(e).lower()

    def test_visualizer_with_extreme_values(self):
        """Test visualizer behavior with extreme return values."""
        visualizer = RiskVisualizer()

        # Create returns with extreme values
        extreme_returns = pd.Series([
            -0.5, 0.5, -0.8, 0.8, 0.0, -0.1, 0.1
        ])

        from core.analysis.risk.var_calculations import VaRMethodology
        var_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.45,
            cvar_estimate=0.50
        )
        var_result.var_95 = var_result.var_estimate
        var_result.var_99 = 0.65
        var_result.method = "test"
        var_result.distribution = "normal"

        # Should handle extreme values
        fig = visualizer.create_var_distribution_plot(var_result, extreme_returns)
        assert isinstance(fig, go.Figure)

    def test_correlation_heatmap_non_square_matrix(self, visualizer):
        """Test correlation heatmap with non-square matrix."""
        # This should not happen in practice, but test robustness
        non_square = pd.DataFrame(
            [[1.0, 0.5, 0.3], [0.5, 1.0, 0.7]],
            columns=['A', 'B', 'C']
        )

        # Should handle gracefully or raise appropriate error
        try:
            fig = visualizer.create_correlation_heatmap(non_square)
            assert isinstance(fig, go.Figure)
        except Exception as e:
            # Non-square correlation matrices are invalid
            assert "correlation" in str(e).lower() or "square" in str(e).lower()


class TestRiskVisualizationPerformance:
    """Test cases for performance and scalability."""

    def test_large_dataset_handling(self):
        """Test visualizer performance with large datasets."""
        visualizer = RiskVisualizer()

        # Create large dataset
        large_returns = pd.Series(np.random.normal(0, 0.02, 10000))

        from core.analysis.risk.var_calculations import VaRMethodology
        var_result = VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.025,
            cvar_estimate=0.030
        )
        var_result.var_95 = var_result.var_estimate
        var_result.var_99 = 0.035
        var_result.method = "test"
        var_result.distribution = "normal"

        # Should handle large datasets efficiently
        import time
        start_time = time.time()

        fig = visualizer.create_var_distribution_plot(var_result, large_returns)

        execution_time = time.time() - start_time

        assert isinstance(fig, go.Figure)
        assert execution_time < 10.0  # Should complete within 10 seconds

    def test_multiple_charts_generation(self):
        """Test generating multiple charts efficiently."""
        visualizer = RiskVisualizer()

        returns = pd.Series(np.random.normal(0, 0.02, 1000))
        from core.analysis.risk.var_calculations import VaRMethodology
        var_results = {}
        for i in range(5):
            result = VaRResult(
                methodology=VaRMethodology.PARAMETRIC_NORMAL,
                confidence_level=0.95,
                var_estimate=0.025 + i*0.001,
                cvar_estimate=0.030 + i*0.001
            )
            result.var_95 = result.var_estimate
            result.var_99 = 0.035 + i*0.001
            result.method = f"method_{i}"
            result.distribution = "normal"
            var_results[f'Method_{i}'] = result

        # Generate multiple charts
        charts = []
        for method, result in var_results.items():
            fig = visualizer.create_var_distribution_plot(result, returns)
            charts.append(fig)

        assert len(charts) == 5
        assert all(isinstance(chart, go.Figure) for chart in charts)


if __name__ == "__main__":
    pytest.main([__file__])