"""
Comprehensive Unit Tests for Financial Calculation Engine
=========================================================

Tests for the core financial calculation engine including FCF calculations,
data loading, validation, and error handling.

This test suite covers:
- FCF calculations (FCFE, FCFF, Levered FCF)
- Financial metrics computation
- Data loading and validation
- Error handling and edge cases
- Integration with multiple data sources

Test Organization follows pytest best practices with proper fixtures,
parametrized tests, and comprehensive coverage of critical functionality.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import os

# Import the class under test
from core.analysis.engines.financial_calculations import (
    FinancialCalculator,
    calculate_unified_fcf,
    calculate_fcf_from_api_data,
    safe_numeric_conversion,
    handle_financial_nan_series,
    retry_with_exponential_backoff
)

# Import supporting classes and exceptions
from core.data_processing.financial_variable_registry import FinancialVariableRegistry
from core.data_processing.var_input_data import VarInputData
from core.analysis.fcf_date_correlation import ComprehensiveFCFResults


@pytest.fixture
def sample_financial_data():
    """Provide sample financial data for testing"""
    return {
        'revenue': [1000, 1100, 1200, 1300],
        'net_income': [100, 110, 120, 130],
        'depreciation': [50, 55, 60, 65],
        'capex': [80, 85, 90, 95],
        'working_capital_change': [10, 12, 14, 16],
        'ebit': [150, 165, 180, 195],
        'tax_rate': 0.25,
        'shares_outstanding': [1000000, 1000000, 1000000, 1000000],
        'debt_payments': [20, 22, 24, 26]
    }


@pytest.fixture
def sample_excel_data():
    """Create sample Excel-like DataFrame for testing"""
    data = {
        'A': ['Revenue', 'Net Income', 'Depreciation & Amortization', 'Capital Expenditures'],
        'B': [1000, 100, 50, 80],
        'C': [1100, 110, 55, 85],
        'D': [1200, 120, 60, 90],
        'E': [1300, 130, 65, 95]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_excel_files(tmp_path):
    """Create temporary Excel files for testing"""
    # Create temporary company directory structure
    company_dir = tmp_path / "MSFT" / "FY"
    company_dir.mkdir(parents=True)

    # Create mock Excel files
    income_statement = company_dir / "Income Statement.xlsx"
    balance_sheet = company_dir / "Balance Sheet.xlsx"
    cash_flow = company_dir / "Cash Flow Statement.xlsx"

    # Create simple Excel-like data
    sample_data = pd.DataFrame({
        'A': ['Revenue', 'Net Income'],
        'B': [1000, 100],
        'C': [1100, 110]
    })

    # Write to files (these would normally be Excel files)
    for file in [income_statement, balance_sheet, cash_flow]:
        sample_data.to_csv(file.with_suffix('.csv'), index=False)

    return {
        'company_dir': str(company_dir.parent),
        'files': {
            'income': str(income_statement),
            'balance': str(balance_sheet),
            'cash_flow': str(cash_flow)
        }
    }


@pytest.fixture
def financial_calculator():
    """Create a FinancialCalculator instance for testing"""
    with patch('core.data_processing.var_input_data.get_var_input_data') as mock_var_data:
        mock_var_data.return_value = None
        calculator = FinancialCalculator(
            ticker_symbol="TEST",
            use_excel_data=False,
            enhanced_data_manager=None
        )
        return calculator


class TestFinancialCalculator:
    """Test suite for FinancialCalculator class"""

    def test_calculator_initialization(self):
        """Test basic calculator initialization"""
        with patch('core.data_processing.var_input_data.get_var_input_data') as mock_var_data:
            mock_var_data.return_value = None
            calculator = FinancialCalculator(
                company_folder="test_dir/MSFT"
            )
            assert calculator.company_folder == "test_dir/MSFT"
            assert calculator.company_name == "MSFT"

    def test_safe_numeric_conversion(self):
        """Test safe numeric conversion utility function"""
        # Test valid numbers
        assert safe_numeric_conversion(100) == 100.0
        assert safe_numeric_conversion("150.5") == 150.5
        assert safe_numeric_conversion(200.75) == 200.75

        # Test invalid values
        assert safe_numeric_conversion("invalid") == 0.0
        assert safe_numeric_conversion(None) == 0.0
        assert safe_numeric_conversion("") == 0.0

        # Test with custom default
        assert safe_numeric_conversion("invalid", default=100.0) == 100.0

        # Test NaN and infinity
        assert safe_numeric_conversion(np.nan) == 0.0
        assert safe_numeric_conversion(np.inf) == 0.0

    def test_handle_financial_nan_series(self):
        """Test financial NaN series handling"""
        # Create test series with NaN values
        series_with_nan = pd.Series([100, np.nan, 200, np.nan, 300])

        # Test forward fill strategy
        result = handle_financial_nan_series(series_with_nan, strategy='forward_fill')
        expected = pd.Series([100, 100, 200, 200, 300])
        pd.testing.assert_series_equal(result, expected)

        # Test zero fill strategy
        result = handle_financial_nan_series(series_with_nan, strategy='zero_fill')
        expected = pd.Series([100, 0, 200, 0, 300])
        pd.testing.assert_series_equal(result, expected)

        # Test interpolation strategy
        result = handle_financial_nan_series(series_with_nan, strategy='interpolate')
        assert not result.isna().any()

    @pytest.mark.parametrize("use_var_input_data", [True, False])
    @pytest.mark.financial_calc
    def test_fcf_to_firm_calculation(self, financial_calculator, sample_financial_data, use_var_input_data):
        """Test FCFF (Free Cash Flow to Firm) calculation"""
        # Mock the necessary data
        financial_calculator.financial_metrics = sample_financial_data

        # Mock var_input_data if using it
        with patch.object(financial_calculator, 'var_input_data') as mock_var_data:
            mock_var_data.get_latest_available_value.side_effect = lambda x: sample_financial_data.get(x, [0])[-1]
            mock_var_data.get_values.side_effect = lambda x: sample_financial_data.get(x, [0])

            result = financial_calculator.calculate_fcf_to_firm(use_var_input_data=use_var_input_data)

            # FCFF = EBIT(1-Tax Rate) + Depreciation - CapEx - Change in Working Capital
            # Expected calculation: 195 * (1-0.25) + 65 - 95 - 16 = 146.25 + 65 - 95 - 16 = 100.25
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(val, (int, float)) for val in result)

    @pytest.mark.parametrize("use_var_input_data", [True, False])
    @pytest.mark.financial_calc
    def test_fcf_to_equity_calculation(self, financial_calculator, sample_financial_data, use_var_input_data):
        """Test FCFE (Free Cash Flow to Equity) calculation"""
        financial_calculator.financial_metrics = sample_financial_data

        with patch.object(financial_calculator, 'var_input_data') as mock_var_data:
            mock_var_data.get_latest_available_value.side_effect = lambda x: sample_financial_data.get(x, [0])[-1]
            mock_var_data.get_values.side_effect = lambda x: sample_financial_data.get(x, [0])

            result = financial_calculator.calculate_fcf_to_equity(use_var_input_data=use_var_input_data)

            # FCFE = Net Income + Depreciation - CapEx - Change in Working Capital - Net Debt Payments
            # Expected calculation: 130 + 65 - 95 - 16 - 26 = 58
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(val, (int, float)) for val in result)

    @pytest.mark.parametrize("use_var_input_data", [True, False])
    @pytest.mark.financial_calc
    def test_levered_fcf_calculation(self, financial_calculator, sample_financial_data, use_var_input_data):
        """Test Levered FCF calculation"""
        financial_calculator.financial_metrics = sample_financial_data

        with patch.object(financial_calculator, 'var_input_data') as mock_var_data:
            mock_var_data.get_latest_available_value.side_effect = lambda x: sample_financial_data.get(x, [0])[-1]
            mock_var_data.get_values.side_effect = lambda x: sample_financial_data.get(x, [0])

            result = financial_calculator.calculate_levered_fcf(use_var_input_data=use_var_input_data)

            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(val, (int, float)) for val in result)

    def test_calculate_all_fcf_types(self, financial_calculator):
        """Test calculation of all FCF types together"""
        with patch.object(financial_calculator, 'calculate_fcf_to_firm') as mock_fcff, \
             patch.object(financial_calculator, 'calculate_fcf_to_equity') as mock_fcfe, \
             patch.object(financial_calculator, 'calculate_levered_fcf') as mock_levered:

            mock_fcff.return_value = [100, 110, 120]
            mock_fcfe.return_value = [80, 85, 90]
            mock_levered.return_value = [90, 95, 100]

            result = financial_calculator.calculate_all_fcf_types()

            assert isinstance(result, dict)
            assert 'fcf_to_firm' in result
            assert 'fcf_to_equity' in result
            assert 'levered_fcf' in result
            assert result['fcf_to_firm'] == [100, 110, 120]
            assert result['fcf_to_equity'] == [80, 85, 90]
            assert result['levered_fcf'] == [90, 95, 100]

    def test_get_comprehensive_fcf_results(self, financial_calculator):
        """Test comprehensive FCF results generation"""
        # Mock the calculate_all_fcf_types method
        with patch.object(financial_calculator, 'calculate_all_fcf_types') as mock_calc, \
             patch.object(financial_calculator, 'get_latest_report_date') as mock_date:

            mock_calc.return_value = {
                'fcf_to_firm': [100, 110, 120],
                'fcf_to_equity': [80, 85, 90],
                'levered_fcf': [90, 95, 100]
            }
            mock_date.return_value = "2023-12-31"

            result = financial_calculator.get_comprehensive_fcf_results()

            assert isinstance(result, ComprehensiveFCFResults)
            assert result.fcf_to_firm == [100, 110, 120]
            assert result.fcf_to_equity == [80, 85, 90]
            assert result.levered_fcf == [90, 95, 100]

    @pytest.mark.integration
    def test_data_loading_error_handling(self, financial_calculator):
        """Test error handling during data loading"""
        # Test with invalid directory
        financial_calculator.company_data_dir = "/invalid/path"
        financial_calculator.use_excel_data = True

        # Should handle missing directory gracefully
        with patch('os.path.exists', return_value=False):
            financial_calculator.load_financial_statements()
            # Should not raise exception, should log error instead
            assert True  # If we get here, error handling worked

    def test_growth_rate_calculation(self, financial_calculator):
        """Test growth rate calculations"""
        values = [100, 110, 121, 133.1]  # 10% growth rate

        with patch.object(financial_calculator, 'var_input_data') as mock_var_data:
            mock_var_data.get_values.return_value = values

            result = financial_calculator.calculate_growth_rates(['revenue'])

            assert isinstance(result, dict)
            assert 'revenue' in result

            growth_rates = result['revenue']
            assert isinstance(growth_rates, list)
            assert len(growth_rates) == len(values) - 1  # One less than input values

            # Check that growth rates are approximately 10%
            for rate in growth_rates:
                assert abs(rate - 0.10) < 0.01  # Within 1% tolerance


class TestUtilityFunctions:
    """Test suite for utility functions"""

    def test_calculate_unified_fcf_function(self):
        """Test standalone unified FCF calculation function"""
        standardized_data = {
            'net_income': [100, 110, 120],
            'depreciation': [50, 55, 60],
            'capex': [80, 85, 90],
            'working_capital_change': [10, 12, 14],
            'ebit': [150, 165, 180],
            'tax_rate': 0.25
        }

        result = calculate_unified_fcf(standardized_data)

        assert isinstance(result, dict)
        assert 'fcf_to_firm' in result
        assert 'fcf_to_equity' in result
        assert isinstance(result['fcf_to_firm'], list)
        assert isinstance(result['fcf_to_equity'], list)

    def test_calculate_fcf_from_api_data_function(self):
        """Test FCF calculation from API data"""
        api_data = {
            'netIncome': [100, 110, 120],
            'depreciation': [50, 55, 60],
            'capitalExpenditure': [80, 85, 90],
        }

        result = calculate_fcf_from_api_data(api_data, 'alpha_vantage')

        assert isinstance(result, dict)
        assert 'fcf_data' in result
        assert 'metadata' in result

    def test_retry_decorator(self):
        """Test exponential backoff retry decorator"""
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.1)
        def failing_function():
            failing_function.call_count += 1
            if failing_function.call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        failing_function.call_count = 0

        result = failing_function()
        assert result == "success"
        assert failing_function.call_count == 3


class TestErrorHandling:
    """Test suite for error handling scenarios"""

    def test_missing_data_handling(self, financial_calculator):
        """Test handling of missing financial data"""
        # Test with empty financial metrics
        financial_calculator.financial_metrics = {}

        result = financial_calculator.calculate_fcf_to_firm(use_var_input_data=False)

        # Should return empty list or zeros, not crash
        assert isinstance(result, list)

    def test_invalid_ticker_handling(self):
        """Test handling of invalid ticker symbols"""
        with patch('core.analysis.engines.financial_calculations.FinancialVariableRegistry'):
            calculator = FinancialCalculator(
                ticker_symbol="INVALID_TICKER_SYMBOL_123",
                use_excel_data=False
            )

            # Should initialize without error
            assert calculator.ticker_symbol == "INVALID_TICKER_SYMBOL_123"

    def test_corrupted_excel_data_handling(self, financial_calculator):
        """Test handling of corrupted Excel data"""
        # Mock corrupted Excel reading
        with patch.object(financial_calculator, '_load_excel_data') as mock_load:
            mock_load.side_effect = Exception("Corrupted file")

            # Should handle exception gracefully
            financial_calculator.load_financial_statements()
            # Test passes if no unhandled exception is raised


@pytest.mark.integration
class TestDataSourceIntegration:
    """Integration tests for data source interactions"""

    def test_excel_data_integration(self, mock_excel_files):
        """Test integration with Excel data sources"""
        with patch('core.analysis.engines.financial_calculations.FinancialVariableRegistry'):
            calculator = FinancialCalculator(
                ticker_symbol="MSFT",
                use_excel_data=True,
                company_data_dir=mock_excel_files['company_dir']
            )

            # Test that calculator can handle file-based data
            assert calculator.use_excel_data is True
            assert calculator.company_data_dir == mock_excel_files['company_dir']

    @patch('core.analysis.engines.financial_calculations.EnhancedDataManager')
    def test_api_data_integration(self, mock_data_manager, financial_calculator):
        """Test integration with API data sources"""
        # Mock API data manager
        mock_manager = Mock()
        mock_manager.get_standardized_data.return_value = {
            'net_income': [100, 110, 120],
            'revenue': [1000, 1100, 1200]
        }

        financial_calculator.enhanced_data_manager = mock_manager

        result = financial_calculator.get_standardized_financial_data()

        assert isinstance(result, dict)
        mock_manager.get_standardized_data.assert_called_once()


@pytest.mark.performance
class TestPerformanceScenarios:
    """Performance-related tests"""

    def test_large_dataset_handling(self, financial_calculator):
        """Test handling of large financial datasets"""
        # Create large dataset (10 years of quarterly data)
        large_dataset = {
            'revenue': list(range(1000, 1400, 10)),  # 40 quarters
            'net_income': list(range(100, 140, 1)),
            'depreciation': list(range(50, 90, 1))
        }

        financial_calculator.financial_metrics = large_dataset

        # Should handle large datasets efficiently
        with patch.object(financial_calculator, 'var_input_data') as mock_var_data:
            mock_var_data.get_values.side_effect = lambda x: large_dataset.get(x, [0])

            result = financial_calculator.calculate_fcf_to_firm(use_var_input_data=use_var_input_data)

            assert isinstance(result, list)
            assert len(result) == len(large_dataset['revenue'])


if __name__ == "__main__":
    # Run tests with coverage if executed directly
    pytest.main([__file__, "-v", "--cov=core.analysis.engines.financial_calculations"])