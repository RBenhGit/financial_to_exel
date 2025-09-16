#!/usr/bin/env python3
"""
Quick test to verify P/B analysis works in the Streamlit context.
"""

import sys
import os
import logging

# Add project path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pb_with_financial_calculator():
    """Test P/B analysis with financial calculator setup like in Streamlit."""
    try:
        from core.analysis.engines.financial_calculations import FinancialCalculator
        from core.analysis.pb.pb_valuation import PBValuator
        
        # Create financial calculator (like in Streamlit)
        company_folder = f"data/companies/GOOGL"  # This may not exist, but we're testing P/B API mode
        financial_calculator = FinancialCalculator(company_folder)
        financial_calculator.ticker_symbol = 'GOOGL'
        
        # Create P/B valuator
        pb_valuator = PBValuator(financial_calculator)
        
        # Run P/B analysis
        logger.info("Running full P/B analysis...")
        pb_analysis = pb_valuator.calculate_pb_analysis('GOOGL')
        
        if 'error' in pb_analysis:
            logger.error(f"P/B analysis failed: {pb_analysis['error']}")
            return False
            
        # Check historical analysis specifically
        historical = pb_analysis.get('historical_analysis', {})
        if 'error' in historical:
            logger.error(f"Historical analysis failed: {historical['error']}")
            return False
        
        logger.info("✅ P/B Analysis successful!")
        logger.info(f"Current P/B ratio: {pb_analysis.get('current_data', {}).get('pb_ratio', 'N/A')}")
        
        if 'statistics' in historical:
            stats = historical['statistics']
            logger.info(f"Historical P/B - Mean: {stats.get('mean', 'N/A'):.2f}, Range: {stats.get('min', 'N/A'):.2f} - {stats.get('max', 'N/A'):.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pb_with_financial_calculator()
    logger.info(f"Full P/B test result: {'SUCCESS' if success else 'FAILED'}")