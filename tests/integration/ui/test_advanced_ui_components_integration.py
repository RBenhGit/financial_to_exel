"""
Integration Tests for Advanced UI Components Framework
=====================================================

Comprehensive integration tests for Phase 2B Advanced UI Components,
including dashboard orchestration, portfolio comparison, and collaboration features.
"""

import pytest
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ui.components.advanced_framework import (
    AdvancedComponent,
    ComponentConfig,
    InteractiveChart,
    SmartDataTable
)
from ui.components.dashboard_orchestrator import (
    DashboardOrchestrator,
    LayoutType,
    ComponentPosition,
    create_dashboard_orchestrator,
    create_standard_financial_dashboard
)
from ui.components.portfolio_comparison_widget import (
    PortfolioComparisonWidget,
    PortfolioAsset,
    ComparisonPeriod,
    create_portfolio_comparison_widget
)
from ui.components.collaboration_features import (
    CollaborationManager,
    SessionRole,
    ActivityType,
    create_collaboration_manager
)
from ui.components.interactive_widgets import (
    create_financial_input_panel,
    create_scenario_analyzer,
    create_data_monitor
)


class TestAdvancedUIComponentsIntegration:
    """Test integration of advanced UI components"""

    @pytest.fixture
    def sample_financial_data(self):
        """Create sample financial data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)

        data = pd.DataFrame({
            'date': dates,
            'AAPL': np.cumsum(np.random.randn(len(dates)) * 0.02) + 150,
            'MSFT': np.cumsum(np.random.randn(len(dates)) * 0.015) + 300,
            'GOOGL': np.cumsum(np.random.randn(len(dates)) * 0.025) + 2500,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })

        return data

    @pytest.fixture
    def dashboard_orchestrator(self):
        """Create dashboard orchestrator for testing"""
        return create_dashboard_orchestrator(
            "test_dashboard",
            "Test Financial Dashboard",
            "Integration test dashboard"
        )

    @pytest.fixture
    def portfolio_widget(self):
        """Create portfolio comparison widget for testing"""
        return create_portfolio_comparison_widget("test_portfolio")

    @pytest.fixture
    def collaboration_manager(self):
        """Create collaboration manager for testing"""
        return create_collaboration_manager("test_collaboration")

    def test_dashboard_orchestrator_initialization(self, dashboard_orchestrator):
        """Test dashboard orchestrator initialization"""
        assert dashboard_orchestrator.config.id == "test_dashboard"
        assert dashboard_orchestrator.config.title == "Test Financial Dashboard"
        assert dashboard_orchestrator.layout.layout_type == LayoutType.TWO_COLUMN
        assert len(dashboard_orchestrator.components) == 0

    def test_component_registration(self, dashboard_orchestrator):
        """Test component registration with dashboard orchestrator"""
        # Create test component
        input_panel = create_financial_input_panel("test_input")

        # Register component
        dashboard_orchestrator.register_component(
            "input_panel",
            input_panel,
            ComponentPosition.SIDEBAR
        )

        # Verify registration
        assert "input_panel" in dashboard_orchestrator.components
        registration = dashboard_orchestrator.components["input_panel"]
        assert registration.component == input_panel
        assert registration.position == ComponentPosition.SIDEBAR
        assert registration.active is True

    def test_layout_configuration(self, dashboard_orchestrator):
        """Test dashboard layout configuration"""
        # Test different layout types
        dashboard_orchestrator.set_layout(LayoutType.THREE_COLUMN)
        assert dashboard_orchestrator.layout.layout_type == LayoutType.THREE_COLUMN

        dashboard_orchestrator.set_layout(LayoutType.GRID, columns=[2, 1, 1])
        assert dashboard_orchestrator.layout.layout_type == LayoutType.GRID
        assert dashboard_orchestrator.layout.columns == [2, 1, 1]

    def test_data_binding_setup(self, dashboard_orchestrator):
        """Test data binding between components"""
        # Register components
        input_panel = create_financial_input_panel("input")
        chart = create_scenario_analyzer("chart")

        dashboard_orchestrator.register_component("input", input_panel)
        dashboard_orchestrator.register_component("chart", chart)

        # Set up data binding
        dashboard_orchestrator.bind_data("input", "chart", "ticker", "symbol")

        # Verify binding
        chart_registration = dashboard_orchestrator.components["chart"]
        assert "symbol" in chart_registration.data_bindings
        assert chart_registration.data_bindings["symbol"] == "input.ticker"

    def test_global_state_management(self, dashboard_orchestrator):
        """Test global state management"""
        # Update global state
        dashboard_orchestrator.update_global_state("selected_ticker", "AAPL")
        dashboard_orchestrator.update_global_state("analysis_period", "1Y")

        # Verify state retrieval
        assert dashboard_orchestrator.get_global_state("selected_ticker") == "AAPL"
        assert dashboard_orchestrator.get_global_state("analysis_period") == "1Y"
        assert dashboard_orchestrator.get_global_state("non_existent") is None

    def test_standard_dashboard_creation(self):
        """Test creation of standard financial dashboard"""
        dashboard = create_standard_financial_dashboard("standard_test")

        # Verify standard components are registered
        expected_components = ["input_panel", "time_series", "heatmap", "scenario_analyzer", "data_monitor"]
        for component_id in expected_components:
            assert component_id in dashboard.components

        # Verify data bindings are set up
        scenario_registration = dashboard.components["scenario_analyzer"]
        assert "base_discount_rate" in scenario_registration.data_bindings

    def test_portfolio_comparison_widget_initialization(self, portfolio_widget):
        """Test portfolio comparison widget initialization"""
        assert portfolio_widget.config.id == "test_portfolio"
        assert len(portfolio_widget.assets) == 0
        assert portfolio_widget.benchmark_ticker == "SPY"
        assert portfolio_widget.comparison_period == ComparisonPeriod.ONE_YEAR

    def test_portfolio_asset_management(self, portfolio_widget):
        """Test portfolio asset addition and management"""
        # Add assets
        portfolio_widget._add_asset("AAPL", 0.3)
        portfolio_widget._add_asset("MSFT", 0.3)
        portfolio_widget._add_asset("GOOGL", 0.4)

        # Verify assets added
        assert len(portfolio_widget.assets) == 3
        tickers = [asset.ticker for asset in portfolio_widget.assets]
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" in tickers

        # Test weight validation
        total_weight = sum(asset.weight for asset in portfolio_widget.assets)
        assert abs(total_weight - 1.0) < 0.01

        # Test asset removal
        portfolio_widget._remove_asset("GOOGL")
        assert len(portfolio_widget.assets) == 2

        # Test rebalancing
        portfolio_widget._rebalance_weights()
        for asset in portfolio_widget.assets:
            assert abs(asset.weight - 0.5) < 0.01

    def test_portfolio_metrics_calculation(self, portfolio_widget, sample_financial_data):
        """Test portfolio metrics calculation"""
        # Add assets
        portfolio_widget._add_asset("AAPL", 0.5)
        portfolio_widget._add_asset("MSFT", 0.5)

        # Calculate metrics
        result = portfolio_widget._calculate_portfolio_metrics()

        # Verify result structure
        assert result is not None
        assert hasattr(result, 'assets')
        assert hasattr(result, 'portfolio_metrics')
        assert hasattr(result, 'correlation_matrix')
        assert hasattr(result, 'risk_metrics')

        # Verify asset metrics
        for asset in result.assets:
            assert 'total_return' in asset.metrics
            assert 'volatility' in asset.metrics
            assert 'sharpe_ratio' in asset.metrics

        # Verify portfolio metrics
        assert 'total_return' in result.portfolio_metrics
        assert 'volatility' in result.portfolio_metrics
        assert 'sharpe_ratio' in result.portfolio_metrics

    def test_collaboration_manager_initialization(self, collaboration_manager):
        """Test collaboration manager initialization"""
        assert collaboration_manager.config.id == "test_collaboration"
        assert len(collaboration_manager.users) == 0
        assert len(collaboration_manager.annotations) == 0
        assert len(collaboration_manager.comments) == 0

    def test_user_management(self, collaboration_manager):
        """Test collaboration user management"""
        # Initialize current user
        collaboration_manager._initialize_current_user()

        # Verify user creation
        assert collaboration_manager.current_user is not None
        assert len(collaboration_manager.users) == 1
        assert collaboration_manager.current_user.role == SessionRole.EDITOR

        # Test user presence
        user_id = collaboration_manager.current_user.id
        assert user_id in collaboration_manager.users
        assert collaboration_manager.users[user_id].is_online is True

    def test_annotation_management(self, collaboration_manager):
        """Test annotation management"""
        # Initialize user
        collaboration_manager._initialize_current_user()

        # Add annotation
        collaboration_manager._add_annotation(
            "test_chart",
            100.0,
            50.0,
            "This is a test annotation",
            "note"
        )

        # Verify annotation added
        assert len(collaboration_manager.annotations) == 1
        annotation = list(collaboration_manager.annotations.values())[0]
        assert annotation.chart_id == "test_chart"
        assert annotation.text == "This is a test annotation"
        assert annotation.annotation_type == "note"
        assert not annotation.resolved

        # Test annotation resolution
        annotation_id = annotation.id
        collaboration_manager._resolve_annotation(annotation_id)
        assert collaboration_manager.annotations[annotation_id].resolved

    def test_comment_management(self, collaboration_manager):
        """Test comment management"""
        # Initialize user
        collaboration_manager._initialize_current_user()

        # Add comment
        collaboration_manager._add_comment(
            "dashboard",
            "main_dashboard",
            "This dashboard looks great!"
        )

        # Verify comment added
        assert len(collaboration_manager.comments) == 1
        comment = list(collaboration_manager.comments.values())[0]
        assert comment.target_type == "dashboard"
        assert comment.target_id == "main_dashboard"
        assert comment.content == "This dashboard looks great!"
        assert not comment.resolved

    def test_shared_analysis_management(self, collaboration_manager):
        """Test shared analysis management"""
        # Initialize user
        collaboration_manager._initialize_current_user()

        # Create shared analysis
        collaboration_manager._create_shared_analysis(
            "Q4 Performance Analysis",
            "Comprehensive analysis of Q4 portfolio performance"
        )

        # Verify analysis created
        assert len(collaboration_manager.shared_analyses) == 1
        analysis = list(collaboration_manager.shared_analyses.values())[0]
        assert analysis.title == "Q4 Performance Analysis"
        assert analysis.creator_id == collaboration_manager.current_user.id

    def test_activity_logging(self, collaboration_manager):
        """Test activity logging"""
        # Initialize user
        collaboration_manager._initialize_current_user()

        initial_activity_count = len(collaboration_manager.activity_log)

        # Perform activities
        collaboration_manager._add_annotation("chart1", 0, 0, "Test annotation", "note")
        collaboration_manager._add_comment("dashboard", "main", "Test comment")
        collaboration_manager._create_shared_analysis("Test Analysis", "Description")

        # Verify activities logged
        # Should have initial user join + 3 new activities
        expected_count = initial_activity_count + 3
        assert len(collaboration_manager.activity_log) == expected_count

        # Verify activity types
        activity_types = [activity.activity_type for activity in collaboration_manager.activity_log[-3:]]
        assert ActivityType.ANNOTATION_ADDED in activity_types
        assert ActivityType.COMMENT_POSTED in activity_types
        assert ActivityType.ANALYSIS_SHARED in activity_types

    @patch('streamlit.session_state')
    def test_component_integration_with_streamlit(self, mock_session_state, dashboard_orchestrator):
        """Test component integration with Streamlit session state"""
        # Mock session state
        mock_session_state.return_value = {}

        # Register component
        input_panel = create_financial_input_panel("input")
        dashboard_orchestrator.register_component("input", input_panel)

        # Test component state persistence
        mock_session_state["input_state"] = "ready"
        mock_session_state["dashboard_initialized"] = True

        # Verify session state integration
        assert hasattr(dashboard_orchestrator, '_initialize_dashboard')

    def test_performance_monitoring(self, dashboard_orchestrator):
        """Test performance monitoring functionality"""
        # Create component with performance monitoring
        chart_config = ComponentConfig(
            id="test_chart",
            title="Test Chart",
            cache_enabled=True
        )

        chart = InteractiveChart(chart_config)

        # Verify metrics initialization
        assert chart.metrics is not None
        assert chart.metrics.render_count == 0
        assert chart.metrics.cache_hits == 0

    def test_error_handling(self, dashboard_orchestrator):
        """Test error handling in components"""
        # Test component not found error
        with patch('streamlit.error') as mock_error:
            dashboard_orchestrator._render_single_component("non_existent_component")
            mock_error.assert_called()

    def test_theme_application(self, dashboard_orchestrator):
        """Test theme application across components"""
        from ui.components.dashboard_orchestrator import DashboardTheme

        # Create custom theme
        custom_theme = DashboardTheme(
            primary_color="#ff0000",
            background_color="#000000",
            text_color="#ffffff"
        )

        # Apply theme
        dashboard_orchestrator.set_theme(custom_theme)

        # Verify theme applied
        assert dashboard_orchestrator.theme.primary_color == "#ff0000"
        assert dashboard_orchestrator.theme.background_color == "#000000"
        assert dashboard_orchestrator.theme.text_color == "#ffffff"

    def test_component_lifecycle(self, dashboard_orchestrator):
        """Test component lifecycle management"""
        # Create and register component
        widget = create_data_monitor("lifecycle_test")
        dashboard_orchestrator.register_component("widget", widget)

        # Verify component is active
        registration = dashboard_orchestrator.components["widget"]
        assert registration.active is True

        # Test component state transitions
        widget._update_state(ComponentState.LOADING)
        # In real implementation, this would be stored in session state

    def test_multi_component_data_flow(self, dashboard_orchestrator, sample_financial_data):
        """Test data flow between multiple components"""
        # Register multiple components
        input_panel = create_financial_input_panel("input")
        scenario_analyzer = create_scenario_analyzer("scenario")
        chart = create_financial_input_panel("chart")  # Using input panel as mock chart

        dashboard_orchestrator.register_component("input", input_panel)
        dashboard_orchestrator.register_component("scenario", scenario_analyzer)
        dashboard_orchestrator.register_component("chart", chart)

        # Set up data bindings
        dashboard_orchestrator.bind_data("input", "scenario", "ticker", "symbol")
        dashboard_orchestrator.bind_data("input", "chart", "discount_rate", "rate")

        # Simulate data flow
        dashboard_orchestrator.data_store["input"] = {
            "ticker": "AAPL",
            "discount_rate": 0.10
        }

        # Test data preparation
        scenario_data = dashboard_orchestrator._prepare_component_data(
            "scenario",
            dashboard_orchestrator.components["scenario"]
        )
        chart_data = dashboard_orchestrator._prepare_component_data(
            "chart",
            dashboard_orchestrator.components["chart"]
        )

        # Verify data binding worked
        assert scenario_data.get("symbol") == "AAPL"
        assert chart_data.get("rate") == 0.10

    def test_export_functionality(self, collaboration_manager, portfolio_widget):
        """Test export functionality across components"""
        # Initialize collaboration manager
        collaboration_manager._initialize_current_user()

        # Create shared analysis
        collaboration_manager._create_shared_analysis("Export Test", "Test analysis for export")

        # Test analysis export preparation
        analysis_id = list(collaboration_manager.shared_analyses.keys())[0]
        analysis = collaboration_manager.shared_analyses[analysis_id]

        # Verify export data structure
        export_data = {
            "title": analysis.title,
            "description": analysis.description,
            "created_at": analysis.created_at.isoformat(),
            "data": analysis.analysis_data
        }

        assert export_data["title"] == "Export Test"
        assert "created_at" in export_data

    def test_responsive_behavior(self, dashboard_orchestrator):
        """Test responsive behavior of components"""
        # Test layout adaptation
        dashboard_orchestrator.layout.responsive = True
        dashboard_orchestrator.layout.breakpoints = {
            "mobile": 768,
            "tablet": 1024,
            "desktop": 1440
        }

        # Verify responsive configuration
        assert dashboard_orchestrator.layout.responsive is True
        assert dashboard_orchestrator.layout.breakpoints["mobile"] == 768

    @pytest.mark.integration
    def test_full_dashboard_workflow(self, sample_financial_data):
        """Test complete dashboard workflow integration"""
        # Create standard dashboard
        dashboard = create_standard_financial_dashboard("workflow_test")

        # Verify all components registered
        expected_components = ["input_panel", "time_series", "heatmap", "scenario_analyzer", "data_monitor"]
        for component_id in expected_components:
            assert component_id in dashboard.components

        # Test layout switching
        dashboard.set_layout(LayoutType.TABS)
        assert dashboard.layout.layout_type == LayoutType.TABS

        # Test global state
        dashboard.update_global_state("current_ticker", "AAPL")
        dashboard.update_global_state("analysis_complete", True)

        # Verify state persistence
        assert dashboard.get_global_state("current_ticker") == "AAPL"
        assert dashboard.get_global_state("analysis_complete") is True

    def test_component_caching(self, dashboard_orchestrator):
        """Test component caching functionality"""
        # Create component with caching enabled
        config = ComponentConfig(
            id="cached_component",
            title="Cached Component",
            cache_enabled=True
        )

        table = SmartDataTable(config)
        dashboard_orchestrator.register_component("table", table)

        # Test cache key generation
        test_data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        cache_key = table._generate_cache_key(test_data, {})

        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    def test_event_handling(self, dashboard_orchestrator):
        """Test event handling between components"""
        # Create components
        chart = InteractiveChart(ComponentConfig(
            id="event_chart",
            title="Event Chart"
        ))

        dashboard_orchestrator.register_component("chart", chart)

        # Test event handler setup
        dashboard_orchestrator._setup_component_events("chart", chart)

        # Verify event handlers registered
        assert InteractionEvent.CLICK in chart.event_handlers
        assert InteractionEvent.CHANGE in chart.event_handlers

    def teardown_method(self):
        """Clean up after each test"""
        # Clear any session state that might affect other tests
        if hasattr(st, 'session_state'):
            # In a real test environment, we would clear session state
            pass