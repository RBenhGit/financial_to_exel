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

        /* RTL Text Support */
        .rtl-support {
            direction: rtl;
            text-align: right;
        }

        .rtl-support .stButton > button {
            margin-left: 0;
            margin-right: auto;
        }

        /* Dyslexia-Friendly Font Support */
        .dyslexic-font {
            font-family: 'OpenDyslexic', 'Arial', sans-serif !important;
            letter-spacing: 0.1em;
            line-height: 1.6;
        }

        /* Text Scaling Support */
        .text-scale-small { font-size: 0.8em !important; }
        .text-scale-medium { font-size: 1.0em !important; }
        .text-scale-large { font-size: 1.2em !important; }
        .text-scale-xlarge { font-size: 1.5em !important; }
        .text-scale-custom { font-size: var(--custom-text-scale, 1em) !important; }

        /* Colorblind-Friendly Color Schemes */
        .colorblind-deuteranopia {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --accent-color: #2ca02c;
            --warning-color: #d62728;
        }

        .colorblind-protanopia {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --accent-color: #2ca02c;
            --warning-color: #d62728;
        }

        .colorblind-tritanopia {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --accent-color: #2ca02c;
            --warning-color: #d62728;
        }

        /* Voice Input Indicator */
        .voice-input-active {
            border: 3px solid #ff4444 !important;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 68, 68, 0); }
        }

        /* Enhanced Focus Indicators */
        .enhanced-focus:focus {
            outline: 3px solid #0066cc !important;
            outline-offset: 3px !important;
            box-shadow: 0 0 0 6px rgba(0, 102, 204, 0.3) !important;
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

    def colorblind_friendly_palette_control(self) -> str:
        """Add colorblind-friendly palette selection."""
        return st.selectbox(
            "Color Palette",
            options=[
                "Default",
                "Deuteranopia Safe",
                "Protanopia Safe",
                "Tritanopia Safe",
                "High Contrast",
                "Viridis",
                "Cividis"
            ],
            index=0,
            help="Select colorblind-friendly color palette for charts and visualizations",
            key="accessibility_colorblind_palette"
        )

    def dyslexia_friendly_font_control(self) -> str:
        """Add dyslexia-friendly font selection."""
        return st.selectbox(
            "Font Family",
            options=[
                "Default",
                "OpenDyslexic",
                "Arial",
                "Verdana",
                "Calibri",
                "Comic Sans MS"
            ],
            index=0,
            help="Select dyslexia-friendly fonts for better readability",
            key="accessibility_dyslexia_font"
        )

    def text_scaling_control(self) -> float:
        """Add text scaling control."""
        return st.slider(
            "Text Scale",
            min_value=0.8,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Scale text size from 80% to 200%",
            key="accessibility_text_scale"
        )

    def language_selection_control(self) -> str:
        """Add language selection control."""
        return st.selectbox(
            "Language",
            options=[
                "English",
                "Spanish",
                "French",
                "German",
                "Chinese (Simplified)",
                "Japanese",
                "Arabic",
                "Hebrew"
            ],
            index=0,
            help="Select interface language",
            key="accessibility_language"
        )

    def voice_input_control(self) -> bool:
        """Add voice input toggle."""
        return st.checkbox(
            "🎤 Voice Input",
            help="Enable voice input for text fields (requires browser support)",
            key="accessibility_voice_input"
        )

    def text_to_speech_control(self) -> bool:
        """Add text-to-speech toggle."""
        return st.checkbox(
            "🔊 Text-to-Speech",
            help="Enable text-to-speech for content reading",
            key="accessibility_text_to_speech"
        )

    def rtl_text_support_control(self) -> bool:
        """Add RTL text support toggle."""
        return st.checkbox(
            "📝 RTL Text Support",
            help="Enable right-to-left text support for Arabic, Hebrew, etc.",
            key="accessibility_rtl_support"
        )

    def apply_accessibility_settings(self, settings: Dict[str, Any]) -> None:
        """Apply accessibility settings to the interface."""
        # Apply text scaling
        if settings.get('text_scale') and settings['text_scale'] != 1.0:
            scale_css = f"""
            <style>
            :root {{
                --custom-text-scale: {settings['text_scale']}em;
            }}
            .stApp {{
                font-size: var(--custom-text-scale) !important;
            }}
            </style>
            """
            st.markdown(scale_css, unsafe_allow_html=True)

        # Apply dyslexia-friendly font
        if settings.get('dyslexia_font') and settings['dyslexia_font'] != "Default":
            font_css = """
            <style>
            .stApp {
                font-family: 'OpenDyslexic', 'Arial', sans-serif !important;
                letter-spacing: 0.1em !important;
                line-height: 1.6 !important;
            }
            </style>
            """
            st.markdown(font_css, unsafe_allow_html=True)

        # Apply RTL support
        if settings.get('rtl_support'):
            rtl_css = """
            <style>
            .stApp {
                direction: rtl !important;
                text-align: right !important;
            }
            .stButton > button {
                margin-left: 0 !important;
                margin-right: auto !important;
            }
            </style>
            """
            st.markdown(rtl_css, unsafe_allow_html=True)

        # Apply colorblind-friendly palette
        if settings.get('colorblind_palette') and settings['colorblind_palette'] != "Default":
            palette_class = f"colorblind-{settings['colorblind_palette'].lower().replace(' ', '-')}"
            palette_css = f"""
            <style>
            .stApp {{
                color-scheme: {palette_class};
            }}
            </style>
            """
            st.markdown(palette_css, unsafe_allow_html=True)

    def add_voice_input_support(self, element_id: str) -> None:
        """Add voice input support to a text element."""
        voice_js = f"""
        <script>
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            const element = document.getElementById('{element_id}');
            if (element) {{
                const voiceButton = document.createElement('button');
                voiceButton.innerHTML = '🎤';
                voiceButton.title = 'Voice Input';
                voiceButton.onclick = function() {{
                    element.classList.add('voice-input-active');
                    recognition.start();
                }};

                element.parentNode.appendChild(voiceButton);

                recognition.onresult = function(event) {{
                    const result = event.results[0][0].transcript;
                    element.value = result;
                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    element.classList.remove('voice-input-active');
                }};

                recognition.onerror = function(event) {{
                    element.classList.remove('voice-input-active');
                    console.log('Voice recognition error:', event.error);
                }};
            }}
        }}
        </script>
        """
        st.markdown(voice_js, unsafe_allow_html=True)

    def add_text_to_speech_support(self, text: str, element_id: str) -> None:
        """Add text-to-speech support for content."""
        tts_js = f"""
        <script>
        function speakText_{element_id}() {{
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance('{text}');
                utterance.rate = 0.8;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                speechSynthesis.speak(utterance);
            }}
        }}

        const element = document.getElementById('{element_id}');
        if (element) {{
            const speakButton = document.createElement('button');
            speakButton.innerHTML = '🔊';
            speakButton.title = 'Read Aloud';
            speakButton.onclick = speakText_{element_id};
            element.parentNode.appendChild(speakButton);
        }}
        </script>
        """
        st.markdown(tts_js, unsafe_allow_html=True)

    def create_enhanced_accessibility_controls(self) -> Dict[str, Any]:
        """Create enhanced accessibility control panel with all features."""
        with st.sidebar.expander("♿ Enhanced Accessibility", expanded=False):
            controls = {}

            st.markdown("### 🎨 Visual Accessibility")
            controls['high_contrast'] = self.color_contrast_toggle()
            controls['colorblind_palette'] = self.colorblind_friendly_palette_control()
            controls['font_size'] = self.font_size_control()
            controls['text_scale'] = self.text_scaling_control()

            st.markdown("### 📝 Reading & Writing")
            controls['dyslexia_font'] = self.dyslexia_friendly_font_control()
            controls['rtl_support'] = self.rtl_text_support_control()

            st.markdown("### 🎤 Voice & Audio")
            controls['voice_input'] = self.voice_input_control()
            controls['text_to_speech'] = self.text_to_speech_control()

            st.markdown("### 🌍 Language & Localization")
            controls['language'] = self.language_selection_control()

            st.markdown("---")
            st.markdown("**⌨️ Keyboard Shortcuts:**")
            st.markdown("- Tab/Shift+Tab: Navigate elements")
            st.markdown("- Enter/Space: Activate buttons")
            st.markdown("- Arrow keys: Navigate lists/menus")
            st.markdown("- Ctrl+'/': Toggle accessibility help")

            # Apply settings immediately
            self.apply_accessibility_settings(controls)

            return controls

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
    return accessibility_manager.create_enhanced_accessibility_controls()