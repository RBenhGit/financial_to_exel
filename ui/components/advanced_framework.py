"""
Advanced UI Components Framework
===============================

Enhanced component system with reactive state management, advanced animations,
and sophisticated user interactions for financial analysis dashboards.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import time
from functools import wraps


class ComponentState(Enum):
    """Component lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    ERROR = "error"
    UPDATING = "updating"


class InteractionEvent(Enum):
    """Types of user interactions"""
    CLICK = "click"
    HOVER = "hover"
    SELECT = "select"
    CHANGE = "change"
    SUBMIT = "submit"
    REFRESH = "refresh"


@dataclass
class ComponentConfig:
    """Advanced configuration for components"""
    id: str
    title: str
    description: str = ""
    cache_enabled: bool = True
    auto_refresh: bool = False
    refresh_interval: int = 30  # seconds
    animation_enabled: bool = True
    loading_placeholder: str = "Loading..."
    error_fallback: str = "Unable to load component"
    responsive: bool = True
    theme: str = "default"
    permissions: List[str] = field(default_factory=list)


@dataclass
class ComponentMetrics:
    """Performance and usage metrics for components"""
    render_time: float = 0.0
    last_render: datetime = field(default_factory=datetime.now)
    render_count: int = 0
    error_count: int = 0
    user_interactions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class EventHandler(Protocol):
    """Protocol for component event handlers"""
    def __call__(self, event: InteractionEvent, data: Any = None) -> Any: ...


class AdvancedComponent(ABC):
    """
    Advanced base component with reactive state management,
    performance monitoring, and sophisticated interactions
    """

    def __init__(self, config: ComponentConfig):
        self.config = config
        self.state = ComponentState.INITIALIZING
        self.metrics = ComponentMetrics()
        self.event_handlers: Dict[InteractionEvent, List[EventHandler]] = {}
        self._cached_data = {}
        self._error_state = None
        self._last_refresh = datetime.now()

    @abstractmethod
    def render_content(self, data: Any = None, **kwargs) -> Any:
        """Render the actual component content"""
        pass

    def render(self, data: Any = None, **kwargs) -> Any:
        """Enhanced render method with lifecycle management"""
        start_time = time.time()

        try:
            # State management
            self._update_state(ComponentState.LOADING)

            # Check cache
            cache_key = self._generate_cache_key(data, kwargs)
            if self.config.cache_enabled and cache_key in self._cached_data:
                self.metrics.cache_hits += 1
                result = self._cached_data[cache_key]
            else:
                self.metrics.cache_misses += 1

                # Auto-refresh logic
                if self._should_refresh():
                    self._last_refresh = datetime.now()

                # Render with loading state
                with self._loading_context():
                    result = self.render_content(data, **kwargs)

                # Cache result
                if self.config.cache_enabled:
                    self._cached_data[cache_key] = result

            # Update metrics
            self.metrics.render_time = time.time() - start_time
            self.metrics.last_render = datetime.now()
            self.metrics.render_count += 1

            # Update state
            self._update_state(ComponentState.READY)

            return result

        except Exception as e:
            self.metrics.error_count += 1
            self._handle_error(e)
            return self._render_error_fallback()

    def _loading_context(self):
        """Context manager for loading states"""
        class LoadingContext:
            def __init__(self, component):
                self.component = component
                self.placeholder = None

            def __enter__(self):
                if self.component.config.animation_enabled:
                    self.placeholder = st.empty()
                    with self.placeholder:
                        st.info(f"🔄 {self.component.config.loading_placeholder}")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.placeholder:
                    self.placeholder.empty()

        return LoadingContext(self)

    def add_event_handler(self, event: InteractionEvent, handler: EventHandler) -> None:
        """Add event handler for user interactions"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def trigger_event(self, event: InteractionEvent, data: Any = None) -> List[Any]:
        """Trigger event and execute all registered handlers"""
        self.metrics.user_interactions += 1
        results = []

        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    result = handler(event, data)
                    results.append(result)
                except Exception as e:
                    st.error(f"Event handler error: {str(e)}")

        return results

    def _update_state(self, new_state: ComponentState) -> None:
        """Update component state"""
        self.state = new_state
        # Store in session state for persistence
        st.session_state[f"{self.config.id}_state"] = new_state.value

    def _should_refresh(self) -> bool:
        """Check if component should auto-refresh"""
        if not self.config.auto_refresh:
            return False

        time_diff = datetime.now() - self._last_refresh
        return time_diff.total_seconds() >= self.config.refresh_interval

    def _generate_cache_key(self, data: Any, kwargs: Dict) -> str:
        """Generate cache key for data and parameters"""
        import hashlib
        content = str(data) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()

    def _handle_error(self, error: Exception) -> None:
        """Handle component errors"""
        self._error_state = error
        self._update_state(ComponentState.ERROR)

        if st.session_state.get("debug_mode", False):
            st.exception(error)

    def _render_error_fallback(self) -> None:
        """Render error fallback UI"""
        st.error(f"⚠️ {self.config.error_fallback}")

        if st.button(f"🔄 Retry {self.config.title}", key=f"{self.config.id}_retry"):
            self.clear_cache()
            st.rerun()

    def clear_cache(self) -> None:
        """Clear component cache"""
        self._cached_data.clear()

    def get_metrics(self) -> ComponentMetrics:
        """Get component performance metrics"""
        return self.metrics


class InteractiveChart(AdvancedComponent):
    """
    Advanced interactive chart component with real-time updates,
    multi-series support, and sophisticated user interactions
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.chart_config = {
            "responsive": True,
            "displayModeBar": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"{config.id}_chart",
                "height": 500,
                "width": 800,
                "scale": 1
            }
        }

    def render_content(self, chart_data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render interactive chart with advanced features"""
        chart_type = chart_data.get("type", "line")
        data = chart_data.get("data")
        layout_config = chart_data.get("layout", {})

        if data is None or data.empty:
            st.warning("No data available for chart")
            return None

        # Create figure based on chart type
        fig = self._create_figure(chart_type, data, chart_data)

        # Apply advanced layout
        self._apply_advanced_layout(fig, layout_config)

        # Add interactivity
        self._add_interactivity(fig, chart_data)

        # Render with Streamlit
        chart_container = st.plotly_chart(
            fig,
            use_container_width=True,
            config=self.chart_config,
            key=f"{self.config.id}_chart"
        )

        # Add chart controls
        self._render_chart_controls(chart_data)

        return fig

    def _create_figure(self, chart_type: str, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create figure based on chart type"""
        if chart_type == "multi_line":
            return self._create_multi_line_chart(data, config)
        elif chart_type == "candlestick":
            return self._create_candlestick_chart(data, config)
        elif chart_type == "heatmap":
            return self._create_heatmap(data, config)
        elif chart_type == "waterfall":
            return self._create_waterfall_chart(data, config)
        elif chart_type == "treemap":
            return self._create_treemap(data, config)
        else:
            # Default line chart
            return px.line(data, x=config.get("x", data.columns[0]),
                          y=config.get("y", data.columns[1]))

    def _create_multi_line_chart(self, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create multi-line chart with custom styling"""
        fig = go.Figure()

        x_col = config.get("x", data.columns[0])
        y_cols = config.get("y_cols", data.columns[1:])

        colors = px.colors.qualitative.Set1

        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
                hovertemplate=f"<b>{y_col}</b><br>" +
                            f"{x_col}: %{{x}}<br>" +
                            f"Value: %{{y:,.2f}}<br>" +
                            "<extra></extra>"
            ))

        return fig

    def _create_candlestick_chart(self, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create candlestick chart for price data"""
        fig = go.Figure(data=go.Candlestick(
            x=data[config.get("x", "date")],
            open=data[config.get("open", "open")],
            high=data[config.get("high", "high")],
            low=data[config.get("low", "low")],
            close=data[config.get("close", "close")],
            name="Price"
        ))

        # Add volume bars if available
        if "volume" in data.columns:
            fig.add_trace(go.Bar(
                x=data[config.get("x", "date")],
                y=data["volume"],
                name="Volume",
                yaxis="y2",
                opacity=0.3
            ))

            # Create secondary y-axis for volume
            fig.update_layout(
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right"
                )
            )

        return fig

    def _create_heatmap(self, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create correlation heatmap"""
        if config.get("correlation", False):
            correlation_data = data.corr()
        else:
            correlation_data = data

        fig = go.Figure(data=go.Heatmap(
            z=correlation_data.values,
            x=correlation_data.columns,
            y=correlation_data.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_data.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        return fig

    def _create_waterfall_chart(self, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create waterfall chart for financial flows"""
        x_col = config.get("x", data.columns[0])
        y_col = config.get("y", data.columns[1])

        fig = go.Figure(go.Waterfall(
            name="Financial Flow",
            orientation="v",
            measure=["relative"] * (len(data) - 1) + ["total"],
            x=data[x_col],
            textposition="outside",
            text=[f"{val:+,.0f}" for val in data[y_col]],
            y=data[y_col],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        return fig

    def _create_treemap(self, data: pd.DataFrame, config: Dict) -> go.Figure:
        """Create treemap for hierarchical data"""
        fig = go.Figure(go.Treemap(
            labels=data[config.get("labels", data.columns[0])],
            values=data[config.get("values", data.columns[1])],
            parents=data[config.get("parents", "")] if "parents" in config else [""] * len(data),
            textinfo="label+value+percent parent",
            textposition="middle center",
            hovertemplate="<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percentParent}<extra></extra>",
        ))

        return fig

    def _apply_advanced_layout(self, fig: go.Figure, layout_config: Dict) -> None:
        """Apply advanced layout configuration"""
        default_layout = {
            "showlegend": True,
            "hovermode": "x unified",
            "xaxis": {
                "showgrid": True,
                "gridwidth": 1,
                "gridcolor": "rgba(128, 128, 128, 0.2)"
            },
            "yaxis": {
                "showgrid": True,
                "gridwidth": 1,
                "gridcolor": "rgba(128, 128, 128, 0.2)"
            },
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Arial, sans-serif", "size": 12},
            "margin": {"l": 50, "r": 50, "t": 80, "b": 50}
        }

        # Merge with user config
        final_layout = {**default_layout, **layout_config}
        fig.update_layout(**final_layout)

    def _add_interactivity(self, fig: go.Figure, config: Dict) -> None:
        """Add interactive features to chart"""
        # Add range selector for time series
        if config.get("time_series", False):
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1M", step="month", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1Y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )

        # Add crossfilter cursor
        fig.update_layout(
            hovermode='x unified',
            spikedistance=1000,
            hoverdistance=100
        )

        fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid")
        fig.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid")

    def _render_chart_controls(self, chart_data: Dict) -> None:
        """Render chart control panel"""
        with st.expander("📊 Chart Controls"):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📸 Save Chart", key=f"{self.config.id}_save"):
                    self.trigger_event(InteractionEvent.CLICK, {"action": "save_chart"})

            with col2:
                if st.button("🔄 Refresh Data", key=f"{self.config.id}_refresh"):
                    self.clear_cache()
                    self.trigger_event(InteractionEvent.REFRESH)
                    st.rerun()

            with col3:
                chart_theme = st.selectbox(
                    "Theme",
                    ["plotly", "plotly_white", "plotly_dark", "ggplot2"],
                    key=f"{self.config.id}_theme"
                )

                if st.session_state.get(f"{self.config.id}_theme") != chart_theme:
                    self.trigger_event(InteractionEvent.CHANGE, {"theme": chart_theme})


class SmartDataTable(AdvancedComponent):
    """
    Advanced data table with sorting, filtering, pagination,
    and real-time data updates
    """

    def render_content(self, data: pd.DataFrame, **kwargs) -> None:
        """Render smart data table with advanced features"""
        if data is None or data.empty:
            st.warning("No data available for table")
            return

        # Apply filters
        filtered_data = self._apply_filters(data, kwargs)

        # Apply sorting
        sorted_data = self._apply_sorting(filtered_data, kwargs)

        # Apply pagination
        paginated_data = self._apply_pagination(sorted_data, kwargs)

        # Render table with styling
        self._render_styled_table(paginated_data, kwargs)

        # Render table controls
        self._render_table_controls(data, kwargs)

    def _apply_filters(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Apply column filters to data"""
        filtered_data = data.copy()

        filters = config.get("filters", {})
        for column, filter_config in filters.items():
            if column in data.columns:
                filter_type = filter_config.get("type", "text")
                filter_value = filter_config.get("value")

                if filter_type == "text" and filter_value:
                    filtered_data = filtered_data[
                        filtered_data[column].astype(str).str.contains(filter_value, case=False, na=False)
                    ]
                elif filter_type == "range" and filter_value:
                    min_val, max_val = filter_value
                    filtered_data = filtered_data[
                        (filtered_data[column] >= min_val) & (filtered_data[column] <= max_val)
                    ]

        return filtered_data

    def _apply_sorting(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Apply sorting to data"""
        sort_config = config.get("sort", {})
        if sort_config:
            column = sort_config.get("column")
            ascending = sort_config.get("ascending", True)

            if column and column in data.columns:
                return data.sort_values(by=column, ascending=ascending)

        return data

    def _apply_pagination(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Apply pagination to data"""
        pagination = config.get("pagination", {})
        if pagination.get("enabled", False):
            page_size = pagination.get("page_size", 25)
            current_page = pagination.get("current_page", 1)

            start_idx = (current_page - 1) * page_size
            end_idx = start_idx + page_size

            return data.iloc[start_idx:end_idx]

        return data

    def _render_styled_table(self, data: pd.DataFrame, config: Dict) -> None:
        """Render table with custom styling"""
        styling = config.get("styling", {})

        if styling:
            styled_df = data.style

            # Apply number formatting
            if "format" in styling:
                for column, format_str in styling["format"].items():
                    if column in data.columns:
                        styled_df = styled_df.format({column: format_str})

            # Apply conditional formatting
            if "conditional" in styling:
                for rule in styling["conditional"]:
                    if rule["type"] == "color_scale":
                        styled_df = styled_df.background_gradient(
                            subset=rule["columns"],
                            cmap=rule.get("colormap", "RdYlGn")
                        )

            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(data, use_container_width=True)

    def _render_table_controls(self, original_data: pd.DataFrame, config: Dict) -> None:
        """Render table control panel"""
        with st.expander("🔧 Table Controls"):
            col1, col2, col3 = st.columns(3)

            with col1:
                # Column filter
                filter_column = st.selectbox(
                    "Filter Column",
                    ["None"] + list(original_data.columns),
                    key=f"{self.config.id}_filter_col"
                )

                if filter_column != "None":
                    filter_value = st.text_input(
                        "Filter Value",
                        key=f"{self.config.id}_filter_val"
                    )

            with col2:
                # Sorting
                sort_column = st.selectbox(
                    "Sort By",
                    ["None"] + list(original_data.columns),
                    key=f"{self.config.id}_sort_col"
                )

                if sort_column != "None":
                    sort_ascending = st.checkbox(
                        "Ascending",
                        value=True,
                        key=f"{self.config.id}_sort_asc"
                    )

            with col3:
                # Export options
                if st.button("📥 Export CSV", key=f"{self.config.id}_export"):
                    csv = original_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{self.config.id}_data.csv",
                        mime="text/csv"
                    )


def performance_monitor(func):
    """Decorator to monitor component performance"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        end_time = time.time()

        # Log performance metrics
        if hasattr(self, 'metrics'):
            self.metrics.render_time = end_time - start_time

        # Show performance warning if slow
        if end_time - start_time > 2.0:
            st.warning(f"⚠️ Component {self.config.id} took {end_time - start_time:.2f}s to render")

        return result
    return wrapper


# Factory function for creating advanced components
def create_advanced_component(component_type: str, config: ComponentConfig) -> AdvancedComponent:
    """Factory function to create advanced components"""
    components = {
        "interactive_chart": InteractiveChart,
        "smart_table": SmartDataTable,
    }

    component_class = components.get(component_type)
    if not component_class:
        raise ValueError(f"Unknown component type: {component_type}")

    return component_class(config)