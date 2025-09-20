#!/usr/bin/env python3
"""
Debug script to examine the actual structure of MSFT Excel data
and understand why property extraction is not working.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.analysis.engines.financial_calculations import FinancialCalculator

def debug_msft_data():
    """Debug MSFT data structure to understand field names"""

    print("Loading MSFT data...")
    msft_folder = "C:\\AsusWebStorage\\ran@benhur.co\\MySyncFolder\\python\\investingAnalysis\\financial_to_exel\\data\\companies\\MSFT"

    calculator = FinancialCalculator(msft_folder)

    print("\n=== Financial Data Structure ===")
    for key, df in calculator.financial_data.items():
        print(f"\n{key.upper()}:")
        if df is not None and not df.empty:
            print(f"  Shape: {df.shape}")
            print(f"  Index (first 10): {list(df.index[:10])}")
            print(f"  Columns: {list(df.columns)}")
            if len(df.index) > 0:
                print(f"  Sample row data: {df.iloc[0].values[:3] if len(df.columns) >= 3 else df.iloc[0].values}")
        else:
            print("  DataFrame is empty or None")

    print("\n=== Property Testing ===")
    properties_to_test = [
        'total_revenue', 'net_income', 'operating_income', 'gross_profit',
        'total_assets', 'current_assets', 'shareholders_equity',
        'operating_cash_flow', 'free_cash_flow', 'capital_expenditures'
    ]

    for prop in properties_to_test:
        try:
            value = getattr(calculator, prop)
            print(f"{prop}: {value}")
        except Exception as e:
            print(f"{prop}: ERROR - {e}")

    print("\n=== Manual Data Search ===")
    # Let's manually search for revenue-like fields in all columns
    for key, df in calculator.financial_data.items():
        if df is not None and not df.empty and 'income' in key.lower():
            print(f"\nSearching {key} DataFrame structure:")
            print(f"  Shape: {df.shape}")
            print(f"  First few rows:")
            for i in range(min(10, len(df))):
                row_data = []
                for j in range(min(5, len(df.columns))):
                    try:
                        val = df.iloc[i, j]
                        if val is not None and str(val).strip():
                            row_data.append(f"Col{j}: {val}")
                    except:
                        pass
                if row_data:
                    print(f"    Row {i}: {', '.join(row_data)}")

            # Look for revenue-like terms in all columns
            print(f"  Searching for financial line items:")
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    try:
                        val = str(df.iloc[i, j]).strip()
                        if val and any(term.lower() in val.lower() for term in ['revenue', 'total revenue', 'sales', 'net income', 'operating income']):
                            print(f"    Found at Row {i}, Col {j}: '{val}'")
                            # Show the corresponding data values
                            if j < len(df.columns) - 1:
                                data_vals = []
                                for k in range(j+1, min(j+4, len(df.columns))):
                                    try:
                                        data_val = df.iloc[i, k]
                                        if data_val is not None and str(data_val).strip():
                                            data_vals.append(str(data_val))
                                    except:
                                        pass
                                if data_vals:
                                    print(f"      Data values: {', '.join(data_vals)}")
                    except:
                        pass

if __name__ == "__main__":
    debug_msft_data()