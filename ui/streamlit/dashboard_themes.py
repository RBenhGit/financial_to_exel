"""
Dashboard Themes and Color Schemes
=================================

This module provides comprehensive theming and color scheme management
for the financial dashboard, supporting multiple themes and customization.
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import colorsys
import json


class ThemeMode(Enum):
    """Theme modes for the dashboard"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system preference


class ColorScheme(Enum):
    """Predefined color schemes"""
    PROFESSIONAL = "professional"  # Blue-based corporate theme
    FINANCIAL = "financial"        # Green/red financial theme
    MINIMAL = "minimal"           # Neutral grays
    VIBRANT = "vibrant"          # Colorful and energetic
    SUNSET = "sunset"            # Warm oranges and reds
    OCEAN = "ocean"              # Blues and teals
    FOREST = "forest"            # Greens and earth tones


@dataclass
class ColorPalette:
    """Color palette definition"""
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    danger: str
    info: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    border: str
    hover: str
    disabled: str

    # Financial-specific colors
    profit: str = "#10B981"      # Green for profits/gains
    loss: str = "#EF4444"        # Red for losses/declines
    neutral: str = "#6B7280"     # Gray for neutral values

    # Chart colors (for data visualization)
    chart_colors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.chart_colors:
            self.chart_colors = [
                self.primary, self.secondary, self.accent,
                self.success, self.warning, self.info
            ]


class DashboardTheme:
    """Complete dashboard theme including colors, typography, and spacing"""

    def __init__(self,
                 name: str,
                 mode: ThemeMode,
                 color_palette: ColorPalette,
                 font_family: str = "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                 font_sizes: Dict[str, str] = None,
                 spacing: Dict[str, str] = None,
                 border_radius: str = "8px",
                 shadows: Dict[str, str] = None):

        self.name = name
        self.mode = mode
        self.colors = color_palette
        self.font_family = font_family
        self.border_radius = border_radius

        self.font_sizes = font_sizes or {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem"
        }

        self.spacing = spacing or {
            "xs": "0.25rem",
            "sm": "0.5rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem",
            "2xl": "3rem"
        }

        self.shadows = shadows or {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
        }


class ThemeManager:
    """Manages theme selection and application"""

    def __init__(self):
        self.themes = self._initialize_themes()
        self.current_theme = self._get_current_theme()

    def _initialize_themes(self) -> Dict[str, DashboardTheme]:
        """Initialize all available themes"""
        themes = {}

        # Professional Light Theme
        professional_light = ColorPalette(
            primary="#1E40AF",
            secondary="#3B82F6",
            accent="#8B5CF6",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
            info="#06B6D4",
            background="#FFFFFF",
            surface="#F9FAFB",
            text_primary="#111827",
            text_secondary="#6B7280",
            border="#E5E7EB",
            hover="#F3F4F6",
            disabled="#D1D5DB"
        )

        themes["professional_light"] = DashboardTheme(
            name="Professional Light",
            mode=ThemeMode.LIGHT,
            color_palette=professional_light
        )

        # Professional Dark Theme
        professional_dark = ColorPalette(
            primary="#3B82F6",
            secondary="#60A5FA",
            accent="#A78BFA",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
            info="#06B6D4",
            background="#111827",
            surface="#1F2937",
            text_primary="#F9FAFB",
            text_secondary="#D1D5DB",
            border="#374151",
            hover="#374151",
            disabled="#4B5563"
        )

        themes["professional_dark"] = DashboardTheme(
            name="Professional Dark",
            mode=ThemeMode.DARK,
            color_palette=professional_dark
        )

        # Financial Theme (Green/Red focused)
        financial_light = ColorPalette(
            primary="#059669",
            secondary="#10B981",
            accent="#34D399",
            success="#10B981",
            warning="#F59E0B",
            danger="#DC2626",
            info="#0891B2",
            background="#FFFFFF",
            surface="#F0FDF4",
            text_primary="#064E3B",
            text_secondary="#6B7280",
            border="#D1FAE5",
            hover="#ECFDF5",
            disabled="#D1D5DB",
            profit="#10B981",
            loss="#DC2626"
        )

        themes["financial_light"] = DashboardTheme(
            name="Financial Light",
            mode=ThemeMode.LIGHT,
            color_palette=financial_light
        )

        # Minimal Theme
        minimal_light = ColorPalette(
            primary="#374151",
            secondary="#6B7280",
            accent="#9CA3AF",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
            info="#06B6D4",
            background="#FFFFFF",
            surface="#F9FAFB",
            text_primary="#111827",
            text_secondary="#6B7280",
            border="#E5E7EB",
            hover="#F3F4F6",
            disabled="#D1D5DB"
        )

        themes["minimal_light"] = DashboardTheme(
            name="Minimal Light",
            mode=ThemeMode.LIGHT,
            color_palette=minimal_light
        )

        # Vibrant Theme
        vibrant_light = ColorPalette(
            primary="#7C3AED",
            secondary="#F59E0B",
            accent="#EF4444",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
            info="#06B6D4",
            background="#FFFFFF",
            surface="#FEFCE8",
            text_primary="#1F2937",
            text_secondary="#6B7280",
            border="#FDE047",
            hover="#FEF3C7",
            disabled="#D1D5DB"
        )

        themes["vibrant_light"] = DashboardTheme(
            name="Vibrant Light",
            mode=ThemeMode.LIGHT,
            color_palette=vibrant_light
        )

        # Ocean Theme
        ocean_light = ColorPalette(
            primary="#0E7490",
            secondary="#0891B2",
            accent="#06B6D4",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
            info="#06B6D4",
            background="#FFFFFF",
            surface="#F0F9FF",
            text_primary="#0C4A6E",
            text_secondary="#6B7280",
            border="#BAE6FD",
            hover="#E0F2FE",
            disabled="#D1D5DB"
        )

        themes["ocean_light"] = DashboardTheme(
            name="Ocean Light",
            mode=ThemeMode.LIGHT,
            color_palette=ocean_light
        )

        return themes

    def _get_current_theme(self) -> DashboardTheme:
        """Get the currently selected theme"""
        theme_name = st.session_state.get('selected_theme', 'professional_light')
        return self.themes.get(theme_name, self.themes['professional_light'])

    def set_theme(self, theme_name: str):
        """Set the current theme"""
        if theme_name in self.themes:
            st.session_state.selected_theme = theme_name
            self.current_theme = self.themes[theme_name]

    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes"""
        return {name: theme.name for name, theme in self.themes.items()}

    def generate_css(self, theme: DashboardTheme = None) -> str:
        """Generate CSS for the specified theme"""
        theme = theme or self.current_theme
        colors = theme.colors

        return f"""
        <style>
        /* CSS Custom Properties for theme colors */
        :root {{
            --color-primary: {colors.primary};
            --color-secondary: {colors.secondary};
            --color-accent: {colors.accent};
            --color-success: {colors.success};
            --color-warning: {colors.warning};
            --color-danger: {colors.danger};
            --color-info: {colors.info};
            --color-background: {colors.background};
            --color-surface: {colors.surface};
            --color-text-primary: {colors.text_primary};
            --color-text-secondary: {colors.text_secondary};
            --color-border: {colors.border};
            --color-hover: {colors.hover};
            --color-disabled: {colors.disabled};
            --color-profit: {colors.profit};
            --color-loss: {colors.loss};
            --color-neutral: {colors.neutral};

            --font-family: {theme.font_family};
            --border-radius: {theme.border_radius};

            --spacing-xs: {theme.spacing['xs']};
            --spacing-sm: {theme.spacing['sm']};
            --spacing-md: {theme.spacing['md']};
            --spacing-lg: {theme.spacing['lg']};
            --spacing-xl: {theme.spacing['xl']};

            --shadow-sm: {theme.shadows['sm']};
            --shadow-md: {theme.shadows['md']};
            --shadow-lg: {theme.shadows['lg']};
            --shadow-xl: {theme.shadows['xl']};
        }}

        /* Override Streamlit's default styles */
        .main .block-container {{
            background-color: var(--color-background);
            color: var(--color-text-primary);
        }}

        /* Dashboard-specific styles */
        .dashboard-header {{
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
            padding: var(--spacing-lg);
            border-radius: var(--border-radius);
            margin-bottom: var(--spacing-lg);
            box-shadow: var(--shadow-lg);
        }}

        .metric-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            margin: var(--spacing-sm);
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }}

        .metric-card:hover {{
            background: var(--color-hover);
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }}

        .metric-value {{
            font-size: var(--font-size-2xl);
            font-weight: 700;
            color: var(--color-text-primary);
            margin: var(--spacing-sm) 0;
        }}

        .metric-label {{
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
            font-weight: 500;
            margin-bottom: var(--spacing-xs);
        }}

        .metric-change-positive {{
            color: var(--color-profit);
            font-weight: 600;
        }}

        .metric-change-negative {{
            color: var(--color-loss);
            font-weight: 600;
        }}

        .metric-change-neutral {{
            color: var(--color-neutral);
            font-weight: 500;
        }}

        .panel-container {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--border-radius);
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
            box-shadow: var(--shadow-sm);
        }}

        .panel-title {{
            font-size: var(--font-size-xl);
            font-weight: 600;
            color: var(--color-primary);
            margin-bottom: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }}

        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: var(--spacing-xs);
        }}

        .status-good {{ background-color: var(--color-success); }}
        .status-warning {{ background-color: var(--color-warning); }}
        .status-danger {{ background-color: var(--color-danger); }}
        .status-info {{ background-color: var(--color-info); }}

        /* Button styles */
        .stButton > button {{
            background: var(--color-primary);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: var(--spacing-sm) var(--spacing-md);
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .stButton > button:hover {{
            background: var(--color-secondary);
            box-shadow: var(--shadow-md);
        }}

        /* Selectbox styles */
        .stSelectbox > div > div {{
            background: var(--color-surface);
            border-color: var(--color-border);
        }}

        /* Sidebar styles */
        .css-1d391kg {{
            background: var(--color-surface);
            border-right: 1px solid var(--color-border);
        }}

        /* Chart container */
        .chart-container {{
            background: var(--color-surface);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            margin: var(--spacing-sm) 0;
            box-shadow: var(--shadow-sm);
        }}

        /* Alert styles */
        .alert-success {{
            background: color-mix(in srgb, var(--color-success) 10%, transparent);
            border-left: 4px solid var(--color-success);
            padding: var(--spacing-md);
            border-radius: var(--border-radius);
            margin: var(--spacing-sm) 0;
        }}

        .alert-warning {{
            background: color-mix(in srgb, var(--color-warning) 10%, transparent);
            border-left: 4px solid var(--color-warning);
            padding: var(--spacing-md);
            border-radius: var(--border-radius);
            margin: var(--spacing-sm) 0;
        }}

        .alert-danger {{
            background: color-mix(in srgb, var(--color-danger) 10%, transparent);
            border-left: 4px solid var(--color-danger);
            padding: var(--spacing-md);
            border-radius: var(--border-radius);
            margin: var(--spacing-sm) 0;
        }}

        /* Data table styles */
        .dataframe {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--border-radius);
        }}

        .dataframe th {{
            background: var(--color-primary);
            color: white;
            font-weight: 600;
        }}

        .dataframe td {{
            border-bottom: 1px solid var(--color-border);
        }}

        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background-color: var(--color-background);
                color: var(--color-text-primary);
            }}
        }}

        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}

        /* High contrast mode */
        @media (prefers-contrast: high) {{
            .metric-card {{
                border-width: 2px;
            }}

            .panel-container {{
                border-width: 2px;
            }}
        }}
        </style>
        """

    def get_plotly_theme(self, theme: DashboardTheme = None) -> Dict:
        """Get Plotly theme configuration"""
        theme = theme or self.current_theme
        colors = theme.colors

        return {
            "layout": {
                "colorway": colors.chart_colors,
                "font": {"family": theme.font_family, "color": colors.text_primary},
                "paper_bgcolor": colors.background,
                "plot_bgcolor": colors.surface,
                "hovermode": "closest",
                "hoverlabel": {
                    "bgcolor": colors.surface,
                    "bordercolor": colors.border,
                    "font": {"color": colors.text_primary}
                },
                "xaxis": {
                    "gridcolor": colors.border,
                    "linecolor": colors.border,
                    "tickcolor": colors.border,
                    "tickfont": {"color": colors.text_secondary}
                },
                "yaxis": {
                    "gridcolor": colors.border,
                    "linecolor": colors.border,
                    "tickcolor": colors.border,
                    "tickfont": {"color": colors.text_secondary}
                }
            }
        }


def create_theme_selector():
    """Create a theme selector widget"""
    theme_manager = ThemeManager()

    st.sidebar.markdown("### 🎨 Theme Settings")

    available_themes = theme_manager.get_available_themes()
    current_theme = st.session_state.get('selected_theme', 'professional_light')

    selected_theme = st.sidebar.selectbox(
        "Select Theme",
        options=list(available_themes.keys()),
        format_func=lambda x: available_themes[x],
        index=list(available_themes.keys()).index(current_theme) if current_theme in available_themes else 0
    )

    if selected_theme != current_theme:
        theme_manager.set_theme(selected_theme)
        st.rerun()

    return theme_manager


def apply_theme(theme_manager: ThemeManager = None):
    """Apply the current theme to the Streamlit app"""
    if theme_manager is None:
        theme_manager = ThemeManager()

    css = theme_manager.generate_css()
    st.markdown(css, unsafe_allow_html=True)

    return theme_manager


def get_financial_colors(theme_manager: ThemeManager = None) -> Dict[str, str]:
    """Get financial-specific colors for charts and indicators"""
    if theme_manager is None:
        theme_manager = ThemeManager()

    colors = theme_manager.current_theme.colors

    return {
        "profit": colors.profit,
        "loss": colors.loss,
        "neutral": colors.neutral,
        "revenue": colors.primary,
        "expenses": colors.danger,
        "assets": colors.info,
        "liabilities": colors.warning,
        "equity": colors.success
    }


if __name__ == "__main__":
    # Demo and testing
    st.set_page_config(
        page_title="Dashboard Themes Demo",
        page_icon="🎨",
        layout="wide"
    )

    # Create theme selector and apply theme
    theme_manager = create_theme_selector()
    apply_theme(theme_manager)

    st.title("🎨 Dashboard Themes Demo")

    current_theme = theme_manager.current_theme
    st.markdown(f"**Current Theme:** {current_theme.name}")

    # Demo metric cards
    st.header("Metric Cards")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">📈 Revenue</div>
            <div class="metric-value">$125.2M</div>
            <div class="metric-change-positive">+12.3% YoY</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">💰 Profit Margin</div>
            <div class="metric-value">18.5%</div>
            <div class="metric-change-negative">-2.1pp</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">🎯 ROE</div>
            <div class="metric-value">15.2%</div>
            <div class="metric-change-positive">+1.8pp</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">⚖️ Debt/Equity</div>
            <div class="metric-value">0.45</div>
            <div class="metric-change-neutral">No change</div>
        </div>
        """, unsafe_allow_html=True)

    # Demo panels
    st.header("Panel Containers")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="panel-container">
            <div class="panel-title">📊 Financial Overview</div>
            <p>This is a sample panel showing how content is displayed within themed containers.</p>
            <div class="status-indicator status-good"></div> All systems operational
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="panel-container">
            <div class="panel-title">🚨 Alerts</div>
            <div class="alert-warning">
                <strong>Warning:</strong> P/E ratio above industry average
            </div>
            <div class="alert-success">
                <strong>Good:</strong> Strong revenue growth this quarter
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Show theme details
    with st.expander("🔧 Theme Details"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Colors")
            colors_dict = {
                "Primary": current_theme.colors.primary,
                "Secondary": current_theme.colors.secondary,
                "Success": current_theme.colors.success,
                "Warning": current_theme.colors.warning,
                "Danger": current_theme.colors.danger,
                "Background": current_theme.colors.background,
                "Text Primary": current_theme.colors.text_primary
            }

            for name, color in colors_dict.items():
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                    <div style="width: 20px; height: 20px; background: {color}; border-radius: 4px; margin-right: 0.5rem; border: 1px solid #ccc;"></div>
                    <span>{name}: {color}</span>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.subheader("Typography & Spacing")
            st.json({
                "font_family": current_theme.font_family,
                "font_sizes": current_theme.font_sizes,
                "spacing": current_theme.spacing,
                "border_radius": current_theme.border_radius
            })

    # Plotly theme demo
    financial_colors = get_financial_colors(theme_manager)
    st.header("Chart Theme Demo")

    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    # Sample data
    dates = pd.date_range('2020-01-01', periods=24, freq='M')
    revenue = np.cumsum(np.random.randn(24) * 10 + 100) + 1000
    profit = revenue * (0.15 + np.random.randn(24) * 0.05)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=revenue, name='Revenue', line_color=financial_colors['revenue']))
    fig.add_trace(go.Scatter(x=dates, y=profit, name='Profit', line_color=financial_colors['profit']))

    # Apply theme
    plotly_theme = theme_manager.get_plotly_theme()
    fig.update_layout(**plotly_theme['layout'])
    fig.update_layout(title="Financial Performance Over Time")

    st.plotly_chart(fig, use_container_width=True)