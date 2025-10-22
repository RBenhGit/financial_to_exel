"""
Composite Variable Dependency Graph - Demo Script
==================================================

Demonstrates the usage of CompositeVariableDependencyGraph for managing
financial variable dependencies and calculation order.

This example shows:
1. Building a dependency graph for financial metrics
2. Calculating topological order
3. Performing impact analysis
4. Visualizing dependencies
5. Detecting and preventing cycles
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_processing.composite_variable_dependency_graph import (
    CompositeVariableDependencyGraph
)


def demo_basic_usage():
    """Demonstrate basic graph operations"""
    print("=" * 60)
    print("DEMO 1: Basic Dependency Graph Usage")
    print("=" * 60)

    # Create graph
    graph = CompositeVariableDependencyGraph()

    # Add base variables (no dependencies)
    print("\n1. Adding base variables...")
    graph.add_variable("revenue", category="income_statement")
    graph.add_variable("net_income", category="income_statement")
    print(f"   Base variables: {graph.get_base_variables()}")

    # Add composite variable
    print("\n2. Adding composite variable...")
    graph.add_variable(
        "profit_margin",
        category="calculated",
        depends_on=["net_income", "revenue"]
    )
    print(f"   Composite variables: {graph.get_composite_variables()}")

    # Get calculation order
    print("\n3. Calculation order:")
    order = graph.get_calculation_order()
    for i, var in enumerate(order, 1):
        depth = graph.get_variable_depth(var)
        var_type = "BASE" if graph._nodes[var].is_base else "COMPOSITE"
        print(f"   {i}. {var} (depth={depth}, type={var_type})")

    # Validate
    print("\n4. Validation:")
    is_valid, errors = graph.validate_dependencies()
    print(f"   Valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"   - {error}")

    print()


def demo_complex_financial_metrics():
    """Demonstrate complex financial metrics with multiple dependencies"""
    print("=" * 60)
    print("DEMO 2: Complex Financial Metrics")
    print("=" * 60)

    graph = CompositeVariableDependencyGraph()

    # Add base variables from financial statements
    print("\n1. Adding base financial variables...")
    base_vars = {
        "revenue": "income_statement",
        "cost_of_revenue": "income_statement",
        "operating_expenses": "income_statement",
        "net_income": "income_statement",
        "total_assets": "balance_sheet",
        "total_liabilities": "balance_sheet",
        "shareholders_equity": "balance_sheet",
        "total_debt": "balance_sheet",
        "operating_cash_flow": "cash_flow",
        "capital_expenditures": "cash_flow"
    }

    for var, category in base_vars.items():
        graph.add_variable(var, category=category)
    print(f"   Added {len(base_vars)} base variables")

    # Add calculated metrics
    print("\n2. Adding calculated metrics...")
    calculated = {
        "gross_profit": ["revenue", "cost_of_revenue"],
        "operating_income": ["gross_profit", "operating_expenses"],
        "profit_margin": ["net_income", "revenue"],
        "gross_margin": ["gross_profit", "revenue"],
        "roe": ["net_income", "shareholders_equity"],
        "roa": ["net_income", "total_assets"],
        "debt_to_equity": ["total_debt", "shareholders_equity"],
        "free_cash_flow": ["operating_cash_flow", "capital_expenditures"]
    }

    for var, deps in calculated.items():
        graph.add_variable(var, category="calculated", depends_on=deps)
    print(f"   Added {len(calculated)} calculated metrics")

    # Show calculation order
    print("\n3. Calculation order (grouped by depth):")
    order = graph.get_calculation_order()

    by_depth = {}
    for var in order:
        depth = graph.get_variable_depth(var)
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(var)

    for depth in sorted(by_depth.keys()):
        print(f"\n   Depth {depth}:")
        for var in by_depth[depth]:
            print(f"      - {var}")

    # Show statistics
    print("\n4. Graph statistics:")
    export = graph.export_to_dict()
    print(f"   Total variables: {export['total_variables']}")
    print(f"   Base variables: {export['base_variables']}")
    print(f"   Composite variables: {export['composite_variables']}")
    print(f"   Total edges (dependencies): {export['total_edges']}")

    print()
    return graph


def demo_impact_analysis(graph):
    """Demonstrate impact analysis for variable changes"""
    print("=" * 60)
    print("DEMO 3: Impact Analysis")
    print("=" * 60)

    # Analyze impact of changing revenue
    print("\n1. Impact of changing 'revenue':")
    impact = graph.get_impact_analysis("revenue")

    print(f"   Variable: {impact['variable']}")
    print(f"   Is base: {impact['is_base']}")
    print(f"   Category: {impact['category']}")
    print(f"   Direct dependents: {impact['direct_dependent_count']}")
    print(f"   Total affected: {impact['total_affected_count']}")
    print(f"   Max propagation depth: {impact['max_propagation_depth']}")

    print("\n   Affected variables:")
    for var in impact['all_affected_variables']:
        print(f"      - {var}")

    # Analyze impact of changing net_income
    print("\n2. Impact of changing 'net_income':")
    impact = graph.get_impact_analysis("net_income")
    print(f"   Total affected: {impact['total_affected_count']}")
    print(f"   Affected variables: {impact['all_affected_variables']}")

    print()


def demo_cycle_detection():
    """Demonstrate cycle detection and prevention"""
    print("=" * 60)
    print("DEMO 4: Cycle Detection and Prevention")
    print("=" * 60)

    graph = CompositeVariableDependencyGraph()

    # Create valid chain: A -> B -> C
    print("\n1. Creating valid dependency chain:")
    graph.add_variable("var_a")
    graph.add_variable("var_b", depends_on=["var_a"])
    graph.add_variable("var_c", depends_on=["var_b"])
    print("   Chain created: var_a -> var_b -> var_c")

    # Validate
    has_cycle, cycle = graph.has_cycle()
    print(f"   Has cycle: {has_cycle}")

    # Try to create cycle (should fail)
    print("\n2. Attempting to create cycle (var_c -> var_a):")
    result = graph.add_dependency("var_a", "var_c")
    print(f"   Cycle creation prevented: {not result}")

    # Verify still acyclic
    has_cycle, cycle = graph.has_cycle()
    print(f"   Graph is still acyclic: {not has_cycle}")

    print()


def demo_dynamic_updates():
    """Demonstrate dynamic dependency updates"""
    print("=" * 60)
    print("DEMO 5: Dynamic Dependency Updates")
    print("=" * 60)

    graph = CompositeVariableDependencyGraph()

    # Start simple
    print("\n1. Initial setup:")
    graph.add_variable("revenue")
    graph.add_variable("net_income")
    graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
    print(f"   Variables: {len(graph)}")
    print(f"   Calculation order: {graph.get_calculation_order()}")

    # Add new variable
    print("\n2. Adding new base variable:")
    graph.add_variable("total_assets")
    print(f"   Variables: {len(graph)}")

    # Add dependency to existing variable
    print("\n3. Adding new calculated metric:")
    graph.add_variable("roa", depends_on=["net_income", "total_assets"])
    print(f"   Variables: {len(graph)}")
    print(f"   Calculation order: {graph.get_calculation_order()}")

    # Remove dependency
    print("\n4. Removing dependency:")
    graph.remove_dependency("profit_margin", "revenue")
    deps = graph.get_dependencies("profit_margin")
    print(f"   profit_margin dependencies: {deps}")

    # Remove variable
    print("\n5. Removing variable:")
    graph.remove_variable("roa")
    print(f"   Variables: {len(graph)}")
    print(f"   Calculation order: {graph.get_calculation_order()}")

    print()


def demo_visualization(graph):
    """Demonstrate graph visualization"""
    print("=" * 60)
    print("DEMO 6: Graph Visualization")
    print("=" * 60)

    print("\n1. Generating visualization...")

    try:
        # Try to save as PNG
        graph.visualize("dependency_graph.png", format="png")
        print("   [OK] Saved as dependency_graph.png")
    except Exception as e:
        print(f"   [FAIL] PNG visualization failed: {e}")

    try:
        # Save as DOT format (always works)
        dot_output = graph.visualize()
        if dot_output:
            with open("dependency_graph.dot", "w") as f:
                f.write(dot_output)
            print("   [OK] Saved as dependency_graph.dot")
    except Exception as e:
        print(f"   [FAIL] DOT visualization failed: {e}")

    print("\n   View the graphs to see visual representation of dependencies")
    print()


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 60)
    print("Composite Variable Dependency Graph - Demonstrations")
    print("=" * 60 + "\n")

    # Run demos
    demo_basic_usage()
    graph = demo_complex_financial_metrics()
    demo_impact_analysis(graph)
    demo_cycle_detection()
    demo_dynamic_updates()
    demo_visualization(graph)

    print("=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
