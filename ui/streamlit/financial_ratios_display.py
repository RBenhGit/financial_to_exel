"""
Financial Ratios Display Component for Advanced Dashboard
========================================================

This module provides comprehensive financial ratio display components
with real-time calculation, formatting, and industry benchmarking.
Integrates with the existing FinancialCalculator and dashboard components.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import logging

# Import existing components
from ui.streamlit.dashboard_components import (
    FinancialMetricsHierarchy,
    MetricDisplayComponents,
    MetricDefinition,
    MetricValue
)

logger = logging.getLogger(__name__)


class FinancialRatiosCalculator:
    """Calculate financial ratios from FinancialCalculator data"""

    def __init__(self, financial_calculator):
        """Initialize with FinancialCalculator instance"""
        self.calc = financial_calculator

    def calculate_all_ratios(self) -> Dict[str, MetricValue]:
        """Calculate all financial ratios and return as MetricValue objects"""
        try:
            # Get formatted metrics from FinancialCalculator
            metrics = self.calc.get_financial_metrics()

            if 'error' in metrics:
                logger.error(f"Error in financial metrics calculation: {metrics['error']}")
                return {}

            # Extract data sections
            profitability = metrics.get('profitability', {})
            efficiency = metrics.get('efficiency', {})
            liquidity = metrics.get('liquidity', {})
            leverage = metrics.get('leverage', {})
            growth = metrics.get('growth', {})

            ratios = {}

            # Profitability Ratios
            ratios.update(self._process_profitability_ratios(profitability))

            # Efficiency Ratios
            ratios.update(self._process_efficiency_ratios(efficiency))

            # Liquidity Ratios
            ratios.update(self._process_liquidity_ratios(liquidity))

            # Leverage Ratios
            ratios.update(self._process_leverage_ratios(leverage))

            # Growth Ratios
            ratios.update(self._process_growth_ratios(growth))

            # Valuation Ratios (from raw metrics)
            ratios.update(self._calculate_valuation_ratios(metrics))

            logger.info(f"Successfully calculated {len(ratios)} financial ratios")
            return ratios

        except Exception as e:
            logger.error(f"Error calculating financial ratios: {e}")
            return {}

    def _process_profitability_ratios(self, profitability: Dict) -> Dict[str, MetricValue]:
        """Process profitability ratios"""
        ratios = {}

        # ROE (Return on Equity)
        if 'roe' in profitability:
            roe_values = profitability['roe']
            if roe_values and len(roe_values) > 0:
                current = roe_values[-1] * 100  # Convert to percentage
                previous = roe_values[-2] * 100 if len(roe_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['roe'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=15.0,  # Industry benchmark
                    trend=trend,
                    confidence=0.9
                )

        # ROA (Return on Assets)
        if 'roa' in profitability:
            roa_values = profitability['roa']
            if roa_values and len(roa_values) > 0:
                current = roa_values[-1] * 100
                previous = roa_values[-2] * 100 if len(roa_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['roa'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=8.0,
                    trend=trend,
                    confidence=0.9
                )

        # Gross Margin
        if 'gross_margin' in profitability:
            margin_values = profitability['gross_margin']
            if margin_values and len(margin_values) > 0:
                current = margin_values[-1] * 100
                previous = margin_values[-2] * 100 if len(margin_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['gross_margin'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=40.0,
                    trend=trend,
                    confidence=0.95
                )

        # Operating Margin
        if 'operating_margin' in profitability:
            margin_values = profitability['operating_margin']
            if margin_values and len(margin_values) > 0:
                current = margin_values[-1] * 100
                previous = margin_values[-2] * 100 if len(margin_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['operating_margin'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=20.0,
                    trend=trend,
                    confidence=0.9
                )

        # Net Margin
        if 'net_margin' in profitability:
            margin_values = profitability['net_margin']
            if margin_values and len(margin_values) > 0:
                current = margin_values[-1] * 100
                previous = margin_values[-2] * 100 if len(margin_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['net_margin'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=15.0,
                    trend=trend,
                    confidence=0.85
                )

        return ratios

    def _process_efficiency_ratios(self, efficiency: Dict) -> Dict[str, MetricValue]:
        """Process efficiency ratios"""
        ratios = {}

        # Asset Turnover
        if 'asset_turnover' in efficiency:
            turnover_values = efficiency['asset_turnover']
            if turnover_values and len(turnover_values) > 0:
                current = turnover_values[-1]
                previous = turnover_values[-2] if len(turnover_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['asset_turnover'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=1.0,
                    trend=trend,
                    confidence=0.8
                )

        # Inventory Turnover
        if 'inventory_turnover' in efficiency:
            turnover_values = efficiency['inventory_turnover']
            if turnover_values and len(turnover_values) > 0:
                current = turnover_values[-1]
                previous = turnover_values[-2] if len(turnover_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['inventory_turnover'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=6.0,
                    trend=trend,
                    confidence=0.75
                )

        return ratios

    def _process_liquidity_ratios(self, liquidity: Dict) -> Dict[str, MetricValue]:
        """Process liquidity ratios"""
        ratios = {}

        # Current Ratio
        if 'current_ratio' in liquidity:
            ratio_values = liquidity['current_ratio']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['current_ratio'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=2.0,
                    trend=trend,
                    confidence=0.9
                )

        # Quick Ratio
        if 'quick_ratio' in liquidity:
            ratio_values = liquidity['quick_ratio']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['quick_ratio'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=1.0,
                    trend=trend,
                    confidence=0.85
                )

        return ratios

    def _process_leverage_ratios(self, leverage: Dict) -> Dict[str, MetricValue]:
        """Process leverage ratios"""
        ratios = {}

        # Debt-to-Equity
        if 'debt_to_equity' in leverage:
            ratio_values = leverage['debt_to_equity']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                # For debt ratios, lower is better, so invert trend logic
                trend = self._determine_trend(current, previous, invert=True)

                ratios['debt_to_equity'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=0.5,
                    trend=trend,
                    confidence=0.8
                )

        # Interest Coverage
        if 'interest_coverage' in leverage:
            coverage_values = leverage['interest_coverage']
            if coverage_values and len(coverage_values) > 0:
                current = coverage_values[-1]
                previous = coverage_values[-2] if len(coverage_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['interest_coverage'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=5.0,
                    trend=trend,
                    confidence=0.75
                )

        return ratios

    def _process_growth_ratios(self, growth: Dict) -> Dict[str, MetricValue]:
        """Process growth ratios"""
        ratios = {}

        # Revenue Growth
        if 'revenue_growth' in growth:
            growth_values = growth['revenue_growth']
            if growth_values and len(growth_values) > 0:
                current = growth_values[-1] * 100  # Convert to percentage
                previous = growth_values[-2] * 100 if len(growth_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['revenue_growth'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=10.0,
                    trend=trend,
                    confidence=0.7
                )

        # FCF Growth
        if 'fcf_growth' in growth:
            growth_values = growth['fcf_growth']
            if growth_values and len(growth_values) > 0:
                current = growth_values[-1] * 100
                previous = growth_values[-2] * 100 if len(growth_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['fcf_growth'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=10.0,
                    trend=trend,
                    confidence=0.6
                )

        return ratios

    def _calculate_valuation_ratios(self, metrics: Dict) -> Dict[str, MetricValue]:
        """Calculate valuation ratios using price data"""
        ratios = {}

        try:
            # Get current price if available
            company_info = metrics.get('company_info', {})
            ticker = company_info.get('ticker', '')

            if ticker:
                # Try to get current price from price service or calculation
                current_price = self._get_current_price(ticker)

                if current_price:
                    # Calculate P/E ratio if we have earnings per share
                    raw_metrics = metrics.get('raw_metrics', {})

                    # P/E Ratio calculation
                    net_income_values = raw_metrics.get('net_income', [])
                    shares_outstanding = self._get_shares_outstanding()

                    if net_income_values and shares_outstanding:
                        latest_net_income = net_income_values[-1]
                        eps = latest_net_income / shares_outstanding

                        if eps > 0:
                            pe_ratio = current_price / eps
                            ratios['pe_ratio'] = MetricValue(
                                current=pe_ratio,
                                benchmark=20.0,
                                trend="neutral",
                                confidence=0.7
                            )

                    # P/B Ratio calculation
                    book_value_values = raw_metrics.get('book_value_per_share', [])
                    if book_value_values:
                        latest_bvps = book_value_values[-1]
                        if latest_bvps > 0:
                            pb_ratio = current_price / latest_bvps
                            ratios['pb_ratio'] = MetricValue(
                                current=pb_ratio,
                                benchmark=1.5,
                                trend="neutral",
                                confidence=0.8
                            )

        except Exception as e:
            logger.warning(f"Error calculating valuation ratios: {e}")

        return ratios

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current stock price (placeholder for price service integration)"""
        try:
            # This would integrate with your existing price service
            # For now, return None to avoid errors
            return None
        except:
            return None

    def _get_shares_outstanding(self) -> Optional[float]:
        """Get shares outstanding from financial data"""
        try:
            # Try to get from financial calculator
            if hasattr(self.calc, 'financial_data') and self.calc.financial_data:
                balance_sheet = self.calc.financial_data.get('balance_sheet', {})
                if balance_sheet:
                    # Look for shares outstanding in common places
                    for key in ['shares_outstanding', 'common_shares_outstanding', 'weighted_average_shares']:
                        if key in balance_sheet:
                            shares_data = balance_sheet[key]
                            if shares_data and len(shares_data) > 0:
                                return shares_data[-1]  # Latest value
            return None
        except:
            return None

    def _determine_trend(self, current: Optional[float], previous: Optional[float], invert: bool = False) -> str:
        """Determine trend direction based on current vs previous values"""
        if current is None or previous is None:
            return "neutral"

        if current > previous:
            return "negative" if invert else "positive"
        elif current < previous:
            return "positive" if invert else "negative"
        else:
            return "neutral"


class AdvancedFinancialRatiosDisplay:
    """Advanced display component for financial ratios with enhanced features"""

    def __init__(self):
        self.hierarchy = FinancialMetricsHierarchy()
        self.components = MetricDisplayComponents(self.hierarchy)

    def render_complete_ratios_dashboard(self, financial_calculator) -> None:
        """Render complete financial ratios dashboard"""
        st.header("📊 Advanced Financial Ratios Dashboard")

        try:
            # Calculate all ratios
            calculator = FinancialRatiosCalculator(financial_calculator)
            ratios_data = calculator.calculate_all_ratios()

            if not ratios_data:
                st.error("Unable to calculate financial ratios. Please ensure financial data is loaded.")
                return

            # Create tabs for different ratio categories
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📈 Profitability",
                "⚡ Efficiency",
                "💧 Liquidity",
                "⚖️ Leverage",
                "🚀 Growth",
                "📊 Overview"
            ])

            with tab1:
                self._render_profitability_ratios(ratios_data)

            with tab2:
                self._render_efficiency_ratios(ratios_data)

            with tab3:
                self._render_liquidity_ratios(ratios_data)

            with tab4:
                self._render_leverage_ratios(ratios_data)

            with tab5:
                self._render_growth_ratios(ratios_data)

            with tab6:
                self._render_overview_dashboard(ratios_data)

        except Exception as e:
            st.error(f"Error rendering financial ratios dashboard: {e}")
            logger.error(f"Dashboard rendering error: {e}")

    def _render_profitability_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render profitability ratios section"""
        st.subheader("📈 Profitability Analysis")

        profitability_ratios = ['roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin']
        available_ratios = {k: v for k, v in ratios_data.items() if k in profitability_ratios}

        if available_ratios:
            # Create metrics grid
            cols = st.columns(min(len(available_ratios), 3))

            for idx, (ratio_key, ratio_value) in enumerate(available_ratios.items()):
                with cols[idx % 3]:
                    self.components.render_metric_card(ratio_key, ratio_value)

            # Add profitability trend chart
            self._render_ratios_trend_chart(available_ratios, "Profitability Trends")
        else:
            st.warning("No profitability ratios available")

    def _render_efficiency_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render efficiency ratios section"""
        st.subheader("⚡ Efficiency Analysis")

        efficiency_ratios = ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
        available_ratios = {k: v for k, v in ratios_data.items() if k in efficiency_ratios}

        if available_ratios:
            cols = st.columns(len(available_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)
        else:
            st.info("Efficiency ratios data not available")

    def _render_liquidity_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render liquidity ratios section"""
        st.subheader("💧 Liquidity Analysis")

        liquidity_ratios = ['current_ratio', 'quick_ratio', 'cash_ratio']
        available_ratios = {k: v for k, v in ratios_data.items() if k in liquidity_ratios}

        if available_ratios:
            cols = st.columns(len(available_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)

            # Add liquidity health indicator
            self._render_liquidity_health_indicator(available_ratios)
        else:
            st.info("Liquidity ratios data not available")

    def _render_leverage_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render leverage ratios section"""
        st.subheader("⚖️ Leverage & Risk Analysis")

        leverage_ratios = ['debt_to_equity', 'debt_to_assets', 'interest_coverage']
        available_ratios = {k: v for k, v in ratios_data.items() if k in leverage_ratios}

        if available_ratios:
            cols = st.columns(len(available_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)
        else:
            st.info("Leverage ratios data not available")

    def _render_growth_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render growth ratios section"""
        st.subheader("🚀 Growth Analysis")

        growth_ratios = ['revenue_growth', 'earnings_growth', 'fcf_growth']
        available_ratios = {k: v for k, v in ratios_data.items() if k in growth_ratios}

        if available_ratios:
            cols = st.columns(len(available_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)
        else:
            st.info("Growth ratios data not available")

    def _render_overview_dashboard(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render overview dashboard with key metrics"""
        st.subheader("📊 Financial Health Overview")

        if ratios_data:
            # Create financial health score
            health_score = self._calculate_financial_health_score(ratios_data)

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.metric(
                    label="📈 Financial Health Score",
                    value=f"{health_score:.1f}/100",
                    delta=self._get_health_score_interpretation(health_score)
                )

            with col2:
                # Key ratios summary
                st.write("**Key Ratios:**")
                key_ratios = ['roe', 'current_ratio', 'debt_to_equity']
                for ratio in key_ratios:
                    if ratio in ratios_data:
                        metric_def = self.hierarchy.metric_definitions.get(ratio)
                        if metric_def:
                            value = ratios_data[ratio].current
                            if metric_def.unit == "%":
                                st.write(f"• {metric_def.name}: {value:.1f}%")
                            else:
                                st.write(f"• {metric_def.name}: {value:.2f}")

            with col3:
                # Risk indicators
                self._render_risk_indicators(ratios_data)

            # Comprehensive ratios table
            self._render_ratios_summary_table(ratios_data)
        else:
            st.warning("No financial ratios data available for overview")

    def _render_ratios_trend_chart(self, ratios_data: Dict[str, MetricValue], title: str) -> None:
        """Render trend chart for ratios"""
        if len(ratios_data) == 0:
            return

        # Create a simple comparison chart showing current vs benchmark
        ratio_names = []
        current_values = []
        benchmark_values = []

        for ratio_key, ratio_value in ratios_data.items():
            metric_def = self.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                ratio_names.append(metric_def.name)
                current_values.append(ratio_value.current)
                benchmark_values.append(ratio_value.benchmark if ratio_value.benchmark else 0)

        if ratio_names:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Current',
                x=ratio_names,
                y=current_values,
                marker_color='lightblue'
            ))

            fig.add_trace(go.Bar(
                name='Benchmark',
                x=ratio_names,
                y=benchmark_values,
                marker_color='orange'
            ))

            fig.update_layout(
                title=title,
                barmode='group',
                height=400,
                yaxis_title='Value'
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_liquidity_health_indicator(self, liquidity_ratios: Dict[str, MetricValue]) -> None:
        """Render liquidity health indicator"""
        if 'current_ratio' in liquidity_ratios:
            current_ratio = liquidity_ratios['current_ratio'].current

            if current_ratio >= 2.0:
                st.success("✅ Strong liquidity position")
            elif current_ratio >= 1.0:
                st.warning("⚠️ Adequate liquidity position")
            else:
                st.error("❌ Weak liquidity position")

    def _render_risk_indicators(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render risk indicators"""
        st.write("**Risk Indicators:**")

        risk_factors = []

        # Check debt levels
        if 'debt_to_equity' in ratios_data:
            debt_ratio = ratios_data['debt_to_equity'].current
            if debt_ratio > 1.0:
                risk_factors.append("High debt levels")

        # Check liquidity
        if 'current_ratio' in ratios_data:
            current_ratio = ratios_data['current_ratio'].current
            if current_ratio < 1.0:
                risk_factors.append("Low liquidity")

        # Check profitability
        if 'roe' in ratios_data:
            roe = ratios_data['roe'].current
            if roe < 10.0:
                risk_factors.append("Low profitability")

        if risk_factors:
            for factor in risk_factors:
                st.write(f"🔴 {factor}")
        else:
            st.write("🟢 No major risk factors")

    def _render_ratios_summary_table(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render comprehensive ratios summary table"""
        st.subheader("📋 Comprehensive Ratios Summary")

        table_data = []

        for ratio_key, ratio_value in ratios_data.items():
            metric_def = self.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                row = {
                    'Metric': metric_def.name,
                    'Category': metric_def.category.title(),
                    'Current': f"{ratio_value.current:.2f}{metric_def.unit}",
                    'Previous': f"{ratio_value.previous:.2f}{metric_def.unit}" if ratio_value.previous else "N/A",
                    'Benchmark': f"{ratio_value.benchmark:.2f}{metric_def.unit}" if ratio_value.benchmark else "N/A",
                    'Trend': ratio_value.trend.title(),
                    'Confidence': f"{ratio_value.confidence:.0%}"
                }
                table_data.append(row)

        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

    def _calculate_financial_health_score(self, ratios_data: Dict[str, MetricValue]) -> float:
        """Calculate overall financial health score (0-100)"""
        score = 0
        max_score = 0

        # Scoring weights
        weights = {
            'roe': 20,
            'roa': 15,
            'current_ratio': 15,
            'debt_to_equity': 15,
            'gross_margin': 10,
            'operating_margin': 10,
            'net_margin': 10,
            'revenue_growth': 5
        }

        for ratio_key, weight in weights.items():
            max_score += weight

            if ratio_key in ratios_data:
                ratio_value = ratios_data[ratio_key]
                metric_def = self.hierarchy.metric_definitions.get(ratio_key)

                if metric_def and metric_def.threshold_good:
                    # Score based on how well it meets thresholds
                    if ratio_value.current >= metric_def.threshold_good:
                        score += weight
                    elif metric_def.threshold_warning and ratio_value.current >= metric_def.threshold_warning:
                        score += weight * 0.5

        return (score / max_score * 100) if max_score > 0 else 0

    def _get_health_score_interpretation(self, score: float) -> str:
        """Get interpretation of health score"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"


def create_ratios_dashboard_demo():
    """Create demo of ratios dashboard"""
    st.set_page_config(page_title="Financial Ratios Dashboard", layout="wide")

    st.title("📊 Advanced Financial Ratios Dashboard")
    st.markdown("---")

    # Create demo data (this would normally come from FinancialCalculator)
    class MockFinancialCalculator:
        def get_financial_metrics(self):
            return {
                'profitability': {
                    'roe': [0.12, 0.15, 0.18],
                    'roa': [0.08, 0.09, 0.11],
                    'gross_margin': [0.35, 0.38, 0.42],
                    'operating_margin': [0.18, 0.20, 0.22],
                    'net_margin': [0.12, 0.14, 0.16]
                },
                'liquidity': {
                    'current_ratio': [1.8, 2.1, 2.3],
                    'quick_ratio': [1.2, 1.4, 1.6]
                },
                'leverage': {
                    'debt_to_equity': [0.6, 0.5, 0.4],
                    'interest_coverage': [8.0, 9.5, 11.2]
                },
                'growth': {
                    'revenue_growth': [0.08, 0.12, 0.15],
                    'fcf_growth': [0.05, 0.10, 0.18]
                },
                'company_info': {
                    'name': 'Demo Company',
                    'ticker': 'DEMO'
                }
            }

    # Initialize display
    display = AdvancedFinancialRatiosDisplay()
    mock_calc = MockFinancialCalculator()

    # Render dashboard
    display.render_complete_ratios_dashboard(mock_calc)


if __name__ == "__main__":
    create_ratios_dashboard_demo()