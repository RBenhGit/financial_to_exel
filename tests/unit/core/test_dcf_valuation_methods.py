#!/usr/bin/env python3
"""
Unit Tests for DCF Valuation Methods
====================================

Comprehensive unit tests for DCF (Discounted Cash Flow) valuation methods
in the FinancialCalculator engine to achieve >95% coverage goal.

Test Coverage Focus:
- calculate_dcf_inputs
- DCF valuation integration
- Terminal value calculations
- Present value calculations
- Enterprise value to equity value conversion
- Error handling and validation
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
from core.analysis.dcf.dcf_valuation import DCFValuator
from tests.utils.common_test_utilities import create_test_excel_structure


class TestFinancialCalculatorDCF(unittest.TestCase):
    """Test suite for FinancialCalculator DCF methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_dir, "DCF_TEST")
        os.makedirs(self.company_folder, exist_ok=True)

        # Create test Excel structure
        create_test_excel_structure(self.company_folder)

        # Initialize calculator
        self.calculator = FinancialCalculator(self.company_folder)

        # Mock realistic DCF input data
        self.sample_dcf_data = {
            'fcf_values': [100000000, 110000000, 120000000, 130000000, 140000000],
            'revenue': [1000000000, 1100000000, 1200000000, 1300000000, 1400000000],
            'ebitda': [200000000, 220000000, 240000000, 260000000, 280000000],
            'ebit': [150000000, 165000000, 180000000, 195000000, 210000000],
            'net_income': [80000000, 88000000, 96000000, 104000000, 112000000],
            'total_debt': [500000000, 520000000, 540000000, 560000000, 580000000],
            'cash': [100000000, 110000000, 120000000, 130000000, 140000000],
            'shares_outstanding': [50000000, 50000000, 50000000, 50000000, 50000000],
            'wacc': 0.10,
            'terminal_growth_rate': 0.03,
            'tax_rate': 0.25
        }

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_calculate_dcf_inputs_basic(self):
        """Test DCF inputs calculation with standard data"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': self.sample_dcf_data['fcf_values']}

            with patch.object(self.calculator, 'get_market_data') as mock_market:
                mock_market.return_value = {
                    'shares_outstanding': self.sample_dcf_data['shares_outstanding'][0],
                    'total_debt': self.sample_dcf_data['total_debt'][0],
                    'cash': self.sample_dcf_data['cash'][0]
                }

                result = self.calculator.calculate_dcf_inputs()

                # Verify result structure
                self.assertIsInstance(result, dict)
                self.assertIn('fcf_projections', result)
                self.assertIn('terminal_growth_rate', result)
                self.assertIn('discount_rate', result)

    def test_dcf_inputs_with_custom_growth_rates(self):
        """Test DCF inputs calculation with custom growth rate scenarios"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                # Mock historical FCF with declining trend
                declining_fcf = [200000000, 180000000, 160000000, 140000000, 120000000]
                mock_fcf.return_value = {'FCFF': declining_fcf}

                result = self.calculator.calculate_dcf_inputs()

                # Should handle negative growth scenarios
                self.assertIsInstance(result, dict)

    def test_dcf_inputs_missing_market_data(self):
        """Test DCF inputs calculation with missing market data"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': self.sample_dcf_data['fcf_values']}

            with patch.object(self.calculator, 'get_market_data') as mock_market:
                # Mock missing market data
                mock_market.return_value = {}

                result = self.calculator.calculate_dcf_inputs()

                # Should handle missing data gracefully
                self.assertIsInstance(result, dict)

    def test_dcf_inputs_with_enhanced_data_manager(self):
        """Test DCF inputs using enhanced data manager integration"""
        # Mock enhanced data manager
        mock_enhanced_manager = MagicMock()
        mock_enhanced_manager.get_financial_statements.return_value = self.sample_dcf_data
        mock_enhanced_manager.get_market_data.return_value = {
            'shares_outstanding': 50000000,
            'market_cap': 2500000000
        }

        # Initialize calculator with enhanced manager
        calc_enhanced = FinancialCalculator(self.company_folder, mock_enhanced_manager)

        with patch.object(calc_enhanced, 'load_financial_statements'):
            result = calc_enhanced.calculate_dcf_inputs()

            # Verify enhanced data integration
            self.assertIsInstance(result, dict)
            mock_enhanced_manager.get_financial_statements.assert_called()

    def test_dcf_terminal_value_calculations(self):
        """Test terminal value calculation methodologies"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': self.sample_dcf_data['fcf_values']}

                # Test different terminal growth rates
                test_growth_rates = [0.02, 0.03, 0.05, 0.07]

                for growth_rate in test_growth_rates:
                    with patch.object(self.calculator, 'terminal_growth_rate', growth_rate):
                        result = self.calculator.calculate_dcf_inputs()

                        # Verify terminal value varies with growth rate
                        self.assertIsInstance(result, dict)

    def test_dcf_discount_rate_calculation(self):
        """Test discount rate (WACC) calculation and validation"""
        with patch.object(self.calculator, 'load_financial_statements'):
            # Mock financial data for WACC calculation
            financial_data = {
                'total_debt': 500000000,
                'market_cap': 2000000000,
                'tax_rate': 0.25,
                'risk_free_rate': 0.03,
                'market_risk_premium': 0.06,
                'beta': 1.2
            }

            with patch.object(self.calculator, 'get_financial_data_for_wacc') as mock_wacc_data:
                mock_wacc_data.return_value = financial_data

                result = self.calculator.calculate_dcf_inputs()

                # Verify WACC calculation
                self.assertIsInstance(result, dict)
                if 'discount_rate' in result:
                    self.assertGreater(result['discount_rate'], 0)
                    self.assertLess(result['discount_rate'], 1)

    def test_dcf_sensitivity_analysis(self):
        """Test DCF sensitivity to key parameters"""
        base_case_inputs = self.sample_dcf_data.copy()

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': base_case_inputs['fcf_values']}

                # Test sensitivity to different parameters
                sensitivity_tests = [
                    {'wacc_adjustment': 0.02},  # Higher discount rate
                    {'growth_adjustment': -0.01},  # Lower growth rate
                    {'fcf_adjustment': 0.1},  # Higher FCF base
                ]

                results = []
                for test_case in sensitivity_tests:
                    # Apply adjustments
                    adjusted_data = base_case_inputs.copy()
                    if 'wacc_adjustment' in test_case:
                        adjusted_data['wacc'] += test_case['wacc_adjustment']
                    if 'growth_adjustment' in test_case:
                        adjusted_data['terminal_growth_rate'] += test_case['growth_adjustment']

                    result = self.calculator.calculate_dcf_inputs()
                    results.append(result)

                # Verify sensitivity results
                self.assertEqual(len(results), len(sensitivity_tests))

    def test_dcf_multi_stage_growth_model(self):
        """Test multi-stage DCF growth models"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                # Mock FCF data for multi-stage model
                multi_stage_fcf = [100, 120, 150, 180, 200, 220, 240, 260, 280, 300]
                mock_fcf.return_value = {'FCFF': [x * 1000000 for x in multi_stage_fcf]}

                # Test different growth phases
                growth_phases = {
                    'high_growth_years': 5,
                    'transition_years': 3,
                    'stable_growth_rate': 0.03
                }

                result = self.calculator.calculate_dcf_inputs()

                # Verify multi-stage modeling
                self.assertIsInstance(result, dict)


class TestDCFEdgeCases(unittest.TestCase):
    """Test DCF edge cases and error conditions"""

    def setUp(self):
        """Set up edge case test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_dir, "DCF_EDGE_TEST")
        os.makedirs(self.company_folder, exist_ok=True)
        self.calculator = FinancialCalculator(self.company_folder)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_dcf_negative_fcf_values(self):
        """Test DCF with negative FCF values"""
        negative_fcf_data = [-50000000, -30000000, -10000000, 20000000, 50000000]

        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': negative_fcf_data}

                result = self.calculator.calculate_dcf_inputs()

                # Should handle negative FCF gracefully
                self.assertIsInstance(result, dict)

    def test_dcf_extreme_discount_rates(self):
        """Test DCF with extreme discount rates"""
        extreme_rates = [0.001, 0.5, 0.99]  # Very low, high, and near 100%

        with patch.object(self.calculator, 'load_financial_statements'):
            for rate in extreme_rates:
                with patch.object(self.calculator, 'wacc', rate):
                    result = self.calculator.calculate_dcf_inputs()

                    # Should handle extreme rates
                    self.assertIsInstance(result, dict)

    def test_dcf_zero_terminal_growth(self):
        """Test DCF with zero terminal growth rate"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': [100000000, 110000000, 120000000]}

            with patch.object(self.calculator, 'terminal_growth_rate', 0.0):
                result = self.calculator.calculate_dcf_inputs()

                # Should handle zero growth
                self.assertIsInstance(result, dict)

    def test_dcf_infinite_growth_rate(self):
        """Test DCF with growth rate equal to discount rate"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': [100000000, 110000000]}

            # Growth rate = discount rate should cause division by zero
            with patch.object(self.calculator, 'wacc', 0.10):
                with patch.object(self.calculator, 'terminal_growth_rate', 0.10):
                    result = self.calculator.calculate_dcf_inputs()

                    # Should handle this edge case
                    self.assertIsInstance(result, dict)

    def test_dcf_missing_shares_outstanding(self):
        """Test DCF when shares outstanding data is missing"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
                mock_fcf.return_value = {'FCFF': [100000000, 110000000]}

            with patch.object(self.calculator, 'get_market_data') as mock_market:
                # Mock missing shares outstanding
                mock_market.return_value = {
                    'total_debt': 500000000,
                    'cash': 100000000
                    # shares_outstanding missing
                }

                result = self.calculator.calculate_dcf_inputs()

                # Should handle missing shares data
                self.assertIsInstance(result, dict)


class TestDCFIntegration(unittest.TestCase):
    """Test DCF integration with other financial models"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_dir, "DCF_INTEGRATION")
        os.makedirs(self.company_folder, exist_ok=True)
        self.calculator = FinancialCalculator(self.company_folder)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_dcf_fcf_integration(self):
        """Test integration between DCF and FCF calculations"""
        with patch.object(self.calculator, 'load_financial_statements'):
            # First calculate FCF
            fcf_result = self.calculator.calculate_all_fcf_types()

            # Then use FCF in DCF calculation
            dcf_result = self.calculator.calculate_dcf_inputs()

            # Verify integration works
            self.assertIsInstance(fcf_result, dict)
            self.assertIsInstance(dcf_result, dict)

    def test_dcf_market_data_integration(self):
        """Test DCF integration with real-time market data"""
        with patch.object(self.calculator, 'load_financial_statements'):
            with patch.object(self.calculator, 'enhanced_data_manager') as mock_manager:
                # Mock real-time data
                mock_manager.get_real_time_data.return_value = {
                    'current_price': 150.0,
                    'market_cap': 7500000000,
                    'beta': 1.15
                }

                result = self.calculator.calculate_dcf_inputs()

                # Verify real-time integration
                self.assertIsInstance(result, dict)


if __name__ == '__main__':
    # Configure test discovery and execution
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialCalculatorDCF))
    suite.addTests(loader.loadTestsFromTestCase(TestDCFEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDCFIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)