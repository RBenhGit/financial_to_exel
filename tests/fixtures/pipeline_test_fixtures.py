"""
Pipeline Test Fixtures
=====================

Reusable test fixtures for end-to-end pipeline testing.
Provides sample data for various financial scenarios.

Author: Claude Code Agent
Task: 235 - Create End-to-End Integration Tests
Date: 2025-10-20
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
import tempfile


class PipelineTestFixtures:
    """Fixtures for pipeline integration testing."""

    @staticmethod
    def create_profitable_company_data() -> Dict[str, Any]:
        """Create sample data for a profitable tech company."""
        return {
            'revenue': 500000000,  # $500M
            'cost_of_revenue': 200000000,  # $200M
            'operating_income': 180000000,  # $180M
            'net_income': 150000000,  # $150M
            'total_assets': 1000000000,  # $1B
            'current_assets': 400000000,  # $400M
            'total_liabilities': 400000000,  # $400M
            'current_liabilities': 150000000,  # $150M
            'shareholders_equity': 600000000,  # $600M
            'operating_cash_flow': 180000000,  # $180M
            'capital_expenditure': 50000000,  # $50M
            'shares_outstanding': 100000000,  # 100M shares
            'stock_price': 75.00,
            'market_cap': 7500000000,  # $7.5B
        }

    @staticmethod
    def create_loss_making_company_data() -> Dict[str, Any]:
        """Create sample data for a loss-making startup."""
        return {
            'revenue': 100000000,  # $100M
            'cost_of_revenue': 80000000,  # $80M
            'operating_income': -20000000,  # -$20M (loss)
            'net_income': -25000000,  # -$25M (loss)
            'total_assets': 500000000,  # $500M
            'current_assets': 200000000,  # $200M
            'total_liabilities': 300000000,  # $300M
            'current_liabilities': 100000000,  # $100M
            'shareholders_equity': 200000000,  # $200M
            'operating_cash_flow': -10000000,  # -$10M (cash burn)
            'capital_expenditure': 30000000,  # $30M
            'shares_outstanding': 50000000,  # 50M shares
            'stock_price': 25.00,
            'market_cap': 1250000000,  # $1.25B
        }

    @staticmethod
    def create_mature_company_data() -> Dict[str, Any]:
        """Create sample data for a mature, dividend-paying company."""
        return {
            'revenue': 1000000000,  # $1B
            'cost_of_revenue': 600000000,  # $600M
            'operating_income': 250000000,  # $250M
            'net_income': 200000000,  # $200M
            'total_assets': 2000000000,  # $2B
            'current_assets': 600000000,  # $600M
            'total_liabilities': 800000000,  # $800M
            'current_liabilities': 300000000,  # $300M
            'shareholders_equity': 1200000000,  # $1.2B
            'operating_cash_flow': 250000000,  # $250M
            'capital_expenditure': 80000000,  # $80M
            'dividends_paid': 100000000,  # $100M
            'shares_outstanding': 200000000,  # 200M shares
            'stock_price': 50.00,
            'market_cap': 10000000000,  # $10B
        }

    @staticmethod
    def create_time_series_data(
        base_revenue: float = 100000000,
        growth_rate: float = 0.10,
        years: int = 5
    ) -> Dict[str, Dict[str, float]]:
        """
        Create time series financial data with growth.

        Args:
            base_revenue: Starting revenue
            growth_rate: Annual growth rate (e.g., 0.10 for 10%)
            years: Number of years of historical data

        Returns:
            Dictionary of year -> financial metrics
        """
        data = {}
        current_year = datetime.now().year

        for i in range(years):
            year = str(current_year - (years - 1 - i))
            revenue = base_revenue * ((1 + growth_rate) ** i)

            data[year] = {
                'revenue': revenue,
                'cost_of_revenue': revenue * 0.60,  # 60% cost ratio
                'operating_income': revenue * 0.20,  # 20% operating margin
                'net_income': revenue * 0.15,  # 15% net margin
                'total_assets': revenue * 2.0,  # 2x asset turnover
                'shareholders_equity': revenue * 1.2,
                'operating_cash_flow': revenue * 0.18,
                'capital_expenditure': revenue * 0.08,
                'shares_outstanding': 100000000,  # Constant shares
            }

        return data

    @staticmethod
    def create_quarterly_data(
        base_revenue: float = 25000000,
        quarters: int = 12
    ) -> Dict[str, Dict[str, float]]:
        """
        Create quarterly financial data.

        Args:
            base_revenue: Base quarterly revenue
            quarters: Number of quarters to generate

        Returns:
            Dictionary of period -> financial metrics
        """
        data = {}
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1

        for i in range(quarters):
            # Calculate year and quarter
            quarters_back = quarters - 1 - i
            year = current_year - (quarters_back // 4)
            quarter = current_quarter - (quarters_back % 4)

            if quarter <= 0:
                quarter += 4
                year -= 1

            period = f"{year}Q{quarter}"

            # Add slight seasonality (Q4 typically higher)
            seasonality_factor = 1.1 if quarter == 4 else (0.95 if quarter == 1 else 1.0)
            revenue = base_revenue * seasonality_factor * (1.02 ** i)  # 2% quarterly growth

            data[period] = {
                'revenue': revenue,
                'cost_of_revenue': revenue * 0.60,
                'operating_income': revenue * 0.18,
                'net_income': revenue * 0.14,
                'total_assets': revenue * 8.0,  # Quarterly assets
                'shareholders_equity': revenue * 5.0,
                'operating_cash_flow': revenue * 0.16,
                'capital_expenditure': revenue * 0.06,
                'shares_outstanding': 100000000,
            }

        return data

    @staticmethod
    def create_excel_file(data: Dict[str, Dict[str, float]], file_path: Path) -> Path:
        """
        Create an Excel file from financial data.

        Args:
            data: Dictionary of period -> financial metrics
            file_path: Path where Excel file should be created

        Returns:
            Path to created Excel file
        """
        # Convert to DataFrame
        df = pd.DataFrame(data).T  # Transpose so periods are rows

        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Financials')

        return file_path

    @staticmethod
    def create_multi_sheet_excel(
        file_path: Path,
        include_balance_sheet: bool = True,
        include_cash_flow: bool = True,
        include_income_statement: bool = True
    ) -> Path:
        """
        Create Excel file with multiple financial statement sheets.

        Args:
            file_path: Path for Excel file
            include_balance_sheet: Include balance sheet data
            include_cash_flow: Include cash flow data
            include_income_statement: Include income statement data

        Returns:
            Path to created Excel file
        """
        years = ['2020', '2021', '2022', '2023']

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            if include_income_statement:
                income_data = {
                    'Revenue': [100000, 110000, 121000, 133100],
                    'Cost of Revenue': [60000, 65000, 70000, 75000],
                    'Gross Profit': [40000, 45000, 51000, 58100],
                    'Operating Income': [25000, 28000, 31000, 34000],
                    'Net Income': [20000, 23000, 26000, 29000],
                }
                df_income = pd.DataFrame(income_data, index=years)
                df_income.to_excel(writer, sheet_name='Income Statement')

            if include_balance_sheet:
                balance_data = {
                    'Total Assets': [500000, 520000, 540000, 560000],
                    'Current Assets': [200000, 210000, 220000, 230000],
                    'Total Liabilities': [200000, 205000, 210000, 215000],
                    'Current Liabilities': [80000, 85000, 90000, 95000],
                    'Shareholders Equity': [300000, 315000, 330000, 345000],
                }
                df_balance = pd.DataFrame(balance_data, index=years)
                df_balance.to_excel(writer, sheet_name='Balance Sheet')

            if include_cash_flow:
                cashflow_data = {
                    'Operating Cash Flow': [30000, 33000, 36000, 39000],
                    'Investing Cash Flow': [-15000, -16000, -17000, -18000],
                    'Financing Cash Flow': [-5000, -6000, -7000, -8000],
                    'Capital Expenditure': [10000, 11000, 12000, 13000],
                    'Free Cash Flow': [20000, 22000, 24000, 26000],
                }
                df_cashflow = pd.DataFrame(cashflow_data, index=years)
                df_cashflow.to_excel(writer, sheet_name='Cash Flow')

        return file_path

    @staticmethod
    def create_incomplete_data() -> Dict[str, Any]:
        """Create data with missing fields (common real-world scenario)."""
        return {
            'revenue': 200000000,
            # Missing: cost_of_revenue
            'operating_income': 40000000,
            'net_income': 30000000,
            # Missing: total_assets
            'shareholders_equity': 150000000,
            # Missing: cash flow data
            'shares_outstanding': 50000000,
            'stock_price': 45.00,
        }

    @staticmethod
    def create_conflicting_sources_data() -> List[Dict[str, Any]]:
        """
        Create data from multiple sources with conflicts.

        Returns:
            List of data dictionaries, each with source and timestamp
        """
        base_time = datetime.now()

        return [
            {
                'source': 'excel',
                'timestamp': base_time - timedelta(hours=2),
                'data': {
                    'revenue': 195000000,  # Older, slightly different
                    'net_income': 29000000,
                    'market_cap': 7200000000,
                }
            },
            {
                'source': 'yfinance',
                'timestamp': base_time,
                'data': {
                    'revenue': 200000000,  # Newer, should win
                    'net_income': 30000000,
                    'market_cap': 7500000000,
                }
            },
            {
                'source': 'fmp',
                'timestamp': base_time - timedelta(hours=1),
                'data': {
                    'revenue': 198000000,  # Middle timestamp
                    'net_income': 29500000,
                    'market_cap': 7350000000,
                }
            },
        ]

    @staticmethod
    def create_edge_case_data() -> Dict[str, Dict[str, Any]]:
        """Create edge case scenarios for testing robustness."""
        return {
            'zero_revenue': {
                'revenue': 0,
                'cost_of_revenue': 50000,  # Costs but no revenue
                'net_income': -50000,
            },
            'negative_equity': {
                'total_assets': 100000000,
                'total_liabilities': 150000000,  # Liabilities > Assets
                'shareholders_equity': -50000000,  # Negative equity
            },
            'extreme_ratios': {
                'revenue': 1000000,
                'net_income': 900000,  # 90% margin (unrealistic)
                'total_assets': 100000,  # Very high asset turnover
            },
            'very_small_values': {
                'revenue': 0.01,  # Micro-cap company or currency issue
                'net_income': 0.001,
            },
            'very_large_values': {
                'revenue': 1e15,  # Trillion-dollar company
                'market_cap': 5e15,
            },
        }


class MockAdapterResponses:
    """Mock responses from various data adapters."""

    @staticmethod
    def create_excel_response(symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock Excel adapter response."""
        return {
            'symbol': symbol,
            'source': 'excel',
            'timestamp': datetime.now(),
            'data': data,
            'success': True,
            'errors': [],
        }

    @staticmethod
    def create_api_response(symbol: str, data: Dict[str, Any], api_name: str = 'yfinance') -> Dict[str, Any]:
        """Create mock API adapter response."""
        return {
            'symbol': symbol,
            'source': api_name,
            'timestamp': datetime.now(),
            'data': data,
            'success': True,
            'rate_limit_remaining': 95,
            'errors': [],
        }

    @staticmethod
    def create_failed_response(symbol: str, error_msg: str) -> Dict[str, Any]:
        """Create mock failed adapter response."""
        return {
            'symbol': symbol,
            'source': 'unknown',
            'timestamp': datetime.now(),
            'data': {},
            'success': False,
            'errors': [error_msg],
        }


class PerformanceTestData:
    """Data generators for performance testing."""

    @staticmethod
    def generate_large_historical_dataset(
        symbol: str,
        years: int = 20,
        quarterly: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """Generate large historical dataset for performance testing."""
        data = {}
        periods = years * (4 if quarterly else 1)

        base_revenue = 100000000
        for i in range(periods):
            if quarterly:
                year = 2024 - (periods - i - 1) // 4
                quarter = ((periods - i - 1) % 4) + 1
                period = f"{year}Q{quarter}"
            else:
                period = str(2024 - (periods - i - 1))

            revenue = base_revenue * (1.08 ** (i / 4))  # 8% annual growth

            data[period] = {
                'revenue': revenue,
                'cost_of_revenue': revenue * 0.62,
                'operating_income': revenue * 0.18,
                'net_income': revenue * 0.14,
                'total_assets': revenue * 2.5,
                'shareholders_equity': revenue * 1.5,
                'operating_cash_flow': revenue * 0.16,
                'capital_expenditure': revenue * 0.07,
            }

        return data

    @staticmethod
    def generate_multi_symbol_dataset(
        symbols: List[str],
        periods: int = 12
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Generate data for multiple symbols for concurrent testing."""
        all_data = {}

        for idx, symbol in enumerate(symbols):
            # Vary base revenue per symbol
            base_revenue = 50000000 * (idx + 1)
            all_data[symbol] = PipelineTestFixtures.create_quarterly_data(
                base_revenue=base_revenue,
                quarters=periods
            )

        return all_data
