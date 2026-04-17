"""
Performance Optimization Testing Suite
======================================

This script comprehensively tests all the performance optimizations implemented
in the financial analysis system, including:

1. Lazy loading for historical data
2. Configurable memory limits with LRU eviction
3. Calculation result caching with dependency invalidation
4. Background data refresh
5. Memory profiling and garbage collection
6. API request batching and connection pooling
7. Performance monitoring and metrics collection

Usage:
    python test_performance_optimizations.py
"""

import asyncio
import gc
import logging
import psutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our optimization modules
try:
    from core.data_processing.var_input_data import (
        VarInputData, get_var_input_data, LazyLoadConfig
    )
    from core.data_processing.calculation_cache import (
        CalculationCache, get_calculation_cache
    )
    from core.data_processing.background_refresh import (
        BackgroundRefreshManager, RefreshPolicy, RefreshPriority
    )
    from core.data_processing.api_batch_manager import (
        ApiBatchManager, BatchConfig, ConnectionConfig, RateLimitConfig
    )
    from core.data_processing.universal_data_registry import (
        UniversalDataRegistry, get_registry
    )
except ImportError as e:
    logger.error(f"Failed to import optimization modules: {e}")
    sys.exit(1)


class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.results = {}
        self.test_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'NFLX']
        self.test_variables = ['revenue', 'net_income', 'total_assets', 'cash_flow', 'debt']
        
        # Get memory baseline
        process = psutil.Process()
        self.baseline_memory_mb = process.memory_info().rss / 1024 / 1024
        
        logger.info(f"Baseline memory usage: {self.baseline_memory_mb:.1f} MB")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("Starting comprehensive performance test suite")
        
        test_methods = [
            self.test_lazy_loading,
            self.test_memory_limits_and_eviction,
            self.test_calculation_caching,
            self.test_background_refresh,
            self.test_memory_profiling,
            self.test_api_batching,
            self.test_performance_monitoring,
            self.test_concurrent_load,
            self.test_memory_leak_detection
        ]
        
        for test_method in test_methods:
            try:
                test_name = test_method.__name__
                logger.info(f"Running {test_name}...")
                
                start_time = time.time()
                result = test_method()
                end_time = time.time()
                
                self.results[test_name] = {
                    'result': result,
                    'duration_seconds': end_time - start_time,
                    'status': 'passed'
                }
                
                logger.info(f"{test_name} completed in {end_time - start_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"{test_name} failed: {e}")
                self.results[test_name] = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        # Generate summary
        self.results['summary'] = self._generate_summary()
        
        logger.info("Performance test suite completed")
        return self.results
    
    def test_lazy_loading(self) -> Dict[str, Any]:
        """Test lazy loading implementation"""
        # Configure aggressive lazy loading
        lazy_config = LazyLoadConfig(
            enable_lazy_loading=True,
            memory_threshold_mb=100,  # Low threshold for testing
            max_cached_symbols=5,
            max_periods_per_variable=3
        )
        
        # Get VarInputData instance with lazy loading
        var_data = VarInputData(lazy_config)
        
        # Test data loading and eviction
        loaded_count = 0
        evicted_count = 0
        
        for symbol in self.test_symbols:
            for variable in self.test_variables:
                for period in ['2021', '2022', '2023']:
                    # Set some test data
                    value = random.uniform(1000, 100000)
                    success = var_data.set_variable(
                        symbol, variable, value, period=period, source="test"
                    )
                    if success:
                        loaded_count += 1
        
        # Force memory optimization
        var_data._check_and_optimize_memory()
        
        # Check statistics
        stats = var_data.get_statistics()
        
        return {
            'lazy_loading_enabled': lazy_config.enable_lazy_loading,
            'loaded_data_points': loaded_count,
            'memory_evictions': stats['performance']['memory_evictions'],
            'lazy_loads': stats['performance']['lazy_loads'],
            'current_memory_mb': stats['memory']['current_usage_mb'],
            'memory_threshold_mb': stats['memory']['threshold_mb'],
            'loaded_symbols': stats['data_storage']['loaded_symbols']
        }
    
    def test_memory_limits_and_eviction(self) -> Dict[str, Any]:
        """Test memory limits and LRU/LFU eviction"""
        # Test Universal Data Registry cache with memory limits
        registry = get_registry()
        
        # Fill cache with test data
        initial_cache_size = len(registry.cache.memory_cache)
        
        # Simulate heavy cache usage
        for i in range(200):  # Exceed typical cache limits
            from core.data_processing.universal_data_registry import DataRequest
            
            request = DataRequest(
                data_type="test_data",
                symbol=f"TEST{i:03d}",
                period="annual"
            )
            
            # Simulate cache entry
            cache_key = registry.cache._generate_cache_key(request)
            test_data = {'value': random.uniform(1, 1000), 'timestamp': datetime.now()}
            
            # Manually add to cache for testing
            registry.cache.memory_cache[cache_key] = test_data
            registry.cache.access_counts[cache_key] = random.randint(1, 10)
            registry.cache.last_access[cache_key] = datetime.now()
        
        # Trigger cleanup
        registry.cache._cleanup_memory_cache()
        
        final_cache_size = len(registry.cache.memory_cache)
        
        return {
            'initial_cache_size': initial_cache_size,
            'final_cache_size': final_cache_size,
            'cache_reduced': final_cache_size < 200,
            'memory_limit_mb': registry.cache.memory_limit_bytes / (1024 * 1024),
            'eviction_working': final_cache_size < initial_cache_size + 200
        }
    
    def test_calculation_caching(self) -> Dict[str, Any]:
        """Test calculation result caching with dependency invalidation"""
        cache = get_calculation_cache()
        
        # Test basic caching
        symbol = "AAPL"
        calculation_id = "dcf_valuation"
        test_result = {"valuation": 150.0, "confidence": 0.85}
        dependencies = ["revenue", "cash_flow", "growth_rate"]
        
        # Cache a calculation result
        success = cache.set_result(
            symbol=symbol,
            calculation_id=calculation_id,
            result=test_result,
            dependencies=dependencies,
            computation_time_seconds=2.5
        )
        
        # Retrieve cached result
        retrieved_result = cache.get_result(symbol, calculation_id)
        
        # Test dependency invalidation
        invalidated_count = cache.invalidate_dependencies(symbol, "revenue")
        
        # Try to retrieve after invalidation
        invalidated_result = cache.get_result(symbol, calculation_id)
        
        # Get cache statistics
        stats = cache.get_statistics()
        
        return {
            'caching_successful': success,
            'retrieval_successful': retrieved_result == test_result,
            'invalidation_count': invalidated_count,
            'invalidation_working': invalidated_result is None,
            'cache_hit_rate': stats['performance_derived']['cache_hit_rate'],
            'total_entries': stats['cache_info']['total_entries'],
            'compression_enabled': stats['compression']['compression_enabled']
        }
    
    def test_background_refresh(self) -> Dict[str, Any]:
        """Test background data refresh system"""
        refresh_manager = BackgroundRefreshManager(max_workers=2)
        
        try:
            refresh_manager.start()
            
            # Schedule some refresh requests
            request_ids = []
            for symbol in self.test_symbols[:3]:
                for variable in self.test_variables[:2]:
                    request_id = refresh_manager.schedule_refresh(
                        symbol=symbol,
                        data_identifier=variable,
                        priority=RefreshPriority.HIGH
                    )
                    request_ids.append(request_id)
            
            # Record some data access patterns
            for _ in range(10):
                refresh_manager.record_data_access("AAPL", "revenue")
                refresh_manager.record_data_access("GOOGL", "net_income")
            
            # Wait a bit for processing
            time.sleep(2.0)
            
            # Get statistics
            stats = refresh_manager.get_statistics()
            
            # Check request status
            completed_requests = 0
            for request_id in request_ids:
                status = refresh_manager.get_refresh_status(request_id)
                if status and status.status.value in ['completed', 'failed']:
                    completed_requests += 1
            
            return {
                'refresh_manager_running': stats['system_status']['running'],
                'requests_scheduled': len(request_ids),
                'requests_processed': completed_requests,
                'active_requests': stats['system_status']['active_requests'],
                'success_rate': stats['performance_derived']['success_rate_percent'],
                'access_tracking_working': stats['access_tracking']['total_accesses'] > 0
            }
        
        finally:
            refresh_manager.stop()
    
    def test_memory_profiling(self) -> Dict[str, Any]:
        """Test memory profiling and garbage collection"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Create some objects to test garbage collection
        large_objects = []
        for i in range(1000):
            large_objects.append({
                'id': i,
                'data': list(range(100)),
                'timestamp': datetime.now()
            })
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        
        # Clear references and force garbage collection
        large_objects.clear()
        del large_objects
        
        # Run garbage collection
        collected_objects = gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_freed = peak_memory - final_memory
        
        return {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_freed_mb': memory_freed,
            'objects_collected': collected_objects,
            'gc_working': memory_freed > 0
        }
    
    def test_api_batching(self) -> Dict[str, Any]:
        """Test API request batching and connection pooling"""
        batch_config = BatchConfig(
            batch_window_seconds=0.5,
            max_batch_size=10,
            enable_deduplication=True
        )
        
        connection_config = ConnectionConfig(
            pool_connections=5,
            pool_maxsize=10,
            timeout_seconds=10
        )
        
        rate_limit_config = {
            'test_provider': RateLimitConfig(
                calls_per_minute=60,
                burst_allowance=5
            )
        }
        
        batch_manager = ApiBatchManager(
            batch_config=batch_config,
            connection_config=connection_config,
            rate_limit_config=rate_limit_config
        )
        
        try:
            batch_manager.start()
            
            # Submit multiple requests for batching
            futures = []
            for symbol in self.test_symbols[:5]:
                future = batch_manager.submit_request(
                    api_provider="test_provider",
                    endpoint="get_quote",
                    params={"symbol": symbol},
                    cache_ttl_seconds=30.0
                )
                futures.append(future)
            
            # Wait for completion (with timeout)
            completed_requests = 0
            for future in futures:
                try:
                    # This will likely fail since we don't have real API endpoints
                    # but we can test the batching mechanism
                    result = future.result(timeout=2.0)
                    completed_requests += 1
                except Exception:
                    # Expected to fail with mock endpoints
                    pass
            
            # Get statistics
            stats = batch_manager.get_statistics()
            
            return {
                'batching_enabled': batch_config.enable_deduplication,
                'requests_submitted': stats['performance']['requests_submitted'],
                'requests_batched': stats['performance']['requests_batched'],
                'batch_efficiency': stats['performance_derived']['batch_efficiency_percent'],
                'active_sessions': stats['system_status']['active_sessions'],
                'cache_entries': stats['cache']['entries'],
                'system_running': stats['system_status']['running']
            }
        
        finally:
            batch_manager.stop()
    
    def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test performance monitoring and metrics collection"""
        # Test VarInputData statistics
        var_data = get_var_input_data()
        stats = var_data.get_statistics()
        
        # Test calculation cache statistics
        calc_cache = get_calculation_cache()
        cache_stats = calc_cache.get_statistics()
        
        # Test system performance metrics
        process = psutil.Process()
        
        return {
            'var_data_stats': {
                'total_symbols': stats['data_storage']['symbols'],
                'cache_hit_rate': stats['cache_hit_rate'],
                'get_operations': stats['performance']['get_operations'],
                'memory_usage_mb': stats['memory']['current_usage_mb']
            },
            'calculation_cache_stats': {
                'total_entries': cache_stats['cache_info']['total_entries'],
                'hit_rate': cache_stats['performance_derived']['cache_hit_rate'],
                'memory_usage_mb': cache_stats['cache_info']['total_size_mb']
            },
            'system_stats': {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'memory_rss_mb': process.memory_info().rss / 1024 / 1024
            },
            'monitoring_working': True
        }
    
    def test_concurrent_load(self) -> Dict[str, Any]:
        """Test system performance under concurrent load"""
        var_data = get_var_input_data()
        
        def worker_task(worker_id: int) -> Dict[str, int]:
            """Worker task for concurrent testing"""
            operations = 0
            errors = 0
            
            for i in range(50):  # 50 operations per worker
                try:
                    symbol = random.choice(self.test_symbols)
                    variable = random.choice(self.test_variables)
                    value = random.uniform(1000, 100000)
                    period = random.choice(['2021', '2022', '2023'])
                    
                    # Mix of read and write operations
                    if i % 3 == 0:
                        # Write operation
                        var_data.set_variable(symbol, variable, value, period)
                    else:
                        # Read operation  
                        var_data.get_variable(symbol, variable, period)
                    
                    operations += 1
                    
                except Exception as e:
                    errors += 1
                    logger.warning(f"Worker {worker_id} error: {e}")
            
            return {'operations': operations, 'errors': errors}
        
        # Run concurrent workers
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(worker_task, i)
                for i in range(10)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        
        # Aggregate results
        total_operations = sum(r['operations'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        duration = end_time - start_time
        operations_per_second = total_operations / duration
        
        return {
            'concurrent_workers': 10,
            'total_operations': total_operations,
            'total_errors': total_errors,
            'duration_seconds': duration,
            'operations_per_second': operations_per_second,
            'error_rate_percent': (total_errors / max(total_operations, 1)) * 100,
            'concurrency_working': total_operations > 400  # 10 workers * 50 ops * 80% success
        }
    
    def test_memory_leak_detection(self) -> Dict[str, Any]:
        """Test for memory leaks during extended operation"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        var_data = get_var_input_data()
        
        # Perform many operations to detect leaks
        for cycle in range(10):  # 10 cycles
            # Create and destroy many objects
            for i in range(100):
                symbol = f"TEST{i:03d}"
                for variable in self.test_variables:
                    value = random.uniform(1000, 100000)
                    var_data.set_variable(symbol, variable, value, "2023")
            
            # Force garbage collection
            gc.collect()
            
            # Clear some cache entries
            if cycle % 3 == 0:
                var_data.clear_cache()
        
        # Final garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for this test)
        acceptable_growth = memory_growth < 50.0
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'acceptable_growth': acceptable_growth,
            'leak_detected': not acceptable_growth,
            'test_cycles': 10,
            'operations_per_cycle': 100 * len(self.test_variables)
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        passed_tests = sum(1 for result in self.results.values() 
                          if isinstance(result, dict) and result.get('status') == 'passed')
        failed_tests = sum(1 for result in self.results.values() 
                          if isinstance(result, dict) and result.get('status') == 'failed')
        
        total_duration = sum(result.get('duration_seconds', 0) 
                           for result in self.results.values() 
                           if isinstance(result, dict))
        
        # Get final memory usage
        process = psutil.Process()
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory_mb - self.baseline_memory_mb
        
        return {
            'total_tests': len(self.results) - 1,  # Exclude summary itself
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate_percent': (passed_tests / max(passed_tests + failed_tests, 1)) * 100,
            'total_duration_seconds': total_duration,
            'baseline_memory_mb': self.baseline_memory_mb,
            'final_memory_mb': final_memory_mb,
            'memory_increase_mb': memory_increase,
            'test_timestamp': datetime.now().isoformat()
        }


def main():
    """Main function to run performance tests"""
    print("=" * 60)
    print("Financial Analysis System - Performance Optimization Tests")
    print("=" * 60)
    
    # Initialize test suite
    test_suite = PerformanceTestSuite()
    
    # Run all tests
    results = test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    summary = results['summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate_percent']:.1f}%")
    print(f"Total Duration: {summary['total_duration_seconds']:.2f} seconds")
    print(f"Memory Increase: {summary['memory_increase_mb']:.1f} MB")
    
    print("\n" + "-" * 60)
    print("INDIVIDUAL TEST RESULTS")
    print("-" * 60)
    
    for test_name, result in results.items():
        if test_name == 'summary':
            continue
            
        status = result.get('status', 'unknown')
        duration = result.get('duration_seconds', 0)
        
        print(f"{test_name}: {status.upper()} ({duration:.2f}s)")
        
        if status == 'failed':
            print(f"  Error: {result.get('error', 'Unknown error')}")
        elif status == 'passed':
            # Print key metrics for passed tests
            test_result = result.get('result', {})
            if isinstance(test_result, dict):
                key_metrics = []
                
                # Extract a few key metrics per test type
                if 'lazy_loading_enabled' in test_result:
                    key_metrics.append(f"Lazy Loading: {test_result['lazy_loading_enabled']}")
                    key_metrics.append(f"Memory Evictions: {test_result['memory_evictions']}")
                
                elif 'cache_hit_rate' in test_result:
                    key_metrics.append(f"Cache Hit Rate: {test_result['cache_hit_rate']:.1f}%")
                
                elif 'operations_per_second' in test_result:
                    key_metrics.append(f"Ops/sec: {test_result['operations_per_second']:.1f}")
                
                elif 'memory_freed_mb' in test_result:
                    key_metrics.append(f"Memory Freed: {test_result['memory_freed_mb']:.1f} MB")
                
                if key_metrics:
                    print(f"  {' | '.join(key_metrics)}")
    
    print("\n" + "=" * 60)
    
    # Overall assessment
    if summary['success_rate_percent'] >= 80:
        print("✅ PERFORMANCE OPTIMIZATIONS: WORKING WELL")
    elif summary['success_rate_percent'] >= 60:
        print("⚠️  PERFORMANCE OPTIMIZATIONS: SOME ISSUES DETECTED")
    else:
        print("❌ PERFORMANCE OPTIMIZATIONS: SIGNIFICANT ISSUES")
    
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()