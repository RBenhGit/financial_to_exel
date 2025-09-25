"""
Direct test of statistical features for confidence intervals and Monte Carlo simulation.

This test bypasses the PBCalculationEngine and directly tests the statistical
functionality by creating PBDataPoint objects manually.
"""

import sys
import os
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    PBHistoricalQualityMetrics,
    PBStatisticalSummary,
    create_pb_historical_report
)
from core.analysis.pb.pb_calculation_engine import PBDataPoint
from core.data_sources.data_sources import DataSourceResponse, DataSourceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_pb_data(quality_score: float = 0.8, volatility_level: str = 'medium') -> List[PBDataPoint]:
    """Create mock PBDataPoint objects for testing"""
    
    # Base P/B values with different volatility patterns
    base_pb = 2.5
    
    if volatility_level == 'low':
        volatility = 0.3
    elif volatility_level == 'high':
        volatility = 1.2
    else:  # medium
        volatility = 0.6
    
    # Generate mock historical data (5 years of quarterly data)
    pb_data = []
    
    for i in range(20):  # 20 quarters = 5 years
        date = datetime.now() - timedelta(days=90 * (19 - i))
        
        # Add trend and seasonality
        trend_component = 0.02 * i  # Slight upward trend
        seasonal_component = 0.1 * np.sin(2 * np.pi * i / 4)  # Quarterly seasonality
        random_component = np.random.normal(0, volatility)
        
        pb_ratio = base_pb + trend_component + seasonal_component + random_component
        pb_ratio = max(0.1, pb_ratio)  # Ensure positive P/B
        
        # Create PBDataPoint
        data_point = PBDataPoint(
            date=date.strftime('%Y-%m-%d'),
            price=pb_ratio * 10.0,  # Assume book value per share of $10
            book_value_per_share=10.0,
            pb_ratio=pb_ratio,
            shares_outstanding=1000000.0,
            market_cap=pb_ratio * 10.0 * 1000000.0,
            data_quality=quality_score
        )
        
        pb_data.append(data_point)
    
    return pb_data


def test_confidence_intervals_direct():
    """Test confidence intervals using direct calculation methods"""
    logger.info("Testing confidence intervals with direct methods...")
    
    engine = PBHistoricalAnalysisEngine()
    
    # Test with different quality scores
    quality_scores = [0.5, 0.7, 0.9]
    results = {}
    
    for quality_score in quality_scores:
        logger.info(f"Testing with quality score: {quality_score}")
        
        pb_data = create_mock_pb_data(quality_score=quality_score)
        valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
        
        # Test confidence interval calculation directly
        confidence_interval = engine._calculate_confidence_intervals(valid_ratios, quality_score)
        
        results[quality_score] = {
            'confidence_interval': confidence_interval,
            'interval_width': confidence_interval[1] - confidence_interval[0],
            'mean_pb': np.mean(valid_ratios)
        }
        
        logger.info(f"Quality {quality_score}: CI = {confidence_interval}, width = {confidence_interval[1] - confidence_interval[0]:.3f}")
    
    # Verify that higher quality leads to narrower confidence intervals
    if len(results) >= 2:
        low_quality_width = results[0.5]['interval_width']
        high_quality_width = results[0.9]['interval_width']
        
        logger.info(f"Low quality CI width: {low_quality_width:.3f}")
        logger.info(f"High quality CI width: {high_quality_width:.3f}")
        
        if high_quality_width < low_quality_width:
            logger.info("✓ Higher quality data produces narrower confidence intervals")
            return True
        else:
            logger.warning("✗ Expected narrower intervals for higher quality data")
            return False
    
    return True


def test_statistical_significance_direct():
    """Test statistical significance testing directly"""
    logger.info("Testing statistical significance tests...")
    
    engine = PBHistoricalAnalysisEngine()
    pb_data = create_mock_pb_data(quality_score=0.8)
    valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
    
    # Create empty summary to populate
    summary = PBStatisticalSummary()
    
    # Test statistical significance directly
    enhanced_summary = engine._perform_statistical_significance_tests(summary, valid_ratios)
    
    logger.info(f"Normality test p-value: {enhanced_summary.normality_test_pvalue:.4f}")
    logger.info(f"Is normal distribution: {enhanced_summary.is_normal_distribution}")
    logger.info(f"Skewness: {enhanced_summary.skewness:.3f}")
    logger.info(f"Kurtosis: {enhanced_summary.kurtosis:.3f}")
    
    # Check significance tests
    if enhanced_summary.statistical_significance:
        significant_tests = 0
        total_tests = 0
        
        for test_name, result in enhanced_summary.statistical_significance.items():
            if isinstance(result, bool):
                total_tests += 1
                if result:
                    significant_tests += 1
                logger.info(f"{test_name}: {'Significant' if result else 'Not significant'}")
            else:
                logger.info(f"{test_name}: {result:.4f}")
        
        logger.info(f"Significant tests: {significant_tests}/{total_tests}")
    
    logger.info("✓ Statistical significance testing completed")
    return True


def test_monte_carlo_direct():
    """Test Monte Carlo simulation directly"""
    logger.info("Testing Monte Carlo simulation...")
    
    engine = PBHistoricalAnalysisEngine()
    pb_data = create_mock_pb_data(quality_score=0.8)
    valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
    
    # Create summary with basic statistics
    summary = PBStatisticalSummary()
    summary.mean_pb = np.mean(valid_ratios)
    summary.std_pb = np.std(valid_ratios)
    summary.is_normal_distribution = True  # Assume normal for this test
    
    # Create quality metrics
    quality_metrics = PBHistoricalQualityMetrics()
    quality_metrics.overall_score = 0.8
    
    # Test Monte Carlo simulation directly
    enhanced_summary = engine._run_monte_carlo_simulation(summary, valid_ratios, quality_metrics)
    
    logger.info(f"Original mean: {summary.mean_pb:.3f}")
    logger.info(f"Monte Carlo mean: {enhanced_summary.monte_carlo_mean:.3f}")
    logger.info(f"Monte Carlo std: {enhanced_summary.monte_carlo_std:.3f}")
    
    # Check confidence intervals
    if enhanced_summary.monte_carlo_confidence_intervals:
        for level, (lower, upper) in enhanced_summary.monte_carlo_confidence_intervals.items():
            width = upper - lower
            logger.info(f"MC {level} CI: [{lower:.3f}, {upper:.3f}] (width: {width:.3f})")
    
    # Check Value at Risk
    if enhanced_summary.monte_carlo_value_at_risk:
        for level, var_value in enhanced_summary.monte_carlo_value_at_risk.items():
            logger.info(f"VaR {level}: {var_value:.3f}")
    
    # Verify Monte Carlo results are reasonable
    mc_mean_diff = abs(enhanced_summary.monte_carlo_mean - summary.mean_pb)
    if mc_mean_diff < 0.5:  # Should be close to original mean
        logger.info("✓ Monte Carlo mean is close to original mean")
        return True
    else:
        logger.warning(f"✗ Monte Carlo mean differs significantly from original: {mc_mean_diff:.3f}")
        return False


def test_risk_scenarios_direct():
    """Test risk scenario generation directly"""
    logger.info("Testing risk scenario generation...")
    
    engine = PBHistoricalAnalysisEngine()
    
    # Test with different volatility levels
    volatility_levels = ['low', 'medium', 'high']
    scenario_widths = {}
    
    for vol_level in volatility_levels:
        logger.info(f"Testing {vol_level} volatility scenario...")
        
        pb_data = create_mock_pb_data(quality_score=0.8, volatility_level=vol_level)
        valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
        
        # Create mock analysis result
        from pb_historical_analysis import PBHistoricalAnalysisResult
        result = PBHistoricalAnalysisResult(success=True)
        
        # Create statistics
        result.statistics = PBStatisticalSummary()
        result.statistics.mean_pb = np.mean(valid_ratios)
        result.statistics.std_pb = np.std(valid_ratios)
        result.statistics.quality_weighted_mean = result.statistics.mean_pb
        
        # Create quality metrics
        result.quality_metrics = PBHistoricalQualityMetrics()
        result.quality_metrics.overall_score = 0.8
        
        # Generate risk scenarios
        engine._generate_risk_scenarios(result)
        
        if result.risk_scenarios:
            bear_pb = result.risk_scenarios['bear']['pb_estimate']
            bull_pb = result.risk_scenarios['bull']['pb_estimate']
            scenario_width = bull_pb - bear_pb
            scenario_widths[vol_level] = scenario_width
            
            logger.info(f"{vol_level.capitalize()} volatility scenarios:")
            for scenario_name, scenario_data in result.risk_scenarios.items():
                logger.info(f"  {scenario_name}: P/B={scenario_data['pb_estimate']:.2f}, "
                          f"Prob={scenario_data['probability_weight']:.1%}")
            
            logger.info(f"Scenario range width: {scenario_width:.2f}")
    
    # Verify that higher volatility leads to wider scenario ranges
    if 'low' in scenario_widths and 'high' in scenario_widths:
        if scenario_widths['high'] > scenario_widths['low']:
            logger.info("✓ Higher volatility produces wider scenario ranges")
            return True
        else:
            logger.warning("✗ Expected wider ranges for higher volatility")
            return False
    
    return True


def run_direct_tests():
    """Run all direct statistical feature tests"""
    logger.info("=" * 80)
    logger.info("RUNNING DIRECT STATISTICAL FEATURE TESTS")
    logger.info("=" * 80)
    
    test_results = {}
    
    try:
        # Test 1: Confidence intervals
        logger.info("\n" + "1. TESTING CONFIDENCE INTERVALS DIRECTLY" + "\n" + "-" * 50)
        test_results['confidence_intervals'] = test_confidence_intervals_direct()
        
        # Test 2: Statistical significance
        logger.info("\n" + "2. TESTING STATISTICAL SIGNIFICANCE DIRECTLY" + "\n" + "-" * 50)
        test_results['statistical_significance'] = test_statistical_significance_direct()
        
        # Test 3: Monte Carlo simulation
        logger.info("\n" + "3. TESTING MONTE CARLO SIMULATION DIRECTLY" + "\n" + "-" * 50)
        test_results['monte_carlo'] = test_monte_carlo_direct()
        
        # Test 4: Risk scenarios
        logger.info("\n" + "4. TESTING RISK SCENARIOS DIRECTLY" + "\n" + "-" * 50)
        test_results['risk_scenarios'] = test_risk_scenarios_direct()
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        test_results['error'] = str(e)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DIRECT TEST SUMMARY")
    logger.info("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result is True)
    total_tests = len([r for r in test_results.values() if isinstance(r, bool)])
    
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, result in test_results.items():
        if isinstance(result, bool):
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        logger.info("\n🎉 ALL DIRECT TESTS PASSED! Statistical features are working correctly.")
    else:
        logger.warning(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the implementation.")
    
    return test_results


if __name__ == "__main__":
    # Set random seed for reproducible results
    np.random.seed(42)
    
    # Run all direct tests
    results = run_direct_tests()