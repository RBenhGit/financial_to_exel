"""
Simple check for market cap issue
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_valuation import PBValuator
from financial_calculations import FinancialCalculator
from enhanced_data_manager import create_enhanced_data_manager


def check_market_cap():
    """Check market cap calculation issue"""
    # Create financial calculator with enhanced data manager
    temp_folder = "temp_AAPL"
    financial_calculator = FinancialCalculator(temp_folder)

    enhanced_data_manager = create_enhanced_data_manager()
    financial_calculator.enhanced_data_manager = enhanced_data_manager
    financial_calculator.ticker_symbol = "AAPL"

    # Create PB valuator
    pb_valuator = PBValuator(financial_calculator)

    # Get market data
    market_data = pb_valuator._get_market_data("AAPL")

    print("Market Data from API:")
    print(f"  Current Price: ${market_data.get('current_price', 0):,.2f}")
    print(f"  Shares Outstanding: {market_data.get('shares_outstanding', 0):,.0f}")
    print(f"  Provided Market Cap: ${market_data.get('market_cap', 0):,.0f}")

    # Calculate correct market cap
    price = market_data.get('current_price', 0)
    shares = market_data.get('shares_outstanding', 0)
    provided_cap = market_data.get('market_cap', 0)

    if price and shares:
        calculated_cap = price * shares
        print(f"  Calculated Market Cap: ${calculated_cap:,.0f}")

        # Check if provided cap might be in thousands
        if abs(provided_cap * 1000 - calculated_cap) < abs(provided_cap - calculated_cap):
            print("  ISSUE: Provided market cap appears to be in thousands!")
            print(f"  Corrected Market Cap: ${provided_cap * 1000:,.0f}")
            return provided_cap * 1000
        else:
            print("  Market cap appears correct")
            return provided_cap

    return None


if __name__ == "__main__":
    correct_market_cap = check_market_cap()
    if correct_market_cap:
        print(f"\nCorrect market cap should be: ${correct_market_cap:,.0f}")
