"""
Theme Customization UI Component
===============================

Advanced theme customization interface for creating, editing,
and managing custom themes with real-time preview.
"""

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import colorsys
import re

from .advanced_theme_customization import (
    AdvancedThemeManager, AdvancedTheme, AdvancedColorPalette,
    ThemeMetadata, CustomFont, BrandingSettings, AutoSwitchSettings,
    FontProvider, AutoSwitchMode, create_default_themes
)
from .dashboard_themes import ThemeManager, apply_theme


class ThemeCustomizationUI:
    """Theme customization user interface"""

    def __init__(self):
        self.advanced_manager = AdvancedThemeManager()
        self.standard_manager = ThemeManager()

        # Initialize session state
        if 'current_custom_theme' not in st.session_state:
            st.session_state.current_custom_theme = None
        if 'theme_preview_mode' not in st.session_state:
            st.session_state.theme_preview_mode = False

    def render(self):
        """Render the complete theme customization interface"""
        st.title("🎨 Advanced Theme Customization")

        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎨 Create Theme",
            "📚 Theme Gallery",
            "🔧 Edit Theme",
            "🌍 Community",
            "⚙️ Settings"
        ])

        with tab1:
            self._render_create_theme()

        with tab2:
            self._render_theme_gallery()

        with tab3:
            self._render_edit_theme()

        with tab4:
            self._render_community_themes()

        with tab5:
            self._render_theme_settings()

    def _render_create_theme(self):
        """Render theme creation interface"""
        st.header("Create Custom Theme")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Theme Information")

            theme_name = st.text_input(
                "Theme Name",
                placeholder="My Custom Theme",
                help="Unique name for your theme"
            )

            description = st.text_area(
                "Description",
                placeholder="A beautiful custom theme for financial analysis",
                help="Brief description of your theme"
            )

            author = st.text_input(
                "Author",
                value=st.session_state.get('user_name', ''),
                help="Your name or username"
            )

            category = st.selectbox(
                "Category",
                options=["custom", "professional", "creative", "accessibility", "financial"],
                help="Theme category for organization"
            )

            tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="corporate, blue, modern",
                help="Tags to help others find your theme"
            )

            # Color palette section
            st.subheader("Color Palette")

            color_preset = st.selectbox(
                "Start with preset",
                options=["Custom", "Professional Blue", "Financial Green", "Creative Purple", "Minimal Gray"],
                help="Choose a starting point for your color palette"
            )

            # Get base colors based on preset
            base_colors = self._get_preset_colors(color_preset)

            col_a, col_b = st.columns(2)
            with col_a:
                primary = st.color_picker("Primary Color", value=base_colors["primary"])
                secondary = st.color_picker("Secondary Color", value=base_colors["secondary"])
                accent = st.color_picker("Accent Color", value=base_colors["accent"])
                success = st.color_picker("Success Color", value=base_colors["success"])

            with col_b:
                warning = st.color_picker("Warning Color", value=base_colors["warning"])
                danger = st.color_picker("Danger Color", value=base_colors["danger"])
                info = st.color_picker("Info Color", value=base_colors["info"])
                background = st.color_picker("Background Color", value=base_colors["background"])

            # Advanced color options
            with st.expander("🎨 Advanced Color Options"):
                surface = st.color_picker("Surface Color", value=base_colors["surface"])
                text_primary = st.color_picker("Primary Text", value=base_colors["text_primary"])
                text_secondary = st.color_picker("Secondary Text", value=base_colors["text_secondary"])
                border = st.color_picker("Border Color", value=base_colors["border"])

                # Gradient settings
                st.markdown("**Gradient Settings**")
                col_grad1, col_grad2 = st.columns(2)
                with col_grad1:
                    gradient_start = st.color_picker("Gradient Start", value=primary)
                    gradient_direction = st.selectbox(
                        "Gradient Direction",
                        options=["45deg", "90deg", "135deg", "180deg", "to right", "to bottom"],
                        index=2
                    )
                with col_grad2:
                    gradient_end = st.color_picker("Gradient End", value=secondary)

        with col2:
            st.subheader("Typography & Layout")

            # Font selection
            font_provider = st.selectbox(
                "Font Provider",
                options=[fp.value for fp in FontProvider],
                help="Choose font source"
            )

            if font_provider == FontProvider.GOOGLE_FONTS.value:
                font_family = st.selectbox(
                    "Font Family",
                    options=[
                        "Inter", "Roboto", "Poppins", "Lato", "Open Sans",
                        "Montserrat", "Source Sans Pro", "Nunito", "Ubuntu", "Raleway"
                    ],
                    help="Google Fonts selection"
                )
            else:
                font_family = st.text_input(
                    "Font Family",
                    value="Inter, sans-serif",
                    help="CSS font family declaration"
                )

            # Typography scales
            font_scale = st.slider(
                "Font Size Scale",
                min_value=0.8,
                max_value=1.5,
                value=1.0,
                step=0.1,
                help="Scale all font sizes"
            )

            line_height = st.slider(
                "Line Height",
                min_value=1.2,
                max_value=2.0,
                value=1.5,
                step=0.1,
                help="Text line spacing"
            )

            # Layout customization
            st.markdown("**Layout Options**")

            border_radius_scale = st.slider(
                "Border Radius Scale",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Scale for rounded corners"
            )

            shadow_intensity = st.slider(
                "Shadow Intensity",
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Intensity of drop shadows"
            )

            spacing_scale = st.slider(
                "Spacing Scale",
                min_value=0.8,
                max_value=1.5,
                value=1.0,
                step=0.1,
                help="Scale for margins and padding"
            )

            # Branding options
            with st.expander("🏢 Branding Options"):
                logo_url = st.text_input(
                    "Logo URL",
                    placeholder="https://example.com/logo.png",
                    help="URL to your logo image"
                )

                company_name = st.text_input(
                    "Company Name",
                    placeholder="Your Company",
                    help="Company name to display"
                )

                tagline = st.text_input(
                    "Tagline",
                    placeholder="Your company tagline",
                    help="Optional tagline"
                )

            # Auto-switch settings
            with st.expander("🌙 Auto Theme Switching"):
                auto_switch_mode = st.selectbox(
                    "Auto Switch Mode",
                    options=[mode.value for mode in AutoSwitchMode],
                    help="Automatic theme switching"
                )

                if auto_switch_mode == AutoSwitchMode.TIME_BASED.value:
                    col_time1, col_time2 = st.columns(2)
                    with col_time1:
                        light_start = st.time_input(
                            "Light Theme Start",
                            value=datetime.strptime("06:00", "%H:%M").time(),
                            help="When to switch to light theme"
                        )
                    with col_time2:
                        dark_start = st.time_input(
                            "Dark Theme Start",
                            value=datetime.strptime("18:00", "%H:%M").time(),
                            help="When to switch to dark theme"
                        )

        # Preview and save section
        st.subheader("Preview & Save")

        col_prev, col_save = st.columns([3, 1])

        with col_prev:
            if st.button("🔍 Preview Theme", use_container_width=True):
                # Create temporary theme for preview
                preview_theme = self._create_theme_from_inputs(
                    theme_name or "Preview Theme",
                    description, author, category, tags,
                    primary, secondary, accent, success, warning, danger, info,
                    background, surface, text_primary, text_secondary, border,
                    gradient_start, gradient_end, gradient_direction,
                    font_family, font_scale, line_height,
                    border_radius_scale, shadow_intensity, spacing_scale,
                    logo_url, company_name, tagline,
                    auto_switch_mode, getattr(locals().get('light_start'), 'strftime', lambda x: "06:00")("%H:%M"),
                    getattr(locals().get('dark_start'), 'strftime', lambda x: "18:00")("%H:%M")
                )

                st.session_state.current_custom_theme = preview_theme
                st.session_state.theme_preview_mode = True
                st.rerun()

        with col_save:
            if st.button("💾 Save Theme", use_container_width=True, type="primary"):
                if not theme_name:
                    st.error("Please enter a theme name")
                else:
                    try:
                        # Create and save theme
                        new_theme = self._create_theme_from_inputs(
                            theme_name, description, author, category, tags,
                            primary, secondary, accent, success, warning, danger, info,
                            background, surface, text_primary, text_secondary, border,
                            gradient_start, gradient_end, gradient_direction,
                            font_family, font_scale, line_height,
                            border_radius_scale, shadow_intensity, spacing_scale,
                            logo_url, company_name, tagline,
                            auto_switch_mode, getattr(locals().get('light_start'), 'strftime', lambda x: "06:00")("%H:%M"),
                            getattr(locals().get('dark_start'), 'strftime', lambda x: "18:00")("%H:%M")
                        )

                        self.advanced_manager.save_theme(new_theme)
                        st.success(f"Theme '{theme_name}' saved successfully!")

                    except Exception as e:
                        st.error(f"Error saving theme: {e}")

        # Live preview section
        if st.session_state.theme_preview_mode and st.session_state.current_custom_theme:
            self._render_theme_preview(st.session_state.current_custom_theme)

    def _render_theme_gallery(self):
        """Render theme gallery with all available themes"""
        st.header("Theme Gallery")

        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search_query = st.text_input(
                "🔍 Search themes",
                placeholder="Search by name, description, or tags"
            )

        with col2:
            category_filter = st.selectbox(
                "Category",
                options=["All"] + ["professional", "creative", "accessibility", "financial", "custom"]
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=["Name", "Created Date", "Category", "Author"]
            )

        # Get and filter themes
        all_themes = self.advanced_manager.get_all_themes()

        if search_query:
            all_themes = self.advanced_manager.search_themes(search_query)

        if category_filter != "All":
            all_themes = {name: theme for name, theme in all_themes.items()
                         if theme.metadata.category == category_filter}

        # Display themes in grid
        if all_themes:
            cols = st.columns(3)
            for idx, (theme_name, theme) in enumerate(all_themes.items()):
                col = cols[idx % 3]

                with col:
                    self._render_theme_card(theme_name, theme)
        else:
            st.info("No themes found matching your criteria.")

        # Default themes section
        st.subheader("Create Default Themes")
        if st.button("📦 Generate Default Themes"):
            default_themes = create_default_themes()
            for theme in default_themes.values():
                self.advanced_manager.save_theme(theme)
            st.success(f"Created {len(default_themes)} default themes!")
            st.rerun()

    def _render_edit_theme(self):
        """Render theme editing interface"""
        st.header("Edit Existing Theme")

        all_themes = self.advanced_manager.get_all_themes()

        if not all_themes:
            st.info("No custom themes available. Create one first!")
            return

        # Theme selection
        selected_theme_name = st.selectbox(
            "Select theme to edit",
            options=list(all_themes.keys()),
            help="Choose a theme to modify"
        )

        if selected_theme_name:
            theme = all_themes[selected_theme_name]

            # Show current theme info
            st.subheader("Current Theme Information")
            col1, col2 = st.columns(2)

            with col1:
                st.text(f"**Name:** {theme.metadata.name}")
                st.text(f"**Author:** {theme.metadata.author}")
                st.text(f"**Category:** {theme.metadata.category}")

            with col2:
                st.text(f"**Version:** {theme.metadata.version}")
                st.text(f"**Created:** {theme.metadata.created_date[:10]}")
                st.text(f"**Tags:** {', '.join(theme.metadata.tags)}")

            # Edit options
            st.subheader("Edit Options")

            edit_type = st.radio(
                "What would you like to do?",
                options=[
                    "Modify colors",
                    "Change typography",
                    "Update branding",
                    "Edit metadata",
                    "Duplicate theme",
                    "Delete theme"
                ]
            )

            if edit_type == "Modify colors":
                self._render_color_editor(theme)
            elif edit_type == "Change typography":
                self._render_typography_editor(theme)
            elif edit_type == "Update branding":
                self._render_branding_editor(theme)
            elif edit_type == "Edit metadata":
                self._render_metadata_editor(theme)
            elif edit_type == "Duplicate theme":
                self._render_theme_duplicator(theme)
            elif edit_type == "Delete theme":
                self._render_theme_deleter(theme)

    def _render_community_themes(self):
        """Render community theme sharing interface"""
        st.header("Community Themes")

        tab1, tab2, tab3 = st.tabs([
            "📥 Import Theme",
            "📤 Export Theme",
            "🌟 Featured Themes"
        ])

        with tab1:
            st.subheader("Import Theme from JSON")

            import_method = st.radio(
                "Import method",
                options=["Paste JSON", "Upload File"]
            )

            if import_method == "Paste JSON":
                theme_json = st.text_area(
                    "Theme JSON",
                    height=200,
                    placeholder="Paste theme JSON here..."
                )

                if st.button("Import Theme") and theme_json:
                    try:
                        imported_theme = self.advanced_manager.import_theme(theme_json, is_community=True)
                        st.success(f"Successfully imported theme: {imported_theme.metadata.name}")
                    except Exception as e:
                        st.error(f"Error importing theme: {e}")

            else:
                uploaded_file = st.file_uploader(
                    "Upload theme file",
                    type=['json'],
                    help="Upload a .json theme file"
                )

                if uploaded_file and st.button("Import Uploaded Theme"):
                    try:
                        theme_json = uploaded_file.read().decode('utf-8')
                        imported_theme = self.advanced_manager.import_theme(theme_json, is_community=True)
                        st.success(f"Successfully imported theme: {imported_theme.metadata.name}")
                    except Exception as e:
                        st.error(f"Error importing theme: {e}")

        with tab2:
            st.subheader("Export Theme for Sharing")

            all_themes = self.advanced_manager.get_all_themes()
            if all_themes:
                export_theme_name = st.selectbox(
                    "Select theme to export",
                    options=list(all_themes.keys())
                )

                if export_theme_name:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("📋 Copy to Clipboard"):
                            theme_json = self.advanced_manager.export_theme(export_theme_name)
                            st.code(theme_json, language='json')
                            st.info("Copy the JSON above to share your theme")

                    with col2:
                        if st.button("💾 Download as File"):
                            theme_json = self.advanced_manager.export_theme(export_theme_name)
                            st.download_button(
                                label="Download Theme JSON",
                                data=theme_json,
                                file_name=f"{export_theme_name.lower().replace(' ', '_')}.json",
                                mime="application/json"
                            )

        with tab3:
            st.subheader("Featured Community Themes")
            st.info("Community theme sharing features will be available in a future update!")

    def _render_theme_settings(self):
        """Render theme system settings"""
        st.header("Theme System Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Auto-Switch Settings")

            global_auto_switch = st.checkbox(
                "Enable Global Auto-Switch",
                help="Override individual theme auto-switch settings"
            )

            if global_auto_switch:
                global_switch_mode = st.selectbox(
                    "Global Switch Mode",
                    options=[mode.value for mode in AutoSwitchMode if mode != AutoSwitchMode.DISABLED]
                )

        with col2:
            st.subheader("Performance Settings")

            enable_preview = st.checkbox(
                "Enable Live Preview",
                value=True,
                help="Show live preview when customizing themes"
            )

            cache_themes = st.checkbox(
                "Cache Themes",
                value=True,
                help="Cache theme data for better performance"
            )

        st.subheader("Theme Management")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🧹 Clear Cache"):
                st.info("Theme cache cleared!")

        with col2:
            if st.button("🔄 Reload Themes"):
                self.advanced_manager._load_themes()
                st.success("Themes reloaded!")

        with col3:
            if st.button("📁 Open Themes Folder"):
                st.info(f"Themes stored in: {self.advanced_manager.themes_dir}")

        # Export/Import all themes
        st.subheader("Backup & Restore")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📦 Export All Themes"):
                all_themes = self.advanced_manager.get_all_themes()
                if all_themes:
                    backup_data = {}
                    for name, theme in all_themes.items():
                        backup_data[name] = self.advanced_manager.export_theme(name)

                    backup_json = json.dumps(backup_data, indent=2)
                    st.download_button(
                        label="Download Themes Backup",
                        data=backup_json,
                        file_name=f"themes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

        with col2:
            backup_file = st.file_uploader(
                "Upload themes backup",
                type=['json'],
                help="Restore themes from backup file"
            )

            if backup_file and st.button("📥 Restore Themes"):
                try:
                    backup_data = json.loads(backup_file.read().decode('utf-8'))
                    imported_count = 0

                    for theme_name, theme_json in backup_data.items():
                        try:
                            self.advanced_manager.import_theme(theme_json)
                            imported_count += 1
                        except Exception as e:
                            st.warning(f"Failed to import {theme_name}: {e}")

                    st.success(f"Successfully imported {imported_count} themes!")

                except Exception as e:
                    st.error(f"Error restoring themes: {e}")

    def _render_theme_card(self, theme_name: str, theme: AdvancedTheme):
        """Render a theme preview card"""
        with st.container():
            # Theme header with colors
            colors = theme.color_palette
            st.markdown(f"""
            <div style="
                background: {colors.get_gradient_css()};
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                color: white;
                text-align: center;
            ">
                <h4 style="margin: 0; color: white;">{theme_name}</h4>
                <small style="opacity: 0.9;">{theme.metadata.category}</small>
            </div>
            """, unsafe_allow_html=True)

            # Theme info
            st.markdown(f"**Author:** {theme.metadata.author}")
            st.markdown(f"**Description:** {theme.metadata.description}")

            if theme.metadata.tags:
                tags_html = " ".join([f'<span style="background: {colors.primary}20; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{tag}</span>' for tag in theme.metadata.tags])
                st.markdown(tags_html, unsafe_allow_html=True)

            # Color palette preview
            st.markdown("**Colors:**")
            color_preview = f"""
            <div style="display: flex; gap: 4px; margin: 0.5rem 0;">
                <div style="width: 20px; height: 20px; background: {colors.primary}; border-radius: 4px;"></div>
                <div style="width: 20px; height: 20px; background: {colors.secondary}; border-radius: 4px;"></div>
                <div style="width: 20px; height: 20px; background: {colors.accent}; border-radius: 4px;"></div>
                <div style="width: 20px; height: 20px; background: {colors.success}; border-radius: 4px;"></div>
                <div style="width: 20px; height: 20px; background: {colors.warning}; border-radius: 4px;"></div>
            </div>
            """
            st.markdown(color_preview, unsafe_allow_html=True)

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"🎨 Apply", key=f"apply_{theme_name}"):
                    # Convert to standard theme and apply
                    standard_theme = theme.to_dashboard_theme()
                    st.session_state.selected_theme = theme_name
                    st.success(f"Applied theme: {theme_name}")

            with col2:
                if st.button(f"📁 Edit", key=f"edit_{theme_name}"):
                    st.session_state.edit_theme = theme_name
                    st.info(f"Switch to Edit tab to modify {theme_name}")

    def _render_theme_preview(self, theme: AdvancedTheme):
        """Render live theme preview"""
        st.subheader("🔍 Theme Preview")

        # Apply theme temporarily
        standard_theme = theme.to_dashboard_theme()
        css = self.standard_manager.generate_css(standard_theme)

        st.markdown(css, unsafe_allow_html=True)

        # Preview content
        st.markdown("### Sample Dashboard Content")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Revenue", "$125.2M", "+12.3%")

        with col2:
            st.metric("Profit Margin", "18.5%", "-2.1pp")

        with col3:
            st.metric("ROE", "15.2%", "+1.8pp")

        with col4:
            st.metric("Debt/Equity", "0.45", "No change")

        # Sample chart
        import plotly.graph_objects as go
        import pandas as pd
        import numpy as np

        dates = pd.date_range('2023-01-01', periods=12, freq='M')
        revenue = np.cumsum(np.random.randn(12) * 10 + 100) + 1000

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=revenue,
            name='Revenue',
            line_color=theme.color_palette.primary
        ))

        fig.update_layout(
            title="Sample Financial Chart",
            paper_bgcolor=theme.color_palette.background,
            plot_bgcolor=theme.color_palette.surface,
            font_color=theme.color_palette.text_primary
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exit preview
        if st.button("❌ Exit Preview"):
            st.session_state.theme_preview_mode = False
            st.session_state.current_custom_theme = None
            st.rerun()

    def _create_theme_from_inputs(self, name, description, author, category, tags,
                                primary, secondary, accent, success, warning, danger, info,
                                background, surface, text_primary, text_secondary, border,
                                gradient_start, gradient_end, gradient_direction,
                                font_family, font_scale, line_height,
                                border_radius_scale, shadow_intensity, spacing_scale,
                                logo_url, company_name, tagline,
                                auto_switch_mode, light_start, dark_start) -> AdvancedTheme:
        """Create AdvancedTheme from UI inputs"""

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

        # Create metadata
        metadata = ThemeMetadata(
            name=name,
            description=description,
            author=author,
            category=category,
            tags=tag_list
        )

        # Create color palette
        color_palette = AdvancedColorPalette(
            primary=primary,
            secondary=secondary,
            accent=accent,
            success=success,
            warning=warning,
            danger=danger,
            info=info,
            background=background,
            surface=surface,
            text_primary=text_primary,
            text_secondary=text_secondary,
            border=border,
            hover=background,
            disabled=border,
            gradient_start=gradient_start,
            gradient_end=gradient_end,
            gradient_direction=gradient_direction
        )

        # Create custom font
        custom_font = CustomFont(
            name=font_family,
            family=font_family,
            provider=FontProvider.GOOGLE_FONTS
        )

        # Create branding
        branding = BrandingSettings(
            logo_url=logo_url or None,
            company_name=company_name,
            tagline=tagline
        )

        # Create auto-switch settings
        auto_switch = AutoSwitchSettings(
            mode=AutoSwitchMode(auto_switch_mode),
            light_theme_start=light_start,
            dark_theme_start=dark_start
        )

        return AdvancedTheme(
            metadata=metadata,
            color_palette=color_palette,
            custom_font=custom_font,
            branding=branding,
            auto_switch=auto_switch,
            font_scale=font_scale,
            line_height=line_height,
            border_radius_scale=border_radius_scale,
            shadow_intensity=shadow_intensity,
            spacing_scale=spacing_scale
        )

    def _get_preset_colors(self, preset: str) -> Dict[str, str]:
        """Get preset color palette"""
        presets = {
            "Custom": {
                "primary": "#1E40AF",
                "secondary": "#3B82F6",
                "accent": "#8B5CF6",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "info": "#06B6D4",
                "background": "#FFFFFF",
                "surface": "#F9FAFB",
                "text_primary": "#111827",
                "text_secondary": "#6B7280",
                "border": "#E5E7EB"
            },
            "Professional Blue": {
                "primary": "#1E40AF",
                "secondary": "#3B82F6",
                "accent": "#60A5FA",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "info": "#06B6D4",
                "background": "#FFFFFF",
                "surface": "#F8FAFC",
                "text_primary": "#0F172A",
                "text_secondary": "#475569",
                "border": "#CBD5E1"
            },
            "Financial Green": {
                "primary": "#059669",
                "secondary": "#10B981",
                "accent": "#34D399",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#DC2626",
                "info": "#0891B2",
                "background": "#FFFFFF",
                "surface": "#F0FDF4",
                "text_primary": "#064E3B",
                "text_secondary": "#047857",
                "border": "#D1FAE5"
            },
            "Creative Purple": {
                "primary": "#7C3AED",
                "secondary": "#A855F7",
                "accent": "#C084FC",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "info": "#06B6D4",
                "background": "#FFFFFF",
                "surface": "#FAF5FF",
                "text_primary": "#581C87",
                "text_secondary": "#7C3AED",
                "border": "#DDD6FE"
            },
            "Minimal Gray": {
                "primary": "#374151",
                "secondary": "#6B7280",
                "accent": "#9CA3AF",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "info": "#06B6D4",
                "background": "#FFFFFF",
                "surface": "#F9FAFB",
                "text_primary": "#111827",
                "text_secondary": "#6B7280",
                "border": "#E5E7EB"
            }
        }

        return presets.get(preset, presets["Custom"])

    def _render_color_editor(self, theme: AdvancedTheme):
        """Render color editing interface"""
        st.subheader("Edit Colors")
        # Implementation for color editing
        st.info("Color editing interface - implementation in progress")

    def _render_typography_editor(self, theme: AdvancedTheme):
        """Render typography editing interface"""
        st.subheader("Edit Typography")
        # Implementation for typography editing
        st.info("Typography editing interface - implementation in progress")

    def _render_branding_editor(self, theme: AdvancedTheme):
        """Render branding editing interface"""
        st.subheader("Edit Branding")
        # Implementation for branding editing
        st.info("Branding editing interface - implementation in progress")

    def _render_metadata_editor(self, theme: AdvancedTheme):
        """Render metadata editing interface"""
        st.subheader("Edit Metadata")
        # Implementation for metadata editing
        st.info("Metadata editing interface - implementation in progress")

    def _render_theme_duplicator(self, theme: AdvancedTheme):
        """Render theme duplication interface"""
        st.subheader("Duplicate Theme")

        new_name = st.text_input(
            "New theme name",
            value=f"{theme.metadata.name} Copy"
        )

        if st.button("Create Duplicate") and new_name:
            try:
                duplicate_theme = self.advanced_manager.duplicate_theme(theme.metadata.name, new_name)
                self.advanced_manager.save_theme(duplicate_theme)
                st.success(f"Created duplicate theme: {new_name}")
            except Exception as e:
                st.error(f"Error duplicating theme: {e}")

    def _render_theme_deleter(self, theme: AdvancedTheme):
        """Render theme deletion interface"""
        st.subheader("Delete Theme")

        st.warning(f"Are you sure you want to delete the theme '{theme.metadata.name}'? This action cannot be undone.")

        confirm_name = st.text_input(
            "Type the theme name to confirm deletion",
            placeholder=theme.metadata.name
        )

        if st.button("🗑️ Delete Theme", type="primary"):
            if confirm_name == theme.metadata.name:
                try:
                    self.advanced_manager.delete_theme(theme.metadata.name)
                    st.success(f"Deleted theme: {theme.metadata.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting theme: {e}")
            else:
                st.error("Theme name doesn't match. Please type the exact name to confirm.")


# Convenience function for integration
def render_advanced_theme_customization():
    """Render the advanced theme customization UI"""
    ui = ThemeCustomizationUI()
    ui.render()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Advanced Theme Customization",
        page_icon="🎨",
        layout="wide"
    )

    render_advanced_theme_customization()