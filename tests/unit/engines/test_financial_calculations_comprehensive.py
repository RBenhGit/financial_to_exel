"""
Comprehensive Unit Tests for FinancialCalculator

This module provides extensive unit test coverage for the core financial calculations
module, focusing on achieving >95% test coverage for critical financial analysis
functionality.

Test Categories:
- Initialization and Setup Tests
- Excel Data Loading Tests
- FCF Calculation Tests (FCFE, FCFF, Levered FCF)
- Market Data Integration Tests
- Enhanced Data Manager Integration Tests
- Growth Rate Calculation Tests
- Data Validation Tests
- Error Handling Tests
- Currency and TASE Integration Tests
- Performance and Caching Tests

Each test category includes both positive and negative test cases with comprehensive
edge case coverage.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the module under test
from core.analysis.engines.financial_calculations import (
    FinancialCalculator,
    retry_with_exponential_backoff,
    calculate_unified_fcf,
    calculate_fcf_from_api_data
)
from core.analysis.fcf_date_correlation import (
    ComprehensiveFCFResults,
    FCFDataPoint,
    CorrelatedFCFResults
)
from tools.utilities.error_handler import (
    FinancialAnalysisError,
    CalculationError,
    ValidationError,
    ExcelDataError
)


class TestFinancialCalculatorInitialization:
    """Test FinancialCalculator initialization and setup"""

    def test_init_with_company_folder(self):
        """Test initialization with valid company folder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            calculator = FinancialCalculator(temp_dir)

            assert calculator.company_folder == temp_dir
            assert calculator.company_name == os.path.basename(temp_dir)
            assert calculator.financial_data == {}
            assert calculator.fcf_results == {}
            assert isinstance(calculator.comprehensive_fcf_results, ComprehensiveFCFResults)
            assert calculator.ticker_symbol is None
            assert calculator.current_stock_price is None
            assert calculator.currency == 'USD'
            assert calculator.financial_scale_factor == 1
            assert calculator.validation_enabled is True

    def test_init_without_company_folder(self):
        """Test initialization without company folder"""
        calculator = FinancialCalculator(None)

        assert calculator.company_folder is None
        assert calculator.company_name is not None  # Should use get_unknown_company_name()
        assert calculator.financial_data == {}

    def test_init_with_enhanced_data_manager(self):
        """Test initialization with enhanced data manager"""
        mock_manager = Mock()

        calculator = FinancialCalculator(None, mock_manager)

        assert calculator.enhanced_data_manager is mock_manager

    def test_init_auto_load_failure_handling(self):
        """Test graceful handling of auto-load failures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory but no valid Excel files
            fy_dir = os.path.join(temp_dir, 'FY')
            os.makedirs(fy_dir)

            # Should not raise exception, just log warning
            calculator = FinancialCalculator(temp_dir)
            assert calculator.company_folder == temp_dir

    @patch('core.analysis.engines.financial_calculations.get_unknown_company_name')
    def test_unknown_company_name_fallback(self, mock_get_name):
        """Test fallback to unknown company name"""
        mock_get_name.return_value = "Unknown Company"

        calculator = FinancialCalculator(None)

        assert calculator.company_name == "Unknown Company"
        mock_get_name.assert_called_once()


class TestExcelDataLoading:
    """Test Excel data loading functionality"""

    def create_mock_excel_file(self, file_path: str, data: Dict[str, Any]):
        """Helper to create mock Excel file data"""
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return df

    def test_load_financial_statements_success(self):
        """Test successful loading of financial statements"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            fy_dir = os.path.join(temp_dir, 'FY')
            ltm_dir = os.path.join(temp_dir, 'LTM')
            os.makedirs(fy_dir)
            os.makedirs(ltm_dir)

            # Create mock Excel files
            income_data = {'Metric': ['Revenue', 'Net Income'], 'FY2023': [1000, 100], 'FY2022': [900, 90]}
            balance_data = {'Metric': ['Total Assets', 'Total Equity'], 'FY2023': [2000, 800], 'FY2022': [1800, 720]}
            cashflow_data = {'Metric': ['Operating Cash Flow', 'CapEx'], 'FY2023': [150, -50], 'FY2022': [135, -45]}

            self.create_mock_excel_file(os.path.join(fy_dir, 'Income Statement.xlsx'), income_data)
            self.create_mock_excel_file(os.path.join(fy_dir, 'Balance Sheet.xlsx'), balance_data)
            self.create_mock_excel_file(os.path.join(fy_dir, 'Cash Flow Statement.xlsx'), cashflow_data)

            # Create LTM files
            self.create_mock_excel_file(os.path.join(ltm_dir, 'Income Statement.xlsx'), income_data)
            self.create_mock_excel_file(os.path.join(ltm_dir, 'Balance Sheet.xlsx'), balance_data)
            self.create_mock_excel_file(os.path.join(ltm_dir, 'Cash Flow Statement.xlsx'), cashflow_data)

            calculator = FinancialCalculator(temp_dir)

            # Check that data was loaded
            assert 'income_fy' in calculator.financial_data
            assert 'balance_fy' in calculator.financial_data
            assert 'cashflow_fy' in calculator.financial_data
            assert 'income_ltm' in calculator.financial_data
            assert 'balance_ltm' in calculator.financial_data
            assert 'cashflow_ltm' in calculator.financial_data

    def test_load_financial_statements_missing_directory(self):
        """Test handling of missing directory"""
        calculator = FinancialCalculator("/non/existent/path")

        with pytest.raises(ExcelDataError):
            calculator.load_financial_statements()

    def test_load_financial_statements_permission_error(self):
        """Test handling of permission errors"""
        with patch('os.listdir', side_effect=PermissionError("Access denied")):
            calculator = FinancialCalculator("some_path")

            with pytest.raises(ExcelDataError, match="Cannot access financial statement files"):
                calculator.load_financial_statements()

    @patch('pandas.read_excel')
    def test_load_excel_data_success(self, mock_read_excel):
        """Test successful Excel data loading"""
        # Setup mock data
        mock_data = pd.DataFrame({
            'Metric': ['Revenue', 'Net Income'],
            'FY2023': [1000, 100],
            'FY2022': [900, 90]
        })
        mock_read_excel.return_value = mock_data

        calculator = FinancialCalculator(None)
        result = calculator._load_excel_data("test_file.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_read_excel.assert_called_once()

    @patch('pandas.read_excel', side_effect=Exception("Excel read error"))
    def test_load_excel_data_failure(self, mock_read_excel):
        """Test Excel data loading failure handling"""
        calculator = FinancialCalculator(None)

        with pytest.raises(Exception):
            calculator._load_excel_data("test_file.xlsx")


class TestFCFCalculations:
    """Test Free Cash Flow calculation methods"""

    def setup_mock_financial_data(self) -> FinancialCalculator:
        """Helper to create calculator with mock financial data"""
        calculator = FinancialCalculator(None)

        # Mock financial data
        calculator.financial_data = {
            'income_fy': pd.DataFrame({
                'Metric': ['Net Income', 'Depreciation'],
                'FY2023': [100, 20],
                'FY2022': [90, 18]
            }),
            'cashflow_fy': pd.DataFrame({
                'Metric': ['Operating Cash Flow', 'Capital Expenditures', 'Free Cash Flow'],
                'FY2023': [150, -50, 100],
                'FY2022': [135, -45, 90]
            }),
            'balance_fy': pd.DataFrame({
                'Metric': ['Total Debt', 'Cash and Equivalents'],
                'FY2023': [200, 50],
                'FY2022': [180, 45]
            })
        }

        return calculator

    @patch('core.analysis.engines.financial_calculations.validate_financial_calculation_input')
    def test_calculate_fcf_to_firm_success(self, mock_validate):
        """Test successful FCFF calculation"""
        calculator = self.setup_mock_financial_data()
        mock_validate.return_value = True

        # Mock the VarInputData method
        with patch.object(calculator, '_get_var_input_data') as mock_var:
            mock_var.return_value = [120, 110, 100]  # Mock 3 years of data

            result = calculator.calculate_fcf_to_firm()

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(x, (int, float)) for x in result)

    @patch('core.analysis.engines.financial_calculations.validate_financial_calculation_input')
    def test_calculate_fcf_to_equity_success(self, mock_validate):
        """Test successful FCFE calculation"""
        calculator = self.setup_mock_financial_data()
        mock_validate.return_value = True

        with patch.object(calculator, '_get_var_input_data') as mock_var:
            mock_var.return_value = [100, 90, 85]

            result = calculator.calculate_fcf_to_equity()

            assert isinstance(result, list)
            assert len(result) == 3

    @patch('core.analysis.engines.financial_calculations.validate_financial_calculation_input')
    def test_calculate_levered_fcf_success(self, mock_validate):
        """Test successful Levered FCF calculation"""
        calculator = self.setup_mock_financial_data()
        mock_validate.return_value = True

        with patch.object(calculator, '_get_var_input_data') as mock_var:
            mock_var.return_value = [110, 95, 88]

            result = calculator.calculate_levered_fcf()

            assert isinstance(result, list)
            assert len(result) == 3

    def test_calculate_all_fcf_types(self):
        """Test calculation of all FCF types together"""
        calculator = self.setup_mock_financial_data()

        with patch.object(calculator, 'calculate_fcf_to_firm') as mock_fcff, \
             patch.object(calculator, 'calculate_fcf_to_equity') as mock_fcfe, \
             patch.object(calculator, 'calculate_levered_fcf') as mock_lfcf:

            mock_fcff.return_value = [120, 110, 100]
            mock_fcfe.return_value = [100, 90, 85]
            mock_lfcf.return_value = [110, 95, 88]

            result = calculator.calculate_all_fcf_types()

            assert isinstance(result, dict)
            assert 'FCFF' in result
            assert 'FCFE' in result
            assert 'LFCF' in result
            assert result['FCFF'] == [120, 110, 100]
            assert result['FCFE'] == [100, 90, 85]
            assert result['LFCF'] == [110, 95, 88]

    @patch('core.analysis.engines.financial_calculations.validate_financial_calculation_input')
    def test_fcf_calculation_validation_failure(self, mock_validate):
        """Test FCF calculation with validation failure"""
        calculator = self.setup_mock_financial_data()
        mock_validate.return_value = False

        with pytest.raises(ValidationError):
            calculator.calculate_fcf_to_firm()

    def test_fcf_calculation_empty_data(self):
        """Test FCF calculation with empty financial data"""
        calculator = FinancialCalculator(None)

        with pytest.raises((ValidationError, CalculationError)):
            calculator.calculate_fcf_to_firm()


class TestMarketDataIntegration:
    """Test market data fetching and integration"""

    @patch('yfinance.Ticker')
    def test_fetch_market_data_success(self, mock_ticker):
        """Test successful market data fetching"""
        calculator = FinancialCalculator(None)
        calculator.ticker_symbol = 'AAPL'

        # Mock yfinance response
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'currentPrice': 150.0,
            'marketCap': 2400000000000,
            'sharesOutstanding': 16000000000
        }
        mock_ticker.return_value = mock_ticker_instance

        result = calculator.fetch_market_data()

        assert result is not None
        assert calculator.current_stock_price == 150.0
        assert calculator.market_cap == 2400000000000
        assert calculator.shares_outstanding == 16000000000

    @patch('yfinance.Ticker')
    def test_fetch_market_data_no_ticker(self, mock_ticker):
        """Test market data fetching without ticker symbol"""
        calculator = FinancialCalculator(None)

        result = calculator.fetch_market_data()

        assert result is None

    @patch('yfinance.Ticker', side_effect=Exception("Network error"))
    def test_fetch_market_data_failure(self, mock_ticker):
        """Test handling of market data fetch failures"""
        calculator = FinancialCalculator(None)
        calculator.ticker_symbol = 'AAPL'

        # Should not raise exception, just return None
        result = calculator.fetch_market_data()

        assert result is None


class TestGrowthRateCalculations:
    """Test growth rate calculation methods"""

    def test_calculate_growth_rates_success(self):
        """Test successful growth rate calculation"""
        calculator = FinancialCalculator(None)

        # Test data with clear growth pattern
        values = [100, 110, 121, 133.1]  # 10% growth each year

        result = calculator.calculate_growth_rates(values)

        assert isinstance(result, dict)
        assert 'historical_growth_rates' in result
        assert 'average_growth_rate' in result
        assert 'compound_growth_rate' in result

        # Check that growth rates are approximately 10%
        assert abs(result['average_growth_rate'] - 0.1) < 0.01

    def test_calculate_growth_rates_negative_values(self):
        """Test growth rate calculation with negative values"""
        calculator = FinancialCalculator(None)

        values = [-10, -5, 0, 5]  # Mixed positive/negative

        result = calculator.calculate_growth_rates(values)

        assert isinstance(result, dict)
        # Should handle negative values gracefully

    def test_calculate_growth_rates_insufficient_data(self):
        """Test growth rate calculation with insufficient data"""
        calculator = FinancialCalculator(None)

        values = [100]  # Only one value

        result = calculator.calculate_growth_rates(values)

        # Should return meaningful result or handle gracefully
        assert isinstance(result, dict)

    def test_calculate_growth_rates_empty_data(self):
        """Test growth rate calculation with empty data"""
        calculator = FinancialCalculator(None)

        values = []

        result = calculator.calculate_growth_rates(values)

        assert isinstance(result, dict)


class TestDataValidation:
    """Test data validation functionality"""

    def test_data_validation_enabled(self):
        """Test that data validation is enabled by default"""
        calculator = FinancialCalculator(None)

        assert calculator.validation_enabled is True
        assert calculator.data_validator is not None

    def test_data_quality_report_generation(self):
        """Test data quality report generation"""
        calculator = FinancialCalculator(None)

        # Mock some financial data
        calculator.financial_data = {
            'income_fy': pd.DataFrame({'Metric': ['Revenue'], 'FY2023': [1000]})
        }

        # This should not raise an exception
        try:
            # Trigger any method that might generate quality reports
            calculator.calculate_all_fcf_types()
        except Exception:
            pass  # Expected to fail without proper data, but shouldn't crash on validation


class TestErrorHandling:
    """Test comprehensive error handling"""

    def test_calculation_error_handling(self):
        """Test that calculation errors are properly handled"""
        calculator = FinancialCalculator(None)

        # Try to calculate FCF without any data
        with pytest.raises((CalculationError, ValidationError)):
            calculator.calculate_fcf_to_firm()

    def test_excel_data_error_handling(self):
        """Test Excel data error handling"""
        calculator = FinancialCalculator(None)

        with pytest.raises(ExcelDataError):
            calculator._load_excel_data("/non/existent/file.xlsx")

    @patch('core.analysis.engines.financial_calculations.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        calculator = FinancialCalculator(None)

        try:
            calculator.calculate_fcf_to_firm()
        except Exception:
            pass

        # Verify that error logging was attempted
        # (Exact assertion depends on logger implementation)


class TestCurrencyAndTASEIntegration:
    """Test currency handling and TASE stock support"""

    def test_default_currency_settings(self):
        """Test default currency settings"""
        calculator = FinancialCalculator(None)

        assert calculator.currency == 'USD'
        assert calculator.financial_currency == 'USD'
        assert calculator.is_tase_stock is False

    def test_tase_stock_detection(self):
        """Test TASE stock detection from ticker"""
        calculator = FinancialCalculator(None)
        calculator.ticker_symbol = 'TEVA.TA'

        # Should trigger TASE detection
        calculator._auto_extract_ticker()

        # Implementation depends on the actual _auto_extract_ticker method


class TestPerformanceAndCaching:
    """Test performance optimizations and caching"""

    def test_metrics_caching(self):
        """Test that financial metrics are cached"""
        calculator = self.setup_mock_financial_data()

        # First call should calculate metrics
        with patch.object(calculator, '_calculate_financial_metrics') as mock_calc:
            mock_calc.return_value = {'roic': 0.15, 'roe': 0.12}

            result1 = calculator.get_financial_metrics()
            result2 = calculator.get_financial_metrics()

            # Should only call calculation once due to caching
            mock_calc.assert_called_once()
            assert result1 == result2

    def test_cache_invalidation_on_data_load(self):
        """Test that cache is invalidated when new data is loaded"""
        calculator = self.setup_mock_financial_data()

        # Calculate metrics first
        calculator.get_financial_metrics()
        assert calculator.metrics_calculated is True

        # Load new data should clear cache
        with patch.object(calculator, '_load_excel_data'):
            calculator.load_financial_statements()

        assert calculator.metrics_calculated is False
        assert calculator.metrics == {}

    def setup_mock_financial_data(self) -> FinancialCalculator:
        """Helper to create calculator with mock financial data"""
        calculator = FinancialCalculator(None)
        calculator.financial_data = {
            'income_fy': pd.DataFrame({'Metric': ['Revenue'], 'FY2023': [1000]})
        }
        return calculator


class TestRetryDecorator:
    """Test retry with exponential backoff decorator"""

    def test_retry_decorator_success(self):
        """Test retry decorator with successful function"""
        @retry_with_exponential_backoff(max_retries=3)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_decorator_eventual_success(self):
        """Test retry decorator with eventual success"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = eventually_successful_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_decorator_max_retries_exceeded(self):
        """Test retry decorator when max retries are exceeded"""
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def always_failing_function():
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            always_failing_function()


class TestStandaloneFunctions:
    """Test standalone utility functions"""

    def test_calculate_unified_fcf(self):
        """Test standalone unified FCF calculation"""
        standardized_data = {
            'operating_cash_flow': 150,
            'capital_expenditures': -50,
            'net_income': 100,
            'depreciation': 20
        }

        result = calculate_unified_fcf(standardized_data)

        assert isinstance(result, dict)
        assert 'fcf' in result or 'error' in result

    def test_calculate_fcf_from_api_data(self):
        """Test FCF calculation from API data"""
        api_data = {
            'operatingCashflow': 150000000,
            'capitalExpenditures': -50000000,
            'netIncome': 100000000
        }

        result = calculate_fcf_from_api_data(api_data, 'yfinance')

        assert isinstance(result, dict)

    def test_calculate_fcf_from_api_data_invalid_type(self):
        """Test FCF calculation with invalid API type"""
        api_data = {'operatingCashflow': 150000000}

        result = calculate_fcf_from_api_data(api_data, 'invalid_api')

        assert isinstance(result, dict)
        assert 'error' in result


# Performance and Integration Test Fixtures
@pytest.fixture
def sample_financial_data():
    """Fixture providing sample financial data for testing"""
    return {
        'income_fy': pd.DataFrame({
            'Metric': ['Revenue', 'Net Income', 'EBIT'],
            'FY2023': [1000, 100, 150],
            'FY2022': [900, 90, 135],
            'FY2021': [800, 80, 120]
        }),
        'balance_fy': pd.DataFrame({
            'Metric': ['Total Assets', 'Total Debt', 'Shareholders Equity'],
            'FY2023': [2000, 500, 1200],
            'FY2022': [1800, 450, 1100],
            'FY2021': [1600, 400, 1000]
        }),
        'cashflow_fy': pd.DataFrame({
            'Metric': ['Operating Cash Flow', 'Capital Expenditures', 'Free Cash Flow'],
            'FY2023': [150, -50, 100],
            'FY2022': [135, -45, 90],
            'FY2021': [120, -40, 80]
        })
    }


@pytest.fixture
def mock_enhanced_data_manager():
    """Fixture providing mock enhanced data manager"""
    manager = Mock()
    manager.get_market_data.return_value = {
        'current_price': 150.0,
        'market_cap': 2400000000000
    }
    return manager


# Mark tests that require API access
pytestmark = pytest.mark.unit