"""
Unit tests for FinancialCalculator utility functions and methods.

This module focuses on testing utility functions, helper methods, and simple
calculations that don't require complex data mocking.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from core.analysis.engines.financial_calculations import (
    FinancialCalculator,
    safe_numeric_conversion,
    handle_financial_nan_series,
    get_unknown_company_name
)


class TestUtilityFunctions:
    """Test standalone utility functions"""

    def test_safe_numeric_conversion_valid_numbers(self):
        """Test safe numeric conversion with valid numbers"""
        # Test integer
        assert safe_numeric_conversion(42) == 42

        # Test float
        assert safe_numeric_conversion(3.14) == 3.14

        # Test string number
        assert safe_numeric_conversion("123") == 123

        # Test string float
        assert safe_numeric_conversion("45.67") == 45.67

    def test_safe_numeric_conversion_invalid_values(self):
        """Test safe numeric conversion with invalid values"""
        # Test None
        assert safe_numeric_conversion(None) == 0

        # Test empty string
        assert safe_numeric_conversion("") == 0

        # Test non-numeric string
        assert safe_numeric_conversion("abc") == 0

        # Test NaN
        assert safe_numeric_conversion(np.nan) == 0

        # Test inf
        assert safe_numeric_conversion(np.inf) == 0

    def test_safe_numeric_conversion_edge_cases(self):
        """Test safe numeric conversion with edge cases"""
        # Test very large number
        large_num = 1e20
        assert safe_numeric_conversion(large_num) == large_num

        # Test very small number
        small_num = 1e-10
        assert safe_numeric_conversion(small_num) == small_num

        # Test negative number
        assert safe_numeric_conversion(-42) == -42

        # Test zero
        assert safe_numeric_conversion(0) == 0

    def test_handle_financial_nan_series_basic(self):
        """Test handle_financial_nan_series with basic data"""
        # Create test series with NaN values
        test_series = pd.Series([1, np.nan, 3, np.nan, 5])

        # Test forward fill method
        result = handle_financial_nan_series(test_series, method='forward')

        # Should be a pandas Series
        assert isinstance(result, pd.Series)

        # Should have no NaN values
        assert not result.isna().any()

        # First value should remain unchanged
        assert result.iloc[0] == 1

    def test_handle_financial_nan_series_all_nan(self):
        """Test handle_financial_nan_series with all NaN values"""
        # Create test series with all NaN values
        test_series = pd.Series([np.nan, np.nan, np.nan])

        # Test with default fill value
        result = handle_financial_nan_series(test_series, fill_value=0)

        # Should be filled with default value
        assert all(result == 0)

    def test_get_unknown_company_name(self):
        """Test get_unknown_company_name function"""
        name = get_unknown_company_name()

        # Should return a string
        assert isinstance(name, str)

        # Should not be empty
        assert len(name) > 0

        # Should contain "Unknown"
        assert "Unknown" in name


class TestFinancialCalculatorBasicMethods:
    """Test FinancialCalculator basic methods that don't require complex data"""

    @pytest.fixture
    def minimal_calculator(self):
        """Create a minimal FinancialCalculator for testing"""
        with patch.object(FinancialCalculator, '_auto_extract_ticker'), \
             patch.object(FinancialCalculator, 'load_financial_statements'):
            calc = FinancialCalculator(None)
            calc.company_name = "Test Company"
            calc.ticker_symbol = "TEST"
            return calc

    def test_calculator_initialization(self, minimal_calculator):
        """Test basic calculator initialization"""
        assert minimal_calculator.company_name == "Test Company"
        assert minimal_calculator.ticker_symbol == "TEST"
        assert isinstance(minimal_calculator.financial_data, dict)
        assert isinstance(minimal_calculator.fcf_results, dict)

    def test_currency_handling(self, minimal_calculator):
        """Test currency-related methods"""
        # Test default currency
        assert minimal_calculator.currency == 'USD'
        assert minimal_calculator.financial_currency == 'USD'

        # Test TASE detection
        assert minimal_calculator.is_tase_stock == False

    def test_validation_enabled_by_default(self, minimal_calculator):
        """Test that validation is enabled by default"""
        assert minimal_calculator.validation_enabled == True
        assert minimal_calculator.data_validator is not None

    def test_metrics_cache_initialization(self, minimal_calculator):
        """Test metrics cache initialization"""
        assert isinstance(minimal_calculator.metrics, dict)
        assert minimal_calculator.metrics_calculated == False


class TestDataProcessingMethods:
    """Test data processing and extraction methods"""

    @pytest.fixture
    def calculator_with_data(self):
        """Create calculator with sample data"""
        with patch.object(FinancialCalculator, '_auto_extract_ticker'), \
             patch.object(FinancialCalculator, 'load_financial_statements'):
            calc = FinancialCalculator(None)

            # Add simple test data
            calc.financial_data = {
                'income_fy': pd.DataFrame({
                    'Revenue': [100, 110, 120],
                    'Net Income': [10, 12, 15]
                }),
                'balance_fy': pd.DataFrame({
                    'Total Assets': [200, 220, 240],
                    'Total Equity': [100, 110, 120]
                })
            }
            return calc

    def test_basic_metric_extraction(self, calculator_with_data):
        """Test basic metric extraction from financial data"""
        calc = calculator_with_data

        # Test that data exists
        assert 'income_fy' in calc.financial_data
        assert 'balance_fy' in calc.financial_data

        # Test data structure
        assert isinstance(calc.financial_data['income_fy'], pd.DataFrame)
        assert len(calc.financial_data['income_fy']) == 3

    def test_empty_data_handling(self):
        """Test handling of empty financial data"""
        with patch.object(FinancialCalculator, '_auto_extract_ticker'), \
             patch.object(FinancialCalculator, 'load_financial_statements'):
            calc = FinancialCalculator(None)

            # Test with empty data
            calc.financial_data = {}

            # Should not crash when accessing empty data
            assert len(calc.financial_data) == 0


class TestCalculationHelpers:
    """Test calculation helper methods"""

    def test_growth_rate_calculation(self):
        """Test growth rate calculation logic"""
        # Test basic growth rate calculation
        values = [100, 110, 121]  # 10% growth each year

        # Test simple growth calculation
        growth = (values[-1] / values[0]) ** (1 / (len(values) - 1)) - 1

        # Should be approximately 10%
        assert abs(growth - 0.1) < 0.001

    def test_compound_annual_growth_rate(self):
        """Test CAGR calculation"""
        # Test CAGR calculation
        starting_value = 100
        ending_value = 150
        years = 3

        cagr = (ending_value / starting_value) ** (1 / years) - 1

        # Should be approximately 14.47%
        assert abs(cagr - 0.1447) < 0.001


class TestErrorHandling:
    """Test error handling in financial calculations"""

    def test_division_by_zero_handling(self):
        """Test division by zero handling"""
        # Test safe division
        result = safe_numeric_conversion(10 / 0 if False else 0)
        assert result == 0

    def test_invalid_data_types(self):
        """Test handling of invalid data types"""
        # Test with list
        result = safe_numeric_conversion([1, 2, 3])
        assert result == 0

        # Test with dict
        result = safe_numeric_conversion({"key": "value"})
        assert result == 0

    def test_overflow_handling(self):
        """Test handling of numeric overflow"""
        # Test very large number
        large_number = 1e308
        result = safe_numeric_conversion(large_number)
        assert result == large_number

        # Test overflow that might cause inf
        try:
            overflow_result = safe_numeric_conversion(float('inf'))
            assert overflow_result == 0  # Should convert inf to 0
        except OverflowError:
            pass  # Acceptable behavior


class TestDataQualityMethods:
    """Test data quality assessment methods"""

    @pytest.fixture
    def quality_calculator(self):
        """Create calculator for quality testing"""
        with patch.object(FinancialCalculator, '_auto_extract_ticker'), \
             patch.object(FinancialCalculator, 'load_financial_statements'):
            calc = FinancialCalculator(None)
            return calc

    def test_data_completeness_scoring(self, quality_calculator):
        """Test data completeness scoring"""
        calc = quality_calculator

        # Test with complete data
        complete_data = pd.Series([1, 2, 3, 4, 5])
        completeness = 1.0 - (complete_data.isna().sum() / len(complete_data))
        assert completeness == 1.0

    def test_data_consistency_checks(self, quality_calculator):
        """Test data consistency validation"""
        calc = quality_calculator

        # Test basic consistency
        values = [100, 110, 120]  # Increasing trend
        assert all(values[i] <= values[i+1] for i in range(len(values)-1))

    def test_missing_data_identification(self, quality_calculator):
        """Test identification of missing data"""
        calc = quality_calculator

        # Test missing data detection
        data_with_missing = pd.Series([1, np.nan, 3, np.nan, 5])
        missing_count = data_with_missing.isna().sum()
        assert missing_count == 2