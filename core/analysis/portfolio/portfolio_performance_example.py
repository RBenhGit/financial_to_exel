"""
Portfolio Performance Analytics Usage Example
============================================

This example demonstrates how to use the comprehensive portfolio performance
analytics system to analyze portfolio returns, risk metrics, and attribution.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date

from .portfolio_models import Portfolio, PortfolioHolding, create_sample_portfolio
from .portfolio_performance_analytics import (
    PortfolioPerformanceAnalyzer,
    PerformancePeriod,
    create_sample_performance_data
)


def demonstrate_portfolio_performance_analysis():
    """
    Comprehensive demonstration of portfolio performance analytics features
    """
    print("=== Portfolio Performance Analytics Demo ===\n")

    # Step 1: Create a sample portfolio
    print("1. Creating sample portfolio...")
    portfolio = create_sample_portfolio()

    print(f"Portfolio: {portfolio.name}")
    print(f"Holdings: {len(portfolio.holdings)} positions")
    print(f"Total Value: ${portfolio.portfolio_metrics.total_value:,.2f}")
    print()

    # Step 2: Generate sample market data
    print("2. Generating sample market data...")
    price_data, benchmark_data = create_sample_performance_data(
        portfolio, days=252, volatility=0.18
    )
    print(f"Price data: {len(price_data)} days of data")
    print(f"Holdings tracked: {list(price_data.columns)}")
    print()

    # Step 3: Initialize performance analyzer
    print("3. Initializing performance analyzer...")
    analyzer = PortfolioPerformanceAnalyzer(portfolio, risk_free_rate=0.03)
    analyzer.set_price_history(price_data)
    analyzer.set_benchmark_history(benchmark_data)
    print("Performance analyzer initialized with market data")
    print()

    # Step 4: Calculate portfolio returns
    print("4. Calculating portfolio returns...")

    # Daily returns
    daily_returns = analyzer.calculate_portfolio_returns(PerformancePeriod.DAILY)
    print(f"Daily returns calculated: {len(daily_returns)} periods")
    print(f"Average daily return: {daily_returns.mean():.4f}")
    print(f"Daily volatility: {daily_returns.std():.4f}")

    # Monthly returns
    monthly_returns = analyzer.calculate_portfolio_returns(PerformancePeriod.MONTHLY)
    print(f"Monthly returns calculated: {len(monthly_returns)} periods")
    print(f"Average monthly return: {monthly_returns.mean():.4f}")
    print()

    # Step 5: Comprehensive performance metrics
    print("5. Calculating comprehensive performance metrics...")

    # Annual performance metrics with benchmark comparison
    annual_metrics = analyzer.calculate_performance_metrics(
        PerformancePeriod.ANNUAL,
        benchmark_ticker="SPY"
    )

    print("=== Annual Performance Metrics ===")
    print(f"Total Return: {annual_metrics.total_return:.2%}" if annual_metrics.total_return is not None else "Total Return: N/A")
    print(f"Annualized Return: {annual_metrics.annualized_return:.2%}" if annual_metrics.annualized_return is not None else "Annualized Return: N/A")
    print(f"Volatility: {annual_metrics.volatility:.2%}" if annual_metrics.volatility is not None else "Volatility: N/A")
    print(f"Sharpe Ratio: {annual_metrics.sharpe_ratio:.3f}" if annual_metrics.sharpe_ratio is not None else "Sharpe Ratio: N/A")
    print(f"Sortino Ratio: {annual_metrics.sortino_ratio:.3f}" if annual_metrics.sortino_ratio is not None else "Sortino Ratio: N/A")
    print(f"Calmar Ratio: {annual_metrics.calmar_ratio:.3f}" if annual_metrics.calmar_ratio is not None else "Calmar Ratio: N/A")
    print()

    print("=== Risk Metrics ===")
    print(f"Maximum Drawdown: {annual_metrics.max_drawdown:.2%}" if annual_metrics.max_drawdown is not None else "Maximum Drawdown: N/A")
    print(f"VaR (95%): {annual_metrics.var_95:.2%}" if annual_metrics.var_95 is not None else "VaR (95%): N/A")
    print(f"VaR (99%): {annual_metrics.var_99:.2%}" if annual_metrics.var_99 is not None else "VaR (99%): N/A")
    print(f"Win Rate: {annual_metrics.win_rate:.1%}" if annual_metrics.win_rate is not None else "Win Rate: N/A")
    print()

    # Benchmark comparison (if available)
    if annual_metrics.alpha is not None:
        print("=== Benchmark Comparison ===")
        print(f"Alpha: {annual_metrics.alpha:.2%}")
        print(f"Beta: {annual_metrics.beta:.3f}")
        print(f"R-squared: {annual_metrics.r_squared:.3f}")
        print(f"Tracking Error: {annual_metrics.tracking_error:.2%}")
        print(f"Information Ratio: {annual_metrics.information_ratio:.3f}")
        print(f"Benchmark: {annual_metrics.benchmark_used}")
        print()

    # Step 6: Attribution analysis
    print("6. Performing attribution analysis...")
    try:
        attribution = analyzer.calculate_attribution_analysis("SPY")

        print("=== Performance Attribution ===")
        print(f"Total Excess Return: {attribution.total_excess_return:.2%}")
        print(f"Allocation Effect: {attribution.allocation_effect:.2%}")
        print(f"Selection Effect: {attribution.selection_effect:.2%}")
        print(f"Interaction Effect: {attribution.interaction_effect:.2%}")
        print(f"Cash Drag: {attribution.cash_drag:.2%}")
        print()
    except Exception as e:
        print(f"Attribution analysis skipped: {str(e)}")
        print()

    # Step 7: Multi-period analysis
    print("7. Multi-period performance comparison...")

    periods = [PerformancePeriod.MONTHLY, PerformancePeriod.QUARTERLY, PerformancePeriod.ANNUAL]

    print("Period\t\tReturn\t\tVolatility\tSharpe Ratio")
    print("-" * 55)

    for period in periods:
        metrics = analyzer.calculate_performance_metrics(period)
        ann_ret = f"{metrics.annualized_return:.2%}" if metrics.annualized_return is not None else "N/A"
        vol = f"{metrics.volatility:.2%}" if metrics.volatility is not None else "N/A"
        sharpe = f"{metrics.sharpe_ratio:.3f}" if metrics.sharpe_ratio is not None else "N/A"
        print(f"{period.value}\t\t{ann_ret}\t\t{vol}\t\t{sharpe}")

    print()

    # Step 8: Comprehensive performance report
    print("8. Generating comprehensive performance report...")

    report = analyzer.generate_performance_report(
        periods=[PerformancePeriod.MONTHLY, PerformancePeriod.ANNUAL],
        benchmark_ticker="SPY"
    )

    print("=== Portfolio Performance Report ===")
    print(f"Portfolio ID: {report['portfolio_info']['portfolio_id']}")
    print(f"Portfolio Name: {report['portfolio_info']['name']}")
    print(f"Total Value: ${report['portfolio_info']['total_value']:,.2f}")
    print(f"Number of Holdings: {report['portfolio_info']['number_of_holdings']}")
    print()

    # Display performance by period
    for period, perf in report['performance_by_period'].items():
        print(f"--- {period} Performance ---")
        print(f"Total Return: {perf['total_return']:.2%}" if perf['total_return'] is not None else "Total Return: N/A")
        print(f"Volatility: {perf['volatility']:.2%}" if perf['volatility'] is not None else "Volatility: N/A")
        print(f"Sharpe Ratio: {perf['sharpe_ratio']:.3f}" if perf['sharpe_ratio'] is not None else "Sharpe Ratio: N/A")
        print(f"Max Drawdown: {perf['max_drawdown']:.2%}" if perf['max_drawdown'] is not None else "Max Drawdown: N/A")
        print()

    # Risk analysis summary
    risk_summary = report['risk_analysis']
    print("=== Risk Analysis Summary ===")
    print(f"Portfolio Beta: {risk_summary.get('portfolio_beta', 'N/A')}")
    print(f"Concentration Risk: {risk_summary.get('concentration_risk', 0):.1%}")
    print(f"Largest Position: {risk_summary.get('largest_position', 0):.1%}")
    print(f"Risk Tolerance: {risk_summary.get('risk_tolerance', 'N/A')}")
    print()

    print("=== Analysis Complete ===")
    print("Portfolio performance analytics demonstration finished successfully!")
    return report


def compare_portfolio_strategies():
    """
    Demonstrate comparing different portfolio strategies
    """
    print("\n=== Portfolio Strategy Comparison ===\n")

    # Create different portfolio configurations
    strategies = {
        'Growth': {
            'holdings': [
                {'ticker': 'AAPL', 'weight': 0.25},
                {'ticker': 'MSFT', 'weight': 0.25},
                {'ticker': 'GOOGL', 'weight': 0.25},
                {'ticker': 'AMZN', 'weight': 0.25}
            ],
            'volatility': 0.22
        },
        'Balanced': {
            'holdings': [
                {'ticker': 'AAPL', 'weight': 0.15},
                {'ticker': 'MSFT', 'weight': 0.15},
                {'ticker': 'JNJ', 'weight': 0.20},
                {'ticker': 'PG', 'weight': 0.20},
                {'ticker': 'SPY', 'weight': 0.30}
            ],
            'volatility': 0.16
        },
        'Conservative': {
            'holdings': [
                {'ticker': 'JNJ', 'weight': 0.30},
                {'ticker': 'PG', 'weight': 0.30},
                {'ticker': 'KO', 'weight': 0.20},
                {'ticker': 'VZ', 'weight': 0.20}
            ],
            'volatility': 0.12
        }
    }

    results = {}

    for strategy_name, config in strategies.items():
        print(f"Analyzing {strategy_name} Strategy...")

        # Create portfolio for this strategy
        holdings = []
        for i, holding_config in enumerate(config['holdings']):
            holding = PortfolioHolding(
                ticker=holding_config['ticker'],
                target_weight=holding_config['weight'],
                shares=100,  # Simplified
                current_price=100,  # Simplified
                market_value=10000 * holding_config['weight']
            )
            holdings.append(holding)

        portfolio = Portfolio(
            portfolio_id=f"{strategy_name.lower()}_001",
            name=f"{strategy_name} Portfolio",
            holdings=holdings
        )

        # Generate performance data
        price_data, benchmark_data = create_sample_performance_data(
            portfolio, days=252, volatility=config['volatility']
        )

        # Analyze performance
        analyzer = PortfolioPerformanceAnalyzer(portfolio, risk_free_rate=0.03)
        analyzer.set_price_history(price_data)
        analyzer.set_benchmark_history(benchmark_data)

        metrics = analyzer.calculate_performance_metrics(PerformancePeriod.ANNUAL, "SPY")

        results[strategy_name] = {
            'return': metrics.annualized_return,
            'volatility': metrics.volatility,
            'sharpe': metrics.sharpe_ratio,
            'max_drawdown': metrics.max_drawdown,
            'win_rate': metrics.win_rate
        }

        print(f"  Return: {metrics.annualized_return:.2%}")
        print(f"  Volatility: {metrics.volatility:.2%}")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
        print()

    # Comparison summary
    print("=== Strategy Comparison Summary ===")
    print("Strategy\t\tReturn\t\tVolatility\tSharpe\t\tMax DD")
    print("-" * 70)

    for strategy, metrics in results.items():
        print(f"{strategy:<15}\t{metrics['return']:.2%}\t\t{metrics['volatility']:.2%}\t\t{metrics['sharpe']:.3f}\t\t{metrics['max_drawdown']:.2%}")

    # Find best strategy by risk-adjusted return
    best_sharpe = max(results.items(), key=lambda x: x[1]['sharpe'])
    print(f"\nBest Risk-Adjusted Performance: {best_sharpe[0]} (Sharpe: {best_sharpe[1]['sharpe']:.3f})")

    return results


if __name__ == "__main__":
    # Run the demonstrations
    print("Portfolio Performance Analytics Examples")
    print("=" * 50)

    # Main demonstration
    report = demonstrate_portfolio_performance_analysis()

    # Strategy comparison
    comparison_results = compare_portfolio_strategies()

    print("\nAll demonstrations completed successfully!")
    print("Check the generated reports and metrics above for detailed analysis.")