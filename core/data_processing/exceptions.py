"""
Data Source Error Handling and Recovery Exceptions
=================================================

Comprehensive exception hierarchy for financial data processing with:
- Specific error types for different failure scenarios
- Error classification and recovery strategies
- Context information for debugging and fallback decisions
- Integration with circuit breaker and retry mechanisms
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for prioritization and handling"""
    LOW = "low"           # Minor issues, degraded functionality
    MEDIUM = "medium"     # Significant issues, fallback required
    HIGH = "high"         # Critical issues, immediate attention
    CRITICAL = "critical" # System-breaking issues, emergency response


class ErrorCategory(Enum):
    """Error categories for classification and handling strategy"""
    NETWORK = "network"           # Network connectivity issues
    RATE_LIMIT = "rate_limit"     # API rate limiting
    AUTHENTICATION = "auth"       # API key or authentication issues
    DATA_QUALITY = "data_quality" # Invalid or incomplete data
    PARSING = "parsing"           # Data format/parsing errors
    TIMEOUT = "timeout"           # Request timeout errors
    SERVER_ERROR = "server"       # External server errors
    CLIENT_ERROR = "client"       # Client-side configuration errors
    RESOURCE = "resource"         # Resource exhaustion (memory, disk)
    VALIDATION = "validation"     # Input validation errors


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY_IMMEDIATE = "retry_immediate"         # Retry immediately
    RETRY_EXPONENTIAL = "retry_exponential"     # Retry with exponential backoff
    RETRY_LINEAR = "retry_linear"              # Retry with linear backoff
    FALLBACK_SOURCE = "fallback_source"        # Switch to alternative source
    USE_CACHE = "use_cache"                    # Use cached data
    DEGRADE_GRACEFULLY = "degrade_graceful"    # Continue with partial data
    CIRCUIT_BREAK = "circuit_break"            # Open circuit breaker
    MANUAL_INTERVENTION = "manual"             # Requires manual intervention


class DataSourceException(Exception):
    """
    Base exception for data source errors with enhanced context and recovery information
    """

    def __init__(self,
                 message: str,
                 error_category: ErrorCategory = ErrorCategory.CLIENT_ERROR,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_EXPONENTIAL,
                 source: Optional[str] = None,
                 ticker: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None,
                 retry_after: Optional[int] = None):

        super().__init__(message)
        self.message = message
        self.error_category = error_category
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.source = source
        self.ticker = ticker
        self.context = context or {}
        self.original_exception = original_exception
        self.retry_after = retry_after
        self.timestamp = datetime.now()

        # Add original exception details to context
        if original_exception:
            self.context.update({
                'original_error_type': type(original_exception).__name__,
                'original_error_message': str(original_exception),
                'original_traceback': getattr(original_exception, '__traceback__', None)
            })

    def is_retryable(self) -> bool:
        """Check if this error should trigger a retry"""
        return self.recovery_strategy in [
            RecoveryStrategy.RETRY_IMMEDIATE,
            RecoveryStrategy.RETRY_EXPONENTIAL,
            RecoveryStrategy.RETRY_LINEAR
        ]

    def should_use_fallback(self) -> bool:
        """Check if this error should trigger fallback to alternative source"""
        return self.recovery_strategy in [
            RecoveryStrategy.FALLBACK_SOURCE,
            RecoveryStrategy.CIRCUIT_BREAK
        ]

    def should_use_cache(self) -> bool:
        """Check if cached data should be used as fallback"""
        return self.recovery_strategy == RecoveryStrategy.USE_CACHE

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on strategy and attempt number"""
        if self.retry_after:
            return float(self.retry_after)

        if self.recovery_strategy == RecoveryStrategy.RETRY_IMMEDIATE:
            return 0.1
        elif self.recovery_strategy == RecoveryStrategy.RETRY_LINEAR:
            return min(attempt * 2.0, 30.0)
        elif self.recovery_strategy == RecoveryStrategy.RETRY_EXPONENTIAL:
            return min(2 ** attempt, 60.0)
        else:
            return 5.0  # Default delay

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and analysis"""
        return {
            'message': self.message,
            'error_category': self.error_category.value,
            'severity': self.severity.value,
            'recovery_strategy': self.recovery_strategy.value,
            'source': self.source,
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat(),
            'retry_after': self.retry_after,
            'context': self.context,
            'is_retryable': self.is_retryable(),
            'should_use_fallback': self.should_use_fallback(),
            'should_use_cache': self.should_use_cache()
        }


# Network-related exceptions
class NetworkException(DataSourceException):
    """Network connectivity and communication errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.RETRY_EXPONENTIAL,
            **kwargs
        )


class TimeoutException(DataSourceException):
    """Request timeout errors"""

    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        context = kwargs.get('context', {})
        if timeout_seconds:
            context['timeout_seconds'] = timeout_seconds
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=RecoveryStrategy.RETRY_LINEAR,
            **kwargs
        )


# API-specific exceptions
class RateLimitException(DataSourceException):
    """API rate limiting errors with retry timing information"""

    def __init__(self, message: str, retry_after: int = None, requests_remaining: int = 0, **kwargs):
        context = kwargs.get('context', {})
        context.update({
            'requests_remaining': requests_remaining,
            'rate_limit_type': 'api_quota'
        })
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=RecoveryStrategy.FALLBACK_SOURCE,
            retry_after=retry_after,
            **kwargs
        )


class AuthenticationException(DataSourceException):
    """API authentication and authorization errors"""

    def __init__(self, message: str, api_key_configured: bool = False, **kwargs):
        context = kwargs.get('context', {})
        context['api_key_configured'] = api_key_configured
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.FALLBACK_SOURCE,
            **kwargs
        )


class ServerException(DataSourceException):
    """External server errors (5xx responses)"""

    def __init__(self, message: str, status_code: int = None, **kwargs):
        context = kwargs.get('context', {})
        if status_code:
            context['status_code'] = status_code
        kwargs['context'] = context

        # Determine recovery strategy based on status code
        recovery = RecoveryStrategy.RETRY_EXPONENTIAL
        if status_code in [502, 503, 504]:  # Temporary server issues
            recovery = RecoveryStrategy.RETRY_LINEAR
        elif status_code == 500:  # Internal server error
            recovery = RecoveryStrategy.FALLBACK_SOURCE

        super().__init__(
            message,
            error_category=ErrorCategory.SERVER_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=recovery,
            **kwargs
        )


class ClientException(DataSourceException):
    """Client errors (4xx responses excluding rate limits and auth)"""

    def __init__(self, message: str, status_code: int = None, **kwargs):
        context = kwargs.get('context', {})
        if status_code:
            context['status_code'] = status_code
        kwargs['context'] = context

        # Client errors usually don't benefit from retries
        recovery = RecoveryStrategy.FALLBACK_SOURCE
        if status_code == 400:  # Bad request - might be ticker issue
            recovery = RecoveryStrategy.MANUAL_INTERVENTION

        super().__init__(
            message,
            error_category=ErrorCategory.CLIENT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=recovery,
            **kwargs
        )


# Data quality and parsing exceptions
class DataQualityException(DataSourceException):
    """Data quality and completeness issues"""

    def __init__(self, message: str, data_completeness: float = 0.0,
                 missing_fields: List[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context.update({
            'data_completeness': data_completeness,
            'missing_fields': missing_fields or [],
            'quality_threshold': 0.5  # Minimum acceptable completeness
        })
        kwargs['context'] = context

        # Use cache if available, otherwise degrade gracefully
        recovery = RecoveryStrategy.USE_CACHE if data_completeness < 0.3 else RecoveryStrategy.DEGRADE_GRACEFULLY

        super().__init__(
            message,
            error_category=ErrorCategory.DATA_QUALITY,
            severity=ErrorSeverity.LOW if data_completeness > 0.5 else ErrorSeverity.MEDIUM,
            recovery_strategy=recovery,
            **kwargs
        )


class DataParsingException(DataSourceException):
    """Data format and parsing errors"""

    def __init__(self, message: str, parsing_stage: str = None, **kwargs):
        context = kwargs.get('context', {})
        if parsing_stage:
            context['parsing_stage'] = parsing_stage
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.PARSING,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=RecoveryStrategy.FALLBACK_SOURCE,
            **kwargs
        )


class DataValidationException(DataSourceException):
    """Input validation and sanity check failures"""

    def __init__(self, message: str, field_name: str = None,
                 expected_range: tuple = None, actual_value: Any = None, **kwargs):
        context = kwargs.get('context', {})
        context.update({
            'field_name': field_name,
            'expected_range': expected_range,
            'actual_value': actual_value
        })
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recovery_strategy=RecoveryStrategy.DEGRADE_GRACEFULLY,
            **kwargs
        )


# Resource and system exceptions
class ResourceException(DataSourceException):
    """System resource exhaustion errors"""

    def __init__(self, message: str, resource_type: str = None, **kwargs):
        context = kwargs.get('context', {})
        if resource_type:
            context['resource_type'] = resource_type
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.CIRCUIT_BREAK,
            **kwargs
        )


# Circuit breaker exception
class CircuitBreakerOpenException(DataSourceException):
    """Circuit breaker is open, preventing requests"""

    def __init__(self, message: str, source: str, recovery_time: datetime = None, **kwargs):
        context = kwargs.get('context', {})
        if recovery_time:
            context['recovery_time'] = recovery_time.isoformat()
            context['recovery_in_seconds'] = (recovery_time - datetime.now()).total_seconds()
        kwargs['context'] = context

        super().__init__(
            message,
            error_category=ErrorCategory.CLIENT_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.FALLBACK_SOURCE,
            source=source,
            **kwargs
        )


def classify_error(exception: Exception, source: str = None, ticker: str = None) -> DataSourceException:
    """
    Classify generic exceptions into specific DataSourceException types

    Args:
        exception: The original exception to classify
        source: Data source where error occurred
        ticker: Ticker symbol being processed

    Returns:
        DataSourceException: Classified exception with appropriate recovery strategy
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__

    # Extract context from exception
    context = {
        'classification_timestamp': datetime.now().isoformat(),
        'original_type': error_type
    }

    # HTTP-specific errors
    if hasattr(exception, 'response') and exception.response is not None:
        status_code = exception.response.status_code
        context['status_code'] = status_code
        context['response_headers'] = dict(exception.response.headers)

        if status_code == 429:
            retry_after = None
            if 'retry-after' in exception.response.headers:
                try:
                    retry_after = int(exception.response.headers['retry-after'])
                except ValueError:
                    pass

            return RateLimitException(
                f"Rate limit exceeded for {source or 'unknown source'}",
                retry_after=retry_after,
                source=source,
                ticker=ticker,
                context=context,
                original_exception=exception
            )

        elif status_code in [401, 403]:
            return AuthenticationException(
                f"Authentication failed for {source or 'unknown source'}",
                source=source,
                ticker=ticker,
                context=context,
                original_exception=exception
            )

        elif 500 <= status_code < 600:
            return ServerException(
                f"Server error ({status_code}) from {source or 'unknown source'}",
                status_code=status_code,
                source=source,
                ticker=ticker,
                context=context,
                original_exception=exception
            )

        elif 400 <= status_code < 500:
            return ClientException(
                f"Client error ({status_code}) for {source or 'unknown source'}",
                status_code=status_code,
                source=source,
                ticker=ticker,
                context=context,
                original_exception=exception
            )

    # Network errors
    if error_type in ['ConnectionError', 'ConnectTimeout', 'ReadTimeout', 'HTTPSConnectionPool']:
        return NetworkException(
            f"Network error connecting to {source or 'unknown source'}: {error_str}",
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # Timeout errors
    if 'timeout' in error_str or 'timed out' in error_str or error_type in ['TimeoutError', 'ReadTimeoutError']:
        return TimeoutException(
            f"Request timed out for {source or 'unknown source'}",
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # Rate limiting (text-based detection)
    if any(phrase in error_str for phrase in ['rate limit', 'too many requests', '429']):
        return RateLimitException(
            f"Rate limit detected for {source or 'unknown source'}: {error_str}",
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # JSON/Parsing errors
    if error_type in ['JSONDecodeError', 'ValueError'] and 'json' in error_str:
        return DataParsingException(
            f"JSON parsing error from {source or 'unknown source'}: {error_str}",
            parsing_stage='json_decode',
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # Data validation errors
    if error_type in ['ValueError', 'TypeError'] and any(phrase in error_str for phrase in ['invalid', 'nan', 'null']):
        return DataValidationException(
            f"Data validation error from {source or 'unknown source'}: {error_str}",
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # Memory/Resource errors
    if error_type in ['MemoryError', 'OSError']:
        return ResourceException(
            f"Resource error: {error_str}",
            resource_type='memory' if error_type == 'MemoryError' else 'system',
            source=source,
            ticker=ticker,
            context=context,
            original_exception=exception
        )

    # Default classification
    return DataSourceException(
        f"Unclassified error from {source or 'unknown source'}: {error_str}",
        error_category=ErrorCategory.CLIENT_ERROR,
        severity=ErrorSeverity.MEDIUM,
        recovery_strategy=RecoveryStrategy.RETRY_EXPONENTIAL,
        source=source,
        ticker=ticker,
        context=context,
        original_exception=exception
    )


def create_error_context(source: str = None, ticker: str = None,
                        attempt: int = 0, response_time: float = None,
                        additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized error context for consistent logging and analysis

    Args:
        source: Data source identifier
        ticker: Stock ticker symbol
        attempt: Current retry attempt number
        response_time: Request response time in seconds
        additional_context: Additional context data

    Returns:
        Dict containing standardized error context
    """
    context = {
        'timestamp': datetime.now().isoformat(),
        'source': source,
        'ticker': ticker,
        'attempt': attempt,
        'response_time_seconds': response_time
    }

    if additional_context:
        context.update(additional_context)

    return context