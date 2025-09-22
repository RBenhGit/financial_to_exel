"""
Risk Type Models and Specialized Risk Analysis
==============================================

This module provides specialized risk analysis models for different types of financial risks,
including market risk, credit risk, operational risk, and liquidity risk. Each risk type
has specialized metrics, models, and analysis techniques.

Key Features:
- Market risk modeling (price volatility, beta, correlation)
- Credit risk assessment (default probability, credit spreads, ratings)
- Operational risk quantification (process failures, human error, fraud)
- Liquidity risk analysis (bid-ask spreads, volume, market depth)
- Interest rate risk modeling (duration, convexity, yield curve)
- Currency risk assessment (exchange rate volatility, correlation)
- Commodity risk analysis (price volatility, basis risk, storage costs)

Classes:
--------
RiskTypeAnalyzer: Base class for specialized risk analysis
MarketRiskAnalyzer: Market risk analysis and modeling
CreditRiskAnalyzer: Credit risk assessment and modeling
OperationalRiskAnalyzer: Operational risk quantification
LiquidityRiskAnalyzer: Liquidity risk analysis
IntegratedRiskTypeFramework: Unified framework for all risk types

Usage Example:
--------------
>>> from core.analysis.risk.risk_type_models import IntegratedRiskTypeFramework
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize risk framework
>>> calc = FinancialCalculator('AAPL')
>>> risk_framework = IntegratedRiskTypeFramework(calc)
>>>
>>> # Analyze market risk
>>> market_risk = risk_framework.analyze_market_risk('AAPL')
>>> print(f"Market Beta: {market_risk.beta}")
>>> print(f"VaR 95%: {market_risk.var_95}")
>>>
>>> # Analyze credit risk
>>> credit_risk = risk_framework.analyze_credit_risk('AAPL')
>>> print(f"Credit Score: {credit_risk.credit_score}")
>>> print(f"Default Probability: {credit_risk.default_probability}")
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from scipy import stats
from scipy.optimize import minimize_scalar
import warnings

# Import base risk components
from .risk_metrics import RiskType, RiskLevel, RiskMetrics
from .probability_distributions import DistributionFitter, ProbabilityDistribution

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class MarketRiskFactor(Enum):
    """Market risk factors for analysis."""
    EQUITY_RISK = "equity_risk"
    INTEREST_RATE_RISK = "interest_rate_risk"
    CURRENCY_RISK = "currency_risk"
    COMMODITY_RISK = "commodity_risk"
    VOLATILITY_RISK = "volatility_risk"
    CORRELATION_RISK = "correlation_risk"
    CONCENTRATION_RISK = "concentration_risk"


class CreditRiskLevel(Enum):
    """Credit risk levels and ratings mapping."""
    AAA = ("AAA", 1, 0.0001)     # (Rating, Level, Default Probability)
    AA = ("AA", 2, 0.0003)
    A = ("A", 3, 0.0010)
    BBB = ("BBB", 4, 0.0050)
    BB = ("BB", 5, 0.0200)
    B = ("B", 6, 0.0800)
    CCC = ("CCC", 7, 0.2000)
    CC = ("CC", 8, 0.4000)
    C = ("C", 9, 0.6000)
    D = ("D", 10, 1.0000)

    def __init__(self, rating: str, level: int, default_prob: float):
        self.rating = rating
        self.level = level
        self.default_prob = default_prob


class LiquidityRiskMetric(Enum):
    """Liquidity risk metrics."""
    BID_ASK_SPREAD = "bid_ask_spread"
    MARKET_IMPACT = "market_impact"
    VOLUME_RISK = "volume_risk"
    TIME_TO_LIQUIDATE = "time_to_liquidate"
    FUNDING_LIQUIDITY = "funding_liquidity"
    MARKET_DEPTH = "market_depth"


@dataclass
class MarketRiskResult:
    """
    Comprehensive market risk analysis result.

    Contains all market risk metrics, factor exposures, and risk decomposition
    for individual assets or portfolios.
    """
    asset_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Core market risk metrics
    beta: Optional[float] = None
    alpha: Optional[float] = None
    r_squared: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None

    # Volatility metrics
    realized_volatility: Optional[float] = None
    implied_volatility: Optional[float] = None
    volatility_risk_premium: Optional[float] = None

    # Value at Risk metrics
    var_1day_95: Optional[float] = None
    var_1day_99: Optional[float] = None
    var_10day_95: Optional[float] = None
    expected_shortfall_95: Optional[float] = None

    # Factor exposures
    factor_exposures: Dict[MarketRiskFactor, float] = field(default_factory=dict)
    factor_contributions: Dict[MarketRiskFactor, float] = field(default_factory=dict)

    # Risk decomposition
    systematic_risk: Optional[float] = None
    idiosyncratic_risk: Optional[float] = None
    total_risk: Optional[float] = None

    # Stress testing
    stress_test_results: Dict[str, float] = field(default_factory=dict)

    # Risk attribution
    risk_contributions: Dict[str, float] = field(default_factory=dict)

    def market_risk_score(self) -> float:
        """Calculate overall market risk score (0-100)."""
        components = []

        # Beta contribution (25% weight)
        if self.beta is not None:
            beta_score = min(abs(self.beta) * 30, 100)
            components.append(('beta', beta_score, 0.25))

        # Volatility contribution (30% weight)
        if self.realized_volatility is not None:
            vol_score = min(self.realized_volatility * 100, 100)
            components.append(('volatility', vol_score, 0.30))

        # VaR contribution (25% weight)
        if self.var_1day_95 is not None:
            var_score = min(abs(self.var_1day_95) * 100, 100)
            components.append(('var', var_score, 0.25))

        # Tracking error contribution (20% weight)
        if self.tracking_error is not None:
            te_score = min(self.tracking_error * 100, 100)
            components.append(('tracking_error', te_score, 0.20))

        if not components:
            return 50.0

        total_score = sum(score * weight for _, score, weight in components)
        total_weight = sum(weight for _, _, weight in components)

        return total_score / total_weight if total_weight > 0 else 50.0


@dataclass
class CreditRiskResult:
    """
    Comprehensive credit risk analysis result.

    Contains credit risk metrics, ratings, default probabilities,
    and credit spread analysis for individual entities.
    """
    entity_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Credit ratings and scores
    credit_rating: Optional[str] = None
    credit_score: Optional[float] = None
    credit_risk_level: Optional[CreditRiskLevel] = None

    # Default risk metrics
    probability_of_default_1y: Optional[float] = None
    probability_of_default_5y: Optional[float] = None
    loss_given_default: Optional[float] = None
    exposure_at_default: Optional[float] = None
    expected_loss: Optional[float] = None

    # Credit spread metrics
    credit_spread: Optional[float] = None
    credit_spread_volatility: Optional[float] = None
    spread_duration: Optional[float] = None

    # Financial strength indicators
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    debt_service_coverage: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None

    # Market-based indicators
    cds_spread: Optional[float] = None
    bond_yield_spread: Optional[float] = None
    equity_volatility: Optional[float] = None

    # Credit migration analysis
    rating_stability: Optional[float] = None
    migration_probabilities: Dict[str, float] = field(default_factory=dict)

    # Recovery analysis
    recovery_rate: Optional[float] = None
    recovery_volatility: Optional[float] = None

    def credit_risk_score(self) -> float:
        """Calculate overall credit risk score (0-100)."""
        components = []

        # Default probability contribution (40% weight)
        if self.probability_of_default_1y is not None:
            pd_score = min(self.probability_of_default_1y * 1000, 100)
            components.append(('default_prob', pd_score, 0.40))

        # Credit spread contribution (25% weight)
        if self.credit_spread is not None:
            spread_score = min(self.credit_spread * 1000, 100)
            components.append(('credit_spread', spread_score, 0.25))

        # Financial ratios contribution (20% weight)
        if self.debt_to_equity is not None and self.interest_coverage is not None:
            leverage_score = min(self.debt_to_equity * 10, 100)
            coverage_score = max(0, 100 - self.interest_coverage * 10)
            ratio_score = (leverage_score + coverage_score) / 2
            components.append(('financial_ratios', ratio_score, 0.20))

        # Rating contribution (15% weight)
        if self.credit_risk_level is not None:
            rating_score = self.credit_risk_level.level * 10
            components.append(('rating', rating_score, 0.15))

        if not components:
            return 50.0

        total_score = sum(score * weight for _, score, weight in components)
        total_weight = sum(weight for _, _, weight in components)

        return total_score / total_weight if total_weight > 0 else 50.0


@dataclass
class OperationalRiskResult:
    """
    Operational risk analysis result.

    Contains operational risk metrics, loss event analysis,
    and process risk indicators.
    """
    entity_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Operational loss metrics
    annual_loss_expectancy: Optional[float] = None
    maximum_probable_loss: Optional[float] = None
    operational_var_95: Optional[float] = None

    # Risk event frequency and severity
    event_frequency: Dict[str, float] = field(default_factory=dict)
    loss_severity: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Process risk indicators
    process_failure_rate: Optional[float] = None
    system_downtime: Optional[float] = None
    error_rates: Dict[str, float] = field(default_factory=dict)

    # Control effectiveness
    control_scores: Dict[str, float] = field(default_factory=dict)
    control_gaps: List[str] = field(default_factory=list)

    # Key risk indicators (KRIs)
    key_risk_indicators: Dict[str, float] = field(default_factory=dict)

    # Business continuity metrics
    recovery_time_objective: Optional[float] = None
    recovery_point_objective: Optional[float] = None

    def operational_risk_score(self) -> float:
        """Calculate overall operational risk score (0-100)."""
        components = []

        # Loss expectancy contribution (40% weight)
        if self.annual_loss_expectancy is not None:
            # Normalize by assuming typical revenue scale
            loss_score = min(self.annual_loss_expectancy / 1000000 * 50, 100)
            components.append(('loss_expectancy', loss_score, 0.40))

        # Process failure contribution (30% weight)
        if self.process_failure_rate is not None:
            failure_score = min(self.process_failure_rate * 1000, 100)
            components.append(('process_failure', failure_score, 0.30))

        # Control effectiveness contribution (30% weight)
        if self.control_scores:
            avg_control_score = np.mean(list(self.control_scores.values()))
            control_risk_score = 100 - avg_control_score  # Invert: lower control = higher risk
            components.append(('control_effectiveness', control_risk_score, 0.30))

        if not components:
            return 50.0

        total_score = sum(score * weight for _, score, weight in components)
        total_weight = sum(weight for _, _, weight in components)

        return total_score / total_weight if total_weight > 0 else 50.0


@dataclass
class LiquidityRiskResult:
    """
    Liquidity risk analysis result.

    Contains liquidity risk metrics, market microstructure analysis,
    and funding liquidity assessment.
    """
    asset_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Market liquidity metrics
    bid_ask_spread: Optional[float] = None
    quoted_spread: Optional[float] = None
    effective_spread: Optional[float] = None
    realized_spread: Optional[float] = None

    # Volume and depth metrics
    average_daily_volume: Optional[float] = None
    volume_volatility: Optional[float] = None
    market_depth: Optional[float] = None
    order_book_imbalance: Optional[float] = None

    # Liquidity risk measures
    liquidity_var: Optional[float] = None
    liquidity_adjusted_var: Optional[float] = None
    liquidity_cost: Optional[float] = None

    # Time-based metrics
    time_to_liquidate: Optional[float] = None
    immediacy_cost: Optional[float] = None

    # Market impact metrics
    price_impact: Optional[float] = None
    temporary_impact: Optional[float] = None
    permanent_impact: Optional[float] = None

    # Funding liquidity (for portfolios/institutions)
    cash_ratio: Optional[float] = None
    funding_gap: Optional[float] = None
    liquidity_coverage_ratio: Optional[float] = None

    # Stress scenarios
    liquidity_stress_results: Dict[str, float] = field(default_factory=dict)

    def liquidity_risk_score(self) -> float:
        """Calculate overall liquidity risk score (0-100)."""
        components = []

        # Bid-ask spread contribution (30% weight)
        if self.bid_ask_spread is not None:
            spread_score = min(self.bid_ask_spread * 10000, 100)  # Convert to basis points
            components.append(('bid_ask_spread', spread_score, 0.30))

        # Volume contribution (25% weight)
        if self.average_daily_volume is not None and self.volume_volatility is not None:
            # Lower volume = higher risk, higher volume volatility = higher risk
            volume_risk = min(100 - np.log10(max(self.average_daily_volume, 1)), 100)
            vol_risk = min(self.volume_volatility * 100, 100)
            volume_score = (volume_risk + vol_risk) / 2
            components.append(('volume_risk', volume_score, 0.25))

        # Market impact contribution (25% weight)
        if self.price_impact is not None:
            impact_score = min(self.price_impact * 1000, 100)
            components.append(('market_impact', impact_score, 0.25))

        # Time to liquidate contribution (20% weight)
        if self.time_to_liquidate is not None:
            time_score = min(self.time_to_liquidate * 10, 100)  # Assume days
            components.append(('time_to_liquidate', time_score, 0.20))

        if not components:
            return 50.0

        total_score = sum(score * weight for _, score, weight in components)
        total_weight = sum(weight for _, _, weight in components)

        return total_score / total_weight if total_weight > 0 else 50.0


class RiskTypeAnalyzer(ABC):
    """
    Abstract base class for specialized risk type analyzers.

    Provides common interface and shared functionality for different
    types of risk analysis (market, credit, operational, liquidity).
    """

    def __init__(self, financial_calculator=None):
        """
        Initialize risk type analyzer.

        Args:
            financial_calculator: FinancialCalculator instance for data access
        """
        self.financial_calculator = financial_calculator
        self.analysis_cache: Dict[str, Any] = {}

    @abstractmethod
    def analyze(self, entity_id: str, **kwargs) -> Any:
        """Perform specialized risk analysis."""
        pass

    def _get_price_data(self, asset_id: str, periods: int = 252) -> Optional[pd.Series]:
        """Get historical price data for analysis."""
        if not self.financial_calculator:
            return None

        # This would integrate with financial calculator to get price data
        # For now, return placeholder
        return None

    def _get_financial_data(self, entity_id: str) -> Optional[Dict[str, float]]:
        """Get financial statement data for analysis."""
        if not self.financial_calculator:
            return None

        # This would integrate with financial calculator to get financial data
        return None


class MarketRiskAnalyzer(RiskTypeAnalyzer):
    """
    Market risk analyzer for equity, bond, and derivative instruments.

    Provides comprehensive market risk analysis including beta calculation,
    VaR estimation, factor analysis, and stress testing.
    """

    def analyze(self, asset_id: str, benchmark_id: str = 'SPY', **kwargs) -> MarketRiskResult:
        """
        Analyze market risk for specified asset.

        Args:
            asset_id: Asset identifier
            benchmark_id: Benchmark for beta calculation
            **kwargs: Additional analysis parameters

        Returns:
            MarketRiskResult with comprehensive market risk metrics
        """
        logger.info(f"Analyzing market risk for {asset_id}")

        result = MarketRiskResult(asset_id=asset_id)

        try:
            # Get price data
            price_data = self._get_price_data(asset_id)
            benchmark_data = self._get_price_data(benchmark_id)

            if price_data is not None and benchmark_data is not None:
                # Calculate returns
                returns = price_data.pct_change().dropna()
                benchmark_returns = benchmark_data.pct_change().dropna()

                # Align data
                aligned_data = pd.DataFrame({
                    'asset': returns,
                    'benchmark': benchmark_returns
                }).dropna()

                if len(aligned_data) > 30:
                    # Calculate beta and alpha
                    result = self._calculate_beta_metrics(result, aligned_data)

                    # Calculate volatility metrics
                    result = self._calculate_volatility_metrics(result, aligned_data['asset'])

                    # Calculate VaR metrics
                    result = self._calculate_var_metrics(result, aligned_data['asset'])

                    # Calculate factor exposures
                    result = self._calculate_factor_exposures(result, aligned_data)

                    # Perform stress testing
                    result = self._perform_market_stress_tests(result, aligned_data['asset'])

        except Exception as e:
            logger.error(f"Market risk analysis failed for {asset_id}: {e}")

        return result

    def _calculate_beta_metrics(self, result: MarketRiskResult, data: pd.DataFrame) -> MarketRiskResult:
        """Calculate beta, alpha, and related regression metrics."""
        try:
            asset_returns = data['asset']
            benchmark_returns = data['benchmark']

            # Linear regression: asset_return = alpha + beta * benchmark_return + error
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                benchmark_returns, asset_returns
            )

            result.beta = slope
            result.alpha = intercept * 252  # Annualized alpha
            result.r_squared = r_value ** 2

            # Tracking error (standard deviation of active returns)
            active_returns = asset_returns - benchmark_returns
            result.tracking_error = active_returns.std() * np.sqrt(252)

            # Information ratio
            if result.tracking_error and result.tracking_error > 0:
                result.information_ratio = (result.alpha or 0) / result.tracking_error

        except Exception as e:
            logger.warning(f"Beta calculation failed: {e}")

        return result

    def _calculate_volatility_metrics(self, result: MarketRiskResult, returns: pd.Series) -> MarketRiskResult:
        """Calculate volatility-based risk metrics."""
        try:
            # Realized volatility
            result.realized_volatility = returns.std() * np.sqrt(252)

            # Additional volatility metrics could be added here
            # (implied volatility would require options data)

        except Exception as e:
            logger.warning(f"Volatility calculation failed: {e}")

        return result

    def _calculate_var_metrics(self, result: MarketRiskResult, returns: pd.Series) -> MarketRiskResult:
        """Calculate Value at Risk metrics."""
        try:
            # Historical VaR
            result.var_1day_95 = np.percentile(returns, 5)
            result.var_1day_99 = np.percentile(returns, 1)

            # 10-day VaR (assuming square root of time scaling)
            result.var_10day_95 = result.var_1day_95 * np.sqrt(10)

            # Expected Shortfall (Conditional VaR)
            var_95_returns = returns[returns <= result.var_1day_95]
            result.expected_shortfall_95 = var_95_returns.mean() if len(var_95_returns) > 0 else result.var_1day_95

        except Exception as e:
            logger.warning(f"VaR calculation failed: {e}")

        return result

    def _calculate_factor_exposures(self, result: MarketRiskResult, data: pd.DataFrame) -> MarketRiskResult:
        """Calculate factor exposures and contributions."""
        try:
            asset_returns = data['asset']

            # Simplified factor analysis - in practice would use multiple factors
            # Market factor (already calculated as beta)
            market_exposure = result.beta or 0
            result.factor_exposures[MarketRiskFactor.EQUITY_RISK] = market_exposure

            # Volatility factor (simplified)
            vol_factor = asset_returns.rolling(30).std().corr(asset_returns.abs())
            result.factor_exposures[MarketRiskFactor.VOLATILITY_RISK] = vol_factor or 0

            # Calculate systematic vs idiosyncratic risk
            total_variance = asset_returns.var()
            systematic_variance = (result.beta ** 2) * data['benchmark'].var() if result.beta else 0
            idiosyncratic_variance = total_variance - systematic_variance

            result.systematic_risk = np.sqrt(max(0, systematic_variance))
            result.idiosyncratic_risk = np.sqrt(max(0, idiosyncratic_variance))
            result.total_risk = np.sqrt(total_variance)

        except Exception as e:
            logger.warning(f"Factor exposure calculation failed: {e}")

        return result

    def _perform_market_stress_tests(self, result: MarketRiskResult, returns: pd.Series) -> MarketRiskResult:
        """Perform market stress testing scenarios."""
        try:
            # Stress test scenarios
            stress_scenarios = {
                'market_crash_10pct': -0.10,
                'market_crash_20pct': -0.20,
                'volatility_spike_2x': None,  # Special case
                'correlation_breakdown': None  # Special case
            }

            for scenario_name, shock in stress_scenarios.items():
                if shock is not None:
                    # Simple linear stress test
                    if result.beta:
                        stressed_return = result.beta * shock
                        result.stress_test_results[scenario_name] = stressed_return
                elif scenario_name == 'volatility_spike_2x':
                    # Volatility spike scenario
                    current_vol = returns.std()
                    stressed_var = np.percentile(returns, 5) * 2  # Double the VaR impact
                    result.stress_test_results[scenario_name] = stressed_var

        except Exception as e:
            logger.warning(f"Stress testing failed: {e}")

        return result


class CreditRiskAnalyzer(RiskTypeAnalyzer):
    """
    Credit risk analyzer for corporate and sovereign entities.

    Provides comprehensive credit risk analysis including rating assessment,
    default probability estimation, and credit spread analysis.
    """

    def analyze(self, entity_id: str, **kwargs) -> CreditRiskResult:
        """
        Analyze credit risk for specified entity.

        Args:
            entity_id: Entity identifier
            **kwargs: Additional analysis parameters

        Returns:
            CreditRiskResult with comprehensive credit risk metrics
        """
        logger.info(f"Analyzing credit risk for {entity_id}")

        result = CreditRiskResult(entity_id=entity_id)

        try:
            # Get financial data
            financial_data = self._get_financial_data(entity_id)

            if financial_data:
                # Calculate financial ratios
                result = self._calculate_financial_ratios(result, financial_data)

                # Estimate credit rating and score
                result = self._estimate_credit_rating(result, financial_data)

                # Calculate default probabilities
                result = self._calculate_default_probabilities(result)

                # Analyze credit spreads (if bond/CDS data available)
                result = self._analyze_credit_spreads(result, entity_id)

        except Exception as e:
            logger.error(f"Credit risk analysis failed for {entity_id}: {e}")

        return result

    def _calculate_financial_ratios(self, result: CreditRiskResult, data: Dict[str, float]) -> CreditRiskResult:
        """Calculate financial strength ratios."""
        try:
            # Leverage ratios
            total_debt = data.get('total_debt', 0)
            total_equity = data.get('total_equity', 1)
            result.debt_to_equity = total_debt / total_equity if total_equity > 0 else np.inf

            # Coverage ratios
            ebitda = data.get('ebitda', 0)
            interest_expense = data.get('interest_expense', 1)
            result.interest_coverage = ebitda / interest_expense if interest_expense > 0 else np.inf

            # Liquidity ratios
            current_assets = data.get('current_assets', 0)
            current_liabilities = data.get('current_liabilities', 1)
            result.current_ratio = current_assets / current_liabilities if current_liabilities > 0 else np.inf

            quick_assets = current_assets - data.get('inventory', 0)
            result.quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else np.inf

            # Debt service coverage
            operating_cash_flow = data.get('operating_cash_flow', 0)
            debt_service = data.get('debt_service', 1)
            result.debt_service_coverage = operating_cash_flow / debt_service if debt_service > 0 else np.inf

        except Exception as e:
            logger.warning(f"Financial ratio calculation failed: {e}")

        return result

    def _estimate_credit_rating(self, result: CreditRiskResult, data: Dict[str, float]) -> CreditRiskResult:
        """Estimate credit rating based on financial ratios."""
        try:
            # Simplified credit scoring model
            score = 100

            # Penalize high leverage
            if result.debt_to_equity:
                if result.debt_to_equity > 2.0:
                    score -= 30
                elif result.debt_to_equity > 1.0:
                    score -= 15

            # Penalize low coverage
            if result.interest_coverage:
                if result.interest_coverage < 2.0:
                    score -= 25
                elif result.interest_coverage < 5.0:
                    score -= 10

            # Penalize low liquidity
            if result.current_ratio:
                if result.current_ratio < 1.0:
                    score -= 20
                elif result.current_ratio < 1.5:
                    score -= 10

            result.credit_score = max(0, score)

            # Map score to rating
            if score >= 90:
                result.credit_risk_level = CreditRiskLevel.AAA
            elif score >= 80:
                result.credit_risk_level = CreditRiskLevel.AA
            elif score >= 70:
                result.credit_risk_level = CreditRiskLevel.A
            elif score >= 60:
                result.credit_risk_level = CreditRiskLevel.BBB
            elif score >= 50:
                result.credit_risk_level = CreditRiskLevel.BB
            elif score >= 40:
                result.credit_risk_level = CreditRiskLevel.B
            elif score >= 30:
                result.credit_risk_level = CreditRiskLevel.CCC
            elif score >= 20:
                result.credit_risk_level = CreditRiskLevel.CC
            elif score >= 10:
                result.credit_risk_level = CreditRiskLevel.C
            else:
                result.credit_risk_level = CreditRiskLevel.D

            result.credit_rating = result.credit_risk_level.rating

        except Exception as e:
            logger.warning(f"Credit rating estimation failed: {e}")

        return result

    def _calculate_default_probabilities(self, result: CreditRiskResult) -> CreditRiskResult:
        """Calculate probability of default."""
        try:
            if result.credit_risk_level:
                # Use rating-based default probabilities
                result.probability_of_default_1y = result.credit_risk_level.default_prob

                # Estimate 5-year cumulative default probability
                # Simplified: assume constant hazard rate
                annual_survival_prob = 1 - result.probability_of_default_1y
                five_year_survival_prob = annual_survival_prob ** 5
                result.probability_of_default_5y = 1 - five_year_survival_prob

                # Loss Given Default estimation (simplified)
                if result.credit_risk_level.level <= 4:  # Investment grade
                    result.loss_given_default = 0.40
                else:  # High yield
                    result.loss_given_default = 0.60

                # Expected Loss calculation would require Exposure at Default
                # result.expected_loss = PD * LGD * EAD (not calculated here)

        except Exception as e:
            logger.warning(f"Default probability calculation failed: {e}")

        return result

    def _analyze_credit_spreads(self, result: CreditRiskResult, entity_id: str) -> CreditRiskResult:
        """Analyze credit spreads from bond/CDS data."""
        try:
            # This would require bond/CDS market data
            # For now, estimate based on rating
            if result.credit_risk_level:
                # Simplified spread estimation based on rating
                rating_spreads = {
                    CreditRiskLevel.AAA: 0.0010,
                    CreditRiskLevel.AA: 0.0020,
                    CreditRiskLevel.A: 0.0040,
                    CreditRiskLevel.BBB: 0.0080,
                    CreditRiskLevel.BB: 0.0200,
                    CreditRiskLevel.B: 0.0400,
                    CreditRiskLevel.CCC: 0.0800,
                    CreditRiskLevel.CC: 0.1200,
                    CreditRiskLevel.C: 0.1600,
                    CreditRiskLevel.D: 0.2000
                }

                result.credit_spread = rating_spreads.get(result.credit_risk_level, 0.0100)
                result.credit_spread_volatility = result.credit_spread * 0.5  # Simplified

        except Exception as e:
            logger.warning(f"Credit spread analysis failed: {e}")

        return result


class OperationalRiskAnalyzer(RiskTypeAnalyzer):
    """
    Operational risk analyzer for process, system, and human risks.

    Provides operational risk quantification using loss event data,
    key risk indicators, and scenario analysis.
    """

    def analyze(self, entity_id: str, **kwargs) -> OperationalRiskResult:
        """
        Analyze operational risk for specified entity.

        Args:
            entity_id: Entity identifier
            **kwargs: Additional analysis parameters

        Returns:
            OperationalRiskResult with operational risk metrics
        """
        logger.info(f"Analyzing operational risk for {entity_id}")

        result = OperationalRiskResult(entity_id=entity_id)

        try:
            # Analyze historical loss events
            result = self._analyze_loss_events(result, entity_id)

            # Calculate key risk indicators
            result = self._calculate_risk_indicators(result, entity_id)

            # Assess control effectiveness
            result = self._assess_control_effectiveness(result, entity_id)

            # Estimate operational VaR
            result = self._calculate_operational_var(result)

        except Exception as e:
            logger.error(f"Operational risk analysis failed for {entity_id}: {e}")

        return result

    def _analyze_loss_events(self, result: OperationalRiskResult, entity_id: str) -> OperationalRiskResult:
        """Analyze historical operational loss events."""
        try:
            # In practice, this would access loss event database
            # For now, use simplified estimates

            # Typical operational risk event categories
            event_categories = [
                'internal_fraud', 'external_fraud', 'employment_practices',
                'clients_products', 'damage_assets', 'business_disruption',
                'execution_delivery'
            ]

            # Simplified loss frequency and severity
            for category in event_categories:
                # Frequency: events per year
                result.event_frequency[category] = np.random.poisson(2)  # Placeholder

                # Severity distribution (lognormal)
                result.loss_severity[category] = {
                    'mean': 100000 * np.random.uniform(0.5, 2.0),  # Placeholder
                    'std': 50000 * np.random.uniform(0.5, 1.5),
                    'distribution': 'lognormal'
                }

            # Calculate annual loss expectancy
            total_ale = 0
            for category in event_categories:
                frequency = result.event_frequency[category]
                mean_severity = result.loss_severity[category]['mean']
                total_ale += frequency * mean_severity

            result.annual_loss_expectancy = total_ale

        except Exception as e:
            logger.warning(f"Loss event analysis failed: {e}")

        return result

    def _calculate_risk_indicators(self, result: OperationalRiskResult, entity_id: str) -> OperationalRiskResult:
        """Calculate key risk indicators."""
        try:
            # Simplified KRI calculation
            result.key_risk_indicators = {
                'system_availability': 99.5,  # Percentage
                'error_rate': 0.01,           # Percentage
                'staff_turnover': 0.15,       # Annual rate
                'training_completion': 85.0,   # Percentage
                'audit_findings': 5,          # Number of findings
                'customer_complaints': 20     # Number per month
            }

            # Calculate derived metrics
            result.process_failure_rate = result.key_risk_indicators['error_rate'] / 100
            result.system_downtime = (100 - result.key_risk_indicators['system_availability']) / 100

            # Error rates by category
            result.error_rates = {
                'data_entry': 0.005,
                'reconciliation': 0.003,
                'authorization': 0.001
            }

        except Exception as e:
            logger.warning(f"Risk indicator calculation failed: {e}")

        return result

    def _assess_control_effectiveness(self, result: OperationalRiskResult, entity_id: str) -> OperationalRiskResult:
        """Assess effectiveness of operational controls."""
        try:
            # Control categories and effectiveness scores
            control_categories = [
                'access_controls', 'segregation_duties', 'authorization_limits',
                'reconciliations', 'monitoring', 'business_continuity'
            ]

            for category in control_categories:
                # Simplified scoring (0-100, higher is better)
                result.control_scores[category] = np.random.uniform(60, 95)  # Placeholder

            # Identify control gaps (scores below threshold)
            threshold = 70
            result.control_gaps = [
                category for category, score in result.control_scores.items()
                if score < threshold
            ]

        except Exception as e:
            logger.warning(f"Control assessment failed: {e}")

        return result

    def _calculate_operational_var(self, result: OperationalRiskResult) -> OperationalRiskResult:
        """Calculate operational Value at Risk."""
        try:
            # Simplified operational VaR using loss distribution approach
            if result.annual_loss_expectancy:
                # Assume coefficient of variation of 2 for operational losses
                ale = result.annual_loss_expectancy
                cv = 2.0
                loss_std = ale * cv

                # Operational VaR at 95% confidence (normal approximation)
                result.operational_var_95 = ale + 1.645 * loss_std

                # Maximum probable loss (99.9% confidence)
                result.maximum_probable_loss = ale + 3.09 * loss_std

        except Exception as e:
            logger.warning(f"Operational VaR calculation failed: {e}")

        return result


class LiquidityRiskAnalyzer(RiskTypeAnalyzer):
    """
    Liquidity risk analyzer for market and funding liquidity assessment.

    Provides comprehensive liquidity analysis including market microstructure
    analysis, liquidity costs, and funding liquidity metrics.
    """

    def analyze(self, asset_id: str, **kwargs) -> LiquidityRiskResult:
        """
        Analyze liquidity risk for specified asset.

        Args:
            asset_id: Asset identifier
            **kwargs: Additional analysis parameters

        Returns:
            LiquidityRiskResult with liquidity risk metrics
        """
        logger.info(f"Analyzing liquidity risk for {asset_id}")

        result = LiquidityRiskResult(asset_id=asset_id)

        try:
            # Get market data (price, volume, bid-ask)
            market_data = self._get_market_microstructure_data(asset_id)

            if market_data:
                # Calculate spread metrics
                result = self._calculate_spread_metrics(result, market_data)

                # Calculate volume and depth metrics
                result = self._calculate_volume_metrics(result, market_data)

                # Calculate market impact metrics
                result = self._calculate_market_impact_metrics(result, market_data)

                # Estimate liquidity costs and time to liquidate
                result = self._estimate_liquidity_costs(result, market_data)

                # Perform liquidity stress testing
                result = self._perform_liquidity_stress_tests(result, market_data)

        except Exception as e:
            logger.error(f"Liquidity risk analysis failed for {asset_id}: {e}")

        return result

    def _get_market_microstructure_data(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get market microstructure data for liquidity analysis."""
        # This would access order book data, trade data, etc.
        # For now, return placeholder data
        return {
            'bid_prices': pd.Series(np.random.normal(100, 1, 252)),
            'ask_prices': pd.Series(np.random.normal(100.1, 1, 252)),
            'volumes': pd.Series(np.random.exponential(1000000, 252)),
            'trade_prices': pd.Series(np.random.normal(100.05, 1, 252))
        }

    def _calculate_spread_metrics(self, result: LiquidityRiskResult, data: Dict[str, Any]) -> LiquidityRiskResult:
        """Calculate bid-ask spread metrics."""
        try:
            bid_prices = data['bid_prices']
            ask_prices = data['ask_prices']
            trade_prices = data['trade_prices']

            # Quoted spread
            quoted_spreads = (ask_prices - bid_prices) / ((ask_prices + bid_prices) / 2)
            result.quoted_spread = quoted_spreads.mean()
            result.bid_ask_spread = result.quoted_spread  # Same as quoted spread

            # Effective spread (if trade data available)
            mid_prices = (bid_prices + ask_prices) / 2
            effective_spreads = 2 * abs(trade_prices - mid_prices) / mid_prices
            result.effective_spread = effective_spreads.mean()

        except Exception as e:
            logger.warning(f"Spread metric calculation failed: {e}")

        return result

    def _calculate_volume_metrics(self, result: LiquidityRiskResult, data: Dict[str, Any]) -> LiquidityRiskResult:
        """Calculate volume and depth metrics."""
        try:
            volumes = data['volumes']

            # Average daily volume
            result.average_daily_volume = volumes.mean()

            # Volume volatility
            result.volume_volatility = volumes.std() / volumes.mean() if volumes.mean() > 0 else 0

            # Market depth (simplified as average volume)
            result.market_depth = volumes.quantile(0.75)  # 75th percentile volume

        except Exception as e:
            logger.warning(f"Volume metric calculation failed: {e}")

        return result

    def _calculate_market_impact_metrics(self, result: LiquidityRiskResult, data: Dict[str, Any]) -> LiquidityRiskResult:
        """Calculate market impact metrics."""
        try:
            # Simplified market impact model: impact = constant * (volume / avg_volume)^0.5
            if result.average_daily_volume and result.average_daily_volume > 0:
                # Assume trading 10% of average daily volume
                trade_volume = result.average_daily_volume * 0.1
                volume_ratio = trade_volume / result.average_daily_volume

                # Simplified linear impact model
                impact_coefficient = 0.01  # 1% impact for 100% of daily volume
                result.price_impact = impact_coefficient * (volume_ratio ** 0.5)

                # Split into temporary and permanent components
                result.temporary_impact = result.price_impact * 0.6  # 60% temporary
                result.permanent_impact = result.price_impact * 0.4  # 40% permanent

        except Exception as e:
            logger.warning(f"Market impact calculation failed: {e}")

        return result

    def _estimate_liquidity_costs(self, result: LiquidityRiskResult, data: Dict[str, Any]) -> LiquidityRiskResult:
        """Estimate liquidity costs and time to liquidate."""
        try:
            # Time to liquidate based on volume
            if result.average_daily_volume and result.average_daily_volume > 0:
                # Assume we want to liquidate position worth 1% of daily volume per day
                daily_liquidation_capacity = result.average_daily_volume * 0.01

                # For a given position size (assume $1M), calculate days needed
                position_size = 1000000  # $1M
                avg_price = 100  # Assume $100 per share
                shares_to_liquidate = position_size / avg_price

                result.time_to_liquidate = shares_to_liquidate / daily_liquidation_capacity

            # Total liquidity cost (spread + impact)
            spread_cost = result.bid_ask_spread or 0
            impact_cost = result.price_impact or 0
            result.liquidity_cost = spread_cost + impact_cost

        except Exception as e:
            logger.warning(f"Liquidity cost estimation failed: {e}")

        return result

    def _perform_liquidity_stress_tests(self, result: LiquidityRiskResult, data: Dict[str, Any]) -> LiquidityRiskResult:
        """Perform liquidity stress testing."""
        try:
            base_spread = result.bid_ask_spread or 0.001
            base_volume = result.average_daily_volume or 1000000

            # Stress scenarios
            stress_scenarios = {
                'market_stress_2x_spread': base_spread * 2,
                'volume_dry_up_50pct': base_volume * 0.5,
                'extreme_stress_5x_spread': base_spread * 5,
                'liquidity_crisis_90pct_volume_drop': base_volume * 0.1
            }

            for scenario_name, stressed_value in stress_scenarios.items():
                if 'spread' in scenario_name:
                    # Estimate impact on liquidity cost
                    stressed_cost = stressed_value + (result.price_impact or 0)
                    result.liquidity_stress_results[scenario_name] = stressed_cost
                elif 'volume' in scenario_name:
                    # Estimate impact on time to liquidate
                    if stressed_value > 0:
                        daily_capacity = stressed_value * 0.01
                        stressed_time = 10000 / daily_capacity  # Assume 10k shares to liquidate
                        result.liquidity_stress_results[scenario_name] = stressed_time

        except Exception as e:
            logger.warning(f"Liquidity stress testing failed: {e}")

        return result


class IntegratedRiskTypeFramework:
    """
    Unified framework that coordinates all risk type analyzers to provide
    comprehensive, multi-dimensional risk assessment across all risk categories.
    """

    def __init__(self, financial_calculator=None):
        """
        Initialize integrated risk type framework.

        Args:
            financial_calculator: FinancialCalculator instance for data access
        """
        self.financial_calculator = financial_calculator

        # Initialize all risk type analyzers
        self.market_risk_analyzer = MarketRiskAnalyzer(financial_calculator)
        self.credit_risk_analyzer = CreditRiskAnalyzer(financial_calculator)
        self.operational_risk_analyzer = OperationalRiskAnalyzer(financial_calculator)
        self.liquidity_risk_analyzer = LiquidityRiskAnalyzer(financial_calculator)

        # Risk analysis cache
        self.risk_analysis_cache: Dict[str, Dict[str, Any]] = {}

        logger.info("Integrated Risk Type Framework initialized")

    def analyze_comprehensive_risk(
        self,
        entity_id: str,
        risk_types: Optional[List[RiskType]] = None,
        **kwargs
    ) -> Dict[RiskType, Any]:
        """
        Perform comprehensive risk analysis across multiple risk types.

        Args:
            entity_id: Entity/asset identifier
            risk_types: List of risk types to analyze (all if None)
            **kwargs: Additional analysis parameters

        Returns:
            Dictionary mapping risk types to their analysis results
        """
        logger.info(f"Performing comprehensive risk analysis for {entity_id}")

        # Default to all risk types if not specified
        if risk_types is None:
            risk_types = [RiskType.MARKET, RiskType.CREDIT, RiskType.OPERATIONAL, RiskType.LIQUIDITY]

        results = {}

        # Analyze each requested risk type
        for risk_type in risk_types:
            try:
                if risk_type == RiskType.MARKET:
                    results[risk_type] = self.market_risk_analyzer.analyze(entity_id, **kwargs)
                elif risk_type == RiskType.CREDIT:
                    results[risk_type] = self.credit_risk_analyzer.analyze(entity_id, **kwargs)
                elif risk_type == RiskType.OPERATIONAL:
                    results[risk_type] = self.operational_risk_analyzer.analyze(entity_id, **kwargs)
                elif risk_type == RiskType.LIQUIDITY:
                    results[risk_type] = self.liquidity_risk_analyzer.analyze(entity_id, **kwargs)
                else:
                    logger.warning(f"Risk type {risk_type} not supported yet")

            except Exception as e:
                logger.error(f"Failed to analyze {risk_type.value} risk for {entity_id}: {e}")
                continue

        # Cache results
        self.risk_analysis_cache[entity_id] = results

        return results

    def analyze_market_risk(self, asset_id: str, **kwargs) -> MarketRiskResult:
        """Analyze market risk for specified asset."""
        return self.market_risk_analyzer.analyze(asset_id, **kwargs)

    def analyze_credit_risk(self, entity_id: str, **kwargs) -> CreditRiskResult:
        """Analyze credit risk for specified entity."""
        return self.credit_risk_analyzer.analyze(entity_id, **kwargs)

    def analyze_operational_risk(self, entity_id: str, **kwargs) -> OperationalRiskResult:
        """Analyze operational risk for specified entity."""
        return self.operational_risk_analyzer.analyze(entity_id, **kwargs)

    def analyze_liquidity_risk(self, asset_id: str, **kwargs) -> LiquidityRiskResult:
        """Analyze liquidity risk for specified asset."""
        return self.liquidity_risk_analyzer.analyze(asset_id, **kwargs)

    def calculate_composite_risk_score(
        self,
        entity_id: str,
        risk_weights: Optional[Dict[RiskType, float]] = None
    ) -> float:
        """
        Calculate composite risk score across all risk types.

        Args:
            entity_id: Entity identifier
            risk_weights: Weights for each risk type (equal if None)

        Returns:
            Composite risk score (0-100)
        """
        if entity_id not in self.risk_analysis_cache:
            logger.warning(f"No risk analysis found for {entity_id}")
            return 50.0

        results = self.risk_analysis_cache[entity_id]

        # Default equal weights
        if risk_weights is None:
            risk_weights = {risk_type: 1.0 / len(results) for risk_type in results.keys()}

        # Calculate weighted composite score
        total_score = 0
        total_weight = 0

        for risk_type, result in results.items():
            weight = risk_weights.get(risk_type, 0)

            if weight > 0:
                # Get risk score from result
                if hasattr(result, 'market_risk_score'):
                    score = result.market_risk_score()
                elif hasattr(result, 'credit_risk_score'):
                    score = result.credit_risk_score()
                elif hasattr(result, 'operational_risk_score'):
                    score = result.operational_risk_score()
                elif hasattr(result, 'liquidity_risk_score'):
                    score = result.liquidity_risk_score()
                else:
                    score = 50.0  # Default moderate risk

                total_score += score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 50.0

    def generate_risk_type_report(self, entity_id: str) -> Dict[str, Any]:
        """Generate comprehensive report across all risk types."""
        if entity_id not in self.risk_analysis_cache:
            return {'error': f'No risk analysis found for {entity_id}'}

        results = self.risk_analysis_cache[entity_id]

        report = {
            'entity_id': entity_id,
            'analysis_date': datetime.now().isoformat(),
            'composite_risk_score': self.calculate_composite_risk_score(entity_id),
            'risk_type_analysis': {}
        }

        # Add individual risk type results
        for risk_type, result in results.items():
            if hasattr(result, 'market_risk_score'):
                report['risk_type_analysis'][risk_type.value] = {
                    'risk_score': result.market_risk_score(),
                    'key_metrics': {
                        'beta': result.beta,
                        'var_95': result.var_1day_95,
                        'volatility': result.realized_volatility
                    }
                }
            elif hasattr(result, 'credit_risk_score'):
                report['risk_type_analysis'][risk_type.value] = {
                    'risk_score': result.credit_risk_score(),
                    'key_metrics': {
                        'credit_rating': result.credit_rating,
                        'default_probability': result.probability_of_default_1y,
                        'debt_to_equity': result.debt_to_equity
                    }
                }
            elif hasattr(result, 'operational_risk_score'):
                report['risk_type_analysis'][risk_type.value] = {
                    'risk_score': result.operational_risk_score(),
                    'key_metrics': {
                        'annual_loss_expectancy': result.annual_loss_expectancy,
                        'process_failure_rate': result.process_failure_rate
                    }
                }
            elif hasattr(result, 'liquidity_risk_score'):
                report['risk_type_analysis'][risk_type.value] = {
                    'risk_score': result.liquidity_risk_score(),
                    'key_metrics': {
                        'bid_ask_spread': result.bid_ask_spread,
                        'time_to_liquidate': result.time_to_liquidate,
                        'average_daily_volume': result.average_daily_volume
                    }
                }

        return report