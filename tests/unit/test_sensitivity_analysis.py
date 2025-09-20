"""
Unit Tests for Sensitivity Analysis Module
==========================================

This module contains comprehensive unit tests for the sensitivity analysis framework,
including tests for parameter definitions, calculation methods, visualization components,
and integration with existing valuation engines.

Test Coverage:
- SensitivityParameter data structure
- SensitivityAnalyzer main functionality
- One-way sensitivity analysis
- Two-way sensitivity analysis
- Tornado analysis
- Elasticity calculations
- Breakeven analysis
- Integration with DCF/DDM/P/B engines
- Visualization components
- Error handling and edge cases
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import modules under test
from core.analysis.risk.sensitivity_analysis import (
    SensitivityParameter, ParameterType, SensitivityAnalyzer,
    SensitivityResult, SensitivityMethod, quick_tornado_analysis,
    create_custom_parameter
)
from core.analysis.risk.sensitivity_integration import (
    SensitivityIntegrator, DCFSensitivityAdapter, DDMSensitivityAdapter,
    PBSensitivityAdapter, create_integrated_sensitivity_analyzer
)
from ui.visualization.sensitivity_visualizer import (
    SensitivityVisualizer, VisualizationConfig
)


class TestSensitivityParameter:
    """Test cases for SensitivityParameter data structure."""

    def test_parameter_creation(self):
        """Test basic parameter creation."""
        param = SensitivityParameter(
            name='revenue_growth',
            param_type=ParameterType.REVENUE_GROWTH,
            base_value=0.05,
            sensitivity_range=(-0.10, 0.20),
            steps=21
        )

        assert param.name == 'revenue_growth'
        assert param.param_type == ParameterType.REVENUE_GROWTH
        assert param.base_value == 0.05
        assert param.sensitivity_range == (-0.10, 0.20)
        assert param.steps == 21
        assert param.display_name == 'Revenue Growth'

    def test_parameter_display_name_override(self):
        """Test custom display name."""
        param = SensitivityParameter(
            name='test_param',
            param_type=ParameterType.DISCOUNT_RATE,
            base_value=0.10,
            sensitivity_range=(0.05, 0.15),
            display_name='Custom Display Name'
        )

        assert param.display_name == 'Custom Display Name'

    def test_generate_test_values(self):
        """Test test value generation."""
        param = SensitivityParameter(
            name='discount_rate',
            param_type=ParameterType.DISCOUNT_RATE,
            base_value=0.10,
            sensitivity_range=(0.05, 0.15),
            steps=11
        )

        test_values = param.generate_test_values()

        assert len(test_values) == 11
        assert test_values[0] == 0.05
        assert test_values[-1] == 0.15
        assert np.isclose(test_values[5], 0.10)  # Middle value should be close to base

    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        param = SensitivityParameter(
            name='growth_rate',
            param_type=ParameterType.REVENUE_GROWTH,
            base_value=0.05,
            sensitivity_range=(0.0, 0.10)
        )

        # Test positive change
        pct_change = param.calculate_percentage_change(0.075)
        assert np.isclose(pct_change, 50.0)  # 50% increase

        # Test negative change
        pct_change = param.calculate_percentage_change(0.025)
        assert np.isclose(pct_change, -50.0)  # 50% decrease

        # Test zero base value
        param.base_value = 0.0
        pct_change = param.calculate_percentage_change(0.05)
        assert pct_change == 0.0


class TestSensitivityAnalyzer:
    """Test cases for SensitivityAnalyzer main functionality."""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create mock financial calculator."""
        calc = Mock()
        calc.calculate_dcf_inputs.return_value = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'growth_rate_yr1_5': 0.05,
            'operating_margin': 0.20,
            'tax_rate': 0.25
        }
        return calc

    @pytest.fixture
    def analyzer(self, mock_financial_calculator):
        """Create sensitivity analyzer instance."""
        return SensitivityAnalyzer(mock_financial_calculator)

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.financial_calculator is not None
        assert 'revenue_growth' in analyzer.default_parameters
        assert 'discount_rate' in analyzer.default_parameters
        assert len(analyzer.analysis_cache) == 0

    def test_default_parameters(self, analyzer):
        """Test default parameter definitions."""
        params = analyzer.default_parameters

        # Check key parameters exist
        assert 'revenue_growth' in params
        assert 'discount_rate' in params
        assert 'terminal_growth' in params
        assert 'operating_margin' in params

        # Check parameter properties
        revenue_param = params['revenue_growth']
        assert revenue_param.param_type == ParameterType.REVENUE_GROWTH
        assert revenue_param.base_value == 0.05
        assert revenue_param.sensitivity_range == (-0.10, 0.25)

    def test_parse_parameters_list(self, analyzer):
        """Test parameter parsing from list."""
        param_list = ['revenue_growth', 'discount_rate']
        parsed = analyzer._parse_parameters(param_list)

        assert len(parsed) == 2
        assert 'revenue_growth' in parsed
        assert 'discount_rate' in parsed
        assert isinstance(parsed['revenue_growth'], SensitivityParameter)

    def test_parse_parameters_dict(self, analyzer):
        """Test parameter parsing from dictionary."""
        param_dict = {
            'revenue_growth': {'base': 0.08, 'range': (-0.05, 0.15), 'steps': 11},
            'discount_rate': {'base': 0.12, 'range': (0.08, 0.16)}
        }
        parsed = analyzer._parse_parameters(param_dict)

        assert len(parsed) == 2
        assert parsed['revenue_growth'].base_value == 0.08
        assert parsed['revenue_growth'].sensitivity_range == (-0.05, 0.15)
        assert parsed['revenue_growth'].steps == 11
        assert parsed['discount_rate'].base_value == 0.12

    def test_simplified_dcf_calculation(self, analyzer):
        """Test simplified DCF calculation."""
        params = {
            'revenue_growth': 0.08,
            'discount_rate': 0.11,
            'terminal_growth': 0.025,
            'operating_margin': 0.22,
            'tax_rate': 0.24
        }

        value = analyzer._simplified_dcf_calculation(params)

        assert isinstance(value, float)
        assert value > 0
        # Value should be reasonable for a simplified DCF
        assert 10 < value < 1000

    def test_calculate_elasticity(self, analyzer):
        """Test elasticity calculation."""
        test_values = np.array([0.03, 0.04, 0.05, 0.06, 0.07])
        output_values = [90, 95, 100, 105, 110]
        base_input = 0.05
        base_output = 100

        elasticity = analyzer._calculate_elasticity(test_values, output_values, base_input, base_output)

        # Expected elasticity should be approximately 1.0 for this linear relationship
        assert 0.8 < elasticity < 1.2

    def test_one_way_sensitivity(self, analyzer):
        """Test one-way sensitivity analysis."""
        parameters = ['revenue_growth', 'discount_rate']

        # Mock the valuation calculation
        def mock_calculate_valuation(method, overrides, custom_func=None):
            base_value = 100
            # Simple mock: revenue growth increases value, discount rate decreases it
            if 'revenue_growth' in overrides:
                base_value += overrides['revenue_growth'] * 1000
            if 'discount_rate' in overrides:
                base_value -= (overrides['discount_rate'] - 0.10) * 500
            return base_value

        analyzer._calculate_valuation = mock_calculate_valuation

        result = analyzer.one_way_sensitivity('dcf', parameters)

        assert isinstance(result, SensitivityResult)
        assert result.method == SensitivityMethod.ONE_WAY
        assert len(result.parameters) == 2
        assert 'revenue_growth' in result.results
        assert 'discount_rate' in result.results
        assert len(result.rankings) > 0

    def test_tornado_analysis(self, analyzer):
        """Test tornado analysis."""
        parameters = ['revenue_growth', 'discount_rate']

        # Mock the valuation calculation
        def mock_calculate_valuation(method, overrides, custom_func=None):
            base_value = 100
            if 'revenue_growth' in overrides:
                base_value += overrides['revenue_growth'] * 800
            if 'discount_rate' in overrides:
                base_value -= (overrides['discount_rate'] - 0.10) * 400
            return base_value

        analyzer._calculate_valuation = mock_calculate_valuation

        result = analyzer.tornado_analysis('dcf', parameters, variation_percentage=0.20)

        assert isinstance(result, SensitivityResult)
        assert result.method == SensitivityMethod.TORNADO
        assert 'tornado_data' in result.results
        assert len(result.rankings) > 0

        # Check tornado data structure
        tornado_data = result.results['tornado_data']
        assert len(tornado_data) == 2
        for item in tornado_data:
            assert 'parameter_name' in item
            assert 'impact_range' in item
            assert 'upside_impact' in item
            assert 'downside_impact' in item

    def test_two_way_sensitivity(self, analyzer):
        """Test two-way sensitivity analysis."""
        # Mock the valuation calculation
        def mock_calculate_valuation(method, overrides, custom_func=None):
            base_value = 100
            if 'revenue_growth' in overrides:
                base_value += overrides['revenue_growth'] * 500
            if 'discount_rate' in overrides:
                base_value -= (overrides['discount_rate'] - 0.10) * 300
            return base_value

        analyzer._calculate_valuation = mock_calculate_valuation

        result = analyzer.two_way_sensitivity('dcf', 'revenue_growth', 'discount_rate')

        assert isinstance(result, SensitivityResult)
        assert result.method == SensitivityMethod.TWO_WAY
        assert 'heatmap_data' in result.results
        assert 'param1_values' in result.results
        assert 'param2_values' in result.results

        # Check heatmap data dimensions
        heatmap_data = result.results['heatmap_data']
        param1_values = result.results['param1_values']
        param2_values = result.results['param2_values']
        assert len(heatmap_data) == len(param2_values)
        assert len(heatmap_data[0]) == len(param1_values)

    def test_elasticity_analysis(self, analyzer):
        """Test elasticity analysis."""
        parameters = ['revenue_growth', 'discount_rate']

        # Mock the valuation calculation
        def mock_calculate_valuation(method, overrides, custom_func=None):
            base_value = 100
            if 'revenue_growth' in overrides:
                base_value += overrides['revenue_growth'] * 600
            if 'discount_rate' in overrides:
                base_value -= (overrides['discount_rate'] - 0.10) * 400
            return base_value

        analyzer._calculate_valuation = mock_calculate_valuation

        result = analyzer.elasticity_analysis('dcf', parameters)

        assert isinstance(result, SensitivityResult)
        assert result.method == SensitivityMethod.ELASTICITY
        assert 'elasticity_data' in result.results
        assert len(result.rankings) > 0

        # Check elasticity data
        elasticity_data = result.results['elasticity_data']
        for item in elasticity_data:
            assert 'elasticity' in item
            assert 'interpretation' in item
            assert 'sensitivity_level' in item

    def test_breakeven_analysis(self, analyzer):
        """Test breakeven analysis."""
        parameters = ['revenue_growth', 'discount_rate']
        target_values = [90, 110, 120]

        # Mock the valuation calculation
        def mock_calculate_valuation(method, overrides, custom_func=None):
            base_value = 100
            if 'revenue_growth' in overrides:
                base_value += overrides['revenue_growth'] * 400
            if 'discount_rate' in overrides:
                base_value -= (overrides['discount_rate'] - 0.10) * 500
            return base_value

        analyzer._calculate_valuation = mock_calculate_valuation

        result = analyzer.breakeven_analysis('dcf', target_values, parameters)

        assert isinstance(result, SensitivityResult)
        assert result.method == SensitivityMethod.BREAKEVEN
        assert 'breakeven_data' in result.results
        assert len(result.rankings) > 0

        # Check breakeven data
        breakeven_data = result.results['breakeven_data']
        assert len(breakeven_data) == len(target_values)
        for target_result in breakeven_data:
            assert 'target_value' in target_result
            assert 'parameter_breakevens' in target_result


class TestSensitivityIntegration:
    """Test cases for sensitivity analysis integration."""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create mock financial calculator."""
        calc = Mock()
        calc.calculate_dcf_inputs.return_value = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'growth_rate_yr1_5': 0.05,
            'operating_margin': 0.20,
            'tax_rate': 0.25
        }
        return calc

    @pytest.fixture
    def mock_dcf_valuator(self):
        """Create mock DCF valuator."""
        valuator = Mock()
        valuator.calculate_dcf_projections.return_value = {'value_per_share': 125.50}
        return valuator

    @pytest.fixture
    def integrator(self, mock_financial_calculator):
        """Create sensitivity integrator."""
        return SensitivityIntegrator(mock_financial_calculator)

    def test_integrator_initialization(self, integrator):
        """Test integrator initialization."""
        assert integrator.financial_calculator is not None
        assert 'dcf' in integrator.adapters
        assert 'ddm' in integrator.adapters
        assert 'pb' in integrator.adapters

    def test_dcf_adapter_parameter_mapping(self, integrator):
        """Test DCF adapter parameter mappings."""
        dcf_adapter = integrator.dcf_adapter
        mappings = dcf_adapter.get_parameter_info()

        assert 'revenue_growth' in mappings
        assert 'discount_rate' in mappings
        assert 'terminal_growth' in mappings

        # Check mapping properties
        revenue_mapping = mappings['revenue_growth']
        assert revenue_mapping.engine_parameter == 'growth_rate_yr1_5'
        assert revenue_mapping.validation_range == (-0.50, 2.0)

    def test_parameter_validation(self, integrator):
        """Test parameter validation."""
        # Valid parameters
        valid_params = {'revenue_growth': 0.08, 'discount_rate': 0.11}
        is_valid, errors = integrator.validate_parameters('dcf', valid_params)
        assert is_valid
        assert len(errors) == 0

        # Invalid parameters
        invalid_params = {'revenue_growth': 5.0, 'unknown_param': 0.1}
        is_valid, errors = integrator.validate_parameters('dcf', invalid_params)
        assert not is_valid
        assert len(errors) > 0

    @patch('core.analysis.dcf.dcf_valuation.DCFValuator')
    def test_dcf_calculation_with_overrides(self, mock_dcf_class, integrator):
        """Test DCF calculation with parameter overrides."""
        mock_dcf_instance = Mock()
        mock_dcf_instance.calculate_dcf_projections.return_value = {'value_per_share': 130.0}
        mock_dcf_class.return_value = mock_dcf_instance

        # Reset the adapter with the mocked DCF valuator
        integrator.dcf_adapter.dcf_valuator = mock_dcf_instance

        overrides = {'revenue_growth': 0.08, 'discount_rate': 0.11}
        result = integrator.calculate_valuation('dcf', overrides)

        assert isinstance(result, float)
        assert result > 0
        mock_dcf_instance.calculate_dcf_projections.assert_called_once()

    def test_get_available_parameters(self, integrator):
        """Test getting available parameters for each method."""
        dcf_params = integrator.get_available_parameters('dcf')
        ddm_params = integrator.get_available_parameters('ddm')
        pb_params = integrator.get_available_parameters('pb')

        assert len(dcf_params) > 0
        assert len(ddm_params) > 0
        assert len(pb_params) > 0

        # Check DCF parameters
        assert 'revenue_growth' in dcf_params
        assert 'discount_rate' in dcf_params

        # Check DDM parameters
        assert 'dividend_growth' in ddm_params
        assert 'required_return' in ddm_params

        # Check P/B parameters
        assert 'roe' in pb_params
        assert 'required_return' in pb_params

    def test_method_info(self, integrator):
        """Test getting method information."""
        info = integrator.get_method_info()

        assert 'dcf' in info
        assert 'ddm' in info
        assert 'pb' in info

        # Check DCF info structure
        dcf_info = info['dcf']
        assert 'parameters' in dcf_info
        assert 'parameter_count' in dcf_info
        assert dcf_info['parameter_count'] > 0

    def test_integration_test_framework(self, integrator):
        """Test the integration test framework."""
        # Mock the adapters to return test values
        integrator.dcf_adapter.calculate_valuation = Mock(return_value=125.0)
        integrator.ddm_adapter.calculate_valuation = Mock(return_value=50.0)
        integrator.pb_adapter.calculate_valuation = Mock(return_value=80.0)

        # Test DCF integration
        dcf_test = integrator.test_integration('dcf')
        assert dcf_test['method'] == 'dcf'
        assert dcf_test['base_case_success']
        assert dcf_test['base_case_value'] == 125.0


class TestSensitivityVisualization:
    """Test cases for sensitivity analysis visualization."""

    @pytest.fixture
    def sample_tornado_result(self):
        """Create sample tornado analysis result."""
        from core.analysis.risk.sensitivity_analysis import SensitivityParameter, ParameterType

        parameters = {
            'revenue_growth': SensitivityParameter(
                'revenue_growth', ParameterType.REVENUE_GROWTH, 0.05, (-0.1, 0.2)
            ),
            'discount_rate': SensitivityParameter(
                'discount_rate', ParameterType.DISCOUNT_RATE, 0.10, (0.06, 0.15)
            )
        }

        tornado_data = [
            {
                'parameter_name': 'revenue_growth',
                'display_name': 'Revenue Growth Rate',
                'base_value': 0.05,
                'high_value': 0.08,
                'low_value': 0.02,
                'high_valuation': 120,
                'low_valuation': 80,
                'impact_range': 40,
                'upside_impact': 20,
                'downside_impact': -20,
                'upside_percentage': 20.0,
                'downside_percentage': -20.0
            },
            {
                'parameter_name': 'discount_rate',
                'display_name': 'Discount Rate',
                'base_value': 0.10,
                'high_value': 0.12,
                'low_value': 0.08,
                'high_valuation': 85,
                'low_valuation': 115,
                'impact_range': 30,
                'upside_impact': -15,
                'downside_impact': 15,
                'upside_percentage': -15.0,
                'downside_percentage': 15.0
            }
        ]

        result = SensitivityResult(
            analysis_id='test_tornado',
            method=SensitivityMethod.TORNADO,
            base_case_value=100.0,
            parameters=parameters,
            results={'tornado_data': tornado_data}
        )

        return result

    def test_visualizer_initialization(self, sample_tornado_result):
        """Test visualizer initialization."""
        visualizer = SensitivityVisualizer(sample_tornado_result)

        assert visualizer.result == sample_tornado_result
        assert isinstance(visualizer.config, VisualizationConfig)

    def test_tornado_chart_creation(self, sample_tornado_result):
        """Test tornado chart creation."""
        visualizer = SensitivityVisualizer(sample_tornado_result)

        fig = visualizer.create_tornado_chart()

        # Check figure properties
        assert fig.layout.title.text is not None
        assert 'tornado' in fig.layout.title.text.lower() or 'test_tornado' in fig.layout.title.text
        assert len(fig.data) == 2  # Two traces: upside and downside

    def test_visualization_config(self):
        """Test visualization configuration."""
        config = VisualizationConfig(
            chart_width=1000,
            chart_height=700,
            tornado_colors=('#FF0000', '#00FF00')
        )

        assert config.chart_width == 1000
        assert config.chart_height == 700
        assert config.tornado_colors == ('#FF0000', '#00FF00')
        assert config.line_colors is not None  # Should be set in __post_init__


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create mock financial calculator."""
        calc = Mock()
        calc.calculate_dcf_inputs.return_value = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'growth_rate_yr1_5': 0.05,
            'operating_margin': 0.20,
            'tax_rate': 0.25
        }
        return calc

    def test_create_custom_parameter(self):
        """Test custom parameter creation."""
        param = create_custom_parameter(
            name='custom_param',
            base_value=0.15,
            min_value=0.10,
            max_value=0.20,
            display_name='Custom Parameter',
            units='ratio'
        )

        assert param.name == 'custom_param'
        assert param.base_value == 0.15
        assert param.sensitivity_range == (0.10, 0.20)
        assert param.display_name == 'Custom Parameter'
        assert param.units == 'ratio'

    @patch('core.analysis.risk.sensitivity_analysis.SensitivityAnalyzer')
    def test_quick_tornado_analysis(self, mock_analyzer_class, mock_financial_calculator):
        """Test quick tornado analysis function."""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_analyzer.tornado_analysis.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer

        result = quick_tornado_analysis(mock_financial_calculator, 'dcf', 0.25)

        mock_analyzer_class.assert_called_once_with(mock_financial_calculator)
        mock_analyzer.tornado_analysis.assert_called_once()
        assert result == mock_result

    def test_create_integrated_sensitivity_analyzer(self, mock_financial_calculator):
        """Test integrated analyzer creation."""
        analyzer = create_integrated_sensitivity_analyzer(mock_financial_calculator)

        assert hasattr(analyzer, '_calculate_valuation')
        assert analyzer.financial_calculator == mock_financial_calculator


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with minimal setup."""
        return SensitivityAnalyzer(None)  # No financial calculator

    def test_invalid_valuation_method(self, analyzer):
        """Test handling of invalid valuation method."""
        with pytest.raises(ValueError):
            analyzer._calculate_valuation('invalid_method', {})

    def test_empty_parameters(self, analyzer):
        """Test handling of empty parameters."""
        result = analyzer._parse_parameters([])
        assert len(result) == 0

        result = analyzer._parse_parameters({})
        assert len(result) == 0

    def test_unknown_parameter_name(self, analyzer):
        """Test handling of unknown parameter names."""
        result = analyzer._parse_parameters(['unknown_parameter'])
        assert len(result) == 0  # Should skip unknown parameters

    def test_calculation_failure_handling(self, analyzer):
        """Test handling of calculation failures."""
        # Mock a calculation that always fails
        def failing_calculation(method, overrides, custom_func=None):
            raise Exception("Calculation failed")

        analyzer._calculate_valuation = failing_calculation

        # Should use fallback values instead of crashing
        result = analyzer.one_way_sensitivity('dcf', ['revenue_growth'])
        assert isinstance(result, SensitivityResult)
        assert 'revenue_growth' in result.results

    def test_zero_base_value_handling(self, analyzer):
        """Test handling of zero base values."""
        test_values = np.array([0.01, 0.02, 0.03])
        output_values = [10, 20, 30]

        # Should handle zero base gracefully
        elasticity = analyzer._calculate_elasticity(test_values, output_values, 0.0, 10.0)
        assert elasticity == 0.0


class TestResultExport:
    """Test cases for result export functionality."""

    @pytest.fixture
    def sample_result(self):
        """Create sample result for export testing."""
        from core.analysis.risk.sensitivity_analysis import SensitivityParameter, ParameterType

        parameters = {
            'revenue_growth': SensitivityParameter(
                'revenue_growth', ParameterType.REVENUE_GROWTH, 0.05, (-0.1, 0.2)
            )
        }

        result = SensitivityResult(
            analysis_id='test_export',
            method=SensitivityMethod.ONE_WAY,
            base_case_value=100.0,
            parameters=parameters,
            results={
                'revenue_growth': {
                    'test_values': [0.02, 0.05, 0.08],
                    'values': [90, 100, 110],
                    'elasticity': 1.0
                }
            }
        )

        result.rankings = [
            {'rank': 1, 'parameter_name': 'revenue_growth', 'sensitivity_range': 20}
        ]

        result.statistics = {'mean_sensitivity': 15.0}

        return result

    def test_sensitivity_table_creation(self, sample_result):
        """Test sensitivity table creation."""
        table = sample_result.get_sensitivity_table()

        assert isinstance(table, pd.DataFrame)
        assert len(table) > 0
        assert 'Parameter' in table.columns

    def test_most_sensitive_parameter(self, sample_result):
        """Test most sensitive parameter identification."""
        most_sensitive = sample_result.get_most_sensitive_parameter()
        assert most_sensitive == 'revenue_growth'

    def test_elasticity_calculation_from_result(self, sample_result):
        """Test elasticity calculation from result."""
        elasticity = sample_result.calculate_elasticity('revenue_growth')
        assert elasticity == 1.0

    def test_breakeven_point_calculation(self, sample_result):
        """Test breakeven point calculation."""
        breakeven = sample_result.find_breakeven_point(105, 'revenue_growth')
        # Should interpolate between test points to find value that gives 105
        assert 0.05 < breakeven < 0.08


if __name__ == '__main__':
    pytest.main([__file__, '-v'])