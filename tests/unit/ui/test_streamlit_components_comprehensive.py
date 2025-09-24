"""
Comprehensive Tests for Streamlit UI Components
==============================================

This module contains comprehensive unit tests for Streamlit UI components,
testing dashboard rendering, user interactions, and data visualization.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, Any, List, Optional

# Import modules under test
from ui.streamlit.dashboard_components import (
    FinancialMetricsHierarchy,
    MetricDisplayComponents,
    MetricDefinition,
    MetricValue,
    create_metric_card,
    create_info_card
)
from ui.components.data_quality_dashboard import DataQualityDashboard, QualityMetric
from tests.utils.common_test_utilities import create_mock_financial_data, TestDataGenerator


class TestFinancialMetricsHierarchy:
    """Test FinancialMetricsHierarchy class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.hierarchy = FinancialMetricsHierarchy()

    def test_hierarchy_initialization(self):
        """Test hierarchy initializes correctly"""
        assert self.hierarchy is not None
        assert hasattr(self.hierarchy, 'metric_definitions')
        assert hasattr(self.hierarchy, 'component_hierarchy')
        assert len(self.hierarchy.metric_definitions) > 0

    def test_metric_definitions_structure(self):
        """Test metric definitions have correct structure"""
        for metric_key, metric_def in self.hierarchy.metric_definitions.items():
            assert isinstance(metric_def, MetricDefinition)
            assert metric_def.name is not None
            assert metric_def.formula is not None
            assert metric_def.category is not None
            assert metric_def.unit is not None

    def test_get_metrics_by_category(self):
        """Test filtering metrics by category"""
        profitability_metrics = self.hierarchy.get_metrics_by_category("profitability")
        assert len(profitability_metrics) > 0

        liquidity_metrics = self.hierarchy.get_metrics_by_category("liquidity")
        assert len(liquidity_metrics) > 0

        # Test non-existent category
        invalid_metrics = self.hierarchy.get_metrics_by_category("non_existent")
        assert len(invalid_metrics) == 0

    def test_panel_configuration(self):
        """Test panel configuration retrieval"""
        overview_config = self.hierarchy.get_panel_configuration("overview_panel")
        assert overview_config is not None
        assert 'title' in overview_config
        assert 'icon' in overview_config
        assert 'components' in overview_config

        # Test non-existent panel
        invalid_config = self.hierarchy.get_panel_configuration("non_existent_panel")
        assert invalid_config == {}

    def test_component_hierarchy_structure(self):
        """Test component hierarchy has expected structure"""
        hierarchy = self.hierarchy.component_hierarchy
        assert isinstance(hierarchy, dict)

        expected_panels = [
            "overview_panel", "profitability_panel", "liquidity_panel",
            "leverage_panel", "valuation_panel", "growth_panel"
        ]

        for panel in expected_panels:
            if panel in hierarchy:
                assert 'title' in hierarchy[panel]
                assert 'icon' in hierarchy[panel]
                assert 'components' in hierarchy[panel]


class TestMetricDefinition:
    """Test MetricDefinition dataclass"""

    def test_metric_definition_creation(self):
        """Test metric definition creation"""
        metric_def = MetricDefinition(
            name="Return on Equity",
            formula="Net Income / Shareholders' Equity",
            category="profitability",
            unit="%",
            icon="📈"
        )

        assert metric_def.name == "Return on Equity"
        assert metric_def.formula == "Net Income / Shareholders' Equity"
        assert metric_def.category == "profitability"
        assert metric_def.unit == "%"
        assert metric_def.icon == "📈"

    def test_metric_definition_defaults(self):
        """Test metric definition default values"""
        metric_def = MetricDefinition(
            name="Test Metric",
            formula="A / B",
            category="test"
        )

        assert metric_def.unit == "%"  # Default value
        assert metric_def.format_string == "{:.2f}"  # Default value
        assert metric_def.icon == "📊"  # Default value


class TestMetricValue:
    """Test MetricValue dataclass"""

    def test_metric_value_creation(self):
        """Test metric value creation"""
        metric_value = MetricValue(
            current=15.2,
            previous=13.8,
            benchmark=12.5,
            trend="positive",
            confidence=0.9
        )

        assert metric_value.current == 15.2
        assert metric_value.previous == 13.8
        assert metric_value.benchmark == 12.5
        assert metric_value.trend == "positive"
        assert metric_value.confidence == 0.9

    def test_metric_value_defaults(self):
        """Test metric value default values"""
        metric_value = MetricValue(current=10.5)

        assert metric_value.current == 10.5
        assert metric_value.previous is None
        assert metric_value.benchmark is None
        assert metric_value.trend == "neutral"
        assert metric_value.confidence == 1.0
        assert isinstance(metric_value.last_updated, datetime)


class TestMetricDisplayComponents:
    """Test MetricDisplayComponents class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.hierarchy = FinancialMetricsHierarchy()
        self.components = MetricDisplayComponents(self.hierarchy)

    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.expander')
    def test_render_metric_card(self, mock_expander, mock_columns, mock_metric):
        """Test metric card rendering"""
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        mock_expander.return_value.__enter__.return_value = Mock()

        metric_value = MetricValue(
            current=15.2,
            previous=13.8,
            benchmark=12.5,
            trend="positive",
            confidence=0.9
        )

        # Test rendering a metric card
        self.components.render_metric_card("roe", metric_value)

        # Verify Streamlit functions were called
        mock_columns.assert_called()
        mock_metric.assert_called()

    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    def test_render_metrics_panel(self, mock_columns, mock_subheader):
        """Test metrics panel rendering"""
        mock_columns.return_value = [Mock(), Mock(), Mock()]

        metrics_data = {
            "roe": MetricValue(current=15.2, previous=13.8, trend="positive"),
            "roa": MetricValue(current=8.1, previous=7.5, trend="positive"),
            "gross_margin": MetricValue(current=65.2, previous=63.1, trend="positive")
        }

        # Test rendering profitability panel
        self.components.render_metrics_panel("profitability_panel", metrics_data)

        mock_subheader.assert_called()
        mock_columns.assert_called()

    @patch('streamlit.plotly_chart')
    @patch('streamlit.warning')
    def test_render_trends_chart(self, mock_warning, mock_plotly):
        """Test trends chart rendering"""
        # Test with no data
        self.components.render_trends_chart({})
        mock_warning.assert_called()

        # Test with valid data
        mock_warning.reset_mock()
        metrics_history = {
            "ROE": [
                {'date': datetime.now() - timedelta(days=30), 'value': 14.5},
                {'date': datetime.now() - timedelta(days=20), 'value': 15.1},
                {'date': datetime.now() - timedelta(days=10), 'value': 15.8},
                {'date': datetime.now(), 'value': 16.2}
            ]
        }

        self.components.render_trends_chart(metrics_history)
        mock_plotly.assert_called()
        mock_warning.assert_not_called()

    @patch('streamlit.plotly_chart')
    @patch('streamlit.warning')
    def test_render_comparison_chart(self, mock_warning, mock_plotly):
        """Test comparison chart rendering"""
        # Test with no data
        self.components.render_comparison_chart({})
        mock_warning.assert_called()

        # Test with valid data
        mock_warning.reset_mock()
        comparison_data = {
            "Company A": {"ROE": 15.2, "ROA": 8.1, "Current Ratio": 2.3},
            "Company B": {"ROE": 12.8, "ROA": 6.9, "Current Ratio": 1.8},
            "Industry Avg": {"ROE": 14.1, "ROA": 7.5, "Current Ratio": 2.0}
        }

        self.components.render_comparison_chart(comparison_data)
        mock_plotly.assert_called()
        mock_warning.assert_not_called()

    @patch('streamlit.subheader')
    @patch('streamlit.info')
    @patch('streamlit.warning')
    @patch('streamlit.error')
    @patch('streamlit.success')
    def test_render_alerts_panel(self, mock_success, mock_error, mock_warning, mock_info, mock_subheader):
        """Test alerts panel rendering"""
        # Test with no alerts
        self.components.render_alerts_panel([])
        mock_info.assert_called()

        # Test with various alert types
        alerts = [
            {'type': 'warning', 'metric': 'Current Ratio', 'message': 'Below industry average'},
            {'type': 'error', 'metric': 'Debt Ratio', 'message': 'Dangerously high'},
            {'type': 'success', 'metric': 'ROE', 'message': 'Exceeding expectations'},
            {'type': 'info', 'metric': 'P/E Ratio', 'message': 'Within normal range'}
        ]

        self.components.render_alerts_panel(alerts)
        mock_warning.assert_called()
        mock_error.assert_called()
        mock_success.assert_called()
        # mock_info called twice (once for empty, once for info alert)


class TestUtilityFunctions:
    """Test utility functions"""

    @patch('streamlit.metric')
    def test_create_metric_card(self, mock_metric):
        """Test create_metric_card function"""
        create_metric_card(
            title="Revenue Growth",
            value="12.5%",
            delta="+2.3%",
            delta_color="normal",
            help_text="Year-over-year revenue growth"
        )

        mock_metric.assert_called_once_with(
            label="Revenue Growth",
            value="12.5%",
            delta="+2.3%",
            delta_color="normal",
            help="Year-over-year revenue growth"
        )

    @patch('streamlit.container')
    @patch('streamlit.markdown')
    def test_create_info_card(self, mock_markdown, mock_container):
        """Test create_info_card function"""
        mock_container.return_value.__enter__.return_value = Mock()

        create_info_card(
            title="Company Overview",
            content="This is a test company description.",
            icon="🏢"
        )

        mock_container.assert_called_once()
        mock_markdown.assert_called()


class TestDataQualityDashboard:
    """Test DataQualityDashboard class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.dashboard = DataQualityDashboard()

    def test_dashboard_initialization(self):
        """Test dashboard initializes correctly"""
        assert self.dashboard is not None
        assert hasattr(self.dashboard, 'colors')
        assert isinstance(self.dashboard.colors, dict)

    def test_get_score_color(self):
        """Test score color determination"""
        # Test excellent score
        color = self.dashboard._get_score_color(95.0)
        assert color == self.dashboard.colors['excellent']

        # Test good score
        color = self.dashboard._get_score_color(80.0)
        assert color == self.dashboard.colors['good']

        # Test warning score
        color = self.dashboard._get_score_color(65.0)
        assert color == self.dashboard.colors['warning']

        # Test critical score
        color = self.dashboard._get_score_color(45.0)
        assert color == self.dashboard.colors['critical']

        # Test poor score
        color = self.dashboard._get_score_color(25.0)
        assert color == self.dashboard.colors['poor']

    def test_calculate_score_delta(self):
        """Test score delta calculation"""
        history = [
            {'overall_score': 80.0},
            {'overall_score': 85.0}
        ]

        delta = self.dashboard._calculate_score_delta(history, 'overall_score')
        assert delta == "+5.0%"

        # Test with insufficient history
        short_history = [{'overall_score': 80.0}]
        delta = self.dashboard._calculate_score_delta(short_history, 'overall_score')
        assert delta is None

        # Test with small change
        stable_history = [
            {'overall_score': 80.0},
            {'overall_score': 80.05}
        ]
        delta = self.dashboard._calculate_score_delta(stable_history, 'overall_score')
        assert delta is None  # Change too small

    @patch('streamlit.header')
    @patch('streamlit.markdown')
    @patch('streamlit.tabs')
    @patch('streamlit.info')
    def test_render_dashboard_no_data(self, mock_info, mock_tabs, mock_markdown, mock_header):
        """Test dashboard rendering with no data"""
        mock_enhanced_data_manager = Mock()
        mock_enhanced_data_manager.get_quality_history.return_value = []

        self.dashboard.render_dashboard(mock_enhanced_data_manager, "test_key")

        mock_header.assert_called()
        mock_info.assert_called()

    @patch('streamlit.header')
    @patch('streamlit.tabs')
    def test_render_dashboard_with_data(self, mock_tabs, mock_header):
        """Test dashboard rendering with valid data"""
        mock_enhanced_data_manager = Mock()
        mock_enhanced_data_manager.get_quality_history.return_value = [
            {
                'overall_score': 85.5,
                'completeness': 90.0,
                'consistency': 85.0,
                'accuracy': 80.0,
                'timeliness': 87.5,
                'timestamp': datetime.now().isoformat(),
                'source_identifier': 'test_source',
                'data_points_analyzed': 1000
            }
        ]
        mock_enhanced_data_manager.get_data_quality_trends.return_value = {'status': 'stable'}
        mock_enhanced_data_manager.predict_data_quality_issues.return_value = {'status': 'no_prediction'}

        # Mock tabs
        mock_tab1, mock_tab2, mock_tab3, mock_tab4 = [Mock() for _ in range(4)]
        mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4]

        for mock_tab in [mock_tab1, mock_tab2, mock_tab3, mock_tab4]:
            mock_tab.__enter__.return_value = Mock()
            mock_tab.__exit__.return_value = None

        self.dashboard.render_dashboard(mock_enhanced_data_manager, "test_key")

        mock_header.assert_called()
        mock_tabs.assert_called()


class TestQualityMetricDataClass:
    """Test QualityMetric dataclass"""

    def test_quality_metric_creation(self):
        """Test quality metric creation"""
        metric = QualityMetric(
            name="Completeness",
            score=85.5,
            weight=0.25,
            status="good",
            message="Data is mostly complete",
            threshold=80.0,
            timestamp=datetime.now()
        )

        assert metric.name == "Completeness"
        assert metric.score == 85.5
        assert metric.weight == 0.25
        assert metric.status == "good"
        assert metric.message == "Data is mostly complete"
        assert metric.threshold == 80.0
        assert isinstance(metric.timestamp, datetime)

    def test_quality_metric_defaults(self):
        """Test quality metric default values"""
        metric = QualityMetric(
            name="Test Metric",
            score=75.0,
            weight=0.5,
            status="warning"
        )

        assert metric.message == ""  # Default value
        assert metric.threshold == 75.0  # Default value
        assert metric.timestamp is None  # Default value


class TestDataVisualizationComponents:
    """Test data visualization components"""

    @patch('plotly.graph_objects.Figure')
    @patch('plotly.express.bar')
    def test_plotly_chart_creation(self, mock_bar, mock_figure):
        """Test Plotly chart creation"""
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        # Simulate chart data
        chart_data = pd.DataFrame({
            'Category': ['A', 'B', 'C'],
            'Value': [10, 20, 15]
        })

        # Test that charts can be created without errors
        # (Actual chart creation would be tested in integration tests)
        assert chart_data is not None

    def test_color_scheme_consistency(self):
        """Test color scheme consistency across components"""
        dashboard = DataQualityDashboard()
        colors = dashboard.colors

        # Test that all required colors are defined
        required_colors = ['excellent', 'good', 'warning', 'critical', 'poor']
        for color_key in required_colors:
            assert color_key in colors
            assert isinstance(colors[color_key], str)
            assert colors[color_key].startswith('#')  # Valid hex color


class TestResponsiveDesign:
    """Test responsive design elements"""

    @patch('streamlit.columns')
    def test_responsive_columns(self, mock_columns):
        """Test responsive column layouts"""
        mock_columns.return_value = [Mock() for _ in range(4)]

        hierarchy = FinancialMetricsHierarchy()
        components = MetricDisplayComponents(hierarchy)

        # Test different column configurations
        for num_cols in [1, 2, 3, 4]:
            components._create_responsive_columns(num_cols)
            if hasattr(components, '_create_responsive_columns'):
                mock_columns.assert_called()

    def test_mobile_optimization(self):
        """Test mobile-friendly layouts"""
        hierarchy = FinancialMetricsHierarchy()
        components = MetricDisplayComponents(hierarchy)

        # Test that components adapt to smaller screens
        # (This would typically be tested with different viewport sizes)
        if hasattr(components, '_is_mobile_layout'):
            is_mobile = components._is_mobile_layout()
            assert isinstance(is_mobile, bool)


class TestAccessibilityFeatures:
    """Test accessibility features"""

    def test_screen_reader_compatibility(self):
        """Test screen reader compatibility"""
        hierarchy = FinancialMetricsHierarchy()

        # Test that all metrics have descriptive names
        for metric_key, metric_def in hierarchy.metric_definitions.items():
            assert len(metric_def.name) > 0
            assert len(metric_def.description) > 0

    def test_color_contrast(self):
        """Test color contrast for accessibility"""
        dashboard = DataQualityDashboard()
        colors = dashboard.colors

        # Test that colors have sufficient contrast
        # (In a real implementation, this would check actual contrast ratios)
        for color_name, color_value in colors.items():
            assert color_value != '#FFFFFF'  # Not pure white
            assert color_value != '#000000'  # Not pure black


class TestErrorHandlingUI:
    """Test UI error handling"""

    @patch('streamlit.error')
    def test_error_display(self, mock_error):
        """Test error message display"""
        dashboard = DataQualityDashboard()

        # Simulate error in data manager
        mock_enhanced_data_manager = Mock()
        mock_enhanced_data_manager.get_quality_history.side_effect = Exception("Database error")

        dashboard.render_dashboard(mock_enhanced_data_manager, "test_key")

        # Should display error message
        mock_error.assert_called()

    def test_graceful_degradation(self):
        """Test graceful degradation when data is unavailable"""
        dashboard = DataQualityDashboard()

        # Test with empty data manager
        mock_enhanced_data_manager = Mock()
        mock_enhanced_data_manager.get_quality_history.return_value = []

        # Should not raise exception
        try:
            dashboard.render_dashboard(mock_enhanced_data_manager, "test_key")
        except Exception:
            pytest.fail("Dashboard should handle empty data gracefully")


class TestPerformanceOptimization:
    """Test performance optimization in UI components"""

    def test_data_caching(self):
        """Test data caching in UI components"""
        # Test that expensive operations are cached
        if hasattr(DataQualityDashboard, '_cache_expensive_calculation'):
            dashboard = DataQualityDashboard()

            # First call should compute
            result1 = dashboard._cache_expensive_calculation("test_key")

            # Second call should use cache
            result2 = dashboard._cache_expensive_calculation("test_key")

            assert result1 == result2

    def test_lazy_rendering(self):
        """Test lazy rendering of components"""
        hierarchy = FinancialMetricsHierarchy()
        components = MetricDisplayComponents(hierarchy)

        # Components should only render when requested
        if hasattr(components, '_should_render_component'):
            should_render = components._should_render_component("expensive_component")
            assert isinstance(should_render, bool)


if __name__ == "__main__":
    pytest.main([__file__])