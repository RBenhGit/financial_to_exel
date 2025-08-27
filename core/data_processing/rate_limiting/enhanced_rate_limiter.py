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
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any, List
from enum import Enum
import re
from contextlib import contextmanager

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
    """Thread-safe request queue with rate limiting"""
    
    def __init__(self, max_size: int = 100, timeout: float = 60.0):
        self.max_size = max_size
        self.timeout = timeout
        self._queue = queue.Queue(maxsize=max_size)
        self._last_request_time = 0.0
        self._lock = threading.Lock()
    
    def enqueue_request(self, request_func: Callable, *args, **kwargs) -> Any:
        """Add request to queue and execute when ready"""
        try:
            # Put the request in queue
            request_item = (request_func, args, kwargs, threading.Event())
            self._queue.put(request_item, timeout=self.timeout)
            
            # Wait for request to be processed
            event = request_item[3]
            if event.wait(timeout=self.timeout):
                return getattr(request_item, 'result', None)
            else:
                raise TimeoutError(f"Request timed out after {self.timeout} seconds")
                
        except queue.Full:
            raise OverflowError(f"Request queue is full (max size: {self.max_size})")
    
    def process_queue(self, min_spacing: float = 0.5):
        """Process queued requests with proper spacing"""
        while True:
            try:
                request_func, args, kwargs, event = self._queue.get(timeout=1.0)
                
                # Ensure minimum spacing between requests
                with self._lock:
                    current_time = time.time()
                    time_since_last = current_time - self._last_request_time
                    if time_since_last < min_spacing:
                        sleep_time = min_spacing - time_since_last
                        time.sleep(sleep_time)
                    
                    self._last_request_time = time.time()
                
                # Execute the request
                try:
                    result = request_func(*args, **kwargs)
                    setattr(request_func, 'result', result)
                except Exception as e:
                    setattr(request_func, 'result', e)
                finally:
                    event.set()
                    self._queue.task_done()
                    
            except queue.Empty:
                continue


class EnhancedRateLimiter:
    """Enhanced rate limiting manager with circuit breaker, queuing, and adaptive delays"""
    
    def __init__(self):
        self.config = get_api_config()
        self.cache_config = get_cache_config()
        
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
                timeout=self.config.queue_timeout
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