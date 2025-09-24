"""
Data Quality Dashboard Component for Streamlit
=============================================

This module provides a comprehensive real-time monitoring dashboard for data quality
metrics, displaying advanced scoring results, trends, and predictive alerts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, NamedTuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityMetric:
    """Data class for quality metric information"""
    name: str
    score: float
    weight: float
    status: str
    message: str = ""
    threshold: float = 75.0
    timestamp: Optional[datetime] = None


class DataQualityDashboard:
    """
    Streamlit component for displaying data quality monitoring dashboard
    """

    def __init__(self):
        """Initialize the dashboard"""
        self.colors = {
            'excellent': '#2E8B57',  # Sea Green
            'good': '#32CD32',       # Lime Green
            'warning': '#FFD700',    # Gold
            'critical': '#FF4500',   # Orange Red
            'poor': '#DC143C'        # Crimson
        }

    def render_dashboard(self, enhanced_data_manager, container_key: str = "data_quality"):
        """
        Render the complete data quality monitoring dashboard

        Args:
            enhanced_data_manager: Instance of EnhancedDataManager with quality scoring
            container_key: Unique key for the Streamlit container
        """
        st.header("🔍 Data Quality Monitoring Dashboard")
        st.markdown("---")

        try:
            # Get quality data
            trends = enhanced_data_manager.get_data_quality_trends()
            predictions = enhanced_data_manager.predict_data_quality_issues()
            history = enhanced_data_manager.get_quality_history(limit=50)

            if not history:
                st.info("📊 No quality data available yet. Quality metrics will appear after data fetching operations.")
                return

            # Create tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs([
                "📈 Current Status",
                "📊 Trends & History",
                "🔮 Predictions & Alerts",
                "⚙️ Configuration"
            ])

            with tab1:
                self._render_current_status(history, container_key + "_current")

            with tab2:
                self._render_trends_history(history, trends, container_key + "_trends")

            with tab3:
                self._render_predictions_alerts(predictions, container_key + "_predictions")

            with tab4:
                self._render_configuration(enhanced_data_manager, container_key + "_config")

        except Exception as e:
            st.error(f"Error rendering data quality dashboard: {str(e)}")
            logger.error(f"Dashboard rendering error: {e}")

    def _render_current_status(self, history: List[Dict[str, Any]], container_key: str):
        """Render current quality status overview"""
        if not history:
            st.info("No quality data available")
            return

        latest_metrics = history[-1]

        # Quality Score Overview
        st.subheader("📊 Current Quality Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            overall_score = latest_metrics.get('overall_score', 0)
            color = self._get_score_color(overall_score)
            st.metric(
                label="Overall Score",
                value=f"{overall_score:.1f}%",
                delta=self._calculate_score_delta(history, 'overall_score'),
                delta_color="normal"
            )

        with col2:
            completeness = latest_metrics.get('completeness', 0)
            st.metric(
                label="Completeness",
                value=f"{completeness:.1f}%",
                delta=self._calculate_score_delta(history, 'completeness'),
                delta_color="normal"
            )

        with col3:
            consistency = latest_metrics.get('consistency', 0)
            st.metric(
                label="Consistency",
                value=f"{consistency:.1f}%",
                delta=self._calculate_score_delta(history, 'consistency'),
                delta_color="normal"
            )

        with col4:
            accuracy = latest_metrics.get('accuracy', 0)
            st.metric(
                label="Accuracy",
                value=f"{accuracy:.1f}%",
                delta=self._calculate_score_delta(history, 'accuracy'),
                delta_color="normal"
            )

        # Quality Breakdown Chart
        st.subheader("🎯 Quality Dimensions Breakdown")

        dimensions = {
            'Completeness': latest_metrics.get('completeness', 0),
            'Consistency': latest_metrics.get('consistency', 0),
            'Accuracy': latest_metrics.get('accuracy', 0),
            'Timeliness': latest_metrics.get('timeliness', 0),
            'Validity': latest_metrics.get('validity', 0),
            'Uniqueness': latest_metrics.get('uniqueness', 0)
        }

        # Create radar chart
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=list(dimensions.values()),
            theta=list(dimensions.keys()),
            fill='toself',
            name='Current Quality',
            marker_color=self._get_score_color(overall_score)
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Data Quality Dimensions",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True, key=f"{container_key}_radar")

        # Recent Activity Summary
        st.subheader("📝 Recent Activity")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Last Analysis:** {latest_metrics.get('timestamp', 'Unknown')}")
            st.info(f"**Source:** {latest_metrics.get('source_identifier', 'Unknown')}")

        with col2:
            data_points = latest_metrics.get('data_points_analyzed', 0)
            st.info(f"**Data Points Analyzed:** {data_points:,}")

            # Show quality status badge
            if overall_score >= 90:
                st.success("🟢 Excellent Quality")
            elif overall_score >= 75:
                st.info("🟡 Good Quality")
            elif overall_score >= 60:
                st.warning("🟠 Fair Quality")
            else:
                st.error("🔴 Poor Quality")

    def _render_trends_history(self, history: List[Dict[str, Any]], trends: Dict[str, Any], container_key: str):
        """Render trends and historical analysis"""
        if not history:
            st.info("No historical data available")
            return

        st.subheader("📈 Quality Trends Over Time")

        # Convert history to DataFrame for easier plotting
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Time series plot
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Overall Quality Score', 'Quality Dimensions'),
            vertical_spacing=0.1
        )

        # Overall score trend
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['overall_score'],
                mode='lines+markers',
                name='Overall Score',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6)
            ),
            row=1, col=1
        )

        # Quality dimensions trends
        dimensions = ['completeness', 'consistency', 'accuracy', 'timeliness']
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

        for dim, color in zip(dimensions, colors):
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[dim],
                    mode='lines',
                    name=dim.title(),
                    line=dict(color=color, width=2)
                ),
                row=2, col=1
            )

        fig.update_layout(
            height=600,
            title_text="Quality Metrics Trends",
            showlegend=True
        )

        fig.update_yaxes(title_text="Score (%)", row=1, col=1)
        fig.update_yaxes(title_text="Score (%)", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True, key=f"{container_key}_trends")

        # Trends Analysis Summary
        if trends.get('status') in ['degrading', 'improving', 'stable']:
            st.subheader("🔍 Trend Analysis")

            col1, col2 = st.columns(2)

            with col1:
                trend_status = trends['status']
                trend_icon = {
                    'improving': '📈',
                    'stable': '➡️',
                    'degrading': '📉'
                }.get(trend_status, '❓')

                if trend_status == 'improving':
                    st.success(f"{trend_icon} **Improving Trend**\n\n{trends['message']}")
                elif trend_status == 'stable':
                    st.info(f"{trend_icon} **Stable Trend**\n\n{trends['message']}")
                else:
                    st.warning(f"{trend_icon} **Degrading Trend**\n\n{trends['message']}")

            with col2:
                st.metric(
                    label="Current Score",
                    value=f"{trends.get('current_score', 0):.1f}%",
                    delta=f"{trends.get('overall_trend', 0):.2f} per period"
                )

                score_range = trends.get('score_range', (0, 0))
                st.metric(
                    label="Score Range",
                    value=f"{score_range[0]:.1f}% - {score_range[1]:.1f}%"
                )

        # Statistical Summary
        st.subheader("📊 Statistical Summary")

        stats_df = pd.DataFrame({
            'Metric': ['Overall Score', 'Completeness', 'Consistency', 'Accuracy'],
            'Mean': [
                df['overall_score'].mean(),
                df['completeness'].mean(),
                df['consistency'].mean(),
                df['accuracy'].mean()
            ],
            'Std Dev': [
                df['overall_score'].std(),
                df['completeness'].std(),
                df['consistency'].std(),
                df['accuracy'].std()
            ],
            'Min': [
                df['overall_score'].min(),
                df['completeness'].min(),
                df['consistency'].min(),
                df['accuracy'].min()
            ],
            'Max': [
                df['overall_score'].max(),
                df['completeness'].max(),
                df['consistency'].max(),
                df['accuracy'].max()
            ]
        })

        stats_df = stats_df.round(2)
        st.dataframe(stats_df, use_container_width=True)

    def _render_predictions_alerts(self, predictions: Dict[str, Any], container_key: str):
        """Render predictions and alerts section"""
        st.subheader("🔮 Predictive Analysis & Alerts")

        if predictions.get('status') == 'error':
            st.error(f"Prediction analysis failed: {predictions.get('message', 'Unknown error')}")
            return

        if predictions.get('status') == 'no_prediction':
            st.info("Insufficient data for predictive analysis. More historical data needed.")
            return

        # Risk Assessment
        st.subheader("⚠️ Risk Assessment")

        col1, col2, col3 = st.columns(3)

        with col1:
            current_quality = predictions.get('current_quality', 0)
            st.metric(
                label="Current Quality",
                value=f"{current_quality:.1f}%"
            )

        with col2:
            projected_quality = predictions.get('projected_quality', 0)
            delta = projected_quality - current_quality
            st.metric(
                label="Projected Quality",
                value=f"{projected_quality:.1f}%",
                delta=f"{delta:+.1f}%"
            )

        with col3:
            risk_level = predictions.get('risk_level', 'unknown')
            risk_colors = {
                'low': 'success',
                'medium': 'warning',
                'high': 'error'
            }

            risk_icon = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴'
            }.get(risk_level, '❓')

            if risk_level in risk_colors:
                getattr(st, risk_colors[risk_level])(f"{risk_icon} **Risk Level: {risk_level.upper()}**")

        # Trend Direction
        trend_direction = predictions.get('trend_direction', 'unknown')
        trend_icons = {
            'improving': '📈',
            'stable': '➡️',
            'degrading': '📉'
        }

        if trend_direction in trend_icons:
            st.info(f"**Trend Direction:** {trend_icons[trend_direction]} {trend_direction.title()}")

        # Recommendations
        recommendations = predictions.get('recommendations', [])
        if recommendations:
            st.subheader("💡 Recommendations")

            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")

        # Prediction Timeline
        prediction_hours = predictions.get('prediction_window_hours', 24)
        st.info(f"📅 **Prediction Window:** {prediction_hours} hours ahead")

    def _render_configuration(self, enhanced_data_manager, container_key: str):
        """Render configuration and settings"""
        st.subheader("⚙️ Data Quality Configuration")

        # Quality Thresholds Configuration
        st.write("**Quality Score Thresholds**")

        col1, col2 = st.columns(2)

        with col1:
            warning_threshold = st.slider(
                "Warning Threshold (%)",
                min_value=50,
                max_value=90,
                value=75,
                help="Quality scores below this threshold will generate warnings",
                key=f"{container_key}_warning_threshold"
            )

        with col2:
            critical_threshold = st.slider(
                "Critical Threshold (%)",
                min_value=30,
                max_value=70,
                value=60,
                help="Quality scores below this threshold will generate critical alerts",
                key=f"{container_key}_critical_threshold"
            )

        # Data Source Information
        st.subheader("📡 Data Sources")

        try:
            sources_info = enhanced_data_manager.get_available_data_sources()

            if sources_info.get('enhanced_sources'):
                st.write(f"**Active Sources:** {sources_info['active_sources']} of {sources_info['total_sources']}")

                # Display source details
                sources_df = []
                for source_name, source_info in sources_info['enhanced_sources'].items():
                    sources_df.append({
                        'Source': source_name,
                        'Status': '🟢 Enabled' if source_info['enabled'] else '🔴 Disabled',
                        'Priority': source_info['priority'],
                        'Has Credentials': '✅' if source_info['has_credentials'] else '❌',
                        'Quality Threshold': f"{source_info['quality_threshold']:.1f}%"
                    })

                if sources_df:
                    st.dataframe(pd.DataFrame(sources_df), use_container_width=True)

        except Exception as e:
            st.warning(f"Could not load data source information: {e}")

        # Monitoring Controls
        st.subheader("🔧 Monitoring Controls")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Refresh Quality Data", key=f"{container_key}_refresh"):
                st.rerun()

        with col2:
            if st.button("📥 Export Quality History", key=f"{container_key}_export"):
                try:
                    history = enhanced_data_manager.get_quality_history(limit=1000)
                    if history:
                        df = pd.DataFrame(history)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"data_quality_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No quality history to export")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    def _get_score_color(self, score: float) -> str:
        """Get color based on quality score"""
        if score >= 90:
            return self.colors['excellent']
        elif score >= 75:
            return self.colors['good']
        elif score >= 60:
            return self.colors['warning']
        elif score >= 40:
            return self.colors['critical']
        else:
            return self.colors['poor']

    def _calculate_score_delta(self, history: List[Dict[str, Any]], metric: str) -> Optional[str]:
        """Calculate score delta for metrics display"""
        if len(history) < 2:
            return None

        current = history[-1].get(metric, 0)
        previous = history[-2].get(metric, 0)
        delta = current - previous

        if abs(delta) < 0.1:  # No significant change
            return None

        return f"{delta:+.1f}%"


def render_quality_monitoring_tab(enhanced_data_manager):
    """
    Render the data quality monitoring as a tab in the main application

    Args:
        enhanced_data_manager: Instance of EnhancedDataManager
    """
    dashboard = DataQualityDashboard()
    dashboard.render_dashboard(enhanced_data_manager, "main_dashboard")


def create_data_quality_dashboard(**kwargs):
    """
    Factory function to create a DataQualityDashboard instance

    Args:
        **kwargs: Additional configuration options for the dashboard

    Returns:
        DataQualityDashboard: Configured dashboard instance
    """
    return DataQualityDashboard()


# Export main components
__all__ = [
    'DataQualityDashboard',
    'render_quality_monitoring_tab',
    'QualityMetric',
    'create_data_quality_dashboard'
]