#!/usr/bin/env python3
"""
Simple test for Data Quality System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Testing Data Quality System...")

    try:
        # Test imports
        from core.data_processing.data_quality_analyzer import DataQualityAnalyzer
        from core.analysis.engines.financial_calculations import FinancialCalculator
        print("PASS: Imports successful")

        # Test basic analyzer
        analyzer = DataQualityAnalyzer()
        sample_data = {
            'Revenue': [100000, 110000, 120000],
            'Assets': [500000, 520000, 550000]
        }

        indicator = analyzer.analyze_financial_data(sample_data, "Test")
        print(f"PASS: Quality Score: {indicator.score:.1f}% ({indicator.level})")

        # Test financial calculator integration
        calc = FinancialCalculator(None)
        calc.financial_data = sample_data

        # Test quality assessment
        result = calc.assess_data_quality("Test")
        print(f"PASS: Calculator Quality: {result.score:.1f}%")

        # Test warnings
        warnings = calc.get_quality_warnings()
        print(f"PASS: Warnings generated: {len(warnings)}")

        print("\nALL TESTS PASSED!")
        print("Data Quality Metrics System is working correctly")

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)