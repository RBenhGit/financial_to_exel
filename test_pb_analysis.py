"""
Test script for P/B Analysis functionality

This script tests the P/B valuation module to ensure it works correctly
with real market data.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_valuation import PBValuator
from financial_calculations import FinancialCalculator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_pb_analysis():
    """Test P/B analysis with a mock financial calculator"""

    print("Testing P/B Analysis Module")
    print("=" * 50)

    try:
        # Create a mock financial calculator for testing
        # In real usage, this would be loaded with actual financial data
        financial_calculator = FinancialCalculator(company_folder=None)

        # Set ticker symbol for testing
        test_ticker = "MSFT"  # Microsoft as a test case
        financial_calculator.ticker_symbol = test_ticker
        financial_calculator.currency = "USD"
        financial_calculator.is_tase_stock = False

        # Mock balance sheet data with shareholders' equity
        financial_calculator.financial_data = {
            'Balance Sheet': {
                '2023': {
                    'Total Stockholder Equity': 206223,  # Example: Microsoft's equity in millions
                    'Total Assets': 411976,
                    'Total Debt': 47082,
                }
            }
        }

        print(f"Testing P/B analysis for {test_ticker}")
        print("-" * 30)

        # Create P/B valuator
        pb_valuator = PBValuator(financial_calculator)

        # Perform P/B analysis
        print("Calculating P/B analysis...")
        pb_analysis = pb_valuator.calculate_pb_analysis(test_ticker)

        # Check results
        if 'error' in pb_analysis:
            print(f"P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error')}")
            print(f"Error type: {pb_analysis.get('error')}")
            return False

        # Display results
        print("P/B Analysis completed successfully!")
        print("\nResults Summary:")
        print("-" * 20)

        current_data = pb_analysis.get('current_data', {})
        if current_data:
            print(f"Current Price: ${current_data.get('current_price', 0):.2f}")
            print(f"Book Value per Share: ${current_data.get('book_value_per_share', 0):.2f}")
            pb_ratio = current_data.get('pb_ratio')
            if pb_ratio:
                print(f"P/B Ratio: {pb_ratio:.2f}")
            print(f"Market Cap: ${current_data.get('market_cap', 0):,.0f}")

        # Industry comparison
        industry_comp = pb_analysis.get('industry_comparison', {})
        if 'position' in industry_comp:
            print(f"\nIndustry Position: {industry_comp['position']}")
            print(f"Industry Key: {industry_comp.get('industry_key', 'Unknown')}")
            benchmarks = industry_comp.get('benchmarks', {})
            if benchmarks:
                print(f"Industry Median P/B: {benchmarks.get('median', 0):.2f}")
                print(f"Full benchmarks: {benchmarks}")

        # Valuation ranges
        valuation_analysis = pb_analysis.get('valuation_analysis', {})
        if 'valuation_ranges' in valuation_analysis:
            ranges = valuation_analysis['valuation_ranges']
            print(f"\nP/B Based Valuation:")
            print(f"Conservative: ${ranges.get('conservative', 0):.2f}")
            print(f"Fair Value: ${ranges.get('fair_value', 0):.2f}")
            print(f"Optimistic: ${ranges.get('optimistic', 0):.2f}")

        # Risk assessment
        risk_assess = pb_analysis.get('risk_assessment', {})
        if 'risk_level' in risk_assess:
            print(f"\nRisk Level: {risk_assess['risk_level']}")

        # Generate summary report
        print("\nSummary Report:")
        print("-" * 20)
        summary_report = pb_valuator.create_pb_summary_report(pb_analysis)
        print(summary_report)

        return True

    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
        logger.error(f"Test exception: {e}", exc_info=True)
        return False


def test_pb_industry_mapping():
    """Test industry mapping functionality"""
    print("\nTesting Industry Mapping")
    print("=" * 30)

    # Create a test valuator
    financial_calculator = FinancialCalculator(company_folder=None)
    pb_valuator = PBValuator(financial_calculator)

    # Test sector mappings
    test_sectors = [
        'Technology',
        'Healthcare',
        'Financial Services',
        'Consumer Cyclical',
        'Energy',
        'Unknown Sector',
    ]

    for sector in test_sectors:
        mapped = pb_valuator._map_to_benchmark_industry(sector)
        benchmarks = pb_valuator.industry_benchmarks.get(mapped, {})
        print(f"{sector:20} -> {mapped:20} (Median P/B: {benchmarks.get('median', 0):.2f})")

    return True


if __name__ == "__main__":
    print("Starting P/B Analysis Tests")
    print("=" * 60)

    success = True

    # Test 1: Basic P/B analysis
    success &= test_pb_analysis()

    # Test 2: Industry mapping
    success &= test_pb_industry_mapping()

    print("\n" + "=" * 60)
    if success:
        print("All P/B analysis tests completed successfully!")
    else:
        print("Some tests failed. Check the output above for details.")

    print("\nNote: This test uses live market data from yfinance.")
    print("Network connectivity is required for full functionality testing.")
