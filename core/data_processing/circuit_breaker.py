"""
Enhanced Circuit Breaker Pattern for Data Source Health Management
=================================================================

Advanced circuit breaker implementation with:
- Multiple failure types and thresholds
- Adaptive recovery strategies
- Health monitoring and metrics
- Integration with data source hierarchy
- Automatic service degradation and recovery
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from .exceptions import (
    DataSourceException, ErrorCategory, ErrorSeverity,
    CircuitBreakerOpenException, classify_error
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation - requests allowed
    OPEN = "open"           # Circuit open - requests blocked
    HALF_OPEN = "half_open" # Testing recovery - limited requests allowed


class FailureType(Enum):
    """Types of failures tracked by circuit breaker"""
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    DATA_QUALITY = "data_quality"
    AUTHENTICATION = "authentication"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: int = 300         # Seconds before attempting recovery
    success_threshold: int = 3          # Consecutive successes to close circuit
    half_open_max_calls: int = 5        # Max calls allowed in half-open state
    failure_rate_threshold: float = 0.5 # Failure rate to open circuit (0.0-1.0)
    volume_threshold: int = 10          # Minimum requests before failure rate applies
    sliding_window_size: int = 100      # Size of sliding window for metrics
    health_check_interval: int = 60     # Seconds between health checks


@dataclass
class CircuitMetrics:
    """Metrics tracked by circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_request_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    failure_rate: float = 0.0
    average_response_time: float = 0.0

    # Failure type tracking
    failures_by_type: Dict[str, int] = field(default_factory=dict)

    # Sliding window for recent requests
    recent_requests: List[bool] = field(default_factory=list)  # True=success, False=failure
    recent_response_times: List[float] = field(default_factory=list)


class EnhancedCircuitBreaker:
    """
    Enhanced circuit breaker with adaptive failure detection and recovery strategies
    """

    def __init__(self,
                 name: str,
                 config: CircuitBreakerConfig = None,
                 health_check_func: Optional[Callable] = None):
        """
        Initialize circuit breaker

        Args:
            name: Unique name for this circuit breaker
            config: Configuration parameters
            health_check_func: Optional function to perform health checks
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.health_check_func = health_check_func

        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.last_state_change = datetime.now()
        self.half_open_calls = 0

        # Thread safety
        self._lock = threading.RLock()

        # Background health monitoring
        self._stop_health_check = threading.Event()
        self._health_check_thread = None

        if self.config.health_check_interval > 0:
            self._start_health_monitoring()

        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")

    def _start_health_monitoring(self):
        """Start background health monitoring thread"""
        def health_monitor():
            while not self._stop_health_check.wait(self.config.health_check_interval):
                try:
                    self._perform_health_check()
                except Exception as e:
                    logger.error(f"Health check failed for circuit breaker '{self.name}': {e}")

        self._health_check_thread = threading.Thread(
            target=health_monitor,
            name=f"CircuitBreaker-{self.name}-HealthCheck",
            daemon=True
        )
        self._health_check_thread.start()
        logger.debug(f"Started health monitoring for circuit breaker '{self.name}'")

    def _perform_health_check(self):
        """Perform health check and update circuit state if needed"""
        if self.state != CircuitState.OPEN or not self.health_check_func:
            return

        try:
            with self._lock:
                logger.debug(f"Performing health check for circuit breaker '{self.name}'")

                # Only attempt health check if recovery timeout has passed
                time_since_failure = (datetime.now() - self.last_state_change).total_seconds()
                if time_since_failure < self.config.recovery_timeout:
                    return

                # Perform health check
                is_healthy = self.health_check_func()

                if is_healthy:
                    logger.info(f"Health check passed for '{self.name}', transitioning to HALF_OPEN")
                    self._transition_to_half_open()
                else:
                    logger.debug(f"Health check failed for '{self.name}', remaining OPEN")

        except Exception as e:
            logger.warning(f"Health check error for '{self.name}': {e}")

    def _update_metrics(self, success: bool, response_time: float = 0.0,
                       failure_type: Optional[FailureType] = None):
        """Update circuit breaker metrics"""
        now = datetime.now()

        self.metrics.total_requests += 1
        self.metrics.last_request_time = now

        # Update sliding window
        self.metrics.recent_requests.append(success)
        self.metrics.recent_response_times.append(response_time)

        # Maintain sliding window size
        if len(self.metrics.recent_requests) > self.config.sliding_window_size:
            self.metrics.recent_requests.pop(0)
            self.metrics.recent_response_times.pop(0)

        if success:
            self.metrics.successful_requests += 1
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes += 1
            self.metrics.last_success_time = now

            # Update average response time
            if self.metrics.successful_requests > 0:
                self.metrics.average_response_time = (
                    (self.metrics.average_response_time * (self.metrics.successful_requests - 1) + response_time)
                    / self.metrics.successful_requests
                )
        else:
            self.metrics.failed_requests += 1
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure_time = now

            # Track failure by type
            if failure_type:
                failure_key = failure_type.value
                self.metrics.failures_by_type[failure_key] = (
                    self.metrics.failures_by_type.get(failure_key, 0) + 1
                )

        # Calculate failure rate from sliding window
        if len(self.metrics.recent_requests) > 0:
            failures_in_window = sum(1 for r in self.metrics.recent_requests if not r)
            self.metrics.failure_rate = failures_in_window / len(self.metrics.recent_requests)

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on current metrics"""
        # Check consecutive failures threshold
        if self.metrics.consecutive_failures >= self.config.failure_threshold:
            logger.warning(f"Circuit '{self.name}' threshold exceeded: {self.metrics.consecutive_failures} consecutive failures")
            return True

        # Check failure rate threshold (only if we have enough volume)
        if (len(self.metrics.recent_requests) >= self.config.volume_threshold and
            self.metrics.failure_rate >= self.config.failure_rate_threshold):
            logger.warning(f"Circuit '{self.name}' failure rate threshold exceeded: {self.metrics.failure_rate:.2%}")
            return True

        return False

    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state"""
        if self.state != CircuitState.OPEN:
            previous_state = self.state
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            self.half_open_calls = 0

            logger.warning(f"Circuit breaker '{self.name}' OPENED (was {previous_state.value})")
            logger.info(f"Circuit will remain open for {self.config.recovery_timeout}s")

    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state"""
        if self.state == CircuitState.OPEN:
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = datetime.now()
            self.half_open_calls = 0

            logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")

    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            previous_state = self.state
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
            self.half_open_calls = 0

            logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered from {previous_state.value})")

    def can_execute(self) -> bool:
        """
        Check if requests can be executed through this circuit breaker

        Returns:
            True if requests are allowed, False if circuit is open
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                time_since_open = (datetime.now() - self.last_state_change).total_seconds()
                if time_since_open >= self.config.recovery_timeout:
                    self._transition_to_half_open()
                    return True
                return False

            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited calls in half-open state
                if self.half_open_calls < self.config.half_open_max_calls:
                    return True
                return False

            return False

    def record_success(self, response_time: float = 0.0):
        """
        Record successful operation

        Args:
            response_time: Operation response time in seconds
        """
        with self._lock:
            self._update_metrics(success=True, response_time=response_time)

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1

                # Check if we have enough successes to close the circuit
                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
                elif self.half_open_calls >= self.config.half_open_max_calls:
                    # All half-open calls were successful, close the circuit
                    self._transition_to_closed()

    def record_failure(self, error: Exception = None):
        """
        Record failed operation

        Args:
            error: The exception that caused the failure (for classification)
        """
        with self._lock:
            # Classify failure type
            failure_type = None
            if error:
                if isinstance(error, DataSourceException):
                    if error.error_category == ErrorCategory.NETWORK:
                        failure_type = FailureType.NETWORK
                    elif error.error_category == ErrorCategory.TIMEOUT:
                        failure_type = FailureType.TIMEOUT
                    elif error.error_category == ErrorCategory.RATE_LIMIT:
                        failure_type = FailureType.RATE_LIMIT
                    elif error.error_category == ErrorCategory.SERVER_ERROR:
                        failure_type = FailureType.SERVER_ERROR
                    elif error.error_category == ErrorCategory.DATA_QUALITY:
                        failure_type = FailureType.DATA_QUALITY
                    elif error.error_category == ErrorCategory.AUTHENTICATION:
                        failure_type = FailureType.AUTHENTICATION
                else:
                    # Classify generic exceptions
                    classified = classify_error(error, source=self.name)
                    if classified.error_category == ErrorCategory.NETWORK:
                        failure_type = FailureType.NETWORK
                    # Add more classifications as needed

            self._update_metrics(success=False, failure_type=failure_type)

            # Check if circuit should be opened
            if self.state == CircuitState.CLOSED:
                if self._should_open_circuit():
                    self._transition_to_open()

            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                logger.warning(f"Failure in HALF_OPEN state for '{self.name}', reopening circuit")
                self._transition_to_open()

    @contextmanager
    def call_protection(self):
        """
        Context manager for protected calls through circuit breaker

        Raises:
            CircuitBreakerOpenException: If circuit is open and requests are blocked
        """
        if not self.can_execute():
            recovery_time = None
            if self.state == CircuitState.OPEN:
                recovery_time = self.last_state_change + timedelta(seconds=self.config.recovery_timeout)

            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is {self.state.value}",
                source=self.name,
                recovery_time=recovery_time
            )

        start_time = time.time()
        success = False
        error = None

        try:
            yield
            success = True
        except Exception as e:
            error = e
            raise
        finally:
            response_time = time.time() - start_time

            if success:
                self.record_success(response_time)
            else:
                self.record_failure(error)

    def get_state_info(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state and metrics

        Returns:
            Dictionary containing state and metric information
        """
        with self._lock:
            state_duration = (datetime.now() - self.last_state_change).total_seconds()

            return {
                'name': self.name,
                'state': self.state.value,
                'state_duration_seconds': state_duration,
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'failure_rate': self.metrics.failure_rate,
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'average_response_time': self.metrics.average_response_time,
                'failures_by_type': self.metrics.failures_by_type.copy(),
                'last_success': self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                'last_failure': self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                'half_open_calls': self.half_open_calls if self.state == CircuitState.HALF_OPEN else 0,
                'next_retry_time': (
                    (self.last_state_change + timedelta(seconds=self.config.recovery_timeout)).isoformat()
                    if self.state == CircuitState.OPEN else None
                )
            }

    def reset(self):
        """Reset circuit breaker to initial state"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitMetrics()
            self.last_state_change = datetime.now()
            self.half_open_calls = 0

            logger.info(f"Circuit breaker '{self.name}' reset to initial state")

    def force_open(self, reason: str = "manual"):
        """
        Force circuit breaker to open state

        Args:
            reason: Reason for forcing open
        """
        with self._lock:
            self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.name}' forced OPEN: {reason}")

    def force_close(self, reason: str = "manual"):
        """
        Force circuit breaker to closed state

        Args:
            reason: Reason for forcing close
        """
        with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' forced CLOSED: {reason}")

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_stop_health_check'):
            self._stop_health_check.set()
        if hasattr(self, '_health_check_thread') and self._health_check_thread:
            if self._health_check_thread.is_alive():
                self._health_check_thread.join(timeout=1.0)


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers with centralized monitoring and control
    """

    def __init__(self, default_config: CircuitBreakerConfig = None):
        """
        Initialize circuit breaker manager

        Args:
            default_config: Default configuration for new circuit breakers
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self._lock = threading.RLock()

        logger.info("Circuit breaker manager initialized")

    def get_or_create_circuit_breaker(self,
                                    name: str,
                                    config: CircuitBreakerConfig = None,
                                    health_check_func: Optional[Callable] = None) -> EnhancedCircuitBreaker:
        """
        Get existing or create new circuit breaker

        Args:
            name: Circuit breaker name
            config: Configuration (uses default if None)
            health_check_func: Optional health check function

        Returns:
            Circuit breaker instance
        """
        with self._lock:
            if name not in self.circuit_breakers:
                circuit_config = config or self.default_config
                self.circuit_breakers[name] = EnhancedCircuitBreaker(
                    name=name,
                    config=circuit_config,
                    health_check_func=health_check_func
                )
                logger.info(f"Created new circuit breaker: {name}")

            return self.circuit_breakers[name]

    def get_circuit_breaker(self, name: str) -> Optional[EnhancedCircuitBreaker]:
        """Get existing circuit breaker by name"""
        return self.circuit_breakers.get(name)

    def remove_circuit_breaker(self, name: str) -> bool:
        """
        Remove circuit breaker

        Args:
            name: Circuit breaker name

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                logger.info(f"Removed circuit breaker: {name}")
                return True
            return False

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state information for all circuit breakers"""
        return {name: cb.get_state_info() for name, cb in self.circuit_breakers.items()}

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary of all circuit breakers

        Returns:
            Health summary with recommendations
        """
        all_states = self.get_all_states()

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_circuit_breakers': len(self.circuit_breakers),
            'states': {state.value: 0 for state in CircuitState},
            'circuit_breakers': all_states,
            'recommendations': []
        }

        # Count states and generate recommendations
        for name, state_info in all_states.items():
            state = state_info['state']
            summary['states'][state] += 1

            # Generate recommendations based on state and metrics
            if state == 'open':
                summary['recommendations'].append(f"Circuit '{name}' is open - check service health")
            elif state_info['failure_rate'] > 0.3:
                summary['recommendations'].append(f"Circuit '{name}' has high failure rate: {state_info['failure_rate']:.1%}")
            elif state_info['consecutive_failures'] > 2:
                summary['recommendations'].append(f"Circuit '{name}' has {state_info['consecutive_failures']} consecutive failures")

        return summary

    def reset_all(self):
        """Reset all circuit breakers to initial state"""
        with self._lock:
            for cb in self.circuit_breakers.values():
                cb.reset()
            logger.info("Reset all circuit breakers")


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager(default_config: CircuitBreakerConfig = None) -> CircuitBreakerManager:
    """Get global circuit breaker manager instance"""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager(default_config)
    return _circuit_breaker_manager


def reset_circuit_breaker_manager():
    """Reset global circuit breaker manager (useful for testing)"""
    global _circuit_breaker_manager
    _circuit_breaker_manager = None