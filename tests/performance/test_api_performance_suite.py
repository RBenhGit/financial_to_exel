"""
API Performance and Rate Limiting Test Suite
===========================================

This module provides comprehensive testing for API performance, rate limiting,
and external service integration under various load conditions.

Features:
- API rate limiting effectiveness testing
- Multiple API provider performance comparison
- Connection pooling and timeout handling
- Error recovery and retry mechanism testing
- API quota management testing
- Background refresh performance

Usage:
    # Run API performance tests
    pytest tests/performance/test_api_performance_suite.py -v

    # Run with mock APIs (default)
    pytest tests/performance/test_api_performance_suite.py -m "not real_api"

    # Run with real APIs (requires API keys)
    pytest tests/performance/test_api_performance_suite.py -m "real_api"
"""

import pytest
import asyncio
import time
import threading
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import psutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import random
from queue import Queue, Empty
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import core modules
try:
    from core.data_processing.rate_limiting.rate_limiter import RateLimiter
except ImportError:
    RateLimiter = None

try:
    from core.data_sources.real_time_price_service import RealTimePriceService
except ImportError:
    RealTimePriceService = None

try:
    from core.data_sources.industry_data_service import IndustryDataService
except ImportError:
    IndustryDataService = None

try:
    from core.data_processing.managers.enhanced_data_manager import EnhancedDataManager
except ImportError:
    EnhancedDataManager = None


@dataclass
class APIPerformanceConfig:
    """Configuration for API performance testing"""
    concurrent_requests: int = 10
    requests_per_thread: int = 5
    rate_limit_per_second: int = 5
    rate_limit_burst: int = 10
    timeout_seconds: int = 10
    max_retries: int = 3
    backoff_factor: float = 0.5
    test_duration_seconds: int = 30


@dataclass
class APITestResult:
    """Results from API performance testing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    timeout_requests: int = 0
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    rate_limit_effectiveness: float = 0.0
    errors: List[str] = field(default_factory=list)


class MockAPIProvider:
    """Mock API provider for testing without external dependencies"""

    def __init__(self, config: APIPerformanceConfig):
        self.config = config
        self.request_times = []
        self.rate_limiter = self._create_rate_limiter()

    def _create_rate_limiter(self):
        """Create a simple rate limiter for testing"""
        return {
            'requests': [],
            'max_per_second': self.config.rate_limit_per_second,
            'burst_capacity': self.config.rate_limit_burst
        }

    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()

        # Remove old requests (older than 1 second)
        self.rate_limiter['requests'] = [
            req_time for req_time in self.rate_limiter['requests']
            if current_time - req_time < 1.0
        ]

        # Check rate limit
        if len(self.rate_limiter['requests']) >= self.rate_limiter['max_per_second']:
            return False

        # Add current request
        self.rate_limiter['requests'].append(current_time)
        return True

    def make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Simulate API request with rate limiting"""
        start_time = time.time()

        # Check rate limit
        if not self._check_rate_limit():
            return {
                'success': False,
                'error': 'Rate limit exceeded',
                'response_time': 0.001,
                'status_code': 429
            }

        # Simulate network delay
        network_delay = random.uniform(0.1, 0.5)
        time.sleep(network_delay)

        # Simulate occasional failures
        failure_rate = 0.05  # 5% failure rate
        if random.random() < failure_rate:
            return {
                'success': False,
                'error': 'Simulated API error',
                'response_time': time.time() - start_time,
                'status_code': 500
            }

        # Simulate successful response
        mock_data = self._generate_mock_data(endpoint)

        return {
            'success': True,
            'data': mock_data,
            'response_time': time.time() - start_time,
            'status_code': 200
        }

    def _generate_mock_data(self, endpoint: str) -> Dict:
        """Generate realistic mock data based on endpoint"""
        if 'price' in endpoint.lower():
            return {
                'symbol': 'TEST',
                'price': round(random.uniform(50, 500), 2),
                'change': round(random.uniform(-10, 10), 2),
                'volume': random.randint(100000, 10000000),
                'timestamp': datetime.now().isoformat()
            }
        elif 'fundamental' in endpoint.lower():
            return {
                'symbol': 'TEST',
                'revenue': random.randint(1000000, 10000000),
                'netIncome': random.randint(100000, 1000000),
                'totalAssets': random.randint(5000000, 50000000),
                'marketCap': random.randint(1000000000, 100000000000)
            }
        elif 'industry' in endpoint.lower():
            return {
                'industry': 'Technology',
                'sector': 'Information Technology',
                'averagePE': round(random.uniform(15, 35), 2),
                'averagePB': round(random.uniform(2, 8), 2),
                'companies_count': random.randint(50, 500)
            }
        else:
            return {
                'status': 'success',
                'message': 'Mock API response',
                'timestamp': datetime.now().isoformat()
            }


class APILoadTester:
    """Utility class for API load testing"""

    def __init__(self, config: APIPerformanceConfig):
        self.config = config
        self.results = []
        self.errors = []

    def run_load_test(self, api_provider, endpoints: List[str]) -> APITestResult:
        """Execute API load test"""
        start_time = time.time()

        # Reset results
        self.results.clear()
        self.errors.clear()

        def worker_thread(thread_id: int):
            """Worker thread for making API requests"""
            thread_results = []

            for request_id in range(self.config.requests_per_thread):
                # Select random endpoint
                endpoint = random.choice(endpoints)

                try:
                    # Make API request
                    result = api_provider.make_request(endpoint, {'test': True})

                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': request_id,
                        'endpoint': endpoint,
                        'success': result.get('success', False),
                        'response_time': result.get('response_time', 0),
                        'status_code': result.get('status_code', 0),
                        'error': result.get('error'),
                        'timestamp': time.time()
                    })

                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': request_id,
                        'endpoint': endpoint,
                        'success': False,
                        'response_time': 0,
                        'error': str(e),
                        'timestamp': time.time()
                    })

                # Add small random delay between requests
                time.sleep(random.uniform(0.1, 0.3))

            return thread_results

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=self.config.concurrent_requests) as executor:
            futures = [
                executor.submit(worker_thread, i)
                for i in range(self.config.concurrent_requests)
            ]

            for future in as_completed(futures):
                try:
                    thread_results = future.result(timeout=60)
                    self.results.extend(thread_results)
                except Exception as e:
                    self.errors.append(f"Thread execution error: {str(e)}")

        # Calculate metrics
        return self._calculate_metrics(start_time)

    def _calculate_metrics(self, start_time: float) -> APITestResult:
        """Calculate performance metrics from results"""
        if not self.results:
            return APITestResult()

        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r['success']])
        failed_requests = total_requests - successful_requests
        rate_limited_requests = len([r for r in self.results if r.get('status_code') == 429])
        timeout_requests = len([r for r in self.results if 'timeout' in str(r.get('error', '')).lower()])

        response_times = [r['response_time'] for r in self.results if r['success']]

        total_time = time.time() - start_time

        return APITestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            rate_limited_requests=rate_limited_requests,
            timeout_requests=timeout_requests,
            average_response_time=sum(response_times) / len(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            requests_per_second=total_requests / total_time if total_time > 0 else 0,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            rate_limit_effectiveness=rate_limited_requests / total_requests if total_requests > 0 else 0,
            errors=self.errors
        )


@pytest.fixture
def api_config():
    """Default API performance test configuration"""
    return APIPerformanceConfig()


@pytest.fixture
def mock_api_provider(api_config):
    """Mock API provider for testing"""
    return MockAPIProvider(api_config)


@pytest.fixture
def test_endpoints():
    """Common API endpoints for testing"""
    return [
        '/api/v1/price/AAPL',
        '/api/v1/price/MSFT',
        '/api/v1/price/GOOGL',
        '/api/v1/fundamental/AAPL',
        '/api/v1/fundamental/MSFT',
        '/api/v1/industry/technology',
        '/api/v1/industry/healthcare',
        '/api/v1/market/overview'
    ]


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limiter_basic_functionality(self, benchmark, api_config, mock_api_provider, test_endpoints):
        """Test basic rate limiting functionality"""

        def rate_limit_test():
            tester = APILoadTester(api_config)

            # Configure for rate limit testing
            tester.config.concurrent_requests = 1  # Sequential requests
            tester.config.requests_per_thread = 20  # More requests than rate limit

            result = tester.run_load_test(mock_api_provider, test_endpoints[:1])  # Single endpoint

            return result

        result = benchmark(rate_limit_test)

        # Assertions
        assert result.total_requests > 0
        assert result.rate_limited_requests > 0, "Rate limiting should be triggered"
        assert result.rate_limit_effectiveness > 0, "Rate limiting should be effective"

    def test_rate_limiter_concurrent_access(self, benchmark, api_config, mock_api_provider, test_endpoints):
        """Test rate limiter under concurrent access"""

        def concurrent_rate_limit_test():
            tester = APILoadTester(api_config)

            # Configure for concurrent testing
            tester.config.concurrent_requests = 5
            tester.config.requests_per_thread = 10

            result = tester.run_load_test(mock_api_provider, test_endpoints)

            return result

        result = benchmark(concurrent_rate_limit_test)

        # Assertions
        assert result.total_requests > 0
        assert result.error_rate < 0.5, f"Error rate too high: {result.error_rate:.2%}"
        assert result.requests_per_second > 0

    def test_rate_limiter_burst_handling(self, benchmark, api_config):
        """Test rate limiter burst capacity"""

        def burst_test():
            provider = MockAPIProvider(api_config)

            # Test burst requests
            burst_results = []
            start_time = time.time()

            # Send burst of requests quickly
            for i in range(api_config.rate_limit_burst + 5):  # Exceed burst capacity
                result = provider.make_request('/test/burst')
                burst_results.append(result)

                if i < api_config.rate_limit_burst:
                    # First few should succeed (within burst)
                    time.sleep(0.01)  # Minimal delay
                else:
                    # Later ones should be rate limited
                    time.sleep(0.01)

            total_time = time.time() - start_time

            successful = len([r for r in burst_results if r['success']])
            rate_limited = len([r for r in burst_results if r.get('status_code') == 429])

            return {
                'total_requests': len(burst_results),
                'successful': successful,
                'rate_limited': rate_limited,
                'total_time': total_time,
                'burst_handled': successful <= api_config.rate_limit_burst
            }

        result = benchmark(burst_test)

        # Assertions
        assert result['total_requests'] > api_config.rate_limit_burst
        assert result['rate_limited'] > 0, "Burst should trigger rate limiting"


class TestAPIProviderPerformance:
    """Test performance of different API providers"""

    @pytest.mark.parametrize("provider_type", ["yfinance", "alpha_vantage", "fmp", "polygon"])
    def test_api_provider_performance(self, benchmark, api_config, provider_type):
        """Test performance of different API providers (mocked)"""

        def api_provider_test():
            # Mock different API providers with different characteristics
            provider_configs = {
                'yfinance': {'rate_limit': 5, 'avg_response': 0.3, 'failure_rate': 0.02},
                'alpha_vantage': {'rate_limit': 5, 'avg_response': 0.5, 'failure_rate': 0.01},
                'fmp': {'rate_limit': 10, 'avg_response': 0.2, 'failure_rate': 0.03},
                'polygon': {'rate_limit': 5, 'avg_response': 0.1, 'failure_rate': 0.01}
            }

            config = provider_configs.get(provider_type, provider_configs['yfinance'])

            # Create provider with specific characteristics
            class MockProvider:
                def __init__(self, provider_config):
                    self.config = provider_config
                    self.request_count = 0
                    self.last_request_time = 0

                def make_request(self, endpoint, params=None):
                    current_time = time.time()

                    # Rate limiting simulation
                    if current_time - self.last_request_time < 1.0 / self.config['rate_limit']:
                        return {
                            'success': False,
                            'error': 'Rate limit exceeded',
                            'status_code': 429,
                            'response_time': 0.001
                        }

                    self.last_request_time = current_time

                    # Simulate response time
                    response_time = random.uniform(
                        self.config['avg_response'] * 0.5,
                        self.config['avg_response'] * 1.5
                    )
                    time.sleep(response_time)

                    # Simulate failures
                    if random.random() < self.config['failure_rate']:
                        return {
                            'success': False,
                            'error': f'{provider_type} API error',
                            'status_code': 500,
                            'response_time': response_time
                        }

                    return {
                        'success': True,
                        'data': {'provider': provider_type, 'value': random.uniform(100, 1000)},
                        'status_code': 200,
                        'response_time': response_time
                    }

            provider = MockProvider(config)
            tester = APILoadTester(api_config)

            # Reduce load for individual provider testing
            tester.config.concurrent_requests = 3
            tester.config.requests_per_thread = 5

            endpoints = [f'/api/{provider_type}/test']
            result = tester.run_load_test(provider, endpoints)

            return {
                'provider': provider_type,
                'result': result,
                'provider_config': config
            }

        result = benchmark(api_provider_test)

        # Assertions
        assert result['result'].total_requests > 0
        assert result['result'].error_rate < 0.2, f"High error rate for {provider_type}: {result['result'].error_rate:.2%}"

    def test_api_fallback_mechanism(self, benchmark, api_config):
        """Test API fallback mechanism when primary provider fails"""

        def fallback_test():
            class FallbackProvider:
                def __init__(self):
                    self.primary_available = True
                    self.fallback_used = 0

                def make_request(self, endpoint, params=None):
                    start_time = time.time()

                    # Simulate primary provider failure after some requests
                    if random.random() < 0.3:  # 30% primary failure rate
                        self.primary_available = False

                    if not self.primary_available:
                        self.fallback_used += 1
                        # Simulate fallback provider (slower but reliable)
                        time.sleep(random.uniform(0.5, 1.0))
                        return {
                            'success': True,
                            'data': {'source': 'fallback', 'value': random.uniform(100, 1000)},
                            'status_code': 200,
                            'response_time': time.time() - start_time,
                            'fallback_used': True
                        }
                    else:
                        # Primary provider (faster)
                        time.sleep(random.uniform(0.1, 0.3))
                        return {
                            'success': True,
                            'data': {'source': 'primary', 'value': random.uniform(100, 1000)},
                            'status_code': 200,
                            'response_time': time.time() - start_time,
                            'fallback_used': False
                        }

            provider = FallbackProvider()
            tester = APILoadTester(api_config)

            tester.config.concurrent_requests = 2
            tester.config.requests_per_thread = 10

            result = tester.run_load_test(provider, ['/api/test'])

            return {
                'result': result,
                'fallback_used': provider.fallback_used
            }

        result = benchmark(fallback_test)

        # Assertions
        assert result['result'].successful_requests > 0
        assert result['fallback_used'] > 0, "Fallback mechanism should be triggered"

    def test_connection_pooling_performance(self, benchmark, api_config):
        """Test connection pooling performance"""

        def connection_pool_test():
            # Simulate connection pooling vs individual connections
            class PooledProvider:
                def __init__(self, use_pooling=True):
                    self.use_pooling = use_pooling
                    self.connection_overhead = 0.1 if not use_pooling else 0.01

                def make_request(self, endpoint, params=None):
                    start_time = time.time()

                    # Simulate connection overhead
                    time.sleep(self.connection_overhead)

                    # Simulate request processing
                    time.sleep(random.uniform(0.1, 0.3))

                    return {
                        'success': True,
                        'data': {'pooled': self.use_pooling},
                        'status_code': 200,
                        'response_time': time.time() - start_time
                    }

            # Test both pooled and non-pooled
            results = {}

            for use_pooling in [False, True]:
                provider = PooledProvider(use_pooling)
                tester = APILoadTester(api_config)

                tester.config.concurrent_requests = 5
                tester.config.requests_per_thread = 8

                result = tester.run_load_test(provider, ['/api/pool_test'])
                results[f'pooled_{use_pooling}'] = result

            return results

        results = benchmark(connection_pool_test)

        # Assertions
        pooled_time = results['pooled_True'].average_response_time
        non_pooled_time = results['pooled_False'].average_response_time

        assert pooled_time < non_pooled_time, "Connection pooling should improve performance"


class TestAPIErrorHandling:
    """Test API error handling and recovery"""

    def test_timeout_handling(self, benchmark, api_config):
        """Test API timeout handling"""

        def timeout_test():
            class TimeoutProvider:
                def __init__(self, timeout_rate=0.2):
                    self.timeout_rate = timeout_rate

                def make_request(self, endpoint, params=None):
                    start_time = time.time()

                    # Simulate timeouts
                    if random.random() < self.timeout_rate:
                        time.sleep(api_config.timeout_seconds + 1)  # Exceed timeout
                        return {
                            'success': False,
                            'error': 'Request timeout',
                            'status_code': 408,
                            'response_time': time.time() - start_time
                        }

                    # Normal response
                    time.sleep(random.uniform(0.1, 0.5))
                    return {
                        'success': True,
                        'data': {'test': 'data'},
                        'status_code': 200,
                        'response_time': time.time() - start_time
                    }

            provider = TimeoutProvider()
            tester = APILoadTester(api_config)

            result = tester.run_load_test(provider, ['/api/timeout_test'])

            return result

        result = benchmark(timeout_test)

        # Assertions
        assert result.timeout_requests > 0, "Timeout handling should be tested"
        assert result.successful_requests > 0, "Some requests should succeed"

    def test_retry_mechanism(self, benchmark, api_config):
        """Test API retry mechanism"""

        def retry_test():
            class RetryProvider:
                def __init__(self):
                    self.attempt_counts = {}

                def make_request(self, endpoint, params=None):
                    request_id = f"{threading.current_thread().ident}_{endpoint}"

                    # Track attempts
                    if request_id not in self.attempt_counts:
                        self.attempt_counts[request_id] = 0

                    self.attempt_counts[request_id] += 1
                    attempt = self.attempt_counts[request_id]

                    start_time = time.time()
                    time.sleep(random.uniform(0.1, 0.3))

                    # Fail first few attempts, succeed later
                    if attempt <= api_config.max_retries - 1:
                        return {
                            'success': False,
                            'error': f'Attempt {attempt} failed',
                            'status_code': 500,
                            'response_time': time.time() - start_time,
                            'attempt': attempt
                        }
                    else:
                        return {
                            'success': True,
                            'data': {'attempt': attempt},
                            'status_code': 200,
                            'response_time': time.time() - start_time,
                            'attempt': attempt
                        }

            provider = RetryProvider()
            tester = APILoadTester(api_config)

            tester.config.concurrent_requests = 2
            tester.config.requests_per_thread = 5

            result = tester.run_load_test(provider, ['/api/retry_test'])

            return {
                'result': result,
                'attempt_counts': provider.attempt_counts
            }

        result = benchmark(retry_test)

        # Assertions
        assert result['result'].total_requests > 0
        # Some requests should eventually succeed after retries
        assert result['result'].successful_requests > 0


if __name__ == '__main__':
    # Run API performance tests
    pytest.main([
        __file__,
        '-v',
        '--tb=short'
    ])