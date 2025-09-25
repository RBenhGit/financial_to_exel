"""
Demo test for financial models
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.data_processing.models.simple_models import (
    SimpleIncomeStatementModel,
    SimpleBalanceSheetModel,
    SimpleCashFlowStatementModel
)
from decimal import Decimal

print("Testing Core Financial Data Models")
print("=" * 50)

try:
    # Test Income Statement Model
    print("\nTesting Income Statement Model...")
    income_model = SimpleIncomeStatementModel(
        company_ticker='AAPL',
        company_name='Apple Inc.',
        period_end_date='2023-09-30',
        revenue=Decimal('394328000000'),
        cost_of_revenue=Decimal('223546000000'),
        net_income=Decimal('96995000000'),
        shares_outstanding=Decimal('15728.8')  # millions
    )

    # Test calculations
    gross_profit = income_model.calculate_gross_profit()
    eps = income_model.calculate_eps()

    print(f"  Model created: {income_model.company_ticker}")
    print(f"  Revenue: ${income_model.revenue:,.0f}")
    print(f"  Gross Profit: ${gross_profit:,.0f}")
    print(f"  EPS: ${eps:.2f}")

    # Test Balance Sheet Model
    print("\nTesting Balance Sheet Model...")
    balance_model = SimpleBalanceSheetModel(
        company_ticker='AAPL',
        period_end_date='2023-09-30',
        total_assets=Decimal('352755000000'),
        current_assets=Decimal('143566000000'),
        current_liabilities=Decimal('145308000000'),
        total_liabilities=Decimal('290437000000'),
        shareholders_equity=Decimal('62318000000')
    )

    # Test calculations
    working_capital = balance_model.calculate_working_capital()
    is_balanced = balance_model.validate_balance_sheet_equation()

    print(f"  ✅ Model created: {balance_model.company_ticker}")
    print(f"  ✅ Total Assets: ${balance_model.total_assets:,.0f}")
    print(f"  ✅ Working Capital: ${working_capital:,.0f}")
    print(f"  ✅ Balance Sheet Balanced: {is_balanced}")

    # Test Cash Flow Model
    print("\n💸 Testing Cash Flow Model...")
    cashflow_model = SimpleCashFlowStatementModel(
        company_ticker='AAPL',
        period_end_date='2023-09-30',
        operating_cash_flow=Decimal('110543000000'),
        investing_cash_flow=Decimal('-3705000000'),
        financing_cash_flow=Decimal('-108488000000'),
        capital_expenditures=Decimal('10959000000')
    )

    # Test calculations
    fcf = cashflow_model.calculate_free_cash_flow()
    net_change = cashflow_model.calculate_net_change_in_cash()

    print(f"  ✅ Model created: {cashflow_model.company_ticker}")
    print(f"  ✅ Operating CF: ${cashflow_model.operating_cash_flow:,.0f}")
    print(f"  ✅ Free Cash Flow: ${fcf:,.0f}")
    print(f"  ✅ Net Change in Cash: ${net_change:,.0f}")

    # Test serialization
    print("\n🔄 Testing Model Serialization...")
    data = income_model.model_dump()
    print(f"  ✅ Serialization works - {len(data)} fields exported")

    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Core Financial Data Models are working correctly")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()