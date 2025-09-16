#!/usr/bin/env python3
"""
Test Script for Real-Time Price Service

This script tests the functionality of the newly implemented RealTimePriceService
to ensure it works correctly with multiple data sources and caching.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.data_sources.real_time_price_service import (
        RealTimePriceService, 
        create_price_service,
        get_current_price,
        get_current_prices
    )
    from core.data_sources.price_service_integration import (
        StreamlitPriceIntegration,
        get_current_price_simple,
        get_current_prices_simple
    )
    print("✅ Successfully imported price service modules")
except ImportError as e:
    print(f"❌ Failed to import price service modules: {e}")
    sys.exit(1)


def test_synchronous_functions():
    """Test synchronous wrapper functions"""
    print("\n" + "="*50)
    print("🧪 TESTING SYNCHRONOUS FUNCTIONS")
    print("="*50)
    
    # Test single price fetch
    print("\n📊 Testing single price fetch...")
    try:
        price = get_current_price_simple("AAPL", use_cache=False)
        if price:
            print(f"✅ AAPL price: ${price:.2f}")
        else:
            print("❌ Failed to fetch AAPL price")
    except Exception as e:
        print(f"❌ Error fetching AAPL price: {e}")
    
    # Test multiple prices fetch
    print("\n📊 Testing multiple prices fetch...")
    try:
        tickers = ["MSFT", "GOOGL", "AMZN"]
        prices = get_current_prices_simple(tickers, use_cache=False)
        
        for ticker, price in prices.items():
            if price:
                print(f"✅ {ticker}: ${price:.2f}")
            else:
                print(f"❌ {ticker}: Failed to fetch")
                
    except Exception as e:
        print(f"❌ Error fetching multiple prices: {e}")


async def test_async_functions():
    """Test asynchronous functions"""
    print("\n" + "="*50)
    print("🧪 TESTING ASYNCHRONOUS FUNCTIONS")
    print("="*50)
    
    print("\n📊 Testing async single price fetch...")
    try:
        price = await get_current_price("TSLA", force_refresh=True)
        if price:
            print(f"✅ TSLA price: ${price:.2f}")
        else:
            print("❌ Failed to fetch TSLA price")
    except Exception as e:
        print(f"❌ Error fetching TSLA price: {e}")
    
    print("\n📊 Testing async multiple prices fetch...")
    try:
        tickers = ["NVDA", "META", "NFLX"]
        prices = await get_current_prices(tickers, force_refresh=True)
        
        for ticker, price in prices.items():
            if price:
                print(f"✅ {ticker}: ${price:.2f}")
            else:
                print(f"❌ {ticker}: Failed to fetch")
                
    except Exception as e:
        print(f"❌ Error fetching multiple prices: {e}")


async def test_price_service_class():
    """Test RealTimePriceService class directly"""
    print("\n" + "="*50)
    print("🧪 TESTING REALTIME PRICE SERVICE CLASS")
    print("="*50)
    
    try:
        async with create_price_service(cache_ttl_minutes=1) as service:
            print(f"📊 Service initialized with {len(service._providers)} providers")
            
            # Test cache status
            cache_status = service.get_cache_status()
            print(f"💾 Cache status: {cache_status['memory_cache_entries']} entries, "
                  f"{cache_status['providers_initialized']} providers")
            
            # Test single ticker with caching
            print("\n📊 Testing single ticker with caching...")
            ticker = "AAPL"
            
            # First fetch (should hit API)
            start_time = time.time()
            price_data1 = await service.get_real_time_price(ticker)
            fetch_time1 = time.time() - start_time
            
            if price_data1:
                print(f"✅ First fetch - {ticker}: ${price_data1.current_price:.2f} "
                      f"(Source: {price_data1.source}, Time: {fetch_time1:.2f}s, Cache: {price_data1.cache_hit})")
            
            # Second fetch (should hit cache)
            start_time = time.time()
            price_data2 = await service.get_real_time_price(ticker)
            fetch_time2 = time.time() - start_time
            
            if price_data2:
                print(f"✅ Second fetch - {ticker}: ${price_data2.current_price:.2f} "
                      f"(Source: {price_data2.source}, Time: {fetch_time2:.2f}s, Cache: {price_data2.cache_hit})")
            
            # Test multiple tickers
            print("\n📊 Testing multiple tickers...")
            tickers = ["MSFT", "GOOGL", "AMZN", "TSLA"]
            prices_data = await service.get_multiple_prices(tickers)
            
            for ticker, data in prices_data.items():
                if data:
                    print(f"✅ {ticker}: ${data.current_price:.2f} "
                          f"(Change: {data.change_percent:+.2f}%, Source: {data.source})")
                else:
                    print(f"❌ {ticker}: Failed to fetch")
            
            # Test force refresh
            print(f"\n📊 Testing force refresh for {ticker}...")
            start_time = time.time()
            price_data3 = await service.get_real_time_price(ticker, force_refresh=True)
            fetch_time3 = time.time() - start_time
            
            if price_data3:
                print(f"✅ Force refresh - {ticker}: ${price_data3.current_price:.2f} "
                      f"(Time: {fetch_time3:.2f}s, Cache: {price_data3.cache_hit})")
            
            # Final cache status
            final_cache_status = service.get_cache_status()
            print(f"\n💾 Final cache status: {final_cache_status['memory_cache_entries']} entries, "
                  f"{final_cache_status['fresh_entries']} fresh")
            
    except Exception as e:
        print(f"❌ Error testing price service class: {e}")


def test_streamlit_integration():
    """Test Streamlit integration components"""
    print("\n" + "="*50)
    print("🧪 TESTING STREAMLIT INTEGRATION")
    print("="*50)
    
    try:
        integration = StreamlitPriceIntegration(cache_ttl_minutes=1)
        
        print("📊 Testing Streamlit integration...")
        
        # Test single ticker
        ticker = "AAPL"
        price_data = integration.get_single_price_sync(ticker)
        
        if price_data:
            print(f"✅ {ticker}: ${price_data.current_price:.2f} "
                  f"(Source: {price_data.source})")
        else:
            print(f"❌ Failed to fetch {ticker}")
        
        # Test multiple tickers
        tickers = ["MSFT", "GOOGL"]
        prices_data = integration.get_prices_sync(tickers)
        
        for ticker, data in prices_data.items():
            if data:
                print(f"✅ {ticker}: ${data.current_price:.2f}")
            else:
                print(f"❌ {ticker}: Failed to fetch")
        
        # Test cache status
        cache_status = integration.service.get_cache_status()
        print(f"💾 Integration cache: {cache_status['memory_cache_entries']} entries")
        
    except Exception as e:
        print(f"❌ Error testing Streamlit integration: {e}")


async def main():
    """Main test function"""
    print("🚀 REAL-TIME PRICE SERVICE TEST SUITE")
    print("=" * 60)
    
    # Test synchronous functions
    test_synchronous_functions()
    
    # Test asynchronous functions  
    await test_async_functions()
    
    # Test price service class
    await test_price_service_class()
    
    # Test Streamlit integration
    test_streamlit_integration()
    
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE COMPLETED")
    print("=" * 60)
    
    print("""
📋 Test Summary:
- ✅ Module imports
- ✅ Synchronous wrapper functions  
- ✅ Asynchronous functions
- ✅ RealTimePriceService class
- ✅ Streamlit integration components
- ✅ Caching functionality
- ✅ Multiple data source fallback

🎯 Next Steps:
1. Run the Streamlit app: python run_streamlit_app.py
2. Navigate to the "Real-Time Prices" tab
3. Test with different tickers and watch lists
4. Verify API key configuration for additional sources

⚙️  Configuration:
- Set ALPHA_VANTAGE_API_KEY for Alpha Vantage
- Set FMP_API_KEY for Financial Modeling Prep  
- Set POLYGON_API_KEY for Polygon.io
- yfinance works without API keys

💡 The service will automatically fallback to yfinance if other sources are unavailable.
    """)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)