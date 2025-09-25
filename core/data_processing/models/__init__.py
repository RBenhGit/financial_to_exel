"""
Core Financial Data Models
==========================

Pydantic models for financial statements with comprehensive validation rules
and business logic constraints.

This module provides structured data models for:
- Income Statements
- Balance Sheets
- Cash Flow Statements
- Base financial statement model with common fields

All models include:
- Field validation using Pydantic validators
- Business logic constraints (e.g., balance sheet equation)
- Cross-field validation for financial statement integrity
- Type hints and field descriptions
- Factory methods for easy instantiation

Usage Example:
--------------
>>> from models import SimpleIncomeStatementModel
>>> from decimal import Decimal
>>>
>>> # Create income statement model
>>> income_stmt = SimpleIncomeStatementModel(
...     company_ticker="AAPL",
...     period_end_date="2023-12-31",
...     revenue=Decimal("100000000000"),
...     cost_of_revenue=Decimal("60000000000")
... )
>>>
>>> # Calculate gross profit
>>> gross_profit = income_stmt.calculate_gross_profit()
>>> print(f"Gross Profit: ${gross_profit:,.0f}")
"""

# Import working simple models
from .simple_models import (
    SimpleFinancialStatementModel,
    SimpleIncomeStatementModel,
    SimpleBalanceSheetModel,
    SimpleCashFlowStatementModel,
    ReportingPeriod,
    Currency,
    DataSource
)

# Export as the standard interface names
BaseFinancialStatementModel = SimpleFinancialStatementModel
IncomeStatementModel = SimpleIncomeStatementModel
BalanceSheetModel = SimpleBalanceSheetModel
CashFlowStatementModel = SimpleCashFlowStatementModel

__all__ = [
    # Standard model names
    'BaseFinancialStatementModel',
    'IncomeStatementModel',
    'BalanceSheetModel',
    'CashFlowStatementModel',

    # Simple model names (for explicit use)
    'SimpleFinancialStatementModel',
    'SimpleIncomeStatementModel',
    'SimpleBalanceSheetModel',
    'SimpleCashFlowStatementModel',

    # Enums
    'ReportingPeriod',
    'Currency',
    'DataSource'
]