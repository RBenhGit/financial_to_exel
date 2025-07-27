#!/usr/bin/env python3
"""
Test script to verify removal of hardcoded metadata and company-specific information.
This script validates that configurable values are being used instead of hardcoded strings.
"""

import sys
import os

sys.path.append('.')

from config import (
    get_default_company_name,
    get_unknown_company_name,
    get_unknown_ticker,
    get_unknown_fcf_type,
    get_test_company_name,
    get_test_company_ticker,
)
from data_processing import DataProcessor
from financial_calculations import FinancialCalculator
import tempfile


def test_config_values():
    """Test that configuration values are properly loaded"""
    print("Testing configuration values...")

    # Test all config values are accessible and non-empty
    config_tests = {
        'Default company name': get_default_company_name(),
        'Unknown company name': get_unknown_company_name(),
        'Unknown ticker': get_unknown_ticker(),
        'Unknown FCF type': get_unknown_fcf_type(),
        'Test company name': get_test_company_name(),
        'Test company ticker': get_test_company_ticker(),
    }

    for key, value in config_tests.items():
        assert value is not None and value != '', f"{key} should not be None or empty"
        assert isinstance(value, str), f"{key} should be a string"
        print(f"  SUCCESS: {key} = '{value}'")

    print("All configuration values properly loaded!\n")


def test_data_processor_no_hardcoded():
    """Test that DataProcessor uses configurable values"""
    print("Testing DataProcessor for hardcoded value removal...")

    processor = DataProcessor()

    # Test with None company name (should use config default)
    mock_fcf_results = {'fcf_data': {'years': [2020, 2021], 'FCFF': [100, 120], 'FCFE': [80, 100]}}

    # These should not fail and should use configured defaults
    try:
        fig1 = processor.create_fcf_comparison_plot(mock_fcf_results, company_name=None)
        fig2 = processor.create_average_fcf_plot(mock_fcf_results, company_name=None)
        fig3 = processor.create_slope_analysis_plot(mock_fcf_results, company_name=None)

        # Check titles contain configured company name, not hardcoded "Company"
        configured_name = get_default_company_name()
        assert (
            configured_name in fig1.layout.title.text
        ), f"Plot should use configured name '{configured_name}'"

        print("  SUCCESS: DataProcessor uses configured values instead of hardcoded strings")

    except Exception as e:
        print(f"  ERROR: DataProcessor test failed: {e}")
        return False

    print("DataProcessor hardcoded value removal verified!\n")
    return True


def test_financial_calculator_no_hardcoded():
    """Test that FinancialCalculator uses configurable values"""
    print("Testing FinancialCalculator for hardcoded value removal...")

    # Test with None/empty company folder (should use config default)
    try:
        calc = FinancialCalculator(None)
        configured_unknown = get_unknown_company_name()

        assert (
            calc.company_name == configured_unknown
        ), f"Should use configured unknown name '{configured_unknown}', got '{calc.company_name}'"
        assert calc.company_name != "Unknown", "Should not use hardcoded 'Unknown'"

        print(f"  SUCCESS: FinancialCalculator uses configured unknown name '{calc.company_name}'")

    except Exception as e:
        print(f"  ERROR: FinancialCalculator test failed: {e}")
        return False

    print("FinancialCalculator hardcoded value removal verified!\n")
    return True


def test_no_hardcoded_strings_in_code():
    """Test that no hardcoded company strings remain in key files"""
    print("Checking for remaining hardcoded strings...")

    # Files to check for hardcoded values
    files_to_check = [
        'fcf_analysis_streamlit.py',
        'data_processing.py',
        'financial_calculations.py',
        'test_report_generator.py',
    ]

    hardcoded_patterns = [
        '"Unknown"',  # Should be get_unknown_company_name()
        '"Company"',  # Should be get_default_company_name()
        '"Test Company"',  # Should be get_test_company_name()
        '"TEST"',  # Should be get_test_company_ticker()
    ]

    issues_found = []

    for filename in files_to_check:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in hardcoded_patterns:
                    if (
                        pattern in content
                        and 'get_'
                        not in content[max(0, content.find(pattern) - 50) : content.find(pattern)]
                    ):
                        issues_found.append(f"Found {pattern} in {filename}")

    if issues_found:
        print("  WARNING: Some hardcoded patterns still found:")
        for issue in issues_found:
            print(f"    - {issue}")
    else:
        print("  SUCCESS: No problematic hardcoded strings found")

    print("Hardcoded string check completed!\n")
    return len(issues_found) == 0


def main():
    """Run all tests to verify hardcoded value removal"""
    print("=== Testing Hardcoded Metadata Removal ===\n")

    tests_passed = 0
    total_tests = 4

    # Test 1: Configuration values
    try:
        test_config_values()
        tests_passed += 1
    except Exception as e:
        print(f"Configuration test failed: {e}\n")

    # Test 2: DataProcessor
    if test_data_processor_no_hardcoded():
        tests_passed += 1

    # Test 3: FinancialCalculator
    if test_financial_calculator_no_hardcoded():
        tests_passed += 1

    # Test 4: Code scanning
    if test_no_hardcoded_strings_in_code():
        tests_passed += 1

    print("=== Test Results ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("SUCCESS: All hardcoded metadata removal tests passed!")
        return True
    else:
        print("WARNING: Some tests failed. Review hardcoded value removal.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
