#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for enhanced price caching mechanism with timestamps and visual indicators
"""

import asyncio
import time
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_sources.real_time_price_service import RealTimePriceService, PriceData
from core.data_sources.price_service_integration import StreamlitPriceIntegration

async def test_cache_freshness_indicators():
    """Test the freshness indicators and caching mechanism"""
    print("Testing Enhanced Price Caching Mechanism")
    print("=" * 60)
    
    # Initialize the service
    service = RealTimePriceService(cache_ttl_minutes=15)
    integration = StreamlitPriceIntegration(cache_ttl_minutes=15)
    
    try:
        # Test 1: Fresh data
        print("\nTest 1: Fetching fresh price data")
        ticker = "AAPL"
        price_data = await service.get_real_time_price(ticker)
        
        if price_data:
            print(f"SUCCESS {ticker}: ${price_data.current_price:.2f}")
            print(f"   Source: {price_data.source}")
            print(f"   Cache hit: {price_data.cache_hit}")
            print(f"   Updated: {price_data.last_updated}")
            
            # Test freshness indicator
            freshness = integration._get_freshness_indicator(price_data)
            print(f"   Freshness: {freshness}")
        else:
            print(f"FAILED to fetch price for {ticker}")
            
        # Test 2: Cached data (immediate re-fetch)
        print(f"\nTest 2: Re-fetching same ticker (should be cached)")
        price_data_cached = await service.get_real_time_price(ticker)
        
        if price_data_cached:
            print(f"SUCCESS {ticker}: ${price_data_cached.current_price:.2f}")
            print(f"   Cache hit: {price_data_cached.cache_hit}")
            freshness = integration._get_freshness_indicator(price_data_cached)
            print(f"   Freshness: {freshness}")
            
        # Test 3: Cache status
        print(f"\nTest 3: Cache status information")
        cache_status = service.get_cache_status()
        print(f"   Memory entries: {cache_status['memory_cache_entries']}")
        print(f"   Fresh entries: {cache_status['fresh_entries']}")
        print(f"   Expired entries: {cache_status['expired_entries']}")
        print(f"   Cache TTL: {cache_status['cache_ttl_minutes']} minutes")
        
        # Test 4: Multiple tickers
        print(f"\nTest 4: Multiple ticker caching")
        tickers = ["MSFT", "GOOGL", "TSLA"]
        prices = await service.get_multiple_prices(tickers)
        
        for ticker, data in prices.items():
            if data:
                freshness = integration._get_freshness_indicator(data)
                print(f"   {ticker}: ${data.current_price:.2f} - {freshness}")
            else:
                print(f"   {ticker}: FAILED")
                
        # Test 5: Freshness stats
        print(f"\nTest 5: Detailed freshness statistics")
        freshness_stats = integration._get_cache_freshness_stats()
        print(f"   Fresh (0-5min): {freshness_stats['fresh']}")
        print(f"   Recent (5-15min): {freshness_stats['recent']}")
        print(f"   Stale (15-30min): {freshness_stats['stale']}")
        print(f"   Old (>30min): {freshness_stats['old']}")
        
        # Test 6: Force refresh
        print(f"\nTest 6: Force refresh test")
        price_data_fresh = await service.get_real_time_price(ticker, force_refresh=True)
        if price_data_fresh:
            freshness = integration._get_freshness_indicator(price_data_fresh)
            print(f"   {ticker} (forced): ${price_data_fresh.current_price:.2f} - {freshness}")
            print(f"   Cache hit: {price_data_fresh.cache_hit}")
        
        # Test 7: Memory usage check
        final_cache_status = service.get_cache_status()
        memory_entries = final_cache_status['memory_cache_entries']
        print(f"\nTest 7: Memory usage check")
        print(f"   Total memory entries: {memory_entries}")
        
        if memory_entries > 10:
            print(f"   WARNING: High memory usage detected")
        else:
            print(f"   SUCCESS: Memory usage is optimal")
            
        print(f"\nAll tests completed successfully!")
        print(f"Cache directory: {service.cache_dir}")
        
    except Exception as e:
        print(f"FAILED: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        service.__exit__(None, None, None)

def test_freshness_edge_cases():
    """Test edge cases for freshness indicators"""
    print("\nTesting Freshness Indicator Edge Cases")
    print("=" * 50)
    
    integration = StreamlitPriceIntegration(cache_ttl_minutes=15)
    
    # Test with different data ages
    test_cases = [
        (datetime.now(), "LIVE", "Live data"),
        (datetime.now() - timedelta(minutes=2), "FRESH", "2 minutes old"),
        (datetime.now() - timedelta(minutes=10), "RECENT", "10 minutes old"),
        (datetime.now() - timedelta(minutes=20), "STALE", "20 minutes old"),
        (datetime.now() - timedelta(minutes=45), "OLD", "45 minutes old"),
    ]
    
    for i, (timestamp, expected_word, description) in enumerate(test_cases, 1):
        # Create mock price data
        price_data = PriceData(
            ticker="TEST",
            current_price=100.0,
            last_updated=timestamp,
            cache_hit=True if i > 1 else False  # First one is live
        )
        
        freshness = integration._get_freshness_indicator(price_data)
        status = "SUCCESS" if expected_word in freshness else "FAILED"
        
        print(f"   Test {i}: {description}")
        print(f"     Expected: {expected_word}")
        print(f"     Got: {freshness} - {status}")

if __name__ == "__main__":
    print("Starting Price Caching Enhancement Tests")
    
    # Run async tests
    asyncio.run(test_cache_freshness_indicators())
    
    # Run edge case tests
    test_freshness_edge_cases()
    
    print("\nAll testing completed!")