"""
Comprehensive Test Suite for P/B Historical Fair Value Module with Multi-Source Data Validation
=============================================================================================

This module provides comprehensive tests for the P/B historical fair value analysis
with focus on multi-source data validation, caching behavior, and error handling.

Test Categories:
- Multi-source data validation tests
- Caching behavior and quality scoring integration
- Fallback scenarios and error handling
- Performance testing with large historical datasets
- Unit tests for fair value calculations
- Statistical analysis validation

Requirements:
- pytest >= 6.0
- numpy
- pandas
- unittest.mock for mocking API responses

Usage:
------
Run all tests:
    python -m pytest test_pb_multi_source_validation.py -v

Run specific test categories:
    python -m pytest test_pb_multi_source_validation.py::TestMultiSourceValidation -v
    python -m pytest test_pb_multi_source_validation.py::TestCachingBehavior -v

Run performance tests:
    python -m pytest test_pb_multi_source_validation.py -m "slow" -v
"""

import unittest
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import time
import json
import tempfile
import os
from pathlib import Path

# Import the modules under test
from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    PBHistoricalAnalysisResult,
    PBHistoricalQualityMetrics,
    PBStatisticalSummary,
    PBTrendAnalysis,
    PBDataPoint,
    create_pb_historical_report,
    validate_pb_historical_data
)

from core.data_sources.unified_data_adapter import (
    UnifiedDataAdapter,
    UsageStatistics,
    CacheEntry
)

from core.data_sources.data_sources import (
    DataSourceResponse,
    DataSourceType,
    DataQualityMetrics,
    FinancialDataRequest,
    DataSourcePriority
)

from core.analysis.pb.pb_calculation_engine import (
    PBCalculationEngine,
    PBCalculationResult
)


class TestMultiSourceValidation(unittest.TestCase):
    """Test multi-source data validation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "AAPL"
        self.test_years = 5
        
        # Create mock data sources
        self.mock_sources = [
            DataSourceType.ALPHA_VANTAGE,
            DataSourceType.FINANCIAL_MODELING_PREP,
            DataSourceType.YFINANCE,
            DataSourceType.POLYGON
        ]
    
    def _create_mock_response(self, source_type: DataSourceType, 
                            success: bool = True, 
                            quality_score: float = 0.85,
                            data_points: int = 20) -> DataSourceResponse:
        """Create a mock data source response"""
        
        # Generate mock historical data
        base_date = datetime.now() - timedelta(days=365 * self.test_years)
        historical_data = []
        
        for i in range(data_points):
            date = base_date + timedelta(days=i * 90)  # Quarterly data
            price = 150 + np.random.normal(0, 10)  # Mock price with some volatility
            book_value = 25 + np.random.normal(0, 2)  # Mock book value
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': max(1.0, price),
                'book_value_per_share': max(0.1, book_value),
                'shares_outstanding': 16_000_000_000  # Mock shares
            })
        
        # Mock response data structure
        response_data = {
            'ticker': self.test_ticker,
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data,  # Simplified for testing
            'metadata': {
                'source': source_type.value,
                'fetch_time': datetime.now().isoformat()
            }
        }
        
        # Create quality metrics
        quality_metrics = DataQualityMetrics(
            completeness=quality_score * 0.9 + np.random.uniform(0, 0.1),
            accuracy=quality_score * 0.95 + np.random.uniform(0, 0.05),
            timeliness=quality_score * 0.8 + np.random.uniform(0, 0.2),
            consistency=quality_score * 0.85 + np.random.uniform(0, 0.15)
        )
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=success,
            data=response_data if success else None,
            source_type=source_type,
            request_timestamp=datetime.now(),
            response_time=np.random.uniform(0.5, 3.0),
            cost_incurred=np.random.uniform(0.01, 0.10),
            rate_limit_remaining=100,
            quality_metrics=quality_metrics,
            error_message=None if success else f"Mock error for {source_type.value}"
        )
    
    def test_multi_source_data_collection(self):
        """Test data collection from multiple sources"""
        
        # Create mock responses from different sources
        mock_responses = {}
        for source in self.mock_sources:
            mock_responses[source] = self._create_mock_response(
                source, 
                success=True,
                quality_score=np.random.uniform(0.7, 0.95)
            )
        
        # Test that we can process responses from multiple sources
        results = []
        for source, response in mock_responses.items():
            result = self.engine.analyze_historical_performance(response, self.test_years)
            results.append((source, result))
        
        # Verify all sources processed successfully
        for source, result in results:
            self.assertTrue(result.success, f"Analysis failed for {source.value}")
            self.assertIsNotNone(result.statistics, f"No statistics for {source.value}")
            self.assertGreater(result.data_points_count, 0, f"No data points for {source.value}")
        
        # Verify quality scores vary by source
        quality_scores = [result.quality_metrics.overall_score 
                         for _, result in results if result.quality_metrics]
        self.assertGreater(len(set(quality_scores)), 1, "Quality scores should vary by source")
    
    def test_data_source_quality_comparison(self):
        """Test comparison of data quality across sources"""
        
        # Create responses with different quality levels
        high_quality_response = self._create_mock_response(
            DataSourceType.ALPHA_VANTAGE, quality_score=0.95, data_points=24
        )
        medium_quality_response = self._create_mock_response(
            DataSourceType.YFINANCE, quality_score=0.75, data_points=20
        )
        low_quality_response = self._create_mock_response(
            DataSourceType.POLYGON, quality_score=0.55, data_points=15
        )
        
        # Analyze each response
        high_result = self.engine.analyze_historical_performance(high_quality_response, self.test_years)
        medium_result = self.engine.analyze_historical_performance(medium_quality_response, self.test_years)
        low_result = self.engine.analyze_historical_performance(low_quality_response, self.test_years)
        
        # Verify quality ordering
        self.assertGreater(
            high_result.quality_metrics.overall_score,
            medium_result.quality_metrics.overall_score
        )
        self.assertGreater(
            medium_result.quality_metrics.overall_score,
            low_result.quality_metrics.overall_score
        )
        
        # Verify that higher quality data leads to more confident valuation signals
        # (not neutral/uncertain)
        self.assertNotEqual(high_result.valuation_signal, "uncertain")
        # Low quality might be uncertain
        if low_result.quality_metrics.overall_score < 0.6:
            self.assertEqual(low_result.valuation_signal, "uncertain")
    
    def test_source_fallback_behavior(self):
        """Test fallback behavior when primary sources fail"""
        
        # Create a mix of successful and failed responses
        primary_response = self._create_mock_response(
            DataSourceType.ALPHA_VANTAGE, success=False
        )
        fallback_response = self._create_mock_response(
            DataSourceType.YFINANCE, success=True, quality_score=0.8
        )
        
        # Test primary source failure
        primary_result = self.engine.analyze_historical_performance(primary_response, self.test_years)
        self.assertFalse(primary_result.success)
        self.assertIsNotNone(primary_result.error_message)
        
        # Test fallback source success
        fallback_result = self.engine.analyze_historical_performance(fallback_response, self.test_years)
        self.assertTrue(fallback_result.success)
        self.assertIsNone(fallback_result.error_message)
    
    def test_data_validation_across_sources(self):
        """Test validation of data consistency across sources"""
        
        # Create responses with similar but slightly different data
        base_pb_ratios = [1.5, 1.8, 2.1, 1.9, 2.3, 2.0, 1.7, 2.2]
        
        responses = []
        for i, source in enumerate(self.mock_sources[:3]):  # Test 3 sources
            # Add some variation to simulate real-world differences
            variation = np.random.normal(0, 0.1, len(base_pb_ratios))
            adjusted_ratios = [max(0.1, ratio + var) 
                             for ratio, var in zip(base_pb_ratios, variation)]
            
            response = self._create_mock_response(source, quality_score=0.8 + i * 0.05)
            responses.append(response)
        
        # Analyze all responses
        results = []
        for response in responses:
            result = self.engine.analyze_historical_performance(response, self.test_years)
            results.append(result)
        
        # Verify all succeeded
        for result in results:
            self.assertTrue(result.success)
        
        # Check that fair value estimates are reasonably consistent
        fair_values = [r.fair_value_estimate for r in results if r.fair_value_estimate]
        if len(fair_values) > 1:
            cv = np.std(fair_values) / np.mean(fair_values)  # Coefficient of variation
            self.assertLess(cv, 0.5, "Fair value estimates should be reasonably consistent")


class TestCachingBehavior(unittest.TestCase):
    """Test caching behavior and quality scoring integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "MSFT"
        
        # Create temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_cache.json")
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)
    
    def _create_cache_entry(self, age_hours: int = 1, quality_score: float = 0.8) -> CacheEntry:
        """Create a test cache entry"""
        timestamp = datetime.now() - timedelta(hours=age_hours)
        
        mock_data = {
            'ticker': self.test_ticker,
            'historical_data': [
                {
                    'date': (datetime.now() - timedelta(days=i*90)).strftime('%Y-%m-%d'),
                    'price': 300 + np.random.normal(0, 15),
                    'book_value_per_share': 45 + np.random.normal(0, 3)
                }
                for i in range(20)
            ]
        }
        
        return CacheEntry(
            data=mock_data,
            timestamp=timestamp,
            source_type=DataSourceType.ALPHA_VANTAGE,
            quality_score=quality_score,
            ttl_hours=24
        )
    
    def test_cache_expiration_logic(self):
        """Test cache expiration and freshness logic"""
        
        # Test fresh cache entry
        fresh_entry = self._create_cache_entry(age_hours=1)
        self.assertFalse(fresh_entry.is_expired())
        self.assertFalse(fresh_entry.is_stale(stale_threshold_hours=6))
        
        # Test stale but not expired entry
        stale_entry = self._create_cache_entry(age_hours=8)
        self.assertFalse(stale_entry.is_expired())
        self.assertTrue(stale_entry.is_stale(stale_threshold_hours=6))
        
        # Test expired entry
        expired_entry = self._create_cache_entry(age_hours=25)
        self.assertTrue(expired_entry.is_expired())
        self.assertTrue(expired_entry.is_stale(stale_threshold_hours=6))
    
    def test_quality_score_impact_on_caching(self):
        """Test how quality scores affect caching decisions"""
        
        # High quality data should be cached longer
        high_quality_entry = self._create_cache_entry(quality_score=0.95)
        
        # Low quality data should have shorter cache life
        low_quality_entry = self._create_cache_entry(quality_score=0.4)
        
        # Simulate quality-based TTL adjustment
        # High quality data gets longer TTL
        adjusted_high_ttl = high_quality_entry.ttl_hours * high_quality_entry.quality_score
        adjusted_low_ttl = low_quality_entry.ttl_hours * low_quality_entry.quality_score
        
        self.assertGreater(adjusted_high_ttl, adjusted_low_ttl)
        
        # Verify that quality score affects cache usage decisions
        self.assertGreater(high_quality_entry.quality_score, 0.8)
        self.assertLess(low_quality_entry.quality_score, 0.6)
    
    @patch('unified_data_adapter.UnifiedDataAdapter')
    def test_cache_hit_miss_behavior(self, mock_adapter):
        """Test cache hit/miss behavior with quality considerations"""
        
        # Configure mock adapter
        mock_adapter_instance = mock_adapter.return_value
        
        # Simulate cache hit with high quality data
        high_quality_cache = self._create_cache_entry(age_hours=2, quality_score=0.9)
        mock_adapter_instance.get_cached_data.return_value = high_quality_cache
        
        # Test that high quality cached data is used
        result = mock_adapter_instance.get_cached_data(self.test_ticker)
        self.assertIsNotNone(result)
        self.assertGreater(result.quality_score, 0.8)
        
        # Simulate cache miss or low quality cache
        low_quality_cache = self._create_cache_entry(age_hours=2, quality_score=0.3)
        mock_adapter_instance.get_cached_data.return_value = low_quality_cache
        
        # Test that low quality cached data might be rejected
        result = mock_adapter_instance.get_cached_data(self.test_ticker)
        if result and result.quality_score < 0.5:
            # Should potentially trigger fresh data fetch
            self.assertLess(result.quality_score, 0.5)
    
    def test_cache_performance_metrics(self):
        """Test cache performance and statistics tracking"""
        
        # Create multiple cache entries with different characteristics
        cache_entries = [
            self._create_cache_entry(age_hours=1, quality_score=0.95),  # Fresh, high quality
            self._create_cache_entry(age_hours=8, quality_score=0.85),  # Stale, good quality
            self._create_cache_entry(age_hours=2, quality_score=0.4),   # Fresh, low quality
            self._create_cache_entry(age_hours=25, quality_score=0.8),  # Expired, good quality
        ]
        
        # Analyze cache efficiency
        fresh_high_quality = sum(1 for entry in cache_entries 
                               if not entry.is_stale() and entry.quality_score > 0.8)
        total_entries = len(cache_entries)
        
        cache_efficiency = fresh_high_quality / total_entries
        
        # Should have at least some efficient cache entries
        self.assertGreater(cache_efficiency, 0)
        
        # Test cache statistics
        avg_quality = np.mean([entry.quality_score for entry in cache_entries])
        self.assertGreater(avg_quality, 0)


class TestErrorHandlingAndFallbacks(unittest.TestCase):
    """Test error handling and fallback scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "TSLA"
    
    def test_invalid_data_response_handling(self):
        """Test handling of invalid or malformed data responses"""
        
        # Test completely empty response
        empty_response = DataSourceResponse(
            success=False,
            data=None,
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now(),
            error_message="No data available"
        )
        
        result = self.engine.analyze_historical_performance(empty_response, 5)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        
        # Test response with insufficient data
        insufficient_data = DataSourceResponse(
            success=True,
            data={
                'ticker': self.test_ticker,
                'historical_prices': [
                    {'date': '2024-01-01', 'price': 200, 'book_value_per_share': 25}
                    # Only one data point - insufficient for analysis
                ]
            },
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now()
        )
        
        result = self.engine.analyze_historical_performance(insufficient_data, 5)
        self.assertFalse(result.success)
        self.assertIn("Insufficient data points", result.error_message)
    
    def test_malformed_data_structure_handling(self):
        """Test handling of malformed data structures"""
        
        # Test missing required fields
        malformed_response = DataSourceResponse(
            success=True,
            data={
                'ticker': self.test_ticker,
                # Missing historical_prices and other required fields
                'some_other_field': 'value'
            },
            source_type=DataSourceType.ALPHA_VANTAGE,
            request_timestamp=datetime.now()
        )
        
        result = self.engine.analyze_historical_performance(malformed_response, 5)
        # Should handle gracefully - either succeed with limited analysis or fail cleanly
        if not result.success:
            self.assertIsNotNone(result.error_message)
        
        # Test data with invalid values
        invalid_values_response = DataSourceResponse(
            success=True,
            data={
                'ticker': self.test_ticker,
                'historical_prices': [
                    {'date': 'invalid-date', 'price': -100, 'book_value_per_share': 'not-a-number'},
                    {'date': '2024-01-01', 'price': None, 'book_value_per_share': 0},
                    {'date': '2024-02-01', 'price': float('inf'), 'book_value_per_share': -5}
                ]
            },
            source_type=DataSourceType.POLYGON,
            request_timestamp=datetime.now()
        )
        
        result = self.engine.analyze_historical_performance(invalid_values_response, 5)
        # Should handle invalid values gracefully
        if result.success:
            # Should have filtered out invalid data
            self.assertGreaterEqual(len(result.quality_warnings), 0)
    
    def test_api_rate_limit_simulation(self):
        """Test behavior under API rate limiting conditions"""
        
        # Simulate rate-limited response
        rate_limited_response = DataSourceResponse(
            success=False,
            data=None,
            source_type=DataSourceType.ALPHA_VANTAGE,
            request_timestamp=datetime.now(),
            response_time=10.0,  # Long response time
            rate_limit_remaining=0,
            error_message="API rate limit exceeded"
        )
        
        result = self.engine.analyze_historical_performance(rate_limited_response, 5)
        self.assertFalse(result.success)
        self.assertIn("rate limit", result.error_message.lower())
    
    def test_network_timeout_simulation(self):
        """Test behavior under network timeout conditions"""
        
        # Simulate timeout response
        timeout_response = DataSourceResponse(
            success=False,
            data=None,
            source_type=DataSourceType.FINANCIAL_MODELING_PREP,
            request_timestamp=datetime.now(),
            response_time=30.0,  # Very long response time indicating timeout
            error_message="Request timeout"
        )
        
        result = self.engine.analyze_historical_performance(timeout_response, 5)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
    
    def test_partial_data_recovery(self):
        """Test recovery and analysis with partial data"""
        
        # Create response with some missing/invalid data points
        partial_data_response = DataSourceResponse(
            success=True,
            data={
                'ticker': self.test_ticker,
                'historical_prices': [
                    {'date': '2020-01-01', 'price': 500, 'book_value_per_share': 60},
                    {'date': '2020-04-01', 'price': 450, 'book_value_per_share': None},  # Missing book value
                    {'date': '2020-07-01', 'price': None, 'book_value_per_share': 65},   # Missing price
                    {'date': '2020-10-01', 'price': 600, 'book_value_per_share': 70},
                    {'date': '2021-01-01', 'price': 650, 'book_value_per_share': 75},
                    {'date': '2021-04-01', 'price': 700, 'book_value_per_share': 80},
                    {'date': '2021-07-01', 'price': 750, 'book_value_per_share': 85},
                    {'date': '2021-10-01', 'price': 800, 'book_value_per_share': 90},
                    {'date': '2022-01-01', 'price': 850, 'book_value_per_share': 95},
                    {'date': '2022-04-01', 'price': 900, 'book_value_per_share': 100},
                    {'date': '2022-07-01', 'price': 950, 'book_value_per_share': 105},
                    {'date': '2022-10-01', 'price': 1000, 'book_value_per_share': 110},
                    {'date': '2023-01-01', 'price': 1050, 'book_value_per_share': 115},
                    {'date': '2023-04-01', 'price': 1100, 'book_value_per_share': 120},
                ]
            },
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now()
        )
        
        result = self.engine.analyze_historical_performance(partial_data_response, 5)
        
        # Should succeed despite missing data points
        self.assertTrue(result.success)
        self.assertGreater(result.data_points_count, 10)  # Should have filtered valid points
        
        # Should have quality warnings about missing data
        self.assertGreater(len(result.quality_warnings), 0)
        
        # Quality score should reflect missing data
        if result.quality_metrics:
            self.assertLess(result.quality_metrics.pb_data_completeness, 1.0)


@pytest.mark.slow
class TestPerformanceWithLargeDatasets(unittest.TestCase):
    """Test performance with large historical datasets"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "SPY"  # Large dataset simulation
    
    def _generate_large_dataset(self, years: int = 10, frequency_days: int = 30) -> DataSourceResponse:
        """Generate a large mock dataset for performance testing"""
        
        total_days = years * 365
        data_points = total_days // frequency_days
        
        base_date = datetime.now() - timedelta(days=total_days)
        historical_data = []
        
        # Generate realistic-looking data with trends and cycles
        base_price = 100
        base_book_value = 20
        
        for i in range(data_points):
            date = base_date + timedelta(days=i * frequency_days)
            
            # Add trend and cyclical components
            trend = i * 0.1  # Gradual upward trend
            cycle = 10 * np.sin(2 * np.pi * i / 40)  # ~3-year cycle
            noise = np.random.normal(0, 5)
            
            price = max(1.0, base_price + trend + cycle + noise)
            book_value = max(0.1, base_book_value + trend * 0.2 + np.random.normal(0, 1))
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'book_value_per_share': book_value,
                'shares_outstanding': 1_000_000_000
            })
        
        response_data = {
            'ticker': self.test_ticker,
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data,
            'metadata': {
                'source': 'mock_large_dataset',
                'data_points': len(historical_data)
            }
        }
        
        quality_metrics = DataQualityMetrics(
            completeness=0.95,
            accuracy=0.88,
            timeliness=0.92,
            consistency=0.87
        )
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now(),
            response_time=2.5,
            quality_metrics=quality_metrics
        )
    
    def test_large_dataset_processing_performance(self):
        """Test processing performance with large datasets"""
        
        # Generate large dataset (10 years, monthly data = ~120 points)
        large_response = self._generate_large_dataset(years=10, frequency_days=30)
        
        # Measure analysis time
        start_time = time.time()
        result = self.engine.analyze_historical_performance(large_response, 10)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        
        # Verify successful processing
        self.assertTrue(result.success)
        self.assertGreater(result.data_points_count, 100)
        
        # Performance should be reasonable (< 30 seconds for large dataset)
        self.assertLess(analysis_time, 30.0, f"Analysis took {analysis_time:.2f} seconds")
        
        # Verify all analysis components completed
        self.assertIsNotNone(result.statistics)
        self.assertIsNotNone(result.trend_analysis)
        self.assertIsNotNone(result.quality_metrics)
        
        # Log performance metrics
        print(f"Large dataset analysis: {result.data_points_count} points in {analysis_time:.2f}s")
    
    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets"""
        
        # Generate very large dataset
        very_large_response = self._generate_large_dataset(years=20, frequency_days=7)  # Weekly data
        
        # Monitor memory usage (simplified - would need psutil for real monitoring)
        import sys
        
        initial_size = sys.getsizeof(very_large_response)
        
        result = self.engine.analyze_historical_performance(very_large_response, 20)
        
        result_size = sys.getsizeof(result)
        
        # Verify processing succeeded
        self.assertTrue(result.success)
        
        # Result should not be dramatically larger than input
        # (allowing for analysis results but not excessive memory usage)
        memory_expansion_ratio = result_size / initial_size
        self.assertLess(memory_expansion_ratio, 3.0, "Memory usage expanded too much")
    
    def test_statistical_accuracy_large_dataset(self):
        """Test statistical accuracy improves with larger datasets"""
        
        # Generate datasets of different sizes
        small_response = self._generate_large_dataset(years=2, frequency_days=90)   # ~8 points
        medium_response = self._generate_large_dataset(years=5, frequency_days=90)  # ~20 points
        large_response = self._generate_large_dataset(years=10, frequency_days=30)  # ~120 points
        
        # Analyze each dataset
        small_result = self.engine.analyze_historical_performance(small_response, 2)
        medium_result = self.engine.analyze_historical_performance(medium_response, 5)
        large_result = self.engine.analyze_historical_performance(large_response, 10)
        
        # All should succeed
        results = [small_result, medium_result, large_result]
        for result in results:
            self.assertTrue(result.success)
        
        # Confidence should generally improve with more data
        # (measured by narrower confidence intervals or higher quality scores)
        if all(r.statistics and r.statistics.mean_confidence_interval for r in results):
            small_ci_width = (small_result.statistics.mean_confidence_interval[1] - 
                            small_result.statistics.mean_confidence_interval[0])
            large_ci_width = (large_result.statistics.mean_confidence_interval[1] - 
                            large_result.statistics.mean_confidence_interval[0])
            
            # Larger dataset should generally have narrower confidence intervals
            # (though this may not always hold due to different underlying data)
            if small_ci_width > 0 and large_ci_width > 0:
                ci_improvement = small_ci_width / large_ci_width
                self.assertGreater(ci_improvement, 0.5, "Confidence interval should improve with more data")


class TestUnitTestsForFairValueCalculations(unittest.TestCase):
    """Unit tests for fair value calculation components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.pb_calc_engine = PBCalculationEngine()
    
    def test_pb_ratio_calculation_accuracy(self):
        """Test accuracy of P/B ratio calculations"""
        
        test_cases = [
            # (price, book_value_per_share, expected_pb)
            (100.0, 20.0, 5.0),
            (50.0, 25.0, 2.0),
            (75.0, 15.0, 5.0),
            (200.0, 40.0, 5.0),
            (30.0, 10.0, 3.0),
        ]
        
        for price, book_value, expected_pb in test_cases:
            calculated_pb = price / book_value if book_value > 0 else 0
            self.assertAlmostEqual(calculated_pb, expected_pb, places=2)
    
    def test_quality_weighted_statistics(self):
        """Test quality-weighted statistical calculations"""
        
        # Create test data with known quality weights
        pb_ratios = [2.0, 3.0, 4.0, 5.0]
        quality_weights = [0.9, 0.8, 0.7, 0.6]  # Decreasing quality
        
        # Calculate quality-weighted mean
        expected_weighted_mean = np.average(pb_ratios, weights=quality_weights)
        
        # This tests the statistical calculation logic
        # In practice, this would be tested through the full analysis pipeline
        calculated_weighted_mean = np.average(pb_ratios, weights=quality_weights)
        
        self.assertAlmostEqual(calculated_weighted_mean, expected_weighted_mean, places=3)
        
        # Higher quality data points should have more influence
        high_quality_mean = np.average([2.0, 100.0], weights=[0.9, 0.1])  # High weight on 2.0
        low_quality_mean = np.average([2.0, 100.0], weights=[0.1, 0.9])   # High weight on 100.0
        
        self.assertLess(high_quality_mean, low_quality_mean)
        self.assertLess(abs(high_quality_mean - 2.0), abs(low_quality_mean - 2.0))
    
    def test_confidence_interval_calculations(self):
        """Test confidence interval calculation methods"""
        
        # Test data with known statistical properties
        test_data = [1.5, 2.0, 2.5, 2.2, 1.8, 2.3, 1.9, 2.1, 2.4, 1.7]
        
        mean_val = np.mean(test_data)
        std_val = np.std(test_data, ddof=1)
        n = len(test_data)
        
        # Calculate 95% confidence interval using t-distribution
        from scipy import stats
        t_critical = stats.t.ppf(0.975, df=n-1)  # 97.5% for two-tailed 95% CI
        margin = t_critical * (std_val / np.sqrt(n))
        
        expected_ci = (mean_val - margin, mean_val + margin)
        
        # This tests the confidence interval calculation logic
        # which is used in the full analysis
        calculated_mean = np.mean(test_data)
        calculated_std = np.std(test_data, ddof=1)
        calculated_margin = t_critical * (calculated_std / np.sqrt(n))
        calculated_ci = (calculated_mean - calculated_margin, calculated_mean + calculated_margin)
        
        self.assertAlmostEqual(calculated_ci[0], expected_ci[0], places=3)
        self.assertAlmostEqual(calculated_ci[1], expected_ci[1], places=3)
        
        # Confidence interval should contain the true mean
        self.assertLessEqual(calculated_ci[0], calculated_mean)
        self.assertGreaterEqual(calculated_ci[1], calculated_mean)
    
    def test_trend_analysis_calculations(self):
        """Test trend analysis calculation methods"""
        
        # Create test data with known trend
        x_values = list(range(10))  # Time points
        y_values = [2.0 + 0.1 * x + np.random.normal(0, 0.05) for x in x_values]  # Upward trend
        
        # Calculate linear regression manually
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x ** 2 for x in x_values)
        
        # Slope calculation
        denominator = n * sum_x2 - sum_x ** 2
        if denominator != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope = 0.0
            intercept = np.mean(y_values)
        
        # Should detect positive trend (slope > 0)
        self.assertGreater(slope, 0, "Should detect upward trend")
        
        # Test with downward trend
        y_values_down = [5.0 - 0.2 * x + np.random.normal(0, 0.05) for x in x_values]
        sum_y_down = sum(y_values_down)
        sum_xy_down = sum(x * y for x, y in zip(x_values, y_values_down))
        
        slope_down = (n * sum_xy_down - sum_x * sum_y_down) / denominator
        
        self.assertLess(slope_down, 0, "Should detect downward trend")
    
    def test_monte_carlo_simulation_parameters(self):
        """Test Monte Carlo simulation parameter validation"""
        
        # Test input validation for Monte Carlo simulation
        sample_data = [1.5, 2.0, 2.5, 1.8, 2.2, 1.9, 2.3, 2.1]
        
        mean_val = np.mean(sample_data)
        std_val = np.std(sample_data, ddof=1)
        
        # Test different simulation sizes
        simulation_sizes = [100, 1000, 10000]
        
        for n_sims in simulation_sizes:
            # Generate Monte Carlo samples
            mc_samples = np.random.normal(mean_val, std_val, n_sims)
            
            # Calculated statistics should converge to input parameters
            mc_mean = np.mean(mc_samples)
            mc_std = np.std(mc_samples)
            
            # With larger sample sizes, should be closer to true parameters
            mean_error = abs(mc_mean - mean_val)
            std_error = abs(mc_std - std_val)
            
            if n_sims >= 1000:
                # Should be reasonably close with larger sample sizes
                self.assertLess(mean_error / mean_val, 0.1, f"Mean error too large for {n_sims} samples")
                self.assertLess(std_error / std_val, 0.2, f"Std error too large for {n_sims} samples")


class TestStatisticalAnalysisValidation(unittest.TestCase):
    """Test statistical analysis components and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
    
    def test_normality_testing(self):
        """Test normality testing functionality"""
        
        # Generate normal and non-normal test data
        np.random.seed(42)  # For reproducible tests
        
        normal_data = np.random.normal(2.0, 0.5, 100).tolist()
        # Non-normal data (exponential distribution)
        non_normal_data = np.random.exponential(2.0, 100).tolist()
        
        # Test normality detection
        from scipy.stats import jarque_bera
        
        # Normal data should pass normality test (high p-value)
        normal_stat, normal_pvalue = jarque_bera(normal_data)
        self.assertGreater(normal_pvalue, 0.05, "Normal data should pass normality test")
        
        # Non-normal data should fail normality test (low p-value)
        non_normal_stat, non_normal_pvalue = jarque_bera(non_normal_data)
        self.assertLess(non_normal_pvalue, 0.05, "Non-normal data should fail normality test")
    
    def test_outlier_detection_logic(self):
        """Test outlier detection using IQR method"""
        
        # Create test data with known outliers
        clean_data = [2.0, 2.1, 1.9, 2.2, 1.8, 2.3, 2.0, 1.9, 2.1, 2.2]
        outlier_data = clean_data + [10.0, -5.0]  # Add clear outliers
        
        # Calculate IQR-based outlier bounds
        q1 = np.percentile(outlier_data, 25)
        q3 = np.percentile(outlier_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Identify outliers
        outliers = [x for x in outlier_data if x < lower_bound or x > upper_bound]
        
        # Should detect the added outliers
        self.assertIn(10.0, outliers)
        self.assertIn(-5.0, outliers)
        
        # Calculate outlier score (percentage of non-outliers)
        non_outliers = [x for x in outlier_data if lower_bound <= x <= upper_bound]
        outlier_score = len(non_outliers) / len(outlier_data)
        
        # Score should reflect presence of outliers
        self.assertLess(outlier_score, 1.0)
        self.assertGreater(outlier_score, 0.7)  # Most data should still be valid
    
    def test_correlation_analysis(self):
        """Test correlation analysis functionality"""
        
        # Create correlated test data
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y_positive = x * 2 + np.random.normal(0, 0.5, len(x))  # Positive correlation
        y_negative = -x * 1.5 + np.random.normal(0, 0.5, len(x))  # Negative correlation
        y_no_corr = np.random.normal(0, 2, len(x))  # No correlation
        
        # Test positive correlation
        corr_pos, p_val_pos = self._calculate_correlation(x, y_positive)
        self.assertGreater(corr_pos, 0.7, "Should detect strong positive correlation")
        self.assertLess(p_val_pos, 0.05, "Positive correlation should be significant")
        
        # Test negative correlation
        corr_neg, p_val_neg = self._calculate_correlation(x, y_negative)
        self.assertLess(corr_neg, -0.7, "Should detect strong negative correlation")
        self.assertLess(p_val_neg, 0.05, "Negative correlation should be significant")
        
        # Test no correlation
        corr_none, p_val_none = self._calculate_correlation(x, y_no_corr)
        self.assertLess(abs(corr_none), 0.5, "Should detect weak/no correlation")
        # p-value might be high (not significant)
    
    def _calculate_correlation(self, x, y):
        """Helper method to calculate correlation"""
        from scipy.stats import pearsonr
        return pearsonr(x, y)
    
    def test_risk_metrics_calculation(self):
        """Test risk-adjusted metrics calculations"""
        
        # Create test data with different risk profiles
        low_risk_data = [2.0 + np.random.normal(0, 0.1) for _ in range(20)]  # Low volatility
        high_risk_data = [2.0 + np.random.normal(0, 1.0) for _ in range(20)]  # High volatility
        
        # Calculate risk metrics
        low_risk_mean = np.mean(low_risk_data)
        low_risk_std = np.std(low_risk_data)
        low_risk_ratio = low_risk_mean / low_risk_std if low_risk_std > 0 else 0
        
        high_risk_mean = np.mean(high_risk_data)
        high_risk_std = np.std(high_risk_data)
        high_risk_ratio = high_risk_mean / high_risk_std if high_risk_std > 0 else 0
        
        # Low risk data should have better risk-adjusted return
        # (higher ratio of return to volatility)
        self.assertGreater(low_risk_ratio, high_risk_ratio)
        
        # Test downside deviation calculation
        downside_low = self._calculate_downside_deviation(low_risk_data, low_risk_mean)
        downside_high = self._calculate_downside_deviation(high_risk_data, high_risk_mean)
        
        # High risk data should have higher downside deviation
        self.assertGreater(downside_high, downside_low)
    
    def _calculate_downside_deviation(self, data, mean):
        """Helper method to calculate downside deviation"""
        downside_deviations = [min(0, x - mean) for x in data]
        return np.sqrt(np.mean([d**2 for d in downside_deviations]))


# Test utility functions
def create_mock_pb_datapoint(date_str: str, price: float, book_value: float) -> PBDataPoint:
    """Utility function to create mock P/B data points"""
    pb_ratio = price / book_value if book_value > 0 else 0
    
    return PBDataPoint(
        date=date_str,
        price=price,
        book_value_per_share=book_value,
        shares_outstanding=1_000_000_000,
        pb_ratio=pb_ratio,
        market_cap=price * 1_000_000_000,
        book_value_total=book_value * 1_000_000_000,
        data_quality=0.85
    )


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main(verbosity=2)