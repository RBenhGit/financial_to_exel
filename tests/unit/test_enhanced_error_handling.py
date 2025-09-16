"""
Comprehensive Test Suite for Enhanced Error Handling System
===========================================================

Tests for:
- Exception classification and recovery strategies
- Retry logic with exponential backoff
- Circuit breaker pattern functionality
- Error handler integration
- Fallback source selection
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from core.data_processing.exceptions import (
    DataSourceException, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    RateLimitException, NetworkException, TimeoutException,
    AuthenticationException, ServerException, ClientException,
    DataQualityException, DataParsingException, DataValidationException,
    classify_error, create_error_context
)

from core.data_processing.error_handler import (
    EnhancedErrorHandler, RetryConfig, ErrorMetrics
)

from core.data_processing.circuit_breaker import (
    EnhancedCircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig,
    CircuitState, FailureType
)


class TestExceptionClassification:
    """Test exception classification and recovery strategies"""

    def test_rate_limit_exception_creation(self):
        """Test RateLimitException creation and properties"""
        error = RateLimitException(
            "Rate limit exceeded",
            retry_after=60,
            requests_remaining=0,
            source="yfinance",
            ticker="AAPL"
        )

        assert error.error_category == ErrorCategory.RATE_LIMIT
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.recovery_strategy == RecoveryStrategy.FALLBACK_SOURCE
        assert error.retry_after == 60
        assert error.source == "yfinance"
        assert error.ticker == "AAPL"
        assert error.context["requests_remaining"] == 0
        assert error.should_use_fallback()
        assert not error.is_retryable()

    def test_network_exception_creation(self):
        """Test NetworkException creation and properties"""
        error = NetworkException(
            "Connection timeout",
            source="alpha_vantage",
            ticker="MSFT"
        )

        assert error.error_category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.HIGH
        assert error.recovery_strategy == RecoveryStrategy.RETRY_EXPONENTIAL
        assert error.is_retryable()
        assert not error.should_use_fallback()

    def test_data_quality_exception_creation(self):
        """Test DataQualityException creation and properties"""
        missing_fields = ["current_price", "market_cap"]
        error = DataQualityException(
            "Incomplete data received",
            data_completeness=0.3,
            missing_fields=missing_fields,
            source="fmp",
            ticker="GOOGL"
        )

        assert error.error_category == ErrorCategory.DATA_QUALITY
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.recovery_strategy == RecoveryStrategy.DEGRADE_GRACEFULLY  # At 0.3 completeness, should degrade gracefully
        assert error.context["data_completeness"] == 0.3
        assert error.context["missing_fields"] == missing_fields
        assert not error.should_use_cache()  # At 0.3 completeness, should degrade gracefully, not use cache

    def test_error_classification_from_http_429(self):
        """Test classification of HTTP 429 errors"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'retry-after': '60'}

        mock_exception = Mock()
        mock_exception.response = mock_response

        classified = classify_error(mock_exception, source="yfinance", ticker="TESLA")

        assert isinstance(classified, RateLimitException)
        assert classified.source == "yfinance"
        assert classified.ticker == "TESLA"
        assert classified.retry_after == 60

    def test_error_classification_from_connection_error(self):
        """Test classification of connection errors"""
        mock_exception = ConnectionError("Connection failed")

        classified = classify_error(mock_exception, source="polygon")

        assert isinstance(classified, NetworkException)
        assert "Network error" in classified.message
        assert classified.source == "polygon"

    def test_error_classification_from_timeout(self):
        """Test classification of timeout errors"""
        mock_exception = TimeoutError("Request timed out")

        classified = classify_error(mock_exception, source="finnhub")

        assert isinstance(classified, TimeoutException)
        assert classified.error_category == ErrorCategory.TIMEOUT
        assert classified.source == "finnhub"

    def test_retry_delay_calculation(self):
        """Test retry delay calculation for different error types"""
        rate_limit_error = RateLimitException("Rate limited", retry_after=30)
        assert rate_limit_error.get_retry_delay(0) == 30.0

        network_error = NetworkException("Network failed")
        delay_1 = network_error.get_retry_delay(0)
        delay_2 = network_error.get_retry_delay(1)
        assert delay_2 > delay_1  # Exponential backoff

        timeout_error = TimeoutException("Timeout")
        delay_linear_1 = timeout_error.get_retry_delay(0)
        delay_linear_2 = timeout_error.get_retry_delay(1)
        assert delay_linear_2 > delay_linear_1  # Linear increase, but may not be exactly double

    def test_error_context_creation(self):
        """Test error context creation"""
        context = create_error_context(
            source="yfinance",
            ticker="AAPL",
            attempt=2,
            response_time=1.5,
            additional_context={"test_key": "test_value"}
        )

        assert context["source"] == "yfinance"
        assert context["ticker"] == "AAPL"
        assert context["attempt"] == 2
        assert context["response_time_seconds"] == 1.5
        assert context["test_key"] == "test_value"
        assert "timestamp" in context


class TestRetryLogic:
    """Test retry logic and backoff strategies"""

    def test_retry_config_creation(self):
        """Test RetryConfig creation and defaults"""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            backoff_factor=3.0
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.backoff_factor == 3.0
        assert config.jitter is True

    def test_error_handler_initialization(self):
        """Test EnhancedErrorHandler initialization"""
        retry_config = RetryConfig(max_retries=3)
        handler = EnhancedErrorHandler(retry_config=retry_config)

        assert handler.retry_config.max_retries == 3
        assert isinstance(handler.metrics, ErrorMetrics)

    def test_retry_delay_calculation(self):
        """Test retry delay calculation with different strategies"""
        handler = EnhancedErrorHandler()

        # Test rate limit error (should use longer delays)
        rate_limit_error = RateLimitException("Rate limited", retry_after=10)
        delay = handler.calculate_retry_delay(0, rate_limit_error)
        # Should use retry_after value plus potential jitter
        assert 10.0 <= delay <= 13.0  # Allow for jitter

        # Test network error with exponential backoff
        network_error = NetworkException("Network failed")
        delay_0 = handler.calculate_retry_delay(0, network_error)
        delay_1 = handler.calculate_retry_delay(1, network_error)
        delay_2 = handler.calculate_retry_delay(2, network_error)

        # Should show exponential growth (allowing for jitter)
        assert delay_1 > delay_0
        assert delay_2 > delay_1

    def test_should_retry_logic(self):
        """Test retry decision logic"""
        retry_config = RetryConfig(
            max_retries=3,
            retry_on_errors=[ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]
        )
        handler = EnhancedErrorHandler(retry_config=retry_config)

        # Network error should be retryable
        network_error = NetworkException("Network failed")
        assert handler.should_retry(network_error, 0)
        assert handler.should_retry(network_error, 1)
        assert handler.should_retry(network_error, 2)
        assert not handler.should_retry(network_error, 3)  # Max retries exceeded

        # Rate limit error should not be retryable (not in retry_on_errors)
        rate_limit_error = RateLimitException("Rate limited")
        assert not handler.should_retry(rate_limit_error, 0)

        # Non-retryable error by recovery strategy
        auth_error = AuthenticationException("Auth failed")
        assert not handler.should_retry(auth_error, 0)

    def test_error_metrics_recording(self):
        """Test error metrics recording and tracking"""
        handler = EnhancedErrorHandler()

        error1 = NetworkException("Network error 1", source="yfinance")
        error2 = RateLimitException("Rate limited", source="yfinance")
        error3 = NetworkException("Network error 2", source="alpha_vantage")

        handler.metrics.record_error(error1)
        handler.metrics.record_error(error2)
        handler.metrics.record_error(error3)

        assert handler.metrics.total_errors == 3
        assert handler.metrics.errors_by_category[ErrorCategory.NETWORK.value] == 2
        assert handler.metrics.errors_by_category[ErrorCategory.RATE_LIMIT.value] == 1
        assert handler.metrics.errors_by_source["yfinance"] == 2
        assert handler.metrics.errors_by_source["alpha_vantage"] == 1
        assert handler.metrics.consecutive_failures["yfinance"] == 2

    def test_error_handling_context_success(self):
        """Test error handling context manager with successful operation"""
        handler = EnhancedErrorHandler()

        with handler.error_handling_context("yfinance", "AAPL", "test_operation"):
            # Simulate successful operation
            pass

        # Should complete without raising exceptions

    def test_error_handling_context_with_retries(self):
        """Test error handling context manager with retry logic"""
        retry_config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        handler = EnhancedErrorHandler(retry_config=retry_config)

        call_count = 0

        def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Connection failed")

        # This should exhaust retries and raise an error
        with pytest.raises(DataSourceException):
            with handler.error_handling_context("yfinance", "AAPL", "test"):
                failing_operation()

        # Should have recorded the error
        assert handler.metrics.total_errors > 0


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization"""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        cb = EnhancedCircuitBreaker("test_service", config)

        assert cb.name == "test_service"
        assert cb.config.failure_threshold == 3
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute()

    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening on failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        cb = EnhancedCircuitBreaker("test_service", config)

        # Record failures up to threshold
        for i in range(3):
            cb.record_failure(Exception(f"Failure {i}"))

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN
        assert not cb.can_execute()

    def test_circuit_breaker_failure_rate_threshold(self):
        """Test circuit breaker opening on failure rate"""
        config = CircuitBreakerConfig(
            failure_threshold=10,  # High threshold
            failure_rate_threshold=0.6,
            volume_threshold=5
        )
        cb = EnhancedCircuitBreaker("test_service", config)

        # Record mixed results: 4 failures, 2 successes (66% failure rate)
        cb.record_failure(Exception("Failure 1"))
        cb.record_failure(Exception("Failure 2"))
        cb.record_success()
        cb.record_failure(Exception("Failure 3"))
        cb.record_failure(Exception("Failure 4"))
        cb.record_success()

        # Circuit should be open due to high failure rate
        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_recovery_timeout(self):
        """Test circuit breaker recovery after timeout"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        cb = EnhancedCircuitBreaker("test_service", config)

        # Trigger circuit opening
        cb.record_failure(Exception("Failure 1"))
        cb.record_failure(Exception("Failure 2"))
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should transition to half-open when checked
        assert cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_half_open_success(self):
        """Test circuit breaker closing after successful half-open attempts"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2
        )
        cb = EnhancedCircuitBreaker("test_service", config)

        # Open circuit
        cb.record_failure(Exception("Failure 1"))
        cb.record_failure(Exception("Failure 2"))
        assert cb.state == CircuitState.OPEN

        # Wait and transition to half-open
        time.sleep(0.2)
        assert cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

        # Record successful attempts
        cb.record_success()
        cb.record_success()

        # Should close circuit
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker reopening on half-open failure"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = EnhancedCircuitBreaker("test_service", config)

        # Open circuit
        cb.record_failure(Exception("Failure 1"))
        cb.record_failure(Exception("Failure 2"))

        # Wait and transition to half-open
        time.sleep(0.2)
        cb.can_execute()  # Triggers transition

        # Fail in half-open state
        cb.record_failure(Exception("Half-open failure"))

        # Should reopen circuit
        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_call_protection_context(self):
        """Test circuit breaker call protection context manager"""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = EnhancedCircuitBreaker("test_service", config)

        # Successful call
        with cb.call_protection():
            pass

        assert cb.metrics.successful_requests == 1

        # Failed call
        with pytest.raises(ValueError):
            with cb.call_protection():
                raise ValueError("Test failure")

        assert cb.metrics.failed_requests == 1

    def test_circuit_breaker_state_info(self):
        """Test circuit breaker state information reporting"""
        cb = EnhancedCircuitBreaker("test_service")

        # Record some activity
        cb.record_success(response_time=0.1)
        cb.record_failure(Exception("Test failure"))

        state_info = cb.get_state_info()

        assert state_info["name"] == "test_service"
        assert state_info["state"] == "closed"
        assert state_info["total_requests"] == 2
        assert state_info["successful_requests"] == 1
        assert state_info["failed_requests"] == 1
        assert "last_success" in state_info
        assert "last_failure" in state_info

    def test_circuit_breaker_force_states(self):
        """Test forcing circuit breaker states"""
        cb = EnhancedCircuitBreaker("test_service")

        # Force open
        cb.force_open("Testing")
        assert cb.state == CircuitState.OPEN

        # Force close
        cb.force_close("Testing")
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset functionality"""
        cb = EnhancedCircuitBreaker("test_service")

        # Add some activity
        cb.record_success()
        cb.record_failure(Exception("Test"))

        # Reset
        cb.reset()

        # Should be back to initial state
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.total_requests == 0
        assert cb.metrics.successful_requests == 0
        assert cb.metrics.failed_requests == 0


class TestCircuitBreakerManager:
    """Test circuit breaker manager functionality"""

    def test_circuit_breaker_manager_initialization(self):
        """Test circuit breaker manager initialization"""
        config = CircuitBreakerConfig(failure_threshold=5)
        manager = CircuitBreakerManager(config)

        assert manager.default_config.failure_threshold == 5

    def test_get_or_create_circuit_breaker(self):
        """Test getting or creating circuit breakers"""
        manager = CircuitBreakerManager()

        # Create new circuit breaker
        cb1 = manager.get_or_create_circuit_breaker("service1")
        assert cb1.name == "service1"
        assert cb1 in manager.circuit_breakers.values()

        # Get existing circuit breaker
        cb2 = manager.get_or_create_circuit_breaker("service1")
        assert cb1 is cb2

    def test_circuit_breaker_manager_health_summary(self):
        """Test health summary generation"""
        manager = CircuitBreakerManager()

        # Create some circuit breakers with different states
        cb1 = manager.get_or_create_circuit_breaker("service1")
        cb2 = manager.get_or_create_circuit_breaker("service2")

        # Make service2 fail
        for _ in range(5):
            cb2.record_failure(Exception("Test failure"))

        health_summary = manager.get_health_summary()

        assert health_summary["total_circuit_breakers"] == 2
        assert health_summary["states"]["closed"] == 1
        assert health_summary["states"]["open"] == 1
        assert len(health_summary["recommendations"]) > 0

    def test_circuit_breaker_manager_remove(self):
        """Test removing circuit breakers"""
        manager = CircuitBreakerManager()

        cb = manager.get_or_create_circuit_breaker("service1")
        assert "service1" in manager.circuit_breakers

        removed = manager.remove_circuit_breaker("service1")
        assert removed
        assert "service1" not in manager.circuit_breakers

        # Removing non-existent service
        removed = manager.remove_circuit_breaker("nonexistent")
        assert not removed

    def test_circuit_breaker_manager_reset_all(self):
        """Test resetting all circuit breakers"""
        manager = CircuitBreakerManager()

        # Create and modify circuit breakers
        cb1 = manager.get_or_create_circuit_breaker("service1")
        cb2 = manager.get_or_create_circuit_breaker("service2")

        cb1.record_failure(Exception("Test"))
        cb2.record_success()

        # Reset all
        manager.reset_all()

        # All should be back to initial state
        for cb in manager.circuit_breakers.values():
            assert cb.state == CircuitState.CLOSED
            assert cb.metrics.total_requests == 0


class TestIntegrationScenarios:
    """Test integrated error handling scenarios"""

    def test_rate_limit_with_fallback(self):
        """Test rate limit handling with fallback source selection"""
        # Mock data source hierarchy
        mock_hierarchy = Mock()
        mock_hierarchy.get_optimal_source_hierarchy.return_value = [
            Mock(value="alpha_vantage")
        ]

        retry_config = RetryConfig(max_retries=2)
        handler = EnhancedErrorHandler(
            retry_config=retry_config,
            data_source_hierarchy=mock_hierarchy
        )

        # Test fallback selection
        fallback = handler.select_fallback_source("yfinance")
        assert fallback == "alpha_vantage"

    def test_network_error_with_circuit_breaker(self):
        """Test network error handling with circuit breaker integration"""
        cb_manager = CircuitBreakerManager()
        cb = cb_manager.get_or_create_circuit_breaker("yfinance")

        handler = EnhancedErrorHandler(circuit_breaker_manager=cb_manager)

        # Simulate network error handling
        network_error = NetworkException("Connection failed", source="yfinance")
        should_retry, delay = handler.handle_network_error(network_error, 0)

        assert should_retry
        assert delay > 0

        # Record the failure in metrics
        handler.metrics.record_error(network_error)
        assert handler.metrics.total_errors > 0

    def test_comprehensive_error_handling_flow(self):
        """Test comprehensive error handling flow"""
        cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb_manager = CircuitBreakerManager(cb_config)
        retry_config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)

        handler = EnhancedErrorHandler(
            retry_config=retry_config,
            circuit_breaker_manager=cb_manager
        )

        def simulated_api_call():
            raise ConnectionError("Network failure")

        # This should exhaust retries and record failure
        with pytest.raises(DataSourceException):
            with handler.error_handling_context("yfinance", "AAPL", "test"):
                simulated_api_call()

        # Verify error was recorded
        assert handler.metrics.total_errors > 0

    def test_error_summary_generation(self):
        """Test comprehensive error summary generation"""
        handler = EnhancedErrorHandler()

        # Generate various errors
        errors = [
            NetworkException("Network 1", source="yfinance"),
            NetworkException("Network 2", source="yfinance"),
            RateLimitException("Rate limit", source="alpha_vantage"),
            TimeoutException("Timeout", source="fmp")
        ]

        for error in errors:
            handler.metrics.record_error(error)

        summary = handler.get_error_summary()

        assert summary["total_errors"] == 4
        assert summary["errors_by_category"]["network"] == 2
        assert summary["errors_by_category"]["rate_limit"] == 1
        assert summary["errors_by_category"]["timeout"] == 1
        assert summary["errors_by_source"]["yfinance"] == 2
        assert len(summary["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])