"""
Test suite for IndustryDataService

This module tests the dynamic industry data fetching service functionality
including peer identification, P/B ratio calculation, and caching mechanisms.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the service we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_sources.industry_data_service import IndustryDataService, IndustryStatistics, IndustryPeerData


class TestIndustryDataService(unittest.TestCase):
    """Test cases for IndustryDataService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.service = IndustryDataService(cache_dir=self.temp_dir, cache_ttl_hours=24)
        
        # Mock data for testing
        self.mock_peer_data = [
            IndustryPeerData(
                ticker='AAPL',
                sector='Technology', 
                industry='Consumer Electronics',
                pb_ratio=28.5,
                data_source='test'
            ),
            IndustryPeerData(
                ticker='MSFT',
                sector='Technology',
                industry='Software',
                pb_ratio=12.3,
                data_source='test'
            ),
            IndustryPeerData(
                ticker='GOOGL',
                sector='Technology',
                industry='Internet Content & Information',
                pb_ratio=5.4,
                data_source='test'
            ),
            IndustryPeerData(
                ticker='META',
                sector='Technology',
                industry='Internet Content & Information',
                pb_ratio=6.8,
                data_source='test'
            ),
            IndustryPeerData(
                ticker='AMZN',
                sector='Technology',
                industry='Internet Retail',
                pb_ratio=8.2,
                data_source='test'
            )
        ]
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_initialization(self):
        """Test service initialization"""
        self.assertEqual(self.service.minimum_peer_count, 5)
        self.assertEqual(self.service.maximum_peer_count, 50)
        self.assertTrue(Path(self.temp_dir).exists())
        
    def test_calculate_industry_statistics(self):
        """Test industry statistics calculation"""
        stats = self.service._calculate_industry_statistics(
            'Technology', 'Software', self.mock_peer_data
        )
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats.sector, 'Technology')
        self.assertEqual(stats.industry, 'Software')
        self.assertEqual(stats.peer_count, 5)
        
        # Test statistical calculations
        expected_median = 8.2  # Median of [28.5, 12.3, 5.4, 6.8, 8.2]
        self.assertAlmostEqual(stats.median_pb, expected_median, places=1)
        
        self.assertGreater(stats.max_pb, stats.min_pb)
        self.assertIsNotNone(stats.mean_pb)
        self.assertIsNotNone(stats.std_pb)
        
    def test_calculate_industry_statistics_insufficient_data(self):
        """Test handling of insufficient peer data"""
        insufficient_data = self.mock_peer_data[:3]  # Only 3 peers, need 5
        
        stats = self.service._calculate_industry_statistics(
            'Technology', 'Software', insufficient_data
        )
        
        self.assertIsNone(stats)
        
    def test_data_quality_score_calculation(self):
        """Test data quality score calculation"""
        # All peers have P/B ratios
        quality_score = self.service._calculate_data_quality_score(self.mock_peer_data)
        self.assertGreater(quality_score, 0.5)
        self.assertLessEqual(quality_score, 1.0)
        
        # Some peers missing P/B ratios
        incomplete_data = self.mock_peer_data.copy()
        incomplete_data[0].pb_ratio = None
        incomplete_data[1].pb_ratio = None
        
        lower_quality_score = self.service._calculate_data_quality_score(incomplete_data)
        self.assertLess(lower_quality_score, quality_score)
        
    def test_caching_functionality(self):
        """Test caching save and load functionality"""
        # Create test statistics
        test_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            mean_pb=12.2,
            min_pb=5.4,
            max_pb=28.5,
            peer_tickers=['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN'],
            data_quality_score=0.85,
            last_updated=datetime.now(),
            cache_expiry=datetime.now() + timedelta(hours=24)
        )
        
        # Save to cache
        self.service._save_to_cache('AAPL', test_stats)
        
        # Load from cache
        loaded_stats = self.service._load_from_cache('AAPL')
        
        self.assertIsNotNone(loaded_stats)
        self.assertEqual(loaded_stats.sector, test_stats.sector)
        self.assertEqual(loaded_stats.industry, test_stats.industry)
        self.assertEqual(loaded_stats.peer_count, test_stats.peer_count)
        self.assertAlmostEqual(loaded_stats.median_pb, test_stats.median_pb, places=2)
        
    def test_cache_expiry(self):
        """Test cache expiry functionality"""
        # Create expired statistics
        expired_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            cache_expiry=datetime.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        self.assertFalse(self.service._is_cache_valid(expired_stats))
        
        # Create valid statistics
        valid_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            cache_expiry=datetime.now() + timedelta(hours=1)  # Expires in 1 hour
        )
        
        self.assertTrue(self.service._is_cache_valid(valid_stats))
        
    @patch('yfinance.Ticker')
    def test_get_sector_classification(self, mock_ticker):
        """Test sector classification retrieval"""
        # Mock yfinance response
        mock_info = {
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'shortName': 'Apple Inc.'
        }
        mock_ticker.return_value.info = mock_info
        
        result = self.service._get_sector_classification('AAPL')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['sector'], 'Technology')
        self.assertEqual(result['industry'], 'Consumer Electronics')
        self.assertEqual(result['company_name'], 'Apple Inc.')
        
    @patch('yfinance.Ticker')
    def test_get_sector_classification_missing_data(self, mock_ticker):
        """Test handling of missing sector classification data"""
        # Mock yfinance response with missing sector
        mock_info = {
            'shortName': 'Test Company'
            # Missing sector and industry
        }
        mock_ticker.return_value.info = mock_info
        
        result = self.service._get_sector_classification('TEST')
        
        self.assertIsNone(result)
        
    def test_get_common_tickers_by_sector(self):
        """Test sector ticker mapping"""
        tech_tickers = self.service._get_common_tickers_by_sector('Technology')
        self.assertIn('AAPL', tech_tickers)
        self.assertIn('MSFT', tech_tickers)
        self.assertGreater(len(tech_tickers), 10)
        
        financial_tickers = self.service._get_common_tickers_by_sector('Financial Services')
        self.assertIn('JPM', financial_tickers)
        self.assertIn('BAC', financial_tickers)
        
        # Test unknown sector
        unknown_tickers = self.service._get_common_tickers_by_sector('Unknown Sector')
        self.assertEqual(len(unknown_tickers), 0)
        
    @patch('yfinance.Ticker')
    def test_fetch_single_ticker_pb_data(self, mock_ticker):
        """Test fetching P/B data for a single ticker"""
        # Mock successful yfinance response
        mock_info = {
            'priceToBook': 15.2,
            'bookValue': 22.95,
            'marketCap': 2800000000000,
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        mock_ticker.return_value.info = mock_info
        
        result = self.service._fetch_single_ticker_pb_data('AAPL')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.ticker, 'AAPL')
        self.assertEqual(result.pb_ratio, 15.2)
        self.assertEqual(result.book_value_per_share, 22.95)
        self.assertEqual(result.sector, 'Technology')
        self.assertEqual(result.data_source, 'yfinance')
        
    @patch('yfinance.Ticker')
    def test_fetch_single_ticker_pb_data_invalid_pb(self, mock_ticker):
        """Test handling of invalid P/B ratio data"""
        # Mock response with invalid P/B ratio
        mock_info = {
            'priceToBook': None,  # or 0, or negative
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        mock_ticker.return_value.info = mock_info
        
        result = self.service._fetch_single_ticker_pb_data('TEST')
        
        self.assertIsNone(result)
        
    def test_cache_info(self):
        """Test cache information retrieval"""
        # Save some test data to cache
        test_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            cache_expiry=datetime.now() + timedelta(hours=24)
        )
        
        self.service._save_to_cache('AAPL', test_stats)
        self.service._save_to_cache('MSFT', test_stats)
        
        cache_info = self.service.get_cache_info()
        
        self.assertEqual(cache_info['total_cached_files'], 2)
        self.assertEqual(cache_info['cache_ttl_hours'], 24)
        self.assertTrue(cache_info['cache_dir'].endswith(Path(self.temp_dir).name))
        self.assertEqual(len(cache_info['files']), 2)
        
    def test_clear_cache_specific_ticker(self):
        """Test clearing cache for specific ticker"""
        # Save test data
        test_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            cache_expiry=datetime.now() + timedelta(hours=24)
        )
        
        self.service._save_to_cache('AAPL', test_stats)
        self.service._save_to_cache('MSFT', test_stats)
        
        # Clear cache for one ticker
        self.service.clear_cache('AAPL')
        
        # Verify one is cleared, one remains
        self.assertIsNone(self.service._load_from_cache('AAPL'))
        self.assertIsNotNone(self.service._load_from_cache('MSFT'))
        
    def test_clear_cache_all(self):
        """Test clearing all cache"""
        # Save test data
        test_stats = IndustryStatistics(
            sector='Technology',
            industry='Software',
            peer_count=5,
            median_pb=8.5,
            cache_expiry=datetime.now() + timedelta(hours=24)
        )
        
        self.service._save_to_cache('AAPL', test_stats)
        self.service._save_to_cache('MSFT', test_stats)
        
        # Clear all cache
        self.service.clear_cache()
        
        # Verify all cleared
        self.assertIsNone(self.service._load_from_cache('AAPL'))
        self.assertIsNone(self.service._load_from_cache('MSFT'))


class TestIndustryDataIntegration(unittest.TestCase):
    """Integration tests requiring actual API calls (run separately)"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = IndustryDataService(cache_dir=self.temp_dir, cache_ttl_hours=1)
        
    def tearDown(self):
        """Clean up integration test fixtures"""
        shutil.rmtree(self.temp_dir)
        
    @unittest.skip("Integration test - requires API access")
    def test_real_industry_data_fetch(self):
        """Test with real API calls (skipped by default)"""
        # This test would make real API calls to yfinance
        # Only run when testing with real API access
        
        result = self.service.get_industry_pb_statistics('AAPL')
        
        if result:  # Only test if we got data back
            self.assertIsNotNone(result.median_pb)
            self.assertGreater(result.peer_count, 0)
            self.assertEqual(result.sector, 'Technology')
            
    @unittest.skip("Integration test - requires API access")
    def test_sector_classification_integration(self):
        """Test real sector classification (skipped by default)"""
        sector_info = self.service._get_sector_classification('AAPL')
        
        if sector_info:  # Only test if we got data back
            self.assertIn('sector', sector_info)
            self.assertIn('industry', sector_info)


if __name__ == '__main__':
    # Run unit tests by default
    unittest.main(verbosity=2)