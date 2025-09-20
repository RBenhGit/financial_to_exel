"""
Accessibility Features for Financial Analysis Application

Implements WCAG 2.1 compliance features including keyboard navigation,
screen reader support, color contrast, and accessible form controls.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class AccessibilityManager:
    """Manages accessibility features and WCAG compliance."""

    def __init__(self):
        self.inject_accessibility_css()

    def inject_accessibility_css(self):
        """Inject accessibility-focused CSS."""
        css = """
        <style>
        /* WCAG 2.1 Compliance Features */

        /* Focus Management */
        *:focus {
            outline: 2px solid #0066cc !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.3) !important;
        }

        /* Skip Links */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            z-index: 9999;
            border-radius: 0 0 4px 4px;
        }

        .skip-link:focus {
            top: 0;
        }

        /* Screen Reader Only Content */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        /* High Contrast Mode Support */
        @media (prefers-contrast: high) {
            .stButton > button {
                border: 2px solid !important;
            }

            .stSelectbox > div > div {
                border: 2px solid !important;
            }

            .metric-card {
                border: 2px solid #333 !important;
            }
        }

        /* Reduced Motion Support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* Color Contrast Improvements */
        .high-contrast {
            background-color: #000 !important;
            color: #fff !important;
        }

        .high-contrast .stButton > button {
            background-color: #fff !important;
            color: #000 !important;
            border: 2px solid #fff !important;
        }

        .high-contrast .stSelectbox {
            background-color: #fff !important;
            color: #000 !important;
        }

        /* Accessible Form Controls */
        .accessible-form-group {
            margin-bottom: 1.5rem;
        }

        .accessible-form-label {
            font-weight: bold;
            margin-bottom: 0.5rem;
            display: block;
        }

        .accessible-form-help {
            font-size: 0.875rem;
            color: #666;
            margin-top: 0.25rem;
        }

        .accessible-form-error {
            color: #dc3545;
            font-weight: bold;
            margin-top: 0.25rem;
        }

        /* Accessible Tables */
        .accessible-table {
            border-collapse: collapse;
            width: 100%;
        }

        .accessible-table th,
        .accessible-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        .accessible-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }

        /* Keyboard Navigation Indicators */
        .keyboard-focus {
            border: 3px solid #0066cc;
            border-radius: 4px;
        }

        /* Touch Target Improvements */
        @media (pointer: coarse) {
            .stButton > button {
                min-height: 44px !important;
                min-width: 44px !important;
                padding: 12px !important;
            }

            .stSelectbox > div > div {
                min-height: 44px !important;
            }

            .stSlider {
                height: 44px !important;
            }
        }

        /* Error and Success States */
        .accessible-error {
            background-color: #fff5f5;
            border: 2px solid #dc3545;
            border-radius: 4px;
            padding: 1rem;
            margin: 1rem 0;
        }

        .accessible-success {
            background-color: #f0fff4;
            border: 2px solid #28a745;
            border-radius: 4px;
            padding: 1rem;
            margin: 1rem 0;
        }

        .accessible-warning {
            background-color: #fffacd;
            border: 2px solid #ffc107;
            border-radius: 4px;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Loading State Accessibility */
        .accessible-loading {
            position: relative;
        }

        .accessible-loading::after {
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #0066cc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }

        /* Accessible Charts */
        .accessible-chart {
            position: relative;
        }

        .accessible-chart .chart-description {
            position: absolute;
            left: -10000px;
            top: auto;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }

        .accessible-chart:focus .chart-description {
            position: static;
            width: auto;
            height: auto;
            overflow: visible;
            background: #fff;
            border: 1px solid #ccc;
            padding: 10px;
            margin-top: 10px;
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    def add_skip_navigation(self, target_id: str = "main-content"):
        """Add skip navigation link for keyboard users."""
        skip_link_html = f'''
        <a href="#{target_id}" class="skip-link">
            Skip to main content
        </a>
        '''
        st.markdown(skip_link_html, unsafe_allow_html=True)

    def create_accessible_form_group(
        self,
        label: str,
        control_func: callable,
        help_text: Optional[str] = None,
        error_message: Optional[str] = None,
        required: bool = False,
        field_id: Optional[str] = None
    ) -> Any:
        """
        Create an accessible form group with proper labeling and error handling.

        Args:
            label: Form field label
            control_func: Function that renders the form control
            help_text: Optional help text
            error_message: Optional error message
            required: Whether field is required
            field_id: Unique field identifier

        Returns:
            Form control value
        """
        with st.container():
            st.markdown('<div class="accessible-form-group">', unsafe_allow_html=True)

            # Label with required indicator
            label_text = f"{label}{'*' if required else ''}"
            st.markdown(
                f'<label class="accessible-form-label" for="{field_id or label.lower().replace(" ", "_")}">'
                f'{label_text}'
                f'</label>',
                unsafe_allow_html=True
            )

            # Screen reader text for required fields
            if required:
                st.markdown(
                    '<span class="sr-only">Required field</span>',
                    unsafe_allow_html=True
                )

            # Form control
            value = control_func()

            # Help text
            if help_text:
                st.markdown(
                    f'<div class="accessible-form-help" id="{field_id or label.lower().replace(" ", "_")}_help">'
                    f'{help_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Error message
            if error_message:
                st.markdown(
                    f'<div class="accessible-form-error" role="alert" aria-live="polite">'
                    f'Error: {error_message}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)
            return value

    def accessible_metric(
        self,
        label: str,
        value: str,
        delta: Optional[str] = None,
        help_text: Optional[str] = None,
        trend_description: Optional[str] = None
    ) -> None:
        """
        Display an accessible metric with proper ARIA labels and descriptions.

        Args:
            label: Metric label
            value: Metric value
            delta: Change indicator
            help_text: Help text
            trend_description: Description of trend for screen readers
        """
        # Create comprehensive screen reader description
        sr_description = f"Metric: {label}. Value: {value}."
        if delta:
            sr_description += f" Change: {delta}."
        if trend_description:
            sr_description += f" Trend: {trend_description}."
        if help_text:
            sr_description += f" Description: {help_text}."

        with st.container():
            # Hidden description for screen readers
            st.markdown(
                f'<div class="sr-only">{sr_description}</div>',
                unsafe_allow_html=True
            )

            # Visual metric
            st.metric(
                label=label,
                value=value,
                delta=delta,
                help=help_text
            )

    def accessible_chart(
        self,
        chart_object: Any,
        title: str,
        description: str,
        data_table: Optional[Any] = None
    ) -> None:
        """
        Display an accessible chart with alternative text descriptions.

        Args:
            chart_object: Chart object (plotly, etc.)
            title: Chart title
            description: Text description of chart content
            data_table: Optional data table as alternative
        """
        with st.container():
            st.markdown('<div class="accessible-chart" tabindex="0">', unsafe_allow_html=True)

            # Chart title
            st.markdown(f"#### {title}")

            # Hidden description for screen readers
            st.markdown(
                f'<div class="chart-description">'
                f'Chart description: {description}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Display chart
            if hasattr(chart_object, 'update_layout'):  # Plotly chart
                chart_object.update_layout(
                    title_text=title,
                    title_x=0.5
                )

            st.plotly_chart(chart_object, use_container_width=True)

            # Alternative data table
            if data_table is not None:
                with st.expander("View chart data as table"):
                    st.dataframe(data_table, use_container_width=True)

            st.markdown('</div>', unsafe_allow_html=True)

    def accessible_alert(
        self,
        message: str,
        alert_type: str = "info",
        dismissible: bool = False,
        live_region: bool = True
    ) -> None:
        """
        Display an accessible alert message.

        Args:
            message: Alert message
            alert_type: Type of alert (success, error, warning, info)
            dismissible: Whether alert can be dismissed
            live_region: Whether to announce to screen readers
        """
        role = "alert" if alert_type == "error" else "status"
        aria_live = "assertive" if alert_type == "error" else "polite"

        css_class = f"accessible-{alert_type}"

        alert_html = f'''
        <div class="{css_class}" role="{role}" aria-live="{aria_live if live_region else "off"}">
            <strong>{alert_type.title()}:</strong> {message}
        </div>
        '''

        st.markdown(alert_html, unsafe_allow_html=True)

    def add_landmark_navigation(self) -> None:
        """Add ARIA landmark navigation."""
        landmarks_html = '''
        <nav aria-label="Page landmarks" class="sr-only">
            <ul>
                <li><a href="#main-content">Main content</a></li>
                <li><a href="#navigation">Navigation</a></li>
                <li><a href="#sidebar">Sidebar controls</a></li>
            </ul>
        </nav>
        '''
        st.markdown(landmarks_html, unsafe_allow_html=True)

    def keyboard_navigation_helper(self) -> None:
        """Add keyboard navigation helper."""
        help_text = '''
        <div class="sr-only" aria-live="polite">
            Keyboard navigation: Use Tab to move forward, Shift+Tab to move backward,
            Enter or Space to activate buttons, Arrow keys to navigate within components.
        </div>
        '''
        st.markdown(help_text, unsafe_allow_html=True)

    def announce_loading_state(self, is_loading: bool, message: str = "Loading...") -> None:
        """Announce loading state to screen readers."""
        if is_loading:
            st.markdown(
                f'<div aria-live="polite" aria-busy="true" class="sr-only">{message}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div aria-live="polite" aria-busy="false" class="sr-only">Loading complete</div>',
                unsafe_allow_html=True
            )

    def create_accessible_table(
        self,
        df: Any,
        caption: str,
        summary: Optional[str] = None,
        sortable: bool = True
    ) -> None:
        """
        Create an accessible data table.

        Args:
            df: DataFrame to display
            caption: Table caption
            summary: Optional table summary
            sortable: Whether table is sortable
        """
        with st.container():
            st.markdown(f"#### {caption}")

            if summary:
                st.markdown(
                    f'<div class="sr-only">Table summary: {summary}</div>',
                    unsafe_allow_html=True
                )

            # Add sortable instruction for screen readers
            if sortable:
                st.markdown(
                    '<div class="sr-only">This table is sortable. Click column headers to sort.</div>',
                    unsafe_allow_html=True
                )

            st.dataframe(df, use_container_width=True)

    def color_contrast_toggle(self) -> bool:
        """Add high contrast mode toggle."""
        return st.checkbox(
            "High Contrast Mode",
            help="Toggle high contrast mode for better visibility",
            key="accessibility_high_contrast"
        )

    def font_size_control(self) -> str:
        """Add font size control."""
        return st.selectbox(
            "Font Size",
            options=["Small", "Medium", "Large", "Extra Large"],
            index=1,
            help="Adjust text size for better readability",
            key="accessibility_font_size"
        )

# Global accessibility manager
accessibility_manager = AccessibilityManager()

def configure_accessibility_features():
    """Configure all accessibility features."""
    accessibility_manager.inject_accessibility_css()
    accessibility_manager.add_skip_navigation()
    accessibility_manager.add_landmark_navigation()
    accessibility_manager.keyboard_navigation_helper()

def create_accessibility_controls() -> Dict[str, Any]:
    """Create accessibility control panel."""
    with st.sidebar.expander("♿ Accessibility Options", expanded=False):
        controls = {}

        controls['high_contrast'] = accessibility_manager.color_contrast_toggle()
        controls['font_size'] = accessibility_manager.font_size_control()

        st.markdown("---")
        st.markdown("**Keyboard Navigation:**")
        st.markdown("- Tab/Shift+Tab: Navigate")
        st.markdown("- Enter/Space: Activate")
        st.markdown("- Arrow keys: Navigate lists")

        return controls