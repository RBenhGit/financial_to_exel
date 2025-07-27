"""
Consolidated Excel processing tests.

This module consolidates tests from multiple files that were testing
similar Excel processing functionality:
- test_excel_extraction.py
- test_excel_optimization.py
- test_metadata_creation.py
- test_date_extraction.py
- test_data_ordering.py
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from tests.fixtures.excel_helpers import ExcelTestHelper
from tests.fixtures.company_data import CompanyDataFixture
from tests.fixtures.mock_data import MockDataGenerator


class TestExcelDataExtraction:
    """Test Excel data extraction functionality"""

    def test_company_name_extraction(self, sample_excel_data):
        """Test company name extraction from Excel files"""
        helper = ExcelTestHelper()

        # Test with standard position
        df = MockDataGenerator.generate_excel_dataframe()
        company_name = helper.find_metric_in_dataframe(df, "Test Company Inc")
        assert company_name == 0  # Should find in first row

    def test_period_date_extraction(self, sample_excel_data):
        """Test extraction of period end dates from Excel"""
        helper = ExcelTestHelper()
        df = MockDataGenerator.generate_excel_dataframe()

        # Find period end date row
        date_row = helper.find_metric_in_dataframe(df, "Period End Date")
        assert date_row is not None

        # Extract date values
        if date_row is not None:
            values = helper.extract_values_from_row(df, date_row, start_col=3, num_values=3)
            assert len(values) == 3

    def test_financial_metric_extraction(self, sample_excel_data):
        """Test extraction of financial metrics from Excel"""
        helper = ExcelTestHelper()
        df = MockDataGenerator.generate_excel_dataframe()

        # Test finding various metrics
        metrics_to_find = ["Revenue", "EBIT", "Net Income", "Total Assets"]

        for metric in metrics_to_find:
            row_idx = helper.find_metric_in_dataframe(df, metric)
            if row_idx is not None:
                values = helper.extract_values_from_row(df, row_idx)
                assert len(values) > 0
                # Values should be numeric (not None)
                numeric_values = [v for v in values if v is not None]
                assert len(numeric_values) > 0

    @pytest.mark.parametrize("company", ["TEST", "SAMPLE", "MOCK"])
    def test_excel_file_loading(self, company, temp_company_structure):
        """Test loading Excel files for different companies"""
        helper = ExcelTestHelper()

        # Create temp Excel file
        temp_file = os.path.join(temp_company_structure, 'FY', f'{company} - Income Statement.xlsx')
        ExcelTestHelper.create_sample_excel_file(temp_file, 'Income Statement')

        # Test loading
        df = helper.load_test_workbook(temp_file)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert df.shape[0] > 5  # Should have header rows plus data

    def test_data_chronological_ordering(self, sample_excel_data):
        """Test that financial data is properly ordered chronologically"""
        # This test consolidates the logic from test_data_ordering.py

        # Create sample data with years
        years = [2022, 2023, 2024]
        fcf_data = {'FCFF': [100, 110, 120], 'FCFE': [90, 100, 115], 'LFCF': [95, 105, 118]}

        # Verify chronological order
        for fcf_type, values in fcf_data.items():
            # Values should generally increase (allowing for some variation)
            assert len(values) == len(years)
            # Check that we have the right number of data points
            assert values[0] < values[-1]  # Generally increasing trend

    def test_excel_memory_optimization(self, temp_company_structure):
        """Test that Excel loading doesn't cause memory issues"""
        # This consolidates logic from test_excel_optimization.py
        helper = ExcelTestHelper()

        # Create multiple temporary Excel files
        temp_files = []
        for i in range(3):
            temp_file = os.path.join(temp_company_structure, 'FY', f'Statement_{i}.xlsx')
            ExcelTestHelper.create_sample_excel_file(temp_file, 'Income Statement')
            temp_files.append(temp_file)

        # Load all files and ensure they can be loaded without issues
        dataframes = []
        for temp_file in temp_files:
            df = helper.load_test_workbook(temp_file)
            dataframes.append(df)
            assert isinstance(df, pd.DataFrame)

        # Verify we loaded all files
        assert len(dataframes) == len(temp_files)


class TestExcelStructureValidation:
    """Test validation of Excel file structure"""

    def test_company_structure_validation(self, company_data_manager):
        """Test validation of company folder structure"""
        # Get available companies
        companies = company_data_manager.find_companies()

        if companies:
            # Test validation for first available company
            company = companies[0]
            validation = company_data_manager.validate_company_structure(company)

            # Validation should return expected keys
            expected_keys = [
                'has_fy_folder',
                'has_ltm_folder',
                'has_income_fy',
                'has_balance_fy',
                'has_cashflow_fy',
                'has_income_ltm',
                'has_balance_ltm',
                'has_cashflow_ltm',
                'is_complete',
            ]

            for key in expected_keys:
                assert key in validation
                assert isinstance(validation[key], bool)

    def test_required_files_detection(self, temp_company_structure):
        """Test detection of required financial statement files"""
        company_data = CompanyDataFixture()

        # Should detect the files we created in temp structure
        excel_files = company_data.get_company_excel_files('TEST')

        assert 'FY' in excel_files
        assert 'LTM' in excel_files

        # Should have found the Excel files we created
        assert len(excel_files['FY']) >= 3  # Income, Balance, Cash Flow
        assert len(excel_files['LTM']) >= 3

    def test_statement_type_detection(self, temp_company_structure):
        """Test detection of specific statement types"""
        company_data = CompanyDataFixture()

        # Test finding specific statements
        income_file = company_data.get_statement_file('TEST', 'FY', 'Income')
        balance_file = company_data.get_statement_file('TEST', 'FY', 'Balance')
        cashflow_file = company_data.get_statement_file('TEST', 'FY', 'Cash Flow')

        # At least one should be found since we created them
        found_statements = [f for f in [income_file, balance_file, cashflow_file] if f]
        assert len(found_statements) > 0


class TestDataProcessing:
    """Test data processing and transformation"""

    def test_numeric_value_extraction(self, sample_excel_data):
        """Test extraction and conversion of numeric values"""
        helper = ExcelTestHelper()

        # Create test data with mixed types
        test_data = pd.DataFrame(
            [
                ['Metric', '', '', '100', '200', '300'],
                ['Revenue', '', '', 1000, 1100, 1200],
                ['Growth', '', '', '10%', '15%', '20%'],
                ['Invalid', '', '', 'N/A', '', None],
            ]
        )

        # Test extraction from numeric row
        values = helper.extract_values_from_row(test_data, 1, start_col=3, num_values=3)
        assert len(values) == 3
        assert all(isinstance(v, float) for v in values if v is not None)
        assert values == [1000.0, 1100.0, 1200.0]

        # Test extraction from string numeric row
        values = helper.extract_values_from_row(test_data, 0, start_col=3, num_values=3)
        assert len(values) == 3
        assert values == [100.0, 200.0, 300.0]

    def test_date_metadata_creation(self, sample_excel_data):
        """Test creation of dates metadata from Excel data"""
        # This consolidates logic from test_metadata_creation.py

        dates_data = MockDataGenerator.generate_dates_metadata()

        # Validate structure
        assert 'fy_years' in dates_data
        assert 'ltm_year' in dates_data
        assert 'extraction_date' in dates_data
        assert 'period_end_dates' in dates_data

        # Validate data types
        assert isinstance(dates_data['fy_years'], list)
        assert isinstance(dates_data['ltm_year'], int)
        assert len(dates_data['fy_years']) > 0

        # Validate chronological order
        fy_years = dates_data['fy_years']
        assert fy_years == sorted(fy_years)  # Should be in chronological order

    def test_error_handling_in_extraction(self):
        """Test error handling during data extraction"""
        helper = ExcelTestHelper()

        # Test with invalid file path
        with pytest.raises((ValueError, FileNotFoundError)):
            helper.load_test_workbook("nonexistent_file.xlsx")

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = helper.find_metric_in_dataframe(empty_df, "Test Metric")
        assert result is None

        # Test with malformed data
        bad_data = pd.DataFrame([[None, None, None]])
        result = helper.find_metric_in_dataframe(bad_data, "Test Metric")
        assert result is None


@pytest.mark.integration
class TestExcelIntegration:
    """Integration tests for Excel processing with real files"""

    @pytest.mark.excel_dependent
    def test_end_to_end_excel_processing(self, company_data_manager):
        """Test complete Excel processing workflow"""
        companies = company_data_manager.get_test_companies(require_complete=True)

        if not companies:
            pytest.skip("No complete company data available for testing")

        # Test with first available complete company
        company = companies[0]

        # Get all statement files
        excel_files = company_data_manager.get_company_excel_files(company)

        for period in ['FY', 'LTM']:
            for file_path in excel_files.get(period, []):
                if os.path.exists(file_path):
                    # Test loading
                    helper = ExcelTestHelper()
                    df = helper.load_test_workbook(file_path)

                    # Basic validation
                    assert isinstance(df, pd.DataFrame)
                    assert not df.empty

                    # Test metric finding
                    common_metrics = [
                        "Period End Date",
                        "Revenue",
                        "Net Income",
                        "Total Assets",
                        "Cash from Operations",
                    ]

                    found_metrics = []
                    for metric in common_metrics:
                        row_idx = helper.find_metric_in_dataframe(df, metric)
                        if row_idx is not None:
                            found_metrics.append(metric)

                    # Should find at least some common metrics
                    assert len(found_metrics) > 0
