"""
Risk Metrics and Data Structures
===============================

This module defines comprehensive risk metrics, data structures, and statistical
models for financial risk analysis. It provides standardized risk measurement
capabilities that integrate with the Monte Carlo engine and portfolio framework.

Key Features:
- Multiple risk types (market, credit, operational, liquidity)
- Standardized risk level classifications
- Portfolio and individual asset risk profiling
- Statistical risk metrics (VaR, CVaR, drawdown, volatility)
- Risk factor identification and modeling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class RiskType(Enum):
    """Classification of financial risk types."""
    MARKET = "market"           # Price volatility, market movements
    CREDIT = "credit"           # Default risk, counterparty risk
    OPERATIONAL = "operational" # Business operations, management
    LIQUIDITY = "liquidity"     # Ability to convert to cash
    CONCENTRATION = "concentration" # Portfolio concentration risk
    CORRELATION = "correlation" # Unexpected correlation changes
    TAIL = "tail"              # Extreme event risk
    SYSTEMIC = "systemic"      # System-wide risk events


class RiskLevel(Enum):
    """Risk level classifications."""
    VERY_LOW = ("very_low", 0, 10)
    LOW = ("low", 10, 25)
    MODERATE = ("moderate", 25, 50)
    HIGH = ("high", 50, 75)
    VERY_HIGH = ("very_high", 75, 90)
    EXTREME = ("extreme", 90, 100)

    def __init__(self, name: str, min_percentile: float, max_percentile: float):
        self.level_name = name
        self.min_percentile = min_percentile
        self.max_percentile = max_percentile

    @classmethod
    def from_percentile(cls, percentile: float) -> 'RiskLevel':
        """Determine risk level from percentile score."""
        for level in cls:
            if level.min_percentile <= percentile < level.max_percentile:
                return level
        return cls.EXTREME  # Default for 90+ percentile


@dataclass
class RiskMetrics:
    """
    Comprehensive risk metrics for financial analysis.

    Contains statistical measures, percentile-based risk metrics,
    and volatility measurements for risk assessment.
    """
    # Value at Risk metrics
    var_1day_95: Optional[float] = None    # 1-day 95% VaR
    var_1day_99: Optional[float] = None    # 1-day 99% VaR
    var_1day_995: Optional[float] = None   # 1-day 99.5% VaR

    # Conditional Value at Risk (Expected Shortfall)
    cvar_1day_95: Optional[float] = None   # 1-day 95% CVaR
    cvar_1day_99: Optional[float] = None   # 1-day 99% CVaR

    # Volatility metrics
    annual_volatility: Optional[float] = None
    downside_volatility: Optional[float] = None
    upside_volatility: Optional[float] = None

    # Drawdown metrics
    max_drawdown: Optional[float] = None
    avg_drawdown: Optional[float] = None
    recovery_time: Optional[int] = None    # Days to recover from max drawdown

    # Distribution metrics
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

    # Risk-adjusted returns
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Tail risk metrics
    tail_ratio: Optional[float] = None     # Ratio of 95th to 5th percentile
    probability_of_loss: Optional[float] = None

    # Time-based metrics
    calculation_date: datetime = field(default_factory=datetime.now)
    data_period_start: Optional[date] = None
    data_period_end: Optional[date] = None

    # Metadata
    confidence_level: float = 0.95
    time_horizon_days: int = 1
    currency: str = "USD"

    def risk_level(self) -> RiskLevel:
        """Determine overall risk level based on VaR percentile."""
        if self.var_1day_95 is None:
            return RiskLevel.MODERATE

        # Convert VaR to percentile-based risk score
        # This is simplified - in practice would use more sophisticated scoring
        var_score = abs(self.var_1day_95) * 100 if self.var_1day_95 < 0 else 0
        return RiskLevel.from_percentile(min(var_score, 99))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'var_metrics': {
                'var_1day_95': self.var_1day_95,
                'var_1day_99': self.var_1day_99,
                'var_1day_995': self.var_1day_995,
                'cvar_1day_95': self.cvar_1day_95,
                'cvar_1day_99': self.cvar_1day_99
            },
            'volatility_metrics': {
                'annual_volatility': self.annual_volatility,
                'downside_volatility': self.downside_volatility,
                'upside_volatility': self.upside_volatility
            },
            'drawdown_metrics': {
                'max_drawdown': self.max_drawdown,
                'avg_drawdown': self.avg_drawdown,
                'recovery_time': self.recovery_time
            },
            'distribution_metrics': {
                'skewness': self.skewness,
                'kurtosis': self.kurtosis
            },
            'risk_adjusted_returns': {
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'calmar_ratio': self.calmar_ratio
            },
            'tail_risk': {
                'tail_ratio': self.tail_ratio,
                'probability_of_loss': self.probability_of_loss
            },
            'metadata': {
                'risk_level': self.risk_level().level_name,
                'calculation_date': self.calculation_date.isoformat(),
                'confidence_level': self.confidence_level,
                'time_horizon_days': self.time_horizon_days,
                'currency': self.currency
            }
        }


@dataclass
class AssetRiskProfile:
    """
    Risk profile for individual financial assets.

    Comprehensive risk assessment including multiple risk types,
    historical analysis, and forward-looking risk indicators.
    """
    asset_id: str
    asset_name: str
    asset_type: str  # 'stock', 'bond', 'etf', etc.

    # Core risk metrics
    risk_metrics: RiskMetrics

    # Risk type breakdown
    risk_types: Dict[RiskType, float] = field(default_factory=dict)

    # Historical risk analysis
    historical_volatility_1y: Optional[float] = None
    historical_volatility_3y: Optional[float] = None
    historical_beta: Optional[float] = None
    correlation_to_market: Optional[float] = None

    # Fundamental risk indicators
    leverage_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Market risk indicators
    market_cap: Optional[float] = None
    average_volume: Optional[float] = None
    bid_ask_spread: Optional[float] = None

    # Sector and industry risk
    sector: Optional[str] = None
    industry: Optional[str] = None
    sector_beta: Optional[float] = None

    # ESG risk factors (if available)
    esg_score: Optional[float] = None
    esg_risk_level: Optional[str] = None

    def overall_risk_score(self) -> float:
        """Calculate composite risk score (0-100, higher = riskier)."""
        risk_components = []

        # Volatility component (30% weight)
        if self.risk_metrics.annual_volatility:
            vol_score = min(self.risk_metrics.annual_volatility * 100, 100)
            risk_components.append(('volatility', vol_score, 0.30))

        # VaR component (25% weight)
        if self.risk_metrics.var_1day_95:
            var_score = min(abs(self.risk_metrics.var_1day_95) * 100, 100)
            risk_components.append(('var', var_score, 0.25))

        # Fundamental component (20% weight)
        if self.leverage_ratio:
            leverage_score = min(self.leverage_ratio * 10, 100)
            risk_components.append(('leverage', leverage_score, 0.20))

        # Market risk component (15% weight)
        if self.historical_beta:
            beta_score = min(abs(self.historical_beta) * 25, 100)
            risk_components.append(('beta', beta_score, 0.15))

        # Liquidity component (10% weight)
        if self.bid_ask_spread:
            liquidity_score = min(self.bid_ask_spread * 1000, 100)
            risk_components.append(('liquidity', liquidity_score, 0.10))

        if not risk_components:
            return 50.0  # Default moderate risk

        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in risk_components)
        total_weight = sum(weight for _, _, weight in risk_components)

        return total_score / total_weight if total_weight > 0 else 50.0

    def risk_level(self) -> RiskLevel:
        """Determine risk level based on overall risk score."""
        return RiskLevel.from_percentile(self.overall_risk_score())


@dataclass
class PortfolioRiskMetrics:
    """
    Comprehensive risk metrics for investment portfolios.

    Includes portfolio-level risk calculations, diversification metrics,
    concentration analysis, and correlation-based risk assessment.
    """
    portfolio_id: str
    portfolio_name: str

    # Portfolio composition
    total_assets: int
    total_value: float

    # Aggregate risk metrics
    portfolio_risk_metrics: RiskMetrics

    # Portfolio metadata
    currency: str = "USD"

    # Individual asset risks
    asset_risks: Dict[str, AssetRiskProfile] = field(default_factory=dict)

    # Portfolio-specific metrics
    diversification_ratio: Optional[float] = None  # Portfolio vol / weighted avg vol
    concentration_risk: Optional[float] = None     # HHI of portfolio weights
    correlation_risk: Optional[float] = None       # Average pairwise correlation

    # Risk contribution analysis
    marginal_var: Dict[str, float] = field(default_factory=dict)
    component_var: Dict[str, float] = field(default_factory=dict)
    risk_contribution_pct: Dict[str, float] = field(default_factory=dict)

    # Sector/geographic concentration
    sector_concentration: Dict[str, float] = field(default_factory=dict)
    geographic_concentration: Dict[str, float] = field(default_factory=dict)

    # Stress test results
    stress_test_results: Dict[str, float] = field(default_factory=dict)

    # Performance and risk-adjusted metrics
    portfolio_return_1y: Optional[float] = None
    portfolio_volatility_1y: Optional[float] = None
    information_ratio: Optional[float] = None
    tracking_error: Optional[float] = None

    def calculate_diversification_benefit(self) -> float:
        """Calculate diversification benefit compared to equal-weighted individual risks."""
        if not self.asset_risks or not self.portfolio_risk_metrics.annual_volatility:
            return 0.0

        # Calculate average individual asset volatility
        individual_vols = [
            asset.risk_metrics.annual_volatility
            for asset in self.asset_risks.values()
            if asset.risk_metrics.annual_volatility is not None
        ]

        if not individual_vols:
            return 0.0

        avg_individual_vol = np.mean(individual_vols)
        portfolio_vol = self.portfolio_risk_metrics.annual_volatility

        # Diversification benefit = (Avg Individual Vol - Portfolio Vol) / Avg Individual Vol
        return (avg_individual_vol - portfolio_vol) / avg_individual_vol

    def concentration_hhi(self) -> float:
        """Calculate Herfindahl-Hirschman Index for concentration measurement."""
        if not hasattr(self, 'weights') or not self.weights:
            return 1.0  # Maximum concentration (single asset)

        return sum(weight ** 2 for weight in self.weights.values())

    def top_risk_contributors(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N risk contributors by risk contribution percentage."""
        if not self.risk_contribution_pct:
            return []

        sorted_contributors = sorted(
            self.risk_contribution_pct.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_contributors[:top_n]

    def risk_budget_utilization(self) -> Dict[str, float]:
        """Calculate risk budget utilization for each asset."""
        if not self.risk_contribution_pct or not hasattr(self, 'risk_budgets'):
            return {}

        utilization = {}
        for asset_id, actual_contribution in self.risk_contribution_pct.items():
            target_budget = getattr(self, 'risk_budgets', {}).get(asset_id, 1.0 / len(self.asset_risks))
            utilization[asset_id] = actual_contribution / target_budget if target_budget > 0 else 0.0

        return utilization


@dataclass
class RiskFactorModel:
    """
    Statistical model for risk factor identification and analysis.

    Provides factor-based risk decomposition using statistical techniques
    like PCA, factor analysis, and regression-based risk attribution.
    """
    model_name: str
    model_type: str  # 'pca', 'factor_analysis', 'regression'

    # Factor structure
    risk_factors: List[str] = field(default_factory=list)
    factor_loadings: Dict[str, Dict[str, float]] = field(default_factory=dict)
    factor_exposures: Dict[str, float] = field(default_factory=dict)

    # Model statistics
    explained_variance: Dict[str, float] = field(default_factory=dict)
    model_r_squared: Optional[float] = None
    residual_risk: Optional[float] = None

    # Factor risk attribution
    systematic_risk: Optional[float] = None
    idiosyncratic_risk: Optional[float] = None
    factor_contributions: Dict[str, float] = field(default_factory=dict)

    # Model validation
    fit_date: datetime = field(default_factory=datetime.now)
    validation_metrics: Dict[str, float] = field(default_factory=dict)

    def dominant_factors(self, threshold: float = 0.1) -> List[str]:
        """Identify dominant risk factors above threshold contribution."""
        return [
            factor for factor, contribution in self.factor_contributions.items()
            if contribution >= threshold
        ]

    def factor_concentration(self) -> float:
        """Calculate concentration of risk in top factors."""
        if not self.factor_contributions:
            return 0.0

        sorted_contributions = sorted(self.factor_contributions.values(), reverse=True)
        top_3_contribution = sum(sorted_contributions[:3])
        return top_3_contribution