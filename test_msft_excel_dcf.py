#!/usr/bin/env python3
"""
Test MSFT DCF calculation using existing Excel files to isolate the bug
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

    print("=== TESTING MSFT DCF WITH EXCEL DATA ===")

    # Use the existing MSFT folder
    msft_folder = "MSFT"

    if not os.path.exists(msft_folder):
        print(f"❌ MSFT folder not found: {msft_folder}")
        sys.exit(1)

    # Create financial calculator with MSFT Excel data
    print("1. Loading MSFT Excel data...")
    calc = FinancialCalculator(msft_folder)

    print("PASS: Calculator created")
    print(f"  Company: {calc.company_name}")
    print(f"  Ticker: {getattr(calc, 'ticker_symbol', 'N/A')}")

    # Load FCF results
    print("\n2. Calculating FCF...")
    fcf_results = calc.calculate_all_fcf_types()

    if fcf_results and any(values for values in fcf_results.values()):
        print("PASS: FCF calculation successful")
        for fcf_type, values in fcf_results.items():
            if values:
                print(f"  {fcf_type}: {len(values)} years, latest: ${values[-1]/1e6:.0f}M")
    else:
        print("FAIL: No FCF data calculated")
        sys.exit(1)

    # Create DCF valuator
    print("\n3. Running DCF valuation...")
    valuator = DCFValuator(calc)

    # Run DCF calculation with debug logging
    dcf_results = valuator.calculate_dcf_projections()

    print("\n=== DCF RESULTS ===")
    enterprise_value = dcf_results.get('enterprise_value')
    equity_value = dcf_results.get('equity_value')
    terminal_value = dcf_results.get('terminal_value')
    value_per_share = dcf_results.get('value_per_share')
    fcf_type = dcf_results.get('fcf_type')

    print(f"FCF Type: {fcf_type}")
    print(f"Enterprise Value: {enterprise_value}")
    print(f"Equity Value: {equity_value}")
    print(f"Terminal Value: {terminal_value}")
    print(f"Value Per Share: {value_per_share}")

    if equity_value:
        if equity_value > 1e12:  # Over 1 trillion
            print(f"PASS: Equity value ${equity_value/1e12:.2f}T appears reasonable for MSFT")
        elif equity_value > 1e9:  # Over 1 billion
            print(f"WARN: Equity value ${equity_value/1e9:.2f}B seems low for MSFT")
        else:
            print(f"FAIL: Equity value ${equity_value/1e6:.2f}M is definitely wrong for MSFT")

    # Test the CSV export scaling
    print("\n=== TESTING CSV EXPORT ===")
    from fcf_analysis_streamlit import get_financial_scale_and_unit, create_enhanced_dcf_csv_export

    if equity_value:
        ev_scaled, ev_unit, ev_abbrev = get_financial_scale_and_unit(
            equity_value, already_in_millions=False
        )
        print(f"Scaled Equity Value: {ev_scaled:.3f} {ev_unit}")

        # Create a dummy DCF DataFrame for CSV export
        import pandas as pd

        dummy_dcf_df = pd.DataFrame(
            {
                'Year': [1, 2, 3],
                'Projected FCF ($M)': [100000, 110000, 120000],
                'Growth Rate': ['10%', '10%', '10%'],
                'Present Value ($M)': [90000, 99000, 108000],
                'Discount Factor': [0.9, 0.81, 0.73],
            }
        )

        # Test CSV export with the calculated values
        print("\n4. Testing CSV export...")
        try:
            csv_data = create_enhanced_dcf_csv_export(
                dummy_dcf_df,
                dcf_results,
                {
                    'discount_rate': 0.1,
                    'terminal_growth_rate': 0.03,
                    'projection_years': 10,
                    'growth_rate_yr1_5': 0.18,
                },
                'MSFT',
                500.0,
            )

            # Extract the enterprise value from CSV
            import re

            ev_match = re.search(r'"Enterprise Value",([0-9.]+),"([^"]+)"', csv_data)
            if ev_match:
                csv_ev_value = float(ev_match.group(1))
                csv_ev_unit = ev_match.group(2)
                print(f"CSV Enterprise Value: {csv_ev_value} {csv_ev_unit}")

                # Compare with what we calculated
                if abs(csv_ev_value - ev_scaled) < 0.001:
                    print("PASS: CSV export scaling is correct")
                else:
                    print(
                        f"FAIL: CSV export scaling error: expected {ev_scaled:.3f}, got {csv_ev_value}"
                    )
            else:
                print("FAIL: Could not find Enterprise Value in CSV")

        except Exception as e:
            print(f"FAIL: CSV export failed: {e}")

    print("\n=== SUMMARY ===")
    print("Excel-based DCF test completed")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
