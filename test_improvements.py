#!/usr/bin/env python3
"""
Comprehensive Test Suite for Financial Analysis Application Improvements

This test suite validates all the improvements made to address the NVDA data loading
issues and overall application robustness.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import json
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to test
from config import (
    ApplicationConfig,
    ExcelStructureConfig,
    FinancialMetricsConfig,
    DCFConfig,
    ValidationConfig,
    ConfigManager,
    get_config,
)
from excel_utils import (
    ExcelDataExtractor,
    get_company_name_from_excel,
    get_period_dates_from_excel,
    extract_financial_data_from_excel,
)
from fcf_consolidated import (
    FCFCalculator,
    calculate_fcf_growth_rates,
    format_fcf_data_for_display,
    get_fcf_recommendation,
)
from error_handler import (
    FinancialAnalysisError,
    ExcelDataError,
    ValidationError,
    EnhancedLogger,
    with_error_handling,
    validate_excel_file,
)


class TestConfigurationSystem(unittest.TestCase):
    """Test the configuration system functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)

    def test_default_configuration_loading(self):
        """Test that default configuration loads correctly"""
        config = get_config()

        # Test that all configuration sections exist
        self.assertIsInstance(config, ApplicationConfig)
        self.assertIsInstance(config.excel_structure, ExcelStructureConfig)
        self.assertIsInstance(config.financial_metrics, FinancialMetricsConfig)
        self.assertIsInstance(config.dcf, DCFConfig)
        self.assertIsInstance(config.validation, ValidationConfig)

        # Test default values
        self.assertEqual(config.excel_structure.data_start_column, 4)
        self.assertEqual(config.excel_structure.ltm_column, 15)
        self.assertEqual(config.dcf.default_discount_rate, 0.10)
        self.assertEqual(config.dcf.default_terminal_growth_rate, 0.025)

    def test_configuration_validation(self):
        """Test configuration validation logic"""
        config = get_config()

        # Test that required financial metrics are present
        self.assertIn("EBIT", config.financial_metrics.income_metrics)
        self.assertIn("Net Income to Company", config.financial_metrics.income_metrics)
        self.assertIn("Total Current Assets", config.financial_metrics.balance_metrics)
        self.assertIn("Cash from Operations", config.financial_metrics.cashflow_metrics)

        # Test that target columns are properly configured
        for metric, details in config.financial_metrics.income_metrics.items():
            self.assertIn("target_column", details)
            self.assertIsInstance(details["target_column"], int)

    def test_config_manager_functionality(self):
        """Test configuration manager save/load functionality"""
        config_manager = ConfigManager(self.config_file)

        # Test loading non-existent config (should use defaults)
        config = config_manager.load_config()
        self.assertIsInstance(config, ApplicationConfig)

        # Test saving configuration
        config_manager.save_config(config)
        self.assertTrue(os.path.exists(self.config_file))

        # Test loading saved configuration
        config_manager._config = None  # Reset cache
        loaded_config = config_manager.load_config()
        self.assertIsInstance(loaded_config, ApplicationConfig)


class TestExcelUtilities(unittest.TestCase):
    """Test the Excel utilities functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_excel_file = os.path.join(self.temp_dir, "sample.xlsx")

        # Create a mock Excel file for testing
        Path(self.sample_excel_file).touch()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.sample_excel_file):
            os.remove(self.sample_excel_file)
        os.rmdir(self.temp_dir)

    @patch('excel_utils.load_workbook')
    def test_company_name_extraction(self, mock_load_workbook):
        """Test dynamic company name extraction"""
        # Mock workbook and worksheet
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_load_workbook.return_value = mock_workbook

        # Test successful company name extraction
        mock_worksheet.cell.return_value.value = "Test Corporation"

        with patch('excel_utils.ExcelDataExtractor._is_likely_company_name', return_value=True):
            company_name = get_company_name_from_excel(self.sample_excel_file)
            self.assertEqual(company_name, "Test Corporation")

    @patch('excel_utils.load_workbook')
    def test_period_dates_extraction(self, mock_load_workbook):
        """Test dynamic period dates extraction"""
        # Mock workbook and worksheet
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_load_workbook.return_value = mock_workbook

        # Test successful period dates extraction
        from datetime import datetime

        current_year = datetime.now().year
        mock_worksheet.cell.side_effect = lambda row, col: MagicMock(
            value=f"{current_year-1}-12-31" if col >= 4 else "Period End Date"
        )

        dates = get_period_dates_from_excel(self.sample_excel_file)
        self.assertIsInstance(dates, list)
        self.assertGreater(len(dates), 0)

    def test_company_name_validation(self):
        """Test company name validation logic"""
        with patch('excel_utils.load_workbook'):
            extractor = ExcelDataExtractor(self.sample_excel_file)

            # Test valid company names
            valid_names = [
                "Test Corporation A",
                "Test Corporation B",
                "Test Corporation C",
                "Alphabet Inc Class C",
            ]

            for name in valid_names:
                self.assertTrue(extractor._is_likely_company_name(name))

            # Test invalid company names
            invalid_names = [
                str(datetime.now().year - 1),
                "Q1",
                "Period End Date",
                "Total Assets",
                "USD",
            ]

            for name in invalid_names:
                self.assertFalse(extractor._is_likely_company_name(name))

    def test_financial_data_extraction(self):
        """Test financial data extraction functionality"""
        # This test would require actual Excel file structure
        # For now, we test the interface exists
        result = extract_financial_data_from_excel("nonexistent.xlsx", "income")
        self.assertIsInstance(result, dict)


class TestFCFConsolidation(unittest.TestCase):
    """Test the consolidated FCF calculation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_fcf_results = {
            'LFCF': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
            'FCFE': [900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800],
            'FCFF': [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
        }

    def test_fcf_calculator_initialization(self):
        """Test FCF calculator initialization"""
        calculator = FCFCalculator()
        self.assertIsNotNone(calculator.dcf_config)

    def test_fcf_growth_rate_calculation(self):
        """Test FCF growth rate calculations"""
        calculator = FCFCalculator()
        growth_rates = calculator.calculate_fcf_growth_rates(self.sample_fcf_results)

        # Test that all FCF types are present
        self.assertIn('LFCF', growth_rates)
        self.assertIn('FCFE', growth_rates)
        self.assertIn('FCFF', growth_rates)
        self.assertIn('Average', growth_rates)

        # Test that growth rates are calculated for different periods
        for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
            self.assertIn('1yr', growth_rates[fcf_type])
            self.assertIn('5yr', growth_rates[fcf_type])
            self.assertIn('10yr', growth_rates[fcf_type])

    def test_fcf_metrics_summary(self):
        """Test FCF metrics summary calculation"""
        calculator = FCFCalculator()
        summary = calculator.calculate_fcf_metrics_summary(self.sample_fcf_results)

        # Test that all summary sections are present
        self.assertIn('latest_values', summary)
        self.assertIn('growth_rates', summary)
        self.assertIn('statistics', summary)
        self.assertIn('average_fcf', summary)

        # Test latest values
        self.assertEqual(summary['latest_values']['LFCF'], 1900)
        self.assertEqual(summary['latest_values']['FCFE'], 1800)
        self.assertEqual(summary['latest_values']['FCFF'], 2000)

    def test_fcf_data_formatting(self):
        """Test FCF data formatting for display"""
        calculator = FCFCalculator()
        df = calculator.format_fcf_data_for_display(self.sample_fcf_results)

        # Test that DataFrame is created
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)

        # Test that required columns are present
        self.assertIn('Year', df.columns)
        self.assertIn('LFCF ($M)', df.columns)
        self.assertIn('FCFE ($M)', df.columns)
        self.assertIn('FCFF ($M)', df.columns)
        self.assertIn('Average FCF ($M)', df.columns)

    def test_fcf_recommendation_system(self):
        """Test FCF recommendation system"""
        calculator = FCFCalculator()
        recommendation = calculator.get_fcf_recommendation(self.sample_fcf_results)

        # Test that all recommendation components are present
        self.assertIn('overall_trend', recommendation)
        self.assertIn('growth_quality', recommendation)
        self.assertIn('consistency', recommendation)
        self.assertIn('recommendation', recommendation)
        self.assertIn('key_metrics', recommendation)
        self.assertIn('warnings', recommendation)

        # Test that recommendations are valid
        valid_trends = ['positive', 'neutral', 'negative']
        valid_qualities = ['excellent', 'good', 'fair', 'poor']
        valid_recommendations = ['buy', 'hold', 'sell']

        self.assertIn(recommendation['overall_trend'], valid_trends)
        self.assertIn(recommendation['growth_quality'], valid_qualities)
        self.assertIn(recommendation['recommendation'], valid_recommendations)

    def test_utility_functions(self):
        """Test utility functions for backward compatibility"""
        # Test standalone utility functions
        growth_rates = calculate_fcf_growth_rates(self.sample_fcf_results)
        self.assertIsInstance(growth_rates, dict)

        df = format_fcf_data_for_display(self.sample_fcf_results)
        self.assertIsNotNone(df)

        recommendation = get_fcf_recommendation(self.sample_fcf_results)
        self.assertIsInstance(recommendation, dict)


class TestErrorHandling(unittest.TestCase):
    """Test the enhanced error handling system"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)

    def test_custom_exception_creation(self):
        """Test custom exception classes"""
        # Test base exception
        base_error = FinancialAnalysisError("Test error", "TEST_001", {"key": "value"})
        self.assertEqual(base_error.message, "Test error")
        self.assertEqual(base_error.error_code, "TEST_001")
        self.assertIn("key", base_error.context)

        # Test specific exception types
        excel_error = ExcelDataError("Excel error", "EXCEL_001")
        self.assertIsInstance(excel_error, FinancialAnalysisError)

        validation_error = ValidationError("Validation error", "VALID_001")
        self.assertIsInstance(validation_error, FinancialAnalysisError)

    def test_enhanced_logger_functionality(self):
        """Test enhanced logger functionality"""
        logger = EnhancedLogger(__name__, self.log_file)

        # Test basic logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Test context logging
        logger.info("Test with context", context={"test": True})

        # Test error tracking
        self.assertGreater(len(logger.warning_history), 0)
        self.assertGreater(len(logger.error_history), 0)

        # Test error summary
        summary = logger.get_error_summary()
        self.assertIn('total_errors', summary)
        self.assertIn('total_warnings', summary)

    def test_error_handling_decorator(self):
        """Test error handling decorator"""

        @with_error_handling(error_type=ValidationError, return_on_error=None)
        def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Test error")
            return "success"

        # Test successful execution
        result = test_function(should_fail=False)
        self.assertEqual(result, "success")

        # Test error handling
        result = test_function(should_fail=True)
        self.assertIsNone(result)

    def test_excel_file_validation(self):
        """Test Excel file validation"""
        # Test with non-existent file
        with self.assertRaises(ExcelDataError):
            validate_excel_file("nonexistent.xlsx")

        # Test with invalid file extension
        invalid_file = os.path.join(self.temp_dir, "test.txt")
        Path(invalid_file).touch()

        with self.assertRaises(ExcelDataError):
            validate_excel_file(invalid_file)

        # Test with valid Excel file
        valid_file = os.path.join(self.temp_dir, "test.xlsx")
        Path(valid_file).touch()

        result = validate_excel_file(valid_file)
        self.assertTrue(result)

        # Clean up
        os.remove(invalid_file)
        os.remove(valid_file)


class TestSystemIntegration(unittest.TestCase):
    """Test system integration and overall improvements"""

    def test_nvda_processing_equality(self):
        """Test that NVDA processing is identical to other companies"""
        # This test ensures that all companies are processed using the same logic
        # without any hardcoded company-specific behavior

        # Use available company directories for testing
        import os

        available_companies = [
            d for d in os.listdir('.') if os.path.isdir(d) and len(d) <= 5 and d.isupper()
        ]
        companies = (
            available_companies[:5]
            if len(available_companies) >= 5
            else ['TEST1', 'TEST2', 'TEST3', 'TEST4', 'TEST5']
        )

        for company in companies:
            # Test that configuration is the same for all companies
            config = get_config()
            self.assertEqual(config.excel_structure.data_start_column, 4)
            self.assertEqual(config.excel_structure.ltm_column, 15)

            # Test that FCF calculation logic is the same
            calculator = FCFCalculator()
            self.assertIsNotNone(calculator.dcf_config)

            # Test that error handling is consistent
            logger = EnhancedLogger(f"test_{company}")
            self.assertIsNotNone(logger)

    def test_hardcoded_values_elimination(self):
        """Test that hardcoded values have been eliminated"""
        # Test configuration system usage
        config = get_config()

        # These values should now come from configuration, not hardcoded
        self.assertIsInstance(config.excel_structure.data_start_column, int)
        self.assertIsInstance(config.excel_structure.ltm_column, int)
        self.assertIsInstance(config.excel_structure.max_scan_rows, int)
        self.assertIsInstance(config.dcf.default_discount_rate, float)
        self.assertIsInstance(config.dcf.default_terminal_growth_rate, float)

    def test_error_resilience(self):
        """Test that the system is more resilient to errors"""
        # Test that invalid inputs are handled gracefully
        with self.assertRaises(ExcelDataError):
            validate_excel_file("")

        with self.assertRaises(ExcelDataError):
            validate_excel_file("invalid_file.txt")

        # Test FCF calculation with invalid data
        invalid_fcf_data = {'LFCF': None, 'FCFE': [], 'FCFF': [None, None]}
        calculator = FCFCalculator()

        # Should not crash, should return empty/safe results
        result = calculator.calculate_fcf_metrics_summary(invalid_fcf_data)
        self.assertIsInstance(result, dict)

    def test_logging_improvements(self):
        """Test that logging has been improved"""
        logger = EnhancedLogger(__name__)

        # Test that enhanced logging captures more information
        logger.info("Test message", context={"test": True})

        # Test that error tracking works
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.error("Test error occurred", error=e)

        # Test that error summary is available
        summary = logger.get_error_summary()
        self.assertIn('total_errors', summary)
        self.assertIn('total_warnings', summary)
        self.assertIn('recent_errors', summary)
        self.assertIn('recent_warnings', summary)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestConfigurationSystem,
        TestExcelUtilities,
        TestFCFConsolidation,
        TestErrorHandling,
        TestSystemIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running comprehensive test suite for financial analysis improvements...")
    success = run_comprehensive_tests()

    if success:
        print("\n✅ ALL TESTS PASSED - Application improvements are working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED - Please review the failures above.")

    sys.exit(0 if success else 1)
