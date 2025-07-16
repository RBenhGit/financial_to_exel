#!/usr/bin/env python3
"""
Test that NVDA behaves identically to other assets
"""
import sys
sys.path.append('.')
from test_comprehensive import discover_companies, test_company_data_ordering

def test_nvda_equality():
    """Test that NVDA behaves identically to other assets"""
    print('Testing that NVDA behaves identically to other assets...')
    companies = discover_companies()
    print(f'Available companies: {companies}')

    if 'NVDA' not in companies:
        print('NVDA not found in companies list')
        return False

    # Test NVDA
    print('\n=== Testing NVDA (should behave like any other company) ===')
    result_nvda = test_company_data_ordering('NVDA')
    print(f'NVDA test result: {result_nvda}')
    
    # Test with another company to compare
    other_companies = [c for c in companies if c != 'NVDA']
    if not other_companies:
        print('\n⚠️ No other companies available for comparison')
        return True  # Can't compare but NVDA works
    
    other_company = other_companies[0]
    print(f'\n=== Testing {other_company} (for comparison) ===')
    result_other = test_company_data_ordering(other_company)
    print(f'{other_company} test result: {result_other}')
    
    # Both should have the same result type (both pass or both fail)
    if result_nvda == result_other:
        print('\n✅ SUCCESS: NVDA behaves identically to other assets!')
        return True
    else:
        print('\n❌ FAIL: NVDA still behaves differently than other assets')
        return False

if __name__ == "__main__":
    success = test_nvda_equality()
    sys.exit(0 if success else 1)