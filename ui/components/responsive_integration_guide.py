"""
Responsive Design Integration Guide for Financial Analysis Application

Provides integration examples and testing utilities for implementing
responsive design components in the existing Streamlit application.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import logging

# Import our responsive components
from .responsive_framework import (
    configure_responsive_page,
    responsive_layout,
    accessibility,
    render_dual_view_toggle
)
from .responsive_dashboard_components import responsive_components
from .responsive_navigation import responsive_tabs, responsive_sidebar, configure_responsive_navigation
from .accessibility_features import accessibility_manager, configure_accessibility_features, create_accessibility_controls

logger = logging.getLogger(__name__)

class ResponsiveIntegrationDemo:
    """Demonstrates how to integrate responsive components into existing application."""

    def __init__(self):
        self.setup_responsive_environment()

    def setup_responsive_environment(self):
        """Setup the complete responsive environment."""
        # Configure responsive page settings
        configure_responsive_page(
            page_title="FCF Analysis Tool - Responsive",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Configure navigation
        configure_responsive_navigation()

        # Configure accessibility features
        configure_accessibility_features()

    def demo_responsive_financial_dashboard(self):
        """Demonstrate responsive financial dashboard implementation."""
        st.title("📊 Responsive Financial Analysis Dashboard")

        # Add accessibility controls
        accessibility_controls = create_accessibility_controls()

        # Demo company summary card
        st.markdown("## Company Overview Demo")
        responsive_components.financial_summary_card(
            company_name="Microsoft Corporation",
            ticker="MSFT",
            current_price=335.50,
            currency="$",
            market_cap=2.5e12,
            additional_metrics={
                "P/E Ratio": "28.5",
                "Market Cap": "$2.5T",
                "52W High": "$468.35"
            }
        )

        # Demo responsive navigation
        st.markdown("## Responsive Navigation Demo")
        tab_config = [
            {"label": "FCF Analysis", "icon": "💰", "key": "fcf", "mobile_priority": 10},
            {"label": "DCF Valuation", "icon": "📈", "key": "dcf", "mobile_priority": 9},
            {"label": "DDM Analysis", "icon": "💵", "key": "ddm", "mobile_priority": 8},
            {"label": "P/B Analysis", "icon": "📊", "key": "pb", "mobile_priority": 7},
            {"label": "Watch Lists", "icon": "👀", "key": "watchlist", "mobile_priority": 6},
            {"label": "Reports", "icon": "📋", "key": "reports", "mobile_priority": 5}
        ]

        tabs, selected_key = responsive_tabs.create_responsive_tabs(tab_config)

        if tabs:  # Desktop/tablet view
            with tabs[0]:
                self._demo_fcf_responsive_layout()
            with tabs[1]:
                self._demo_dcf_responsive_layout()
            with tabs[2]:
                st.info("DDM Analysis with responsive components")
            with tabs[3]:
                st.info("P/B Analysis with responsive components")
            with tabs[4]:
                st.info("Watch Lists with responsive components")
            with tabs[5]:
                st.info("Reports with responsive components")
        else:  # Mobile dropdown view
            if selected_key == "fcf":
                self._demo_fcf_responsive_layout()
            elif selected_key == "dcf":
                self._demo_dcf_responsive_layout()
            else:
                st.info(f"Selected: {selected_key}")

    def _demo_fcf_responsive_layout(self):
        """Demo FCF analysis with responsive layout."""
        st.markdown("### 💰 FCF Analysis - Responsive Layout")

        # Sample FCF data
        fcf_data = {
            "FCFE": {
                "values": [1200, 1350, 1180, 1420, 1650],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            },
            "FCFF": {
                "values": [1500, 1680, 1450, 1750, 2100],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            },
            "Levered_FCF": {
                "values": [1100, 1200, 1050, 1300, 1580],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            }
        }

        # Display using responsive components
        responsive_components.fcf_analysis_dashboard(fcf_data, show_detailed=True)

        # Demo responsive dual view toggle
        st.markdown("#### Dual View Toggle Demo")
        view_mode = render_dual_view_toggle(context="fcf_demo")
        st.info(f"Current view mode: {view_mode}")

    def _demo_dcf_responsive_layout(self):
        """Demo DCF analysis with responsive layout."""
        st.markdown("### 📈 DCF Valuation - Responsive Layout")

        # Sample valuation data
        dcf_result = {"fair_value": 385.50, "enterprise_value": 2.1e12}
        ddm_result = {"fair_value": 340.25, "dividend_yield": 0.025}
        pb_result = {"fair_value": 360.75, "book_value": 45.30}

        # Display using responsive components
        responsive_components.valuation_comparison_panel(
            dcf_result=dcf_result,
            ddm_result=ddm_result,
            pb_result=pb_result,
            current_price=335.50
        )

    def demo_responsive_sidebar(self):
        """Demonstrate responsive sidebar controls."""
        st.markdown("## Responsive Sidebar Demo")

        # Demo responsive sidebar controls
        data_source_controls = [
            {
                "type": "selectbox",
                "key": "data_source",
                "label": "Data Source",
                "options": ["Excel Files", "API (Auto)", "yfinance", "Alpha Vantage"],
                "help": "Choose your preferred data source"
            },
            {
                "type": "slider",
                "key": "discount_rate",
                "label": "Discount Rate (%)",
                "min": 5,
                "max": 15,
                "default": 10,
                "step": 0.5,
                "help": "Set the discount rate for DCF calculations"
            }
        ]

        valuation_controls = [
            {
                "type": "number_input",
                "key": "growth_rate",
                "label": "Growth Rate (%)",
                "min": 0.0,
                "max": 50.0,
                "default": 5.0,
                "step": 0.1,
                "help": "Expected long-term growth rate"
            },
            {
                "type": "checkbox",
                "key": "conservative_mode",
                "label": "Conservative Estimates",
                "default": False,
                "help": "Use conservative assumptions in calculations"
            }
        ]

        data_controls = responsive_sidebar.responsive_control_group(
            controls=data_source_controls,
            title="Data Source Settings",
            icon="🔧",
            expanded=True
        )

        valuation_controls_result = responsive_sidebar.responsive_control_group(
            controls=valuation_controls,
            title="Valuation Parameters",
            icon="📊",
            expanded=True
        )

        # Display results
        st.write("**Sidebar Control Values:**")
        st.json({**data_controls, **valuation_controls_result})

    def demo_accessibility_features(self):
        """Demonstrate accessibility features."""
        st.markdown("## Accessibility Features Demo")

        # Demo accessible form
        st.markdown("### Accessible Form Example")

        def ticker_input():
            return st.text_input(
                "Stock Ticker",
                value="MSFT",
                key="accessible_ticker"
            )

        ticker_value = accessibility_manager.create_accessible_form_group(
            label="Stock Ticker Symbol",
            control_func=ticker_input,
            help_text="Enter a valid stock ticker symbol (e.g., MSFT, AAPL)",
            required=True,
            field_id="ticker_input"
        )

        # Demo accessible metrics
        st.markdown("### Accessible Metrics Example")
        accessibility_manager.accessible_metric(
            label="Stock Price",
            value="$335.50",
            delta="+2.5%",
            help_text="Current stock price with daily change",
            trend_description="Price increased by 2.5% today, showing positive momentum"
        )

        # Demo accessible alerts
        st.markdown("### Accessible Alerts Example")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Show Success Alert"):
                accessibility_manager.accessible_alert(
                    "Data loaded successfully!",
                    alert_type="success"
                )

        with col2:
            if st.button("Show Warning Alert"):
                accessibility_manager.accessible_alert(
                    "API rate limit approaching",
                    alert_type="warning"
                )

        with col3:
            if st.button("Show Error Alert"):
                accessibility_manager.accessible_alert(
                    "Failed to fetch data",
                    alert_type="error"
                )

def demo_responsive_design():
    """Main function to demonstrate all responsive design features."""
    # Initialize demo
    demo = ResponsiveIntegrationDemo()

    # Show demo sections
    demo.demo_responsive_financial_dashboard()

    st.markdown("---")

    demo.demo_responsive_sidebar()

    st.markdown("---")

    demo.demo_accessibility_features()

    # Show integration instructions
    st.markdown("---")
    st.markdown("## Integration Instructions")

    with st.expander("📋 How to Integrate into Existing Application", expanded=False):
        st.markdown("""
        ### Step 1: Replace Page Configuration
        Replace the existing `st.set_page_config()` call with:
        ```python
        from ui.components.responsive_framework import configure_responsive_page
        configure_responsive_page()
        ```

        ### Step 2: Update Column Layouts
        Replace fixed `st.columns()` calls with responsive alternatives:
        ```python
        from ui.components.responsive_framework import responsive_layout

        # Instead of: col1, col2 = st.columns([2, 1])
        col1, col2 = responsive_layout.responsive_columns([2, 1])
        ```

        ### Step 3: Add Accessibility Features
        Import and configure accessibility:
        ```python
        from ui.components.accessibility_features import configure_accessibility_features
        configure_accessibility_features()
        ```

        ### Step 4: Update Navigation
        Replace tab creation with responsive navigation:
        ```python
        from ui.components.responsive_navigation import responsive_tabs

        tab_config = [
            {"label": "FCF Analysis", "icon": "💰", "key": "fcf", "mobile_priority": 10},
            # ... more tabs
        ]
        tabs, selected_key = responsive_tabs.create_responsive_tabs(tab_config)
        ```

        ### Step 5: Update Financial Components
        Use responsive financial components:
        ```python
        from ui.components.responsive_dashboard_components import responsive_components

        responsive_components.financial_summary_card(
            company_name=company_name,
            ticker=ticker,
            current_price=price
        )
        ```
        """)

    # Show testing guidelines
    with st.expander("🧪 Testing Guidelines", expanded=False):
        st.markdown("""
        ### Responsive Design Testing

        1. **Desktop Testing (>1024px)**
           - Verify full column layouts work correctly
           - Check all navigation tabs are visible
           - Ensure proper spacing and alignment

        2. **Tablet Testing (768-1024px)**
           - Test column stacking behavior
           - Verify sidebar responsiveness
           - Check touch target sizes

        3. **Mobile Testing (<768px)**
           - Verify single-column stacking
           - Test navigation dropdown functionality
           - Check accessibility features

        ### Accessibility Testing

        1. **Keyboard Navigation**
           - Tab through all interactive elements
           - Verify focus indicators are visible
           - Test skip links functionality

        2. **Screen Reader Testing**
           - Use NVDA, JAWS, or VoiceOver
           - Verify all content is announced
           - Check ARIA labels and descriptions

        3. **Color Contrast**
           - Use tools like WebAIM Contrast Checker
           - Test high contrast mode
           - Verify readability in all conditions

        ### Browser Testing
        - Chrome/Edge (Chromium)
        - Firefox
        - Safari (if available)
        - Mobile browsers (Chrome Mobile, Safari Mobile)
        """)

if __name__ == "__main__":
    demo_responsive_design()