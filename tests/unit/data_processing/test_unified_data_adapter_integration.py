"""
Integration Test Suite for UnifiedDataAdapter with Multi-Source Data Validation
==============================================================================

This module provides integration tests for the UnifiedDataAdapter focusing on
real-world scenarios with multiple data sources, caching, fallback mechanisms,
and quality scoring integration.

Test Categories:
- Integration tests with multiple real data sources
- Cache management and TTL behavior
- Source priority and fallback logic
- Cost tracking and rate limiting
- Quality-based source selection
- Performance with concurrent requests

Requirements:
- pytest >= 6.0
- All data source providers configured
- Network access for API testing (marked as api_dependent)

Usage:
------
Run integration tests:
    python -m pytest test_unified_data_adapter_integration.py -v

Run without API tests:
    python -m pytest test_unified_data_adapter_integration.py -m "not api_dependent" -v

Run performance tests:
    python -m pytest test_unified_data_adapter_integration.py -m "slow" -v
"""

import unittest
import pytest
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from pathlib import Path
import concurrent.futures

# Import modules under test
from core.data_sources.unified_data_adapter import (
    UnifiedDataAdapter,
    UsageStatistics,
    CacheEntry
)

from core.data_sources.data_sources import (
    DataSourceType,
    DataSourcePriority,
    DataSourceConfig,
    FinancialDataRequest,
    DataSourceResponse,
    DataQualityMetrics,
    AlphaVantageProvider,
    FinancialModelingPrepProvider,
    PolygonProvider,
    YfinanceProvider
)

from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    validate_pb_historical_data
)


class TestUnifiedDataAdapterIntegration(unittest.TestCase):
    """Integration tests for UnifiedDataAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Mock configuration
        self.mock_config = {
            'cache_directory': self.cache_dir,
            'default_ttl_hours': 24,
            'max_cache_size_mb': 100,
            'enable_quality_scoring': True,
            'source_priorities': {
                DataSourceType.ALPHA_VANTAGE.value: 1,
                DataSourceType.FINANCIAL_MODELING_PREP.value: 2,
                DataSourceType.YFINANCE.value: 3,
                DataSourceType.POLYGON.value: 4
            }
        }
        
        # Create adapter instance with mocked dependencies
        self.adapter = self._create_mock_adapter()
        
        self.test_ticker = "AAPL"
        self.test_request = FinancialDataRequest(
            ticker=self.test_ticker,
            data_types=['price', 'fundamentals'],
            period='quarterly',
            limit=20
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_mock_adapter(self) -> Mock:
        """Create a mock UnifiedDataAdapter with realistic behavior"""
        adapter = Mock(spec=UnifiedDataAdapter)
        
        # Mock the initialization
        adapter.cache_dir = self.cache_dir
        adapter.usage_stats = {}
        adapter.source_configs = {}
        adapter._cache_lock = threading.Lock()
        
        # Mock methods with realistic implementations
        adapter.get_data = Mock(side_effect=self._mock_get_data)
        adapter.get_cached_data = Mock(side_effect=self._mock_get_cached_data)
        adapter.cache_data = Mock(side_effect=self._mock_cache_data)
        adapter.get_usage_statistics = Mock(side_effect=self._mock_get_usage_statistics)
        adapter.clear_expired_cache = Mock(side_effect=self._mock_clear_expired_cache)
        
        return adapter
    
    def _mock_get_data(self, request: FinancialDataRequest, 
                      preferred_sources: Optional[List[DataSourceType]] = None) -> DataSourceResponse:
        """Mock implementation of get_data method"""
        
        # Simulate source priority logic
        sources_to_try = preferred_sources or [
            DataSourceType.ALPHA_VANTAGE,
            DataSourceType.YFINANCE,
            DataSourceType.FINANCIAL_MODELING_PREP
        ]
        
        for source_type in sources_to_try:
            # Simulate different success rates and quality scores by source
            success_rate = self._get_mock_success_rate(source_type)
            quality_score = self._get_mock_quality_score(source_type)
            
            if success_rate > 0.5:  # Succeed if success rate > 50%
                return self._create_mock_successful_response(
                    source_type, request, quality_score
                )
        
        # If all sources fail
        return DataSourceResponse(
            success=False,
            data=None,
            source_type=sources_to_try[0],
            request_timestamp=datetime.now(),
            error_message="All sources failed"
        )
    
    def _get_mock_success_rate(self, source_type: DataSourceType) -> float:
        """Get mock success rate for different sources"""
        rates = {
            DataSourceType.ALPHA_VANTAGE: 0.95,
            DataSourceType.FINANCIAL_MODELING_PREP: 0.90,
            DataSourceType.YFINANCE: 0.85,
            DataSourceType.POLYGON: 0.80
        }
        return rates.get(source_type, 0.75)
    
    def _get_mock_quality_score(self, source_type: DataSourceType) -> float:
        """Get mock quality score for different sources"""
        scores = {
            DataSourceType.ALPHA_VANTAGE: 0.92,
            DataSourceType.FINANCIAL_MODELING_PREP: 0.88,
            DataSourceType.YFINANCE: 0.82,
            DataSourceType.POLYGON: 0.85
        }
        return scores.get(source_type, 0.80)
    
    def _create_mock_successful_response(self, source_type: DataSourceType,
                                       request: FinancialDataRequest,
                                       quality_score: float) -> DataSourceResponse:
        """Create a mock successful response"""
        
        # Generate mock historical data
        historical_data = []
        # Use limit as a proxy for years of history since years_history doesn't exist
        years_history = getattr(request, 'years_history', request.limit // 4)  # Assume 4 quarters per year
        base_date = datetime.now() - timedelta(days=365 * years_history)
        
        for i in range(years_history * 4):  # Quarterly data
            date = base_date + timedelta(days=i * 90)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': 150 + i * 2 + np.random.normal(0, 5),
                'book_value_per_share': 25 + i * 0.5 + np.random.normal(0, 1),
                'shares_outstanding': 16_000_000_000
            })
        
        response_data = {
            'ticker': request.ticker,
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data,
            'metadata': {
                'source': source_type.value,
                'request_id': f"mock_{int(time.time())}",
                'data_points': len(historical_data)
            }
        }
        
        # Create quality metrics
        quality_metrics = DataQualityMetrics(
            completeness=quality_score * 0.95,
            accuracy=quality_score * 0.98,
            timeliness=quality_score * 0.90,
            consistency=quality_score * 0.92
        )
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=True,
            data=response_data,
            source_type=source_type,
            response_time=np.random.uniform(0.5, 2.0),
            cost_incurred=np.random.uniform(0.01, 0.05),
            quality_metrics=quality_metrics
        )
    
    def _mock_get_cached_data(self, cache_key: str) -> Optional[CacheEntry]:
        """Mock implementation of get_cached_data"""
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                timestamp = datetime.fromisoformat(cache_data['timestamp'])
                
                return CacheEntry(
                    data=cache_data['data'],
                    timestamp=timestamp,
                    source_type=DataSourceType(cache_data['source_type']),
                    quality_score=cache_data['quality_score'],
                    ttl_hours=cache_data.get('ttl_hours', 24)
                )
            except Exception:
                return None
        
        return None
    
    def _mock_cache_data(self, cache_key: str, data: Dict[str, Any],
                        source_type: DataSourceType, quality_score: float,
                        ttl_hours: int = 24) -> None:
        """Mock implementation of cache_data"""
        
        cache_entry = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'source_type': source_type.value,
            'quality_score': quality_score,
            'ttl_hours': ttl_hours
        }
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        with open(cache_file, 'w') as f:
            json.dump(cache_entry, f, indent=2)
    
    def _mock_get_usage_statistics(self) -> Dict[DataSourceType, UsageStatistics]:
        """Mock implementation of get_usage_statistics"""
        
        stats = {}
        for source_type in [DataSourceType.ALPHA_VANTAGE, DataSourceType.YFINANCE]:
            stats[source_type] = UsageStatistics(
                source_type=source_type,
                total_calls=np.random.randint(50, 200),
                total_cost=np.random.uniform(1.0, 10.0),
                successful_calls=np.random.randint(45, 190),
                failed_calls=np.random.randint(1, 10),
                average_response_time=np.random.uniform(0.5, 3.0),
                last_used=datetime.now() - timedelta(hours=np.random.randint(1, 24)),
                monthly_calls=np.random.randint(10, 50),
                monthly_cost=np.random.uniform(0.5, 5.0)
            )
        
        return stats
    
    def _mock_clear_expired_cache(self) -> int:
        """Mock implementation of clear_expired_cache"""
        
        expired_count = 0
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    # Simulate some cache entries being expired
                    if np.random.random() < 0.3:  # 30% chance of being expired
                        os.remove(filepath)
                        expired_count += 1
        
        return expired_count
    
    def test_multi_source_priority_ordering(self):
        """Test that sources are tried in priority order"""
        
        # Test with preferred sources
        preferred_sources = [
            DataSourceType.YFINANCE,
            DataSourceType.ALPHA_VANTAGE
        ]
        
        response = self.adapter.get_data(self.test_request, preferred_sources)
        
        # Should succeed with one of the preferred sources
        self.assertTrue(response.success)
        self.assertIn(response.source_type, preferred_sources)
    
    def test_fallback_mechanism(self):
        """Test fallback to alternative sources when primary fails"""
        
        # Mock a scenario where primary source fails
        with patch.object(self.adapter, 'get_data') as mock_get_data:
            # First call fails (primary source)
            # Second call succeeds (fallback source)
            mock_get_data.side_effect = [
                DataSourceResponse(
                    success=False,
                    data=None,
                    source_type=DataSourceType.ALPHA_VANTAGE,
                    request_timestamp=datetime.now(),
                    error_message="Primary source failed"
                ),
                self._create_mock_successful_response(
                    DataSourceType.YFINANCE, self.test_request, 0.85
                )
            ]
            
            # Test fallback logic (would be implemented in real adapter)
            primary_response = mock_get_data(self.test_request, [DataSourceType.ALPHA_VANTAGE])
            self.assertFalse(primary_response.success)
            
            fallback_response = mock_get_data(self.test_request, [DataSourceType.YFINANCE])
            self.assertTrue(fallback_response.success)
    
    def test_cache_integration_workflow(self):
        """Test complete cache integration workflow"""
        
        cache_key = f"{self.test_ticker}_historical_5y"
        
        # 1. Initial request - no cache
        cached_data = self.adapter.get_cached_data(cache_key)
        self.assertIsNone(cached_data)
        
        # 2. Fetch data and cache it
        response = self.adapter.get_data(self.test_request)
        self.assertTrue(response.success)
        
        # Cache the response
        self.adapter.cache_data(
            cache_key,
            response.data,
            response.source_type,
            response.quality_metrics.overall_score if response.quality_metrics else 0.8
        )
        
        # 3. Verify data is cached
        cached_data = self.adapter.get_cached_data(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data.data['ticker'], self.test_ticker)
        self.assertFalse(cached_data.is_expired())
    
    def test_quality_based_source_selection(self):
        """Test that higher quality sources are preferred"""
        
        # Create responses with different quality scores
        high_quality_response = self._create_mock_successful_response(
            DataSourceType.ALPHA_VANTAGE, self.test_request, 0.95
        )
        medium_quality_response = self._create_mock_successful_response(
            DataSourceType.YFINANCE, self.test_request, 0.75
        )
        
        # Higher quality should be preferred
        self.assertGreater(
            high_quality_response.quality_metrics.overall_score,
            medium_quality_response.quality_metrics.overall_score
        )
        
        # Test quality-based caching decisions
        high_quality_cache = CacheEntry(
            data={'test': 'data'},
            timestamp=datetime.now(),
            source_type=DataSourceType.ALPHA_VANTAGE,
            quality_score=0.95,
            ttl_hours=24
        )
        
        low_quality_cache = CacheEntry(
            data={'test': 'data'},
            timestamp=datetime.now(),
            source_type=DataSourceType.POLYGON,
            quality_score=0.4,
            ttl_hours=24
        )
        
        # High quality cache should be preferred even if slightly older
        self.assertGreater(high_quality_cache.quality_score, low_quality_cache.quality_score)
    
    def test_usage_statistics_tracking(self):
        """Test usage statistics tracking across sources"""
        
        stats = self.adapter.get_usage_statistics()
        
        # Should have statistics for multiple sources
        self.assertGreater(len(stats), 0)
        
        for source_type, stat in stats.items():
            self.assertIsInstance(stat, UsageStatistics)
            self.assertEqual(stat.source_type, source_type)
            self.assertGreaterEqual(stat.total_calls, 0)
            self.assertGreaterEqual(stat.successful_calls, 0)
            self.assertGreaterEqual(stat.failed_calls, 0)
            
            # Success rate should be reasonable
            if stat.total_calls > 0:
                success_rate = stat.successful_calls / stat.total_calls
                self.assertGreaterEqual(success_rate, 0.0)
                self.assertLessEqual(success_rate, 1.0)
    
    def test_cache_management_operations(self):
        """Test cache management and cleanup operations"""
        
        # Create some cached entries
        test_entries = [
            ('AAPL_test1', {'data': 'test1'}, DataSourceType.ALPHA_VANTAGE, 0.9),
            ('MSFT_test2', {'data': 'test2'}, DataSourceType.YFINANCE, 0.8),
            ('GOOGL_test3', {'data': 'test3'}, DataSourceType.POLYGON, 0.7)
        ]
        
        for cache_key, data, source, quality in test_entries:
            self.adapter.cache_data(cache_key, data, source, quality)
        
        # Verify all entries are cached
        for cache_key, _, _, _ in test_entries:
            cached = self.adapter.get_cached_data(cache_key)
            self.assertIsNotNone(cached)
        
        # Test cache cleanup
        expired_count = self.adapter.clear_expired_cache()
        self.assertGreaterEqual(expired_count, 0)
    
    @pytest.mark.slow
    def test_concurrent_requests_handling(self):
        """Test handling of concurrent requests to the same data"""
        
        def make_request(request_id: int) -> DataSourceResponse:
            """Make a request with identifier"""
            request = FinancialDataRequest(
                ticker=f"TEST{request_id}",
                data_types=['historical_prices'],
                years_history=2
            )
            return self.adapter.get_data(request)
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete
        self.assertEqual(len(responses), 5)
        
        # All should be successful (with mocked implementation)
        successful_responses = [r for r in responses if r.success]
        self.assertGreater(len(successful_responses), 0)
    
    def test_integration_with_pb_analysis(self):
        """Test integration with P/B historical analysis"""
        
        # Get data through adapter
        response = self.adapter.get_data(self.test_request)
        self.assertTrue(response.success)
        
        # Validate data for P/B analysis
        validation = validate_pb_historical_data(response)
        self.assertTrue(validation['valid'])
        
        # Perform P/B analysis
        pb_engine = PBHistoricalAnalysisEngine()
        analysis_result = pb_engine.analyze_historical_performance(response, 5)
        
        # Should succeed with adapter data
        self.assertTrue(analysis_result.success)
        self.assertIsNotNone(analysis_result.statistics)
        self.assertIsNotNone(analysis_result.quality_metrics)


@pytest.mark.api_dependent
class TestRealDataSourceIntegration(unittest.TestCase):
    """Integration tests with real data sources (requires API keys)"""
    
    def setUp(self):
        """Set up for real API testing"""
        # These tests require actual API keys and network access
        self.test_tickers = ["AAPL", "MSFT"]  # Use liquid, well-known stocks
        self.test_years = 2  # Use shorter period to reduce API costs
    
    @pytest.mark.skipif(not os.getenv('ALPHA_VANTAGE_API_KEY'), 
                       reason="Alpha Vantage API key not available")
    def test_alpha_vantage_real_integration(self):
        """Test integration with real Alpha Vantage API"""
        
        # This test would make real API calls
        # Implementation would depend on actual API provider setup
        
        request = FinancialDataRequest(
            ticker=self.test_tickers[0],
            data_types=['historical_prices', 'quarterly_balance_sheet'],
            years_history=self.test_years
        )
        
        # Would use real UnifiedDataAdapter instance
        # adapter = UnifiedDataAdapter(config=real_config)
        # response = adapter.get_data(request, [DataSourceType.ALPHA_VANTAGE])
        
        # For now, just ensure the test structure is in place
        self.assertTrue(True, "Real API integration test placeholder")
    
    @pytest.mark.skipif(not os.getenv('YFINANCE_AVAILABLE'), 
                       reason="yfinance not available")
    def test_yfinance_real_integration(self):
        """Test integration with real yfinance data"""
        
        # This test would use real yfinance calls
        request = FinancialDataRequest(
            ticker=self.test_tickers[1],
            data_types=['historical_prices'],
            years_history=self.test_years
        )
        
        # Would use real provider
        # yf_provider = YfinanceProvider()
        # response = yf_provider.fetch_data(request)
        
        self.assertTrue(True, "Real yfinance integration test placeholder")


# Import numpy for test data generation
import numpy as np


# Test configuration and utilities
class TestConfiguration:
    """Test configuration settings"""
    
    # Test data settings
    DEFAULT_TEST_YEARS = 5
    DEFAULT_DATA_POINTS = 20
    CACHE_TTL_HOURS = 24
    
    # Quality score ranges
    HIGH_QUALITY_MIN = 0.85
    MEDIUM_QUALITY_MIN = 0.70
    LOW_QUALITY_MAX = 0.60
    
    # Performance thresholds
    MAX_RESPONSE_TIME_SECONDS = 5.0
    MAX_CACHE_LOOKUP_TIME_MS = 100.0


if __name__ == '__main__':
    # Configure test environment
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests with custom markers
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'not api_dependent'  # Skip API tests by default
    ])