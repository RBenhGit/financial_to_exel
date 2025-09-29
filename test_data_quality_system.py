#!/usr/bin/env python3
"""
Quick functional test for the Data Quality Metrics System
=======================================================

This script tests the end-to-end functionality of the data quality system
including analyzer, financial calculator integration, and scoring algorithms.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.data_processing.data_quality_analyzer import DataQualityAnalyzer, quick_quality_check, get_quality_warnings
    from core.analysis.engines.financial_calculations import FinancialCalculator
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def test_basic_analyzer():
    """Test basic data quality analyzer functionality"""
    print("\nTesting Basic Data Quality Analyzer...")

    analyzer = DataQualityAnalyzer()

    # Test with sample financial data
    sample_data = {
        'Total Revenue': [100000, 110000, 120000, 130000],
        'Net Income': [10000, 12000, 15000, 18000],
        'Total Assets': [500000, 520000, 550000, 580000],
        'Cash Flow from Operations': [15000, 18000, 22000, 25000]
    }

    # Analyze quality
    indicator = analyzer.analyze_financial_data(sample_data, "Test Data")

    print(f"  Quality Score: {indicator.score:.1f}%")
    print(f"  Quality Level: {indicator.level}")
    print(f"  Message: {indicator.message}")
    print(f"  Details: {list(indicator.details.keys())}")

    assert indicator.score > 0, "Quality score should be greater than 0"
    assert indicator.level in ['high', 'medium', 'low', 'unknown'], "Quality level should be valid"

    print("Basic analyzer test passed")


def test_incomplete_data():
    """Test analyzer with incomplete data"""
    print("\n📊 Testing Incomplete Data Handling...")

    # Create data with missing values
    incomplete_data = {
        'Total Revenue': [100000, None, 120000, None],
        'Net Income': [10000, 12000, None, 18000],
        'Total Assets': [None, None, 550000, 580000]
    }

    score, level = quick_quality_check(incomplete_data, "Incomplete Test Data")

    print(f"  Quality Score: {score:.1f}%")
    print(f"  Quality Level: {level}")

    # Should detect incomplete data
    assert score < 100, "Score should be less than 100% for incomplete data"

    print("✅ Incomplete data test passed")


def test_data_warnings():
    """Test quality warnings system"""
    print("\n⚠️ Testing Quality Warnings...")

    # Create problematic data
    problematic_data = {
        'Total Revenue': [100, 0, 0, 0],  # Many zeros
        'Net Income': [-100000, -200000, -300000, -400000],  # All negative
        'Total Assets': [1e15, 2e15, 3e15, 4e15]  # Unreasonably large numbers
    }

    warnings = get_quality_warnings(problematic_data, "Problematic Data")

    print(f"  Number of warnings: {len(warnings)}")
    for warning in warnings:
        print(f"    {warning}")

    assert len(warnings) > 0, "Should generate warnings for problematic data"

    print("✅ Quality warnings test passed")


def test_financial_calculator_integration():
    """Test integration with FinancialCalculator"""
    print("\n🧮 Testing FinancialCalculator Integration...")

    try:
        # Create calculator without data folder (should still initialize quality components)
        calc = FinancialCalculator(None)

        # Check that quality analyzer is initialized
        assert hasattr(calc, 'quality_analyzer'), "Calculator should have quality_analyzer"
        assert hasattr(calc, 'quality_indicator'), "Calculator should have quality_indicator"

        # Test quality methods
        assert hasattr(calc, 'assess_data_quality'), "Calculator should have assess_data_quality method"
        assert hasattr(calc, 'get_quality_warnings'), "Calculator should have get_quality_warnings method"
        assert hasattr(calc, 'get_data_reliability_score'), "Calculator should have get_data_reliability_score method"

        print("  ✅ Quality analyzer initialized")
        print("  ✅ Quality methods available")

        # Test with mock data
        calc.financial_data = {
            'income_fy': {'Total Revenue': [100000, 110000, 120000]},
            'balance_fy': {'Total Assets': [500000, 520000, 550000]}
        }

        # Test quality assessment
        indicator = calc.assess_data_quality("Test")

        print(f"  Quality Score: {indicator.score:.1f}%")
        print(f"  Quality Level: {indicator.level}")

        # Test reliability score
        reliability = calc.get_data_reliability_score()
        assert reliability >= 0 and reliability <= 100, "Reliability should be 0-100"

        print(f"  Reliability Score: {reliability:.1f}%")

        print("✅ FinancialCalculator integration test passed")

    except Exception as e:
        print(f"❌ FinancialCalculator integration test failed: {e}")
        raise


def test_dashboard_data():
    """Test dashboard data functionality"""
    print("\n📈 Testing Dashboard Data...")

    analyzer = DataQualityAnalyzer()

    # Generate some sample quality data
    sample_data_sets = [
        {'Revenue': [100, 110, 120], 'Assets': [500, 520, 550]},
        {'Revenue': [90, 100, 110], 'Assets': [480, 500, 520]},
        {'Revenue': [110, 120, 130], 'Assets': [520, 540, 560]}
    ]

    # Analyze multiple datasets to build history
    for i, data in enumerate(sample_data_sets):
        analyzer.analyze_financial_data(data, f"Test Dataset {i+1}")

    # Get dashboard data
    dashboard_data = analyzer.get_quality_dashboard_data()

    print(f"  Total analyses: {dashboard_data['total_analyses']}")
    print(f"  Average score: {dashboard_data['average_score']:.1f}%")
    print(f"  Recent scores: {len(dashboard_data['recent_scores'])}")

    assert dashboard_data['total_analyses'] >= 3, "Should have at least 3 analyses"
    assert len(dashboard_data['recent_scores']) >= 3, "Should have recent scores"

    print("✅ Dashboard data test passed")


def main():
    """Run all tests"""
    print("🚀 Starting Data Quality System Tests")
    print("=" * 50)

    try:
        test_basic_analyzer()
        test_incomplete_data()
        test_data_warnings()
        test_financial_calculator_integration()
        test_dashboard_data()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Data Quality Metrics System is working correctly")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()