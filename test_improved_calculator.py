"""
Test the improved calculator with your GOOG data
"""

import sys
import os
from improved_financial_calculations import ImprovedFinancialCalculator

def test_goog_data():
    """Test with the GOOG folder"""
    # Use relative path that works in both environments
    company_folder = "GOOG"
    
    print(f"🧪 Testing improved calculator with: {company_folder}")
    print("=" * 60)
    
    try:
        # Initialize calculator
        calc = ImprovedFinancialCalculator(company_folder)
        
        # Load statements
        print("📊 Loading financial statements...")
        calc.load_financial_statements()
        
        # Show what was loaded
        print("\n📋 Loaded data:")
        for key, data in calc.financial_data.items():
            if not data.empty:
                print(f"  ✅ {key}: {data.shape} (rows x cols)")
                # Show first few rows of first column
                first_col = data.iloc[:5, 0].tolist()
                print(f"     Sample metrics: {first_col}")
            else:
                print(f"  ❌ {key}: Empty")
        
        # Calculate FCF
        print("\n💰 Calculating FCF...")
        fcf_results = calc.calculate_all_fcf_types()
        
        print("\n🎯 FCF Results:")
        for fcf_type, values in fcf_results.items():
            if values:
                print(f"  ✅ {fcf_type}: {len(values)} years")
                recent_values = [f"${v/1e6:.1f}M" for v in values[-3:]]
                print(f"     Recent values: {recent_values}")
            else:
                print(f"  ❌ {fcf_type}: No data")
        
        return len([v for v in fcf_results.values() if v]) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_goog_data()
    if success:
        print("\n🎉 SUCCESS: Improved calculator is working!")
    else:
        print("\n❌ Still having issues - may need manual inspection of Excel files")
    
    print("\nNext step: Try the Streamlit app with the improved calculator")