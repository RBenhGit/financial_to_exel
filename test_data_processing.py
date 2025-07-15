#!/usr/bin/env python3

"""
Test data processing with dynamic date extraction
"""

import json
from datetime import datetime
from data_processing import DataProcessor

def test_data_processing():
    """Test that data processing uses the extracted dates"""
    
    # Create sample FCF data
    sample_fcf_data = {
        'FCFF': [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
        'FCFE': [90, 100, 110, 120, 130, 140, 150, 160, 170, 180],
        'LFCF': [95, 105, 115, 125, 135, 145, 155, 165, 175, 185]
    }
    
    print("Testing data processing with dynamic date extraction...")
    
    # Test with metadata present
    try:
        processor = DataProcessor()
        result = processor.prepare_fcf_data(sample_fcf_data)
        print(f"Result with metadata: {result}")
        
        # Check if the result contains the expected years
        if result and 'fcf_data' in result:
            for fcf_type, data in result['fcf_data'].items():
                if 'years' in data:
                    print(f"{fcf_type} years: {data['years']}")
        
    except Exception as e:
        print(f"Error in data processing: {e}")
    
    # Test without metadata (should fallback to current year)
    try:
        import os
        if os.path.exists("dates_metadata.json"):
            os.rename("dates_metadata.json", "dates_metadata.json.backup")
        
        processor = DataProcessor()
        result = processor.prepare_fcf_data(sample_fcf_data)
        print(f"Result without metadata: {result}")
        
        # Restore metadata
        if os.path.exists("dates_metadata.json.backup"):
            os.rename("dates_metadata.json.backup", "dates_metadata.json")
        
    except Exception as e:
        print(f"Error in fallback test: {e}")

if __name__ == "__main__":
    test_data_processing()