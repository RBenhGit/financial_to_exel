#!/usr/bin/env python3

"""
Test complete date integration flow with mock data that has proper dates
"""

import pandas as pd
from core.data_processing.processors.data_processing import DataProcessor

def test_date_integration():
    """Test the complete date integration flow"""
    
    print("Testing complete date integration flow...")
    
    # Create mock FCF results
    fcf_results = {
        'FCFF': [100, 110, 120, 130],
        'FCFE': [90, 100, 110, 120],
        'LFCF': [95, 105, 115, 125]
    }
    
    # Create mock data point dates
    data_point_dates = {
        'FCFF': ['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31'],
        'FCFE': ['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31'],
        'LFCF': ['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31']
    }
    
    # Test data processor
    processor = DataProcessor()
    
    print("Testing prepare_fcf_data with data_point_dates...")
    fcf_data = processor.prepare_fcf_data(
        fcf_results, 
        data_point_dates=data_point_dates
    )
    
    print("Results:")
    print(f"  Years: {fcf_data.get('years')}")
    print(f"  Actual dates: {fcf_data.get('actual_dates')}")
    print(f"  Data point dates preserved: {fcf_data.get('data_point_dates') is not None}")
    
    # Test plotting with dates
    print("\nTesting plotting with actual dates...")
    try:
        fig = processor.create_fcf_comparison_plot(
            fcf_results, 
            company_name="Test Company",
            data_point_dates=data_point_dates
        )
        print("  FCF comparison plot created successfully")
        
        avg_fig = processor.create_average_fcf_plot(
            fcf_results,
            company_name="Test Company", 
            data_point_dates=data_point_dates
        )
        print("  Average FCF plot created successfully")
        
        # Check if the plots use actual dates
        has_date_traces = any(
            '2020-12-31' in str(trace.x) or '2021-12-31' in str(trace.x) 
            for trace in fig.data
        )
        print(f"  Plots use actual dates: {has_date_traces}")
        
    except Exception as e:
        print(f"  Error creating plots: {e}")
        return False
    
    print("\n✅ Date integration test completed successfully!")
    return True

if __name__ == "__main__":
    test_date_integration()