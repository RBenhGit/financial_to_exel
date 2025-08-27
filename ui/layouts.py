"""
Layout Components for Streamlit Application
===========================================

Layout managers that handle page structure and organization
without coupling to business logic.
"""

from typing import Dict, List, Optional, Any, Callable
import streamlit as st
from .components import UIComponent


class SidebarLayout(UIComponent):
    """Component for managing sidebar content and navigation"""
    
    def __init__(self, component_id: str = "sidebar"):
        super().__init__(component_id)
        self.sections = {}
    
    def add_section(self, section_id: str, title: str, 
                   render_func: Callable, expanded: bool = True) -> None:
        """Add a collapsible section to the sidebar"""
        self.sections[section_id] = {
            'title': title,
            'render_func': render_func,
            'expanded': expanded
        }
    
    def render(self, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Render sidebar with all configured sections"""
        sidebar_data = {}
        
        with st.sidebar:
            st.title("⚙️ Settings")
            
            for section_id, section_config in self.sections.items():
                with st.expander(section_config['title'], 
                               expanded=section_config['expanded']):
                    section_data = section_config['render_func'](data, **kwargs)
                    if section_data:
                        sidebar_data[section_id] = section_data
        
        return sidebar_data


class MainContentLayout(UIComponent):
    """Component for organizing main content area"""
    
    def __init__(self, component_id: str = "main_content"):
        super().__init__(component_id)
        self.content_areas = {}
    
    def add_content_area(self, area_id: str, render_func: Callable,
                        title: Optional[str] = None,
                        width_ratio: float = 1.0) -> None:
        """Add a content area to the main layout"""
        self.content_areas[area_id] = {
            'render_func': render_func,
            'title': title,
            'width_ratio': width_ratio
        }
    
    def render(self, data: Any = None, layout_type: str = "single_column", 
               **kwargs) -> Dict[str, Any]:
        """
        Render main content area
        
        Args:
            data: Data to pass to render functions
            layout_type: 'single_column', 'two_columns', or 'custom'
        """
        content_data = {}
        
        if layout_type == "single_column":
            for area_id, area_config in self.content_areas.items():
                if area_config['title']:
                    st.subheader(area_config['title'])
                
                area_data = area_config['render_func'](data, **kwargs)
                if area_data:
                    content_data[area_id] = area_data
        
        elif layout_type == "two_columns":
            # Split content areas across two columns
            areas = list(self.content_areas.items())
            left_areas = areas[:len(areas)//2]
            right_areas = areas[len(areas)//2:]
            
            col1, col2 = st.columns(2)
            
            with col1:
                for area_id, area_config in left_areas:
                    if area_config['title']:
                        st.subheader(area_config['title'])
                    
                    area_data = area_config['render_func'](data, **kwargs)
                    if area_data:
                        content_data[area_id] = area_data
            
            with col2:
                for area_id, area_config in right_areas:
                    if area_config['title']:
                        st.subheader(area_config['title'])
                    
                    area_data = area_config['render_func'](data, **kwargs)
                    if area_data:
                        content_data[area_id] = area_data
        
        elif layout_type == "custom":
            # Use width ratios for custom column layout
            if len(self.content_areas) > 1:
                ratios = [area['width_ratio'] for area in self.content_areas.values()]
                columns = st.columns(ratios)
                
                for i, (area_id, area_config) in enumerate(self.content_areas.items()):
                    with columns[i]:
                        if area_config['title']:
                            st.subheader(area_config['title'])
                        
                        area_data = area_config['render_func'](data, **kwargs)
                        if area_data:
                            content_data[area_id] = area_data
            else:
                # Single area
                area_id, area_config = next(iter(self.content_areas.items()))
                if area_config['title']:
                    st.subheader(area_config['title'])
                
                area_data = area_config['render_func'](data, **kwargs)
                if area_data:
                    content_data[area_id] = area_data
        
        return content_data


class TabsLayout(UIComponent):
    """Component for organizing content in tabs"""
    
    def __init__(self, component_id: str = "tabs"):
        super().__init__(component_id)
        self.tabs = {}
    
    def add_tab(self, tab_id: str, label: str, render_func: Callable,
               icon: Optional[str] = None) -> None:
        """Add a tab to the layout"""
        display_label = f"{icon} {label}" if icon else label
        self.tabs[tab_id] = {
            'label': display_label,
            'render_func': render_func
        }
    
    def render(self, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Render tabs layout"""
        if not self.tabs:
            st.warning("No tabs configured")
            return {}
        
        tab_labels = [tab_config['label'] for tab_config in self.tabs.values()]
        tab_objects = st.tabs(tab_labels)
        
        tabs_data = {}
        
        for i, (tab_id, tab_config) in enumerate(self.tabs.items()):
            with tab_objects[i]:
                tab_data = tab_config['render_func'](data, **kwargs)
                if tab_data:
                    tabs_data[tab_id] = tab_data
        
        return tabs_data


class ResponsiveLayout(UIComponent):
    """Responsive layout that adapts to screen size"""
    
    def render(self, content_func: Callable, data: Any = None,
               mobile_breakpoint: int = 768, **kwargs) -> Any:
        """
        Render responsive layout
        
        Args:
            content_func: Function to render content
            data: Data to pass to content function
            mobile_breakpoint: Screen width breakpoint for mobile layout
        """
        # Add responsive CSS
        st.markdown(
            f"""
            <style>
            @media (max-width: {mobile_breakpoint}px) {{
                .stTabs [data-baseweb="tab-list"] {{
                    gap: 2px;
                }}
                .stTabs [data-baseweb="tab"] {{
                    height: 50px;
                    padding-left: 10px;
                    padding-right: 10px;
                }}
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        return content_func(data, **kwargs)


class ContainerLayout(UIComponent):
    """Container layout with consistent styling"""
    
    def render(self, content_func: Callable, data: Any = None,
               container_type: str = "default", **kwargs) -> Any:
        """
        Render content in a container
        
        Args:
            content_func: Function to render content
            data: Data to pass to content function  
            container_type: 'default', 'card', or 'bordered'
        """
        if container_type == "card":
            with st.container():
                st.markdown(
                    """
                    <style>
                    .stContainer > div {
                        background-color: #f8f9fa;
                        padding: 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid #dee2e6;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                return content_func(data, **kwargs)
        
        elif container_type == "bordered":
            with st.container():
                st.markdown(
                    """
                    <style>
                    .stContainer > div {
                        border: 2px solid #007bff;
                        border-radius: 0.5rem;
                        padding: 1rem;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                return content_func(data, **kwargs)
        
        else:  # default
            with st.container():
                return content_func(data, **kwargs)