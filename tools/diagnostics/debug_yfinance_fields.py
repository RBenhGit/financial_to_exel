#!/usr/bin/env python3
"""
Debug script to check yfinance field names for AAPL

DEPRECATION WARNING: This diagnostic tool uses direct yfinance imports for debugging purposes.
This is intentionally preserved for diagnostic use only. Production code should use VarInputData
for all data access. See Task 233 for details on the centralized data infrastructure migration.
"""

import warnings
import yfinance as yf
import pandas as pd

# Issue deprecation warning when this module is imported
warnings.warn(
    "This diagnostic tool uses direct yfinance imports and is preserved for debugging purposes only. "
    "Production code must use VarInputData for all data access. "
    "See .taskmaster/docs/task_233_migration_strategy.md for details.",
    DeprecationWarning,
    stacklevel=2
)


def check_yfinance_fields():
    """Check what field names yfinance provides for AAPL"""

    print("Fetching AAPL data from yfinance...")
    ticker = yf.Ticker("AAPL")

    # Get financial statements
    print("\n=== Income Statement Fields ===")
    income_stmt = ticker.financials
    if not income_stmt.empty:
        print("Available fields:")
        for i, field in enumerate(income_stmt.index):
            print(f"  {i+1:2d}. {field}")
    else:
        print("No income statement data available")

    print("\n=== Balance Sheet Fields ===")
    balance_sheet = ticker.balance_sheet
    if not balance_sheet.empty:
        print("Available fields:")
        for i, field in enumerate(balance_sheet.index):
            print(f"  {i+1:2d}. {field}")
    else:
        print("No balance sheet data available")

    print("\n=== Cash Flow Fields ===")
    cash_flow = ticker.cashflow
    if not cash_flow.empty:
        print("Available fields:")
        for i, field in enumerate(cash_flow.index):
            print(f"  {i+1:2d}. {field}")
    else:
        print("No cash flow data available")

    print("\n=== Looking for Required Fields ===")
    required_fields = [
        "Net Income",
        "EBIT",
        "EBT",
        "Income Tax Expense",
        "Total Current Assets",
        "Total Current Liabilities",
        "Depreciation & Amortization",
        "Cash from Operations",
        "Capital Expenditure",
    ]

    all_fields = set()
    if not income_stmt.empty:
        all_fields.update(income_stmt.index)
    if not balance_sheet.empty:
        all_fields.update(balance_sheet.index)
    if not cash_flow.empty:
        all_fields.update(cash_flow.index)

    for req_field in required_fields:
        print(f"\nSearching for: '{req_field}'")
        matches = [field for field in all_fields if req_field.lower() in field.lower()]
        if matches:
            print(f"  Found similar fields: {matches}")
        else:
            print(f"  No similar fields found")


if __name__ == "__main__":
    check_yfinance_fields()
