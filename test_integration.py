#!/usr/bin/env python3
"""
Test script for the centralized integration layer.
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from centralized_integration import CentralizedFinancialCalculator, create_centralized_calculator
from financial_calculations import FinancialCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compare_calculators():
    """Compare original and centralized calculators"""
    
    print("=" * 70)
    print("COMPARING ORIGINAL VS CENTRALIZED FINANCIAL CALCULATORS")
    print("=" * 70)
    
    company_folder = '/mnt/c/AsusWebStorage/ran@benhur.co/MySyncFolder/python/investingAnalysis/financial_to_exel/TSLA'
    
    # Test 1: Original Calculator
    print("\\n1. Testing Original FinancialCalculator...")
    try:
        original_calc = FinancialCalculator(company_folder)
        original_result = original_calc.calculate_all_fcf_types()
        
        if original_result and 'FCFF' in original_result:
            print("✅ Original calculator successful")
            print(f"   - FCFF: {len(original_result['FCFF'])} years")
            print(f"   - FCFE: {len(original_result['FCFE'])} years")
            print(f"   - LFCF: {len(original_result['LFCF'])} years")
            if original_result['FCFF']:
                print(f"   - Latest FCFF: ${original_result['FCFF'][-1]:.0f}M")
        else:
            print("❌ Original calculator failed")
            
    except Exception as e:
        print(f"❌ Original calculator error: {e}")
    
    # Test 2: Centralized Calculator
    print("\\n2. Testing Centralized FinancialCalculator...")
    try:
        centralized_calc = create_centralized_calculator(company_folder)
        centralized_result = centralized_calc.calculate_all_fcf_types()
        
        if centralized_result and 'FCFF' in centralized_result:
            print("✅ Centralized calculator successful")
            print(f"   - FCFF: {len(centralized_result['FCFF'])} years")
            print(f"   - FCFE: {len(centralized_result['FCFE'])} years")
            print(f"   - LFCF: {len(centralized_result['LFCF'])} years")
            if centralized_result['FCFF']:
                print(f"   - Latest FCFF: ${centralized_result['FCFF'][-1]:.0f}M")
            print(f"   - Calculation method: {centralized_result.get('calculation_method', 'unknown')}")
        else:
            print("❌ Centralized calculator failed")
            
    except Exception as e:
        print(f"❌ Centralized calculator error: {e}")
    
    # Test 3: Performance Comparison
    print("\\n3. Testing Performance (Cached vs Uncached)...")
    try:
        import time
        
        # First call (uncached)
        start_time = time.time()
        centralized_calc = create_centralized_calculator(company_folder)
        result1 = centralized_calc.calculate_all_fcf_types()
        uncached_time = time.time() - start_time
        
        # Second call (cached)
        start_time = time.time()
        result2 = centralized_calc.calculate_all_fcf_types()
        cached_time = time.time() - start_time
        
        print(f"   - Uncached calculation: {uncached_time:.3f}s")
        print(f"   - Cached calculation: {cached_time:.3f}s")
        print(f"   - Performance improvement: {(uncached_time/cached_time):.1f}x faster")
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
    
    # Test 4: Cache Statistics
    print("\\n4. Testing Cache Statistics...")
    try:
        centralized_calc = create_centralized_calculator(company_folder)
        centralized_calc.calculate_all_fcf_types()  # Ensure cache is populated
        
        cache_stats = centralized_calc.get_cache_statistics()
        if cache_stats and 'centralized_system' in cache_stats:
            cs = cache_stats['centralized_system']
            print("✅ Cache statistics available")
            print(f"   - Total cache entries: {cs['cache_stats']['total_entries']}")
            print(f"   - Active entries: {cs['cache_stats']['active_entries']}")
            print(f"   - Supported metrics: {len(cs['processing_stats']['processing_stats']['supported_metrics'])}")
        else:
            print("❌ Cache statistics failed")
            
    except Exception as e:
        print(f"❌ Cache statistics error: {e}")
    
    # Test 5: Market Data Integration
    print("\\n5. Testing Market Data Integration...")
    try:
        centralized_calc = create_centralized_calculator(company_folder)
        market_data = centralized_calc.fetch_market_data('TSLA')
        
        if market_data:
            print("✅ Market data fetch successful")
            print(f"   - Current price: ${market_data.get('current_price', 0):.2f}")
            print(f"   - Shares outstanding: {market_data.get('shares_outstanding', 0)/1000000:.0f}M")
            print(f"   - Market cap: ${market_data.get('market_cap', 0):.0f}M")
        else:
            print("⚠️ Market data fetch failed (likely rate limited)")
            
    except Exception as e:
        print(f"❌ Market data integration error: {e}")
    
    print("\\n" + "=" * 70)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    compare_calculators()