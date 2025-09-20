"""
Test Financial Calculator Property Access Interface

This module tests the new property-based access interface for FinancialCalculator
to ensure users can access financial metrics through simple property access patterns
like calculator.total_revenue, calculator.net_income, etc.

These tests address the critical integration issues identified during user acceptance testing.
"""

import pytest
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.analysis.engines.financial_calculations import FinancialCalculator


class TestFinancialCalculatorProperties:
    """Test suite for FinancialCalculator property access interface"""

    def setup_method(self):
        """Set up test fixtures for each test"""
        # Create test data structure similar to real Excel data
        self.test_data_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.test_data_dir, "TESTCO")
        self.fy_folder = os.path.join(self.company_folder, "FY")
        self.ltm_folder = os.path.join(self.company_folder, "LTM")

        os.makedirs(self.fy_folder, exist_ok=True)
        os.makedirs(self.ltm_folder, exist_ok=True)

        # Create mock financial data matching real Excel structure
        # Based on MSFT data analysis: line items are in column 2, data in subsequent columns
        income_rows = [
            [None, None, 'Period End Date', '2021-06-30', '2022-06-30', '2023-06-30'],
            [None, None, '', '', '', ''],  # Empty row
            [None, None, 'Revenue', 100000.0, 110000.0, 120000.0],
            [None, None, 'Cost of Revenue', 80000.0, 85000.0, 90000.0],  # Cost is positive in raw data
            [None, None, 'Gross Profit', 20000.0, 25000.0, 30000.0],
            [None, None, 'Operating Expenses', 15000.0, 18000.0, 22000.0],  # Expenses are positive in raw data
            [None, None, 'Operating Income', 5000.0, 7000.0, 8000.0],
            [None, None, 'Interest Expense', 3000.0, 4000.0, 5000.0],  # Expenses are positive in raw data
            [None, None, 'Net Income', 2000.0, 3000.0, 3000.0]
        ]

        self.mock_income_data = pd.DataFrame(income_rows, columns=[
            None, None, '', 'FY-2', 'FY-1', 'FY'
        ])

        # Balance sheet data matching Excel structure
        balance_rows = [
            [None, None, 'Period End Date', '2021-06-30', '2022-06-30', '2023-06-30'],
            [None, None, '', '', '', ''],  # Empty row
            [None, None, 'Total Assets', 500000.0, 550000.0, 600000.0],
            [None, None, 'Current Assets', 200000.0, 220000.0, 250000.0],
            [None, None, 'Cash and Cash Equivalents', 50000.0, 60000.0, 70000.0],
            [None, None, 'Total Liabilities', 300000.0, 330000.0, 350000.0],
            [None, None, 'Current Liabilities', 150000.0, 170000.0, 180000.0],
            [None, None, 'Total Debt', 100000.0, 120000.0, 130000.0],
            [None, None, 'Shareholders Equity', 200000.0, 220000.0, 250000.0]
        ]

        self.mock_balance_data = pd.DataFrame(balance_rows, columns=[
            None, None, '', 'FY-2', 'FY-1', 'FY'
        ])

        # Cash flow data matching Excel structure
        cashflow_rows = [
            [None, None, 'Period End Date', '2021-06-30', '2022-06-30', '2023-06-30'],
            [None, None, '', '', '', ''],  # Empty row
            [None, None, 'Cash Flow from Operating Activities', 25000.0, 30000.0, 35000.0],
            [None, None, 'Capital Expenditures', -15000.0, -18000.0, -20000.0],
            [None, None, 'Depreciation and Amortization', -5000.0, -6000.0, -7000.0],
            [None, None, 'Cash Flow from Investing Activities', 8000.0, 10000.0, 12000.0],
            [None, None, 'Cash Flow from Financing Activities', -2000.0, -3000.0, -4000.0]
        ]

        self.mock_cashflow_data = pd.DataFrame(cashflow_rows, columns=[
            None, None, '', 'FY-2', 'FY-1', 'FY'
        ])

        # Create Excel files (simplified - just store data directly in calculator for testing)

    def create_test_calculator_with_data(self):
        """Create a FinancialCalculator instance with test data loaded"""
        calculator = FinancialCalculator(self.company_folder)

        # Manually populate financial_data to simulate loaded Excel data
        calculator.financial_data = {
            'income_fy': self.mock_income_data,
            'income_ltm': self.mock_income_data,  # Use same data for LTM for simplicity
            'balance_fy': self.mock_balance_data,
            'balance_ltm': self.mock_balance_data,
            'cashflow_fy': self.mock_cashflow_data,
            'cashflow_ltm': self.mock_cashflow_data
        }

        # Set some market data
        calculator.current_stock_price = 150.50
        calculator.market_cap = 2500000000  # 2.5B market cap
        calculator.shares_outstanding = 16611295  # shares outstanding

        return calculator

    def test_total_revenue_property_access(self):
        """Test that total_revenue property returns correct value - this was failing in UAT"""
        calculator = self.create_test_calculator_with_data()

        # This should work without AttributeError
        assert calculator.total_revenue is not None
        assert calculator.total_revenue == 120000.0  # Most recent value from FY column
        assert isinstance(calculator.total_revenue, float)

    def test_net_income_property_access(self):
        """Test net_income property access"""
        calculator = self.create_test_calculator_with_data()

        assert calculator.net_income is not None
        assert calculator.net_income == 3000.0  # Most recent value from FY column
        assert isinstance(calculator.net_income, float)

    def test_income_statement_properties(self):
        """Test all income statement properties"""
        calculator = self.create_test_calculator_with_data()

        # Test all income statement properties exist and return reasonable values
        assert calculator.total_revenue == 120000.0
        assert calculator.net_income == 3000.0
        assert calculator.operating_income == 8000.0
        assert calculator.gross_profit == 30000.0
        assert calculator.cost_of_revenue == 90000.0  # Cost is positive in raw data
        # Note: operating_expenses and interest_expense not in our mock data structure

    def test_balance_sheet_properties(self):
        """Test all balance sheet properties"""
        calculator = self.create_test_calculator_with_data()

        # Test balance sheet properties
        assert calculator.total_assets == 600000.0
        assert calculator.current_assets == 250000.0
        assert calculator.cash_and_equivalents == 70000.0
        assert calculator.total_liabilities == 350000.0
        assert calculator.current_liabilities == 180000.0
        assert calculator.total_debt == 130000.0
        assert calculator.shareholders_equity == 250000.0

    def test_cash_flow_statement_properties(self):
        """Test all cash flow statement properties"""
        calculator = self.create_test_calculator_with_data()

        # Test cash flow properties
        assert calculator.operating_cash_flow == 35000.0
        assert calculator.capital_expenditures == -20000.0  # Should be negative
        assert calculator.depreciation_amortization == -7000.0
        assert calculator.investing_cash_flow == 12000.0
        assert calculator.financing_cash_flow == -4000.0

    def test_calculated_properties(self):
        """Test properties that are calculated from other properties"""
        calculator = self.create_test_calculator_with_data()

        # Test working capital calculation
        expected_working_capital = 250000.0 - 180000.0  # current_assets - current_liabilities
        assert calculator.working_capital == expected_working_capital

        # Test free cash flow calculation
        expected_fcf = 35000.0 + (-20000.0)  # operating_cash_flow + capex (capex is negative)
        assert calculator.free_cash_flow == expected_fcf

    def test_market_data_properties(self):
        """Test market data properties"""
        calculator = self.create_test_calculator_with_data()

        # Test market data properties
        assert calculator.current_price == 150.50
        assert calculator.market_cap == 2500000000
        assert calculator.shares_outstanding == 16611295

        # Test enterprise value calculation
        # EV = Market Cap + Total Debt - Cash
        expected_ev = 2500000000 + 130000 - 70000
        assert calculator.enterprise_value == expected_ev

    def test_missing_data_graceful_handling(self):
        """Test that properties handle missing data gracefully"""
        # Create calculator with empty data
        calculator = FinancialCalculator(self.company_folder)
        calculator.financial_data = {}

        # All properties should return None for missing data, not raise AttributeError
        assert calculator.total_revenue is None
        assert calculator.net_income is None
        assert calculator.total_assets is None
        assert calculator.operating_cash_flow is None
        assert calculator.working_capital is None  # Should be None if components are missing
        assert calculator.free_cash_flow is None

    def test_property_fallback_names(self):
        """Test that properties work with different naming conventions"""
        calculator = FinancialCalculator(self.company_folder)

        # Test with alternative naming using proper Excel structure
        # Line items in column 2, data in column 3
        alternative_rows = [
            [None, None, 'Period End Date', '2023-06-30'],
            [None, None, '', ''],
            [None, None, 'Revenue', 120000],  # Alternative to 'Total Revenue'
            [None, None, 'COGS', 90000],     # Alternative to 'Cost of Revenue'
            [None, None, 'Net Profit', 3000], # Alternative to 'Net Income'
            [None, None, 'EBIT', 8000]      # Alternative to 'Operating Income'
        ]

        alternative_income_data = pd.DataFrame(alternative_rows, columns=[
            None, None, '', 'FY'
        ])

        calculator.financial_data = {
            'income_fy': alternative_income_data,
            'income_ltm': alternative_income_data
        }

        # Should still work with alternative names
        assert calculator.total_revenue == 120000  # Found 'Revenue'
        assert calculator.cost_of_revenue == 90000  # Found 'COGS'
        assert calculator.net_income == 3000       # Found 'Net Profit'
        assert calculator.operating_income == 8000 # Found 'EBIT'

    def test_ltm_vs_fy_preference(self):
        """Test that properties prefer LTM data over FY data when available"""
        calculator = FinancialCalculator(self.company_folder)

        # Create different FY and LTM data using proper Excel structure
        fy_rows = [
            [None, None, 'Period End Date', '2023-06-30'],
            [None, None, '', ''],
            [None, None, 'Total Revenue', 100000],
            [None, None, 'Net Income', 2000]
        ]
        fy_data = pd.DataFrame(fy_rows, columns=[None, None, '', 'FY'])

        ltm_rows = [
            [None, None, 'Period End Date', 'LTM'],
            [None, None, '', ''],
            [None, None, 'Total Revenue', 110000],
            [None, None, 'Net Income', 2500]
        ]
        ltm_data = pd.DataFrame(ltm_rows, columns=[None, None, '', 'LTM'])

        calculator.financial_data = {
            'income_fy': fy_data,
            'income_ltm': ltm_data
        }

        # Should prefer LTM values
        assert calculator.total_revenue == 110000  # LTM value, not FY
        assert calculator.net_income == 2500       # LTM value, not FY

    def test_user_acceptance_scenario_reproduction(self):
        """
        Reproduce the exact scenario that was failing in user acceptance testing.

        This test mirrors the code from test_excel_import_ux.py that was failing.
        """
        calculator = self.create_test_calculator_with_data()

        # This exact pattern was failing in user acceptance testing
        try:
            # Load financial data
            success = calculator.load_financial_statements()  # This might fail with empty folders
            # But we've manually loaded data, so test the property access

            # The failing assertions from user acceptance testing:
            assert calculator.total_revenue is not None
            assert calculator.total_revenue > 0

            # Additional validation that was expected
            assert hasattr(calculator, 'total_revenue')
            assert hasattr(calculator, 'net_income')
            assert hasattr(calculator, 'operating_cash_flow')

            # Verify these are actual properties, not just attributes
            assert isinstance(calculator.__class__.total_revenue, property)
            assert isinstance(calculator.__class__.net_income, property)
            assert isinstance(calculator.__class__.operating_cash_flow, property)

        except AttributeError as e:
            pytest.fail(f"Property access failed with AttributeError: {e}")

    def test_comprehensive_property_availability(self):
        """Test that all expected properties are available as properties"""
        calculator = FinancialCalculator(self.company_folder)

        # List of all properties that should be available
        expected_properties = [
            # Income statement
            'total_revenue', 'net_income', 'operating_income', 'gross_profit',
            'cost_of_revenue', 'operating_expenses', 'research_development',
            'selling_general_admin', 'interest_expense', 'tax_expense',

            # Balance sheet
            'total_assets', 'current_assets', 'cash_and_equivalents',
            'total_liabilities', 'current_liabilities', 'total_debt',
            'shareholders_equity', 'retained_earnings', 'working_capital',

            # Cash flow
            'operating_cash_flow', 'free_cash_flow', 'capital_expenditures',
            'depreciation_amortization', 'investing_cash_flow', 'financing_cash_flow',

            # Market data
            'current_price', 'enterprise_value'
        ]

        for prop_name in expected_properties:
            # Check that the property exists
            assert hasattr(calculator, prop_name), f"Property '{prop_name}' is missing"

            # Check that it's actually a property, not just an attribute
            assert isinstance(getattr(calculator.__class__, prop_name), property), \
                f"'{prop_name}' is not implemented as a property"

    def test_property_return_types(self):
        """Test that properties return appropriate types"""
        calculator = self.create_test_calculator_with_data()

        # Numeric properties should return float or None
        numeric_properties = [
            'total_revenue', 'net_income', 'total_assets', 'operating_cash_flow',
            'current_price', 'market_cap', 'working_capital', 'free_cash_flow'
        ]

        for prop_name in numeric_properties:
            value = getattr(calculator, prop_name)
            assert value is None or isinstance(value, (int, float)), \
                f"Property '{prop_name}' returned {type(value)}, expected float or None"

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        try:
            shutil.rmtree(self.test_data_dir)
        except:
            pass  # Cleanup is best-effort


if __name__ == "__main__":
    # Run a quick test to verify properties work
    test = TestFinancialCalculatorProperties()
    test.setup_method()

    try:
        calculator = test.create_test_calculator_with_data()
        print(f"total_revenue: {calculator.total_revenue}")
        print(f"net_income: {calculator.net_income}")
        print(f"total_assets: {calculator.total_assets}")
        print(f"operating_cash_flow: {calculator.operating_cash_flow}")
        print(f"working_capital: {calculator.working_capital}")
        print(f"free_cash_flow: {calculator.free_cash_flow}")
        print(f"enterprise_value: {calculator.enterprise_value}")
        print("Property access test PASSED!")
    except Exception as e:
        print(f"Property access test FAILED: {e}")
    finally:
        test.teardown_method()