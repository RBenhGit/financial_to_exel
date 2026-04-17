#!/usr/bin/env python3
"""
Test Excel Adapter with populated registry
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.WARNING)

def test_with_populated_registry():
    """Test the Excel adapter with a populated registry"""
    print("Testing Excel Adapter with Populated Registry")
    print("=" * 50)
    
    try:
        # Import required modules
        from core.data_processing.financial_variable_registry import get_registry
        from core.data_processing.standard_financial_variables import register_all_variables
        from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
        from core.data_processing.var_input_data import get_var_input_data, clear_cache
        
        # Step 1: Populate the registry
        print("1. Populating financial variable registry...")
        registry = get_registry()
        registration_results = register_all_variables(registry)
        
        all_vars = registry.list_all_variables()
        print(f"   Registered {len(all_vars)} variables")
        print(f"   Registration results: {registration_results}")
        
        # Show some examples
        income_vars = [var for var in all_vars 
                      if registry.get_variable_definition(var) and 
                      registry.get_variable_definition(var).category.value == 'income_statement']
        print(f"   Income statement variables: {len(income_vars)}")
        print(f"   Examples: {income_vars[:5]}")
        
        # Step 2: Test single file extraction
        print("\n2. Testing single file extraction...")
        clear_cache()
        
        test_file = "data/companies/GOOG/FY/Alphabet Inc Class C - Income Statement.xlsx"
        
        if not os.path.exists(test_file):
            print(f"   Test file not found: {test_file}")
            return False
        
        adapter = ExcelDataAdapter()
        var_data = get_var_input_data()
        
        results = adapter.load_single_file(
            symbol="GOOG",
            file_path=test_file,
            sheet_type="income", 
            period_type="FY",
            validate_data=True
        )
        
        print(f"   Variables extracted: {results['variables_extracted']}")
        print(f"   Data points stored: {results['data_points_stored']}")
        print(f"   Quality score: {results['quality_score']}")
        print(f"   Errors: {len(results.get('errors', []))}")
        
        if results.get('errors'):
            print("   First few errors:")
            for error in results['errors'][:2]:
                print(f"     - {error}")
        
        # Step 3: Test data retrieval
        print("\n3. Testing data retrieval...")
        available_vars = var_data.get_available_variables("GOOG")
        print(f"   Available GOOG variables: {len(available_vars)}")
        
        if available_vars:
            print(f"   Examples: {available_vars[:5]}")
            
            # Test retrieving specific variables
            for var_name in available_vars[:3]:
                try:
                    value = var_data.get_variable("GOOG", var_name, period="latest")
                    periods = var_data.get_available_periods("GOOG", var_name)
                    print(f"   {var_name}: {value} (periods: {len(periods)})")
                except Exception as e:
                    print(f"   {var_name}: Error - {str(e)}")
        
        # Step 4: Test with multiple files
        print("\n4. Testing company data loading...")
        clear_cache()
        
        company_path = "data/companies/GOOG"
        company_results = adapter.load_company_data(
            symbol="GOOG",
            company_data_path=company_path,
            load_fy=True,
            load_ltm=False,
            max_historical_years=10,
            validate_data=True
        )
        
        print(f"   Files processed: {company_results['files_processed']}")
        print(f"   Variables loaded: {company_results['variables_loaded']}")
        print(f"   Data points loaded: {company_results['data_points_loaded']}")
        
        # Get final statistics
        stats = adapter.get_adapter_statistics()
        print(f"\n5. Final Statistics:")
        print(f"   Registry variables: {stats['registry_info']['total_variables']}")
        print(f"   Adapter files processed: {stats['adapter_stats']['files_processed']}")
        print(f"   VarData symbols: {stats['var_data_stats']['data_storage']['symbols']}")
        
        success = (results['variables_extracted'] > 0 and 
                  results['data_points_stored'] > 0 and 
                  len(available_vars) > 0)
        
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    success = test_with_populated_registry()
    sys.exit(0 if success else 1)