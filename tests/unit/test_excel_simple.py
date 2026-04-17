#!/usr/bin/env python3
"""
Simple Excel Data Adapter Test
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
        from core.data_processing.var_input_data import get_var_input_data
        from core.data_processing.financial_variable_registry import get_registry
        print("- All imports successful")
        return True
    except Exception as e:
        print(f"- Import failed: {str(e)}")
        return False

def test_initialization():
    """Test that components initialize correctly"""
    print("Testing initialization...")
    
    try:
        from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
        from core.data_processing.var_input_data import get_var_input_data
        from core.data_processing.financial_variable_registry import get_registry
        
        adapter = ExcelDataAdapter()
        var_data = get_var_input_data()
        registry = get_registry()
        
        print(f"- Adapter initialized: {adapter is not None}")
        print(f"- VarInputData initialized: {var_data is not None}")
        print(f"- Registry initialized: {registry is not None}")
        
        return True
    except Exception as e:
        print(f"- Initialization failed: {str(e)}")
        return False

def test_file_analysis():
    """Test Excel file analysis"""
    print("Testing file analysis...")
    
    test_file = "data/companies/GOOG/FY/Alphabet Inc Class C - Income Statement.xlsx"
    
    if not os.path.exists(test_file):
        print(f"- Test file not found: {test_file}")
        return False
    
    try:
        from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
        
        adapter = ExcelDataAdapter()
        
        # Test file analysis
        file_info = adapter._analyze_excel_file(test_file, "GOOG", "income", "FY")
        
        print(f"- File analyzed successfully")
        print(f"- Periods found: {len(file_info.available_periods)}")
        print(f"- Quality score: {file_info.data_quality_score}")
        print(f"- Available periods: {file_info.available_periods[:5]}")  # First 5
        
        return len(file_info.available_periods) > 0
        
    except Exception as e:
        print(f"- File analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_tests():
    """Run all tests"""
    print("Excel Adapter Simple Test")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Initialization", test_initialization), 
        ("File Analysis", test_file_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            print(f"- Status: {status}")
        except Exception as e:
            print(f"- Status: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(1)