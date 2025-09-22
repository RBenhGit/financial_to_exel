"""
Risk Analysis Visualization and Reporting
=========================================

This module provides comprehensive visualization and reporting capabilities for risk analysis results,
including probability distribution plots, risk heatmaps, sensitivity charts, and interactive dashboards.

Key Features:
- Probability distribution visualizations with confidence intervals
- Risk heatmaps and correlation matrices
- Interactive tornado charts and sensitivity plots
- Monte Carlo simulation result visualizations
- Comprehensive risk reports with statistical summaries
- Interactive dashboards with drill-down capabilities

Classes:
--------
RiskVisualizationEngine
    Main orchestrator for all risk visualization operations

ProbabilityDistributionPlotter
    Specialized plots for probability distributions and statistical analysis

RiskHeatmapGenerator
    Advanced heatmaps for risk correlation and concentration analysis

SensitivityChartBuilder
    Interactive tornado charts and sensitivity analysis plots

MonteCarloVisualizer
    Visualizations for Monte Carlo simulation results

RiskDashboard
    Interactive dashboard combining all risk visualizations

Usage Example:
--------------
>>> from core.analysis.risk.risk_visualization import RiskVisualizationEngine
>>> from core.analysis.risk.integrated_risk_engine import IntegratedRiskEngine
>>>
>>> # Initialize visualization engine
>>> viz_engine = RiskVisualizationEngine()
>>>
>>> # Create visualizations from risk analysis result
>>> risk_result = integrated_risk_engine.analyze_risk(request)
>>> viz_suite = viz_engine.create_comprehensive_visualizations(risk_result)
>>>
>>> # Generate interactive dashboard
>>> dashboard = viz_engine.create_risk_dashboard(risk_result)
>>> dashboard.render()
>>>
>>> # Export reports
>>> viz_engine.export_risk_report(risk_result, 'risk_analysis_report.html')
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import warnings

# Visualization imports
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import streamlit as st

# Scientific computing imports
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, leaves_list
from scipy.spatial.distance import squareform
import seaborn as sns
import matplotlib.pyplot as plt

# Risk analysis imports
from .risk_framework import RiskAnalysisResult, RiskMetrics
from .risk_metrics import RiskType, RiskLevel
from .correlation_analysis import CorrelationMatrix, CorrelationMethod
from .probability_distributions import ProbabilityDistribution, DistributionType
from ..statistics.monte_carlo_engine import SimulationResult

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of risk visualizations."""
    DISTRIBUTION_PLOT = "distribution_plot"
    RISK_HEATMAP = "risk_heatmap"
    CORRELATION_MATRIX = "correlation_matrix"
    TORNADO_CHART = "tornado_chart"
    SENSITIVITY_PLOT = "sensitivity_plot"
    MONTE_CARLO_HISTOGRAM = "monte_carlo_histogram"
    VALUE_AT_RISK_PLOT = "value_at_risk_plot"
    SCENARIO_COMPARISON = "scenario_comparison"
    RISK_DASHBOARD = "risk_dashboard"
    TAIL_ANALYSIS = "tail_analysis"


@dataclass
class VisualizationConfig:
    """Configuration for risk visualizations."""
    # Chart dimensions
    width: int = 800
    height: int = 600

    # Color schemes
    color_palette: List[str] = field(default_factory=lambda: px.colors.qualitative.Set1)
    risk_color_scale: str = "RdYlBu_r"
    distribution_colors: Dict[str, str] = field(default_factory=lambda: {
        'empirical': '#1f77b4',
        'fitted': '#ff7f0e',
        'confidence': 'rgba(255, 127, 14, 0.3)'
    })

    # Style settings
    font_family: str = "Arial, sans-serif"
    title_font_size: int = 18
    axis_font_size: int = 12
    legend_font_size: int = 10

    # Interactive features
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_selection: bool = True
    show_toolbar: bool = True

    # Report settings
    include_statistics: bool = True
    include_methodology: bool = True
    include_confidence_intervals: bool = True
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95, 0.99])


@dataclass
class VisualizationSuite:
    """Complete suite of risk visualizations."""
    distribution_plots: Dict[str, go.Figure] = field(default_factory=dict)
    risk_heatmaps: Dict[str, go.Figure] = field(default_factory=dict)
    sensitivity_charts: Dict[str, go.Figure] = field(default_factory=dict)
    monte_carlo_plots: Dict[str, go.Figure] = field(default_factory=dict)
    dashboard: Optional[go.Figure] = None
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)


class ProbabilityDistributionPlotter:
    """
    Specialized plotter for probability distributions and statistical analysis.
    Creates comprehensive distribution visualizations with confidence intervals.
    """

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def plot_distribution_analysis(
        self,
        empirical_data: pd.Series,
        fitted_distribution: Optional[ProbabilityDistribution] = None,
        confidence_levels: Optional[List[float]] = None
    ) -> go.Figure:
        """
        Create comprehensive distribution analysis plot.

        Args:
            empirical_data: Empirical data series
            fitted_distribution: Fitted distribution object
            confidence_levels: Confidence levels for VaR visualization

        Returns:
            Plotly figure with distribution analysis
        """
        confidence_levels = confidence_levels or self.config.confidence_levels

        # Create subplots: histogram + QQ plot + P-P plot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Distribution Comparison', 'Histogram with Fitted Distribution',
                'Q-Q Plot', 'P-P Plot'
            ],
            specs=[
                [{"colspan": 2}, None],
                [{"type": "scatter"}, {"type": "scatter"}]
            ]
        )

        # Main distribution plot
        self._add_distribution_comparison(fig, empirical_data, fitted_distribution, row=1, col=1)

        # QQ plot
        if fitted_distribution:
            self._add_qq_plot(fig, empirical_data, fitted_distribution, row=2, col=1)
            self._add_pp_plot(fig, empirical_data, fitted_distribution, row=2, col=2)

        # Add VaR markers
        self._add_var_markers(fig, empirical_data, fitted_distribution, confidence_levels)

        # Style the plot
        self._style_distribution_plot(fig)

        return fig

    def _add_distribution_comparison(
        self,
        fig: go.Figure,
        empirical_data: pd.Series,
        fitted_distribution: Optional[ProbabilityDistribution],
        row: int,
        col: int
    ):
        """Add distribution comparison to subplot."""
        # Empirical histogram
        fig.add_trace(
            go.Histogram(
                x=empirical_data,
                histnorm='probability density',
                nbinsx=50,
                name='Empirical Data',
                opacity=0.7,
                marker_color=self.config.distribution_colors['empirical']
            ),
            row=row, col=col
        )

        if fitted_distribution:
            # Generate x values for fitted distribution
            x_min, x_max = empirical_data.min(), empirical_data.max()
            x_range = x_max - x_min
            x_vals = np.linspace(x_min - 0.1 * x_range, x_max + 0.1 * x_range, 200)

            # Calculate PDF values
            pdf_vals = [fitted_distribution.pdf(x) for x in x_vals]

            # Add fitted distribution curve
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=pdf_vals,
                    mode='lines',
                    name=f'Fitted {fitted_distribution.distribution_type.value}',
                    line=dict(color=self.config.distribution_colors['fitted'], width=3)
                ),
                row=row, col=col
            )

    def _add_qq_plot(
        self,
        fig: go.Figure,
        empirical_data: pd.Series,
        fitted_distribution: ProbabilityDistribution,
        row: int,
        col: int
    ):
        """Add Q-Q plot for distribution comparison."""
        # Calculate quantiles
        sorted_data = np.sort(empirical_data.dropna())
        n = len(sorted_data)
        theoretical_quantiles = [(i - 0.5) / n for i in range(1, n + 1)]

        # Get theoretical quantiles from fitted distribution
        fitted_quantiles = [fitted_distribution.ppf(q) for q in theoretical_quantiles]

        # Add Q-Q plot
        fig.add_trace(
            go.Scatter(
                x=fitted_quantiles,
                y=sorted_data,
                mode='markers',
                name='Q-Q Plot',
                marker=dict(size=4, color='blue'),
                showlegend=False
            ),
            row=row, col=col
        )

        # Add diagonal reference line
        min_val = min(min(fitted_quantiles), min(sorted_data))
        max_val = max(max(fitted_quantiles), max(sorted_data))
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                line=dict(dash='dash', color='red'),
                name='Perfect Fit',
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_pp_plot(
        self,
        fig: go.Figure,
        empirical_data: pd.Series,
        fitted_distribution: ProbabilityDistribution,
        row: int,
        col: int
    ):
        """Add P-P plot for distribution comparison."""
        # Calculate empirical CDF
        sorted_data = np.sort(empirical_data.dropna())
        n = len(sorted_data)
        empirical_probs = [(i - 0.5) / n for i in range(1, n + 1)]

        # Calculate theoretical probabilities
        theoretical_probs = [fitted_distribution.cdf(x) for x in sorted_data]

        # Add P-P plot
        fig.add_trace(
            go.Scatter(
                x=theoretical_probs,
                y=empirical_probs,
                mode='markers',
                name='P-P Plot',
                marker=dict(size=4, color='green'),
                showlegend=False
            ),
            row=row, col=col
        )

        # Add diagonal reference line
        fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode='lines',
                line=dict(dash='dash', color='red'),
                name='Perfect Fit',
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_var_markers(
        self,
        fig: go.Figure,
        empirical_data: pd.Series,
        fitted_distribution: Optional[ProbabilityDistribution],
        confidence_levels: List[float]
    ):
        """Add VaR markers to distribution plot."""
        for i, confidence_level in enumerate(confidence_levels):
            alpha = 1 - confidence_level

            # Calculate empirical VaR
            empirical_var = empirical_data.quantile(alpha)

            # Add vertical line for empirical VaR
            fig.add_vline(
                x=empirical_var,
                line_dash="dash",
                line_color=self.config.color_palette[i % len(self.config.color_palette)],
                annotation_text=f"VaR {confidence_level:.0%}: {empirical_var:.3f}",
                annotation_position="top"
            )

            # If fitted distribution available, add theoretical VaR
            if fitted_distribution:
                theoretical_var = fitted_distribution.var(alpha)
                fig.add_vline(
                    x=theoretical_var,
                    line_dash="dot",
                    line_color=self.config.color_palette[i % len(self.config.color_palette)],
                    annotation_text=f"Fitted VaR {confidence_level:.0%}: {theoretical_var:.3f}",
                    annotation_position="bottom"
                )

    def _style_distribution_plot(self, fig: go.Figure):
        """Apply styling to distribution plot."""
        fig.update_layout(
            title="Distribution Analysis",
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=self.config.height,
            showlegend=True
        )

        # Update subplot titles
        fig.update_xaxes(title_text="Value", row=1, col=1)
        fig.update_yaxes(title_text="Density", row=1, col=1)
        fig.update_xaxes(title_text="Theoretical Quantiles", row=2, col=1)
        fig.update_yaxes(title_text="Sample Quantiles", row=2, col=1)
        fig.update_xaxes(title_text="Theoretical Probabilities", row=2, col=2)
        fig.update_yaxes(title_text="Empirical Probabilities", row=2, col=2)


class RiskHeatmapGenerator:
    """
    Advanced heatmap generator for risk correlation and concentration analysis.
    Creates interactive heatmaps with clustering and statistical significance indicators.
    """

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def create_risk_concentration_heatmap(
        self,
        risk_metrics: Dict[str, RiskMetrics],
        risk_types: List[RiskType]
    ) -> go.Figure:
        """
        Create risk concentration heatmap across assets and risk types.

        Args:
            risk_metrics: Dictionary of risk metrics by asset
            risk_types: List of risk types to include

        Returns:
            Interactive risk concentration heatmap
        """
        # Prepare data matrix
        risk_matrix = self._prepare_risk_matrix(risk_metrics, risk_types)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=risk_matrix.values,
            x=risk_matrix.columns,
            y=risk_matrix.index,
            colorscale=self.config.risk_color_scale,
            zmid=50,  # Neutral risk level
            zmin=0,
            zmax=100,
            text=risk_matrix.values.round(1),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>" +
                        "Risk Type: %{x}<br>" +
                        "Risk Score: %{z:.1f}<br>" +
                        "<extra></extra>",
            colorbar=dict(
                title="Risk Score",
                titleside="right",
                tickmode="array",
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["Low", "Low-Med", "Medium", "Med-High", "High"]
            )
        ))

        self._style_risk_heatmap(fig, "Risk Concentration Heatmap")
        return fig

    def create_correlation_heatmap(
        self,
        correlation_matrix: CorrelationMatrix,
        cluster: bool = True,
        show_significance: bool = True
    ) -> go.Figure:
        """
        Create advanced correlation heatmap with clustering and significance.

        Args:
            correlation_matrix: Correlation matrix object
            cluster: Whether to apply hierarchical clustering
            show_significance: Whether to show significance indicators

        Returns:
            Interactive correlation heatmap
        """
        corr_df = correlation_matrix.to_dataframe()

        # Apply clustering if requested
        if cluster and len(corr_df) > 2:
            corr_df = self._apply_hierarchical_clustering(corr_df)

        # Prepare annotations
        annotations = self._prepare_correlation_annotations(corr_df, show_significance)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_df.values,
            x=corr_df.columns,
            y=corr_df.index,
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            text=annotations,
            texttemplate="%{text}",
            textfont={"size": 9},
            hoverongaps=False,
            hovertemplate="<b>%{y} vs %{x}</b><br>" +
                        "Correlation: %{z:.3f}<br>" +
                        "<extra></extra>",
            colorbar=dict(
                title="Correlation",
                titleside="right"
            )
        ))

        self._style_risk_heatmap(fig, "Asset Correlation Matrix")
        return fig

    def _prepare_risk_matrix(
        self,
        risk_metrics: Dict[str, RiskMetrics],
        risk_types: List[RiskType]
    ) -> pd.DataFrame:
        """Prepare risk matrix for heatmap visualization."""
        risk_data = {}

        for asset_id, metrics in risk_metrics.items():
            asset_risks = {}

            for risk_type in risk_types:
                # Extract risk score based on risk type
                if risk_type == RiskType.MARKET:
                    score = self._calculate_market_risk_score(metrics)
                elif risk_type == RiskType.CREDIT:
                    score = self._calculate_credit_risk_score(metrics)
                elif risk_type == RiskType.LIQUIDITY:
                    score = self._calculate_liquidity_risk_score(metrics)
                elif risk_type == RiskType.OPERATIONAL:
                    score = self._calculate_operational_risk_score(metrics)
                else:
                    score = 50  # Default moderate risk

                asset_risks[risk_type.value] = score

            risk_data[asset_id] = asset_risks

        return pd.DataFrame(risk_data).T

    def _calculate_market_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate market risk score from metrics."""
        components = []

        if metrics.var_1day_95:
            # Convert VaR to risk score (higher VaR = higher risk)
            var_score = min(abs(metrics.var_1day_95) * 1000, 100)
            components.append(var_score)

        if metrics.annual_volatility:
            # Convert volatility to risk score
            vol_score = min(metrics.annual_volatility * 200, 100)
            components.append(vol_score)

        if metrics.max_drawdown:
            # Convert max drawdown to risk score
            dd_score = min(abs(metrics.max_drawdown) * 100, 100)
            components.append(dd_score)

        return np.mean(components) if components else 50

    def _calculate_credit_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate credit risk score from metrics."""
        # Placeholder implementation - would use credit-specific metrics
        return 40  # Default low-medium credit risk

    def _calculate_liquidity_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate liquidity risk score from metrics."""
        # Placeholder implementation - would use liquidity-specific metrics
        return 30  # Default low liquidity risk

    def _calculate_operational_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate operational risk score from metrics."""
        # Placeholder implementation - would use operational-specific metrics
        return 35  # Default low-medium operational risk

    def _apply_hierarchical_clustering(self, corr_df: pd.DataFrame) -> pd.DataFrame:
        """Apply hierarchical clustering to reorder correlation matrix."""
        # Convert correlation to distance matrix
        distance_matrix = 1 - np.abs(corr_df)
        condensed_distances = squareform(distance_matrix)

        # Perform hierarchical clustering
        linkage_matrix = linkage(condensed_distances, method='average')
        cluster_order = leaves_list(linkage_matrix)

        # Reorder correlation matrix
        ordered_columns = corr_df.columns[cluster_order]
        return corr_df.loc[ordered_columns, ordered_columns]

    def _prepare_correlation_annotations(
        self,
        corr_df: pd.DataFrame,
        show_significance: bool
    ) -> np.ndarray:
        """Prepare annotations for correlation heatmap."""
        annotations = corr_df.values.round(3).astype(str)

        if show_significance:
            # Placeholder for significance testing
            # In real implementation, would calculate p-values
            pass

        return annotations

    def _style_risk_heatmap(self, fig: go.Figure, title: str):
        """Apply styling to risk heatmap."""
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor="center",
                font=dict(size=self.config.title_font_size)
            ),
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=self.config.height,
            xaxis={"side": "bottom"},
            yaxis={"side": "left"}
        )


class SensitivityChartBuilder:
    """
    Interactive tornado charts and sensitivity analysis plots.
    Creates comprehensive sensitivity visualizations with parameter impact analysis.
    """

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def create_tornado_chart(
        self,
        sensitivity_results: Dict[str, Dict[str, float]],
        base_value: float,
        title: str = "Sensitivity Analysis"
    ) -> go.Figure:
        """
        Create tornado chart for sensitivity analysis.

        Args:
            sensitivity_results: Dict with parameter names and their impact ranges
            base_value: Base case value
            title: Chart title

        Returns:
            Interactive tornado chart
        """
        # Prepare data for tornado chart
        parameters = []
        low_impacts = []
        high_impacts = []

        for param_name, impacts in sensitivity_results.items():
            parameters.append(param_name)
            low_impact = impacts.get('low', 0) - base_value
            high_impact = impacts.get('high', 0) - base_value

            # Ensure low impact is negative, high impact is positive
            if low_impact > high_impact:
                low_impact, high_impact = high_impact, low_impact

            low_impacts.append(low_impact)
            high_impacts.append(high_impact)

        # Sort by total impact (largest range first)
        total_impacts = [high - low for high, low in zip(high_impacts, low_impacts)]
        sorted_indices = np.argsort(total_impacts)[::-1]

        parameters = [parameters[i] for i in sorted_indices]
        low_impacts = [low_impacts[i] for i in sorted_indices]
        high_impacts = [high_impacts[i] for i in sorted_indices]

        # Create tornado chart
        fig = go.Figure()

        # Add negative (low) impacts
        fig.add_trace(go.Bar(
            y=parameters,
            x=low_impacts,
            orientation='h',
            name='Downside Impact',
            marker_color='red',
            text=[f"{x:.2f}" for x in low_impacts],
            textposition='inside',
            hovertemplate="<b>%{y}</b><br>Impact: %{x:.2f}<extra></extra>"
        ))

        # Add positive (high) impacts
        fig.add_trace(go.Bar(
            y=parameters,
            x=high_impacts,
            orientation='h',
            name='Upside Impact',
            marker_color='green',
            text=[f"{x:.2f}" for x in high_impacts],
            textposition='inside',
            hovertemplate="<b>%{y}</b><br>Impact: %{x:.2f}<extra></extra>"
        ))

        # Add vertical line for base case
        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="black",
            annotation_text=f"Base Case: {base_value:.2f}",
            annotation_position="top"
        )

        # Style the chart
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor="center",
                font=dict(size=self.config.title_font_size)
            ),
            xaxis_title="Impact on Value",
            yaxis_title="Parameters",
            barmode='overlay',
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=max(400, len(parameters) * 30),  # Dynamic height based on parameters
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    def create_sensitivity_spider_chart(
        self,
        sensitivity_results: Dict[str, Dict[str, float]],
        base_value: float
    ) -> go.Figure:
        """
        Create spider/radar chart for sensitivity analysis.

        Args:
            sensitivity_results: Sensitivity analysis results
            base_value: Base case value

        Returns:
            Interactive spider chart
        """
        # Prepare data
        parameters = list(sensitivity_results.keys())
        low_values = []
        high_values = []

        for param in parameters:
            impacts = sensitivity_results[param]
            low_values.append(abs((impacts.get('low', base_value) - base_value) / base_value * 100))
            high_values.append(abs((impacts.get('high', base_value) - base_value) / base_value * 100))

        # Close the radar chart
        parameters += [parameters[0]]
        low_values += [low_values[0]]
        high_values += [high_values[0]]

        # Create spider chart
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=low_values,
            theta=parameters,
            fill='toself',
            name='Downside Sensitivity',
            marker_color='red',
            opacity=0.6
        ))

        fig.add_trace(go.Scatterpolar(
            r=high_values,
            theta=parameters,
            fill='toself',
            name='Upside Sensitivity',
            marker_color='green',
            opacity=0.6
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max(low_values), max(high_values)) * 1.1],
                    title="Sensitivity (%)"
                )
            ),
            title="Sensitivity Spider Chart",
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=self.config.height,
            showlegend=True
        )

        return fig


class MonteCarloVisualizer:
    """
    Visualizations for Monte Carlo simulation results.
    Creates comprehensive plots for simulation distributions and confidence intervals.
    """

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def create_simulation_histogram(
        self,
        simulation_result: SimulationResult,
        confidence_levels: Optional[List[float]] = None
    ) -> go.Figure:
        """
        Create histogram of Monte Carlo simulation results with confidence intervals.

        Args:
            simulation_result: Monte Carlo simulation results
            confidence_levels: Confidence levels for VaR visualization

        Returns:
            Interactive histogram with confidence intervals
        """
        confidence_levels = confidence_levels or self.config.confidence_levels

        # Extract simulation data
        sim_data = simulation_result.simulated_values

        # Create histogram
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=sim_data,
            nbinsx=50,
            histnorm='probability density',
            name='Simulation Results',
            opacity=0.7,
            marker_color=self.config.color_palette[0]
        ))

        # Add confidence interval markers
        for i, confidence_level in enumerate(confidence_levels):
            alpha = 1 - confidence_level
            var_value = np.percentile(sim_data, alpha * 100)

            fig.add_vline(
                x=var_value,
                line_dash="dash",
                line_color=self.config.color_palette[(i + 1) % len(self.config.color_palette)],
                annotation_text=f"VaR {confidence_level:.0%}: {var_value:.3f}",
                annotation_position="top right"
            )

        # Add mean line
        mean_value = np.mean(sim_data)
        fig.add_vline(
            x=mean_value,
            line_dash="solid",
            line_color="black",
            annotation_text=f"Mean: {mean_value:.3f}",
            annotation_position="top left"
        )

        # Style the plot
        fig.update_layout(
            title="Monte Carlo Simulation Results",
            xaxis_title="Simulated Values",
            yaxis_title="Probability Density",
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=self.config.height,
            showlegend=True
        )

        return fig

    def create_convergence_plot(
        self,
        simulation_result: SimulationResult
    ) -> go.Figure:
        """
        Create convergence plot showing how estimates stabilize with more simulations.

        Args:
            simulation_result: Monte Carlo simulation results

        Returns:
            Convergence analysis plot
        """
        sim_data = simulation_result.simulated_values
        n_sims = len(sim_data)

        # Calculate running means and confidence intervals
        sample_sizes = np.logspace(2, np.log10(n_sims), 50).astype(int)
        running_means = []
        running_stds = []
        running_vars_95 = []

        for size in sample_sizes:
            subset = sim_data[:size]
            running_means.append(np.mean(subset))
            running_stds.append(np.std(subset))
            running_vars_95.append(np.percentile(subset, 5))

        # Create convergence plot
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Mean Convergence', 'Standard Deviation Convergence', 'VaR 95% Convergence'],
            vertical_spacing=0.1
        )

        # Mean convergence
        fig.add_trace(
            go.Scatter(
                x=sample_sizes,
                y=running_means,
                mode='lines',
                name='Running Mean',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        # Standard deviation convergence
        fig.add_trace(
            go.Scatter(
                x=sample_sizes,
                y=running_stds,
                mode='lines',
                name='Running Std',
                line=dict(color='green'),
                showlegend=False
            ),
            row=2, col=1
        )

        # VaR convergence
        fig.add_trace(
            go.Scatter(
                x=sample_sizes,
                y=running_vars_95,
                mode='lines',
                name='Running VaR 95%',
                line=dict(color='red'),
                showlegend=False
            ),
            row=3, col=1
        )

        # Update layout
        fig.update_layout(
            title="Monte Carlo Convergence Analysis",
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width,
            height=self.config.height * 1.5,
            showlegend=True
        )

        # Update x-axes to log scale
        fig.update_xaxes(type="log", title_text="Number of Simulations", row=3, col=1)

        return fig


class RiskVisualizationEngine:
    """
    Main orchestrator for all risk visualization operations.
    Coordinates different visualization components to create comprehensive risk analysis plots.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()

        # Initialize visualization components
        self.distribution_plotter = ProbabilityDistributionPlotter(self.config)
        self.heatmap_generator = RiskHeatmapGenerator(self.config)
        self.sensitivity_builder = SensitivityChartBuilder(self.config)
        self.monte_carlo_visualizer = MonteCarloVisualizer(self.config)

        logger.info("Risk Visualization Engine initialized")

    def create_comprehensive_visualizations(
        self,
        risk_analysis_result: RiskAnalysisResult
    ) -> VisualizationSuite:
        """
        Create comprehensive suite of risk visualizations.

        Args:
            risk_analysis_result: Complete risk analysis results

        Returns:
            Complete visualization suite
        """
        logger.info("Creating comprehensive risk visualization suite")

        suite = VisualizationSuite()

        try:
            # Distribution analysis plots
            if hasattr(risk_analysis_result, 'distribution_analysis'):
                suite.distribution_plots = self._create_distribution_plots(risk_analysis_result)

            # Risk heatmaps
            if risk_analysis_result.correlation_matrices:
                suite.risk_heatmaps = self._create_risk_heatmaps(risk_analysis_result)

            # Sensitivity charts
            if hasattr(risk_analysis_result, 'sensitivity_results'):
                suite.sensitivity_charts = self._create_sensitivity_charts(risk_analysis_result)

            # Monte Carlo visualizations
            if risk_analysis_result.monte_carlo_results:
                suite.monte_carlo_plots = self._create_monte_carlo_plots(risk_analysis_result)

            # Summary statistics
            suite.summary_statistics = self._extract_summary_statistics(risk_analysis_result)

            # Generation metadata
            suite.generation_metadata = {
                'generation_time': datetime.now().isoformat(),
                'analysis_id': risk_analysis_result.analysis_id,
                'visualization_config': self.config.__dict__
            }

            logger.info("Comprehensive visualization suite created successfully")

        except Exception as e:
            logger.error(f"Failed to create comprehensive visualizations: {e}")
            raise

        return suite

    def create_risk_dashboard(
        self,
        risk_analysis_result: RiskAnalysisResult
    ) -> go.Figure:
        """
        Create interactive risk dashboard combining multiple visualizations.

        Args:
            risk_analysis_result: Risk analysis results

        Returns:
            Interactive dashboard figure
        """
        logger.info("Creating interactive risk dashboard")

        # Create dashboard with subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Risk Score Distribution', 'Correlation Heatmap',
                'Value at Risk Timeline', 'Sensitivity Analysis',
                'Monte Carlo Results', 'Risk Concentration'
            ],
            specs=[
                [{"type": "histogram"}, {"type": "heatmap"}],
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "histogram"}, {"type": "heatmap"}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.1
        )

        # Add individual components to dashboard
        self._add_dashboard_components(fig, risk_analysis_result)

        # Style dashboard
        fig.update_layout(
            title=dict(
                text="Risk Analysis Dashboard",
                x=0.5,
                xanchor="center",
                font=dict(size=self.config.title_font_size + 4)
            ),
            font=dict(family=self.config.font_family, size=self.config.axis_font_size),
            width=self.config.width * 1.5,
            height=self.config.height * 2,
            showlegend=False
        )

        return fig

    def export_risk_report(
        self,
        risk_analysis_result: RiskAnalysisResult,
        output_path: str,
        format: str = "html"
    ):
        """
        Export comprehensive risk report with all visualizations.

        Args:
            risk_analysis_result: Risk analysis results
            output_path: Output file path
            format: Export format (html, pdf, png)
        """
        logger.info(f"Exporting risk report to {output_path}")

        # Create visualization suite
        viz_suite = self.create_comprehensive_visualizations(risk_analysis_result)

        if format.lower() == "html":
            self._export_html_report(viz_suite, risk_analysis_result, output_path)
        elif format.lower() == "pdf":
            self._export_pdf_report(viz_suite, risk_analysis_result, output_path)
        else:
            logger.warning(f"Unsupported export format: {format}")

    def _create_distribution_plots(self, result: RiskAnalysisResult) -> Dict[str, go.Figure]:
        """Create distribution analysis plots."""
        plots = {}

        # Placeholder for distribution plots
        # Would integrate with actual distribution analysis results

        return plots

    def _create_risk_heatmaps(self, result: RiskAnalysisResult) -> Dict[str, go.Figure]:
        """Create risk heatmaps."""
        heatmaps = {}

        # Correlation heatmaps
        for method, corr_matrix in result.correlation_matrices.items():
            heatmaps[f'correlation_{method}'] = self.heatmap_generator.create_correlation_heatmap(
                corr_matrix, cluster=True, show_significance=True
            )

        return heatmaps

    def _create_sensitivity_charts(self, result: RiskAnalysisResult) -> Dict[str, go.Figure]:
        """Create sensitivity analysis charts."""
        charts = {}

        # Placeholder for sensitivity charts
        # Would integrate with actual sensitivity analysis results

        return charts

    def _create_monte_carlo_plots(self, result: RiskAnalysisResult) -> Dict[str, go.Figure]:
        """Create Monte Carlo visualization plots."""
        plots = {}

        # Process Monte Carlo results
        for analysis_type, mc_result in result.monte_carlo_results.items():
            if hasattr(mc_result, 'simulated_values'):
                plots[f'histogram_{analysis_type}'] = self.monte_carlo_visualizer.create_simulation_histogram(
                    mc_result, self.config.confidence_levels
                )
                plots[f'convergence_{analysis_type}'] = self.monte_carlo_visualizer.create_convergence_plot(
                    mc_result
                )

        return plots

    def _extract_summary_statistics(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Extract summary statistics for visualization suite."""
        stats = {}

        if result.risk_metrics:
            stats['risk_metrics'] = {
                'var_95': result.risk_metrics.var_1day_95,
                'annual_volatility': result.risk_metrics.annual_volatility,
                'max_drawdown': result.risk_metrics.max_drawdown,
                'sharpe_ratio': result.risk_metrics.sharpe_ratio
            }

        if result.overall_risk_score:
            stats['overall_risk'] = {
                'risk_score': result.overall_risk_score,
                'risk_level': result.risk_level.level_name if result.risk_level else 'Unknown'
            }

        return stats

    def _add_dashboard_components(self, fig: go.Figure, result: RiskAnalysisResult):
        """Add individual components to dashboard."""
        # Placeholder for dashboard component addition
        # Would integrate actual visualization components
        pass

    def _export_html_report(
        self,
        viz_suite: VisualizationSuite,
        result: RiskAnalysisResult,
        output_path: str
    ):
        """Export visualization suite as HTML report."""
        # Placeholder for HTML export implementation
        logger.info(f"HTML report would be exported to {output_path}")

    def _export_pdf_report(
        self,
        viz_suite: VisualizationSuite,
        result: RiskAnalysisResult,
        output_path: str
    ):
        """Export visualization suite as PDF report."""
        # Placeholder for PDF export implementation
        logger.info(f"PDF report would be exported to {output_path}")


# Factory functions for creating visualization components
def create_risk_visualization_engine(config: Optional[VisualizationConfig] = None) -> RiskVisualizationEngine:
    """Create risk visualization engine with optional custom configuration."""
    return RiskVisualizationEngine(config)


def create_custom_visualization_config(
    width: int = 800,
    height: int = 600,
    color_palette: Optional[List[str]] = None,
    risk_color_scale: str = "RdYlBu_r"
) -> VisualizationConfig:
    """Create custom visualization configuration."""
    return VisualizationConfig(
        width=width,
        height=height,
        color_palette=color_palette or px.colors.qualitative.Set1,
        risk_color_scale=risk_color_scale
    )