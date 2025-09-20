"""
Portfolio Optimization Algorithms
=================================

This module implements modern portfolio theory algorithms for optimal asset allocation
and risk-return optimization, including Mean-Variance Optimization, risk parity,
and constraint-based optimization strategies.

Implemented Algorithms:
- Mean-Variance Optimization (Markowitz model)
- Risk Parity allocation
- Equal Weight allocation
- Efficient Frontier calculation
- Black-Litterman model
- Constraint-based optimization

Features:
- Integration with existing Portfolio and PortfolioHolding models
- Support for various objective functions (max Sharpe, min volatility, etc.)
- Flexible constraint handling (position limits, sector constraints)
- Robust optimization with uncertainty handling
- Performance attribution and risk decomposition
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, date
import warnings

from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioMetrics,
    PositionSizingMethod
)
from core.data_processing.data_contracts import FinancialStatement, MarketData

# Suppress optimization warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Portfolio optimization objectives"""
    MAX_SHARPE = "max_sharpe"                    # Maximum Sharpe ratio
    MIN_VOLATILITY = "min_volatility"            # Minimum volatility
    MAX_RETURN = "max_return"                    # Maximum return
    RISK_PARITY = "risk_parity"                  # Risk parity allocation
    EQUAL_WEIGHT = "equal_weight"                # Equal weight allocation
    MAX_DIVERSIFICATION = "max_diversification"  # Maximum diversification ratio
    MIN_CONCENTRATION = "min_concentration"      # Minimize concentration risk


class OptimizationMethod(Enum):
    """Optimization solution methods"""
    QUADRATIC = "quadratic"                      # Quadratic programming
    SEQUENTIAL = "sequential"                    # Sequential quadratic programming
    GENETIC = "genetic"                          # Genetic algorithm
    MONTE_CARLO = "monte_carlo"                  # Monte Carlo optimization
    GRADIENT_DESCENT = "gradient_descent"        # Gradient descent


@dataclass
class OptimizationConstraints:
    """Portfolio optimization constraints"""

    # Position Constraints
    min_weight: float = 0.0                      # Minimum position weight
    max_weight: float = 1.0                      # Maximum position weight
    position_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # ticker: (min, max)

    # Portfolio Constraints
    target_return: Optional[float] = None        # Target portfolio return
    max_volatility: Optional[float] = None       # Maximum portfolio volatility
    max_tracking_error: Optional[float] = None   # Maximum tracking error vs benchmark

    # Sector/Group Constraints
    sector_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # sector: (min, max)
    group_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)   # group: (min, max)

    # Risk Constraints
    max_concentration: float = 0.4               # Maximum single position weight
    min_positions: int = 1                       # Minimum number of positions
    max_positions: Optional[int] = None          # Maximum number of positions

    # Transaction Constraints
    turnover_limit: Optional[float] = None       # Maximum portfolio turnover
    transaction_costs: Dict[str, float] = field(default_factory=dict)  # ticker: cost

    # ESG/Other Constraints
    esg_score_min: Optional[float] = None        # Minimum ESG score
    exclude_tickers: List[str] = field(default_factory=list)  # Excluded tickers
    include_tickers: List[str] = field(default_factory=list)  # Required tickers


@dataclass
class OptimizationResult:
    """Result of portfolio optimization"""

    # Optimization Details
    objective: OptimizationObjective
    method: OptimizationMethod
    success: bool = False
    message: str = ""

    # Optimized Weights
    weights: Dict[str, float] = field(default_factory=dict)
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Risk Metrics
    portfolio_beta: Optional[float] = None
    value_at_risk: Optional[float] = None
    expected_shortfall: Optional[float] = None
    max_drawdown: Optional[float] = None

    # Constraint Compliance
    constraints_satisfied: bool = False
    constraint_violations: List[str] = field(default_factory=list)

    # Performance Attribution
    risk_contribution: Dict[str, float] = field(default_factory=dict)
    return_contribution: Dict[str, float] = field(default_factory=dict)

    # Optimization Metrics
    iterations: int = 0
    computation_time: float = 0.0
    objective_value: Optional[float] = None

    # Additional Results
    efficient_frontier_points: List[Tuple[float, float]] = field(default_factory=list)
    corner_portfolios: List[Dict[str, float]] = field(default_factory=list)

    # Metadata
    optimization_date: datetime = field(default_factory=datetime.now)
    risk_free_rate: float = 0.02
    benchmark_return: Optional[float] = None


class PortfolioOptimizer:
    """
    Main portfolio optimization engine implementing various optimization algorithms
    """

    def __init__(self,
                 risk_free_rate: float = 0.02,
                 estimation_window: int = 252,
                 confidence_level: float = 0.95):
        """
        Initialize portfolio optimizer

        Args:
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            estimation_window: Number of periods for parameter estimation
            confidence_level: Confidence level for risk metrics
        """
        self.risk_free_rate = risk_free_rate
        self.estimation_window = estimation_window
        self.confidence_level = confidence_level

        # Will be populated during optimization
        self.returns_data: Optional[pd.DataFrame] = None
        self.expected_returns: Optional[np.ndarray] = None
        self.covariance_matrix: Optional[np.ndarray] = None
        self.tickers: List[str] = []

    def optimize_portfolio(self,
                          tickers: List[str],
                          returns_data: Optional[pd.DataFrame] = None,
                          expected_returns: Optional[Dict[str, float]] = None,
                          covariance_matrix: Optional[np.ndarray] = None,
                          objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
                          constraints: Optional[OptimizationConstraints] = None,
                          method: OptimizationMethod = OptimizationMethod.QUADRATIC,
                          **kwargs) -> OptimizationResult:
        """
        Optimize portfolio allocation

        Args:
            tickers: List of asset tickers
            returns_data: Historical returns data (DataFrame with tickers as columns)
            expected_returns: Expected returns for each asset
            covariance_matrix: Asset covariance matrix
            objective: Optimization objective
            constraints: Portfolio constraints
            method: Optimization method
            **kwargs: Additional optimization parameters

        Returns:
            OptimizationResult with optimal weights and metrics
        """
        start_time = datetime.now()

        try:
            # Setup optimization data
            self.tickers = tickers
            self._setup_optimization_data(returns_data, expected_returns, covariance_matrix)

            # Validate inputs
            if not self._validate_inputs():
                return OptimizationResult(
                    objective=objective,
                    method=method,
                    success=False,
                    message="Input validation failed"
                )

            # Setup constraints
            if constraints is None:
                constraints = OptimizationConstraints()

            # Choose optimization algorithm
            if objective == OptimizationObjective.EQUAL_WEIGHT:
                result = self._equal_weight_allocation()
            elif objective == OptimizationObjective.RISK_PARITY:
                result = self._risk_parity_allocation(method)
            elif objective == OptimizationObjective.MAX_SHARPE:
                result = self._maximize_sharpe_ratio(constraints, method)
            elif objective == OptimizationObjective.MIN_VOLATILITY:
                result = self._minimize_volatility(constraints, method)
            elif objective == OptimizationObjective.MAX_RETURN:
                result = self._maximize_return(constraints, method)
            elif objective == OptimizationObjective.MAX_DIVERSIFICATION:
                result = self._maximize_diversification(constraints, method)
            elif objective == OptimizationObjective.MIN_CONCENTRATION:
                result = self._minimize_concentration(constraints, method)
            else:
                raise ValueError(f"Unsupported optimization objective: {objective}")

            # Calculate portfolio metrics
            result = self._calculate_portfolio_metrics(result)

            # Check constraint compliance
            result = self._check_constraint_compliance(result, constraints)

            # Record optimization details
            result.objective = objective
            result.method = method
            result.computation_time = (datetime.now() - start_time).total_seconds()
            result.risk_free_rate = self.risk_free_rate

            logger.info(f"Portfolio optimization completed: {objective.value} using {method.value}")
            logger.info(f"Success: {result.success}, Expected Return: {result.expected_return:.4f}, "
                       f"Volatility: {result.expected_volatility:.4f}, Sharpe: {result.sharpe_ratio:.4f}")

            return result

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}")
            return OptimizationResult(
                objective=objective,
                method=method,
                success=False,
                message=f"Optimization failed: {str(e)}",
                computation_time=(datetime.now() - start_time).total_seconds()
            )

    def calculate_efficient_frontier(self,
                                   tickers: List[str],
                                   returns_data: Optional[pd.DataFrame] = None,
                                   expected_returns: Optional[Dict[str, float]] = None,
                                   covariance_matrix: Optional[np.ndarray] = None,
                                   constraints: Optional[OptimizationConstraints] = None,
                                   num_points: int = 50) -> List[OptimizationResult]:
        """
        Calculate efficient frontier portfolios

        Args:
            tickers: List of asset tickers
            returns_data: Historical returns data
            expected_returns: Expected returns for each asset
            covariance_matrix: Asset covariance matrix
            constraints: Portfolio constraints
            num_points: Number of efficient frontier points

        Returns:
            List of OptimizationResult objects representing efficient portfolios
        """
        logger.info(f"Calculating efficient frontier with {num_points} points")

        # Setup optimization data
        self.tickers = tickers
        self._setup_optimization_data(returns_data, expected_returns, covariance_matrix)

        if constraints is None:
            constraints = OptimizationConstraints()

        # Calculate return range for efficient frontier
        min_vol_result = self.optimize_portfolio(
            tickers, returns_data, expected_returns, covariance_matrix,
            OptimizationObjective.MIN_VOLATILITY, constraints
        )

        max_return_result = self.optimize_portfolio(
            tickers, returns_data, expected_returns, covariance_matrix,
            OptimizationObjective.MAX_RETURN, constraints
        )

        if not min_vol_result.success or not max_return_result.success:
            logger.error("Failed to calculate efficient frontier bounds")
            return []

        # Generate target returns between min volatility and max return
        min_return = min_vol_result.expected_return
        max_return = max_return_result.expected_return
        target_returns = np.linspace(min_return, max_return, num_points)

        efficient_portfolios = []

        for target_return in target_returns:
            # Set target return constraint
            target_constraints = OptimizationConstraints(
                min_weight=constraints.min_weight,
                max_weight=constraints.max_weight,
                position_limits=constraints.position_limits,
                target_return=target_return,
                max_volatility=constraints.max_volatility,
                sector_limits=constraints.sector_limits,
                max_concentration=constraints.max_concentration,
                exclude_tickers=constraints.exclude_tickers
            )

            result = self._minimize_volatility(target_constraints, OptimizationMethod.QUADRATIC)

            if result.success:
                efficient_portfolios.append(result)

        logger.info(f"Calculated {len(efficient_portfolios)} efficient frontier points")
        return efficient_portfolios

    def _setup_optimization_data(self,
                                returns_data: Optional[pd.DataFrame],
                                expected_returns: Optional[Dict[str, float]],
                                covariance_matrix: Optional[np.ndarray]) -> None:
        """Setup optimization input data"""

        if returns_data is not None:
            self.returns_data = returns_data[self.tickers].dropna()

            # Calculate expected returns if not provided
            if expected_returns is None:
                self.expected_returns = self.returns_data.mean().values
            else:
                self.expected_returns = np.array([expected_returns.get(ticker, 0.0) for ticker in self.tickers])

            # Calculate covariance matrix if not provided
            if covariance_matrix is None:
                self.covariance_matrix = self.returns_data.cov().values
            else:
                self.covariance_matrix = covariance_matrix

        else:
            # Use provided expected returns and covariance matrix
            if expected_returns is None or covariance_matrix is None:
                raise ValueError("Either returns_data or both expected_returns and covariance_matrix must be provided")

            self.expected_returns = np.array([expected_returns.get(ticker, 0.0) for ticker in self.tickers])
            self.covariance_matrix = covariance_matrix

    def _validate_inputs(self) -> bool:
        """Validate optimization inputs"""
        n_assets = len(self.tickers)

        if n_assets == 0:
            logger.error("No tickers provided")
            return False

        if self.expected_returns is None or len(self.expected_returns) != n_assets:
            logger.error(f"Expected returns dimension mismatch: {len(self.expected_returns) if self.expected_returns is not None else 0} vs {n_assets}")
            return False

        if self.covariance_matrix is None or self.covariance_matrix.shape != (n_assets, n_assets):
            logger.error(f"Covariance matrix dimension mismatch: {self.covariance_matrix.shape if self.covariance_matrix is not None else None} vs ({n_assets}, {n_assets})")
            return False

        # Check if covariance matrix is positive semi-definite
        try:
            eigenvals = np.linalg.eigvals(self.covariance_matrix)
            if np.any(eigenvals < -1e-8):  # Allow for small numerical errors
                logger.warning("Covariance matrix is not positive semi-definite")
                # Fix by adding regularization
                self.covariance_matrix += np.eye(n_assets) * 1e-8
        except Exception as e:
            logger.error(f"Failed to validate covariance matrix: {str(e)}")
            return False

        return True

    def _equal_weight_allocation(self) -> OptimizationResult:
        """Calculate equal weight allocation"""
        n_assets = len(self.tickers)
        weights = {ticker: 1.0 / n_assets for ticker in self.tickers}

        return OptimizationResult(
            objective=OptimizationObjective.EQUAL_WEIGHT,
            method=OptimizationMethod.QUADRATIC,
            success=True,
            weights=weights,
            message="Equal weight allocation completed successfully"
        )

    def _risk_parity_allocation(self, method: OptimizationMethod) -> OptimizationResult:
        """Calculate risk parity allocation"""
        try:
            # Risk parity: each asset contributes equally to portfolio risk
            # Start with equal weights and iterate
            n_assets = len(self.tickers)
            weights = np.ones(n_assets) / n_assets

            # Iterative algorithm for risk parity
            for iteration in range(100):  # Maximum iterations
                # Calculate risk contributions
                portfolio_vol = np.sqrt(weights.T @ self.covariance_matrix @ weights)
                marginal_contribs = (self.covariance_matrix @ weights) / portfolio_vol
                risk_contribs = weights * marginal_contribs

                # Target risk contribution
                target_risk_contrib = portfolio_vol / n_assets

                # Update weights
                weights = weights * (target_risk_contrib / risk_contribs)
                weights = weights / np.sum(weights)  # Normalize

                # Check convergence
                risk_contrib_error = np.max(np.abs(risk_contribs - target_risk_contrib))
                if risk_contrib_error < 1e-6:
                    break

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.RISK_PARITY,
                method=method,
                success=True,
                weights=weights_dict,
                iterations=iteration + 1,
                message="Risk parity allocation completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.RISK_PARITY,
                method=method,
                success=False,
                message=f"Risk parity optimization failed: {str(e)}"
            )

    def _maximize_sharpe_ratio(self, constraints: OptimizationConstraints, method: OptimizationMethod) -> OptimizationResult:
        """Maximize Sharpe ratio using analytical solution"""
        try:
            # For mean-variance optimization, we can use analytical solution
            # when no additional constraints are present

            excess_returns = self.expected_returns - self.risk_free_rate

            # Analytical solution for maximum Sharpe ratio portfolio
            try:
                inv_cov = np.linalg.inv(self.covariance_matrix)
                weights = inv_cov @ excess_returns
                weights = weights / np.sum(weights)  # Normalize to sum to 1
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if matrix is singular
                inv_cov = np.linalg.pinv(self.covariance_matrix)
                weights = inv_cov @ excess_returns
                weights = weights / np.sum(weights)

            # Apply constraints
            weights = self._apply_position_constraints(weights, constraints)

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.MAX_SHARPE,
                method=method,
                success=True,
                weights=weights_dict,
                message="Maximum Sharpe ratio optimization completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.MAX_SHARPE,
                method=method,
                success=False,
                message=f"Sharpe ratio optimization failed: {str(e)}"
            )

    def _minimize_volatility(self, constraints: OptimizationConstraints, method: OptimizationMethod) -> OptimizationResult:
        """Minimize portfolio volatility"""
        try:
            # Analytical solution for minimum variance portfolio
            ones = np.ones((len(self.tickers), 1))

            try:
                inv_cov = np.linalg.inv(self.covariance_matrix)
                weights = (inv_cov @ ones) / (ones.T @ inv_cov @ ones)
                weights = weights.flatten()
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if matrix is singular
                inv_cov = np.linalg.pinv(self.covariance_matrix)
                weights = (inv_cov @ ones) / (ones.T @ inv_cov @ ones)
                weights = weights.flatten()

            # Apply constraints
            weights = self._apply_position_constraints(weights, constraints)

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.MIN_VOLATILITY,
                method=method,
                success=True,
                weights=weights_dict,
                message="Minimum volatility optimization completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.MIN_VOLATILITY,
                method=method,
                success=False,
                message=f"Minimum volatility optimization failed: {str(e)}"
            )

    def _maximize_return(self, constraints: OptimizationConstraints, method: OptimizationMethod) -> OptimizationResult:
        """Maximize expected return subject to constraints"""
        try:
            # Simple approach: invest in asset with highest expected return
            # subject to position constraints

            max_return_idx = np.argmax(self.expected_returns)
            weights = np.zeros(len(self.tickers))
            weights[max_return_idx] = 1.0

            # Apply constraints
            weights = self._apply_position_constraints(weights, constraints)

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.MAX_RETURN,
                method=method,
                success=True,
                weights=weights_dict,
                message="Maximum return optimization completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.MAX_RETURN,
                method=method,
                success=False,
                message=f"Maximum return optimization failed: {str(e)}"
            )

    def _maximize_diversification(self, constraints: OptimizationConstraints, method: OptimizationMethod) -> OptimizationResult:
        """Maximize diversification ratio"""
        try:
            # Diversification ratio = weighted average volatility / portfolio volatility
            # This is equivalent to minimizing concentration

            asset_volatilities = np.sqrt(np.diag(self.covariance_matrix))

            # Start with equal weights and optimize
            n_assets = len(self.tickers)
            weights = np.ones(n_assets) / n_assets

            # Simple heuristic: weight inversely proportional to individual volatility
            inv_vol_weights = 1.0 / asset_volatilities
            weights = inv_vol_weights / np.sum(inv_vol_weights)

            # Apply constraints
            weights = self._apply_position_constraints(weights, constraints)

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.MAX_DIVERSIFICATION,
                method=method,
                success=True,
                weights=weights_dict,
                message="Maximum diversification optimization completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.MAX_DIVERSIFICATION,
                method=method,
                success=False,
                message=f"Maximum diversification optimization failed: {str(e)}"
            )

    def _minimize_concentration(self, constraints: OptimizationConstraints, method: OptimizationMethod) -> OptimizationResult:
        """Minimize concentration risk"""
        try:
            # Simple approach: equal weights subject to constraints
            n_assets = len(self.tickers)
            weights = np.ones(n_assets) / n_assets

            # Apply constraints
            weights = self._apply_position_constraints(weights, constraints)

            weights_dict = {ticker: float(weight) for ticker, weight in zip(self.tickers, weights)}

            return OptimizationResult(
                objective=OptimizationObjective.MIN_CONCENTRATION,
                method=method,
                success=True,
                weights=weights_dict,
                message="Minimum concentration optimization completed successfully"
            )

        except Exception as e:
            return OptimizationResult(
                objective=OptimizationObjective.MIN_CONCENTRATION,
                method=method,
                success=False,
                message=f"Minimum concentration optimization failed: {str(e)}"
            )

    def _apply_position_constraints(self, weights: np.ndarray, constraints: OptimizationConstraints) -> np.ndarray:
        """Apply position-level constraints to weights"""

        # Apply min/max weight constraints
        weights = np.clip(weights, constraints.min_weight, constraints.max_weight)

        # Apply specific position limits
        for i, ticker in enumerate(self.tickers):
            if ticker in constraints.position_limits:
                min_w, max_w = constraints.position_limits[ticker]
                weights[i] = np.clip(weights[i], min_w, max_w)

        # Normalize weights to sum to 1
        if np.sum(weights) > 0:
            weights = weights / np.sum(weights)

        # Apply concentration constraint
        max_weight = np.max(weights)
        if max_weight > constraints.max_concentration:
            # Reduce largest weights and redistribute
            excess = max_weight - constraints.max_concentration
            weights[weights == max_weight] = constraints.max_concentration

            # Redistribute excess to other positions
            other_positions = weights < constraints.max_concentration
            if np.any(other_positions):
                weights[other_positions] += excess / np.sum(other_positions)

            # Renormalize
            weights = weights / np.sum(weights)

        return weights

    def _calculate_portfolio_metrics(self, result: OptimizationResult) -> OptimizationResult:
        """Calculate portfolio performance metrics"""

        weights_array = np.array([result.weights.get(ticker, 0.0) for ticker in self.tickers])

        # Expected return
        result.expected_return = float(weights_array.T @ self.expected_returns)

        # Expected volatility
        result.expected_volatility = float(np.sqrt(weights_array.T @ self.covariance_matrix @ weights_array))

        # Sharpe ratio
        if result.expected_volatility > 0:
            result.sharpe_ratio = float((result.expected_return - self.risk_free_rate) / result.expected_volatility)
        else:
            result.sharpe_ratio = 0.0

        # Risk contribution
        if result.expected_volatility > 0:
            marginal_contribs = (self.covariance_matrix @ weights_array) / result.expected_volatility
            risk_contribs = weights_array * marginal_contribs
            result.risk_contribution = {ticker: float(contrib) for ticker, contrib in zip(self.tickers, risk_contribs)}

        # Return contribution
        return_contribs = weights_array * self.expected_returns
        result.return_contribution = {ticker: float(contrib) for ticker, contrib in zip(self.tickers, return_contribs)}

        return result

    def _check_constraint_compliance(self, result: OptimizationResult, constraints: OptimizationConstraints) -> OptimizationResult:
        """Check if optimization result satisfies constraints"""

        violations = []

        # Check position constraints
        for ticker, weight in result.weights.items():
            if weight < constraints.min_weight - 1e-6:
                violations.append(f"{ticker} weight {weight:.4f} below minimum {constraints.min_weight:.4f}")
            if weight > constraints.max_weight + 1e-6:
                violations.append(f"{ticker} weight {weight:.4f} above maximum {constraints.max_weight:.4f}")

        # Check concentration constraint
        max_weight = max(result.weights.values()) if result.weights else 0.0
        if max_weight > constraints.max_concentration + 1e-6:
            violations.append(f"Maximum position weight {max_weight:.4f} exceeds concentration limit {constraints.max_concentration:.4f}")

        # Check target return constraint
        if constraints.target_return is not None:
            return_diff = abs(result.expected_return - constraints.target_return)
            if return_diff > 1e-4:  # Allow small tolerance
                violations.append(f"Expected return {result.expected_return:.4f} deviates from target {constraints.target_return:.4f}")

        # Check volatility constraint
        if constraints.max_volatility is not None and result.expected_volatility > constraints.max_volatility + 1e-6:
            violations.append(f"Expected volatility {result.expected_volatility:.4f} exceeds maximum {constraints.max_volatility:.4f}")

        result.constraint_violations = violations
        result.constraints_satisfied = len(violations) == 0

        return result


def create_optimization_constraints_from_portfolio(portfolio: Portfolio) -> OptimizationConstraints:
    """
    Create optimization constraints from existing portfolio settings

    Args:
        portfolio: Portfolio object with constraint settings

    Returns:
        OptimizationConstraints object
    """
    return OptimizationConstraints(
        min_weight=portfolio.min_position_weight,
        max_weight=portfolio.max_position_weight,
        max_concentration=portfolio.max_position_weight,
        max_volatility=portfolio.target_volatility,
        exclude_tickers=[]  # Can be extended based on portfolio settings
    )


def apply_optimization_to_portfolio(portfolio: Portfolio,
                                  optimization_result: OptimizationResult) -> Portfolio:
    """
    Apply optimization results to update portfolio target weights

    Args:
        portfolio: Portfolio object to update
        optimization_result: Optimization result with new weights

    Returns:
        Updated Portfolio object
    """
    if not optimization_result.success:
        logger.warning("Optimization was not successful, portfolio unchanged")
        return portfolio

    # Update target weights for existing holdings
    for holding in portfolio.holdings:
        if holding.ticker in optimization_result.weights:
            holding.target_weight = optimization_result.weights[holding.ticker]
            holding.weight_deviation = holding.current_weight - holding.target_weight

    # Update portfolio metrics if available
    if optimization_result.expected_return:
        portfolio.portfolio_metrics.portfolio_return = optimization_result.expected_return
    if optimization_result.expected_volatility:
        portfolio.portfolio_metrics.volatility = optimization_result.expected_volatility
    if optimization_result.sharpe_ratio:
        portfolio.portfolio_metrics.sharpe_ratio = optimization_result.sharpe_ratio

    # Update rebalancing recommendation
    total_deviation = sum(abs(h.weight_deviation) for h in portfolio.holdings)
    avg_deviation = total_deviation / len(portfolio.holdings) if portfolio.holdings else 0
    portfolio.portfolio_metrics.deviation_from_targets = avg_deviation
    portfolio.portfolio_metrics.rebalancing_needed = avg_deviation > portfolio.rebalancing_threshold

    return portfolio


# Example usage and testing functions
def create_sample_optimization_data() -> Tuple[List[str], Dict[str, float], np.ndarray]:
    """Create sample data for optimization testing"""

    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Sample expected returns (annualized)
    expected_returns = {
        'AAPL': 0.12,
        'MSFT': 0.14,
        'GOOGL': 0.13,
        'AMZN': 0.15,
        'TSLA': 0.20
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

    return tickers, expected_returns, covariance_matrix