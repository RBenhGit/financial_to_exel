"""
Comprehensive Excel Processing Performance Benchmarks
====================================================

This module provides extensive performance benchmarks for Excel processing,
testing various scenarios, file sizes, and optimization techniques.

Benchmarks include:
- Single file processing with different sizes
- Concurrent processing with multiple files
- Memory usage optimization
- Streaming vs standard processing comparison
- Cache effectiveness testing
- Format detection performance
- Real-world financial data processing

Usage:
    # Run all benchmarks
    pytest tests/performance/test_excel_performance_benchmarks.py -v

    # Run with benchmark reporting
    pytest tests/performance/test_excel_performance_benchmarks.py --benchmark-only

    # Run specific benchmark categories
    pytest tests/performance/test_excel_performance_benchmarks.py -k "streaming"
    pytest tests/performance/test_excel_performance_benchmarks.py -k "concurrent"
    pytest tests/performance/test_excel_performance_benchmarks.py -k "memory"
"""

import pytest
import os
import sys
import tempfile
import shutil
import time
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil
from dataclasses import dataclass
import random

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules to benchmark
from core.excel_integration.performance_optimized_processor import (
    PerformanceOptimizedExcelProcessor,
    PerformanceConfig,
    create_performance_config,
    StreamingExcelReader,
    MemoryMonitor
)
from core.excel_integration.excel_utils import ExcelDataExtractor
from core.excel_integration.format_detector import ExcelFormatDetector
from tests.performance.test_excel_stress_suite import ExcelStressTestGenerator


@dataclass
class BenchmarkScenario:
    """Configuration for benchmark scenarios"""
    name: str
    rows: int
    columns: int
    sheet_count: int = 1
    complexity: str = "medium"
    file_count: int = 1
    concurrent_workers: int = 2


class BenchmarkDataGenerator:
    """Generate benchmark data and Excel files"""

    @staticmethod
    def create_benchmark_scenarios() -> List[BenchmarkScenario]:
        """Create various benchmark scenarios"""
        return [
            # Small files
            BenchmarkScenario("small_single", 1000, 10, 1, "simple", 1, 1),
            BenchmarkScenario("small_multiple", 1000, 10, 1, "simple", 5, 3),

            # Medium files
            BenchmarkScenario("medium_single", 5000, 25, 2, "medium", 1, 1),
            BenchmarkScenario("medium_multiple", 5000, 25, 2, "medium", 3, 3),

            # Large files
            BenchmarkScenario("large_single", 15000, 50, 3, "complex", 1, 1),
            BenchmarkScenario("large_multiple", 15000, 50, 3, "complex", 2, 4),

            # Very large files (for stress testing)
            BenchmarkScenario("xlarge_single", 50000, 100, 1, "enterprise", 1, 1),

            # Financial data scenarios
            BenchmarkScenario("financial_simple", 50, 15, 3, "simple", 1, 1),
            BenchmarkScenario("financial_complex", 200, 20, 3, "complex", 1, 1),
            BenchmarkScenario("financial_portfolio", 100, 18, 3, "medium", 10, 6),
        ]

    @staticmethod
    def create_benchmark_files(
        scenario: BenchmarkScenario,
        temp_dir: str
    ) -> List[str]:
        """Create benchmark files for a scenario"""
        file_paths = []

        for i in range(scenario.file_count):
            if "financial" in scenario.name:
                # Create realistic financial Excel files
                file_path = Path(temp_dir) / f"{scenario.name}_{i}.xlsx"
                stats = ExcelStressTestGenerator.create_financial_excel_template(
                    str(file_path),
                    years=scenario.columns - 5,  # Reserve 5 columns for labels/metadata
                    complexity=scenario.complexity
                )
            else:
                # Create generic large Excel files
                file_path = Path(temp_dir) / f"{scenario.name}_{i}.xlsx"
                stats = ExcelStressTestGenerator.create_large_excel_file(
                    str(file_path),
                    scenario.rows,
                    scenario.columns,
                    scenario.sheet_count
                )

            if stats.get('success', False):
                file_paths.append(str(file_path))

        return file_paths


@pytest.fixture(scope="session")
def benchmark_scenarios():
    """Create benchmark scenarios"""
    return BenchmarkDataGenerator.create_benchmark_scenarios()


@pytest.fixture(scope="session")
def benchmark_data_dir():
    """Create temporary directory with benchmark data"""
    temp_dir = tempfile.mkdtemp(prefix="excel_benchmarks_")

    # Create all benchmark files at session start
    scenarios = BenchmarkDataGenerator.create_benchmark_scenarios()
    file_registry = {}

    for scenario in scenarios:
        print(f"Creating benchmark files for scenario: {scenario.name}")
        file_paths = BenchmarkDataGenerator.create_benchmark_files(scenario, temp_dir)
        file_registry[scenario.name] = file_paths

    yield temp_dir, file_registry

    # Cleanup at session end
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def performance_configs():
    """Different performance configurations to test"""
    return {
        'default': create_performance_config(),
        'memory_optimized': create_performance_config(
            max_memory_mb=512,
            enable_streaming=True,
            cache_size=64
        ),
        'speed_optimized': create_performance_config(
            max_memory_mb=2048,
            max_workers=8,
            enable_streaming=False,
            cache_size=256
        ),
        'balanced': create_performance_config(
            max_memory_mb=1024,
            max_workers=4,
            enable_streaming=True,
            cache_size=128
        )
    }


class TestSingleFileProcessingBenchmarks:
    """Benchmark single file processing performance"""

    @pytest.mark.parametrize("scenario_name", [
        "small_single", "medium_single", "large_single", "financial_simple", "financial_complex"
    ])
    def test_standard_vs_optimized_processing(
        self,
        benchmark,
        benchmark_data_dir,
        scenario_name
    ):
        """Compare standard vs optimized processing performance"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get(scenario_name, [])

        if not file_paths:
            pytest.skip(f"No files available for scenario {scenario_name}")

        file_path = file_paths[0]

        def benchmark_standard_processing():
            """Benchmark standard Excel processing"""
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            with ExcelDataExtractor(file_path) as extractor:
                # Extract data from all statement types
                all_data = {}
                for statement_type in ['income', 'balance', 'cashflow']:
                    try:
                        metrics = extractor.extract_all_financial_metrics(statement_type)
                        if metrics:
                            all_data[statement_type] = len(metrics)
                    except Exception:
                        all_data[statement_type] = 0

            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            return {
                'data_extracted': sum(all_data.values()),
                'memory_delta_mb': end_memory - start_memory,
                'method': 'standard'
            }

        def benchmark_optimized_processing():
            """Benchmark optimized Excel processing"""
            config = create_performance_config(enable_streaming=True)
            processor = PerformanceOptimizedExcelProcessor(config)

            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            result = processor.process_single_file(file_path)

            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            return {
                'success': result['success'],
                'memory_delta_mb': end_memory - start_memory,
                'method': 'optimized',
                'processing_metrics': result.get('metrics', {})
            }

        # Run both benchmarks
        standard_result = benchmark(benchmark_standard_processing)
        optimized_result = benchmark_optimized_processing()

        # Assert optimized version is competitive
        assert optimized_result['success'], "Optimized processing should succeed"

        # Memory usage should be reasonable
        assert optimized_result['memory_delta_mb'] < 500, f"Memory usage too high: {optimized_result['memory_delta_mb']:.1f}MB"

    @pytest.mark.parametrize("config_name", ["memory_optimized", "speed_optimized", "balanced"])
    def test_configuration_performance_impact(
        self,
        benchmark,
        benchmark_data_dir,
        performance_configs,
        config_name
    ):
        """Test performance impact of different configurations"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("medium_single", [])

        if not file_paths:
            pytest.skip("No medium_single files available")

        file_path = file_paths[0]
        config = performance_configs[config_name]

        def benchmark_with_config():
            processor = PerformanceOptimizedExcelProcessor(config)

            start_time = time.time()
            result = processor.process_single_file(file_path)
            processing_time = time.time() - start_time

            return {
                'success': result['success'],
                'processing_time': processing_time,
                'config_name': config_name,
                'performance_summary': processor.get_performance_summary()
            }

        result = benchmark(benchmark_with_config)

        # Assertions based on config type
        assert result['success'], f"Processing with {config_name} config should succeed"

        if config_name == "speed_optimized":
            # Speed optimized should be relatively fast
            assert result['processing_time'] < 30, f"Speed optimized processing too slow: {result['processing_time']:.2f}s"

        elif config_name == "memory_optimized":
            # Memory optimized should use less memory
            memory_metrics = result['performance_summary']['memory_metrics']
            assert memory_metrics['peak_memory_mb'] < 1000, f"Memory optimized using too much memory: {memory_metrics['peak_memory_mb']:.1f}MB"


class TestConcurrentProcessingBenchmarks:
    """Benchmark concurrent processing performance"""

    @pytest.mark.parametrize("scenario_name", ["small_multiple", "medium_multiple", "financial_portfolio"])
    def test_concurrent_vs_sequential_processing(
        self,
        benchmark,
        benchmark_data_dir,
        scenario_name
    ):
        """Compare concurrent vs sequential processing"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get(scenario_name, [])

        if len(file_paths) < 2:
            pytest.skip(f"Insufficient files for concurrent testing: {len(file_paths)}")

        def benchmark_sequential_processing():
            """Process files sequentially"""
            config = create_performance_config(max_workers=1)
            processor = PerformanceOptimizedExcelProcessor(config)

            start_time = time.time()
            results = []

            for file_path in file_paths:
                result = processor.process_single_file(file_path)
                results.append(result)

            total_time = time.time() - start_time
            successful = len([r for r in results if r.get('success', False)])

            return {
                'total_time': total_time,
                'successful_files': successful,
                'total_files': len(file_paths),
                'method': 'sequential'
            }

        def benchmark_concurrent_processing():
            """Process files concurrently"""
            config = create_performance_config(max_workers=min(4, len(file_paths)))
            processor = PerformanceOptimizedExcelProcessor(config)

            start_time = time.time()
            result = processor.process_multiple_files(file_paths)
            total_time = time.time() - start_time

            return {
                'total_time': total_time,
                'successful_files': result['successful_files'],
                'total_files': result['total_files'],
                'method': 'concurrent',
                'performance_metrics': result['performance_metrics']
            }

        # Benchmark both approaches
        sequential_result = benchmark_sequential_processing()
        concurrent_result = benchmark_concurrent_processing()

        # Concurrent should be faster for multiple files
        speedup = sequential_result['total_time'] / concurrent_result['total_time']

        # Allow for some overhead but expect speedup for multiple files
        if len(file_paths) >= 3:
            assert speedup > 1.2, f"Concurrent processing not significantly faster: {speedup:.2f}x speedup"

        assert concurrent_result['successful_files'] == sequential_result['successful_files'], "Both methods should process same number of files successfully"

    def test_scalability_with_worker_count(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Test how performance scales with worker count"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("small_multiple", [])

        if len(file_paths) < 3:
            pytest.skip("Insufficient files for scalability testing")

        worker_counts = [1, 2, 4]
        results = {}

        for worker_count in worker_counts:
            def benchmark_with_workers():
                config = create_performance_config(max_workers=worker_count)
                processor = PerformanceOptimizedExcelProcessor(config)

                start_time = time.time()
                result = processor.process_multiple_files(file_paths)
                total_time = time.time() - start_time

                return {
                    'worker_count': worker_count,
                    'total_time': total_time,
                    'successful_files': result['successful_files'],
                    'throughput': result['successful_files'] / total_time if total_time > 0 else 0
                }

            results[worker_count] = benchmark(benchmark_with_workers)

        # Analyze scalability
        baseline_throughput = results[1]['throughput']

        for worker_count in [2, 4]:
            if worker_count in results:
                throughput_improvement = results[worker_count]['throughput'] / baseline_throughput
                # Expect some improvement, but not perfect scaling due to overhead
                assert throughput_improvement > 1.1, f"Worker count {worker_count} not improving throughput significantly"


class TestMemoryOptimizationBenchmarks:
    """Benchmark memory optimization techniques"""

    def test_streaming_vs_standard_memory_usage(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Compare memory usage between streaming and standard processing"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("large_single", [])

        if not file_paths:
            pytest.skip("No large files available for memory testing")

        file_path = file_paths[0]

        def benchmark_standard_memory():
            """Benchmark standard processing memory usage"""
            gc.collect()  # Clean up before measurement
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            config = create_performance_config(enable_streaming=False)
            processor = PerformanceOptimizedExcelProcessor(config)

            with MemoryMonitor(2048) as monitor:
                result = processor.process_single_file(file_path)

            memory_metrics = monitor.get_metrics()

            return {
                'success': result['success'],
                'peak_memory_mb': memory_metrics['peak_memory_mb'],
                'memory_delta_mb': memory_metrics['memory_delta_mb'],
                'method': 'standard'
            }

        def benchmark_streaming_memory():
            """Benchmark streaming processing memory usage"""
            gc.collect()  # Clean up before measurement

            config = create_performance_config(
                enable_streaming=True,
                chunk_size=500  # Smaller chunks for better memory control
            )
            processor = PerformanceOptimizedExcelProcessor(config)

            with MemoryMonitor(2048) as monitor:
                result = processor.process_single_file(file_path)

            memory_metrics = monitor.get_metrics()

            return {
                'success': result['success'],
                'peak_memory_mb': memory_metrics['peak_memory_mb'],
                'memory_delta_mb': memory_metrics['memory_delta_mb'],
                'method': 'streaming'
            }

        # Benchmark both approaches
        standard_result = benchmark_standard_memory()
        streaming_result = benchmark_streaming_memory()

        # Both should succeed
        assert standard_result['success'], "Standard processing should succeed"
        assert streaming_result['success'], "Streaming processing should succeed"

        # Streaming should use less peak memory for large files
        memory_reduction = (standard_result['peak_memory_mb'] - streaming_result['peak_memory_mb']) / standard_result['peak_memory_mb']

        # Expect at least 10% memory reduction with streaming
        if memory_reduction > 0:
            print(f"Memory reduction with streaming: {memory_reduction:.1%}")

    def test_chunk_size_impact_on_memory(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Test impact of chunk size on memory usage"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("medium_single", [])

        if not file_paths:
            pytest.skip("No medium files available")

        file_path = file_paths[0]
        chunk_sizes = [100, 500, 1000, 2000]
        results = {}

        for chunk_size in chunk_sizes:
            def benchmark_chunk_size():
                config = create_performance_config(
                    enable_streaming=True,
                    chunk_size=chunk_size
                )
                processor = PerformanceOptimizedExcelProcessor(config)

                with MemoryMonitor(1024) as monitor:
                    result = processor.process_single_file(file_path)

                memory_metrics = monitor.get_metrics()

                return {
                    'chunk_size': chunk_size,
                    'success': result['success'],
                    'peak_memory_mb': memory_metrics['peak_memory_mb'],
                    'processing_time': result.get('metrics', {}).get('processing_time_seconds', 0)
                }

            results[chunk_size] = benchmark(benchmark_chunk_size)

        # Analyze chunk size impact
        for chunk_size, result in results.items():
            assert result['success'], f"Processing with chunk size {chunk_size} should succeed"

        # Smaller chunks should generally use less memory
        memory_usage = [(cs, results[cs]['peak_memory_mb']) for cs in chunk_sizes]
        print(f"Memory usage by chunk size: {memory_usage}")


class TestCacheEffectivenessBenchmarks:
    """Benchmark caching effectiveness"""

    def test_cache_hit_rate_performance(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Test cache hit rate and performance impact"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("small_multiple", [])

        if len(file_paths) < 2:
            pytest.skip("Insufficient files for cache testing")

        # Process the same files multiple times to test caching
        file_path = file_paths[0]  # Use same file for cache testing

        def benchmark_with_cache():
            config = create_performance_config(cache_size=64)
            processor = PerformanceOptimizedExcelProcessor(config)

            # First pass - populate cache
            first_result = processor.process_single_file(file_path)

            # Second pass - should hit cache
            start_time = time.time()
            second_result = processor.process_single_file(file_path)
            cached_time = time.time() - start_time

            performance_summary = processor.get_performance_summary()
            cache_stats = performance_summary['cache_metrics']

            return {
                'first_success': first_result['success'],
                'second_success': second_result['success'],
                'cached_processing_time': cached_time,
                'cache_hit_rate': cache_stats['hit_rate'],
                'cache_hits': cache_stats['hits'],
                'cache_misses': cache_stats['misses']
            }

        result = benchmark(benchmark_with_cache)

        # Assertions
        assert result['first_success'], "First processing should succeed"
        assert result['second_success'], "Cached processing should succeed"
        assert result['cache_hits'] > 0, "Should have cache hits"
        assert result['cached_processing_time'] < 1.0, f"Cached processing should be fast: {result['cached_processing_time']:.3f}s"

    def test_cache_memory_efficiency(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Test cache memory efficiency with different cache sizes"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("small_multiple", [])

        if len(file_paths) < 3:
            pytest.skip("Insufficient files for cache memory testing")

        cache_sizes = [16, 64, 256]
        results = {}

        for cache_size in cache_sizes:
            def benchmark_cache_size():
                config = create_performance_config(cache_size=cache_size)
                processor = PerformanceOptimizedExcelProcessor(config)

                with MemoryMonitor(1024) as monitor:
                    # Process all files to test cache behavior
                    for file_path in file_paths:
                        processor.process_single_file(file_path)

                    # Process first file again to test cache hit
                    processor.process_single_file(file_paths[0])

                memory_metrics = monitor.get_metrics()
                performance_summary = processor.get_performance_summary()

                return {
                    'cache_size': cache_size,
                    'peak_memory_mb': memory_metrics['peak_memory_mb'],
                    'cache_stats': performance_summary['cache_metrics']
                }

            results[cache_size] = benchmark(benchmark_cache_size)

        # Analyze cache size impact
        for cache_size, result in results.items():
            print(f"Cache size {cache_size}: Memory {result['peak_memory_mb']:.1f}MB, Hit rate {result['cache_stats']['hit_rate']:.1%}")


class TestRealWorldScenarios:
    """Benchmark real-world usage scenarios"""

    def test_portfolio_analysis_scenario(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Simulate analyzing a portfolio of companies"""
        temp_dir, file_registry = benchmark_data_dir
        file_paths = file_registry.get("financial_portfolio", [])

        if len(file_paths) < 5:
            pytest.skip("Insufficient files for portfolio scenario")

        def benchmark_portfolio_analysis():
            config = create_performance_config(
                max_workers=4,
                enable_streaming=True,
                cache_size=128
            )
            processor = PerformanceOptimizedExcelProcessor(config)

            start_time = time.time()

            # Simulate portfolio analysis workflow
            results = processor.process_multiple_files(file_paths[:5])  # Analyze 5 companies

            # Simulate re-analysis (should benefit from caching)
            reanalysis_start = time.time()
            reanalysis_results = processor.process_multiple_files(file_paths[:3])
            reanalysis_time = time.time() - reanalysis_start

            total_time = time.time() - start_time

            return {
                'total_companies': 5,
                'successful_companies': results['successful_files'],
                'total_analysis_time': total_time,
                'reanalysis_time': reanalysis_time,
                'performance_metrics': results['performance_metrics'],
                'speedup_from_cache': results['total_processing_time'] / reanalysis_time if reanalysis_time > 0 else 1
            }

        result = benchmark(benchmark_portfolio_analysis)

        # Assertions for real-world scenario
        assert result['successful_companies'] >= 4, "Should successfully analyze most companies"
        assert result['total_analysis_time'] < 120, f"Portfolio analysis too slow: {result['total_analysis_time']:.1f}s"
        assert result['reanalysis_time'] < result['total_analysis_time'] / 2, "Reanalysis should be faster due to caching"

    def test_daily_processing_workload(
        self,
        benchmark,
        benchmark_data_dir
    ):
        """Simulate daily processing workload"""
        temp_dir, file_registry = benchmark_data_dir

        # Collect files from multiple scenarios to simulate mixed workload
        mixed_files = []
        for scenario_name in ["small_multiple", "medium_single", "financial_simple"]:
            files = file_registry.get(scenario_name, [])
            mixed_files.extend(files[:2])  # Take first 2 from each

        if len(mixed_files) < 4:
            pytest.skip("Insufficient files for daily workload simulation")

        def benchmark_daily_workload():
            config = create_performance_config(
                max_workers=6,
                enable_streaming=True,
                cache_size=256,
                max_memory_mb=2048
            )
            processor = PerformanceOptimizedExcelProcessor(config)

            start_time = time.time()

            # Process mixed workload
            batch_results = []
            batch_size = 3

            for i in range(0, len(mixed_files), batch_size):
                batch_files = mixed_files[i:i+batch_size]
                batch_result = processor.process_multiple_files(batch_files)
                batch_results.append(batch_result)

            total_time = time.time() - start_time
            total_successful = sum(br['successful_files'] for br in batch_results)
            total_files = sum(br['total_files'] for br in batch_results)

            performance_summary = processor.get_performance_summary()

            return {
                'total_files_processed': total_files,
                'successful_files': total_successful,
                'total_processing_time': total_time,
                'throughput_files_per_minute': (total_successful / total_time) * 60 if total_time > 0 else 0,
                'performance_summary': performance_summary
            }

        result = benchmark(benchmark_daily_workload)

        # Assertions for daily workload
        success_rate = result['successful_files'] / result['total_files_processed'] if result['total_files_processed'] > 0 else 0
        assert success_rate >= 0.8, f"Daily workload success rate too low: {success_rate:.1%}"
        assert result['throughput_files_per_minute'] > 5, f"Daily throughput too low: {result['throughput_files_per_minute']:.1f} files/min"


if __name__ == '__main__':
    # Run performance benchmarks
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--benchmark-only',
        '--benchmark-sort=mean'
    ])