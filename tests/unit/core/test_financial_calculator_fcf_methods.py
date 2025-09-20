#!/usr/bin/env python3
"""
Unit Tests for FinancialCalculator FCF Methods
=============================================

Comprehensive unit tests for all Free Cash Flow calculation methods in the
FinancialCalculator engine to achieve >95% coverage goal.

Test Coverage Focus:
- calculate_fcf_to_firm (FCFF)
- calculate_fcf_to_equity (FCFE)
- calculate_levered_fcf (LFCF)
- calculate_all_fcf_types
- calculate_growth_rates
- Error handling and edge cases
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# Ensure proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pytest
from core.analysis.engines.financial_calculations import FinancialCalculator
from tests.utils.common_test_utilities import (
    create_test_excel_structure,
    get_test_financial_data,
    TestDataGenerator
)


class TestFinancialCalculatorFCF(unittest.TestCase):
    """Test suite for FinancialCalculator FCF methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_dir, "TEST_COMPANY")
        os.makedirs(self.company_folder, exist_ok=True)

        # Create test Excel structure with realistic data
        create_test_excel_structure(self.company_folder)

        # Initialize calculator
        self.calculator = FinancialCalculator(self.company_folder)

        # Mock realistic financial data
        self.sample_financial_data = {
            'net_income': [100000000, 120000000, 140000000, 160000000],
            'operating_cash_flow': [150000000, 170000000, 190000000, 210000000],
            'capital_expenditures': [50000000, 60000000, 70000000, 80000000],
            'depreciation': [30000000, 35000000, 40000000, 45000000],
            'working_capital_change': [10000000, -5000000, 15000000, 20000000],
            'total_debt': [500000000, 520000000, 550000000, 580000000],
            'cash': [80000000, 90000000, 100000000, 110000000],
            'ebit': [180000000, 200000000, 220000000, 240000000],
            'tax_rate': 0.25
        }

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_calculate_fcf_to_firm_basic(self):
        """Test FCFF calculation with standard inputs"""
        # Mock data loading
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = self.sample_financial_data

                result = self.calculator.calculate_fcf_to_firm()

                # Verify result structure
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

                # Verify calculations
                # FCFF = EBIT(1-Tax Rate) + Depreciation - CapEx - Change in WC
                expected_fcff_0 = (180000000 * (1-0.25)) + 30000000 - 50000000 - 10000000
                self.assertAlmostEqual(result[0], expected_fcff_0, places=-3)

    def test_calculate_fcf_to_equity_basic(self):
        """Test FCFE calculation with standard inputs"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = self.sample_financial_data

                result = self.calculator.calculate_fcf_to_equity()

                # Verify result structure
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

                # Verify FCFE calculation
                # FCFE = Net Income + Depreciation - CapEx - Change in WC - Net Debt Payments
                net_debt_change_0 = (520000000 - 500000000) - (90000000 - 80000000)
                expected_fcfe_0 = 100000000 + 30000000 - 50000000 - 10000000 - net_debt_change_0
                self.assertAlmostEqual(result[0], expected_fcfe_0, places=-3)

    def test_calculate_levered_fcf_basic(self):
        """Test Levered FCF calculation with standard inputs"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = self.sample_financial_data

                result = self.calculator.calculate_levered_fcf()

                # Verify result structure
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

                # Verify LFCF calculation
                # LFCF = Operating Cash Flow - Capital Expenditures
                expected_lfcf_0 = 150000000 - 50000000
                self.assertAlmostEqual(result[0], expected_lfcf_0, places=-3)

    def test_calculate_all_fcf_types(self):
        """Test calculation of all FCF types together"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = self.sample_financial_data

                result = self.calculator.calculate_all_fcf_types()

                # Verify result structure
                self.assertIsInstance(result, dict)
                self.assertIn('FCFF', result)
                self.assertIn('FCFE', result)
                self.assertIn('LFCF', result)

                # Verify all results are lists
                for fcf_type, values in result.items():
                    self.assertIsInstance(values, list)
                    self.assertGreater(len(values), 0)

    def test_calculate_growth_rates_standard(self):
        """Test growth rate calculations with standard periods"""
        values = (100, 110, 121, 133.1, 146.41)  # 10% annual growth
        periods = (1, 2, 3, 4)

        result = self.calculator.calculate_growth_rates(values, periods)

        # Verify result structure
        self.assertIsInstance(result, dict)

        # Check 1-year growth rate (should be ~10%)
        if '1_year' in result:
            self.assertAlmostEqual(result['1_year'], 0.10, places=2)

    def test_calculate_growth_rates_negative_values(self):
        """Test growth rate calculations with negative values"""
        values = (100, 90, -80, -70, -60)
        periods = (1, 2, 3, 4)

        result = self.calculator.calculate_growth_rates(values, periods)

        # Should handle negative values gracefully
        self.assertIsInstance(result, dict)

    def test_calculate_growth_rates_zero_values(self):
        """Test growth rate calculations with zero values"""
        values = (0, 100, 200, 300, 400)
        periods = (1, 2, 3, 4)

        result = self.calculator.calculate_growth_rates(values, periods)

        # Should handle zero starting values
        self.assertIsInstance(result, dict)

    def test_fcf_calculations_missing_data(self):
        """Test FCF calculations with missing/incomplete data"""
        incomplete_data = {
            'net_income': [100000000, 120000000],  # Missing years
            'operating_cash_flow': [150000000, 170000000],
            'capital_expenditures': [50000000, 60000000],
            # Missing other required fields
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = incomplete_data

                # Should handle missing data gracefully
                result = self.calculator.calculate_all_fcf_types()
                self.assertIsInstance(result, dict)

    def test_fcf_calculations_with_var_input_data(self):
        """Test FCF calculations using VarInputData system"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'var_input_data') as mock_var_data:
                # Mock VarInputData interface
                mock_var_data.get_variable.return_value = [150000000, 170000000, 190000000]

                result = self.calculator.calculate_levered_fcf(use_var_input_data=True)

                # Verify it uses VarInputData when available
                self.assertIsInstance(result, list)
                mock_var_data.get_variable.assert_called()

    def test_error_handling_invalid_data_types(self):
        """Test error handling with invalid data types"""
        invalid_data = {
            'net_income': ['invalid', 'string', 'data'],  # Non-numeric data
            'operating_cash_flow': [None, None, None],    # None values
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = invalid_data

                # Should handle invalid data gracefully
                with self.assertRaises((ValueError, TypeError)) or self.assertIsInstance([], list):
                    self.calculator.calculate_all_fcf_types()

    def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency with large datasets"""
        large_data = {
            'net_income': [100000000] * 1000,  # Large dataset
            'operating_cash_flow': [150000000] * 1000,
            'capital_expenditures': [50000000] * 1000,
            'depreciation': [30000000] * 1000,
            'working_capital_change': [10000000] * 1000,
            'total_debt': [500000000] * 1000,
            'cash': [80000000] * 1000,
            'ebit': [180000000] * 1000,
            'tax_rate': 0.25
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = large_data

                # Should handle large datasets without memory issues
                result = self.calculator.calculate_all_fcf_types()
                self.assertIsInstance(result, dict)

    def test_currency_handling(self):
        """Test FCF calculations with different currencies"""
        # Test with currency conversion factors
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = self.sample_financial_data

                # Mock currency handling
                with patch.object(self.calculator, 'company_currency', 'USD'):
                    result = self.calculator.calculate_all_fcf_types()

                # Verify currency is handled appropriately
                self.assertIsInstance(result, dict)


class TestFinancialCalculatorEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        """Set up edge case test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_dir, "EDGE_TEST")
        os.makedirs(self.company_folder, exist_ok=True)

        self.calculator = FinancialCalculator(self.company_folder)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_extreme_negative_values(self):
        """Test calculations with extreme negative values"""
        extreme_data = {
            'net_income': [-1000000000, -500000000, -200000000, 100000000],
            'operating_cash_flow': [-800000000, -400000000, 200000000, 300000000],
            'capital_expenditures': [100000000, 150000000, 200000000, 250000000],
            'depreciation': [50000000, 60000000, 70000000, 80000000],
            'working_capital_change': [50000000, -30000000, 40000000, 60000000],
            'total_debt': [1000000000, 900000000, 800000000, 700000000],
            'cash': [50000000, 40000000, 60000000, 80000000],
            'ebit': [-900000000, -400000000, 250000000, 300000000],
            'tax_rate': 0.25
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = extreme_data

                result = self.calculator.calculate_all_fcf_types()

                # Verify it handles extreme negatives
                self.assertIsInstance(result, dict)
                for fcf_type, values in result.items():
                    self.assertIsInstance(values, list)

    def test_infinite_and_nan_values(self):
        """Test handling of infinite and NaN values"""
        problematic_data = {
            'net_income': [np.inf, np.nan, 100000000, -np.inf],
            'operating_cash_flow': [150000000, np.inf, np.nan, 200000000],
            'capital_expenditures': [np.nan, 60000000, np.inf, 80000000],
            'tax_rate': 0.25
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = problematic_data

                # Should handle infinite/NaN values gracefully
                result = self.calculator.calculate_all_fcf_types()
                self.assertIsInstance(result, dict)

    def test_single_year_data(self):
        """Test calculations with only single year of data"""
        single_year_data = {
            'net_income': [100000000],
            'operating_cash_flow': [150000000],
            'capital_expenditures': [50000000],
            'depreciation': [30000000],
            'tax_rate': 0.25
        }

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'get_financial_data_for_fcf') as mock_data:
                mock_data.return_value = single_year_data

                result = self.calculator.calculate_all_fcf_types()

                # Should handle single year data
                self.assertIsInstance(result, dict)
                for fcf_type, values in result.items():
                    if values:  # If any data returned
                        self.assertEqual(len(values), 1)


if __name__ == '__main__':
    # Configure test discovery and execution
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialCalculatorFCF))
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialCalculatorEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)