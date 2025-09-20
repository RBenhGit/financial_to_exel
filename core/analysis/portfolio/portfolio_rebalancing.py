"""
Portfolio Rebalancing and Position Sizing Module
===============================================

This module implements sophisticated position sizing and rebalancing algorithms
for portfolio management, supporting multiple methodologies and strategies.

Key Features:
- Multiple position sizing methods (equal weight, market cap, risk parity, etc.)
- Automatic rebalancing based on thresholds or time periods
- Transaction cost optimization
- Risk-based position sizing
- Custom constraint handling

Rebalancing Strategies:
- Threshold-based: Rebalance when positions deviate beyond limits
- Periodic: Time-based rebalancing (monthly, quarterly, etc.)
- Momentum: Trend-following adjustments
- Mean reversion: Contrarian rebalancing
- Volatility targeting: Maintain target portfolio volatility
"""

import math
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
import logging

import numpy as np
from scipy.optimize import minimize

from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PositionSizingMethod,
    RebalancingStrategy,
    PortfolioType
)

logger = logging.getLogger(__name__)


@dataclass
class RebalancingTransaction:
    """Represents a single rebalancing transaction"""

    ticker: str
    action: str  # "BUY", "SELL", "HOLD"
    current_shares: float
    target_shares: float
    shares_to_trade: float
    current_weight: float
    target_weight: float
    current_value: float
    target_value: float
    estimated_cost: float = 0.0  # Transaction costs
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class RebalancingPlan:
    """Complete rebalancing plan for a portfolio"""

    portfolio_id: str
    plan_date: datetime = field(default_factory=datetime.now)
    total_portfolio_value: float = 0.0
    cash_needed: float = 0.0
    cash_generated: float = 0.0
    net_cash_impact: float = 0.0

    transactions: List[RebalancingTransaction] = field(default_factory=list)
    estimated_total_costs: float = 0.0
    rebalancing_reason: str = ""
    priority_level: str = "medium"  # "high", "medium", "low"


class PositionSizer:
    """
    Implements various position sizing methodologies
    """

    def __init__(self, transaction_cost_bps: float = 10.0):
        """
        Initialize position sizer

        Args:
            transaction_cost_bps: Transaction costs in basis points (default 10 bps)
        """
        self.transaction_cost_bps = transaction_cost_bps

    def calculate_equal_weight_targets(self, portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate equal weight target allocations

        Args:
            portfolio: Portfolio to rebalance

        Returns:
            Dictionary mapping ticker to target weight
        """
        if not portfolio.holdings:
            return {}

        # Equal weight across all holdings, accounting for cash
        available_weight = 1.0 - portfolio.target_cash_allocation
        equal_weight = available_weight / len(portfolio.holdings)

        return {holding.ticker: equal_weight for holding in portfolio.holdings}

    def calculate_market_cap_weights(self, portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate market capitalization weighted targets

        Args:
            portfolio: Portfolio to rebalance

        Returns:
            Dictionary mapping ticker to target weight
        """
        target_weights = {}
        total_market_cap = 0.0

        # Calculate total market cap
        for holding in portfolio.holdings:
            if holding.market_data and holding.market_data.market_cap:
                total_market_cap += holding.market_data.market_cap

        if total_market_cap == 0:
            # Fall back to equal weight if no market cap data
            return self.calculate_equal_weight_targets(portfolio)

        # Calculate weights proportional to market cap
        available_weight = 1.0 - portfolio.target_cash_allocation

        for holding in portfolio.holdings:
            if holding.market_data and holding.market_data.market_cap:
                weight = (holding.market_data.market_cap / total_market_cap) * available_weight
                # Apply position limits
                weight = min(weight, portfolio.max_position_weight)
                weight = max(weight, portfolio.min_position_weight)
                target_weights[holding.ticker] = weight

        # Normalize weights to sum to available weight
        total_weight = sum(target_weights.values())
        if total_weight > 0:
            adjustment_factor = available_weight / total_weight
            for ticker in target_weights:
                target_weights[ticker] *= adjustment_factor

        return target_weights

    def calculate_risk_parity_weights(self, portfolio: Portfolio,
                                    returns_data: Optional[Dict[str, List[float]]] = None) -> Dict[str, float]:
        """
        Calculate risk parity (equal risk contribution) weights

        Args:
            portfolio: Portfolio to rebalance
            returns_data: Historical returns data for volatility calculation

        Returns:
            Dictionary mapping ticker to target weight
        """
        if not portfolio.holdings:
            return {}

        # Use beta as proxy for risk if no returns data available
        risk_measures = {}
        for holding in portfolio.holdings:
            if returns_data and holding.ticker in returns_data:
                # Calculate volatility from returns
                returns = np.array(returns_data[holding.ticker])
                risk_measures[holding.ticker] = np.std(returns) if len(returns) > 1 else 1.0
            elif holding.beta:
                # Use beta as risk proxy
                risk_measures[holding.ticker] = abs(holding.beta)
            else:
                # Default risk measure
                risk_measures[holding.ticker] = 1.0

        # Calculate inverse volatility weights
        if not risk_measures:
            return self.calculate_equal_weight_targets(portfolio)

        inverse_vol_weights = {ticker: 1.0 / risk for ticker, risk in risk_measures.items()}
        total_inverse_vol = sum(inverse_vol_weights.values())

        # Normalize to available weight
        available_weight = 1.0 - portfolio.target_cash_allocation
        target_weights = {}

        for ticker, inv_vol in inverse_vol_weights.items():
            weight = (inv_vol / total_inverse_vol) * available_weight
            # Apply position limits
            weight = min(weight, portfolio.max_position_weight)
            weight = max(weight, portfolio.min_position_weight)
            target_weights[ticker] = weight

        return target_weights

    def calculate_optimized_weights(self, portfolio: Portfolio,
                                  expected_returns: Dict[str, float],
                                  covariance_matrix: Optional[np.ndarray] = None,
                                  risk_aversion: float = 1.0) -> Dict[str, float]:
        """
        Calculate optimized weights using mean-variance optimization

        Args:
            portfolio: Portfolio to optimize
            expected_returns: Expected returns for each holding
            covariance_matrix: Covariance matrix of returns
            risk_aversion: Risk aversion parameter (higher = more risk averse)

        Returns:
            Dictionary mapping ticker to target weight
        """
        tickers = [h.ticker for h in portfolio.holdings]
        n_assets = len(tickers)

        if n_assets == 0:
            return {}

        # Create expected returns vector
        mu = np.array([expected_returns.get(ticker, 0.05) for ticker in tickers])

        # Create covariance matrix if not provided
        if covariance_matrix is None:
            # Simple diagonal matrix using beta as risk proxy
            variances = []
            for holding in portfolio.holdings:
                if holding.beta:
                    # Estimate variance from beta (assuming market variance of 0.04)
                    variance = (holding.beta ** 2) * 0.04
                else:
                    variance = 0.04  # Default 20% volatility
                variances.append(variance)
            covariance_matrix = np.diag(variances)

        # Objective function: minimize -return + risk_aversion * risk
        def objective(weights):
            portfolio_return = np.dot(weights, mu)
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(covariance_matrix, weights)))
            return -portfolio_return + risk_aversion * portfolio_risk

        # Constraints
        available_weight = 1.0 - portfolio.target_cash_allocation
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - available_weight}  # Weights sum to available weight
        ]

        # Bounds for each weight
        bounds = []
        for _ in range(n_assets):
            bounds.append((portfolio.min_position_weight, portfolio.max_position_weight))

        # Initial guess (equal weights)
        x0 = np.array([available_weight / n_assets] * n_assets)

        # Optimize
        try:
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
            if result.success:
                return dict(zip(tickers, result.x))
        except Exception as e:
            logger.warning(f"Optimization failed: {str(e)}")

        # Fall back to equal weights
        return self.calculate_equal_weight_targets(portfolio)

    def apply_momentum_adjustment(self, portfolio: Portfolio,
                                current_weights: Dict[str, float],
                                momentum_scores: Dict[str, float],
                                adjustment_factor: float = 0.1) -> Dict[str, float]:
        """
        Apply momentum-based adjustments to position weights

        Args:
            portfolio: Portfolio instance
            current_weights: Current target weights
            momentum_scores: Momentum scores for each holding (-1 to 1)
            adjustment_factor: How much to adjust weights based on momentum

        Returns:
            Adjusted weights dictionary
        """
        adjusted_weights = current_weights.copy()

        for ticker, momentum in momentum_scores.items():
            if ticker in adjusted_weights:
                # Positive momentum increases weight, negative decreases
                adjustment = momentum * adjustment_factor * adjusted_weights[ticker]
                new_weight = adjusted_weights[ticker] + adjustment

                # Apply position limits
                new_weight = min(new_weight, portfolio.max_position_weight)
                new_weight = max(new_weight, portfolio.min_position_weight)
                adjusted_weights[ticker] = new_weight

        # Renormalize weights
        total_weight = sum(adjusted_weights.values())
        available_weight = 1.0 - portfolio.target_cash_allocation

        if total_weight > 0:
            adjustment_factor = available_weight / total_weight
            for ticker in adjusted_weights:
                adjusted_weights[ticker] *= adjustment_factor

        return adjusted_weights


class PortfolioRebalancer:
    """
    Implements portfolio rebalancing logic and strategies
    """

    def __init__(self, transaction_cost_bps: float = 10.0, min_trade_size: float = 100.0):
        """
        Initialize rebalancer

        Args:
            transaction_cost_bps: Transaction costs in basis points
            min_trade_size: Minimum trade size to avoid tiny trades
        """
        self.transaction_cost_bps = transaction_cost_bps
        self.min_trade_size = min_trade_size
        self.position_sizer = PositionSizer(transaction_cost_bps)

    def needs_rebalancing(self, portfolio: Portfolio) -> Tuple[bool, str]:
        """
        Determine if portfolio needs rebalancing

        Args:
            portfolio: Portfolio to check

        Returns:
            Tuple of (needs_rebalancing, reason)
        """
        # Check threshold-based rebalancing
        if portfolio.rebalancing_strategy == RebalancingStrategy.THRESHOLD:
            max_deviation = max(abs(h.weight_deviation) for h in portfolio.holdings) if portfolio.holdings else 0
            if max_deviation > portfolio.rebalancing_threshold:
                return True, f"Weight deviation {max_deviation:.2%} exceeds threshold {portfolio.rebalancing_threshold:.2%}"

        # Check periodic rebalancing
        elif portfolio.rebalancing_strategy == RebalancingStrategy.PERIODIC:
            if portfolio.last_rebalance_date:
                days_since = (date.today() - portfolio.last_rebalance_date).days
                if days_since >= portfolio.rebalancing_frequency_days:
                    return True, f"Periodic rebalancing due ({days_since} days since last rebalance)"

        # Check if any position exceeds maximum weight
        for holding in portfolio.holdings:
            if holding.current_weight > portfolio.max_position_weight:
                return True, f"{holding.ticker} weight {holding.current_weight:.2%} exceeds maximum {portfolio.max_position_weight:.2%}"

        # Check if any position is below minimum weight
        for holding in portfolio.holdings:
            if holding.current_weight < portfolio.min_position_weight and holding.current_weight > 0:
                return True, f"{holding.ticker} weight {holding.current_weight:.2%} below minimum {portfolio.min_position_weight:.2%}"

        return False, "No rebalancing needed"

    def calculate_target_weights(self, portfolio: Portfolio,
                               market_data: Optional[Dict[str, Dict]] = None,
                               momentum_scores: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Calculate target weights based on portfolio's position sizing method

        Args:
            portfolio: Portfolio to calculate targets for
            market_data: Additional market data for calculations
            momentum_scores: Momentum scores for momentum-based adjustments

        Returns:
            Dictionary mapping ticker to target weight
        """
        # Base calculation based on position sizing method
        if portfolio.position_sizing_method == PositionSizingMethod.EQUAL_WEIGHT:
            target_weights = self.position_sizer.calculate_equal_weight_targets(portfolio)

        elif portfolio.position_sizing_method == PositionSizingMethod.MARKET_CAP_WEIGHT:
            target_weights = self.position_sizer.calculate_market_cap_weights(portfolio)

        elif portfolio.position_sizing_method == PositionSizingMethod.RISK_PARITY:
            returns_data = market_data.get('returns') if market_data else None
            target_weights = self.position_sizer.calculate_risk_parity_weights(portfolio, returns_data)

        elif portfolio.position_sizing_method == PositionSizingMethod.OPTIMIZATION:
            expected_returns = market_data.get('expected_returns', {}) if market_data else {}
            covariance_matrix = market_data.get('covariance_matrix') if market_data else None
            target_weights = self.position_sizer.calculate_optimized_weights(
                portfolio, expected_returns, covariance_matrix
            )

        elif portfolio.position_sizing_method == PositionSizingMethod.CUSTOM_WEIGHTS:
            # Use existing target weights
            target_weights = {h.ticker: h.target_weight for h in portfolio.holdings}

        else:
            # Default to equal weight
            target_weights = self.position_sizer.calculate_equal_weight_targets(portfolio)

        # Apply momentum adjustments if using momentum strategy
        if (portfolio.rebalancing_strategy == RebalancingStrategy.MOMENTUM and
            momentum_scores):
            target_weights = self.position_sizer.apply_momentum_adjustment(
                portfolio, target_weights, momentum_scores
            )

        return target_weights

    def create_rebalancing_plan(self, portfolio: Portfolio,
                              target_weights: Optional[Dict[str, float]] = None,
                              market_data: Optional[Dict[str, Dict]] = None) -> RebalancingPlan:
        """
        Create detailed rebalancing plan

        Args:
            portfolio: Portfolio to rebalance
            target_weights: Target weights (calculated if not provided)
            market_data: Market data for calculations

        Returns:
            RebalancingPlan with detailed transactions
        """
        # Check if rebalancing is needed
        needs_rebalancing, reason = self.needs_rebalancing(portfolio)

        if not needs_rebalancing and target_weights is None:
            return RebalancingPlan(
                portfolio_id=portfolio.portfolio_id,
                rebalancing_reason="No rebalancing needed"
            )

        # Calculate target weights if not provided
        if target_weights is None:
            target_weights = self.calculate_target_weights(portfolio, market_data)

        # Calculate total portfolio value
        total_value = portfolio.portfolio_metrics.total_value + portfolio.cash_position

        # Create rebalancing plan
        plan = RebalancingPlan(
            portfolio_id=portfolio.portfolio_id,
            total_portfolio_value=total_value,
            rebalancing_reason=reason
        )

        # Calculate transactions for each holding
        for holding in portfolio.holdings:
            ticker = holding.ticker
            target_weight = target_weights.get(ticker, 0.0)

            # Calculate target value and shares
            target_value = target_weight * total_value
            current_value = holding.market_value or 0.0

            if holding.current_price and holding.current_price > 0:
                current_shares = holding.shares
                target_shares = target_value / holding.current_price
                shares_to_trade = target_shares - current_shares

                # Determine action
                if abs(shares_to_trade) < self.min_trade_size:
                    action = "HOLD"
                    shares_to_trade = 0.0
                elif shares_to_trade > 0:
                    action = "BUY"
                else:
                    action = "SELL"
                    shares_to_trade = abs(shares_to_trade)

                # Calculate transaction costs
                trade_value = abs(shares_to_trade * holding.current_price)
                estimated_cost = trade_value * (self.transaction_cost_bps / 10000.0)

                # Create transaction
                transaction = RebalancingTransaction(
                    ticker=ticker,
                    action=action,
                    current_shares=current_shares,
                    target_shares=target_shares,
                    shares_to_trade=shares_to_trade,
                    current_weight=holding.current_weight,
                    target_weight=target_weight,
                    current_value=current_value,
                    target_value=target_value,
                    estimated_cost=estimated_cost
                )

                # Set priority based on deviation size
                deviation = abs(holding.current_weight - target_weight)
                if deviation > portfolio.rebalancing_threshold * 2:
                    transaction.priority = 1  # High priority
                elif deviation > portfolio.rebalancing_threshold:
                    transaction.priority = 2  # Medium priority
                else:
                    transaction.priority = 3  # Low priority

                plan.transactions.append(transaction)

                # Update cash impact
                if action == "BUY":
                    plan.cash_needed += trade_value + estimated_cost
                elif action == "SELL":
                    plan.cash_generated += trade_value - estimated_cost

                plan.estimated_total_costs += estimated_cost

        # Calculate net cash impact
        plan.net_cash_impact = plan.cash_needed - plan.cash_generated

        # Set priority level for overall plan
        high_priority_count = sum(1 for t in plan.transactions if t.priority == 1)
        if high_priority_count > 0:
            plan.priority_level = "high"
        elif any(t.priority == 2 for t in plan.transactions):
            plan.priority_level = "medium"
        else:
            plan.priority_level = "low"

        return plan

    def execute_rebalancing_plan(self, portfolio: Portfolio, plan: RebalancingPlan) -> bool:
        """
        Execute rebalancing plan (simulated - updates portfolio state)

        Args:
            portfolio: Portfolio to rebalance
            plan: Rebalancing plan to execute

        Returns:
            True if execution successful
        """
        try:
            # Check if sufficient cash is available
            if plan.net_cash_impact > portfolio.cash_position:
                logger.error(f"Insufficient cash for rebalancing: need {plan.net_cash_impact}, have {portfolio.cash_position}")
                return False

            # Execute transactions
            for transaction in plan.transactions:
                holding = portfolio.get_holding(transaction.ticker)
                if holding:
                    if transaction.action == "BUY":
                        holding.shares = transaction.target_shares
                        holding.market_value = transaction.target_value
                    elif transaction.action == "SELL":
                        holding.shares = transaction.target_shares
                        holding.market_value = transaction.target_value

                    # Update target weight
                    holding.target_weight = transaction.target_weight

            # Update cash position
            portfolio.cash_position -= plan.net_cash_impact

            # Update portfolio state
            portfolio.last_rebalance_date = date.today()
            portfolio._calculate_weights()
            portfolio._update_portfolio_metrics()

            logger.info(f"Successfully executed rebalancing plan for portfolio {portfolio.portfolio_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to execute rebalancing plan: {str(e)}")
            return False

    def get_rebalancing_recommendations(self, portfolio: Portfolio) -> List[str]:
        """
        Get human-readable rebalancing recommendations

        Args:
            portfolio: Portfolio to analyze

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check if rebalancing is needed
        needs_rebalancing, reason = self.needs_rebalancing(portfolio)

        if needs_rebalancing:
            recommendations.append(f"Rebalancing recommended: {reason}")

            # Create a sample plan to get specific recommendations
            plan = self.create_rebalancing_plan(portfolio)

            # High priority transactions
            high_priority = [t for t in plan.transactions if t.priority == 1]
            if high_priority:
                recommendations.append(f"High priority adjustments needed for {len(high_priority)} positions")

            # Cash requirements
            if plan.net_cash_impact > 0:
                recommendations.append(f"Will require ${plan.net_cash_impact:,.2f} in additional cash")
            elif plan.net_cash_impact < 0:
                recommendations.append(f"Will generate ${abs(plan.net_cash_impact):,.2f} in cash")

            # Transaction costs
            if plan.estimated_total_costs > 0:
                cost_pct = (plan.estimated_total_costs / plan.total_portfolio_value) * 100
                recommendations.append(f"Estimated transaction costs: ${plan.estimated_total_costs:,.2f} ({cost_pct:.3f}%)")

        else:
            recommendations.append("Portfolio is well-balanced, no rebalancing needed")

        return recommendations