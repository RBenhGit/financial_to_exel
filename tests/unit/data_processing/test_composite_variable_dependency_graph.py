"""
Tests for Composite Variable Dependency Graph
==============================================

Comprehensive test suite for CompositeVariableDependencyGraph class covering:
- Basic graph operations (add, remove variables)
- Dependency management (add, remove dependencies)
- Topological sorting and calculation order
- Cycle detection
- Validation
- Impact analysis
- Graph statistics and metadata
"""

import pytest
from core.data_processing.composite_variable_dependency_graph import (
    CompositeVariableDependencyGraph,
    VariableNode,
    create_dependency_graph_from_registry
)
from core.data_processing.financial_variable_registry import (
    FinancialVariableRegistry,
    VariableDefinition,
    VariableCategory,
    DataType,
    Units
)


class TestVariableNode:
    """Test VariableNode dataclass"""

    def test_variable_node_creation(self):
        """Test basic node creation"""
        node = VariableNode(
            name="revenue",
            category="income_statement",
            is_base=True
        )
        assert node.name == "revenue"
        assert node.category == "income_statement"
        assert node.is_base is True
        assert len(node.dependencies) == 0
        assert len(node.dependents) == 0

    def test_variable_node_with_dependencies(self):
        """Test node with dependencies"""
        node = VariableNode(
            name="profit_margin",
            category="calculated",
            is_base=False,
            dependencies=["net_income", "revenue"]
        )
        assert node.is_base is False
        assert len(node.dependencies) == 2
        assert "net_income" in node.dependencies
        assert "revenue" in node.dependencies

    def test_variable_node_hash_equality(self):
        """Test node hashing and equality"""
        node1 = VariableNode(name="revenue")
        node2 = VariableNode(name="revenue")
        node3 = VariableNode(name="net_income")

        assert node1 == node2
        assert node1 != node3
        assert hash(node1) == hash(node2)
        assert hash(node1) != hash(node3)


class TestCompositeVariableDependencyGraph:
    """Test main dependency graph functionality"""

    def test_graph_initialization(self):
        """Test graph initialization"""
        graph = CompositeVariableDependencyGraph()
        assert len(graph) == 0
        assert len(graph.get_base_variables()) == 0
        assert len(graph.get_composite_variables()) == 0

    def test_add_base_variable(self):
        """Test adding a base variable (no dependencies)"""
        graph = CompositeVariableDependencyGraph()
        result = graph.add_variable("revenue", category="income_statement")

        assert result is True
        assert len(graph) == 1
        assert "revenue" in graph
        assert len(graph.get_base_variables()) == 1

    def test_add_composite_variable(self):
        """Test adding a composite variable with dependencies"""
        graph = CompositeVariableDependencyGraph()

        # Add base variables
        graph.add_variable("net_income")
        graph.add_variable("revenue")

        # Add composite variable
        result = graph.add_variable(
            "profit_margin",
            category="calculated",
            depends_on=["net_income", "revenue"]
        )

        assert result is True
        assert len(graph) == 3
        assert len(graph.get_composite_variables()) == 1
        assert "profit_margin" in graph

    def test_add_duplicate_variable(self):
        """Test adding duplicate variable fails gracefully"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")

        result = graph.add_variable("revenue")
        assert result is False
        assert len(graph) == 1

    def test_auto_add_missing_dependencies(self):
        """Test automatic addition of missing dependencies"""
        graph = CompositeVariableDependencyGraph()

        # Add composite variable without adding dependencies first
        graph.add_variable(
            "profit_margin",
            depends_on=["net_income", "revenue"]
        )

        # Dependencies should be auto-added
        assert len(graph) == 3
        assert "net_income" in graph
        assert "revenue" in graph
        assert "profit_margin" in graph

    def test_remove_variable(self):
        """Test removing a variable"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")

        result = graph.remove_variable("revenue")
        assert result is True
        assert len(graph) == 1
        assert "revenue" not in graph

    def test_remove_nonexistent_variable(self):
        """Test removing nonexistent variable"""
        graph = CompositeVariableDependencyGraph()
        result = graph.remove_variable("nonexistent")
        assert result is False

    def test_add_dependency(self):
        """Test adding a dependency relationship"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("net_income")
        graph.add_variable("revenue")
        graph.add_variable("profit_margin")

        result = graph.add_dependency("profit_margin", "net_income")
        assert result is True

        deps = graph.get_dependencies("profit_margin")
        assert "net_income" in deps

    def test_add_dependency_creates_base_variable(self):
        """Test adding dependency auto-creates missing variable"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("profit_margin")

        result = graph.add_dependency("profit_margin", "net_income")
        assert result is True
        assert "net_income" in graph
        assert graph._nodes["net_income"].is_base is True

    def test_remove_dependency(self):
        """Test removing a dependency"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        result = graph.remove_dependency("profit_margin", "net_income")
        assert result is True

        deps = graph.get_dependencies("profit_margin")
        assert "net_income" not in deps
        assert "revenue" in deps

    def test_get_calculation_order_simple(self):
        """Test topological sort for simple dependency chain"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        order = graph.get_calculation_order()

        # profit_margin should come after its dependencies
        assert order.index("profit_margin") > order.index("revenue")
        assert order.index("profit_margin") > order.index("net_income")

    def test_get_calculation_order_complex(self):
        """Test topological sort for complex dependency graph"""
        graph = CompositeVariableDependencyGraph()

        # Build complex graph:
        # revenue, total_debt, shareholders_equity (base)
        # net_income (no deps)
        # profit_margin <- net_income, revenue
        # debt_to_equity <- total_debt, shareholders_equity
        # roe <- net_income, shareholders_equity

        graph.add_variable("revenue")
        graph.add_variable("total_debt")
        graph.add_variable("shareholders_equity")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
        graph.add_variable("debt_to_equity", depends_on=["total_debt", "shareholders_equity"])
        graph.add_variable("roe", depends_on=["net_income", "shareholders_equity"])

        order = graph.get_calculation_order()

        # Verify dependencies come before dependents
        assert order.index("profit_margin") > order.index("net_income")
        assert order.index("profit_margin") > order.index("revenue")
        assert order.index("debt_to_equity") > order.index("total_debt")
        assert order.index("debt_to_equity") > order.index("shareholders_equity")
        assert order.index("roe") > order.index("net_income")
        assert order.index("roe") > order.index("shareholders_equity")

    def test_calculation_order_caching(self):
        """Test that calculation order is cached"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        order1 = graph.get_calculation_order()
        order2 = graph.get_calculation_order()

        # Should return same object (cached)
        assert order1 == order2

    def test_calculation_order_invalidation(self):
        """Test that calculation order is invalidated on graph changes"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")

        order1 = graph.get_calculation_order()

        # Add new variable
        graph.add_variable("net_income")

        order2 = graph.get_calculation_order()

        # Should recalculate
        assert len(order2) == 2
        assert len(order1) == 1


class TestCycleDetection:
    """Test cycle detection functionality"""

    def test_no_cycle_simple(self):
        """Test cycle detection on acyclic graph"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        has_cycle, cycle = graph.has_cycle()
        assert has_cycle is False
        assert cycle is None

    def test_detect_simple_cycle(self):
        """Test detection of simple 2-node cycle"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("var_a")
        graph.add_variable("var_b")

        # Create cycle: A -> B -> A
        graph.add_dependency("var_b", "var_a")
        graph._graph.add_edge("var_b", "var_a")  # Force cycle

        has_cycle, cycle = graph.has_cycle()
        assert has_cycle is True
        assert cycle is not None
        assert len(cycle) >= 2

    def test_prevent_cycle_creation(self):
        """Test that add_dependency prevents cycle creation"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("var_a")
        graph.add_variable("var_b")
        graph.add_variable("var_c")

        # Create chain: A -> B -> C
        graph.add_dependency("var_b", "var_a")
        graph.add_dependency("var_c", "var_b")

        # Try to create cycle: C -> A (would create A -> B -> C -> A)
        result = graph.add_dependency("var_a", "var_c")

        assert result is False  # Should be prevented
        has_cycle, _ = graph.has_cycle()
        assert has_cycle is False

    def test_calculation_order_fails_on_cycle(self):
        """Test that calculation order raises error on cyclic graph"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("var_a")
        graph.add_variable("var_b")

        # Force create cycle
        graph._graph.add_edge("var_a", "var_b")
        graph._graph.add_edge("var_b", "var_a")

        with pytest.raises(ValueError, match="cycle"):
            graph.get_calculation_order()


class TestDependencyValidation:
    """Test dependency validation"""

    def test_validate_valid_graph(self):
        """Test validation of valid graph"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        is_valid, errors = graph.validate_dependencies()
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_detects_cycle(self):
        """Test validation detects cycles"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("var_a")
        graph.add_variable("var_b")

        # Force cycle
        graph._graph.add_edge("var_a", "var_b")
        graph._graph.add_edge("var_b", "var_a")

        is_valid, errors = graph.validate_dependencies()
        assert is_valid is False
        assert len(errors) > 0
        assert any("cycle" in err.lower() for err in errors)

    def test_validate_empty_graph(self):
        """Test validation of empty graph"""
        graph = CompositeVariableDependencyGraph()
        is_valid, errors = graph.validate_dependencies()
        assert is_valid is True
        assert len(errors) == 0


class TestDependencyQueries:
    """Test querying dependencies and dependents"""

    def test_get_dependencies_direct(self):
        """Test getting direct dependencies"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        deps = graph.get_dependencies("profit_margin", recursive=False)
        assert len(deps) == 2
        assert "net_income" in deps
        assert "revenue" in deps

    def test_get_dependencies_recursive(self):
        """Test getting transitive dependencies"""
        graph = CompositeVariableDependencyGraph()

        # Create chain: A -> B -> C
        graph.add_variable("var_a")
        graph.add_variable("var_b", depends_on=["var_a"])
        graph.add_variable("var_c", depends_on=["var_b"])

        deps = graph.get_dependencies("var_c", recursive=True)
        assert len(deps) == 2
        assert "var_b" in deps
        assert "var_a" in deps

    def test_get_dependents_direct(self):
        """Test getting direct dependents"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])
        graph.add_variable("ps_ratio", depends_on=["revenue"])

        dependents = graph.get_dependents("revenue", recursive=False)
        assert len(dependents) == 2
        assert "profit_margin" in dependents
        assert "ps_ratio" in dependents

    def test_get_dependents_recursive(self):
        """Test getting transitive dependents"""
        graph = CompositeVariableDependencyGraph()

        # Create chain: A -> B -> C
        graph.add_variable("var_a")
        graph.add_variable("var_b", depends_on=["var_a"])
        graph.add_variable("var_c", depends_on=["var_b"])

        dependents = graph.get_dependents("var_a", recursive=True)
        assert len(dependents) == 2
        assert "var_b" in dependents
        assert "var_c" in dependents

    def test_get_dependencies_nonexistent(self):
        """Test getting dependencies of nonexistent variable"""
        graph = CompositeVariableDependencyGraph()
        deps = graph.get_dependencies("nonexistent")
        assert len(deps) == 0


class TestImpactAnalysis:
    """Test impact analysis functionality"""

    def test_impact_analysis_base_variable(self):
        """Test impact analysis for base variable"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])
        graph.add_variable("ps_ratio", depends_on=["revenue"])

        impact = graph.get_impact_analysis("revenue")

        assert impact["exists"] is True
        assert impact["is_base"] is True
        assert impact["direct_dependent_count"] == 2
        assert impact["total_affected_count"] == 2
        assert "profit_margin" in impact["all_affected_variables"]
        assert "ps_ratio" in impact["all_affected_variables"]

    def test_impact_analysis_composite_variable(self):
        """Test impact analysis for composite variable"""
        graph = CompositeVariableDependencyGraph()

        # A -> B -> C
        graph.add_variable("var_a")
        graph.add_variable("var_b", depends_on=["var_a"])
        graph.add_variable("var_c", depends_on=["var_b"])

        impact = graph.get_impact_analysis("var_b")

        assert impact["exists"] is True
        assert impact["is_base"] is False
        assert impact["direct_dependent_count"] == 1
        assert "var_c" in impact["direct_dependents"]

    def test_impact_analysis_propagation_depth(self):
        """Test propagation depth calculation"""
        graph = CompositeVariableDependencyGraph()

        # Create chain with depth 3
        graph.add_variable("var_a")
        graph.add_variable("var_b", depends_on=["var_a"])
        graph.add_variable("var_c", depends_on=["var_b"])
        graph.add_variable("var_d", depends_on=["var_c"])

        impact = graph.get_impact_analysis("var_a")
        assert impact["max_propagation_depth"] == 3

    def test_impact_analysis_nonexistent(self):
        """Test impact analysis for nonexistent variable"""
        graph = CompositeVariableDependencyGraph()
        impact = graph.get_impact_analysis("nonexistent")

        assert impact["exists"] is False
        assert "error" in impact


class TestGraphStatistics:
    """Test graph statistics and metadata"""

    def test_get_base_variables(self):
        """Test getting base variables"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        base_vars = graph.get_base_variables()
        assert len(base_vars) == 2
        assert "revenue" in base_vars
        assert "net_income" in base_vars

    def test_get_composite_variables(self):
        """Test getting composite variables"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
        graph.add_variable("roe", depends_on=["net_income"])

        composite_vars = graph.get_composite_variables()
        assert len(composite_vars) == 2
        assert "profit_margin" in composite_vars
        assert "roe" in composite_vars

    def test_get_variable_depth_base(self):
        """Test depth calculation for base variable"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")

        depth = graph.get_variable_depth("revenue")
        assert depth == 0

    def test_get_variable_depth_composite(self):
        """Test depth calculation for composite variable"""
        graph = CompositeVariableDependencyGraph()

        # Chain: A -> B -> C
        graph.add_variable("var_a")
        graph.add_variable("var_b", depends_on=["var_a"])
        graph.add_variable("var_c", depends_on=["var_b"])

        assert graph.get_variable_depth("var_a") == 0
        assert graph.get_variable_depth("var_b") == 1
        assert graph.get_variable_depth("var_c") == 2

    def test_get_variable_depth_nonexistent(self):
        """Test depth for nonexistent variable"""
        graph = CompositeVariableDependencyGraph()
        depth = graph.get_variable_depth("nonexistent")
        assert depth == -1

    def test_export_to_dict(self):
        """Test exporting graph to dictionary"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue", category="income_statement")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        export = graph.export_to_dict()

        assert "variables" in export
        assert "total_variables" in export
        assert export["total_variables"] == 2
        assert export["base_variables"] == 1
        assert export["composite_variables"] == 1
        assert "revenue" in export["variables"]
        assert "profit_margin" in export["variables"]


class TestVisualization:
    """Test visualization functionality"""

    def test_visualize_returns_dot_string(self):
        """Test visualization returns DOT string when no output file"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        # Without matplotlib, should return DOT string
        try:
            import matplotlib
            pytest.skip("matplotlib installed, test not applicable")
        except ImportError:
            dot_string = graph.visualize()
            assert dot_string is not None
            assert "digraph" in dot_string
            assert "revenue" in dot_string

    def test_visualize_saves_to_file(self, tmp_path):
        """Test visualization saves to file"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        # Use .dot extension to get DOT format, or .png for image
        output_file = tmp_path / "graph.png"
        result = graph.visualize(output_file=str(output_file), format="png")

        assert result is None
        assert output_file.exists()
        # For PNG, just check file is not empty
        assert output_file.stat().st_size > 0


class TestSpecialMethods:
    """Test special methods (__len__, __contains__, __repr__)"""

    def test_len(self):
        """Test __len__ method"""
        graph = CompositeVariableDependencyGraph()
        assert len(graph) == 0

        graph.add_variable("revenue")
        assert len(graph) == 1

        graph.add_variable("net_income")
        assert len(graph) == 2

    def test_contains(self):
        """Test __contains__ method"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")

        assert "revenue" in graph
        assert "nonexistent" not in graph

    def test_repr(self):
        """Test __repr__ method"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])

        repr_str = repr(graph)
        assert "CompositeVariableDependencyGraph" in repr_str
        assert "variables=2" in repr_str


class TestRegistryIntegration:
    """Test integration with FinancialVariableRegistry"""

    def test_create_from_registry_basic(self):
        """Test creating graph from registry"""
        # Create registry with test variables
        registry = FinancialVariableRegistry()
        registry.clear_registry()

        revenue_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.CURRENCY,
            units=Units.MILLIONS_USD
        )
        profit_def = VariableDefinition(
            name="profit_margin",
            category=VariableCategory.CALCULATED,
            data_type=DataType.PERCENTAGE,
            units=Units.PERCENTAGE,
            depends_on=["net_income", "revenue"]
        )

        registry.register_variable(revenue_def)
        registry.register_variable(profit_def)

        # Create graph from registry
        graph = create_dependency_graph_from_registry(registry)

        assert len(graph) >= 2
        assert "revenue" in graph
        assert "profit_margin" in graph

    def test_create_from_registry_with_filter(self):
        """Test creating graph with category filter"""
        registry = FinancialVariableRegistry()
        registry.clear_registry()

        revenue_def = VariableDefinition(
            name="revenue",
            category=VariableCategory.INCOME_STATEMENT,
            data_type=DataType.CURRENCY,
            units=Units.MILLIONS_USD
        )
        ratio_def = VariableDefinition(
            name="current_ratio",
            category=VariableCategory.RATIOS,
            data_type=DataType.FLOAT,
            units=Units.RATIO
        )

        registry.register_variable(revenue_def)
        registry.register_variable(ratio_def)

        # Filter for income statement only
        graph = create_dependency_graph_from_registry(
            registry,
            filter_category="income_statement"
        )

        assert "revenue" in graph
        assert "current_ratio" not in graph


class TestRealWorldScenarios:
    """Test real-world financial variable scenarios"""

    def test_profit_margin_calculation_order(self):
        """Test calculation order for profit margin"""
        graph = CompositeVariableDependencyGraph()

        # profit_margin depends on net_income and revenue
        graph.add_variable("net_income", category="income_statement")
        graph.add_variable("revenue", category="income_statement")
        graph.add_variable(
            "profit_margin",
            category="calculated",
            depends_on=["net_income", "revenue"]
        )

        order = graph.get_calculation_order()

        # Both dependencies must come before profit_margin
        assert order.index("profit_margin") > order.index("net_income")
        assert order.index("profit_margin") > order.index("revenue")

    def test_debt_to_equity_calculation_order(self):
        """Test calculation order for debt-to-equity ratio"""
        graph = CompositeVariableDependencyGraph()

        # debt_to_equity depends on total_debt and shareholders_equity
        graph.add_variable("total_debt", category="balance_sheet")
        graph.add_variable("shareholders_equity", category="balance_sheet")
        graph.add_variable(
            "debt_to_equity",
            category="calculated",
            depends_on=["total_debt", "shareholders_equity"]
        )

        order = graph.get_calculation_order()

        assert order.index("debt_to_equity") > order.index("total_debt")
        assert order.index("debt_to_equity") > order.index("shareholders_equity")

    def test_complex_financial_metrics(self):
        """Test complex dependency graph with multiple metrics"""
        graph = CompositeVariableDependencyGraph()

        # Base variables
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("total_assets")
        graph.add_variable("shareholders_equity")
        graph.add_variable("total_debt")

        # Calculated metrics
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
        graph.add_variable("roe", depends_on=["net_income", "shareholders_equity"])
        graph.add_variable("roa", depends_on=["net_income", "total_assets"])
        graph.add_variable("debt_to_equity", depends_on=["total_debt", "shareholders_equity"])

        # Validate graph
        is_valid, errors = graph.validate_dependencies()
        assert is_valid is True

        # Get calculation order
        order = graph.get_calculation_order()
        assert len(order) == 9

        # All base variables should come before calculated ones
        for base_var in ["revenue", "net_income", "total_assets", "shareholders_equity", "total_debt"]:
            for calc_var in ["profit_margin", "roe", "roa", "debt_to_equity"]:
                deps = graph.get_dependencies(calc_var, recursive=True)
                if base_var in deps:
                    assert order.index(base_var) < order.index(calc_var)

    def test_impact_of_changing_base_variable(self):
        """Test impact analysis when changing a widely-used base variable"""
        graph = CompositeVariableDependencyGraph()

        # revenue is used by multiple calculations
        graph.add_variable("revenue")
        graph.add_variable("profit_margin", depends_on=["revenue"])
        graph.add_variable("ps_ratio", depends_on=["revenue"])
        graph.add_variable("revenue_growth", depends_on=["revenue"])

        impact = graph.get_impact_analysis("revenue")

        assert impact["is_base"] is True
        assert impact["direct_dependent_count"] == 3
        assert impact["total_affected_count"] == 3
        assert set(impact["all_affected_variables"]) == {"profit_margin", "ps_ratio", "revenue_growth"}


class TestPerformance:
    """Test performance with large graphs"""

    def test_large_graph_performance(self):
        """Test performance with larger dependency graph"""
        graph = CompositeVariableDependencyGraph()

        # Create 100 base variables
        for i in range(100):
            graph.add_variable(f"base_var_{i}")

        # Create 50 composite variables each depending on 2-3 base variables
        for i in range(50):
            deps = [f"base_var_{i % 100}", f"base_var_{(i+1) % 100}"]
            graph.add_variable(f"composite_var_{i}", depends_on=deps)

        # Should complete quickly
        assert len(graph) == 150
        order = graph.get_calculation_order()
        assert len(order) == 150

        is_valid, errors = graph.validate_dependencies()
        assert is_valid is True
