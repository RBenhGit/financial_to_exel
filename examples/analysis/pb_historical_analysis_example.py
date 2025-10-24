"""
P/B Historical Analysis Integration Example
==========================================

This example demonstrates how to use the P/B Historical Analysis Engine
with DataQualityMetrics to analyze historical P/B performance.

Usage:
    python examples/analysis/pb_historical_analysis_example.py

This will demonstrate:
1. Creating historical P/B data
2. Running comprehensive analysis with quality assessment
3. Generating insights and reports
4. Showcasing quality-weighted calculations
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our modules
from core.analysis.pb.pb_historical_analysis import (
    PBHistoricalAnalysisEngine,
    create_pb_historical_report,
    validate_pb_historical_data
)
from core.data_sources.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics
from core.analysis.pb.pb_calculation_engine import PBDataPoint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_realistic_historical_data(ticker: str = "MSFT", years: int = 5) -> DataSourceResponse:
    """
    Create realistic historical P/B data for demonstration.
    
    This simulates data that would come from a real financial data provider.
    """
    logger.info(f"Creating {years} years of historical data for {ticker}")
    
    # Generate realistic historical prices (quarterly)
    base_date = datetime.now() - timedelta(days=365 * years)
    historical_prices = {}
    
    base_price = 100.0
    for i in range(years * 4):  # Quarterly data
        date = base_date + timedelta(days=i * 90)
        date_str = date.strftime('%Y-%m-%d')
        
        # Simulate price movement with trend and seasonality
        trend = 1.02 ** i  # 2% quarterly growth trend
        seasonal = 1.0 + 0.05 * np.sin(i * np.pi / 2)  # Seasonal variation
        noise = np.random.normal(1.0, 0.1)  # Random noise
        
        price = base_price * trend * seasonal * noise
        historical_prices[date_str] = {'4. close': price}
    
    # Generate realistic balance sheet data (quarterly)
    quarterly_balance_sheet = []
    base_equity = 50000000  # $50M initial equity
    base_shares = 1000000   # 1M shares
    
    for i in range(years * 4):
        date = base_date + timedelta(days=i * 90)
        
        # Simulate equity growth
        equity_growth = 1.015 ** i  # 1.5% quarterly equity growth
        equity = base_equity * equity_growth * np.random.normal(1.0, 0.05)
        
        # Simulate small changes in shares outstanding
        shares = base_shares * (1.0 + np.random.normal(0.0, 0.02))
        
        quarterly_balance_sheet.append({
            'fiscalDateEnding': date.strftime('%Y-%m-%d'),
            'totalStockholderEquity': int(equity),
            'commonSharesOutstanding': int(shares)
        })
    
    # Create mock financial data response
    financial_data = {
        'ticker': ticker,
        'historical_prices': historical_prices,
        'quarterly_balance_sheet': quarterly_balance_sheet,
        'current_price': list(historical_prices.values())[-1]['4. close'],
        'last_updated': datetime.now().isoformat()
    }
    
    # Create quality metrics that reflect real-world data quality
    quality_metrics = DataQualityMetrics(
        completeness=0.87,  # Some missing data points
        accuracy=0.91,      # High accuracy from established provider
        timeliness=0.83,    # Reasonably current data
        consistency=0.88    # Good consistency across sources
    )
    quality_metrics.calculate_overall_score()
    
    return DataSourceResponse(
        success=True,
        data=financial_data,
        source_type=DataSourceType.ALPHA_VANTAGE,
        quality_metrics=quality_metrics,
        response_time=1.2,
        api_calls_used=3,
        cost_incurred=0.03
    )


def demonstrate_pb_analysis():
    """Demonstrate comprehensive P/B historical analysis"""
    
    print("=" * 80)
    print("P/B HISTORICAL ANALYSIS DEMONSTRATION")
    print("=" * 80)
    
    # 1. Create sample data
    print("\n1. Creating sample historical data...")
    response = create_realistic_historical_data("MSFT", years=5)
    
    print(f"   * Created {len(response.data['historical_prices'])} price data points")
    print(f"   * Created {len(response.data['quarterly_balance_sheet'])} balance sheet entries")
    print(f"   * Data quality score: {response.quality_metrics.overall_score:.3f}")
    
    # 2. Validate data
    print("\n2. Validating data for P/B analysis...")
    validation = validate_pb_historical_data(response)
    
    if validation['valid']:
        print("   * Data validation passed")
        if validation['recommendations']:
            for rec in validation['recommendations']:
                print(f"   - {rec}")
    else:
        print("   * Data validation failed:")
        for issue in validation['issues']:
            print(f"   - {issue}")
        return
    
    # 3. Run comprehensive analysis
    print("\n3. Running P/B historical analysis...")
    engine = PBHistoricalAnalysisEngine()
    analysis_result = engine.analyze_historical_performance(response, years=5)
    
    if not analysis_result.success:
        print(f"   * Analysis failed: {analysis_result.error_message}")
        return
    
    print(f"   * Analysis completed successfully")
    print(f"   * Processed {analysis_result.data_points_count} data points")
    print(f"   * Overall data quality: {analysis_result.quality_metrics.overall_score:.3f}")
    
    # 4. Display key results
    print("\n4. Analysis Results")
    print("-" * 50)
    
    stats = analysis_result.statistics
    trend = analysis_result.trend_analysis
    quality = analysis_result.quality_metrics
    
    print(f"Ticker: {analysis_result.ticker}")
    print(f"Analysis Period: {analysis_result.analysis_period}")
    print(f"Data Points: {analysis_result.data_points_count}")
    print()
    
    print("Statistical Summary:")
    print(f"  • Mean P/B Ratio: {stats.mean_pb:.2f}")
    print(f"  • Median P/B Ratio: {stats.median_pb:.2f}")
    print(f"  • Standard Deviation: {stats.std_pb:.2f}")
    print(f"  • 25th Percentile: {stats.p25_pb:.2f}")
    print(f"  • 75th Percentile: {stats.p75_pb:.2f}")
    print(f"  • Quality-Weighted Mean: {stats.quality_weighted_mean:.2f}")
    print()
    
    print("Trend Analysis:")
    print(f"  • Trend Direction: {trend.trend_direction.capitalize()}")
    print(f"  • Trend Strength: {trend.trend_strength:.2%}")
    print(f"  • Volatility: {trend.volatility:.2f}")
    print(f"  • Mean Reversion Score: {trend.mean_reversion_score:.2%}")
    print(f"  • Cycles Detected: {trend.cycles_detected}")
    print(f"  • Current Cycle Position: {trend.current_cycle_position.replace('_', ' ').title()}")
    print()
    
    print("Quality Assessment:")
    print(f"  • Overall Quality Score: {quality.overall_score:.1%}")
    print(f"  • P/B Data Completeness: {quality.pb_data_completeness:.1%}")
    print(f"  • Price Data Quality: {quality.price_data_quality:.1%}")
    print(f"  • Balance Sheet Quality: {quality.balance_sheet_quality:.1%}")
    print(f"  • Temporal Consistency: {quality.temporal_consistency:.1%}")
    print(f"  • Outlier Detection Score: {quality.outlier_detection_score:.1%}")
    print()
    
    print("Valuation Insights:")
    print(f"  • Current P/B Percentile: {analysis_result.current_pb_percentile:.1%}")
    print(f"  • Fair Value Estimate: {analysis_result.fair_value_estimate:.2f}")
    print(f"  • Valuation Signal: {analysis_result.valuation_signal.replace('_', ' ').title()}")
    print()
    
    # 5. Display quality warnings and notes
    if analysis_result.quality_warnings:
        print("Quality Warnings:")
        for warning in analysis_result.quality_warnings:
            print(f"  ⚠ {warning}")
        print()
    
    if analysis_result.analysis_notes:
        print("Analysis Notes:")
        for note in analysis_result.analysis_notes:
            print(f"  • {note}")
        print()
    
    # 6. Generate comprehensive report
    print("\n5. Generating comprehensive report...")
    report = create_pb_historical_report(analysis_result)
    
    print("   * Report generated successfully")
    
    # Display report summary
    print("\n6. Report Summary")
    print("-" * 50)
    print(f"Success: {report['success']}")
    print(f"Ticker: {report['ticker']}")
    print(f"Analysis Period: {report['analysis_period']}")
    print(f"Data Points: {report['data_points_count']}")
    
    if 'summary' in report:
        summary = report['summary']
        print(f"Current P/B Percentile: {summary['current_pb_percentile']:.1%}")
        print(f"Fair Value: {summary['fair_value_estimate']:.2f}")
        print(f"Signal: {summary['valuation_signal']}")
    
    # 7. Demonstrate quality impact
    print("\n7. Quality Impact Analysis")
    print("-" * 50)
    
    regular_mean = stats.mean_pb
    quality_weighted_mean = stats.quality_weighted_mean
    difference = abs(quality_weighted_mean - regular_mean)
    
    print(f"Regular Mean P/B: {regular_mean:.3f}")
    print(f"Quality-Weighted Mean P/B: {quality_weighted_mean:.3f}")
    print(f"Quality Impact: {difference:.3f} ({difference/regular_mean:.1%})")
    
    if difference > 0.05:  # 5% threshold
        print("   → Significant quality impact detected")
        print("   → Quality weighting provides more reliable estimate")
    else:
        print("   → Quality impact is minimal")
        print("   → Data quality is consistently good across time periods")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


def demonstrate_different_quality_scenarios():
    """Demonstrate how different data quality affects analysis"""
    
    print("\n" + "=" * 80)
    print("DATA QUALITY IMPACT DEMONSTRATION")
    print("=" * 80)
    
    engine = PBHistoricalAnalysisEngine()
    
    scenarios = [
        ("High Quality Data", 0.95),
        ("Medium Quality Data", 0.75),
        ("Low Quality Data", 0.45)
    ]
    
    for scenario_name, base_quality in scenarios:
        print(f"\n{scenario_name} (Base Quality: {base_quality:.1%}):")
        print("-" * 50)
        
        # Create response with different quality level
        response = create_realistic_historical_data("TEST", years=3)
        
        # Adjust quality metrics
        response.quality_metrics.completeness = base_quality + np.random.normal(0, 0.05)
        response.quality_metrics.accuracy = base_quality + np.random.normal(0, 0.03)
        response.quality_metrics.timeliness = base_quality + np.random.normal(0, 0.08)
        response.quality_metrics.consistency = base_quality + np.random.normal(0, 0.04)
        
        # Ensure values stay in bounds
        for attr in ['completeness', 'accuracy', 'timeliness', 'consistency']:
            value = getattr(response.quality_metrics, attr)
            setattr(response.quality_metrics, attr, max(0.0, min(1.0, value)))
        
        response.quality_metrics.calculate_overall_score()
        
        # Run analysis
        result = engine.analyze_historical_performance(response, years=3)
        
        if result.success:
            print(f"Overall Quality Score: {result.quality_metrics.overall_score:.3f}")
            print(f"Confidence Interval Width: {result.quality_metrics.confidence_interval_width:.3f}")
            print(f"Quality Warnings: {len(result.quality_warnings)}")
            print(f"Valuation Signal: {result.valuation_signal}")
            
            if result.quality_warnings:
                print("Key Warnings:")
                for warning in result.quality_warnings[:2]:  # Show first 2
                    print(f"  • {warning}")
        else:
            print(f"Analysis failed: {result.error_message}")
    
    print("\nKey Insights:")
    print("• Higher quality data produces narrower confidence intervals")
    print("• Low quality data triggers more warnings and uncertainty")
    print("• Quality weighting helps maintain reliability even with mixed data")


if __name__ == "__main__":
    # Run comprehensive demonstration
    try:
        demonstrate_pb_analysis()
        demonstrate_different_quality_scenarios()
        
        print("\n" + "=" * 80)
        print("🎉 P/B HISTORICAL ANALYSIS DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("\nKey Features Demonstrated:")
        print("✓ Historical P/B data processing with quality assessment")
        print("✓ P/B-specific completeness and consistency checks")
        print("✓ Trend analysis and statistical calculations")
        print("✓ Quality-weighted confidence calculations")
        print("✓ Rolling statistics and volatility metrics")
        print("✓ Comprehensive reporting and validation")
        print("\nThe P/B Historical Analysis Engine is ready for production use!")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise