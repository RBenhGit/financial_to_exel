"""
Base UI Components for Financial Analysis
=========================================

Reusable presentation components that abstract Streamlit UI elements
from business logic, enabling clean separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class UIComponent(ABC):
    """Base class for all UI components"""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.state_key = f"ui_{component_id}"
    
    @abstractmethod
    def render(self, data: Any = None, **kwargs) -> Any:
        """Render the component with given data"""
        pass
    
    def get_state(self) -> Any:
        """Get component state from session state"""
        return st.session_state.get(self.state_key)
    
    def set_state(self, value: Any) -> None:
        """Set component state in session state"""
        st.session_state[self.state_key] = value


class MetricsDisplay(UIComponent):
    """Component for displaying financial metrics in cards/columns"""
    
    def render(self, metrics: Dict[str, Union[float, str]], 
               layout: str = "columns", 
               format_func: Optional[Callable] = None) -> None:
        """
        Render metrics display
        
        Args:
            metrics: Dictionary of metric name to value
            layout: 'columns', 'rows', or 'cards'  
            format_func: Optional formatting function for values
        """
        if not metrics:
            st.warning("No metrics data provided")
            return
            
        if layout == "columns":
            cols = st.columns(len(metrics))
            for i, (key, value) in enumerate(metrics.items()):
                formatted_value = format_func(value) if format_func else str(value)
                cols[i].metric(label=key, value=formatted_value)
                
        elif layout == "rows":
            for key, value in metrics.items():
                formatted_value = format_func(value) if format_func else str(value)
                st.metric(label=key, value=formatted_value)
                
        elif layout == "cards":
            for key, value in metrics.items():
                with st.container():
                    formatted_value = format_func(value) if format_func else str(value)
                    st.metric(label=key, value=formatted_value)


class ChartRenderer(UIComponent):
    """Component for rendering financial charts"""
    
    def render(self, chart_data: Dict[str, Any], 
               chart_type: str = "line",
               **chart_options) -> go.Figure:
        """
        Render financial chart
        
        Args:
            chart_data: Chart data and configuration
            chart_type: Type of chart ('line', 'bar', 'scatter', etc.)
            chart_options: Additional chart configuration options
            
        Returns:
            Plotly figure object
        """
        data = chart_data.get('data')
        if data is None:
            st.error("No chart data provided")
            return None
            
        title = chart_data.get('title', 'Financial Chart')
        x_col = chart_data.get('x_column', 'Year')
        y_col = chart_data.get('y_column', 'Value')
        
        if isinstance(data, pd.DataFrame):
            if chart_type == "line":
                fig = px.line(data, x=x_col, y=y_col, title=title, **chart_options)
            elif chart_type == "bar":
                fig = px.bar(data, x=x_col, y=y_col, title=title, **chart_options)
            elif chart_type == "scatter":
                fig = px.scatter(data, x=x_col, y=y_col, title=title, **chart_options)
            else:
                st.error(f"Unsupported chart type: {chart_type}")
                return None
        else:
            # Handle dictionary/list data
            fig = go.Figure()
            if chart_type == "line":
                fig.add_trace(go.Scatter(x=list(data.keys()), y=list(data.values()), mode='lines+markers'))
            elif chart_type == "bar":
                fig.add_trace(go.Bar(x=list(data.keys()), y=list(data.values())))
            
            fig.update_layout(title=title, **chart_options)
        
        st.plotly_chart(fig, use_container_width=True)
        return fig


class TableFormatter(UIComponent):
    """Component for displaying formatted data tables"""
    
    def render(self, data: pd.DataFrame,
               styling_config: Optional[Dict] = None,
               interactive: bool = True,
               download_filename: Optional[str] = None) -> None:
        """
        Render formatted data table
        
        Args:
            data: DataFrame to display
            styling_config: Styling configuration for the table
            interactive: Whether to show interactive features
            download_filename: If provided, adds download button
        """
        if data is None or data.empty:
            st.warning("No table data provided")
            return
            
        # Apply styling if configured
        if styling_config:
            styled_df = data.style
            
            # Apply formatting
            if 'format' in styling_config:
                for col, fmt in styling_config['format'].items():
                    if col in data.columns:
                        styled_df = styled_df.format({col: fmt})
            
            # Apply conditional formatting
            if 'highlight' in styling_config:
                for rule in styling_config['highlight']:
                    if rule['type'] == 'positive_negative':
                        styled_df = styled_df.applymap(
                            lambda x: 'color: green' if x > 0 else 'color: red' if x < 0 else '',
                            subset=rule.get('columns', [])
                        )
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(data, use_container_width=True)
        
        # Add download option
        if download_filename:
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=download_filename,
                mime="text/csv"
            )


class FormBuilder(UIComponent):
    """Component for building interactive forms"""
    
    def render(self, form_config: Dict[str, Any],
               submit_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Render interactive form based on configuration
        
        Args:
            form_config: Form field configurations
            submit_callback: Optional callback function for form submission
            
        Returns:
            Dictionary of form field values
        """
        form_data = {}
        
        with st.form(self.component_id):
            st.subheader(form_config.get('title', 'Form'))
            
            if 'description' in form_config:
                st.write(form_config['description'])
            
            # Render form fields
            for field_name, field_config in form_config.get('fields', {}).items():
                field_type = field_config.get('type', 'text')
                label = field_config.get('label', field_name.title())
                default_value = field_config.get('default')
                
                if field_type == 'text':
                    form_data[field_name] = st.text_input(label, value=default_value or "")
                elif field_type == 'number':
                    form_data[field_name] = st.number_input(
                        label, 
                        value=default_value or 0.0,
                        min_value=field_config.get('min'),
                        max_value=field_config.get('max'),
                        step=field_config.get('step', 0.01)
                    )
                elif field_type == 'selectbox':
                    options = field_config.get('options', [])
                    form_data[field_name] = st.selectbox(label, options, index=0)
                elif field_type == 'multiselect':
                    options = field_config.get('options', [])
                    form_data[field_name] = st.multiselect(label, options)
                elif field_type == 'checkbox':
                    form_data[field_name] = st.checkbox(label, value=default_value or False)
                elif field_type == 'date':
                    form_data[field_name] = st.date_input(label)
                elif field_type == 'file':
                    form_data[field_name] = st.file_uploader(
                        label,
                        type=field_config.get('allowed_types')
                    )
            
            # Submit button
            submitted = st.form_submit_button(form_config.get('submit_label', 'Submit'))
            
            if submitted:
                if submit_callback:
                    submit_callback(form_data)
                self.set_state(form_data)
        
        return form_data if submitted else {}