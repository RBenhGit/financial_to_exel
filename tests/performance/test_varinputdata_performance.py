"""
VarInputData Performance Benchmarking
====================================

Comprehensive performance analysis of the VarInputData system including:
- Memory optimization effectiveness
- Lazy loading performance
- Thread safety overhead
- Concurrent access patterns
- Cache hit/miss ratios
- Eviction strategy performance
"""

import time
import threading
import psutil
import gc
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the VarInputData system
from core.data_processing.var_input_data import (
    VarInputData, 
    get_var_input_data,
    VariableMetadata,
    LazyLoadConfig,
    clear_cache
)

logger = logging.getLogger(__name__)


@dataclass
class VarInputDataBenchmarkResult:
    """Results of VarInputData performance benchmark"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_start_mb: float
    memory_end_mb: float
    memory_peak_mb: float
    operations_count: int
    operations_per_second: float
    cache_hit_rate: float
    evictions_count: int
    gc_runs: int
    thread_count: int
    success_rate: float
    average_response_time: float
    p95_response_time: float
    system_stats: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_delta_mb(self) -> float:
        """Memory change during benchmark"""
        return self.memory_end_mb - self.memory_start_mb


class VarInputDataPerformanceBenchmark:
    """
    Comprehensive VarInputData performance benchmarking system
    """
    
    def __init__(self, output_dir: str = "performance_reports"):
        """Initialize benchmark system"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[VarInputDataBenchmarkResult] = []
        self.response_times: List[float] = []
        
        logger.info(f"VarInputData performance benchmarking initialized")
    
    def benchmark_basic_operations(self, 
                                 symbols: List[str] = None,
                                 variables: List[str] = None,
                                 periods: List[str] = None,
                                 iterations: int = 1000) -> VarInputDataBenchmarkResult:
        """
        Benchmark basic get/set operations performance
        
        Args:
            symbols: List of symbols to test (defaults to FAANG stocks)
            variables: List of variables to test (defaults to core metrics)
            periods: List of periods to test
            iterations: Number of operations to perform
        """
        if symbols is None:
            symbols = ['AAPL', 'AMZN', 'GOOGL', 'META', 'NFLX', 'MSFT', 'TSLA', 'NVDA']
        
        if variables is None:
            variables = ['revenue', 'net_income', 'free_cash_flow', 'total_assets', 'total_debt']
        
        if periods is None:
            periods = ['2023', '2022', '2021', '2020', '2019']
        
        logger.info(f"Benchmarking basic operations: {iterations} iterations")
        
        # Clear cache to ensure fair test
        clear_cache()
        gc.collect()
        
        # Get VarInputData instance
        var_data = get_var_input_data()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        start_stats = var_data.get_statistics()
        
        response_times = []
        success_count = 0
        
        try:
            # Perform set operations
            for i in range(iterations // 2):
                symbol = symbols[i % len(symbols)]
                variable = variables[i % len(variables)]
                period = periods[i % len(periods)]
                value = np.random.uniform(1000, 100000)  # Random financial value
                
                operation_start = time.time()
                success = var_data.set_variable(
                    symbol=symbol,
                    variable_name=variable,
                    value=value,
                    period=period,
                    source="benchmark_test"
                )
                operation_end = time.time()
                
                if success:
                    success_count += 1
                response_times.append(operation_end - operation_start)
            
            # Perform get operations
            for i in range(iterations // 2):
                symbol = symbols[i % len(symbols)]
                variable = variables[i % len(variables)]
                period = periods[i % len(periods)]
                
                operation_start = time.time()
                result = var_data.get_variable(symbol, variable, period)
                operation_end = time.time()
                
                if result is not None:
                    success_count += 1
                response_times.append(operation_end - operation_start)
        
        except Exception as e:
            logger.error(f"Error during basic operations benchmark: {e}")
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        end_stats = var_data.get_statistics()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        cache_hit_rate = end_stats['cache_hit_rate']
        evictions = end_stats['performance']['memory_evictions'] - start_stats['performance']['memory_evictions']
        gc_runs = end_stats['performance']['gc_runs'] - start_stats['performance']['gc_runs']
        
        result = VarInputDataBenchmarkResult(
            test_name="Basic Operations",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            operations_count=iterations,
            operations_per_second=iterations / max(duration, 0.001),
            cache_hit_rate=cache_hit_rate,
            evictions_count=evictions,
            gc_runs=gc_runs,
            thread_count=1,
            success_rate=(success_count / iterations) * 100,
            average_response_time=np.mean(response_times) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            system_stats=end_stats
        )
        
        self.results.append(result)
        logger.info(f"Basic operations benchmark completed: {result.operations_per_second:.1f} ops/sec")
        return result
    
    def benchmark_concurrent_access(self,
                                  thread_count: int = 10,
                                  operations_per_thread: int = 100,
                                  symbols: List[str] = None) -> VarInputDataBenchmarkResult:
        """
        Benchmark concurrent access performance and thread safety
        
        Args:
            thread_count: Number of concurrent threads
            operations_per_thread: Operations each thread performs
            symbols: List of symbols to test
        """
        if symbols is None:
            symbols = ['AAPL', 'AMZN', 'GOOGL', 'META', 'NFLX']
        
        logger.info(f"Benchmarking concurrent access: {thread_count} threads, {operations_per_thread} ops/thread")
        
        # Clear cache
        clear_cache()
        gc.collect()
        
        var_data = get_var_input_data()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        start_stats = var_data.get_statistics()
        
        response_times = []
        success_count = [0]  # Use list for thread-safe access
        lock = threading.Lock()
        
        def worker_thread(thread_id: int):
            """Worker thread function"""
            local_success = 0
            local_times = []
            
            for i in range(operations_per_thread):
                symbol = symbols[i % len(symbols)]
                variable = f"test_var_{thread_id}_{i}"
                value = np.random.uniform(1000, 50000)
                
                try:
                    # Set operation
                    operation_start = time.time()
                    success = var_data.set_variable(
                        symbol=symbol,
                        variable_name=variable,
                        value=value,
                        period="2023",
                        source=f"thread_{thread_id}"
                    )
                    operation_end = time.time()
                    
                    if success:
                        local_success += 1
                    local_times.append(operation_end - operation_start)
                    
                    # Get operation
                    operation_start = time.time()
                    result = var_data.get_variable(symbol, variable, "2023")
                    operation_end = time.time()
                    
                    if result is not None:
                        local_success += 1
                    local_times.append(operation_end - operation_start)
                    
                except Exception as e:
                    logger.error(f"Error in worker thread {thread_id}: {e}")
            
            # Thread-safe update of global counters
            with lock:
                success_count[0] += local_success
                response_times.extend(local_times)
        
        # Run concurrent threads
        threads = []
        for i in range(thread_count):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        end_stats = var_data.get_statistics()
        duration = (end_time - start_time).total_seconds()
        
        total_operations = thread_count * operations_per_thread * 2  # set + get operations
        
        # Calculate metrics
        cache_hit_rate = end_stats['cache_hit_rate']
        evictions = end_stats['performance']['memory_evictions'] - start_stats['performance']['memory_evictions']
        gc_runs = end_stats['performance']['gc_runs'] - start_stats['performance']['gc_runs']
        
        result = VarInputDataBenchmarkResult(
            test_name="Concurrent Access",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            operations_count=total_operations,
            operations_per_second=total_operations / max(duration, 0.001),
            cache_hit_rate=cache_hit_rate,
            evictions_count=evictions,
            gc_runs=gc_runs,
            thread_count=thread_count,
            success_rate=(success_count[0] / total_operations) * 100,
            average_response_time=np.mean(response_times) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            system_stats=end_stats
        )
        
        self.results.append(result)
        logger.info(f"Concurrent access benchmark completed: {result.operations_per_second:.1f} ops/sec")
        return result
    
    def benchmark_memory_optimization(self,
                                    data_volume: int = 10000,
                                    memory_threshold_mb: int = 256) -> VarInputDataBenchmarkResult:
        """
        Benchmark memory optimization and lazy loading effectiveness
        
        Args:
            data_volume: Number of data points to create
            memory_threshold_mb: Memory threshold for lazy loading
        """
        logger.info(f"Benchmarking memory optimization with {data_volume} data points")
        
        # Clear cache first
        clear_cache()
        gc.collect()
        
        # Get existing instance (singleton pattern)
        var_data = get_var_input_data()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        start_stats = var_data.get_statistics()
        
        symbols = [f"TEST{i:04d}" for i in range(100)]  # 100 test symbols
        variables = ['revenue', 'net_income', 'cash_flow', 'assets', 'debt']
        periods = [str(year) for year in range(2014, 2024)]  # 10 years
        
        response_times = []
        success_count = 0
        memory_samples = []
        
        try:
            # Fill system with data
            for i in range(data_volume):
                symbol = symbols[i % len(symbols)]
                variable = variables[i % len(variables)]
                period = periods[i % len(periods)]
                value = np.random.uniform(1000000, 100000000)  # Large financial values
                
                operation_start = time.time()
                success = var_data.set_variable(
                    symbol=symbol,
                    variable_name=variable,
                    value=value,
                    period=period,
                    source="memory_test"
                )
                operation_end = time.time()
                
                if success:
                    success_count += 1
                response_times.append(operation_end - operation_start)
                
                # Sample memory usage periodically
                if i % 100 == 0:
                    memory_samples.append(self._get_memory_usage())
        
        except Exception as e:
            logger.error(f"Error during memory optimization benchmark: {e}")
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        end_stats = var_data.get_statistics()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate peak memory
        peak_memory = max(memory_samples + [start_memory, end_memory])
        
        # Calculate metrics
        cache_hit_rate = end_stats['cache_hit_rate']
        evictions = end_stats['performance']['memory_evictions'] - start_stats['performance']['memory_evictions']
        gc_runs = end_stats['performance']['gc_runs'] - start_stats['performance']['gc_runs']
        
        result = VarInputDataBenchmarkResult(
            test_name="Memory Optimization",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=peak_memory,
            operations_count=data_volume,
            operations_per_second=data_volume / max(duration, 0.001),
            cache_hit_rate=cache_hit_rate,
            evictions_count=evictions,
            gc_runs=gc_runs,
            thread_count=1,
            success_rate=(success_count / data_volume) * 100,
            average_response_time=np.mean(response_times) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            system_stats=end_stats
        )
        
        self.results.append(result)
        logger.info(f"Memory optimization benchmark completed: peak {peak_memory:.1f}MB, {evictions} evictions")
        return result
    
    def benchmark_historical_data_performance(self,
                                            symbols_count: int = 50,
                                            years_of_data: int = 15) -> VarInputDataBenchmarkResult:
        """
        Benchmark historical data management performance
        
        Args:
            symbols_count: Number of symbols to test
            years_of_data: Years of historical data per symbol
        """
        logger.info(f"Benchmarking historical data: {symbols_count} symbols, {years_of_data} years")
        
        # Clear cache
        clear_cache()
        gc.collect()
        
        var_data = get_var_input_data()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        start_stats = var_data.get_statistics()
        
        symbols = [f"HIST{i:03d}" for i in range(symbols_count)]
        variables = ['revenue', 'net_income', 'free_cash_flow']
        
        response_times = []
        success_count = 0
        total_operations = symbols_count * len(variables) * years_of_data
        
        try:
            # Create historical data
            for symbol in symbols:
                for variable in variables:
                    for year in range(2024 - years_of_data, 2024):
                        value = np.random.uniform(1000000, 50000000)
                        
                        operation_start = time.time()
                        success = var_data.set_variable(
                            symbol=symbol,
                            variable_name=variable,
                            value=value,
                            period=str(year),
                            source="historical_test"
                        )
                        operation_end = time.time()
                        
                        if success:
                            success_count += 1
                        response_times.append(operation_end - operation_start)
            
            # Test historical data retrieval
            retrieval_times = []
            for symbol in symbols[:10]:  # Test subset for retrieval
                for variable in variables:
                    operation_start = time.time()
                    historical = var_data.get_historical_data(symbol, variable, years=years_of_data)
                    operation_end = time.time()
                    
                    retrieval_times.append(operation_end - operation_start)
                    if historical:
                        success_count += len(historical)
        
        except Exception as e:
            logger.error(f"Error during historical data benchmark: {e}")
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        end_stats = var_data.get_statistics()
        duration = (end_time - start_time).total_seconds()
        
        # Combine all response times
        all_response_times = response_times + (retrieval_times or [])
        
        # Calculate metrics
        cache_hit_rate = end_stats['cache_hit_rate']
        evictions = end_stats['performance']['memory_evictions'] - start_stats['performance']['memory_evictions']
        gc_runs = end_stats['performance']['gc_runs'] - start_stats['performance']['gc_runs']
        
        result = VarInputDataBenchmarkResult(
            test_name="Historical Data Management",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            operations_count=total_operations,
            operations_per_second=total_operations / max(duration, 0.001),
            cache_hit_rate=cache_hit_rate,
            evictions_count=evictions,
            gc_runs=gc_runs,
            thread_count=1,
            success_rate=(success_count / total_operations) * 100,
            average_response_time=np.mean(all_response_times) if all_response_times else 0,
            p95_response_time=np.percentile(all_response_times, 95) if all_response_times else 0,
            system_stats=end_stats
        )
        
        self.results.append(result)
        logger.info(f"Historical data benchmark completed: {result.operations_per_second:.1f} ops/sec")
        return result
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive performance analysis report"""
        if not self.results:
            logger.warning("No benchmark results to report")
            return ""
        
        # Generate detailed analysis
        report = f"""
# VarInputData Performance Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

Total benchmarks executed: {len(self.results)}
Overall system performance analysis of VarInputData singleton system with focus on:
- Memory optimization effectiveness
- Thread safety overhead
- Lazy loading performance 
- Historical data management efficiency

## System Configuration
- Memory threshold: {self.results[0].system_stats.get('memory', {}).get('threshold_mb', 'N/A')} MB
- Eviction policy: {self.results[0].system_stats.get('memory', {}).get('eviction_policy', 'N/A')}
- Lazy loading: {self.results[0].system_stats.get('memory', {}).get('lazy_loading_active', 'N/A')}

## Benchmark Results Detail

"""
        
        for result in self.results:
            efficiency_score = self._calculate_efficiency_score(result)
            
            report += f"""
### {result.test_name}
**Performance Metrics:**
- Duration: {result.duration_seconds:.2f}s
- Operations/second: {result.operations_per_second:.1f}
- Success rate: {result.success_rate:.1f}%
- Average response time: {result.average_response_time*1000:.2f}ms
- P95 response time: {result.p95_response_time*1000:.2f}ms

**Memory Management:**
- Memory delta: {result.memory_delta_mb:+.1f} MB
- Peak memory: {result.memory_peak_mb:.1f} MB  
- Memory evictions: {result.evictions_count}
- GC runs: {result.gc_runs}

**Cache Performance:**
- Cache hit rate: {result.cache_hit_rate:.1f}%

**Thread Safety:** 
- Thread count: {result.thread_count}
- Concurrent efficiency: {"High" if result.thread_count > 1 and result.success_rate > 95 else "Standard"}

**Overall Efficiency Score: {efficiency_score:.1f}/100**

"""
        
        # Add performance comparison
        report += self._generate_performance_comparison()
        
        # Add recommendations
        report += self._generate_optimization_recommendations()
        
        # Save report
        report_file = self.output_dir / f"varinputdata_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"VarInputData performance report saved: {report_file}")
        return report
    
    def _calculate_efficiency_score(self, result: VarInputDataBenchmarkResult) -> float:
        """Calculate overall efficiency score (0-100)"""
        # Base score from success rate
        score = result.success_rate * 0.3
        
        # Performance score (ops/sec, normalized to 0-30)
        perf_score = min(result.operations_per_second / 100, 30)
        score += perf_score
        
        # Memory efficiency (less memory growth is better, 0-20 points)
        if result.memory_delta_mb <= 0:
            memory_score = 20
        elif result.memory_delta_mb < 50:
            memory_score = 20 - (result.memory_delta_mb / 2.5)
        else:
            memory_score = 0
        score += memory_score
        
        # Cache efficiency (0-20 points)
        cache_score = result.cache_hit_rate * 0.2
        score += cache_score
        
        return min(score, 100)
    
    def _generate_performance_comparison(self) -> str:
        """Generate performance comparison section"""
        if len(self.results) < 2:
            return "\n## Performance Comparison\nInsufficient data for comparison.\n"
        
        # Find best and worst performers
        best_ops = max(self.results, key=lambda r: r.operations_per_second)
        worst_memory = max(self.results, key=lambda r: r.memory_delta_mb)
        best_cache = max(self.results, key=lambda r: r.cache_hit_rate)
        
        return f"""
## Performance Comparison

**Highest Throughput:** {best_ops.test_name}
- {best_ops.operations_per_second:.1f} operations/second
- Response time: {best_ops.average_response_time*1000:.2f}ms avg

**Highest Memory Usage:** {worst_memory.test_name}  
- Memory delta: +{worst_memory.memory_delta_mb:.1f} MB
- Peak memory: {worst_memory.memory_peak_mb:.1f} MB

**Best Cache Performance:** {best_cache.test_name}
- Cache hit rate: {best_cache.cache_hit_rate:.1f}%
- Evictions: {best_cache.evictions_count}

"""
    
    def _generate_optimization_recommendations(self) -> str:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Analyze results for recommendations
        for result in self.results:
            if result.memory_delta_mb > 100:
                recommendations.append(f"- High memory usage in {result.test_name}: Consider reducing cache size or increasing eviction frequency")
            
            if result.cache_hit_rate < 50:
                recommendations.append(f"- Low cache hit rate in {result.test_name}: Review caching strategy and data access patterns")
            
            if result.operations_per_second < 100:
                recommendations.append(f"- Low throughput in {result.test_name}: Consider optimizing locking mechanisms or data structures")
            
            if result.evictions_count > result.operations_count * 0.1:
                recommendations.append(f"- High eviction rate in {result.test_name}: Consider increasing memory limits or optimizing data retention")
        
        if not recommendations:
            recommendations.append("- System performance is within acceptable parameters")
            recommendations.append("- Consider monitoring long-term memory trends")
            recommendations.append("- Evaluate concurrent access patterns under production load")
        
        return f"""
## Optimization Recommendations

{chr(10).join(recommendations)}

### Priority Actions:
1. **Memory Management**: Monitor eviction patterns and adjust thresholds
2. **Cache Optimization**: Analyze access patterns to improve hit rates  
3. **Concurrency**: Profile thread contention in high-load scenarios
4. **Data Structures**: Consider using more memory-efficient storage for large datasets

"""
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0


def run_comprehensive_varinputdata_benchmark(output_dir: str = "performance_reports") -> List[VarInputDataBenchmarkResult]:
    """
    Run comprehensive VarInputData performance benchmark suite
    
    Args:
        output_dir: Output directory for reports
        
    Returns:
        List of benchmark results
    """
    benchmark = VarInputDataPerformanceBenchmark(output_dir)
    
    logger.info("Starting comprehensive VarInputData performance analysis...")
    
    try:
        # Run all benchmark tests
        results = []
        
        # Basic operations performance
        results.append(benchmark.benchmark_basic_operations(iterations=2000))
        
        # Concurrent access performance
        results.append(benchmark.benchmark_concurrent_access(thread_count=8, operations_per_thread=200))
        
        # Memory optimization effectiveness
        results.append(benchmark.benchmark_memory_optimization(data_volume=5000))
        
        # Historical data management
        results.append(benchmark.benchmark_historical_data_performance(symbols_count=30, years_of_data=10))
        
        # Generate comprehensive report
        report = benchmark.generate_comprehensive_report()
        print(f"\n{report}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error running comprehensive benchmark: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive benchmark
    results = run_comprehensive_varinputdata_benchmark()
    
    print(f"\nBenchmark completed successfully!")
    print(f"Results summary:")
    for result in results:
        print(f"  {result.test_name}: {result.operations_per_second:.1f} ops/sec, {result.success_rate:.1f}% success")