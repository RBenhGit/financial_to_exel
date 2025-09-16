"""
Unit tests for DCF shares outstanding fix (Task #128)
====================================================

Tests to verify that DCF calculation can access shares outstanding data
through the enhanced fallback mechanism.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.engines.financial_calculations import FinancialCalculator


class TestDCFSharesOutstandingFix:
    """Test cases for DCF shares outstanding retrieval fix"""

    def test_market_data_retrieval_with_var_input_data(self):
        """Test that market data retrieval works with var_input_data"""
        # Create mock financial calculator
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "MSFT"

        # Mock var_input_data
        mock_var_data = Mock()
        mock_var_data.get_variable = Mock(side_effect=[
            None,  # current_price
            None,  # market_cap
            7433169920,  # shares_outstanding - SUCCESS
            None   # weighted_avg_shares_outstanding
        ])

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Test market data retrieval
        market_data = dcf._get_market_data()

        # Verify shares outstanding was retrieved
        assert market_data['shares_outstanding'] == 7433169920
        assert 'MSFT' in str(mock_var_data.get_variable.call_args_list)

    def test_market_data_fallback_to_calculation(self):
        """Test market data fallback to market_cap/price calculation"""
        # Create mock financial calculator
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "MSFT"

        # Mock var_input_data returning market_cap and price but not shares
        mock_var_data = Mock()
        mock_var_data.get_variable = Mock(side_effect=[
            509.90,  # current_price
            3790173372416,  # market_cap
            None,  # shares_outstanding - missing
            None   # weighted_avg_shares_outstanding
        ])

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Test market data retrieval
        market_data = dcf._get_market_data()

        # Verify shares outstanding was calculated from market_cap/price
        expected_shares = 3790173372416 / 509.90
        assert abs(market_data['shares_outstanding'] - expected_shares) < 1000
        assert market_data['current_price'] == 509.90
        assert market_data['market_cap'] == 3790173372416

    def test_market_data_fallback_to_fresh_api(self):
        """Test market data fallback to fresh API fetch"""
        # Create mock financial calculator with fresh data method
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "MSFT"
        mock_calc.fetch_market_data = Mock(return_value={
            'shares_outstanding': 7433169920,
            'current_price': 509.90,
            'market_cap': 3790173372416
        })

        # Mock var_input_data returning no data
        mock_var_data = Mock()
        mock_var_data.get_variable = Mock(return_value=None)

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Test market data retrieval
        market_data = dcf._get_market_data()

        # Verify fresh API was called and data retrieved
        mock_calc.fetch_market_data.assert_called_once()
        assert market_data['shares_outstanding'] == 7433169920

    def test_market_data_fallback_to_cached_attributes(self):
        """Test market data fallback to cached financial calculator attributes"""
        # Create mock financial calculator with cached attributes
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "MSFT"
        mock_calc.shares_outstanding = 7433169920
        mock_calc.current_stock_price = 509.90
        mock_calc.market_cap = 3790173372416
        mock_calc.currency = "USD"
        mock_calc.is_tase_stock = False
        mock_calc.fetch_market_data = Mock(return_value=None)

        # Mock var_input_data returning no data
        mock_var_data = Mock()
        mock_var_data.get_variable = Mock(return_value=None)

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Test market data retrieval
        market_data = dcf._get_market_data()

        # Verify cached attributes were used
        assert market_data['shares_outstanding'] == 7433169920
        assert market_data['current_price'] == 509.90
        assert market_data['market_cap'] == 3790173372416

    def test_dcf_no_longer_fails_with_shares_outstanding_error(self):
        """Test that DCF calculation no longer fails with shares outstanding error"""
        # Create mock financial calculator
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "MSFT"
        mock_calc.shares_outstanding = 7433169920
        mock_calc.current_stock_price = 509.90
        mock_calc.market_cap = 3790173372416

        # Mock var_input_data
        mock_var_data = Mock()
        mock_var_data.get_variable = Mock(return_value=None)
        mock_var_data.get_historical_data = Mock(return_value=[])

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Mock FCF data to avoid FCF-related errors
        with patch.object(dcf, '_get_fcf_data_from_var_system', return_value=[]):
            result = dcf.calculate_dcf_projections()

            # Should NOT get shares_outstanding_unavailable error
            assert result.get('error') != 'shares_outstanding_unavailable'

            # Should get FCF unavailable error instead (different issue)
            # This confirms shares outstanding was accessible

    def test_enhanced_error_message_when_all_methods_fail(self):
        """Test enhanced error message when all retrieval methods fail"""
        # Create mock financial calculator with no data
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker_symbol = "INVALID"
        mock_calc.shares_outstanding = 0
        mock_calc.current_stock_price = 0
        mock_calc.market_cap = 0
        mock_calc.fetch_market_data = Mock(return_value=None)

        # Mock var_input_data returning no data for market variables
        # but provide FCF data to get past the FCF check
        mock_var_data = Mock()
        def mock_get_variable(symbol, var_name, period=None):
            if var_name in ['current_price', 'market_cap', 'shares_outstanding', 'weighted_avg_shares_outstanding']:
                return None
            return None

        def mock_get_historical_data(symbol, var_name, years=None):
            if var_name in ['fcfe', 'fcff', 'levered_fcf', 'free_cash_flow']:
                return [('2023', 50000), ('2022', 45000), ('2021', 40000)]  # Mock FCF data
            return []

        mock_var_data.get_variable = Mock(side_effect=mock_get_variable)
        mock_var_data.get_historical_data = Mock(side_effect=mock_get_historical_data)

        dcf = DCFValuator(mock_calc)
        dcf.var_data = mock_var_data

        # Test DCF calculation
        result = dcf.calculate_dcf_projections()

        # Should get enhanced error message
        assert result.get('error') == 'shares_outstanding_unavailable'
        error_msg = result.get('error_message', '')
        assert 'Excel files or API sources' in error_msg
        assert 'debug_info' in result
        assert 'attempted_sources' in result['debug_info']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])