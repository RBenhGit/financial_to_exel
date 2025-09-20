"""
Responsive Navigation Components for Financial Analysis Application

Provides mobile-optimized navigation components that adapt to different
screen sizes and provide accessible navigation patterns.
"""

import streamlit as st
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ResponsiveTabNavigation:
    """Mobile-optimized tab navigation for financial analysis."""

    def __init__(self):
        self.inject_navigation_css()

    def inject_navigation_css(self):
        """Inject responsive navigation CSS."""
        css = """
        <style>
        /* Responsive Tab Navigation */
        .responsive-tabs {
            margin-bottom: 1rem;
        }

        /* Mobile tab navigation */
        @media (max-width: 768px) {
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap !important;
                gap: 0.25rem !important;
            }

            .stTabs [data-baseweb="tab-list"] button {
                min-width: auto !important;
                padding: 0.5rem 0.75rem !important;
                font-size: 0.85rem !important;
                flex: 1 !important;
                min-width: 120px !important;
            }

            /* Hide less important tabs on mobile */
            .stTabs [data-baseweb="tab-list"] button:nth-child(n+6) {
                display: none;
            }
        }

        /* Compact navigation for small screens */
        @media (max-width: 640px) {
            .compact-nav-selector {
                width: 100%;
                margin-bottom: 1rem;
            }

            .compact-nav-selector .stSelectbox {
                width: 100%;
            }

            /* Hide regular tabs, show dropdown */
            .mobile-hide-tabs .stTabs {
                display: none !important;
            }
        }

        /* Navigation breadcrumbs */
        .nav-breadcrumb {
            background-color: #f8f9fa;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #6c757d;
        }

        .nav-breadcrumb a {
            color: #007bff;
            text-decoration: none;
        }

        .nav-breadcrumb a:hover {
            text-decoration: underline;
        }

        /* Quick action buttons */
        .quick-actions {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .quick-actions .stButton {
            flex: 1;
            min-width: 120px;
        }

        @media (max-width: 640px) {
            .quick-actions .stButton {
                min-width: 100%;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    def create_responsive_tabs(
        self,
        tab_config: List[Dict[str, Any]],
        mobile_threshold: int = 5
    ) -> Tuple[List[Any], str]:
        """
        Create responsive tabs that adapt to screen size.

        Args:
            tab_config: List of tab configurations with keys: 'label', 'icon', 'key', 'mobile_priority'
            mobile_threshold: Number of tabs to show before switching to dropdown on mobile

        Returns:
            Tuple of (tab_objects, selected_tab_key)
        """
        # Sort tabs by mobile priority (higher priority first)
        sorted_tabs = sorted(
            tab_config,
            key=lambda x: x.get('mobile_priority', 0),
            reverse=True
        )

        # Create tab labels with icons
        tab_labels = []
        tab_keys = []

        for tab in sorted_tabs:
            icon = tab.get('icon', '')
            label = tab.get('label', 'Tab')
            tab_labels.append(f"{icon} {label}" if icon else label)
            tab_keys.append(tab.get('key', label.lower().replace(' ', '_')))

        # For mobile: Use dropdown if too many tabs
        if len(tab_labels) > mobile_threshold:
            with st.container():
                st.markdown('<div class="compact-nav-selector">', unsafe_allow_html=True)

                selected_index = st.selectbox(
                    "Navigate to section:",
                    range(len(tab_labels)),
                    format_func=lambda x: tab_labels[x],
                    key="mobile_tab_selector"
                )

                selected_tab_key = tab_keys[selected_index]
                st.markdown('</div>', unsafe_allow_html=True)

                # Return None for tab objects since we're using dropdown
                return None, selected_tab_key

        # Regular tabs for desktop/tablet
        with st.container():
            st.markdown('<div class="responsive-tabs">', unsafe_allow_html=True)
            tabs = st.tabs(tab_labels)
            st.markdown('</div>', unsafe_allow_html=True)

            return tabs, None

    def create_breadcrumb_navigation(
        self,
        navigation_path: List[Tuple[str, Optional[str]]]
    ) -> None:
        """
        Create breadcrumb navigation.

        Args:
            navigation_path: List of (label, url) tuples for breadcrumb items
        """
        if not navigation_path:
            return

        breadcrumb_html = '<nav class="nav-breadcrumb" aria-label="Breadcrumb">'
        breadcrumb_items = []

        for i, (label, url) in enumerate(navigation_path):
            if i == len(navigation_path) - 1:  # Last item (current page)
                breadcrumb_items.append(f'<span aria-current="page">{label}</span>')
            elif url:
                breadcrumb_items.append(f'<a href="{url}">{label}</a>')
            else:
                breadcrumb_items.append(f'<span>{label}</span>')

        breadcrumb_html += ' / '.join(breadcrumb_items)
        breadcrumb_html += '</nav>'

        st.markdown(breadcrumb_html, unsafe_allow_html=True)

    def create_quick_action_bar(
        self,
        actions: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Create quick action button bar.

        Args:
            actions: List of action configs with keys: 'label', 'key', 'icon', 'type', 'help'

        Returns:
            Dictionary of action results
        """
        results = {}

        with st.container():
            st.markdown('<div class="quick-actions">', unsafe_allow_html=True)

            # Use columns for desktop, stack for mobile
            if len(actions) <= 4:
                cols = st.columns(len(actions))
                for i, action in enumerate(actions):
                    with cols[i]:
                        results[action['key']] = self._render_action_button(action)
            else:
                # For many actions, use rows of columns
                actions_per_row = 3
                for i in range(0, len(actions), actions_per_row):
                    row_actions = actions[i:i + actions_per_row]
                    cols = st.columns(len(row_actions))

                    for j, action in enumerate(row_actions):
                        with cols[j]:
                            results[action['key']] = self._render_action_button(action)

            st.markdown('</div>', unsafe_allow_html=True)

        return results

    def _render_action_button(self, action: Dict[str, Any]) -> bool:
        """Render individual action button."""
        icon = action.get('icon', '')
        label = action.get('label', 'Action')
        display_text = f"{icon} {label}" if icon else label

        return st.button(
            display_text,
            key=action['key'],
            type=action.get('type', 'secondary'),
            help=action.get('help'),
            use_container_width=True
        )

class ResponsiveSidebar:
    """Responsive sidebar management."""

    def __init__(self):
        self.inject_sidebar_css()

    def inject_sidebar_css(self):
        """Inject responsive sidebar CSS."""
        css = """
        <style>
        /* Responsive Sidebar */
        @media (max-width: 768px) {
            /* Collapsible sidebar sections */
            .css-1d391kg {
                padding-top: 1rem !important;
            }

            /* Smaller sidebar width on tablets */
            .css-1d391kg {
                width: 280px !important;
            }
        }

        @media (max-width: 640px) {
            /* Even smaller sidebar on mobile */
            .css-1d391kg {
                width: 260px !important;
            }

            /* Hide sidebar by default on mobile, show as overlay */
            .css-1d391kg {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }

            .css-1d391kg.sidebar-open {
                transform: translateX(0);
            }
        }

        /* Compact sidebar controls */
        .sidebar-section {
            margin-bottom: 1rem;
        }

        .sidebar-section .stExpander {
            border: 1px solid #e6e6e6;
            border-radius: 0.25rem;
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    def create_collapsible_section(
        self,
        title: str,
        icon: str = "",
        expanded: bool = False,
        key_suffix: str = ""
    ) -> Any:
        """
        Create collapsible sidebar section.

        Args:
            title: Section title
            icon: Optional icon
            expanded: Whether expanded by default
            key_suffix: Unique key suffix

        Returns:
            Expander context manager
        """
        display_title = f"{icon} {title}" if icon else title

        return st.sidebar.expander(
            display_title,
            expanded=expanded
        )

    def responsive_control_group(
        self,
        controls: List[Dict[str, Any]],
        title: str,
        icon: str = "",
        expanded: bool = True
    ) -> Dict[str, Any]:
        """
        Create responsive control group.

        Args:
            controls: List of control configurations
            title: Group title
            icon: Optional icon
            expanded: Whether expanded by default

        Returns:
            Dictionary of control values
        """
        results = {}

        with self.create_collapsible_section(title, icon, expanded):
            for control in controls:
                control_type = control.get('type', 'text_input')
                key = control.get('key', 'control')
                label = control.get('label', 'Control')

                if control_type == 'selectbox':
                    results[key] = st.selectbox(
                        label,
                        options=control.get('options', []),
                        index=control.get('default_index', 0),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )
                elif control_type == 'slider':
                    results[key] = st.slider(
                        label,
                        min_value=control.get('min', 0),
                        max_value=control.get('max', 100),
                        value=control.get('default', 50),
                        step=control.get('step', 1),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )
                elif control_type == 'number_input':
                    results[key] = st.number_input(
                        label,
                        min_value=control.get('min', 0.0),
                        max_value=control.get('max', 100.0),
                        value=control.get('default', 10.0),
                        step=control.get('step', 0.1),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )
                elif control_type == 'radio':
                    results[key] = st.radio(
                        label,
                        options=control.get('options', []),
                        index=control.get('default_index', 0),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )
                elif control_type == 'checkbox':
                    results[key] = st.checkbox(
                        label,
                        value=control.get('default', False),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )
                else:  # Default to text_input
                    results[key] = st.text_input(
                        label,
                        value=control.get('default', ''),
                        key=f"sidebar_{key}",
                        help=control.get('help')
                    )

        return results

# Global instances
responsive_tabs = ResponsiveTabNavigation()
responsive_sidebar = ResponsiveSidebar()

def configure_responsive_navigation():
    """Configure the responsive navigation system."""
    responsive_tabs.inject_navigation_css()
    responsive_sidebar.inject_sidebar_css()