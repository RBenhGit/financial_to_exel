"""
Black-Litterman Portfolio Optimization Model
===========================================

Implementation of the Black-Litterman model for portfolio optimization,
which combines market equilibrium assumptions with investor views to
generate more stable and intuitive portfolio allocations.

The Black-Litterman model addresses several limitations of traditional
mean-variance optimization:
- Reduces sensitivity to estimation errors in expected returns
- Incorporates investor views in a systematic way
- Provides more diversified portfolios
- Accounts for estimation uncertainty

Key Components:
- Market equilibrium returns calculation
- Investor views specification and confidence
- Bayesian updating of expected returns
- Integration with standard optimization framework
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

from .portfolio_optimization import (
    OptimizationResult,
    OptimizationConstraints,
    OptimizationObjective,
    OptimizationMethod,
    PortfolioOptimizer
)

logger = logging.getLogger(__name__)


class ViewType(Enum):
    """Types of investor views in Black-Litterman model"""
    ABSOLUTE = "absolute"        # Absolute return view (asset will return X%)
    RELATIVE = "relative"        # Relative return view (asset A will outperform asset B by X%)
    VOLATILITY = "volatility"    # Volatility view (asset volatility will be X%)


@dataclass
class InvestorView:
    """Individual investor view for Black-Litterman model"""

    view_type: ViewType
    assets: List[str]                    # Assets involved in the view
    expected_return: float               # Expected return or relative performance
    confidence: float = 0.5              # Confidence level (0-1, where 1 is highest confidence)

    # For relative views
    picking_vector: Optional[np.ndarray] = None    # P matrix row (auto-calculated)
    view_uncertainty: Optional[float] = None       # Omega matrix element (auto-calculated)

    # View description
    description: str = ""
    view_id: Optional[str] = None

    def __post_init__(self):
        """Validate and set default values"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        if not self.description:
            if self.view_type == ViewType.ABSOLUTE:
                self.description = f"Absolute view: {self.assets[0]} expected return {self.expected_return:.2%}"
            elif self.view_type == ViewType.RELATIVE:
                self.description = f"Relative view: {self.assets[0]} vs {self.assets[1]} by {self.expected_return:.2%}"

        if not self.view_id:
            self.view_id = f"view_{hash(self.description) % 10000}"


@dataclass
class BlackLittermanInputs:
    """Inputs for Black-Litterman model"""

    # Market data
    market_caps: Dict[str, float]         # Market capitalizations
    covariance_matrix: np.ndarray         # Historical covariance matrix
    risk_aversion: float = 3.0            # Market risk aversion parameter

    # Prior assumptions
    risk_free_rate: float = 0.02          # Risk-free rate
    market_return: Optional[float] = None # Market return (if None, calculated from market caps)
    tau: float = 0.025                    # Scales uncertainty of prior (typically 0.01-0.05)

    # Investor views
    views: List[InvestorView] = field(default_factory=list)

    # Model parameters
    confidence_scaling: float = 1.0       # Scales all view confidences
    min_weight: float = 0.0               # Minimum asset weight
    max_weight: float = 1.0               # Maximum asset weight


@dataclass
class BlackLittermanResult:
    """Result of Black-Litterman optimization"""

    # Model outputs
    implied_returns: Dict[str, float] = field(default_factory=dict)    # Market equilibrium returns
    adjusted_returns: Dict[str, float] = field(default_factory=dict)   # Black-Litterman adjusted returns
    adjusted_covariance: Optional[np.ndarray] = None                   # Adjusted covariance matrix

    # Portfolio allocation
    optimal_weights: Dict[str, float] = field(default_factory=dict)
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Model diagnostics
    view_impacts: Dict[str, float] = field(default_factory=dict)       # Impact of each view on portfolio
    certainty_equivalent: Optional[float] = None                      # Certainty equivalent return
    diversification_ratio: Optional[float] = None

    # Comparison with market cap weights
    market_cap_weights: Dict[str, float] = field(default_factory=dict)
    weight_deviations: Dict[str, float] = field(default_factory=dict)  # Deviation from market cap weights

    # Model metadata
    model_success: bool = False
    error_message: str = ""
    computation_date: datetime = field(default_factory=datetime.now)
    tau_used: float = 0.025
    risk_aversion_used: float = 3.0


class BlackLittermanOptimizer:
    """
    Black-Litterman portfolio optimization implementation
    """

    def __init__(self):
        self.tickers: List[str] = []
        self.n_assets: int = 0

    def optimize(self,
                tickers: List[str],
                inputs: BlackLittermanInputs,
                constraints: Optional[OptimizationConstraints] = None) -> BlackLittermanResult:
        """
        Run Black-Litterman optimization

        Args:
            tickers: List of asset tickers
            inputs: Black-Litterman model inputs
            constraints: Additional optimization constraints

        Returns:
            BlackLittermanResult with optimized portfolio
        """
        try:
            self.tickers = tickers
            self.n_assets = len(tickers)

            result = BlackLittermanResult()

            # Step 1: Calculate market equilibrium (implied) returns
            implied_returns = self._calculate_implied_returns(inputs)
            result.implied_returns = {ticker: float(ret) for ticker, ret in zip(tickers, implied_returns)}

            # Step 2: Set up investor views
            P, Q, Omega = self._setup_views(inputs.views, tickers)

            # Step 3: Calculate Black-Litterman adjusted returns
            if P.size > 0:  # If we have views
                bl_returns, bl_cov = self._calculate_bl_returns(
                    implied_returns, inputs.covariance_matrix, P, Q, Omega, inputs.tau
                )
            else:
                # No views, use market equilibrium returns
                bl_returns = implied_returns
                bl_cov = inputs.covariance_matrix

            result.adjusted_returns = {ticker: float(ret) for ticker, ret in zip(tickers, bl_returns)}
            result.adjusted_covariance = bl_cov

            # Step 4: Optimize portfolio using adjusted returns
            optimizer = PortfolioOptimizer(risk_free_rate=inputs.risk_free_rate)

            # Convert to expected returns dict for optimizer
            bl_returns_dict = {ticker: float(ret) for ticker, ret in zip(tickers, bl_returns)}

            optimization_result = optimizer.optimize_portfolio(
                tickers=tickers,
                expected_returns=bl_returns_dict,
                covariance_matrix=bl_cov,
                objective=OptimizationObjective.MAX_SHARPE,
                constraints=constraints,
                method=OptimizationMethod.QUADRATIC
            )

            if optimization_result.success:
                result.optimal_weights = optimization_result.weights
                result.expected_return = optimization_result.expected_return
                result.expected_volatility = optimization_result.expected_volatility
                result.sharpe_ratio = optimization_result.sharpe_ratio
                result.model_success = True

                # Calculate additional metrics
                result = self._calculate_additional_metrics(result, inputs, tickers)

            else:
                result.model_success = False
                result.error_message = f"Portfolio optimization failed: {optimization_result.message}"

            result.tau_used = inputs.tau
            result.risk_aversion_used = inputs.risk_aversion

            logger.info(f"Black-Litterman optimization completed. Success: {result.model_success}")
            if result.model_success:
                logger.info(f"Expected Return: {result.expected_return:.4f}, "
                           f"Volatility: {result.expected_volatility:.4f}, "
                           f"Sharpe: {result.sharpe_ratio:.4f}")

            return result

        except Exception as e:
            logger.error(f"Black-Litterman optimization failed: {str(e)}")
            return BlackLittermanResult(
                model_success=False,
                error_message=f"Black-Litterman optimization failed: {str(e)}"
            )

    def _calculate_implied_returns(self, inputs: BlackLittermanInputs) -> np.ndarray:
        """
        Calculate market equilibrium (implied) returns using reverse optimization

        The implied returns are those that would make the market cap weighted
        portfolio optimal under mean-variance optimization.

        Formula: μ = λ * Σ * w_market
        where λ is risk aversion, Σ is covariance matrix, w_market is market cap weights
        """
        # Calculate market cap weights
        total_market_cap = sum(inputs.market_caps.values())
        market_weights = np.array([
            inputs.market_caps.get(ticker, 0.0) / total_market_cap
            for ticker in self.tickers
        ])

        # Implied returns = risk_aversion * covariance_matrix * market_weights
        implied_returns = inputs.risk_aversion * (inputs.covariance_matrix @ market_weights)

        return implied_returns

    def _setup_views(self, views: List[InvestorView], tickers: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Set up the P (picking), Q (views), and Omega (uncertainty) matrices

        Args:
            views: List of investor views
            tickers: List of asset tickers

        Returns:
            Tuple of (P, Q, Omega) matrices
        """
        n_views = len(views)
        n_assets = len(tickers)

        if n_views == 0:
            return np.array([]), np.array([]), np.array([])

        # Initialize matrices
        P = np.zeros((n_views, n_assets))  # Picking matrix
        Q = np.zeros(n_views)               # View returns
        Omega = np.zeros((n_views, n_views))  # View uncertainty matrix

        ticker_to_idx = {ticker: i for i, ticker in enumerate(tickers)}

        for i, view in enumerate(views):
            Q[i] = view.expected_return

            if view.view_type == ViewType.ABSOLUTE:
                # Absolute view: single asset expected return
                if len(view.assets) != 1:
                    raise ValueError(f"Absolute view must specify exactly one asset, got {len(view.assets)}")

                asset_idx = ticker_to_idx.get(view.assets[0])
                if asset_idx is not None:
                    P[i, asset_idx] = 1.0

            elif view.view_type == ViewType.RELATIVE:
                # Relative view: asset A outperforms asset B
                if len(view.assets) != 2:
                    raise ValueError(f"Relative view must specify exactly two assets, got {len(view.assets)}")

                asset_a_idx = ticker_to_idx.get(view.assets[0])
                asset_b_idx = ticker_to_idx.get(view.assets[1])

                if asset_a_idx is not None and asset_b_idx is not None:
                    P[i, asset_a_idx] = 1.0
                    P[i, asset_b_idx] = -1.0

            # Calculate view uncertainty based on confidence
            # Higher confidence -> lower uncertainty
            # Omega[i,i] represents the variance of the view
            base_uncertainty = 0.1  # Base uncertainty level
            Omega[i, i] = base_uncertainty * (1.0 - view.confidence)

        return P, Q, Omega

    def _calculate_bl_returns(self,
                             implied_returns: np.ndarray,
                             covariance_matrix: np.ndarray,
                             P: np.ndarray,
                             Q: np.ndarray,
                             Omega: np.ndarray,
                             tau: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Black-Litterman adjusted returns and covariance matrix

        Black-Litterman formula:
        μ_BL = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) * [(τΣ)^(-1)μ + P'Ω^(-1)Q]
        Σ_BL = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1)

        Args:
            implied_returns: Market equilibrium returns
            covariance_matrix: Asset covariance matrix
            P: Picking matrix
            Q: View returns vector
            Omega: View uncertainty matrix
            tau: Scaling parameter for prior uncertainty

        Returns:
            Tuple of (adjusted_returns, adjusted_covariance)
        """
        try:
            # Prior covariance scaled by tau
            tau_sigma = tau * covariance_matrix

            # Compute inverse matrices
            tau_sigma_inv = np.linalg.inv(tau_sigma)
            omega_inv = np.linalg.inv(Omega)

            # Black-Litterman calculations
            # M1 = (τΣ)^(-1) + P'Ω^(-1)P
            M1 = tau_sigma_inv + P.T @ omega_inv @ P

            # M2 = (τΣ)^(-1)μ + P'Ω^(-1)Q
            M2 = tau_sigma_inv @ implied_returns + P.T @ omega_inv @ Q

            # M3 = M1^(-1)
            M3 = np.linalg.inv(M1)

            # Black-Litterman expected returns
            bl_returns = M3 @ M2

            # Black-Litterman covariance matrix
            bl_covariance = M3

            return bl_returns, bl_covariance

        except np.linalg.LinAlgError as e:
            logger.error(f"Matrix inversion failed in Black-Litterman calculation: {str(e)}")
            # Fallback to original values
            return implied_returns, covariance_matrix

    def _calculate_additional_metrics(self,
                                    result: BlackLittermanResult,
                                    inputs: BlackLittermanInputs,
                                    tickers: List[str]) -> BlackLittermanResult:
        """Calculate additional metrics and diagnostics"""

        # Market cap weights for comparison
        total_market_cap = sum(inputs.market_caps.values())
        result.market_cap_weights = {
            ticker: inputs.market_caps.get(ticker, 0.0) / total_market_cap
            for ticker in tickers
        }

        # Weight deviations from market cap weights
        result.weight_deviations = {
            ticker: result.optimal_weights.get(ticker, 0.0) - result.market_cap_weights.get(ticker, 0.0)
            for ticker in tickers
        }

        # Calculate diversification ratio
        if result.adjusted_covariance is not None and result.optimal_weights:
            weights_array = np.array([result.optimal_weights.get(ticker, 0.0) for ticker in tickers])
            asset_volatilities = np.sqrt(np.diag(result.adjusted_covariance))
            weighted_avg_vol = weights_array @ asset_volatilities

            if result.expected_volatility and result.expected_volatility > 0:
                result.diversification_ratio = weighted_avg_vol / result.expected_volatility

        # View impact analysis (simplified)
        if inputs.views:
            total_deviation = sum(abs(dev) for dev in result.weight_deviations.values())
            result.view_impacts = {
                view.view_id: view.confidence * abs(view.expected_return)
                for view in inputs.views
            }

        return result


def create_absolute_view(asset: str, expected_return: float, confidence: float = 0.5) -> InvestorView:
    """
    Create an absolute return view for a single asset

    Args:
        asset: Asset ticker
        expected_return: Expected return for the asset
        confidence: Confidence in the view (0-1)

    Returns:
        InvestorView object
    """
    return InvestorView(
        view_type=ViewType.ABSOLUTE,
        assets=[asset],
        expected_return=expected_return,
        confidence=confidence,
        description=f"Absolute view: {asset} expected return {expected_return:.2%}"
    )


def create_relative_view(asset_a: str, asset_b: str, relative_return: float, confidence: float = 0.5) -> InvestorView:
    """
    Create a relative return view between two assets

    Args:
        asset_a: First asset ticker
        asset_b: Second asset ticker
        relative_return: Expected outperformance of asset_a vs asset_b
        confidence: Confidence in the view (0-1)

    Returns:
        InvestorView object
    """
    return InvestorView(
        view_type=ViewType.RELATIVE,
        assets=[asset_a, asset_b],
        expected_return=relative_return,
        confidence=confidence,
        description=f"Relative view: {asset_a} outperforms {asset_b} by {relative_return:.2%}"
    )


def create_sample_bl_optimization() -> Tuple[List[str], BlackLittermanInputs]:
    """Create sample data for Black-Litterman optimization testing"""

    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Sample market caps (in billions)
    market_caps = {
        'AAPL': 2800.0,
        'MSFT': 2600.0,
        'GOOGL': 1800.0,
        'AMZN': 1500.0,
        'TSLA': 800.0
    }

    # Sample correlation matrix
    correlation_matrix = np.array([
        [1.00, 0.65, 0.70, 0.60, 0.45],
        [0.65, 1.00, 0.75, 0.55, 0.40],
        [0.70, 0.75, 1.00, 0.65, 0.50],
        [0.60, 0.55, 0.65, 1.00, 0.35],
        [0.45, 0.40, 0.50, 0.35, 1.00]
    ])

    # Sample volatilities
    volatilities = np.array([0.25, 0.22, 0.28, 0.32, 0.45])

    # Convert to covariance matrix
    covariance_matrix = np.outer(volatilities, volatilities) * correlation_matrix

    # Sample views
    views = [
        create_absolute_view('TSLA', 0.25, confidence=0.7),  # Tesla expected 25% return
        create_relative_view('AAPL', 'MSFT', 0.03, confidence=0.6),  # Apple outperforms Microsoft by 3%
        create_absolute_view('AMZN', 0.18, confidence=0.8)   # Amazon expected 18% return
    ]

    inputs = BlackLittermanInputs(
        market_caps=market_caps,
        covariance_matrix=covariance_matrix,
        risk_aversion=3.0,
        risk_free_rate=0.02,
        tau=0.025,
        views=views
    )

    return tickers, inputs


# Integration with main portfolio optimization
def integrate_black_litterman_with_portfolio(portfolio_optimizer: PortfolioOptimizer,
                                           tickers: List[str],
                                           bl_inputs: BlackLittermanInputs,
                                           constraints: Optional[OptimizationConstraints] = None) -> OptimizationResult:
    """
    Integrate Black-Litterman with standard portfolio optimization

    Args:
        portfolio_optimizer: Standard portfolio optimizer
        tickers: Asset tickers
        bl_inputs: Black-Litterman inputs
        constraints: Portfolio constraints

    Returns:
        OptimizationResult with Black-Litterman adjusted inputs
    """
    # Run Black-Litterman optimization
    bl_optimizer = BlackLittermanOptimizer()
    bl_result = bl_optimizer.optimize(tickers, bl_inputs, constraints)

    if not bl_result.model_success:
        logger.error(f"Black-Litterman optimization failed: {bl_result.error_message}")
        # Fallback to standard optimization with market equilibrium returns
        implied_returns = {ticker: ret for ticker, ret in bl_result.implied_returns.items()}
        return portfolio_optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=implied_returns,
            covariance_matrix=bl_inputs.covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE,
            constraints=constraints
        )

    # Convert Black-Litterman result to standard OptimizationResult
    optimization_result = OptimizationResult(
        objective=OptimizationObjective.MAX_SHARPE,
        method=OptimizationMethod.QUADRATIC,
        success=bl_result.model_success,
        weights=bl_result.optimal_weights,
        expected_return=bl_result.expected_return,
        expected_volatility=bl_result.expected_volatility,
        sharpe_ratio=bl_result.sharpe_ratio,
        message="Black-Litterman optimization completed successfully"
    )

    return optimization_result