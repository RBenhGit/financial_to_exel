"""
User Analytics Visualization

Advanced visualization components for user analytics, including analysis history,
usage trends, performance metrics, and interactive charts for the user profile dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from core.user_preferences.user_analytics import (
    UserAnalyticsTracker, AnalysisSession, UsageStatistics, AnalysisType, EventType
)

logger = logging.getLogger(__name__)


class UserAnalyticsVisualizer:
    """Comprehensive visualization component for user analytics"""

    def __init__(self, analytics_tracker: UserAnalyticsTracker):
        """
        Initialize the analytics visualizer

        Args:
            analytics_tracker: Analytics tracker instance
        """
        self.tracker = analytics_tracker

    def render_usage_overview_charts(self, user_id: str, period_days: int = 30) -> None:
        """
        Render usage overview charts for a user

        Args:
            user_id: User identifier
            period_days: Period in days to analyze
        """
        st.subheader("📊 Usage Overview")

        # Generate usage statistics
        stats = self.tracker.generate_usage_statistics(user_id, period_days)
        if not stats:
            st.error("Failed to load usage statistics")
            return

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Analyses",
                stats.total_analyses,
                delta=f"+{stats.successful_analyses - stats.failed_analyses}" if stats.total_analyses > 0 else None,
                help="Total number of analyses performed"
            )

        with col2:
            success_rate = (stats.successful_analyses / stats.total_analyses * 100) if stats.total_analyses > 0 else 0
            st.metric(
                "Success Rate",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 90:.1f}%" if success_rate > 0 else None,
                help="Percentage of successful analyses"
            )

        with col3:
            st.metric(
                "Avg Analysis Time",
                f"{stats.average_analysis_time_seconds:.1f}s",
                delta=f"-{max(0, stats.average_analysis_time_seconds - 30):.1f}s" if stats.average_analysis_time_seconds > 30 else None,
                help="Average time per analysis"
            )

        with col4:
            st.metric(
                "Data Quality",
                f"{stats.average_data_quality_score:.1f}%",
                delta=f"{stats.average_data_quality_score - 85:.1f}%" if stats.average_data_quality_score > 0 else None,
                help="Average data quality score"
            )

        # Analysis type distribution
        self._render_analysis_type_distribution(stats)

        # Performance trends
        self._render_performance_trends(user_id, period_days)

    def render_analysis_history_timeline(self, user_id: str, limit: int = 20) -> None:
        """
        Render analysis history timeline

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to show
        """
        st.subheader("📈 Analysis History Timeline")

        # Get analysis history
        sessions = self.tracker.get_analysis_history(user_id, limit)
        if not sessions:
            st.info("No analysis history available")
            return

        # Convert to DataFrame for visualization
        session_data = []
        for session in sessions:
            session_data.append({
                'Session ID': session.session_id,
                'Company': session.company_ticker,
                'Analysis Type': session.analysis_type.value.upper(),
                'Start Time': session.start_time,
                'End Time': session.end_time or session.start_time,
                'Duration (s)': session.execution_time_seconds,
                'Success': session.success,
                'Data Quality': session.data_quality_score
            })

        df = pd.DataFrame(session_data)

        if df.empty:
            st.info("No analysis sessions found")
            return

        # Timeline chart
        fig = px.timeline(
            df,
            x_start="Start Time",
            x_end="End Time",
            y="Company",
            color="Analysis Type",
            title="Analysis Timeline",
            hover_data=["Duration (s)", "Success", "Data Quality"],
            height=max(400, len(df) * 25)
        )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Company",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Analysis history table
        st.subheader("📋 Detailed History")

        # Format the DataFrame for display
        display_df = df.copy()
        display_df['Success'] = display_df['Success'].map({True: '✅', False: '❌'})
        display_df['Duration (s)'] = display_df['Duration (s)'].round(1)
        display_df['Data Quality'] = display_df['Data Quality'].round(1)

        st.dataframe(
            display_df[['Company', 'Analysis Type', 'Start Time', 'Duration (s)', 'Success', 'Data Quality']],
            use_container_width=True,
            hide_index=True
        )

    def render_performance_analytics(self, user_id: str, period_days: int = 30) -> None:
        """
        Render performance analytics charts

        Args:
            user_id: User identifier
            period_days: Period in days to analyze
        """
        st.subheader("⚡ Performance Analytics")

        # Get sessions for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        sessions = self.tracker._load_sessions_for_period(user_id, start_date, end_date)

        if not sessions:
            st.info("No performance data available for the selected period")
            return

        # Performance metrics over time
        self._render_performance_over_time(sessions)

        # Efficiency analysis
        self._render_efficiency_analysis(sessions)

        # Error analysis
        self._render_error_analysis(sessions)

    def render_company_analysis_breakdown(self, user_id: str, period_days: int = 30) -> None:
        """
        Render company analysis breakdown

        Args:
            user_id: User identifier
            period_days: Period in days to analyze
        """
        st.subheader("🏢 Company Analysis Breakdown")

        # Get sessions for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        sessions = self.tracker._load_sessions_for_period(user_id, start_date, end_date)

        if not sessions:
            st.info("No analysis data available for the selected period")
            return

        # Company frequency analysis
        company_counts = {}
        company_success_rates = {}

        for session in sessions:
            ticker = session.company_ticker
            company_counts[ticker] = company_counts.get(ticker, 0) + 1

            if ticker not in company_success_rates:
                company_success_rates[ticker] = {'success': 0, 'total': 0}

            company_success_rates[ticker]['total'] += 1
            if session.success:
                company_success_rates[ticker]['success'] += 1

        # Most analyzed companies
        col1, col2 = st.columns(2)

        with col1:
            if company_counts:
                top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                fig = px.bar(
                    x=[count for _, count in top_companies],
                    y=[company for company, _ in top_companies],
                    orientation='h',
                    title="Most Analyzed Companies",
                    labels={'x': 'Number of Analyses', 'y': 'Company'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Success rates by company
            if company_success_rates:
                success_data = []
                for company, data in company_success_rates.items():
                    if data['total'] >= 2:  # Only show companies with multiple analyses
                        success_rate = (data['success'] / data['total']) * 100
                        success_data.append({
                            'Company': company,
                            'Success Rate': success_rate,
                            'Total Analyses': data['total']
                        })

                if success_data:
                    success_df = pd.DataFrame(success_data)
                    success_df = success_df.sort_values('Success Rate', ascending=True)

                    fig = px.bar(
                        success_df,
                        x='Success Rate',
                        y='Company',
                        orientation='h',
                        title="Success Rate by Company (2+ analyses)",
                        labels={'Success Rate': 'Success Rate (%)', 'Company': 'Company'},
                        hover_data=['Total Analyses']
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

    def render_usage_heatmap(self, user_id: str, period_days: int = 30) -> None:
        """
        Render usage heatmap showing activity patterns

        Args:
            user_id: User identifier
            period_days: Period in days to analyze
        """
        st.subheader("🔥 Activity Heatmap")

        # Get sessions for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        sessions = self.tracker._load_sessions_for_period(user_id, start_date, end_date)

        if not sessions:
            st.info("No activity data available for the selected period")
            return

        # Create heatmap data
        heatmap_data = self._create_activity_heatmap_data(sessions)

        if heatmap_data is not None:
            fig = px.imshow(
                heatmap_data,
                title="Activity Heatmap (Hour of Day vs Day of Week)",
                labels=dict(x="Day of Week", y="Hour of Day", color="Activity Count"),
                aspect="auto",
                color_continuous_scale="viridis"
            )

            fig.update_xaxes(
                tickvals=list(range(7)),
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            )

            fig.update_yaxes(
                tickvals=list(range(0, 24, 2)),
                ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)]
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_analysis_type_distribution(self, stats: UsageStatistics) -> None:
        """Render analysis type distribution pie chart"""
        if not stats.analyses_by_type:
            return

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=list(stats.analyses_by_type.values()),
                names=[name.replace('_', ' ').title() for name in stats.analyses_by_type.keys()],
                title='Analysis Type Distribution'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=list(stats.analyses_by_type.values()),
                y=[name.replace('_', ' ').title() for name in stats.analyses_by_type.keys()],
                orientation='h',
                title='Analysis Type Counts',
                labels={'x': 'Count', 'y': 'Analysis Type'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    def _render_performance_trends(self, user_id: str, period_days: int) -> None:
        """Render performance trends over time"""
        # Generate sample trend data (in real implementation, this would use actual data)
        dates = pd.date_range(end=datetime.now(), periods=period_days, freq='D')

        # Sample performance data
        np.random.seed(42)  # For consistent demo data
        execution_times = 30 + np.random.normal(0, 5, period_days)
        success_rates = 85 + np.random.normal(0, 10, period_days)
        data_quality = 80 + np.random.normal(0, 8, period_days)

        # Ensure values are within reasonable bounds
        execution_times = np.clip(execution_times, 10, 120)
        success_rates = np.clip(success_rates, 0, 100)
        data_quality = np.clip(data_quality, 0, 100)

        # Create subplot
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Execution Time (s)', 'Success Rate (%)', 'Data Quality (%)'),
            shared_xaxes=True,
            vertical_spacing=0.08
        )

        # Add traces
        fig.add_trace(
            go.Scatter(x=dates, y=execution_times, name='Execution Time', line=dict(color='blue')),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=dates, y=success_rates, name='Success Rate', line=dict(color='green')),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=dates, y=data_quality, name='Data Quality', line=dict(color='orange')),
            row=3, col=1
        )

        fig.update_layout(
            title="Performance Trends Over Time",
            height=600,
            showlegend=False
        )

        fig.update_xaxes(title_text="Date", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

    def _render_performance_over_time(self, sessions: List[AnalysisSession]) -> None:
        """Render performance metrics over time"""
        if not sessions:
            return

        # Convert sessions to DataFrame
        session_data = []
        for session in sessions:
            session_data.append({
                'date': session.start_time.date(),
                'execution_time': session.execution_time_seconds,
                'data_quality': session.data_quality_score,
                'success': session.success
            })

        df = pd.DataFrame(session_data)

        # Group by date and calculate averages
        daily_stats = df.groupby('date').agg({
            'execution_time': 'mean',
            'data_quality': 'mean',
            'success': 'mean'
        }).reset_index()

        if daily_stats.empty:
            return

        # Create subplot
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Average Execution Time', 'Data Quality & Success Rate'),
            shared_xaxes=True
        )

        # Execution time
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['execution_time'],
                name='Execution Time (s)',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        # Data quality and success rate
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['data_quality'],
                name='Data Quality (%)',
                line=dict(color='orange')
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['success'] * 100,
                name='Success Rate (%)',
                line=dict(color='green')
            ),
            row=2, col=1
        )

        fig.update_layout(height=500, title="Performance Over Time")
        st.plotly_chart(fig, use_container_width=True)

    def _render_efficiency_analysis(self, sessions: List[AnalysisSession]) -> None:
        """Render efficiency analysis charts"""
        if not sessions:
            return

        col1, col2 = st.columns(2)

        with col1:
            # Cache hit rate analysis
            cache_data = []
            for session in sessions:
                total_requests = session.cache_hits + session.api_calls
                if total_requests > 0:
                    cache_rate = (session.cache_hits / total_requests) * 100
                    cache_data.append({
                        'company': session.company_ticker,
                        'cache_rate': cache_rate,
                        'total_requests': total_requests
                    })

            if cache_data:
                cache_df = pd.DataFrame(cache_data)
                avg_cache_rate = cache_df['cache_rate'].mean()

                fig = px.histogram(
                    cache_df,
                    x='cache_rate',
                    title=f'Cache Hit Rate Distribution (Avg: {avg_cache_rate:.1f}%)',
                    labels={'cache_rate': 'Cache Hit Rate (%)', 'count': 'Frequency'}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Execution time distribution
            execution_times = [s.execution_time_seconds for s in sessions if s.execution_time_seconds > 0]
            if execution_times:
                fig = px.histogram(
                    x=execution_times,
                    title=f'Execution Time Distribution (Avg: {np.mean(execution_times):.1f}s)',
                    labels={'x': 'Execution Time (s)', 'count': 'Frequency'}
                )
                st.plotly_chart(fig, use_container_width=True)

    def _render_error_analysis(self, sessions: List[AnalysisSession]) -> None:
        """Render error analysis"""
        failed_sessions = [s for s in sessions if not s.success]

        if not failed_sessions:
            st.success("🎉 No errors in the selected period!")
            return

        st.subheader("❌ Error Analysis")

        # Error rate over time
        daily_errors = {}
        daily_totals = {}

        for session in sessions:
            date_key = session.start_time.date()
            daily_totals[date_key] = daily_totals.get(date_key, 0) + 1
            if not session.success:
                daily_errors[date_key] = daily_errors.get(date_key, 0) + 1

        error_data = []
        for date, total in daily_totals.items():
            error_count = daily_errors.get(date, 0)
            error_rate = (error_count / total) * 100
            error_data.append({
                'date': date,
                'error_rate': error_rate,
                'error_count': error_count,
                'total_analyses': total
            })

        if error_data:
            error_df = pd.DataFrame(error_data)

            fig = px.line(
                error_df,
                x='date',
                y='error_rate',
                title='Error Rate Over Time',
                labels={'error_rate': 'Error Rate (%)', 'date': 'Date'},
                hover_data=['error_count', 'total_analyses']
            )
            st.plotly_chart(fig, use_container_width=True)

        # Common error messages
        error_messages = [s.error_message for s in failed_sessions if s.error_message]
        if error_messages:
            st.subheader("Common Error Messages")
            for i, msg in enumerate(set(error_messages)[:5], 1):
                count = error_messages.count(msg)
                st.write(f"{i}. **{msg}** (occurred {count} times)")

    def _create_activity_heatmap_data(self, sessions: List[AnalysisSession]) -> Optional[np.ndarray]:
        """Create activity heatmap data matrix"""
        if not sessions:
            return None

        # Initialize 24x7 matrix (hours x days of week)
        heatmap = np.zeros((24, 7))

        for session in sessions:
            hour = session.start_time.hour
            day_of_week = session.start_time.weekday()  # 0=Monday, 6=Sunday
            heatmap[hour][day_of_week] += 1

        return heatmap


def create_user_analytics_visualizer(analytics_tracker: UserAnalyticsTracker) -> UserAnalyticsVisualizer:
    """Create and return a UserAnalyticsVisualizer instance"""
    return UserAnalyticsVisualizer(analytics_tracker)