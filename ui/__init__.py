"""
UI Package - Presentation Layer Components
==========================================

Modular UI components for financial analysis application.
Separates presentation logic from business logic.
"""

# Export main UI components
from .components import (
    UIComponent,
    MetricsDisplay,
    ChartRenderer,
    TableFormatter,
    FormBuilder
)

from .layouts import (
    SidebarLayout,
    MainContentLayout,
    TabsLayout
)

from .widgets import (
    FinancialInputWidget,
    ExportWidget,
    SettingsWidget
)

__all__ = [
    'UIComponent',
    'MetricsDisplay', 
    'ChartRenderer',
    'TableFormatter',
    'FormBuilder',
    'SidebarLayout',
    'MainContentLayout', 
    'TabsLayout',
    'FinancialInputWidget',
    'ExportWidget',
    'SettingsWidget'
]