"""
Test the market cap fix in P/B analysis
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_valuation import PBValuator
from financial_calculations import FinancialCalculator
from enhanced_data_manager import create_enhanced_data_manager


def test_pb_market_cap_fix():
    """Test that P/B analysis now shows correct market cap"""
    print("Testing P/B Analysis Market Cap Fix")
    print("=" * 50)

    # Create financial calculator with enhanced data manager
    temp_folder = "temp_AAPL"
    financial_calculator = FinancialCalculator(temp_folder)

    enhanced_data_manager = create_enhanced_data_manager()
    financial_calculator.enhanced_data_manager = enhanced_data_manager
    financial_calculator.ticker_symbol = "AAPL"

    # Create PB valuator and run analysis
    pb_valuator = PBValuator(financial_calculator)
    pb_analysis = pb_valuator.calculate_pb_analysis("AAPL")

    if 'error' in pb_analysis:
        print(f"Error: {pb_analysis.get('error_message')}")
        return False

    # Check the results
    current_data = pb_analysis.get('current_data', {})
    price = current_data.get('current_price', 0)
    shares = current_data.get('shares_outstanding', 0)
    market_cap = current_data.get('market_cap', 0)

    print(f"P/B Analysis Results:")
    print(f"  Current Price: ${price:,.2f}")
    print(f"  Shares Outstanding: {shares:,.0f}")
    print(f"  Market Cap: ${market_cap:,.0f}")

    # Verify market cap is calculated correctly
    if price and shares:
        expected_market_cap = price * shares
        print(f"  Expected Market Cap: ${expected_market_cap:,.0f}")

        # Check if they match (within rounding tolerance)
        difference = abs(market_cap - expected_market_cap)
        tolerance = expected_market_cap * 0.001  # 0.1% tolerance

        if difference <= tolerance:
            print("  [OK] Market cap is correctly calculated!")
            return True
        else:
            print(f"  [ERROR] Market cap mismatch! Difference: ${difference:,.0f}")
            return False
    else:
        print("  [ERROR] Missing price or shares data")
        return False


if __name__ == "__main__":
    success = test_pb_market_cap_fix()
    print(f"\nTest Result: {'PASS' if success else 'FAIL'}")
