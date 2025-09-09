"""
Test Suite for Large Watch List Performance Optimizations

This test suite validates the performance optimizations implemented for Task #86,
specifically testing concurrent API calls, lazy loading, memory optimization,
and overall performance with 50+ stocks.

Tests:
- Concurrent vs sequential loading performance comparison
- Memory usage and leak detection
- Lazy loading functionality
- Performance under load (50+ stocks)
- Error handling and resilience
- Cache effectiveness
"""

import pytest
import time
import gc
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Any
import tempfile
import shutil
from pathlib import Path

# Import components to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from performance.concurrent_watch_list_optimizer import (
    ConcurrentWatchListOptimizer, 
    ConcurrencyConfig,
    LazyLoadingConfig,
    create_optimized_watch_list_manager
)
from performance.performance_benchmark import PerformanceBenchmark, run_performance_benchmark
from core.data_processing.managers.watch_list_manager import WatchListManager
from core.data_sources.real_time_price_service import PriceData


class TestLargeWatchListPerformance:
    """Test suite for large watch list performance optimizations"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_watch_list_manager(self, temp_dir):
        """Create mock watch list manager with test data"""
        manager = WatchListManager(temp_dir)
        
        # Create test watch lists of different sizes
        test_lists = {
            "small_list": 10,
            "medium_list": 25,
            "large_list": 50,
            "xlarge_list": 100
        }
        
        for list_name, size in test_lists.items():
            manager.create_watch_list(list_name, f"Test list with {size} stocks")
            
            # Add test stocks
            for i in range(size):
                analysis_data = {
                    'ticker': f'STOCK{i:03d}',
                    'company_name': f'Test Company {i}',
                    'current_price': 100.0 + i,
                    'fair_value': 120.0 + i,
                    'discount_rate': 0.1,
                    'terminal_growth_rate': 0.03,
                    'fcf_type': 'FCFE',
                    'analysis_type': 'DCF'
                }
                manager.add_analysis_to_watch_list(list_name, analysis_data)
        
        return manager
    
    @pytest.fixture
    def mock_price_service(self):
        """Create mock price service for controlled testing"""
        with patch('performance.concurrent_watch_list_optimizer.RealTimePriceService') as mock_service:
            # Configure mock to return test price data
            def mock_get_detailed_price_data(ticker, force_refresh=False):
                # Simulate API delay
                time.sleep(0.1)  # 100ms delay per request
                
                return PriceData(
                    ticker=ticker,
                    current_price=100.0 + hash(ticker) % 50,
                    change_percent=1.5,
                    volume=1000000,
                    market_cap=5000000000,
                    source='mock_api',
                    cache_hit=not force_refresh
                )
            
            mock_service.return_value.get_detailed_price_data.side_effect = mock_get_detailed_price_data
            yield mock_service
    
    def test_concurrent_vs_sequential_performance(self, mock_watch_list_manager, mock_price_service):
        """Test that concurrent loading is significantly faster than sequential"""
        
        # Test with large list (50 stocks)
        list_name = "large_list"
        
        # Create optimizer
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            # Test concurrent loading
            start_time = time.time()
            concurrent_result = optimizer.get_watch_list_with_concurrent_prices(
                list_name, force_refresh=True
            )
            concurrent_time = time.time() - start_time
            
            # Test sequential loading (simulate by reducing thread pool to 1)
            optimizer.executor = ThreadPoolExecutor(max_workers=1)
            start_time = time.time()
            sequential_result = optimizer.get_watch_list_with_concurrent_prices(
                list_name, force_refresh=True
            )
            sequential_time = time.time() - start_time
            
            # Assertions
            assert concurrent_result is not None, "Concurrent loading should succeed"
            assert sequential_result is not None, "Sequential loading should succeed"
            
            # Concurrent should be significantly faster (at least 2x speedup expected)
            speedup = sequential_time / max(concurrent_time, 0.001)
            assert speedup > 2.0, f"Expected speedup >2x, got {speedup:.2f}x"
            
            # Both should return same number of stocks
            assert len(concurrent_result['stocks']) == len(sequential_result['stocks'])
            
            # Performance metadata should be present
            assert 'performance_metadata' in concurrent_result
            perf_meta = concurrent_result['performance_metadata']
            assert perf_meta['concurrent_processing'] is True
            assert perf_meta['processing_time_seconds'] < sequential_time
            
        finally:
            optimizer.shutdown()
    
    def test_loading_time_requirement_50_stocks(self, mock_watch_list_manager, mock_price_service):
        """Test that loading 50 stocks meets the <3 seconds requirement"""
        
        list_name = "large_list"  # 50 stocks
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            start_time = time.time()
            result = optimizer.get_watch_list_with_concurrent_prices(
                list_name, force_refresh=True
            )
            loading_time = time.time() - start_time
            
            # Assertions
            assert result is not None, "Loading should succeed"
            assert len(result['stocks']) == 50, "Should load all 50 stocks"
            assert loading_time < 3.0, f"Loading time {loading_time:.2f}s should be < 3 seconds"
            
            # Verify performance metadata
            perf_meta = result['performance_metadata']
            assert perf_meta['total_tickers_processed'] == 50
            assert perf_meta['requests_per_second'] > 15  # Should process >15 requests/sec
            
        finally:
            optimizer.shutdown()
    
    def test_memory_usage_optimization(self, mock_watch_list_manager, mock_price_service):
        """Test memory usage remains reasonable and no leaks occur"""
        
        import psutil
        import gc
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            # Load multiple large watch lists
            for list_name in ["large_list", "xlarge_list", "medium_list"]:
                result = optimizer.get_watch_list_with_concurrent_prices(
                    list_name, force_refresh=True
                )
                assert result is not None
                
                # Force memory optimization
                optimizer.optimize_memory()
                gc.collect()
            
            # Check final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (<100MB for our test data)
            assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB is too high"
            
            # Check metrics
            metrics = optimizer.get_performance_metrics()
            assert metrics.peak_memory_mb > 0, "Should track peak memory usage"
            
        finally:
            optimizer.shutdown()
    
    def test_lazy_loading_pagination(self, mock_watch_list_manager, mock_price_service):
        """Test lazy loading with pagination functionality"""
        
        list_name = "xlarge_list"  # 100 stocks
        page_size = 25
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            # Test first page
            page1 = optimizer.get_paginated_watch_list(list_name, page=1, page_size=page_size)
            
            assert page1 is not None, "Page 1 should load successfully"
            assert len(page1['stocks']) == page_size, f"Page 1 should have {page_size} stocks"
            assert page1['page'] == 1
            assert page1['total_pages'] == 4  # 100 stocks / 25 per page
            assert page1['has_next'] is True
            assert page1['has_previous'] is False
            
            # Test middle page
            page2 = optimizer.get_paginated_watch_list(list_name, page=2, page_size=page_size)
            
            assert page2 is not None, "Page 2 should load successfully" 
            assert len(page2['stocks']) == page_size, f"Page 2 should have {page_size} stocks"
            assert page2['page'] == 2
            assert page2['has_next'] is True
            assert page2['has_previous'] is True
            
            # Test last page
            page4 = optimizer.get_paginated_watch_list(list_name, page=4, page_size=page_size)
            
            assert page4 is not None, "Page 4 should load successfully"
            assert len(page4['stocks']) == page_size, f"Page 4 should have {page_size} stocks"
            assert page4['has_next'] is False
            assert page4['has_previous'] is True
            
            # Test different page sizes
            large_page = optimizer.get_paginated_watch_list(list_name, page=1, page_size=50)
            assert len(large_page['stocks']) == 50
            assert large_page['total_pages'] == 2
            
        finally:
            optimizer.shutdown()
    
    def test_concurrent_error_handling(self, mock_watch_list_manager):
        """Test error handling and resilience in concurrent processing"""
        
        # Mock price service that fails for some tickers
        with patch('performance.concurrent_watch_list_optimizer.RealTimePriceService') as mock_service:
            def mock_get_detailed_price_data(ticker, force_refresh=False):
                if 'STOCK020' in ticker or 'STOCK040' in ticker:
                    raise Exception(f"API error for {ticker}")
                
                time.sleep(0.05)  # Small delay
                return PriceData(
                    ticker=ticker,
                    current_price=100.0,
                    source='mock_api'
                )
            
            mock_service.return_value.get_detailed_price_data.side_effect = mock_get_detailed_price_data
            
            optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
            
            try:
                result = optimizer.get_watch_list_with_concurrent_prices(
                    "large_list", force_refresh=True
                )
                
                assert result is not None, "Should handle errors gracefully"
                assert len(result['stocks']) == 50, "Should still return all stocks"
                
                # Some stocks should have price data, some should not
                stocks_with_prices = [s for s in result['stocks'] if s.get('current_market_price')]
                stocks_without_prices = [s for s in result['stocks'] if not s.get('current_market_price')]
                
                assert len(stocks_with_prices) > 40, "Most stocks should have prices"
                assert len(stocks_without_prices) > 0, "Some stocks should fail (as expected)"
                
                # Performance metadata should reflect partial success
                perf_meta = result['performance_metadata']
                assert perf_meta['failed_price_fetches'] > 0
                assert perf_meta['successful_price_fetches'] > perf_meta['failed_price_fetches']
                
            finally:
                optimizer.shutdown()
    
    def test_circuit_breaker_functionality(self, mock_watch_list_manager):
        """Test circuit breaker pattern for API failures"""
        
        # Mock price service that always fails
        with patch('performance.concurrent_watch_list_optimizer.RealTimePriceService') as mock_service:
            mock_service.return_value.get_detailed_price_data.side_effect = Exception("API unavailable")
            
            config = ConcurrencyConfig(
                circuit_breaker_threshold=3,  # Low threshold for testing
                max_workers=2
            )
            
            optimizer = ConcurrentWatchListOptimizer(
                mock_watch_list_manager,
                concurrency_config=config
            )
            
            try:
                # This should trigger circuit breaker after a few failures
                result = optimizer.get_watch_list_with_concurrent_prices(
                    "medium_list", force_refresh=True
                )
                
                assert result is not None, "Should return data even with circuit breaker open"
                
                # Check that circuit breaker opened
                assert optimizer._circuit_breaker_open is True, "Circuit breaker should be open"
                
            finally:
                optimizer.shutdown()
    
    def test_performance_metrics_tracking(self, mock_watch_list_manager, mock_price_service):
        """Test that performance metrics are properly tracked"""
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            # Load some data
            result = optimizer.get_watch_list_with_concurrent_prices(
                "medium_list", force_refresh=True
            )
            
            assert result is not None
            
            # Get metrics
            metrics = optimizer.get_performance_metrics()
            
            # Verify metrics are populated
            assert metrics.total_requests > 0, "Should track total requests"
            assert metrics.successful_requests > 0, "Should track successful requests"
            assert metrics.average_response_time > 0, "Should track response times"
            assert metrics.peak_memory_mb > 0, "Should track memory usage"
            assert metrics.operations_per_second > 0, "Should calculate ops/sec"
            assert 0 <= metrics.cache_hit_ratio <= 1, "Cache hit ratio should be valid percentage"
            
        finally:
            optimizer.shutdown()
    
    @pytest.mark.slow
    def test_comprehensive_benchmark(self, mock_watch_list_manager, mock_price_service):
        """Run comprehensive performance benchmark (marked as slow test)"""
        
        benchmark = PerformanceBenchmark(output_dir=tempfile.mkdtemp())
        
        try:
            # Benchmark large watch list
            profile = benchmark.benchmark_watch_list_performance(
                watch_list_manager=mock_watch_list_manager,
                watch_list_name="large_list",  # 50 stocks
                test_concurrent=True,
                test_sequential=True,
                test_paginated=True,
                force_refresh=True
            )
            
            # Verify benchmark results
            assert profile.list_size == 50, "Should benchmark correct list size"
            
            # Concurrent results should be present
            assert profile.concurrent_result is not None, "Should have concurrent benchmark"
            assert profile.concurrent_result.success_count > 0, "Concurrent should have successes"
            assert profile.concurrent_result.duration_seconds > 0, "Should measure duration"
            assert profile.concurrent_result.operations_per_second > 0, "Should calculate ops/sec"
            
            # Sequential results should be present  
            assert profile.sequential_result is not None, "Should have sequential benchmark"
            
            # Concurrent should be faster (speedup > 1)
            assert profile.concurrent_speedup is not None, "Should calculate speedup"
            assert profile.concurrent_speedup > 1.0, f"Expected speedup >1x, got {profile.concurrent_speedup:.2f}x"
            
            # Paginated results should be present
            assert profile.paginated_result is not None, "Should have paginated benchmark"
            assert profile.paginated_result.success_count > 0, "Paginated should have successes"
            
        finally:
            # Cleanup
            shutil.rmtree(benchmark.output_dir, ignore_errors=True)
    
    def test_request_deduplication(self, mock_watch_list_manager, mock_price_service):
        """Test that duplicate requests are properly deduplicated"""
        
        config = ConcurrencyConfig(enable_request_deduplication=True)
        optimizer = ConcurrentWatchListOptimizer(
            mock_watch_list_manager,
            concurrency_config=config
        )
        
        # Mock the price service to track call counts
        call_count = {}
        original_method = optimizer.price_service.get_detailed_price_data
        
        def counting_method(ticker, force_refresh=False):
            call_count[ticker] = call_count.get(ticker, 0) + 1
            return original_method(ticker, force_refresh)
        
        optimizer.price_service.get_detailed_price_data = counting_method
        
        try:
            # Create test data with duplicate tickers
            test_tickers = ['AAPL', 'GOOGL', 'AAPL', 'MSFT', 'GOOGL', 'AAPL']  # 3 unique tickers
            
            # Fetch prices concurrently
            results = optimizer._fetch_prices_concurrently(test_tickers, force_refresh=True)
            
            # Should only make 3 unique calls despite 6 requests
            assert len(call_count) == 3, "Should deduplicate requests"
            assert all(count == 1 for count in call_count.values()), "Each ticker should be called only once"
            
            # Should still return results for all requested tickers
            assert len(results) == 6, "Should return results for all requested tickers"
            
        finally:
            optimizer.shutdown()
    
    def test_configuration_customization(self, mock_watch_list_manager, mock_price_service):
        """Test that custom configurations work properly"""
        
        # Custom concurrency config
        concurrency_config = ConcurrencyConfig(
            max_workers=4,
            batch_size=5,
            timeout_seconds=15.0,
            max_retries=1,
            circuit_breaker_threshold=2
        )
        
        # Custom lazy loading config
        lazy_config = LazyLoadingConfig(
            page_size=10,
            prefetch_pages=1,
            cache_pages=3
        )
        
        optimizer = ConcurrentWatchListOptimizer(
            mock_watch_list_manager,
            concurrency_config=concurrency_config,
            lazy_loading_config=lazy_config
        )
        
        try:
            # Test that configurations are applied
            assert optimizer.concurrency_config.max_workers == 4
            assert optimizer.concurrency_config.batch_size == 5
            assert optimizer.lazy_config.page_size == 10
            
            # Test paginated loading with custom page size
            result = optimizer.get_paginated_watch_list("medium_list", page=1, page_size=10)
            
            assert result is not None
            assert len(result['stocks']) == 10, "Should use custom page size"
            assert result['page_size'] == 10
            
        finally:
            optimizer.shutdown()


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_watch_list(self, mock_watch_list_manager, mock_price_service):
        """Test handling of empty watch lists"""
        
        # Create empty watch list
        mock_watch_list_manager.create_watch_list("empty_list", "Empty test list")
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            result = optimizer.get_watch_list_with_concurrent_prices("empty_list")
            
            # Should handle empty list gracefully
            assert result is not None
            assert result.get('stocks', []) == []
            
            # Pagination should also work with empty list
            paginated = optimizer.get_paginated_watch_list("empty_list", page=1)
            assert paginated['total_items'] == 0
            assert paginated['stocks'] == []
            
        finally:
            optimizer.shutdown()
    
    def test_nonexistent_watch_list(self, mock_watch_list_manager, mock_price_service):
        """Test handling of nonexistent watch lists"""
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        try:
            result = optimizer.get_watch_list_with_concurrent_prices("nonexistent_list")
            
            # Should return None or handle gracefully
            assert result is None or result.get('stocks', []) == []
            
        finally:
            optimizer.shutdown()
    
    def test_resource_cleanup_on_shutdown(self, mock_watch_list_manager, mock_price_service):
        """Test that resources are properly cleaned up on shutdown"""
        
        optimizer = create_optimized_watch_list_manager(mock_watch_list_manager)
        
        # Use the optimizer 
        result = optimizer.get_watch_list_with_concurrent_prices("small_list")
        assert result is not None
        
        # Shutdown
        optimizer.shutdown()
        
        # Thread pool should be shutdown
        assert optimizer.executor._shutdown is True
        
        # Caches should be cleared
        assert len(optimizer._page_cache) == 0
        assert len(optimizer._active_requests) == 0


if __name__ == "__main__":
    # Run specific test for development
    pytest.main([__file__ + "::TestLargeWatchListPerformance::test_loading_time_requirement_50_stocks", "-v"])