#!/usr/bin/env python3
"""
Excel Dividend Extraction Diagnostic Tool
=========================================

This script analyzes Excel files to diagnose dividend data extraction issues.
It shows the exact field names and data structure to help fix the dividend graph display problem.

Usage:
    python debug_excel_dividend_extraction.py

Features:
- Analyzes Income Statement for shares outstanding field names
- Analyzes Cash Flow Statement for dividend field names
- Shows fuzzy matching suggestions for field names
- Provides detailed data structure analysis
"""

import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from financial_calculations import FinancialCalculator
from config import get_logger

logger = get_logger(__name__)

class ExcelDividendDiagnostic:
    """Diagnostic tool for Excel dividend extraction issues"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.financial_calculator = None
        
    def initialize_calculator(self) -> bool:
        """Initialize the financial calculator with Excel data"""
        try:
            self.financial_calculator = FinancialCalculator(self.ticker)
            return True
        except Exception as e:
            print(f"❌ Error initializing calculator for {self.ticker}: {e}")
            return False
    
    def analyze_excel_structure(self) -> Dict:
        """Analyze the Excel file structure for dividend-related data"""
        if not self.financial_calculator:
            return {}
            
        analysis = {
            'income_statement': self._analyze_income_statement(),
            'cash_flow_statement': self._analyze_cash_flow_statement(),
            'shares_outstanding': self._analyze_shares_outstanding(),
            'dividend_extraction': self._analyze_dividend_extraction()
        }
        
        return analysis
    
    def _analyze_income_statement(self) -> Dict:
        """Analyze Income Statement structure and field names"""
        result = {
            'found_data': False,
            'data_keys': [],
            'field_names': [],
            'shares_related_fields': [],
            'column_structure': {},
            'sample_data': {}
        }
        
        try:
            # Check both FY and LTM data
            for data_key in ['income_fy', 'income_ltm']:
                income_data = self.financial_calculator.financial_data.get(data_key, pd.DataFrame())
                
                if not income_data.empty:
                    result['found_data'] = True
                    result['data_keys'].append(data_key)
                    result['column_structure'][data_key] = list(income_data.columns)
                    
                    # Extract all field names (typically in column 3, index 2)
                    field_names = []
                    shares_fields = []
                    
                    for index, row in income_data.iterrows():
                        # Extract field name from column 3 (index 2)
                        field_name = ""
                        if len(row) >= 3:
                            field_name = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                        elif len(row) >= 1:
                            field_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                        
                        if field_name and field_name != "nan":
                            field_names.append(field_name)
                            
                            # Look for shares-related fields
                            if any(keyword in field_name.lower() for keyword in 
                                   ['shares', 'share', 'outstanding', 'weighted', 'average', 'basic']):
                                shares_fields.append(field_name)
                    
                    result['field_names'].extend(field_names)
                    result['shares_related_fields'].extend(shares_fields)
                    
                    # Sample data for debugging
                    if len(income_data) > 0:
                        result['sample_data'][data_key] = income_data.head(10).to_dict()
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_cash_flow_statement(self) -> Dict:
        """Analyze Cash Flow Statement structure and field names"""
        result = {
            'found_data': False,
            'data_keys': [],
            'field_names': [],
            'dividend_related_fields': [],
            'column_structure': {},
            'sample_data': {}
        }
        
        try:
            # Check both FY and LTM data
            for data_key in ['cashflow_fy', 'cashflow_ltm']:
                cashflow_data = self.financial_calculator.financial_data.get(data_key, pd.DataFrame())
                
                if not cashflow_data.empty:
                    result['found_data'] = True
                    result['data_keys'].append(data_key)
                    result['column_structure'][data_key] = list(cashflow_data.columns)
                    
                    # Extract all field names (typically in column 3, index 2)
                    field_names = []
                    dividend_fields = []
                    
                    for index, row in cashflow_data.iterrows():
                        # Extract field name from column 3 (index 2)
                        field_name = ""
                        if len(row) >= 3:
                            field_name = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                        elif len(row) >= 1:
                            field_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                        
                        if field_name and field_name != "nan":
                            field_names.append(field_name)
                            
                            # Look for dividend-related fields
                            if any(keyword in field_name.lower() for keyword in 
                                   ['dividend', 'dividends', 'payment', 'paid', 'cash', 'distribution']):
                                dividend_fields.append(field_name)
                    
                    result['field_names'].extend(field_names)
                    result['dividend_related_fields'].extend(dividend_fields)
                    
                    # Sample data for debugging
                    if len(cashflow_data) > 0:
                        result['sample_data'][data_key] = cashflow_data.head(10).to_dict()
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_shares_outstanding(self) -> Dict:
        """Test the shares outstanding extraction method"""
        result = {
            'current_method_result': None,
            'expected_field_name': "Weighted Average Basic Shares Out",
            'found_similar_fields': [],
            'extraction_successful': False
        }
        
        try:
            # Test the current extraction method
            if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
                shares = self.financial_calculator._extract_excel_shares_outstanding()
                result['current_method_result'] = shares
                result['extraction_successful'] = shares is not None and shares > 0
            
            # Find similar field names using fuzzy matching
            income_analysis = self._analyze_income_statement()
            all_fields = income_analysis.get('field_names', [])
            
            # Fuzzy match for shares outstanding field
            close_matches = get_close_matches(
                result['expected_field_name'], 
                all_fields, 
                n=5, 
                cutoff=0.6
            )
            result['found_similar_fields'] = close_matches
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_dividend_extraction(self) -> Dict:
        """Test the dividend extraction method"""
        result = {
            'current_method_result': None,
            'expected_field_names': {
                'regular': "Dividends Paid (Ex Special Dividends)",
                'special': "Special Dividend Paid"
            },
            'found_similar_fields': {
                'regular': [],
                'special': []
            },
            'extraction_successful': False
        }
        
        try:
            # Test the current extraction method
            if hasattr(self.financial_calculator, '_extract_excel_dividends'):
                dividends = self.financial_calculator._extract_excel_dividends()
                result['current_method_result'] = dividends
                result['extraction_successful'] = len(dividends.get('years', [])) > 0
            
            # Find similar field names using fuzzy matching
            cashflow_analysis = self._analyze_cash_flow_statement()
            all_fields = cashflow_analysis.get('field_names', [])
            
            # Fuzzy match for dividend fields
            regular_matches = get_close_matches(
                result['expected_field_names']['regular'], 
                all_fields, 
                n=5, 
                cutoff=0.5
            )
            result['found_similar_fields']['regular'] = regular_matches
            
            special_matches = get_close_matches(
                result['expected_field_names']['special'], 
                all_fields, 
                n=5, 
                cutoff=0.5
            )
            result['found_similar_fields']['special'] = special_matches
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def print_analysis_report(self, analysis: Dict):
        """Print a comprehensive analysis report"""
        print(f"\n{'='*80}")
        print(f"📊 EXCEL DIVIDEND EXTRACTION DIAGNOSTIC REPORT")
        print(f"{'='*80}")
        print(f"Ticker: {self.ticker}")
        print(f"{'='*80}")
        
        # Income Statement Analysis
        print(f"\n🏦 INCOME STATEMENT ANALYSIS")
        print(f"{'-'*50}")
        income = analysis.get('income_statement', {})
        
        if income.get('found_data'):
            print(f"✅ Found Income Statement data in: {income['data_keys']}")
            print(f"📋 Total field names found: {len(set(income['field_names']))}")
            
            if income['shares_related_fields']:
                print(f"\n💰 SHARES-RELATED FIELDS FOUND:")
                for field in set(income['shares_related_fields']):
                    print(f"   • {field}")
            else:
                print(f"❌ No shares-related fields found")
        else:
            print(f"❌ No Income Statement data found")
            if 'error' in income:
                print(f"Error: {income['error']}")
        
        # Cash Flow Statement Analysis
        print(f"\n💸 CASH FLOW STATEMENT ANALYSIS")
        print(f"{'-'*50}")
        cashflow = analysis.get('cash_flow_statement', {})
        
        if cashflow.get('found_data'):
            print(f"✅ Found Cash Flow Statement data in: {cashflow['data_keys']}")
            print(f"📋 Total field names found: {len(set(cashflow['field_names']))}")
            
            if cashflow['dividend_related_fields']:
                print(f"\n💰 DIVIDEND-RELATED FIELDS FOUND:")
                for field in set(cashflow['dividend_related_fields']):
                    print(f"   • {field}")
            else:
                print(f"❌ No dividend-related fields found")
        else:
            print(f"❌ No Cash Flow Statement data found")
            if 'error' in cashflow:
                print(f"Error: {cashflow['error']}")
        
        # Shares Outstanding Analysis
        print(f"\n📈 SHARES OUTSTANDING EXTRACTION TEST")
        print(f"{'-'*50}")
        shares = analysis.get('shares_outstanding', {})
        
        print(f"Expected field name: '{shares['expected_field_name']}'")
        
        if shares['extraction_successful']:
            print(f"✅ Extraction successful! Value: {shares['current_method_result']:,.0f}")
        else:
            print(f"❌ Extraction failed. Current result: {shares['current_method_result']}")
            
            if shares['found_similar_fields']:
                print(f"\n🔍 SIMILAR FIELD NAMES FOUND (fuzzy match):")
                for field in shares['found_similar_fields']:
                    print(f"   • {field}")
            else:
                print(f"🔍 No similar field names found")
        
        # Dividend Extraction Analysis
        print(f"\n💰 DIVIDEND EXTRACTION TEST")
        print(f"{'-'*50}")
        dividends = analysis.get('dividend_extraction', {})
        
        print(f"Expected regular dividend field: '{dividends['expected_field_names']['regular']}'")
        print(f"Expected special dividend field: '{dividends['expected_field_names']['special']}'")
        
        if dividends['extraction_successful']:
            result = dividends['current_method_result']
            print(f"✅ Extraction successful! Found {len(result['years'])} years of data:")
            for i, year in enumerate(result['years']):
                regular = result['regular_dividends'][i]
                special = result['special_dividends'][i]
                total = result['total_dividends'][i]
                print(f"   • {year}: Regular=${regular:,.0f}, Special=${special:,.0f}, Total=${total:,.0f}")
        else:
            print(f"❌ Extraction failed. Current result: {dividends['current_method_result']}")
            
            # Show fuzzy matches
            regular_matches = dividends['found_similar_fields']['regular']
            special_matches = dividends['found_similar_fields']['special']
            
            if regular_matches:
                print(f"\n🔍 SIMILAR REGULAR DIVIDEND FIELDS (fuzzy match):")
                for field in regular_matches:
                    print(f"   • {field}")
            
            if special_matches:
                print(f"\n🔍 SIMILAR SPECIAL DIVIDEND FIELDS (fuzzy match):")
                for field in special_matches:
                    print(f"   • {field}")
            
            if not regular_matches and not special_matches:
                print(f"🔍 No similar dividend field names found")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print(f"{'-'*50}")
        
        if not shares['extraction_successful']:
            if shares['found_similar_fields']:
                print(f"📋 For Shares Outstanding:")
                print(f"   Consider updating code to also look for: {shares['found_similar_fields'][0]}")
            else:
                print(f"📋 Check if Income Statement contains shares outstanding data")
        
        if not dividends['extraction_successful']:
            if dividends['found_similar_fields']['regular']:
                print(f"📋 For Regular Dividends:")
                print(f"   Consider updating code to also look for: {dividends['found_similar_fields']['regular'][0]}")
            
            if dividends['found_similar_fields']['special']:
                print(f"📋 For Special Dividends:")
                print(f"   Consider updating code to also look for: {dividends['found_similar_fields']['special'][0]}")
            
            if not any(dividends['found_similar_fields'].values()):
                print(f"📋 Check if Cash Flow Statement contains dividend payment data")
        
        print(f"\n{'='*80}")


def main():
    """Main diagnostic function"""
    print("🔍 Excel Dividend Extraction Diagnostic Tool")
    print("=" * 50)
    
    # Get ticker from user input
    ticker = input("Enter ticker symbol to analyze: ").strip().upper()
    
    if not ticker:
        print("❌ No ticker provided. Exiting.")
        return
    
    # Check if Excel data exists
    data_path = Path(f"data/companies/{ticker}")
    if not data_path.exists():
        print(f"❌ No data directory found for {ticker} at {data_path}")
        print(f"   Expected structure: data/companies/{ticker}/FY/ and data/companies/{ticker}/LTM/")
        return
    
    # Initialize diagnostic tool
    diagnostic = ExcelDividendDiagnostic(ticker)
    
    if not diagnostic.initialize_calculator():
        print("❌ Failed to initialize financial calculator. Check Excel data format.")
        return
    
    # Run analysis
    print(f"\n🔄 Analyzing Excel data for {ticker}...")
    analysis = diagnostic.analyze_excel_structure()
    
    # Print report
    diagnostic.print_analysis_report(analysis)
    
    # Save detailed analysis to file
    output_file = f"excel_dividend_diagnostic_{ticker}.txt"
    try:
        import json
        with open(output_file, 'w') as f:
            f.write(f"Excel Dividend Extraction Diagnostic Report for {ticker}\n")
            f.write("=" * 60 + "\n\n")
            f.write(json.dumps(analysis, indent=2, default=str))
        
        print(f"\n💾 Detailed analysis saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save detailed analysis: {e}")


if __name__ == "__main__":
    main()