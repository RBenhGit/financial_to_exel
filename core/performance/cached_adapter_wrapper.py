"""
Cached Adapter Wrapper
======================

Wraps data adapters with intelligent caching from the performance framework.
Provides transparent caching layer for all data adapter calls.

Features:
---------
- Automatic caching of adapter responses
- Cache-aware adapter interface
- Connection pooling integration
- Performance tracking
- Intelligent TTL based on data type
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from .performance_framework import get_performance_framework, track_performance, PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class AdapterCallMetadata:
    """Metadata for adapter calls"""
    adapter_name: str
    method_name: str
    ticker: str
    data_type: str
    cache_hit: bool
    execution_time_ms: float
    timestamp: datetime


class CachedAdapterWrapper:
    """
    Wrapper that adds intelligent caching to any data adapter.

    This wrapper intercepts adapter calls and:
    1. Checks the cache first
    2. Falls back to the adapter if cache miss
    3. Caches the response with appropriate TTL
    4. Tracks performance metrics
    """

    def __init__(
        self,
        adapter: Any,
        adapter_name: str = "unknown",
        enable_caching: bool = True
    ):
        """
        Initialize the cached adapter wrapper.

        Args:
            adapter: The adapter instance to wrap
            adapter_name: Name for tracking purposes
            enable_caching: Whether to enable caching
        """
        self.adapter = adapter
        self.adapter_name = adapter_name
        self.enable_caching = enable_caching
        self.framework = get_performance_framework()

        logger.info(f"Initialized cached wrapper for {adapter_name} adapter")

    def fetch_fundamentals(
        self,
        ticker: str,
        force_refresh: bool = False,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental data with caching.

        Args:
            ticker: Stock ticker symbol
            force_refresh: Force fresh data from adapter
            **kwargs: Additional parameters

        Returns:
            Fundamental data dictionary or None
        """
        return self._cached_call(
            method_name="fetch_fundamentals",
            data_type="fundamentals",
            ticker=ticker,
            force_refresh=force_refresh,
            adapter_method=self.adapter.fetch_fundamentals,
            ttl_hours=24.0,
            **kwargs
        )

    def fetch_price_data(
        self,
        ticker: str,
        force_refresh: bool = False,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch price data with caching.

        Args:
            ticker: Stock ticker symbol
            force_refresh: Force fresh data from adapter
            **kwargs: Additional parameters

        Returns:
            Price data dictionary or None
        """
        return self._cached_call(
            method_name="fetch_price_data",
            data_type="price",
            ticker=ticker,
            force_refresh=force_refresh,
            adapter_method=self.adapter.fetch_price_data,
            ttl_hours=1.0,  # Price data changes frequently
            **kwargs
        )

    def fetch_market_data(
        self,
        ticker: str,
        force_refresh: bool = False,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch market data with caching.

        Args:
            ticker: Stock ticker symbol
            force_refresh: Force fresh data from adapter
            **kwargs: Additional parameters

        Returns:
            Market data dictionary or None
        """
        return self._cached_call(
            method_name="fetch_market_data",
            data_type="market_data",
            ticker=ticker,
            force_refresh=force_refresh,
            adapter_method=self.adapter.fetch_market_data,
            ttl_hours=6.0,
            **kwargs
        )

    def _cached_call(
        self,
        method_name: str,
        data_type: str,
        ticker: str,
        force_refresh: bool,
        adapter_method: Callable,
        ttl_hours: float,
        **kwargs
    ) -> Optional[Any]:
        """
        Generic cached call implementation.

        Args:
            method_name: Name of the method being called
            data_type: Type of data being fetched
            ticker: Stock ticker
            force_refresh: Whether to bypass cache
            adapter_method: The adapter method to call
            ttl_hours: Time to live for cached data
            **kwargs: Additional parameters

        Returns:
            Data from cache or adapter
        """
        start_time = time.time()
        cache_hit = False
        result = None

        try:
            # Check cache first (unless force_refresh)
            if self.enable_caching and not force_refresh:
                result = self.framework.get_cached_adapter_response(
                    ticker=ticker,
                    data_type=data_type,
                    parameters=kwargs
                )

                if result is not None:
                    cache_hit = True
                    logger.debug(f"Cache hit for {ticker} {data_type}")

            # Cache miss or force refresh - call adapter
            if result is None:
                logger.debug(f"Cache miss for {ticker} {data_type}, calling adapter")
                result = adapter_method(ticker, **kwargs)

                # Cache the result
                if result is not None and self.enable_caching:
                    self.framework.cache_adapter_response(
                        ticker=ticker,
                        data_type=data_type,
                        data=result,
                        ttl_hours=ttl_hours,
                        parameters=kwargs
                    )

            execution_time_ms = (time.time() - start_time) * 1000

            # Track metrics
            if self.framework.enable_monitoring:
                self.framework._record_metric(PerformanceMetrics(
                    operation_name=f"{self.adapter_name}.{method_name}",
                    execution_time_ms=execution_time_ms,
                    cache_hit=cache_hit,
                    layer_used="adapter_response",
                    metadata={
                        "ticker": ticker,
                        "data_type": data_type,
                        "adapter": self.adapter_name
                    }
                ))

            return result

        except Exception as e:
            logger.error(f"Error in cached adapter call {method_name} for {ticker}: {e}")
            raise

    def invalidate_cache(self, ticker: Optional[str] = None, data_type: Optional[str] = None):
        """
        Invalidate cached data for this adapter.

        Args:
            ticker: Optional ticker to scope invalidation
            data_type: Optional data type to scope invalidation
        """
        if ticker and data_type:
            trigger = f"{data_type}:{ticker}"
        elif data_type:
            trigger = f"{data_type}:*"
        else:
            trigger = "*"

        self.framework.invalidate_caches(trigger=trigger, ticker=ticker)
        logger.info(f"Invalidated cache for {self.adapter_name}: {trigger}")

    def __getattr__(self, name: str):
        """
        Pass through any other method calls to the underlying adapter.
        """
        return getattr(self.adapter, name)


class BatchAdapterWrapper:
    """
    Wrapper for batch operations across multiple symbols.

    Provides parallel fetching with intelligent caching and connection pooling.
    """

    def __init__(
        self,
        adapter: Any,
        adapter_name: str = "batch_adapter",
        max_workers: int = 5
    ):
        """
        Initialize batch adapter wrapper.

        Args:
            adapter: The adapter instance to wrap
            adapter_name: Name for tracking
            max_workers: Maximum parallel workers
        """
        self.cached_adapter = CachedAdapterWrapper(adapter, adapter_name)
        self.max_workers = max_workers
        self.framework = get_performance_framework()

        logger.info(f"Initialized batch adapter with {max_workers} workers")

    @track_performance("batch_fundamentals_fetch")
    def fetch_fundamentals_batch(
        self,
        tickers: List[str],
        force_refresh: bool = False,
        **kwargs
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch fundamentals for multiple tickers in parallel.

        Args:
            tickers: List of ticker symbols
            force_refresh: Force fresh data
            **kwargs: Additional parameters

        Returns:
            Dictionary mapping ticker to fundamental data
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all fetch tasks
            future_to_ticker = {
                executor.submit(
                    self.cached_adapter.fetch_fundamentals,
                    ticker,
                    force_refresh,
                    **kwargs
                ): ticker
                for ticker in tickers
            }

            # Collect results as they complete
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    results[ticker] = data
                except Exception as e:
                    logger.error(f"Error fetching fundamentals for {ticker}: {e}")
                    results[ticker] = None

        logger.info(f"Batch fetch completed: {len(results)}/{len(tickers)} successful")
        return results

    @track_performance("batch_price_fetch")
    def fetch_price_data_batch(
        self,
        tickers: List[str],
        force_refresh: bool = False,
        **kwargs
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch price data for multiple tickers in parallel.

        Args:
            tickers: List of ticker symbols
            force_refresh: Force fresh data
            **kwargs: Additional parameters

        Returns:
            Dictionary mapping ticker to price data
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    self.cached_adapter.fetch_price_data,
                    ticker,
                    force_refresh,
                    **kwargs
                ): ticker
                for ticker in tickers
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    results[ticker] = data
                except Exception as e:
                    logger.error(f"Error fetching price for {ticker}: {e}")
                    results[ticker] = None

        return results


__all__ = [
    'CachedAdapterWrapper',
    'BatchAdapterWrapper',
    'AdapterCallMetadata'
]
