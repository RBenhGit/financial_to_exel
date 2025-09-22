"""
Valuation-Scenario Integration Module
===================================

This module provides integration between scenario modeling and existing valuation frameworks.
It enables scenario-based valuation analysis using DCF, DDM, and P/B models with the
scenario modeling system for comprehensive risk assessment.

Key Features:
- Integration with existing FinancialCalculator and valuation modules
- Scenario-based DCF, DDM, and P/B valuations
- Probability-weighted expected values across scenarios
- Valuation sensitivity analysis using scenario parameters
- Three-point scenario analysis (pessimistic/base/optimistic)
- Integration with Monte Carlo engine for combined analysis

Classes:
--------
ValuationScenarioIntegrator
    Main integration class connecting scenarios with valuation models

ScenarioValuationResult
    Container for scenario-based valuation results

Usage Example:
-------------
>>> from core.analysis.risk.valuation_scenario_integration import ValuationScenarioIntegrator
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>> from core.analysis.risk.scenario_modeling import ScenarioModelingFramework
>>>
>>> # Initialize components
>>> calc = FinancialCalculator('AAPL')
>>> framework = ScenarioModelingFramework()
>>> integrator = ValuationScenarioIntegrator(calc, framework)
>>>
>>> # Run scenario-based DCF analysis
>>> scenarios = ['Base Case', 'Optimistic Case', 'Pessimistic Case']
>>> result = integrator.run_scenario_dcf_analysis(scenarios)
>>> print(f"Expected DCF Value: ${result.expected_value:.2f}")
>>> print(f"95% Confidence Range: ${result.confidence_interval_95[0]:.2f} - ${result.confidence_interval_95[1]:.2f}")
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# Import valuation modules
from ..engines.financial_calculations import FinancialCalculator
from ..dcf.dcf_valuation import DCFValuator
from ..ddm.ddm_valuation import DDMValuator
from ..pb.pb_valuation import PBValuator

# Import scenario modeling
from .scenario_modeling import ScenarioModelingFramework, CustomScenario, ScenarioParameter
from ..statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult

logger = logging.getLogger(__name__)


@dataclass
class ScenarioValuationResult:
    """
    Container for scenario-based valuation analysis results.

    Attributes:
        expected_value: Probability-weighted expected valuation
        scenario_values: Individual scenario valuations
        confidence_intervals: Statistical confidence intervals
        risk_metrics: Risk assessment metrics
        sensitivity_analysis: Parameter sensitivity results
    """
    expected_value: float
    scenario_values: Dict[str, float]
    probabilities: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    valuation_method: str = "dcf"
    calculation_date: datetime = field(default_factory=datetime.now)

    @property
    def confidence_interval_95(self) -> Tuple[float, float]:
        """Get 95% confidence interval."""
        return self.confidence_intervals.get('95%', (0, 0))

    @property
    def confidence_interval_90(self) -> Tuple[float, float]:
        """Get 90% confidence interval."""
        return self.confidence_intervals.get('90%', (0, 0))

    @property
    def downside_risk(self) -> float:
        """Calculate downside risk (expected value - 5th percentile)."""
        ci_90 = self.confidence_interval_90
        return self.expected_value - ci_90[0] if ci_90[0] != 0 else 0

    @property
    def upside_potential(self) -> float:
        """Calculate upside potential (95th percentile - expected value)."""
        ci_90 = self.confidence_interval_90
        return ci_90[1] - self.expected_value if ci_90[1] != 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'expected_value': self.expected_value,
            'scenario_values': self.scenario_values,
            'probabilities': self.probabilities,
            'confidence_intervals': self.confidence_intervals,
            'risk_metrics': self.risk_metrics,
            'valuation_method': self.valuation_method,
            'calculation_date': self.calculation_date.isoformat(),
            'downside_risk': self.downside_risk,
            'upside_potential': self.upside_potential
        }


class ValuationScenarioIntegrator:
    """
    Integrates scenario modeling with existing valuation frameworks.

    This class provides comprehensive scenario-based valuation analysis
    by connecting the scenario modeling system with DCF, DDM, and P/B
    valuation methods.
    """

    def __init__(
        self,
        financial_calculator: FinancialCalculator,
        scenario_framework: Optional[ScenarioModelingFramework] = None
    ):
        """
        Initialize valuation scenario integrator.

        Args:
            financial_calculator: FinancialCalculator instance for data access
            scenario_framework: ScenarioModelingFramework instance (creates new if None)
        """
        self.financial_calculator = financial_calculator
        self.scenario_framework = scenario_framework or ScenarioModelingFramework()

        # Initialize valuation modules
        self.dcf_valuator = DCFValuator(financial_calculator)
        self.ddm_valuator = DDMValuator(financial_calculator)
        self.pb_valuator = PBValuator(financial_calculator)
        self.monte_carlo_engine = MonteCarloEngine(financial_calculator)

        logger.info("Valuation Scenario Integrator initialized")

    def run_scenario_dcf_analysis(
        self,
        scenario_names: List[str],
        normalize_probabilities: bool = True
    ) -> ScenarioValuationResult:
        """
        Run DCF valuation analysis across multiple scenarios.

        Args:
            scenario_names: List of scenario names to analyze
            normalize_probabilities: Whether to normalize scenario probabilities

        Returns:
            ScenarioValuationResult with DCF analysis results
        """
        logger.info(f"Running scenario DCF analysis for {len(scenario_names)} scenarios")

        def dcf_valuation_function(scenario_params: Dict[str, float]) -> float:
            """Calculate DCF value with scenario parameters."""
            try:
                # Create temporary DCF parameters
                dcf_params = {
                    'discount_rate': scenario_params.get('discount_rate', 0.10),
                    'terminal_growth_rate': scenario_params.get('terminal_growth', 0.03),
                    'revenue_growth_rate': scenario_params.get('revenue_growth', 0.05),
                    'operating_margin': scenario_params.get('operating_margin', 0.20)
                }

                # Use existing DCF module with scenario parameters
                result = self.dcf_valuator.calculate_dcf_projections(**dcf_params)
                return result.get('value_per_share', 0)

            except Exception as e:
                logger.debug(f"DCF calculation failed with scenario params: {e}")
                return 0

        # Calculate probability-weighted valuation
        weighted_result = self.scenario_framework.calculate_probability_weighted_valuation(
            scenario_names,
            dcf_valuation_function,
            normalize_probabilities
        )

        # Extract scenario values and probabilities
        scenario_values = {
            item['name']: item['valuation']
            for item in weighted_result['scenario_details']
        }
        probabilities = {
            item['name']: item['probability']
            for item in weighted_result['scenario_details']
        }

        # Calculate confidence intervals and risk metrics
        confidence_intervals = self._calculate_confidence_intervals(weighted_result)
        risk_metrics = self._calculate_risk_metrics(weighted_result)

        return ScenarioValuationResult(
            expected_value=weighted_result['expected_value'],
            scenario_values=scenario_values,
            probabilities=probabilities,
            confidence_intervals=confidence_intervals,
            risk_metrics=risk_metrics,
            valuation_method="dcf"
        )

    def run_scenario_ddm_analysis(
        self,
        scenario_names: List[str],
        normalize_probabilities: bool = True
    ) -> ScenarioValuationResult:
        """
        Run DDM valuation analysis across multiple scenarios.

        Args:
            scenario_names: List of scenario names to analyze
            normalize_probabilities: Whether to normalize scenario probabilities

        Returns:
            ScenarioValuationResult with DDM analysis results
        """
        logger.info(f"Running scenario DDM analysis for {len(scenario_names)} scenarios")

        def ddm_valuation_function(scenario_params: Dict[str, float]) -> float:
            """Calculate DDM value with scenario parameters."""
            try:
                # Extract DDM-specific parameters
                dividend_growth_rate = scenario_params.get('dividend_growth', 0.05)
                required_return = scenario_params.get('required_return', 0.10)
                payout_ratio = scenario_params.get('payout_ratio', 0.40)

                # Use existing DDM module with scenario parameters
                result = self.ddm_valuator.calculate_ddm_valuation(
                    dividend_growth_rate=dividend_growth_rate,
                    required_return=required_return,
                    payout_ratio=payout_ratio
                )
                return result.get('intrinsic_value', 0)

            except Exception as e:
                logger.debug(f"DDM calculation failed with scenario params: {e}")
                return 0

        # Calculate probability-weighted valuation
        weighted_result = self.scenario_framework.calculate_probability_weighted_valuation(
            scenario_names,
            ddm_valuation_function,
            normalize_probabilities
        )

        # Extract results
        scenario_values = {
            item['name']: item['valuation']
            for item in weighted_result['scenario_details']
        }
        probabilities = {
            item['name']: item['probability']
            for item in weighted_result['scenario_details']
        }

        # Calculate confidence intervals and risk metrics
        confidence_intervals = self._calculate_confidence_intervals(weighted_result)
        risk_metrics = self._calculate_risk_metrics(weighted_result)

        return ScenarioValuationResult(
            expected_value=weighted_result['expected_value'],
            scenario_values=scenario_values,
            probabilities=probabilities,
            confidence_intervals=confidence_intervals,
            risk_metrics=risk_metrics,
            valuation_method="ddm"
        )

    def run_scenario_pb_analysis(
        self,
        scenario_names: List[str],
        normalize_probabilities: bool = True
    ) -> ScenarioValuationResult:
        """
        Run P/B valuation analysis across multiple scenarios.

        Args:
            scenario_names: List of scenario names to analyze
            normalize_probabilities: Whether to normalize scenario probabilities

        Returns:
            ScenarioValuationResult with P/B analysis results
        """
        logger.info(f"Running scenario P/B analysis for {len(scenario_names)} scenarios")

        def pb_valuation_function(scenario_params: Dict[str, float]) -> float:
            """Calculate P/B value with scenario parameters."""
            try:
                # Extract P/B-specific parameters
                pb_multiple = scenario_params.get('pb_multiple', 2.0)
                roe_adjustment = scenario_params.get('roe_adjustment', 1.0)

                # Use existing P/B module with scenario parameters
                result = self.pb_valuator.calculate_pb_valuation(
                    target_pb_ratio=pb_multiple,
                    roe_adjustment_factor=roe_adjustment
                )
                return result.get('fair_value', 0)

            except Exception as e:
                logger.debug(f"P/B calculation failed with scenario params: {e}")
                return 0

        # Calculate probability-weighted valuation
        weighted_result = self.scenario_framework.calculate_probability_weighted_valuation(
            scenario_names,
            pb_valuation_function,
            normalize_probabilities
        )

        # Extract results
        scenario_values = {
            item['name']: item['valuation']
            for item in weighted_result['scenario_details']
        }
        probabilities = {
            item['name']: item['probability']
            for item in weighted_result['scenario_details']
        }

        # Calculate confidence intervals and risk metrics
        confidence_intervals = self._calculate_confidence_intervals(weighted_result)
        risk_metrics = self._calculate_risk_metrics(weighted_result)

        return ScenarioValuationResult(
            expected_value=weighted_result['expected_value'],
            scenario_values=scenario_values,
            probabilities=probabilities,
            confidence_intervals=confidence_intervals,
            risk_metrics=risk_metrics,
            valuation_method="pb"
        )

    def create_custom_three_point_analysis(
        self,
        base_parameters: Dict[str, float],
        parameter_ranges: Dict[str, Tuple[float, float]],
        valuation_method: str = "dcf"
    ) -> ScenarioValuationResult:
        """
        Create and analyze custom three-point scenarios.

        Args:
            base_parameters: Base case parameter values
            parameter_ranges: Parameter ranges for pessimistic/optimistic cases
            valuation_method: Valuation method to use ('dcf', 'ddm', or 'pb')

        Returns:
            ScenarioValuationResult for three-point analysis
        """
        logger.info(f"Creating custom three-point {valuation_method.upper()} analysis")

        # Generate three-point scenarios
        scenarios = self.scenario_framework.generate_three_point_scenarios(
            base_parameters,
            parameter_ranges
        )

        scenario_names = [scenario.name for scenario in scenarios]

        # Run appropriate valuation analysis
        if valuation_method.lower() == "dcf":
            return self.run_scenario_dcf_analysis(scenario_names)
        elif valuation_method.lower() == "ddm":
            return self.run_scenario_ddm_analysis(scenario_names)
        elif valuation_method.lower() == "pb":
            return self.run_scenario_pb_analysis(scenario_names)
        else:
            raise ValueError(f"Unsupported valuation method: {valuation_method}")

    def run_combined_monte_carlo_scenario_analysis(
        self,
        scenario_name: str,
        num_simulations: int = 10000,
        valuation_method: str = "dcf"
    ) -> Dict[str, Any]:
        """
        Combine scenario analysis with Monte Carlo simulation.

        Args:
            scenario_name: Name of scenario to use for Monte Carlo base case
            num_simulations: Number of Monte Carlo simulations
            valuation_method: Valuation method for simulation

        Returns:
            Combined analysis results with scenario and simulation metrics
        """
        logger.info(f"Running combined scenario-Monte Carlo analysis: {scenario_name}")

        if scenario_name not in self.scenario_framework.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        scenario = self.scenario_framework.scenarios[scenario_name]
        scenario_values = scenario.generate_scenario_values()

        # Extract volatility parameters from scenario
        volatility_settings = {
            'revenue_growth_volatility': 0.15,
            'discount_rate_volatility': 0.02,
            'terminal_growth_volatility': 0.01,
            'margin_volatility': 0.05
        }

        # Adjust volatility based on scenario type
        if scenario.scenario_type.value == 'pessimistic':
            # Increase volatility in pessimistic scenarios
            volatility_settings = {k: v * 1.5 for k, v in volatility_settings.items()}
        elif scenario.scenario_type.value == 'optimistic':
            # Decrease volatility in optimistic scenarios
            volatility_settings = {k: v * 0.7 for k, v in volatility_settings.items()}

        # Run Monte Carlo simulation
        if valuation_method.lower() == "dcf":
            mc_result = self.monte_carlo_engine.simulate_dcf_valuation(
                num_simulations=num_simulations,
                **volatility_settings
            )
        elif valuation_method.lower() == "ddm":
            mc_result = self.monte_carlo_engine.simulate_dividend_discount_model(
                num_simulations=num_simulations,
                dividend_growth_volatility=volatility_settings['revenue_growth_volatility'],
                required_return_volatility=volatility_settings['discount_rate_volatility']
            )
        else:
            raise ValueError(f"Unsupported valuation method for Monte Carlo: {valuation_method}")

        return {
            'scenario_name': scenario_name,
            'scenario_values': scenario_values,
            'monte_carlo_result': mc_result,
            'combined_metrics': {
                'scenario_expected_value': np.mean(list(scenario_values.values())),
                'monte_carlo_mean': mc_result.mean_value,
                'monte_carlo_std': mc_result.statistics['std'],
                'monte_carlo_var_5': mc_result.var_5,
                'combined_confidence_interval': mc_result.ci_95
            }
        }

    def _calculate_confidence_intervals(
        self,
        weighted_result: Dict[str, Any]
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals from scenario results."""
        scenario_details = weighted_result['scenario_details']
        valuations = [item['valuation'] for item in scenario_details]

        if len(valuations) < 2:
            return {}

        # Sort valuations for percentile calculation
        sorted_vals = sorted(valuations)
        n = len(sorted_vals)

        # Calculate confidence intervals
        ci_90 = (
            sorted_vals[max(0, int(0.05 * n))],
            sorted_vals[min(n-1, int(0.95 * n))]
        )

        ci_95 = (
            sorted_vals[max(0, int(0.025 * n))],
            sorted_vals[min(n-1, int(0.975 * n))]
        )

        return {
            '90%': ci_90,
            '95%': ci_95
        }

    def _calculate_risk_metrics(
        self,
        weighted_result: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate risk metrics from scenario results."""
        scenario_details = weighted_result['scenario_details']

        if not scenario_details:
            return {}

        valuations = np.array([item['valuation'] for item in scenario_details])
        probabilities = np.array([item['probability'] for item in scenario_details])
        expected_value = weighted_result['expected_value']

        # Calculate weighted variance
        weighted_variance = np.sum(probabilities * (valuations - expected_value) ** 2)
        weighted_std = np.sqrt(weighted_variance)

        # Calculate downside deviation (variance below expected value)
        downside_mask = valuations < expected_value
        if np.any(downside_mask):
            downside_probs = probabilities[downside_mask]
            downside_vals = valuations[downside_mask]
            downside_variance = np.sum(downside_probs * (downside_vals - expected_value) ** 2)
            downside_std = np.sqrt(downside_variance)
        else:
            downside_std = 0

        # Probability of loss (below certain threshold)
        current_price = getattr(self.financial_calculator, 'current_price', expected_value)
        prob_loss = np.sum(probabilities[valuations < current_price])

        return {
            'weighted_std': weighted_std,
            'weighted_variance': weighted_variance,
            'downside_std': downside_std,
            'probability_of_loss': prob_loss,
            'coefficient_of_variation': weighted_std / expected_value if expected_value != 0 else 0,
            'min_value': np.min(valuations),
            'max_value': np.max(valuations)
        }


# Convenience functions for quick analysis

def quick_three_point_dcf_analysis(
    financial_calculator: FinancialCalculator,
    revenue_growth_range: Tuple[float, float] = (-0.05, 0.15),
    discount_rate_range: Tuple[float, float] = (0.08, 0.12),
    terminal_growth_range: Tuple[float, float] = (0.02, 0.04)
) -> ScenarioValuationResult:
    """
    Quick three-point DCF analysis with standard parameter ranges.

    Args:
        financial_calculator: FinancialCalculator instance
        revenue_growth_range: (pessimistic, optimistic) revenue growth rates
        discount_rate_range: (optimistic, pessimistic) discount rates (reversed)
        terminal_growth_range: (pessimistic, optimistic) terminal growth rates

    Returns:
        ScenarioValuationResult for three-point DCF analysis
    """
    integrator = ValuationScenarioIntegrator(financial_calculator)

    base_parameters = {
        'revenue_growth': 0.05,
        'discount_rate': 0.10,
        'terminal_growth': 0.03,
        'operating_margin': 0.20
    }

    parameter_ranges = {
        'revenue_growth': revenue_growth_range,
        'discount_rate': (discount_rate_range[1], discount_rate_range[0]),  # Reversed for discount rate
        'terminal_growth': terminal_growth_range,
        'operating_margin': (0.15, 0.25)
    }

    return integrator.create_custom_three_point_analysis(
        base_parameters,
        parameter_ranges,
        "dcf"
    )


def create_economic_scenario_dcf_analysis(
    financial_calculator: FinancialCalculator
) -> ScenarioValuationResult:
    """
    Create DCF analysis using predefined economic scenarios.

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        ScenarioValuationResult using economic scenarios
    """
    integrator = ValuationScenarioIntegrator(financial_calculator)

    # Use predefined economic scenarios
    scenario_names = [
        'Base Case',
        'Optimistic Case',
        'Pessimistic Case',
        'Economic Expansion',
        'Recession'
    ]

    return integrator.run_scenario_dcf_analysis(scenario_names)