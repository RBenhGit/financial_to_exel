"""
Debug Market Cap calculation in P/B analysis
Check what market data is being provided and verify calculations
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


def debug_market_cap_calculation():
    """Debug market cap data flow in P/B analysis"""
    print("Debugging Market Cap Calculation in P/B Analysis")
    print("=" * 60)

    try:
        # Create financial calculator with enhanced data manager
        temp_folder = "temp_AAPL"
        financial_calculator = FinancialCalculator(temp_folder)

        # Attach enhanced data manager
        enhanced_data_manager = create_enhanced_data_manager()
        financial_calculator.enhanced_data_manager = enhanced_data_manager

        # Set ticker
        ticker_symbol = "AAPL"
        financial_calculator.ticker_symbol = ticker_symbol

        # Create PB valuator
        pb_valuator = PBValuator(financial_calculator)

        print(f"1. Debugging market data for {ticker_symbol}...")

        # Get market data directly to see what we're working with
        market_data = pb_valuator._get_market_data(ticker_symbol)

        print("2. Raw market data:")
        for key, value in market_data.items():
            print(f"   {key}: {value}")

        # Calculate what market cap should be
        current_price = market_data.get('current_price', 0)
        shares_outstanding = market_data.get('shares_outstanding', 0)
        provided_market_cap = market_data.get('market_cap', 0)

        if current_price and shares_outstanding:
            calculated_market_cap = current_price * shares_outstanding
            print(f"\n3. Market Cap Analysis:")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Shares Outstanding: {shares_outstanding:,.0f}")
            print(f"   Provided Market Cap: ${provided_market_cap:,.0f}")
            print(f"   Calculated Market Cap: ${calculated_market_cap:,.0f}")

            # Check if there's a discrepancy
            if abs(provided_market_cap - calculated_market_cap) > (
                calculated_market_cap * 0.01
            ):  # 1% tolerance
                discrepancy_percent = (
                    abs(provided_market_cap - calculated_market_cap) / calculated_market_cap * 100
                )
                print(f"   ⚠️  DISCREPANCY: {discrepancy_percent:.1f}% difference!")
                print(f"   Recommendation: Use calculated market cap")
            else:
                print(f"   ✅ Market caps match (within 1% tolerance)")
        else:
            print(f"\n3. ❌ Cannot calculate market cap - missing price or shares data")

        # Run full P/B analysis to see the result
        print(f"\n4. Running full P/B analysis...")
        pb_analysis = pb_valuator.calculate_pb_analysis(ticker_symbol)

        if 'error' not in pb_analysis:
            current_data = pb_analysis.get('current_data', {})
            pb_price = current_data.get('current_price', 0)
            pb_shares = current_data.get('shares_outstanding', 0)
            pb_market_cap = current_data.get('market_cap', 0)

            print(f"5. P/B Analysis Results:")
            print(f"   Price in P/B: ${pb_price:.2f}")
            print(f"   Shares in P/B: {pb_shares:,.0f}")
            print(f"   Market Cap in P/B: ${pb_market_cap:,.0f}")

            # Check if P/B uses correct market cap
            if pb_price and pb_shares:
                pb_calculated_market_cap = pb_price * pb_shares
                print(f"   P/B Calculated Market Cap: ${pb_calculated_market_cap:,.0f}")

                if abs(pb_market_cap - pb_calculated_market_cap) > (
                    pb_calculated_market_cap * 0.01
                ):
                    print(f"   ⚠️  P/B MARKET CAP ISSUE: Using provided instead of calculated!")
                else:
                    print(f"   ✅ P/B market cap is consistent")

        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        logger.exception("Debug exception")
        return False


def test_market_cap_from_different_sources():
    """Test market cap data from different sources"""
    print("\nTesting Market Cap from Different Data Sources")
    print("=" * 60)

    try:
        # Test yfinance directly
        import yfinance as yf

        ticker_symbol = "AAPL"
        print(f"1. Testing yfinance data for {ticker_symbol}:")

        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        yf_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        yf_shares = info.get('sharesOutstanding', info.get('impliedSharesOutstanding', 0))
        yf_market_cap = info.get('marketCap', 0)

        print(f"   YFinance Price: ${yf_price:.2f}")
        print(f"   YFinance Shares: {yf_shares:,.0f}")
        print(f"   YFinance Market Cap: ${yf_market_cap:,.0f}")

        if yf_price and yf_shares:
            yf_calculated = yf_price * yf_shares
            print(f"   YFinance Calculated: ${yf_calculated:,.0f}")

            if abs(yf_market_cap - yf_calculated) > (yf_calculated * 0.01):
                print(f"   ⚠️  YFinance has market cap discrepancy!")
            else:
                print(f"   ✅ YFinance market cap is consistent")

        # Test enhanced data manager
        print(f"\n2. Testing enhanced data manager for {ticker_symbol}:")

        enhanced_data_manager = create_enhanced_data_manager()
        edm_data = enhanced_data_manager.fetch_market_data(ticker_symbol)

        if edm_data:
            edm_price = edm_data.get('current_price', 0)
            edm_shares = edm_data.get('shares_outstanding', 0)
            edm_market_cap = edm_data.get('market_cap', 0)

            print(f"   Enhanced Manager Price: ${edm_price:.2f}")
            print(f"   Enhanced Manager Shares: {edm_shares:,.0f}")
            print(f"   Enhanced Manager Market Cap: ${edm_market_cap:,.0f}")

            if edm_price and edm_shares:
                edm_calculated = edm_price * edm_shares
                print(f"   Enhanced Manager Calculated: ${edm_calculated:,.0f}")

                if abs(edm_market_cap - edm_calculated) > (edm_calculated * 0.01):
                    print(f"   ⚠️  Enhanced Manager has market cap discrepancy!")
                else:
                    print(f"   ✅ Enhanced Manager market cap is consistent")
        else:
            print(f"   ❌ Enhanced Manager returned no data")

        return True

    except Exception as e:
        print(f"❌ Source comparison failed: {e}")
        logger.exception("Source comparison exception")
        return False


if __name__ == "__main__":
    print("Market Cap Debug Analysis")
    print("=" * 70)

    # Test 1: Debug P/B market cap calculation
    success1 = debug_market_cap_calculation()

    # Test 2: Compare different data sources
    success2 = test_market_cap_from_different_sources()

    print("\n" + "=" * 70)
    print("Debug Results:")
    print(f"P/B Market Cap Debug: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Data Source Comparison: {'✅ PASS' if success2 else '❌ FAIL'}")

    if success1 and success2:
        print("\n🔍 Analysis complete. Check output above for market cap issues.")
    else:
        print("\n⚠️ Some debug tests failed.")
