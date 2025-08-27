#!/usr/bin/env python3
"""
Test script to verify data ordering fix
"""
import sys
import os
import pytest

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_ordering():
    """Test that FCF data is returned in correct chronological order."""
    try:
        from core.analysis.engines.financial_calculations import FinancialCalculator
        from core.data_processing.processors.data_processing import DataProcessor
        import pandas as pd
        import numpy as np

        print("Testing data ordering fix...")

        # Test with first available company data
        companies = []
        for item in os.listdir("."):
            if os.path.isdir(item) and not item.startswith('.') and not item.startswith('_'):
                fy_path = os.path.join(item, 'FY')
                if os.path.exists(fy_path):
                    companies.append(item)

        if not companies:
            pytest.skip("No companies found in dataset")

        company = sorted(companies)[0]
        company_folder = os.path.abspath(company)
        print(f"Testing with {company} data from: {company_folder}")

        # Initialize calculator
        calc = FinancialCalculator(company_folder)

        # Get FCF calculations
        print("Calculating FCF data...")
        fcf_results = calc.calculate_all_fcf_types()

        assert fcf_results, "FCF results should not be empty"
        
        print("\nFCF Results:")
        for fcf_type, values in fcf_results.items():
            print(f"{fcf_type}: {values}")

        # Test data processor
        processor = DataProcessor()
        processed_data = processor.prepare_fcf_data(fcf_results)

        print("\nProcessed Data:")
        print(processed_data)

        # Check if LFCF data is in correct chronological order
        if 'LFCF' in processed_data.get('all_fcf_data', {}):
            lfcf_data = processed_data['all_fcf_data']['LFCF']
            years = lfcf_data.get('years', [])
            values = lfcf_data.get('values', [])

            print(f"\nLFCF Chronological Order Test:")
            print(f"Years: {years}")
            print(f"Values: {values}")

            # Test that years are in ascending chronological order
            if len(years) > 1:
                years_sorted = sorted(years)
                assert years == years_sorted, f"Years should be in chronological order. Expected: {years_sorted}, Got: {years}"
                print("✅ SUCCESS: Years are in correct chronological order (ascending)!")
            else:
                print("✅ SUCCESS: Single year data point (no ordering needed)")
        else:
            pytest.fail("LFCF data not found in processed results")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"Test failed with exception: {e}")
