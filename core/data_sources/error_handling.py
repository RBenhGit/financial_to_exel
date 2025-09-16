"""
Enhanced Error Handling and Recovery for Data Sources
====================================================

This module provides comprehensive error handling, classification, retry logic with
exponential backoff, and circuit breaker patterns for all data source operations.

Features:
- Intelligent error classification and specific error types
- Retry logic with exponential backoff and jitter
- Circuit breaker pattern for failed services
- Comprehensive logging and monitoring
- Recovery strategies for different failure types
"""

import asyncio
import logging
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of different error types"""
    NETWORK_ERROR = "network_error"
    API_RATE_LIMIT = "api_rate_limit"
    API_QUOTA_EXCEEDED = "api_quota_exceeded"
    INVALID_API_KEY = "invalid_api_key"
    DATA_NOT_FOUND = "data_not_found"
    INVALID_SYMBOL = "invalid_symbol"
    PARSING_ERROR = "parsing_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    EXCEL_FILE_ERROR = "excel_file_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    original_exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    should_retry: bool = True
    backoff_seconds: float = 1.0
    circuit_breaker_trigger: bool = False


class DataSourceException(Exception):
    """Base exception for data source errors"""

    def __init__(self, error_info: ErrorInfo):
        super().__init__(error_info.message)
        self.error_info = error_info


class NetworkException(DataSourceException):
    """Network-related errors"""
    pass


class APIException(DataSourceException):
    """API-related errors"""
    pass


class DataException(DataSourceException):
    """Data processing errors"""
    pass


class ConfigurationException(DataSourceException):
    """Configuration errors"""
    pass


class ErrorClassifier:
    """Intelligent error classification system"""

    @staticmethod
    def classify_error(exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """
        Classify an exception into structured error information

        Args:
            exception: The exception to classify
            context: Additional context about the error

        Returns:
            ErrorInfo: Classified error information
        """
        context = context or {}
        error_message = str(exception)
        error_lower = error_message.lower()

        # Network-related errors
        if any(keyword in error_lower for keyword in [
            'connection', 'network', 'timeout', 'unreachable', 'dns', 'socket'
        ]):
            return ErrorInfo(
                error_type=ErrorType.NETWORK_ERROR,
                severity=ErrorSeverity.HIGH,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=True,
                backoff_seconds=2.0
            )

        # API Rate limiting
        if any(keyword in error_lower for keyword in [
            'rate limit', 'too many requests', '429', 'quota exceeded'
        ]):
            return ErrorInfo(
                error_type=ErrorType.API_RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=True,
                backoff_seconds=60.0  # Longer backoff for rate limits
            )

        # Authentication errors
        if any(keyword in error_lower for keyword in [
            'unauthorized', 'authentication', 'api key', '401', '403'
        ]):
            return ErrorInfo(
                error_type=ErrorType.INVALID_API_KEY,
                severity=ErrorSeverity.CRITICAL,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=False,  # Don't retry auth errors
                circuit_breaker_trigger=True
            )

        # Server errors (retryable)
        if any(keyword in error_lower for keyword in [
            '500', '502', '503', '504', 'server error', 'internal error'
        ]):
            return ErrorInfo(
                error_type=ErrorType.SERVER_ERROR,
                severity=ErrorSeverity.HIGH,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=True,
                backoff_seconds=5.0
            )

        # Excel/file errors (check before client errors to avoid conflict with "not found")
        if any(keyword in error_lower for keyword in [
            'excel', 'corrupted'
        ]) or ('file not found' in error_lower and any(ext in error_lower for ext in ['.xlsx', '.xls', 'excel'])):
            return ErrorInfo(
                error_type=ErrorType.EXCEL_FILE_ERROR,
                severity=ErrorSeverity.HIGH,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=False
            )

        # Client errors (usually not retryable)
        if any(keyword in error_lower for keyword in [
            '400', '404', 'bad request', 'not found', 'invalid symbol'
        ]):
            return ErrorInfo(
                error_type=ErrorType.INVALID_SYMBOL if 'symbol' in error_lower else ErrorType.CLIENT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=False
            )

        # Data validation errors
        if any(keyword in error_lower for keyword in [
            'validation', 'invalid data', 'parsing', 'malformed'
        ]):
            return ErrorInfo(
                error_type=ErrorType.DATA_VALIDATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=error_message,
                original_exception=exception,
                context=context,
                should_retry=False
            )

        # Default classification
        return ErrorInfo(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=error_message,
            original_exception=exception,
            context=context,
            should_retry=True,
            backoff_seconds=1.0
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures to trigger open state
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    success_threshold: int = 3  # Successes needed to close circuit
    timeout_duration: float = 30.0  # Request timeout


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = threading.Lock()

        logger.info(f"Circuit breaker '{name}' initialized: {self.config}")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            DataSourceException: If circuit is open or function fails
        """
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moving to HALF_OPEN state")
                else:
                    error_info = ErrorInfo(
                        error_type=ErrorType.SERVER_ERROR,
                        severity=ErrorSeverity.CRITICAL,
                        message=f"Circuit breaker '{self.name}' is OPEN",
                        context={'circuit_breaker': self.name},
                        should_retry=False
                    )
                    raise DataSourceException(error_info)

        try:
            # Execute with timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                result = future.result(timeout=self.config.timeout_duration)

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful execution"""
        with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' is now CLOSED")
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0

    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' failed in HALF_OPEN, moving to OPEN")
            elif self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' threshold reached, moving to OPEN")

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryConfig:
    """Configuration for retry logic"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter"""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()

    def execute_with_retry(
        self,
        func: Callable,
        error_classifier: ErrorClassifier = None,
        context: Dict[str, Any] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            error_classifier: Error classifier instance
            context: Additional context
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            DataSourceException: If all retries fail
        """
        error_classifier = error_classifier or ErrorClassifier()
        context = context or {}
        last_error_info = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Attempting execution (attempt {attempt}/{self.config.max_attempts})")
                return func(*args, **kwargs)

            except Exception as e:
                error_info = error_classifier.classify_error(e, context)
                error_info.retry_count = attempt
                last_error_info = error_info

                logger.warning(
                    f"Attempt {attempt} failed: {error_info.error_type.value} - {error_info.message}",
                    extra={'error_info': error_info.__dict__}
                )

                if not error_info.should_retry or attempt >= self.config.max_attempts:
                    break

                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt, error_info.backoff_seconds)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)

        # All retries failed
        if last_error_info:
            exception_class = self._get_exception_class(last_error_info.error_type)
            raise exception_class(last_error_info)

        # Shouldn't reach here, but just in case
        error_info = ErrorInfo(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="All retry attempts failed",
            context=context
        )
        raise DataSourceException(error_info)

    def _calculate_delay(self, attempt: int, base_delay: float = None) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Use provided base_delay if given, otherwise use config base_delay
        if base_delay is not None:
            base = base_delay
        else:
            base = self.config.base_delay

        delay = base * (self.config.exponential_base ** (attempt - 1))
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def _get_exception_class(self, error_type: ErrorType) -> Type[DataSourceException]:
        """Get appropriate exception class for error type"""
        mapping = {
            ErrorType.NETWORK_ERROR: NetworkException,
            ErrorType.API_RATE_LIMIT: APIException,
            ErrorType.API_QUOTA_EXCEEDED: APIException,
            ErrorType.INVALID_API_KEY: APIException,
            ErrorType.AUTHENTICATION_ERROR: APIException,
            ErrorType.SERVER_ERROR: APIException,
            ErrorType.CLIENT_ERROR: APIException,
            ErrorType.EXCEL_FILE_ERROR: DataException,
            ErrorType.DATA_VALIDATION_ERROR: DataException,
            ErrorType.PARSING_ERROR: DataException,
            ErrorType.CONFIGURATION_ERROR: ConfigurationException,
        }
        return mapping.get(error_type, DataSourceException)


class DataSourceErrorHandler:
    """Comprehensive error handler for data sources"""

    def __init__(
        self,
        name: str,
        retry_config: RetryConfig = None,
        circuit_breaker_config: CircuitBreakerConfig = None,
        enable_circuit_breaker: bool = True
    ):
        self.name = name
        self.retry_handler = RetryHandler(retry_config)
        self.error_classifier = ErrorClassifier()
        self.circuit_breaker = CircuitBreaker(name, circuit_breaker_config) if enable_circuit_breaker else None

        # Error tracking
        self.error_history: List[ErrorInfo] = []
        self.success_count = 0
        self.total_requests = 0

        logger.info(f"Data source error handler '{name}' initialized")

    def execute(
        self,
        func: Callable,
        context: Dict[str, Any] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with comprehensive error handling

        Args:
            func: Function to execute
            context: Additional context
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        self.total_requests += 1
        context = context or {}
        context.update({
            'handler_name': self.name,
            'attempt_timestamp': datetime.now().isoformat()
        })

        try:
            if self.circuit_breaker:
                # Use circuit breaker protection
                result = self.circuit_breaker.call(
                    self.retry_handler.execute_with_retry,
                    func,
                    self.error_classifier,
                    context,
                    *args,
                    **kwargs
                )
            else:
                # Use retry handler only
                result = self.retry_handler.execute_with_retry(
                    func,
                    self.error_classifier,
                    context,
                    *args,
                    **kwargs
                )

            self.success_count += 1
            logger.debug(f"Successful execution for '{self.name}'")
            return result

        except DataSourceException as e:
            self.error_history.append(e.error_info)
            logger.error(
                f"Data source '{self.name}' failed: {e.error_info.error_type.value} - {e.error_info.message}",
                extra={'error_info': e.error_info.__dict__}
            )
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        success_rate = (self.success_count / self.total_requests) if self.total_requests > 0 else 0.0
        recent_errors = self.error_history[-10:]  # Last 10 errors

        status = {
            'name': self.name,
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'error_count': len(self.error_history),
            'success_rate': success_rate,
            'recent_errors': [
                {
                    'type': err.error_type.value,
                    'severity': err.severity.value,
                    'message': err.message,
                    'timestamp': err.timestamp.isoformat()
                }
                for err in recent_errors
            ]
        }

        if self.circuit_breaker:
            status['circuit_breaker'] = self.circuit_breaker.get_state()

        return status

    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        if self.circuit_breaker:
            with self.circuit_breaker.lock:
                self.circuit_breaker.state = CircuitBreakerState.CLOSED
                self.circuit_breaker.failure_count = 0
                self.circuit_breaker.success_count = 0
                self.circuit_breaker.last_failure_time = None
                logger.info(f"Circuit breaker '{self.name}' manually reset")


def with_error_handling(
    name: str = None,
    retry_config: RetryConfig = None,
    circuit_breaker_config: CircuitBreakerConfig = None,
    enable_circuit_breaker: bool = True
):
    """
    Decorator for adding comprehensive error handling to functions

    Args:
        name: Name for the error handler
        retry_config: Retry configuration
        circuit_breaker_config: Circuit breaker configuration
        enable_circuit_breaker: Whether to enable circuit breaker
    """

    def decorator(func: Callable) -> Callable:
        handler_name = name or func.__name__
        error_handler = DataSourceErrorHandler(
            handler_name,
            retry_config,
            circuit_breaker_config,
            enable_circuit_breaker
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            context = {
                'function_name': func.__name__,
                'module': func.__module__
            }
            return error_handler.execute(func, context, *args, **kwargs)

        # Attach error handler to wrapper for external access
        wrapper._error_handler = error_handler
        return wrapper

    return decorator


# Global error handler registry
_error_handlers: Dict[str, DataSourceErrorHandler] = {}


def get_error_handler(name: str) -> Optional[DataSourceErrorHandler]:
    """Get error handler by name"""
    return _error_handlers.get(name)


def register_error_handler(handler: DataSourceErrorHandler):
    """Register error handler globally"""
    _error_handlers[handler.name] = handler
    logger.info(f"Registered error handler: {handler.name}")


def get_all_health_status() -> Dict[str, Any]:
    """Get health status for all registered error handlers"""
    return {
        name: handler.get_health_status()
        for name, handler in _error_handlers.items()
    }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    # Test error classification
    classifier = ErrorClassifier()

    test_exceptions = [
        Exception("Connection timeout"),
        Exception("Rate limit exceeded"),
        Exception("401 Unauthorized"),
        Exception("Invalid symbol INVALIDTICKER"),
        Exception("Excel file not found"),
    ]

    for exc in test_exceptions:
        error_info = classifier.classify_error(exc)
        print(f"Error: {exc} -> Type: {error_info.error_type}, Severity: {error_info.severity}, Retry: {error_info.should_retry}")

    # Test decorator
    @with_error_handling(name="test_function", retry_config=RetryConfig(max_attempts=2))
    def test_function(should_fail: bool = False):
        if should_fail:
            raise Exception("Test failure")
        return "Success"

    try:
        result = test_function(should_fail=False)
        print(f"Success result: {result}")

        result = test_function(should_fail=True)
        print(f"Failure result: {result}")
    except DataSourceException as e:
        print(f"Handled error: {e.error_info.error_type} - {e.error_info.message}")

    # Print health status
    health_status = get_all_health_status()
    print(f"Health status: {health_status}")