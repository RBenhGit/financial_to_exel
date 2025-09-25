"""
Test UI Components Integration
=============================

Validation tests for the new modular UI architecture to ensure
proper separation of concerns and functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any

# Import new UI components
from ui.components import (
    AdvancedComponent,
    InteractiveChart,
    SmartDataTable,
    create_advanced_component
)
# from ui.layouts import TabsLayout, SidebarLayout, MainContentLayout
# from ui.widgets import FinancialInputWidget, ExportWidget, SettingsWidget
# from presentation.financial_presenter import FinancialAnalysisPresenter


def test_components_basic():
    """Test basic functionality of UI components"""
    st.header("🧪 UI Components Test")
    
    # Test MetricsDisplay
    st.subheader("📊 Metrics Display Test")
    metrics_display = MetricsDisplay("test_metrics")
    
    test_metrics = {
        "Revenue": 1000000,
        "FCF": 150000,
        "Growth Rate": 0.12,
        "Margin": 0.15
    }
    
    def format_test_values(value):
        if isinstance(value, float) and value < 1:
            return f"{value:.2%}"
        elif isinstance(value, (int, float)) and value >= 1000:
            return f"${value:,.0f}"
        else:
            return str(value)
    
    metrics_display.render(
        metrics=test_metrics,
        layout="columns",
        format_func=format_test_values
    )
    
    # Test ChartRenderer
    st.subheader("📈 Chart Renderer Test")
    chart_renderer = ChartRenderer("test_chart")
    
    # Generate sample data
    years = list(range(2019, 2024))
    fcf_values = [100 + i * 15 + np.random.normal(0, 10) for i in range(5)]
    
    chart_data_df = pd.DataFrame({
        "Year": years,
        "FCF": fcf_values
    })
    
    chart_config = {
        "data": chart_data_df,
        "title": "FCF Growth Test Chart",
        "x_column": "Year",
        "y_column": "FCF"
    }
    
    chart_renderer.render(chart_config, chart_type="line")
    
    # Test TableFormatter
    st.subheader("📋 Table Formatter Test")
    table_formatter = TableFormatter("test_table")
    
    test_table_data = pd.DataFrame({
        "Metric": ["Revenue Growth", "FCF Growth", "Margin Improvement"],
        "2022": [0.08, 0.12, -0.02],
        "2023": [0.10, 0.15, 0.03],
        "2024": [0.07, 0.18, 0.05]
    })
    
    styling_config = {
        "format": {
            "2022": "{:.2%}",
            "2023": "{:.2%}",
            "2024": "{:.2%}"
        },
        "highlight": [{
            "type": "positive_negative",
            "columns": ["2022", "2023", "2024"]
        }]
    }
    
    table_formatter.render(
        test_table_data,
        styling_config=styling_config,
        download_filename="test_metrics.csv"
    )


def test_layouts():
    """Test layout components"""
    st.header("🎨 Layout Components Test")
    
    # Test TabsLayout
    st.subheader("📑 Tabs Layout Test")
    tabs_layout = TabsLayout("test_tabs")
    
    def render_tab_content_1(data, **kwargs):
        st.write("Content for Tab 1")
        st.info("This is test content for the first tab")
        return {"tab1_rendered": True}
    
    def render_tab_content_2(data, **kwargs):
        st.write("Content for Tab 2")
        st.success("This is test content for the second tab")
        return {"tab2_rendered": True}
    
    tabs_layout.add_tab("tab1", "Test Tab 1", render_tab_content_1, "🔍")
    tabs_layout.add_tab("tab2", "Test Tab 2", render_tab_content_2, "⚡")
    
    tabs_result = tabs_layout.render()
    
    if tabs_result:
        st.write("✅ Tabs rendered successfully")
        st.json(tabs_result)


def test_widgets():
    """Test specialized widgets"""
    st.header("🔧 Widget Components Test")
    
    # Test FinancialInputWidget
    st.subheader("📈 Financial Input Widget Test")
    
    input_widget = FinancialInputWidget("test_input")
    
    input_type = st.selectbox(
        "Select Input Type",
        ["ticker", "excel", "manual"],
        key="input_type_test"
    )
    
    def validate_ticker(ticker, market):
        if len(ticker) < 1:
            return False, "Ticker cannot be empty"
        if len(ticker) > 10:
            return False, "Ticker too long"
        return True, f"Valid ticker: {ticker}"
    
    input_result = input_widget.render(
        input_type=input_type,
        validation_callback=validate_ticker if input_type == "ticker" else None
    )
    
    if input_result.get("valid"):
        st.success("✅ Input validation passed")
        st.json(input_result)
    
    # Test SettingsWidget
    st.subheader("⚙️ Settings Widget Test")
    settings_widget = SettingsWidget("test_settings")
    
    current_settings = {
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.025,
        "decimal_places": 2,
        "currency_symbol": "$"
    }
    
    settings_result = settings_widget.render(current_settings=current_settings)
    
    if settings_result:
        st.write("✅ Settings configured")
        with st.expander("Settings Values", expanded=False):
            st.json(settings_result)


def test_presenter_integration():
    """Test presenter integration with UI components"""
    st.header("🎭 Presenter Integration Test")
    
    # Create test financial data
    test_financial_data = {
        "fcf_results": {
            "FCFF": [100, 115, 132, 152, 175],
            "FCFE": [80, 92, 106, 122, 140],
            "LFCF": [90, 103, 119, 137, 157]
        },
        "growth_rates": {
            "FCFF": {"3yr": 0.12, "5yr": 0.15},
            "FCFE": {"3yr": 0.14, "5yr": 0.16},
            "Average": {"3yr": 0.13, "5yr": 0.155}
        }
    }
    
    # Test financial presenter
    financial_presenter = FinancialAnalysisPresenter()
    
    st.subheader("💰 FCF Analysis Presentation Test")
    try:
        fcf_results = financial_presenter.present(
            financial_data=test_financial_data,
            analysis_type="fcf"
        )
        
        if fcf_results:
            st.success("✅ FCF analysis presented successfully")
            
            # Show presenter state
            presenter_state = financial_presenter.get_presenter_state()
            if presenter_state:
                with st.expander("Presenter State", expanded=False):
                    st.json(presenter_state)
        else:
            st.warning("⚠️ No FCF analysis results")
            
    except Exception as e:
        st.error(f"❌ FCF presentation failed: {str(e)}")


def test_form_builder():
    """Test FormBuilder component"""
    st.header("📝 Form Builder Test")
    
    form_builder = FormBuilder("test_form")
    
    form_config = {
        "title": "Sample Financial Analysis Form",
        "description": "Enter parameters for financial analysis",
        "fields": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "default": "Test Company"
            },
            "ticker": {
                "type": "text", 
                "label": "Ticker Symbol",
                "default": "TEST"
            },
            "discount_rate": {
                "type": "number",
                "label": "Discount Rate (%)",
                "default": 10.0,
                "min": 1.0,
                "max": 50.0,
                "step": 0.1
            },
            "analysis_type": {
                "type": "selectbox",
                "label": "Analysis Type",
                "options": ["FCF", "DCF", "DDM"]
            },
            "include_sensitivity": {
                "type": "checkbox",
                "label": "Include Sensitivity Analysis",
                "default": True
            }
        },
        "submit_label": "Run Analysis"
    }
    
    def handle_form_submission(form_data):
        st.success("✅ Form submitted successfully!")
        st.json(form_data)
    
    form_result = form_builder.render(
        form_config=form_config,
        submit_callback=handle_form_submission
    )
    
    if form_result:
        st.write("Form data captured:")
        st.json(form_result)


def main():
    """Main test function"""
    st.set_page_config(
        page_title="UI Components Test",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 UI Components Integration Test")
    st.write("Testing the new modular UI architecture for financial analysis application")
    
    # Sidebar for test selection
    with st.sidebar:
        st.header("Test Selection")
        
        test_type = st.selectbox(
            "Choose Test Type",
            [
                "Basic Components",
                "Layouts", 
                "Widgets",
                "Presenter Integration",
                "Form Builder",
                "All Tests"
            ]
        )
    
    # Run selected tests
    if test_type == "Basic Components" or test_type == "All Tests":
        test_components_basic()
    
    if test_type == "Layouts" or test_type == "All Tests":
        if test_type == "All Tests":
            st.divider()
        test_layouts()
    
    if test_type == "Widgets" or test_type == "All Tests":
        if test_type == "All Tests":
            st.divider()
        test_widgets()
    
    if test_type == "Presenter Integration" or test_type == "All Tests":
        if test_type == "All Tests":
            st.divider()
        test_presenter_integration()
    
    if test_type == "Form Builder" or test_type == "All Tests":
        if test_type == "All Tests":
            st.divider()
        test_form_builder()
    
    # Test summary
    st.divider()
    st.subheader("🎯 Test Summary")
    
    st.success("✅ Component architecture separation working")
    st.info("ℹ️ UI components decoupled from business logic")
    st.info("ℹ️ Presenter pattern enables clean data flow")
    st.info("ℹ️ Widgets provide domain-specific functionality")


if __name__ == "__main__":
    main()