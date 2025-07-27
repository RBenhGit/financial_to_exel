#!/usr/bin/env python3
"""
Unit tests to verify FCF and DCF calculations use consistent units
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator


class TestUnitsConsistency(unittest.TestCase):
    """Test that FCF and DCF calculations use consistent units"""

    def setUp(self):
        """Set up test financial calculator"""
        self.calc = FinancialCalculator(None)

    def test_financial_scale_factor_is_one(self):
        """Test that financial scale factor is 1 to keep values in millions"""
        self.assertEqual(self.calc.financial_scale_factor, 1)

    def test_fcf_values_remain_in_millions(self):
        """Test that FCF values are kept in millions after scaling"""
        # Mock FCF data in millions
        test_fcf = [45000, 50000, 55000]  # $45M, $50M, $55M

        # Apply scaling
        scaled_fcf = [value * self.calc.financial_scale_factor for value in test_fcf]

        # Should remain the same (scale factor = 1)
        self.assertEqual(scaled_fcf, test_fcf)

    def test_dcf_calculation_with_millions_input(self):
        """Test DCF calculation works correctly with millions-based input"""
        # Set up mock data
        self.calc.fcf_results = {'FCFE': [50000]}  # $50M
        self.calc.ticker_symbol = 'TEST'
        self.calc.shares_outstanding = 1000  # 1B shares (in millions)
        self.calc.current_stock_price = 100
        self.calc.market_cap = 100000  # $100M market cap

        # Mock market data fetch
        def mock_fetch():
            return {
                'shares_outstanding': 1000000000,  # 1B shares actual
                'current_price': 100,
                'market_cap': 100000000000,  # $100B actual
                'ticker_symbol': 'TEST',
                'currency': 'USD',
                'is_tase_stock': False,
            }

        self.calc.fetch_market_data = mock_fetch

        # Create DCF valuator and calculate
        dcf = DCFValuator(self.calc)
        result = dcf.calculate_dcf_projections()

        # Basic validation
        self.assertIsNotNone(result)
        self.assertIn('equity_value', result)
        self.assertIn('value_per_share', result)

        # Value should be reasonable (not astronomical)
        equity_value = result.get('equity_value', 0)
        value_per_share = result.get('value_per_share', 0)

        # Equity value should be less than $100 trillion (avoiding old bug)
        self.assertLess(equity_value, 100_000_000)  # Less than $100T

        # Value per share should be reasonable
        self.assertGreater(value_per_share, 10)  # Greater than $10
        self.assertLess(value_per_share, 10000)  # Less than $10,000


if __name__ == '__main__':
    unittest.main()
