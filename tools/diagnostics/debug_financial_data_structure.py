#!/usr/bin/env python3

"""
Debug script to examine the structure of the financial data for GOOG
to understand where the Period End Date information is stored.
"""

import sys
import pandas as pd
from core.analysis.engines.financial_calculations import FinancialCalculator

def debug_financial_data_structure():
    """Debug the structure of financial data."""
    
    print("=" * 60)
    print("DEBUGGING FINANCIAL DATA STRUCTURE FOR GOOG")
    print("=" * 60)
    
    # Create calculator for GOOG
    calculator = FinancialCalculator("GOOG")
    
    if hasattr(calculator, 'financial_data') and isinstance(calculator.financial_data, pd.DataFrame):
        print(f"Financial data type: {type(calculator.financial_data)}")
        print(f"Financial data shape: {calculator.financial_data.shape}")
        print()
        
        print("Index (rows):")
        for i, idx in enumerate(calculator.financial_data.index):
            print(f"  {i}: '{idx}' (type: {type(idx)})")
            if i > 20:  # Limit output
                print(f"  ... and {len(calculator.financial_data.index) - i - 1} more")
                break
        print()
        
        print("Columns:")
        for i, col in enumerate(calculator.financial_data.columns):
            print(f"  {i}: '{col}' (type: {type(col)})")
            if i > 20:  # Limit output
                print(f"  ... and {len(calculator.financial_data.columns) - i - 1} more")
                break
        print()
        
        # Look for date-related entries
        print("Looking for date-related entries in index:")
        date_related_index = []
        for idx in calculator.financial_data.index:
            idx_str = str(idx).lower()
            if any(keyword in idx_str for keyword in ['date', 'period', 'end', 'report']):
                date_related_index.append(idx)
        
        if date_related_index:
            print("Found date-related entries in index:")
            for entry in date_related_index:
                print(f"  '{entry}'")
                # Show the data for this row
                row_data = calculator.financial_data.loc[entry]
                print(f"    Data: {row_data.values}")
        else:
            print("No obvious date-related entries found in index.")
        print()
        
        print("Looking for date-related entries in columns:")
        date_related_cols = []
        for col in calculator.financial_data.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['date', 'period', 'end', 'report']):
                date_related_cols.append(col)
        
        if date_related_cols:
            print("Found date-related entries in columns:")
            for entry in date_related_cols:
                print(f"  '{entry}'")
                # Show the data for this column
                col_data = calculator.financial_data[entry]
                print(f"    Data: {col_data.values}")
        else:
            print("No obvious date-related entries found in columns.")
        print()
        
        # Show a sample of the data
        print("Sample of financial data (first 5 rows, first 5 columns):")
        print(calculator.financial_data.iloc[:5, :5])
        print()
        
        # Try the date extraction method
        print("Testing date extraction method:")
        dates = calculator._extract_excel_dates()
        print(f"Extracted dates: {dates}")
        
    else:
        print("No financial data found or data is not a DataFrame")
        print(f"Type: {type(calculator.financial_data)}")
        if hasattr(calculator, 'financial_data'):
            print(f"Value: {calculator.financial_data}")

if __name__ == "__main__":
    debug_financial_data_structure()