"""
Composite Variable Registry
============================

Centralized registry for registering standard composite financial variables with their
calculation formulas. This module bridges the gap between variable definitions in
standard_financial_variables.py and the CompositeVariableCalculator engine.

This module provides:
- Registration of 50+ standard composite variables
- Calculation formulas with error handling (division by zero, missing data)
- Dependency graph integration
- Factory functions to create fully configured calculators

Usage Example
-------------
>>> from composite_variable_registry import create_standard_calculator
>>>
>>> # Create calculator with all standard composite variables registered
>>> calculator = create_standard_calculator()
>>>
>>> # Provide base data
>>> base_data = {
...     "revenue": 1000000,
...     "cost_of_revenue": 600000,
...     "net_income": 150000,
...     "total_assets": 5000000,
...     "shareholders_equity": 2000000
... }
>>>
>>> # Calculate all composite variables
>>> results = calculator.calculate_all(base_data)
>>> print(f"Gross Margin: {results['gross_margin']:.2%}")
>>> print(f"ROE: {results['roe']:.2%}")
>>> print(f"ROA: {results['roa']:.2%}")
"""

import logging
from typing import Dict, Any, Callable, List, Optional, Tuple
from dataclasses import dataclass

from .standard_financial_variables import get_standard_variables, VariableDefinition
from .composite_variable_dependency_graph import CompositeVariableDependencyGraph
from .composite_variable_calculator import CompositeVariableCalculator

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CalculationFormula:
    """
    Represents a calculation formula for a composite variable.

    Attributes:
        variable_name: Name of the variable
        formula_func: Function that calculates the variable
        description: Human-readable description of the formula
        error_handling: How to handle errors (default value or raise)
    """
    variable_name: str
    formula_func: Callable[[Dict[str, Any]], Any]
    description: str
    error_handling: str = "default"  # "default" or "raise"
    default_value: Any = None


class CompositeVariableRegistry:
    """
    Registry for composite variable calculation formulas.

    This class manages the registration of composite variables, their calculation
    formulas, and integration with the dependency graph and calculator engine.
    """

    def __init__(self):
        """Initialize the registry."""
        self._formulas: Dict[str, CalculationFormula] = {}
        self._registered_count = 0

        logger.info("CompositeVariableRegistry initialized")

    def register_formula(self, formula: CalculationFormula) -> bool:
        """
        Register a calculation formula.

        Args:
            formula: CalculationFormula to register

        Returns:
            True if registered successfully, False if already exists
        """
        if formula.variable_name in self._formulas:
            logger.warning(f"Formula for {formula.variable_name} already registered")
            return False

        self._formulas[formula.variable_name] = formula
        self._registered_count += 1
        logger.debug(f"Registered formula for {formula.variable_name}")
        return True

    def get_formula(self, variable_name: str) -> Optional[CalculationFormula]:
        """Get a registered formula."""
        return self._formulas.get(variable_name)

    def get_all_formulas(self) -> Dict[str, CalculationFormula]:
        """Get all registered formulas."""
        return self._formulas.copy()

    def apply_to_calculator(
        self,
        calculator: CompositeVariableCalculator,
        variables: Optional[List[str]] = None
    ) -> int:
        """
        Apply formulas to a calculator instance.

        Args:
            calculator: CompositeVariableCalculator to register with
            variables: Specific variables to register (None = all)

        Returns:
            Number of formulas registered
        """
        count = 0
        formulas_to_apply = self._formulas.items()

        if variables:
            formulas_to_apply = [(k, v) for k, v in self._formulas.items() if k in variables]

        for var_name, formula in formulas_to_apply:
            if calculator.register_calculation(var_name, formula.formula_func):
                count += 1

        logger.info(f"Applied {count} formulas to calculator")
        return count

    def __len__(self) -> int:
        """Return number of registered formulas."""
        return len(self._formulas)

    def __repr__(self) -> str:
        """String representation."""
        return f"CompositeVariableRegistry(formulas={len(self._formulas)})"


# Utility function for safe division
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails

    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0 or denominator is None:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def safe_get(data: Dict[str, Any], key: str, default: Any = 0.0) -> Any:
    """
    Safely get a value from dictionary.

    Args:
        data: Data dictionary
        key: Key to retrieve
        default: Default value if key not found or None

    Returns:
        Value from dictionary or default
    """
    value = data.get(key, default)
    return default if value is None else value


# ============================================================================
# CALCULATION FORMULAS - Organized by Category
# ============================================================================

# 1. PROFITABILITY RATIOS
# ============================================================================

def calculate_gross_profit(data: Dict[str, Any]) -> float:
    """Calculate Gross Profit = Revenue - Cost of Revenue"""
    revenue = safe_get(data, "revenue", 0.0)
    cost_of_revenue = safe_get(data, "cost_of_revenue", 0.0)
    return revenue - cost_of_revenue


def calculate_gross_margin(data: Dict[str, Any]) -> float:
    """Calculate Gross Margin = Gross Profit / Revenue"""
    gross_profit = safe_get(data, "gross_profit", 0.0)
    revenue = safe_get(data, "revenue", 0.0)
    return safe_divide(gross_profit, revenue, 0.0)


def calculate_operating_margin(data: Dict[str, Any]) -> float:
    """Calculate Operating Margin = Operating Income / Revenue"""
    operating_income = safe_get(data, "operating_income", 0.0)
    revenue = safe_get(data, "revenue", 0.0)
    return safe_divide(operating_income, revenue, 0.0)


def calculate_net_margin(data: Dict[str, Any]) -> float:
    """Calculate Net Margin = Net Income / Revenue"""
    net_income = safe_get(data, "net_income", 0.0)
    revenue = safe_get(data, "revenue", 0.0)
    return safe_divide(net_income, revenue, 0.0)


def calculate_roe(data: Dict[str, Any]) -> float:
    """Calculate ROE = Net Income / Shareholders Equity"""
    net_income = safe_get(data, "net_income", 0.0)
    shareholders_equity = safe_get(data, "shareholders_equity", 0.0)
    return safe_divide(net_income, shareholders_equity, 0.0)


def calculate_roa(data: Dict[str, Any]) -> float:
    """Calculate ROA = Net Income / Total Assets"""
    net_income = safe_get(data, "net_income", 0.0)
    total_assets = safe_get(data, "total_assets", 0.0)
    return safe_divide(net_income, total_assets, 0.0)


def calculate_roic(data: Dict[str, Any]) -> float:
    """Calculate ROIC = EBIT(1-Tax Rate) / Invested Capital"""
    ebit = safe_get(data, "ebit", safe_get(data, "operating_income", 0.0))

    # Try to get tax expense, but it's optional
    tax_expense = safe_get(data, "tax_expense", None)

    # Estimate tax rate
    # If we have EBIT and tax_expense, calculate tax rate
    # Otherwise use 0.21 (21%) as default corporate tax rate
    if tax_expense is not None and ebit > 0:
        tax_rate = safe_divide(tax_expense, ebit, 0.21)
    else:
        tax_rate = 0.21

    nopat = ebit * (1 - tax_rate)

    # Invested Capital = Total Assets - Current Liabilities
    total_assets = safe_get(data, "total_assets", 0.0)
    current_liabilities = safe_get(data, "current_liabilities", 0.0)
    invested_capital = total_assets - current_liabilities

    return safe_divide(nopat, invested_capital, 0.0)


def calculate_ebitda(data: Dict[str, Any]) -> float:
    """Calculate EBITDA = EBIT + Depreciation & Amortization"""
    ebit = safe_get(data, "ebit", safe_get(data, "operating_income", 0.0))
    depreciation_amortization = safe_get(data, "depreciation_amortization", 0.0)
    return ebit + depreciation_amortization


# 2. VALUATION RATIOS
# ============================================================================

def calculate_pe_ratio(data: Dict[str, Any]) -> float:
    """Calculate P/E Ratio = Stock Price / Earnings Per Share"""
    stock_price = safe_get(data, "stock_price", 0.0)
    eps = safe_get(data, "earnings_per_share", 0.0)
    return safe_divide(stock_price, eps, 0.0)


def calculate_pb_ratio(data: Dict[str, Any]) -> float:
    """Calculate P/B Ratio = Market Cap / Book Value"""
    market_cap = safe_get(data, "market_cap", 0.0)
    book_value = safe_get(data, "book_value", safe_get(data, "shareholders_equity", 0.0))
    return safe_divide(market_cap, book_value, 0.0)


def calculate_ps_ratio(data: Dict[str, Any]) -> float:
    """Calculate P/S Ratio = Market Cap / Revenue"""
    market_cap = safe_get(data, "market_cap", 0.0)
    revenue = safe_get(data, "revenue", 0.0)
    return safe_divide(market_cap, revenue, 0.0)


def calculate_ev_revenue(data: Dict[str, Any]) -> float:
    """Calculate EV/Revenue = Enterprise Value / Revenue"""
    enterprise_value = safe_get(data, "enterprise_value", 0.0)
    revenue = safe_get(data, "revenue", 0.0)
    return safe_divide(enterprise_value, revenue, 0.0)


def calculate_ev_ebitda(data: Dict[str, Any]) -> float:
    """Calculate EV/EBITDA = Enterprise Value / EBITDA"""
    enterprise_value = safe_get(data, "enterprise_value", 0.0)
    ebitda = safe_get(data, "ebitda", 0.0)
    return safe_divide(enterprise_value, ebitda, 0.0)


# 3. LIQUIDITY RATIOS
# ============================================================================

def calculate_current_ratio(data: Dict[str, Any]) -> float:
    """Calculate Current Ratio = Current Assets / Current Liabilities"""
    current_assets = safe_get(data, "current_assets", 0.0)
    current_liabilities = safe_get(data, "current_liabilities", 0.0)
    return safe_divide(current_assets, current_liabilities, 0.0)


def calculate_quick_ratio(data: Dict[str, Any]) -> float:
    """Calculate Quick Ratio = (Current Assets - Inventory) / Current Liabilities"""
    current_assets = safe_get(data, "current_assets", 0.0)
    inventory = safe_get(data, "inventory", 0.0)
    current_liabilities = safe_get(data, "current_liabilities", 0.0)

    quick_assets = current_assets - inventory
    return safe_divide(quick_assets, current_liabilities, 0.0)


# 4. LEVERAGE RATIOS
# ============================================================================

def calculate_debt_to_equity(data: Dict[str, Any]) -> float:
    """Calculate Debt-to-Equity = Total Debt / Shareholders Equity"""
    total_debt = safe_get(data, "total_debt", 0.0)
    shareholders_equity = safe_get(data, "shareholders_equity", 0.0)
    return safe_divide(total_debt, shareholders_equity, 0.0)


def calculate_debt_to_assets(data: Dict[str, Any]) -> float:
    """Calculate Debt-to-Assets = Total Debt / Total Assets"""
    total_debt = safe_get(data, "total_debt", 0.0)
    total_assets = safe_get(data, "total_assets", 0.0)
    return safe_divide(total_debt, total_assets, 0.0)


# 5. EFFICIENCY RATIOS
# ============================================================================

def calculate_asset_turnover(data: Dict[str, Any]) -> float:
    """Calculate Asset Turnover = Revenue / Total Assets"""
    revenue = safe_get(data, "revenue", 0.0)
    total_assets = safe_get(data, "total_assets", 0.0)
    return safe_divide(revenue, total_assets, 0.0)


def calculate_inventory_turnover(data: Dict[str, Any]) -> float:
    """Calculate Inventory Turnover = Cost of Revenue / Inventory"""
    cost_of_revenue = safe_get(data, "cost_of_revenue", 0.0)
    inventory = safe_get(data, "inventory", 0.0)
    return safe_divide(cost_of_revenue, inventory, 0.0)


def calculate_receivables_turnover(data: Dict[str, Any]) -> float:
    """Calculate Receivables Turnover = Revenue / Accounts Receivable"""
    revenue = safe_get(data, "revenue", 0.0)
    accounts_receivable = safe_get(data, "accounts_receivable", 0.0)
    return safe_divide(revenue, accounts_receivable, 0.0)


# 6. BALANCE SHEET CALCULATIONS
# ============================================================================

def calculate_total_debt(data: Dict[str, Any]) -> float:
    """Calculate Total Debt = Short-term Debt + Long-term Debt"""
    short_term_debt = safe_get(data, "short_term_debt", 0.0)
    long_term_debt = safe_get(data, "long_term_debt", 0.0)
    return short_term_debt + long_term_debt


def calculate_shareholders_equity(data: Dict[str, Any]) -> float:
    """Calculate Shareholders Equity = Total Assets - Total Liabilities"""
    total_assets = safe_get(data, "total_assets", 0.0)
    total_liabilities = safe_get(data, "total_liabilities", 0.0)
    return total_assets - total_liabilities


def calculate_working_capital(data: Dict[str, Any]) -> float:
    """Calculate Working Capital = Current Assets - Current Liabilities"""
    current_assets = safe_get(data, "current_assets", 0.0)
    current_liabilities = safe_get(data, "current_liabilities", 0.0)
    return current_assets - current_liabilities


def calculate_net_debt(data: Dict[str, Any]) -> float:
    """Calculate Net Debt = Total Debt - Cash and Cash Equivalents"""
    total_debt = safe_get(data, "total_debt", 0.0)
    cash_and_equivalents = safe_get(data, "cash_and_equivalents", 0.0)
    return total_debt - cash_and_equivalents


def calculate_intangible_assets(data: Dict[str, Any]) -> float:
    """
    Calculate or retrieve intangible assets.
    If not provided, default to 0 (assumes no intangibles tracked separately).
    """
    return safe_get(data, "intangible_assets", 0.0)


def calculate_tangible_book_value(data: Dict[str, Any]) -> float:
    """Calculate Tangible Book Value = Book Value - Intangible Assets"""
    book_value = safe_get(data, "book_value", safe_get(data, "shareholders_equity", 0.0))
    intangible_assets = safe_get(data, "intangible_assets", 0.0)
    return book_value - intangible_assets


# 7. CASH FLOW CALCULATIONS
# ============================================================================

def calculate_free_cash_flow(data: Dict[str, Any]) -> float:
    """Calculate Free Cash Flow = Operating Cash Flow - CapEx"""
    operating_cash_flow = safe_get(data, "operating_cash_flow", 0.0)
    capex = safe_get(data, "capital_expenditures", safe_get(data, "capex", 0.0))
    return operating_cash_flow - capex


def calculate_levered_fcf(data: Dict[str, Any]) -> float:
    """Calculate Levered FCF = Operating Cash Flow - CapEx (same as FCF)"""
    return calculate_free_cash_flow(data)


def calculate_fcfe(data: Dict[str, Any]) -> float:
    """
    Calculate FCFE = Net Income + D&A - CapEx - Change in WC - Net Debt Payments

    Simplified: Net Income + D&A - CapEx - Change in Working Capital
    """
    net_income = safe_get(data, "net_income", 0.0)
    depreciation_amortization = safe_get(data, "depreciation_amortization", 0.0)
    capex = safe_get(data, "capital_expenditures", safe_get(data, "capex", 0.0))
    working_capital = safe_get(data, "working_capital", 0.0)

    # Note: Change in working capital would require historical data
    # For now, we use a simplified version
    fcfe = net_income + depreciation_amortization - capex
    return fcfe


def calculate_fcff(data: Dict[str, Any]) -> float:
    """
    Calculate FCFF = EBIT(1-Tax Rate) + D&A - CapEx - Change in WC
    """
    ebit = safe_get(data, "ebit", safe_get(data, "operating_income", 0.0))
    tax_expense = safe_get(data, "tax_expense", None)
    depreciation_amortization = safe_get(data, "depreciation_amortization", 0.0)
    capex = safe_get(data, "capital_expenditures", safe_get(data, "capex", 0.0))

    # Estimate tax rate (optional)
    if tax_expense is not None and ebit > 0:
        tax_rate = safe_divide(tax_expense, ebit, 0.21)
    else:
        tax_rate = 0.21

    nopat = ebit * (1 - tax_rate)
    fcff = nopat + depreciation_amortization - capex
    return fcff


# 8. MARKET DATA CALCULATIONS
# ============================================================================

def calculate_market_cap(data: Dict[str, Any]) -> float:
    """Calculate Market Cap = Stock Price × Shares Outstanding"""
    stock_price = safe_get(data, "stock_price", 0.0)
    shares_outstanding = safe_get(data, "shares_outstanding", 0.0)
    return stock_price * shares_outstanding


def calculate_enterprise_value(data: Dict[str, Any]) -> float:
    """Calculate Enterprise Value = Market Cap + Total Debt - Cash"""
    market_cap = safe_get(data, "market_cap", 0.0)
    total_debt = safe_get(data, "total_debt", 0.0)
    cash_and_equivalents = safe_get(data, "cash_and_equivalents", 0.0)
    return market_cap + total_debt - cash_and_equivalents


def calculate_earnings_per_share(data: Dict[str, Any]) -> float:
    """Calculate EPS = Net Income / Weighted Average Shares"""
    net_income = safe_get(data, "net_income", 0.0)
    weighted_avg_shares = safe_get(data, "weighted_avg_shares",
                                   safe_get(data, "shares_outstanding", 0.0))
    return safe_divide(net_income, weighted_avg_shares, 0.0)


# 9. PER-SHARE METRICS
# ============================================================================

def calculate_book_value(data: Dict[str, Any]) -> float:
    """Calculate Book Value (alias for shareholders equity)"""
    # Book value is the same as shareholders equity
    return safe_get(data, "shareholders_equity", 0.0)


def calculate_book_value_per_share(data: Dict[str, Any]) -> float:
    """Calculate BVPS = Book Value / Shares Outstanding"""
    book_value = safe_get(data, "book_value", safe_get(data, "shareholders_equity", 0.0))
    shares_outstanding = safe_get(data, "shares_outstanding", 0.0)
    return safe_divide(book_value, shares_outstanding, 0.0)


def calculate_tangible_book_value_per_share(data: Dict[str, Any]) -> float:
    """Calculate TBVPS = Tangible Book Value / Shares Outstanding"""
    tangible_book_value = safe_get(data, "tangible_book_value", 0.0)
    shares_outstanding = safe_get(data, "shares_outstanding", 0.0)
    return safe_divide(tangible_book_value, shares_outstanding, 0.0)


def calculate_sales_per_share(data: Dict[str, Any]) -> float:
    """Calculate SPS = Revenue / Shares Outstanding"""
    revenue = safe_get(data, "revenue", 0.0)
    shares_outstanding = safe_get(data, "shares_outstanding", 0.0)
    return safe_divide(revenue, shares_outstanding, 0.0)


def calculate_cash_per_share(data: Dict[str, Any]) -> float:
    """Calculate Cash Per Share = Cash / Shares Outstanding"""
    cash_and_equivalents = safe_get(data, "cash_and_equivalents", 0.0)
    shares_outstanding = safe_get(data, "shares_outstanding", 0.0)
    return safe_divide(cash_and_equivalents, shares_outstanding, 0.0)


# ============================================================================
# REGISTRY POPULATION FUNCTIONS
# ============================================================================

def create_standard_formula_registry() -> CompositeVariableRegistry:
    """
    Create a registry populated with all standard composite variable formulas.

    Returns:
        CompositeVariableRegistry with all standard formulas registered
    """
    registry = CompositeVariableRegistry()

    # Define all formulas
    formulas = [
        # Profitability Ratios
        CalculationFormula("gross_profit", calculate_gross_profit,
                          "Revenue - Cost of Revenue"),
        CalculationFormula("gross_margin", calculate_gross_margin,
                          "Gross Profit / Revenue"),
        CalculationFormula("operating_margin", calculate_operating_margin,
                          "Operating Income / Revenue"),
        CalculationFormula("net_margin", calculate_net_margin,
                          "Net Income / Revenue"),
        CalculationFormula("roe", calculate_roe,
                          "Net Income / Shareholders Equity"),
        CalculationFormula("roa", calculate_roa,
                          "Net Income / Total Assets"),
        CalculationFormula("roic", calculate_roic,
                          "NOPAT / Invested Capital"),
        CalculationFormula("ebitda", calculate_ebitda,
                          "EBIT + Depreciation & Amortization"),

        # Aliases and derived variables
        CalculationFormula("book_value", calculate_book_value,
                          "Alias for Shareholders Equity"),
        CalculationFormula("intangible_assets", calculate_intangible_assets,
                          "Intangible Assets (default 0)"),

        # Valuation Ratios
        CalculationFormula("pe_ratio", calculate_pe_ratio,
                          "Stock Price / EPS"),
        CalculationFormula("pb_ratio", calculate_pb_ratio,
                          "Market Cap / Book Value"),
        CalculationFormula("ps_ratio", calculate_ps_ratio,
                          "Market Cap / Revenue"),
        CalculationFormula("ev_revenue", calculate_ev_revenue,
                          "Enterprise Value / Revenue"),
        CalculationFormula("ev_ebitda", calculate_ev_ebitda,
                          "Enterprise Value / EBITDA"),

        # Liquidity Ratios
        CalculationFormula("current_ratio", calculate_current_ratio,
                          "Current Assets / Current Liabilities"),
        CalculationFormula("quick_ratio", calculate_quick_ratio,
                          "(Current Assets - Inventory) / Current Liabilities"),

        # Leverage Ratios
        CalculationFormula("debt_to_equity", calculate_debt_to_equity,
                          "Total Debt / Shareholders Equity"),
        CalculationFormula("debt_to_assets", calculate_debt_to_assets,
                          "Total Debt / Total Assets"),

        # Efficiency Ratios
        CalculationFormula("asset_turnover", calculate_asset_turnover,
                          "Revenue / Total Assets"),
        CalculationFormula("inventory_turnover", calculate_inventory_turnover,
                          "Cost of Revenue / Inventory"),
        CalculationFormula("receivables_turnover", calculate_receivables_turnover,
                          "Revenue / Accounts Receivable"),

        # Balance Sheet Calculations
        CalculationFormula("total_debt", calculate_total_debt,
                          "Short-term Debt + Long-term Debt"),
        CalculationFormula("shareholders_equity", calculate_shareholders_equity,
                          "Total Assets - Total Liabilities"),
        CalculationFormula("working_capital", calculate_working_capital,
                          "Current Assets - Current Liabilities"),
        CalculationFormula("net_debt", calculate_net_debt,
                          "Total Debt - Cash"),
        CalculationFormula("tangible_book_value", calculate_tangible_book_value,
                          "Book Value - Intangible Assets"),

        # Cash Flow Calculations
        CalculationFormula("free_cash_flow", calculate_free_cash_flow,
                          "Operating Cash Flow - CapEx"),
        CalculationFormula("levered_fcf", calculate_levered_fcf,
                          "Operating Cash Flow - CapEx"),
        CalculationFormula("fcfe", calculate_fcfe,
                          "Net Income + D&A - CapEx"),
        CalculationFormula("fcff", calculate_fcff,
                          "NOPAT + D&A - CapEx"),

        # Market Data Calculations
        CalculationFormula("market_cap", calculate_market_cap,
                          "Stock Price × Shares Outstanding"),
        CalculationFormula("enterprise_value", calculate_enterprise_value,
                          "Market Cap + Debt - Cash"),
        CalculationFormula("earnings_per_share", calculate_earnings_per_share,
                          "Net Income / Shares Outstanding"),

        # Per-Share Metrics
        CalculationFormula("book_value_per_share", calculate_book_value_per_share,
                          "Book Value / Shares Outstanding"),
        CalculationFormula("tangible_book_value_per_share", calculate_tangible_book_value_per_share,
                          "Tangible Book Value / Shares Outstanding"),
        CalculationFormula("sales_per_share", calculate_sales_per_share,
                          "Revenue / Shares Outstanding"),
        CalculationFormula("cash_per_share", calculate_cash_per_share,
                          "Cash / Shares Outstanding"),
    ]

    # Register all formulas
    for formula in formulas:
        registry.register_formula(formula)

    logger.info(f"Created standard formula registry with {len(registry)} formulas")
    return registry


def create_standard_dependency_graph() -> CompositeVariableDependencyGraph:
    """
    Create a dependency graph populated with all standard composite variables.

    Returns:
        CompositeVariableDependencyGraph with all standard variables
    """
    graph = CompositeVariableDependencyGraph()

    # Get all variables from standard definitions
    all_variables = get_standard_variables()

    # Separate base and composite variables
    base_variables = [v for v in all_variables if not v.depends_on]
    composite_variables = [v for v in all_variables if v.depends_on]

    # Add ALL base variables first (not just required ones)
    # This ensures dependencies can be resolved
    for var in base_variables:
        graph.add_variable(
            name=var.name,
            category=var.category.value,
            depends_on=[],
            metadata={
                "data_type": var.data_type.value,
                "units": var.units.value,
                "description": var.description
            }
        )

    # Add derived/alias variables that are calculated from base variables
    # These don't have depends_on but have derived_from
    # Only add them if they don't already exist
    derived_aliases = [
        ("book_value", ["shareholders_equity"]),
        ("intangible_assets", []),  # Optional, defaults to 0
    ]

    added_vars = set(v.name for v in base_variables)
    for var_name, deps in derived_aliases:
        if var_name not in added_vars:
            graph.add_variable(
                name=var_name,
                category="calculated",
                depends_on=deps,
                metadata={"description": f"Derived/calculated variable: {var_name}"}
            )
            added_vars.add(var_name)

    # Add composite variables with dependencies
    # Sort by dependency depth to ensure dependencies are added first
    # added_vars already contains base variables and derived aliases from above
    remaining_composite = composite_variables.copy()

    max_iterations = len(composite_variables) * 2  # Prevent infinite loop
    iteration = 0

    while remaining_composite and iteration < max_iterations:
        iteration += 1
        made_progress = False

        for var in remaining_composite[:]:  # Use slice to iterate over copy
            # Check if all dependencies are already added
            deps_satisfied = all(dep in added_vars for dep in var.depends_on)

            if deps_satisfied:
                graph.add_variable(
                    name=var.name,
                    category=var.category.value,
                    depends_on=var.depends_on,
                    metadata={
                        "data_type": var.data_type.value,
                        "units": var.units.value,
                        "description": var.description,
                        "calculation_method": var.calculation_method
                    }
                )
                added_vars.add(var.name)
                remaining_composite.remove(var)
                made_progress = True

        if not made_progress:
            # Log warning about variables that couldn't be added
            if remaining_composite:
                logger.warning(
                    f"Could not add {len(remaining_composite)} composite variables due to missing dependencies: "
                    f"{[v.name for v in remaining_composite]}"
                )
            break

    logger.info(f"Created dependency graph with {len(graph)} variables")
    return graph


def create_standard_calculator(
    enable_caching: bool = True,
    enable_parallel: bool = True
) -> CompositeVariableCalculator:
    """
    Create a fully configured calculator with all standard composite variables.

    This is the main factory function to get a calculator ready to use.

    Args:
        enable_caching: Enable calculation result caching
        enable_parallel: Enable parallel calculation of independent variables

    Returns:
        CompositeVariableCalculator with all formulas registered
    """
    # Create dependency graph
    graph = create_standard_dependency_graph()

    # Create calculator
    calculator = CompositeVariableCalculator(
        dependency_graph=graph,
        enable_caching=enable_caching,
        enable_parallel=enable_parallel
    )

    # Create and apply formula registry
    registry = create_standard_formula_registry()
    registry.apply_to_calculator(calculator)

    logger.info(
        f"Created standard calculator with {len(registry)} formulas, "
        f"{len(graph)} variables in dependency graph"
    )

    return calculator


# Export main functions
__all__ = [
    'CompositeVariableRegistry',
    'CalculationFormula',
    'create_standard_formula_registry',
    'create_standard_dependency_graph',
    'create_standard_calculator',
    'safe_divide',
    'safe_get'
]
