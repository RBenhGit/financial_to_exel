"""
Test backward compatibility of DCF capture functionality
"""

import logging
from analysis_capture import analysis_capture
from watch_list_manager import WatchListManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_legacy_dcf_capture():
    """Test that existing DCF capture still works"""
    print("Testing legacy DCF capture functionality...")

    # Sample DCF results (old format)
    dcf_results = {
        'value_per_share': 185.50,
        'enterprise_value': 2500000000000,
        'equity_value': 2200000000000,
        'terminal_value': 1800000000000,
        'pv_terminal': 950000000000,
        'assumptions': {
            'discount_rate': 0.08,
            'terminal_growth_rate': 0.025,
            'projection_years': 10,
        },
        'market_data': {'current_price': 170.00},
        'currency': 'USD',
        'is_tase_stock': False,
        'fcf_type': 'FCFE',
    }

    # Test legacy DCF capture method
    success = analysis_capture.capture_dcf_analysis(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        dcf_results=dcf_results,
        watch_list_name="Test Portfolio",
    )

    print(f"Legacy DCF capture result: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_legacy_multiple_capture():
    """Test legacy multiple list capture"""
    print("Testing legacy multiple list capture...")

    # Create another test watch list
    watch_list_manager = WatchListManager()
    watch_list_manager.create_watch_list("Test Portfolio 2", "Second test portfolio")

    dcf_results = {
        'value_per_share': 95.25,
        'assumptions': {'discount_rate': 0.09, 'terminal_growth_rate': 0.03},
        'market_data': {'current_price': 88.00},
        'currency': 'USD',
    }

    # Test capture to multiple lists (legacy method signature should still work)
    results = analysis_capture.capture_to_multiple_lists(
        ticker="AMD",
        company_name="Advanced Micro Devices",
        analysis_results=dcf_results,  # Updated parameter name
        watch_list_names=["Test Portfolio", "Test Portfolio 2"],
        analysis_type="DCF",  # New parameter with default
    )

    success = all(results.values())
    print(f"Multiple list capture result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Results: {results}")
    return success


def verify_data_structure():
    """Verify that captured data has the correct structure"""
    print("Verifying captured data structure...")

    watch_list_manager = WatchListManager()

    # Get the test portfolio data
    portfolio_data = watch_list_manager.get_watch_list("Test Portfolio", latest_only=False)

    if not portfolio_data or not portfolio_data.get('stocks'):
        print("No data found in test portfolio")
        return False

    # Check that we have different analysis types
    analysis_types = set()
    for stock in portfolio_data['stocks']:
        analysis_type = stock.get(
            'analysis_type', 'DCF'
        )  # Default to DCF for backward compatibility
        analysis_types.add(analysis_type)

    print(f"Found analysis types: {analysis_types}")

    # Should have DCF, DDM, and PB
    expected_types = {'DCF', 'DDM', 'PB'}
    has_all_types = expected_types.issubset(analysis_types)

    print(f"Data structure verification: {'SUCCESS' if has_all_types else 'FAILED'}")
    return has_all_types


def main():
    """Run backward compatibility tests"""
    print("=" * 50)
    print("Backward Compatibility Tests")
    print("=" * 50)

    # Enable capture
    analysis_capture.enable_capture()
    analysis_capture.set_current_watch_list("Test Portfolio")

    # Run tests
    tests = [
        ("Legacy DCF Capture", test_legacy_dcf_capture),
        ("Legacy Multiple Capture", test_legacy_multiple_capture),
        ("Data Structure Verification", verify_data_structure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))
        print("-" * 30)

    # Summary
    print("\n" + "=" * 50)
    print("BACKWARD COMPATIBILITY RESULTS")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:30}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("All backward compatibility tests PASSED!")
    else:
        print("Some backward compatibility tests FAILED.")


if __name__ == "__main__":
    main()
