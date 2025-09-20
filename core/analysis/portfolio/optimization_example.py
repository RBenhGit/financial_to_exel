"""
Portfolio Optimization Examples and Testing
==========================================

This module demonstrates the complete portfolio optimization system,
including Mean-Variance Optimization, Risk Parity, Black-Litterman,
and constraint-based optimization.

Features Demonstrated:
- Various optimization objectives (Max Sharpe, Min Volatility, Risk Parity)
- Efficient frontier calculation
- Black-Litterman model with investor views
- Constraint handling and validation
- Performance attribution and risk decomposition
- Integration with existing portfolio models
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, date

# Portfolio optimization imports
from .portfolio_optimization import (
    PortfolioOptimizer,
    OptimizationObjective,
    OptimizationMethod,
    OptimizationConstraints,
    OptimizationResult,
    create_sample_optimization_data,
    create_optimization_constraints_from_portfolio,
    apply_optimization_to_portfolio
)

# Black-Litterman imports
from .black_litterman import (
    BlackLittermanOptimizer,
    BlackLittermanInputs,
    InvestorView,
    ViewType,
    create_absolute_view,
    create_relative_view,
    create_sample_bl_optimization,
    integrate_black_litterman_with_portfolio
)

# Portfolio model imports
from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    create_sample_portfolio
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_optimization() -> None:
    """Example: Basic portfolio optimization with different objectives"""
    print("\n" + "="*80)
    print("Basic Portfolio Optimization Example")
    print("="*80)

    # Get sample data
    tickers, expected_returns, covariance_matrix = create_sample_optimization_data()

    print(f"Assets: {', '.join(tickers)}")
    print(f"Expected Returns: {[f'{ticker}: {ret:.1%}' for ticker, ret in expected_returns.items()]}")

    # Initialize optimizer
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)

    # Define different optimization objectives to test
    objectives = [
        OptimizationObjective.EQUAL_WEIGHT,
        OptimizationObjective.RISK_PARITY,
        OptimizationObjective.MIN_VOLATILITY,
        OptimizationObjective.MAX_SHARPE,
        OptimizationObjective.MAX_DIVERSIFICATION
    ]

    results = {}

    print(f"\nOptimization Results:")
    print("-" * 80)
    print(f"{'Objective':<20} {'Return':<10} {'Volatility':<12} {'Sharpe':<10} {'Top Holdings'}")
    print("-" * 80)

    for objective in objectives:
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=objective
        )

        if result.success:
            results[objective.value] = result

            # Get top 3 holdings
            sorted_weights = sorted(result.weights.items(), key=lambda x: x[1], reverse=True)
            top_holdings = [f"{ticker}({weight:.1%})" for ticker, weight in sorted_weights[:3]]

            print(f"{objective.value:<20} {result.expected_return:<9.1%} "
                  f"{result.expected_volatility:<11.1%} {result.sharpe_ratio:<9.2f} "
                  f"{', '.join(top_holdings)}")
        else:
            print(f"{objective.value:<20} {'FAILED':<10} {'FAILED':<12} {'FAILED':<10} {result.message}")

    # Detailed analysis of Max Sharpe portfolio
    if OptimizationObjective.MAX_SHARPE.value in results:
        sharpe_result = results[OptimizationObjective.MAX_SHARPE.value]
        print(f"\nMax Sharpe Portfolio Detailed Analysis:")
        print(f"Expected Return: {sharpe_result.expected_return:.2%}")
        print(f"Expected Volatility: {sharpe_result.expected_volatility:.2%}")
        print(f"Sharpe Ratio: {sharpe_result.sharpe_ratio:.3f}")

        print(f"\nAsset Allocation:")
        for ticker, weight in sorted(sharpe_result.weights.items(), key=lambda x: x[1], reverse=True):
            if weight > 0.01:  # Show weights > 1%
                print(f"  {ticker}: {weight:.1%}")

        if sharpe_result.risk_contribution:
            print(f"\nRisk Contribution:")
            for ticker, risk_contrib in sorted(sharpe_result.risk_contribution.items(), key=lambda x: x[1], reverse=True):
                if risk_contrib > 0.01:
                    print(f"  {ticker}: {risk_contrib:.1%}")


def example_efficient_frontier() -> None:
    """Example: Calculate and display efficient frontier"""
    print("\n" + "="*80)
    print("Efficient Frontier Calculation Example")
    print("="*80)

    # Get sample data
    tickers, expected_returns, covariance_matrix = create_sample_optimization_data()

    # Initialize optimizer
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)

    # Create basic constraints
    constraints = OptimizationConstraints(
        min_weight=0.0,
        max_weight=0.4,  # Max 40% in any single asset
        max_concentration=0.4
    )

    print(f"Calculating efficient frontier with constraints:")
    print(f"  Max position weight: {constraints.max_weight:.1%}")
    print(f"  Max concentration: {constraints.max_concentration:.1%}")

    # Calculate efficient frontier
    efficient_portfolios = optimizer.calculate_efficient_frontier(
        tickers=tickers,
        expected_returns=expected_returns,
        covariance_matrix=covariance_matrix,
        constraints=constraints,
        num_points=20
    )

    if efficient_portfolios:
        print(f"\nEfficient Frontier ({len(efficient_portfolios)} portfolios):")
        print("-" * 60)
        print(f"{'Return':<10} {'Volatility':<12} {'Sharpe':<10} {'Max Weight'}")
        print("-" * 60)

        for portfolio in efficient_portfolios:
            max_weight = max(portfolio.weights.values()) if portfolio.weights else 0.0
            print(f"{portfolio.expected_return:<9.1%} {portfolio.expected_volatility:<11.1%} "
                  f"{portfolio.sharpe_ratio:<9.2f} {max_weight:<9.1%}")

        # Find portfolio with best Sharpe ratio
        best_sharpe_portfolio = max(efficient_portfolios, key=lambda p: p.sharpe_ratio or 0)
        print(f"\nBest Sharpe Ratio Portfolio:")
        print(f"  Return: {best_sharpe_portfolio.expected_return:.2%}")
        print(f"  Volatility: {best_sharpe_portfolio.expected_volatility:.2%}")
        print(f"  Sharpe: {best_sharpe_portfolio.sharpe_ratio:.3f}")

        print(f"  Allocation:")
        for ticker, weight in sorted(best_sharpe_portfolio.weights.items(), key=lambda x: x[1], reverse=True):
            if weight > 0.01:
                print(f"    {ticker}: {weight:.1%}")

    else:
        print("Failed to calculate efficient frontier")


def example_black_litterman() -> None:
    """Example: Black-Litterman optimization with investor views"""
    print("\n" + "="*80)
    print("Black-Litterman Model Example")
    print("="*80)

    # Get sample Black-Litterman data
    tickers, bl_inputs = create_sample_bl_optimization()

    print(f"Assets: {', '.join(tickers)}")
    print(f"Market Caps: {[f'{ticker}: ${cap:.0f}B' for ticker, cap in bl_inputs.market_caps.items()]}")

    # Calculate market cap weights
    total_market_cap = sum(bl_inputs.market_caps.values())
    market_weights = {ticker: cap / total_market_cap for ticker, cap in bl_inputs.market_caps.items()}

    print(f"\nMarket Cap Weights:")
    for ticker, weight in sorted(market_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ticker}: {weight:.1%}")

    print(f"\nInvestor Views:")
    for i, view in enumerate(bl_inputs.views, 1):
        print(f"  {i}. {view.description} (Confidence: {view.confidence:.1%})")

    # Run Black-Litterman optimization
    bl_optimizer = BlackLittermanOptimizer()
    bl_result = bl_optimizer.optimize(tickers, bl_inputs)

    if bl_result.model_success:
        print(f"\nBlack-Litterman Results:")
        print(f"Expected Return: {bl_result.expected_return:.2%}")
        print(f"Expected Volatility: {bl_result.expected_volatility:.2%}")
        print(f"Sharpe Ratio: {bl_result.sharpe_ratio:.3f}")

        print(f"\nImplied vs Adjusted Returns:")
        print("-" * 50)
        print(f"{'Asset':<8} {'Implied':<10} {'Adjusted':<10} {'Difference'}")
        print("-" * 50)
        for ticker in tickers:
            implied = bl_result.implied_returns.get(ticker, 0.0)
            adjusted = bl_result.adjusted_returns.get(ticker, 0.0)
            diff = adjusted - implied
            print(f"{ticker:<8} {implied:<9.1%} {adjusted:<9.1%} {diff:>+7.1%}")

        print(f"\nOptimal Allocation vs Market Cap Weights:")
        print("-" * 60)
        print(f"{'Asset':<8} {'Market Cap':<12} {'BL Optimal':<12} {'Deviation'}")
        print("-" * 60)
        for ticker in tickers:
            market_w = bl_result.market_cap_weights.get(ticker, 0.0)
            optimal_w = bl_result.optimal_weights.get(ticker, 0.0)
            deviation = bl_result.weight_deviations.get(ticker, 0.0)
            print(f"{ticker:<8} {market_w:<11.1%} {optimal_w:<11.1%} {deviation:>+7.1%}")

        if bl_result.view_impacts:
            print(f"\nView Impact Analysis:")
            for view_id, impact in bl_result.view_impacts.items():
                print(f"  {view_id}: Impact score {impact:.3f}")

    else:
        print(f"Black-Litterman optimization failed: {bl_result.error_message}")


def example_constraint_optimization() -> None:
    """Example: Optimization with various constraints"""
    print("\n" + "="*80)
    print("Constraint-Based Optimization Example")
    print("="*80)

    # Get sample data
    tickers, expected_returns, covariance_matrix = create_sample_optimization_data()

    # Initialize optimizer
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)

    # Define different constraint scenarios
    constraint_scenarios = [
        ("No Constraints", OptimizationConstraints()),
        ("Basic Limits", OptimizationConstraints(min_weight=0.05, max_weight=0.30)),
        ("Conservative", OptimizationConstraints(min_weight=0.10, max_weight=0.25, max_concentration=0.25)),
        ("Target Return", OptimizationConstraints(min_weight=0.0, max_weight=0.50, target_return=0.14)),
        ("Max Volatility", OptimizationConstraints(min_weight=0.0, max_weight=0.40, max_volatility=0.20))
    ]

    print(f"Testing different constraint scenarios:")
    print("-" * 100)
    print(f"{'Scenario':<15} {'Return':<10} {'Volatility':<12} {'Sharpe':<10} {'Max Weight':<12} {'Status'}")
    print("-" * 100)

    for scenario_name, constraints in constraint_scenarios:
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE,
            constraints=constraints
        )

        if result.success:
            max_weight = max(result.weights.values()) if result.weights else 0.0
            status = "✓ Satisfied" if result.constraints_satisfied else "⚠ Violations"

            print(f"{scenario_name:<15} {result.expected_return:<9.1%} "
                  f"{result.expected_volatility:<11.1%} {result.sharpe_ratio:<9.2f} "
                  f"{max_weight:<11.1%} {status}")

            if not result.constraints_satisfied and result.constraint_violations:
                print(f"    Violations: {'; '.join(result.constraint_violations[:2])}")

        else:
            print(f"{scenario_name:<15} {'FAILED':<10} {'FAILED':<12} {'FAILED':<10} "
                  f"{'FAILED':<12} {result.message}")


def example_portfolio_integration() -> None:
    """Example: Integration with Portfolio model"""
    print("\n" + "="*80)
    print("Portfolio Model Integration Example")
    print("="*80)

    # Create sample portfolio
    portfolio = create_sample_portfolio()

    print(f"Portfolio: {portfolio.name}")
    print(f"Type: {portfolio.portfolio_type.value}")
    print(f"Holdings: {len(portfolio.holdings)}")

    # Show current allocation
    print(f"\nCurrent Allocation:")
    total_value = sum(h.market_value or 0 for h in portfolio.holdings)
    for holding in portfolio.holdings:
        if holding.market_value:
            weight = holding.market_value / total_value
            print(f"  {holding.ticker}: {weight:.1%} (Target: {holding.target_weight:.1%})")

    # Create constraints from portfolio settings
    constraints = create_optimization_constraints_from_portfolio(portfolio)

    print(f"\nPortfolio Constraints:")
    print(f"  Min Weight: {constraints.min_weight:.1%}")
    print(f"  Max Weight: {constraints.max_weight:.1%}")
    print(f"  Max Concentration: {constraints.max_concentration:.1%}")

    # Get optimization data for portfolio holdings
    tickers = [h.ticker for h in portfolio.holdings]
    expected_returns, covariance_matrix = create_simple_returns_data(tickers)

    # Optimize portfolio
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)
    result = optimizer.optimize_portfolio(
        tickers=tickers,
        expected_returns=expected_returns,
        covariance_matrix=covariance_matrix,
        objective=OptimizationObjective.MAX_SHARPE,
        constraints=constraints
    )

    if result.success:
        print(f"\nOptimization Results:")
        print(f"Expected Return: {result.expected_return:.2%}")
        print(f"Expected Volatility: {result.expected_volatility:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")

        print(f"\nOptimal vs Current Allocation:")
        print("-" * 50)
        print(f"{'Asset':<8} {'Current':<10} {'Optimal':<10} {'Change'}")
        print("-" * 50)

        for holding in portfolio.holdings:
            current_weight = holding.current_weight
            optimal_weight = result.weights.get(holding.ticker, 0.0)
            change = optimal_weight - current_weight

            print(f"{holding.ticker:<8} {current_weight:<9.1%} {optimal_weight:<9.1%} {change:>+7.1%}")

        # Apply optimization results to portfolio
        updated_portfolio = apply_optimization_to_portfolio(portfolio, result)

        print(f"\nRebalancing Analysis:")
        print(f"Average Deviation: {updated_portfolio.portfolio_metrics.deviation_from_targets:.1%}")
        print(f"Rebalancing Needed: {updated_portfolio.portfolio_metrics.rebalancing_needed}")

    else:
        print(f"Optimization failed: {result.message}")


def create_simple_returns_data(tickers: List[str]) -> tuple[Dict[str, float], np.ndarray]:
    """Create simple returns data for a list of tickers"""
    # Sample expected returns
    base_returns = {'AAPL': 0.12, 'MSFT': 0.14, 'GOOGL': 0.13, 'AMZN': 0.15, 'TSLA': 0.20}
    expected_returns = {ticker: base_returns.get(ticker, 0.10) for ticker in tickers}

    # Simple covariance matrix (assume moderate correlation)
    n = len(tickers)
    volatilities = np.array([0.25] * n)  # Assume 25% volatility for all
    correlation = 0.6  # Assume 60% correlation

    # Create correlation matrix
    corr_matrix = np.full((n, n), correlation)
    np.fill_diagonal(corr_matrix, 1.0)

    # Convert to covariance matrix
    covariance_matrix = np.outer(volatilities, volatilities) * corr_matrix

    return expected_returns, covariance_matrix


def run_comprehensive_optimization_example() -> None:
    """Run the complete portfolio optimization example suite"""
    print("Portfolio Optimization System - Comprehensive Examples")
    print("=" * 80)

    try:
        # 1. Basic optimization
        example_basic_optimization()

        # 2. Efficient frontier
        example_efficient_frontier()

        # 3. Black-Litterman
        example_black_litterman()

        # 4. Constraint optimization
        example_constraint_optimization()

        # 5. Portfolio integration
        example_portfolio_integration()

        print("\n" + "="*80)
        print("Portfolio Optimization Examples Completed Successfully!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✓ Mean-Variance Optimization with multiple objectives")
        print("✓ Risk Parity and Equal Weight allocation strategies")
        print("✓ Efficient Frontier calculation with constraints")
        print("✓ Black-Litterman model with investor views")
        print("✓ Constraint-based optimization and validation")
        print("✓ Integration with existing Portfolio models")
        print("✓ Performance attribution and risk decomposition")

    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_comprehensive_optimization_example()