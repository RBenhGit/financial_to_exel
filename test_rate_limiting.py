#!/usr/bin/env python3
"""
Test the enhanced rate limiting implementation
"""

import sys
import logging
from centralized_data_manager import CentralizedDataManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_rate_limiting():
    """Test the enhanced Yahoo Finance rate limiting"""
    print("Testing enhanced Yahoo Finance rate limiting...")
    
    try:
        # Create manager instance with current directory
        manager = CentralizedDataManager(base_path=".")
        
        # Test with ASML (the ticker from the error log)
        print("Attempting to fetch market data for ASML...")
        result = manager.fetch_market_data('ASML', force_reload=True)
        
        if result:
            print(f"SUCCESS: Fetched data for {result.get('ticker')} at ${result.get('current_price')}")
            
            # Check if fallback was used
            if 'fallback_source' in result:
                print(f"Used fallback source: {result['fallback_source']}")
                if result['fallback_source'] == 'placeholder':
                    print("WARNING: Using placeholder data - all APIs failed")
            else:
                print("Data fetched from primary source (Yahoo Finance)")
                
            # Show key metrics
            print(f"Company: {result.get('company_name', 'N/A')}")
            print(f"Market Cap: ${result.get('market_cap', 0):.2f}M")
            print(f"Shares Outstanding: {result.get('shares_outstanding', 0):,.0f}")
            
        else:
            print("FAILED: Could not fetch market data from any source")
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_rate_limiting()