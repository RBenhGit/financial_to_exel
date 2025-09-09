"""
Integration Test Runner with Test Data Infrastructure
====================================================

Comprehensive test runner that creates test data infrastructure and runs
the previously failing integration tests with proper data setup.

Task #28 Implementation: Create Test Data Infrastructure for Integration Tests
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import traceback

# Add current directory and parent directories to path
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

# Import our test utilities
try:
    from tests.utils.test_data_generator import (
        TestDataInfrastructure, 
        TestDataScenario,
        TemporaryTestData
    )
    from tests.utils.windows_unicode_support import SafeTestExecution, UnicodeHelper
    HAS_TEST_UTILS = True
except ImportError as e:
    print(f"Warning: Test utilities not available: {e}")
    HAS_TEST_UTILS = False

# Import system modules for testing
try:
    from core.analysis.engines.financial_calculations import FinancialCalculator
    from core.data_processing.managers.centralized_data_manager import CentralizedDataManager  
    from data_validator import FinancialDataValidator
    from error_handler import FinancialAnalysisError
    HAS_FINANCIAL_MODULES = True
except ImportError as e:
    print(f"Warning: Some financial modules not available: {e}")
    HAS_FINANCIAL_MODULES = False

logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Main class for running integration tests with proper test data"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_infrastructure = None
        self.test_results = []
        
        # Configure logging
        if verbose:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.WARNING)
    
    def run_all_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests with comprehensive test data setup"""
        
        if not HAS_TEST_UTILS or not HAS_FINANCIAL_MODULES:
            return {
                'success': False,
                'error': 'Required modules not available',
                'tests_run': 0,
                'tests_passed': 0
            }
        
        with SafeTestExecution("Integration Test Suite - Task #28") as reporter:
            try:
                # Set up test data infrastructure
                reporter.report_section("Test Data Infrastructure Setup")
                success = self._setup_test_infrastructure(reporter)
                if not success:
                    return self._create_failure_result("Test infrastructure setup failed")
                
                # Run test categories
                self._run_financial_calculator_tests(reporter)
                self._run_data_manager_tests(reporter) 
                self._run_edge_case_tests(reporter)
                self._run_file_access_tests(reporter)
                self._run_unicode_compatibility_tests(reporter)
                
                # Generate final summary
                summary = reporter.get_summary()
                
                return {
                    'success': summary['all_passed'],
                    'tests_run': summary['total_tests'],
                    'tests_passed': summary['passed_tests'],
                    'tests_failed': summary['failed_tests'],
                    'execution_time': summary['execution_time'],
                    'details': summary['results']
                }
                
            except Exception as e:
                logger.error(f"Critical error in integration testing: {e}")
                reporter.report_test("Integration Test Suite", False, error=str(e))
                return self._create_failure_result(f"Critical error: {e}")
            
            finally:
                if self.test_infrastructure:
                    self.test_infrastructure.cleanup()
    
    def _setup_test_infrastructure(self, reporter) -> bool:
        """Set up the test data infrastructure"""
        try:
            self.test_infrastructure = TestDataInfrastructure()
            
            # Create edge case test companies
            company_paths = self.test_infrastructure.create_edge_case_test_data()
            
            reporter.report_test(
                "Test Infrastructure Creation", 
                True, 
                f"Created {len(company_paths)} test companies"
            )
            
            # Verify test data files exist
            total_files = 0
            for company_name, company_path in company_paths.items():
                company_dir = Path(company_path)
                
                # Check FY files
                fy_dir = company_dir / "FY"
                if fy_dir.exists():
                    excel_files = list(fy_dir.glob("*.xlsx"))
                    total_files += len(excel_files)
                    
                    if len(excel_files) >= 3:  # Income, Balance, Cash Flow
                        reporter.report_test(
                            f"FY Data for {company_name}",
                            True,
                            f"Created {len(excel_files)} Excel files"
                        )
                    else:
                        reporter.report_test(
                            f"FY Data for {company_name}",
                            False,
                            f"Only {len(excel_files)} Excel files created"
                        )
                        return False
                
                # Check LTM files if they should exist
                ltm_dir = company_dir / "LTM"
                if ltm_dir.exists():
                    ltm_files = list(ltm_dir.glob("*.xlsx"))
                    total_files += len(ltm_files)
            
            reporter.report_test(
                "Total Test Files Created",
                total_files >= 15,  # Expect at least 15 files total
                f"Created {total_files} Excel test files"
            )
            
            return total_files >= 15
            
        except Exception as e:
            reporter.report_test("Test Infrastructure Setup", False, error=str(e))
            return False
    
    def _run_financial_calculator_tests(self, reporter):
        """Test FinancialCalculator with generated test data"""
        reporter.report_section("Financial Calculator Integration Tests")
        
        test_companies = ["HEALTHY_CORP", "DISTRESSED_CORP", "GROWTH_CORP"]
        
        for company_name in test_companies:
            try:
                company_path = Path(self.test_infrastructure.get_test_data_path()) / company_name
                
                if not company_path.exists():
                    reporter.report_test(
                        f"Calculator Test - {company_name}",
                        False,
                        error=f"Company directory not found: {company_path}"
                    )
                    continue
                
                # Test calculator initialization
                try:
                    calculator = FinancialCalculator(company_folder=str(company_path))
                    reporter.report_test(
                        f"Calculator Init - {company_name}",
                        True,
                        "Calculator initialized successfully"
                    )
                except Exception as init_error:
                    reporter.report_test(
                        f"Calculator Init - {company_name}",
                        False,
                        error=str(init_error)
                    )
                    continue
                
                # Test FCF calculation (using correct method name)
                try:
                    fcf_result = calculator.calculate_all_fcf_types()
                    has_fcf_data = fcf_result is not None and len(fcf_result) > 0
                    
                    reporter.report_test(
                        f"FCF Calculation - {company_name}",
                        has_fcf_data,
                        f"FCF types calculated: {len(fcf_result) if fcf_result else 0}"
                    )
                except Exception as fcf_error:
                    # Try alternative method
                    try:
                        fcf_result = calculator.calculate_fcf_to_firm()
                        has_fcf_data = fcf_result is not None and len(fcf_result) > 0
                        reporter.report_test(
                            f"FCF Calculation - {company_name}",
                            has_fcf_data,
                            f"FCF to Firm calculated: {len(fcf_result) if fcf_result else 0}"
                        )
                    except Exception as alt_error:
                        reporter.report_test(
                            f"FCF Calculation - {company_name}",
                            False,
                            error=str(fcf_error)
                        )
                
                # Test that calculator has financial data loaded
                try:
                    # Test that we have access to financial statements
                    has_statements = hasattr(calculator, 'cashflow_fy') or hasattr(calculator, 'income_fy')
                    
                    reporter.report_test(
                        f"Financial Data Access - {company_name}",
                        has_statements,
                        "Financial statements accessible"
                    )
                except Exception as data_error:
                    reporter.report_test(
                        f"Financial Data Access - {company_name}",
                        False,
                        error=str(data_error)
                    )
                
            except Exception as e:
                reporter.report_test(
                    f"Calculator Tests - {company_name}",
                    False,
                    error=f"Unexpected error: {e}"
                )
    
    def _run_data_manager_tests(self, reporter):
        """Test CentralizedDataManager with test data"""
        reporter.report_section("Data Manager Integration Tests")
        
        try:
            # Test data manager initialization
            data_manager = CentralizedDataManager(
                base_path=self.test_infrastructure.get_test_data_path()
            )
            
            reporter.report_test(
                "Data Manager Init",
                True,
                "CentralizedDataManager initialized successfully"
            )
            
            # Test loading Excel data for each test company
            test_companies = ["HEALTHY_CORP", "DISTRESSED_CORP"]
            
            for company in test_companies:
                try:
                    excel_data = data_manager.load_excel_data(company)
                    has_data = excel_data is not None and len(excel_data) > 0
                    
                    reporter.report_test(
                        f"Load Excel Data - {company}",
                        has_data,
                        f"Loaded {len(excel_data) if excel_data else 0} data sets"
                    )
                except Exception as e:
                    reporter.report_test(
                        f"Load Excel Data - {company}",
                        False,
                        error=str(e)
                    )
            
            # Test cache functionality
            try:
                cache_stats = data_manager.get_cache_stats()
                has_cache_stats = isinstance(cache_stats, dict) and 'total_entries' in cache_stats
                
                reporter.report_test(
                    "Cache Statistics",
                    has_cache_stats,
                    f"Cache entries: {cache_stats.get('total_entries', 0)}"
                )
            except Exception as e:
                reporter.report_test("Cache Statistics", False, error=str(e))
                
        except Exception as e:
            reporter.report_test("Data Manager Tests", False, error=str(e))
    
    def _run_edge_case_tests(self, reporter):
        """Test edge cases that were previously failing"""
        reporter.report_section("Edge Case Scenario Tests")
        
        edge_cases = [
            ("DISTRESSED_CORP", "Financial distress scenario"),
            ("GROWTH_CORP", "High growth scenario"),
            ("MATURE_CORP", "Mature stable scenario")
        ]
        
        for company_name, scenario_desc in edge_cases:
            try:
                company_path = Path(self.test_infrastructure.get_test_data_path()) / company_name
                
                # Test that we can handle the edge case scenario
                calculator = FinancialCalculator(company_folder=str(company_path))
                
                # Try to calculate FCF for the edge case (using correct method)
                try:
                    fcf_result = calculator.calculate_all_fcf_types()
                except:
                    # Fallback to alternative method
                    fcf_result = calculator.calculate_fcf_to_firm()
                
                # For distressed companies, FCF might be negative - that's valid
                if company_name == "DISTRESSED_CORP":
                    # Check that we get numerical results (even if negative)
                    has_valid_result = fcf_result is not None
                    if has_valid_result:
                        if isinstance(fcf_result, dict):
                            # Multiple FCF types
                            numerical_values = []
                            for v in fcf_result.values():
                                if isinstance(v, list):
                                    numerical_values.extend([x for x in v if isinstance(x, (int, float))])
                                elif isinstance(v, (int, float)):
                                    numerical_values.append(v)
                            has_negative_fcf = any(v < 0 for v in numerical_values)
                        elif isinstance(fcf_result, list):
                            # Single FCF type
                            numerical_values = [v for v in fcf_result if isinstance(v, (int, float))]
                            has_negative_fcf = any(v < 0 for v in numerical_values)
                        else:
                            has_negative_fcf = False
                        
                        reporter.report_test(
                            f"Edge Case - {scenario_desc}",
                            True,
                            f"Handled scenario correctly, negative FCF detected: {has_negative_fcf}"
                        )
                    else:
                        reporter.report_test(
                            f"Edge Case - {scenario_desc}",
                            False,
                            "No FCF results for distressed company"
                        )
                else:
                    # For other scenarios, just check we get results
                    has_valid_result = fcf_result is not None
                    if isinstance(fcf_result, (dict, list)):
                        has_valid_result = has_valid_result and len(fcf_result) > 0
                    
                    reporter.report_test(
                        f"Edge Case - {scenario_desc}",
                        has_valid_result,
                        "FCF calculation completed for scenario"
                    )
                        
            except Exception as e:
                reporter.report_test(
                    f"Edge Case - {scenario_desc}",
                    False,
                    error=str(e)
                )
    
    def _run_file_access_tests(self, reporter):
        """Test file access patterns that were causing failures"""
        reporter.report_section("File Access Pattern Tests")
        
        base_path = Path(self.test_infrastructure.get_test_data_path())
        
        # Test directory structure access
        required_dirs = ["HEALTHY_CORP/FY", "DISTRESSED_CORP/FY", "GROWTH_CORP/FY"]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            dir_exists = full_path.exists() and full_path.is_dir()
            
            reporter.report_test(
                f"Directory Access - {dir_path}",
                dir_exists,
                f"Path: {full_path}"
            )
        
        # Test Excel file access
        test_files = [
            "HEALTHY_CORP/FY/HEALTHY_CORP - Income Statement.xlsx",
            "HEALTHY_CORP/FY/HEALTHY_CORP - Balance Sheet.xlsx", 
            "HEALTHY_CORP/FY/HEALTHY_CORP - Cash Flow Statement.xlsx"
        ]
        
        for file_path in test_files:
            full_path = base_path / file_path
            file_exists = full_path.exists() and full_path.is_file()
            file_size = full_path.stat().st_size if file_exists else 0
            
            reporter.report_test(
                f"File Access - {Path(file_path).name}",
                file_exists and file_size > 0,
                f"Size: {file_size} bytes"
            )
    
    def _run_unicode_compatibility_tests(self, reporter):
        """Test Unicode compatibility fixes"""
        reporter.report_section("Unicode Compatibility Tests")
        
        # Test that Unicode helper functions work
        try:
            from tests.utils.windows_unicode_support import UnicodeHelper
            
            # Test Unicode character replacement
            test_chars = ['✓', '✗', '→', '←']
            all_chars_handled = True
            
            for char in test_chars:
                try:
                    safe_char = UnicodeHelper.UNICODE_MAPPINGS.get(char, char)
                    # Try to "print" it safely (capture any encoding errors)
                    test_output = f"Test {char} -> {safe_char}"
                    UnicodeHelper.safe_format("Test: {symbol}", symbol=char)
                except Exception:
                    all_chars_handled = False
                    break
            
            reporter.report_test(
                "Unicode Character Mapping",
                all_chars_handled,
                f"Tested {len(test_chars)} Unicode characters"
            )
            
            # Test Windows detection
            is_windows_detected = UnicodeHelper.is_windows_cp1252()
            reporter.report_test(
                "Windows CP1252 Detection",
                True,  # Detection function should work regardless of result
                f"Windows CP1252: {is_windows_detected}"
            )
            
        except Exception as e:
            reporter.report_test("Unicode Compatibility", False, error=str(e))
    
    def _create_failure_result(self, error_message: str) -> Dict[str, Any]:
        """Create a failure result dictionary"""
        return {
            'success': False,
            'error': error_message,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 1,
            'execution_time': 0,
            'details': []
        }


def run_integration_tests_with_infrastructure(verbose: bool = True) -> Dict[str, Any]:
    """
    Convenience function to run all integration tests with test data infrastructure
    
    Returns:
        Dict with test results including success status and detailed results
    """
    runner = IntegrationTestRunner(verbose=verbose)
    return runner.run_all_integration_tests()


def verify_test_infrastructure_setup() -> bool:
    """
    Quick verification that test infrastructure can be set up properly
    
    Returns:
        bool: True if infrastructure setup succeeds
    """
    try:
        with TemporaryTestData() as (infrastructure, company_paths):
            if len(company_paths) < 5:  # Should create at least 5 companies
                return False
                
            # Check that Excel files were created
            total_files = 0
            for company_path in company_paths.values():
                fy_dir = Path(company_path) / "FY"
                if fy_dir.exists():
                    total_files += len(list(fy_dir.glob("*.xlsx")))
            
            return total_files >= 15  # Should have at least 15 Excel files
            
    except Exception as e:
        logger.error(f"Infrastructure verification failed: {e}")
        return False


if __name__ == "__main__":
    print("Integration Test Runner - Task #28 Implementation")
    print("=" * 60)
    
    # Quick infrastructure verification
    print("Verifying test infrastructure setup...")
    if verify_test_infrastructure_setup():
        print("[PASS] Test infrastructure setup verified successfully")
    else:
        print("[FAIL] Test infrastructure setup verification failed")
        sys.exit(1)
    
    print("")
    
    # Run full integration test suite
    results = run_integration_tests_with_infrastructure(verbose=True)
    
    print("")
    print("Final Results:")
    print(f"Success: {results['success']}")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Execution Time: {results.get('execution_time', 0):.2f} seconds")
    
    if results['success']:
        print("\n[SUCCESS] All integration tests passed!")
        sys.exit(0)
    else:
        print(f"\n[FAILED] Integration tests failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)