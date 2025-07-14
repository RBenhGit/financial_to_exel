#!/usr/bin/env python3
"""
Debug FCF Algorithm - Root Cause Analysis

This script analyzes the FCF calculation algorithm to identify the root causes
of N/A values in year 9 and other potential year misalignment issues.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from financial_calculations import FinancialCalculator
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_data_lengths_and_alignment():
    """
    Analyze data lengths and alignment issues across all sample companies
    """
    companies = ['MSFT', 'GOOG', 'TSLA', 'NVDA', 'V']
    
    for company in companies:
        company_folder = os.path.join(os.path.dirname(__file__), company)
        if not os.path.exists(company_folder):
            logger.warning(f"Company folder not found: {company}")
            continue
        
        print(f"\n" + "="*60)
        print(f"ANALYZING {company} - DATA LENGTH AND ALIGNMENT")
        print("="*60)
        
        try:
            # Initialize calculator
            calc = FinancialCalculator(company_folder)
            calc.set_validation_enabled(False)  # Disable validation for faster debugging
            
            # Load financial statements
            calc.load_financial_statements()
            
            # Get metrics
            metrics = calc._calculate_all_metrics()
            
            if not metrics:
                print(f"❌ No metrics calculated for {company}")
                continue
            
            # Analyze data lengths
            print("\n📊 RAW DATA LENGTHS:")
            print("-" * 40)
            for metric_name, values in metrics.items():
                if isinstance(values, list):
                    print(f"{metric_name:25}: {len(values):2} values")
            
            # Identify the root cause of misalignment
            print("\n🔍 ALIGNMENT ANALYSIS:")
            print("-" * 40)
            
            # Check base financial data lengths
            base_metrics = ['ebit', 'net_income', 'current_assets', 'current_liabilities', 
                          'depreciation_amortization', 'operating_cash_flow', 'capex']
            
            base_lengths = {}
            for metric in base_metrics:
                if metric in metrics and metrics[metric]:
                    base_lengths[metric] = len(metrics[metric])
            
            # Find the reference length (should be 10 for FY+LTM)
            if base_lengths:
                max_length = max(base_lengths.values())
                min_length = min(base_lengths.values())
                print(f"Base data length range: {min_length} to {max_length}")
                
                if max_length != min_length:
                    print("❌ INCONSISTENT BASE DATA LENGTHS!")
                    for metric, length in base_lengths.items():
                        if length != max_length:
                            print(f"  - {metric}: {length} (expected {max_length})")
                else:
                    print(f"✅ Consistent base data length: {max_length}")
            
            # Check working capital changes length
            wc_changes = metrics.get('working_capital_changes', [])
            wc_length = len(wc_changes)
            expected_wc_length = max_length - 1 if base_lengths else 0
            
            print(f"\nWorking Capital Changes:")
            print(f"  Actual length: {wc_length}")
            print(f"  Expected length: {expected_wc_length} (base_length - 1)")
            
            if wc_length != expected_wc_length:
                print("❌ WORKING CAPITAL LENGTH MISMATCH!")
            else:
                print("✅ Working capital length correct")
            
            # Check FCF calculation impact
            print(f"\n⚙️ FCF CALCULATION ANALYSIS:")
            print("-" * 40)
            
            # Simulate FCFF calculation
            ebit_values = metrics.get('ebit', [])
            tax_rates = metrics.get('tax_rates', [])
            da_values = metrics.get('depreciation_amortization', [])
            capex_values = metrics.get('capex', [])
            working_capital_changes = metrics.get('working_capital_changes', [])
            
            fcf_components = {
                'ebit': len(ebit_values),
                'tax_rates': len(tax_rates),
                'da_values': len(da_values),
                'capex_values': len(capex_values),
                'working_capital_changes': len(working_capital_changes)
            }
            
            print("FCF Component lengths:")
            for component, length in fcf_components.items():
                print(f"  {component:25}: {length}")
            
            min_fcf_length = min(fcf_components.values()) if fcf_components.values() else 0
            print(f"\nMinimum FCF component length: {min_fcf_length}")
            print(f"This means FCF can be calculated for {min_fcf_length} years")
            
            # Identify the bottleneck
            bottleneck_components = [comp for comp, length in fcf_components.items() 
                                   if length == min_fcf_length]
            print(f"Bottleneck component(s): {', '.join(bottleneck_components)}")
            
            # Check if year 9 would be missing
            if min_fcf_length < 9:
                print(f"❌ YEAR 9 ISSUE CONFIRMED: Only {min_fcf_length} years available, year 9 would be N/A")
            else:
                print(f"✅ Year 9 should be available ({min_fcf_length} years total)")
            
            # Test actual FCF calculation
            print(f"\n🧪 ACTUAL FCF CALCULATION TEST:")
            print("-" * 40)
            try:
                fcff_result = calc.calculate_fcf_to_firm()
                fcfe_result = calc.calculate_fcf_to_equity()
                lfcf_result = calc.calculate_levered_fcf()
                
                print(f"FCFF calculated years: {len(fcff_result)}")
                print(f"FCFE calculated years: {len(fcfe_result)}")
                print(f"LFCF calculated years: {len(lfcf_result)}")
                
                # Check for N/A values in year 9 (index 8)
                for fcf_type, values in [('FCFF', fcff_result), ('FCFE', fcfe_result), ('LFCF', lfcf_result)]:
                    if len(values) > 8:
                        year9_value = values[8]
                        print(f"{fcf_type} Year 9 value: {year9_value}")
                    else:
                        print(f"❌ {fcf_type} Year 9: N/A (insufficient data)")
                        
            except Exception as e:
                print(f"❌ FCF calculation failed: {e}")
            
        except Exception as e:
            print(f"❌ Analysis failed for {company}: {e}")
            import traceback
            traceback.print_exc()

def analyze_ltm_integration_impact():
    """
    Analyze how LTM data integration affects array lengths
    """
    print(f"\n" + "="*60)
    print("LTM INTEGRATION IMPACT ANALYSIS")
    print("="*60)
    
    company_folder = os.path.join(os.path.dirname(__file__), 'MSFT')
    
    try:
        calc = FinancialCalculator(company_folder)
        calc.set_validation_enabled(False)
        calc.load_financial_statements()
        
        # Simulate the _extract_metric_with_ltm logic manually
        income_data = calc.financial_data.get('income_fy', None)
        income_ltm = calc.financial_data.get('income_ltm', None)
        
        if income_data is None or income_ltm is None:
            print("❌ Could not load income data")
            return
        
        # Test metric extraction
        fy_ebit = calc._extract_metric_values(income_data, "EBIT", reverse=True)
        ltm_ebit = calc._extract_metric_values(income_ltm, "EBIT", reverse=True) if not income_ltm.empty else []
        
        print(f"FY EBIT length: {len(fy_ebit)}")
        print(f"LTM EBIT length: {len(ltm_ebit)}")
        
        # Simulate the combination logic
        if fy_ebit and ltm_ebit:
            combined_ebit = fy_ebit[:-1] + [ltm_ebit[-1]]
            print(f"Combined EBIT length: {len(combined_ebit)} (FY historical + LTM latest)")
            print(f"LTM replacement: FY[{len(fy_ebit)-1}] = {fy_ebit[-1]} → LTM = {ltm_ebit[-1]}")
        
        # Test balance sheet data for working capital
        balance_data = calc.financial_data.get('balance_fy', None)
        balance_ltm = calc.financial_data.get('balance_ltm', None)
        
        if balance_data is not None:
            fy_current_assets = calc._extract_metric_values(balance_data, "Total Current Assets", reverse=True)
            ltm_current_assets = calc._extract_metric_values(balance_ltm, "Total Current Assets", reverse=True) if not balance_ltm.empty else []
            
            print(f"\nFY Current Assets length: {len(fy_current_assets)}")
            print(f"LTM Current Assets length: {len(ltm_current_assets)}")
            
            if fy_current_assets and ltm_current_assets:
                combined_assets = fy_current_assets[:-1] + [ltm_current_assets[-1]]
                print(f"Combined Current Assets length: {len(combined_assets)}")
                
                # Working capital changes calculation
                if len(combined_assets) >= 2:
                    wc_changes_length = len(combined_assets) - 1
                    print(f"Working capital changes length: {wc_changes_length}")
                    print(f"This explains why WC changes has {wc_changes_length} years while base data has {len(combined_assets)}")
        
    except Exception as e:
        print(f"❌ LTM analysis failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    Main analysis function
    """
    print("🔍 FCF ALGORITHM ROOT CAUSE ANALYSIS")
    print("="*60)
    
    analyze_data_lengths_and_alignment()
    analyze_ltm_integration_impact()
    
    print(f"\n" + "="*60)
    print("SUMMARY AND RECOMMENDATIONS")
    print("="*60)
    
    print("""
ROOT CAUSE IDENTIFIED:
1. Working capital changes calculation uses (current_year - previous_year), 
   so it produces N-1 years compared to base financial data
2. Base financial data has 10 years (FY historical + LTM latest)
3. Working capital changes has 9 years (10 - 1)
4. FCF calculation uses min() of all component lengths
5. Therefore, FCF calculations are limited to 9 years maximum

ALGORITHMIC FIX RECOMMENDATIONS:
1. Adjust FCF indexing to properly align with working capital changes
2. Consider adding a zero working capital change for the first year
3. Or modify FCF calculation to handle the length mismatch properly
4. Ensure LTM integration doesn't create additional alignment issues

SPECIFIC CODE CHANGES NEEDED:
- Fix min_length calculation in FCF methods
- Handle array length mismatches gracefully
- Add validation for component alignment
""")

if __name__ == "__main__":
    main()