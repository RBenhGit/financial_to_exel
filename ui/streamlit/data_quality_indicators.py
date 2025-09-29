"""
Data Quality Indicators for Streamlit Interface
==============================================

This module provides Streamlit components for displaying data quality indicators,
warnings, and detailed quality information to help users understand data reliability.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import data quality types
from core.data_processing.data_quality_analyzer import DataQualityIndicator, DataQualityAnalyzer

logger = logging.getLogger(__name__)


def render_quality_indicator(indicator: DataQualityIndicator, compact: bool = False) -> None:
    """
    Render a data quality indicator in the Streamlit interface

    Args:
        indicator: DataQualityIndicator to display
        compact: If True, render in compact mode for sidebar/small spaces
    """
    if compact:
        _render_compact_indicator(indicator)
    else:
        _render_full_indicator(indicator)


def _render_compact_indicator(indicator: DataQualityIndicator) -> None:
    """Render compact quality indicator for sidebars"""
    col1, col2 = st.columns([1, 3])

    with col1:
        # Quality score badge
        if indicator.level == "high":
            st.success(f"**{indicator.score:.0f}%**")
        elif indicator.level == "medium":
            st.warning(f"**{indicator.score:.0f}%**")
        elif indicator.level == "low":
            st.error(f"**{indicator.score:.0f}%**")
        else:
            st.info(f"**{indicator.score:.0f}%**")

    with col2:
        st.caption(f"🔍 {indicator.message}")


def _render_full_indicator(indicator: DataQualityIndicator) -> None:
    """Render full quality indicator with details"""

    # Main quality score and status
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.metric(
            label="Data Quality Score",
            value=f"{indicator.score:.1f}%",
            help="Overall data quality score (0-100%)"
        )

    with col2:
        # Quality level badge
        if indicator.level == "high":
            st.success(f"✅ **{indicator.level.upper()} QUALITY**")
        elif indicator.level == "medium":
            st.warning(f"⚠️ **{indicator.level.upper()} QUALITY**")
        elif indicator.level == "low":
            st.error(f"❌ **{indicator.level.upper()} QUALITY**")
        else:
            st.info(f"❓ **{indicator.level.upper()} QUALITY**")

    with col3:
        st.caption(f"📅 {indicator.timestamp.strftime('%H:%M')}")

    # Quality message
    st.info(f"💡 {indicator.message}")

    # Quality breakdown if details available
    if indicator.details:
        with st.expander("📊 Quality Details"):
            _render_quality_breakdown(indicator.details)


def _render_quality_breakdown(details: Dict[str, float]) -> None:
    """Render detailed quality metrics breakdown"""

    # Convert to DataFrame for easier handling
    quality_data = []
    for dimension, score in details.items():
        if score > 0:  # Only show dimensions with data
            quality_data.append({
                'Dimension': dimension.title(),
                'Score': score,
                'Level': _get_quality_level(score)
            })

    if not quality_data:
        st.info("No detailed quality metrics available")
        return

    df = pd.DataFrame(quality_data)

    # Create horizontal bar chart
    fig = px.bar(
        df,
        x='Score',
        y='Dimension',
        color='Score',
        color_continuous_scale=['red', 'yellow', 'green'],
        range_color=[0, 100],
        orientation='h',
        title="Quality Metrics Breakdown"
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Also show as metrics
    cols = st.columns(min(len(quality_data), 3))
    for i, item in enumerate(quality_data):
        with cols[i % len(cols)]:
            st.metric(
                label=item['Dimension'],
                value=f"{item['Score']:.1f}%",
                help=f"Quality score for {item['Dimension'].lower()}"
            )


def render_quality_warnings(warnings: List[str]) -> None:
    """
    Render data quality warnings

    Args:
        warnings: List of warning messages
    """
    if not warnings:
        return

    st.warning("⚠️ **Data Quality Warnings**")
    for warning in warnings:
        st.caption(f"• {warning}")


def render_quality_dashboard(analyzer: DataQualityAnalyzer) -> None:
    """
    Render a comprehensive data quality dashboard

    Args:
        analyzer: DataQualityAnalyzer instance
    """
    try:
        dashboard_data = analyzer.get_quality_dashboard_data()

        st.subheader("📊 Data Quality Dashboard")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Analyses",
                dashboard_data['total_analyses'],
                help="Total number of data quality assessments performed"
            )

        with col2:
            st.metric(
                "Average Score",
                f"{dashboard_data['average_score']:.1f}%",
                help="Average quality score across recent analyses"
            )

        with col3:
            # Trend status
            trends = dashboard_data['trends']
            if trends.get('status') == 'improving':
                st.metric("Trend", "📈 Improving", help="Data quality is improving over time")
            elif trends.get('status') == 'degrading':
                st.metric("Trend", "📉 Degrading", help="Data quality is declining over time")
            else:
                st.metric("Trend", "📊 Stable", help="Data quality is stable")

        with col4:
            # Risk level from predictions
            predictions = dashboard_data['predictions']
            risk_level = predictions.get('risk_level', 'unknown')
            if risk_level == 'low':
                st.metric("Risk Level", "🟢 Low", help="Low risk of quality issues")
            elif risk_level == 'medium':
                st.metric("Risk Level", "🟡 Medium", help="Medium risk of quality issues")
            elif risk_level == 'high':
                st.metric("Risk Level", "🔴 High", help="High risk of quality issues")
            else:
                st.metric("Risk Level", "⚪ Unknown", help="Unable to assess risk")

        # Quality trend chart
        if dashboard_data['recent_scores']:
            st.subheader("📈 Quality Trend")

            df_trend = pd.DataFrame({
                'Time': dashboard_data['recent_timestamps'],
                'Quality Score': dashboard_data['recent_scores']
            })

            df_trend['Time'] = pd.to_datetime(df_trend['Time'])

            fig = px.line(
                df_trend,
                x='Time',
                y='Quality Score',
                title="Data Quality Over Time",
                line_shape='linear'
            )

            fig.update_layout(
                height=400,
                yaxis_range=[0, 100],
                margin=dict(l=20, r=20, t=40, b=20)
            )

            # Add quality level zones
            fig.add_hline(y=80, line_dash="dash", line_color="green",
                         annotation_text="High Quality Threshold")
            fig.add_hline(y=60, line_dash="dash", line_color="orange",
                         annotation_text="Acceptable Quality Threshold")

            st.plotly_chart(fig, use_container_width=True)

        # Predictions and recommendations
        if predictions.get('recommendations'):
            st.subheader("💡 Recommendations")
            for rec in predictions['recommendations']:
                st.info(f"• {rec}")

    except Exception as e:
        logger.error(f"Error rendering quality dashboard: {e}")
        st.error("Unable to load quality dashboard data")


def render_quality_sidebar(calculator) -> None:
    """
    Render quality information in the sidebar

    Args:
        calculator: FinancialCalculator instance with quality data
    """
    try:
        st.sidebar.subheader("🔍 Data Quality")

        # Get quality indicator
        indicator = calculator.get_data_quality_indicator()

        if indicator:
            render_quality_indicator(indicator, compact=True)

            # Show warnings if any
            warnings = calculator.get_quality_warnings()
            if warnings:
                with st.sidebar.expander("⚠️ Warnings"):
                    for warning in warnings:
                        st.caption(warning)

        else:
            st.sidebar.info("Quality assessment not available")

    except Exception as e:
        logger.warning(f"Error rendering quality sidebar: {e}")
        st.sidebar.warning("Quality info unavailable")


def render_data_source_quality(data_sources: Dict[str, Any]) -> None:
    """
    Render quality information for multiple data sources

    Args:
        data_sources: Dictionary mapping source names to quality data
    """
    st.subheader("📋 Data Source Quality")

    if not data_sources:
        st.info("No data source quality information available")
        return

    # Create tabs for each data source
    tabs = st.tabs(list(data_sources.keys()))

    for tab, (source_name, source_data) in zip(tabs, data_sources.items()):
        with tab:
            if isinstance(source_data, DataQualityIndicator):
                render_quality_indicator(source_data)
            else:
                st.info(f"Quality data not available for {source_name}")


def _get_quality_level(score: float) -> str:
    """Get quality level from score"""
    if score >= 80:
        return "high"
    elif score >= 60:
        return "medium"
    else:
        return "low"


# Export main functions
__all__ = [
    'render_quality_indicator',
    'render_quality_warnings',
    'render_quality_dashboard',
    'render_quality_sidebar',
    'render_data_source_quality'
]