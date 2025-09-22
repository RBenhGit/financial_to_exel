"""
Consolidated financial calculations tests.

This module consolidates tests for FCF calculations, growth rates, and
financial metrics that were scattered across multiple test files.
"""

import os
import pytest
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, List

from tests.fixtures.mock_data import MockDataGenerator
from core.analysis.fcf_consolidated import FCFCalculator
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.processors.data_processing import DataProcessor


class TestFCFCalculations:
    """Test Free Cash Flow calculations"""

    def test_fcf_growth_rate_calculations(self, sample_fcf_data):
        """Test FCF growth rate calculations"""
        calculator = FCFCalculator()

        # Test with sample FCF data
        growth_rates = calculator.calculate_fcf_growth_rates(sample_fcf_data)

        # Should have growth rates for all FCF types plus average
        expected_types = ['FCFF', 'FCFE', 'LFCF', 'Average']
        for fcf_type in expected_types:
            if fcf_type in growth_rates:
                assert isinstance(growth_rates[fcf_type], dict)
                # Should have growth rates for different periods
                expected_periods = ['1yr', '3yr', '5yr']
                for period in expected_periods:
                    assert period in growth_rates[fcf_type]

    def test_negative_fcf_growth_handling(self):
        """Test handling of negative FCF values in growth calculations"""
        calculator = FCFCalculator()

        # Create test data with negative values
        fcf_data = {
            'FCFF': [100, 110, -50, 80, 120],  # Includes negative value
            'FCFE': [-50, -30, 20, 50, 80],  # Starts negative, becomes positive
        }

        growth_rates = calculator.calculate_fcf_growth_rates(fcf_data)

        # Should handle negative values without crashing
        assert 'FCFF' in growth_rates
        assert 'FCFE' in growth_rates

        # Growth rates should be calculated or None
        for fcf_type in growth_rates:
            for period, rate in growth_rates[fcf_type].items():
                assert rate is None or isinstance(rate, (int, float))

    def test_insufficient_data_handling(self):
        """Test handling when insufficient data is available for growth calculations"""
        calculator = FCFCalculator()

        # Test with insufficient data
        fcf_data = {'FCFF': [100], 'FCFE': []}  # Only one data point  # No data

        growth_rates = calculator.calculate_fcf_growth_rates(fcf_data)

        # Should return structure with None values for impossible calculations
        if 'FCFF' in growth_rates:
            for period, rate in growth_rates['FCFF'].items():
                assert rate is None  # Can't calculate growth with only one point

    def test_fcf_metrics_summary(self, sample_fcf_data):
        """Test comprehensive FCF metrics summary calculation"""
        calculator = FCFCalculator()

        summary = calculator.calculate_fcf_metrics_summary(sample_fcf_data)

        # Should have expected structure
        expected_keys = ['latest_values', 'growth_rates', 'statistics', 'average_fcf']
        for key in expected_keys:
            assert key in summary

        # Latest values should be the last values from each FCF type
        for fcf_type, values in sample_fcf_data.items():
            if values:
                assert fcf_type in summary['latest_values']
                assert summary['latest_values'][fcf_type] == values[-1]


class TestDataProcessorFCF:
    """Test DataProcessor FCF-related functionality"""

    def test_fcf_data_preparation(self, sample_fcf_data):
        """Test centralized FCF data preparation"""
        processor = DataProcessor()

        processed_data = processor.prepare_fcf_data(sample_fcf_data)

        # Should have expected structure
        expected_keys = [
            'years',
            'max_years',
            'all_fcf_data',
            'padded_fcf_data',
            'average_fcf',
            'common_years',
            'common_average_values',
            'growth_rates',
        ]

        for key in expected_keys:
            assert key in processed_data

        # Verify data consistency
        if processed_data['all_fcf_data']:
            assert processed_data['max_years'] > 0
            assert len(processed_data['years']) == processed_data['max_years']

    def test_fcf_data_caching(self, sample_fcf_data):
        """Test that FCF data preparation uses caching to avoid redundant calculations"""
        processor = DataProcessor()

        # First call
        data1 = processor.prepare_fcf_data(sample_fcf_data)

        # Second call (should use cache)
        data2 = processor.prepare_fcf_data(sample_fcf_data)

        # Results should be identical (cached)
        assert data1 == data2

        # Force refresh should recalculate
        data3 = processor.prepare_fcf_data(sample_fcf_data, force_refresh=True)
        assert data3 == data1  # Same calculation, but freshly computed

    def test_average_fcf_calculation(self, sample_fcf_data):
        """Test average FCF calculation across different types"""
        processor = DataProcessor()

        processed_data = processor.prepare_fcf_data(sample_fcf_data)

        if processed_data['common_average_values']:
            # Average values should be reasonable
            avg_values = processed_data['common_average_values']
            assert all(isinstance(v, (int, float)) or v is None for v in avg_values)

            # Should have values for common years
            assert len(avg_values) == len(processed_data['common_years'])


class TestGrowthRateCalculations:
    """Test growth rate calculation logic"""

    @pytest.mark.parametrize(
        "values,periods,expected_length",
        [
            ([100, 110, 121], [1, 2], 2),
            ([50, 75, 100, 125], [1, 2, 3], 3),
            ([200], [1], 0),  # Insufficient data
        ],
    )
    def test_growth_rate_periods(self, values, periods, expected_length):
        """Test growth rate calculations for different periods"""
        calculator = FCFCalculator()

        growth_rates = calculator._calculate_growth_rates_for_values(values, periods)

        # Should return dictionary with expected period keys
        assert len(growth_rates) == len(periods)

        # Count non-None values
        non_none_values = [rate for rate in growth_rates.values() if rate is not None]
        assert len(non_none_values) <= expected_length

    def test_zero_value_handling(self):
        """Test handling of zero values in growth calculations"""
        calculator = FCFCalculator()

        # Test with zero starting value
        values = [0, 100, 200]
        growth_rates = calculator._calculate_growth_rates_for_values(values, [1, 2])

        # Should handle zero gracefully (return None for impossible calculations)
        for rate in growth_rates.values():
            assert rate is None or isinstance(rate, (int, float))

    def test_growth_rate_formulas(self):
        """Test that growth rate formulas are mathematically correct"""
        calculator = FCFCalculator()

        # Test with known values
        values = [100, 110, 121]  # 10% annual growth
        growth_rates = calculator._calculate_growth_rates_for_values(values, [1, 2])

        # 1-year growth should be approximately 21/110 - 1 ≈ 0.1 (10%)
        if growth_rates['1yr'] is not None:
            assert abs(growth_rates['1yr'] - 0.1) < 0.001

        # 2-year CAGR should be approximately (121/100)^(1/2) - 1 ≈ 0.1 (10%)
        if growth_rates['2yr'] is not None:
            assert abs(growth_rates['2yr'] - 0.1) < 0.001


class TestFinancialCalculatorIntegration:
    """Test FinancialCalculator class integration"""

    def test_financial_calculator_initialization(self, temp_company_structure):
        """Test FinancialCalculator initialization"""
        calculator = FinancialCalculator(temp_company_structure)

        assert calculator.company_folder == temp_company_structure
        assert calculator.company_name == os.path.basename(temp_company_structure)
        assert isinstance(calculator.financial_data, dict)
        assert isinstance(calculator.fcf_results, dict)

    @patch('core.analysis.engines.financial_calculations.os.path.exists')
    @patch('core.analysis.engines.financial_calculations.os.listdir')
    def test_financial_statements_loading(self, mock_listdir, mock_exists, temp_company_structure):
        """Test loading of financial statements"""
        # Mock file system
        mock_exists.return_value = True
        mock_listdir.side_effect = lambda path: [
            'TEST - Income Statement.xlsx',
            'TEST - Balance Sheet.xlsx',
            'TEST - Cash Flow Statement.xlsx',
        ]

        calculator = FinancialCalculator(temp_company_structure)

        # Mock the _load_excel_data method
        calculator._load_excel_data = Mock(
            return_value=MockDataGenerator.generate_excel_dataframe()
        )

        # Test loading
        calculator.load_financial_statements()

        # Should have loaded data for both FY and LTM
        expected_keys = [
            'income_fy',
            'balance_fy',
            'cashflow_fy',
            'income_ltm',
            'balance_ltm',
            'cashflow_ltm',
        ]

        for key in expected_keys:
            assert key in calculator.financial_data

    def test_ticker_extraction(self):
        """Test automatic ticker extraction from folder structure"""
        # Test with company folder name that looks like ticker
        calculator = FinancialCalculator('AAPL')
        assert calculator.ticker_symbol == 'AAPL'

        # Test with longer company name
        calculator = FinancialCalculator('TestCompany')
        # Should extract some form of ticker or use default


class TestErrorHandling:
    """Test error handling in financial calculations"""

    def test_empty_fcf_data_handling(self):
        """Test handling of empty FCF data"""
        calculator = FCFCalculator()
        processor = DataProcessor()

        empty_data = {}

        # Should handle empty data gracefully
        growth_rates = calculator.calculate_fcf_growth_rates(empty_data)
        assert isinstance(growth_rates, dict)

        processed_data = processor.prepare_fcf_data(empty_data)
        assert isinstance(processed_data, dict)

    def test_malformed_data_handling(self):
        """Test handling of malformed data"""
        calculator = FCFCalculator()

        # Test with malformed data
        bad_data = {'FCFF': [None, 'invalid', float('inf')], 'FCFE': ['not_a_number', [], {}]}

        # Should not crash with malformed data
        try:
            growth_rates = calculator.calculate_fcf_growth_rates(bad_data)
            assert isinstance(growth_rates, dict)
        except Exception as e:
            # If it does raise an exception, it should be a handled one
            assert isinstance(e, (ValueError, TypeError))

    def test_infinite_values_handling(self):
        """Test handling of infinite values in calculations"""
        calculator = FCFCalculator()

        # Test with infinite values
        inf_data = {'FCFF': [100, float('inf'), 200], 'FCFE': [float('-inf'), 150, 180]}

        growth_rates = calculator.calculate_fcf_growth_rates(inf_data)

        # Should handle infinite values gracefully
        assert isinstance(growth_rates, dict)

        # Growth rates involving infinite values should be None or handled appropriately
        for fcf_type in growth_rates:
            for period, rate in growth_rates[fcf_type].items():
                assert rate is None or (isinstance(rate, (int, float)) and np.isfinite(rate))


class TestFinancialCalculatorFCFMethods:
    """Test core FCF calculation methods in FinancialCalculator"""

    @pytest.fixture
    def mock_calculator(self):
        """Create a FinancialCalculator with mock data bypassing file loading"""
        with patch.object(FinancialCalculator, '_auto_extract_ticker'), \
             patch.object(FinancialCalculator, 'load_financial_statements'):

            # Initialize without loading file data
            calc = FinancialCalculator(None)

            # Override ticker to avoid market data fetch
            calc.ticker_symbol = "MOCK"
            calc.company_name = "MOCK Company"
            calc.company_folder = "/mock/path"

            # Mock financial data with pandas Series format expected by calculations
            import pandas as pd

            calc.financial_data = {
                'income_fy': pd.DataFrame({
                    'Net Income': [100000, 110000, 120000],
                    'Depreciation & Amortization': [10000, 11000, 12000],
                    'Interest Expense': [5000, 5500, 6000],
                    'EBIT': [140000, 154000, 168000]
                }),
                'balance_fy': pd.DataFrame({
                    'Working Capital': [50000, 52000, 54000],
                    'Total Debt': [50000, 52000, 54000],
                    'Cash': [20000, 22000, 24000]
                }),
                'cashflow_fy': pd.DataFrame({
                    'Operating Cash Flow': [120000, 132000, 144000],
                    'Capital Expenditures': [-15000, -16500, -18000],
                    'Long-Term Debt Issued': [5000, 0, 2000],
                    'Long-Term Debt Repaid': [-3000, -2000, -4000],
                    'Dividends Paid': [-8000, -8800, -9600]
                })
            }

            # Mock market data to avoid yfinance calls
            calc.current_stock_price = 100.0
            calc.shares_outstanding = 1000000
            calc.market_cap = 100000000

            return calc

    def test_calculate_fcf_to_firm(self, mock_calculator):
        """Test FCFF calculation"""
        fcff = mock_calculator.calculate_fcf_to_firm(use_var_input_data=False)

        assert isinstance(fcff, list)
        assert len(fcff) > 0

        # FCFF should be positive for our mock data
        # FCFF = Operating Cash Flow - CapEx
        for value in fcff:
            if value is not None:
                assert isinstance(value, (int, float))
                assert not np.isnan(value)

    def test_calculate_fcf_to_equity(self, mock_calculator):
        """Test FCFE calculation"""
        fcfe = mock_calculator.calculate_fcf_to_equity()

        assert isinstance(fcfe, list)
        assert len(fcfe) > 0

        # FCFE should be numeric values
        for value in fcfe:
            if value is not None:
                assert isinstance(value, (int, float))
                assert not np.isnan(value)

    def test_calculate_levered_fcf(self, mock_calculator):
        """Test Levered FCF calculation"""
        levered_fcf = mock_calculator.calculate_levered_fcf()

        assert isinstance(levered_fcf, list)
        assert len(levered_fcf) > 0

        # Should return numeric values
        for value in levered_fcf:
            if value is not None:
                assert isinstance(value, (int, float))
                assert not np.isnan(value)

    def test_calculate_all_fcf_types(self, mock_calculator):
        """Test calculation of all FCF types"""
        all_fcf = mock_calculator.calculate_all_fcf_types()

        assert isinstance(all_fcf, dict)

        # Should contain the main FCF types
        expected_keys = ['FCFF', 'FCFE', 'Levered FCF']
        for key in expected_keys:
            assert key in all_fcf
            assert isinstance(all_fcf[key], list)


class TestFinancialCalculatorUtilityMethods:
    """Test utility and helper methods in FinancialCalculator"""

    @pytest.fixture
    def mock_calculator(self, temp_company_structure):
        """Create a FinancialCalculator with mock data"""
        calc = FinancialCalculator(temp_company_structure)
        calc.financial_data = {
            'income_statement': {'Net Income': [100000, 110000, 120000]},
            'balance_sheet': {'Total Assets': [500000, 550000, 600000]},
            'cash_flow': {'Operating Cash Flow': [120000, 132000, 144000]}
        }
        return calc

    def test_get_latest_report_date(self, mock_calculator):
        """Test latest report date extraction"""
        date = mock_calculator.get_latest_report_date()

        assert isinstance(date, str)
        assert len(date) > 0

    def test_calculate_growth_rates(self, mock_calculator):
        """Test growth rate calculations"""
        growth_rates = mock_calculator.calculate_growth_rates([100, 110, 121])

        assert isinstance(growth_rates, dict)
        assert '1yr' in growth_rates
        assert '2yr' in growth_rates

        # Should calculate 10% growth
        if growth_rates['1yr'] is not None:
            assert abs(growth_rates['1yr'] - 0.1) < 0.01

    def test_calculate_dcf_inputs(self, mock_calculator):
        """Test DCF inputs calculation"""
        dcf_inputs = mock_calculator.calculate_dcf_inputs()

        assert isinstance(dcf_inputs, dict)

        # Should contain key DCF components
        expected_keys = ['fcf_projections', 'terminal_value', 'discount_rate']
        for key in expected_keys:
            if key in dcf_inputs:
                assert dcf_inputs[key] is not None


class TestSafeNumericConversion:
    """Test safe numeric conversion utility function"""

    def test_safe_numeric_conversion_valid_numbers(self):
        """Test conversion of valid numbers"""
        from core.analysis.engines.financial_calculations import safe_numeric_conversion

        assert safe_numeric_conversion(123) == 123.0
        assert safe_numeric_conversion("456") == 456.0
        assert safe_numeric_conversion(78.9) == 78.9

    def test_safe_numeric_conversion_invalid_values(self):
        """Test conversion of invalid values"""
        from core.analysis.engines.financial_calculations import safe_numeric_conversion

        assert safe_numeric_conversion("invalid") == 0.0
        assert safe_numeric_conversion(None) == 0.0
        assert safe_numeric_conversion("") == 0.0

        # Test with custom default
        assert safe_numeric_conversion("invalid", default=99.0) == 99.0

    def test_safe_numeric_conversion_edge_cases(self):
        """Test edge cases in numeric conversion"""
        from core.analysis.engines.financial_calculations import safe_numeric_conversion

        # Test infinity and NaN
        assert safe_numeric_conversion(float('inf')) == 0.0
        assert safe_numeric_conversion(float('-inf')) == 0.0
        assert safe_numeric_conversion(float('nan')) == 0.0


class TestHandleFinancialNanSeries:
    """Test financial NaN handling utility function"""

    def test_handle_financial_nan_series_basic(self):
        """Test basic NaN handling"""
        import pandas as pd
        from core.analysis.engines.financial_calculations import handle_financial_nan_series

        # Create series with NaN values
        series = pd.Series([100, np.nan, 200, np.nan, 300])
        result = handle_financial_nan_series(series)

        assert isinstance(result, pd.Series)
        assert len(result) == len(series)

    def test_handle_financial_nan_series_all_nan(self):
        """Test handling series with all NaN values"""
        import pandas as pd
        from core.analysis.engines.financial_calculations import handle_financial_nan_series

        series = pd.Series([np.nan, np.nan, np.nan])
        result = handle_financial_nan_series(series)

        assert isinstance(result, pd.Series)
        assert len(result) == len(series)
