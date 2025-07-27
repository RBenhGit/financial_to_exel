"""
Test the corrected DDM and PB capture implementation
"""

import logging
from analysis_capture import analysis_capture
from watch_list_manager import WatchListManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_corrected_capture_implementation():
    """Test that the corrected centralized capture works"""
    print("Testing corrected capture implementation...")

    # Set up test environment
    watch_list_manager = WatchListManager()

    # Create test portfolio if it doesn't exist
    watch_lists = watch_list_manager.list_watch_lists()
    if not any(wl['name'] == 'Corrected Test' for wl in watch_lists):
        watch_list_manager.create_watch_list("Corrected Test", "Testing corrected implementation")

    # Enable capture
    analysis_capture.enable_capture()
    analysis_capture.set_current_watch_list("Corrected Test")

    # Test DCF capture (should still work)
    dcf_results = {
        'value_per_share': 200.00,
        'assumptions': {'discount_rate': 0.08, 'terminal_growth_rate': 0.025},
        'market_data': {'current_price': 180.00},
        'currency': 'USD',
    }

    dcf_success = analysis_capture.capture_dcf_analysis(
        ticker="TEST1", company_name="Test Company 1", dcf_results=dcf_results
    )

    # Test DDM capture
    ddm_results = {
        'intrinsic_value': 150.00,
        'current_dividend': 3.00,
        'model_type': 'gordon',
        'assumptions': {'discount_rate': 0.09, 'terminal_growth_rate': 0.03},
        'market_data': {'current_price': 140.00},
        'currency': 'USD',
    }

    ddm_success = analysis_capture.capture_ddm_analysis(
        ticker="TEST2", company_name="Test Company 2", ddm_results=ddm_results
    )

    # Test P/B capture
    pb_results = {
        'ticker_symbol': 'TEST3',
        'current_data': {'current_price': 50.00, 'book_value_per_share': 15.00, 'pb_ratio': 3.33},
        'valuation_analysis': {
            'valuation_ranges': {'conservative': 30.00, 'fair_value': 45.00, 'optimistic': 60.00}
        },
        'currency': 'USD',
    }

    pb_success = analysis_capture.capture_pb_analysis(
        ticker="TEST3", company_name="Test Company 3", pb_results=pb_results
    )

    # Test unified capture method
    unified_success = analysis_capture.capture_analysis(
        ticker="TEST4",
        company_name="Test Company 4",
        analysis_results=dcf_results,
        analysis_type="DCF",
    )

    # Verify results
    results = {
        'DCF Legacy': dcf_success,
        'DDM': ddm_success,
        'P/B': pb_success,
        'Unified DCF': unified_success,
    }

    print("\n" + "=" * 50)
    print("CORRECTED IMPLEMENTATION TEST RESULTS")
    print("=" * 50)

    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:15}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    # Verify data in watch list
    portfolio_data = watch_list_manager.get_watch_list("Corrected Test", latest_only=False)
    if portfolio_data and portfolio_data.get('stocks'):
        analysis_types = set()
        for stock in portfolio_data['stocks']:
            analysis_type = stock.get('analysis_type', 'DCF')
            analysis_types.add(analysis_type)

        print(f"\nFound analysis types in watch list: {analysis_types}")

        if {'DCF', 'DDM', 'PB'}.issubset(analysis_types):
            print("✅ All analysis types successfully captured to watch list!")
        else:
            print("❌ Some analysis types missing from watch list")
    else:
        print("❌ No data found in watch list")

    return passed == len(results)


def verify_ui_changes():
    """Verify that the UI changes are correct"""
    print("\n" + "=" * 50)
    print("UI VERIFICATION")
    print("=" * 50)

    # Read the streamlit file to verify changes
    with open('fcf_analysis_streamlit.py', 'r') as f:
        content = f.read()

    # Check that incorrect capture sections were removed
    ddm_capture_removed = "🎯 Capture DDM Analysis to Watch List" not in content
    pb_capture_removed = "🎯 Capture P/B Analysis to Watch List" not in content

    # Check that correct capture section exists
    manual_capture_enhanced = "Manual Analysis Capture" in content
    multi_analysis_support = "available_analyses" in content
    capture_all_button = "Capture All Available Analyses" in content

    checks = {
        "DDM capture section removed": ddm_capture_removed,
        "P/B capture section removed": pb_capture_removed,
        "Manual capture section exists": manual_capture_enhanced,
        "Multi-analysis support": multi_analysis_support,
        "Capture all button": capture_all_button,
    }

    passed_ui = 0
    for check_name, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"{check_name:30}: {status}")
        if result:
            passed_ui += 1

    print(f"\nUI Verification: {passed_ui}/{len(checks)} checks passed")
    return passed_ui == len(checks)


def main():
    """Run all corrected implementation tests"""
    print("=" * 60)
    print("CORRECTED DDM AND PB CAPTURE IMPLEMENTATION TESTS")
    print("=" * 60)

    # Test functionality
    functionality_passed = test_corrected_capture_implementation()

    # Verify UI changes
    ui_passed = verify_ui_changes()

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    if functionality_passed and ui_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ DDM and PB capture is now correctly implemented")
        print("✅ Capture functionality centralized in Watch Lists tab")
        print("✅ Incorrect capture sections removed from analysis tabs")
        return True
    else:
        print("❌ Some tests failed")
        if not functionality_passed:
            print("  - Capture functionality issues")
        if not ui_passed:
            print("  - UI implementation issues")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
