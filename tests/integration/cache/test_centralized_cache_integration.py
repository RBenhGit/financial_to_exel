"""
Integration tests for Optimized Cache Manager with CentralizedDataManager
========================================================================

Tests the integration of the new caching system with existing data management.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from utils.input_validator import ValidationLevel


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Robust cleanup with multiple attempts for Windows file locking issues
    import time
    import os

    def force_remove_readonly(func, path, _):
        """Handle readonly files on Windows"""
        try:
            os.chmod(path, 0o777)
            func(path)
        except (OSError, PermissionError):
            pass

    # Try cleanup with multiple attempts
    for attempt in range(3):
        try:
            shutil.rmtree(temp_dir, onerror=force_remove_readonly)
            break
        except (PermissionError, OSError):
            if attempt < 2:
                time.sleep(0.2 * (attempt + 1))  # Progressive backoff
            # Final attempt: ignore errors completely
            if attempt == 2:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass


@pytest.fixture
def data_manager(temp_data_dir):
    """Create CentralizedDataManager with optimized caching"""
    manager = CentralizedDataManager(
        base_path=temp_data_dir,
        cache_dir=str(Path(temp_data_dir) / "cache"),
        validation_level=ValidationLevel.MODERATE  # Use moderate validation for testing
    )
    yield manager


class TestCentralizedCacheIntegration:
    """Integration tests for cache with data manager"""

    def test_data_manager_cache_initialization(self, data_manager):
        """Test that data manager initializes with optimized cache"""
        assert data_manager is not None

        # Should have optimized cache manager
        assert hasattr(data_manager, 'cache_manager')
        assert data_manager.cache_manager is not None

        # Basic cache functionality should work
        test_data = {"test": "integration"}
        data_manager.cache_data("integration_test", test_data, "test_source")

        cached_result = data_manager.get_cached_data("integration_test")
        assert cached_result == test_data

    def test_cache_performance_report(self, data_manager):
        """Test cache performance reporting"""
        # Add some test data
        for i in range(10):
            data_manager.cache_data(f"perf_test_{i}", {"data": i}, "test")

        # Get performance report
        report = data_manager.get_cache_performance_report()

        assert report is not None
        assert "optimized_cache_enabled" in report
        assert report["optimized_cache_enabled"] is True

        assert "cache_stats" in report
        stats = report["cache_stats"]

        assert "memory_cache" in stats
        assert "performance" in stats

        # Should have cached entries
        assert stats["memory_cache"]["entry_count"] > 0

        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)

    def test_cache_invalidation_integration(self, data_manager):
        """Test cache invalidation through data manager"""
        # Cache some ticker data
        aapl_price = {"price": 150.0, "timestamp": "2024-01-01"}
        aapl_financials = {"revenue": 1000000, "timestamp": "2024-01-01"}
        msft_price = {"price": 300.0, "timestamp": "2024-01-01"}

        data_manager.cache_data("aapl_price", aapl_price, "yfinance", ticker="AAPL", data_type="price")
        data_manager.cache_data("aapl_financials", aapl_financials, "yfinance", ticker="AAPL", data_type="financials")
        data_manager.cache_data("msft_price", msft_price, "yfinance", ticker="MSFT", data_type="price")

        # Verify data exists
        assert data_manager.get_cached_data("aapl_price", ticker="AAPL") == aapl_price
        assert data_manager.get_cached_data("aapl_financials", ticker="AAPL") == aapl_financials
        assert data_manager.get_cached_data("msft_price", ticker="MSFT") == msft_price

        # Invalidate AAPL cache
        data_manager.invalidate_ticker_cache("AAPL")

        # AAPL data should be gone, MSFT should remain
        assert data_manager.get_cached_data("aapl_price", ticker="AAPL") is None
        assert data_manager.get_cached_data("aapl_financials", ticker="AAPL") is None
        assert data_manager.get_cached_data("msft_price", ticker="MSFT") == msft_price

    def test_cache_cleanup_integration(self, data_manager):
        """Test cache cleanup functionality"""
        # Add some test data
        for i in range(5):
            data_manager.cache_data(f"cleanup_test_{i}", {"data": i}, "test")

        # Clean up expired entries (should return 0 for fresh entries)
        cleaned = data_manager.cleanup_expired_cache()

        # Should return integer count
        assert isinstance(cleaned, int)
        assert cleaned >= 0

    def test_adaptive_ttl_with_rate_limiter(self, data_manager):
        """Test adaptive TTL based on rate limiting status"""
        # This test verifies the integration with rate limiter
        # The actual TTL adaptation is tested in the rate limiter tests

        test_data = {"adaptive": "ttl_test"}

        # Cache data with rate limiter integration
        data_manager.cache_data("adaptive_test", test_data, "yfinance", data_type="market_data")

        # Should be cached
        result = data_manager.get_cached_data("adaptive_test", data_type="market_data")
        assert result == test_data

    def test_fallback_to_basic_cache(self, temp_data_dir):
        """Test fallback to basic cache when optimized cache is unavailable"""
        # Create data manager that might fall back to basic cache
        # This would happen if the optimized cache module isn't available

        manager = CentralizedDataManager(
            base_path=temp_data_dir,
            cache_dir=str(Path(temp_data_dir) / "cache"),
            validation_level=ValidationLevel.MODERATE
        )

        # Should still work regardless of cache type
        test_data = {"fallback": "test"}
        manager.cache_data("fallback_test", test_data, "test")

        result = manager.get_cached_data("fallback_test")
        assert result == test_data

    def test_cache_with_ticker_metadata(self, data_manager):
        """Test caching with ticker and data type metadata"""
        ticker_data = {
            "AAPL": {"price": 150, "volume": 1000000},
            "MSFT": {"price": 300, "volume": 800000}
        }

        for ticker, data in ticker_data.items():
            data_manager.cache_data(
                f"{ticker}_market_data",
                data,
                "yfinance",
                ticker=ticker,
                data_type="market_data"
            )

        # Should be able to retrieve with metadata
        for ticker, expected_data in ticker_data.items():
            result = data_manager.get_cached_data(
                f"{ticker}_market_data",
                data_type="market_data",
                ticker=ticker
            )
            assert result == expected_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])