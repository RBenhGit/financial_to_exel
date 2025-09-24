"""
Theme Preview System
===================

Real-time theme preview functionality with live updates
and integration with the main application interface.
"""

import streamlit as st
import json
from typing import Dict, List, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .advanced_theme_customization import AdvancedTheme, AdvancedColorPalette
from .dashboard_themes import ThemeManager


class ThemePreviewSystem:
    """System for previewing themes with live updates"""

    def __init__(self):
        self.theme_manager = ThemeManager()

    def render_live_preview(self, theme: AdvancedTheme, preview_type: str = "comprehensive"):
        """Render live preview of a theme"""
        st.subheader("🔍 Live Theme Preview")

        # Apply theme CSS
        css = self._generate_theme_css(theme)
        st.markdown(css, unsafe_allow_html=True)

        # Preview tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard",
            "📈 Charts",
            "🎨 Components",
            "📱 Layout"
        ])

        with tab1:
            self._render_dashboard_preview(theme)

        with tab2:
            self._render_charts_preview(theme)

        with tab3:
            self._render_components_preview(theme)

        with tab4:
            self._render_layout_preview(theme)

        # Theme info sidebar
        with st.sidebar:
            self._render_theme_info_sidebar(theme)

    def _generate_theme_css(self, theme: AdvancedTheme) -> str:
        """Generate comprehensive CSS for theme preview"""
        colors = theme.color_palette
        font_family = theme.custom_font.family if theme.custom_font else "Inter, sans-serif"

        # Import custom font if needed
        font_import = ""
        if theme.custom_font and theme.custom_font.provider.value == "google":
            font_import = f'@import url("{theme.custom_font.get_font_url()}");'

        # Calculate scaled values
        base_border_radius = 8 * theme.border_radius_scale
        base_spacing = 1 * theme.spacing_scale

        return f"""
        <style>
        {font_import}

        /* CSS Custom Properties */
        :root {{
            --theme-primary: {colors.primary};
            --theme-secondary: {colors.secondary};
            --theme-accent: {colors.accent};
            --theme-success: {colors.success};
            --theme-warning: {colors.warning};
            --theme-danger: {colors.danger};
            --theme-info: {colors.info};
            --theme-background: {colors.background};
            --theme-surface: {colors.surface};
            --theme-text-primary: {colors.text_primary};
            --theme-text-secondary: {colors.text_secondary};
            --theme-border: {colors.border};
            --theme-hover: {colors.hover};
            --theme-gradient: {colors.get_gradient_css()};

            --theme-font-family: {font_family};
            --theme-font-scale: {theme.font_scale};
            --theme-line-height: {theme.line_height};
            --theme-border-radius: {base_border_radius}px;
            --theme-spacing: {base_spacing}rem;
            --theme-shadow-intensity: {theme.shadow_intensity};
        }}

        /* Global Overrides */
        .stApp {{
            background-color: var(--theme-background);
            color: var(--theme-text-primary);
            font-family: var(--theme-font-family);
            line-height: var(--theme-line-height);
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--theme-text-primary);
            font-family: var(--theme-font-family);
        }}

        h1 {{ font-size: calc(2.5rem * var(--theme-font-scale)); }}
        h2 {{ font-size: calc(2rem * var(--theme-font-scale)); }}
        h3 {{ font-size: calc(1.5rem * var(--theme-font-scale)); }}

        /* Preview-specific components */
        .preview-header {{
            background: var(--theme-gradient);
            color: white;
            padding: calc(var(--theme-spacing) * 2);
            border-radius: var(--theme-border-radius);
            margin-bottom: var(--theme-spacing);
            box-shadow: 0 4px 12px rgba(0,0,0,calc(0.1 * var(--theme-shadow-intensity)));
            text-align: center;
        }}

        .preview-metric-card {{
            background: var(--theme-surface);
            border: 1px solid var(--theme-border);
            border-radius: var(--theme-border-radius);
            padding: var(--theme-spacing);
            margin: calc(var(--theme-spacing) * 0.5);
            box-shadow: 0 2px 8px rgba(0,0,0,calc(0.05 * var(--theme-shadow-intensity)));
            transition: all 0.3s ease;
        }}

        .preview-metric-card:hover {{
            background: var(--theme-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,calc(0.1 * var(--theme-shadow-intensity)));
        }}

        .preview-metric-value {{
            font-size: calc(2rem * var(--theme-font-scale));
            font-weight: 700;
            color: var(--theme-primary);
            margin: calc(var(--theme-spacing) * 0.5) 0;
        }}

        .preview-metric-label {{
            font-size: calc(0.875rem * var(--theme-font-scale));
            color: var(--theme-text-secondary);
            margin-bottom: calc(var(--theme-spacing) * 0.25);
            font-weight: 500;
        }}

        .preview-metric-positive {{
            color: var(--theme-success);
            font-weight: 600;
        }}

        .preview-metric-negative {{
            color: var(--theme-danger);
            font-weight: 600;
        }}

        .preview-panel {{
            background: var(--theme-surface);
            border: 1px solid var(--theme-border);
            border-radius: var(--theme-border-radius);
            padding: calc(var(--theme-spacing) * 1.5);
            margin: var(--theme-spacing) 0;
            box-shadow: 0 2px 8px rgba(0,0,0,calc(0.05 * var(--theme-shadow-intensity)));
        }}

        .preview-panel-title {{
            color: var(--theme-primary);
            font-size: calc(1.25rem * var(--theme-font-scale));
            font-weight: 600;
            margin-bottom: var(--theme-spacing);
            border-bottom: 2px solid var(--theme-primary);
            padding-bottom: calc(var(--theme-spacing) * 0.5);
        }}

        .preview-button {{
            background: var(--theme-primary);
            color: white;
            border: none;
            border-radius: var(--theme-border-radius);
            padding: calc(var(--theme-spacing) * 0.5) var(--theme-spacing);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: var(--theme-font-family);
        }}

        .preview-button:hover {{
            background: var(--theme-secondary);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,calc(0.2 * var(--theme-shadow-intensity)));
        }}

        .preview-alert-success {{
            background: color-mix(in srgb, var(--theme-success) 10%, transparent);
            border-left: 4px solid var(--theme-success);
            padding: var(--theme-spacing);
            border-radius: var(--theme-border-radius);
            margin: calc(var(--theme-spacing) * 0.5) 0;
        }}

        .preview-alert-warning {{
            background: color-mix(in srgb, var(--theme-warning) 10%, transparent);
            border-left: 4px solid var(--theme-warning);
            padding: var(--theme-spacing);
            border-radius: var(--theme-border-radius);
            margin: calc(var(--theme-spacing) * 0.5) 0;
        }}

        .preview-alert-danger {{
            background: color-mix(in srgb, var(--theme-danger) 10%, transparent);
            border-left: 4px solid var(--theme-danger);
            padding: var(--theme-spacing);
            border-radius: var(--theme-border-radius);
            margin: calc(var(--theme-spacing) * 0.5) 0;
        }}

        .preview-tag {{
            background: var(--theme-primary);
            color: white;
            padding: calc(var(--theme-spacing) * 0.25) calc(var(--theme-spacing) * 0.5);
            border-radius: calc(var(--theme-border-radius) * 0.5);
            font-size: calc(0.75rem * var(--theme-font-scale));
            margin: calc(var(--theme-spacing) * 0.25);
            display: inline-block;
        }}

        .preview-table {{
            background: var(--theme-surface);
            border: 1px solid var(--theme-border);
            border-radius: var(--theme-border-radius);
            overflow: hidden;
            margin: var(--theme-spacing) 0;
        }}

        .preview-table th {{
            background: var(--theme-primary);
            color: white;
            padding: calc(var(--theme-spacing) * 0.75);
            text-align: left;
            font-weight: 600;
        }}

        .preview-table td {{
            padding: calc(var(--theme-spacing) * 0.75);
            border-bottom: 1px solid var(--theme-border);
        }}

        .preview-table tr:hover {{
            background: var(--theme-hover);
        }}

        /* Branding elements */
        .preview-logo {{
            max-height: 48px;
            margin-right: var(--theme-spacing);
        }}

        .preview-company-name {{
            font-size: calc(1.5rem * var(--theme-font-scale));
            font-weight: 700;
            color: white;
        }}

        .preview-tagline {{
            font-size: calc(0.875rem * var(--theme-font-scale));
            opacity: 0.9;
            color: white;
        }}
        </style>
        """

    def _render_dashboard_preview(self, theme: AdvancedTheme):
        """Render dashboard preview with theme"""
        colors = theme.color_palette

        # Header with branding
        header_content = ""
        if theme.branding.show_logo_in_header and theme.branding.logo_url:
            header_content += f'<img src="{theme.branding.logo_url}" class="preview-logo">'

        if theme.branding.show_company_name and theme.branding.company_name:
            header_content += f'<div class="preview-company-name">{theme.branding.company_name}</div>'

        if theme.branding.tagline:
            header_content += f'<div class="preview-tagline">{theme.branding.tagline}</div>'

        if not header_content:
            header_content = '<div class="preview-company-name">Financial Analysis Dashboard</div><div class="preview-tagline">Advanced Theme Preview</div>'

        st.markdown(f"""
        <div class="preview-header">
            {header_content}
        </div>
        """, unsafe_allow_html=True)

        # Key metrics
        st.markdown("### 📊 Key Financial Metrics")

        col1, col2, col3, col4 = st.columns(4)

        metrics_data = [
            ("Revenue", "$2.5B", "+15.3%", True),
            ("Net Income", "$450M", "+8.7%", True),
            ("Debt/Equity", "0.65", "-5.2%", False),
            ("ROE", "18.2%", "+2.1pp", True)
        ]

        for i, (col, (label, value, change, positive)) in enumerate(zip([col1, col2, col3, col4], metrics_data)):
            change_class = "preview-metric-positive" if positive else "preview-metric-negative"
            with col:
                st.markdown(f"""
                <div class="preview-metric-card">
                    <div class="preview-metric-label">{label}</div>
                    <div class="preview-metric-value">{value}</div>
                    <div class="{change_class}">{change}</div>
                </div>
                """, unsafe_allow_html=True)

        # Status alerts
        st.markdown("### 🚨 Status Alerts")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="preview-alert-success">
                <strong>✅ Good:</strong> Cash flow is strong and improving
            </div>
            <div class="preview-alert-warning">
                <strong>⚠️ Warning:</strong> P/E ratio above industry average
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="preview-alert-danger">
                <strong>🚨 Alert:</strong> Debt levels increasing rapidly
            </div>
            <div class="preview-panel">
                <div class="preview-panel-title">💡 Insights</div>
                <p>The company shows strong fundamentals with room for improvement in debt management.</p>
            </div>
            """, unsafe_allow_html=True)

        # Sample data table
        st.markdown("### 📋 Financial Data")

        sample_data = pd.DataFrame({
            'Quarter': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
            'Revenue': ['$615M', '$642M', '$678M', '$695M'],
            'Growth': ['+12.3%', '+15.1%', '+18.2%', '+16.8%'],
            'Margin': ['16.2%', '17.1%', '18.5%', '17.9%']
        })

        # Custom styled table
        table_html = """
        <div class="preview-table">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th>Quarter</th>
                        <th>Revenue</th>
                        <th>Growth</th>
                        <th>Margin</th>
                    </tr>
                </thead>
                <tbody>
        """

        for _, row in sample_data.iterrows():
            table_html += f"""
                <tr>
                    <td>{row['Quarter']}</td>
                    <td>{row['Revenue']}</td>
                    <td class="preview-metric-positive">{row['Growth']}</td>
                    <td>{row['Margin']}</td>
                </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)

    def _render_charts_preview(self, theme: AdvancedTheme):
        """Render charts with theme colors"""
        colors = theme.color_palette
        st.markdown("### 📈 Chart Visualizations")

        # Generate sample data
        dates = pd.date_range('2023-01-01', periods=12, freq='M')
        np.random.seed(42)  # For consistent demo data

        # Revenue trend chart
        revenue_data = np.cumsum(np.random.randn(12) * 50 + 200) + 2000
        profit_data = revenue_data * (0.18 + np.random.randn(12) * 0.03)

        col1, col2 = st.columns(2)

        with col1:
            # Line chart
            fig_line = go.Figure()

            fig_line.add_trace(go.Scatter(
                x=dates,
                y=revenue_data,
                name='Revenue',
                line=dict(color=colors.primary, width=3),
                mode='lines+markers'
            ))

            fig_line.add_trace(go.Scatter(
                x=dates,
                y=profit_data,
                name='Profit',
                line=dict(color=colors.success, width=3),
                mode='lines+markers'
            ))

            fig_line.update_layout(
                title="Revenue & Profit Trends",
                paper_bgcolor=colors.background,
                plot_bgcolor=colors.surface,
                font=dict(family=theme.custom_font.family if theme.custom_font else "Inter",
                         color=colors.text_primary),
                title_font_size=int(16 * theme.font_scale),
                xaxis=dict(gridcolor=colors.border, linecolor=colors.border),
                yaxis=dict(gridcolor=colors.border, linecolor=colors.border),
                legend=dict(bgcolor=colors.surface, bordercolor=colors.border)
            )

            st.plotly_chart(fig_line, use_container_width=True)

        with col2:
            # Bar chart
            categories = ['Assets', 'Liabilities', 'Equity', 'Cash']
            values = [5200, 2800, 2400, 800]
            chart_colors = [colors.primary, colors.warning, colors.success, colors.info]

            fig_bar = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=values,
                    marker_color=chart_colors,
                    text=[f'${v}M' for v in values],
                    textposition='auto'
                )
            ])

            fig_bar.update_layout(
                title="Balance Sheet Overview",
                paper_bgcolor=colors.background,
                plot_bgcolor=colors.surface,
                font=dict(family=theme.custom_font.family if theme.custom_font else "Inter",
                         color=colors.text_primary),
                title_font_size=int(16 * theme.font_scale),
                xaxis=dict(gridcolor=colors.border, linecolor=colors.border),
                yaxis=dict(gridcolor=colors.border, linecolor=colors.border)
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        # Pie chart
        st.markdown("### 🥧 Portfolio Composition")

        portfolio_data = {
            'Technology': 35,
            'Healthcare': 20,
            'Financials': 18,
            'Consumer': 15,
            'Energy': 12
        }

        fig_pie = go.Figure(data=[
            go.Pie(
                labels=list(portfolio_data.keys()),
                values=list(portfolio_data.values()),
                hole=.3,
                marker_colors=colors.chart_colors_extended[:len(portfolio_data)]
            )
        ])

        fig_pie.update_layout(
            title="Sector Allocation",
            paper_bgcolor=colors.background,
            font=dict(family=theme.custom_font.family if theme.custom_font else "Inter",
                     color=colors.text_primary),
            title_font_size=int(16 * theme.font_scale)
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    def _render_components_preview(self, theme: AdvancedTheme):
        """Render individual UI components with theme"""
        st.markdown("### 🎨 UI Components Showcase")

        # Buttons
        st.markdown("**Buttons & Interactive Elements**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<button class="preview-button">Primary Button</button>', unsafe_allow_html=True)

        with col2:
            st.button("Streamlit Button")

        with col3:
            st.selectbox("Select Option", ["Option 1", "Option 2", "Option 3"])

        with col4:
            st.slider("Value", 0, 100, 50)

        # Tags and labels
        st.markdown("**Tags & Labels**")

        tags = ["Financial", "Analysis", "Dashboard", "Premium", "Custom Theme"]
        tags_html = "".join([f'<span class="preview-tag">{tag}</span>' for tag in tags])
        st.markdown(tags_html, unsafe_allow_html=True)

        # Progress indicators
        st.markdown("**Progress & Status Indicators**")

        col1, col2 = st.columns(2)

        with col1:
            st.progress(0.75)
            st.write("Loading Progress: 75%")

        with col2:
            # Custom status indicators
            st.markdown("""
            <div style="margin: 1rem 0;">
                <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                    <div style="width: 12px; height: 12px; background: var(--theme-success); border-radius: 50%; margin-right: 0.5rem;"></div>
                    <span>System Operational</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                    <div style="width: 12px; height: 12px; background: var(--theme-warning); border-radius: 50%; margin-right: 0.5rem;"></div>
                    <span>Minor Issues</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                    <div style="width: 12px; height: 12px; background: var(--theme-danger); border-radius: 50%; margin-right: 0.5rem;"></div>
                    <span>Critical Alert</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Form elements
        st.markdown("**Form Elements**")

        with st.form("preview_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.text_input("Company Ticker", value="AAPL")
                st.date_input("Analysis Date")

            with col2:
                st.number_input("Target Price", value=150.0)
                st.checkbox("Include Projections")

            submitted = st.form_submit_button("Analyze")

        # Color palette display
        st.markdown("**Color Palette**")

        color_data = {
            'Primary': theme.color_palette.primary,
            'Secondary': theme.color_palette.secondary,
            'Accent': theme.color_palette.accent,
            'Success': theme.color_palette.success,
            'Warning': theme.color_palette.warning,
            'Danger': theme.color_palette.danger,
            'Info': theme.color_palette.info
        }

        color_html = '<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;">'
        for name, color in color_data.items():
            color_html += f"""
            <div style="text-align: center;">
                <div style="width: 60px; height: 60px; background: {color}; border-radius: var(--theme-border-radius); margin-bottom: 0.5rem; border: 1px solid var(--theme-border);"></div>
                <div style="font-size: 0.75rem; color: var(--theme-text-secondary);">{name}</div>
                <div style="font-size: 0.7rem; font-family: monospace; color: var(--theme-text-secondary);">{color}</div>
            </div>
            """
        color_html += '</div>'

        st.markdown(color_html, unsafe_allow_html=True)

    def _render_layout_preview(self, theme: AdvancedTheme):
        """Render layout and spacing preview"""
        st.markdown("### 📱 Layout & Spacing")

        # Typography scale
        st.markdown("**Typography Scale**")

        typography_samples = [
            ("Heading 1", "h1", "The quick brown fox jumps"),
            ("Heading 2", "h2", "Over the lazy dog"),
            ("Heading 3", "h3", "Typography demonstration"),
            ("Body Text", "p", "This is regular body text with normal weight and spacing. It should be comfortable to read at the current font scale."),
            ("Small Text", "small", "This is smaller text used for captions and footnotes.")
        ]

        for label, tag, text in typography_samples:
            if tag.startswith('h'):
                st.markdown(f"**{label}:**")
                if tag == 'h1':
                    st.markdown(f"# {text}")
                elif tag == 'h2':
                    st.markdown(f"## {text}")
                elif tag == 'h3':
                    st.markdown(f"### {text}")
            else:
                st.markdown(f"**{label}:** {text}")

        # Spacing demonstration
        st.markdown("**Spacing & Layout**")

        # Create nested containers to show spacing
        st.markdown("""
        <div class="preview-panel">
            <div class="preview-panel-title">Container with Standard Spacing</div>
            <p>This container demonstrates the standard spacing values applied throughout the interface.</p>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--theme-spacing); margin: var(--theme-spacing) 0;">
                <div class="preview-metric-card">
                    <div class="preview-metric-label">Card 1</div>
                    <div class="preview-metric-value">$1,234</div>
                </div>
                <div class="preview-metric-card">
                    <div class="preview-metric-label">Card 2</div>
                    <div class="preview-metric-value">$5,678</div>
                </div>
            </div>

            <p>Notice how the spacing scales consistently with the theme settings.</p>
        </div>
        """, unsafe_allow_html=True)

        # Border radius demonstration
        st.markdown("**Border Radius Scale**")

        radius_examples = [
            ("Small", 0.5),
            ("Medium", 1.0),
            ("Large", 1.5),
            ("Extra Large", 2.0)
        ]

        radius_html = '<div style="display: flex; gap: 1rem; margin: 1rem 0;">'
        for label, scale in radius_examples:
            radius_html += f"""
            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: var(--theme-primary);
                    border-radius: calc(var(--theme-border-radius) * {scale});
                    margin-bottom: 0.5rem;
                "></div>
                <div style="font-size: 0.75rem; color: var(--theme-text-secondary);">{label}</div>
            </div>
            """
        radius_html += '</div>'

        st.markdown(radius_html, unsafe_allow_html=True)

        # Shadow intensity
        st.markdown("**Shadow Intensity**")

        shadow_examples = [
            ("None", 0),
            ("Light", 0.5),
            ("Normal", 1.0),
            ("Heavy", 2.0)
        ]

        shadow_html = '<div style="display: flex; gap: 1rem; margin: 1rem 0;">'
        for label, intensity in shadow_examples:
            shadow_html += f"""
            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: var(--theme-surface);
                    border-radius: var(--theme-border-radius);
                    box-shadow: 0 4px 12px rgba(0,0,0,calc(0.1 * {intensity}));
                    margin-bottom: 0.5rem;
                    border: 1px solid var(--theme-border);
                "></div>
                <div style="font-size: 0.75rem; color: var(--theme-text-secondary);">{label}</div>
            </div>
            """
        shadow_html += '</div>'

        st.markdown(shadow_html, unsafe_allow_html=True)

    def _render_theme_info_sidebar(self, theme: AdvancedTheme):
        """Render theme information in sidebar"""
        st.markdown("### 🎨 Theme Details")

        st.markdown(f"**Name:** {theme.metadata.name}")
        st.markdown(f"**Author:** {theme.metadata.author}")
        st.markdown(f"**Category:** {theme.metadata.category}")

        if theme.metadata.description:
            st.markdown(f"**Description:** {theme.metadata.description}")

        if theme.metadata.tags:
            st.markdown(f"**Tags:** {', '.join(theme.metadata.tags)}")

        # Font information
        if theme.custom_font:
            st.markdown("### 📝 Typography")
            st.markdown(f"**Font Family:** {theme.custom_font.family}")
            st.markdown(f"**Font Scale:** {theme.font_scale}x")
            st.markdown(f"**Line Height:** {theme.line_height}")

        # Layout settings
        st.markdown("### 📐 Layout")
        st.markdown(f"**Border Radius Scale:** {theme.border_radius_scale}x")
        st.markdown(f"**Shadow Intensity:** {theme.shadow_intensity}x")
        st.markdown(f"**Spacing Scale:** {theme.spacing_scale}x")

        # Branding info
        if (theme.branding.company_name or theme.branding.logo_url or theme.branding.tagline):
            st.markdown("### 🏢 Branding")
            if theme.branding.company_name:
                st.markdown(f"**Company:** {theme.branding.company_name}")
            if theme.branding.tagline:
                st.markdown(f"**Tagline:** {theme.branding.tagline}")
            if theme.branding.logo_url:
                st.markdown(f"**Logo:** [View Logo]({theme.branding.logo_url})")

        # Auto-switch settings
        if theme.auto_switch.mode.value != "disabled":
            st.markdown("### 🌙 Auto-Switch")
            st.markdown(f"**Mode:** {theme.auto_switch.mode.value}")
            if theme.auto_switch.mode.value == "time_based":
                st.markdown(f"**Light Start:** {theme.auto_switch.light_theme_start}")
                st.markdown(f"**Dark Start:** {theme.auto_switch.dark_theme_start}")


def create_theme_preview_demo():
    """Create a standalone theme preview demo"""
    st.set_page_config(
        page_title="Theme Preview System",
        page_icon="🎨",
        layout="wide"
    )

    st.title("🎨 Theme Preview System Demo")

    # Load a sample theme for demo
    from .advanced_theme_customization import create_default_themes

    default_themes = create_default_themes()
    selected_theme_name = st.selectbox(
        "Select theme to preview",
        options=list(default_themes.keys())
    )

    if selected_theme_name:
        theme = default_themes[selected_theme_name]
        preview_system = ThemePreviewSystem()
        preview_system.render_live_preview(theme)


if __name__ == "__main__":
    create_theme_preview_demo()