#!/usr/bin/env python3
"""
Test Enhanced Dividend Extraction Methods
==========================================

This script tests the enhanced dividend and shares outstanding extraction methods
to verify that the dividend graph will display properly in the Streamlit app.

Usage:
    python test_enhanced_dividend_extraction.py

Features:
- Tests both shares outstanding and dividend extraction
- Tests both the diagnostic tool and the actual methods
- Provides clear success/failure feedback
- Shows exactly what data would be available for the dividend graph
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from financial_calculations import FinancialCalculator
from ddm_valuation import DDMValuator
from config import get_logger

logger = get_logger(__name__)

class DividendExtractionTester:
    """Test the enhanced dividend extraction functionality"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.financial_calculator = None
        self.ddm_valuator = None
        
    def initialize_components(self) -> bool:
        """Initialize the financial calculator and DDM valuator"""
        try:
            print(f"🔄 Initializing components for {self.ticker}...")
            
            # Initialize financial calculator
            self.financial_calculator = FinancialCalculator(self.ticker)
            print(f"✅ Financial calculator initialized")
            
            # Initialize DDM valuator
            self.ddm_valuator = DDMValuator(self.financial_calculator)
            print(f"✅ DDM valuator initialized")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            return False
    
    def test_shares_outstanding_extraction(self) -> dict:
        """Test the enhanced shares outstanding extraction"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING SHARES OUTSTANDING EXTRACTION")
        print(f"{'='*60}")
        
        result = {
            'success': False,
            'shares_outstanding': None,
            'method_used': None,
            'error': None
        }
        
        try:
            if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
                print(f"🔍 Testing enhanced shares outstanding extraction...")
                shares = self.financial_calculator._extract_excel_shares_outstanding()
                
                if shares and shares > 0:
                    result['success'] = True
                    result['shares_outstanding'] = shares
                    result['method_used'] = 'enhanced_excel_extraction'
                    print(f"✅ SUCCESS: Shares outstanding = {shares:,.0f}")
                else:
                    result['error'] = "No shares outstanding found or invalid value"
                    print(f"❌ FAILED: {result['error']}")
            else:
                result['error'] = "Enhanced shares extraction method not available"
                print(f"❌ FAILED: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return result
    
    def test_dividend_extraction(self) -> dict:
        """Test the enhanced dividend extraction"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING DIVIDEND EXTRACTION")
        print(f"{'='*60}")
        
        result = {
            'success': False,
            'dividend_data': None,
            'years_found': 0,
            'method_used': None,
            'error': None
        }
        
        try:
            if hasattr(self.financial_calculator, '_extract_excel_dividends'):
                print(f"🔍 Testing enhanced dividend extraction...")
                dividend_data = self.financial_calculator._extract_excel_dividends()
                
                if dividend_data and len(dividend_data.get('years', [])) > 0:
                    result['success'] = True
                    result['dividend_data'] = dividend_data
                    result['years_found'] = len(dividend_data['years'])
                    result['method_used'] = 'enhanced_excel_extraction'
                    
                    print(f"✅ SUCCESS: Found dividend data for {result['years_found']} years")
                    print(f"   Years: {dividend_data['years']}")
                    
                    # Show summary
                    for i, year in enumerate(dividend_data['years']):
                        regular = dividend_data['regular_dividends'][i]
                        special = dividend_data['special_dividends'][i] 
                        total = dividend_data['total_dividends'][i]
                        print(f"   {year}: Regular=${regular:,.0f}, Special=${special:,.0f}, Total=${total:,.0f}")
                        
                else:
                    result['error'] = "No dividend data found"
                    print(f"❌ FAILED: {result['error']}")
            else:
                result['error'] = "Enhanced dividend extraction method not available"
                print(f"❌ FAILED: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return result
    
    def test_ddm_dividend_extraction(self) -> dict:
        """Test the DDM-level dividend extraction (what the graph uses)"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING DDM DIVIDEND EXTRACTION (FOR GRAPH)")
        print(f"{'='*60}")
        
        result = {
            'success': False,
            'dividend_result': None,
            'per_share_data': None,
            'error': None
        }
        
        try:
            if hasattr(self.ddm_valuator, '_extract_dividend_data'):
                print(f"🔍 Testing DDM dividend data extraction (used by dividend graph)...")
                dividend_result = self.ddm_valuator._extract_dividend_data()
                
                if dividend_result.get('success') and dividend_result.get('data') is not None:
                    result['success'] = True
                    result['dividend_result'] = dividend_result
                    
                    data = dividend_result['data']
                    if not data.empty:
                        result['per_share_data'] = data
                        print(f"✅ SUCCESS: DDM dividend extraction successful")
                        print(f"   Found {len(data)} years of per-share dividend data")
                        print(f"   Data source: {dividend_result.get('data_source_used', 'unknown')}")
                        
                        # Show the actual per-share dividend data that would be graphed
                        print(f"\n📊 PER-SHARE DIVIDEND DATA (for graph):")
                        for index, row in data.iterrows():
                            year = row.get('year', 'Unknown')
                            dps = row.get('dividend_per_share', 0)
                            print(f"   {year}: ${dps:.2f} per share")
                    else:
                        result['error'] = "DDM extraction succeeded but returned empty data"
                        print(f"❌ FAILED: {result['error']}")
                else:
                    error_msg = dividend_result.get('error_message', 'Unknown error')
                    result['error'] = error_msg
                    print(f"❌ FAILED: {error_msg}")
            else:
                result['error'] = "DDM dividend extraction method not available"
                print(f"❌ FAILED: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return result
    
    def test_dividend_graph_readiness(self, shares_result: dict, dividend_result: dict, ddm_result: dict) -> dict:
        """Test if all components are ready for dividend graph display"""
        print(f"\n{'='*60}")
        print(f"🖼️  DIVIDEND GRAPH READINESS TEST")
        print(f"{'='*60}")
        
        result = {
            'graph_ready': False,
            'missing_components': [],
            'recommendations': []
        }
        
        # Check shares outstanding
        if not shares_result['success']:
            result['missing_components'].append('shares_outstanding')
            result['recommendations'].append("Fix shares outstanding field name in Income Statement")
        
        # Check dividend data
        if not dividend_result['success']:
            result['missing_components'].append('dividend_data')
            result['recommendations'].append("Fix dividend field names in Cash Flow Statement")
        
        # Check DDM integration
        if not ddm_result['success']:
            result['missing_components'].append('ddm_integration')
            result['recommendations'].append("Fix DDM dividend data integration")
        
        # Determine overall readiness
        result['graph_ready'] = len(result['missing_components']) == 0
        
        if result['graph_ready']:
            print(f"✅ DIVIDEND GRAPH IS READY TO DISPLAY!")
            print(f"   All required components are working correctly")
            print(f"   The dividend graph should now show in the DDM analysis tab")
        else:
            print(f"❌ DIVIDEND GRAPH NOT READY")
            print(f"   Missing components: {', '.join(result['missing_components'])}")
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        return result
    
    def run_comprehensive_test(self) -> dict:
        """Run all tests and provide comprehensive results"""
        print(f"\n{'='*80}")
        print(f"🧪 COMPREHENSIVE DIVIDEND EXTRACTION TEST")
        print(f"Ticker: {self.ticker}")
        print(f"{'='*80}")
        
        if not self.initialize_components():
            return {'success': False, 'error': 'Failed to initialize components'}
        
        # Run individual tests
        shares_result = self.test_shares_outstanding_extraction()
        dividend_result = self.test_dividend_extraction()
        ddm_result = self.test_ddm_dividend_extraction()
        
        # Test overall readiness
        graph_readiness = self.test_dividend_graph_readiness(shares_result, dividend_result, ddm_result)
        
        # Overall result
        overall_result = {
            'success': graph_readiness['graph_ready'],
            'ticker': self.ticker,
            'shares_outstanding': shares_result,
            'dividend_extraction': dividend_result,
            'ddm_integration': ddm_result,
            'graph_readiness': graph_readiness
        }
        
        print(f"\n{'='*80}")
        print(f"📋 FINAL SUMMARY")
        print(f"{'='*80}")
        
        if overall_result['success']:
            print(f"🎉 SUCCESS: All tests passed! The dividend graph should now display properly.")
            print(f"   You can now run the Streamlit app and check the DDM tab for the dividend graph.")
        else:
            print(f"⚠️  Some issues found. Please check the recommendations above.")
            print(f"   Run the diagnostic script for more detailed field name analysis.")
        
        return overall_result


def main():
    """Main test function"""
    print("🧪 Enhanced Dividend Extraction Test Suite")
    print("=" * 50)
    
    # Get ticker from user input
    ticker = input("Enter ticker symbol to test: ").strip().upper()
    
    if not ticker:
        print("❌ No ticker provided. Exiting.")
        return
    
    # Check if Excel data exists
    data_path = Path(f"data/companies/{ticker}")
    if not data_path.exists():
        print(f"❌ No data directory found for {ticker} at {data_path}")
        print(f"   Expected structure: data/companies/{ticker}/FY/ and data/companies/{ticker}/LTM/")
        return
    
    # Run tests
    tester = DividendExtractionTester(ticker)
    results = tester.run_comprehensive_test()
    
    # Save results to file
    output_file = f"dividend_extraction_test_results_{ticker}.txt"
    try:
        import json
        with open(output_file, 'w') as f:
            f.write(f"Enhanced Dividend Extraction Test Results for {ticker}\n")
            f.write("=" * 60 + "\n\n")
            f.write(json.dumps(results, indent=2, default=str))
        
        print(f"\n💾 Detailed test results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")
    
    # Final instructions
    print(f"\n📋 NEXT STEPS:")
    if results['success']:
        print(f"✅ 1. Launch the Streamlit app: python run_streamlit_app.py")
        print(f"✅ 2. Load data for {ticker}")
        print(f"✅ 3. Go to the DDM Valuation tab")
        print(f"✅ 4. Check that the dividend history chart displays at the top")
    else:
        print(f"⚠️  1. Run diagnostic script: python debug_excel_dividend_extraction.py")
        print(f"⚠️  2. Check Excel field names match expected names")
        print(f"⚠️  3. Fix any field name mismatches")
        print(f"⚠️  4. Re-run this test")


if __name__ == "__main__":
    main()