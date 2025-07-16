#!/usr/bin/env python3
"""
Test script for the updated report generator
"""

import os
import sys
import tempfile
import logging

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_generator import FCFReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_report_generation():
    """Test report generation with various data scenarios"""
    
    # Test scenario 1: Empty/missing data
    print("Testing scenario 1: Empty/missing data")
    try:
        generator = FCFReportGenerator()
        pdf_bytes = generator.generate_report(
            company_name="Test Company",
            fcf_results={},
            dcf_results={},
            dcf_assumptions={},
            fcf_plots={},
            dcf_plots={},
            growth_analysis_df=None,
            fcf_data_df=None,
            dcf_projections_df=None,
            current_price=None,
            ticker="TEST",
            sensitivity_params=None,
            user_decisions=None
        )
        
        if pdf_bytes:
            print("✅ Empty data scenario - Report generated successfully")
        else:
            print("❌ Empty data scenario - Failed to generate report")
            
    except Exception as e:
        print(f"❌ Empty data scenario - Error: {e}")
    
    # Test scenario 2: FCF only
    print("\nTesting scenario 2: FCF data only")
    try:
        fcf_results = {
            'LFCF': [100, 120, 140, 160, 180],
            'FCFE': [80, 95, 110, 125, 140],
            'FCFF': [120, 135, 150, 165, 180]
        }
        
        pdf_bytes = generator.generate_report(
            company_name="Test Company",
            fcf_results=fcf_results,
            dcf_results={},
            dcf_assumptions={},
            fcf_plots={},
            dcf_plots={},
            growth_analysis_df=None,
            fcf_data_df=None,
            dcf_projections_df=None,
            current_price=50.0,
            ticker="TEST",
            sensitivity_params=None,
            user_decisions=None
        )
        
        if pdf_bytes:
            print("✅ FCF only scenario - Report generated successfully")
        else:
            print("❌ FCF only scenario - Failed to generate report")
            
    except Exception as e:
        print(f"❌ FCF only scenario - Error: {e}")
    
    # Test scenario 3: DCF only
    print("\nTesting scenario 3: DCF data only")
    try:
        dcf_results = {
            'enterprise_value': 1000.0,
            'value_per_share': 55.0,
            'terminal_value': 800.0,
            'pv_fcf_total': 200.0
        }
        
        dcf_assumptions = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.025,
            'growth_rate_yr1_5': 0.05,
            'fcf_type': 'LFCF'
        }
        
        pdf_bytes = generator.generate_report(
            company_name="Test Company",
            fcf_results={},
            dcf_results=dcf_results,
            dcf_assumptions=dcf_assumptions,
            fcf_plots={},
            dcf_plots={},
            growth_analysis_df=None,
            fcf_data_df=None,
            dcf_projections_df=None,
            current_price=50.0,
            ticker="TEST",
            sensitivity_params=None,
            user_decisions=None
        )
        
        if pdf_bytes:
            print("✅ DCF only scenario - Report generated successfully")
        else:
            print("❌ DCF only scenario - Failed to generate report")
            
    except Exception as e:
        print(f"❌ DCF only scenario - Error: {e}")
    
    print("\nReport generation tests completed!")

if __name__ == "__main__":
    test_report_generation()