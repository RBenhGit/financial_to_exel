"""
Simple Test Suite for P/B Historical Analysis Module
====================================================

This module provides simple, focused tests for the P/B historical analysis
functionality that can run without complex dependencies.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import warnings

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore")

# Import the actual modules
try:
    from core.analysis.pb.pb_historical_analysis import (
        PBHistoricalAnalysisEngine,
        PBHistoricalAnalysisResult,
        PBHistoricalQualityMetrics,
        PBStatisticalSummary,
        PBTrendAnalysis,
        PBDataPoint
    )
    PB_HISTORICAL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: pb_historical_analysis not available: {e}")
    PB_HISTORICAL_AVAILABLE = False

try:
    from core.data_sources.data_sources import (
        DataSourceResponse,
        DataSourceType,
        DataQualityMetrics
    )
    DATA_SOURCES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: data_sources not available: {e}")
    DATA_SOURCES_AVAILABLE = False


class TestPBHistoricalBasics(unittest.TestCase):
    """Basic tests for P/B historical analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not PB_HISTORICAL_AVAILABLE:
            self.skipTest("pb_historical_analysis module not available")
        
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "TEST"
    
    def test_engine_initialization(self):
        """Test that the P/B historical analysis engine initializes properly"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.pb_engine)
        self.assertEqual(self.engine.min_data_points, 12)
        self.assertEqual(self.engine.confidence_level, 0.95)
    
    def test_pb_data_point_creation(self):
        """Test creation of P/B data points"""
        
        # Create a test data point
        dp = PBDataPoint(
            date="2024-01-01",
            price=100.0,
            book_value_per_share=20.0,
            shares_outstanding=1_000_000_000,
            pb_ratio=5.0,
            market_cap=100_000_000_000,
            book_value_total=20_000_000_000,
            data_quality=0.85
        )
        
        self.assertEqual(dp.date, "2024-01-01")
        self.assertEqual(dp.price, 100.0)
        self.assertEqual(dp.book_value_per_share, 20.0)
        self.assertEqual(dp.pb_ratio, 5.0)
        self.assertEqual(dp.data_quality, 0.85)
    
    def test_quality_metrics_calculation(self):
        """Test P/B quality metrics calculation"""
        
        metrics = PBHistoricalQualityMetrics()
        
        # Set some test values
        metrics.completeness = 0.9
        metrics.accuracy = 0.85
        metrics.timeliness = 0.8
        metrics.consistency = 0.87
        metrics.pb_data_completeness = 0.92
        metrics.price_data_quality = 0.88
        metrics.balance_sheet_quality = 0.83
        
        # Calculate overall score
        overall_score = metrics.calculate_overall_score()
        
        self.assertGreater(overall_score, 0.0)
        self.assertLessEqual(overall_score, 1.0)
        self.assertEqual(metrics.overall_score, overall_score)
    
    def test_statistical_summary_initialization(self):
        """Test statistical summary initialization"""
        
        summary = PBStatisticalSummary()
        
        # Check default values
        self.assertEqual(summary.mean_pb, 0.0)
        self.assertEqual(summary.median_pb, 0.0)
        self.assertEqual(summary.std_pb, 0.0)
        self.assertEqual(summary.min_pb, 0.0)
        self.assertEqual(summary.max_pb, 0.0)
        
        # Check that lists are initialized
        self.assertIsInstance(summary.rolling_mean_12m, list)
        self.assertIsInstance(summary.rolling_median_12m, list)
        self.assertIsInstance(summary.rolling_std_12m, list)
    
    def test_trend_analysis_initialization(self):
        """Test trend analysis initialization"""
        
        trend = PBTrendAnalysis()
        
        # Check default values
        self.assertEqual(trend.trend_direction, "neutral")
        self.assertEqual(trend.trend_strength, 0.0)
        self.assertEqual(trend.trend_slope, 0.0)
        self.assertEqual(trend.r_squared, 0.0)
        self.assertEqual(trend.volatility, 0.0)
        self.assertEqual(trend.cycles_detected, 0)
        self.assertEqual(trend.current_cycle_position, "unknown")


class TestBasicCalculations(unittest.TestCase):
    """Test basic calculation functions"""
    
    def test_pb_ratio_calculation(self):
        """Test basic P/B ratio calculation"""
        
        test_cases = [
            (100.0, 20.0, 5.0),
            (50.0, 25.0, 2.0),
            (75.0, 15.0, 5.0),
            (200.0, 40.0, 5.0),
            (30.0, 10.0, 3.0),
        ]
        
        for price, book_value, expected_pb in test_cases:
            with self.subTest(price=price, book_value=book_value):
                calculated_pb = price / book_value if book_value > 0 else 0
                self.assertAlmostEqual(calculated_pb, expected_pb, places=2)
    
    def test_statistical_calculations(self):
        """Test basic statistical calculations"""
        
        test_data = [1.5, 2.0, 2.5, 2.2, 1.8, 2.3, 1.9, 2.1, 2.4, 1.7]
        
        # Test mean calculation
        mean_val = np.mean(test_data)
        self.assertAlmostEqual(mean_val, 2.04, places=2)
        
        # Test median calculation
        median_val = np.median(test_data)
        self.assertAlmostEqual(median_val, 2.05, places=2)
        
        # Test standard deviation
        std_val = np.std(test_data, ddof=1)
        self.assertGreater(std_val, 0)
        
        # Test percentiles
        p25 = np.percentile(test_data, 25)
        p75 = np.percentile(test_data, 75)
        self.assertLess(p25, median_val)
        self.assertGreater(p75, median_val)
    
    def test_outlier_detection_logic(self):
        """Test outlier detection using IQR method"""
        
        # Normal data
        clean_data = [2.0, 2.1, 1.9, 2.2, 1.8, 2.3, 2.0, 1.9, 2.1, 2.2]
        
        # Data with outliers
        outlier_data = clean_data + [10.0, -5.0]
        
        # Calculate IQR
        q1 = np.percentile(outlier_data, 25)
        q3 = np.percentile(outlier_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Count outliers
        outliers = [x for x in outlier_data if x < lower_bound or x > upper_bound]
        
        # Should detect the added outliers
        self.assertGreater(len(outliers), 0)
        self.assertIn(10.0, outliers)
        self.assertIn(-5.0, outliers)


class TestDataResponseHandling(unittest.TestCase):
    """Test data response handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not DATA_SOURCES_AVAILABLE or not PB_HISTORICAL_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.engine = PBHistoricalAnalysisEngine()
    
    def _create_mock_response(self, success: bool = True, 
                            data_points: int = 20) -> DataSourceResponse:
        """Create a mock data source response"""
        
        if not success:
            return DataSourceResponse(
                success=False,
                data=None,
                source_type=DataSourceType.YFINANCE,
                request_timestamp=datetime.now(),
                error_message="Mock error"
            )
        
        # Generate mock historical data
        historical_data = []
        base_date = datetime.now() - timedelta(days=365 * 5)
        
        for i in range(data_points):
            date = base_date + timedelta(days=i * 90)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': 150 + i * 2 + np.random.normal(0, 5),
                'book_value_per_share': 25 + i * 0.5 + np.random.normal(0, 1),
                'shares_outstanding': 1_000_000_000
            })
        
        response_data = {
            'ticker': 'TEST',
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data
        }
        
        quality_metrics = DataQualityMetrics(
            completeness=0.85,
            accuracy=0.90,
            timeliness=0.80,
            consistency=0.88
        )
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now(),
            quality_metrics=quality_metrics
        )
    
    def test_successful_data_response(self):
        """Test handling of successful data response"""
        
        response = self._create_mock_response(success=True, data_points=20)
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should succeed with sufficient data
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.data_points_count, 0)
        self.assertIsNotNone(result.statistics)
        self.assertIsNotNone(result.quality_metrics)
    
    def test_failed_data_response(self):
        """Test handling of failed data response"""
        
        response = self._create_mock_response(success=False)
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should fail gracefully
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
    
    def test_insufficient_data_response(self):
        """Test handling of response with insufficient data"""
        
        response = self._create_mock_response(success=True, data_points=5)  # Too few points
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should fail due to insufficient data
        self.assertFalse(result.success)
        self.assertIn("Insufficient data points", result.error_message)


class TestPerformanceBasics(unittest.TestCase):
    """Basic performance tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not DATA_SOURCES_AVAILABLE or not PB_HISTORICAL_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.engine = PBHistoricalAnalysisEngine()
    
    def test_reasonable_processing_time(self):
        """Test that processing time is reasonable for typical datasets"""
        
        # Create a response with moderate amount of data
        historical_data = []
        base_date = datetime.now() - timedelta(days=365 * 5)
        
        for i in range(60):  # 5 years of quarterly data
            date = base_date + timedelta(days=i * 30)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': 150 + i * 0.5,
                'book_value_per_share': 25 + i * 0.1,
                'shares_outstanding': 1_000_000_000
            })
        
        response_data = {
            'ticker': 'PERF_TEST',
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data
        }
        
        quality_metrics = DataQualityMetrics(
            completeness=0.95,
            accuracy=0.90,
            timeliness=0.85,
            consistency=0.88
        )
        quality_metrics.calculate_overall_score()
        
        response = DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE,
            request_timestamp=datetime.now(),
            quality_metrics=quality_metrics
        )
        
        # Measure processing time
        import time
        start_time = time.time()
        result = self.engine.analyze_historical_performance(response, 5)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (< 10 seconds for moderate dataset)
        self.assertLess(processing_time, 10.0)
        self.assertTrue(result.success)
        
        print(f"Processing time for {len(historical_data)} data points: {processing_time:.2f} seconds")


def run_simple_tests():
    """Run the simple test suite"""
    
    print("Running Simple P/B Historical Analysis Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPBHistoricalBasics,
        TestBasicCalculations,
        TestDataResponseHandling,
        TestPerformanceBasics
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0] if 'AssertionError:' in traceback else 'Unknown failure'}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error: ')[-1].split('\n')[0] if 'Error:' in traceback else 'Unknown error'}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_simple_tests()
    exit(0 if success else 1)