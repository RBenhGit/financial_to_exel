"""
Test script for DDM and PB capture functionality
"""

import logging
from analysis_capture import analysis_capture
from watch_list_manager import WatchListManager
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ddm_capture():
    """Test DDM analysis capture"""
    print("Testing DDM capture functionality...")

    # Sample DDM results (similar to what DDMValuator would return)
    ddm_results = {
        'intrinsic_value': 150.25,
        'current_dividend': 2.50,
        'model_type': 'gordon',
        'model_variant': 'Gordon Growth Model',
        'assumptions': {'discount_rate': 0.10, 'terminal_growth_rate': 0.03},
        'market_data': {'current_price': 140.00},
        'currency': 'USD',
        'is_tase_stock': False,
        'upside_downside': 0.073,
        'calculation_method': 'Single-stage perpetual growth model',
        'dividend_metrics': {'dividend_cagr_3y': 0.05, 'payout_ratio': 0.6},
    }

    # Test DDM capture
    success = analysis_capture.capture_ddm_analysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        ddm_results=ddm_results,
        watch_list_name="Test Portfolio",
    )

    print(f"DDM capture result: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_pb_capture():
    """Test P/B analysis capture"""
    print("Testing P/B capture functionality...")

    # Sample P/B results (similar to what PBValuator would return)
    pb_results = {
        'ticker_symbol': 'MSFT',
        'analysis_date': datetime.now().isoformat(),
        'current_data': {
            'current_price': 380.00,
            'book_value_per_share': 25.50,
            'pb_ratio': 14.9,
            'shares_outstanding': 7400000000,
            'market_cap': 2812000000000,
        },
        'industry_info': {
            'industry': 'Software',
            'sector': 'Technology',
            'industry_key': 'Technology',
        },
        'industry_comparison': {
            'position': 'Above Industry Median',
            'percentile': '75%',
            'analysis': 'Trading at premium to peers',
        },
        'valuation_analysis': {
            'valuation_ranges': {'conservative': 89.25, 'fair_value': 178.50, 'optimistic': 357.00}
        },
        'risk_assessment': {
            'risk_level': 'Medium',
            'risks': ['High P/B ratio suggests significant premium valuation'],
        },
        'currency': 'USD',
        'is_tase_stock': False,
    }

    # Test P/B capture
    success = analysis_capture.capture_pb_analysis(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        pb_results=pb_results,
        watch_list_name="Test Portfolio",
    )

    print(f"P/B capture result: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_unified_capture():
    """Test unified capture functionality"""
    print("Testing unified capture functionality...")

    # Sample DCF results for comparison
    dcf_results = {
        'value_per_share': 175.00,
        'enterprise_value': 1500000000000,
        'equity_value': 1300000000000,
        'assumptions': {'discount_rate': 0.09, 'terminal_growth_rate': 0.025},
        'market_data': {'current_price': 160.00},
        'currency': 'USD',
        'is_tase_stock': False,
    }

    # Test unified capture with different analysis types
    success_dcf = analysis_capture.capture_analysis(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        analysis_results=dcf_results,
        analysis_type="DCF",
        watch_list_name="Test Portfolio",
    )

    print(f"Unified DCF capture result: {'SUCCESS' if success_dcf else 'FAILED'}")
    return success_dcf


def setup_test_environment():
    """Set up test environment"""
    print("Setting up test environment...")

    # Create a test watch list
    watch_list_manager = WatchListManager()

    # Check if test portfolio exists, create if not
    watch_lists = watch_list_manager.list_watch_lists()
    test_exists = any(wl['name'] == 'Test Portfolio' for wl in watch_lists)

    if not test_exists:
        success = watch_list_manager.create_watch_list(
            "Test Portfolio", "Test portfolio for capture functionality testing"
        )
        print(f"Created test watch list: {'SUCCESS' if success else 'FAILED'}")
        return success
    else:
        print("Test watch list already exists")
        return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("DDM and P/B Capture Functionality Tests")
    print("=" * 50)

    # Set up test environment
    if not setup_test_environment():
        print("Failed to set up test environment. Exiting.")
        return

    # Enable capture
    analysis_capture.enable_capture()
    analysis_capture.set_current_watch_list("Test Portfolio")

    # Run tests
    tests = [
        ("DDM Capture", test_ddm_capture),
        ("P/B Capture", test_pb_capture),
        ("Unified Capture", test_unified_capture),
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
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("✅ All tests PASSED! DDM and P/B capture functionality is working correctly.")
    else:
        print("❌ Some tests FAILED. Please check the implementation.")


if __name__ == "__main__":
    main()
