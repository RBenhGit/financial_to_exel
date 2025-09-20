"""
Basic Unit Tests for Financial Calculations Engine
==================================================

Tests core functionality of the financial calculations engine with mock data
to improve test coverage and validate basic computational methods.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.analysis.engines.financial_calculations import FinancialCalculator
from config.config import get_config


class TestFinancialCalculatorBasic:
    """Basic tests for FinancialCalculator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_config = get_config()
        self.mock_data = {
            'Income Statement': {
                2023: {
                    'Net Income': 100000000,
                    'Revenue': 500000000,
                    'Operating Income': 150000000,
                    'Interest Expense': 5000000,
                    'Tax Expense': 25000000,
                    'Cost of Revenue': 300000000,
                    'Gross Profit': 200000000,
                    'Operating Expenses': 50000000,
                    'EBITDA': 180000000,
                    'Earnings Per Share': 2.50,
                    'Shares Outstanding': 40000000
                },
                2022: {
                    'Net Income': 80000000,
                    'Revenue': 450000000,
                    'Operating Income': 120000000,
                    'Interest Expense': 4000000,
                    'Tax Expense': 20000000,
                    'Cost of Revenue': 270000000,
                    'Gross Profit': 180000000,
                    'Operating Expenses': 60000000,
                    'EBITDA': 160000000,
                    'Earnings Per Share': 2.00,
                    'Shares Outstanding': 40000000
                }
            },
            'Balance Sheet': {
                2023: {
                    'Total Assets': 1000000000,
                    'Total Debt': 200000000,
                    'Total Equity': 600000000,
                    'Cash and Cash Equivalents': 100000000,
                    'Current Assets': 400000000,
                    'Current Liabilities': 150000000,
                    'Long Term Debt': 150000000,
                    'Short Term Debt': 50000000,
                    'Inventory': 50000000,
                    'Accounts Receivable': 80000000,
                    'Property Plant Equipment': 300000000,
                    'Intangible Assets': 200000000,
                    'Book Value': 600000000
                },
                2022: {
                    'Total Assets': 900000000,
                    'Total Debt': 180000000,
                    'Total Equity': 550000000,
                    'Cash and Cash Equivalents': 90000000,
                    'Current Assets': 350000000,
                    'Current Liabilities': 130000000,
                    'Long Term Debt': 130000000,
                    'Short Term Debt': 50000000,
                    'Inventory': 45000000,
                    'Accounts Receivable': 75000000,
                    'Property Plant Equipment': 280000000,
                    'Intangible Assets': 180000000,
                    'Book Value': 550000000
                }
            },
            'Cash Flow Statement': {
                2023: {
                    'Operating Cash Flow': 140000000,
                    'Capital Expenditures': -50000000,
                    'Free Cash Flow': 90000000,
                    'Financing Cash Flow': -30000000,
                    'Investing Cash Flow': -60000000,
                    'Depreciation and Amortization': 30000000,
                    'Stock Based Compensation': 10000000,
                    'Changes in Working Capital': -5000000,
                    'Dividends Paid': -20000000
                },
                2022: {
                    'Operating Cash Flow': 120000000,
                    'Capital Expenditures': -45000000,
                    'Free Cash Flow': 75000000,
                    'Financing Cash Flow': -25000000,
                    'Investing Cash Flow': -55000000,
                    'Depreciation and Amortization': 25000000,
                    'Stock Based Compensation': 8000000,
                    'Changes in Working Capital': -3000000,
                    'Dividends Paid': -18000000
                }
            }
        }

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_financial_calculator_initialization(self, mock_load_data):
        """Test basic initialization of FinancialCalculator."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        assert calculator.ticker_symbol == 'AAPL'
        assert calculator.financial_data == self.mock_data
        mock_load_data.assert_called_once()

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_revenue_calculation(self, mock_load_data):
        """Test revenue calculation methods."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test latest revenue
        latest_revenue = calculator.get_latest_revenue()
        assert latest_revenue == 500000000

        # Test revenue growth
        revenue_growth = calculator.calculate_revenue_growth()
        expected_growth = (500000000 - 450000000) / 450000000
        assert abs(revenue_growth - expected_growth) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_profitability_ratios(self, mock_load_data):
        """Test profitability ratio calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test gross margin
        gross_margin = calculator.calculate_gross_margin()
        expected_margin = 200000000 / 500000000  # Gross Profit / Revenue
        assert abs(gross_margin - expected_margin) < 0.001

        # Test net margin
        net_margin = calculator.calculate_net_margin()
        expected_net_margin = 100000000 / 500000000  # Net Income / Revenue
        assert abs(net_margin - expected_net_margin) < 0.001

        # Test ROE
        roe = calculator.calculate_roe()
        expected_roe = 100000000 / 600000000  # Net Income / Total Equity
        assert abs(roe - expected_roe) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_liquidity_ratios(self, mock_load_data):
        """Test liquidity ratio calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test current ratio
        current_ratio = calculator.calculate_current_ratio()
        expected_ratio = 400000000 / 150000000  # Current Assets / Current Liabilities
        assert abs(current_ratio - expected_ratio) < 0.001

        # Test quick ratio (assuming current assets - inventory)
        quick_ratio = calculator.calculate_quick_ratio()
        expected_quick = (400000000 - 50000000) / 150000000
        assert abs(quick_ratio - expected_quick) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_leverage_ratios(self, mock_load_data):
        """Test leverage ratio calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test debt-to-equity ratio
        debt_to_equity = calculator.calculate_debt_to_equity()
        expected_ratio = 200000000 / 600000000  # Total Debt / Total Equity
        assert abs(debt_to_equity - expected_ratio) < 0.001

        # Test debt-to-assets ratio
        debt_to_assets = calculator.calculate_debt_to_assets()
        expected_ratio = 200000000 / 1000000000  # Total Debt / Total Assets
        assert abs(debt_to_assets - expected_ratio) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_efficiency_ratios(self, mock_load_data):
        """Test efficiency ratio calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test asset turnover
        asset_turnover = calculator.calculate_asset_turnover()
        expected_turnover = 500000000 / 1000000000  # Revenue / Total Assets
        assert abs(asset_turnover - expected_turnover) < 0.001

        # Test inventory turnover
        inventory_turnover = calculator.calculate_inventory_turnover()
        expected_turnover = 300000000 / 50000000  # COGS / Inventory
        assert abs(inventory_turnover - expected_turnover) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_cash_flow_metrics(self, mock_load_data):
        """Test cash flow metric calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test operating cash flow
        ocf = calculator.get_operating_cash_flow()
        assert ocf == 140000000

        # Test free cash flow
        fcf = calculator.get_free_cash_flow()
        assert fcf == 90000000

        # Test FCF growth
        fcf_growth = calculator.calculate_fcf_growth()
        expected_growth = (90000000 - 75000000) / 75000000
        assert abs(fcf_growth - expected_growth) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_per_share_metrics(self, mock_load_data):
        """Test per-share metric calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test book value per share
        bvps = calculator.calculate_book_value_per_share()
        expected_bvps = 600000000 / 40000000  # Book Value / Shares Outstanding
        assert abs(bvps - expected_bvps) < 0.001

        # Test cash per share
        cash_per_share = calculator.calculate_cash_per_share()
        expected_cash = 100000000 / 40000000  # Cash / Shares Outstanding
        assert abs(cash_per_share - expected_cash) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_growth_metrics(self, mock_load_data):
        """Test growth metric calculations."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test earnings growth
        earnings_growth = calculator.calculate_earnings_growth()
        expected_growth = (100000000 - 80000000) / 80000000
        assert abs(earnings_growth - expected_growth) < 0.001

        # Test asset growth
        asset_growth = calculator.calculate_asset_growth()
        expected_growth = (1000000000 - 900000000) / 900000000
        assert abs(asset_growth - expected_growth) < 0.001

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_error_handling(self, mock_load_data):
        """Test error handling for missing data."""
        # Test with empty data
        mock_load_data.return_value = {}

        calculator = FinancialCalculator('INVALID')

        # Should handle missing data gracefully
        assert calculator.get_latest_revenue() == 0
        assert calculator.calculate_revenue_growth() == 0

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_data_validation(self, mock_load_data):
        """Test data validation methods."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Test that calculator has required data
        assert calculator.financial_data is not None
        assert 'Income Statement' in calculator.financial_data
        assert 'Balance Sheet' in calculator.financial_data
        assert 'Cash Flow Statement' in calculator.financial_data

    def test_configuration_loading(self):
        """Test configuration loading."""
        config = get_config()
        assert config is not None
        assert hasattr(config, 'data_sources')

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_financial_data_structure(self, mock_load_data):
        """Test financial data structure validation."""
        mock_load_data.return_value = self.mock_data

        calculator = FinancialCalculator('AAPL')

        # Verify data structure
        data = calculator.financial_data

        # Check that all main statements exist
        assert 'Income Statement' in data
        assert 'Balance Sheet' in data
        assert 'Cash Flow Statement' in data

        # Check that years exist
        for statement in data.values():
            assert 2023 in statement
            assert 2022 in statement

        # Check key metrics exist
        assert 'Net Income' in data['Income Statement'][2023]
        assert 'Total Assets' in data['Balance Sheet'][2023]
        assert 'Operating Cash Flow' in data['Cash Flow Statement'][2023]


class TestFinancialCalculatorMethods:
    """Test specific calculation methods."""

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_margin_calculations(self, mock_load_data):
        """Test various margin calculations."""
        mock_data = {
            'Income Statement': {
                2023: {
                    'Revenue': 1000,
                    'Gross Profit': 400,
                    'Operating Income': 200,
                    'Net Income': 150,
                    'EBITDA': 250
                }
            }
        }
        mock_load_data.return_value = mock_data

        calculator = FinancialCalculator('TEST')

        # Test various margins
        assert calculator.calculate_gross_margin() == 0.4  # 400/1000
        assert calculator.calculate_operating_margin() == 0.2  # 200/1000
        assert calculator.calculate_net_margin() == 0.15  # 150/1000
        assert calculator.calculate_ebitda_margin() == 0.25  # 250/1000

    @patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_financial_data')
    def test_ratio_edge_cases(self, mock_load_data):
        """Test ratio calculations with edge cases."""
        mock_data = {
            'Balance Sheet': {
                2023: {
                    'Current Assets': 100,
                    'Current Liabilities': 0,  # Edge case: zero denominator
                    'Total Debt': 50,
                    'Total Equity': 200
                }
            }
        }
        mock_load_data.return_value = mock_data

        calculator = FinancialCalculator('TEST')

        # Should handle division by zero gracefully
        current_ratio = calculator.calculate_current_ratio()
        assert current_ratio == float('inf') or current_ratio == 0  # Depending on implementation

        # Normal ratio should work
        debt_to_equity = calculator.calculate_debt_to_equity()
        assert debt_to_equity == 0.25  # 50/200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])