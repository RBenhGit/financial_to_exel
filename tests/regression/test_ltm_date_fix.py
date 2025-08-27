#!/usr/bin/env python3
"""
Test script to verify that the actual LTM date used in calculations is correctly captured.
"""

import os
import sys
from pathlib import Path
from core.analysis.engines.financial_calculations import FinancialCalculator

def test_ltm_date_capture():
    """Test that the actual LTM date is captured from calculations"""
    
    # Use GOOG as test company (has both FY and LTM data)
    test_folder = "GOOG"
    print(f"\nTesting with folder: {test_folder}")
    
    try:
        # Initialize calculator
        calculator = FinancialCalculator(test_folder)
        print(f"Calculator initialized for: {calculator.company_name}")
        
        # Check initial state
        print(f"Initial actual_ltm_date_used: {calculator.actual_ltm_date_used}")
        
        # Load financial data
        calculator.load_financial_statements()
        print(f"Financial data loaded. Available keys: {list(calculator.financial_data.keys())}")
        
        # Calculate FCF to trigger the LTM date capture
        print("\nCalculating Levered FCF to trigger LTM date capture...")
        fcf_results = calculator.calculate_levered_fcf()
        print(f"FCF calculated: {len(fcf_results)} data points")
        
        # Check if LTM date was captured
        print(f"Actual LTM date used after calculation: {calculator.actual_ltm_date_used}")
        
        if calculator.actual_ltm_date_used:
            print("✅ SUCCESS: LTM date capture is working!")
        else:
            print("❌ WARNING: No LTM date was captured. This might be normal if no LTM data is available.")
        
        # Show some sample LTM data if available
        if 'cashflow_ltm' in calculator.financial_data and not calculator.financial_data['cashflow_ltm'].empty:
            ltm_df = calculator.financial_data['cashflow_ltm']
            print(f"LTM cashflow data shape: {ltm_df.shape}")
            print(f"LTM cashflow index type: {type(ltm_df.index)}")
            print(f"LTM cashflow index: {ltm_df.index.tolist()}")
            if hasattr(ltm_df, 'index') and len(ltm_df.index) > 0:
                print(f"Last LTM index: {ltm_df.index[-1]}")
                print(f"Last LTM index type: {type(ltm_df.index[-1])}")
                
                # Test date parsing logic
                try:
                    import pandas as pd
                    if isinstance(ltm_df.index, pd.DatetimeIndex):
                        print("Index is already DatetimeIndex")
                        ltm_date_used = ltm_df.index[-1].strftime("%Y-%m-%d")
                    else:
                        print("Index is not DatetimeIndex, trying to parse...")
                        try:
                            parsed_date = pd.to_datetime(ltm_df.index[-1])
                            ltm_date_used = parsed_date.strftime("%Y-%m-%d")
                            print(f"Parsed date: {ltm_date_used}")
                        except Exception as e:
                            print(f"Failed to parse date: {e}")
                            ltm_date_used = str(ltm_df.index[-1])
                            print(f"Using string representation: {ltm_date_used}")
                except Exception as e:
                    print(f"Error in date parsing test: {e}")
        else:
            print("No LTM cashflow data available")
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ltm_date_capture()