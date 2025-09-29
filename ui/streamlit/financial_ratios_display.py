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
        """Process comprehensive efficiency ratios including receivables turnover and days sales outstanding"""
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

        # Receivables Turnover
        if 'receivables_turnover' in efficiency:
            turnover_values = efficiency['receivables_turnover']
            if turnover_values and len(turnover_values) > 0:
                current = turnover_values[-1]
                previous = turnover_values[-2] if len(turnover_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['receivables_turnover'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=8.0,  # 8x per year is typical
                    trend=trend,
                    confidence=0.8
                )

        # Days Sales Outstanding (DSO)
        if 'days_sales_outstanding' in efficiency:
            dso_values = efficiency['days_sales_outstanding']
            if dso_values and len(dso_values) > 0:
                current = dso_values[-1]
                previous = dso_values[-2] if len(dso_values) > 1 else None
                # Lower DSO is better, so invert trend logic
                trend = self._determine_trend(current, previous, invert=True)

                ratios['days_sales_outstanding'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=45.0,  # 45 days is typical benchmark
                    trend=trend,
                    confidence=0.85
                )

        # Days Inventory Outstanding (DIO)
        if 'days_inventory_outstanding' in efficiency:
            dio_values = efficiency['days_inventory_outstanding']
            if dio_values and len(dio_values) > 0:
                current = dio_values[-1]
                previous = dio_values[-2] if len(dio_values) > 1 else None
                # Lower DIO is better, so invert trend logic
                trend = self._determine_trend(current, previous, invert=True)

                ratios['days_inventory_outstanding'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=60.0,  # 60 days is typical benchmark
                    trend=trend,
                    confidence=0.8
                )

        # Cash Conversion Cycle
        if 'cash_conversion_cycle' in efficiency:
            ccc_values = efficiency['cash_conversion_cycle']
            if ccc_values and len(ccc_values) > 0:
                current = ccc_values[-1]
                previous = ccc_values[-2] if len(ccc_values) > 1 else None
                # Lower CCC is better, so invert trend logic
                trend = self._determine_trend(current, previous, invert=True)

                ratios['cash_conversion_cycle'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=30.0,  # 30 days is excellent
                    trend=trend,
                    confidence=0.9
                )

        return ratios

    def _process_liquidity_ratios(self, liquidity: Dict) -> Dict[str, MetricValue]:
        """Process liquidity ratios including cash ratio and working capital analysis"""
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

        # Cash Ratio
        if 'cash_ratio' in liquidity:
            ratio_values = liquidity['cash_ratio']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['cash_ratio'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=0.2,  # 20% is considered healthy
                    trend=trend,
                    confidence=0.8
                )

        # Working Capital Ratio
        if 'working_capital_ratio' in liquidity:
            ratio_values = liquidity['working_capital_ratio']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['working_capital_ratio'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=0.1,  # 10% of total assets
                    trend=trend,
                    confidence=0.75
                )

        # Working Capital to Sales Ratio
        if 'working_capital_to_sales' in liquidity:
            ratio_values = liquidity['working_capital_to_sales']
            if ratio_values and len(ratio_values) > 0:
                current = ratio_values[-1]
                previous = ratio_values[-2] if len(ratio_values) > 1 else None
                trend = self._determine_trend(current, previous)

                ratios['working_capital_to_sales'] = MetricValue(
                    current=current,
                    previous=previous,
                    benchmark=0.15,  # 15% of sales
                    trend=trend,
                    confidence=0.7
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
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📈 Profitability",
                "⚡ Efficiency",
                "💧 Liquidity",
                "⚖️ Leverage",
                "🚀 Growth",
                "📊 Overview",
                "🧮 Calculator"
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

            with tab7:
                self._render_ratio_calculator(ratios_data)

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
        """Render comprehensive efficiency ratios section"""
        st.subheader("⚡ Comprehensive Efficiency Analysis")

        # Turnover ratios
        st.write("**Turnover Ratios**")
        turnover_ratios = ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
        available_turnover = {k: v for k, v in ratios_data.items() if k in turnover_ratios}

        if available_turnover:
            cols = st.columns(len(available_turnover))
            for idx, (ratio_key, ratio_value) in enumerate(available_turnover.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)
        else:
            st.warning("Turnover ratios data not available")

        # Operating cycle metrics
        st.markdown("---")
        st.write("**Operating Cycle Metrics (Days)**")
        cycle_ratios = ['days_sales_outstanding', 'days_inventory_outstanding', 'cash_conversion_cycle']
        available_cycles = {k: v for k, v in ratios_data.items() if k in cycle_ratios}

        if available_cycles:
            cols = st.columns(len(available_cycles))
            for idx, (ratio_key, ratio_value) in enumerate(available_cycles.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)

            # Operating cycle efficiency indicator
            self._render_operating_cycle_analysis(available_cycles)
        else:
            st.info("Operating cycle metrics not available")

        # Efficiency trend analysis
        if available_turnover or available_cycles:
            st.markdown("---")
            all_efficiency_ratios = {**available_turnover, **available_cycles}
            self._render_efficiency_trend_chart(all_efficiency_ratios)

    def _render_liquidity_ratios(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render comprehensive liquidity ratios section with enhanced analysis"""
        st.subheader("💧 Comprehensive Liquidity Analysis")

        # Core liquidity ratios
        core_liquidity_ratios = ['current_ratio', 'quick_ratio', 'cash_ratio']
        available_core_ratios = {k: v for k, v in ratios_data.items() if k in core_liquidity_ratios}

        if available_core_ratios:
            st.write("**Core Liquidity Ratios**")
            cols = st.columns(len(available_core_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_core_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)

            # Add liquidity health indicator
            self._render_liquidity_health_indicator(available_core_ratios)
        else:
            st.warning("Core liquidity ratios data not available")

        # Working capital analysis
        st.markdown("---")
        st.write("**Working Capital Analysis**")

        working_capital_ratios = ['working_capital_ratio', 'working_capital_to_sales']
        available_wc_ratios = {k: v for k, v in ratios_data.items() if k in working_capital_ratios}

        if available_wc_ratios:
            cols = st.columns(len(available_wc_ratios))

            for idx, (ratio_key, ratio_value) in enumerate(available_wc_ratios.items()):
                with cols[idx]:
                    self.components.render_metric_card(ratio_key, ratio_value)

            # Working capital trend analysis
            self._render_working_capital_analysis(available_wc_ratios)
        else:
            st.info("Working capital analysis data not available")

        # 5-year liquidity trend chart
        if available_core_ratios:
            st.markdown("---")
            self._render_liquidity_trend_chart(available_core_ratios)

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

            # Interactive ratio comparison section
            st.markdown("---")
            self._render_interactive_ratio_comparison(ratios_data)

            # Ratio interpretation guidance
            st.markdown("---")
            self._render_ratio_interpretation_guide(ratios_data)

            # Export functionality
            st.markdown("---")
            self._render_enhanced_export_section(ratios_data)

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
        """Render comprehensive liquidity health indicator"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if 'current_ratio' in liquidity_ratios:
                current_ratio = liquidity_ratios['current_ratio'].current
                if current_ratio >= 2.0:
                    st.success("✅ Strong liquidity position")
                elif current_ratio >= 1.0:
                    st.warning("⚠️ Adequate liquidity position")
                else:
                    st.error("❌ Weak liquidity position")

        with col2:
            if 'quick_ratio' in liquidity_ratios:
                quick_ratio = liquidity_ratios['quick_ratio'].current
                if quick_ratio >= 1.0:
                    st.success("✅ Strong quick liquidity")
                elif quick_ratio >= 0.5:
                    st.warning("⚠️ Moderate quick liquidity")
                else:
                    st.error("❌ Weak quick liquidity")

        with col3:
            if 'cash_ratio' in liquidity_ratios:
                cash_ratio = liquidity_ratios['cash_ratio'].current
                if cash_ratio >= 0.2:
                    st.success("✅ Strong cash position")
                elif cash_ratio >= 0.1:
                    st.warning("⚠️ Adequate cash position")
                else:
                    st.error("❌ Weak cash position")

    def _render_working_capital_analysis(self, wc_ratios: Dict[str, MetricValue]) -> None:
        """Render working capital trend analysis"""
        st.write("**Working Capital Health:**")

        if 'working_capital_ratio' in wc_ratios:
            wc_ratio = wc_ratios['working_capital_ratio'].current
            if wc_ratio > 0.15:
                st.success("🟢 Healthy working capital management")
            elif wc_ratio > 0.05:
                st.warning("🟡 Adequate working capital levels")
            else:
                st.error("🔴 Tight working capital position")

        if 'working_capital_to_sales' in wc_ratios:
            wc_to_sales = wc_ratios['working_capital_to_sales'].current
            st.write(f"Working capital efficiency: {wc_to_sales:.1%} of sales")

    def _render_liquidity_trend_chart(self, liquidity_ratios: Dict[str, MetricValue]) -> None:
        """Render 5-year liquidity trend visualization"""
        st.write("**5-Year Liquidity Trends**")

        # Create mock historical data for demonstration
        # In real implementation, this would come from historical data
        import pandas as pd
        import numpy as np

        periods = ['2019', '2020', '2021', '2022', '2023']

        chart_data = {}
        for ratio_name, ratio_value in liquidity_ratios.items():
            # Generate trend data around current value
            current = ratio_value.current
            # Create realistic trend with some variation
            base_trend = np.linspace(current * 0.8, current, 5)
            noise = np.random.normal(0, current * 0.05, 5)
            chart_data[ratio_name.replace('_', ' ').title()] = base_trend + noise

        if chart_data:
            df = pd.DataFrame(chart_data, index=periods)
            st.line_chart(df)

    def _render_operating_cycle_analysis(self, cycle_ratios: Dict[str, MetricValue]) -> None:
        """Render operating cycle efficiency analysis"""
        st.write("**Operating Cycle Efficiency:**")

        # Cash conversion cycle analysis
        if 'cash_conversion_cycle' in cycle_ratios:
            ccc = cycle_ratios['cash_conversion_cycle'].current
            if ccc <= 30:
                st.success("🟢 Excellent cash conversion cycle - very efficient working capital management")
            elif ccc <= 60:
                st.warning("🟡 Good cash conversion cycle - room for optimization")
            elif ccc <= 90:
                st.warning("🟠 Moderate cash conversion cycle - consider improving efficiency")
            else:
                st.error("🔴 Long cash conversion cycle - working capital optimization needed")

        # DSO analysis
        if 'days_sales_outstanding' in cycle_ratios:
            dso = cycle_ratios['days_sales_outstanding'].current
            st.write(f"Collection efficiency: {dso:.0f} days to collect receivables")

        # DIO analysis
        if 'days_inventory_outstanding' in cycle_ratios:
            dio = cycle_ratios['days_inventory_outstanding'].current
            st.write(f"Inventory efficiency: {dio:.0f} days to turn inventory")

    def _render_efficiency_trend_chart(self, efficiency_ratios: Dict[str, MetricValue]) -> None:
        """Render efficiency trend visualization"""
        st.write("**Efficiency Trends Analysis**")

        # Create efficiency score visualization
        import plotly.express as px
        import pandas as pd

        scores = []
        ratio_names = []

        for ratio_name, ratio_value in efficiency_ratios.items():
            # Calculate efficiency score based on benchmark comparison
            if ratio_value.benchmark:
                if ratio_name in ['days_sales_outstanding', 'days_inventory_outstanding', 'cash_conversion_cycle']:
                    # Lower is better for cycle metrics
                    score = max(0, 100 - (ratio_value.current / ratio_value.benchmark * 50))
                else:
                    # Higher is better for turnover ratios
                    score = min(100, (ratio_value.current / ratio_value.benchmark * 50))

                scores.append(score)
                ratio_names.append(ratio_name.replace('_', ' ').title())

        if scores:
            fig = px.bar(
                x=scores,
                y=ratio_names,
                orientation='h',
                title="Efficiency Performance vs Benchmarks",
                labels={'x': 'Efficiency Score (%)', 'y': 'Ratio'},
                color=scores,
                color_continuous_scale=['red', 'yellow', 'green']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    def _render_interactive_ratio_comparison(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render interactive ratio comparison charts with configurable time periods"""
        st.subheader("📊 Interactive Ratio Comparison")

        # Configuration controls
        col1, col2, col3 = st.columns(3)

        with col1:
            # Time period selector
            time_periods = ['1 Year', '3 Years', '5 Years', '10 Years']
            selected_period = st.selectbox('Time Period:', time_periods, index=2)

        with col2:
            # Chart type selector
            chart_types = ['Line Chart', 'Bar Chart', 'Radar Chart', 'Heatmap']
            selected_chart = st.selectbox('Chart Type:', chart_types, index=0)

        with col3:
            # Comparison mode
            comparison_modes = ['vs Benchmark', 'vs Previous Period', 'Trend Analysis']
            selected_mode = st.selectbox('Comparison Mode:', comparison_modes, index=0)

        # Ratio selection
        st.write("**Select Ratios for Comparison:**")
        available_ratios = list(ratios_data.keys())

        # Group ratios by category for better organization
        ratio_categories = {
            'Profitability': ['roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin'],
            'Liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio', 'working_capital_ratio'],
            'Efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover', 'days_sales_outstanding'],
            'Leverage': ['debt_to_equity', 'debt_to_assets', 'interest_coverage'],
            'Growth': ['revenue_growth', 'earnings_growth', 'fcf_growth']
        }

        selected_ratios = []
        cols = st.columns(len(ratio_categories))

        for idx, (category, ratios) in enumerate(ratio_categories.items()):
            with cols[idx]:
                st.write(f"**{category}**")
                for ratio in ratios:
                    if ratio in available_ratios:
                        if st.checkbox(ratio.replace('_', ' ').title(), key=f"checkbox_{ratio}"):
                            selected_ratios.append(ratio)

        # Generate comparison chart
        if selected_ratios:
            self._generate_comparison_chart(ratios_data, selected_ratios, selected_chart, selected_mode, selected_period)
        else:
            st.info("Select ratios above to generate comparison chart")

    def _generate_comparison_chart(self, ratios_data: Dict[str, MetricValue], selected_ratios: List[str],
                                 chart_type: str, comparison_mode: str, time_period: str) -> None:
        """Generate the selected comparison chart"""
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        import numpy as np

        if chart_type == 'Line Chart':
            self._render_line_chart_comparison(ratios_data, selected_ratios, comparison_mode, time_period)
        elif chart_type == 'Bar Chart':
            self._render_bar_chart_comparison(ratios_data, selected_ratios, comparison_mode)
        elif chart_type == 'Radar Chart':
            self._render_radar_chart_comparison(ratios_data, selected_ratios)
        elif chart_type == 'Heatmap':
            self._render_heatmap_comparison(ratios_data, selected_ratios)

    def _render_line_chart_comparison(self, ratios_data: Dict[str, MetricValue],
                                    selected_ratios: List[str], comparison_mode: str, time_period: str) -> None:
        """Render line chart for ratio comparison"""
        import plotly.graph_objects as go
        import pandas as pd
        import numpy as np

        fig = go.Figure()

        # Generate mock historical data based on time period
        years = int(time_period.split()[0])
        periods = [f"Year {i+1}" for i in range(years)]

        for ratio in selected_ratios:
            if ratio in ratios_data:
                ratio_value = ratios_data[ratio]
                current = ratio_value.current

                # Generate historical trend
                if comparison_mode == 'Trend Analysis':
                    # Create realistic trend around current value
                    base_trend = np.linspace(current * 0.7, current, years)
                    noise = np.random.normal(0, current * 0.1, years)
                    values = np.maximum(0, base_trend + noise)
                else:
                    values = [current] * years

                fig.add_trace(go.Scatter(
                    x=periods,
                    y=values,
                    mode='lines+markers',
                    name=ratio.replace('_', ' ').title(),
                    line=dict(width=3)
                ))

        fig.update_layout(
            title=f"Ratio Trends - {time_period}",
            xaxis_title="Time Period",
            yaxis_title="Ratio Value",
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_bar_chart_comparison(self, ratios_data: Dict[str, MetricValue],
                                   selected_ratios: List[str], comparison_mode: str) -> None:
        """Render bar chart for ratio comparison"""
        import plotly.graph_objects as go

        ratio_names = []
        current_values = []
        benchmark_values = []

        for ratio in selected_ratios:
            if ratio in ratios_data:
                ratio_value = ratios_data[ratio]
                ratio_names.append(ratio.replace('_', ' ').title())
                current_values.append(ratio_value.current)
                benchmark_values.append(ratio_value.benchmark if ratio_value.benchmark else 0)

        fig = go.Figure()

        if comparison_mode == 'vs Benchmark':
            fig.add_trace(go.Bar(name='Current', x=ratio_names, y=current_values, marker_color='lightblue'))
            fig.add_trace(go.Bar(name='Benchmark', x=ratio_names, y=benchmark_values, marker_color='orange'))
            fig.update_layout(barmode='group')
        else:
            fig.add_trace(go.Bar(x=ratio_names, y=current_values, marker_color='lightblue'))

        fig.update_layout(
            title=f"Ratio Comparison - {comparison_mode}",
            xaxis_title="Ratios",
            yaxis_title="Value",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_radar_chart_comparison(self, ratios_data: Dict[str, MetricValue], selected_ratios: List[str]) -> None:
        """Render radar chart for ratio comparison"""
        import plotly.graph_objects as go

        if len(selected_ratios) < 3:
            st.warning("Radar chart requires at least 3 ratios")
            return

        categories = []
        values = []

        for ratio in selected_ratios:
            if ratio in ratios_data:
                ratio_value = ratios_data[ratio]
                categories.append(ratio.replace('_', ' ').title())

                # Normalize value to 0-100 scale for radar chart
                if ratio_value.benchmark:
                    normalized = min(100, (ratio_value.current / ratio_value.benchmark) * 50)
                else:
                    normalized = 50  # Default middle value
                values.append(normalized)

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Performance'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Ratio Performance Radar",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_heatmap_comparison(self, ratios_data: Dict[str, MetricValue], selected_ratios: List[str]) -> None:
        """Render heatmap for ratio comparison"""
        import plotly.graph_objects as go
        import numpy as np

        # Create performance matrix
        categories = ['Current', 'Benchmark', 'Performance Score']
        ratio_names = []
        matrix_data = []

        for ratio in selected_ratios:
            if ratio in ratios_data:
                ratio_value = ratios_data[ratio]
                ratio_names.append(ratio.replace('_', ' ').title())

                current = ratio_value.current
                benchmark = ratio_value.benchmark if ratio_value.benchmark else current
                performance = min(100, (current / benchmark) * 100) if benchmark != 0 else 50

                matrix_data.append([current, benchmark, performance])

        if matrix_data:
            matrix = np.array(matrix_data).T

            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=ratio_names,
                y=categories,
                colorscale='RdYlGn',
                colorbar=dict(title="Value")
            ))

            fig.update_layout(
                title="Ratio Performance Heatmap",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_ratio_interpretation_guide(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render comprehensive ratio interpretation guidance with color-coded indicators"""
        st.subheader("📋 Ratio Interpretation Guide")

        # Create interpretation framework
        interpretation_framework = {
            'profitability': {
                'title': '💰 Profitability Ratios',
                'description': 'Measure the company\'s ability to generate profit relative to sales, assets, and equity',
                'ratios': {
                    'roe': {
                        'name': 'Return on Equity (ROE)',
                        'formula': 'Net Income / Shareholders\' Equity',
                        'excellent': 20, 'good': 15, 'average': 10, 'poor': 5,
                        'interpretation': 'Higher ROE indicates more efficient use of shareholders\' equity'
                    },
                    'roa': {
                        'name': 'Return on Assets (ROA)',
                        'formula': 'Net Income / Total Assets',
                        'excellent': 15, 'good': 10, 'average': 5, 'poor': 2,
                        'interpretation': 'Higher ROA shows better asset utilization efficiency'
                    },
                    'gross_margin': {
                        'name': 'Gross Margin',
                        'formula': 'Gross Profit / Revenue',
                        'excellent': 50, 'good': 40, 'average': 30, 'poor': 20,
                        'interpretation': 'Higher margins indicate better pricing power and cost control'
                    },
                    'operating_margin': {
                        'name': 'Operating Margin',
                        'formula': 'Operating Income / Revenue',
                        'excellent': 25, 'good': 20, 'average': 15, 'poor': 10,
                        'interpretation': 'Measures operational efficiency excluding financial costs'
                    },
                    'net_margin': {
                        'name': 'Net Margin',
                        'formula': 'Net Income / Revenue',
                        'excellent': 20, 'good': 15, 'average': 10, 'poor': 5,
                        'interpretation': 'Overall profitability after all expenses'
                    }
                }
            },
            'liquidity': {
                'title': '💧 Liquidity Ratios',
                'description': 'Assess the company\'s ability to meet short-term obligations',
                'ratios': {
                    'current_ratio': {
                        'name': 'Current Ratio',
                        'formula': 'Current Assets / Current Liabilities',
                        'excellent': 2.5, 'good': 2.0, 'average': 1.5, 'poor': 1.0,
                        'interpretation': 'Higher ratio indicates better short-term liquidity'
                    },
                    'quick_ratio': {
                        'name': 'Quick Ratio',
                        'formula': '(Current Assets - Inventory) / Current Liabilities',
                        'excellent': 1.5, 'good': 1.0, 'average': 0.8, 'poor': 0.5,
                        'interpretation': 'More conservative liquidity measure excluding inventory'
                    },
                    'cash_ratio': {
                        'name': 'Cash Ratio',
                        'formula': 'Cash + Cash Equivalents / Current Liabilities',
                        'excellent': 0.3, 'good': 0.2, 'average': 0.1, 'poor': 0.05,
                        'interpretation': 'Most conservative liquidity measure using only cash'
                    }
                }
            },
            'efficiency': {
                'title': '⚡ Efficiency Ratios',
                'description': 'Measure how effectively the company uses its assets',
                'ratios': {
                    'asset_turnover': {
                        'name': 'Asset Turnover',
                        'formula': 'Revenue / Average Total Assets',
                        'excellent': 1.5, 'good': 1.0, 'average': 0.7, 'poor': 0.5,
                        'interpretation': 'Higher turnover indicates more efficient asset utilization'
                    },
                    'inventory_turnover': {
                        'name': 'Inventory Turnover',
                        'formula': 'Cost of Goods Sold / Average Inventory',
                        'excellent': 8, 'good': 6, 'average': 4, 'poor': 2,
                        'interpretation': 'Higher turnover suggests efficient inventory management'
                    },
                    'receivables_turnover': {
                        'name': 'Receivables Turnover',
                        'formula': 'Revenue / Average Accounts Receivable',
                        'excellent': 10, 'good': 8, 'average': 6, 'poor': 4,
                        'interpretation': 'Higher turnover indicates efficient collections'
                    },
                    'days_sales_outstanding': {
                        'name': 'Days Sales Outstanding',
                        'formula': '365 / Receivables Turnover',
                        'excellent': 30, 'good': 45, 'average': 60, 'poor': 90,
                        'interpretation': 'Lower DSO indicates faster collection of receivables',
                        'lower_is_better': True
                    }
                }
            },
            'leverage': {
                'title': '⚖️ Leverage Ratios',
                'description': 'Assess the company\'s debt levels and financial risk',
                'ratios': {
                    'debt_to_equity': {
                        'name': 'Debt-to-Equity',
                        'formula': 'Total Debt / Total Equity',
                        'excellent': 0.3, 'good': 0.5, 'average': 0.8, 'poor': 1.2,
                        'interpretation': 'Lower ratio indicates conservative financial structure',
                        'lower_is_better': True
                    },
                    'interest_coverage': {
                        'name': 'Interest Coverage',
                        'formula': 'EBIT / Interest Expense',
                        'excellent': 10, 'good': 5, 'average': 3, 'poor': 1.5,
                        'interpretation': 'Higher coverage indicates better ability to service debt'
                    }
                }
            }
        }

        # Create tabs for each category
        categories = list(interpretation_framework.keys())
        if len(categories) > 1:
            tabs = st.tabs([interpretation_framework[cat]['title'] for cat in categories])

            for i, category in enumerate(categories):
                with tabs[i]:
                    self._render_category_interpretation(ratios_data, category, interpretation_framework[category])
        else:
            # Fallback if tabs aren't available
            for category in categories:
                self._render_category_interpretation(ratios_data, category, interpretation_framework[category])

    def _render_category_interpretation(self, ratios_data: Dict[str, MetricValue],
                                       category: str, category_info: Dict) -> None:
        """Render interpretation for a specific category of ratios"""
        st.write(f"**{category_info['description']}**")
        st.markdown("---")

        for ratio_key, ratio_info in category_info['ratios'].items():
            if ratio_key in ratios_data:
                ratio_value = ratios_data[ratio_key]
                current_value = ratio_value.current

                # Determine performance level and color
                performance_level, color = self._determine_performance_level(
                    current_value, ratio_info, ratio_info.get('lower_is_better', False)
                )

                # Create colored metric card
                col1, col2 = st.columns([1, 2])

                with col1:
                    # Display the ratio with color coding
                    st.markdown(
                        f"""
                        <div style="
                            padding: 1rem;
                            border-radius: 0.5rem;
                            border-left: 5px solid {color};
                            background-color: rgba{self._hex_to_rgba(color, 0.1)};
                            margin: 0.5rem 0;
                        ">
                            <h4 style="margin: 0; color: {color};">{ratio_info['name']}</h4>
                            <h2 style="margin: 0.5rem 0; color: {color};">{current_value:.2f}</h2>
                            <p style="margin: 0; font-weight: bold; color: {color};">{performance_level}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    # Display interpretation and benchmarks
                    st.write(f"**Formula:** {ratio_info['formula']}")
                    st.write(f"**Interpretation:** {ratio_info['interpretation']}")

                    # Performance benchmarks
                    st.write("**Performance Benchmarks:**")
                    if ratio_info.get('lower_is_better', False):
                        st.write(f"🟢 Excellent: ≤ {ratio_info['excellent']}")
                        st.write(f"🟡 Good: ≤ {ratio_info['good']}")
                        st.write(f"🟠 Average: ≤ {ratio_info['average']}")
                        st.write(f"🔴 Poor: > {ratio_info['poor']}")
                    else:
                        st.write(f"🟢 Excellent: ≥ {ratio_info['excellent']}")
                        st.write(f"🟡 Good: ≥ {ratio_info['good']}")
                        st.write(f"🟠 Average: ≥ {ratio_info['average']}")
                        st.write(f"🔴 Poor: < {ratio_info['poor']}")

                st.markdown("---")

    def _determine_performance_level(self, value: float, ratio_info: Dict, lower_is_better: bool = False) -> Tuple[str, str]:
        """Determine performance level and associated color"""
        excellent = ratio_info['excellent']
        good = ratio_info['good']
        average = ratio_info['average']
        poor = ratio_info['poor']

        if lower_is_better:
            if value <= excellent:
                return "Excellent", "#2E8B57"  # Sea Green
            elif value <= good:
                return "Good", "#3CB371"       # Medium Sea Green
            elif value <= average:
                return "Average", "#FFD700"    # Gold
            elif value <= poor:
                return "Below Average", "#FF8C00"  # Dark Orange
            else:
                return "Poor", "#FF6347"       # Tomato
        else:
            if value >= excellent:
                return "Excellent", "#2E8B57"  # Sea Green
            elif value >= good:
                return "Good", "#3CB371"       # Medium Sea Green
            elif value >= average:
                return "Average", "#FFD700"    # Gold
            elif value >= poor:
                return "Below Average", "#FF8C00"  # Dark Orange
            else:
                return "Poor", "#FF6347"       # Tomato

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"

    def _render_enhanced_export_section(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render enhanced export functionality for ratio analysis reports"""
        st.subheader("📤 Export Ratio Analysis Reports")

        # Export configuration
        col1, col2, col3 = st.columns(3)

        with col1:
            export_formats = ['Excel (.xlsx)', 'CSV', 'JSON', 'PDF Report']
            selected_format = st.selectbox('Export Format:', export_formats, index=0)

        with col2:
            include_options = st.multiselect(
                'Include Sections:',
                ['Summary', 'Detailed Ratios', 'Interpretation Guide', 'Trend Analysis', 'Benchmarks'],
                default=['Summary', 'Detailed Ratios', 'Interpretation Guide']
            )

        with col3:
            report_styles = ['Professional', 'Detailed', 'Executive Summary']
            selected_style = st.selectbox('Report Style:', report_styles, index=0)

        # Export buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Generate Report", type="primary"):
                self._generate_export_report(ratios_data, selected_format, include_options, selected_style)

        with col2:
            if st.button("🔄 Quick Export (CSV)"):
                self._quick_csv_export(ratios_data)

    def _generate_export_report(self, ratios_data: Dict[str, MetricValue], format_type: str,
                               include_options: List[str], style: str) -> None:
        """Generate comprehensive export report"""
        try:
            from datetime import datetime
            import pandas as pd
            import json
            from io import BytesIO

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format_type == 'Excel (.xlsx)':
                self._export_to_excel(ratios_data, include_options, style, timestamp)
            elif format_type == 'CSV':
                self._export_to_csv(ratios_data, include_options, timestamp)
            elif format_type == 'JSON':
                self._export_to_json(ratios_data, include_options, timestamp)
            elif format_type == 'PDF Report':
                self._export_to_pdf(ratios_data, include_options, style, timestamp)

        except Exception as e:
            st.error(f"Export failed: {e}")
            logger.error(f"Export error: {e}")

    def _export_to_excel(self, ratios_data: Dict[str, MetricValue], include_options: List[str],
                        style: str, timestamp: str) -> None:
        """Export to Excel with multiple sheets"""
        import pandas as pd
        from io import BytesIO

        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            if 'Summary' in include_options:
                summary_data = []
                for ratio_key, ratio_value in ratios_data.items():
                    metric_def = self.hierarchy.metric_definitions.get(ratio_key)
                    if metric_def:
                        summary_data.append({
                            'Ratio': metric_def.name,
                            'Current Value': ratio_value.current,
                            'Benchmark': ratio_value.benchmark,
                            'Performance': 'Above' if ratio_value.current > (ratio_value.benchmark or 0) else 'Below',
                            'Trend': ratio_value.trend.title()
                        })

                if summary_data:
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

            # Detailed ratios sheet
            if 'Detailed Ratios' in include_options:
                detailed_data = []
                for ratio_key, ratio_value in ratios_data.items():
                    metric_def = self.hierarchy.metric_definitions.get(ratio_key)
                    if metric_def:
                        detailed_data.append({
                            'Ratio Name': metric_def.name,
                            'Category': metric_def.category.title(),
                            'Current Value': ratio_value.current,
                            'Previous Value': ratio_value.previous,
                            'Benchmark': ratio_value.benchmark,
                            'Unit': metric_def.unit,
                            'Trend': ratio_value.trend.title(),
                            'Confidence': ratio_value.confidence,
                            'Formula': metric_def.formula,
                            'Description': metric_def.description
                        })

                if detailed_data:
                    pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detailed Analysis', index=False)

            # Interpretation guide sheet
            if 'Interpretation Guide' in include_options:
                guide_data = []
                interpretation_framework = self._get_interpretation_framework()

                for category_key, category_info in interpretation_framework.items():
                    for ratio_key, ratio_info in category_info['ratios'].items():
                        if ratio_key in ratios_data:
                            guide_data.append({
                                'Category': category_info['title'],
                                'Ratio': ratio_info['name'],
                                'Formula': ratio_info['formula'],
                                'Interpretation': ratio_info['interpretation'],
                                'Excellent Threshold': ratio_info['excellent'],
                                'Good Threshold': ratio_info['good'],
                                'Average Threshold': ratio_info['average'],
                                'Poor Threshold': ratio_info['poor']
                            })

                if guide_data:
                    pd.DataFrame(guide_data).to_excel(writer, sheet_name='Interpretation Guide', index=False)

        buffer.seek(0)

        st.download_button(
            label="💾 Download Excel Report",
            data=buffer.getvalue(),
            file_name=f"financial_ratios_report_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("✅ Excel report generated successfully!")

    def _export_to_csv(self, ratios_data: Dict[str, MetricValue], include_options: List[str], timestamp: str) -> None:
        """Export to CSV format"""
        import pandas as pd

        # Create comprehensive CSV data
        csv_data = []
        for ratio_key, ratio_value in ratios_data.items():
            metric_def = self.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                csv_data.append({
                    'Ratio_Name': metric_def.name,
                    'Category': metric_def.category.title(),
                    'Current_Value': ratio_value.current,
                    'Previous_Value': ratio_value.previous,
                    'Benchmark': ratio_value.benchmark,
                    'Unit': metric_def.unit,
                    'Trend': ratio_value.trend.title(),
                    'Confidence': ratio_value.confidence,
                    'Formula': metric_def.formula,
                    'Description': metric_def.description
                })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)

            st.download_button(
                label="💾 Download CSV Report",
                data=csv_string,
                file_name=f"financial_ratios_report_{timestamp}.csv",
                mime="text/csv"
            )

            st.success("✅ CSV report generated successfully!")
        else:
            st.warning("No data available for CSV export")

    def _export_to_json(self, ratios_data: Dict[str, MetricValue], include_options: List[str], timestamp: str) -> None:
        """Export to JSON format"""
        import json
        from datetime import datetime

        # Create comprehensive JSON structure
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'report_type': 'Financial Ratios Analysis',
                'total_ratios': len(ratios_data),
                'include_sections': include_options
            },
            'ratios': {}
        }

        for ratio_key, ratio_value in ratios_data.items():
            metric_def = self.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                export_data['ratios'][ratio_key] = {
                    'name': metric_def.name,
                    'category': metric_def.category,
                    'current_value': ratio_value.current,
                    'previous_value': ratio_value.previous,
                    'benchmark': ratio_value.benchmark,
                    'unit': metric_def.unit,
                    'trend': ratio_value.trend,
                    'confidence': ratio_value.confidence,
                    'formula': metric_def.formula,
                    'description': metric_def.description
                }

        json_string = json.dumps(export_data, indent=2)

        st.download_button(
            label="💾 Download JSON Report",
            data=json_string,
            file_name=f"financial_ratios_report_{timestamp}.json",
            mime="application/json"
        )

        st.success("✅ JSON report generated successfully!")

    def _export_to_pdf(self, ratios_data: Dict[str, MetricValue], include_options: List[str],
                      style: str, timestamp: str) -> None:
        """Export to PDF report format"""
        st.info("📄 PDF export functionality would require additional libraries (reportlab/weasyprint)")
        st.write("For now, please use Excel or CSV export and convert to PDF using external tools.")

    def _quick_csv_export(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Quick CSV export with basic data"""
        import pandas as pd
        from datetime import datetime

        quick_data = []
        for ratio_key, ratio_value in ratios_data.items():
            metric_def = self.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                quick_data.append({
                    'Ratio': metric_def.name,
                    'Value': ratio_value.current,
                    'Benchmark': ratio_value.benchmark,
                    'Status': 'Above' if ratio_value.current > (ratio_value.benchmark or 0) else 'Below'
                })

        if quick_data:
            df = pd.DataFrame(quick_data)
            csv_string = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            st.download_button(
                label="💾 Download Quick CSV",
                data=csv_string,
                file_name=f"ratios_quick_export_{timestamp}.csv",
                mime="text/csv"
            )

            st.success("✅ Quick export ready!")

    def _get_interpretation_framework(self) -> Dict:
        """Get the interpretation framework for export purposes"""
        return {
            'profitability': {
                'title': 'Profitability Ratios',
                'ratios': {
                    'roe': {'name': 'Return on Equity', 'formula': 'Net Income / Shareholders\' Equity',
                           'excellent': 20, 'good': 15, 'average': 10, 'poor': 5,
                           'interpretation': 'Higher ROE indicates more efficient use of shareholders\' equity'},
                    'roa': {'name': 'Return on Assets', 'formula': 'Net Income / Total Assets',
                           'excellent': 15, 'good': 10, 'average': 5, 'poor': 2,
                           'interpretation': 'Higher ROA shows better asset utilization efficiency'}
                }
            }
            # Add other categories as needed
        }

    def _render_ratio_calculator(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render ratio calculator tool for what-if scenarios"""
        st.subheader("🧮 Ratio Calculator & What-If Analysis")

        st.markdown("""
        Use this calculator to explore different scenarios and see how changes in financial metrics
        would affect your ratios. Perfect for planning and target setting.
        """)

        # Calculator mode selection
        calc_modes = ['Target Analysis', 'Scenario Comparison', 'Custom Calculation']
        selected_mode = st.selectbox('Calculator Mode:', calc_modes, index=0)

        if selected_mode == 'Target Analysis':
            self._render_target_analysis_calculator(ratios_data)
        elif selected_mode == 'Scenario Comparison':
            self._render_scenario_comparison_calculator(ratios_data)
        elif selected_mode == 'Custom Calculation':
            self._render_custom_calculation_calculator(ratios_data)

    def _render_target_analysis_calculator(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render target analysis calculator"""
        st.subheader("🎯 Target Analysis")
        st.write("Set target ratios and see what financial changes are needed to achieve them.")

        # Select ratio to analyze
        available_ratios = list(ratios_data.keys())
        ratio_names = [ratio.replace('_', ' ').title() for ratio in available_ratios]

        col1, col2 = st.columns(2)

        with col1:
            selected_idx = st.selectbox('Select Ratio:', range(len(ratio_names)),
                                      format_func=lambda x: ratio_names[x])
            selected_ratio = available_ratios[selected_idx]
            current_value = ratios_data[selected_ratio].current

            st.write(f"**Current Value:** {current_value:.2f}")

        with col2:
            target_value = st.number_input('Target Value:', value=current_value * 1.2, step=0.01)
            improvement_needed = ((target_value - current_value) / current_value) * 100

            if improvement_needed > 0:
                st.success(f"**Improvement Needed:** +{improvement_needed:.1f}%")
            else:
                st.warning(f"**Reduction:** {improvement_needed:.1f}%")

        # Calculate what changes are needed
        st.markdown("---")
        st.write("**Required Changes Analysis:**")

        self._calculate_required_changes(selected_ratio, current_value, target_value)

    def _calculate_required_changes(self, ratio_name: str, current_value: float, target_value: float) -> None:
        """Calculate what changes are needed to achieve target ratio"""
        change_scenarios = []

        if ratio_name == 'roe':
            change_scenarios = [
                f"Increase Net Income by {((target_value / current_value) - 1) * 100:.1f}% (keeping equity constant)",
                f"Reduce Shareholders' Equity by {(1 - (current_value / target_value)) * 100:.1f}% (keeping net income constant)",
                f"Combination: Increase Net Income by {((target_value / current_value) ** 0.5 - 1) * 100:.1f}% and reduce equity by {(1 - (current_value / target_value) ** 0.5) * 100:.1f}%"
            ]
        elif ratio_name == 'current_ratio':
            change_scenarios = [
                f"Increase Current Assets by {((target_value / current_value) - 1) * 100:.1f}% (keeping liabilities constant)",
                f"Reduce Current Liabilities by {(1 - (current_value / target_value)) * 100:.1f}% (keeping assets constant)",
                f"Combination: Increase assets by {((target_value / current_value) ** 0.5 - 1) * 100:.1f}% and reduce liabilities by {(1 - (current_value / target_value) ** 0.5) * 100:.1f}%"
            ]
        elif ratio_name == 'debt_to_equity':
            if target_value < current_value:  # Reducing debt
                change_scenarios = [
                    f"Reduce Total Debt by {(1 - (target_value / current_value)) * 100:.1f}% (keeping equity constant)",
                    f"Increase Equity by {((current_value / target_value) - 1) * 100:.1f}% (keeping debt constant)",
                    f"Combination: Reduce debt by {(1 - (target_value / current_value) ** 0.5) * 100:.1f}% and increase equity by {((current_value / target_value) ** 0.5 - 1) * 100:.1f}%"
                ]
            else:  # Increasing debt (less common but possible)
                change_scenarios = [
                    f"Increase Total Debt by {((target_value / current_value) - 1) * 100:.1f}% (keeping equity constant)",
                    f"Reduce Equity by {(1 - (current_value / target_value)) * 100:.1f}% (keeping debt constant)"
                ]
        else:
            change_scenarios = [
                f"To achieve target of {target_value:.2f}, adjust underlying financial metrics accordingly",
                f"Consider industry benchmarks and company-specific factors",
                f"Consult financial planning tools for detailed scenarios"
            ]

        for i, scenario in enumerate(change_scenarios, 1):
            st.write(f"{i}. {scenario}")

    def _render_scenario_comparison_calculator(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render scenario comparison calculator"""
        st.subheader("📊 Scenario Comparison")
        st.write("Compare how different scenarios affect multiple ratios simultaneously.")

        # Create scenario inputs
        col1, col2, col3 = st.columns(3)

        scenarios = {}

        with col1:
            st.write("**Base Case (Current)**")
            scenarios['base'] = {
                'revenue_change': 0,
                'cost_change': 0,
                'debt_change': 0,
                'asset_change': 0
            }

        with col2:
            st.write("**Optimistic Scenario**")
            scenarios['optimistic'] = {
                'revenue_change': st.slider('Revenue Change (%)', -50, 100, 20, key='opt_rev'),
                'cost_change': st.slider('Cost Change (%)', -50, 50, -10, key='opt_cost'),
                'debt_change': st.slider('Debt Change (%)', -50, 50, -15, key='opt_debt'),
                'asset_change': st.slider('Asset Change (%)', -30, 100, 10, key='opt_asset')
            }

        with col3:
            st.write("**Conservative Scenario**")
            scenarios['conservative'] = {
                'revenue_change': st.slider('Revenue Change (%)', -50, 100, 5, key='cons_rev'),
                'cost_change': st.slider('Cost Change (%)', -50, 50, 0, key='cons_cost'),
                'debt_change': st.slider('Debt Change (%)', -50, 50, -5, key='cons_debt'),
                'asset_change': st.slider('Asset Change (%)', -30, 100, 0, key='cons_asset')
            }

        # Calculate and display scenario results
        st.markdown("---")
        st.write("**Scenario Results Comparison:**")

        self._calculate_scenario_impacts(ratios_data, scenarios)

    def _calculate_scenario_impacts(self, ratios_data: Dict[str, MetricValue], scenarios: Dict) -> None:
        """Calculate impact of scenarios on ratios"""
        import pandas as pd

        # Key ratios to analyze
        key_ratios = ['roe', 'current_ratio', 'debt_to_equity', 'roa']
        available_key_ratios = [ratio for ratio in key_ratios if ratio in ratios_data]

        scenario_results = []

        for scenario_name, changes in scenarios.items():
            scenario_row = {'Scenario': scenario_name.title()}

            for ratio in available_key_ratios:
                current_value = ratios_data[ratio].current

                # Apply simplified impact calculations
                if ratio == 'roe':
                    # ROE affected by revenue and cost changes
                    revenue_impact = 1 + (changes['revenue_change'] / 100)
                    cost_impact = 1 + (changes['cost_change'] / 100)
                    net_income_impact = revenue_impact / cost_impact
                    new_value = current_value * net_income_impact

                elif ratio == 'current_ratio':
                    # Current ratio affected by asset changes
                    asset_impact = 1 + (changes['asset_change'] / 100)
                    new_value = current_value * asset_impact

                elif ratio == 'debt_to_equity':
                    # Debt to equity affected by debt changes
                    debt_impact = 1 + (changes['debt_change'] / 100)
                    new_value = current_value * debt_impact

                elif ratio == 'roa':
                    # ROA affected by revenue, cost, and asset changes
                    revenue_impact = 1 + (changes['revenue_change'] / 100)
                    cost_impact = 1 + (changes['cost_change'] / 100)
                    asset_impact = 1 + (changes['asset_change'] / 100)
                    net_income_impact = revenue_impact / cost_impact
                    new_value = (current_value * net_income_impact) / asset_impact

                else:
                    new_value = current_value

                scenario_row[ratio.replace('_', ' ').title()] = f"{new_value:.2f}"

            scenario_results.append(scenario_row)

        # Display results table
        if scenario_results:
            df = pd.DataFrame(scenario_results)
            st.dataframe(df, use_container_width=True)

            # Create comparison chart
            self._create_scenario_chart(scenario_results, available_key_ratios)

    def _create_scenario_chart(self, scenario_results: List[Dict], ratios: List[str]) -> None:
        """Create scenario comparison chart"""
        import plotly.graph_objects as go
        import pandas as pd

        fig = go.Figure()

        scenarios = [result['Scenario'] for result in scenario_results]

        for ratio in ratios:
            ratio_title = ratio.replace('_', ' ').title()
            if ratio_title in scenario_results[0]:
                values = [float(result[ratio_title]) for result in scenario_results]

                fig.add_trace(go.Bar(
                    name=ratio_title,
                    x=scenarios,
                    y=values,
                ))

        fig.update_layout(
            title='Scenario Comparison - Key Ratios',
            barmode='group',
            height=400,
            xaxis_title='Scenarios',
            yaxis_title='Ratio Values'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_custom_calculation_calculator(self, ratios_data: Dict[str, MetricValue]) -> None:
        """Render custom calculation calculator"""
        st.subheader("🔧 Custom Ratio Calculator")
        st.write("Create your own ratio calculations with custom inputs.")

        # Predefined financial inputs
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Income Statement Items ($M)**")
            revenue = st.number_input('Revenue', value=1000.0, step=10.0)
            gross_profit = st.number_input('Gross Profit', value=400.0, step=10.0)
            operating_income = st.number_input('Operating Income', value=200.0, step=10.0)
            net_income = st.number_input('Net Income', value=150.0, step=10.0)

        with col2:
            st.write("**Balance Sheet Items ($M)**")
            total_assets = st.number_input('Total Assets', value=2000.0, step=50.0)
            current_assets = st.number_input('Current Assets', value=800.0, step=25.0)
            current_liabilities = st.number_input('Current Liabilities', value=400.0, step=25.0)
            total_debt = st.number_input('Total Debt', value=600.0, step=25.0)
            shareholders_equity = st.number_input('Shareholders Equity', value=1400.0, step=50.0)

        # Calculate ratios
        st.markdown("---")
        st.write("**Calculated Ratios:**")

        calculated_ratios = {
            'Gross Margin': (gross_profit / revenue * 100) if revenue > 0 else 0,
            'Operating Margin': (operating_income / revenue * 100) if revenue > 0 else 0,
            'Net Margin': (net_income / revenue * 100) if revenue > 0 else 0,
            'ROA': (net_income / total_assets * 100) if total_assets > 0 else 0,
            'ROE': (net_income / shareholders_equity * 100) if shareholders_equity > 0 else 0,
            'Current Ratio': (current_assets / current_liabilities) if current_liabilities > 0 else 0,
            'Debt-to-Equity': (total_debt / shareholders_equity) if shareholders_equity > 0 else 0,
            'Asset Turnover': (revenue / total_assets) if total_assets > 0 else 0
        }

        # Display calculated ratios in a nice format
        cols = st.columns(4)
        for i, (ratio_name, value) in enumerate(calculated_ratios.items()):
            with cols[i % 4]:
                if 'Margin' in ratio_name or ratio_name in ['ROA', 'ROE']:
                    st.metric(ratio_name, f"{value:.1f}%")
                else:
                    st.metric(ratio_name, f"{value:.2f}")

        # Save custom scenario
        st.markdown("---")
        if st.button("💾 Save Custom Scenario"):
            scenario_name = st.text_input("Scenario Name:", value="Custom Scenario")
            if scenario_name:
                # Here you could save to session state or export
                st.success(f"Scenario '{scenario_name}' saved!")
                st.json(calculated_ratios)

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