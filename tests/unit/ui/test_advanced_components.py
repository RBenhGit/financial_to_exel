"""
Unit Tests for Advanced UI Components Framework
==============================================

Test suite for the advanced component framework including base classes,
interactive widgets, and visualization components.
"""

import pytest
import unittest.mock as mock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Import components to test
from ui.components.advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState, ComponentMetrics,
    InteractionEvent, InteractiveChart, SmartDataTable, performance_monitor
)
from ui.components.interactive_widgets import (
    FinancialInputPanel, InteractiveScenarioAnalyzer, RealTimeDataMonitor,
    create_financial_input_panel, create_scenario_analyzer, create_data_monitor
)


class TestComponentConfig:
    """Test ComponentConfig class"""

    def test_component_config_creation(self):
        """Test creating component configuration"""
        config = ComponentConfig(
            id="test_component",
            title="Test Component",
            description="Test description",
            cache_enabled=True,
            auto_refresh=False
        )

        assert config.id == "test_component"
        assert config.title == "Test Component"
        assert config.description == "Test description"
        assert config.cache_enabled is True
        assert config.auto_refresh is False
        assert config.refresh_interval == 30  # default value

    def test_component_config_defaults(self):
        """Test default values in component configuration"""
        config = ComponentConfig(
            id="minimal_component",
            title="Minimal Component"
        )

        assert config.description == ""
        assert config.cache_enabled is True
        assert config.auto_refresh is False
        assert config.animation_enabled is True
        assert config.responsive is True
        assert config.theme == "default"
        assert config.permissions == []


class TestComponentMetrics:
    """Test ComponentMetrics class"""

    def test_component_metrics_creation(self):
        """Test creating component metrics"""
        metrics = ComponentMetrics()

        assert metrics.render_time == 0.0
        assert metrics.render_count == 0
        assert metrics.error_count == 0
        assert metrics.user_interactions == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert isinstance(metrics.last_render, datetime)

    def test_metrics_update(self):
        """Test updating metrics"""
        metrics = ComponentMetrics()

        # Update metrics
        metrics.render_time = 0.5
        metrics.render_count = 1
        metrics.cache_hits = 5
        metrics.cache_misses = 2

        assert metrics.render_time == 0.5
        assert metrics.render_count == 1
        assert metrics.cache_hits == 5
        assert metrics.cache_misses == 2


class MockAdvancedComponent(AdvancedComponent):
    """Mock component for testing base functionality"""

    def render_content(self, data=None, **kwargs):
        """Mock render implementation"""
        if data is None:
            return "No data provided"

        if isinstance(data, dict) and data.get("error"):
            raise ValueError("Test error")

        return f"Rendered with data: {data}"


class TestAdvancedComponent:
    """Test AdvancedComponent base class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = ComponentConfig(
            id="test_component",
            title="Test Component",
            cache_enabled=True
        )
        self.component = MockAdvancedComponent(self.config)

    def test_component_initialization(self):
        """Test component initialization"""
        assert self.component.config == self.config
        assert self.component.state == ComponentState.INITIALIZING
        assert isinstance(self.component.metrics, ComponentMetrics)
        assert self.component.event_handlers == {}
        assert self.component._cached_data == {}

    def test_component_render_success(self):
        """Test successful component rendering"""
        test_data = {"value": 100}

        with mock.patch('streamlit.session_state', {}):
            result = self.component.render(test_data)

        assert "Rendered with data:" in result
        assert self.component.metrics.render_count == 1
        assert self.component.metrics.render_time > 0

    def test_component_render_with_cache(self):
        """Test component rendering with caching"""
        test_data = {"value": 100}

        with mock.patch('streamlit.session_state', {}):
            # First render
            result1 = self.component.render(test_data)
            initial_cache_misses = self.component.metrics.cache_misses

            # Second render (should hit cache)
            result2 = self.component.render(test_data)

        assert result1 == result2
        assert self.component.metrics.cache_hits >= 1
        assert self.component.metrics.cache_misses == initial_cache_misses

    def test_component_render_error(self):
        """Test component error handling"""
        error_data = {"error": True}

        with mock.patch('streamlit.session_state', {}):
            with mock.patch('streamlit.error'):
                result = self.component.render(error_data)

        assert result is None  # Error fallback
        assert self.component.metrics.error_count == 1
        assert self.component.state == ComponentState.ERROR

    def test_event_handler_registration(self):
        """Test event handler registration and triggering"""
        handler_called = False
        handler_data = None

        def test_handler(event, data):
            nonlocal handler_called, handler_data
            handler_called = True
            handler_data = data
            return "handler_result"

        # Register handler
        self.component.add_event_handler(InteractionEvent.CLICK, test_handler)

        # Trigger event
        results = self.component.trigger_event(InteractionEvent.CLICK, "test_data")

        assert handler_called
        assert handler_data == "test_data"
        assert results == ["handler_result"]
        assert self.component.metrics.user_interactions == 1

    def test_cache_management(self):
        """Test cache clearing"""
        test_data = {"value": 100}

        with mock.patch('streamlit.session_state', {}):
            # Render to populate cache
            self.component.render(test_data)
            assert len(self.component._cached_data) > 0

            # Clear cache
            self.component.clear_cache()
            assert len(self.component._cached_data) == 0

    def test_cache_key_generation(self):
        """Test cache key generation"""
        data1 = {"value": 100}
        data2 = {"value": 200}
        kwargs1 = {"param": "a"}
        kwargs2 = {"param": "b"}

        key1 = self.component._generate_cache_key(data1, kwargs1)
        key2 = self.component._generate_cache_key(data1, kwargs1)  # Same data
        key3 = self.component._generate_cache_key(data2, kwargs1)  # Different data
        key4 = self.component._generate_cache_key(data1, kwargs2)  # Different kwargs

        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different data should generate different key
        assert key1 != key4  # Different kwargs should generate different key


class TestInteractiveChart:
    """Test InteractiveChart component"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = ComponentConfig(
            id="test_chart",
            title="Test Chart"
        )
        self.chart = InteractiveChart(self.config)

        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'date': dates,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 5000000, 100)
        })

    def test_chart_initialization(self):
        """Test chart component initialization"""
        assert self.chart.config.id == "test_chart"
        assert "responsive" in self.chart.chart_config
        assert self.chart.chart_config["responsive"] is True

    @mock.patch('streamlit.plotly_chart')
    @mock.patch('streamlit.session_state', {})
    def test_chart_render_line_chart(self, mock_plotly_chart):
        """Test rendering line chart"""
        chart_data = {
            "type": "line",
            "data": self.sample_data,
            "x": "date",
            "y": "close"
        }

        with mock.patch('streamlit.expander'):
            result = self.chart.render_content(chart_data)

        assert result is not None
        mock_plotly_chart.assert_called_once()

    @mock.patch('streamlit.plotly_chart')
    @mock.patch('streamlit.session_state', {})
    def test_chart_render_multi_line(self, mock_plotly_chart):
        """Test rendering multi-line chart"""
        chart_data = {
            "type": "multi_line",
            "data": self.sample_data,
            "x": "date",
            "y_cols": ["close", "volume"]
        }

        with mock.patch('streamlit.expander'):
            result = self.chart.render_content(chart_data)

        assert result is not None
        mock_plotly_chart.assert_called_once()

    @mock.patch('streamlit.warning')
    def test_chart_render_no_data(self, mock_warning):
        """Test chart rendering with no data"""
        chart_data = {
            "type": "line",
            "data": None
        }

        result = self.chart.render_content(chart_data)

        assert result is None
        mock_warning.assert_called_once()

    def test_chart_moving_averages(self):
        """Test moving average calculation"""
        # This would test the _add_trend_analysis method
        # Implementation depends on the actual method structure
        pass


class TestSmartDataTable:
    """Test SmartDataTable component"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = ComponentConfig(
            id="test_table",
            title="Test Table"
        )
        self.table = SmartDataTable(self.config)

        # Create sample data
        self.sample_data = pd.DataFrame({
            'company': ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
            'price': [150.0, 300.0, 2500.0, 3200.0],
            'volume': [1000000, 800000, 500000, 600000],
            'change': [2.5, -1.2, 0.8, 1.5]
        })

    @mock.patch('streamlit.dataframe')
    @mock.patch('streamlit.session_state', {})
    def test_table_render_basic(self, mock_dataframe):
        """Test basic table rendering"""
        with mock.patch('streamlit.expander'):
            self.table.render_content(self.sample_data)

        mock_dataframe.assert_called_once()

    def test_table_filter_application(self):
        """Test applying filters to data"""
        config = {
            "filters": {
                "company": {"type": "text", "value": "AAPL"}
            }
        }

        filtered_data = self.table._apply_filters(self.sample_data, config)

        assert len(filtered_data) == 1
        assert filtered_data.iloc[0]['company'] == 'AAPL'

    def test_table_sorting(self):
        """Test data sorting"""
        config = {
            "sort": {"column": "price", "ascending": False}
        }

        sorted_data = self.table._apply_sorting(self.sample_data, config)

        assert sorted_data.iloc[0]['company'] == 'AMZN'  # Highest price
        assert sorted_data.iloc[-1]['company'] == 'AAPL'  # Lowest price

    def test_table_pagination(self):
        """Test data pagination"""
        config = {
            "pagination": {
                "enabled": True,
                "page_size": 2,
                "current_page": 1
            }
        }

        paginated_data = self.table._apply_pagination(self.sample_data, config)

        assert len(paginated_data) == 2
        assert paginated_data.iloc[0]['company'] == 'AAPL'


class TestFinancialInputPanel:
    """Test FinancialInputPanel widget"""

    def setup_method(self):
        """Setup test fixtures"""
        self.panel = create_financial_input_panel("test_inputs")

    def test_panel_creation(self):
        """Test panel creation through factory function"""
        assert self.panel.config.id == "test_inputs"
        assert "Financial Analysis Input" in self.panel.config.title

    def test_ticker_suggestions(self):
        """Test ticker suggestion functionality"""
        suggestions = self.panel._get_ticker_suggestions("AA")

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(ticker.startswith("AA") for ticker in suggestions)

    def test_company_name_lookup(self):
        """Test company name lookup"""
        company_name = self.panel._get_company_name("AAPL")

        assert company_name == "Apple Inc."

    def test_input_validation(self):
        """Test input validation"""
        # Valid inputs
        valid_inputs = {
            "ticker": "AAPL",
            "discount_rate": 0.10,
            "terminal_growth": 0.025
        }

        validation_result = self.panel._validate_inputs(valid_inputs)
        assert validation_result["is_valid"] is True
        assert len(validation_result["issues"]) == 0

        # Invalid inputs
        invalid_inputs = {
            "ticker": "",
            "discount_rate": -0.05,
            "terminal_growth": -0.01
        }

        validation_result = self.panel._validate_inputs(invalid_inputs)
        assert validation_result["is_valid"] is False
        assert len(validation_result["issues"]) > 0


class TestInteractiveScenarioAnalyzer:
    """Test InteractiveScenarioAnalyzer widget"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = create_scenario_analyzer("test_scenarios")

        self.base_parameters = {
            "revenue_growth": 0.05,
            "operating_margin": 0.15,
            "discount_rate": 0.10,
            "terminal_growth": 0.025,
            "tax_rate": 0.21,
            "beta": 1.0,
            "debt_ratio": 0.3,
            "capex_rate": 0.05
        }

    def test_analyzer_creation(self):
        """Test analyzer creation"""
        assert self.analyzer.config.id == "test_scenarios"
        assert len(self.analyzer.scenarios) >= 3  # base, optimistic, pessimistic

    def test_scenario_valuation_calculation(self):
        """Test scenario valuation calculations"""
        scenario_params = {
            "growth": {"adjusted_revenue_growth": 0.06},
            "margins": {"adjusted_operating_margin": 0.16},
            "risk": {"adjusted_discount_rate": 0.11},
            "structure": {"adjusted_debt_ratio": 0.25}
        }

        results = self.analyzer._calculate_scenario_valuations(scenario_params)

        assert isinstance(results, dict)
        assert len(results) > 0

        # Check that each scenario has required fields
        for scenario_name, scenario_data in results.items():
            assert "Fair Value" in scenario_data
            assert "Current Price" in scenario_data
            assert "Upside/Downside" in scenario_data

    def test_sensitivity_data_generation(self):
        """Test sensitivity analysis data generation"""
        sensitivity_data = self.analyzer._generate_sensitivity_data(self.base_parameters)

        assert "variables" in sensitivity_data
        assert "impacts" in sensitivity_data
        assert len(sensitivity_data["variables"]) == len(sensitivity_data["impacts"])
        assert all(isinstance(impact, (int, float)) for impact in sensitivity_data["impacts"])


class TestRealTimeDataMonitor:
    """Test RealTimeDataMonitor widget"""

    def setup_method(self):
        """Setup test fixtures"""
        self.monitor = create_data_monitor("test_monitor")

    def test_monitor_creation(self):
        """Test monitor creation"""
        assert self.monitor.config.id == "test_monitor"
        assert self.monitor.refresh_interval == 10

    def test_alert_checking(self):
        """Test alert checking functionality"""
        alerts = self.monitor._check_alerts()

        assert isinstance(alerts, list)
        # Alerts may or may not be present depending on random conditions
        for alert in alerts:
            assert "type" in alert
            assert "message" in alert
            assert alert["type"] in ["warning", "error", "info"]


class TestPerformanceMonitor:
    """Test performance monitoring decorator"""

    def test_performance_monitor_decorator(self):
        """Test performance monitoring decorator"""
        @performance_monitor
        def mock_render_method(self):
            # Simulate some work
            import time
            time.sleep(0.01)
            return "result"

        # Create mock component with metrics
        mock_component = mock.MagicMock()
        mock_component.metrics = ComponentMetrics()

        # Call decorated method
        result = mock_render_method(mock_component)

        assert result == "result"
        assert mock_component.metrics.render_time > 0


class TestFactoryFunctions:
    """Test factory functions for component creation"""

    def test_create_financial_input_panel(self):
        """Test financial input panel factory"""
        panel = create_financial_input_panel("factory_test")

        assert isinstance(panel, FinancialInputPanel)
        assert panel.config.id == "factory_test"

    def test_create_scenario_analyzer(self):
        """Test scenario analyzer factory"""
        analyzer = create_scenario_analyzer("factory_test")

        assert isinstance(analyzer, InteractiveScenarioAnalyzer)
        assert analyzer.config.id == "factory_test"

    def test_create_data_monitor(self):
        """Test data monitor factory"""
        monitor = create_data_monitor("factory_test")

        assert isinstance(monitor, RealTimeDataMonitor)
        assert monitor.config.id == "factory_test"


@pytest.fixture
def sample_financial_data():
    """Fixture providing sample financial data for tests"""
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    np.random.seed(42)  # For reproducible tests

    data = pd.DataFrame({
        'date': dates,
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 105,
        'low': np.random.randn(len(dates)).cumsum() + 95,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(500000, 2000000, len(dates)),
        'revenue': np.random.randn(len(dates)).cumsum() + 1000000,
        'net_income': np.random.randn(len(dates)).cumsum() + 100000
    })

    return data


@pytest.fixture
def sample_correlation_data():
    """Fixture providing sample correlation data for tests"""
    np.random.seed(42)
    n_vars = 10
    n_obs = 100

    # Generate correlated data
    base_data = np.random.randn(n_obs, n_vars)
    correlation_matrix = np.random.rand(n_vars, n_vars)
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
    np.fill_diagonal(correlation_matrix, 1)

    data = pd.DataFrame(
        base_data @ np.linalg.cholesky(correlation_matrix).T,
        columns=[f'Var_{i}' for i in range(n_vars)]
    )

    return data


if __name__ == "__main__":
    pytest.main([__file__])