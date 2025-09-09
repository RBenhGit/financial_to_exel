"""
Debug script to investigate DCF calculation issues
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_dcf_present_value_summation():
    """
    Test if the DCF calculation is correctly summing present values
    """
    print("Analyzing DCF Present Value Summation...")

    # Values from the actual Microsoft CSV export
    present_values_from_csv = [
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

    # Terminal value from CSV
    terminal_value_pv = 5.655  # This should be present value of terminal value

    # Calculate the sum manually
    sum_pv_fcf = sum(present_values_from_csv)
    total_enterprise_value = sum_pv_fcf + terminal_value_pv

    print(f"Sum of PV of FCF: {sum_pv_fcf:,.2f} million")
    print(f"PV of Terminal Value: {terminal_value_pv:,.3f} million")
    print(f"Total Enterprise Value: {total_enterprise_value:,.2f} million")
    print(f"Total Enterprise Value: {total_enterprise_value/1000000:,.3f} trillion")

    # Compare with what was exported
    exported_ev = 3.487
    print(f"\nExported Enterprise Value: {exported_ev} million")
    print(f"Expected Enterprise Value: {total_enterprise_value:,.2f} million")
    print(f"Difference: {total_enterprise_value - exported_ev:,.2f} million")
    print(f"Ratio (Expected/Exported): {total_enterprise_value/exported_ev:,.0f}x")

    # This suggests a massive calculation error
    if total_enterprise_value / exported_ev > 100000:
        print("\n🚨 CRITICAL BUG DETECTED:")
        print("   The DCF calculation is off by more than 100,000x!")
        print("   This indicates a severe unit conversion or summation error.")
        return False
    else:
        print("\n✅ DCF calculation appears reasonable")
        return True


def investigate_potential_causes():
    """
    Investigate potential causes of the DCF calculation error
    """
    print("\n" + "=" * 60)
    print("INVESTIGATING POTENTIAL ROOT CAUSES")
    print("=" * 60)

    print("\nPotential Issues:")
    print("1. Unit conversion error in DCF calculation")
    print("2. Division instead of summation")
    print("3. Present value calculation using wrong discount factor")
    print("4. Terminal value calculation error")
    print("5. Data type conversion issues (float precision)")
    print("6. Missing multiplication factor")

    print("\nNext Steps:")
    print("1. Examine DCF calculation code line by line")
    print("2. Add debug logging to track intermediate values")
    print("3. Compare manual calculation vs code calculation")
    print("4. Test with simplified inputs")


def main():
    """Run DCF calculation debugging"""
    print("DCF Calculation Bug Investigation")
    print("=" * 50)

    # Test present value summation
    is_reasonable = test_dcf_present_value_summation()

    if not is_reasonable:
        investigate_potential_causes()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
