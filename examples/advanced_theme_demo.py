"""
Advanced Theme Customization Demo
=================================

Demonstration script showcasing the advanced theme customization features
including custom color palettes, typography, branding, and real-time preview.
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.streamlit.advanced_theme_customization import (
    AdvancedThemeManager, create_default_themes, AdvancedTheme
)
from ui.streamlit.theme_customization_ui import ThemeCustomizationUI
from ui.streamlit.theme_preview_system import ThemePreviewSystem
from ui.streamlit.theme_integration import ThemeIntegrationManager


def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Advanced Theme Customization Demo",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎨 Advanced Theme Customization System")
    st.markdown("""
    **Welcome to the Advanced Theme Customization Demo!**

    This demonstration showcases the comprehensive theme system featuring:
    - **Custom Color Palettes** with gradient support
    - **Typography Customization** with Google Fonts integration
    - **Personalized Branding** with logos and company information
    - **Auto-Switching** based on time or system preferences
    - **Theme Sharing** via JSON import/export
    - **Real-time Preview** functionality
    """)

    # Initialize managers
    if 'theme_managers_initialized' not in st.session_state:
        st.session_state.advanced_manager = AdvancedThemeManager()
        st.session_state.customization_ui = ThemeCustomizationUI()
        st.session_state.preview_system = ThemePreviewSystem()
        st.session_state.integration_manager = ThemeIntegrationManager()
        st.session_state.theme_managers_initialized = True

        # Create default themes if none exist
        try:
            all_themes = st.session_state.advanced_manager.get_all_themes()
            if not all_themes:
                st.info("Creating default theme collection...")
                default_themes = create_default_themes()
                for theme in default_themes.values():
                    st.session_state.advanced_manager.save_theme(theme)
                st.success(f"Created {len(default_themes)} default themes!")
        except Exception as e:
            st.error(f"Error creating default themes: {e}")

    # Main demo tabs
    demo_tab, customization_tab, preview_tab, integration_tab = st.tabs([
        "🏠 Demo Overview",
        "🎨 Theme Designer",
        "👁️ Theme Preview",
        "🔧 Integration"
    ])

    with demo_tab:
        render_demo_overview()

    with customization_tab:
        render_customization_demo()

    with preview_tab:
        render_preview_demo()

    with integration_tab:
        render_integration_demo()

    # Sidebar with theme controls
    render_demo_sidebar()


def render_demo_overview():
    """Render the demo overview tab"""
    st.header("🏠 System Overview")

    # Feature showcase
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎨 Core Features")

        features = [
            ("Custom Color Palettes", "Create unlimited color schemes with gradient support"),
            ("Typography Control", "Choose from Google Fonts with size and spacing controls"),
            ("Branding Integration", "Add logos, company names, and taglines"),
            ("Auto Theme Switching", "Time-based or system preference switching"),
            ("Real-time Preview", "See changes instantly as you customize"),
            ("Theme Sharing", "Import/export themes via JSON format")
        ]

        for title, description in features:
            with st.expander(f"**{title}**"):
                st.write(description)

    with col2:
        st.subheader("📊 Theme Statistics")

        try:
            all_themes = st.session_state.advanced_manager.get_all_themes()
            custom_themes = st.session_state.advanced_manager.custom_themes
            community_themes = st.session_state.advanced_manager.community_themes

            st.metric("Total Themes", len(all_themes))
            st.metric("Custom Themes", len(custom_themes))
            st.metric("Community Themes", len(community_themes))

            # Theme categories
            if all_themes:
                categories = {}
                for theme in all_themes.values():
                    cat = theme.metadata.category
                    categories[cat] = categories.get(cat, 0) + 1

                st.markdown("**Themes by Category:**")
                for category, count in categories.items():
                    st.write(f"- {category.title()}: {count}")

        except Exception as e:
            st.error(f"Error loading theme statistics: {e}")

    # Sample theme showcase
    st.subheader("🌟 Featured Themes")

    try:
        all_themes = st.session_state.advanced_manager.get_all_themes()

        if all_themes:
            theme_cols = st.columns(min(len(all_themes), 4))

            for i, (theme_name, theme) in enumerate(list(all_themes.items())[:4]):
                with theme_cols[i]:
                    render_theme_preview_card(theme_name, theme)
        else:
            st.info("No themes available. Create some using the Theme Designer!")

    except Exception as e:
        st.error(f"Error displaying featured themes: {e}")


def render_customization_demo():
    """Render the theme customization demo"""
    st.header("🎨 Theme Designer")

    try:
        st.session_state.customization_ui.render()
    except Exception as e:
        st.error(f"Error rendering customization UI: {e}")
        st.exception(e)


def render_preview_demo():
    """Render the theme preview demo"""
    st.header("👁️ Theme Preview System")

    try:
        all_themes = st.session_state.advanced_manager.get_all_themes()

        if not all_themes:
            st.info("No themes available for preview. Create some first!")
            return

        # Theme selection for preview
        col1, col2 = st.columns([1, 3])

        with col1:
            st.subheader("Select Theme")

            selected_theme_name = st.selectbox(
                "Choose theme to preview",
                options=list(all_themes.keys()),
                key="preview_theme_selector"
            )

            if selected_theme_name:
                theme = all_themes[selected_theme_name]

                # Theme info
                st.markdown(f"**Name:** {theme.metadata.name}")
                st.markdown(f"**Author:** {theme.metadata.author}")
                st.markdown(f"**Category:** {theme.metadata.category}")

                if theme.metadata.description:
                    st.markdown(f"**Description:** {theme.metadata.description}")

                # Preview options
                st.markdown("**Preview Options:**")
                preview_type = st.radio(
                    "Preview Type",
                    options=["Comprehensive", "Dashboard Only", "Charts Only", "Components Only"],
                    index=0
                )

        with col2:
            if selected_theme_name:
                st.subheader(f"Preview: {theme.metadata.name}")

                try:
                    preview_type_map = {
                        "Comprehensive": "comprehensive",
                        "Dashboard Only": "dashboard",
                        "Charts Only": "charts",
                        "Components Only": "components"
                    }

                    st.session_state.preview_system.render_live_preview(
                        theme,
                        preview_type_map.get(preview_type, "comprehensive")
                    )
                except Exception as e:
                    st.error(f"Error rendering theme preview: {e}")

    except Exception as e:
        st.error(f"Error in preview demo: {e}")


def render_integration_demo():
    """Render the integration demo"""
    st.header("🔧 System Integration")

    st.markdown("""
    This tab demonstrates how the advanced theme system integrates with the main application.
    """)

    # Integration status
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Integration Status")

        integration_checks = [
            ("Theme Manager", True, "Advanced theme manager initialized"),
            ("UI Integration", True, "Theme customization UI available"),
            ("Preview System", True, "Real-time preview functionality"),
            ("File System", True, "Theme storage and management"),
            ("Import/Export", True, "JSON theme sharing capability")
        ]

        for component, status, description in integration_checks:
            status_icon = "✅" if status else "❌"
            st.markdown(f"{status_icon} **{component}**: {description}")

    with col2:
        st.subheader("Integration Features")

        features = [
            "Seamless integration with existing Streamlit UI",
            "Backward compatibility with standard themes",
            "Session state management for theme persistence",
            "CSS generation and injection",
            "Component-specific styling overrides",
            "Accessibility enhancements"
        ]

        for feature in features:
            st.markdown(f"• {feature}")

    # Test integration
    st.subheader("Test Integration")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧪 Test Theme Application", type="primary"):
            try:
                all_themes = st.session_state.advanced_manager.get_all_themes()
                if all_themes:
                    test_theme = list(all_themes.values())[0]
                    st.session_state.integration_manager._apply_advanced_theme(test_theme)
                    st.success(f"Successfully applied test theme: {test_theme.metadata.name}")
                else:
                    st.warning("No themes available for testing")
            except Exception as e:
                st.error(f"Error testing theme application: {e}")

    with col2:
        if st.button("📊 Show Theme Info"):
            try:
                theme_info = st.session_state.integration_manager.get_current_theme_info()
                st.json(theme_info)
            except Exception as e:
                st.error(f"Error getting theme info: {e}")


def render_demo_sidebar():
    """Render demo controls in sidebar"""
    with st.sidebar:
        st.markdown("### 🎛️ Demo Controls")

        # Theme system status
        st.markdown("**System Status**")
        status_items = [
            ("Advanced Manager", "✅"),
            ("Customization UI", "✅"),
            ("Preview System", "✅"),
            ("Integration", "✅")
        ]

        for item, status in status_items:
            st.markdown(f"{status} {item}")

        st.markdown("---")

        # Quick actions
        st.markdown("**Quick Actions**")

        if st.button("🔄 Reload Themes", use_container_width=True):
            try:
                st.session_state.advanced_manager._load_themes()
                st.success("Themes reloaded!")
            except Exception as e:
                st.error(f"Error reloading: {e}")

        if st.button("🧹 Clear Cache", use_container_width=True):
            # Clear theme-related session state
            theme_keys = [k for k in st.session_state.keys() if 'theme' in k.lower()]
            for key in theme_keys:
                if key != 'theme_managers_initialized':
                    del st.session_state[key]
            st.success("Cache cleared!")

        if st.button("📁 Theme Directory", use_container_width=True):
            st.info(f"Themes stored in: {st.session_state.advanced_manager.themes_dir}")

        st.markdown("---")

        # System info
        st.markdown("**System Information**")
        st.markdown(f"**Streamlit Version:** {st.__version__}")
        st.markdown(f"**Theme System:** Advanced v1.0")

        try:
            all_themes = st.session_state.advanced_manager.get_all_themes()
            st.markdown(f"**Available Themes:** {len(all_themes)}")
        except:
            st.markdown("**Available Themes:** Error loading")


def render_theme_preview_card(theme_name: str, theme):
    """Render a compact theme preview card"""
    colors = theme.color_palette

    # Theme preview with colors
    st.markdown(f"""
    <div style="
        background: {colors.get_gradient_css()};
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        color: white;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <h4 style="margin: 0; color: white;">{theme_name}</h4>
        <small style="opacity: 0.9;">{theme.metadata.category}</small>
    </div>
    """, unsafe_allow_html=True)

    # Color palette
    color_preview = f"""
    <div style="display: flex; gap: 2px; justify-content: center; margin: 0.5rem 0;">
        <div style="width: 15px; height: 15px; background: {colors.primary}; border-radius: 2px;"></div>
        <div style="width: 15px; height: 15px; background: {colors.secondary}; border-radius: 2px;"></div>
        <div style="width: 15px; height: 15px; background: {colors.accent}; border-radius: 2px;"></div>
        <div style="width: 15px; height: 15px; background: {colors.success}; border-radius: 2px;"></div>
        <div style="width: 15px; height: 15px; background: {colors.warning}; border-radius: 2px;"></div>
    </div>
    """
    st.markdown(color_preview, unsafe_allow_html=True)

    # Quick apply button
    if st.button(f"Apply {theme_name}", key=f"apply_card_{theme_name}", use_container_width=True):
        try:
            st.session_state.integration_manager._apply_advanced_theme(theme)
            st.success(f"Applied: {theme_name}")
        except Exception as e:
            st.error(f"Error applying theme: {e}")


if __name__ == "__main__":
    main()