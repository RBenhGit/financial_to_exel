#!/usr/bin/env python3

"""
Test date tracking with API data that has proper timestamps
"""

import sys
import os
from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.analysis.engines.financial_calculations import FinancialCalculator

def test_api_date_tracking():
    """Test date tracking with API data"""
    
    print("Testing API date tracking...")
    
    try:
        # Initialize enhanced data manager
        data_manager = CentralizedDataManager(".")
        
        # Try to get financial data for MSFT via API
        ticker = "MSFT"
        print(f"Fetching financial data for {ticker}...")
        
        financial_data, metadata, actual_source = data_manager.get_financial_data(ticker)
        
        if not financial_data:
            print("No financial data available from API")
            return False
            
        print(f"Got financial data from: {actual_source}")
        
        # Create financial calculator with API data
        calculator = FinancialCalculator(None, data_manager)
        calculator.financial_data = financial_data
        calculator._has_api_financial_data = True
        calculator._data_source_used = actual_source
        
        print(f"Calculator initialized with API data")
        print(f"data_point_dates initialized: {hasattr(calculator, 'data_point_dates')}")
        
        # Calculate FCF to trigger date tracking
        fcf_result = calculator.calculate_levered_fcf()
        print(f"FCF calculation successful: {len(fcf_result)} data points")
        
        # Check date tracking results
        print(f"data_point_dates populated: {bool(calculator.data_point_dates)}")
        print(f"actual_ltm_date_used: {calculator.actual_ltm_date_used}")
        
        # Show a sample of the data point dates
        if calculator.data_point_dates:
            for metric, dates in list(calculator.data_point_dates.items())[:2]:
                print(f"{metric} dates (first 3): {dates[:3] if len(dates) >= 3 else dates}")
        
        return True
        
    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api_date_tracking()