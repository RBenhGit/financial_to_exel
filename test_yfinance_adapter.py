#!/usr/bin/env python3
"""
Simple test script for YFinanceAdapter functionality
"""

import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_yfinance_adapter():
    """Test basic YFinanceAdapter functionality"""
    print("=" * 60)
    print("Testing YFinance Adapter")
    print("=" * 60)
    
    try:
        # Import the adapter
        from core.data_processing.adapters import YFinanceAdapter, check_yfinance_availability
        print("[OK] YFinanceAdapter imported successfully")
        
        # Test symbol availability check
        test_symbol = "AAPL"
        print(f"\n1. Checking data availability for {test_symbol}...")
        
        availability = check_yfinance_availability(test_symbol)
        if 'error' in availability:
            print(f"   [ERROR] Error checking availability: {availability['error']}")
            return False
        
        print(f"   [OK] Market data available: {availability.get('market_data_available', False)}")
        print(f"   [OK] Statements available: {len([k for k, v in availability.get('statements_available', {}).items() if v])}")
        
        # Create adapter instance
        print(f"\n2. Creating YFinanceAdapter instance...")
        adapter = YFinanceAdapter(timeout=10, max_retries=2)
        print("   [OK] Adapter created successfully")
        
        # Test data loading
        print(f"\n3. Loading data for {test_symbol} (market data only for quick test)...")
        result = adapter.load_symbol_data(
            symbol=test_symbol,
            include_financials=False,  # Skip for quick test
            include_balance_sheet=False,
            include_cashflow=False,
            include_market_data=True,
            validate_data=True
        )
        
        print(f"   [OK] Variables extracted: {result.variables_extracted}")
        print(f"   [OK] Data points stored: {result.data_points_stored}")
        print(f"   [OK] Market data retrieved: {result.market_data_retrieved}")
        print(f"   [OK] Quality score: {result.quality_score:.2f}")
        print(f"   [OK] Extraction time: {result.extraction_time:.2f}s")
        
        if result.errors:
            print(f"   [WARN] Errors encountered: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"      - {error}")
        
        # Test VarInputData integration
        print(f"\n4. Testing VarInputData integration...")
        from core.data_processing.var_input_data import get_var_input_data
        
        var_data = get_var_input_data()
        available_vars = var_data.get_available_variables(test_symbol)
        
        print(f"   [OK] Variables available in VarInputData: {len(available_vars)}")
        if available_vars:
            print(f"   [OK] Sample variables: {available_vars[:5]}")
            
            # Try to retrieve a common variable
            for var_name in ['market_cap', 'pe_ratio', 'book_value_per_share']:
                if var_name in available_vars:
                    value = var_data.get_variable(test_symbol, var_name, period="current")
                    if value is not None:
                        print(f"   [OK] {test_symbol}.{var_name} = {value}")
                        break
        
        # Get adapter statistics
        print(f"\n5. Adapter statistics...")
        stats = adapter.get_adapter_statistics()
        adapter_stats = stats.get('adapter_stats', {})
        
        print(f"   [OK] Symbols processed: {adapter_stats.get('symbols_processed', 0)}")
        print(f"   [OK] API calls made: {adapter_stats.get('api_calls_made', 0)}")
        print(f"   [OK] Variables extracted: {adapter_stats.get('variables_extracted', 0)}")
        
        performance = stats.get('performance_metrics', {})
        if performance:
            print(f"   [OK] Success rate: {performance.get('success_rate', 0):.2%}")
        
        print(f"\n[SUCCESS] YFinance Adapter test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_data_load():
    """Test full data loading with all statements (slower test)"""
    print("\n" + "=" * 60)
    print("Testing Full Data Load (Optional)")
    print("=" * 60)
    
    try:
        from core.data_processing.adapters import YFinanceAdapter
        
        test_symbol = "MSFT"  # Use different symbol for variety
        print(f"Loading full financial data for {test_symbol}...")
        
        adapter = YFinanceAdapter(timeout=15)
        result = adapter.load_symbol_data(
            symbol=test_symbol,
            include_financials=True,
            include_balance_sheet=True,
            include_cashflow=True,
            include_market_data=True,
            historical_years=3,  # Limit for faster test
            validate_data=True
        )
        
        print(f"[OK] Full load results for {test_symbol}:")
        print(f"   Variables extracted: {result.variables_extracted}")
        print(f"   Data points stored: {result.data_points_stored}")
        print(f"   Periods covered: {len(result.periods_covered)}")
        print(f"   Quality score: {result.quality_score:.2f}")
        print(f"   Extraction time: {result.extraction_time:.2f}s")
        
        if result.periods_covered:
            print(f"   Sample periods: {result.periods_covered[:5]}")
        
        return True
        
    except Exception as e:
        print(f"[WARN] Full data load test failed: {e}")
        return False


if __name__ == "__main__":
    print("YFinance Adapter Test Suite")
    print("=" * 60)
    
    # Run basic test
    success = test_yfinance_adapter()
    
    if success:
        # Ask if user wants to run full test
        try:
            response = input("\nRun full data load test? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                test_full_data_load()
        except KeyboardInterrupt:
            pass
    
    print(f"\nTest completed at: {datetime.now()}")