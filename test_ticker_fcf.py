"""
Test script to verify ticker mode FCF calculations work
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ticker_fcf_calculation():
    """Test complete ticker mode FCF calculation"""
    print("Testing Ticker Mode FCF Calculation")
    print("=" * 40)
    
    try:
        from fcf_analysis_streamlit import create_ticker_mode_calculator, _convert_yfinance_to_calculator_format
        
        print("1. Creating ticker mode calculator for AAPL...")
        calculator, error = create_ticker_mode_calculator("AAPL", "US Market")
        
        if not calculator:
            print(f"FAIL: Calculator creation failed - {error}")
            return False
        
        print("PASS: Calculator created successfully")
        print(f"  Company: {calculator.company_name}")
        print(f"  Ticker: {calculator.ticker_symbol}")
        print(f"  Price: ${calculator.current_stock_price}")
        
        # Check if financial data was loaded
        if hasattr(calculator, 'financial_data') and calculator.financial_data:
            print("PASS: Financial data loaded")
            
            # Check what data types are available
            data_types = list(calculator.financial_data.keys())
            print(f"  Available data types: {data_types}")
            
            # Check data shapes
            for data_type, data in calculator.financial_data.items():
                if hasattr(data, 'shape'):
                    print(f"  {data_type} shape: {data.shape}")
        else:
            print("FAIL: No financial data loaded")
            return False
        
        print("\n2. Testing FCF calculations...")
        
        # Try to calculate FCF
        try:
            fcf_results = calculator.calculate_all_fcf_types()
            
            if fcf_results:
                print("PASS: FCF calculation completed")
                
                # Show what FCF types were calculated
                for fcf_type, values in fcf_results.items():
                    if values:
                        print(f"  {fcf_type}: {len(values) if isinstance(values, (list, dict)) else 'calculated'}")
                    else:
                        print(f"  {fcf_type}: no data")
                
                return True
            else:
                print("FAIL: FCF calculation returned empty results")
                return False
                
        except Exception as fcf_error:
            print(f"FAIL: FCF calculation error - {fcf_error}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"FAIL: Test error - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yfinance_data_structure():
    """Test the yfinance data structure conversion"""
    print("\nTesting YFinance Data Structure")
    print("=" * 35)
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker("AAPL")
        
        # Get financial statements
        income_stmt = ticker.financials
        balance_sheet = ticker.balance_sheet  
        cash_flow = ticker.cashflow
        
        print("YFinance data loaded:")
        print(f"  Income statement shape: {income_stmt.shape}")
        print(f"  Balance sheet shape: {balance_sheet.shape}")
        print(f"  Cash flow shape: {cash_flow.shape}")
        
        # Test conversion function
        from fcf_analysis_streamlit import _convert_yfinance_to_calculator_format
        
        financial_data = _convert_yfinance_to_calculator_format(
            income_stmt, balance_sheet, cash_flow, "AAPL"
        )
        
        if financial_data:
            print("PASS: Data conversion successful")
            print("  Converted data types:", list(financial_data.keys()))
            
            # Check shapes of converted data
            for data_type, data in financial_data.items():
                if hasattr(data, 'shape'):
                    print(f"  {data_type} converted shape: {data.shape}")
            
            return True
        else:
            print("FAIL: Data conversion failed")
            return False
            
    except Exception as e:
        print(f"FAIL: YFinance test error - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Ticker Mode FCF Test Suite")
    print("=" * 50)
    
    tests = [
        ("YFinance Data Structure", test_yfinance_data_structure),
        ("Ticker FCF Calculation", test_ticker_fcf_calculation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*10} {test_name} {'='*10}")
        try:
            if test_func():
                print(f"RESULT: {test_name} PASSED")
                passed += 1
            else:
                print(f"RESULT: {test_name} FAILED")
        except Exception as e:
            print(f"RESULT: {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print("FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\nSUCCESS: Ticker mode FCF calculation is working!")
        return 0
    else:
        print(f"\nFAILED: {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())