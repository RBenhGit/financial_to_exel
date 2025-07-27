"""
Test cases for Tel Aviv Stock Exchange (TASE) support

Tests the currency handling and valuation logic for Israeli stocks.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator


class TestTASESupport(unittest.TestCase):
    """Test TASE stock support functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_company_folder = "/mock/tase_company"
        self.calculator = FinancialCalculator(self.mock_company_folder)

    def test_currency_conversion_utilities(self):
        """Test Agorot/Shekel conversion functions"""
        # Test Agorot to Shekel conversion
        agorot_value = 1000  # 1000 Agorot
        expected_shekels = 10.0  # 10 Shekels
        result = self.calculator.convert_agorot_to_shekel(agorot_value)
        self.assertEqual(result, expected_shekels)

        # Test Shekel to Agorot conversion
        shekel_value = 5.50  # 5.50 Shekels
        expected_agorot = 550  # 550 Agorot
        result = self.calculator.convert_shekel_to_agorot(shekel_value)
        self.assertEqual(result, expected_agorot)

        # Test None handling
        self.assertIsNone(self.calculator.convert_agorot_to_shekel(None))
        self.assertIsNone(self.calculator.convert_shekel_to_agorot(None))

    def test_tase_stock_detection(self):
        """Test TASE stock detection logic"""
        # Test .TA suffix detection
        test_cases = [
            ("TEVA.TA", True),
            ("CHKP.TA", True),
            ("MSFT", False),
            ("AAPL", False),
        ]

        for ticker, expected_is_tase in test_cases:
            # Reset calculator state
            self.calculator = FinancialCalculator(self.mock_company_folder)
            self.calculator.ticker_symbol = ticker

            with patch('yfinance.Ticker') as mock_yf_ticker:
                # Mock yfinance Ticker and info
                mock_ticker_instance = Mock()
                mock_yf_ticker.return_value = mock_ticker_instance
                mock_ticker_instance.info = {
                    'currentPrice': 1500.0,
                    'sharesOutstanding': 1000000,
                    'marketCap': 1500000000,
                    'longName': 'Test Company',
                    'currency': 'ILS' if expected_is_tase else 'USD',
                    'financialCurrency': 'ILS' if expected_is_tase else 'USD',
                }

                # Call the actual fetch_market_data method
                result = self.calculator.fetch_market_data()

                # Check results
                if result:  # Only check if fetch succeeded
                    self.assertEqual(result['is_tase_stock'], expected_is_tase)
                    self.assertEqual(self.calculator.is_tase_stock, expected_is_tase)

    def test_tase_price_handling(self):
        """Test TASE stock price handling"""
        # Set up TASE stock
        self.calculator.ticker_symbol = "TEVA.TA"
        self.calculator.current_stock_price = 1500.0  # 1500 Agorot
        self.calculator.is_tase_stock = True
        self.calculator.currency = "ILS"

        # Test price in Shekels conversion
        price_shekels = self.calculator.get_price_in_shekels()
        self.assertEqual(price_shekels, 15.0)  # 1500 Agorot = 15 Shekels

        # Test price in Agorot
        price_agorot = self.calculator.get_price_in_agorot()
        self.assertEqual(price_agorot, 1500.0)

        # Test non-TASE stock
        self.calculator.is_tase_stock = False
        self.calculator.currency = "USD"

        price_usd = self.calculator.get_price_in_shekels()
        self.assertEqual(price_usd, 1500.0)  # Returns original price for non-TASE

        price_agorot_non_tase = self.calculator.get_price_in_agorot()
        self.assertIsNone(price_agorot_non_tase)  # Returns None for non-TASE

    def test_dcf_currency_handling(self):
        """Test DCF valuation with TASE currency handling"""
        # Set up mock financial calculator with TASE stock
        self.calculator.ticker_symbol = "TEVA.TA"
        self.calculator.current_stock_price = 2000.0  # 2000 Agorot
        self.calculator.is_tase_stock = True
        self.calculator.currency = "ILS"
        self.calculator.shares_outstanding = 1000000000  # 1B shares

        # Mock FCF results (in millions ILS)
        self.calculator.fcf_results = {
            'FCFE': [100, 110, 120, 130, 140]  # 5 years of FCF in millions ILS
        }

        # Create DCF valuator
        valuator = DCFValuator(self.calculator)

        # Mock market data
        with patch.object(valuator, '_get_market_data') as mock_market_data:
            mock_market_data.return_value = {
                'current_price': 2000.0,  # Agorot
                'shares_outstanding': 1000000000,
                'market_cap': 2000000000000,  # Market cap in Agorot
                'ticker_symbol': 'TEVA.TA',
                'currency': 'ILS',
                'is_tase_stock': True,
            }

            # Calculate DCF
            result = valuator.calculate_dcf_projections()

            # Check that result contains TASE-specific information
            self.assertTrue(result.get('is_tase_stock', False))
            self.assertEqual(result.get('currency'), 'ILS')

            # Check that per-share values are provided in both currencies
            self.assertIn('value_per_share_agorot', result)
            self.assertIn('value_per_share_shekels', result)

            # Verify currency conversion
            agorot_value = result.get('value_per_share_agorot', 0)
            shekel_value = result.get('value_per_share_shekels', 0)
            self.assertAlmostEqual(agorot_value / 100.0, shekel_value, places=2)

    def test_currency_info_retrieval(self):
        """Test currency information retrieval"""
        # Test TASE stock
        self.calculator.ticker_symbol = "CHKP.TA"
        self.calculator.current_stock_price = 5000.0  # 5000 Agorot
        self.calculator.is_tase_stock = True
        self.calculator.currency = "ILS"

        currency_info = self.calculator.get_currency_info()

        self.assertTrue(currency_info['is_tase_stock'])
        self.assertEqual(currency_info['currency'], 'ILS')
        self.assertEqual(currency_info['price_in_agorot'], 5000.0)
        self.assertEqual(currency_info['price_in_shekels'], 50.0)
        self.assertIn('currency_note', currency_info)

        # Test non-TASE stock
        self.calculator.is_tase_stock = False
        self.calculator.currency = "USD"

        currency_info = self.calculator.get_currency_info()

        self.assertFalse(currency_info['is_tase_stock'])
        self.assertEqual(currency_info['currency'], 'USD')
        self.assertNotIn('price_in_agorot', currency_info)

    def test_financial_values_normalization(self):
        """Test financial values normalization for TASE stocks"""
        # Test with TASE stock
        self.calculator.is_tase_stock = True

        # Mock financial values in millions ILS
        financial_values = [100, 110, 120, 130]  # millions ILS

        normalized = self.calculator.normalize_financial_values_for_tase(financial_values)

        # For TASE stocks, values should remain the same (already in correct units)
        self.assertEqual(normalized, financial_values)

        # Test with non-TASE stock
        self.calculator.is_tase_stock = False

        normalized = self.calculator.normalize_financial_values_for_tase(financial_values)

        # For non-TASE stocks, values should remain unchanged
        self.assertEqual(normalized, financial_values)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
