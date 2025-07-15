#!/usr/bin/env python3
"""
Test script to verify data ordering fix
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from financial_calculations import FinancialCalculator
    from data_processing import DataProcessor
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
        print("❌ No companies found in dataset")
        return
    
    company = sorted(companies)[0]
    company_folder = os.path.abspath(company)
    print(f"Testing with {company} data from: {company_folder}")
    
    # Initialize calculator
    calc = FinancialCalculator(company_folder)
    
    # Get FCF calculations
    print("Calculating FCF data...")
    fcf_results = calc.calculate_all_fcf_types()
    
    if fcf_results:
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
                if years == years_sorted:
                    print("✅ SUCCESS: Years are in correct chronological order (ascending)!")
                else:
                    print("❌ FAIL: Years are not in chronological order")
                    print(f"Expected: {years_sorted}")
                    print(f"Got: {years}")
            else:
                print("✅ SUCCESS: Single year data point (no ordering needed)")
        else:
            print("❌ FAIL: LFCF data not found in processed results")
    else:
        print("❌ FAIL: No FCF results calculated")
        
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()