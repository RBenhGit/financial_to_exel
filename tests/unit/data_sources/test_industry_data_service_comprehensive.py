"""
Comprehensive test suite for IndustryDataService uncovered functionality

This module provides additional tests for:
- Error handling in main API methods
- API data fetching with mocking
- Fallback mechanisms
- Batch peer verification
- Rate limiting integration
- Complex peer discovery scenarios
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import yfinance as yf

from core.data_sources.industry_data_service import (
    IndustryDataService,
    IndustryStatistics,
    IndustryPeerData
)


class TestIndustryDataServiceErrorHandling:
    """Test error handling scenarios"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=24)

    def test_get_industry_pb_statistics_with_api_failure(self, service):
        """Test behavior when API calls fail"""
        with patch.object(service, '_get_sector_classification', return_value=None):
            result = service.get_industry_pb_statistics("INVALID")
            assert result is None

    def test_get_industry_pb_statistics_with_insufficient_peers(self, service):
        """Test behavior when insufficient peer companies found"""
        mock_sector = {"sector": "Technology", "industry": "Software"}

        with patch.object(service, '_get_sector_classification', return_value=mock_sector), \
             patch.object(service, '_find_peer_companies', return_value=["AAPL"]), \
             patch.object(service, '_fetch_peer_pb_data', return_value=[]):

            result = service.get_industry_pb_statistics("MSFT")
            assert result is None

    def test_get_industry_pb_statistics_with_partial_data(self, service):
        """Test behavior with partial peer data"""
        mock_sector = {"sector": "Technology", "industry": "Software"}
        # Need at least 5 peers for the service to return results
        mock_peer_data = [
            IndustryPeerData("AAPL", "Technology", "Software", 28.5, "yfinance"),
            IndustryPeerData("MSFT", "Technology", "Software", 12.3, "yfinance"),
            IndustryPeerData("GOOGL", "Technology", "Software", 15.8, "yfinance"),
            IndustryPeerData("AMZN", "Technology", "Software", 20.1, "yfinance"),
            IndustryPeerData("META", "Technology", "Software", 18.4, "yfinance")
        ]

        with patch.object(service, '_get_sector_classification', return_value=mock_sector), \
             patch.object(service, '_find_peer_companies', return_value=["AAPL", "MSFT", "GOOGL", "AMZN", "META"]), \
             patch.object(service, '_fetch_peer_pb_data', return_value=mock_peer_data):

            result = service.get_industry_pb_statistics("NVDA")
            assert result is not None
            assert result.peer_count == 5


class TestIndustryDataServiceAPIIntegration:
    """Test API integration scenarios with mocking"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=24)

    @patch('yfinance.Ticker')
    def test_get_sector_classification_success(self, mock_ticker_class, service):
        """Test successful sector classification retrieval"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        mock_ticker_class.return_value = mock_ticker

        result = service._get_sector_classification("AAPL")

        assert result is not None
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Consumer Electronics'
        mock_ticker_class.assert_called_with("AAPL")

    @patch('yfinance.Ticker')
    def test_get_sector_classification_missing_data(self, mock_ticker_class, service):
        """Test sector classification with missing data"""
        mock_ticker = Mock()
        mock_ticker.info = {}  # Empty info
        mock_ticker_class.return_value = mock_ticker

        result = service._get_sector_classification("INVALID")
        assert result is None

    @patch('yfinance.Ticker')
    def test_get_sector_classification_api_exception(self, mock_ticker_class, service):
        """Test sector classification with API exception"""
        mock_ticker_class.side_effect = Exception("API Error")

        result = service._get_sector_classification("AAPL")
        assert result is None

    def test_find_peer_companies_with_fallback(self, service):
        """Test peer discovery with fallback mechanism"""
        with patch.object(service, '_get_common_tickers_by_sector', return_value=['AAPL', 'MSFT', 'GOOGL']), \
             patch.object(service, '_batch_verify_peers', return_value=['AAPL', 'MSFT']), \
             patch.object(service, '_fallback_sector_search', return_value=['NVDA', 'AMD']):

            # First call returns insufficient peers, triggering fallback
            peers = service._find_peer_companies("Technology", "Software")

            # Should have called fallback and returned combined results
            assert len(peers) >= 2

    def test_fallback_sector_search(self, service):
        """Test fallback sector search mechanism"""
        with patch.object(service, '_get_common_tickers_by_sector', return_value=['TECH1', 'TECH2', 'TECH3']):
            result = service._fallback_sector_search("Technology", "Software")

            assert isinstance(result, list)
            assert len(result) <= 10  # Should limit results


class TestIndustryDataServiceBatchOperations:
    """Test batch operations and peer verification"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=24)

    @patch('yfinance.Ticker')
    def test_batch_verify_peers_success(self, mock_ticker_class, service):
        """Test successful batch peer verification"""
        def mock_ticker_side_effect(ticker):
            mock_ticker = Mock()
            if ticker in ['AAPL', 'MSFT']:
                mock_ticker.info = {'sector': 'Technology'}
            else:
                mock_ticker.info = {'sector': 'Healthcare'}
            return mock_ticker

        mock_ticker_class.side_effect = mock_ticker_side_effect

        potential_peers = ['AAPL', 'MSFT', 'JNJ', 'PFE']
        verified_peers = service._batch_verify_peers(potential_peers, 'Technology')

        assert len(verified_peers) == 2
        assert 'AAPL' in verified_peers
        assert 'MSFT' in verified_peers
        assert 'JNJ' not in verified_peers

    @patch('yfinance.Ticker')
    def test_fetch_peer_pb_data_mixed_results(self, mock_ticker_class, service):
        """Test fetching P/B data with mixed success/failure"""
        def mock_ticker_side_effect(ticker):
            mock_ticker = Mock()
            if ticker == 'AAPL':
                mock_ticker.info = {
                    'priceToBook': 28.5,
                    'sector': 'Technology',
                    'industry': 'Consumer Electronics'
                }
            elif ticker == 'MSFT':
                mock_ticker.info = {
                    'priceToBook': 12.3,
                    'sector': 'Technology',
                    'industry': 'Software'
                }
            else:
                # Simulate API failure or missing data
                mock_ticker.info = {}
            return mock_ticker

        mock_ticker_class.side_effect = mock_ticker_side_effect

        peer_tickers = ['AAPL', 'MSFT', 'INVALID', 'MISSING']
        peer_data = service._fetch_peer_pb_data(peer_tickers)

        assert len(peer_data) == 2
        assert any(p.ticker == 'AAPL' and p.pb_ratio == 28.5 for p in peer_data)
        assert any(p.ticker == 'MSFT' and p.pb_ratio == 12.3 for p in peer_data)

    @patch('yfinance.Ticker')
    def test_fetch_single_ticker_pb_data_invalid_pb(self, mock_ticker_class, service):
        """Test fetching single ticker with invalid P/B ratio"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'priceToBook': -1.5,  # Invalid negative P/B
            'sector': 'Technology',
            'industry': 'Software'
        }
        mock_ticker_class.return_value = mock_ticker

        result = service._fetch_single_ticker_pb_data('TEST')
        assert result is None


class TestIndustryDataServiceCachingAdvanced:
    """Test advanced caching scenarios"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=1)

    def test_cache_expiry_behavior(self, service):
        """Test cache expiry and refresh behavior"""
        # Create expired cache entry
        old_stats = IndustryStatistics(
            sector="Technology",
            industry="Software",
            peer_count=5,
            median_pb=15.0,
            mean_pb=16.5,
            q1_pb=12.0,
            q3_pb=20.0,
            min_pb=8.0,
            max_pb=25.0,
            data_quality_score=0.8,
            peer_tickers=['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD'],
            last_updated=datetime.now(),
            cache_expiry=datetime.now() - timedelta(hours=1)  # Expired
        )

        # Save to cache
        service._save_to_cache("MSFT", old_stats)

        # Load cache and verify expiry check works
        cached_result = service._load_from_cache("MSFT")
        assert cached_result is not None  # Load should succeed

        # But validation should fail for expired cache
        is_valid = service._is_cache_valid(cached_result)
        assert is_valid is False

    def test_cache_info_functionality(self, service):
        """Test cache information retrieval"""
        # Create some cache entries
        stats1 = IndustryStatistics(
            sector="Technology", industry="Software", peer_count=3,
            median_pb=15.0, mean_pb=15.0, q1_pb=10.0, q3_pb=20.0,
            min_pb=5.0, max_pb=25.0, data_quality_score=0.9,
            peer_tickers=['A', 'B', 'C'], last_updated=datetime.now()
        )

        service._save_to_cache("TEST1", stats1)
        service._save_to_cache("TEST2", stats1)

        cache_info = service.get_cache_info()

        assert isinstance(cache_info, dict)
        assert 'total_cached_files' in cache_info
        assert cache_info['total_cached_files'] >= 2
        assert 'cache_dir' in cache_info

    def test_clear_cache_specific_ticker(self, service):
        """Test clearing cache for specific ticker"""
        stats = IndustryStatistics(
            sector="Technology", industry="Software", peer_count=3,
            median_pb=15.0, mean_pb=15.0, q1_pb=10.0, q3_pb=20.0,
            min_pb=5.0, max_pb=25.0, data_quality_score=0.9,
            peer_tickers=['A', 'B', 'C'], last_updated=datetime.now()
        )

        service._save_to_cache("CLEAR_TEST", stats)

        # Verify cache exists
        assert service._load_from_cache("CLEAR_TEST") is not None

        # Clear specific ticker
        service.clear_cache("CLEAR_TEST")

        # Verify cache is cleared
        assert service._load_from_cache("CLEAR_TEST") is None


class TestIndustryDataServiceRateLimiting:
    """Test rate limiting integration"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=24)

    def test_rate_limiter_initialization_success(self, service):
        """Test successful rate limiter initialization"""
        # Mock the import since it might not be available in test environment
        with patch('core.data_sources.industry_data_service.EnhancedRateLimiter') as mock_rate_limiter:
            mock_rate_limiter.return_value = Mock()

            service._initialize_rate_limiters()

            assert hasattr(service, 'rate_limiters')
            assert isinstance(service.rate_limiters, dict)
            # Should have common API providers
            expected_providers = ['yfinance', 'alpha_vantage', 'fmp']
            for provider in expected_providers:
                assert provider in service.rate_limiters

    @patch('core.data_sources.industry_data_service.EnhancedRateLimiter')
    def test_rate_limiter_initialization_failure(self, mock_rate_limiter, service):
        """Test rate limiter initialization with failure"""
        mock_rate_limiter.side_effect = Exception("Rate limiter error")

        service._initialize_rate_limiters()

        # Should handle gracefully
        assert hasattr(service, 'rate_limiters')
        assert service.rate_limiters == {}


class TestIndustryDataServiceStatisticsCalculation:
    """Test statistics calculation edge cases"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        temp_dir = tempfile.mkdtemp()
        return IndustryDataService(cache_dir=temp_dir, cache_ttl_hours=24)

    def test_calculate_industry_statistics_insufficient_data(self, service):
        """Test statistics calculation with insufficient data"""
        # Only one peer company (insufficient)
        peer_data = [
            IndustryPeerData("AAPL", "Technology", "Software", 28.5, "yfinance")
        ]

        result = service._calculate_industry_statistics("Technology", "Software", peer_data)
        assert result is None

    def test_calculate_data_quality_score_edge_cases(self, service):
        """Test data quality score calculation with edge cases"""
        # Test with mixed quality data
        peer_data = [
            IndustryPeerData("AAPL", "Technology", "Software", 28.5, "yfinance"),
            IndustryPeerData("MSFT", "Technology", "Software", 12.3, "alpha_vantage"),
            IndustryPeerData("GOOGL", "", "", 15.8, "yfinance"),  # Missing sector/industry
        ]

        quality_score = service._calculate_data_quality_score(peer_data)

        assert 0.0 <= quality_score <= 1.0
        # Should be penalized for missing sector/industry data
        assert quality_score < 1.0

    def test_calculate_data_quality_score_empty_data(self, service):
        """Test data quality score with empty data"""
        quality_score = service._calculate_data_quality_score([])
        assert quality_score == 0.0


if __name__ == '__main__':
    pytest.main([__file__])