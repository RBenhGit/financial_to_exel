"""
Comprehensive test suite for RealTimePriceService missing coverage areas

This module targets specific uncovered functionality:
- Provider initialization and configuration
- Cache management and persistence
- Multi-source data fetching with fallbacks
- Background price refresh mechanisms
- Error handling and logging
- Async operations and context management
"""

import pytest
import tempfile
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor

from core.data_sources.real_time_price_service import (
    PriceData,
    PriceCacheEntry,
    RealTimePriceService
)
from core.data_sources.interfaces.data_sources import (
    DataSourceType,
    DataSourceResponse,
    FinancialDataRequest
)


class TestPriceDataClass:
    """Test PriceData dataclass functionality"""

    def test_price_data_creation_with_defaults(self):
        """Test PriceData creation with default values"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)

        assert price_data.ticker == "AAPL"
        assert price_data.current_price == 150.0
        assert price_data.change_percent == 0.0
        assert price_data.volume == 0
        assert price_data.market_cap == 0.0
        assert price_data.source == "unknown"
        assert price_data.currency == "USD"
        assert price_data.cache_hit is False
        assert price_data.timestamp is not None
        assert price_data.last_updated is not None

    def test_price_data_post_init_timestamps(self):
        """Test that __post_init__ sets timestamps correctly"""
        # Test with no timestamps provided
        price_data = PriceData(ticker="MSFT", current_price=300.0)
        assert price_data.timestamp is not None
        assert price_data.last_updated is not None

        # Test with timestamps provided
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        price_data2 = PriceData(
            ticker="GOOGL",
            current_price=2500.0,
            timestamp=custom_time,
            last_updated=custom_time
        )
        assert price_data2.timestamp == custom_time
        assert price_data2.last_updated == custom_time

    def test_price_data_all_fields(self):
        """Test PriceData with all fields specified"""
        timestamp = datetime.now()
        price_data = PriceData(
            ticker="NVDA",
            current_price=500.0,
            change_percent=2.5,
            volume=1000000,
            market_cap=1.2e12,
            timestamp=timestamp,
            source="yfinance",
            currency="USD",
            last_updated=timestamp,
            cache_hit=True
        )

        assert price_data.ticker == "NVDA"
        assert price_data.current_price == 500.0
        assert price_data.change_percent == 2.5
        assert price_data.volume == 1000000
        assert price_data.market_cap == 1.2e12
        assert price_data.source == "yfinance"
        assert price_data.currency == "USD"
        assert price_data.cache_hit is True


class TestPriceCacheEntry:
    """Test PriceCacheEntry functionality"""

    def test_cache_entry_creation(self):
        """Test cache entry creation"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)
        cached_at = datetime.now()
        expires_at = cached_at + timedelta(minutes=15)

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=cached_at,
            expires_at=expires_at,
            source_priority=1
        )

        assert cache_entry.price_data == price_data
        assert cache_entry.cached_at == cached_at
        assert cache_entry.expires_at == expires_at
        assert cache_entry.source_priority == 1
        assert cache_entry.fetch_success is True
        assert cache_entry.error_message is None

    def test_cache_entry_is_expired_false(self):
        """Test cache entry that is not expired"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)
        cached_at = datetime.now()
        expires_at = datetime.now() + timedelta(minutes=30)  # Future expiry

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=cached_at,
            expires_at=expires_at,
            source_priority=1
        )

        assert not cache_entry.is_expired()

    def test_cache_entry_is_expired_true(self):
        """Test cache entry that is expired"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)
        cached_at = datetime.now() - timedelta(minutes=30)
        expires_at = datetime.now() - timedelta(minutes=1)  # Past expiry

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=cached_at,
            expires_at=expires_at,
            source_priority=1
        )

        assert cache_entry.is_expired()

    def test_cache_entry_is_fresh_true(self):
        """Test cache entry that is fresh"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)
        cached_at = datetime.now() - timedelta(minutes=5)  # 5 minutes ago
        expires_at = datetime.now() + timedelta(minutes=10)

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=cached_at,
            expires_at=expires_at,
            source_priority=1
        )

        assert cache_entry.is_fresh(max_age_minutes=15)

    def test_cache_entry_is_fresh_false(self):
        """Test cache entry that is not fresh"""
        price_data = PriceData(ticker="AAPL", current_price=150.0)
        cached_at = datetime.now() - timedelta(minutes=20)  # 20 minutes ago
        expires_at = datetime.now() + timedelta(minutes=10)

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=cached_at,
            expires_at=expires_at,
            source_priority=1
        )

        assert not cache_entry.is_fresh(max_age_minutes=15)

    def test_cache_entry_with_error(self):
        """Test cache entry with error information"""
        price_data = PriceData(ticker="INVALID", current_price=0.0)

        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=15),
            source_priority=1,
            fetch_success=False,
            error_message="API rate limit exceeded"
        )

        assert cache_entry.fetch_success is False
        assert cache_entry.error_message == "API rate limit exceeded"


class TestRealTimePriceServiceInitialization:
    """Test RealTimePriceService initialization"""

    def test_service_initialization_defaults(self):
        """Test service initialization with default parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RealTimePriceService(cache_dir=temp_dir)

            assert service.cache_ttl_minutes == 15
            assert service.cache_dir == Path(temp_dir)
            assert isinstance(service._memory_cache, dict)
            assert isinstance(service._providers, dict)
            assert isinstance(service._provider_configs, dict)
            assert isinstance(service._executor, ThreadPoolExecutor)

    def test_service_initialization_custom_params(self):
        """Test service initialization with custom parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RealTimePriceService(cache_dir=temp_dir, cache_ttl_minutes=30)

            assert service.cache_ttl_minutes == 30
            assert service.cache_dir == Path(temp_dir)

    def test_service_initialization_no_cache_dir(self):
        """Test service initialization without cache directory"""
        service = RealTimePriceService()

        assert service.cache_dir == Path("data/cache/prices")
        # Directory creation is tested implicitly

    @patch('core.data_sources.real_time_price_service.logger')
    def test_service_initialization_logging(self, mock_logger):
        """Test that initialization logs correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RealTimePriceService(cache_dir=temp_dir, cache_ttl_minutes=25)

            mock_logger.info.assert_called_with(
                "RealTimePriceService initialized with cache TTL: 25 minutes"
            )


class TestProviderInitialization:
    """Test provider initialization functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    @patch('core.data_sources.real_time_price_service.YfinanceProvider')
    def test_initialize_providers_yfinance_success(self, mock_yfinance, service):
        """Test successful yfinance provider initialization"""
        mock_provider = Mock()
        mock_yfinance.return_value = mock_provider

        service._initialize_providers()

        assert DataSourceType.YFINANCE in service._providers
        assert DataSourceType.YFINANCE in service._provider_configs

    @patch('core.data_sources.real_time_price_service.AlphaVantageProvider')
    @patch('core.data_sources.real_time_price_service.FinancialModelingPrepProvider')
    @patch('core.data_sources.real_time_price_service.PolygonProvider')
    @patch('core.data_sources.real_time_price_service.YfinanceProvider')
    def test_initialize_all_providers(self, mock_yf, mock_polygon, mock_fmp, mock_av, service):
        """Test initialization of all provider types"""
        # Mock all providers
        mock_yf.return_value = Mock()
        mock_polygon.return_value = Mock()
        mock_fmp.return_value = Mock()
        mock_av.return_value = Mock()

        service._initialize_providers()

        # Should have attempted to initialize yfinance at minimum
        assert len(service._providers) >= 1
        assert len(service._provider_configs) >= 1

    @patch('core.data_sources.real_time_price_service.YfinanceProvider')
    @patch('core.data_sources.real_time_price_service.logger')
    def test_initialize_providers_with_exception(self, mock_logger, mock_yfinance):
        """Test provider initialization with exception handling"""
        mock_yfinance.side_effect = Exception("Provider initialization failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create service which will trigger initialization with mocked provider
            service = RealTimePriceService(cache_dir=temp_dir)

            # Should have logged warning about provider failure
            mock_logger.warning.assert_called()
            # Should still have created the service instance
            assert isinstance(service, RealTimePriceService)


class TestCacheManagement:
    """Test cache management functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    def test_cache_price_data_memory_cache(self, service):
        """Test caching price data to memory cache"""
        price_data = PriceData(ticker="AAPL", current_price=150.0, source="test")

        service._cache_price_data("AAPL", price_data)

        assert "AAPL" in service._memory_cache
        cache_entry = service._memory_cache["AAPL"]
        assert cache_entry.price_data == price_data
        assert cache_entry.fetch_success is True

    def test_get_cached_price_memory_hit(self, service):
        """Test getting cached price from memory cache"""
        price_data = PriceData(ticker="MSFT", current_price=300.0)
        service._cache_price_data("MSFT", price_data)

        cached_entry = service._get_cached_price("MSFT")

        assert cached_entry is not None
        assert cached_entry.price_data.ticker == "MSFT"
        assert cached_entry.price_data.current_price == 300.0

    def test_get_cached_price_memory_miss(self, service):
        """Test getting cached price when not in memory cache"""
        cached_entry = service._get_cached_price("NONEXISTENT")

        # Should attempt to load from persistent cache and return None if not found
        assert cached_entry is None

    def test_get_cached_price_expired(self, service):
        """Test getting expired cached price"""
        price_data = PriceData(ticker="EXPIRED", current_price=100.0)

        # Create expired cache entry
        expired_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=datetime.now() - timedelta(hours=1),
            expires_at=datetime.now() - timedelta(minutes=30),  # Expired
            source_priority=1
        )
        service._memory_cache["EXPIRED"] = expired_entry

        cached_entry = service._get_cached_price("EXPIRED")

        # Should return None for expired entries
        assert cached_entry is None

    def test_clear_cache_specific_ticker(self, service):
        """Test clearing cache for specific ticker"""
        price_data = PriceData(ticker="CLEAR_ME", current_price=200.0)
        service._cache_price_data("CLEAR_ME", price_data)

        # Verify cached
        assert "CLEAR_ME" in service._memory_cache

        service.clear_cache("CLEAR_ME")

        # Verify cleared
        assert "CLEAR_ME" not in service._memory_cache

    def test_clear_cache_all(self, service):
        """Test clearing all cache"""
        price_data1 = PriceData(ticker="AAPL", current_price=150.0)
        price_data2 = PriceData(ticker="MSFT", current_price=300.0)

        service._cache_price_data("AAPL", price_data1)
        service._cache_price_data("MSFT", price_data2)

        # Verify cached
        assert len(service._memory_cache) == 2

        service.clear_cache()

        # Verify all cleared
        assert len(service._memory_cache) == 0

    def test_get_cache_status(self, service):
        """Test getting cache status information"""
        price_data = PriceData(ticker="STATUS_TEST", current_price=250.0)
        service._cache_price_data("STATUS_TEST", price_data)

        status = service.get_cache_status()

        assert isinstance(status, dict)
        assert "memory_cache_entries" in status
        assert "cache_ttl_minutes" in status
        assert "cache_directory" in status
        assert status["memory_cache_entries"] == 1
        assert status["cache_ttl_minutes"] == service.cache_ttl_minutes


class TestErrorHandling:
    """Test error handling functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    @patch('core.data_sources.real_time_price_service.logger')
    def test_get_api_key_not_found(self, mock_logger, service):
        """Test API key retrieval when key not found"""
        with patch.dict('os.environ', {}, clear=True):
            api_key = service._get_api_key("NONEXISTENT_API_KEY")

            assert api_key is None

    @patch.dict('os.environ', {'TEST_API_KEY': 'test_value'})
    def test_get_api_key_found(self, service):
        """Test API key retrieval when key is found"""
        api_key = service._get_api_key("TEST_API_KEY")

        assert api_key == "test_value"

    def test_convert_to_price_data_invalid_response(self, service):
        """Test price data conversion with invalid response"""
        invalid_response = DataSourceResponse(
            success=False,
            data={},
            source_type=DataSourceType.YFINANCE,
            error_message="API Error"
        )

        price_data = service._convert_to_price_data("AAPL", invalid_response, DataSourceType.YFINANCE)

        assert price_data is None

    def test_convert_to_price_data_missing_price_field(self, service):
        """Test price data conversion with missing price field"""
        response_data = {
            "symbol": "AAPL",
            # Missing price field
            "volume": 1000000
        }

        response = DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE
        )

        price_data = service._convert_to_price_data("AAPL", response, DataSourceType.YFINANCE)

        # Should handle missing price gracefully
        assert price_data is None or price_data.current_price == 0.0


class TestAsyncOperations:
    """Test async operation functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_get_real_time_price_with_cache_hit(self, service):
        """Test getting real-time price with cache hit"""
        # Pre-populate cache
        price_data = PriceData(ticker="CACHED", current_price=150.0, cache_hit=True)
        service._cache_price_data("CACHED", price_data)

        result = await service.get_real_time_price("CACHED")

        assert result is not None
        assert result.ticker == "CACHED"
        assert result.cache_hit is True

    @pytest.mark.asyncio
    async def test_get_real_time_price_force_refresh(self, service):
        """Test getting real-time price with force refresh"""
        # Pre-populate cache
        price_data = PriceData(ticker="FORCE_REFRESH", current_price=150.0, cache_hit=True)
        service._cache_price_data("FORCE_REFRESH", price_data)

        with patch.object(service, '_fetch_price_from_providers', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = PriceData(ticker="FORCE_REFRESH", current_price=160.0, source="api")

            result = await service.get_real_time_price("FORCE_REFRESH", force_refresh=True)

            # Should have called fetch despite cache
            mock_fetch.assert_called_once_with("FORCE_REFRESH")
            assert result.current_price == 160.0

    @pytest.mark.asyncio
    async def test_get_multiple_prices_empty_list(self, service):
        """Test getting multiple prices with empty ticker list"""
        result = await service.get_multiple_prices([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_multiple_prices_mixed_results(self, service):
        """Test getting multiple prices with mixed success/failure"""
        # Mock individual price fetching
        with patch.object(service, 'get_real_time_price', new_callable=AsyncMock) as mock_get_price:
            def side_effect(ticker, force_refresh=False):
                if ticker == "VALID":
                    return PriceData(ticker="VALID", current_price=100.0)
                else:
                    return None

            mock_get_price.side_effect = side_effect

            result = await service.get_multiple_prices(["VALID", "INVALID"])

            assert len(result) == 2
            assert result["VALID"] is not None
            assert result["INVALID"] is None

    @pytest.mark.asyncio
    @patch('core.data_sources.real_time_price_service.logger')
    async def test_fetch_price_from_providers_no_providers(self, mock_logger, service):
        """Test fetching price when no providers are available"""
        # Clear providers
        service._providers = {}

        result = await service._fetch_price_from_providers("AAPL")

        assert result is None
        # Should have logged an error about all providers failing
        mock_logger.error.assert_called_with("All providers failed for AAPL")


class TestContextManager:
    """Test context manager functionality"""

    def test_context_manager_enter_exit(self):
        """Test context manager enter and exit"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with RealTimePriceService(cache_dir=temp_dir) as service:
                assert isinstance(service, RealTimePriceService)
                assert hasattr(service, '_executor')

            # After exit, executor should be shut down
            assert service._executor._shutdown

    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with RealTimePriceService(cache_dir=temp_dir) as service:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Executor should still be shut down properly
            assert service._executor._shutdown


class TestUtilityMethods:
    """Test utility and helper methods"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    def test_get_source_priority_known_sources(self, service):
        """Test getting priority for known sources"""
        # Test known source priorities
        assert service._get_source_priority("yfinance") == 1
        assert service._get_source_priority("alpha_vantage") >= service._get_source_priority("yfinance")
        assert service._get_source_priority("fmp") >= service._get_source_priority("yfinance")
        assert service._get_source_priority("polygon") >= service._get_source_priority("yfinance")

    def test_get_source_priority_unknown_source(self, service):
        """Test getting priority for unknown source"""
        priority = service._get_source_priority("unknown_source")

        # Should return default low priority value
        assert priority == 5

    def test_sync_fetch_price_wrapper(self, service):
        """Test synchronous fetch price wrapper"""
        expected_price_data = PriceData(ticker="SYNC_TEST", current_price=200.0)

        with patch.object(service, '_fetch_price_from_providers', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = expected_price_data

            result = service._sync_fetch_price("SYNC_TEST")

            assert result is not None
            assert result.ticker == "SYNC_TEST"
            assert result.current_price == 200.0
            mock_fetch.assert_called_once_with("SYNC_TEST")


class TestBackgroundOperations:
    """Test background operation functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield RealTimePriceService(cache_dir=temp_dir)

    def test_refresh_prices_background_empty_list(self, service):
        """Test background refresh with empty ticker list"""
        result = service.refresh_prices_background([])

        assert result == {}

    def test_refresh_prices_background_with_tickers(self, service):
        """Test background refresh with ticker list"""
        with patch.object(service, '_sync_fetch_price') as mock_sync_fetch:
            def side_effect(ticker):
                if ticker == "SUCCESS":
                    return PriceData(ticker="SUCCESS", current_price=100.0)
                else:
                    return None

            mock_sync_fetch.side_effect = side_effect

            result = service.refresh_prices_background(["SUCCESS", "FAILURE"])

            assert len(result) == 2
            assert result["SUCCESS"] is True
            assert result["FAILURE"] is False


if __name__ == '__main__':
    pytest.main([__file__])