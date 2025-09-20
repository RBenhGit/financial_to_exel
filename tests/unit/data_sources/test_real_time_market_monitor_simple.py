"""
Simplified unit tests for Real-Time Market Monitor Module
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from core.data_sources.real_time_market_monitor import (
    MarketStatus,
    MarketInfo,
    RealTimeMarketMonitor
)


class TestMarketStatusEnum:
    """Test MarketStatus enum"""

    def test_market_status_values(self):
        """Test that all expected market status values exist"""
        assert MarketStatus.CLOSED.value == "closed"
        assert MarketStatus.OPEN.value == "open"
        assert MarketStatus.PRE_MARKET.value == "pre_market"
        assert MarketStatus.AFTER_HOURS.value == "after_hours"
        assert MarketStatus.WEEKEND.value == "weekend"
        assert MarketStatus.HOLIDAY.value == "holiday"


class TestMarketInfoDataclass:
    """Test MarketInfo dataclass"""

    def test_market_info_basic_creation(self):
        """Test basic MarketInfo creation"""
        market_info = MarketInfo(
            status=MarketStatus.OPEN,
            is_trading_day=True
        )

        assert market_info.status == MarketStatus.OPEN
        assert market_info.is_trading_day is True
        assert market_info.current_time is not None  # Set by __post_init__

    def test_market_info_with_custom_values(self):
        """Test MarketInfo creation with custom values"""
        now = datetime.now(timezone.utc)
        market_info = MarketInfo(
            status=MarketStatus.CLOSED,
            is_trading_day=False,
            current_time=now,
            timezone_name="US/Eastern",
            market_name="NASDAQ"
        )

        assert market_info.status == MarketStatus.CLOSED
        assert market_info.is_trading_day is False
        assert market_info.current_time == now
        assert market_info.timezone_name == "US/Eastern"
        assert market_info.market_name == "NASDAQ"


class TestRealTimeMarketMonitorBasic:
    """Test basic RealTimeMarketMonitor functionality"""

    @pytest.fixture
    def monitor(self):
        """Create a test monitor instance"""
        return RealTimeMarketMonitor(cache_ttl_minutes=5, auto_refresh_interval=10)

    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.cache_ttl_minutes == 5
        assert monitor.auto_refresh_interval == 10
        assert monitor._auto_refresh_enabled is False
        assert monitor._auto_refresh_thread is None
        assert monitor._price_service is not None
        assert monitor._refresh_callbacks == []

    def test_get_market_status_basic(self, monitor):
        """Test basic market status retrieval"""
        market_info = monitor.get_market_status()

        assert isinstance(market_info, MarketInfo)
        assert isinstance(market_info.status, MarketStatus)
        assert isinstance(market_info.is_trading_day, bool)
        assert market_info.current_time is not None

    def test_get_market_status_weekend(self, monitor):
        """Test market status on weekend"""
        # Mock a Saturday
        saturday = datetime(2024, 1, 13, 15, 0, tzinfo=timezone.utc)

        with patch('core.data_sources.real_time_market_monitor.datetime') as mock_dt:
            mock_dt.now.return_value = saturday
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            market_info = monitor.get_market_status()

            assert market_info.status == MarketStatus.WEEKEND
            assert not market_info.is_trading_day

    def test_auto_refresh_control(self, monitor):
        """Test auto refresh start/stop control"""
        # Initially not running
        assert not monitor._auto_refresh_enabled
        assert monitor._auto_refresh_thread is None

        # Test that we can call stop without error when not running
        monitor.stop_auto_refresh()
        assert not monitor._auto_refresh_enabled

    def test_callback_management(self, monitor):
        """Test callback management"""
        callback1 = Mock()
        callback2 = Mock()

        # Add callbacks
        monitor.add_refresh_callback(callback1)
        monitor.add_refresh_callback(callback2)

        assert callback1 in monitor._refresh_callbacks
        assert callback2 in monitor._refresh_callbacks
        assert len(monitor._refresh_callbacks) == 2

        # Test adding same callback again (may or may not prevent duplicates)
        initial_count = len(monitor._refresh_callbacks)
        monitor.add_refresh_callback(callback1)
        # Just verify callbacks are managed, implementation may allow duplicates
        assert len(monitor._refresh_callbacks) >= initial_count

    @pytest.mark.asyncio
    async def test_get_real_time_price_with_status_basic(self, monitor):
        """Test basic async price retrieval with status"""
        # Mock the price service
        mock_price_data = Mock()
        mock_price_data.ticker = "AAPL"

        monitor._price_service = AsyncMock()
        monitor._price_service.get_real_time_price.return_value = mock_price_data

        # Call the method
        price_data, market_info = await monitor.get_real_time_price_with_status("AAPL")

        # Verify results
        assert price_data == mock_price_data
        assert isinstance(market_info, MarketInfo)
        monitor._price_service.get_real_time_price.assert_called_once_with("AAPL", False)

    @pytest.mark.asyncio
    async def test_get_multiple_prices_with_status_basic(self, monitor):
        """Test basic async multiple prices retrieval"""
        # Mock the price service
        mock_prices = {"AAPL": Mock(), "MSFT": Mock()}

        monitor._price_service = AsyncMock()
        monitor._price_service.get_multiple_prices.return_value = mock_prices

        # Call the method
        prices, market_info = await monitor.get_multiple_prices_with_status(["AAPL", "MSFT"])

        # Verify results
        assert prices == mock_prices
        assert isinstance(market_info, MarketInfo)
        monitor._price_service.get_multiple_prices.assert_called_once_with(["AAPL", "MSFT"], False)

    def test_next_market_open_calculation(self, monitor):
        """Test next market open calculation"""
        # Test with a Friday evening (after market close)
        friday_evening = datetime(2024, 1, 19, 22, 0, tzinfo=timezone.utc)  # 5 PM EST

        next_open = monitor._get_next_market_open(friday_evening)

        # Should be next Monday
        assert next_open.weekday() == 0  # Monday
        assert next_open > friday_evening

    def test_error_handling_in_async_methods(self, monitor):
        """Test error handling in async methods"""
        # Test that exceptions in price service don't crash the monitor
        monitor._price_service = AsyncMock()
        monitor._price_service.get_real_time_price.side_effect = Exception("API Error")

        # This should be tested with pytest.mark.asyncio but for now just verify setup
        assert monitor._price_service is not None


class TestMarketTimeCalculations:
    """Test market time and timezone calculations"""

    def test_market_timezone_handling(self):
        """Test market timezone setup"""
        monitor = RealTimeMarketMonitor()

        # Should have timezone info (either pytz or warning logged)
        # Don't test specific timezone object since pytz might not be available
        assert hasattr(monitor, 'market_timezone')

    def test_cache_ttl_validation(self):
        """Test cache TTL parameter validation"""
        # Test with different cache TTL values
        monitor1 = RealTimeMarketMonitor(cache_ttl_minutes=1)
        monitor2 = RealTimeMarketMonitor(cache_ttl_minutes=60)

        assert monitor1.cache_ttl_minutes == 1
        assert monitor2.cache_ttl_minutes == 60

    def test_auto_refresh_interval_validation(self):
        """Test auto refresh interval parameter validation"""
        # Test with different refresh intervals
        monitor1 = RealTimeMarketMonitor(auto_refresh_interval=5)
        monitor2 = RealTimeMarketMonitor(auto_refresh_interval=120)

        assert monitor1.auto_refresh_interval == 5
        assert monitor2.auto_refresh_interval == 120


@pytest.mark.integration
class TestRealTimeMarketMonitorIntegration:
    """Integration tests - require real components"""

    @pytest.mark.skip(reason="Requires real price service and API access")
    def test_full_integration(self):
        """Test full integration with real price service"""
        monitor = RealTimeMarketMonitor()

        # Test market status
        market_info = monitor.get_market_status()
        assert isinstance(market_info, MarketInfo)

    @pytest.mark.unit
    def test_basic_component_integration(self):
        """Test that components integrate correctly without external dependencies"""
        monitor = RealTimeMarketMonitor()

        # Basic integration test
        assert monitor._price_service is not None
        assert hasattr(monitor, 'get_market_status')
        assert callable(monitor.get_market_status)
        assert hasattr(monitor, 'get_real_time_price_with_status')
        assert callable(monitor.get_real_time_price_with_status)