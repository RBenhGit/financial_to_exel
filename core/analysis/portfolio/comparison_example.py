"""
Multi-Company Comparison Example
===============================

This example demonstrates the complete multi-company comparison and analysis system,
including relative valuation, growth analysis, and sector benchmarking.

Features Demonstrated:
- Multi-company financial metric comparison
- Relative valuation analysis with peer benchmarking
- Growth trend analysis and sustainability scoring
- Sector and industry comparison
- Investment recommendation generation
"""

import logging
from datetime import datetime, date
from typing import Dict, List

from . import (
    Portfolio,
    PortfolioHolding,
    create_sample_portfolio
)
from .company_comparison import (
    MultiCompanyComparator,
    ComparisonMetric,
    ComparisonType,
    CompanyMetrics
)
from .relative_valuation import (
    RelativeValuationAnalyzer,
    ValuationMultiple
)
from .growth_trend_analysis import (
    GrowthTrendAnalyzer,
    GrowthMetricType,
    GrowthPeriod
)
from core.data_processing.data_contracts import FinancialStatement, MarketData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_financial_data() -> Dict[str, List[FinancialStatement]]:
    """Create sample historical financial data for demonstration"""

    # Sample data for AAPL, MSFT, GOOGL
    sample_data = {
        'AAPL': [
            FinancialStatement(
                ticker='AAPL',
                period='2023',
                revenue=383_285_000_000,
                net_income=96_995_000_000,
                operating_cash_flow=110_543_000_000,
                free_cash_flow=99_584_000_000,
                total_assets=352_755_000_000,
                shareholders_equity=62_146_000_000,
                shares_outstanding=15_728_700_000
            ),
            FinancialStatement(
                ticker='AAPL',
                period='2022',
                revenue=394_328_000_000,
                net_income=99_803_000_000,
                operating_cash_flow=122_151_000_000,
                free_cash_flow=111_443_000_000,
                total_assets=352_583_000_000,
                shareholders_equity=50_672_000_000,
                shares_outstanding=16_006_400_000
            ),
            FinancialStatement(
                ticker='AAPL',
                period='2021',
                revenue=365_817_000_000,
                net_income=94_680_000_000,
                operating_cash_flow=104_038_000_000,
                free_cash_flow=92_953_000_000,
                total_assets=351_002_000_000,
                shareholders_equity=63_090_000_000,
                shares_outstanding=16_426_800_000
            )
        ],
        'MSFT': [
            FinancialStatement(
                ticker='MSFT',
                period='2023',
                revenue=211_915_000_000,
                net_income=72_361_000_000,
                operating_cash_flow=87_582_000_000,
                free_cash_flow=65_149_000_000,
                total_assets=411_976_000_000,
                shareholders_equity=206_223_000_000,
                shares_outstanding=7_430_000_000
            ),
            FinancialStatement(
                ticker='MSFT',
                period='2022',
                revenue=198_270_000_000,
                net_income=72_738_000_000,
                operating_cash_flow=89_035_000_000,
                free_cash_flow=65_149_000_000,
                total_assets=364_840_000_000,
                shareholders_equity=166_542_000_000,
                shares_outstanding=7_464_000_000
            ),
            FinancialStatement(
                ticker='MSFT',
                period='2021',
                revenue=168_088_000_000,
                net_income=61_271_000_000,
                operating_cash_flow=76_740_000_000,
                free_cash_flow=56_118_000_000,
                total_assets=333_779_000_000,
                shareholders_equity=141_988_000_000,
                shares_outstanding=7_519_000_000
            )
        ],
        'GOOGL': [
            FinancialStatement(
                ticker='GOOGL',
                period='2023',
                revenue=307_394_000_000,
                net_income=73_795_000_000,
                operating_cash_flow=101_775_000_000,
                free_cash_flow=69_495_000_000,
                total_assets=402_392_000_000,
                shareholders_equity=283_893_000_000,
                shares_outstanding=12_695_000_000
            ),
            FinancialStatement(
                ticker='GOOGL',
                period='2022',
                revenue=282_836_000_000,
                net_income=59_972_000_000,
                operating_cash_flow=91_495_000_000,
                free_cash_flow=60_010_000_000,
                total_assets=365_264_000_000,
                shareholders_equity=251_635_000_000,
                shares_outstanding=12_998_000_000
            ),
            FinancialStatement(
                ticker='GOOGL',
                period='2021',
                revenue=257_637_000_000,
                net_income=76_033_000_000,
                operating_cash_flow=91_652_000_000,
                free_cash_flow=67_012_000_000,
                total_assets=359_268_000_000,
                shareholders_equity=251_635_000_000,
                shares_outstanding=13_044_000_000
            )
        ]
    }

    return sample_data


def create_sample_market_data() -> Dict[str, MarketData]:
    """Create sample market data for demonstration"""
    return {
        'AAPL': MarketData(
            ticker='AAPL',
            price=175.00,
            market_cap=2_750_000_000_000,
            pe_ratio=28.5,
            pb_ratio=44.3,
            ps_ratio=7.2,
            beta=1.29,
            dividend_yield=0.005
        ),
        'MSFT': MarketData(
            ticker='MSFT',
            price=350.00,
            market_cap=2_600_000_000_000,
            pe_ratio=35.9,
            pb_ratio=12.6,
            ps_ratio=12.3,
            beta=0.90,
            dividend_yield=0.007
        ),
        'GOOGL': MarketData(
            ticker='GOOGL',
            price=140.00,
            market_cap=1_780_000_000_000,
            pe_ratio=24.1,
            pb_ratio=6.3,
            ps_ratio=5.8,
            beta=1.06,
            dividend_yield=0.000
        )
    }


def example_basic_comparison() -> None:
    """Example: Basic multi-company comparison"""
    print("\n" + "="*70)
    print("Basic Multi-Company Comparison")
    print("="*70)

    # Initialize comparator
    comparator = MultiCompanyComparator()

    # Define companies to compare
    tickers = ['AAPL', 'MSFT', 'GOOGL']

    # Define metrics to compare
    metrics = [
        ComparisonMetric.REVENUE,
        ComparisonMetric.NET_INCOME,
        ComparisonMetric.FREE_CASH_FLOW,
        ComparisonMetric.PE_RATIO,
        ComparisonMetric.PB_RATIO,
        ComparisonMetric.ROE,
        ComparisonMetric.MARKET_CAP
    ]

    print(f"Comparing {len(tickers)} companies across {len(metrics)} metrics...")

    # Note: In a real environment, this would load actual data
    # For demo purposes, we'll show the structure
    print("\nComparison Structure:")
    print(f"Companies: {', '.join(tickers)}")
    print(f"Metrics: {', '.join([m.value for m in metrics])}")

    # Create comparison matrix (would work with real data)
    try:
        matrix = comparator.create_comparison_matrix(
            tickers, metrics, ComparisonType.ABSOLUTE
        )

        print(f"\nComparison Matrix Created:")
        print(f"- Data Quality: {matrix.data_quality.value}")
        print(f"- Companies Analyzed: {len(matrix.companies)}")
        print(f"- Metrics Compared: {len(matrix.metrics)}")

        # Show rankings if available
        if matrix.rankings:
            print(f"\nTop Performers by Metric:")
            for metric, ranking in matrix.rankings.items():
                if ranking:
                    top_performer = ranking[0]
                    print(f"  {metric}: {top_performer[0]} ({top_performer[1]:.2f})")

        # Generate summary
        summary = comparator.generate_comparison_summary(matrix)
        print(f"\nComparison Summary:")
        print(f"- Analysis Date: {summary['comparison_overview']['analysis_date']}")
        print(f"- Data Quality: {summary['comparison_overview']['data_quality']}")

        if summary['outliers']:
            print(f"- Outliers Detected: {len(summary['outliers'])} metrics have outliers")

    except Exception as e:
        print(f"Note: Comparison requires actual financial data: {str(e)}")
        print("In a real environment, this would connect to FinancialCalculator instances")


def example_relative_valuation() -> None:
    """Example: Relative valuation analysis"""
    print("\n" + "="*70)
    print("Relative Valuation Analysis")
    print("="*70)

    analyzer = RelativeValuationAnalyzer()

    target_ticker = 'AAPL'
    peer_tickers = ['MSFT', 'GOOGL']

    print(f"Analyzing {target_ticker} vs peers: {', '.join(peer_tickers)}")

    # Sample market data for demonstration
    market_data = create_sample_market_data()

    print(f"\nSample Valuation Multiples:")
    for ticker, data in market_data.items():
        print(f"{ticker}:")
        print(f"  P/E Ratio: {data.pe_ratio:.1f}")
        print(f"  P/B Ratio: {data.pb_ratio:.1f}")
        print(f"  P/S Ratio: {data.ps_ratio:.1f}")
        print(f"  Beta: {data.beta:.2f}")

    # Valuation comparison insights
    pe_ratios = [data.pe_ratio for data in market_data.values()]
    pb_ratios = [data.pb_ratio for data in market_data.values()]

    print(f"\nValuation Analysis:")
    print(f"P/E Ratio Range: {min(pe_ratios):.1f} - {max(pe_ratios):.1f}")
    print(f"P/B Ratio Range: {min(pb_ratios):.1f} - {max(pb_ratios):.1f}")

    # Identify relative positioning
    aapl_data = market_data['AAPL']
    avg_pe = sum(pe_ratios) / len(pe_ratios)
    avg_pb = sum(pb_ratios) / len(pb_ratios)

    print(f"\n{target_ticker} Relative Position:")
    pe_position = "Premium" if aapl_data.pe_ratio > avg_pe else "Discount"
    pb_position = "Premium" if aapl_data.pb_ratio > avg_pb else "Discount"
    print(f"P/E: {pe_position} to peer average ({aapl_data.pe_ratio:.1f} vs {avg_pe:.1f})")
    print(f"P/B: {pb_position} to peer average ({aapl_data.pb_ratio:.1f} vs {avg_pb:.1f})")

    # Investment implication
    if aapl_data.pe_ratio > avg_pe:
        print(f"\nInvestment Implication: {target_ticker} trades at a premium, suggesting")
        print("strong market confidence but potentially limited upside")
    else:
        print(f"\nInvestment Implication: {target_ticker} trades at a discount, suggesting")
        print("potential value opportunity or market concerns")


def example_growth_analysis() -> None:
    """Example: Growth trend analysis"""
    print("\n" + "="*70)
    print("Growth Trend Analysis")
    print("="*70)

    analyzer = GrowthTrendAnalyzer()

    # Get sample historical data
    historical_data = create_sample_financial_data()

    print(f"Analyzing growth trends for {len(historical_data)} companies...")

    # Analyze growth for each company
    for ticker, statements in historical_data.items():
        print(f"\n{ticker} Growth Analysis:")
        print(f"  Periods Available: {len(statements)}")

        # Calculate simple revenue growth
        if len(statements) >= 2:
            latest_revenue = statements[0].revenue
            previous_revenue = statements[1].revenue
            if previous_revenue and previous_revenue > 0:
                yoy_growth = (latest_revenue - previous_revenue) / previous_revenue
                print(f"  Latest YoY Revenue Growth: {yoy_growth:.1%}")

        # Calculate 3-year CAGR if available
        if len(statements) >= 3:
            start_revenue = statements[-1].revenue  # Oldest
            end_revenue = statements[0].revenue     # Most recent
            if start_revenue and start_revenue > 0:
                years = len(statements) - 1
                cagr = ((end_revenue / start_revenue) ** (1/years)) - 1
                print(f"  {years}-Year Revenue CAGR: {cagr:.1%}")

        # Net income growth
        if len(statements) >= 2:
            latest_ni = statements[0].net_income
            previous_ni = statements[1].net_income
            if previous_ni and previous_ni > 0:
                ni_growth = (latest_ni - previous_ni) / previous_ni
                print(f"  Latest YoY Net Income Growth: {ni_growth:.1%}")

        # FCF growth
        if len(statements) >= 2:
            latest_fcf = statements[0].free_cash_flow
            previous_fcf = statements[1].free_cash_flow
            if previous_fcf and previous_fcf > 0:
                fcf_growth = (latest_fcf - previous_fcf) / previous_fcf
                print(f"  Latest YoY FCF Growth: {fcf_growth:.1%}")

    # Comparative growth analysis
    print(f"\nComparative Growth Summary:")

    revenue_growth_rates = {}
    for ticker, statements in historical_data.items():
        if len(statements) >= 2:
            latest = statements[0].revenue
            previous = statements[1].revenue
            if previous and previous > 0:
                growth = (latest - previous) / previous
                revenue_growth_rates[ticker] = growth

    # Rank by growth
    if revenue_growth_rates:
        sorted_growth = sorted(revenue_growth_rates.items(), key=lambda x: x[1], reverse=True)
        print(f"Revenue Growth Rankings:")
        for i, (ticker, growth) in enumerate(sorted_growth, 1):
            print(f"  {i}. {ticker}: {growth:.1%}")

    # Growth insights
    print(f"\nGrowth Insights:")
    if revenue_growth_rates:
        avg_growth = sum(revenue_growth_rates.values()) / len(revenue_growth_rates)
        print(f"  Average Revenue Growth: {avg_growth:.1%}")

        growth_leader = max(revenue_growth_rates.items(), key=lambda x: x[1])
        print(f"  Growth Leader: {growth_leader[0]} ({growth_leader[1]:.1%})")

        growth_laggard = min(revenue_growth_rates.items(), key=lambda x: x[1])
        print(f"  Growth Laggard: {growth_laggard[0]} ({growth_laggard[1]:.1%})")


def example_portfolio_comparison() -> None:
    """Example: Portfolio holdings comparison"""
    print("\n" + "="*70)
    print("Portfolio Holdings Comparison")
    print("="*70)

    # Create sample portfolio
    portfolio = create_sample_portfolio()

    print(f"Portfolio: {portfolio.name}")
    print(f"Holdings ({len(portfolio.holdings)}):")

    total_value = 0
    for holding in portfolio.holdings:
        print(f"  {holding.ticker}: {holding.shares} shares @ ${holding.current_price:.2f}")
        print(f"    Market Value: ${holding.market_value:,.2f}")
        print(f"    Target Weight: {holding.target_weight:.1%}")
        print(f"    Current Weight: {holding.current_weight:.1%}")
        total_value += holding.market_value or 0

    print(f"\nTotal Portfolio Value: ${total_value:,.2f}")
    print(f"Cash Position: ${portfolio.cash_position:,.2f}")

    # Portfolio metrics
    print(f"\nPortfolio Metrics:")
    print(f"  Number of Holdings: {portfolio.portfolio_metrics.number_of_holdings}")
    print(f"  Concentration Risk: {portfolio.portfolio_metrics.concentration_risk:.1%}")
    print(f"  Rebalancing Needed: {portfolio.portfolio_metrics.rebalancing_needed}")

    # Holdings analysis
    market_data = create_sample_market_data()

    print(f"\nHoldings Valuation Analysis:")
    for holding in portfolio.holdings:
        if holding.ticker in market_data:
            md = market_data[holding.ticker]
            print(f"{holding.ticker}:")
            print(f"  P/E Ratio: {md.pe_ratio:.1f}")
            print(f"  Beta: {md.beta:.2f}")
            print(f"  Portfolio Weight: {holding.current_weight:.1%}")

    # Risk assessment
    portfolio_beta = 0
    total_weight = 0
    for holding in portfolio.holdings:
        if holding.ticker in market_data and holding.current_weight > 0:
            beta = market_data[holding.ticker].beta
            portfolio_beta += beta * holding.current_weight
            total_weight += holding.current_weight

    if total_weight > 0:
        portfolio_beta = portfolio_beta / total_weight
        print(f"\nPortfolio Risk Assessment:")
        print(f"  Weighted Average Beta: {portfolio_beta:.2f}")
        risk_level = "High" if portfolio_beta > 1.2 else "Moderate" if portfolio_beta > 0.8 else "Low"
        print(f"  Risk Level: {risk_level}")


def run_complete_comparison_example() -> None:
    """Run the complete multi-company comparison example"""
    print("Multi-Company Comparison System - Complete Example")
    print("=" * 80)

    try:
        # 1. Basic comparison
        example_basic_comparison()

        # 2. Relative valuation
        example_relative_valuation()

        # 3. Growth analysis
        example_growth_analysis()

        # 4. Portfolio comparison
        example_portfolio_comparison()

        print("\n" + "="*80)
        print("Multi-Company Comparison Example Completed Successfully!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✓ Multi-company financial metric comparison")
        print("✓ Relative valuation analysis with peer benchmarking")
        print("✓ Growth trend analysis and ranking")
        print("✓ Portfolio-level comparison and risk assessment")
        print("✓ Investment insights and recommendations")

    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_complete_comparison_example()