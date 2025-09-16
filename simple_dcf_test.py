#!/usr/bin/env python3
"""
Simple DCF Shares Outstanding Test
================================

Quick test to verify DCF shares outstanding fix for Task #128
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)

# Import the necessary modules
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator


def test_dcf_shares_outstanding(ticker="MSFT"):
    """Test DCF shares outstanding retrieval"""
    print(f"Testing DCF shares outstanding for {ticker}")
    print("=" * 50)

    try:
        # Test with Excel data if available
        excel_path = Path(f"data/companies/{ticker}")
        if excel_path.exists():
            print(f"Testing with Excel data: {excel_path}")

            # Load financial calculator
            calc = FinancialCalculator(str(excel_path))
            calc.load_financial_data()

            print(f"Ticker: {calc.ticker_symbol}")

            # Test DCF
            dcf = DCFValuator(calc)

            # Test market data retrieval
            print("\nTesting market data retrieval...")
            market_data = dcf._get_market_data()

            shares = market_data.get('shares_outstanding', 0)
            price = market_data.get('current_price', 0)
            market_cap = market_data.get('market_cap', 0)

            print(f"Shares outstanding: {shares:,.0f}")
            print(f"Current price: ${price:.2f}")
            print(f"Market cap: ${market_cap:,.0f}")

            if shares > 0:
                print("SUCCESS: Shares outstanding retrieved successfully")

                # Test full DCF calculation
                print("\nTesting full DCF calculation...")
                dcf_result = dcf.calculate_dcf_projections()

                if 'error' in dcf_result:
                    print(f"DCF failed: {dcf_result.get('error_message', 'Unknown error')}")
                    return False
                else:
                    print(f"DCF SUCCESS: Value per share = ${dcf_result.get('value_per_share', 0):.2f}")
                    return True
            else:
                print("FAILED: Shares outstanding not available")
                return False
        else:
            print(f"Excel data not found at {excel_path}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    success = test_dcf_shares_outstanding(ticker)
    sys.exit(0 if success else 1)