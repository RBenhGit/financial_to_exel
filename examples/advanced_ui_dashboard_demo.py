"""
Advanced UI Components Dashboard Demo
====================================

Comprehensive demonstration of Phase 2B Advanced UI Components Framework
including dashboard orchestration, portfolio comparison, collaboration features,
and advanced visualizations.

Run with: streamlit run examples/advanced_ui_dashboard_demo.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the advanced UI components
from ui.components import (
    create_dashboard_orchestrator,
    create_standard_financial_dashboard,
    create_portfolio_comparison_widget,
    create_collaboration_manager,
    LayoutType,
    ComponentPosition
)

from ui.visualization.advanced_visualizations import (
    create_time_series_chart,
    create_interactive_heatmap,
    create_3d_visualization
)


def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Advanced UI Components Demo",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # App header
    st.title("🚀 Advanced UI Components Framework Demo")
    st.markdown("""
    Welcome to the comprehensive demonstration of our Advanced UI Components Framework.
    This demo showcases sophisticated dashboard orchestration, portfolio analysis,
    real-time collaboration, and advanced visualizations.
    """)

    # Demo mode selection
    demo_mode = st.sidebar.selectbox(
        "Select Demo Mode",
        [
            "🏠 Overview",
            "📊 Standard Financial Dashboard",
            "🎛️ Custom Dashboard Orchestration",
            "📈 Portfolio Comparison Analysis",
            "👥 Real-Time Collaboration",
            "📊 Advanced Visualizations",
            "🔧 Component Showcase"
        ]
    )

    if demo_mode == "🏠 Overview":
        render_overview()
    elif demo_mode == "📊 Standard Financial Dashboard":
        render_standard_dashboard()
    elif demo_mode == "🎛️ Custom Dashboard Orchestration":
        render_custom_orchestration()
    elif demo_mode == "📈 Portfolio Comparison Analysis":
        render_portfolio_comparison()
    elif demo_mode == "👥 Real-Time Collaboration":
        render_collaboration_demo()
    elif demo_mode == "📊 Advanced Visualizations":
        render_visualization_demo()
    elif demo_mode == "🔧 Component Showcase":
        render_component_showcase()


def render_overview():
    """Render overview of the framework"""
    st.header("Framework Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - **Dashboard Orchestration**: Intelligent layout management and component coordination
        - **Portfolio Analysis**: Advanced multi-asset comparison and risk analysis
        - **Real-Time Collaboration**: Live sharing, annotations, and team discussions
        - **Advanced Visualizations**: Interactive charts with technical indicators
        - **Responsive Design**: Mobile-first responsive components
        - **Performance Monitoring**: Built-in performance tracking and optimization
        """)

    with col2:
        st.subheader("🏗️ Architecture")
        st.markdown("""
        ```
        Advanced UI Framework
        ├── 🧩 Core Components
        │   ├── AdvancedComponent (Base)
        │   ├── InteractiveChart
        │   └── SmartDataTable
        ├── 🎛️ Dashboard Orchestration
        │   ├── Layout Management
        │   ├── Component Registration
        │   └── Data Binding
        ├── 📊 Specialized Widgets
        │   ├── Financial Input Panel
        │   ├── Scenario Analyzer
        │   ├── Portfolio Comparison
        │   └── Data Monitor
        └── 👥 Collaboration Features
            ├── Real-Time Sharing
            ├── Annotations System
            └── Activity Tracking
        ```
        """)

    # Framework metrics
    st.subheader("📈 Framework Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Components", "15+", "3 new")
    with col2:
        st.metric("Layout Types", "7", "2 advanced")
    with col3:
        st.metric("Visualization Types", "10+", "5 interactive")
    with col4:
        st.metric("Integration Points", "20+", "seamless")


def render_standard_dashboard():
    """Render standard financial dashboard demo"""
    st.header("📊 Standard Financial Dashboard")
    st.markdown("Pre-configured dashboard with common financial analysis components")

    # Create standard dashboard
    if 'standard_dashboard' not in st.session_state:
        st.session_state.standard_dashboard = create_standard_financial_dashboard("demo_standard")

    dashboard = st.session_state.standard_dashboard

    # Dashboard controls
    with st.sidebar:
        st.subheader("Dashboard Controls")

        layout_type = st.selectbox(
            "Layout Type",
            [layout.value for layout in LayoutType],
            index=1  # Default to TWO_COLUMN
        )

        if st.button("Apply Layout"):
            dashboard.set_layout(LayoutType(layout_type))
            st.success(f"Layout changed to {layout_type}")

        st.subheader("Global Settings")

        selected_ticker = st.text_input("Primary Ticker", value="AAPL")
        analysis_period = st.selectbox("Analysis Period", ["1M", "3M", "6M", "1Y", "2Y"])

        if st.button("Update Global State"):
            dashboard.update_global_state("primary_ticker", selected_ticker)
            dashboard.update_global_state("analysis_period", analysis_period)
            st.success("Global state updated")

    # Render dashboard
    try:
        result = dashboard.render()

        # Show dashboard metrics
        if result:
            st.sidebar.subheader("Dashboard Status")
            st.sidebar.metric("Active Components", result.get("active_components", 0))
            st.sidebar.metric("Session ID", result.get("dashboard_state", {}).get("session_id", "N/A")[:8] + "...")

    except Exception as e:
        st.error(f"Dashboard rendering error: {str(e)}")
        st.info("This is a demo - some components may require additional setup for full functionality.")


def render_custom_orchestration():
    """Render custom dashboard orchestration demo"""
    st.header("🎛️ Custom Dashboard Orchestration")
    st.markdown("Build your own dashboard with custom component arrangement")

    # Create custom dashboard
    if 'custom_dashboard' not in st.session_state:
        st.session_state.custom_dashboard = create_dashboard_orchestrator(
            "demo_custom",
            "Custom Financial Dashboard",
            "User-configured dashboard with flexible layout"
        )

    dashboard = st.session_state.custom_dashboard

    # Component configuration
    with st.sidebar:
        st.subheader("Component Management")

        # Available components
        available_components = {
            "Financial Input Panel": "input_panel",
            "Time Series Chart": "time_series",
            "Correlation Heatmap": "heatmap",
            "Scenario Analyzer": "scenario",
            "Data Monitor": "monitor",
            "Portfolio Comparison": "portfolio"
        }

        component_to_add = st.selectbox(
            "Add Component",
            ["Select..."] + list(available_components.keys())
        )

        position = st.selectbox(
            "Position",
            [pos.value for pos in ComponentPosition]
        )

        if st.button("Add Component") and component_to_add != "Select...":
            component_id = available_components[component_to_add]

            # Create component based on type
            if component_id == "input_panel":
                from ui.components.interactive_widgets import create_financial_input_panel
                component = create_financial_input_panel(f"custom_{component_id}")
            elif component_id == "portfolio":
                component = create_portfolio_comparison_widget(f"custom_{component_id}")
            else:
                # For demo, create a mock component
                from ui.components.advanced_framework import ComponentConfig, InteractiveChart
                config = ComponentConfig(
                    id=f"custom_{component_id}",
                    title=component_to_add,
                    description=f"Custom {component_to_add.lower()}"
                )
                component = InteractiveChart(config)

            dashboard.register_component(
                f"custom_{component_id}",
                component,
                ComponentPosition(position)
            )

            st.success(f"Added {component_to_add} to {position}")
            st.rerun()

        # Layout configuration
        st.subheader("Layout Configuration")

        layout_type = st.selectbox(
            "Layout Type",
            [layout.value for layout in LayoutType],
            key="custom_layout"
        )

        if st.button("Apply Layout", key="custom_apply_layout"):
            dashboard.set_layout(LayoutType(layout_type))
            st.success(f"Layout changed to {layout_type}")

        # Show registered components
        st.subheader("Registered Components")
        for comp_id, registration in dashboard.components.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"{comp_id} ({registration.position.value})")
            with col2:
                if st.button("🗑️", key=f"remove_{comp_id}"):
                    del dashboard.components[comp_id]
                    st.rerun()

    # Render custom dashboard
    try:
        if dashboard.components:
            result = dashboard.render()

            # Show component status
            st.sidebar.subheader("Dashboard Status")
            active_components = [comp_id for comp_id, reg in dashboard.components.items() if reg.active]
            st.sidebar.metric("Active Components", len(active_components))

        else:
            st.info("Add components using the sidebar controls to build your custom dashboard")

    except Exception as e:
        st.error(f"Custom dashboard error: {str(e)}")


def render_portfolio_comparison():
    """Render portfolio comparison demo"""
    st.header("📈 Portfolio Comparison Analysis")
    st.markdown("Advanced multi-asset portfolio analysis with risk metrics")

    # Create portfolio widget
    if 'portfolio_widget' not in st.session_state:
        st.session_state.portfolio_widget = create_portfolio_comparison_widget("demo_portfolio")

    widget = st.session_state.portfolio_widget

    # Render portfolio comparison
    try:
        result = widget.render()

        if result and result.assets:
            # Show portfolio summary
            st.sidebar.subheader("Portfolio Summary")
            st.sidebar.metric("Total Assets", len(result.assets))

            total_return = result.portfolio_metrics.get('total_return', 0)
            st.sidebar.metric("Portfolio Return", f"{total_return:.2%}")

            volatility = result.portfolio_metrics.get('volatility', 0)
            st.sidebar.metric("Portfolio Volatility", f"{volatility:.2%}")

            sharpe_ratio = result.portfolio_metrics.get('sharpe_ratio', 0)
            st.sidebar.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

    except Exception as e:
        st.error(f"Portfolio comparison error: {str(e)}")
        st.info("This is a demo - portfolio data is simulated for demonstration purposes.")


def render_collaboration_demo():
    """Render collaboration features demo"""
    st.header("👥 Real-Time Collaboration Demo")
    st.markdown("Experience live collaboration features for team financial analysis")

    # Create collaboration manager
    if 'collaboration_manager' not in st.session_state:
        st.session_state.collaboration_manager = create_collaboration_manager("demo_collab")

    manager = st.session_state.collaboration_manager

    # Render collaboration interface
    try:
        result = manager.render()

        # Show collaboration metrics
        if result:
            st.sidebar.subheader("Collaboration Status")
            st.sidebar.metric("Active Users", result.get("active_users", 0))
            st.sidebar.metric("Annotations", result.get("annotations_count", 0))
            st.sidebar.metric("Comments", result.get("comments_count", 0))
            st.sidebar.metric("Shared Analyses", result.get("shared_analyses_count", 0))

    except Exception as e:
        st.error(f"Collaboration demo error: {str(e)}")
        st.info("This is a demo - collaboration features simulate real-time interaction.")


def render_visualization_demo():
    """Render advanced visualizations demo"""
    st.header("📊 Advanced Visualizations Demo")
    st.markdown("Showcase of sophisticated interactive charts and visualizations")

    # Generate sample data
    @st.cache_data
    def generate_sample_data():
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)

        data = pd.DataFrame({
            'date': dates,
            'price': 100 + np.cumsum(np.random.randn(len(dates)) * 0.02),
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'moving_avg_20': np.nan,
            'moving_avg_50': np.nan
        })

        # Calculate moving averages
        data['moving_avg_20'] = data['price'].rolling(window=20).mean()
        data['moving_avg_50'] = data['price'].rolling(window=50).mean()

        return data

    sample_data = generate_sample_data()

    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["📈 Time Series", "🔥 Heatmap", "🌐 3D Visualization"])

    with tab1:
        st.subheader("Advanced Time Series Chart")

        # Create time series chart
        time_series_chart = create_time_series_chart("demo_timeseries")

        chart_config = {
            "type": "multi_line",
            "date_column": "date",
            "value_columns": ["price", "moving_avg_20", "moving_avg_50"],
            "show_trends": True,
            "moving_averages": [20, 50],
            "show_range_selector": True,
            "title": "Stock Price with Technical Indicators"
        }

        try:
            fig = time_series_chart.render_content(sample_data, chart_config)
            if fig:
                st.success("✅ Time series chart rendered successfully")
        except Exception as e:
            st.error(f"Time series chart error: {str(e)}")

    with tab2:
        st.subheader("Interactive Correlation Heatmap")

        # Generate correlation data
        correlation_data = pd.DataFrame({
            'AAPL': np.random.randn(100),
            'MSFT': np.random.randn(100),
            'GOOGL': np.random.randn(100),
            'AMZN': np.random.randn(100),
            'TSLA': np.random.randn(100)
        })

        # Add some correlation
        correlation_data['MSFT'] += 0.3 * correlation_data['AAPL']
        correlation_data['GOOGL'] += 0.2 * correlation_data['AAPL']

        heatmap = create_interactive_heatmap("demo_heatmap")

        heatmap_config = {
            "correlation": True,
            "cluster": False,
            "show_significance": False,
            "title": "Asset Correlation Matrix"
        }

        try:
            fig = heatmap.render_content(correlation_data, heatmap_config)
            if fig:
                st.success("✅ Heatmap rendered successfully")
        except Exception as e:
            st.error(f"Heatmap error: {str(e)}")

    with tab3:
        st.subheader("Multi-Dimensional 3D Visualization")

        # Generate 3D data
        np.random.seed(42)
        viz_3d_data = pd.DataFrame({
            'pe_ratio': np.random.uniform(10, 30, 50),
            'debt_ratio': np.random.uniform(0.1, 0.8, 50),
            'roe': np.random.uniform(5, 25, 50),
            'market_cap': np.random.uniform(1e9, 1e12, 50),
            'revenue': np.random.uniform(1e6, 1e9, 50)
        })

        viz_3d = create_3d_visualization("demo_3d")

        viz_config = {
            "chart_type": "scatter",
            "x_column": "pe_ratio",
            "y_column": "debt_ratio",
            "z_column": "roe",
            "color_column": "market_cap",
            "size_column": "revenue",
            "title": "Financial Metrics 3D Analysis"
        }

        try:
            fig = viz_3d.render_content(viz_3d_data, viz_config)
            if fig:
                st.success("✅ 3D visualization rendered successfully")
        except Exception as e:
            st.error(f"3D visualization error: {str(e)}")


def render_component_showcase():
    """Render individual component showcase"""
    st.header("🔧 Component Showcase")
    st.markdown("Detailed exploration of individual framework components")

    component_type = st.selectbox(
        "Select Component to Showcase",
        [
            "🎛️ Dashboard Orchestrator",
            "📝 Financial Input Panel",
            "📊 Interactive Chart",
            "📋 Smart Data Table",
            "🎯 Scenario Analyzer",
            "📡 Data Monitor"
        ]
    )

    if component_type == "🎛️ Dashboard Orchestrator":
        showcase_dashboard_orchestrator()
    elif component_type == "📝 Financial Input Panel":
        showcase_input_panel()
    elif component_type == "📊 Interactive Chart":
        showcase_interactive_chart()
    elif component_type == "📋 Smart Data Table":
        showcase_smart_table()
    elif component_type == "🎯 Scenario Analyzer":
        showcase_scenario_analyzer()
    elif component_type == "📡 Data Monitor":
        showcase_data_monitor()


def showcase_dashboard_orchestrator():
    """Showcase dashboard orchestrator features"""
    st.subheader("Dashboard Orchestrator Features")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Key Features:**
        - Multi-layout support (Grid, Tabs, Columns)
        - Component registration and management
        - Data binding between components
        - Global state management
        - Theme customization
        - Export functionality
        """)

    with col2:
        st.markdown("""
        **Layout Types:**
        - Single Column
        - Two Column
        - Three Column
        - Grid Layout
        - Tabbed Layout
        - Accordion Layout
        """)

    # Configuration example
    st.subheader("Configuration Example")
    st.code("""
    # Create dashboard orchestrator
    dashboard = create_dashboard_orchestrator(
        "my_dashboard",
        "Financial Analysis Dashboard",
        "Advanced financial analysis with multiple components"
    )

    # Register components
    input_panel = create_financial_input_panel("inputs")
    dashboard.register_component("inputs", input_panel, ComponentPosition.SIDEBAR)

    # Configure layout
    dashboard.set_layout(LayoutType.TWO_COLUMN)

    # Set up data binding
    dashboard.bind_data("inputs", "charts", "ticker", "symbol")

    # Render dashboard
    result = dashboard.render()
    """, language="python")


def showcase_input_panel():
    """Showcase financial input panel"""
    st.subheader("Financial Input Panel")

    from ui.components.interactive_widgets import create_financial_input_panel

    # Create input panel
    input_panel = create_financial_input_panel("showcase_input")

    try:
        result = input_panel.render()

        if result:
            st.subheader("Input Data Captured")
            st.json(result)

    except Exception as e:
        st.error(f"Input panel error: {str(e)}")


def showcase_interactive_chart():
    """Showcase interactive chart component"""
    st.subheader("Interactive Chart Component")

    # Generate sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'date': dates,
        'price': 100 + np.cumsum(np.random.randn(100) * 0.02),
        'volume': np.random.randint(1000, 10000, 100)
    })

    from ui.components.advanced_framework import InteractiveChart, ComponentConfig

    config = ComponentConfig(
        id="showcase_chart",
        title="Interactive Financial Chart",
        description="Demonstration of interactive chart capabilities"
    )

    chart = InteractiveChart(config)

    chart_config = {
        "type": "multi_line",
        "data": data,
        "layout": {
            "title": "Sample Financial Data",
            "xaxis_title": "Date",
            "yaxis_title": "Price"
        },
        "show_range_selector": True
    }

    try:
        fig = chart.render_content(chart_config)
        if fig:
            st.success("✅ Interactive chart rendered")
    except Exception as e:
        st.error(f"Chart error: {str(e)}")


def showcase_smart_table():
    """Showcase smart data table"""
    st.subheader("Smart Data Table Component")

    # Generate sample data
    sample_data = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
        'Price': [150.25, 305.50, 2650.75, 3200.00, 850.30],
        'Change': [2.50, -5.25, 15.80, -12.50, 25.75],
        'Volume': [45000000, 25000000, 1500000, 3500000, 18000000],
        'Market Cap': [2.4e12, 2.2e12, 1.8e12, 1.6e12, 8e11]
    })

    from ui.components.advanced_framework import SmartDataTable, ComponentConfig

    config = ComponentConfig(
        id="showcase_table",
        title="Smart Financial Data Table",
        description="Advanced table with filtering and sorting"
    )

    table = SmartDataTable(config)

    table_config = {
        "styling": {
            "format": {
                "Price": "${:.2f}",
                "Change": "{:+.2f}",
                "Volume": "{:,}",
                "Market Cap": "${:.2e}"
            }
        },
        "pagination": {"enabled": False}
    }

    try:
        table.render_content(sample_data, **table_config)
        st.success("✅ Smart table rendered")
    except Exception as e:
        st.error(f"Table error: {str(e)}")


def showcase_scenario_analyzer():
    """Showcase scenario analyzer"""
    st.subheader("Interactive Scenario Analyzer")
    st.info("This component provides sophisticated scenario analysis with parameter adjustment capabilities")


def showcase_data_monitor():
    """Showcase data monitor"""
    st.subheader("Real-Time Data Monitor")
    st.info("This component provides real-time data monitoring with alerts and status tracking")


if __name__ == "__main__":
    main()