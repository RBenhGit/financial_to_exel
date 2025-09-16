"""
Advanced Ratio Dashboard with Industry Comparisons
==================================================

Enhanced Streamlit dashboard that integrates the advanced ratio analysis module
with sophisticated visualizations, trend analysis, and industry benchmarking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Import the advanced ratio analysis components
from core.analysis.ratios import (
    AdvancedRatioAnalyzer,
    IndustryBenchmarkManager,
    PeerComparisonEngine,
    RatioStatisticalAnalysis
)

logger = logging.getLogger(__name__)


class AdvancedRatioDashboard:
    """Advanced dashboard for comprehensive ratio analysis"""

    def __init__(self):
        """Initialize the advanced dashboard"""
        self.ratio_analyzer = AdvancedRatioAnalyzer()
        self.benchmark_manager = IndustryBenchmarkManager()

        # Color schemes
        self.color_scheme = {
            'excellent': '#2E8B57',     # Sea Green
            'good': '#3CB371',          # Medium Sea Green
            'average': '#FFD700',       # Gold
            'poor': '#FF6347',          # Tomato
            'background': '#F8F9FA',    # Light Gray
            'primary': '#1f77b4',       # Blue
            'secondary': '#ff7f0e'      # Orange
        }

    def render_dashboard(self, financial_calculator, company_info: Optional[Dict] = None) -> None:
        """Render the complete advanced ratio dashboard"""

        st.title("🏆 Advanced Financial Ratio Analysis")
        st.markdown("---")

        try:
            # Get financial metrics from calculator
            metrics = financial_calculator.get_financial_metrics()

            if 'error' in metrics:
                st.error(f"Error loading financial data: {metrics['error']}")
                return

            # Extract company information
            company_data = metrics.get('company_info', {})
            ticker = company_data.get('ticker', 'Unknown')
            company_name = company_data.get('name', ticker)

            # Configuration sidebar
            with st.sidebar:
                st.header("⚙️ Analysis Configuration")

                # Industry selection
                available_industries = self.benchmark_manager.get_available_industries()
                selected_industry = st.selectbox(
                    "Industry Classification",
                    available_industries,
                    index=0 if 'Technology' in available_industries else 0
                )

                # Analysis options
                include_peer_analysis = st.checkbox("Include Peer Comparison", value=True)
                include_trend_analysis = st.checkbox("Include Trend Analysis", value=True)
                include_statistical_analysis = st.checkbox("Include Statistical Analysis", value=True)

                st.markdown("---")
                confidence_level = st.slider("Statistical Confidence Level", 0.90, 0.99, 0.95, 0.01)

            # Main dashboard content
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.subheader(f"📊 {company_name} ({ticker})")
                st.write(f"**Industry:** {selected_industry}")

            with col2:
                if include_peer_analysis:
                    st.metric("Peer Analysis", "Enabled", "✓")
                else:
                    st.metric("Peer Analysis", "Disabled", "✗")

            with col3:
                analysis_date = datetime.now().strftime("%Y-%m-%d")
                st.metric("Analysis Date", analysis_date)

            # Extract ratio data for analysis
            current_ratios = self._extract_current_ratios(metrics)
            historical_ratios = self._extract_historical_ratios(metrics)

            if not current_ratios:
                st.warning("No ratio data available for analysis")
                return

            # Perform comprehensive analysis
            with st.spinner("🔄 Performing advanced ratio analysis..."):
                report = self.ratio_analyzer.analyze_company(
                    company_ticker=ticker,
                    company_name=company_name,
                    industry=selected_industry,
                    current_ratios=current_ratios,
                    historical_ratios=historical_ratios if include_trend_analysis else None,
                    peer_data=self._get_mock_peer_data(selected_industry) if include_peer_analysis else None
                )

            # Display results in tabs
            tabs = st.tabs([
                "📈 Overview",
                "🎯 Industry Benchmarks",
                "📊 Peer Comparison",
                "📉 Trend Analysis",
                "⚡ Statistical Insights",
                "🎯 Strategic Recommendations"
            ])

            with tabs[0]:
                self._render_overview_tab(report)

            with tabs[1]:
                self._render_benchmark_tab(report, selected_industry)

            with tabs[2]:
                if include_peer_analysis and report.peer_analysis:
                    self._render_peer_comparison_tab(report.peer_analysis)
                else:
                    st.info("Peer comparison not available or disabled")

            with tabs[3]:
                if include_trend_analysis and historical_ratios:
                    self._render_trend_analysis_tab(report, historical_ratios)
                else:
                    st.info("Trend analysis requires historical data")

            with tabs[4]:
                if include_statistical_analysis and report.statistical_summary:
                    self._render_statistical_tab(report.statistical_summary)
                else:
                    st.info("Statistical analysis not available")

            with tabs[5]:
                self._render_recommendations_tab(report)

        except Exception as e:
            st.error(f"Error in dashboard rendering: {e}")
            logger.error(f"Dashboard error: {e}")

    def _render_overview_tab(self, report) -> None:
        """Render the overview tab with key metrics"""
        st.subheader("📈 Financial Health Overview")

        # Overall health metrics
        health = report.overall_financial_health

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            score = health.get('score', 0)
            delta_color = 'normal' if score >= 70 else 'inverse'
            st.metric(
                "Overall Score",
                f"{score}/100",
                delta=health.get('grade', 'N/A'),
                delta_color=delta_color
            )

        with col2:
            risk_level = report.risk_assessment.get('risk_level', 'Unknown')
            risk_color = 'normal' if risk_level == 'Low' else 'inverse'
            st.metric("Risk Level", risk_level, delta_color=risk_color)

        with col3:
            strong_areas = len(health.get('strong_areas', []))
            st.metric("Strong Areas", strong_areas)

        with col4:
            weak_areas = len(health.get('weak_areas', []))
            weak_color = 'normal' if weak_areas <= 2 else 'inverse'
            st.metric("Areas for Improvement", weak_areas, delta_color=weak_color)

        # Performance radar chart
        if report.enhanced_ratios:
            self._render_performance_radar(report)

        # Key ratio cards
        st.subheader("🎯 Key Financial Ratios")
        self._render_ratio_cards(report.enhanced_ratios)

    def _render_benchmark_tab(self, report, industry: str) -> None:
        """Render industry benchmark comparison"""
        st.subheader(f"🏭 {industry} Industry Benchmarks")

        # Industry profile information
        industry_profile = self.benchmark_manager.get_industry_profile(industry)

        if industry_profile:
            with st.expander("Industry Profile", expanded=True):
                st.write(f"**Description:** {industry_profile.description}")
                st.write("**Typical Characteristics:**")
                for char in industry_profile.typical_characteristics:
                    st.write(f"• {char}")

        # Benchmark comparison chart
        self._render_benchmark_comparison_chart(report, industry)

        # Detailed benchmark table
        self._render_benchmark_table(report, industry)

    def _render_peer_comparison_tab(self, peer_analysis) -> None:
        """Render peer comparison analysis"""
        st.subheader("👥 Peer Group Analysis")

        if not peer_analysis:
            st.info("No peer comparison data available")
            return

        # Peer group overview
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Overall Ranking", f"#{peer_analysis.overall_ranking}")
            st.metric("Total Peers", len(peer_analysis.peer_group))

        with col2:
            strengths = len(peer_analysis.strength_areas)
            weaknesses = len(peer_analysis.weakness_areas)
            st.metric("Strength Areas", strengths)
            st.metric("Weakness Areas", weaknesses)

        # Competitive positioning chart
        self._render_competitive_positioning(peer_analysis)

        # Peer comparison summary
        st.write("**Competitive Summary:**")
        st.write(peer_analysis.competitive_summary)

    def _render_trend_analysis_tab(self, report, historical_ratios: Dict[str, List[float]]) -> None:
        """Render trend analysis visualizations"""
        st.subheader("📈 Trend Analysis")

        # Trend summary
        improving_trends = []
        declining_trends = []
        stable_trends = []

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.trend_analysis:
                trend_dir = enhanced_ratio.trend_analysis.trend_direction
                if trend_dir == "improving":
                    improving_trends.append(ratio_name)
                elif trend_dir == "declining":
                    declining_trends.append(ratio_name)
                else:
                    stable_trends.append(ratio_name)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Improving Trends", len(improving_trends), "🟢")

        with col2:
            st.metric("Declining Trends", len(declining_trends), "🔴")

        with col3:
            st.metric("Stable Trends", len(stable_trends), "🟡")

        # Trend visualization
        self._render_trend_charts(historical_ratios)

    def _render_statistical_tab(self, statistical_summary: Dict[str, Any]) -> None:
        """Render statistical analysis results"""
        st.subheader("📊 Statistical Analysis")

        summary = statistical_summary.get('summary', {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Ratios", summary.get('total_ratios', 0))

        with col2:
            st.metric("High Volatility Ratios", summary.get('high_volatility_ratios', 0))

        with col3:
            st.metric("Significant Correlations", summary.get('significant_correlations', 0))

        # Correlation matrix
        correlation_data = statistical_summary.get('correlation_analysis', {})
        if correlation_data and hasattr(correlation_data, 'correlation_matrix'):
            self._render_correlation_matrix(correlation_data)

    def _render_recommendations_tab(self, report) -> None:
        """Render strategic recommendations"""
        st.subheader("🎯 Strategic Recommendations")

        # Strategic insights
        if report.strategic_insights:
            st.write("**Key Strategic Insights:**")
            for i, insight in enumerate(report.strategic_insights, 1):
                st.write(f"{i}. {insight}")

        st.markdown("---")

        # Risk factors
        risk_factors = report.risk_assessment.get('risk_factors', [])
        if risk_factors:
            st.write("**Risk Factors to Monitor:**")
            for factor in risk_factors:
                st.warning(f"⚠️ {factor}")

        # Ratio-specific recommendations
        st.write("**Ratio-Specific Recommendations:**")
        recommendations_found = False

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.recommendations:
                recommendations_found = True
                with st.expander(f"📊 {ratio_name.replace('_', ' ').title()}", expanded=False):
                    for rec in enhanced_ratio.recommendations:
                        st.write(f"• {rec}")

        if not recommendations_found:
            st.info("No specific recommendations generated")

    def _render_performance_radar(self, report) -> None:
        """Create performance radar chart"""
        # Extract performance scores by category
        category_scores = report.overall_financial_health.get('category_scores', {})

        if not category_scores:
            st.info("Performance radar not available")
            return

        categories = list(category_scores.keys())
        scores = list(category_scores.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=[cat.replace('_', ' ').title() for cat in categories],
            fill='toself',
            name='Performance Score',
            line_color=self.color_scheme['primary']
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Performance Radar Chart",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_ratio_cards(self, enhanced_ratios: Dict) -> None:
        """Render ratio performance cards"""
        # Select key ratios for display
        key_ratios = ['roe', 'current_ratio', 'debt_to_equity', 'gross_margin']
        available_ratios = [r for r in key_ratios if r in enhanced_ratios]

        if available_ratios:
            cols = st.columns(len(available_ratios))

            for idx, ratio_name in enumerate(available_ratios):
                enhanced_ratio = enhanced_ratios[ratio_name]

                with cols[idx]:
                    # Performance indicator color
                    position = enhanced_ratio.industry_position
                    if position == "leader":
                        color = self.color_scheme['excellent']
                    elif position == "above_average":
                        color = self.color_scheme['good']
                    elif position == "below_average":
                        color = self.color_scheme['average']
                    else:
                        color = self.color_scheme['poor']

                    st.markdown(
                        f"""
                        <div style="
                            padding: 1rem;
                            border-radius: 0.5rem;
                            border-left: 4px solid {color};
                            background-color: {self.color_scheme['background']};
                        ">
                            <h4>{ratio_name.replace('_', ' ').title()}</h4>
                            <h2>{enhanced_ratio.current_value:.2f}</h2>
                            <p>Position: {position.replace('_', ' ').title()}</p>
                            <p>Score: {enhanced_ratio.performance_score:.1f}/100</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    def _render_benchmark_comparison_chart(self, report, industry: str) -> None:
        """Create benchmark comparison chart"""
        ratios_data = []

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.industry_benchmark:
                benchmark = enhanced_ratio.industry_benchmark

                ratios_data.append({
                    'Ratio': ratio_name.replace('_', ' ').title(),
                    'Company': enhanced_ratio.current_value,
                    'Industry 25th': benchmark.percentile_25,
                    'Industry Median': benchmark.median,
                    'Industry 75th': benchmark.percentile_75
                })

        if ratios_data:
            df = pd.DataFrame(ratios_data)

            fig = go.Figure()

            # Add company values
            fig.add_trace(go.Bar(
                name='Company',
                x=df['Ratio'],
                y=df['Company'],
                marker_color=self.color_scheme['primary']
            ))

            # Add industry benchmarks
            fig.add_trace(go.Bar(
                name='Industry Median',
                x=df['Ratio'],
                y=df['Industry Median'],
                marker_color=self.color_scheme['secondary'],
                opacity=0.7
            ))

            fig.update_layout(
                title='Company vs Industry Benchmarks',
                barmode='group',
                height=500,
                xaxis_title='Financial Ratios',
                yaxis_title='Value'
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_benchmark_table(self, report, industry: str) -> None:
        """Create detailed benchmark comparison table"""
        table_data = []

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.industry_benchmark:
                benchmark = enhanced_ratio.industry_benchmark

                table_data.append({
                    'Ratio': ratio_name.replace('_', ' ').title(),
                    'Company Value': f"{enhanced_ratio.current_value:.2f}",
                    'Industry 25th': f"{benchmark.percentile_25:.2f}",
                    'Industry Median': f"{benchmark.median:.2f}",
                    'Industry 75th': f"{benchmark.percentile_75:.2f}",
                    'Position': enhanced_ratio.industry_position.replace('_', ' ').title(),
                    'Percentile': f"{enhanced_ratio.performance_score:.1f}"
                })

        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

    def _render_competitive_positioning(self, peer_analysis) -> None:
        """Create competitive positioning visualization"""
        if not peer_analysis.ratio_comparisons:
            st.info("No peer comparison data available for visualization")
            return

        # Create scatter plot of performance vs peers
        ratio_names = []
        percentile_ranks = []

        for ratio_name, comparison in peer_analysis.ratio_comparisons.items():
            ratio_names.append(ratio_name.replace('_', ' ').title())
            percentile_ranks.append(comparison.percentile_rank)

        if ratio_names:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=ratio_names,
                y=percentile_ranks,
                mode='markers+lines',
                name='Percentile Rank',
                marker=dict(
                    size=10,
                    color=percentile_ranks,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Percentile Rank")
                )
            ))

            # Add benchmark lines
            fig.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="Top Quartile")
            fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Median")
            fig.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Bottom Quartile")

            fig.update_layout(
                title='Competitive Positioning vs Peers',
                xaxis_title='Financial Ratios',
                yaxis_title='Percentile Rank',
                height=500,
                yaxis=dict(range=[0, 100])
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_trend_charts(self, historical_ratios: Dict[str, List[float]]) -> None:
        """Create trend analysis charts"""
        if not historical_ratios:
            st.info("No historical data available for trend analysis")
            return

        # Select key ratios for trend display
        key_ratios = ['roe', 'current_ratio', 'debt_to_equity', 'gross_margin']
        available_ratios = {k: v for k, v in historical_ratios.items()
                          if k in key_ratios and len(v) > 1}

        if available_ratios:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[r.replace('_', ' ').title() for r in available_ratios.keys()],
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )

            colors = ['blue', 'red', 'green', 'purple']
            positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

            for idx, (ratio_name, values) in enumerate(available_ratios.items()):
                if idx < 4:  # Limit to 4 charts
                    row, col = positions[idx]
                    periods = list(range(len(values)))

                    fig.add_trace(
                        go.Scatter(
                            x=periods,
                            y=values,
                            mode='lines+markers',
                            name=ratio_name.replace('_', ' ').title(),
                            line=dict(color=colors[idx]),
                            showlegend=False
                        ),
                        row=row, col=col
                    )

            fig.update_layout(
                title='Historical Ratio Trends',
                height=600,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_correlation_matrix(self, correlation_data) -> None:
        """Render correlation matrix heatmap"""
        if (not hasattr(correlation_data, 'correlation_matrix') or
            not hasattr(correlation_data, 'ratio_names')):
            st.info("Correlation data not available")
            return

        matrix = correlation_data.correlation_matrix
        ratio_names = [name.replace('_', ' ').title() for name in correlation_data.ratio_names]

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=ratio_names,
            y=ratio_names,
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(title="Correlation")
        ))

        fig.update_layout(
            title='Ratio Correlation Matrix',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    def _extract_current_ratios(self, metrics: Dict) -> Dict[str, float]:
        """Extract current period ratios from metrics"""
        ratios = {}

        # Extract from different metric categories
        categories = ['profitability', 'liquidity', 'leverage', 'efficiency', 'growth']

        for category in categories:
            category_data = metrics.get(category, {})
            for ratio_name, values in category_data.items():
                if isinstance(values, list) and len(values) > 0:
                    # Take the most recent value
                    latest_value = values[-1]
                    if isinstance(latest_value, (int, float)) and np.isfinite(latest_value):
                        ratios[ratio_name] = float(latest_value)

        return ratios

    def _extract_historical_ratios(self, metrics: Dict) -> Dict[str, List[float]]:
        """Extract historical ratio data from metrics"""
        historical = {}

        categories = ['profitability', 'liquidity', 'leverage', 'efficiency', 'growth']

        for category in categories:
            category_data = metrics.get(category, {})
            for ratio_name, values in category_data.items():
                if isinstance(values, list) and len(values) > 1:
                    # Clean and validate historical values
                    clean_values = [float(v) for v in values
                                  if isinstance(v, (int, float)) and np.isfinite(v)]
                    if len(clean_values) > 1:
                        historical[ratio_name] = clean_values

        return historical

    def _get_mock_peer_data(self, industry: str) -> Dict[str, Dict[str, Any]]:
        """Generate mock peer data for demonstration"""
        # This would normally come from a real data source
        if industry == 'Technology':
            return {
                'MSFT': {
                    'company_name': 'Microsoft Corporation',
                    'industry': 'Technology',
                    'ratios': {
                        'roe': 0.42, 'roa': 0.18, 'current_ratio': 2.5,
                        'debt_to_equity': 0.35, 'gross_margin': 0.68
                    }
                },
                'AAPL': {
                    'company_name': 'Apple Inc.',
                    'industry': 'Technology',
                    'ratios': {
                        'roe': 0.83, 'roa': 0.28, 'current_ratio': 1.1,
                        'debt_to_equity': 1.73, 'gross_margin': 0.38
                    }
                }
            }
        return {}


# Demo function for standalone testing
def create_advanced_ratio_demo():
    """Create demo of advanced ratio dashboard"""
    st.set_page_config(page_title="Advanced Ratio Analysis", layout="wide")

    # Mock financial calculator
    class MockAdvancedCalculator:
        def get_financial_metrics(self):
            return {
                'profitability': {
                    'roe': [0.15, 0.18, 0.22, 0.25],
                    'roa': [0.08, 0.10, 0.12, 0.14],
                    'gross_margin': [0.40, 0.42, 0.45, 0.48],
                    'operating_margin': [0.18, 0.20, 0.22, 0.25],
                    'net_margin': [0.12, 0.14, 0.16, 0.18]
                },
                'liquidity': {
                    'current_ratio': [1.8, 2.0, 2.2, 2.4],
                    'quick_ratio': [1.2, 1.3, 1.4, 1.5]
                },
                'leverage': {
                    'debt_to_equity': [0.6, 0.5, 0.4, 0.3],
                    'interest_coverage': [8.0, 9.0, 10.0, 12.0]
                },
                'efficiency': {
                    'asset_turnover': [0.8, 0.9, 1.0, 1.1],
                    'inventory_turnover': [4.0, 4.5, 5.0, 5.5]
                },
                'growth': {
                    'revenue_growth': [0.08, 0.12, 0.15, 0.18],
                    'fcf_growth': [0.05, 0.10, 0.15, 0.20]
                },
                'company_info': {
                    'name': 'Advanced Demo Corp',
                    'ticker': 'DEMO'
                }
            }

    # Initialize dashboard
    dashboard = AdvancedRatioDashboard()
    mock_calc = MockAdvancedCalculator()

    # Render dashboard
    dashboard.render_dashboard(mock_calc)


if __name__ == "__main__":
    create_advanced_ratio_demo()