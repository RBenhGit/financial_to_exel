"""
Test script for enhanced FCF date correlation system
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import logging
from pathlib import Path
from core.analysis.engines.financial_calculations import FinancialCalculator
# from core.excel_integration.excel_utils import get_fy_ltm_correlated_dates, get_structured_period_dates_from_excel
# Note: These functions are not implemented yet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_date_extraction():
    """Test the enhanced date extraction functions"""
    logger.info("Testing enhanced date extraction...")
    
    # Test with MSFT data if available
    msft_folder = Path("data/companies/MSFT")
    if msft_folder.exists():
        logger.info("Testing with MSFT data")
        
        # Test basic date extraction with available functions
        ltm_income = msft_folder / "LTM" / "Microsoft Corporation - Income Statement.xlsx"
        if ltm_income.exists():
            logger.info(f"Testing basic date extraction from: {ltm_income}")
            from core.excel_integration.excel_utils import get_period_dates_from_excel
            date_info = get_period_dates_from_excel(str(ltm_income))
            logger.info(f"Extracted date info: {date_info}")
            return date_info
        
        logger.warning("LTM Income Statement not found")
        return None
    else:
        logger.warning("MSFT test data not found, creating mock test")
        return None


def test_enhanced_fcf_calculation():
    """Test the enhanced FCF calculation system"""
    logger.info("Testing enhanced FCF calculation...")
    
    # Use any available company folder for testing
    test_folders = ["data/companies/MSFT", "V", "TSLA", "GOOG", "NVDA"]
    
    for folder in test_folders:
        if Path(folder).exists():
            logger.info(f"Testing FCF calculation with: {folder}")
            
            try:
                # Create financial calculator
                calc = FinancialCalculator(folder)
                
                # Test enhanced date correlation initialization
                correlation_success = calc.initialize_enhanced_date_correlation()
                logger.info(f"Date correlation initialization: {correlation_success}")
                
                # Load financial data
                calc.load_financial_statements()
                
                # Calculate FCF with enhanced correlation
                fcf_results = calc.calculate_all_fcf_types()
                logger.info(f"Legacy FCF results: {list(fcf_results.keys())}")
                
                # Get enhanced FCF results
                comprehensive_results = calc.get_comprehensive_fcf_results()
                logger.info(f"Enhanced FCF types: {list(comprehensive_results.results.keys())}")
                
                # Test date correlation summary
                date_summary = calc.get_date_correlation_summary()
                logger.info(f"Date correlation summary: {date_summary}")
                
                # Test individual FCF type with dates
                for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
                    if fcf_type in comprehensive_results.results:
                        fcf_with_dates = calc.get_fcf_with_dates(fcf_type)
                        logger.info(f"{fcf_type} with dates: {len(fcf_with_dates.get('values', []))} values, {len(fcf_with_dates.get('dates', []))} dates")
                        if fcf_with_dates.get('dates'):
                            logger.info(f"{fcf_type} date range: {fcf_with_dates['dates'][0]} to {fcf_with_dates['dates'][-1]}")
                
                return calc
                
            except Exception as e:
                logger.error(f"Error testing {folder}: {e}")
                continue
    
    logger.warning("No suitable test folders found")
    return None


def main():
    """Main test function"""
    logger.info("Starting enhanced FCF date correlation tests")
    
    # Test 1: Date extraction
    date_extraction_result = test_date_extraction()
    
    # Test 2: Enhanced FCF calculation
    calc_result = test_enhanced_fcf_calculation()
    
    # Summary
    if calc_result:
        logger.info("Enhanced FCF correlation system test completed successfully!")
        
        # Print final summary
        summary = calc_result.get_date_correlation_summary()
        print("\n" + "="*60)
        print("ENHANCED FCF DATE CORRELATION TEST SUMMARY")
        print("="*60)
        print(f"Common date pattern: {summary.get('common_date_pattern')}")
        print(f"Correlation quality: {summary.get('correlation_quality')}")
        print(f"Source distribution: {summary.get('source_type_distribution')}")
        print(f"Date ranges: {summary.get('date_ranges')}")
        print("="*60)
        
    else:
        logger.error("Enhanced FCF correlation system test failed!")


if __name__ == "__main__":
    main()