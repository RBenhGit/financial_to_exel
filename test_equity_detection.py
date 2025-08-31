#!/usr/bin/env python3
"""
Test script for enhanced equity field name detection functionality.
Tests the expanded equity_keywords list and improved matching logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analysis.pb.pb_valuation import PBValuator
import logging

# Configure logging for testing
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_equity_detection_variations():
    """Test equity detection with various naming conventions"""
    
    pb_calc = PBValuator("TEST")
    
    # Test different Excel naming conventions
    test_cases = [
        # Standard variations
        {"2023": {"Shareholders' Equity": 1000.5}},
        {"2023": {"Stockholders Equity": 2000.0}},
        {"2023": {"Total Equity": 3000.25}},
        {"2023": {"Book Value": 4000.75}},
        
        # International variations  
        {"2023": {"Shareowners Equity": 5000.0}},
        {"2023": {"Shareholders' Funds": 6000.5}},
        {"2023": {"Net Worth": 7000.25}},
        
        # Common equity variations
        {"2023": {"Common Equity": 8000.0}},
        {"2023": {"Common Stock Equity": 9000.5}},
        
        # Formatted/parenthetical variations
        {"2023": {"Equity (Total)": 10000.0}},
        {"2023": {"Total (Equity)": 11000.5}},
        {"2023": {"Shareholders Equity (Total)": 12000.25}},
        
        # Abbreviated variations
        {"2023": {"Sh Equity": 13000.0}},
        {"2023": {"Stk Equity": 14000.5}},
        
        # Complex naming
        {"2023": {"Equity Attributable to Shareholders": 15000.75}},
        {"2023": {"Total Equity Attributable to Stockholders": 16000.25}},
    ]
    
    print("\n=== Testing Equity Field Detection Variations ===")
    
    for i, test_data in enumerate(test_cases):
        expected_value = list(test_data.values())[0]
        expected_value = list(expected_value.values())[0]
        field_name = list(list(test_data.values())[0].keys())[0]
        
        result = pb_calc._extract_shareholders_equity(test_data)
        
        print(f"Test {i+1:2d}: {field_name:<40} -> ${result:.2f}M (Expected: ${expected_value:.2f}M)")
        
        if result is None:
            logger.error(f"Failed to detect equity in: {field_name}")
        elif abs(result - expected_value) > 0.01:
            logger.error(f"Value mismatch for {field_name}: got ${result:.2f}M, expected ${expected_value:.2f}M")
        else:
            logger.debug(f"✓ Successfully detected: {field_name}")

def test_false_positive_prevention():
    """Test that non-equity fields are properly filtered out"""
    
    pb_calc = PBValuator("TEST")
    
    # Test cases that should NOT match as equity
    false_positive_cases = [
        {"2023": {"Total Liabilities": 1000.0}},
        {"2023": {"Long-term Debt": 2000.0}},
        {"2023": {"Cash and Cash Equivalents": 3000.0}},
        {"2023": {"Total Assets": 4000.0}},
        {"2023": {"Accounts Payable": 5000.0}},
        {"2023": {"Revenue": 6000.0}},
        {"2023": {"Operating Income": 7000.0}},
    ]
    
    print("\n=== Testing False Positive Prevention ===")
    
    for i, test_data in enumerate(false_positive_cases):
        field_name = list(list(test_data.values())[0].keys())[0]
        result = pb_calc._extract_shareholders_equity(test_data)
        
        print(f"Test {i+1}: {field_name:<30} -> {result}")
        
        if result is not None:
            logger.warning(f"False positive detected for: {field_name}")
        else:
            logger.debug(f"✓ Correctly rejected: {field_name}")

def test_fuzzy_matching():
    """Test fuzzy matching functionality"""
    
    pb_calc = PBValuator("TEST")
    
    # Test cases with potential matches that need fuzzy logic
    fuzzy_test_cases = [
        {"2023": {"Total Stockholders' Equity (Note 15)": 1000.0}},
        {"2023": {"Shareholders Equity, Total": 2000.0}},
        {"2023": {"BOOK VALUE OF EQUITY": 3000.0}},
        {"2023": {"Net Worth (Shareholders)": 4000.0}},
    ]
    
    print("\n=== Testing Fuzzy Matching ===")
    
    for i, test_data in enumerate(fuzzy_test_cases):
        expected_value = list(test_data.values())[0]
        expected_value = list(expected_value.values())[0]
        field_name = list(list(test_data.values())[0].keys())[0]
        
        result = pb_calc._extract_shareholders_equity(test_data)
        
        print(f"Test {i+1}: {field_name:<45} -> ${result:.2f}M" if result else f"Test {i+1}: {field_name:<45} -> No match")
        
        if result is None:
            logger.warning(f"Fuzzy matching failed for: {field_name}")
        else:
            logger.debug(f"✓ Fuzzy match successful: {field_name}")

if __name__ == "__main__":
    print("Testing Enhanced Equity Field Detection")
    print("=" * 60)
    
    try:
        test_equity_detection_variations()
        test_false_positive_prevention() 
        test_fuzzy_matching()
        
        print("\n" + "=" * 60)
        print("✓ All equity detection tests completed!")
        print("Check the output above for any warnings or errors.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()