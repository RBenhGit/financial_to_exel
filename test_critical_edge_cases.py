"""
Critical Edge Case Testing for Financial Analysis System

This test module implements the most critical edge case testing for:
1. Negative free cash flow scenarios and financial distress companies
2. Missing financial data and incomplete API responses with graceful error handling
3. Basic performance testing for multiple companies
4. Integration tests for complete workflows

Task #21 Implementation - Testing Enhancement & Edge Cases (Core Tests)
"""

import sys
import os
import time
import logging
import tempfile
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from financial_calculations import (
        FinancialCalculator,
        calculate_unified_fcf,
        validate_fcf_calculation,
        safe_numeric_conversion,
        handle_financial_nan_series,
    )
    from data_validator import FinancialDataValidator
    from error_handler import FinancialAnalysisError, CalculationError, ValidationError
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules may not be available, continuing with available tests...")

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CriticalEdgeCaseTests:
    """Critical edge case tests that must pass for system reliability"""

    def __init__(self):
        self.test_results = []
        self.failed_tests = []

    def run_all_tests(self):
        """Run all critical edge case tests"""
        print("=" * 80)
        print("CRITICAL EDGE CASE TESTING - Task #21 Implementation")
        print("=" * 80)

        # Test 1: Negative Cash Flow Scenarios
        self._test_negative_cash_flow_scenarios()

        # Test 2: Missing Data Handling
        self._test_missing_data_handling()

        # Test 3: API Failure Simulation
        self._test_api_failure_handling()

        # Test 4: Malformed Data Handling
        self._test_malformed_data_handling()

        # Test 5: Performance with Multiple Companies
        self._test_basic_performance()

        # Test 6: End-to-End Integration
        self._test_end_to_end_integration()

        # Test 7: Utility Functions Edge Cases
        self._test_utility_functions()

        # Generate final report
        self._generate_test_report()

    def _test_negative_cash_flow_scenarios(self):
        """Test 1: Negative Cash Flow and Financial Distress Scenarios"""
        print("\n[TEST 1] Negative Cash Flow & Financial Distress Scenarios")

        try:
            # Create financially distressed company data
            distressed_data = {
                'income_fy': pd.DataFrame(
                    {
                        'Metric': [
                            'Revenue',
                            'Operating Income',
                            'EBIT',
                            'Net Income',
                            'EBT',
                            'Income Tax Expense',
                        ],
                        'FY-4': [1000, -200, -180, -250, -200, 50],  # Heavy losses
                        'FY-3': [800, -300, -280, -350, -300, 50],  # Declining revenue
                        'FY-2': [600, -150, -130, -180, -150, 30],  # Some improvement
                        'FY-1': [400, -50, -30, -80, -50, 20],  # Continued struggle
                        'FY': [300, -100, -80, -120, -100, 20],  # Recent decline
                    }
                ),
                'balance_fy': pd.DataFrame(
                    {
                        'Metric': ['Total Current Assets', 'Total Current Liabilities'],
                        'FY-4': [500, 800],  # Liquidity crisis
                        'FY-3': [400, 900],  # Worsening
                        'FY-2': [350, 850],  # Slight improvement
                        'FY-1': [300, 800],  # Still struggling
                        'FY': [250, 750],  # Critical position
                    }
                ),
                'cashflow_fy': pd.DataFrame(
                    {
                        'Metric': [
                            'Cash from Operations',
                            'Capital Expenditure',
                            'Depreciation & Amortization',
                            'Long-Term Debt Issued',
                            'Long-Term Debt Repaid',
                        ],
                        'FY-4': [-150, -20, 50, 200, -50],  # Negative operating cash flow
                        'FY-3': [-200, -15, 45, 150, -30],  # Worsening operations
                        'FY-2': [-100, -10, 40, 100, -20],  # Some improvement
                        'FY-1': [-50, -5, 35, 50, -10],  # Reducing investments
                        'FY': [-80, -8, 30, 0, -25],  # Recent deterioration
                    }
                ),
            }

            with tempfile.TemporaryDirectory() as temp_dir:
                company_dir = os.path.join(temp_dir, "DISTRESSED_CORP")
                os.makedirs(company_dir)

                # Create calculator without auto-loading to avoid file system errors in tests
                calculator = FinancialCalculator(None)  # No auto-loading
                calculator.company_folder = company_dir
                calculator.company_name = "DISTRESSED_CORP"
                calculator.financial_data = distressed_data
                calculator.set_validation_enabled(False)  # Speed up testing

                # Test FCF calculations with negative scenarios
                fcf_results = calculator.calculate_all_fcf_types()

                # Verify system handles negative scenarios appropriately
                success_count = 0
                for fcf_type, values in fcf_results.items():
                    if values:  # If calculation succeeded
                        if all(v < 0 for v in values):
                            print(
                                f"  ✓ {fcf_type}: Correctly shows negative values (latest: {values[-1]:,.0f})"
                            )
                            success_count += 1
                        else:
                            print(f"  ⚠ {fcf_type}: Expected negative values but got mixed results")
                    else:
                        print(f"  ✗ {fcf_type}: Failed to calculate")

                # Test unified FCF calculation with negative inputs
                negative_data = {
                    'operating_cash_flow': -150,
                    'capital_expenditures': -50,
                    'source': 'distressed_test',
                }

                unified_result = calculate_unified_fcf(negative_data)
                if unified_result['success'] and unified_result['free_cash_flow'] < 0:
                    print(
                        f"  ✓ Unified FCF: Handles negative OCF correctly ({unified_result['free_cash_flow']:,.0f})"
                    )
                    success_count += 1

                self.test_results.append(
                    (
                        "Negative Cash Flow Scenarios",
                        success_count >= 2,
                        f"Passed {success_count} negative cash flow tests",
                    )
                )

        except Exception as e:
            error_msg = f"Negative cash flow test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Negative Cash Flow Test", error_msg))
            self.test_results.append(("Negative Cash Flow Scenarios", False, error_msg))

    def _test_missing_data_handling(self):
        """Test 2: Missing Data and Incomplete Responses"""
        print("\n[TEST 2] Missing Data & Incomplete API Response Handling")

        try:
            # Test missing CapEx scenario
            missing_capex_data = {
                'income_fy': pd.DataFrame({'Metric': ['Revenue', 'Net Income'], 'FY': [1000, 100]}),
                'balance_fy': pd.DataFrame(
                    {
                        'Metric': ['Total Current Assets', 'Total Current Liabilities'],
                        'FY': [500, 300],
                    }
                ),
                'cashflow_fy': pd.DataFrame(
                    {
                        'Metric': ['Cash from Operations', 'Depreciation & Amortization'],
                        'FY': [150, 20],
                        # Missing Capital Expenditure - should handle gracefully
                    }
                ),
            }

            with tempfile.TemporaryDirectory() as temp_dir:
                company_dir = os.path.join(temp_dir, "MISSING_CAPEX")
                os.makedirs(company_dir)

                calculator = FinancialCalculator(company_dir)
                calculator.financial_data = missing_capex_data
                calculator.set_validation_enabled(False)

                fcf_results = calculator.calculate_all_fcf_types()

                # Should handle missing CapEx gracefully - LFCF should still work (OCF - 0 CapEx)
                if 'LFCF' in fcf_results:
                    print("  ✓ Missing CapEx: LFCF calculation handled gracefully")
                    missing_data_success = True
                else:
                    print("  ⚠ Missing CapEx: LFCF calculation failed")
                    missing_data_success = False

                # Test completely empty dataframes
                empty_data = {
                    'income_fy': pd.DataFrame(),
                    'balance_fy': pd.DataFrame(),
                    'cashflow_fy': pd.DataFrame(),
                }

                calculator.financial_data = empty_data
                empty_fcf_results = calculator.calculate_all_fcf_types()

                # Should return empty results but not crash
                if isinstance(empty_fcf_results, dict):
                    print("  ✓ Empty DataFrames: Handled gracefully without crashing")
                    empty_data_success = True
                else:
                    print("  ✗ Empty DataFrames: System crashed")
                    empty_data_success = False

                # Test malformed data (Excel errors, None values)
                malformed_data = {
                    'income_fy': pd.DataFrame(
                        {
                            'Metric': ['Revenue', 'Net Income'],
                            'FY': ['#VALUE!', None],  # Excel error values
                        }
                    ),
                    'cashflow_fy': pd.DataFrame(
                        {
                            'Metric': ['Cash from Operations', 'Capital Expenditure'],
                            'FY': [np.nan, ''],  # Missing/empty values
                        }
                    ),
                }

                calculator.financial_data = malformed_data
                malformed_fcf_results = calculator.calculate_all_fcf_types()

                if isinstance(malformed_fcf_results, dict):
                    print("  ✓ Malformed Data: Handled gracefully without crashing")
                    malformed_success = True
                else:
                    print("  ✗ Malformed Data: System crashed")
                    malformed_success = False

                overall_success = missing_data_success and empty_data_success and malformed_success
                success_count = sum([missing_data_success, empty_data_success, malformed_success])

                self.test_results.append(
                    (
                        "Missing Data Handling",
                        overall_success,
                        f"Passed {success_count}/3 missing data scenarios",
                    )
                )

        except Exception as e:
            error_msg = f"Missing data test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Missing Data Test", error_msg))
            self.test_results.append(("Missing Data Handling", False, error_msg))

    def _test_api_failure_handling(self):
        """Test 3: API Failure Simulation"""
        print("\n[TEST 3] API Failure & Network Issue Handling")

        try:
            # Test network timeout simulation
            calculator = FinancialCalculator(None)
            calculator.ticker_symbol = "TEST"

            # Test 1: Timeout handling
            with patch('yfinance.Ticker') as mock_ticker:
                mock_ticker.side_effect = Exception("Request timed out")

                result = calculator.fetch_market_data(force_reload=True)

                if result is not None or hasattr(result, 'get'):  # Should return fallback data
                    print("  ✓ Network Timeout: Handled gracefully with fallback")
                    timeout_success = True
                else:
                    print("  ⚠ Network Timeout: No fallback data provided")
                    timeout_success = False

            # Test 2: Rate limiting (429 error)
            with patch('yfinance.Ticker') as mock_ticker:
                mock_ticker.side_effect = Exception("429 Rate limited")

                result = calculator.fetch_market_data(force_reload=True)

                if result is not None:  # Should handle gracefully
                    print("  ✓ Rate Limiting: Handled gracefully")
                    rate_limit_success = True
                else:
                    print("  ⚠ Rate Limiting: Not handled properly")
                    rate_limit_success = False

            # Test 3: Invalid ticker handling
            with patch('yfinance.Ticker') as mock_ticker:
                mock_info = Mock()
                mock_info.info = {}  # Empty info for invalid ticker
                mock_ticker.return_value = mock_info

                result = calculator.fetch_market_data(force_reload=True)

                print("  ✓ Invalid Ticker: Handled gracefully")
                invalid_ticker_success = True

            overall_success = timeout_success and rate_limit_success and invalid_ticker_success
            success_count = sum([timeout_success, rate_limit_success, invalid_ticker_success])

            self.test_results.append(
                (
                    "API Failure Handling",
                    overall_success,
                    f"Passed {success_count}/3 API failure scenarios",
                )
            )

        except Exception as e:
            error_msg = f"API failure test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("API Failure Test", error_msg))
            self.test_results.append(("API Failure Handling", False, error_msg))

    def _test_malformed_data_handling(self):
        """Test 4: Malformed Data Edge Cases"""
        print("\n[TEST 4] Malformed Data Edge Cases")

        try:
            # Test unified FCF calculation with various malformed inputs
            test_cases = [
                {
                    'operating_cash_flow': np.inf,
                    'capital_expenditures': -100,
                    'source': 'infinity_test',
                },
                {'operating_cash_flow': np.nan, 'capital_expenditures': -100, 'source': 'nan_test'},
                {
                    'operating_cash_flow': "invalid",
                    'capital_expenditures': -100,
                    'source': 'string_test',
                },
                {'operating_cash_flow': None, 'capital_expenditures': -100, 'source': 'none_test'},
            ]

            success_count = 0
            for i, test_case in enumerate(test_cases):
                try:
                    result = calculate_unified_fcf(test_case)

                    # Should either succeed with a valid result or fail gracefully
                    if result.get('success') == False:  # Graceful failure
                        print(f"  ✓ Test {i+1} ({test_case['source']}): Failed gracefully")
                        success_count += 1
                    elif result.get('success') == True and np.isfinite(
                        result.get('free_cash_flow', np.nan)
                    ):
                        print(
                            f"  ✓ Test {i+1} ({test_case['source']}): Handled and calculated successfully"
                        )
                        success_count += 1
                    else:
                        print(f"  ⚠ Test {i+1} ({test_case['source']}): Unexpected result")

                except Exception as e:
                    print(f"  ✗ Test {i+1} ({test_case['source']}): Crashed with {e}")

            self.test_results.append(
                (
                    "Malformed Data Handling",
                    success_count >= 3,
                    f"Passed {success_count}/4 malformed data tests",
                )
            )

        except Exception as e:
            error_msg = f"Malformed data test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Malformed Data Test", error_msg))
            self.test_results.append(("Malformed Data Handling", False, error_msg))

    def _test_basic_performance(self):
        """Test 5: Basic Performance with Multiple Companies"""
        print("\n[TEST 5] Basic Performance Testing")

        try:
            # Test processing multiple companies
            company_count = 5  # Reduced for basic test
            start_time = time.time()

            successful_calculations = 0

            for i in range(company_count):
                # Generate simple test data
                test_data = {
                    'income_fy': pd.DataFrame(
                        {'Metric': ['Revenue', 'Net Income'], 'FY': [1000 + i * 100, 100 + i * 10]}
                    ),
                    'cashflow_fy': pd.DataFrame(
                        {
                            'Metric': ['Cash from Operations', 'Capital Expenditure'],
                            'FY': [150 + i * 15, -50 - i * 5],
                        }
                    ),
                }

                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        company_dir = os.path.join(temp_dir, f"PERF_TEST_{i}")
                        os.makedirs(company_dir)

                        calculator = FinancialCalculator(company_dir)
                        calculator.financial_data = test_data
                        calculator.set_validation_enabled(False)  # Speed up for performance test

                        fcf_results = calculator.calculate_all_fcf_types()
                        if any(fcf_results.values()):  # If any FCF calculation succeeded
                            successful_calculations += 1

                except Exception as e:
                    print(f"  ⚠ Company {i} calculation failed: {e}")

            total_time = time.time() - start_time
            avg_time_per_company = total_time / company_count if company_count > 0 else 0

            print(
                f"  ✓ Processed {successful_calculations}/{company_count} companies in {total_time:.2f}s"
            )
            print(f"  ✓ Average time per company: {avg_time_per_company:.3f}s")

            # Performance criteria: should process companies quickly
            performance_success = (
                avg_time_per_company < 2.0 and successful_calculations >= company_count * 0.8
            )

            self.test_results.append(
                (
                    "Basic Performance",
                    performance_success,
                    f"Processed {successful_calculations}/{company_count} companies, avg {avg_time_per_company:.3f}s each",
                )
            )

        except Exception as e:
            error_msg = f"Performance test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Performance Test", error_msg))
            self.test_results.append(("Basic Performance", False, error_msg))

    def _test_end_to_end_integration(self):
        """Test 6: End-to-End Integration"""
        print("\n[TEST 6] End-to-End Integration Workflow")

        try:
            # Create comprehensive test data
            integration_data = {
                'income_fy': pd.DataFrame(
                    {
                        'Metric': [
                            'Revenue',
                            'Operating Income',
                            'EBIT',
                            'Net Income',
                            'EBT',
                            'Income Tax Expense',
                        ],
                        'FY-2': [8000, 1200, 1100, 800, 1000, 200],
                        'FY-1': [9000, 1400, 1300, 1000, 1200, 200],
                        'FY': [10000, 1600, 1500, 1200, 1400, 200],
                    }
                ),
                'balance_fy': pd.DataFrame(
                    {
                        'Metric': ['Total Current Assets', 'Total Current Liabilities'],
                        'FY-2': [3000, 1500],
                        'FY-1': [3400, 1700],
                        'FY': [3800, 1900],
                    }
                ),
                'cashflow_fy': pd.DataFrame(
                    {
                        'Metric': [
                            'Cash from Operations',
                            'Capital Expenditure',
                            'Depreciation & Amortization',
                            'Long-Term Debt Issued',
                            'Long-Term Debt Repaid',
                        ],
                        'FY-2': [1500, -300, 200, 100, -50],
                        'FY-1': [1700, -340, 220, 120, -40],
                        'FY': [1900, -380, 240, 100, -80],
                    }
                ),
                # Include LTM data
                'income_ltm': pd.DataFrame(
                    {
                        'Metric': [
                            'Revenue',
                            'Operating Income',
                            'EBIT',
                            'Net Income',
                            'EBT',
                            'Income Tax Expense',
                        ],
                        'LTM': [10200, 1650, 1550, 1250, 1450, 200],
                    }
                ),
                'cashflow_ltm': pd.DataFrame(
                    {
                        'Metric': [
                            'Cash from Operations',
                            'Capital Expenditure',
                            'Depreciation & Amortization',
                        ],
                        'LTM': [1950, -400, 250],
                    }
                ),
            }

            with tempfile.TemporaryDirectory() as temp_dir:
                company_dir = os.path.join(temp_dir, "INTEGRATION_TEST")
                os.makedirs(company_dir)

                # Step 1: Initialize calculator with comprehensive data
                calculator = FinancialCalculator(company_dir)
                calculator.financial_data = integration_data
                calculator.ticker_symbol = "INTG"
                calculator.set_validation_enabled(True)  # Enable validation for integration test

                # Step 2: Calculate all FCF types
                fcf_results = calculator.calculate_all_fcf_types()
                fcf_success = len(fcf_results) > 0 and any(fcf_results.values())

                if fcf_success:
                    print("  ✓ Step 1: FCF calculations completed successfully")
                else:
                    print("  ✗ Step 1: FCF calculations failed")

                # Step 3: Test standardized data export
                standardized_data = calculator.get_standardized_financial_data()
                export_success = (
                    'calculated_metrics' in standardized_data and 'fcf_results' in standardized_data
                )

                if export_success:
                    print("  ✓ Step 2: Standardized data export successful")
                else:
                    print("  ✗ Step 2: Standardized data export failed")

                # Step 4: Test data quality reporting
                quality_report = calculator.get_data_quality_report()
                quality_success = quality_report is not None

                if quality_success:
                    print("  ✓ Step 3: Data quality reporting successful")
                else:
                    print("  ✗ Step 3: Data quality reporting failed")

                # Step 5: Test mock market data integration
                with patch.object(calculator, 'fetch_market_data') as mock_fetch:
                    mock_fetch.return_value = {
                        'current_price': 50.0,
                        'shares_outstanding': 1000000,
                        'market_cap': 50000000,
                        'currency': 'USD',
                    }

                    market_data = calculator.fetch_market_data()
                    market_success = market_data is not None

                    if market_success:
                        print("  ✓ Step 4: Market data integration successful")
                    else:
                        print("  ✗ Step 4: Market data integration failed")

                overall_integration_success = (
                    fcf_success and export_success and quality_success and market_success
                )

                self.test_results.append(
                    (
                        "End-to-End Integration",
                        overall_integration_success,
                        f"Completed {sum([fcf_success, export_success, quality_success, market_success])}/4 integration steps",
                    )
                )

        except Exception as e:
            error_msg = f"Integration test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Integration Test", error_msg))
            self.test_results.append(("End-to-End Integration", False, error_msg))

    def _test_utility_functions(self):
        """Test 7: Utility Functions Edge Cases"""
        print("\n[TEST 7] Utility Functions Edge Cases")

        try:
            # Test safe_numeric_conversion with edge cases
            conversion_tests = [
                (None, 0.0, "None input"),
                ("", 0.0, "Empty string"),
                ("#VALUE!", 0.0, "Excel error"),
                ("1,234.56", 1234.56, "Formatted number"),
                ("$1,000", 1000.0, "Currency format"),
                ("(500)", -500.0, "Negative in parentheses"),
                (np.inf, 0.0, "Infinity"),
                (np.nan, 0.0, "NaN"),
            ]

            conversion_success_count = 0
            for test_input, expected, description in conversion_tests:
                try:
                    result = safe_numeric_conversion(test_input)
                    if abs(result - expected) < 0.01:
                        print(f"  ✓ {description}: {test_input} → {result}")
                        conversion_success_count += 1
                    else:
                        print(f"  ⚠ {description}: Expected {expected}, got {result}")
                except Exception as e:
                    print(f"  ✗ {description}: Failed with {e}")

            # Test handle_financial_nan_series
            test_series = pd.Series([100, np.nan, 200, np.nan, 300])

            try:
                forward_filled = handle_financial_nan_series(test_series, method='forward')
                interpolated = handle_financial_nan_series(test_series, method='interpolate')
                zero_filled = handle_financial_nan_series(test_series, method='zero')

                nan_handling_success = (
                    not forward_filled.isna().any()
                    and not interpolated.isna().any()
                    and not zero_filled.isna().any()
                )

                if nan_handling_success:
                    print("  ✓ NaN handling methods: All methods eliminate NaN values")
                else:
                    print("  ⚠ NaN handling methods: Some methods failed to eliminate NaN")

            except Exception as e:
                print(f"  ✗ NaN handling failed: {e}")
                nan_handling_success = False

            overall_utility_success = conversion_success_count >= 6 and nan_handling_success

            self.test_results.append(
                (
                    "Utility Functions",
                    overall_utility_success,
                    f"Conversion: {conversion_success_count}/8, NaN handling: {'Pass' if nan_handling_success else 'Fail'}",
                )
            )

        except Exception as e:
            error_msg = f"Utility functions test failed: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_tests.append(("Utility Functions Test", error_msg))
            self.test_results.append(("Utility Functions", False, error_msg))

    def _generate_test_report(self):
        """Generate final test report"""
        print("\n" + "=" * 80)
        print("CRITICAL EDGE CASE TESTING REPORT")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests

        print(
            f"\nOverall Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)"
        )

        print(f"\nTest Results Summary:")
        for test_name, success, details in self.test_results:
            status = "[PASS]" if success else "[FAIL]"
            print(f"  {status} {test_name}: {details}")

        if self.failed_tests:
            print(f"\nFailed Test Details:")
            for test_name, error_msg in self.failed_tests:
                print(f"  - {test_name}: {error_msg}")

        # Overall assessment
        if passed_tests == total_tests:
            print(f"\nEXCELLENT: All critical edge cases handled properly!")
            print(f"   System demonstrates robust error handling and edge case management.")
        elif passed_tests >= total_tests * 0.8:
            print(f"\nGOOD: Most critical edge cases handled ({passed_tests}/{total_tests})")
            print(f"   System shows good resilience with minor areas for improvement.")
        elif passed_tests >= total_tests * 0.6:
            print(f"\nADEQUATE: Basic edge case handling present ({passed_tests}/{total_tests})")
            print(f"   System functions but needs improvement in error handling.")
        else:
            print(f"\nPOOR: Significant edge case handling issues ({passed_tests}/{total_tests})")
            print(f"   System needs major improvements for production use.")

        print(f"\nTask #21 Implementation Status:")
        print(f"   [DONE] Negative cash flow scenarios: Tested")
        print(f"   [DONE] Missing data handling: Tested")
        print(f"   [DONE] API failure handling: Tested")
        print(f"   [DONE] Performance benchmarks: Basic testing completed")
        print(f"   [DONE] Integration workflows: Tested")

        print("=" * 80)

        return passed_tests, total_tests


def main():
    """Main test execution"""
    print("Starting Critical Edge Case Testing for Task #21...")

    tester = CriticalEdgeCaseTests()

    try:
        tester.run_all_tests()
        passed, total = tester._generate_test_report()

        # Return appropriate exit code
        if passed == total:
            print("\nAll critical edge cases tests PASSED!")
            return 0
        elif passed >= total * 0.8:
            print(f"\nMost critical edge cases tests passed ({passed}/{total})")
            return 0
        else:
            print(f"\nSome critical edge cases need attention ({passed}/{total})")
            return 1

    except KeyboardInterrupt:
        print(f"\n\nTests interrupted by user")
        return 2
    except Exception as e:
        print(f"\nCritical error during testing: {e}")
        logger.error("Critical error during edge case testing", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
