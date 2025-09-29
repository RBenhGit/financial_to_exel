"""
Data Quality Dashboard for Streamlit
===================================

Comprehensive data quality dashboard providing detailed insights into data reliability,
quality trends, and recommendations for data improvement.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from core.data_processing.data_quality_analyzer import DataQualityAnalyzer
from .data_quality_indicators import render_quality_indicator, render_quality_warnings

logger = logging.getLogger(__name__)


def render_data_quality_dashboard(calculator=None) -> None:
    """
    Render the main data quality dashboard

    Args:
        calculator: FinancialCalculator instance (optional)
    """
    st.header("📊 Data Quality Dashboard")
    st.markdown("Comprehensive view of data reliability and quality metrics")

    try:
        # Initialize analyzer
        analyzer = DataQualityAnalyzer()

        # Get dashboard data
        dashboard_data = analyzer.get_quality_dashboard_data()

        # Overview section
        _render_quality_overview(dashboard_data)

        # Current analysis section
        if calculator:
            st.divider()
            _render_current_analysis_quality(calculator)

        # Historical trends section
        st.divider()
        _render_historical_trends(dashboard_data)

        # Predictions and recommendations
        st.divider()
        _render_predictions_and_recommendations(dashboard_data)

        # Quality settings and controls
        st.divider()
        _render_quality_controls()

    except Exception as e:
        logger.error(f"Error rendering data quality dashboard: {e}")
        st.error("Unable to load data quality dashboard. Please check the logs for details.")


def _render_quality_overview(dashboard_data: Dict[str, Any]) -> None:
    """Render quality overview metrics"""
    st.subheader("🎯 Quality Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Analyses",
            dashboard_data.get('total_analyses', 0),
            help="Total number of data quality assessments performed"
        )

    with col2:
        avg_score = dashboard_data.get('average_score', 0)
        st.metric(
            "Average Quality",
            f"{avg_score:.1f}%",
            help="Average quality score across recent analyses"
        )

    with col3:
        # Trend indicator
        trends = dashboard_data.get('trends', {})
        trend_status = trends.get('status', 'unknown')

        if trend_status == 'improving':
            trend_delta = f"+{abs(trends.get('overall_trend', 0)):.1f}"
            st.metric("Quality Trend", "Improving", delta=trend_delta, delta_color="normal")
        elif trend_status == 'degrading':
            trend_delta = f"-{abs(trends.get('overall_trend', 0)):.1f}"
            st.metric("Quality Trend", "Declining", delta=trend_delta, delta_color="inverse")
        else:
            st.metric("Quality Trend", "Stable", help="Quality levels are stable")

    with col4:
        # Risk assessment
        predictions = dashboard_data.get('predictions', {})
        risk_level = predictions.get('risk_level', 'unknown')

        risk_colors = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }

        risk_emoji = risk_colors.get(risk_level, '⚪')
        st.metric(
            "Risk Level",
            f"{risk_emoji} {risk_level.title()}",
            help=f"Predicted risk level for data quality issues"
        )


def _render_current_analysis_quality(calculator) -> None:
    """Render current analysis quality information"""
    st.subheader("🔍 Current Analysis Quality")

    try:
        # Get quality indicator
        indicator = calculator.get_data_quality_indicator()

        if indicator:
            # Main quality display
            render_quality_indicator(indicator)

            # Quality warnings
            warnings = calculator.get_quality_warnings()
            if warnings:
                render_quality_warnings(warnings)

            # Data source information
            col1, col2 = st.columns(2)

            with col1:
                st.info(f"**Company:** {calculator.company_name}")
                if calculator.ticker_symbol:
                    st.info(f"**Ticker:** {calculator.ticker_symbol}")

            with col2:
                st.info(f"**Assessment Time:** {indicator.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.info(f"**Data Points:** {len(calculator.financial_data)}")

        else:
            # No quality data available
            st.warning("No quality assessment available for current analysis")

            if st.button("🔍 Assess Data Quality"):
                with st.spinner("Assessing data quality..."):
                    try:
                        indicator = calculator.assess_data_quality()
                        st.success(f"Quality assessment completed: {indicator.score:.1f}%")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Quality assessment failed: {e}")

    except Exception as e:
        logger.error(f"Error rendering current analysis quality: {e}")
        st.error("Unable to load current analysis quality information")


def _render_historical_trends(dashboard_data: Dict[str, Any]) -> None:
    """Render historical quality trends"""
    st.subheader("📈 Historical Quality Trends")

    recent_scores = dashboard_data.get('recent_scores', [])
    recent_timestamps = dashboard_data.get('recent_timestamps', [])

    if not recent_scores:
        st.info("No historical quality data available")
        return

    # Create trend chart
    df_trend = pd.DataFrame({
        'Time': recent_timestamps,
        'Quality Score': recent_scores
    })

    if len(df_trend) > 0:
        df_trend['Time'] = pd.to_datetime(df_trend['Time'])

        # Main trend chart
        fig = px.line(
            df_trend,
            x='Time',
            y='Quality Score',
            title="Data Quality Over Time",
            line_shape='linear'
        )

        # Add quality thresholds
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="green",
            annotation_text="High Quality (80%+)"
        )
        fig.add_hline(
            y=60,
            line_dash="dash",
            line_color="orange",
            annotation_text="Acceptable Quality (60%+)"
        )
        fig.add_hline(
            y=40,
            line_dash="dash",
            line_color="red",
            annotation_text="Poor Quality (40%+)"
        )

        fig.update_layout(
            height=400,
            yaxis_range=[0, 100],
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Quality distribution
        col1, col2 = st.columns(2)

        with col1:
            # Quality score distribution
            fig_hist = px.histogram(
                df_trend,
                x='Quality Score',
                nbins=10,
                title="Quality Score Distribution"
            )
            fig_hist.update_layout(height=300)
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            # Quality level summary
            quality_levels = []
            for score in recent_scores:
                if score >= 80:
                    quality_levels.append('High')
                elif score >= 60:
                    quality_levels.append('Medium')
                else:
                    quality_levels.append('Low')

            level_counts = pd.Series(quality_levels).value_counts()

            fig_pie = px.pie(
                values=level_counts.values,
                names=level_counts.index,
                title="Quality Level Distribution"
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)


def _render_predictions_and_recommendations(dashboard_data: Dict[str, Any]) -> None:
    """Render predictions and recommendations"""
    st.subheader("🔮 Predictions & Recommendations")

    predictions = dashboard_data.get('predictions', {})

    if predictions.get('status') == 'no_prediction':
        st.info("Insufficient data for quality predictions")
        return

    # Prediction summary
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Current Quality",
            f"{predictions.get('current_quality', 0):.1f}%",
            help="Current data quality score"
        )

    with col2:
        projected_quality = predictions.get('projected_quality', 0)
        current_quality = predictions.get('current_quality', 0)
        delta = projected_quality - current_quality

        st.metric(
            "Projected Quality",
            f"{projected_quality:.1f}%",
            delta=f"{delta:+.1f}%",
            help="Projected quality based on trends"
        )

    # Recommendations
    recommendations = predictions.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Actionable Recommendations")

        for i, rec in enumerate(recommendations, 1):
            st.info(f"**{i}.** {rec}")

    # Risk assessment details
    risk_level = predictions.get('risk_level', 'unknown')
    trend_direction = predictions.get('trend_direction', 'unknown')

    if risk_level != 'unknown':
        if risk_level == 'high':
            st.error(f"⚠️ **High Risk:** Quality trend is {trend_direction}. Immediate attention recommended.")
        elif risk_level == 'medium':
            st.warning(f"⚠️ **Medium Risk:** Quality trend is {trend_direction}. Monitor closely.")
        else:
            st.success(f"✅ **Low Risk:** Quality trend is {trend_direction}. Continue current practices.")


def _render_quality_controls() -> None:
    """Render quality settings and controls"""
    st.subheader("⚙️ Quality Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Quality Thresholds**")

        # Quality threshold controls
        high_threshold = st.slider(
            "High Quality Threshold",
            min_value=70,
            max_value=95,
            value=80,
            step=5,
            help="Minimum score for high quality classification"
        )

        medium_threshold = st.slider(
            "Acceptable Quality Threshold",
            min_value=40,
            max_value=80,
            value=60,
            step=5,
            help="Minimum score for acceptable quality classification"
        )

    with col2:
        st.write("**Analysis Options**")

        # Analysis options
        auto_assess = st.checkbox(
            "Auto-assess quality on data load",
            value=True,
            help="Automatically assess data quality when loading new data"
        )

        show_warnings = st.checkbox(
            "Show quality warnings",
            value=True,
            help="Display quality warnings in the interface"
        )

        detailed_breakdown = st.checkbox(
            "Show detailed quality breakdown",
            value=False,
            help="Show detailed quality metrics for each dimension"
        )

    # Action buttons
    st.write("**Actions**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()

    with col2:
        if st.button("📊 Export Quality Report"):
            st.info("Quality report export feature coming soon!")

    with col3:
        if st.button("🧹 Clear History"):
            if st.session_state.get('confirm_clear'):
                st.success("Quality history cleared!")
                del st.session_state['confirm_clear']
            else:
                st.session_state['confirm_clear'] = True
                st.warning("Click again to confirm clearing quality history")


# Export main function
__all__ = ['render_data_quality_dashboard']