"""
Enhanced Error Handler with Retry Logic and Recovery Mechanisms
==============================================================

Comprehensive error handling system for financial data processing with:
- Intelligent retry logic with exponential backoff
- Circuit breaker integration for service health management
- Fallback source selection and recovery strategies
- Error logging and metrics collection
- Context-aware error classification and recovery
"""

import time
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple, Union
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, field

from .exceptions import (
    DataSourceException, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    classify_error, create_error_context,
    RateLimitException, NetworkException, TimeoutException,
    CircuitBreakerOpenException
)

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorCategory] = field(default_factory=lambda: [
        ErrorCategory.NETWORK, ErrorCategory.TIMEOUT, ErrorCategory.SERVER_ERROR, ErrorCategory.RATE_LIMIT
    ])


@dataclass
class ErrorMetrics:
    """Track error statistics for analysis and optimization"""
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_source: Dict[str, int] = field(default_factory=dict)
    recovery_success_rate: Dict[str, float] = field(default_factory=dict)
    last_error_time: Optional[datetime] = None
    consecutive_failures: Dict[str, int] = field(default_factory=dict)

    def record_error(self, error: DataSourceException):
        """Record error occurrence for metrics"""
        self.total_errors += 1
        self.last_error_time = datetime.now()

        # Track by category
        category = error.error_category.value
        self.errors_by_category[category] = self.errors_by_category.get(category, 0) + 1

        # Track by source
        if error.source:
            self.errors_by_source[error.source] = self.errors_by_source.get(error.source, 0) + 1
            self.consecutive_failures[error.source] = self.consecutive_failures.get(error.source, 0) + 1

    def record_recovery_success(self, source: str, strategy: str):
        """Record successful recovery for metrics"""
        if source in self.consecutive_failures:
            self.consecutive_failures[source] = 0

        # Update recovery success rate
        key = f"{source}_{strategy}"
        current_rate = self.recovery_success_rate.get(key, 0.5)
        self.recovery_success_rate[key] = min(1.0, current_rate + 0.1)


class EnhancedErrorHandler:
    """
    Enhanced error handler with retry logic, circuit breaker integration,
    and intelligent recovery strategies
    """

    def __init__(self,
                 retry_config: RetryConfig = None,
                 circuit_breaker_manager = None,
                 rate_limiter = None,
                 data_source_hierarchy = None):
        """
        Initialize enhanced error handler

        Args:
            retry_config: Configuration for retry behavior
            circuit_breaker_manager: Circuit breaker manager for service health
            rate_limiter: Rate limiter for API request management
            data_source_hierarchy: Data source hierarchy for fallback selection
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_manager = circuit_breaker_manager
        self.rate_limiter = rate_limiter
        self.data_source_hierarchy = data_source_hierarchy
        self.metrics = ErrorMetrics()

        logger.info("Enhanced error handler initialized")

    def calculate_retry_delay(self, attempt: int, error: DataSourceException) -> float:
        """
        Calculate retry delay based on error type and attempt number

        Args:
            attempt: Current retry attempt (0-based)
            error: The error that occurred

        Returns:
            Delay in seconds before next retry
        """
        # Use error-specific delay if available
        if error.retry_after:
            base_delay = error.retry_after
        elif error.error_category == ErrorCategory.RATE_LIMIT:
            # Longer delays for rate limit errors
            base_delay = self.retry_config.base_delay * 3
        elif error.error_category == ErrorCategory.NETWORK:
            # Moderate delays for network errors
            base_delay = self.retry_config.base_delay * 2
        else:
            base_delay = self.retry_config.base_delay

        # Apply exponential backoff
        delay = min(base_delay * (self.retry_config.backoff_factor ** attempt),
                   self.retry_config.max_delay)

        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter

        logger.debug(f"Calculated retry delay: {delay:.2f}s for attempt {attempt + 1}")
        return delay

    def should_retry(self, error: DataSourceException, attempt: int) -> bool:
        """
        Determine if an error should trigger a retry

        Args:
            error: The error that occurred
            attempt: Current retry attempt (0-based)

        Returns:
            True if retry should be attempted
        """
        # Check maximum retries
        if attempt >= self.retry_config.max_retries:
            logger.debug(f"Max retries ({self.retry_config.max_retries}) exceeded")
            return False

        # Check if error category is retryable
        if error.error_category not in self.retry_config.retry_on_errors:
            logger.debug(f"Error category {error.error_category.value} not configured for retry")
            return False

        # Check error-specific retry logic
        if not error.is_retryable():
            logger.debug(f"Error marked as non-retryable: {error.recovery_strategy.value}")
            return False

        # Check circuit breaker status for the source
        if (self.circuit_breaker_manager and error.source and
            hasattr(self.circuit_breaker_manager, 'circuit_breakers')):
            circuit_breaker = self.circuit_breaker_manager.circuit_breakers.get(error.source)
            if circuit_breaker and not circuit_breaker.can_execute():
                logger.debug(f"Circuit breaker open for {error.source}, skipping retry")
                return False

        logger.debug(f"Retry approved for attempt {attempt + 1}")
        return True

    def select_fallback_source(self, failed_source: str, exclude: List[str] = None) -> Optional[str]:
        """
        Select fallback data source when primary source fails

        Args:
            failed_source: The source that failed
            exclude: List of sources to exclude from selection

        Returns:
            Best available fallback source or None
        """
        if not self.data_source_hierarchy:
            logger.warning("No data source hierarchy available for fallback selection")
            return None

        exclude = exclude or []
        exclude.append(failed_source)  # Always exclude the failed source

        # Get optimal hierarchy excluding failed sources
        try:
            from .data_source_hierarchy import DataSourceType

            # Convert source names to DataSourceType enums
            exclude_types = []
            for source in exclude:
                source_type = getattr(DataSourceType, source.upper(), None)
                if source_type:
                    exclude_types.append(source_type)

            hierarchy = self.data_source_hierarchy.get_optimal_source_hierarchy(exclude_types)

            if hierarchy:
                fallback = hierarchy[0].value
                logger.info(f"Selected fallback source: {fallback} (failed: {failed_source})")
                return fallback

        except Exception as e:
            logger.warning(f"Error selecting fallback source: {e}")

        return None

    def handle_rate_limit_error(self, error: RateLimitException) -> Tuple[bool, Optional[str]]:
        """
        Handle rate limit errors with intelligent recovery

        Args:
            error: Rate limit exception

        Returns:
            Tuple of (should_fallback, fallback_source)
        """
        logger.warning(f"Rate limit encountered for {error.source}: {error.message}")

        # Record rate limit in circuit breaker if available
        if (self.circuit_breaker_manager and error.source and
            hasattr(self.circuit_breaker_manager, 'circuit_breakers')):
            circuit_breaker = self.circuit_breaker_manager.circuit_breakers.get(error.source)
            if circuit_breaker:
                circuit_breaker.record_failure()

        # Update rate limiter if available
        if (self.rate_limiter and error.source and
            hasattr(self.rate_limiter, '_update_health_metrics')):
            self.rate_limiter._update_health_metrics(
                error.source, success=False, is_rate_limited=True
            )

        # Select fallback source
        fallback_source = self.select_fallback_source(error.source)
        return True, fallback_source

    def handle_network_error(self, error: NetworkException, attempt: int) -> Tuple[bool, float]:
        """
        Handle network errors with appropriate retry strategy

        Args:
            error: Network exception
            attempt: Current attempt number

        Returns:
            Tuple of (should_retry, retry_delay)
        """
        logger.warning(f"Network error for {error.source}: {error.message}")

        if self.should_retry(error, attempt):
            delay = self.calculate_retry_delay(attempt, error)
            logger.info(f"Retrying {error.source} after network error in {delay:.1f}s")
            return True, delay

        logger.error(f"Network error for {error.source} exceeded retry limits")
        return False, 0.0

    def handle_server_error(self, error: DataSourceException, attempt: int) -> Tuple[bool, Union[float, str]]:
        """
        Handle server errors with fallback or retry strategy

        Args:
            error: Server exception
            attempt: Current attempt number

        Returns:
            Tuple of (should_retry_or_fallback, retry_delay_or_fallback_source)
        """
        logger.warning(f"Server error for {error.source}: {error.message}")

        # For temporary server errors (502, 503, 504), prefer retry
        if (hasattr(error, 'context') and error.context and
            error.context.get('status_code') in [502, 503, 504]):

            if self.should_retry(error, attempt):
                delay = self.calculate_retry_delay(attempt, error)
                logger.info(f"Retrying {error.source} after temporary server error in {delay:.1f}s")
                return True, delay

        # For persistent server errors, use fallback
        fallback_source = self.select_fallback_source(error.source)
        if fallback_source:
            logger.info(f"Using fallback source {fallback_source} for server error from {error.source}")
            return True, fallback_source

        return False, 0.0

    @contextmanager
    def error_handling_context(self, source: str, ticker: str = None,
                              operation: str = "data_fetch"):
        """
        Context manager for comprehensive error handling

        Args:
            source: Data source identifier
            ticker: Stock ticker symbol
            operation: Operation being performed

        Yields:
            Error handling context
        """
        start_time = time.time()
        attempt = 0
        max_attempts = self.retry_config.max_retries + 1

        while attempt < max_attempts:
            try:
                context = create_error_context(
                    source=source,
                    ticker=ticker,
                    attempt=attempt,
                    additional_context={'operation': operation}
                )

                logger.debug(f"Attempting {operation} for {ticker} from {source} (attempt {attempt + 1}/{max_attempts})")

                yield context

                # Success - record metrics and exit
                response_time = time.time() - start_time
                logger.info(f"Successfully completed {operation} for {ticker} from {source} in {response_time:.2f}s")

                if source in self.metrics.consecutive_failures:
                    self.metrics.record_recovery_success(source, "retry_success")

                return

            except Exception as e:
                response_time = time.time() - start_time

                # Classify the error
                classified_error = classify_error(e, source, ticker)
                classified_error.context.update({
                    'operation': operation,
                    'attempt': attempt + 1,
                    'response_time': response_time
                })

                # Record error metrics
                self.metrics.record_error(classified_error)

                logger.error(f"Error in {operation} for {ticker} from {source} (attempt {attempt + 1}): {classified_error}")

                # Handle specific error types
                if isinstance(classified_error, RateLimitException):
                    should_fallback, fallback_source = self.handle_rate_limit_error(classified_error)
                    if should_fallback and fallback_source:
                        logger.info(f"Switching to fallback source: {fallback_source}")
                        source = fallback_source
                        attempt = 0  # Reset attempts for new source
                        continue

                elif isinstance(classified_error, NetworkException):
                    should_retry, retry_delay = self.handle_network_error(classified_error, attempt)
                    if should_retry and attempt < max_attempts - 1:
                        logger.info(f"Retrying after network error in {retry_delay:.1f}s")
                        time.sleep(retry_delay)
                        attempt += 1
                        start_time = time.time()  # Reset timer for retry
                        continue

                elif classified_error.error_category == ErrorCategory.SERVER_ERROR:
                    should_retry_or_fallback, delay_or_source = self.handle_server_error(classified_error, attempt)
                    if should_retry_or_fallback:
                        if isinstance(delay_or_source, str):  # Fallback source
                            source = delay_or_source
                            attempt = 0
                            continue
                        elif attempt < max_attempts - 1:  # Retry delay
                            time.sleep(delay_or_source)
                            attempt += 1
                            start_time = time.time()
                            continue

                # General retry logic for other error types
                elif self.should_retry(classified_error, attempt) and attempt < max_attempts - 1:
                    retry_delay = self.calculate_retry_delay(attempt, classified_error)
                    logger.info(f"Retrying {operation} for {ticker} from {source} in {retry_delay:.1f}s")
                    time.sleep(retry_delay)
                    attempt += 1
                    start_time = time.time()
                    continue

                # No more retries or fallbacks available
                total_time = time.time() - start_time
                logger.error(f"Failed {operation} for {ticker} from {source} after {attempt + 1} attempts in {total_time:.2f}s")
                raise classified_error

            # If we reach here, retries were exhausted
            break

    def with_retry(self, operation_name: str = "operation"):
        """
        Decorator for adding retry logic to functions

        Args:
            operation_name: Name of the operation for logging

        Returns:
            Decorated function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract source and ticker from function arguments
                source = kwargs.get('source') or getattr(args[0] if args else None, 'source', 'unknown')
                ticker = kwargs.get('ticker')

                with self.error_handling_context(source, ticker, operation_name):
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive error summary for monitoring and analysis

        Returns:
            Dictionary containing error metrics and recommendations
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': self.metrics.total_errors,
            'errors_by_category': self.metrics.errors_by_category.copy(),
            'errors_by_source': self.metrics.errors_by_source.copy(),
            'consecutive_failures': self.metrics.consecutive_failures.copy(),
            'recovery_success_rates': self.metrics.recovery_success_rate.copy(),
            'last_error_time': self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None,
            'recommendations': []
        }

        # Generate recommendations based on error patterns
        for source, failures in self.metrics.consecutive_failures.items():
            if failures >= 5:
                summary['recommendations'].append(f"Consider disabling {source} - {failures} consecutive failures")
            elif failures >= 3:
                summary['recommendations'].append(f"Monitor {source} - {failures} consecutive failures detected")

        # Add recommendations based on error counts
        if self.metrics.total_errors >= 5:
            summary['recommendations'].append("High error count detected - review system health")

        # Check for rate limiting issues
        rate_limit_errors = self.metrics.errors_by_category.get('rate_limit', 0)
        if rate_limit_errors > 10:
            summary['recommendations'].append(f"Rate limiting detected - consider increasing delays or using more fallback sources")

        return summary

    def reset_metrics(self):
        """Reset error metrics (useful for testing or periodic cleanup)"""
        self.metrics = ErrorMetrics()
        logger.info("Error metrics reset")


# Global error handler instance
_error_handler: Optional[EnhancedErrorHandler] = None


def get_error_handler(**kwargs) -> EnhancedErrorHandler:
    """
    Get global error handler instance

    Args:
        **kwargs: Arguments for error handler initialization (only used on first call)

    Returns:
        Global error handler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = EnhancedErrorHandler(**kwargs)
    return _error_handler


def reset_error_handler():
    """Reset global error handler (useful for testing)"""
    global _error_handler
    _error_handler = None