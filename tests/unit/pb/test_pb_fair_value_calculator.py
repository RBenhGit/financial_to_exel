"""
Test Suite for P/B Fair Value Calculator
========================================

Comprehensive tests for the fair value calculation engine including:
- Input validation
- Core algorithm functionality  
- Weighted calculations with exponential decay
- Scenario analysis (Conservative/Fair/Optimistic)
- Quality integration and confidence adjustments
- Statistical significance testing
- Investment recommendation logic
"""

import unittest
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import modules to test
from pb_fair_value_calculator import (
    PBFairValueCalculator, 
    FairValueScenario, 
    FairValueCalculationResult,
    create_fair_value_report,
    validate_fair_value_inputs
)
from pb_historical_analysis import (
    PBHistoricalAnalysisResult, 
    PBHistoricalQualityMetrics, 
    PBStatisticalSummary,
    PBTrendAnalysis
)
from pb_calculation_engine import PBDataPoint
from data_sources import DataSourceType


class TestPBFairValueCalculator(unittest.TestCase):
    """Test cases for P/B Fair Value Calculator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = PBFairValueCalculator(decay_factor=0.85, min_data_points=12)
        self.sample_ticker = "MSFT"
        self.sample_book_value = 25.50
        self.sample_current_price = 380.00
        
        # Create sample historical analysis result
        self.sample_historical = self._create_sample_historical_analysis()
    
    def _create_sample_historical_analysis(self) -> PBHistoricalAnalysisResult:
        """Create sample historical analysis for testing"""
        
        # Create sample P/B data points (5 years quarterly = 20 points)
        historical_data = []
        base_date = datetime.now() - timedelta(days=5*365)
        
        # Generate realistic P/B ratios with some variation
        pb_values = [2.1, 2.3, 2.0, 2.4, 2.2, 2.6, 2.1, 2.3, 2.5, 2.2, 
                    2.4, 2.0, 2.7, 2.3, 2.1, 2.5, 2.2, 2.4, 2.6, 2.3]
        
        for i, pb in enumerate(pb_values):
            date = base_date + timedelta(days=i*90)  # Quarterly
            historical_data.append(PBDataPoint(
                date=date.strftime('%Y-%m-%d'),
                price=pb * self.sample_book_value,  # Derive price from P/B
                book_value_per_share=self.sample_book_value + (i * 0.5),  # Growing book value
                pb_ratio=pb,
                data_quality=0.85
            ))
        
        # Create quality metrics
        quality_metrics = PBHistoricalQualityMetrics()
        quality_metrics.completeness = 0.90
        quality_metrics.accuracy = 0.85
        quality_metrics.timeliness = 0.80
        quality_metrics.consistency = 0.88
        quality_metrics.pb_data_completeness = 0.95
        quality_metrics.price_data_quality = 0.90
        quality_metrics.balance_sheet_quality = 0.85
        quality_metrics.temporal_consistency = 0.85
        quality_metrics.calculate_overall_score()
        
        # Create statistical summary
        statistics = PBStatisticalSummary()
        statistics.mean_pb = np.mean(pb_values)
        statistics.median_pb = np.median(pb_values)
        statistics.std_pb = np.std(pb_values)
        statistics.min_pb = np.min(pb_values)
        statistics.max_pb = np.max(pb_values)
        statistics.p25_pb = np.percentile(pb_values, 25)
        statistics.p75_pb = np.percentile(pb_values, 75)
        statistics.p90_pb = np.percentile(pb_values, 90)
        statistics.p95_pb = np.percentile(pb_values, 95)
        statistics.quality_weighted_mean = statistics.mean_pb * 1.02  # Slightly higher due to quality weighting
        statistics.quality_weighted_std = statistics.std_pb * 0.95
        
        # Create trend analysis
        trend_analysis = PBTrendAnalysis()
        trend_analysis.trend_direction = "neutral"
        trend_analysis.trend_strength = 0.3
        trend_analysis.volatility = statistics.std_pb
        trend_analysis.r_squared = 0.15
        
        # Create full result
        result = PBHistoricalAnalysisResult(
            success=True,
            ticker=self.sample_ticker,
            analysis_period="5 years",
            data_points_count=len(historical_data),
            historical_data=historical_data,
            quality_metrics=quality_metrics,
            statistics=statistics,
            trend_analysis=trend_analysis,
            current_pb_percentile=0.45,
            fair_value_estimate=statistics.mean_pb,
            valuation_signal="fairly_valued"
        )
        
        return result
    
    def test_calculator_initialization(self):
        """Test calculator initialization with parameters"""
        calc = PBFairValueCalculator(decay_factor=0.9, min_data_points=16)
        
        self.assertEqual(calc.decay_factor, 0.9)
        self.assertEqual(calc.min_data_points, 16)
        self.assertEqual(calc.confidence_threshold, 0.7)
    
    def test_input_validation_success(self):
        """Test successful input validation"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical, 
            self.sample_book_value,
            self.sample_current_price
        )
        
        # Should not fail validation
        self.assertTrue(result.success or len(result.calculation_warnings) == 0)
    
    def test_input_validation_insufficient_data(self):
        """Test validation with insufficient historical data"""
        # Create minimal historical data
        minimal_historical = self.sample_historical
        minimal_historical.data_points_count = 3
        minimal_historical.historical_data = minimal_historical.historical_data[:3]
        
        result = self.calculator.calculate_fair_value(minimal_historical, self.sample_book_value)
        
        self.assertFalse(result.success)
        self.assertIn("Insufficient historical data", result.error_message)
    
    def test_input_validation_invalid_book_value(self):
        """Test validation with invalid book value"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical, 
            -5.0  # Negative book value
        )
        
        self.assertFalse(result.success)
        self.assertIn("Invalid book value", result.error_message)
    
    def test_weighted_pb_calculation(self):
        """Test weighted P/B multiple calculation with exponential decay"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value
        )
        
        self.assertTrue(result.success)
        self.assertGreater(result.weighted_pb_multiple, 0)
        self.assertEqual(result.exponential_decay_factor, 0.85)
        self.assertGreater(result.quality_adjustment_factor, 0)
        
        # Weighted P/B should be reasonable (between min and max historical)
        stats = self.sample_historical.statistics
        self.assertGreaterEqual(result.weighted_pb_multiple, stats.min_pb * 0.8)
        self.assertLessEqual(result.weighted_pb_multiple, stats.max_pb * 1.2)
    
    def test_scenario_analysis(self):
        """Test Conservative/Fair/Optimistic scenario calculations"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value
        )
        
        self.assertTrue(result.success)
        
        # All scenarios should exist
        self.assertIsNotNone(result.conservative_scenario)
        self.assertIsNotNone(result.fair_scenario)
        self.assertIsNotNone(result.optimistic_scenario)
        
        # Scenarios should be ordered: Conservative < Fair < Optimistic
        conservative_price = result.conservative_scenario.target_price
        fair_price = result.fair_scenario.target_price
        optimistic_price = result.optimistic_scenario.target_price
        
        self.assertLess(conservative_price, fair_price)
        self.assertLess(fair_price, optimistic_price)
        
        # Check percentile basis
        self.assertEqual(result.conservative_scenario.percentile_basis, 25.0)
        self.assertEqual(result.fair_scenario.percentile_basis, 50.0)
        self.assertEqual(result.optimistic_scenario.percentile_basis, 75.0)
        
        # All scenarios should use current book value
        for scenario in [result.conservative_scenario, result.fair_scenario, result.optimistic_scenario]:
            self.assertEqual(scenario.book_value_per_share, self.sample_book_value)
            self.assertGreater(scenario.pb_multiple, 0)
            self.assertGreater(scenario.confidence_level, 0)
    
    def test_quality_integration(self):
        """Test integration of DataQualityMetrics for confidence adjustments"""
        # Test with high quality data
        result_high_quality = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value
        )
        
        # Test with low quality data
        low_quality_historical = self.sample_historical
        low_quality_historical.quality_metrics.overall_score = 0.4
        low_quality_historical.quality_metrics.pb_data_completeness = 0.5
        
        result_low_quality = self.calculator.calculate_fair_value(
            low_quality_historical,
            self.sample_book_value
        )
        
        # High quality should have higher confidence
        if result_high_quality.success and result_low_quality.success:
            self.assertGreater(
                result_high_quality.fair_scenario.confidence_level,
                result_low_quality.fair_scenario.confidence_level
            )
            
            # Low quality should generate warnings
            self.assertGreater(len(result_low_quality.calculation_warnings), 0)
    
    def test_statistical_validation(self):
        """Test statistical significance and confidence interval calculations"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value
        )
        
        self.assertTrue(result.success)
        
        # Statistical validation should be calculated
        self.assertGreaterEqual(result.statistical_significance, 0.0)
        self.assertLessEqual(result.statistical_significance, 1.0)
        
        # Confidence interval should exist and be reasonable
        lower, upper = result.confidence_interval
        self.assertLess(lower, upper)
        self.assertGreater(lower, 0)
        
        # Fair value should be within or near confidence interval
        fair_price = result.fair_scenario.target_price
        interval_width = upper - lower
        self.assertLess(abs(fair_price - (lower + upper) / 2), interval_width)
    
    def test_investment_recommendation_buy_signal(self):
        """Test investment recommendation with undervalued scenario"""
        # Set current price significantly below fair value
        low_current_price = 40.0  # Much lower than expected fair value
        
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value,
            low_current_price
        )
        
        self.assertTrue(result.success)
        
        # Should generate buy signal with significant undervaluation
        self.assertEqual(result.investment_signal, "buy")
        self.assertGreater(result.signal_strength, 0.5)
        self.assertGreater(result.margin_of_safety, 0.15)
    
    def test_investment_recommendation_sell_signal(self):
        """Test investment recommendation with overvalued scenario"""
        # Set current price significantly above fair value
        high_current_price = 150.0  # Much higher than expected fair value
        
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value,
            high_current_price
        )
        
        self.assertTrue(result.success)
        
        # Should generate sell signal with significant overvaluation
        self.assertEqual(result.investment_signal, "sell")
        self.assertGreater(result.signal_strength, 0.5)
        self.assertLess(result.margin_of_safety, -0.15)
    
    def test_investment_recommendation_neutral_low_confidence(self):
        """Test neutral recommendation with low confidence data"""
        # Create low confidence scenario
        low_confidence_historical = self.sample_historical
        low_confidence_historical.quality_metrics.overall_score = 0.4
        
        result = self.calculator.calculate_fair_value(
            low_confidence_historical,
            self.sample_book_value,
            self.sample_current_price
        )
        
        if result.success:
            # Should be neutral due to low confidence
            self.assertEqual(result.investment_signal, "neutral")
            self.assertLess(result.signal_strength, 0.7)
    
    def test_methodology_notes_generation(self):
        """Test generation of methodology notes and warnings"""
        result = self.calculator.calculate_fair_value(
            self.sample_historical,
            self.sample_book_value
        )
        
        self.assertTrue(result.success)
        
        # Should have methodology notes
        self.assertGreater(len(result.methodology_notes), 0)
        
        # Should mention key methodology elements
        notes_text = " ".join(result.methodology_notes)
        self.assertIn("historical p/b", notes_text.lower())
        self.assertIn("exponential decay", notes_text.lower())
        self.assertIn("quality", notes_text.lower())
    
    def test_edge_case_single_scenario_value(self):
        """Test edge case where all historical P/B values are identical"""
        # Create historical data with identical P/B values
        uniform_historical = self.sample_historical
        uniform_pb = 2.5
        
        for dp in uniform_historical.historical_data:
            dp.pb_ratio = uniform_pb
        
        # Update statistics to reflect uniform values
        uniform_historical.statistics.mean_pb = uniform_pb
        uniform_historical.statistics.median_pb = uniform_pb
        uniform_historical.statistics.std_pb = 0.0
        uniform_historical.statistics.p25_pb = uniform_pb
        uniform_historical.statistics.p75_pb = uniform_pb
        
        result = self.calculator.calculate_fair_value(
            uniform_historical,
            self.sample_book_value
        )
        
        # Should still succeed and provide reasonable scenarios
        self.assertTrue(result.success)
        self.assertIsNotNone(result.fair_scenario)
        
        # All scenarios might be close to the uniform value
        fair_pb = result.fair_scenario.pb_multiple
        self.assertAlmostEqual(fair_pb, uniform_pb, delta=0.5)


class TestFairValueUtilityFunctions(unittest.TestCase):
    """Test utility functions for fair value calculations"""
    
    def test_create_fair_value_report_success(self):
        """Test successful fair value report creation"""
        # Create sample successful result
        result = FairValueCalculationResult(
            success=True,
            ticker="AAPL",
            calculation_date=datetime.now().isoformat(),
            current_price=150.0,
            current_book_value=20.0
        )
        
        # Add scenarios
        result.fair_scenario = FairValueScenario(
            scenario_name="Fair",
            pb_multiple=2.5,
            book_value_per_share=20.0,
            target_price=50.0,
            confidence_level=0.8
        )
        
        result.investment_signal = "buy"
        result.signal_strength = 0.7
        result.margin_of_safety = 0.25
        
        report = create_fair_value_report(result)
        
        self.assertTrue(report['success'])
        self.assertEqual(report['ticker'], "AAPL")
        self.assertEqual(report['fair_value_estimate']['target_price'], 50.0)
        self.assertEqual(report['investment_recommendation']['signal'], "buy")
    
    def test_create_fair_value_report_failure(self):
        """Test fair value report creation with failed calculation"""
        result = FairValueCalculationResult(
            success=False,
            ticker="MSFT",
            error_message="Insufficient data"
        )
        
        report = create_fair_value_report(result)
        
        self.assertFalse(report['success'])
        self.assertEqual(report['ticker'], "MSFT")
        self.assertIn("Insufficient data", report['error'])
    
    def test_validate_fair_value_inputs_valid(self):
        """Test input validation with valid inputs"""
        validation = validate_fair_value_inputs(25.50, 380.0)
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['issues']), 0)
        self.assertGreater(len(validation['recommendations']), 0)
    
    def test_validate_fair_value_inputs_invalid_book_value(self):
        """Test input validation with invalid book value"""
        validation = validate_fair_value_inputs(-5.0, 100.0)
        
        self.assertFalse(validation['valid'])
        self.assertIn("Book value per share must be positive", validation['issues'])
    
    def test_validate_fair_value_inputs_invalid_price(self):
        """Test input validation with invalid current price"""
        validation = validate_fair_value_inputs(25.0, -50.0)
        
        self.assertIn("Current price must be positive", validation['issues'])
    
    def test_validate_fair_value_inputs_extreme_pb_ratio(self):
        """Test input validation with extreme P/B ratio"""
        validation = validate_fair_value_inputs(1.0, 50.0)  # P/B = 50
        
        self.assertTrue(any("Very high P/B ratio" in issue for issue in validation['issues']))


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)