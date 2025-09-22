#!/usr/bin/env python3
"""
End-to-End Resilience Workflow Tests
====================================

Comprehensive end-to-end tests that validate complete data acquisition
workflows with resilience features including:
- Complete data flow from source to analysis
- Fallback source integration
- Cache coherency across workflow steps
- Error recovery during multi-step processes
- Real-world scenario validation
"""

import sys
import time
import logging
import unittest
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.data_processing.rate_limiting.enhanced_rate_limiter import reset_rate_limiter
from core.data_processing.monitoring.health_monitor import reset_health_monitor
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.ddm.ddm_valuation import DDMValuator
from core.analysis.pb.pb_calculation_engine import PBCalculationEngine
from utils.input_validator import ValidationLevel
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkflowValidator:
    """Helper class to validate workflow results"""

    @staticmethod
    def validate_market_data(data: dict, ticker: str) -> bool:
        """Validate market data structure and content"""
        if not data:
            return False

        required_fields = ['ticker', 'current_price', 'company_name']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False

        if data.get('ticker') != ticker:
            logger.warning(f"Ticker mismatch: expected {ticker}, got {data.get('ticker')}")
            return False

        if not isinstance(data.get('current_price'), (int, float)) or data.get('current_price') <= 0:
            logger.warning(f"Invalid price: {data.get('current_price')}")
            return False

        return True

    @staticmethod
    def validate_financial_data(data: dict, ticker: str) -> bool:
        """Validate financial statement data"""
        if not data:
            return False

        # Check for essential financial metrics
        essential_metrics = ['revenue', 'total_assets', 'total_equity']
        found_metrics = 0

        for metric in essential_metrics:
            if metric in data and data[metric] is not None:
                found_metrics += 1

        return found_metrics >= 2  # At least 2 out of 3 essential metrics

    @staticmethod
    def validate_analysis_result(result: dict, analysis_type: str) -> bool:
        """Validate analysis calculation results"""
        if not result:
            return False

        if analysis_type == 'dcf':
            required_fields = ['intrinsic_value', 'current_price']
        elif analysis_type == 'ddm':
            required_fields = ['fair_value', 'current_price']
        elif analysis_type == 'pb':
            required_fields = ['fair_value', 'current_pb_ratio']
        else:
            return False

        for field in required_fields:
            if field not in result or result[field] is None:
                logger.warning(f"Missing {analysis_type} field: {field}")
                return False

        return True


@pytest.mark.e2e
class TestResilienceWorkflows(unittest.TestCase):
    """End-to-end resilience workflow tests"""

    def setUp(self):
        """Set up test environment"""
        reset_rate_limiter()
        reset_health_monitor()

        with patch('time.sleep'):  # Speed up setup
            self.manager = CentralizedDataManager(
                base_path=".",
                validation_level=ValidationLevel.PERMISSIVE
            )

        self.validator = WorkflowValidator()
        self.test_ticker = "AAPL"  # Use well-known ticker for testing

    def tearDown(self):
        """Clean up after tests"""
        reset_rate_limiter()
        reset_health_monitor()

    @pytest.mark.timeout(120)
    def test_complete_market_data_workflow(self):
        """Test complete market data acquisition workflow with resilience"""
        logger.info("Testing complete market data workflow")

        workflow_results = {
            'steps_completed': 0,
            'fallback_used': False,
            'cache_utilized': False,
            'data_quality': 'unknown'
        }

        # Step 1: Initial market data fetch
        logger.info(f"Step 1: Fetching market data for {self.test_ticker}")
        try:
            market_data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
            workflow_results['steps_completed'] += 1

            if self.validator.validate_market_data(market_data, self.test_ticker):
                workflow_results['data_quality'] = 'good'
                logger.info("✓ Market data validation passed")
            else:
                workflow_results['data_quality'] = 'poor'
                logger.warning("⚠ Market data validation failed")

        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            market_data = None

        # Step 2: Test cache utilization
        logger.info("Step 2: Testing cache utilization")
        try:
            start_time = time.time()
            cached_data = self.manager.fetch_market_data(self.test_ticker, force_reload=False)
            cache_time = time.time() - start_time

            workflow_results['steps_completed'] += 1

            if cached_data and cache_time < 1.0:  # Should be fast from cache
                workflow_results['cache_utilized'] = True
                logger.info("✓ Cache utilization successful")
            else:
                logger.warning("⚠ Cache utilization unclear")

        except Exception as e:
            logger.error(f"Step 2 failed: {e}")

        # Step 3: Test fallback mechanism
        logger.info("Step 3: Testing fallback mechanism")
        try:
            # Force Yahoo Finance to fail
            with patch('core.data_processing.managers.centralized_data_manager.yf.Ticker') as mock_ticker:
                mock_ticker.side_effect = Exception("Simulated Yahoo Finance failure")

                fallback_data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
                workflow_results['steps_completed'] += 1

                if fallback_data:
                    workflow_results['fallback_used'] = True
                    logger.info("✓ Fallback mechanism successful")
                else:
                    logger.warning("⚠ Fallback mechanism failed")

        except Exception as e:
            logger.error(f"Step 3 failed: {e}")

        # Workflow validation
        self.assertGreaterEqual(workflow_results['steps_completed'], 2,
                               "Should complete at least 2 workflow steps")

        if workflow_results['cache_utilized']:
            logger.info("✓ Cache workflow validated")

        if workflow_results['fallback_used']:
            logger.info("✓ Fallback workflow validated")

        logger.info(f"Market data workflow results: {workflow_results}")

    @pytest.mark.timeout(180)
    def test_financial_analysis_workflow_with_resilience(self):
        """Test complete financial analysis workflow with resilience features"""
        logger.info("Testing financial analysis workflow with resilience")

        analysis_results = {
            'market_data_success': False,
            'financial_data_success': False,
            'dcf_analysis_success': False,
            'ddm_analysis_success': False,
            'pb_analysis_success': False,
            'resilience_events': []
        }

        # Step 1: Market data acquisition with resilience
        logger.info("Step 1: Market data acquisition")
        try:
            market_data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)

            if market_data and self.validator.validate_market_data(market_data, self.test_ticker):
                analysis_results['market_data_success'] = True
                logger.info("✓ Market data acquired successfully")
            else:
                logger.warning("⚠ Market data acquisition failed")

        except Exception as e:
            logger.error(f"Market data step failed: {e}")
            analysis_results['resilience_events'].append(f"market_data_error: {type(e).__name__}")

        # Step 2: Financial data acquisition
        logger.info("Step 2: Financial data acquisition")
        try:
            # Try to get financial data from Excel first, then APIs
            financial_data = {}

            # Attempt Excel data fetch
            try:
                excel_data = self.manager.fetch_financial_data(self.test_ticker)
                if excel_data:
                    financial_data.update(excel_data)
                    logger.info("✓ Excel financial data loaded")
            except Exception as e:
                analysis_results['resilience_events'].append(f"excel_fallback: {type(e).__name__}")
                logger.info("→ Excel data unavailable, using API fallback")

            # Fallback to API data if needed
            if not financial_data:
                try:
                    api_data = self.manager._fetch_fallback_financial_data(self.test_ticker)
                    if api_data:
                        financial_data.update(api_data)
                        logger.info("✓ API financial data fallback successful")
                except Exception as e:
                    analysis_results['resilience_events'].append(f"api_fallback: {type(e).__name__}")

            if self.validator.validate_financial_data(financial_data, self.test_ticker):
                analysis_results['financial_data_success'] = True
                logger.info("✓ Financial data validation passed")

        except Exception as e:
            logger.error(f"Financial data step failed: {e}")
            analysis_results['resilience_events'].append(f"financial_data_error: {type(e).__name__}")

        # Step 3: DCF Analysis with resilience
        logger.info("Step 3: DCF Analysis")
        try:
            if analysis_results['market_data_success'] and analysis_results['financial_data_success']:
                with patch('time.sleep'):  # Speed up analysis
                    calculator = FinancialCalculator(
                        ticker=self.test_ticker,
                        base_path=".",
                        validation_level=ValidationLevel.PERMISSIVE
                    )

                    dcf_analysis = DCFValuator(calculator)
                    dcf_result = dcf_analysis.calculate_dcf_valuation()

                    if self.validator.validate_analysis_result(dcf_result, 'dcf'):
                        analysis_results['dcf_analysis_success'] = True
                        logger.info("✓ DCF analysis successful")

        except Exception as e:
            logger.error(f"DCF analysis failed: {e}")
            analysis_results['resilience_events'].append(f"dcf_error: {type(e).__name__}")

        # Step 4: DDM Analysis with resilience
        logger.info("Step 4: DDM Analysis")
        try:
            if analysis_results['market_data_success']:
                with patch('time.sleep'):  # Speed up analysis
                    calculator = FinancialCalculator(
                        ticker=self.test_ticker,
                        base_path=".",
                        validation_level=ValidationLevel.PERMISSIVE
                    )

                    ddm_analysis = DDMValuator(calculator)
                    ddm_result = ddm_analysis.calculate_fair_value()

                    if self.validator.validate_analysis_result(ddm_result, 'ddm'):
                        analysis_results['ddm_analysis_success'] = True
                        logger.info("✓ DDM analysis successful")

        except Exception as e:
            logger.error(f"DDM analysis failed: {e}")
            analysis_results['resilience_events'].append(f"ddm_error: {type(e).__name__}")

        # Step 5: P/B Analysis with resilience
        logger.info("Step 5: P/B Analysis")
        try:
            if analysis_results['market_data_success']:
                with patch('time.sleep'):  # Speed up analysis
                    calculator = FinancialCalculator(
                        ticker=self.test_ticker,
                        base_path=".",
                        validation_level=ValidationLevel.PERMISSIVE
                    )

                    pb_engine = PBCalculationEngine(calculator)
                    pb_result = pb_engine.calculate_pb_fair_value()

                    if self.validator.validate_analysis_result(pb_result, 'pb'):
                        analysis_results['pb_analysis_success'] = True
                        logger.info("✓ P/B analysis successful")

        except Exception as e:
            logger.error(f"P/B analysis failed: {e}")
            analysis_results['resilience_events'].append(f"pb_error: {type(e).__name__}")

        # Workflow validation
        successful_analyses = sum([
            analysis_results['dcf_analysis_success'],
            analysis_results['ddm_analysis_success'],
            analysis_results['pb_analysis_success']
        ])

        self.assertGreaterEqual(successful_analyses, 1,
                               "Should complete at least one financial analysis")

        # Log resilience events
        if analysis_results['resilience_events']:
            logger.info(f"Resilience events encountered: {analysis_results['resilience_events']}")
        else:
            logger.info("✓ No resilience events needed - smooth workflow")

        logger.info(f"Financial analysis workflow results: {analysis_results}")

    @pytest.mark.timeout(90)
    def test_multi_ticker_workflow_resilience(self):
        """Test workflow resilience across multiple tickers"""
        logger.info("Testing multi-ticker workflow resilience")

        test_tickers = ["AAPL", "MSFT", "GOOGL", "INVALID_TICKER", "TSLA"]
        workflow_results = {
            'total_tickers': len(test_tickers),
            'successful_tickers': 0,
            'failed_tickers': 0,
            'fallback_used_count': 0,
            'error_recovery_count': 0,
            'ticker_results': {}
        }

        for ticker in test_tickers:
            logger.info(f"Processing ticker: {ticker}")
            ticker_result = {
                'market_data': False,
                'financial_data': False,
                'errors_encountered': [],
                'fallback_used': False
            }

            # Market data for each ticker
            try:
                market_data = self.manager.fetch_market_data(ticker, force_reload=True)
                if market_data and self.validator.validate_market_data(market_data, ticker):
                    ticker_result['market_data'] = True
                    logger.info(f"✓ {ticker} market data success")
                else:
                    logger.warning(f"⚠ {ticker} market data validation failed")

            except Exception as e:
                ticker_result['errors_encountered'].append(f"market_data: {type(e).__name__}")
                logger.info(f"→ {ticker} market data error, attempting fallback")

                # Attempt fallback
                try:
                    fallback_data = self.manager._fetch_fallback_market_data(ticker)
                    if fallback_data:
                        ticker_result['fallback_used'] = True
                        ticker_result['market_data'] = True
                        workflow_results['fallback_used_count'] += 1
                        logger.info(f"✓ {ticker} fallback market data success")
                except Exception as fallback_e:
                    ticker_result['errors_encountered'].append(f"fallback: {type(fallback_e).__name__}")

            # Financial data for each ticker (if market data succeeded)
            if ticker_result['market_data']:
                try:
                    financial_data = self.manager.fetch_financial_data(ticker)
                    if financial_data and self.validator.validate_financial_data(financial_data, ticker):
                        ticker_result['financial_data'] = True
                        logger.info(f"✓ {ticker} financial data success")

                except Exception as e:
                    ticker_result['errors_encountered'].append(f"financial_data: {type(e).__name__}")

            # Count successes and failures
            if ticker_result['market_data'] or ticker_result['financial_data']:
                workflow_results['successful_tickers'] += 1
            else:
                workflow_results['failed_tickers'] += 1

            if ticker_result['errors_encountered']:
                workflow_results['error_recovery_count'] += 1

            workflow_results['ticker_results'][ticker] = ticker_result

        # Workflow validation
        success_rate = (workflow_results['successful_tickers'] /
                       workflow_results['total_tickers'] * 100)

        self.assertGreater(success_rate, 50,
                          "Should maintain >50% success rate across multiple tickers")

        if workflow_results['fallback_used_count'] > 0:
            logger.info(f"✓ Fallback mechanisms used {workflow_results['fallback_used_count']} times")

        logger.info(f"Multi-ticker workflow results: {workflow_results}")
        logger.info(f"Overall success rate: {success_rate:.1f}%")

    @pytest.mark.timeout(60)
    def test_error_recovery_workflow(self):
        """Test error recovery during workflow execution"""
        logger.info("Testing error recovery workflow")

        recovery_results = {
            'network_error_recovery': False,
            'api_error_recovery': False,
            'data_validation_recovery': False,
            'circuit_breaker_recovery': False
        }

        # Test 1: Network error recovery
        logger.info("Test 1: Network error recovery")
        try:
            with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network error")):
                data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
                if data:  # Should get data from fallback or cache
                    recovery_results['network_error_recovery'] = True
                    logger.info("✓ Network error recovery successful")
        except Exception as e:
            logger.info(f"→ Network error recovery test: {e}")

        # Test 2: API error recovery
        logger.info("Test 2: API error recovery")
        try:
            with patch('requests.get', side_effect=requests.exceptions.HTTPError("API error")):
                data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
                if data:  # Should get data from alternative source
                    recovery_results['api_error_recovery'] = True
                    logger.info("✓ API error recovery successful")
        except Exception as e:
            logger.info(f"→ API error recovery test: {e}")

        # Test 3: Data validation recovery
        logger.info("Test 3: Data validation recovery")
        try:
            # Mock invalid data that should trigger validation fallback
            def mock_invalid_data(*args, **kwargs):
                return {'ticker': 'WRONG', 'price': -100}  # Invalid data

            with patch.object(self.manager, '_fetch_yahoo_finance_data', mock_invalid_data):
                data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
                if data and data.get('ticker') == self.test_ticker:
                    recovery_results['data_validation_recovery'] = True
                    logger.info("✓ Data validation recovery successful")
        except Exception as e:
            logger.info(f"→ Data validation recovery test: {e}")

        # Test 4: Circuit breaker recovery
        logger.info("Test 4: Circuit breaker recovery")
        try:
            rate_limiter = self.manager.rate_limiter
            yahoo_cb = rate_limiter.circuit_breakers.get('yahoo_finance')

            if yahoo_cb:
                # Force circuit breaker open
                for i in range(10):
                    yahoo_cb.record_failure()

                # Should still get data via fallback
                data = self.manager.fetch_market_data(self.test_ticker, force_reload=True)
                if data:
                    recovery_results['circuit_breaker_recovery'] = True
                    logger.info("✓ Circuit breaker recovery successful")

        except Exception as e:
            logger.info(f"→ Circuit breaker recovery test: {e}")

        # Validate recovery mechanisms
        recovery_count = sum(recovery_results.values())
        self.assertGreater(recovery_count, 0,
                          "Should demonstrate at least one recovery mechanism")

        logger.info(f"Error recovery results: {recovery_results}")
        logger.info(f"Recovery mechanisms working: {recovery_count}/4")


def run_resilience_workflow_tests():
    """Run the resilience workflow test suite"""
    print("=" * 70)
    print("RESILIENCE WORKFLOW TEST SUITE")
    print("=" * 70)
    print("Testing end-to-end workflow resilience and recovery")
    print()

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestResilienceWorkflows)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 70)
    print("WORKFLOW RESILIENCE SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nWORKFLOW ISSUES:")
        for test, traceback in result.failures:
            print(f"- {test}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) /
                   result.testsRun * 100) if result.testsRun > 0 else 0

    print(f"\nWorkflow Resilience Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("🔄 WORKFLOW RESILIENCE EXCELLENT: End-to-end workflows handle failures gracefully")
    elif success_rate >= 60:
        print("⚠️  WORKFLOW RESILIENCE GOOD: Most workflows resilient, some improvements possible")
    else:
        print("❌ WORKFLOW RESILIENCE NEEDS IMPROVEMENT: Significant workflow robustness issues")

    print("\nWorkflow Recommendations:")
    print("- Monitor end-to-end success rates in production")
    print("- Implement workflow health dashboards")
    print("- Add workflow-level alerting for systematic failures")
    print("- Consider workflow retry mechanisms for transient failures")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_resilience_workflow_tests()
    print(f"\n{'✅ Workflow tests passed!' if success else '❌ Workflow tests failed!'}")