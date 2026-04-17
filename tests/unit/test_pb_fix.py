#!/usr/bin/env python3
"""
Test the fixed P/B historical analysis functionality.
"""

import sys
import os
import logging
from datetime import datetime

# Add project path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pb_historical_analysis():
    """Test the P/B historical analysis with the fixes."""
    
    try:
        # Import the PB valuation class
        from core.analysis.pb.pb_valuation import PBValuator
        
        # Create instance with minimal setup
        pb_valuator = PBValuator(financial_calculator=None)
        
        # Test with GOOGL (which worked in our debug)
        ticker_symbol = 'GOOGL'
        logger.info(f"Testing P/B historical analysis for {ticker_symbol}")
        
        # Call the historical analysis method directly
        result = pb_valuator._analyze_historical_pb(ticker_symbol, years=5)
        
        logger.info(f"Result for {ticker_symbol}: {result}")
        
        if 'error' in result:
            logger.error(f"Error in P/B historical analysis: {result['error']}")
            return False
        else:
            logger.info("P/B historical analysis successful!")
            # Print some key statistics
            if 'statistics' in result:
                stats = result['statistics']
                logger.info(f"Historical P/B statistics:")
                logger.info(f"  Mean P/B: {stats.get('mean', 'N/A'):.2f}")
                logger.info(f"  Min P/B: {stats.get('min', 'N/A'):.2f}")
                logger.info(f"  Max P/B: {stats.get('max', 'N/A'):.2f}")
                logger.info(f"  Data points: {result.get('data_points', 'N/A')}")
            return True
            
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pb_historical_analysis()
    logger.info(f"Test result: {'SUCCESS' if success else 'FAILED'}")