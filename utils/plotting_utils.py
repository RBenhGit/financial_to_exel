"""
Unified Plotting Utilities

This module consolidates plotting and visualization logic to eliminate
duplicate chart creation patterns found in data_processing.py and other modules.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class PlottingUtils:
    """
    Centralized plotting utilities for consistent visualization across the application
    """

    # Standard color schemes
    FCF_COLORS = {
        'FCFF': '#1f77b4',  # Blue
        'FCFE': '#ff7f0e',  # Orange
        'LFCF': '#2ca02c',  # Green
        'Average': '#d62728',  # Red
    }

    CHART_DEFAULTS = {
        'height': 600,
        'hover_mode': 'x unified',
        'legend_position': dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        'line_width': 3,
        'marker_size': 8,
    }

    def __init__(self):
        """Initialize plotting utilities"""
        pass

    def create_fcf_comparison_chart(
        self,
        fcf_data: Dict[str, List[float]],
        years: List[int],
        title: Optional[str] = None,
        show_average: bool = True,
    ) -> go.Figure:
        """
        Create FCF comparison chart with consistent styling

        This consolidates the plotting logic from data_processing.py

        Args:
            fcf_data: Dictionary mapping FCF types to value lists
            years: List of years corresponding to the data
            title: Chart title
            show_average: Whether to show average FCF line

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        if not fcf_data:
            return self._create_empty_chart("No FCF data available")

        # Add traces for each FCF type
        for fcf_type, values in fcf_data.items():
            if not values:
                continue

            # Ensure we have matching years and values
            chart_years = years[-len(values) :] if len(years) >= len(values) else years
            chart_values = (
                values[-len(chart_years) :] if len(values) >= len(chart_years) else values
            )

            color = self.FCF_COLORS.get(fcf_type, '#000000')

            fig.add_trace(
                go.Scatter(
                    x=chart_years,
                    y=chart_values,
                    mode='lines+markers',
                    name=fcf_type,
                    line=dict(color=color, width=self.CHART_DEFAULTS['line_width']),
                    marker=dict(size=self.CHART_DEFAULTS['marker_size']),
                    hovertemplate=f'<b>{fcf_type}</b><br>'
                    + 'Year: %{x}<br>'
                    + 'FCF: $%{y:.1f}M<extra></extra>',
                )
            )

        # Add average line if requested and we have multiple FCF types
        if show_average and len(fcf_data) > 1:
            average_values = self._calculate_average_fcf_values(fcf_data, years)
            if average_values['values']:
                fig.add_trace(
                    go.Scatter(
                        x=average_values['years'],
                        y=average_values['values'],
                        mode='lines+markers',
                        name='Average FCF',
                        line=dict(color='#ff4500', width=5, dash='dash'),
                        marker=dict(
                            size=12,
                            symbol='diamond',
                            color='#ff4500',
                            line=dict(width=2, color='#000000'),
                        ),
                        hovertemplate='<b>Average FCF</b><br>'
                        + 'Year: %{x}<br>'
                        + 'Avg FCF: $%{y:.1f}M<br>'
                        + '<i>Average of all FCF types</i><extra></extra>',
                    )
                )

        # Style the chart
        fig.update_layout(
            title=title or 'Free Cash Flow Analysis',
            xaxis_title='Year',
            yaxis_title='Free Cash Flow ($ Millions)',
            hovermode=self.CHART_DEFAULTS['hover_mode'],
            legend=self.CHART_DEFAULTS['legend_position'],
            height=self.CHART_DEFAULTS['height'],
            showlegend=True,
        )

        # Add zero reference line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def create_growth_rate_chart(
        self, growth_rates: Dict[str, Dict[str, Optional[float]]], title: Optional[str] = None
    ) -> go.Figure:
        """
        Create growth rate comparison chart

        Args:
            growth_rates: Nested dict of growth rates by FCF type and period
            title: Chart title

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        if not growth_rates:
            return self._create_empty_chart("No growth rate data available")

        # Extract periods and prepare data
        all_periods = set()
        for rates in growth_rates.values():
            all_periods.update(rates.keys())

        periods = sorted(all_periods, key=lambda x: int(x.replace('yr', '')))
        period_numbers = [int(p.replace('yr', '')) for p in periods]

        # Add trace for each FCF type
        for fcf_type, rates in growth_rates.items():
            values = [rates.get(period) for period in periods]
            # Convert to percentages and handle None values
            percentage_values = [v * 100 if v is not None else None for v in values]

            color = self.FCF_COLORS.get(fcf_type, '#000000')

            fig.add_trace(
                go.Scatter(
                    x=period_numbers,
                    y=percentage_values,
                    mode='lines+markers',
                    name=f'{fcf_type} Growth',
                    line=dict(color=color, width=self.CHART_DEFAULTS['line_width']),
                    marker=dict(size=self.CHART_DEFAULTS['marker_size']),
                    hovertemplate=f'<b>{fcf_type}</b><br>'
                    + 'Period: %{x} years<br>'
                    + 'CAGR: %{y:.1f}%<extra></extra>',
                    connectgaps=False,  # Don't connect None values
                )
            )

        # Style the chart
        fig.update_layout(
            title=title or 'FCF Growth Rate Analysis',
            xaxis_title='Years',
            yaxis_title='Growth Rate (%)',
            hovermode=self.CHART_DEFAULTS['hover_mode'],
            legend=self.CHART_DEFAULTS['legend_position'],
            height=400,
        )

        # Add zero reference line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def create_trend_analysis_chart(
        self,
        years: List[int],
        values: List[float],
        title: Optional[str] = None,
        show_trend_line: bool = True,
    ) -> go.Figure:
        """
        Create trend analysis chart with optional trend line

        Args:
            years: List of years
            values: List of values
            title: Chart title
            show_trend_line: Whether to add linear trend line

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        if not years or not values:
            return self._create_empty_chart("No trend data available")

        # Main data line
        fig.add_trace(
            go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name='Data',
                line=dict(color='#d62728', width=4),
                marker=dict(size=10, symbol='diamond'),
                hovertemplate='<b>Value</b><br>'
                + 'Year: %{x}<br>'
                + 'Value: $%{y:.1f}M<extra></extra>',
            )
        )

        # Add trend line if requested
        if show_trend_line and len(years) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
            trend_values = [slope * year + intercept for year in years]

            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=trend_values,
                    mode='lines',
                    name=f'Trend (R²={r_value**2:.3f})',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    hovertemplate='<b>Trend Line</b><br>'
                    + 'Year: %{x}<br>'
                    + 'Trend: $%{y:.1f}M<br>'
                    + f'Slope: ${slope:.1f}M/year<extra></extra>',
                )
            )

        # Style the chart
        fig.update_layout(
            title=title or 'Trend Analysis',
            xaxis_title='Year',
            yaxis_title='Value ($ Millions)',
            hovermode=self.CHART_DEFAULTS['hover_mode'],
            legend=self.CHART_DEFAULTS['legend_position'],
            height=500,
        )

        # Add zero reference line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def create_dcf_waterfall_chart(
        self, dcf_components: Dict[str, float], title: Optional[str] = None
    ) -> go.Figure:
        """
        Create DCF waterfall chart

        Args:
            dcf_components: Dictionary of DCF components and values
            title: Chart title

        Returns:
            Plotly Figure object
        """
        if not dcf_components:
            return self._create_empty_chart("No DCF data available")

        # Prepare waterfall data
        categories = list(dcf_components.keys())
        values = list(dcf_components.values())

        # Create waterfall chart
        fig = go.Figure(
            go.Waterfall(
                name="DCF Waterfall",
                orientation="v",
                measure=["relative"] * (len(categories) - 1) + ["total"],
                x=categories,
                textposition="outside",
                text=[f"${v:.1f}M" for v in values],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        )

        fig.update_layout(
            title=title or "DCF Valuation Waterfall",
            xaxis_title="Components",
            yaxis_title="Value ($ Millions)",
            height=500,
        )

        return fig

    def create_sensitivity_heatmap(
        self, sensitivity_data: Dict[str, Any], title: Optional[str] = None
    ) -> go.Figure:
        """
        Create sensitivity analysis heatmap

        Args:
            sensitivity_data: Dictionary containing sensitivity analysis results
            title: Chart title

        Returns:
            Plotly Figure object
        """
        if not sensitivity_data:
            return self._create_empty_chart("No sensitivity data available")

        discount_rates = sensitivity_data.get('discount_rates', [])
        growth_rates = sensitivity_data.get('terminal_growth_rates', [])
        valuations = sensitivity_data.get('valuations', [])

        if not all([discount_rates, growth_rates, valuations]):
            return self._create_empty_chart("Incomplete sensitivity data")

        fig = go.Figure(
            data=go.Heatmap(
                z=valuations,
                x=[f"{rate:.1%}" for rate in growth_rates],
                y=[f"{rate:.1%}" for rate in discount_rates],
                colorscale='RdYlGn',
                hovertemplate='<b>Sensitivity Analysis</b><br>'
                + 'Growth Rate: %{x}<br>'
                + 'Discount Rate: %{y}<br>'
                + 'Value per Share: $%{z:.2f}<extra></extra>',
            )
        )

        fig.update_layout(
            title=title or 'DCF Sensitivity Analysis',
            xaxis_title='Terminal Growth Rate',
            yaxis_title='Discount Rate',
            height=500,
        )

        return fig

    def _create_empty_chart(self, message: str) -> go.Figure:
        """
        Create an empty chart with a message

        Args:
            message: Message to display

        Returns:
            Empty Plotly Figure with message
        """
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=20),
        )
        return fig

    def _calculate_average_fcf_values(
        self, fcf_data: Dict[str, List[float]], years: List[int]
    ) -> Dict[str, List]:
        """
        Calculate average FCF values across FCF types

        Args:
            fcf_data: FCF data by type
            years: List of years

        Returns:
            Dictionary with average years and values
        """
        if not fcf_data:
            return {'years': [], 'values': []}

        # Find common years across all FCF types
        all_years_sets = []
        for fcf_type, values in fcf_data.items():
            if values:
                fcf_years = years[-len(values) :] if len(years) >= len(values) else years
                all_years_sets.append(set(fcf_years))

        if not all_years_sets:
            return {'years': [], 'values': []}

        common_years = sorted(list(set.intersection(*all_years_sets)))

        # Calculate averages for common years
        average_values = []
        for year in common_years:
            year_values = []
            for fcf_type, values in fcf_data.items():
                if values:
                    fcf_years = years[-len(values) :] if len(years) >= len(values) else years
                    if year in fcf_years:
                        year_idx = fcf_years.index(year)
                        if year_idx < len(values):
                            year_values.append(values[year_idx])

            if year_values:
                average_values.append(sum(year_values) / len(year_values))
            else:
                average_values.append(None)

        return {'years': common_years, 'values': average_values}

    def apply_common_styling(
        self,
        fig: go.Figure,
        title: Optional[str] = None,
        xaxis_title: Optional[str] = None,
        yaxis_title: Optional[str] = None,
    ) -> go.Figure:
        """
        Apply common styling to a Plotly figure

        Args:
            fig: Figure to style
            title: Chart title
            xaxis_title: X-axis title
            yaxis_title: Y-axis title

        Returns:
            Styled figure
        """
        fig.update_layout(
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            hovermode=self.CHART_DEFAULTS['hover_mode'],
            legend=self.CHART_DEFAULTS['legend_position'],
            height=self.CHART_DEFAULTS['height'],
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
        )

        # Update axes styling
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

        return fig
