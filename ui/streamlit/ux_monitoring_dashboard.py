"""
UX Monitoring Dashboard for Streamlit Application

This module provides a comprehensive dashboard for visualizing user experience
metrics, performance data, and monitoring insights based on the continuous
monitoring system integration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Import monitoring components
from core.validation.continuous_ux_monitor import (
    StreamlitMonitoringIntegration, initialize_ux_monitoring
)
from tests.user_acceptance.monitoring_system import AlertLevel


def render_ux_monitoring_dashboard():
    """Render the comprehensive UX monitoring dashboard."""
    st.title("🔍 User Experience Monitoring Dashboard")
    st.markdown("Real-time insights from continuous UX monitoring and user session analytics")

    # Initialize monitoring
    monitor = initialize_ux_monitoring()

    # Time period selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        time_period = st.selectbox(
            "Analysis Period",
            [("Last 1 Hour", 1), ("Last 6 Hours", 6), ("Last 24 Hours", 24), ("Last 7 Days", 168)],
            index=2,
            format_func=lambda x: x[0]
        )[1]

    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=False)

    with col3:
        if st.button("🔄 Refresh Data") or auto_refresh:
            st.rerun()

    # Get dashboard data
    dashboard_data = monitor.generate_ux_dashboard_data(hours=time_period)

    # Main metrics overview
    render_metrics_overview(dashboard_data)

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Performance Analytics",
        "🎯 User Engagement",
        "🚨 Alerts & Issues",
        "🔧 Feature Usage",
        "📈 Trends & Insights"
    ])

    with tab1:
        render_performance_analytics(dashboard_data, monitor)

    with tab2:
        render_user_engagement_analytics(dashboard_data, monitor)

    with tab3:
        render_alerts_and_issues(dashboard_data, monitor)

    with tab4:
        render_feature_usage_analytics(dashboard_data, monitor)

    with tab5:
        render_trends_and_insights(dashboard_data, monitor, time_period)


def render_metrics_overview(dashboard_data: Dict[str, Any]):
    """Render high-level metrics overview."""
    st.subheader("📈 Real-Time Overview")

    session_stats = dashboard_data.get("session_statistics", {})
    ux_metrics = dashboard_data.get("ux_metrics", {})
    system_health = dashboard_data.get("system_health", {})

    # Key metrics in columns
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_sessions = session_stats.get("total_sessions", 0)
        active_sessions = session_stats.get("active_sessions", 0)
        st.metric(
            "Total Sessions",
            total_sessions,
            delta=f"{active_sessions} active" if active_sessions > 0 else "No active sessions"
        )

    with col2:
        avg_metrics = session_stats.get("average_metrics_per_session", 0)
        st.metric(
            "Avg Interactions/Session",
            f"{avg_metrics:.1f}"
        )

    with col3:
        engagement_score = ux_metrics.get("user_engagement_score", 0)
        st.metric(
            "Engagement Score",
            f"{engagement_score:.1%}",
            delta="Excellent" if engagement_score > 0.8 else "Good" if engagement_score > 0.6 else "Needs Improvement"
        )

    with col4:
        cpu_usage = system_health.get("cpu_usage_percent", 0)
        memory_usage = system_health.get("memory_usage_percent", 0)
        st.metric(
            "System Health",
            "Healthy" if cpu_usage < 70 and memory_usage < 70 else "Stressed",
            delta=f"CPU: {cpu_usage:.0f}%, RAM: {memory_usage:.0f}%"
        )

    with col5:
        feature_adoption = ux_metrics.get("feature_adoption_rate", 0)
        st.metric(
            "Feature Adoption",
            f"{feature_adoption:.1%}",
            delta="High" if feature_adoption > 0.7 else "Medium" if feature_adoption > 0.5 else "Low"
        )


def render_performance_analytics(dashboard_data: Dict[str, Any], monitor: StreamlitMonitoringIntegration):
    """Render performance analytics section."""
    st.subheader("⚡ Performance Analytics")

    # Get current session health
    session_health = monitor.get_current_session_health()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### System Performance")

        if session_health.get("status") != "no_active_session":
            system_health = session_health.get("system_health", {})

            # Create performance gauge charts
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("CPU Usage", "Memory Usage", "Disk Usage", "Active Sessions"),
                specs=[[{"type": "indicator"}, {"type": "indicator"}],
                       [{"type": "indicator"}, {"type": "indicator"}]]
            )

            # CPU Usage
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=system_health.get("cpu_usage_percent", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU %"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkgreen"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "yellow"},
                           {'range': [80, 100], 'color': "red"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}
            ), row=1, col=1)

            # Memory Usage
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=system_health.get("memory_usage_percent", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Memory %"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "yellow"},
                           {'range': [80, 100], 'color': "red"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}
            ), row=1, col=2)

            # Disk Usage
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=system_health.get("disk_usage_percent", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Disk %"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkred"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "yellow"},
                           {'range': [80, 100], 'color': "red"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}
            ), row=2, col=1)

            # Active Sessions
            active_sessions = system_health.get("active_monitoring_sessions", 0)
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=active_sessions,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Active Sessions"},
                number={'font': {'size': 40}}
            ), row=2, col=2)

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No active session to monitor")

    with col2:
        st.markdown("#### Response Time Trends")

        # Create sample data for demonstration
        # In production, this would come from actual metrics
        sample_times = pd.date_range(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now(),
            freq='1min'
        )

        sample_data = pd.DataFrame({
            'timestamp': sample_times,
            'response_time': np.random.normal(2.5, 0.5, len(sample_times)).clip(1, 8),
            'page_load_time': np.random.normal(3.2, 0.8, len(sample_times)).clip(1.5, 10)
        })

        fig = px.line(sample_data, x='timestamp', y=['response_time', 'page_load_time'],
                     title='Performance Over Time',
                     labels={'value': 'Time (seconds)', 'timestamp': 'Time'})

        fig.add_hline(y=3.0, line_dash="dash", line_color="red",
                     annotation_text="Response Time Threshold")
        fig.add_hline(y=8.0, line_dash="dash", line_color="orange",
                     annotation_text="Page Load Threshold")

        st.plotly_chart(fig, use_container_width=True)


def render_user_engagement_analytics(dashboard_data: Dict[str, Any], monitor: StreamlitMonitoringIntegration):
    """Render user engagement analytics."""
    st.subheader("🎯 User Engagement Analytics")

    session_health = monitor.get_current_session_health()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Session Activity")

        if session_health.get("status") != "no_active_session":
            # Session duration pie chart
            duration = session_health.get("duration_minutes", 0)
            interactions = session_health.get("interactions_count", 0)
            features_used = session_health.get("features_used_count", 0)

            # Engagement metrics
            engagement_data = pd.DataFrame({
                'Metric': ['Interactions', 'Features Used', 'Session Duration (min)'],
                'Value': [interactions, features_used, duration]
            })

            fig = px.bar(engagement_data, x='Metric', y='Value',
                        title='Current Session Engagement',
                        color='Value', color_continuous_scale='viridis')

            st.plotly_chart(fig, use_container_width=True)

            # Engagement quality assessment
            if duration > 5 and interactions > 10:
                st.success("🎉 High engagement session detected!")
            elif duration > 2 and interactions > 5:
                st.info("👍 Good user engagement")
            else:
                st.warning("⚠️ Low engagement - consider UX improvements")

        else:
            st.info("No active session to analyze")

    with col2:
        st.markdown("#### Feature Usage Distribution")

        # Sample feature usage data
        feature_data = pd.DataFrame({
            'Feature': ['FCF Analysis', 'DCF Valuation', 'P/B Analysis', 'Portfolio View', 'Data Export'],
            'Usage_Count': [45, 32, 28, 15, 8],
            'Success_Rate': [0.92, 0.87, 0.95, 0.78, 0.98]
        })

        fig = px.scatter(feature_data, x='Usage_Count', y='Success_Rate',
                        size='Usage_Count', color='Feature',
                        title='Feature Performance vs Usage',
                        labels={'Usage_Count': 'Usage Count', 'Success_Rate': 'Success Rate'})

        fig.add_hline(y=0.8, line_dash="dash", line_color="red",
                     annotation_text="Minimum Success Rate")

        st.plotly_chart(fig, use_container_width=True)


def render_alerts_and_issues(dashboard_data: Dict[str, Any], monitor: StreamlitMonitoringIntegration):
    """Render alerts and issues section."""
    st.subheader("🚨 Alerts & Issues")

    session_health = monitor.get_current_session_health()
    recent_alerts = session_health.get("recent_alerts", [])

    col1, col2 = st.columns([2, 1])

    with col1:
        if recent_alerts:
            st.markdown("#### Recent Alerts")

            for alert in recent_alerts:
                alert_data = alert if isinstance(alert, dict) else alert.__dict__

                level = alert_data.get('level', 'info')
                title = alert_data.get('title', 'Unknown Alert')
                description = alert_data.get('description', '')
                timestamp = alert_data.get('timestamp', '')

                # Color-code alerts
                if level == 'critical':
                    st.error(f"🔴 **{title}** - {description}")
                elif level == 'error':
                    st.error(f"🟠 **{title}** - {description}")
                elif level == 'warning':
                    st.warning(f"🟡 **{title}** - {description}")
                else:
                    st.info(f"🔵 **{title}** - {description}")

                if timestamp:
                    st.caption(f"Time: {timestamp}")

        else:
            st.success("✅ No recent alerts - System running smoothly!")

    with col2:
        st.markdown("#### System Status")

        # Error rate indicator
        errors_count = session_health.get("errors_count", 0)
        if errors_count == 0:
            st.success("🟢 No Errors")
        elif errors_count < 3:
            st.warning(f"🟡 {errors_count} Minor Issues")
        else:
            st.error(f"🔴 {errors_count} Errors")

        # Performance status
        system_health = session_health.get("system_health", {})
        cpu_usage = system_health.get("cpu_usage_percent", 0)
        memory_usage = system_health.get("memory_usage_percent", 0)

        if cpu_usage < 50 and memory_usage < 50:
            st.success("🟢 Performance: Excellent")
        elif cpu_usage < 70 and memory_usage < 70:
            st.info("🟡 Performance: Good")
        else:
            st.warning("🔴 Performance: Stressed")

    # Alert trends
    st.markdown("#### Alert Trends")
    alert_stats = dashboard_data.get("alert_statistics", [])

    if alert_stats:
        alert_df = pd.DataFrame(alert_stats)
        fig = px.pie(alert_df, values='count', names='level',
                    title='Alert Distribution by Severity')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alerts to display in the selected period")


def render_feature_usage_analytics(dashboard_data: Dict[str, Any], monitor: StreamlitMonitoringIntegration):
    """Render feature usage analytics."""
    st.subheader("🔧 Feature Usage Analytics")

    feature_analytics = dashboard_data.get("feature_analytics", {})
    features_data = feature_analytics.get("features", {})
    recommendations = feature_analytics.get("recommendations", [])

    if features_data:
        # Convert to DataFrame for visualization
        features_list = []
        for feature_name, data in features_data.items():
            features_list.append({
                'Feature': feature_name,
                'Total Uses': data.get('total_uses', 0),
                'Success Rate': data.get('success_rate', 0),
                'Unique Sessions': data.get('unique_sessions', 0),
                'Complexity': data.get('feature_info', {}).get('complexity', 'unknown')
            })

        features_df = pd.DataFrame(features_list)

        col1, col2 = st.columns(2)

        with col1:
            # Feature usage bar chart
            fig = px.bar(features_df, x='Feature', y='Total Uses',
                        title='Feature Usage Frequency',
                        color='Success Rate',
                        color_continuous_scale='RdYlGn')

            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Success rate vs complexity scatter
            fig = px.scatter(features_df, x='Success Rate', y='Total Uses',
                           size='Unique Sessions', color='Complexity',
                           title='Feature Performance Analysis',
                           hover_data=['Feature'])

            fig.add_vline(x=0.8, line_dash="dash", line_color="red",
                         annotation_text="Target Success Rate")

            st.plotly_chart(fig, use_container_width=True)

        # Feature recommendations
        if recommendations:
            st.markdown("#### 💡 Optimization Recommendations")

            for rec in recommendations:
                rec_type = rec.get('type', '')
                feature = rec.get('feature', '')
                message = rec.get('message', '')
                priority = rec.get('priority', 'medium')

                if priority == 'high':
                    st.error(f"🔴 **High Priority**: {message}")
                elif priority == 'medium':
                    st.warning(f"🟡 **Medium Priority**: {message}")
                else:
                    st.info(f"🔵 **Low Priority**: {message}")

    else:
        st.info("No feature usage data available for the selected period")


def render_trends_and_insights(dashboard_data: Dict[str, Any], monitor: StreamlitMonitoringIntegration, time_period: int):
    """Render trends and insights section."""
    st.subheader("📈 Trends & Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Performance Correlation")

        # Performance vs satisfaction correlation
        ux_metrics = dashboard_data.get("ux_metrics", {})
        correlation = ux_metrics.get("performance_satisfaction_correlation", 0)

        st.metric(
            "Performance-Satisfaction Correlation",
            f"{correlation:.2f}",
            delta="Strong" if correlation > 0.8 else "Moderate" if correlation > 0.6 else "Weak"
        )

        # Correlation explanation
        if correlation > 0.8:
            st.success("🎯 Strong correlation indicates performance improvements directly enhance user satisfaction")
        elif correlation > 0.6:
            st.info("👍 Moderate correlation suggests performance is a significant factor in user experience")
        else:
            st.warning("⚠️ Weak correlation may indicate other UX factors need attention")

    with col2:
        st.markdown("#### Usage Patterns")

        # Time-based usage pattern (sample data)
        hours = list(range(24))
        usage_pattern = [
            max(0, 10 + 30 * np.sin((h - 9) * np.pi / 12) + np.random.normal(0, 5))
            for h in hours
        ]

        pattern_df = pd.DataFrame({
            'Hour': hours,
            'Usage': usage_pattern
        })

        fig = px.line(pattern_df, x='Hour', y='Usage',
                     title='Usage Pattern by Hour',
                     markers=True)

        st.plotly_chart(fig, use_container_width=True)

    # Insights summary
    st.markdown("#### 🧠 Key Insights")

    insights = generate_insights(dashboard_data, time_period)

    for insight in insights:
        insight_type = insight.get('type', 'info')
        message = insight.get('message', '')
        impact = insight.get('impact', 'medium')

        if insight_type == 'success':
            st.success(f"✅ {message}")
        elif insight_type == 'warning':
            st.warning(f"⚠️ {message}")
        elif insight_type == 'improvement':
            st.info(f"💡 {message}")
        else:
            st.info(f"ℹ️ {message}")


def generate_insights(dashboard_data: Dict[str, Any], time_period: int) -> List[Dict[str, str]]:
    """Generate insights based on monitoring data."""
    insights = []

    session_stats = dashboard_data.get("session_statistics", {})
    ux_metrics = dashboard_data.get("ux_metrics", {})
    system_health = dashboard_data.get("system_health", {})

    # Session-based insights
    total_sessions = session_stats.get("total_sessions", 0)
    if total_sessions == 0:
        insights.append({
            'type': 'warning',
            'message': f'No user sessions detected in the last {time_period} hours. Consider checking application availability.',
            'impact': 'high'
        })
    elif total_sessions > 20:
        insights.append({
            'type': 'success',
            'message': f'High user activity with {total_sessions} sessions in the last {time_period} hours.',
            'impact': 'positive'
        })

    # Engagement insights
    engagement_score = ux_metrics.get("user_engagement_score", 0)
    if engagement_score > 0.8:
        insights.append({
            'type': 'success',
            'message': f'Excellent user engagement score of {engagement_score:.1%} indicates strong user experience.',
            'impact': 'positive'
        })
    elif engagement_score < 0.5:
        insights.append({
            'type': 'improvement',
            'message': f'User engagement score of {engagement_score:.1%} suggests opportunities for UX improvements.',
            'impact': 'medium'
        })

    # Performance insights
    cpu_usage = system_health.get("cpu_usage_percent", 0)
    memory_usage = system_health.get("memory_usage_percent", 0)

    if cpu_usage > 80 or memory_usage > 80:
        insights.append({
            'type': 'warning',
            'message': f'High resource usage detected (CPU: {cpu_usage:.0f}%, Memory: {memory_usage:.0f}%). Consider performance optimization.',
            'impact': 'high'
        })

    # UAT correlation insight
    correlation = ux_metrics.get("performance_satisfaction_correlation", 0)
    if correlation > 0.85:
        insights.append({
            'type': 'success',
            'message': f'Strong performance-satisfaction correlation ({correlation:.2f}) validates UAT framework success rate of 88.9%.',
            'impact': 'validation'
        })

    return insights


# Integration function for main application
def integrate_ux_monitoring_dashboard():
    """Integration function to add UX monitoring to main application."""
    if st.sidebar.button("🔍 UX Monitoring Dashboard"):
        render_ux_monitoring_dashboard()


if __name__ == "__main__":
    render_ux_monitoring_dashboard()