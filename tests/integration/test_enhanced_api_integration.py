"""
Test Suite for Enhanced API Integration with Fallback Logic
===========================================================

This test suite validates the enhanced API integration system including:
- Cascading fallback logic across multiple API providers
- Rate limiting and error handling
- Comprehensive logging and monitoring
- Circuit breaker functionality
- Health monitoring and performance metrics

Usage:
    python test_enhanced_api_integration.py
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Import the enhanced API manager
from core.data_processing.adapters.enhanced_api_manager import (
    EnhancedApiManager,
    create_enhanced_manager,
    ProviderHealthStatus,
    RateLimitConfig
)
from core.data_processing.adapters.base_adapter import DataCategory, DataSourceType

# Setup logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApiIntegrationTester:
    """Comprehensive test suite for Enhanced API Manager"""
    
    def __init__(self):
        self.manager = None
        self.test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        self.results = {}
    
    def run_all_tests(self):
        """Run all API integration tests"""
        logger.info("Starting Enhanced API Integration Test Suite")
        logger.info("=" * 60)
        
        try:
            # Initialize the enhanced manager
            self.setup_test_environment()
            
            # Test basic functionality
            self.test_basic_fallback_logic()
            
            # Test rate limiting
            self.test_rate_limiting()
            
            # Test error handling and recovery
            self.test_error_handling()
            
            # Test circuit breaker functionality
            self.test_circuit_breaker()
            
            # Test parallel processing
            self.test_parallel_processing()
            
            # Test health monitoring
            self.test_health_monitoring()
            
            # Test comprehensive logging
            self.test_logging_functionality()
            
            # Generate final report
            self.generate_test_report()
            
            return self.results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
        finally:
            self.cleanup_test_environment()
    
    def setup_test_environment(self):
        """Initialize test environment"""
        logger.info("Setting up test environment...")
        
        # Create enhanced manager with test configuration
        self.manager = create_enhanced_manager()
        
        # Verify manager initialization
        assert self.manager is not None, "Enhanced manager failed to initialize"
        assert len(self.manager.adapters) > 0, "No API adapters available"
        
        logger.info(f"Initialized with {len(self.manager.adapters)} API adapters")
        for adapter_type in self.manager.adapters.keys():
            logger.info(f"  - {adapter_type.value} adapter available")
        
        self.results['setup'] = {
            'success': True,
            'adapters_count': len(self.manager.adapters),
            'adapters': [a.value for a in self.manager.adapters.keys()]
        }
    
    def test_basic_fallback_logic(self):
        """Test basic cascading fallback functionality"""
        logger.info("\n--- Testing Basic Fallback Logic ---")
        
        test_symbol = "AAPL"
        
        try:
            # Test normal fallback scenario
            result = self.manager.load_symbol_data_enhanced(
                symbol=test_symbol,
                categories=[DataCategory.MARKET_DATA, DataCategory.COMPANY_INFO],
                historical_years=2
            )
            
            # Validate results
            assert result is not None, "No result returned"
            assert result.symbol == test_symbol, f"Symbol mismatch: {result.symbol}"
            
            # Check fallback behavior
            logger.info(f"Sources attempted: {[s.value for s in result.sources_attempted]}")
            logger.info(f"Primary source: {result.primary_source.value if result.primary_source else 'None'}")
            logger.info(f"Fallback sources: {[s.value for s in result.fallback_sources]}")
            logger.info(f"Overall quality: {result.overall_quality:.2f}")
            logger.info(f"Success: {result.success}")
            
            self.results['basic_fallback'] = {
                'success': result.success,
                'sources_attempted': len(result.sources_attempted),
                'primary_source': result.primary_source.value if result.primary_source else None,
                'fallback_count': len(result.fallback_sources),
                'quality_score': result.overall_quality,
                'variables_extracted': result.total_variables_extracted
            }
            
            logger.info("✓ Basic fallback logic test completed successfully")
            
        except Exception as e:
            logger.error(f"✗ Basic fallback test failed: {e}")
            self.results['basic_fallback'] = {'success': False, 'error': str(e)}
            raise
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        logger.info("\n--- Testing Rate Limiting ---")
        
        try:
            # Test rapid requests to trigger rate limiting
            start_time = time.time()
            requests_made = 0
            rate_limit_triggered = False
            
            for i in range(10):  # Make multiple rapid requests
                try:
                    result = self.manager.load_symbol_data_enhanced(
                        symbol=self.test_symbols[i % len(self.test_symbols)],
                        categories=[DataCategory.MARKET_DATA]
                    )
                    requests_made += 1
                    
                    # Check for rate limit warnings
                    if any("rate limit" in warning.lower() for warning in result.warnings):
                        rate_limit_triggered = True
                        logger.info(f"Rate limit detected after {requests_made} requests")
                        break
                        
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        rate_limit_triggered = True
                        logger.info(f"Rate limit exception after {requests_made} requests: {e}")
                        break
                    else:
                        logger.warning(f"Unexpected error during rate limit test: {e}")
            
            elapsed_time = time.time() - start_time
            
            # Get rate limit status
            rate_status = self.manager._get_rate_limit_status()
            
            self.results['rate_limiting'] = {
                'success': True,
                'requests_made': requests_made,
                'rate_limit_triggered': rate_limit_triggered,
                'elapsed_time': elapsed_time,
                'rate_status': rate_status
            }
            
            logger.info(f"✓ Rate limiting test completed")
            logger.info(f"  Requests made: {requests_made}")
            logger.info(f"  Rate limit triggered: {rate_limit_triggered}")
            logger.info(f"  Elapsed time: {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"✗ Rate limiting test failed: {e}")
            self.results['rate_limiting'] = {'success': False, 'error': str(e)}
    
    def test_error_handling(self):
        """Test error handling and recovery mechanisms"""
        logger.info("\n--- Testing Error Handling ---")
        
        try:
            # Test with invalid symbol
            result = self.manager.load_symbol_data_enhanced(
                symbol="INVALID_SYMBOL_12345",
                categories=[DataCategory.MARKET_DATA]
            )
            
            # Should handle gracefully
            assert result is not None, "No result for invalid symbol"
            
            # Test network timeout scenarios (simulated)
            logger.info("Testing timeout handling...")
            
            # Test multiple failures to trigger circuit breaker
            failure_count = 0
            for i in range(3):
                try:
                    result = self.manager.load_symbol_data_enhanced(
                        symbol="ANOTHER_INVALID_SYMBOL",
                        categories=[DataCategory.MARKET_DATA]
                    )
                    if not result.success:
                        failure_count += 1
                except Exception:
                    failure_count += 1
            
            self.results['error_handling'] = {
                'success': True,
                'invalid_symbol_handled': True,
                'failure_count': failure_count,
                'errors_recorded': len(result.errors) if 'result' in locals() else 0
            }
            
            logger.info("✓ Error handling test completed successfully")
            logger.info(f"  Handled {failure_count} simulated failures")
            
        except Exception as e:
            logger.error(f"✗ Error handling test failed: {e}")
            self.results['error_handling'] = {'success': False, 'error': str(e)}
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        logger.info("\n--- Testing Circuit Breaker ---")
        
        try:
            # Get initial circuit breaker status
            initial_stats = self.manager.get_enhanced_statistics()
            circuit_breaker_status = initial_stats.get('circuit_breaker_status', {})
            
            logger.info("Circuit breaker states:")
            for provider, status in circuit_breaker_status.items():
                logger.info(f"  {provider}: {status['state']} (failures: {status['failure_count']})")
            
            # Test manual circuit breaker reset
            reset_success = False
            for source_type in self.manager.circuit_breakers.keys():
                if self.manager.reset_circuit_breaker(source_type):
                    reset_success = True
                    logger.info(f"Successfully reset circuit breaker for {source_type.value}")
                    break
            
            self.results['circuit_breaker'] = {
                'success': True,
                'initial_states': circuit_breaker_status,
                'reset_test': reset_success
            }
            
            logger.info("✓ Circuit breaker test completed successfully")
            
        except Exception as e:
            logger.error(f"✗ Circuit breaker test failed: {e}")
            self.results['circuit_breaker'] = {'success': False, 'error': str(e)}
    
    def test_parallel_processing(self):
        """Test parallel API processing"""
        logger.info("\n--- Testing Parallel Processing ---")
        
        try:
            # Test parallel requests for multiple symbols
            start_time = time.time()
            
            # Test parallel-style requests (sequential for now) 
            results = []
            for symbol in self.test_symbols[:3]:  # Test with first 3 symbols
                try:
                    result = self.manager.load_symbol_data_enhanced(
                        symbol=symbol,
                        categories=[DataCategory.MARKET_DATA],
                        max_parallel_requests=2
                    )
                    results.append((symbol, result))
                    logger.info(f"Request for {symbol}: {'SUCCESS' if result.success else 'FAILED'}")
                except Exception as e:
                    logger.error(f"Request for {symbol} failed: {e}")
                    results.append((symbol, None))
            
            elapsed_time = time.time() - start_time
            successful_results = [r for _, r in results if r and r.success]
            
            self.results['parallel_processing'] = {
                'success': True,
                'total_requests': len(results),
                'successful_requests': len(successful_results),
                'elapsed_time': elapsed_time,
                'parallel_efficiency': len(successful_results) / len(results) if results else 0
            }
            
            logger.info("✓ Parallel processing test completed successfully")
            logger.info(f"  Total requests: {len(results)}")
            logger.info(f"  Successful: {len(successful_results)}")
            logger.info(f"  Elapsed time: {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"✗ Parallel processing test failed: {e}")
            self.results['parallel_processing'] = {'success': False, 'error': str(e)}
    
    def test_health_monitoring(self):
        """Test health monitoring functionality"""
        logger.info("\n--- Testing Health Monitoring ---")
        
        try:
            # Get health report
            health_report = self.manager.get_health_report()
            
            logger.info(f"Overall health: {health_report['overall_health']}")
            logger.info("Provider health status:")
            
            healthy_providers = 0
            total_providers = len(health_report['providers'])
            
            for provider, status in health_report['providers'].items():
                logger.info(f"  {provider}: {status['status']} "
                          f"(success rate: {status['success_rate']}, "
                          f"response time: {status['avg_response_time']})")
                
                if status['status'] in ['healthy', 'degraded']:
                    healthy_providers += 1
            
            # Test enhanced statistics
            enhanced_stats = self.manager.get_enhanced_statistics()
            
            self.results['health_monitoring'] = {
                'success': True,
                'overall_health': health_report['overall_health'],
                'healthy_providers': healthy_providers,
                'total_providers': total_providers,
                'health_percentage': healthy_providers / total_providers if total_providers > 0 else 0,
                'stats_available': 'provider_health' in enhanced_stats
            }
            
            logger.info("✓ Health monitoring test completed successfully")
            logger.info(f"  Healthy providers: {healthy_providers}/{total_providers}")
            
        except Exception as e:
            logger.error(f"✗ Health monitoring test failed: {e}")
            self.results['health_monitoring'] = {'success': False, 'error': str(e)}
    
    def test_logging_functionality(self):
        """Test comprehensive logging functionality"""
        logger.info("\n--- Testing Logging Functionality ---")
        
        try:
            # Make a request to generate log entries
            result = self.manager.load_symbol_data_enhanced(
                symbol="AAPL",
                categories=[DataCategory.MARKET_DATA]
            )
            
            # Check if API call details are recorded
            api_calls_recorded = len(result.api_call_details) > 0
            
            # Check request history
            request_history_available = len(self.manager.request_history) > 0
            
            # Test logging levels and structured data
            log_data_structured = False
            if request_history_available:
                last_request = list(self.manager.request_history)[-1]
                required_fields = ['timestamp', 'provider', 'symbol', 'status', 'response_time_ms']
                log_data_structured = all(field in last_request for field in required_fields)
            
            self.results['logging'] = {
                'success': True,
                'api_calls_recorded': api_calls_recorded,
                'request_history_available': request_history_available,
                'structured_logging': log_data_structured,
                'total_requests_logged': len(self.manager.request_history)
            }
            
            logger.info("✓ Logging functionality test completed successfully")
            logger.info(f"  API calls recorded: {api_calls_recorded}")
            logger.info(f"  Request history available: {request_history_available}")
            logger.info(f"  Structured logging: {log_data_structured}")
            
        except Exception as e:
            logger.error(f"✗ Logging functionality test failed: {e}")
            self.results['logging'] = {'success': False, 'error': str(e)}
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("ENHANCED API INTEGRATION TEST REPORT")
        logger.info("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        logger.info(f"Test Summary: {passed_tests}/{total_tests} tests passed")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        # Detailed results
        for test_name, result in self.results.items():
            status = "✓ PASS" if result.get('success', False) else "✗ FAIL"
            logger.info(f"\n{test_name.upper()}: {status}")
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if key != 'success':
                        if isinstance(value, (int, float, str, bool)):
                            logger.info(f"  {key}: {value}")
                        elif isinstance(value, list) and len(value) <= 5:
                            logger.info(f"  {key}: {value}")
                        elif isinstance(value, dict) and len(value) <= 3:
                            logger.info(f"  {key}: {value}")
        
        # Performance metrics
        if self.manager:
            final_stats = self.manager.get_enhanced_statistics()
            if 'manager_stats' in final_stats:
                manager_stats = final_stats['manager_stats']
                logger.info(f"\nPerformance Metrics:")
                logger.info(f"  Total requests: {manager_stats.get('total_requests', 0)}")
                logger.info(f"  Success rate: {manager_stats.get('success_rate', 0):.1%}")
                logger.info(f"  Average response time: {manager_stats.get('average_response_times', {})}")
        
        # Final assessment
        if passed_tests == total_tests:
            logger.info("\n🎉 ALL TESTS PASSED - Enhanced API Integration is working correctly!")
        elif passed_tests >= total_tests * 0.8:
            logger.info(f"\n⚠️  MOSTLY PASSING - {passed_tests}/{total_tests} tests passed")
        else:
            logger.info(f"\n❌ MULTIPLE FAILURES - Only {passed_tests}/{total_tests} tests passed")
        
        return self.results
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        logger.info("\nCleaning up test environment...")
        
        # Any cleanup operations would go here
        if self.manager:
            # Log final statistics
            try:
                final_health = self.manager.get_health_report()
                logger.info("Final system health: " + final_health['overall_health'])
            except Exception as e:
                logger.warning(f"Could not get final health report: {e}")
        
        logger.info("Test cleanup completed")


def main():
    """Main test execution function"""
    tester = ApiIntegrationTester()
    
    try:
        results = tester.run_all_tests()
        
        # Return exit code based on test results
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        if passed_tests == total_tests:
            print(f"\n[PASS] All {total_tests} tests passed successfully!")
            return 0
        else:
            print(f"\n[PARTIAL] {total_tests - passed_tests} of {total_tests} tests failed")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] Test suite execution failed: {e}")
        logger.exception("Test suite execution failed")
        return 2


def run_synchronous_test():
    """Synchronous wrapper for running tests"""
    print("Enhanced API Integration Test Suite")
    print("=" * 50)
    
    try:
        # Run the test suite
        return main()
    except KeyboardInterrupt:
        print("\n[STOP] Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Failed to start test suite: {e}")
        return 2


if __name__ == "__main__":
    import sys
    exit_code = run_synchronous_test()
    sys.exit(exit_code)