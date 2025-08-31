"""
API Error Handling Module
========================

This module provides comprehensive error handling for external API calls with
retry mechanisms, circuit breaker patterns, and graceful degradation.

Features:
- Exponential backoff retry logic
- Circuit breaker pattern for failing services
- API failure categorization and response strategies
- User-friendly error messages with actionable guidance
- Performance monitoring and logging

Classes:
    APIErrorHandler: Main error handling coordinator
    RetryStrategy: Configurable retry mechanisms
    CircuitBreakerManager: Circuit breaker implementation
    APIFailureCategory: Classification of API failures
"""

import time
import logging
import functools
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, Tuple, List
from dataclasses import dataclass, field
import random


logger = logging.getLogger(__name__)


class APIFailureCategory(Enum):
    """Categories of API failures for targeted handling strategies"""
    RATE_LIMIT = "rate_limit"           # 429 errors, rate limit exceeded
    AUTHENTICATION = "authentication"   # 401/403 errors, invalid API keys
    NETWORK_ERROR = "network_error"     # Connection timeouts, DNS failures
    SERVER_ERROR = "server_error"       # 5xx errors, server downtime
    DATA_ERROR = "data_error"          # Invalid response format, missing data
    QUOTA_EXCEEDED = "quota_exceeded"   # Monthly/daily quota limits
    MAINTENANCE = "maintenance"         # Planned maintenance windows
    UNKNOWN = "unknown"                # Unclassified errors


@dataclass
class APIFailure:
    """Data class for API failure information"""
    category: APIFailureCategory
    original_error: Exception
    service_name: str
    error_message: str
    user_message: str
    retry_after: Optional[int] = None
    is_temporary: bool = True
    suggested_action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RetryConfig:
    """Configuration for retry strategies"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: str = "exponential"  # "fixed", "linear", "exponential"


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds


class RetryStrategy:
    """Implements various retry strategies with exponential backoff"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if self.config.backoff_strategy == "fixed":
            delay = self.config.base_delay
        elif self.config.backoff_strategy == "linear":
            delay = self.config.base_delay * attempt
        elif self.config.backoff_strategy == "exponential":
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        else:
            delay = self.config.base_delay
            
        # Cap at maximum delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
            
        return max(delay, 0)
    
    def should_retry(self, attempt: int, failure: APIFailure) -> bool:
        """Determine if we should retry based on attempt count and failure type"""
        if attempt >= self.config.max_attempts:
            return False
            
        # Don't retry certain failure types
        non_retryable = {
            APIFailureCategory.AUTHENTICATION,
            APIFailureCategory.QUOTA_EXCEEDED
        }
        
        if failure.category in non_retryable:
            return False
            
        return failure.is_temporary


class CircuitBreakerManager:
    """Implements circuit breaker pattern to prevent cascading failures"""
    
    def __init__(self):
        self.services: Dict[str, CircuitBreakerState] = {}
        
    def get_service_state(self, service_name: str) -> CircuitBreakerState:
        """Get or create circuit breaker state for service"""
        if service_name not in self.services:
            self.services[service_name] = CircuitBreakerState()
        return self.services[service_name]
    
    def is_call_allowed(self, service_name: str) -> bool:
        """Check if API call is allowed based on circuit breaker state"""
        state = self.get_service_state(service_name)
        
        if state.state == "CLOSED":
            return True
        elif state.state == "OPEN":
            # Check if we should transition to HALF_OPEN
            if (state.last_failure_time and 
                datetime.now() - state.last_failure_time > timedelta(seconds=state.recovery_timeout)):
                state.state = "HALF_OPEN"
                logger.info(f"Circuit breaker for {service_name} transitioning to HALF_OPEN")
                return True
            return False
        elif state.state == "HALF_OPEN":
            return True
            
        return False
    
    def record_success(self, service_name: str):
        """Record successful API call"""
        state = self.get_service_state(service_name)
        if state.state == "HALF_OPEN":
            state.state = "CLOSED"
            state.failure_count = 0
            state.last_failure_time = None
            logger.info(f"Circuit breaker for {service_name} CLOSED after successful call")
    
    def record_failure(self, service_name: str, failure: APIFailure):
        """Record API failure and update circuit breaker state"""
        state = self.get_service_state(service_name)
        state.failure_count += 1
        state.last_failure_time = datetime.now()
        
        if state.failure_count >= state.failure_threshold and state.state == "CLOSED":
            state.state = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} OPENED after {state.failure_count} failures")
        elif state.state == "HALF_OPEN":
            state.state = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} returned to OPEN after failed test call")


class APIErrorHandler:
    """
    Main API error handler with retry, circuit breaker, and user-friendly messaging
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_strategy = RetryStrategy(retry_config or RetryConfig())
        self.circuit_breaker = CircuitBreakerManager()
        
    def classify_error(self, error: Exception, service_name: str) -> APIFailure:
        """Classify an API error into appropriate category with user guidance"""
        error_str = str(error).lower()
        
        # Rate limiting errors
        if "429" in error_str or "rate limit" in error_str:
            return APIFailure(
                category=APIFailureCategory.RATE_LIMIT,
                original_error=error,
                service_name=service_name,
                error_message=str(error),
                user_message="API rate limit exceeded. The system will automatically retry after a brief delay.",
                suggested_action="Consider upgrading to a higher tier API plan for more requests per minute.",
                is_temporary=True
            )
            
        # Authentication errors
        if any(code in error_str for code in ["401", "403", "unauthorized", "invalid api key", "invalid x-api-key"]):
            return APIFailure(
                category=APIFailureCategory.AUTHENTICATION,
                original_error=error,
                service_name=service_name,
                error_message=str(error),
                user_message=f"Authentication failed for {service_name}. Please check your API key configuration.",
                suggested_action="Verify your API key is valid and properly set in environment variables.",
                is_temporary=False
            )
            
        # Network errors
        if any(term in error_str for term in ["timeout", "connection", "network", "dns", "unreachable"]):
            return APIFailure(
                category=APIFailureCategory.NETWORK_ERROR,
                original_error=error,
                service_name=service_name,
                error_message=str(error),
                user_message="Network connection issue. The system will retry automatically.",
                suggested_action="Check your internet connection. If issues persist, the service may be down.",
                is_temporary=True
            )
            
        # Server errors (5xx)
        if any(code in error_str for code in ["500", "502", "503", "504", "server error"]):
            return APIFailure(
                category=APIFailureCategory.SERVER_ERROR,
                original_error=error,
                service_name=service_name,
                error_message=str(error),
                user_message=f"{service_name} is experiencing server issues. Will retry automatically.",
                suggested_action="This is a temporary server issue. The system will retry with exponential backoff.",
                is_temporary=True
            )
            
        # Quota exceeded
        if any(term in error_str for term in ["quota", "limit exceeded", "monthly limit"]):
            return APIFailure(
                category=APIFailureCategory.QUOTA_EXCEEDED,
                original_error=error,
                service_name=service_name,
                error_message=str(error),
                user_message=f"API quota exceeded for {service_name}. Switch to historical data analysis.",
                suggested_action="Upgrade your API plan or wait until quota resets next month.",
                is_temporary=False
            )
            
        # Default to unknown error
        return APIFailure(
            category=APIFailureCategory.UNKNOWN,
            original_error=error,
            service_name=service_name,
            error_message=str(error),
            user_message="An unexpected error occurred. The system will attempt to retry.",
            suggested_action="If this error persists, please check the logs for more details.",
            is_temporary=True
        )
    
    def execute_with_retry(self, func: Callable, service_name: str, *args, **kwargs) -> Tuple[Any, Optional[APIFailure]]:
        """
        Execute a function with retry logic and circuit breaker protection
        
        Args:
            func: Function to execute
            service_name: Name of the service for circuit breaker tracking
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Tuple of (result, failure_info) where failure_info is None on success
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_call_allowed(service_name):
            failure = APIFailure(
                category=APIFailureCategory.SERVER_ERROR,
                original_error=Exception("Circuit breaker OPEN"),
                service_name=service_name,
                error_message="Service temporarily unavailable due to repeated failures",
                user_message=f"{service_name} is temporarily unavailable. Using cached/historical data instead.",
                suggested_action="The system will automatically retry when the service recovers.",
                is_temporary=True
            )
            return None, failure
        
        last_failure = None
        
        for attempt in range(1, self.retry_strategy.config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                
                # Success - record in circuit breaker and return
                self.circuit_breaker.record_success(service_name)
                return result, None
                
            except Exception as e:
                failure = self.classify_error(e, service_name)
                last_failure = failure
                
                logger.warning(f"Attempt {attempt}/{self.retry_strategy.config.max_attempts} failed for {service_name}: {failure.error_message}")
                
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure(service_name, failure)
                
                # Check if we should retry
                if not self.retry_strategy.should_retry(attempt, failure):
                    logger.error(f"Not retrying {service_name} due to failure type: {failure.category}")
                    break
                    
                # If this is the last attempt, don't wait
                if attempt >= self.retry_strategy.config.max_attempts:
                    break
                    
                # Calculate and wait for retry delay
                delay = self.retry_strategy.calculate_delay(attempt)
                logger.info(f"Retrying {service_name} in {delay:.2f} seconds (attempt {attempt + 1})")
                time.sleep(delay)
        
        return None, last_failure
    
    def with_error_handling(self, service_name: str):
        """Decorator for adding error handling to API calls"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result, failure = self.execute_with_retry(func, service_name, *args, **kwargs)
                if failure:
                    logger.error(f"API call failed: {failure.user_message}")
                    raise failure.original_error
                return result
            return wrapper
        return decorator
    
    def get_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all monitored services"""
        health_status = {}
        
        for service_name, state in self.circuit_breaker.services.items():
            health_status[service_name] = {
                'state': state.state,
                'failure_count': state.failure_count,
                'last_failure': state.last_failure_time.isoformat() if state.last_failure_time else None,
                'is_healthy': state.state == "CLOSED"
            }
            
        return health_status
    
    def reset_service_circuit_breaker(self, service_name: str):
        """Manually reset circuit breaker for a service"""
        if service_name in self.circuit_breaker.services:
            state = self.circuit_breaker.services[service_name]
            state.state = "CLOSED"
            state.failure_count = 0
            state.last_failure_time = None
            logger.info(f"Circuit breaker for {service_name} manually reset")


# Global error handler instance
_global_error_handler = None


def get_error_handler() -> APIErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = APIErrorHandler()
    return _global_error_handler


def with_api_error_handling(service_name: str):
    """Decorator for adding API error handling to functions"""
    return get_error_handler().with_error_handling(service_name)