"""
Optimized test datasets for performance testing.
Contains small, focused datasets for efficient testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class PerformanceTestDatasets:
    """Factory for creating optimized test datasets."""
    
    @staticmethod
    def create_minimal_financials():
        """Create minimal financial data for performance testing."""
        dates = pd.date_range('2023-01-01', periods=3, freq='Y')
        
        return {
            'income_statement': pd.DataFrame({
                'Date': dates,
                'Revenue': [1000, 1100, 1210],
                'Operating Income': [200, 220, 242],
                'Net Income': [150, 165, 182],
                'EBITDA': [250, 275, 303]
            }),
            'balance_sheet': pd.DataFrame({
                'Date': dates, 
                'Total Assets': [5000, 5500, 6050],
                'Total Debt': [2000, 2100, 2205],
                'Shareholders Equity': [2500, 2750, 3025],
                'Current Assets': [1500, 1650, 1815],
                'Current Liabilities': [500, 550, 605]
            }),
            'cash_flow': pd.DataFrame({
                'Date': dates,
                'Operating Cash Flow': [200, 220, 242],
                'Capital Expenditures': [-50, -55, -61],
                'Free Cash Flow': [150, 165, 181],
                'Cash and Cash Equivalents': [300, 330, 363]
            })
        }
    
    @staticmethod
    def create_market_data():
        """Create minimal market data for testing."""
        return {
            'ticker': 'TEST',
            'company_name': 'Test Company Inc.',
            'current_price': 150.0,
            'market_cap': 150000000,
            'shares_outstanding': 1000000,
            'beta': 1.2,
            'pe_ratio': 15.0,
            'pb_ratio': 2.5,
            'dividend_yield': 0.02,
            'last_updated': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_valuation_inputs():
        """Create minimal valuation inputs."""
        return {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'projection_years': 5,
            'fcf_projections': [100, 110, 121, 133, 146],
            'revenue_growth_rates': [0.10, 0.10, 0.10, 0.10],
            'margin_assumptions': {
                'gross_margin': 0.40,
                'operating_margin': 0.20,
                'tax_rate': 0.25
            }
        }
    
    @staticmethod
    def create_historical_data():
        """Create minimal historical data."""
        return {
            'prices': pd.DataFrame({
                'Date': pd.date_range('2023-01-01', periods=12, freq='M'),
                'Close': np.random.normal(150, 10, 12).clip(100, 200)
            }),
            'returns': [0.05, -0.02, 0.03, 0.01, -0.01, 0.04, 
                       0.02, -0.03, 0.06, -0.01, 0.02, 0.03],
            'volatility': 0.25
        }
    
    @staticmethod
    def create_benchmark_data():
        """Create benchmark data for performance testing."""
        return {
            'sp500_returns': [0.04, -0.01, 0.02, 0.00, 0.01, 0.03,
                             0.01, -0.02, 0.05, 0.00, 0.01, 0.02],
            'risk_free_rate': 0.03,
            'market_risk_premium': 0.06
        }


def create_sample_excel_data():
    """Create sample Excel-like data structure for mocking."""
    datasets = PerformanceTestDatasets()
    financials = datasets.create_minimal_financials()
    
    # Simulate Excel worksheet structure
    excel_data = {}
    
    for sheet_name, df in financials.items():
        # Convert to Excel-like format (rows and columns)
        excel_data[sheet_name] = {
            'max_row': len(df) + 1,  # +1 for header
            'max_column': len(df.columns),
            'values': [df.columns.tolist()] + df.values.tolist()
        }
    
    return excel_data


def create_api_response_mock():
    """Create realistic API response mock data."""
    datasets = PerformanceTestDatasets()
    market_data = datasets.create_market_data()
    
    return {
        'yfinance': {
            'info': market_data,
            'history': datasets.create_historical_data()['prices'],
            'financials': datasets.create_minimal_financials()['income_statement'],
            'balance_sheet': datasets.create_minimal_financials()['balance_sheet'],
            'cashflow': datasets.create_minimal_financials()['cash_flow']
        },
        'alpha_vantage': {
            'symbol': market_data['ticker'],
            'price': market_data['current_price'],
            'change': '+2.50',
            'change_percent': '+1.69%',
            'volume': 1000000
        },
        'fmp': {
            'symbol': market_data['ticker'],
            'price': market_data['current_price'],
            'marketCap': market_data['market_cap'],
            'pe': market_data['pe_ratio'],
            'beta': market_data['beta']
        }
    }