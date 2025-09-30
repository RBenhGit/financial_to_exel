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
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine, CalculationResult


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
    # Test Profitability Ratio Calculations
    # =====================

    def test_calculate_return_on_equity_valid(self):
        """Test ROE calculation with valid inputs"""
        result = self.engine.calculate_return_on_equity(100.0, 500.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.20, places=3)  # 100/500 = 20%

        # Check metadata
        self.assertEqual(result.metadata['net_income'], 100.0)
        self.assertEqual(result.metadata['shareholders_equity'], 500.0)
        self.assertEqual(result.metadata['equity_used'], 500.0)
        self.assertIn('ROE = Net Income', result.metadata['calculation_method'])
        self.assertFalse(result.metadata['negative_equity_scenario'])

    def test_calculate_return_on_equity_with_average_equity(self):
        """Test ROE calculation with average equity"""
        result = self.engine.calculate_return_on_equity(120.0, 600.0, average_equity=550.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.218, places=3)  # 120/550 = ~21.8%

        # Check that average equity was used
        self.assertEqual(result.metadata['average_equity'], 550.0)
        self.assertEqual(result.metadata['equity_used'], 550.0)
        self.assertIn('Average Equity', result.metadata['calculation_method'])

    def test_calculate_return_on_equity_zero_equity(self):
        """Test ROE calculation with zero equity"""
        result = self.engine.calculate_return_on_equity(100.0, 0.0)

        self.assertFalse(result.is_valid)
        self.assertIn("denominator cannot be zero", result.error_message)

    def test_calculate_return_on_equity_negative_equity_positive_income(self):
        """Test ROE calculation with negative equity and positive net income"""
        result = self.engine.calculate_return_on_equity(50.0, -200.0)

        self.assertTrue(result.is_valid)  # Mathematically valid but financially concerning
        self.assertAlmostEqual(result.value, -0.25, places=3)  # 50/(-200) = -25%

        # Check special handling metadata
        self.assertTrue(result.metadata['negative_equity_scenario'])
        self.assertIn("severe financial distress", result.metadata['interpretation'])

    def test_calculate_return_on_equity_negative_equity_negative_income(self):
        """Test ROE calculation with both negative equity and negative income"""
        result = self.engine.calculate_return_on_equity(-30.0, -200.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.15, places=3)  # -30/(-200) = 15%

        # This scenario produces positive ROE but indicates severe distress
        self.assertTrue(result.metadata['negative_equity_scenario'])
        self.assertIn("severe financial distress", result.metadata['interpretation'])

    def test_calculate_return_on_equity_none_inputs(self):
        """Test ROE calculation with None inputs"""
        result_none_income = self.engine.calculate_return_on_equity(None, 500.0)
        result_none_equity = self.engine.calculate_return_on_equity(100.0, None)
        result_both_none = self.engine.calculate_return_on_equity(None, None)

        for result in [result_none_income, result_none_equity, result_both_none]:
            self.assertFalse(result.is_valid)
            self.assertIn("cannot be None", result.error_message)

    def test_calculate_return_on_equity_edge_cases(self):
        """Test ROE calculation with edge cases"""
        # Very high ROE
        result_high = self.engine.calculate_return_on_equity(400.0, 500.0)  # 80% ROE
        self.assertTrue(result_high.is_valid)
        self.assertAlmostEqual(result_high.value, 0.80, places=3)

        # Very low ROE
        result_low = self.engine.calculate_return_on_equity(1.0, 1000.0)  # 0.1% ROE
        self.assertTrue(result_low.is_valid)
        self.assertAlmostEqual(result_low.value, 0.001, places=4)

        # Negative ROE with positive equity
        result_negative = self.engine.calculate_return_on_equity(-50.0, 500.0)  # -10% ROE
        self.assertTrue(result_negative.is_valid)
        self.assertAlmostEqual(result_negative.value, -0.10, places=3)

    def test_calculate_return_on_equity_interpretation_levels(self):
        """Test ROE interpretation for different performance levels"""
        # Test different ROE levels and their interpretations
        test_cases = [
            (120.0, 500.0, "Excellent return on equity"),      # 24% - excellent
            (80.0, 500.0, "Strong return on equity"),          # 16% - strong
            (60.0, 500.0, "Moderate return on equity"),        # 12% - moderate
            (25.0, 500.0, "Low return on equity"),             # 5% - low
            (-25.0, 500.0, "Negative ROE"),                    # -5% - negative
        ]

        for net_income, equity, expected_interpretation in test_cases:
            result = self.engine.calculate_return_on_equity(net_income, equity)
            self.assertTrue(result.is_valid)
            self.assertIn(expected_interpretation.split()[0].lower(),
                         result.metadata['interpretation'].lower())

    def test_calculate_return_on_equity_mathematical_accuracy(self):
        """Test mathematical accuracy of ROE calculations"""
        # Test various scenarios with known expected results
        test_scenarios = [
            (100.0, 1000.0, 0.10),      # 10%
            (250.0, 1000.0, 0.25),      # 25%
            (87.5, 350.0, 0.25),        # 25%
            (150.0, 750.0, 0.20),       # 20%
            (0.0, 500.0, 0.00),         # 0%
        ]

        for net_income, equity, expected_roe in test_scenarios:
            result = self.engine.calculate_return_on_equity(net_income, equity)
            self.assertTrue(result.is_valid)
            self.assertAlmostEqual(result.value, expected_roe, places=3,
                                 msg=f"ROE calculation failed for net_income={net_income}, equity={equity}")

    # =====================
    # Test ROIC Calculations
    # =====================

    def test_calculate_return_on_invested_capital_with_direct_inputs(self):
        """Test ROIC calculation with directly provided NOPAT and invested capital"""
        result = self.engine.calculate_return_on_invested_capital(
            nopat=100.0,
            invested_capital=500.0
        )

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.20, places=3)  # 100/500 = 20%

        # Check metadata
        self.assertEqual(result.metadata['nopat'], 100.0)
        self.assertEqual(result.metadata['invested_capital'], 500.0)
        self.assertEqual(result.metadata['nopat_method'], 'provided')
        self.assertEqual(result.metadata['invested_capital_method'], 'provided')
        self.assertIn('ROIC = NOPAT / Invested Capital', result.metadata['calculation_method'])

    def test_calculate_return_on_invested_capital_with_ebit_and_tax(self):
        """Test ROIC calculation with EBIT and tax rate for NOPAT calculation"""
        result = self.engine.calculate_return_on_invested_capital(
            ebit=150.0,
            tax_rate=0.25,
            invested_capital=600.0
        )

        self.assertTrue(result.is_valid)
        # NOPAT = 150 * (1 - 0.25) = 112.5
        # ROIC = 112.5 / 600 = 0.1875 = 18.75%
        expected_roic = (150.0 * (1 - 0.25)) / 600.0
        self.assertAlmostEqual(result.value, expected_roic, places=3)

        # Check metadata shows calculated NOPAT
        self.assertEqual(result.metadata['nopat'], 112.5)
        self.assertEqual(result.metadata['ebit'], 150.0)
        self.assertEqual(result.metadata['tax_rate'], 0.25)
        self.assertIn('calculated from EBIT', result.metadata['nopat_method'])

    def test_calculate_return_on_invested_capital_with_assets_calculation(self):
        """Test ROIC calculation with invested capital calculated from assets"""
        result = self.engine.calculate_return_on_invested_capital(
            nopat=80.0,
            total_assets=1000.0,
            current_liabilities=200.0
        )

        self.assertTrue(result.is_valid)
        # Invested Capital = 1000 - 200 = 800
        # ROIC = 80 / 800 = 0.10 = 10%
        expected_roic = 80.0 / (1000.0 - 200.0)
        self.assertAlmostEqual(result.value, expected_roic, places=3)

        # Check metadata shows calculated invested capital
        self.assertEqual(result.metadata['invested_capital'], 800.0)
        self.assertEqual(result.metadata['total_assets'], 1000.0)
        self.assertEqual(result.metadata['current_liabilities'], 200.0)
        self.assertIn('Total Assets - Current Liabilities', result.metadata['invested_capital_method'])

    def test_calculate_return_on_invested_capital_with_equity_debt_calculation(self):
        """Test ROIC calculation with invested capital calculated from equity and debt"""
        result = self.engine.calculate_return_on_invested_capital(
            nopat=90.0,
            equity=400.0,
            debt=300.0
        )

        self.assertTrue(result.is_valid)
        # Invested Capital = 400 + 300 = 700
        # ROIC = 90 / 700 = 0.1286 ≈ 12.86%
        expected_roic = 90.0 / (400.0 + 300.0)
        self.assertAlmostEqual(result.value, expected_roic, places=3)

        # Check metadata shows calculated invested capital
        self.assertEqual(result.metadata['invested_capital'], 700.0)
        self.assertEqual(result.metadata['equity'], 400.0)
        self.assertEqual(result.metadata['debt'], 300.0)
        self.assertIn('Equity + Debt', result.metadata['invested_capital_method'])

    def test_calculate_return_on_invested_capital_complete_calculation(self):
        """Test ROIC calculation with full calculation from components"""
        result = self.engine.calculate_return_on_invested_capital(
            ebit=200.0,
            tax_rate=0.30,
            total_assets=1200.0,
            current_liabilities=300.0
        )

        self.assertTrue(result.is_valid)
        # NOPAT = 200 * (1 - 0.30) = 140
        # Invested Capital = 1200 - 300 = 900
        # ROIC = 140 / 900 = 0.1556 ≈ 15.56%
        expected_nopat = 200.0 * (1 - 0.30)
        expected_invested_capital = 1200.0 - 300.0
        expected_roic = expected_nopat / expected_invested_capital
        self.assertAlmostEqual(result.value, expected_roic, places=3)

        # Check both calculations were performed
        self.assertEqual(result.metadata['nopat'], expected_nopat)
        self.assertEqual(result.metadata['invested_capital'], expected_invested_capital)
        self.assertIn('calculated from EBIT', result.metadata['nopat_method'])
        self.assertIn('Total Assets - Current Liabilities', result.metadata['invested_capital_method'])

    def test_calculate_return_on_invested_capital_missing_inputs(self):
        """Test ROIC calculation with insufficient inputs"""
        # Missing both NOPAT and EBIT/tax_rate
        result_no_nopat = self.engine.calculate_return_on_invested_capital(
            invested_capital=500.0
        )
        self.assertFalse(result_no_nopat.is_valid)
        self.assertIn("Either NOPAT must be provided", result_no_nopat.error_message)

        # Missing invested capital components
        result_no_capital = self.engine.calculate_return_on_invested_capital(
            nopat=100.0
        )
        self.assertFalse(result_no_capital.is_valid)
        self.assertIn("Either invested_capital must be provided", result_no_capital.error_message)

        # Missing tax rate for NOPAT calculation
        result_no_tax = self.engine.calculate_return_on_invested_capital(
            ebit=150.0,
            invested_capital=500.0
        )
        self.assertFalse(result_no_tax.is_valid)
        self.assertIn("both EBIT and tax_rate must be provided", result_no_tax.error_message)

    def test_calculate_return_on_invested_capital_zero_invested_capital(self):
        """Test ROIC calculation with zero invested capital"""
        result = self.engine.calculate_return_on_invested_capital(
            nopat=100.0,
            invested_capital=0.0
        )

        self.assertFalse(result.is_valid)
        self.assertIn("Invested capital cannot be zero", result.error_message)

    def test_calculate_return_on_invested_capital_invalid_tax_rate(self):
        """Test ROIC calculation with invalid tax rates"""
        # Tax rate > 1
        result_high_tax = self.engine.calculate_return_on_invested_capital(
            ebit=100.0,
            tax_rate=1.5,
            invested_capital=500.0
        )
        self.assertTrue(result_high_tax.is_valid)  # Should clamp tax rate to 1.0
        # NOPAT = 100 * (1 - 1.0) = 0, ROIC = 0 / 500 = 0
        self.assertAlmostEqual(result_high_tax.value, 0.0, places=3)

        # Negative tax rate
        result_negative_tax = self.engine.calculate_return_on_invested_capital(
            ebit=100.0,
            tax_rate=-0.1,
            invested_capital=500.0
        )
        self.assertTrue(result_negative_tax.is_valid)  # Should clamp tax rate to 0.0
        # NOPAT = 100 * (1 - 0.0) = 100, ROIC = 100 / 500 = 0.20
        self.assertAlmostEqual(result_negative_tax.value, 0.20, places=3)

    def test_calculate_return_on_invested_capital_negative_invested_capital(self):
        """Test ROIC calculation with negative invested capital"""
        result = self.engine.calculate_return_on_invested_capital(
            nopat=50.0,
            invested_capital=-200.0
        )

        self.assertTrue(result.is_valid)  # Mathematically valid but concerning
        self.assertAlmostEqual(result.value, -0.25, places=3)  # 50 / (-200) = -25%

    def test_calculate_return_on_invested_capital_edge_cases(self):
        """Test ROIC calculation with edge cases"""
        # Very high ROIC
        result_high = self.engine.calculate_return_on_invested_capital(
            nopat=200.0,
            invested_capital=500.0
        )
        self.assertTrue(result_high.is_valid)
        self.assertAlmostEqual(result_high.value, 0.40, places=3)  # 40%

        # Very low ROIC
        result_low = self.engine.calculate_return_on_invested_capital(
            nopat=5.0,
            invested_capital=1000.0
        )
        self.assertTrue(result_low.is_valid)
        self.assertAlmostEqual(result_low.value, 0.005, places=4)  # 0.5%

        # Negative ROIC
        result_negative = self.engine.calculate_return_on_invested_capital(
            nopat=-30.0,
            invested_capital=500.0
        )
        self.assertTrue(result_negative.is_valid)
        self.assertAlmostEqual(result_negative.value, -0.06, places=3)  # -6%

        # Zero NOPAT
        result_zero_nopat = self.engine.calculate_return_on_invested_capital(
            nopat=0.0,
            invested_capital=500.0
        )
        self.assertTrue(result_zero_nopat.is_valid)
        self.assertAlmostEqual(result_zero_nopat.value, 0.0, places=3)  # 0%

    def test_calculate_return_on_invested_capital_interpretation_levels(self):
        """Test ROIC interpretation for different performance levels"""
        test_cases = [
            (120.0, 500.0, "Excellent capital efficiency"),      # 24% - excellent
            (80.0, 500.0, "Strong capital efficiency"),          # 16% - strong
            (60.0, 500.0, "Moderate capital efficiency"),        # 12% - moderate
            (35.0, 500.0, "Low capital efficiency"),             # 7% - low
            (15.0, 500.0, "Very low capital efficiency"),        # 3% - very low
            (-25.0, 500.0, "Negative ROIC"),                     # -5% - negative
        ]

        for nopat, invested_capital, expected_interpretation in test_cases:
            result = self.engine.calculate_return_on_invested_capital(
                nopat=nopat,
                invested_capital=invested_capital
            )
            self.assertTrue(result.is_valid)
            self.assertIn(expected_interpretation.split()[0].lower(),
                         result.metadata['interpretation'].lower())

    def test_calculate_return_on_invested_capital_mathematical_accuracy(self):
        """Test mathematical accuracy of ROIC calculations"""
        test_scenarios = [
            # (nopat, invested_capital, expected_roic)
            (100.0, 1000.0, 0.10),      # 10%
            (250.0, 1000.0, 0.25),      # 25%
            (87.5, 350.0, 0.25),        # 25%
            (150.0, 750.0, 0.20),       # 20%
            (0.0, 500.0, 0.00),         # 0%
            (75.0, 300.0, 0.25),        # 25%
        ]

        for nopat, invested_capital, expected_roic in test_scenarios:
            result = self.engine.calculate_return_on_invested_capital(
                nopat=nopat,
                invested_capital=invested_capital
            )
            self.assertTrue(result.is_valid)
            self.assertAlmostEqual(result.value, expected_roic, places=3,
                                 msg=f"ROIC calculation failed for nopat={nopat}, invested_capital={invested_capital}")

    def test_calculate_return_on_invested_capital_comprehensive_calculation_accuracy(self):
        """Test comprehensive ROIC calculation accuracy with component calculations"""
        # Test scenario: EBIT=200, tax_rate=0.25, total_assets=1000, current_liabilities=100
        result = self.engine.calculate_return_on_invested_capital(
            ebit=200.0,
            tax_rate=0.25,
            total_assets=1000.0,
            current_liabilities=100.0
        )

        self.assertTrue(result.is_valid)

        # Manual calculations:
        # NOPAT = 200 * (1 - 0.25) = 150
        # Invested Capital = 1000 - 100 = 900
        # ROIC = 150 / 900 = 0.1667 ≈ 16.67%
        expected_nopat = 200.0 * (1 - 0.25)
        expected_invested_capital = 1000.0 - 100.0
        expected_roic = expected_nopat / expected_invested_capital

        self.assertAlmostEqual(result.value, expected_roic, places=4)
        self.assertAlmostEqual(result.metadata['nopat'], expected_nopat, places=2)
        self.assertAlmostEqual(result.metadata['invested_capital'], expected_invested_capital, places=2)

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
            self.engine.calculate_book_value_per_share(1000.0, 40.0),
            self.engine.calculate_return_on_equity(100.0, 500.0),
            self.engine.calculate_return_on_invested_capital(nopat=100.0, invested_capital=500.0)
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
            self.engine.calculate_book_value_per_share(None, 40.0),
            self.engine.calculate_return_on_equity(None, 500.0)
        ]

        for result in none_results:
            self.assertFalse(result.is_valid)
            self.assertIn("None", result.error_message)

        # Test ROIC separately as it has different error message pattern
        roic_result = self.engine.calculate_return_on_invested_capital()  # No parameters should fail
        self.assertFalse(roic_result.is_valid)
        self.assertIn("must be provided", roic_result.error_message)


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

    # =====================
    # Test Leverage/Solvency Ratio Calculations
    # =====================

    def test_calculate_debt_to_assets_ratio_valid(self):
        """Test debt-to-assets ratio calculation with valid inputs"""
        result = self.engine.calculate_debt_to_assets_ratio(300.0, 1000.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.30, places=3)  # 300/1000 = 30%

        # Check metadata
        self.assertEqual(result.metadata['total_debt'], 300.0)
        self.assertEqual(result.metadata['total_assets'], 1000.0)
        self.assertIn('Debt-to-Assets Ratio = Total Debt / Total Assets', result.metadata['calculation_method'])

    def test_calculate_debt_to_assets_ratio_zero_assets(self):
        """Test debt-to-assets ratio calculation with zero total assets"""
        result = self.engine.calculate_debt_to_assets_ratio(300.0, 0.0)

        self.assertFalse(result.is_valid)
        self.assertIn("Total assets cannot be zero", result.error_message)

    def test_calculate_debt_to_assets_ratio_none_inputs(self):
        """Test debt-to-assets ratio calculation with None inputs"""
        result_none_debt = self.engine.calculate_debt_to_assets_ratio(None, 1000.0)
        result_none_assets = self.engine.calculate_debt_to_assets_ratio(300.0, None)
        result_both_none = self.engine.calculate_debt_to_assets_ratio(None, None)

        for result in [result_none_debt, result_none_assets, result_both_none]:
            self.assertFalse(result.is_valid)
            self.assertIn("cannot be None", result.error_message)

    def test_calculate_debt_to_assets_ratio_negative_values(self):
        """Test debt-to-assets ratio calculation with negative values"""
        # Negative debt
        result_negative_debt = self.engine.calculate_debt_to_assets_ratio(-100.0, 1000.0)
        self.assertTrue(result_negative_debt.is_valid)  # Mathematically valid but unusual
        self.assertAlmostEqual(result_negative_debt.value, -0.10, places=3)

        # Negative assets
        result_negative_assets = self.engine.calculate_debt_to_assets_ratio(300.0, -1000.0)
        self.assertTrue(result_negative_assets.is_valid)  # Mathematically valid but concerning
        self.assertAlmostEqual(result_negative_assets.value, -0.30, places=3)

        # Both negative
        result_both_negative = self.engine.calculate_debt_to_assets_ratio(-300.0, -1000.0)
        self.assertTrue(result_both_negative.is_valid)
        self.assertAlmostEqual(result_both_negative.value, 0.30, places=3)  # -300/-1000 = 0.30

    def test_calculate_debt_to_assets_ratio_zero_debt(self):
        """Test debt-to-assets ratio calculation with zero debt"""
        result = self.engine.calculate_debt_to_assets_ratio(0.0, 1000.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.0, places=3)  # 0/1000 = 0%

    def test_calculate_debt_to_assets_ratio_edge_cases(self):
        """Test debt-to-assets ratio calculation with edge cases"""
        # Very high leverage (debt > assets)
        result_high = self.engine.calculate_debt_to_assets_ratio(1200.0, 1000.0)
        self.assertTrue(result_high.is_valid)
        self.assertAlmostEqual(result_high.value, 1.20, places=3)  # 120%

        # Very low leverage
        result_low = self.engine.calculate_debt_to_assets_ratio(50.0, 1000.0)
        self.assertTrue(result_low.is_valid)
        self.assertAlmostEqual(result_low.value, 0.05, places=3)  # 5%

        # Equal debt and assets
        result_equal = self.engine.calculate_debt_to_assets_ratio(1000.0, 1000.0)
        self.assertTrue(result_equal.is_valid)
        self.assertAlmostEqual(result_equal.value, 1.0, places=3)  # 100%

    def test_calculate_debt_to_assets_ratio_interpretation_levels(self):
        """Test debt-to-assets ratio interpretation for different leverage levels"""
        test_cases = [
            (700.0, 1000.0, "High leverage"),               # 70% - high
            (500.0, 1000.0, "Moderate leverage"),           # 50% - moderate
            (300.0, 1000.0, "Conservative leverage"),       # 30% - conservative
            (100.0, 1000.0, "Very conservative"),           # 10% - very conservative
            (0.0, 1000.0, "Very conservative"),             # 0% - minimal debt
        ]

        for debt, assets, expected_interpretation in test_cases:
            result = self.engine.calculate_debt_to_assets_ratio(debt, assets)
            self.assertTrue(result.is_valid)
            self.assertIn(expected_interpretation.split()[0].lower(),
                         result.metadata['interpretation'].lower())

    def test_calculate_debt_to_assets_ratio_mathematical_accuracy(self):
        """Test mathematical accuracy of debt-to-assets ratio calculations"""
        test_scenarios = [
            # (total_debt, total_assets, expected_ratio)
            (250.0, 1000.0, 0.25),        # 25%
            (400.0, 1000.0, 0.40),        # 40%
            (600.0, 1000.0, 0.60),        # 60%
            (0.0, 1000.0, 0.00),          # 0%
            (1000.0, 1000.0, 1.00),       # 100%
            (300.0, 600.0, 0.50),         # 50%
            (150.0, 750.0, 0.20),         # 20%
        ]

        for debt, assets, expected_ratio in test_scenarios:
            result = self.engine.calculate_debt_to_assets_ratio(debt, assets)
            self.assertTrue(result.is_valid)
            self.assertAlmostEqual(result.value, expected_ratio, places=3,
                                 msg=f"Debt-to-assets calculation failed for debt={debt}, assets={assets}")

    def test_calculate_debt_to_assets_ratio_financial_interpretation(self):
        """Test financial interpretation accuracy"""
        # Very conservative company (low debt - 15%)
        very_conservative_result = self.engine.calculate_debt_to_assets_ratio(150.0, 1000.0)
        self.assertTrue(very_conservative_result.is_valid)
        self.assertIn("conservative", very_conservative_result.metadata['interpretation'].lower())

        # Conservative company (25% debt)
        conservative_result = self.engine.calculate_debt_to_assets_ratio(250.0, 1000.0)
        self.assertTrue(conservative_result.is_valid)
        self.assertIn("conservative", conservative_result.metadata['interpretation'].lower())

        # Moderate leverage company (45% debt)
        moderate_result = self.engine.calculate_debt_to_assets_ratio(450.0, 1000.0)
        self.assertTrue(moderate_result.is_valid)
        self.assertIn("moderate", moderate_result.metadata['interpretation'].lower())

        # High leverage company (70% debt)
        high_result = self.engine.calculate_debt_to_assets_ratio(700.0, 1000.0)
        self.assertTrue(high_result.is_valid)
        self.assertIn("high", high_result.metadata['interpretation'].lower())

        # Overleveraged company (debt > assets - 120%)
        overleveraged_result = self.engine.calculate_debt_to_assets_ratio(1200.0, 1000.0)
        self.assertTrue(overleveraged_result.is_valid)
        self.assertIn("high", overleveraged_result.metadata['interpretation'].lower())

    # =====================
    # Test Debt-to-Equity Ratio Calculations
    # =====================

    def test_calculate_debt_to_equity_ratio_valid(self):
        """Test debt-to-equity ratio calculation with valid inputs"""
        result = self.engine.calculate_debt_to_equity_ratio(300.0, 500.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.60, places=3)  # 300/500 = 0.6

        # Check metadata
        self.assertEqual(result.metadata['total_debt'], 300.0)
        self.assertEqual(result.metadata['total_equity'], 500.0)
        self.assertIn('Debt-to-Equity Ratio = Total Debt / Total Equity', result.metadata['calculation_method'])
        self.assertFalse(result.metadata['negative_equity_scenario'])

    def test_calculate_debt_to_equity_ratio_zero_equity(self):
        """Test debt-to-equity ratio calculation with zero total equity"""
        result = self.engine.calculate_debt_to_equity_ratio(300.0, 0.0)

        self.assertFalse(result.is_valid)
        self.assertIn("Total equity cannot be zero", result.error_message)

    def test_calculate_debt_to_equity_ratio_none_inputs(self):
        """Test debt-to-equity ratio calculation with None inputs"""
        result_none_debt = self.engine.calculate_debt_to_equity_ratio(None, 500.0)
        result_none_equity = self.engine.calculate_debt_to_equity_ratio(300.0, None)
        result_both_none = self.engine.calculate_debt_to_equity_ratio(None, None)

        for result in [result_none_debt, result_none_equity, result_both_none]:
            self.assertFalse(result.is_valid)
            self.assertIn("cannot be None", result.error_message)

    def test_calculate_debt_to_equity_ratio_negative_equity(self):
        """Test debt-to-equity ratio calculation with negative equity"""
        # Positive debt, negative equity (severe distress)
        result_pos_debt = self.engine.calculate_debt_to_equity_ratio(300.0, -200.0)
        self.assertTrue(result_pos_debt.is_valid)  # Mathematically valid but concerning
        self.assertAlmostEqual(result_pos_debt.value, -1.50, places=3)  # 300/-200 = -1.5
        self.assertTrue(result_pos_debt.metadata['negative_equity_scenario'])
        self.assertIn("severe financial distress", result_pos_debt.metadata['interpretation'].lower())

        # Both negative
        result_both_negative = self.engine.calculate_debt_to_equity_ratio(-300.0, -200.0)
        self.assertTrue(result_both_negative.is_valid)
        self.assertAlmostEqual(result_both_negative.value, 1.50, places=3)  # -300/-200 = 1.5
        self.assertTrue(result_both_negative.metadata['negative_equity_scenario'])

    def test_calculate_debt_to_equity_ratio_zero_debt(self):
        """Test debt-to-equity ratio calculation with zero debt"""
        result = self.engine.calculate_debt_to_equity_ratio(0.0, 500.0)

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 0.0, places=3)  # 0/500 = 0

    def test_calculate_debt_to_equity_ratio_high_leverage(self):
        """Test debt-to-equity ratio calculation with high leverage scenarios"""
        # Moderate leverage (D/E = 1.5)
        result_moderate = self.engine.calculate_debt_to_equity_ratio(750.0, 500.0)
        self.assertTrue(result_moderate.is_valid)
        self.assertAlmostEqual(result_moderate.value, 1.50, places=3)

        # High leverage (D/E = 2.5)
        result_high = self.engine.calculate_debt_to_equity_ratio(1250.0, 500.0)
        self.assertTrue(result_high.is_valid)
        self.assertAlmostEqual(result_high.value, 2.50, places=3)
        self.assertIn("high", result_high.metadata['interpretation'].lower())

        # Very high leverage (D/E = 4.0)
        result_very_high = self.engine.calculate_debt_to_equity_ratio(2000.0, 500.0)
        self.assertTrue(result_very_high.is_valid)
        self.assertAlmostEqual(result_very_high.value, 4.00, places=3)
        self.assertIn("excessive", result_very_high.metadata['interpretation'].lower())

    def test_calculate_debt_to_equity_ratio_interpretation_levels(self):
        """Test debt-to-equity ratio interpretation for different leverage levels"""
        test_cases = [
            (1500.0, 500.0, "Excessive leverage"),        # D/E = 3.0 - excessive
            (1000.0, 500.0, "High leverage"),             # D/E = 2.0 - high
            (750.0, 500.0, "Moderate leverage"),          # D/E = 1.5 - moderate
            (250.0, 500.0, "Conservative leverage"),      # D/E = 0.5 - conservative
            (100.0, 500.0, "Very conservative"),          # D/E = 0.2 - very conservative
            (0.0, 500.0, "Very conservative"),            # D/E = 0.0 - minimal debt
        ]

        for debt, equity, expected_interpretation in test_cases:
            result = self.engine.calculate_debt_to_equity_ratio(debt, equity)
            self.assertTrue(result.is_valid)
            # Check if key term from expected interpretation appears in result
            key_term = expected_interpretation.split()[0].lower()
            self.assertIn(key_term, result.metadata['interpretation'].lower(),
                         msg=f"Expected '{key_term}' in interpretation for D/E={debt/equity:.2f}")

    def test_calculate_debt_to_equity_ratio_mathematical_accuracy(self):
        """Test mathematical accuracy of debt-to-equity ratio calculations"""
        test_scenarios = [
            # (total_debt, total_equity, expected_ratio)
            (200.0, 1000.0, 0.20),        # 20%
            (500.0, 1000.0, 0.50),        # 50%
            (1000.0, 1000.0, 1.00),       # 100%
            (1500.0, 1000.0, 1.50),       # 150%
            (2000.0, 1000.0, 2.00),       # 200%
            (0.0, 1000.0, 0.00),          # 0%
            (300.0, 600.0, 0.50),         # 50%
            (450.0, 750.0, 0.60),         # 60%
        ]

        for debt, equity, expected_ratio in test_scenarios:
            result = self.engine.calculate_debt_to_equity_ratio(debt, equity)
            self.assertTrue(result.is_valid)
            self.assertAlmostEqual(result.value, expected_ratio, places=3,
                                 msg=f"Debt-to-equity calculation failed for debt={debt}, equity={equity}")

    def test_calculate_debt_to_equity_ratio_financial_interpretation(self):
        """Test financial interpretation accuracy for various D/E scenarios"""
        # Very conservative company (D/E = 0.2)
        very_conservative_result = self.engine.calculate_debt_to_equity_ratio(100.0, 500.0)
        self.assertTrue(very_conservative_result.is_valid)
        self.assertIn("conservative", very_conservative_result.metadata['interpretation'].lower())

        # Conservative company (D/E = 0.6)
        conservative_result = self.engine.calculate_debt_to_equity_ratio(300.0, 500.0)
        self.assertTrue(conservative_result.is_valid)
        self.assertIn("conservative", conservative_result.metadata['interpretation'].lower())

        # Moderate leverage (D/E = 1.2)
        moderate_result = self.engine.calculate_debt_to_equity_ratio(600.0, 500.0)
        self.assertTrue(moderate_result.is_valid)
        self.assertIn("moderate", moderate_result.metadata['interpretation'].lower())

        # High leverage (D/E = 2.2)
        high_result = self.engine.calculate_debt_to_equity_ratio(1100.0, 500.0)
        self.assertTrue(high_result.is_valid)
        self.assertIn("high", high_result.metadata['interpretation'].lower())

        # Excessive leverage (D/E = 3.5)
        excessive_result = self.engine.calculate_debt_to_equity_ratio(1750.0, 500.0)
        self.assertTrue(excessive_result.is_valid)
        self.assertIn("excessive", excessive_result.metadata['interpretation'].lower())

    # =====================
    # Test Interest Coverage Ratio
    # =====================

    def test_calculate_interest_coverage_ratio_valid(self):
        """Test interest coverage ratio calculation with valid inputs"""
        result = self.engine.calculate_interest_coverage_ratio(
            ebit=200.0,
            interest_expense=40.0
        )

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, 5.0, places=2)  # 200 / 40 = 5.0

        # Verify metadata
        self.assertEqual(result.metadata['ebit'], 200.0)
        self.assertEqual(result.metadata['interest_expense'], 40.0)
        self.assertIn('Interest Coverage Ratio', result.metadata['calculation_method'])

    def test_calculate_interest_coverage_ratio_zero_interest_expense(self):
        """Test interest coverage ratio with zero interest expense"""
        result = self.engine.calculate_interest_coverage_ratio(
            ebit=200.0,
            interest_expense=0.0
        )

        self.assertFalse(result.is_valid)
        self.assertIn("Interest expense cannot be zero", result.error_message)

    def test_calculate_interest_coverage_ratio_none_inputs(self):
        """Test interest coverage ratio with None inputs"""
        result_none_ebit = self.engine.calculate_interest_coverage_ratio(
            ebit=None,
            interest_expense=40.0
        )
        self.assertFalse(result_none_ebit.is_valid)
        self.assertIn("cannot be None", result_none_ebit.error_message)

        result_none_interest = self.engine.calculate_interest_coverage_ratio(
            ebit=200.0,
            interest_expense=None
        )
        self.assertFalse(result_none_interest.is_valid)
        self.assertIn("cannot be None", result_none_interest.error_message)

    def test_calculate_interest_coverage_ratio_negative_ebit(self):
        """Test interest coverage ratio with negative EBIT"""
        result = self.engine.calculate_interest_coverage_ratio(
            ebit=-50.0,
            interest_expense=40.0
        )

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, -1.25, places=2)  # -50 / 40 = -1.25

        # Check for negative EBIT scenario flag
        self.assertTrue(result.metadata['negative_ebit_scenario'])
        self.assertIn("unable to cover interest", result.metadata['interpretation'].lower())

    def test_calculate_interest_coverage_ratio_negative_interest_expense(self):
        """Test interest coverage ratio with negative interest expense"""
        result = self.engine.calculate_interest_coverage_ratio(
            ebit=200.0,
            interest_expense=-40.0
        )

        self.assertTrue(result.is_valid)
        self.assertAlmostEqual(result.value, -5.0, places=2)  # 200 / -40 = -5.0

    def test_calculate_interest_coverage_ratio_low_coverage(self):
        """Test interest coverage ratio with low coverage scenarios"""
        # Very weak coverage (ICR = 0.8)
        result_very_weak = self.engine.calculate_interest_coverage_ratio(
            ebit=32.0,
            interest_expense=40.0
        )
        self.assertTrue(result_very_weak.is_valid)
        self.assertAlmostEqual(result_very_weak.value, 0.8, places=2)
        self.assertIn("Very weak", result_very_weak.metadata['interpretation'])

        # Weak coverage (ICR = 1.2)
        result_weak = self.engine.calculate_interest_coverage_ratio(
            ebit=48.0,
            interest_expense=40.0
        )
        self.assertTrue(result_weak.is_valid)
        self.assertAlmostEqual(result_weak.value, 1.2, places=2)
        self.assertIn("Weak", result_weak.metadata['interpretation'])

        # Moderate coverage (ICR = 2.0)
        result_moderate = self.engine.calculate_interest_coverage_ratio(
            ebit=80.0,
            interest_expense=40.0
        )
        self.assertTrue(result_moderate.is_valid)
        self.assertAlmostEqual(result_moderate.value, 2.0, places=2)
        self.assertIn("Moderate", result_moderate.metadata['interpretation'])

    def test_calculate_interest_coverage_ratio_high_coverage(self):
        """Test interest coverage ratio with high coverage scenarios"""
        # Strong coverage (ICR = 3.5)
        result_strong = self.engine.calculate_interest_coverage_ratio(
            ebit=140.0,
            interest_expense=40.0
        )
        self.assertTrue(result_strong.is_valid)
        self.assertAlmostEqual(result_strong.value, 3.5, places=2)
        self.assertIn("Strong", result_strong.metadata['interpretation'])

        # Excellent coverage (ICR = 8.0)
        result_excellent = self.engine.calculate_interest_coverage_ratio(
            ebit=320.0,
            interest_expense=40.0
        )
        self.assertTrue(result_excellent.is_valid)
        self.assertAlmostEqual(result_excellent.value, 8.0, places=2)
        self.assertIn("Excellent", result_excellent.metadata['interpretation'])

    def test_calculate_interest_coverage_ratio_interpretation_levels(self):
        """Test interest coverage ratio interpretation for different performance levels"""
        test_cases = [
            (400.0, 40.0, "Excellent"),     # 10.0 - excellent
            (140.0, 40.0, "Strong"),        # 3.5 - strong
            (80.0, 40.0, "Moderate"),       # 2.0 - moderate
            (48.0, 40.0, "Weak"),           # 1.2 - weak
            (32.0, 40.0, "Very weak"),      # 0.8 - very weak
            (-50.0, 40.0, "unable to cover"), # -1.25 - negative
        ]

        for ebit, interest_expense, expected_interpretation in test_cases:
            result = self.engine.calculate_interest_coverage_ratio(
                ebit=ebit,
                interest_expense=interest_expense
            )
            self.assertTrue(result.is_valid)
            self.assertIn(expected_interpretation.lower(),
                         result.metadata['interpretation'].lower())

    def test_calculate_interest_coverage_ratio_mathematical_accuracy(self):
        """Test mathematical accuracy of interest coverage ratio calculations"""
        test_scenarios = [
            # (ebit, interest_expense, expected_ratio)
            (200.0, 40.0, 5.0),      # Strong coverage
            (100.0, 50.0, 2.0),      # Moderate coverage
            (75.0, 50.0, 1.5),       # Weak coverage
            (300.0, 100.0, 3.0),     # Strong coverage
            (150.0, 25.0, 6.0),      # Excellent coverage
            (50.0, 100.0, 0.5),      # Very weak coverage
        ]

        for ebit, interest_expense, expected_ratio in test_scenarios:
            result = self.engine.calculate_interest_coverage_ratio(
                ebit=ebit,
                interest_expense=interest_expense
            )
            self.assertTrue(result.is_valid)
            self.assertAlmostEqual(result.value, expected_ratio, places=3,
                                 msg=f"Interest coverage calculation failed for ebit={ebit}, interest_expense={interest_expense}")

    def test_calculate_interest_coverage_ratio_financial_interpretation(self):
        """Test financial interpretation accuracy for various coverage scenarios"""
        # Excellent coverage company (ICR = 10.0)
        excellent_result = self.engine.calculate_interest_coverage_ratio(400.0, 40.0)
        self.assertTrue(excellent_result.is_valid)
        self.assertIn("excellent", excellent_result.metadata['interpretation'].lower())

        # Strong coverage company (ICR = 4.0)
        strong_result = self.engine.calculate_interest_coverage_ratio(160.0, 40.0)
        self.assertTrue(strong_result.is_valid)
        self.assertIn("strong", strong_result.metadata['interpretation'].lower())

        # Moderate coverage company (ICR = 2.0)
        moderate_result = self.engine.calculate_interest_coverage_ratio(80.0, 40.0)
        self.assertTrue(moderate_result.is_valid)
        self.assertIn("moderate", moderate_result.metadata['interpretation'].lower())

        # Weak coverage company (ICR = 1.2)
        weak_result = self.engine.calculate_interest_coverage_ratio(48.0, 40.0)
        self.assertTrue(weak_result.is_valid)
        self.assertIn("weak", weak_result.metadata['interpretation'].lower())

        # Very weak coverage company (ICR = 0.6)
        very_weak_result = self.engine.calculate_interest_coverage_ratio(24.0, 40.0)
        self.assertTrue(very_weak_result.is_valid)
        self.assertIn("very weak", very_weak_result.metadata['interpretation'].lower())

        # Negative EBIT scenario
        negative_result = self.engine.calculate_interest_coverage_ratio(-50.0, 40.0)
        self.assertTrue(negative_result.is_valid)
        self.assertIn("unable to cover", negative_result.metadata['interpretation'].lower())


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)