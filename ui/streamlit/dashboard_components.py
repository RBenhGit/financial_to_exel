"""
Dashboard Components Hierarchy for Financial Metrics
==================================================

This module defines the component hierarchy and organization for displaying
financial metrics in a structured, intuitive dashboard layout.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np


@dataclass
class MetricDefinition:
    """Definition of a financial metric with display properties"""
    name: str
    formula: str
    category: str
    unit: str = "%"
    format_string: str = "{:.2f}"
    icon: str = "📊"
    description: str = ""
    benchmark_type: str = "industry"  # industry, peers, historical
    threshold_good: float = None
    threshold_warning: float = None


@dataclass
class MetricValue:
    """Container for metric values and metadata"""
    current: float
    previous: Optional[float] = None
    benchmark: Optional[float] = None
    trend: str = "neutral"  # positive, negative, neutral
    confidence: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)


class FinancialMetricsHierarchy:
    """Defines the hierarchical organization of financial metrics"""

    def __init__(self):
        self.metric_definitions = self._initialize_metric_definitions()
        self.component_hierarchy = self._build_component_hierarchy()

    def _initialize_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Initialize all financial metric definitions"""
        return {
            # Profitability Metrics
            "roe": MetricDefinition(
                name="Return on Equity",
                formula="Net Income / Shareholders' Equity",
                category="profitability",
                unit="%",
                icon="📈",
                description="Measures company's ability to generate returns on shareholders' investments",
                threshold_good=15.0,
                threshold_warning=10.0
            ),
            "roa": MetricDefinition(
                name="Return on Assets",
                formula="Net Income / Total Assets",
                category="profitability",
                unit="%",
                icon="📈",
                description="Indicates how efficiently company uses its assets to generate profit",
                threshold_good=8.0,
                threshold_warning=4.0
            ),
            "gross_margin": MetricDefinition(
                name="Gross Margin",
                formula="(Revenue - COGS) / Revenue",
                category="profitability",
                unit="%",
                icon="💰",
                description="Percentage of revenue retained after direct costs",
                threshold_good=40.0,
                threshold_warning=20.0
            ),
            "operating_margin": MetricDefinition(
                name="Operating Margin",
                formula="Operating Income / Revenue",
                category="profitability",
                unit="%",
                icon="💰",
                description="Profit margin from core business operations",
                threshold_good=20.0,
                threshold_warning=10.0
            ),
            "net_margin": MetricDefinition(
                name="Net Margin",
                formula="Net Income / Revenue",
                category="profitability",
                unit="%",
                icon="💰",
                description="Percentage of revenue that becomes profit",
                threshold_good=15.0,
                threshold_warning=5.0
            ),

            # Liquidity Metrics
            "current_ratio": MetricDefinition(
                name="Current Ratio",
                formula="Current Assets / Current Liabilities",
                category="liquidity",
                unit="x",
                format_string="{:.2f}",
                icon="💧",
                description="Ability to pay short-term obligations",
                threshold_good=2.0,
                threshold_warning=1.0
            ),
            "quick_ratio": MetricDefinition(
                name="Quick Ratio",
                formula="(Current Assets - Inventory) / Current Liabilities",
                category="liquidity",
                unit="x",
                format_string="{:.2f}",
                icon="💧",
                description="Ability to pay short-term debts without selling inventory",
                threshold_good=1.0,
                threshold_warning=0.5
            ),
            "cash_ratio": MetricDefinition(
                name="Cash Ratio",
                formula="Cash & Cash Equivalents / Current Liabilities",
                category="liquidity",
                unit="x",
                format_string="{:.2f}",
                icon="💧",
                description="Most conservative liquidity measure",
                threshold_good=0.5,
                threshold_warning=0.1
            ),

            # Efficiency Metrics
            "asset_turnover": MetricDefinition(
                name="Asset Turnover",
                formula="Revenue / Average Total Assets",
                category="efficiency",
                unit="x",
                format_string="{:.2f}",
                icon="⚡",
                description="How efficiently company uses assets to generate sales",
                threshold_good=1.0,
                threshold_warning=0.5
            ),
            "inventory_turnover": MetricDefinition(
                name="Inventory Turnover",
                formula="COGS / Average Inventory",
                category="efficiency",
                unit="x",
                format_string="{:.2f}",
                icon="⚡",
                description="How quickly company sells inventory",
                threshold_good=6.0,
                threshold_warning=3.0
            ),
            "receivables_turnover": MetricDefinition(
                name="Receivables Turnover",
                formula="Revenue / Average Accounts Receivable",
                category="efficiency",
                unit="x",
                format_string="{:.2f}",
                icon="⚡",
                description="How efficiently company collects receivables",
                threshold_good=8.0,
                threshold_warning=4.0
            ),

            # Leverage Metrics
            "debt_to_equity": MetricDefinition(
                name="Debt-to-Equity",
                formula="Total Debt / Total Equity",
                category="leverage",
                unit="x",
                format_string="{:.2f}",
                icon="⚖️",
                description="Financial leverage and capital structure",
                threshold_good=0.5,
                threshold_warning=1.0
            ),
            "debt_to_assets": MetricDefinition(
                name="Debt-to-Assets",
                formula="Total Debt / Total Assets",
                category="leverage",
                unit="%",
                icon="⚖️",
                description="Percentage of assets financed by debt",
                threshold_good=30.0,
                threshold_warning=60.0
            ),
            "interest_coverage": MetricDefinition(
                name="Interest Coverage",
                formula="EBIT / Interest Expense",
                category="leverage",
                unit="x",
                format_string="{:.2f}",
                icon="⚖️",
                description="Ability to pay interest on debt",
                threshold_good=5.0,
                threshold_warning=2.0
            ),

            # Valuation Metrics
            "pe_ratio": MetricDefinition(
                name="P/E Ratio",
                formula="Price per Share / Earnings per Share",
                category="valuation",
                unit="x",
                format_string="{:.2f}",
                icon="💰",
                description="Price relative to earnings",
                benchmark_type="industry"
            ),
            "pb_ratio": MetricDefinition(
                name="P/B Ratio",
                formula="Price per Share / Book Value per Share",
                category="valuation",
                unit="x",
                format_string="{:.2f}",
                icon="💰",
                description="Price relative to book value",
                benchmark_type="industry"
            ),
            "ps_ratio": MetricDefinition(
                name="P/S Ratio",
                formula="Market Cap / Revenue",
                category="valuation",
                unit="x",
                format_string="{:.2f}",
                icon="💰",
                description="Price relative to sales",
                benchmark_type="industry"
            ),
            "ev_ebitda": MetricDefinition(
                name="EV/EBITDA",
                formula="Enterprise Value / EBITDA",
                category="valuation",
                unit="x",
                format_string="{:.2f}",
                icon="💰",
                description="Enterprise value relative to EBITDA",
                benchmark_type="industry"
            ),

            # Growth Metrics
            "revenue_growth": MetricDefinition(
                name="Revenue Growth",
                formula="(Current Revenue - Previous Revenue) / Previous Revenue",
                category="growth",
                unit="%",
                icon="🚀",
                description="Year-over-year revenue growth rate",
                threshold_good=10.0,
                threshold_warning=0.0
            ),
            "earnings_growth": MetricDefinition(
                name="Earnings Growth",
                formula="(Current Earnings - Previous Earnings) / Previous Earnings",
                category="growth",
                unit="%",
                icon="🚀",
                description="Year-over-year earnings growth rate",
                threshold_good=15.0,
                threshold_warning=0.0
            ),
            "fcf_growth": MetricDefinition(
                name="FCF Growth",
                formula="(Current FCF - Previous FCF) / Previous FCF",
                category="growth",
                unit="%",
                icon="🚀",
                description="Free cash flow growth rate",
                threshold_good=10.0,
                threshold_warning=0.0
            )
        }

    def _build_component_hierarchy(self) -> Dict:
        """Build the hierarchical component structure"""
        return {
            "overview_panel": {
                "title": "Company Overview",
                "icon": "🏢",
                "components": ["company_header", "key_metrics_summary", "price_chart"]
            },
            "profitability_panel": {
                "title": "Profitability Analysis",
                "icon": "📈",
                "components": ["profitability_metrics", "profitability_trends", "margin_analysis"]
            },
            "liquidity_panel": {
                "title": "Liquidity & Efficiency",
                "icon": "💧",
                "components": ["liquidity_metrics", "efficiency_metrics", "working_capital_analysis"]
            },
            "leverage_panel": {
                "title": "Leverage & Risk",
                "icon": "⚖️",
                "components": ["leverage_metrics", "debt_analysis", "risk_indicators"]
            },
            "valuation_panel": {
                "title": "Valuation Metrics",
                "icon": "💰",
                "components": ["valuation_ratios", "peer_comparison", "historical_valuation"]
            },
            "growth_panel": {
                "title": "Growth Analysis",
                "icon": "🚀",
                "components": ["growth_metrics", "growth_trends", "growth_forecasts"]
            },
            "comparison_panel": {
                "title": "Peer Comparison",
                "icon": "📊",
                "components": ["peer_metrics", "industry_benchmarks", "relative_performance"]
            },
            "alerts_panel": {
                "title": "Alerts & Insights",
                "icon": "🚨",
                "components": ["metric_alerts", "trend_alerts", "anomaly_detection"]
            }
        }

    def get_metrics_by_category(self, category: str) -> Dict[str, MetricDefinition]:
        """Get all metrics for a specific category"""
        return {
            key: metric for key, metric in self.metric_definitions.items()
            if metric.category == category
        }

    def get_panel_configuration(self, panel_name: str) -> Dict:
        """Get configuration for a specific panel"""
        return self.component_hierarchy.get(panel_name, {})


class MetricDisplayComponents:
    """Components for displaying financial metrics"""

    def __init__(self, hierarchy: FinancialMetricsHierarchy):
        self.hierarchy = hierarchy

    def render_metric_card(self, metric_key: str, metric_value: MetricValue) -> None:
        """Render a single metric card with value, trend, and comparison"""
        metric_def = self.hierarchy.metric_definitions.get(metric_key)
        if not metric_def:
            st.error(f"Metric definition not found: {metric_key}")
            return

        # Determine trend color and icon
        trend_color, trend_icon = self._get_trend_indicators(metric_value.trend)

        # Calculate percentage change if previous value exists
        change_text = ""
        if metric_value.previous is not None:
            change = ((metric_value.current - metric_value.previous) / metric_value.previous) * 100
            change_text = f"{change:+.1f}%"

        # Format the current value
        if metric_def.unit == "%":
            formatted_value = f"{metric_value.current:.1f}%"
        else:
            formatted_value = metric_def.format_string.format(metric_value.current)

        # Create the metric card
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.metric(
                label=f"{metric_def.icon} {metric_def.name}",
                value=formatted_value,
                delta=change_text if change_text else None
            )

        with col2:
            if metric_value.benchmark is not None:
                benchmark_formatted = metric_def.format_string.format(metric_value.benchmark)
                if metric_def.unit == "%":
                    benchmark_formatted = f"{metric_value.benchmark:.1f}%"
                st.caption(f"Industry: {benchmark_formatted}")

        with col3:
            # Confidence indicator
            confidence_color = "green" if metric_value.confidence > 0.8 else "orange" if metric_value.confidence > 0.5 else "red"
            st.markdown(f"<span style='color: {confidence_color}'>●</span> {metric_value.confidence:.0%}", unsafe_allow_html=True)

        # Add description in expandable section
        with st.expander(f"ℹ️ About {metric_def.name}"):
            st.write(metric_def.description)
            st.write(f"**Formula:** {metric_def.formula}")
            if metric_def.threshold_good is not None:
                st.write(f"**Good:** ≥ {metric_def.threshold_good}{metric_def.unit}")
            if metric_def.threshold_warning is not None:
                st.write(f"**Warning:** < {metric_def.threshold_warning}{metric_def.unit}")

    def render_metrics_panel(self, panel_name: str, metrics_data: Dict[str, MetricValue]) -> None:
        """Render a complete metrics panel"""
        panel_config = self.hierarchy.get_panel_configuration(panel_name)
        if not panel_config:
            st.error(f"Panel configuration not found: {panel_name}")
            return

        st.subheader(f"{panel_config['icon']} {panel_config['title']}")

        # Get relevant metrics for this panel
        if "profitability" in panel_name:
            relevant_metrics = self.hierarchy.get_metrics_by_category("profitability")
        elif "liquidity" in panel_name:
            relevant_metrics = self.hierarchy.get_metrics_by_category("liquidity")
        elif "leverage" in panel_name:
            relevant_metrics = self.hierarchy.get_metrics_by_category("leverage")
        elif "valuation" in panel_name:
            relevant_metrics = self.hierarchy.get_metrics_by_category("valuation")
        elif "growth" in panel_name:
            relevant_metrics = self.hierarchy.get_metrics_by_category("growth")
        else:
            relevant_metrics = {}

        # Render metrics in a grid
        if relevant_metrics:
            # Create columns for metric cards
            num_cols = min(len(relevant_metrics), 3)
            cols = st.columns(num_cols)

            for idx, (metric_key, metric_def) in enumerate(relevant_metrics.items()):
                if metric_key in metrics_data:
                    with cols[idx % num_cols]:
                        self.render_metric_card(metric_key, metrics_data[metric_key])

    def render_trends_chart(self, metrics_history: Dict[str, List[Dict]]) -> None:
        """Render trends chart for multiple metrics over time"""
        if not metrics_history:
            st.warning("No historical data available for trends chart")
            return

        fig = make_subplots(
            rows=len(metrics_history),
            cols=1,
            subplot_titles=list(metrics_history.keys()),
            vertical_spacing=0.1
        )

        for idx, (metric_name, history) in enumerate(metrics_history.items(), 1):
            dates = [item['date'] for item in history]
            values = [item['value'] for item in history]

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=metric_name,
                    line=dict(width=2)
                ),
                row=idx, col=1
            )

        fig.update_layout(
            height=400 * len(metrics_history),
            showlegend=True,
            title="Financial Metrics Trends"
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_comparison_chart(self, comparison_data: Dict[str, Dict[str, float]]) -> None:
        """Render peer comparison chart"""
        if not comparison_data:
            st.warning("No comparison data available")
            return

        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(comparison_data).T
        df.index.name = 'Company'
        df = df.reset_index()

        # Create comparison chart
        fig = px.bar(
            df.melt(id_vars=['Company'], var_name='Metric', value_name='Value'),
            x='Company',
            y='Value',
            color='Metric',
            barmode='group',
            title="Peer Comparison"
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _get_trend_indicators(self, trend: str) -> tuple:
        """Get color and icon for trend indicators"""
        indicators = {
            "positive": ("green", "📈"),
            "negative": ("red", "📉"),
            "neutral": ("gray", "➡️")
        }
        return indicators.get(trend, indicators["neutral"])

    def render_alerts_panel(self, alerts: List[Dict]) -> None:
        """Render alerts and notifications panel"""
        st.subheader("🚨 Alerts & Insights")

        if not alerts:
            st.info("No alerts at this time")
            return

        for alert in alerts:
            alert_type = alert.get('type', 'info')
            message = alert.get('message', '')
            metric = alert.get('metric', '')

            if alert_type == 'warning':
                st.warning(f"⚠️ **{metric}**: {message}")
            elif alert_type == 'error':
                st.error(f"❌ **{metric}**: {message}")
            elif alert_type == 'success':
                st.success(f"✅ **{metric}**: {message}")
            else:
                st.info(f"ℹ️ **{metric}**: {message}")


def create_metric_card(title: str, value: Union[str, float], delta: Optional[str] = None,
                      delta_color: str = "normal", help_text: Optional[str] = None) -> None:
    """Create a metric card component"""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def create_info_card(title: str, content: str, icon: str = "ℹ️") -> None:
    """Create an information card component"""
    with st.container():
        st.markdown(f"### {icon} {title}")
        st.markdown(content)


def create_sample_metrics_data() -> Dict[str, MetricValue]:
    """Create sample metrics data for testing"""
    return {
        "roe": MetricValue(current=15.2, previous=13.8, benchmark=12.5, trend="positive", confidence=0.9),
        "roa": MetricValue(current=8.1, previous=7.5, benchmark=6.8, trend="positive", confidence=0.85),
        "current_ratio": MetricValue(current=2.1, previous=2.3, benchmark=1.8, trend="negative", confidence=0.95),
        "debt_to_equity": MetricValue(current=0.45, previous=0.52, benchmark=0.6, trend="positive", confidence=0.8),
        "pe_ratio": MetricValue(current=18.5, previous=16.2, benchmark=20.1, trend="positive", confidence=0.7),
        "revenue_growth": MetricValue(current=12.3, previous=8.7, benchmark=10.5, trend="positive", confidence=0.9)
    }


if __name__ == "__main__":
    # Example usage
    st.set_page_config(page_title="Financial Metrics Components", layout="wide")

    st.title("📊 Financial Metrics Dashboard Components")

    # Initialize hierarchy and components
    hierarchy = FinancialMetricsHierarchy()
    components = MetricDisplayComponents(hierarchy)

    # Create sample data
    sample_data = create_sample_metrics_data()

    # Render sample panels
    st.header("Sample Panels")

    col1, col2 = st.columns(2)

    with col1:
        components.render_metrics_panel("profitability_panel", sample_data)

    with col2:
        components.render_metrics_panel("liquidity_panel", sample_data)

    # Show hierarchy structure
    with st.expander("🏗️ Component Hierarchy"):
        st.json(hierarchy.component_hierarchy)