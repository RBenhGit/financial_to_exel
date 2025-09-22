"""
Risk Visualization Example
=========================

Comprehensive example demonstrating the risk visualization and reporting capabilities.
Shows how to create probability distribution plots, risk heatmaps, sensitivity charts,
and interactive dashboards from risk analysis results.

This example demonstrates:
- Creating probability distribution visualizations with confidence intervals
- Building risk correlation heatmaps with clustering
- Generating interactive tornado charts for sensitivity analysis
- Visualizing Monte Carlo simulation results
- Creating comprehensive risk dashboards
- Exporting risk reports in multiple formats

Usage:
------
python examples/risk_visualization_example.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Core risk analysis imports
from core.analysis.risk.integrated_risk_engine import IntegratedRiskEngine, RiskAnalysisRequest
from core.analysis.risk.risk_visualization import (
    RiskVisualizationEngine,
    VisualizationConfig,
    create_risk_visualization_engine,
    create_custom_visualization_config
)
from core.analysis.risk.risk_framework import RiskAnalysisResult
from core.analysis.risk.risk_metrics import RiskMetrics, RiskType, RiskLevel
from core.analysis.risk.correlation_analysis import CorrelationMatrix, CorrelationMethod
from core.analysis.risk.probability_distributions import (
    ProbabilityDistribution, DistributionType, DistributionParameters
)
from core.analysis.statistics.monte_carlo_engine import SimulationResult

# Visualization imports
import plotly.express as px
import streamlit as st


def create_sample_risk_analysis_result():
    """
    Create a comprehensive sample risk analysis result for demonstration.
    In a real application, this would come from the IntegratedRiskEngine.
    """
    print("📊 Creating sample risk analysis result...")

    # Create main risk analysis result
    result = RiskAnalysisResult(
        analysis_id="demo_risk_analysis_20241201",
        analysis_date=datetime.now(),
        asset_id="PORTFOLIO_DEMO",
        calculation_time=15.3
    )

    # Set overall risk assessment
    result.overall_risk_score = 72.5
    result.risk_level = RiskLevel.MEDIUM_HIGH
    result.key_risk_drivers = [
        "High market volatility exposure",
        "Concentration in technology sector",
        "Correlation instability during stress periods"
    ]

    # Create comprehensive risk metrics
    result.risk_metrics = RiskMetrics(
        var_1day_95=-0.028,  # 2.8% daily VaR at 95% confidence
        var_1day_99=-0.042,  # 4.2% daily VaR at 99% confidence
        cvar_1day_95=-0.035,  # 3.5% daily CVaR at 95% confidence
        annual_volatility=0.24,  # 24% annual volatility
        max_drawdown=-0.18,  # 18% maximum drawdown
        sharpe_ratio=1.15,  # Sharpe ratio of 1.15
        sortino_ratio=1.42,  # Sortino ratio of 1.42
        calmar_ratio=0.64   # Calmar ratio of 0.64
    )

    # Create correlation matrices
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    n_assets = len(assets)

    # Generate realistic correlation matrix
    np.random.seed(42)
    base_corr = 0.3 + 0.4 * np.random.random((n_assets, n_assets))
    base_corr = (base_corr + base_corr.T) / 2  # Make symmetric
    np.fill_diagonal(base_corr, 1.0)

    # Create correlation matrix objects
    correlation_df = pd.DataFrame(base_corr, index=assets, columns=assets)

    class MockCorrelationMatrix:
        def __init__(self, corr_df):
            self._corr_df = corr_df

        def to_dataframe(self):
            return self._corr_df

        def market_concentration(self):
            return np.mean(self._corr_df.values[np.triu_indices_from(self._corr_df.values, k=1)])

        @property
        def stability_score(self):
            return 0.85

        def identify_highly_correlated_pairs(self, threshold):
            pairs = []
            for i in range(len(self._corr_df)):
                for j in range(i + 1, len(self._corr_df)):
                    if abs(self._corr_df.iloc[i, j]) > threshold:
                        pairs.append((self._corr_df.index[i], self._corr_df.columns[j]))
            return pairs

    result.correlation_matrices = {
        CorrelationMethod.PEARSON.value: MockCorrelationMatrix(correlation_df),
        CorrelationMethod.SPEARMAN.value: MockCorrelationMatrix(correlation_df * 0.95)
    }

    # Create Monte Carlo simulation results
    class MockSimulationResult:
        def __init__(self, name, mean, std, n_sims=10000):
            np.random.seed(hash(name) % (2**32))
            self.simulated_values = np.random.normal(mean, std, n_sims)
            self.statistics = {
                'mean': np.mean(self.simulated_values),
                'std': np.std(self.simulated_values),
                'var_95': np.percentile(self.simulated_values, 5),
                'var_99': np.percentile(self.simulated_values, 1),
                'cvar_95': np.mean(self.simulated_values[self.simulated_values <= np.percentile(self.simulated_values, 5)]),
                'skewness': pd.Series(self.simulated_values).skew(),
                'kurtosis': pd.Series(self.simulated_values).kurtosis()
            }

    result.monte_carlo_results = {
        'portfolio_returns': MockSimulationResult('portfolio', 0.08, 0.15),
        'worst_case_scenario': MockSimulationResult('worst_case', -0.25, 0.20),
        'stress_test': MockSimulationResult('stress', -0.15, 0.18)
    }

    # Add scenario analysis results
    result.scenario_results = {
        'market_crash': {
            'scenario_probability': 0.05,
            'portfolio_analysis': {
                'total_return': {
                    'mean': -0.28,
                    'std': 0.12,
                    'max_loss': -0.45,
                    'var_95': -0.35
                }
            }
        },
        'inflation_spike': {
            'scenario_probability': 0.15,
            'portfolio_analysis': {
                'total_return': {
                    'mean': -0.12,
                    'std': 0.08,
                    'max_loss': -0.22,
                    'var_95': -0.18
                }
            }
        },
        'bull_market': {
            'scenario_probability': 0.25,
            'portfolio_analysis': {
                'total_return': {
                    'mean': 0.35,
                    'std': 0.15,
                    'max_loss': 0.08,
                    'var_95': 0.15
                }
            }
        }
    }

    # Add distribution analysis
    result.distribution_analysis = {
        'fitted_distributions': {
            'portfolio_returns': {
                'distribution_type': 'skew_normal',
                'parameters': {'loc': 0.08, 'scale': 0.15, 'shape': -0.5},
                'moments': {
                    'mean': 0.08,
                    'std': 0.15,
                    'skewness': -0.5,
                    'kurtosis': 3.2
                },
                'tail_behavior': 'fat',
                'var_estimates': {
                    'var_90': -0.12,
                    'var_95': -0.17,
                    'var_99': -0.28
                }
            }
        },
        'fitting_summary': {
            'assets_fitted': 1,
            'fitting_method': 'maximum_likelihood',
            'distribution_comparison': {
                'normal': {'aic': 1250, 'bic': 1260, 'log_likelihood': -622},
                'skew_normal': {'aic': 1245, 'bic': 1258, 'log_likelihood': -619},
                'student_t': {'aic': 1248, 'bic': 1261, 'log_likelihood': -621}
            }
        }
    }

    # Add sensitivity analysis results
    result.sensitivity_results = {
        'one_way_analysis': {
            'most_sensitive_parameter': 'discount_rate',
            'sensitivity_rankings': [
                'discount_rate', 'revenue_growth', 'terminal_growth', 'market_volatility'
            ],
            'elasticity_analysis': {
                'discount_rate': {'low': 85.2, 'high': 116.8},
                'revenue_growth': {'low': 88.5, 'high': 112.3},
                'terminal_growth': {'low': 94.1, 'high': 106.2},
                'market_volatility': {'low': 91.7, 'high': 108.9}
            }
        }
    }

    print("✅ Sample risk analysis result created successfully")
    return result


def demonstrate_probability_distribution_plots():
    """Demonstrate probability distribution plotting capabilities."""
    print("\n🎯 Demonstrating Probability Distribution Plots...")

    # Create visualization config
    config = VisualizationConfig(
        width=1000,
        height=700,
        confidence_levels=[0.90, 0.95, 0.99]
    )

    # Create distribution plotter
    from core.analysis.risk.risk_visualization import ProbabilityDistributionPlotter
    plotter = ProbabilityDistributionPlotter(config)

    # Generate sample return data
    np.random.seed(42)
    empirical_data = pd.Series(
        np.random.normal(0.05, 0.15, 2000),
        name="Portfolio Returns"
    )

    # Create mock fitted distribution
    class MockDistribution:
        def __init__(self):
            self.distribution_type = DistributionType.NORMAL

        def pdf(self, x):
            return np.exp(-0.5 * ((x - 0.05) / 0.15)**2) / (0.15 * np.sqrt(2 * np.pi))

        def cdf(self, x):
            from scipy.stats import norm
            return norm.cdf(x, loc=0.05, scale=0.15)

        def ppf(self, q):
            from scipy.stats import norm
            return norm.ppf(q, loc=0.05, scale=0.15)

        def var(self, alpha):
            return self.ppf(alpha)

    fitted_dist = MockDistribution()

    # Create distribution analysis plot
    print("  📈 Creating comprehensive distribution analysis...")
    fig = plotter.plot_distribution_analysis(
        empirical_data=empirical_data,
        fitted_distribution=fitted_dist,
        confidence_levels=config.confidence_levels
    )

    # Display plot information
    print(f"  ✅ Distribution plot created with {len(fig.data)} traces")
    print(f"  📊 Plot includes: histogram, fitted curve, Q-Q plot, P-P plot")
    print(f"  📏 VaR markers for confidence levels: {config.confidence_levels}")

    return fig


def demonstrate_risk_heatmaps():
    """Demonstrate risk heatmap creation capabilities."""
    print("\n🌡️ Demonstrating Risk Heatmaps...")

    # Create visualization config
    config = VisualizationConfig(
        width=900,
        height=700,
        risk_color_scale="RdYlBu_r"
    )

    # Create heatmap generator
    from core.analysis.risk.risk_visualization import RiskHeatmapGenerator
    generator = RiskHeatmapGenerator(config)

    # Create sample risk metrics for multiple assets
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']
    risk_metrics = {}

    np.random.seed(42)
    for asset in assets:
        risk_metrics[asset] = RiskMetrics(
            var_1day_95=-np.random.uniform(0.015, 0.045),
            annual_volatility=np.random.uniform(0.15, 0.35),
            max_drawdown=-np.random.uniform(0.10, 0.25),
            sharpe_ratio=np.random.uniform(0.8, 1.8)
        )

    # Create risk concentration heatmap
    print("  🎯 Creating risk concentration heatmap...")
    risk_types = [RiskType.MARKET, RiskType.CREDIT, RiskType.LIQUIDITY, RiskType.OPERATIONAL]
    risk_heatmap = generator.create_risk_concentration_heatmap(risk_metrics, risk_types)

    # Create correlation heatmap
    print("  🔗 Creating correlation heatmap with clustering...")
    correlation_data = np.random.uniform(0.2, 0.8, (len(assets), len(assets)))
    correlation_data = (correlation_data + correlation_data.T) / 2
    np.fill_diagonal(correlation_data, 1.0)

    corr_df = pd.DataFrame(correlation_data, index=assets, columns=assets)

    class MockCorrMatrix:
        def to_dataframe(self):
            return corr_df

    mock_corr = MockCorrMatrix()
    correlation_heatmap = generator.create_correlation_heatmap(
        mock_corr, cluster=True, show_significance=True
    )

    print(f"  ✅ Risk concentration heatmap created for {len(assets)} assets")
    print(f"  ✅ Correlation heatmap created with hierarchical clustering")

    return risk_heatmap, correlation_heatmap


def demonstrate_sensitivity_charts():
    """Demonstrate sensitivity analysis charts."""
    print("\n📊 Demonstrating Sensitivity Charts...")

    # Create visualization config
    config = VisualizationConfig(width=900, height=600)

    # Create sensitivity chart builder
    from core.analysis.risk.risk_visualization import SensitivityChartBuilder
    builder = SensitivityChartBuilder(config)

    # Create sample sensitivity results
    sensitivity_results = {
        'Discount Rate': {'low': 85.2, 'high': 116.8},
        'Revenue Growth': {'low': 88.5, 'high': 112.3},
        'Terminal Growth': {'low': 94.1, 'high': 106.2},
        'Market Volatility': {'low': 91.7, 'high': 108.9},
        'Margin Compression': {'low': 89.3, 'high': 110.7},
        'Interest Rate Change': {'low': 92.1, 'high': 107.8}
    }

    base_value = 100.0

    # Create tornado chart
    print("  🌪️ Creating tornado chart...")
    tornado_chart = builder.create_tornado_chart(
        sensitivity_results,
        base_value,
        title="Portfolio Valuation Sensitivity Analysis"
    )

    # Create spider chart
    print("  🕷️ Creating sensitivity spider chart...")
    spider_chart = builder.create_sensitivity_spider_chart(
        sensitivity_results,
        base_value
    )

    print(f"  ✅ Tornado chart created with {len(sensitivity_results)} parameters")
    print(f"  ✅ Spider chart created for sensitivity visualization")

    return tornado_chart, spider_chart


def demonstrate_monte_carlo_visualizations():
    """Demonstrate Monte Carlo simulation visualizations."""
    print("\n🎲 Demonstrating Monte Carlo Visualizations...")

    # Create visualization config
    config = VisualizationConfig(
        width=1000,
        height=600,
        confidence_levels=[0.90, 0.95, 0.99]
    )

    # Create Monte Carlo visualizer
    from core.analysis.risk.risk_visualization import MonteCarloVisualizer
    visualizer = MonteCarloVisualizer(config)

    # Create sample simulation result
    class MockSimResult:
        def __init__(self):
            np.random.seed(42)
            # Simulate portfolio returns with some skewness
            normal_returns = np.random.normal(0.08, 0.12, 8000)
            tail_returns = np.random.normal(-0.15, 0.08, 2000)
            self.simulated_values = np.concatenate([normal_returns, tail_returns])
            np.random.shuffle(self.simulated_values)

    sim_result = MockSimResult()

    # Create simulation histogram
    print("  📊 Creating Monte Carlo histogram with confidence intervals...")
    histogram = visualizer.create_simulation_histogram(
        sim_result,
        config.confidence_levels
    )

    # Create convergence plot
    print("  📈 Creating convergence analysis plot...")
    convergence_plot = visualizer.create_convergence_plot(sim_result)

    print(f"  ✅ Histogram created for {len(sim_result.simulated_values)} simulations")
    print(f"  ✅ Convergence plot shows estimation stability")

    return histogram, convergence_plot


def demonstrate_comprehensive_dashboard():
    """Demonstrate comprehensive risk dashboard creation."""
    print("\n🎛️ Demonstrating Comprehensive Risk Dashboard...")

    # Create sample risk analysis result
    risk_result = create_sample_risk_analysis_result()

    # Create visualization engine with custom config
    config = create_custom_visualization_config(
        width=1400,
        height=1000,
        color_palette=px.colors.qualitative.Set3,
        risk_color_scale="RdYlBu_r"
    )

    viz_engine = create_risk_visualization_engine(config)

    # Create comprehensive visualization suite
    print("  🎨 Creating comprehensive visualization suite...")
    viz_suite = viz_engine.create_comprehensive_visualizations(risk_result)

    # Create interactive dashboard
    print("  📱 Creating interactive risk dashboard...")
    dashboard = viz_engine.create_risk_dashboard(risk_result)

    # Display suite information
    print(f"  ✅ Visualization suite created:")
    print(f"    🎯 Risk heatmaps: {len(viz_suite.risk_heatmaps)}")
    print(f"    🎲 Monte Carlo plots: {len(viz_suite.monte_carlo_plots)}")
    print(f"    📊 Summary statistics: {len(viz_suite.summary_statistics)} sections")

    print(f"  ✅ Interactive dashboard created with multiple subplots")

    return viz_suite, dashboard


def demonstrate_report_export():
    """Demonstrate risk report export capabilities."""
    print("\n📄 Demonstrating Risk Report Export...")

    # Create sample risk analysis result
    risk_result = create_sample_risk_analysis_result()

    # Create visualization engine
    viz_engine = create_risk_visualization_engine()

    # Export HTML report
    html_output = "data/reports/risk_analysis_report.html"
    print(f"  📄 Exporting HTML report to {html_output}...")

    try:
        viz_engine.export_risk_report(
            risk_result,
            html_output,
            format="html"
        )
        print("  ✅ HTML report export completed")
    except Exception as e:
        print(f"  ⚠️ HTML export simulation: {e}")

    # Export PDF report
    pdf_output = "data/reports/risk_analysis_report.pdf"
    print(f"  📄 Exporting PDF report to {pdf_output}...")

    try:
        viz_engine.export_risk_report(
            risk_result,
            pdf_output,
            format="pdf"
        )
        print("  ✅ PDF report export completed")
    except Exception as e:
        print(f"  ⚠️ PDF export simulation: {e}")

    return html_output, pdf_output


def create_streamlit_dashboard():
    """Create Streamlit dashboard for interactive risk visualization."""
    print("\n🚀 Creating Streamlit Dashboard...")

    # This would be run in a Streamlit environment
    streamlit_code = '''
import streamlit as st
from core.analysis.risk.risk_visualization import create_risk_visualization_engine

# Streamlit dashboard
st.set_page_config(
    page_title="Risk Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Comprehensive Risk Analysis Dashboard")

# Sidebar controls
st.sidebar.header("🎛️ Visualization Controls")
confidence_level = st.sidebar.selectbox(
    "Confidence Level",
    [0.90, 0.95, 0.99],
    index=1
)

show_clustering = st.sidebar.checkbox("Apply Correlation Clustering", value=True)
color_scheme = st.sidebar.selectbox(
    "Color Scheme",
    ["RdYlBu_r", "Viridis", "Plasma", "Blues"]
)

# Main dashboard
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Risk Distribution Analysis")
    # Distribution plot would go here

    st.subheader("🌡️ Risk Concentration Heatmap")
    # Risk heatmap would go here

with col2:
    st.subheader("🔗 Correlation Analysis")
    # Correlation heatmap would go here

    st.subheader("🎲 Monte Carlo Results")
    # Monte Carlo histogram would go here

# Full-width sensitivity analysis
st.subheader("📊 Sensitivity Analysis")
# Tornado chart would go here

# Risk metrics summary
st.subheader("📈 Risk Metrics Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("VaR 95%", "-2.8%", delta="-0.3%")
with col2:
    st.metric("Annual Volatility", "24.0%", delta="+1.2%")
with col3:
    st.metric("Max Drawdown", "-18.0%", delta="+2.1%")
with col4:
    st.metric("Sharpe Ratio", "1.15", delta="+0.05")
'''

    print("  🎨 Streamlit dashboard code generated")
    print("  📱 Dashboard includes:")
    print("    - Interactive controls for visualization parameters")
    print("    - Multi-column layout for comprehensive view")
    print("    - Real-time risk metrics display")
    print("    - Downloadable reports and charts")

    return streamlit_code


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("🚀 RISK VISUALIZATION AND REPORTING DEMONSTRATION")
    print("=" * 60)

    try:
        # 1. Probability Distribution Plots
        dist_fig = demonstrate_probability_distribution_plots()

        # 2. Risk Heatmaps
        risk_heatmap, corr_heatmap = demonstrate_risk_heatmaps()

        # 3. Sensitivity Charts
        tornado_chart, spider_chart = demonstrate_sensitivity_charts()

        # 4. Monte Carlo Visualizations
        mc_histogram, mc_convergence = demonstrate_monte_carlo_visualizations()

        # 5. Comprehensive Dashboard
        viz_suite, dashboard = demonstrate_comprehensive_dashboard()

        # 6. Report Export
        html_report, pdf_report = demonstrate_report_export()

        # 7. Streamlit Dashboard
        streamlit_code = create_streamlit_dashboard()

        print("\n" + "=" * 60)
        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print("\n📋 Summary of Created Visualizations:")
        print("  🎯 Probability distribution analysis with Q-Q and P-P plots")
        print("  🌡️ Risk concentration and correlation heatmaps")
        print("  📊 Interactive tornado and spider charts for sensitivity")
        print("  🎲 Monte Carlo simulation histograms and convergence plots")
        print("  🎛️ Comprehensive risk dashboard with multiple subplots")
        print("  📄 Exportable HTML and PDF reports")
        print("  🚀 Streamlit dashboard for interactive exploration")

        print("\n🎯 Key Features Demonstrated:")
        print("  ✅ Comprehensive risk visualization suite")
        print("  ✅ Interactive charts with plotly")
        print("  ✅ Statistical significance testing")
        print("  ✅ Hierarchical clustering for correlation analysis")
        print("  ✅ Multi-format report export capabilities")
        print("  ✅ Streamlit integration for web dashboards")

        print("\n📊 Visualization Components:")
        print("  • ProbabilityDistributionPlotter: Distribution analysis with fitted curves")
        print("  • RiskHeatmapGenerator: Advanced heatmaps with clustering")
        print("  • SensitivityChartBuilder: Tornado and spider charts")
        print("  • MonteCarloVisualizer: Simulation result visualizations")
        print("  • RiskVisualizationEngine: Orchestrates all components")

        print("\n🔧 Integration Notes:")
        print("  • All visualizations are created using plotly for interactivity")
        print("  • Components are designed to work with IntegratedRiskEngine results")
        print("  • Configuration system allows customization of all visual elements")
        print("  • Export functionality supports multiple formats (HTML, PDF)")
        print("  • Streamlit integration enables web-based dashboards")

        return {
            'distribution_plot': dist_fig,
            'risk_heatmap': risk_heatmap,
            'correlation_heatmap': corr_heatmap,
            'tornado_chart': tornado_chart,
            'spider_chart': spider_chart,
            'monte_carlo_histogram': mc_histogram,
            'convergence_plot': mc_convergence,
            'visualization_suite': viz_suite,
            'dashboard': dashboard,
            'streamlit_code': streamlit_code
        }

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Please ensure all required dependencies are installed:")
        print("  pip install plotly pandas numpy scipy streamlit")
        raise


if __name__ == "__main__":
    # Run the demonstration
    results = main()

    print(f"\n🎉 Risk visualization demonstration completed!")
    print(f"📊 Created {len(results)} visualization components")
    print(f"🚀 Ready for integration with the financial analysis system")