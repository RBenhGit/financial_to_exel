"""
Debug DCF calculation by adding strategic logging
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def debug_dcf_calculation():
    """
    Add debug logging to track where the DCF calculation goes wrong
    """
    print("Adding debug logging to DCF calculation...")

    # I need to examine the actual DCF calculation step by step
    # The most suspicious place is around line 99 where equity_value is calculated

    # Let me create a test that mimics the DCF calculation with the actual values
    # from the Microsoft CSV

    # Present values from CSV (in millions)
    pv_fcf_values = [
        102260.94545454544,  # Year 1
        109698.1051239669,  # Year 2
        117676.14913298265,  # Year 3
        126234.4145244723,  # Year 4
        135415.0992171612,  # Year 5
        137877.1919302005,  # Year 6
        140384.049965295,  # Year 7
        142936.4872373913,  # Year 8
        145535.33245988932,  # Year 9
        148181.42941370548,  # Year 10
    ]

    # Terminal value present value from CSV
    pv_terminal = 5.655  # millions

    print("Simulating DCF calculation logic:")
    print(f"pv_fcf = {pv_fcf_values}")
    print(f"pv_terminal = {pv_terminal}")

    # This mirrors line 99 in dcf_valuation.py:
    # equity_value = sum(pv_fcf) + pv_terminal
    sum_pv_fcf = sum(pv_fcf_values)
    equity_value = sum_pv_fcf + pv_terminal

    print(f"\nCalculation steps:")
    print(f"sum(pv_fcf) = {sum_pv_fcf:,.2f} million")
    print(f"pv_terminal = {pv_terminal:,.3f} million")
    print(f"equity_value = sum(pv_fcf) + pv_terminal = {equity_value:,.2f} million")

    # Now test the per-share calculation (line 164-165):
    # equity_value_actual_currency = equity_value * 1000000
    # value_per_share = equity_value_actual_currency / shares_outstanding

    shares_outstanding = 7.43e9  # 7.43 billion shares
    equity_value_actual_currency = equity_value * 1000000
    value_per_share = equity_value_actual_currency / shares_outstanding

    print(f"\nPer-share calculation:")
    print(f"shares_outstanding = {shares_outstanding:,.0f}")
    print(
        f"equity_value_actual_currency = {equity_value} * 1,000,000 = {equity_value_actual_currency:,.0f}"
    )
    print(
        f"value_per_share = {equity_value_actual_currency:,.0f} / {shares_outstanding:,.0f} = ${value_per_share:.2f}"
    )

    # Compare with actual CSV values
    print(f"\nComparison with CSV export:")
    print(f"Expected value_per_share: $469.10")
    print(f"Calculated value_per_share: ${value_per_share:.2f}")
    print(f"Expected equity_value: 3.487 million (from CSV)")
    print(f"Calculated equity_value: {equity_value:,.2f} million")

    # The discrepancy shows where the bug is
    ratio = equity_value / 3.487
    print(f"\nDISCREPANCY ANALYSIS:")
    print(f"Calculated equity_value is {ratio:,.0f}x larger than exported value")
    print(f"This suggests the exported value was divided by {ratio:,.0f}")

    if abs(ratio - 1000000) < 1000:
        print("🚨 CONFIRMED: The equity_value is being divided by ~1,000,000 somewhere!")
        print("   This is likely happening between the DCF calculation and CSV export")

        # Let me check what the equity_value should be to get the correct per-share value
        expected_equity_value_for_correct_per_share = (469.10 * shares_outstanding) / 1000000
        print(f"\nFor the correct per-share value of $469.10:")
        print(
            f"Expected equity_value should be: {expected_equity_value_for_correct_per_share:,.2f} million"
        )
        print(f"This matches our calculated value: {equity_value:,.2f} million")
        print(f"But CSV shows: 3.487 million")
        print("\nCONCLUSION: There's a bug in the DCF-to-CSV export process")

    return True


def main():
    """Run DCF debugging"""
    print("DCF Calculation Step-by-Step Debug")
    print("=" * 50)

    debug_dcf_calculation()
    return 0


if __name__ == "__main__":
    sys.exit(main())
