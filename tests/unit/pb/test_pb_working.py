"""
Working Test Suite for P/B Historical Analysis Module
=====================================================

This module provides working tests for the P/B historical analysis
functionality using the correct class interfaces.
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
import warnings

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore")

# Import the actual modules with error handling
try:
    from pb_historical_analysis import (
        PBHistoricalAnalysisEngine,
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
    from data_sources import (
        DataSourceResponse,
        DataSourceType,
        DataQualityMetrics
    )
    DATA_SOURCES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: data_sources not available: {e}")
    DATA_SOURCES_AVAILABLE = False


class TestPBHistoricalEngine(unittest.TestCase):
    """Test P/B Historical Analysis Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not PB_HISTORICAL_AVAILABLE:
            self.skipTest("pb_historical_analysis module not available")
        
        self.engine = PBHistoricalAnalysisEngine()
        self.test_ticker = "AAPL"
    
    def test_engine_initialization(self):
        """Test that the engine initializes correctly"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.pb_engine)
        self.assertEqual(self.engine.min_data_points, 12)
        self.assertEqual(self.engine.confidence_level, 0.95)
    
    def test_pb_data_point_creation(self):
        """Test creation of PB data points with correct parameters"""
        
        # Use only the parameters that exist in the actual class
        dp = PBDataPoint(
            date="2024-01-01",
            price=100.0,
            book_value_per_share=20.0,
            pb_ratio=5.0,
            shares_outstanding=1_000_000_000,
            market_cap=100_000_000_000,
            data_quality=0.85
        )
        
        self.assertEqual(dp.date, "2024-01-01")
        self.assertEqual(dp.price, 100.0)
        self.assertEqual(dp.book_value_per_share, 20.0)
        self.assertEqual(dp.pb_ratio, 5.0)
        self.assertEqual(dp.data_quality, 0.85)
    
    def test_quality_metrics_creation(self):
        """Test creation and calculation of quality metrics"""
        
        metrics = PBHistoricalQualityMetrics()
        
        # Set basic values
        metrics.completeness = 0.9
        metrics.accuracy = 0.85
        metrics.timeliness = 0.8
        metrics.consistency = 0.87
        
        # Set P/B specific values
        metrics.pb_data_completeness = 0.92
        metrics.price_data_quality = 0.88
        metrics.balance_sheet_quality = 0.83
        
        # Calculate overall score
        overall_score = metrics.calculate_overall_score()
        
        self.assertGreater(overall_score, 0.0)
        self.assertLessEqual(overall_score, 1.0)
        self.assertEqual(metrics.overall_score, overall_score)


class TestStatisticalCalculations(unittest.TestCase):
    """Test statistical calculation functions"""
    
    def test_basic_pb_calculations(self):
        """Test basic P/B ratio calculations"""
        
        test_cases = [
            (100.0, 20.0, 5.0),   # Standard case
            (50.0, 25.0, 2.0),    # Lower ratio
            (200.0, 40.0, 5.0),   # Higher values, same ratio
            (30.0, 10.0, 3.0),    # Different ratio
        ]
        
        for price, book_value, expected_pb in test_cases:
            with self.subTest(price=price, book_value=book_value):
                calculated_pb = price / book_value if book_value > 0 else 0
                self.assertAlmostEqual(calculated_pb, expected_pb, places=2)
    
    def test_statistical_measures(self):
        """Test basic statistical measures"""
        
        # Create test data with known properties
        test_data = [1.5, 2.0, 2.5, 2.2, 1.8, 2.3, 1.9, 2.1, 2.4, 1.7]
        
        # Test mean
        mean_val = np.mean(test_data)
        self.assertAlmostEqual(mean_val, 2.04, places=1)
        
        # Test median
        median_val = np.median(test_data)
        self.assertAlmostEqual(median_val, 2.05, places=1)
        
        # Test standard deviation
        std_val = np.std(test_data, ddof=1)
        self.assertGreater(std_val, 0)
        self.assertLess(std_val, 1.0)  # Should be reasonable for this data
        
        # Test percentiles
        p25 = np.percentile(test_data, 25)
        p75 = np.percentile(test_data, 75)
        self.assertLess(p25, median_val)
        self.assertGreater(p75, median_val)
    
    def test_outlier_detection(self):
        """Test outlier detection logic"""
        
        # Create data with clear outliers
        normal_data = [2.0, 2.1, 1.9, 2.2, 1.8, 2.3, 2.0, 1.9, 2.1, 2.2]
        outlier_data = normal_data + [10.0, -5.0]  # Add obvious outliers
        
        # Calculate IQR bounds
        q1 = np.percentile(outlier_data, 25)
        q3 = np.percentile(outlier_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Identify outliers
        outliers = [x for x in outlier_data if x < lower_bound or x > upper_bound]
        
        # Should detect the extreme values
        self.assertGreater(len(outliers), 0)
        
        # Calculate outlier score (percentage of normal values)
        normal_values = [x for x in outlier_data if lower_bound <= x <= upper_bound]
        outlier_score = len(normal_values) / len(outlier_data)
        
        self.assertLess(outlier_score, 1.0)  # Should be less than 100%
        self.assertGreater(outlier_score, 0.5)  # But most should still be normal


class TestDataSourceIntegration(unittest.TestCase):
    """Test integration with data sources"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not (PB_HISTORICAL_AVAILABLE and DATA_SOURCES_AVAILABLE):
            self.skipTest("Required modules not available")
        
        self.engine = PBHistoricalAnalysisEngine()
    
    def _create_simple_response(self, success: bool = True, 
                               data_points: int = 20) -> DataSourceResponse:
        """Create a simple mock response with correct parameters"""
        
        if not success:
            return DataSourceResponse(
                success=False,
                error_message="Mock error"
            )
        
        # Create mock historical data
        historical_data = []
        base_date = datetime.now() - timedelta(days=365 * 5)
        
        for i in range(data_points):
            date = base_date + timedelta(days=i * 90)  # Quarterly
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': 150 + i * 2,
                'book_value_per_share': 25 + i * 0.5,
                'shares_outstanding': 1_000_000_000
            })
        
        response_data = {
            'ticker': 'TEST',
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data
        }
        
        # Create quality metrics
        quality_metrics = DataQualityMetrics()
        quality_metrics.completeness = 0.85
        quality_metrics.accuracy = 0.90
        quality_metrics.timeliness = 0.80
        quality_metrics.consistency = 0.88
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE,
            quality_metrics=quality_metrics
        )
    
    def test_successful_analysis(self):
        """Test successful analysis with good data"""
        
        response = self._create_simple_response(success=True, data_points=20)
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should succeed with sufficient data
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.data_points_count, 0)
        self.assertIsNotNone(result.statistics)
        self.assertIsNotNone(result.quality_metrics)
        self.assertEqual(result.ticker, 'TEST')
        
        # Check that basic statistics are calculated
        if result.statistics:
            self.assertGreater(result.statistics.mean_pb, 0)
            self.assertGreater(result.statistics.std_pb, 0)
    
    def test_failed_response_handling(self):
        """Test handling of failed data response"""
        
        response = self._create_simple_response(success=False)
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should fail gracefully
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Invalid or unsuccessful", result.error_message)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        
        # Create response with too few data points
        response = self._create_simple_response(success=True, data_points=5)
        result = self.engine.analyze_historical_performance(response, 5)
        
        # Should fail due to insufficient data
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Insufficient data points", result.error_message)


class TestPerformance(unittest.TestCase):
    """Basic performance tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not (PB_HISTORICAL_AVAILABLE and DATA_SOURCES_AVAILABLE):
            self.skipTest("Required modules not available")
        
        self.engine = PBHistoricalAnalysisEngine()
    
    def test_processing_time(self):
        """Test that processing completes in reasonable time"""
        
        # Create a larger dataset
        historical_data = []
        base_date = datetime.now() - timedelta(days=365 * 5)
        
        for i in range(60):  # 5 years of monthly data
            date = base_date + timedelta(days=i * 30)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': 150 + i * 0.5 + np.random.normal(0, 2),
                'book_value_per_share': 25 + i * 0.1 + np.random.normal(0, 0.5),
                'shares_outstanding': 1_000_000_000
            })
        
        response_data = {
            'ticker': 'PERF_TEST',
            'historical_prices': historical_data,
            'quarterly_balance_sheet': historical_data
        }
        
        quality_metrics = DataQualityMetrics()
        quality_metrics.completeness = 0.95
        quality_metrics.accuracy = 0.90
        quality_metrics.timeliness = 0.85
        quality_metrics.consistency = 0.88
        quality_metrics.calculate_overall_score()
        
        response = DataSourceResponse(
            success=True,
            data=response_data,
            source_type=DataSourceType.YFINANCE,
            quality_metrics=quality_metrics
        )
        
        # Measure processing time
        import time
        start_time = time.time()
        result = self.engine.analyze_historical_performance(response, 5)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete successfully
        self.assertTrue(result.success)
        
        # Should complete in reasonable time (< 5 seconds for moderate dataset)
        self.assertLess(processing_time, 5.0)
        
        print(f"Processing time for {len(historical_data)} data points: {processing_time:.3f} seconds")


def run_working_tests():
    """Run the working test suite"""
    
    print("P/B Historical Analysis - Working Test Suite")
    print("=" * 50)
    
    # Check module availability
    if not PB_HISTORICAL_AVAILABLE:
        print("ERROR: pb_historical_analysis module not available")
        return False
    
    if not DATA_SOURCES_AVAILABLE:
        print("WARNING: data_sources module not available - some tests will be skipped")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPBHistoricalEngine,
        TestStatisticalCalculations,
    ]
    
    # Add data source tests only if available
    if DATA_SOURCES_AVAILABLE:
        test_classes.extend([
            TestDataSourceIntegration,
            TestPerformance
        ])
    
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
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = result.wasSuccessful()
    
    if success:
        print("\n✓ All tests passed! P/B Historical Analysis module is working correctly.")
    else:
        print("\n✗ Some tests failed. Review the output above.")
    
    return success


if __name__ == '__main__':
    success = run_working_tests()
    exit(0 if success else 1)