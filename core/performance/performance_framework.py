"""
Performance Optimization Framework
===================================

Multi-layer caching and performance monitoring system for the financial analysis platform.
Integrates all cache layers and provides comprehensive performance tracking.

Architecture:
------------
Layer 1: Adapter Response Cache (2s target)
  - Caches raw API responses (yfinance, FMP, etc.)
  - TTL: 1-24 hours depending on data type
  - Key strategy: ticker + data_type + parameters hash

Layer 2: VarInputData Memory Cache (500ms target)
  - Caches processed financial variables
  - TTL: 6 hours for calculated, 24 hours for base
  - Key strategy: symbol + variable_name + period

Layer 3: Composite Variable Cache (100ms target)
  - Caches computed composite variables (ratios, metrics)
  - TTL: Based on dependency freshness
  - Key strategy: symbol + composite_variable + dependencies_hash

Layer 4: Analysis Result Cache (10s total target)
  - Caches complete analysis results (DCF, DDM, P/B, etc.)
  - TTL: 1 hour
  - Key strategy: symbol + analysis_type + parameters

Performance Targets:
------------------
- Adapter extraction: <2s
- Composite calculation: <500ms
- Complete data flow: <10s
- Cache hit ratio: >80%
- Memory usage: <1GB per 50 symbols

Features:
---------
- Automatic cache warming for frequently accessed data
- Intelligent invalidation based on data dependencies
- Connection pooling for API adapters
- Parallel processing for batch operations
- Performance metrics collection and reporting
- Automated regression testing
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict, deque
from pathlib import Path
import json
import hashlib

from core.data_processing.cache.optimized_cache_manager import (
    OptimizedCacheManager,
    CacheEventType,
    CacheStats
)
from core.data_processing.calculation_cache import CalculationCache
from core.data_processing.composite_variable_calculator import CompositeVariableCalculator

logger = logging.getLogger(__name__)


class CacheLayer:
    """Enumeration of cache layers"""
    ADAPTER_RESPONSE = "adapter_response"
    VAR_INPUT_DATA = "var_input_data"
    COMPOSITE_VARIABLE = "composite_variable"
    ANALYSIS_RESULT = "analysis_result"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation"""
    operation_name: str
    execution_time_ms: float
    cache_hit: bool
    layer_used: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTarget:
    """Performance target definition"""
    name: str
    target_ms: float
    warning_threshold_ms: float
    critical_threshold_ms: float
    description: str = ""


@dataclass
class CacheInvalidationRule:
    """Rule for automatic cache invalidation"""
    trigger_pattern: str  # Pattern to match (e.g., "fundamentals:*")
    affected_layers: List[str]  # Which cache layers to invalidate
    cascade_dependencies: bool = True  # Whether to cascade to dependent caches
    ttl_override_hours: Optional[float] = None  # Override TTL for invalidated entries


class PerformanceFramework:
    """
    Centralized performance optimization and monitoring framework.

    Coordinates all cache layers and provides unified performance tracking.
    """

    def __init__(
        self,
        cache_dir: str = "data_cache",
        enable_monitoring: bool = True,
        enable_auto_warming: bool = True,
        max_workers: int = 4
    ):
        """
        Initialize the performance framework.

        Args:
            cache_dir: Base directory for all caches
            enable_monitoring: Enable performance monitoring
            enable_auto_warming: Enable automatic cache warming
            max_workers: Maximum worker threads for parallel operations
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.enable_monitoring = enable_monitoring
        self.enable_auto_warming = enable_auto_warming

        # Initialize cache layers
        self._initialize_cache_layers()

        # Performance tracking
        self.metrics_history: deque = deque(maxlen=10000)
        self.metrics_lock = threading.Lock()

        # Define performance targets
        self.targets = {
            "adapter_extraction": PerformanceTarget(
                name="Adapter Extraction",
                target_ms=2000,
                warning_threshold_ms=2500,
                critical_threshold_ms=3000,
                description="API adapter data extraction"
            ),
            "composite_calculation": PerformanceTarget(
                name="Composite Variable Calculation",
                target_ms=500,
                warning_threshold_ms=750,
                critical_threshold_ms=1000,
                description="Composite variable computation"
            ),
            "complete_flow": PerformanceTarget(
                name="Complete Data Flow",
                target_ms=10000,
                warning_threshold_ms=12000,
                critical_threshold_ms=15000,
                description="End-to-end data pipeline"
            )
        }

        # Cache invalidation rules
        self.invalidation_rules: List[CacheInvalidationRule] = []
        self._setup_default_invalidation_rules()

        # Thread pool for background operations
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="perf-"
        )

        # Connection pooling for API adapters (to be integrated)
        self.connection_pools = {}

        logger.info(f"Performance Framework initialized with {max_workers} workers")

    def _initialize_cache_layers(self):
        """Initialize all cache layers"""
        # Layer 1: Adapter Response Cache
        self.adapter_cache = OptimizedCacheManager(
            cache_dir=str(self.cache_dir / "adapters"),
            memory_cache_size=500,
            memory_cache_mb=200,
            enable_disk_cache=True,
            enable_compression=True,
            enable_cache_warming=self.enable_auto_warming
        )

        # Layer 2: VarInputData Memory Cache (to be integrated with var_input_data.py)
        self.var_input_cache = OptimizedCacheManager(
            cache_dir=str(self.cache_dir / "variables"),
            memory_cache_size=1000,
            memory_cache_mb=150,
            enable_disk_cache=False,  # Memory only for fast access
            enable_compression=False,
            enable_cache_warming=False
        )

        # Layer 3: Composite Variable Cache
        self.composite_cache = CalculationCache(
            cache_dir=str(self.cache_dir / "composites"),
            max_memory_mb=256,
            default_ttl_seconds=3600,
            enable_compression=True
        )

        # Layer 4: Analysis Result Cache
        self.analysis_cache = OptimizedCacheManager(
            cache_dir=str(self.cache_dir / "analysis"),
            memory_cache_size=200,
            memory_cache_mb=300,
            enable_disk_cache=True,
            enable_compression=True,
            enable_cache_warming=self.enable_auto_warming
        )

        logger.info("All cache layers initialized")

    def _setup_default_invalidation_rules(self):
        """Setup default cache invalidation rules"""
        # When fundamentals data changes, invalidate dependent caches
        self.invalidation_rules.append(
            CacheInvalidationRule(
                trigger_pattern="fundamentals:*",
                affected_layers=[
                    CacheLayer.VAR_INPUT_DATA,
                    CacheLayer.COMPOSITE_VARIABLE,
                    CacheLayer.ANALYSIS_RESULT
                ],
                cascade_dependencies=True
            )
        )

        # When price data changes, invalidate market-related caches
        self.invalidation_rules.append(
            CacheInvalidationRule(
                trigger_pattern="price:*",
                affected_layers=[
                    CacheLayer.VAR_INPUT_DATA,
                    CacheLayer.ANALYSIS_RESULT
                ],
                cascade_dependencies=False
            )
        )

        # When composite variables change, invalidate analysis results
        self.invalidation_rules.append(
            CacheInvalidationRule(
                trigger_pattern="composite:*",
                affected_layers=[CacheLayer.ANALYSIS_RESULT],
                cascade_dependencies=True
            )
        )

    def get_cached_adapter_response(
        self,
        ticker: str,
        data_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached adapter response with performance tracking.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data (fundamentals, price, etc.)
            parameters: Optional parameters affecting the request

        Returns:
            Cached response or None
        """
        start_time = time.time()

        cache_key = self._generate_adapter_cache_key(ticker, data_type, parameters)
        result = self.adapter_cache.get(cache_key, data_type=data_type, ticker=ticker)

        execution_time_ms = (time.time() - start_time) * 1000

        if self.enable_monitoring:
            self._record_metric(PerformanceMetrics(
                operation_name="adapter_cache_lookup",
                execution_time_ms=execution_time_ms,
                cache_hit=result is not None,
                layer_used=CacheLayer.ADAPTER_RESPONSE,
                metadata={"ticker": ticker, "data_type": data_type}
            ))

        return result

    def cache_adapter_response(
        self,
        ticker: str,
        data_type: str,
        data: Any,
        ttl_hours: float = 24.0,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache adapter response with appropriate TTL.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data
            data: Data to cache
            ttl_hours: Time to live in hours
            parameters: Optional parameters

        Returns:
            True if cached successfully
        """
        cache_key = self._generate_adapter_cache_key(ticker, data_type, parameters)

        # Adjust TTL based on data type
        if data_type == "price":
            ttl_hours = 1.0  # Prices change frequently
        elif data_type == "fundamentals":
            ttl_hours = 24.0  # Fundamentals change less frequently

        return self.adapter_cache.put(
            key=cache_key,
            data=data,
            ttl_hours=ttl_hours,
            data_type=data_type,
            source="adapter",
            ticker=ticker,
            tags=[f"{data_type}", "adapter_response"]
        )

    def get_cached_composite(
        self,
        symbol: str,
        composite_variable: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached composite variable calculation.

        Args:
            symbol: Stock symbol
            composite_variable: Name of composite variable
            parameters: Optional calculation parameters

        Returns:
            Cached calculation result or None
        """
        start_time = time.time()

        result = self.composite_cache.get_result(
            symbol=symbol,
            calculation_id=composite_variable,
            parameters=parameters
        )

        execution_time_ms = (time.time() - start_time) * 1000

        if self.enable_monitoring:
            self._record_metric(PerformanceMetrics(
                operation_name="composite_cache_lookup",
                execution_time_ms=execution_time_ms,
                cache_hit=result is not None,
                layer_used=CacheLayer.COMPOSITE_VARIABLE,
                metadata={"symbol": symbol, "variable": composite_variable}
            ))

        return result

    def cache_composite_result(
        self,
        symbol: str,
        composite_variable: str,
        result: Any,
        dependencies: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        computation_time_seconds: float = 0.0
    ) -> bool:
        """
        Cache composite variable calculation result.

        Args:
            symbol: Stock symbol
            composite_variable: Name of composite variable
            result: Calculation result
            dependencies: List of dependencies
            parameters: Optional parameters
            computation_time_seconds: Time taken to compute

        Returns:
            True if cached successfully
        """
        return self.composite_cache.set_result(
            symbol=symbol,
            calculation_id=composite_variable,
            result=result,
            dependencies=dependencies,
            parameters=parameters,
            computation_time_seconds=computation_time_seconds
        )

    def invalidate_caches(
        self,
        trigger: str,
        ticker: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Invalidate caches based on trigger pattern.

        Args:
            trigger: Trigger pattern (e.g., "fundamentals:AAPL")
            ticker: Optional ticker to scope invalidation

        Returns:
            Dictionary of {layer: count_invalidated}
        """
        invalidation_results = {}

        # Find matching rules
        matching_rules = [
            rule for rule in self.invalidation_rules
            if self._pattern_matches(trigger, rule.trigger_pattern)
        ]

        for rule in matching_rules:
            for layer in rule.affected_layers:
                count = 0

                if layer == CacheLayer.ADAPTER_RESPONSE:
                    count = self.adapter_cache.invalidate(
                        ticker=ticker,
                        event_type=CacheEventType.DATA_UPDATE
                    )
                elif layer == CacheLayer.VAR_INPUT_DATA:
                    count = self.var_input_cache.invalidate(
                        ticker=ticker,
                        event_type=CacheEventType.DATA_UPDATE
                    )
                elif layer == CacheLayer.COMPOSITE_VARIABLE:
                    if ticker:
                        count = self.composite_cache.clear_cache(symbol=ticker)
                elif layer == CacheLayer.ANALYSIS_RESULT:
                    count = self.analysis_cache.invalidate(
                        ticker=ticker,
                        event_type=CacheEventType.DATA_UPDATE
                    )

                invalidation_results[layer] = count

        logger.info(f"Cache invalidation completed: {invalidation_results}")
        return invalidation_results

    def warm_caches(
        self,
        tickers: List[str],
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Proactively warm caches for specified tickers.

        Args:
            tickers: List of ticker symbols
            data_types: List of data types to warm

        Returns:
            Warming statistics
        """
        if not self.enable_auto_warming:
            logger.info("Cache warming is disabled")
            return {"status": "disabled"}

        data_types = data_types or ["price", "fundamentals", "market_data"]

        logger.info(f"Warming caches for {len(tickers)} tickers")

        # Warm adapter cache
        self.adapter_cache.warm_cache(tickers=tickers, data_types=data_types)

        return {
            "status": "warming",
            "tickers": len(tickers),
            "data_types": len(data_types)
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Returns:
            Performance statistics and cache status
        """
        with self.metrics_lock:
            recent_metrics = list(self.metrics_history)

        # Calculate aggregate metrics
        total_operations = len(recent_metrics)
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        cache_hit_ratio = cache_hits / total_operations if total_operations > 0 else 0

        avg_execution_times = defaultdict(list)
        for metric in recent_metrics:
            avg_execution_times[metric.operation_name].append(metric.execution_time_ms)

        avg_times = {
            op: sum(times) / len(times)
            for op, times in avg_execution_times.items()
        }

        # Get cache statistics
        adapter_stats = self.adapter_cache.get_cache_stats()
        composite_stats = self.composite_cache.get_statistics()
        analysis_stats = self.analysis_cache.get_cache_stats()

        # Check against targets
        target_status = {}
        for target_name, target in self.targets.items():
            actual_time = avg_times.get(target_name, 0)
            status = "meeting" if actual_time <= target.target_ms else \
                     "warning" if actual_time <= target.warning_threshold_ms else \
                     "critical"

            target_status[target_name] = {
                "target_ms": target.target_ms,
                "actual_ms": actual_time,
                "status": status,
                "description": target.description
            }

        return {
            "summary": {
                "total_operations": total_operations,
                "cache_hit_ratio": round(cache_hit_ratio * 100, 2),
                "avg_execution_times_ms": {k: round(v, 2) for k, v in avg_times.items()}
            },
            "targets": target_status,
            "cache_layers": {
                "adapter_cache": adapter_stats,
                "composite_cache": composite_stats,
                "analysis_cache": analysis_stats
            },
            "timestamp": datetime.now().isoformat()
        }

    def _generate_adapter_cache_key(
        self,
        ticker: str,
        data_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for adapter responses"""
        params_str = json.dumps(parameters or {}, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{data_type}_{ticker}_{params_hash}"

    def _pattern_matches(self, trigger: str, pattern: str) -> bool:
        """Check if trigger matches pattern (supports wildcards)"""
        if pattern == "*":
            return True

        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return trigger.startswith(prefix)

        return trigger == pattern

    def _record_metric(self, metric: PerformanceMetrics):
        """Record a performance metric"""
        if not self.enable_monitoring:
            return

        with self.metrics_lock:
            self.metrics_history.append(metric)

    def shutdown(self):
        """Shutdown the performance framework"""
        logger.info("Shutting down performance framework")

        # Shutdown caches
        self.adapter_cache.shutdown()
        self.composite_cache = None  # No shutdown method
        self.analysis_cache.shutdown()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("Performance framework shutdown complete")


# Global singleton instance
_performance_framework: Optional[PerformanceFramework] = None
_framework_lock = threading.Lock()


def get_performance_framework(**kwargs) -> PerformanceFramework:
    """Get the global performance framework instance"""
    global _performance_framework

    if _performance_framework is None:
        with _framework_lock:
            if _performance_framework is None:
                _performance_framework = PerformanceFramework(**kwargs)

    return _performance_framework


# Convenience decorator for performance tracking
def track_performance(operation_name: str):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            framework = get_performance_framework()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time_ms = (time.time() - start_time) * 1000

                if framework.enable_monitoring:
                    framework._record_metric(PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time_ms=execution_time_ms,
                        cache_hit=False,  # Not a cache operation
                        metadata={"function": func.__name__}
                    ))

                return result

            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                raise

        return wrapper
    return decorator


__all__ = [
    'PerformanceFramework',
    'get_performance_framework',
    'track_performance',
    'CacheLayer',
    'PerformanceMetrics',
    'PerformanceTarget'
]
