"""
Financial Calculator Property Interface Definition

This module defines the standard property interface that users expect
when accessing financial metrics from the FinancialCalculator class.

Based on user acceptance testing, users expect to access financial data
through simple property access patterns like calculator.total_revenue,
calculator.net_income, etc.
"""

from typing import Optional, Dict, Any
from enum import Enum


class FinancialPeriod(Enum):
    """Enum for financial reporting periods"""
    FY = "FY"      # Full Year
    LTM = "LTM"    # Last Twelve Months
    LATEST = "LATEST"  # Most recent available


class StandardFinancialProperties:
    """
    Definition of standard financial properties that users expect to access
    directly from FinancialCalculator instances.

    These properties should return the most recent/relevant financial metric
    values, typically preferring LTM data when available, falling back to FY data.
    """

    # Income Statement Properties
    INCOME_STATEMENT_PROPERTIES = {
        'total_revenue': {
            'description': 'Total Revenue/Sales for the most recent period',
            'fallback_names': ['Revenue', 'Net Revenue', 'Sales', 'Total Sales'],
            'data_type': float,
            'required': True
        },
        'net_income': {
            'description': 'Net Income for the most recent period',
            'fallback_names': ['Net Income', 'Net Profit', 'Profit After Tax'],
            'data_type': float,
            'required': True
        },
        'operating_income': {
            'description': 'Operating Income/EBIT for the most recent period',
            'fallback_names': ['Operating Income', 'EBIT', 'Earnings Before Interest and Tax'],
            'data_type': float,
            'required': False
        },
        'gross_profit': {
            'description': 'Gross Profit for the most recent period',
            'fallback_names': ['Gross Profit', 'Gross Income'],
            'data_type': float,
            'required': False
        },
        'cost_of_revenue': {
            'description': 'Cost of Goods Sold/Cost of Revenue',
            'fallback_names': ['Cost of Revenue', 'Cost of Goods Sold', 'COGS'],
            'data_type': float,
            'required': False
        },
        'operating_expenses': {
            'description': 'Total Operating Expenses',
            'fallback_names': ['Operating Expenses', 'Total Operating Expenses'],
            'data_type': float,
            'required': False
        },
        'research_development': {
            'description': 'Research and Development Expenses',
            'fallback_names': ['Research and Development', 'R&D', 'Research & Development'],
            'data_type': float,
            'required': False
        },
        'selling_general_admin': {
            'description': 'Selling, General & Administrative Expenses',
            'fallback_names': ['Selling General and Administrative', 'SG&A', 'SGA'],
            'data_type': float,
            'required': False
        },
        'interest_expense': {
            'description': 'Interest Expense',
            'fallback_names': ['Interest Expense', 'Interest'],
            'data_type': float,
            'required': False
        },
        'tax_expense': {
            'description': 'Income Tax Expense',
            'fallback_names': ['Tax Expense', 'Income Tax Expense', 'Provision for Income Tax'],
            'data_type': float,
            'required': False
        }
    }

    # Balance Sheet Properties
    BALANCE_SHEET_PROPERTIES = {
        'total_assets': {
            'description': 'Total Assets as of most recent period end',
            'fallback_names': ['Total Assets'],
            'data_type': float,
            'required': True
        },
        'current_assets': {
            'description': 'Current Assets as of most recent period end',
            'fallback_names': ['Current Assets', 'Total Current Assets'],
            'data_type': float,
            'required': False
        },
        'cash_and_equivalents': {
            'description': 'Cash and Cash Equivalents',
            'fallback_names': ['Cash and Cash Equivalents', 'Cash and Equivalents', 'Cash'],
            'data_type': float,
            'required': False
        },
        'total_liabilities': {
            'description': 'Total Liabilities as of most recent period end',
            'fallback_names': ['Total Liabilities'],
            'data_type': float,
            'required': True
        },
        'current_liabilities': {
            'description': 'Current Liabilities as of most recent period end',
            'fallback_names': ['Current Liabilities', 'Total Current Liabilities'],
            'data_type': float,
            'required': False
        },
        'total_debt': {
            'description': 'Total Debt (Short-term + Long-term)',
            'fallback_names': ['Total Debt', 'Total Financial Debt'],
            'data_type': float,
            'required': False
        },
        'shareholders_equity': {
            'description': 'Total Shareholders Equity',
            'fallback_names': ['Shareholders Equity', 'Total Equity', 'Stockholders Equity'],
            'data_type': float,
            'required': True
        },
        'retained_earnings': {
            'description': 'Retained Earnings',
            'fallback_names': ['Retained Earnings'],
            'data_type': float,
            'required': False
        },
        'working_capital': {
            'description': 'Working Capital (Current Assets - Current Liabilities)',
            'fallback_names': ['Working Capital'],
            'data_type': float,
            'required': False,
            'calculated': True  # This is typically calculated rather than directly reported
        }
    }

    # Cash Flow Statement Properties
    CASH_FLOW_PROPERTIES = {
        'operating_cash_flow': {
            'description': 'Cash Flow from Operating Activities',
            'fallback_names': ['Cash Flow from Operating Activities', 'Operating Cash Flow', 'Net Cash from Operations'],
            'data_type': float,
            'required': True
        },
        'free_cash_flow': {
            'description': 'Free Cash Flow (Operating CF - CapEx)',
            'fallback_names': ['Free Cash Flow'],
            'data_type': float,
            'required': False,
            'calculated': True
        },
        'capital_expenditures': {
            'description': 'Capital Expenditures (typically negative)',
            'fallback_names': ['Capital Expenditures', 'CapEx', 'Purchase of Property Plant Equipment'],
            'data_type': float,
            'required': False
        },
        'depreciation_amortization': {
            'description': 'Depreciation and Amortization',
            'fallback_names': ['Depreciation and Amortization', 'Depreciation & Amortization', 'D&A'],
            'data_type': float,
            'required': False
        },
        'investing_cash_flow': {
            'description': 'Cash Flow from Investing Activities',
            'fallback_names': ['Cash Flow from Investing Activities', 'Net Cash from Investing'],
            'data_type': float,
            'required': False
        },
        'financing_cash_flow': {
            'description': 'Cash Flow from Financing Activities',
            'fallback_names': ['Cash Flow from Financing Activities', 'Net Cash from Financing'],
            'data_type': float,
            'required': False
        }
    }

    # Market Data Properties
    MARKET_DATA_PROPERTIES = {
        'current_price': {
            'description': 'Current stock price per share',
            'fallback_names': ['Current Price', 'Stock Price', 'Price'],
            'data_type': float,
            'required': False,
            'source': 'api'
        },
        'market_cap': {
            'description': 'Market Capitalization',
            'fallback_names': ['Market Cap', 'Market Capitalization'],
            'data_type': float,
            'required': False,
            'source': 'api'
        },
        'shares_outstanding': {
            'description': 'Total Shares Outstanding',
            'fallback_names': ['Shares Outstanding', 'Outstanding Shares'],
            'data_type': float,
            'required': False,
            'source': 'api'
        },
        'enterprise_value': {
            'description': 'Enterprise Value (Market Cap + Total Debt - Cash)',
            'fallback_names': ['Enterprise Value', 'EV'],
            'data_type': float,
            'required': False,
            'calculated': True
        }
    }

    # Company Information Properties
    COMPANY_INFO_PROPERTIES = {
        'company_name': {
            'description': 'Company name',
            'fallback_names': ['Company Name', 'Name'],
            'data_type': str,
            'required': False
        },
        'ticker_symbol': {
            'description': 'Stock ticker symbol',
            'fallback_names': ['Ticker', 'Symbol'],
            'data_type': str,
            'required': False
        },
        'currency': {
            'description': 'Reporting currency',
            'fallback_names': ['Currency'],
            'data_type': str,
            'required': False
        }
    }

    @classmethod
    def get_all_properties(cls) -> Dict[str, Dict[str, Any]]:
        """Get all defined properties as a single dictionary"""
        all_properties = {}
        all_properties.update(cls.INCOME_STATEMENT_PROPERTIES)
        all_properties.update(cls.BALANCE_SHEET_PROPERTIES)
        all_properties.update(cls.CASH_FLOW_PROPERTIES)
        all_properties.update(cls.MARKET_DATA_PROPERTIES)
        all_properties.update(cls.COMPANY_INFO_PROPERTIES)
        return all_properties

    @classmethod
    def get_required_properties(cls) -> Dict[str, Dict[str, Any]]:
        """Get only properties marked as required"""
        all_properties = cls.get_all_properties()
        return {
            name: config for name, config in all_properties.items()
            if config.get('required', False)
        }

    @classmethod
    def get_calculated_properties(cls) -> Dict[str, Dict[str, Any]]:
        """Get properties that need to be calculated rather than extracted"""
        all_properties = cls.get_all_properties()
        return {
            name: config for name, config in all_properties.items()
            if config.get('calculated', False)
        }


class PropertyExtractor:
    """
    Utility class for extracting property values from financial data structures.

    Handles the logic of finding values in pandas DataFrames using fallback names
    and proper period selection (LTM vs FY).
    """

    @staticmethod
    def extract_value_from_dataframe(df, property_config: Dict[str, Any], period: FinancialPeriod = FinancialPeriod.LATEST) -> Optional[float]:
        """
        Extract a financial metric value from a pandas DataFrame.

        Args:
            df: pandas DataFrame containing financial data
            property_config: Property configuration from StandardFinancialProperties
            period: Which period to prefer (LATEST, LTM, FY)

        Returns:
            The extracted value or None if not found
        """
        if df is None or df.empty:
            return None

        # Try to find the metric using fallback names
        for name in property_config['fallback_names']:
            if name in df.index:
                # Get the most recent value (rightmost column)
                try:
                    value = df.loc[name].iloc[-1] if len(df.loc[name].shape) > 0 else df.loc[name]
                    if value is not None and not pd.isna(value):
                        return float(value)
                except (KeyError, IndexError, TypeError):
                    continue

        return None

    @staticmethod
    def calculate_derived_metric(property_name: str, financial_data: Dict) -> Optional[float]:
        """
        Calculate derived metrics that aren't directly in financial statements.

        Args:
            property_name: Name of the property to calculate
            financial_data: Dictionary containing financial statement DataFrames

        Returns:
            Calculated value or None if calculation not possible
        """
        if property_name == 'working_capital':
            # Working Capital = Current Assets - Current Liabilities
            current_assets = PropertyExtractor.extract_value_from_dataframe(
                financial_data.get('balance_ltm') or financial_data.get('balance_fy'),
                StandardFinancialProperties.BALANCE_SHEET_PROPERTIES['current_assets']
            )
            current_liabilities = PropertyExtractor.extract_value_from_dataframe(
                financial_data.get('balance_ltm') or financial_data.get('balance_fy'),
                StandardFinancialProperties.BALANCE_SHEET_PROPERTIES['current_liabilities']
            )

            if current_assets is not None and current_liabilities is not None:
                return current_assets - current_liabilities

        elif property_name == 'free_cash_flow':
            # Free Cash Flow = Operating Cash Flow - Capital Expenditures
            operating_cf = PropertyExtractor.extract_value_from_dataframe(
                financial_data.get('cashflow_ltm') or financial_data.get('cashflow_fy'),
                StandardFinancialProperties.CASH_FLOW_PROPERTIES['operating_cash_flow']
            )
            capex = PropertyExtractor.extract_value_from_dataframe(
                financial_data.get('cashflow_ltm') or financial_data.get('cashflow_fy'),
                StandardFinancialProperties.CASH_FLOW_PROPERTIES['capital_expenditures']
            )

            if operating_cf is not None and capex is not None:
                # CapEx is typically negative in cash flow statements
                return operating_cf - abs(capex)

        return None


# Import pandas only when needed
try:
    import pandas as pd
except ImportError:
    pd = None