#!/usr/bin/env python3
"""
Debug script to check yfinance adapter and variable registry integration
"""

import sys
import logging

# Add project root to path
sys.path.insert(0, '.')

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

def debug_registry():
    """Debug the financial variable registry"""
    print("=" * 60)
    print("Debugging Financial Variable Registry")
    print("=" * 60)
    
    try:
        from core.data_processing.financial_variable_registry import get_registry, VariableCategory
        
        registry = get_registry()
        all_variables = registry.list_all_variables()
        
        print(f"Total variables in registry: {len(all_variables)}")
        
        # Check for market data variables
        market_vars = []
        for var_name in all_variables:
            var_def = registry.get_variable_definition(var_name)
            if var_def and var_def.category == VariableCategory.MARKET_DATA:
                market_vars.append(var_name)
        
        print(f"Market data variables: {len(market_vars)}")
        print("Market variables:", market_vars[:10])
        
        # Check for specific variables we expect
        expected_vars = ['market_cap', 'pe_ratio', 'pb_ratio', 'dividend_yield']
        for var in expected_vars:
            var_def = registry.get_variable_definition(var)
            if var_def:
                print(f"✓ {var}: category={var_def.category.value}, aliases={getattr(var_def, 'aliases', 'None')}")
            else:
                print(f"✗ {var}: NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"Registry debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def debug_yfinance_conversion():
    """Debug yfinance data conversion"""
    print("\n" + "=" * 60)
    print("Debugging YFinance Data Conversion")
    print("=" * 60)
    
    try:
        import yfinance as yf
        from core.data_processing.converters.yfinance_converter import YfinanceConverter
        
        # Test with Apple
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        print(f"Raw yfinance info keys: {len(info.keys())}")
        print("Sample info keys:", list(info.keys())[:20])
        
        # Convert using converter
        converter = YfinanceConverter()
        converted = converter.convert_info_data(info)
        
        print(f"\nConverted fields: {len(converted)}")
        print("Converted fields:", list(converted.keys()))
        
        # Check specific mappings
        for yf_field, std_field in converter.FIELD_MAPPINGS.items():
            if yf_field in info:
                value = info[yf_field]
                print(f"Mapping: {yf_field} ({value}) -> {std_field}")
        
        return True
        
    except Exception as e:
        print(f"Conversion debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def debug_adapter_flow():
    """Debug the full adapter flow step by step"""
    print("\n" + "=" * 60)
    print("Debugging YFinance Adapter Flow")
    print("=" * 60)
    
    try:
        from core.data_processing.adapters import YFinanceAdapter
        from core.data_processing.financial_variable_registry import get_registry
        
        registry = get_registry()
        adapter = YFinanceAdapter(timeout=10)
        
        # Check what happens in market data extraction
        import yfinance as yf
        ticker = yf.Ticker("AAPL")
        
        # Manually test the _extract_market_data method
        print("Testing market data extraction...")
        result = adapter._extract_market_data(ticker, "AAPL", validate=True)
        
        print(f"Market data extraction result: {result}")
        
        # Check if converter works
        info = ticker.info
        converted = adapter.converter.convert_info_data(info)
        print(f"Converted data keys: {list(converted.keys())}")
        
        # Check which variables are found in registry
        found_vars = []
        for var_name in converted.keys():
            if var_name not in ['source', 'converted_at']:
                var_def = registry.get_variable_definition(var_name)
                if var_def:
                    found_vars.append(var_name)
                else:
                    print(f"Variable {var_name} not found in registry")
        
        print(f"Variables found in registry: {found_vars}")
        
        return True
        
    except Exception as e:
        print(f"Adapter flow debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("YFinance Adapter Debug Suite")
    
    debug_registry()
    debug_yfinance_conversion() 
    debug_adapter_flow()