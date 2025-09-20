"""
Basic Unit Tests for Financial Calculations Module

Tests core functionality of FinancialCalculator to improve coverage
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from core.analysis.engines.financial_calculations import (
    FinancialCalculator,
    safe_numeric_conversion,
    handle_financial_nan_series
)


class TestSafeNumericConversion:
    """Test safe numeric conversion utility function"""

    def test_valid_numeric_conversion(self):
        assert safe_numeric_conversion(10.5) == 10.5
        assert safe_numeric_conversion("15.7") == 15.7
        assert safe_numeric_conversion(100) == 100.0

    def test_invalid_numeric_conversion(self):
        assert safe_numeric_conversion("invalid") == 0.0
        assert safe_numeric_conversion(None) == 0.0
        assert safe_numeric_conversion("") == 0.0

    def test_custom_default(self):
        assert safe_numeric_conversion("invalid", default=99.9) == 99.9


class TestHandleFinancialNanSeries:
    """Test financial NaN series handling function"""

    def test_clean_series(self):
        series = pd.Series([100.0, 200.0, 300.0])
        result = handle_financial_nan_series(series, "test_metric")
        assert len(result) == 3
        assert result[0] == 100.0

    def test_series_with_nans(self):
        series = pd.Series([100.0, np.nan, 300.0])
        result = handle_financial_nan_series(series, "test_metric")
        assert len(result) == 3
        # NaN is forward-filled to 100.0, then fallback filled
        assert result[1] == 100.0


class TestFinancialCalculatorBasic:
    """Test FinancialCalculator basic functionality"""

    def test_init_with_company_folder(self):
        calc = FinancialCalculator("data/companies/MSFT")
        assert calc.company_folder == "data/companies/MSFT"
        assert calc.company_name == "MSFT"
        assert isinstance(calc.financial_data, dict)

    def test_init_without_company_folder(self):
        calc = FinancialCalculator(None)
        assert calc.company_folder is None
        # The actual implementation returns "Unknown Company"
        assert calc.company_name == "Unknown Company"

    def test_set_validation_enabled(self):
        calc = FinancialCalculator("test")
        calc.set_validation_enabled(True)
        assert calc.validation_enabled is True
        calc.set_validation_enabled(False)
        assert calc.validation_enabled is False

    def test_convert_agorot_to_shekel(self):
        calc = FinancialCalculator("test")
        assert calc.convert_agorot_to_shekel(100) == 1.0
        assert calc.convert_agorot_to_shekel(None) is None

    def test_convert_shekel_to_agorot(self):
        calc = FinancialCalculator("test")
        assert calc.convert_shekel_to_agorot(1.0) == 100.0
        assert calc.convert_shekel_to_agorot(None) is None

    def test_get_currency_info(self):
        calc = FinancialCalculator("test")
        result = calc.get_currency_info()
        assert isinstance(result, dict)
        # The actual keys are 'currency', 'financial_currency', 'is_tase_stock'
        assert 'currency' in result

    def test_looks_like_date(self):
        calc = FinancialCalculator("test")
        # Test with various date formats that the implementation recognizes
        assert calc._looks_like_date("2023") is True  # Year only
        assert calc._looks_like_date("FY2023") is True  # Fiscal year
        assert calc._looks_like_date("not_a_date") is False

    def test_standardize_excel_date(self):
        calc = FinancialCalculator("test")
        result = calc._standardize_excel_date("Dec 2023")
        assert isinstance(result, str)

    @patch('os.path.exists', return_value=True)
    @patch('openpyxl.load_workbook')
    def test_load_excel_data_success(self, mock_load_workbook, mock_exists):
        calc = FinancialCalculator("test")
        # Mock the openpyxl workbook structure
        mock_workbook = Mock()
        mock_worksheet = Mock()
        mock_workbook.active = mock_worksheet
        mock_load_workbook.return_value = mock_workbook

        # Mock the worksheet data
        mock_worksheet.iter_rows.return_value = [
            [Mock(value='Revenue'), Mock(value=1000)],
            [Mock(value='Expenses'), Mock(value=800)]
        ]
        mock_worksheet.max_row = 2
        mock_worksheet.max_column = 2

        result = calc._load_excel_data("test.xlsx")
        assert isinstance(result, pd.DataFrame)

    @patch('openpyxl.load_workbook', side_effect=Exception("File error"))
    def test_load_excel_data_failure(self, mock_load_workbook):
        calc = FinancialCalculator("test")
        result = calc._load_excel_data("invalid.xlsx")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])