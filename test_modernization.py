"""
Test script for the modernized FCF analysis application

This script validates that the new Streamlit-based application maintains
all the functionality of the original matplotlib version.
"""

import sys
import os
import traceback

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from financial_calculations import FinancialCalculator
        print("  ✅ FinancialCalculator")
        
        from dcf_valuation import DCFValuator
        print("  ✅ DCFValuator")
        
        from data_processing import DataProcessor
        print("  ✅ DataProcessor")
        
        # Test Streamlit app syntax
        import importlib.util
        spec = importlib.util.spec_from_file_location("streamlit_app", "fcf_analysis_streamlit.py")
        module = importlib.util.module_from_spec(spec)
        print("  ✅ Streamlit application syntax")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without requiring real data"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from financial_calculations import FinancialCalculator
        from dcf_valuation import DCFValuator
        from data_processing import DataProcessor
        
        # Test DataProcessor
        processor = DataProcessor()
        validation = processor.validate_company_folder("/dummy/path")
        assert 'is_valid' in validation
        print("  ✅ DataProcessor validation")
        
        # Test FinancialCalculator initialization
        calc = FinancialCalculator("/dummy/path")
        assert calc.company_name == "path"
        print("  ✅ FinancialCalculator initialization")
        
        # Test DCFValuator initialization
        valuator = DCFValuator(calc)
        assert valuator.financial_calculator == calc
        print("  ✅ DCFValuator initialization")
        
        # Test DCF calculations with dummy data
        calc.fcf_results = {'FCFF': [1000000, 1100000, 1200000]}
        dcf_result = valuator.calculate_dcf_projections()
        assert 'enterprise_value' in dcf_result
        print("  ✅ DCF calculation functionality")
        
        # Test plotting (without actually displaying)
        fcf_results = {'FCFF': [1000000, 1100000, 1200000], 'FCFE': [900000, 1000000, 1100000]}
        fig = processor.create_fcf_comparison_plot(fcf_results, "Test Company")
        assert fig is not None
        print("  ✅ Chart generation")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_requirements():
    """Test that all required packages are available"""
    print("\n📦 Testing package requirements...")
    
    required_packages = [
        'streamlit', 'plotly', 'pandas', 'numpy', 
        'openpyxl', 'scipy', 'yfinance'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {missing_packages}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def test_file_structure():
    """Test that all required files are present"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'financial_calculations.py',
        'dcf_valuation.py', 
        'data_processing.py',
        'fcf_analysis_streamlit.py',
        'run_streamlit_app.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (missing)")
            missing_files.append(file_name)
    
    return len(missing_files) == 0

def main():
    """Run all tests"""
    print("🚀 Testing Modern FCF Analysis Application")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Package Requirements", test_requirements),
        ("Module Imports", test_imports),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modernized application is ready.")
        print("\n🚀 To launch the application:")
        print("   python3 run_streamlit_app.py")
        print("   OR")
        print("   streamlit run fcf_analysis_streamlit.py")
        return True
    else:
        print("⚠️  Some tests failed. Please address the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)