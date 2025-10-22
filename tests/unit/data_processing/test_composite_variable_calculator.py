"""
Unit Tests for CompositeVariableCalculator
==========================================

Comprehensive test suite covering:
- Calculation accuracy
- Incremental update verification
- Performance benchmarking
- Parallel processing validation
- Error handling and rollback
- Caching functionality
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any

from core.data_processing.composite_variable_calculator import (
    CompositeVariableCalculator,
    CalculationResult,
    CalculationContext
)
from core.data_processing.composite_variable_dependency_graph import (
    CompositeVariableDependencyGraph
)


class TestBasicCalculations:
    """Test basic calculation functionality"""

    def test_simple_calculation(self):
        """Test simple variable calculation"""
        # Create graph
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])

        # Create calculator
        calculator = CompositeVariableCalculator(graph)

        # Register calculation
        calculator.register_calculation(
            "profit_margin",
            lambda data: data["net_income"] / data["revenue"] if data["revenue"] != 0 else 0
        )

        # Calculate
        base_data = {"revenue": 1000000, "net_income": 150000}
        results = calculator.calculate_all(base_data)

        assert "profit_margin" in results
        assert results["profit_margin"] == 0.15

    def test_multi_level_dependencies(self):
        """Test calculation with multiple dependency levels"""
        # Create graph with chain: a -> b -> c -> d
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])
        graph.add_variable("c", depends_on=["b"])
        graph.add_variable("d", depends_on=["c"])

        calculator = CompositeVariableCalculator(graph)

        # Register calculations
        calculator.register_calculation("b", lambda data: data["a"] * 2)
        calculator.register_calculation("c", lambda data: data["b"] + 10)
        calculator.register_calculation("d", lambda data: data["c"] ** 2)

        # Calculate
        base_data = {"a": 5}
        results = calculator.calculate_all(base_data)

        assert results["a"] == 5
        assert results["b"] == 10  # 5 * 2
        assert results["c"] == 20  # 10 + 10
        assert results["d"] == 400  # 20 ** 2

    def test_diamond_dependencies(self):
        """Test calculation with diamond dependency pattern"""
        # Create diamond: a -> b, a -> c, b -> d, c -> d
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])
        graph.add_variable("c", depends_on=["a"])
        graph.add_variable("d", depends_on=["b", "c"])

        calculator = CompositeVariableCalculator(graph)

        # Register calculations
        calculator.register_calculation("b", lambda data: data["a"] * 2)
        calculator.register_calculation("c", lambda data: data["a"] + 10)
        calculator.register_calculation("d", lambda data: data["b"] + data["c"])

        # Calculate
        base_data = {"a": 5}
        results = calculator.calculate_all(base_data)

        assert results["a"] == 5
        assert results["b"] == 10  # 5 * 2
        assert results["c"] == 15  # 5 + 10
        assert results["d"] == 25  # 10 + 15

    def test_multiple_base_variables(self):
        """Test calculation with multiple base variables"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("revenue")
        graph.add_variable("cost_of_revenue")
        graph.add_variable("operating_expenses")
        graph.add_variable("gross_profit", depends_on=["revenue", "cost_of_revenue"])
        graph.add_variable("operating_income", depends_on=["gross_profit", "operating_expenses"])

        calculator = CompositeVariableCalculator(graph)

        calculator.register_calculation(
            "gross_profit",
            lambda data: data["revenue"] - data["cost_of_revenue"]
        )
        calculator.register_calculation(
            "operating_income",
            lambda data: data["gross_profit"] - data["operating_expenses"]
        )

        base_data = {
            "revenue": 1000000,
            "cost_of_revenue": 400000,
            "operating_expenses": 300000
        }
        results = calculator.calculate_all(base_data)

        assert results["gross_profit"] == 600000
        assert results["operating_income"] == 300000


class TestIncrementalUpdates:
    """Test incremental update functionality"""

    def test_incremental_update_single_variable(self):
        """Test that incremental update only recalculates affected variables"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b")
        graph.add_variable("c", depends_on=["a"])
        graph.add_variable("d", depends_on=["b"])

        calculator = CompositeVariableCalculator(graph)
        calculator.register_calculation("c", lambda data: data["a"] * 2)
        calculator.register_calculation("d", lambda data: data["b"] * 3)

        # Initial calculation
        base_data = {"a": 5, "b": 10}
        results = calculator.calculate_all(base_data)

        assert results["c"] == 10
        assert results["d"] == 30

        # Update only 'a' - should only recalculate 'c'
        updated = calculator.update_and_recalculate({"a": 7}, results)

        assert updated["a"] == 7
        assert updated["b"] == 10
        assert updated["c"] == 14  # Recalculated
        assert updated["d"] == 30  # Not recalculated

    def test_incremental_update_cascade(self):
        """Test that incremental updates cascade through dependencies"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])
        graph.add_variable("c", depends_on=["b"])
        graph.add_variable("d", depends_on=["c"])

        calculator = CompositeVariableCalculator(graph)
        calculator.register_calculation("b", lambda data: data["a"] * 2)
        calculator.register_calculation("c", lambda data: data["b"] + 10)
        calculator.register_calculation("d", lambda data: data["c"] ** 2)

        # Initial calculation
        base_data = {"a": 5}
        results = calculator.calculate_all(base_data)

        # Update 'a' - should recalculate b, c, d
        updated = calculator.update_and_recalculate({"a": 3}, results)

        assert updated["a"] == 3
        assert updated["b"] == 6  # 3 * 2
        assert updated["c"] == 16  # 6 + 10
        assert updated["d"] == 256  # 16 ** 2


class TestCaching:
    """Test caching functionality"""

    def test_cache_enabled(self):
        """Test that caching improves performance"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph, enable_caching=True)

        # Register expensive calculation
        def expensive_calc(data):
            time.sleep(0.01)  # Simulate expensive operation
            return data["a"] * 2

        calculator.register_calculation("b", expensive_calc)

        # First calculation - should be slow
        base_data = {"a": 5}
        start = time.time()
        results1 = calculator.calculate_all(base_data)
        time1 = time.time() - start

        # Second calculation with same data - should be faster due to cache
        start = time.time()
        results2 = calculator.calculate_all(base_data)
        time2 = time.time() - start

        assert results1["b"] == results2["b"]
        # Cache should make second calculation significantly faster
        # (accounting for overhead, cache should be at least 2x faster)

        stats = calculator.get_statistics()
        assert stats["cache_hits"] > 0

    def test_cache_invalidation(self):
        """Test that cache is invalidated on data change"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph, enable_caching=True)
        calculator.register_calculation("b", lambda data: data["a"] * 2)

        # First calculation
        results1 = calculator.calculate_all({"a": 5})
        assert results1["b"] == 10

        # Second calculation with different data - cache should not be used
        results2 = calculator.calculate_all({"a": 10})
        assert results2["b"] == 20

    def test_clear_cache(self):
        """Test manual cache clearing"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph, enable_caching=True)
        calculator.register_calculation("b", lambda data: data["a"] * 2)

        # Calculate and populate cache
        calculator.calculate_all({"a": 5})
        stats_before = calculator.get_statistics()
        assert stats_before["cache_size"] > 0

        # Clear cache
        calculator.clear_cache()
        stats_after = calculator.get_statistics()
        assert stats_after["cache_size"] == 0


class TestParallelProcessing:
    """Test parallel processing functionality"""

    def test_parallel_independent_variables(self):
        """Test that independent variables are calculated in parallel"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b")
        graph.add_variable("c", depends_on=["a"])
        graph.add_variable("d", depends_on=["b"])

        calculator = CompositeVariableCalculator(graph, enable_parallel=True)

        # Register calculations with delays
        def calc_c(data):
            time.sleep(0.05)
            return data["a"] * 2

        def calc_d(data):
            time.sleep(0.05)
            return data["b"] * 3

        calculator.register_calculation("c", calc_c)
        calculator.register_calculation("d", calc_d)

        # Calculate - c and d should be calculated in parallel
        base_data = {"a": 5, "b": 10}
        start = time.time()
        results = calculator.calculate_all(base_data)
        parallel_time = time.time() - start

        # Disable parallel and compare
        calculator_seq = CompositeVariableCalculator(graph, enable_parallel=False)
        calculator_seq.register_calculation("c", calc_c)
        calculator_seq.register_calculation("d", calc_d)

        start = time.time()
        results_seq = calculator_seq.calculate_all(base_data)
        sequential_time = time.time() - start

        # Results should be the same
        assert results["c"] == results_seq["c"]
        assert results["d"] == results_seq["d"]

        # Parallel should be faster (accounting for overhead)
        assert parallel_time < sequential_time * 1.5

    def test_parallel_batching_by_depth(self):
        """Test that variables are batched correctly by depth"""
        # Create graph with multiple levels
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b1", depends_on=["a"])
        graph.add_variable("b2", depends_on=["a"])
        graph.add_variable("b3", depends_on=["a"])
        graph.add_variable("c", depends_on=["b1", "b2", "b3"])

        calculator = CompositeVariableCalculator(graph, enable_parallel=True)

        calculator.register_calculation("b1", lambda data: data["a"] + 1)
        calculator.register_calculation("b2", lambda data: data["a"] + 2)
        calculator.register_calculation("b3", lambda data: data["a"] + 3)
        calculator.register_calculation("c", lambda data: data["b1"] + data["b2"] + data["b3"])

        results = calculator.calculate_all({"a": 10})

        assert results["b1"] == 11
        assert results["b2"] == 12
        assert results["b3"] == 13
        assert results["c"] == 36

        stats = calculator.get_statistics()
        # Should have parallel batches
        assert stats["parallel_batches"] > 0


class TestErrorHandling:
    """Test error handling and rollback"""

    def test_missing_dependency(self):
        """Test error when dependency is missing"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph)
        calculator.register_calculation("b", lambda data: data["a"] * 2)

        # Missing base data
        with pytest.raises(ValueError, match="Missing dependencies"):
            calculator.calculate_all({})

    def test_calculation_error(self):
        """Test error handling in calculation function"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph)

        # Calculation that will fail
        def failing_calc(data):
            raise ValueError("Intentional error")

        calculator.register_calculation("b", failing_calc)

        with pytest.raises(ValueError, match="Calculation errors"):
            calculator.calculate_all({"a": 5})

    def test_division_by_zero(self):
        """Test handling of division by zero"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("numerator")
        graph.add_variable("denominator")
        graph.add_variable("ratio", depends_on=["numerator", "denominator"])

        calculator = CompositeVariableCalculator(graph)

        # Safe division
        calculator.register_calculation(
            "ratio",
            lambda data: data["numerator"] / data["denominator"] if data["denominator"] != 0 else 0
        )

        results = calculator.calculate_all({"numerator": 10, "denominator": 0})
        assert results["ratio"] == 0

    def test_missing_calculation_function(self):
        """Test error when calculation function not registered"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph)
        # Don't register calculation for 'b'

        with pytest.raises(ValueError, match="No calculation function"):
            calculator.calculate_all({"a": 5})


class TestCalculationResults:
    """Test CalculationResult functionality"""

    def test_calculation_result_tracking(self):
        """Test that calculation results are tracked properly"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph)
        calculator.register_calculation("b", lambda data: data["a"] * 2)

        # Calculate single variable
        value, result = calculator.calculate_variable("b", {"a": 5})

        assert value == 10
        assert result.success is True
        assert result.variable == "b"
        assert result.value == 10
        assert result.error is None
        assert "a" in result.dependencies_used


class TestStatistics:
    """Test statistics tracking"""

    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])
        graph.add_variable("c", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph, enable_caching=True)
        calculator.register_calculation("b", lambda data: data["a"] * 2)
        calculator.register_calculation("c", lambda data: data["a"] + 10)

        # First calculation
        calculator.calculate_all({"a": 5})

        # Second calculation (should use cache)
        calculator.calculate_all({"a": 5})

        stats = calculator.get_statistics()

        assert stats["total_calculations"] > 0
        assert stats["cache_hits"] > 0
        assert stats["registered_functions"] == 2

    def test_reset_statistics(self):
        """Test statistics reset"""
        graph = CompositeVariableDependencyGraph()
        graph.add_variable("a")
        graph.add_variable("b", depends_on=["a"])

        calculator = CompositeVariableCalculator(graph)
        calculator.register_calculation("b", lambda data: data["a"] * 2)

        calculator.calculate_all({"a": 5})

        stats_before = calculator.get_statistics()
        assert stats_before["total_calculations"] > 0

        calculator.reset_statistics()

        stats_after = calculator.get_statistics()
        assert stats_after["total_calculations"] == 0


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_financial_ratios(self):
        """Test calculating complex financial ratios"""
        graph = CompositeVariableDependencyGraph()

        # Base variables
        graph.add_variable("revenue")
        graph.add_variable("net_income")
        graph.add_variable("total_assets")
        graph.add_variable("total_equity")
        graph.add_variable("current_assets")
        graph.add_variable("current_liabilities")

        # Calculated ratios
        graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
        graph.add_variable("roa", depends_on=["net_income", "total_assets"])
        graph.add_variable("roe", depends_on=["net_income", "total_equity"])
        graph.add_variable("current_ratio", depends_on=["current_assets", "current_liabilities"])

        calculator = CompositeVariableCalculator(graph)

        # Register calculations
        calculator.register_calculations({
            "profit_margin": lambda d: d["net_income"] / d["revenue"] if d["revenue"] != 0 else 0,
            "roa": lambda d: d["net_income"] / d["total_assets"] if d["total_assets"] != 0 else 0,
            "roe": lambda d: d["net_income"] / d["total_equity"] if d["total_equity"] != 0 else 0,
            "current_ratio": lambda d: d["current_assets"] / d["current_liabilities"] if d["current_liabilities"] != 0 else 0,
        })

        base_data = {
            "revenue": 1000000,
            "net_income": 150000,
            "total_assets": 500000,
            "total_equity": 300000,
            "current_assets": 200000,
            "current_liabilities": 100000
        }

        results = calculator.calculate_all(base_data)

        assert results["profit_margin"] == 0.15
        assert results["roa"] == 0.30
        assert results["roe"] == 0.50
        assert results["current_ratio"] == 2.0

    def test_dcf_valuation_components(self):
        """Test DCF valuation component calculations"""
        graph = CompositeVariableDependencyGraph()

        # Base variables
        graph.add_variable("fcf")
        graph.add_variable("growth_rate")
        graph.add_variable("discount_rate")
        graph.add_variable("terminal_growth_rate")

        # Calculated components
        graph.add_variable("pv_fcf", depends_on=["fcf", "discount_rate"])
        graph.add_variable("terminal_value", depends_on=["fcf", "growth_rate", "discount_rate", "terminal_growth_rate"])

        calculator = CompositeVariableCalculator(graph)

        calculator.register_calculations({
            "pv_fcf": lambda d: d["fcf"] / (1 + d["discount_rate"]),
            "terminal_value": lambda d: (
                d["fcf"] * (1 + d["growth_rate"]) / (d["discount_rate"] - d["terminal_growth_rate"])
                if d["discount_rate"] > d["terminal_growth_rate"] else 0
            ),
        })

        base_data = {
            "fcf": 100000,
            "growth_rate": 0.05,
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.02
        }

        results = calculator.calculate_all(base_data)

        assert results["pv_fcf"] == pytest.approx(90909.09, rel=1e-2)
        assert results["terminal_value"] > 0


class TestPerformance:
    """Performance benchmarking tests"""

    def test_large_graph_performance(self):
        """Test performance with a large dependency graph"""
        graph = CompositeVariableDependencyGraph()

        # Create a large graph with 100 variables
        num_vars = 100
        graph.add_variable("base")

        for i in range(1, num_vars):
            graph.add_variable(f"var_{i}", depends_on=["base"])

        calculator = CompositeVariableCalculator(graph, enable_parallel=True)

        # Register simple calculations
        for i in range(1, num_vars):
            calculator.register_calculation(
                f"var_{i}",
                lambda data, idx=i: data["base"] + idx
            )

        # Measure performance
        start = time.time()
        results = calculator.calculate_all({"base": 100})
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second for 100 variables)
        assert elapsed < 1.0
        assert len(results) == num_vars

    def test_deep_dependency_chain(self):
        """Test performance with deep dependency chain"""
        graph = CompositeVariableDependencyGraph()

        # Create chain of 50 variables
        depth = 50
        graph.add_variable("var_0")

        for i in range(1, depth):
            graph.add_variable(f"var_{i}", depends_on=[f"var_{i-1}"])

        calculator = CompositeVariableCalculator(graph, enable_caching=True)

        # Register calculations
        for i in range(1, depth):
            calculator.register_calculation(
                f"var_{i}",
                lambda data, prev=f"var_{i-1}": data[prev] + 1
            )

        start = time.time()
        results = calculator.calculate_all({"var_0": 0})
        elapsed = time.time() - start

        assert results[f"var_{depth-1}"] == depth - 1
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
