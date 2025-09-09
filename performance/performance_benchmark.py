"""
Performance Benchmarking and Monitoring Tools

This module provides comprehensive performance benchmarking, monitoring, and
reporting tools for watch list operations, especially focused on large-scale
concurrent API operations.

Features:
- Comprehensive benchmarking of watch list operations
- Memory usage monitoring and leak detection
- API call performance analysis
- Concurrent vs sequential performance comparison
- Performance regression detection
- Automated performance reports
"""

import time
import psutil
import gc
import threading
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Import components to benchmark
from .concurrent_watch_list_optimizer import ConcurrentWatchListOptimizer, create_optimized_watch_list_manager
from core.data_processing.managers.watch_list_manager import WatchListManager

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_start_mb: float
    memory_end_mb: float
    memory_peak_mb: float
    cpu_percent: float
    success_count: int
    failure_count: int
    total_operations: int
    operations_per_second: float
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_delta_mb(self) -> float:
        """Memory change during benchmark"""
        return self.memory_end_mb - self.memory_start_mb
    
    @property
    def success_rate(self) -> float:
        """Success rate percentage"""
        if self.total_operations > 0:
            return (self.success_count / self.total_operations) * 100
        return 0.0


@dataclass
class PerformanceProfile:
    """Performance profile for different watch list sizes"""
    list_size: int
    concurrent_result: Optional[BenchmarkResult] = None
    sequential_result: Optional[BenchmarkResult] = None
    paginated_result: Optional[BenchmarkResult] = None
    
    @property
    def concurrent_speedup(self) -> Optional[float]:
        """Speed improvement of concurrent vs sequential"""
        if self.concurrent_result and self.sequential_result:
            if self.concurrent_result.duration_seconds > 0:
                return self.sequential_result.duration_seconds / self.concurrent_result.duration_seconds
        return None


class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking and monitoring system
    """
    
    def __init__(self, output_dir: str = "performance_reports"):
        """
        Initialize benchmark system
        
        Args:
            output_dir: Directory for performance reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitoring data
        self.memory_samples: List[Tuple[datetime, float]] = []
        self.cpu_samples: List[Tuple[datetime, float]] = []
        self.response_times: List[float] = []
        
        # Benchmark results
        self.benchmark_results: List[BenchmarkResult] = []
        self.performance_profiles: Dict[int, PerformanceProfile] = {}
        
        # System info
        self.system_info = self._get_system_info()
        
        logger.info(f"Performance benchmarking initialized. Reports will be saved to: {self.output_dir}")
    
    def benchmark_watch_list_performance(self, 
                                       watch_list_manager: WatchListManager,
                                       watch_list_name: str,
                                       test_concurrent: bool = True,
                                       test_sequential: bool = True,
                                       test_paginated: bool = True,
                                       force_refresh: bool = True) -> PerformanceProfile:
        """
        Comprehensive benchmark of watch list performance across different loading strategies
        
        Args:
            watch_list_manager: Watch list manager instance
            watch_list_name: Name of watch list to benchmark
            test_concurrent: Test concurrent loading
            test_sequential: Test sequential loading  
            test_paginated: Test paginated loading
            force_refresh: Force API calls (disable caching)
            
        Returns:
            PerformanceProfile: Benchmark results for all tested strategies
        """
        logger.info(f"Starting comprehensive benchmark for watch list: {watch_list_name}")
        
        # Get watch list size
        watch_list = watch_list_manager.get_watch_list(watch_list_name)
        if not watch_list or not watch_list.get('stocks'):
            raise ValueError(f"Watch list '{watch_list_name}' not found or empty")
        
        list_size = len(watch_list['stocks'])
        logger.info(f"Benchmarking watch list with {list_size} stocks")
        
        profile = PerformanceProfile(list_size=list_size)
        
        # Test concurrent loading
        if test_concurrent:
            logger.info("Benchmarking concurrent loading...")
            profile.concurrent_result = self._benchmark_concurrent_loading(
                watch_list_manager, watch_list_name, force_refresh
            )
            
        # Test sequential loading
        if test_sequential:
            logger.info("Benchmarking sequential loading...")
            profile.sequential_result = self._benchmark_sequential_loading(
                watch_list_manager, watch_list_name, force_refresh
            )
        
        # Test paginated loading
        if test_paginated and list_size > 20:
            logger.info("Benchmarking paginated loading...")
            profile.paginated_result = self._benchmark_paginated_loading(
                watch_list_manager, watch_list_name
            )
        
        # Store results
        self.performance_profiles[list_size] = profile
        
        # Generate comparison report
        self._generate_profile_report(profile, watch_list_name)
        
        logger.info(f"Benchmark completed for {watch_list_name}")
        return profile
    
    def _benchmark_concurrent_loading(self, 
                                    watch_list_manager: WatchListManager,
                                    watch_list_name: str,
                                    force_refresh: bool) -> BenchmarkResult:
        """Benchmark concurrent loading strategy"""
        
        # Clear cache to ensure fair test
        gc.collect()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        
        # Create optimizer and run test
        optimizer = create_optimized_watch_list_manager(watch_list_manager)
        
        # Progress tracking
        operations_completed = 0
        operation_times = []
        
        def progress_callback(completed: int, total: int):
            nonlocal operations_completed
            operations_completed = completed
        
        try:
            # Execute concurrent loading
            operation_start = time.time()
            result = optimizer.get_watch_list_with_concurrent_prices(
                watch_list_name=watch_list_name,
                force_refresh=force_refresh,
                progress_callback=progress_callback
            )
            operation_end = time.time()
            
            # Record results
            success = result is not None and result.get('stocks')
            if success:
                success_count = len([s for s in result['stocks'] if s.get('current_market_price')])
                failure_count = len([s for s in result['stocks'] if not s.get('current_market_price')])
                total_ops = len(result['stocks'])
                
                # Extract response times from performance metadata
                if 'performance_metadata' in result:
                    operation_times = [operation_end - operation_start]
            else:
                success_count = 0
                failure_count = operations_completed
                total_ops = operations_completed
                
        except Exception as e:
            logger.error(f"Error during concurrent benchmark: {e}")
            success_count = 0 
            failure_count = operations_completed or 1
            total_ops = failure_count
            operation_times = []
        
        finally:
            # Clean up
            optimizer.shutdown()
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        if operation_times:
            avg_response = np.mean(operation_times)
            median_response = np.median(operation_times)
            p95_response = np.percentile(operation_times, 95)
            p99_response = np.percentile(operation_times, 99)
        else:
            avg_response = median_response = p95_response = p99_response = duration
        
        benchmark_result = BenchmarkResult(
            test_name="Concurrent Loading",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            cpu_percent=self._get_avg_cpu_usage(),
            success_count=success_count,
            failure_count=failure_count,
            total_operations=total_ops,
            operations_per_second=total_ops / max(duration, 0.001),
            average_response_time=avg_response,
            median_response_time=median_response,
            p95_response_time=p95_response,
            p99_response_time=p99_response,
            error_rate=(failure_count / max(total_ops, 1)) * 100,
            metadata={
                'force_refresh': force_refresh,
                'strategy': 'concurrent',
                'watch_list_name': watch_list_name
            }
        )
        
        self.benchmark_results.append(benchmark_result)
        return benchmark_result
    
    def _benchmark_sequential_loading(self,
                                    watch_list_manager: WatchListManager,
                                    watch_list_name: str,
                                    force_refresh: bool) -> BenchmarkResult:
        """Benchmark sequential (standard) loading strategy"""
        
        # Clear cache
        gc.collect()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        
        try:
            # Execute sequential loading
            result = watch_list_manager.get_watch_list_with_current_prices(
                watch_list_name, force_refresh
            )
            
            # Record results
            success = result is not None and result.get('stocks')
            if success:
                success_count = len([s for s in result['stocks'] if s.get('current_market_price')])
                failure_count = len([s for s in result['stocks'] if not s.get('current_market_price')])
                total_ops = len(result['stocks'])
            else:
                success_count = 0
                failure_count = 1
                total_ops = 1
                
        except Exception as e:
            logger.error(f"Error during sequential benchmark: {e}")
            success_count = 0
            failure_count = 1
            total_ops = 1
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        duration = (end_time - start_time).total_seconds()
        
        benchmark_result = BenchmarkResult(
            test_name="Sequential Loading", 
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            cpu_percent=self._get_avg_cpu_usage(),
            success_count=success_count,
            failure_count=failure_count,
            total_operations=total_ops,
            operations_per_second=total_ops / max(duration, 0.001),
            average_response_time=duration / max(total_ops, 1),
            median_response_time=duration / max(total_ops, 1),
            p95_response_time=duration / max(total_ops, 1),
            p99_response_time=duration / max(total_ops, 1),
            error_rate=(failure_count / max(total_ops, 1)) * 100,
            metadata={
                'force_refresh': force_refresh,
                'strategy': 'sequential',
                'watch_list_name': watch_list_name
            }
        )
        
        self.benchmark_results.append(benchmark_result)
        return benchmark_result
    
    def _benchmark_paginated_loading(self,
                                   watch_list_manager: WatchListManager,
                                   watch_list_name: str) -> BenchmarkResult:
        """Benchmark paginated loading strategy"""
        
        # Clear cache
        gc.collect()
        
        # Start monitoring
        start_time = datetime.now()
        start_memory = self._get_memory_usage()
        
        try:
            # Create optimizer for paginated loading
            optimizer = create_optimized_watch_list_manager(watch_list_manager)
            
            # Load first page (typical user behavior)
            result = optimizer.get_paginated_watch_list(
                watch_list_name=watch_list_name,
                page=1,
                page_size=25
            )
            
            # Record results
            success = result is not None and result.get('stocks')
            if success:
                success_count = len([s for s in result['stocks'] if s.get('current_market_price')])
                failure_count = len([s for s in result['stocks'] if not s.get('current_market_price')])
                total_ops = len(result['stocks'])
            else:
                success_count = 0
                failure_count = 1
                total_ops = 1
            
            # Clean up
            optimizer.shutdown()
            
        except Exception as e:
            logger.error(f"Error during paginated benchmark: {e}")
            success_count = 0
            failure_count = 1
            total_ops = 1
        
        # End monitoring
        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        duration = (end_time - start_time).total_seconds()
        
        benchmark_result = BenchmarkResult(
            test_name="Paginated Loading",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start_mb=start_memory,
            memory_end_mb=end_memory,
            memory_peak_mb=max(end_memory, start_memory),
            cpu_percent=self._get_avg_cpu_usage(),
            success_count=success_count,
            failure_count=failure_count,
            total_operations=total_ops,
            operations_per_second=total_ops / max(duration, 0.001),
            average_response_time=duration / max(total_ops, 1),
            median_response_time=duration / max(total_ops, 1),
            p95_response_time=duration / max(total_ops, 1),
            p99_response_time=duration / max(total_ops, 1),
            error_rate=(failure_count / max(total_ops, 1)) * 100,
            metadata={
                'strategy': 'paginated',
                'page_size': 25,
                'watch_list_name': watch_list_name
            }
        )
        
        self.benchmark_results.append(benchmark_result)
        return benchmark_result
    
    def benchmark_large_watch_list_scaling(self,
                                         watch_list_manager: WatchListManager,
                                         test_sizes: List[int] = [10, 25, 50, 100, 200]) -> Dict[int, PerformanceProfile]:
        """
        Benchmark performance scaling with different watch list sizes
        
        Args:
            watch_list_manager: Watch list manager instance
            test_sizes: List of sizes to test
            
        Returns:
            Dict: Mapping of size to performance profile
        """
        logger.info(f"Starting scaling benchmark with sizes: {test_sizes}")
        
        scaling_results = {}
        
        for size in test_sizes:
            logger.info(f"Creating test watch list with {size} stocks...")
            
            # Create synthetic test watch list
            test_list_name = f"benchmark_test_{size}_stocks"
            
            try:
                # Create test list (you would need to implement this)
                success = self._create_test_watch_list(watch_list_manager, test_list_name, size)
                
                if success:
                    # Benchmark this size
                    profile = self.benchmark_watch_list_performance(
                        watch_list_manager=watch_list_manager,
                        watch_list_name=test_list_name,
                        force_refresh=True
                    )
                    
                    scaling_results[size] = profile
                    
                    # Clean up test list
                    watch_list_manager.delete_watch_list(test_list_name)
                else:
                    logger.warning(f"Failed to create test list with {size} stocks")
                    
            except Exception as e:
                logger.error(f"Error benchmarking size {size}: {e}")
        
        # Generate scaling report
        self._generate_scaling_report(scaling_results)
        
        return scaling_results
    
    def _create_test_watch_list(self, watch_list_manager: WatchListManager, name: str, size: int) -> bool:
        """
        Create a synthetic test watch list with the specified number of stocks
        Note: This is a placeholder - you would implement this based on available test data
        """
        try:
            # Create the watch list
            success = watch_list_manager.create_watch_list(
                name, f"Synthetic test list with {size} stocks for benchmarking"
            )
            
            if success:
                # Add synthetic stock entries (you would customize this based on your needs)
                test_tickers = [f"TEST{i:03d}" for i in range(size)]
                
                for ticker in test_tickers:
                    analysis_data = {
                        'ticker': ticker,
                        'company_name': f"Test Company {ticker}",
                        'current_price': 100.0,
                        'fair_value': 120.0,
                        'analysis_type': 'DCF',
                        'fcf_type': 'FCFE'
                    }
                    watch_list_manager.add_analysis_to_watch_list(name, analysis_data)
                
                return True
                
        except Exception as e:
            logger.error(f"Error creating test watch list: {e}")
            
        return False
    
    def _generate_profile_report(self, profile: PerformanceProfile, watch_list_name: str):
        """Generate detailed report for a performance profile"""
        
        report_data = {
            'watch_list_name': watch_list_name,
            'list_size': profile.list_size,
            'test_date': datetime.now().isoformat(),
            'system_info': self.system_info,
            'results': {}
        }
        
        # Add results for each tested strategy
        if profile.concurrent_result:
            report_data['results']['concurrent'] = asdict(profile.concurrent_result)
            
        if profile.sequential_result:
            report_data['results']['sequential'] = asdict(profile.sequential_result)
            
        if profile.paginated_result:
            report_data['results']['paginated'] = asdict(profile.paginated_result)
        
        # Add comparison metrics
        if profile.concurrent_speedup:
            report_data['concurrent_speedup'] = profile.concurrent_speedup
        
        # Save report
        report_file = self.output_dir / f"performance_profile_{watch_list_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Performance profile report saved: {report_file}")
    
    def _generate_scaling_report(self, scaling_results: Dict[int, PerformanceProfile]):
        """Generate scaling performance report"""
        
        report_data = {
            'test_date': datetime.now().isoformat(),
            'system_info': self.system_info,
            'scaling_results': {}
        }
        
        for size, profile in scaling_results.items():
            report_data['scaling_results'][size] = {
                'list_size': size,
                'concurrent_duration': profile.concurrent_result.duration_seconds if profile.concurrent_result else None,
                'sequential_duration': profile.sequential_result.duration_seconds if profile.sequential_result else None,
                'speedup': profile.concurrent_speedup,
                'concurrent_ops_per_sec': profile.concurrent_result.operations_per_second if profile.concurrent_result else None,
                'sequential_ops_per_sec': profile.sequential_result.operations_per_second if profile.sequential_result else None
            }
        
        # Save report
        report_file = self.output_dir / f"scaling_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Scaling report saved: {report_file}")
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive performance report"""
        
        if not self.benchmark_results:
            logger.warning("No benchmark results to report")
            return ""
        
        # Create summary report
        report = f"""
# Performance Benchmark Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Information
- CPU: {self.system_info.get('cpu_count', 'Unknown')} cores
- Memory: {self.system_info.get('memory_gb', 'Unknown')} GB
- Python Version: {self.system_info.get('python_version', 'Unknown')}

## Benchmark Results Summary
Total Tests Run: {len(self.benchmark_results)}

"""
        
        # Add individual results
        for result in self.benchmark_results:
            report += f"""
### {result.test_name}
- Duration: {result.duration_seconds:.2f}s
- Success Rate: {result.success_rate:.1f}%
- Operations/sec: {result.operations_per_second:.1f}
- Memory Delta: {result.memory_delta_mb:.1f} MB
- Avg Response Time: {result.average_response_time:.3f}s
- P95 Response Time: {result.p95_response_time:.3f}s

"""
        
        # Save report
        report_file = self.output_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Comprehensive report saved: {report_file}")
        return report
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_avg_cpu_usage(self) -> float:
        """Get average CPU usage"""
        try:
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / 1024**3,
                'python_version': f"{psutil.PYTHON_VERSION}",
                'platform': psutil.PLATFORM
            }
        except:
            return {}


def run_performance_benchmark(watch_list_manager: WatchListManager, 
                            watch_list_name: str,
                            output_dir: str = "performance_reports") -> PerformanceProfile:
    """
    Convenience function to run a comprehensive performance benchmark
    
    Args:
        watch_list_manager: Watch list manager instance
        watch_list_name: Name of watch list to benchmark
        output_dir: Output directory for reports
        
    Returns:
        PerformanceProfile: Benchmark results
    """
    benchmark = PerformanceBenchmark(output_dir)
    
    try:
        profile = benchmark.benchmark_watch_list_performance(
            watch_list_manager=watch_list_manager,
            watch_list_name=watch_list_name
        )
        
        # Generate comprehensive report
        benchmark.generate_comprehensive_report()
        
        return profile
        
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        raise


def run_scaling_benchmark(watch_list_manager: WatchListManager,
                         test_sizes: List[int] = [10, 25, 50, 100],
                         output_dir: str = "performance_reports") -> Dict[int, PerformanceProfile]:
    """
    Convenience function to run scaling performance benchmark
    
    Args:
        watch_list_manager: Watch list manager instance  
        test_sizes: List of sizes to test
        output_dir: Output directory for reports
        
    Returns:
        Dict: Scaling results mapping size to performance profile
    """
    benchmark = PerformanceBenchmark(output_dir)
    
    try:
        results = benchmark.benchmark_large_watch_list_scaling(
            watch_list_manager=watch_list_manager,
            test_sizes=test_sizes
        )
        
        # Generate comprehensive report
        benchmark.generate_comprehensive_report()
        
        return results
        
    except Exception as e:
        logger.error(f"Error running scaling benchmark: {e}")
        raise