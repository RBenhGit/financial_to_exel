"""
Scenario Modeling Framework
==========================

This module provides comprehensive scenario modeling capabilities for financial
risk analysis. It integrates with the Monte Carlo engine and risk metrics framework
to provide flexible scenario analysis, stress testing, and what-if analysis.

Key Features:
- Predefined financial scenarios (bull/bear markets, recessions, etc.)
- Custom scenario creation with parameter specifications
- Multi-dimensional scenario analysis
- Scenario correlation and dependency modeling
- Historical scenario replication
- Forward-looking scenario generation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of financial scenarios."""
    HISTORICAL = "historical"      # Historical market events
    STRESS = "stress"             # Extreme stress conditions
    BASELINE = "baseline"         # Base case scenarios
    OPTIMISTIC = "optimistic"     # Positive scenarios
    PESSIMISTIC = "pessimistic"   # Negative scenarios
    REGULATORY = "regulatory"     # Regulatory changes
    GEOPOLITICAL = "geopolitical" # Geopolitical events
    TECHNOLOGICAL = "technological" # Technology disruptions
    ENVIRONMENTAL = "environmental" # Climate/ESG events
    CUSTOM = "custom"             # User-defined scenarios


class ScenarioSeverity(Enum):
    """Severity levels for scenario impacts."""
    MILD = (1, "1-in-5 year event")
    MODERATE = (2, "1-in-10 year event")
    SEVERE = (3, "1-in-25 year event")
    EXTREME = (4, "1-in-50 year event")
    CATASTROPHIC = (5, "1-in-100+ year event")

    def __init__(self, level: int, description: str):
        self.level = level
        self.description = description


@dataclass
class ScenarioParameter:
    """
    Definition of a scenario parameter with statistical properties.

    Represents a single financial variable that can be shocked or modified
    in scenario analysis, with its distribution and correlation properties.
    """
    name: str
    variable_type: str  # 'return', 'volatility', 'correlation', 'spread', etc.
    base_value: float
    shock_value: Optional[float] = None
    shock_type: str = 'absolute'  # 'absolute', 'relative', 'percentile'

    # Statistical properties
    distribution: str = 'normal'
    distribution_params: Dict[str, float] = field(default_factory=dict)

    # Bounds and constraints
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Temporal properties
    persistence: float = 0.0  # How long the shock persists (0-1)
    mean_reversion_speed: float = 0.1  # Speed of mean reversion

    # Metadata
    description: str = ""
    units: str = ""
    source: str = ""

    def apply_shock(self, current_value: Optional[float] = None) -> float:
        """Apply scenario shock to parameter value."""
        if self.shock_value is None:
            return current_value or self.base_value

        base = current_value or self.base_value

        if self.shock_type == 'absolute':
            shocked_value = base + self.shock_value
        elif self.shock_type == 'relative':
            shocked_value = base * (1 + self.shock_value)
        elif self.shock_type == 'percentile':
            # Interpret shock_value as percentile (0-100)
            if self.distribution == 'normal':
                from scipy.stats import norm
                shocked_value = base + norm.ppf(self.shock_value / 100.0) * self.distribution_params.get('std', 0.1)
            else:
                shocked_value = base + self.shock_value / 100.0
        else:
            shocked_value = self.shock_value

        # Apply bounds
        if self.min_value is not None:
            shocked_value = max(shocked_value, self.min_value)
        if self.max_value is not None:
            shocked_value = min(shocked_value, self.max_value)

        return shocked_value

    def generate_time_series(self, periods: int, dt: float = 1.0) -> np.ndarray:
        """Generate time series for the parameter under scenario conditions."""
        if self.shock_value is None:
            return np.full(periods, self.base_value)

        shocked_value = self.apply_shock()
        time_series = np.zeros(periods)

        # Initialize with shocked value
        time_series[0] = shocked_value

        # Apply mean reversion with persistence
        for t in range(1, periods):
            # Mean reversion force pulls toward base value
            reversion_force = self.mean_reversion_speed * (self.base_value - time_series[t-1])

            # Persistence reduces the effect of mean reversion (0 = full reversion, 1 = no reversion)
            effective_reversion = reversion_force * (1 - self.persistence)

            time_series[t] = time_series[t-1] + effective_reversion * dt

            # Add random component if distribution specified
            if 'std' in self.distribution_params:
                noise = np.random.normal(0, self.distribution_params['std'] * np.sqrt(dt))
                time_series[t] += noise

            # Apply bounds
            if self.min_value is not None:
                time_series[t] = max(time_series[t], self.min_value)
            if self.max_value is not None:
                time_series[t] = min(time_series[t], self.max_value)

        return time_series


@dataclass
class CustomScenario:
    """
    User-defined custom scenario with parameter specifications.

    Allows creation of flexible scenarios with multiple parameter shocks,
    correlations, and temporal dynamics for comprehensive what-if analysis.
    """
    name: str
    description: str
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    severity: ScenarioSeverity = ScenarioSeverity.MODERATE

    # Parameter specifications
    parameters: Dict[str, ScenarioParameter] = field(default_factory=dict)

    # Correlation structure
    parameter_correlations: Optional[np.ndarray] = None
    correlation_param_names: List[str] = field(default_factory=list)

    # Temporal properties
    duration: int = 1  # Number of periods scenario lasts
    transition_periods: int = 0  # Periods to transition into scenario

    # Probability and likelihood
    probability: Optional[float] = None  # Annual probability of occurrence
    confidence_level: float = 0.95

    # Metadata
    creation_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: List[str] = field(default_factory=list)

    def add_parameter(self, parameter: ScenarioParameter) -> None:
        """Add a parameter to the scenario."""
        self.parameters[parameter.name] = parameter

    def remove_parameter(self, parameter_name: str) -> None:
        """Remove a parameter from the scenario."""
        if parameter_name in self.parameters:
            del self.parameters[parameter_name]

    def set_parameter_correlation(
        self,
        param_names: List[str],
        correlation_matrix: np.ndarray
    ) -> None:
        """Set correlation structure between parameters."""
        if correlation_matrix.shape[0] != len(param_names):
            raise ValueError("Correlation matrix size must match parameter count")

        self.correlation_param_names = param_names
        self.parameter_correlations = correlation_matrix

    def generate_scenario_values(self, random_state: Optional[int] = None) -> Dict[str, float]:
        """Generate correlated parameter values for the scenario."""
        if random_state is not None:
            np.random.seed(random_state)

        scenario_values = {}

        if self.parameter_correlations is not None and self.correlation_param_names:
            # Generate correlated shocks
            n_params = len(self.correlation_param_names)
            random_shocks = np.random.multivariate_normal(
                mean=np.zeros(n_params),
                cov=self.parameter_correlations
            )

            for i, param_name in enumerate(self.correlation_param_names):
                if param_name in self.parameters:
                    param = self.parameters[param_name]
                    base_shock = param.shock_value or 0
                    correlated_shock = base_shock + random_shocks[i] * param.distribution_params.get('std', 0.1)

                    # Temporarily set shock value
                    original_shock = param.shock_value
                    param.shock_value = correlated_shock
                    scenario_values[param_name] = param.apply_shock()
                    param.shock_value = original_shock
        else:
            # Generate independent parameter values
            for param_name, param in self.parameters.items():
                scenario_values[param_name] = param.apply_shock()

        return scenario_values

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'scenario_type': self.scenario_type.value,
            'severity': self.severity.level,
            'parameters': {
                name: {
                    'name': param.name,
                    'variable_type': param.variable_type,
                    'base_value': param.base_value,
                    'shock_value': param.shock_value,
                    'shock_type': param.shock_type,
                    'distribution': param.distribution,
                    'distribution_params': param.distribution_params,
                    'min_value': param.min_value,
                    'max_value': param.max_value,
                    'description': param.description
                }
                for name, param in self.parameters.items()
            },
            'duration': self.duration,
            'probability': self.probability,
            'creation_date': self.creation_date.isoformat(),
            'tags': self.tags
        }


class PredefinedScenarios:
    """
    Collection of predefined financial scenarios for common stress testing.

    Provides ready-to-use scenarios for typical market conditions, economic
    events, and financial stress situations commonly used in risk analysis.
    """

    @staticmethod
    def market_crash_2008() -> CustomScenario:
        """Replicate 2008 financial crisis conditions."""
        scenario = CustomScenario(
            name="2008 Financial Crisis",
            description="Severe market stress similar to 2008 financial crisis",
            scenario_type=ScenarioType.HISTORICAL,
            severity=ScenarioSeverity.EXTREME
        )

        # Market parameters
        scenario.add_parameter(ScenarioParameter(
            name="equity_return",
            variable_type="return",
            base_value=0.0,
            shock_value=-0.37,  # S&P 500 fell ~37% in 2008
            shock_type="absolute",
            description="Equity market decline"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="credit_spread",
            variable_type="spread",
            base_value=0.02,
            shock_value=0.06,  # Credit spreads widened dramatically
            shock_type="absolute",
            description="Corporate credit spread widening"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="volatility",
            variable_type="volatility",
            base_value=0.15,
            shock_value=0.45,  # VIX reached ~80
            shock_type="absolute",
            description="Market volatility spike"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="correlation",
            variable_type="correlation",
            base_value=0.3,
            shock_value=0.8,  # Correlations approached 1
            shock_type="absolute",
            description="Asset correlation increase"
        ))

        return scenario

    @staticmethod
    def covid_crash_2020() -> CustomScenario:
        """Replicate COVID-19 pandemic market conditions."""
        scenario = CustomScenario(
            name="COVID-19 Pandemic",
            description="Market stress from COVID-19 pandemic (March 2020)",
            scenario_type=ScenarioType.HISTORICAL,
            severity=ScenarioSeverity.SEVERE
        )

        scenario.add_parameter(ScenarioParameter(
            name="equity_return",
            variable_type="return",
            base_value=0.0,
            shock_value=-0.34,  # S&P 500 fell ~34% peak-to-trough
            shock_type="absolute",
            description="Rapid equity market decline"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="volatility",
            variable_type="volatility",
            base_value=0.15,
            shock_value=0.75,  # VIX spiked to ~82
            shock_type="absolute",
            description="Extreme volatility spike"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="liquidity_premium",
            variable_type="spread",
            base_value=0.01,
            shock_value=0.05,
            shock_type="absolute",
            description="Liquidity crisis premium"
        ))

        return scenario

    @staticmethod
    def recession_scenario() -> CustomScenario:
        """Standard recession scenario."""
        scenario = CustomScenario(
            name="Economic Recession",
            description="Typical economic recession with market stress",
            scenario_type=ScenarioType.STRESS,
            severity=ScenarioSeverity.MODERATE
        )

        scenario.add_parameter(ScenarioParameter(
            name="gdp_growth",
            variable_type="economic",
            base_value=0.02,
            shock_value=-0.02,
            shock_type="absolute",
            description="GDP growth decline"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="equity_return",
            variable_type="return",
            base_value=0.0,
            shock_value=-0.20,
            shock_type="absolute",
            description="Equity market decline"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="unemployment_rate",
            variable_type="economic",
            base_value=0.04,
            shock_value=0.08,
            shock_type="absolute",
            description="Rising unemployment"
        ))

        return scenario

    @staticmethod
    def interest_rate_shock() -> CustomScenario:
        """Interest rate shock scenario."""
        scenario = CustomScenario(
            name="Interest Rate Shock",
            description="Sudden and significant interest rate increase",
            scenario_type=ScenarioType.STRESS,
            severity=ScenarioSeverity.MODERATE
        )

        scenario.add_parameter(ScenarioParameter(
            name="interest_rate",
            variable_type="rate",
            base_value=0.02,
            shock_value=0.05,
            shock_type="absolute",
            description="Interest rate increase"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="bond_return",
            variable_type="return",
            base_value=0.0,
            shock_value=-0.15,
            shock_type="relative",
            description="Bond price decline"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="duration_risk",
            variable_type="risk",
            base_value=1.0,
            shock_value=1.5,
            shock_type="relative",
            description="Duration risk increase"
        ))

        return scenario

    @staticmethod
    def inflation_surge() -> CustomScenario:
        """High inflation scenario."""
        scenario = CustomScenario(
            name="Inflation Surge",
            description="Sustained high inflation environment",
            scenario_type=ScenarioType.STRESS,
            severity=ScenarioSeverity.MODERATE
        )

        scenario.add_parameter(ScenarioParameter(
            name="inflation_rate",
            variable_type="economic",
            base_value=0.02,
            shock_value=0.07,
            shock_type="absolute",
            description="High inflation"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="real_return",
            variable_type="return",
            base_value=0.0,
            shock_value=-0.05,
            shock_type="absolute",
            description="Negative real returns"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="commodity_return",
            variable_type="return",
            base_value=0.0,
            shock_value=0.25,
            shock_type="relative",
            description="Commodity price surge"
        ))

        return scenario

    @staticmethod
    def base_case_scenario() -> CustomScenario:
        """Standard base case scenario for normal market conditions."""
        scenario = CustomScenario(
            name="Base Case",
            description="Standard baseline scenario with normal market conditions",
            scenario_type=ScenarioType.BASELINE,
            severity=ScenarioSeverity.MILD
        )

        scenario.add_parameter(ScenarioParameter(
            name="revenue_growth",
            variable_type="growth",
            base_value=0.05,
            shock_value=0.0,  # No shock for base case
            shock_type="absolute",
            description="Steady revenue growth"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="discount_rate",
            variable_type="rate",
            base_value=0.10,
            shock_value=0.0,  # No shock for base case
            shock_type="absolute",
            description="Standard discount rate"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="operating_margin",
            variable_type="margin",
            base_value=0.20,
            shock_value=0.0,  # No shock for base case
            shock_type="absolute",
            description="Stable operating margins"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="terminal_growth",
            variable_type="growth",
            base_value=0.03,
            shock_value=0.0,  # No shock for base case
            shock_type="absolute",
            description="Long-term GDP growth"
        ))

        return scenario

    @staticmethod
    def optimistic_scenario() -> CustomScenario:
        """Optimistic scenario with favorable market conditions."""
        scenario = CustomScenario(
            name="Optimistic Case",
            description="Favorable scenario with strong growth and improving conditions",
            scenario_type=ScenarioType.OPTIMISTIC,
            severity=ScenarioSeverity.MILD,
            probability=0.25  # 25% probability of occurrence
        )

        scenario.add_parameter(ScenarioParameter(
            name="revenue_growth",
            variable_type="growth",
            base_value=0.05,
            shock_value=0.10,  # Adding 10% to base 5% = 15%
            shock_type="absolute",
            description="Strong revenue expansion"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="discount_rate",
            variable_type="rate",
            base_value=0.10,
            shock_value=-0.02,  # Lower discount rate (cheaper capital) - decrease from base
            shock_type="absolute",
            description="Lower cost of capital"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="operating_margin",
            variable_type="margin",
            base_value=0.20,
            shock_value=0.25,  # Improved margins
            shock_type="absolute",
            description="Operational efficiency gains"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="terminal_growth",
            variable_type="growth",
            base_value=0.03,
            shock_value=0.04,  # Higher long-term growth
            shock_type="absolute",
            description="Sustained economic expansion"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="market_multiple",
            variable_type="multiple",
            base_value=1.0,
            shock_value=1.2,  # Market re-rating
            shock_type="relative",
            description="Market multiple expansion"
        ))

        return scenario

    @staticmethod
    def pessimistic_scenario() -> CustomScenario:
        """Pessimistic scenario with challenging market conditions."""
        scenario = CustomScenario(
            name="Pessimistic Case",
            description="Challenging scenario with economic headwinds and market stress",
            scenario_type=ScenarioType.PESSIMISTIC,
            severity=ScenarioSeverity.MODERATE,
            probability=0.20  # 20% probability of occurrence
        )

        scenario.add_parameter(ScenarioParameter(
            name="revenue_growth",
            variable_type="growth",
            base_value=0.05,
            shock_value=-0.10,  # Subtracting 10% from base 5% = -5%
            shock_type="absolute",
            description="Revenue contraction"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="discount_rate",
            variable_type="rate",
            base_value=0.10,
            shock_value=0.12,  # Higher discount rate (expensive capital)
            shock_type="absolute",
            description="Higher cost of capital"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="operating_margin",
            variable_type="margin",
            base_value=0.20,
            shock_value=0.15,  # Compressed margins
            shock_type="absolute",
            description="Margin compression"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="terminal_growth",
            variable_type="growth",
            base_value=0.03,
            shock_value=0.02,  # Lower long-term growth
            shock_type="absolute",
            description="Slower economic growth"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="market_multiple",
            variable_type="multiple",
            base_value=1.0,
            shock_value=0.8,  # Market de-rating
            shock_type="relative",
            description="Market multiple contraction"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="credit_risk_premium",
            variable_type="spread",
            base_value=0.02,
            shock_value=0.05,  # Higher credit spreads
            shock_type="absolute",
            description="Increased credit risk"
        ))

        return scenario

    @staticmethod
    def economic_expansion_scenario() -> CustomScenario:
        """Economic expansion with strong GDP growth."""
        scenario = CustomScenario(
            name="Economic Expansion",
            description="Strong economic expansion with robust GDP growth and business investment",
            scenario_type=ScenarioType.OPTIMISTIC,
            severity=ScenarioSeverity.MILD
        )

        scenario.add_parameter(ScenarioParameter(
            name="gdp_growth",
            variable_type="economic",
            base_value=0.02,
            shock_value=0.05,
            shock_type="absolute",
            description="Strong GDP expansion"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="business_investment",
            variable_type="economic",
            base_value=0.03,
            shock_value=0.08,
            shock_type="absolute",
            description="High business investment"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="consumer_confidence",
            variable_type="index",
            base_value=100,
            shock_value=120,
            shock_type="absolute",
            description="High consumer confidence"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="employment_growth",
            variable_type="economic",
            base_value=0.02,
            shock_value=0.04,
            shock_type="absolute",
            description="Strong job creation"
        ))

        return scenario

    @staticmethod
    def stagflation_scenario() -> CustomScenario:
        """Stagflation scenario with high inflation and low growth."""
        scenario = CustomScenario(
            name="Stagflation",
            description="Stagflation environment with high inflation and economic stagnation",
            scenario_type=ScenarioType.STRESS,
            severity=ScenarioSeverity.SEVERE
        )

        scenario.add_parameter(ScenarioParameter(
            name="inflation_rate",
            variable_type="economic",
            base_value=0.02,
            shock_value=0.08,
            shock_type="absolute",
            description="High inflation"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="gdp_growth",
            variable_type="economic",
            base_value=0.02,
            shock_value=0.0,
            shock_type="absolute",
            description="Economic stagnation"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="interest_rate",
            variable_type="rate",
            base_value=0.02,
            shock_value=0.07,
            shock_type="absolute",
            description="High interest rates"
        ))

        scenario.add_parameter(ScenarioParameter(
            name="commodity_prices",
            variable_type="price",
            base_value=1.0,
            shock_value=1.5,
            shock_type="relative",
            description="Commodity price surge"
        ))

        return scenario

    @staticmethod
    def all_predefined_scenarios() -> List[CustomScenario]:
        """Get all predefined scenarios."""
        return [
            PredefinedScenarios.base_case_scenario(),
            PredefinedScenarios.optimistic_scenario(),
            PredefinedScenarios.pessimistic_scenario(),
            PredefinedScenarios.economic_expansion_scenario(),
            PredefinedScenarios.stagflation_scenario(),
            PredefinedScenarios.market_crash_2008(),
            PredefinedScenarios.covid_crash_2020(),
            PredefinedScenarios.recession_scenario(),
            PredefinedScenarios.interest_rate_shock(),
            PredefinedScenarios.inflation_surge()
        ]


class ScenarioModelingFramework:
    """
    Comprehensive scenario modeling framework for financial risk analysis.

    Provides tools for creating, analyzing, and applying scenarios to
    financial portfolios and individual assets for risk assessment.
    """

    def __init__(self):
        """Initialize scenario modeling framework."""
        self.scenarios: Dict[str, CustomScenario] = {}
        self.scenario_results: Dict[str, Dict[str, Any]] = {}

        # Load predefined scenarios
        self._load_predefined_scenarios()

        logger.info("Scenario Modeling Framework initialized")

    def _load_predefined_scenarios(self):
        """Load predefined scenarios into framework."""
        predefined = PredefinedScenarios.all_predefined_scenarios()
        for scenario in predefined:
            self.scenarios[scenario.name] = scenario

    def add_scenario(self, scenario: CustomScenario) -> None:
        """Add a custom scenario to the framework."""
        self.scenarios[scenario.name] = scenario
        logger.info(f"Added scenario: {scenario.name}")

    def remove_scenario(self, scenario_name: str) -> None:
        """Remove a scenario from the framework."""
        if scenario_name in self.scenarios:
            del self.scenarios[scenario_name]
            logger.info(f"Removed scenario: {scenario_name}")

    def get_scenario(self, scenario_name: str) -> Optional[CustomScenario]:
        """Get a scenario by name."""
        return self.scenarios.get(scenario_name)

    def list_scenarios(self) -> List[str]:
        """List all available scenario names."""
        return list(self.scenarios.keys())

    def run_scenario_analysis(
        self,
        scenario_names: List[str],
        portfolio_data: Optional[Dict[str, Any]] = None,
        monte_carlo_runs: int = 1000
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run comprehensive scenario analysis for specified scenarios.

        Args:
            scenario_names: List of scenario names to analyze
            portfolio_data: Portfolio data for analysis
            monte_carlo_runs: Number of Monte Carlo simulations per scenario

        Returns:
            Dictionary mapping scenario names to analysis results
        """
        logger.info(f"Running scenario analysis for {len(scenario_names)} scenarios")

        results = {}

        for scenario_name in scenario_names:
            if scenario_name not in self.scenarios:
                logger.warning(f"Scenario '{scenario_name}' not found, skipping")
                continue

            scenario = self.scenarios[scenario_name]

            # Run scenario analysis
            scenario_result = self._analyze_single_scenario(
                scenario,
                portfolio_data,
                monte_carlo_runs
            )

            results[scenario_name] = scenario_result

        self.scenario_results = results
        return results

    def _analyze_single_scenario(
        self,
        scenario: CustomScenario,
        portfolio_data: Optional[Dict[str, Any]],
        monte_carlo_runs: int
    ) -> Dict[str, Any]:
        """Analyze a single scenario with Monte Carlo simulation."""
        logger.info(f"Analyzing scenario: {scenario.name}")

        scenario_values_list = []
        portfolio_impacts = []

        # Run Monte Carlo simulations
        for run in range(monte_carlo_runs):
            scenario_values = scenario.generate_scenario_values(random_state=run)
            scenario_values_list.append(scenario_values)

            # Calculate portfolio impact if portfolio data provided
            if portfolio_data:
                portfolio_impact = self._calculate_portfolio_impact(scenario_values, portfolio_data)
                portfolio_impacts.append(portfolio_impact)

        # Aggregate results
        result = {
            'scenario_name': scenario.name,
            'scenario_type': scenario.scenario_type.value,
            'severity': scenario.severity.level,
            'runs': monte_carlo_runs,
            'parameter_statistics': self._calculate_parameter_statistics(scenario_values_list),
            'scenario_probability': scenario.probability
        }

        if portfolio_impacts:
            result['portfolio_analysis'] = self._analyze_portfolio_impacts(portfolio_impacts)

        return result

    def _calculate_portfolio_impact(
        self,
        scenario_values: Dict[str, float],
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate portfolio impact under scenario conditions."""
        # Simplified portfolio impact calculation
        # In practice, this would integrate with the portfolio framework
        impact = {
            'total_return': 0.0,
            'volatility_change': 0.0,
            'var_change': 0.0
        }

        # Apply scenario shocks to portfolio
        if 'equity_return' in scenario_values and 'equity_weight' in portfolio_data:
            equity_impact = scenario_values['equity_return'] * portfolio_data['equity_weight']
            impact['total_return'] += equity_impact

        if 'bond_return' in scenario_values and 'bond_weight' in portfolio_data:
            bond_impact = scenario_values['bond_return'] * portfolio_data['bond_weight']
            impact['total_return'] += bond_impact

        # Volatility impact
        if 'volatility' in scenario_values:
            base_volatility = portfolio_data.get('base_volatility', 0.15)
            impact['volatility_change'] = scenario_values['volatility'] - base_volatility

        return impact

    def _calculate_parameter_statistics(
        self,
        scenario_values_list: List[Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for scenario parameters across Monte Carlo runs."""
        if not scenario_values_list:
            return {}

        parameter_stats = {}
        all_params = set()
        for values in scenario_values_list:
            all_params.update(values.keys())

        for param in all_params:
            param_values = [values.get(param, 0) for values in scenario_values_list]
            parameter_stats[param] = {
                'mean': np.mean(param_values),
                'std': np.std(param_values),
                'min': np.min(param_values),
                'max': np.max(param_values),
                'p5': np.percentile(param_values, 5),
                'p95': np.percentile(param_values, 95)
            }

        return parameter_stats

    def _analyze_portfolio_impacts(
        self,
        portfolio_impacts: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """Analyze portfolio impacts across Monte Carlo runs."""
        impact_df = pd.DataFrame(portfolio_impacts)

        analysis = {}
        for column in impact_df.columns:
            values = impact_df[column].values
            analysis[column] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'var_95': np.percentile(values, 5),  # 5th percentile for loss
                'var_99': np.percentile(values, 1),
                'max_loss': np.min(values),
                'probability_of_loss': np.mean(values < 0)
            }

        return analysis

    def compare_scenarios(
        self,
        scenario_names: List[str],
        comparison_metrics: List[str] = None
    ) -> pd.DataFrame:
        """Compare multiple scenarios across key metrics."""
        if comparison_metrics is None:
            comparison_metrics = ['severity', 'probability', 'max_loss', 'var_95']

        comparison_data = []

        for scenario_name in scenario_names:
            if scenario_name not in self.scenario_results:
                logger.warning(f"No results for scenario '{scenario_name}'")
                continue

            result = self.scenario_results[scenario_name]
            scenario_data = {'scenario': scenario_name}

            # Add scenario properties
            scenario_data['severity'] = result.get('severity', 0)
            scenario_data['probability'] = result.get('scenario_probability', 0)

            # Add portfolio analysis metrics if available
            portfolio_analysis = result.get('portfolio_analysis', {})
            for metric in comparison_metrics:
                if metric in portfolio_analysis.get('total_return', {}):
                    scenario_data[metric] = portfolio_analysis['total_return'][metric]

            comparison_data.append(scenario_data)

        return pd.DataFrame(comparison_data)

    def export_scenarios(self, file_path: str, scenario_names: Optional[List[str]] = None) -> None:
        """Export scenarios to file for sharing or backup."""
        scenarios_to_export = scenario_names or list(self.scenarios.keys())

        export_data = {
            'scenarios': [
                self.scenarios[name].to_dict()
                for name in scenarios_to_export
                if name in self.scenarios
            ],
            'export_date': datetime.now().isoformat(),
            'framework_version': '1.0'
        }

        import json
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(export_data['scenarios'])} scenarios to {file_path}")

    def import_scenarios(self, file_path: str) -> List[str]:
        """Import scenarios from file."""
        import json
        with open(file_path, 'r') as f:
            import_data = json.load(f)

        imported_scenarios = []

        for scenario_dict in import_data.get('scenarios', []):
            scenario = self._dict_to_scenario(scenario_dict)
            self.scenarios[scenario.name] = scenario
            imported_scenarios.append(scenario.name)

        logger.info(f"Imported {len(imported_scenarios)} scenarios")
        return imported_scenarios

    def calculate_probability_weighted_valuation(
        self,
        scenario_names: List[str],
        valuation_function: callable,
        normalize_probabilities: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate probability-weighted expected valuation across scenarios.

        Args:
            scenario_names: List of scenario names to include
            valuation_function: Function that takes scenario parameters and returns valuation
            normalize_probabilities: Whether to normalize probabilities to sum to 1

        Returns:
            Dictionary containing weighted valuation metrics
        """
        logger.info(f"Calculating probability-weighted valuation for {len(scenario_names)} scenarios")

        scenario_valuations = []
        total_probability = 0

        # Calculate valuations for each scenario
        for scenario_name in scenario_names:
            if scenario_name not in self.scenarios:
                logger.warning(f"Scenario '{scenario_name}' not found, skipping")
                continue

            scenario = self.scenarios[scenario_name]
            scenario_values = scenario.generate_scenario_values()

            try:
                valuation = valuation_function(scenario_values)
                probability = scenario.probability or (1.0 / len(scenario_names))  # Equal weight if no probability

                scenario_valuations.append({
                    'name': scenario_name,
                    'valuation': valuation,
                    'probability': probability,
                    'scenario_type': scenario.scenario_type.value,
                    'severity': scenario.severity.level
                })

                total_probability += probability

            except Exception as e:
                logger.error(f"Failed to calculate valuation for scenario '{scenario_name}': {e}")
                continue

        if not scenario_valuations:
            raise ValueError("No valid scenario valuations calculated")

        # Normalize probabilities if requested
        if normalize_probabilities and total_probability > 0:
            for item in scenario_valuations:
                item['probability'] = item['probability'] / total_probability

        # Calculate weighted metrics
        expected_value = sum(item['valuation'] * item['probability'] for item in scenario_valuations)

        # Calculate weighted variance and other statistics
        weighted_variance = sum(
            item['probability'] * (item['valuation'] - expected_value) ** 2
            for item in scenario_valuations
        )
        weighted_std = np.sqrt(weighted_variance)

        # Probability-weighted percentiles (approximate)
        sorted_scenarios = sorted(scenario_valuations, key=lambda x: x['valuation'])
        cumulative_prob = 0
        percentiles = {}

        for p in [5, 25, 50, 75, 95]:
            target_prob = p / 100.0
            for item in sorted_scenarios:
                cumulative_prob += item['probability']
                if cumulative_prob >= target_prob:
                    percentiles[f'p{p}'] = item['valuation']
                    break

        result = {
            'expected_value': expected_value,
            'weighted_std': weighted_std,
            'weighted_variance': weighted_variance,
            'percentiles': percentiles,
            'scenario_details': scenario_valuations,
            'total_probability': sum(item['probability'] for item in scenario_valuations),
            'num_scenarios': len(scenario_valuations)
        }

        logger.info(f"Probability-weighted expected value: {expected_value:.2f}")
        return result

    def create_scenario_sensitivity_analysis(
        self,
        base_scenario_name: str,
        parameter_variations: Dict[str, List[float]],
        valuation_function: callable
    ) -> Dict[str, Any]:
        """
        Create sensitivity analysis by varying parameters around a base scenario.

        Args:
            base_scenario_name: Name of base scenario to vary
            parameter_variations: Dict mapping parameter names to list of variation values
            valuation_function: Function that calculates valuation from scenario parameters

        Returns:
            Dictionary containing sensitivity analysis results
        """
        logger.info(f"Creating sensitivity analysis for scenario: {base_scenario_name}")

        if base_scenario_name not in self.scenarios:
            raise ValueError(f"Base scenario '{base_scenario_name}' not found")

        base_scenario = self.scenarios[base_scenario_name]
        base_values = base_scenario.generate_scenario_values()
        base_valuation = valuation_function(base_values)

        sensitivity_results = {
            'base_scenario': base_scenario_name,
            'base_valuation': base_valuation,
            'parameter_sensitivities': {},
            'correlation_matrix': None
        }

        # Analyze sensitivity for each parameter
        for param_name, variation_values in parameter_variations.items():
            if param_name not in base_scenario.parameters:
                logger.warning(f"Parameter '{param_name}' not found in base scenario")
                continue

            param_results = {
                'base_value': base_values.get(param_name, 0),
                'variations': [],
                'elasticity': None
            }

            for variation_value in variation_values:
                # Create modified scenario values
                modified_values = base_values.copy()
                modified_values[param_name] = variation_value

                try:
                    modified_valuation = valuation_function(modified_values)

                    # Calculate percentage changes
                    param_change = (variation_value - param_results['base_value']) / param_results['base_value']
                    valuation_change = (modified_valuation - base_valuation) / base_valuation

                    param_results['variations'].append({
                        'parameter_value': variation_value,
                        'valuation': modified_valuation,
                        'param_change_pct': param_change * 100,
                        'valuation_change_pct': valuation_change * 100,
                        'elasticity': valuation_change / param_change if param_change != 0 else 0
                    })

                except Exception as e:
                    logger.debug(f"Failed to calculate variation for {param_name}={variation_value}: {e}")
                    continue

            # Calculate average elasticity
            elasticities = [v['elasticity'] for v in param_results['variations'] if abs(v['elasticity']) < 100]
            param_results['elasticity'] = np.mean(elasticities) if elasticities else 0

            sensitivity_results['parameter_sensitivities'][param_name] = param_results

        return sensitivity_results

    def generate_three_point_scenarios(
        self,
        base_parameters: Dict[str, float],
        parameter_ranges: Dict[str, Tuple[float, float]],
        scenario_names: Tuple[str, str, str] = ("Pessimistic", "Base", "Optimistic")
    ) -> List[CustomScenario]:
        """
        Generate three-point scenario analysis (pessimistic, base, optimistic).

        Args:
            base_parameters: Base case parameter values
            parameter_ranges: Dict mapping parameter names to (min, max) tuples
            scenario_names: Tuple of (pessimistic, base, optimistic) scenario names

        Returns:
            List of three CustomScenario objects
        """
        logger.info("Generating three-point scenario analysis")

        scenarios = []
        scenario_types = [ScenarioType.PESSIMISTIC, ScenarioType.BASELINE, ScenarioType.OPTIMISTIC]
        probabilities = [0.25, 0.50, 0.25]  # Standard probability weights

        for i, (name, scenario_type, probability) in enumerate(zip(scenario_names, scenario_types, probabilities)):
            scenario = CustomScenario(
                name=name,
                description=f"Generated {name.lower()} scenario for three-point analysis",
                scenario_type=scenario_type,
                probability=probability
            )

            for param_name, base_value in base_parameters.items():
                if param_name in parameter_ranges:
                    min_val, max_val = parameter_ranges[param_name]

                    # Calculate shock values: pessimistic uses min, base uses base, optimistic uses max
                    if i == 0:  # Pessimistic
                        shock_value = min_val
                    elif i == 1:  # Base
                        shock_value = base_value
                    else:  # Optimistic
                        shock_value = max_val

                    parameter = ScenarioParameter(
                        name=param_name,
                        variable_type="variable",
                        base_value=base_value,
                        shock_value=shock_value,
                        shock_type="absolute",
                        description=f"{name} case for {param_name}"
                    )
                    scenario.add_parameter(parameter)

            scenarios.append(scenario)
            self.scenarios[name] = scenario

        logger.info(f"Generated {len(scenarios)} three-point scenarios")
        return scenarios

    def _dict_to_scenario(self, scenario_dict: Dict[str, Any]) -> CustomScenario:
        """Convert dictionary to CustomScenario object."""
        scenario = CustomScenario(
            name=scenario_dict['name'],
            description=scenario_dict['description'],
            scenario_type=ScenarioType(scenario_dict['scenario_type']),
            severity=ScenarioSeverity(scenario_dict['severity'])
        )

        # Add parameters
        for param_name, param_dict in scenario_dict.get('parameters', {}).items():
            parameter = ScenarioParameter(
                name=param_dict['name'],
                variable_type=param_dict['variable_type'],
                base_value=param_dict['base_value'],
                shock_value=param_dict.get('shock_value'),
                shock_type=param_dict.get('shock_type', 'absolute'),
                distribution=param_dict.get('distribution', 'normal'),
                distribution_params=param_dict.get('distribution_params', {}),
                min_value=param_dict.get('min_value'),
                max_value=param_dict.get('max_value'),
                description=param_dict.get('description', '')
            )
            scenario.add_parameter(parameter)

        return scenario