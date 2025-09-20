"""
Advanced Data Visualizations
===========================

Sophisticated visualization components with interactive features,
animations, and advanced chart types for financial analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import colorcet as cc
from scipy import stats
import math

from ..components.advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState,
    InteractionEvent, performance_monitor
)


@dataclass
class VisualizationTheme:
    """Theme configuration for visualizations"""
    primary_colors: List[str]
    background_color: str = "rgba(0,0,0,0)"
    grid_color: str = "rgba(128,128,128,0.2)"
    text_color: str = "#000000"
    font_family: str = "Arial, sans-serif"
    line_width: int = 2
    marker_size: int = 8
    opacity: float = 0.8


class AdvancedTimeSeriesChart(AdvancedComponent):
    """
    Advanced time series visualization with multiple series,
    annotations, trend analysis, and interactive features
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.theme = VisualizationTheme(
            primary_colors=px.colors.qualitative.Set1
        )

    @performance_monitor
    def render_content(self, data: pd.DataFrame, config: Dict = None, **kwargs) -> go.Figure:
        """Render advanced time series chart"""
        if data is None or data.empty:
            st.warning("No data available for time series chart")
            return None

        chart_config = config or {}

        # Create subplot structure
        fig = self._create_subplot_structure(chart_config)

        # Add main time series
        self._add_time_series_traces(fig, data, chart_config)

        # Add trend analysis
        if chart_config.get("show_trends", True):
            self._add_trend_analysis(fig, data, chart_config)

        # Add annotations
        if chart_config.get("annotations"):
            self._add_annotations(fig, chart_config["annotations"])

        # Add technical indicators
        if chart_config.get("technical_indicators"):
            self._add_technical_indicators(fig, data, chart_config)

        # Apply styling and layout
        self._apply_advanced_styling(fig, chart_config)

        # Add interactivity
        self._add_chart_interactivity(fig, chart_config)

        # Render with controls
        self._render_chart_with_controls(fig, data, chart_config)

        return fig

    def _create_subplot_structure(self, config: Dict) -> go.Figure:
        """Create subplot structure based on configuration"""
        show_volume = config.get("show_volume", False)
        show_indicators = config.get("technical_indicators", {})

        if show_volume or show_indicators:
            rows = 2 if show_volume else len(show_indicators) + 1
            row_heights = [0.7, 0.3] if show_volume else [0.7] + [0.3/(len(show_indicators))] * len(show_indicators)

            fig = make_subplots(
                rows=rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=row_heights,
                subplot_titles=["Price"] + (["Volume"] if show_volume else [])
            )
        else:
            fig = go.Figure()

        return fig

    def _add_time_series_traces(self, fig: go.Figure, data: pd.DataFrame, config: Dict):
        """Add main time series traces"""
        date_col = config.get("date_column", data.columns[0])
        value_cols = config.get("value_columns", data.columns[1:])

        if isinstance(value_cols, str):
            value_cols = [value_cols]

        for i, col in enumerate(value_cols):
            if col not in data.columns:
                continue

            color = self.theme.primary_colors[i % len(self.theme.primary_colors)]

            # Determine chart type
            chart_type = config.get("chart_type", {}).get(col, "line")

            if chart_type == "candlestick":
                self._add_candlestick_trace(fig, data, config, row=1)
            elif chart_type == "ohlc":
                self._add_ohlc_trace(fig, data, config, row=1)
            elif chart_type == "area":
                self._add_area_trace(fig, data, date_col, col, color, row=1)
            else:  # line chart
                self._add_line_trace(fig, data, date_col, col, color, row=1)

    def _add_candlestick_trace(self, fig: go.Figure, data: pd.DataFrame, config: Dict, row: int = 1):
        """Add candlestick trace for OHLC data"""
        if not all(col in data.columns for col in ["open", "high", "low", "close"]):
            st.warning("OHLC columns not found for candlestick chart")
            return

        fig.add_trace(
            go.Candlestick(
                x=data[config.get("date_column", data.columns[0])],
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                name="Price",
                increasing_line_color="green",
                decreasing_line_color="red"
            ),
            row=row, col=1
        )

    def _add_ohlc_trace(self, fig: go.Figure, data: pd.DataFrame, config: Dict, row: int = 1):
        """Add OHLC trace"""
        if not all(col in data.columns for col in ["open", "high", "low", "close"]):
            st.warning("OHLC columns not found for OHLC chart")
            return

        fig.add_trace(
            go.Ohlc(
                x=data[config.get("date_column", data.columns[0])],
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                name="Price"
            ),
            row=row, col=1
        )

    def _add_area_trace(self, fig: go.Figure, data: pd.DataFrame, date_col: str, value_col: str, color: str, row: int = 1):
        """Add area trace"""
        fig.add_trace(
            go.Scatter(
                x=data[date_col],
                y=data[value_col],
                mode='lines',
                fill='tonexty' if fig.data else 'tozeroy',
                line=dict(color=color, width=self.theme.line_width),
                name=value_col,
                opacity=self.theme.opacity
            ),
            row=row, col=1
        )

    def _add_line_trace(self, fig: go.Figure, data: pd.DataFrame, date_col: str, value_col: str, color: str, row: int = 1):
        """Add line trace"""
        fig.add_trace(
            go.Scatter(
                x=data[date_col],
                y=data[value_col],
                mode='lines+markers',
                line=dict(color=color, width=self.theme.line_width),
                marker=dict(size=self.theme.marker_size, color=color),
                name=value_col,
                hovertemplate=f"<b>{value_col}</b><br>" +
                            f"Date: %{{x}}<br>" +
                            f"Value: %{{y:,.2f}}<br>" +
                            "<extra></extra>"
            ),
            row=row, col=1
        )

    def _add_trend_analysis(self, fig: go.Figure, data: pd.DataFrame, config: Dict):
        """Add trend analysis overlays"""
        date_col = config.get("date_column", data.columns[0])
        value_cols = config.get("value_columns", data.columns[1:])

        if isinstance(value_cols, str):
            value_cols = [value_cols]

        for col in value_cols:
            if col not in data.columns:
                continue

            # Calculate trend line
            trend_data = self._calculate_trend_line(data[date_col], data[col])

            # Add trend line
            fig.add_trace(
                go.Scatter(
                    x=data[date_col],
                    y=trend_data,
                    mode='lines',
                    line=dict(dash='dash', color='gray', width=1),
                    name=f"{col} Trend",
                    showlegend=False
                ),
                row=1, col=1
            )

            # Add moving averages
            for period in config.get("moving_averages", [20, 50]):
                ma_data = data[col].rolling(window=period).mean()
                fig.add_trace(
                    go.Scatter(
                        x=data[date_col],
                        y=ma_data,
                        mode='lines',
                        line=dict(dash='dot', width=1),
                        name=f"MA{period}",
                        opacity=0.7
                    ),
                    row=1, col=1
                )

    def _calculate_trend_line(self, x_data: pd.Series, y_data: pd.Series) -> np.ndarray:
        """Calculate linear trend line"""
        # Convert dates to numeric values
        x_numeric = pd.to_numeric(x_data)
        valid_mask = ~(pd.isna(x_numeric) | pd.isna(y_data))

        if valid_mask.sum() < 2:
            return np.full(len(y_data), np.nan)

        x_clean = x_numeric[valid_mask]
        y_clean = y_data[valid_mask]

        # Calculate linear regression
        slope, intercept, _, _, _ = stats.linregress(x_clean, y_clean)

        # Generate trend line
        return slope * x_numeric + intercept

    def _add_annotations(self, fig: go.Figure, annotations: List[Dict]):
        """Add custom annotations to chart"""
        for annotation in annotations:
            fig.add_annotation(
                x=annotation.get("x"),
                y=annotation.get("y"),
                text=annotation.get("text", ""),
                showarrow=annotation.get("show_arrow", True),
                arrowhead=annotation.get("arrow_head", 2),
                arrowsize=annotation.get("arrow_size", 1),
                arrowwidth=annotation.get("arrow_width", 2),
                arrowcolor=annotation.get("arrow_color", "blue"),
                bgcolor=annotation.get("bg_color", "white"),
                bordercolor=annotation.get("border_color", "black"),
                borderwidth=annotation.get("border_width", 1)
            )

    def _add_technical_indicators(self, fig: go.Figure, data: pd.DataFrame, config: Dict):
        """Add technical indicators as separate subplots"""
        indicators = config.get("technical_indicators", {})
        current_row = 2

        for indicator_name, indicator_config in indicators.items():
            if indicator_name == "rsi":
                self._add_rsi_indicator(fig, data, indicator_config, current_row)
            elif indicator_name == "macd":
                self._add_macd_indicator(fig, data, indicator_config, current_row)
            elif indicator_name == "bollinger_bands":
                self._add_bollinger_bands(fig, data, indicator_config, 1)  # Add to main chart

            current_row += 1

    def _add_rsi_indicator(self, fig: go.Figure, data: pd.DataFrame, config: Dict, row: int):
        """Add RSI indicator"""
        price_col = config.get("price_column", "close")
        period = config.get("period", 14)

        if price_col not in data.columns:
            return

        # Calculate RSI
        rsi_data = self._calculate_rsi(data[price_col], period)

        # Add RSI line
        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=rsi_data,
                mode='lines',
                line=dict(color='purple', width=2),
                name='RSI'
            ),
            row=row, col=1
        )

        # Add overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=1)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _add_macd_indicator(self, fig: go.Figure, data: pd.DataFrame, config: Dict, row: int):
        """Add MACD indicator"""
        price_col = config.get("price_column", "close")
        fast_period = config.get("fast_period", 12)
        slow_period = config.get("slow_period", 26)
        signal_period = config.get("signal_period", 9)

        if price_col not in data.columns:
            return

        # Calculate MACD
        macd_line, signal_line, histogram = self._calculate_macd(
            data[price_col], fast_period, slow_period, signal_period
        )

        # Add MACD line
        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=macd_line,
                mode='lines',
                line=dict(color='blue', width=2),
                name='MACD'
            ),
            row=row, col=1
        )

        # Add signal line
        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=signal_line,
                mode='lines',
                line=dict(color='red', width=2),
                name='Signal'
            ),
            row=row, col=1
        )

        # Add histogram
        fig.add_trace(
            go.Bar(
                x=data[config.get("date_column", data.columns[0])],
                y=histogram,
                name='Histogram',
                opacity=0.7
            ),
            row=row, col=1
        )

    def _calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _add_bollinger_bands(self, fig: go.Figure, data: pd.DataFrame, config: Dict, row: int):
        """Add Bollinger Bands to main chart"""
        price_col = config.get("price_column", "close")
        period = config.get("period", 20)
        std_dev = config.get("std_dev", 2)

        if price_col not in data.columns:
            return

        # Calculate Bollinger Bands
        middle_band = data[price_col].rolling(window=period).mean()
        std = data[price_col].rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        # Add bands
        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=upper_band,
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                name='Upper BB',
                showlegend=False
            ),
            row=row, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=lower_band,
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                name='Lower BB',
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)',
                showlegend=False
            ),
            row=row, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data[config.get("date_column", data.columns[0])],
                y=middle_band,
                mode='lines',
                line=dict(color='gray', width=1),
                name='Middle BB',
                showlegend=False
            ),
            row=row, col=1
        )

    def _apply_advanced_styling(self, fig: go.Figure, config: Dict):
        """Apply advanced styling to the chart"""
        layout_config = {
            "title": {
                "text": config.get("title", "Time Series Analysis"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.theme.font_family}
            },
            "showlegend": config.get("show_legend", True),
            "hovermode": "x unified",
            "plot_bgcolor": self.theme.background_color,
            "paper_bgcolor": self.theme.background_color,
            "font": {"family": self.theme.font_family, "color": self.theme.text_color},
            "margin": {"l": 50, "r": 50, "t": 80, "b": 50},
            "xaxis": {
                "showgrid": True,
                "gridwidth": 1,
                "gridcolor": self.theme.grid_color,
                "showspikes": True,
                "spikemode": "across",
                "spikesnap": "cursor",
                "spikedash": "solid"
            },
            "yaxis": {
                "showgrid": True,
                "gridwidth": 1,
                "gridcolor": self.theme.grid_color,
                "showspikes": True,
                "spikemode": "across",
                "spikesnap": "cursor",
                "spikedash": "solid"
            }
        }

        # Add range selector for time series
        if config.get("show_range_selector", True):
            layout_config["xaxis"]["rangeselector"] = {
                "buttons": [
                    {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                    {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                    {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                    {"count": 1, "label": "YTD", "step": "year", "stepmode": "todate"},
                    {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                    {"step": "all"}
                ]
            }

        # Add range slider
        if config.get("show_range_slider", True):
            layout_config["xaxis"]["rangeslider"] = {"visible": True}

        fig.update_layout(**layout_config)

    def _add_chart_interactivity(self, fig: go.Figure, config: Dict):
        """Add interactive features to the chart"""
        # Enable crossfilter cursor
        fig.update_layout(
            hovermode='x unified',
            spikedistance=1000,
            hoverdistance=100
        )

        # Add drawing tools if requested
        if config.get("enable_drawing", False):
            fig.update_layout(
                dragmode='drawline',
                newshape=dict(line_color='cyan')
            )

    def _render_chart_with_controls(self, fig: go.Figure, data: pd.DataFrame, config: Dict):
        """Render chart with interactive controls"""
        # Main chart
        st.plotly_chart(fig, use_container_width=True, key=f"{self.config.id}_chart")

        # Chart controls
        with st.expander("📊 Chart Controls", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📸 Save Chart", key=f"{self.config.id}_save"):
                    # Export chart
                    st.success("Chart export functionality would be implemented here")

            with col2:
                chart_theme = st.selectbox(
                    "Theme",
                    ["plotly", "plotly_white", "plotly_dark", "ggplot2"],
                    key=f"{self.config.id}_theme"
                )

            with col3:
                show_volume = st.checkbox(
                    "Show Volume",
                    value=config.get("show_volume", False),
                    key=f"{self.config.id}_volume"
                )

            with col4:
                if st.button("🔄 Refresh", key=f"{self.config.id}_refresh"):
                    self.clear_cache()
                    st.rerun()


class InteractiveHeatmap(AdvancedComponent):
    """
    Interactive correlation heatmap with clustering,
    statistical significance, and drill-down capabilities
    """

    @performance_monitor
    def render_content(self, data: pd.DataFrame, config: Dict = None, **kwargs) -> go.Figure:
        """Render interactive heatmap"""
        if data is None or data.empty:
            st.warning("No data available for heatmap")
            return None

        chart_config = config or {}

        # Calculate correlation matrix
        if chart_config.get("correlation", True):
            correlation_data = data.corr()
        else:
            correlation_data = data

        # Apply clustering if requested
        if chart_config.get("cluster", False):
            correlation_data = self._apply_clustering(correlation_data)

        # Calculate statistical significance
        significance_data = None
        if chart_config.get("show_significance", False):
            significance_data = self._calculate_significance(data)

        # Create heatmap
        fig = self._create_heatmap(correlation_data, significance_data, chart_config)

        # Add interactivity
        self._add_heatmap_interactivity(fig, correlation_data, chart_config)

        # Render with controls
        self._render_heatmap_with_controls(fig, correlation_data, chart_config)

        return fig

    def _apply_clustering(self, correlation_data: pd.DataFrame) -> pd.DataFrame:
        """Apply hierarchical clustering to reorder correlation matrix"""
        from scipy.cluster.hierarchy import dendrogram, linkage, leaves_list
        from scipy.spatial.distance import squareform

        # Convert correlation to distance matrix
        distance_matrix = 1 - np.abs(correlation_data)
        condensed_distances = squareform(distance_matrix)

        # Perform hierarchical clustering
        linkage_matrix = linkage(condensed_distances, method='average')
        cluster_order = leaves_list(linkage_matrix)

        # Reorder correlation matrix
        ordered_columns = correlation_data.columns[cluster_order]
        return correlation_data.loc[ordered_columns, ordered_columns]

    def _calculate_significance(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate statistical significance of correlations"""
        n = len(data)
        significance_matrix = pd.DataFrame(
            index=data.columns,
            columns=data.columns,
            dtype=float
        )

        for i, col1 in enumerate(data.columns):
            for j, col2 in enumerate(data.columns):
                if i == j:
                    significance_matrix.loc[col1, col2] = 0.0
                else:
                    # Calculate p-value for correlation
                    corr_coef = data[col1].corr(data[col2])
                    t_stat = corr_coef * np.sqrt((n - 2) / (1 - corr_coef**2))
                    p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 2))
                    significance_matrix.loc[col1, col2] = p_value

        return significance_matrix

    def _create_heatmap(self, correlation_data: pd.DataFrame, significance_data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create the heatmap visualization"""
        # Prepare text annotations
        text_annotations = correlation_data.values.round(3).astype(str)

        # Add significance indicators if available
        if significance_data is not None:
            for i in range(len(correlation_data)):
                for j in range(len(correlation_data.columns)):
                    p_val = significance_data.iloc[i, j]
                    if p_val < 0.001:
                        text_annotations[i, j] += "***"
                    elif p_val < 0.01:
                        text_annotations[i, j] += "**"
                    elif p_val < 0.05:
                        text_annotations[i, j] += "*"

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_data.values,
            x=correlation_data.columns,
            y=correlation_data.index,
            colorscale=config.get("colorscale", "RdBu"),
            zmid=0,
            text=text_annotations,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate="<b>%{y} vs %{x}</b><br>" +
                        "Correlation: %{z:.3f}<br>" +
                        "<extra></extra>"
        ))

        # Update layout
        fig.update_layout(
            title={
                "text": config.get("title", "Correlation Heatmap"),
                "x": 0.5,
                "xanchor": "center"
            },
            width=config.get("width", 800),
            height=config.get("height", 800),
            xaxis={"side": "bottom"},
            yaxis={"side": "left"}
        )

        return fig

    def _add_heatmap_interactivity(self, fig: go.Figure, correlation_data: pd.DataFrame, config: Dict):
        """Add interactive features to heatmap"""
        # Enable selection
        fig.update_traces(
            selector=dict(type='heatmap'),
            selected=dict(marker=dict(opacity=1.0)),
            unselected=dict(marker=dict(opacity=0.5))
        )

    def _render_heatmap_with_controls(self, fig: go.Figure, correlation_data: pd.DataFrame, config: Dict):
        """Render heatmap with controls"""
        # Main heatmap
        st.plotly_chart(fig, use_container_width=True, key=f"{self.config.id}_heatmap")

        # Controls
        with st.expander("🎛️ Heatmap Controls", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                colorscale = st.selectbox(
                    "Color Scale",
                    ["RdBu", "Viridis", "Plasma", "Blues", "Reds"],
                    key=f"{self.config.id}_colorscale"
                )

            with col2:
                show_values = st.checkbox(
                    "Show Values",
                    value=True,
                    key=f"{self.config.id}_show_values"
                )

            with col3:
                cluster_data = st.checkbox(
                    "Apply Clustering",
                    value=False,
                    key=f"{self.config.id}_cluster"
                )

            # Statistical summary
            st.subheader("📊 Correlation Summary")
            summary_stats = pd.DataFrame({
                "Statistic": ["Mean", "Std", "Min", "Max", "Median"],
                "Value": [
                    correlation_data.values[correlation_data.values != 1].mean(),
                    correlation_data.values[correlation_data.values != 1].std(),
                    correlation_data.values[correlation_data.values != 1].min(),
                    correlation_data.values[correlation_data.values != 1].max(),
                    np.median(correlation_data.values[correlation_data.values != 1])
                ]
            })
            st.dataframe(summary_stats, use_container_width=True)


class Multi3DVisualization(AdvancedComponent):
    """
    Advanced 3D visualization for multi-dimensional financial data
    with interactive rotation, zoom, and data point selection
    """

    @performance_monitor
    def render_content(self, data: pd.DataFrame, config: Dict = None, **kwargs) -> go.Figure:
        """Render 3D visualization"""
        if data is None or data.empty:
            st.warning("No data available for 3D visualization")
            return None

        chart_config = config or {}

        # Get axis columns
        x_col = chart_config.get("x_column", data.columns[0])
        y_col = chart_config.get("y_column", data.columns[1])
        z_col = chart_config.get("z_column", data.columns[2] if len(data.columns) > 2 else data.columns[1])

        # Create 3D visualization
        chart_type = chart_config.get("chart_type", "scatter")

        if chart_type == "scatter":
            fig = self._create_3d_scatter(data, x_col, y_col, z_col, chart_config)
        elif chart_type == "surface":
            fig = self._create_3d_surface(data, x_col, y_col, z_col, chart_config)
        elif chart_type == "mesh":
            fig = self._create_3d_mesh(data, x_col, y_col, z_col, chart_config)
        else:
            fig = self._create_3d_scatter(data, x_col, y_col, z_col, chart_config)

        # Apply 3D styling
        self._apply_3d_styling(fig, chart_config)

        # Render with controls
        self._render_3d_with_controls(fig, data, chart_config)

        return fig

    def _create_3d_scatter(self, data: pd.DataFrame, x_col: str, y_col: str, z_col: str, config: Dict) -> go.Figure:
        """Create 3D scatter plot"""
        # Color mapping
        color_col = config.get("color_column")
        size_col = config.get("size_column")

        fig = go.Figure(data=go.Scatter3d(
            x=data[x_col],
            y=data[y_col],
            z=data[z_col],
            mode='markers',
            marker=dict(
                size=data[size_col] if size_col and size_col in data.columns else 8,
                color=data[color_col] if color_col and color_col in data.columns else data[z_col],
                colorscale=config.get("colorscale", "Viridis"),
                showscale=True,
                colorbar=dict(title=color_col if color_col else z_col)
            ),
            text=data.index if config.get("show_labels", False) else None,
            hovertemplate="<b>%{text}</b><br>" +
                        f"{x_col}: %{{x}}<br>" +
                        f"{y_col}: %{{y}}<br>" +
                        f"{z_col}: %{{z}}<br>" +
                        "<extra></extra>"
        ))

        return fig

    def _create_3d_surface(self, data: pd.DataFrame, x_col: str, y_col: str, z_col: str, config: Dict) -> go.Figure:
        """Create 3D surface plot"""
        # Create meshgrid for surface
        x_unique = sorted(data[x_col].unique())
        y_unique = sorted(data[y_col].unique())

        # Pivot data for surface
        surface_data = data.pivot_table(values=z_col, index=y_col, columns=x_col, fill_value=0)

        fig = go.Figure(data=go.Surface(
            z=surface_data.values,
            x=x_unique,
            y=y_unique,
            colorscale=config.get("colorscale", "Viridis"),
            showscale=True
        ))

        return fig

    def _create_3d_mesh(self, data: pd.DataFrame, x_col: str, y_col: str, z_col: str, config: Dict) -> go.Figure:
        """Create 3D mesh plot"""
        fig = go.Figure(data=go.Mesh3d(
            x=data[x_col],
            y=data[y_col],
            z=data[z_col],
            opacity=config.get("opacity", 0.7),
            color=config.get("mesh_color", "lightblue")
        ))

        return fig

    def _apply_3d_styling(self, fig: go.Figure, config: Dict):
        """Apply 3D-specific styling"""
        fig.update_layout(
            title=config.get("title", "3D Financial Analysis"),
            scene=dict(
                xaxis_title=config.get("x_title", "X Axis"),
                yaxis_title=config.get("y_title", "Y Axis"),
                zaxis_title=config.get("z_title", "Z Axis"),
                camera=dict(
                    eye=dict(x=1.2, y=1.2, z=1.2)
                )
            ),
            margin=dict(l=0, r=0, t=50, b=0)
        )

    def _render_3d_with_controls(self, fig: go.Figure, data: pd.DataFrame, config: Dict):
        """Render 3D chart with controls"""
        # Main chart
        st.plotly_chart(fig, use_container_width=True, key=f"{self.config.id}_3d")

        # Controls
        with st.expander("🎮 3D Controls", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                chart_type = st.selectbox(
                    "Chart Type",
                    ["scatter", "surface", "mesh"],
                    key=f"{self.config.id}_3d_type"
                )

            with col2:
                colorscale = st.selectbox(
                    "Color Scale",
                    ["Viridis", "Plasma", "Blues", "Reds", "RdBu"],
                    key=f"{self.config.id}_3d_colorscale"
                )

            with col3:
                opacity = st.slider(
                    "Opacity",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    key=f"{self.config.id}_3d_opacity"
                )


# Factory functions for creating advanced visualizations
def create_time_series_chart(component_id: str) -> AdvancedTimeSeriesChart:
    """Create advanced time series chart"""
    config = ComponentConfig(
        id=component_id,
        title="Advanced Time Series Analysis",
        description="Interactive time series chart with technical indicators",
        cache_enabled=True
    )
    return AdvancedTimeSeriesChart(config)


def create_interactive_heatmap(component_id: str) -> InteractiveHeatmap:
    """Create interactive correlation heatmap"""
    config = ComponentConfig(
        id=component_id,
        title="Interactive Correlation Heatmap",
        description="Advanced heatmap with clustering and significance testing",
        cache_enabled=True
    )
    return InteractiveHeatmap(config)


def create_3d_visualization(component_id: str) -> Multi3DVisualization:
    """Create 3D visualization component"""
    config = ComponentConfig(
        id=component_id,
        title="3D Financial Visualization",
        description="Interactive 3D charts for multi-dimensional analysis",
        cache_enabled=True
    )
    return Multi3DVisualization(config)