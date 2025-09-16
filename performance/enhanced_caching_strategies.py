"""
Enhanced Caching Strategies for Financial Analysis Application

This module provides advanced caching strategies specifically optimized for
financial data processing and analysis workflows.
"""

import asyncio
import hashlib
import json
import pickle
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import wraps
import weakref

# Import existing cache manager if available
try:
    from core.data_processing.cache.optimized_cache_manager import (
        OptimizedCacheManager,
        CacheLayer,
        CacheEventType
    )
    OPTIMIZED_CACHE_AVAILABLE = True
except ImportError:
    OPTIMIZED_CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CacheStrategy:
    """Configuration for different caching strategies"""
    name: str
    ttl_seconds: int
    max_entries: int
    compression: bool = False
    background_refresh: bool = False
    priority_weight: float = 1.0


class StrategicCacheManager:
    """Enhanced cache manager with multiple strategic approaches"""

    # Predefined cache strategies for different data types
    STRATEGIES = {
        'financial_data': CacheStrategy(
            name='financial_data',
            ttl_seconds=3600,  # 1 hour
            max_entries=1000,
            compression=True,
            background_refresh=True,
            priority_weight=1.5
        ),
        'price_data': CacheStrategy(
            name='price_data',
            ttl_seconds=300,   # 5 minutes
            max_entries=500,
            compression=False,
            background_refresh=True,
            priority_weight=2.0
        ),
        'calculation_results': CacheStrategy(
            name='calculation_results',
            ttl_seconds=1800,  # 30 minutes
            max_entries=200,
            compression=True,
            background_refresh=False,
            priority_weight=1.2
        ),
        'visualization_data': CacheStrategy(
            name='visualization_data',
            ttl_seconds=900,   # 15 minutes
            max_entries=100,
            compression=True,
            background_refresh=False,
            priority_weight=0.8
        )
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize optimized cache if available
        if OPTIMIZED_CACHE_AVAILABLE:
            self.optimized_cache = OptimizedCacheManager(str(self.cache_dir))
        else:
            self.optimized_cache = None

        self._memory_caches = {}
        self._background_refreshers = {}
        self._stats = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="CacheRefresh")

    def get_cache_key(self, *args, strategy: str = 'default', **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = {
            'args': args,
            'kwargs': kwargs,
            'strategy': strategy
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def cache_with_strategy(
        self,
        strategy_name: str = 'financial_data',
        key_prefix: str = '',
        background_refresh_func: Optional[Callable] = None
    ):
        """Decorator for applying strategic caching to functions"""
        def decorator(func: Callable) -> Callable:
            strategy = self.STRATEGIES.get(strategy_name, self.STRATEGIES['financial_data'])

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}_{self.get_cache_key(*args, strategy=strategy_name, **kwargs)}"

                # Try to get from cache
                cached_result = self._get_from_cache(cache_key, strategy)
                if cached_result is not None:
                    self._update_stats(strategy_name, 'hit')
                    return cached_result

                # Cache miss - compute result
                start_time = time.time()
                result = func(*args, **kwargs)
                computation_time = time.time() - start_time

                # Store in cache
                self._store_in_cache(cache_key, result, strategy)
                self._update_stats(strategy_name, 'miss', computation_time)

                # Schedule background refresh if configured
                if strategy.background_refresh and background_refresh_func:
                    self._schedule_background_refresh(
                        cache_key,
                        background_refresh_func,
                        args,
                        kwargs,
                        strategy
                    )

                return result

            return wrapper
        return decorator

    def _get_from_cache(self, key: str, strategy: CacheStrategy) -> Any:
        """Get item from cache with strategy-specific logic"""
        if self.optimized_cache:
            try:
                return self.optimized_cache.get(key)
            except Exception as e:
                logger.warning(f"Failed to get from optimized cache: {e}")

        # Fallback to simple file-based cache
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                # Check TTL
                if time.time() - cached_data['timestamp'] < strategy.ttl_seconds:
                    return cached_data['data']
                else:
                    cache_file.unlink()  # Remove expired cache
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")

        return None

    def _store_in_cache(self, key: str, data: Any, strategy: CacheStrategy):
        """Store item in cache with strategy-specific logic"""
        if self.optimized_cache:
            try:
                self.optimized_cache.put(
                    key,
                    data,
                    ttl=strategy.ttl_seconds,
                    compression=strategy.compression
                )
                return
            except Exception as e:
                logger.warning(f"Failed to store in optimized cache: {e}")

        # Fallback to simple file-based cache
        cache_file = self.cache_dir / f"{key}.cache"
        cached_data = {
            'data': data,
            'timestamp': time.time(),
            'strategy': strategy.name
        }

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")

    def _schedule_background_refresh(
        self,
        cache_key: str,
        refresh_func: Callable,
        args: tuple,
        kwargs: dict,
        strategy: CacheStrategy
    ):
        """Schedule background cache refresh"""
        def refresh_task():
            try:
                # Wait until 80% of TTL has passed
                refresh_delay = strategy.ttl_seconds * 0.8
                time.sleep(refresh_delay)

                # Refresh the cached data
                new_data = refresh_func(*args, **kwargs)
                self._store_in_cache(cache_key, new_data, strategy)
                logger.debug(f"Background refresh completed for key: {cache_key}")

            except Exception as e:
                logger.warning(f"Background refresh failed for key {cache_key}: {e}")

        # Submit to executor
        self.executor.submit(refresh_task)

    def _update_stats(self, strategy_name: str, operation: str, computation_time: float = 0):
        """Update cache statistics"""
        if strategy_name not in self._stats:
            self._stats[strategy_name] = {
                'hits': 0,
                'misses': 0,
                'total_computation_time': 0,
                'avg_computation_time': 0
            }

        stats = self._stats[strategy_name]
        if operation == 'hit':
            stats['hits'] += 1
        elif operation == 'miss':
            stats['misses'] += 1
            stats['total_computation_time'] += computation_time
            stats['avg_computation_time'] = stats['total_computation_time'] / stats['misses']

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'strategies': self._stats.copy(),
            'overall': {
                'total_hits': sum(s['hits'] for s in self._stats.values()),
                'total_misses': sum(s['misses'] for s in self._stats.values()),
                'hit_ratio': 0
            }
        }

        total_requests = stats['overall']['total_hits'] + stats['overall']['total_misses']
        if total_requests > 0:
            stats['overall']['hit_ratio'] = stats['overall']['total_hits'] / total_requests

        # Add optimized cache stats if available
        if self.optimized_cache:
            try:
                stats['optimized_cache'] = self.optimized_cache.get_cache_stats()
            except Exception as e:
                logger.warning(f"Failed to get optimized cache stats: {e}")

        return stats

    def clear_cache(self, strategy_name: Optional[str] = None):
        """Clear cache for specific strategy or all caches"""
        if self.optimized_cache:
            try:
                self.optimized_cache.clear()
            except Exception as e:
                logger.warning(f"Failed to clear optimized cache: {e}")

        # Clear file-based cache
        pattern = "*.cache"
        if strategy_name:
            # Clear only files for specific strategy would require metadata
            # For now, clear all
            pass

        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

    def warm_cache(self, warming_functions: Dict[str, Callable], concurrency: int = 4):
        """Warm cache with pre-computed data"""
        def warm_function(name: str, func: Callable):
            try:
                logger.info(f"Starting cache warming for: {name}")
                result = func()
                logger.info(f"Cache warming completed for: {name}")
                return result
            except Exception as e:
                logger.warning(f"Cache warming failed for {name}: {e}")
                return None

        # Submit warming tasks
        futures = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            for name, func in warming_functions.items():
                future = executor.submit(warm_function, name, func)
                futures.append((name, future))

        # Collect results
        results = {}
        for name, future in futures:
            try:
                results[name] = future.result()
            except Exception as e:
                logger.warning(f"Failed to get warming result for {name}: {e}")
                results[name] = None

        return results


# Global cache manager instance
strategic_cache = StrategicCacheManager()


# Convenience decorators for common use cases
def cache_financial_data(key_prefix: str = ''):
    """Cache financial data with appropriate TTL and compression"""
    return strategic_cache.cache_with_strategy('financial_data', key_prefix)


def cache_price_data(key_prefix: str = ''):
    """Cache price data with short TTL for real-time updates"""
    return strategic_cache.cache_with_strategy('price_data', key_prefix)


def cache_calculations(key_prefix: str = ''):
    """Cache calculation results with medium TTL"""
    return strategic_cache.cache_with_strategy('calculation_results', key_prefix)


def cache_visualizations(key_prefix: str = ''):
    """Cache visualization data with short TTL"""
    return strategic_cache.cache_with_strategy('visualization_data', key_prefix)


class AdaptiveCachePredictor:
    """Predicts and pre-caches likely needed data"""

    def __init__(self, cache_manager: StrategicCacheManager):
        self.cache_manager = cache_manager
        self.access_patterns = {}
        self.prediction_accuracy = {}

    def record_access(self, data_type: str, key: str, context: Dict[str, Any] = None):
        """Record data access patterns for prediction"""
        if data_type not in self.access_patterns:
            self.access_patterns[data_type] = []

        access_record = {
            'key': key,
            'timestamp': time.time(),
            'context': context or {}
        }
        self.access_patterns[data_type].append(access_record)

        # Keep only recent patterns (last 1000 accesses)
        if len(self.access_patterns[data_type]) > 1000:
            self.access_patterns[data_type] = self.access_patterns[data_type][-1000:]

    def predict_next_access(self, data_type: str, current_context: Dict[str, Any] = None) -> List[str]:
        """Predict likely next data accesses"""
        if data_type not in self.access_patterns:
            return []

        recent_patterns = self.access_patterns[data_type][-100:]  # Last 100 accesses

        # Simple frequency-based prediction
        key_frequency = {}
        for pattern in recent_patterns:
            key = pattern['key']
            key_frequency[key] = key_frequency.get(key, 0) + 1

        # Sort by frequency and return top predictions
        predictions = sorted(key_frequency.items(), key=lambda x: x[1], reverse=True)
        return [key for key, _ in predictions[:5]]  # Top 5 predictions

    def adaptive_prefetch(self, data_type: str, fetch_function: Callable, context: Dict[str, Any] = None):
        """Adaptively prefetch likely needed data"""
        predictions = self.predict_next_access(data_type, context)

        def prefetch_task():
            for predicted_key in predictions:
                try:
                    # This would need to be implemented based on specific data types
                    # For now, just log the prediction
                    logger.info(f"Predicted access for {data_type}: {predicted_key}")
                except Exception as e:
                    logger.warning(f"Prefetch failed for {predicted_key}: {e}")

        # Run prefetch in background
        self.cache_manager.executor.submit(prefetch_task)


# Example usage and integration helpers
def integrate_with_existing_financial_calculator():
    """Example integration with the existing financial calculator"""

    @cache_financial_data(key_prefix='fcf_analysis')
    def cached_fcf_calculation(calculator, periods: int = 5):
        """Cached FCF calculation with strategic caching"""
        return calculator.calculate_fcf_analysis(periods)

    @cache_calculations(key_prefix='dcf_valuation')
    def cached_dcf_valuation(valuator, discount_rate: float, growth_rate: float):
        """Cached DCF valuation with appropriate TTL"""
        return valuator.calculate_dcf(discount_rate, growth_rate)

    return {
        'fcf_calculation': cached_fcf_calculation,
        'dcf_valuation': cached_dcf_valuation
    }


def get_cache_performance_summary() -> Dict[str, Any]:
    """Get performance summary for monitoring"""
    stats = strategic_cache.get_cache_statistics()

    summary = {
        'overall_hit_ratio': f"{stats['overall']['hit_ratio']:.2%}",
        'total_requests': stats['overall']['total_hits'] + stats['overall']['total_misses'],
        'strategies_performance': {}
    }

    for strategy_name, strategy_stats in stats['strategies'].items():
        total_requests = strategy_stats['hits'] + strategy_stats['misses']
        hit_ratio = strategy_stats['hits'] / total_requests if total_requests > 0 else 0

        summary['strategies_performance'][strategy_name] = {
            'hit_ratio': f"{hit_ratio:.2%}",
            'avg_computation_time': f"{strategy_stats['avg_computation_time']:.3f}s",
            'total_requests': total_requests
        }

    return summary