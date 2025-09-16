#!/usr/bin/env python3
"""
Resilience Performance Tests
===========================

Performance tests specifically focused on resilience features including:
- Cache performance under stress
- Rate limiting efficiency
- Fallback mechanism performance
- Circuit breaker overhead
- Concurrent data source access
"""

import sys
import time
import logging
import unittest
import pytest
import statistics
from unittest.mock import patch, MagicMock
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import threading
import gc

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.data_processing.rate_limiting.enhanced_rate_limiter import (
    EnhancedRateLimiter, get_rate_limiter, reset_rate_limiter
)
from core.data_processing.monitoring.health_monitor import get_health_monitor, reset_health_monitor
from utils.input_validator import ValidationLevel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Helper class for performance measurement"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.measurements = []

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.measurements.append(duration)

    def add_measurement(self, duration: float):
        """Add a manual measurement"""
        self.measurements.append(duration)

    def get_stats(self) -> dict:
        """Get performance statistics"""
        if not self.measurements:
            return {}

        return {
            'count': len(self.measurements),
            'total_time': sum(self.measurements),
            'avg_time': statistics.mean(self.measurements),
            'min_time': min(self.measurements),
            'max_time': max(self.measurements),
            'median_time': statistics.median(self.measurements),
            'std_dev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0
        }


@pytest.mark.performance
class TestResiliencePerformance(unittest.TestCase):
    """Performance tests for resilience features"""

    def setUp(self):
        """Set up test environment"""
        reset_rate_limiter()
        reset_health_monitor()

        with patch('time.sleep'):  # Speed up setup
            self.manager = CentralizedDataManager(
                base_path=".",
                validation_level=ValidationLevel.PERMISSIVE
            )

        self.test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]

    def tearDown(self):
        """Clean up after tests"""
        reset_rate_limiter()
        reset_health_monitor()
        gc.collect()  # Force garbage collection

    @pytest.mark.timeout(60)
    def test_cache_performance_under_load(self):
        """Test cache performance under concurrent load"""
        logger.info("Testing cache performance under concurrent load")

        cache_hits = 0
        cache_misses = 0
        total_requests = 0
        cache_hit_times = []
        cache_miss_times = []

        def fetch_with_timing(ticker, force_reload=False):
            """Fetch data and measure cache performance"""
            nonlocal cache_hits, cache_misses, total_requests

            start_time = time.time()

            # First request (cache miss expected)
            data1 = self.manager.fetch_market_data(ticker, force_reload=force_reload)
            first_time = time.time() - start_time

            start_time = time.time()
            # Second request (cache hit expected if not force_reload)
            data2 = self.manager.fetch_market_data(ticker, force_reload=False)
            second_time = time.time() - start_time

            total_requests += 2

            if data1:
                cache_miss_times.append(first_time)
                cache_misses += 1

            if data2:
                if second_time < first_time * 0.5:  # Significantly faster = cache hit
                    cache_hits += 1
                    cache_hit_times.append(second_time)
                else:
                    cache_misses += 1
                    cache_miss_times.append(second_time)

            return data1 or data2

        # Test sequential cache performance
        sequential_profiler = PerformanceProfiler("sequential_cache")
        with sequential_profiler:
            for ticker in self.test_tickers[:4]:
                fetch_with_timing(ticker)

        # Test concurrent cache performance
        concurrent_profiler = PerformanceProfiler("concurrent_cache")
        with concurrent_profiler:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for ticker in self.test_tickers:
                    future = executor.submit(fetch_with_timing, ticker)
                    futures.append(future)

                for future in as_completed(futures, timeout=30):
                    try:
                        future.result()
                    except Exception as e:
                        logger.warning(f"Concurrent cache test error: {e}")

        # Performance assertions
        sequential_stats = sequential_profiler.get_stats()
        concurrent_stats = concurrent_profiler.get_stats()

        self.assertGreater(cache_hits, 0, "Should have cache hits")
        self.assertGreater(cache_misses, 0, "Should have cache misses")

        # Cache hits should be significantly faster than misses
        if cache_hit_times and cache_miss_times:
            avg_hit_time = statistics.mean(cache_hit_times)
            avg_miss_time = statistics.mean(cache_miss_times)
            self.assertLess(avg_hit_time, avg_miss_time * 0.8,
                           "Cache hits should be significantly faster")

        cache_hit_ratio = cache_hits / total_requests if total_requests > 0 else 0
        logger.info(f"Cache hit ratio: {cache_hit_ratio:.2%}")
        logger.info(f"Sequential stats: {sequential_stats}")
        logger.info(f"Concurrent stats: {concurrent_stats}")

        # Basic performance expectations
        if concurrent_stats.get('avg_time'):
            self.assertLess(concurrent_stats['avg_time'], 10.0,
                           "Concurrent cache access should be reasonable")

    @pytest.mark.timeout(90)
    def test_rate_limiter_performance_overhead(self):
        """Test rate limiter performance overhead"""
        logger.info("Testing rate limiter performance overhead")

        # Test without rate limiter
        no_limiter_times = []
        for i in range(20):
            start_time = time.time()
            # Simulate request without rate limiting
            with patch.object(self.manager, 'rate_limiter', None):
                try:
                    self.manager.fetch_market_data("AAPL", force_reload=True)
                except:
                    pass  # Ignore errors, just measure timing
            no_limiter_times.append(time.time() - start_time)

        # Test with rate limiter
        with_limiter_times = []
        for i in range(20):
            start_time = time.time()
            try:
                self.manager.fetch_market_data("AAPL", force_reload=True)
            except:
                pass  # Ignore errors, just measure timing
            with_limiter_times.append(time.time() - start_time)

        # Calculate overhead
        if no_limiter_times and with_limiter_times:
            avg_no_limiter = statistics.mean(no_limiter_times)
            avg_with_limiter = statistics.mean(with_limiter_times)
            overhead = avg_with_limiter - avg_no_limiter
            overhead_percentage = (overhead / avg_no_limiter) * 100 if avg_no_limiter > 0 else 0

            logger.info(f"Average time without rate limiter: {avg_no_limiter:.4f}s")
            logger.info(f"Average time with rate limiter: {avg_with_limiter:.4f}s")
            logger.info(f"Rate limiter overhead: {overhead:.4f}s ({overhead_percentage:.1f}%)")

            # Overhead should be minimal
            self.assertLess(overhead_percentage, 50,
                           "Rate limiter overhead should be under 50%")

    @pytest.mark.timeout(120)
    def test_circuit_breaker_performance(self):
        """Test circuit breaker performance impact"""
        logger.info("Testing circuit breaker performance impact")

        rate_limiter = self.manager.rate_limiter
        yahoo_cb = rate_limiter.circuit_breakers['yahoo_finance']

        # Test performance with closed circuit breaker
        closed_times = []
        yahoo_cb.state = yahoo_cb.CircuitState.CLOSED if hasattr(yahoo_cb, 'CircuitState') else 'CLOSED'

        for i in range(15):
            start_time = time.time()
            try:
                self.manager.fetch_market_data("MSFT", force_reload=True)
            except:
                pass
            closed_times.append(time.time() - start_time)

        # Force circuit breaker to open
        for i in range(10):
            yahoo_cb.record_failure()

        # Test performance with open circuit breaker
        open_times = []
        for i in range(15):
            start_time = time.time()
            try:
                self.manager.fetch_market_data("MSFT", force_reload=True)
            except:
                pass
            open_times.append(time.time() - start_time)

        # Analyze performance difference
        if closed_times and open_times:
            avg_closed = statistics.mean(closed_times)
            avg_open = statistics.mean(open_times)

            logger.info(f"Average time with closed circuit: {avg_closed:.4f}s")
            logger.info(f"Average time with open circuit: {avg_open:.4f}s")

            # Open circuit should trigger faster fallback
            if avg_open < avg_closed:
                logger.info("✓ Circuit breaker reduces response time by triggering fallback")
            else:
                logger.info("⚠ Circuit breaker shows mixed performance impact")

    @pytest.mark.timeout(90)
    def test_fallback_mechanism_performance(self):
        """Test fallback mechanism performance"""
        logger.info("Testing fallback mechanism performance")

        # Simulate primary source failure
        original_fetch = self.manager._fetch_yahoo_finance_data

        def failing_yahoo(*args, **kwargs):
            raise Exception("Simulated Yahoo Finance failure")

        fallback_times = []
        direct_times = []

        # Test direct fallback performance
        with patch.object(self.manager, '_fetch_yahoo_finance_data', failing_yahoo):
            for ticker in self.test_tickers[:3]:
                start_time = time.time()
                try:
                    result = self.manager.fetch_market_data(ticker, force_reload=True)
                    fallback_time = time.time() - start_time
                    fallback_times.append(fallback_time)
                except Exception as e:
                    logger.warning(f"Fallback test error for {ticker}: {e}")

        # Test normal direct access performance (for comparison)
        for ticker in self.test_tickers[:3]:
            start_time = time.time()
            try:
                result = self.manager.fetch_market_data(ticker, force_reload=True)
                direct_time = time.time() - start_time
                direct_times.append(direct_time)
            except Exception as e:
                logger.warning(f"Direct test error for {ticker}: {e}")

        # Analyze fallback performance
        if fallback_times:
            avg_fallback = statistics.mean(fallback_times)
            max_fallback = max(fallback_times)
            logger.info(f"Average fallback time: {avg_fallback:.4f}s")
            logger.info(f"Maximum fallback time: {max_fallback:.4f}s")

            # Fallback should complete within reasonable time
            self.assertLess(avg_fallback, 15.0,
                           "Fallback mechanism should be reasonably fast")
            self.assertLess(max_fallback, 30.0,
                           "Maximum fallback time should be acceptable")

        if direct_times and fallback_times:
            avg_direct = statistics.mean(direct_times)
            avg_fallback = statistics.mean(fallback_times)
            logger.info(f"Performance ratio (fallback/direct): {avg_fallback/avg_direct:.2f}")

    @pytest.mark.timeout(120)
    def test_concurrent_data_source_performance(self):
        """Test performance under concurrent access to multiple data sources"""
        logger.info("Testing concurrent data source performance")

        results = {
            'successful_requests': 0,
            'failed_requests': 0,
            'total_time': 0,
            'thread_times': [],
            'requests_per_second': 0
        }

        def concurrent_fetch(ticker_batch):
            """Fetch data for a batch of tickers"""
            thread_start = time.time()
            local_success = 0
            local_failure = 0

            for ticker in ticker_batch:
                try:
                    data = self.manager.fetch_market_data(ticker, force_reload=True)
                    if data:
                        local_success += 1
                    else:
                        local_failure += 1
                except Exception:
                    local_failure += 1

            thread_time = time.time() - thread_start
            return {
                'success': local_success,
                'failure': local_failure,
                'time': thread_time
            }

        # Create batches for concurrent processing
        batch_size = 2
        ticker_batches = [
            self.test_tickers[i:i + batch_size]
            for i in range(0, len(self.test_tickers), batch_size)
        ]

        overall_start = time.time()

        # Execute concurrent batches
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for batch in ticker_batches:
                future = executor.submit(concurrent_fetch, batch)
                futures.append(future)

            for future in as_completed(futures, timeout=60):
                try:
                    result = future.result()
                    results['successful_requests'] += result['success']
                    results['failed_requests'] += result['failure']
                    results['thread_times'].append(result['time'])
                except Exception as e:
                    logger.warning(f"Concurrent test thread error: {e}")
                    results['failed_requests'] += batch_size

        results['total_time'] = time.time() - overall_start

        # Calculate performance metrics
        total_requests = results['successful_requests'] + results['failed_requests']
        if results['total_time'] > 0:
            results['requests_per_second'] = total_requests / results['total_time']

        success_rate = (results['successful_requests'] / total_requests * 100
                       if total_requests > 0 else 0)

        # Performance assertions
        self.assertGreater(results['requests_per_second'], 0.5,
                          "Should maintain reasonable throughput")
        self.assertGreater(success_rate, 30,
                          "Should maintain reasonable success rate under concurrent load")

        if results['thread_times']:
            avg_thread_time = statistics.mean(results['thread_times'])
            max_thread_time = max(results['thread_times'])

            logger.info(f"Concurrent performance results:")
            logger.info(f"  Total requests: {total_requests}")
            logger.info(f"  Success rate: {success_rate:.1f}%")
            logger.info(f"  Requests/second: {results['requests_per_second']:.2f}")
            logger.info(f"  Average thread time: {avg_thread_time:.2f}s")
            logger.info(f"  Maximum thread time: {max_thread_time:.2f}s")

    @pytest.mark.timeout(60)
    def test_memory_usage_under_load(self):
        """Test memory usage during resilience operations"""
        logger.info("Testing memory usage under resilience load")

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform multiple operations to test memory usage
        for i in range(50):
            try:
                ticker = self.test_tickers[i % len(self.test_tickers)]
                self.manager.fetch_market_data(ticker, force_reload=True)

                # Force some failures to test error handling memory
                if i % 10 == 0:
                    with patch('requests.get', side_effect=Exception("Test error")):
                        try:
                            self.manager.fetch_market_data(ticker, force_reload=True)
                        except:
                            pass

            except Exception:
                pass  # Ignore errors, focus on memory usage

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        logger.info(f"Initial memory: {initial_memory:.1f} MB")
        logger.info(f"Final memory: {final_memory:.1f} MB")
        logger.info(f"Memory growth: {memory_growth:.1f} MB")

        # Memory growth should be reasonable
        self.assertLess(memory_growth, 100,
                       "Memory growth should be under 100MB for resilience operations")


def run_resilience_performance_tests():
    """Run the resilience performance test suite"""
    print("=" * 70)
    print("RESILIENCE PERFORMANCE TEST SUITE")
    print("=" * 70)
    print("Testing performance characteristics of resilience features")
    print()

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestResiliencePerformance)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 70)
    print("RESILIENCE PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nPERFORMANCE ISSUES:")
        for test, traceback in result.failures:
            print(f"- {test}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) /
                   result.testsRun * 100) if result.testsRun > 0 else 0

    print(f"\nPerformance Test Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("🚀 PERFORMANCE EXCELLENT: Resilience features maintain good performance")
    elif success_rate >= 60:
        print("⚠️  PERFORMANCE ACCEPTABLE: Some resilience features may need optimization")
    else:
        print("❌ PERFORMANCE CRITICAL: Significant performance issues with resilience features")

    print("\nPerformance Recommendations:")
    print("- Monitor cache hit ratios in production")
    print("- Optimize fallback source selection algorithms")
    print("- Consider async processing for non-critical data fetching")
    print("- Review rate limiting thresholds for optimal performance")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_resilience_performance_tests()
    print(f"\n{'✅ Performance tests passed!' if success else '❌ Performance tests failed!'}")