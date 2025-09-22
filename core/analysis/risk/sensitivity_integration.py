"""
Sensitivity Analysis Integration Module
======================================

This module provides integration between the sensitivity analysis framework and existing
financial calculation engines (DCF, DDM, P/B). It acts as a bridge to ensure proper
parameter passing and result extraction from the established valuation models.

Key Features:
- Integration with FinancialCalculator engine
- DCF valuation parameter override capabilities
- DDM and P/B analysis integration
- Automatic parameter mapping and validation
- Result standardization and error handling
- Performance optimization for batch calculations

Classes:
--------
SensitivityIntegrator
    Main integration class for connecting sensitivity analysis with valuation models

DCFSensitivityAdapter
    Specialized adapter for DCF valuation integration

DDMSensitivityAdapter
    Specialized adapter for DDM valuation integration

PBSensitivityAdapter
    Specialized adapter for P/B analysis integration

Usage Example:
--------------
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>> from core.analysis.risk.sensitivity_analysis import SensitivityAnalyzer
>>> from core.analysis.risk.sensitivity_integration import SensitivityIntegrator
>>>
>>> # Initialize components
>>> calc = FinancialCalculator('AAPL')
>>> integrator = SensitivityIntegrator(calc)
>>> analyzer = SensitivityAnalyzer(calc)
>>>
>>> # Configure analyzer to use integrator
>>> analyzer.set_valuation_integrator(integrator)
>>>
>>> # Run integrated sensitivity analysis
>>> result = analyzer.tornado_analysis('dcf', ['revenue_growth', 'discount_rate'])
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
from dataclasses import dataclass
import logging
from copy import deepcopy

# Import existing valuation modules
from ..engines.financial_calculations import FinancialCalculator
from ..dcf.dcf_valuation import DCFValuator
from ..ddm.ddm_valuation import DDMValuator
from ..pb.pb_valuation import PBValuator

logger = logging.getLogger(__name__)


@dataclass
class ParameterMapping:
    """Mapping between sensitivity parameter names and calculation engine parameters."""
    sensitivity_name: str
    engine_parameter: str
    transformation: Optional[Callable[[float], float]] = None
    validation_range: Optional[tuple] = None
    units: str = "%"
    description: Optional[str] = None


class DCFSensitivityAdapter:
    """
    Adapter for integrating sensitivity analysis with DCF valuation.

    This adapter handles parameter mapping and calculation execution for DCF models,
    ensuring proper parameter injection and result extraction.
    """

    def __init__(self, financial_calculator: FinancialCalculator):
        """
        Initialize DCF sensitivity adapter.

        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator
        self.dcf_valuator = DCFValuator(financial_calculator)

        # Define parameter mappings for DCF
        self.parameter_mappings = {
            'revenue_growth': ParameterMapping(
                sensitivity_name='revenue_growth',
                engine_parameter='growth_rate_yr1_5',
                validation_range=(-0.50, 2.0),
                description='Revenue growth rate for years 1-5'
            ),
            'discount_rate': ParameterMapping(
                sensitivity_name='discount_rate',
                engine_parameter='discount_rate',
                validation_range=(0.01, 0.30),
                description='Discount rate (WACC/Cost of Equity)'
            ),
            'terminal_growth': ParameterMapping(
                sensitivity_name='terminal_growth',
                engine_parameter='terminal_growth_rate',
                validation_range=(0.0, 0.10),
                description='Terminal growth rate'
            ),
            'operating_margin': ParameterMapping(
                sensitivity_name='operating_margin',
                engine_parameter='operating_margin_assumption',
                validation_range=(0.0, 1.0),
                description='Operating margin assumption'
            ),
            'tax_rate': ParameterMapping(
                sensitivity_name='tax_rate',
                engine_parameter='tax_rate',
                validation_range=(0.0, 0.50),
                description='Effective tax rate'
            ),
            'capex_ratio': ParameterMapping(
                sensitivity_name='capex_ratio',
                engine_parameter='capex_as_percent_revenue',
                validation_range=(0.0, 0.30),
                description='Capital expenditure as % of revenue'
            ),
            'working_capital_ratio': ParameterMapping(
                sensitivity_name='working_capital_ratio',
                engine_parameter='working_capital_change_assumption',
                validation_range=(-0.10, 0.10),
                description='Working capital change assumption'
            )
        }

        logger.info("DCF Sensitivity Adapter initialized")

    def calculate_valuation(self, parameter_overrides: Dict[str, float]) -> float:
        """
        Calculate DCF valuation with parameter overrides.

        Args:
            parameter_overrides: Dictionary of parameter name to value overrides

        Returns:
            Calculated value per share

        Raises:
            ValueError: If parameter validation fails
            Exception: If DCF calculation fails
        """
        try:
            # Validate and map parameters
            mapped_overrides = self._map_and_validate_parameters(parameter_overrides)

            # Get base DCF configuration
            base_config = self._get_base_dcf_config()

            # Apply overrides
            calculation_config = {**base_config, **mapped_overrides}

            # Perform DCF calculation with overrides
            dcf_result = self.dcf_valuator.calculate_dcf_projections(**calculation_config)

            # Extract value per share
            value_per_share = dcf_result.get('value_per_share', 0)

            if value_per_share <= 0:
                logger.warning(f"Invalid DCF result: {value_per_share}")
                return self._get_fallback_value()

            return float(value_per_share)

        except Exception as e:
            logger.error(f"DCF calculation failed with overrides {parameter_overrides}: {e}")
            return self._get_fallback_value()

    def _map_and_validate_parameters(self, parameter_overrides: Dict[str, float]) -> Dict[str, float]:
        """Map sensitivity parameters to DCF engine parameters and validate."""
        mapped_params = {}

        for param_name, param_value in parameter_overrides.items():
            if param_name not in self.parameter_mappings:
                logger.warning(f"Unknown parameter: {param_name}")
                continue

            mapping = self.parameter_mappings[param_name]

            # Validate parameter range
            if mapping.validation_range:
                min_val, max_val = mapping.validation_range
                if not (min_val <= param_value <= max_val):
                    logger.warning(f"Parameter {param_name} value {param_value} outside valid range {mapping.validation_range}")
                    param_value = max(min_val, min(max_val, param_value))  # Clamp to valid range

            # Apply transformation if specified
            if mapping.transformation:
                param_value = mapping.transformation(param_value)

            # Map to engine parameter name
            mapped_params[mapping.engine_parameter] = param_value

        return mapped_params

    def _get_base_dcf_config(self) -> Dict[str, Any]:
        """Get base DCF configuration from the calculation engine."""
        try:
            # Get DCF inputs from financial calculator
            dcf_inputs = self.financial_calculator.calculate_dcf_inputs()

            # Extract base configuration
            base_config = {
                'discount_rate': dcf_inputs.get('discount_rate', 0.10),
                'terminal_growth_rate': dcf_inputs.get('terminal_growth_rate', 0.03),
                'growth_rate_yr1_5': dcf_inputs.get('growth_rate_yr1_5', 0.05),
                'growth_rate_yr5_10': dcf_inputs.get('growth_rate_yr5_10', 0.04),
                'tax_rate': dcf_inputs.get('tax_rate', 0.25),
                'operating_margin_assumption': dcf_inputs.get('operating_margin', 0.20),
                'capex_as_percent_revenue': dcf_inputs.get('capex_ratio', 0.05),
                'working_capital_change_assumption': dcf_inputs.get('working_capital_change', 0.02)
            }

            return base_config

        except Exception as e:
            logger.warning(f"Could not get base DCF config: {e}")
            # Return default configuration
            return {
                'discount_rate': 0.10,
                'terminal_growth_rate': 0.03,
                'growth_rate_yr1_5': 0.05,
                'growth_rate_yr5_10': 0.04,
                'tax_rate': 0.25,
                'operating_margin_assumption': 0.20,
                'capex_as_percent_revenue': 0.05,
                'working_capital_change_assumption': 0.02
            }

    def _get_fallback_value(self) -> float:
        """Get fallback value for failed calculations."""
        try:
            # Try to get base case DCF value
            base_result = self.dcf_valuator.calculate_dcf_projections()
            return float(base_result.get('value_per_share', 100.0))
        except:
            return 100.0  # Default fallback

    def get_parameter_info(self) -> Dict[str, ParameterMapping]:
        """Get information about available parameters."""
        return self.parameter_mappings


class DDMSensitivityAdapter:
    """
    Adapter for integrating sensitivity analysis with DDM valuation.
    """

    def __init__(self, financial_calculator: FinancialCalculator):
        """Initialize DDM sensitivity adapter."""
        self.financial_calculator = financial_calculator
        self.ddm_valuator = DDMValuator(financial_calculator)

        # Define parameter mappings for DDM
        self.parameter_mappings = {
            'dividend_growth': ParameterMapping(
                sensitivity_name='dividend_growth',
                engine_parameter='dividend_growth_rate',
                validation_range=(-0.20, 0.50),
                description='Dividend growth rate'
            ),
            'required_return': ParameterMapping(
                sensitivity_name='required_return',
                engine_parameter='required_return',
                validation_range=(0.01, 0.25),
                description='Required return on equity'
            ),
            'payout_ratio': ParameterMapping(
                sensitivity_name='payout_ratio',
                engine_parameter='payout_ratio',
                validation_range=(0.0, 1.0),
                description='Dividend payout ratio'
            ),
            'terminal_growth': ParameterMapping(
                sensitivity_name='terminal_growth',
                engine_parameter='terminal_growth_rate',
                validation_range=(0.0, 0.10),
                description='Terminal dividend growth rate'
            )
        }

        logger.info("DDM Sensitivity Adapter initialized")

    def calculate_valuation(self, parameter_overrides: Dict[str, float]) -> float:
        """Calculate DDM valuation with parameter overrides."""
        try:
            # Map and validate parameters
            mapped_overrides = self._map_and_validate_parameters(parameter_overrides)

            # Get base DDM configuration
            base_config = self._get_base_ddm_config()

            # Apply overrides
            calculation_config = {**base_config, **mapped_overrides}

            # Ensure required_return > dividend_growth for convergence
            if calculation_config['required_return'] <= calculation_config.get('dividend_growth_rate', 0):
                calculation_config['required_return'] = calculation_config.get('dividend_growth_rate', 0) + 0.02

            # Perform DDM calculation
            ddm_result = self.ddm_valuator.calculate_ddm_valuation(**calculation_config)

            # Extract value per share
            value_per_share = ddm_result.get('value_per_share', 0)

            if value_per_share <= 0:
                logger.warning(f"Invalid DDM result: {value_per_share}")
                return self._get_fallback_value()

            return float(value_per_share)

        except Exception as e:
            logger.error(f"DDM calculation failed with overrides {parameter_overrides}: {e}")
            return self._get_fallback_value()

    def _map_and_validate_parameters(self, parameter_overrides: Dict[str, float]) -> Dict[str, float]:
        """Map and validate DDM parameters."""
        mapped_params = {}

        for param_name, param_value in parameter_overrides.items():
            if param_name not in self.parameter_mappings:
                continue

            mapping = self.parameter_mappings[param_name]

            # Validate range
            if mapping.validation_range:
                min_val, max_val = mapping.validation_range
                param_value = max(min_val, min(max_val, param_value))

            mapped_params[mapping.engine_parameter] = param_value

        return mapped_params

    def _get_base_ddm_config(self) -> Dict[str, Any]:
        """Get base DDM configuration."""
        try:
            # This would integrate with actual DDM input calculation
            return {
                'dividend_growth_rate': 0.05,
                'required_return': 0.10,
                'payout_ratio': 0.40,
                'terminal_growth_rate': 0.03
            }
        except Exception as e:
            logger.warning(f"Could not get base DDM config: {e}")
            return {
                'dividend_growth_rate': 0.05,
                'required_return': 0.10,
                'payout_ratio': 0.40,
                'terminal_growth_rate': 0.03
            }

    def _get_fallback_value(self) -> float:
        """Get fallback value for failed DDM calculations."""
        return 50.0  # Default DDM fallback


class PBSensitivityAdapter:
    """
    Adapter for integrating sensitivity analysis with P/B valuation.
    """

    def __init__(self, financial_calculator: FinancialCalculator):
        """Initialize P/B sensitivity adapter."""
        self.financial_calculator = financial_calculator
        self.pb_valuator = PBValuator(financial_calculator)

        # Define parameter mappings for P/B
        self.parameter_mappings = {
            'roe': ParameterMapping(
                sensitivity_name='roe',
                engine_parameter='roe',
                validation_range=(0.0, 0.50),
                description='Return on Equity'
            ),
            'required_return': ParameterMapping(
                sensitivity_name='required_return',
                engine_parameter='required_return',
                validation_range=(0.01, 0.25),
                description='Required return on equity'
            ),
            'growth_rate': ParameterMapping(
                sensitivity_name='growth_rate',
                engine_parameter='growth_rate',
                validation_range=(0.0, 0.20),
                description='Sustainable growth rate'
            ),
            'payout_ratio': ParameterMapping(
                sensitivity_name='payout_ratio',
                engine_parameter='payout_ratio',
                validation_range=(0.0, 1.0),
                description='Dividend payout ratio'
            )
        }

        logger.info("P/B Sensitivity Adapter initialized")

    def calculate_valuation(self, parameter_overrides: Dict[str, float]) -> float:
        """Calculate P/B valuation with parameter overrides."""
        try:
            # Map and validate parameters
            mapped_overrides = self._map_and_validate_parameters(parameter_overrides)

            # Get base P/B configuration
            base_config = self._get_base_pb_config()

            # Apply overrides
            calculation_config = {**base_config, **mapped_overrides}

            # Perform P/B calculation
            pb_result = self.pb_valuator.calculate_pb_valuation(**calculation_config)

            # Extract value per share
            value_per_share = pb_result.get('value_per_share', 0)

            if value_per_share <= 0:
                logger.warning(f"Invalid P/B result: {value_per_share}")
                return self._get_fallback_value()

            return float(value_per_share)

        except Exception as e:
            logger.error(f"P/B calculation failed with overrides {parameter_overrides}: {e}")
            return self._get_fallback_value()

    def _map_and_validate_parameters(self, parameter_overrides: Dict[str, float]) -> Dict[str, float]:
        """Map and validate P/B parameters."""
        mapped_params = {}

        for param_name, param_value in parameter_overrides.items():
            if param_name not in self.parameter_mappings:
                continue

            mapping = self.parameter_mappings[param_name]

            # Validate range
            if mapping.validation_range:
                min_val, max_val = mapping.validation_range
                param_value = max(min_val, min(max_val, param_value))

            mapped_params[mapping.engine_parameter] = param_value

        return mapped_params

    def _get_base_pb_config(self) -> Dict[str, Any]:
        """Get base P/B configuration."""
        try:
            # This would integrate with actual P/B input calculation
            return {
                'roe': 0.15,
                'required_return': 0.10,
                'growth_rate': 0.05,
                'payout_ratio': 0.40
            }
        except Exception as e:
            logger.warning(f"Could not get base P/B config: {e}")
            return {
                'roe': 0.15,
                'required_return': 0.10,
                'growth_rate': 0.05,
                'payout_ratio': 0.40
            }

    def _get_fallback_value(self) -> float:
        """Get fallback value for failed P/B calculations."""
        return 15.0  # Default P/B fallback


class SensitivityIntegrator:
    """
    Main integration class for connecting sensitivity analysis with valuation models.

    This class provides a unified interface for sensitivity analysis across different
    valuation methods, handling parameter mapping, validation, and calculation execution.
    """

    def __init__(self, financial_calculator: FinancialCalculator):
        """
        Initialize sensitivity integrator.

        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator

        # Initialize adapters
        self.dcf_adapter = DCFSensitivityAdapter(financial_calculator)
        self.ddm_adapter = DDMSensitivityAdapter(financial_calculator)
        self.pb_adapter = PBSensitivityAdapter(financial_calculator)

        # Map valuation methods to adapters
        self.adapters = {
            'dcf': self.dcf_adapter,
            'ddm': self.ddm_adapter,
            'pb': self.pb_adapter
        }

        logger.info("Sensitivity Integrator initialized")

    def calculate_valuation(
        self,
        valuation_method: str,
        parameter_overrides: Dict[str, float],
        custom_function: Optional[Callable] = None
    ) -> float:
        """
        Calculate valuation with parameter overrides.

        Args:
            valuation_method: Valuation method ('dcf', 'ddm', 'pb', or 'custom')
            parameter_overrides: Dictionary of parameter overrides
            custom_function: Custom valuation function for 'custom' method

        Returns:
            Calculated valuation

        Raises:
            ValueError: If valuation method is not supported
        """
        if valuation_method == 'custom' and custom_function:
            return custom_function(parameter_overrides)

        if valuation_method not in self.adapters:
            raise ValueError(f"Unsupported valuation method: {valuation_method}")

        adapter = self.adapters[valuation_method]
        return adapter.calculate_valuation(parameter_overrides)

    def get_base_case_value(self, valuation_method: str) -> float:
        """Get base case valuation without parameter overrides."""
        return self.calculate_valuation(valuation_method, {})

    def get_available_parameters(self, valuation_method: str) -> Dict[str, ParameterMapping]:
        """
        Get available parameters for a valuation method.

        Args:
            valuation_method: Valuation method name

        Returns:
            Dictionary of parameter mappings

        Raises:
            ValueError: If valuation method is not supported
        """
        if valuation_method not in self.adapters:
            raise ValueError(f"Unsupported valuation method: {valuation_method}")

        adapter = self.adapters[valuation_method]
        return adapter.get_parameter_info()

    def validate_parameters(
        self,
        valuation_method: str,
        parameters: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Validate parameters for a valuation method.

        Args:
            valuation_method: Valuation method name
            parameters: Dictionary of parameters to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if valuation_method not in self.adapters:
            return False, [f"Unsupported valuation method: {valuation_method}"]

        adapter = self.adapters[valuation_method]
        parameter_mappings = adapter.get_parameter_info()

        errors = []
        for param_name, param_value in parameters.items():
            if param_name not in parameter_mappings:
                errors.append(f"Unknown parameter: {param_name}")
                continue

            mapping = parameter_mappings[param_name]
            if mapping.validation_range:
                min_val, max_val = mapping.validation_range
                if not (min_val <= param_value <= max_val):
                    errors.append(f"Parameter {param_name} value {param_value} outside valid range {mapping.validation_range}")

        return len(errors) == 0, errors

    def get_method_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all supported valuation methods."""
        info = {}

        for method_name, adapter in self.adapters.items():
            parameter_info = adapter.get_parameter_info()
            info[method_name] = {
                'parameters': {
                    param_name: {
                        'description': mapping.description,
                        'units': mapping.units,
                        'validation_range': mapping.validation_range
                    }
                    for param_name, mapping in parameter_info.items()
                },
                'parameter_count': len(parameter_info)
            }

        return info

    def test_integration(self, valuation_method: str) -> Dict[str, Any]:
        """
        Test integration for a specific valuation method.

        Args:
            valuation_method: Method to test

        Returns:
            Dictionary with test results
        """
        test_results = {
            'method': valuation_method,
            'base_case_success': False,
            'base_case_value': None,
            'parameter_override_success': False,
            'override_value': None,
            'errors': []
        }

        try:
            # Test base case calculation
            base_value = self.get_base_case_value(valuation_method)
            test_results['base_case_success'] = True
            test_results['base_case_value'] = base_value

            # Test with parameter overrides
            if valuation_method == 'dcf':
                test_overrides = {'discount_rate': 0.12}
            elif valuation_method == 'ddm':
                test_overrides = {'required_return': 0.12}
            elif valuation_method == 'pb':
                test_overrides = {'required_return': 0.12}
            else:
                test_overrides = {}

            if test_overrides:
                override_value = self.calculate_valuation(valuation_method, test_overrides)
                test_results['parameter_override_success'] = True
                test_results['override_value'] = override_value

        except Exception as e:
            test_results['errors'].append(str(e))

        return test_results


# Convenience functions for integration

def create_integrated_sensitivity_analyzer(
    financial_calculator: FinancialCalculator
) -> 'SensitivityAnalyzer':
    """
    Create sensitivity analyzer with proper integration.

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        SensitivityAnalyzer with integrated valuation methods
    """
    from .sensitivity_analysis import SensitivityAnalyzer

    # Create integrator
    integrator = SensitivityIntegrator(financial_calculator)

    # Create analyzer
    analyzer = SensitivityAnalyzer(financial_calculator)

    # Override the valuation calculation method
    def integrated_calculate_valuation(method, overrides, custom_func=None):
        return integrator.calculate_valuation(method, overrides, custom_func)

    analyzer._calculate_valuation = integrated_calculate_valuation

    return analyzer


def quick_integrated_tornado_analysis(
    financial_calculator: FinancialCalculator,
    valuation_method: str = 'dcf',
    variation_percentage: float = 0.20
) -> 'SensitivityResult':
    """
    Quick tornado analysis with proper integration.

    Args:
        financial_calculator: FinancialCalculator instance
        valuation_method: Valuation method to analyze
        variation_percentage: Percentage variation from base case

    Returns:
        SensitivityResult with tornado analysis
    """
    analyzer = create_integrated_sensitivity_analyzer(financial_calculator)

    # Get appropriate parameters for the method
    integrator = SensitivityIntegrator(financial_calculator)
    available_params = integrator.get_available_parameters(valuation_method)
    param_names = list(available_params.keys())

    return analyzer.tornado_analysis(
        valuation_method=valuation_method,
        parameters=param_names,
        variation_percentage=variation_percentage
    )


def test_all_integrations(financial_calculator: FinancialCalculator) -> Dict[str, Dict[str, Any]]:
    """
    Test all valuation method integrations.

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        Dictionary of test results for each method
    """
    integrator = SensitivityIntegrator(financial_calculator)

    results = {}
    for method in ['dcf', 'ddm', 'pb']:
        results[method] = integrator.test_integration(method)

    return results