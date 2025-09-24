"""
User Preferences UI Components

Streamlit interface components for managing user preferences
and customization options in the financial analysis application.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.user_preferences.user_profile import (
    UserProfile, UserPreferences, FinancialPreferences, DisplayPreferences,
    NotificationPreferences, DataSourcePreferences, WatchListPreferences,
    AnalysisMethodology, CurrencyPreference, RegionPreference
)
from core.user_preferences.preference_manager import get_preference_manager
from core.user_preferences.ui_preferences import (
    UIPreferences, ThemePreferences, LayoutPreferences, AccessibilityPreferences,
    ThemeMode, ChartStyle, LayoutMode, create_default_ui_preferences
)
from core.user_preferences.recommendation_engine import (
    get_recommendation_engine, RecommendationType, RecommendationPriority
)
from .preference_templates_ui import (
    display_template_selector, apply_template_to_user, display_template_comparison,
    display_custom_template_creator, display_template_management, display_template_search
)

logger = logging.getLogger(__name__)


class UserPreferencesUI:
    """Streamlit UI component for user preferences management"""

    def __init__(self):
        """Initialize the preferences UI"""
        self.manager = get_preference_manager()
        self.recommendation_engine = get_recommendation_engine()
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize session state variables"""
        if 'user_preferences_ui_initialized' not in st.session_state:
            st.session_state.user_preferences_ui_initialized = True
            st.session_state.current_user_profile = None
            st.session_state.preferences_modified = False
            st.session_state.ui_preferences = create_default_ui_preferences()

    def render_user_management_sidebar(self) -> None:
        """Render user management controls in sidebar"""
        with st.sidebar.expander("👤 User Profile", expanded=False):
            current_user = self.manager.get_current_user()

            if current_user:
                st.success(f"**Logged in as:** {current_user.username}")
                st.caption(f"User ID: {current_user.user_id}")

                if st.button("🚪 Logout", key="logout_btn"):
                    self.manager.clear_current_user()
                    st.session_state.current_user_profile = None
                    st.rerun()

                if st.button("⚙️ Edit Preferences", key="edit_prefs_btn"):
                    st.session_state.show_preferences_modal = True
                    st.rerun()

                if st.button("🎯 Restart Onboarding", key="restart_onboarding_btn"):
                    st.session_state.show_onboarding = True
                    st.session_state.onboarding_step = 0
                    st.session_state.onboarding_data = {}
                    st.rerun()

                if st.button("💡 View Recommendations", key="view_recommendations_btn"):
                    st.session_state.show_recommendations = True
                    st.rerun()

            else:
                st.info("No user logged in")
                self._render_user_login_controls()

    def _render_user_login_controls(self) -> None:
        """Render user login/registration controls"""
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Login")
            user_id = st.text_input("User ID", key="login_user_id")

            if st.button("Login", key="login_btn"):
                if user_id and self.manager.user_exists(user_id):
                    if self.manager.set_current_user(user_id):
                        st.success(f"Logged in as {user_id}")
                        st.rerun()
                    else:
                        st.error("Login failed")
                else:
                    st.error("User not found")

        with tab2:
            st.subheader("Register New User")
            new_user_id = st.text_input("User ID", key="register_user_id")
            new_username = st.text_input("Username", key="register_username")
            new_email = st.text_input("Email (optional)", key="register_email")

            if st.button("Register", key="register_btn"):
                if new_user_id and new_username:
                    try:
                        profile = self.manager.create_user(
                            new_user_id,
                            new_username,
                            new_email if new_email else None
                        )
                        if self.manager.set_current_user(new_user_id):
                            st.success(f"Registered and logged in as {new_username}")
                            st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.error("User ID and Username are required")

    def render_preferences_interface(self) -> None:
        """Render the main preferences interface"""
        current_user = self.manager.get_current_user()
        if not current_user:
            st.warning("Please log in to access preferences")
            return

        st.header("⚙️ User Preferences")
        st.caption(f"Customize your experience, {current_user.username}")

        # Create tabs for different preference categories
        tabs = st.tabs([
            "🎯 Templates",
            "💰 Financial",
            "🎨 Display",
            "🔔 Notifications",
            "📊 Data Sources",
            "📋 Watch Lists",
            "🎯 UI Theme",
            "📱 Layout",
            "♿ Accessibility"
        ])

        # Store original preferences for comparison
        original_prefs = current_user.preferences

        with tabs[0]:  # Templates
            self._render_template_preferences(current_user.user_id)

        with tabs[1]:  # Financial
            financial_prefs = self._render_financial_preferences(original_prefs.financial)

        with tabs[2]:  # Display
            display_prefs = self._render_display_preferences(original_prefs.display)

        with tabs[3]:  # Notifications
            notification_prefs = self._render_notification_preferences(original_prefs.notifications)

        with tabs[4]:  # Data Sources
            data_source_prefs = self._render_data_source_preferences(original_prefs.data_sources)

        with tabs[5]:  # Watch Lists
            watch_list_prefs = self._render_watch_list_preferences(original_prefs.watch_lists)

        with tabs[6]:  # UI Theme
            ui_theme_prefs = self._render_ui_theme_preferences()

        with tabs[7]:  # Layout
            ui_layout_prefs = self._render_ui_layout_preferences()

        with tabs[8]:  # Accessibility
            ui_accessibility_prefs = self._render_ui_accessibility_preferences()

        # Save preferences section
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            if st.button("💾 Save All Preferences", type="primary", use_container_width=True):
                # Create updated preferences
                updated_prefs = UserPreferences(
                    financial=financial_prefs,
                    display=display_prefs,
                    notifications=notification_prefs,
                    data_sources=data_source_prefs,
                    watch_lists=watch_list_prefs
                )

                # Update and save
                if self.manager.update_preferences(current_user.user_id, updated_prefs):
                    st.success("✅ Preferences saved successfully!")

                    # Apply UI preferences immediately
                    ui_prefs = UIPreferences(
                        theme=ui_theme_prefs,
                        layout=ui_layout_prefs,
                        accessibility=ui_accessibility_prefs
                    )
                    st.session_state.ui_preferences = ui_prefs
                    ui_prefs.apply_to_streamlit()

                    st.rerun()
                else:
                    st.error("❌ Failed to save preferences")

        with col3:
            if st.button("🔄 Reset to Defaults", use_container_width=True):
                if st.session_state.get('confirm_reset', False):
                    # Reset to defaults
                    default_prefs = UserPreferences()
                    if self.manager.update_preferences(current_user.user_id, default_prefs):
                        st.session_state.ui_preferences = create_default_ui_preferences()
                        st.success("✅ Preferences reset to defaults!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset preferences")
                    st.session_state.confirm_reset = False
                else:
                    st.session_state.confirm_reset = True
                    st.warning("⚠️ Click again to confirm reset")

    def _render_financial_preferences(self, current_prefs: FinancialPreferences) -> FinancialPreferences:
        """Render financial preferences section"""
        st.subheader("💰 Financial Analysis Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Default Valuation Parameters**")

            discount_rate = st.slider(
                "Default Discount Rate (%)",
                min_value=5.0,
                max_value=20.0,
                value=current_prefs.default_discount_rate * 100,
                step=0.5,
                help="Default cost of equity for DCF calculations"
            ) / 100

            terminal_growth_rate = st.slider(
                "Terminal Growth Rate (%)",
                min_value=0.0,
                max_value=5.0,
                value=current_prefs.default_terminal_growth_rate * 100,
                step=0.1,
                help="Long-term growth rate assumption"
            ) / 100

            projection_years = st.selectbox(
                "Projection Years",
                options=[3, 5, 7, 10, 15],
                index=[3, 5, 7, 10, 15].index(current_prefs.default_projection_years),
                help="Number of years to project for DCF analysis"
            )

        with col2:
            st.markdown("**Risk Parameters**")

            risk_free_rate = st.slider(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=current_prefs.risk_free_rate * 100,
                step=0.1,
                help="Government bond yield or similar risk-free rate"
            ) / 100

            market_risk_premium = st.slider(
                "Market Risk Premium (%)",
                min_value=3.0,
                max_value=10.0,
                value=current_prefs.market_risk_premium * 100,
                step=0.1,
                help="Expected market return above risk-free rate"
            ) / 100

            methodology = st.selectbox(
                "Analysis Methodology",
                options=[m.value for m in AnalysisMethodology],
                index=list(AnalysisMethodology).index(current_prefs.methodology),
                help="Overall approach to financial analysis"
            )

        st.markdown("**Regional and Currency Preferences**")
        col3, col4 = st.columns(2)

        with col3:
            primary_currency = st.selectbox(
                "Primary Currency",
                options=[c.value for c in CurrencyPreference],
                index=list(CurrencyPreference).index(current_prefs.primary_currency),
                help="Default currency for analysis"
            )

        with col4:
            preferred_regions = st.multiselect(
                "Preferred Regions",
                options=[r.value for r in RegionPreference],
                default=[r.value for r in current_prefs.preferred_regions],
                help="Regional markets of interest"
            )

        st.markdown("**Advanced Options**")
        col5, col6 = st.columns(2)

        with col5:
            include_beta_adjustment = st.checkbox(
                "Include Beta Adjustment",
                value=current_prefs.include_beta_adjustment,
                help="Adjust discount rate based on company beta"
            )

        with col6:
            use_country_risk_premium = st.checkbox(
                "Use Country Risk Premium",
                value=current_prefs.use_country_risk_premium,
                help="Add country-specific risk premium"
            )

        return FinancialPreferences(
            default_discount_rate=discount_rate,
            default_terminal_growth_rate=terminal_growth_rate,
            default_projection_years=projection_years,
            risk_free_rate=risk_free_rate,
            market_risk_premium=market_risk_premium,
            methodology=AnalysisMethodology(methodology),
            primary_currency=CurrencyPreference(primary_currency),
            preferred_regions=[RegionPreference(r) for r in preferred_regions],
            include_beta_adjustment=include_beta_adjustment,
            use_country_risk_premium=use_country_risk_premium
        )

    def _render_display_preferences(self, current_prefs: DisplayPreferences) -> DisplayPreferences:
        """Render display preferences section"""
        st.subheader("🎨 Display Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Number Formatting**")

            decimal_places = st.selectbox(
                "Decimal Places",
                options=[0, 1, 2, 3, 4],
                index=current_prefs.decimal_places,
                help="Number of decimal places for financial figures"
            )

            use_thousands_separator = st.checkbox(
                "Use Thousands Separator",
                value=current_prefs.use_thousands_separator,
                help="Display numbers with comma separators (e.g., 1,000)"
            )

            percentage_decimal_places = st.selectbox(
                "Percentage Decimal Places",
                options=[0, 1, 2, 3],
                index=current_prefs.percentage_decimal_places,
                help="Decimal places for percentages"
            )

        with col2:
            st.markdown("**Chart Preferences**")

            chart_theme = st.selectbox(
                "Chart Theme",
                options=["plotly", "seaborn", "matplotlib"],
                index=["plotly", "seaborn", "matplotlib"].index(current_prefs.chart_theme),
                help="Default charting library theme"
            )

            default_chart_type = st.selectbox(
                "Default Chart Type",
                options=["line", "bar", "candlestick", "area"],
                index=["line", "bar", "candlestick", "area"].index(current_prefs.default_chart_type),
                help="Default chart type for financial data"
            )

            show_grid = st.checkbox(
                "Show Grid Lines",
                value=current_prefs.show_grid,
                help="Display grid lines on charts"
            )

        st.markdown("**Color Preferences**")
        col3, col4, col5 = st.columns(3)

        with col3:
            positive_color = st.color_picker(
                "Positive Values",
                value=current_prefs.positive_color,
                help="Color for positive financial values"
            )

        with col4:
            negative_color = st.color_picker(
                "Negative Values",
                value=current_prefs.negative_color,
                help="Color for negative financial values"
            )

        with col5:
            neutral_color = st.color_picker(
                "Neutral Values",
                value=current_prefs.neutral_color,
                help="Color for neutral or informational values"
            )

        return DisplayPreferences(
            decimal_places=decimal_places,
            use_thousands_separator=use_thousands_separator,
            percentage_decimal_places=percentage_decimal_places,
            chart_theme=chart_theme,
            default_chart_type=default_chart_type,
            show_grid=show_grid,
            positive_color=positive_color,
            negative_color=negative_color,
            neutral_color=neutral_color
        )

    def _render_notification_preferences(self, current_prefs: NotificationPreferences) -> NotificationPreferences:
        """Render notification preferences section"""
        st.subheader("🔔 Notification Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**In-App Notifications**")

            show_calculation_warnings = st.checkbox(
                "Calculation Warnings",
                value=current_prefs.show_calculation_warnings,
                help="Show warnings about calculation accuracy"
            )

            show_data_quality_alerts = st.checkbox(
                "Data Quality Alerts",
                value=current_prefs.show_data_quality_alerts,
                help="Alert when data quality issues are detected"
            )

            show_performance_tips = st.checkbox(
                "Performance Tips",
                value=current_prefs.show_performance_tips,
                help="Show tips for improving application performance"
            )

        with col2:
            st.markdown("**Alert Thresholds**")

            price_change_threshold = st.slider(
                "Price Change Alert (%)",
                min_value=1.0,
                max_value=20.0,
                value=current_prefs.price_change_threshold * 100,
                step=0.5,
                help="Alert when stock price changes by this percentage"
            ) / 100

            valuation_change_threshold = st.slider(
                "Valuation Change Alert (%)",
                min_value=5.0,
                max_value=50.0,
                value=current_prefs.valuation_change_threshold * 100,
                step=1.0,
                help="Alert when calculated valuation changes significantly"
            ) / 100

        return NotificationPreferences(
            show_calculation_warnings=show_calculation_warnings,
            show_data_quality_alerts=show_data_quality_alerts,
            show_performance_tips=show_performance_tips,
            price_change_threshold=price_change_threshold,
            valuation_change_threshold=valuation_change_threshold
        )

    def _render_data_source_preferences(self, current_prefs: DataSourcePreferences) -> DataSourcePreferences:
        """Render data source preferences section"""
        st.subheader("📊 Data Source Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Data Source Priority**")

            prefer_excel_over_api = st.checkbox(
                "Prefer Excel Over API",
                value=current_prefs.prefer_excel_over_api,
                help="Use local Excel files when available, fallback to API"
            )

            auto_refresh_data = st.checkbox(
                "Auto-Refresh Data",
                value=current_prefs.auto_refresh_data,
                help="Automatically refresh data periodically"
            )

            cache_duration_hours = st.slider(
                "Cache Duration (hours)",
                min_value=1,
                max_value=168,  # 1 week
                value=current_prefs.cache_duration_hours,
                help="How long to cache API data"
            )

        with col2:
            st.markdown("**API Configuration**")

            api_timeout_seconds = st.slider(
                "API Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=current_prefs.api_timeout_seconds,
                help="Timeout for API requests"
            )

            max_retry_attempts = st.slider(
                "Max Retry Attempts",
                min_value=1,
                max_value=5,
                value=current_prefs.max_retry_attempts,
                help="Number of times to retry failed API calls"
            )

        return DataSourcePreferences(
            prefer_excel_over_api=prefer_excel_over_api,
            auto_refresh_data=auto_refresh_data,
            cache_duration_hours=cache_duration_hours,
            api_timeout_seconds=api_timeout_seconds,
            max_retry_attempts=max_retry_attempts
        )

    def _render_watch_list_preferences(self, current_prefs: WatchListPreferences) -> WatchListPreferences:
        """Render watch list preferences section"""
        st.subheader("📋 Watch List Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**List Configuration**")

            max_companies_per_list = st.slider(
                "Max Companies per List",
                min_value=10,
                max_value=100,
                value=current_prefs.max_companies_per_list,
                help="Maximum number of companies in a watch list"
            )

            auto_sort_by = st.selectbox(
                "Auto Sort By",
                options=["market_cap", "alphabetical", "performance", "last_updated"],
                index=["market_cap", "alphabetical", "performance", "last_updated"].index(current_prefs.auto_sort_by),
                help="Default sorting for watch lists"
            )

        with col2:
            st.markdown("**Update Settings**")

            auto_refresh_enabled = st.checkbox(
                "Auto-Refresh Enabled",
                value=current_prefs.auto_refresh_enabled,
                help="Automatically refresh watch list data"
            )

            if auto_refresh_enabled:
                refresh_interval_minutes = st.slider(
                    "Refresh Interval (minutes)",
                    min_value=5,
                    max_value=240,  # 4 hours
                    value=current_prefs.refresh_interval_minutes,
                    help="How often to refresh watch list data"
                )
            else:
                refresh_interval_minutes = current_prefs.refresh_interval_minutes

        return WatchListPreferences(
            max_companies_per_list=max_companies_per_list,
            auto_sort_by=auto_sort_by,
            auto_refresh_enabled=auto_refresh_enabled,
            refresh_interval_minutes=refresh_interval_minutes
        )

    def _render_ui_theme_preferences(self) -> ThemePreferences:
        """Render UI theme preferences"""
        st.subheader("🎨 Theme Preferences")

        # Theme customization tabs
        basic_tab, advanced_tab = st.tabs(["🎨 Basic Themes", "🛠️ Advanced Customization"])

        with basic_tab:
            current_ui_prefs = st.session_state.get('ui_preferences', create_default_ui_preferences())
            current_theme = current_ui_prefs.theme

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Theme Mode**")

                theme_mode = st.selectbox(
                    "Theme Mode",
                    options=[mode.value for mode in ThemeMode],
                    index=list(ThemeMode).index(current_theme.mode),
                    help="Application color theme"
                )

                chart_style = st.selectbox(
                    "Chart Style",
                    options=[style.value for style in ChartStyle],
                    index=list(ChartStyle).index(current_theme.chart_style),
                    help="Chart visual style"
                )

            with col2:
                st.markdown("**Typography**")

                font_family = st.selectbox(
                    "Font Family",
                    options=[
                        "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                        "Arial, sans-serif",
                        "Helvetica, sans-serif",
                        "Georgia, serif",
                        "Times New Roman, serif"
                    ],
                    index=0,
                    help="Primary font family"
                )

                font_size_base = st.slider(
                    "Base Font Size",
                    min_value=12,
                    max_value=18,
                    value=current_theme.font_size_base,
                    help="Base font size in pixels"
                )

            # Quick theme preset selection
            st.markdown("**Quick Theme Presets**")

            preset_cols = st.columns(4)
            preset_themes = [
                ("Professional", "🏢", "#1E40AF"),
                ("Financial", "💰", "#059669"),
                ("Creative", "🎨", "#7C3AED"),
                ("Minimal", "⚪", "#374151")
            ]

            for i, (name, icon, color) in enumerate(preset_themes):
                with preset_cols[i]:
                    if st.button(f"{icon} {name}", key=f"preset_{name.lower()}", use_container_width=True):
                        st.info(f"Applied {name} theme preset")

        with advanced_tab:
            st.info("🚀 **Advanced Theme Customization**")
            st.markdown("""
            Create and customize themes with:
            - Custom color palettes with gradient support
            - Typography options with Google Fonts integration
            - Personalized branding (logos, company name, tagline)
            - Auto-switching based on time or system preference
            - Theme sharing and community themes
            - Real-time preview functionality
            """)

            # Button to open advanced customization
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎨 Open Advanced Theme Designer", type="primary", use_container_width=True):
                    # Set session state to indicate user wants advanced customization
                    st.session_state.show_advanced_themes = True
                    st.info("📝 **Coming Up:** Advanced theme customization interface will open.")
                    st.markdown("""
                    The advanced theme designer includes:

                    **🎨 Create Theme Tab:**
                    - Custom color palette creator with preset options
                    - Typography selection with Google Fonts integration
                    - Gradient color settings
                    - Branding options (logo, company name, tagline)
                    - Auto-switching settings for light/dark modes
                    - Real-time preview functionality

                    **📚 Theme Gallery Tab:**
                    - Browse all available themes
                    - Search and filter by category
                    - Apply themes instantly
                    - Generate default theme collection

                    **🔧 Edit Theme Tab:**
                    - Modify existing themes
                    - Duplicate themes for customization
                    - Update metadata and settings
                    - Delete unwanted themes

                    **🌍 Community Tab:**
                    - Import themes from JSON
                    - Export themes for sharing
                    - Future: Browse community-created themes

                    **⚙️ Settings Tab:**
                    - Global auto-switch settings
                    - Performance preferences
                    - Theme management tools
                    - Backup and restore functionality
                    """)

            # Show current advanced theme if any
            if hasattr(st.session_state, 'current_advanced_theme'):
                st.markdown("**Current Advanced Theme:**")
                theme_info = st.session_state.current_advanced_theme
                st.markdown(f"- **Name:** {theme_info.get('name', 'Custom Theme')}")
                st.markdown(f"- **Author:** {theme_info.get('author', 'Unknown')}")
                st.markdown(f"- **Category:** {theme_info.get('category', 'custom')}")

        return ThemePreferences(
            mode=ThemeMode(theme_mode),
            chart_style=ChartStyle(chart_style),
            font_family=font_family,
            font_size_base=font_size_base
        )

    def _render_ui_layout_preferences(self) -> LayoutPreferences:
        """Render UI layout preferences"""
        st.subheader("📱 Layout Preferences")

        current_ui_prefs = st.session_state.get('ui_preferences', create_default_ui_preferences())
        current_layout = current_ui_prefs.layout

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Layout Configuration**")

            layout_mode = st.selectbox(
                "Layout Mode",
                options=[mode.value for mode in LayoutMode],
                index=list(LayoutMode).index(current_layout.mode),
                help="Overall layout density"
            )

            sidebar_default_expanded = st.checkbox(
                "Sidebar Expanded by Default",
                value=current_layout.sidebar_default_expanded,
                help="Show sidebar expanded when app loads"
            )

            enable_sticky_headers = st.checkbox(
                "Sticky Headers",
                value=current_layout.enable_sticky_headers,
                help="Keep headers visible when scrolling"
            )

        with col2:
            st.markdown("**Table and Chart Settings**")

            rows_per_page = st.slider(
                "Table Rows per Page",
                min_value=10,
                max_value=100,
                value=current_layout.rows_per_page,
                help="Number of rows to display in tables"
            )

            default_chart_height = st.slider(
                "Default Chart Height",
                min_value=300,
                max_value=800,
                value=current_layout.default_chart_height,
                help="Default height for charts in pixels"
            )

        return LayoutPreferences(
            mode=LayoutMode(layout_mode),
            sidebar_default_expanded=sidebar_default_expanded,
            enable_sticky_headers=enable_sticky_headers,
            rows_per_page=rows_per_page,
            default_chart_height=default_chart_height
        )

    def _render_ui_accessibility_preferences(self) -> AccessibilityPreferences:
        """Render UI accessibility preferences"""
        st.subheader("♿ Accessibility Preferences")

        current_ui_prefs = st.session_state.get('ui_preferences', create_default_ui_preferences())
        current_accessibility = current_ui_prefs.accessibility

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Visual Accessibility**")

            high_contrast_mode = st.checkbox(
                "High Contrast Mode",
                value=current_accessibility.high_contrast_mode,
                help="Use high contrast colors for better visibility"
            )

            large_text_mode = st.checkbox(
                "Large Text Mode",
                value=current_accessibility.large_text_mode,
                help="Increase text size throughout the application"
            )

            reduce_motion = st.checkbox(
                "Reduce Motion",
                value=current_accessibility.reduce_motion,
                help="Minimize animations and transitions"
            )

        with col2:
            st.markdown("**Interaction Preferences**")

            show_tooltips = st.checkbox(
                "Show Tooltips",
                value=current_accessibility.show_tooltips,
                help="Display helpful tooltips on hover"
            )

            show_help_text = st.checkbox(
                "Show Help Text",
                value=current_accessibility.show_help_text,
                help="Display explanatory text for features"
            )

            beginner_mode = st.checkbox(
                "Beginner Mode",
                value=current_accessibility.beginner_mode,
                help="Show additional guidance for new users"
            )

        return AccessibilityPreferences(
            high_contrast_mode=high_contrast_mode,
            large_text_mode=large_text_mode,
            reduce_motion=reduce_motion,
            show_tooltips=show_tooltips,
            show_help_text=show_help_text,
            beginner_mode=beginner_mode
        )

    def render_user_analytics(self) -> None:
        """Render user analytics and statistics"""
        current_user = self.manager.get_current_user()
        if not current_user:
            st.warning("Please log in to view analytics")
            return

        st.header("📊 User Analytics")

        analytics = self.manager.get_user_analytics(current_user.user_id)
        if not analytics:
            st.error("Failed to load analytics")
            return

        # Display analytics in metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Analyses",
                analytics['total_analyses'],
                help="Number of financial analyses performed"
            )

        with col2:
            st.metric(
                "Login Count",
                analytics['login_count'],
                help="Number of times logged in"
            )

        with col3:
            st.metric(
                "Favorite Companies",
                analytics['favorite_companies_count'],
                help="Number of companies in favorites"
            )

        with col4:
            st.metric(
                "Recent Searches",
                analytics['recent_searches_count'],
                help="Number of recent search terms"
            )

        # Recent activity
        if current_user.recent_searches:
            st.subheader("Recent Searches")
            for i, search in enumerate(current_user.recent_searches[:5]):
                st.text(f"{i+1}. {search}")

        if current_user.favorite_companies:
            st.subheader("Favorite Companies")
            for company in current_user.favorite_companies:
                st.text(f"• {company}")

    def render_recommendations_interface(self) -> None:
        """Render the smart recommendations interface"""
        current_user = self.manager.get_current_user()
        if not current_user:
            st.warning("Please log in to view recommendations")
            return

        st.header("💡 Smart Recommendations")
        st.caption(f"Personalized suggestions for {current_user.username}")

        # Generate fresh recommendations button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Generate New Recommendations", type="primary", use_container_width=True):
                with st.spinner("Analyzing your patterns and generating recommendations..."):
                    recommendations = self.recommendation_engine.generate_recommendations(current_user.user_id)
                    if recommendations:
                        st.success(f"Generated {len(recommendations)} new recommendations!")
                        st.rerun()
                    else:
                        st.warning("No new recommendations available at this time.")

        # Get current recommendations
        recommendations = self.recommendation_engine.get_user_recommendations(current_user.user_id)

        if not recommendations:
            st.info("No recommendations available. Generate some by using the app and analyzing companies!")
            return

        # Group recommendations by type
        rec_by_type = {}
        for rec in recommendations:
            rec_type = rec.type.value
            if rec_type not in rec_by_type:
                rec_by_type[rec_type] = []
            rec_by_type[rec_type].append(rec)

        # Create tabs for different recommendation types
        tab_names = []
        tab_emojis = {
            "financial_parameters": "💰",
            "company_suggestions": "🏢",
            "analysis_methodology": "📊",
            "ui_preferences": "🎨",
            "workflow_optimization": "⚡"
        }

        for rec_type in rec_by_type.keys():
            emoji = tab_emojis.get(rec_type, "💡")
            count = len(rec_by_type[rec_type])
            tab_names.append(f"{emoji} {rec_type.replace('_', ' ').title()} ({count})")

        if tab_names:
            tabs = st.tabs(tab_names)

            for i, (rec_type, recs) in enumerate(rec_by_type.items()):
                with tabs[i]:
                    st.subheader(f"{tab_emojis.get(rec_type, '💡')} {rec_type.replace('_', ' ').title()} Recommendations")

                    for rec in recs:
                        self._render_recommendation_card(rec)

    def _render_recommendation_card(self, rec) -> None:
        """Render a single recommendation card"""
        # Priority styling
        priority_colors = {
            "low": "#E5E7EB",
            "medium": "#FEF3C7",
            "high": "#FEE2E2",
            "critical": "#FECACA"
        }

        priority_icons = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🔥",
            "critical": "🚨"
        }

        with st.container():
            # Card header
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{priority_icons.get(rec.priority.value, '💡')} {rec.title}**")

            with col2:
                confidence_color = "🟢" if rec.confidence_score > 0.8 else "🟡" if rec.confidence_score > 0.6 else "🔴"
                st.caption(f"Confidence: {confidence_color} {rec.confidence_score:.1%}")

            with col3:
                priority_label = rec.priority.value.upper()
                st.caption(f"Priority: **{priority_label}**")

            # Description
            st.markdown(rec.description)

            # Current vs Suggested (if applicable)
            if rec.current_value is not None and rec.suggested_value is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Current:** `{rec.current_value}`")
                with col2:
                    st.markdown(f"**Suggested:** `{rec.suggested_value}`")

            # Reasoning
            if rec.reasoning:
                with st.expander("💭 Why this recommendation?", expanded=False):
                    st.markdown(rec.reasoning)
                    if rec.category:
                        st.caption(f"Category: {rec.category}")
                    if rec.tags:
                        st.caption(f"Tags: {', '.join(rec.tags)}")

            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("✅ Apply", key=f"apply_{rec.recommendation_id}", use_container_width=True):
                    if self.recommendation_engine.apply_recommendation(rec.user_id, rec.recommendation_id):
                        st.success("Applied successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to apply recommendation")

            with col2:
                if st.button("❌ Dismiss", key=f"dismiss_{rec.recommendation_id}", use_container_width=True):
                    dismiss_reason = st.text_input(
                        "Reason (optional):",
                        key=f"dismiss_reason_{rec.recommendation_id}",
                        placeholder="Why are you dismissing this?"
                    )
                    if self.recommendation_engine.dismiss_recommendation(
                        rec.user_id,
                        rec.recommendation_id,
                        dismiss_reason
                    ):
                        st.success("Recommendation dismissed")
                        st.rerun()
                    else:
                        st.error("Failed to dismiss recommendation")

            with col3:
                # Feedback section
                with st.expander("📝 Provide Feedback", expanded=False):
                    feedback = st.text_area(
                        "Your feedback on this recommendation:",
                        key=f"feedback_{rec.recommendation_id}",
                        placeholder="How useful is this recommendation? Any suggestions?"
                    )
                    if st.button("Submit Feedback", key=f"submit_feedback_{rec.recommendation_id}"):
                        # Store feedback for learning
                        st.success("Thank you for your feedback!")

            # A/B Testing info (for debugging/transparency)
            if rec.test_group and rec.variant:
                st.caption(f"🧪 A/B Test: {rec.test_group} - {rec.variant}")

            st.divider()

    def render_behavior_analytics(self) -> None:
        """Render user behavior analytics and patterns"""
        current_user = self.manager.get_current_user()
        if not current_user:
            st.warning("Please log in to view behavior analytics")
            return

        st.header("📈 Behavior Analytics")
        st.caption(f"Analysis patterns and insights for {current_user.username}")

        # Analyze behavior patterns
        with st.spinner("Analyzing your behavior patterns..."):
            patterns = self.recommendation_engine.analyze_user_behavior(current_user.user_id)

        if not patterns:
            st.info("Not enough usage data yet. Use the app more to see behavior insights!")
            return

        # Display patterns in cards
        for pattern in patterns:
            with st.expander(f"📊 {pattern.pattern_type.replace('_', ' ').title()}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Frequency", f"{pattern.frequency:.1f}/day")

                with col2:
                    st.metric("Success Rate", f"{pattern.success_rate:.1%}")

                with col3:
                    trend_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
                    st.metric("Trend", f"{trend_emoji.get(pattern.trend, '➡️')} {pattern.trend}")

                # Pattern-specific details
                if pattern.pattern_type == "analysis_preferences":
                    if pattern.common_analysis_types:
                        st.markdown("**Most Used Analysis Types:**")
                        for analysis_type in pattern.common_analysis_types[:3]:
                            st.markdown(f"• {analysis_type.upper()}")

                elif pattern.pattern_type == "company_preferences":
                    if pattern.preferred_companies:
                        st.markdown("**Frequently Analyzed Companies:**")
                        for company in pattern.preferred_companies[:5]:
                            st.markdown(f"• {company}")

                elif pattern.pattern_type == "parameter_usage":
                    if pattern.typical_parameters:
                        st.markdown("**Typical Parameters:**")
                        for param, value in list(pattern.typical_parameters.items())[:3]:
                            st.markdown(f"• {param}: {value}")

                if pattern.average_session_duration > 0:
                    st.markdown(f"**Average Session Duration:** {pattern.average_session_duration/60:.1f} minutes")

    def _render_template_preferences(self, user_id: str) -> None:
        """Render preference templates interface"""
        st.markdown("""
        Choose from predefined templates to quickly configure your preferences,
        or create custom templates to save your preferred settings.
        """)

        # Template action selector
        template_action = st.radio(
            "What would you like to do?",
            ["Apply Template", "Compare Templates", "Search Templates", "Create Custom", "Manage Templates"],
            horizontal=True,
            help="Choose an action for working with preference templates"
        )

        st.divider()

        if template_action == "Apply Template":
            selected_template_id = display_template_selector()
            if selected_template_id:
                if st.button("Apply Selected Template", type="primary"):
                    success = apply_template_to_user(selected_template_id, user_id)
                    if success:
                        st.balloons()
                        st.rerun()

        elif template_action == "Compare Templates":
            display_template_comparison()

        elif template_action == "Search Templates":
            selected_template_id = display_template_search()
            if selected_template_id:
                if st.button("Apply Found Template", type="primary"):
                    success = apply_template_to_user(selected_template_id, user_id)
                    if success:
                        st.balloons()
                        st.rerun()

        elif template_action == "Create Custom":
            display_custom_template_creator()

        elif template_action == "Manage Templates":
            display_template_management()


def create_user_preferences_ui() -> UserPreferencesUI:
    """Create and return a UserPreferencesUI instance"""
    return UserPreferencesUI()