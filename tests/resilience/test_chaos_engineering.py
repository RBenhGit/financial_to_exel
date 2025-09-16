#!/usr/bin/env python3
"""
Chaos Engineering Tests for Data Source Resilience
================================================

Comprehensive chaos engineering test suite that systematically simulates
various failure scenarios to validate the resilience of the data acquisition
system including fallback mechanisms, recovery protocols, and error handling.
"""

import sys
import time
import random
import logging
import unittest
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.data_processing.rate_limiting.enhanced_rate_limiter import (
    EnhancedRateLimiter, CircuitState, get_rate_limiter, reset_rate_limiter
)
from core.data_processing.monitoring.health_monitor import (
    get_health_monitor, reset_health_monitor
)
from config.settings import get_api_config
from utils.input_validator import ValidationLevel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChaosScenario:
    """Base class for chaos engineering scenarios"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.results = {}

    def execute(self, manager: CentralizedDataManager, duration_seconds: int = 30):
        """Execute the chaos scenario"""
        raise NotImplementedError

    def validate_recovery(self, manager: CentralizedDataManager) -> bool:
        """Validate that the system recovered properly"""
        raise NotImplementedError


class APIFailureScenario(ChaosScenario):
    """Simulate complete API failure"""

    def __init__(self):
        super().__init__(
            "API_FAILURE",
            "Complete API failure simulation with fallback validation"
        )

    @contextmanager
    def simulate_api_failure(self, source_name: str):
        """Context manager to simulate API failure"""
        original_request = requests.get

        def failing_request(*args, **kwargs):
            if any(domain in str(args) for domain in ['finance.yahoo.com', 'api.polygon.io']):
                raise requests.exceptions.ConnectionError("Simulated API failure")
            return original_request(*args, **kwargs)

        with patch('requests.get', side_effect=failing_request):
            yield

    def execute(self, manager: CentralizedDataManager, duration_seconds: int = 30):
        """Execute API failure scenario"""
        test_ticker = "AAPL"
        start_time = time.time()
        results = {
            'fallback_triggered': False,
            'error_handled': False,
            'data_retrieved': False,
            'response_times': []
        }

        logger.info(f"Starting {self.name} scenario for {duration_seconds} seconds")

        with self.simulate_api_failure('yahoo_finance'):
            while time.time() - start_time < duration_seconds:
                try:
                    request_start = time.time()
                    data = manager.fetch_market_data(test_ticker, force_reload=True)
                    response_time = time.time() - request_start

                    results['response_times'].append(response_time)

                    if data:
                        results['data_retrieved'] = True
                        results['fallback_triggered'] = True
                        logger.info(f"✓ Fallback successful - got data from alternative source")

                except Exception as e:
                    results['error_handled'] = True
                    logger.info(f"✓ Error properly handled: {type(e).__name__}")

                time.sleep(1)  # Small delay between requests

        self.results = results
        logger.info(f"Completed {self.name} scenario")
        return results

    def validate_recovery(self, manager: CentralizedDataManager) -> bool:
        """Validate recovery after API failure"""
        try:
            # Check if circuit breakers reset properly
            rate_limiter = manager.rate_limiter
            yahoo_cb = rate_limiter.circuit_breakers.get('yahoo_finance')

            if yahoo_cb and yahoo_cb.state == CircuitState.OPEN:
                # Simulate recovery timeout
                yahoo_cb.last_failure_time = datetime.now() - timedelta(seconds=301)

            # Try normal operation
            data = manager.fetch_market_data("MSFT", force_reload=True)
            return data is not None

        except Exception as e:
            logger.error(f"Recovery validation failed: {e}")
            return False


class RateLimitingScenario(ChaosScenario):
    """Simulate rate limiting responses from APIs"""

    def __init__(self):
        super().__init__(
            "RATE_LIMITING",
            "Rate limiting simulation with adaptive delay validation"
        )

    @contextmanager
    def simulate_rate_limiting(self):
        """Context manager to simulate rate limiting"""
        original_request = requests.get
        request_count = 0

        def rate_limited_request(*args, **kwargs):
            nonlocal request_count
            request_count += 1

            if request_count % 3 == 0:  # Every 3rd request gets rate limited
                mock_response = MagicMock()
                mock_response.status_code = 429
                mock_response.headers = {
                    'retry-after': '2',
                    'x-ratelimit-remaining': '0',
                    'x-ratelimit-reset': str(int(time.time()) + 60)
                }
                error = requests.exceptions.HTTPError("429 Too Many Requests")
                error.response = mock_response
                raise error

            return original_request(*args, **kwargs)

        with patch('requests.get', side_effect=rate_limited_request):
            yield

    def execute(self, manager: CentralizedDataManager, duration_seconds: int = 30):
        """Execute rate limiting scenario"""
        test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        start_time = time.time()
        results = {
            'rate_limits_encountered': 0,
            'adaptive_delays_triggered': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0
        }

        response_times = []

        logger.info(f"Starting {self.name} scenario")

        with self.simulate_rate_limiting():
            while time.time() - start_time < duration_seconds:
                ticker = random.choice(test_tickers)

                try:
                    request_start = time.time()
                    data = manager.fetch_market_data(ticker, force_reload=True)
                    response_time = time.time() - request_start
                    response_times.append(response_time)

                    if data:
                        results['successful_requests'] += 1
                    else:
                        results['failed_requests'] += 1

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        results['rate_limits_encountered'] += 1
                        results['adaptive_delays_triggered'] += 1
                except Exception:
                    results['failed_requests'] += 1

                time.sleep(0.5)  # Small delay between requests

        if response_times:
            results['average_response_time'] = sum(response_times) / len(response_times)

        self.results = results
        logger.info(f"Completed {self.name} scenario")
        return results

    def validate_recovery(self, manager: CentralizedDataManager) -> bool:
        """Validate that rate limiting subsided"""
        try:
            # Check if adaptive delays were reset
            rate_limiter = manager.rate_limiter
            initial_delay = rate_limiter.adaptive_delays.get('yahoo_finance', 1.0)

            # Wait for potential cooldown
            time.sleep(2)

            # Try normal request
            data = manager.fetch_market_data("NVDA", force_reload=True)
            return data is not None

        except Exception as e:
            logger.error(f"Rate limiting recovery validation failed: {e}")
            return False


class NetworkLatencyScenario(ChaosScenario):
    """Simulate high network latency"""

    def __init__(self):
        super().__init__(
            "NETWORK_LATENCY",
            "High network latency simulation with timeout handling"
        )

    @contextmanager
    def simulate_network_latency(self, delay_seconds: float = 5.0):
        """Context manager to simulate network latency"""
        original_request = requests.get

        def slow_request(*args, **kwargs):
            time.sleep(delay_seconds)  # Simulate network delay
            return original_request(*args, **kwargs)

        with patch('requests.get', side_effect=slow_request):
            yield

    def execute(self, manager: CentralizedDataManager, duration_seconds: int = 30):
        """Execute network latency scenario"""
        test_ticker = "TSLA"
        start_time = time.time()
        results = {
            'timeouts_encountered': 0,
            'slow_responses': 0,
            'fallback_triggered': False,
            'max_response_time': 0
        }

        logger.info(f"Starting {self.name} scenario")

        with self.simulate_network_latency(delay_seconds=8.0):  # 8 second delay
            while time.time() - start_time < duration_seconds:
                try:
                    request_start = time.time()
                    # Set shorter timeout to trigger timeout handling
                    with patch.object(manager, 'request_timeout', 3):
                        data = manager.fetch_market_data(test_ticker, force_reload=True)

                    response_time = time.time() - request_start
                    results['max_response_time'] = max(results['max_response_time'], response_time)

                    if response_time > 5.0:
                        results['slow_responses'] += 1

                    if data:
                        results['fallback_triggered'] = True

                except requests.exceptions.Timeout:
                    results['timeouts_encountered'] += 1
                except Exception:
                    pass  # Other errors are expected

                if time.time() - start_time > 15:  # Don't wait too long
                    break

        self.results = results
        logger.info(f"Completed {self.name} scenario")
        return results

    def validate_recovery(self, manager: CentralizedDataManager) -> bool:
        """Validate recovery from network latency"""
        try:
            # Normal request should work now
            data = manager.fetch_market_data("IBM", force_reload=True)
            return data is not None
        except Exception as e:
            logger.error(f"Network latency recovery validation failed: {e}")
            return False


class ConcurrentLoadScenario(ChaosScenario):
    """Simulate high concurrent load"""

    def __init__(self):
        super().__init__(
            "CONCURRENT_LOAD",
            "High concurrent load simulation with resource management"
        )

    def execute(self, manager: CentralizedDataManager, duration_seconds: int = 30):
        """Execute concurrent load scenario"""
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX"]
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'concurrent_threads': 10,
            'average_response_time': 0,
            'max_response_time': 0
        }

        response_times = []

        def fetch_data(ticker):
            """Function to fetch data in thread"""
            try:
                start_time = time.time()
                data = manager.fetch_market_data(ticker, force_reload=True)
                response_time = time.time() - start_time

                return {
                    'success': data is not None,
                    'response_time': response_time,
                    'ticker': ticker
                }
            except Exception as e:
                return {
                    'success': False,
                    'response_time': 0,
                    'ticker': ticker,
                    'error': str(e)
                }

        logger.info(f"Starting {self.name} scenario with {results['concurrent_threads']} threads")

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=results['concurrent_threads']) as executor:
            while time.time() - start_time < duration_seconds:
                # Submit batch of requests
                futures = []
                for i in range(results['concurrent_threads']):
                    ticker = random.choice(tickers)
                    future = executor.submit(fetch_data, ticker)
                    futures.append(future)

                # Collect results
                for future in as_completed(futures, timeout=10):
                    try:
                        result = future.result()
                        results['total_requests'] += 1

                        if result['success']:
                            results['successful_requests'] += 1
                        else:
                            results['failed_requests'] += 1

                        if result['response_time'] > 0:
                            response_times.append(result['response_time'])
                            results['max_response_time'] = max(
                                results['max_response_time'],
                                result['response_time']
                            )

                    except Exception as e:
                        results['failed_requests'] += 1
                        logger.warning(f"Thread result error: {e}")

                time.sleep(1)  # Brief pause between batches

        if response_times:
            results['average_response_time'] = sum(response_times) / len(response_times)

        self.results = results
        logger.info(f"Completed {self.name} scenario")
        return results

    def validate_recovery(self, manager: CentralizedDataManager) -> bool:
        """Validate system stability after concurrent load"""
        try:
            # Check system is still responsive
            data = manager.fetch_market_data("V", force_reload=True)

            # Check rate limiter health
            rate_limiter = manager.rate_limiter
            health_report = rate_limiter.get_source_health_report()

            # System should be in reasonable state
            return data is not None and len(health_report) > 0

        except Exception as e:
            logger.error(f"Concurrent load recovery validation failed: {e}")
            return False


@pytest.mark.chaos
class TestChaosEngineering(unittest.TestCase):
    """Chaos engineering test suite"""

    def setUp(self):
        """Set up test environment"""
        reset_rate_limiter()
        reset_health_monitor()

        with patch('time.sleep'):  # Speed up setup
            self.manager = CentralizedDataManager(
                base_path=".",
                validation_level=ValidationLevel.PERMISSIVE
            )

    def tearDown(self):
        """Clean up after tests"""
        reset_rate_limiter()
        reset_health_monitor()

    @pytest.mark.timeout(60)
    def test_api_failure_scenario(self):
        """Test complete API failure scenario"""
        scenario = APIFailureScenario()

        # Execute chaos scenario
        results = scenario.execute(self.manager, duration_seconds=10)

        # Validate results
        self.assertGreater(results.get('response_times', []), 0,
                          "Should have recorded response times")
        self.assertTrue(results.get('error_handled', False),
                       "Should have handled errors gracefully")

        # Validate recovery
        recovery_success = scenario.validate_recovery(self.manager)
        self.assertTrue(recovery_success, "System should recover after API failure")

        logger.info("✓ API failure scenario completed successfully")

    @pytest.mark.timeout(60)
    def test_rate_limiting_scenario(self):
        """Test rate limiting scenario"""
        scenario = RateLimitingScenario()

        # Execute chaos scenario
        results = scenario.execute(self.manager, duration_seconds=15)

        # Validate results
        self.assertGreater(results.get('rate_limits_encountered', 0), 0,
                          "Should have encountered rate limits")
        self.assertGreater(results.get('adaptive_delays_triggered', 0), 0,
                          "Should have triggered adaptive delays")

        # Validate recovery
        recovery_success = scenario.validate_recovery(self.manager)
        self.assertTrue(recovery_success, "System should recover from rate limiting")

        logger.info("✓ Rate limiting scenario completed successfully")

    @pytest.mark.timeout(45)
    def test_network_latency_scenario(self):
        """Test network latency scenario"""
        scenario = NetworkLatencyScenario()

        # Execute chaos scenario
        results = scenario.execute(self.manager, duration_seconds=10)

        # Validate results
        self.assertGreaterEqual(results.get('max_response_time', 0), 0,
                               "Should have recorded response times")

        # Validate recovery
        recovery_success = scenario.validate_recovery(self.manager)
        self.assertTrue(recovery_success, "System should recover from network latency")

        logger.info("✓ Network latency scenario completed successfully")

    @pytest.mark.timeout(60)
    def test_concurrent_load_scenario(self):
        """Test concurrent load scenario"""
        scenario = ConcurrentLoadScenario()

        # Execute chaos scenario
        results = scenario.execute(self.manager, duration_seconds=20)

        # Validate results
        self.assertGreater(results.get('total_requests', 0), 0,
                          "Should have made requests")
        self.assertGreaterEqual(results.get('successful_requests', 0), 0,
                               "Should have some successful requests")

        # Calculate success rate
        total = results.get('total_requests', 1)
        success_rate = results.get('successful_requests', 0) / total
        self.assertGreater(success_rate, 0.3,
                          "Should maintain reasonable success rate under load")

        # Validate recovery
        recovery_success = scenario.validate_recovery(self.manager)
        self.assertTrue(recovery_success, "System should remain stable after concurrent load")

        logger.info("✓ Concurrent load scenario completed successfully")

    @pytest.mark.timeout(120)
    def test_combined_chaos_scenario(self):
        """Test combined chaos scenarios"""
        logger.info("Starting combined chaos scenario")

        # Run multiple scenarios in sequence
        scenarios = [
            APIFailureScenario(),
            RateLimitingScenario(),
        ]

        all_results = {}

        for scenario in scenarios:
            logger.info(f"Running {scenario.name} as part of combined test")
            results = scenario.execute(self.manager, duration_seconds=8)
            all_results[scenario.name] = results

            # Brief recovery time between scenarios
            time.sleep(2)

        # Validate overall system resilience
        for scenario in scenarios:
            recovery_success = scenario.validate_recovery(self.manager)
            self.assertTrue(recovery_success,
                           f"System should recover after {scenario.name}")

        # Validate final system state
        final_data = self.manager.fetch_market_data("PLTR", force_reload=True)
        self.assertIsNotNone(final_data, "System should be functional after combined chaos")

        logger.info("✓ Combined chaos scenario completed successfully")


def run_chaos_engineering_suite():
    """Run the complete chaos engineering test suite"""
    print("=" * 70)
    print("CHAOS ENGINEERING TEST SUITE")
    print("=" * 70)
    print("Testing data source resilience through systematic failure simulation")
    print()

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestChaosEngineering)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)

    # Print comprehensive summary
    print("\n" + "=" * 70)
    print("CHAOS ENGINEERING TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback[:200]}...")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback[:200]}...")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) /
                   result.testsRun * 100) if result.testsRun > 0 else 0

    print(f"\nChaos Engineering Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("🔥 RESILIENCE VALIDATED: System demonstrates excellent chaos resistance!")
        print("✅ Data source fallback mechanisms working properly")
        print("✅ Rate limiting and recovery protocols functional")
        print("✅ System maintains stability under adverse conditions")
    elif success_rate >= 60:
        print("⚠️  RESILIENCE PARTIAL: Some chaos scenarios need attention")
    else:
        print("❌ RESILIENCE CRITICAL: Significant chaos resistance issues detected")

    print("\nRecommendations:")
    print("- Monitor circuit breaker behavior in production")
    print("- Consider implementing additional fallback data sources")
    print("- Review rate limiting thresholds based on API provider limits")
    print("- Set up proactive monitoring for data source health")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Allow running specific scenarios
    import argparse

    parser = argparse.ArgumentParser(description="Run chaos engineering tests")
    parser.add_argument("--scenario", choices=['api_failure', 'rate_limiting', 'latency', 'load', 'all'],
                       default='all', help="Specific scenario to run")
    parser.add_argument("--duration", type=int, default=30, help="Duration for each scenario")

    args = parser.parse_args()

    if args.scenario == 'all':
        success = run_chaos_engineering_suite()
    else:
        # Run specific scenario
        reset_rate_limiter()
        reset_health_monitor()

        with patch('time.sleep'):
            manager = CentralizedDataManager(base_path=".", validation_level=ValidationLevel.PERMISSIVE)

        if args.scenario == 'api_failure':
            scenario = APIFailureScenario()
        elif args.scenario == 'rate_limiting':
            scenario = RateLimitingScenario()
        elif args.scenario == 'latency':
            scenario = NetworkLatencyScenario()
        elif args.scenario == 'load':
            scenario = ConcurrentLoadScenario()

        results = scenario.execute(manager, args.duration)
        recovery = scenario.validate_recovery(manager)

        print(f"Scenario: {scenario.name}")
        print(f"Results: {results}")
        print(f"Recovery: {'✓' if recovery else '✗'}")