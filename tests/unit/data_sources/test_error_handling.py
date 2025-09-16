"""
Test suite for enhanced error handling and recovery mechanisms
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from core.data_sources.error_handling import (
    ErrorType,
    ErrorSeverity,
    ErrorInfo,
    ErrorClassifier,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RetryHandler,
    RetryConfig,
    DataSourceErrorHandler,
    DataSourceException,
    NetworkException,
    APIException,
    with_error_handling,
    get_error_handler,
    register_error_handler,
)


class TestErrorClassifier:
    """Test error classification system"""

    def setup_method(self):
        self.classifier = ErrorClassifier()

    def test_network_error_classification(self):
        """Test network error classification"""
        exception = Exception("Connection timeout occurred")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.NETWORK_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.should_retry is True
        assert error_info.backoff_seconds == 2.0

    def test_rate_limit_error_classification(self):
        """Test rate limit error classification"""
        exception = Exception("Rate limit exceeded - too many requests")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.API_RATE_LIMIT
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is True
        assert error_info.backoff_seconds == 60.0

    def test_authentication_error_classification(self):
        """Test authentication error classification"""
        exception = Exception("401 Unauthorized - Invalid API key")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.INVALID_API_KEY
        assert error_info.severity == ErrorSeverity.CRITICAL
        assert error_info.should_retry is False
        assert error_info.circuit_breaker_trigger is True

    def test_server_error_classification(self):
        """Test server error classification"""
        exception = Exception("500 Internal Server Error")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.SERVER_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.should_retry is True
        assert error_info.backoff_seconds == 5.0

    def test_client_error_classification(self):
        """Test client error classification"""
        exception = Exception("400 Bad Request - Invalid symbol")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.INVALID_SYMBOL
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is False

    def test_excel_error_classification(self):
        """Test Excel file error classification"""
        exception = Exception("Excel file not found or corrupted")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.EXCEL_FILE_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.should_retry is False

    def test_unknown_error_classification(self):
        """Test unknown error classification"""
        exception = Exception("Some unknown error occurred")
        error_info = self.classifier.classify_error(exception)

        assert error_info.error_type == ErrorType.UNKNOWN_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is True

    def test_error_with_context(self):
        """Test error classification with context"""
        exception = Exception("Network error")
        context = {"source": "yahoo_finance", "ticker": "AAPL"}
        error_info = self.classifier.classify_error(exception, context)

        assert error_info.context == context
        assert "source" in error_info.context
        assert error_info.context["ticker"] == "AAPL"


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def setup_method(self):
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1.0,
            success_threshold=2,
            timeout_duration=0.5
        )
        self.circuit_breaker = CircuitBreaker("test_circuit", config)

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        def successful_function():
            return "success"

        result = self.circuit_breaker.call(successful_function)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after failures"""
        def failing_function():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_function)
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED

        # Second failure - should open circuit
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_function)
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_open_state_rejection(self):
        """Test circuit breaker rejects calls in open state"""
        # Force circuit to open
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.last_failure_time = datetime.now()

        def any_function():
            return "should not execute"

        with pytest.raises(DataSourceException) as exc_info:
            self.circuit_breaker.call(any_function)

        assert "Circuit breaker" in str(exc_info.value)

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        # Force circuit to open with old timestamp
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=2)

        def successful_function():
            return "success"

        # First call should move to half-open
        result = self.circuit_breaker.call(successful_function)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        # Second successful call should close circuit
        result = self.circuit_breaker.call(successful_function)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_timeout(self):
        """Test circuit breaker timeout functionality"""
        def slow_function():
            time.sleep(1.0)  # Longer than timeout
            return "should timeout"

        with pytest.raises(Exception):
            self.circuit_breaker.call(slow_function)

    def test_circuit_breaker_state_info(self):
        """Test circuit breaker state information"""
        state_info = self.circuit_breaker.get_state()

        assert state_info["name"] == "test_circuit"
        assert state_info["state"] == CircuitBreakerState.CLOSED.value
        assert state_info["failure_count"] == 0
        assert state_info["success_count"] == 0


class TestRetryHandler:
    """Test retry logic with exponential backoff"""

    def setup_method(self):
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            jitter=False  # Disable jitter for predictable testing
        )
        self.retry_handler = RetryHandler(config)

    def test_successful_execution_no_retry(self):
        """Test successful execution without retries"""
        mock_func = Mock(return_value="success")

        result = self.retry_handler.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_retryable_error(self):
        """Test retry on retryable errors"""
        mock_func = Mock()
        mock_func.side_effect = [
            Exception("Network timeout"),  # First call fails
            Exception("Connection error"),  # Second call fails
            "success"  # Third call succeeds
        ]

        result = self.retry_handler.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_no_retry_on_non_retryable_error(self):
        """Test no retry on non-retryable errors"""
        mock_func = Mock()
        mock_func.side_effect = Exception("401 Unauthorized")

        with pytest.raises(APIException):
            self.retry_handler.execute_with_retry(mock_func)

        assert mock_func.call_count == 1

    def test_max_attempts_reached(self):
        """Test behavior when max attempts are reached"""
        mock_func = Mock()
        mock_func.side_effect = Exception("Network error")

        with pytest.raises(NetworkException):
            self.retry_handler.execute_with_retry(mock_func)

        assert mock_func.call_count == 3  # max_attempts

    def test_delay_calculation(self):
        """Test delay calculation with exponential backoff"""
        # Create handler with higher max_delay to avoid capping
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=10.0,  # Higher max to avoid capping
            jitter=False
        )
        handler = RetryHandler(config)

        delays = []
        for attempt in range(1, 4):
            delay = handler._calculate_delay(attempt, 1.0)
            delays.append(delay)

        # Check exponential growth (base_delay * 2^(attempt-1))
        assert delays[0] == 1.0  # 1.0 * 2^0
        assert delays[1] == 2.0  # 1.0 * 2^1
        assert delays[2] == 4.0  # 1.0 * 2^2

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        config = RetryConfig(max_delay=2.0, jitter=False)
        handler = RetryHandler(config)

        delay = handler._calculate_delay(10, 1.0)  # Would be very large without cap
        assert delay <= 2.0


class TestDataSourceErrorHandler:
    """Test comprehensive data source error handler"""

    def setup_method(self):
        retry_config = RetryConfig(max_attempts=2, base_delay=0.1, jitter=False)
        circuit_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0)
        self.error_handler = DataSourceErrorHandler(
            "test_handler",
            retry_config,
            circuit_config
        )

    def test_successful_execution(self):
        """Test successful execution tracking"""
        mock_func = Mock(return_value="success")

        result = self.error_handler.execute(mock_func)

        assert result == "success"
        assert self.error_handler.success_count == 1
        assert self.error_handler.total_requests == 1

    def test_error_tracking(self):
        """Test error tracking and history"""
        mock_func = Mock()
        mock_func.side_effect = Exception("401 Unauthorized")

        with pytest.raises(APIException):
            self.error_handler.execute(mock_func)

        assert len(self.error_handler.error_history) == 1
        assert self.error_handler.error_history[0].error_type == ErrorType.INVALID_API_KEY
        assert self.error_handler.total_requests == 1

    def test_health_status(self):
        """Test health status reporting"""
        # Execute some successful requests
        mock_func = Mock(return_value="success")
        self.error_handler.execute(mock_func)
        self.error_handler.execute(mock_func)

        # Execute a failed request
        mock_func.side_effect = Exception("Network error")
        with pytest.raises(NetworkException):
            self.error_handler.execute(mock_func)

        health_status = self.error_handler.get_health_status()

        assert health_status["name"] == "test_handler"
        assert health_status["total_requests"] == 3
        assert health_status["success_count"] == 2
        assert health_status["error_count"] == 1
        assert health_status["success_rate"] == 2/3
        assert len(health_status["recent_errors"]) == 1
        assert "circuit_breaker" in health_status

    def test_circuit_breaker_integration(self):
        """Test integration with circuit breaker"""
        mock_func = Mock()
        mock_func.side_effect = Exception("Server error")

        # First two failures should open circuit
        with pytest.raises(APIException):
            self.error_handler.execute(mock_func)
        with pytest.raises(APIException):
            self.error_handler.execute(mock_func)

        # Third call should be rejected by circuit breaker
        with pytest.raises(DataSourceException) as exc_info:
            self.error_handler.execute(mock_func)

        assert "Circuit breaker" in str(exc_info.value)

    def test_manual_circuit_breaker_reset(self):
        """Test manual circuit breaker reset"""
        # Force circuit open
        self.error_handler.circuit_breaker.state = CircuitBreakerState.OPEN

        # Reset circuit
        self.error_handler.reset_circuit_breaker()

        assert self.error_handler.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.error_handler.circuit_breaker.failure_count == 0


class TestErrorHandlingDecorator:
    """Test error handling decorator"""

    def test_decorator_basic_functionality(self):
        """Test basic decorator functionality"""
        @with_error_handling(name="test_func", enable_circuit_breaker=False)
        def test_function(value):
            if value == "fail":
                raise Exception("Test failure")
            return f"success_{value}"

        # Test successful call
        result = test_function("test")
        assert result == "success_test"

        # Test failed call
        with pytest.raises(DataSourceException):
            test_function("fail")

        # Check that error handler is attached
        assert hasattr(test_function, '_error_handler')
        assert test_function._error_handler.name == "test_func"

    def test_decorator_with_retry(self):
        """Test decorator with retry functionality"""
        call_count = 0

        @with_error_handling(
            name="retry_func",
            retry_config=RetryConfig(max_attempts=3, base_delay=0.1),
            enable_circuit_breaker=False
        )
        def retry_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return "success"

        result = retry_function()
        assert result == "success"
        assert call_count == 3


class TestGlobalErrorHandlerRegistry:
    """Test global error handler registry"""

    def test_register_and_get_error_handler(self):
        """Test registering and retrieving error handlers"""
        handler = DataSourceErrorHandler("test_global_handler")
        register_error_handler(handler)

        retrieved_handler = get_error_handler("test_global_handler")
        assert retrieved_handler is handler

        # Test non-existent handler
        assert get_error_handler("non_existent") is None

    def test_global_health_status(self):
        """Test global health status reporting"""
        from core.data_sources.error_handling import get_all_health_status

        # Register a couple of handlers
        handler1 = DataSourceErrorHandler("handler_1")
        handler2 = DataSourceErrorHandler("handler_2")
        register_error_handler(handler1)
        register_error_handler(handler2)

        health_status = get_all_health_status()

        assert "handler_1" in health_status
        assert "handler_2" in health_status
        assert health_status["handler_1"]["name"] == "handler_1"
        assert health_status["handler_2"]["name"] == "handler_2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])