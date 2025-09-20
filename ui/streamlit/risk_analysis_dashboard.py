"""
Risk Analysis Streamlit Dashboard
==================================

This module provides a comprehensive Streamlit dashboard for risk analysis,
integrating VaR calculations, stress testing, correlation analysis, and
reporting capabilities in an interactive web interface.

Key Features:
- Interactive VaR analysis with multiple methodologies
- Real-time risk metrics visualization
- Correlation and portfolio analysis
- Stress testing scenarios
- Automated report generation
- Data import and export capabilities

Usage:
------
Run this dashboard by including it in the main Streamlit application or
running it standalone:

>>> streamlit run ui/streamlit/risk_analysis_dashboard.py

Components:
-----------
- Data Input/Upload Section
- VaR Analysis Configuration
- Interactive Risk Visualizations
- Stress Testing Interface
- Report Generation and Export
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import io
import logging

# Import risk analysis components
try:
    from core.analysis.risk.var_calculations import VaRCalculator, VaRResult
    from core.analysis.risk.risk_reporting import RiskReporter
    from ui.visualization.risk_visualizer import RiskVisualizer
    from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine
except ImportError as e:
    st.error(f"Failed to import risk analysis components: {e}")
    st.stop()

logger = logging.getLogger(__name__)


def setup_risk_analysis_page():
    """Setup the main risk analysis page layout."""
    st.set_page_config(
        page_title="Risk Analysis Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📊 Risk Analysis Dashboard")
    st.markdown("""
    Comprehensive risk analysis including Value-at-Risk (VaR), stress testing,
    correlation analysis, and portfolio risk assessment.
    """)


def create_sidebar_controls():
    """Create sidebar controls for risk analysis configuration."""
    st.sidebar.header("Risk Analysis Configuration")

    # Analysis type selection
    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["Value-at-Risk (VaR)", "Stress Testing", "Correlation Analysis", "Portfolio Risk"],
        help="Select the type of risk analysis to perform"
    )

    # Confidence levels
    st.sidebar.subheader("Confidence Levels")
    confidence_95 = st.sidebar.checkbox("95% Confidence Level", value=True)
    confidence_99 = st.sidebar.checkbox("99% Confidence Level", value=True)

    # VaR methodologies
    st.sidebar.subheader("VaR Methodologies")
    methods = {
        "Parametric (Normal)": st.sidebar.checkbox("Parametric (Normal)", value=True),
        "Parametric (t-Distribution)": st.sidebar.checkbox("Parametric (t-Distribution)", value=True),
        "Historical Simulation": st.sidebar.checkbox("Historical Simulation", value=True),
        "Monte Carlo": st.sidebar.checkbox("Monte Carlo", value=False),
        "Cornish-Fisher": st.sidebar.checkbox("Cornish-Fisher", value=False)
    }

    selected_methods = [method for method, selected in methods.items() if selected]

    # Additional parameters
    st.sidebar.subheader("Parameters")
    window_size = st.sidebar.slider("Rolling Window Size", 50, 500, 250)
    bootstrap_iterations = st.sidebar.slider("Bootstrap Iterations", 100, 5000, 1000)

    return {
        'analysis_type': analysis_type,
        'confidence_levels': [0.95 if confidence_95 else None, 0.99 if confidence_99 else None],
        'selected_methods': selected_methods,
        'window_size': window_size,
        'bootstrap_iterations': bootstrap_iterations
    }


def create_data_input_section():
    """Create data input section with multiple data source options."""
    st.header("📥 Data Input")

    data_source = st.radio(
        "Select Data Source",
        ["Upload CSV File", "Use Sample Data", "Enter Ticker Symbol", "Manual Entry"],
        horizontal=True
    )

    returns_data = None
    data_info = {}

    if data_source == "Upload CSV File":
        uploaded_file = st.file_uploader(
            "Upload returns data (CSV format)",
            type=['csv'],
            help="Upload a CSV file with date index and return columns"
        )

        if uploaded_file is not None:
            try:
                returns_data = pd.read_csv(uploaded_file, index_col=0, parse_dates=True)
                data_info = {
                    'source': 'Upload',
                    'filename': uploaded_file.name,
                    'shape': returns_data.shape,
                    'date_range': (returns_data.index.min(), returns_data.index.max())
                }
                st.success(f"Loaded data: {returns_data.shape[0]} observations, {returns_data.shape[1]} series")
            except Exception as e:
                st.error(f"Error loading CSV file: {e}")

    elif data_source == "Use Sample Data":
        st.info("Using simulated financial returns data for demonstration")

        # Generate sample data
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        n_assets = st.selectbox("Number of assets", [1, 2, 3, 5], index=0)

        if n_assets == 1:
            returns_data = pd.Series(
                np.random.normal(0.0005, 0.015, len(dates)),
                index=dates,
                name='Portfolio_Returns'
            )
        else:
            # Create correlated returns
            correlation_matrix = np.random.uniform(0.1, 0.7, (n_assets, n_assets))
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1.0)

            # Generate correlated returns using Cholesky decomposition
            L = np.linalg.cholesky(correlation_matrix)
            random_returns = np.random.normal(0, 0.015, (len(dates), n_assets))
            correlated_returns = random_returns @ L.T

            returns_data = pd.DataFrame(
                correlated_returns,
                index=dates,
                columns=[f'Asset_{i+1}' for i in range(n_assets)]
            )

        data_info = {
            'source': 'Sample',
            'type': 'Simulated',
            'shape': returns_data.shape,
            'date_range': (returns_data.index.min(), returns_data.index.max())
        }

    elif data_source == "Enter Ticker Symbol":
        ticker = st.text_input("Enter ticker symbol", "AAPL")
        period = st.selectbox("Data period", ["1y", "2y", "3y", "5y"])

        if st.button("Fetch Data") and ticker:
            try:
                # This would integrate with actual data fetching
                st.info(f"Would fetch {period} of data for {ticker}")
                # Placeholder for actual implementation

            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {e}")

    elif data_source == "Manual Entry":
        st.info("Manual data entry option")
        # Could add manual data entry interface here

    return returns_data, data_info


def display_data_summary(returns_data, data_info):
    """Display summary of loaded data."""
    if returns_data is None:
        return

    st.subheader("📊 Data Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Observations", f"{len(returns_data)}")

    with col2:
        if isinstance(returns_data, pd.DataFrame):
            st.metric("Assets", f"{len(returns_data.columns)}")
        else:
            st.metric("Assets", "1")

    with col3:
        st.metric("Start Date", data_info['date_range'][0].strftime('%Y-%m-%d'))

    with col4:
        st.metric("End Date", data_info['date_range'][1].strftime('%Y-%m-%d'))

    # Basic statistics
    if st.checkbox("Show detailed statistics"):
        st.subheader("Descriptive Statistics")
        if isinstance(returns_data, pd.DataFrame):
            st.dataframe(returns_data.describe())
        else:
            stats_df = pd.DataFrame(returns_data.describe()).T
            st.dataframe(stats_df)

    # Plot time series
    if st.checkbox("Show time series plot"):
        st.subheader("Time Series Plot")

        fig = go.Figure()

        if isinstance(returns_data, pd.DataFrame):
            for column in returns_data.columns:
                fig.add_trace(go.Scatter(
                    x=returns_data.index,
                    y=returns_data[column],
                    mode='lines',
                    name=column,
                    line=dict(width=1)
                ))
        else:
            fig.add_trace(go.Scatter(
                x=returns_data.index,
                y=returns_data.values,
                mode='lines',
                name='Returns',
                line=dict(width=1)
            ))

        fig.update_layout(
            title="Historical Returns",
            xaxis_title="Date",
            yaxis_title="Returns",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)


def perform_var_analysis(returns_data, config):
    """Perform VaR analysis based on configuration."""
    if returns_data is None or len(config['selected_methods']) == 0:
        st.warning("Please select data and VaR methodologies to perform analysis")
        return None, None

    st.header("📈 Value-at-Risk Analysis")

    # Convert to single series if DataFrame
    if isinstance(returns_data, pd.DataFrame):
        if len(returns_data.columns) == 1:
            returns_series = returns_data.iloc[:, 0]
        else:
            # For multiple assets, use equal-weighted portfolio or let user choose
            selected_column = st.selectbox(
                "Select asset for VaR analysis",
                returns_data.columns.tolist() + ["Equal-Weighted Portfolio"]
            )

            if selected_column == "Equal-Weighted Portfolio":
                returns_series = returns_data.mean(axis=1)
            else:
                returns_series = returns_data[selected_column]
    else:
        returns_series = returns_data

    # Initialize VaR calculator
    calculator = VaRCalculator()
    var_results = {}

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Calculate VaR for each selected method
    confidence_levels = [level for level in config['confidence_levels'] if level is not None]

    for i, method in enumerate(config['selected_methods']):
        status_text.text(f"Calculating {method}...")
        progress_bar.progress((i + 1) / len(config['selected_methods']))

        try:
            if method == "Parametric (Normal)":
                result = calculator.calculate_parametric_var(
                    returns_series,
                    confidence_level=0.95,
                    distribution='normal',
                    bootstrap_ci=True
                )
                var_results['Parametric (Normal)'] = result

            elif method == "Parametric (t-Distribution)":
                result = calculator.calculate_parametric_var(
                    returns_series,
                    confidence_level=0.95,
                    distribution='t',
                    bootstrap_ci=True
                )
                var_results['Parametric (t-Distribution)'] = result

            elif method == "Historical Simulation":
                result = calculator.calculate_historical_var(
                    returns_series,
                    confidence_level=0.95,
                    bootstrap_ci=True
                )
                var_results['Historical Simulation'] = result

            elif method == "Monte Carlo":
                result = calculator.calculate_monte_carlo_var(
                    returns_series,
                    confidence_level=0.95,
                    n_simulations=config['bootstrap_iterations']
                )
                var_results['Monte Carlo'] = result

            elif method == "Cornish-Fisher":
                result = calculator.calculate_cornish_fisher_var(
                    returns_series,
                    confidence_level=0.95
                )
                var_results['Cornish-Fisher'] = result

        except Exception as e:
            st.error(f"Error calculating {method}: {e}")

    status_text.text("VaR analysis completed!")
    progress_bar.progress(1.0)

    return var_results, returns_series


def display_var_results(var_results, returns_series):
    """Display VaR analysis results."""
    if not var_results:
        return

    st.subheader("🎯 VaR Results Summary")

    # Create summary table
    summary_data = []
    for method, result in var_results.items():
        summary_data.append({
            'Method': method,
            '95% VaR': f"{result.var_95:.4f}" if result.var_95 else "N/A",
            '99% VaR': f"{result.var_99:.4f}" if result.var_99 else "N/A",
            '95% CVaR': f"{getattr(result, 'cvar_95', 'N/A')}",
            'Distribution': result.distribution if hasattr(result, 'distribution') else "N/A"
        })

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    # Initialize visualizer
    visualizer = RiskVisualizer()

    # VaR comparison chart
    st.subheader("📊 VaR Methodology Comparison")
    comparison_fig = visualizer.create_var_comparison_chart(var_results)
    st.plotly_chart(comparison_fig, use_container_width=True)

    # Individual VaR analysis
    st.subheader("🔍 Detailed VaR Analysis")

    selected_method = st.selectbox(
        "Select method for detailed analysis",
        list(var_results.keys())
    )

    if selected_method:
        result = var_results[selected_method]

        # Distribution plot
        dist_fig = visualizer.create_var_distribution_plot(result, returns_series)
        st.plotly_chart(dist_fig, use_container_width=True)

        # Detailed metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("95% VaR", f"{result.var_95:.4f}" if result.var_95 else "N/A")

        with col2:
            st.metric("99% VaR", f"{result.var_99:.4f}" if result.var_99 else "N/A")

        with col3:
            if hasattr(result, 'cvar_95') and result.cvar_95:
                st.metric("95% CVaR", f"{result.cvar_95:.4f}")

        # Confidence intervals if available
        if hasattr(result, 'confidence_intervals') and result.confidence_intervals:
            st.subheader("Confidence Intervals")
            ci_data = []
            for level, (lower, upper) in result.confidence_intervals.items():
                ci_data.append({
                    'Confidence Level': f"{level:.1%}",
                    'Lower Bound': f"{lower:.4f}" if lower else "N/A",
                    'Upper Bound': f"{upper:.4f}" if upper else "N/A"
                })

            ci_df = pd.DataFrame(ci_data)
            st.dataframe(ci_df)


def create_risk_dashboard(var_results, returns_series):
    """Create comprehensive risk dashboard."""
    if not var_results:
        return

    st.header("🎛️ Risk Dashboard")

    visualizer = RiskVisualizer()

    # Main dashboard
    dashboard_fig = visualizer.create_risk_dashboard(var_results, returns_series)
    st.plotly_chart(dashboard_fig, use_container_width=True)

    # Risk metrics summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        volatility = returns_series.std() * np.sqrt(252)
        st.metric("Annualized Volatility", f"{volatility:.2%}")

    with col2:
        mean_return = returns_series.mean() * 252
        st.metric("Expected Annual Return", f"{mean_return:.2%}")

    with col3:
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

    with col4:
        max_dd = ((1 + returns_series).cumprod() / (1 + returns_series).cumprod().expanding().max() - 1).min()
        st.metric("Max Drawdown", f"{max_dd:.2%}")


def create_stress_testing_section():
    """Create stress testing interface."""
    st.header("⚠️ Stress Testing")

    st.info("Stress testing functionality would be implemented here")

    # Placeholder for stress testing interface
    scenarios = ["2008 Financial Crisis", "COVID-19 Pandemic", "Interest Rate Shock", "Custom Scenario"]

    selected_scenario = st.selectbox("Select Stress Scenario", scenarios)

    if selected_scenario == "Custom Scenario":
        col1, col2 = st.columns(2)

        with col1:
            market_shock = st.slider("Market Shock (%)", -50, 0, -20)

        with col2:
            volatility_multiplier = st.slider("Volatility Multiplier", 1.0, 5.0, 2.0)

    if st.button("Run Stress Test"):
        st.info(f"Running stress test for: {selected_scenario}")
        # Placeholder for actual stress testing implementation


def create_report_generation_section(var_results, returns_series):
    """Create report generation and export section."""
    if not var_results:
        return

    st.header("📋 Report Generation")

    # Report options
    col1, col2 = st.columns(2)

    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Executive Summary", "Detailed Analysis", "Full Report"]
        )

    with col2:
        export_format = st.selectbox(
            "Export Format",
            ["PDF", "Excel", "HTML", "JSON"]
        )

    # Report generation
    if st.button("Generate Report"):
        try:
            reporter = RiskReporter()

            if report_type == "Executive Summary":
                summary = reporter.generate_executive_summary_only(var_results, returns_series)
                st.subheader("Executive Summary")
                st.text_area("Summary", summary, height=300)

            elif report_type == "Detailed Analysis":
                dashboard_data = reporter.create_risk_dashboard_report(var_results, returns_series)
                st.subheader("Dashboard Data")
                st.json(dashboard_data['summary_metrics'])

            elif report_type == "Full Report":
                report = reporter.generate_comprehensive_report(var_results, returns_series)

                st.subheader("Report Metadata")
                st.json(report.metadata.to_dict())

                st.subheader("Executive Summary")
                st.text_area("Summary", report.executive_summary, height=200)

                st.subheader("Recommendations")
                for i, rec in enumerate(report.recommendations, 1):
                    st.write(f"{i}. {rec}")

            st.success(f"Report generated successfully in {export_format} format!")

        except Exception as e:
            st.error(f"Error generating report: {e}")


def render_risk_analysis_tab(financial_calculator=None):
    """
    Render risk analysis dashboard content within a tab of the main application.

    Args:
        financial_calculator: FinancialCalculator instance for integration
    """
    st.markdown("""
    ## 📊 Risk Analysis & Monte Carlo Simulation

    Comprehensive risk analysis including Value-at-Risk (VaR), Monte Carlo simulations,
    stress testing, and scenario analysis for your financial valuations.
    """)

    # Quick access buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        monte_carlo_btn = st.button("🎲 Monte Carlo DCF", help="Run Monte Carlo simulation on DCF valuation")
    with col2:
        var_analysis_btn = st.button("📉 VaR Analysis", help="Calculate Value at Risk metrics")
    with col3:
        stress_test_btn = st.button("⚠️ Stress Testing", help="Run stress testing scenarios")
    with col4:
        scenario_btn = st.button("📋 Scenario Analysis", help="Compare different scenarios")

    # Risk analysis configuration
    st.subheader("Risk Analysis Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        confidence_level = st.selectbox(
            "Confidence Level",
            [90, 95, 99],
            index=1,
            help="Confidence level for VaR calculations"
        )

    with col2:
        num_simulations = st.selectbox(
            "Number of Simulations",
            [1000, 5000, 10000, 50000],
            index=2,
            help="Number of Monte Carlo simulations to run"
        )

    with col3:
        volatility_level = st.selectbox(
            "Volatility Scenario",
            ["Low", "Medium", "High"],
            index=1,
            help="Expected volatility level for parameters"
        )

    # Monte Carlo Analysis Section
    if monte_carlo_btn or st.session_state.get('show_monte_carlo', False):
        st.session_state.show_monte_carlo = True

        st.subheader("🎲 Monte Carlo DCF Analysis")

        if financial_calculator is not None:
            try:
                from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine, quick_dcf_simulation

                # Run Monte Carlo simulation
                with st.spinner("Running Monte Carlo simulation..."):
                    volatility_map = {"Low": "low", "Medium": "medium", "High": "high"}
                    result = quick_dcf_simulation(
                        financial_calculator,
                        num_simulations=num_simulations,
                        volatility_level=volatility_map[volatility_level]
                    )

                # Display results
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Mean Value", f"${result.mean_value:.2f}")
                with col2:
                    st.metric("Std Deviation", f"${result.statistics['std']:.2f}")
                with col3:
                    st.metric("VaR (5%)", f"${result.var_5:.2f}")
                with col4:
                    st.metric("95th Percentile", f"${result.percentiles['p95']:.2f}")

                # Create visualization
                import plotly.graph_objects as go
                import plotly.express as px

                # Histogram of simulation results
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=result.values,
                    nbinsx=50,
                    name="Simulation Results",
                    opacity=0.7
                ))

                # Add percentile lines
                fig.add_vline(
                    x=result.percentiles['p5'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="5th Percentile (VaR)"
                )
                fig.add_vline(
                    x=result.percentiles['p95'],
                    line_dash="dash",
                    line_color="green",
                    annotation_text="95th Percentile"
                )
                fig.add_vline(
                    x=result.mean_value,
                    line_dash="solid",
                    line_color="blue",
                    annotation_text="Mean Value"
                )

                fig.update_layout(
                    title=f"Monte Carlo DCF Simulation Results ({num_simulations:,} simulations)",
                    xaxis_title="Value per Share ($)",
                    yaxis_title="Frequency",
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

                # Summary statistics table
                st.subheader("Summary Statistics")
                summary_df = result.summary_table()
                st.dataframe(summary_df, use_container_width=True)

            except Exception as e:
                st.error(f"Monte Carlo simulation failed: {e}")
                st.info("Ensure you have run FCF analysis first to initialize the financial calculator.")
        else:
            st.warning("⚠️ Financial calculator not available. Please run FCF analysis first.")

    # Scenario Analysis Section
    if scenario_btn or st.session_state.get('show_scenarios', False):
        st.session_state.show_scenarios = True

        st.subheader("📋 Scenario Analysis")

        if financial_calculator is not None:
            try:
                from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine, create_standard_scenarios

                # Create Monte Carlo engine
                monte_carlo = MonteCarloEngine(financial_calculator)

                # Get standard scenarios
                scenarios = create_standard_scenarios()

                # Run scenario analysis
                with st.spinner("Running scenario analysis..."):
                    scenario_results = monte_carlo.run_scenario_analysis(scenarios, 'dcf')

                # Display results
                scenario_df = pd.DataFrame([
                    {
                        'Scenario': name,
                        'Value per Share': f"${value:.2f}" if value else "Failed",
                        'Revenue Growth': f"{params['revenue_growth']:.1%}",
                        'Discount Rate': f"{params['discount_rate']:.1%}",
                        'Terminal Growth': f"{params['terminal_growth']:.1%}",
                        'Operating Margin': f"{params['operating_margin']:.1%}"
                    }
                    for name, (value, params) in [(name, (scenario_results[name], scenarios[name])) for name in scenarios.keys()]
                ])

                st.dataframe(scenario_df, use_container_width=True)

                # Visualization
                valid_results = {k: v for k, v in scenario_results.items() if v is not None}
                if valid_results:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=list(valid_results.keys()),
                        y=list(valid_results.values()),
                        text=[f"${v:.2f}" for v in valid_results.values()],
                        textposition='auto'
                    ))

                    fig.update_layout(
                        title="Scenario Analysis Results",
                        xaxis_title="Scenario",
                        yaxis_title="Value per Share ($)"
                    )

                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Scenario analysis failed: {e}")
        else:
            st.warning("⚠️ Financial calculator not available. Please run FCF analysis first.")

    # Full risk dashboard (embedded)
    if var_analysis_btn or stress_test_btn:
        st.subheader("🔬 Advanced Risk Analysis")
        st.info("💡 For comprehensive risk analysis including VaR calculations and stress testing, please use the dedicated risk analysis tools above or run the full risk analysis module.")

        # Embed main risk dashboard functionality
        try:
            # Sidebar controls (in main content area for tab)
            st.markdown("### Configuration")

            analysis_type = st.selectbox(
                "Analysis Type",
                ["Value-at-Risk (VaR)", "Stress Testing", "Correlation Analysis"],
                help="Select the type of risk analysis to perform"
            )

            # Basic VaR section
            if analysis_type == "Value-at-Risk (VaR)":
                st.markdown("#### VaR Analysis")
                st.info("Upload historical returns data or connect to your financial data to perform VaR analysis.")

                # File upload for returns data
                uploaded_file = st.file_uploader(
                    "Upload Returns Data (CSV)",
                    type=['csv'],
                    help="Upload a CSV file with historical returns data"
                )

                if uploaded_file is not None:
                    try:
                        returns_data = pd.read_csv(uploaded_file)
                        st.success("✅ Data uploaded successfully!")
                        st.dataframe(returns_data.head(), use_container_width=True)

                        if st.button("Calculate VaR"):
                            st.info("VaR calculation functionality ready - connect to risk analysis engine")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

        except Exception as e:
            st.error(f"Risk analysis setup failed: {e}")


def main():
    """Main function to run the risk analysis dashboard."""
    setup_risk_analysis_page()

    # Sidebar controls
    config = create_sidebar_controls()

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Data & VaR", "📊 Dashboard", "⚠️ Stress Testing", "📋 Reports"])

    with tab1:
        # Data input
        returns_data, data_info = create_data_input_section()

        if returns_data is not None:
            display_data_summary(returns_data, data_info)

            # VaR analysis
            if st.button("🚀 Run VaR Analysis", type="primary"):
                var_results, returns_series = perform_var_analysis(returns_data, config)

                if var_results:
                    # Store results in session state
                    st.session_state['var_results'] = var_results
                    st.session_state['returns_series'] = returns_series

                    display_var_results(var_results, returns_series)

    with tab2:
        if 'var_results' in st.session_state:
            create_risk_dashboard(st.session_state['var_results'], st.session_state['returns_series'])
        else:
            st.info("Please run VaR analysis first to view the dashboard")

    with tab3:
        create_stress_testing_section()

    with tab4:
        if 'var_results' in st.session_state:
            create_report_generation_section(st.session_state['var_results'], st.session_state['returns_series'])
        else:
            st.info("Please run VaR analysis first to generate reports")

    # Footer
    st.markdown("---")
    st.markdown("*Risk Analysis Dashboard - Built with Streamlit*")


if __name__ == "__main__":
    main()