"""
Test Suite for Scenario Modeling System
=======================================

Comprehensive test suite for the scenario modeling system including:
- Scenario parameter creation and validation
- Predefined scenario functionality
- Custom scenario building
- Probability weighting and expected value calculations
- Three-point analysis generation
- Integration with valuation models

Test Categories:
- Unit tests for individual components
- Integration tests for scenario framework
- Validation tests for valuation integration
- Performance tests for large scenario sets
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Import scenario modeling components
from core.analysis.risk.scenario_modeling import (
    ScenarioType,
    ScenarioSeverity,
    ScenarioParameter,
    CustomScenario,
    PredefinedScenarios,
    ScenarioModelingFramework
)

from core.analysis.risk.valuation_scenario_integration import (
    ValuationScenarioIntegrator,
    ScenarioValuationResult,
    quick_three_point_dcf_analysis,
    create_economic_scenario_dcf_analysis
)


class TestScenarioParameter:
    """Test ScenarioParameter functionality."""

    def test_scenario_parameter_creation(self):
        """Test basic scenario parameter creation."""
        param = ScenarioParameter(
            name="revenue_growth",
            variable_type="growth",
            base_value=0.05,
            shock_value=0.10,
            shock_type="absolute",
            description="Revenue growth rate"
        )

        assert param.name == "revenue_growth"
        assert param.base_value == 0.05
        assert param.shock_value == 0.10
        assert param.shock_type == "absolute"

    def test_absolute_shock_application(self):
        """Test absolute shock value application."""
        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.03,
            shock_type="absolute"
        )

        result = param.apply_shock()
        assert result == 0.08  # 0.05 + 0.03

    def test_relative_shock_application(self):
        """Test relative shock value application."""
        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=100.0,
            shock_value=0.20,  # 20% increase
            shock_type="relative"
        )

        result = param.apply_shock()
        assert result == 120.0  # 100 * (1 + 0.20)

    def test_parameter_bounds(self):
        """Test parameter bounds enforcement."""
        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.10,
            shock_type="absolute",
            min_value=0.0,
            max_value=0.12
        )

        result = param.apply_shock()
        assert result == 0.12  # Capped at max_value

    def test_time_series_generation(self):
        """Test time series generation with mean reversion."""
        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.10,
            shock_type="absolute",
            mean_reversion_speed=0.1,
            persistence=0.5
        )

        time_series = param.generate_time_series(periods=10)
        assert len(time_series) == 10
        assert time_series[0] == 0.10  # Initial shocked value
        # Check that values trend back toward base value due to mean reversion
        assert abs(time_series[-1] - param.base_value) < abs(time_series[0] - param.base_value)


class TestCustomScenario:
    """Test CustomScenario functionality."""

    def test_custom_scenario_creation(self):
        """Test basic custom scenario creation."""
        scenario = CustomScenario(
            name="Test Scenario",
            description="Test scenario for unit testing",
            scenario_type=ScenarioType.CUSTOM,
            severity=ScenarioSeverity.MODERATE
        )

        assert scenario.name == "Test Scenario"
        assert scenario.scenario_type == ScenarioType.CUSTOM
        assert scenario.severity == ScenarioSeverity.MODERATE

    def test_parameter_addition_and_removal(self):
        """Test adding and removing parameters from scenario."""
        scenario = CustomScenario(
            name="Test Scenario",
            description="Test scenario"
        )

        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.08
        )

        # Add parameter
        scenario.add_parameter(param)
        assert "test_param" in scenario.parameters
        assert len(scenario.parameters) == 1

        # Remove parameter
        scenario.remove_parameter("test_param")
        assert "test_param" not in scenario.parameters
        assert len(scenario.parameters) == 0

    def test_scenario_value_generation(self):
        """Test scenario value generation."""
        scenario = CustomScenario(
            name="Test Scenario",
            description="Test scenario"
        )

        # Add multiple parameters
        params = [
            ScenarioParameter("param1", "rate", 0.05, 0.08, "absolute"),
            ScenarioParameter("param2", "growth", 0.03, 0.05, "absolute"),
            ScenarioParameter("param3", "margin", 0.20, 0.25, "absolute")
        ]

        for param in params:
            scenario.add_parameter(param)

        # Generate scenario values
        values = scenario.generate_scenario_values(random_state=42)

        assert len(values) == 3
        assert "param1" in values
        assert "param2" in values
        assert "param3" in values
        assert values["param1"] == 0.08
        assert values["param2"] == 0.05
        assert values["param3"] == 0.25

    def test_correlation_matrix_setting(self):
        """Test setting correlation matrix for parameters."""
        scenario = CustomScenario(
            name="Test Scenario",
            description="Test scenario"
        )

        # Add parameters
        params = ["param1", "param2"]
        correlation_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])

        scenario.set_parameter_correlation(params, correlation_matrix)

        assert np.array_equal(scenario.parameter_correlations, correlation_matrix)
        assert scenario.correlation_param_names == params

    def test_scenario_serialization(self):
        """Test scenario serialization to dictionary."""
        scenario = CustomScenario(
            name="Test Scenario",
            description="Test scenario",
            scenario_type=ScenarioType.STRESS,
            severity=ScenarioSeverity.SEVERE,
            probability=0.1
        )

        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.10,
            description="Test parameter"
        )
        scenario.add_parameter(param)

        scenario_dict = scenario.to_dict()

        assert scenario_dict['name'] == "Test Scenario"
        assert scenario_dict['scenario_type'] == "stress"
        assert scenario_dict['severity'] == 3  # SEVERE level
        assert scenario_dict['probability'] == 0.1
        assert 'test_param' in scenario_dict['parameters']


class TestPredefinedScenarios:
    """Test predefined scenario functionality."""

    def test_base_case_scenario(self):
        """Test base case scenario creation."""
        scenario = PredefinedScenarios.base_case_scenario()

        assert scenario.name == "Base Case"
        assert scenario.scenario_type == ScenarioType.BASELINE
        assert len(scenario.parameters) > 0
        assert "revenue_growth" in scenario.parameters
        assert "discount_rate" in scenario.parameters

    def test_optimistic_scenario(self):
        """Test optimistic scenario creation."""
        scenario = PredefinedScenarios.optimistic_scenario()

        assert scenario.name == "Optimistic Case"
        assert scenario.scenario_type == ScenarioType.OPTIMISTIC
        assert scenario.probability == 0.25
        assert len(scenario.parameters) > 0

        # Check that optimistic scenario has favorable parameters
        values = scenario.generate_scenario_values()
        assert values.get("revenue_growth", 0) > 0.10  # Higher growth
        assert values.get("discount_rate", 0) < 0.10   # Lower discount rate

    def test_pessimistic_scenario(self):
        """Test pessimistic scenario creation."""
        scenario = PredefinedScenarios.pessimistic_scenario()

        assert scenario.name == "Pessimistic Case"
        assert scenario.scenario_type == ScenarioType.PESSIMISTIC
        assert scenario.probability == 0.20
        assert len(scenario.parameters) > 0

        # Check that pessimistic scenario has challenging parameters
        values = scenario.generate_scenario_values()
        assert values.get("revenue_growth", 0) < 0.05  # Lower growth
        assert values.get("discount_rate", 0) > 0.10   # Higher discount rate

    def test_historical_scenarios(self):
        """Test historical crisis scenarios."""
        scenarios = [
            PredefinedScenarios.market_crash_2008(),
            PredefinedScenarios.covid_crash_2020(),
            PredefinedScenarios.recession_scenario()
        ]

        for scenario in scenarios:
            assert scenario.scenario_type in [ScenarioType.HISTORICAL, ScenarioType.STRESS]
            assert len(scenario.parameters) > 0

            # Check that historical scenarios have severe impacts
            values = scenario.generate_scenario_values()
            if "equity_return" in values:
                assert values["equity_return"] < 0  # Negative equity returns

    def test_all_predefined_scenarios(self):
        """Test that all predefined scenarios can be created."""
        scenarios = PredefinedScenarios.all_predefined_scenarios()

        assert len(scenarios) >= 10  # Should have multiple scenarios

        scenario_names = [s.name for s in scenarios]
        expected_scenarios = [
            "Base Case",
            "Optimistic Case",
            "Pessimistic Case",
            "2008 Financial Crisis",
            "COVID-19 Pandemic"
        ]

        for expected in expected_scenarios:
            assert expected in scenario_names


class TestScenarioModelingFramework:
    """Test ScenarioModelingFramework functionality."""

    def setUp(self):
        """Set up test framework."""
        self.framework = ScenarioModelingFramework()

    def test_framework_initialization(self):
        """Test framework initialization with predefined scenarios."""
        framework = ScenarioModelingFramework()

        # Should have predefined scenarios loaded
        scenarios = framework.list_scenarios()
        assert len(scenarios) > 0
        assert "Base Case" in scenarios
        assert "Optimistic Case" in scenarios

    def test_custom_scenario_management(self):
        """Test adding and removing custom scenarios."""
        framework = ScenarioModelingFramework()

        custom_scenario = CustomScenario(
            name="Custom Test Scenario",
            description="Test scenario for framework testing"
        )

        # Add custom scenario
        framework.add_scenario(custom_scenario)
        assert "Custom Test Scenario" in framework.list_scenarios()

        # Remove custom scenario
        framework.remove_scenario("Custom Test Scenario")
        assert "Custom Test Scenario" not in framework.list_scenarios()

    def test_probability_weighted_valuation(self):
        """Test probability-weighted valuation calculation."""
        framework = ScenarioModelingFramework()

        # Define simple valuation function
        def simple_valuation(params: Dict[str, float]) -> float:
            return params.get("revenue_growth", 0.05) * 1000  # Simple scaling

        scenario_names = ["Base Case", "Optimistic Case", "Pessimistic Case"]

        result = framework.calculate_probability_weighted_valuation(
            scenario_names,
            simple_valuation,
            normalize_probabilities=True
        )

        assert "expected_value" in result
        assert "scenario_details" in result
        assert len(result["scenario_details"]) == 3
        assert result["expected_value"] > 0

        # Check that probabilities sum to 1 (approximately)
        total_prob = sum(item["probability"] for item in result["scenario_details"])
        assert abs(total_prob - 1.0) < 1e-6

    def test_three_point_scenario_generation(self):
        """Test three-point scenario generation."""
        framework = ScenarioModelingFramework()

        base_parameters = {
            "revenue_growth": 0.05,
            "discount_rate": 0.10,
            "margin": 0.20
        }

        parameter_ranges = {
            "revenue_growth": (0.0, 0.10),
            "discount_rate": (0.08, 0.12),
            "margin": (0.15, 0.25)
        }

        scenarios = framework.generate_three_point_scenarios(
            base_parameters,
            parameter_ranges
        )

        assert len(scenarios) == 3

        # Check scenario types
        scenario_types = [s.scenario_type for s in scenarios]
        assert ScenarioType.PESSIMISTIC in scenario_types
        assert ScenarioType.BASELINE in scenario_types
        assert ScenarioType.OPTIMISTIC in scenario_types

        # Check that scenarios are added to framework
        scenario_names = framework.list_scenarios()
        assert "Pessimistic" in scenario_names
        assert "Base" in scenario_names
        assert "Optimistic" in scenario_names

    def test_scenario_sensitivity_analysis(self):
        """Test scenario sensitivity analysis."""
        framework = ScenarioModelingFramework()

        def test_valuation(params: Dict[str, float]) -> float:
            return params.get("revenue_growth", 0.05) * 1000

        parameter_variations = {
            "revenue_growth": [0.0, 0.05, 0.10, 0.15, 0.20]
        }

        sensitivity_result = framework.create_scenario_sensitivity_analysis(
            "Base Case",
            parameter_variations,
            test_valuation
        )

        assert "base_scenario" in sensitivity_result
        assert "parameter_sensitivities" in sensitivity_result
        assert "revenue_growth" in sensitivity_result["parameter_sensitivities"]

        # Check elasticity calculation
        revenue_sensitivity = sensitivity_result["parameter_sensitivities"]["revenue_growth"]
        assert "elasticity" in revenue_sensitivity
        assert len(revenue_sensitivity["variations"]) == 5


class TestValuationScenarioIntegration:
    """Test integration between scenarios and valuation models."""

    def setUp(self):
        """Set up test components."""
        # Mock financial calculator
        self.mock_calculator = Mock()
        self.mock_calculator.current_price = 150.0

        # Mock valuation modules
        self.mock_dcf_valuator = Mock()
        self.mock_ddm_valuator = Mock()
        self.mock_pb_valuator = Mock()

    @patch('core.analysis.risk.valuation_scenario_integration.DCFValuator')
    @patch('core.analysis.risk.valuation_scenario_integration.DDMValuator')
    @patch('core.analysis.risk.valuation_scenario_integration.PBValuator')
    def test_integrator_initialization(self, mock_pb, mock_ddm, mock_dcf):
        """Test valuation scenario integrator initialization."""
        integrator = ValuationScenarioIntegrator(self.mock_calculator)

        assert integrator.financial_calculator == self.mock_calculator
        assert integrator.scenario_framework is not None
        mock_dcf.assert_called_once()
        mock_ddm.assert_called_once()
        mock_pb.assert_called_once()

    def test_scenario_valuation_result(self):
        """Test ScenarioValuationResult functionality."""
        scenario_values = {"Base": 100.0, "Optimistic": 120.0, "Pessimistic": 80.0}
        probabilities = {"Base": 0.5, "Optimistic": 0.25, "Pessimistic": 0.25}

        result = ScenarioValuationResult(
            expected_value=100.0,
            scenario_values=scenario_values,
            probabilities=probabilities,
            confidence_intervals={'95%': (85.0, 115.0), '90%': (88.0, 112.0)},
            valuation_method="dcf"
        )

        assert result.expected_value == 100.0
        assert result.confidence_interval_95 == (85.0, 115.0)
        assert result.confidence_interval_90 == (88.0, 112.0)
        assert result.downside_risk == 12.0  # 100 - 88
        assert result.upside_potential == 12.0  # 112 - 100
        assert result.valuation_method == "dcf"

        # Test serialization
        result_dict = result.to_dict()
        assert "expected_value" in result_dict
        assert "scenario_values" in result_dict
        assert "downside_risk" in result_dict

    @patch('core.analysis.risk.valuation_scenario_integration.DCFValuator')
    def test_dcf_scenario_analysis_integration(self, mock_dcf_class):
        """Test DCF scenario analysis integration."""
        # Mock DCF valuator
        mock_dcf_instance = Mock()
        mock_dcf_instance.calculate_dcf_projections.return_value = {'value_per_share': 100.0}
        mock_dcf_class.return_value = mock_dcf_instance

        integrator = ValuationScenarioIntegrator(self.mock_calculator)

        # Mock scenario framework to return test scenarios
        integrator.scenario_framework.scenarios = {
            'Base Case': Mock(),
            'Optimistic Case': Mock(),
            'Pessimistic Case': Mock()
        }

        # Mock scenario value generation
        for scenario_name, scenario in integrator.scenario_framework.scenarios.items():
            scenario.generate_scenario_values.return_value = {
                'revenue_growth': 0.05,
                'discount_rate': 0.10,
                'terminal_growth': 0.03,
                'operating_margin': 0.20
            }
            scenario.probability = 0.33

        with patch.object(integrator.scenario_framework, 'calculate_probability_weighted_valuation') as mock_calc:
            mock_calc.return_value = {
                'expected_value': 100.0,
                'scenario_details': [
                    {'name': 'Base Case', 'valuation': 100.0, 'probability': 0.33},
                    {'name': 'Optimistic Case', 'valuation': 120.0, 'probability': 0.33},
                    {'name': 'Pessimistic Case', 'valuation': 80.0, 'probability': 0.34}
                ]
            }

            result = integrator.run_scenario_dcf_analysis(['Base Case', 'Optimistic Case', 'Pessimistic Case'])

            assert isinstance(result, ScenarioValuationResult)
            assert result.expected_value == 100.0
            assert result.valuation_method == "dcf"
            assert len(result.scenario_values) == 3


class TestConvenienceFunctions:
    """Test convenience functions for quick analysis."""

    @patch('core.analysis.risk.valuation_scenario_integration.ValuationScenarioIntegrator')
    def test_quick_three_point_dcf_analysis(self, mock_integrator_class):
        """Test quick three-point DCF analysis function."""
        mock_calculator = Mock()

        # Mock integrator and its methods
        mock_integrator = Mock()
        mock_integrator_class.return_value = mock_integrator

        mock_result = ScenarioValuationResult(
            expected_value=100.0,
            scenario_values={'Pessimistic': 80.0, 'Base': 100.0, 'Optimistic': 120.0},
            probabilities={'Pessimistic': 0.25, 'Base': 0.5, 'Optimistic': 0.25},
            valuation_method="dcf"
        )
        mock_integrator.create_custom_three_point_analysis.return_value = mock_result

        result = quick_three_point_dcf_analysis(mock_calculator)

        assert isinstance(result, ScenarioValuationResult)
        assert result.expected_value == 100.0
        mock_integrator.create_custom_three_point_analysis.assert_called_once()

    @patch('core.analysis.risk.valuation_scenario_integration.ValuationScenarioIntegrator')
    def test_economic_scenario_dcf_analysis(self, mock_integrator_class):
        """Test economic scenario DCF analysis function."""
        mock_calculator = Mock()

        # Mock integrator and its methods
        mock_integrator = Mock()
        mock_integrator_class.return_value = mock_integrator

        mock_result = ScenarioValuationResult(
            expected_value=105.0,
            scenario_values={
                'Base Case': 100.0,
                'Optimistic Case': 120.0,
                'Pessimistic Case': 80.0,
                'Economic Expansion': 130.0,
                'Recession': 70.0
            },
            probabilities={
                'Base Case': 0.3,
                'Optimistic Case': 0.2,
                'Pessimistic Case': 0.2,
                'Economic Expansion': 0.15,
                'Recession': 0.15
            },
            valuation_method="dcf"
        )
        mock_integrator.run_scenario_dcf_analysis.return_value = mock_result

        result = create_economic_scenario_dcf_analysis(mock_calculator)

        assert isinstance(result, ScenarioValuationResult)
        assert result.expected_value == 105.0
        mock_integrator.run_scenario_dcf_analysis.assert_called_once()


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""

    def test_large_scenario_set_performance(self):
        """Test performance with large number of scenarios."""
        framework = ScenarioModelingFramework()

        # Create many custom scenarios
        for i in range(100):
            scenario = CustomScenario(
                name=f"Scenario_{i}",
                description=f"Test scenario {i}",
                probability=0.01
            )
            scenario.add_parameter(ScenarioParameter(
                name="test_param",
                variable_type="rate",
                base_value=0.05,
                shock_value=0.05 + i * 0.001
            ))
            framework.add_scenario(scenario)

        # Test that large scenario set doesn't cause performance issues
        scenario_names = framework.list_scenarios()
        assert len(scenario_names) >= 100

        # Test probability weighted calculation with many scenarios
        def simple_valuation(params):
            return params.get("test_param", 0.05) * 1000

        result = framework.calculate_probability_weighted_valuation(
            scenario_names[-50:],  # Use last 50 scenarios
            simple_valuation
        )

        assert "expected_value" in result
        assert len(result["scenario_details"]) == 50

    def test_missing_scenario_handling(self):
        """Test handling of missing scenarios."""
        framework = ScenarioModelingFramework()

        def simple_valuation(params):
            return 100.0

        # Test with non-existent scenario
        result = framework.calculate_probability_weighted_valuation(
            ["Non-existent Scenario"],
            simple_valuation
        )

        # Should handle gracefully
        assert result["num_scenarios"] == 0

    def test_invalid_parameter_values(self):
        """Test handling of invalid parameter values."""
        param = ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=None  # No shock value
        )

        # Should return base value when no shock
        result = param.apply_shock()
        assert result == 0.05

    def test_zero_probability_scenarios(self):
        """Test handling of scenarios with zero probability."""
        framework = ScenarioModelingFramework()

        scenario = CustomScenario(
            name="Zero Prob Scenario",
            description="Scenario with zero probability",
            probability=0.0
        )
        scenario.add_parameter(ScenarioParameter(
            name="test_param",
            variable_type="rate",
            base_value=0.05,
            shock_value=0.10
        ))

        framework.add_scenario(scenario)

        def simple_valuation(params):
            return 100.0

        result = framework.calculate_probability_weighted_valuation(
            ["Zero Prob Scenario", "Base Case"],
            simple_valuation
        )

        # Should handle zero probability correctly
        assert result["expected_value"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])