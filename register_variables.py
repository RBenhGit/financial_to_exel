#!/usr/bin/env python3
"""
Register standard variables to test yfinance adapter
"""

import sys
sys.path.insert(0, '.')

def register_and_test():
    from core.data_processing.standard_financial_variables import register_all_variables
    from core.data_processing.financial_variable_registry import get_registry
    
    print("Registering standard variables...")
    registry = get_registry()
    result = register_all_variables(registry)
    print(f"Registration result: {result}")
    
    # Check what variables are now available
    all_vars = registry.list_all_variables()
    print(f"Total variables in registry: {len(all_vars)}")
    
    # Check specific variables we need
    test_vars = ['market_cap', 'pe_ratio', 'total_revenue', 'net_income']
    for var in test_vars:
        var_def = registry.get_variable_definition(var)
        if var_def:
            print(f"[OK] {var}: {var_def.category.value}")
        else:
            print(f"[MISSING] {var}")
    
    print("\nTesting yfinance adapter with registered variables...")
    from core.data_processing.adapters import YFinanceAdapter
    
    adapter = YFinanceAdapter(timeout=10)
    result = adapter.load_symbol_data(
        symbol="AAPL",
        include_financials=False,
        include_balance_sheet=False, 
        include_cashflow=False,
        include_market_data=True,
        validate_data=True
    )
    
    print(f"Variables extracted: {result.variables_extracted}")
    print(f"Data points stored: {result.data_points_stored}")
    print(f"Market data retrieved: {result.market_data_retrieved}")
    
    if result.variables_extracted > 0:
        print("[SUCCESS] Variables are now being extracted and stored!")
    else:
        print("[ISSUE] Still no variables extracted")

if __name__ == "__main__":
    register_and_test()