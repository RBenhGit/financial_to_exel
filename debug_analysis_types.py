"""
Debug analysis types in captured data
"""

import json
from watch_list_manager import WatchListManager


def debug_captured_data():
    """Debug what was actually captured"""
    print("Debugging captured analysis types...")

    watch_list_manager = WatchListManager()

    # Get the test portfolio data
    portfolio_data = watch_list_manager.get_watch_list("Corrected Test", latest_only=False)

    if portfolio_data and portfolio_data.get('stocks'):
        print(f"\nFound {len(portfolio_data['stocks'])} captured analyses:")
        print("=" * 60)

        for i, stock in enumerate(portfolio_data['stocks']):
            print(f"\nAnalysis #{i+1}:")
            print(f"  Ticker: {stock.get('ticker', 'N/A')}")
            print(f"  Company: {stock.get('company_name', 'N/A')}")
            print(f"  Analysis Type: {stock.get('analysis_type', 'NOT SET')}")
            print(f"  Fair Value: {stock.get('fair_value', 'N/A')}")
            print(f"  Current Price: {stock.get('current_price', 'N/A')}")

            # Check for type-specific fields
            if 'fcf_type' in stock:
                print(f"  FCF Type: {stock['fcf_type']} (DCF indicator)")
            if 'current_dividend' in stock:
                print(f"  Current Dividend: {stock['current_dividend']} (DDM indicator)")
            if 'pb_ratio' in stock:
                print(f"  P/B Ratio: {stock['pb_ratio']} (P/B indicator)")

            print("  " + "-" * 40)
    else:
        print("No data found in 'Corrected Test' watch list")


if __name__ == "__main__":
    debug_captured_data()
