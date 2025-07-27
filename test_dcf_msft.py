#!/usr/bin/env python3
"""
Test script to debug MSFT DCF calculation values
"""

import sys
import logging
import os
from pathlib import Path

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add current directory to path
sys.path.append('.')

try:
    from financial_calculations import FinancialCalculator
    from dcf_valuation import DCFValuator

    print("=== TESTING MSFT DCF CALCULATION ===")

    # Create a dummy company folder (DCF calculation uses ticker data anyway)
    test_folder = "data/test_company"
    os.makedirs(test_folder, exist_ok=True)

    # Create minimal CSV files for the calculator
    with open(f"{test_folder}/income_statement.csv", "w") as f:
        f.write("Year,Revenue\n2023,100000\n")
    with open(f"{test_folder}/balance_sheet.csv", "w") as f:
        f.write("Year,Total Assets\n2023,50000\n")
    with open(f"{test_folder}/cash_flow.csv", "w") as f:
        f.write("Year,Operating Cash Flow\n2023,25000\n")

    # Create financial calculator
    calc = FinancialCalculator(test_folder)

    # Load MSFT ticker data - this is where the real data comes from
    success = calc.load_ticker_data('MSFT')
    print(f"Ticker data loaded: {success}")

    if success:
        # Create DCF valuator
        valuator = DCFValuator(calc)

        # Run DCF calculation with debug logging
        print("\n--- Running DCF Calculation ---")
        dcf_results = valuator.calculate_dcf_projections()

        print("\n--- DCF RESULTS ---")
        print(f"Enterprise Value: {dcf_results.get('enterprise_value', 'N/A')}")
        print(f"Equity Value: {dcf_results.get('equity_value', 'N/A')}")
        print(f"Terminal Value: {dcf_results.get('terminal_value', 'N/A')}")
        print(f"Value Per Share: {dcf_results.get('value_per_share', 'N/A')}")
        print(f"FCF Type: {dcf_results.get('fcf_type', 'N/A')}")

        # Check if values are reasonable for Microsoft
        equity_value = dcf_results.get('equity_value', 0)
        if equity_value > 1e12:  # Over 1 trillion
            print(f"✅ Equity value {equity_value/1e12:.2f}T appears reasonable for MSFT")
        elif equity_value > 1e9:  # Over 1 billion
            print(f"⚠️ Equity value {equity_value/1e9:.2f}B seems low for MSFT")
        else:
            print(f"❌ Equity value {equity_value} is definitely wrong for MSFT")

        # Test the CSV export scaling
        from fcf_analysis_streamlit import get_financial_scale_and_unit

        print("\n--- TESTING CSV SCALING ---")
        ev_scaled, ev_unit, ev_abbrev = get_financial_scale_and_unit(
            equity_value, already_in_millions=False
        )
        print(f"Scaled Enterprise Value: {ev_scaled:.3f} {ev_unit}")

    else:
        print("❌ Failed to load MSFT ticker data")

    # Clean up test files
    import shutil

    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
