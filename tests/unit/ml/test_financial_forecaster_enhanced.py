"""
Unit tests for enhanced FinancialForecaster with real data integration.

Tests the enhanced functionality for real financial data extraction and processing.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from core.analysis.ml.forecasting.financial_forecaster import FinancialForecaster
from core.analysis.engines.financial_calculations import FinancialCalculator


class TestFinancialForecasterEnhanced:
    """Unit tests for enhanced FinancialForecaster functionality."""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create mock financial calculator with realistic data."""
        calculator = Mock(spec=FinancialCalculator)

        # Create sample time series data
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='QE')

        # Mock income statements
        calculator.income_statements = pd.DataFrame({
            'date': dates,
            'revenue': np.random.uniform(10000, 50000, len(dates)),
            'net_income': np.random.uniform(1000, 5000, len(dates)),
            'gross_profit': np.random.uniform(5000, 25000, len(dates))
        })

        # Mock cash flow statements
        calculator.cash_flow_statements = pd.DataFrame({
            'date': dates,
            'operating_cash_flow': np.random.uniform(2000, 8000, len(dates)),
            'capex': np.random.uniform(500, 2000, len(dates)),
            'free_cash_flow': np.random.uniform(1000, 6000, len(dates))
        })

        # Mock balance sheets
        calculator.balance_sheets = pd.DataFrame({
            'date': dates,
            'total_assets': np.random.uniform(50000, 100000, len(dates)),
            'total_liabilities': np.random.uniform(20000, 60000, len(dates)),
            'shareholders_equity': np.random.uniform(30000, 40000, len(dates))
        })

        # Mock FCF calculation results - returns dict with lists
        calculator.calculate_all_fcf_types.return_value = {
            'FCFE': [3500, 3700, 3900, 4100],  # Free Cash Flow to Equity
            'FCFF': [4000, 4200, 4500, 4800],  # Free Cash Flow to Firm
            'LFCF': [3800, 4000, 4200, 4400]   # Levered Free Cash Flow
        }

        # Mock financial metrics
        calculator.get_financial_metrics.return_value = {
            'revenue_growth': 0.08,
            'fcf_margin': 0.12,
            'debt_to_equity': 0.5
        }

        return calculator

    @pytest.fixture
    def forecaster(self, mock_financial_calculator):
        """Create FinancialForecaster with mock calculator."""
        return FinancialForecaster(financial_calculator=mock_financial_calculator)

    def test_get_historical_fcf_data_real_integration(self, forecaster, mock_financial_calculator):
        """Test _get_historical_fcf_data with real data integration."""
        ticker = "TEST"

        # Call the enhanced method
        result = forecaster._get_historical_fcf_data(ticker)

        # Verify data structure
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'fcf' in result.columns

        # Verify financial calculator was called correctly
        mock_financial_calculator.load_financial_statements.assert_called_once()
        mock_financial_calculator.calculate_all_fcf_types.assert_called_once()

        # Verify data types and values
        assert result['fcf'].dtype in [np.float64, np.int64]
        assert all(result['fcf'] > 0)  # Should have positive FCF values

    def test_get_historical_revenue_data_real_integration(self, forecaster, mock_financial_calculator):
        """Test _get_historical_revenue_data with real data integration."""
        ticker = "TEST"

        # Call the enhanced method
        result = forecaster._get_historical_revenue_data(ticker)

        # Verify data structure
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'revenue' in result.columns

        # Verify financial calculator was called
        mock_financial_calculator.load_financial_statements.assert_called_once()

        # Verify data types and values
        assert result['revenue'].dtype in [np.float64, np.int64]
        assert all(result['revenue'] > 0)  # Should have positive revenue values

    def test_extract_time_series_data_helper(self, forecaster):
        """Test _extract_time_series_data helper method."""
        # Create sample dataframe
        sample_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=4, freq='Q'),
            'value': [100, 110, 120, 130],
            'other_column': [1, 2, 3, 4]
        })

        # Test extraction
        result = forecaster._extract_time_series_data(sample_data, 'value')

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert 'value' in result.columns
        assert len(result) == 4
        assert all(result['value'] == [100, 110, 120, 130])

    def test_extract_time_series_data_missing_column(self, forecaster):
        """Test _extract_time_series_data with missing column."""
        # Create sample dataframe without target column
        sample_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=4, freq='Q'),
            'other_value': [100, 110, 120, 130]
        })

        # Test extraction with missing column
        result = forecaster._extract_time_series_data(sample_data, 'missing_column')

        # Should return empty DataFrame
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_extract_time_series_data_empty_dataframe(self, forecaster):
        """Test _extract_time_series_data with empty dataframe."""
        empty_data = pd.DataFrame()

        # Test extraction with empty data
        result = forecaster._extract_time_series_data(empty_data, 'any_column')

        # Should return empty DataFrame
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_feature_engineering_in_fcf_data(self, forecaster, mock_financial_calculator):
        """Test that FCF data includes proper feature engineering."""
        ticker = "TEST"

        # Get FCF data
        fcf_data = forecaster._get_historical_fcf_data(ticker)

        # Verify feature columns exist
        expected_features = ['fcf', 'quarter', 'year']
        for feature in expected_features:
            assert feature in fcf_data.columns, f"Missing feature: {feature}"

        # Verify feature engineering
        assert fcf_data['quarter'].min() >= 1
        assert fcf_data['quarter'].max() <= 4
        assert fcf_data['year'].min() >= 2020
        assert fcf_data['year'].max() <= 2024

    def test_data_quality_validation(self, forecaster, mock_financial_calculator):
        """Test data quality validation in enhanced methods."""
        ticker = "TEST"

        # Test FCF data quality
        fcf_data = forecaster._get_historical_fcf_data(ticker)

        # Should not contain NaN values in critical columns
        assert not fcf_data['fcf'].isna().any()

        # Should have reasonable data ranges
        assert fcf_data['fcf'].min() >= 0  # FCF can be positive
        assert fcf_data['fcf'].max() < float('inf')

        # Test revenue data quality
        revenue_data = forecaster._get_historical_revenue_data(ticker)

        # Should not contain NaN values in critical columns
        assert not revenue_data['revenue'].isna().any()

        # Should have reasonable data ranges
        assert revenue_data['revenue'].min() > 0  # Revenue should be positive
        assert revenue_data['revenue'].max() < float('inf')

    def test_error_handling_missing_financial_statements(self, forecaster):
        """Test error handling when financial statements are missing."""
        # Mock calculator that raises exception
        forecaster.financial_calculator.load_financial_statements.side_effect = Exception("No data found")

        ticker = "MISSING"

        # Should handle error gracefully
        with pytest.raises(Exception) as exc_info:
            forecaster._get_historical_fcf_data(ticker)

        assert "No data found" in str(exc_info.value)

    def test_error_handling_empty_statements(self, forecaster, mock_financial_calculator):
        """Test error handling when statements are empty."""
        # Mock empty statements
        mock_financial_calculator.cash_flow_statements = pd.DataFrame()
        mock_financial_calculator.income_statements = pd.DataFrame()

        ticker = "EMPTY"

        # Test FCF data extraction with empty statements
        result = forecaster._get_historical_fcf_data(ticker)
        assert isinstance(result, pd.DataFrame)
        # Result may be empty or have default structure

        # Test revenue data extraction with empty statements
        result = forecaster._get_historical_revenue_data(ticker)
        assert isinstance(result, pd.DataFrame)
        # Result may be empty or have default structure

    def test_integration_with_existing_ml_workflow(self, forecaster, mock_financial_calculator):
        """Test that enhanced data methods work with existing ML workflow."""
        ticker = "TEST"

        # Get data using enhanced methods
        fcf_data = forecaster._get_historical_fcf_data(ticker)
        revenue_data = forecaster._get_historical_revenue_data(ticker)

        # Verify data is suitable for ML training
        assert len(fcf_data) >= 4  # Minimum data for training
        assert 'fcf' in fcf_data.columns

        # Test model training with real data
        model, metrics = forecaster.train_fcf_model(ticker, periods=min(8, len(fcf_data)))

        # Verify training succeeded
        assert model is not None
        assert isinstance(metrics, dict)
        assert 'r2_score' in metrics

        # Test prediction with real data
        predictions = forecaster.forecast_fcf(ticker, periods=4)

        # Verify predictions
        assert isinstance(predictions, dict)
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 4

    def test_data_consistency_across_methods(self, forecaster, mock_financial_calculator):
        """Test that data is consistent across different extraction methods."""
        ticker = "TEST"

        # Get data from both methods
        fcf_data = forecaster._get_historical_fcf_data(ticker)
        revenue_data = forecaster._get_historical_revenue_data(ticker)

        # Both should have same date ranges
        if not fcf_data.empty and not revenue_data.empty:
            fcf_years = set(fcf_data['year'].unique()) if 'year' in fcf_data.columns else set()
            revenue_years = set(revenue_data['year'].unique()) if 'year' in revenue_data.columns else set()

            # Should have overlapping years
            assert len(fcf_years.intersection(revenue_years)) > 0 or len(fcf_years) == 0 or len(revenue_years) == 0

    @patch('core.analysis.ml.forecasting.financial_forecaster.datetime')
    def test_date_handling_robustness(self, mock_datetime, forecaster, mock_financial_calculator):
        """Test robust date handling in data extraction."""
        # Mock current date
        mock_datetime.now.return_value = datetime(2024, 1, 1)

        ticker = "TEST"

        # Test with various date formats in mock data
        dates_with_mixed_formats = [
            datetime(2023, 1, 1),
            pd.Timestamp('2023-04-01'),
            '2023-07-01',
            np.datetime64('2023-10-01')
        ]

        # Update mock data with mixed date formats
        mock_financial_calculator.income_statements = pd.DataFrame({
            'date': dates_with_mixed_formats,
            'revenue': [10000, 11000, 12000, 13000]
        })

        # Should handle mixed date formats gracefully
        result = forecaster._get_historical_revenue_data(ticker)
        assert isinstance(result, pd.DataFrame)

        if not result.empty and 'year' in result.columns:
            # Years should be properly extracted
            assert all(isinstance(year, (int, np.integer)) for year in result['year'])
            assert all(2023 <= year <= 2024 for year in result['year'])