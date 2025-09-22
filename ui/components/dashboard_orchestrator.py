"""
Dashboard Orchestrator
======================

Advanced dashboard orchestration component that manages multiple UI components,
handles inter-component communication, and provides sophisticated layout management
for complex financial analysis dashboards.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid

from .advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState,
    InteractionEvent, performance_monitor
)
from .interactive_widgets import (
    FinancialInputPanel, InteractiveScenarioAnalyzer, RealTimeDataMonitor
)
from ..visualization.advanced_visualizations import (
    AdvancedTimeSeriesChart, InteractiveHeatmap, Multi3DVisualization
)


class LayoutType(Enum):
    """Dashboard layout types"""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    GRID = "grid"
    TABS = "tabs"
    ACCORDION = "accordion"
    FLOATING = "floating"


class ComponentPosition(Enum):
    """Component positioning options"""
    MAIN = "main"
    SIDEBAR = "sidebar"
    HEADER = "header"
    FOOTER = "footer"
    MODAL = "modal"
    FLOATING = "floating"


@dataclass
class ComponentRegistration:
    """Registration information for dashboard components"""
    component: AdvancedComponent
    position: ComponentPosition
    layout_config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    data_bindings: Dict[str, str] = field(default_factory=dict)
    event_subscriptions: List[str] = field(default_factory=list)
    active: bool = True


@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    layout_type: LayoutType
    columns: List[int] = field(default_factory=lambda: [1])
    spacing: float = 0.02
    padding: Dict[str, int] = field(default_factory=lambda: {"top": 10, "bottom": 10, "left": 10, "right": 10})
    responsive: bool = True
    breakpoints: Dict[str, int] = field(default_factory=lambda: {"mobile": 768, "tablet": 1024, "desktop": 1440})


@dataclass
class DashboardTheme:
    """Dashboard theming configuration"""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    background_color: str = "#ffffff"
    text_color: str = "#000000"
    sidebar_color: str = "#f0f2f6"
    header_color: str = "#ffffff"
    border_radius: str = "8px"
    shadow: str = "0 2px 4px rgba(0,0,0,0.1)"
    font_family: str = "Arial, sans-serif"


class DashboardOrchestrator(AdvancedComponent):
    """
    Advanced dashboard orchestrator that manages complex multi-component layouts,
    handles inter-component communication, and provides sophisticated state management
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.components: Dict[str, ComponentRegistration] = {}
        self.layout = DashboardLayout(LayoutType.TWO_COLUMN)
        self.theme = DashboardTheme()
        self.global_state = {}
        self.event_bus = {}
        self.data_store = {}

    @performance_monitor
    def render_content(self, data: Dict = None, **kwargs) -> Dict[str, Any]:
        """Render complete dashboard with all registered components"""

        # Initialize dashboard
        self._initialize_dashboard()

        # Apply theme
        self._apply_dashboard_theme()

        # Render header
        self._render_dashboard_header()

        # Render main content based on layout
        content_result = self._render_main_content()

        # Render sidebar components
        self._render_sidebar_components()

        # Render footer
        self._render_dashboard_footer()

        # Handle inter-component communication
        self._process_component_events()

        return {
            "dashboard_state": self.global_state,
            "component_results": content_result,
            "active_components": list(self.components.keys())
        }

    def register_component(self,
                         component_id: str,
                         component: AdvancedComponent,
                         position: ComponentPosition = ComponentPosition.MAIN,
                         layout_config: Dict = None,
                         dependencies: List[str] = None,
                         data_bindings: Dict[str, str] = None) -> None:
        """Register a component with the dashboard"""

        registration = ComponentRegistration(
            component=component,
            position=position,
            layout_config=layout_config or {},
            dependencies=dependencies or [],
            data_bindings=data_bindings or {},
            active=True
        )

        self.components[component_id] = registration

        # Set up event handling
        self._setup_component_events(component_id, component)

        # Initialize component data bindings
        self._initialize_data_bindings(component_id, registration)

    def set_layout(self, layout_type: LayoutType, **layout_kwargs) -> None:
        """Configure dashboard layout"""
        self.layout = DashboardLayout(layout_type=layout_type, **layout_kwargs)

    def set_theme(self, theme: DashboardTheme) -> None:
        """Set dashboard theme"""
        self.theme = theme

    def update_global_state(self, key: str, value: Any) -> None:
        """Update global dashboard state"""
        self.global_state[key] = value
        self._notify_state_change(key, value)

    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get value from global dashboard state"""
        return self.global_state.get(key, default)

    def bind_data(self, source_component: str, target_component: str,
                  source_key: str, target_key: str) -> None:
        """Create data binding between components"""
        if target_component in self.components:
            self.components[target_component].data_bindings[target_key] = f"{source_component}.{source_key}"

    def _initialize_dashboard(self):
        """Initialize dashboard state and configuration"""
        if "dashboard_initialized" not in st.session_state:
            st.session_state.dashboard_initialized = True
            st.session_state.dashboard_id = str(uuid.uuid4())
            st.session_state.component_states = {}

    def _apply_dashboard_theme(self):
        """Apply custom CSS theme to dashboard"""
        theme_css = f"""
        <style>
        .main .block-container {{
            background-color: {self.theme.background_color};
            color: {self.theme.text_color};
            font-family: {self.theme.font_family};
            padding-top: {self.layout.padding['top']}px;
            padding-bottom: {self.layout.padding['bottom']}px;
            padding-left: {self.layout.padding['left']}px;
            padding-right: {self.layout.padding['right']}px;
        }}

        .sidebar .sidebar-content {{
            background-color: {self.theme.sidebar_color};
            border-radius: {self.theme.border_radius};
            box-shadow: {self.theme.shadow};
        }}

        .dashboard-header {{
            background-color: {self.theme.header_color};
            border-bottom: 1px solid #e0e0e0;
            padding: 1rem;
            margin-bottom: 1rem;
        }}

        .component-card {{
            background-color: {self.theme.background_color};
            border-radius: {self.theme.border_radius};
            box-shadow: {self.theme.shadow};
            padding: 1rem;
            margin: 0.5rem 0;
        }}

        .dashboard-footer {{
            border-top: 1px solid #e0e0e0;
            padding: 1rem;
            margin-top: 2rem;
            text-align: center;
            color: #666;
        }}
        </style>
        """
        st.markdown(theme_css, unsafe_allow_html=True)

    def _render_dashboard_header(self):
        """Render dashboard header with title and controls"""
        header_components = [comp_id for comp_id, reg in self.components.items()
                           if reg.position == ComponentPosition.HEADER and reg.active]

        if header_components or self.config.title:
            st.markdown('<div class="dashboard-header">', unsafe_allow_html=True)

            if self.config.title:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.title(f"📊 {self.config.title}")
                    if self.config.description:
                        st.caption(self.config.description)

                with col2:
                    self._render_dashboard_controls()

                with col3:
                    self._render_dashboard_status()

            # Render header components
            for comp_id in header_components:
                self._render_single_component(comp_id)

            st.markdown('</div>', unsafe_allow_html=True)

    def _render_dashboard_controls(self):
        """Render dashboard-level controls"""
        with st.popover("⚙️ Dashboard Settings"):
            st.subheader("Layout Options")

            layout_type = st.selectbox(
                "Layout Type",
                options=[layout.value for layout in LayoutType],
                index=list(LayoutType).index(self.layout.layout_type),
                key=f"{self.config.id}_layout_type"
            )

            if layout_type != self.layout.layout_type.value:
                self.layout.layout_type = LayoutType(layout_type)
                st.rerun()

            st.subheader("Theme Options")
            theme_preset = st.selectbox(
                "Theme Preset",
                options=["Default", "Dark", "High Contrast", "Minimal"],
                key=f"{self.config.id}_theme_preset"
            )

            if st.button("Apply Theme", key=f"{self.config.id}_apply_theme"):
                self._apply_theme_preset(theme_preset)
                st.rerun()

            st.subheader("Export Options")
            if st.button("📸 Export Dashboard", key=f"{self.config.id}_export"):
                self._export_dashboard()

    def _render_dashboard_status(self):
        """Render dashboard status indicators"""
        active_components = sum(1 for reg in self.components.values() if reg.active)
        total_components = len(self.components)

        st.metric(
            "Active Components",
            active_components,
            delta=f"{total_components - active_components} inactive"
        )

    def _render_main_content(self) -> Dict[str, Any]:
        """Render main content area based on layout configuration"""
        main_components = [comp_id for comp_id, reg in self.components.items()
                          if reg.position == ComponentPosition.MAIN and reg.active]

        if not main_components:
            st.info("No active components configured for main content area")
            return {}

        results = {}

        if self.layout.layout_type == LayoutType.SINGLE_COLUMN:
            results = self._render_single_column_layout(main_components)
        elif self.layout.layout_type == LayoutType.TWO_COLUMN:
            results = self._render_two_column_layout(main_components)
        elif self.layout.layout_type == LayoutType.THREE_COLUMN:
            results = self._render_three_column_layout(main_components)
        elif self.layout.layout_type == LayoutType.GRID:
            results = self._render_grid_layout(main_components)
        elif self.layout.layout_type == LayoutType.TABS:
            results = self._render_tabs_layout(main_components)
        elif self.layout.layout_type == LayoutType.ACCORDION:
            results = self._render_accordion_layout(main_components)
        else:
            results = self._render_single_column_layout(main_components)

        return results

    def _render_single_column_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in single column layout"""
        results = {}
        for comp_id in component_ids:
            st.markdown('<div class="component-card">', unsafe_allow_html=True)
            results[comp_id] = self._render_single_component(comp_id)
            st.markdown('</div>', unsafe_allow_html=True)
        return results

    def _render_two_column_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in two column layout"""
        results = {}
        col1, col2 = st.columns([1, 1])

        for i, comp_id in enumerate(component_ids):
            column = col1 if i % 2 == 0 else col2
            with column:
                st.markdown('<div class="component-card">', unsafe_allow_html=True)
                results[comp_id] = self._render_single_component(comp_id)
                st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_three_column_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in three column layout"""
        results = {}
        col1, col2, col3 = st.columns([1, 1, 1])
        columns = [col1, col2, col3]

        for i, comp_id in enumerate(component_ids):
            column = columns[i % 3]
            with column:
                st.markdown('<div class="component-card">', unsafe_allow_html=True)
                results[comp_id] = self._render_single_component(comp_id)
                st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_grid_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in grid layout"""
        results = {}
        grid_cols = self.layout.columns if self.layout.columns else [1, 1]

        # Calculate grid dimensions
        cols_per_row = len(grid_cols)
        rows_needed = (len(component_ids) + cols_per_row - 1) // cols_per_row

        for row in range(rows_needed):
            columns = st.columns(grid_cols)
            for col_idx in range(cols_per_row):
                comp_idx = row * cols_per_row + col_idx
                if comp_idx < len(component_ids):
                    comp_id = component_ids[comp_idx]
                    with columns[col_idx]:
                        st.markdown('<div class="component-card">', unsafe_allow_html=True)
                        results[comp_id] = self._render_single_component(comp_id)
                        st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_tabs_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in tabbed layout"""
        results = {}

        if component_ids:
            tab_names = [self.components[comp_id].component.config.title for comp_id in component_ids]
            tabs = st.tabs(tab_names)

            for i, (comp_id, tab) in enumerate(zip(component_ids, tabs)):
                with tab:
                    st.markdown('<div class="component-card">', unsafe_allow_html=True)
                    results[comp_id] = self._render_single_component(comp_id)
                    st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_accordion_layout(self, component_ids: List[str]) -> Dict[str, Any]:
        """Render components in accordion layout"""
        results = {}

        for comp_id in component_ids:
            component_title = self.components[comp_id].component.config.title
            with st.expander(f"📊 {component_title}", expanded=True):
                st.markdown('<div class="component-card">', unsafe_allow_html=True)
                results[comp_id] = self._render_single_component(comp_id)
                st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_sidebar_components(self):
        """Render components in sidebar"""
        sidebar_components = [comp_id for comp_id, reg in self.components.items()
                            if reg.position == ComponentPosition.SIDEBAR and reg.active]

        if sidebar_components:
            with st.sidebar:
                st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
                for comp_id in sidebar_components:
                    self._render_single_component(comp_id)
                st.markdown('</div>', unsafe_allow_html=True)

    def _render_dashboard_footer(self):
        """Render dashboard footer"""
        footer_components = [comp_id for comp_id, reg in self.components.items()
                           if reg.position == ComponentPosition.FOOTER and reg.active]

        if footer_components or True:  # Always show footer for dashboard info
            st.markdown('<div class="dashboard-footer">', unsafe_allow_html=True)

            for comp_id in footer_components:
                self._render_single_component(comp_id)

            # Dashboard info
            st.markdown(f"""
            **Dashboard ID:** {st.session_state.get('dashboard_id', 'Unknown')} |
            **Components:** {len(self.components)} |
            **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """)

            st.markdown('</div>', unsafe_allow_html=True)

    def _render_single_component(self, component_id: str) -> Any:
        """Render a single registered component"""
        if component_id not in self.components:
            st.error(f"Component '{component_id}' not found")
            return None

        registration = self.components[component_id]
        component = registration.component

        try:
            # Prepare component data based on bindings
            component_data = self._prepare_component_data(component_id, registration)

            # Render component
            result = component.render(data=component_data, **registration.layout_config)

            # Store result for data bindings
            self.data_store[component_id] = result

            # Trigger component events
            self._trigger_component_events(component_id, result)

            return result

        except Exception as e:
            st.error(f"Error rendering component '{component_id}': {str(e)}")
            return None

    def _prepare_component_data(self, component_id: str, registration: ComponentRegistration) -> Dict:
        """Prepare data for component based on data bindings"""
        component_data = {}

        for target_key, binding in registration.data_bindings.items():
            if '.' in binding:
                source_component, source_key = binding.split('.', 1)
                if source_component in self.data_store:
                    source_data = self.data_store[source_component]
                    if isinstance(source_data, dict) and source_key in source_data:
                        component_data[target_key] = source_data[source_key]

        return component_data

    def _setup_component_events(self, component_id: str, component: AdvancedComponent):
        """Set up event handling for component"""
        def event_handler(event: InteractionEvent, data: Any = None):
            self._handle_component_event(component_id, event, data)

        # Register event handler for all interaction events
        for event_type in InteractionEvent:
            component.add_event_handler(event_type, event_handler)

    def _handle_component_event(self, component_id: str, event: InteractionEvent, data: Any):
        """Handle events from components"""
        event_key = f"{component_id}.{event.value}"

        # Store event in event bus
        if event_key not in self.event_bus:
            self.event_bus[event_key] = []

        self.event_bus[event_key].append({
            "timestamp": datetime.now(),
            "data": data
        })

        # Process event-based data flow
        self._process_event_data_flow(component_id, event, data)

    def _process_event_data_flow(self, source_component: str, event: InteractionEvent, data: Any):
        """Process data flow between components based on events"""
        # Find components that depend on this event
        for comp_id, registration in self.components.items():
            if f"{source_component}.{event.value}" in registration.event_subscriptions:
                # Update component data or trigger refresh
                if hasattr(registration.component, 'trigger_event'):
                    registration.component.trigger_event(event, data)

    def _process_component_events(self):
        """Process inter-component communication events"""
        # This is called after all components are rendered to handle
        # any cross-component updates that need to happen
        pass

    def _initialize_data_bindings(self, component_id: str, registration: ComponentRegistration):
        """Initialize data bindings for component"""
        # Set up initial data bindings if needed
        pass

    def _notify_state_change(self, key: str, value: Any):
        """Notify components of global state changes"""
        for comp_id, registration in self.components.items():
            if hasattr(registration.component, 'on_state_change'):
                registration.component.on_state_change(key, value)

    def _apply_theme_preset(self, preset: str):
        """Apply a theme preset"""
        if preset == "Dark":
            self.theme = DashboardTheme(
                primary_color="#3498db",
                background_color="#2c3e50",
                text_color="#ecf0f1",
                sidebar_color="#34495e"
            )
        elif preset == "High Contrast":
            self.theme = DashboardTheme(
                primary_color="#000000",
                background_color="#ffffff",
                text_color="#000000",
                sidebar_color="#f8f9fa"
            )
        elif preset == "Minimal":
            self.theme = DashboardTheme(
                primary_color="#6c757d",
                background_color="#ffffff",
                text_color="#495057",
                sidebar_color="#f8f9fa"
            )

    def _export_dashboard(self):
        """Export dashboard configuration and state"""
        export_data = {
            "dashboard_config": {
                "id": self.config.id,
                "title": self.config.title,
                "description": self.config.description
            },
            "layout": {
                "layout_type": self.layout.layout_type.value,
                "columns": self.layout.columns,
                "spacing": self.layout.spacing
            },
            "components": {
                comp_id: {
                    "type": type(reg.component).__name__,
                    "position": reg.position.value,
                    "layout_config": reg.layout_config,
                    "active": reg.active
                }
                for comp_id, reg in self.components.items()
            },
            "theme": {
                "primary_color": self.theme.primary_color,
                "background_color": self.theme.background_color,
                "text_color": self.theme.text_color
            },
            "export_timestamp": datetime.now().isoformat()
        }

        export_json = json.dumps(export_data, indent=2)
        st.download_button(
            label="📥 Download Dashboard Config",
            data=export_json,
            file_name=f"dashboard_config_{self.config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


# Factory function for creating dashboard orchestrator
def create_dashboard_orchestrator(dashboard_id: str, title: str = None, description: str = None) -> DashboardOrchestrator:
    """Create dashboard orchestrator with configuration"""
    config = ComponentConfig(
        id=dashboard_id,
        title=title or "Financial Analysis Dashboard",
        description=description or "Advanced multi-component financial analysis dashboard",
        cache_enabled=True,
        auto_refresh=False
    )
    return DashboardOrchestrator(config)


# Convenience functions for quick dashboard setup
def create_standard_financial_dashboard(dashboard_id: str = "financial_dashboard") -> DashboardOrchestrator:
    """Create a standard financial analysis dashboard with common components"""
    dashboard = create_dashboard_orchestrator(
        dashboard_id,
        "Financial Analysis Dashboard",
        "Comprehensive financial analysis with DCF, scenario analysis, and real-time monitoring"
    )

    # Register standard components
    from .interactive_widgets import create_financial_input_panel, create_scenario_analyzer, create_data_monitor
    from ..visualization.advanced_visualizations import create_time_series_chart, create_interactive_heatmap

    # Input panel in sidebar
    input_panel = create_financial_input_panel("financial_inputs")
    dashboard.register_component("input_panel", input_panel, ComponentPosition.SIDEBAR)

    # Main charts in main area
    time_series = create_time_series_chart("price_chart")
    dashboard.register_component("time_series", time_series, ComponentPosition.MAIN)

    heatmap = create_interactive_heatmap("correlation_heatmap")
    dashboard.register_component("heatmap", heatmap, ComponentPosition.MAIN)

    # Scenario analyzer in main area
    scenario_analyzer = create_scenario_analyzer("scenario_analysis")
    dashboard.register_component("scenario_analyzer", scenario_analyzer, ComponentPosition.MAIN)

    # Data monitor in main area
    data_monitor = create_data_monitor("data_monitor")
    dashboard.register_component("data_monitor", data_monitor, ComponentPosition.MAIN)

    # Set up data bindings
    dashboard.bind_data("input_panel", "time_series", "ticker", "ticker")
    dashboard.bind_data("input_panel", "scenario_analyzer", "discount_rate", "base_discount_rate")

    return dashboard