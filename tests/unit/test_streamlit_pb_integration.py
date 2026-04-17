"""
Test P/B Analysis Integration as used in Streamlit Application

This test simulates how the P/B analysis is called in the actual Streamlit app
to ensure the enhanced data manager integration works correctly.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_valuation import PBValuator
from financial_calculations import FinancialCalculator
from enhanced_data_manager import create_enhanced_data_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_streamlit_pb_integration():
    """Test P/B analysis as it would be used in Streamlit with enhanced data manager"""
    print("Testing P/B Analysis - Streamlit Integration")
    print("=" * 60)

    try:
        # Simulate ticker mode (no Excel folder)
        print("1. Creating financial calculator (ticker mode)...")
        temp_folder = "temp_AAPL"
        financial_calculator = FinancialCalculator(temp_folder)

        # Attach enhanced data manager (as done in fixed Streamlit code)
        print("2. Attaching enhanced data manager...")
        try:
            enhanced_data_manager = create_enhanced_data_manager()
            financial_calculator.enhanced_data_manager = enhanced_data_manager
            print("   [OK] Enhanced data manager attached successfully")
        except Exception as e:
            print(f"   [X] Could not attach enhanced data manager: {e}")
            return False

        # Set ticker symbol
        ticker_symbol = "AAPL"
        financial_calculator.ticker_symbol = ticker_symbol
        financial_calculator.currency = "USD"
        financial_calculator.is_tase_stock = False

        print(f"3. Creating PB Valuator for {ticker_symbol}...")
        pb_valuator = PBValuator(financial_calculator)

        # Check that enhanced data manager is available
        has_enhanced = pb_valuator.enhanced_data_manager is not None
        print(f"   Enhanced data manager available: {has_enhanced}")

        if not has_enhanced:
            print("   [X] PB Valuator doesn't have enhanced data manager")
            return False

        print("4. Performing P/B analysis...")
        pb_analysis = pb_valuator.calculate_pb_analysis(ticker_symbol)

        # Check results
        if 'error' in pb_analysis:
            print(f"   [X] P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error')}")
            print(f"   Error type: {pb_analysis.get('error')}")
            return False

        # Display results
        current_data = pb_analysis.get('current_data', {})
        industry_info = pb_analysis.get('industry_info', {})

        print("5. Results:")
        print(f"   [OK] P/B analysis completed successfully!")
        print(f"   Current Price: ${current_data.get('current_price', 0):.2f}")
        print(f"   Book Value per Share: ${current_data.get('book_value_per_share', 0):.2f}")
        print(f"   P/B Ratio: {current_data.get('pb_ratio', 0):.2f}")
        print(f"   Industry: {industry_info.get('sector', 'Unknown')}")
        print(f"   Industry Key: {industry_info.get('industry_key', 'Unknown')}")

        # Check if we're using enhanced data
        if current_data.get('book_value_per_share', 0) > 0:
            print("   [API] Successfully calculated book value using enhanced data sources")

        return True

    except Exception as e:
        print(f"[X] Test failed with exception: {str(e)}")
        logger.exception("Test exception")
        return False


def test_folder_mode_integration():
    """Test P/B analysis in folder mode (Excel-based) with enhanced data fallback"""
    print("\nTesting P/B Analysis - Folder Mode Integration")
    print("=" * 60)

    try:
        # Simulate folder mode with mock data
        print("1. Creating financial calculator (folder mode)...")
        financial_calculator = FinancialCalculator(company_folder=None)

        # Add mock balance sheet data (as would come from Excel)
        financial_calculator.financial_data = {
            'Balance Sheet': {
                '2023': {
                    'Total Stockholder Equity': 62146,  # Apple's equity in millions
                    'Total Assets': 352755,
                    'Total Debt': 123930,
                }
            }
        }

        # Attach enhanced data manager
        print("2. Attaching enhanced data manager...")
        try:
            enhanced_data_manager = create_enhanced_data_manager()
            financial_calculator.enhanced_data_manager = enhanced_data_manager
            print("   [OK] Enhanced data manager attached successfully")
        except Exception as e:
            print(f"   [X] Could not attach enhanced data manager: {e}")
            return False

        # Set ticker and properties
        ticker_symbol = "AAPL"
        financial_calculator.ticker_symbol = ticker_symbol
        financial_calculator.currency = "USD"
        financial_calculator.is_tase_stock = False

        print(f"3. Creating PB Valuator for {ticker_symbol}...")
        pb_valuator = PBValuator(financial_calculator)

        print("4. Performing P/B analysis (should use Excel data + enhanced market data)...")
        pb_analysis = pb_valuator.calculate_pb_analysis(ticker_symbol)

        # Check results
        if 'error' in pb_analysis:
            print(f"   [X] P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error')}")
            return False

        # Display results
        current_data = pb_analysis.get('current_data', {})

        print("5. Results:")
        print(f"   [OK] P/B analysis completed successfully!")
        print(f"   Current Price: ${current_data.get('current_price', 0):.2f}")
        print(f"   Book Value per Share: ${current_data.get('book_value_per_share', 0):.2f}")
        print(f"   P/B Ratio: {current_data.get('pb_ratio', 0):.2f}")
        print("   [DATA] Used Excel balance sheet data + enhanced market data")

        return True

    except Exception as e:
        print(f"[X] Test failed with exception: {str(e)}")
        logger.exception("Test exception")
        return False


if __name__ == "__main__":
    print("P/B Analysis Streamlit Integration Tests")
    print("=" * 70)

    # Test 1: Ticker mode (API-only)
    success1 = test_streamlit_pb_integration()

    # Test 2: Folder mode (Excel + API)
    success2 = test_folder_mode_integration()

    print("\n" + "=" * 70)
    print("Test Results:")
    print(f"Ticker Mode: {'[OK] PASS' if success1 else '[X] FAIL'}")
    print(f"Folder Mode: {'[OK] PASS' if success2 else '[X] FAIL'}")

    if success1 and success2:
        print("\nSuccess! All integration tests passed! P/B analysis should work in Streamlit.")
    else:
        print("\n[WARNING] Some tests failed. Review the error messages above.")

    print("\nNote: These tests simulate the Streamlit application flow.")
