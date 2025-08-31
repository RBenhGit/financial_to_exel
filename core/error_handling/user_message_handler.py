"""
User Message Handler Module
===========================

This module provides user-friendly error messaging and guidance system for the
financial analysis application. It translates technical errors into actionable
user guidance and provides contextual help based on the current situation.

Features:
- Context-aware error message translation
- Actionable guidance and recommendations
- Severity-based message classification
- Streamlit integration for UI messaging
- Progressive disclosure of technical details
- Recovery suggestions and next steps

Classes:
    UserMessageHandler: Main message handling and UI integration
    MessageSeverity: Classification of message importance
    UserMessage: Structured user message with guidance
    StreamlitMessenger: Streamlit-specific UI integration
"""

import logging
import streamlit as st
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


class MessageSeverity(Enum):
    """Severity levels for user messages"""
    INFO = "info"           # General information, no action needed
    SUCCESS = "success"     # Operation completed successfully
    WARNING = "warning"     # Attention needed, but not blocking
    ERROR = "error"         # Something went wrong, action needed
    CRITICAL = "critical"   # Critical error, service may be unusable


class MessageCategory(Enum):
    """Categories of user messages for contextual handling"""
    API_ERROR = "api_error"                 # External API failures
    DATA_QUALITY = "data_quality"           # Data quality issues
    DEGRADED_SERVICE = "degraded_service"   # Service degradation
    USER_INPUT = "user_input"               # User input validation
    CALCULATION = "calculation"             # Calculation errors
    SYSTEM = "system"                       # General system messages


@dataclass
class UserMessage:
    """Structured user message with guidance"""
    title: str
    message: str
    severity: MessageSeverity
    category: MessageCategory
    
    # User guidance
    what_happened: str = ""
    why_it_happened: str = ""
    what_to_do: str = ""
    
    # Action items
    immediate_actions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    # Technical details (collapsible)
    technical_details: str = ""
    error_code: Optional[str] = None
    
    # Context
    affected_features: List[str] = field(default_factory=list)
    available_alternatives: List[str] = field(default_factory=list)
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    show_until: Optional[datetime] = None


class UserMessageHandler:
    """
    Main handler for creating and managing user-friendly messages
    """
    
    def __init__(self):
        self.message_templates = self._initialize_message_templates()
        self.active_messages: List[UserMessage] = []
        
    def _initialize_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize templates for common error scenarios"""
        return {
            "api_rate_limit": {
                "title": "Data Update Temporarily Limited",
                "what_happened": "We've reached the rate limit for market data updates.",
                "why_it_happened": "External data providers limit how frequently we can request updates to ensure fair usage.",
                "what_to_do": "The system will automatically retry in a few moments. Your analysis will continue with slightly older data.",
                "immediate_actions": ["Continue with current analysis", "Wait 1-2 minutes for automatic retry"],
                "recommended_actions": ["Consider upgrading to premium data plan for higher limits"]
            },
            
            "api_authentication": {
                "title": "Data Service Configuration Issue", 
                "what_happened": "Unable to authenticate with market data provider.",
                "why_it_happened": "API key may be invalid, expired, or not properly configured.",
                "what_to_do": "Check your API key configuration in the system settings.",
                "immediate_actions": ["Verify API keys in configuration", "Contact administrator"],
                "recommended_actions": ["Update API keys", "Switch to alternative data source"]
            },
            
            "network_error": {
                "title": "Connection Issue",
                "what_happened": "Unable to connect to market data services.",
                "why_it_happened": "This could be due to internet connectivity issues or temporary service outages.",
                "what_to_do": "Check your internet connection. The system will use cached data if available.",
                "immediate_actions": ["Check internet connection", "Try refreshing the page"],
                "recommended_actions": ["Wait a few minutes and retry", "Use historical analysis mode"]
            },
            
            "data_quality_poor": {
                "title": "Data Quality Warning",
                "what_happened": "The quality of available market data is below recommended levels.",
                "why_it_happened": "Insufficient peer companies, missing data, or inconsistent information.",
                "what_to_do": "Results may be less reliable. Consider using historical analysis only.",
                "immediate_actions": ["Review results with caution", "Consider manual verification"],
                "recommended_actions": ["Try different sector criteria", "Use historical data instead"]
            },
            
            "service_degraded": {
                "title": "Limited Service Mode",
                "what_happened": "Some analysis features are temporarily unavailable.",
                "why_it_happened": "External data sources are experiencing issues.",
                "what_to_do": "Basic analysis is still available using historical data.",
                "immediate_actions": ["Use available features", "Save current work"],
                "recommended_actions": ["Check back later for full features", "Export results before refreshing"]
            }
        }
    
    def create_api_error_message(self, api_failure) -> UserMessage:
        """Create user message for API failures"""
        if hasattr(api_failure, 'category'):
            if api_failure.category.value == "rate_limit":
                template = self.message_templates["api_rate_limit"]
                severity = MessageSeverity.WARNING
            elif api_failure.category.value == "authentication":
                template = self.message_templates["api_authentication"] 
                severity = MessageSeverity.ERROR
            elif api_failure.category.value == "network_error":
                template = self.message_templates["network_error"]
                severity = MessageSeverity.WARNING
            else:
                template = {
                    "title": "Data Service Error",
                    "what_happened": "External data service is temporarily unavailable.",
                    "why_it_happened": "The service may be experiencing technical issues.",
                    "what_to_do": "The system will retry automatically and use cached data when possible.",
                    "immediate_actions": ["Continue with available data"],
                    "recommended_actions": ["Try again later", "Use historical analysis"]
                }
                severity = MessageSeverity.ERROR
        else:
            template = self.message_templates["network_error"]
            severity = MessageSeverity.ERROR
        
        return UserMessage(
            title=template["title"],
            message=api_failure.user_message if hasattr(api_failure, 'user_message') else template["what_happened"],
            severity=severity,
            category=MessageCategory.API_ERROR,
            what_happened=template["what_happened"],
            why_it_happened=template["why_it_happened"], 
            what_to_do=template["what_to_do"],
            immediate_actions=template["immediate_actions"],
            recommended_actions=template["recommended_actions"],
            technical_details=api_failure.error_message if hasattr(api_failure, 'error_message') else str(api_failure),
            affected_features=["Real-time market data", "Industry comparisons"],
            available_alternatives=["Historical analysis", "Excel-based calculations"]
        )
    
    def create_data_quality_message(self, validation_result) -> UserMessage:
        """Create user message for data quality issues"""
        if hasattr(validation_result, 'quality_level'):
            quality_level = validation_result.quality_level.value
            
            if quality_level in ["excellent", "good"]:
                return None  # No message needed for good quality
            
            elif quality_level == "acceptable":
                severity = MessageSeverity.INFO
                title = "Data Quality: Acceptable"
                message = "Data quality is acceptable but could be better. Results should be reliable."
            
            elif quality_level == "poor":
                severity = MessageSeverity.WARNING
                title = "Data Quality: Poor"
                message = "Data quality is poor. Use results with caution."
                
            else:  # unusable
                severity = MessageSeverity.ERROR
                title = "Data Quality: Unusable" 
                message = "Data quality is too poor for reliable analysis."
        else:
            severity = MessageSeverity.WARNING
            title = "Data Quality Warning"
            message = "Unable to assess data quality. Results may be unreliable."
        
        template = self.message_templates["data_quality_poor"]
        
        issues = validation_result.issues if hasattr(validation_result, 'issues') else []
        recommendations = validation_result.recommendations if hasattr(validation_result, 'recommendations') else []
        
        return UserMessage(
            title=title,
            message=message,
            severity=severity,
            category=MessageCategory.DATA_QUALITY,
            what_happened=template["what_happened"],
            why_it_happened="; ".join(issues) if issues else template["why_it_happened"],
            what_to_do=template["what_to_do"],
            immediate_actions=template["immediate_actions"],
            recommended_actions=recommendations if recommendations else template["recommended_actions"],
            technical_details=f"Issues: {'; '.join(issues)}" if issues else "",
            affected_features=["Industry comparisons", "Peer analysis"],
            available_alternatives=["Historical analysis", "Manual verification"]
        )
    
    def create_degradation_message(self, degradation_result) -> UserMessage:
        """Create user message for service degradation"""
        template = self.message_templates["service_degraded"]
        
        if hasattr(degradation_result, 'degradation_level'):
            level = degradation_result.degradation_level.value
            
            if level == "full_service":
                return None  # No message needed
            elif level == "reduced_industry":
                severity = MessageSeverity.INFO
                title = "Limited Industry Data"
            elif level == "historical_only":
                severity = MessageSeverity.WARNING 
                title = "Historical Analysis Only"
            elif level == "basic_metrics":
                severity = MessageSeverity.WARNING
                title = "Basic Analysis Mode"
            elif level == "minimal_service":
                severity = MessageSeverity.ERROR
                title = "Minimal Service Mode"
            else:
                severity = MessageSeverity.CRITICAL
                title = "Service Unavailable"
        else:
            severity = MessageSeverity.WARNING
            title = template["title"]
        
        return UserMessage(
            title=title,
            message=degradation_result.user_message if hasattr(degradation_result, 'user_message') else template["what_happened"],
            severity=severity,
            category=MessageCategory.DEGRADED_SERVICE,
            what_happened=template["what_happened"],
            why_it_happened=degradation_result.technical_details if hasattr(degradation_result, 'technical_details') else template["why_it_happened"],
            what_to_do=template["what_to_do"],
            immediate_actions=template["immediate_actions"],
            recommended_actions=degradation_result.recommendations if hasattr(degradation_result, 'recommendations') else template["recommended_actions"],
            technical_details=degradation_result.technical_details if hasattr(degradation_result, 'technical_details') else "",
            affected_features=degradation_result.disabled_features if hasattr(degradation_result, 'disabled_features') else [],
            available_alternatives=degradation_result.available_features if hasattr(degradation_result, 'available_features') else []
        )
    
    def add_message(self, message: UserMessage):
        """Add a message to the active messages list"""
        self.active_messages.append(message)
        logger.info(f"User message added: {message.title} ({message.severity.value})")
    
    def clear_messages(self, category: Optional[MessageCategory] = None):
        """Clear messages, optionally filtered by category"""
        if category:
            self.active_messages = [msg for msg in self.active_messages if msg.category != category]
        else:
            self.active_messages.clear()
    
    def get_messages_by_severity(self, severity: MessageSeverity) -> List[UserMessage]:
        """Get messages filtered by severity"""
        return [msg for msg in self.active_messages if msg.severity == severity]


class StreamlitMessenger:
    """
    Streamlit-specific UI integration for user messages
    """
    
    def __init__(self, message_handler: UserMessageHandler):
        self.message_handler = message_handler
        
    def display_message(self, message: UserMessage, container=None):
        """Display a single message in Streamlit UI"""
        # Use provided container or default to main area
        display_container = container if container else st
        
        # Choose appropriate Streamlit message function based on severity
        if message.severity == MessageSeverity.SUCCESS:
            display_func = display_container.success
        elif message.severity == MessageSeverity.INFO:
            display_func = display_container.info
        elif message.severity == MessageSeverity.WARNING:
            display_func = display_container.warning
        elif message.severity in [MessageSeverity.ERROR, MessageSeverity.CRITICAL]:
            display_func = display_container.error
        else:
            display_func = display_container.info
        
        # Display main message
        with display_func(message.message):
            # Show available alternatives if any
            if message.available_alternatives:
                st.write("**Available features:**")
                for feature in message.available_alternatives:
                    st.write(f"• {feature}")
        
        # Show expandable details if requested
        if message.immediate_actions or message.recommended_actions or message.technical_details:
            with display_container.expander(f"ℹ️ More details about: {message.title}"):
                
                if message.what_happened:
                    st.write("**What happened:**")
                    st.write(message.what_happened)
                
                if message.why_it_happened:
                    st.write("**Why it happened:**")
                    st.write(message.why_it_happened)
                
                if message.what_to_do:
                    st.write("**What to do:**")
                    st.write(message.what_to_do)
                
                if message.immediate_actions:
                    st.write("**Immediate actions:**")
                    for action in message.immediate_actions:
                        st.write(f"• {action}")
                
                if message.recommended_actions:
                    st.write("**Recommended actions:**") 
                    for action in message.recommended_actions:
                        st.write(f"• {action}")
                
                if message.technical_details:
                    st.write("**Technical details:**")
                    st.code(message.technical_details)
    
    def display_all_messages(self, container=None):
        """Display all active messages"""
        if not self.message_handler.active_messages:
            return
        
        # Sort messages by severity (critical first)
        severity_order = {
            MessageSeverity.CRITICAL: 0,
            MessageSeverity.ERROR: 1, 
            MessageSeverity.WARNING: 2,
            MessageSeverity.INFO: 3,
            MessageSeverity.SUCCESS: 4
        }
        
        sorted_messages = sorted(
            self.message_handler.active_messages,
            key=lambda msg: severity_order.get(msg.severity, 5)
        )
        
        for message in sorted_messages:
            self.display_message(message, container)
    
    def display_status_banner(self, container=None):
        """Display a status banner summarizing current issues"""
        if not self.message_handler.active_messages:
            return
            
        display_container = container if container else st
        
        # Count messages by severity
        critical_count = len(self.message_handler.get_messages_by_severity(MessageSeverity.CRITICAL))
        error_count = len(self.message_handler.get_messages_by_severity(MessageSeverity.ERROR))
        warning_count = len(self.message_handler.get_messages_by_severity(MessageSeverity.WARNING))
        
        # Create status message
        if critical_count > 0:
            status_msg = f"🔴 {critical_count} critical issue(s)"
            display_container.error(status_msg)
        elif error_count > 0:
            status_msg = f"🟠 {error_count} error(s)"
            if warning_count > 0:
                status_msg += f", {warning_count} warning(s)"
            display_container.warning(status_msg)
        elif warning_count > 0:
            status_msg = f"🟡 {warning_count} warning(s) - limited functionality"
            display_container.info(status_msg)
    
    def create_error_summary_sidebar(self):
        """Create error summary in sidebar"""
        if not self.message_handler.active_messages:
            return
            
        with st.sidebar:
            st.subheader("🚨 Current Issues")
            
            for message in self.message_handler.active_messages:
                severity_icon = {
                    MessageSeverity.CRITICAL: "🔴",
                    MessageSeverity.ERROR: "🔴", 
                    MessageSeverity.WARNING: "🟡",
                    MessageSeverity.INFO: "ℹ️",
                    MessageSeverity.SUCCESS: "✅"
                }.get(message.severity, "ℹ️")
                
                st.write(f"{severity_icon} {message.title}")
                
                if message.affected_features:
                    st.caption(f"Affected: {', '.join(message.affected_features[:2])}")


# Global message handler instance
_global_message_handler = None
_global_streamlit_messenger = None


def get_message_handler() -> UserMessageHandler:
    """Get global message handler instance"""
    global _global_message_handler
    if _global_message_handler is None:
        _global_message_handler = UserMessageHandler()
    return _global_message_handler


def get_streamlit_messenger() -> StreamlitMessenger:
    """Get global Streamlit messenger instance"""
    global _global_streamlit_messenger
    if _global_streamlit_messenger is None:
        _global_streamlit_messenger = StreamlitMessenger(get_message_handler())
    return _global_streamlit_messenger