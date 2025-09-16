"""
Enhanced Error Handling Integration for Centralized Data Manager
===============================================================

Integration layer that enhances the existing CentralizedDataManager with:
- Advanced error classification and recovery
- Circuit breaker pattern integration
- Enhanced retry logic with exponential backoff
- Fallback source management
- Comprehensive error metrics and monitoring
"""

import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from ..exceptions import (
    DataSourceException, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    classify_error, RateLimitException, NetworkException
)
from ..error_handler import EnhancedErrorHandler, RetryConfig, get_error_handler
from ..circuit_breaker import (
    CircuitBreakerManager, CircuitBreakerConfig, EnhancedCircuitBreaker,
    get_circuit_breaker_manager
)

logger = logging.getLogger(__name__)


class ErrorHandlingMixin:
    """
    Mixin class to add enhanced error handling capabilities to the CentralizedDataManager
    """

    def __init__(self, *args, **kwargs):
        """Initialize error handling components"""
        super().__init__(*args, **kwargs)

        # Initialize enhanced error handling
        self._init_error_handling()

    def _init_error_handling(self):
        """Initialize error handling infrastructure"""
        # Configure retry behavior
        retry_config = RetryConfig(
            max_retries=4,
            base_delay=2.0,
            max_delay=120.0,
            backoff_factor=2.0,
            jitter=True
        )

        # Configure circuit breaker
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=300,  # 5 minutes
            success_threshold=3,
            failure_rate_threshold=0.6,
            volume_threshold=10
        )

        # Get global managers
        self.circuit_breaker_manager = get_circuit_breaker_manager(circuit_config)
        self.error_handler = get_error_handler(
            retry_config=retry_config,
            circuit_breaker_manager=self.circuit_breaker_manager,
            rate_limiter=getattr(self, 'rate_limiter', None),
            data_source_hierarchy=getattr(self, 'hierarchy_manager', None)
        )

        # Initialize circuit breakers for known sources
        self._init_circuit_breakers()

        logger.info("Enhanced error handling initialized for centralized data manager")

    def _init_circuit_breakers(self):
        """Initialize circuit breakers for known data sources"""
        data_sources = [
            'yfinance', 'excel_data', 'fmp', 'alpha_vantage',
            'polygon', 'finnhub', 'market_data'
        ]

        for source in data_sources:
            # Create health check function for API sources
            health_check_func = None
            if source in ['yfinance', 'fmp', 'alpha_vantage', 'polygon', 'finnhub']:
                health_check_func = self._create_health_check_func(source)

            self.circuit_breaker_manager.get_or_create_circuit_breaker(
                name=source,
                health_check_func=health_check_func
            )

        logger.debug(f"Initialized circuit breakers for {len(data_sources)} data sources")

    def _create_health_check_func(self, source: str):
        """Create health check function for a data source"""
        def health_check():
            try:
                # Perform lightweight health check based on source type
                if source == 'yfinance':
                    return self._check_yfinance_health()
                elif source == 'fmp':
                    return self._check_fmp_health()
                elif source == 'alpha_vantage':
                    return self._check_alpha_vantage_health()
                elif source == 'polygon':
                    return self._check_polygon_health()
                elif source == 'finnhub':
                    return self._check_finnhub_health()
                else:
                    return True  # Default to healthy
            except Exception as e:
                logger.warning(f"Health check failed for {source}: {e}")
                return False

        return health_check

    def _check_yfinance_health(self) -> bool:
        """Lightweight health check for yfinance"""
        try:
            import yfinance as yf
            # Quick test with a well-known ticker
            ticker = yf.Ticker("AAPL")
            info = ticker.fast_info  # This is a lightweight call in yfinance
            return bool(info and hasattr(info, 'last_price'))
        except Exception:
            return False

    def _check_fmp_health(self) -> bool:
        """Lightweight health check for FMP API"""
        # Placeholder - would implement actual FMP health check
        return True

    def _check_alpha_vantage_health(self) -> bool:
        """Lightweight health check for Alpha Vantage API"""
        # Placeholder - would implement actual Alpha Vantage health check
        return True

    def _check_polygon_health(self) -> bool:
        """Lightweight health check for Polygon API"""
        # Placeholder - would implement actual Polygon health check
        return True

    def _check_finnhub_health(self) -> bool:
        """Lightweight health check for Finnhub API"""
        # Placeholder - would implement actual Finnhub health check
        return True

    @contextmanager
    def enhanced_error_handling(self, source: str, ticker: str = None, operation: str = "data_operation"):
        """
        Enhanced error handling context manager for data operations

        Args:
            source: Data source identifier
            ticker: Stock ticker symbol
            operation: Operation being performed
        """
        circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(source)

        if circuit_breaker:
            # Use circuit breaker protection
            with circuit_breaker.call_protection():
                with self.error_handler.error_handling_context(source, ticker, operation):
                    yield
        else:
            # Fallback to basic error handling
            with self.error_handler.error_handling_context(source, ticker, operation):
                yield

    def enhanced_fetch_market_data(self, ticker: str, force_reload: bool = False,
                                 skip_validation: bool = False) -> Optional[Dict[str, Any]]:
        """
        Enhanced market data fetching with comprehensive error handling

        Args:
            ticker: Stock ticker symbol
            force_reload: Force reload even if cached data exists
            skip_validation: Skip pre-flight validation

        Returns:
            Market data or None if failed
        """
        with self.enhanced_error_handling('yfinance', ticker, 'market_data_fetch'):
            # Call the original method with enhanced error handling
            return self.fetch_market_data(ticker, force_reload, skip_validation)

    def enhanced_load_excel_data(self, company_folder: str,
                               force_reload: bool = False) -> Dict[str, Any]:
        """
        Enhanced Excel data loading with error handling

        Args:
            company_folder: Company folder name
            force_reload: Force reload even if cached data exists

        Returns:
            Excel data dictionary
        """
        with self.enhanced_error_handling('excel_data', company_folder, 'excel_load'):
            # Call the original method with enhanced error handling
            return self.load_excel_data(company_folder, force_reload)

    def get_error_handling_status(self) -> Dict[str, Any]:
        """
        Get comprehensive error handling status and metrics

        Returns:
            Dictionary containing error handling metrics and status
        """
        return {
            'timestamp': time.time(),
            'error_handler_metrics': self.error_handler.get_error_summary(),
            'circuit_breaker_status': self.circuit_breaker_manager.get_health_summary(),
            'individual_circuit_breakers': self.circuit_breaker_manager.get_all_states()
        }

    def reset_error_handling_state(self, source: str = None):
        """
        Reset error handling state for debugging or recovery

        Args:
            source: Specific source to reset, or None for all sources
        """
        if source:
            circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(source)
            if circuit_breaker:
                circuit_breaker.reset()
                logger.info(f"Reset error handling state for {source}")
        else:
            self.circuit_breaker_manager.reset_all()
            self.error_handler.reset_metrics()
            logger.info("Reset all error handling state")

    def force_circuit_breaker_state(self, source: str, state: str, reason: str = "manual"):
        """
        Force circuit breaker to specific state for testing/debugging

        Args:
            source: Data source name
            state: 'open' or 'closed'
            reason: Reason for forcing state change
        """
        circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(source)
        if circuit_breaker:
            if state.lower() == 'open':
                circuit_breaker.force_open(reason)
            elif state.lower() == 'closed':
                circuit_breaker.force_close(reason)
            logger.info(f"Forced circuit breaker {source} to {state}: {reason}")

    def get_fallback_recommendations(self) -> Dict[str, List[str]]:
        """
        Get fallback source recommendations based on current health status

        Returns:
            Dictionary mapping failed sources to recommended fallbacks
        """
        recommendations = {}
        circuit_states = self.circuit_breaker_manager.get_all_states()

        for source, state_info in circuit_states.items():
            if state_info['state'] == 'open' or state_info['failure_rate'] > 0.5:
                # Get fallback recommendations from hierarchy manager if available
                if hasattr(self, 'hierarchy_manager') and self.hierarchy_manager:
                    fallback = self.error_handler.select_fallback_source(source)
                    if fallback:
                        recommendations[source] = [fallback]
                    else:
                        # Generic fallback recommendations
                        if source == 'yfinance':
                            recommendations[source] = ['fmp', 'alpha_vantage', 'polygon']
                        elif source == 'fmp':
                            recommendations[source] = ['yfinance', 'alpha_vantage', 'polygon']
                        elif source == 'alpha_vantage':
                            recommendations[source] = ['yfinance', 'fmp', 'polygon']
                        elif source == 'polygon':
                            recommendations[source] = ['yfinance', 'fmp', 'alpha_vantage']

        return recommendations

    def monitor_error_trends(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Monitor error trends over a time window for proactive management

        Args:
            time_window_minutes: Time window for trend analysis

        Returns:
            Dictionary containing trend analysis and alerts
        """
        analysis = {
            'time_window_minutes': time_window_minutes,
            'trends': {},
            'alerts': [],
            'recommendations': []
        }

        # Get current circuit breaker states
        all_states = self.circuit_breaker_manager.get_all_states()

        for source, state_info in all_states.items():
            trends = {
                'current_state': state_info['state'],
                'failure_rate': state_info['failure_rate'],
                'consecutive_failures': state_info['consecutive_failures'],
                'trend_direction': 'stable'  # Would calculate based on historical data
            }

            # Generate alerts based on trends
            if state_info['failure_rate'] > 0.3:
                analysis['alerts'].append(f"High failure rate for {source}: {state_info['failure_rate']:.1%}")

            if state_info['consecutive_failures'] > 3:
                analysis['alerts'].append(f"Multiple consecutive failures for {source}: {state_info['consecutive_failures']}")

            if state_info['state'] == 'open':
                analysis['alerts'].append(f"Circuit breaker OPEN for {source}")
                analysis['recommendations'].append(f"Check {source} service health and consider using fallback sources")

            analysis['trends'][source] = trends

        return analysis


def enhance_centralized_data_manager(manager_class):
    """
    Decorator to enhance CentralizedDataManager class with error handling capabilities

    Args:
        manager_class: The CentralizedDataManager class to enhance

    Returns:
        Enhanced class with error handling capabilities
    """
    class EnhancedCentralizedDataManager(ErrorHandlingMixin, manager_class):
        """Enhanced CentralizedDataManager with advanced error handling"""

        def __init__(self, *args, **kwargs):
            """Initialize with enhanced error handling"""
            super().__init__(*args, **kwargs)
            logger.info("CentralizedDataManager enhanced with advanced error handling")

    return EnhancedCentralizedDataManager


# Monkey patch methods to add error handling to existing methods
def patch_existing_methods(manager_instance):
    """
    Monkey patch existing CentralizedDataManager instance with enhanced error handling

    Args:
        manager_instance: Instance of CentralizedDataManager to patch
    """
    # Store original methods
    original_fetch_market_data = manager_instance.fetch_market_data
    original_load_excel_data = manager_instance.load_excel_data

    # Initialize error handling if not already present
    if not hasattr(manager_instance, 'error_handler'):
        ErrorHandlingMixin._init_error_handling(manager_instance)

    def patched_fetch_market_data(ticker: str, force_reload: bool = False,
                                skip_validation: bool = False) -> Optional[Dict[str, Any]]:
        """Patched version with error handling"""
        try:
            with manager_instance.enhanced_error_handling('yfinance', ticker, 'market_data_fetch'):
                return original_fetch_market_data(ticker, force_reload, skip_validation)
        except AttributeError:
            # Fallback if enhanced_error_handling not available
            return original_fetch_market_data(ticker, force_reload, skip_validation)

    def patched_load_excel_data(company_folder: str, force_reload: bool = False) -> Dict[str, Any]:
        """Patched version with error handling"""
        try:
            with manager_instance.enhanced_error_handling('excel_data', company_folder, 'excel_load'):
                return original_load_excel_data(company_folder, force_reload)
        except AttributeError:
            # Fallback if enhanced_error_handling not available
            return original_load_excel_data(company_folder, force_reload)

    # Apply patches
    manager_instance.fetch_market_data = patched_fetch_market_data
    manager_instance.load_excel_data = patched_load_excel_data

    # Add error handling methods
    manager_instance.enhanced_error_handling = ErrorHandlingMixin.enhanced_error_handling.__get__(manager_instance)
    manager_instance.get_error_handling_status = ErrorHandlingMixin.get_error_handling_status.__get__(manager_instance)
    manager_instance.reset_error_handling_state = ErrorHandlingMixin.reset_error_handling_state.__get__(manager_instance)
    manager_instance.force_circuit_breaker_state = ErrorHandlingMixin.force_circuit_breaker_state.__get__(manager_instance)
    manager_instance.get_fallback_recommendations = ErrorHandlingMixin.get_fallback_recommendations.__get__(manager_instance)
    manager_instance.monitor_error_trends = ErrorHandlingMixin.monitor_error_trends.__get__(manager_instance)

    logger.info("Successfully patched CentralizedDataManager with enhanced error handling")


# Example usage functions
def create_enhanced_data_manager(*args, **kwargs):
    """
    Factory function to create CentralizedDataManager with enhanced error handling

    Returns:
        Enhanced CentralizedDataManager instance
    """
    # Import here to avoid circular imports
    from .centralized_data_manager import CentralizedDataManager

    # Create enhanced class
    EnhancedClass = enhance_centralized_data_manager(CentralizedDataManager)

    return EnhancedClass(*args, **kwargs)


def add_error_handling_to_existing_manager(manager_instance):
    """
    Add error handling to existing CentralizedDataManager instance

    Args:
        manager_instance: Existing CentralizedDataManager instance

    Returns:
        The same instance with added error handling capabilities
    """
    patch_existing_methods(manager_instance)
    return manager_instance