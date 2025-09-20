"""
Comprehensive test fixtures for analysis modules
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any


@pytest.fixture
def sample_fcf_data():
    """Sample FCF data for testing"""
    return {
        'FCFE': [10000, 11000, 12000, 13000, 14000],
        'FCFF': [12000, 13200, 14400, 15600, 16800],
        'levered_fcf': [9000, 9900, 10800, 11700, 12600],
        'free_cash_flow': [10500, 11550, 12600, 13650, 14700]
    }


@pytest.fixture
def sample_financial_statements():
    """Sample financial statements for testing"""
    years = [2019, 2020, 2021, 2022, 2023]

    income_statement = pd.DataFrame({
        'Year': years,
        'Revenue': [100000, 110000, 120000, 130000, 140000],
        'Operating Income': [20000, 22000, 24000, 26000, 28000],
        'Net Income': [15000, 16500, 18000, 19500, 21000],
        'Interest Expense': [2000, 2200, 2400, 2600, 2800]
    })

    balance_sheet = pd.DataFrame({
        'Year': years,
        'Total Assets': [200000, 220000, 240000, 260000, 280000],
        'Total Debt': [50000, 55000, 60000, 65000, 70000],
        'Cash and Cash Equivalents': [20000, 25000, 30000, 35000, 40000],
        'Total Equity': [120000, 135000, 150000, 165000, 180000],
        'Shares Outstanding': [1000, 1050, 1100, 1150, 1200]
    })

    cash_flow = pd.DataFrame({
        'Year': years,
        'Operating Cash Flow': [25000, 27500, 30000, 32500, 35000],
        'Capital Expenditures': [-15000, -16500, -18000, -19500, -21000],
        'Free Cash Flow': [10000, 11000, 12000, 13000, 14000]
    })

    return {
        'income_statement': income_statement,
        'balance_sheet': balance_sheet,
        'cash_flow': cash_flow
    }


@pytest.fixture
def comprehensive_mock_calculator(sample_fcf_data, sample_financial_statements):
    """Create comprehensive mock FinancialCalculator for testing"""
    calc = Mock()
    calc.company_name = "Test Company"
    calc.ticker_symbol = "TEST"

    # Set up financial statements
    calc.income_statement = sample_financial_statements['income_statement']
    calc.balance_sheet = sample_financial_statements['balance_sheet']
    calc.cash_flow = sample_financial_statements['cash_flow']

    # FCF methods
    calc.calculate_all_fcf_types.return_value = sample_fcf_data
    calc.get_financial_data.return_value = sample_financial_statements['income_statement']['Revenue'].tolist()

    # FCF results for DCF module
    calc.fcf_results = sample_fcf_data

    # Make FCF data accessible through var_input_data style access
    def mock_get_variable(variable_name):
        fcf_mapping = {
            'FCFE': sample_fcf_data['FCFE'],
            'FCFF': sample_fcf_data['FCFF'],
            'levered_fcf': sample_fcf_data['levered_fcf'],
            'free_cash_flow': sample_fcf_data['free_cash_flow']
        }
        return fcf_mapping.get(variable_name, [])

    calc.get_variable = mock_get_variable

    return calc


@pytest.fixture
def mock_var_input_data(sample_fcf_data):
    """Mock var_input_data system"""
    with patch('core.data_processing.var_input_data.get_var_input_data') as mock_var_data:
        mock_instance = Mock()

        def mock_get_variable(variable_name, **kwargs):
            fcf_mapping = {
                'FCFE': sample_fcf_data['FCFE'],
                'FCFF': sample_fcf_data['FCFF'],
                'levered_fcf': sample_fcf_data['levered_fcf'],
                'free_cash_flow': sample_fcf_data['free_cash_flow']
            }
            # Return data in the format expected by DCF: list of (period, value) tuples
            data = fcf_mapping.get(variable_name, [])
            if data:
                return [(f"2019-{i}", value) for i, value in enumerate(data, 1)]
            return []

        mock_instance.get_variable = mock_get_variable
        mock_var_data.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def dcf_valuator_with_mocks(comprehensive_mock_calculator, mock_var_input_data):
    """Create DCF valuator with comprehensive mocks"""
    from core.analysis.dcf.dcf_valuation import DCFValuator
    return DCFValuator(comprehensive_mock_calculator)


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'current_price': 150.0,
        'market_cap': 180000000,  # $180M
        'beta': 1.2,
        'risk_free_rate': 0.03,
        'market_premium': 0.06
    }


@pytest.fixture
def dcf_assumptions():
    """Standard DCF assumptions for testing"""
    return {
        'discount_rate': 0.10,
        'terminal_growth_rate': 0.03,
        'growth_rate_yr1_5': 0.15,
        'growth_rate_yr5_10': 0.08,
        'projection_years': 10,
        'terminal_method': 'gordon_growth',
        'fcf_type': 'FCFF'
    }


class AnalysisFixtures:
    """Comprehensive test fixtures and utilities for analysis testing"""

    @staticmethod
    def get_sample_fcf_data():
        """Get sample FCF data for testing"""
        return {
            'FCFE': [10000, 11000, 12000, 13000, 14000],
            'FCFF': [12000, 13200, 14400, 15600, 16800],
            'levered_fcf': [9000, 9900, 10800, 11700, 12600],
            'free_cash_flow': [10500, 11550, 12600, 13650, 14700]
        }

    @staticmethod
    def get_sample_financial_statements():
        """Get sample financial statements for testing"""
        years = [2019, 2020, 2021, 2022, 2023]

        income_statement = pd.DataFrame({
            'Year': years,
            'Revenue': [100000, 110000, 120000, 130000, 140000],
            'Operating Income': [20000, 22000, 24000, 26000, 28000],
            'Net Income': [15000, 16500, 18000, 19500, 21000],
            'Interest Expense': [2000, 2200, 2400, 2600, 2800]
        })

        balance_sheet = pd.DataFrame({
            'Year': years,
            'Total Assets': [200000, 220000, 240000, 260000, 280000],
            'Total Debt': [50000, 55000, 60000, 65000, 70000],
            'Cash and Cash Equivalents': [20000, 25000, 30000, 35000, 40000],
            'Total Equity': [120000, 135000, 150000, 165000, 180000],
            'Shares Outstanding': [1000, 1050, 1100, 1150, 1200]
        })

        cash_flow = pd.DataFrame({
            'Year': years,
            'Operating Cash Flow': [25000, 27500, 30000, 32500, 35000],
            'Capital Expenditures': [-15000, -16500, -18000, -19500, -21000],
            'Free Cash Flow': [10000, 11000, 12000, 13000, 14000]
        })

        return {
            'income_statement': income_statement,
            'balance_sheet': balance_sheet,
            'cash_flow': cash_flow
        }

    @staticmethod
    def get_mock_calculator():
        """Get comprehensive mock FinancialCalculator for testing"""
        calc = Mock()
        calc.company_name = "Test Company"
        calc.ticker_symbol = "TEST"

        # Set up financial statements
        statements = AnalysisFixtures.get_sample_financial_statements()
        calc.income_statement = statements['income_statement']
        calc.balance_sheet = statements['balance_sheet']
        calc.cash_flow = statements['cash_flow']

        # FCF methods
        fcf_data = AnalysisFixtures.get_sample_fcf_data()
        calc.calculate_all_fcf_types.return_value = fcf_data
        calc.get_financial_data.return_value = statements['income_statement']['Revenue'].tolist()
        calc.fcf_results = fcf_data

        return calc