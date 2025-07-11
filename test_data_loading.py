"""
Quick test script to debug data loading issues

Usage: python test_data_loading.py <path_to_company_folder>
"""

import sys
import os
from financial_calculations import FinancialCalculator

def test_data_loading(company_folder):
    """Test the data loading process step by step"""
    print(f"🧪 Testing data loading for: {company_folder}")
    print("=" * 60)
    
    # Test 1: Check folder exists
    print("1. Checking folder exists...")
    if not os.path.exists(company_folder):
        print(f"❌ Folder does not exist: {company_folder}")
        return False
    print("✅ Folder exists")
    
    # Test 2: Check required subfolders
    print("\n2. Checking required subfolders...")
    required_folders = ['FY', 'LTM']
    for folder in required_folders:
        folder_path = os.path.join(company_folder, folder)
        if os.path.exists(folder_path):
            print(f"✅ {folder}/ exists")
            files = [f for f in os.listdir(folder_path) if f.endswith(('.xlsx', '.xls'))]
            print(f"   Found {len(files)} Excel files: {files}")
        else:
            print(f"❌ {folder}/ missing")
    
    # Test 3: Initialize calculator
    print("\n3. Initializing FinancialCalculator...")
    try:
        calc = FinancialCalculator(company_folder)
        print("✅ FinancialCalculator created")
    except Exception as e:
        print(f"❌ Failed to create FinancialCalculator: {e}")
        return False
    
    # Test 4: Load financial statements
    print("\n4. Loading financial statements...")
    try:
        calc.load_financial_statements()
        print("✅ Financial statements loaded")
        
        # Show what was loaded
        for key, data in calc.financial_data.items():
            if not data.empty:
                print(f"   ✅ {key}: {data.shape} (rows x cols)")
            else:
                print(f"   ❌ {key}: Empty DataFrame")
                
    except Exception as e:
        print(f"❌ Failed to load financial statements: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Calculate FCF
    print("\n5. Calculating FCF...")
    try:
        fcf_results = calc.calculate_all_fcf_types()
        print("✅ FCF calculation completed")
        
        for fcf_type, values in fcf_results.items():
            if values:
                print(f"   ✅ {fcf_type}: {len(values)} years of data")
                print(f"      Values: {[f'{v/1e6:.1f}M' for v in values[-3:]]}")  # Show last 3 years
            else:
                print(f"   ❌ {fcf_type}: No data")
                
    except Exception as e:
        print(f"❌ Failed to calculate FCF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    
    # Summary
    total_fcf_types = len(fcf_results)
    successful_fcf_types = len([v for v in fcf_results.values() if v])
    
    if successful_fcf_types > 0:
        print(f"✅ SUCCESS: {successful_fcf_types}/{total_fcf_types} FCF types calculated")
        return True
    else:
        print(f"❌ ISSUE: 0/{total_fcf_types} FCF types calculated")
        print("\nPossible issues:")
        print("- Excel files don't contain expected metric names")
        print("- Data format is different than expected")
        print("- Files are empty or corrupted")
        print("\nRun: python diagnose_data.py <folder> for detailed analysis")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_data_loading.py <path_to_company_folder>")
        print("\nExample:")
        print("  python test_data_loading.py C:/data/AAPL")
        sys.exit(1)
    
    company_folder = sys.argv[1]
    success = test_data_loading(company_folder)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()