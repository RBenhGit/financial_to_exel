"""
Sensitivity Analysis Visualization Module
=========================================

This module provides comprehensive visualization capabilities for sensitivity analysis results,
including tornado charts, heatmaps, elasticity plots, and interactive sensitivity dashboards.

Key Features:
- Tornado charts for parameter impact ranking
- Two-way sensitivity heatmaps
- One-way sensitivity line plots
- Elasticity visualization
- Breakeven analysis charts
- Interactive Streamlit components
- Export capabilities for reports

Classes:
--------
SensitivityVisualizer
    Main visualization class for sensitivity analysis results

TornadoChart
    Specialized tornado chart implementation

SensitivityHeatmap
    Two-way sensitivity heatmap visualization

Usage Example:
--------------
>>> from core.analysis.risk.sensitivity_analysis import SensitivityAnalyzer
>>> from ui.visualization.sensitivity_visualizer import SensitivityVisualizer
>>>
>>> # Run sensitivity analysis
>>> analyzer = SensitivityAnalyzer(financial_calculator)
>>> result = analyzer.tornado_analysis('dcf', ['revenue_growth', 'discount_rate'])
>>>
>>> # Create visualizations
>>> visualizer = SensitivityVisualizer(result)
>>> fig = visualizer.create_tornado_chart()
>>> fig.show()
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union, Any
import streamlit as st
from dataclasses import dataclass
import logging

# Import sensitivity analysis components
from core.analysis.risk.sensitivity_analysis import SensitivityResult, SensitivityMethod

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for sensitivity analysis visualizations."""
    # Color schemes
    tornado_colors: Tuple[str, str] = ('#FF6B6B', '#4ECDC4')  # Red for negative, teal for positive
    heatmap_colorscale: str = 'RdYlBu_r'
    line_colors: List[str] = None

    # Chart dimensions
    chart_width: int = 800
    chart_height: int = 600
    tornado_height: int = 500

    # Formatting
    decimal_places: int = 2
    percentage_format: bool = True
    show_grid: bool = True

    # Interactive features
    show_hover_data: bool = True
    enable_zoom: bool = True
    show_legend: bool = True

    def __post_init__(self):
        """Set default line colors if not provided."""
        if self.line_colors is None:
            self.line_colors = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]


class SensitivityVisualizer:
    """
    Main visualization class for sensitivity analysis results.

    Provides comprehensive visualization capabilities for different types
    of sensitivity analysis including tornado charts, heatmaps, and line plots.
    """

    def __init__(self, result: SensitivityResult, config: Optional[VisualizationConfig] = None):
        """
        Initialize sensitivity visualizer.

        Args:
            result: SensitivityResult containing analysis data
            config: Visualization configuration
        """
        self.result = result
        self.config = config or VisualizationConfig()

        logger.info(f"Sensitivity Visualizer initialized for analysis: {result.analysis_id}")

    def create_tornado_chart(self, top_n: Optional[int] = None, title: Optional[str] = None) -> go.Figure:
        """
        Create tornado chart for parameter impact visualization.

        Args:
            top_n: Number of top parameters to show (default: all)
            title: Custom chart title

        Returns:
            Plotly Figure object
        """
        if self.result.method != SensitivityMethod.TORNADO:
            raise ValueError("Tornado chart requires tornado analysis results")

        tornado_data = self.result.results.get('tornado_data', [])
        if not tornado_data:
            raise ValueError("No tornado data available in results")

        # Limit to top N parameters if specified
        if top_n:
            tornado_data = tornado_data[:top_n]

        # Prepare data for tornado chart
        parameters = [item['display_name'] for item in tornado_data]
        upside_values = [item['upside_percentage'] for item in tornado_data]
        downside_values = [item['downside_percentage'] for item in tornado_data]

        # Create horizontal bar chart
        fig = go.Figure()

        # Add downside bars (negative values)
        fig.add_trace(go.Bar(
            y=parameters,
            x=downside_values,
            name='Downside Impact',
            orientation='h',
            marker_color=self.config.tornado_colors[0],
            hovertemplate='%{y}<br>Downside: %{x:.1f}%<extra></extra>'
        ))

        # Add upside bars (positive values)
        fig.add_trace(go.Bar(
            y=parameters,
            x=upside_values,
            name='Upside Impact',
            orientation='h',
            marker_color=self.config.tornado_colors[1],
            hovertemplate='%{y}<br>Upside: %{x:.1f}%<extra></extra>'
        ))

        # Update layout
        chart_title = title or f"Tornado Chart - {self.result.analysis_id}"

        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Impact on Valuation (%)",
            yaxis_title="Parameters",
            barmode='relative',
            width=self.config.chart_width,
            height=max(self.config.tornado_height, len(parameters) * 40),
            showlegend=self.config.show_legend,
            hovermode='closest',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=self.config.show_grid,
                gridcolor='lightgray',
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=2
            ),
            yaxis=dict(
                showgrid=False,
                categoryorder='array',
                categoryarray=parameters[::-1]  # Reverse to show most sensitive at top
            )
        )

        # Add base case line
        fig.add_vline(
            x=0,
            line_color="black",
            line_width=2,
            annotation_text="Base Case"
        )

        return fig

    def create_sensitivity_heatmap(self, title: Optional[str] = None) -> go.Figure:
        """
        Create heatmap for two-way sensitivity analysis.

        Args:
            title: Custom chart title

        Returns:
            Plotly Figure object
        """
        if self.result.method != SensitivityMethod.TWO_WAY:
            raise ValueError("Heatmap requires two-way sensitivity analysis results")

        heatmap_data = self.result.results.get('heatmap_data')
        param1_values = self.result.results.get('param1_values')
        param2_values = self.result.results.get('param2_values')
        param1_name = self.result.results.get('param1_name')
        param2_name = self.result.results.get('param2_name')

        if not all([heatmap_data, param1_values, param2_values, param1_name, param2_name]):
            raise ValueError("Incomplete two-way sensitivity data")

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[f"{val:.3f}" for val in param1_values],
            y=[f"{val:.3f}" for val in param2_values],
            colorscale=self.config.heatmap_colorscale,
            hoverongaps=False,
            hovertemplate=f'{param1_name}: %{{x}}<br>{param2_name}: %{{y}}<br>Valuation: %{{z:.2f}}<extra></extra>'
        ))

        # Add base case marker if available
        base_coords = self.result.results.get('base_case_coordinates')
        if base_coords:
            # Find closest indices for base case
            param1_base, param2_base = base_coords
            param1_idx = np.argmin(np.abs(np.array(param1_values) - param1_base))
            param2_idx = np.argmin(np.abs(np.array(param2_values) - param2_base))

            fig.add_scatter(
                x=[f"{param1_values[param1_idx]:.3f}"],
                y=[f"{param2_values[param2_idx]:.3f}"],
                mode='markers',
                marker=dict(
                    size=15,
                    color='white',
                    symbol='star',
                    line=dict(color='black', width=2)
                ),
                name='Base Case',
                hovertemplate='Base Case<extra></extra>'
            )

        # Update layout
        chart_title = title or f"Two-Way Sensitivity Analysis - {self.result.analysis_id}"

        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title=param1_name,
            yaxis_title=param2_name,
            width=self.config.chart_width,
            height=self.config.chart_height,
            showlegend=self.config.show_legend
        )

        return fig

    def create_one_way_plots(self, parameters: Optional[List[str]] = None, title: Optional[str] = None) -> go.Figure:
        """
        Create line plots for one-way sensitivity analysis.

        Args:
            parameters: List of parameters to plot (default: all)
            title: Custom chart title

        Returns:
            Plotly Figure object
        """
        if self.result.method not in [SensitivityMethod.ONE_WAY, SensitivityMethod.ELASTICITY]:
            raise ValueError("Line plots require one-way sensitivity analysis results")

        # Get data from appropriate source
        if self.result.method == SensitivityMethod.ELASTICITY:
            results_data = self.result.results.get('derived_from_one_way', {})
        else:
            results_data = self.result.results

        if not results_data:
            raise ValueError("No one-way sensitivity data available")

        # Filter parameters if specified
        if parameters:
            results_data = {k: v for k, v in results_data.items() if k in parameters}

        # Create subplots
        num_params = len(results_data)
        if num_params == 0:
            raise ValueError("No parameters to plot")

        # Determine subplot layout
        if num_params == 1:
            rows, cols = 1, 1
        elif num_params <= 4:
            rows, cols = 2, 2
        elif num_params <= 6:
            rows, cols = 2, 3
        else:
            rows, cols = 3, 3

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[self.result.parameters[param].display_name for param in results_data.keys()],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )

        # Plot each parameter
        row, col = 1, 1
        for i, (param_name, param_data) in enumerate(results_data.items()):
            if 'test_values' not in param_data or 'values' not in param_data:
                continue

            test_values = param_data['test_values']
            output_values = param_data['values']
            base_value = param_data.get('base_value', 0)

            # Calculate percentage changes
            pct_changes = [(val - base_value) / abs(base_value) * 100 for val in test_values]
            output_pct_changes = [(val - self.result.base_case_value) / abs(self.result.base_case_value) * 100
                                 for val in output_values]

            # Add line plot
            color = self.config.line_colors[i % len(self.config.line_colors)]

            fig.add_trace(
                go.Scatter(
                    x=pct_changes,
                    y=output_pct_changes,
                    mode='lines+markers',
                    name=param_name,
                    line=dict(color=color, width=2),
                    marker=dict(size=4),
                    hovertemplate=f'Input Change: %{{x:.1f}}%<br>Output Change: %{{y:.1f}}%<extra></extra>',
                    showlegend=False
                ),
                row=row,
                col=col
            )

            # Add base case point
            fig.add_trace(
                go.Scatter(
                    x=[0],
                    y=[0],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='red',
                        symbol='star'
                    ),
                    name='Base Case',
                    hovertemplate='Base Case<extra></extra>',
                    showlegend=(i == 0)
                ),
                row=row,
                col=col
            )

            # Update subplot axes
            fig.update_xaxes(
                title_text="Parameter Change (%)",
                showgrid=self.config.show_grid,
                row=row,
                col=col
            )
            fig.update_yaxes(
                title_text="Valuation Change (%)",
                showgrid=self.config.show_grid,
                row=row,
                col=col
            )

            # Move to next subplot
            col += 1
            if col > cols:
                col = 1
                row += 1

            if row > rows:
                break

        # Update layout
        chart_title = title or f"One-Way Sensitivity Analysis - {self.result.analysis_id}"

        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center'
            },
            width=self.config.chart_width,
            height=self.config.chart_height,
            showlegend=self.config.show_legend,
            plot_bgcolor='white'
        )

        return fig

    def create_elasticity_chart(self, title: Optional[str] = None) -> go.Figure:
        """
        Create bar chart for elasticity analysis.

        Args:
            title: Custom chart title

        Returns:
            Plotly Figure object
        """
        if self.result.method != SensitivityMethod.ELASTICITY:
            raise ValueError("Elasticity chart requires elasticity analysis results")

        elasticity_data = self.result.results.get('elasticity_data', [])
        if not elasticity_data:
            raise ValueError("No elasticity data available")

        # Prepare data
        parameters = [item['display_name'] for item in elasticity_data]
        elasticities = [item['elasticity'] for item in elasticity_data]

        # Color bars based on elasticity value
        colors = ['red' if e < 0 else 'green' for e in elasticities]

        # Create bar chart
        fig = go.Figure(data=go.Bar(
            x=parameters,
            y=elasticities,
            marker_color=colors,
            hovertemplate='%{x}<br>Elasticity: %{y:.2f}<extra></extra>'
        ))

        # Add horizontal line at elasticity = 1
        fig.add_hline(y=1, line_dash="dash", line_color="gray",
                     annotation_text="Unit Elastic")
        fig.add_hline(y=-1, line_dash="dash", line_color="gray")

        # Update layout
        chart_title = title or f"Parameter Elasticity Analysis - {self.result.analysis_id}"

        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Parameters",
            yaxis_title="Elasticity",
            width=self.config.chart_width,
            height=self.config.chart_height,
            showlegend=False,
            plot_bgcolor='white',
            xaxis=dict(tickangle=45),
            yaxis=dict(
                showgrid=self.config.show_grid,
                gridcolor='lightgray',
                zeroline=True,
                zerolinecolor='black'
            )
        )

        return fig

    def create_breakeven_chart(self, target_value: float, title: Optional[str] = None) -> go.Figure:
        """
        Create bar chart for breakeven analysis.

        Args:
            target_value: Target value for breakeven analysis
            title: Custom chart title

        Returns:
            Plotly Figure object
        """
        if self.result.method != SensitivityMethod.BREAKEVEN:
            raise ValueError("Breakeven chart requires breakeven analysis results")

        breakeven_data = self.result.results.get('breakeven_data', [])
        if not breakeven_data:
            raise ValueError("No breakeven data available")

        # Find data for the specified target value
        target_data = None
        for data in breakeven_data:
            if abs(data['target_value'] - target_value) < 0.01:  # Small tolerance
                target_data = data
                break

        if not target_data:
            raise ValueError(f"No breakeven data found for target value: {target_value}")

        # Prepare data
        parameters = []
        percentage_changes = []
        feasible_flags = []

        for param_name, param_data in target_data['parameter_breakevens'].items():
            param_display = self.result.parameters[param_name].display_name
            parameters.append(param_display)
            percentage_changes.append(param_data['percentage_change'])
            feasible_flags.append(param_data['feasible'])

        # Color bars based on feasibility
        colors = ['green' if feasible else 'red' for feasible in feasible_flags]

        # Create bar chart
        fig = go.Figure(data=go.Bar(
            x=parameters,
            y=percentage_changes,
            marker_color=colors,
            hovertemplate='%{x}<br>Required Change: %{y:.1f}%<extra></extra>'
        ))

        # Update layout
        chart_title = title or f"Breakeven Analysis (Target: {target_value:.2f}) - {self.result.analysis_id}"

        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Parameters",
            yaxis_title="Required Change (%)",
            width=self.config.chart_width,
            height=self.config.chart_height,
            showlegend=False,
            plot_bgcolor='white',
            xaxis=dict(tickangle=45),
            yaxis=dict(
                showgrid=self.config.show_grid,
                gridcolor='lightgray',
                zeroline=True,
                zerolinecolor='black'
            )
        )

        return fig

    def create_summary_dashboard(self) -> go.Figure:
        """
        Create comprehensive summary dashboard.

        Returns:
            Plotly Figure object with multiple subplots
        """
        if self.result.method == SensitivityMethod.TORNADO:
            return self.create_tornado_chart()
        elif self.result.method == SensitivityMethod.TWO_WAY:
            return self.create_sensitivity_heatmap()
        elif self.result.method == SensitivityMethod.ONE_WAY:
            return self.create_one_way_plots()
        elif self.result.method == SensitivityMethod.ELASTICITY:
            return self.create_elasticity_chart()
        else:
            # Create a general summary figure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Analysis Type: {self.result.method.value}<br>"
                     f"Analysis ID: {self.result.analysis_id}<br>"
                     f"Base Case Value: {self.result.base_case_value:.2f}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(
                title="Sensitivity Analysis Summary",
                width=self.config.chart_width,
                height=self.config.chart_height
            )
            return fig

    def export_charts(self, output_dir: str, formats: List[str] = None) -> List[str]:
        """
        Export all applicable charts for the analysis type.

        Args:
            output_dir: Output directory for chart files
            formats: List of formats ('png', 'pdf', 'html', 'svg')

        Returns:
            List of created file paths
        """
        if formats is None:
            formats = ['png', 'html']

        import os
        os.makedirs(output_dir, exist_ok=True)

        created_files = []

        try:
            if self.result.method == SensitivityMethod.TORNADO:
                fig = self.create_tornado_chart()
                for fmt in formats:
                    filepath = os.path.join(output_dir, f"tornado_chart.{fmt}")
                    if fmt == 'html':
                        fig.write_html(filepath)
                    else:
                        fig.write_image(filepath)
                    created_files.append(filepath)

            elif self.result.method == SensitivityMethod.TWO_WAY:
                fig = self.create_sensitivity_heatmap()
                for fmt in formats:
                    filepath = os.path.join(output_dir, f"sensitivity_heatmap.{fmt}")
                    if fmt == 'html':
                        fig.write_html(filepath)
                    else:
                        fig.write_image(filepath)
                    created_files.append(filepath)

            elif self.result.method == SensitivityMethod.ONE_WAY:
                fig = self.create_one_way_plots()
                for fmt in formats:
                    filepath = os.path.join(output_dir, f"one_way_sensitivity.{fmt}")
                    if fmt == 'html':
                        fig.write_html(filepath)
                    else:
                        fig.write_image(filepath)
                    created_files.append(filepath)

            elif self.result.method == SensitivityMethod.ELASTICITY:
                fig = self.create_elasticity_chart()
                for fmt in formats:
                    filepath = os.path.join(output_dir, f"elasticity_analysis.{fmt}")
                    if fmt == 'html':
                        fig.write_html(filepath)
                    else:
                        fig.write_image(filepath)
                    created_files.append(filepath)

            logger.info(f"Exported {len(created_files)} chart files to {output_dir}")

        except Exception as e:
            logger.error(f"Error exporting charts: {e}")

        return created_files


def render_sensitivity_analysis_streamlit(result: SensitivityResult) -> None:
    """
    Render sensitivity analysis results in Streamlit interface.

    Args:
        result: SensitivityResult to display
    """
    st.header(f"Sensitivity Analysis: {result.analysis_id}")

    # Display summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Analysis Method", result.method.value.replace('_', ' ').title())

    with col2:
        st.metric("Base Case Value", f"${result.base_case_value:.2f}")

    with col3:
        most_sensitive = result.get_most_sensitive_parameter()
        st.metric("Most Sensitive Parameter", most_sensitive or "N/A")

    # Create visualizer
    visualizer = SensitivityVisualizer(result)

    # Display appropriate chart based on analysis type
    if result.method == SensitivityMethod.TORNADO:
        st.subheader("Tornado Chart")

        # Control for top N parameters
        top_n = st.slider("Number of parameters to show", 1, len(result.parameters),
                         min(10, len(result.parameters)))

        fig = visualizer.create_tornado_chart(top_n=top_n)
        st.plotly_chart(fig, use_container_width=True)

        # Display tornado data table
        if st.checkbox("Show detailed tornado data"):
            tornado_table = result.get_sensitivity_table()
            st.dataframe(tornado_table)

    elif result.method == SensitivityMethod.TWO_WAY:
        st.subheader("Two-Way Sensitivity Heatmap")

        fig = visualizer.create_sensitivity_heatmap()
        st.plotly_chart(fig, use_container_width=True)

        # Display heatmap data table
        if st.checkbox("Show heatmap data"):
            heatmap_table = result.get_sensitivity_table()
            st.dataframe(heatmap_table)

    elif result.method == SensitivityMethod.ONE_WAY:
        st.subheader("One-Way Sensitivity Analysis")

        # Parameter selection
        available_params = list(result.parameters.keys())
        selected_params = st.multiselect(
            "Select parameters to display",
            available_params,
            default=available_params[:4]  # Show first 4 by default
        )

        if selected_params:
            fig = visualizer.create_one_way_plots(parameters=selected_params)
            st.plotly_chart(fig, use_container_width=True)

        # Display sensitivity table
        if st.checkbox("Show sensitivity data"):
            sensitivity_table = result.get_sensitivity_table()
            st.dataframe(sensitivity_table)

    elif result.method == SensitivityMethod.ELASTICITY:
        st.subheader("Elasticity Analysis")

        fig = visualizer.create_elasticity_chart()
        st.plotly_chart(fig, use_container_width=True)

        # Display elasticity interpretation
        if st.checkbox("Show elasticity interpretations"):
            elasticity_data = result.results.get('elasticity_data', [])
            for item in elasticity_data:
                st.write(f"**{item['display_name']}**: {item['interpretation']}")

    elif result.method == SensitivityMethod.BREAKEVEN:
        st.subheader("Breakeven Analysis")

        # Target value selection
        breakeven_data = result.results.get('breakeven_data', [])
        if breakeven_data:
            target_values = [data['target_value'] for data in breakeven_data]
            selected_target = st.selectbox("Select target value", target_values)

            fig = visualizer.create_breakeven_chart(selected_target)
            st.plotly_chart(fig, use_container_width=True)

    # Display parameter rankings if available
    if result.rankings:
        st.subheader("Parameter Sensitivity Rankings")
        rankings_df = pd.DataFrame(result.rankings)
        st.dataframe(rankings_df)

    # Display statistics
    if result.statistics:
        st.subheader("Analysis Statistics")
        stats_df = pd.DataFrame([result.statistics]).T
        stats_df.columns = ['Value']
        st.dataframe(stats_df)

    # Export options
    if st.button("Export Analysis Results"):
        try:
            # Export to Excel
            filename = f"sensitivity_analysis_{result.analysis_id}.xlsx"
            result.export_results(filename, format='excel')
            st.success(f"Results exported to {filename}")

            # Export charts
            chart_files = visualizer.export_charts("sensitivity_charts", formats=['png', 'html'])
            st.success(f"Charts exported: {len(chart_files)} files created")

        except Exception as e:
            st.error(f"Export failed: {e}")


def create_sensitivity_analysis_tab() -> None:
    """Create Streamlit tab for sensitivity analysis."""
    st.header("Sensitivity Analysis")

    st.write("""
    Perform comprehensive sensitivity analysis on financial valuation models.
    Analyze how changes in key parameters affect valuation outcomes.
    """)

    # Analysis type selection
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Tornado Analysis", "One-Way Sensitivity", "Two-Way Sensitivity",
         "Elasticity Analysis", "Breakeven Analysis"]
    )

    # Valuation method selection
    valuation_method = st.selectbox(
        "Select Valuation Method",
        ["DCF", "DDM", "P/B Analysis"]
    )

    # Parameter selection
    st.subheader("Parameter Configuration")

    # This would integrate with the actual sensitivity analyzer
    # For now, show placeholder UI
    if analysis_type == "Tornado Analysis":
        st.write("Configure tornado analysis parameters:")
        variation_pct = st.slider("Variation Percentage", 0.05, 0.50, 0.20, 0.05)

    elif analysis_type == "Two-Way Sensitivity":
        st.write("Select two parameters for interaction analysis:")
        col1, col2 = st.columns(2)
        with col1:
            param1 = st.selectbox("First Parameter", ["Revenue Growth", "Discount Rate", "Terminal Growth"])
        with col2:
            param2 = st.selectbox("Second Parameter", ["Operating Margin", "Tax Rate", "CAPEX Ratio"])

    # Run analysis button
    if st.button("Run Sensitivity Analysis"):
        with st.spinner("Performing sensitivity analysis..."):
            # This would integrate with the actual analyzer
            st.info("Sensitivity analysis integration would be implemented here")

            # For demonstration, show placeholder result
            st.success("Sensitivity analysis completed!")

            # Show placeholder visualization
            fig = go.Figure()
            fig.add_annotation(
                text="Sensitivity Analysis Results<br>Would be displayed here",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(
                title="Sample Sensitivity Analysis",
                width=800,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)