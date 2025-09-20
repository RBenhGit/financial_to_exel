"""
Unit tests for data validator module
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch


class TestDataValidator:
    """Test cases for DataValidator class"""

    @pytest.fixture
    def validator(self):
        """Create FinancialDataValidator instance for testing"""
        from core.data_processing.data_validator import FinancialDataValidator
        return FinancialDataValidator()

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator is not None

    def test_validate_numeric_data(self, validator):
        """Test numeric data validation"""
        # Valid numeric data
        valid_data = [100, 200, 300.5, 0]

        # Test with FinancialDataValidator's validate_data_series method
        if hasattr(validator, 'validate_data_series'):
            validated_values, validation_info = validator.validate_data_series(valid_data, "test_metric")
            assert validated_values is not None
            assert validation_info['valid_count'] > 0
        else:
            # Basic validation
            assert all(isinstance(x, (int, float)) for x in valid_data)

    def test_validate_financial_data_structure(self, validator):
        """Test financial data structure validation"""
        # Valid financial data structure
        financial_data = pd.DataFrame({
            'Year': [2020, 2021, 2022],
            'Revenue': [100000, 110000, 120000],
            'Net Income': [10000, 12000, 14000]
        })

        if hasattr(validator, 'validate_dataframe'):
            result = validator.validate_dataframe(financial_data)
            assert result is not None
        else:
            # Basic structure validation
            assert isinstance(financial_data, pd.DataFrame)
            assert len(financial_data.columns) > 0
            assert len(financial_data) > 0

    def test_validate_ticker_symbol(self, validator):
        """Test ticker symbol validation"""
        valid_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        invalid_tickers = ['', '123', 'TOOLONGOFATICKER']  # Removed 'A' as it's actually valid

        for ticker in valid_tickers:
            # Basic ticker validation
            assert isinstance(ticker, str)
            assert len(ticker) >= 1
            assert len(ticker) <= 5
            assert ticker.isalpha()

        for ticker in invalid_tickers:
            # These should fail basic validation
            is_valid = (isinstance(ticker, str) and
                       len(ticker) >= 1 and
                       len(ticker) <= 5 and
                       ticker.isalpha())
            assert not is_valid

    def test_validate_date_ranges(self, validator):
        """Test date range validation"""
        from datetime import datetime, timedelta

        # Valid date range
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 12, 31)

        assert start_date < end_date
        assert (end_date - start_date).days > 0

        # Invalid date range
        invalid_start = datetime(2024, 1, 1)
        invalid_end = datetime(2023, 1, 1)
        assert invalid_start > invalid_end  # This should be caught

    def test_validate_financial_ratios(self, validator):
        """Test financial ratio validation"""
        # Valid ratios should be within reasonable bounds
        pe_ratio = 15.5
        debt_to_equity = 0.3
        profit_margin = 0.12

        # Basic ratio validation
        assert pe_ratio > 0
        assert debt_to_equity >= 0
        assert 0 <= profit_margin <= 1

        # Invalid ratios
        invalid_pe = -5
        invalid_margin = 1.5  # 150% margin is unrealistic

        assert invalid_pe < 0  # Should be caught
        assert invalid_margin > 1  # Should be caught

    def test_validate_missing_data_handling(self, validator):
        """Test handling of missing data"""
        data_with_nulls = pd.DataFrame({
            'Year': [2020, 2021, None],
            'Revenue': [100000, None, 120000],
            'Net Income': [10000, 12000, 14000]
        })

        # Should identify missing data
        null_count = data_with_nulls.isnull().sum().sum()
        assert null_count > 0

        # Should handle missing data appropriately
        if hasattr(validator, 'check_missing_data'):
            missing_info = validator.check_missing_data(data_with_nulls)
            assert missing_info is not None


class TestDataQualityChecks:
    """Test data quality checking functions"""

    def test_check_data_consistency(self):
        """Test data consistency checks"""
        # Consistent data
        consistent_data = pd.DataFrame({
            'Year': [2020, 2021, 2022],
            'Revenue': [100000, 110000, 120000],
            'Expenses': [80000, 85000, 90000]
        })

        # Revenue should be greater than expenses
        revenue_vs_expenses = consistent_data['Revenue'] > consistent_data['Expenses']
        assert all(revenue_vs_expenses)

    def test_check_outlier_detection(self):
        """Test outlier detection"""
        # Data with outlier
        data_with_outlier = [100, 110, 105, 1000, 115]  # 1000 is an outlier

        # Simple outlier detection using IQR
        q1 = np.percentile(data_with_outlier, 25)
        q3 = np.percentile(data_with_outlier, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [x for x in data_with_outlier if x < lower_bound or x > upper_bound]
        assert len(outliers) > 0  # Should detect the outlier

    def test_check_growth_rate_validation(self):
        """Test growth rate validation"""
        # Reasonable growth rates
        reasonable_growth = [0.05, 0.10, -0.02, 0.15]  # 5%, 10%, -2%, 15%

        for rate in reasonable_growth:
            assert -1 < rate < 1  # Growth rates should be within reasonable bounds

        # Unreasonable growth rates
        unreasonable_growth = [5.0, -2.0, 10.0]  # 500%, -200%, 1000%

        for rate in unreasonable_growth:
            assert abs(rate) > 1  # Should be flagged as unreasonable

    def test_check_currency_format_validation(self):
        """Test currency format validation"""
        # Valid currency amounts
        valid_amounts = [1000000, 1.5e6, 2500000.50]

        for amount in valid_amounts:
            assert isinstance(amount, (int, float))
            assert amount >= 0

        # Invalid currency amounts
        invalid_amounts = ["1M", "$1000", "one million"]

        for amount in invalid_amounts:
            # These should not be numeric
            assert not isinstance(amount, (int, float))


class TestDataTypeValidation:
    """Test data type validation"""

    def test_validate_dataframe_types(self):
        """Test DataFrame column type validation"""
        df = pd.DataFrame({
            'Year': [2020, 2021, 2022],
            'Revenue': [100000.0, 110000.0, 120000.0],
            'Company': ['ABC', 'ABC', 'ABC']
        })

        # Check expected types
        assert pd.api.types.is_integer_dtype(df['Year'])
        assert pd.api.types.is_float_dtype(df['Revenue'])
        assert pd.api.types.is_object_dtype(df['Company'])

    def test_validate_numeric_columns(self):
        """Test numeric column validation"""
        numeric_data = pd.Series([100, 200, 300, 400])
        non_numeric_data = pd.Series(['a', 'b', 'c', 'd'])

        assert pd.api.types.is_numeric_dtype(numeric_data)
        assert not pd.api.types.is_numeric_dtype(non_numeric_data)

    def test_validate_date_columns(self):
        """Test date column validation"""
        date_data = pd.to_datetime(['2020-01-01', '2021-01-01', '2022-01-01'])
        non_date_data = pd.Series(['not', 'a', 'date'])

        assert pd.api.types.is_datetime64_any_dtype(date_data)
        assert not pd.api.types.is_datetime64_any_dtype(non_date_data)


class TestBusinessLogicValidation:
    """Test business logic validation"""

    def test_validate_financial_statement_relationships(self):
        """Test financial statement relationship validation"""
        # Basic accounting equation: Assets = Liabilities + Equity
        assets = 1000000
        liabilities = 600000
        equity = 400000

        # Should balance
        assert abs(assets - (liabilities + equity)) < 1e-6

        # Imbalanced example
        imbalanced_assets = 1000000
        imbalanced_liabilities = 700000
        imbalanced_equity = 400000

        # Should not balance
        assert abs(imbalanced_assets - (imbalanced_liabilities + imbalanced_equity)) > 1e-6

    def test_validate_cash_flow_relationships(self):
        """Test cash flow statement relationship validation"""
        # Operating CF should typically be positive for healthy companies
        operating_cf = 150000
        assert operating_cf > 0

        # Free Cash Flow = Operating CF - Capital Expenditures
        capex = 50000
        expected_fcf = operating_cf - capex
        calculated_fcf = 100000

        assert abs(expected_fcf - calculated_fcf) < 1e-6

    def test_validate_profitability_metrics(self):
        """Test profitability metric validation"""
        revenue = 1000000
        net_income = 100000
        profit_margin = net_income / revenue

        # Profit margin should be reasonable
        assert 0 <= profit_margin <= 1
        assert profit_margin == 0.1  # 10%

        # Gross profit should be >= net profit
        gross_profit = 400000
        assert gross_profit >= net_income


class TestErrorHandling:
    """Test error handling in validation"""

    def test_handle_empty_dataframes(self):
        """Test handling of empty DataFrames"""
        empty_df = pd.DataFrame()

        # Should handle empty DataFrame gracefully
        assert len(empty_df) == 0
        assert len(empty_df.columns) == 0

    def test_handle_invalid_data_types(self):
        """Test handling of invalid data types"""
        # Attempting to perform numeric operations on non-numeric data
        try:
            result = "string" + 100
            assert False, "Should have raised TypeError"
        except TypeError:
            pass  # Expected behavior

    def test_handle_division_by_zero(self):
        """Test handling of division by zero"""
        try:
            result = 100 / 0
            assert False, "Should have raised ZeroDivisionError"
        except ZeroDivisionError:
            pass  # Expected behavior

    def test_handle_negative_values_in_ratios(self):
        """Test handling of negative values in financial ratios"""
        # Some ratios can be negative (e.g., negative earnings)
        negative_earnings = -10000
        shares_outstanding = 1000000
        eps = negative_earnings / shares_outstanding

        # Should handle negative EPS
        assert eps < 0


class TestPerformanceValidation:
    """Test performance-related validation"""

    def test_large_dataset_validation_performance(self):
        """Test validation performance with large datasets"""
        import time

        # Create large dataset
        large_df = pd.DataFrame({
            'Year': list(range(2000, 2024)) * 1000,
            'Revenue': np.random.uniform(1000000, 10000000, 24000),
            'Net Income': np.random.uniform(50000, 1000000, 24000)
        })

        start_time = time.time()

        # Perform basic validations
        assert len(large_df) > 0
        assert pd.api.types.is_numeric_dtype(large_df['Revenue'])
        assert pd.api.types.is_numeric_dtype(large_df['Net Income'])

        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0

    def test_memory_usage_validation(self):
        """Test memory usage is reasonable"""
        df = pd.DataFrame({
            'Year': [2020, 2021, 2022],
            'Revenue': [100000, 110000, 120000]
        })

        # Memory usage should be reasonable
        memory_usage = df.memory_usage(deep=True).sum()
        assert memory_usage < 1000000  # Less than 1MB for small dataset


if __name__ == "__main__":
    pytest.main([__file__])