"""
Specialized UI Widgets for Financial Analysis
============================================

Domain-specific widgets that combine base components for 
financial analysis functionality.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from .components import UIComponent, FormBuilder, TableFormatter


class FinancialInputWidget(UIComponent):
    """Widget for financial data input with validation"""
    
    def render(self, input_type: str = "ticker", 
               validation_callback: Optional[Callable] = None,
               **kwargs) -> Dict[str, Any]:
        """
        Render financial input widget
        
        Args:
            input_type: 'ticker', 'excel', 'manual'
            validation_callback: Function to validate input
        """
        input_data = {}
        
        if input_type == "ticker":
            input_data = self._render_ticker_input(validation_callback, **kwargs)
        elif input_type == "excel":
            input_data = self._render_excel_input(validation_callback, **kwargs)
        elif input_type == "manual":
            input_data = self._render_manual_input(validation_callback, **kwargs)
        
        return input_data
    
    def _render_ticker_input(self, validation_callback: Optional[Callable],
                           **kwargs) -> Dict[str, Any]:
        """Render ticker symbol input"""
        st.subheader("📈 Stock Ticker Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ticker = st.text_input(
                "Enter Stock Ticker Symbol",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                help="Enter a valid stock ticker symbol"
            ).upper()
        
        with col2:
            market = st.selectbox(
                "Market",
                options=["US", "TASE", "Auto"],
                index=2,
                help="Select stock market or use auto-detection"
            )
        
        # Data source selection
        data_source = st.selectbox(
            "Data Source",
            options=["Auto", "Yahoo Finance", "Alpha Vantage", "FMP", "Polygon"],
            help="Choose preferred data source"
        )
        
        # Validation
        if ticker and validation_callback:
            is_valid, validation_msg = validation_callback(ticker, market)
            if is_valid:
                st.success(f"✓ {validation_msg}")
            else:
                st.error(f"✗ {validation_msg}")
        
        return {
            "ticker": ticker,
            "market": market,
            "data_source": data_source,
            "valid": bool(ticker and len(ticker) > 0)
        }
    
    def _render_excel_input(self, validation_callback: Optional[Callable],
                          **kwargs) -> Dict[str, Any]:
        """Render Excel file input"""
        st.subheader("📊 Excel File Analysis")
        
        uploaded_file = st.file_uploader(
            "Upload Financial Statements Excel File",
            type=['xlsx', 'xls'],
            help="Upload Excel file containing financial statements"
        )
        
        if uploaded_file:
            st.success(f"✓ File uploaded: {uploaded_file.name}")
            
            # Sheet selection (if multiple sheets)
            try:
                excel_file = pd.ExcelFile(uploaded_file)
                if len(excel_file.sheet_names) > 1:
                    selected_sheet = st.selectbox(
                        "Select Sheet",
                        options=excel_file.sheet_names,
                        help="Choose the sheet containing financial data"
                    )
                else:
                    selected_sheet = excel_file.sheet_names[0]
                    st.info(f"Using sheet: {selected_sheet}")
                
                return {
                    "file": uploaded_file,
                    "sheet": selected_sheet,
                    "valid": True
                }
            except Exception as e:
                st.error(f"Error reading Excel file: {str(e)}")
                return {"valid": False}
        
        return {"valid": False}
    
    def _render_manual_input(self, validation_callback: Optional[Callable],
                           **kwargs) -> Dict[str, Any]:
        """Render manual financial data input"""
        st.subheader("✏️ Manual Data Entry")
        
        # Company information
        company_name = st.text_input("Company Name")
        ticker = st.text_input("Ticker Symbol (Optional)")
        
        # Financial periods
        num_years = st.number_input(
            "Number of Historical Years",
            min_value=1, max_value=10, value=3
        )
        
        # Dynamic form for financial data
        financial_data = {}
        
        with st.expander("📋 Financial Data Entry", expanded=True):
            for year in range(num_years):
                year_label = f"Year {year + 1}"
                st.write(f"**{year_label}**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    revenue = st.number_input(
                        f"Revenue", 
                        key=f"revenue_{year}",
                        format="%.0f"
                    )
                
                with col2:
                    fcf = st.number_input(
                        f"Free Cash Flow",
                        key=f"fcf_{year}",
                        format="%.0f"
                    )
                
                with col3:
                    net_income = st.number_input(
                        f"Net Income",
                        key=f"net_income_{year}",
                        format="%.0f"
                    )
                
                financial_data[f"year_{year}"] = {
                    "revenue": revenue,
                    "fcf": fcf,
                    "net_income": net_income
                }
        
        return {
            "company_name": company_name,
            "ticker": ticker,
            "num_years": num_years,
            "financial_data": financial_data,
            "valid": bool(company_name and any(
                data["revenue"] > 0 for data in financial_data.values()
            ))
        }


class ExportWidget(UIComponent):
    """Widget for exporting analysis results"""
    
    def render(self, export_data: Dict[str, Any], 
               available_formats: List[str] = None,
               **kwargs) -> Dict[str, Any]:
        """
        Render export options widget
        
        Args:
            export_data: Data available for export
            available_formats: List of supported export formats
        """
        if available_formats is None:
            available_formats = ["Excel", "CSV", "PDF", "JSON"]
        
        st.subheader("📥 Export Results")
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            options=available_formats,
            help="Choose export format"
        )
        
        # Export scope selection
        export_scope = st.multiselect(
            "Data to Export",
            options=list(export_data.keys()),
            default=list(export_data.keys()),
            help="Select which data to include in export"
        )
        
        # File naming
        col1, col2 = st.columns([2, 1])
        
        with col1:
            filename = st.text_input(
                "Export Filename",
                value=f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                help="Enter filename (extension will be added automatically)"
            )
        
        with col2:
            include_timestamp = st.checkbox(
                "Include Timestamp",
                value=True,
                help="Add timestamp to filename"
            )
        
        # Export directory
        export_dir = st.text_input(
            "Export Directory",
            value=str(Path.home() / "Downloads"),
            help="Directory where file will be saved"
        )
        
        # Export button
        if st.button("📤 Export Analysis", type="primary"):
            if filename and export_scope:
                return {
                    "format": export_format,
                    "scope": export_scope,
                    "filename": filename,
                    "include_timestamp": include_timestamp,
                    "directory": export_dir,
                    "requested": True
                }
            else:
                st.error("Please enter filename and select data to export")
        
        return {"requested": False}


class SettingsWidget(UIComponent):
    """Widget for application settings and configuration"""
    
    def render(self, current_settings: Dict[str, Any] = None,
               **kwargs) -> Dict[str, Any]:
        """Render settings configuration widget"""
        if current_settings is None:
            current_settings = {}
        
        settings = {}
        
        with st.expander("⚙️ Analysis Settings", expanded=False):
            # DCF Settings
            st.write("**DCF Valuation Settings**")
            col1, col2 = st.columns(2)
            
            with col1:
                settings["discount_rate"] = st.number_input(
                    "Discount Rate (%)",
                    value=current_settings.get("discount_rate", 10.0),
                    min_value=1.0, max_value=50.0, step=0.1,
                    format="%.1f"
                ) / 100
                
                settings["terminal_growth_rate"] = st.number_input(
                    "Terminal Growth Rate (%)",
                    value=current_settings.get("terminal_growth_rate", 2.5) * 100,
                    min_value=0.0, max_value=10.0, step=0.1,
                    format="%.1f"
                ) / 100
            
            with col2:
                settings["projection_years"] = st.number_input(
                    "Projection Years",
                    value=current_settings.get("projection_years", 5),
                    min_value=1, max_value=20, step=1
                )
                
                settings["confidence_level"] = st.number_input(
                    "Confidence Level (%)",
                    value=current_settings.get("confidence_level", 95),
                    min_value=80, max_value=99, step=1
                ) / 100
        
        with st.expander("📊 Display Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                settings["decimal_places"] = st.number_input(
                    "Decimal Places",
                    value=current_settings.get("decimal_places", 2),
                    min_value=0, max_value=6, step=1
                )
                
                settings["currency_symbol"] = st.text_input(
                    "Currency Symbol",
                    value=current_settings.get("currency_symbol", "$"),
                    max_chars=3
                )
            
            with col2:
                settings["number_format"] = st.selectbox(
                    "Number Format",
                    options=["1,000,000", "1M", "1000000"],
                    index=0 if current_settings.get("number_format") == "1,000,000" else 1
                )
                
                settings["chart_theme"] = st.selectbox(
                    "Chart Theme",
                    options=["plotly", "plotly_white", "plotly_dark", "ggplot2"],
                    index=0
                )
        
        with st.expander("🔧 Advanced Settings", expanded=False):
            settings["enable_caching"] = st.checkbox(
                "Enable Data Caching",
                value=current_settings.get("enable_caching", True),
                help="Cache API responses to improve performance"
            )
            
            settings["auto_refresh"] = st.checkbox(
                "Auto-refresh Data",
                value=current_settings.get("auto_refresh", False),
                help="Automatically refresh data on page load"
            )
            
            settings["debug_mode"] = st.checkbox(
                "Debug Mode",
                value=current_settings.get("debug_mode", False),
                help="Show debug information and logs"
            )
        
        # Reset settings button
        if st.button("🔄 Reset to Defaults", help="Reset all settings to default values"):
            settings = self._get_default_settings()
            st.rerun()
        
        return settings
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings configuration"""
        return {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "projection_years": 5,
            "confidence_level": 0.95,
            "decimal_places": 2,
            "currency_symbol": "$",
            "number_format": "1,000,000",
            "chart_theme": "plotly",
            "enable_caching": True,
            "auto_refresh": False,
            "debug_mode": False
        }