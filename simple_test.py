"""Simple test for financial models"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.data_processing.models.simple_models import SimpleIncomeStatementModel
from decimal import Decimal

print("Testing Core Financial Data Models")
print("=" * 40)

try:
    # Create a simple income statement model
    model = SimpleIncomeStatementModel(
        company_ticker='AAPL',
        period_end_date='2023-09-30',
        revenue=Decimal('100000'),
        cost_of_revenue=Decimal('60000'),
        net_income=Decimal('20000'),
        shares_outstanding=Decimal('1000')  # millions
    )

    print(f"Model created: {model.company_ticker}")
    print(f"Revenue: ${model.revenue:,.0f}")

    # Test calculations
    gross_profit = model.calculate_gross_profit()
    eps = model.calculate_eps()

    print(f"Gross Profit: ${gross_profit:,.0f}")
    print(f"EPS: ${eps:.2f}")

    # Test serialization
    data = model.model_dump()
    print(f"Serialization: {len(data)} fields")

    print("SUCCESS: All tests passed!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()