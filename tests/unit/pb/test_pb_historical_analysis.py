"""
Test Suite for P/B Historical Analysis Engine
===========================================

Comprehensive tests for the P/B Historical Performance Analysis Engine
with DataQualityMetrics integration.

Test Categories:
- Unit tests for individual components
- Integration tests with DataSourceResponse objects
- Quality metrics validation tests
- Statistical analysis accuracy tests
- Edge case and error handling tests
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import logging

# Import modules to test
from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    PBHistoricalQualityMetrics,
    PBHistoricalAnalysisResult,
    PBStatisticalSummary,
    PBTrendAnalysis,
    create_pb_historical_report,
    validate_pb_historical_data
)

from core.data_sources.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics, FinancialDataRequest
from pb_calculation_engine import PBDataPoint

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestPBHistoricalQualityMetrics(unittest.TestCase):
    """Test P/B-specific quality metrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.quality_metrics = PBHistoricalQualityMetrics()
    
    def test_initialization(self):
        """Test quality metrics initialization"""
        self.assertEqual(self.quality_metrics.pb_data_completeness, 0.0)
        self.assertEqual(self.quality_metrics.price_data_quality, 0.0)
        self.assertEqual(self.quality_metrics.balance_sheet_quality, 0.0)
        self.assertEqual(self.quality_metrics.confidence_level, 0.95)
    
    def test_calculate_overall_score(self):
        """Test overall score calculation with P/B-specific weights"""
        # Set up test metrics
        self.quality_metrics.completeness = 0.8
        self.quality_metrics.accuracy = 0.9
        self.quality_metrics.timeliness = 0.7
        self.quality_metrics.consistency = 0.8
        self.quality_metrics.pb_data_completeness = 0.85
        self.quality_metrics.price_data_quality = 0.9
        self.quality_metrics.balance_sheet_quality = 0.8
        self.quality_metrics.data_gap_penalty = 0.1
        
        score = self.quality_metrics.calculate_overall_score()
        
        # Verify score is calculated and within bounds
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(score, self.quality_metrics.overall_score)
        
        # Verify penalty is applied
        self.assertLess(score, 0.9)  # Should be reduced by gap penalty
    
    def test_score_bounds(self):
        """Test that scores remain within bounds"""
        # Test with extreme values
        self.quality_metrics.completeness = 1.5  # Over limit
        self.quality_metrics.accuracy = -0.1     # Under limit
        
        score = self.quality_metrics.calculate_overall_score()
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestPBHistoricalAnalysisEngine(unittest.TestCase):
    """Test the main P/B Historical Analysis Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
        self.sample_pb_data = self._create_sample_pb_data()
        self.sample_response = self._create_sample_response()
    
    def _create_sample_pb_data(self) -> list:
        """Create sample P/B data points for testing"""
        base_date = datetime.now() - timedelta(days=365*5)  # 5 years ago
        data_points = []
        
        for i in range(20):  # 20 quarterly data points (5 years)
            date = base_date + timedelta(days=i*90)  # Quarterly intervals
            pb_ratio = 2.0 + 0.5 * np.sin(i * 0.3) + np.random.normal(0, 0.1)  # Cyclical with noise
            
            data_points.append(PBDataPoint(
                date=date.strftime('%Y-%m-%d'),
                price=pb_ratio * 20.0,  # Assume $20 book value
                book_value_per_share=20.0,
                pb_ratio=pb_ratio,
                shares_outstanding=1000000,
                market_cap=pb_ratio * 20.0 * 1000000,
                source_type=DataSourceType.ALPHA_VANTAGE,
                data_quality=0.85
            ))
        
        return data_points
    
    def _create_sample_response(self) -> DataSourceResponse:
        """Create sample DataSourceResponse for testing"""
        # Create mock historical data
        historical_data = {
            'ticker': 'TEST',
            'historical_prices': {
                '2019-01-01': {'4. close': 40.0},
                '2019-04-01': {'4. close': 42.0},
                '2019-07-01': {'4. close': 38.0},
                '2019-10-01': {'4. close': 45.0},
                '2020-01-01': {'4. close': 41.0},
                # Add more test data...
            },
            'quarterly_balance_sheet': [
                {
                    'fiscalDateEnding': '2019-12-31',
                    'totalStockholderEquity': 20000000,
                    'commonSharesOutstanding': 1000000
                },
                {
                    'fiscalDateEnding': '2020-12-31',
                    'totalStockholderEquity': 21000000,
                    'commonSharesOutstanding': 1000000
                },
                # Add more test data...
            ]
        }
        
        quality_metrics = DataQualityMetrics(
            completeness=0.85,
            accuracy=0.90,
            timeliness=0.75,
            consistency=0.80
        )
        quality_metrics.calculate_overall_score()
        
        return DataSourceResponse(
            success=True,
            data=historical_data,
            source_type=DataSourceType.ALPHA_VANTAGE,
            quality_metrics=quality_metrics
        )
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine.pb_engine)
        self.assertEqual(self.engine.min_data_points, 12)
        self.assertEqual(self.engine.confidence_level, 0.95)
    
    def test_analyze_historical_performance_success(self):
        """Test successful historical performance analysis"""
        # Mock the calculate_historical_pb method to return our sample data
        with patch.object(self.engine.pb_engine, 'calculate_historical_pb', return_value=self.sample_pb_data):
            result = self.engine.analyze_historical_performance(self.sample_response, years=5)
        
        # Verify successful analysis
        self.assertTrue(result.success)
        self.assertEqual(result.ticker, 'TEST')
        self.assertEqual(result.data_points_count, 20)
        self.assertIsNotNone(result.quality_metrics)
        self.assertIsNotNone(result.statistics)
        self.assertIsNotNone(result.trend_analysis)
    
    def test_analyze_historical_performance_insufficient_data(self):
        """Test analysis with insufficient data points"""
        # Create minimal data
        minimal_data = self.sample_pb_data[:5]  # Only 5 data points
        
        with patch.object(self.engine.pb_engine, 'calculate_historical_pb', return_value=minimal_data):
            result = self.engine.analyze_historical_performance(self.sample_response, years=5)
        
        # Should fail due to insufficient data
        self.assertFalse(result.success)
        self.assertIn("Insufficient data points", result.error_message)
    
    def test_analyze_historical_performance_invalid_response(self):
        """Test analysis with invalid response"""
        invalid_response = DataSourceResponse(success=False, error_message="API Error")
        
        result = self.engine.analyze_historical_performance(invalid_response, years=5)
        
        self.assertFalse(result.success)
        self.assertIn("Invalid or unsuccessful", result.error_message)
    
    def test_calculate_pb_quality_metrics(self):
        """Test P/B-specific quality metrics calculation"""
        quality_metrics = self.engine._calculate_pb_quality_metrics(self.sample_pb_data, self.sample_response)
        
        # Verify quality metrics are calculated
        self.assertIsInstance(quality_metrics, PBHistoricalQualityMetrics)
        self.assertGreater(quality_metrics.pb_data_completeness, 0.8)  # Should be high for good data
        self.assertGreater(quality_metrics.price_data_quality, 0.8)
        self.assertGreater(quality_metrics.balance_sheet_quality, 0.8)
        self.assertGreater(quality_metrics.overall_score, 0.0)
    
    def test_calculate_statistical_summary(self):
        """Test statistical summary calculation"""
        quality_metrics = PBHistoricalQualityMetrics()
        quality_metrics.overall_score = 0.85
        
        summary = self.engine._calculate_statistical_summary(self.sample_pb_data, quality_metrics)
        
        # Verify statistical calculations
        self.assertIsInstance(summary, PBStatisticalSummary)
        self.assertGreater(summary.mean_pb, 0)
        self.assertGreater(summary.median_pb, 0)
        self.assertGreater(summary.std_pb, 0)
        self.assertGreater(summary.p25_pb, 0)
        self.assertGreater(summary.p75_pb, 0)
        
        # Verify percentile ordering
        self.assertLessEqual(summary.p25_pb, summary.median_pb)
        self.assertLessEqual(summary.median_pb, summary.p75_pb)
        self.assertLessEqual(summary.p75_pb, summary.p90_pb)
    
    def test_analyze_trends(self):
        """Test trend analysis"""
        trend_analysis = self.engine._analyze_trends(self.sample_pb_data)
        
        # Verify trend analysis results
        self.assertIsInstance(trend_analysis, PBTrendAnalysis)
        self.assertIn(trend_analysis.trend_direction, ['upward', 'downward', 'neutral'])
        self.assertGreaterEqual(trend_analysis.trend_strength, 0.0)
        self.assertLessEqual(trend_analysis.trend_strength, 1.0)
        self.assertGreaterEqual(trend_analysis.volatility, 0.0)
        self.assertGreaterEqual(trend_analysis.mean_reversion_score, 0.0)
        self.assertLessEqual(trend_analysis.mean_reversion_score, 1.0)
    
    def test_assess_temporal_consistency(self):
        """Test temporal consistency assessment"""
        consistency_score = self.engine._assess_temporal_consistency(self.sample_pb_data)
        
        self.assertGreaterEqual(consistency_score, 0.0)
        self.assertLessEqual(consistency_score, 1.0)
        # Should be high for our regularly spaced quarterly data
        self.assertGreater(consistency_score, 0.7)
    
    def test_calculate_outlier_score(self):
        """Test outlier detection scoring"""
        outlier_score = self.engine._calculate_outlier_score(self.sample_pb_data)
        
        self.assertGreaterEqual(outlier_score, 0.0)
        self.assertLessEqual(outlier_score, 1.0)
        # Should be high for our reasonable test data
        self.assertGreater(outlier_score, 0.8)
    
    def test_calculate_data_gap_penalty(self):
        """Test data gap penalty calculation"""
        gap_penalty = self.engine._calculate_data_gap_penalty(self.sample_pb_data)
        
        self.assertGreaterEqual(gap_penalty, 0.0)
        self.assertLessEqual(gap_penalty, 0.5)  # Max penalty should be reasonable
        # Should be low for our complete quarterly data
        self.assertLess(gap_penalty, 0.1)
    
    def test_rolling_statistics(self):
        """Test rolling statistics calculation"""
        rolling_mean = self.engine._calculate_rolling_stats(self.sample_pb_data, 'mean', 4)
        rolling_std = self.engine._calculate_rolling_stats(self.sample_pb_data, 'std', 4)
        
        # Should have values for a 4-period window
        expected_length = len(self.sample_pb_data) - 3  # 4-period window
        self.assertEqual(len(rolling_mean), expected_length)
        self.assertEqual(len(rolling_std), expected_length)
        
        # All values should be positive
        self.assertTrue(all(val > 0 for val in rolling_mean))
        self.assertTrue(all(val >= 0 for val in rolling_std))
    
    def test_autocorrelation_calculation(self):
        """Test autocorrelation calculation"""
        pb_ratios = [dp.pb_ratio for dp in self.sample_pb_data if dp.pb_ratio]
        autocorr = self.engine._calculate_autocorrelation(pb_ratios, 1)
        
        self.assertGreaterEqual(autocorr, -1.0)
        self.assertLessEqual(autocorr, 1.0)
    
    def test_cycle_detection(self):
        """Test cycle detection in P/B data"""
        pb_ratios = [dp.pb_ratio for dp in self.sample_pb_data if dp.pb_ratio]
        cycles_info = self.engine._detect_cycles(pb_ratios)
        
        self.assertIn('cycle_count', cycles_info)
        self.assertIn('avg_duration', cycles_info)
        self.assertIn('current_position', cycles_info)
        
        self.assertGreaterEqual(cycles_info['cycle_count'], 0)
        self.assertGreaterEqual(cycles_info['avg_duration'], 0.0)
        self.assertIn(cycles_info['current_position'], 
                     ['peak', 'trough', 'rising', 'falling', 'neutral', 'unknown'])
    
    def test_valuation_insights(self):
        """Test valuation insight calculations"""
        # Create a complete analysis result
        result = PBHistoricalAnalysisResult(success=True, ticker='TEST')
        result.historical_data = self.sample_pb_data
        
        # Create statistics
        quality_metrics = PBHistoricalQualityMetrics()
        quality_metrics.overall_score = 0.85
        result.quality_metrics = quality_metrics
        
        statistics = PBStatisticalSummary()
        statistics.mean_pb = 2.0
        statistics.quality_weighted_mean = 2.1
        result.statistics = statistics
        
        # Calculate insights
        self.engine._calculate_valuation_insights(result)
        
        # Verify insights are calculated
        self.assertGreaterEqual(result.current_pb_percentile, 0.0)
        self.assertLessEqual(result.current_pb_percentile, 1.0)
        self.assertIsNotNone(result.fair_value_estimate)
        self.assertIn(result.valuation_signal, 
                     ['undervalued', 'overvalued', 'fairly_valued', 'neutral', 'uncertain'])
    
    def test_generate_analysis_notes(self):
        """Test analysis notes generation"""
        # Create a result with various conditions that should trigger notes
        result = PBHistoricalAnalysisResult(success=True, ticker='TEST')
        result.data_points_count = 15
        
        # Low quality metrics to trigger warnings
        quality_metrics = PBHistoricalQualityMetrics()
        quality_metrics.overall_score = 0.5
        quality_metrics.pb_data_completeness = 0.7
        quality_metrics.temporal_consistency = 0.6
        quality_metrics.outlier_detection_score = 0.7
        quality_metrics.data_gap_penalty = 0.3
        result.quality_metrics = quality_metrics
        
        # Statistics that should trigger notes
        statistics = PBStatisticalSummary()
        statistics.mean_pb = 2.0
        statistics.std_pb = 3.0  # High volatility
        statistics.max_pb = 25.0  # Extreme value
        result.statistics = statistics
        
        # Trend analysis
        trend = PBTrendAnalysis()
        trend.trend_strength = 0.8
        trend.trend_direction = 'upward'
        trend.mean_reversion_score = 0.9
        trend.cycles_detected = 3
        result.trend_analysis = trend
        
        # Generate notes
        self.engine._generate_analysis_notes(result)
        
        # Verify notes are generated
        self.assertGreater(len(result.quality_warnings), 0)
        self.assertGreater(len(result.analysis_notes), 0)
        
        # Check for specific expected warnings/notes
        warning_text = ' '.join(result.quality_warnings)
        self.assertIn('quality', warning_text.lower())
        
        notes_text = ' '.join(result.analysis_notes)
        self.assertIn('volatility', notes_text.lower())


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_pb_historical_report(self):
        """Test report creation from analysis results"""
        # Create sample analysis result
        result = PBHistoricalAnalysisResult(
            success=True,
            ticker='TEST',
            analysis_period='5 years',
            data_points_count=20
        )
        
        # Add required components
        result.quality_metrics = PBHistoricalQualityMetrics()
        result.quality_metrics.overall_score = 0.85
        result.quality_metrics.pb_data_completeness = 0.9
        
        result.statistics = PBStatisticalSummary()
        result.statistics.mean_pb = 2.0
        result.statistics.median_pb = 1.9
        result.statistics.std_pb = 0.5
        result.statistics.p25_pb = 1.7
        result.statistics.p75_pb = 2.3
        
        result.trend_analysis = PBTrendAnalysis()
        result.trend_analysis.trend_direction = 'upward'
        result.trend_analysis.trend_strength = 0.6
        
        result.current_pb_percentile = 0.65
        result.fair_value_estimate = 2.1
        result.valuation_signal = 'fairly_valued'
        result.quality_warnings = ['Test warning']
        result.analysis_notes = ['Test note']
        
        # Create report
        report = create_pb_historical_report(result)
        
        # Verify report structure
        self.assertTrue(report['success'])
        self.assertEqual(report['ticker'], 'TEST')
        self.assertIn('summary', report)
        self.assertIn('quality_assessment', report)
        self.assertIn('statistics', report)
        self.assertIn('trend_analysis', report)
        self.assertIn('notes', report)
        
        # Verify content
        self.assertEqual(report['summary']['valuation_signal'], 'fairly_valued')
        self.assertEqual(report['statistics']['mean_pb'], 2.0)
        self.assertEqual(report['trend_analysis']['direction'], 'upward')
    
    def test_create_pb_historical_report_failure(self):
        """Test report creation for failed analysis"""
        result = PBHistoricalAnalysisResult(
            success=False,
            ticker='TEST',
            error_message='Test error'
        )
        
        report = create_pb_historical_report(result)
        
        self.assertFalse(report['success'])
        self.assertEqual(report['error'], 'Test error')
        self.assertEqual(report['ticker'], 'TEST')
    
    def test_validate_pb_historical_data(self):
        """Test data validation function"""
        # Valid response
        valid_response = DataSourceResponse(
            success=True,
            data={
                'historical_prices': {'2020-01-01': {'close': 100}},
                'quarterly_balance_sheet': [{'equity': 1000000}]
            },
            quality_metrics=DataQualityMetrics(completeness=0.8, accuracy=0.9, timeliness=0.7, consistency=0.8)
        )
        valid_response.quality_metrics.calculate_overall_score()
        
        validation = validate_pb_historical_data(valid_response)
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['issues']), 0)
        
        # Invalid response
        invalid_response = DataSourceResponse(success=False, error_message='API Error')
        
        validation = validate_pb_historical_data(invalid_response)
        self.assertFalse(validation['valid'])
        self.assertGreater(len(validation['issues']), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PBHistoricalAnalysisEngine()
    
    def test_empty_pb_data(self):
        """Test handling of empty P/B data"""
        empty_data = []
        
        quality_metrics = self.engine._calculate_pb_quality_metrics(empty_data, Mock())
        self.assertEqual(quality_metrics.pb_data_completeness, 0.0)
        
        summary = self.engine._calculate_statistical_summary(empty_data, quality_metrics)
        self.assertEqual(summary.mean_pb, 0.0)
        
        trend = self.engine._analyze_trends(empty_data)
        self.assertEqual(trend.trend_direction, "neutral")
    
    def test_single_data_point(self):
        """Test handling of single data point"""
        single_point = [PBDataPoint(
            date='2020-01-01',
            pb_ratio=2.0,
            price=40.0,
            book_value_per_share=20.0
        )]
        
        # Should handle gracefully without errors
        quality_metrics = self.engine._calculate_pb_quality_metrics(single_point, Mock())
        self.assertGreaterEqual(quality_metrics.overall_score, 0.0)
        
        summary = self.engine._calculate_statistical_summary(single_point, quality_metrics)
        self.assertEqual(summary.mean_pb, 2.0)
        self.assertEqual(summary.std_pb, 0.0)  # No variation with single point
    
    def test_invalid_pb_ratios(self):
        """Test handling of invalid P/B ratios"""
        invalid_data = [
            PBDataPoint(date='2020-01-01', pb_ratio=None),  # None value
            PBDataPoint(date='2020-04-01', pb_ratio=-1.0),  # Negative value
            PBDataPoint(date='2020-07-01', pb_ratio=0.0),   # Zero value
            PBDataPoint(date='2020-10-01', pb_ratio=2.0),   # Valid value
        ]
        
        # Should filter out invalid values
        quality_metrics = self.engine._calculate_pb_quality_metrics(invalid_data, Mock())
        self.assertLess(quality_metrics.pb_data_completeness, 1.0)  # Should detect incomplete data
        
        summary = self.engine._calculate_statistical_summary(invalid_data, quality_metrics)
        self.assertEqual(summary.mean_pb, 2.0)  # Should only use valid value
    
    def test_extreme_pb_values(self):
        """Test handling of extreme P/B values"""
        extreme_data = [
            PBDataPoint(date='2020-01-01', pb_ratio=0.01),   # Very low
            PBDataPoint(date='2020-04-01', pb_ratio=100.0),  # Very high
            PBDataPoint(date='2020-07-01', pb_ratio=2.0),    # Normal
        ]
        
        # Should handle without crashing
        quality_metrics = self.engine._calculate_pb_quality_metrics(extreme_data, Mock())
        outlier_score = self.engine._calculate_outlier_score(extreme_data)
        
        # Should detect outliers
        self.assertLess(outlier_score, 1.0)
    
    def test_missing_dates(self):
        """Test handling of missing or invalid dates"""
        data_missing_dates = [
            PBDataPoint(date='', pb_ratio=2.0),           # Empty date
            PBDataPoint(date='invalid-date', pb_ratio=2.1), # Invalid date
            PBDataPoint(date='2020-01-01', pb_ratio=2.2),  # Valid date
        ]
        
        # Should handle gracefully
        consistency_score = self.engine._assess_temporal_consistency(data_missing_dates)
        self.assertGreaterEqual(consistency_score, 0.0)
        self.assertLessEqual(consistency_score, 1.0)


if __name__ == '__main__':
    # Set up test logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    unittest.main(verbosity=2)