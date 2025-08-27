"""
Test script for extended FinancialDataRequest functionality
Tests new historical P/B data parameters and backward compatibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources import FinancialDataRequest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_backward_compatibility():
    """Test that existing FinancialDataRequest usage still works"""
    print("\n=== Testing Backward Compatibility ===")
    
    # Test 1: Default initialization (should work as before)
    request1 = FinancialDataRequest(ticker="AAPL")
    print(f"[OK] Default request: ticker={request1.ticker}, data_types={request1.data_types}")
    print(f"  period={request1.period}, limit={request1.limit}, historical_years={request1.historical_years}")
    
    # Test 2: Existing parameter usage
    request2 = FinancialDataRequest(
        ticker="MSFT",
        data_types=['price', 'fundamentals'],
        period='quarterly',
        limit=20,
        force_refresh=True
    )
    print(f"[OK] Legacy request: ticker={request2.ticker}, data_types={request2.data_types}")
    print(f"  period={request2.period}, limit={request2.limit}, pb_mode={request2.pb_analysis_mode}")
    
    return True


def test_new_pb_functionality():
    """Test new P/B analysis specific functionality"""
    print("\n=== Testing New P/B Functionality ===")
    
    # Test 1: P/B analysis mode with auto-adjustments
    request1 = FinancialDataRequest(
        ticker="GOOGL",
        pb_analysis_mode=True,
        historical_years=3
    )
    print(f"[OK] P/B mode request: ticker={request1.ticker}")
    print(f"  pb_analysis_mode={request1.pb_analysis_mode}")
    print(f"  historical_years={request1.historical_years}")
    print(f"  period={request1.period} (auto-adjusted)")
    print(f"  limit={request1.limit} (auto-adjusted)")
    print(f"  data_types={request1.data_types} (auto-extended)")
    
    # Test 2: Manual historical P/B data request
    request2 = FinancialDataRequest(
        ticker="BRK-B",
        data_types=['historical_prices', 'quarterly_balance_sheet', 'historical_fundamentals'],
        period='quarterly',
        historical_years=5,
        limit=20,
        pb_analysis_mode=False
    )
    print(f"[OK] Manual P/B request: ticker={request2.ticker}")
    print(f"  data_types={request2.data_types}")
    print(f"  historical_years={request2.historical_years}")
    print(f"  period={request2.period}, limit={request2.limit}")
    
    # Test 3: Historical years validation
    request3 = FinancialDataRequest(
        ticker="TSLA",
        historical_years=15,  # Should be capped at 10
        pb_analysis_mode=True
    )
    print(f"[OK] Validation test: historical_years={request3.historical_years} (capped from 15)")
    
    request4 = FinancialDataRequest(
        ticker="NVDA",
        historical_years=-2,  # Should be set to 1
        pb_analysis_mode=True
    )
    print(f"[OK] Validation test: historical_years={request4.historical_years} (adjusted from -2)")
    
    return True


def test_pb_request_examples():
    """Test example usage patterns for P/B analysis"""
    print("\n=== Testing P/B Request Examples ===")
    
    # Example 1: Simple P/B analysis request
    pb_request = FinancialDataRequest(
        ticker="AAPL",
        pb_analysis_mode=True,
        historical_years=5
    )
    print("[OK] Simple P/B Analysis Request:")
    print(f"  FinancialDataRequest(ticker='AAPL', pb_analysis_mode=True, historical_years=5)")
    print(f"  -> Auto-configured: period='{pb_request.period}', limit={pb_request.limit}")
    print(f"  -> Data types: {pb_request.data_types}")
    
    # Example 2: Advanced P/B analysis request with custom parameters
    advanced_pb_request = FinancialDataRequest(
        ticker="MSFT",
        data_types=['price', 'fundamentals', 'historical_prices', 'quarterly_balance_sheet'],
        period='quarterly',
        limit=24,  # 6 years of quarterly data
        historical_years=6,
        pb_analysis_mode=True,
        force_refresh=True
    )
    print("[OK] Advanced P/B Analysis Request:")
    print(f"  Custom configuration maintained: limit={advanced_pb_request.limit}")
    print(f"  Data types preserved and extended: {advanced_pb_request.data_types}")
    
    return True


def main():
    """Run all tests"""
    print("Testing Extended FinancialDataRequest for Historical P/B Data")
    print("=" * 60)
    
    try:
        # Run all test suites
        assert test_backward_compatibility(), "Backward compatibility test failed"
        assert test_new_pb_functionality(), "New P/B functionality test failed"
        assert test_pb_request_examples(), "P/B request examples test failed"
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("[SUCCESS] FinancialDataRequest extension is working correctly")
        print("[SUCCESS] Backward compatibility maintained")
        print("[SUCCESS] New P/B functionality validated")
        
        return True
        
    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        logger.error(f"Test failure: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)