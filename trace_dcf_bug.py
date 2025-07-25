"""
Trace the exact DCF calculation bug by simulating the code flow
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_exact_dcf_calculation():
    """
    Simulate the exact DCF calculation to find where the bug occurs
    """
    print("Simulating exact DCF calculation flow...")
    
    # These are the present values from the actual CSV export - they appear correct
    pv_fcf_from_csv = [
        102260.94545454544,   # Year 1
        109698.1051239669,    # Year 2
        117676.14913298265,   # Year 3
        126234.4145244723,    # Year 4
        135415.0992171612,    # Year 5
        137877.1919302005,    # Year 6
        140384.049965295,     # Year 7
        142936.4872373913,    # Year 8
        145535.33245988932,   # Year 9
        148181.42941370548,   # Year 10
    ]
    
    pv_terminal_from_csv = 5.655
    
    print(f"Individual PV values from CSV: {len(pv_fcf_from_csv)} values")
    for i, pv in enumerate(pv_fcf_from_csv, 1):
        print(f"  Year {i}: ${pv:,.2f}M")
    print(f"PV Terminal: ${pv_terminal_from_csv}M")
    
    # Simulate the exact calculation from dcf_valuation.py line 99:
    # equity_value = sum(pv_fcf) + pv_terminal
    
    print(f"\nSimulating DCF calculation:")
    print(f"pv_fcf = {pv_fcf_from_csv}")
    print(f"pv_terminal = {pv_terminal_from_csv}")
    
    # Step 1: Calculate sum(pv_fcf)
    sum_pv_fcf = sum(pv_fcf_from_csv)
    print(f"sum(pv_fcf) = {sum_pv_fcf:,.2f}")
    
    # Step 2: Add terminal value
    equity_value = sum_pv_fcf + pv_terminal_from_csv
    print(f"equity_value = sum(pv_fcf) + pv_terminal = {equity_value:,.2f}")
    
    # This should give us ~1.306 trillion, but CSV shows 3.487
    csv_exported_value = 3.487
    print(f"\nExpected equity_value: {equity_value:,.2f} million")
    print(f"CSV exported equity_value: {csv_exported_value} million")
    print(f"Ratio: {equity_value / csv_exported_value:,.0f}x")
    
    # Now let's check if this might be a precision/rounding issue
    # Maybe the individual PV values are stored differently than displayed
    
    print(f"\nDetailed analysis:")
    print(f"Sum using Python sum(): {sum(pv_fcf_from_csv):,.10f}")
    print(f"Sum using manual addition:")
    manual_sum = 0
    for pv in pv_fcf_from_csv:
        manual_sum += pv
    print(f"  Manual sum: {manual_sum:,.10f}")
    
    # Check if there might be a data type issue
    print(f"\nData type analysis:")
    print(f"Type of pv_fcf_from_csv[0]: {type(pv_fcf_from_csv[0])}")
    print(f"Type of sum result: {type(sum_pv_fcf)}")
    
    # The issue might be that the actual DCF calculation is using different values
    # than what's exported to the CSV projections section
    
    print(f"\n" + "="*60)
    print("HYPOTHESIS: The individual PV values in CSV are correct,")
    print("but the DCF calculation uses different internal values.")
    print("This suggests a disconnect between:")
    print("1. The values used for the projections table (correct)")
    print("2. The values used for the summary calculation (wrong)")
    print("="*60)
    
    return equity_value

def investigate_potential_disconnect():
    """
    Investigate potential disconnect between projection values and summary calculation
    """
    print("\nInvestigating potential disconnect...")
    
    # If the individual PV values are correct (~1.3T total) but the final
    # equity value is wrong (3.487M), then either:
    
    print("Potential causes:")
    print("1. DCF calculation uses different PV values than exported")
    print("2. There's a data corruption between calculation and summary")
    print("3. The sum() operation has a bug or precision issue")
    print("4. The equity_value gets overwritten somewhere")
    print("5. Different FCF data is used for projections vs calculations")
    
    # The most likely scenario is #1 or #5
    print("\nMost likely scenario:")
    print("The DCF calculation and CSV projection export use different data sources")
    print("- CSV projections: Uses correct FCF data")
    print("- DCF summary: Uses wrong/corrupted FCF data")
    
    print("\nNext investigation steps:")
    print("1. Check if there are multiple FCF data sources")
    print("2. Verify if DCF calculation receives the same data as projections")
    print("3. Add debug logging to trace actual values in DCF calculation")
    print("4. Compare fcf_values input vs projected_fcf output")

def main():
    """Run DCF bug tracing"""
    print("DCF Bug Tracing - Data Flow Analysis")
    print("=" * 50)
    
    calculated_equity_value = simulate_exact_dcf_calculation()
    investigate_potential_disconnect()
    
    print(f"\nConclusion: Need to verify if DCF calculation uses same data as CSV export")
    return 0

if __name__ == "__main__":
    sys.exit(main())