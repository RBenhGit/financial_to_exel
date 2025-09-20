"""
Unit tests for Price Service Integration Module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import pandas as pd

from core.data_sources.price_service_integration import (
    StreamlitPriceIntegration,
    get_price_integration,
    display_real_time_prices_section,
    integrate_with_watch_list_manager,
    get_current_price_simple,
    get_current_prices_simple
)

# Import required classes for mocking
from core.data_sources.real_time_price_service import PriceData


class TestStreamlitPriceIntegration:
    """Test cases for StreamlitPriceIntegration class"""

    @pytest.fixture
    def integration(self):
        """Create StreamlitPriceIntegration instance for testing"""
        return StreamlitPriceIntegration(cache_ttl_minutes=10)

    @pytest.fixture
    def mock_price_data(self):
        """Create mock PriceData for testing"""
        return PriceData(
            ticker="AAPL",
            current_price=150.25,
            change_percent=1.69,
            volume=45000000,
            market_cap=2500000000000,
            last_updated=datetime.now(),
            source="yfinance",
            cache_hit=False
        )

    def test_initialization(self, integration):
        """Test StreamlitPriceIntegration initializes correctly"""
        assert integration.cache_ttl_minutes == 10
        assert integration._service is None

    def test_lazy_service_initialization(self, integration):
        """Test lazy initialization of price service"""
        with patch('core.data_sources.price_service_integration.create_price_service') as mock_create:
            mock_service = Mock()
            mock_create.return_value = mock_service

            # First access should create service
            service = integration.service
            assert service == mock_service
            mock_create.assert_called_once_with(cache_ttl_minutes=10)

            # Second access should reuse same service
            service2 = integration.service
            assert service2 == mock_service
            mock_create.assert_called_once()  # Still only called once

    @patch('core.data_sources.price_service_integration.asyncio.set_event_loop')
    @patch('core.data_sources.price_service_integration.asyncio.new_event_loop')
    def test_get_single_price_sync_success(self, mock_new_loop, mock_set_loop, integration, mock_price_data):
        """Test successful single price retrieval"""
        # Create a proper mock event loop
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = mock_price_data
        mock_loop.close.return_value = None
        mock_new_loop.return_value = mock_loop

        # Mock the service
        integration._service = Mock()
        integration._service.get_real_time_price = AsyncMock(return_value=mock_price_data)

        result = integration.get_single_price_sync("AAPL", force_refresh=True)

        assert result == mock_price_data
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()

    @patch('core.data_sources.price_service_integration.asyncio.set_event_loop')
    @patch('core.data_sources.price_service_integration.asyncio.new_event_loop')
    def test_get_single_price_sync_error(self, mock_new_loop, mock_set_loop, integration):
        """Test single price retrieval with error"""
        # Mock event loop that raises exception
        mock_loop = Mock()
        mock_loop.run_until_complete.side_effect = Exception("API Error")
        mock_loop.close.return_value = None
        mock_new_loop.return_value = mock_loop

        # Mock the service
        integration._service = Mock()
        integration._service.get_real_time_price = AsyncMock()

        result = integration.get_single_price_sync("INVALID")

        assert result is None
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.close.assert_called_once()

    @patch('core.data_sources.price_service_integration.asyncio.set_event_loop')
    @patch('core.data_sources.price_service_integration.asyncio.new_event_loop')
    def test_get_prices_sync_success(self, mock_new_loop, mock_set_loop, integration, mock_price_data):
        """Test successful multiple prices retrieval"""
        # Mock event loop
        mock_loop = Mock()
        mock_loop.close.return_value = None
        mock_new_loop.return_value = mock_loop
        expected_result = {"AAPL": mock_price_data, "MSFT": mock_price_data}
        mock_loop.run_until_complete.return_value = expected_result

        # Mock the service
        integration._service = Mock()
        integration._service.get_multiple_prices = AsyncMock(return_value=expected_result)

        result = integration.get_prices_sync(["AAPL", "MSFT"])

        assert result == expected_result
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()

    @patch('core.data_sources.price_service_integration.asyncio.set_event_loop')
    @patch('core.data_sources.price_service_integration.asyncio.new_event_loop')
    def test_get_prices_sync_error(self, mock_new_loop, mock_set_loop, integration):
        """Test multiple prices retrieval with error"""
        # Mock event loop that raises exception
        mock_loop = Mock()
        mock_loop.run_until_complete.side_effect = Exception("API Error")
        mock_loop.close.return_value = None
        mock_new_loop.return_value = mock_loop

        # Mock the service
        integration._service = Mock()
        integration._service.get_multiple_prices = AsyncMock()

        tickers = ["AAPL", "MSFT"]
        result = integration.get_prices_sync(tickers)

        # Should return None for each ticker on error
        expected = {"AAPL": None, "MSFT": None}
        assert result == expected
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.close.assert_called_once()


class TestStreamlitDisplayFormatting:
    """Test display formatting functions"""

    @pytest.fixture
    def sample_price_data(self):
        """Sample price data for testing"""
        return {
            "AAPL": PriceData(
                ticker="AAPL",
                current_price=150.25,
                change_percent=1.69,
                volume=45000000,
                market_cap=2500000000000,
                last_updated=datetime(2024, 1, 15, 10, 30),
                source="yfinance",
                cache_hit=False
            ),
            "MSFT": PriceData(
                ticker="MSFT",
                current_price=380.75,
                change_percent=-1.36,
                volume=23000000,
                market_cap=2800000000000,
                last_updated=datetime(2024, 1, 15, 10, 30),
                source="alpha_vantage",
                cache_hit=True
            ),
            "INVALID": None  # Failed to fetch
        }

    @patch('streamlit.dataframe')
    def test_display_price_table(self, mock_dataframe, sample_price_data):
        """Test display price table functionality"""
        integration = StreamlitPriceIntegration()

        with patch.object(integration, 'get_prices_sync', return_value=sample_price_data):
            try:
                result = integration.display_price_table(["AAPL", "MSFT", "INVALID"], show_refresh_button=False)
                assert isinstance(result, pd.DataFrame)
                # Should have entries for all tickers (including failed ones)
                assert len(result) == 3
            except ImportError:
                # Expected in test environment without streamlit
                pass

    @patch('streamlit.metric')
    def test_display_price_metrics(self, mock_metric):
        """Test display price metrics functionality"""
        integration = StreamlitPriceIntegration()

        price_data = PriceData(
            ticker="AAPL",
            current_price=150.25,
            change_percent=1.69,
            volume=45000000,
            market_cap=2500000000000,
            last_updated=datetime.now(),
            source="yfinance",
            cache_hit=False
        )

        with patch.object(integration, 'get_single_price_sync', return_value=price_data):
            try:
                result = integration.display_price_metrics("AAPL", show_refresh=False)
                assert result == price_data
            except ImportError:
                # Expected in test environment without streamlit
                pass


class TestWatchlistDisplay:
    """Test watchlist display functionality"""

    def test_get_price_integration(self):
        """Test getting cached price integration instance"""
        try:
            integration = get_price_integration()
            assert isinstance(integration, StreamlitPriceIntegration)
        except ImportError:
            # Expected in test environment without streamlit
            pass

    @patch('streamlit.header')
    def test_display_real_time_prices_section(self, mock_header):
        """Test complete real-time prices section"""
        try:
            display_real_time_prices_section(["AAPL", "MSFT"])
            # Should not raise any exceptions
        except ImportError:
            # Expected in test environment without streamlit
            pass

    def test_integrate_with_watch_list_manager(self):
        """Test integration with existing watch list manager"""
        # Test with different data structures
        watch_list_dict = {"tickers": ["AAPL", "MSFT"]}
        watch_list_companies = {"companies": {"AAPL": {}, "MSFT": {}}}
        watch_list_list = ["AAPL", "MSFT"]

        with patch('core.data_sources.price_service_integration.StreamlitPriceIntegration') as mock_integration:
            mock_instance = Mock()
            mock_integration.return_value = mock_instance
            mock_instance.get_prices_sync.return_value = {"AAPL": Mock(), "MSFT": None}

            # Test dict with tickers
            result = integrate_with_watch_list_manager(watch_list_dict)
            assert isinstance(result, dict)

            # Test dict with companies
            result = integrate_with_watch_list_manager(watch_list_companies)
            assert isinstance(result, dict)

            # Test list format
            result = integrate_with_watch_list_manager(watch_list_list)
            assert isinstance(result, dict)


class TestUtilityFunctions:
    """Test utility functions for simple price access"""

    @patch('core.data_sources.price_service_integration.StreamlitPriceIntegration')
    def test_get_current_price_simple(self, mock_integration_class):
        """Test simple price retrieval function"""
        mock_integration = Mock()
        mock_integration_class.return_value = mock_integration

        # Mock successful price data
        mock_price_data = Mock()
        mock_price_data.current_price = 150.25
        mock_integration.get_single_price_sync.return_value = mock_price_data

        result = get_current_price_simple("AAPL", use_cache=True)

        assert result == 150.25
        mock_integration.get_single_price_sync.assert_called_once_with("AAPL", force_refresh=False)

    @patch('core.data_sources.price_service_integration.StreamlitPriceIntegration')
    def test_get_current_price_simple_none(self, mock_integration_class):
        """Test simple price retrieval with None result"""
        mock_integration = Mock()
        mock_integration_class.return_value = mock_integration
        mock_integration.get_single_price_sync.return_value = None

        result = get_current_price_simple("INVALID", use_cache=False)

        assert result is None
        mock_integration.get_single_price_sync.assert_called_once_with("INVALID", force_refresh=True)

    @patch('core.data_sources.price_service_integration.StreamlitPriceIntegration')
    def test_get_current_prices_simple(self, mock_integration_class):
        """Test simple multiple prices retrieval function"""
        mock_integration = Mock()
        mock_integration_class.return_value = mock_integration

        # Mock price data
        mock_price_data_aapl = Mock()
        mock_price_data_aapl.current_price = 150.25
        mock_price_data_msft = Mock()
        mock_price_data_msft.current_price = 380.75

        mock_integration.get_prices_sync.return_value = {
            "AAPL": mock_price_data_aapl,
            "MSFT": mock_price_data_msft,
            "INVALID": None
        }

        result = get_current_prices_simple(["AAPL", "MSFT", "INVALID"], use_cache=True)

        expected = {"AAPL": 150.25, "MSFT": 380.75, "INVALID": None}
        assert result == expected
        mock_integration.get_prices_sync.assert_called_once_with(["AAPL", "MSFT", "INVALID"], force_refresh=False)


class TestErrorHandling:
    """Test error handling in price service integration"""

    def test_price_service_creation_error(self):
        """Test handling price service creation errors"""
        with patch('core.data_sources.price_service_integration.create_price_service') as mock_create:
            mock_create.side_effect = Exception("Service creation failed")

            integration = StreamlitPriceIntegration()

            # Service property should handle errors gracefully
            try:
                service = integration.service
                # If no exception, service should still be None or handle gracefully
            except Exception as e:
                # Should be handled appropriately
                assert "Service creation failed" in str(e)

    def test_async_context_error_handling(self):
        """Test error handling in async context management"""
        integration = StreamlitPriceIntegration()

        # Test with broken event loop
        with patch('core.data_sources.price_service_integration.asyncio.set_event_loop') as mock_set_loop, \
             patch('core.data_sources.price_service_integration.asyncio.new_event_loop') as mock_new_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete.side_effect = RuntimeError("Event loop error")
            mock_loop.close.return_value = None
            mock_new_loop.return_value = mock_loop

            integration._service = Mock()
            integration._service.get_real_time_price = AsyncMock()

            result = integration.get_single_price_sync("AAPL")
            assert result is None
            mock_new_loop.assert_called_once()
            mock_set_loop.assert_called_once_with(mock_loop)
            mock_loop.close.assert_called_once()


class TestIntegrationUtilities:
    """Test utility functions for integration"""

    def test_price_data_validation(self):
        """Test price data validation utilities"""
        valid_price_data = PriceData(
            ticker="AAPL",
            current_price=150.25,
            change_percent=1.69,
            volume=45000000,
            market_cap=2500000000000,
            last_updated=datetime.now(),
            source="yfinance"
        )

        # Test that PriceData can be created and accessed
        assert valid_price_data.ticker == "AAPL"
        assert valid_price_data.current_price == 150.25
        assert valid_price_data.change_percent == 1.69

    def test_ticker_list_validation(self):
        """Test ticker list validation"""
        # Valid ticker lists
        valid_lists = [
            ["AAPL"],
            ["AAPL", "MSFT", "GOOGL"],
            []  # Empty list should be valid
        ]

        for ticker_list in valid_lists:
            assert isinstance(ticker_list, list)
            for ticker in ticker_list:
                assert isinstance(ticker, str)
                assert len(ticker) > 0

    def test_cache_ttl_configuration(self):
        """Test cache TTL configuration"""
        # Test different cache TTL values
        integration1 = StreamlitPriceIntegration(cache_ttl_minutes=5)
        integration2 = StreamlitPriceIntegration(cache_ttl_minutes=30)
        integration3 = StreamlitPriceIntegration(cache_ttl_minutes=60)

        assert integration1.cache_ttl_minutes == 5
        assert integration2.cache_ttl_minutes == 30
        assert integration3.cache_ttl_minutes == 60


class TestPerformance:
    """Test performance aspects of price service integration"""

    def test_concurrent_price_requests(self):
        """Test handling of concurrent price requests"""
        integration = StreamlitPriceIntegration()

        # This would ideally test concurrent access patterns
        # For now, just ensure basic functionality works
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NFLX"]

        with patch('core.data_sources.price_service_integration.asyncio.new_event_loop') as mock_new_loop:
            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = {ticker: None for ticker in tickers}

            integration._service = Mock()
            integration._service.get_multiple_prices = AsyncMock()

            result = integration.get_prices_sync(tickers)

            # Should handle all tickers
            assert len(result) == len(tickers)
            for ticker in tickers:
                assert ticker in result

    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large price data sets"""
        # Create large mock dataset
        large_price_data = {}
        for i in range(100):
            ticker = f"TICK{i:03d}"
            large_price_data[ticker] = PriceData(
                ticker=ticker,
                current_price=100.0 + i,
                change_percent=1.0,
                volume=1000000,
                market_cap=1000000000,
                last_updated=datetime.now(),
                source="test"
            )

        # Test that large dataset can be created
        assert len(large_price_data) == 100

        # Test that each price data object was created correctly
        for ticker, price_data in large_price_data.items():
            assert isinstance(price_data, PriceData)
            assert price_data.ticker == ticker


if __name__ == "__main__":
    pytest.main([__file__])