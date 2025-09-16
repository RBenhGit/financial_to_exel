"""
Company Comparison Dashboard Component
====================================

This module provides multi-company comparison capabilities with side-by-side metrics
and relative performance analysis for the advanced financial dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import logging

# Import existing components
from ui.streamlit.dashboard_components import (
    FinancialMetricsHierarchy,
    MetricDisplayComponents,
    MetricDefinition,
    MetricValue
)
from core.analysis.engines.financial_calculations import FinancialCalculator

logger = logging.getLogger(__name__)


@dataclass
class CompanyData:
    """Container for company financial data and metrics"""
    ticker: str
    name: str
    financial_calculator: FinancialCalculator
    metrics: Dict[str, MetricValue] = field(default_factory=dict)
    industry: str = "Unknown"
    market_cap: Optional[float] = None
    sector: str = "Unknown"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ComparisonConfig:
    """Configuration for comparison analysis"""
    selected_companies: List[str] = field(default_factory=list)
    comparison_metrics: List[str] = field(default_factory=list)
    reference_company: Optional[str] = None
    show_industry_benchmarks: bool = True
    normalize_by_market_cap: bool = False
    time_period: str = "5Y"


class CompanyComparisonDashboard:
    """Multi-company comparison dashboard with side-by-side metrics analysis"""

    def __init__(self):
        """Initialize comparison dashboard"""
        self.hierarchy = FinancialMetricsHierarchy()
        self.components = MetricDisplayComponents(self.hierarchy)
        self.companies_data: Dict[str, CompanyData] = {}
        self.color_palette = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'tertiary': '#F18F01',
            'quaternary': '#C73E1D',
            'quinary': '#2ECC71',
            'industry_benchmark': '#95A5A6',
            'positive': '#27AE60',
            'negative': '#E74C3C',
            'neutral': '#F39C12'
        }

    def render_comparison_dashboard(
        self,
        available_companies: Dict[str, FinancialCalculator],
        context: str = "main_comparison"
    ) -> None:
        """Render the complete company comparison dashboard"""
        st.header("🔄 Multi-Company Comparison Dashboard")

        if not available_companies:
            st.error("No companies available for comparison")
            return

        # Company selection interface
        comparison_config = self._render_company_selection_interface(
            list(available_companies.keys()),
            context
        )

        if len(comparison_config.selected_companies) < 2:
            st.info("📝 Select at least 2 companies to begin comparison analysis")
            return

        # Load company data
        self._load_company_data(available_companies, comparison_config.selected_companies)

        if not self.companies_data:
            st.error("Failed to load company data for comparison")
            return

        # Main comparison tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Side-by-Side Metrics",
            "📈 Performance Comparison",
            "🏆 Ranking Analysis",
            "📉 Relative Performance",
            "🎯 Peer Analysis"
        ])

        with tab1:
            self._render_side_by_side_metrics(comparison_config, context)

        with tab2:
            self._render_performance_comparison_charts(comparison_config, context)

        with tab3:
            self._render_ranking_analysis(comparison_config, context)

        with tab4:
            self._render_relative_performance_analysis(comparison_config, context)

        with tab5:
            self._render_peer_analysis(comparison_config, context)

    def _render_company_selection_interface(
        self,
        available_tickers: List[str],
        context: str
    ) -> ComparisonConfig:
        """Render company selection and comparison configuration interface"""

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            selected_companies = st.multiselect(
                "🏢 Select Companies to Compare (2-5 companies)",
                options=available_tickers,
                default=available_tickers[:min(3, len(available_tickers))],
                max_selections=5,
                key=f"company_selection_{context}",
                help="Choose 2-5 companies for comprehensive comparison analysis"
            )

        with col2:
            reference_company = st.selectbox(
                "📌 Reference Company",
                options=["None"] + selected_companies,
                index=0,
                key=f"reference_company_{context}",
                help="Optional: Set one company as baseline for relative comparisons"
            )

        with col3:
            time_period = st.selectbox(
                "⏱️ Time Period",
                options=["1Y", "3Y", "5Y", "10Y", "All"],
                index=2,  # Default to 5Y
                key=f"time_period_{context}"
            )

        # Advanced comparison options
        with st.expander("⚙️ Advanced Comparison Options"):
            col_adv1, col_adv2, col_adv3 = st.columns(3)

            with col_adv1:
                show_benchmarks = st.checkbox(
                    "📊 Show Industry Benchmarks",
                    value=True,
                    key=f"show_benchmarks_{context}"
                )

            with col_adv2:
                normalize_by_market_cap = st.checkbox(
                    "📏 Normalize by Market Cap",
                    value=False,
                    key=f"normalize_market_cap_{context}",
                    help="Adjust metrics relative to company size"
                )

            with col_adv3:
                comparison_metrics = st.multiselect(
                    "📋 Select Metrics for Comparison",
                    options=list(self.hierarchy.metric_definitions.keys()),
                    default=["roe", "roa", "current_ratio", "debt_to_equity", "revenue_growth"],
                    key=f"comparison_metrics_{context}"
                )

        return ComparisonConfig(
            selected_companies=selected_companies,
            comparison_metrics=comparison_metrics,
            reference_company=reference_company if reference_company != "None" else None,
            show_industry_benchmarks=show_benchmarks,
            normalize_by_market_cap=normalize_by_market_cap,
            time_period=time_period
        )

    def _load_company_data(
        self,
        available_companies: Dict[str, FinancialCalculator],
        selected_tickers: List[str]
    ) -> None:
        """Load financial data for selected companies"""
        self.companies_data.clear()

        for ticker in selected_tickers:
            if ticker in available_companies:
                try:
                    calculator = available_companies[ticker]

                    # Create company data
                    company_data = CompanyData(
                        ticker=ticker,
                        name=self._get_company_name(calculator, ticker),
                        financial_calculator=calculator,
                        industry=self._get_company_industry(calculator),
                        market_cap=self._get_market_cap(calculator),
                        sector=self._get_company_sector(calculator)
                    )

                    # Calculate metrics
                    company_data.metrics = self._calculate_company_metrics(calculator)

                    self.companies_data[ticker] = company_data
                    logger.info(f"Loaded data for {ticker}")

                except Exception as e:
                    logger.error(f"Error loading data for {ticker}: {e}")
                    st.error(f"Failed to load data for {ticker}: {e}")

    def _calculate_company_metrics(self, calculator: FinancialCalculator) -> Dict[str, MetricValue]:
        """Calculate all financial metrics for a company"""
        try:
            # Get financial metrics from the calculator
            metrics_data = calculator.get_financial_metrics()

            if 'error' in metrics_data:
                logger.warning(f"Error in metrics calculation: {metrics_data['error']}")
                return {}

            calculated_metrics = {}

            # Extract profitability metrics
            profitability = metrics_data.get('profitability', {})
            for metric_key in ['roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin']:
                if metric_key in profitability:
                    values = profitability[metric_key]
                    if values and len(values) > 0:
                        current = values[-1] * 100 if metric_key in ['roe', 'roa'] else values[-1] * 100
                        previous = values[-2] * 100 if len(values) > 1 else None
                        if metric_key in ['roe', 'roa']:
                            previous = previous if previous is not None else None

                        calculated_metrics[metric_key] = MetricValue(
                            current=current,
                            previous=previous,
                            benchmark=self._get_industry_benchmark(metric_key),
                            trend=self._determine_trend(current, previous),
                            confidence=0.8
                        )

            # Extract liquidity metrics
            liquidity = metrics_data.get('liquidity', {})
            for metric_key in ['current_ratio', 'quick_ratio']:
                if metric_key in liquidity:
                    values = liquidity[metric_key]
                    if values and len(values) > 0:
                        current = values[-1]
                        previous = values[-2] if len(values) > 1 else None

                        calculated_metrics[metric_key] = MetricValue(
                            current=current,
                            previous=previous,
                            benchmark=self._get_industry_benchmark(metric_key),
                            trend=self._determine_trend(current, previous),
                            confidence=0.9
                        )

            # Extract leverage metrics
            leverage = metrics_data.get('leverage', {})
            for metric_key in ['debt_to_equity', 'interest_coverage']:
                if metric_key in leverage:
                    values = leverage[metric_key]
                    if values and len(values) > 0:
                        current = values[-1]
                        previous = values[-2] if len(values) > 1 else None
                        # For debt ratios, lower is better
                        invert_trend = metric_key == 'debt_to_equity'

                        calculated_metrics[metric_key] = MetricValue(
                            current=current,
                            previous=previous,
                            benchmark=self._get_industry_benchmark(metric_key),
                            trend=self._determine_trend(current, previous, invert_trend),
                            confidence=0.8
                        )

            # Extract growth metrics
            growth = metrics_data.get('growth', {})
            for metric_key in ['revenue_growth', 'fcf_growth']:
                if metric_key in growth:
                    values = growth[metric_key]
                    if values and len(values) > 0:
                        current = values[-1] * 100  # Convert to percentage
                        previous = values[-2] * 100 if len(values) > 1 else None

                        calculated_metrics[metric_key] = MetricValue(
                            current=current,
                            previous=previous,
                            benchmark=self._get_industry_benchmark(metric_key),
                            trend=self._determine_trend(current, previous),
                            confidence=0.7
                        )

            return calculated_metrics

        except Exception as e:
            logger.error(f"Error calculating company metrics: {e}")
            return {}

    def _render_side_by_side_metrics(self, config: ComparisonConfig, context: str) -> None:
        """Render side-by-side metrics comparison table"""
        st.subheader("📊 Side-by-Side Financial Metrics")

        if not self.companies_data:
            st.warning("No company data available for comparison")
            return

        # Create metrics comparison table
        comparison_data = []

        # Get all available metrics across companies
        all_metrics = set()
        for company_data in self.companies_data.values():
            all_metrics.update(company_data.metrics.keys())

        # Filter by selected metrics if specified
        if config.comparison_metrics:
            metrics_to_show = [m for m in config.comparison_metrics if m in all_metrics]
        else:
            metrics_to_show = list(all_metrics)

        for metric_key in metrics_to_show:
            metric_def = self.hierarchy.metric_definitions.get(metric_key)
            if not metric_def:
                continue

            row = {
                'Metric': metric_def.name,
                'Category': metric_def.category.title(),
                'Unit': metric_def.unit
            }

            # Add company values
            for ticker, company_data in self.companies_data.items():
                if metric_key in company_data.metrics:
                    metric_value = company_data.metrics[metric_key]
                    formatted_value = f"{metric_value.current:.2f}{metric_def.unit}"

                    # Add trend indicator
                    trend_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}
                    trend_indicator = trend_emoji.get(metric_value.trend, "➡️")

                    row[f"{ticker} ({company_data.name})"] = f"{formatted_value} {trend_indicator}"
                else:
                    row[f"{ticker} ({company_data.name})"] = "N/A"

            # Add industry benchmark if enabled
            if config.show_industry_benchmarks:
                benchmark = self._get_industry_benchmark(metric_key)
                if benchmark:
                    row['Industry Benchmark'] = f"{benchmark:.2f}{metric_def.unit}"

            comparison_data.append(row)

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)

            # Add download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📄 Download Comparison Table",
                data=csv,
                file_name=f"company_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No comparable metrics found")

    def _render_performance_comparison_charts(self, config: ComparisonConfig, context: str) -> None:
        """Render performance comparison charts"""
        st.subheader("📈 Performance Comparison Charts")

        # Select metrics for charting
        chart_metrics = st.multiselect(
            "Select metrics to visualize",
            options=config.comparison_metrics,
            default=config.comparison_metrics[:4],
            key=f"chart_metrics_{context}"
        )

        if not chart_metrics:
            st.info("Select metrics to display performance charts")
            return

        # Create comparison charts
        cols = st.columns(2)
        chart_colors = list(self.color_palette.values())

        for i, metric_key in enumerate(chart_metrics):
            metric_def = self.hierarchy.metric_definitions.get(metric_key)
            if not metric_def:
                continue

            col_idx = i % 2
            with cols[col_idx]:
                fig = go.Figure()

                # Add bars for each company
                companies = list(self.companies_data.keys())
                values = []

                for ticker in companies:
                    company_data = self.companies_data[ticker]
                    if metric_key in company_data.metrics:
                        values.append(company_data.metrics[metric_key].current)
                    else:
                        values.append(0)

                fig.add_trace(go.Bar(
                    x=companies,
                    y=values,
                    name=metric_def.name,
                    marker_color=chart_colors[i % len(chart_colors)],
                    text=[f"{v:.1f}{metric_def.unit}" for v in values],
                    textposition='auto'
                ))

                # Add industry benchmark line if available
                if config.show_industry_benchmarks:
                    benchmark = self._get_industry_benchmark(metric_key)
                    if benchmark:
                        fig.add_hline(
                            y=benchmark,
                            line_dash="dash",
                            line_color="gray",
                            annotation_text=f"Industry: {benchmark:.1f}{metric_def.unit}"
                        )

                fig.update_layout(
                    title=metric_def.name,
                    height=300,
                    showlegend=False,
                    template='plotly_white'
                )

                st.plotly_chart(fig, use_container_width=True)

    def _render_ranking_analysis(self, config: ComparisonConfig, context: str) -> None:
        """Render ranking analysis across metrics"""
        st.subheader("🏆 Company Rankings Analysis")

        if not config.comparison_metrics:
            st.warning("No metrics selected for ranking analysis")
            return

        # Calculate rankings for each metric
        rankings_data = []

        for metric_key in config.comparison_metrics:
            metric_def = self.hierarchy.metric_definitions.get(metric_key)
            if not metric_def:
                continue

            # Get values for all companies
            company_values = []
            for ticker, company_data in self.companies_data.items():
                if metric_key in company_data.metrics:
                    value = company_data.metrics[metric_key].current
                    company_values.append((ticker, company_data.name, value))

            # Sort by value (higher is better for most metrics)
            reverse_sort = metric_key not in ['debt_to_equity']  # Lower debt is better
            company_values.sort(key=lambda x: x[2], reverse=reverse_sort)

            # Create ranking
            for rank, (ticker, name, value) in enumerate(company_values, 1):
                rankings_data.append({
                    'Metric': metric_def.name,
                    'Rank': rank,
                    'Company': f"{ticker} ({name})",
                    'Value': f"{value:.2f}{metric_def.unit}",
                    'Score': 100 - (rank - 1) * (100 / len(company_values))  # Score from 100 to lowest
                })

        if rankings_data:
            rankings_df = pd.DataFrame(rankings_data)

            # Display rankings table
            st.dataframe(rankings_df, use_container_width=True)

            # Create overall performance score
            st.subheader("🎯 Overall Performance Scoring")
            self._render_overall_performance_scores(rankings_df)

    def _render_overall_performance_scores(self, rankings_df: pd.DataFrame) -> None:
        """Calculate and display overall performance scores"""
        # Calculate average score per company
        avg_scores = rankings_df.groupby('Company')['Score'].mean().sort_values(ascending=False)

        # Create performance score chart
        fig = go.Figure()

        companies = avg_scores.index.tolist()
        scores = avg_scores.values.tolist()

        # Color code based on performance
        colors = []
        for score in scores:
            if score >= 80:
                colors.append(self.color_palette['positive'])
            elif score >= 60:
                colors.append(self.color_palette['neutral'])
            else:
                colors.append(self.color_palette['negative'])

        fig.add_trace(go.Bar(
            x=companies,
            y=scores,
            marker_color=colors,
            text=[f"{s:.1f}" for s in scores],
            textposition='auto',
            name='Overall Score'
        ))

        fig.update_layout(
            title="Overall Financial Performance Scores",
            yaxis_title="Performance Score (0-100)",
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display score interpretation
        st.markdown("**Score Interpretation:**")
        st.markdown("- 80-100: Excellent performance")
        st.markdown("- 60-79: Good performance")
        st.markdown("- 40-59: Average performance")
        st.markdown("- Below 40: Below average performance")

    def _render_relative_performance_analysis(self, config: ComparisonConfig, context: str) -> None:
        """Render relative performance analysis"""
        st.subheader("📉 Relative Performance Analysis")

        if not config.reference_company:
            st.info("Select a reference company to view relative performance analysis")
            return

        if config.reference_company not in self.companies_data:
            st.error(f"Reference company {config.reference_company} not found in loaded data")
            return

        reference_data = self.companies_data[config.reference_company]

        # Calculate relative performance
        relative_data = []

        for metric_key in config.comparison_metrics:
            if metric_key not in reference_data.metrics:
                continue

            reference_value = reference_data.metrics[metric_key].current

            for ticker, company_data in self.companies_data.items():
                if ticker == config.reference_company:
                    continue

                if metric_key in company_data.metrics:
                    company_value = company_data.metrics[metric_key].current

                    # Calculate relative performance
                    if reference_value != 0:
                        relative_perf = ((company_value - reference_value) / reference_value) * 100
                    else:
                        relative_perf = 0

                    metric_def = self.hierarchy.metric_definitions.get(metric_key)
                    relative_data.append({
                        'Company': f"{ticker} ({company_data.name})",
                        'Metric': metric_def.name if metric_def else metric_key,
                        'Relative_Performance': relative_perf,
                        'Company_Value': company_value,
                        'Reference_Value': reference_value
                    })

        if relative_data:
            relative_df = pd.DataFrame(relative_data)

            # Create heatmap of relative performance
            pivot_df = relative_df.pivot(index='Company', columns='Metric', values='Relative_Performance')

            fig = px.imshow(
                pivot_df.values,
                labels=dict(x="Metrics", y="Companies", color="Relative Performance (%)"),
                x=pivot_df.columns,
                y=pivot_df.index,
                color_continuous_scale="RdYlGn",
                color_continuous_midpoint=0,
                title=f"Relative Performance vs {config.reference_company}"
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Display relative performance table
            st.subheader("📊 Detailed Relative Performance")
            display_df = relative_df.copy()
            display_df['Relative_Performance'] = display_df['Relative_Performance'].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(display_df[['Company', 'Metric', 'Relative_Performance']], use_container_width=True)

    def _render_peer_analysis(self, config: ComparisonConfig, context: str) -> None:
        """Render peer analysis based on industry/sector"""
        st.subheader("🎯 Peer & Industry Analysis")

        # Group companies by industry/sector
        industry_groups = {}
        for ticker, company_data in self.companies_data.items():
            industry = company_data.industry
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append((ticker, company_data))

        if len(industry_groups) > 1:
            st.markdown("**🏭 Industry Grouping:**")
            for industry, companies in industry_groups.items():
                company_names = [f"{ticker} ({data.name})" for ticker, data in companies]
                st.markdown(f"- **{industry}:** {', '.join(company_names)}")

        # Peer comparison analysis
        st.markdown("**📊 Peer Performance Analysis:**")

        if config.comparison_metrics:
            # Calculate industry averages
            for metric_key in config.comparison_metrics[:3]:  # Limit to first 3 for display
                metric_def = self.hierarchy.metric_definitions.get(metric_key)
                if not metric_def:
                    continue

                st.markdown(f"**{metric_def.name}:**")

                # Calculate values by industry
                industry_values = {}
                for industry, companies in industry_groups.items():
                    values = []
                    for ticker, company_data in companies:
                        if metric_key in company_data.metrics:
                            values.append(company_data.metrics[metric_key].current)

                    if values:
                        industry_values[industry] = {
                            'average': np.mean(values),
                            'companies': len(values),
                            'values': values
                        }

                # Display industry comparison
                if industry_values:
                    cols = st.columns(len(industry_values))
                    for i, (industry, stats) in enumerate(industry_values.items()):
                        with cols[i]:
                            st.metric(
                                label=f"{industry} Avg",
                                value=f"{stats['average']:.2f}{metric_def.unit}",
                                delta=f"{len(stats['values'])} companies"
                            )

    def _get_company_name(self, calculator: FinancialCalculator, ticker: str) -> str:
        """Extract company name from calculator"""
        try:
            metrics = calculator.get_financial_metrics()
            company_info = metrics.get('company_info', {})
            return company_info.get('name', ticker)
        except:
            return ticker

    def _get_company_industry(self, calculator: FinancialCalculator) -> str:
        """Extract company industry from calculator"""
        try:
            metrics = calculator.get_financial_metrics()
            company_info = metrics.get('company_info', {})
            return company_info.get('industry', 'Technology')  # Default fallback
        except:
            return 'Technology'

    def _get_company_sector(self, calculator: FinancialCalculator) -> str:
        """Extract company sector from calculator"""
        try:
            metrics = calculator.get_financial_metrics()
            company_info = metrics.get('company_info', {})
            return company_info.get('sector', 'Technology')
        except:
            return 'Technology'

    def _get_market_cap(self, calculator: FinancialCalculator) -> Optional[float]:
        """Extract market cap from calculator"""
        try:
            metrics = calculator.get_financial_metrics()
            company_info = metrics.get('company_info', {})
            return company_info.get('market_cap')
        except:
            return None

    def _get_industry_benchmark(self, metric_key: str) -> Optional[float]:
        """Get industry benchmark for a metric"""
        # Industry benchmarks (these would typically come from a database)
        benchmarks = {
            'roe': 15.0,
            'roa': 8.0,
            'current_ratio': 2.0,
            'debt_to_equity': 0.5,
            'gross_margin': 40.0,
            'operating_margin': 20.0,
            'net_margin': 15.0,
            'revenue_growth': 10.0,
            'fcf_growth': 10.0,
            'quick_ratio': 1.0,
            'interest_coverage': 5.0
        }
        return benchmarks.get(metric_key)

    def _determine_trend(self, current: float, previous: Optional[float], invert: bool = False) -> str:
        """Determine trend direction"""
        if previous is None:
            return "neutral"

        if current > previous:
            return "negative" if invert else "positive"
        elif current < previous:
            return "positive" if invert else "negative"
        else:
            return "neutral"


def create_company_comparison_dashboard() -> CompanyComparisonDashboard:
    """Factory function to create CompanyComparisonDashboard instance"""
    return CompanyComparisonDashboard()


if __name__ == "__main__":
    # Demo/testing mode
    st.set_page_config(page_title="Company Comparison Dashboard", layout="wide")

    st.title("🔄 Multi-Company Comparison Dashboard Demo")
    st.markdown("---")

    dashboard = create_company_comparison_dashboard()

    # Mock data for demonstration
    st.info("This is a demo mode. In actual implementation, connect to real FinancialCalculator instances.")