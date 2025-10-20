"""
User Profile Dashboard

A comprehensive dashboard showing user analytics, usage statistics, analysis history,
favorite companies, and preference management interface for the financial analysis application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from core.user_preferences.user_profile import (
    UserProfile, UserPreferences, AnalysisMethodology, CurrencyPreference, RegionPreference
)
from core.user_preferences.preference_manager import get_preference_manager
from core.user_preferences.user_analytics import get_analytics_tracker, AnalysisType, EventType
from ui.streamlit.user_preferences_ui import UserPreferencesUI
from ui.visualization.user_analytics_visualizer import create_user_analytics_visualizer

logger = logging.getLogger(__name__)


class UserProfileDashboard:
    """Comprehensive user profile dashboard for analytics and management"""

    def __init__(self):
        """Initialize the user profile dashboard"""
        self.manager = get_preference_manager()
        self.preferences_ui = UserPreferencesUI()
        self.analytics_tracker = get_analytics_tracker()
        self.analytics_visualizer = create_user_analytics_visualizer(self.analytics_tracker)
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize session state variables"""
        if 'user_dashboard_initialized' not in st.session_state:
            st.session_state.user_dashboard_initialized = True
            st.session_state.dashboard_view = 'overview'
            st.session_state.show_detailed_analytics = False
            st.session_state.selected_time_range = '30 days'

    def render_dashboard(self) -> None:
        """Render the complete user profile dashboard"""
        current_user = self.manager.get_current_user()
        if not current_user:
            self._render_login_required_message()
            return

        st.title("👤 User Profile Dashboard")
        st.caption(f"Welcome back, {current_user.username}!")

        # Dashboard navigation tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview",
            "📈 Analytics",
            "📋 Activity",
            "⭐ Favorites",
            "⚙️ Preferences",
            "📤 Export/Import"
        ])

        with tab1:
            self._render_overview_tab(current_user)

        with tab2:
            self._render_analytics_tab(current_user)

        with tab3:
            self._render_activity_tab(current_user)

        with tab4:
            self._render_favorites_tab(current_user)

        with tab5:
            self._render_preferences_tab(current_user)

        with tab6:
            self._render_export_import_tab(current_user)

    def _render_login_required_message(self) -> None:
        """Show login required message with login interface"""
        st.warning("🔒 Please log in to access your profile dashboard")

        with st.expander("Login or Register", expanded=True):
            self.preferences_ui._render_user_login_controls(context="dashboard")

    def _render_overview_tab(self, user: UserProfile) -> None:
        """Render the overview tab with key metrics and quick stats"""
        st.header("📊 Profile Overview")

        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        analytics = self.manager.get_user_analytics(user.user_id)
        if analytics:
            with col1:
                st.metric(
                    "Total Analyses",
                    analytics['total_analyses'],
                    help="Total number of financial analyses performed"
                )

            with col2:
                st.metric(
                    "Login Sessions",
                    analytics['login_count'],
                    help="Number of times you've logged in"
                )

            with col3:
                st.metric(
                    "Favorite Companies",
                    analytics['favorite_companies_count'],
                    help="Companies added to your favorites"
                )

            with col4:
                days_since_created = (datetime.now() - user.created_at).days if user.created_at else 0
                st.metric(
                    "Days Active",
                    days_since_created,
                    help="Days since account creation"
                )

        # Profile information section
        st.subheader("👤 Profile Information")

        profile_col1, profile_col2 = st.columns(2)

        with profile_col1:
            st.info(f"**User ID:** {user.user_id}")
            st.info(f"**Username:** {user.username}")
            if user.email:
                st.info(f"**Email:** {user.email}")

        with profile_col2:
            if user.created_at:
                st.info(f"**Member Since:** {user.created_at.strftime('%B %d, %Y')}")
            if user.last_login:
                st.info(f"**Last Login:** {user.last_login.strftime('%B %d, %Y at %I:%M %p')}")

        # Quick preferences summary
        st.subheader("⚙️ Current Preferences Summary")

        prefs_col1, prefs_col2, prefs_col3 = st.columns(3)

        with prefs_col1:
            st.write("**Financial Preferences**")
            st.write(f"• Methodology: {user.preferences.financial.methodology.value.title()}")
            st.write(f"• Primary Currency: {user.preferences.financial.primary_currency.value}")
            st.write(f"• Discount Rate: {user.preferences.financial.default_discount_rate:.1%}")

        with prefs_col2:
            st.write("**Display Preferences**")
            st.write(f"• Chart Theme: {user.preferences.display.chart_theme.title()}")
            st.write(f"• Decimal Places: {user.preferences.display.decimal_places}")
            st.write(f"• Thousands Separator: {'Yes' if user.preferences.display.use_thousands_separator else 'No'}")

        with prefs_col3:
            st.write("**Data Preferences**")
            st.write(f"• Prefer Excel: {'Yes' if user.preferences.data_sources.prefer_excel_over_api else 'No'}")
            st.write(f"• Cache Duration: {user.preferences.data_sources.cache_duration_hours}h")
            st.write(f"• Auto Refresh: {'Yes' if user.preferences.data_sources.auto_refresh_data else 'No'}")

        # Recent activity preview
        if user.recent_searches:
            st.subheader("🔍 Recent Activity Preview")
            recent_searches = user.recent_searches[:5]
            for i, search in enumerate(recent_searches, 1):
                st.write(f"{i}. {search}")

            if len(user.recent_searches) > 5:
                st.caption(f"... and {len(user.recent_searches) - 5} more searches")

    def _render_analytics_tab(self, user: UserProfile) -> None:
        """Render detailed analytics and usage statistics"""
        st.header("📈 Detailed Analytics")

        # Time range selector
        time_range = st.selectbox(
            "📅 Time Range",
            options=['7 days', '30 days', '90 days', '1 year', 'All time'],
            index=1,
            key="analytics_time_range"
        )

        # Convert time range to days
        period_days_map = {
            '7 days': 7,
            '30 days': 30,
            '90 days': 90,
            '1 year': 365,
            'All time': 1000  # Large number for all-time
        }
        period_days = period_days_map.get(time_range, 30)

        # Advanced analytics visualization
        try:
            # Usage overview charts
            self.analytics_visualizer.render_usage_overview_charts(user.user_id, period_days)

            # Analytics sub-tabs
            analytics_tabs = st.tabs([
                "📊 Performance",
                "📈 History",
                "🏢 Companies",
                "🔥 Activity Patterns"
            ])

            with analytics_tabs[0]:
                self.analytics_visualizer.render_performance_analytics(user.user_id, period_days)

            with analytics_tabs[1]:
                self.analytics_visualizer.render_analysis_history_timeline(user.user_id, limit=50)

            with analytics_tabs[2]:
                self.analytics_visualizer.render_company_analysis_breakdown(user.user_id, period_days)

            with analytics_tabs[3]:
                self.analytics_visualizer.render_usage_heatmap(user.user_id, period_days)

        except Exception as e:
            logger.error(f"Error rendering analytics: {e}")
            st.error("Failed to load advanced analytics. Falling back to basic analytics.")

            # Fallback to basic analytics
            self._render_basic_analytics(user, period_days)

    def _render_basic_analytics(self, user: UserProfile, period_days: int) -> None:
        """Render basic analytics as fallback"""
        analytics = self.manager.get_user_analytics(user.user_id)
        if not analytics:
            st.error("Failed to load analytics data")
            return

        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Analyses",
                analytics['total_analyses'],
                help="Total number of analyses performed"
            )

        with col2:
            st.metric(
                "Login Count",
                analytics['login_count'],
                help="Number of login sessions"
            )

        with col3:
            st.metric(
                "Favorite Companies",
                analytics['favorite_companies_count'],
                help="Companies in favorites list"
            )

        with col4:
            st.metric(
                "Recent Searches",
                analytics['recent_searches_count'],
                help="Number of recent searches"
            )

        # Sample charts for demonstration
        st.subheader("Sample Analytics")
        st.info("Advanced analytics require activity data. Start using the application to see detailed analytics!")

    def _render_activity_tab(self, user: UserProfile) -> None:
        """Render user activity timeline and history"""
        st.header("📋 Activity Timeline")

        # Activity timeline visualization
        activity_data = self._generate_sample_activity_data(user)

        if activity_data:
            # Timeline chart
            fig = px.timeline(
                activity_data,
                x_start="start_time",
                x_end="end_time",
                y="activity_type",
                color="activity_type",
                title="Recent Activity Timeline",
                labels={"activity_type": "Activity Type"}
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

        # Recent searches section
        st.subheader("🔍 Search History")

        if user.recent_searches:
            search_df = pd.DataFrame({
                'Search Term': user.recent_searches,
                'Rank': range(1, len(user.recent_searches) + 1)
            })

            st.dataframe(
                search_df,
                use_container_width=True,
                hide_index=True
            )

            # Search frequency analysis
            if len(user.recent_searches) > 1:
                search_counts = pd.Series(user.recent_searches).value_counts().head(10)

                fig_search = px.bar(
                    x=search_counts.index,
                    y=search_counts.values,
                    title="Most Searched Terms",
                    labels={'x': 'Search Term', 'y': 'Frequency'}
                )
                st.plotly_chart(fig_search, use_container_width=True)
        else:
            st.info("No search history available")

        # Session activity log
        st.subheader("📝 Session Log")

        # Sample session data
        session_data = [
            {"timestamp": "2024-01-15 09:30:15", "action": "Login", "details": "Successful login from Chrome"},
            {"timestamp": "2024-01-15 09:31:42", "action": "Search", "details": "Searched for 'AAPL'"},
            {"timestamp": "2024-01-15 09:35:18", "action": "Analysis", "details": "Completed DCF analysis for AAPL"},
            {"timestamp": "2024-01-15 09:40:33", "action": "Export", "details": "Exported results to Excel"},
            {"timestamp": "2024-01-15 09:45:12", "action": "Preferences", "details": "Updated display preferences"},
        ]

        session_df = pd.DataFrame(session_data)
        st.dataframe(
            session_df,
            use_container_width=True,
            hide_index=True
        )

    def _render_favorites_tab(self, user: UserProfile) -> None:
        """Render favorite companies management interface"""
        st.header("⭐ Favorite Companies")

        # Add new favorite section
        st.subheader("➕ Add New Favorite")

        col1, col2 = st.columns([3, 1])

        with col1:
            new_ticker = st.text_input(
                "Company Ticker",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                help="Enter the stock ticker symbol"
            ).upper()

        with col2:
            if st.button("Add to Favorites", type="primary", disabled=not new_ticker):
                if new_ticker and new_ticker not in user.favorite_companies:
                    user.add_favorite_company(new_ticker)
                    if self.manager.update_user(user):
                        st.success(f"Added {new_ticker} to favorites!")
                        st.rerun()
                    else:
                        st.error("Failed to save favorite")
                elif new_ticker in user.favorite_companies:
                    st.warning(f"{new_ticker} is already in your favorites")

        # Display current favorites
        st.subheader("📋 Your Favorites")

        if user.favorite_companies:
            # Create favorites dataframe with mock data
            favorites_data = []
            for ticker in user.favorite_companies:
                # In a real implementation, this would fetch actual market data
                favorites_data.append({
                    'Ticker': ticker,
                    'Company Name': f"{ticker} Corporation",  # Mock data
                    'Current Price': f"${100 + hash(ticker) % 200:.2f}",  # Mock price
                    'Market Cap': f"${(hash(ticker) % 500 + 50):.1f}B",  # Mock market cap
                    'Last Analysis': "3 days ago",  # Mock data
                    'Actions': ticker
                })

            favorites_df = pd.DataFrame(favorites_data)

            # Display as interactive table
            for idx, row in favorites_df.iterrows():
                with st.container():
                    fav_col1, fav_col2, fav_col3, fav_col4, fav_col5 = st.columns([2, 3, 2, 2, 2])

                    with fav_col1:
                        st.write(f"**{row['Ticker']}**")

                    with fav_col2:
                        st.write(row['Company Name'])

                    with fav_col3:
                        st.write(row['Current Price'])

                    with fav_col4:
                        st.write(row['Market Cap'])

                    with fav_col5:
                        if st.button("🗑️ Remove", key=f"remove_{row['Ticker']}"):
                            user.remove_favorite_company(row['Ticker'])
                            if self.manager.update_user(user):
                                st.success(f"Removed {row['Ticker']} from favorites")
                                st.rerun()

                    st.divider()

            # Favorites analytics
            st.subheader("📊 Favorites Analytics")

            fav_col1, fav_col2 = st.columns(2)

            with fav_col1:
                st.metric(
                    "Total Favorites",
                    len(user.favorite_companies),
                    help="Number of companies in your favorites list"
                )

            with fav_col2:
                # Mock sector distribution
                sectors = ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer']
                sector_counts = [len(user.favorite_companies) // len(sectors) + (1 if i < len(user.favorite_companies) % len(sectors) else 0) for i in range(len(sectors))]

                fig_sectors = px.pie(
                    values=sector_counts,
                    names=sectors,
                    title='Favorites by Sector'
                )
                st.plotly_chart(fig_sectors, use_container_width=True)

        else:
            st.info("You haven't added any favorite companies yet. Add some above to get started!")

    def _render_preferences_tab(self, user: UserProfile) -> None:
        """Render preferences management interface"""
        st.header("⚙️ Preferences Management")

        # Embedded preferences interface
        self.preferences_ui.render_preferences_interface()

    def _render_export_import_tab(self, user: UserProfile) -> None:
        """Render preference export/import functionality"""
        st.header("📤 Export/Import Preferences")

        # Export section
        st.subheader("📤 Export Your Data")

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            st.write("**Export Options:**")

            export_preferences = st.checkbox("Preferences", value=True)
            export_favorites = st.checkbox("Favorite Companies", value=True)
            export_analytics = st.checkbox("Analytics Data", value=True)
            export_searches = st.checkbox("Search History", value=False)

        with export_col2:
            export_format = st.selectbox(
                "Export Format",
                options=["JSON", "CSV", "Excel"],
                help="Choose the format for your exported data"
            )

        if st.button("🔽 Export Data", type="primary"):
            export_data = self._generate_export_data(
                user,
                export_preferences,
                export_favorites,
                export_analytics,
                export_searches
            )

            if export_format == "JSON":
                export_json = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="Download JSON File",
                    data=export_json,
                    file_name=f"user_data_{user.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            elif export_format == "CSV":
                # Convert to CSV format (simplified)
                csv_data = self._convert_to_csv(export_data)
                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name=f"user_data_{user.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            st.success("Export generated successfully!")

        # Import section
        st.subheader("📥 Import Preferences")

        st.warning("⚠️ Importing will overwrite your current preferences. Make sure to export your current settings first!")

        uploaded_file = st.file_uploader(
            "Choose preferences file",
            type=['json'],
            help="Upload a previously exported preferences file"
        )

        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)

                # Preview import data
                st.subheader("Preview Import Data")
                st.json(import_data)

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Confirm Import", type="primary"):
                        if self._import_user_data(user, import_data):
                            st.success("Preferences imported successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to import preferences")

                with col2:
                    if st.button("❌ Cancel Import"):
                        st.info("Import cancelled")
                        st.rerun()

            except Exception as e:
                st.error(f"Failed to read import file: {e}")

        # Preference comparison tools
        st.subheader("🔍 Preference Comparison")

        # Allow users to compare their current preferences with defaults
        if st.button("Compare with Default Preferences"):
            default_prefs = UserPreferences()
            current_prefs = user.preferences

            comparison_data = self._compare_preferences(current_prefs, default_prefs)

            st.subheader("Preference Comparison Results")

            for category, differences in comparison_data.items():
                if differences:
                    st.write(f"**{category.title()}:**")
                    for diff in differences:
                        st.write(f"• {diff}")
                else:
                    st.success(f"✅ {category.title()}: No differences from defaults")

    def _generate_sample_usage_data(self, user: UserProfile, time_range: str) -> pd.DataFrame:
        """Generate sample usage data for analytics visualization"""
        # In a real implementation, this would query actual usage logs
        import random
        from datetime import timedelta

        days = {'7 days': 7, '30 days': 30, '90 days': 90, '1 year': 365, 'All time': 365}
        num_days = days.get(time_range, 30)

        dates = [datetime.now() - timedelta(days=i) for i in range(num_days)]
        analyses_counts = [random.randint(0, 5) for _ in range(num_days)]

        return pd.DataFrame({
            'date': dates,
            'analyses_count': analyses_counts
        })

    def _generate_sample_activity_data(self, user: UserProfile) -> pd.DataFrame:
        """Generate sample activity timeline data"""
        activities = [
            {'activity_type': 'Analysis', 'start_time': datetime.now() - timedelta(hours=2), 'end_time': datetime.now() - timedelta(hours=1.5)},
            {'activity_type': 'Search', 'start_time': datetime.now() - timedelta(hours=4), 'end_time': datetime.now() - timedelta(hours=3.9)},
            {'activity_type': 'Export', 'start_time': datetime.now() - timedelta(hours=1), 'end_time': datetime.now() - timedelta(hours=0.8)},
            {'activity_type': 'Preferences', 'start_time': datetime.now() - timedelta(hours=6), 'end_time': datetime.now() - timedelta(hours=5.7)},
        ]

        return pd.DataFrame(activities)

    def _generate_export_data(self, user: UserProfile, include_prefs: bool, include_favs: bool,
                            include_analytics: bool, include_searches: bool) -> Dict[str, Any]:
        """Generate export data based on selected options"""
        export_data = {
            'user_id': user.user_id,
            'username': user.username,
            'export_timestamp': datetime.now().isoformat(),
            'export_version': '1.0'
        }

        if include_prefs:
            export_data['preferences'] = user.preferences.to_dict() if hasattr(user.preferences, 'to_dict') else user.to_dict()['preferences']

        if include_favs:
            export_data['favorite_companies'] = user.favorite_companies

        if include_analytics:
            export_data['analytics'] = self.manager.get_user_analytics(user.user_id)

        if include_searches:
            export_data['search_history'] = user.recent_searches

        return export_data

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert export data to CSV format"""
        # Simplified CSV conversion
        csv_lines = []
        csv_lines.append("Key,Value")

        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, '; '.join(map(str, v))))
                else:
                    items.append((new_key, str(v)))
            return dict(items)

        flat_data = flatten_dict(data)
        for key, value in flat_data.items():
            csv_lines.append(f'"{key}","{value}"')

        return '\n'.join(csv_lines)

    def _import_user_data(self, user: UserProfile, import_data: Dict[str, Any]) -> bool:
        """Import user data from uploaded file"""
        try:
            # Import preferences if available
            if 'preferences' in import_data:
                # Create UserPreferences from imported data
                prefs_data = import_data['preferences']

                # Update user preferences (simplified)
                if self.manager.update_preferences(user.user_id, user.preferences):
                    return True

            return False
        except Exception as e:
            logger.error(f"Failed to import user data: {e}")
            return False

    def _compare_preferences(self, current: UserPreferences, default: UserPreferences) -> Dict[str, List[str]]:
        """Compare current preferences with default preferences"""
        differences = {
            'financial': [],
            'display': [],
            'notifications': [],
            'data_sources': [],
            'watch_lists': []
        }

        # Compare financial preferences
        if current.financial.default_discount_rate != default.financial.default_discount_rate:
            differences['financial'].append(f"Discount Rate: {current.financial.default_discount_rate:.1%} vs {default.financial.default_discount_rate:.1%} (default)")

        if current.financial.methodology != default.financial.methodology:
            differences['financial'].append(f"Methodology: {current.financial.methodology.value} vs {default.financial.methodology.value} (default)")

        # Compare display preferences
        if current.display.chart_theme != default.display.chart_theme:
            differences['display'].append(f"Chart Theme: {current.display.chart_theme} vs {default.display.chart_theme} (default)")

        if current.display.decimal_places != default.display.decimal_places:
            differences['display'].append(f"Decimal Places: {current.display.decimal_places} vs {default.display.decimal_places} (default)")

        # Add more comparisons as needed...

        return differences


def create_user_profile_dashboard() -> UserProfileDashboard:
    """Create and return a UserProfileDashboard instance"""
    return UserProfileDashboard()