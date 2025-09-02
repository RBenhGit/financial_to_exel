#!/usr/bin/env python3
"""
Test Excel Data Extraction Functionality
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

def test_single_file_extraction():
    """Test extraction from a single Excel file"""
    print("Testing single file extraction...")
    
    test_file = "data/companies/GOOG/FY/Alphabet Inc Class C - Income Statement.xlsx"
    
    if not os.path.exists(test_file):
        print(f"- Test file not found: {test_file}")
        return False
    
    try:
        from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
        from core.data_processing.var_input_data import get_var_input_data, clear_cache
        
        # Clear cache for clean test
        clear_cache()
        
        adapter = ExcelDataAdapter()
        var_data = get_var_input_data()
        
        # Load single file
        results = adapter.load_single_file(
            symbol="GOOG",
            file_path=test_file,
            sheet_type="income",
            period_type="FY",
            validate_data=True
        )
        
        print(f"- Variables extracted: {results['variables_extracted']}")
        print(f"- Data points stored: {results['data_points_stored']}")
        print(f"- Periods covered: {len(results['periods_covered'])}")
        print(f"- Quality score: {results['quality_score']}")
        print(f"- Errors: {len(results.get('errors', []))}")
        
        # Try to retrieve some data
        print("- Testing data retrieval:")
        
        # Get available variables for GOOG
        available_vars = var_data.get_available_variables("GOOG")
        print(f"  Available variables: {len(available_vars)}")
        
        if available_vars:
            # Test first few variables
            for var_name in available_vars[:3]:
                try:
                    value = var_data.get_variable("GOOG", var_name, period="latest")
                    if value is not None:
                        print(f"    {var_name}: {value}")
                    else:
                        print(f"    {var_name}: None")
                except Exception as e:
                    print(f"    {var_name}: Error - {str(e)}")
        
        return results['variables_extracted'] > 0 and results['data_points_stored'] > 0
        
    except Exception as e:
        print(f"- Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_extraction_tests():
    """Run extraction tests"""
    print("Excel Adapter Extraction Test")
    print("=" * 40)
    
    tests = [
        ("Single File Extraction", test_single_file_extraction)
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
        success = run_extraction_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(1)