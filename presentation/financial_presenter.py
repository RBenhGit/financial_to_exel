"""
Financial Analysis Presenter
===========================

Coordinates between financial calculation business logic and UI presentation
for FCF analysis, metrics display, and financial data visualization.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import streamlit as st
import logging

from .base_presenter import BasePresenter
from ui.components import MetricsDisplay, ChartRenderer, TableFormatter
from ui.layouts import TabsLayout, MainContentLayout

logger = logging.getLogger(__name__)


class FinancialAnalysisPresenter(BasePresenter):
    """Presenter for financial analysis workflow"""
    
    def __init__(self):
        super().__init__("financial_analysis")
        self._setup_ui_components()
    
    def _setup_ui_components(self):
        """Initialize UI components for financial analysis"""
        self.register_ui_component("metrics", MetricsDisplay("financial_metrics"))
        self.register_ui_component("charts", ChartRenderer("financial_charts"))
        self.register_ui_component("tables", TableFormatter("financial_tables"))
        self.register_ui_component("tabs", TabsLayout("financial_tabs"))
        self.register_ui_component("layout", MainContentLayout("financial_layout"))
    
    def present(self, financial_data: Dict[str, Any], 
               analysis_type: str = "fcf", **kwargs) -> Dict[str, Any]:
        """
        Present financial analysis results
        
        Args:
            financial_data: Financial calculation results
            analysis_type: Type of analysis ('fcf', 'dcf', 'metrics')
        """
        try:
            presentation_results = {}
            
            if analysis_type == "fcf":
                presentation_results = self._present_fcf_analysis(financial_data, **kwargs)
            elif analysis_type == "dcf":  
                presentation_results = self._present_dcf_analysis(financial_data, **kwargs)
            elif analysis_type == "metrics":
                presentation_results = self._present_metrics_overview(financial_data, **kwargs)
            else:
                st.error(f"Unknown analysis type: {analysis_type}")
                return {}
            
            # Store results in presenter state
            self.update_presenter_state({
                "last_analysis": analysis_type,
                "last_results": presentation_results
            })
            
            return presentation_results
            
        except Exception as e:
            self.handle_error(e, f"presenting {analysis_type} analysis")
            return {}
    
    def _present_fcf_analysis(self, fcf_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Present Free Cash Flow analysis"""
        st.header("💰 Free Cash Flow Analysis")
        
        results = {}
        
        # Extract FCF metrics
        fcf_metrics = self._extract_fcf_metrics(fcf_data)
        
        # Display key metrics
        metrics_component = self.get_ui_component("metrics")
        if metrics_component and fcf_metrics:
            st.subheader("📊 Key FCF Metrics")
            metrics_component.render(
                metrics=fcf_metrics,
                layout="columns",
                format_func=self.format_currency
            )
            results["displayed_metrics"] = fcf_metrics
        
        # FCF trends chart
        fcf_trends = self._prepare_fcf_trends_data(fcf_data)
        if fcf_trends:
            charts_component = self.get_ui_component("charts")
            if charts_component:
                st.subheader("📈 FCF Trends")
                chart_config = {
                    "data": fcf_trends,
                    "title": "Free Cash Flow Trends",
                    "x_column": "Year",
                    "y_column": "FCF"
                }
                fig = charts_component.render(chart_config, chart_type="line")
                results["fcf_trends_chart"] = fig
        
        # FCF growth rates table
        growth_rates = fcf_data.get("growth_rates", {})
        if growth_rates:
            st.subheader("📊 FCF Growth Rates")
            growth_df = self._format_growth_rates_table(growth_rates)
            
            tables_component = self.get_ui_component("tables")
            if tables_component:
                styling_config = {
                    "format": {col: "{:.2%}" for col in growth_df.columns if "Rate" in col},
                    "highlight": [{
                        "type": "positive_negative",
                        "columns": [col for col in growth_df.columns if "Rate" in col]
                    }]
                }
                
                tables_component.render(
                    growth_df,
                    styling_config=styling_config,
                    download_filename="fcf_growth_rates.csv"
                )
                results["growth_rates_table"] = growth_df
        
        return results
    
    def _present_dcf_analysis(self, dcf_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Present DCF valuation analysis"""  
        st.header("🏢 DCF Valuation Analysis")
        
        results = {}
        
        # Valuation summary metrics
        valuation_metrics = self._extract_dcf_metrics(dcf_data)
        
        metrics_component = self.get_ui_component("metrics")
        if metrics_component and valuation_metrics:
            st.subheader("💵 Valuation Summary")
            metrics_component.render(
                metrics=valuation_metrics,
                layout="columns", 
                format_func=self.format_currency
            )
            results["valuation_metrics"] = valuation_metrics
        
        # DCF sensitivity analysis
        sensitivity_data = dcf_data.get("sensitivity_analysis")
        if sensitivity_data:
            st.subheader("🎯 Sensitivity Analysis")
            sensitivity_df = self._format_sensitivity_table(sensitivity_data)
            
            tables_component = self.get_ui_component("tables")
            if tables_component:
                styling_config = {
                    "format": {col: self.format_currency for col in sensitivity_df.columns[1:]}
                }
                
                tables_component.render(
                    sensitivity_df,
                    styling_config=styling_config,
                    download_filename="dcf_sensitivity.csv"
                )
                results["sensitivity_table"] = sensitivity_df
        
        # DCF waterfall chart
        if "cash_flows" in dcf_data:
            st.subheader("🌊 DCF Waterfall")
            waterfall_data = self._prepare_dcf_waterfall_data(dcf_data)
            
            charts_component = self.get_ui_component("charts")
            if charts_component:
                chart_config = {
                    "data": waterfall_data,
                    "title": "DCF Valuation Waterfall",
                    "x_column": "Component",
                    "y_column": "Value"
                }
                fig = charts_component.render(chart_config, chart_type="bar")
                results["waterfall_chart"] = fig
        
        return results
    
    def _present_metrics_overview(self, metrics_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Present financial metrics overview"""
        st.header("📊 Financial Metrics Overview")
        
        results = {}
        
        # Setup tabs for different metric categories  
        tabs_component = self.get_ui_component("tabs")
        if tabs_component:
            tabs_component.add_tab("profitability", "💰 Profitability", 
                                 self._render_profitability_metrics)
            tabs_component.add_tab("liquidity", "💧 Liquidity", 
                                 self._render_liquidity_metrics)
            tabs_component.add_tab("efficiency", "⚡ Efficiency",
                                 self._render_efficiency_metrics)
            tabs_component.add_tab("leverage", "🏗️ Leverage",
                                 self._render_leverage_metrics)
            
            tabs_results = tabs_component.render(metrics_data)
            results.update(tabs_results)
        
        return results
    
    def _extract_fcf_metrics(self, fcf_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract key FCF metrics for display"""
        metrics = {}
        
        # Get latest FCF values
        if "fcf_results" in fcf_data:
            fcf_results = fcf_data["fcf_results"]
            
            # Latest year FCF values
            for fcf_type in ["FCFF", "FCFE", "LFCF"]:
                if fcf_type in fcf_results and fcf_results[fcf_type]:
                    latest_fcf = fcf_results[fcf_type][-1]
                    metrics[f"Latest {fcf_type}"] = latest_fcf
        
        # Average growth rates
        if "growth_rates" in fcf_data:
            growth_rates = fcf_data["growth_rates"]
            if "Average" in growth_rates:
                avg_growth = growth_rates["Average"]
                if "5yr" in avg_growth:
                    metrics["5-Year Growth Rate"] = avg_growth["5yr"]
        
        return metrics
    
    def _extract_dcf_metrics(self, dcf_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract key DCF metrics for display"""
        metrics = {}
        
        if "valuation" in dcf_data:
            valuation = dcf_data["valuation"]
            metrics["Enterprise Value"] = valuation.get("enterprise_value", 0)
            metrics["Equity Value"] = valuation.get("equity_value", 0)
            metrics["Value per Share"] = valuation.get("value_per_share", 0)
        
        if "current_price" in dcf_data:
            current_price = dcf_data["current_price"]
            value_per_share = metrics.get("Value per Share", 0)
            if current_price > 0 and value_per_share > 0:
                upside = (value_per_share - current_price) / current_price
                metrics["Upside/Downside"] = upside
        
        return metrics
    
    def _prepare_fcf_trends_data(self, fcf_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Prepare FCF trends data for charting"""
        if "fcf_results" not in fcf_data:
            return None
        
        fcf_results = fcf_data["fcf_results"]
        trends_data = []
        
        # Assume years are consecutive starting from a base year
        base_year = 2019  # Or extract from metadata
        
        for i, year_idx in enumerate(range(len(fcf_results.get("FCFF", [])))):
            year = base_year + i
            row = {"Year": year}
            
            for fcf_type in ["FCFF", "FCFE", "LFCF"]:
                if fcf_type in fcf_results and year_idx < len(fcf_results[fcf_type]):
                    row[fcf_type] = fcf_results[fcf_type][year_idx]
            
            trends_data.append(row)
        
        return pd.DataFrame(trends_data) if trends_data else None
    
    def _format_growth_rates_table(self, growth_rates: Dict[str, Any]) -> pd.DataFrame:
        """Format growth rates data as a table"""
        rows = []
        
        for fcf_type, rates in growth_rates.items():
            row = {"FCF Type": fcf_type}
            for period, rate in rates.items():
                row[f"{period} Growth Rate"] = rate
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _format_sensitivity_table(self, sensitivity_data: Dict[str, Any]) -> pd.DataFrame:
        """Format sensitivity analysis as a table"""
        discount_rates = sensitivity_data.get("discount_rates", [])
        growth_rates = sensitivity_data.get("terminal_growth_rates", [])
        valuations = sensitivity_data.get("valuations", [])
        
        # Create DataFrame with discount rates as rows and growth rates as columns
        df = pd.DataFrame(
            valuations,
            index=[f"{r:.1%}" for r in discount_rates],
            columns=[f"{g:.1%}" for g in growth_rates]
        )
        df.index.name = "Discount Rate"
        
        return df
    
    def _prepare_dcf_waterfall_data(self, dcf_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare DCF waterfall chart data"""
        components = []
        values = []
        
        if "cash_flows" in dcf_data:
            cash_flows = dcf_data["cash_flows"]
            
            # Add projected cash flows
            for year, cf in enumerate(cash_flows.get("projected", []), 1):
                components.append(f"Year {year} FCF")
                values.append(cf)
            
            # Add terminal value
            if "terminal_value" in cash_flows:
                components.append("Terminal Value")
                values.append(cash_flows["terminal_value"])
        
        return pd.DataFrame({"Component": components, "Value": values})
    
    def _render_profitability_metrics(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Render profitability metrics tab"""
        st.write("🔢 **Profitability Ratios**")
        
        # Extract profitability metrics from data
        profitability = data.get("profitability", {})
        
        if profitability:
            metrics_component = self.get_ui_component("metrics")
            if metrics_component:
                metrics_component.render(profitability, format_func=self.format_percentage)
        
        return {"profitability_displayed": True}
    
    def _render_liquidity_metrics(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Render liquidity metrics tab"""
        st.write("💧 **Liquidity Ratios**")
        
        liquidity = data.get("liquidity", {})
        
        if liquidity:
            metrics_component = self.get_ui_component("metrics")
            if metrics_component:
                metrics_component.render(liquidity, format_func=lambda x: f"{x:.2f}")
        
        return {"liquidity_displayed": True}
    
    def _render_efficiency_metrics(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Render efficiency metrics tab"""
        st.write("⚡ **Efficiency Ratios**")
        
        efficiency = data.get("efficiency", {})
        
        if efficiency:
            metrics_component = self.get_ui_component("metrics")
            if metrics_component:
                metrics_component.render(efficiency, format_func=lambda x: f"{x:.2f}x")
        
        return {"efficiency_displayed": True}
    
    def _render_leverage_metrics(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Render leverage metrics tab"""
        st.write("🏗️ **Leverage Ratios**")
        
        leverage = data.get("leverage", {})
        
        if leverage:
            metrics_component = self.get_ui_component("metrics")
            if metrics_component:
                metrics_component.render(leverage, format_func=lambda x: f"{x:.2f}x")
        
        return {"leverage_displayed": True}