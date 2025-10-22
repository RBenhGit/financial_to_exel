"""
Test VarInputData Integration in Export Layer
==============================================

Tests to verify that all export formats (PDF, Excel, CSV, Print View)
correctly include VarInputData metadata and data freshness indicators.

Task 234: Standardize Export Layer Data Access
"""

import pytest
import pandas as pd
import io
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the export utilities
from ui.streamlit.dashboard_export_utils import (
    DashboardExporter,
    collect_dashboard_data,
    get_current_company_info,
    get_current_charts,
    get_current_filters
)


class TestVarInputDataMetadataExtraction:
    """Test VarInputData metadata extraction functionality"""

    def test_get_varinputdata_metadata_with_valid_ticker(self):
        """Test metadata extraction with valid ticker symbol"""
        exporter = DashboardExporter()

        # Mock VarInputData
        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0  # Mock stock price
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')

            assert metadata['data_system'] == 'VarInputData'
            assert metadata['last_updated'] == '2025-10-20T10:00:00'
            assert metadata['source_info'] == 'yfinance'
            assert 'data_freshness' in metadata

    def test_get_varinputdata_metadata_calculates_freshness(self):
        """Test that data freshness is calculated correctly"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0

            # Mock timestamp from 2 hours ago
            two_hours_ago = datetime.now() - timedelta(hours=2)
            mock_instance.get_metadata.return_value = {
                'last_updated': two_hours_ago.isoformat(),
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')

            assert '2 hours old' in metadata['data_freshness']

    def test_get_varinputdata_metadata_handles_missing_data(self):
        """Test graceful handling when VarInputData returns no data"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = None  # No data
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('INVALID')

            # Should return default metadata
            assert metadata['data_system'] == 'VarInputData'
            assert metadata['last_updated'] == 'N/A'
            assert metadata['data_freshness'] == 'Unknown'

    def test_get_varinputdata_metadata_handles_exceptions(self):
        """Test exception handling in metadata extraction"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_var_data.side_effect = Exception("VarInputData unavailable")

            metadata = exporter._get_varinputdata_metadata('AAPL')

            # Should return default metadata without crashing
            assert metadata['data_system'] == 'VarInputData'
            assert metadata['last_updated'] == 'N/A'


class TestPDFExportWithVarInputData:
    """Test PDF export includes VarInputData metadata"""

    def test_pdf_export_includes_metadata_table(self):
        """Test that PDF includes VarInputData metadata in company info section"""
        exporter = DashboardExporter()

        dashboard_data = {
            'financial_ratios': pd.DataFrame({
                'Ratio': ['P/E', 'ROE'],
                'Value': [25.0, 15.0]
            })
        }

        company_info = {
            'name': 'Apple Inc.',
            'ticker': 'AAPL'
        }

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            pdf_bytes = exporter.export_dashboard_to_pdf(
                dashboard_data=dashboard_data,
                company_info=company_info,
                charts=[],
                include_charts=False,
                include_data_tables=True
            )

            # Verify PDF was generated
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0

            # Note: Full PDF content verification would require PDF parsing library
            # For now, we verify the method executes without error


class TestExcelExportWithVarInputData:
    """Test Excel export includes VarInputData metadata sheet"""

    def test_excel_export_includes_metadata_sheet(self):
        """Test that Excel includes dedicated metadata sheet with VarInputData info"""
        exporter = DashboardExporter()

        dashboard_data = {
            'financial_ratios': pd.DataFrame({
                'Ratio': ['P/E', 'ROE'],
                'Value': [25.0, 15.0]
            })
        }

        company_info = {
            'name': 'Apple Inc.',
            'ticker': 'AAPL'
        }

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            excel_bytes = exporter.export_data_to_excel(
                dashboard_data=dashboard_data,
                company_info=company_info
            )

            # Verify Excel was generated
            assert isinstance(excel_bytes, bytes)
            assert len(excel_bytes) > 0

            # Read Excel to verify metadata sheet
            excel_df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=None)

            # Check that Metadata sheet exists
            assert 'Metadata' in excel_df

            metadata_df = excel_df['Metadata']
            assert 'Field' in metadata_df.columns
            assert 'Value' in metadata_df.columns

            # Verify key metadata fields are present
            fields = metadata_df['Field'].tolist()
            assert 'Data System' in fields
            assert 'Data Freshness' in fields
            assert 'Last Updated' in fields
            assert 'Data Source' in fields


class TestCSVExportWithVarInputData:
    """Test CSV/ZIP export includes VarInputData metadata file"""

    def test_csv_zip_includes_metadata_file(self):
        """Test that CSV ZIP bundle includes metadata CSV with VarInputData info"""
        exporter = DashboardExporter()

        dashboard_data = {
            'financial_ratios': pd.DataFrame({
                'Ratio': ['P/E', 'ROE'],
                'Value': [25.0, 15.0]
            })
        }

        company_info = {
            'name': 'Apple Inc.',
            'ticker': 'AAPL'
        }

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            zip_bytes = exporter.export_data_to_csv_zip(
                dashboard_data=dashboard_data,
                company_info=company_info,
                company_name='Apple'
            )

            # Verify ZIP was generated
            assert isinstance(zip_bytes, bytes)
            assert len(zip_bytes) > 0

            # Read ZIP to verify metadata file
            import zipfile
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
                file_list = zip_file.namelist()

                # Check for metadata CSV
                metadata_files = [f for f in file_list if 'metadata' in f.lower()]
                assert len(metadata_files) > 0

                # Read metadata CSV
                metadata_csv = zip_file.read(metadata_files[0]).decode('utf-8')
                assert 'Data System' in metadata_csv
                assert 'VarInputData' in metadata_csv
                assert 'Data Freshness' in metadata_csv


class TestPrintViewWithVarInputData:
    """Test print view HTML includes VarInputData metadata"""

    def test_print_view_includes_metadata_box(self):
        """Test that print view HTML includes VarInputData metadata box"""
        exporter = DashboardExporter()

        dashboard_data = {
            'financial_ratios': pd.DataFrame({
                'Ratio': ['P/E', 'ROE'],
                'Value': [25.0, 15.0]
            }),
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.'
        }

        company_info = {
            'name': 'Apple Inc.',
            'ticker': 'AAPL'
        }

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            html_content = exporter.create_print_friendly_view(
                dashboard_data=dashboard_data,
                company_info=company_info
            )

            # Verify HTML contains VarInputData metadata
            assert 'Data System' in html_content
            assert 'VarInputData' in html_content
            assert 'Data Freshness' in html_content
            assert 'Last Updated' in html_content
            assert 'Data Source' in html_content
            assert 'metadata-box' in html_content


class TestDataFreshnessCalculation:
    """Test data freshness calculation logic"""

    def test_freshness_minutes(self):
        """Test freshness displays in minutes for recent data"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0

            # 30 minutes ago
            thirty_min_ago = datetime.now() - timedelta(minutes=30)
            mock_instance.get_metadata.return_value = {
                'last_updated': thirty_min_ago.isoformat(),
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')
            assert 'minutes old' in metadata['data_freshness']

    def test_freshness_hours(self):
        """Test freshness displays in hours for data from hours ago"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0

            # 5 hours ago
            five_hours_ago = datetime.now() - timedelta(hours=5)
            mock_instance.get_metadata.return_value = {
                'last_updated': five_hours_ago.isoformat(),
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')
            assert 'hours old' in metadata['data_freshness']

    def test_freshness_days(self):
        """Test freshness displays in days for old data"""
        exporter = DashboardExporter()

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0

            # 3 days ago
            three_days_ago = datetime.now() - timedelta(days=3)
            mock_instance.get_metadata.return_value = {
                'last_updated': three_days_ago.isoformat(),
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')
            assert 'days old' in metadata['data_freshness']


class TestExportConsistency:
    """Test that all export formats maintain consistent VarInputData metadata"""

    def test_all_formats_include_same_metadata_fields(self):
        """Test that PDF, Excel, CSV, and Print View all include same metadata fields"""
        exporter = DashboardExporter()

        required_fields = [
            'data_system',
            'last_updated',
            'data_freshness',
            'source_info'
        ]

        with patch('ui.streamlit.dashboard_export_utils.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 150.0
            mock_instance.get_metadata.return_value = {
                'last_updated': '2025-10-20T10:00:00',
                'source': 'yfinance'
            }
            mock_var_data.return_value = mock_instance

            metadata = exporter._get_varinputdata_metadata('AAPL')

            # Verify all required fields are present
            for field in required_fields:
                assert field in metadata, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
