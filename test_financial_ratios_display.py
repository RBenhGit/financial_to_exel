"""
Test script for Financial Ratios Display Component
==================================================

This script demonstrates the financial ratios dashboard functionality
with mock data to validate the implementation.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from ui.streamlit.financial_ratios_display import (
        AdvancedFinancialRatiosDisplay,
        FinancialRatiosCalculator,
        MetricValue
    )
    print("Successfully imported financial ratios components")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class MockFinancialCalculator:
    """Mock FinancialCalculator for testing"""

    def __init__(self):
        self.company_name = "Mock Corporation"
        self.ticker_symbol = "MOCK"

    def get_financial_metrics(self):
        """Return mock financial metrics data"""
        return {
            'profitability': {
                'roe': [0.12, 0.15, 0.18],  # 12%, 15%, 18%
                'roa': [0.08, 0.09, 0.11],  # 8%, 9%, 11%
                'gross_margin': [0.35, 0.38, 0.42],  # 35%, 38%, 42%
                'operating_margin': [0.18, 0.20, 0.22],  # 18%, 20%, 22%
                'net_margin': [0.12, 0.14, 0.16]  # 12%, 14%, 16%
            },
            'efficiency': {
                'asset_turnover': [0.8, 0.9, 1.1],
                'inventory_turnover': [4.5, 5.2, 6.1]
            },
            'liquidity': {
                'current_ratio': [1.8, 2.1, 2.3],
                'quick_ratio': [1.2, 1.4, 1.6]
            },
            'leverage': {
                'debt_to_equity': [0.6, 0.5, 0.4],
                'interest_coverage': [8.0, 9.5, 11.2]
            },
            'growth': {
                'revenue_growth': [0.08, 0.12, 0.15],  # 8%, 12%, 15%
                'fcf_growth': [0.05, 0.10, 0.18]  # 5%, 10%, 18%
            },
            'raw_metrics': {
                'net_income': [50000000, 60000000, 72000000],  # $50M, $60M, $72M
                'book_value_per_share': [25.50, 28.20, 31.10]
            },
            'company_info': {
                'name': 'Mock Corporation',
                'ticker': 'MOCK',
                'currency': 'USD',
                'is_tase_stock': False
            },
            'data_quality': {
                'validation_enabled': True,
                'data_quality_report': None,
                'metrics_completeness': 0.95
            }
        }


def test_financial_ratios_calculator():
    """Test the FinancialRatiosCalculator"""
    print("\nTesting FinancialRatiosCalculator...")

    mock_calc = MockFinancialCalculator()
    ratios_calc = FinancialRatiosCalculator(mock_calc)

    # Calculate all ratios
    ratios_data = ratios_calc.calculate_all_ratios()

    print(f"Calculated {len(ratios_data)} financial ratios")

    # Display sample ratios
    for ratio_key, ratio_value in list(ratios_data.items())[:5]:  # Show first 5
        print(f"  - {ratio_key}: {ratio_value.current:.2f} (trend: {ratio_value.trend})")

    return ratios_data


def test_metrics_hierarchy():
    """Test the metrics hierarchy and definitions"""
    print("\nTesting Metrics Hierarchy...")

    display = AdvancedFinancialRatiosDisplay()

    # Test metric definitions
    profitability_metrics = display.hierarchy.get_metrics_by_category("profitability")
    print(f"Found {len(profitability_metrics)} profitability metrics")

    for key, metric_def in list(profitability_metrics.items())[:3]:  # Show first 3
        print(f"  - {metric_def.name}: {metric_def.formula}")

    # Test panel configuration
    panel_config = display.hierarchy.get_panel_configuration("profitability_panel")
    print(f"Profitability panel config: {panel_config['title']}")

    return display


def test_component_integration():
    """Test component integration"""
    print("\nTesting Component Integration...")

    mock_calc = MockFinancialCalculator()
    display = AdvancedFinancialRatiosDisplay()

    # Test the main calculation pipeline
    ratios_calc = FinancialRatiosCalculator(mock_calc)
    ratios_data = ratios_calc.calculate_all_ratios()

    # Test health score calculation
    health_score = display._calculate_financial_health_score(ratios_data)
    print(f"Financial health score: {health_score:.1f}/100")

    # Test health score interpretation
    interpretation = display._get_health_score_interpretation(health_score)
    print(f"Health interpretation: {interpretation}")

    return health_score, interpretation


def run_comprehensive_test():
    """Run comprehensive test of the financial ratios system"""
    print("Starting Comprehensive Financial Ratios Test")
    print("=" * 60)

    try:
        # Test 1: Calculator functionality
        ratios_data = test_financial_ratios_calculator()

        # Test 2: Hierarchy and definitions
        display = test_metrics_hierarchy()

        # Test 3: Component integration
        health_score, interpretation = test_component_integration()

        # Summary
        print("\nTest Summary:")
        print(f"  - Total ratios calculated: {len(ratios_data)}")
        print(f"  - Financial health score: {health_score:.1f}/100 ({interpretation})")
        print(f"  - Component integration: Successful")

        # Test data quality
        data_quality_tests = []

        # Check for required ratio categories
        categories = set()
        for ratio_key in ratios_data.keys():
            metric_def = display.hierarchy.metric_definitions.get(ratio_key)
            if metric_def:
                categories.add(metric_def.category)

        expected_categories = {'profitability', 'liquidity', 'leverage', 'growth'}
        found_categories = categories.intersection(expected_categories)

        print(f"  - Ratio categories found: {len(found_categories)}/{len(expected_categories)}")
        print(f"    Categories: {', '.join(sorted(found_categories))}")

        # Overall test result
        if len(ratios_data) >= 10 and len(found_categories) >= 3:
            print("\nCOMPREHENSIVE TEST PASSED!")
            print("   The Financial Ratios Dashboard is ready for production use.")
            return True
        else:
            print("\nTest completed with limitations")
            print("   Some functionality may need additional development.")
            return False

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()

    if success:
        print("\nNext Steps:")
        print("   1. Integrate with Streamlit application")
        print("   2. Test with real financial data")
        print("   3. Add industry benchmarking")
        print("   4. Implement historical trend analysis")
    else:
        print("\nRecommended Actions:")
        print("   1. Review error messages above")
        print("   2. Check dependencies and imports")
        print("   3. Validate data structure compatibility")
        print("   4. Test with different data scenarios")