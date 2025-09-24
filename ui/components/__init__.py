"""
Advanced UI Components Framework
===============================

Comprehensive collection of sophisticated UI components for financial analysis
dashboards with real-time collaboration, advanced visualizations, and
intelligent orchestration capabilities.

Components:
- Advanced Framework: Base classes and infrastructure
- Interactive Widgets: Financial input panels, scenario analyzers, data monitors
- Dashboard Orchestrator: Multi-component layout and state management
- Portfolio Comparison: Advanced portfolio analysis and comparison tools
- Collaboration Features: Real-time sharing, annotations, and team collaboration
- Data Quality Dashboard: Data validation and quality monitoring
- Responsive Framework: Mobile-first responsive design components
"""

# Core framework components
from .advanced_framework import (
    AdvancedComponent,
    ComponentConfig,
    ComponentState,
    InteractionEvent,
    ComponentMetrics,
    InteractiveChart,
    SmartDataTable,
    create_advanced_component,
    performance_monitor
)

# Interactive widgets
from .interactive_widgets import (
    FinancialInputPanel,
    InteractiveScenarioAnalyzer,
    RealTimeDataMonitor,
    WidgetTheme,
    create_financial_input_panel,
    create_scenario_analyzer,
    create_data_monitor
)

# Dashboard orchestration
from .dashboard_orchestrator import (
    DashboardOrchestrator,
    LayoutType,
    ComponentPosition,
    ComponentRegistration,
    DashboardLayout,
    DashboardTheme,
    create_dashboard_orchestrator,
    create_standard_financial_dashboard
)

# Portfolio comparison
from .portfolio_comparison_widget import (
    PortfolioComparisonWidget,
    PortfolioAsset,
    ComparisonResult,
    ComparisonMetric,
    ComparisonPeriod,
    create_portfolio_comparison_widget
)

# Collaboration features
from .collaboration_features import (
    CollaborationManager,
    CollaborationUser,
    Annotation,
    Comment,
    SharedAnalysis,
    SessionRole,
    ActivityType,
    create_collaboration_manager
)

# Data quality dashboard (existing)
from .data_quality_dashboard import (
    DataQualityDashboard,
    QualityMetric,
    create_data_quality_dashboard
)

# Responsive framework (existing)
from .responsive_framework import (
    ResponsiveComponent,
    BreakPoint,
    ResponsiveConfig,
    create_responsive_component
)

# Navigation components (temporarily disabled due to missing implementation)
# from .responsive_navigation import (
#     NavigationComponent,
#     create_navigation_component
# )

# Accessibility features (temporarily disabled due to missing implementation)
# from .accessibility_features import (
#     AccessibilityComponent,
#     create_accessibility_component
# )

__all__ = [
    # Core framework
    'AdvancedComponent',
    'ComponentConfig',
    'ComponentState',
    'InteractionEvent',
    'ComponentMetrics',
    'InteractiveChart',
    'SmartDataTable',
    'create_advanced_component',
    'performance_monitor',

    # Interactive widgets
    'FinancialInputPanel',
    'InteractiveScenarioAnalyzer',
    'RealTimeDataMonitor',
    'WidgetTheme',
    'create_financial_input_panel',
    'create_scenario_analyzer',
    'create_data_monitor',

    # Dashboard orchestration
    'DashboardOrchestrator',
    'LayoutType',
    'ComponentPosition',
    'ComponentRegistration',
    'DashboardLayout',
    'DashboardTheme',
    'create_dashboard_orchestrator',
    'create_standard_financial_dashboard',

    # Portfolio comparison
    'PortfolioComparisonWidget',
    'PortfolioAsset',
    'ComparisonResult',
    'ComparisonMetric',
    'ComparisonPeriod',
    'create_portfolio_comparison_widget',

    # Collaboration features
    'CollaborationManager',
    'CollaborationUser',
    'Annotation',
    'Comment',
    'SharedAnalysis',
    'SessionRole',
    'ActivityType',
    'create_collaboration_manager',

    # Existing components
    'DataQualityDashboard',
    'QualityMetric',
    'create_data_quality_dashboard',
    'ResponsiveComponent',
    'BreakPoint',
    'ResponsiveConfig',
    'create_responsive_component',
    'NavigationComponent',
    'create_navigation_component',
    'AccessibilityComponent',
    'create_accessibility_component'
]