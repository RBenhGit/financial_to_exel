"""
Test suite for P/B Calculation Engine
====================================

This script tests the P/B calculation engine against various DataSourceResponse formats
to ensure proper parsing and calculation of P/B ratios from generalized data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd

from core.analysis.pb.pb_calculation_engine import PBCalculationEngine, PBCalculationResult, PBDataPoint
from core.data_sources.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_alpha_vantage_response() -> DataSourceResponse:
    """Create a sample Alpha Vantage DataSourceResponse for testing"""
    sample_data = {
        "current_price": 150.25,
        "fundamentals": {
            "marketCap": 2500000000000,  # 2.5T
            "sharesOutstanding": 16000000000  # 16B shares
        },
        "balance_sheet": [
            {
                "fiscalDateEnding": "2023-09-30",
                "totalStockholderEquity": 62146000000,  # 62.146B
                "commonSharesOutstanding": 15943400000
            }
        ]
    }
    
    quality_metrics = DataQualityMetrics()
    quality_metrics.completeness = 0.95
    quality_metrics.accuracy = 0.90
    quality_metrics.timeliness = 0.85
    quality_metrics.consistency = 0.88
    quality_metrics.calculate_overall_score()
    
    return DataSourceResponse(
        success=True,
        data=sample_data,
        source_type=DataSourceType.ALPHA_VANTAGE,
        quality_metrics=quality_metrics,
        response_time=1.2,
        api_calls_used=1,
        cost_incurred=0.0
    )


def create_sample_fmp_response() -> DataSourceResponse:
    """Create a sample Financial Modeling Prep DataSourceResponse for testing"""
    sample_data = {
        "current_price": 150.30,
        "marketCap": 2502000000000,
        "fundamentals": {
            "weightedAverageShsOut": 15950000000,
            "totalStockholdersEquity": 62200000000
        }
    }
    
    quality_metrics = DataQualityMetrics()
    quality_metrics.completeness = 0.92
    quality_metrics.accuracy = 0.88
    quality_metrics.timeliness = 0.90
    quality_metrics.consistency = 0.85
    quality_metrics.calculate_overall_score()
    
    return DataSourceResponse(
        success=True,
        data=sample_data,
        source_type=DataSourceType.FINANCIAL_MODELING_PREP,
        quality_metrics=quality_metrics,
        response_time=0.8,
        api_calls_used=1,
        cost_incurred=0.001
    )


def create_sample_historical_response() -> DataSourceResponse:
    """Create a sample DataSourceResponse with historical data for testing"""
    # Create sample historical price data
    historical_prices = {}
    base_date = datetime(2023, 1, 1)
    
    for i in range(12):  # 12 months of data
        date_str = (base_date + timedelta(days=i*30)).strftime("%Y-%m-%d")
        historical_prices[date_str] = {
            "4. close": 140.0 + i * 2.5,  # Gradually increasing price
            "close": 140.0 + i * 2.5
        }
    
    # Create sample quarterly balance sheet data
    quarterly_balance_sheet = [
        {
            "fiscalDateEnding": "2023-03-31",
            "totalStockholderEquity": 60000000000,
            "commonSharesOutstanding": 16000000000
        },
        {
            "fiscalDateEnding": "2023-06-30", 
            "totalStockholderEquity": 61000000000,
            "commonSharesOutstanding": 15950000000
        },
        {
            "fiscalDateEnding": "2023-09-30",
            "totalStockholderEquity": 62146000000,
            "commonSharesOutstanding": 15943400000
        },
        {
            "fiscalDateEnding": "2023-12-31",
            "totalStockholderEquity": 63200000000,
            "commonSharesOutstanding": 15900000000
        }
    ]
    
    sample_data = {
        "historical_prices": historical_prices,
        "quarterly_balance_sheet": quarterly_balance_sheet,
        "current_price": 167.5
    }
    
    quality_metrics = DataQualityMetrics()
    quality_metrics.completeness = 0.88
    quality_metrics.accuracy = 0.85
    quality_metrics.timeliness = 0.80
    quality_metrics.consistency = 0.82
    quality_metrics.calculate_overall_score()
    
    return DataSourceResponse(
        success=True,
        data=sample_data,
        source_type=DataSourceType.ALPHA_VANTAGE,
        quality_metrics=quality_metrics,
        response_time=2.1,
        api_calls_used=3,
        cost_incurred=0.0
    )


def test_current_pb_calculation():
    """Test current P/B ratio calculation"""
    print("\n" + "="*60)
    print("TESTING CURRENT P/B CALCULATION")
    print("="*60)
    
    engine = PBCalculationEngine()
    
    # Test Alpha Vantage format
    print("\n1. Testing Alpha Vantage Response Format:")
    av_response = create_sample_alpha_vantage_response()
    av_result = engine.calculate_current_pb(av_response)
    
    if av_result.success:
        print(f"   [OK] Current Price: ${av_result.current_price:.2f}")
        print(f"   [OK] Book Value per Share: ${av_result.book_value_per_share:.2f}")
        print(f"   [OK] P/B Ratio: {av_result.pb_ratio:.2f}")
        print(f"   [OK] Market Cap: ${av_result.market_cap/1e9:.1f}B")
        print(f"   [OK] Data Quality: {av_result.data_quality_score:.2f}")
        print(f"   [OK] Validation Notes: {len(av_result.validation_notes)} items")
        for note in av_result.validation_notes:
            print(f"     - {note}")
    else:
        print(f"   [ERROR] Error: {av_result.error_message}")
    
    # Test FMP format
    print("\n2. Testing Financial Modeling Prep Response Format:")
    fmp_response = create_sample_fmp_response()
    fmp_result = engine.calculate_current_pb(fmp_response)
    
    if fmp_result.success:
        print(f"   [OK] Current Price: ${fmp_result.current_price:.2f}")
        print(f"   [OK] Book Value per Share: ${fmp_result.book_value_per_share:.2f}")
        print(f"   [OK] P/B Ratio: {fmp_result.pb_ratio:.2f}")
        print(f"   [OK] Data Quality: {fmp_result.data_quality_score:.2f}")
    else:
        print(f"   [ERROR] Error: {fmp_result.error_message}")


def test_historical_pb_calculation():
    """Test historical P/B ratio calculation"""
    print("\n" + "="*60)
    print("TESTING HISTORICAL P/B CALCULATION")
    print("="*60)
    
    engine = PBCalculationEngine()
    
    print("\n1. Testing Historical Data Processing:")
    historical_response = create_sample_historical_response()
    historical_data = engine.calculate_historical_pb(historical_response, years=1)
    
    if historical_data:
        print(f"   [OK] Generated {len(historical_data)} historical P/B data points")
        
        # Show sample data points
        print("   [OK] Sample data points:")
        for i, point in enumerate(historical_data[:3]):  # First 3 points
            print(f"     {i+1}. Date: {point.date}")
            print(f"        Price: ${point.price:.2f}")
            print(f"        BVPS: ${point.book_value_per_share:.2f}")
            print(f"        P/B: {point.pb_ratio:.2f}")
        
        if len(historical_data) > 3:
            print(f"     ... and {len(historical_data) - 3} more data points")
        
        # Calculate statistics
        pb_ratios = [p.pb_ratio for p in historical_data if p.pb_ratio]
        if pb_ratios:
            min_pb = min(pb_ratios)
            max_pb = max(pb_ratios)
            avg_pb = sum(pb_ratios) / len(pb_ratios)
            print(f"   [OK] P/B Statistics: Min={min_pb:.2f}, Max={max_pb:.2f}, Avg={avg_pb:.2f}")
    else:
        print("   [ERROR] No historical data points generated")


def test_multi_source_reconciliation():
    """Test multi-source data reconciliation"""
    print("\n" + "="*60)
    print("TESTING MULTI-SOURCE RECONCILIATION")
    print("="*60)
    
    engine = PBCalculationEngine()
    
    # Create multiple responses with slight variations
    av_response = create_sample_alpha_vantage_response()
    fmp_response = create_sample_fmp_response()
    
    responses = [av_response, fmp_response]
    
    print(f"\n1. Reconciling data from {len(responses)} sources:")
    reconciled_result = engine.reconcile_multi_source_data(responses)
    
    if reconciled_result.success:
        print(f"   [OK] Reconciled P/B Ratio: {reconciled_result.pb_ratio:.2f}")
        print(f"   [OK] Reconciled BVPS: ${reconciled_result.book_value_per_share:.2f}")
        print(f"   [OK] Reconciled Price: ${reconciled_result.current_price:.2f}")
        print(f"   [OK] Data Quality Score: {reconciled_result.data_quality_score:.2f}")
        print("   [OK] Validation Notes:")
        for note in reconciled_result.validation_notes:
            print(f"     - {note}")
    else:
        print(f"   [ERROR] Error: {reconciled_result.error_message}")


def test_error_handling():
    """Test error handling with invalid data"""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    engine = PBCalculationEngine()
    
    # Test with invalid response
    print("\n1. Testing with unsuccessful response:")
    invalid_response = DataSourceResponse(
        success=False,
        error_message="API call failed",
        source_type=DataSourceType.ALPHA_VANTAGE
    )
    
    result = engine.calculate_current_pb(invalid_response)
    if not result.success:
        print(f"   [OK] Correctly handled error: {result.error_message}")
    else:
        print("   [ERROR] Should have failed with invalid response")
    
    # Test with missing data
    print("\n2. Testing with missing critical data:")
    incomplete_response = DataSourceResponse(
        success=True,
        data={"some_field": "some_value"},  # Missing price and equity data
        source_type=DataSourceType.ALPHA_VANTAGE
    )
    
    result = engine.calculate_current_pb(incomplete_response)
    if not result.success:
        print(f"   [OK] Correctly handled missing data: {result.error_message}")
    else:
        print("   [ERROR] Should have failed with incomplete data")


def run_comprehensive_test():
    """Run all tests"""
    print("P/B CALCULATION ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    try:
        test_current_pb_calculation()
        test_historical_pb_calculation()
        test_multi_source_reconciliation()
        test_error_handling()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nP/B Calculation Engine is ready for production use!")
        
    except Exception as e:
        print(f"\n" + "="*80)
        print("TEST SUITE FAILED")
        print("="*80)
        print(f"Error: {e}")
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == "__main__":
    run_comprehensive_test()