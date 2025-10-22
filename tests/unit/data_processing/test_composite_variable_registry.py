"""
Tests for Composite Variable Registry
======================================

Comprehensive test suite for the CompositeVariableRegistry module, including:
- Formula registration and retrieval
- Calculation accuracy for all composite variables
- Error handling (division by zero, missing data)
- Integration with dependency graph and calculator
- End-to-end calculation workflows
"""

import pytest
from core.data_processing.composite_variable_registry import (
    CompositeVariableRegistry,
    CalculationFormula,
    create_standard_formula_registry,
    create_standard_dependency_graph,
    create_standard_calculator,
    safe_divide,
    safe_get,
    # Individual calculation functions
    calculate_gross_profit,
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roe,
    calculate_roa,
    calculate_roic,
    calculate_pe_ratio,
    calculate_pb_ratio,
    calculate_current_ratio,
    calculate_quick_ratio,
    calculate_debt_to_equity,
    calculate_free_cash_flow,
    calculate_market_cap,
    calculate_enterprise_value,
)


class TestUtilityFunctions:
    """Test utility functions for safe calculations."""

    def test_safe_divide_normal(self):
        """Test safe division with normal values."""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(100, 4) == 25.0

    def test_safe_divide_zero_denominator(self):
        """Test safe division with zero denominator."""
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=99.0) == 99.0

    def test_safe_divide_none_denominator(self):
        """Test safe division with None denominator."""
        assert safe_divide(10, None) == 0.0

    def test_safe_get_existing_key(self):
        """Test safe_get with existing key."""
        data = {"revenue": 1000000}
        assert safe_get(data, "revenue") == 1000000

    def test_safe_get_missing_key(self):
        """Test safe_get with missing key."""
        data = {"revenue": 1000000}
        assert safe_get(data, "expenses", 500000) == 500000

    def test_safe_get_none_value(self):
        """Test safe_get with None value."""
        data = {"revenue": None}
        assert safe_get(data, "revenue", 0.0) == 0.0


class TestCompositeVariableRegistry:
    """Test the CompositeVariableRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CompositeVariableRegistry()
        assert len(registry) == 0

    def test_register_formula(self):
        """Test registering a formula."""
        registry = CompositeVariableRegistry()
        formula = CalculationFormula(
            variable_name="test_var",
            formula_func=lambda data: data.get("a", 0) + data.get("b", 0),
            description="Test formula"
        )
        assert registry.register_formula(formula) is True
        assert len(registry) == 1

    def test_register_duplicate_formula(self):
        """Test registering duplicate formula."""
        registry = CompositeVariableRegistry()
        formula = CalculationFormula(
            variable_name="test_var",
            formula_func=lambda data: data.get("a", 0),
            description="Test formula"
        )
        assert registry.register_formula(formula) is True
        assert registry.register_formula(formula) is False
        assert len(registry) == 1

    def test_get_formula(self):
        """Test retrieving a formula."""
        registry = CompositeVariableRegistry()
        formula = CalculationFormula(
            variable_name="test_var",
            formula_func=lambda data: data.get("a", 0),
            description="Test formula"
        )
        registry.register_formula(formula)
        retrieved = registry.get_formula("test_var")
        assert retrieved is not None
        assert retrieved.variable_name == "test_var"

    def test_get_nonexistent_formula(self):
        """Test retrieving nonexistent formula."""
        registry = CompositeVariableRegistry()
        assert registry.get_formula("nonexistent") is None


class TestProfitabilityCalculations:
    """Test profitability ratio calculations."""

    def test_gross_profit(self):
        """Test gross profit calculation."""
        data = {"revenue": 1000000, "cost_of_revenue": 600000}
        assert calculate_gross_profit(data) == 400000

    def test_gross_margin(self):
        """Test gross margin calculation."""
        data = {"gross_profit": 400000, "revenue": 1000000}
        assert calculate_gross_margin(data) == 0.4

    def test_gross_margin_zero_revenue(self):
        """Test gross margin with zero revenue."""
        data = {"gross_profit": 400000, "revenue": 0}
        assert calculate_gross_margin(data) == 0.0

    def test_operating_margin(self):
        """Test operating margin calculation."""
        data = {"operating_income": 250000, "revenue": 1000000}
        assert calculate_operating_margin(data) == 0.25

    def test_net_margin(self):
        """Test net margin calculation."""
        data = {"net_income": 150000, "revenue": 1000000}
        assert calculate_net_margin(data) == 0.15

    def test_roe(self):
        """Test ROE calculation."""
        data = {"net_income": 150000, "shareholders_equity": 1000000}
        assert calculate_roe(data) == 0.15

    def test_roa(self):
        """Test ROA calculation."""
        data = {"net_income": 150000, "total_assets": 3000000}
        assert calculate_roa(data) == 0.05

    def test_roic(self):
        """Test ROIC calculation."""
        data = {
            "ebit": 250000,
            "tax_expense": 50000,
            "total_assets": 3000000,
            "current_liabilities": 500000
        }
        result = calculate_roic(data)
        # ROIC = EBIT(1-Tax Rate) / Invested Capital
        # Tax Rate = 50000 / 250000 = 0.2
        # NOPAT = 250000 * 0.8 = 200000
        # Invested Capital = 3000000 - 500000 = 2500000
        # ROIC = 200000 / 2500000 = 0.08
        assert abs(result - 0.08) < 0.001


class TestValuationCalculations:
    """Test valuation ratio calculations."""

    def test_pe_ratio(self):
        """Test P/E ratio calculation."""
        data = {"stock_price": 100, "earnings_per_share": 5}
        assert calculate_pe_ratio(data) == 20.0

    def test_pe_ratio_zero_eps(self):
        """Test P/E ratio with zero EPS."""
        data = {"stock_price": 100, "earnings_per_share": 0}
        assert calculate_pe_ratio(data) == 0.0

    def test_pb_ratio(self):
        """Test P/B ratio calculation."""
        data = {"market_cap": 10000000, "book_value": 5000000}
        assert calculate_pb_ratio(data) == 2.0

    def test_market_cap(self):
        """Test market cap calculation."""
        data = {"stock_price": 100, "shares_outstanding": 1000000}
        assert calculate_market_cap(data) == 100000000

    def test_enterprise_value(self):
        """Test enterprise value calculation."""
        data = {
            "market_cap": 10000000,
            "total_debt": 2000000,
            "cash_and_equivalents": 500000
        }
        # EV = Market Cap + Debt - Cash
        # EV = 10000000 + 2000000 - 500000 = 11500000
        assert calculate_enterprise_value(data) == 11500000


class TestLiquidityCalculations:
    """Test liquidity ratio calculations."""

    def test_current_ratio(self):
        """Test current ratio calculation."""
        data = {"current_assets": 2000000, "current_liabilities": 1000000}
        assert calculate_current_ratio(data) == 2.0

    def test_current_ratio_zero_liabilities(self):
        """Test current ratio with zero liabilities."""
        data = {"current_assets": 2000000, "current_liabilities": 0}
        assert calculate_current_ratio(data) == 0.0

    def test_quick_ratio(self):
        """Test quick ratio calculation."""
        data = {
            "current_assets": 2000000,
            "inventory": 500000,
            "current_liabilities": 1000000
        }
        # Quick Ratio = (2000000 - 500000) / 1000000 = 1.5
        assert calculate_quick_ratio(data) == 1.5


class TestLeverageCalculations:
    """Test leverage ratio calculations."""

    def test_debt_to_equity(self):
        """Test debt-to-equity ratio."""
        data = {"total_debt": 3000000, "shareholders_equity": 2000000}
        assert calculate_debt_to_equity(data) == 1.5

    def test_debt_to_equity_zero_equity(self):
        """Test debt-to-equity with zero equity."""
        data = {"total_debt": 3000000, "shareholders_equity": 0}
        assert calculate_debt_to_equity(data) == 0.0


class TestCashFlowCalculations:
    """Test cash flow calculations."""

    def test_free_cash_flow(self):
        """Test free cash flow calculation."""
        data = {"operating_cash_flow": 500000, "capital_expenditures": 150000}
        assert calculate_free_cash_flow(data) == 350000

    def test_free_cash_flow_with_capex_alias(self):
        """Test FCF using capex alias."""
        data = {"operating_cash_flow": 500000, "capex": 150000}
        assert calculate_free_cash_flow(data) == 350000


class TestStandardRegistry:
    """Test the standard formula registry creation."""

    def test_create_standard_registry(self):
        """Test creating standard formula registry."""
        registry = create_standard_formula_registry()
        assert len(registry) > 30  # Should have 35+ formulas

    def test_standard_registry_has_key_formulas(self):
        """Test that standard registry has key formulas."""
        registry = create_standard_formula_registry()

        key_formulas = [
            "gross_margin", "operating_margin", "net_margin",
            "roe", "roa", "roic",
            "pe_ratio", "pb_ratio",
            "current_ratio", "quick_ratio",
            "debt_to_equity",
            "free_cash_flow", "market_cap", "enterprise_value"
        ]

        for formula_name in key_formulas:
            formula = registry.get_formula(formula_name)
            assert formula is not None, f"Missing formula: {formula_name}"


class TestStandardDependencyGraph:
    """Test the standard dependency graph creation."""

    def test_create_standard_graph(self):
        """Test creating standard dependency graph."""
        graph = create_standard_dependency_graph()
        assert len(graph) > 30  # Should have many variables

    def test_graph_has_no_cycles(self):
        """Test that dependency graph has no cycles."""
        graph = create_standard_dependency_graph()
        has_cycle, cycle_path = graph.has_cycle()
        assert has_cycle is False, f"Graph has cycle: {cycle_path}"

    def test_graph_calculation_order(self):
        """Test that graph can produce calculation order."""
        graph = create_standard_dependency_graph()
        order = graph.get_calculation_order()
        assert len(order) > 0


class TestStandardCalculator:
    """Test the standard calculator creation and usage."""

    def test_create_standard_calculator(self):
        """Test creating standard calculator."""
        calculator = create_standard_calculator()
        assert calculator is not None
        stats = calculator.get_statistics()
        assert stats["registered_functions"] > 30

    def test_calculator_with_real_data(self):
        """Test calculator with realistic financial data."""
        calculator = create_standard_calculator()

        # Realistic financial data for a tech company
        base_data = {
            # Income Statement
            "revenue": 100000,
            "cost_of_revenue": 40000,
            "operating_income": 30000,
            "net_income": 25000,
            "ebit": 30000,
            "depreciation_amortization": 5000,

            # Balance Sheet
            "total_assets": 200000,
            "current_assets": 80000,
            "cash_and_equivalents": 30000,
            "accounts_receivable": 15000,
            "inventory": 10000,
            "total_liabilities": 80000,
            "current_liabilities": 30000,
            "short_term_debt": 5000,
            "long_term_debt": 25000,

            # Cash Flow
            "operating_cash_flow": 35000,
            "capital_expenditures": 10000,

            # Market Data
            "stock_price": 50,
            "shares_outstanding": 10000,
            "weighted_avg_shares": 10000,
        }

        # Calculate all composite variables
        results = calculator.calculate_all(base_data)

        # Verify key calculations
        assert "gross_profit" in results
        assert results["gross_profit"] == 60000  # 100000 - 40000

        assert "gross_margin" in results
        assert abs(results["gross_margin"] - 0.6) < 0.001  # 60000 / 100000

        assert "roe" in results
        # Shareholders Equity = 200000 - 80000 = 120000
        # ROE = 25000 / 120000 = 0.2083
        assert abs(results["roe"] - 0.2083) < 0.001

        assert "free_cash_flow" in results
        assert results["free_cash_flow"] == 25000  # 35000 - 10000

        assert "market_cap" in results
        assert results["market_cap"] == 500000  # 50 * 10000

    def test_calculator_handles_missing_data(self):
        """Test calculator handles missing data gracefully."""
        calculator = create_standard_calculator()

        # Minimal data
        base_data = {
            "revenue": 100000,
            "net_income": 25000,
        }

        # Should not raise error
        results = calculator.calculate_all(base_data)

        # Basic calculations should work
        assert "net_margin" in results
        assert results["net_margin"] == 0.25

    def test_calculator_handles_zero_denominators(self):
        """Test calculator handles division by zero."""
        calculator = create_standard_calculator()

        base_data = {
            "revenue": 0,  # Zero revenue
            "net_income": 25000,
            "shareholders_equity": 0,  # Zero equity
        }

        # Should not raise error
        results = calculator.calculate_all(base_data)

        # Margin calculations should return 0
        assert results.get("net_margin", 0) == 0.0
        assert results.get("roe", 0) == 0.0

    def test_incremental_update(self):
        """Test incremental update functionality."""
        calculator = create_standard_calculator()

        base_data = {
            "revenue": 100000,
            "cost_of_revenue": 40000,
            "net_income": 25000,
            "total_assets": 200000,
            "total_liabilities": 80000,
        }

        # Calculate initial
        results = calculator.calculate_all(base_data)
        initial_roe = results["roe"]

        # Update net income
        updated_data = {"net_income": 30000}
        new_results = calculator.update_and_recalculate(updated_data, results)

        # ROE should change
        assert new_results["roe"] != initial_roe
        # New ROE = 30000 / 120000 = 0.25
        assert abs(new_results["roe"] - 0.25) < 0.001


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    def test_complete_financial_analysis(self):
        """Test complete financial analysis workflow."""
        calculator = create_standard_calculator()

        # Apple-like company data (simplified)
        company_data = {
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

        results = calculator.calculate_all(company_data)

        # Verify comprehensive set of calculations
        expected_metrics = [
            "gross_profit", "gross_margin",
            "operating_margin", "net_margin",
            "roe", "roa",
            "current_ratio", "quick_ratio",
            "debt_to_equity",
            "free_cash_flow",
            "market_cap", "enterprise_value",
            "pe_ratio", "pb_ratio",
        ]

        for metric in expected_metrics:
            assert metric in results, f"Missing metric: {metric}"
            assert results[metric] is not None

        # Verify some key values
        assert results["gross_margin"] > 0.4  # Apple has high gross margins
        assert results["net_margin"] > 0.2   # Apple has strong net margins
        assert results["roe"] > 0.0          # Positive ROE
        assert results["free_cash_flow"] > 100000  # Strong FCF

    def test_performance_with_caching(self):
        """Test that caching improves performance."""
        import time

        calculator_with_cache = create_standard_calculator(enable_caching=True)
        calculator_no_cache = create_standard_calculator(enable_caching=False)

        base_data = {
            "revenue": 100000,
            "cost_of_revenue": 40000,
            "net_income": 25000,
            "total_assets": 200000,
            "total_liabilities": 80000,
            "operating_cash_flow": 35000,
            "capital_expenditures": 10000,
        }

        # First calculation (no cache benefit)
        start = time.time()
        calculator_with_cache.calculate_all(base_data)
        first_time_with_cache = time.time() - start

        # Second calculation (with cache)
        start = time.time()
        calculator_with_cache.calculate_all(base_data)
        second_time_with_cache = time.time() - start

        # No cache calculation
        start = time.time()
        calculator_no_cache.calculate_all(base_data)
        time_no_cache = time.time() - start

        # Cache should improve performance on second run
        # (or at least not make it worse)
        assert second_time_with_cache <= first_time_with_cache * 1.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
