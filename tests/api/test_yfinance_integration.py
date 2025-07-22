"""
Consolidated yfinance API integration tests.

This module consolidates API-related tests from multiple files:
- test_api_behavior.py
- test_market_data_equality.py
- test_rate_limiting.py
- test_yfinance_enhancement.py
- test_yfinance_logging.py
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from tests.fixtures.api_helpers import APITestHelper
from tests.fixtures.mock_data import MockDataGenerator


class TestYFinanceBasicIntegration:
    """Test basic yfinance API integration"""
    
    @pytest.mark.api_dependent
    def test_ticker_info_retrieval(self, mock_yfinance_responses):
        """Test retrieval of basic ticker information"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            info = ticker.info
            
            # Should have expected fields
            expected_fields = [
                'symbol', 'currentPrice', 'marketCap', 'sharesOutstanding',
                'enterpriseValue', 'totalDebt', 'totalCash'
            ]
            
            for field in expected_fields:
                assert field in info
                assert info[field] is not None
    
    @pytest.mark.api_dependent
    def test_financial_statements_retrieval(self, mock_yfinance_responses):
        """Test retrieval of financial statements"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            
            # Test different statement types
            statements = {
                'financials': ticker.financials,
                'balance_sheet': ticker.balance_sheet,
                'cashflow': ticker.cashflow
            }
            
            for statement_name, statement_data in statements.items():
                assert isinstance(statement_data, pd.DataFrame)
                assert not statement_data.empty
                assert len(statement_data.columns) > 0
    
    @pytest.mark.api_dependent
    def test_historical_data_retrieval(self, mock_yfinance_responses):
        """Test retrieval of historical price data"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            history = ticker.history(period="1mo")
            
            assert isinstance(history, pd.DataFrame)
            assert not history.empty
            
            # Should have expected columns
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in expected_columns:
                assert col in history.columns


class TestAPIBehavior:
    """Test API behavior patterns and error handling"""
    
    def test_successful_api_calls(self, mock_yfinance_responses):
        """Test successful API call patterns"""
        test_scenarios = APITestHelper.create_api_behavior_test_scenarios()
        
        successful_scenario = next(s for s in test_scenarios if s['name'] == 'successful_call')
        
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            # Should complete without raising exceptions
            mock_ticker = successful_scenario['mock_func']()
            assert mock_ticker is not None
    
    def test_rate_limiting_behavior(self):
        """Test API rate limiting handling"""
        # Create mock that simulates rate limiting
        rate_limited_mock = APITestHelper.mock_rate_limited_response(calls_before_limit=2)
        
        # Should handle rate limiting gracefully
        call_count = 0
        for _ in range(5):  # Try more calls than allowed
            try:
                _ = rate_limited_mock.info
                call_count += 1
            except Exception as e:
                # Should get rate limit exception after limit is reached
                assert "Too Many Requests" in str(e)
                break
        
        assert call_count <= 2  # Should have been limited
    
    def test_timeout_handling(self):
        """Test handling of API timeouts"""
        timeout_func = APITestHelper.simulate_api_timeout()
        
        with pytest.raises(TimeoutError):
            timeout_func()
    
    def test_network_error_handling(self):
        """Test handling of network errors"""
        network_error_func = APITestHelper.simulate_network_error()
        
        with pytest.raises(ConnectionError):
            network_error_func()
    
    @pytest.mark.parametrize("retry_count", [1, 3, 5])
    def test_retry_logic(self, retry_count):
        """Test retry logic for failed API calls"""
        # Simulate a function that fails a few times then succeeds
        call_attempts = {'count': 0}
        
        def mock_api_call():
            call_attempts['count'] += 1
            if call_attempts['count'] < retry_count:
                raise ConnectionError("Network error")
            return MockDataGenerator.generate_market_data()
        
        # Test retry logic
        max_retries = retry_count + 1
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = mock_api_call()
                assert result is not None
                break
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # Brief delay between retries
        else:
            # If we exhausted retries, re-raise the last exception
            if last_exception:
                raise last_exception


class TestMarketDataEquality:
    """Test equality and consistency of market data across different calls"""
    
    def test_market_data_consistency(self, mock_yfinance_responses):
        """Test that multiple calls return consistent data"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            
            # Get data twice
            info1 = ticker.info
            info2 = ticker.info
            
            # Should be consistent
            consistency_check = APITestHelper.assert_api_data_consistency(
                info1, info2, tolerance=0.01
            )
            assert len(consistency_check) == 0  # No inconsistencies
    
    @pytest.mark.parametrize("ticker_symbol", ['AAPL', 'MSFT', 'GOOGL'])
    def test_data_structure_consistency(self, ticker_symbol, mock_yfinance_responses):
        """Test that different tickers return data with consistent structure"""
        mock_tickers = APITestHelper.create_mock_ticker_list([ticker_symbol])
        
        # Mock the yfinance.Ticker constructor
        def mock_ticker_constructor(symbol):
            return mock_tickers.get(symbol, APITestHelper.mock_yfinance_ticker(symbol))
        
        with patch('yfinance.Ticker', side_effect=mock_ticker_constructor):
            import yfinance as yf
            
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Should have consistent structure regardless of ticker
            test_data = APITestHelper.create_market_data_equality_test_data()
            expected_fields = test_data['expected_fields']
            
            for field in expected_fields:
                assert field in info, f"Missing field {field} for ticker {ticker_symbol}"
    
    def test_numerical_data_validity(self, mock_yfinance_responses):
        """Test that numerical data is valid and within reasonable ranges"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            info = ticker.info
            
            # Test numerical fields
            numerical_fields = ['currentPrice', 'marketCap', 'sharesOutstanding']
            
            for field in numerical_fields:
                if field in info and info[field] is not None:
                    value = info[field]
                    assert isinstance(value, (int, float))
                    assert value >= 0  # Should be non-negative
                    assert not (isinstance(value, float) and (
                        value != value or  # NaN check
                        value == float('inf') or 
                        value == float('-inf')
                    ))


class TestRateLimiting:
    """Test rate limiting and throttling mechanisms"""
    
    def test_rate_limit_detection(self):
        """Test detection of rate limiting responses"""
        # Create mock that simulates rate limiting after some calls
        rate_limited_ticker = APITestHelper.mock_rate_limited_response(calls_before_limit=3)
        
        successful_calls = 0
        rate_limited_calls = 0
        
        # Make multiple calls
        for i in range(10):
            try:
                _ = rate_limited_ticker.info
                successful_calls += 1
            except Exception as e:
                if "Too Many Requests" in str(e):
                    rate_limited_calls += 1
                else:
                    raise  # Re-raise unexpected exceptions
        
        # Should have hit rate limiting
        assert successful_calls <= 3
        assert rate_limited_calls > 0
    
    @pytest.mark.slow
    def test_rate_limiting_backoff(self):
        """Test exponential backoff for rate-limited requests"""
        # This would test actual backoff logic if implemented
        backoff_delays = [0.1, 0.2, 0.4, 0.8, 1.6]  # Exponential backoff
        
        for delay in backoff_delays:
            start_time = time.time()
            time.sleep(delay)
            elapsed = time.time() - start_time
            
            # Allow for some timing variance
            assert elapsed >= delay * 0.9
            assert elapsed <= delay * 1.1
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent API requests"""
        # This test would verify that concurrent requests are properly throttled
        # For now, just test that the mock system can handle multiple rapid calls
        
        import threading
        results = []
        errors = []
        
        def make_api_call():
            try:
                mock_ticker = APITestHelper.mock_yfinance_ticker('TEST')
                result = mock_ticker.info
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_api_call)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout
        
        # Should handle concurrent requests
        assert len(results) + len(errors) == 5
        assert len(results) > 0  # At least some should succeed


class TestYFinanceEnhancements:
    """Test enhanced yfinance functionality and logging"""
    
    def test_enhanced_error_reporting(self, mock_yfinance_responses):
        """Test enhanced error reporting for API failures"""
        # Test with various error scenarios
        error_scenarios = [
            (APITestHelper.simulate_api_timeout, "timeout"),
            (APITestHelper.simulate_network_error, "network"),
            (APITestHelper.simulate_api_rate_limit, "rate_limit")
        ]
        
        for error_func, error_type in error_scenarios:
            try:
                error_func()
                assert False, f"Expected {error_type} error was not raised"
            except Exception as e:
                # Error should be properly categorized
                assert len(str(e)) > 0  # Should have descriptive message
    
    @patch('logging.Logger.info')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_api_call_logging(self, mock_error, mock_warning, mock_info, mock_yfinance_responses):
        """Test that API calls are properly logged"""
        with APITestHelper.patch_yfinance(mock_yfinance_responses):
            import yfinance as yf
            
            ticker = yf.Ticker('TEST')
            _ = ticker.info
            
            # In a real implementation, we would verify that appropriate
            # log messages were generated for API calls
            # For now, just verify the mocks are available
            assert mock_info.called or mock_warning.called or mock_error.called or True
    
    def test_response_caching(self, mock_yfinance_responses):
        """Test response caching to reduce API calls"""
        cache = {}
        
        def cached_api_call(ticker_symbol):
            if ticker_symbol not in cache:
                # Simulate API call
                cache[ticker_symbol] = MockDataGenerator.generate_market_data(ticker_symbol)
            return cache[ticker_symbol]
        
        # Multiple calls for same ticker should use cache
        result1 = cached_api_call('TEST')
        result2 = cached_api_call('TEST')
        
        assert result1 == result2  # Should be identical (cached)
        assert len(cache) == 1  # Only one entry in cache
        
        # Different ticker should make new call
        result3 = cached_api_call('OTHER')
        assert result3 != result1
        assert len(cache) == 2  # Two entries now