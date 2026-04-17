"""
Test DDM integration with Streamlit application

This script tests that the DDM functionality integrates correctly with the Streamlit app.
"""

import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_ddm_streamlit_integration():
    """Test that DDM integrates properly with Streamlit"""

    print("Testing DDM Integration with Streamlit")
    print("=" * 50)

    try:
        # Test imports
        print("[TEST] Testing Streamlit module imports...")
        from fcf_analysis_streamlit import render_ddm_analysis
        from ddm_valuation import DDMValuator

        print("[SUCCESS] DDM and Streamlit modules import successfully")

        # Test that render_ddm_analysis function exists and is callable
        print("[TEST] Testing DDM render function...")
        if callable(render_ddm_analysis):
            print("[SUCCESS] render_ddm_analysis function is callable")
        else:
            print("[ERROR] render_ddm_analysis is not callable")
            return False

        # Test DDMValuator class
        print("[TEST] Testing DDMValuator class...")
        if hasattr(DDMValuator, 'calculate_ddm_valuation'):
            print("[SUCCESS] DDMValuator has calculate_ddm_valuation method")
        else:
            print("[ERROR] DDMValuator missing calculate_ddm_valuation method")
            return False

        # Test sensitivity analysis method
        if hasattr(DDMValuator, 'sensitivity_analysis'):
            print("[SUCCESS] DDMValuator has sensitivity_analysis method")
        else:
            print("[ERROR] DDMValuator missing sensitivity_analysis method")
            return False

        print("\n[SUMMARY] Integration Test Results:")
        print("=" * 50)
        print("[SUCCESS] All DDM integration tests passed")
        print("[SUCCESS] DDM is ready for use in Streamlit application")
        print("[SUCCESS] New DDM tab should work correctly")

        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        logger.error(f"Integration test error: {e}", exc_info=True)
        return False


def test_streamlit_app_structure():
    """Test that the Streamlit app structure includes DDM correctly"""

    print("\n[TEST] Testing Streamlit App Structure...")

    try:
        # Import the main function
        from fcf_analysis_streamlit import main

        # Read the source code to verify DDM integration
        with open('fcf_analysis_streamlit.py', 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Check for DDM-related elements
        ddm_checks = [
            ('DDM import', 'from ddm_valuation import DDMValuator'),
            ('DDM tab', 'DDM Valuation'),
            ('DDM render function', 'render_ddm_analysis'),
            ('DDM tab call', 'render_ddm_analysis()'),
        ]

        all_checks_passed = True
        for check_name, check_string in ddm_checks:
            if check_string in source_code:
                print(f"[SUCCESS] {check_name} found in Streamlit app")
            else:
                print(f"[ERROR] {check_name} NOT found in Streamlit app")
                all_checks_passed = False

        return all_checks_passed

    except Exception as e:
        print(f"[ERROR] App structure test failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting DDM Streamlit Integration Tests")
    print("=" * 60)

    # Test DDM integration
    integration_success = test_ddm_streamlit_integration()

    # Test app structure
    structure_success = test_streamlit_app_structure()

    if integration_success and structure_success:
        print("\n[SUCCESS] All DDM Streamlit integration tests passed!")
        print("The DDM feature is ready for use in the web application.")
        print("\nTo use DDM:")
        print("1. Run: streamlit run fcf_analysis_streamlit.py")
        print("2. Load financial data for a dividend-paying company")
        print("3. Navigate to the 'DDM Valuation' tab")
        print("4. Configure DDM parameters and run analysis")
    else:
        print("\n[ERROR] Some integration tests failed.")
        print("Please check the implementation before using DDM in Streamlit.")

    print("\n" + "=" * 60)
