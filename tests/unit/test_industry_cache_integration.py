"""
Unit tests for industry data caching integration
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.analysis.pb.pb_valuation import PBValuator
    from core.data_sources.industry_data_service import IndustryDataService, IndustryStatistics
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestIndustryCacheIntegration(unittest.TestCase):
    """Test suite for industry data caching integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_financial_calculator = Mock()
        self.mock_financial_calculator.ticker_symbol = "AAPL"
        self.mock_financial_calculator.enhanced_data_manager = None

    def test_pb_valuator_initializes_industry_service(self):
        """Test that PBValuator properly initializes IndustryDataService"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Should have industry service initialized
        self.assertIsNotNone(pb_valuator.industry_service)
        self.assertIsInstance(pb_valuator.industry_service, IndustryDataService)

    def test_get_cache_info_with_service_available(self):
        """Test get_cache_info when IndustryDataService is available"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Mock the industry service
        mock_cache_info = {
            'cache_dir': 'data/cache',
            'total_cached_files': 5,
            'cache_ttl_hours': 24.0
        }
        pb_valuator.industry_service.get_cache_info = Mock(return_value=mock_cache_info)
        
        result = pb_valuator.get_cache_info()
        
        self.assertEqual(result, mock_cache_info)
        pb_valuator.industry_service.get_cache_info.assert_called_once()

    def test_clear_industry_cache(self):
        """Test clearing industry cache"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Mock the clear_cache method
        pb_valuator.industry_service.clear_cache = Mock()
        
        # Test clearing specific ticker
        pb_valuator.clear_industry_cache("AAPL")
        pb_valuator.industry_service.clear_cache.assert_called_with("AAPL")
        
        # Test clearing all cache
        pb_valuator.clear_industry_cache()
        pb_valuator.industry_service.clear_cache.assert_called_with(None)

    @patch('core.analysis.pb.pb_valuation.IndustryDataService')
    def test_pb_valuator_handles_service_initialization_failure(self, mock_service_class):
        """Test that PBValuator handles IndustryDataService initialization failure gracefully"""
        # Make IndustryDataService initialization raise an exception
        mock_service_class.side_effect = Exception("Service initialization failed")
        
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Should gracefully handle the failure
        self.assertIsNone(pb_valuator.industry_service)

    def test_compare_to_industry_with_real_time_data(self):
        """Test _compare_to_industry method with real-time cached data"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Create mock industry statistics
        mock_industry_stats = IndustryStatistics(
            sector="Technology",
            industry="Consumer Electronics",
            peer_count=15,
            median_pb=10.97,
            q1_pb=6.11,
            q3_pb=16.28,
            last_updated=datetime.now(),
            cache_expiry=datetime.now() + timedelta(hours=24)
        )
        
        # Mock the industry service
        pb_valuator.industry_service.get_industry_pb_statistics = Mock(return_value=mock_industry_stats)
        
        result = pb_valuator._compare_to_industry(12.5, "Technology", "AAPL")
        
        # Should contain cache info
        self.assertIn('cache_info', result)
        cache_info = result['cache_info']
        
        self.assertEqual(cache_info['data_source'], 'real_time')
        self.assertTrue(cache_info['cache_used'])
        self.assertEqual(cache_info['peer_count'], 15)
        self.assertIn('data_quality', cache_info)
        
        # Should use real-time benchmarks
        benchmarks = result['benchmarks']
        self.assertEqual(benchmarks['median'], 10.97)

    def test_compare_to_industry_with_static_fallback(self):
        """Test _compare_to_industry method falling back to static benchmarks"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Mock industry service to return None (no real-time data)
        pb_valuator.industry_service.get_industry_pb_statistics = Mock(return_value=None)
        
        result = pb_valuator._compare_to_industry(3.5, "Technology", "AAPL")
        
        # Should contain cache info indicating fallback
        self.assertIn('cache_info', result)
        cache_info = result['cache_info']
        
        self.assertEqual(cache_info['data_source'], 'static_fallback')
        self.assertFalse(cache_info['cache_used'])
        
        # Should use static benchmarks
        benchmarks = result['benchmarks']
        self.assertEqual(benchmarks['median'], 3.5)  # Technology static median

    def test_compare_to_industry_without_ticker(self):
        """Test _compare_to_industry method without ticker symbol"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        result = pb_valuator._compare_to_industry(3.5, "Technology")
        
        # Should contain cache info indicating static data
        self.assertIn('cache_info', result)
        cache_info = result['cache_info']
        
        self.assertEqual(cache_info['data_source'], 'static_fallback')
        self.assertFalse(cache_info['cache_used'])

    def test_compare_to_industry_with_service_error(self):
        """Test _compare_to_industry method when industry service raises an error"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        
        # Mock industry service to raise an exception
        pb_valuator.industry_service.get_industry_pb_statistics = Mock(
            side_effect=Exception("API error")
        )
        
        result = pb_valuator._compare_to_industry(3.5, "Technology", "AAPL")
        
        # Should fall back to static benchmarks
        self.assertIn('cache_info', result)
        cache_info = result['cache_info']
        
        self.assertEqual(cache_info['data_source'], 'static_fallback')
        self.assertFalse(cache_info['cache_used'])

    def test_get_cache_info_without_service(self):
        """Test get_cache_info when IndustryDataService is not available"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        pb_valuator.industry_service = None  # Simulate service not available
        
        result = pb_valuator.get_cache_info()
        
        self.assertFalse(result['service_available'])
        self.assertIn('message', result)

    def test_clear_cache_without_service(self):
        """Test clear_industry_cache when IndustryDataService is not available"""
        pb_valuator = PBValuator(self.mock_financial_calculator)
        pb_valuator.industry_service = None  # Simulate service not available
        
        # Should not raise an error
        pb_valuator.clear_industry_cache("AAPL")
        pb_valuator.clear_industry_cache()


if __name__ == '__main__':
    unittest.main()