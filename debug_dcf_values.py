#!/usr/bin/env python3
"""
Debug script to analyze DCF value scaling issues
"""

import pandas as pd
from pathlib import Path

def get_financial_scale_and_unit(value, already_in_millions=True):
    """
    Test version of the scaling function
    """
    print(f"Input: value={value}, already_in_millions={already_in_millions}")
    
    # If value is already in millions, convert back to raw currency for proper scaling
    if already_in_millions:
        raw_value = value * 1e6
        print(f"Converting from millions: {value} * 1e6 = {raw_value}")
    else:
        raw_value = value
        print(f"Using raw value: {raw_value}")
    
    abs_value = abs(raw_value)
    print(f"Absolute value for comparison: {abs_value}")
    
    if abs_value >= 1e12:  # Trillions
        result = raw_value / 1e12, "Trillions USD", "T"
        print(f"Scaling to trillions: {raw_value} / 1e12 = {result[0]}")
        return result
    elif abs_value >= 1e9:  # Billions
        result = raw_value / 1e9, "Billions USD", "B"
        print(f"Scaling to billions: {raw_value} / 1e9 = {result[0]}")
        return result
    elif abs_value >= 1e6:  # Millions
        result = raw_value / 1e6, "Millions USD", "M"
        print(f"Scaling to millions: {raw_value} / 1e6 = {result[0]}")
        return result
    elif abs_value >= 1e3:  # Thousands
        result = raw_value / 1e3, "Thousands USD", "K"
        print(f"Scaling to thousands: {raw_value} / 1e3 = {result[0]}")
        return result
    else:
        result = raw_value, "USD", ""
        print(f"No scaling needed: {raw_value}")
        return result

def analyze_csv_values():
    """Analyze the values from the actual CSV file"""
    csv_path = "exports/MSFT_DCF_Analysis_Enhanced_20250724_215809.csv"
    
    print("=== ANALYZING CSV VALUES ===")
    
    # Read the CSV and extract the problematic values
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    
    # Find the enterprise value line
    for line in lines:
        if '"Enterprise Value"' in line:
            parts = line.strip().split(',')
            ev_value = float(parts[1])
            ev_unit = parts[2].strip('"')
            print(f"CSV Enterprise Value: {ev_value} {ev_unit}")
            
            # What should this value be if it was correctly scaled?
            # Based on the FCF projections, this should be in trillions
            # From the CSV: individual FCFs are ~100B each, so total should be ~1-3T
            expected_raw_value = 3.487e12  # 3.487 trillion
            print(f"Expected raw value: {expected_raw_value}")
            
            # Test the scaling function
            print("\n--- Testing scaling with expected value ---")
            scaled, unit, abbrev = get_financial_scale_and_unit(expected_raw_value, already_in_millions=False)
            print(f"Scaled result: {scaled} {unit}")
            
            # Test with the incorrect CSV value
            print("\n--- Testing scaling with CSV value (treating as raw) ---")
            scaled2, unit2, abbrev2 = get_financial_scale_and_unit(ev_value, already_in_millions=False)
            print(f"Scaled result: {scaled2} {unit2}")
            
            break

if __name__ == "__main__":
    analyze_csv_values()