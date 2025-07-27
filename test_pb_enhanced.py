"""
Test PB Valuation with Enhanced Data Manager
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


def test_with_enhanced_data_manager():
    """Test P/B analysis with enhanced data manager"""
    print("Testing P/B with Enhanced Data Manager...")

    try:
        # Create enhanced data manager
        edm = EnhancedDataManager(".")

        # Create financial calculator and attach enhanced data manager
        financial_calculator = FinancialCalculator(company_folder=None)
        financial_calculator.enhanced_data_manager = edm
        financial_calculator.ticker_symbol = "AAPL"

        print(
            f"Financial calculator has enhanced_data_manager: {hasattr(financial_calculator, 'enhanced_data_manager')}"
        )
        print(f"Enhanced data manager type: {type(financial_calculator.enhanced_data_manager)}")

        # Create PB valuator
        pb_valuator = PBValuator(financial_calculator)

        print(
            f"PB valuator has enhanced_data_manager: {pb_valuator.enhanced_data_manager is not None}"
        )

        # Try the analysis
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
        logger.exception("Enhanced test exception")
        return False


if __name__ == "__main__":
    print("Enhanced P/B Analysis Test")
    print("=" * 40)

    success = test_with_enhanced_data_manager()

    print("\n" + "=" * 40)
    print(f"Enhanced test: {'PASS' if success else 'FAIL'}")
