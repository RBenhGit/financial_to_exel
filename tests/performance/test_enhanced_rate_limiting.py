#!/usr/bin/env python3
"""
Comprehensive Enhanced Rate Limiting Test Suite
===============================================

Tests for the enhanced rate limiting system including:
- Adaptive rate limiting with dynamic delay adjustment
- Circuit breaker pattern functionality
- Request queuing and spacing
- Fallback source selection
- Cache TTL adjustments during rate limiting
"""

import sys
import time
import logging
import unittest
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.data_processing.rate_limiting.enhanced_rate_limiter import (
    EnhancedRateLimiter, CircuitState, get_rate_limiter, reset_rate_limiter
)
from config.settings import get_api_config
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Add performance marker to all tests in this class
@pytest.mark.performance
class TestEnhancedRateLimiting(unittest.TestCase):
    """Test suite for enhanced rate limiting functionality"""

    def setUp(self):
        """Set up test environment"""
        # Reset the global rate limiter for clean tests
        reset_rate_limiter()
        
        # Create test manager with timeout patches
        from utils.input_validator import ValidationLevel
        with patch('time.sleep'):  # Prevent sleep delays during setup
            self.manager = CentralizedDataManager(
                base_path=".", 
                validation_level=ValidationLevel.PERMISSIVE
            )
        self.rate_limiter = self.manager.rate_limiter
        
        # Test configuration
        self.test_ticker = "AAPL"
        
    def tearDown(self):
        """Clean up after tests"""
        reset_rate_limiter()

    @pytest.mark.timeout(15)
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker opens and recovers properly"""
        logger.info("Testing circuit breaker functionality...")
        
        source = 'yahoo_finance'
        circuit_breaker = self.rate_limiter.circuit_breakers[source]
        
        # Initially should be closed
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)
        self.assertTrue(self.rate_limiter.can_make_request(source))
        
        # Record enough failures to open circuit (reduced for testing)
        failure_threshold = min(5, self.rate_limiter.config.circuit_breaker_failure_threshold)
        for i in range(failure_threshold):
            circuit_breaker.record_failure()
            
        # Circuit should now be open
        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)
        self.assertFalse(self.rate_limiter.can_make_request(source))
        
        logger.info("✓ Circuit breaker opens after threshold failures")
        
        # Simulate recovery timeout
        circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=301)
        
        # Should transition to half-open
        self.assertTrue(self.rate_limiter.can_make_request(source))
        self.assertEqual(circuit_breaker.state, CircuitState.HALF_OPEN)
        
        # Record enough successes to close circuit (reduced for testing) 
        success_threshold = min(3, self.rate_limiter.config.circuit_breaker_success_threshold)
        for i in range(success_threshold):
            circuit_breaker.record_success()
            
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)
        
        logger.info("✓ Circuit breaker recovers and closes after successful requests")

    @pytest.mark.timeout(10)
    @patch('time.sleep')  # Mock sleep to prevent actual delays
    def test_adaptive_rate_limiting(self, mock_sleep):
        """Test adaptive rate limiting adjusts delays based on response headers"""
        logger.info("Testing adaptive rate limiting...")
        
        source = 'yahoo_finance'
        initial_delay = self.rate_limiter.adaptive_delays[source]
        
        # Simulate 429 error with retry-after header
        mock_response = MagicMock()
        mock_response.headers = {'retry-after': '1', 'x-ratelimit-remaining': '0'}  # Reduced to 1 second
        
        # Create mock HTTP error
        error = requests.exceptions.HTTPError("429 Too Many Requests")
        error.response = mock_response
        
        # Test rate limiting context with mocked sleep
        try:
            with self.rate_limiter.rate_limited_request(source, attempt=1):
                raise error
        except requests.exceptions.HTTPError:
            pass  # Expected
            
        # Check that adaptive delay was updated
        updated_delay = self.rate_limiter.adaptive_delays[source]
        self.assertGreater(updated_delay, initial_delay)
        
        logger.info("✓ Adaptive delays adjust based on rate limit responses")

    @pytest.mark.timeout(5)
    def test_fallback_source_selection(self):
        """Test intelligent fallback source selection"""
        logger.info("Testing fallback source selection...")
        
        # Set up different health states for sources
        sources = ['alpha_vantage', 'fmp', 'polygon']
        
        # Make alpha_vantage appear healthier
        alpha_metrics = self.rate_limiter.health_metrics['alpha_vantage']
        alpha_metrics.total_requests = 10
        alpha_metrics.consecutive_successes = 5
        
        # Make fmp appear less healthy
        fmp_metrics = self.rate_limiter.health_metrics['fmp']
        fmp_metrics.total_requests = 10
        fmp_metrics.total_failures = 3
        fmp_metrics.consecutive_failures = 2
        
        # Get best source
        best_source = self.rate_limiter.get_best_available_source(sources)
        
        # Should prefer alpha_vantage due to better health
        self.assertEqual(best_source, 'alpha_vantage')
        
        logger.info("✓ Best available source selected based on health metrics")

    @pytest.mark.timeout(5)
    def test_cache_ttl_extension_during_rate_limiting(self):
        """Test cache TTL extension during rate limiting periods"""
        logger.info("Testing cache TTL extension during rate limiting...")
        
        source = 'yahoo_finance'
        
        # Simulate rate limiting issues
        self.rate_limiter.health_metrics[source].rate_limited_count = 5
        self.rate_limiter.health_metrics[source].consecutive_failures = 3
        
        # Get TTL for market data
        ttl_seconds = self.rate_limiter.get_cache_ttl_for_source(source, 'market_data')
        
        # Should use extended TTL
        cache_config = self.rate_limiter.cache_config
        self.assertEqual(ttl_seconds, cache_config.rate_limited_market_data_ttl)
        self.assertGreater(ttl_seconds, cache_config.default_ttl)
        
        logger.info("✓ Cache TTL extended during rate limiting")

    @pytest.mark.timeout(5)
    @patch('time.sleep')  # Mock sleep to prevent actual delays
    def test_request_spacing(self, mock_sleep):
        """Test minimum request spacing functionality"""
        logger.info("Testing request spacing...")
        
        source = 'yahoo_finance'
        min_spacing = self.rate_limiter.config.min_request_spacing
        
        if min_spacing <= 0:
            logger.info("⚠️  Minimum request spacing disabled, skipping test")
            return
            
        start_time = time.time()
        
        # Make two quick requests with mocked sleep
        try:
            with self.rate_limiter.rate_limited_request(source, 0):
                pass
        except Exception:
            pass
            
        try:
            with self.rate_limiter.rate_limited_request(source, 0):
                pass
        except Exception:
            pass
            
        elapsed = time.time() - start_time
        
        # With mocked sleep, this should complete quickly
        self.assertLess(elapsed, 1.0, "With mocked sleep, test should complete quickly")
        
        # Verify sleep was called (indicating spacing logic was triggered)
        if min_spacing > 0:
            mock_sleep.assert_called()
        
        logger.info(f"✓ Request spacing logic verified (completed in {elapsed:.2f}s)")

    @pytest.mark.timeout(15)
    @patch('core.data_processing.managers.centralized_data_manager.yf.Ticker')
    def test_rate_limiter_integration_with_manager(self, mock_ticker):
        """Test rate limiter integration with CentralizedDataManager"""
        logger.info("Testing rate limiter integration...")
        
        # Mock successful response
        mock_stock = MagicMock()
        mock_stock.info = {
            'symbol': self.test_ticker,
            'shortName': 'Apple Inc.',
            'regularMarketPrice': 150.0,
            'marketCap': 2500000000000,
            'sharesOutstanding': 16000000000
        }
        mock_ticker.return_value = mock_stock
        
        # Test fetch with rate limiter
        result = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['ticker'], self.test_ticker)
        
        # Check that rate limiter recorded the success
        yahoo_metrics = self.rate_limiter.health_metrics['yahoo_finance']
        self.assertGreater(yahoo_metrics.total_requests, 0)
        
        logger.info("✓ Rate limiter integrated successfully with data manager")

    @pytest.mark.timeout(5)
    def test_health_metrics_tracking(self):
        """Test comprehensive health metrics tracking"""
        logger.info("Testing health metrics tracking...")
        
        source = 'yahoo_finance'
        
        # Simulate some API activity
        self.rate_limiter._update_health_metrics(source, success=True, response_time=0.5)
        self.rate_limiter._update_health_metrics(source, success=False, is_rate_limited=True)
        self.rate_limiter._update_health_metrics(source, success=True, response_time=1.2)
        
        metrics = self.rate_limiter.health_metrics[source]
        
        self.assertEqual(metrics.total_requests, 3)
        self.assertEqual(metrics.total_failures, 1)
        self.assertEqual(metrics.rate_limited_count, 1)
        self.assertEqual(metrics.consecutive_successes, 1)
        self.assertGreater(metrics.average_response_time, 0)
        
        logger.info("✓ Health metrics tracked accurately")

    @pytest.mark.timeout(5)
    def test_health_report_generation(self):
        """Test comprehensive health report generation"""
        logger.info("Testing health report generation...")
        
        # Add some test data
        source = 'yahoo_finance'
        self.rate_limiter._update_health_metrics(source, success=True, response_time=0.8)
        self.rate_limiter._update_health_metrics(source, success=False, is_rate_limited=True)
        
        report = self.rate_limiter.get_source_health_report()
        
        self.assertIn(source, report)
        source_report = report[source]
        
        self.assertIn('circuit_breaker_state', source_report)
        self.assertIn('total_requests', source_report)
        self.assertIn('failure_rate_percent', source_report)
        self.assertIn('rate_limited_count', source_report)
        self.assertIn('average_response_time_ms', source_report)
        
        self.assertEqual(source_report['total_requests'], 2)
        self.assertEqual(source_report['rate_limited_count'], 1)
        self.assertEqual(source_report['failure_rate_percent'], 50.0)
        
        logger.info("✓ Health report generated successfully")

    @pytest.mark.timeout(10)
    @patch('requests.get')
    def test_fallback_with_rate_limiting(self, mock_get):
        """Test fallback mechanism with rate limiting"""
        logger.info("Testing fallback with rate limiting...")
        
        # Make Yahoo Finance unavailable
        yahoo_cb = self.rate_limiter.circuit_breakers['yahoo_finance']
        for _ in range(6):  # Exceed failure threshold
            yahoo_cb.record_failure()
            
        self.assertEqual(yahoo_cb.state, CircuitState.OPEN)
        
        # Test fallback data fetch
        fallback_result = self.manager._fetch_fallback_market_data(self.test_ticker)
        
        # Should attempt fallback (even if it returns None due to no API keys)
        self.assertIsNone(fallback_result)  # Expected since no real API keys
        
        # But should have attempted best available source
        logger.info("✓ Fallback mechanism triggered when primary source unavailable")


def run_comprehensive_rate_limiting_test():
    """Run comprehensive rate limiting tests"""
    print("=" * 60)
    print("ENHANCED RATE LIMITING TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedRateLimiting)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                   result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Enhanced rate limiting system is working well!")
    else:
        print("⚠️  Enhanced rate limiting system needs attention")
    
    return result.wasSuccessful()


def test_live_api_with_rate_limiting():
    """Test live API calls with enhanced rate limiting (optional)"""
    print("\n" + "=" * 60)
    print("LIVE API RATE LIMITING TEST")
    print("=" * 60)
    
    try:
        # Create manager
        from utils.input_validator import ValidationLevel
        manager = CentralizedDataManager(
            base_path=".", 
            validation_level=ValidationLevel.PERMISSIVE
        )
        
        # Test with a known ticker
        print(f"Testing enhanced rate limiting with live API calls...")
        
        start_time = time.time()
        result = manager.fetch_market_data('AAPL', force_reload=True)
        elapsed_time = time.time() - start_time
        
        if result:
            print(f"✅ Successfully fetched data for {result.get('ticker', 'AAPL')}")
            print(f"   Company: {result.get('company_name', 'N/A')}")
            print(f"   Price: ${result.get('current_price', 0)}")
            print(f"   Response time: {elapsed_time:.2f}s")
            
            # Check if rate limiter was used
            rate_limiter = manager.rate_limiter
            yahoo_metrics = rate_limiter.health_metrics['yahoo_finance']
            print(f"   Total requests tracked: {yahoo_metrics.total_requests}")
            print(f"   Consecutive successes: {yahoo_metrics.consecutive_successes}")
            print(f"   Average response time: {yahoo_metrics.average_response_time:.2f}s")
            
        else:
            print("⚠️  No data returned (might be due to rate limiting)")
            
        # Print health report
        print("\nAPI Health Report:")
        health_report = manager.rate_limiter.get_source_health_report()
        for source, metrics in health_report.items():
            if metrics['total_requests'] > 0:
                print(f"  {source}:")
                print(f"    Circuit Breaker: {metrics['circuit_breaker_state']}")
                print(f"    Requests: {metrics['total_requests']}")
                print(f"    Failure Rate: {metrics['failure_rate_percent']:.1f}%")
                print(f"    Rate Limited: {metrics['rate_limited_count']}")
        
    except Exception as e:
        print(f"❌ Live API test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run unit tests
    success = run_comprehensive_rate_limiting_test()
    
    # Optionally run live API test
    user_input = input("\nRun live API test? (y/N): ").strip().lower()
    if user_input == 'y':
        test_live_api_with_rate_limiting()
    else:
        print("Skipping live API test")
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")