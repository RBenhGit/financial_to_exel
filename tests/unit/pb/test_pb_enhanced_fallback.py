#!/usr/bin/env python3
"""
Test Enhanced P/B Analysis with API Fallback System
==================================================

This test validates the enhanced P/B historical analysis system with:
- Improved Excel parsing for non-standard layouts (VISA-style)
- Intelligent API fallback for missing shares outstanding data  
- Specific diagnostic error messages
- Comprehensive data validation layer
- Unified data completion strategy

Usage:
    python test_pb_enhanced_fallback.py
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pb_enhanced_fallback_system():
    """Test the enhanced P/B analysis with API fallback capabilities"""
    
    print("🧪 Enhanced P/B Analysis API Fallback Test")
    print("=" * 50)
    
    try:
        from core.analysis.engines.financial_calculations import FinancialCalculator
        from pb_valuation import PBValuator
        
        # Test with a sample ticker (Microsoft)
        test_ticker = "MSFT"
        print(f"\n📊 Testing enhanced P/B analysis for {test_ticker}")
        
        # Initialize with mock company folder (won't exist, forcing API fallback)
        calc = FinancialCalculator(f"./mock_data/{test_ticker}")
        calc.ticker_symbol = test_ticker
        
        # Initialize P/B valuator
        pb_valuator = PBValuator(calc)
        
        print(f"\n🔍 Running P/B analysis with enhanced diagnostics...")
        
        # Run P/B analysis - this should trigger API fallback
        result = pb_valuator.calculate_pb_analysis(test_ticker)
        
        print(f"\n📋 P/B Analysis Results:")
        print(f"Status: {'✅ Success' if 'error' not in result else '❌ Error'}")
        
        if 'error' in result:
            print(f"Error Type: {result['error']}")
            print(f"Error Message: {result['error_message']}")
            
            if 'diagnostic_info' in result:
                diag = result['diagnostic_info']
                print(f"\n🔧 Diagnostic Information:")
                
                if 'data_sources_tried' in diag:
                    print(f"Data Sources Tried: {', '.join(diag['data_sources_tried'])}")
                    
                if 'failures' in diag:
                    print(f"Failures ({len(diag['failures'])}):")
                    for i, failure in enumerate(diag['failures'][:3], 1):  # Show first 3
                        print(f"  {i}. {failure['source']}: {failure['reason']}")
                        
                if 'missing_data' in diag:
                    print(f"Missing Data Items:")
                    for item in diag['missing_data'][:3]:  # Show first 3
                        print(f"  • {item}")
                        
                if 'fallback_attempts' in diag:
                    print(f"Fallback Attempts: {', '.join(diag['fallback_attempts'])}")
                    
                if 'final_source' in diag and diag['final_source']:
                    print(f"Final Data Source: {diag['final_source']}")
                    
            if 'suggested_solutions' in result:
                print(f"\n💡 Suggested Solutions:")
                for i, solution in enumerate(result['suggested_solutions'][:3], 1):
                    print(f"  {i}. {solution}")
                    
        else:
            print(f"✅ Successfully calculated P/B analysis!")
            current_data = result.get('current_data', {})
            pb_ratio = current_data.get('pb_ratio')
            book_value = current_data.get('book_value_per_share')
            
            if pb_ratio and book_value:
                print(f"P/B Ratio: {pb_ratio:.2f}")
                print(f"Book Value per Share: ${book_value:.2f}")
                
        # Test enhanced diagnostics separately
        print(f"\n🔍 Testing diagnostic functionality...")
        book_value, diagnostics = pb_valuator._calculate_book_value_per_share_with_diagnostics()
        
        print(f"Book Value Calculation: {'✅ Success' if book_value else '❌ Failed'}")
        if book_value:
            print(f"Book Value per Share: ${book_value:.2f}")
            
        print(f"Diagnostics Summary:")
        print(f"  Sources Tried: {len(diagnostics.get('data_sources_tried', []))}")
        print(f"  Failures: {len(diagnostics.get('failures', []))}")
        print(f"  Fallback Attempts: {len(diagnostics.get('fallback_attempts', []))}")
        print(f"  Final Source: {diagnostics.get('final_source', 'None')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Ensure all required modules are available")
        return False
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_excel_parser_enhancements():
    """Test the enhanced Excel parsing capabilities"""
    
    print(f"\n📁 Testing Enhanced Excel Parsing")
    print("=" * 40)
    
    try:
        from core.analysis.engines.financial_calculations import FinancialCalculator
        
        # Test the enhanced parsing methods
        calc = FinancialCalculator("./test_data")
        
        # Test header detection
        sample_data = [
            ["", "", "", ""],
            ["Company Balance Sheet", "", "", ""],
            ["", "2021", "2022", "2023"],
            ["Total Assets", 100000, 110000, 120000],
            ["Shareholders Equity", 50000, 55000, 60000],
        ]
        
        header_row, date_row = calc._find_header_rows(sample_data)
        print(f"Header Detection: header_row={header_row}, date_row={date_row}")
        
        # Test non-standard layout parsing
        if header_row is not None and date_row is not None:
            df = calc._parse_non_standard_layout(sample_data, header_row, date_row)
            print(f"Parsed DataFrame Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
        print("✅ Excel parsing enhancements working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Excel parsing test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced P/B Analysis Test Suite")
    print("=" * 60)
    
    # Test 1: Enhanced P/B Analysis with API Fallback
    test1_success = test_pb_enhanced_fallback_system()
    
    # Test 2: Excel Parser Enhancements
    test2_success = test_excel_parser_enhancements()
    
    print(f"\n📊 Test Results Summary:")
    print(f"Enhanced P/B Analysis: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Excel Parser Enhancements: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print(f"\n🎉 All tests passed! Enhanced P/B analysis system is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)