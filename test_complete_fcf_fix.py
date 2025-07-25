#!/usr/bin/env python3
"""
Test the complete FCF calculation after field mapping fix
"""

import logging
import warnings
warnings.filterwarnings('ignore')

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_fcf():
    """Test complete FCF calculation with the fixed field mapping"""
    
    print("Testing complete FCF calculation for AAPL...")
    
    try:
        # Import the necessary modules
        from fcf_analysis_streamlit import create_ticker_mode_calculator
        
        print("1. Creating ticker mode calculator...")
        calculator, error = create_ticker_mode_calculator("AAPL", "US Market")
        
        if error:
            print(f"Error creating calculator: {error}")
            return False
            
        if not calculator:
            print("Failed to create calculator")
            return False
            
        print("2. Calculator created successfully!")
        
        # Test the comprehensive financial calculations
        print("3. Testing comprehensive FCF calculation...")
        try:
            fcf_results = calculator.calculate_all_fcf_types()
            
            print("4. FCF Calculation Results:")
            if fcf_results:
                for fcf_type, values in fcf_results.items():
                    if values:
                        print(f"  {fcf_type}: {len(values)} years of data")
                        print(f"    Latest value: ${values[-1]:.1f}M")
                        if len(values) > 1:
                            print(f"    Average: ${sum(values)/len(values):.1f}M")
                    else:
                        print(f"  {fcf_type}: No data")
                
                # Check if we have successful FCF calculations
                successful_calcs = sum(1 for values in fcf_results.values() if values)
                print(f"\n  Successfully calculated {successful_calcs} FCF types")
                
                if successful_calcs > 0:
                    print("SUCCESS: FCF calculations are now working!")
                    return True
                else:
                    print("FAILED: No FCF calculations successful")
                    return False
            else:
                print("FAILED: No FCF results returned")
                return False
                
        except Exception as e:
            print(f"Error in FCF calculation: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"Error in test setup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_fcf()
    print(f"\n=== FINAL RESULT ===")
    if success:
        print("Field mapping fix SUCCESSFUL - FCF calculations now work!")
    else:
        print("Field mapping fix INCOMPLETE - still need more work")
    
    exit(0 if success else 1)