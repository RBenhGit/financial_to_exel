"""
UI Preferences and Theme Management

Specialized preferences for Streamlit UI customization and theming
in the financial analysis application.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Theme modes for the application"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ChartStyle(Enum):
    """Chart styling options"""
    PROFESSIONAL = "professional"
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"


class LayoutMode(Enum):
    """Layout configuration modes"""
    COMPACT = "compact"
    STANDARD = "standard"
    EXPANDED = "expanded"


@dataclass
class ColorScheme:
    """Color scheme definition"""

    # Primary colors
    primary: str = "#1f77b4"
    secondary: str = "#ff7f0e"
    accent: str = "#2ca02c"

    # Status colors
    success: str = "#00C851"
    warning: str = "#FFB700"
    error: str = "#FF4444"
    info: str = "#33B5E5"

    # Financial colors
    profit: str = "#00C851"
    loss: str = "#FF4444"
    neutral: str = "#6c757d"

    # Background colors
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    card: str = "#ffffff"

    # Text colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#adb5bd"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format"""
        return {
            'primary': self.primary,
            'secondary': self.secondary,
            'accent': self.accent,
            'success': self.success,
            'warning': self.warning,
            'error': self.error,
            'info': self.info,
            'profit': self.profit,
            'loss': self.loss,
            'neutral': self.neutral,
            'background': self.background,
            'surface': self.surface,
            'card': self.card,
            'text_primary': self.text_primary,
            'text_secondary': self.text_secondary,
            'text_muted': self.text_muted
        }


@dataclass
class ThemePreferences:
    """Theme and visual styling preferences"""

    # Theme settings
    mode: ThemeMode = ThemeMode.LIGHT
    custom_css_enabled: bool = True

    # Color schemes
    light_colors: ColorScheme = field(default_factory=ColorScheme)
    dark_colors: ColorScheme = field(default_factory=lambda: ColorScheme(
        primary="#4dabf7",
        secondary="#fd7e14",
        accent="#51cf66",
        background="#212529",
        surface="#343a40",
        card="#495057",
        text_primary="#f8f9fa",
        text_secondary="#adb5bd",
        text_muted="#6c757d"
    ))

    # Typography
    font_family: str = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    font_size_base: int = 14
    header_font_size: int = 24

    # Chart styling
    chart_style: ChartStyle = ChartStyle.PROFESSIONAL
    chart_background_transparent: bool = False
    show_chart_toolbar: bool = True

    def get_active_colors(self) -> ColorScheme:
        """Get the color scheme for the current theme mode"""
        if self.mode == ThemeMode.DARK:
            return self.dark_colors
        else:
            return self.light_colors

    def get_streamlit_css(self) -> str:
        """Generate custom CSS for Streamlit"""
        colors = self.get_active_colors()

        return f"""
        <style>
        /* Import fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global styles */
        .stApp {{
            font-family: {self.font_family};
            background-color: {colors.background};
            color: {colors.text_primary};
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {colors.text_primary};
            font-family: {self.font_family};
        }}

        h1 {{
            font-size: {self.header_font_size + 8}px;
            font-weight: 700;
        }}

        h2 {{
            font-size: {self.header_font_size}px;
            font-weight: 600;
        }}

        /* Cards and containers */
        .metric-card {{
            background-color: {colors.card};
            border: 1px solid {colors.surface};
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .success-card {{
            background-color: {colors.success}15;
            border: 1px solid {colors.success}40;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}

        .warning-card {{
            background-color: {colors.warning}15;
            border: 1px solid {colors.warning}40;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}

        .error-card {{
            background-color: {colors.error}15;
            border: 1px solid {colors.error}40;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}

        /* Metrics */
        .metric-positive {{
            color: {colors.profit};
            font-weight: 600;
        }}

        .metric-negative {{
            color: {colors.loss};
            font-weight: 600;
        }}

        .metric-neutral {{
            color: {colors.neutral};
            font-weight: 500;
        }}

        /* Sidebar */
        .css-1d391kg {{
            background-color: {colors.surface};
        }}

        /* Buttons */
        .stButton > button {{
            background-color: {colors.primary};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .stButton > button:hover {{
            background-color: {colors.primary}dd;
            transform: translateY(-1px);
        }}

        /* Selectbox and inputs */
        .stSelectbox > div > div {{
            background-color: {colors.card};
            border: 1px solid {colors.surface};
            border-radius: 6px;
        }}

        .stTextInput > div > div > input {{
            background-color: {colors.card};
            border: 1px solid {colors.surface};
            border-radius: 6px;
            color: {colors.text_primary};
        }}

        /* Tables */
        .stDataFrame {{
            background-color: {colors.card};
            border-radius: 8px;
            overflow: hidden;
        }}

        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {colors.surface};
            border-radius: 6px;
        }}

        /* Custom financial indicators */
        .financial-positive {{
            color: {colors.profit};
            font-weight: 600;
        }}

        .financial-negative {{
            color: {colors.loss};
            font-weight: 600;
        }}

        .financial-ratio {{
            font-family: 'Courier New', monospace;
            font-weight: 500;
            background-color: {colors.surface};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        </style>
        """


@dataclass
class LayoutPreferences:
    """Layout and structure preferences"""

    # Layout mode
    mode: LayoutMode = LayoutMode.STANDARD

    # Sidebar preferences
    sidebar_width: int = 300
    sidebar_default_expanded: bool = True
    show_sidebar_company_info: bool = True
    show_sidebar_quick_actions: bool = True

    # Main content preferences
    show_header_logo: bool = True
    show_navigation_breadcrumbs: bool = True
    enable_sticky_headers: bool = False

    # Tab preferences
    default_tab: str = "Analysis"
    remember_tab_state: bool = True

    # Table preferences
    rows_per_page: int = 25
    enable_pagination: bool = True
    show_row_numbers: bool = False
    enable_sorting: bool = True
    enable_filtering: bool = True

    # Chart preferences
    default_chart_height: int = 400
    enable_chart_interactivity: bool = True
    show_chart_controls: bool = True

    # Performance preferences
    enable_caching: bool = True
    lazy_load_charts: bool = False
    reduce_animations: bool = False


@dataclass
class AccessibilityPreferences:
    """Accessibility and usability preferences"""

    # Visual accessibility
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    reduce_motion: bool = False

    # Interaction preferences
    keyboard_shortcuts_enabled: bool = True
    focus_indicators_enhanced: bool = False
    click_confirmation: bool = False

    # Screen reader support
    aria_labels_verbose: bool = False
    table_headers_enhanced: bool = True

    # Language and localization
    language: str = "en"
    number_format_locale: str = "en-US"
    date_format: str = "MM/dd/yyyy"

    # Help and guidance
    show_tooltips: bool = True
    show_help_text: bool = True
    beginner_mode: bool = False


@dataclass
class UIPreferences:
    """Complete UI preferences container"""

    # Sub-preference categories
    theme: ThemePreferences = field(default_factory=ThemePreferences)
    layout: LayoutPreferences = field(default_factory=LayoutPreferences)
    accessibility: AccessibilityPreferences = field(default_factory=AccessibilityPreferences)

    # Application-specific preferences
    show_performance_monitor: bool = False
    enable_experimental_features: bool = False
    auto_save_preferences: bool = True

    # Export preferences
    default_export_format: str = "xlsx"
    include_charts_in_exports: bool = True
    watermark_exports: bool = False

    def apply_to_streamlit(self) -> None:
        """Apply UI preferences to the current Streamlit session"""
        try:
            import streamlit as st

            # Apply theme CSS
            if self.theme.custom_css_enabled:
                st.markdown(self.theme.get_streamlit_css(), unsafe_allow_html=True)

            # Configure sidebar
            if hasattr(st, 'set_page_config'):
                st.set_page_config(
                    initial_sidebar_state="expanded" if self.layout.sidebar_default_expanded else "collapsed"
                )

            # Store preferences in session state for component access
            st.session_state.ui_preferences = self

            logger.debug("Applied UI preferences to Streamlit session")

        except Exception as e:
            logger.warning(f"Failed to apply UI preferences to Streamlit: {e}")

    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration based on preferences"""
        colors = self.theme.get_active_colors()

        config = {
            'height': self.layout.default_chart_height,
            'interactive': self.layout.enable_chart_interactivity,
            'show_controls': self.layout.show_chart_controls,
            'background_color': colors.background if not self.theme.chart_background_transparent else 'transparent',
            'text_color': colors.text_primary,
            'grid_color': colors.surface,
            'color_palette': [
                colors.primary,
                colors.secondary,
                colors.accent,
                colors.success,
                colors.warning,
                colors.error
            ]
        }

        # Apply chart style modifications
        if self.theme.chart_style == ChartStyle.MINIMAL:
            config['show_controls'] = False
            config['grid_opacity'] = 0.3
        elif self.theme.chart_style == ChartStyle.PROFESSIONAL:
            config['grid_opacity'] = 0.6
            config['font_family'] = self.theme.font_family

        return config

    def get_table_config(self) -> Dict[str, Any]:
        """Get table configuration based on preferences"""
        return {
            'rows_per_page': self.layout.rows_per_page,
            'show_pagination': self.layout.enable_pagination,
            'show_row_numbers': self.layout.show_row_numbers,
            'enable_sorting': self.layout.enable_sorting,
            'enable_filtering': self.layout.enable_filtering,
            'large_text': self.accessibility.large_text_mode,
            'high_contrast': self.accessibility.high_contrast_mode
        }


def create_default_ui_preferences() -> UIPreferences:
    """Create default UI preferences"""
    return UIPreferences()


def create_dark_theme_preferences() -> UIPreferences:
    """Create UI preferences with dark theme"""
    prefs = UIPreferences()
    prefs.theme.mode = ThemeMode.DARK
    return prefs


def create_accessible_preferences() -> UIPreferences:
    """Create UI preferences optimized for accessibility"""
    prefs = UIPreferences()
    prefs.accessibility.high_contrast_mode = True
    prefs.accessibility.large_text_mode = True
    prefs.accessibility.reduce_motion = True
    prefs.accessibility.aria_labels_verbose = True
    prefs.accessibility.show_tooltips = True
    prefs.accessibility.show_help_text = True
    return prefs