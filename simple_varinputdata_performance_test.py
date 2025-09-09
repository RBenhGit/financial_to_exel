"""
Simple VarInputData Performance Test
===================================

Quick performance analysis focusing on key metrics without complex setup.
"""

import time
import psutil
import gc
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List

# Import the VarInputData system
from core.data_processing.var_input_data import get_var_input_data, clear_cache
from core.data_processing.financial_variable_registry import (
    get_registry, VariableDefinition, VariableCategory, DataType, Units
)

logger = logging.getLogger(__name__)


def setup_test_variables():
    """Register required variables for testing"""
    registry = get_registry()
    
    # Define test variables
    test_vars = [
        ('revenue', 'Total Revenue', VariableCategory.INCOME_STATEMENT, DataType.CURRENCY, Units.MILLIONS_USD),
        ('net_income', 'Net Income', VariableCategory.INCOME_STATEMENT, DataType.CURRENCY, Units.MILLIONS_USD),
        ('free_cash_flow', 'Free Cash Flow', VariableCategory.CASH_FLOW, DataType.CURRENCY, Units.MILLIONS_USD),
        ('total_assets', 'Total Assets', VariableCategory.BALANCE_SHEET, DataType.CURRENCY, Units.MILLIONS_USD),
        ('total_debt', 'Total Debt', VariableCategory.BALANCE_SHEET, DataType.CURRENCY, Units.MILLIONS_USD),
    ]
    
    for var_name, description, category, data_type, units in test_vars:
        if not registry.get_variable_definition(var_name):
            var_def = VariableDefinition(
                name=var_name,
                description=description,
                category=category,
                data_type=data_type,
                units=units,
                validation_rules={}
            )
            registry.register_variable(var_def)
            logger.info(f"Registered variable: {var_name}")


def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    try:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0


def test_basic_performance():
    """Test basic VarInputData performance"""
    print("\nVarInputData Basic Performance Test")
    print("=" * 50)
    
    # Setup
    setup_test_variables()
    clear_cache()
    gc.collect()
    
    var_data = get_var_input_data()
    
    # Test parameters
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    variables = ['revenue', 'net_income', 'free_cash_flow', 'total_assets', 'total_debt']
    periods = ['2023', '2022', '2021', '2020', '2019']
    iterations = 1000
    
    print(f"Testing {len(symbols)} symbols × {len(variables)} variables × {len(periods)} periods")
    print(f"Total operations: {iterations} (set + get operations)")
    
    # Monitor memory
    start_memory = get_memory_usage()
    start_stats = var_data.get_statistics()
    start_time = time.time()
    
    # Performance tracking
    set_times = []
    get_times = []
    success_count = 0
    
    print("\nRunning benchmark...")
    
    # SET operations
    for i in range(iterations // 2):
        symbol = symbols[i % len(symbols)]
        variable = variables[i % len(variables)]
        period = periods[i % len(periods)]
        value = np.random.uniform(1000000, 100000000)
        
        op_start = time.time()
        success = var_data.set_variable(symbol, variable, value, period, "benchmark")
        op_end = time.time()
        
        set_times.append(op_end - op_start)
        if success:
            success_count += 1
    
    # GET operations  
    for i in range(iterations // 2):
        symbol = symbols[i % len(symbols)]
        variable = variables[i % len(variables)]
        period = periods[i % len(periods)]
        
        op_start = time.time()
        result = var_data.get_variable(symbol, variable, period)
        op_end = time.time()
        
        get_times.append(op_end - op_start)
        if result is not None:
            success_count += 1
    
    # End monitoring
    end_time = time.time()
    end_memory = get_memory_usage()
    end_stats = var_data.get_statistics()
    
    # Calculate metrics
    duration = end_time - start_time
    ops_per_second = iterations / duration
    avg_set_time = np.mean(set_times) * 1000  # Convert to milliseconds
    avg_get_time = np.mean(get_times) * 1000
    p95_set_time = np.percentile(set_times, 95) * 1000
    p95_get_time = np.percentile(get_times, 95) * 1000
    
    memory_delta = end_memory - start_memory
    cache_hit_rate = end_stats['cache_hit_rate']
    
    # Results
    print(f"\nPERFORMANCE RESULTS")
    print(f"{'='*30}")
    print(f"Duration: {duration:.2f}s")
    print(f"Operations/second: {ops_per_second:.1f}")
    print(f"Success rate: {(success_count/iterations)*100:.1f}%")
    print(f"")
    print(f"OPERATION TIMING")
    print(f"SET operations avg: {avg_set_time:.2f}ms")
    print(f"GET operations avg: {avg_get_time:.2f}ms") 
    print(f"SET operations p95: {p95_set_time:.2f}ms")
    print(f"GET operations p95: {p95_get_time:.2f}ms")
    print(f"")
    print(f"MEMORY USAGE")
    print(f"Start memory: {start_memory:.1f} MB")
    print(f"End memory: {end_memory:.1f} MB")
    print(f"Memory delta: {memory_delta:+.1f} MB")
    print(f"")
    print(f"CACHE PERFORMANCE")
    print(f"Cache hit rate: {cache_hit_rate:.1f}%")
    print(f"Cache hits: {end_stats['performance']['cache_hits']}")
    print(f"Cache misses: {end_stats['performance']['cache_misses']}")
    print(f"")
    print(f"SYSTEM STATS")
    print(f"Symbols loaded: {end_stats['data_storage']['symbols']}")
    print(f"Total data points: {end_stats['data_storage']['total_data_points']}")
    print(f"Memory evictions: {end_stats['performance']['memory_evictions']}")
    print(f"GC runs: {end_stats['performance']['gc_runs']}")
    
    return {
        'ops_per_second': ops_per_second,
        'success_rate': (success_count/iterations)*100,
        'memory_delta_mb': memory_delta,
        'cache_hit_rate': cache_hit_rate,
        'avg_set_time_ms': avg_set_time,
        'avg_get_time_ms': avg_get_time
    }


def test_memory_scaling():
    """Test memory usage with increasing data volume"""
    print("\nMemory Scaling Test")
    print("=" * 50)
    
    setup_test_variables()
    
    data_volumes = [100, 500, 1000, 2000, 5000]
    results = []
    
    for volume in data_volumes:
        print(f"\nTesting {volume} data points...")
        
        # Clear cache for clean test
        clear_cache()
        gc.collect()
        
        var_data = get_var_input_data()
        start_memory = get_memory_usage()
        start_time = time.time()
        
        # Generate test data
        symbols = [f"TEST{i:03d}" for i in range(min(100, volume // 10))]
        variables = ['revenue', 'net_income', 'free_cash_flow']
        
        for i in range(volume):
            symbol = symbols[i % len(symbols)]
            variable = variables[i % len(variables)]
            period = str(2020 + (i % 4))  # 2020-2023
            value = np.random.uniform(1000000, 50000000)
            
            var_data.set_variable(symbol, variable, value, period, "scaling_test")
        
        end_time = time.time()
        end_memory = get_memory_usage()
        stats = var_data.get_statistics()
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        result = {
            'volume': volume,
            'duration': duration,
            'memory_mb': memory_used,
            'data_points': stats['data_storage']['total_data_points'],
            'symbols': stats['data_storage']['symbols'],
            'evictions': stats['performance']['memory_evictions']
        }
        results.append(result)
        
        print(f"  Duration: {duration:.2f}s")
        print(f"  Memory used: +{memory_used:.1f} MB")
        print(f"  Evictions: {stats['performance']['memory_evictions']}")
    
    # Summary
    print(f"\nSCALING RESULTS")
    print(f"{'Volume':>8} {'Duration':>10} {'Memory':>10} {'Points':>8} {'Symbols':>8} {'Evictions':>10}")
    print(f"{'-'*66}")
    
    for r in results:
        print(f"{r['volume']:>8} {r['duration']:>9.2f}s {r['memory_mb']:>8.1f}MB {r['data_points']:>8} {r['symbols']:>8} {r['evictions']:>10}")
    
    return results


def test_concurrent_access_simple():
    """Simple concurrent access test"""
    print("\nConcurrent Access Test")
    print("=" * 50)
    
    setup_test_variables()
    clear_cache()
    gc.collect()
    
    var_data = get_var_input_data()
    
    # Pre-populate with test data
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    variables = ['revenue', 'net_income']
    
    for symbol in symbols:
        for variable in variables:
            for year in range(2020, 2024):
                value = np.random.uniform(10000000, 100000000)
                var_data.set_variable(symbol, variable, value, str(year), "concurrent_test")
    
    print(f"Pre-populated data for {len(symbols)} symbols")
    
    # Test concurrent reads
    import threading
    import queue
    
    thread_count = 4
    operations_per_thread = 250
    results_queue = queue.Queue()
    
    def worker():
        """Worker thread for concurrent reads"""
        local_times = []
        local_success = 0
        
        for i in range(operations_per_thread):
            symbol = symbols[i % len(symbols)]
            variable = variables[i % len(variables)]
            period = str(2020 + (i % 4))
            
            start_time = time.time()
            result = var_data.get_variable(symbol, variable, period)
            end_time = time.time()
            
            local_times.append(end_time - start_time)
            if result is not None:
                local_success += 1
        
        results_queue.put((local_success, local_times))
    
    print(f"Running {thread_count} threads × {operations_per_thread} operations...")
    
    start_time = time.time()
    threads = []
    
    for i in range(thread_count):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    end_time = time.time()
    
    # Collect results
    total_success = 0
    all_times = []
    
    while not results_queue.empty():
        success, times = results_queue.get()
        total_success += success
        all_times.extend(times)
    
    # Calculate metrics
    duration = end_time - start_time
    total_operations = thread_count * operations_per_thread
    ops_per_second = total_operations / duration
    success_rate = (total_success / total_operations) * 100
    avg_response_time = np.mean(all_times) * 1000  # ms
    
    print(f"\nCONCURRENT RESULTS")
    print(f"Duration: {duration:.2f}s")
    print(f"Operations/second: {ops_per_second:.1f}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Average response time: {avg_response_time:.2f}ms")
    
    return {
        'ops_per_second': ops_per_second,
        'success_rate': success_rate,
        'avg_response_time_ms': avg_response_time
    }


def main():
    """Run comprehensive simple performance tests"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("VarInputData Simple Performance Analysis")
    print("=" * 60)
    
    try:
        # Run tests
        basic_results = test_basic_performance()
        scaling_results = test_memory_scaling()
        concurrent_results = test_concurrent_access_simple()
        
        # Summary report
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\nBASIC PERFORMANCE")
        print(f"   Operations/second: {basic_results['ops_per_second']:.1f}")
        print(f"   Success rate: {basic_results['success_rate']:.1f}%")
        print(f"   Memory delta: {basic_results['memory_delta_mb']:+.1f} MB")
        print(f"   Cache hit rate: {basic_results['cache_hit_rate']:.1f}%")
        
        print(f"\nMEMORY SCALING")
        max_volume = max(scaling_results, key=lambda x: x['volume'])
        print(f"   Max tested volume: {max_volume['volume']} points")
        print(f"   Memory at max: +{max_volume['memory_mb']:.1f} MB")
        print(f"   Evictions at max: {max_volume['evictions']}")
        
        print(f"\nCONCURRENT ACCESS")
        print(f"   Concurrent ops/sec: {concurrent_results['ops_per_second']:.1f}")
        print(f"   Concurrent success rate: {concurrent_results['success_rate']:.1f}%")
        print(f"   Avg response time: {concurrent_results['avg_response_time_ms']:.2f}ms")
        
        # Overall assessment
        print(f"\nOVERALL ASSESSMENT")
        overall_score = (
            min(basic_results['ops_per_second'] / 10, 10) +
            min(basic_results['success_rate'] / 10, 10) +
            min(concurrent_results['ops_per_second'] / 50, 10) +
            (10 if basic_results['cache_hit_rate'] > 70 else 5)
        ) * 2.5
        
        print(f"   Performance Score: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print(f"   Status: EXCELLENT - System performing well")
        elif overall_score >= 60:
            print(f"   Status: GOOD - Minor optimization opportunities")
        else:
            print(f"   Status: NEEDS OPTIMIZATION - Performance issues detected")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        logger.error(f"Performance test failed: {e}")


if __name__ == "__main__":
    main()