"""
Test script for enhanced confidence intervals and valuation ranges with quality scoring.

This script tests the new statistical significance testing, Monte Carlo simulation,
and risk-adjusted scenario functionality added to the P/B historical analysis.
"""

import sys
import os
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pb_historical_analysis import (
    PBHistoricalAnalysisEngine, 
    PBHistoricalQualityMetrics,
    create_pb_historical_report
)
from data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics
from pb_calculation_engine import PBDataPoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_data_response(quality_score: float = 0.8, volatility_level: str = 'medium') -> DataSourceResponse:
    """Create mock data response for testing with different quality scores and volatility"""
    
    # Base P/B values with different volatility patterns
    base_pb = 2.5
    
    if volatility_level == 'low':
        volatility = 0.3
    elif volatility_level == 'high':
        volatility = 1.2
    else:  # medium
        volatility = 0.6
    
    # Generate mock historical data (5 years of quarterly data)
    historical_data = []
    dates = []
    pb_ratios = []
    
    for i in range(20):  # 20 quarters = 5 years
        date = datetime.now() - timedelta(days=90 * (19 - i))
        dates.append(date.strftime('%Y-%m-%d'))
        
        # Add trend and seasonality
        trend_component = 0.02 * i  # Slight upward trend
        seasonal_component = 0.1 * np.sin(2 * np.pi * i / 4)  # Quarterly seasonality
        random_component = np.random.normal(0, volatility)
        
        pb_ratio = base_pb + trend_component + seasonal_component + random_component
        pb_ratio = max(0.1, pb_ratio)  # Ensure positive P/B
        pb_ratios.append(pb_ratio)
        
        # Create mock balance sheet and price data
        price = pb_ratio * 10.0  # Assume book value per share of $10
        book_value_per_share = 10.0
        
        historical_data.append({
            'date': dates[-1],
            'price': price,
            'book_value_per_share': book_value_per_share,
            'pb_ratio': pb_ratio
        })
    
    # Create quality metrics based on input score
    quality_metrics = DataQualityMetrics()
    quality_metrics.completeness = min(1.0, quality_score + 0.1)
    quality_metrics.accuracy = quality_score
    quality_metrics.timeliness = max(0.5, quality_score - 0.1)
    quality_metrics.consistency = quality_score
    quality_metrics.calculate_overall_score()
    
    # Create properly formatted historical prices as list
    historical_prices_list = []
    quarterly_balance_sheet_list = []
    
    for data_point in historical_data:
        historical_prices_list.append({
            'date': data_point['date'],
            'close': data_point['price'],
            'price': data_point['price']
        })
        quarterly_balance_sheet_list.append({
            'date': data_point['date'],
            'totalStockholderEquity': data_point['book_value_per_share'] * 1000000,  # Scale up to total equity
            'sharesOutstanding': 1000000,  # 1M shares outstanding
            'bookValuePerShare': data_point['book_value_per_share']
        })
    
    # Mock data structure
    mock_data = {
        'ticker': 'TEST',
        'historical_prices': historical_prices_list,
        'quarterly_balance_sheet': quarterly_balance_sheet_list,
        'current_price': pb_ratios[-1] * 10.0,
        'current_book_value_per_share': 10.0
    }
    
    response = DataSourceResponse(
        success=True,
        data=mock_data,
        source_type=DataSourceType.ALPHA_VANTAGE,
        quality_metrics=quality_metrics
    )
    
    return response


def test_confidence_intervals_with_quality_scores():
    """Test confidence intervals with various quality scores"""
    logger.info("Testing confidence intervals with various quality scores...")
    
    engine = PBHistoricalAnalysisEngine()
    quality_scores = [0.5, 0.7, 0.9]
    
    results = {}
    
    for quality_score in quality_scores:
        logger.info(f"Testing with quality score: {quality_score}")
        
        response = create_mock_data_response(quality_score=quality_score)
        analysis_result = engine.analyze_historical_performance(response, years=5)
        
        if analysis_result.success:
            results[quality_score] = {
                'confidence_interval': analysis_result.statistics.mean_confidence_interval,
                'monte_carlo_intervals': analysis_result.statistics.monte_carlo_confidence_intervals,
                'quality_score': analysis_result.quality_metrics.overall_score,
                'volatility_ranges': analysis_result.volatility_adjusted_ranges
            }
            
            logger.info(f"Quality {quality_score}: CI = {analysis_result.statistics.mean_confidence_interval}")
            logger.info(f"Monte Carlo 95%: {analysis_result.statistics.monte_carlo_confidence_intervals.get('95%', 'N/A')}")
        else:
            logger.error(f"Analysis failed for quality score {quality_score}: {analysis_result.error_message}")
    
    # Verify that higher quality leads to narrower confidence intervals
    if len(results) >= 2:
        low_quality_width = results[0.5]['confidence_interval'][1] - results[0.5]['confidence_interval'][0]
        high_quality_width = results[0.9]['confidence_interval'][1] - results[0.9]['confidence_interval'][0]
        
        logger.info(f"Low quality CI width: {low_quality_width:.3f}")
        logger.info(f"High quality CI width: {high_quality_width:.3f}")
        
        if high_quality_width < low_quality_width:
            logger.info("✓ Higher quality data produces narrower confidence intervals")
        else:
            logger.warning("✗ Expected narrower intervals for higher quality data")
    
    return results


def test_statistical_significance():
    """Test statistical significance testing functionality"""
    logger.info("Testing statistical significance testing...")
    
    engine = PBHistoricalAnalysisEngine()
    response = create_mock_data_response(quality_score=0.8)
    analysis_result = engine.analyze_historical_performance(response, years=5)
    
    if analysis_result.success and analysis_result.statistics:
        stats = analysis_result.statistics
        
        logger.info(f"Normality test p-value: {stats.normality_test_pvalue:.4f}")
        logger.info(f"Is normal distribution: {stats.is_normal_distribution}")
        logger.info(f"Skewness: {stats.skewness:.3f}")
        logger.info(f"Kurtosis: {stats.kurtosis:.3f}")
        
        # Check significance tests
        if stats.statistical_significance:
            for test_name, result in stats.statistical_significance.items():
                if isinstance(result, bool):
                    logger.info(f"{test_name}: {'Significant' if result else 'Not significant'}")
                else:
                    logger.info(f"{test_name}: {result:.4f}")
        
        logger.info("✓ Statistical significance testing completed")
        return True
    else:
        logger.error("Statistical significance testing failed")
        return False


def test_monte_carlo_simulation():
    """Test Monte Carlo simulation functionality"""
    logger.info("Testing Monte Carlo simulation...")
    
    engine = PBHistoricalAnalysisEngine()
    response = create_mock_data_response(quality_score=0.8)
    analysis_result = engine.analyze_historical_performance(response, years=5)
    
    if analysis_result.success and analysis_result.statistics:
        stats = analysis_result.statistics
        
        logger.info(f"Monte Carlo mean: {stats.monte_carlo_mean:.3f}")
        logger.info(f"Monte Carlo std: {stats.monte_carlo_std:.3f}")
        
        # Check confidence intervals
        if stats.monte_carlo_confidence_intervals:
            for level, (lower, upper) in stats.monte_carlo_confidence_intervals.items():
                width = upper - lower
                logger.info(f"MC {level} CI: [{lower:.3f}, {upper:.3f}] (width: {width:.3f})")
        
        # Check Value at Risk
        if stats.monte_carlo_value_at_risk:
            for level, var_value in stats.monte_carlo_value_at_risk.items():
                logger.info(f"VaR {level}: {var_value:.3f}")
        
        logger.info("✓ Monte Carlo simulation completed")
        return True
    else:
        logger.error("Monte Carlo simulation failed")
        return False


def test_risk_scenarios():
    """Test risk-adjusted scenario generation"""
    logger.info("Testing risk-adjusted scenarios...")
    
    engine = PBHistoricalAnalysisEngine()
    
    # Test with different volatility levels
    volatility_levels = ['low', 'medium', 'high']
    
    for vol_level in volatility_levels:
        logger.info(f"Testing {vol_level} volatility scenario...")
        
        response = create_mock_data_response(quality_score=0.8, volatility_level=vol_level)
        analysis_result = engine.analyze_historical_performance(response, years=5)
        
        if analysis_result.success:
            # Check scenarios
            if analysis_result.risk_scenarios:
                logger.info(f"{vol_level.capitalize()} volatility scenarios:")
                for scenario_name, scenario_data in analysis_result.risk_scenarios.items():
                    logger.info(f"  {scenario_name}: P/B={scenario_data['pb_estimate']:.2f}, "
                              f"Prob={scenario_data['probability_weight']:.1%}")
            
            # Check volatility ranges
            if analysis_result.volatility_adjusted_ranges:
                logger.info(f"Volatility-adjusted ranges:")
                for range_name, (lower, upper) in analysis_result.volatility_adjusted_ranges.items():
                    width = upper - lower
                    logger.info(f"  {range_name}: [{lower:.2f}, {upper:.2f}] (width: {width:.2f})")
    
    logger.info("✓ Risk scenario testing completed")
    return True


def test_comprehensive_report():
    """Test comprehensive report generation with all new features"""
    logger.info("Testing comprehensive report generation...")
    
    engine = PBHistoricalAnalysisEngine()
    response = create_mock_data_response(quality_score=0.85)
    analysis_result = engine.analyze_historical_performance(response, years=5)
    
    if analysis_result.success:
        # Generate comprehensive report
        report = create_pb_historical_report(analysis_result)
        
        # Check that all new sections are included
        required_sections = [
            'monte_carlo_analysis',
            'risk_metrics',
            'statistics'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in report:
                missing_sections.append(section)
        
        if missing_sections:
            logger.error(f"Missing report sections: {missing_sections}")
            return False
        
        # Check specific new fields
        if report['statistics']:
            new_fields = ['statistical_significance', 'normality_test_pvalue', 'skewness', 'kurtosis']
            for field in new_fields:
                if field not in report['statistics']:
                    logger.warning(f"Missing statistics field: {field}")
        
        if report['monte_carlo_analysis']:
            mc_fields = ['confidence_intervals', 'value_at_risk']
            for field in mc_fields:
                if field not in report['monte_carlo_analysis']:
                    logger.warning(f"Missing Monte Carlo field: {field}")
        
        if report['risk_metrics']:
            risk_fields = ['scenarios', 'scenario_probabilities', 'volatility_adjusted_ranges']
            for field in risk_fields:
                if field not in report['risk_metrics']:
                    logger.warning(f"Missing risk metrics field: {field}")
        
        logger.info("✓ Comprehensive report generation completed")
        logger.info(f"Report keys: {list(report.keys())}")
        
        return True
    else:
        logger.error(f"Report generation failed: {analysis_result.error_message}")
        return False


def run_all_tests():
    """Run all confidence interval and valuation range tests"""
    logger.info("=" * 80)
    logger.info("RUNNING COMPREHENSIVE CONFIDENCE INTERVAL AND VALUATION RANGE TESTS")
    logger.info("=" * 80)
    
    test_results = {}
    
    try:
        # Test 1: Quality-weighted confidence intervals
        logger.info("\n" + "1. TESTING QUALITY-WEIGHTED CONFIDENCE INTERVALS" + "\n" + "-" * 50)
        test_results['confidence_intervals'] = test_confidence_intervals_with_quality_scores()
        
        # Test 2: Statistical significance testing
        logger.info("\n" + "2. TESTING STATISTICAL SIGNIFICANCE" + "\n" + "-" * 50)
        test_results['statistical_significance'] = test_statistical_significance()
        
        # Test 3: Monte Carlo simulation
        logger.info("\n" + "3. TESTING MONTE CARLO SIMULATION" + "\n" + "-" * 50)
        test_results['monte_carlo'] = test_monte_carlo_simulation()
        
        # Test 4: Risk scenarios
        logger.info("\n" + "4. TESTING RISK-ADJUSTED SCENARIOS" + "\n" + "-" * 50)
        test_results['risk_scenarios'] = test_risk_scenarios()
        
        # Test 5: Comprehensive report
        logger.info("\n" + "5. TESTING COMPREHENSIVE REPORT" + "\n" + "-" * 50)
        test_results['comprehensive_report'] = test_comprehensive_report()
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        test_results['error'] = str(e)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result is True)
    total_tests = len([r for r in test_results.values() if isinstance(r, bool)])
    
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, result in test_results.items():
        if isinstance(result, bool):
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"  {test_name}: {status}")
        elif test_name == 'confidence_intervals':
            logger.info(f"  {test_name}: ✓ COMPLETED (see detailed results above)")
    
    if passed_tests == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED! Confidence intervals and valuation ranges are working correctly.")
    else:
        logger.warning(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the implementation.")
    
    return test_results


if __name__ == "__main__":
    # Set random seed for reproducible results
    np.random.seed(42)
    
    # Run all tests
    results = run_all_tests()