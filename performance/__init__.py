"""
Performance Optimization Package

This package provides high-performance watch list processing optimizations
including concurrent API calls, lazy loading, and memory management.
"""

from .concurrent_watch_list_optimizer import (
    ConcurrentWatchListOptimizer,
    ConcurrencyConfig,
    LazyLoadingConfig,
    create_optimized_watch_list_manager,
    PerformanceMetrics
)

from .streamlit_performance_integration import (
    StreamlitPerformanceIntegration,
    display_performance_optimized_watch_lists
)

from .performance_benchmark import (
    PerformanceBenchmark,
    BenchmarkResult,
    PerformanceProfile,
    run_performance_benchmark,
    run_scaling_benchmark
)

__all__ = [
    'ConcurrentWatchListOptimizer',
    'ConcurrencyConfig', 
    'LazyLoadingConfig',
    'create_optimized_watch_list_manager',
    'PerformanceMetrics',
    'StreamlitPerformanceIntegration',
    'display_performance_optimized_watch_lists',
    'PerformanceBenchmark',
    'BenchmarkResult',
    'PerformanceProfile',
    'run_performance_benchmark',
    'run_scaling_benchmark'
]