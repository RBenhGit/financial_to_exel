"""
Portfolio Backtesting Framework Example
=======================================

This module demonstrates how to use the portfolio backtesting framework
to test investment strategies, analyze performance, and generate reports.

Examples covered:
1. Basic backtest setup and execution
2. Custom transaction cost modeling
3. Multiple strategy comparison
4. Regime analysis and stress testing
5. Monte Carlo simulation for strategy robustness
6. Performance report generation
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.analysis.portfolio.portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    RebalancingStrategy,
    PositionSizingMethod,
    create_sample_portfolio
)
from core.analysis.portfolio.portfolio_backtesting import (
    BacktestEngine,
    BacktestResult,
    BacktestPeriod,
    TransactionCostModel,
    MarketRegime,
    StressScenario
)

logger = logging.getLogger(__name__)


def create_growth_portfolio() -> Portfolio:
    """Create a sample growth-focused portfolio for backtesting"""

    holdings = [
        PortfolioHolding(
            ticker="AAPL",
            company_name="Apple Inc.",
            target_weight=0.20,
            current_price=175.0
        ),
        PortfolioHolding(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            target_weight=0.20,
            current_price=350.0
        ),
        PortfolioHolding(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            target_weight=0.15,
            current_price=140.0
        ),
        PortfolioHolding(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            target_weight=0.15,
            current_price=450.0
        ),
        PortfolioHolding(
            ticker="TSLA",
            company_name="Tesla Inc.",
            target_weight=0.10,
            current_price=250.0
        ),
        PortfolioHolding(
            ticker="AMZN",
            company_name="Amazon.com Inc.",
            target_weight=0.10,
            current_price=150.0
        ),
        PortfolioHolding(
            ticker="META",
            company_name="Meta Platforms Inc.",
            target_weight=0.10,
            current_price=300.0
        )
    ]

    portfolio = Portfolio(
        portfolio_id="growth_tech_001",
        name="Growth Technology Portfolio",
        description="High-growth technology stocks with quarterly rebalancing",
        portfolio_type=PortfolioType.GROWTH,
        rebalancing_strategy=RebalancingStrategy.PERIODIC,
        position_sizing_method=PositionSizingMethod.CUSTOM_WEIGHTS,
        holdings=holdings,
        rebalancing_frequency_days=90,  # Quarterly
        rebalancing_threshold=0.05,     # 5% deviation threshold
        max_position_weight=0.25,       # 25% max per position
        min_position_weight=0.05,       # 5% minimum per position
        target_cash_allocation=0.00     # Fully invested
    )

    return portfolio


def create_value_portfolio() -> Portfolio:
    """Create a sample value-focused portfolio for backtesting"""

    holdings = [
        PortfolioHolding(
            ticker="BRK.B",
            company_name="Berkshire Hathaway Inc.",
            target_weight=0.25,
            current_price=350.0
        ),
        PortfolioHolding(
            ticker="JPM",
            company_name="JPMorgan Chase & Co.",
            target_weight=0.20,
            current_price=150.0
        ),
        PortfolioHolding(
            ticker="JNJ",
            company_name="Johnson & Johnson",
            target_weight=0.15,
            current_price=160.0
        ),
        PortfolioHolding(
            ticker="PG",
            company_name="Procter & Gamble Co.",
            target_weight=0.15,
            current_price=155.0
        ),
        PortfolioHolding(
            ticker="KO",
            company_name="The Coca-Cola Company",
            target_weight=0.15,
            current_price=60.0
        ),
        PortfolioHolding(
            ticker="WMT",
            company_name="Walmart Inc.",
            target_weight=0.10,
            current_price=160.0
        )
    ]

    portfolio = Portfolio(
        portfolio_id="value_dividend_001",
        name="Value Dividend Portfolio",
        description="Value stocks with strong dividend yields and annual rebalancing",
        portfolio_type=PortfolioType.VALUE,
        rebalancing_strategy=RebalancingStrategy.THRESHOLD,
        position_sizing_method=PositionSizingMethod.CUSTOM_WEIGHTS,
        holdings=holdings,
        rebalancing_frequency_days=365,  # Annual
        rebalancing_threshold=0.10,      # 10% deviation threshold (less frequent)
        max_position_weight=0.30,        # 30% max per position
        min_position_weight=0.08,        # 8% minimum per position
        target_cash_allocation=0.00      # Fully invested
    )

    return portfolio


def generate_sample_price_data(tickers: List[str],
                             start_date: str = "2019-01-01",
                             end_date: str = "2023-12-31",
                             annual_return: float = 0.10,
                             annual_volatility: float = 0.20) -> pd.DataFrame:
    """
    Generate sample price data for backtesting

    Args:
        tickers: List of ticker symbols
        start_date: Start date string
        end_date: End date string
        annual_return: Expected annual return
        annual_volatility: Annual volatility

    Returns:
        DataFrame with price data
    """
    # Create date range (business days only)
    dates = pd.bdate_range(start=start_date, end=end_date)

    # Calculate daily parameters
    daily_return = annual_return / 252
    daily_vol = annual_volatility / np.sqrt(252)

    # Create price data
    np.random.seed(42)  # For reproducible results
    price_data = pd.DataFrame(index=dates, columns=tickers)

    for ticker in tickers:
        # Generate correlated returns (some correlation between stocks)
        market_factor = np.random.normal(daily_return * 0.5, daily_vol * 0.7, len(dates))
        idiosyncratic = np.random.normal(daily_return * 0.5, daily_vol * 0.5, len(dates))

        # Combine for total returns
        returns = market_factor + idiosyncratic

        # Add some ticker-specific characteristics
        if ticker in ["NVDA", "TSLA"]:  # Higher volatility for growth stocks
            returns += np.random.normal(0, daily_vol * 0.5, len(dates))
        elif ticker in ["KO", "JNJ", "PG"]:  # Lower volatility for defensive stocks
            returns *= 0.7

        # Convert to prices starting at $100
        prices = 100 * np.cumprod(1 + returns)
        price_data[ticker] = prices

    return price_data


def generate_benchmark_data(price_data: pd.DataFrame) -> pd.DataFrame:
    """Generate benchmark data (S&P 500 proxy)"""

    # Create a market-cap weighted benchmark
    np.random.seed(42)

    # Simulate S&P 500 returns
    daily_return = 0.10 / 252  # 10% annual return
    daily_vol = 0.16 / np.sqrt(252)  # 16% annual volatility

    returns = np.random.normal(daily_return, daily_vol, len(price_data))
    benchmark_prices = 100 * np.cumprod(1 + returns)

    benchmark_data = pd.DataFrame(
        {"SPY": benchmark_prices},
        index=price_data.index
    )

    return benchmark_data


def run_basic_backtest_example():
    """Example 1: Basic backtest setup and execution"""

    print("=" * 60)
    print("Example 1: Basic Portfolio Backtest")
    print("=" * 60)

    # Create portfolio
    portfolio = create_growth_portfolio()

    # Get tickers from portfolio
    tickers = [h.ticker for h in portfolio.holdings]

    # Generate sample data
    print("Generating sample price data...")
    price_data = generate_sample_price_data(tickers)
    benchmark_data = generate_benchmark_data(price_data)

    # Setup backtest engine
    engine = BacktestEngine(
        initial_capital=100000.0,
        risk_free_rate=0.02
    )

    # Run backtest
    print("Running backtest...")
    result = engine.run_backtest(
        strategy_portfolio=portfolio,
        price_data=price_data,
        benchmark_data=benchmark_data,
        backtest_period=BacktestPeriod.FIVE_YEARS,
        rebalancing_frequency=90  # Quarterly
    )

    # Print results
    print_backtest_summary(result)

    return result


def run_transaction_cost_comparison():
    """Example 2: Compare performance with different transaction cost models"""

    print("\n" + "=" * 60)
    print("Example 2: Transaction Cost Impact Analysis")
    print("=" * 60)

    portfolio = create_growth_portfolio()
    tickers = [h.ticker for h in portfolio.holdings]
    price_data = generate_sample_price_data(tickers)
    benchmark_data = generate_benchmark_data(price_data)

    # Test different transaction cost scenarios
    cost_scenarios = [
        ("No Costs", TransactionCostModel(0.0, 0.0, 0.0, 0.0)),
        ("Low Costs", TransactionCostModel(0.0005, 0.0002, 0.0001, 0.0001)),
        ("Moderate Costs", TransactionCostModel(0.001, 0.0005, 0.0002, 0.0002)),
        ("High Costs", TransactionCostModel(0.002, 0.001, 0.0005, 0.0005))
    ]

    results = []

    for scenario_name, cost_model in cost_scenarios:
        print(f"Testing {scenario_name}...")

        engine = BacktestEngine(
            initial_capital=100000.0,
            transaction_cost_model=cost_model
        )

        result = engine.run_backtest(
            strategy_portfolio=portfolio,
            price_data=price_data,
            benchmark_data=benchmark_data,
            backtest_period=BacktestPeriod.FIVE_YEARS
        )

        results.append((scenario_name, result))

    # Compare results
    print("\nTransaction Cost Impact Comparison:")
    print("-" * 80)
    print(f"{'Scenario':<15} {'Total Return':<12} {'Ann. Return':<12} {'Sharpe':<8} {'Total Costs':<12}")
    print("-" * 80)

    for scenario_name, result in results:
        print(f"{scenario_name:<15} {result.total_return:>10.2%} {result.annualized_return:>10.2%} "
              f"{result.sharpe_ratio:>6.2f} ${result.total_transaction_costs:>10,.0f}")

    return results


def run_strategy_comparison():
    """Example 3: Compare different portfolio strategies"""

    print("\n" + "=" * 60)
    print("Example 3: Strategy Comparison")
    print("=" * 60)

    # Create different portfolios
    growth_portfolio = create_growth_portfolio()
    value_portfolio = create_value_portfolio()

    # Get all unique tickers
    all_tickers = list(set([h.ticker for h in growth_portfolio.holdings] +
                          [h.ticker for h in value_portfolio.holdings]))

    # Generate price data for all tickers
    price_data = generate_sample_price_data(all_tickers)
    benchmark_data = generate_benchmark_data(price_data)

    portfolios = [
        ("Growth Tech", growth_portfolio),
        ("Value Dividend", value_portfolio)
    ]

    results = []

    for strategy_name, portfolio in portfolios:
        print(f"Backtesting {strategy_name} strategy...")

        # Filter price data to portfolio tickers
        portfolio_tickers = [h.ticker for h in portfolio.holdings]
        portfolio_price_data = price_data[portfolio_tickers].copy()

        engine = BacktestEngine(initial_capital=100000.0)

        result = engine.run_backtest(
            strategy_portfolio=portfolio,
            price_data=portfolio_price_data,
            benchmark_data=benchmark_data,
            backtest_period=BacktestPeriod.FIVE_YEARS
        )

        results.append((strategy_name, result))

    # Compare strategies
    print("\nStrategy Performance Comparison:")
    print("-" * 100)
    print(f"{'Strategy':<15} {'Total Return':<12} {'Ann. Return':<12} {'Volatility':<10} "
          f"{'Sharpe':<8} {'Max DD':<8} {'Alpha':<8}")
    print("-" * 100)

    for strategy_name, result in results:
        alpha_str = f"{result.alpha:.3f}" if result.alpha is not None else "N/A"
        print(f"{strategy_name:<15} {result.total_return:>10.2%} {result.annualized_return:>10.2%} "
              f"{result.volatility:>8.2%} {result.sharpe_ratio:>6.2f} {result.max_drawdown:>6.2%} "
              f"{alpha_str:>6}")

    return results


def run_regime_analysis_example():
    """Example 4: Regime analysis and stress testing"""

    print("\n" + "=" * 60)
    print("Example 4: Regime Analysis and Stress Testing")
    print("=" * 60)

    portfolio = create_growth_portfolio()
    tickers = [h.ticker for h in portfolio.holdings]

    # Generate more volatile data to show regime differences
    price_data = generate_sample_price_data(
        tickers,
        annual_volatility=0.25  # Higher volatility
    )
    benchmark_data = generate_benchmark_data(price_data)

    engine = BacktestEngine(initial_capital=100000.0)

    result = engine.run_backtest(
        strategy_portfolio=portfolio,
        price_data=price_data,
        benchmark_data=benchmark_data,
        backtest_period=BacktestPeriod.FIVE_YEARS
    )

    # Analyze regimes
    if result.regime_analysis:
        print("\nMarket Regime Analysis:")
        print("-" * 60)

        for regime, performance in result.regime_analysis.regime_performance.items():
            if performance['days'] > 0:
                print(f"{regime.value.title():<15}: {performance['annualized_return']:>8.2%} return, "
                      f"{performance['volatility']:>6.2%} vol, {performance['days']:>3} days")

        if result.regime_analysis.best_regime and result.regime_analysis.worst_regime:
            print(f"\nBest Regime: {result.regime_analysis.best_regime.value.title()}")
            print(f"Worst Regime: {result.regime_analysis.worst_regime.value.title()}")

    # Stress testing results
    if result.stress_test_results:
        print("\nStress Testing Results:")
        print("-" * 60)

        for stress_result in result.stress_test_results:
            print(f"{stress_result.scenario.value}: {stress_result.stress_period_return:>8.2%} return, "
                  f"Max loss: {stress_result.max_loss:>6.2%}")

    return result


def run_monte_carlo_simulation():
    """Example 5: Monte Carlo simulation for strategy robustness"""

    print("\n" + "=" * 60)
    print("Example 5: Monte Carlo Strategy Robustness")
    print("=" * 60)

    portfolio = create_growth_portfolio()
    tickers = [h.ticker for h in portfolio.holdings]

    # Run multiple simulations with different random seeds
    n_simulations = 50
    results = []

    print(f"Running {n_simulations} Monte Carlo simulations...")

    for i in range(n_simulations):
        # Generate different random price paths
        np.random.seed(i)  # Different seed for each simulation

        price_data = generate_sample_price_data(tickers)
        benchmark_data = generate_benchmark_data(price_data)

        engine = BacktestEngine(initial_capital=100000.0)

        result = engine.run_backtest(
            strategy_portfolio=portfolio,
            price_data=price_data,
            benchmark_data=benchmark_data,
            backtest_period=BacktestPeriod.THREE_YEARS
        )

        results.append(result)

        if (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{n_simulations} simulations")

    # Analyze results distribution
    total_returns = [r.total_return for r in results]
    sharpe_ratios = [r.sharpe_ratio for r in results]
    max_drawdowns = [r.max_drawdown for r in results]

    print("\nMonte Carlo Results Summary:")
    print("-" * 50)
    print(f"{'Metric':<20} {'Mean':<10} {'Std':<10} {'5th %ile':<10} {'95th %ile':<10}")
    print("-" * 50)

    metrics = [
        ("Total Return", total_returns),
        ("Sharpe Ratio", sharpe_ratios),
        ("Max Drawdown", max_drawdowns)
    ]

    for metric_name, values in metrics:
        mean_val = np.mean(values)
        std_val = np.std(values)
        p5 = np.percentile(values, 5)
        p95 = np.percentile(values, 95)

        if "Return" in metric_name or "Drawdown" in metric_name:
            print(f"{metric_name:<20} {mean_val:>8.2%} {std_val:>8.2%} {p5:>8.2%} {p95:>8.2%}")
        else:
            print(f"{metric_name:<20} {mean_val:>8.2f} {std_val:>8.2f} {p5:>8.2f} {p95:>8.2f}")

    # Calculate probability of positive Sharpe ratio
    positive_sharpe_prob = np.mean([s > 0 for s in sharpe_ratios])
    print(f"\nProbability of positive Sharpe ratio: {positive_sharpe_prob:.1%}")

    return results


def print_backtest_summary(result: BacktestResult):
    """Print a comprehensive backtest summary"""

    print(f"\nBacktest Results for {result.strategy_name}")
    print("=" * 50)

    # Basic performance
    print("Performance Summary:")
    print(f"  Period: {result.start_date} to {result.end_date}")
    print(f"  Initial Capital: ${result.initial_capital:,.0f}")
    print(f"  Final Value: ${result.final_value:,.0f}")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Annualized Return: {result.annualized_return:.2%}")
    print(f"  Volatility: {result.volatility:.2%}")

    # Risk-adjusted metrics
    print("\nRisk-Adjusted Metrics:")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"  Calmar Ratio: {result.calmar_ratio:.2f}")
    print(f"  Maximum Drawdown: {result.max_drawdown:.2%}")

    # Benchmark comparison
    if result.benchmark_return is not None:
        print("\nBenchmark Comparison:")
        print(f"  Benchmark Return: {result.benchmark_return:.2%}")
        if result.alpha is not None:
            print(f"  Alpha: {result.alpha:.3f}")
        if result.beta is not None:
            print(f"  Beta: {result.beta:.2f}")
        if result.tracking_error is not None:
            print(f"  Tracking Error: {result.tracking_error:.2%}")
        if result.information_ratio is not None:
            print(f"  Information Ratio: {result.information_ratio:.2f}")

    # Transaction analysis
    print("\nTransaction Analysis:")
    print(f"  Total Transactions: {result.total_transactions}")
    print(f"  Total Transaction Costs: ${result.total_transaction_costs:,.0f}")
    print(f"  Transaction Cost Impact: {result.transaction_cost_impact:.3%}")

    # Risk metrics
    print("\nRisk Metrics:")
    print(f"  95% VaR: {result.var_95:.2%}")
    print(f"  99% VaR: {result.var_99:.2%}")
    print(f"  Expected Shortfall (95%): {result.expected_shortfall_95:.2%}")
    print(f"  Win Rate: {result.win_rate:.1%}")

    # Quality metrics
    print("\nQuality Assessment:")
    print(f"  Data Quality: {result.data_quality.value}")
    print(f"  Backtest Reliability: {result.backtest_reliability:.1%}")


def run_all_examples():
    """Run all backtesting examples"""

    print("Portfolio Backtesting Framework Examples")
    print("=" * 70)

    # Run all examples
    example_functions = [
        run_basic_backtest_example,
        run_transaction_cost_comparison,
        run_strategy_comparison,
        run_regime_analysis_example,
        run_monte_carlo_simulation
    ]

    results = {}

    for func in example_functions:
        try:
            result = func()
            results[func.__name__] = result
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)

    return results


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Run examples
    results = run_all_examples()