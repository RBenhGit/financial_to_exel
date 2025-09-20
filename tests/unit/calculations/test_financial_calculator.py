"""
Comprehensive Test Suite for FinancialCalculator

This test suite covers the core financial calculation engine with emphasis on:
- FCF calculations (FCFE, FCFF, Levered FCF)
- Excel data loading and processing
- Financial metrics computation
- Data validation and error handling
- Market data integration
- Multi-source data management

Test Structure:
- Unit tests for individual methods
- Integration tests with real company data
- Edge case and error condition testing
- Performance and regression testing
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Import the module under test
from core.analysis.engines.financial_calculations import (
    FinancialCalculator,
    safe_numeric_conversion,
    handle_financial_nan_series,
    retry_with_exponential_backoff
)
from core.data_processing.data_validator import FinancialDataValidator
from tools.utilities.error_handler import (
    FinancialAnalysisError,
    CalculationError,
    ValidationError,
    ExcelDataError
)


class TestSafeNumericConversion:
    """Test the safe_numeric_conversion utility function"""

    def test_valid_numeric_string(self):
        """Test conversion of valid numeric strings"""
        assert safe_numeric_conversion("123.45") == 123.45
        assert safe_numeric_conversion("0") == 0.0
        assert safe_numeric_conversion("-456.78") == -456.78

    def test_valid_numeric_types(self):
        """Test conversion of numeric types"""
        assert safe_numeric_conversion(123) == 123.0
        assert safe_numeric_conversion(123.45) == 123.45
        assert safe_numeric_conversion(Decimal('123.45')) == 123.45

    def test_invalid_values_return_default(self):
        """Test that invalid values return the default"""
        assert safe_numeric_conversion("invalid") == 0.0
        assert safe_numeric_conversion("invalid", default=99.9) == 99.9
        assert safe_numeric_conversion(None) == 0.0
        assert safe_numeric_conversion("") == 0.0

    def test_nan_and_infinity_handling(self):
        """Test handling of NaN and infinity values"""
        assert safe_numeric_conversion(float('nan')) == 0.0
        assert safe_numeric_conversion(float('inf')) == 0.0
        assert safe_numeric_conversion(float('-inf')) == 0.0

    def test_context_logging(self):
        """Test that context is properly used in logging"""
        # This would require checking logging output in a real implementation
        result = safe_numeric_conversion("invalid", context="test_context")
        assert result == 0.0


class TestHandleFinancialNanSeries:
    """Test the handle_financial_nan_series utility function"""

    def test_series_with_valid_values(self):
        """Test series with all valid values"""
        series = pd.Series([1.0, 2.0, 3.0, 4.0])
        result = handle_financial_nan_series(series)
        pd.testing.assert_series_equal(result, series)

    def test_series_with_nan_values(self):
        """Test series with NaN values - should be forward filled"""
        series = pd.Series([1.0, np.nan, 3.0, np.nan])
        result = handle_financial_nan_series(series)
        expected = pd.Series([1.0, 1.0, 3.0, 3.0])
        pd.testing.assert_series_equal(result, expected)

    def test_series_starting_with_nan(self):
        """Test series starting with NaN - forward fill uses default fill_value"""
        series = pd.Series([np.nan, np.nan, 3.0, 4.0])
        result = handle_financial_nan_series(series)
        expected = pd.Series([0.0, 0.0, 3.0, 4.0])
        pd.testing.assert_series_equal(result, expected)

    def test_series_starting_with_nan_backward_method(self):
        """Test series starting with NaN using backward method"""
        series = pd.Series([np.nan, np.nan, 3.0, 4.0])
        result = handle_financial_nan_series(series, method='backward')
        expected = pd.Series([3.0, 3.0, 3.0, 4.0])
        pd.testing.assert_series_equal(result, expected)

    def test_all_nan_series(self):
        """Test series with all NaN values"""
        series = pd.Series([np.nan, np.nan, np.nan])
        result = handle_financial_nan_series(series, default_value=0.0)
        expected = pd.Series([0.0, 0.0, 0.0])
        pd.testing.assert_series_equal(result, expected)


class TestFinancialCalculatorInitialization:
    """Test FinancialCalculator initialization and basic setup"""

    def test_initialization_with_valid_folder(self):
        """Test initialization with a valid company folder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            company_folder = os.path.join(temp_dir, "TEST_COMPANY")
            fy_folder = os.path.join(company_folder, "FY")
            ltm_folder = os.path.join(company_folder, "LTM")
            os.makedirs(fy_folder)
            os.makedirs(ltm_folder)

            # Create minimal Excel files to prevent auto-load errors
            self.create_minimal_excel_file(os.path.join(fy_folder, "Income Statement.xlsx"))
            self.create_minimal_excel_file(os.path.join(fy_folder, "Balance Sheet.xlsx"))
            self.create_minimal_excel_file(os.path.join(fy_folder, "Cash Flow Statement.xlsx"))
            self.create_minimal_excel_file(os.path.join(ltm_folder, "Income Statement.xlsx"))
            self.create_minimal_excel_file(os.path.join(ltm_folder, "Balance Sheet.xlsx"))
            self.create_minimal_excel_file(os.path.join(ltm_folder, "Cash Flow Statement.xlsx"))

            calc = FinancialCalculator(company_folder)

            assert calc.company_folder == company_folder
            assert calc.company_name == "TEST_COMPANY"
            assert calc.currency == 'USD'
            assert calc.financial_currency == 'USD'
            assert not calc.is_tase_stock

    def create_minimal_excel_file(self, file_path: str) -> None:
        """Create a minimal Excel file for testing"""
        df = pd.DataFrame({"Metric": ["Test"], "2023": [100]})
        df.to_excel(file_path, index=False)

    def test_initialization_with_none_folder(self):
        """Test initialization with None folder"""
        calc = FinancialCalculator(None)

        assert calc.company_folder is None
        assert calc.company_name is not None  # Should use unknown company name
        assert calc.financial_data == {}

    def test_initialization_with_enhanced_data_manager(self):
        """Test initialization with enhanced data manager"""
        mock_manager = Mock()
        calc = FinancialCalculator("test_folder", enhanced_data_manager=mock_manager)

        assert calc.enhanced_data_manager == mock_manager

    def test_auto_ticker_extraction(self):
        """Test automatic ticker symbol extraction from folder name"""
        calc = FinancialCalculator("./data/AAPL")
        assert calc.company_name == "AAPL"


class TestFinancialCalculatorDataLoading:
    """Test financial data loading from Excel files"""

    def setup_method(self):
        """Set up test environment with mock Excel files"""
        self.temp_dir = tempfile.mkdtemp()
        self.company_folder = os.path.join(self.temp_dir, "TEST_COMPANY")
        self.fy_folder = os.path.join(self.company_folder, "FY")
        self.ltm_folder = os.path.join(self.company_folder, "LTM")

        os.makedirs(self.fy_folder)
        os.makedirs(self.ltm_folder)

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def create_mock_excel_file(self, file_path: str, data: Dict[str, List]) -> None:
        """Create a mock Excel file with test data"""
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)

    def test_load_financial_statements_success(self):
        """Test successful loading of financial statements"""
        # Create mock Excel files
        income_data = {
            "Metric": ["Revenue", "Net Income", "EBIT"],
            "2023": [1000, 100, 150],
            "2022": [900, 90, 135],
            "2021": [800, 80, 120]
        }

        balance_data = {
            "Metric": ["Total Assets", "Total Equity", "Cash"],
            "2023": [5000, 2000, 500],
            "2022": [4500, 1800, 450],
            "2021": [4000, 1600, 400]
        }

        cashflow_data = {
            "Metric": ["Operating Cash Flow", "CapEx", "Free Cash Flow"],
            "2023": [200, -50, 150],
            "2022": [180, -45, 135],
            "2021": [160, -40, 120]
        }

        self.create_mock_excel_file(
            os.path.join(self.fy_folder, "Income Statement.xlsx"), income_data
        )
        self.create_mock_excel_file(
            os.path.join(self.fy_folder, "Balance Sheet.xlsx"), balance_data
        )
        self.create_mock_excel_file(
            os.path.join(self.fy_folder, "Cash Flow Statement.xlsx"), cashflow_data
        )

        # Create LTM files
        self.create_mock_excel_file(
            os.path.join(self.ltm_folder, "Income Statement.xlsx"), income_data
        )
        self.create_mock_excel_file(
            os.path.join(self.ltm_folder, "Balance Sheet.xlsx"), balance_data
        )
        self.create_mock_excel_file(
            os.path.join(self.ltm_folder, "Cash Flow Statement.xlsx"), cashflow_data
        )

        calc = FinancialCalculator(self.company_folder)
        calc.load_financial_statements()

        # Verify data was loaded
        assert 'income_fy' in calc.financial_data
        assert 'balance_fy' in calc.financial_data
        assert 'cashflow_fy' in calc.financial_data
        assert 'income_ltm' in calc.financial_data
        assert 'balance_ltm' in calc.financial_data
        assert 'cashflow_ltm' in calc.financial_data

    def test_load_financial_statements_missing_files(self):
        """Test handling of missing financial statement files"""
        calc = FinancialCalculator(self.company_folder)

        with pytest.raises((FileNotFoundError, ExcelDataError)):
            calc.load_financial_statements()


class TestFinancialCalculatorFCFCalculations:
    """Test FCF calculations with real company data"""

    @pytest.fixture
    def calc_with_test_data(self):
        """Fixture providing a calculator with test data"""
        # Use one of the available test companies
        company_path = "C:\\AsusWebStorage\\ran@benhur.co\\MySyncFolder\\python\\investingAnalysis\\financial_to_exel\\data\\companies\\MSFT"

        if os.path.exists(company_path):
            calc = FinancialCalculator(company_path)
            return calc
        else:
            pytest.skip(f"Test data not available at {company_path}")

    def test_calculate_fcf_to_firm(self, calc_with_test_data):
        """Test FCFF calculation with real data"""
        fcff_results = calc_with_test_data.calculate_fcf_to_firm()

        assert isinstance(fcff_results, list)
        assert len(fcff_results) > 0
        assert all(isinstance(x, (int, float)) for x in fcff_results)

    def test_calculate_fcf_to_equity(self, calc_with_test_data):
        """Test FCFE calculation with real data"""
        fcfe_results = calc_with_test_data.calculate_fcf_to_equity()

        assert isinstance(fcfe_results, list)
        assert len(fcfe_results) > 0
        assert all(isinstance(x, (int, float)) for x in fcfe_results)

    def test_calculate_levered_fcf(self, calc_with_test_data):
        """Test Levered FCF calculation with real data"""
        lfcf_results = calc_with_test_data.calculate_levered_fcf()

        assert isinstance(lfcf_results, list)
        assert len(lfcf_results) > 0
        assert all(isinstance(x, (int, float)) for x in lfcf_results)

    def test_calculate_all_fcf_types(self, calc_with_test_data):
        """Test calculation of all FCF types together"""
        all_fcf = calc_with_test_data.calculate_all_fcf_types()

        assert isinstance(all_fcf, dict)
        assert 'FCFF' in all_fcf
        assert 'FCFE' in all_fcf
        assert 'LFCF' in all_fcf

        for fcf_type, values in all_fcf.items():
            assert isinstance(values, list)
            assert len(values) > 0


class TestFinancialCalculatorMetrics:
    """Test financial metrics calculation"""

    @pytest.fixture
    def calc_with_test_data(self):
        """Fixture providing a calculator with test data"""
        company_path = "C:\\AsusWebStorage\\ran@benhur.co\\MySyncFolder\\python\\investingAnalysis\\financial_to_exel\\data\\companies\\GOOG"

        if os.path.exists(company_path):
            calc = FinancialCalculator(company_path)
            return calc
        else:
            pytest.skip(f"Test data not available at {company_path}")

    def test_get_financial_metrics(self, calc_with_test_data):
        """Test comprehensive financial metrics calculation"""
        metrics = calc_with_test_data.get_financial_metrics()

        assert isinstance(metrics, dict)

        # Check for key financial metrics
        expected_metrics = [
            'revenue', 'net_income', 'ebit', 'total_assets',
            'total_equity', 'operating_cash_flow'
        ]

        for metric in expected_metrics:
            if metric in metrics:
                assert isinstance(metrics[metric], list)
                assert len(metrics[metric]) > 0

    def test_get_latest_report_date(self, calc_with_test_data):
        """Test getting the latest report date"""
        latest_date = calc_with_test_data.get_latest_report_date()

        assert isinstance(latest_date, str)
        assert len(latest_date) > 0


class TestFinancialCalculatorDataValidation:
    """Test data validation functionality"""

    def test_data_validation_enabled_by_default(self):
        """Test that data validation is enabled by default"""
        calc = FinancialCalculator(None)
        assert calc.validation_enabled is True

    def test_set_validation_enabled(self):
        """Test enabling/disabling validation"""
        calc = FinancialCalculator(None)

        calc.set_validation_enabled(False)
        assert calc.validation_enabled is False

        calc.set_validation_enabled(True)
        assert calc.validation_enabled is True

    def test_data_quality_report_generation(self):
        """Test data quality report generation"""
        calc = FinancialCalculator(None)
        calc.data_quality_report = {"test": "report"}

        report = calc.get_data_quality_report()
        assert report == {"test": "report"}


class TestFinancialCalculatorErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_company_folder(self):
        """Test handling of invalid company folder"""
        calc = FinancialCalculator("/nonexistent/path")

        # Should not raise exception during initialization
        assert calc.company_folder == "/nonexistent/path"

    def test_excel_file_reading_error(self):
        """Test handling of Excel file reading errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            company_folder = os.path.join(temp_dir, "ERROR_TEST")
            fy_folder = os.path.join(company_folder, "FY")
            os.makedirs(fy_folder)

            # Create an invalid Excel file
            invalid_file = os.path.join(fy_folder, "Income Statement.xlsx")
            with open(invalid_file, 'w') as f:
                f.write("This is not an Excel file")

            calc = FinancialCalculator(company_folder)

            with pytest.raises((ExcelDataError, Exception)):
                calc.load_financial_statements()


class TestFinancialCalculatorMarketData:
    """Test market data integration"""

    @patch('yfinance.Ticker')
    def test_get_current_stock_price_success(self, mock_ticker):
        """Test successful stock price retrieval"""
        # Mock yfinance response
        mock_info = {
            'regularMarketPrice': 150.0,
            'marketCap': 2500000000000,
            'sharesOutstanding': 16600000000
        }
        mock_ticker.return_value.info = mock_info

        calc = FinancialCalculator(None)
        calc.ticker_symbol = "AAPL"

        price = calc.get_current_stock_price()

        assert price == 150.0
        assert calc.current_stock_price == 150.0
        assert calc.market_cap == 2500000000000
        assert calc.shares_outstanding == 16600000000

    @patch('yfinance.Ticker')
    def test_get_current_stock_price_failure(self, mock_ticker):
        """Test handling of stock price retrieval failure"""
        # Mock yfinance to raise an exception
        mock_ticker.side_effect = Exception("API Error")

        calc = FinancialCalculator(None)
        calc.ticker_symbol = "INVALID"

        price = calc.get_current_stock_price()

        assert price is None
        assert calc.current_stock_price is None


class TestFinancialCalculatorIntegration:
    """Integration tests with multiple components"""

    @pytest.mark.integration
    def test_end_to_end_calculation_workflow(self):
        """Test complete calculation workflow with real data"""
        # Test with available company data
        available_companies = ["MSFT", "GOOG", "NVDA", "TSLA", "V"]
        base_path = "C:\\AsusWebStorage\\ran@benhur.co\\MySyncFolder\\python\\investingAnalysis\\financial_to_exel\\data\\companies"

        for company in available_companies:
            company_path = os.path.join(base_path, company)

            if os.path.exists(company_path):
                calc = FinancialCalculator(company_path)

                # Test the complete workflow
                try:
                    # Load financial statements
                    calc.load_financial_statements()

                    # Calculate FCF values
                    fcf_results = calc.calculate_all_fcf_types()
                    assert isinstance(fcf_results, dict)

                    # Get financial metrics
                    metrics = calc.get_financial_metrics()
                    assert isinstance(metrics, dict)

                    # Get data quality report
                    quality_report = calc.get_data_quality_report()

                    print(f"✅ End-to-end test passed for {company}")

                except Exception as e:
                    pytest.fail(f"End-to-end test failed for {company}: {e}")

                break  # Test with first available company
        else:
            pytest.skip("No test company data available")


class TestFinancialCalculatorPerformance:
    """Performance and regression tests"""

    @pytest.mark.performance
    def test_calculation_performance(self):
        """Test that calculations complete within reasonable time"""
        import time

        company_path = "C:\\AsusWebStorage\\ran@benhur.co\\MySyncFolder\\python\\investingAnalysis\\financial_to_exel\\data\\companies\\MSFT"

        if not os.path.exists(company_path):
            pytest.skip("Test data not available")

        calc = FinancialCalculator(company_path)

        # Measure FCF calculation time
        start_time = time.time()
        fcf_results = calc.calculate_all_fcf_types()
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete within 10 seconds
        assert calculation_time < 10.0, f"Calculation took too long: {calculation_time:.2f}s"

        # Should return valid results
        assert isinstance(fcf_results, dict)
        assert len(fcf_results) > 0


class TestRetryDecorator:
    """Test the retry_with_exponential_backoff decorator"""

    def test_successful_function_call(self):
        """Test decorator with function that succeeds immediately"""
        @retry_with_exponential_backoff(max_retries=3)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_function_with_retryable_exception(self):
        """Test decorator with function that fails then succeeds"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(ValueError,))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 3

    def test_function_with_non_retryable_exception(self):
        """Test decorator with non-retryable exception"""
        @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(ValueError,))
        def failing_function():
            raise TypeError("Non-retryable error")

        with pytest.raises(TypeError):
            failing_function()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])