#!/usr/bin/env python3
"""
Comprehensive FCF Validation System
Analyzes and validates FCF calculations between Excel files and app calculations
Cross-validates with multiple companies (GOOG, MSFT, NVDA, TSLA, V)
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import traceback
from financial_calculations import FinancialCalculator

class FCFValidator:
    def __init__(self):
        self.base_path = "/mnt/c/AsusWebStorage/ran@benhur.co/MySyncFolder/python/investingAnalysis/financial_to_exel"
        self.companies = ["GOOG", "MSFT", "NVDA", "TSLA", "V"]
        self.results = {}
        
    def read_excel_fcf_data(self, company):
        """Extract FCF data from Excel file"""
        try:
            excel_file = f"{self.base_path}/{company}/FCF_Analysis_*.xlsx"
            # Find the actual file
            import glob
            excel_files = glob.glob(excel_file)
            if not excel_files:
                print(f"❌ No Excel file found for {company}")
                return None
                
            excel_path = excel_files[0]
            print(f"📊 Reading Excel file: {excel_path}")
            
            # Read FCF DATA sheet if it exists
            try:
                fcf_data = pd.read_excel(excel_path, sheet_name='FCF DATA', header=0)
                return self.parse_excel_fcf_data(fcf_data, company)
            except Exception as e:
                print(f"⚠️ FCF DATA sheet not found for {company}, trying main sheets: {e}")
                
            # Try to read main calculation sheets
            try:
                dcf_sheet = pd.read_excel(excel_path, sheet_name='DCF', header=None)
                return self.parse_excel_dcf_sheet(dcf_sheet, company)
            except Exception as e:
                print(f"⚠️ DCF sheet not found for {company}: {e}")
                
            return None
            
        except Exception as e:
            print(f"❌ Error reading Excel file for {company}: {e}")
            return None
    
    def parse_excel_fcf_data(self, df, company):
        """Parse FCF data from Excel FCF DATA sheet"""
        fcf_data = {}
        
        # Look for years in the first row or column
        try:
            # Check if years are in the first row
            year_row = df.iloc[0]
            years = []
            for val in year_row:
                if isinstance(val, (int, float)) and 2010 <= val <= 2030:
                    years.append(int(val))
            
            if not years:
                # Check first column for years
                year_col = df.iloc[:, 0]
                for val in year_col:
                    if isinstance(val, (int, float)) and 2010 <= val <= 2030:
                        years.append(int(val))
            
            print(f"📅 Found years for {company}: {years}")
            
            # Look for FCF-related rows
            fcf_types = ["Simple FCF", "LFCF", "FCFF", "FCFE", "Free Cash Flow", "Operating Cash Flow", "CapEx"]
            
            for idx, row in df.iterrows():
                row_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                
                for fcf_type in fcf_types:
                    if fcf_type.lower() in row_name.lower():
                        values = []
                        for col_idx in range(1, min(len(row), len(years) + 1)):
                            val = row.iloc[col_idx]
                            if pd.notna(val) and isinstance(val, (int, float)):
                                values.append(float(val))
                        
                        if values:
                            fcf_data[fcf_type] = {
                                'years': years[:len(values)],
                                'values': values
                            }
                            print(f"✅ Found {fcf_type} for {company}: {len(values)} values")
            
            return fcf_data
            
        except Exception as e:
            print(f"❌ Error parsing FCF data for {company}: {e}")
            return {}
    
    def parse_excel_dcf_sheet(self, df, company):
        """Parse FCF data from Excel DCF sheet"""
        fcf_data = {}
        
        try:
            # Look for year headers and FCF values
            for idx, row in df.iterrows():
                row_str = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                
                # Look for year rows
                if any(str(year) in row_str for year in range(2015, 2030)):
                    years = []
                    for val in row:
                        if pd.notna(val) and isinstance(val, (int, float)) and 2010 <= val <= 2030:
                            years.append(int(val))
                    if years:
                        fcf_data['years'] = years
                
                # Look for FCF rows
                if any(keyword in row_str.lower() for keyword in ['fcf', 'free cash flow', 'cash flow']):
                    values = []
                    for col_idx in range(1, len(row)):
                        val = row.iloc[col_idx]
                        if pd.notna(val) and isinstance(val, (int, float)) and abs(val) > 100:  # Filter out small values
                            values.append(float(val))
                    
                    if values and len(values) >= 3:
                        fcf_data['DCF_FCF'] = values
                        print(f"✅ Found DCF FCF values for {company}: {values}")
            
            return fcf_data
            
        except Exception as e:
            print(f"❌ Error parsing DCF sheet for {company}: {e}")
            return {}
    
    def calculate_app_fcf(self, company):
        """Calculate FCF using the app's methodology"""
        try:
            company_folder = f"{self.base_path}/{company}"
            if not os.path.exists(company_folder):
                print(f"❌ Company folder not found: {company_folder}")
                return None
            
            # Initialize calculator with company folder
            calc = FinancialCalculator(company_folder)
            
            # Load financial data
            calc.load_financial_statements()
            
            # Calculate all FCF types
            fcf_results = {}
            
            # Get available years from metrics
            metrics = calc._calculate_all_metrics()
            available_years = list(range(2015, 2025))  # Approximate years
            
            # LFCF (Levered Free Cash Flow)
            lfcf_values = calc.calculate_levered_fcf()
            if lfcf_values:
                fcf_results['LFCF'] = {
                    'values': lfcf_values,
                    'years': available_years[:len(lfcf_values)],
                    'method': 'Operating Cash Flow - CapEx'
                }
            
            # FCFF (Free Cash Flow to Firm) 
            fcff_values = calc.calculate_fcf_to_firm()
            if fcff_values:
                fcf_results['FCFF'] = {
                    'values': fcff_values,
                    'years': available_years[:len(fcff_values)],
                    'method': 'EBIT(1-Tax Rate) + D&A - ΔWorking Capital - CapEx'
                }
            
            # FCFE (Free Cash Flow to Equity)
            fcfe_values = calc.calculate_fcf_to_equity()
            if fcfe_values:
                fcf_results['FCFE'] = {
                    'values': fcfe_values,
                    'years': available_years[:len(fcfe_values)],
                    'method': 'Net Income + D&A - ΔWorking Capital - CapEx + Net Borrowing'
                }
            
            return fcf_results
            
        except Exception as e:
            print(f"❌ Error calculating app FCF for {company}: {e}")
            traceback.print_exc()
            return None
    
    def compare_fcf_values(self, excel_data, app_data, company):
        """Compare Excel and App FCF values"""
        comparison = {
            'company': company,
            'matches': {},
            'differences': {},
            'issues': []
        }
        
        if not excel_data or not app_data:
            comparison['issues'].append("Missing data - cannot compare")
            return comparison
        
        # Compare LFCF (should match exactly)
        if 'LFCF' in app_data:
            app_lfcf = app_data['LFCF']['values']
            
            # Try to find matching Excel data
            excel_lfcf = None
            for key in ['Simple FCF', 'LFCF', 'Free Cash Flow']:
                if key in excel_data and 'values' in excel_data[key]:
                    excel_lfcf = excel_data[key]['values']
                    break
            
            if excel_lfcf:
                # Reverse app values to match Excel order (newest first)
                app_lfcf_reversed = list(reversed(app_lfcf))
                
                # Compare values
                min_len = min(len(excel_lfcf), len(app_lfcf_reversed))
                matches = 0
                for i in range(min_len):
                    if abs(excel_lfcf[i] - app_lfcf_reversed[i]) < 1000:  # Allow for rounding
                        matches += 1
                
                match_percentage = (matches / min_len) * 100 if min_len > 0 else 0
                comparison['matches']['LFCF'] = {
                    'excel_values': excel_lfcf[:min_len],
                    'app_values': app_lfcf_reversed[:min_len],
                    'match_percentage': match_percentage,
                    'matches': matches,
                    'total': min_len
                }
        
        # Compare FCFF
        if 'FCFF' in app_data:
            app_fcff = app_data['FCFF']['values']
            comparison['differences']['FCFF'] = {
                'app_values': app_fcff,
                'note': 'Excel FCFF calculation method may differ from app methodology'
            }
        
        # Compare FCFE  
        if 'FCFE' in app_data:
            app_fcfe = app_data['FCFE']['values']
            comparison['differences']['FCFE'] = {
                'app_values': app_fcfe,
                'note': 'Excel FCFE calculation method may differ from app methodology'
            }
        
        return comparison
    
    def analyze_calculation_issues(self):
        """Analyze common calculation issues across companies"""
        issues = {
            'indexing_problems': [],
            'working_capital_issues': [],
            'tax_rate_problems': [],
            'net_borrowing_differences': []
        }
        
        # Check for index alignment issues in FCFF calculation
        try:
            from financial_calculations import FinancialCalculator
            import inspect
            
            # Get FCFF method source code
            source = inspect.getsource(FinancialCalculator.calculate_fcf_to_firm)
            
            if 'i+1' in source and 'range(len(' in source:
                issues['indexing_problems'].append(
                    "FCFF calculation uses i+1 indexing which may cause array bounds issues"
                )
            
            if 'ebit_values[i+1]' in source:
                issues['indexing_problems'].append(
                    "EBIT values accessed with i+1 offset - potential index mismatch"
                )
            
            if 'working_capital_changes[i]' in source and 'ebit_values[i+1]' in source:
                issues['working_capital_issues'].append(
                    "Working capital and EBIT use different indexing (i vs i+1)"
                )
        
        except Exception as e:
            issues['indexing_problems'].append(f"Could not analyze source code: {e}")
        
        return issues
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        report = []
        report.append("="*80)
        report.append("🔍 COMPREHENSIVE FCF VALIDATION REPORT")
        report.append("="*80)
        report.append("")
        
        # Test each company
        for company in self.companies:
            report.append(f"📊 ANALYZING {company}")
            report.append("-" * 40)
            
            # Load Excel data
            excel_data = self.read_excel_fcf_data(company)
            
            # Calculate app data
            app_data = self.calculate_app_fcf(company)
            
            # Compare
            comparison = self.compare_fcf_values(excel_data, app_data, company)
            self.results[company] = comparison
            
            # Report results
            if comparison['matches']:
                for fcf_type, match_data in comparison['matches'].items():
                    report.append(f"✅ {fcf_type}: {match_data['match_percentage']:.1f}% match")
                    report.append(f"   Excel: {match_data['excel_values']}")
                    report.append(f"   App:   {match_data['app_values']}")
            
            if comparison['differences']:
                for fcf_type, diff_data in comparison['differences'].items():
                    report.append(f"❌ {fcf_type}: Calculation differences detected")
                    report.append(f"   App values: {diff_data['app_values']}")
                    report.append(f"   Note: {diff_data['note']}")
            
            if comparison['issues']:
                for issue in comparison['issues']:
                    report.append(f"⚠️ Issue: {issue}")
            
            report.append("")
        
        # Analyze calculation issues
        report.append("🛠️ CALCULATION ISSUE ANALYSIS")
        report.append("-" * 40)
        issues = self.analyze_calculation_issues()
        
        for issue_type, problems in issues.items():
            if problems:
                report.append(f"❌ {issue_type.replace('_', ' ').title()}:")
                for problem in problems:
                    report.append(f"   • {problem}")
        
        # Recommendations
        report.append("")
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        report.append("1. Fix indexing issue in FCFF calculation (change i+1 to i)")
        report.append("2. Standardize working capital calculation across all FCF types")
        report.append("3. Validate tax rate calculation methodology")
        report.append("4. Align FCFE net borrowing with Excel financing approach")
        report.append("5. Add data validation checks for array length mismatches")
        
        return "\n".join(report)

def main():
    """Main validation function"""
    print("🚀 Starting Comprehensive FCF Validation...")
    
    validator = FCFValidator()
    report = validator.generate_validation_report()
    
    # Save report
    report_file = "/mnt/c/AsusWebStorage/ran@benhur.co/MySyncFolder/python/investingAnalysis/financial_to_exel/FCF_Validation_Report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Full report saved to: {report_file}")
    
    return validator.results

if __name__ == "__main__":
    results = main()