"""
Mock data generators for testing financial calculations without external dependencies.

This module provides consistent test data generation to replace redundant
data creation across test files.
"""

import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import random


class MockDataGenerator:
    """Generate consistent mock data for testing"""

    @staticmethod
    def generate_fcf_data(years: int = 5, include_negative: bool = True) -> Dict[str, List[float]]:
        """
        Generate realistic FCF data for testing

        Args:
            years (int): Number of years of data to generate
            include_negative (bool): Whether to include some negative FCF values

        Returns:
            Dict[str, List[float]]: FCF data by type
        """
        # Set seed for reproducible test data
        np.random.seed(42)

        # Base FCF values with growth
        base_fcf = 100  # Start with $100M FCF
        growth_rate = 0.05  # 5% growth
        volatility = 0.15  # 15% volatility

        fcf_data = {}

        for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
            values = []
            current_fcf = base_fcf + np.random.normal(
                0, 20
            )  # Different starting point for each type

            for year in range(years):
                # Add growth and some volatility
                growth = np.random.normal(growth_rate, volatility)
                current_fcf = current_fcf * (1 + growth)

                # Occasionally add negative values if requested
                if include_negative and year > 0 and np.random.random() < 0.1:
                    current_fcf = -abs(current_fcf) * 0.3

                values.append(round(current_fcf, 1))

            fcf_data[fcf_type] = values

        return fcf_data

    @staticmethod
    def generate_financial_metrics(num_years: int = 3) -> Dict[str, List[float]]:
        """
        Generate sample financial metrics for testing

        Args:
            num_years (int): Number of years of data

        Returns:
            Dict[str, List[float]]: Financial metrics by category
        """
        np.random.seed(42)

        metrics = {
            # Income statement metrics
            'revenue': [1000 * (1.1**i) + np.random.normal(0, 50) for i in range(num_years)],
            'ebit': [200 * (1.08**i) + np.random.normal(0, 20) for i in range(num_years)],
            'net_income': [150 * (1.12**i) + np.random.normal(0, 15) for i in range(num_years)],
            'tax_expense': [-30 * (1.1**i) + np.random.normal(0, 5) for i in range(num_years)],
            # Balance sheet metrics
            'current_assets': [300 * (1.05**i) + np.random.normal(0, 30) for i in range(num_years)],
            'current_liabilities': [
                200 * (1.03**i) + np.random.normal(0, 20) for i in range(num_years)
            ],
            'total_assets': [1000 * (1.08**i) + np.random.normal(0, 80) for i in range(num_years)],
            # Cash flow metrics
            'cash_from_operations': [
                250 * (1.07**i) + np.random.normal(0, 25) for i in range(num_years)
            ],
            'capex': [-80 * (1.04**i) + np.random.normal(0, 10) for i in range(num_years)],
            'depreciation': [50 * (1.02**i) + np.random.normal(0, 5) for i in range(num_years)],
            'cash_from_financing': [
                -20 * (1.15**i) + np.random.normal(0, 15) for i in range(num_years)
            ],
        }

        # Round values to 1 decimal place
        for key, values in metrics.items():
            metrics[key] = [round(v, 1) for v in values]

        return metrics

    @staticmethod
    def generate_dcf_inputs() -> Dict[str, float]:
        """
        Generate sample DCF valuation inputs

        Returns:
            Dict[str, float]: DCF input parameters
        """
        return {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.025,
            'growth_rate_yr1_5': 0.08,
            'growth_rate_yr5_10': 0.04,
            'shares_outstanding': 100.0,
            'net_debt': 500.0,
            'current_stock_price': 150.0,
        }

    @staticmethod
    def generate_market_data(ticker: str = 'TEST') -> Dict[str, Any]:
        """
        Generate mock market data for testing yfinance operations

        Args:
            ticker (str): Ticker symbol

        Returns:
            Dict[str, Any]: Mock market data
        """
        return {
            'symbol': ticker,
            'currentPrice': 150.0 + np.random.normal(0, 10),
            'marketCap': 15000000000 + np.random.normal(0, 1000000000),
            'sharesOutstanding': 100000000 + np.random.normal(0, 5000000),
            'enterpriseValue': 16000000000 + np.random.normal(0, 1200000000),
            'totalDebt': 2000000000 + np.random.normal(0, 200000000),
            'totalCash': 1000000000 + np.random.normal(0, 100000000),
            'currency': 'USD',
            'exchange': 'NASDAQ',
        }

    @staticmethod
    def generate_growth_rates(periods: List[int] = None) -> Dict[str, Dict[str, float]]:
        """
        Generate sample growth rates for testing

        Args:
            periods (List[int]): List of periods (years)

        Returns:
            Dict[str, Dict[str, float]]: Growth rates by FCF type and period
        """
        if periods is None:
            periods = [1, 3, 5, 10]

        np.random.seed(42)

        growth_rates = {}

        for fcf_type in ['FCFF', 'FCFE', 'LFCF', 'Average']:
            type_rates = {}

            for period in periods:
                # Generate realistic growth rates with some variation
                base_rate = 0.05  # 5% base growth
                variation = np.random.normal(0, 0.02)  # +/- 2% variation
                growth_rate = base_rate + variation

                # Longer periods tend to have lower growth rates
                if period > 5:
                    growth_rate *= 0.8

                type_rates[f'{period}yr'] = round(growth_rate, 4)

            growth_rates[fcf_type] = type_rates

        return growth_rates

    @staticmethod
    def generate_excel_dataframe(rows: int = 20, cols: int = 6) -> pd.DataFrame:
        """
        Generate a DataFrame that mimics Excel financial statement structure

        Args:
            rows (int): Number of rows
            cols (int): Number of columns

        Returns:
            pd.DataFrame: Mock Excel-like financial data
        """
        data = []

        # Header rows
        data.append(['Test Company Inc'] + [''] * (cols - 1))
        data.append(['Financial Statement'] + [''] * (cols - 1))
        data.append(['Period End Date', '', ''] + [f'12/31/{2020 + i}' for i in range(cols - 3)])
        data.append([''] * cols)

        # Financial metrics
        metrics = [
            ('Revenue', [1000, 1100, 1200]),
            ('Operating Expenses', [-800, -850, -900]),
            ('EBIT', [200, 250, 300]),
            ('Net Income', [150, 180, 220]),
            ('Total Assets', [2000, 2200, 2400]),
            ('Current Assets', [500, 550, 600]),
            ('Current Liabilities', [300, 320, 350]),
            ('Cash from Operations', [250, 280, 320]),
            ('Capital Expenditures', [-100, -120, -140]),
            ('Free Cash Flow', [150, 160, 180]),
        ]

        for metric_name, values in metrics:
            row = [metric_name, '', ''] + values + [''] * (cols - len(values) - 3)
            data.append(row)

        # Fill remaining rows with empty data
        while len(data) < rows:
            data.append([''] * cols)

        return pd.DataFrame(data)

    @staticmethod
    def generate_sensitivity_analysis_data() -> Dict[str, Any]:
        """
        Generate sample sensitivity analysis results

        Returns:
            Dict[str, Any]: Sensitivity analysis data
        """
        discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        growth_rates = [0.01, 0.02, 0.025, 0.03, 0.04]

        # Generate value matrix
        valuations = []
        for discount_rate in discount_rates:
            row = []
            for growth_rate in growth_rates:
                # Simple mock valuation formula
                value = 1000 / (discount_rate - growth_rate) + np.random.normal(0, 50)
                row.append(max(value, 0))  # Ensure positive values
            valuations.append(row)

        return {
            'discount_rates': discount_rates,
            'terminal_growth_rates': growth_rates,
            'valuations': valuations,
            'current_price': 150.0,
            'upside_downside': [[(val / 150.0 - 1) for val in row] for row in valuations],
        }

    @staticmethod
    def generate_dates_metadata() -> Dict[str, Any]:
        """
        Generate sample dates metadata for testing

        Returns:
            Dict[str, Any]: Dates metadata
        """
        current_year = datetime.now().year

        return {
            'fy_years': list(range(current_year - 4, current_year + 1)),
            'ltm_year': current_year,
            'extraction_date': datetime.now().isoformat(),
            'period_end_dates': {
                'fy': [f'12/31/{year}' for year in range(current_year - 4, current_year + 1)],
                'ltm': [f'12/31/{current_year}'],
            },
        }

    @staticmethod
    def generate_validation_test_data() -> Dict[str, Any]:
        """
        Generate data for validation testing including edge cases

        Returns:
            Dict[str, Any]: Validation test data
        """
        return {
            'valid_data': {
                'revenue': [1000, 1100, 1200],
                'expenses': [-800, -850, -900],
                'net_income': [200, 250, 300],
            },
            'invalid_data': {
                'empty_values': [None, None, None],
                'mixed_types': ['text', 123, None],
                'zero_division': [0, 0, 0],
                'negative_unexpected': [-1000, -1100, -1200],
            },
            'edge_cases': {
                'very_large': [1e12, 1.1e12, 1.2e12],
                'very_small': [0.001, 0.002, 0.003],
                'infinity': [float('inf'), float('-inf'), float('nan')],
            },
        }
