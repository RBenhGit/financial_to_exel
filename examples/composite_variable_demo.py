"""
Composite Variable Registry Demo
================================

Demonstrates the use of the composite variable registry and calculator
for calculating financial ratios and metrics.
"""

from core.data_processing.composite_variable_registry import create_standard_calculator

def main():
    """Run demo of composite variable calculations."""

    # Create calculator with all standard formulas
    calculator = create_standard_calculator()

    print("=" * 80)
    print("Composite Variable Registry - Demo")
    print("=" * 80)
    print()

    # Get statistics
    stats = calculator.get_statistics()
    print(f"Registered Formulas: {stats['registered_functions']}")
    print(f"Variables in Graph: {len(calculator._graph)}")
    print()

    # Example financial data (Apple-like company, simplified)
    print("Sample Financial Data:")
    print("-" * 80)
    base_data = {
        # Income Statement (in millions)
        "revenue": 394328,
        "cost_of_revenue": 214137,
        "operating_income": 119437,
        "net_income": 99803,
        "ebit": 119437,
        "depreciation_amortization": 11284,

        # Balance Sheet (in millions)
        "total_assets": 352755,
        "current_assets": 143566,
        "cash_and_equivalents": 48304,
        "accounts_receivable": 28184,
        "inventory": 4061,
        "total_liabilities": 290020,
        "current_liabilities": 125481,
        "short_term_debt": 9613,
        "long_term_debt": 106063,

        # Cash Flow (in millions)
        "operating_cash_flow": 122151,
        "capital_expenditures": 10708,

        # Market Data
        "stock_price": 170,
        "shares_outstanding": 15634,
        "weighted_avg_shares": 15634,
    }

    for key, value in list(base_data.items())[:10]:
        print(f"  {key}: ${value:,}" if "ratio" not in key.lower() else f"  {key}: {value}")
    print(f"  ... and {len(base_data) - 10} more variables")
    print()

    # Calculate specific variables
    print("Calculating Specific Variables:")
    print("-" * 80)

    specific_vars = [
        "gross_profit", "gross_margin",
        "roe", "roa",
        "current_ratio",
        "free_cash_flow",
        "market_cap"
    ]

    results = {}
    for var_name in specific_vars:
        try:
            value, result = calculator.calculate_variable(var_name, base_data)
            results[var_name] = value
            print(f"  {var_name}: {value:,.4f}")
        except Exception as e:
            print(f"  {var_name}: ERROR - {str(e)[:60]}")

    print()
    print("Key Insights:")
    print("-" * 80)
    print(f"  Gross Margin: {results.get('gross_margin', 0):.1%}")
    print(f"  ROE (Return on Equity): {results.get('roe', 0):.1%}")
    print(f"  ROA (Return on Assets): {results.get('roa', 0):.1%}")
    print(f"  Current Ratio: {results.get('current_ratio', 0):.2f}x")
    print(f"  Free Cash Flow: ${results.get('free_cash_flow', 0):,.0f}M")
    print(f"  Market Cap: ${results.get('market_cap', 0):,.0f}M")
    print()

    # Calculate ALL available variables
    print("Attempting to Calculate All Variables:")
    print("-" * 80)
    try:
        all_results = calculator.calculate_all(base_data)
        calculated_count = len([k for k in all_results.keys() if k not in base_data])
        print(f"  Successfully calculated {calculated_count} composite variables")
        print()

        # Show some key ratios
        print("Sample Calculated Ratios:")
        print(f"  Operating Margin: {all_results.get('operating_margin', 0):.1%}")
        print(f"  Net Margin: {all_results.get('net_margin', 0):.1%}")
        print(f"  Debt-to-Equity: {all_results.get('debt_to_equity', 0):.2f}")
        print(f"  Quick Ratio: {all_results.get('quick_ratio', 0):.2f}")
        print(f"  EBITDA: ${all_results.get('ebitda', 0):,.0f}M")

    except Exception as e:
        print(f"  Error calculating all variables: {e}")
        print("  This is expected if some required data is missing")

    print()
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
