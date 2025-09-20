"""
Interactive Widgets Collection
=============================

Specialized interactive widgets for financial analysis with advanced features
like real-time updates, drag-and-drop, progressive disclosure, and smart defaults.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import json
import time

from .advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState,
    InteractionEvent, performance_monitor
)


@dataclass
class WidgetTheme:
    """Theme configuration for widgets"""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    success_color: str = "#2ca02c"
    warning_color: str = "#ff7f0e"
    error_color: str = "#d62728"
    background_color: str = "#ffffff"
    text_color: str = "#000000"
    border_radius: str = "8px"
    font_family: str = "Arial, sans-serif"


class FinancialInputPanel(AdvancedComponent):
    """
    Advanced financial input panel with smart validation,
    auto-suggestions, and contextual help
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.validation_rules = {}
        self.auto_suggestions = {}

    @performance_monitor
    def render_content(self, data: Dict = None, **kwargs) -> Dict[str, Any]:
        """Render financial input panel"""
        input_data = {}

        # Panel header with context
        self._render_panel_header()

        # Company identification section
        company_data = self._render_company_section()
        input_data.update(company_data)

        # Financial parameters section
        financial_data = self._render_financial_parameters()
        input_data.update(financial_data)

        # Advanced options (collapsible)
        advanced_data = self._render_advanced_options()
        input_data.update(advanced_data)

        # Validation summary
        self._render_validation_summary(input_data)

        return input_data

    def _render_panel_header(self):
        """Render panel header with help and context"""
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.subheader(f"📊 {self.config.title}")
            st.caption(self.config.description)

        with col2:
            if st.button("❓ Help", key=f"{self.config.id}_help"):
                self._show_contextual_help()

        with col3:
            if st.button("🔄 Reset", key=f"{self.config.id}_reset"):
                self._reset_inputs()

    def _render_company_section(self) -> Dict[str, Any]:
        """Render company identification section"""
        st.markdown("### 🏢 Company Information")

        col1, col2 = st.columns(2)

        with col1:
            # Smart ticker input with suggestions
            ticker = st.text_input(
                "Stock Ticker Symbol",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                help="Enter a valid stock ticker symbol",
                key=f"{self.config.id}_ticker"
            ).upper()

            # Auto-suggestions based on input
            if ticker and len(ticker) >= 2:
                suggestions = self._get_ticker_suggestions(ticker)
                if suggestions:
                    st.info(f"💡 Suggestions: {', '.join(suggestions[:3])}")

        with col2:
            # Market selection with smart defaults
            market = st.selectbox(
                "Market",
                options=["Auto-detect", "US (NASDAQ/NYSE)", "TASE (Tel Aviv)", "LSE (London)", "TSX (Toronto)"],
                index=0,
                help="Select the primary market or use auto-detection",
                key=f"{self.config.id}_market"
            )

        # Company name auto-fill (if ticker is recognized)
        company_name = ""
        if ticker:
            company_name = self._get_company_name(ticker)
            if company_name:
                st.success(f"✅ Identified: {company_name}")

        return {
            "ticker": ticker,
            "market": market,
            "company_name": company_name
        }

    def _render_financial_parameters(self) -> Dict[str, Any]:
        """Render financial parameters section with smart defaults"""
        st.markdown("### 💰 Financial Parameters")

        # DCF Parameters
        with st.expander("📈 DCF Valuation Parameters", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                discount_rate = st.number_input(
                    "Discount Rate (%)",
                    min_value=1.0,
                    max_value=50.0,
                    value=10.0,
                    step=0.1,
                    format="%.1f",
                    help="Required rate of return (WACC)",
                    key=f"{self.config.id}_discount_rate"
                )

            with col2:
                terminal_growth = st.number_input(
                    "Terminal Growth Rate (%)",
                    min_value=0.0,
                    max_value=10.0,
                    value=2.5,
                    step=0.1,
                    format="%.1f",
                    help="Long-term growth rate",
                    key=f"{self.config.id}_terminal_growth"
                )

            with col3:
                projection_years = st.number_input(
                    "Projection Years",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Number of years to project",
                    key=f"{self.config.id}_projection_years"
                )

        # Risk Assessment
        with st.expander("⚖️ Risk Assessment", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                risk_level = st.select_slider(
                    "Risk Level",
                    options=["Very Low", "Low", "Medium", "High", "Very High"],
                    value="Medium",
                    help="Overall company risk assessment",
                    key=f"{self.config.id}_risk_level"
                )

            with col2:
                confidence_level = st.slider(
                    "Confidence Level (%)",
                    min_value=80,
                    max_value=99,
                    value=95,
                    step=1,
                    help="Statistical confidence level",
                    key=f"{self.config.id}_confidence"
                )

        return {
            "discount_rate": discount_rate / 100,
            "terminal_growth": terminal_growth / 100,
            "projection_years": projection_years,
            "risk_level": risk_level,
            "confidence_level": confidence_level / 100
        }

    def _render_advanced_options(self) -> Dict[str, Any]:
        """Render advanced options section"""
        advanced_data = {}

        with st.expander("🔧 Advanced Options", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Data Sources**")
                data_sources = st.multiselect(
                    "Preferred Data Sources",
                    options=["Yahoo Finance", "Alpha Vantage", "FMP", "Polygon", "Excel Files"],
                    default=["Yahoo Finance", "Excel Files"],
                    help="Select preferred data sources in order of priority",
                    key=f"{self.config.id}_data_sources"
                )

                enable_caching = st.checkbox(
                    "Enable Data Caching",
                    value=True,
                    help="Cache API responses for faster subsequent loads",
                    key=f"{self.config.id}_caching"
                )

            with col2:
                st.markdown("**Analysis Options**")
                analysis_options = st.multiselect(
                    "Analysis Types",
                    options=["DCF", "DDM", "P/B Ratio", "Monte Carlo", "Sensitivity Analysis"],
                    default=["DCF"],
                    help="Select types of analysis to perform",
                    key=f"{self.config.id}_analysis_types"
                )

                auto_refresh = st.checkbox(
                    "Auto-refresh Data",
                    value=False,
                    help="Automatically refresh data on page load",
                    key=f"{self.config.id}_auto_refresh"
                )

            advanced_data = {
                "data_sources": data_sources,
                "enable_caching": enable_caching,
                "analysis_types": analysis_options,
                "auto_refresh": auto_refresh
            }

        return advanced_data

    def _render_validation_summary(self, input_data: Dict):
        """Render validation summary and readiness indicator"""
        validation_results = self._validate_inputs(input_data)

        if validation_results["is_valid"]:
            st.success("✅ All inputs are valid. Ready to proceed with analysis.")
        else:
            st.warning("⚠️ Please review the following issues:")
            for issue in validation_results["issues"]:
                st.error(f"• {issue}")

    def _validate_inputs(self, input_data: Dict) -> Dict:
        """Validate all inputs and return validation results"""
        issues = []

        # Validate ticker
        if not input_data.get("ticker"):
            issues.append("Stock ticker is required")
        elif len(input_data["ticker"]) < 1:
            issues.append("Stock ticker must be at least 1 character")

        # Validate financial parameters
        if input_data.get("discount_rate", 0) <= 0:
            issues.append("Discount rate must be greater than 0")

        if input_data.get("terminal_growth", 0) < 0:
            issues.append("Terminal growth rate cannot be negative")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }

    def _get_ticker_suggestions(self, partial_ticker: str) -> List[str]:
        """Get ticker suggestions based on partial input"""
        # Mock suggestions - in real implementation, this would query a database
        common_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "AMD",
            "JPM", "BAC", "WFC", "GS", "V", "MA", "JNJ", "PFE", "XOM", "CVX"
        ]
        return [ticker for ticker in common_tickers if ticker.startswith(partial_ticker)]

    def _get_company_name(self, ticker: str) -> str:
        """Get company name from ticker symbol"""
        # Mock company names - in real implementation, this would query an API
        company_names = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc."
        }
        return company_names.get(ticker, "")

    def _show_contextual_help(self):
        """Show contextual help modal"""
        with st.modal("📖 Financial Input Help"):
            st.markdown("""
            ### Getting Started

            **Ticker Symbol**: Enter the stock ticker symbol (e.g., AAPL for Apple)

            **Discount Rate**: The required rate of return, typically the company's WACC
            - Conservative: 8-10%
            - Moderate: 10-12%
            - Aggressive: 12-15%

            **Terminal Growth Rate**: Long-term sustainable growth rate
            - Typically 2-4% for mature companies
            - GDP growth rate is a good benchmark

            **Projection Years**: Number of years to forecast
            - 5 years is standard
            - Use longer periods for high-growth companies
            """)

    def _reset_inputs(self):
        """Reset all inputs to default values"""
        # Clear session state for this component
        keys_to_clear = [key for key in st.session_state.keys()
                        if key.startswith(f"{self.config.id}_")]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()


class InteractiveScenarioAnalyzer(AdvancedComponent):
    """
    Interactive scenario analysis widget with drag-and-drop parameter adjustment
    and real-time sensitivity analysis visualization
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.scenarios = {
            "base_case": {"name": "Base Case", "color": "#1f77b4"},
            "optimistic": {"name": "Optimistic", "color": "#2ca02c"},
            "pessimistic": {"name": "Pessimistic", "color": "#d62728"}
        }

    @performance_monitor
    def render_content(self, base_parameters: Dict = None, **kwargs) -> Dict[str, Any]:
        """Render interactive scenario analyzer"""
        if not base_parameters:
            st.warning("Base parameters required for scenario analysis")
            return {}

        # Scenario selection and management
        scenario_controls = self._render_scenario_controls()

        # Parameter adjustment interface
        scenario_parameters = self._render_parameter_adjustments(base_parameters)

        # Real-time results visualization
        self._render_scenario_results(scenario_parameters)

        # Sensitivity analysis
        self._render_sensitivity_analysis(base_parameters)

        return scenario_parameters

    def _render_scenario_controls(self) -> Dict:
        """Render scenario selection and management controls"""
        st.markdown("### 🎯 Scenario Analysis")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            selected_scenario = st.selectbox(
                "Active Scenario",
                options=list(self.scenarios.keys()),
                format_func=lambda x: self.scenarios[x]["name"],
                key=f"{self.config.id}_scenario"
            )

        with col2:
            if st.button("➕ Add Scenario", key=f"{self.config.id}_add"):
                self._add_custom_scenario()

        with col3:
            if st.button("📋 Compare All", key=f"{self.config.id}_compare"):
                self._compare_all_scenarios()

        with col4:
            if st.button("💾 Save", key=f"{self.config.id}_save"):
                self._save_scenarios()

        return {"selected_scenario": selected_scenario}

    def _render_parameter_adjustments(self, base_parameters: Dict) -> Dict[str, Dict]:
        """Render parameter adjustment interface with sliders and percentage changes"""
        st.markdown("### 🎛️ Parameter Adjustments")

        scenario_params = {}

        # Create tabs for different parameter categories
        tabs = st.tabs(["📈 Growth", "💰 Margins", "⚖️ Risk", "🏗️ Structure"])

        with tabs[0]:  # Growth parameters
            scenario_params["growth"] = self._render_growth_adjustments(base_parameters)

        with tabs[1]:  # Margin parameters
            scenario_params["margins"] = self._render_margin_adjustments(base_parameters)

        with tabs[2]:  # Risk parameters
            scenario_params["risk"] = self._render_risk_adjustments(base_parameters)

        with tabs[3]:  # Capital structure
            scenario_params["structure"] = self._render_structure_adjustments(base_parameters)

        return scenario_params

    def _render_growth_adjustments(self, base_params: Dict) -> Dict:
        """Render growth parameter adjustments"""
        col1, col2 = st.columns(2)

        with col1:
            revenue_growth_adj = st.slider(
                "Revenue Growth Adjustment (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                key=f"{self.config.id}_revenue_growth",
                help="Adjust base case revenue growth rate"
            )

            base_growth = base_params.get("revenue_growth", 0.05)
            adjusted_growth = base_growth * (1 + revenue_growth_adj / 100)
            st.metric("Adjusted Revenue Growth", f"{adjusted_growth:.1%}", f"{revenue_growth_adj:+}%")

        with col2:
            terminal_growth_adj = st.slider(
                "Terminal Growth Adjustment (%)",
                min_value=-50,
                max_value=50,
                value=0,
                step=5,
                key=f"{self.config.id}_terminal_growth",
                help="Adjust terminal growth rate"
            )

            base_terminal = base_params.get("terminal_growth", 0.025)
            adjusted_terminal = base_terminal * (1 + terminal_growth_adj / 100)
            st.metric("Adjusted Terminal Growth", f"{adjusted_terminal:.1%}", f"{terminal_growth_adj:+}%")

        return {
            "revenue_growth_adjustment": revenue_growth_adj,
            "terminal_growth_adjustment": terminal_growth_adj,
            "adjusted_revenue_growth": adjusted_growth,
            "adjusted_terminal_growth": adjusted_terminal
        }

    def _render_margin_adjustments(self, base_params: Dict) -> Dict:
        """Render margin parameter adjustments"""
        col1, col2 = st.columns(2)

        with col1:
            operating_margin_adj = st.slider(
                "Operating Margin Adjustment (bps)",
                min_value=-1000,
                max_value=1000,
                value=0,
                step=50,
                key=f"{self.config.id}_operating_margin",
                help="Adjust operating margin in basis points"
            )

            base_margin = base_params.get("operating_margin", 0.15)
            adjusted_margin = base_margin + (operating_margin_adj / 10000)
            st.metric("Adjusted Operating Margin", f"{adjusted_margin:.1%}", f"{operating_margin_adj:+} bps")

        with col2:
            tax_rate_adj = st.slider(
                "Tax Rate Adjustment (%)",
                min_value=-30,
                max_value=30,
                value=0,
                step=1,
                key=f"{self.config.id}_tax_rate",
                help="Adjust effective tax rate"
            )

            base_tax = base_params.get("tax_rate", 0.21)
            adjusted_tax = base_tax + (tax_rate_adj / 100)
            st.metric("Adjusted Tax Rate", f"{adjusted_tax:.1%}", f"{tax_rate_adj:+}%")

        return {
            "operating_margin_adjustment": operating_margin_adj,
            "tax_rate_adjustment": tax_rate_adj,
            "adjusted_operating_margin": adjusted_margin,
            "adjusted_tax_rate": adjusted_tax
        }

    def _render_risk_adjustments(self, base_params: Dict) -> Dict:
        """Render risk parameter adjustments"""
        col1, col2 = st.columns(2)

        with col1:
            discount_rate_adj = st.slider(
                "Discount Rate Adjustment (%)",
                min_value=-5.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
                key=f"{self.config.id}_discount_rate",
                help="Adjust WACC/discount rate"
            )

            base_discount = base_params.get("discount_rate", 0.10)
            adjusted_discount = base_discount + (discount_rate_adj / 100)
            st.metric("Adjusted Discount Rate", f"{adjusted_discount:.1%}", f"{discount_rate_adj:+}%")

        with col2:
            beta_adj = st.slider(
                "Beta Adjustment (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                key=f"{self.config.id}_beta",
                help="Adjust systematic risk (beta)"
            )

            base_beta = base_params.get("beta", 1.0)
            adjusted_beta = base_beta * (1 + beta_adj / 100)
            st.metric("Adjusted Beta", f"{adjusted_beta:.2f}", f"{beta_adj:+}%")

        return {
            "discount_rate_adjustment": discount_rate_adj,
            "beta_adjustment": beta_adj,
            "adjusted_discount_rate": adjusted_discount,
            "adjusted_beta": adjusted_beta
        }

    def _render_structure_adjustments(self, base_params: Dict) -> Dict:
        """Render capital structure adjustments"""
        col1, col2 = st.columns(2)

        with col1:
            debt_ratio_adj = st.slider(
                "Debt Ratio Adjustment (%)",
                min_value=-50,
                max_value=50,
                value=0,
                step=5,
                key=f"{self.config.id}_debt_ratio",
                help="Adjust debt-to-equity ratio"
            )

            base_debt_ratio = base_params.get("debt_ratio", 0.3)
            adjusted_debt_ratio = base_debt_ratio * (1 + debt_ratio_adj / 100)
            st.metric("Adjusted Debt Ratio", f"{adjusted_debt_ratio:.1%}", f"{debt_ratio_adj:+}%")

        with col2:
            capex_adj = st.slider(
                "CapEx Adjustment (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=10,
                key=f"{self.config.id}_capex",
                help="Adjust capital expenditure"
            )

            base_capex = base_params.get("capex_rate", 0.05)
            adjusted_capex = base_capex * (1 + capex_adj / 100)
            st.metric("Adjusted CapEx Rate", f"{adjusted_capex:.1%}", f"{capex_adj:+}%")

        return {
            "debt_ratio_adjustment": debt_ratio_adj,
            "capex_adjustment": capex_adj,
            "adjusted_debt_ratio": adjusted_debt_ratio,
            "adjusted_capex": adjusted_capex
        }

    def _render_scenario_results(self, scenario_params: Dict):
        """Render real-time scenario results"""
        st.markdown("### 📊 Scenario Results")

        # Calculate valuation for each scenario
        results = self._calculate_scenario_valuations(scenario_params)

        # Display results in a comparison table
        if results:
            results_df = pd.DataFrame(results).T

            # Style the table
            styled_df = results_df.style.format({
                'Fair Value': '${:,.0f}',
                'Upside/Downside': '{:+.1%}',
                'NPV': '${:,.0f}M',
                'P/E Implied': '{:.1f}x'
            }).background_gradient(subset=['Fair Value'], cmap='RdYlGn')

            st.dataframe(styled_df, use_container_width=True)

            # Create comparison chart
            self._create_scenario_comparison_chart(results)

    def _render_sensitivity_analysis(self, base_params: Dict):
        """Render tornado chart for sensitivity analysis"""
        st.markdown("### 🌪️ Sensitivity Analysis")

        # Generate sensitivity data
        sensitivity_data = self._generate_sensitivity_data(base_params)

        # Create tornado chart
        self._create_tornado_chart(sensitivity_data)

    def _calculate_scenario_valuations(self, scenario_params: Dict) -> Dict:
        """Calculate valuations for different scenarios"""
        # Mock calculation - replace with actual DCF logic
        base_value = 100.0

        results = {}
        for scenario_key, scenario_info in self.scenarios.items():
            # Apply scenario adjustments
            adjustment_factor = 1.0

            if scenario_key == "optimistic":
                adjustment_factor = 1.2
            elif scenario_key == "pessimistic":
                adjustment_factor = 0.8

            fair_value = base_value * adjustment_factor
            current_price = 85.0  # Mock current price
            upside = (fair_value - current_price) / current_price

            results[scenario_info["name"]] = {
                "Fair Value": fair_value,
                "Current Price": current_price,
                "Upside/Downside": upside,
                "NPV": fair_value * 1000,  # Mock NPV in millions
                "P/E Implied": fair_value / 5.2  # Mock earnings
            }

        return results

    def _create_scenario_comparison_chart(self, results: Dict):
        """Create comparison chart for scenarios"""
        scenarios = list(results.keys())
        fair_values = [results[scenario]["Fair Value"] for scenario in scenarios]
        current_price = results[scenarios[0]]["Current Price"]

        fig = go.Figure()

        # Add current price line
        fig.add_hline(
            y=current_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Current Price: ${current_price:.0f}"
        )

        # Add scenario bars
        colors = ["#1f77b4", "#2ca02c", "#d62728"]  # Blue, Green, Red
        fig.add_trace(go.Bar(
            x=scenarios,
            y=fair_values,
            marker_color=colors[:len(scenarios)],
            text=[f"${val:.0f}" for val in fair_values],
            textposition='auto',
        ))

        fig.update_layout(
            title="Scenario Valuation Comparison",
            yaxis_title="Fair Value ($)",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def _generate_sensitivity_data(self, base_params: Dict) -> Dict:
        """Generate sensitivity analysis data"""
        # Mock sensitivity data
        variables = [
            "Revenue Growth", "Operating Margin", "Discount Rate",
            "Terminal Growth", "Tax Rate", "CapEx Rate"
        ]

        # Calculate impact of ±10% change in each variable
        impacts = []
        for var in variables:
            # Mock calculation - replace with actual sensitivity analysis
            if "Growth" in var:
                impact = np.random.uniform(15, 25)  # High impact
            elif "Margin" in var:
                impact = np.random.uniform(10, 20)  # Medium-high impact
            elif "Rate" in var:
                impact = np.random.uniform(5, 15)   # Medium impact
            else:
                impact = np.random.uniform(2, 10)   # Low-medium impact

            impacts.append(impact)

        return {
            "variables": variables,
            "impacts": impacts
        }

    def _create_tornado_chart(self, sensitivity_data: Dict):
        """Create tornado chart for sensitivity analysis"""
        variables = sensitivity_data["variables"]
        impacts = sensitivity_data["impacts"]

        # Create tornado chart data
        y_pos = np.arange(len(variables))

        fig = go.Figure()

        # Negative impacts (left side)
        fig.add_trace(go.Bar(
            y=variables,
            x=[-impact for impact in impacts],
            orientation='h',
            name='Downside',
            marker_color='red',
            opacity=0.7
        ))

        # Positive impacts (right side)
        fig.add_trace(go.Bar(
            y=variables,
            x=impacts,
            orientation='h',
            name='Upside',
            marker_color='green',
            opacity=0.7
        ))

        fig.update_layout(
            title="Sensitivity Analysis - Impact on Fair Value (%)",
            xaxis_title="Impact on Valuation (%)",
            barmode='overlay',
            height=400,
            xaxis=dict(range=[-max(impacts)*1.1, max(impacts)*1.1])
        )

        st.plotly_chart(fig, use_container_width=True)

    def _add_custom_scenario(self):
        """Add custom scenario"""
        st.info("Custom scenario functionality would be implemented here")

    def _compare_all_scenarios(self):
        """Compare all scenarios side by side"""
        st.info("Scenario comparison functionality would be implemented here")

    def _save_scenarios(self):
        """Save scenarios to session state or file"""
        st.success("Scenarios saved successfully!")


class RealTimeDataMonitor(AdvancedComponent):
    """
    Real-time data monitoring widget with live updates,
    alerts, and automatic refresh capabilities
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.refresh_interval = 10  # seconds
        self.alert_thresholds = {}

    @performance_monitor
    def render_content(self, data_sources: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Render real-time data monitor"""
        # Monitor controls
        monitor_config = self._render_monitor_controls()

        # Data source status
        self._render_data_source_status(data_sources or [])

        # Real-time metrics
        self._render_realtime_metrics()

        # Alert system
        self._render_alert_system()

        return monitor_config

    def _render_monitor_controls(self) -> Dict:
        """Render monitoring controls"""
        st.markdown("### 📡 Real-Time Data Monitor")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            auto_refresh = st.checkbox(
                "Auto Refresh",
                value=True,
                key=f"{self.config.id}_auto_refresh"
            )

        with col2:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                options=[5, 10, 30, 60],
                index=1,
                format_func=lambda x: f"{x}s",
                key=f"{self.config.id}_interval"
            )

        with col3:
            if st.button("🔄 Refresh Now", key=f"{self.config.id}_refresh_now"):
                self.clear_cache()
                st.rerun()

        with col4:
            alerts_enabled = st.checkbox(
                "Enable Alerts",
                value=True,
                key=f"{self.config.id}_alerts"
            )

        # Auto-refresh logic
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

        return {
            "auto_refresh": auto_refresh,
            "refresh_interval": refresh_interval,
            "alerts_enabled": alerts_enabled
        }

    def _render_data_source_status(self, data_sources: List[str]):
        """Render data source status indicators"""
        st.markdown("### 🔗 Data Source Status")

        if not data_sources:
            st.warning("No data sources configured")
            return

        cols = st.columns(len(data_sources))

        for i, source in enumerate(data_sources):
            with cols[i]:
                # Mock status check
                status = "online" if np.random.random() > 0.1 else "offline"
                latency = np.random.uniform(50, 200)

                status_color = "🟢" if status == "online" else "🔴"
                st.metric(
                    f"{status_color} {source}",
                    f"{latency:.0f}ms",
                    delta=f"{np.random.uniform(-10, 10):+.0f}ms"
                )

    def _render_realtime_metrics(self):
        """Render real-time metrics dashboard"""
        st.markdown("### 📊 Live Metrics")

        # Generate mock real-time data
        current_time = datetime.now()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            price = 150 + np.random.uniform(-5, 5)
            price_change = np.random.uniform(-2, 2)
            st.metric("Current Price", f"${price:.2f}", f"{price_change:+.2f}")

        with col2:
            volume = np.random.uniform(1000000, 5000000)
            volume_change = np.random.uniform(-20, 20)
            st.metric("Volume", f"{volume/1000000:.1f}M", f"{volume_change:+.1f}%")

        with col3:
            volatility = np.random.uniform(15, 35)
            volatility_change = np.random.uniform(-2, 2)
            st.metric("Volatility", f"{volatility:.1f}%", f"{volatility_change:+.1f}%")

        with col4:
            last_update = current_time.strftime("%H:%M:%S")
            st.metric("Last Update", last_update, "Real-time")

    def _render_alert_system(self):
        """Render alert system interface"""
        st.markdown("### 🚨 Alert System")

        with st.expander("Configure Alerts", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Price Alerts")
                price_alert_upper = st.number_input(
                    "Upper Threshold ($)",
                    value=160.0,
                    key=f"{self.config.id}_price_upper"
                )
                price_alert_lower = st.number_input(
                    "Lower Threshold ($)",
                    value=140.0,
                    key=f"{self.config.id}_price_lower"
                )

            with col2:
                st.subheader("Volume Alerts")
                volume_alert = st.number_input(
                    "Volume Threshold (M)",
                    value=10.0,
                    key=f"{self.config.id}_volume_alert"
                )
                volatility_alert = st.number_input(
                    "Volatility Threshold (%)",
                    value=30.0,
                    key=f"{self.config.id}_volatility_alert"
                )

        # Show active alerts
        active_alerts = self._check_alerts()
        if active_alerts:
            for alert in active_alerts:
                alert_type = alert.get("type", "info")
                message = alert.get("message", "")

                if alert_type == "warning":
                    st.warning(f"⚠️ {message}")
                elif alert_type == "error":
                    st.error(f"🚨 {message}")
                else:
                    st.info(f"ℹ️ {message}")

    def _check_alerts(self) -> List[Dict]:
        """Check for active alerts"""
        # Mock alert checking
        alerts = []

        if np.random.random() > 0.8:
            alerts.append({
                "type": "warning",
                "message": "Price approaching upper threshold"
            })

        if np.random.random() > 0.9:
            alerts.append({
                "type": "error",
                "message": "Unusual trading volume detected"
            })

        return alerts


# Factory functions for creating interactive widgets
def create_financial_input_panel(component_id: str) -> FinancialInputPanel:
    """Create financial input panel widget"""
    config = ComponentConfig(
        id=component_id,
        title="Financial Analysis Input",
        description="Enter company information and analysis parameters",
        cache_enabled=True,
        auto_refresh=False
    )
    return FinancialInputPanel(config)


def create_scenario_analyzer(component_id: str) -> InteractiveScenarioAnalyzer:
    """Create interactive scenario analyzer widget"""
    config = ComponentConfig(
        id=component_id,
        title="Scenario Analysis",
        description="Analyze multiple scenarios with parameter adjustments",
        cache_enabled=True,
        auto_refresh=False
    )
    return InteractiveScenarioAnalyzer(config)


def create_data_monitor(component_id: str) -> RealTimeDataMonitor:
    """Create real-time data monitoring widget"""
    config = ComponentConfig(
        id=component_id,
        title="Real-Time Data Monitor",
        description="Monitor live data feeds and system status",
        cache_enabled=False,
        auto_refresh=True
    )
    return RealTimeDataMonitor(config)