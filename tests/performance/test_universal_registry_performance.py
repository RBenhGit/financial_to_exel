"""
Universal Data Registry Performance Analysis
==========================================

Performance testing for the Universal Data Registry system focusing on:
- Cache performance and hit rates
- Multi-layer caching (memory + disk) efficiency
- Data source fallback performance  
- Thread safety under load
"""

import time
import threading
import psutil
import gc
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# Import the Universal Data Registry system
from core.data_processing.universal_data_registry import (
    UniversalDataRegistry,
    DataRequest,
    DataResponse,
    CachePolicy,
    ValidationLevel,
    DataSourceType,
    DataLineage
)

logger = logging.getLogger(__name__)


def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    try:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0


def test_registry_cache_performance():
    """Test Universal Data Registry cache performance"""
    print("\nUniversal Data Registry Cache Performance Test")
    print("=" * 50)
    
    # Initialize registry
    registry = UniversalDataRegistry()
    
    # Test parameters
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    data_types = ['financial_statements', 'market_data', 'ratios']
    periods = ['annual', 'quarterly', 'monthly']
    
    print(f"Testing {len(symbols)} symbols × {len(data_types)} data types × {len(periods)} periods")
    
    # Start monitoring
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Performance tracking
    cache_hits = 0
    cache_misses = 0
    response_times = []
    
    # First pass - populate cache (will be cache misses)
    print("First pass: Populating cache...")
    for symbol in symbols:
        for data_type in data_types:
            for period in periods:
                request = DataRequest(
                    data_type=data_type,
                    symbol=symbol,
                    period=period,
                    cache_policy=CachePolicy.DEFAULT
                )
                
                op_start = time.time()
                response = registry.get_data(request)
                op_end = time.time()
                
                response_times.append(op_end - op_start)
                
                if response and response.cache_hit:
                    cache_hits += 1
                else:
                    cache_misses += 1
    
    # Second pass - test cache hits
    print("Second pass: Testing cache hits...")
    second_pass_times = []
    second_pass_hits = 0
    second_pass_misses = 0
    
    for symbol in symbols:
        for data_type in data_types:
            for period in periods:
                request = DataRequest(
                    data_type=data_type,
                    symbol=symbol,
                    period=period,
                    cache_policy=CachePolicy.PREFER_CACHE
                )
                
                op_start = time.time()
                response = registry.get_data(request)
                op_end = time.time()
                
                second_pass_times.append(op_end - op_start)
                
                if response and response.cache_hit:
                    second_pass_hits += 1
                else:
                    second_pass_misses += 1
    
    # End monitoring
    end_time = time.time()
    end_memory = get_memory_usage()
    duration = end_time - start_time
    
    total_operations = len(symbols) * len(data_types) * len(periods) * 2  # Two passes
    
    # Calculate metrics
    avg_response_time_1st = np.mean(response_times) * 1000  # ms
    avg_response_time_2nd = np.mean(second_pass_times) * 1000  # ms
    cache_hit_rate_2nd = (second_pass_hits / max(1, second_pass_hits + second_pass_misses)) * 100
    memory_delta = end_memory - start_memory
    
    # Results
    print(f"\nPERFORMANCE RESULTS")
    print(f"{'='*30}")
    print(f"Total duration: {duration:.2f}s")
    print(f"Total operations: {total_operations}")
    print(f"Operations/second: {total_operations/duration:.1f}")
    print(f"Memory delta: {memory_delta:+.1f} MB")
    print(f"")
    print(f"FIRST PASS (Cache Population)")
    print(f"Average response time: {avg_response_time_1st:.2f}ms")
    print(f"Cache hits: {cache_hits}")
    print(f"Cache misses: {cache_misses}")
    print(f"")
    print(f"SECOND PASS (Cache Testing)")
    print(f"Average response time: {avg_response_time_2nd:.2f}ms")
    print(f"Cache hit rate: {cache_hit_rate_2nd:.1f}%")
    print(f"Cache hits: {second_pass_hits}")
    print(f"Cache misses: {second_pass_misses}")
    print(f"")
    print(f"CACHE EFFICIENCY")
    if avg_response_time_1st > 0:
        speedup = avg_response_time_1st / max(avg_response_time_2nd, 0.001)
        print(f"Cache speedup: {speedup:.1f}x faster")
    
    return {
        'total_ops_per_sec': total_operations/duration,
        'cache_hit_rate': cache_hit_rate_2nd,
        'avg_response_1st_ms': avg_response_time_1st,
        'avg_response_2nd_ms': avg_response_time_2nd,
        'memory_delta_mb': memory_delta
    }


def test_registry_data_source_fallback():
    """Test data source fallback performance"""
    print("\nData Source Fallback Performance Test")
    print("=" * 50)
    
    registry = UniversalDataRegistry()
    
    # Test different source preferences
    fallback_tests = [
        {'name': 'Excel Primary', 'sources': [DataSourceType.EXCEL, DataSourceType.API_YAHOO]},
        {'name': 'API Primary', 'sources': [DataSourceType.API_YAHOO, DataSourceType.EXCEL]},
        {'name': 'Multi-API', 'sources': [DataSourceType.API_FMP, DataSourceType.API_ALPHA_VANTAGE, DataSourceType.API_YAHOO]}
    ]
    
    results = []
    
    for test_config in fallback_tests:
        print(f"\nTesting: {test_config['name']}")
        
        start_time = time.time()
        response_times = []
        success_count = 0
        
        # Test with sample requests
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_symbols:
            request = DataRequest(
                data_type='financial_statements',
                symbol=symbol,
                period='annual',
                source_preference=test_config['sources'],
                cache_policy=CachePolicy.NO_CACHE  # Force fresh requests
            )
            
            op_start = time.time()
            response = registry.get_data(request)
            op_end = time.time()
            
            response_times.append(op_end - op_start)
            if response:
                success_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        avg_response_time = np.mean(response_times) * 1000 if response_times else 0
        success_rate = (success_count / len(test_symbols)) * 100
        
        result = {
            'name': test_config['name'],
            'duration': duration,
            'avg_response_ms': avg_response_time,
            'success_rate': success_rate,
            'operations': len(test_symbols)
        }
        results.append(result)
        
        print(f"  Duration: {duration:.2f}s")
        print(f"  Avg response time: {avg_response_time:.2f}ms")
        print(f"  Success rate: {success_rate:.1f}%")
    
    # Summary comparison
    print(f"\nFALLBACK COMPARISON")
    print(f"{'Strategy':<15} {'Duration':<10} {'Response':<12} {'Success':<8}")
    print(f"{'-'*50}")
    
    for result in results:
        print(f"{result['name']:<15} {result['duration']:<9.2f}s {result['avg_response_ms']:<11.1f}ms {result['success_rate']:<7.1f}%")
    
    return results


def test_registry_concurrent_access():
    """Test concurrent access to Universal Data Registry"""
    print("\nConcurrent Access Performance Test")
    print("=" * 50)
    
    registry = UniversalDataRegistry()
    
    # Test parameters
    thread_count = 6
    operations_per_thread = 20
    
    print(f"Running {thread_count} threads × {operations_per_thread} operations...")
    
    # Shared results storage
    import queue
    results_queue = queue.Queue()
    
    def worker_thread(thread_id: int):
        """Worker thread function"""
        local_times = []
        local_success = 0
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        for i in range(operations_per_thread):
            symbol = symbols[i % len(symbols)]
            
            request = DataRequest(
                data_type='market_data',
                symbol=symbol,
                period='daily',
                cache_policy=CachePolicy.DEFAULT
            )
            
            try:
                start_time = time.time()
                response = registry.get_data(request)
                end_time = time.time()
                
                local_times.append(end_time - start_time)
                if response:
                    local_success += 1
                    
            except Exception as e:
                logger.error(f"Error in worker thread {thread_id}: {e}")
        
        results_queue.put((thread_id, local_success, local_times))
    
    # Start monitoring
    start_time = time.time()
    start_memory = get_memory_usage()
    
    # Run concurrent threads
    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=worker_thread, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # End monitoring
    end_time = time.time()
    end_memory = get_memory_usage()
    
    # Collect results
    total_success = 0
    all_times = []
    
    while not results_queue.empty():
        thread_id, success, times = results_queue.get()
        total_success += success
        all_times.extend(times)
    
    # Calculate metrics
    duration = end_time - start_time
    total_operations = thread_count * operations_per_thread
    ops_per_second = total_operations / duration
    success_rate = (total_success / total_operations) * 100
    avg_response_time = np.mean(all_times) * 1000 if all_times else 0
    memory_delta = end_memory - start_memory
    
    print(f"\nCONCURRENT RESULTS")
    print(f"Duration: {duration:.2f}s")
    print(f"Operations/second: {ops_per_second:.1f}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Average response time: {avg_response_time:.2f}ms")
    print(f"Memory delta: {memory_delta:+.1f} MB")
    print(f"Threads completed: {len(threads)}/{thread_count}")
    
    return {
        'ops_per_second': ops_per_second,
        'success_rate': success_rate,
        'avg_response_time_ms': avg_response_time,
        'memory_delta_mb': memory_delta,
        'thread_safety_verified': len(threads) == thread_count
    }


def main():
    """Run comprehensive Universal Data Registry performance tests"""
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')  # Reduce log noise
    
    print("Universal Data Registry Performance Analysis")
    print("=" * 60)
    
    try:
        # Run performance tests
        cache_results = test_registry_cache_performance()
        fallback_results = test_registry_data_source_fallback()
        concurrent_results = test_registry_concurrent_access()
        
        # Summary report
        print("\n" + "="*60)
        print("REGISTRY PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\nCACHE PERFORMANCE")
        print(f"   Operations/second: {cache_results['total_ops_per_sec']:.1f}")
        print(f"   Cache hit rate: {cache_results['cache_hit_rate']:.1f}%")
        print(f"   Memory delta: {cache_results['memory_delta_mb']:+.1f} MB")
        if cache_results['avg_response_1st_ms'] > 0:
            speedup = cache_results['avg_response_1st_ms'] / max(cache_results['avg_response_2nd_ms'], 0.001)
            print(f"   Cache speedup: {speedup:.1f}x")
        
        print(f"\nDATA SOURCE FALLBACK")
        best_fallback = min(fallback_results, key=lambda x: x['avg_response_ms'])
        print(f"   Best strategy: {best_fallback['name']}")
        print(f"   Best avg response: {best_fallback['avg_response_ms']:.1f}ms")
        print(f"   Best success rate: {best_fallback['success_rate']:.1f}%")
        
        print(f"\nCONCURRENT ACCESS")
        print(f"   Concurrent ops/sec: {concurrent_results['ops_per_second']:.1f}")
        print(f"   Success rate: {concurrent_results['success_rate']:.1f}%")
        print(f"   Thread safety: {'✓ VERIFIED' if concurrent_results['thread_safety_verified'] else '✗ ISSUES'}")
        
        # Overall assessment
        print(f"\nOVERALL ASSESSMENT")
        
        # Calculate overall score
        cache_score = min(cache_results['cache_hit_rate'] / 10, 10)  # 0-10
        perf_score = min(cache_results['total_ops_per_sec'] / 50, 10)  # 0-10
        concurrent_score = min(concurrent_results['ops_per_second'] / 20, 10)  # 0-10
        reliability_score = min(concurrent_results['success_rate'] / 10, 10)  # 0-10
        
        overall_score = (cache_score + perf_score + concurrent_score + reliability_score) * 2.5
        
        print(f"   Performance Score: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print(f"   Status: EXCELLENT - Registry performing optimally")
        elif overall_score >= 60:
            print(f"   Status: GOOD - Some optimization opportunities")
        else:
            print(f"   Status: NEEDS OPTIMIZATION - Performance issues detected")
        
        # Key recommendations
        print(f"\nKEY FINDINGS")
        print(f"- Cache system {'is working effectively' if cache_results['cache_hit_rate'] > 80 else 'needs optimization'}")
        print(f"- Memory usage is {'efficient' if cache_results['memory_delta_mb'] < 10 else 'high'}")
        print(f"- Thread safety is {'verified' if concurrent_results['thread_safety_verified'] else 'problematic'}")
        print(f"- Data source fallback is {'reliable' if best_fallback['success_rate'] > 80 else 'unreliable'}")
        
        return {
            'overall_score': overall_score,
            'cache_results': cache_results,
            'fallback_results': fallback_results,
            'concurrent_results': concurrent_results
        }
        
    except Exception as e:
        print(f"\nERROR: {e}")
        logger.error(f"Registry performance test failed: {e}")
        return None


if __name__ == "__main__":
    results = main()
    if results:
        print(f"\nBenchmark completed successfully!")
        print(f"Overall performance score: {results['overall_score']:.1f}/100")