"""
Simple test for PB Valuation module - debug basic functionality
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


def test_simple_pb():
    """Test basic P/B functionality with just yfinance fallback"""
    print("Testing basic P/B functionality with yfinance...")

    # Test with Apple - should have good data availability
    financial_calculator = FinancialCalculator(company_folder=None)
    financial_calculator.ticker_symbol = "AAPL"

    pb_valuator = PBValuator(financial_calculator)

    try:
        pb_analysis = pb_valuator.calculate_pb_analysis("AAPL")

        if 'error' in pb_analysis:
            print(f"Error: {pb_analysis.get('error_message', 'Unknown error')}")
            print(f"Error type: {pb_analysis.get('error')}")
            return False
        else:
            current_data = pb_analysis.get('current_data', {})
            print(f"Success! P/B ratio: {current_data.get('pb_ratio', 'N/A')}")
            print(f"Book value per share: ${current_data.get('book_value_per_share', 0):.2f}")
            print(f"Current price: ${current_data.get('current_price', 0):.2f}")
            return True

    except Exception as e:
        print(f"Exception: {e}")
        logger.exception("Test exception")
        return False


def test_enhanced_data_manager_init():
    """Test if we can initialize the enhanced data manager"""
    print("\nTesting enhanced data manager initialization...")

    try:
        from enhanced_data_manager import EnhancedDataManager

        edm = EnhancedDataManager(".")

        print(f"Enhanced data manager created: {type(edm)}")
        print(f"Has unified_adapter: {hasattr(edm, 'unified_adapter')}")

        if hasattr(edm, 'unified_adapter') and edm.unified_adapter:
            print(f"Unified adapter type: {type(edm.unified_adapter)}")
            return True
        else:
            print("unified_adapter is None or missing")
            return False

    except Exception as e:
        print(f"Failed to initialize enhanced data manager: {e}")
        logger.exception("Enhanced data manager init exception")
        return False


if __name__ == "__main__":
    print("Simple P/B Analysis Test")
    print("=" * 40)

    # Test 1: Basic functionality
    success1 = test_simple_pb()

    # Test 2: Enhanced data manager
    success2 = test_enhanced_data_manager_init()

    print("\n" + "=" * 40)
    print(f"Basic test: {'PASS' if success1 else 'FAIL'}")
    print(f"Enhanced test: {'PASS' if success2 else 'FAIL'}")
