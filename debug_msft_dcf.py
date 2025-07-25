#!/usr/bin/env python3
"""
Debug the MSFT DCF values by reading the existing CSV and examining what created them
"""

import re
from pathlib import Path

def analyze_msft_dcf_csv():
    """Analyze the MSFT DCF CSV to understand the values"""
    
    csv_path = "exports/MSFT_DCF_Analysis_Enhanced_20250724_215809.csv"
    
    if not Path(csv_path).exists():
        print(f"CSV file not found: {csv_path}")
        return
    
    print("=== ANALYZING MSFT DCF CSV FILE ===")
    
    with open(csv_path, 'r') as f:
        content = f.read()
    
    print("\n--- ENTERPRISE VALUE INVESTIGATION ---")
    
    # Find the Enterprise Value line
    ev_match = re.search(r'"Enterprise Value",([0-9.]+),"([^"]+)"', content)
    if ev_match:
        ev_value = float(ev_match.group(1))
        ev_unit = ev_match.group(2)
        print(f"CSV Enterprise Value: {ev_value} {ev_unit}")
        
        # This should be trillions for Microsoft, but it's showing millions
        # Let's see what the projection values are
        
        print("\n--- PROJECTED FCF VALUES ---")
        # Find all the projection lines
        projection_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),MSFT,Microsoft Corporation,FCFE,(\d+),([0-9,]+\.\d+),[0-9.%]+,([0-9,]+\.\d+),[0-9.]+'
        
        projections = re.findall(projection_pattern, content)
        total_pv = 0
        
        for i, (date, year, projected_fcf, pv_fcf, discount_factor) in enumerate(projections):
            projected_fcf_num = float(projected_fcf.replace(',', ''))
            pv_fcf_num = float(pv_fcf.replace(',', ''))
            
            print(f"Year {year}: Projected FCF ${projected_fcf_num/1e6:.0f}M → PV ${pv_fcf_num/1e6:.0f}M")
            total_pv += pv_fcf_num
        
        print(f"\nTotal PV of FCF: ${total_pv/1e9:.1f}B")
        
        # Find terminal value
        terminal_match = re.search(r'"Terminal Value",([0-9.]+),"([^"]+)"', content)
        if terminal_match:
            terminal_value = float(terminal_match.group(1))
            terminal_unit = terminal_match.group(2)
            print(f"Terminal Value: {terminal_value} {terminal_unit}")
            
            if terminal_unit == "Millions USD":
                terminal_actual = terminal_value * 1e6
            else:
                terminal_actual = terminal_value
                
            print(f"Terminal Value (actual): ${terminal_actual/1e9:.1f}B")
            
            # The total equity value should be PV of FCF + Terminal Value
            total_expected = total_pv + terminal_actual
            print(f"\nExpected Total Equity Value: ${(total_pv + terminal_actual)/1e12:.3f}T")
            print(f"CSV Enterprise Value: {ev_value} {ev_unit}")
            
            # The discrepancy suggests a scaling error
            if ev_unit == "Millions USD":
                scaling_error = (total_pv + terminal_actual) / (ev_value * 1e6)
                print(f"Scaling Error Factor: {scaling_error:,.0f}x")
                print(f"The actual DCF calculation appears to be {scaling_error:,.0f} times larger than what's exported")

if __name__ == "__main__":
    analyze_msft_dcf_csv()