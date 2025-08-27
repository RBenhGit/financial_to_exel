"""
Base Presenter Class
===================

Abstract base class for all presenters that handle the coordination
between business logic and UI components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class BasePresenter(ABC):
    """Base presenter class for coordinating business logic and UI"""
    
    def __init__(self, presenter_id: str):
        self.presenter_id = presenter_id
        self.state_key = f"presenter_{presenter_id}"
        self._ui_components = {}
        self._business_services = {}
    
    def register_ui_component(self, component_name: str, component: Any) -> None:
        """Register a UI component with this presenter"""
        self._ui_components[component_name] = component
        logger.debug(f"Registered UI component '{component_name}' in presenter '{self.presenter_id}'")
    
    def register_business_service(self, service_name: str, service: Any) -> None:
        """Register a business service with this presenter"""
        self._business_services[service_name] = service
        logger.debug(f"Registered business service '{service_name}' in presenter '{self.presenter_id}'")
    
    def get_ui_component(self, component_name: str) -> Optional[Any]:
        """Get registered UI component by name"""
        return self._ui_components.get(component_name)
    
    def get_business_service(self, service_name: str) -> Optional[Any]:
        """Get registered business service by name"""
        return self._business_services.get(service_name)
    
    def get_presenter_state(self) -> Dict[str, Any]:
        """Get presenter state from Streamlit session state"""
        return st.session_state.get(self.state_key, {})
    
    def set_presenter_state(self, state: Dict[str, Any]) -> None:
        """Set presenter state in Streamlit session state"""
        st.session_state[self.state_key] = state
    
    def update_presenter_state(self, updates: Dict[str, Any]) -> None:
        """Update specific fields in presenter state"""
        current_state = self.get_presenter_state()
        current_state.update(updates)
        self.set_presenter_state(current_state)
    
    @abstractmethod
    def present(self, **kwargs) -> Dict[str, Any]:
        """
        Main presentation method - coordinates business logic and UI rendering
        
        Returns:
            Dictionary containing presentation results and user interactions
        """
        pass
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """Standard error handling for presentations"""
        error_msg = f"Error in {self.presenter_id}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg, exc_info=True)
        st.error(f"⚠️ {error_msg}")
    
    def format_currency(self, value: float, currency: str = "$") -> str:
        """Format currency values for display"""
        if abs(value) >= 1e9:
            return f"{currency}{value/1e9:.1f}B"
        elif abs(value) >= 1e6:
            return f"{currency}{value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"{currency}{value/1e3:.1f}K"
        else:
            return f"{currency}{value:.2f}"
    
    def format_percentage(self, value: float, decimal_places: int = 2) -> str:
        """Format percentage values for display"""
        return f"{value*100:.{decimal_places}f}%"
    
    def validate_input_data(self, required_fields: List[str], 
                          input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that required input fields are present and valid
        
        Args:
            required_fields: List of required field names
            input_data: Dictionary of input data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in input_data:
                missing_fields.append(field)
            elif input_data[field] is None:
                missing_fields.append(field)
            elif isinstance(input_data[field], str) and not input_data[field].strip():
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, None