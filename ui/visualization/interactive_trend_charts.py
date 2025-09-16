"""
Interactive Trend Analysis Charts Module
========================================

This module provides interactive trend analysis charts for financial metrics including
revenue, profit, cash flow with time period selectors and drill-down capabilities.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChartPeriod:
    """Represents a chart time period configuration"""
    label: str
    years: int
    quarters: Optional[int] = None

    @property
    def total_periods(self) -> int:
        """Total number of periods for data filtering"""
        return self.quarters if self.quarters else self.years


class InteractiveTrendCharts:
    """
    Interactive trend charts with time period selectors and drill-down capabilities
    """

    def __init__(self):
        """Initialize interactive trend charts"""
        self.color_palette = {
            'revenue': '#2E86AB',      # Blue
            'profit': '#A23B72',       # Purple
            'cash_flow': '#F18F01',    # Orange
            'operating_income': '#C73E1D',  # Red
            'net_income': '#592E83',   # Dark Purple
            'fcf': '#00B4A6',          # Teal
            'growth_positive': '#2ECC71',  # Green
            'growth_negative': '#E74C3C', # Red
            'trend_line': '#34495E',   # Dark Gray
            'benchmark': '#95A5A6'     # Light Gray
        }

        self.chart_periods = {
            '1Y': ChartPeriod('1 Year', 1, 4),      # 4 quarters
            '3Y': ChartPeriod('3 Years', 3, 12),    # 12 quarters
            '5Y': ChartPeriod('5 Years', 5),        # 5 years
            '10Y': ChartPeriod('10 Years', 10),     # 10 years
            'All': ChartPeriod('All Available', 999) # All data
        }

    def render_revenue_trend_chart(
        self,
        financial_data: Dict[str, Any],
        context: str = "dashboard"
    ) -> None:
        """Render interactive revenue trend chart"""
        st.subheader("📈 Revenue Trend Analysis")

        # Time period selector
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            selected_period = st.selectbox(
                "Select Time Period",
                options=list(self.chart_periods.keys()),
                index=2,  # Default to 5Y
                key=f"revenue_period_{context}"
            )

        with col2:
            show_growth_rate = st.checkbox(
                "Show Growth Rate",
                value=True,
                key=f"revenue_growth_{context}"
            )

        with col3:
            chart_type = st.selectbox(
                "Chart Type",
                ["Line", "Bar", "Area"],
                key=f"revenue_chart_type_{context}"
            )

        # Extract revenue data
        revenue_data = self._extract_revenue_data(financial_data, selected_period)

        if not revenue_data:
            st.warning("No revenue data available for the selected period")
            return

        # Create the chart
        fig = self._create_revenue_chart(
            revenue_data,
            chart_type,
            show_growth_rate,
            selected_period
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add drill-down capability
        if selected_period in ['5Y', '10Y', 'All']:
            if st.button(f"📊 Drill Down to Quarterly View", key=f"revenue_drill_{context}"):
                self._render_quarterly_drill_down(revenue_data, "Revenue")

    def render_profit_trend_chart(
        self,
        financial_data: Dict[str, Any],
        context: str = "dashboard"
    ) -> None:
        """Render interactive profit trend chart"""
        st.subheader("💰 Profit Trend Analysis")

        # Profit metrics selector
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            profit_metrics = st.multiselect(
                "Select Profit Metrics",
                ["Net Income", "Operating Income", "Gross Profit", "EBITDA"],
                default=["Net Income", "Operating Income"],
                key=f"profit_metrics_{context}"
            )

        with col2:
            selected_period = st.selectbox(
                "Time Period",
                options=list(self.chart_periods.keys()),
                index=2,
                key=f"profit_period_{context}"
            )

        with col3:
            show_margins = st.checkbox(
                "Show Margins",
                value=False,
                key=f"profit_margins_{context}"
            )

        # Extract profit data
        profit_data = self._extract_profit_data(financial_data, selected_period, profit_metrics)

        if not profit_data:
            st.warning("No profit data available for the selected period")
            return

        # Create the chart
        fig = self._create_profit_chart(
            profit_data,
            profit_metrics,
            show_margins,
            selected_period
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_cash_flow_trend_chart(
        self,
        fcf_data: Dict[str, Any],
        context: str = "dashboard"
    ) -> None:
        """Render interactive cash flow trend chart"""
        st.subheader("💸 Cash Flow Trend Analysis")

        # FCF type selector
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            fcf_types = st.multiselect(
                "Select FCF Types",
                ["FCFE", "FCFF", "LFCF"],
                default=["FCFE", "FCFF"],
                key=f"fcf_types_{context}"
            )

        with col2:
            selected_period = st.selectbox(
                "Time Period",
                options=list(self.chart_periods.keys()),
                index=2,
                key=f"fcf_period_{context}"
            )

        with col3:
            show_trend_lines = st.checkbox(
                "Show Trend Lines",
                value=True,
                key=f"fcf_trends_{context}"
            )

        # Extract FCF data
        cash_flow_data = self._extract_fcf_data(fcf_data, selected_period, fcf_types)

        if not cash_flow_data:
            st.warning("No cash flow data available for the selected period")
            return

        # Create the chart
        fig = self._create_cash_flow_chart(
            cash_flow_data,
            fcf_types,
            show_trend_lines,
            selected_period
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display FCF averages and growth rates
        if cash_flow_data:
            self._display_fcf_summary_metrics(cash_flow_data, fcf_types)

    def render_comprehensive_trends_dashboard(
        self,
        financial_data: Dict[str, Any],
        fcf_data: Dict[str, Any],
        context: str = "main_dashboard"
    ) -> None:
        """Render comprehensive trends dashboard with all metrics"""
        st.header("📊 Comprehensive Financial Trends Dashboard")

        # Global controls
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            global_period = st.selectbox(
                "Global Time Period",
                options=list(self.chart_periods.keys()),
                index=2,
                key=f"global_period_{context}"
            )

        with col2:
            sync_periods = st.checkbox(
                "Sync All Charts",
                value=True,
                key=f"sync_periods_{context}"
            )

        with col3:
            show_annotations = st.checkbox(
                "Show Annotations",
                value=True,
                key=f"show_annotations_{context}"
            )

        with col4:
            export_data = st.button(
                "📄 Export Data",
                key=f"export_trends_{context}"
            )

        # Create tabs for different trend views
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenue", "💰 Profitability", "💸 Cash Flow", "🔄 Combined"])

        with tab1:
            period = global_period if sync_periods else None
            self._render_detailed_revenue_trends(financial_data, period, context + "_rev")

        with tab2:
            period = global_period if sync_periods else None
            self._render_detailed_profit_trends(financial_data, period, context + "_prof")

        with tab3:
            period = global_period if sync_periods else None
            self._render_detailed_cash_flow_trends(fcf_data, period, context + "_cf")

        with tab4:
            self._render_combined_metrics_chart(financial_data, fcf_data, global_period, context + "_comb")

        if export_data:
            self._export_trend_data(financial_data, fcf_data, global_period)

    def _extract_revenue_data(self, financial_data: Dict[str, Any], period: str) -> Dict[str, List]:
        """Extract revenue data for the specified period"""
        try:
            # This is a placeholder - in a real implementation, you would extract
            # actual revenue data from the financial_data structure
            years = self.chart_periods[period].years

            # Sample data structure (replace with actual data extraction)
            sample_data = {
                'years': [2020, 2021, 2022, 2023, 2024],
                'revenue': [100000, 110000, 125000, 140000, 150000],
                'growth_rates': [None, 10.0, 13.6, 12.0, 7.1]
            }

            # Filter by period
            if period != 'All':
                max_periods = min(years, len(sample_data['years']))
                sample_data = {
                    'years': sample_data['years'][-max_periods:],
                    'revenue': sample_data['revenue'][-max_periods:],
                    'growth_rates': sample_data['growth_rates'][-max_periods:]
                }

            return sample_data

        except Exception as e:
            logger.error(f"Error extracting revenue data: {e}")
            return {}

    def _extract_profit_data(
        self,
        financial_data: Dict[str, Any],
        period: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Extract profit data for specified metrics and period"""
        try:
            # Sample data structure (replace with actual data extraction)
            sample_data = {
                'years': [2020, 2021, 2022, 2023, 2024],
                'Net Income': [20000, 25000, 30000, 35000, 40000],
                'Operating Income': [30000, 35000, 42000, 48000, 52000],
                'Gross Profit': [60000, 66000, 75000, 84000, 90000],
                'EBITDA': [35000, 40000, 47000, 53000, 57000]
            }

            # Filter by period
            years = self.chart_periods[period].years
            if period != 'All':
                max_periods = min(years, len(sample_data['years']))
                filtered_data = {'years': sample_data['years'][-max_periods:]}
                for metric in metrics:
                    if metric in sample_data:
                        filtered_data[metric] = sample_data[metric][-max_periods:]
                return filtered_data

            return {k: v for k, v in sample_data.items() if k == 'years' or k in metrics}

        except Exception as e:
            logger.error(f"Error extracting profit data: {e}")
            return {}

    def _extract_fcf_data(
        self,
        fcf_data: Dict[str, Any],
        period: str,
        fcf_types: List[str]
    ) -> Dict[str, Any]:
        """Extract FCF data for specified types and period"""
        try:
            if not fcf_data:
                return {}

            # Extract from actual FCF data structure
            extracted_data = {'years': []}

            # If fcf_data has the expected structure from FCFCalculator
            if 'FCFE' in fcf_data and isinstance(fcf_data['FCFE'], list):
                # Assume years are sequential from current year backwards
                current_year = datetime.now().year
                num_years = len(fcf_data['FCFE'])
                extracted_data['years'] = list(range(current_year - num_years + 1, current_year + 1))

                for fcf_type in fcf_types:
                    if fcf_type in fcf_data and isinstance(fcf_data[fcf_type], list):
                        extracted_data[fcf_type] = fcf_data[fcf_type]
            else:
                # Fallback to sample data
                sample_data = {
                    'years': [2020, 2021, 2022, 2023, 2024],
                    'FCFE': [15000, 18000, 22000, 25000, 28000],
                    'FCFF': [25000, 28000, 32000, 35000, 38000],
                    'LFCF': [20000, 23000, 27000, 30000, 33000]
                }
                extracted_data = sample_data

            # Filter by period
            years = self.chart_periods[period].years
            if period != 'All':
                max_periods = min(years, len(extracted_data['years']))
                filtered_data = {'years': extracted_data['years'][-max_periods:]}
                for fcf_type in fcf_types:
                    if fcf_type in extracted_data:
                        filtered_data[fcf_type] = extracted_data[fcf_type][-max_periods:]
                return filtered_data

            return {k: v for k, v in extracted_data.items() if k == 'years' or k in fcf_types}

        except Exception as e:
            logger.error(f"Error extracting FCF data: {e}")
            return {}

    def _create_revenue_chart(
        self,
        data: Dict[str, List],
        chart_type: str,
        show_growth: bool,
        period: str
    ) -> go.Figure:
        """Create interactive revenue chart"""
        years = data.get('years', [])
        revenue = data.get('revenue', [])
        growth_rates = data.get('growth_rates', [])

        # Create subplot if showing growth rates
        if show_growth and growth_rates:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Revenue Trend', 'Growth Rate (%)'),
                vertical_spacing=0.15,
                row_heights=[0.7, 0.3]
            )
        else:
            fig = go.Figure()

        # Main revenue chart
        if chart_type == "Line":
            trace = go.Scatter(
                x=years,
                y=revenue,
                mode='lines+markers',
                name='Revenue',
                line=dict(color=self.color_palette['revenue'], width=3),
                marker=dict(size=8),
                hovertemplate='<b>Year:</b> %{x}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
            )
        elif chart_type == "Bar":
            trace = go.Bar(
                x=years,
                y=revenue,
                name='Revenue',
                marker_color=self.color_palette['revenue'],
                hovertemplate='<b>Year:</b> %{x}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
            )
        else:  # Area
            trace = go.Scatter(
                x=years,
                y=revenue,
                mode='lines',
                fill='tonexty',
                name='Revenue',
                line=dict(color=self.color_palette['revenue']),
                hovertemplate='<b>Year:</b> %{x}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
            )

        if show_growth and growth_rates:
            fig.add_trace(trace, row=1, col=1)

            # Growth rate chart
            growth_colors = [
                self.color_palette['growth_positive'] if gr and gr > 0
                else self.color_palette['growth_negative']
                for gr in growth_rates
            ]

            fig.add_trace(
                go.Bar(
                    x=years,
                    y=growth_rates,
                    name='Growth Rate',
                    marker_color=growth_colors,
                    hovertemplate='<b>Year:</b> %{x}<br><b>Growth:</b> %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
        else:
            fig.add_trace(trace)

        # Add trend line
        if len(years) > 2:
            trend_line = np.poly1d(np.polyfit(range(len(years)), revenue, 1))
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=[trend_line(i) for i in range(len(years))],
                    mode='lines',
                    name='Trend',
                    line=dict(color=self.color_palette['trend_line'], dash='dash', width=2),
                    hovertemplate='<b>Trend Line</b><extra></extra>'
                ),
                row=1 if show_growth else None, col=1 if show_growth else None
            )

        # Update layout
        title = f"Revenue Trend Analysis ({period})"
        fig.update_layout(
            title=title,
            height=600 if show_growth else 400,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def _create_profit_chart(
        self,
        data: Dict[str, Any],
        metrics: List[str],
        show_margins: bool,
        period: str
    ) -> go.Figure:
        """Create interactive profit chart"""
        years = data.get('years', [])

        if show_margins:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Profit Metrics', 'Profit Margins (%)'),
                vertical_spacing=0.15
            )
        else:
            fig = go.Figure()

        # Color mapping for different metrics
        color_map = {
            'Net Income': self.color_palette['net_income'],
            'Operating Income': self.color_palette['operating_income'],
            'Gross Profit': self.color_palette['revenue'],
            'EBITDA': self.color_palette['cash_flow']
        }

        for metric in metrics:
            if metric in data:
                values = data[metric]
                fig.add_trace(
                    go.Scatter(
                        x=years,
                        y=values,
                        mode='lines+markers',
                        name=metric,
                        line=dict(color=color_map.get(metric, self.color_palette['profit']), width=3),
                        marker=dict(size=6),
                        hovertemplate=f'<b>{metric}:</b> ${{y:,.0f}}<extra></extra>'
                    ),
                    row=1 if show_margins else None, col=1 if show_margins else None
                )

        # Add margins if requested
        if show_margins and 'Net Income' in data and 'revenue' in data:
            # Calculate margins (simplified - in real implementation, get from financial data)
            revenue = data.get('revenue', [100000] * len(years))  # Placeholder
            margins = [(data[metric][i] / revenue[i] * 100) if revenue[i] > 0 else 0
                      for i, metric in enumerate(metrics) if metric in data]

            if margins:
                fig.add_trace(
                    go.Bar(
                        x=years,
                        y=margins[:len(years)],  # Ensure same length
                        name='Net Margin %',
                        marker_color=self.color_palette['profit'],
                        hovertemplate='<b>Net Margin:</b> %{y:.1f}%<extra></extra>'
                    ),
                    row=2, col=1
                )

        fig.update_layout(
            title=f"Profit Trend Analysis ({period})",
            height=600 if show_margins else 400,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def _create_cash_flow_chart(
        self,
        data: Dict[str, Any],
        fcf_types: List[str],
        show_trends: bool,
        period: str
    ) -> go.Figure:
        """Create interactive cash flow chart"""
        years = data.get('years', [])

        fig = go.Figure()

        # Color mapping for FCF types
        color_map = {
            'FCFE': self.color_palette['fcf'],
            'FCFF': self.color_palette['cash_flow'],
            'LFCF': self.color_palette['operating_income']
        }

        for fcf_type in fcf_types:
            if fcf_type in data:
                values = data[fcf_type]
                fig.add_trace(
                    go.Scatter(
                        x=years,
                        y=values,
                        mode='lines+markers',
                        name=fcf_type,
                        line=dict(color=color_map.get(fcf_type, self.color_palette['cash_flow']), width=3),
                        marker=dict(size=8),
                        hovertemplate=f'<b>{fcf_type}:</b> ${{y:,.0f}}<extra></extra>'
                    )
                )

                # Add trend line if requested
                if show_trends and len(values) > 2:
                    trend_line = np.poly1d(np.polyfit(range(len(years)), values, 1))
                    fig.add_trace(
                        go.Scatter(
                            x=years,
                            y=[trend_line(i) for i in range(len(years))],
                            mode='lines',
                            name=f'{fcf_type} Trend',
                            line=dict(
                                color=color_map.get(fcf_type, self.color_palette['cash_flow']),
                                dash='dash',
                                width=1
                            ),
                            showlegend=False,
                            hovertemplate=f'<b>{fcf_type} Trend</b><extra></extra>'
                        )
                    )

        # Add zero line for reference
        if years:
            fig.add_hline(
                y=0,
                line_dash="dot",
                line_color="gray",
                annotation_text="Break-even"
            )

        fig.update_layout(
            title=f"Cash Flow Trend Analysis ({period})",
            height=500,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified',
            yaxis_title="Cash Flow ($)"
        )

        return fig

    def _render_quarterly_drill_down(self, data: Dict[str, Any], metric_name: str) -> None:
        """Render quarterly drill-down view"""
        st.subheader(f"📊 Quarterly {metric_name} Breakdown")

        # Create quarterly data (placeholder - replace with actual quarterly data extraction)
        quarters = ['Q1 2023', 'Q2 2023', 'Q3 2023', 'Q4 2023', 'Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
        values = [25000, 27000, 26000, 35000, 28000, 30000, 29000, 38000]  # Sample quarterly data

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=quarters,
                y=values,
                name=f'Quarterly {metric_name}',
                marker_color=self.color_palette['revenue'],
                hovertemplate=f'<b>{{x}}</b><br><b>{metric_name}:</b> ${{y:,.0f}}<extra></extra>'
            )
        )

        fig.update_layout(
            title=f"Quarterly {metric_name} Analysis",
            height=400,
            template='plotly_white',
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)

    def _display_fcf_summary_metrics(self, data: Dict[str, Any], fcf_types: List[str]) -> None:
        """Display FCF summary metrics"""
        st.subheader("📊 Cash Flow Summary Metrics")

        cols = st.columns(len(fcf_types))

        for i, fcf_type in enumerate(fcf_types):
            if fcf_type in data:
                values = data[fcf_type]
                avg_fcf = np.mean(values)
                growth_rate = ((values[-1] / values[0]) ** (1/(len(values)-1)) - 1) * 100 if len(values) > 1 and values[0] != 0 else 0

                with cols[i]:
                    st.metric(
                        label=f"{fcf_type} Average",
                        value=f"${avg_fcf:,.0f}",
                        delta=f"{growth_rate:.1f}% CAGR"
                    )

    def _render_detailed_revenue_trends(self, financial_data: Dict[str, Any], period: Optional[str], context: str) -> None:
        """Render detailed revenue trends in tab"""
        if period:
            st.info(f"Synchronized to {period} period")

        # Use the main revenue chart method
        self.render_revenue_trend_chart(financial_data, context)

    def _render_detailed_profit_trends(self, financial_data: Dict[str, Any], period: Optional[str], context: str) -> None:
        """Render detailed profit trends in tab"""
        if period:
            st.info(f"Synchronized to {period} period")

        # Use the main profit chart method
        self.render_profit_trend_chart(financial_data, context)

    def _render_detailed_cash_flow_trends(self, fcf_data: Dict[str, Any], period: Optional[str], context: str) -> None:
        """Render detailed cash flow trends in tab"""
        if period:
            st.info(f"Synchronized to {period} period")

        # Use the main cash flow chart method
        self.render_cash_flow_trend_chart(fcf_data, context)

    def _render_combined_metrics_chart(
        self,
        financial_data: Dict[str, Any],
        fcf_data: Dict[str, Any],
        period: str,
        context: str
    ) -> None:
        """Render combined metrics chart"""
        st.subheader("🔄 Combined Financial Metrics")

        # Extract data for all metrics
        revenue_data = self._extract_revenue_data(financial_data, period)
        fcf_data_extracted = self._extract_fcf_data(fcf_data, period, ['FCFE'])

        if not revenue_data or not fcf_data_extracted:
            st.warning("Insufficient data for combined chart")
            return

        years = revenue_data.get('years', [])

        # Create combined chart with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Revenue on primary y-axis
        fig.add_trace(
            go.Scatter(
                x=years,
                y=revenue_data.get('revenue', []),
                mode='lines+markers',
                name='Revenue',
                line=dict(color=self.color_palette['revenue'], width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )

        # FCF on secondary y-axis
        if 'FCFE' in fcf_data_extracted:
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=fcf_data_extracted['FCFE'],
                    mode='lines+markers',
                    name='FCFE',
                    line=dict(color=self.color_palette['fcf'], width=3),
                    marker=dict(size=8)
                ),
                secondary_y=True
            )

        # Update layout
        fig.update_layout(
            title=f"Combined Financial Metrics ({period})",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )

        fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig.update_yaxes(title_text="Free Cash Flow ($)", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)

    def _export_trend_data(self, financial_data: Dict[str, Any], fcf_data: Dict[str, Any], period: str) -> None:
        """Export trend data to CSV"""
        try:
            # Extract all data
            revenue_data = self._extract_revenue_data(financial_data, period)
            fcf_data_extracted = self._extract_fcf_data(fcf_data, period, ['FCFE', 'FCFF', 'LFCF'])

            # Combine into DataFrame
            years = revenue_data.get('years', [])
            export_df = pd.DataFrame({'Year': years})

            if 'revenue' in revenue_data:
                export_df['Revenue'] = revenue_data['revenue']

            for fcf_type in ['FCFE', 'FCFF', 'LFCF']:
                if fcf_type in fcf_data_extracted:
                    export_df[fcf_type] = fcf_data_extracted[fcf_type]

            # Provide download
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Trend Data CSV",
                data=csv,
                file_name=f"financial_trends_{period}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

            st.success("✅ Export data prepared for download")

        except Exception as e:
            st.error(f"Error exporting data: {e}")
            logger.error(f"Export error: {e}")


def create_interactive_trend_charts() -> InteractiveTrendCharts:
    """Factory function to create InteractiveTrendCharts instance"""
    return InteractiveTrendCharts()