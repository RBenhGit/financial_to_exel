"""
API Request Batching and Connection Pooling Manager
===================================================

This module provides intelligent batching of API requests and connection pooling
to optimize performance and reduce API costs while respecting rate limits.

Features:
- Request batching with configurable windows
- Connection pooling with keepalive
- Rate limiting and throttling
- Retry logic with exponential backoff
- Request deduplication
- Circuit breaker pattern
- Comprehensive metrics and monitoring

Usage Example:
>>> from api_batch_manager import ApiBatchManager
>>> batch_manager = ApiBatchManager()
>>> 
>>> # Submit requests for batching
>>> future1 = batch_manager.submit_request("yahoo", "get_price", {"symbol": "AAPL"})
>>> future2 = batch_manager.submit_request("yahoo", "get_price", {"symbol": "GOOGL"})
>>> 
>>> # Get results
>>> price1 = future1.result()
>>> price2 = future2.result()
"""

import asyncio
import logging
import threading
import time
import json
import hashlib
from collections import defaultdict, deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple, Union
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

# Configure logging
logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Status of API requests"""
    PENDING = "pending"
    BATCHED = "batched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class BatchConfig:
    """Configuration for request batching"""
    batch_window_seconds: float = 1.0      # How long to wait for batching
    max_batch_size: int = 50               # Maximum requests per batch
    max_concurrent_batches: int = 5        # Concurrent batch processing limit
    enable_deduplication: bool = True      # Remove duplicate requests
    merge_compatible_requests: bool = True  # Merge similar requests when possible


@dataclass
class ConnectionConfig:
    """Configuration for connection pooling"""
    pool_connections: int = 20             # Connection pool size
    pool_maxsize: int = 20                # Max connections per host
    max_retries: int = 3                  # Retry attempts
    backoff_factor: float = 1.0           # Exponential backoff factor
    timeout_seconds: float = 30.0         # Request timeout
    keepalive_timeout: float = 300.0      # Keep connections alive for 5 minutes


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    calls_per_minute: int = 60            # API calls per minute
    calls_per_hour: int = 1000           # API calls per hour
    calls_per_day: int = 10000           # API calls per day
    burst_allowance: int = 10            # Burst capacity above average
    
    
@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5            # Failures before opening
    success_threshold: int = 3            # Successes before closing
    timeout_seconds: float = 60.0        # Time to wait before half-open
    
    
@dataclass
class ApiRequest:
    """Individual API request with metadata"""
    request_id: str
    api_provider: str
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[Any] = None
    priority: int = 5  # 1=highest, 10=lowest
    timeout: Optional[float] = None
    retry_attempts: int = 0
    max_retries: int = 3
    submitted_time: datetime = field(default_factory=datetime.now)
    batch_compatible: bool = True  # Can this request be batched?
    cache_key: Optional[str] = None
    
    def __post_init__(self):
        """Initialize derived fields"""
        if self.cache_key is None:
            self.cache_key = self._generate_cache_key()
    
    def _generate_cache_key(self) -> str:
        """Generate cache key for request deduplication"""
        key_data = {
            'provider': self.api_provider,
            'endpoint': self.endpoint,
            'method': self.method,
            'params': self.params,
            'data': self.data
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_expired(self, max_age_seconds: float = 300.0) -> bool:
        """Check if request has expired"""
        return (datetime.now() - self.submitted_time).total_seconds() > max_age_seconds


@dataclass
class BatchedRequestGroup:
    """Group of requests that can be processed together"""
    batch_id: str
    requests: List[ApiRequest]
    api_provider: str
    endpoint: str
    created_time: datetime = field(default_factory=datetime.now)
    processing_started: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    status: RequestStatus = RequestStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    def add_request(self, request: ApiRequest) -> bool:
        """Add request to batch if compatible"""
        if (request.api_provider == self.api_provider and
            request.endpoint == self.endpoint and
            request.batch_compatible):
            self.requests.append(request)
            return True
        return False
    
    def get_batch_params(self) -> Dict[str, Any]:
        """Merge parameters from all requests for batch processing"""
        # This would be customized based on API provider capabilities
        batch_params = {}
        
        # Example: Collect all symbols for a batch quote request
        if self.endpoint == "get_quotes":
            symbols = []
            for request in self.requests:
                if "symbol" in request.params:
                    symbols.append(request.params["symbol"])
            batch_params["symbols"] = ",".join(symbols)
        
        return batch_params


class RateLimiter:
    """Multi-level rate limiter with burst handling"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._call_times: Dict[str, deque] = {
            'minute': deque(),
            'hour': deque(), 
            'day': deque()
        }
        self._burst_tokens = config.burst_allowance
        self._last_refill = time.time()
        self._lock = threading.RLock()
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without violating rate limits"""
        with self._lock:
            current_time = time.time()
            
            # Refill burst tokens
            self._refill_burst_tokens(current_time)
            
            # Clean old call records
            self._cleanup_old_calls(current_time)
            
            # Check limits
            minute_calls = len(self._call_times['minute'])
            hour_calls = len(self._call_times['hour'])
            day_calls = len(self._call_times['day'])
            
            # Use burst tokens if available
            if self._burst_tokens > 0:
                return True
            
            # Check standard limits
            return (minute_calls < self.config.calls_per_minute and
                    hour_calls < self.config.calls_per_hour and
                    day_calls < self.config.calls_per_day)
    
    def record_request(self) -> None:
        """Record that a request was made"""
        with self._lock:
            current_time = time.time()
            
            # Use burst token if available
            if self._burst_tokens > 0:
                self._burst_tokens -= 1
            
            # Record call time
            self._call_times['minute'].append(current_time)
            self._call_times['hour'].append(current_time)
            self._call_times['day'].append(current_time)
    
    def wait_time(self) -> float:
        """Get time to wait before next request"""
        if self.can_make_request():
            return 0.0
        
        with self._lock:
            # Calculate wait time based on most restrictive limit
            wait_times = []
            
            if len(self._call_times['minute']) >= self.config.calls_per_minute:
                oldest_minute = self._call_times['minute'][0]
                wait_times.append(60.0 - (time.time() - oldest_minute))
            
            if len(self._call_times['hour']) >= self.config.calls_per_hour:
                oldest_hour = self._call_times['hour'][0]
                wait_times.append(3600.0 - (time.time() - oldest_hour))
            
            if len(self._call_times['day']) >= self.config.calls_per_day:
                oldest_day = self._call_times['day'][0]
                wait_times.append(86400.0 - (time.time() - oldest_day))
            
            return max(wait_times) if wait_times else 0.0
    
    def _refill_burst_tokens(self, current_time: float) -> None:
        """Refill burst tokens based on time elapsed"""
        time_elapsed = current_time - self._last_refill
        
        # Refill 1 token per 60/calls_per_minute seconds
        refill_rate = 60.0 / self.config.calls_per_minute
        tokens_to_add = int(time_elapsed / refill_rate)
        
        if tokens_to_add > 0:
            self._burst_tokens = min(
                self.config.burst_allowance,
                self._burst_tokens + tokens_to_add
            )
            self._last_refill = current_time
    
    def _cleanup_old_calls(self, current_time: float) -> None:
        """Remove old call records that are outside the time windows"""
        # Remove calls older than 1 minute
        while (self._call_times['minute'] and
               current_time - self._call_times['minute'][0] > 60):
            self._call_times['minute'].popleft()
        
        # Remove calls older than 1 hour
        while (self._call_times['hour'] and
               current_time - self._call_times['hour'][0] > 3600):
            self._call_times['hour'].popleft()
        
        # Remove calls older than 1 day
        while (self._call_times['day'] and
               current_time - self._call_times['day'][0] > 86400):
            self._call_times['day'].popleft()


class CircuitBreaker:
    """Circuit breaker to protect against failing services"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = threading.RLock()
    
    def can_execute(self) -> bool:
        """Check if requests can be executed"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if (self.last_failure_time and
                    time.time() - self.last_failure_time > self.config.timeout_seconds):
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            
            return False
    
    def record_success(self) -> None:
        """Record successful execution"""
        with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    logger.info("Circuit breaker closed - service recovered")
    
    def record_failure(self) -> None:
        """Record failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning("Circuit breaker opened - service failing")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker re-opened - service still failing")


class ApiBatchManager:
    """
    Manages API request batching, connection pooling, and optimization.
    
    This manager intelligently batches compatible API requests, manages
    connection pools, enforces rate limits, and provides circuit breaker
    protection for external API services.
    """
    
    def __init__(
        self,
        batch_config: Optional[BatchConfig] = None,
        connection_config: Optional[ConnectionConfig] = None,
        rate_limit_config: Optional[Dict[str, RateLimitConfig]] = None,
        circuit_breaker_config: Optional[Dict[str, CircuitBreakerConfig]] = None
    ):
        """
        Initialize the API batch manager.
        
        Args:
            batch_config: Configuration for request batching
            connection_config: Configuration for connection pooling
            rate_limit_config: Rate limit configs per API provider
            circuit_breaker_config: Circuit breaker configs per API provider
        """
        self.batch_config = batch_config or BatchConfig()
        self.connection_config = connection_config or ConnectionConfig()
        
        # Per-provider configurations
        self.rate_limiters = {}
        self.circuit_breakers = {}
        
        if rate_limit_config:
            for provider, config in rate_limit_config.items():
                self.rate_limiters[provider] = RateLimiter(config)
        
        if circuit_breaker_config:
            for provider, config in circuit_breaker_config.items():
                self.circuit_breakers[provider] = CircuitBreaker(config)
        
        # Request management
        self._pending_requests: Dict[str, ApiRequest] = {}
        self._batch_groups: Dict[str, BatchedRequestGroup] = {}
        self._request_futures: Dict[str, Future] = {}
        self._request_cache: Dict[str, Tuple[Any, datetime]] = {}
        
        # Connection pools per provider
        self._sessions: Dict[str, requests.Session] = {}
        self._setup_sessions()
        
        # Threading
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._batch_processor_thread = None
        self._running = False
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'requests_submitted': 0,
            'requests_batched': 0,
            'requests_completed': 0,
            'requests_failed': 0,
            'cache_hits': 0,
            'circuit_breaker_trips': 0,
            'rate_limit_delays': 0,
            'total_response_time': 0.0,
            'batches_processed': 0
        }
        self._stats_lock = threading.Lock()
        
        logger.info("ApiBatchManager initialized")
    
    def start(self) -> None:
        """Start the batch processing system"""
        if self._running:
            return
        
        self._running = True
        
        # Start batch processor thread
        self._batch_processor_thread = threading.Thread(
            target=self._batch_processor_loop,
            name="ApiBatchProcessor",
            daemon=True
        )
        self._batch_processor_thread.start()
        
        logger.info("ApiBatchManager started")
    
    def stop(self, timeout: float = 30.0) -> None:
        """Stop the batch processing system"""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for processor thread to stop
        if self._batch_processor_thread and self._batch_processor_thread.is_alive():
            self._batch_processor_thread.join(timeout=timeout)
        
        # Shutdown executor
        self._executor.shutdown(wait=True, timeout=timeout)
        
        # Close sessions
        for session in self._sessions.values():
            session.close()
        
        logger.info("ApiBatchManager stopped")
    
    def submit_request(
        self,
        api_provider: str,
        endpoint: str,
        params: Dict[str, Any],
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        priority: int = 5,
        cache_ttl_seconds: float = 60.0
    ) -> Future:
        """
        Submit an API request for batching and processing.
        
        Args:
            api_provider: Name of the API provider
            endpoint: API endpoint
            params: Request parameters
            method: HTTP method
            headers: Additional headers
            data: Request body data
            priority: Request priority (1=highest, 10=lowest)
            cache_ttl_seconds: Cache time-to-live
            
        Returns:
            Future that will contain the response
        """
        if not self._running:
            self.start()  # Auto-start if needed
        
        # Create request
        request = ApiRequest(
            request_id=f"req_{int(time.time() * 1000000)}",
            api_provider=api_provider,
            endpoint=endpoint,
            method=method,
            params=params,
            headers=headers or {},
            data=data,
            priority=priority
        )
        
        # Check cache first
        if cache_ttl_seconds > 0:
            cached_result = self._check_cache(request.cache_key, cache_ttl_seconds)
            if cached_result is not None:
                with self._stats_lock:
                    self._stats['cache_hits'] += 1
                
                # Create completed future
                future = Future()
                future.set_result(cached_result)
                return future
        
        # Create future for result
        future = Future()
        
        with self._lock:
            self._pending_requests[request.request_id] = request
            self._request_futures[request.request_id] = future
        
        with self._stats_lock:
            self._stats['requests_submitted'] += 1
        
        logger.debug(f"Submitted request {request.request_id} to {api_provider}/{endpoint}")
        return future
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        with self._lock:
            pending_count = len(self._pending_requests)
            batch_count = len(self._batch_groups)
            active_sessions = len(self._sessions)
        
        with self._stats_lock:
            stats = dict(self._stats)
        
        # Calculate derived metrics
        total_requests = stats['requests_completed'] + stats['requests_failed']
        success_rate = (stats['requests_completed'] / max(total_requests, 1)) * 100
        avg_response_time = (stats['total_response_time'] / max(stats['requests_completed'], 1))
        batch_efficiency = (stats['requests_batched'] / max(stats['requests_submitted'], 1)) * 100
        
        # Rate limiter stats
        rate_limiter_stats = {}
        for provider, limiter in self.rate_limiters.items():
            rate_limiter_stats[provider] = {
                'can_make_request': limiter.can_make_request(),
                'wait_time_seconds': limiter.wait_time(),
                'burst_tokens': limiter._burst_tokens
            }
        
        # Circuit breaker stats
        circuit_breaker_stats = {}
        for provider, breaker in self.circuit_breakers.items():
            circuit_breaker_stats[provider] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'can_execute': breaker.can_execute()
            }
        
        return {
            'system_status': {
                'running': self._running,
                'pending_requests': pending_count,
                'active_batches': batch_count,
                'active_sessions': active_sessions
            },
            'performance': stats,
            'performance_derived': {
                'success_rate_percent': success_rate,
                'average_response_time_seconds': avg_response_time,
                'batch_efficiency_percent': batch_efficiency
            },
            'rate_limiters': rate_limiter_stats,
            'circuit_breakers': circuit_breaker_stats,
            'cache': {
                'entries': len(self._request_cache),
                'hit_rate': stats['cache_hits'] / max(stats['requests_submitted'], 1) * 100
            }
        }
    
    # Private methods
    
    def _setup_sessions(self) -> None:
        """Setup HTTP sessions with connection pooling"""
        retry_strategy = Retry(
            total=self.connection_config.max_retries,
            backoff_factor=self.connection_config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            pool_connections=self.connection_config.pool_connections,
            pool_maxsize=self.connection_config.pool_maxsize,
            max_retries=retry_strategy
        )
        
        # Create sessions for common providers (can be extended)
        providers = ['yahoo', 'alpha_vantage', 'fmp', 'polygon']
        
        for provider in providers:
            session = requests.Session()
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            self._sessions[provider] = session
    
    def _batch_processor_loop(self) -> None:
        """Main loop for processing batched requests"""
        logger.info("API batch processor started")
        
        while self._running:
            try:
                self._create_batches()
                self._process_batches()
                time.sleep(0.1)  # Small delay between processing cycles
                
            except Exception as e:
                logger.error(f"Error in batch processor loop: {e}")
                time.sleep(1.0)
        
        logger.info("API batch processor stopped")
    
    def _create_batches(self) -> None:
        """Create batches from pending requests"""
        with self._lock:
            if not self._pending_requests:
                return
            
            # Group requests by provider and endpoint
            groups = defaultdict(list)
            
            for request in self._pending_requests.values():
                if request.batch_compatible:
                    key = (request.api_provider, request.endpoint)
                    groups[key].append(request)
            
            # Create batches
            current_time = datetime.now()
            
            for (provider, endpoint), requests in groups.items():
                # Sort by priority (lower number = higher priority)
                requests.sort(key=lambda r: r.priority)
                
                # Create batches
                while requests:
                    batch_size = min(len(requests), self.batch_config.max_batch_size)
                    batch_requests = requests[:batch_size]
                    requests = requests[batch_size:]
                    
                    # Check if batch window has elapsed for oldest request
                    oldest_request = min(batch_requests, key=lambda r: r.submitted_time)
                    time_elapsed = (current_time - oldest_request.submitted_time).total_seconds()
                    
                    if (time_elapsed >= self.batch_config.batch_window_seconds or
                        len(batch_requests) >= self.batch_config.max_batch_size):
                        
                        # Create batch
                        batch_id = f"batch_{int(time.time() * 1000000)}"
                        batch_group = BatchedRequestGroup(
                            batch_id=batch_id,
                            requests=batch_requests,
                            api_provider=provider,
                            endpoint=endpoint
                        )
                        
                        self._batch_groups[batch_id] = batch_group
                        
                        # Remove from pending
                        for req in batch_requests:
                            del self._pending_requests[req.request_id]
                        
                        with self._stats_lock:
                            self._stats['requests_batched'] += len(batch_requests)
                        
                        logger.debug(f"Created batch {batch_id} with {len(batch_requests)} requests")
    
    def _process_batches(self) -> None:
        """Process ready batches"""
        with self._lock:
            ready_batches = [
                batch for batch in self._batch_groups.values()
                if batch.status == RequestStatus.PENDING
            ]
        
        # Limit concurrent batch processing
        active_batches = sum(1 for batch in self._batch_groups.values()
                           if batch.status == RequestStatus.IN_PROGRESS)
        
        available_slots = self.batch_config.max_concurrent_batches - active_batches
        
        for batch in ready_batches[:available_slots]:
            batch.status = RequestStatus.IN_PROGRESS
            batch.processing_started = datetime.now()
            
            # Submit batch for processing
            self._executor.submit(self._execute_batch, batch)
    
    def _execute_batch(self, batch: BatchedRequestGroup) -> None:
        """Execute a batch of requests"""
        provider = batch.api_provider
        
        try:
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(provider)
            if circuit_breaker and not circuit_breaker.can_execute():
                # Circuit breaker is open
                self._handle_batch_failure(batch, "Circuit breaker open")
                with self._stats_lock:
                    self._stats['circuit_breaker_trips'] += 1
                return
            
            # Check rate limiting
            rate_limiter = self.rate_limiters.get(provider)
            if rate_limiter:
                wait_time = rate_limiter.wait_time()
                if wait_time > 0:
                    logger.debug(f"Rate limit delay: {wait_time:.1f}s for {provider}")
                    time.sleep(wait_time)
                    with self._stats_lock:
                        self._stats['rate_limit_delays'] += 1
                
                rate_limiter.record_request()
            
            # Execute the batch request
            start_time = time.time()
            
            if len(batch.requests) == 1:
                # Single request
                result = self._execute_single_request(batch.requests[0])
                batch.results[batch.requests[0].request_id] = result
            else:
                # Batch request (if API supports it)
                results = self._execute_batch_request(batch)
                batch.results.update(results)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Mark as completed
            batch.status = RequestStatus.COMPLETED
            batch.completed_time = datetime.now()
            
            # Record success with circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success()
            
            # Update statistics
            with self._stats_lock:
                self._stats['requests_completed'] += len(batch.requests)
                self._stats['total_response_time'] += response_time
                self._stats['batches_processed'] += 1
            
            # Cache results and resolve futures
            self._handle_batch_success(batch)
            
            logger.debug(f"Completed batch {batch.batch_id} in {response_time:.2f}s")
            
        except Exception as e:
            # Handle batch failure
            self._handle_batch_failure(batch, str(e))
            
            # Record failure with circuit breaker
            circuit_breaker = self.circuit_breakers.get(provider)
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            with self._stats_lock:
                self._stats['requests_failed'] += len(batch.requests)
            
            logger.error(f"Batch {batch.batch_id} failed: {e}")
        
        finally:
            # Clean up
            with self._lock:
                if batch.batch_id in self._batch_groups:
                    del self._batch_groups[batch.batch_id]
    
    def _execute_single_request(self, request: ApiRequest) -> Any:
        """Execute a single API request"""
        session = self._sessions.get(request.api_provider)
        if not session:
            raise Exception(f"No session configured for provider: {request.api_provider}")
        
        # Build request parameters
        request_kwargs = {
            'method': request.method,
            'url': self._build_url(request),
            'params': request.params if request.method == 'GET' else None,
            'json': request.data if request.method != 'GET' else None,
            'headers': request.headers,
            'timeout': request.timeout or self.connection_config.timeout_seconds
        }
        
        response = session.request(**request_kwargs)
        response.raise_for_status()
        
        return response.json() if response.content else None
    
    def _execute_batch_request(self, batch: BatchedRequestGroup) -> Dict[str, Any]:
        """Execute a batch request (if supported by API)"""
        # This would be customized per API provider
        # For now, execute individual requests
        results = {}
        
        for request in batch.requests:
            try:
                result = self._execute_single_request(request)
                results[request.request_id] = result
            except Exception as e:
                batch.errors[request.request_id] = str(e)
        
        return results
    
    def _build_url(self, request: ApiRequest) -> str:
        """Build full URL for request"""
        # This would be customized per API provider
        base_urls = {
            'yahoo': 'https://query1.finance.yahoo.com',
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'fmp': 'https://financialmodelingprep.com/api/v3',
            'polygon': 'https://api.polygon.io'
        }
        
        base_url = base_urls.get(request.api_provider, 'https://api.example.com')
        return f"{base_url}/{request.endpoint.lstrip('/')}"
    
    def _handle_batch_success(self, batch: BatchedRequestGroup) -> None:
        """Handle successful batch completion"""
        for request in batch.requests:
            # Cache result
            if request.request_id in batch.results:
                result = batch.results[request.request_id]
                self._cache_result(request.cache_key, result)
                
                # Resolve future
                future = self._request_futures.get(request.request_id)
                if future:
                    future.set_result(result)
            else:
                # Request failed within batch
                error = batch.errors.get(request.request_id, "Unknown error")
                future = self._request_futures.get(request.request_id)
                if future:
                    future.set_exception(Exception(error))
            
            # Cleanup
            self._request_futures.pop(request.request_id, None)
    
    def _handle_batch_failure(self, batch: BatchedRequestGroup, error_message: str) -> None:
        """Handle batch failure"""
        batch.status = RequestStatus.FAILED
        
        for request in batch.requests:
            future = self._request_futures.get(request.request_id)
            if future:
                future.set_exception(Exception(error_message))
            
            # Cleanup
            self._request_futures.pop(request.request_id, None)
    
    def _check_cache(self, cache_key: str, ttl_seconds: float) -> Optional[Any]:
        """Check if result is cached and valid"""
        if cache_key in self._request_cache:
            result, timestamp = self._request_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < ttl_seconds:
                return result
            else:
                # Remove expired cache entry
                del self._request_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache a result"""
        self._request_cache[cache_key] = (result, datetime.now())
        
        # Limit cache size
        if len(self._request_cache) > 1000:
            # Remove oldest 20% of entries
            sorted_items = sorted(
                self._request_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            items_to_remove = len(sorted_items) // 5
            for key, _ in sorted_items[:items_to_remove]:
                del self._request_cache[key]


# Global batch manager instance
_global_batch_manager: Optional[ApiBatchManager] = None
_manager_lock = threading.Lock()


def get_api_batch_manager() -> ApiBatchManager:
    """Get the global API batch manager instance"""
    global _global_batch_manager
    
    if _global_batch_manager is None:
        with _manager_lock:
            if _global_batch_manager is None:
                _global_batch_manager = ApiBatchManager()
    
    return _global_batch_manager


# Export main classes and functions
__all__ = [
    'ApiBatchManager',
    'ApiRequest',
    'BatchConfig',
    'ConnectionConfig',
    'RateLimitConfig',
    'CircuitBreakerConfig',
    'RequestStatus',
    'get_api_batch_manager'
]