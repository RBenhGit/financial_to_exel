"""
Test script to verify the DCF Enterprise Value scaling fix
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_get_financial_scale_and_unit():
    """Test the fixed get_financial_scale_and_unit function"""
    from fcf_analysis_streamlit import get_financial_scale_and_unit

    print("Testing get_financial_scale_and_unit function...")

    # Test case: Microsoft's enterprise value
    # The DCF calculation should return ~1,306,205 (already in millions)
    # This should be recognized as 1.306 trillion, not millions

    test_cases = [
        # (input_value, already_in_millions, expected_scaled_value, expected_unit)
        (1306205, True, 1.306, "Trillions USD"),  # Microsoft EV case (correct calculation)
        (500000, True, 500.0, "Billions USD"),  # 500B case
        (50000, True, 50.0, "Billions USD"),  # 50B case
        (5000, True, 5.0, "Billions USD"),  # 5B case
        (500, True, 500.0, "Millions USD"),  # 500M case
        (50, True, 50.0, "Millions USD"),  # 50M case
        # Test with already_in_millions=False (legacy behavior)
        (3487000000000, False, 3.487, "Trillions USD"),  # Raw 3.487T
        (500000000000, False, 500.0, "Billions USD"),  # Raw 500B
    ]

    passed = 0
    total = len(test_cases)

    for i, (input_val, already_millions, expected_scaled, expected_unit) in enumerate(test_cases):
        try:
            scaled_val, unit, abbrev = get_financial_scale_and_unit(input_val, already_millions)

            # Check if results match expectations
            scaled_ok = (
                abs(scaled_val - expected_scaled) < 0.01
            )  # Allow small floating point differences
            unit_ok = unit == expected_unit

            if scaled_ok and unit_ok:
                print(
                    f"  PASS Test {i+1}: {input_val} ({'millions' if already_millions else 'raw'}) -> {scaled_val:.3f} {unit}"
                )
                passed += 1
            else:
                print(
                    f"  FAIL Test {i+1}: {input_val} ({'millions' if already_millions else 'raw'}) -> {scaled_val:.3f} {unit}"
                )
                print(f"     Expected: {expected_scaled:.3f} {expected_unit}")

        except Exception as e:
            print(f"  FAIL Test {i+1}: Error - {e}")

    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total


def test_microsoft_dcf_scaling():
    """Test the specific Microsoft DCF case"""
    from fcf_analysis_streamlit import get_financial_scale_and_unit

    print("\nTesting Microsoft DCF specific case...")

    # Simulate Microsoft DCF results (values that would come from DCF calculation)
    microsoft_dcf_results = {
        'enterprise_value': 1306205,  # This is in millions (1.306 trillion actual)
        'equity_value': 1306205,  # Same for FCFE
        'terminal_value': 5.655,  # Small number, should stay in millions
        'net_debt': 0,  # Zero debt
    }

    print("Simulating CSV export scaling:")

    # Test enterprise value scaling
    ev_scaled, ev_unit, ev_abbrev = get_financial_scale_and_unit(
        microsoft_dcf_results['enterprise_value']
    )
    print(f"  Enterprise Value: {ev_scaled:.3f} {ev_unit}")

    # Test equity value scaling
    eq_scaled, eq_unit, eq_abbrev = get_financial_scale_and_unit(
        microsoft_dcf_results['equity_value']
    )
    print(f"  Equity Value: {eq_scaled:.3f} {eq_unit}")

    # Test terminal value scaling
    tv_scaled, tv_unit, tv_abbrev = get_financial_scale_and_unit(
        microsoft_dcf_results['terminal_value']
    )
    print(f"  Terminal Value: {tv_scaled:.3f} {tv_unit}")

    # Verify expectations
    expected_ev_unit = "Trillions USD"
    expected_ev_scaled = 1.306

    success = abs(ev_scaled - expected_ev_scaled) < 0.01 and ev_unit == expected_ev_unit

    if success:
        print("  PASS: Microsoft DCF scaling is now CORRECT!")
        print(f"    Before fix: 1.306 Millions USD (WRONG)")
        print(f"    After fix:  {ev_scaled:.3f} {ev_unit} (CORRECT)")
    else:
        print("  FAIL: Microsoft DCF scaling is still incorrect")
        print(f"    Got: {ev_scaled:.3f} {ev_unit}")
        print(f"    Expected: {expected_ev_scaled:.3f} {expected_ev_unit}")

    return success


def main():
    """Run all tests"""
    print("DCF Enterprise Value Scaling Fix - Test Suite")
    print("=" * 60)

    tests = [
        ("Scale Function Tests", test_get_financial_scale_and_unit),
        ("Microsoft DCF Case", test_microsoft_dcf_scaling),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'-' * 30}")
        print(f"TEST: {test_name}")
        print(f"{'-' * 30}")

        try:
            if test_func():
                print(f"PASS: {test_name} PASSED")
                passed += 1
            else:
                print(f"FAIL: {test_name} FAILED")
        except Exception as e:
            print(f"FAIL: {test_name} FAILED - {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"FINAL RESULTS")
    print(f"{'=' * 60}")
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\nSUCCESS: All tests passed! The DCF scaling fix is working correctly.")
        return 0
    else:
        print(f"\nFAILED: {total - passed} test(s) failed. Review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
