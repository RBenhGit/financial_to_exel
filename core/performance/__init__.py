"""
Performance Optimization Module
================================

Provides multi-layer caching, performance monitoring, and optimization tools
for the financial analysis platform.

Main Components:
---------------
- PerformanceFramework: Central framework coordinating all cache layers
- OptimizedCacheManager: Multi-tier cache with intelligent eviction
- CalculationCache: Dependency-aware caching for calculations
- Performance tracking and metrics collection

Usage:
------
>>> from core.performance import get_performance_framework
>>>
>>> framework = get_performance_framework()
>>>
>>> # Get cached adapter response
>>> data = framework.get_cached_adapter_response("AAPL", "fundamentals")
>>>
>>> # Cache new data
>>> framework.cache_adapter_response("AAPL", "fundamentals", data, ttl_hours=24)
>>>
>>> # Get performance report
>>> report = framework.get_performance_report()
>>> print(f"Cache hit ratio: {report['summary']['cache_hit_ratio']}%")
"""

from .performance_framework import (
    PerformanceFramework,
    get_performance_framework,
    track_performance,
    CacheLayer,
    PerformanceMetrics,
    PerformanceTarget,
    CacheInvalidationRule
)

__all__ = [
    'PerformanceFramework',
    'get_performance_framework',
    'track_performance',
    'CacheLayer',
    'PerformanceMetrics',
    'PerformanceTarget',
    'CacheInvalidationRule'
]

__version__ = '1.0.0'
