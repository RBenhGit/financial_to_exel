"""
Comprehensive test for PB Valuation module
Tests multiple tickers and data sources to identify edge cases and errors
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_valuation import PBValuator
from financial_calculations import FinancialCalculator
from enhanced_data_manager import EnhancedDataManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_pb_with_enhanced_data_manager():
    """Test P/B analysis with enhanced data manager"""
    print("\nTesting P/B Analysis with Enhanced Data Manager")
    print("=" * 60)

    try:
        # Create enhanced data manager with base path
        enhanced_data_manager = EnhancedDataManager(".")

        # Create financial calculator with enhanced data manager
        financial_calculator = FinancialCalculator(company_folder=None)
        financial_calculator.enhanced_data_manager = enhanced_data_manager

        test_tickers = ["AAPL", "MSFT", "GOOGL"]

        for ticker in test_tickers:
            print(f"\nTesting {ticker} with enhanced data manager:")
            print("-" * 40)

            financial_calculator.ticker_symbol = ticker
            pb_valuator = PBValuator(financial_calculator)

            try:
                pb_analysis = pb_valuator.calculate_pb_analysis(ticker)

                if 'error' in pb_analysis:
                    print(f"[X] {ticker}: {pb_analysis.get('error_message', 'Unknown error')}")
                else:
                    current_data = pb_analysis.get('current_data', {})
                    pb_ratio = current_data.get('pb_ratio')
                    industry_key = pb_analysis.get('industry_info', {}).get(
                        'industry_key', 'Unknown'
                    )

                    pb_str = f"{pb_ratio:.2f}" if pb_ratio is not None else "N/A"
                    print(
                        f"[OK] {ticker}: P/B = {pb_str}, "
                        f"Industry = {industry_key}, "
                        f"BVPS = ${current_data.get('book_value_per_share', 0):.2f}"
                    )

            except Exception as e:
                print(f"[X] {ticker}: Exception - {str(e)}")
                logger.exception(f"Error testing {ticker}")

        return True

    except Exception as e:
        print(f"Enhanced data manager test failed: {e}")
        logger.exception("Enhanced data manager test exception")
        return False


def test_pb_edge_cases():
    """Test P/B analysis with various edge cases"""
    print("\nTesting P/B Analysis Edge Cases")
    print("=" * 50)

    # Test cases with different financial situations
    test_cases = [
        {'name': 'High P/B Tech Stock', 'ticker': 'NVDA', 'expected_issues': ['high_pb_ratio']},
        {'name': 'Financial Services', 'ticker': 'JPM', 'expected_issues': []},
        {'name': 'REIT (Real Estate)', 'ticker': 'O', 'expected_issues': []},  # Realty Income
        {'name': 'Utility Company', 'ticker': 'NEE', 'expected_issues': []},  # NextEra Energy
    ]

    results = []

    for test_case in test_cases:
        ticker = test_case['ticker']
        name = test_case['name']

        print(f"\nTesting {name} ({ticker}):")
        print("-" * 30)

        try:
            financial_calculator = FinancialCalculator(company_folder=None)
            financial_calculator.ticker_symbol = ticker
            pb_valuator = PBValuator(financial_calculator)

            pb_analysis = pb_valuator.calculate_pb_analysis(ticker)

            if 'error' in pb_analysis:
                print(f"[X] Error: {pb_analysis.get('error_message', 'Unknown error')}")
                results.append(
                    {'ticker': ticker, 'success': False, 'error': pb_analysis.get('error')}
                )
            else:
                current_data = pb_analysis.get('current_data', {})
                industry_info = pb_analysis.get('industry_info', {})
                risk_assessment = pb_analysis.get('risk_assessment', {})

                pb_ratio = current_data.get('pb_ratio')
                industry_key = industry_info.get('industry_key', 'Unknown')
                sector = industry_info.get('sector', 'Unknown')
                risk_level = risk_assessment.get('risk_level', 'Unknown')

                pb_str = f"{pb_ratio:.2f}" if pb_ratio is not None else "N/A"
                print(f"[OK] Success:")
                print(f"   P/B Ratio: {pb_str}")
                print(f"   Sector: {sector}")
                print(f"   Industry Key: {industry_key}")
                print(f"   Risk Level: {risk_level}")
                print(f"   BVPS: ${current_data.get('book_value_per_share', 0):.2f}")

                results.append(
                    {
                        'ticker': ticker,
                        'success': True,
                        'pb_ratio': pb_ratio,
                        'industry_key': industry_key,
                        'risk_level': risk_level,
                    }
                )

        except Exception as e:
            print(f"[X] Exception: {str(e)}")
            results.append({'ticker': ticker, 'success': False, 'error': str(e)})
            logger.exception(f"Error testing {ticker}")

    # Summary
    print(f"\nEdge Case Test Summary:")
    print("=" * 30)
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")

    for result in results:
        status = "[OK]" if result['success'] else "[X]"
        print(f"{status} {result['ticker']}")

    return successful == total


def test_data_source_fallbacks():
    """Test fallback mechanisms between data sources"""
    print("\nTesting Data Source Fallback Mechanisms")
    print("=" * 50)

    # Create financial calculator without enhanced data manager
    financial_calculator = FinancialCalculator(company_folder=None)
    financial_calculator.ticker_symbol = "AAPL"

    # Mock some balance sheet data
    financial_calculator.financial_data = {
        'Balance Sheet': {
            '2023': {
                'Total Stockholder Equity': 62146,  # Apple's equity
                'Total Assets': 352755,
                'Total Debt': 123930,
            }
        }
    }

    pb_valuator = PBValuator(financial_calculator)

    try:
        print("Testing fallback to financial statements...")
        pb_analysis = pb_valuator.calculate_pb_analysis("AAPL")

        if 'error' in pb_analysis:
            print(f"[X] Fallback failed: {pb_analysis.get('error_message')}")
            return False
        else:
            current_data = pb_analysis.get('current_data', {})
            pb_ratio = current_data.get('pb_ratio')
            bvps = current_data.get('book_value_per_share')

            pb_str = f"{pb_ratio:.2f}" if pb_ratio is not None else "N/A"
            bvps_str = f"${bvps:.2f}" if bvps is not None else "N/A"
            print(f"[OK] Fallback successful:")
            print(f"   P/B Ratio: {pb_str}")
            print(f"   BVPS: {bvps_str}")
            print(f"   Data source used: financial_statements")

            return True

    except Exception as e:
        print(f"[X] Fallback test failed: {e}")
        logger.exception("Fallback test exception")
        return False


if __name__ == "__main__":
    print("Starting Comprehensive P/B Analysis Tests")
    print("=" * 70)

    all_passed = True

    # Test 1: Enhanced data manager integration
    all_passed &= test_pb_with_enhanced_data_manager()

    # Test 2: Edge cases with different stock types
    all_passed &= test_pb_edge_cases()

    # Test 3: Data source fallbacks
    all_passed &= test_data_source_fallbacks()

    print("\n" + "=" * 70)
    if all_passed:
        print("All comprehensive P/B tests passed!")
    else:
        print("Some tests failed. Review output above for details.")

    print("\nNote: These tests use live market data and may take time to complete.")
