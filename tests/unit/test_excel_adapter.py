#!/usr/bin/env python3
"""
Excel Data Adapter Test Script
=============================

Test script to verify the ExcelDataAdapter functionality with real Excel files.
This script will test the adapter with actual company data to ensure proper
integration with VarInputData and FinancialVariableRegistry.
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.data_processing.adapters.excel_adapter import ExcelDataAdapter, load_company_excel_data
from core.data_processing.var_input_data import get_var_input_data, clear_cache
from core.data_processing.financial_variable_registry import get_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_excel_adapter():
    """Test the Excel adapter with real data files"""
    
    print("Testing Excel Data Adapter")
    print("=" * 50)
    
    # Clear any existing cache
    print("Clearing existing cache...")
    clear_cache()
    
    # Initialize components
    print("Initializing adapter and registries...")
    adapter = ExcelDataAdapter()
    var_data = get_var_input_data()
    registry = get_registry()
    
    print(f"Registry has {len(registry.list_all_variables())} variables defined")
    
    # Test with Google (GOOG) data since we know it exists
    company_symbol = "GOOG"
    company_data_path = "data/companies/GOOG"
    
    if not os.path.exists(company_data_path):
        print(f"Company data path not found: {company_data_path}")
        return False
    
    print(f"Testing with {company_symbol} data from {company_data_path}")
    
    try:
        # Load company data
        print("Loading company data...")
        results = adapter.load_company_data(
            symbol=company_symbol,
            company_data_path=company_data_path,
            load_fy=True,
            load_ltm=True,
            max_historical_years=10,
            validate_data=True
        )
        
        # Display results
        print("\n📈 Loading Results:")
        print(f"  Symbol: {results['symbol']}")
        print(f"  Files processed: {results['files_processed']}")
        print(f"  Variables loaded: {results['variables_loaded']}")
        print(f"  Data points loaded: {results['data_points_loaded']}")
        
        if results['errors']:
            print(f"  Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"    - {error}")
        
        # Test specific variable retrieval
        print("\n🔍 Testing variable retrieval...")
        
        # Try to get some common variables
        test_variables = ['revenue', 'net_income', 'total_assets', 'operating_cash_flow']
        
        for var_name in test_variables:
            try:
                value = var_data.get_variable(company_symbol, var_name, period="latest")
                if value is not None:
                    print(f"  ✅ {var_name}: {value}")
                else:
                    print(f"  ❌ {var_name}: Not found")
            except Exception as e:
                print(f"  ⚠️ {var_name}: Error - {str(e)}")
        
        # Get historical data for revenue
        print("\n📊 Testing historical data retrieval...")
        try:
            historical_revenue = var_data.get_historical_data(company_symbol, "revenue", years=5)
            if historical_revenue:
                print(f"  📈 Revenue history ({len(historical_revenue)} periods):")
                for period, value in historical_revenue[:3]:  # Show first 3 periods
                    print(f"    {period}: ${value}M")
            else:
                print("  ❌ No historical revenue data found")
        except Exception as e:
            print(f"  ⚠️ Historical data error: {str(e)}")
        
        # Get adapter statistics
        print("\n📊 Adapter Statistics:")
        stats = adapter.get_adapter_statistics()
        adapter_stats = stats['adapter_stats']
        
        print(f"  Files processed: {adapter_stats['files_processed']}")
        print(f"  Variables extracted: {adapter_stats['variables_extracted']}")
        print(f"  Data points loaded: {adapter_stats['data_points_loaded']}")
        print(f"  Validation failures: {adapter_stats['validation_failures']}")
        print(f"  Unit conversions: {adapter_stats['conversion_applied']}")
        
        # Get VarInputData statistics
        var_data_stats = stats['var_data_stats']
        print(f"\n💾 VarInputData Statistics:")
        print(f"  Symbols in cache: {var_data_stats['data_storage']['symbols']}")
        print(f"  Unique variables: {var_data_stats['data_storage']['unique_variables']}")
        print(f"  Total data points: {var_data_stats['data_storage']['total_data_points']}")
        print(f"  Cache hit rate: {var_data_stats['cache_hit_rate']:.2%}")
        
        success = results['variables_loaded'] > 0 and results['data_points_loaded'] > 0
        
        if success:
            print("\n✅ Excel Adapter Test PASSED!")
        else:
            print("\n❌ Excel Adapter Test FAILED - No data loaded")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        logger.exception("Test execution failed")
        return False


def test_single_file():
    """Test loading a single Excel file"""
    
    print("\n🎯 Testing single file loading...")
    
    # Test with a specific file
    test_file = "data/companies/GOOG/FY/Alphabet Inc Class C - Income Statement.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        adapter = ExcelDataAdapter()
        
        results = adapter.load_single_file(
            symbol="GOOG",
            file_path=test_file,
            sheet_type="income",
            period_type="FY",
            validate_data=True
        )
        
        print(f"📋 Single File Results:")
        print(f"  File: {results['file_path']}")
        print(f"  Variables extracted: {results['variables_extracted']}")
        print(f"  Data points stored: {results['data_points_stored']}")
        print(f"  Periods covered: {results['periods_covered']}")
        print(f"  Quality score: {results['quality_score']}")
        
        if results['errors']:
            print(f"  Errors: {len(results['errors'])}")
            for error in results['errors'][:2]:
                print(f"    - {error}")
        
        return results['variables_extracted'] > 0
        
    except Exception as e:
        print(f"💥 Single file test failed: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        print("🧪 Excel Data Adapter Test Suite")
        print("================================\n")
        
        # Run tests
        test1_passed = test_excel_adapter()
        test2_passed = test_single_file()
        
        # Summary
        print("\n" + "=" * 50)
        print("📝 Test Summary:")
        print(f"  Full company data test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"  Single file test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests PASSED! Excel Adapter is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests FAILED. Check the logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
        logger.exception("Test suite execution failed")
        sys.exit(1)