"""
Dashboard Component Caching System

Implements intelligent caching for Streamlit dashboard components to optimize
performance for large datasets and repeated calculations.

Features:
- Component-level result caching with TTL
- Chart and visualization memoization
- Data transformation caching
- Memory-aware cache management
- Cache performance metrics
"""

import streamlit as st
import pandas as pd
import time
import hashlib
import pickle
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, field
import weakref
import gc
import sys

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_mb: float = 0.0
    avg_hit_time_ms: float = 0.0
    avg_miss_time_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / max(total, 1)) * 100

    @property
    def effectiveness_score(self) -> float:
        """Overall cache effectiveness (0-100)"""
        if self.avg_miss_time_ms == 0:
            return 100.0
        time_savings = max(0, (self.avg_miss_time_ms - self.avg_hit_time_ms) / self.avg_miss_time_ms)
        return self.hit_rate * 0.7 + time_savings * 100 * 0.3


@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Age of entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class DashboardCacheOptimizer:
    """
    Intelligent caching system for dashboard components
    """

    def __init__(self, max_size_mb: float = 100.0, default_ttl: int = 300):
        """
        Initialize cache optimizer

        Args:
            max_size_mb: Maximum cache size in MB
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.max_size_mb = max_size_mb
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.metrics = CacheMetrics()

        # Initialize Streamlit session state
        if 'dashboard_cache' not in st.session_state:
            st.session_state.dashboard_cache = {}
        if 'cache_metrics' not in st.session_state:
            st.session_state.cache_metrics = CacheMetrics()

    def cached_component(self, ttl: Optional[int] = None, key_params: List[str] = None):
        """
        Decorator for caching Streamlit component results

        Args:
            ttl: Time-to-live in seconds
            key_params: Specific parameters to include in cache key
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(func.__name__, args, kwargs, key_params)

                # Check cache first
                start_time = time.time()
                cached_result = self._get_from_cache(cache_key)

                if cached_result is not None:
                    # Cache hit
                    hit_time = (time.time() - start_time) * 1000
                    self._record_hit(hit_time)
                    logger.debug(f"Cache hit for {func.__name__}: {hit_time:.2f}ms")
                    return cached_result

                # Cache miss - execute function
                miss_start = time.time()
                result = func(*args, **kwargs)
                execution_time = (time.time() - miss_start) * 1000

                # Store in cache
                self._store_in_cache(cache_key, result, ttl or self.default_ttl)
                self._record_miss(execution_time)

                logger.debug(f"Cache miss for {func.__name__}: {execution_time:.2f}ms")
                return result

            return wrapper
        return decorator

    def cached_dataframe_operation(self, operation_name: str, ttl: int = 300):
        """
        Cache DataFrame operations with intelligent key generation

        Args:
            operation_name: Name of the operation for cache key
            ttl: Time-to-live in seconds
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(df: pd.DataFrame, *args, **kwargs):
                # Generate cache key based on DataFrame content hash and parameters
                df_hash = self._hash_dataframe(df)
                params_hash = self._hash_params(args, kwargs)
                cache_key = f"{operation_name}:{df_hash}:{params_hash}"

                # Check cache
                start_time = time.time()
                cached_result = self._get_from_cache(cache_key)

                if cached_result is not None:
                    hit_time = (time.time() - start_time) * 1000
                    self._record_hit(hit_time)
                    return cached_result

                # Execute operation
                miss_start = time.time()
                result = func(df, *args, **kwargs)
                execution_time = (time.time() - miss_start) * 1000

                # Cache result
                self._store_in_cache(cache_key, result, ttl)
                self._record_miss(execution_time)

                return result

            return wrapper
        return decorator

    def cache_chart(self, chart_type: str, data_source: str, ttl: int = 600):
        """
        Cache chart/visualization objects

        Args:
            chart_type: Type of chart (e.g., 'scatter', 'line', 'bar')
            data_source: Source identifier for the data
            ttl: Time-to-live in seconds (10 minutes default)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key for chart
                params_str = f"{chart_type}:{data_source}:{self._hash_params(args, kwargs)}"
                cache_key = f"chart:{params_str}"

                # Check cache
                cached_chart = self._get_from_cache(cache_key)
                if cached_chart is not None:
                    self._record_hit(0.1)  # Charts load very fast from cache
                    return cached_chart

                # Generate chart
                start_time = time.time()
                chart = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                # Cache chart object
                self._store_in_cache(cache_key, chart, ttl)
                self._record_miss(execution_time)

                return chart

            return wrapper
        return decorator

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict, key_params: List[str] = None) -> str:
        """Generate cache key from function name and parameters"""
        if key_params:
            # Only use specified parameters
            relevant_kwargs = {k: v for k, v in kwargs.items() if k in key_params}
            key_data = f"{func_name}:{self._hash_params((), relevant_kwargs)}"
        else:
            # Use all parameters
            key_data = f"{func_name}:{self._hash_params(args, kwargs)}"

        return hashlib.md5(key_data.encode()).hexdigest()

    def _hash_params(self, args: tuple, kwargs: dict) -> str:
        """Generate hash for function parameters"""
        try:
            # Convert parameters to string representation
            params_str = f"{args}:{sorted(kwargs.items())}"
            return hashlib.md5(params_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning(f"Error hashing parameters: {e}")
            return f"unhashable_{time.time()}"

    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """Generate hash for DataFrame content"""
        try:
            # Use DataFrame shape and column hash for efficiency
            shape_str = f"{df.shape}"
            columns_str = f"{list(df.columns)}"

            # Sample some data points for content verification
            if len(df) > 0:
                sample_size = min(100, len(df))
                sample_data = df.head(sample_size).to_string()
                content_hash = hashlib.md5(sample_data.encode()).hexdigest()[:8]
            else:
                content_hash = "empty"

            return f"{shape_str}:{columns_str}:{content_hash}"

        except Exception as e:
            logger.warning(f"Error hashing DataFrame: {e}")
            return f"df_unhashable_{time.time()}"

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve item from cache"""
        # Check session state cache first (Streamlit-aware)
        if cache_key in st.session_state.dashboard_cache:
            entry = st.session_state.dashboard_cache[cache_key]

            # Check if expired
            if entry.is_expired:
                del st.session_state.dashboard_cache[cache_key]
                return None

            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            return entry.data

        return None

    def _store_in_cache(self, cache_key: str, data: Any, ttl: int):
        """Store item in cache with memory management"""
        try:
            # Calculate data size
            data_size = sys.getsizeof(pickle.dumps(data))

            # Check if we need to evict items
            self._ensure_cache_space(data_size)

            # Create cache entry
            entry = CacheEntry(
                data=data,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=data_size,
                ttl_seconds=ttl
            )

            # Store in session state
            st.session_state.dashboard_cache[cache_key] = entry

            # Update metrics
            self.metrics.total_size_mb = self._calculate_total_cache_size()

        except Exception as e:
            logger.warning(f"Error storing in cache: {e}")

    def _ensure_cache_space(self, required_bytes: int):
        """Ensure sufficient cache space by evicting old entries"""
        current_size_mb = self._calculate_total_cache_size()
        required_mb = required_bytes / (1024 * 1024)

        if current_size_mb + required_mb > self.max_size_mb:
            # Need to evict entries
            entries_by_priority = self._get_eviction_candidates()

            for cache_key in entries_by_priority:
                if cache_key in st.session_state.dashboard_cache:
                    del st.session_state.dashboard_cache[cache_key]
                    self.metrics.evictions += 1

                    current_size_mb = self._calculate_total_cache_size()
                    if current_size_mb + required_mb <= self.max_size_mb:
                        break

    def _get_eviction_candidates(self) -> List[str]:
        """Get cache keys ordered by eviction priority (least valuable first)"""
        candidates = []

        for cache_key, entry in st.session_state.dashboard_cache.items():
            # Calculate priority score (lower = higher eviction priority)
            age_score = entry.age_seconds / 3600  # Hours
            access_score = 1 / max(entry.access_count, 1)
            size_penalty = entry.size_bytes / (1024 * 1024)  # MB

            priority = age_score + access_score + (size_penalty * 0.1)
            candidates.append((priority, cache_key))

        # Sort by priority (highest priority = first to evict)
        candidates.sort(reverse=True)
        return [key for _, key in candidates]

    def _calculate_total_cache_size(self) -> float:
        """Calculate total cache size in MB"""
        total_bytes = sum(
            entry.size_bytes for entry in st.session_state.dashboard_cache.values()
        )
        return total_bytes / (1024 * 1024)

    def _record_hit(self, time_ms: float):
        """Record cache hit metrics"""
        if 'cache_metrics' not in st.session_state:
            st.session_state.cache_metrics = CacheMetrics()

        metrics = st.session_state.cache_metrics
        metrics.hits += 1

        # Update running average
        total_hits = metrics.hits
        metrics.avg_hit_time_ms = ((metrics.avg_hit_time_ms * (total_hits - 1)) + time_ms) / total_hits

        st.session_state.cache_metrics = metrics

    def _record_miss(self, time_ms: float):
        """Record cache miss metrics"""
        if 'cache_metrics' not in st.session_state:
            st.session_state.cache_metrics = CacheMetrics()

        metrics = st.session_state.cache_metrics
        metrics.misses += 1

        # Update running average
        total_misses = metrics.misses
        metrics.avg_miss_time_ms = ((metrics.avg_miss_time_ms * (total_misses - 1)) + time_ms) / total_misses

        st.session_state.cache_metrics = metrics

    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries, optionally matching a pattern"""
        if pattern is None:
            st.session_state.dashboard_cache.clear()
            logger.info("Cleared entire dashboard cache")
        else:
            keys_to_remove = [
                key for key in st.session_state.dashboard_cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del st.session_state.dashboard_cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")

        # Reset metrics
        st.session_state.cache_metrics = CacheMetrics()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        if 'cache_metrics' not in st.session_state:
            st.session_state.cache_metrics = CacheMetrics()

        metrics = st.session_state.cache_metrics
        cache_size = len(st.session_state.dashboard_cache)
        size_mb = self._calculate_total_cache_size()

        return {
            'entries_count': cache_size,
            'size_mb': size_mb,
            'max_size_mb': self.max_size_mb,
            'utilization_pct': (size_mb / self.max_size_mb) * 100,
            'hit_rate': metrics.hit_rate,
            'effectiveness_score': metrics.effectiveness_score,
            'total_hits': metrics.hits,
            'total_misses': metrics.misses,
            'evictions': metrics.evictions,
            'avg_hit_time_ms': metrics.avg_hit_time_ms,
            'avg_miss_time_ms': metrics.avg_miss_time_ms
        }

    def optimize_memory(self):
        """Force memory optimization and garbage collection"""
        # Remove expired entries
        expired_keys = [
            key for key, entry in st.session_state.dashboard_cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del st.session_state.dashboard_cache[key]

        # Force garbage collection
        gc.collect()

        # Update metrics
        self.metrics.total_size_mb = self._calculate_total_cache_size()

        logger.info(f"Memory optimization completed. Removed {len(expired_keys)} expired entries.")
        return len(expired_keys)


# Global cache optimizer instance
_cache_optimizer = None


def get_cache_optimizer() -> DashboardCacheOptimizer:
    """Get the global cache optimizer instance"""
    global _cache_optimizer
    if _cache_optimizer is None:
        _cache_optimizer = DashboardCacheOptimizer()
    return _cache_optimizer


# Convenience decorators using global instance
def cache_component(ttl: Optional[int] = None, key_params: List[str] = None):
    """Convenience decorator for component caching"""
    return get_cache_optimizer().cached_component(ttl, key_params)


def cache_dataframe_op(operation_name: str, ttl: int = 300):
    """Convenience decorator for DataFrame operation caching"""
    return get_cache_optimizer().cached_dataframe_operation(operation_name, ttl)


def cache_chart(chart_type: str, data_source: str, ttl: int = 600):
    """Convenience decorator for chart caching"""
    return get_cache_optimizer().cache_chart(chart_type, data_source, ttl)


def display_cache_management_panel():
    """Display cache management controls in Streamlit"""
    optimizer = get_cache_optimizer()
    stats = optimizer.get_cache_stats()

    st.subheader("🗄️ Cache Management")

    # Display stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Cache Entries", stats['entries_count'])

    with col2:
        st.metric("Memory Usage", f"{stats['size_mb']:.1f} MB",
                 f"{stats['utilization_pct']:.1f}% capacity")

    with col3:
        st.metric("Hit Rate", f"{stats['hit_rate']:.1f}%",
                 "Excellent" if stats['hit_rate'] > 80 else "Good" if stats['hit_rate'] > 60 else "Poor")

    with col4:
        st.metric("Effectiveness", f"{stats['effectiveness_score']:.0f}/100")

    # Cache controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧹 Clear Cache"):
            optimizer.clear_cache()
            st.success("Cache cleared!")
            st.rerun()

    with col2:
        if st.button("⚡ Optimize Memory"):
            removed = optimizer.optimize_memory()
            st.success(f"Optimized! Removed {removed} expired entries.")
            st.rerun()

    with col3:
        # Pattern-based clearing
        pattern = st.text_input("Clear by pattern:", placeholder="e.g., 'chart:' or 'financial_'")
        if st.button("🎯 Clear Pattern") and pattern:
            optimizer.clear_cache(pattern)
            st.success(f"Cleared entries matching '{pattern}'")
            st.rerun()

    # Performance metrics
    if stats['total_hits'] + stats['total_misses'] > 0:
        with st.expander("📊 Detailed Performance Metrics"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Response Times**")
                st.write(f"Cache Hits: {stats['avg_hit_time_ms']:.2f}ms avg")
                st.write(f"Cache Misses: {stats['avg_miss_time_ms']:.2f}ms avg")
                if stats['avg_miss_time_ms'] > 0:
                    speedup = stats['avg_miss_time_ms'] / max(stats['avg_hit_time_ms'], 0.1)
                    st.write(f"Speedup: {speedup:.1f}x faster")

            with col2:
                st.write("**Cache Operations**")
                st.write(f"Total Hits: {stats['total_hits']:,}")
                st.write(f"Total Misses: {stats['total_misses']:,}")
                st.write(f"Evictions: {stats['evictions']:,}")