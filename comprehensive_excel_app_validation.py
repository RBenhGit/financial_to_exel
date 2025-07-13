#!/usr/bin/env python3
"""
Comprehensive Excel vs App Validation
1. Data Integrity: Compare Data Entry tab inputs with App extracted data
2. Calculation Methodology: Compare FCF DATA tab calculations with App calculations
"""

import pandas as pd
import numpy as np
import openpyxl
from financial_calculations import FinancialCalculator

def extract_data_entry_inputs(excel_path, company_name):
    """Extract historical financial data from Data Entry tab"""
    print(f"\n📊 EXTRACTING DATA ENTRY INPUTS: {company_name}")
    print("=" * 60)
    
    try:
        # Read Data Entry sheet
        data_entry = pd.read_excel(excel_path, sheet_name='Data Entry')
        print(f"Data Entry sheet shape: {data_entry.shape}")
        print(f"Columns: {list(data_entry.columns)}")
        
        # Look for financial statement data
        extracted_data = {}
        
        # Search for key financial metrics in the sheet
        financial_metrics = [
            'Revenue', 'Net Income', 'EBIT', 'Operating Cash Flow', 
            'Capital Expenditure', 'CapEx', 'Current Assets', 'Current Liabilities',
            'Depreciation', 'Amortization', 'Tax', 'Interest'
        ]
        
        for idx, row in data_entry.iterrows():
            if idx > 50:  # Limit search
                break
                
            # Check first column for metric names
            first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            
            for metric in financial_metrics:
                if metric.lower() in first_col.lower():
                    # Extract values from subsequent columns
                    values = []
                    years = []
                    
                    # Look for year headers (usually in a row above or same row)
                    for col_idx in range(1, min(len(row), 15)):
                        val = row.iloc[col_idx]
                        if pd.notna(val) and isinstance(val, (int, float)) and abs(val) > 1:
                            values.append(float(val))
                    
                    if values and len(values) >= 3:
                        extracted_data[first_col] = {
                            'values': values,
                            'row_index': idx,
                            'metric_type': metric
                        }
                        print(f"   📈 {first_col}: {values[:5]}..." if len(values) > 5 else f"   📈 {first_col}: {values}")
        
        return extracted_data
        
    except Exception as e:
        print(f"❌ Error extracting Data Entry: {e}")
        return {}

def extract_fcf_data_calculations(excel_path, company_name):
    """Extract FCF calculations from FCF DATA tab"""
    print(f"\n📊 EXTRACTING FCF DATA CALCULATIONS: {company_name}")
    print("=" * 60)
    
    try:
        fcf_data = pd.read_excel(excel_path, sheet_name='FCF DATA', header=None)
        print(f"FCF DATA sheet shape: {fcf_data.shape}")
        
        calculations = {}
        
        # Extract year-by-year FCF calculations (rows 3-12 based on previous analysis)
        years = []
        operating_cf = []
        capex = []
        fcf_values = []
        
        print("\n📋 Extracting FCF calculation details:")
        for i in range(2, min(12, len(fcf_data))):  # Rows 3-12
            row_data = fcf_data.iloc[i]
            
            if pd.notna(row_data.iloc[0]):  # Year
                year = row_data.iloc[0]
                op_cf = row_data.iloc[2] if pd.notna(row_data.iloc[2]) else 0  # Operating CF
                capex_val = row_data.iloc[3] if pd.notna(row_data.iloc[3]) else 0  # CapEx
                fcf_val = row_data.iloc[4] if pd.notna(row_data.iloc[4]) else 0  # FCF
                
                # Convert string values with commas
                if isinstance(op_cf, str):
                    op_cf = float(op_cf.replace(',', ''))
                if isinstance(capex_val, str):
                    capex_val = float(capex_val.replace(',', ''))
                if isinstance(fcf_val, (str, int, float)):
                    if isinstance(fcf_val, str):
                        fcf_val = float(fcf_val.replace(',', '')) if ',' in fcf_val else float(fcf_val)
                    else:
                        fcf_val = float(fcf_val)
                
                years.append(int(year))
                operating_cf.append(float(op_cf))
                capex.append(float(capex_val))
                fcf_values.append(fcf_val)
                
                print(f"   {int(year)}: Op CF ${op_cf:,.0f}, CapEx ${capex_val:,.0f}, FCF ${fcf_val:,.0f}")
        
        calculations['LFCF'] = {
            'years': years,
            'operating_cf': operating_cf,
            'capex': capex,
            'fcf_calculated': fcf_values,
            'method': 'Operating CF - CapEx'
        }
        
        # Look for other FCF calculations in the sheet
        print("\n🔍 Searching for other FCF methodologies...")
        for i in range(len(fcf_data)):
            if i > 50:  # Limit search
                break
            
            first_cell = str(fcf_data.iloc[i, 0]).lower() if pd.notna(fcf_data.iloc[i, 0]) else ""
            
            if any(term in first_cell for term in ['fcff', 'fcfe', 'levered', 'unlevered', 'firm', 'equity']):
                print(f"   📍 Found FCF-related calculation: {fcf_data.iloc[i, 0]}")
                
                # Try to extract associated values
                values = []
                for col in range(1, min(12, fcf_data.shape[1])):
                    val = fcf_data.iloc[i, col]
                    if pd.notna(val) and isinstance(val, (int, float)) and abs(val) > 100:
                        values.append(float(val))
                
                if values:
                    print(f"      Values: {values[:8]}")
        
        return calculations
        
    except Exception as e:
        print(f"❌ Error extracting FCF DATA: {e}")
        return {}

def get_app_calculations(company_folder, company_name):
    """Get app calculations and underlying data"""
    print(f"\n🤖 GETTING APP CALCULATIONS: {company_name}")
    print("=" * 60)
    
    try:
        calc = FinancialCalculator(company_folder)
        calc.load_financial_statements()
        
        # Get all metrics
        metrics = calc._calculate_all_metrics()
        
        # Calculate FCF
        lfcf_values = calc.calculate_levered_fcf()
        fcff_values = calc.calculate_fcf_to_firm()
        fcfe_values = calc.calculate_fcf_to_equity()
        
        app_data = {
            'LFCF': {
                'values': lfcf_values,
                'method': 'Operating CF - CapEx'
            },
            'FCFF': {
                'values': fcff_values,
                'method': 'EBIT(1-Tax) + D&A - ΔWC - CapEx'
            },
            'FCFE': {
                'values': fcfe_values,
                'method': 'NI + D&A - ΔWC - CapEx + Net Borrowing'
            },
            'underlying_metrics': {
                'operating_cash_flow': metrics.get('operating_cash_flow', []),
                'capex': metrics.get('capex', []),
                'ebit': metrics.get('ebit', []),
                'net_income': metrics.get('net_income', []),
                'tax_rates': metrics.get('tax_rates', []),
                'depreciation_amortization': metrics.get('depreciation_amortization', []),
                'working_capital_changes': metrics.get('working_capital_changes', []),
                'net_borrowing': metrics.get('net_borrowing', [])
            }
        }
        
        print(f"📊 App FCF Results:")
        print(f"   LFCF: {len(lfcf_values)} years - {lfcf_values}")
        print(f"   FCFF: {len(fcff_values)} years - {fcff_values}")
        print(f"   FCFE: {len(fcfe_values)} years - {fcfe_values}")
        
        print(f"\n📊 App Underlying Data:")
        print(f"   Operating CF: {metrics.get('operating_cash_flow', [])}")
        print(f"   CapEx: {metrics.get('capex', [])}")
        
        return app_data
        
    except Exception as e:
        print(f"❌ Error getting app calculations: {e}")
        import traceback
        traceback.print_exc()
        return {}

def validate_data_integrity(data_entry_data, app_data, company_name):
    """Validate that app extracted the same data as shown in Data Entry"""
    print(f"\n✅ DATA INTEGRITY VALIDATION: {company_name}")
    print("=" * 60)
    
    app_metrics = app_data.get('underlying_metrics', {})
    
    # Compare key financial metrics
    comparisons = []
    
    # Operating Cash Flow comparison
    app_operating_cf = app_metrics.get('operating_cash_flow', [])
    excel_operating_cf = None
    
    for key, data in data_entry_data.items():
        if 'operating' in key.lower() and 'cash' in key.lower():
            excel_operating_cf = data['values']
            break
    
    if excel_operating_cf and app_operating_cf:
        print(f"🔍 Operating Cash Flow Comparison:")
        print(f"   Excel (Data Entry): {excel_operating_cf}")
        print(f"   App Extracted:      {list(reversed(app_operating_cf))}")  # App is newest-first
        
        # Compare alignment
        app_reversed = list(reversed(app_operating_cf))
        min_len = min(len(excel_operating_cf), len(app_reversed))
        
        matches = 0
        for i in range(min_len):
            diff = abs(excel_operating_cf[i] - app_reversed[i])
            if diff < 1000:  # Allow for rounding
                matches += 1
        
        match_pct = (matches / min_len) * 100 if min_len > 0 else 0
        print(f"   Match: {matches}/{min_len} ({match_pct:.1f}%)")
        
        comparisons.append({
            'metric': 'Operating Cash Flow',
            'match_percentage': match_pct,
            'status': '✅ MATCH' if match_pct >= 90 else '❌ MISMATCH'
        })
    
    # CapEx comparison
    app_capex = app_metrics.get('capex', [])
    excel_capex = None
    
    for key, data in data_entry_data.items():
        if 'capex' in key.lower() or 'capital expenditure' in key.lower():
            excel_capex = data['values']
            break
    
    if excel_capex and app_capex:
        print(f"\n🔍 CapEx Comparison:")
        print(f"   Excel (Data Entry): {excel_capex}")
        print(f"   App Extracted:      {list(reversed(app_capex))}")
        
        app_reversed = list(reversed(app_capex))
        min_len = min(len(excel_capex), len(app_reversed))
        
        matches = 0
        for i in range(min_len):
            diff = abs(abs(excel_capex[i]) - abs(app_reversed[i]))  # Compare absolute values
            if diff < 1000:
                matches += 1
        
        match_pct = (matches / min_len) * 100 if min_len > 0 else 0
        print(f"   Match: {matches}/{min_len} ({match_pct:.1f}%)")
        
        comparisons.append({
            'metric': 'CapEx',
            'match_percentage': match_pct,
            'status': '✅ MATCH' if match_pct >= 90 else '❌ MISMATCH'
        })
    
    return comparisons

def validate_calculation_methodology(fcf_calculations, app_data, company_name):
    """Validate FCF calculation methodology between Excel and App"""
    print(f"\n✅ CALCULATION METHODOLOGY VALIDATION: {company_name}")
    print("=" * 60)
    
    results = {}
    
    # LFCF Calculation Validation
    excel_lfcf = fcf_calculations.get('LFCF', {})
    app_lfcf = app_data.get('LFCF', {})
    
    if excel_lfcf and app_lfcf:
        print(f"🧮 LFCF Calculation Validation:")
        print(f"   Method: {excel_lfcf.get('method', 'Operating CF - CapEx')}")
        
        excel_years = excel_lfcf.get('years', [])
        excel_op_cf = excel_lfcf.get('operating_cf', [])
        excel_capex = excel_lfcf.get('capex', [])
        excel_fcf = excel_lfcf.get('fcf_calculated', [])
        
        app_lfcf_values = app_lfcf.get('values', [])
        app_reversed = list(reversed(app_lfcf_values))  # App is newest-first
        
        print(f"\n📊 Year-by-Year LFCF Validation:")
        matches = 0
        total_years = min(len(excel_fcf), len(app_reversed))
        
        for i in range(total_years):
            excel_val = excel_fcf[i]
            app_val = app_reversed[i]
            diff = abs(excel_val - app_val)
            diff_pct = (diff / abs(excel_val)) * 100 if excel_val != 0 else 0
            
            # Manual calculation from Excel components
            manual_calc = excel_op_cf[i] - abs(excel_capex[i])
            manual_diff = abs(excel_val - manual_calc)
            
            year = excel_years[i] if i < len(excel_years) else f"Year {i+1}"
            
            print(f"   {year}:")
            print(f"      Excel LFCF: ${excel_val:,.0f}")
            print(f"      App LFCF:   ${app_val:,.0f}")
            print(f"      Manual calc: ${excel_op_cf[i]:,.0f} - ${abs(excel_capex[i]):,.0f} = ${manual_calc:,.0f}")
            print(f"      Excel vs App diff: ${diff:,.0f} ({diff_pct:.2f}%)")
            print(f"      Excel vs Manual diff: ${manual_diff:,.0f}")
            
            if diff < 1000 or diff_pct < 1:
                matches += 1
                print(f"      Status: ✅ MATCH")
            else:
                print(f"      Status: ❌ MISMATCH")
        
        match_percentage = (matches / total_years) * 100 if total_years > 0 else 0
        results['LFCF'] = {
            'matches': matches,
            'total': total_years,
            'match_percentage': match_percentage,
            'status': '✅ VALIDATED' if match_percentage >= 90 else '❌ VALIDATION FAILED'
        }
        
        print(f"\n🎯 LFCF Summary: {matches}/{total_years} matches ({match_percentage:.1f}%)")
        print(f"   Status: {results['LFCF']['status']}")
    
    # FCFF/FCFE Validation (if Excel data available)
    for fcf_type in ['FCFF', 'FCFE']:
        if fcf_type in fcf_calculations:
            print(f"\n🧮 {fcf_type} Calculation Found in Excel")
            # Additional validation logic here if Excel has FCFF/FCFE
        else:
            print(f"\n⚠️ {fcf_type}: No Excel calculation found for comparison")
            results[fcf_type] = {
                'status': 'No Excel comparison available',
                'note': 'Excel contains projections only'
            }
    
    return results

def generate_comprehensive_report(company_name, data_integrity_results, calculation_results):
    """Generate comprehensive validation report"""
    print(f"\n📋 COMPREHENSIVE VALIDATION REPORT: {company_name}")
    print("=" * 80)
    
    print("🔍 DATA INTEGRITY RESULTS:")
    for comparison in data_integrity_results:
        metric = comparison['metric']
        status = comparison['status']
        match_pct = comparison['match_percentage']
        print(f"   {metric}: {status} ({match_pct:.1f}% match)")
    
    print("\n🧮 CALCULATION METHODOLOGY RESULTS:")
    for fcf_type, result in calculation_results.items():
        if isinstance(result, dict) and 'status' in result:
            print(f"   {fcf_type}: {result['status']}")
            if 'match_percentage' in result:
                print(f"      Match rate: {result['match_percentage']:.1f}%")
    
    # Overall assessment
    data_integrity_good = all(comp['match_percentage'] >= 90 for comp in data_integrity_results)
    calculation_good = any(res.get('match_percentage', 0) >= 90 for res in calculation_results.values() if isinstance(res, dict))
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   Data Integrity: {'✅ VALIDATED' if data_integrity_good else '⚠️ ISSUES FOUND'}")
    print(f"   Calculation Accuracy: {'✅ VALIDATED' if calculation_good else '⚠️ PARTIAL VALIDATION'}")
    
    if data_integrity_good and calculation_good:
        print(f"   Final Status: ✅ APP FULLY VALIDATED AGAINST EXCEL")
    else:
        print(f"   Final Status: ⚠️ VALIDATION ISSUES REQUIRE ATTENTION")

def main():
    print("🚀 COMPREHENSIVE EXCEL vs APP VALIDATION")
    print("=" * 80)
    print("Validating both data integrity and calculation methodology")
    
    # Focus on GOOG for detailed validation
    company = "GOOG"
    excel_path = "/mnt/c/AsusWebStorage/ran@benhur.co/MySyncFolder/python/investingAnalysis/financial_to_exel/GOOG/FCF_Analysis_Alphabet Inc Class C.xlsx"
    company_folder = "/mnt/c/AsusWebStorage/ran@benhur.co/MySyncFolder/python/investingAnalysis/financial_to_exel/GOOG"
    
    # 1. Extract Data Entry inputs
    data_entry_data = extract_data_entry_inputs(excel_path, company)
    
    # 2. Extract FCF DATA calculations
    fcf_calculations = extract_fcf_data_calculations(excel_path, company)
    
    # 3. Get App calculations
    app_data = get_app_calculations(company_folder, company)
    
    # 4. Validate data integrity
    data_integrity_results = validate_data_integrity(data_entry_data, app_data, company)
    
    # 5. Validate calculation methodology
    calculation_results = validate_calculation_methodology(fcf_calculations, app_data, company)
    
    # 6. Generate comprehensive report
    generate_comprehensive_report(company, data_integrity_results, calculation_results)

if __name__ == "__main__":
    main()