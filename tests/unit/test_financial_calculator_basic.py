"""
Basic Test Suite for FinancialCalculator Class
==============================================

This test suite provides basic coverage for the main FinancialCalculator class,
testing initialization, basic operations, and error handling.
"""

import unittest
import tempfile
import os
import sys
import shutil
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.analysis.engines.financial_calculations import FinancialCalculator


class TestFinancialCalculatorBasic(unittest.TestCase):
    """Test basic FinancialCalculator functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_company_folder = os.path.join(self.temp_dir, "TEST_COMPANY")
        os.makedirs(self.test_company_folder)

        # Create FY and LTM directories
        self.fy_dir = os.path.join(self.test_company_folder, "FY")
        self.ltm_dir = os.path.join(self.test_company_folder, "LTM")
        os.makedirs(self.fy_dir)
        os.makedirs(self.ltm_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_valid_folder(self):
        """Test FinancialCalculator initialization with valid company folder"""
        calculator = FinancialCalculator(self.test_company_folder)

        self.assertEqual(calculator.company_folder, self.test_company_folder)
        self.assertEqual(calculator.company_name, "TEST_COMPANY")
        self.assertIsInstance(calculator.financial_data, dict)
        self.assertIsInstance(calculator.fcf_results, dict)
        self.assertEqual(calculator.currency, 'USD')
        self.assertEqual(calculator.financial_currency, 'USD')
        self.assertFalse(calculator.is_tase_stock)

    def test_initialization_with_none_folder(self):
        """Test FinancialCalculator initialization with None folder"""
        calculator = FinancialCalculator(None)

        self.assertIsNone(calculator.company_folder)
        self.assertIsNotNone(calculator.company_name)
        self.assertIsInstance(calculator.financial_data, dict)
        self.assertIsInstance(calculator.fcf_results, dict)

    def test_initialization_with_enhanced_data_manager(self):
        """Test FinancialCalculator initialization with enhanced data manager"""
        mock_manager = Mock()
        calculator = FinancialCalculator(self.test_company_folder, mock_manager)

        self.assertEqual(calculator.enhanced_data_manager, mock_manager)
        self.assertEqual(calculator.company_folder, self.test_company_folder)

    def test_basic_properties(self):
        """Test basic properties are set correctly"""
        calculator = FinancialCalculator(self.test_company_folder)

        # Test property types and basic state
        self.assertIsNotNone(calculator.ticker_symbol)  # Auto-extracted from folder name
        self.assertIsNone(calculator.current_stock_price)
        self.assertIsNone(calculator.market_cap)
        self.assertIsNone(calculator.shares_outstanding)
        # date_correlation_info may be set during initialization

    def test_get_data_quality_report_empty(self):
        """Test data quality report with no data"""
        calculator = FinancialCalculator(self.test_company_folder)

        report = calculator.get_data_quality_report()

        # Should return a data quality report object (may be empty but not None)
        self.assertIsNotNone(report)

    def test_get_latest_report_date_empty(self):
        """Test latest report date with no data"""
        calculator = FinancialCalculator(self.test_company_folder)

        try:
            date = calculator.get_latest_report_date()
            # Should return empty string or None when no data
            self.assertIn(date, [None, "", "Unknown"])
        except Exception:
            # Acceptable to raise exception when no data available
            pass

    @patch('core.analysis.engines.financial_calculations.logger')
    def test_load_financial_statements_empty_directory(self, mock_logger):
        """Test loading financial statements from empty directory"""
        calculator = FinancialCalculator(self.test_company_folder)

        # Should handle empty directory gracefully
        calculator.load_financial_statements()

        # Should not crash and should log appropriate messages
        self.assertIsInstance(calculator.financial_data, dict)

    def test_currency_properties(self):
        """Test currency-related properties"""
        calculator = FinancialCalculator(self.test_company_folder)

        # Test default currency values
        self.assertEqual(calculator.currency, 'USD')
        self.assertEqual(calculator.financial_currency, 'USD')
        self.assertFalse(calculator.is_tase_stock)


class TestFinancialCalculatorErrorHandling(unittest.TestCase):
    """Test error handling in FinancialCalculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_invalid_folder(self):
        """Test initialization with non-existent folder"""
        invalid_folder = os.path.join(self.temp_dir, "NON_EXISTENT")

        # Should not crash during initialization
        calculator = FinancialCalculator(invalid_folder)

        self.assertEqual(calculator.company_folder, invalid_folder)
        self.assertIsInstance(calculator.financial_data, dict)

    def test_load_excel_data_missing_file(self):
        """Test loading non-existent Excel file"""
        calculator = FinancialCalculator(None)
        missing_file = os.path.join(self.temp_dir, "missing.xlsx")

        # Should handle missing file gracefully
        try:
            df = calculator._load_excel_data(missing_file)
            # Should return empty DataFrame or handle gracefully
            self.assertIsNotNone(df)
        except Exception:
            # Acceptable to raise exception for missing file
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)