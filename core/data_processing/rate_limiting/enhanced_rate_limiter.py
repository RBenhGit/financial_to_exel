"""
Enhanced Rate Limiting Manager
=============================

Comprehensive rate limiting solution for Yahoo Finance and other APIs with:
- Adaptive rate limiting with dynamic delay adjustment
- Circuit breaker pattern for API health management
- Request queuing system to serialize API calls
- Request spacing with minimum delays
- Intelligent fallback source selection
"""

import time
import random
import threading
import queue
import logging
import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any, List
from enum import Enum
import re
from contextlib import contextmanager
from pathlib import Path
from urllib3.poolmanager import PoolManager
from urllib3.util.retry import Retry

from config.settings import get_api_config, get_cache_config

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # API disabled due to failures
    HALF_OPEN = "half_open"  # Testing if API has recovered


@dataclass
class RateLimitInfo:
    """Rate limit information extracted from API responses"""
    requests_remaining: Optional[int] = None
    requests_limit: Optional[int] = None
    reset_time: Optional[datetime] = None
    retry_after: Optional[int] = None
    backoff_seconds: Optional[float] = None


@dataclass
class ApiHealthMetrics:
    """API health tracking metrics"""
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    average_response_time: float = 0.0
    rate_limited_count: int = 0


@dataclass
class QuotaInfo:
    """API quota tracking information"""
    requests_made: int = 0
    requests_limit: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    reset_time: Optional[datetime] = None
    remaining_requests: int = 0

    def is_quota_exceeded(self) -> bool:
        """Check if quota is exceeded"""
        return self.requests_made >= self.requests_limit

    def get_time_until_reset(self) -> Optional[timedelta]:
        """Get time until quota resets"""
        if self.reset_time:
            now = datetime.now()
            if self.reset_time > now:
                return self.reset_time - now
        return None


class ConnectionPool:
    """HTTP connection pool manager for API providers"""

    def __init__(self, config):
        self.config = config
        self._pools: Dict[str, PoolManager] = {}
        self._sessions: Dict[str, requests.Session] = {}
        self._lock = threading.Lock()

        # Initialize pools for each provider
        if config.connection_pool_enabled:
            self._init_pools()

    def _init_pools(self):
        """Initialize connection pools for each API provider"""
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True
        )

        pool_config = {
            'num_pools': 10,
            'maxsize': self.config.pool_maxsize,
            'block': self.config.pool_block,
            'retries': retry_strategy
        }

        providers = ['yahoo_finance', 'alpha_vantage', 'fmp', 'polygon']

        for provider in providers:
            with self._lock:
                # Create urllib3 pool
                self._pools[provider] = PoolManager(**pool_config)

                # Create requests session with pool
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=self.config.max_pool_connections,
                    pool_maxsize=self.config.max_pool_connections_per_host,
                    max_retries=retry_strategy
                )
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                session.timeout = self.config.network_timeout

                self._sessions[provider] = session

                logger.info(f"Initialized connection pool for {provider}")

    def get_session(self, provider: str) -> requests.Session:
        """Get connection pool session for provider"""
        if not self.config.connection_pool_enabled:
            # Return default session if pooling disabled
            session = requests.Session()
            session.timeout = self.config.network_timeout
            return session

        with self._lock:
            if provider not in self._sessions:
                logger.warning(f"No pool found for provider {provider}, creating default session")
                session = requests.Session()
                session.timeout = self.config.network_timeout
                return session

            return self._sessions[provider]

    def get_pool_stats(self) -> Dict[str, Dict]:
        """Get connection pool statistics"""
        stats = {}

        if not self.config.connection_pool_enabled:
            return {"connection_pooling": "disabled"}

        with self._lock:
            for provider, pool in self._pools.items():
                # Get basic pool statistics
                pool_info = {
                    "provider": provider,
                    "pool_type": type(pool).__name__,
                    "config_maxsize": self.config.pool_maxsize,
                    "initialized": pool is not None
                }

                # Get session statistics
                session_info = {}
                if provider in self._sessions:
                    session = self._sessions[provider]
                    session_info = {
                        "session_type": type(session).__name__,
                        "has_adapters": hasattr(session, 'adapters'),
                        "adapter_count": len(session.adapters) if hasattr(session, 'adapters') else 0
                    }

                pool_info["session_info"] = session_info
                stats[provider] = pool_info

        return stats

    def close_pools(self):
        """Close all connection pools"""
        with self._lock:
            for provider, session in self._sessions.items():
                try:
                    session.close()
                    logger.debug(f"Closed session for {provider}")
                except Exception as e:
                    logger.warning(f"Error closing session for {provider}: {e}")

            for provider, pool in self._pools.items():
                try:
                    pool.clear()
                    logger.debug(f"Cleared pool for {provider}")
                except Exception as e:
                    logger.warning(f"Error clearing pool for {provider}: {e}")

            self._sessions.clear()
            self._pools.clear()


class QuotaTracker:
    """Persistent quota tracking across sessions"""

    def __init__(self, config):
        self.config = config
        self.quota_info: Dict[str, QuotaInfo] = {}
        self._lock = threading.Lock()
        self.storage_file = Path(config.quota_storage_file)

        # Load existing quota data
        if config.quota_tracking_enabled:
            self._load_quota_data()
            self._init_provider_quotas()

    def _init_provider_quotas(self):
        """Initialize quota information for providers"""
        providers_config = {
            'yahoo_finance': {
                'limit': self.config.yfinance_quota_limit,
                'period': self.config.yfinance_quota_period
            },
            'alpha_vantage': {
                'limit': self.config.alpha_vantage_quota_limit,
                'period': self.config.alpha_vantage_quota_period
            },
            'fmp': {
                'limit': self.config.fmp_quota_limit,
                'period': self.config.fmp_quota_period
            },
            'polygon': {
                'limit': self.config.polygon_quota_limit,
                'period': self.config.polygon_quota_period
            }
        }

        now = datetime.now()

        for provider, settings in providers_config.items():
            if provider not in self.quota_info:
                period_start = now
                period_end = now + timedelta(seconds=settings['period'])

                self.quota_info[provider] = QuotaInfo(
                    requests_made=0,
                    requests_limit=settings['limit'],
                    period_start=period_start,
                    period_end=period_end,
                    reset_time=period_end,
                    remaining_requests=settings['limit']
                )

                logger.debug(f"Initialized quota for {provider}: {settings['limit']} requests per {settings['period']}s")

    def _load_quota_data(self):
        """Load quota data from persistent storage"""
        if not self.config.quota_persistence_enabled:
            return

        try:
            if self.storage_file.exists():
                data = json.loads(self.storage_file.read_text(encoding='utf-8'))

                for provider, quota_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if quota_data.get('period_start'):
                        quota_data['period_start'] = datetime.fromisoformat(quota_data['period_start'])
                    if quota_data.get('period_end'):
                        quota_data['period_end'] = datetime.fromisoformat(quota_data['period_end'])
                    if quota_data.get('reset_time'):
                        quota_data['reset_time'] = datetime.fromisoformat(quota_data['reset_time'])

                    self.quota_info[provider] = QuotaInfo(**quota_data)

                logger.info(f"Loaded quota data for {len(self.quota_info)} providers")

        except Exception as e:
            logger.warning(f"Failed to load quota data: {e}")
            self.quota_info = {}

    def _save_quota_data(self):
        """Save quota data to persistent storage"""
        if not self.config.quota_persistence_enabled:
            return

        try:
            # Ensure directory exists
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert quota info to JSON-serializable format
            data = {}
            for provider, quota_info in self.quota_info.items():
                data[provider] = {
                    'requests_made': quota_info.requests_made,
                    'requests_limit': quota_info.requests_limit,
                    'period_start': quota_info.period_start.isoformat() if quota_info.period_start else None,
                    'period_end': quota_info.period_end.isoformat() if quota_info.period_end else None,
                    'reset_time': quota_info.reset_time.isoformat() if quota_info.reset_time else None,
                    'remaining_requests': quota_info.remaining_requests
                }

            self.storage_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            logger.debug("Saved quota data to storage")

        except Exception as e:
            logger.error(f"Failed to save quota data: {e}")

    def can_make_request(self, provider: str) -> bool:
        """Check if request can be made within quota limits"""
        if not self.config.quota_tracking_enabled:
            return True

        with self._lock:
            if provider not in self.quota_info:
                return True

            quota = self.quota_info[provider]
            now = datetime.now()

            # Check if quota period has expired and needs reset
            if quota.reset_time and now >= quota.reset_time:
                self._reset_quota_period(provider)
                quota = self.quota_info[provider]  # Get updated quota

            # Check if quota exceeded
            if quota.is_quota_exceeded():
                time_until_reset = quota.get_time_until_reset()
                if time_until_reset:
                    logger.info(f"Quota exceeded for {provider}, resets in {time_until_reset}")
                return False

            return True

    def record_request(self, provider: str):
        """Record a request against provider quota"""
        if not self.config.quota_tracking_enabled:
            return

        with self._lock:
            if provider in self.quota_info:
                quota = self.quota_info[provider]
                quota.requests_made += 1
                quota.remaining_requests = max(0, quota.requests_limit - quota.requests_made)

                logger.debug(f"Recorded request for {provider}: {quota.requests_made}/{quota.requests_limit}")

                # Save periodically
                if quota.requests_made % 10 == 0:  # Save every 10 requests
                    self._save_quota_data()

    def _reset_quota_period(self, provider: str):
        """Reset quota period for provider"""
        if provider not in self.quota_info:
            return

        quota = self.quota_info[provider]
        now = datetime.now()

        # Calculate new period based on provider settings
        if provider == 'yahoo_finance':
            period_seconds = self.config.yfinance_quota_period
            new_limit = self.config.yfinance_quota_limit
        elif provider == 'alpha_vantage':
            period_seconds = self.config.alpha_vantage_quota_period
            new_limit = self.config.alpha_vantage_quota_limit
        elif provider == 'fmp':
            period_seconds = self.config.fmp_quota_period
            new_limit = self.config.fmp_quota_limit
        elif provider == 'polygon':
            period_seconds = self.config.polygon_quota_period
            new_limit = self.config.polygon_quota_limit
        else:
            period_seconds = 3600  # Default 1 hour
            new_limit = 100  # Default limit

        quota.requests_made = 0
        quota.requests_limit = new_limit
        quota.period_start = now
        quota.period_end = now + timedelta(seconds=period_seconds)
        quota.reset_time = quota.period_end
        quota.remaining_requests = new_limit

        logger.info(f"Reset quota period for {provider}: {new_limit} requests until {quota.reset_time}")
        self._save_quota_data()

    def get_quota_status(self) -> Dict[str, Dict]:
        """Get current quota status for all providers"""
        status = {}

        if not self.config.quota_tracking_enabled:
            return {"quota_tracking": "disabled"}

        with self._lock:
            for provider, quota in self.quota_info.items():
                time_until_reset = quota.get_time_until_reset()
                status[provider] = {
                    'requests_made': quota.requests_made,
                    'requests_limit': quota.requests_limit,
                    'remaining_requests': quota.remaining_requests,
                    'quota_exceeded': quota.is_quota_exceeded(),
                    'reset_time': quota.reset_time.isoformat() if quota.reset_time else None,
                    'time_until_reset_seconds': int(time_until_reset.total_seconds()) if time_until_reset else None,
                    'usage_percentage': round((quota.requests_made / quota.requests_limit) * 100, 1) if quota.requests_limit > 0 else 0
                }

        return status

    def force_save(self):
        """Force save quota data immediately"""
        self._save_quota_data()


class CircuitBreaker:
    """Circuit breaker implementation for API health management"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 300,
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if requests can proceed through the circuit"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if (self.last_failure_time and 
                    datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)):
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            return False
    
    def record_success(self):
        """Record a successful API call"""
        with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    logger.info("Circuit breaker transitioned to CLOSED state after recovery")
    
    def record_failure(self):
        """Record a failed API call"""
        with self._lock:
            self.failure_count += 1
            self.success_count = 0
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")


class RequestQueue:
    """Thread-safe request queue with rate limiting and connection pool integration"""

    def __init__(self, max_size: int = 100, timeout: float = 60.0, connection_pool=None):
        self.max_size = max_size
        self.timeout = timeout
        self.connection_pool = connection_pool
        self._queue = queue.Queue(maxsize=max_size)
        self._last_request_time = 0.0
        self._lock = threading.Lock()
        self._stats = {
            'requests_queued': 0,
            'requests_processed': 0,
            'requests_failed': 0,
            'average_wait_time': 0.0,
            'queue_length': 0
        }

    def enqueue_request(self, request_func: Callable, provider: str = None, *args, **kwargs) -> Any:
        """Add request to queue and execute when ready"""
        enqueue_time = time.time()

        try:
            # Put the request in queue with provider info
            request_item = (request_func, provider, args, kwargs, threading.Event(), enqueue_time)
            self._queue.put(request_item, timeout=self.timeout)

            with self._lock:
                self._stats['requests_queued'] += 1
                self._stats['queue_length'] = self._queue.qsize()

            # Wait for request to be processed
            event = request_item[4]
            if event.wait(timeout=self.timeout):
                # Calculate wait time
                wait_time = time.time() - enqueue_time
                with self._lock:
                    # Update average wait time
                    current_avg = self._stats['average_wait_time']
                    processed = self._stats['requests_processed']
                    if processed > 0:
                        self._stats['average_wait_time'] = (current_avg * processed + wait_time) / (processed + 1)
                    else:
                        self._stats['average_wait_time'] = wait_time

                return getattr(request_item, 'result', None)
            else:
                with self._lock:
                    self._stats['requests_failed'] += 1
                raise TimeoutError(f"Request timed out after {self.timeout} seconds")

        except queue.Full:
            with self._lock:
                self._stats['requests_failed'] += 1
            raise OverflowError(f"Request queue is full (max size: {self.max_size})")

    def process_queue(self, min_spacing: float = 0.5):
        """Process queued requests with proper spacing and connection pool support"""
        while True:
            try:
                request_func, provider, args, kwargs, event, enqueue_time = self._queue.get(timeout=1.0)

                # Ensure minimum spacing between requests
                with self._lock:
                    current_time = time.time()
                    time_since_last = current_time - self._last_request_time
                    if time_since_last < min_spacing:
                        sleep_time = min_spacing - time_since_last
                        time.sleep(sleep_time)

                    self._last_request_time = time.time()

                # Execute the request with connection pool if available
                try:
                    if self.connection_pool and provider:
                        # Inject session from connection pool
                        session = self.connection_pool.get_session(provider)
                        kwargs['session'] = session

                    result = request_func(*args, **kwargs)
                    setattr(request_func, 'result', result)

                    with self._lock:
                        self._stats['requests_processed'] += 1

                except Exception as e:
                    setattr(request_func, 'result', e)
                    with self._lock:
                        self._stats['requests_failed'] += 1

                finally:
                    event.set()
                    self._queue.task_done()
                    with self._lock:
                        self._stats['queue_length'] = self._queue.qsize()

            except queue.Empty:
                continue

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self._lock:
            return self._stats.copy()

    def clear_queue(self):
        """Clear all pending requests in queue"""
        with self._lock:
            while not self._queue.empty():
                try:
                    item = self._queue.get_nowait()
                    # Signal any waiting threads
                    if len(item) >= 5:
                        event = item[4]
                        event.set()
                    self._queue.task_done()
                except queue.Empty:
                    break

            self._stats['queue_length'] = 0


class EnhancedRateLimiter:
    """Enhanced rate limiting manager with circuit breaker, queuing, and adaptive delays"""

    def __init__(self):
        self.config = get_api_config()
        self.cache_config = get_cache_config()

        # Connection pooling
        self.connection_pool = ConnectionPool(self.config)

        # Quota tracking
        self.quota_tracker = QuotaTracker(self.config)

        # Circuit breakers per API source
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # API health metrics
        self.health_metrics: Dict[str, ApiHealthMetrics] = {}

        # Request queues per API source
        self.request_queues: Dict[str, RequestQueue] = {}

        # Rate limit tracking
        self.rate_limit_info: Dict[str, RateLimitInfo] = {}

        # Adaptive delays per source
        self.adaptive_delays: Dict[str, float] = {}

        # Thread locks
        self._locks: Dict[str, threading.Lock] = {}

        # Initialize default sources
        self._init_source('yahoo_finance')
        self._init_source('alpha_vantage')
        self._init_source('fmp')
        self._init_source('polygon')
    
    def _init_source(self, source: str):
        """Initialize rate limiting components for a data source"""
        if self.config.circuit_breaker_enabled:
            self.circuit_breakers[source] = CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.circuit_breaker_recovery_timeout,
                success_threshold=self.config.circuit_breaker_success_threshold
            )

        self.health_metrics[source] = ApiHealthMetrics()

        if self.config.request_queue_enabled:
            self.request_queues[source] = RequestQueue(
                max_size=self.config.max_queue_size,
                timeout=self.config.queue_timeout,
                connection_pool=self.connection_pool
            )

        self.rate_limit_info[source] = RateLimitInfo()
        self.adaptive_delays[source] = self.config.base_delay
        self._locks[source] = threading.Lock()
    
    def _extract_rate_limit_headers(self, response_headers: dict) -> RateLimitInfo:
        """Extract rate limit information from API response headers"""
        rate_info = RateLimitInfo()
        
        # Yahoo Finance headers
        if 'x-ratelimit-remaining' in response_headers:
            rate_info.requests_remaining = int(response_headers.get('x-ratelimit-remaining', 0))
        if 'x-ratelimit-limit' in response_headers:
            rate_info.requests_limit = int(response_headers.get('x-ratelimit-limit', 0))
        if 'x-ratelimit-reset' in response_headers:
            try:
                reset_timestamp = int(response_headers['x-ratelimit-reset'])
                rate_info.reset_time = datetime.fromtimestamp(reset_timestamp)
            except (ValueError, OSError):
                pass
        
        # Standard retry-after header
        if 'retry-after' in response_headers:
            try:
                rate_info.retry_after = int(response_headers['retry-after'])
                rate_info.backoff_seconds = float(rate_info.retry_after)
            except ValueError:
                # Could be HTTP-date format
                pass
        
        return rate_info
    
    def _calculate_adaptive_delay(self, source: str, attempt: int, 
                                  rate_info: Optional[RateLimitInfo] = None) -> float:
        """Calculate adaptive delay based on rate limit info and attempt number"""
        
        # Use retry-after if available
        if rate_info and rate_info.backoff_seconds:
            base_delay = rate_info.backoff_seconds
        else:
            # Use configured adaptive delay for this source
            base_delay = self.adaptive_delays[source]
        
        # Apply exponential backoff if enabled
        if self.config.dynamic_backoff_enabled and attempt > 0:
            delay = min(base_delay * (self.config.backoff_factor ** attempt), 
                       self.config.max_delay)
        else:
            delay = base_delay
        
        # Add jitter to prevent thundering herd
        if self.config.jitter_enabled:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        # Update adaptive delay for future requests
        if self.config.adaptive_rate_limiting:
            with self._locks[source]:
                self.adaptive_delays[source] = min(delay * 1.1, self.config.max_delay)
        
        return delay
    
    def _update_health_metrics(self, source: str, success: bool, 
                               response_time: float = 0.0, is_rate_limited: bool = False):
        """Update API health metrics"""
        with self._locks[source]:
            metrics = self.health_metrics[source]
            metrics.total_requests += 1
            
            if success:
                metrics.consecutive_failures = 0
                metrics.consecutive_successes += 1
                metrics.last_success_time = datetime.now()
                
                # Update average response time
                if metrics.total_requests > 1:
                    metrics.average_response_time = (
                        (metrics.average_response_time * (metrics.total_requests - 1) + response_time) 
                        / metrics.total_requests
                    )
                else:
                    metrics.average_response_time = response_time
                    
                # Reduce adaptive delay on success
                if self.config.adaptive_rate_limiting:
                    self.adaptive_delays[source] = max(
                        self.adaptive_delays[source] * 0.9, 
                        self.config.base_delay
                    )
            else:
                metrics.consecutive_successes = 0
                metrics.consecutive_failures += 1
                metrics.total_failures += 1
                metrics.last_failure_time = datetime.now()
                
                if is_rate_limited:
                    metrics.rate_limited_count += 1
    
    def can_make_request(self, source: str) -> bool:
        """Check if a request can be made to the specified source"""

        # Check quota tracker first
        if not self.quota_tracker.can_make_request(source):
            logger.info(f"Quota exceeded for {source}")
            return False

        # Check circuit breaker
        if source in self.circuit_breakers:
            if not self.circuit_breakers[source].can_proceed():
                logger.warning(f"Circuit breaker OPEN for {source} - request blocked")
                return False

        # Check if we have rate limit info suggesting we should wait
        if source in self.rate_limit_info:
            rate_info = self.rate_limit_info[source]
            if rate_info.requests_remaining is not None and rate_info.requests_remaining <= 0:
                if rate_info.reset_time and datetime.now() < rate_info.reset_time:
                    logger.info(f"Rate limit reached for {source}, waiting for reset")
                    return False

        return True
    
    @contextmanager
    def rate_limited_request(self, source: str, attempt: int = 0):
        """Context manager for making rate-limited requests"""
        start_time = time.time()
        success = False
        is_rate_limited = False

        try:
            # Check if request can proceed
            if not self.can_make_request(source):
                raise RuntimeError(f"Request to {source} blocked by rate limiter")

            # Record quota usage at start of request
            self.quota_tracker.record_request(source)

            # Apply minimum request spacing
            if self.config.min_request_spacing > 0:
                time.sleep(self.config.min_request_spacing)

            yield

            success = True

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limited = ('429' in error_str or 'rate limit' in error_str or
                             'too many requests' in error_str)

            # Extract rate limit info from error if possible
            if hasattr(e, 'response') and e.response is not None:
                rate_info = self._extract_rate_limit_headers(dict(e.response.headers))
                self.rate_limit_info[source] = rate_info

                # Calculate and apply adaptive delay
                if is_rate_limited and attempt < self.config.max_retries - 1:
                    delay = self._calculate_adaptive_delay(source, attempt, rate_info)
                    logger.info(f"Rate limited on {source}, waiting {delay:.1f}s before retry")
                    time.sleep(delay)

            raise

        finally:
            response_time = time.time() - start_time

            # Update metrics
            self._update_health_metrics(source, success, response_time, is_rate_limited)

            # Update circuit breaker
            if source in self.circuit_breakers:
                if success:
                    self.circuit_breakers[source].record_success()
                else:
                    self.circuit_breakers[source].record_failure()
    
    def get_best_available_source(self, sources: List[str]) -> Optional[str]:
        """Get the best available source based on health metrics and circuit breaker state"""
        
        available_sources = []
        
        for source in sources:
            if self.can_make_request(source):
                metrics = self.health_metrics.get(source, ApiHealthMetrics())
                
                # Calculate health score
                if metrics.total_requests > 0:
                    failure_rate = metrics.total_failures / metrics.total_requests
                    health_score = (1 - failure_rate) * 100
                    
                    # Penalize for recent failures
                    if metrics.consecutive_failures > 0:
                        health_score *= (1 - 0.1 * metrics.consecutive_failures)
                    
                    # Bonus for recent successes
                    if metrics.consecutive_successes > 0:
                        health_score *= (1 + 0.05 * metrics.consecutive_successes)
                        
                else:
                    health_score = 100  # New source, assume healthy
                
                available_sources.append((source, health_score))
        
        if available_sources:
            # Sort by health score (descending) and return the best
            available_sources.sort(key=lambda x: x[1], reverse=True)
            best_source = available_sources[0][0]
            logger.debug(f"Selected {best_source} as best available source")
            return best_source
        
        return None
    
    def get_cache_ttl_for_source(self, source: str, data_type: str = 'market_data') -> int:
        """Get appropriate cache TTL based on source health and rate limiting status"""
        
        # Check if source is experiencing issues
        is_problematic = False
        if source in self.health_metrics:
            metrics = self.health_metrics[source]
            is_problematic = (metrics.consecutive_failures > 2 or 
                            metrics.rate_limited_count > 0 or
                            (source in self.circuit_breakers and 
                             self.circuit_breakers[source].state != CircuitState.CLOSED))
        
        if is_problematic and self.cache_config.emergency_cache_extension:
            # Use extended TTL during problems
            if data_type == 'price':
                return self.cache_config.rate_limited_price_ttl
            elif data_type == 'financial_data':
                return self.cache_config.rate_limited_financial_ttl
            else:
                return self.cache_config.rate_limited_market_data_ttl
        else:
            # Use normal TTL
            if data_type == 'price':
                return self.cache_config.price_ttl
            elif data_type == 'financial_data':
                return self.cache_config.financial_data_ttl
            else:
                return self.cache_config.default_ttl
    
    def get_source_health_report(self) -> Dict[str, Dict]:
        """Get comprehensive health report for all sources"""
        report = {}

        for source, metrics in self.health_metrics.items():
            circuit_state = "N/A"
            if source in self.circuit_breakers:
                circuit_state = self.circuit_breakers[source].state.value

            failure_rate = 0
            if metrics.total_requests > 0:
                failure_rate = (metrics.total_failures / metrics.total_requests) * 100

            report[source] = {
                'circuit_breaker_state': circuit_state,
                'total_requests': metrics.total_requests,
                'total_failures': metrics.total_failures,
                'failure_rate_percent': round(failure_rate, 2),
                'consecutive_failures': metrics.consecutive_failures,
                'consecutive_successes': metrics.consecutive_successes,
                'rate_limited_count': metrics.rate_limited_count,
                'average_response_time_ms': round(metrics.average_response_time * 1000, 2),
                'adaptive_delay_seconds': round(self.adaptive_delays.get(source, 0), 2),
                'last_success': metrics.last_success_time.isoformat() if metrics.last_success_time else None,
                'last_failure': metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
            }

        return report

    def get_session(self, provider: str) -> requests.Session:
        """Get HTTP session with connection pooling for provider"""
        return self.connection_pool.get_session(provider)

    def get_quota_status(self) -> Dict[str, Dict]:
        """Get current quota status for all providers"""
        return self.quota_tracker.get_quota_status()

    def get_connection_pool_stats(self) -> Dict[str, Dict]:
        """Get connection pool statistics"""
        return self.connection_pool.get_pool_stats()

    def get_queue_stats(self) -> Dict[str, Dict]:
        """Get request queue statistics for all sources"""
        queue_stats = {}

        if not self.config.request_queue_enabled:
            return {"request_queuing": "disabled"}

        for source, queue in self.request_queues.items():
            queue_stats[source] = queue.get_stats()

        return queue_stats

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status including health, quota, connection pool, and queue stats"""
        return {
            'health_metrics': self.get_source_health_report(),
            'quota_status': self.get_quota_status(),
            'connection_pool_stats': self.get_connection_pool_stats(),
            'queue_stats': self.get_queue_stats(),
            'rate_limiter_config': {
                'connection_pooling_enabled': self.config.connection_pool_enabled,
                'quota_tracking_enabled': self.config.quota_tracking_enabled,
                'circuit_breaker_enabled': self.config.circuit_breaker_enabled,
                'adaptive_rate_limiting': self.config.adaptive_rate_limiting,
                'request_queue_enabled': self.config.request_queue_enabled,
                'max_retries': self.config.max_retries,
                'base_delay': self.config.base_delay,
                'max_delay': self.config.max_delay,
                'min_request_spacing': self.config.min_request_spacing,
                'max_pool_connections': self.config.max_pool_connections,
                'max_queue_size': self.config.max_queue_size
            }
        }

    def force_save_quota(self):
        """Force save quota data immediately"""
        self.quota_tracker.force_save()

    def close(self):
        """Clean shutdown of rate limiter components"""
        try:
            # Save quota data
            self.quota_tracker.force_save()
            logger.debug("Saved quota data during shutdown")

            # Close connection pools
            self.connection_pool.close_pools()
            logger.debug("Closed connection pools during shutdown")

        except Exception as e:
            logger.error(f"Error during rate limiter shutdown: {e}")


# Global rate limiter instance
_rate_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter() -> EnhancedRateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = EnhancedRateLimiter()
    return _rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter (useful for testing)"""
    global _rate_limiter
    _rate_limiter = None