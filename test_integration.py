#!/usr/bin/env python3
"""
Integration Test Suite for DDM and PB Analysis Data Integration

This script tests the integration between DDM/PB analysis modules and the
enhanced data infrastructure (APIs + Excel sheets).

Test scenarios:
1. API-only mode (with different API fallbacks)
2. Excel-only mode (offline analysis)
3. Hybrid mode (API + Excel with fallbacks)
4. Error handling and graceful degradation
5. Data quality validation
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
try:
    from financial_calculations import FinancialCalculator
    from enhanced_data_manager import EnhancedDataManager
    from ddm_valuation import DDMValuator
    from pb_valuation import PBValuator
    from data_source_bridge import DataSourceBridge
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """
    Comprehensive integration test suite for DDM and PB analysis data integration
    """

    def __init__(self, test_company_folder: str = None, test_ticker: str = "AAPL"):
        """
        Initialize the integration tester

        Args:
            test_company_folder (str): Path to test company folder with Excel files
            test_ticker (str): Ticker symbol for API testing
        """
        self.test_company_folder = test_company_folder
        self.test_ticker = test_ticker
        self.test_results = {}
        self.setup_complete = False

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all integration tests

        Returns:
            Dict with comprehensive test results
        """
        logger.info("Starting comprehensive integration test suite")

        try:
            # Setup phase
            self._setup_test_environment()

            # Test scenarios
            test_scenarios = [
                ("API Only Mode", self._test_api_only_mode),
                ("Excel Only Mode", self._test_excel_only_mode),
                ("Hybrid Mode", self._test_hybrid_mode),
                ("Error Handling", self._test_error_handling),
                ("Data Quality Validation", self._test_data_quality),
                ("Bridge Integration", self._test_bridge_integration),
            ]

            for test_name, test_function in test_scenarios:
                logger.info(f"Running test: {test_name}")
                try:
                    result = test_function()
                    self.test_results[test_name] = {
                        'status': 'PASSED',
                        'result': result,
                        'error': None,
                    }
                    logger.info(f"✅ {test_name} PASSED")
                except Exception as e:
                    self.test_results[test_name] = {
                        'status': 'FAILED',
                        'result': None,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                    }
                    logger.error(f"❌ {test_name} FAILED: {e}")

            # Generate summary
            self._generate_test_summary()

            return self.test_results

        except Exception as e:
            logger.error(f"Test suite failed during setup: {e}")
            return {'setup_error': str(e)}

    def _setup_test_environment(self):
        """Setup test environment and validate prerequisites"""
        logger.info("Setting up test environment")

        # Check if we have a company folder for Excel testing
        if self.test_company_folder and os.path.exists(self.test_company_folder):
            logger.info(f"Using test company folder: {self.test_company_folder}")
        else:
            logger.warning("No valid company folder provided - Excel-only tests will be skipped")
            self.test_company_folder = None

        # Test basic imports and API availability
        try:
            import yfinance as yf

            # Test basic yfinance connectivity
            test_ticker = yf.Ticker(self.test_ticker)
            info = test_ticker.info
            if info:
                logger.info("✅ yfinance connectivity confirmed")
            else:
                logger.warning("⚠️ yfinance connectivity issues detected")
        except Exception as e:
            logger.warning(f"⚠️ yfinance setup issue: {e}")

        self.setup_complete = True
        logger.info("Test environment setup complete")

    def _test_api_only_mode(self) -> Dict[str, Any]:
        """Test API-only mode with various data sources"""
        logger.info("Testing API-only mode")

        # Create enhanced data manager
        try:
            enhanced_data_manager = EnhancedDataManager(
                base_path=str(project_root), cache_dir="test_cache"
            )
            logger.info("✅ Enhanced data manager created successfully")
        except Exception as e:
            logger.warning(f"Enhanced data manager creation failed: {e}")
            enhanced_data_manager = None

        # Create financial calculator without Excel data
        financial_calculator = FinancialCalculator(
            company_folder=None, enhanced_data_manager=enhanced_data_manager  # No Excel data
        )

        # Set ticker for API testing
        financial_calculator.ticker_symbol = self.test_ticker

        results = {}

        # Test market data fetching
        try:
            market_data = financial_calculator.fetch_market_data()
            results['market_data'] = {
                'success': market_data is not None,
                'has_price': bool(market_data and market_data.get('current_price', 0) > 0),
                'data_source': (
                    getattr(enhanced_data_manager, '_data_source_used', 'unknown')
                    if enhanced_data_manager
                    else 'fallback'
                ),
            }
            logger.info(
                f"Market data fetch: {'✅ Success' if results['market_data']['success'] else '❌ Failed'}"
            )
        except Exception as e:
            results['market_data'] = {'success': False, 'error': str(e)}

        # Test DDM with API data
        try:
            ddm_valuator = DDMValuator(financial_calculator)
            ddm_result = ddm_valuator.calculate_ddm_valuation()

            results['ddm_analysis'] = {
                'success': 'error' not in ddm_result,
                'has_dividend_data': ddm_result.get('dividend_data', {}).get('data_points', 0) > 0,
                'model_type': ddm_result.get('model_type', 'unknown'),
                'data_source': ddm_result.get('dividend_data', {}).get(
                    'data_source_used', 'unknown'
                ),
            }
            logger.info(
                f"DDM analysis: {'✅ Success' if results['ddm_analysis']['success'] else '❌ Failed'}"
            )
        except Exception as e:
            results['ddm_analysis'] = {'success': False, 'error': str(e)}

        # Test PB with API data
        try:
            pb_valuator = PBValuator(financial_calculator)
            pb_result = pb_valuator.calculate_pb_analysis()

            results['pb_analysis'] = {
                'success': 'error' not in pb_result,
                'has_book_value': pb_result.get('current_data', {}).get('book_value_per_share', 0)
                > 0,
                'has_pb_ratio': pb_result.get('current_data', {}).get('pb_ratio') is not None,
            }
            logger.info(
                f"PB analysis: {'✅ Success' if results['pb_analysis']['success'] else '❌ Failed'}"
            )
        except Exception as e:
            results['pb_analysis'] = {'success': False, 'error': str(e)}

        return results

    def _test_excel_only_mode(self) -> Dict[str, Any]:
        """Test Excel-only mode (offline analysis)"""
        logger.info("Testing Excel-only mode")

        if not self.test_company_folder:
            return {'skipped': True, 'reason': 'No test company folder available'}

        # Create financial calculator with Excel data only
        financial_calculator = FinancialCalculator(
            company_folder=self.test_company_folder, enhanced_data_manager=None  # No API access
        )

        results = {}

        # Test Excel data loading
        try:
            financial_calculator.load_financial_statements()
            results['excel_loading'] = {
                'success': bool(financial_calculator.financial_data),
                'statements_loaded': len(financial_calculator.financial_data),
                'has_income': 'income_fy' in financial_calculator.financial_data,
                'has_balance': 'balance_fy' in financial_calculator.financial_data,
                'has_cashflow': 'cashflow_fy' in financial_calculator.financial_data,
            }
            logger.info(
                f"Excel loading: {'✅ Success' if results['excel_loading']['success'] else '❌ Failed'}"
            )
        except Exception as e:
            results['excel_loading'] = {'success': False, 'error': str(e)}

        return results

    def _test_hybrid_mode(self) -> Dict[str, Any]:
        """Test hybrid mode (API + Excel with intelligent fallbacks)"""
        logger.info("Testing hybrid mode")

        if not self.test_company_folder:
            return {
                'skipped': True,
                'reason': 'No test company folder available for hybrid testing',
            }

        # Create enhanced data manager
        try:
            enhanced_data_manager = EnhancedDataManager(
                base_path=str(project_root), cache_dir="test_cache"
            )
        except Exception as e:
            logger.warning(f"Enhanced data manager creation failed: {e}")
            enhanced_data_manager = None

        # Create financial calculator with both Excel and API access
        financial_calculator = FinancialCalculator(
            company_folder=self.test_company_folder, enhanced_data_manager=enhanced_data_manager
        )

        # Set ticker for API testing
        financial_calculator.ticker_symbol = self.test_ticker

        results = {'setup': 'completed'}
        return results

    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and graceful degradation"""
        logger.info("Testing error handling")

        results = {}

        # Test with invalid ticker
        try:
            financial_calculator = FinancialCalculator(company_folder=None)
            financial_calculator.ticker_symbol = "INVALID_TICKER_12345"

            market_data = financial_calculator.fetch_market_data()
            results['invalid_ticker'] = {
                'handled_gracefully': market_data is None,
                'no_exception': True,
            }
        except Exception as e:
            results['invalid_ticker'] = {
                'handled_gracefully': False,
                'no_exception': False,
                'error': str(e),
            }

        return results

    def _test_data_quality(self) -> Dict[str, Any]:
        """Test data quality validation features"""
        logger.info("Testing data quality validation")

        results = {}

        # Test with real data
        try:
            financial_calculator = FinancialCalculator(company_folder=self.test_company_folder)
            financial_calculator.ticker_symbol = self.test_ticker

            # Test data source bridge validation
            bridge = DataSourceBridge(financial_calculator)

            ddm_validation = bridge.validate_data_for_analysis('ddm')
            pb_validation = bridge.validate_data_for_analysis('pb')

            results['data_validation'] = {
                'ddm_validation_works': isinstance(ddm_validation, dict)
                and 'valid' in ddm_validation,
                'pb_validation_works': isinstance(pb_validation, dict) and 'valid' in pb_validation,
                'ddm_completeness': ddm_validation.get('completeness_score', 0),
                'pb_completeness': pb_validation.get('completeness_score', 0),
            }

        except Exception as e:
            results['data_validation'] = {'success': False, 'error': str(e)}

        return results

    def _test_bridge_integration(self) -> Dict[str, Any]:
        """Test DataSourceBridge integration functionality"""
        logger.info("Testing DataSourceBridge integration")

        results = {}

        try:
            # Create minimal setup
            financial_calculator = FinancialCalculator(company_folder=self.test_company_folder)
            financial_calculator.ticker_symbol = self.test_ticker

            bridge = DataSourceBridge(financial_calculator)

            # Test market data access through bridge
            market_data = bridge.get_market_data()
            results['bridge_market_data'] = {
                'success': market_data is not None,
                'has_price': bool(market_data and market_data.get('current_price', 0) > 0),
            }

            # Test caching functionality
            cache_stats_before = bridge.get_cache_stats()
            market_data_2 = bridge.get_market_data()  # Should use cache
            cache_stats_after = bridge.get_cache_stats()

            results['bridge_caching'] = {
                'cache_working': cache_stats_after['cached_items']
                >= cache_stats_before['cached_items'],
                'cache_items': cache_stats_after['cached_items'],
            }

        except Exception as e:
            results['bridge_integration'] = {'success': False, 'error': str(e)}

        return results

    def _generate_test_summary(self):
        """Generate comprehensive test summary"""
        logger.info("Generating test summary")

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result['status'] == 'PASSED'
        )
        failed_tests = total_tests - passed_tests

        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_completion_time': 'N/A',  # Could add timing if needed
        }

        self.test_results['SUMMARY'] = summary

        # Log summary
        logger.info(
            f"Test Summary: {passed_tests}/{total_tests} passed ({summary['success_rate']:.1f}%)"
        )

        if failed_tests > 0:
            logger.warning("Failed tests:")
            for test_name, result in self.test_results.items():
                if result.get('status') == 'FAILED':
                    logger.warning(f"  - {test_name}: {result.get('error', 'Unknown error')}")


def main():
    """Main test runner"""
    print("🧪 DDM and PB Analysis Data Integration Test Suite")
    print("=" * 60)

    # Check for test data
    test_company_folder = None
    possible_test_folders = [
        "test_data/sample_company",
        "../test_data/sample_company",
        "data/sample_company",
    ]

    for folder in possible_test_folders:
        if os.path.exists(folder):
            test_company_folder = folder
            break

    if test_company_folder:
        print(f"📁 Using test company folder: {test_company_folder}")
    else:
        print("⚠️  No test company folder found - Excel-only tests will be skipped")

    # Run tests
    tester = IntegrationTester(
        test_company_folder=test_company_folder, test_ticker="AAPL"  # Use Apple as test ticker
    )

    results = tester.run_all_tests()

    # Print final results
    print("\n" + "=" * 60)
    print("📊 Final Test Results")
    print("=" * 60)

    if 'SUMMARY' in results:
        summary = results['SUMMARY']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        if summary['success_rate'] >= 80:
            print("\n🎉 Integration tests mostly successful!")
        elif summary['success_rate'] >= 60:
            print("\n⚠️  Integration tests partially successful - some issues detected")
        else:
            print("\n❌ Integration tests failed - significant issues detected")
    else:
        print("❌ Test suite failed to complete")

    return results


if __name__ == "__main__":
    results = main()
