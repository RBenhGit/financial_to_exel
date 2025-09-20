#!/usr/bin/env python3
"""
Simple test script to verify that our property fix works with real MSFT data.
This directly tests the user acceptance testing scenario that was failing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.analysis.engines.financial_calculations import FinancialCalculator

def test_property_fix():
    """Test the exact scenario that was failing in user acceptance testing"""

    print("Testing FinancialCalculator property access fix...")
    print("=" * 60)

    # Load MSFT data (same as UAT)
    msft_folder = r"C:\AsusWebStorage\ran@benhur.co\MySyncFolder\python\investingAnalysis\financial_to_exel\data\companies\MSFT"

    # Create calculator and load data
    calculator = FinancialCalculator(msft_folder)
    success = calculator.load_financial_data()
    print(f"Financial data loaded: {success}")

    print("\n=== CRITICAL TEST: Property Access ===")
    print("These were the exact assertions that were failing in UAT:")

    # The failing assertions from user acceptance testing:
    try:
        print(f"calculator.total_revenue: {calculator.total_revenue}")
        assert calculator.total_revenue is not None, "total_revenue should not be None"
        assert calculator.total_revenue > 0, "total_revenue should be positive"
        print("✅ PASS: total_revenue property access works!")
    except Exception as e:
        print(f"❌ FAIL: total_revenue property access failed: {e}")
        return False

    try:
        print(f"calculator.net_income: {calculator.net_income}")
        assert calculator.net_income is not None, "net_income should not be None"
        assert calculator.net_income > 0, "net_income should be positive"
        print("✅ PASS: net_income property access works!")
    except Exception as e:
        print(f"❌ FAIL: net_income property access failed: {e}")
        return False

    try:
        print(f"calculator.operating_cash_flow: {calculator.operating_cash_flow}")
        # operating_cash_flow can be None or a number
        print("✅ PASS: operating_cash_flow property access works!")
    except Exception as e:
        print(f"❌ FAIL: operating_cash_flow property access failed: {e}")
        return False

    print("\n=== Additional Property Testing ===")

    properties_to_test = [
        'total_assets', 'current_assets', 'shareholders_equity',
        'operating_income', 'gross_profit', 'cost_of_revenue',
        'free_cash_flow', 'working_capital', 'enterprise_value'
    ]

    for prop in properties_to_test:
        try:
            value = getattr(calculator, prop)
            print(f"calculator.{prop}: {value}")
        except Exception as e:
            print(f"❌ ERROR accessing {prop}: {e}")

    print("\n=== Property Type Verification ===")

    # Verify these are actual properties, not just attributes
    try:
        assert isinstance(calculator.__class__.total_revenue, property), "total_revenue should be a property"
        assert isinstance(calculator.__class__.net_income, property), "net_income should be a property"
        assert isinstance(calculator.__class__.operating_cash_flow, property), "operating_cash_flow should be a property"
        print("✅ PASS: Properties are correctly implemented as @property decorators")
    except Exception as e:
        print(f"❌ FAIL: Property verification failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 SUCCESS: All critical user acceptance test scenarios PASS!")
    print("The FinancialCalculator property access fix is working correctly!")
    print("Users can now access financial metrics through simple property access patterns.")
    return True


if __name__ == "__main__":
    success = test_property_fix()
    sys.exit(0 if success else 1)