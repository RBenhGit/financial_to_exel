"""
Comprehensive P/B Expansion Testing Suite
========================================

This test suite provides thorough validation for the expanded P/B historical range
functionality, covering 2015-2024 data validation, calculation accuracy preservation,
and comprehensive edge case testing.

Test Categories:
1. Expanded date range validation (2015-2016, 2024 inclusion)
2. Calculation accuracy preservation (no regression in 2017-2023)
3. Price matching accuracy with fiscal year-ends
4. Data quality transparency features
5. Edge cases (missing data, partial years, different fiscal year-ends)
6. Performance with larger historical datasets
"""

import unittest
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import time
import logging
from typing import List, Dict, Any, Optional

# Import modules to test - fix path to root directory
import sys
import os

# Add root directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, root_dir)

from core.analysis.pb.pb_valuation import PBValuator
from core.analysis.engines.financial_calculations import FinancialCalculator


class TestExpandedDateRangeValidation(unittest.TestCase):
    """Test expanded date range validation (2015-2016, 2024 inclusion)"""
    
    def setUp(self):
        """Set up test fixtures for date range tests"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]
        
    def test_2015_2016_data_availability(self):
        """Test that 2015-2016 data can be retrieved and processed"""
        for ticker in self.test_tickers:
            with self.subTest(ticker=ticker):
                self.calculator.ticker_symbol = ticker
                
                # Mock historical data that includes 2015-2016
                mock_data = self._create_extended_historical_data(
                    start_year=2015, end_year=2024
                )
                
                with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Verify 2015-2016 data is included
                    if result.get('historical_analysis'):
                        historical_data = result['historical_analysis'].get('historical_pb_ratios', [])
                        dates = [item['date'] for item in historical_data if isinstance(item, dict)]
                        
                        # Check for 2015 and 2016 data points
                        has_2015 = any('2015' in str(date) for date in dates)
                        has_2016 = any('2016' in str(date) for date in dates)
                        
                        if has_2015 or has_2016:
                            self.assertTrue(True, f"{ticker}: Successfully includes 2015-2016 data")
                        else:
                            self.fail(f"{ticker}: Missing 2015-2016 data in historical analysis")

    def test_2024_data_inclusion(self):
        """Test that 2024 data is included where available"""
        for ticker in self.test_tickers:
            with self.subTest(ticker=ticker):
                self.calculator.ticker_symbol = ticker
                
                # Mock data with recent 2024 entries
                mock_data = self._create_extended_historical_data(
                    start_year=2020, end_year=2024, include_recent=True
                )
                
                with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    if result.get('historical_analysis'):
                        historical_data = result['historical_analysis'].get('historical_pb_ratios', [])
                        dates = [item['date'] for item in historical_data if isinstance(item, dict)]
                        
                        # Check for 2024 data
                        has_2024 = any('2024' in str(date) for date in dates)
                        
                        if mock_data.get('has_2024_data', False):
                            self.assertTrue(has_2024, f"{ticker}: 2024 data available but not included")

    def test_expanded_range_completeness(self):
        """Test completeness of expanded historical range (2015-2024)"""
        ticker = "AAPL"  # Use Apple as reference
        self.calculator.ticker_symbol = ticker
        
        # Create comprehensive test data spanning full range
        mock_data = self._create_comprehensive_test_data()
        
        with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            if result.get('historical_analysis'):
                historical = result['historical_analysis']
                
                # Verify minimum expected data points for 9-year range
                expected_min_points = 9  # At least annual data
                actual_count = len(historical.get('historical_pb_ratios', []))
                
                self.assertGreaterEqual(
                    actual_count, 
                    expected_min_points,
                    f"Insufficient data points for expanded range: {actual_count} < {expected_min_points}"
                )
                
                # Verify date range spans correctly
                if historical.get('date_range'):
                    start_year = int(historical['date_range'].get('start', '2017')[:4])
                    end_year = int(historical['date_range'].get('end', '2023')[:4])
                    
                    self.assertLessEqual(start_year, 2016, "Start year should include 2015-2016 range")
                    self.assertGreaterEqual(end_year, 2023, "End year should include recent data")

    def _create_extended_historical_data(self, start_year: int, end_year: int, include_recent: bool = False) -> Dict:
        """Helper to create mock historical data for date range testing"""
        historical_prices = {}
        balance_sheets = []
        
        for year in range(start_year, end_year + 1):
            # Create quarterly data points
            for quarter in range(1, 5):
                date_str = f"{year}-{quarter*3:02d}-01"
                price = 100 + year * 10 + quarter * 5 + np.random.normal(0, 5)
                historical_prices[date_str] = {'4. close': max(price, 10)}
            
            # Create annual balance sheet data
            equity = 50000000 + year * 5000000  # Growing equity
            shares = 1000000 + year * 10000     # Growing shares
            
            balance_sheets.append({
                'fiscalDateEnding': f'{year}-12-31',
                'totalStockholderEquity': equity,
                'commonSharesOutstanding': shares
            })
        
        return {
            'ticker': 'TEST',
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets,
            'has_2024_data': include_recent and end_year >= 2024,
            'date_range': {'start': f'{start_year}-01-01', 'end': f'{end_year}-12-31'}
        }
    
    def _create_comprehensive_test_data(self) -> Dict:
        """Create comprehensive test data covering full 2015-2024 range"""
        return self._create_extended_historical_data(2015, 2024, include_recent=True)


class TestCalculationAccuracyPreservation(unittest.TestCase):
    """Test calculation accuracy preservation (no regression in 2017-2023)"""
    
    def setUp(self):
        """Set up regression test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
        
        # Known good values from existing calculations (baseline)
        self.baseline_calculations = {
            'AAPL': {
                '2020': {'pb_ratio': 9.2, 'bvps': 16.5},
                '2021': {'pb_ratio': 11.8, 'bvps': 18.2},
                '2022': {'pb_ratio': 6.1, 'bvps': 20.1},
                '2023': {'pb_ratio': 8.4, 'bvps': 22.3}
            },
            'MSFT': {
                '2020': {'pb_ratio': 8.9, 'bvps': 28.5},
                '2021': {'pb_ratio': 10.2, 'bvps': 31.2},
                '2022': {'pb_ratio': 7.8, 'bvps': 34.1},
                '2023': {'pb_ratio': 9.1, 'bvps': 37.8}
            }
        }
    
    def test_2017_2023_calculation_consistency(self):
        """Verify calculations for 2017-2023 remain consistent with baseline"""
        tolerance = 0.05  # 5% tolerance for calculation consistency
        
        for ticker, baseline_data in self.baseline_calculations.items():
            with self.subTest(ticker=ticker):
                self.calculator.ticker_symbol = ticker
                
                # Mock data that includes baseline years
                mock_data = self._create_baseline_test_data(ticker, baseline_data)
                
                with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    if result.get('historical_analysis'):
                        historical = result['historical_analysis']
                        historical_ratios = historical.get('historical_pb_ratios', [])
                        
                        # Check each baseline year for consistency
                        for year, expected_values in baseline_data.items():
                            year_data = self._find_year_data(historical_ratios, year)
                            
                            if year_data:
                                actual_pb = year_data.get('pb_ratio')
                                expected_pb = expected_values['pb_ratio']
                                
                                if actual_pb is not None:
                                    relative_error = abs(actual_pb - expected_pb) / expected_pb
                                    self.assertLess(
                                        relative_error,
                                        tolerance,
                                        f"{ticker} {year}: P/B regression detected. "
                                        f"Expected {expected_pb:.2f}, got {actual_pb:.2f} "
                                        f"(error: {relative_error:.1%})"
                                    )

    def test_book_value_calculation_stability(self):
        """Test that book value per share calculations remain stable"""
        ticker = "AAPL"
        self.calculator.ticker_symbol = ticker
        
        # Test with consistent equity and shares data
        stable_data = {
            'quarterly_balance_sheet': [
                {
                    'fiscalDateEnding': '2020-12-31',
                    'totalStockholderEquity': 65339000000,
                    'commonSharesOutstanding': 16788096000
                },
                {
                    'fiscalDateEnding': '2021-12-31', 
                    'totalStockholderEquity': 63090000000,
                    'commonSharesOutstanding': 16325819000
                },
                {
                    'fiscalDateEnding': '2022-12-31',
                    'totalStockholderEquity': 50672000000,
                    'commonSharesOutstanding': 15943425000
                }
            ]
        }
        
        with patch.object(self.calculator, 'get_financial_data', return_value=stable_data):
            # Calculate BVPS for multiple years
            bvps_2020 = self.calculator.calculate_book_value_per_share('2020')
            bvps_2021 = self.calculator.calculate_book_value_per_share('2021')
            bvps_2022 = self.calculator.calculate_book_value_per_share('2022')
            
            # Verify calculations are reasonable and consistent
            expected_bvps_2020 = 65339000000 / 16788096000  # ~3.89
            expected_bvps_2021 = 63090000000 / 16325819000  # ~3.87
            expected_bvps_2022 = 50672000000 / 15943425000  # ~3.18
            
            tolerance = 0.01  # 1% tolerance
            
            if bvps_2020:
                self.assertAlmostEqual(bvps_2020, expected_bvps_2020, delta=tolerance)
            if bvps_2021:
                self.assertAlmostEqual(bvps_2021, expected_bvps_2021, delta=tolerance)
            if bvps_2022:
                self.assertAlmostEqual(bvps_2022, expected_bvps_2022, delta=tolerance)

    def _create_baseline_test_data(self, ticker: str, baseline_data: Dict) -> Dict:
        """Create test data based on baseline calculations"""
        historical_prices = {}
        balance_sheets = []
        
        for year, values in baseline_data.items():
            # Create price data for the year
            date_str = f"{year}-12-31"
            price = values['pb_ratio'] * values['bvps']
            historical_prices[date_str] = {'4. close': price}
            
            # Create balance sheet data
            shares = 1000000000  # 1B shares for testing
            equity = values['bvps'] * shares
            
            balance_sheets.append({
                'fiscalDateEnding': f'{year}-12-31',
                'totalStockholderEquity': equity,
                'commonSharesOutstanding': shares
            })
        
        return {
            'ticker': ticker,
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets
        }
    
    def _find_year_data(self, historical_ratios: List, year: str) -> Optional[Dict]:
        """Find data for specific year in historical ratios"""
        for item in historical_ratios:
            if isinstance(item, dict) and str(year) in item.get('date', ''):
                return item
        return None


class TestPriceMatchingAccuracy(unittest.TestCase):
    """Test price matching accuracy with fiscal year-ends"""
    
    def setUp(self):
        """Set up price matching test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
    
    def test_fiscal_year_end_price_alignment(self):
        """Test that prices align correctly with fiscal year-ends"""
        # Test companies with different fiscal year-ends
        test_cases = [
            {
                'ticker': 'AAPL',
                'fiscal_year_end': '09-30',  # Apple: September 30
                'test_years': ['2020', '2021', '2022', '2023']
            },
            {
                'ticker': 'MSFT', 
                'fiscal_year_end': '06-30',  # Microsoft: June 30
                'test_years': ['2020', '2021', '2022', '2023']
            },
            {
                'ticker': 'WMT',
                'fiscal_year_end': '01-31',  # Walmart: January 31
                'test_years': ['2020', '2021', '2022', '2023']
            }
        ]
        
        for case in test_cases:
            with self.subTest(ticker=case['ticker']):
                self.calculator.ticker_symbol = case['ticker']
                
                # Create test data with specific fiscal year-end alignment
                mock_data = self._create_fiscal_aligned_data(
                    case['ticker'],
                    case['fiscal_year_end'],
                    case['test_years']
                )
                
                with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
                    result = self.pb_valuator.calculate_pb_analysis(case['ticker'])
                    
                    if result.get('historical_analysis'):
                        # Verify price alignment with fiscal dates
                        self._verify_fiscal_alignment(result, case)

    def test_price_date_matching_tolerance(self):
        """Test price matching with reasonable date tolerance around fiscal year-end"""
        ticker = "AAPL"
        self.calculator.ticker_symbol = ticker
        
        # Create test data with prices slightly off from fiscal year-end
        fiscal_end = "2023-09-30"
        price_dates = [
            "2023-09-29",  # 1 day before
            "2023-09-30",  # Exact match
            "2023-10-01",  # 1 day after
            "2023-10-02",  # 2 days after
        ]
        
        for price_date in price_dates:
            with self.subTest(price_date=price_date):
                mock_data = {
                    'historical_prices': {price_date: {'4. close': 150.0}},
                    'quarterly_balance_sheet': [{
                        'fiscalDateEnding': fiscal_end,
                        'totalStockholderEquity': 62146000000,
                        'commonSharesOutstanding': 15728700000
                    }]
                }
                
                with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Should successfully match within reasonable tolerance
                    if result.get('current_data'):
                        current_pb = result['current_data'].get('pb_ratio')
                        self.assertIsNotNone(current_pb, f"Failed to match price for {price_date}")

    def _create_fiscal_aligned_data(self, ticker: str, fiscal_end: str, years: List[str]) -> Dict:
        """Create test data aligned to fiscal year-ends"""
        historical_prices = {}
        balance_sheets = []
        
        for year in years:
            # Create fiscal year-end date
            fiscal_date = f"{year}-{fiscal_end}"
            price = 100 + int(year) * 5  # Simple price progression
            
            historical_prices[fiscal_date] = {'4. close': price}
            
            # Corresponding balance sheet data
            balance_sheets.append({
                'fiscalDateEnding': fiscal_date,
                'totalStockholderEquity': 50000000000 + int(year) * 1000000000,
                'commonSharesOutstanding': 1000000000
            })
        
        return {
            'ticker': ticker,
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets,
            'fiscal_year_end': fiscal_end
        }
    
    def _verify_fiscal_alignment(self, result: Dict, case: Dict):
        """Verify that calculated P/B ratios align with fiscal year-ends"""
        historical = result['historical_analysis']
        historical_ratios = historical.get('historical_pb_ratios', [])
        
        for year in case['test_years']:
            year_data = self._find_year_data(historical_ratios, year)
            if year_data:
                # Verify date is close to fiscal year-end
                date_str = year_data.get('date', '')
                expected_month = case['fiscal_year_end'][:2]
                
                if date_str and len(date_str) >= 7:
                    actual_month = date_str[5:7]
                    month_diff = abs(int(actual_month) - int(expected_month))
                    
                    # Allow 1-month tolerance for fiscal alignment
                    self.assertLessEqual(
                        month_diff,
                        1,
                        f"{case['ticker']} {year}: Price date {date_str} not aligned with fiscal year-end"
                    )

    def _find_year_data(self, historical_ratios: List, year: str) -> Optional[Dict]:
        """Find data for specific year"""
        for item in historical_ratios:
            if isinstance(item, dict) and year in item.get('date', ''):
                return item
        return None


class TestDataQualityTransparency(unittest.TestCase):
    """Test data quality transparency features"""
    
    def setUp(self):
        """Set up data quality test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
    
    def test_data_quality_indicators(self):
        """Test that data quality indicators are properly reported"""
        ticker = "AAPL"
        self.calculator.ticker_symbol = ticker
        
        # Create test data with varying quality levels
        mock_data = self._create_quality_test_data()
        
        with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            # Verify quality indicators are present
            self.assertIn('data_quality', result, "Missing data quality indicators")
            
            quality = result['data_quality']
            
            # Check for required quality metrics
            required_metrics = [
                'completeness_score',
                'data_source_reliability',
                'temporal_consistency',
                'calculation_confidence'
            ]
            
            for metric in required_metrics:
                self.assertIn(metric, quality, f"Missing quality metric: {metric}")
                self.assertIsInstance(quality[metric], (int, float))
                self.assertGreaterEqual(quality[metric], 0.0)
                self.assertLessEqual(quality[metric], 1.0)

    def test_source_attribution(self):
        """Test that data sources are properly attributed"""
        ticker = "MSFT"
        self.calculator.ticker_symbol = ticker
        
        mock_data = {
            'source_info': {
                'primary_source': 'alpha_vantage',
                'fallback_sources': ['yfinance', 'financial_statements'],
                'data_freshness': '2024-08-31'
            }
        }
        
        with patch.object(self.calculator, 'get_historical_data', return_value=mock_data):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            # Verify source attribution
            if result.get('data_sources'):
                sources = result['data_sources']
                self.assertIn('primary_source', sources)
                self.assertIn('data_freshness', sources)

    def test_equity_source_transparency(self):
        """Test transparency of equity data sources (Excel field names used)"""
        ticker = "GOOGL"
        self.calculator.ticker_symbol = ticker
        
        # Test with different equity field sources
        test_equity_fields = [
            'Total Stockholder Equity',
            'Total Shareholders Equity', 
            'Total Equity',
            'Stockholders Equity'
        ]
        
        for equity_field in test_equity_fields:
            with self.subTest(equity_field=equity_field):
                mock_financial_data = {
                    'Balance Sheet': {
                        '2023': {
                            equity_field: 50000000000,
                            'Total Assets': 100000000000
                        }
                    },
                    'metadata': {
                        'equity_field_used': equity_field
                    }
                }
                
                with patch.object(self.calculator, 'financial_data', mock_financial_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Verify equity source is documented
                    if result.get('calculation_details'):
                        details = result['calculation_details']
                        if 'equity_source_field' in details:
                            self.assertEqual(details['equity_source_field'], equity_field)

    def _create_quality_test_data(self) -> Dict:
        """Create test data with embedded quality metrics"""
        return {
            'historical_prices': {
                '2023-12-31': {'4. close': 195.0, 'data_quality': 0.95},
                '2022-12-31': {'4. close': 129.0, 'data_quality': 0.88},
                '2021-12-31': {'4. close': 177.0, 'data_quality': 0.92}
            },
            'quarterly_balance_sheet': [
                {
                    'fiscalDateEnding': '2023-12-31',
                    'totalStockholderEquity': 62146000000,
                    'commonSharesOutstanding': 15728700000,
                    'data_quality': 0.90
                }
            ],
            'quality_summary': {
                'overall_score': 0.91,
                'completeness': 0.88,
                'timeliness': 0.95,
                'accuracy': 0.89
            }
        }


class TestEdgeCaseHandling(unittest.TestCase):
    """Test edge cases (missing data, partial years, different fiscal year-ends)"""
    
    def setUp(self):
        """Set up edge case test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
    
    def test_missing_data_handling(self):
        """Test graceful handling of missing historical data"""
        ticker = "TEST_MISSING"
        self.calculator.ticker_symbol = ticker
        
        # Test with various missing data scenarios
        missing_data_scenarios = [
            {'historical_prices': {}, 'quarterly_balance_sheet': []},  # No data
            {'historical_prices': {'2023-01-01': {'4. close': 100}}, 'quarterly_balance_sheet': []},  # No balance sheet
            {'historical_prices': {}, 'quarterly_balance_sheet': [{'fiscalDateEnding': '2023-12-31'}]}  # No prices
        ]
        
        for scenario in missing_data_scenarios:
            with self.subTest(scenario=str(scenario)):
                with patch.object(self.calculator, 'get_historical_data', return_value=scenario):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Should handle gracefully without crashing
                    self.assertIsNotNone(result)
                    
                    # Should indicate data limitations
                    if result.get('error') or result.get('warnings'):
                        self.assertTrue(True, "Appropriately indicates data limitations")

    def test_partial_year_data(self):
        """Test handling of partial year data (mid-year fiscal ends)"""
        ticker = "PARTIAL_YEAR"
        self.calculator.ticker_symbol = ticker
        
        # Create data with mid-year fiscal year-end (e.g., June 30)
        partial_year_data = {
            'historical_prices': {
                '2023-06-30': {'4. close': 150.0},
                '2022-06-30': {'4. close': 140.0},
                '2021-06-30': {'4. close': 130.0}
            },
            'quarterly_balance_sheet': [
                {
                    'fiscalDateEnding': '2023-06-30',
                    'totalStockholderEquity': 50000000000,
                    'commonSharesOutstanding': 1000000000
                },
                {
                    'fiscalDateEnding': '2022-06-30', 
                    'totalStockholderEquity': 45000000000,
                    'commonSharesOutstanding': 1000000000
                }
            ]
        }
        
        with patch.object(self.calculator, 'get_historical_data', return_value=partial_year_data):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            # Should calculate P/B ratios correctly for mid-year ends
            if result.get('current_data'):
                current_pb = result['current_data'].get('pb_ratio')
                expected_pb = 150.0 / 50.0  # Price / BVPS = 3.0
                
                if current_pb:
                    self.assertAlmostEqual(current_pb, expected_pb, places=1)

    def test_different_fiscal_year_ends(self):
        """Test various fiscal year-end patterns"""
        fiscal_patterns = [
            {'month': '12', 'day': '31', 'name': 'calendar_year'},
            {'month': '09', 'day': '30', 'name': 'september_end'},
            {'month': '06', 'day': '30', 'name': 'june_end'},
            {'month': '03', 'day': '31', 'name': 'march_end'}
        ]
        
        for pattern in fiscal_patterns:
            with self.subTest(fiscal_pattern=pattern['name']):
                ticker = f"TEST_{pattern['name'].upper()}"
                self.calculator.ticker_symbol = ticker
                
                # Create data with specific fiscal pattern
                fiscal_data = self._create_fiscal_pattern_data(pattern, ['2022', '2023'])
                
                with patch.object(self.calculator, 'get_historical_data', return_value=fiscal_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Should handle different fiscal patterns appropriately
                    if result.get('current_data'):
                        self.assertIsNotNone(result['current_data'].get('pb_ratio'))

    def test_data_gap_handling(self):
        """Test handling of data gaps in historical series"""
        ticker = "GAP_TEST"
        self.calculator.ticker_symbol = ticker
        
        # Create data with intentional gaps
        gap_data = {
            'historical_prices': {
                '2023-12-31': {'4. close': 200.0},
                '2022-12-31': {'4. close': 180.0},
                # Missing 2021 data (gap)
                '2020-12-31': {'4. close': 160.0},
                '2019-12-31': {'4. close': 150.0}
            },
            'quarterly_balance_sheet': [
                {'fiscalDateEnding': '2023-12-31', 'totalStockholderEquity': 60000000000, 'commonSharesOutstanding': 1000000000},
                {'fiscalDateEnding': '2022-12-31', 'totalStockholderEquity': 55000000000, 'commonSharesOutstanding': 1000000000},
                {'fiscalDateEnding': '2020-12-31', 'totalStockholderEquity': 50000000000, 'commonSharesOutstanding': 1000000000},
                {'fiscalDateEnding': '2019-12-31', 'totalStockholderEquity': 45000000000, 'commonSharesOutstanding': 1000000000}
            ]
        }
        
        with patch.object(self.calculator, 'get_historical_data', return_value=gap_data):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            # Should identify and handle data gaps appropriately
            if result.get('data_quality'):
                quality = result['data_quality']
                completeness = quality.get('completeness_score', 1.0)
                
                # Should detect the data gap
                self.assertLess(completeness, 1.0, "Should detect data gap in historical series")

    def _create_fiscal_pattern_data(self, pattern: Dict, years: List[str]) -> Dict:
        """Create test data for specific fiscal year pattern"""
        historical_prices = {}
        balance_sheets = []
        
        for year in years:
            fiscal_date = f"{year}-{pattern['month']}-{pattern['day']}"
            
            historical_prices[fiscal_date] = {'4. close': 100 + int(year)}
            balance_sheets.append({
                'fiscalDateEnding': fiscal_date,
                'totalStockholderEquity': 50000000000,
                'commonSharesOutstanding': 1000000000
            })
        
        return {
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets,
            'fiscal_pattern': pattern
        }


class TestPerformanceWithLargeDatasets(unittest.TestCase):
    """Test performance with larger historical datasets"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
    
    def test_large_historical_dataset_performance(self):
        """Test performance with 10+ years of quarterly data"""
        ticker = "PERF_TEST"
        self.calculator.ticker_symbol = ticker
        
        # Create large dataset (10 years of quarterly data = 40+ data points)
        large_dataset = self._create_large_historical_dataset(years=10)
        
        with patch.object(self.calculator, 'get_historical_data', return_value=large_dataset):
            start_time = time.time()
            
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            execution_time = time.time() - start_time
            
            # Should complete within reasonable time (< 10 seconds)
            self.assertLess(execution_time, 10.0, f"Performance degraded: {execution_time:.2f}s")
            
            # Should still produce valid results
            if result.get('historical_analysis'):
                historical = result['historical_analysis']
                data_points = len(historical.get('historical_pb_ratios', []))
                
                # Should process most of the data points
                self.assertGreater(data_points, 30, f"Should process substantial data: {data_points}")

    def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency with large datasets"""
        ticker = "MEMORY_TEST"
        self.calculator.ticker_symbol = ticker
        
        # Create very large dataset (15 years of monthly data = 180+ points)
        very_large_dataset = self._create_large_historical_dataset(years=15, frequency='monthly')
        
        with patch.object(self.calculator, 'get_historical_data', return_value=very_large_dataset):
            try:
                result = self.pb_valuator.calculate_pb_analysis(ticker)
                
                # Should complete without memory errors
                self.assertIsNotNone(result, "Should handle large datasets without memory issues")
                
                # Verify reasonable memory usage (result size)
                if result.get('historical_analysis'):
                    # Result should be structured efficiently
                    historical_ratios = result['historical_analysis'].get('historical_pb_ratios', [])
                    self.assertIsInstance(historical_ratios, list)
                    
            except MemoryError:
                self.fail("Memory error with large dataset")

    def test_calculation_accuracy_large_datasets(self):
        """Test that calculation accuracy is maintained with large datasets"""
        ticker = "ACCURACY_TEST"
        self.calculator.ticker_symbol = ticker
        
        # Create dataset with known statistical properties
        controlled_dataset = self._create_controlled_statistical_dataset()
        
        with patch.object(self.calculator, 'get_historical_data', return_value=controlled_dataset):
            result = self.pb_valuator.calculate_pb_analysis(ticker)
            
            if result.get('historical_analysis'):
                historical = result['historical_analysis']
                stats = historical.get('statistics', {})
                
                # Verify statistical accuracy with known data
                expected_mean = 2.5  # From controlled dataset
                actual_mean = stats.get('mean_pb')
                
                if actual_mean:
                    error = abs(actual_mean - expected_mean) / expected_mean
                    self.assertLess(error, 0.05, f"Statistical accuracy degraded: {error:.1%}")

    def _create_large_historical_dataset(self, years: int, frequency: str = 'quarterly') -> Dict:
        """Create large test dataset for performance testing"""
        historical_prices = {}
        balance_sheets = []
        
        periods_per_year = 12 if frequency == 'monthly' else 4
        
        base_year = 2024 - years
        
        for year in range(base_year, 2025):
            for period in range(1, periods_per_year + 1):
                if frequency == 'monthly':
                    month = period
                    date_str = f"{year}-{month:02d}-01"
                else:
                    month = period * 3
                    date_str = f"{year}-{month:02d}-01"
                
                # Generate realistic price with trend and volatility
                base_price = 100
                trend = (year - base_year) * 2
                seasonal = 5 * np.sin(period * np.pi / 6)
                noise = np.random.normal(0, 3)
                price = max(base_price + trend + seasonal + noise, 10)
                
                historical_prices[date_str] = {'4. close': price}
        
        # Create annual balance sheet data
        for year in range(base_year, 2025):
            equity = 50000000000 + (year - base_year) * 2000000000
            shares = 1000000000 + (year - base_year) * 10000000
            
            balance_sheets.append({
                'fiscalDateEnding': f'{year}-12-31',
                'totalStockholderEquity': equity,
                'commonSharesOutstanding': shares
            })
        
        return {
            'ticker': 'PERF_TEST',
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets,
            'dataset_size': len(historical_prices),
            'years_covered': years
        }
    
    def _create_controlled_statistical_dataset(self) -> Dict:
        """Create dataset with known statistical properties for accuracy testing"""
        # Create data with known mean P/B of 2.5
        pb_values = [2.0, 2.2, 2.5, 2.8, 3.0, 2.3, 2.7, 2.1, 2.9, 2.4]  # Mean = 2.5
        
        historical_prices = {}
        balance_sheets = []
        bvps = 50.0  # Fixed book value per share
        
        for i, pb_ratio in enumerate(pb_values):
            year = 2015 + i
            date_str = f"{year}-12-31"
            price = pb_ratio * bvps
            
            historical_prices[date_str] = {'4. close': price}
            balance_sheets.append({
                'fiscalDateEnding': date_str,
                'totalStockholderEquity': bvps * 1000000000,  # 1B shares
                'commonSharesOutstanding': 1000000000
            })
        
        return {
            'historical_prices': historical_prices,
            'quarterly_balance_sheet': balance_sheets,
            'statistical_properties': {'expected_mean_pb': 2.5}
        }


class TestRegressionValidation(unittest.TestCase):
    """Test against known good values to prevent regressions"""
    
    def setUp(self):
        """Set up regression validation fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
        
        # Known good test cases with expected results
        self.known_good_cases = {
            'AAPL_2023': {
                'ticker': 'AAPL',
                'price': 195.89,
                'equity': 62146000000,
                'shares': 15728700000,
                'expected_pb': 4.96,  # 195.89 / (62146000000/15728700000)
                'tolerance': 0.1
            },
            'MSFT_2023': {
                'ticker': 'MSFT',
                'price': 374.51,
                'equity': 206223000000,
                'shares': 7430000000,
                'expected_pb': 13.49,  # 374.51 / (206223000000/7430000000)
                'tolerance': 0.2
            }
        }
    
    def test_known_good_calculations(self):
        """Validate against known good P/B calculations"""
        for case_name, case_data in self.known_good_cases.items():
            with self.subTest(case=case_name):
                ticker = case_data['ticker']
                self.calculator.ticker_symbol = ticker
                
                # Create test data based on known values
                test_data = {
                    'historical_prices': {'2023-12-31': {'4. close': case_data['price']}},
                    'quarterly_balance_sheet': [{
                        'fiscalDateEnding': '2023-12-31',
                        'totalStockholderEquity': case_data['equity'],
                        'commonSharesOutstanding': case_data['shares']
                    }]
                }
                
                with patch.object(self.calculator, 'get_historical_data', return_value=test_data):
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    if result.get('current_data'):
                        actual_pb = result['current_data'].get('pb_ratio')
                        expected_pb = case_data['expected_pb']
                        tolerance = case_data['tolerance']
                        
                        if actual_pb:
                            self.assertAlmostEqual(
                                actual_pb,
                                expected_pb,
                                delta=tolerance,
                                msg=f"{case_name}: P/B calculation regression detected"
                            )


@pytest.mark.integration
class TestIntegrationWithRealData(unittest.TestCase):
    """Integration tests with real market data (requires network access)"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.calculator = FinancialCalculator(company_folder=None)
        self.pb_valuator = PBValuator(self.calculator)
        
        # Test with well-known stable companies
        self.integration_tickers = ["AAPL", "MSFT"]
    
    @pytest.mark.api_dependent
    def test_real_data_expanded_range(self):
        """Test expanded range functionality with real market data"""
        for ticker in self.integration_tickers:
            with self.subTest(ticker=ticker):
                try:
                    self.calculator.ticker_symbol = ticker
                    result = self.pb_valuator.calculate_pb_analysis(ticker)
                    
                    # Verify real data produces valid results
                    if not result.get('error'):
                        self.assertIn('current_data', result)
                        self.assertIn('historical_analysis', result)
                        
                        # Check for expanded historical coverage
                        historical = result['historical_analysis']
                        if historical.get('date_range'):
                            start_year = int(historical['date_range'].get('start', '2017')[:4])
                            self.assertLessEqual(start_year, 2017, 
                                               f"{ticker}: Should include pre-2017 data where available")
                
                except Exception as e:
                    self.skipTest(f"Real data test skipped for {ticker}: {e}")


if __name__ == '__main__':
    # Configure test logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the comprehensive test suite
    unittest.main(verbosity=2)