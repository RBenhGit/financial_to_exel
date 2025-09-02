"""
Background Data Refresh System
=============================

This module provides an intelligent background refresh system that proactively
updates frequently accessed financial data to ensure optimal performance and
data freshness.

Features:
- Intelligent refresh scheduling based on access patterns
- Priority-based refresh queues
- Rate limiting and API throttling
- Configurable refresh policies per data type
- Health monitoring and error handling
- Integration with VarInputData and UniversalDataRegistry

Usage Example:
>>> from background_refresh import BackgroundRefreshManager
>>> refresh_manager = BackgroundRefreshManager()
>>> refresh_manager.start()
>>> 
>>> # Mark data for refresh
>>> refresh_manager.schedule_refresh("AAPL", "revenue", priority="high")
>>> 
>>> # Stop the refresh system
>>> refresh_manager.stop()
"""

import logging
import threading
import time
import queue
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import weakref

# Configure logging
logger = logging.getLogger(__name__)


class RefreshPriority(Enum):
    """Priority levels for data refresh"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RefreshStatus(Enum):
    """Status of refresh operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RefreshPolicy:
    """Configuration for data refresh behavior"""
    refresh_interval_hours: float = 24.0  # How often to refresh
    access_threshold: int = 5             # Min accesses before background refresh
    priority_boost_after_hours: float = 1.0  # Boost priority after this time
    max_age_hours: float = 72.0          # Max age before forced refresh
    retry_attempts: int = 3              # Number of retry attempts
    retry_delay_seconds: float = 60.0    # Delay between retries
    rate_limit_per_minute: int = 10      # API calls per minute for this data type


@dataclass
class RefreshRequest:
    """Request for data refresh"""
    symbol: str
    data_identifier: str
    priority: RefreshPriority
    scheduled_time: datetime
    policy: RefreshPolicy
    request_id: str = field(default_factory=lambda: f"req_{int(time.time() * 1000)}")
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    status: RefreshStatus = RefreshStatus.PENDING
    error_message: Optional[str] = None
    estimated_duration_seconds: float = 30.0
    
    def __post_init__(self):
        """Initialize derived fields"""
        if self.scheduled_time is None:
            self.scheduled_time = datetime.now()
    
    def get_cache_key(self) -> str:
        """Get unique cache key for this request"""
        return f"{self.symbol}:{self.data_identifier}"
    
    def should_retry(self) -> bool:
        """Check if this request should be retried"""
        return (self.status == RefreshStatus.FAILED and 
                self.attempts < self.policy.retry_attempts)
    
    def get_next_retry_time(self) -> datetime:
        """Calculate when to retry this request"""
        delay = self.policy.retry_delay_seconds * (2 ** (self.attempts - 1))  # Exponential backoff
        return datetime.now() + timedelta(seconds=delay)


class AccessTracker:
    """Tracks access patterns for intelligent refresh scheduling"""
    
    def __init__(self, tracking_window_hours: float = 24.0):
        self.tracking_window_hours = tracking_window_hours
        self._access_log: Dict[str, deque] = defaultdict(lambda: deque())
        self._lock = threading.RLock()
    
    def record_access(self, symbol: str, data_identifier: str) -> None:
        """Record an access to data"""
        key = f"{symbol}:{data_identifier}"
        current_time = datetime.now()
        
        with self._lock:
            self._access_log[key].append(current_time)
            
            # Clean old entries
            cutoff_time = current_time - timedelta(hours=self.tracking_window_hours)
            while (self._access_log[key] and 
                   self._access_log[key][0] < cutoff_time):
                self._access_log[key].popleft()
    
    def get_access_frequency(self, symbol: str, data_identifier: str) -> float:
        """Get access frequency (accesses per hour)"""
        key = f"{symbol}:{data_identifier}"
        
        with self._lock:
            if key not in self._access_log or not self._access_log[key]:
                return 0.0
            
            access_count = len(self._access_log[key])
            return access_count / self.tracking_window_hours
    
    def get_last_access_time(self, symbol: str, data_identifier: str) -> Optional[datetime]:
        """Get the time of last access"""
        key = f"{symbol}:{data_identifier}"
        
        with self._lock:
            if key not in self._access_log or not self._access_log[key]:
                return None
            return self._access_log[key][-1]
    
    def get_access_statistics(self) -> Dict[str, Any]:
        """Get comprehensive access statistics"""
        with self._lock:
            total_keys = len(self._access_log)
            active_keys = sum(1 for accesses in self._access_log.values() if accesses)
            total_accesses = sum(len(accesses) for accesses in self._access_log.values())
            
            # Top accessed data
            top_accessed = sorted(
                [(key, len(accesses)) for key, accesses in self._access_log.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'total_tracked_keys': total_keys,
                'active_keys': active_keys,
                'total_accesses': total_accesses,
                'top_accessed': top_accessed,
                'tracking_window_hours': self.tracking_window_hours
            }


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_times: deque = deque()
        self._lock = threading.Lock()
    
    def can_make_call(self) -> bool:
        """Check if we can make an API call without exceeding rate limit"""
        current_time = time.time()
        
        with self._lock:
            # Remove calls older than 1 minute
            while self.call_times and current_time - self.call_times[0] > 60:
                self.call_times.popleft()
            
            return len(self.call_times) < self.calls_per_minute
    
    def record_call(self) -> None:
        """Record an API call"""
        with self._lock:
            self.call_times.append(time.time())
    
    def wait_time_seconds(self) -> float:
        """Get seconds to wait before next call is allowed"""
        if self.can_make_call():
            return 0.0
        
        with self._lock:
            if not self.call_times:
                return 0.0
            
            # Time until oldest call is 1 minute old
            oldest_call_time = self.call_times[0]
            return max(0.0, 60.0 - (time.time() - oldest_call_time))


class BackgroundRefreshManager:
    """
    Manages background refresh of frequently accessed financial data.
    
    This system intelligently schedules data refreshes based on access patterns,
    data age, and configured policies to ensure optimal performance and data
    freshness without overwhelming external APIs.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        queue_size: int = 1000,
        default_policy: Optional[RefreshPolicy] = None
    ):
        """
        Initialize the background refresh manager.
        
        Args:
            max_workers: Maximum number of worker threads
            queue_size: Maximum size of refresh queue
            default_policy: Default refresh policy
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.default_policy = default_policy or RefreshPolicy()
        
        # Refresh queues by priority
        self._refresh_queues = {
            RefreshPriority.CRITICAL: queue.PriorityQueue(maxsize=queue_size),
            RefreshPriority.HIGH: queue.PriorityQueue(maxsize=queue_size),
            RefreshPriority.MEDIUM: queue.PriorityQueue(maxsize=queue_size),
            RefreshPriority.LOW: queue.PriorityQueue(maxsize=queue_size)
        }
        
        # Tracking and management
        self._access_tracker = AccessTracker()
        self._active_requests: Dict[str, RefreshRequest] = {}
        self._completed_requests: deque = deque(maxlen=1000)  # Keep last 1000 for stats
        self._rate_limiters: Dict[str, RateLimiter] = defaultdict(lambda: RateLimiter(60))
        self._data_policies: Dict[str, RefreshPolicy] = {}
        
        # Threading
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'requests_scheduled': 0,
            'requests_completed': 0,
            'requests_failed': 0,
            'total_refresh_time': 0.0,
            'api_calls_made': 0,
            'rate_limit_delays': 0
        }
        self._stats_lock = threading.Lock()
        
        # Callbacks
        self._refresh_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("BackgroundRefreshManager initialized")
    
    def start(self) -> None:
        """Start the background refresh system"""
        if self._running:
            logger.warning("BackgroundRefreshManager already running")
            return
        
        self._running = True
        
        # Start scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="BackgroundRefreshScheduler",
            daemon=True
        )
        self._scheduler_thread.start()
        
        logger.info("BackgroundRefreshManager started")
    
    def stop(self, timeout: float = 30.0) -> None:
        """Stop the background refresh system"""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for scheduler to stop
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=timeout)
        
        # Shutdown executor
        self._executor.shutdown(wait=True, timeout=timeout)
        
        logger.info("BackgroundRefreshManager stopped")
    
    def schedule_refresh(
        self,
        symbol: str,
        data_identifier: str,
        priority: RefreshPriority = RefreshPriority.MEDIUM,
        policy: Optional[RefreshPolicy] = None,
        delay_seconds: float = 0.0
    ) -> str:
        """
        Schedule a data refresh operation.
        
        Args:
            symbol: Stock symbol
            data_identifier: Identifier for the data to refresh
            priority: Priority level for the refresh
            policy: Custom refresh policy (uses default if None)
            delay_seconds: Delay before starting refresh
            
        Returns:
            Request ID for tracking
        """
        if not self._running:
            raise RuntimeError("BackgroundRefreshManager is not running")
        
        policy = policy or self._data_policies.get(data_identifier, self.default_policy)
        
        request = RefreshRequest(
            symbol=symbol,
            data_identifier=data_identifier,
            priority=priority,
            scheduled_time=datetime.now() + timedelta(seconds=delay_seconds),
            policy=policy
        )
        
        # Check if similar request already exists
        cache_key = request.get_cache_key()
        with self._lock:
            if cache_key in self._active_requests:
                existing_request = self._active_requests[cache_key]
                if existing_request.priority.value < priority.value:
                    # Upgrade priority
                    existing_request.priority = priority
                    logger.debug(f"Upgraded priority for {cache_key} to {priority}")
                return existing_request.request_id
            
            # Add to active requests
            self._active_requests[cache_key] = request
        
        # Add to appropriate queue
        try:
            # Priority is negative for min-heap behavior
            queue_item = (-priority.value, request.scheduled_time, request)
            self._refresh_queues[priority].put_nowait(queue_item)
            
            with self._stats_lock:
                self._stats['requests_scheduled'] += 1
            
            logger.debug(f"Scheduled refresh for {cache_key} with priority {priority}")
            return request.request_id
            
        except queue.Full:
            logger.error(f"Refresh queue full for priority {priority}")
            with self._lock:
                del self._active_requests[cache_key]
            raise RuntimeError(f"Refresh queue full for priority {priority}")
    
    def record_data_access(self, symbol: str, data_identifier: str) -> None:
        """Record access to data for intelligent refresh scheduling"""
        self._access_tracker.record_access(symbol, data_identifier)
        
        # Check if we should schedule a background refresh
        self._maybe_schedule_background_refresh(symbol, data_identifier)
    
    def set_data_policy(self, data_identifier: str, policy: RefreshPolicy) -> None:
        """Set refresh policy for a specific data type"""
        self._data_policies[data_identifier] = policy
        logger.debug(f"Set refresh policy for {data_identifier}")
    
    def add_refresh_callback(self, data_identifier: str, callback: Callable) -> None:
        """Add callback to be called when data is refreshed"""
        self._refresh_callbacks[data_identifier].append(callback)
    
    def get_refresh_status(self, request_id: str) -> Optional[RefreshRequest]:
        """Get status of a specific refresh request"""
        with self._lock:
            # Check active requests
            for request in self._active_requests.values():
                if request.request_id == request_id:
                    return request
            
            # Check completed requests
            for request in self._completed_requests:
                if request.request_id == request_id:
                    return request
            
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        with self._lock:
            active_by_priority = {
                priority.name: sum(1 for req in self._active_requests.values() 
                                 if req.priority == priority)
                for priority in RefreshPriority
            }
            
            queue_sizes = {
                priority.name: queue.qsize()
                for priority, queue in self._refresh_queues.items()
            }
        
        with self._stats_lock:
            stats = dict(self._stats)
        
        # Add derived statistics
        total_requests = stats['requests_completed'] + stats['requests_failed']
        success_rate = (stats['requests_completed'] / max(total_requests, 1)) * 100
        avg_refresh_time = (stats['total_refresh_time'] / max(stats['requests_completed'], 1))
        
        return {
            'system_status': {
                'running': self._running,
                'active_requests': len(self._active_requests),
                'completed_requests': len(self._completed_requests),
                'worker_threads': self.max_workers
            },
            'queues': queue_sizes,
            'active_by_priority': active_by_priority,
            'performance': stats,
            'performance_derived': {
                'success_rate_percent': success_rate,
                'average_refresh_time_seconds': avg_refresh_time
            },
            'access_tracking': self._access_tracker.get_access_statistics(),
            'rate_limiting': {
                'active_limiters': len(self._rate_limiters),
                'total_delays': stats.get('rate_limit_delays', 0)
            }
        }
    
    def force_refresh(self, symbol: str, data_identifier: str) -> str:
        """Force immediate refresh of specific data"""
        return self.schedule_refresh(
            symbol=symbol,
            data_identifier=data_identifier,
            priority=RefreshPriority.CRITICAL
        )
    
    def cancel_refresh(self, request_id: str) -> bool:
        """Cancel a pending refresh request"""
        with self._lock:
            # Find and cancel request
            for cache_key, request in list(self._active_requests.items()):
                if request.request_id == request_id:
                    if request.status == RefreshStatus.PENDING:
                        request.status = RefreshStatus.CANCELLED
                        del self._active_requests[cache_key]
                        self._completed_requests.append(request)
                        logger.debug(f"Cancelled refresh request {request_id}")
                        return True
                    else:
                        logger.warning(f"Cannot cancel {request.status} request {request_id}")
                        return False
            
            logger.warning(f"Refresh request {request_id} not found")
            return False
    
    # Private methods
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        logger.info("Background refresh scheduler started")
        
        while self._running:
            try:
                self._process_refresh_queues()
                self._check_for_automatic_refreshes()
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5.0)  # Wait before retrying
        
        logger.info("Background refresh scheduler stopped")
    
    def _process_refresh_queues(self) -> None:
        """Process refresh queues in priority order"""
        current_time = datetime.now()
        
        # Process queues in priority order
        for priority in [RefreshPriority.CRITICAL, RefreshPriority.HIGH, 
                        RefreshPriority.MEDIUM, RefreshPriority.LOW]:
            
            queue_obj = self._refresh_queues[priority]
            
            # Process up to 5 items from each queue per iteration
            for _ in range(5):
                try:
                    # Check if item is ready to be processed
                    item = queue_obj.get_nowait()
                    _, scheduled_time, request = item
                    
                    if scheduled_time <= current_time:
                        # Submit for processing
                        future = self._executor.submit(self._process_refresh_request, request)
                        # Don't wait for completion - it's background processing
                    else:
                        # Put back if not ready
                        queue_obj.put_nowait(item)
                        break
                        
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error processing {priority} queue: {e}")
    
    def _process_refresh_request(self, request: RefreshRequest) -> None:
        """Process a single refresh request"""
        cache_key = request.get_cache_key()
        
        try:
            # Update request status
            request.status = RefreshStatus.IN_PROGRESS
            request.attempts += 1
            request.last_attempt = datetime.now()
            
            start_time = time.time()
            
            # Check rate limiting
            limiter = self._rate_limiters[request.data_identifier]
            if not limiter.can_make_call():
                wait_time = limiter.wait_time_seconds()
                if wait_time > 0:
                    logger.debug(f"Rate limiting delay: {wait_time:.1f}s for {cache_key}")
                    time.sleep(wait_time)
                    with self._stats_lock:
                        self._stats['rate_limit_delays'] += 1
            
            # Perform the actual refresh
            success = self._refresh_data(request)
            
            # Record API call
            limiter.record_call()
            with self._stats_lock:
                self._stats['api_calls_made'] += 1
            
            # Update request status
            end_time = time.time()
            refresh_duration = end_time - start_time
            
            if success:
                request.status = RefreshStatus.COMPLETED
                with self._stats_lock:
                    self._stats['requests_completed'] += 1
                    self._stats['total_refresh_time'] += refresh_duration
                
                # Call callbacks
                self._call_refresh_callbacks(request)
                
                logger.debug(f"Successfully refreshed {cache_key} in {refresh_duration:.1f}s")
            else:
                request.status = RefreshStatus.FAILED
                with self._stats_lock:
                    self._stats['requests_failed'] += 1
                
                # Schedule retry if applicable
                if request.should_retry():
                    retry_time = request.get_next_retry_time()
                    self.schedule_refresh(
                        request.symbol,
                        request.data_identifier,
                        request.priority,
                        request.policy,
                        (retry_time - datetime.now()).total_seconds()
                    )
                    logger.debug(f"Scheduled retry for {cache_key}")
                else:
                    logger.warning(f"Failed to refresh {cache_key} after {request.attempts} attempts")
            
        except Exception as e:
            request.status = RefreshStatus.FAILED
            request.error_message = str(e)
            with self._stats_lock:
                self._stats['requests_failed'] += 1
            logger.error(f"Error refreshing {cache_key}: {e}")
        
        finally:
            # Move from active to completed
            with self._lock:
                if cache_key in self._active_requests:
                    del self._active_requests[cache_key]
                self._completed_requests.append(request)
    
    def _refresh_data(self, request: RefreshRequest) -> bool:
        """
        Perform the actual data refresh.
        
        This method should be overridden or configured to integrate with
        your specific data sources (VarInputData, APIs, etc.)
        """
        try:
            # Import here to avoid circular imports
            from .var_input_data import get_var_input_data
            from .universal_data_registry import get_registry, DataRequest
            
            var_data = get_var_input_data()
            registry = get_registry()
            
            # Create data request
            data_request = DataRequest(
                data_type=request.data_identifier,
                symbol=request.symbol,
                period="latest",
                cache_policy="FORCE_REFRESH"  # Force refresh from source
            )
            
            # Get fresh data from registry
            response = registry.get_data(data_request)
            
            if response and response.data is not None:
                # Update VarInputData
                success = var_data.set_variable(
                    symbol=request.symbol,
                    variable_name=request.data_identifier,
                    value=response.data,
                    source="background_refresh",
                    emit_event=True
                )
                return success
            else:
                request.error_message = "No data received from registry"
                return False
                
        except Exception as e:
            request.error_message = f"Refresh failed: {str(e)}"
            logger.error(f"Error in _refresh_data: {e}")
            return False
    
    def _maybe_schedule_background_refresh(self, symbol: str, data_identifier: str) -> None:
        """Check if we should schedule a background refresh based on access patterns"""
        frequency = self._access_tracker.get_access_frequency(symbol, data_identifier)
        policy = self._data_policies.get(data_identifier, self.default_policy)
        
        # Check if data meets criteria for background refresh
        if frequency >= policy.access_threshold / 24.0:  # Convert to per-hour
            last_access = self._access_tracker.get_last_access_time(symbol, data_identifier)
            
            if last_access:
                hours_since_access = (datetime.now() - last_access).total_seconds() / 3600
                
                # Schedule refresh if data is getting stale
                if hours_since_access > policy.refresh_interval_hours:
                    priority = RefreshPriority.MEDIUM
                    
                    # Boost priority for very stale data
                    if hours_since_access > policy.max_age_hours:
                        priority = RefreshPriority.HIGH
                    
                    try:
                        self.schedule_refresh(
                            symbol=symbol,
                            data_identifier=data_identifier,
                            priority=priority,
                            policy=policy
                        )
                        logger.debug(f"Auto-scheduled refresh for {symbol}:{data_identifier}")
                    except Exception as e:
                        logger.warning(f"Failed to auto-schedule refresh: {e}")
    
    def _check_for_automatic_refreshes(self) -> None:
        """Check for data that needs automatic refresh"""
        # This runs periodically to check for stale data
        # Implementation would check VarInputData for old data that needs refresh
        pass
    
    def _call_refresh_callbacks(self, request: RefreshRequest) -> None:
        """Call registered callbacks for data refresh"""
        callbacks = self._refresh_callbacks.get(request.data_identifier, [])
        
        for callback in callbacks:
            try:
                callback(request.symbol, request.data_identifier, request.status)
            except Exception as e:
                logger.error(f"Error in refresh callback: {e}")


# Global refresh manager instance
_global_refresh_manager: Optional[BackgroundRefreshManager] = None
_manager_lock = threading.Lock()


def get_background_refresh_manager() -> BackgroundRefreshManager:
    """Get the global background refresh manager instance"""
    global _global_refresh_manager
    
    if _global_refresh_manager is None:
        with _manager_lock:
            if _global_refresh_manager is None:
                _global_refresh_manager = BackgroundRefreshManager()
    
    return _global_refresh_manager


# Export main classes and functions
__all__ = [
    'BackgroundRefreshManager',
    'RefreshRequest',
    'RefreshPolicy',
    'RefreshPriority',
    'RefreshStatus',
    'AccessTracker',
    'RateLimiter',
    'get_background_refresh_manager'
]