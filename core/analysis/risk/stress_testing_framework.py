"""
Stress Testing Framework
========================

Comprehensive stress testing capabilities for extreme market conditions and tail risk analysis.
This module provides historical and hypothetical stress scenarios, regime-switching models,
and tail risk analysis using extreme value theory.

Key Features:
- Historical stress scenarios (2008 Financial Crisis, COVID-19, Dot-com Crash)
- Hypothetical extreme stress scenarios
- Regime-switching models for different market conditions
- Tail risk analysis with extreme value theory
- Stress test reporting and visualization
- Integration with existing risk and valuation frameworks

The stress testing framework is designed to assess portfolio and asset performance
under extreme adverse conditions that may not be captured by standard risk models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date, timedelta
import logging
from abc import ABC, abstractmethod

# Scientific computing imports
from scipy import stats
from scipy.optimize import minimize
import warnings

# Import existing framework components
from .scenario_modeling import ScenarioType, ScenarioSeverity
from .risk_metrics import RiskMetrics, RiskType
from .var_calculations import VaRCalculator
from ..statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult

logger = logging.getLogger(__name__)


class StressScenarioType(Enum):
    """Types of stress testing scenarios."""
    HISTORICAL_CRISIS = "historical_crisis"
    HYPOTHETICAL_EXTREME = "hypothetical_extreme"
    REGIME_SWITCH = "regime_switch"
    TAIL_RISK = "tail_risk"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    VOLATILITY_SPIKE = "volatility_spike"


class MarketRegime(Enum):
    """Different market regime types."""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    STAGNATION = "stagnation"


@dataclass
class StressScenarioDefinition:
    """Definition of a stress testing scenario."""
    name: str
    scenario_type: StressScenarioType
    severity: ScenarioSeverity
    description: str

    # Market parameter shocks
    equity_shock: float = 0.0  # Percentage shock to equity markets
    bond_shock: float = 0.0    # Percentage shock to bond markets
    volatility_multiplier: float = 1.0  # Volatility increase factor
    correlation_shift: float = 0.0  # Correlation increase (crisis correlation)

    # Economic parameter changes
    gdp_shock: float = 0.0
    inflation_shock: float = 0.0
    interest_rate_shock: float = 0.0
    credit_spread_shock: float = 0.0

    # Liquidity and other factors
    liquidity_shock: float = 0.0
    fx_shock: float = 0.0  # Currency shock
    commodity_shock: float = 0.0

    # Timing and duration
    duration_months: int = 6
    recovery_months: int = 12
    probability: float = 0.01  # Annual probability

    # Metadata
    historical_precedent: Optional[str] = None
    data_source: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)


@dataclass
class RegimeSwitchingModel:
    """Regime-switching model parameters."""
    regimes: List[MarketRegime]
    transition_matrix: np.ndarray  # Transition probabilities between regimes
    regime_parameters: Dict[MarketRegime, Dict[str, float]]  # Parameters for each regime
    current_regime: MarketRegime
    regime_probabilities: np.ndarray  # Current regime probabilities


@dataclass
class TailRiskMetrics:
    """Tail risk analysis results."""
    extreme_value_params: Dict[str, float]  # EVT distribution parameters
    tail_var_estimates: Dict[str, float]    # Tail VaR estimates
    tail_cvar_estimates: Dict[str, float]   # Tail CVaR estimates
    extreme_event_probability: float       # Probability of extreme events
    tail_index: float                      # Hill estimator or similar
    threshold: float                       # Threshold for tail analysis
    exceedances: pd.DataFrame              # Tail exceedances data
    gumbel_params: Optional[Tuple[float, float]] = None
    pareto_params: Optional[Tuple[float, float]] = None


@dataclass
class StressTestResult:
    """Results from stress testing analysis."""
    scenario_name: str
    scenario_definition: StressScenarioDefinition

    # Portfolio impact
    portfolio_value_impact: float = 0.0
    portfolio_return_impact: float = 0.0
    max_drawdown: float = 0.0
    time_to_recovery: Optional[int] = None

    # Risk metric changes
    var_change: Dict[str, float] = field(default_factory=dict)
    cvar_change: Dict[str, float] = field(default_factory=dict)
    volatility_change: float = 0.0
    correlation_change: float = 0.0

    # Asset-level impacts
    asset_impacts: Dict[str, float] = field(default_factory=dict)
    sector_impacts: Dict[str, float] = field(default_factory=dict)

    # Statistical significance
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    p_value: Optional[float] = None

    # Metadata
    calculation_date: datetime = field(default_factory=datetime.now)
    calculation_time: Optional[float] = None


class HistoricalStressScenarios:
    """Predefined historical stress scenarios."""

    @staticmethod
    def financial_crisis_2008() -> StressScenarioDefinition:
        """2008 Financial Crisis scenario."""
        return StressScenarioDefinition(
            name="Financial Crisis 2008",
            scenario_type=StressScenarioType.HISTORICAL_CRISIS,
            severity=ScenarioSeverity.EXTREME,
            description="Global financial crisis triggered by subprime mortgage collapse",
            equity_shock=-0.37,  # S&P 500 peak-to-trough decline
            bond_shock=0.20,     # Flight to quality
            volatility_multiplier=2.5,
            correlation_shift=0.3,  # Correlations increase during crisis
            gdp_shock=-0.026,
            credit_spread_shock=0.06,
            liquidity_shock=-0.4,
            duration_months=18,
            recovery_months=36,
            probability=0.02,
            historical_precedent="Sep 2008 - Mar 2009",
            data_source="Federal Reserve, BLS, S&P"
        )

    @staticmethod
    def covid19_pandemic() -> StressScenarioDefinition:
        """COVID-19 pandemic scenario."""
        return StressScenarioDefinition(
            name="COVID-19 Pandemic",
            scenario_type=StressScenarioType.HISTORICAL_CRISIS,
            severity=ScenarioSeverity.SEVERE,
            description="Global pandemic causing widespread economic disruption",
            equity_shock=-0.34,  # Initial market crash
            bond_shock=0.15,
            volatility_multiplier=3.0,
            correlation_shift=0.4,  # Very high correlation during crisis
            gdp_shock=-0.032,
            inflation_shock=-0.01,
            interest_rate_shock=-0.015,
            credit_spread_shock=0.04,
            liquidity_shock=-0.3,
            duration_months=3,
            recovery_months=18,
            probability=0.01,
            historical_precedent="Mar 2020 - May 2020",
            data_source="WHO, Federal Reserve, BEA"
        )

    @staticmethod
    def dotcom_crash() -> StressScenarioDefinition:
        """Dot-com bubble crash scenario."""
        return StressScenarioDefinition(
            name="Dot-com Crash",
            scenario_type=StressScenarioType.HISTORICAL_CRISIS,
            severity=ScenarioSeverity.SEVERE,
            description="Technology bubble burst and subsequent market decline",
            equity_shock=-0.49,  # NASDAQ peak-to-trough
            bond_shock=0.10,
            volatility_multiplier=2.0,
            correlation_shift=0.2,
            gdp_shock=-0.003,
            interest_rate_shock=-0.05,
            duration_months=30,
            recovery_months=60,
            probability=0.015,
            historical_precedent="Mar 2000 - Oct 2002",
            data_source="NASDAQ, Federal Reserve"
        )

    @staticmethod
    def black_monday_1987() -> StressScenarioDefinition:
        """Black Monday 1987 scenario."""
        return StressScenarioDefinition(
            name="Black Monday 1987",
            scenario_type=StressScenarioType.HISTORICAL_CRISIS,
            severity=ScenarioSeverity.EXTREME,
            description="Single-day market crash with extreme volatility",
            equity_shock=-0.22,  # Single day decline
            volatility_multiplier=5.0,
            correlation_shift=0.5,
            liquidity_shock=-0.6,
            duration_months=1,
            recovery_months=24,
            probability=0.005,
            historical_precedent="October 19, 1987",
            data_source="NYSE, Federal Reserve"
        )


class HypotheticalStressScenarios:
    """Hypothetical extreme stress scenarios."""

    @staticmethod
    def extreme_inflation() -> StressScenarioDefinition:
        """Extreme inflation scenario."""
        return StressScenarioDefinition(
            name="Extreme Inflation Shock",
            scenario_type=StressScenarioType.HYPOTHETICAL_EXTREME,
            severity=ScenarioSeverity.EXTREME,
            description="Sudden onset of extreme inflation due to monetary/fiscal policy",
            equity_shock=-0.25,
            bond_shock=-0.40,  # Bonds perform poorly in inflation
            volatility_multiplier=2.5,
            inflation_shock=0.08,  # 8 percentage point increase
            interest_rate_shock=0.06,
            credit_spread_shock=0.03,
            duration_months=12,
            recovery_months=36,
            probability=0.005
        )

    @staticmethod
    def geopolitical_crisis() -> StressScenarioDefinition:
        """Major geopolitical crisis scenario."""
        return StressScenarioDefinition(
            name="Geopolitical Crisis",
            scenario_type=StressScenarioType.HYPOTHETICAL_EXTREME,
            severity=ScenarioSeverity.SEVERE,
            description="Major geopolitical event causing global market disruption",
            equity_shock=-0.30,
            bond_shock=0.15,  # Flight to safety
            volatility_multiplier=3.0,
            correlation_shift=0.4,
            commodity_shock=0.50,  # Commodity price spike
            fx_shock=-0.15,
            liquidity_shock=-0.4,
            duration_months=6,
            recovery_months=24,
            probability=0.008
        )

    @staticmethod
    def cyber_attack() -> StressScenarioDefinition:
        """Major cyber attack on financial infrastructure."""
        return StressScenarioDefinition(
            name="Systemic Cyber Attack",
            scenario_type=StressScenarioType.HYPOTHETICAL_EXTREME,
            severity=ScenarioSeverity.EXTREME,
            description="Large-scale cyber attack on financial infrastructure",
            equity_shock=-0.20,
            volatility_multiplier=4.0,
            correlation_shift=0.6,  # Markets move together during crisis
            liquidity_shock=-0.8,  # Severe liquidity constraints
            duration_months=2,
            recovery_months=12,
            probability=0.003
        )


class ExtreemeValueAnalyzer:
    """Extreme Value Theory analysis for tail risk assessment."""

    def __init__(self, confidence_levels: List[float] = None):
        """Initialize extreme value analyzer."""
        self.confidence_levels = confidence_levels or [0.99, 0.995, 0.999]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze_tail_risk(
        self,
        returns: pd.Series,
        threshold_percentile: float = 0.95
    ) -> TailRiskMetrics:
        """
        Perform comprehensive tail risk analysis using Extreme Value Theory.

        Args:
            returns: Time series of returns
            threshold_percentile: Percentile for threshold selection

        Returns:
            TailRiskMetrics with comprehensive tail analysis
        """
        self.logger.info("Starting extreme value analysis")

        # Clean data
        returns_clean = returns.dropna()
        if len(returns_clean) < 100:
            raise ValueError("Insufficient data for extreme value analysis (minimum 100 observations)")

        # Determine threshold using percentile method
        threshold = np.percentile(np.abs(returns_clean), threshold_percentile * 100)

        # Extract exceedances (considering both tails)
        negative_exceedances = returns_clean[returns_clean <= -threshold]
        positive_exceedances = returns_clean[returns_clean >= threshold]
        all_exceedances = pd.concat([negative_exceedances, positive_exceedances])

        if len(all_exceedances) < 20:
            self.logger.warning("Few extreme observations for reliable EVT analysis")

        # Fit Generalized Pareto Distribution (GPD) to exceedances
        try:
            # Transform to positive values for GPD fitting
            excess_values = np.abs(all_exceedances) - threshold

            # Fit GPD using method of moments or MLE
            gpd_params = self._fit_gpd(excess_values)

            # Fit Gumbel distribution to block maxima
            gumbel_params = self._fit_gumbel_block_maxima(returns_clean)

            # Calculate tail VaR and CVaR estimates
            tail_var_estimates = {}
            tail_cvar_estimates = {}

            for conf_level in self.confidence_levels:
                tail_var = self._calculate_tail_var(threshold, gpd_params, conf_level, len(returns_clean))
                tail_cvar = self._calculate_tail_cvar(threshold, gpd_params, conf_level, len(returns_clean))

                tail_var_estimates[f"VaR_{conf_level}"] = tail_var
                tail_cvar_estimates[f"CVaR_{conf_level}"] = tail_cvar

            # Calculate Hill estimator for tail index
            tail_index = self._calculate_hill_estimator(returns_clean, len(all_exceedances))

            # Estimate extreme event probability
            extreme_prob = len(all_exceedances) / len(returns_clean)

            return TailRiskMetrics(
                extreme_value_params=gpd_params,
                tail_var_estimates=tail_var_estimates,
                tail_cvar_estimates=tail_cvar_estimates,
                extreme_event_probability=extreme_prob,
                tail_index=tail_index,
                threshold=threshold,
                exceedances=pd.DataFrame({
                    'date': all_exceedances.index,
                    'value': all_exceedances.values,
                    'excess': np.abs(all_exceedances.values) - threshold
                }),
                gumbel_params=gumbel_params,
                pareto_params=(gpd_params.get('shape', 0), gpd_params.get('scale', 1))
            )

        except Exception as e:
            self.logger.error(f"Extreme value analysis failed: {e}")
            # Return basic metrics if EVT fails
            return TailRiskMetrics(
                extreme_value_params={},
                tail_var_estimates={},
                tail_cvar_estimates={},
                extreme_event_probability=len(all_exceedances) / len(returns_clean),
                tail_index=0.0,
                threshold=threshold,
                exceedances=pd.DataFrame()
            )

    def _fit_gpd(self, excess_values: np.ndarray) -> Dict[str, float]:
        """Fit Generalized Pareto Distribution to exceedances."""
        try:
            # Method of moments estimator as initial guess
            mean_excess = np.mean(excess_values)
            var_excess = np.var(excess_values)

            # Initial parameter estimates
            shape_init = 0.5 * (1 - mean_excess**2 / var_excess)
            scale_init = 0.5 * mean_excess * (1 + mean_excess**2 / var_excess)

            # MLE estimation using scipy
            def neg_log_likelihood(params):
                shape, scale = params
                if scale <= 0:
                    return np.inf

                try:
                    if abs(shape) < 1e-6:  # Exponential case
                        return len(excess_values) * np.log(scale) + np.sum(excess_values) / scale
                    else:
                        log_terms = (1 + 1/shape) * np.sum(np.log(1 + shape * excess_values / scale))
                        return len(excess_values) * np.log(scale) + log_terms
                except:
                    return np.inf

            # Optimize
            result = minimize(
                neg_log_likelihood,
                x0=[shape_init, scale_init],
                method='L-BFGS-B',
                bounds=[(-0.5, 0.5), (0.01, None)]
            )

            if result.success:
                shape, scale = result.x
                return {'shape': shape, 'scale': scale, 'method': 'MLE'}
            else:
                # Fall back to method of moments
                return {'shape': shape_init, 'scale': scale_init, 'method': 'MoM'}

        except Exception as e:
            self.logger.warning(f"GPD fitting failed: {e}")
            return {'shape': 0.1, 'scale': np.std(excess_values), 'method': 'fallback'}

    def _fit_gumbel_block_maxima(self, returns: pd.Series, block_size: int = 252) -> Tuple[float, float]:
        """Fit Gumbel distribution to block maxima."""
        try:
            # Create blocks (e.g., annual blocks)
            blocks = [returns[i:i+block_size] for i in range(0, len(returns), block_size)]
            block_maxima = [np.max(np.abs(block)) if len(block) > 0 else 0 for block in blocks]
            block_maxima = [x for x in block_maxima if x > 0]

            if len(block_maxima) < 3:
                return (0.0, 1.0)

            # Fit Gumbel distribution
            loc, scale = stats.gumbel_r.fit(block_maxima)
            return (loc, scale)

        except Exception as e:
            self.logger.warning(f"Gumbel fitting failed: {e}")
            return (0.0, 1.0)

    def _calculate_tail_var(self, threshold: float, gpd_params: Dict[str, float],
                           confidence_level: float, n_observations: int) -> float:
        """Calculate tail VaR using GPD approximation."""
        try:
            shape = gpd_params.get('shape', 0.1)
            scale = gpd_params.get('scale', 1.0)

            # Number of exceedances
            n_u = n_observations * (1 - 0.95)  # Assuming 95th percentile threshold

            # Tail probability
            tail_prob = 1 - confidence_level

            # GPD quantile function
            if abs(shape) < 1e-6:  # Exponential distribution
                tail_var = threshold + scale * np.log(n_observations * tail_prob / n_u)
            else:
                tail_var = threshold + (scale / shape) * ((n_observations * tail_prob / n_u) ** (-shape) - 1)

            return abs(tail_var)

        except Exception as e:
            self.logger.warning(f"Tail VaR calculation failed: {e}")
            return threshold * 1.5

    def _calculate_tail_cvar(self, threshold: float, gpd_params: Dict[str, float],
                            confidence_level: float, n_observations: int) -> float:
        """Calculate tail CVaR (Expected Shortfall) using GPD."""
        try:
            shape = gpd_params.get('shape', 0.1)
            scale = gpd_params.get('scale', 1.0)

            # Calculate VaR first
            tail_var = self._calculate_tail_var(threshold, gpd_params, confidence_level, n_observations)

            # CVaR calculation depends on shape parameter
            if shape >= 1:
                # Undefined expected value
                return tail_var * 1.2

            if abs(shape) < 1e-6:  # Exponential case
                tail_cvar = tail_var + scale
            else:
                tail_cvar = tail_var / (1 - shape) + (scale - shape * threshold) / (1 - shape)

            return abs(tail_cvar)

        except Exception as e:
            self.logger.warning(f"Tail CVaR calculation failed: {e}")
            return self._calculate_tail_var(threshold, gpd_params, confidence_level, n_observations) * 1.1

    def _calculate_hill_estimator(self, returns: pd.Series, n_exceedances: int) -> float:
        """Calculate Hill estimator for tail index."""
        try:
            # Sort absolute returns in descending order
            sorted_returns = np.sort(np.abs(returns.dropna()))[::-1]

            # Use top n_exceedances for Hill estimator
            k = min(n_exceedances, len(sorted_returns) // 4)  # Use at most 25% of data

            if k < 5:
                return 0.5  # Default moderate tail index

            # Hill estimator
            log_ratios = np.log(sorted_returns[:k] / sorted_returns[k])
            hill_estimate = np.mean(log_ratios)

            # Tail index is 1/Hill estimate (for heavy-tailed distributions)
            tail_index = 1 / hill_estimate if hill_estimate > 0 else 2.0

            # Bound the estimate to reasonable range
            return max(0.1, min(tail_index, 5.0))

        except Exception as e:
            self.logger.warning(f"Hill estimator calculation failed: {e}")
            return 1.0


class RegimeSwitchingAnalyzer:
    """Regime-switching model for different market conditions."""

    def __init__(self, n_regimes: int = 3):
        """Initialize regime-switching analyzer."""
        self.n_regimes = n_regimes
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def fit_regime_model(
        self,
        returns: pd.Series,
        market_indicators: Optional[pd.DataFrame] = None
    ) -> RegimeSwitchingModel:
        """
        Fit regime-switching model to returns data.

        Args:
            returns: Time series of returns
            market_indicators: Additional market indicators for regime identification

        Returns:
            RegimeSwitchingModel with fitted parameters
        """
        self.logger.info("Fitting regime-switching model")

        # Simple implementation using volatility regimes
        # In practice, this could use more sophisticated HMM models

        # Calculate rolling volatility
        vol_window = 60  # 60-day rolling window
        rolling_vol = returns.rolling(vol_window).std() * np.sqrt(252)

        # Define regime thresholds based on volatility quantiles
        vol_quantiles = rolling_vol.dropna().quantile([0.33, 0.67])

        # Classify regimes
        regimes = []
        for vol in rolling_vol:
            if pd.isna(vol):
                regimes.append(MarketRegime.BULL_MARKET)  # Default
            elif vol <= vol_quantiles.iloc[0]:
                regimes.append(MarketRegime.LOW_VOLATILITY)
            elif vol <= vol_quantiles.iloc[1]:
                regimes.append(MarketRegime.BULL_MARKET)
            else:
                regimes.append(MarketRegime.HIGH_VOLATILITY)

        # Calculate transition matrix
        transition_matrix = self._calculate_transition_matrix(regimes)

        # Calculate regime parameters
        regime_params = self._calculate_regime_parameters(returns, regimes)

        # Current regime (most recent)
        current_regime = regimes[-1] if regimes else MarketRegime.BULL_MARKET

        # Current regime probabilities (simplified)
        regime_probs = np.array([0.4, 0.4, 0.2])  # Low vol, bull, high vol

        return RegimeSwitchingModel(
            regimes=[MarketRegime.LOW_VOLATILITY, MarketRegime.BULL_MARKET, MarketRegime.HIGH_VOLATILITY],
            transition_matrix=transition_matrix,
            regime_parameters=regime_params,
            current_regime=current_regime,
            regime_probabilities=regime_probs
        )

    def _calculate_transition_matrix(self, regimes: List[MarketRegime]) -> np.ndarray:
        """Calculate transition probability matrix between regimes."""
        unique_regimes = list(set(regimes))
        n = len(unique_regimes)
        transition_matrix = np.zeros((n, n))

        # Count transitions
        for i in range(len(regimes) - 1):
            current_idx = unique_regimes.index(regimes[i])
            next_idx = unique_regimes.index(regimes[i + 1])
            transition_matrix[current_idx, next_idx] += 1

        # Convert to probabilities
        for i in range(n):
            row_sum = transition_matrix[i, :].sum()
            if row_sum > 0:
                transition_matrix[i, :] /= row_sum
            else:
                transition_matrix[i, i] = 1.0  # Stay in same regime if no transitions

        return transition_matrix

    def _calculate_regime_parameters(
        self,
        returns: pd.Series,
        regimes: List[MarketRegime]
    ) -> Dict[MarketRegime, Dict[str, float]]:
        """Calculate statistical parameters for each regime."""
        regime_params = {}

        returns_array = returns.values
        unique_regimes = list(set(regimes))

        for regime in unique_regimes:
            # Get returns for this regime
            regime_mask = [r == regime for r in regimes]
            regime_returns = returns_array[regime_mask]

            if len(regime_returns) > 5:
                params = {
                    'mean': np.mean(regime_returns),
                    'std': np.std(regime_returns),
                    'skewness': stats.skew(regime_returns) if len(regime_returns) > 3 else 0,
                    'kurtosis': stats.kurtosis(regime_returns) if len(regime_returns) > 3 else 0,
                    'min': np.min(regime_returns),
                    'max': np.max(regime_returns),
                    'duration': len(regime_returns)
                }
            else:
                # Default parameters if insufficient data
                params = {
                    'mean': 0.0,
                    'std': 0.15,
                    'skewness': 0.0,
                    'kurtosis': 0.0,
                    'min': -0.1,
                    'max': 0.1,
                    'duration': 1
                }

            regime_params[regime] = params

        return regime_params


class StressTestingFramework:
    """
    Comprehensive stress testing framework for extreme market conditions.

    This framework integrates historical scenarios, hypothetical stress tests,
    regime-switching models, and extreme value analysis to provide comprehensive
    stress testing capabilities.
    """

    def __init__(
        self,
        financial_calculator=None,
        monte_carlo_engine: Optional[MonteCarloEngine] = None,
        var_calculator: Optional[VaRCalculator] = None
    ):
        """Initialize stress testing framework."""
        self.financial_calculator = financial_calculator
        self.monte_carlo_engine = monte_carlo_engine or MonteCarloEngine(financial_calculator)
        self.var_calculator = var_calculator or VaRCalculator()

        # Initialize analyzers
        self.evt_analyzer = ExtreemeValueAnalyzer()
        self.regime_analyzer = RegimeSwitchingAnalyzer()

        # Predefined scenarios
        self.historical_scenarios = self._load_historical_scenarios()
        self.hypothetical_scenarios = self._load_hypothetical_scenarios()

        # Results cache
        self.stress_test_cache: Dict[str, StressTestResult] = {}

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Stress Testing Framework initialized")

    def _load_historical_scenarios(self) -> Dict[str, StressScenarioDefinition]:
        """Load predefined historical stress scenarios."""
        return {
            "financial_crisis_2008": HistoricalStressScenarios.financial_crisis_2008(),
            "covid19_pandemic": HistoricalStressScenarios.covid19_pandemic(),
            "dotcom_crash": HistoricalStressScenarios.dotcom_crash(),
            "black_monday_1987": HistoricalStressScenarios.black_monday_1987()
        }

    def _load_hypothetical_scenarios(self) -> Dict[str, StressScenarioDefinition]:
        """Load predefined hypothetical stress scenarios."""
        return {
            "extreme_inflation": HypotheticalStressScenarios.extreme_inflation(),
            "geopolitical_crisis": HypotheticalStressScenarios.geopolitical_crisis(),
            "cyber_attack": HypotheticalStressScenarios.cyber_attack()
        }

    def run_comprehensive_stress_test(
        self,
        portfolio_data: Optional[Dict[str, Any]] = None,
        asset_returns: Optional[pd.Series] = None,
        scenarios: Optional[List[str]] = None,
        include_tail_analysis: bool = True,
        include_regime_analysis: bool = True
    ) -> Dict[str, StressTestResult]:
        """
        Run comprehensive stress testing analysis.

        Args:
            portfolio_data: Portfolio composition and characteristics
            asset_returns: Historical returns for analysis
            scenarios: List of scenario names to test (None = all scenarios)
            include_tail_analysis: Whether to include extreme value analysis
            include_regime_analysis: Whether to include regime-switching analysis

        Returns:
            Dictionary of stress test results by scenario name
        """
        self.logger.info("Starting comprehensive stress test")

        # Determine which scenarios to run
        if scenarios is None:
            test_scenarios = {**self.historical_scenarios, **self.hypothetical_scenarios}
        else:
            test_scenarios = {}
            for scenario_name in scenarios:
                if scenario_name in self.historical_scenarios:
                    test_scenarios[scenario_name] = self.historical_scenarios[scenario_name]
                elif scenario_name in self.hypothetical_scenarios:
                    test_scenarios[scenario_name] = self.hypothetical_scenarios[scenario_name]
                else:
                    self.logger.warning(f"Unknown scenario: {scenario_name}")

        results = {}

        # Run scenario-based stress tests
        for scenario_name, scenario_def in test_scenarios.items():
            try:
                self.logger.info(f"Running stress test: {scenario_name}")
                result = self._run_single_stress_test(scenario_def, portfolio_data, asset_returns)
                results[scenario_name] = result
                self.stress_test_cache[scenario_name] = result
            except Exception as e:
                self.logger.error(f"Stress test failed for {scenario_name}: {e}")

        # Add tail risk analysis if requested
        if include_tail_analysis and asset_returns is not None:
            try:
                tail_result = self._run_tail_risk_stress_test(asset_returns, portfolio_data)
                results["tail_risk_analysis"] = tail_result
                self.stress_test_cache["tail_risk_analysis"] = tail_result
            except Exception as e:
                self.logger.error(f"Tail risk analysis failed: {e}")

        # Add regime-switching analysis if requested
        if include_regime_analysis and asset_returns is not None:
            try:
                regime_result = self._run_regime_switching_stress_test(asset_returns, portfolio_data)
                results["regime_switching"] = regime_result
                self.stress_test_cache["regime_switching"] = regime_result
            except Exception as e:
                self.logger.error(f"Regime switching analysis failed: {e}")

        self.logger.info(f"Comprehensive stress test completed. {len(results)} scenarios analyzed.")
        return results

    def _run_single_stress_test(
        self,
        scenario: StressScenarioDefinition,
        portfolio_data: Optional[Dict[str, Any]],
        asset_returns: Optional[pd.Series]
    ) -> StressTestResult:
        """Run stress test for a single scenario."""
        start_time = datetime.now()

        # Initialize result
        result = StressTestResult(
            scenario_name=scenario.name,
            scenario_definition=scenario
        )

        # Apply scenario shocks to portfolio/asset
        if portfolio_data:
            portfolio_impact = self._calculate_portfolio_impact(scenario, portfolio_data)
            result.portfolio_value_impact = portfolio_impact.get('value_change', 0.0)
            result.portfolio_return_impact = portfolio_impact.get('return_change', 0.0)
            result.asset_impacts = portfolio_impact.get('asset_impacts', {})
            result.sector_impacts = portfolio_impact.get('sector_impacts', {})

        # Calculate risk metric changes
        if asset_returns is not None:
            risk_changes = self._calculate_risk_metric_changes(scenario, asset_returns)
            result.var_change = risk_changes.get('var_change', {})
            result.cvar_change = risk_changes.get('cvar_change', {})
            result.volatility_change = risk_changes.get('volatility_change', 0.0)
            result.correlation_change = risk_changes.get('correlation_change', 0.0)

        # Calculate maximum drawdown and recovery time
        result.max_drawdown = self._estimate_max_drawdown(scenario)
        result.time_to_recovery = self._estimate_recovery_time(scenario)

        # Statistical significance testing
        result.confidence_interval = self._calculate_confidence_interval(scenario, asset_returns)

        # Record calculation time
        end_time = datetime.now()
        result.calculation_time = (end_time - start_time).total_seconds()

        return result

    def _calculate_portfolio_impact(
        self,
        scenario: StressScenarioDefinition,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate portfolio impact under stress scenario."""
        # Get portfolio composition
        equity_weight = portfolio_data.get('equity_weight', 0.6)
        bond_weight = portfolio_data.get('bond_weight', 0.3)
        cash_weight = portfolio_data.get('cash_weight', 0.1)

        # Apply scenario shocks
        equity_impact = equity_weight * scenario.equity_shock
        bond_impact = bond_weight * scenario.bond_shock

        # Total portfolio impact
        total_impact = equity_impact + bond_impact  # Cash assumed stable

        # Asset-level impacts (simplified)
        asset_impacts = {}
        if 'holdings' in portfolio_data:
            for holding in portfolio_data['holdings']:
                asset_id = holding.get('asset_id', 'unknown')
                weight = holding.get('weight', 0.0)
                asset_type = holding.get('asset_type', 'equity')

                if asset_type == 'equity':
                    asset_impacts[asset_id] = weight * scenario.equity_shock
                elif asset_type == 'bond':
                    asset_impacts[asset_id] = weight * scenario.bond_shock
                else:
                    asset_impacts[asset_id] = 0.0

        # Sector impacts (placeholder)
        sector_impacts = {
            'financial': scenario.equity_shock * 1.2,  # Financial sector more sensitive
            'technology': scenario.equity_shock * 1.1,
            'utilities': scenario.equity_shock * 0.8,
            'consumer_staples': scenario.equity_shock * 0.9
        }

        return {
            'value_change': total_impact,
            'return_change': total_impact,
            'asset_impacts': asset_impacts,
            'sector_impacts': sector_impacts
        }

    def _calculate_risk_metric_changes(
        self,
        scenario: StressScenarioDefinition,
        asset_returns: pd.Series
    ) -> Dict[str, Any]:
        """Calculate changes in risk metrics under stress scenario."""
        # Calculate baseline VaR
        baseline_var = {
            'var_95': np.percentile(asset_returns, 5),
            'var_99': np.percentile(asset_returns, 1)
        }

        # Apply volatility multiplier to simulate stressed returns
        stressed_returns = asset_returns * scenario.volatility_multiplier

        # Calculate stressed VaR
        stressed_var = {
            'var_95': np.percentile(stressed_returns, 5),
            'var_99': np.percentile(stressed_returns, 1)
        }

        # Calculate changes
        var_change = {
            'var_95_change': stressed_var['var_95'] - baseline_var['var_95'],
            'var_99_change': stressed_var['var_99'] - baseline_var['var_99']
        }

        # CVaR changes
        baseline_cvar_95 = asset_returns[asset_returns <= baseline_var['var_95']].mean()
        stressed_cvar_95 = stressed_returns[stressed_returns <= stressed_var['var_95']].mean()

        cvar_change = {
            'cvar_95_change': stressed_cvar_95 - baseline_cvar_95
        }

        # Volatility change
        baseline_vol = asset_returns.std()
        stressed_vol = stressed_returns.std()
        volatility_change = (stressed_vol - baseline_vol) / baseline_vol

        return {
            'var_change': var_change,
            'cvar_change': cvar_change,
            'volatility_change': volatility_change,
            'correlation_change': scenario.correlation_shift
        }

    def _estimate_max_drawdown(self, scenario: StressScenarioDefinition) -> float:
        """Estimate maximum drawdown for scenario."""
        # Simple heuristic based on scenario parameters
        base_drawdown = abs(scenario.equity_shock)

        # Adjust for volatility and duration
        volatility_adjustment = (scenario.volatility_multiplier - 1) * 0.1
        duration_adjustment = min(scenario.duration_months / 12, 1.0) * 0.1

        max_drawdown = base_drawdown + volatility_adjustment + duration_adjustment
        return min(max_drawdown, 0.8)  # Cap at 80%

    def _estimate_recovery_time(self, scenario: StressScenarioDefinition) -> int:
        """Estimate recovery time in months."""
        # Use scenario recovery time as base
        base_recovery = scenario.recovery_months

        # Adjust based on severity and market factors
        if scenario.severity == ScenarioSeverity.EXTREME:
            return int(base_recovery * 1.2)
        elif scenario.severity == ScenarioSeverity.CATASTROPHIC:
            return int(base_recovery * 1.5)
        else:
            return base_recovery

    def _calculate_confidence_interval(
        self,
        scenario: StressScenarioDefinition,
        asset_returns: Optional[pd.Series],
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for scenario impact."""
        if asset_returns is None:
            # Use scenario-based estimate
            base_impact = abs(scenario.equity_shock)
            margin = base_impact * 0.2  # 20% margin
            return (base_impact - margin, base_impact + margin)

        # Bootstrap confidence interval
        n_bootstrap = 1000
        bootstrap_impacts = []

        for _ in range(n_bootstrap):
            # Sample with replacement
            sample_returns = asset_returns.sample(len(asset_returns), replace=True)

            # Apply scenario shock
            shocked_returns = sample_returns * (1 + scenario.equity_shock)
            sample_impact = (shocked_returns.mean() - asset_returns.mean()) / asset_returns.std()
            bootstrap_impacts.append(sample_impact)

        # Calculate percentiles
        alpha = (1 - confidence_level) / 2
        lower = np.percentile(bootstrap_impacts, alpha * 100)
        upper = np.percentile(bootstrap_impacts, (1 - alpha) * 100)

        return (lower, upper)

    def _run_tail_risk_stress_test(
        self,
        asset_returns: pd.Series,
        portfolio_data: Optional[Dict[str, Any]]
    ) -> StressTestResult:
        """Run stress test based on extreme value analysis."""
        # Perform tail risk analysis
        tail_metrics = self.evt_analyzer.analyze_tail_risk(asset_returns)

        # Create tail risk scenario
        tail_scenario = StressScenarioDefinition(
            name="Tail Risk Analysis",
            scenario_type=StressScenarioType.TAIL_RISK,
            severity=ScenarioSeverity.EXTREME,
            description="Extreme tail event based on historical return distribution",
            equity_shock=-tail_metrics.tail_var_estimates.get("VaR_0.999", 0.1),
            volatility_multiplier=2.0,
            correlation_shift=0.5,
            duration_months=3,
            recovery_months=18,
            probability=tail_metrics.extreme_event_probability
        )

        # Run stress test with tail scenario
        result = self._run_single_stress_test(tail_scenario, portfolio_data, asset_returns)

        # Add tail-specific metrics
        result.scenario_definition = tail_scenario

        return result

    def _run_regime_switching_stress_test(
        self,
        asset_returns: pd.Series,
        portfolio_data: Optional[Dict[str, Any]]
    ) -> StressTestResult:
        """Run stress test based on regime-switching analysis."""
        # Fit regime-switching model
        regime_model = self.regime_analyzer.fit_regime_model(asset_returns)

        # Find worst-case regime
        worst_regime = None
        worst_mean = float('inf')

        for regime, params in regime_model.regime_parameters.items():
            if params['mean'] < worst_mean:
                worst_mean = params['mean']
                worst_regime = regime

        if worst_regime is None:
            worst_regime = MarketRegime.CRISIS
            worst_params = {'mean': -0.02, 'std': 0.25}
        else:
            worst_params = regime_model.regime_parameters[worst_regime]

        # Create regime-based scenario
        regime_scenario = StressScenarioDefinition(
            name=f"Regime Switch to {worst_regime.value.title()}",
            scenario_type=StressScenarioType.REGIME_SWITCH,
            severity=ScenarioSeverity.SEVERE,
            description=f"Market regime switch to {worst_regime.value} conditions",
            equity_shock=worst_params['mean'] * 12,  # Annualized
            volatility_multiplier=worst_params['std'] / asset_returns.std(),
            duration_months=6,
            recovery_months=12,
            probability=0.05
        )

        # Run stress test with regime scenario
        result = self._run_single_stress_test(regime_scenario, portfolio_data, asset_returns)

        return result

    def get_scenario_summary(self) -> pd.DataFrame:
        """Get summary of all available stress scenarios."""
        all_scenarios = {**self.historical_scenarios, **self.hypothetical_scenarios}

        summary_data = []
        for name, scenario in all_scenarios.items():
            summary_data.append({
                'Scenario': name,
                'Type': scenario.scenario_type.value,
                'Severity': scenario.severity.value[1],
                'Equity Shock': f"{scenario.equity_shock:.1%}",
                'Duration (months)': scenario.duration_months,
                'Annual Probability': f"{scenario.probability:.1%}",
                'Description': scenario.description[:50] + "..." if len(scenario.description) > 50 else scenario.description
            })

        return pd.DataFrame(summary_data)

    def generate_stress_test_report(
        self,
        stress_results: Dict[str, StressTestResult],
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive stress test report."""
        report = {
            'executive_summary': {
                'total_scenarios': len(stress_results),
                'analysis_date': datetime.now().isoformat(),
                'worst_case_scenario': None,
                'maximum_loss': 0.0,
                'scenarios_tested': list(stress_results.keys())
            },
            'scenario_results': {},
            'risk_ranking': [],
            'recommendations': []
        }

        # Find worst case scenario
        worst_loss = 0
        worst_scenario = None

        for scenario_name, result in stress_results.items():
            loss = abs(result.portfolio_value_impact)
            if loss > worst_loss:
                worst_loss = loss
                worst_scenario = scenario_name

        report['executive_summary']['worst_case_scenario'] = worst_scenario
        report['executive_summary']['maximum_loss'] = worst_loss

        # Scenario results summary
        for scenario_name, result in stress_results.items():
            report['scenario_results'][scenario_name] = {
                'portfolio_impact': result.portfolio_value_impact,
                'max_drawdown': result.max_drawdown,
                'recovery_time': result.time_to_recovery,
                'severity': result.scenario_definition.severity.value[1],
                'probability': result.scenario_definition.probability
            }

        # Risk ranking
        ranked_scenarios = sorted(
            stress_results.items(),
            key=lambda x: abs(x[1].portfolio_value_impact),
            reverse=True
        )

        for i, (scenario_name, result) in enumerate(ranked_scenarios[:5]):
            report['risk_ranking'].append({
                'rank': i + 1,
                'scenario': scenario_name,
                'impact': result.portfolio_value_impact,
                'probability': result.scenario_definition.probability
            })

        # Recommendations
        if worst_loss > 0.2:  # More than 20% loss
            report['recommendations'].append("Consider reducing portfolio risk exposure")

        if any(result.time_to_recovery and result.time_to_recovery > 24 for result in stress_results.values()):
            report['recommendations'].append("Long recovery times indicate need for liquidity buffers")

        high_prob_scenarios = [
            name for name, result in stress_results.items()
            if result.scenario_definition.probability > 0.01 and abs(result.portfolio_value_impact) > 0.1
        ]

        if high_prob_scenarios:
            report['recommendations'].append(f"High-probability scenarios with significant impact: {', '.join(high_prob_scenarios)}")

        return report

    def export_stress_results(
        self,
        stress_results: Dict[str, StressTestResult],
        file_path: str,
        format: str = 'json'
    ) -> None:
        """Export stress test results to file."""
        if format.lower() == 'json':
            import json
            export_data = {}
            for name, result in stress_results.items():
                export_data[name] = {
                    'scenario_name': result.scenario_name,
                    'portfolio_impact': result.portfolio_value_impact,
                    'max_drawdown': result.max_drawdown,
                    'recovery_time': result.time_to_recovery,
                    'var_changes': result.var_change,
                    'calculation_date': result.calculation_date.isoformat(),
                    'scenario_definition': {
                        'type': result.scenario_definition.scenario_type.value,
                        'severity': result.scenario_definition.severity.value[1],
                        'equity_shock': result.scenario_definition.equity_shock,
                        'duration': result.scenario_definition.duration_months,
                        'probability': result.scenario_definition.probability
                    }
                }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)

        elif format.lower() == 'csv':
            # Convert to DataFrame and save as CSV
            summary_data = []
            for name, result in stress_results.items():
                summary_data.append({
                    'Scenario': name,
                    'Portfolio_Impact': result.portfolio_value_impact,
                    'Max_Drawdown': result.max_drawdown,
                    'Recovery_Time_Months': result.time_to_recovery,
                    'Severity': result.scenario_definition.severity.value[1],
                    'Probability': result.scenario_definition.probability,
                    'Equity_Shock': result.scenario_definition.equity_shock,
                    'Duration_Months': result.scenario_definition.duration_months
                })

            df = pd.DataFrame(summary_data)
            df.to_csv(file_path, index=False)

        self.logger.info(f"Stress test results exported to {file_path}")


# Convenience function for quick stress testing
def run_quick_stress_test(
    asset_returns: pd.Series,
    scenarios: Optional[List[str]] = None,
    financial_calculator=None
) -> Dict[str, StressTestResult]:
    """
    Convenience function for quick stress testing.

    Args:
        asset_returns: Historical returns data
        scenarios: List of scenarios to test (None = default set)
        financial_calculator: Optional financial calculator instance

    Returns:
        Dictionary of stress test results
    """
    framework = StressTestingFramework(financial_calculator=financial_calculator)

    # Default scenarios for quick testing
    if scenarios is None:
        scenarios = ["financial_crisis_2008", "covid19_pandemic", "extreme_inflation"]

    return framework.run_comprehensive_stress_test(
        asset_returns=asset_returns,
        scenarios=scenarios,
        include_tail_analysis=True,
        include_regime_analysis=False  # Skip regime analysis for speed
    )