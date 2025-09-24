"""
Unified Scenario Planning Interface
==================================

This module provides a comprehensive, unified interface for scenario planning and
sensitivity analysis that integrates all existing components of the financial
analysis framework. It serves as the central orchestrator for scenario-based
valuation analysis, combining scenario modeling, sensitivity analysis, Monte Carlo
simulation, and interactive visualization.

Key Features:
- Unified interface for all scenario planning capabilities
- Integration of existing scenario modeling, sensitivity analysis, and Monte Carlo engines
- Streamlined workflow for comprehensive scenario-based valuation analysis
- Interactive parameter configuration and scenario selection
- Automated report generation and visualization
- Performance optimization with intelligent caching

Classes:
--------
UnifiedScenarioPlanner
    Main interface class that orchestrates all scenario planning capabilities

ScenarioPlanningWorkflow
    Workflow manager for comprehensive scenario analysis workflows

ScenarioPlanningResult
    Comprehensive result container for all analysis outputs

Usage Example:
-------------
>>> from core.analysis.scenario_planning_interface import UnifiedScenarioPlanner
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize unified scenario planner
>>> calc = FinancialCalculator('AAPL')
>>> planner = UnifiedScenarioPlanner(calc)
>>>
>>> # Run comprehensive scenario analysis
>>> result = planner.run_comprehensive_scenario_analysis(
...     scenarios=['Base Case', 'Optimistic Case', 'Pessimistic Case'],
...     valuation_methods=['dcf', 'ddm'],
...     include_sensitivity=True,
...     include_monte_carlo=True,
...     monte_carlo_simulations=10000
... )
>>>
>>> # Access results
>>> print(f"Expected DCF Value: ${result.dcf_results.expected_value:.2f}")
>>> print(f"Most Sensitive Parameter: {result.sensitivity_results.get_most_sensitive_parameter()}")
>>> print(f"Monte Carlo 95% CI: ${result.monte_carlo_results.ci_95[0]:.2f} - ${result.monte_carlo_results.ci_95[1]:.2f}")
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import existing components
from .engines.financial_calculations import FinancialCalculator
from .risk.scenario_modeling import ScenarioModelingFramework, CustomScenario, PredefinedScenarios
from .risk.valuation_scenario_integration import ValuationScenarioIntegrator, ScenarioValuationResult
from .risk.sensitivity_analysis import SensitivityAnalyzer, SensitivityResult
from .statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult

logger = logging.getLogger(__name__)


class AnalysisScope(Enum):
    """Scope of scenario planning analysis."""
    BASIC = "basic"              # Single valuation method, predefined scenarios
    COMPREHENSIVE = "comprehensive"  # Multiple methods, custom scenarios, sensitivity
    ADVANCED = "advanced"        # Full analysis with Monte Carlo and visualization


@dataclass
class ScenarioPlanningConfig:
    """
    Configuration for scenario planning analysis.

    Attributes:
        valuation_methods: List of valuation methods to include
        scenario_names: List of scenario names to analyze
        include_sensitivity: Whether to include sensitivity analysis
        include_monte_carlo: Whether to include Monte Carlo simulation
        monte_carlo_simulations: Number of Monte Carlo simulations
        confidence_levels: Confidence levels for analysis
        analysis_scope: Scope of analysis to perform
    """
    valuation_methods: List[str] = field(default_factory=lambda: ['dcf'])
    scenario_names: List[str] = field(default_factory=lambda: ['Base Case', 'Optimistic Case', 'Pessimistic Case'])
    include_sensitivity: bool = True
    include_monte_carlo: bool = True
    monte_carlo_simulations: int = 10000
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95])
    analysis_scope: AnalysisScope = AnalysisScope.COMPREHENSIVE

    # Sensitivity analysis parameters
    sensitivity_parameters: Optional[List[str]] = None
    sensitivity_variation_percentage: float = 0.20

    # Monte Carlo parameters
    monte_carlo_volatility_level: str = "medium"  # low, medium, high
    monte_carlo_correlation_enabled: bool = False

    # Custom scenario parameters
    custom_scenarios: Optional[Dict[str, Dict[str, float]]] = None

    # Output preferences
    generate_visualizations: bool = True
    export_detailed_results: bool = True


@dataclass
class ScenarioPlanningResult:
    """
    Comprehensive container for all scenario planning analysis results.

    Attributes:
        config: Configuration used for analysis
        scenario_results: Scenario-based valuation results by method
        sensitivity_results: Sensitivity analysis results by method
        monte_carlo_results: Monte Carlo simulation results by method
        summary_metrics: Summary metrics across all analyses
        recommendations: AI-generated recommendations based on results
    """
    config: ScenarioPlanningConfig
    scenario_results: Dict[str, ScenarioValuationResult] = field(default_factory=dict)
    sensitivity_results: Dict[str, SensitivityResult] = field(default_factory=dict)
    monte_carlo_results: Dict[str, SimulationResult] = field(default_factory=dict)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    analysis_date: datetime = field(default_factory=datetime.now)

    @property
    def primary_valuation_method(self) -> str:
        """Get the primary valuation method used."""
        return self.config.valuation_methods[0] if self.config.valuation_methods else 'dcf'

    @property
    def expected_value(self) -> float:
        """Get expected value from primary valuation method."""
        primary_method = self.primary_valuation_method
        if primary_method in self.scenario_results:
            return self.scenario_results[primary_method].expected_value
        return 0.0

    @property
    def confidence_interval_95(self) -> Tuple[float, float]:
        """Get 95% confidence interval from primary valuation method."""
        primary_method = self.primary_valuation_method
        if primary_method in self.scenario_results:
            return self.scenario_results[primary_method].confidence_interval_95
        return (0.0, 0.0)

    @property
    def most_sensitive_parameter(self) -> Optional[str]:
        """Get most sensitive parameter from sensitivity analysis."""
        primary_method = self.primary_valuation_method
        if primary_method in self.sensitivity_results:
            return self.sensitivity_results[primary_method].get_most_sensitive_parameter()
        return None

    def get_summary_table(self) -> pd.DataFrame:
        """Generate summary table of all results."""
        summary_data = []

        for method in self.config.valuation_methods:
            row = {'Valuation Method': method.upper()}

            # Scenario results
            if method in self.scenario_results:
                result = self.scenario_results[method]
                row.update({
                    'Expected Value': result.expected_value,
                    'Downside Risk': result.downside_risk,
                    'Upside Potential': result.upside_potential,
                    'Confidence Interval (95%)': f"{result.confidence_interval_95[0]:.2f} - {result.confidence_interval_95[1]:.2f}"
                })

            # Sensitivity results
            if method in self.sensitivity_results:
                sens_result = self.sensitivity_results[method]
                most_sensitive = sens_result.get_most_sensitive_parameter()
                row['Most Sensitive Parameter'] = most_sensitive or 'N/A'

            # Monte Carlo results
            if method in self.monte_carlo_results:
                mc_result = self.monte_carlo_results[method]
                row.update({
                    'Monte Carlo Mean': mc_result.mean_value,
                    'Monte Carlo Std': mc_result.statistics['std'],
                    'Value at Risk (5%)': mc_result.var_5
                })

            summary_data.append(row)

        return pd.DataFrame(summary_data)

    def export_to_dict(self) -> Dict[str, Any]:
        """Export all results to dictionary for serialization."""
        return {
            'config': {
                'valuation_methods': self.config.valuation_methods,
                'scenario_names': self.config.scenario_names,
                'include_sensitivity': self.config.include_sensitivity,
                'include_monte_carlo': self.config.include_monte_carlo,
                'analysis_scope': self.config.analysis_scope.value
            },
            'scenario_results': {
                method: result.to_dict()
                for method, result in self.scenario_results.items()
            },
            'summary_metrics': self.summary_metrics,
            'recommendations': self.recommendations,
            'analysis_date': self.analysis_date.isoformat(),
            'key_metrics': {
                'expected_value': self.expected_value,
                'confidence_interval_95': self.confidence_interval_95,
                'most_sensitive_parameter': self.most_sensitive_parameter
            }
        }


class UnifiedScenarioPlanner:
    """
    Unified interface for comprehensive scenario planning and sensitivity analysis.

    This class orchestrates all existing scenario planning components to provide
    a streamlined, comprehensive analysis workflow.
    """

    def __init__(self, financial_calculator: FinancialCalculator):
        """
        Initialize unified scenario planner.

        Args:
            financial_calculator: FinancialCalculator instance for data access
        """
        self.financial_calculator = financial_calculator

        # Initialize all analysis components
        self.scenario_framework = ScenarioModelingFramework()
        self.scenario_integrator = ValuationScenarioIntegrator(
            financial_calculator, self.scenario_framework
        )
        self.sensitivity_analyzer = SensitivityAnalyzer(financial_calculator)
        self.monte_carlo_engine = MonteCarloEngine(financial_calculator)

        # Cache for analysis results
        self.analysis_cache: Dict[str, ScenarioPlanningResult] = {}

        logger.info("Unified Scenario Planner initialized")

    def run_comprehensive_scenario_analysis(
        self,
        scenarios: Optional[List[str]] = None,
        valuation_methods: Optional[List[str]] = None,
        include_sensitivity: bool = True,
        include_monte_carlo: bool = True,
        monte_carlo_simulations: int = 10000,
        analysis_scope: AnalysisScope = AnalysisScope.COMPREHENSIVE
    ) -> ScenarioPlanningResult:
        """
        Run comprehensive scenario planning analysis.

        Args:
            scenarios: List of scenario names to analyze
            valuation_methods: List of valuation methods ('dcf', 'ddm', 'pb')
            include_sensitivity: Whether to include sensitivity analysis
            include_monte_carlo: Whether to include Monte Carlo simulation
            monte_carlo_simulations: Number of Monte Carlo simulations
            analysis_scope: Scope of analysis to perform

        Returns:
            ScenarioPlanningResult with comprehensive analysis results
        """
        # Set defaults
        scenarios = scenarios or ['Base Case', 'Optimistic Case', 'Pessimistic Case']
        valuation_methods = valuation_methods or ['dcf']

        # Create configuration
        config = ScenarioPlanningConfig(
            valuation_methods=valuation_methods,
            scenario_names=scenarios,
            include_sensitivity=include_sensitivity,
            include_monte_carlo=include_monte_carlo,
            monte_carlo_simulations=monte_carlo_simulations,
            analysis_scope=analysis_scope
        )

        logger.info(f"Starting comprehensive scenario analysis: {len(scenarios)} scenarios, {len(valuation_methods)} methods")

        # Initialize result container
        result = ScenarioPlanningResult(config=config)

        # Run scenario-based valuation analysis
        result.scenario_results = self._run_scenario_valuations(config)

        # Run sensitivity analysis if requested
        if include_sensitivity:
            result.sensitivity_results = self._run_sensitivity_analysis(config)

        # Run Monte Carlo analysis if requested
        if include_monte_carlo:
            result.monte_carlo_results = self._run_monte_carlo_analysis(config)

        # Calculate summary metrics
        result.summary_metrics = self._calculate_summary_metrics(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        # Cache result
        cache_key = self._generate_cache_key(config)
        self.analysis_cache[cache_key] = result

        logger.info(f"Comprehensive scenario analysis completed: Expected value ${result.expected_value:.2f}")
        return result

    def create_custom_scenario_analysis(
        self,
        custom_scenarios: Dict[str, Dict[str, float]],
        valuation_method: str = 'dcf'
    ) -> ScenarioPlanningResult:
        """
        Create and analyze custom scenarios.

        Args:
            custom_scenarios: Dictionary mapping scenario names to parameter dictionaries
            valuation_method: Valuation method to use

        Returns:
            ScenarioPlanningResult with custom scenario analysis
        """
        logger.info(f"Creating custom scenario analysis with {len(custom_scenarios)} scenarios")

        # Create custom scenarios in the framework
        for scenario_name, params in custom_scenarios.items():
            custom_scenario = CustomScenario(
                name=scenario_name,
                description=f"Custom scenario: {scenario_name}"
            )

            # Add parameters
            for param_name, param_value in params.items():
                from .risk.scenario_modeling import ScenarioParameter, ParameterType
                parameter = ScenarioParameter(
                    name=param_name,
                    variable_type="custom",
                    base_value=param_value,
                    shock_value=param_value,
                    shock_type="absolute"
                )
                custom_scenario.add_parameter(parameter)

            self.scenario_framework.add_scenario(custom_scenario)

        # Run analysis with custom scenarios
        config = ScenarioPlanningConfig(
            valuation_methods=[valuation_method],
            scenario_names=list(custom_scenarios.keys()),
            custom_scenarios=custom_scenarios
        )

        return self.run_comprehensive_scenario_analysis(
            scenarios=list(custom_scenarios.keys()),
            valuation_methods=[valuation_method]
        )

    def run_three_point_analysis(
        self,
        base_parameters: Dict[str, float],
        parameter_ranges: Dict[str, Tuple[float, float]],
        valuation_method: str = 'dcf'
    ) -> ScenarioPlanningResult:
        """
        Run three-point scenario analysis (pessimistic/base/optimistic).

        Args:
            base_parameters: Base case parameter values
            parameter_ranges: Parameter ranges for pessimistic/optimistic cases
            valuation_method: Valuation method to use

        Returns:
            ScenarioPlanningResult with three-point analysis
        """
        logger.info("Running three-point scenario analysis")

        result = self.scenario_integrator.create_custom_three_point_analysis(
            base_parameters, parameter_ranges, valuation_method
        )

        # Convert to unified result format
        config = ScenarioPlanningConfig(
            valuation_methods=[valuation_method],
            scenario_names=["Pessimistic", "Base", "Optimistic"]
        )

        unified_result = ScenarioPlanningResult(config=config)
        unified_result.scenario_results[valuation_method] = result

        return unified_result

    def run_quick_sensitivity_analysis(
        self,
        valuation_method: str = 'dcf',
        parameters: Optional[List[str]] = None,
        variation_percentage: float = 0.20
    ) -> SensitivityResult:
        """
        Run quick sensitivity analysis with default parameters.

        Args:
            valuation_method: Valuation method to analyze
            parameters: List of parameters to analyze (uses defaults if None)
            variation_percentage: Percentage variation from base case

        Returns:
            SensitivityResult with analysis results
        """
        logger.info(f"Running quick sensitivity analysis for {valuation_method}")

        # Use default parameters if none specified
        if parameters is None:
            if valuation_method == 'dcf':
                parameters = ['revenue_growth', 'discount_rate', 'terminal_growth', 'operating_margin']
            elif valuation_method == 'ddm':
                parameters = ['dividend_growth', 'required_return', 'payout_ratio']
            else:
                parameters = ['revenue_growth', 'discount_rate']

        return self.sensitivity_analyzer.tornado_analysis(
            valuation_method=valuation_method,
            parameters=parameters,
            variation_percentage=variation_percentage
        )

    def run_quick_monte_carlo_analysis(
        self,
        valuation_method: str = 'dcf',
        num_simulations: int = 5000,
        volatility_level: str = 'medium'
    ) -> SimulationResult:
        """
        Run quick Monte Carlo analysis with predefined settings.

        Args:
            valuation_method: Valuation method to simulate
            num_simulations: Number of simulations
            volatility_level: Volatility level ('low', 'medium', 'high')

        Returns:
            SimulationResult with simulation results
        """
        logger.info(f"Running quick Monte Carlo analysis: {num_simulations} simulations")

        if valuation_method == 'dcf':
            from .statistics.monte_carlo_engine import quick_dcf_simulation
            return quick_dcf_simulation(
                self.financial_calculator,
                num_simulations,
                volatility_level
            )
        elif valuation_method == 'ddm':
            return self.monte_carlo_engine.simulate_dividend_discount_model(
                num_simulations=num_simulations
            )
        else:
            raise ValueError(f"Unsupported valuation method for Monte Carlo: {valuation_method}")

    def compare_scenarios(
        self,
        scenario_groups: Dict[str, List[str]],
        valuation_method: str = 'dcf'
    ) -> pd.DataFrame:
        """
        Compare different groups of scenarios.

        Args:
            scenario_groups: Dictionary mapping group names to scenario lists
            valuation_method: Valuation method to use for comparison

        Returns:
            DataFrame with scenario comparison results
        """
        logger.info(f"Comparing {len(scenario_groups)} scenario groups")

        comparison_data = []

        for group_name, scenarios in scenario_groups.items():
            # Run scenario analysis for this group
            if valuation_method == 'dcf':
                result = self.scenario_integrator.run_scenario_dcf_analysis(scenarios)
            elif valuation_method == 'ddm':
                result = self.scenario_integrator.run_scenario_ddm_analysis(scenarios)
            elif valuation_method == 'pb':
                result = self.scenario_integrator.run_scenario_pb_analysis(scenarios)
            else:
                continue

            comparison_data.append({
                'Scenario Group': group_name,
                'Expected Value': result.expected_value,
                'Downside Risk': result.downside_risk,
                'Upside Potential': result.upside_potential,
                'Confidence Interval (95%)': f"{result.confidence_interval_95[0]:.2f} - {result.confidence_interval_95[1]:.2f}",
                'Number of Scenarios': len(scenarios)
            })

        return pd.DataFrame(comparison_data)

    def _run_scenario_valuations(self, config: ScenarioPlanningConfig) -> Dict[str, ScenarioValuationResult]:
        """Run scenario-based valuations for all specified methods."""
        results = {}

        for method in config.valuation_methods:
            try:
                if method == 'dcf':
                    result = self.scenario_integrator.run_scenario_dcf_analysis(
                        config.scenario_names, normalize_probabilities=True
                    )
                elif method == 'ddm':
                    result = self.scenario_integrator.run_scenario_ddm_analysis(
                        config.scenario_names, normalize_probabilities=True
                    )
                elif method == 'pb':
                    result = self.scenario_integrator.run_scenario_pb_analysis(
                        config.scenario_names, normalize_probabilities=True
                    )
                else:
                    logger.warning(f"Unsupported valuation method: {method}")
                    continue

                results[method] = result
                logger.debug(f"Scenario valuation completed for {method}: {result.expected_value:.2f}")

            except Exception as e:
                logger.error(f"Scenario valuation failed for {method}: {e}")
                continue

        return results

    def _run_sensitivity_analysis(self, config: ScenarioPlanningConfig) -> Dict[str, SensitivityResult]:
        """Run sensitivity analysis for all specified methods."""
        results = {}

        parameters = config.sensitivity_parameters or self._get_default_sensitivity_parameters()

        for method in config.valuation_methods:
            try:
                # Get method-specific parameters
                method_params = self._get_method_sensitivity_parameters(method, parameters)

                result = self.sensitivity_analyzer.tornado_analysis(
                    valuation_method=method,
                    parameters=method_params,
                    variation_percentage=config.sensitivity_variation_percentage
                )

                results[method] = result
                logger.debug(f"Sensitivity analysis completed for {method}")

            except Exception as e:
                logger.error(f"Sensitivity analysis failed for {method}: {e}")
                continue

        return results

    def _run_monte_carlo_analysis(self, config: ScenarioPlanningConfig) -> Dict[str, SimulationResult]:
        """Run Monte Carlo analysis for all specified methods."""
        results = {}

        for method in config.valuation_methods:
            try:
                if method == 'dcf':
                    result = self.monte_carlo_engine.simulate_dcf_valuation(
                        num_simulations=config.monte_carlo_simulations
                    )
                elif method == 'ddm':
                    result = self.monte_carlo_engine.simulate_dividend_discount_model(
                        num_simulations=config.monte_carlo_simulations
                    )
                else:
                    logger.warning(f"Monte Carlo not supported for method: {method}")
                    continue

                results[method] = result
                logger.debug(f"Monte Carlo analysis completed for {method}: {result.mean_value:.2f}")

            except Exception as e:
                logger.error(f"Monte Carlo analysis failed for {method}: {e}")
                continue

        return results

    def _calculate_summary_metrics(self, result: ScenarioPlanningResult) -> Dict[str, Any]:
        """Calculate summary metrics across all analyses."""
        metrics = {}

        # Primary method metrics
        primary_method = result.primary_valuation_method

        if primary_method in result.scenario_results:
            scenario_result = result.scenario_results[primary_method]
            metrics.update({
                'expected_value': scenario_result.expected_value,
                'downside_risk': scenario_result.downside_risk,
                'upside_potential': scenario_result.upside_potential,
                'confidence_interval_width': (
                    scenario_result.confidence_interval_95[1] -
                    scenario_result.confidence_interval_95[0]
                )
            })

        # Sensitivity metrics
        if primary_method in result.sensitivity_results:
            sens_result = result.sensitivity_results[primary_method]
            metrics.update({
                'most_sensitive_parameter': sens_result.get_most_sensitive_parameter(),
                'sensitivity_score': sens_result.statistics.get('max_sensitivity', 0)
            })

        # Monte Carlo metrics
        if primary_method in result.monte_carlo_results:
            mc_result = result.monte_carlo_results[primary_method]
            metrics.update({
                'monte_carlo_convergence': mc_result.convergence_info.get('converged', False),
                'monte_carlo_var_5': mc_result.var_5,
                'monte_carlo_coefficient_of_variation': (
                    mc_result.statistics['std'] / mc_result.statistics['mean']
                    if mc_result.statistics['mean'] != 0 else 0
                )
            })

        return metrics

    def _generate_recommendations(self, result: ScenarioPlanningResult) -> List[str]:
        """Generate AI-powered recommendations based on analysis results."""
        recommendations = []

        primary_method = result.primary_valuation_method

        # Risk-based recommendations
        if primary_method in result.scenario_results:
            scenario_result = result.scenario_results[primary_method]

            risk_ratio = scenario_result.downside_risk / scenario_result.expected_value
            if risk_ratio > 0.3:
                recommendations.append(
                    "High downside risk detected. Consider hedging strategies or "
                    "additional scenario analysis for risk mitigation."
                )

            upside_ratio = scenario_result.upside_potential / scenario_result.expected_value
            if upside_ratio > 0.5:
                recommendations.append(
                    "Significant upside potential identified. Consider growth "
                    "acceleration strategies or increased investment allocation."
                )

        # Sensitivity-based recommendations
        if primary_method in result.sensitivity_results:
            sens_result = result.sensitivity_results[primary_method]
            most_sensitive = sens_result.get_most_sensitive_parameter()

            if most_sensitive:
                recommendations.append(
                    f"Focus management attention on {most_sensitive.replace('_', ' ')} "
                    f"as it has the highest impact on valuation."
                )

        # Monte Carlo-based recommendations
        if primary_method in result.monte_carlo_results:
            mc_result = result.monte_carlo_results[primary_method]

            if not mc_result.convergence_info.get('converged', False):
                recommendations.append(
                    "Monte Carlo simulation did not fully converge. Consider "
                    "increasing simulation count for more reliable results."
                )

            prob_loss = mc_result.risk_metrics.probability_of_loss if mc_result.risk_metrics else 0
            if prob_loss > 0.2:
                recommendations.append(
                    f"High probability of loss ({prob_loss:.1%}). Consider "
                    "defensive positioning or risk management strategies."
                )

        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "Analysis completed successfully. Results suggest balanced "
                "risk-return profile with normal market conditions."
            )

        return recommendations

    def _get_default_sensitivity_parameters(self) -> List[str]:
        """Get default sensitivity parameters."""
        return ['revenue_growth', 'discount_rate', 'terminal_growth', 'operating_margin']

    def _get_method_sensitivity_parameters(self, method: str, parameters: List[str]) -> List[str]:
        """Get method-specific sensitivity parameters."""
        method_mappings = {
            'dcf': ['revenue_growth', 'discount_rate', 'terminal_growth', 'operating_margin', 'tax_rate'],
            'ddm': ['dividend_growth', 'required_return', 'payout_ratio'],
            'pb': ['roe', 'required_return', 'growth_rate']
        }

        method_params = method_mappings.get(method, parameters)
        return [p for p in parameters if p in method_params]

    def _generate_cache_key(self, config: ScenarioPlanningConfig) -> str:
        """Generate cache key for analysis configuration."""
        key_parts = [
            '-'.join(sorted(config.valuation_methods)),
            '-'.join(sorted(config.scenario_names)),
            str(config.include_sensitivity),
            str(config.include_monte_carlo),
            str(config.monte_carlo_simulations)
        ]
        return '_'.join(key_parts)

    def get_available_scenarios(self) -> List[str]:
        """Get list of all available scenario names."""
        return self.scenario_framework.list_scenarios()

    def get_predefined_scenarios(self) -> List[str]:
        """Get list of predefined scenario names."""
        predefined = PredefinedScenarios.all_predefined_scenarios()
        return [scenario.name for scenario in predefined]

    def clear_cache(self) -> None:
        """Clear analysis result cache."""
        self.analysis_cache.clear()
        self.sensitivity_analyzer.clear_cache()
        logger.info("Scenario planning cache cleared")


# Convenience functions for quick analysis

def quick_scenario_planning_analysis(
    financial_calculator: FinancialCalculator,
    analysis_type: str = "comprehensive"
) -> ScenarioPlanningResult:
    """
    Quick scenario planning analysis with predefined settings.

    Args:
        financial_calculator: FinancialCalculator instance
        analysis_type: Type of analysis ('basic', 'comprehensive', 'advanced')

    Returns:
        ScenarioPlanningResult with analysis results
    """
    planner = UnifiedScenarioPlanner(financial_calculator)

    if analysis_type == "basic":
        return planner.run_comprehensive_scenario_analysis(
            valuation_methods=['dcf'],
            include_sensitivity=False,
            include_monte_carlo=False,
            analysis_scope=AnalysisScope.BASIC
        )
    elif analysis_type == "comprehensive":
        return planner.run_comprehensive_scenario_analysis(
            valuation_methods=['dcf', 'ddm'],
            include_sensitivity=True,
            include_monte_carlo=True,
            analysis_scope=AnalysisScope.COMPREHENSIVE
        )
    else:  # advanced
        return planner.run_comprehensive_scenario_analysis(
            valuation_methods=['dcf', 'ddm', 'pb'],
            include_sensitivity=True,
            include_monte_carlo=True,
            monte_carlo_simulations=20000,
            analysis_scope=AnalysisScope.ADVANCED
        )


def create_economic_scenario_comparison(
    financial_calculator: FinancialCalculator
) -> pd.DataFrame:
    """
    Create comparison of economic scenarios.

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        DataFrame with scenario comparison
    """
    planner = UnifiedScenarioPlanner(financial_calculator)

    scenario_groups = {
        'Current Economic Environment': ['Base Case'],
        'Growth Scenarios': ['Optimistic Case', 'Economic Expansion'],
        'Stress Scenarios': ['Pessimistic Case', 'Recession'],
        'Crisis Scenarios': ['2008 Financial Crisis', 'COVID-19 Pandemic']
    }

    return planner.compare_scenarios(scenario_groups, 'dcf')