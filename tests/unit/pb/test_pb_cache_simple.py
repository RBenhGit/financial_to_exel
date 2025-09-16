"""
Simple P/B Historical Data Caching Test
=======================================

Test the P/B historical data caching functionality without Unicode characters.
"""

import logging
import time
from datetime import datetime, timedelta

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pb_cache_basic():
    """Basic test of P/B caching functionality"""
    print("=" * 60)
    print("Testing P/B Historical Data Caching Implementation")
    print("=" * 60)
    
    try:
        from unified_data_adapter import UnifiedDataAdapter, PBHistoricalCacheEntry
        from data_sources import DataSourceType
        
        # Initialize the adapter
        adapter = UnifiedDataAdapter()
        print("SUCCESS: UnifiedDataAdapter initialized")
        
        # Test 1: Cache key generation
        print("\n1. Testing cache key generation...")
        cache_key_1 = adapter._generate_pb_cache_key("AAPL", 5)
        cache_key_2 = adapter._generate_pb_cache_key("AAPL", 5)
        cache_key_3 = adapter._generate_pb_cache_key("MSFT", 5)
        
        assert cache_key_1 == cache_key_2, "Same parameters should generate same key"
        assert cache_key_1 != cache_key_3, "Different tickers should generate different keys"
        print("SUCCESS: Cache key generation working correctly")
        print(f"  AAPL 5Y key: {cache_key_1[:12]}...")
        print(f"  MSFT 5Y key: {cache_key_3[:12]}...")
        
        # Test 2: Create sample historical data
        print("\n2. Creating sample P/B historical data...")
        sample_data = []
        base_date = datetime.now() - timedelta(days=365*5)  # 5 years ago
        
        for i in range(20):  # 20 quarters
            quarter_date = base_date + timedelta(days=90*i)
            sample_data.append({
                'date': quarter_date.strftime('%Y-%m-%d'),
                'price': 150.0 + (i * 2.5),
                'book_value_per_share': 25.0 + (i * 0.8),
                'pb_ratio': (150.0 + (i * 2.5)) / (25.0 + (i * 0.8)),
                'shares_outstanding': 16_000_000_000
            })
        
        print(f"SUCCESS: Created {len(sample_data)} sample data points")
        print(f"  Date range: {sample_data[0]['date']} to {sample_data[-1]['date']}")
        print(f"  P/B range: {sample_data[0]['pb_ratio']:.2f} to {sample_data[-1]['pb_ratio']:.2f}")
        
        # Test 3: Cache the data
        print("\n3. Testing data caching...")
        test_ticker = "AAPL"
        test_years = 5
        
        adapter.cache_pb_historical_data(
            ticker=test_ticker,
            historical_data=sample_data,
            years=test_years,
            source_type=DataSourceType.YFINANCE,
            quality_score=0.9
        )
        print(f"SUCCESS: Data cached for {test_ticker}")
        
        # Test 4: Retrieve cached data
        print("\n4. Testing cache retrieval...")
        retrieved_data = adapter.get_cached_pb_historical_data(test_ticker, test_years)
        
        assert retrieved_data is not None, "Should retrieve cached data"
        assert len(retrieved_data) == len(sample_data), "Should retrieve all data points"
        
        print(f"SUCCESS: Retrieved {len(retrieved_data)} data points from cache")
        
        # Test 5: Cache statistics
        print("\n5. Testing cache statistics...")
        cache_stats = adapter.get_pb_cache_stats()
        
        assert cache_stats['total_pb_entries'] > 0, "Should have P/B entries"
        assert test_ticker in cache_stats['ticker_details'], "Should have ticker details"
        
        print("SUCCESS: Cache statistics retrieved")
        print(f"  Total P/B entries: {cache_stats['total_pb_entries']}")
        
        # Test 6: Cache invalidation
        print("\n6. Testing cache invalidation...")
        adapter.invalidate_pb_cache(test_ticker)
        
        retrieved_after = adapter.get_cached_pb_historical_data(test_ticker, test_years)
        assert retrieved_after is None, "Should return None after invalidation"
        
        print("SUCCESS: Cache invalidation working")
        
        print("\n" + "=" * 60)
        print("ALL P/B CACHE TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Test failed with: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_entry_properties():
    """Test the PBHistoricalCacheEntry properties"""
    print("\n" + "=" * 40)
    print("TESTING CACHE ENTRY PROPERTIES")
    print("=" * 40)
    
    try:
        from core.data_sources.unified_data_adapter import PBHistoricalCacheEntry
        from data_sources import DataSourceType
        
        # Create sample data
        sample_data = [
            {'date': '2023-01-01', 'pb_ratio': 5.2, 'price': 150.0},
            {'date': '2023-04-01', 'pb_ratio': 5.5, 'price': 155.0},
            {'date': '2023-07-01', 'pb_ratio': None, 'price': 160.0},  # Missing P/B
            {'date': '2023-10-01', 'pb_ratio': 5.8, 'price': 165.0}
        ]
        
        # Create cache entry
        cache_entry = PBHistoricalCacheEntry(
            data=sample_data,
            timestamp=datetime.now(),
            source_type=DataSourceType.YFINANCE,
            quality_score=0.8,
            ticker_symbol="TEST",
            years_covered=1,
            quarterly_periods=4,
            last_quarter_date='2023-10-01',
            data_completeness=0.75  # 3 out of 4 valid P/B ratios
        )
        
        print(f"Cache entry created:")
        print(f"  Ticker: {cache_entry.ticker_symbol}")
        print(f"  TTL hours: {cache_entry.ttl_hours}")
        print(f"  Data completeness: {cache_entry.data_completeness:.1%}")
        print(f"  Is expired: {cache_entry.is_expired()}")
        print(f"  Needs refresh: {cache_entry.needs_data_quality_refresh()}")
        
        # Test cache key suffix
        key_suffix = cache_entry.get_cache_key_suffix()
        print(f"  Cache key suffix: {key_suffix}")
        
        assert cache_entry.data_type == "pb_historical", "Should be P/B historical type"
        assert not cache_entry.is_expired(), "Should not be expired immediately"
        
        print("SUCCESS: Cache entry properties working correctly")
        return True
        
    except Exception as e:
        print(f"ERROR: Cache entry test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting P/B Cache Implementation Tests...")
    
    # Run basic functionality tests
    basic_success = test_pb_cache_basic()
    
    # Run cache entry tests
    if basic_success:
        entry_success = test_cache_entry_properties()
    else:
        entry_success = False
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Basic Tests: {'PASSED' if basic_success else 'FAILED'}")
    print(f"Entry Tests: {'PASSED' if entry_success else 'FAILED'}")
    
    if basic_success and entry_success:
        print("\nSUCCESS: P/B CACHE IMPLEMENTATION WORKING!")
        print("\nTask #31 Implementation Summary:")
        print("- Extended CacheEntry structure for P/B historical datasets")
        print("- Set appropriate TTL (24-48 hours) based on data quality") 
        print("- Implemented P/B-specific cache keys and validation logic")
        print("- Integrated with existing cache cleanup and management")
        print("- Added cache invalidation for data quality changes")
        print("- Created efficient cache lookup for quarterly data")
    else:
        print("\nERROR: Some tests failed - review implementation")
    
    print("=" * 60)