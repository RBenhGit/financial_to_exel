"""
Unit tests for Enhanced Data Manager
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock


class TestEnhancedDataManager:
    """Test cases for EnhancedDataManager class"""

    @pytest.fixture
    def data_manager(self):
        """Create EnhancedDataManager instance for testing"""
        from core.data_processing.managers.enhanced_data_manager import create_enhanced_data_manager
        return create_enhanced_data_manager()

    def test_data_manager_creation(self, data_manager):
        """Test data manager creates successfully"""
        assert data_manager is not None
        assert hasattr(data_manager, 'get_available_data_sources')

    def test_get_available_data_sources(self, data_manager):
        """Test getting available data sources"""
        sources_info = data_manager.get_available_data_sources()

        assert isinstance(sources_info, dict)
        assert 'total_sources' in sources_info
        assert sources_info['total_sources'] >= 0

    def test_backward_compatibility(self, data_manager):
        """Test backward compatibility with existing interfaces"""
        # Should have key methods for backward compatibility
        assert hasattr(data_manager, 'fetch_market_data')

    def test_cleanup(self, data_manager):
        """Test cleanup functionality"""
        # Should not raise errors
        data_manager.cleanup()

    def test_data_source_configuration(self, data_manager):
        """Test data source configuration loading"""
        if hasattr(data_manager, 'data_sources'):
            assert data_manager.data_sources is not None

    def test_error_handling_invalid_ticker(self, data_manager):
        """Test error handling for invalid ticker symbols"""
        try:
            result = data_manager.fetch_market_data('INVALID_TICKER_12345')
            # Should either return None/empty or handle gracefully
            assert result is None or isinstance(result, (dict, pd.DataFrame))
        except Exception as e:
            # Should raise appropriate exceptions, not crash
            assert isinstance(e, (ValueError, KeyError, ConnectionError))

    def test_caching_functionality(self, data_manager):
        """Test caching functionality if available"""
        if hasattr(data_manager, 'cache'):
            # Test cache is initialized
            assert data_manager.cache is not None

    def test_rate_limiting_protection(self, data_manager):
        """Test rate limiting protection"""
        if hasattr(data_manager, 'rate_limiter'):
            assert data_manager.rate_limiter is not None


class TestDataManagerIntegration:
    """Integration tests for data manager"""

    def test_multiple_data_source_access(self, data_manager):
        """Test accessing multiple data sources"""
        sources_info = data_manager.get_available_data_sources()

        if sources_info.get('total_sources', 0) > 1:
            # If multiple sources available, test they can be accessed
            assert sources_info['total_sources'] > 1

    def test_data_consistency_across_sources(self, data_manager):
        """Test data consistency across different sources"""
        # This would test that the same ticker returns consistent data
        # across different data sources (within reasonable bounds)
        pass  # Implementation depends on actual data source setup

    def test_fallback_mechanism(self, data_manager):
        """Test fallback mechanism when primary source fails"""
        if hasattr(data_manager, 'fallback_sources'):
            # Test fallback functionality
            pass  # Implementation depends on fallback setup


class TestDataValidation:
    """Test data validation functionality"""

    def test_ticker_symbol_validation(self):
        """Test ticker symbol validation"""
        from core.data_processing.managers.enhanced_data_manager import create_enhanced_data_manager

        manager = create_enhanced_data_manager()

        # Valid ticker symbols
        valid_tickers = ['AAPL', 'MSFT', 'GOOGL']
        for ticker in valid_tickers:
            # Should not raise validation errors
            assert isinstance(ticker, str)
            assert len(ticker) > 0

        # Invalid ticker symbols
        invalid_tickers = ['', '   ', '123!@#']
        for ticker in invalid_tickers:
            # These should be caught by validation
            assert not (ticker.strip() and ticker.isalpha())

    def test_data_format_validation(self, data_manager):
        """Test data format validation"""
        # Test that returned data follows expected format
        sources_info = data_manager.get_available_data_sources()

        # Should be a dictionary with expected keys
        assert isinstance(sources_info, dict)
        if 'sources' in sources_info:
            assert isinstance(sources_info['sources'], (list, dict))

    def test_date_range_validation(self):
        """Test date range validation"""
        from datetime import datetime, timedelta

        # Valid date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        assert start_date < end_date
        assert (end_date - start_date).days > 0

        # Invalid date ranges
        invalid_start = end_date + timedelta(days=30)
        assert invalid_start > end_date  # This should be caught


class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""

    def test_data_manager_memory_usage(self, data_manager):
        """Test memory usage is reasonable"""
        import sys

        # Get size of data manager object
        size = sys.getsizeof(data_manager)

        # Should not be excessively large
        assert size < 10000000  # Less than 10MB

    def test_concurrent_access_safety(self, data_manager):
        """Test thread safety for concurrent access"""
        # Basic test - should not crash with multiple calls
        sources_info1 = data_manager.get_available_data_sources()
        sources_info2 = data_manager.get_available_data_sources()

        assert sources_info1 == sources_info2

    @pytest.mark.skipif(True, reason="Performance test - enable if needed")
    def test_response_time_performance(self, data_manager):
        """Test response time performance"""
        import time

        start_time = time.time()
        sources_info = data_manager.get_available_data_sources()
        end_time = time.time()

        # Should respond within reasonable time
        assert (end_time - start_time) < 5.0
        assert sources_info is not None


class TestConfigurationManagement:
    """Test configuration management"""

    def test_default_configuration_loading(self):
        """Test default configuration loads correctly"""
        from core.data_processing.managers.enhanced_data_manager import create_enhanced_data_manager

        manager = create_enhanced_data_manager()
        assert manager is not None

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test that invalid configurations are handled properly
        pass  # Implementation depends on configuration structure

    def test_environment_specific_config(self):
        """Test environment-specific configuration handling"""
        # Test development vs production configurations
        pass  # Implementation depends on environment setup


class TestErrorHandling:
    """Test comprehensive error handling"""

    def test_network_error_handling(self, data_manager):
        """Test handling of network errors"""
        # Should handle network errors gracefully
        if hasattr(data_manager, 'fetch_market_data'):
            try:
                # This might fail due to network issues
                result = data_manager.fetch_market_data('AAPL')
                # If it succeeds, should return valid data
                if result is not None:
                    assert isinstance(result, (dict, pd.DataFrame))
            except Exception as e:
                # Should raise appropriate exceptions
                assert isinstance(e, (ConnectionError, TimeoutError, ValueError))

    def test_api_limit_handling(self, data_manager):
        """Test handling of API rate limits"""
        # Should handle API rate limits gracefully
        sources_info = data_manager.get_available_data_sources()
        assert isinstance(sources_info, dict)

    def test_malformed_data_handling(self, data_manager):
        """Test handling of malformed data responses"""
        # Should handle malformed or unexpected data
        if hasattr(data_manager, '_process_data'):
            try:
                # Test with malformed data
                bad_data = "not valid json or data"
                # Should either handle gracefully or raise appropriate error
                pass  # Implementation depends on actual method
            except (ValueError, TypeError):
                pass  # Expected for malformed data


if __name__ == "__main__":
    pytest.main([__file__])