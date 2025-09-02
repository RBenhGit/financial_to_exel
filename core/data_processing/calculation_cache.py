"""
Calculation Result Cache with Dependency Invalidation
====================================================

This module provides intelligent caching for financial calculations with 
automatic dependency tracking and invalidation. When input data changes,
all dependent calculations are automatically invalidated.

Features:
- Dependency graph tracking
- Automatic invalidation cascades
- Memory-efficient storage with compression
- Thread-safe operations
- Performance metrics and monitoring

Usage Example:
>>> from calculation_cache import CalculationCache
>>> cache = CalculationCache()
>>> 
>>> # Cache a calculation result
>>> cache.set_result("AAPL", "dcf_valuation", result_data, dependencies=["revenue", "cash_flow"])
>>> 
>>> # Get cached result
>>> result = cache.get_result("AAPL", "dcf_valuation")
>>> 
>>> # Invalidate when input data changes
>>> cache.invalidate_dependencies("AAPL", "revenue")  # This will also invalidate dcf_valuation
"""

import json
import logging
import threading
import pickle
import gzip
import hashlib
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import weakref

# Configure logging
logger = logging.getLogger(__name__)


class CacheEntryStatus(Enum):
    """Status of cache entries"""
    VALID = "valid"
    INVALID = "invalid"
    COMPUTING = "computing"
    ERROR = "error"


@dataclass
class CacheEntry:
    """Single cache entry with metadata and dependency tracking"""
    result: Any
    timestamp: datetime
    dependencies: Set[str] = field(default_factory=set)
    computation_time_seconds: float = 0.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    status: CacheEntryStatus = CacheEntryStatus.VALID
    size_bytes: int = 0
    compression_ratio: float = 1.0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Calculate entry size and update metadata"""
        if self.result is not None:
            try:
                # Estimate size of the result
                self.size_bytes = len(pickle.dumps(self.result))
            except Exception:
                self.size_bytes = 0
    
    def mark_accessed(self):
        """Mark this entry as recently accessed"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if entry has expired"""
        if self.status != CacheEntryStatus.VALID:
            return True
        return (datetime.now() - self.timestamp).total_seconds() > ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry metadata to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'dependencies': list(self.dependencies),
            'computation_time_seconds': self.computation_time_seconds,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat(),
            'status': self.status.value,
            'size_bytes': self.size_bytes,
            'compression_ratio': self.compression_ratio,
            'error_message': self.error_message
        }


@dataclass
class DependencyNode:
    """Node in the dependency graph"""
    symbol: str
    calculation_id: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)  # What depends on this
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_cache_key(self) -> str:
        """Get cache key for this node"""
        return f"{self.symbol}:{self.calculation_id}"


class CalculationCache:
    """
    Intelligent cache for financial calculations with dependency tracking.
    
    This cache automatically invalidates dependent calculations when input
    data changes, ensuring calculation results are always consistent with
    the underlying data.
    """
    
    def __init__(
        self, 
        cache_dir: str = "./data_cache/calculations",
        max_memory_mb: int = 512,
        default_ttl_seconds: int = 3600,
        enable_compression: bool = True
    ):
        """
        Initialize the calculation cache.
        
        Args:
            cache_dir: Directory for persistent cache storage
            max_memory_mb: Maximum memory usage in MB
            default_ttl_seconds: Default time-to-live for cache entries
            enable_compression: Whether to compress stored results
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_compression = enable_compression
        
        # In-memory cache: {cache_key: CacheEntry}
        self._cache: Dict[str, CacheEntry] = {}
        
        # Dependency graph: {dependency: set(cache_keys)}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance metrics
        self._metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'invalidations': 0,
            'computations_saved': 0,
            'total_computation_time_saved': 0.0,
            'dependency_invalidations': 0
        }
        self._metrics_lock = threading.Lock()
        
        # Load existing cache from disk
        self._load_cache_index()
        
        logger.info(f"CalculationCache initialized with {len(self._cache)} entries")
    
    def get_result(
        self, 
        symbol: str, 
        calculation_id: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get a cached calculation result.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            calculation_id: Unique identifier for the calculation type
            parameters: Optional parameters that affect the calculation
            
        Returns:
            Cached result if available and valid, None otherwise
        """
        cache_key = self._generate_cache_key(symbol, calculation_id, parameters)
        
        with self._lock:
            if cache_key not in self._cache:
                with self._metrics_lock:
                    self._metrics['cache_misses'] += 1
                return None
            
            entry = self._cache[cache_key]
            
            # Check if entry is valid and not expired
            if entry.status != CacheEntryStatus.VALID or entry.is_expired(self.default_ttl_seconds):
                # Remove expired/invalid entry
                self._remove_entry(cache_key)
                with self._metrics_lock:
                    self._metrics['cache_misses'] += 1
                return None
            
            # Update access statistics
            entry.mark_accessed()
            
            with self._metrics_lock:
                self._metrics['cache_hits'] += 1
                self._metrics['computations_saved'] += 1
                self._metrics['total_computation_time_saved'] += entry.computation_time_seconds
            
            logger.debug(f"Cache hit for {cache_key}")
            return entry.result
    
    def set_result(
        self,
        symbol: str,
        calculation_id: str,
        result: Any,
        dependencies: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        computation_time_seconds: float = 0.0
    ) -> bool:
        """
        Store a calculation result in the cache.
        
        Args:
            symbol: Stock symbol
            calculation_id: Unique identifier for the calculation type
            result: The calculation result to cache
            dependencies: List of data dependencies for this calculation
            parameters: Optional parameters that affect the calculation
            computation_time_seconds: Time taken to compute this result
            
        Returns:
            True if stored successfully, False otherwise
        """
        cache_key = self._generate_cache_key(symbol, calculation_id, parameters)
        dependencies = dependencies or []
        
        try:
            with self._lock:
                # Create cache entry
                entry = CacheEntry(
                    result=result,
                    timestamp=datetime.now(),
                    dependencies=set(dependencies),
                    computation_time_seconds=computation_time_seconds
                )
                
                # Compress result if enabled and beneficial
                if self.enable_compression and entry.size_bytes > 1024:  # Compress if > 1KB
                    compressed_result = self._compress_result(result)
                    if len(compressed_result) < entry.size_bytes * 0.8:  # Only if 20% smaller
                        entry.result = compressed_result
                        entry.compression_ratio = entry.size_bytes / len(compressed_result)
                        entry.size_bytes = len(compressed_result)
                
                # Update dependency graph
                self._update_dependency_graph(cache_key, dependencies)
                
                # Store entry
                self._cache[cache_key] = entry
                
                # Check memory limits and cleanup if needed
                self._cleanup_memory_if_needed()
                
                # Persist to disk if large or important
                if entry.size_bytes > 10 * 1024:  # Persist if > 10KB
                    self._persist_entry(cache_key, entry)
                
                logger.debug(f"Cached result for {cache_key} (deps: {dependencies})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cache result for {cache_key}: {e}")
            return False
    
    def invalidate_dependencies(self, symbol: str, dependency: str) -> int:
        """
        Invalidate all cache entries that depend on a specific data element.
        
        Args:
            symbol: Stock symbol
            dependency: Name of the dependency that changed
            
        Returns:
            Number of cache entries invalidated
        """
        dependency_key = f"{symbol}:{dependency}"
        
        with self._lock:
            # Find all cache entries that depend on this data
            dependent_keys = self._dependency_graph.get(dependency_key, set())
            invalidated_count = 0
            
            # Use BFS to find all transitively dependent entries
            to_invalidate = deque(dependent_keys)
            invalidated_keys = set()
            
            while to_invalidate:
                cache_key = to_invalidate.popleft()
                
                if cache_key in invalidated_keys:
                    continue
                    
                invalidated_keys.add(cache_key)
                
                if cache_key in self._cache:
                    # Mark as invalid
                    self._cache[cache_key].status = CacheEntryStatus.INVALID
                    invalidated_count += 1
                    
                    # Find entries that depend on this one
                    for dep in self._cache[cache_key].dependencies:
                        dep_key = f"{symbol}:{dep}"
                        if dep_key in self._dependency_graph:
                            to_invalidate.extend(self._dependency_graph[dep_key])
            
            with self._metrics_lock:
                self._metrics['invalidations'] += invalidated_count
                self._metrics['dependency_invalidations'] += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries due to {dependency_key} change")
            return invalidated_count
    
    def clear_cache(self, symbol: Optional[str] = None) -> int:
        """
        Clear cache entries for a specific symbol or all entries.
        
        Args:
            symbol: Stock symbol to clear (None for all)
            
        Returns:
            Number of entries cleared
        """
        with self._lock:
            if symbol is None:
                # Clear everything
                count = len(self._cache)
                self._cache.clear()
                self._dependency_graph.clear()
                self._reverse_dependencies.clear()
                logger.info(f"Cleared entire calculation cache ({count} entries)")
                return count
            else:
                # Clear symbol-specific entries
                keys_to_remove = [
                    key for key in self._cache.keys() 
                    if key.startswith(f"{symbol}:")
                ]
                
                for key in keys_to_remove:
                    self._remove_entry(key)
                
                logger.info(f"Cleared {len(keys_to_remove)} cache entries for {symbol}")
                return len(keys_to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total_size_bytes = sum(entry.size_bytes for entry in self._cache.values())
            valid_entries = sum(1 for entry in self._cache.values() 
                              if entry.status == CacheEntryStatus.VALID)
            
            # Calculate compression statistics
            compressed_entries = sum(1 for entry in self._cache.values() 
                                   if entry.compression_ratio > 1.0)
            avg_compression_ratio = (
                sum(entry.compression_ratio for entry in self._cache.values()) / 
                max(len(self._cache), 1)
            )
            
            with self._metrics_lock:
                hit_rate = (
                    self._metrics['cache_hits'] / 
                    max(1, self._metrics['cache_hits'] + self._metrics['cache_misses'])
                )
                
                stats = {
                    'cache_info': {
                        'total_entries': len(self._cache),
                        'valid_entries': valid_entries,
                        'total_size_mb': total_size_bytes / (1024 * 1024),
                        'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                        'memory_usage_percent': (total_size_bytes / self.max_memory_bytes) * 100
                    },
                    'performance': dict(self._metrics),
                    'performance_derived': {
                        'cache_hit_rate': hit_rate,
                        'avg_computation_time_saved': (
                            self._metrics['total_computation_time_saved'] / 
                            max(1, self._metrics['computations_saved'])
                        )
                    },
                    'compression': {
                        'compressed_entries': compressed_entries,
                        'compression_enabled': self.enable_compression,
                        'avg_compression_ratio': avg_compression_ratio
                    },
                    'dependencies': {
                        'dependency_count': len(self._dependency_graph),
                        'avg_dependencies_per_entry': (
                            sum(len(deps) for deps in self._dependency_graph.values()) / 
                            max(len(self._dependency_graph), 1)
                        )
                    }
                }
                
                return stats
    
    def get_dependency_info(self, symbol: str, calculation_id: str) -> Dict[str, Any]:
        """Get dependency information for a specific calculation"""
        cache_key = self._generate_cache_key(symbol, calculation_id)
        
        with self._lock:
            if cache_key not in self._cache:
                return {}
            
            entry = self._cache[cache_key]
            
            # Find what this entry depends on and what depends on it
            depends_on = list(entry.dependencies)
            depended_by = [
                key for dep_key, cache_keys in self._dependency_graph.items()
                if cache_key in cache_keys
            ]
            
            return {
                'cache_key': cache_key,
                'depends_on': depends_on,
                'depended_by': depended_by,
                'status': entry.status.value,
                'last_computed': entry.timestamp.isoformat(),
                'computation_time_seconds': entry.computation_time_seconds,
                'access_count': entry.access_count,
                'size_bytes': entry.size_bytes
            }
    
    # Private helper methods
    
    def _generate_cache_key(
        self, 
        symbol: str, 
        calculation_id: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate unique cache key for calculation"""
        key_data = {
            'symbol': symbol.upper(),
            'calculation_id': calculation_id,
            'parameters': parameters or {}
        }
        
        # Create deterministic hash of parameters
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        
        return f"{symbol.upper()}:{calculation_id}:{key_hash}"
    
    def _update_dependency_graph(self, cache_key: str, dependencies: List[str]) -> None:
        """Update the dependency graph with new relationships"""
        symbol = cache_key.split(':')[0]
        
        # Remove old dependencies for this cache key
        for dep_key, cache_keys in self._dependency_graph.items():
            cache_keys.discard(cache_key)
        
        # Add new dependencies
        for dep in dependencies:
            dep_key = f"{symbol}:{dep}"
            self._dependency_graph[dep_key].add(cache_key)
            self._reverse_dependencies[cache_key].add(dep_key)
    
    def _remove_entry(self, cache_key: str) -> None:
        """Remove a cache entry and clean up dependencies"""
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Clean up dependency graph
        for dep_key in self._reverse_dependencies.get(cache_key, set()):
            if dep_key in self._dependency_graph:
                self._dependency_graph[dep_key].discard(cache_key)
        
        if cache_key in self._reverse_dependencies:
            del self._reverse_dependencies[cache_key]
        
        # Remove from disk if exists
        self._remove_persisted_entry(cache_key)
    
    def _cleanup_memory_if_needed(self) -> None:
        """Clean up memory cache if size limit exceeded"""
        total_size = sum(entry.size_bytes for entry in self._cache.values())
        
        if total_size > self.max_memory_bytes:
            # Remove 20% of entries, prioritizing least recently used and invalid
            target_removals = int(len(self._cache) * 0.2)
            
            # Sort by priority for removal
            candidates = []
            for cache_key, entry in self._cache.items():
                score = 0
                
                # Higher score = higher priority for removal
                if entry.status != CacheEntryStatus.VALID:
                    score += 1000
                
                # Time since last access (hours)
                hours_since_access = (datetime.now() - entry.last_accessed).total_seconds() / 3600
                score += hours_since_access
                
                # Inverse access frequency
                score += 100 / max(entry.access_count, 1)
                
                candidates.append((cache_key, score))
            
            # Sort by score (highest first) and remove top candidates
            candidates.sort(key=lambda x: x[1], reverse=True)
            for cache_key, _ in candidates[:target_removals]:
                self._remove_entry(cache_key)
            
            logger.info(f"Cleaned up {target_removals} cache entries to free memory")
    
    def _compress_result(self, result: Any) -> bytes:
        """Compress a result using gzip"""
        try:
            pickled = pickle.dumps(result)
            return gzip.compress(pickled)
        except Exception as e:
            logger.warning(f"Failed to compress result: {e}")
            return pickle.dumps(result)
    
    def _decompress_result(self, compressed_data: bytes) -> Any:
        """Decompress a result"""
        try:
            pickled = gzip.decompress(compressed_data)
            return pickle.loads(pickled)
        except Exception as e:
            logger.warning(f"Failed to decompress result: {e}")
            return pickle.loads(compressed_data)
    
    def _persist_entry(self, cache_key: str, entry: CacheEntry) -> None:
        """Persist cache entry to disk"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to persist cache entry {cache_key}: {e}")
    
    def _remove_persisted_entry(self, cache_key: str) -> None:
        """Remove persisted cache entry from disk"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove persisted entry {cache_key}: {e}")
    
    def _load_cache_index(self) -> None:
        """Load cache entries from disk"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_key = cache_file.stem
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    
                # Only load if not expired
                if not entry.is_expired(self.default_ttl_seconds):
                    self._cache[cache_key] = entry
                    
                    # Rebuild dependency graph
                    symbol = cache_key.split(':')[0]
                    for dep in entry.dependencies:
                        dep_key = f"{symbol}:{dep}"
                        self._dependency_graph[dep_key].add(cache_key)
                        self._reverse_dependencies[cache_key].add(dep_key)
                else:
                    # Remove expired file
                    cache_file.unlink()
                        
        except Exception as e:
            logger.warning(f"Failed to load cache index: {e}")


# Global cache instance
_global_cache: Optional[CalculationCache] = None
_cache_lock = threading.Lock()


def get_calculation_cache() -> CalculationCache:
    """Get the global calculation cache instance"""
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = CalculationCache()
    
    return _global_cache


# Convenience functions
def cache_calculation_result(
    symbol: str,
    calculation_id: str,
    result: Any,
    dependencies: Optional[List[str]] = None,
    **kwargs
) -> bool:
    """Convenience function to cache a calculation result"""
    cache = get_calculation_cache()
    return cache.set_result(symbol, calculation_id, result, dependencies, **kwargs)


def get_cached_calculation(
    symbol: str,
    calculation_id: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """Convenience function to get a cached calculation result"""
    cache = get_calculation_cache()
    return cache.get_result(symbol, calculation_id, parameters)


def invalidate_calculation_dependencies(symbol: str, dependency: str) -> int:
    """Convenience function to invalidate dependencies"""
    cache = get_calculation_cache()
    return cache.invalidate_dependencies(symbol, dependency)


# Export main classes and functions
__all__ = [
    'CalculationCache',
    'CacheEntry', 
    'CacheEntryStatus',
    'get_calculation_cache',
    'cache_calculation_result',
    'get_cached_calculation',
    'invalidate_calculation_dependencies'
]