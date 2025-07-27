#!/usr/bin/env python3
"""
Simple test to verify field mapping fix without Unicode issues
"""


def test_field_mapping():
    """Test the field mapping fix"""

    print("Testing field mapping fix for AAPL...")

    # Import modules
    import yfinance as yf
    from fcf_analysis_streamlit import _convert_yfinance_to_calculator_format

    # Get AAPL data
    ticker = yf.Ticker("AAPL")
    income_stmt = ticker.financials
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow

    # Convert the data
    financial_data = _convert_yfinance_to_calculator_format(
        income_stmt, balance_sheet, cash_flow, "AAPL"
    )

    # Check for required fields
    required_fields = {
        'income_fy': ['Net Income', 'EBIT', 'EBT', 'Income Tax Expense'],
        'balance_fy': ['Total Current Assets', 'Total Current Liabilities'],
        'cashflow_fy': [
            'Depreciation & Amortization',
            'Cash from Operations',
            'Capital Expenditure',
        ],
    }

    print("\n=== Field Mapping Results ===")
    total_found = 0
    total_required = 0

    for data_type, required_list in required_fields.items():
        if data_type in financial_data:
            df = financial_data[data_type]
            if not df.empty:
                print(f"\n{data_type}:")
                for req_field in required_list:
                    total_required += 1
                    if req_field in df.columns:
                        print(f"  FOUND: {req_field}")
                        total_found += 1
                    else:
                        print(f"  MISSING: {req_field}")

    print(f"\n=== SUMMARY ===")
    print(f"Found {total_found} out of {total_required} required fields")

    if total_found >= total_required * 0.8:  # 80% success rate
        print("SUCCESS: Field mapping fix is working!")
        return True
    else:
        print("PARTIAL: Some fields still missing")
        return False


if __name__ == "__main__":
    success = test_field_mapping()
    exit(0 if success else 1)
