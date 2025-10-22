"""
CompositeVariableCalculator Demo
=================================

Practical examples demonstrating the CompositeVariableCalculator capabilities
for financial analysis use cases.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_processing.composite_variable_dependency_graph import CompositeVariableDependencyGraph
from core.data_processing.composite_variable_calculator import CompositeVariableCalculator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def demo_basic_financial_ratios():
    """
    Demo 1: Calculate basic financial ratios
    """
    print("\n" + "="*80)
    print("DEMO 1: Basic Financial Ratios")
    print("="*80)

    # Create dependency graph
    graph = CompositeVariableDependencyGraph()

    # Add base variables (from financial statements)
    graph.add_variable("revenue", category="income_statement")
    graph.add_variable("net_income", category="income_statement")
    graph.add_variable("total_assets", category="balance_sheet")
    graph.add_variable("total_equity", category="balance_sheet")
    graph.add_variable("current_assets", category="balance_sheet")
    graph.add_variable("current_liabilities", category="balance_sheet")

    # Add calculated ratios
    graph.add_variable("profit_margin", category="calculated", depends_on=["net_income", "revenue"])
    graph.add_variable("roa", category="calculated", depends_on=["net_income", "total_assets"])
    graph.add_variable("roe", category="calculated", depends_on=["net_income", "total_equity"])
    graph.add_variable("current_ratio", category="calculated", depends_on=["current_assets", "current_liabilities"])

    print(f"\nDependency graph created with {len(graph)} variables")
    print(f"Base variables: {graph.get_base_variables()}")
    print(f"Composite variables: {graph.get_composite_variables()}")

    # Create calculator
    calculator = CompositeVariableCalculator(graph, enable_caching=True, enable_parallel=True)

    # Register calculation functions
    calculations = {
        "profit_margin": lambda d: d["net_income"] / d["revenue"] if d["revenue"] != 0 else 0,
        "roa": lambda d: d["net_income"] / d["total_assets"] if d["total_assets"] != 0 else 0,
        "roe": lambda d: d["net_income"] / d["total_equity"] if d["total_equity"] != 0 else 0,
        "current_ratio": lambda d: d["current_assets"] / d["current_liabilities"] if d["current_liabilities"] != 0 else 0,
    }
    calculator.register_calculations(calculations)

    # Sample company data (in millions)
    company_data = {
        "revenue": 100000,
        "net_income": 15000,
        "total_assets": 50000,
        "total_equity": 30000,
        "current_assets": 20000,
        "current_liabilities": 10000
    }

    print("\nInput Data (in millions):")
    for key, value in company_data.items():
        print(f"  {key}: ${value:,.0f}")

    # Calculate all ratios
    results = calculator.calculate_all(company_data)

    print("\nCalculated Ratios:")
    print(f"  Profit Margin: {results['profit_margin']:.2%}")
    print(f"  ROA: {results['roa']:.2%}")
    print(f"  ROE: {results['roe']:.2%}")
    print(f"  Current Ratio: {results['current_ratio']:.2f}")

    # Show statistics
    stats = calculator.get_statistics()
    print(f"\nCalculation Statistics:")
    print(f"  Total calculations: {stats['total_calculations']}")
    print(f"  Cache hit rate: {stats['cache_hit_rate']:.1%}")


def demo_incremental_updates():
    """
    Demo 2: Incremental updates for scenario analysis
    """
    print("\n" + "="*80)
    print("DEMO 2: Incremental Updates for Scenario Analysis")
    print("="*80)

    # Create dependency graph
    graph = CompositeVariableDependencyGraph()

    # Income statement items
    graph.add_variable("revenue")
    graph.add_variable("cogs")
    graph.add_variable("operating_expenses")

    # Calculated profitability metrics
    graph.add_variable("gross_profit", depends_on=["revenue", "cogs"])
    graph.add_variable("operating_income", depends_on=["gross_profit", "operating_expenses"])
    graph.add_variable("gross_margin", depends_on=["gross_profit", "revenue"])
    graph.add_variable("operating_margin", depends_on=["operating_income", "revenue"])

    # Create calculator
    calculator = CompositeVariableCalculator(graph, enable_caching=True)

    # Register calculations
    calculations = {
        "gross_profit": lambda d: d["revenue"] - d["cogs"],
        "operating_income": lambda d: d["gross_profit"] - d["operating_expenses"],
        "gross_margin": lambda d: d["gross_profit"] / d["revenue"] if d["revenue"] != 0 else 0,
        "operating_margin": lambda d: d["operating_income"] / d["revenue"] if d["revenue"] != 0 else 0,
    }
    calculator.register_calculations(calculations)

    # Base case
    base_case = {
        "revenue": 100000,
        "cogs": 60000,
        "operating_expenses": 25000
    }

    print("\nBase Case:")
    results = calculator.calculate_all(base_case)
    print(f"  Revenue: ${results['revenue']:,.0f}")
    print(f"  Gross Profit: ${results['gross_profit']:,.0f}")
    print(f"  Operating Income: ${results['operating_income']:,.0f}")
    print(f"  Gross Margin: {results['gross_margin']:.2%}")
    print(f"  Operating Margin: {results['operating_margin']:.2%}")

    # Scenario 1: Revenue increase
    print("\nScenario 1: Revenue increases by 10%")
    scenario1 = calculator.update_and_recalculate(
        {"revenue": 110000},
        results
    )
    print(f"  Revenue: ${scenario1['revenue']:,.0f} (+{(scenario1['revenue']/results['revenue']-1):.1%})")
    print(f"  Gross Profit: ${scenario1['gross_profit']:,.0f} (+{(scenario1['gross_profit']/results['gross_profit']-1):.1%})")
    print(f"  Operating Income: ${scenario1['operating_income']:,.0f} (+{(scenario1['operating_income']/results['operating_income']-1):.1%})")
    print(f"  Operating Margin: {scenario1['operating_margin']:.2%}")

    # Scenario 2: Cost reduction
    print("\nScenario 2: Operating expenses reduced by 20%")
    scenario2 = calculator.update_and_recalculate(
        {"operating_expenses": 20000},
        results
    )
    print(f"  Operating Expenses: ${scenario2['operating_expenses']:,.0f} ({(scenario2['operating_expenses']/results['operating_expenses']-1):.1%})")
    print(f"  Operating Income: ${scenario2['operating_income']:,.0f} (+{(scenario2['operating_income']/results['operating_income']-1):.1%})")
    print(f"  Operating Margin: {scenario2['operating_margin']:.2%}")


def demo_dcf_valuation():
    """
    Demo 3: DCF valuation components with multi-level dependencies
    """
    print("\n" + "="*80)
    print("DEMO 3: DCF Valuation Components")
    print("="*80)

    # Create dependency graph
    graph = CompositeVariableDependencyGraph()

    # Base inputs
    graph.add_variable("ebit")
    graph.add_variable("tax_rate")
    graph.add_variable("depreciation")
    graph.add_variable("capex")
    graph.add_variable("change_in_nwc")
    graph.add_variable("wacc")
    graph.add_variable("growth_rate")
    graph.add_variable("terminal_growth_rate")

    # Level 1 calculations
    graph.add_variable("nopat", depends_on=["ebit", "tax_rate"])
    graph.add_variable("ebitda", depends_on=["ebit", "depreciation"])

    # Level 2 calculations
    graph.add_variable("fcf", depends_on=["nopat", "depreciation", "capex", "change_in_nwc"])

    # Level 3 calculations
    graph.add_variable("pv_fcf", depends_on=["fcf", "wacc"])
    graph.add_variable("terminal_value", depends_on=["fcf", "growth_rate", "wacc", "terminal_growth_rate"])

    print(f"\nDependency graph created with {len(graph)} variables")
    print(f"Calculation order: {graph.get_calculation_order()}")

    # Create calculator
    calculator = CompositeVariableCalculator(graph, enable_caching=True, enable_parallel=True)

    # Register calculation functions
    calculations = {
        "nopat": lambda d: d["ebit"] * (1 - d["tax_rate"]),
        "ebitda": lambda d: d["ebit"] + d["depreciation"],
        "fcf": lambda d: d["nopat"] + d["depreciation"] - d["capex"] - d["change_in_nwc"],
        "pv_fcf": lambda d: d["fcf"] / (1 + d["wacc"]),
        "terminal_value": lambda d: (
            d["fcf"] * (1 + d["growth_rate"]) / (d["wacc"] - d["terminal_growth_rate"])
            if d["wacc"] > d["terminal_growth_rate"] else 0
        ),
    }
    calculator.register_calculations(calculations)

    # Sample data
    dcf_inputs = {
        "ebit": 50000,
        "tax_rate": 0.21,
        "depreciation": 10000,
        "capex": 12000,
        "change_in_nwc": 2000,
        "wacc": 0.10,
        "growth_rate": 0.05,
        "terminal_growth_rate": 0.02
    }

    print("\nInput Data:")
    for key, value in dcf_inputs.items():
        if "rate" in key:
            print(f"  {key}: {value:.1%}")
        else:
            print(f"  {key}: ${value:,.0f}")

    # Calculate
    results = calculator.calculate_all(dcf_inputs)

    print("\nCalculated Values:")
    print(f"  NOPAT: ${results['nopat']:,.0f}")
    print(f"  EBITDA: ${results['ebitda']:,.0f}")
    print(f"  Free Cash Flow: ${results['fcf']:,.0f}")
    print(f"  PV of FCF (Year 1): ${results['pv_fcf']:,.0f}")
    print(f"  Terminal Value: ${results['terminal_value']:,.0f}")

    # Show calculation statistics
    stats = calculator.get_statistics()
    print(f"\nPerformance:")
    print(f"  Calculations performed: {stats['total_calculations']}")
    print(f"  Parallel batches: {stats['parallel_batches']}")


def demo_performance_comparison():
    """
    Demo 4: Performance comparison - sequential vs parallel
    """
    print("\n" + "="*80)
    print("DEMO 4: Performance Comparison")
    print("="*80)

    import time

    # Create a graph with many independent variables
    graph = CompositeVariableDependencyGraph()
    graph.add_variable("base")

    num_vars = 50
    for i in range(num_vars):
        graph.add_variable(f"calc_{i}", depends_on=["base"])

    # Sequential calculator
    calc_seq = CompositeVariableCalculator(graph, enable_parallel=False, enable_caching=False)
    for i in range(num_vars):
        calc_seq.register_calculation(f"calc_{i}", lambda d, idx=i: d["base"] * (idx + 1))

    # Parallel calculator
    calc_par = CompositeVariableCalculator(graph, enable_parallel=True, enable_caching=False)
    for i in range(num_vars):
        calc_par.register_calculation(f"calc_{i}", lambda d, idx=i: d["base"] * (idx + 1))

    base_data = {"base": 100}

    # Sequential
    start = time.time()
    results_seq = calc_seq.calculate_all(base_data)
    time_seq = time.time() - start

    # Parallel
    start = time.time()
    results_par = calc_par.calculate_all(base_data)
    time_par = time.time() - start

    print(f"\nCalculating {num_vars} independent variables:")
    print(f"  Sequential time: {time_seq*1000:.2f}ms")
    print(f"  Parallel time: {time_par*1000:.2f}ms")
    print(f"  Speedup: {time_seq/time_par:.2f}x")

    # Verify results match
    assert results_seq == results_par
    print(f"\n  Results verified: Both methods produce identical results")


if __name__ == "__main__":
    demo_basic_financial_ratios()
    demo_incremental_updates()
    demo_dcf_valuation()
    demo_performance_comparison()

    print("\n" + "="*80)
    print("All demos completed successfully!")
    print("="*80 + "\n")
