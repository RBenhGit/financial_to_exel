"""
Error Handling Package
=====================

Comprehensive error handling infrastructure for the financial analysis toolkit.

This package provides:
- API failure handling with retry logic
- Circuit breaker patterns for service resilience  
- Exponential backoff strategies
- User-friendly error messaging
- Data quality validation and scoring
- Graceful degradation mechanisms

Main Components:
- APIErrorHandler: Core error handling for external API calls
- DataQualityValidator: Validation and scoring for data integrity
- UserMessageHandler: User-friendly error communication
- GracefulDegradation: Fallback strategies when services fail

Usage:
    from core.error_handling import get_error_handler, with_api_error_handling
    
    # Using decorator
    @with_api_error_handling("yfinance")
    def fetch_stock_data(ticker):
        return yf.Ticker(ticker).info
    
    # Using context manager
    handler = get_error_handler()
    result, error = handler.execute_with_retry(some_api_call, "service_name")
"""

from .api_error_handler import (
    APIErrorHandler,
    APIFailure, 
    APIFailureCategory,
    RetryConfig,
    RetryStrategy,
    CircuitBreakerManager,
    get_error_handler,
    with_api_error_handling
)

from .data_quality_validator import (
    DataQualityValidator,
    DataQualityLevel,
    DataSourceReliability,
    QualityMetrics,
    ValidationResult,
    QualityReport
)

from .graceful_degradation import (
    GracefulDegradationManager,
    DegradationLevel,
    FallbackDataSource,
    DegradationContext,
    DegradationResult,
    get_degradation_manager
)

from .user_message_handler import (
    UserMessageHandler,
    MessageSeverity,
    MessageCategory,
    UserMessage,
    StreamlitMessenger,
    get_message_handler,
    get_streamlit_messenger
)

__all__ = [
    'APIErrorHandler',
    'APIFailure',
    'APIFailureCategory', 
    'RetryConfig',
    'RetryStrategy',
    'CircuitBreakerManager',
    'get_error_handler',
    'with_api_error_handling',
    'DataQualityValidator',
    'DataQualityLevel',
    'DataSourceReliability',
    'QualityMetrics',
    'ValidationResult',
    'QualityReport',
    'GracefulDegradationManager',
    'DegradationLevel',
    'FallbackDataSource',
    'DegradationContext',
    'DegradationResult',
    'get_degradation_manager',
    'UserMessageHandler',
    'MessageSeverity',
    'MessageCategory',
    'UserMessage',
    'StreamlitMessenger',
    'get_message_handler',
    'get_streamlit_messenger'
]