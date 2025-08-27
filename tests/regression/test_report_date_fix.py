"""
Test script to verify that report dates are properly extracted from enhanced FCF correlation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import logging
from pathlib import Path
from core.analysis.engines.financial_calculations import FinancialCalculator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_report_date_extraction():
    """Test that report dates are properly extracted using enhanced correlation"""
    
    logger.info("Testing report date extraction with enhanced FCF correlation")
    
    # Test with NVDA data (what's currently running in Streamlit)
    nvda_folder = "data/companies/NVDA"
    
    if not Path(nvda_folder).exists():
        logger.warning("NVDA data not found, testing with any available company")
        # Try other companies
        test_folders = ["data/companies/MSFT", "V", "TSLA", "GOOG"]
        nvda_folder = None
        for folder in test_folders:
            if Path(folder).exists():
                nvda_folder = folder
                break
    
    if not nvda_folder:
        logger.error("No test data found")
        return False
    
    logger.info(f"Testing with: {nvda_folder}")
    
    try:
        # Create financial calculator
        calc = FinancialCalculator(nvda_folder)
        calc.load_financial_statements()
        
        # Calculate FCF with enhanced correlation
        fcf_results = calc.calculate_all_fcf_types()
        logger.info(f"FCF calculation completed: {list(fcf_results.keys())}")
        
        # Test 1: Get enhanced FCF results with dates
        enhanced_results = calc.get_fcf_results_with_dates()
        logger.info(f"Enhanced results available: {bool(enhanced_results)}")
        
        if enhanced_results:
            for fcf_type, fcf_data in enhanced_results.items():
                if fcf_type != 'metadata' and isinstance(fcf_data, dict):
                    dates = fcf_data.get('dates', [])
                    values = fcf_data.get('values', [])
                    sources = fcf_data.get('sources', [])
                    
                    logger.info(f"{fcf_type}: {len(dates)} dates, {len(values)} values")
                    if dates:
                        logger.info(f"  Date range: {dates[0]} to {dates[-1]}")
                        logger.info(f"  Sources: {sources}")
        
        # Test 2: Extract latest date using our new logic
        latest_date = "Unknown"
        if enhanced_results:
            all_dates = []
            for fcf_type, fcf_data in enhanced_results.items():
                if fcf_type != 'metadata' and isinstance(fcf_data, dict) and 'dates' in fcf_data:
                    if fcf_data['dates']:
                        all_dates.extend(fcf_data['dates'])
            
            if all_dates:
                latest_date = max(all_dates)
                logger.info(f"✓ Latest date extracted: {latest_date}")
            else:
                logger.warning("No dates found in enhanced results")
        
        # Test 3: Compare with original method
        try:
            original_date = calc.get_latest_report_date()
            logger.info(f"Original method date: {original_date}")
        except Exception as e:
            logger.info(f"Original method failed: {e}")
            original_date = "Unknown"
        
        # Test 4: Check that we're getting actual report dates, not today's date
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        if latest_date != "Unknown" and not latest_date.startswith(today[:4]):  # Not this year
            logger.info(f"✓ SUCCESS: Using actual report date ({latest_date}), not today's date")
        elif latest_date == "Unknown":
            logger.warning("⚠️  Latest date is Unknown - this needs investigation")
        else:
            logger.info(f"ℹ️  Latest date ({latest_date}) appears to be recent - this might be correct for LTM data")
        
        return latest_date != "Unknown"
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_report_date_extraction()
    if success:
        logger.info("✓ Report date extraction test completed successfully")
    else:
        logger.error("❌ Report date extraction test failed")
    
    sys.exit(0 if success else 1)