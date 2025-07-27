"""
API testing helpers for mocking external API calls and avoiding rate limiting.

This module centralizes API mocking logic to eliminate duplicate API testing
patterns across multiple test files.
"""

import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np


class APITestHelper:
    """Helper class for API-related testing operations"""

    @staticmethod
    def create_mock_responses() -> Dict[str, Any]:
        """
        Create comprehensive mock responses for yfinance API

        Returns:
            Dict[str, Any]: Mock responses for different API calls
        """
        return {
            'ticker_info': {
                'symbol': 'TEST',
                'longName': 'Test Company Inc',
                'currentPrice': 150.0,
                'marketCap': 15000000000,
                'sharesOutstanding': 100000000,
                'enterpriseValue': 16000000000,
                'totalDebt': 2000000000,
                'totalCash': 1000000000,
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Software',
                'fullTimeEmployees': 50000,
            },
            'history_data': pd.DataFrame(
                {
                    'Open': [145, 148, 152, 149, 151],
                    'High': [149, 153, 156, 154, 155],
                    'Low': [143, 146, 150, 147, 149],
                    'Close': [148, 152, 154, 151, 153],
                    'Volume': [1000000, 1200000, 800000, 1500000, 900000],
                },
                index=pd.date_range('2024-01-01', periods=5, freq='D'),
            ),
            'financials': pd.DataFrame(
                {
                    'Total Revenue': [10000000000, 11000000000, 12000000000],
                    'Net Income': [1500000000, 1800000000, 2200000000],
                    'Operating Income': [2000000000, 2500000000, 3000000000],
                },
                index=pd.to_datetime(['2022-12-31', '2023-12-31', '2024-12-31']),
            ),
            'balance_sheet': pd.DataFrame(
                {
                    'Total Assets': [20000000000, 22000000000, 24000000000],
                    'Current Assets': [5000000000, 5500000000, 6000000000],
                    'Current Liabilities': [3000000000, 3200000000, 3500000000],
                    'Total Debt': [2000000000, 2200000000, 2400000000],
                    'Cash And Cash Equivalents': [1000000000, 1200000000, 1400000000],
                },
                index=pd.to_datetime(['2022-12-31', '2023-12-31', '2024-12-31']),
            ),
            'cashflow': pd.DataFrame(
                {
                    'Operating Cash Flow': [2500000000, 2800000000, 3200000000],
                    'Capital Expenditures': [-800000000, -900000000, -1000000000],
                    'Free Cash Flow': [1700000000, 1900000000, 2200000000],
                    'Financing Cash Flow': [-500000000, -600000000, -700000000],
                },
                index=pd.to_datetime(['2022-12-31', '2023-12-31', '2024-12-31']),
            ),
        }

    @staticmethod
    def mock_yfinance_ticker(
        ticker: str = 'TEST', mock_responses: Optional[Dict[str, Any]] = None
    ) -> Mock:
        """
        Create a mock yfinance Ticker object

        Args:
            ticker (str): Ticker symbol
            mock_responses (Optional[Dict[str, Any]]): Custom mock responses

        Returns:
            Mock: Mock Ticker object
        """
        if mock_responses is None:
            mock_responses = APITestHelper.create_mock_responses()

        mock_ticker = Mock(spec=yf.Ticker)

        # Set up info property
        mock_ticker.info = mock_responses['ticker_info']

        # Set up history method
        mock_ticker.history.return_value = mock_responses['history_data']

        # Set up financials properties
        mock_ticker.financials = mock_responses['financials']
        mock_ticker.balance_sheet = mock_responses['balance_sheet']
        mock_ticker.cashflow = mock_responses['cashflow']

        # Set up quarterly data (simplified versions)
        mock_ticker.quarterly_financials = mock_responses['financials'].head(4)
        mock_ticker.quarterly_balance_sheet = mock_responses['balance_sheet'].head(4)
        mock_ticker.quarterly_cashflow = mock_responses['cashflow'].head(4)

        return mock_ticker

    @staticmethod
    def patch_yfinance(mock_responses: Optional[Dict[str, Any]] = None):
        """
        Context manager to patch yfinance for testing

        Args:
            mock_responses (Optional[Dict[str, Any]]): Custom mock responses

        Returns:
            Context manager for patching yfinance
        """

        def mock_ticker_constructor(ticker_symbol):
            return APITestHelper.mock_yfinance_ticker(ticker_symbol, mock_responses)

        return patch('yfinance.Ticker', side_effect=mock_ticker_constructor)

    @staticmethod
    def simulate_api_rate_limit():
        """
        Simulate API rate limiting for testing rate limit handling

        Returns:
            Mock that raises rate limit exceptions
        """

        def rate_limit_side_effect(*args, **kwargs):
            raise Exception("Too Many Requests (429)")

        return rate_limit_side_effect

    @staticmethod
    def simulate_api_timeout():
        """
        Simulate API timeout for testing timeout handling

        Returns:
            Mock that raises timeout exceptions
        """

        def timeout_side_effect(*args, **kwargs):
            raise TimeoutError("Request timed out")

        return timeout_side_effect

    @staticmethod
    def simulate_network_error():
        """
        Simulate network errors for testing error handling

        Returns:
            Mock that raises network exceptions
        """

        def network_error_side_effect(*args, **kwargs):
            raise ConnectionError("Network connection failed")

        return network_error_side_effect

    @staticmethod
    def create_mock_ticker_list(tickers: List[str]) -> Dict[str, Mock]:
        """
        Create multiple mock tickers for testing

        Args:
            tickers (List[str]): List of ticker symbols

        Returns:
            Dict[str, Mock]: Dictionary of ticker symbol to mock ticker
        """
        mock_tickers = {}

        for ticker in tickers:
            # Create unique mock data for each ticker
            base_responses = APITestHelper.create_mock_responses()

            # Modify some values to make each ticker unique
            price_multiplier = hash(ticker) % 100 / 100.0 + 0.5  # 0.5 to 1.5
            base_responses['ticker_info']['currentPrice'] *= price_multiplier
            base_responses['ticker_info']['symbol'] = ticker
            base_responses['ticker_info']['longName'] = f'{ticker} Corporation'

            # Scale historical data
            for col in base_responses['history_data'].columns:
                if col != 'Volume':
                    base_responses['history_data'][col] *= price_multiplier

            mock_tickers[ticker] = APITestHelper.mock_yfinance_ticker(ticker, base_responses)

        return mock_tickers

    @staticmethod
    def validate_api_call_count(mock_object: Mock, expected_calls: int) -> bool:
        """
        Validate that an API was called the expected number of times

        Args:
            mock_object (Mock): Mock object to check
            expected_calls (int): Expected number of calls

        Returns:
            bool: True if call count matches expectation
        """
        return mock_object.call_count == expected_calls

    @staticmethod
    def create_market_data_equality_test_data() -> Dict[str, Any]:
        """
        Create test data for market data equality tests

        Returns:
            Dict[str, Any]: Test data for equality comparisons
        """
        return {
            'companies': ['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
            'expected_fields': [
                'currentPrice',
                'marketCap',
                'sharesOutstanding',
                'enterpriseValue',
                'totalDebt',
                'totalCash',
            ],
            'tolerance': 0.01,  # 1% tolerance for floating point comparisons
            'max_retries': 3,
            'retry_delay': 1.0,  # seconds
        }

    @staticmethod
    def mock_rate_limited_response(calls_before_limit: int = 5):
        """
        Create a mock that succeeds for a number of calls then rate limits

        Args:
            calls_before_limit (int): Number of successful calls before rate limiting

        Returns:
            Mock object that simulates rate limiting
        """
        call_count = {'count': 0}

        def side_effect(*args, **kwargs):
            call_count['count'] += 1
            if call_count['count'] <= calls_before_limit:
                return APITestHelper.create_mock_responses()['ticker_info']
            else:
                raise Exception("Too Many Requests (429)")

        mock = Mock()
        mock.info = property(lambda self: side_effect())
        return mock

    @staticmethod
    def create_api_behavior_test_scenarios() -> List[Dict[str, Any]]:
        """
        Create test scenarios for API behavior testing

        Returns:
            List[Dict[str, Any]]: List of test scenarios
        """
        return [
            {
                'name': 'successful_call',
                'mock_func': lambda: APITestHelper.mock_yfinance_ticker(),
                'expected_result': 'success',
                'should_retry': False,
            },
            {
                'name': 'rate_limited',
                'mock_func': APITestHelper.simulate_api_rate_limit,
                'expected_result': 'rate_limit_error',
                'should_retry': True,
            },
            {
                'name': 'timeout',
                'mock_func': APITestHelper.simulate_api_timeout,
                'expected_result': 'timeout_error',
                'should_retry': True,
            },
            {
                'name': 'network_error',
                'mock_func': APITestHelper.simulate_network_error,
                'expected_result': 'network_error',
                'should_retry': True,
            },
        ]

    @staticmethod
    def assert_api_data_consistency(
        data1: Dict[str, Any], data2: Dict[str, Any], tolerance: float = 0.01
    ) -> List[str]:
        """
        Assert that two sets of API data are consistent within tolerance

        Args:
            data1 (Dict[str, Any]): First dataset
            data2 (Dict[str, Any]): Second dataset
            tolerance (float): Tolerance for numeric comparisons

        Returns:
            List[str]: List of inconsistencies found
        """
        inconsistencies = []

        # Check that both datasets have the same keys
        if set(data1.keys()) != set(data2.keys()):
            missing_in_1 = set(data2.keys()) - set(data1.keys())
            missing_in_2 = set(data1.keys()) - set(data2.keys())

            if missing_in_1:
                inconsistencies.append(f"Keys missing in first dataset: {missing_in_1}")
            if missing_in_2:
                inconsistencies.append(f"Keys missing in second dataset: {missing_in_2}")

        # Compare common keys
        common_keys = set(data1.keys()) & set(data2.keys())
        for key in common_keys:
            val1, val2 = data1[key], data2[key]

            # Handle numeric comparisons
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if abs(val1 - val2) > tolerance * max(abs(val1), abs(val2), 1):
                    inconsistencies.append(f"Numeric value mismatch for '{key}': {val1} vs {val2}")
            # Handle string comparisons
            elif isinstance(val1, str) and isinstance(val2, str):
                if val1 != val2:
                    inconsistencies.append(
                        f"String value mismatch for '{key}': '{val1}' vs '{val2}'"
                    )
            # Handle None comparisons
            elif val1 != val2:
                inconsistencies.append(f"Value mismatch for '{key}': {val1} vs {val2}")

        return inconsistencies
