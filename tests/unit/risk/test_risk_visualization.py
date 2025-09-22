"""
Tests for Risk Visualization Module
===================================

Comprehensive test suite for risk visualization and reporting components.
Tests all visualization types, dashboard functionality, and export capabilities.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import plotly.graph_objects as go

from core.analysis.risk.risk_visualization import (
    RiskVisualizationEngine,
    ProbabilityDistributionPlotter,
    RiskHeatmapGenerator,
    SensitivityChartBuilder,
    MonteCarloVisualizer,
    VisualizationConfig,
    VisualizationSuite,
    VisualizationType
)
from core.analysis.risk.risk_framework import RiskAnalysisResult
from core.analysis.risk.risk_metrics import RiskMetrics, RiskType, RiskLevel
from core.analysis.risk.correlation_analysis import CorrelationMatrix, CorrelationMethod
from core.analysis.risk.probability_distributions import ProbabilityDistribution, DistributionType
from core.analysis.statistics.monte_carlo_engine import SimulationResult


class TestVisualizationConfig:
    """Test visualization configuration."""

    def test_default_config_creation(self):
        """Test default configuration creation."""
        config = VisualizationConfig()

        assert config.width == 800
        assert config.height == 600
        assert isinstance(config.color_palette, list)
        assert config.risk_color_scale == "RdYlBu_r"
        assert config.font_family == "Arial, sans-serif"
        assert config.enable_zoom is True

    def test_custom_config_creation(self):
        """Test custom configuration creation."""
        custom_colors = ['#FF0000', '#00FF00', '#0000FF']
        config = VisualizationConfig(
            width=1000,
            height=800,
            color_palette=custom_colors,
            risk_color_scale="Viridis"
        )

        assert config.width == 1000
        assert config.height == 800
        assert config.color_palette == custom_colors
        assert config.risk_color_scale == "Viridis"

    def test_confidence_levels_setting(self):
        """Test confidence levels configuration."""
        custom_levels = [0.90, 0.95, 0.99, 0.999]
        config = VisualizationConfig(confidence_levels=custom_levels)

        assert config.confidence_levels == custom_levels


class TestProbabilityDistributionPlotter:
    """Test probability distribution plotter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return VisualizationConfig()

    @pytest.fixture
    def plotter(self, config):
        """Create distribution plotter."""
        return ProbabilityDistributionPlotter(config)

    @pytest.fixture
    def sample_data(self):
        """Create sample empirical data."""
        np.random.seed(42)
        return pd.Series(np.random.normal(0, 1, 1000))

    @pytest.fixture
    def mock_distribution(self):
        """Create mock fitted distribution."""
        mock_dist = Mock(spec=ProbabilityDistribution)
        mock_dist.distribution_type = DistributionType.NORMAL
        mock_dist.pdf.side_effect = lambda x: np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
        mock_dist.cdf.side_effect = lambda x: 0.5 * (1 + np.tanh(x / np.sqrt(2)))
        mock_dist.ppf.side_effect = lambda q: np.sqrt(2) * np.arctanh(2 * q - 1)
        mock_dist.var.side_effect = lambda alpha: -1.645 if alpha == 0.05 else -2.326
        return mock_dist

    def test_plot_distribution_analysis_empirical_only(self, plotter, sample_data):
        """Test distribution analysis plot with empirical data only."""
        fig = plotter.plot_distribution_analysis(sample_data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1  # At least empirical histogram
        assert fig.layout.title.text == "Distribution Analysis"

    def test_plot_distribution_analysis_with_fitted(self, plotter, sample_data, mock_distribution):
        """Test distribution analysis plot with fitted distribution."""
        fig = plotter.plot_distribution_analysis(
            sample_data,
            fitted_distribution=mock_distribution,
            confidence_levels=[0.95, 0.99]
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Empirical + fitted
        # Should have VaR lines
        assert any('VaR' in str(annotation.text) for annotation in fig.layout.annotations)

    def test_qq_plot_addition(self, plotter, sample_data, mock_distribution):
        """Test Q-Q plot addition to distribution analysis."""
        fig = plotter.plot_distribution_analysis(sample_data, mock_distribution)

        # Check that subplots were created
        assert hasattr(fig, '_grid_ref')
        assert len(fig.data) >= 4  # Histogram, fitted curve, QQ plot, PP plot

    def test_var_markers_addition(self, plotter, sample_data):
        """Test VaR markers addition."""
        confidence_levels = [0.90, 0.95, 0.99]
        fig = plotter.plot_distribution_analysis(sample_data, confidence_levels=confidence_levels)

        # Should have VaR lines for each confidence level
        vlines = [shape for shape in fig.layout.shapes if shape.type == 'line']
        assert len(vlines) >= len(confidence_levels)

    def test_empty_data_handling(self, plotter):
        """Test handling of empty data."""
        empty_data = pd.Series([])
        fig = plotter.plot_distribution_analysis(empty_data)

        assert isinstance(fig, go.Figure)


class TestRiskHeatmapGenerator:
    """Test risk heatmap generator."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return VisualizationConfig()

    @pytest.fixture
    def generator(self, config):
        """Create heatmap generator."""
        return RiskHeatmapGenerator(config)

    @pytest.fixture
    def sample_risk_metrics(self):
        """Create sample risk metrics."""
        metrics = {}
        for asset in ['AAPL', 'GOOGL', 'MSFT']:
            metrics[asset] = RiskMetrics(
                var_1day_95=-0.02,
                var_1day_99=-0.03,
                annual_volatility=0.25,
                max_drawdown=-0.15,
                sharpe_ratio=1.2
            )
        return metrics

    @pytest.fixture
    def sample_correlation_matrix(self):
        """Create sample correlation matrix."""
        data = np.array([[1.0, 0.7, 0.6], [0.7, 1.0, 0.8], [0.6, 0.8, 1.0]])
        df = pd.DataFrame(data, columns=['AAPL', 'GOOGL', 'MSFT'], index=['AAPL', 'GOOGL', 'MSFT'])

        mock_corr_matrix = Mock(spec=CorrelationMatrix)
        mock_corr_matrix.to_dataframe.return_value = df
        return mock_corr_matrix

    def test_risk_concentration_heatmap_creation(self, generator, sample_risk_metrics):
        """Test risk concentration heatmap creation."""
        risk_types = [RiskType.MARKET, RiskType.CREDIT, RiskType.LIQUIDITY]

        fig = generator.create_risk_concentration_heatmap(sample_risk_metrics, risk_types)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # One heatmap trace
        assert fig.data[0].type == 'heatmap'
        assert fig.layout.title.text == "Risk Concentration Heatmap"

    def test_correlation_heatmap_creation(self, generator, sample_correlation_matrix):
        """Test correlation heatmap creation."""
        fig = generator.create_correlation_heatmap(sample_correlation_matrix)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # One heatmap trace
        assert fig.data[0].type == 'heatmap'
        assert fig.layout.title.text == "Asset Correlation Matrix"

    def test_correlation_heatmap_with_clustering(self, generator, sample_correlation_matrix):
        """Test correlation heatmap with clustering."""
        fig = generator.create_correlation_heatmap(
            sample_correlation_matrix,
            cluster=True,
            show_significance=True
        )

        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == 'heatmap'

    def test_market_risk_score_calculation(self, generator):
        """Test market risk score calculation."""
        metrics = RiskMetrics(
            var_1day_95=-0.05,  # High VaR
            annual_volatility=0.30,  # High volatility
            max_drawdown=-0.20  # Large drawdown
        )

        score = generator._calculate_market_risk_score(metrics)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 50  # Should be high risk

    def test_hierarchical_clustering(self, generator):
        """Test hierarchical clustering application."""
        # Create correlation matrix with clear clusters
        corr_data = pd.DataFrame({
            'A': [1.0, 0.9, 0.1, 0.1],
            'B': [0.9, 1.0, 0.1, 0.1],
            'C': [0.1, 0.1, 1.0, 0.8],
            'D': [0.1, 0.1, 0.8, 1.0]
        }, index=['A', 'B', 'C', 'D'])

        clustered_corr = generator._apply_hierarchical_clustering(corr_data)

        assert isinstance(clustered_corr, pd.DataFrame)
        assert clustered_corr.shape == corr_data.shape
        # Assets A,B should be clustered together, and C,D together


class TestSensitivityChartBuilder:
    """Test sensitivity chart builder."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return VisualizationConfig()

    @pytest.fixture
    def builder(self, config):
        """Create sensitivity chart builder."""
        return SensitivityChartBuilder(config)

    @pytest.fixture
    def sample_sensitivity_results(self):
        """Create sample sensitivity analysis results."""
        return {
            'discount_rate': {'low': 90, 'high': 110},
            'revenue_growth': {'low': 85, 'high': 115},
            'terminal_growth': {'low': 95, 'high': 105},
            'market_volatility': {'low': 80, 'high': 120}
        }

    def test_tornado_chart_creation(self, builder, sample_sensitivity_results):
        """Test tornado chart creation."""
        base_value = 100

        fig = builder.create_tornado_chart(
            sample_sensitivity_results,
            base_value,
            title="Test Sensitivity"
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Upside and downside bars
        assert fig.layout.title.text == "Test Sensitivity"
        assert fig.layout.barmode == 'overlay'

    def test_tornado_chart_sorting(self, builder, sample_sensitivity_results):
        """Test tornado chart parameter sorting by impact."""
        base_value = 100
        fig = builder.create_tornado_chart(sample_sensitivity_results, base_value)

        # Parameters should be sorted by total impact (largest range first)
        y_values = fig.data[0].y
        assert len(y_values) == len(sample_sensitivity_results)

    def test_spider_chart_creation(self, builder, sample_sensitivity_results):
        """Test sensitivity spider chart creation."""
        base_value = 100

        fig = builder.create_sensitivity_spider_chart(sample_sensitivity_results, base_value)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Upside and downside traces
        assert fig.layout.title.text == "Sensitivity Spider Chart"

    def test_empty_sensitivity_results(self, builder):
        """Test handling of empty sensitivity results."""
        empty_results = {}
        base_value = 100

        fig = builder.create_tornado_chart(empty_results, base_value)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Still has upside/downside traces (empty)


class TestMonteCarloVisualizer:
    """Test Monte Carlo visualizer."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return VisualizationConfig()

    @pytest.fixture
    def visualizer(self, config):
        """Create Monte Carlo visualizer."""
        return MonteCarloVisualizer(config)

    @pytest.fixture
    def sample_simulation_result(self):
        """Create sample simulation result."""
        np.random.seed(42)
        simulated_values = np.random.normal(100, 15, 10000)

        mock_result = Mock(spec=SimulationResult)
        mock_result.simulated_values = simulated_values
        mock_result.statistics = {
            'mean': np.mean(simulated_values),
            'std': np.std(simulated_values),
            'var_95': np.percentile(simulated_values, 5),
            'var_99': np.percentile(simulated_values, 1)
        }
        return mock_result

    def test_simulation_histogram_creation(self, visualizer, sample_simulation_result):
        """Test Monte Carlo simulation histogram creation."""
        confidence_levels = [0.95, 0.99]

        fig = visualizer.create_simulation_histogram(
            sample_simulation_result,
            confidence_levels
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1  # At least histogram
        assert fig.data[0].type == 'histogram'
        assert fig.layout.title.text == "Monte Carlo Simulation Results"

        # Should have VaR lines
        vlines = [shape for shape in fig.layout.shapes if shape.type == 'line']
        assert len(vlines) >= len(confidence_levels) + 1  # VaRs + mean line

    def test_convergence_plot_creation(self, visualizer, sample_simulation_result):
        """Test convergence plot creation."""
        fig = visualizer.create_convergence_plot(sample_simulation_result)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 3  # Mean, std, VaR convergence
        assert fig.layout.title.text == "Monte Carlo Convergence Analysis"

    def test_convergence_plot_log_scale(self, visualizer, sample_simulation_result):
        """Test convergence plot uses log scale for x-axis."""
        fig = visualizer.create_convergence_plot(sample_simulation_result)

        # Check that x-axis is log scale
        assert fig.layout.xaxis3.type == "log"

    def test_small_simulation_handling(self, visualizer):
        """Test handling of small simulation results."""
        # Create very small simulation
        small_values = np.array([100, 101, 99, 102, 98])
        mock_result = Mock(spec=SimulationResult)
        mock_result.simulated_values = small_values

        fig = visualizer.create_simulation_histogram(mock_result)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1


class TestRiskVisualizationEngine:
    """Test risk visualization engine."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return VisualizationConfig()

    @pytest.fixture
    def engine(self, config):
        """Create visualization engine."""
        return RiskVisualizationEngine(config)

    @pytest.fixture
    def sample_risk_result(self):
        """Create sample risk analysis result."""
        result = Mock(spec=RiskAnalysisResult)
        result.analysis_id = "test_analysis_001"
        result.analysis_date = datetime.now()
        result.overall_risk_score = 65.5
        result.risk_level = RiskLevel.MEDIUM
        result.key_risk_drivers = ["Market volatility", "Correlation concentration"]

        # Risk metrics
        result.risk_metrics = RiskMetrics(
            var_1day_95=-0.025,
            var_1day_99=-0.035,
            annual_volatility=0.22,
            max_drawdown=-0.18,
            sharpe_ratio=1.15
        )

        # Correlation matrices
        corr_data = pd.DataFrame(
            [[1.0, 0.6, 0.7], [0.6, 1.0, 0.5], [0.7, 0.5, 1.0]],
            columns=['A', 'B', 'C'], index=['A', 'B', 'C']
        )
        mock_corr = Mock(spec=CorrelationMatrix)
        mock_corr.to_dataframe.return_value = corr_data
        result.correlation_matrices = {CorrelationMethod.PEARSON.value: mock_corr}

        # Monte Carlo results
        np.random.seed(42)
        mock_mc = Mock(spec=SimulationResult)
        mock_mc.simulated_values = np.random.normal(100, 15, 1000)
        result.monte_carlo_results = {'portfolio_return': mock_mc}

        return result

    def test_engine_initialization(self, engine):
        """Test visualization engine initialization."""
        assert engine.config is not None
        assert engine.distribution_plotter is not None
        assert engine.heatmap_generator is not None
        assert engine.sensitivity_builder is not None
        assert engine.monte_carlo_visualizer is not None

    def test_comprehensive_visualizations_creation(self, engine, sample_risk_result):
        """Test comprehensive visualization suite creation."""
        suite = engine.create_comprehensive_visualizations(sample_risk_result)

        assert isinstance(suite, VisualizationSuite)
        assert isinstance(suite.risk_heatmaps, dict)
        assert isinstance(suite.monte_carlo_plots, dict)
        assert isinstance(suite.summary_statistics, dict)
        assert suite.generation_metadata is not None

    def test_risk_dashboard_creation(self, engine, sample_risk_result):
        """Test risk dashboard creation."""
        dashboard = engine.create_risk_dashboard(sample_risk_result)

        assert isinstance(dashboard, go.Figure)
        assert dashboard.layout.title.text == "Risk Analysis Dashboard"

    def test_summary_statistics_extraction(self, engine, sample_risk_result):
        """Test summary statistics extraction."""
        stats = engine._extract_summary_statistics(sample_risk_result)

        assert 'risk_metrics' in stats
        assert 'overall_risk' in stats
        assert stats['risk_metrics']['var_95'] == -0.025
        assert stats['overall_risk']['risk_score'] == 65.5

    @patch('core.analysis.risk.risk_visualization.logger')
    def test_visualization_error_handling(self, mock_logger, engine):
        """Test error handling in visualization creation."""
        # Create invalid risk result
        invalid_result = Mock()
        invalid_result.analysis_id = "invalid"
        invalid_result.correlation_matrices = None
        invalid_result.monte_carlo_results = None

        # Should handle errors gracefully
        suite = engine.create_comprehensive_visualizations(invalid_result)
        assert isinstance(suite, VisualizationSuite)

    def test_export_risk_report_html(self, engine, sample_risk_result):
        """Test HTML report export."""
        output_path = "test_report.html"

        # Should not raise exception
        engine.export_risk_report(sample_risk_result, output_path, format="html")

    def test_export_risk_report_unsupported_format(self, engine, sample_risk_result):
        """Test handling of unsupported export format."""
        output_path = "test_report.xyz"

        # Should handle gracefully and log warning
        with patch('core.analysis.risk.risk_visualization.logger') as mock_logger:
            engine.export_risk_report(sample_risk_result, output_path, format="xyz")
            mock_logger.warning.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for risk visualization scenarios."""

    @pytest.fixture
    def engine(self):
        """Create visualization engine."""
        return RiskVisualizationEngine()

    def test_complete_visualization_workflow(self, engine):
        """Test complete visualization workflow from risk result to dashboard."""
        # Create comprehensive risk result
        result = Mock(spec=RiskAnalysisResult)
        result.analysis_id = "integration_test"
        result.analysis_date = datetime.now()
        result.overall_risk_score = 75.0
        result.risk_level = RiskLevel.HIGH

        # Add all components
        result.risk_metrics = RiskMetrics(var_1day_95=-0.03, annual_volatility=0.25)

        corr_data = pd.DataFrame([[1.0, 0.8], [0.8, 1.0]], columns=['A', 'B'], index=['A', 'B'])
        mock_corr = Mock(spec=CorrelationMatrix)
        mock_corr.to_dataframe.return_value = corr_data
        result.correlation_matrices = {'pearson': mock_corr}

        mock_mc = Mock(spec=SimulationResult)
        mock_mc.simulated_values = np.random.normal(100, 10, 1000)
        result.monte_carlo_results = {'test': mock_mc}

        # Create full visualization suite
        suite = engine.create_comprehensive_visualizations(result)

        # Verify all components created
        assert isinstance(suite, VisualizationSuite)
        assert len(suite.risk_heatmaps) > 0
        assert len(suite.monte_carlo_plots) > 0
        assert suite.summary_statistics is not None

        # Create dashboard
        dashboard = engine.create_risk_dashboard(result)
        assert isinstance(dashboard, go.Figure)

    def test_empty_result_handling(self, engine):
        """Test handling of empty risk analysis result."""
        empty_result = Mock(spec=RiskAnalysisResult)
        empty_result.analysis_id = "empty_test"
        empty_result.analysis_date = datetime.now()
        empty_result.correlation_matrices = {}
        empty_result.monte_carlo_results = {}
        empty_result.risk_metrics = None

        # Should handle gracefully
        suite = engine.create_comprehensive_visualizations(empty_result)
        assert isinstance(suite, VisualizationSuite)

    def test_partial_result_handling(self, engine):
        """Test handling of partial risk analysis result."""
        partial_result = Mock(spec=RiskAnalysisResult)
        partial_result.analysis_id = "partial_test"
        partial_result.analysis_date = datetime.now()

        # Only correlation data available
        corr_data = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], columns=['X', 'Y'], index=['X', 'Y'])
        mock_corr = Mock(spec=CorrelationMatrix)
        mock_corr.to_dataframe.return_value = corr_data
        partial_result.correlation_matrices = {'pearson': mock_corr}
        partial_result.monte_carlo_results = {}
        partial_result.risk_metrics = None

        # Should handle gracefully and create available visualizations
        suite = engine.create_comprehensive_visualizations(partial_result)
        assert isinstance(suite, VisualizationSuite)
        assert len(suite.risk_heatmaps) > 0
        assert len(suite.monte_carlo_plots) == 0  # No MC results


@pytest.mark.parametrize("viz_type", [
    VisualizationType.DISTRIBUTION_PLOT,
    VisualizationType.RISK_HEATMAP,
    VisualizationType.TORNADO_CHART,
    VisualizationType.MONTE_CARLO_HISTOGRAM
])
def test_visualization_type_enum(viz_type):
    """Test visualization type enumeration."""
    assert isinstance(viz_type, VisualizationType)
    assert isinstance(viz_type.value, str)


def test_factory_functions():
    """Test factory functions for creating visualization components."""
    from core.analysis.risk.risk_visualization import (
        create_risk_visualization_engine,
        create_custom_visualization_config
    )

    # Test engine factory
    engine = create_risk_visualization_engine()
    assert isinstance(engine, RiskVisualizationEngine)

    # Test custom config factory
    config = create_custom_visualization_config(
        width=1200,
        height=800,
        color_palette=['red', 'blue', 'green']
    )
    assert isinstance(config, VisualizationConfig)
    assert config.width == 1200
    assert config.height == 800
    assert config.color_palette == ['red', 'blue', 'green']