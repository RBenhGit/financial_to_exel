"""
User Onboarding Flow for Financial Analysis Application

Multi-step guided onboarding experience for new users to set up their
initial preferences, including financial methodology, regional focus,
and display preferences.
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

logger = logging.getLogger(__name__)


class UserOnboardingFlow:
    """Multi-step onboarding wizard for new users"""

    def __init__(self):
        """Initialize the onboarding flow"""
        self.manager = get_preference_manager()
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize session state variables for onboarding"""
        if 'onboarding_initialized' not in st.session_state:
            st.session_state.onboarding_initialized = True
            st.session_state.onboarding_step = 0
            st.session_state.onboarding_data = {}
            st.session_state.show_onboarding = False
            st.session_state.onboarding_completed = False
            st.session_state.skip_onboarding = False

    def _map_region_to_enum(self, region_display: str) -> str:
        """Map display region names to enum values"""
        mapping = {
            "North America": "north_america",
            "Europe": "europe",
            "Asia Pacific": "asia_pacific",
            "Emerging Markets": "emerging_markets",
            "Israel": "israel",
            "Global": "global"
        }
        return mapping.get(region_display, region_display.lower().replace(' ', '_'))

    def should_show_onboarding(self) -> bool:
        """Check if onboarding should be shown to current user"""
        # Safety mechanism: Auto-skip after too many refreshes
        refresh_count = st.session_state.get('onboarding_refresh_count', 0)
        if refresh_count > 10:  # User has refreshed more than 10 times
            st.session_state.skip_onboarding = True
            st.warning("⚠️ Onboarding automatically skipped after multiple refreshes. You can access setup later in the sidebar.")
            return False

        # Increment refresh counter
        st.session_state.onboarding_refresh_count = refresh_count + 1

        current_user = self.manager.get_current_user()

        # Show onboarding if:
        # 1. No user is logged in and onboarding hasn't been skipped
        # 2. User exists but hasn't completed onboarding
        if not current_user:
            return not st.session_state.get('skip_onboarding', False)

        # Check if user has completed onboarding
        return not getattr(current_user, 'onboarding_completed', False)

    def render_onboarding_flow(self) -> bool:
        """
        Render the complete onboarding flow

        Returns:
            bool: True if onboarding is complete, False if still in progress
        """
        if not self.should_show_onboarding():
            return True

        st.markdown("""
        <style>
        .onboarding-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        }
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        .step {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 10px;
            font-weight: bold;
        }
        .step.active {
            background-color: #4CAF50;
            color: white;
        }
        .step.completed {
            background-color: #2196F3;
            color: white;
        }
        .step.upcoming {
            background-color: #f0f0f0;
            color: #666;
        }
        </style>
        """, unsafe_allow_html=True)

        # Onboarding container
        with st.container():
            st.markdown('<div class="onboarding-container">', unsafe_allow_html=True)

            # Header
            st.markdown("# 🎯 Welcome to Financial Analysis Pro!")
            st.markdown("Let's set up your personalized analysis experience in just a few steps.")

            # Step indicator
            self._render_step_indicator()

            st.markdown('</div>', unsafe_allow_html=True)

        # Current step content
        current_step = st.session_state.get('onboarding_step', 0)

        if current_step == 0:
            completed = self._render_welcome_step()
        elif current_step == 1:
            completed = self._render_experience_step()
        elif current_step == 2:
            completed = self._render_financial_methodology_step()
        elif current_step == 3:
            completed = self._render_regional_preferences_step()
        elif current_step == 4:
            completed = self._render_display_preferences_step()
        elif current_step == 5:
            completed = self._render_final_setup_step()
        else:
            completed = True

        return completed

    def _render_step_indicator(self) -> None:
        """Render the step progress indicator"""
        current_step = st.session_state.get('onboarding_step', 0)
        total_steps = 6

        cols = st.columns(total_steps)

        for i in range(total_steps):
            with cols[i]:
                if i < current_step:
                    st.markdown(f'<div class="step completed">{i+1}</div>', unsafe_allow_html=True)
                elif i == current_step:
                    st.markdown(f'<div class="step active">{i+1}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="step upcoming">{i+1}</div>', unsafe_allow_html=True)

    def _render_welcome_step(self) -> bool:
        """Render welcome and introduction step"""
        st.header("👋 Welcome!")

        st.markdown("""
        **Financial Analysis Pro** helps you make informed investment decisions through:

        - 📊 **Free Cash Flow (FCF) Analysis** - Understand a company's cash generation
        - 💰 **Discounted Cash Flow (DCF) Valuation** - Calculate intrinsic value
        - 📈 **Dividend Discount Model (DDM)** - Value dividend-paying stocks
        - 📋 **Price-to-Book (P/B) Analysis** - Compare market vs book value
        - 🎯 **Risk Analysis & Scenario Modeling** - Assess investment risks

        This quick setup will customize the tool to your preferences and experience level.
        """)

        st.info("💡 **Tip:** You can always change these settings later in your user preferences.")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🚀 Let's Get Started!", type="primary", use_container_width=True):
                st.session_state.onboarding_step = 1
                st.rerun()

        # Skip option
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⏭️ Skip Setup (Use Defaults)", use_container_width=True):
                st.session_state.skip_onboarding = True
                return True

        return False

    def _render_experience_step(self) -> bool:
        """Render investment experience level step"""
        st.header("📚 Your Investment Experience")
        st.markdown("Help us tailor the interface to your experience level:")

        experience_level = st.radio(
            "How would you describe your investment experience?",
            options=[
                "Beginner - New to financial analysis",
                "Intermediate - Some experience with valuation",
                "Advanced - Experienced investor/analyst",
                "Professional - Financial industry professional"
            ],
            key="experience_level"
        )

        # Show appropriate features based on experience
        if "Beginner" in experience_level:
            st.success("""
            **Perfect!** We'll enable:
            - 📚 Guided tutorials and explanations
            - 💡 Helpful tooltips throughout the app
            - 🎯 Simplified interface with key metrics highlighted
            - 📖 Educational content for financial concepts
            """)
            st.session_state.onboarding_data['beginner_mode'] = True
            st.session_state.onboarding_data['show_help_text'] = True
            st.session_state.onboarding_data['show_tooltips'] = True

        elif "Intermediate" in experience_level:
            st.info("""
            **Great!** We'll provide:
            - ⚖️ Balanced interface with optional advanced features
            - 💡 Contextual help when needed
            - 📊 Standard financial ratios and metrics
            - 🔍 Optional detailed analysis sections
            """)
            st.session_state.onboarding_data['beginner_mode'] = False
            st.session_state.onboarding_data['show_help_text'] = True
            st.session_state.onboarding_data['show_tooltips'] = True

        elif "Advanced" in experience_level:
            st.info("""
            **Excellent!** You'll get:
            - 🚀 Full feature access from the start
            - 📈 Advanced analytics and ratios
            - 🔧 Customizable parameters and assumptions
            - 📊 Professional-grade charts and exports
            """)
            st.session_state.onboarding_data['beginner_mode'] = False
            st.session_state.onboarding_data['show_help_text'] = False
            st.session_state.onboarding_data['show_tooltips'] = False

        else:  # Professional
            st.success("""
            **Outstanding!** Professional mode includes:
            - 🏢 Enterprise-level features and customization
            - 📊 Advanced risk analysis and scenario modeling
            - 🔬 Detailed sensitivity analysis tools
            - 📋 Batch processing and automation features
            """)
            st.session_state.onboarding_data['beginner_mode'] = False
            st.session_state.onboarding_data['show_help_text'] = False
            st.session_state.onboarding_data['show_tooltips'] = False

        st.session_state.onboarding_data['experience_level'] = experience_level

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("⬅️ Back", key="exp_back"):
                st.session_state.onboarding_step = 0
                st.rerun()

        with col3:
            if st.button("Next ➡️", type="primary", key="exp_next"):
                st.session_state.onboarding_step = 2
                st.rerun()

        return False

    def _render_financial_methodology_step(self) -> bool:
        """Render financial analysis methodology preferences"""
        st.header("💰 Financial Analysis Preferences")
        st.markdown("Configure your default analysis parameters:")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Analysis Approach")

            methodology = st.selectbox(
                "Preferred Analysis Methodology",
                options=["Conservative", "Moderate", "Aggressive", "Custom"],
                help="This affects default assumptions for growth rates and risk parameters"
            )

            if methodology == "Conservative":
                st.info("📉 Lower growth assumptions, higher discount rates, margin of safety focus")
                default_discount = 12.0
                default_growth = 2.0

            elif methodology == "Moderate":
                st.info("⚖️ Balanced assumptions based on historical averages")
                default_discount = 10.0
                default_growth = 2.5

            elif methodology == "Aggressive":
                st.info("📈 Higher growth assumptions, optimistic scenarios")
                default_discount = 8.0
                default_growth = 3.0

            else:  # Custom
                st.info("🔧 You'll set custom parameters for each analysis")
                default_discount = 10.0
                default_growth = 2.5

            projection_years = st.selectbox(
                "Default Projection Period",
                options=[5, 7, 10, 15],
                index=1,
                help="Number of years to project for DCF analysis"
            )

        with col2:
            st.subheader("🌍 Regional Focus")

            primary_currency = st.selectbox(
                "Primary Currency",
                options=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "ILS"],
                help="Default currency for analysis and display"
            )

            regions = st.multiselect(
                "Markets of Interest",
                options=[
                    "North America", "Europe", "Asia Pacific",
                    "Emerging Markets", "Israel", "Global"
                ],
                default=["North America"],
                help="Select the regional markets you're most interested in"
            )

            st.subheader("⚙️ Risk Parameters")

            use_beta_adjustment = st.checkbox(
                "Include Beta Adjustment",
                value=True,
                help="Adjust discount rate based on company beta (systematic risk)"
            )

            country_risk = st.checkbox(
                "Use Country Risk Premium",
                value=False,
                help="Add country-specific risk premium for international investments"
            )

        # Store preferences
        st.session_state.onboarding_data.update({
            'methodology': methodology.lower(),
            'default_discount_rate': default_discount / 100,
            'default_terminal_growth_rate': default_growth / 100,
            'projection_years': projection_years,
            'primary_currency': primary_currency,
            'preferred_regions': [self._map_region_to_enum(r) for r in regions],
            'use_beta_adjustment': use_beta_adjustment,
            'use_country_risk_premium': country_risk
        })

        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("⬅️ Back", key="fin_back"):
                st.session_state.onboarding_step = 1
                st.rerun()

        with col3:
            if st.button("Next ➡️", type="primary", key="fin_next"):
                st.session_state.onboarding_step = 3
                st.rerun()

        return False

    def _render_regional_preferences_step(self) -> bool:
        """Render regional and data source preferences"""
        st.header("🌍 Data & Regional Preferences")
        st.markdown("Configure how you want to access and view financial data:")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Data Sources")

            excel_preference = st.radio(
                "Data Source Priority",
                options=[
                    "Prefer Excel files (when available)",
                    "Prefer API data (real-time)",
                    "Balanced approach"
                ],
                help="Choose how to prioritize local Excel files vs real-time API data"
            )

            auto_refresh = st.checkbox(
                "Auto-refresh data",
                value=True,
                help="Automatically update data during analysis sessions"
            )

            cache_duration = st.selectbox(
                "Data cache duration",
                options=["1 hour", "4 hours", "24 hours", "1 week"],
                index=2,
                help="How long to cache API data before refreshing"
            )

        with col2:
            st.subheader("🔔 Notifications")

            calculation_warnings = st.checkbox(
                "Show calculation warnings",
                value=True,
                help="Alert when data quality might affect accuracy"
            )

            performance_tips = st.checkbox(
                "Show performance tips",
                value=st.session_state.onboarding_data.get('beginner_mode', True),
                help="Display tips for improving analysis workflow"
            )

            price_alerts = st.slider(
                "Price change alert threshold (%)",
                min_value=1.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="Alert when stock prices change by this percentage"
            )

        # Store preferences
        cache_hours = {"1 hour": 1, "4 hours": 4, "24 hours": 24, "1 week": 168}[cache_duration]

        st.session_state.onboarding_data.update({
            'prefer_excel_over_api': "Excel" in excel_preference,
            'auto_refresh_data': auto_refresh,
            'cache_duration_hours': cache_hours,
            'show_calculation_warnings': calculation_warnings,
            'show_performance_tips': performance_tips,
            'price_change_threshold': price_alerts / 100
        })

        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("⬅️ Back", key="reg_back"):
                st.session_state.onboarding_step = 2
                st.rerun()

        with col3:
            if st.button("Next ➡️", type="primary", key="reg_next"):
                st.session_state.onboarding_step = 4
                st.rerun()

        return False

    def _render_display_preferences_step(self) -> bool:
        """Render display and UI preferences"""
        st.header("🎨 Display Preferences")
        st.markdown("Customize how information is displayed:")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔢 Number Formatting")

            decimal_places = st.selectbox(
                "Decimal places for financial figures",
                options=[0, 1, 2, 3, 4],
                index=2,
                help="Number of decimal places to show for monetary values"
            )

            thousands_separator = st.checkbox(
                "Use thousands separator",
                value=True,
                help="Display numbers with comma separators (e.g., 1,000,000)"
            )

            st.subheader("📈 Charts & Visuals")

            chart_theme = st.selectbox(
                "Chart style",
                options=["Professional", "Modern", "Minimal"],
                help="Visual style for charts and graphs"
            )

            default_chart = st.selectbox(
                "Default chart type",
                options=["Line", "Bar", "Candlestick", "Area"],
                help="Preferred chart type for financial data"
            )

        with col2:
            st.subheader("🎯 Theme & Layout")

            theme_mode = st.selectbox(
                "Theme mode",
                options=["Auto (follow system)", "Light", "Dark"],
                help="Color theme for the application"
            )

            layout_density = st.selectbox(
                "Layout density",
                options=["Compact", "Comfortable", "Spacious"],
                index=1,
                help="How much information to show per screen"
            )

            sidebar_expanded = st.checkbox(
                "Keep sidebar expanded",
                value=True,
                help="Show sidebar expanded by default"
            )

            st.subheader("🎨 Colors")

            col_left, col_right = st.columns(2)
            with col_left:
                positive_color = st.color_picker(
                    "Positive values",
                    value="#00C851",
                    help="Color for positive financial values"
                )

            with col_right:
                negative_color = st.color_picker(
                    "Negative values",
                    value="#FF4444",
                    help="Color for negative financial values"
                )

        # Store preferences
        st.session_state.onboarding_data.update({
            'decimal_places': decimal_places,
            'use_thousands_separator': thousands_separator,
            'chart_theme': chart_theme.lower(),
            'default_chart_type': default_chart.lower(),
            'theme_mode': theme_mode.lower().replace(' (follow system)', '').replace(' ', '_'),
            'layout_density': layout_density.lower(),
            'sidebar_default_expanded': sidebar_expanded,
            'positive_color': positive_color,
            'negative_color': negative_color
        })

        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("⬅️ Back", key="disp_back"):
                st.session_state.onboarding_step = 3
                st.rerun()

        with col3:
            if st.button("Next ➡️", type="primary", key="disp_next"):
                st.session_state.onboarding_step = 5
                st.rerun()

        return False

    def _render_final_setup_step(self) -> bool:
        """Render final setup and user creation step"""
        st.header("🎯 Complete Your Setup")
        st.markdown("Create your user profile to save these preferences:")

        # User creation form
        with st.form("user_creation_form"):
            st.subheader("👤 Create Your Profile")

            col1, col2 = st.columns(2)

            with col1:
                user_id = st.text_input(
                    "User ID *",
                    placeholder="e.g., john_smith",
                    help="Unique identifier for your account"
                )

                username = st.text_input(
                    "Display Name *",
                    placeholder="e.g., John Smith",
                    help="Name to display in the application"
                )

            with col2:
                email = st.text_input(
                    "Email (optional)",
                    placeholder="e.g., john@example.com",
                    help="For future features like sharing and notifications"
                )

            # Preferences summary
            st.subheader("📋 Your Preferences Summary")

            data = st.session_state.onboarding_data

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **Experience Level:** {data.get('experience_level', 'Not set')}

                **Financial Preferences:**
                - Methodology: {data.get('methodology', 'moderate').title()}
                - Primary Currency: {data.get('primary_currency', 'USD')}
                - Projection Years: {data.get('projection_years', 5)}
                """)

            with col2:
                st.markdown(f"""
                **Display Preferences:**
                - Theme: {data.get('theme_mode', 'auto').title()}
                - Layout: {data.get('layout_density', 'comfortable').title()}
                - Chart Style: {data.get('chart_theme', 'professional').title()}
                """)

            # Submit form
            submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])

            with submit_col2:
                submitted = st.form_submit_button(
                    "🚀 Complete Setup",
                    type="primary",
                    use_container_width=True
                )

            if submitted:
                if user_id and username:
                    if self._create_user_with_preferences(user_id, username, email):
                        st.success("✅ Setup completed successfully!")
                        st.session_state.onboarding_completed = True
                        st.balloons()
                        return True
                    else:
                        st.error("❌ Failed to create user profile")
                else:
                    st.error("❌ User ID and Display Name are required")

        # Navigation
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("⬅️ Back", key="final_back"):
                st.session_state.onboarding_step = 4
                st.rerun()

        with col2:
            if st.button("✅ Complete Without Profile", key="complete_no_profile", type="primary"):
                st.session_state.onboarding_completed = True
                st.success("Setup completed! You can create a user profile later in the sidebar.")
                st.balloons()
                return True

        with col3:
            if st.button("⏭️ Skip User Creation", key="skip_user"):
                st.session_state.onboarding_completed = True
                st.info("You can create a user profile later in the sidebar")
                return True

        return False

    def _create_user_with_preferences(self, user_id: str, username: str, email: Optional[str]) -> bool:
        """Create user with onboarding preferences"""
        try:
            data = st.session_state.onboarding_data

            # Map onboarding data to preference objects
            financial_prefs = FinancialPreferences(
                default_discount_rate=data.get('default_discount_rate', 0.10),
                default_terminal_growth_rate=data.get('default_terminal_growth_rate', 0.025),
                default_projection_years=data.get('projection_years', 5),
                methodology=AnalysisMethodology(data.get('methodology', 'moderate')),
                primary_currency=CurrencyPreference(data.get('primary_currency', 'USD')),
                preferred_regions=[
                    RegionPreference(region) for region in data.get('preferred_regions', ['north_america'])
                ],
                include_beta_adjustment=data.get('use_beta_adjustment', True),
                use_country_risk_premium=data.get('use_country_risk_premium', False)
            )

            display_prefs = DisplayPreferences(
                decimal_places=data.get('decimal_places', 2),
                use_thousands_separator=data.get('use_thousands_separator', True),
                chart_theme=data.get('chart_theme', 'plotly'),
                default_chart_type=data.get('default_chart_type', 'line'),
                positive_color=data.get('positive_color', '#00C851'),
                negative_color=data.get('negative_color', '#FF4444')
            )

            notification_prefs = NotificationPreferences(
                show_calculation_warnings=data.get('show_calculation_warnings', True),
                show_performance_tips=data.get('show_performance_tips', True),
                price_change_threshold=data.get('price_change_threshold', 0.05)
            )

            data_source_prefs = DataSourcePreferences(
                prefer_excel_over_api=data.get('prefer_excel_over_api', False),
                auto_refresh_data=data.get('auto_refresh_data', True),
                cache_duration_hours=data.get('cache_duration_hours', 24)
            )

            watch_list_prefs = WatchListPreferences()

            user_preferences = UserPreferences(
                financial=financial_prefs,
                display=display_prefs,
                notifications=notification_prefs,
                data_sources=data_source_prefs,
                watch_lists=watch_list_prefs
            )

            # Create user profile
            profile = self.manager.create_user(user_id, username, email)

            # Update preferences
            if self.manager.update_preferences(user_id, user_preferences):
                # Mark onboarding as completed
                profile.onboarding_completed = True
                self.manager.set_current_user(user_id)

                # Apply UI preferences to session state
                ui_prefs = create_default_ui_preferences()
                if data.get('beginner_mode'):
                    ui_prefs.accessibility.beginner_mode = True
                    ui_prefs.accessibility.show_help_text = True
                    ui_prefs.accessibility.show_tooltips = True

                st.session_state.ui_preferences = ui_prefs

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to create user with preferences: {e}")
            return False

    def render_onboarding_reminder(self) -> None:
        """Render a small reminder to complete onboarding"""
        if self.should_show_onboarding():
            with st.sidebar:
                st.warning("""
                🎯 **Complete Your Setup**

                Personalize your financial analysis experience with our quick onboarding.
                """)

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("▶️ Start Setup", key="start_onboarding"):
                        st.session_state.show_onboarding = True
                        st.rerun()

                with col2:
                    if st.button("🚨 Skip All", key="emergency_exit", help="Skip onboarding completely"):
                        st.session_state.onboarding_completed = True
                        st.session_state.skip_onboarding = True
                        st.success("✅ Onboarding skipped!")
                        st.rerun()


def create_user_onboarding_flow() -> UserOnboardingFlow:
    """Create and return a UserOnboardingFlow instance"""
    return UserOnboardingFlow()


def should_show_onboarding() -> bool:
    """Helper function to check if onboarding should be shown"""
    flow = create_user_onboarding_flow()
    return flow.should_show_onboarding()