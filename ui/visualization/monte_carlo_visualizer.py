"""
Monte Carlo Visualization Module
===============================

This module provides comprehensive visualization capabilities for Monte Carlo simulation
results in financial analysis. It creates interactive charts and plots for probability
distributions, risk assessments, and scenario comparisons.

Key Features
------------
- **Probability Distribution Plots**: Histograms and density plots of simulation results
- **Risk Assessment Charts**: VaR, CVaR, and confidence interval visualizations
- **Scenario Comparison**: Side-by-side scenario analysis charts
- **Interactive Streamlit Components**: Web-based interactive visualizations
- **Statistical Summary Tables**: Formatted tables with key metrics
- **Parameter Sensitivity Analysis**: Tornado charts and correlation heatmaps

Classes
-------
MonteCarloVisualizer
    Main class for creating Monte Carlo visualization components

RiskVisualizationManager
    Specialized class for risk-focused visualizations

ScenarioComparisonVisualizer
    Specialized class for scenario comparison charts

Usage Example
-------------
>>> from ui.visualization.monte_carlo_visualizer import MonteCarloVisualizer
>>> from core.analysis.statistics.monte_carlo_engine import SimulationResult
>>>
>>> # Initialize visualizer
>>> visualizer = MonteCarloVisualizer()
>>>
>>> # Create probability distribution plot
>>> fig = visualizer.create_distribution_plot(simulation_result)
>>> fig.show()
>>>
>>> # Create risk assessment dashboard
>>> risk_dashboard = visualizer.create_risk_dashboard(simulation_result)
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any, Union
import streamlit as st
from dataclasses import dataclass
import logging

# Try to import the simulation result classes
try:
    from core.analysis.statistics.monte_carlo_engine import SimulationResult, RiskMetrics
    from core.analysis.dcf.monte_carlo_dcf_integration import MonteCarloDCFAnalyzer
except ImportError:
    # Fallback if imports fail
    SimulationResult = None
    RiskMetrics = None
    MonteCarloDCFAnalyzer = None

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration settings for Monte Carlo visualizations."""
    color_scheme: str = 'viridis'
    figure_width: int = 800
    figure_height: int = 600
    show_confidence_bands: bool = True
    show_risk_zones: bool = True
    interactive: bool = True
    theme: str = 'plotly_white'


class MonteCarloVisualizer:
    """
    Main class for creating Monte Carlo visualization components.

    This class provides comprehensive visualization capabilities for Monte Carlo
    simulation results, including probability distributions, risk metrics,
    and scenario comparisons.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize Monte Carlo visualizer.

        Args:
            config: Visualization configuration settings
        """
        self.config = config or VisualizationConfig()
        self.colors = self._setup_color_palette()
        logger.info("Monte Carlo Visualizer initialized")

    def _setup_color_palette(self) -> Dict[str, str]:
        """Setup color palette for consistent visualization theming."""
        return {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'risk_high': '#dc3545',
            'risk_medium': '#ffc107',
            'risk_low': '#28a745'
        }

    def create_distribution_plot(
        self,
        simulation_result: 'SimulationResult',
        title: str = "Monte Carlo Simulation Results",
        show_statistics: bool = True,
        highlight_percentiles: bool = True
    ) -> go.Figure:
        """
        Create probability distribution plot for simulation results.

        Args:
            simulation_result: Monte Carlo simulation result
            title: Plot title
            show_statistics: Whether to show statistical annotations
            highlight_percentiles: Whether to highlight key percentiles

        Returns:
            Plotly figure with distribution plot
        """
        if simulation_result is None:
            raise ValueError("Simulation result is required")

        values = simulation_result.values

        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Probability Distribution", "Box Plot"),
            vertical_spacing=0.12
        )

        # Histogram with density curve
        fig.add_trace(
            go.Histogram(
                x=values,
                nbinsx=50,
                histnorm='probability density',
                name='Distribution',
                marker_color=self.colors['primary'],
                opacity=0.7,
                showlegend=False
            ),
            row=1, col=1
        )

        # Add kernel density estimation curve
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(values)
            x_range = np.linspace(values.min(), values.max(), 200)
            kde_values = kde(x_range)

            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=kde_values,
                    mode='lines',
                    name='Density Curve',
                    line=dict(color=self.colors['secondary'], width=3),
                    showlegend=False
                ),
                row=1, col=1
            )
        except ImportError:
            logger.warning("scipy not available for KDE curve")

        # Highlight percentiles
        if highlight_percentiles and hasattr(simulation_result, 'percentiles'):
            percentiles = simulation_result.percentiles

            # Key percentiles to highlight
            key_percentiles = [
                ('p5', '5th Percentile (VaR)', self.colors['risk_high']),
                ('p25', '25th Percentile', self.colors['risk_medium']),
                ('p50', 'Median', self.colors['success']),
                ('p75', '75th Percentile', self.colors['risk_medium']),
                ('p95', '95th Percentile', self.colors['risk_low'])
            ]

            for p_key, p_label, p_color in key_percentiles:
                if p_key in percentiles:
                    fig.add_vline(
                        x=percentiles[p_key],
                        line_dash="dash",
                        line_color=p_color,
                        annotation_text=p_label,
                        annotation_position="top",
                        row=1, col=1
                    )

        # Box plot
        fig.add_trace(
            go.Box(
                y=values,
                name='Distribution',
                marker_color=self.colors['primary'],
                boxpoints='outliers',
                showlegend=False
            ),
            row=2, col=1
        )

        # Add statistical annotations
        if show_statistics and hasattr(simulation_result, 'statistics'):
            stats = simulation_result.statistics

            annotation_text = (
                f"Mean: ${stats['mean']:,.2f}<br>"
                f"Std Dev: ${stats['std']:,.2f}<br>"
                f"Skewness: {stats['skewness']:.2f}<br>"
                f"Kurtosis: {stats['kurtosis']:.2f}"
            )

            fig.add_annotation(
                x=0.98, y=0.98,
                xref="paper", yref="paper",
                text=annotation_text,
                showarrow=False,
                align="left",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            )

        # Update layout
        fig.update_layout(
            title=title,
            template=self.config.theme,
            width=self.config.figure_width,
            height=self.config.figure_height,
            showlegend=True
        )

        fig.update_xaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Probability Density", row=1, col=1)
        fig.update_yaxes(title_text="Value ($)", row=2, col=1)

        return fig

    def create_risk_dashboard(
        self,
        simulation_result: 'SimulationResult',
        current_market_price: Optional[float] = None
    ) -> go.Figure:
        """
        Create comprehensive risk assessment dashboard.

        Args:
            simulation_result: Monte Carlo simulation result
            current_market_price: Current market price for comparison

        Returns:
            Plotly figure with risk dashboard
        """
        if not hasattr(simulation_result, 'risk_metrics') or simulation_result.risk_metrics is None:
            raise ValueError("Risk metrics not available in simulation result")

        risk_metrics = simulation_result.risk_metrics
        values = simulation_result.values

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Value at Risk Analysis",
                "Return Distribution",
                "Risk Metrics Comparison",
                "Probability Zones"
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "bar"}, {"type": "pie"}]
            ]
        )

        # 1. VaR Analysis (Top Left)
        var_data = {
            'VaR 1%': risk_metrics.var_1,
            'VaR 5%': risk_metrics.var_5,
            'Median': np.median(values),
            'Mean': np.mean(values),
            '95th Percentile': risk_metrics.upside_potential
        }

        fig.add_trace(
            go.Bar(
                x=list(var_data.keys()),
                y=list(var_data.values()),
                marker_color=[
                    self.colors['risk_high'],
                    self.colors['risk_medium'],
                    self.colors['info'],
                    self.colors['primary'],
                    self.colors['risk_low']
                ],
                showlegend=False,
                name="Risk Levels"
            ),
            row=1, col=1
        )

        # Add current market price line if available
        if current_market_price:
            fig.add_hline(
                y=current_market_price,
                line_dash="dash",
                line_color=self.colors['warning'],
                annotation_text=f"Market Price: ${current_market_price:.2f}",
                row=1, col=1
            )

        # 2. Return Distribution (Top Right)
        if current_market_price:
            returns = (values - current_market_price) / current_market_price * 100

            fig.add_trace(
                go.Histogram(
                    x=returns,
                    nbinsx=40,
                    name='Returns',
                    marker_color=self.colors['secondary'],
                    opacity=0.7,
                    showlegend=False
                ),
                row=1, col=2
            )

            # Add zero return line
            fig.add_vline(
                x=0,
                line_dash="solid",
                line_color=self.colors['dark'],
                annotation_text="Break-even",
                row=1, col=2
            )

        # 3. Risk Metrics Comparison (Bottom Left)
        risk_comparison = {
            'VaR 5%': abs(risk_metrics.var_5),
            'CVaR 5%': abs(risk_metrics.cvar_5),
            'Max Drawdown': abs(risk_metrics.max_drawdown),
            'Std Deviation': np.std(values)
        }

        fig.add_trace(
            go.Bar(
                x=list(risk_comparison.values()),
                y=list(risk_comparison.keys()),
                orientation='h',
                marker_color=self.colors['primary'],
                showlegend=False,
                name="Risk Metrics"
            ),
            row=2, col=1
        )

        # 4. Probability Zones (Bottom Right)
        if current_market_price:
            prob_loss = risk_metrics.probability_of_loss
            prob_gain = 1 - prob_loss

            # Calculate probability of significant gains/losses
            prob_big_gain = np.sum(values > current_market_price * 1.2) / len(values)
            prob_moderate_gain = np.sum((values > current_market_price) &
                                      (values <= current_market_price * 1.2)) / len(values)
            prob_moderate_loss = np.sum((values < current_market_price) &
                                       (values >= current_market_price * 0.8)) / len(values)
            prob_big_loss = np.sum(values < current_market_price * 0.8) / len(values)

            prob_zones = {
                'Big Gain (+20%)': prob_big_gain,
                'Moderate Gain': prob_moderate_gain,
                'Moderate Loss': prob_moderate_loss,
                'Big Loss (-20%)': prob_big_loss
            }

            colors_pie = [self.colors['risk_low'], self.colors['success'],
                         self.colors['warning'], self.colors['risk_high']]

            fig.add_trace(
                go.Pie(
                    labels=list(prob_zones.keys()),
                    values=list(prob_zones.values()),
                    marker_colors=colors_pie,
                    showlegend=True,
                    name="Probability Zones"
                ),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            title="Risk Assessment Dashboard",
            template=self.config.theme,
            width=self.config.figure_width * 1.5,
            height=self.config.figure_height * 1.2,
            showlegend=True
        )

        # Update axes labels
        fig.update_xaxes(title_text="Risk Level", row=1, col=1)
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)

        if current_market_price:
            fig.update_xaxes(title_text="Return (%)", row=1, col=2)
            fig.update_yaxes(title_text="Frequency", row=1, col=2)

        fig.update_xaxes(title_text="Risk Value ($)", row=2, col=1)

        return fig

    def create_scenario_comparison(
        self,
        scenario_results: Dict[str, 'SimulationResult'],
        metric: str = 'mean'
    ) -> go.Figure:
        """
        Create scenario comparison visualization.

        Args:
            scenario_results: Dictionary mapping scenario names to simulation results
            metric: Metric to compare ('mean', 'median', 'var_5', etc.)

        Returns:
            Plotly figure with scenario comparison
        """
        if not scenario_results:
            raise ValueError("Scenario results are required")

        scenarios = list(scenario_results.keys())
        values = []

        # Extract metric values from each scenario
        for scenario_name in scenarios:
            result = scenario_results[scenario_name]

            if metric == 'mean':
                value = result.statistics['mean'] if hasattr(result, 'statistics') else np.mean(result.values)
            elif metric == 'median':
                value = result.statistics['median'] if hasattr(result, 'statistics') else np.median(result.values)
            elif metric == 'var_5':
                value = result.risk_metrics.var_5 if hasattr(result, 'risk_metrics') and result.risk_metrics else np.percentile(result.values, 5)
            elif metric == 'std':
                value = result.statistics['std'] if hasattr(result, 'statistics') else np.std(result.values)
            else:
                value = np.mean(result.values)  # Default to mean

            values.append(value)

        # Create comparison chart
        fig = go.Figure()

        # Bar chart
        fig.add_trace(
            go.Bar(
                x=scenarios,
                y=values,
                marker_color=[self.colors['primary'], self.colors['secondary'],
                             self.colors['success'], self.colors['warning'],
                             self.colors['info']][:len(scenarios)],
                text=[f'${v:,.2f}' for v in values],
                textposition='auto',
                name=f'Scenario {metric.capitalize()}'
            )
        )

        # Update layout
        fig.update_layout(
            title=f"Scenario Comparison - {metric.capitalize()}",
            template=self.config.theme,
            width=self.config.figure_width,
            height=self.config.figure_height,
            xaxis_title="Scenario",
            yaxis_title=f"{metric.capitalize()} Value ($)",
            showlegend=False
        )

        return fig

    def create_parameter_sensitivity_chart(
        self,
        simulation_result: 'SimulationResult',
        parameter_impacts: Dict[str, float]
    ) -> go.Figure:
        """
        Create parameter sensitivity tornado chart.

        Args:
            simulation_result: Monte Carlo simulation result
            parameter_impacts: Dictionary of parameter names to impact values

        Returns:
            Plotly figure with tornado chart
        """
        if not parameter_impacts:
            raise ValueError("Parameter impacts are required")

        # Sort parameters by absolute impact
        sorted_params = sorted(parameter_impacts.items(),
                              key=lambda x: abs(x[1]), reverse=True)

        params, impacts = zip(*sorted_params)

        # Create tornado chart
        fig = go.Figure()

        colors = [self.colors['primary'] if impact >= 0 else self.colors['secondary']
                 for impact in impacts]

        fig.add_trace(
            go.Bar(
                y=params,
                x=impacts,
                orientation='h',
                marker_color=colors,
                text=[f'{impact:+.1%}' for impact in impacts],
                textposition='auto',
                showlegend=False
            )
        )

        fig.update_layout(
            title="Parameter Sensitivity Analysis",
            template=self.config.theme,
            width=self.config.figure_width,
            height=self.config.figure_height,
            xaxis_title="Impact on Valuation (%)",
            yaxis_title="Parameters",
            showlegend=False
        )

        # Add zero line
        fig.add_vline(x=0, line_color=self.colors['dark'], line_width=1)

        return fig

    def create_convergence_plot(
        self,
        simulation_result: 'SimulationResult',
        window_size: int = 100
    ) -> go.Figure:
        """
        Create convergence analysis plot showing how the mean stabilizes.

        Args:
            simulation_result: Monte Carlo simulation result
            window_size: Moving average window size

        Returns:
            Plotly figure with convergence plot
        """
        values = simulation_result.values
        n_simulations = len(values)

        # Calculate cumulative mean
        cumulative_mean = np.cumsum(values) / np.arange(1, n_simulations + 1)

        # Calculate moving average if requested
        moving_avg = None
        if window_size < n_simulations:
            moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')

        fig = go.Figure()

        # Cumulative mean
        fig.add_trace(
            go.Scatter(
                x=np.arange(1, n_simulations + 1),
                y=cumulative_mean,
                mode='lines',
                name='Cumulative Mean',
                line=dict(color=self.colors['primary'], width=2)
            )
        )

        # Moving average
        if moving_avg is not None:
            fig.add_trace(
                go.Scatter(
                    x=np.arange(window_size, n_simulations + 1),
                    y=moving_avg,
                    mode='lines',
                    name=f'Moving Average ({window_size})',
                    line=dict(color=self.colors['secondary'], width=2)
                )
            )

        # Final mean line
        final_mean = cumulative_mean[-1]
        fig.add_hline(
            y=final_mean,
            line_dash="dash",
            line_color=self.colors['success'],
            annotation_text=f"Final Mean: ${final_mean:.2f}"
        )

        fig.update_layout(
            title="Monte Carlo Convergence Analysis",
            template=self.config.theme,
            width=self.config.figure_width,
            height=self.config.figure_height,
            xaxis_title="Number of Simulations",
            yaxis_title="Mean Value ($)",
            showlegend=True
        )

        return fig


class RiskVisualizationManager:
    """
    Specialized class for risk-focused visualizations.

    This class provides advanced risk visualization capabilities including
    VaR analysis, stress testing results, and risk decomposition charts.
    """

    def __init__(self, visualizer: Optional[MonteCarloVisualizer] = None):
        """
        Initialize risk visualization manager.

        Args:
            visualizer: Base Monte Carlo visualizer instance
        """
        self.visualizer = visualizer or MonteCarloVisualizer()
        logger.info("Risk Visualization Manager initialized")

    def create_var_evolution_chart(
        self,
        results_over_time: Dict[str, 'SimulationResult'],
        confidence_levels: List[float] = [0.01, 0.05, 0.10]
    ) -> go.Figure:
        """
        Create VaR evolution chart over time periods.

        Args:
            results_over_time: Dictionary mapping time periods to simulation results
            confidence_levels: VaR confidence levels to display

        Returns:
            Plotly figure with VaR evolution
        """
        time_periods = list(results_over_time.keys())

        fig = go.Figure()

        for conf_level in confidence_levels:
            var_values = []
            for period in time_periods:
                result = results_over_time[period]
                var_value = np.percentile(result.values, conf_level * 100)
                var_values.append(var_value)

            fig.add_trace(
                go.Scatter(
                    x=time_periods,
                    y=var_values,
                    mode='lines+markers',
                    name=f'VaR {conf_level:.0%}',
                    line=dict(width=3)
                )
            )

        fig.update_layout(
            title="Value at Risk Evolution Over Time",
            template=self.visualizer.config.theme,
            width=self.visualizer.config.figure_width,
            height=self.visualizer.config.figure_height,
            xaxis_title="Time Period",
            yaxis_title="VaR Value ($)",
            showlegend=True
        )

        return fig

    def create_risk_contribution_chart(
        self,
        parameter_risks: Dict[str, float],
        total_risk: float
    ) -> go.Figure:
        """
        Create risk contribution decomposition chart.

        Args:
            parameter_risks: Dictionary of parameter names to risk contributions
            total_risk: Total portfolio risk

        Returns:
            Plotly figure with risk contribution breakdown
        """
        # Calculate percentage contributions
        risk_percentages = {param: (risk / total_risk) * 100
                           for param, risk in parameter_risks.items()}

        # Sort by contribution
        sorted_risks = sorted(risk_percentages.items(),
                             key=lambda x: abs(x[1]), reverse=True)

        params, percentages = zip(*sorted_risks)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=percentages,
                y=params,
                orientation='h',
                marker_color=self.visualizer.colors['primary'],
                text=[f'{pct:+.1f}%' for pct in percentages],
                textposition='auto'
            )
        )

        fig.update_layout(
            title="Risk Contribution by Parameter",
            template=self.visualizer.config.theme,
            width=self.visualizer.config.figure_width,
            height=self.visualizer.config.figure_height,
            xaxis_title="Risk Contribution (%)",
            yaxis_title="Parameters",
            showlegend=False
        )

        return fig


class ScenarioComparisonVisualizer:
    """
    Specialized class for scenario comparison charts.

    This class provides advanced scenario comparison capabilities including
    multi-metric comparisons, scenario probability analysis, and decision trees.
    """

    def __init__(self, visualizer: Optional[MonteCarloVisualizer] = None):
        """
        Initialize scenario comparison visualizer.

        Args:
            visualizer: Base Monte Carlo visualizer instance
        """
        self.visualizer = visualizer or MonteCarloVisualizer()
        logger.info("Scenario Comparison Visualizer initialized")

    def create_multi_metric_comparison(
        self,
        scenario_results: Dict[str, 'SimulationResult'],
        metrics: List[str] = ['mean', 'var_5', 'upside_potential']
    ) -> go.Figure:
        """
        Create multi-metric scenario comparison chart.

        Args:
            scenario_results: Dictionary mapping scenario names to results
            metrics: List of metrics to compare

        Returns:
            Plotly figure with multi-metric comparison
        """
        scenarios = list(scenario_results.keys())

        fig = make_subplots(
            rows=1, cols=len(metrics),
            subplot_titles=[m.replace('_', ' ').title() for m in metrics],
            shared_yaxis=True
        )

        colors = [self.visualizer.colors['primary'],
                 self.visualizer.colors['secondary'],
                 self.visualizer.colors['success']][:len(metrics)]

        for i, metric in enumerate(metrics):
            values = []
            for scenario in scenarios:
                result = scenario_results[scenario]

                if metric == 'mean':
                    value = result.statistics.get('mean', np.mean(result.values))
                elif metric == 'var_5':
                    value = result.risk_metrics.var_5 if result.risk_metrics else np.percentile(result.values, 5)
                elif metric == 'upside_potential':
                    value = result.risk_metrics.upside_potential if result.risk_metrics else np.percentile(result.values, 95)
                else:
                    value = np.mean(result.values)

                values.append(value)

            fig.add_trace(
                go.Bar(
                    x=scenarios,
                    y=values,
                    marker_color=colors[i % len(colors)],
                    name=metric.replace('_', ' ').title(),
                    text=[f'${v:,.2f}' for v in values],
                    textposition='auto',
                    showlegend=(i == 0)
                ),
                row=1, col=i+1
            )

        fig.update_layout(
            title="Multi-Metric Scenario Comparison",
            template=self.visualizer.config.theme,
            width=self.visualizer.config.figure_width * len(metrics),
            height=self.visualizer.config.figure_height,
            showlegend=False
        )

        return fig

    def create_scenario_probability_matrix(
        self,
        scenario_results: Dict[str, 'SimulationResult'],
        value_thresholds: List[float]
    ) -> go.Figure:
        """
        Create scenario probability matrix heatmap.

        Args:
            scenario_results: Dictionary mapping scenario names to results
            value_thresholds: List of value thresholds for probability calculation

        Returns:
            Plotly figure with probability matrix heatmap
        """
        scenarios = list(scenario_results.keys())

        # Calculate probability matrix
        prob_matrix = []
        threshold_labels = [f'>${t:,.0f}+' for t in value_thresholds]

        for scenario in scenarios:
            result = scenario_results[scenario]
            probs = []

            for threshold in value_thresholds:
                prob = np.sum(result.values >= threshold) / len(result.values)
                probs.append(prob)

            prob_matrix.append(probs)

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=prob_matrix,
                x=threshold_labels,
                y=scenarios,
                colorscale='RdYlGn',
                text=[[f'{prob:.1%}' for prob in row] for row in prob_matrix],
                texttemplate='%{text}',
                textfont={"size": 12},
                colorbar=dict(title="Probability")
            )
        )

        fig.update_layout(
            title="Scenario Probability Matrix",
            template=self.visualizer.config.theme,
            width=self.visualizer.config.figure_width,
            height=self.visualizer.config.figure_height,
            xaxis_title="Value Thresholds",
            yaxis_title="Scenarios"
        )

        return fig


# Streamlit integration functions

def render_monte_carlo_dashboard(
    simulation_result: 'SimulationResult',
    current_market_price: Optional[float] = None,
    show_advanced: bool = True
) -> None:
    """
    Render complete Monte Carlo dashboard in Streamlit.

    Args:
        simulation_result: Monte Carlo simulation result
        current_market_price: Current market price for comparison
        show_advanced: Whether to show advanced visualizations
    """
    visualizer = MonteCarloVisualizer()

    st.title("Monte Carlo Analysis Dashboard")

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Expected Value", f"${simulation_result.mean_value:,.2f}")

    with col2:
        st.metric("Standard Deviation", f"${simulation_result.statistics.get('std', 0):,.2f}")

    with col3:
        if hasattr(simulation_result, 'risk_metrics') and simulation_result.risk_metrics:
            st.metric("Value at Risk (5%)", f"${simulation_result.risk_metrics.var_5:,.2f}")

    with col4:
        if current_market_price:
            prob_undervalued = np.sum(simulation_result.values > current_market_price) / len(simulation_result.values)
            st.metric("Prob. Undervalued", f"{prob_undervalued:.1%}")

    # Main distribution plot
    st.subheader("Probability Distribution")
    dist_fig = visualizer.create_distribution_plot(simulation_result)
    st.plotly_chart(dist_fig, use_container_width=True)

    if show_advanced:
        # Risk dashboard
        st.subheader("Risk Assessment")
        risk_fig = visualizer.create_risk_dashboard(simulation_result, current_market_price)
        st.plotly_chart(risk_fig, use_container_width=True)

        # Summary statistics table
        st.subheader("Statistical Summary")
        if hasattr(simulation_result, 'summary_table'):
            summary_df = simulation_result.summary_table()
            st.dataframe(summary_df, use_container_width=True)

        # Convergence analysis
        st.subheader("Convergence Analysis")
        conv_fig = visualizer.create_convergence_plot(simulation_result)
        st.plotly_chart(conv_fig, use_container_width=True)


def render_scenario_comparison_dashboard(
    scenario_results: Dict[str, 'SimulationResult']
) -> None:
    """
    Render scenario comparison dashboard in Streamlit.

    Args:
        scenario_results: Dictionary mapping scenario names to simulation results
    """
    st.title("Scenario Comparison Dashboard")

    visualizer = ScenarioComparisonVisualizer()

    # Multi-metric comparison
    st.subheader("Multi-Metric Comparison")
    multi_fig = visualizer.create_multi_metric_comparison(scenario_results)
    st.plotly_chart(multi_fig, use_container_width=True)

    # Scenario selection for detailed view
    selected_scenario = st.selectbox("Select Scenario for Details",
                                   list(scenario_results.keys()))

    if selected_scenario:
        result = scenario_results[selected_scenario]

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Mean Value", f"${result.statistics.get('mean', 0):,.2f}")
            st.metric("Median Value", f"${result.statistics.get('median', 0):,.2f}")

        with col2:
            if hasattr(result, 'risk_metrics') and result.risk_metrics:
                st.metric("VaR 5%", f"${result.risk_metrics.var_5:,.2f}")
                st.metric("Upside 95%", f"${result.risk_metrics.upside_potential:,.2f}")

        # Individual scenario distribution
        base_visualizer = MonteCarloVisualizer()
        scenario_fig = base_visualizer.create_distribution_plot(
            result,
            title=f"{selected_scenario} - Distribution"
        )
        st.plotly_chart(scenario_fig, use_container_width=True)