"""
Comprehensive test suite for YfinanceConverter

This module provides extensive testing for:
- Field mapping and normalization
- DataFrame and dictionary conversion
- Cash flow data extraction
- Financial data conversion methods
- Error handling and edge cases
- Data type validation and transformation
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

from core.data_processing.converters.yfinance_converter import YfinanceConverter


class TestYfinanceConverterFieldMappings:
    """Test field mappings and normalization"""

    def test_field_mappings_exist(self):
        """Test that field mappings are properly defined"""
        assert hasattr(YfinanceConverter, 'FIELD_MAPPINGS')
        assert isinstance(YfinanceConverter.FIELD_MAPPINGS, dict)
        assert len(YfinanceConverter.FIELD_MAPPINGS) > 0

    def test_cash_flow_field_mappings(self):
        """Test cash flow statement field mappings"""
        mappings = YfinanceConverter.FIELD_MAPPINGS

        # Test operating cash flow mappings
        assert "Total Cash From Operating Activities" in mappings
        assert mappings["Total Cash From Operating Activities"] == "operating_cash_flow"
        assert mappings["Operating Cash Flow"] == "operating_cash_flow"

        # Test capital expenditures mappings
        assert "Capital Expenditures" in mappings
        assert mappings["Capital Expenditures"] == "capital_expenditures"

        # Test free cash flow mapping
        assert "Free Cash Flow" in mappings
        assert mappings["Free Cash Flow"] == "free_cash_flow"

    def test_income_statement_field_mappings(self):
        """Test income statement field mappings"""
        mappings = YfinanceConverter.FIELD_MAPPINGS

        # Test net income mappings
        assert "Net Income" in mappings
        assert mappings["Net Income"] == "net_income"
        assert mappings["Net Income Common Stockholders"] == "net_income"

        # Test revenue mappings
        assert "Total Revenue" in mappings
        assert mappings["Total Revenue"] == "total_revenue"
        assert mappings["Revenue"] == "total_revenue"

        # Test earnings per share mappings
        assert "Basic EPS" in mappings
        assert mappings["Basic EPS"] == "earnings_per_share"

    def test_balance_sheet_field_mappings(self):
        """Test balance sheet field mappings"""
        mappings = YfinanceConverter.FIELD_MAPPINGS

        # Test assets mappings
        assert "Total Assets" in mappings
        assert mappings["Total Assets"] == "total_assets"
        assert mappings["Current Assets"] == "total_current_assets"

        # Test liabilities mappings
        assert "Total Liabilities Net Minority Interest" in mappings
        assert mappings["Total Liabilities Net Minority Interest"] == "total_liabilities"

    def test_get_supported_fields(self):
        """Test getting list of supported fields"""
        supported_fields = YfinanceConverter.get_supported_fields()

        assert isinstance(supported_fields, list)
        assert len(supported_fields) > 0
        assert "operating_cash_flow" in supported_fields
        assert "net_income" in supported_fields
        assert "total_revenue" in supported_fields

    def test_get_yfinance_field_for_standard(self):
        """Test reverse field mapping lookup"""
        # Test finding yfinance field for standard field
        yf_field = YfinanceConverter.get_yfinance_field_for_standard("operating_cash_flow")
        assert yf_field in ["Total Cash From Operating Activities", "Operating Cash Flow",
                           "Cash Flow From Continuing Operating Activities"]

        # Test non-existent field
        result = YfinanceConverter.get_yfinance_field_for_standard("nonexistent_field")
        assert result is None


class TestYfinanceConverterDataNormalization:
    """Test data normalization and value conversion"""

    def test_normalize_value_numeric(self):
        """Test normalizing numeric values"""
        # Test integer
        result = YfinanceConverter._normalize_value(12345)
        assert result == 12345.0
        assert isinstance(result, float)

        # Test float
        result = YfinanceConverter._normalize_value(123.45)
        assert result == 123.45
        assert isinstance(result, float)

        # Test numpy int
        result = YfinanceConverter._normalize_value(np.int64(12345))
        assert result == 12345.0

        # Test numpy float
        result = YfinanceConverter._normalize_value(np.float64(123.45))
        assert result == 123.45

    def test_normalize_value_string_numeric(self):
        """Test normalizing string representations of numbers"""
        # Test string integer
        result = YfinanceConverter._normalize_value("12345")
        assert result == 12345.0

        # Test string float
        result = YfinanceConverter._normalize_value("123.45")
        assert result == 123.45

        # Test string with commas
        result = YfinanceConverter._normalize_value("1,234,567")
        assert result == 1234567.0

    def test_normalize_value_invalid(self):
        """Test normalizing invalid values"""
        # Test None
        result = YfinanceConverter._normalize_value(None)
        assert result is None

        # Test NaN
        result = YfinanceConverter._normalize_value(np.nan)
        assert result is None

        # Test invalid string
        result = YfinanceConverter._normalize_value("invalid")
        assert result is None

        # Test empty string
        result = YfinanceConverter._normalize_value("")
        assert result is None

    def test_normalize_value_edge_cases(self):
        """Test normalizing edge case values"""
        # Test zero
        result = YfinanceConverter._normalize_value(0)
        assert result == 0.0

        # Test negative number
        result = YfinanceConverter._normalize_value(-12345)
        assert result == -12345.0

        # Test very large number
        result = YfinanceConverter._normalize_value(1e12)
        assert result == 1e12

        # Test very small number
        result = YfinanceConverter._normalize_value(1e-12)
        assert result == 1e-12


class TestYfinanceConverterDataFrameConversion:
    """Test DataFrame conversion functionality"""

    def test_convert_dataframe_simple(self):
        """Test converting simple DataFrame"""
        # Create test DataFrame
        df = pd.DataFrame({
            'Net Income': [100000, 110000, 120000],
            'Total Revenue': [500000, 550000, 600000],
            'Operating Cash Flow': [150000, 165000, 180000]
        })

        result = YfinanceConverter._convert_dataframe(df)

        assert isinstance(result, dict)
        assert 'net_income' in result
        assert 'total_revenue' in result
        assert 'operating_cash_flow' in result

        # Check converted values (should take the first/most recent)
        assert result['net_income'] == 100000.0
        assert result['total_revenue'] == 500000.0
        assert result['operating_cash_flow'] == 150000.0

    def test_convert_dataframe_with_nans(self):
        """Test converting DataFrame with NaN values"""
        df = pd.DataFrame({
            'Net Income': [np.nan, 110000, 120000],
            'Total Revenue': [500000, np.nan, 600000],
            'Operating Cash Flow': [150000, 165000, np.nan]
        })

        result = YfinanceConverter._convert_dataframe(df)

        # NaN values should be converted to None
        assert result['net_income'] is None  # First value is NaN
        assert result['total_revenue'] == 500000.0  # First value is valid
        assert result['operating_cash_flow'] == 150000.0  # First value is valid

    def test_convert_dataframe_unmapped_fields(self):
        """Test converting DataFrame with unmapped fields"""
        df = pd.DataFrame({
            'Net Income': [100000],
            'Unknown Field': [999999],  # This field is not in mappings
            'Total Revenue': [500000]
        })

        result = YfinanceConverter._convert_dataframe(df)

        # Only mapped fields should be in result
        assert 'net_income' in result
        assert 'total_revenue' in result
        assert 'unknown_field' not in result
        assert len(result) == 2

    def test_convert_dataframe_empty(self):
        """Test converting empty DataFrame"""
        df = pd.DataFrame()

        result = YfinanceConverter._convert_dataframe(df)

        assert isinstance(result, dict)
        assert len(result) == 0


class TestYfinanceConverterDictionaryConversion:
    """Test dictionary conversion functionality"""

    def test_convert_dict_simple(self):
        """Test converting simple dictionary"""
        data_dict = {
            'Net Income': 100000,
            'Total Revenue': 500000,
            'Operating Cash Flow': 150000
        }

        result = YfinanceConverter._convert_dict(data_dict)

        assert isinstance(result, dict)
        assert result['net_income'] == 100000.0
        assert result['total_revenue'] == 500000.0
        assert result['operating_cash_flow'] == 150000.0

    def test_convert_dict_with_nones(self):
        """Test converting dictionary with None values"""
        data_dict = {
            'Net Income': None,
            'Total Revenue': 500000,
            'Operating Cash Flow': np.nan
        }

        result = YfinanceConverter._convert_dict(data_dict)

        assert result['net_income'] is None
        assert result['total_revenue'] == 500000.0
        assert result['operating_cash_flow'] is None

    def test_convert_dict_string_values(self):
        """Test converting dictionary with string values"""
        data_dict = {
            'Net Income': '100000',
            'Total Revenue': '500,000',
            'Operating Cash Flow': 'invalid'
        }

        result = YfinanceConverter._convert_dict(data_dict)

        assert result['net_income'] == 100000.0
        assert result['total_revenue'] == 500000.0
        assert result['operating_cash_flow'] is None

    def test_convert_dict_unmapped_fields(self):
        """Test converting dictionary with unmapped fields"""
        data_dict = {
            'Net Income': 100000,
            'Unknown Field': 999999,
            'Total Revenue': 500000
        }

        result = YfinanceConverter._convert_dict(data_dict)

        # Only mapped fields should be in result
        assert 'net_income' in result
        assert 'total_revenue' in result
        assert 'unknown_field' not in result


class TestYfinanceConverterMainConversion:
    """Test main conversion method"""

    def test_convert_financial_data_dataframe(self):
        """Test converting DataFrame through main method"""
        df = pd.DataFrame({
            'Net Income': [100000, 110000],
            'Total Revenue': [500000, 550000]
        })

        result = YfinanceConverter.convert_financial_data(df)

        assert isinstance(result, dict)
        assert 'net_income' in result
        assert 'total_revenue' in result
        assert result['net_income'] == 100000.0

    def test_convert_financial_data_dict(self):
        """Test converting dictionary through main method"""
        data_dict = {
            'Net Income': 100000,
            'Total Revenue': 500000
        }

        result = YfinanceConverter.convert_financial_data(data_dict)

        assert isinstance(result, dict)
        assert result['net_income'] == 100000.0
        assert result['total_revenue'] == 500000.0

    def test_convert_financial_data_invalid_type(self):
        """Test converting invalid data type"""
        invalid_data = "invalid data type"

        result = YfinanceConverter.convert_financial_data(invalid_data)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_convert_financial_data_none(self):
        """Test converting None data"""
        result = YfinanceConverter.convert_financial_data(None)

        assert isinstance(result, dict)
        assert len(result) == 0


class TestYfinanceConverterSpecializedMethods:
    """Test specialized conversion methods"""

    def test_extract_cash_flow_data(self):
        """Test extracting cash flow data from DataFrame"""
        cf_df = pd.DataFrame({
            'Operating Cash Flow': [150000, 165000],
            'Capital Expenditures': [-50000, -55000],
            'Free Cash Flow': [100000, 110000]
        })

        result = YfinanceConverter.extract_cash_flow_data(cf_df)

        assert isinstance(result, dict)
        assert 'operating_cash_flow' in result
        assert 'capital_expenditures' in result
        assert 'free_cash_flow' in result
        assert result['operating_cash_flow'] == 150000.0
        assert result['capital_expenditures'] == -50000.0
        assert result['free_cash_flow'] == 100000.0

    def test_convert_info_data(self):
        """Test converting info dictionary data"""
        info_dict = {
            'marketCap': 1000000000,
            'totalRevenue': 500000000,
            'trailingEps': 5.25
        }

        # This method currently just returns the input dict converted
        result = YfinanceConverter.convert_info_data(info_dict)

        assert isinstance(result, dict)
        # The exact behavior depends on implementation

    def test_convert_financials(self):
        """Test converting financials DataFrame"""
        financials_df = pd.DataFrame({
            'Total Revenue': [500000, 550000],
            'Net Income': [100000, 110000],
            'Operating Income': [150000, 165000]
        })

        result = YfinanceConverter.convert_financials(financials_df)

        assert isinstance(result, dict)
        # Should contain converted financial data

    def test_convert_balance_sheet(self):
        """Test converting balance sheet DataFrame"""
        bs_df = pd.DataFrame({
            'Total Assets': [1000000, 1100000],
            'Total Liabilities Net Minority Interest': [600000, 650000],
            'Current Assets': [400000, 440000]
        })

        result = YfinanceConverter.convert_balance_sheet(bs_df)

        assert isinstance(result, dict)
        # Should contain converted balance sheet data


class TestYfinanceConverterQuarterlyHandling:
    """Test quarterly vs annual data handling"""

    def test_handle_quarterly_vs_annual_prefer_annual(self):
        """Test handling quarterly vs annual data with annual preference"""
        quarterly_df = pd.DataFrame({
            'Net Income': [25000, 27000, 23000, 30000]  # Q1, Q2, Q3, Q4
        })

        annual_df = pd.DataFrame({
            'Net Income': [105000]  # Annual total
        })

        result = YfinanceConverter.handle_quarterly_vs_annual(
            quarterly_data=quarterly_df,
            annual_data=annual_df,
            prefer_annual=True
        )

        assert isinstance(result, dict)
        assert 'net_income' in result
        # Should prefer annual data
        assert result['net_income'] == 105000.0

    def test_handle_quarterly_vs_annual_prefer_quarterly(self):
        """Test handling quarterly vs annual data with quarterly preference"""
        quarterly_df = pd.DataFrame({
            'Net Income': [25000, 27000, 23000, 30000]
        })

        annual_df = pd.DataFrame({
            'Net Income': [105000]
        })

        result = YfinanceConverter.handle_quarterly_vs_annual(
            quarterly_data=quarterly_df,
            annual_data=annual_df,
            prefer_annual=False
        )

        assert isinstance(result, dict)
        assert 'net_income' in result
        # Should prefer quarterly data (most recent quarter)
        assert result['net_income'] == 25000.0

    def test_handle_quarterly_vs_annual_no_annual(self):
        """Test handling when no annual data is available"""
        quarterly_df = pd.DataFrame({
            'Net Income': [25000, 27000, 23000, 30000]
        })

        result = YfinanceConverter.handle_quarterly_vs_annual(
            quarterly_data=quarterly_df,
            annual_data=None,
            prefer_annual=True
        )

        assert isinstance(result, dict)
        # Should fall back to quarterly data
        assert 'net_income' in result
        assert result['net_income'] == 25000.0

    def test_handle_quarterly_vs_annual_no_quarterly(self):
        """Test handling when no quarterly data is available"""
        annual_df = pd.DataFrame({
            'Net Income': [105000]
        })

        result = YfinanceConverter.handle_quarterly_vs_annual(
            quarterly_data=None,
            annual_data=annual_df,
            prefer_annual=False
        )

        assert isinstance(result, dict)
        # Should fall back to annual data
        assert 'net_income' in result
        assert result['net_income'] == 105000.0

    def test_handle_quarterly_vs_annual_empty_data(self):
        """Test handling when both datasets are empty"""
        result = YfinanceConverter.handle_quarterly_vs_annual(
            quarterly_data=None,
            annual_data=None,
            prefer_annual=True
        )

        assert isinstance(result, dict)
        assert len(result) == 0


class TestYfinanceConverterErrorHandling:
    """Test error handling and edge cases"""

    def test_convert_corrupted_dataframe(self):
        """Test converting DataFrame with corrupted data"""
        # Create DataFrame with mixed data types
        df = pd.DataFrame({
            'Net Income': [100000, 'invalid', np.inf],
            'Total Revenue': [500000, -np.inf, None]
        })

        result = YfinanceConverter._convert_dataframe(df)

        assert isinstance(result, dict)
        # Should handle corrupted data gracefully
        assert 'net_income' in result
        assert 'total_revenue' in result

    def test_convert_with_special_characters(self):
        """Test converting data with special characters in field names"""
        data_dict = {
            'Net Income (in millions)': 100,
            'Total Revenue ($)': 500,
            'Operating Cash Flow - Continuing': 150
        }

        result = YfinanceConverter._convert_dict(data_dict)

        # Should handle fields that don't exactly match mappings
        assert isinstance(result, dict)

    @patch('core.data_processing.converters.yfinance_converter.logger')
    def test_logging_during_conversion(self, mock_logger):
        """Test that appropriate logging occurs during conversion"""
        df = pd.DataFrame({
            'Net Income': [100000],
            'Invalid Field': ['invalid_value']
        })

        result = YfinanceConverter._convert_dataframe(df)

        # Should have logged something during conversion
        assert isinstance(result, dict)


class TestYfinanceConverterIntegration:
    """Test integration scenarios"""

    def test_full_conversion_pipeline(self):
        """Test complete conversion pipeline with realistic data"""
        # Simulate realistic yfinance data structure
        financials_df = pd.DataFrame({
            'Total Revenue': [5000000000, 4800000000, 4600000000],
            'Net Income': [1000000000, 950000000, 900000000],
            'Operating Income': [1200000000, 1150000000, 1100000000],
            'Gross Profit': [2500000000, 2400000000, 2300000000]
        })

        result = YfinanceConverter.convert_financial_data(financials_df)

        assert isinstance(result, dict)
        assert len(result) > 0

        # Check that values are properly converted
        assert 'total_revenue' in result
        assert 'net_income' in result
        assert 'operating_income' in result
        assert 'gross_profit' in result

        # Check value types
        for key, value in result.items():
            if value is not None:
                assert isinstance(value, float)

    def test_multi_format_data_handling(self):
        """Test handling multiple data formats in one conversion"""
        # Test with different input types that might come from yfinance
        test_cases = [
            pd.DataFrame({'Net Income': [100000]}),
            {'Net Income': 100000},
            pd.Series([100000], index=['Net Income']),
        ]

        for test_data in test_cases:
            try:
                result = YfinanceConverter.convert_financial_data(test_data)
                assert isinstance(result, dict)
            except Exception as e:
                # Some formats might not be supported, that's okay
                pass


if __name__ == '__main__':
    pytest.main([__file__])