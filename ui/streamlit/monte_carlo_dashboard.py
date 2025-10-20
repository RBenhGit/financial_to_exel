"""
Monte Carlo Analysis Dashboard for Streamlit
===========================================

This module provides a comprehensive Streamlit interface for Monte Carlo simulation
analysis in financial valuation. It integrates with the existing FCF analysis framework
to provide probabilistic valuation analysis with interactive visualizations.

Key Features
------------
- **Interactive Monte Carlo DCF Analysis**: User-configurable simulation parameters
- **Real-time Parameter Adjustment**: Sliders and inputs for volatility settings
- **Risk Assessment Dashboard**: VaR, CVaR, and probability analysis
- **Scenario Comparison**: Side-by-side scenario analysis
- **Export Capabilities**: Download results and visualizations
- **Performance Optimization**: Efficient calculations with caching

Functions
---------
render_monte_carlo_dashboard()
    Main dashboard rendering function

render_monte_carlo_settings_sidebar()
    Settings panel for simulation configuration

render_scenario_analysis_tab()
    Scenario comparison interface

Usage Integration
-----------------
Add to main Streamlit app:

>>> from ui.streamlit.monte_carlo_dashboard import render_monte_carlo_dashboard
>>>
>>> # In main app
>>> if selected_tab == "Monte Carlo Analysis":
>>>     render_monte_carlo_dashboard(financial_calculator)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import asdict
import io
import json
from datetime import datetime

# Import VarInputData for centralized data access
from core.data_processing.var_input_data import get_var_input_data

# Import Monte Carlo components
try:
    from core.analysis.statistics.monte_carlo_engine import (
        MonteCarloEngine,
        ParameterDistribution,
        DistributionType,
        SimulationResult,
        quick_dcf_simulation,
        create_standard_scenarios
    )
    from core.analysis.dcf.monte_carlo_dcf_integration import (
        MonteCarloDCFAnalyzer,
        DCFParameterSet,
        quick_monte_carlo_dcf,
        scenario_comparison_analysis
    )
    from ui.visualization.monte_carlo_visualizer import (
        MonteCarloVisualizer,
        RiskVisualizationManager,
        ScenarioComparisonVisualizer,
        render_monte_carlo_dashboard,
        render_scenario_comparison_dashboard
    )
    MONTE_CARLO_AVAILABLE = True
except ImportError as e:
    st.error(f"Monte Carlo components not available: {e}")
    MONTE_CARLO_AVAILABLE = False

logger = logging.getLogger(__name__)


def render_monte_carlo_analysis_tab(financial_calculator) -> None:
    """
    Render the main Monte Carlo analysis tab.

    Args:
        financial_calculator: FinancialCalculator instance with financial data
    """
    if not MONTE_CARLO_AVAILABLE:
        st.error("Monte Carlo analysis components are not available. Please ensure all dependencies are installed.")
        return

    if financial_calculator is None:
        st.error("Financial calculator is required for Monte Carlo analysis")
        return

    st.header("🎲 Monte Carlo Simulation Analysis")
    st.write("Probabilistic valuation analysis using Monte Carlo simulation for comprehensive risk assessment")

    # Create tabs for different Monte Carlo analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "DCF Monte Carlo",
        "Scenario Analysis",
        "Risk Assessment",
        "Settings & Export"
    ])

    with tab1:
        render_dcf_monte_carlo_tab(financial_calculator)

    with tab2:
        render_scenario_analysis_tab(financial_calculator)

    with tab3:
        render_risk_assessment_tab(financial_calculator)

    with tab4:
        render_settings_export_tab()


def render_dcf_monte_carlo_tab(financial_calculator) -> None:
    """
    Render DCF Monte Carlo simulation interface.

    Args:
        financial_calculator: FinancialCalculator instance
    """
    st.subheader("DCF Monte Carlo Simulation")

    # Simulation settings in columns
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.write("**Simulation Parameters**")
        num_simulations = st.slider(
            "Number of Simulations",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000,
            help="More simulations provide more accurate results but take longer"
        )

        volatility_level = st.selectbox(
            "Volatility Level",
            options=["Low", "Medium", "High", "Custom"],
            index=1,
            help="Predefined volatility levels or custom settings"
        )

        use_historical_data = st.checkbox(
            "Use Historical Volatility",
            value=True,
            help="Use historical data to estimate parameter volatilities"
        )

    with col2:
        st.write("**Custom Volatilities** (if Custom selected)")

        # Custom volatility settings (only shown if Custom is selected)
        if volatility_level == "Custom":
            revenue_volatility = st.slider("Revenue Growth Volatility", 0.01, 0.50, 0.15, 0.01)
            discount_volatility = st.slider("Discount Rate Volatility", 0.005, 0.05, 0.02, 0.005)
            terminal_volatility = st.slider("Terminal Growth Volatility", 0.005, 0.03, 0.01, 0.005)
            margin_volatility = st.slider("Margin Volatility", 0.01, 0.15, 0.05, 0.01)
        else:
            # Use predefined settings
            volatility_settings = {
                "Low": {"revenue": 0.05, "discount": 0.01, "terminal": 0.005, "margin": 0.02},
                "Medium": {"revenue": 0.15, "discount": 0.02, "terminal": 0.01, "margin": 0.05},
                "High": {"revenue": 0.30, "discount": 0.04, "terminal": 0.02, "margin": 0.10}
            }
            settings = volatility_settings.get(volatility_level, volatility_settings["Medium"])
            revenue_volatility = settings["revenue"]
            discount_volatility = settings["discount"]
            terminal_volatility = settings["terminal"]
            margin_volatility = settings["margin"]

    with col3:
        st.write("**Actions**")
        run_simulation = st.button("🚀 Run Simulation", type="primary")

        if st.button("📋 Load Example"):
            st.session_state.monte_carlo_example_loaded = True

    # Display current settings
    with st.expander("Current Simulation Settings", expanded=False):
        settings_df = pd.DataFrame({
            'Parameter': ['Revenue Growth Volatility', 'Discount Rate Volatility',
                         'Terminal Growth Volatility', 'Margin Volatility'],
            'Value': [f"{revenue_volatility:.1%}", f"{discount_volatility:.1%}",
                     f"{terminal_volatility:.1%}", f"{margin_volatility:.1%}"]
        })
        st.dataframe(settings_df, use_container_width=True)

    # Run simulation
    if run_simulation or st.session_state.get('monte_carlo_example_loaded', False):
        with st.spinner("Running Monte Carlo simulation..."):
            try:
                # Initialize Monte Carlo analyzer
                mc_analyzer = MonteCarloDCFAnalyzer(financial_calculator)

                # Run simulation based on settings
                if volatility_level != "Custom" and not use_historical_data:
                    # Use quick simulation with predefined volatility
                    result = quick_dcf_simulation(
                        financial_calculator,
                        num_simulations,
                        volatility_level.lower()
                    )
                else:
                    # Use detailed analysis
                    if volatility_level == "Custom":
                        # Create custom parameter set
                        from core.analysis.dcf.monte_carlo_dcf_integration import DCFParameterSet

                        # Get base parameters from estimator
                        base_params = mc_analyzer.parameter_estimator._get_default_parameters()

                        custom_params = DCFParameterSet(
                            revenue_growth=base_params.revenue_growth,
                            revenue_growth_volatility=revenue_volatility,
                            discount_rate=base_params.discount_rate,
                            discount_rate_volatility=discount_volatility,
                            terminal_growth=base_params.terminal_growth,
                            terminal_growth_volatility=terminal_volatility,
                            operating_margin=base_params.operating_margin,
                            margin_volatility=margin_volatility,
                            tax_rate=base_params.tax_rate,
                            tax_volatility=base_params.tax_volatility,
                            capex_rate=base_params.capex_rate,
                            capex_volatility=base_params.capex_volatility,
                            working_capital_rate=base_params.working_capital_rate,
                            wc_volatility=base_params.wc_volatility
                        )

                        result = mc_analyzer.analyze_dcf_uncertainty(
                            num_simulations=num_simulations,
                            use_historical_volatility=False,
                            custom_parameters=custom_params
                        )
                    else:
                        result = mc_analyzer.analyze_dcf_uncertainty(
                            num_simulations=num_simulations,
                            use_historical_volatility=use_historical_data
                        )

                # Store result in session state
                st.session_state.monte_carlo_result = result

                # Display results
                display_monte_carlo_results(result, financial_calculator)

                # Clear example flag
                if 'monte_carlo_example_loaded' in st.session_state:
                    del st.session_state.monte_carlo_example_loaded

            except Exception as e:
                st.error(f"Error running Monte Carlo simulation: {str(e)}")
                logger.error(f"Monte Carlo simulation error: {e}", exc_info=True)

    # Show previous results if available
    elif 'monte_carlo_result' in st.session_state:
        st.info("Showing previous simulation results. Click 'Run Simulation' to generate new results.")
        display_monte_carlo_results(st.session_state.monte_carlo_result, financial_calculator)


def display_monte_carlo_results(result: SimulationResult, financial_calculator) -> None:
    """
    Display Monte Carlo simulation results.

    Args:
        result: Monte Carlo simulation result
        financial_calculator: FinancialCalculator instance
    """
    st.success(f"✅ Simulation completed successfully with {len(result.values)} valid simulations")

    # Key metrics overview
    st.subheader("📊 Key Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Expected Intrinsic Value",
            f"${result.mean_value:,.2f}",
            help="Mean of all simulated valuations"
        )

    with col2:
        st.metric(
            "Median Value",
            f"${result.median_value:,.2f}",
            help="Middle value when all results are sorted"
        )

    with col3:
        confidence_interval = result.ci_95
        ci_range = confidence_interval[1] - confidence_interval[0]
        st.metric(
            "95% Confidence Range",
            f"${ci_range:,.2f}",
            help=f"Range: ${confidence_interval[0]:,.2f} - ${confidence_interval[1]:,.2f}"
        )

    with col4:
        if hasattr(result, 'risk_metrics') and result.risk_metrics:
            st.metric(
                "Value at Risk (5%)",
                f"${result.risk_metrics.var_5:,.2f}",
                help="Worst-case outcome at 5% confidence level"
            )

    # Current market price comparison
    try:
        current_price = get_current_market_price(financial_calculator)
        if current_price:
            st.subheader("🎯 Market Comparison")

            prob_undervalued = np.sum(result.values > current_price) / len(result.values)
            expected_return = (result.mean_value - current_price) / current_price

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Current Market Price", f"${current_price:.2f}")

            with col2:
                st.metric(
                    "Probability Undervalued",
                    f"{prob_undervalued:.1%}",
                    help="Probability that intrinsic value > market price"
                )

            with col3:
                color = "normal" if abs(expected_return) < 0.1 else ("off" if expected_return < 0 else "inverse")
                st.metric(
                    "Expected Return",
                    f"{expected_return:.1%}",
                    delta=f"{expected_return:.1%}",
                    delta_color=color,
                    help="Expected return vs current market price"
                )

    except Exception as e:
        logger.warning(f"Could not get current market price: {e}")

    # Visualizations
    st.subheader("📈 Probability Distribution")

    visualizer = MonteCarloVisualizer()

    # Distribution plot
    dist_fig = visualizer.create_distribution_plot(
        result,
        title="Monte Carlo DCF Valuation Distribution"
    )
    st.plotly_chart(dist_fig, use_container_width=True)

    # Risk assessment if available
    if hasattr(result, 'risk_metrics') and result.risk_metrics:
        st.subheader("⚠️ Risk Assessment")

        risk_fig = visualizer.create_risk_dashboard(result, current_price if 'current_price' in locals() else None)
        st.plotly_chart(risk_fig, use_container_width=True)

    # Statistical summary table
    with st.expander("📋 Detailed Statistics", expanded=False):
        if hasattr(result, 'summary_table'):
            summary_df = result.summary_table()
            st.dataframe(summary_df, use_container_width=True)
        else:
            # Create basic summary
            basic_stats = pd.DataFrame({
                'Statistic': ['Mean', 'Median', 'Standard Deviation', 'Minimum', 'Maximum'],
                'Value': [
                    f"${result.statistics.get('mean', 0):,.2f}",
                    f"${result.statistics.get('median', 0):,.2f}",
                    f"${result.statistics.get('std', 0):,.2f}",
                    f"${result.statistics.get('min', 0):,.2f}",
                    f"${result.statistics.get('max', 0):,.2f}"
                ]
            })
            st.dataframe(basic_stats, use_container_width=True)


def render_scenario_analysis_tab(financial_calculator) -> None:
    """
    Render scenario analysis interface.

    Args:
        financial_calculator: FinancialCalculator instance
    """
    st.subheader("📊 Scenario Analysis")
    st.write("Compare different economic scenarios using Monte Carlo simulation")

    # Scenario selection
    col1, col2 = st.columns([3, 1])

    with col1:
        # Get standard scenarios
        standard_scenarios = create_standard_scenarios()

        selected_scenarios = st.multiselect(
            "Select Scenarios to Compare",
            options=list(standard_scenarios.keys()),
            default=["Base Case", "Optimistic", "Pessimistic"],
            help="Choose multiple scenarios for comparison"
        )

    with col2:
        st.write("**Analysis Settings**")
        scenario_simulations = st.slider(
            "Simulations per Scenario",
            min_value=1000,
            max_value=10000,
            value=5000,
            step=500
        )

        run_scenarios = st.button("🚀 Run Scenario Analysis", type="primary")

    # Custom scenario definition
    with st.expander("➕ Define Custom Scenario", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            custom_name = st.text_input("Scenario Name", value="Custom Scenario")
            custom_revenue_growth = st.slider("Revenue Growth", -0.20, 0.50, 0.05, 0.01)
            custom_discount_rate = st.slider("Discount Rate", 0.05, 0.20, 0.10, 0.005)
            custom_terminal_growth = st.slider("Terminal Growth", 0.0, 0.08, 0.03, 0.005)

        with col2:
            custom_margin = st.slider("Operating Margin", 0.05, 0.50, 0.20, 0.01)
            custom_tax_rate = st.slider("Tax Rate", 0.15, 0.40, 0.25, 0.01)
            custom_capex = st.slider("CapEx Rate", 0.01, 0.15, 0.05, 0.01)

        if st.button("Add Custom Scenario"):
            custom_scenario = {
                'revenue_growth': custom_revenue_growth,
                'discount_rate': custom_discount_rate,
                'terminal_growth': custom_terminal_growth,
                'operating_margin': custom_margin,
                'tax_rate': custom_tax_rate,
                'capex_rate': custom_capex
            }

            # Add to session state
            if 'custom_scenarios' not in st.session_state:
                st.session_state.custom_scenarios = {}
            st.session_state.custom_scenarios[custom_name] = custom_scenario

            st.success(f"Added custom scenario: {custom_name}")

    # Include custom scenarios in selection
    if 'custom_scenarios' in st.session_state:
        all_scenarios = {**standard_scenarios, **st.session_state.custom_scenarios}
    else:
        all_scenarios = standard_scenarios

    # Display selected scenarios
    if selected_scenarios:
        st.write("**Selected Scenarios:**")

        scenario_df = pd.DataFrame({
            scenario: params for scenario, params in all_scenarios.items()
            if scenario in selected_scenarios
        }).T

        if not scenario_df.empty:
            # Format as percentages
            for col in scenario_df.columns:
                if col in ['revenue_growth', 'discount_rate', 'terminal_growth', 'operating_margin', 'tax_rate']:
                    scenario_df[col] = scenario_df[col].apply(lambda x: f"{x:.1%}")

            st.dataframe(scenario_df, use_container_width=True)

    # Run scenario analysis
    if run_scenarios and selected_scenarios:
        with st.spinner("Running scenario analysis..."):
            try:
                mc_analyzer = MonteCarloDCFAnalyzer(financial_calculator)

                scenario_results = {}
                progress_bar = st.progress(0)

                for i, scenario_name in enumerate(selected_scenarios):
                    progress_bar.progress((i + 1) / len(selected_scenarios))

                    result = mc_analyzer.run_scenario_monte_carlo(
                        scenario_name,
                        num_simulations=scenario_simulations
                    )
                    scenario_results[scenario_name] = result

                progress_bar.empty()

                # Store results in session state
                st.session_state.scenario_results = scenario_results

                # Display scenario comparison
                display_scenario_comparison(scenario_results)

            except Exception as e:
                st.error(f"Error running scenario analysis: {str(e)}")
                logger.error(f"Scenario analysis error: {e}", exc_info=True)

    # Show previous results if available
    elif 'scenario_results' in st.session_state:
        st.info("Showing previous scenario analysis results.")
        display_scenario_comparison(st.session_state.scenario_results)


def display_scenario_comparison(scenario_results: Dict[str, SimulationResult]) -> None:
    """
    Display scenario comparison results.

    Args:
        scenario_results: Dictionary mapping scenario names to simulation results
    """
    st.success(f"✅ Scenario analysis completed for {len(scenario_results)} scenarios")

    # Summary metrics comparison
    st.subheader("📊 Scenario Comparison Summary")

    summary_data = []
    for scenario_name, result in scenario_results.items():
        summary_data.append({
            'Scenario': scenario_name,
            'Mean Value': result.mean_value,
            'Median Value': result.median_value,
            'Std Deviation': result.statistics.get('std', 0),
            'VaR 5%': result.risk_metrics.var_5 if hasattr(result, 'risk_metrics') and result.risk_metrics else np.percentile(result.values, 5)
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.set_index('Scenario')

    # Format as currency
    for col in ['Mean Value', 'Median Value', 'Std Deviation', 'VaR 5%']:
        summary_df[col] = summary_df[col].apply(lambda x: f"${x:,.2f}")

    st.dataframe(summary_df, use_container_width=True)

    # Scenario comparison charts
    visualizer = ScenarioComparisonVisualizer()

    st.subheader("📈 Multi-Metric Comparison")
    multi_fig = visualizer.create_multi_metric_comparison(scenario_results)
    st.plotly_chart(multi_fig, use_container_width=True)

    # Individual scenario selection for detailed view
    st.subheader("🔍 Detailed Scenario Analysis")
    selected_scenario = st.selectbox(
        "Select Scenario for Detailed View",
        list(scenario_results.keys()),
        help="Choose a scenario to see its detailed distribution"
    )

    if selected_scenario:
        result = scenario_results[selected_scenario]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mean Value", f"${result.mean_value:,.2f}")

        with col2:
            st.metric("Standard Deviation", f"${result.statistics.get('std', 0):,.2f}")

        with col3:
            if hasattr(result, 'risk_metrics') and result.risk_metrics:
                st.metric("Probability of Loss", f"{result.risk_metrics.probability_of_loss:.1%}")

        # Individual distribution plot
        base_visualizer = MonteCarloVisualizer()
        scenario_fig = base_visualizer.create_distribution_plot(
            result,
            title=f"{selected_scenario} - Valuation Distribution"
        )
        st.plotly_chart(scenario_fig, use_container_width=True)


def render_risk_assessment_tab(financial_calculator) -> None:
    """
    Render risk assessment interface.

    Args:
        financial_calculator: FinancialCalculator instance
    """
    st.subheader("⚠️ Risk Assessment Dashboard")
    st.write("Comprehensive risk analysis based on Monte Carlo simulation results")

    # Check if we have Monte Carlo results
    if 'monte_carlo_result' not in st.session_state:
        st.warning("⚠️ No Monte Carlo results available. Please run a DCF Monte Carlo simulation first.")
        return

    result = st.session_state.monte_carlo_result

    # Risk metrics overview
    st.subheader("📊 Risk Metrics Overview")

    if hasattr(result, 'risk_metrics') and result.risk_metrics:
        risk_metrics = result.risk_metrics

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Value at Risk (1%)",
                f"${risk_metrics.var_1:,.2f}",
                help="Worst 1% of outcomes"
            )

        with col2:
            st.metric(
                "Value at Risk (5%)",
                f"${risk_metrics.var_5:,.2f}",
                help="Worst 5% of outcomes"
            )

        with col3:
            st.metric(
                "Conditional VaR (5%)",
                f"${risk_metrics.cvar_5:,.2f}",
                help="Average of worst 5% outcomes"
            )

        with col4:
            st.metric(
                "Upside Potential (95%)",
                f"${risk_metrics.upside_potential:,.2f}",
                help="Best 5% of outcomes"
            )

        # Additional risk metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Probability of Loss",
                f"{risk_metrics.probability_of_loss:.1%}",
                help="Chance of negative valuation"
            )

        with col2:
            st.metric(
                "Maximum Drawdown",
                f"${risk_metrics.max_drawdown:,.2f}",
                help="Maximum potential loss"
            )

        with col3:
            st.metric(
                "Downside Deviation",
                f"${risk_metrics.downside_deviation:,.2f}",
                help="Volatility of negative outcomes"
            )

    # Risk visualization
    st.subheader("📈 Risk Analysis Charts")

    risk_manager = RiskVisualizationManager()
    visualizer = MonteCarloVisualizer()

    # Main risk dashboard
    try:
        current_price = get_current_market_price(financial_calculator)
        risk_dashboard_fig = visualizer.create_risk_dashboard(result, current_price)
        st.plotly_chart(risk_dashboard_fig, use_container_width=True)
    except Exception as e:
        logger.warning(f"Could not create full risk dashboard: {e}")
        # Fallback to basic distribution
        dist_fig = visualizer.create_distribution_plot(result, title="Risk Distribution Analysis")
        st.plotly_chart(dist_fig, use_container_width=True)

    # Risk breakdown table
    st.subheader("📋 Risk Analysis Summary")

    if hasattr(result, 'risk_metrics') and result.risk_metrics:
        risk_data = {
            'Risk Metric': [
                'Value at Risk (1%)',
                'Value at Risk (5%)',
                'Conditional VaR (5%)',
                'Expected Value',
                'Upside Potential (95%)',
                'Maximum Value',
                'Probability of Loss',
                'Downside Deviation'
            ],
            'Value': [
                f"${risk_metrics.var_1:,.2f}",
                f"${risk_metrics.var_5:,.2f}",
                f"${risk_metrics.cvar_5:,.2f}",
                f"${result.mean_value:,.2f}",
                f"${risk_metrics.upside_potential:,.2f}",
                f"${max(result.values):,.2f}",
                f"{risk_metrics.probability_of_loss:.1%}",
                f"${risk_metrics.downside_deviation:,.2f}"
            ],
            'Interpretation': [
                'Worst-case scenario (1% probability)',
                'Moderate downside risk (5% probability)',
                'Average loss in worst 5% of cases',
                'Most likely outcome',
                'Moderate upside potential (5% probability)',
                'Best-case scenario observed',
                'Chance of any loss occurring',
                'Volatility of negative outcomes only'
            ]
        }

        risk_df = pd.DataFrame(risk_data)
        st.dataframe(risk_df, use_container_width=True)


def render_settings_export_tab() -> None:
    """
    Render settings and export interface.
    """
    st.subheader("⚙️ Settings & Export")

    # Visualization settings
    st.write("**Visualization Settings**")

    col1, col2 = st.columns(2)

    with col1:
        chart_theme = st.selectbox(
            "Chart Theme",
            options=["plotly_white", "plotly_dark", "simple_white", "ggplot2"],
            index=0,
            help="Choose visualization theme"
        )

        color_scheme = st.selectbox(
            "Color Scheme",
            options=["viridis", "plasma", "blues", "reds", "greens"],
            index=0,
            help="Select color palette for charts"
        )

    with col2:
        show_confidence_bands = st.checkbox(
            "Show Confidence Bands",
            value=True,
            help="Display confidence intervals on charts"
        )

        interactive_charts = st.checkbox(
            "Interactive Charts",
            value=True,
            help="Enable interactive features in visualizations"
        )

    # Export functionality
    st.write("**Export Options**")

    # Check if results are available
    results_available = ('monte_carlo_result' in st.session_state or
                        'scenario_results' in st.session_state)

    if not results_available:
        st.info("💡 Run a Monte Carlo analysis to enable export options")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Export Results to CSV"):
                export_results_csv()

        with col2:
            if st.button("📈 Export Charts"):
                export_charts()

        with col3:
            if st.button("📋 Generate Report"):
                generate_monte_carlo_report()

    # Reset/Clear data
    st.write("**Data Management**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Monte Carlo Results"):
            if 'monte_carlo_result' in st.session_state:
                del st.session_state.monte_carlo_result
            if 'scenario_results' in st.session_state:
                del st.session_state.scenario_results
            if 'custom_scenarios' in st.session_state:
                del st.session_state.custom_scenarios
            st.success("✅ Cleared all Monte Carlo results")
            st.rerun()

    with col2:
        if st.button("🔄 Reset to Defaults"):
            # Clear custom settings
            st.success("✅ Reset to default settings")


def get_current_market_price(financial_calculator) -> Optional[float]:
    """
    Get current market price from financial calculator.

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        Current market price or None if not available
    """
    try:
        if hasattr(financial_calculator, 'get_current_price'):
            return financial_calculator.get_current_price()
        elif hasattr(financial_calculator, 'current_price'):
            return financial_calculator.current_price
        else:
            # Get from VarInputData (centralized data access)
            ticker = getattr(financial_calculator, 'ticker', None)
            if ticker:
                var_input_data = get_var_input_data()
                stock_price = var_input_data.get_variable('stock_price', ticker)
                if stock_price is not None:
                    return stock_price
    except Exception as e:
        logger.debug(f"Could not get current market price: {e}")

    return None


def export_results_csv() -> None:
    """Export Monte Carlo results to CSV format."""
    try:
        if 'monte_carlo_result' in st.session_state:
            result = st.session_state.monte_carlo_result

            # Create CSV data
            csv_data = pd.DataFrame({
                'Simulation': range(1, len(result.values) + 1),
                'Value': result.values
            })

            # Add statistics
            stats_data = pd.DataFrame({
                'Statistic': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                'Value': [
                    result.statistics.get('mean', 0),
                    result.statistics.get('median', 0),
                    result.statistics.get('std', 0),
                    result.statistics.get('min', 0),
                    result.statistics.get('max', 0)
                ]
            })

            # Convert to CSV
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False)
            csv_buffer.write('\n\nStatistics:\n')
            stats_data.to_csv(csv_buffer, index=False)

            # Download
            st.download_button(
                label="💾 Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"monte_carlo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        else:
            st.warning("No Monte Carlo results to export")

    except Exception as e:
        st.error(f"Error exporting CSV: {str(e)}")


def export_charts() -> None:
    """Export charts as images."""
    st.info("Chart export functionality would be implemented here")
    # Implementation would save current charts as PNG/PDF


def generate_monte_carlo_report() -> None:
    """Generate comprehensive Monte Carlo analysis report."""
    st.info("Report generation functionality would be implemented here")
    # Implementation would create PDF report with all analysis results


# Integration helper function
def add_monte_carlo_to_main_app() -> str:
    """
    Helper function to integrate Monte Carlo analysis into the main Streamlit app.

    Returns:
        Tab name for Monte Carlo analysis
    """
    return "🎲 Monte Carlo Analysis"


# Usage example for integration
"""
# In the main Streamlit app (fcf_analysis_streamlit.py), add this tab:

from ui.streamlit.monte_carlo_dashboard import (
    render_monte_carlo_analysis_tab,
    add_monte_carlo_to_main_app
)

# Add to the main tab selection
main_tabs = [
    "Overview", "FCF Analysis", "DCF Valuation", "DDM Analysis",
    "P/B Analysis", add_monte_carlo_to_main_app(), "Reports"
]

selected_tab = st.selectbox("Select Analysis", main_tabs)

# Add the Monte Carlo tab handler
if selected_tab == add_monte_carlo_to_main_app():
    render_monte_carlo_analysis_tab(financial_calculator)
"""