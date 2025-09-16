"""
Responsive Design Patterns for Financial Dashboard
=================================================

This module provides responsive design utilities and patterns for creating
adaptive layouts that work across different screen sizes and devices.
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json


class ScreenSize(Enum):
    """Screen size categories for responsive design"""
    MOBILE = "mobile"      # < 768px
    TABLET = "tablet"      # 768px - 1024px
    DESKTOP = "desktop"    # 1024px - 1440px
    WIDE = "wide"         # > 1440px


class LayoutMode(Enum):
    """Layout modes for different content densities"""
    COMPACT = "compact"     # Minimal spacing, dense content
    STANDARD = "standard"   # Balanced spacing and content
    COMFORTABLE = "comfortable"  # Generous spacing, larger elements


@dataclass
class ResponsiveConfig:
    """Configuration for responsive layouts"""
    # Column configurations for different screen sizes
    mobile_columns: List[float] = None
    tablet_columns: List[float] = None
    desktop_columns: List[float] = None
    wide_columns: List[float] = None

    # Spacing configurations
    mobile_spacing: str = "0.5rem"
    tablet_spacing: str = "1rem"
    desktop_spacing: str = "1.5rem"
    wide_spacing: str = "2rem"

    # Font size multipliers
    mobile_font_scale: float = 0.9
    tablet_font_scale: float = 1.0
    desktop_font_scale: float = 1.1
    wide_font_scale: float = 1.2

    # Component visibility by screen size
    mobile_hidden: List[str] = None
    tablet_hidden: List[str] = None

    def __post_init__(self):
        if self.mobile_columns is None:
            self.mobile_columns = [1.0]
        if self.tablet_columns is None:
            self.tablet_columns = [0.5, 0.5]
        if self.desktop_columns is None:
            self.desktop_columns = [0.25, 0.5, 0.25]
        if self.wide_columns is None:
            self.wide_columns = [0.2, 0.3, 0.3, 0.2]
        if self.mobile_hidden is None:
            self.mobile_hidden = []
        if self.tablet_hidden is None:
            self.tablet_hidden = []


class ResponsiveLayoutManager:
    """Manages responsive layouts and adapts to different screen sizes"""

    def __init__(self, config: ResponsiveConfig = None):
        self.config = config or ResponsiveConfig()
        self.current_screen_size = self._detect_screen_size()
        self.layout_mode = LayoutMode.STANDARD

    def _detect_screen_size(self) -> ScreenSize:
        """Detect screen size using Streamlit's viewport information"""
        # Note: This is a simplified detection. In production, you might use
        # JavaScript injection to get actual viewport dimensions

        # For now, we'll use session state to track user preference
        if 'screen_size' not in st.session_state:
            # Default to desktop, but allow user to override
            st.session_state.screen_size = ScreenSize.DESKTOP

        return st.session_state.screen_size

    def get_columns_config(self, screen_size: ScreenSize = None) -> List[float]:
        """Get column configuration for the specified screen size"""
        screen_size = screen_size or self.current_screen_size

        column_map = {
            ScreenSize.MOBILE: self.config.mobile_columns,
            ScreenSize.TABLET: self.config.tablet_columns,
            ScreenSize.DESKTOP: self.config.desktop_columns,
            ScreenSize.WIDE: self.config.wide_columns
        }

        return column_map.get(screen_size, self.config.desktop_columns)

    def create_responsive_columns(self, screen_size: ScreenSize = None):
        """Create Streamlit columns based on responsive configuration"""
        columns_config = self.get_columns_config(screen_size)
        return st.columns(columns_config)

    def get_spacing(self, screen_size: ScreenSize = None) -> str:
        """Get spacing value for the specified screen size"""
        screen_size = screen_size or self.current_screen_size

        spacing_map = {
            ScreenSize.MOBILE: self.config.mobile_spacing,
            ScreenSize.TABLET: self.config.tablet_spacing,
            ScreenSize.DESKTOP: self.config.desktop_spacing,
            ScreenSize.WIDE: self.config.wide_spacing
        }

        return spacing_map.get(screen_size, self.config.desktop_spacing)

    def get_font_scale(self, screen_size: ScreenSize = None) -> float:
        """Get font scale multiplier for the specified screen size"""
        screen_size = screen_size or self.current_screen_size

        scale_map = {
            ScreenSize.MOBILE: self.config.mobile_font_scale,
            ScreenSize.TABLET: self.config.tablet_font_scale,
            ScreenSize.DESKTOP: self.config.desktop_font_scale,
            ScreenSize.WIDE: self.config.wide_font_scale
        }

        return scale_map.get(screen_size, self.config.desktop_font_scale)

    def should_hide_component(self, component_name: str, screen_size: ScreenSize = None) -> bool:
        """Check if a component should be hidden on the specified screen size"""
        screen_size = screen_size or self.current_screen_size

        if screen_size == ScreenSize.MOBILE:
            return component_name in self.config.mobile_hidden
        elif screen_size == ScreenSize.TABLET:
            return component_name in self.config.tablet_hidden

        return False

    def generate_responsive_css(self) -> str:
        """Generate CSS for responsive design"""
        mobile_spacing = self.config.mobile_spacing
        tablet_spacing = self.config.tablet_spacing
        desktop_spacing = self.config.desktop_spacing
        wide_spacing = self.config.wide_spacing

        return f"""
        <style>
        /* Base responsive styles */
        .responsive-container {{
            width: 100%;
            padding: {desktop_spacing};
        }}

        .responsive-grid {{
            display: grid;
            gap: {desktop_spacing};
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }}

        .responsive-card {{
            background: white;
            border-radius: 8px;
            padding: {desktop_spacing};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}

        .responsive-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        /* Mobile styles */
        @media (max-width: 767px) {{
            .responsive-container {{
                padding: {mobile_spacing};
            }}

            .responsive-grid {{
                gap: {mobile_spacing};
                grid-template-columns: 1fr;
            }}

            .responsive-card {{
                padding: {mobile_spacing};
            }}

            .mobile-hidden {{
                display: none !important;
            }}

            .mobile-stack {{
                flex-direction: column !important;
            }}

            .mobile-full-width {{
                width: 100% !important;
            }}

            /* Adjust font sizes for mobile */
            h1 {{ font-size: 1.5rem !important; }}
            h2 {{ font-size: 1.3rem !important; }}
            h3 {{ font-size: 1.1rem !important; }}

            /* Make tables scrollable on mobile */
            .dataframe {{
                overflow-x: auto;
                white-space: nowrap;
            }}
        }}

        /* Tablet styles */
        @media (min-width: 768px) and (max-width: 1023px) {{
            .responsive-container {{
                padding: {tablet_spacing};
            }}

            .responsive-grid {{
                gap: {tablet_spacing};
                grid-template-columns: repeat(2, 1fr);
            }}

            .responsive-card {{
                padding: {tablet_spacing};
            }}

            .tablet-hidden {{
                display: none !important;
            }}

            .tablet-stack {{
                flex-direction: column !important;
            }}
        }}

        /* Desktop styles */
        @media (min-width: 1024px) and (max-width: 1439px) {{
            .responsive-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}

        /* Wide screen styles */
        @media (min-width: 1440px) {{
            .responsive-container {{
                padding: {wide_spacing};
            }}

            .responsive-grid {{
                gap: {wide_spacing};
                grid-template-columns: repeat(4, 1fr);
            }}

            .responsive-card {{
                padding: {wide_spacing};
            }}
        }}

        /* Print styles */
        @media print {{
            .no-print {{
                display: none !important;
            }}

            .responsive-card {{
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ccc;
            }}
        }}

        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {{
            .responsive-card {{
                transition: none;
            }}

            .responsive-card:hover {{
                transform: none;
            }}
        }}

        @media (prefers-color-scheme: dark) {{
            .responsive-card {{
                background: #2d3748;
                color: #e2e8f0;
                border: 1px solid #4a5568;
            }}
        }}
        </style>
        """


class ResponsiveComponents:
    """Responsive UI components for the dashboard"""

    def __init__(self, layout_manager: ResponsiveLayoutManager):
        self.layout_manager = layout_manager

    def responsive_metric_grid(self, metrics: Dict, max_cols: int = 4):
        """Create a responsive grid of metrics that adapts to screen size"""
        screen_size = self.layout_manager.current_screen_size

        # Determine number of columns based on screen size
        if screen_size == ScreenSize.MOBILE:
            num_cols = 1
        elif screen_size == ScreenSize.TABLET:
            num_cols = min(2, len(metrics))
        else:
            num_cols = min(max_cols, len(metrics))

        # Create columns
        cols = st.columns(num_cols)

        # Distribute metrics across columns
        for idx, (metric_name, metric_data) in enumerate(metrics.items()):
            with cols[idx % num_cols]:
                self._render_responsive_metric(metric_name, metric_data)

    def _render_responsive_metric(self, name: str, data: Dict):
        """Render a single metric with responsive design"""
        value = data.get('value', 'N/A')
        change = data.get('change', '')
        icon = data.get('icon', '📊')

        # Apply responsive styling
        st.markdown(
            f"""
            <div class="responsive-card">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                    <span style="font-weight: 600; color: #4a5568;">{name}</span>
                </div>
                <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">
                    {value}
                </div>
                {f'<div style="font-size: 0.9rem; color: #718096;">{change}</div>' if change else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

    def responsive_chart_container(self, title: str, chart_func, **kwargs):
        """Create a responsive container for charts"""
        screen_size = self.layout_manager.current_screen_size

        # Adjust chart height based on screen size
        height_map = {
            ScreenSize.MOBILE: 300,
            ScreenSize.TABLET: 400,
            ScreenSize.DESKTOP: 500,
            ScreenSize.WIDE: 600
        }

        height = height_map.get(screen_size, 500)

        st.markdown(
            f"""
            <div class="responsive-card">
                <h3 style="margin-bottom: 1rem; color: #2d3748;">{title}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Call the chart function with responsive height
        chart_func(height=height, **kwargs)

    def responsive_data_table(self, df, title: str = ""):
        """Create a responsive data table"""
        screen_size = self.layout_manager.current_screen_size

        if title:
            st.subheader(title)

        # On mobile, limit columns or use scrollable container
        if screen_size == ScreenSize.MOBILE:
            # Limit to most important columns on mobile
            important_cols = df.columns[:3] if len(df.columns) > 3 else df.columns
            mobile_df = df[important_cols]

            st.markdown('<div class="mobile-table-container">', unsafe_allow_html=True)
            st.dataframe(mobile_df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Show expandable section for full data
            with st.expander("View All Columns"):
                st.dataframe(df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    def responsive_sidebar_content(self, content_func):
        """Render sidebar content that adapts to screen size"""
        screen_size = self.layout_manager.current_screen_size

        if screen_size == ScreenSize.MOBILE:
            # On mobile, move sidebar content to expandable section in main area
            with st.expander("⚙️ Settings & Controls", expanded=False):
                content_func()
        else:
            # On larger screens, use normal sidebar
            with st.sidebar:
                content_func()


def create_screen_size_selector():
    """Create a screen size selector for testing responsive layouts"""
    st.sidebar.markdown("### 📱 Screen Size (Testing)")

    size_options = {
        "📱 Mobile": ScreenSize.MOBILE,
        "📱 Tablet": ScreenSize.TABLET,
        "💻 Desktop": ScreenSize.DESKTOP,
        "🖥️ Wide": ScreenSize.WIDE
    }

    selected = st.sidebar.selectbox(
        "Select Screen Size",
        options=list(size_options.keys()),
        index=2  # Default to Desktop
    )

    st.session_state.screen_size = size_options[selected]
    return size_options[selected]


def apply_responsive_design():
    """Apply responsive design CSS to the current Streamlit app"""
    layout_manager = ResponsiveLayoutManager()
    css = layout_manager.generate_responsive_css()
    st.markdown(css, unsafe_allow_html=True)
    return layout_manager


if __name__ == "__main__":
    # Example usage and testing
    st.set_page_config(
        page_title="Responsive Design Demo",
        page_icon="📱",
        layout="wide"
    )

    # Apply responsive design
    layout_manager = apply_responsive_design()
    components = ResponsiveComponents(layout_manager)

    # Screen size selector for testing
    current_size = create_screen_size_selector()

    st.title("📱 Responsive Design Demo")
    st.markdown(f"**Current Screen Size:** {current_size.value}")

    # Demo responsive metrics grid
    st.header("Responsive Metrics Grid")

    sample_metrics = {
        "Revenue": {"value": "$125.2M", "change": "+12.3% YoY", "icon": "💰"},
        "Profit Margin": {"value": "18.5%", "change": "+2.1pp", "icon": "📈"},
        "ROE": {"value": "15.2%", "change": "+1.8pp", "icon": "🎯"},
        "Debt/Equity": {"value": "0.45", "change": "-0.07", "icon": "⚖️"},
        "P/E Ratio": {"value": "18.5x", "change": "+1.2x", "icon": "💎"},
        "Current Ratio": {"value": "2.1", "change": "-0.3", "icon": "💧"}
    }

    components.responsive_metric_grid(sample_metrics)

    # Demo responsive columns
    st.header("Responsive Column Layout")

    cols = layout_manager.create_responsive_columns()

    for idx, col in enumerate(cols):
        with col:
            st.markdown(
                f"""
                <div class="responsive-card">
                    <h4>Column {idx + 1}</h4>
                    <p>This column adapts to different screen sizes.</p>
                    <p>Current columns: {len(cols)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Demo responsive data table
    st.header("Responsive Data Table")

    import pandas as pd
    import numpy as np

    sample_data = pd.DataFrame({
        'Company': ['Apple', 'Microsoft', 'Google', 'Amazon'],
        'Revenue': ['$394.3B', '$198.3B', '$282.8B', '$513.9B'],
        'Profit': ['$99.8B', '$72.4B', '$76.0B', '$33.4B'],
        'P/E Ratio': [28.5, 32.1, 26.8, 58.2],
        'Market Cap': ['$2.8T', '$2.3T', '$1.7T', '$1.5T'],
        'Employees': [164000, 221000, 156500, 1541000]
    })

    components.responsive_data_table(sample_data, "Company Comparison")

    # Show layout configuration
    with st.expander("🔧 Layout Configuration"):
        st.json({
            "screen_size": current_size.value,
            "columns_config": layout_manager.get_columns_config(),
            "spacing": layout_manager.get_spacing(),
            "font_scale": layout_manager.get_font_scale()
        })