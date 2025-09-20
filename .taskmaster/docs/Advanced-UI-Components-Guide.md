# Advanced UI Components - Developer Guide

## Introduction

The Advanced UI Components Framework provides sophisticated user interface components with reactive state management, performance monitoring, and advanced user interactions specifically designed for financial analysis dashboards.

## Architecture Overview

### Core Components

The framework is built around several key classes:

- **AdvancedComponent**: Base class for all advanced UI components
- **ComponentConfig**: Configuration system for component behavior
- **ComponentMetrics**: Performance and usage tracking
- **EventHandler**: Sophisticated event handling system
- **ComponentState**: Lifecycle state management

## Getting Started

### Basic Component Setup

```python
from ui.components.advanced_framework import AdvancedComponent, ComponentConfig, ComponentState
import streamlit as st

# Create component configuration
config = ComponentConfig(
    id="dcf_analyzer",
    title="DCF Analysis Dashboard",
    description="Interactive DCF valuation with Monte Carlo simulation",
    cache_enabled=True,
    auto_refresh=False,
    animation_enabled=True,
    responsive=True,
    theme="financial"
)

# Create custom component
class DCFAnalysisComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        st.subheader(self.config.title)

        # Component-specific rendering logic
        if data:
            self._render_dcf_results(data)
        else:
            st.info("No analysis data available")

    def _render_dcf_results(self, data):
        # Render DCF analysis results
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("DCF Value", f"${data.get('dcf_value', 0):.2f}")
        with col2:
            st.metric("Current Price", f"${data.get('current_price', 0):.2f}")
        with col3:
            upside = data.get('upside', 0)
            st.metric("Upside", f"{upside:.1f}%", delta=f"{upside:.1f}%")

# Initialize and use component
dcf_component = DCFAnalysisComponent(config)
dcf_component.render(analysis_data)
```

### Component Lifecycle Management

Components have sophisticated lifecycle management:

```python
# Component states
ComponentState.INITIALIZING  # Component being initialized
ComponentState.READY        # Ready for user interaction
ComponentState.LOADING      # Loading data or processing
ComponentState.ERROR        # Error state with fallback
ComponentState.UPDATING     # Updating with new data

# Lifecycle hooks
class MyComponent(AdvancedComponent):
    def on_initialize(self):
        """Called when component initializes"""
        st.info("Component initializing...")

    def on_ready(self):
        """Called when component is ready"""
        self.metrics.render_count += 1

    def on_error(self, error):
        """Called when component encounters error"""
        st.error(f"Component error: {error}")
        return self.config.error_fallback

    def on_update(self, new_data):
        """Called when component data updates"""
        self.state = ComponentState.UPDATING
        # Process new data
        self.state = ComponentState.READY
```

## Performance Monitoring

### Metrics Collection

All components automatically collect performance metrics:

```python
# Access component metrics
metrics = component.metrics

print(f"Render time: {metrics.render_time:.2f}s")
print(f"Render count: {metrics.render_count}")
print(f"User interactions: {metrics.user_interactions}")
print(f"Cache hit rate: {metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses):.2%}")

# Display metrics in development mode
if st.checkbox("Show Performance Metrics", value=False):
    st.json({
        "render_time": metrics.render_time,
        "render_count": metrics.render_count,
        "error_count": metrics.error_count,
        "cache_hits": metrics.cache_hits,
        "cache_misses": metrics.cache_misses
    })
```

### Performance Optimization

```python
class OptimizedComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        # Use caching for expensive operations
        if self.config.cache_enabled:
            cache_key = f"{self.config.id}_{hash(str(data))}"

            if cache_key in self._cached_data:
                self.metrics.cache_hits += 1
                return self._cached_data[cache_key]
            else:
                self.metrics.cache_misses += 1

        # Expensive computation
        result = self._compute_expensive_analysis(data)

        if self.config.cache_enabled:
            self._cached_data[cache_key] = result

        return result

    def _compute_expensive_analysis(self, data):
        """Expensive computation with progress indication"""
        progress_bar = st.progress(0)

        for i in range(100):
            # Simulate expensive computation
            time.sleep(0.01)
            progress_bar.progress((i + 1) / 100)

        return {"computed_value": 42}
```

## Event Handling System

### Registering Event Handlers

```python
from ui.components.advanced_framework import InteractionEvent

class InteractiveComponent(AdvancedComponent):
    def __init__(self, config):
        super().__init__(config)

        # Register event handlers
        self.add_event_handler(InteractionEvent.CLICK, self.on_click)
        self.add_event_handler(InteractionEvent.CHANGE, self.on_change)
        self.add_event_handler(InteractionEvent.REFRESH, self.on_refresh)

    def on_click(self, event, data=None):
        """Handle click events"""
        self.metrics.user_interactions += 1
        st.success(f"Component clicked! Data: {data}")

    def on_change(self, event, data=None):
        """Handle change events"""
        self.emit_event(InteractionEvent.CHANGE, data)
        self.refresh_data()

    def on_refresh(self, event, data=None):
        """Handle refresh events"""
        self.state = ComponentState.LOADING
        # Refresh logic here
        self.state = ComponentState.READY

    def render_content(self, data=None, **kwargs):
        # Interactive elements with event emission
        if st.button("Analyze", key=f"{self.config.id}_analyze"):
            self.emit_event(InteractionEvent.CLICK, {"action": "analyze"})

        # Change detection
        selected_ticker = st.selectbox("Ticker", ["AAPL", "MSFT", "GOOGL"])
        if selected_ticker != st.session_state.get(f"{self.config.id}_ticker"):
            st.session_state[f"{self.config.id}_ticker"] = selected_ticker
            self.emit_event(InteractionEvent.CHANGE, {"ticker": selected_ticker})
```

## Advanced Component Types

### 1. Financial Chart Component

```python
import plotly.graph_objects as go
from ui.components.advanced_framework import AdvancedComponent

class FinancialChartComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        chart_type = kwargs.get('chart_type', 'line')

        if not data:
            st.warning("No data available for chart")
            return

        fig = self._create_chart(data, chart_type)

        # Enhanced chart with interactions
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
            }
        )

    def _create_chart(self, data, chart_type):
        fig = go.Figure()

        if chart_type == 'dcf_waterfall':
            # Create DCF waterfall chart
            values = [data['base_value'], data['growth_impact'],
                     data['margin_impact'], data['risk_adjustment']]
            labels = ['Base Value', 'Growth Impact', 'Margin Impact', 'Risk Adj']

            fig.add_trace(go.Waterfall(
                name="DCF Components",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative"],
                x=labels,
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))

        elif chart_type == 'monte_carlo':
            # Create Monte Carlo distribution
            fig.add_trace(go.Histogram(
                x=data['simulation_results'],
                nbinsx=50,
                name="Valuation Distribution"
            ))

            # Add VaR line
            fig.add_vline(
                x=data['var_5'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"VaR (5%): ${data['var_5']:.2f}"
            )

        fig.update_layout(
            title=self.config.title,
            theme="plotly_white",
            height=400
        )

        return fig
```

### 2. Data Quality Dashboard

```python
class DataQualityComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        if not data:
            return

        st.subheader("Data Quality Assessment")

        # Quality metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            completeness = data.get('completeness', 0)
            st.metric(
                "Completeness",
                f"{completeness:.1%}",
                delta=self._get_quality_delta(completeness, 0.95)
            )

        with col2:
            accuracy = data.get('accuracy', 0)
            st.metric("Accuracy", f"{accuracy:.1%}")

        with col3:
            timeliness = data.get('timeliness', 0)
            st.metric("Timeliness", f"{timeliness:.1%}")

        with col4:
            consistency = data.get('consistency', 0)
            st.metric("Consistency", f"{consistency:.1%}")

        # Quality details
        with st.expander("Quality Details"):
            quality_df = pd.DataFrame({
                'Metric': ['Completeness', 'Accuracy', 'Timeliness', 'Consistency'],
                'Score': [completeness, accuracy, timeliness, consistency],
                'Target': [0.95, 0.98, 0.90, 0.95],
                'Status': [
                    '✅' if completeness >= 0.95 else '⚠️',
                    '✅' if accuracy >= 0.98 else '⚠️',
                    '✅' if timeliness >= 0.90 else '⚠️',
                    '✅' if consistency >= 0.95 else '⚠️'
                ]
            })
            st.dataframe(quality_df, use_container_width=True)

    def _get_quality_delta(self, current, target):
        if current >= target:
            return f"+{(current - target):.1%}"
        else:
            return f"{(current - target):.1%}"
```

### 3. Interactive Parameter Tuner

```python
class ParameterTunerComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        st.subheader("Parameter Tuning")

        # Parameter controls
        parameters = {}

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Growth Parameters**")
            parameters['revenue_growth'] = st.slider(
                "Revenue Growth", -0.20, 0.50, 0.05, 0.01,
                format="%.1%%",
                key=f"{self.config.id}_revenue_growth"
            )
            parameters['terminal_growth'] = st.slider(
                "Terminal Growth", 0.0, 0.10, 0.03, 0.01,
                format="%.1%%",
                key=f"{self.config.id}_terminal_growth"
            )

        with col2:
            st.markdown("**Risk Parameters**")
            parameters['discount_rate'] = st.slider(
                "Discount Rate", 0.05, 0.20, 0.10, 0.01,
                format="%.1%%",
                key=f"{self.config.id}_discount_rate"
            )
            parameters['beta'] = st.slider(
                "Beta", 0.5, 2.0, 1.0, 0.1,
                key=f"{self.config.id}_beta"
            )

        # Real-time calculation
        if any(param != st.session_state.get(f"{self.config.id}_prev_{key}")
               for key, param in parameters.items()):

            # Store previous values
            for key, param in parameters.items():
                st.session_state[f"{self.config.id}_prev_{key}"] = param

            # Emit parameter change event
            self.emit_event(InteractionEvent.CHANGE, {
                'parameters': parameters,
                'source': 'parameter_tuner'
            })

        # Show impact
        if data and 'base_value' in data:
            with st.container():
                st.markdown("**Valuation Impact**")

                base_value = data['base_value']
                current_value = self._calculate_value(parameters)
                impact = (current_value - base_value) / base_value

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Base Value", f"${base_value:.2f}")
                with col2:
                    st.metric("Current Value", f"${current_value:.2f}")
                with col3:
                    st.metric("Impact", f"{impact:.1%}", delta=f"{impact:.1%}")

    def _calculate_value(self, parameters):
        # Simplified valuation calculation
        base_fcf = 100
        growth_years = 5

        # Project cash flows
        current_fcf = base_fcf
        pv_fcf = 0

        for year in range(1, growth_years + 1):
            current_fcf *= (1 + parameters['revenue_growth'])
            pv_fcf += current_fcf / ((1 + parameters['discount_rate']) ** year)

        # Terminal value
        terminal_fcf = current_fcf * (1 + parameters['terminal_growth'])
        terminal_value = terminal_fcf / (parameters['discount_rate'] - parameters['terminal_growth'])
        pv_terminal = terminal_value / ((1 + parameters['discount_rate']) ** growth_years)

        return pv_fcf + pv_terminal
```

## Responsive Design

### Adaptive Layouts

```python
class ResponsiveComponent(AdvancedComponent):
    def render_content(self, data=None, **kwargs):
        # Detect screen size (simplified)
        viewport_width = st.sidebar.slider("Viewport Width (debug)", 300, 1920, 1200)

        if viewport_width < 768:
            # Mobile layout
            self._render_mobile_layout(data)
        elif viewport_width < 1024:
            # Tablet layout
            self._render_tablet_layout(data)
        else:
            # Desktop layout
            self._render_desktop_layout(data)

    def _render_mobile_layout(self, data):
        st.markdown("📱 Mobile Layout")
        # Single column layout
        if data:
            for metric_name, value in data.items():
                st.metric(metric_name, f"${value:.2f}")

    def _render_tablet_layout(self, data):
        st.markdown("📱 Tablet Layout")
        # Two column layout
        if data:
            col1, col2 = st.columns(2)
            items = list(data.items())

            for i, (metric_name, value) in enumerate(items):
                col = col1 if i % 2 == 0 else col2
                with col:
                    st.metric(metric_name, f"${value:.2f}")

    def _render_desktop_layout(self, data):
        st.markdown("🖥️ Desktop Layout")
        # Three column layout
        if data:
            cols = st.columns(3)
            items = list(data.items())

            for i, (metric_name, value) in enumerate(items):
                col = cols[i % 3]
                with col:
                    st.metric(metric_name, f"${value:.2f}")
```

## Component Composition

### Building Complex Dashboards

```python
class ComprehensiveDashboard(AdvancedComponent):
    def __init__(self, config):
        super().__init__(config)

        # Initialize sub-components
        self.chart_component = FinancialChartComponent(ComponentConfig(
            id="dashboard_chart",
            title="Financial Analysis Chart"
        ))

        self.parameter_tuner = ParameterTunerComponent(ComponentConfig(
            id="dashboard_tuner",
            title="Parameter Controls"
        ))

        self.data_quality = DataQualityComponent(ComponentConfig(
            id="dashboard_quality",
            title="Data Quality"
        ))

        # Register inter-component event handlers
        self.parameter_tuner.add_event_handler(
            InteractionEvent.CHANGE,
            self._on_parameter_change
        )

    def render_content(self, data=None, **kwargs):
        # Main dashboard layout
        st.title("Comprehensive Financial Analysis")

        # Top row - key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("DCF Value", f"${data.get('dcf_value', 0):.2f}")
        with col2:
            st.metric("Monte Carlo Mean", f"${data.get('mc_mean', 0):.2f}")
        with col3:
            st.metric("Risk Score", f"{data.get('risk_score', 0):.1f}/10")

        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["Analysis", "Parameters", "Data Quality", "Export"])

        with tab1:
            self.chart_component.render(data, chart_type="dcf_waterfall")

        with tab2:
            self.parameter_tuner.render(data)

        with tab3:
            self.data_quality.render(data.get('quality_metrics'))

        with tab4:
            self._render_export_options(data)

    def _on_parameter_change(self, event, data):
        """Handle parameter changes from tuner component"""
        st.session_state['dashboard_parameters'] = data['parameters']
        st.rerun()

    def _render_export_options(self, data):
        st.subheader("Export Options")

        export_format = st.selectbox("Format", ["PDF", "Excel", "JSON", "CSV"])
        include_charts = st.checkbox("Include Charts", value=True)
        include_data = st.checkbox("Include Raw Data", value=True)

        if st.button("Generate Export"):
            # Export logic here
            st.success(f"Exported to {export_format}")
```

## Testing Components

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch

class TestAdvancedComponent(unittest.TestCase):
    def setUp(self):
        self.config = ComponentConfig(
            id="test_component",
            title="Test Component"
        )
        self.component = AdvancedComponent(self.config)

    def test_initialization(self):
        self.assertEqual(self.component.state, ComponentState.INITIALIZING)
        self.assertEqual(self.component.config.id, "test_component")
        self.assertEqual(self.component.metrics.render_count, 0)

    def test_event_handling(self):
        handler = Mock()
        self.component.add_event_handler(InteractionEvent.CLICK, handler)

        self.component.emit_event(InteractionEvent.CLICK, {"test": "data"})

        handler.assert_called_once_with(InteractionEvent.CLICK, {"test": "data"})

    @patch('streamlit.metric')
    def test_render_with_data(self, mock_metric):
        data = {"dcf_value": 100.0}

        # Mock render_content method
        self.component.render_content = Mock()

        self.component.render(data)

        self.component.render_content.assert_called_once_with(data)
        self.assertGreater(self.component.metrics.render_count, 0)

if __name__ == '__main__':
    unittest.main()
```

## Best Practices

### 1. Component Design
- Keep components focused on a single responsibility
- Use configuration objects for flexibility
- Implement proper error handling and fallbacks
- Design for reusability across different contexts

### 2. Performance
- Enable caching for expensive operations
- Monitor and optimize render times
- Use lazy loading for heavy components
- Implement proper cleanup for resources

### 3. User Experience
- Provide loading indicators for slow operations
- Implement proper error states with helpful messages
- Use progressive disclosure for complex interfaces
- Ensure responsive design for different screen sizes

### 4. Event Handling
- Use appropriate event types for different interactions
- Implement event delegation for performance
- Provide feedback for user actions
- Handle edge cases gracefully

---

*This guide covers the advanced UI component framework. For specific implementation examples and API details, refer to the source code and additional documentation.*