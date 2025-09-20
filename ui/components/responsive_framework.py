"""
Responsive Design Framework for Streamlit Financial Analysis Application

Provides adaptive layout components and utilities for creating responsive,
accessible financial dashboards that work across multiple device types.
"""

import streamlit as st
from typing import List, Tuple, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ResponsiveBreakpoints:
    """Define responsive breakpoints for different screen sizes."""

    MOBILE = 640
    TABLET = 768
    DESKTOP = 1024
    WIDE = 1280

    @classmethod
    def get_viewport_class(cls, width: int) -> str:
        """Get CSS class based on viewport width."""
        if width < cls.MOBILE:
            return "mobile"
        elif width < cls.TABLET:
            return "tablet"
        elif width < cls.DESKTOP:
            return "desktop"
        else:
            return "wide"

class ResponsiveLayoutManager:
    """Manages responsive layouts and column configurations."""

    def __init__(self):
        self.inject_responsive_css()

    def inject_responsive_css(self):
        """Inject responsive CSS framework into Streamlit."""
        css = """
        <style>
        /* Responsive Layout Framework */
        @media (max-width: 640px) {
            /* Mobile styles */
            .stColumn {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            .responsive-stack > div {
                width: 100% !important;
                margin-bottom: 1rem;
            }
            .mobile-hide {
                display: none !important;
            }
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            /* Sidebar adjustments for mobile */
            .css-1d391kg {
                padding-top: 1rem !important;
            }
        }

        @media (min-width: 641px) and (max-width: 768px) {
            /* Tablet styles */
            .tablet-hide {
                display: none !important;
            }
        }

        @media (min-width: 769px) {
            /* Desktop and above */
            .desktop-hide {
                display: none !important;
            }
        }

        /* Responsive column utilities */
        .responsive-columns {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .responsive-columns > div {
            flex: 1;
            min-width: 300px;
        }

        /* Accessibility improvements */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }

        /* Enhanced focus indicators */
        .stButton > button:focus {
            outline: 2px solid #0066cc !important;
            outline-offset: 2px !important;
        }

        /* Improved mobile touch targets */
        @media (max-width: 640px) {
            .stButton > button {
                min-height: 44px !important;
                padding: 0.75rem 1rem !important;
            }
            .stSelectbox > div > div {
                min-height: 44px !important;
            }
        }

        /* Responsive navigation */
        .responsive-nav {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .responsive-nav-item {
            flex: 1;
            min-width: 120px;
        }

        /* Mobile-optimized metrics */
        @media (max-width: 640px) {
            .metric-container {
                text-align: center;
                margin-bottom: 1rem;
            }
            .metric-container [data-testid="metric-container"] {
                border: 1px solid #e0e0e0;
                padding: 1rem;
                border-radius: 0.5rem;
            }
        }

        /* Responsive charts */
        .responsive-chart {
            width: 100%;
            overflow-x: auto;
        }

        /* Improved table responsiveness */
        @media (max-width: 768px) {
            .stDataFrame {
                font-size: 0.8rem;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    def responsive_columns(
        self,
        desktop_spec: Union[int, List[Union[int, float]]],
        tablet_spec: Optional[Union[int, List[Union[int, float]]]] = None,
        mobile_spec: Optional[Union[int, List[Union[int, float]]]] = None,
        gap: str = "small",
        vertical_alignment: str = "top"
    ) -> List[Any]:
        """
        Create responsive columns that adapt to different screen sizes.

        Args:
            desktop_spec: Column specification for desktop (>768px)
            tablet_spec: Column specification for tablet (641-768px), defaults to desktop_spec
            mobile_spec: Column specification for mobile (<640px), defaults to 1
            gap: Gap between columns ("small", "medium", "large")
            vertical_alignment: Vertical alignment ("top", "center", "bottom")

        Returns:
            List of column objects
        """
        # Default fallbacks
        if tablet_spec is None:
            tablet_spec = desktop_spec
        if mobile_spec is None:
            mobile_spec = 1  # Stack vertically on mobile

        # For now, use desktop_spec (Streamlit doesn't have built-in responsive columns)
        # But add responsive CSS classes
        with st.container():
            st.markdown('<div class="responsive-columns">', unsafe_allow_html=True)
            cols = st.columns(desktop_spec, gap=gap, vertical_alignment=vertical_alignment)
            st.markdown('</div>', unsafe_allow_html=True)
            return cols

    def mobile_stack_container(self, content_blocks: List[callable]) -> None:
        """
        Create a container that stacks content vertically on mobile.

        Args:
            content_blocks: List of callable functions that render content
        """
        with st.container():
            st.markdown('<div class="responsive-stack">', unsafe_allow_html=True)

            # On desktop, use columns
            if len(content_blocks) > 1:
                cols = st.columns(len(content_blocks))
                for i, content_func in enumerate(content_blocks):
                    with cols[i]:
                        content_func()
            else:
                # Single content block
                content_blocks[0]()

            st.markdown('</div>', unsafe_allow_html=True)

    def responsive_metric_grid(
        self,
        metrics: List[Dict[str, Any]],
        max_cols: int = 4
    ) -> None:
        """
        Display metrics in a responsive grid.

        Args:
            metrics: List of metric dictionaries with keys: label, value, delta, help
            max_cols: Maximum columns for desktop view
        """
        if not metrics:
            return

        # Calculate columns based on number of metrics
        num_metrics = len(metrics)
        if num_metrics <= max_cols:
            cols = st.columns(num_metrics)
        else:
            # Create multiple rows
            rows_needed = (num_metrics + max_cols - 1) // max_cols
            for row in range(rows_needed):
                start_idx = row * max_cols
                end_idx = min(start_idx + max_cols, num_metrics)
                row_metrics = metrics[start_idx:end_idx]

                cols = st.columns(len(row_metrics))
                for i, metric in enumerate(row_metrics):
                    with cols[i]:
                        self.accessible_metric(
                            label=metric.get('label', ''),
                            value=metric.get('value', ''),
                            delta=metric.get('delta'),
                            help=metric.get('help')
                        )
            return

        # Single row
        for i, metric in enumerate(metrics):
            with cols[i]:
                self.accessible_metric(
                    label=metric.get('label', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta'),
                    help=metric.get('help')
                )

    def accessible_metric(
        self,
        label: str,
        value: str,
        delta: Optional[str] = None,
        help: Optional[str] = None
    ) -> None:
        """
        Display an accessible metric with proper ARIA labels.

        Args:
            label: Metric label
            value: Metric value
            delta: Change indicator
            help: Help text
        """
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)

            # Add screen reader text
            if help:
                st.markdown(
                    f'<span class="sr-only">Metric: {label}. Value: {value}. {help}</span>',
                    unsafe_allow_html=True
                )

            st.metric(
                label=label,
                value=value,
                delta=delta,
                help=help
            )

            st.markdown('</div>', unsafe_allow_html=True)

    def responsive_navigation(
        self,
        nav_items: List[Tuple[str, str]],
        key_prefix: str = "nav"
    ) -> str:
        """
        Create responsive navigation with proper accessibility.

        Args:
            nav_items: List of (label, value) tuples
            key_prefix: Unique key prefix

        Returns:
            Selected navigation value
        """
        with st.container():
            st.markdown('<nav class="responsive-nav" role="navigation">', unsafe_allow_html=True)

            # Mobile: Use selectbox
            if len(nav_items) > 4:  # Use selectbox for many items
                selected = st.selectbox(
                    "Navigation",
                    options=[item[1] for item in nav_items],
                    format_func=lambda x: next(item[0] for item in nav_items if item[1] == x),
                    key=f"{key_prefix}_mobile",
                    label_visibility="collapsed"
                )
            else:
                # Desktop: Use radio buttons in columns
                cols = st.columns(len(nav_items))
                selected = None

                for i, (label, value) in enumerate(nav_items):
                    with cols[i]:
                        if st.button(
                            label,
                            key=f"{key_prefix}_{i}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            selected = value

                # Default to first item if none selected
                if selected is None and nav_items:
                    selected = nav_items[0][1]

            st.markdown('</nav>', unsafe_allow_html=True)
            return selected

class AccessibilityHelpers:
    """Utilities for improving accessibility."""

    @staticmethod
    def add_aria_label(text: str, label: str) -> str:
        """Add ARIA label to text content."""
        return f'<span aria-label="{label}">{text}</span>'

    @staticmethod
    def add_skip_link(target_id: str, text: str = "Skip to main content") -> None:
        """Add skip link for keyboard navigation."""
        st.markdown(
            f'''
            <a href="#{target_id}" class="sr-only"
               style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;">
               {text}
            </a>
            ''',
            unsafe_allow_html=True
        )

    @staticmethod
    def add_landmark(content: str, role: str = "main", aria_label: str = None) -> None:
        """Add ARIA landmark to content."""
        aria_attr = f'aria-label="{aria_label}"' if aria_label else ''
        st.markdown(
            f'<div role="{role}" {aria_attr}>{content}</div>',
            unsafe_allow_html=True
        )

# Global instance for easy access
responsive_layout = ResponsiveLayoutManager()
accessibility = AccessibilityHelpers()

def configure_responsive_page(
    page_title: str = "Financial Analysis",
    page_icon: str = "📊",
    layout: str = "wide",
    initial_sidebar_state: str = "expanded"
) -> None:
    """
    Configure page with responsive settings and accessibility features.

    Args:
        page_title: Page title
        page_icon: Page icon
        layout: Layout mode
        initial_sidebar_state: Sidebar initial state
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )

    # Initialize responsive framework
    responsive_layout.inject_responsive_css()

    # Add accessibility features
    accessibility.add_skip_link("main-content", "Skip to main content")

def responsive_container(use_container_width: bool = True) -> Any:
    """Create a responsive container with proper landmarks."""
    container = st.container()
    with container:
        st.markdown('<div id="main-content" role="main">', unsafe_allow_html=True)
    return container

def render_dual_view_toggle(context: str = "default") -> str:
    """
    Render dual view toggle with unique context to avoid key conflicts.

    Args:
        context: Unique context identifier for the toggle

    Returns:
        Selected view mode
    """
    return st.selectbox(
        "View Mode",
        options=["Historical Analysis", "Current Market View"],
        key=f"dual_view_toggle_{context}",
        help="Switch between historical data analysis and current market perspective"
    )