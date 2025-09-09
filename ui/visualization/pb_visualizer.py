"""
P/B Ratio Visualization Module

This module provides visualization components for P/B analysis including
industry comparisons, historical trends, and valuation charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PBVisualizer:
    """
    Handles visualization of P/B ratio analysis results
    """

    def __init__(self):
        """Initialize P/B visualizer"""
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#ff9800',
            'danger': '#d62728',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
        }

    def create_pb_dashboard(self, pb_analysis: Dict) -> None:
        """
        Create comprehensive P/B analysis dashboard

        Args:
            pb_analysis (dict): P/B analysis results
        """
        if 'error' in pb_analysis:
            st.error(f"P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error')}")
            return

        ticker = pb_analysis.get('ticker_symbol', 'Unknown')
        st.subheader(f"📊 P/B Ratio Analysis: {ticker}")

        # Current metrics overview
        self._display_current_metrics(pb_analysis)

        # Create visualization tabs - prioritize historical analysis
        tab1, tab2, tab3 = st.tabs(
            [
                "📊 Historical Trends",
                "🏭 Industry Context",
                "📈 Current Analysis",
            ]
        )

        with tab1:
            self._create_historical_trends_tab(pb_analysis)

        with tab2:
            self._create_industry_comparison_tab(pb_analysis)

        with tab3:
            self._create_current_analysis_tab(pb_analysis)

    def _display_current_metrics(self, pb_analysis: Dict) -> None:
        """
        Display current P/B metrics in a card layout

        Args:
            pb_analysis (dict): P/B analysis results
        """
        current_data = pb_analysis.get('current_data', {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            current_price = current_data.get('current_price', 0)
            st.metric(
                label="Current Price", value=f"${current_price:.2f}", help="Latest stock price"
            )

        with col2:
            book_value = current_data.get('book_value_per_share', 0)
            equity_quality = current_data.get('equity_quality', 'medium')
            quality_indicator = '🟢' if equity_quality == 'high' else '🟡' if equity_quality == 'medium' else '🟠'
            
            st.metric(
                label=f"Book Value/Share {quality_indicator}",
                value=f"${book_value:.2f}",
                help=f"Book value per share from latest financial statements (Data Quality: {equity_quality.title()})",
            )

        with col3:
            pb_ratio = current_data.get('pb_ratio')
            if pb_ratio is not None:
                # Determine color based on typical P/B ranges
                delta_color = "normal"
                if pb_ratio < 1.0:
                    delta_color = "inverse"  # Low P/B might be good
                elif pb_ratio > 5.0:
                    delta_color = "off"  # High P/B might be concerning

                st.metric(
                    label="P/B Ratio",
                    value=f"{pb_ratio:.2f}",
                    help="Price-to-Book ratio (Current Price ÷ Book Value per Share)",
                )
            else:
                st.metric(label="P/B Ratio", value="N/A")

        with col4:
            market_cap = current_data.get('market_cap', 0)
            if market_cap > 1_000_000_000:
                market_cap_display = f"${market_cap/1_000_000_000:.1f}B"
            elif market_cap > 1_000_000:
                market_cap_display = f"${market_cap/1_000_000:.1f}M"
            else:
                market_cap_display = f"${market_cap:,.0f}"

            st.metric(
                label="Market Cap", value=market_cap_display, help="Total market capitalization"
            )

    def _create_current_analysis_tab(self, pb_analysis: Dict) -> None:
        """
        Create current analysis tab with gauges and summary

        Args:
            pb_analysis (dict): P/B analysis results
        """
        current_data = pb_analysis.get('current_data', {})
        pb_ratio = current_data.get('pb_ratio')

        if pb_ratio is None:
            st.warning("Unable to display current analysis: P/B ratio not available")
            return

        col1, col2 = st.columns([1, 1])

        with col1:
            # P/B Ratio Gauge
            fig_gauge = self._create_pb_gauge(pb_ratio)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            # Risk Assessment
            risk_assessment = pb_analysis.get('risk_assessment', {})
            self._display_risk_assessment(risk_assessment)

        # Industry position summary
        industry_comp = pb_analysis.get('industry_comparison', {})
        if 'analysis' in industry_comp:
            st.info(f"**Industry Position:** {industry_comp['analysis']}")

    def _create_pb_gauge(self, pb_ratio: float) -> go.Figure:
        """
        Create P/B ratio gauge chart

        Args:
            pb_ratio (float): P/B ratio value

        Returns:
            plotly.graph_objects.Figure: Gauge chart
        """
        # Define gauge ranges
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=pb_ratio,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "P/B Ratio"},
                delta={'reference': 2.0, 'position': "top"},
                gauge={
                    'axis': {'range': [None, 10]},
                    'bar': {'color': self.color_scheme['primary']},
                    'steps': [
                        {'range': [0, 1], 'color': self.color_scheme['success']},  # Attractive
                        {'range': [1, 3], 'color': self.color_scheme['info']},  # Reasonable
                        {'range': [3, 5], 'color': self.color_scheme['warning']},  # Elevated
                        {'range': [5, 10], 'color': self.color_scheme['danger']},  # High
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 5,
                    },
                },
            )
        )

        fig.update_layout(height=300, font={'size': 12}, margin=dict(l=20, r=20, t=40, b=20))

        return fig

    def _display_risk_assessment(self, risk_assessment: Dict) -> None:
        """
        Display risk assessment information

        Args:
            risk_assessment (dict): Risk assessment data
        """
        st.markdown("### Risk Assessment")

        risk_level = risk_assessment.get('risk_level', 'Unknown')

        # Color code risk level
        if risk_level == 'Low':
            st.success(f"**Risk Level:** {risk_level}")
        elif risk_level == 'Medium':
            st.warning(f"**Risk Level:** {risk_level}")
        else:
            st.error(f"**Risk Level:** {risk_level}")

        # Display risk factors
        risks = risk_assessment.get('risks', [])
        if risks:
            st.markdown("**Key Risk Factors:**")
            for i, risk in enumerate(risks[:3], 1):  # Show top 3 risks
                st.markdown(f"{i}. {risk}")

    def _create_industry_comparison_tab(self, pb_analysis: Dict) -> None:
        """
        Create industry comparison tab with conditional display based on data availability

        Args:
            pb_analysis (dict): P/B analysis results
        """
        industry_comp = pb_analysis.get('industry_comparison', {})

        # Check if industry data is available and sufficient
        if 'error' in industry_comp or not industry_comp:
            st.info(
                "🏭 **Industry Context Not Available**\n\n"
                "Industry comparison requires live market data from multiple peer companies in the same sector. "
                "This feature may be unavailable due to:\n\n"
                "• Insufficient peer companies identified\n"
                "• API rate limits or data source unavailability\n"
                "• Company sector/industry classification issues\n\n"
                "💡 **Focus on Historical Analysis**: The Historical Trends tab provides comprehensive "
                "valuation context using the company's own trading patterns."
            )
            return

        current_pb = industry_comp.get('current_pb')
        benchmarks = industry_comp.get('benchmarks', {})
        industry_key = industry_comp.get('industry_key', 'Unknown')
        peer_count = industry_comp.get('peer_count', 0)
        data_source = industry_comp.get('data_source', 'Market APIs')
        last_updated = industry_comp.get('last_updated', 'Unknown')

        if not benchmarks or current_pb is None or peer_count < 5:
            # Enhanced messaging with troubleshooting suggestions
            if peer_count == 0:
                st.error(
                    f"**No Industry Data Available for {industry_key}**\n\n"
                    f"🔍 **Data Source:** {data_source}\n"
                    f"📊 **Peer Companies Found:** {peer_count} companies\n"
                    f"⚠️ **Status:** No peer companies could be identified\n"
                    f"📅 **Last Attempted:** {last_updated}\n\n"
                    f"**🛠️ Possible Solutions:**\n"
                    f"• **Wait and Retry:** API rate limits may be causing temporary issues\n"
                    f"• **Check Network:** Ensure internet connection is stable\n"
                    f"• **Sector Classification:** The company may be in a niche or new sector\n"
                    f"• **Use Historical Analysis:** The Historical Trends tab provides reliable valuation context\n\n"
                    f"💡 **Alternative:** Use the Historical Trends analysis which doesn't require peer data "
                    f"and provides comprehensive valuation insights based on the company's own trading patterns."
                )
            else:
                st.warning(
                    f"**Insufficient Industry Data Available for {industry_key}**\n\n"
                    f"🔍 **Data Source:** {data_source}\n"
                    f"📊 **Peer Companies Found:** {peer_count} companies\n"
                    f"⚠️ **Minimum Required:** 5 peer companies for statistical reliability\n"
                    f"📅 **Last Updated:** {last_updated}\n\n"
                    f"**🛠️ Troubleshooting:**\n"
                    f"• **Try Again Later:** More peer data may become available\n"
                    f"• **Sector Coverage:** This sector may have limited public companies\n"
                    f"• **Data Quality:** Some peers may lack P/B ratio data\n\n"
                    f"💡 **Recommendation:** The Historical Trends tab provides comprehensive valuation analysis "
                    f"using the company's own historical P/B patterns, which is often more reliable than industry comparisons."
                )
            return

        # Display enhanced data transparency information with quality indicators
        data_quality = "High" if peer_count >= 15 else "Medium" if peer_count >= 10 else "Limited"
        confidence_level = "High confidence" if peer_count >= 15 else "Medium confidence" if peer_count >= 10 else "Limited confidence"
        
        # Create visual quality indicator
        if data_quality == "High":
            quality_color = "🟢"
        elif data_quality == "Medium":
            quality_color = "🟡"
        else:
            quality_color = "🟠"
        
        # Get cache information if available
        cache_info = industry_comp.get('cache_info', {})
        cache_status_text = ""
        
        if cache_info:
            cache_used = cache_info.get('cache_used', False)
            data_source_type = cache_info.get('data_source', 'unknown')
            
            if cache_used and data_source_type == 'real_time':
                cache_status_text = f"\n**Cache Status:** 🟢 **Real-time data cached** (Performance optimized)"
            elif data_source_type == 'static_fallback':
                cache_status_text = f"\n**Cache Status:** 🔴 **Using static benchmarks** (Real-time data unavailable)"
            elif not cache_used:
                cache_status_text = f"\n**Cache Status:** 🟡 **Fresh API call** (Data not cached)"

        st.info(
            f"📊 **Industry Analysis Transparency & Attribution**\n\n"
            f"**Industry/Sector:** {industry_key}\n"
            f"**Peer Company Count:** {peer_count} companies\n"
            f"**Data Quality:** {quality_color} {data_quality} ({confidence_level} - {peer_count} peers)\n"
            f"**Data Source:** {data_source}{cache_status_text}\n"
            f"**Last Updated:** {last_updated}\n"
            f"**Minimum Threshold:** {'✅ Met' if peer_count >= 5 else '❌ Not Met'} (5+ peer companies required)\n\n"
            f"💡 **Data Reliability:** Based on {peer_count} companies in the {industry_key} sector. "
            f"Industry comparison shown only when minimum peer threshold is met for statistical reliability."
        )

        # Industry comparison chart
        fig_industry = self._create_industry_comparison_chart(current_pb, benchmarks, industry_key, peer_count)
        st.plotly_chart(fig_industry, use_container_width=True)

        # Industry statistics table
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Industry Benchmarks")
            benchmark_df = pd.DataFrame(
                {
                    'Metric': ['Industry Low', 'Industry Median', 'Industry High', 'Current P/B'],
                    'Value': [
                        f"{benchmarks.get('low', 0):.2f}",
                        f"{benchmarks.get('median', 0):.2f}",
                        f"{benchmarks.get('high', 0):.2f}",
                        f"{current_pb:.2f}",
                    ],
                }
            )
            st.dataframe(benchmark_df, hide_index=True)

        with col2:
            st.markdown("### Position Analysis")
            position = industry_comp.get('position', 'Unknown')
            percentile = industry_comp.get('percentile', 'Unknown')
            discount_premium = industry_comp.get('discount_premium_to_median', 0)

            st.metric("Industry Position", position)
            st.metric("Percentile Range", percentile)
            st.metric(
                "Premium/Discount to Median",
                f"{discount_premium:+.1%}",
                delta=f"{discount_premium:+.1%}",
            )
            
        # Add enhanced disclaimer with data source attribution
        st.caption(
            f"*Industry comparison based on {peer_count} companies in {industry_key} sector. "
            f"Data sourced from {data_source} and may vary based on market conditions. "
            f"Last updated: {last_updated}. Only displayed when minimum 5 peer companies available for statistical reliability.*"
        )

    def _create_industry_comparison_chart(
        self, current_pb: float, benchmarks: Dict, industry_key: str, peer_count: int = 0
    ) -> go.Figure:
        """
        Create industry comparison horizontal bar chart

        Args:
            current_pb (float): Current P/B ratio
            benchmarks (dict): Industry benchmarks
            industry_key (str): Industry category
            peer_count (int): Number of peer companies in analysis

        Returns:
            plotly.graph_objects.Figure: Industry comparison chart
        """
        categories = ['Industry Low', 'Industry Median', 'Industry High', 'Current P/B']
        values = [
            benchmarks.get('low', 0),
            benchmarks.get('median', 0),
            benchmarks.get('high', 0),
            current_pb,
        ]
        colors = [
            self.color_scheme['success'],
            self.color_scheme['info'],
            self.color_scheme['warning'],
            self.color_scheme['primary'],
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    y=categories,
                    x=values,
                    orientation='h',
                    marker_color=colors,
                    text=[f'{v:.2f}' for v in values],
                    textposition='auto',
                )
            ]
        )

        # Create more informative title with data quality indication
        title_text = f'{industry_key} Industry P/B Comparison'
        if peer_count > 0:
            data_quality_indicator = "High Confidence" if peer_count >= 15 else "Medium Confidence" if peer_count >= 10 else "Limited Data"
            title_text += f' (Based on {peer_count} Companies - {data_quality_indicator})'
            
        fig.update_layout(
            title=title_text,
            xaxis_title='P/B Ratio',
            yaxis_title='Category',
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig

    def _create_historical_trends_tab(self, pb_analysis: Dict) -> None:
        """
        Create historical trends tab with emphasis on implied price targets

        Args:
            pb_analysis (dict): P/B analysis results
        """
        historical_analysis = pb_analysis.get('historical_analysis', {})

        if 'error' in historical_analysis:
            error_type = historical_analysis.get('error', 'Unknown error')
            
            if error_type == 'excel_mode_limitation':
                st.info(
                    "📊 **Historical P/B Analysis Unavailable in Excel Mode**\n\n"
                    "Historical P/B trends require quarterly financial data over multiple years, which is not available "
                    "in Excel mode. The current P/B analysis above uses your Excel data for accurate present-day calculations.\n\n"
                    "💡 **To view historical trends**: Switch to Ticker Mode (API Data) which provides quarterly historical data."
                )
            else:
                st.warning(
                    f"Historical analysis not available: {error_type}"
                )
            return

        historical_data = historical_analysis.get('historical_data', [])

        if not historical_data:
            st.warning("No historical P/B data available")
            return

        # Historical Implied Price Targets (Primary Section)
        self._create_historical_implied_prices_section(pb_analysis)
        
        st.divider()
        
        # Historical P/B trend chart with enhanced context
        fig_trend = self._create_historical_trend_chart(historical_data, pb_analysis)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Add data quality and source attribution report
        self._create_data_quality_report_section(pb_analysis)

        # Historical statistics
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Historical Statistics")
            stats = historical_analysis.get('statistics', {})
            if stats:
                stats_df = pd.DataFrame(
                    {
                        'Statistic': ['Minimum', 'Maximum', 'Mean', 'Median', 'Std Deviation'],
                        'Value': [
                            f"{stats.get('min', 0):.2f}",
                            f"{stats.get('max', 0):.2f}",
                            f"{stats.get('mean', 0):.2f}",
                            f"{stats.get('median', 0):.2f}",
                            f"{stats.get('std', 0):.2f}",
                        ],
                    }
                )
                st.dataframe(stats_df, hide_index=True)

        with col2:
            st.markdown("### Trend Analysis")
            trend_analysis = historical_analysis.get('trend_analysis', {})
            interpretation = historical_analysis.get(
                'interpretation', 'No interpretation available'
            )

            if trend_analysis:
                trend = trend_analysis.get('trend', 'Unknown').title()
                volatility = trend_analysis.get('volatility', 0)

                st.metric("Trend Direction", trend)
                st.metric("Volatility", f"{volatility:.1%}")

            st.info(interpretation)

    def _create_historical_implied_prices_section(self, pb_analysis: Dict) -> None:
        """
        Create historical implied price targets section

        Args:
            pb_analysis (dict): P/B analysis results
        """
        st.markdown("### 🎯 Historical Implied Price Targets")
        
        # Add explanation callout
        st.info(
            "💡 **What you're seeing:** These are implied stock price targets calculated by applying "
            "the company's own historical P/B ratio patterns to the current book value per share. "
            "This helps assess if the current price is reasonable based on the stock's own trading history."
        )
        
        historical_analysis = pb_analysis.get('historical_analysis', {})
        current_data = pb_analysis.get('current_data', {})
        
        current_price = current_data.get('current_price', 0)
        book_value_per_share = current_data.get('book_value_per_share', 0)
        stats = historical_analysis.get('statistics', {})
        
        if not stats or book_value_per_share <= 0:
            st.warning("Insufficient data to calculate historical implied prices")
            return
        
        # Calculate historical implied prices
        historical_min = stats.get('min', 0)
        historical_mean = stats.get('mean', 0)
        historical_median = stats.get('median', 0)
        historical_max = stats.get('max', 0)
        
        # Calculate implied prices
        implied_prices = {
            'Conservative (Historical Min)': historical_min * book_value_per_share,
            'Mean P/B Target': historical_mean * book_value_per_share,
            'Median P/B Target': historical_median * book_value_per_share,
            'Optimistic (Historical Max)': historical_max * book_value_per_share,
        }
        
        # Create full-width chart showing implied prices vs current
        self._create_historical_implied_prices_chart(implied_prices, current_price)
        
        # Create columns for table and methodology (below the chart)
        col1, col2 = st.columns([1.2, 0.8])
        
        with col1:
            st.markdown("### Implied Stock Price Targets")
            
            # Create DataFrame for display
            targets_data = []
            for scenario, price in implied_prices.items():
                if scenario == 'Conservative (Historical Min)':
                    pb_multiple = historical_min
                elif scenario == 'Mean P/B Target':
                    pb_multiple = historical_mean
                elif scenario == 'Median P/B Target':
                    pb_multiple = historical_median
                else:  # Optimistic
                    pb_multiple = historical_max
                
                upside_downside = ((price - current_price) / current_price) if current_price > 0 else 0
                
                targets_data.append({
                    'Scenario': scenario,
                    'Historical P/B': f"{pb_multiple:.2f}x",
                    'Implied Price': f"${price:.2f}",
                    'Upside/Downside': f"{upside_downside:+.1%}"
                })
            
            # Add current price row
            targets_data.append({
                'Scenario': 'Current Price',
                'Historical P/B': f"{(current_price / book_value_per_share):.2f}x" if book_value_per_share > 0 else "N/A",
                'Implied Price': f"${current_price:.2f}",
                'Upside/Downside': "0.0%"
            })
            
            targets_df = pd.DataFrame(targets_data)
            st.dataframe(targets_df, hide_index=True, use_container_width=True)
        
        with col2:
            # Show calculation methodology
            st.markdown("### Calculation Methodology")
            st.markdown("**Formula:**")
            st.code("Implied Price = Current Book Value/Share × Historical P/B Ratio")
            
            if book_value_per_share > 0:
                st.markdown(f"**Current Book Value/Share:** ${book_value_per_share:.2f}")
                
                # Example calculation
                example_price = historical_median * book_value_per_share
                st.markdown("**Example (Median P/B):**")
                st.info(f"Implied Price = ${book_value_per_share:.2f} × {historical_median:.2f}x = ${example_price:.2f}")

    def _create_historical_implied_prices_chart(self, implied_prices: Dict, current_price: float) -> None:
        """
        Create chart showing historical implied prices vs current price
        
        Args:
            implied_prices (dict): Dictionary of scenario: implied_price
            current_price (float): Current stock price
        """
        scenarios = list(implied_prices.keys())
        prices = list(implied_prices.values())
        
        # Color scheme for different scenarios
        colors = [
            self.color_scheme['success'],    # Conservative
            self.color_scheme['info'],       # Mean
            self.color_scheme['info'],       # Median  
            self.color_scheme['warning'],    # Optimistic
        ]
        
        fig = go.Figure()
        
        # Add bars for implied prices
        fig.add_trace(
            go.Bar(
                x=scenarios,
                y=prices,
                marker_color=colors,
                text=[f'${price:.2f}' for price in prices],
                textposition='auto',
                name='Historical Implied Prices',
            )
        )
        
        # Add current price line
        fig.add_hline(
            y=current_price,
            line_dash="dash",
            line_color=self.color_scheme['danger'],
            annotation_text=f"Current: ${current_price:.2f}",
            annotation_position="top right",
        )
        
        fig.update_layout(
            title='Historical P/B Implied Prices vs Current Price',
            yaxis_title='Stock Price ($)',
            xaxis_title='Historical P/B Scenarios',
            height=300,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)

    def _create_historical_trend_chart(self, historical_data: List[Dict], pb_analysis: Dict) -> go.Figure:
        """
        Create historical P/B trend line chart with data quality indicators and enhanced source attribution

        Args:
            historical_data (list): Historical P/B data points
            pb_analysis (dict): Complete P/B analysis data including current values and statistics

        Returns:
            plotly.graph_objects.Figure: Enhanced historical trend chart with data transparency features
        """
        # Extract historical data points with data quality information
        dates = []
        pb_ratios = []
        prices = []
        data_quality_indicators = []
        equity_sources = []
        shares_sources = []
        price_sources = []
        fiscal_year_end_dates = []
        
        for entry in historical_data:
            if entry.get('pb_ratio') is not None:
                dates.append(entry['date'])
                pb_ratios.append(entry['pb_ratio'])
                prices.append(entry['price'])
                
                # Extract data quality and source information
                data_quality = entry.get('data_quality', 'medium')
                equity_source = entry.get('equity_source', 'financial_statements')
                shares_source = entry.get('shares_source', 'current_outstanding')
                price_source = entry.get('price_source', 'market_data')
                fiscal_year_end = entry.get('fiscal_year_end_date', entry['date'])
                
                data_quality_indicators.append(data_quality)
                equity_sources.append(equity_source)
                shares_sources.append(shares_source)
                price_sources.append(price_source)
                fiscal_year_end_dates.append(fiscal_year_end)

        # Get current position data
        current_data = pb_analysis.get('current_data', {})
        current_pb = current_data.get('pb_ratio')
        current_price = current_data.get('current_price', 0)
        book_value_per_share = current_data.get('book_value_per_share', 0)
        
        # Get historical statistics for reference lines
        historical_analysis = pb_analysis.get('historical_analysis', {})
        stats = historical_analysis.get('statistics', {})
        historical_mean = stats.get('mean', 0)
        historical_median = stats.get('median', 0)
        
        # Get trend analysis for indicators
        trend_analysis = historical_analysis.get('trend_analysis', {})
        trend_direction = trend_analysis.get('trend', 'Unknown').lower()

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1,
            cols=1,
            specs=[[{"secondary_y": True}]],
            subplot_titles=("Historical P/B Ratio with Current Position & Key Levels"),
        )

        # Add P/B ratio line with enhanced hover data including data quality and source attribution
        hover_text = []
        marker_colors = []
        marker_sizes = []
        
        # Define quality-based styling
        quality_colors = {
            'high': self.color_scheme['success'],
            'medium': self.color_scheme['info'], 
            'low': self.color_scheme['warning']
        }
        
        quality_sizes = {
            'high': 6,
            'medium': 5,
            'low': 4
        }
        
        quality_badges = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🟠'
        }
        
        for i, (date, pb, price) in enumerate(zip(dates, pb_ratios, prices)):
            # Calculate implied price at current book value
            implied_current_price = pb * book_value_per_share if book_value_per_share > 0 else 0
            
            # Get data quality and source information for this data point
            quality = data_quality_indicators[i] if i < len(data_quality_indicators) else 'medium'
            equity_src = equity_sources[i] if i < len(equity_sources) else 'unknown'
            shares_src = shares_sources[i] if i < len(shares_sources) else 'unknown' 
            price_src = price_sources[i] if i < len(price_sources) else 'unknown'
            fy_end = fiscal_year_end_dates[i] if i < len(fiscal_year_end_dates) else date
            
            # Format source names for display
            equity_display = self._format_source_name(equity_src)
            shares_display = self._format_source_name(shares_src)
            price_display = self._format_source_name(price_src)
            
            # Calculate days between price date and fiscal year end
            try:
                from datetime import datetime
                price_date = datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date
                fy_date = datetime.strptime(fy_end, '%Y-%m-%d') if isinstance(fy_end, str) else fy_end
                days_diff = abs((price_date - fy_date).days)
                date_alignment = f"{days_diff} days from fiscal year-end"
            except:
                date_alignment = "Date alignment unknown"
            
            hover_info = (
                f"📊 <b>P/B Analysis - {date}</b><br>"
                f"P/B Ratio: <b>{pb:.2f}x</b><br>"
                f"Stock Price: <b>${price:.2f}</b><br>"
                f"Implied Current Price: <b>${implied_current_price:.2f}</b><br>"
                f"<br>"
                f"📋 <b>Data Quality & Sources:</b><br>"
                f"{quality_badges.get(quality, '⚪')} Quality Level: <b>{quality.title()}</b><br>"
                f"📈 Equity Source: <i>{equity_display}</i><br>"
                f"📊 Shares Source: <i>{shares_display}</i><br>"
                f"💰 Price Source: <i>{price_display}</i><br>"
                f"📅 {date_alignment}<br>"
                f"🗓️ Fiscal Year End: {fy_end}"
            )
            hover_text.append(hover_info)
            
            # Set marker styling based on quality
            marker_colors.append(quality_colors.get(quality, quality_colors['medium']))
            marker_sizes.append(quality_sizes.get(quality, quality_sizes['medium']))

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=pb_ratios,
                mode='lines+markers',
                name='Historical P/B (Quality-Enhanced)',
                line=dict(color=self.color_scheme['primary'], width=2),
                marker=dict(
                    size=marker_sizes,
                    color=marker_colors,
                    line=dict(width=1, color='white'),
                    opacity=0.8
                ),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
            ),
            secondary_y=False,
        )

        # Add stock price line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name='Historical Stock Price',
                line=dict(color=self.color_scheme['secondary'], width=1, dash='dash'),
                opacity=0.7,
                hovertemplate='Stock Price: $%{y:.2f}<extra></extra>',
            ),
            secondary_y=True,
        )

        # Add horizontal reference lines for historical averages
        if historical_mean > 0:
            fig.add_hline(
                y=historical_mean,
                line_dash="dot",
                line_color=self.color_scheme['info'],
                line_width=2,
                annotation_text=f"Historical Mean: {historical_mean:.2f}x",
                annotation_position="top left",
                annotation_bgcolor="rgba(255,255,255,0.8)",
                annotation_bordercolor=self.color_scheme['info'],
                secondary_y=False,
            )

        if historical_median > 0:
            fig.add_hline(
                y=historical_median,
                line_dash="dash",
                line_color=self.color_scheme['success'],
                line_width=2,
                annotation_text=f"Historical Median: {historical_median:.2f}x",
                annotation_position="top right",
                annotation_bgcolor="rgba(255,255,255,0.8)",
                annotation_bordercolor=self.color_scheme['success'],
                secondary_y=False,
            )

        # Highlight current P/B position with distinct marker
        if current_pb is not None and dates:
            # Add current position marker at the end of the chart
            latest_date = max(dates) if dates else None
            if latest_date:
                fig.add_trace(
                    go.Scatter(
                        x=[latest_date],
                        y=[current_pb],
                        mode='markers',
                        name='Current P/B',
                        marker=dict(
                            size=15,
                            color=self.color_scheme['danger'],
                            symbol='star',
                            line=dict(width=2, color='white')
                        ),
                        hovertemplate=(
                            f'Current Position<br>'
                            f'P/B Ratio: {current_pb:.2f}x<br>'
                            f'Stock Price: ${current_price:.2f}<br>'
                            f'vs Mean: {((current_pb - historical_mean) / historical_mean * 100):+.1f}%<br>'
                            f'vs Median: {((current_pb - historical_median) / historical_median * 100):+.1f}%<extra></extra>'
                        ) if historical_mean > 0 and historical_median > 0 else (
                            f'Current Position<br>'
                            f'P/B Ratio: {current_pb:.2f}x<br>'
                            f'Stock Price: ${current_price:.2f}<extra></extra>'
                        ),
                        showlegend=True,
                    ),
                    secondary_y=False,
                )

        # Add trend direction indicator
        if trend_direction in ['upward', 'up']:
            trend_symbol = '↗'
            trend_color = self.color_scheme['success']
        elif trend_direction in ['downward', 'down']:
            trend_symbol = '↘'  
            trend_color = self.color_scheme['danger']
        else:
            trend_symbol = '→'
            trend_color = self.color_scheme['info']

        # Set y-axes titles
        fig.update_yaxes(title_text="P/B Ratio", secondary_y=False)
        fig.update_yaxes(title_text="Stock Price ($)", secondary_y=True)

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Add trend indicator annotation
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=f"Trend: {trend_symbol} {trend_direction.title()}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=trend_color,
            borderwidth=1,
            font=dict(size=12, color=trend_color),
        )

        fig.update_layout(
            height=450,
            hovermode='x unified',
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="right", 
                x=1,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            margin=dict(l=20, r=20, t=80, b=20),
        )

        return fig

    def _create_valuation_ranges_tab(self, pb_analysis: Dict) -> None:
        """
        Create valuation ranges tab

        Args:
            pb_analysis (dict): P/B analysis results
        """
        valuation_analysis = pb_analysis.get('valuation_analysis', {})
        current_data = pb_analysis.get('current_data', {})

        if 'valuation_ranges' not in valuation_analysis:
            st.warning("Valuation ranges not available")
            return

        ranges = valuation_analysis['valuation_ranges']
        current_price = current_data.get('current_price', 0)
        
        # Add explanation callout at the top
        st.info(
            "💡 **What you're seeing:** These are implied stock price targets calculated by applying "
            "industry-specific P/B ratio benchmarks to the company's book value per share. "
            "The upside/downside shows potential returns if the stock trades at these industry multiples."
        )

        # Valuation ranges chart
        fig_valuation = self._create_valuation_ranges_chart(ranges, current_price)
        st.plotly_chart(fig_valuation, use_container_width=True)

        # Valuation analysis table
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Implied Stock Price Targets (P/B Method)")

            # Get industry benchmarks for P/B multiples display
            benchmarks = valuation_analysis.get('industry_benchmarks', {})
            book_value_per_share = valuation_analysis.get('book_value_per_share', 0)
            
            valuation_df = pd.DataFrame(
                {
                    'Scenario': ['Conservative', 'Fair Value', 'Optimistic', 'Current Price'],
                    'P/B Multiple': [
                        f"{benchmarks.get('low', 0):.2f}x",
                        f"{benchmarks.get('median', 0):.2f}x", 
                        f"{benchmarks.get('high', 0):.2f}x",
                        f"{(current_price / book_value_per_share):.2f}x" if book_value_per_share > 0 else "N/A",
                    ],
                    'Implied Stock Price': [
                        f"${ranges.get('conservative', 0):.2f}",
                        f"${ranges.get('fair_value', 0):.2f}",
                        f"${ranges.get('optimistic', 0):.2f}",
                        f"${current_price:.2f}",
                    ],
                    'Upside/Downside': [
                        (
                            f"{(ranges.get('conservative', 0) - current_price) / current_price:+.1%}"
                            if current_price > 0
                            else "N/A"
                        ),
                        (
                            f"{(ranges.get('fair_value', 0) - current_price) / current_price:+.1%}"
                            if current_price > 0
                            else "N/A"
                        ),
                        (
                            f"{(ranges.get('optimistic', 0) - current_price) / current_price:+.1%}"
                            if current_price > 0
                            else "N/A"
                        ),
                        "0.0%",
                    ],
                }
            )
            st.dataframe(valuation_df, hide_index=True)

        with col2:
            st.markdown("### Calculation Methodology")
            
            # Show the explicit calculation formula
            book_value_per_share = valuation_analysis.get('book_value_per_share', 0)
            st.markdown("**Formula:**")
            st.code("Implied Stock Price = Book Value per Share × Industry P/B Multiple")
            
            # Show the book value being used
            if book_value_per_share > 0:
                st.markdown(f"**Book Value per Share:** ${book_value_per_share:.2f}")
            
            # Add calculation example using fair value
            benchmarks = valuation_analysis.get('industry_benchmarks', {})
            if benchmarks and book_value_per_share > 0:
                fair_pb = benchmarks.get('median', 0)
                fair_price = ranges.get('fair_value', 0)
                st.markdown("**Example Calculation:**")
                st.info(f"Fair Value = ${book_value_per_share:.2f} × {fair_pb:.2f}x = ${fair_price:.2f}")

            # Display industry benchmarks used
            if benchmarks:
                st.markdown("**Industry P/B Benchmarks:**")
                st.write(f"• Conservative: {benchmarks.get('low', 0):.2f}x")
                st.write(f"• Fair Value: {benchmarks.get('median', 0):.2f}x") 
                st.write(f"• Optimistic: {benchmarks.get('high', 0):.2f}x")

    def _create_valuation_ranges_chart(self, ranges: Dict, current_price: float) -> go.Figure:
        """
        Create valuation ranges horizontal bar chart

        Args:
            ranges (dict): Valuation ranges
            current_price (float): Current stock price

        Returns:
            plotly.graph_objects.Figure: Valuation ranges chart
        """
        scenarios = ['Conservative', 'Fair Value', 'Optimistic']
        prices = [
            ranges.get('conservative', 0),
            ranges.get('fair_value', 0),
            ranges.get('optimistic', 0),
        ]

        colors = [
            self.color_scheme['success'],
            self.color_scheme['info'],
            self.color_scheme['warning'],
        ]

        fig = go.Figure()

        # Add valuation bars
        fig.add_trace(
            go.Bar(
                y=scenarios,
                x=prices,
                orientation='h',
                marker_color=colors,
                text=[f'${price:.2f}' for price in prices],
                textposition='auto',
                name='P/B Valuation',
            )
        )

        # Add current price line
        fig.add_vline(
            x=current_price,
            line_dash="dash",
            line_color=self.color_scheme['danger'],
            annotation_text=f"Current: ${current_price:.2f}",
            annotation_position="top",
        )

        fig.update_layout(
            title='Implied Stock Price Targets (P/B Method) vs Current Price',
            xaxis_title='Implied Stock Price ($)',
            yaxis_title='Valuation Scenario',
            height=300,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig

    def _format_source_name(self, source: str) -> str:
        """
        Format data source names for user-friendly display
        
        Args:
            source (str): Raw source identifier
            
        Returns:
            str: Formatted source name
        """
        source_mappings = {
            'financial_statements': 'Excel Financial Statements',
            'excel_specific_fields': 'Excel (Specific Fields)',
            'enhanced_data_manager': 'Enhanced Data Manager',
            'yfinance': 'Yahoo Finance API',
            'market_data': 'Market Data APIs',
            'current_outstanding': 'Current Shares Outstanding',
            'year_specific': 'Year-Specific from Excel',
            'interpolated': 'Interpolated (Missing Years)',
            'generic_cashflow_search': 'Cash Flow Statement Search',
            'unknown': 'Source Unknown'
        }
        return source_mappings.get(source, source.replace('_', ' ').title())

    def _create_data_quality_report_section(self, pb_analysis: Dict) -> None:
        """
        Create expandable data quality report section with comprehensive transparency information
        
        Args:
            pb_analysis (dict): P/B analysis results
        """
        # Define quality badges for this method
        quality_badges = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🟠'
        }
        
        with st.expander("📋 Data Quality & Source Attribution Report", expanded=False):
            st.markdown("### 🔍 Comprehensive Data Transparency")
            
            # Overall data quality assessment
            current_data = pb_analysis.get('current_data', {})
            historical_analysis = pb_analysis.get('historical_analysis', {})
            industry_comp = pb_analysis.get('industry_comparison', {})
            
            # Current P/B calculation data quality
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### Current P/B Calculation")
                
                # Book value source attribution
                book_value_source = current_data.get('equity_source', 'financial_statements')
                book_value_quality = current_data.get('equity_quality', 'medium')
                
                st.markdown(f"**📈 Book Value Source:** {self._format_source_name(book_value_source)}")
                st.markdown(f"**🔍 Equity Data Quality:** {quality_badges.get(book_value_quality, '⚪')} {book_value_quality.title()}")
                
                # Shares outstanding source
                shares_source = current_data.get('shares_source', 'current_outstanding')
                shares_quality = current_data.get('shares_quality', 'medium')
                
                st.markdown(f"**📊 Shares Source:** {self._format_source_name(shares_source)}")
                st.markdown(f"**🔍 Shares Data Quality:** {quality_badges.get(shares_quality, '⚪')} {shares_quality.title()}")
                
                # Price source and timing
                price_source = current_data.get('price_source', 'market_data')
                price_date = current_data.get('price_date', 'Current')
                fiscal_year_end = current_data.get('fiscal_year_end_date', 'Unknown')
                
                st.markdown(f"**💰 Price Source:** {self._format_source_name(price_source)}")
                st.markdown(f"**📅 Price Date:** {price_date}")
                st.markdown(f"**🗓️ Fiscal Year End:** {fiscal_year_end}")
            
            with col2:
                st.markdown("#### Historical Analysis Coverage")
                
                historical_data = historical_analysis.get('historical_data', [])
                if historical_data:
                    # Calculate quality distribution
                    quality_counts = {'high': 0, 'medium': 0, 'low': 0}
                    total_points = len(historical_data)
                    
                    for entry in historical_data:
                        quality = entry.get('data_quality', 'medium')
                        quality_counts[quality] = quality_counts.get(quality, 0) + 1
                    
                    st.markdown(f"**📊 Total Data Points:** {total_points}")
                    st.markdown(f"**🟢 High Quality:** {quality_counts['high']} ({quality_counts['high']/total_points*100:.1f}%)")
                    st.markdown(f"**🟡 Medium Quality:** {quality_counts['medium']} ({quality_counts['medium']/total_points*100:.1f}%)")
                    st.markdown(f"**🟠 Low Quality:** {quality_counts['low']} ({quality_counts['low']/total_points*100:.1f}%)")
                    
                    # Historical data range
                    date_range = historical_analysis.get('date_range', {})
                    if date_range:
                        st.markdown(f"**📅 Date Range:** {date_range.get('start', 'Unknown')} to {date_range.get('end', 'Unknown')}")
                else:
                    st.warning("No historical data available for quality analysis")
                    
                # Industry comparison data quality
                if industry_comp and 'error' not in industry_comp:
                    peer_count = industry_comp.get('peer_count', 0)
                    industry_data_source = industry_comp.get('data_source', 'Unknown')
                    last_updated = industry_comp.get('last_updated', 'Unknown')
                    
                    st.markdown("#### Industry Comparison Quality")
                    st.markdown(f"**🏭 Peer Companies:** {peer_count}")
                    st.markdown(f"**🌐 Industry Data Source:** {industry_data_source}")
                    st.markdown(f"**🕒 Last Updated:** {last_updated}")
            
            # Data quality legend
            st.markdown("---")
            st.markdown("#### 📚 Data Quality Legend")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🟢 High Quality**")
                st.caption("✅ Complete data from primary sources\n✅ Recent and verified\n✅ Cross-validated")
                
            with col2:
                st.markdown("**🟡 Medium Quality**")
                st.caption("⚠️ Some gaps or estimated data\n⚠️ Reliable but not perfect\n⚠️ Standard data sources")
                
            with col3:
                st.markdown("**🟠 Low Quality**")
                st.caption("⚠️ Significant gaps or estimates\n⚠️ Older or incomplete data\n⚠️ Fallback data sources")
            
            # Source attribution details
            st.markdown("---")
            st.markdown("#### 🔗 Source Attribution Details")
            
            source_details = {
                "Excel Financial Statements": "Company-provided financial data from uploaded Excel files",
                "Enhanced Data Manager": "Multi-source validated financial data with quality checks",
                "Yahoo Finance API": "Real-time market data and historical prices",
                "Market Data APIs": "Financial market data from various API providers",
                "Year-Specific from Excel": "Year-specific shares outstanding from income statements",
                "Interpolated (Missing Years)": "Calculated values for missing data points",
                "Current Shares Outstanding": "Latest available shares outstanding data"
            }
            
            for source, description in source_details.items():
                st.markdown(f"**{source}:** {description}")


def display_pb_analysis(pb_analysis: Dict) -> None:
    """
    Main function to display P/B analysis in Streamlit

    Args:
        pb_analysis (dict): P/B analysis results
    """
    visualizer = PBVisualizer()
    visualizer.create_pb_dashboard(pb_analysis)
