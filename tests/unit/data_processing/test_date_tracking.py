#!/usr/bin/env python3

"""
Quick test to verify date tracking functionality is working correctly
"""

import sys
import os
from core.analysis.engines.financial_calculations import FinancialCalculator

def test_date_tracking():
    """Test the new date tracking functionality"""
    
    print("Testing date tracking with GOOG data...")
    
    # Initialize calculator
    calculator = FinancialCalculator("GOOG")
    
    # Check if data_point_dates attribute exists
    print(f"data_point_dates attribute exists: {hasattr(calculator, 'data_point_dates')}")
    print(f"actual_ltm_date_used attribute exists: {hasattr(calculator, 'actual_ltm_date_used')}")
    
    # Calculate some FCF to trigger date tracking
    try:
        fcf_result = calculator.calculate_levered_fcf()
        print(f"FCF calculation successful: {len(fcf_result)} data points")
        
        # Check if date tracking was populated
        print(f"data_point_dates populated: {bool(calculator.data_point_dates)}")
        print(f"data_point_dates content: {calculator.data_point_dates}")
        
        print(f"actual_ltm_date_used: {calculator.actual_ltm_date_used}")
        
    except Exception as e:
        print(f"Error during FCF calculation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_date_tracking()