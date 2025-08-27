"""
Test Suite for Financial Calculation Engine
==========================================

Comprehensive mathematical validation tests for the pure calculation functions
in the Financial Calculation Engine. Tests focus on mathematical accuracy,
edge cases, and error handling.

Test Categories:
1. Free Cash Flow Calculations (FCFF, FCFE, LFCF)
2. Growth Rate Calculations (CAGR)
3. DCF Calculations (Present Value, Terminal Value)
4. DDM Calculations (Gordon Growth Model)
5. P/B Calculations (Ratio, BVPS)
6. Utility Functions (Percentile, Validation)
7. Edge Cases and Error Conditions
"""

import unittest
import math
from financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class TestFinancialCalculationEngine(unittest.TestCase):
    """Test suite for the Financial Calculation Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()
        
        # Sample data for testing
        self.sample_ebit = [100.0, 110.0, 121.0, 133.1, 146.4]
        self.sample_tax_rates = [0.25, 0.25, 0.25, 0.25, 0.25]
        self.sample_depreciation = [10.0, 11.0, 12.1, 13.3, 14.6]
        self.sample_wc_changes = [5.0, 5.5, 6.1, 6.7, 7.4]
        self.sample_capex = [20.0, 22.0, 24.2, 26.6, 29.3]
        
        self.sample_net_income = [75.0, 82.5, 90.8, 99.9, 109.9]
        self.sample_ocf = [95.0, 104.5, 115.0, 126.5, 139.2]
        self.sample_net_borrowing = [5.0, 3.0, 2.0, -1.0, -2.0]
    
    # =====================
    # Test FCF Calculations
    # =====================
    
    def test_calculate_fcf_to_firm_valid(self):
        """Test FCFF calculation with valid inputs"""
        result = self.engine.calculate_fcf_to_firm(
            self.sample_ebit,
            self.sample_tax_rates,
            self.sample_depreciation,
            self.sample_wc_changes,
            self.sample_capex
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.value), 5)
        
        # Manual calculation for first year: 100*(1-0.25) + 10 - 20 - 5 = 60
        expected_first_year = 100.0 * (1 - 0.25) + 10.0 - 20.0 - 5.0
        self.assertAlmostEqual(result.value[0], expected_first_year, places=2)
        
        # Verify metadata
        self.assertIn('calculation_method', result.metadata)
        self.assertEqual(result.metadata['periods_calculated'], 5)
    
    def test_calculate_fcf_to_firm_empty_inputs(self):
        """Test FCFF calculation with empty inputs"""
        result = self.engine.calculate_fcf_to_firm([], [], [], [], [])
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.value), 0)
        self.assertIn("non-empty", result.error_message)
    
    def test_calculate_fcf_to_firm_invalid_tax_rates(self):
        """Test FCFF calculation with invalid tax rates"""
        invalid_tax_rates = [1.5, -0.1, 0.25, 0.25, 0.25]  # >1 and negative
        
        result = self.engine.calculate_fcf_to_firm(
            self.sample_ebit,
            invalid_tax_rates,
            self.sample_depreciation,
            self.sample_wc_changes,
            self.sample_capex
        )
        
        # Should still be valid but tax rates should be clamped
        self.assertTrue(result.is_valid)
        # First calculation should use clamped tax rate of 1.0
        expected_first_year = 100.0 * (1 - 1.0) + 10.0 - 20.0 - 5.0  # = -15
        self.assertAlmostEqual(result.value[0], expected_first_year, places=2)
    
    def test_calculate_fcf_to_equity_valid(self):
        """Test FCFE calculation with valid inputs"""
        result = self.engine.calculate_fcf_to_equity(
            self.sample_net_income,
            self.sample_depreciation,
            self.sample_wc_changes,
            self.sample_capex,
            self.sample_net_borrowing
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.value), 5)
        
        # Manual calculation for first year: 75 + 10 - 20 - 5 + 5 = 65
        expected_first_year = 75.0 + 10.0 - 20.0 - 5.0 + 5.0
        self.assertAlmostEqual(result.value[0], expected_first_year, places=2)
    
    def test_calculate_levered_fcf_valid(self):
        """Test LFCF calculation with valid inputs"""
        result = self.engine.calculate_levered_fcf(
            self.sample_ocf,
            self.sample_capex
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.value), 5)
        
        # Manual calculation for first year: 95 - 20 = 75
        expected_first_year = 95.0 - 20.0
        self.assertAlmostEqual(result.value[0], expected_first_year, places=2)
    
    # =====================
    # Test Growth Calculations
    # =====================
    
    def test_calculate_cagr_valid(self):
        """Test CAGR calculation with valid inputs"""
        result = self.engine.calculate_cagr(100.0, 161.05, 5.0)  # ~10% CAGR
        
        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.1, places=3)  # 10%
        
        # Verify metadata
        self.assertEqual(result.metadata['start_value'], 100.0)
        self.assertEqual(result.metadata['end_value'], 161.05)
        self.assertEqual(result.metadata['periods'], 5.0)
    
    def test_calculate_cagr_zero_start_value(self):
        """Test CAGR calculation with zero start value"""
        result = self.engine.calculate_cagr(0.0, 100.0, 5.0)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Start value cannot be zero", result.error_message)
    
    def test_calculate_cagr_negative_periods(self):
        """Test CAGR calculation with negative periods"""
        result = self.engine.calculate_cagr(100.0, 150.0, -2.0)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Periods must be positive", result.error_message)
    
    def test_calculate_cagr_negative_values(self):
        """Test CAGR calculation with negative values"""
        result = self.engine.calculate_cagr(-100.0, -50.0, 2.0)
        
        # Actually this works mathematically but produces warning
        self.assertTrue(result.is_valid)  # Still mathematically valid
        # From -100 to -50 over 2 years is negative growth (losses decreasing)
        self.assertLess(result.value, 0)  # Should be negative growth rate
    
    # =====================
    # Test DCF Calculations
    # =====================
    
    def test_calculate_present_value_valid(self):
        """Test present value calculation with valid inputs"""
        cash_flows = [100.0, 110.0, 121.0, 133.1, 146.4]
        discount_rate = 0.10
        
        result = self.engine.calculate_present_value(cash_flows, discount_rate)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.value), 5)
        
        # Manual calculation for first year: 100 / (1.10)^1 = 90.91
        expected_first_pv = 100.0 / (1.10 ** 1)
        self.assertAlmostEqual(result.value[0], expected_first_pv, places=2)
        
        # Check total PV in metadata
        self.assertIn('total_pv', result.metadata)
    
    def test_calculate_present_value_invalid_discount_rate(self):
        """Test present value with invalid discount rates"""
        cash_flows = [100.0, 110.0, 121.0]
        
        # Too high discount rate
        result_high = self.engine.calculate_present_value(cash_flows, 0.60)
        self.assertFalse(result_high.is_valid)
        self.assertIn("outside valid range", result_high.error_message)
        
        # Too low discount rate
        result_low = self.engine.calculate_present_value(cash_flows, -0.01)
        self.assertFalse(result_low.is_valid)
    
    def test_calculate_terminal_value_valid(self):
        """Test terminal value calculation with valid inputs"""
        result = self.engine.calculate_terminal_value(146.4, 0.03, 0.10)
        
        self.assertTrue(result.is_valid)
        
        # Manual calculation: 146.4 * (1.03) / (0.10 - 0.03) = 2,154.17
        expected_tv = 146.4 * 1.03 / 0.07
        self.assertAlmostEqual(result.value, expected_tv, places=2)
    
    def test_calculate_terminal_value_growth_exceeds_discount(self):
        """Test terminal value when growth rate exceeds discount rate"""
        result = self.engine.calculate_terminal_value(100.0, 0.12, 0.10)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Growth rate", result.error_message)
        self.assertIn("must be less than discount rate", result.error_message)
    
    def test_calculate_terminal_value_equal_rates(self):
        """Test terminal value when growth equals discount rate"""
        result = self.engine.calculate_terminal_value(100.0, 0.10, 0.10)
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be less than discount rate", result.error_message)
    
    # =====================
    # Test DDM Calculations
    # =====================
    
    def test_calculate_gordon_growth_value_valid(self):
        """Test Gordon Growth Model with valid inputs"""
        result = self.engine.calculate_gordon_growth_value(2.0, 0.05, 0.12)
        
        self.assertTrue(result.is_valid)
        
        # Manual calculation: 2.0 * 1.05 / (0.12 - 0.05) = 30.0
        expected_value = 2.0 * 1.05 / 0.07
        self.assertAlmostEqual(result.value, expected_value, places=2)
        
        # Check metadata
        self.assertEqual(result.metadata['current_dividend'], 2.0)
        self.assertAlmostEqual(result.metadata['next_dividend'], 2.1, places=2)
    
    def test_calculate_gordon_growth_value_negative_dividend(self):
        """Test Gordon Growth Model with negative dividend"""
        result = self.engine.calculate_gordon_growth_value(-1.0, 0.05, 0.12)
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be positive", result.error_message)
    
    def test_calculate_gordon_growth_value_growth_exceeds_discount(self):
        """Test Gordon Growth Model when growth exceeds discount rate"""
        result = self.engine.calculate_gordon_growth_value(2.0, 0.15, 0.12)
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be less than discount rate", result.error_message)
    
    # =====================
    # Test P/B Calculations
    # =====================
    
    def test_calculate_pb_ratio_valid(self):
        """Test P/B ratio calculation with valid inputs"""
        result = self.engine.calculate_pb_ratio(50.0, 25.0)
        
        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 2.0, places=2)
        
        # Check metadata
        self.assertEqual(result.metadata['market_price'], 50.0)
        self.assertEqual(result.metadata['book_value_per_share'], 25.0)
    
    def test_calculate_pb_ratio_zero_book_value(self):
        """Test P/B ratio with zero book value"""
        result = self.engine.calculate_pb_ratio(50.0, 0.0)
        
        self.assertFalse(result.is_valid)
        self.assertIn("cannot be zero", result.error_message)
    
    def test_calculate_pb_ratio_negative_market_price(self):
        """Test P/B ratio with negative market price"""
        result = self.engine.calculate_pb_ratio(-10.0, 25.0)
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be positive", result.error_message)
    
    def test_calculate_book_value_per_share_valid(self):
        """Test BVPS calculation with valid inputs"""
        result = self.engine.calculate_book_value_per_share(1000000.0, 40000.0)
        
        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 25.0, places=2)  # 1M / 40K = 25
    
    def test_calculate_book_value_per_share_zero_shares(self):
        """Test BVPS calculation with zero shares outstanding"""
        result = self.engine.calculate_book_value_per_share(1000000.0, 0.0)
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be positive", result.error_message)
    
    def test_calculate_book_value_per_share_negative_equity(self):
        """Test BVPS calculation with negative equity"""
        result = self.engine.calculate_book_value_per_share(-500000.0, 40000.0)
        
        self.assertTrue(result.is_valid)  # Valid calculation but negative result
        self.assertLess(result.value, 0)  # Should be negative
    
    # =====================
    # Test Utility Functions
    # =====================
    
    def test_validate_positive_values_valid(self):
        """Test validation of positive values"""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = self.engine.validate_positive_values(values)
        
        self.assertTrue(result)
    
    def test_validate_positive_values_with_negatives(self):
        """Test validation with negative values"""
        values = [10.0, -20.0, 30.0]
        result = self.engine.validate_positive_values(values)
        
        self.assertFalse(result)
    
    def test_validate_positive_values_with_zeros(self):
        """Test validation with zero values"""
        values = [10.0, 0.0, 30.0]
        result = self.engine.validate_positive_values(values)
        
        self.assertFalse(result)
    
    def test_calculate_percentile_valid(self):
        """Test percentile calculation with valid inputs"""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = self.engine.calculate_percentile(25.0, values)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, 40.0)  # 25 is at 40th percentile (2 out of 5 values)
    
    def test_calculate_percentile_empty_list(self):
        """Test percentile calculation with empty list"""
        result = self.engine.calculate_percentile(25.0, [])
        
        self.assertFalse(result.is_valid)
        self.assertIn("non-empty", result.error_message)
    
    def test_calculate_percentile_with_none_values(self):
        """Test percentile calculation with None values in list"""
        values = [10.0, None, 30.0, None, 50.0]
        result = self.engine.calculate_percentile(25.0, values)
        
        self.assertTrue(result.is_valid)
        # Should ignore None values and calculate from [10.0, 30.0, 50.0]
        self.assertEqual(result.metadata['total_values'], 3)
    
    # =====================
    # Integration Tests
    # =====================
    
    def test_calculation_result_structure(self):
        """Test that all calculation results follow the standard structure"""
        # Test various calculations to ensure consistent result structure
        results = [
            self.engine.calculate_cagr(100.0, 110.0, 1.0),
            self.engine.calculate_present_value([100.0], 0.10),
            self.engine.calculate_terminal_value(100.0, 0.03, 0.10),
            self.engine.calculate_gordon_growth_value(2.0, 0.05, 0.10),
            self.engine.calculate_pb_ratio(50.0, 25.0),
            self.engine.calculate_book_value_per_share(1000.0, 40.0)
        ]
        
        for result in results:
            self.assertIsInstance(result, CalculationResult)
            self.assertIsNotNone(result.value)
            self.assertIsInstance(result.is_valid, bool)
            if not result.is_valid:
                self.assertIsNotNone(result.error_message)
            if result.metadata:
                self.assertIsInstance(result.metadata, dict)
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across all functions"""
        # Test None inputs across different functions
        none_results = [
            self.engine.calculate_cagr(None, 110.0, 1.0),
            self.engine.calculate_terminal_value(None, 0.03, 0.10),
            self.engine.calculate_gordon_growth_value(None, 0.05, 0.10),
            self.engine.calculate_pb_ratio(None, 25.0),
            self.engine.calculate_book_value_per_share(None, 40.0)
        ]
        
        for result in none_results:
            self.assertFalse(result.is_valid)
            self.assertIn("None", result.error_message)


class TestFinancialCalculationEnginePerformance(unittest.TestCase):
    """Performance tests for the Financial Calculation Engine"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.engine = FinancialCalculationEngine()
        
        # Large datasets for performance testing
        self.large_dataset = list(range(1, 1001))  # 1000 data points
        self.large_dataset_float = [float(x) for x in self.large_dataset]
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        import time
        
        # Test present value calculation with 1000 cash flows
        start_time = time.time()
        result = self.engine.calculate_present_value(self.large_dataset_float, 0.10)
        end_time = time.time()
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.value), 1000)
        
        # Should complete within reasonable time (< 1 second)
        calculation_time = end_time - start_time
        self.assertLess(calculation_time, 1.0)
    
    def test_percentile_performance(self):
        """Test percentile calculation performance with large dataset"""
        import time
        
        start_time = time.time()
        result = self.engine.calculate_percentile(500.0, self.large_dataset_float)
        end_time = time.time()
        
        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 50.0, places=1)  # Should be ~50th percentile
        
        # Should complete within reasonable time
        calculation_time = end_time - start_time
        self.assertLess(calculation_time, 0.1)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)