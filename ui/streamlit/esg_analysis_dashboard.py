"""
ESG Analysis Dashboard
======================

Comprehensive ESG (Environmental, Social, Governance) analysis dashboard for Streamlit.
Provides interactive visualization and analysis of ESG metrics, scores, and risk assessment.

Key Features:
- ESG score visualization and breakdown
- Risk assessment and materiality analysis
- Peer comparison and industry benchmarking
- ESG trend analysis and performance tracking
- Interactive charts and data exploration
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine, ESGAnalysisResult
from core.analysis.esg.esg_data_adapter import ESGDataAdapter
from core.analysis.esg.esg_variable_definitions import register_esg_variables_with_registry
from ui.streamlit.dashboard_components import create_metric_card, create_info_card

logger = logging.getLogger(__name__)


class ESGDashboard:
    """ESG Analysis Dashboard for Streamlit UI"""

    def __init__(self):
        """Initialize ESG Dashboard"""
        self.esg_engine = ESGAnalysisEngine()
        self.esg_adapter = ESGDataAdapter()

        # Register ESG variables with the system
        try:
            register_esg_variables_with_registry()
        except Exception as e:
            logger.warning(f"Could not register ESG variables: {e}")

        # Color scheme for ESG visualizations
        self.colors = {
            'environmental': '#2E8B57',  # Sea Green
            'social': '#4682B4',         # Steel Blue
            'governance': '#DAA520',      # Goldenrod
            'overall': '#483D8B',        # Dark Slate Blue
            'risk_high': '#DC143C',      # Crimson
            'risk_medium': '#FF8C00',    # Dark Orange
            'risk_low': '#32CD32'        # Lime Green
        }

    def render_esg_dashboard(self, symbol: str):
        """
        Render the complete ESG analysis dashboard for a given symbol.

        Args:
            symbol: Stock ticker symbol to analyze
        """
        st.title("🌱 ESG Analysis Dashboard")

        if not symbol:
            st.info("👈 Please enter a company ticker symbol in the sidebar to begin ESG analysis.")
            self._render_esg_overview()
            return

        try:
            # Show loading spinner
            with st.spinner(f"Analyzing ESG metrics for {symbol}..."):
                # Fetch ESG data
                data_result = self.esg_adapter.load_symbol_data(symbol)

                if not data_result.success:
                    st.error(f"❌ Could not fetch ESG data for {symbol}")
                    st.info("ESG data may not be available for this company. Try a larger, publicly traded company.")
                    return

                # Perform ESG analysis
                esg_analysis = self.esg_engine.analyze_company_esg(symbol)

            # Display the analysis
            self._render_esg_analysis_results(esg_analysis, data_result)

        except Exception as e:
            logger.error(f"Error in ESG dashboard for {symbol}: {e}")
            st.error(f"An error occurred during ESG analysis: {str(e)}")

    def _render_esg_overview(self):
        """Render ESG overview information when no symbol is selected"""
        st.markdown("""
        ## What is ESG Analysis?

        **ESG (Environmental, Social, Governance)** analysis evaluates companies based on their:

        ### 🌍 Environmental Factors
        - Carbon emissions and climate impact
        - Energy efficiency and renewable energy use
        - Waste management and recycling
        - Water usage and conservation

        ### 👥 Social Factors
        - Employee satisfaction and diversity
        - Workplace safety and labor practices
        - Community relations and social impact
        - Customer data protection and privacy

        ### 🏛️ Governance Factors
        - Board composition and independence
        - Executive compensation and accountability
        - Shareholder rights and transparency
        - Business ethics and compliance

        ### 📊 ESG Scoring
        Companies receive scores on a **0-100 scale** for each pillar:
        - **85-100**: AAA (Excellent)
        - **75-84**: AA (Very Good)
        - **65-74**: A (Good)
        - **55-64**: BBB (Average)
        - **45-54**: BB (Below Average)
        - **35-44**: B (Poor)
        - **0-34**: CCC (Very Poor)
        """)

        # Sample ESG analysis for demonstration
        with st.expander("📈 View Sample ESG Analysis"):
            self._render_sample_esg_data()

    def _render_sample_esg_data(self):
        """Render sample ESG data for demonstration"""
        sample_data = {
            'Company': ['Apple Inc.', 'Microsoft Corp.', 'Tesla Inc.', 'ExxonMobil Corp.'],
            'ESG Score': [78, 82, 65, 45],
            'Environmental': [85, 88, 92, 25],
            'Social': [75, 80, 60, 55],
            'Governance': [74, 79, 43, 55],
            'ESG Rating': ['AA', 'AA', 'A', 'BB']
        }

        df = pd.DataFrame(sample_data)

        col1, col2 = st.columns([2, 1])

        with col1:
            # Create horizontal bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Environmental',
                y=df['Company'],
                x=df['Environmental'],
                orientation='h',
                marker_color=self.colors['environmental']
            ))

            fig.add_trace(go.Bar(
                name='Social',
                y=df['Company'],
                x=df['Social'],
                orientation='h',
                marker_color=self.colors['social']
            ))

            fig.add_trace(go.Bar(
                name='Governance',
                y=df['Company'],
                x=df['Governance'],
                orientation='h',
                marker_color=self.colors['governance']
            ))

            fig.update_layout(
                title="Sample ESG Pillar Scores",
                xaxis_title="ESG Score (0-100)",
                barmode='group',
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Sample Scores")
            st.dataframe(df[['Company', 'ESG Score', 'ESG Rating']], hide_index=True)

    def _render_esg_analysis_results(self, analysis: ESGAnalysisResult, data_result):
        """Render comprehensive ESG analysis results"""

        # Header with company information
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader(f"{analysis.company_name} ({analysis.symbol})")
            st.caption(f"Analysis Date: {analysis.analysis_date.strftime('%B %d, %Y')}")

        with col2:
            confidence_color = {
                'High': '🟢',
                'Medium': '🟡',
                'Low': '🔴'
            }
            st.metric(
                "Data Confidence",
                f"{confidence_color.get(analysis.confidence_level, '⚪')} {analysis.confidence_level}",
                f"{analysis.data_completeness:.1%} Complete"
            )

        with col3:
            sources_text = ", ".join(analysis.data_sources_used)
            st.metric(
                "Data Sources",
                len(analysis.data_sources_used),
                sources_text[:20] + "..." if len(sources_text) > 20 else sources_text
            )

        # Overall ESG Score Section
        self._render_overall_esg_section(analysis)

        # Pillar Analysis Section
        self._render_pillar_analysis(analysis)

        # Risk Assessment Section
        self._render_risk_assessment(analysis)

        # Comparative Analysis (if available)
        if analysis.industry_percentile or analysis.peer_comparison:
            self._render_comparative_analysis(analysis)

        # Recommendations Section
        self._render_recommendations(analysis)

        # Detailed Metrics Section
        self._render_detailed_metrics(analysis)

        # Data Quality and Methodology
        with st.expander("📋 Data Quality & Methodology"):
            self._render_methodology_info(analysis, data_result)

    def _render_overall_esg_section(self, analysis: ESGAnalysisResult):
        """Render overall ESG score and rating"""
        st.markdown("---")
        st.subheader("🎯 Overall ESG Assessment")

        col1, col2, col3, col4 = st.columns(4)

        # Overall ESG Score
        with col1:
            score_color = self._get_score_color(analysis.overall_esg_score)
            st.metric(
                "ESG Score",
                f"{analysis.overall_esg_score:.1f}/100",
                delta=None,
                delta_color="normal"
            )
            st.markdown(f"<div style='text-align: center; color: {score_color}; font-size: 20px; font-weight: bold;'>{analysis.overall_esg_rating.value}</div>", unsafe_allow_html=True)

        # Risk Level
        with col2:
            risk_emoji = self._get_risk_emoji(analysis.overall_risk_level)
            st.metric(
                "Risk Level",
                f"{risk_emoji} {analysis.overall_risk_level.value.replace('_', ' ').title()}",
                delta=None
            )

        # Industry Percentile
        with col3:
            if analysis.industry_percentile:
                st.metric(
                    "Industry Rank",
                    f"{analysis.industry_percentile:.0f}th percentile",
                    delta=None
                )
            else:
                st.metric("Industry Rank", "Not Available", delta=None)

        # Trend
        with col4:
            trend_emoji = {"improving": "📈", "stable": "➡️", "deteriorating": "📉"}.get(analysis.score_trend, "➡️")
            st.metric(
                "Score Trend",
                f"{trend_emoji} {analysis.score_trend.title()}",
                delta=None
            )

        # ESG Score Gauge Chart
        self._create_esg_gauge_chart(analysis.overall_esg_score, analysis.overall_esg_rating)

    def _render_pillar_analysis(self, analysis: ESGAnalysisResult):
        """Render detailed pillar analysis"""
        st.markdown("---")
        st.subheader("📊 ESG Pillar Breakdown")

        # Pillar scores comparison
        pillars_data = {
            'Pillar': ['Environmental', 'Social', 'Governance'],
            'Score': [
                analysis.environmental_score.score,
                analysis.social_score.score,
                analysis.governance_score.score
            ],
            'Risk Level': [
                analysis.environmental_score.risk_level.value.replace('_', ' ').title(),
                analysis.social_score.risk_level.value.replace('_', ' ').title(),
                analysis.governance_score.risk_level.value.replace('_', ' ').title()
            ],
            'Data Quality': [
                analysis.environmental_score.data_quality,
                analysis.social_score.data_quality,
                analysis.governance_score.data_quality
            ]
        }

        df_pillars = pd.DataFrame(pillars_data)

        # Create pillar comparison chart
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure()

            # Add bar chart for scores
            fig.add_trace(go.Bar(
                x=df_pillars['Pillar'],
                y=df_pillars['Score'],
                marker_color=[
                    self.colors['environmental'],
                    self.colors['social'],
                    self.colors['governance']
                ],
                text=df_pillars['Score'].round(1),
                textposition='auto',
                name='ESG Score'
            ))

            fig.update_layout(
                title="ESG Pillar Scores",
                yaxis_title="Score (0-100)",
                yaxis=dict(range=[0, 100]),
                height=400,
                showlegend=False
            )

            # Add horizontal line at 50 (neutral)
            fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Pillar Details")

            for i, pillar in enumerate(['Environmental', 'Social', 'Governance']):
                score = df_pillars.iloc[i]['Score']
                risk = df_pillars.iloc[i]['Risk Level']
                quality = df_pillars.iloc[i]['Data Quality']

                with st.expander(f"{pillar} ({score:.1f})"):
                    st.metric("Score", f"{score:.1f}/100")
                    st.metric("Risk Level", risk)
                    st.progress(quality)
                    st.caption(f"Data Quality: {quality:.1%}")

    def _render_risk_assessment(self, analysis: ESGAnalysisResult):
        """Render risk assessment section"""
        st.markdown("---")
        st.subheader("⚠️ Risk Assessment")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Key Risk Factors:**")
            if analysis.esg_risk_factors:
                for factor in analysis.esg_risk_factors:
                    st.markdown(f"• ⚠️ {factor}")
            else:
                st.info("No significant ESG risk factors identified.")

        with col2:
            st.markdown("**Material ESG Issues:**")
            if analysis.material_esg_issues:
                for issue in analysis.material_esg_issues:
                    st.markdown(f"• 🔍 {issue}")
            else:
                st.info("No material ESG issues identified for this industry.")

    def _render_comparative_analysis(self, analysis: ESGAnalysisResult):
        """Render comparative analysis section"""
        st.markdown("---")
        st.subheader("📈 Comparative Analysis")

        if analysis.peer_comparison:
            # Create peer comparison chart
            peers_data = []
            for peer, score in analysis.peer_comparison.items():
                peers_data.append({'Company': peer, 'ESG Score': score})

            # Add current company
            peers_data.append({
                'Company': f"{analysis.symbol} (Current)",
                'ESG Score': analysis.overall_esg_score
            })

            df_peers = pd.DataFrame(peers_data)

            fig = px.bar(
                df_peers,
                x='Company',
                y='ESG Score',
                title="Peer ESG Score Comparison",
                color='ESG Score',
                color_continuous_scale='viridis'
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    def _render_recommendations(self, analysis: ESGAnalysisResult):
        """Render recommendations section"""
        st.markdown("---")
        st.subheader("💡 Recommendations")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Priority Improvement Areas:**")
            if analysis.improvement_areas:
                for area in analysis.improvement_areas:
                    st.markdown(f"🎯 {area}")
            else:
                st.success("No major improvement areas identified - Strong ESG performance!")

        with col2:
            st.markdown("**ESG Opportunities:**")
            if analysis.esg_opportunities:
                for opportunity in analysis.esg_opportunities:
                    st.markdown(f"🌟 {opportunity}")
            else:
                st.info("Specific opportunities will be identified as more data becomes available.")

    def _render_detailed_metrics(self, analysis: ESGAnalysisResult):
        """Render detailed ESG metrics section"""
        with st.expander("📋 Detailed ESG Metrics"):
            # Try to get detailed metrics from var_data
            try:
                var_data = self.esg_engine.var_data
                detailed_metrics = {}

                # Environmental metrics
                env_metrics = {
                    'Carbon Emissions Total': 'carbon_emissions_total',
                    'Carbon Intensity': 'carbon_intensity',
                    'Renewable Energy %': 'renewable_energy_percentage',
                    'Waste Recycling Rate': 'waste_recycling_rate'
                }

                # Social metrics
                social_metrics = {
                    'Employee Count': 'employee_count_total',
                    'Employee Turnover Rate': 'employee_turnover_rate',
                    'Board Gender Diversity': 'gender_diversity_board',
                    'Workplace Safety Incidents': 'workplace_safety_incidents'
                }

                # Governance metrics
                governance_metrics = {
                    'Board Independence': 'board_independence',
                    'Board Size': 'board_size',
                    'Audit Committee Independence': 'audit_committee_independence'
                }

                all_metrics = {
                    'Environmental': env_metrics,
                    'Social': social_metrics,
                    'Governance': governance_metrics
                }

                for category, metrics in all_metrics.items():
                    st.subheader(f"{category} Metrics")

                    metrics_data = []
                    for display_name, var_name in metrics.items():
                        try:
                            value = var_data.get_variable(analysis.symbol, var_name)
                            if value is not None:
                                # Format value based on metric type
                                if 'percentage' in var_name or 'rate' in var_name:
                                    formatted_value = f"{value * 100:.1f}%" if value <= 1 else f"{value:.1f}%"
                                elif 'count' in var_name or 'size' in var_name:
                                    formatted_value = f"{value:,.0f}"
                                else:
                                    formatted_value = f"{value:.2f}"

                                metrics_data.append({
                                    'Metric': display_name,
                                    'Value': formatted_value
                                })
                        except:
                            pass

                    if metrics_data:
                        df_metrics = pd.DataFrame(metrics_data)
                        st.dataframe(df_metrics, hide_index=True)
                    else:
                        st.info(f"No {category.lower()} metrics available.")

            except Exception as e:
                logger.debug(f"Could not load detailed metrics: {e}")
                st.info("Detailed metrics will be displayed when ESG data is available.")

    def _render_methodology_info(self, analysis: ESGAnalysisResult, data_result):
        """Render methodology and data quality information"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Data Quality")
            st.progress(analysis.data_completeness)
            st.caption(f"Data Completeness: {analysis.data_completeness:.1%}")

            st.metric("Data Sources", len(analysis.data_sources_used))
            for source in analysis.data_sources_used:
                st.caption(f"• {source}")

            st.metric("Variables Analyzed", data_result.variables_extracted)

        with col2:
            st.subheader("🔬 Methodology")
            for note in analysis.methodology_notes:
                st.caption(f"• {note}")

            st.subheader("⏱️ Processing Stats")
            st.caption(f"Analysis Time: {data_result.extraction_time:.2f}s")
            st.caption(f"Data Points: {data_result.data_points_stored}")

    def _create_esg_gauge_chart(self, score: float, rating):
        """Create a gauge chart for ESG score"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"ESG Score - {rating.value}"},
            delta={'reference': 50},  # 50 is neutral
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.colors['overall']},
                'steps': [
                    {'range': [0, 35], 'color': "#FF6B6B"},    # Poor (CCC-B)
                    {'range': [35, 55], 'color': "#FFE66D"},   # Below Average (BB-BBB)
                    {'range': [55, 75], 'color': "#A8E6CF"},   # Good (A-AA)
                    {'range': [75, 100], 'color': "#6BCF7F"}   # Excellent (AAA)
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    def _get_score_color(self, score: float) -> str:
        """Get color based on ESG score"""
        if score >= 75:
            return "#6BCF7F"  # Green
        elif score >= 55:
            return "#A8E6CF"  # Light Green
        elif score >= 35:
            return "#FFE66D"  # Yellow
        else:
            return "#FF6B6B"  # Red

    def _get_risk_emoji(self, risk_level) -> str:
        """Get emoji based on risk level"""
        risk_emojis = {
            'very_low': '🟢',
            'low': '🟡',
            'medium': '🟠',
            'high': '🔴',
            'very_high': '⛔'
        }
        return risk_emojis.get(risk_level.value, '⚪')


def render_esg_analysis(symbol: str):
    """
    Main function to render ESG analysis dashboard.

    Args:
        symbol: Stock ticker symbol to analyze
    """
    dashboard = ESGDashboard()
    dashboard.render_esg_dashboard(symbol)