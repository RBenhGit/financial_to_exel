"""
Concurrent Watch List Performance Optimizer

This module provides optimized concurrent processing for large watch lists,
implementing parallel API calls, lazy loading, and memory management for
improved performance with 50+ stocks.

Features:
- Concurrent API price fetching with configurable thread pools
- Lazy loading with pagination for large datasets  
- Memory usage monitoring and optimization
- Performance benchmarking and metrics
- Circuit breaker pattern for API resilience
- Request batching and deduplication
"""

import asyncio
import concurrent.futures
import logging
import time
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from pathlib import Path
import threading
from collections import defaultdict, deque
import queue
import weakref

# Import existing components
from core.data_sources.real_time_price_service import RealTimePriceService, PriceData
from watch_list_manager import WatchListManager

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrent processing"""
    max_workers: int = 8                    # Thread pool size
    batch_size: int = 10                   # Stocks per batch
    timeout_seconds: float = 30.0          # Request timeout
    max_retries: int = 3                   # Retry failed requests
    backoff_factor: float = 1.5            # Exponential backoff
    circuit_breaker_threshold: int = 5     # Failures before circuit opens
    enable_request_deduplication: bool = True


@dataclass 
class LazyLoadingConfig:
    """Configuration for lazy loading"""
    page_size: int = 25                    # Items per page
    prefetch_pages: int = 1                # Pages to prefetch
    cache_pages: int = 5                   # Pages to keep in memory
    enable_virtualization: bool = True     # Virtual scrolling


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    peak_memory_mb: float = 0.0
    concurrent_requests_peak: int = 0
    cache_hit_ratio: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def total_time_seconds(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def requests_per_second(self) -> float:
        if self.total_time_seconds > 0:
            return self.total_requests / self.total_time_seconds
        return 0.0


class ConcurrentWatchListOptimizer:
    """
    High-performance watch list processor with concurrent API calls and lazy loading
    """
    
    def __init__(self, 
                 watch_list_manager: WatchListManager,
                 concurrency_config: Optional[ConcurrencyConfig] = None,
                 lazy_loading_config: Optional[LazyLoadingConfig] = None):
        """
        Initialize the concurrent optimizer
        
        Args:
            watch_list_manager: Watch list manager instance
            concurrency_config: Concurrency configuration
            lazy_loading_config: Lazy loading configuration
        """
        self.watch_list_manager = watch_list_manager
        self.concurrency_config = concurrency_config or ConcurrencyConfig()
        self.lazy_config = lazy_loading_config or LazyLoadingConfig()
        
        # Initialize price service
        self.price_service = RealTimePriceService()
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=self.concurrency_config.max_workers)
        
        # Performance monitoring
        self.metrics = PerformanceMetrics()
        self._request_times: deque = deque(maxlen=1000)
        self._memory_samples: deque = deque(maxlen=100)
        
        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_open = False
        self._circuit_breaker_last_failure = None
        
        # Request deduplication
        self._active_requests: Dict[str, concurrent.futures.Future] = {}
        self._request_lock = threading.Lock()
        
        # Lazy loading cache
        self._page_cache: Dict[str, Dict] = {}
        self._page_cache_access: Dict[str, datetime] = {}
        
        logger.info(f"ConcurrentWatchListOptimizer initialized with {self.concurrency_config.max_workers} workers")
    
    def get_watch_list_with_concurrent_prices(self, 
                                            watch_list_name: str,
                                            force_refresh: bool = False,
                                            progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[Dict]:
        """
        Get watch list data with concurrent price fetching for optimal performance
        
        Args:
            watch_list_name: Name of the watch list
            force_refresh: Force refresh prices from APIs
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict: Watch list data with current prices
        """
        try:
            # Start performance monitoring
            start_time = time.time()
            initial_memory = self._get_memory_usage()
            
            # Get base watch list data
            watch_list = self.watch_list_manager.get_watch_list(watch_list_name)
            if not watch_list or not watch_list.get('stocks'):
                logger.warning(f"Watch list '{watch_list_name}' not found or empty")
                return watch_list
            
            stocks = watch_list['stocks']
            tickers = list(set(stock['ticker'] for stock in stocks))
            
            logger.info(f"Processing {len(tickers)} unique tickers from watch list '{watch_list_name}'")
            
            # Fetch prices concurrently
            price_results = self._fetch_prices_concurrently(
                tickers, force_refresh, progress_callback
            )
            
            # Enrich stock data with concurrent results
            self._enrich_stocks_with_prices(stocks, price_results)
            
            # Update performance metrics
            end_time = time.time()
            self.metrics.end_time = datetime.now()
            processing_time = end_time - start_time
            peak_memory = max(self._memory_samples) if self._memory_samples else initial_memory
            
            # Add performance metadata
            watch_list['performance_metadata'] = {
                'processing_time_seconds': processing_time,
                'total_tickers_processed': len(tickers),
                'successful_price_fetches': len([r for r in price_results.values() if r is not None]),
                'failed_price_fetches': len([r for r in price_results.values() if r is None]),
                'requests_per_second': len(tickers) / max(processing_time, 0.001),
                'peak_memory_mb': peak_memory,
                'concurrent_processing': True,
                'force_refresh_used': force_refresh
            }
            
            logger.info(f"Concurrent processing completed in {processing_time:.2f}s for {len(tickers)} tickers")
            return watch_list
            
        except Exception as e:
            logger.error(f"Error in concurrent watch list processing: {e}")
            # Fallback to original method
            return self.watch_list_manager.get_watch_list_with_current_prices(
                watch_list_name, force_refresh
            )
    
    def _fetch_prices_concurrently(self, 
                                 tickers: List[str],
                                 force_refresh: bool = False,
                                 progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Optional[PriceData]]:
        """
        Fetch prices for multiple tickers using concurrent processing
        
        Args:
            tickers: List of ticker symbols
            force_refresh: Force refresh from APIs
            progress_callback: Progress update callback
            
        Returns:
            Dict: Mapping of ticker to PriceData or None
        """
        results = {}
        completed_count = 0
        
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                logger.warning("Circuit breaker is open, using cached data only")
                force_refresh = False
            
            # Submit concurrent tasks
            future_to_ticker = {}
            
            for ticker in tickers:
                # Check for request deduplication
                if self.concurrency_config.enable_request_deduplication:
                    with self._request_lock:
                        if ticker in self._active_requests:
                            future_to_ticker[self._active_requests[ticker]] = ticker
                            continue
                
                # Submit new request
                future = self.executor.submit(
                    self._fetch_single_price_with_retry,
                    ticker,
                    force_refresh
                )
                
                future_to_ticker[future] = ticker
                
                # Store in active requests for deduplication
                if self.concurrency_config.enable_request_deduplication:
                    with self._request_lock:
                        self._active_requests[ticker] = future
            
            # Process completed requests
            for future in as_completed(future_to_ticker, timeout=self.concurrency_config.timeout_seconds):
                ticker = future_to_ticker[future]
                
                try:
                    price_data = future.result(timeout=5.0)  # Short timeout for individual results
                    results[ticker] = price_data
                    
                    if price_data:
                        self.metrics.successful_requests += 1
                        self._record_success()
                    else:
                        self.metrics.failed_requests += 1
                        self._record_failure()
                        
                except Exception as e:
                    logger.warning(f"Failed to get price for {ticker}: {e}")
                    results[ticker] = None
                    self.metrics.failed_requests += 1
                    self._record_failure()
                
                finally:
                    completed_count += 1
                    self.metrics.total_requests += 1
                    
                    # Remove from active requests
                    if self.concurrency_config.enable_request_deduplication:
                        with self._request_lock:
                            self._active_requests.pop(ticker, None)
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(completed_count, len(tickers))
            
            # Track memory usage
            current_memory = self._get_memory_usage()
            self._memory_samples.append(current_memory)
            if current_memory > self.metrics.peak_memory_mb:
                self.metrics.peak_memory_mb = current_memory
            
            return results
            
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout occurred during concurrent price fetching for {len(tickers)} tickers")
            # Return partial results
            for ticker in tickers:
                if ticker not in results:
                    results[ticker] = None
            return results
        
        except Exception as e:
            logger.error(f"Error during concurrent price fetching: {e}")
            return {ticker: None for ticker in tickers}
    
    def _fetch_single_price_with_retry(self, ticker: str, force_refresh: bool) -> Optional[PriceData]:
        """
        Fetch price for a single ticker with retry logic
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Force refresh from API
            
        Returns:
            PriceData or None if failed
        """
        start_time = time.time()
        
        for attempt in range(self.concurrency_config.max_retries + 1):
            try:
                # Fetch price data
                price_data = self.price_service.get_detailed_price_data(ticker, force_refresh)
                
                # Record timing
                response_time = time.time() - start_time
                self._request_times.append(response_time)
                
                return price_data
                
            except Exception as e:
                if attempt < self.concurrency_config.max_retries:
                    # Exponential backoff
                    sleep_time = self.concurrency_config.backoff_factor ** attempt
                    time.sleep(sleep_time)
                    logger.debug(f"Retrying {ticker} after {sleep_time:.1f}s (attempt {attempt + 1})")
                else:
                    logger.warning(f"Failed to fetch price for {ticker} after {attempt + 1} attempts: {e}")
        
        return None
    
    def _enrich_stocks_with_prices(self, stocks: List[Dict], price_results: Dict[str, Optional[PriceData]]):
        """
        Enrich stock data with fetched price information
        
        Args:
            stocks: List of stock dictionaries to enrich
            price_results: Price data results from concurrent fetching
        """
        for stock in stocks:
            ticker = stock['ticker']
            price_data = price_results.get(ticker)
            
            if price_data:
                # Add current market data
                stock['current_market_price'] = price_data.current_price
                stock['price_last_updated'] = price_data.last_updated.isoformat()
                stock['price_source'] = price_data.source
                stock['price_cache_hit'] = price_data.cache_hit
                stock['current_volume'] = price_data.volume
                stock['current_market_cap'] = price_data.market_cap
                stock['current_change_percent'] = price_data.change_percent
                
                # Calculate updated upside/downside if we have fair value
                if stock.get('fair_value') and price_data.current_price:
                    stock['updated_upside_downside_pct'] = (
                        (stock['fair_value'] - price_data.current_price) / price_data.current_price * 100
                    )
            else:
                # Mark as failed to fetch
                stock['current_market_price'] = None
                stock['price_fetch_failed'] = True
                stock['price_last_updated'] = datetime.now().isoformat()
    
    def get_paginated_watch_list(self, 
                                watch_list_name: str,
                                page: int = 1,
                                page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Get watch list with lazy loading pagination
        
        Args:
            watch_list_name: Name of the watch list
            page: Page number (1-indexed)
            page_size: Items per page (defaults to config)
            
        Returns:
            Dict: Paginated watch list data with metadata
        """
        try:
            page_size = page_size or self.lazy_config.page_size
            cache_key = f"{watch_list_name}_page_{page}_size_{page_size}"
            
            # Check cache first
            if cache_key in self._page_cache and not self._is_page_cache_expired(cache_key):
                self._page_cache_access[cache_key] = datetime.now()
                return self._page_cache[cache_key]
            
            # Get full watch list
            watch_list = self.watch_list_manager.get_watch_list(watch_list_name)
            if not watch_list or not watch_list.get('stocks'):
                return {
                    'watch_list_name': watch_list_name,
                    'page': page,
                    'page_size': page_size,
                    'total_items': 0,
                    'total_pages': 0,
                    'stocks': [],
                    'has_next': False,
                    'has_previous': False
                }
            
            stocks = watch_list['stocks']
            total_items = len(stocks)
            total_pages = (total_items + page_size - 1) // page_size
            
            # Calculate pagination bounds
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            
            # Get page data
            page_stocks = stocks[start_idx:end_idx]
            
            # Fetch prices for current page only
            tickers = [stock['ticker'] for stock in page_stocks]
            price_results = self._fetch_prices_concurrently(tickers, force_refresh=False)
            self._enrich_stocks_with_prices(page_stocks, price_results)
            
            # Create paginated response
            paginated_data = {
                'watch_list_name': watch_list_name,
                'description': watch_list.get('description', ''),
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': total_pages,
                'stocks': page_stocks,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'lazy_loading_enabled': True,
                'cache_hit': False,
                'generated_at': datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache_page(cache_key, paginated_data)
            
            return paginated_data
            
        except Exception as e:
            logger.error(f"Error in paginated watch list retrieval: {e}")
            return {
                'watch_list_name': watch_list_name,
                'error': str(e),
                'page': page,
                'page_size': page_size,
                'stocks': []
            }
    
    def prefetch_pages(self, watch_list_name: str, current_page: int, page_size: int):
        """
        Prefetch adjacent pages for improved user experience
        
        Args:
            watch_list_name: Name of the watch list
            current_page: Current page being viewed
            page_size: Items per page
        """
        try:
            # Prefetch next pages
            for i in range(1, self.lazy_config.prefetch_pages + 1):
                next_page = current_page + i
                
                # Submit prefetch task (non-blocking)
                self.executor.submit(
                    self.get_paginated_watch_list,
                    watch_list_name,
                    next_page,
                    page_size
                )
                
        except Exception as e:
            logger.warning(f"Error prefetching pages: {e}")
    
    def _cache_page(self, cache_key: str, data: Dict[str, Any]):
        """Cache page data with LRU eviction"""
        self._page_cache[cache_key] = data
        self._page_cache_access[cache_key] = datetime.now()
        
        # Evict old pages if cache is full
        if len(self._page_cache) > self.lazy_config.cache_pages:
            oldest_key = min(self._page_cache_access.keys(), 
                           key=lambda k: self._page_cache_access[k])
            del self._page_cache[oldest_key]
            del self._page_cache_access[oldest_key]
    
    def _is_page_cache_expired(self, cache_key: str) -> bool:
        """Check if page cache has expired"""
        if cache_key not in self._page_cache_access:
            return True
        
        cache_age = datetime.now() - self._page_cache_access[cache_key]
        return cache_age > timedelta(minutes=5)  # 5 minute cache
    
    def _record_success(self):
        """Record successful API call for circuit breaker"""
        self._circuit_breaker_failures = 0
        if self._circuit_breaker_open:
            logger.info("Circuit breaker closed after successful request")
            self._circuit_breaker_open = False
    
    def _record_failure(self):
        """Record failed API call for circuit breaker"""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.now()
        
        if (self._circuit_breaker_failures >= self.concurrency_config.circuit_breaker_threshold 
            and not self._circuit_breaker_open):
            logger.warning("Circuit breaker opened due to repeated failures")
            self._circuit_breaker_open = True
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self._circuit_breaker_open:
            return False
        
        # Auto-close after 5 minutes
        if (self._circuit_breaker_last_failure and 
            datetime.now() - self._circuit_breaker_last_failure > timedelta(minutes=5)):
            logger.info("Circuit breaker auto-closed after timeout")
            self._circuit_breaker_open = False
            self._circuit_breaker_failures = 0
            return False
        
        return True
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        # Update calculated fields
        if self._request_times:
            self.metrics.average_response_time = sum(self._request_times) / len(self._request_times)
        
        if self.metrics.total_requests > 0:
            self.metrics.cache_hit_ratio = self.metrics.successful_requests / self.metrics.total_requests
            
        return self.metrics
    
    def optimize_memory(self):
        """Perform memory optimization"""
        try:
            # Clear old page cache
            current_time = datetime.now()
            expired_keys = [
                key for key, access_time in self._page_cache_access.items()
                if current_time - access_time > timedelta(minutes=10)
            ]
            
            for key in expired_keys:
                self._page_cache.pop(key, None)
                self._page_cache_access.pop(key, None)
            
            # Clear old request times
            if len(self._request_times) > 500:
                # Keep only recent half
                self._request_times = deque(list(self._request_times)[-500:], maxlen=1000)
            
            # Force garbage collection
            gc.collect()
            
            logger.debug(f"Memory optimization completed. Cleared {len(expired_keys)} expired cache entries.")
            
        except Exception as e:
            logger.warning(f"Error during memory optimization: {e}")
    
    def shutdown(self):
        """Cleanup and shutdown the optimizer"""
        try:
            self.executor.shutdown(wait=True, timeout=30)
            self._page_cache.clear()
            self._page_cache_access.clear()
            self._active_requests.clear()
            logger.info("ConcurrentWatchListOptimizer shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def create_optimized_watch_list_manager(watch_list_manager: WatchListManager) -> ConcurrentWatchListOptimizer:
    """
    Factory function to create optimized watch list manager with performance tuning
    
    Args:
        watch_list_manager: Existing watch list manager
        
    Returns:
        ConcurrentWatchListOptimizer: Optimized manager instance
    """
    # Configure for optimal performance
    concurrency_config = ConcurrencyConfig(
        max_workers=min(8, (psutil.cpu_count() or 4) * 2),  # Adapt to CPU
        batch_size=15,  # Optimal batch size for most APIs
        timeout_seconds=45.0,  # Generous timeout for stability
        max_retries=2,  # Quick retries
        circuit_breaker_threshold=3  # Quick circuit breaking
    )
    
    lazy_config = LazyLoadingConfig(
        page_size=20,  # Good balance for UI performance
        prefetch_pages=2,  # Aggressive prefetching
        cache_pages=10   # Generous caching
    )
    
    return ConcurrentWatchListOptimizer(
        watch_list_manager=watch_list_manager,
        concurrency_config=concurrency_config,
        lazy_loading_config=lazy_config
    )