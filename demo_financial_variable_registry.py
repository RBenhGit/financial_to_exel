#!/usr/bin/env python3
"""
Financial Variable Registry Demonstration
=========================================

This script demonstrates the core functionality of the FinancialVariableRegistry
system implemented in Task #57.

Key features demonstrated:
- Variable registration and retrieval
- Category-based organization
- Source alias resolution
- Data validation
- JSON serialization
"""

import json
from datetime import datetime

from core.data_processing.financial_variable_registry import (
    FinancialVariableRegistry,
    VariableDefinition,
    VariableCategory,
    DataType,
    Units,
    ValidationRule,
    get_registry
)


def main():
    """Demonstrate FinancialVariableRegistry functionality"""
    
    print("Financial Variable Registry Demo")
    print("=" * 50)
    
    # Get the singleton registry instance
    registry = get_registry()
    
    # Clear any existing data for clean demo
    registry.clear_registry()
    
    print("\n1. VARIABLE REGISTRATION")
    print("-" * 30)
    
    # Define some core financial variables
    variables_to_register = [
        VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            units=Units.MILLIONS_USD,
            description="Total company revenue",
            aliases={
                "yfinance": "totalRevenue",
                "excel": "Revenue",
                "fmp": "revenue"
            },
            validation_rules=[
                ValidationRule("non_negative", error_message="Revenue cannot be negative")
            ],
            tags={"core", "income", "fundamental"}
        ),
        
        VariableDefinition(
            name="net_income",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.FLOAT,
            units=Units.MILLIONS_USD,
            description="Net income after taxes",
            aliases={
                "yfinance": "netIncome",
                "excel": "Net Income",
                "fmp": "netIncome"
            },
            validation_rules=[
                ValidationRule("range", parameters={"min": -10000, "max": 100000})
            ],
            tags={"core", "income", "profitability"}
        ),
        
        VariableDefinition(
            name="total_assets",
            category=VariableCategory.BALANCE_SHEET,
            data_type=DataType.FLOAT,
            units=Units.MILLIONS_USD,
            description="Total assets on balance sheet",
            aliases={
                "yfinance": "totalAssets",
                "excel": "Total Assets",
                "fmp": "totalAssets"
            },
            validation_rules=[
                ValidationRule("positive", error_message="Assets must be positive")
            ],
            tags={"core", "balance_sheet"}
        ),
        
        VariableDefinition(
            name="stock_price",
            category=VariableCategory.MARKET_DATA,
            data_type=DataType.FLOAT,
            units=Units.DOLLARS,
            description="Current stock price",
            aliases={
                "yfinance": "regularMarketPrice",
                "excel": "Stock Price"
            },
            validation_rules=[
                ValidationRule("positive", error_message="Price must be positive")
            ],
            tags={"market", "real_time"}
        ),
        
        VariableDefinition(
            name="pe_ratio",
            category=VariableCategory.RATIOS,
            data_type=DataType.FLOAT,
            units=Units.RATIO,
            description="Price-to-earnings ratio",
            aliases={
                "yfinance": "forwardPE",
                "excel": "P/E Ratio"
            },
            validation_rules=[
                ValidationRule("range", parameters={"min": 0, "max": 1000}, warning_only=True)
            ],
            tags={"valuation", "ratio"}
        )
    ]
    
    # Register variables
    for var_def in variables_to_register:
        success = registry.register_variable(var_def)
        print(f"Registered {var_def.name}: {'OK' if success else 'FAILED'}")
    
    print(f"\nTotal variables registered: {len(registry.list_all_variables())}")
    
    print("\n2. CATEGORY FILTERING")
    print("-" * 30)
    
    # Demonstrate category filtering
    for category in [VariableCategory.INCOME_STATEMENT, VariableCategory.BALANCE_SHEET, 
                     VariableCategory.MARKET_DATA, VariableCategory.RATIOS]:
        vars_in_category = registry.get_variables_by_category(category)
        print(f"{category.value.replace('_', ' ').title()}: {len(vars_in_category)} variables")
        for var_def in vars_in_category:
            print(f"  - {var_def.name}: {var_def.description}")
    
    print("\n3. ALIAS RESOLUTION")
    print("-" * 30)
    
    # Demonstrate alias resolution
    test_aliases = [
        ("yfinance", "totalRevenue"),
        ("excel", "Net Income"),
        ("fmp", "netIncome"),
        ("yfinance", "regularMarketPrice"),
        ("unknown_source", "someField")
    ]
    
    for source, alias in test_aliases:
        resolved = registry.resolve_alias(source, alias)
        if resolved:
            print(f"{source}.{alias} -> {resolved}")
        else:
            print(f"{source}.{alias} -> Not found")
    
    print("\n4. DATA VALIDATION")
    print("-" * 30)
    
    # Demonstrate validation
    test_validations = [
        ("revenue", 150000),      # Valid positive revenue
        ("revenue", -50000),      # Invalid negative revenue
        ("stock_price", 185.50),  # Valid stock price
        ("stock_price", -10),     # Invalid negative price
        ("pe_ratio", 25.5),       # Valid P/E ratio
        ("pe_ratio", 2000),       # Warning: high P/E ratio
    ]
    
    for variable_name, value in test_validations:
        is_valid, errors = registry.validate_value(variable_name, value)
        status = "VALID" if is_valid else "INVALID"
        print(f"{variable_name} = {value}: {status}")
        if errors:
            for error in errors:
                print(f"  Error: {error}")
    
    print("\n5. TAG FILTERING")
    print("-" * 30)
    
    # Demonstrate tag filtering
    test_tags = ["core", "income", "valuation", "real_time"]
    
    for tag in test_tags:
        vars_with_tag = registry.get_variables_by_tag(tag)
        print(f"Tag '{tag}': {len(vars_with_tag)} variables")
        for var_def in vars_with_tag:
            print(f"  - {var_def.name}")
    
    print("\n6. REGISTRY STATISTICS")
    print("-" * 30)
    
    stats = registry.get_statistics()
    print(f"Total variables: {stats['total_variables']}")
    print(f"Categories: {len(stats['categories'])}")
    print(f"Sources with aliases: {stats['sources_with_aliases']}")
    print(f"Total aliases: {stats['total_aliases']}")
    print(f"Available tags: {stats['tags']}")
    
    print("\nCategory breakdown:")
    for category, count in stats['categories'].items():
        if count > 0:
            print(f"  {category.replace('_', ' ').title()}: {count}")
    
    print("\n7. JSON SERIALIZATION")
    print("-" * 30)
    
    # Demonstrate JSON export/import
    print("Exporting to JSON...")
    json_data = registry.export_to_json()
    
    # Show a snippet of the JSON
    parsed = json.loads(json_data)
    print(f"JSON contains {len(parsed['variables'])} variables")
    print("Sample JSON structure:")
    if parsed['variables']:
        sample_var = list(parsed['variables'].keys())[0]
        sample_data = parsed['variables'][sample_var]
        print(f"  {sample_var}:")
        print(f"    category: {sample_data['category']}")
        print(f"    data_type: {sample_data['data_type']}")
        print(f"    units: {sample_data['units']}")
        print(f"    aliases: {sample_data.get('aliases', {})}")
    
    print("\n8. SOURCE ALIAS MAPPING")
    print("-" * 30)
    
    # Show all aliases for each source
    sources = ["yfinance", "excel", "fmp"]
    for source in sources:
        aliases = registry.get_aliases_for_source(source)
        print(f"{source.upper()} mappings:")
        for alias, standard_name in aliases.items():
            print(f"  {alias} -> {standard_name}")
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("* Variable registration and retrieval")
    print("* Category-based organization") 
    print("* Source alias resolution")
    print("* Data validation")
    print("* Thread-safe operations")
    print("* JSON serialization support")


if __name__ == "__main__":
    main()