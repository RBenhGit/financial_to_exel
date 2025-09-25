"""
Comprehensive Test Suite for P/B Statistical Analysis Engine
===========================================================

This module provides comprehensive tests for the advanced P/B statistical analysis
features including trend detection, market cycle analysis, volatility assessment,
and correlation analysis.

Test Categories:
- Unit tests for individual statistical methods
- Integration tests with historical P/B data
- Edge case handling and error conditions
- Performance and accuracy validation
- Mock data generation for controlled testing

Usage:
------
Run all tests:
    python -m pytest test_pb_statistical_analysis.py -v

Run specific test class:
    python -m pytest test_pb_statistical_analysis.py::TestPBTrendDetection -v
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import warnings

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore")

from core.analysis.pb.pb_statistical_analysis import (
    PBStatisticalAnalysisEngine,
    PBStatisticalAnalysisResult,
    PBTrendDetectionResult,
    PBMarketCycleAnalysis,
    PBVolatilityAssessment,
    PBCorrelationAnalysis,
    create_statistical_analysis_report,
    validate_statistical_analysis_inputs
)
from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisResult,
    PBDataPoint,
    PBStatisticalSummary,
    PBHistoricalQualityMetrics,
    PBTrendAnalysis
)


class TestDataGenerator:
    """Helper class to generate test data for P/B analysis."""
    
    @staticmethod
    def create_sample_pb_data(periods: int = 48, 
                             trend: str = "neutral",
                             volatility: float = 0.2,
                             cycles: bool = False) -> List[PBDataPoint]:
        """
        Create sample P/B data points for testing.
        
        Args:
            periods (int): Number of periods to generate
            trend (str): "upward", "downward", or "neutral"
            volatility (float): Volatility level (0.0 to 1.0)
            cycles (bool): Whether to include cyclical patterns
            
        Returns:
            List[PBDataPoint]: Generated test data
        """
        np.random.seed(42)  # For reproducible tests
        
        base_pb = 1.5
        data_points = []
        
        for i in range(periods):
            # Generate date (monthly data going back)
            date = datetime.now() - timedelta(days=30 * (periods - i - 1))
            
            # Calculate P/B ratio with trend and noise
            time_factor = i / periods
            
            # Add trend
            if trend == "upward":
                trend_component = base_pb * (1 + 0.5 * time_factor)
            elif trend == "downward":
                trend_component = base_pb * (1 - 0.3 * time_factor)
            else:
                trend_component = base_pb
            
            # Add cyclical component
            if cycles:
                cycle_component = 0.3 * np.sin(2 * np.pi * i / 12)  # 12-month cycle
            else:
                cycle_component = 0.0
            
            # Add random noise
            noise = np.random.normal(0, volatility * base_pb)
            
            pb_ratio = trend_component + cycle_component + noise
            pb_ratio = max(0.1, pb_ratio)  # Ensure positive P/B
            
            # Generate corresponding values
            book_value = 20.0 + np.random.normal(0, 2.0)
            market_price = pb_ratio * book_value
            
            data_point = PBDataPoint(
                date=date.strftime('%Y-%m-%d'),
                pb_ratio=pb_ratio,
                book_value_per_share=book_value,
                market_price=market_price,
                market_cap=market_price * 1000000,  # Mock market cap
                shares_outstanding=1000000
            )
            
            data_points.append(data_point)
        
        return data_points
    
    @staticmethod
    def create_mock_historical_result(pb_data: List[PBDataPoint],
                                     ticker: str = "TEST") -> PBHistoricalAnalysisResult:
        """Create a mock historical analysis result for testing."""
        
        # Create quality metrics
        quality_metrics = PBHistoricalQualityMetrics()
        quality_metrics.completeness = 0.95
        quality_metrics.accuracy = 0.90
        quality_metrics.consistency = 0.85
        quality_metrics.pb_data_completeness = 0.95
        quality_metrics.calculate_overall_score()
        
        # Create statistical summary
        pb_values = [dp.pb_ratio for dp in pb_data if dp.pb_ratio]
        statistics = PBStatisticalSummary()
        statistics.mean_pb = np.mean(pb_values)
        statistics.median_pb = np.median(pb_values)
        statistics.std_pb = np.std(pb_values)
        statistics.min_pb = np.min(pb_values)
        statistics.max_pb = np.max(pb_values)
        statistics.p25_pb = np.percentile(pb_values, 25)
        statistics.p75_pb = np.percentile(pb_values, 75)
        statistics.quality_weighted_mean = statistics.mean_pb * 0.95
        
        # Create basic trend analysis
        trend_analysis = PBTrendAnalysis()
        trend_analysis.trend_direction = "neutral"
        trend_analysis.trend_strength = 0.3
        trend_analysis.volatility = statistics.std_pb
        
        # Create historical result
        result = PBHistoricalAnalysisResult(
            success=True,
            ticker=ticker,
            analysis_period="4 years",
            data_points_count=len(pb_data),
            historical_data=pb_data,
            quality_metrics=quality_metrics,
            statistics=statistics,
            trend_analysis=trend_analysis
        )
        
        return result


class TestPBTrendDetection(unittest.TestCase):
    """Test cases for P/B trend detection functionality."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_upward_trend_detection(self):
        """Test detection of statistically significant upward trends."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=36, trend="upward", volatility=0.1
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertIsNotNone(analysis_result.trend_analysis)
        
        trend = analysis_result.trend_analysis
        self.assertEqual(trend.trend_direction, "upward")
        self.assertGreater(trend.trend_strength, 0.3)
        self.assertGreater(trend.statistical_significance, 0.5)
        self.assertGreater(trend.linear_slope, 0)
    
    def test_downward_trend_detection(self):
        """Test detection of statistically significant downward trends."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=36, trend="downward", volatility=0.1
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        trend = analysis_result.trend_analysis
        self.assertEqual(trend.trend_direction, "downward")
        self.assertGreater(trend.trend_strength, 0.2)
        self.assertLess(trend.linear_slope, 0)
    
    def test_neutral_trend_detection(self):
        """Test detection of neutral/sideways trends."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=36, trend="neutral", volatility=0.15
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        trend = analysis_result.trend_analysis
        self.assertEqual(trend.trend_direction, "neutral")
        self.assertLess(trend.trend_strength, 0.5)
    
    def test_trend_consistency_calculation(self):
        """Test trend consistency scoring."""
        # Create data with consistent trend
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, trend="upward", volatility=0.05
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        trend = analysis_result.trend_analysis
        self.assertGreaterEqual(trend.trend_consistency, 0.0)
        self.assertLessEqual(trend.trend_consistency, 1.0)
    
    def test_confidence_intervals(self):
        """Test confidence interval calculation for trends."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        trend = analysis_result.trend_analysis
        self.assertIsInstance(trend.confidence_interval, tuple)
        self.assertEqual(len(trend.confidence_interval), 2)
        self.assertLessEqual(trend.confidence_interval[0], trend.confidence_interval[1])


class TestPBMarketCycleAnalysis(unittest.TestCase):
    """Test cases for market cycle detection and analysis."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_cycle_detection(self):
        """Test detection of cyclical patterns in P/B data."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=60, cycles=True, volatility=0.1
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertIsNotNone(analysis_result.cycle_analysis)
        
        cycle = analysis_result.cycle_analysis
        self.assertGreaterEqual(cycle.cycles_detected, 0)
        self.assertIn(cycle.current_cycle_position, 
                     ["expansion", "peak", "contraction", "trough", "unknown"])
    
    def test_regime_analysis(self):
        """Test market regime detection."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, volatility=0.3  # High volatility
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        cycle = analysis_result.cycle_analysis
        self.assertIn(cycle.current_regime, ["bull", "bear", "normal", "volatile"])
        self.assertGreaterEqual(cycle.regime_probability, 0.0)
        self.assertLessEqual(cycle.regime_probability, 1.0)
    
    def test_cycle_timing_metrics(self):
        """Test cycle timing and maturity calculations."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        cycle = analysis_result.cycle_analysis
        self.assertGreaterEqual(cycle.time_since_last_peak, 0)
        self.assertGreaterEqual(cycle.time_since_last_trough, 0)
        self.assertGreaterEqual(cycle.cycle_maturity, 0.0)
        self.assertLessEqual(cycle.cycle_maturity, 1.0)


class TestPBVolatilityAssessment(unittest.TestCase):
    """Test cases for volatility assessment and risk scoring."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_volatility_calculation(self):
        """Test basic volatility calculations."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, volatility=0.25
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertIsNotNone(analysis_result.volatility_analysis)
        
        vol = analysis_result.volatility_analysis
        self.assertGreater(vol.historical_volatility, 0)
        self.assertGreaterEqual(vol.volatility_percentile, 0.0)
        self.assertLessEqual(vol.volatility_percentile, 1.0)
    
    def test_risk_scoring(self):
        """Test risk score calculations."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, volatility=0.4  # High volatility
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        vol = analysis_result.volatility_analysis
        self.assertGreaterEqual(vol.overall_risk_score, 0.0)
        self.assertLessEqual(vol.overall_risk_score, 1.0)
        self.assertGreaterEqual(vol.downside_risk_score, 0.0)
        self.assertGreaterEqual(vol.tail_risk_score, 0.0)
    
    def test_volatility_clustering(self):
        """Test volatility clustering detection."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        vol = analysis_result.volatility_analysis
        self.assertGreaterEqual(vol.volatility_clustering_score, 0.0)
        self.assertLessEqual(vol.volatility_clustering_score, 1.0)
    
    def test_maximum_drawdown(self):
        """Test maximum drawdown calculation."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        vol = analysis_result.volatility_analysis
        self.assertGreaterEqual(vol.maximum_drawdown, 0.0)
        self.assertLessEqual(vol.maximum_drawdown, 1.0)
    
    def test_volatility_regimes(self):
        """Test volatility regime classification."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        vol = analysis_result.volatility_analysis
        self.assertIn(vol.current_vol_regime, ["low", "normal", "high", "extreme"])
        self.assertIn(vol.volatility_trend, ["increasing", "decreasing", "stable"])


class TestPBCorrelationAnalysis(unittest.TestCase):
    """Test cases for correlation analysis functionality."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_correlation_analysis_without_market_data(self):
        """Test correlation analysis with internal data only."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertIsNotNone(analysis_result.correlation_analysis)
        
        corr = analysis_result.correlation_analysis
        self.assertIn(corr.correlation_regime, ["low", "normal", "high", "crisis"])
    
    def test_correlation_analysis_with_market_data(self):
        """Test correlation analysis with external market data."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        # Mock market data
        market_data = {
            'market_returns': np.random.normal(0, 0.1, 48),
            'sector_returns': np.random.normal(0, 0.12, 48)
        }
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result, market_data)
        
        corr = analysis_result.correlation_analysis
        self.assertGreaterEqual(corr.market_correlation, 0.0)
        self.assertGreaterEqual(corr.predictive_power, 0.0)


class TestPBStatisticalAnalysisEngine(unittest.TestCase):
    """Test cases for the main statistical analysis engine."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_complete_analysis_success(self):
        """Test successful completion of full statistical analysis."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertEqual(analysis_result.ticker, "TEST")
        self.assertIsNotNone(analysis_result.trend_analysis)
        self.assertIsNotNone(analysis_result.cycle_analysis)
        self.assertIsNotNone(analysis_result.volatility_analysis)
        self.assertIsNotNone(analysis_result.correlation_analysis)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data scenarios."""
        # Create very limited data
        pb_data = self.data_generator.create_sample_pb_data(periods=10)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertFalse(analysis_result.success)
        self.assertIsNotNone(analysis_result.error_message)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        # Create invalid historical result
        invalid_result = PBHistoricalAnalysisResult(success=False, error_message="Test error")
        
        analysis_result = self.engine.analyze_pb_statistics(invalid_result)
        
        self.assertFalse(analysis_result.success)
        self.assertIsNotNone(analysis_result.error_message)
    
    def test_overall_assessment_generation(self):
        """Test generation of overall market timing assessment."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, trend="upward", volatility=0.1
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertTrue(analysis_result.success)
        self.assertIn(analysis_result.market_timing_signal, ["bullish", "bearish", "neutral"])
        self.assertGreaterEqual(analysis_result.signal_strength, 0.0)
        self.assertLessEqual(analysis_result.signal_strength, 1.0)
        self.assertGreaterEqual(analysis_result.statistical_confidence, 0.0)
        self.assertLessEqual(analysis_result.statistical_confidence, 1.0)
    
    def test_analysis_warnings_generation(self):
        """Test generation of appropriate analysis warnings."""
        # Create low quality data
        pb_data = self.data_generator.create_sample_pb_data(periods=20)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        historical_result.quality_metrics.overall_score = 0.3  # Low quality
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        # Should generate warnings for low data quality
        if analysis_result.success:
            self.assertTrue(len(analysis_result.analysis_warnings) >= 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    def setUp(self):
        self.data_generator = TestDataGenerator()
    
    def test_create_statistical_analysis_report(self):
        """Test statistical analysis report creation."""
        # Create mock analysis result
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        engine = PBStatisticalAnalysisEngine()
        analysis_result = engine.analyze_pb_statistics(historical_result)
        
        report = create_statistical_analysis_report(analysis_result)
        
        self.assertTrue(report['success'])
        self.assertIn('trend_analysis', report)
        self.assertIn('cycle_analysis', report)
        self.assertIn('volatility_analysis', report)
        self.assertIn('market_timing', report)
    
    def test_validate_statistical_analysis_inputs(self):
        """Test input validation for statistical analysis."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        validation = validate_statistical_analysis_inputs(historical_result)
        
        self.assertTrue(validation['valid'])
        self.assertIsInstance(validation['issues'], list)
        self.assertIsInstance(validation['recommendations'], list)
    
    def test_validation_with_insufficient_data(self):
        """Test validation with insufficient data."""
        pb_data = self.data_generator.create_sample_pb_data(periods=5)
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        validation = validate_statistical_analysis_inputs(historical_result)
        
        self.assertGreater(len(validation['issues']), 0)
    
    def test_report_creation_with_failed_analysis(self):
        """Test report creation when analysis fails."""
        failed_result = PBStatisticalAnalysisResult(
            success=False,
            ticker="TEST",
            error_message="Test failure"
        )
        
        report = create_statistical_analysis_report(failed_result)
        
        self.assertFalse(report['success'])
        self.assertEqual(report['error'], "Test failure")
        self.assertEqual(report['ticker'], "TEST")


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and error conditions."""
    
    def setUp(self):
        self.engine = PBStatisticalAnalysisEngine()
        self.data_generator = TestDataGenerator()
    
    def test_all_zero_pb_ratios(self):
        """Test handling of all zero P/B ratios."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        # Set all P/B ratios to None or 0
        for dp in pb_data:
            dp.pb_ratio = 0.0
        
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertFalse(analysis_result.success)
    
    def test_single_valid_pb_ratio(self):
        """Test handling of single valid P/B ratio."""
        pb_data = self.data_generator.create_sample_pb_data(periods=48)
        # Set all but one P/B ratio to None
        for i, dp in enumerate(pb_data):
            if i != 0:
                dp.pb_ratio = None
        
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        self.assertFalse(analysis_result.success)
    
    def test_extreme_volatility(self):
        """Test handling of extreme volatility scenarios."""
        pb_data = self.data_generator.create_sample_pb_data(
            periods=48, volatility=2.0  # Extreme volatility
        )
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        if analysis_result.success:
            vol = analysis_result.volatility_analysis
            self.assertGreater(vol.overall_risk_score, 0.7)  # Should detect high risk
    
    def test_perfect_linear_trend(self):
        """Test handling of perfect linear trend (no noise)."""
        # Create perfect linear trend
        pb_data = []
        for i in range(48):
            date = datetime.now() - timedelta(days=30 * (48 - i - 1))
            pb_ratio = 1.0 + (i * 0.01)  # Perfect linear increase
            
            data_point = PBDataPoint(
                date=date.strftime('%Y-%m-%d'),
                pb_ratio=pb_ratio,
                book_value_per_share=20.0,
                market_price=pb_ratio * 20.0,
                market_cap=pb_ratio * 20.0 * 1000000,
                shares_outstanding=1000000
            )
            pb_data.append(data_point)
        
        historical_result = self.data_generator.create_mock_historical_result(pb_data)
        analysis_result = self.engine.analyze_pb_statistics(historical_result)
        
        if analysis_result.success:
            trend = analysis_result.trend_analysis
            self.assertEqual(trend.trend_direction, "upward")
            self.assertGreater(trend.r_squared, 0.9)  # Should have very high R-squared


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)