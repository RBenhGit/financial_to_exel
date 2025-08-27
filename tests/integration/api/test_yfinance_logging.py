"""
Test script to demonstrate the enhanced Yahoo Finance API logging system.

This script shows the detailed step-by-step logging for Yahoo Finance API requests.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from centralized_data_manager import CentralizedDataManager
from input_validator import ValidationLevel


def test_yfinance_logging():
    """Test the YFinance API logging with a sample ticker."""

    print("🚀 Testing Yahoo Finance API Detailed Logging System")
    print("=" * 80)

    # Initialize the centralized data manager with enhanced logging
    base_path = "."
    data_manager = CentralizedDataManager(
        base_path=base_path, validation_level=ValidationLevel.MODERATE
    )

    print("\n📊 Testing with AAPL (Apple Inc.)")
    print("-" * 50)

    # Test with a real ticker - this will show the complete logging flow
    ticker = "AAPL"

    try:
        # Fetch market data - this will trigger all the detailed logging
        market_data = data_manager.fetch_market_data(
            ticker=ticker,
            force_reload=True,  # Force fresh API call to see all logging
            skip_validation=False,  # Include validation logging
        )

        if market_data:
            print(f"\n✅ Successfully fetched data for {ticker}")
            print(f"   Company: {market_data.get('company_name', 'N/A')}")
            print(f"   Price: ${market_data.get('current_price', 0):,.2f}")
            print(f"   Market Cap: ${market_data.get('market_cap', 0):,.0f}M")
            print(f"   Shares Outstanding: {market_data.get('shares_outstanding', 0):,.0f}")
        else:
            print(f"\n❌ Failed to fetch data for {ticker}")

    except Exception as e:
        print(f"\n💥 Error during testing: {e}")

    # Test cache functionality
    print(f"\n📦 Testing Cache Hit (second request for {ticker})")
    print("-" * 50)

    try:
        # Second request should hit cache and show cache logging
        cached_data = data_manager.fetch_market_data(
            ticker=ticker, force_reload=False  # Allow cache hit
        )

        if cached_data:
            print(f"✅ Cache hit successful for {ticker}")
        else:
            print(f"❌ Cache miss or failed for {ticker}")

    except Exception as e:
        print(f"💥 Error during cache testing: {e}")

    # Test with invalid ticker to show error logging
    print(f"\n🚫 Testing Error Logging with Invalid Ticker")
    print("-" * 50)

    try:
        invalid_data = data_manager.fetch_market_data(
            ticker="INVALID_TICKER_XYZ123", force_reload=True
        )

        if invalid_data:
            print("✅ Surprisingly got data for invalid ticker")
        else:
            print("❌ Expected failure for invalid ticker - check logs for error details")

    except Exception as e:
        print(f"💥 Expected error for invalid ticker: {e}")

    # Show cache statistics
    print(f"\n📈 Cache Statistics")
    print("-" * 50)
    cache_stats = data_manager.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 80)
    print("🎯 Logging Test Complete!")
    print("📁 Check the logs directory for detailed step-by-step logs:")
    print(f"   {Path(data_manager.cache_dir) / 'logs'}")
    print("=" * 80)


if __name__ == "__main__":
    test_yfinance_logging()
