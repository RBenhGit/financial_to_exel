"""
Portfolio Analysis Usage Example
===============================

This example demonstrates how to use the portfolio analysis system to:
1. Create portfolios using strategy templates
2. Integrate with existing financial analysis
3. Perform rebalancing and optimization
4. Generate comprehensive portfolio reports

Run this example to see the complete portfolio analysis workflow.
"""

import logging
from datetime import date
from typing import Dict, List

from . import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    PortfolioStrategyFactory,
    PortfolioCompanyIntegrator,
    PortfolioRebalancer,
    create_portfolio_from_template,
    create_sample_portfolio
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_create_growth_portfolio() -> Portfolio:
    """Example: Create a growth-focused portfolio"""
    print("\n" + "="*60)
    print("Creating Growth Portfolio")
    print("="*60)

    # Get growth strategy template
    growth_template = PortfolioStrategyFactory.create_growth_strategy()
    print(f"Strategy: {growth_template.name}")
    print(f"Description: {growth_template.description}")
    print(f"Risk Tolerance: {growth_template.risk_tolerance}")
    print(f"Max Position Weight: {growth_template.max_position_weight:.1%}")

    # Sample holdings data for a growth portfolio
    holdings_data = [
        {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'shares': 100,
            'current_price': 175.00,
            'target_weight': 0.20
        },
        {
            'ticker': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'shares': 50,
            'current_price': 350.00,
            'target_weight': 0.18
        },
        {
            'ticker': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'shares': 25,
            'current_price': 140.00,
            'target_weight': 0.15
        },
        {
            'ticker': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'shares': 40,
            'current_price': 450.00,
            'target_weight': 0.17
        },
        {
            'ticker': 'TSLA',
            'company_name': 'Tesla Inc.',
            'shares': 30,
            'current_price': 250.00,
            'target_weight': 0.12
        },
        {
            'ticker': 'META',
            'company_name': 'Meta Platforms Inc.',
            'shares': 35,
            'current_price': 300.00,
            'target_weight': 0.18
        }
    ]

    # Create portfolio from template
    portfolio = create_portfolio_from_template(
        template=growth_template,
        holdings_data=holdings_data,
        portfolio_id="growth_001",
        name="Tech Growth Portfolio"
    )

    # Set cash position
    portfolio.cash_position = 5000.00

    # Display portfolio information
    print(f"\nPortfolio Created: {portfolio.name}")
    print(f"Portfolio ID: {portfolio.portfolio_id}")
    print(f"Holdings: {len(portfolio.holdings)}")
    print(f"Total Value: ${portfolio.portfolio_metrics.total_value:,.2f}")
    print(f"Cash Position: ${portfolio.cash_position:,.2f}")

    print("\nHoldings Summary:")
    for holding in portfolio.holdings:
        print(f"  {holding.ticker}: {holding.shares} shares @ ${holding.current_price:.2f} "
              f"= ${holding.market_value:,.2f} ({holding.current_weight:.1%})")

    return portfolio


def example_rebalancing_analysis(portfolio: Portfolio) -> None:
    """Example: Analyze rebalancing needs and create plan"""
    print("\n" + "="*60)
    print("Rebalancing Analysis")
    print("="*60)

    rebalancer = PortfolioRebalancer(transaction_cost_bps=10.0)

    # Check if rebalancing is needed
    needs_rebalancing, reason = rebalancer.needs_rebalancing(portfolio)
    print(f"Needs Rebalancing: {needs_rebalancing}")
    print(f"Reason: {reason}")

    if needs_rebalancing:
        # Create rebalancing plan
        plan = rebalancer.create_rebalancing_plan(portfolio)

        print(f"\nRebalancing Plan:")
        print(f"Total Portfolio Value: ${plan.total_portfolio_value:,.2f}")
        print(f"Cash Needed: ${plan.cash_needed:,.2f}")
        print(f"Cash Generated: ${plan.cash_generated:,.2f}")
        print(f"Net Cash Impact: ${plan.net_cash_impact:,.2f}")
        print(f"Estimated Costs: ${plan.estimated_total_costs:,.2f}")
        print(f"Priority Level: {plan.priority_level}")

        print(f"\nTransactions ({len(plan.transactions)}):")
        for transaction in plan.transactions:
            print(f"  {transaction.ticker}: {transaction.action} "
                  f"{transaction.shares_to_trade:.0f} shares "
                  f"({transaction.current_weight:.1%} → {transaction.target_weight:.1%}) "
                  f"Priority: {transaction.priority}")

    # Get recommendations
    recommendations = rebalancer.get_rebalancing_recommendations(portfolio)
    print(f"\nRecommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def example_strategy_comparison() -> None:
    """Example: Compare different portfolio strategies"""
    print("\n" + "="*60)
    print("Strategy Comparison")
    print("="*60)

    strategies = PortfolioStrategyFactory.get_all_strategies()

    print(f"Available Strategies ({len(strategies)}):\n")

    for name, template in strategies.items():
        print(f"{template.name}:")
        print(f"  Type: {template.portfolio_type.value}")
        print(f"  Risk Tolerance: {template.risk_tolerance}")
        print(f"  Max Position Weight: {template.max_position_weight:.1%}")
        print(f"  Target Cash: {template.target_cash_allocation:.1%}")
        print(f"  Min Holdings: {template.min_holdings}")
        print(f"  Rebalancing: {template.rebalancing_strategy.value}")
        print(f"  Position Sizing: {template.position_sizing_method.value}")
        print(f"  Benchmark: {template.benchmark_ticker}")
        print()


def example_portfolio_integration() -> None:
    """Example: Integration with financial analysis"""
    print("\n" + "="*60)
    print("Portfolio-Financial Analysis Integration")
    print("="*60)

    # Create a sample portfolio
    portfolio = create_sample_portfolio()
    print(f"Sample Portfolio: {portfolio.name}")
    print(f"Holdings: {len(portfolio.holdings)}")

    # Create integrator
    integrator = PortfolioCompanyIntegrator()

    try:
        # Load company data (this would connect to FinancialCalculator)
        print("\nLoading company financial data...")
        company_data = integrator.load_portfolio_company_data(portfolio)

        print(f"Loaded data for {len(company_data)} companies:")
        for ticker, data in company_data.items():
            print(f"  {ticker}: Data completeness {data.data_completeness:.1%}")
            if data.latest_financials:
                print(f"    Revenue: ${data.latest_financials.revenue:,.0f}" if data.latest_financials.revenue else "    Revenue: N/A")
            if data.dcf_valuation:
                print(f"    DCF Fair Value: ${data.dcf_valuation.fair_value:.2f}" if data.dcf_valuation.fair_value else "    DCF: N/A")

        # Calculate weighted metrics
        weighted_metrics = integrator.calculate_portfolio_weighted_metrics(portfolio, company_data)
        print(f"\nPortfolio Weighted Metrics:")
        for metric, value in weighted_metrics.items():
            if isinstance(value, (int, float)):
                if 'ratio' in metric or 'beta' in metric:
                    print(f"  {metric}: {value:.3f}")
                else:
                    print(f"  {metric}: ${value:,.0f}")

        # Create comprehensive analysis
        analysis = integrator.create_portfolio_analysis_result(portfolio)
        print(f"\nPortfolio Analysis:")
        print(f"  Data Completeness: {analysis.data_completeness:.1%}")
        print(f"  Optimization Suggestions ({len(analysis.optimization_suggestions)}):")
        for suggestion in analysis.optimization_suggestions:
            print(f"    - {suggestion}")
        print(f"  Risk Warnings ({len(analysis.risk_warnings)}):")
        for warning in analysis.risk_warnings:
            print(f"    - {warning}")

    except Exception as e:
        print(f"Note: Financial integration requires actual company data: {str(e)}")
        print("In a real environment, this would connect to existing FinancialCalculator instances")


def run_complete_example() -> None:
    """Run the complete portfolio analysis example"""
    print("Portfolio Analysis System - Complete Example")
    print("=" * 80)

    try:
        # 1. Create a growth portfolio
        growth_portfolio = example_create_growth_portfolio()

        # 2. Analyze rebalancing needs
        example_rebalancing_analysis(growth_portfolio)

        # 3. Compare strategies
        example_strategy_comparison()

        # 4. Demonstrate integration
        example_portfolio_integration()

        print("\n" + "="*80)
        print("Example completed successfully!")
        print("="*80)

    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_complete_example()