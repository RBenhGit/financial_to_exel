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

        # Create visualization tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📈 Current Analysis",
                "🏭 Industry Comparison",
                "📊 Historical Trends",
                "💰 Valuation Ranges",
            ]
        )

        with tab1:
            self._create_current_analysis_tab(pb_analysis)

        with tab2:
            self._create_industry_comparison_tab(pb_analysis)

        with tab3:
            self._create_historical_trends_tab(pb_analysis)

        with tab4:
            self._create_valuation_ranges_tab(pb_analysis)

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
            st.metric(
                label="Book Value/Share",
                value=f"${book_value:.2f}",
                help="Book value per share from latest financial statements",
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
        Create industry comparison tab

        Args:
            pb_analysis (dict): P/B analysis results
        """
        industry_comp = pb_analysis.get('industry_comparison', {})

        if 'error' in industry_comp:
            st.warning("Industry comparison data not available")
            return

        current_pb = industry_comp.get('current_pb')
        benchmarks = industry_comp.get('benchmarks', {})
        industry_key = industry_comp.get('industry_key', 'Unknown')

        if not benchmarks or current_pb is None:
            st.warning("Insufficient data for industry comparison")
            return

        # Industry comparison chart
        fig_industry = self._create_industry_comparison_chart(current_pb, benchmarks, industry_key)
        st.plotly_chart(fig_industry, use_container_width=True)

        # Industry statistics table
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Industry Benchmarks")
            benchmark_df = pd.DataFrame(
                {
                    'Metric': ['Industry Low', 'Industry Median', 'Industry High', 'Current P/B'],
                    'Value': [
                        benchmarks.get('low', 0),
                        benchmarks.get('median', 0),
                        benchmarks.get('high', 0),
                        current_pb,
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

    def _create_industry_comparison_chart(
        self, current_pb: float, benchmarks: Dict, industry_key: str
    ) -> go.Figure:
        """
        Create industry comparison horizontal bar chart

        Args:
            current_pb (float): Current P/B ratio
            benchmarks (dict): Industry benchmarks
            industry_key (str): Industry category

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

        fig.update_layout(
            title=f'{industry_key} Industry P/B Comparison',
            xaxis_title='P/B Ratio',
            yaxis_title='Category',
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig

    def _create_historical_trends_tab(self, pb_analysis: Dict) -> None:
        """
        Create historical trends tab

        Args:
            pb_analysis (dict): P/B analysis results
        """
        historical_analysis = pb_analysis.get('historical_analysis', {})

        if 'error' in historical_analysis:
            st.warning(
                f"Historical analysis not available: {historical_analysis.get('error', 'Unknown error')}"
            )
            return

        historical_data = historical_analysis.get('historical_data', [])

        if not historical_data:
            st.warning("No historical P/B data available")
            return

        # Historical P/B trend chart
        fig_trend = self._create_historical_trend_chart(historical_data)
        st.plotly_chart(fig_trend, use_container_width=True)

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

    def _create_historical_trend_chart(self, historical_data: List[Dict]) -> go.Figure:
        """
        Create historical P/B trend line chart

        Args:
            historical_data (list): Historical P/B data points

        Returns:
            plotly.graph_objects.Figure: Historical trend chart
        """
        dates = [entry['date'] for entry in historical_data if entry.get('pb_ratio') is not None]
        pb_ratios = [
            entry['pb_ratio'] for entry in historical_data if entry.get('pb_ratio') is not None
        ]
        prices = [entry['price'] for entry in historical_data if entry.get('pb_ratio') is not None]

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1,
            cols=1,
            secondary_y=True,
            subplot_titles=("Historical P/B Ratio and Stock Price"),
        )

        # Add P/B ratio line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=pb_ratios,
                mode='lines+markers',
                name='P/B Ratio',
                line=dict(color=self.color_scheme['primary'], width=2),
                marker=dict(size=4),
            ),
            secondary_y=False,
        )

        # Add stock price line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name='Stock Price',
                line=dict(color=self.color_scheme['secondary'], width=1, dash='dash'),
                opacity=0.7,
            ),
            secondary_y=True,
        )

        # Set y-axes titles
        fig.update_yaxes(title_text="P/B Ratio", secondary_y=False)
        fig.update_yaxes(title_text="Stock Price ($)", secondary_y=True)

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        fig.update_layout(
            height=400,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
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

        # Valuation ranges chart
        fig_valuation = self._create_valuation_ranges_chart(ranges, current_price)
        st.plotly_chart(fig_valuation, use_container_width=True)

        # Valuation analysis table
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### P/B Based Valuation")

            valuation_df = pd.DataFrame(
                {
                    'Scenario': ['Conservative', 'Fair Value', 'Optimistic', 'Current Price'],
                    'Price Target': [
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
            st.markdown("### Methodology")
            methodology = valuation_analysis.get('methodology', 'No methodology specified')
            st.info(methodology)

            # Display industry benchmarks used
            benchmarks = valuation_analysis.get('industry_benchmarks', {})
            if benchmarks:
                st.markdown("**Industry P/B Benchmarks:**")
                st.write(f"• Low: {benchmarks.get('low', 0):.2f}")
                st.write(f"• Median: {benchmarks.get('median', 0):.2f}")
                st.write(f"• High: {benchmarks.get('high', 0):.2f}")

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
            title='P/B Based Valuation Ranges vs Current Price',
            xaxis_title='Price ($)',
            yaxis_title='Valuation Scenario',
            height=300,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig


def display_pb_analysis(pb_analysis: Dict) -> None:
    """
    Main function to display P/B analysis in Streamlit

    Args:
        pb_analysis (dict): P/B analysis results
    """
    visualizer = PBVisualizer()
    visualizer.create_pb_dashboard(pb_analysis)
