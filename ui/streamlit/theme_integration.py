"""
Theme Integration Module
========================

Integration module for the advanced theme customization system
with the main Streamlit financial analysis application.
"""

import streamlit as st
import os
from typing import Optional, Dict, Any
import logging

from .advanced_theme_customization import AdvancedThemeManager, AdvancedTheme
from .theme_customization_ui import ThemeCustomizationUI
from .theme_preview_system import ThemePreviewSystem
from .dashboard_themes import ThemeManager, apply_theme

logger = logging.getLogger(__name__)


class ThemeIntegrationManager:
    """Manages integration of advanced themes with the main application"""

    def __init__(self):
        self.advanced_manager = AdvancedThemeManager()
        self.standard_manager = ThemeManager()
        self.customization_ui = ThemeCustomizationUI()
        self.preview_system = ThemePreviewSystem()

        # Initialize session state for theme management
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize theme-related session state variables"""
        if 'theme_integration_initialized' not in st.session_state:
            st.session_state.theme_integration_initialized = True
            st.session_state.show_advanced_themes = False
            st.session_state.current_advanced_theme = None
            st.session_state.theme_preview_mode = False
            st.session_state.active_theme_type = "standard"  # "standard" or "advanced"

    def render_theme_selector_sidebar(self):
        """Render theme selector in sidebar with advanced options"""
        with st.sidebar:
            st.markdown("### 🎨 Theme Settings")

            # Theme type selector
            theme_type = st.radio(
                "Theme Type",
                options=["Standard Themes", "Advanced Themes"],
                index=0 if st.session_state.active_theme_type == "standard" else 1,
                help="Choose between standard themes or advanced custom themes"
            )

            if theme_type == "Standard Themes":
                self._render_standard_theme_selector()
            else:
                self._render_advanced_theme_selector()

            # Quick access to advanced customization
            st.markdown("---")
            if st.button("🛠️ Open Theme Designer", use_container_width=True):
                st.session_state.show_advanced_themes = True
                st.switch_page("Theme Designer")  # Would need to be implemented as a separate page

    def _render_standard_theme_selector(self):
        """Render standard theme selector"""
        st.session_state.active_theme_type = "standard"

        available_themes = self.standard_manager.get_available_themes()
        current_theme = st.session_state.get('selected_theme', 'professional_light')

        selected_theme = st.selectbox(
            "Select Theme",
            options=list(available_themes.keys()),
            format_func=lambda x: available_themes[x],
            index=list(available_themes.keys()).index(current_theme) if current_theme in available_themes else 0,
            key="standard_theme_selector"
        )

        if selected_theme != current_theme:
            self.standard_manager.set_theme(selected_theme)
            st.session_state.current_advanced_theme = None
            st.rerun()

    def _render_advanced_theme_selector(self):
        """Render advanced theme selector"""
        st.session_state.active_theme_type = "advanced"

        all_themes = self.advanced_manager.get_all_themes()

        if not all_themes:
            st.info("No advanced themes found. Create one using the Theme Designer!")
            if st.button("🎨 Create First Theme"):
                st.session_state.show_advanced_themes = True
            return

        theme_names = list(all_themes.keys())
        current_advanced = st.session_state.get('current_advanced_theme_name', theme_names[0] if theme_names else None)

        selected_theme_name = st.selectbox(
            "Select Advanced Theme",
            options=theme_names,
            index=theme_names.index(current_advanced) if current_advanced in theme_names else 0,
            key="advanced_theme_selector"
        )

        if selected_theme_name:
            selected_theme = all_themes[selected_theme_name]

            # Show theme info
            st.markdown(f"**Author:** {selected_theme.metadata.author}")
            st.markdown(f"**Category:** {selected_theme.metadata.category}")

            if selected_theme.metadata.tags:
                st.markdown(f"**Tags:** {', '.join(selected_theme.metadata.tags[:3])}")

            # Apply theme button
            if st.button("Apply Theme", use_container_width=True):
                self._apply_advanced_theme(selected_theme)
                st.session_state.current_advanced_theme_name = selected_theme_name
                st.success(f"Applied: {selected_theme.metadata.name}")

            # Theme actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.edit_theme_name = selected_theme_name
                    st.session_state.show_advanced_themes = True

            with col2:
                if st.button("👁️ Preview", use_container_width=True):
                    st.session_state.preview_theme = selected_theme
                    st.session_state.theme_preview_mode = True

    def _apply_advanced_theme(self, theme: AdvancedTheme):
        """Apply an advanced theme to the current session"""
        try:
            # Convert to standard theme format for compatibility
            standard_theme = theme.to_dashboard_theme()

            # Generate and apply CSS
            css = self._generate_advanced_theme_css(theme)
            st.markdown(css, unsafe_allow_html=True)

            # Store theme in session state
            st.session_state.current_advanced_theme = {
                'name': theme.metadata.name,
                'author': theme.metadata.author,
                'category': theme.metadata.category,
                'theme_object': theme
            }

            # Apply auto-switching if enabled
            self._handle_auto_switching(theme)

            logger.info(f"Applied advanced theme: {theme.metadata.name}")

        except Exception as e:
            logger.error(f"Error applying advanced theme: {e}")
            st.error(f"Failed to apply theme: {e}")

    def _generate_advanced_theme_css(self, theme: AdvancedTheme) -> str:
        """Generate CSS for advanced theme with all customizations"""
        colors = theme.color_palette
        font_family = theme.custom_font.family if theme.custom_font else "Inter, sans-serif"

        # Font import
        font_import = ""
        if theme.custom_font and theme.custom_font.provider.value == "google":
            font_import = f'@import url("{theme.custom_font.get_font_url()}");'

        # Calculate scaled values
        base_border_radius = 8 * theme.border_radius_scale
        shadow_base = 0.1 * theme.shadow_intensity

        return f"""
        <style>
        {font_import}

        /* Advanced Theme: {theme.metadata.name} */
        :root {{
            /* Color Variables */
            --at-primary: {colors.primary};
            --at-secondary: {colors.secondary};
            --at-accent: {colors.accent};
            --at-success: {colors.success};
            --at-warning: {colors.warning};
            --at-danger: {colors.danger};
            --at-info: {colors.info};
            --at-background: {colors.background};
            --at-surface: {colors.surface};
            --at-text-primary: {colors.text_primary};
            --at-text-secondary: {colors.text_secondary};
            --at-border: {colors.border};
            --at-hover: {colors.hover};

            /* Extended Colors */
            --at-link: {colors.link};
            --at-focus: {colors.focus};
            --at-selection: {colors.selection};
            --at-sidebar-bg: {colors.sidebar_bg};
            --at-header-bg: {colors.header_bg};
            --at-footer-bg: {colors.footer_bg};

            /* Typography */
            --at-font-family: {font_family};
            --at-font-scale: {theme.font_scale};
            --at-line-height: {theme.line_height};
            --at-letter-spacing: {theme.letter_spacing}em;

            /* Layout */
            --at-border-radius: {base_border_radius}px;
            --at-spacing: {theme.spacing_scale}rem;
            --at-shadow-intensity: {theme.shadow_intensity};

            /* Gradients */
            --at-gradient: {colors.get_gradient_css()};
        }}

        /* Global Application Styles */
        .stApp {{
            background-color: var(--at-background);
            color: var(--at-text-primary);
            font-family: var(--at-font-family);
            line-height: var(--at-line-height);
            letter-spacing: var(--at-letter-spacing);
        }}

        /* Typography Scaling */
        .stApp h1 {{ font-size: calc(2.5rem * var(--at-font-scale)); }}
        .stApp h2 {{ font-size: calc(2rem * var(--at-font-scale)); }}
        .stApp h3 {{ font-size: calc(1.5rem * var(--at-font-scale)); }}
        .stApp h4 {{ font-size: calc(1.25rem * var(--at-font-scale)); }}
        .stApp h5 {{ font-size: calc(1.125rem * var(--at-font-scale)); }}
        .stApp h6 {{ font-size: calc(1rem * var(--at-font-scale)); }}

        /* Sidebar Customization */
        .css-1d391kg {{
            background-color: var(--at-sidebar-bg);
            border-right: 1px solid var(--at-border);
        }}

        /* Main Content Area */
        .main .block-container {{
            background-color: var(--at-background);
            color: var(--at-text-primary);
            padding-top: calc(var(--at-spacing) * 2);
        }}

        /* Buttons */
        .stButton > button {{
            background: var(--at-primary);
            color: white;
            border: none;
            border-radius: var(--at-border-radius);
            padding: calc(var(--at-spacing) * 0.5) var(--at-spacing);
            font-weight: 500;
            transition: all 0.2s ease;
            font-family: var(--at-font-family);
        }}

        .stButton > button:hover {{
            background: var(--at-secondary);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,calc(0.2 * var(--at-shadow-intensity)));
        }}

        /* Form Elements */
        .stSelectbox > div > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {{
            background-color: var(--at-surface);
            border: 1px solid var(--at-border);
            border-radius: var(--at-border-radius);
            color: var(--at-text-primary);
        }}

        /* Metrics */
        .metric-container {{
            background: var(--at-surface);
            border: 1px solid var(--at-border);
            border-radius: var(--at-border-radius);
            padding: var(--at-spacing);
            box-shadow: 0 2px 8px rgba(0,0,0,calc(0.05 * var(--at-shadow-intensity)));
        }}

        /* Charts Container */
        .js-plotly-plot {{
            background: var(--at-surface) !important;
            border-radius: var(--at-border-radius);
        }}

        /* Data Tables */
        .stDataFrame {{
            background: var(--at-surface);
            border: 1px solid var(--at-border);
            border-radius: var(--at-border-radius);
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: var(--at-surface);
            border: 1px solid var(--at-border);
            border-radius: var(--at-border-radius);
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: var(--at-surface);
            border-radius: var(--at-border-radius);
        }}

        .stTabs [data-baseweb="tab"] {{
            color: var(--at-text-secondary);
            background-color: transparent;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: var(--at-primary);
            background-color: var(--at-background);
        }}

        /* Success/Warning/Error States */
        .stSuccess {{
            background-color: color-mix(in srgb, var(--at-success) 10%, transparent);
            border-left: 4px solid var(--at-success);
            border-radius: var(--at-border-radius);
        }}

        .stWarning {{
            background-color: color-mix(in srgb, var(--at-warning) 10%, transparent);
            border-left: 4px solid var(--at-warning);
            border-radius: var(--at-border-radius);
        }}

        .stError {{
            background-color: color-mix(in srgb, var(--at-danger) 10%, transparent);
            border-left: 4px solid var(--at-danger);
            border-radius: var(--at-border-radius);
        }}

        /* Custom Branding Header */
        .advanced-theme-header {{
            background: var(--at-gradient);
            color: white;
            padding: calc(var(--at-spacing) * 2);
            border-radius: var(--at-border-radius);
            margin-bottom: var(--at-spacing);
            text-align: center;
        }}

        /* Component Overrides */
        {self._generate_component_overrides(theme)}

        /* Accessibility Enhancements */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}

        /* Selection Colors */
        ::selection {{
            background-color: var(--at-selection);
            color: var(--at-text-primary);
        }}

        /* Focus States */
        .stButton > button:focus,
        .stSelectbox > div > div:focus,
        .stTextInput > div > div > input:focus {{
            outline: 2px solid var(--at-focus);
            outline-offset: 2px;
        }}
        </style>
        """

    def _generate_component_overrides(self, theme: AdvancedTheme) -> str:
        """Generate CSS for custom component overrides"""
        overrides_css = ""

        for component, styles in theme.component_overrides.items():
            css_rules = []
            for property_name, value in styles.items():
                css_property = property_name.replace('_', '-')
                css_rules.append(f"    {css_property}: {value};")

            if css_rules:
                overrides_css += f"""
                {component} {{
                {chr(10).join(css_rules)}
                }}
                """

        return overrides_css

    def _handle_auto_switching(self, theme: AdvancedTheme):
        """Handle automatic theme switching if enabled"""
        if theme.auto_switch.mode.value != "disabled":
            target_mode = self.advanced_manager.should_auto_switch(theme)

            if target_mode:
                # This would require creating light/dark variants of the theme
                # For now, just log the intended switch
                logger.info(f"Auto-switch would change to {target_mode.value} mode")

    def render_theme_customization_page(self):
        """Render the full theme customization interface as a separate page"""
        if st.session_state.get('show_advanced_themes', False):
            st.title("🎨 Advanced Theme Customization")

            # Back button
            if st.button("← Back to Main App"):
                st.session_state.show_advanced_themes = False
                st.rerun()

            # Render the customization UI
            self.customization_ui.render()

        else:
            st.info("Advanced theme customization is not currently open.")
            if st.button("🎨 Open Theme Designer"):
                st.session_state.show_advanced_themes = True
                st.rerun()

    def apply_current_theme(self):
        """Apply the currently selected theme (standard or advanced)"""
        if st.session_state.active_theme_type == "advanced" and st.session_state.current_advanced_theme:
            theme_obj = st.session_state.current_advanced_theme.get('theme_object')
            if theme_obj:
                self._apply_advanced_theme(theme_obj)
        else:
            # Apply standard theme
            apply_theme(self.standard_manager)

    def get_current_theme_info(self) -> Dict[str, Any]:
        """Get information about the currently applied theme"""
        if st.session_state.active_theme_type == "advanced" and st.session_state.current_advanced_theme:
            return {
                'type': 'advanced',
                'name': st.session_state.current_advanced_theme['name'],
                'author': st.session_state.current_advanced_theme['author'],
                'category': st.session_state.current_advanced_theme['category']
            }
        else:
            current_standard = st.session_state.get('selected_theme', 'professional_light')
            available_themes = self.standard_manager.get_available_themes()
            return {
                'type': 'standard',
                'name': available_themes.get(current_standard, current_standard),
                'key': current_standard
            }


# Global instance for easy access
theme_integration = ThemeIntegrationManager()


def integrate_theme_system():
    """Initialize and integrate the theme system with the current app"""
    theme_integration.apply_current_theme()
    return theme_integration


def render_theme_sidebar():
    """Render theme controls in sidebar"""
    theme_integration.render_theme_selector_sidebar()


def get_theme_info():
    """Get current theme information"""
    return theme_integration.get_current_theme_info()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Theme Integration Demo",
        page_icon="🎨",
        layout="wide"
    )

    # Demo the integration
    st.title("🎨 Theme Integration Demo")

    # Initialize theme system
    integration = integrate_theme_system()

    # Show theme info
    theme_info = get_theme_info()
    st.json(theme_info)

    # Render sidebar controls
    render_theme_sidebar()

    # Sample content to demonstrate theming
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Revenue", "$2.5B", "+15%")

    with col2:
        st.metric("Profit", "$450M", "+8%")

    with col3:
        st.metric("Growth", "12%", "+2pp")

    # Sample chart
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2023-01-01', periods=12, freq='M')
    values = np.cumsum(np.random.randn(12) * 10 + 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, name='Sample Data'))
    fig.update_layout(title="Sample Chart with Theme")

    st.plotly_chart(fig, use_container_width=True)