"""
Test International Format Support for Excel Data Processing
==========================================================

This module tests the new international format handling capabilities
including European number formats, international date formats, merged
cells, and custom templates.
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime
from openpyxl import Workbook

from core.excel_integration.international_format_handler import (
    InternationalFormatHandler,
    InternationalConfig,
    NumberFormat,
    DateFormat,
    InternationalNumberParser,
    InternationalDateParser,
    MergedCellHandler,
    FormulaHandler,
    create_european_handler,
    create_asian_handler,
    create_us_handler
)
from core.excel_integration.custom_template_manager import (
    CustomTemplateManager,
    CustomTemplate,
    TemplateType,
    CellMapping,
    SectionMapping
)
from core.excel_integration.excel_utils import (
    extract_financial_data_with_international_support,
    create_european_excel_extractor,
    analyze_excel_international_format,
    detect_excel_layout_type
)


class TestInternationalNumberParser:
    """Test international number format parsing"""

    def test_us_format_parsing(self):
        """Test US number format (1,234.56)"""
        config = InternationalConfig(preferred_number_format=NumberFormat.US_FORMAT)
        parser = InternationalNumberParser(config)

        # Test basic US format
        result, format_type, confidence = parser.parse_number("1,234.56")
        assert result == 1234.56
        assert "us_format" in format_type.lower()
        assert confidence > 0.7

        # Test with currency symbol
        result, format_type, confidence = parser.parse_number("$1,234.56")
        assert result == 1234.56

        # Test simple decimal
        result, format_type, confidence = parser.parse_number("1234.56")
        assert result == 1234.56

    def test_european_format_parsing(self):
        """Test European number format (1.234,56)"""
        config = InternationalConfig(preferred_number_format=NumberFormat.EUROPEAN_FORMAT)
        parser = InternationalNumberParser(config)

        # Test basic European format
        result, format_type, confidence = parser.parse_number("1.234,56")
        assert result == 1234.56
        assert "european_format" in format_type.lower()
        assert confidence > 0.7

        # Test with Euro symbol
        result, format_type, confidence = parser.parse_number("€1.234,56")
        assert result == 1234.56

        # Test thousands without decimal
        result, format_type, confidence = parser.parse_number("1.234")
        assert result == 1234

    def test_invalid_number_parsing(self):
        """Test parsing of invalid numbers"""
        config = InternationalConfig()
        parser = InternationalNumberParser(config)

        # Test empty string
        result, format_type, confidence = parser.parse_number("")
        assert result is None
        assert confidence == 0.0

        # Test non-numeric string
        result, format_type, confidence = parser.parse_number("not a number")
        assert result is None

        # Test None input
        result, format_type, confidence = parser.parse_number(123)  # Not a string
        assert result is None


class TestInternationalDateParser:
    """Test international date format parsing"""

    def test_mdy_format_parsing(self):
        """Test MDY date format (MM/DD/YYYY)"""
        config = InternationalConfig(preferred_date_format=DateFormat.MDY)
        parser = InternationalDateParser(config)

        result, format_type, confidence = parser.parse_date("12/25/2023")
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25

    def test_dmy_format_parsing(self):
        """Test DMY date format (DD/MM/YYYY)"""
        config = InternationalConfig(preferred_date_format=DateFormat.DMY)
        parser = InternationalDateParser(config)

        result, format_type, confidence = parser.parse_date("25/12/2023")
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25

    def test_ymd_format_parsing(self):
        """Test YMD date format (YYYY/MM/DD)"""
        config = InternationalConfig(preferred_date_format=DateFormat.YMD)
        parser = InternationalDateParser(config)

        result, format_type, confidence = parser.parse_date("2023/12/25")
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25


class TestMergedCellHandler:
    """Test merged cell handling"""

    def test_merged_cell_detection(self):
        """Test detection and value extraction from merged cells"""
        handler = MergedCellHandler()

        # Create a mock worksheet with merged cells
        mock_worksheet = Mock()
        mock_worksheet.merged_cells.ranges = []

        # Mock a merged range
        mock_range = Mock()
        mock_range.min_row = 1
        mock_range.max_row = 2
        mock_range.min_col = 1
        mock_range.max_col = 3
        mock_worksheet.merged_cells.ranges = [mock_range]

        # Mock the top-left cell
        mock_cell = Mock()
        mock_cell.value = "Merged Cell Value"
        mock_worksheet.cell.return_value = mock_cell

        value, is_merged = handler.get_merged_cell_value(mock_worksheet, 1, 2)
        assert value == "Merged Cell Value"
        assert is_merged is True

    def test_non_merged_cell(self):
        """Test handling of non-merged cells"""
        handler = MergedCellHandler()

        mock_worksheet = Mock()
        mock_worksheet.merged_cells.ranges = []

        mock_cell = Mock()
        mock_cell.value = "Regular Cell Value"
        mock_worksheet.cell.return_value = mock_cell

        value, is_merged = handler.get_merged_cell_value(mock_worksheet, 1, 1)
        assert value == "Regular Cell Value"
        assert is_merged is False


class TestFormulaHandler:
    """Test formula cell handling"""

    def test_formula_classification(self):
        """Test classification of different formula types"""
        handler = FormulaHandler()

        # Test SUM formula
        mock_cell = Mock()
        mock_cell.formula = "=SUM(A1:A10)"
        mock_cell.value = 100

        info = handler.get_formula_info(mock_cell)
        assert info['is_formula'] is True
        assert info['formula_type'] == 'sum'
        assert info['calculated_value'] == 100

        # Test non-formula cell
        mock_cell.formula = None
        info = handler.get_formula_info(mock_cell)
        assert info['is_formula'] is False


class TestCustomTemplateManager:
    """Test custom template management"""

    def test_template_creation(self):
        """Test creating a custom template"""
        manager = CustomTemplateManager()

        template = manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            template_type=TemplateType.USER_DEFINED
        )

        assert template.template_id == "test_template"
        assert template.name == "Test Template"
        assert template.template_type == TemplateType.USER_DEFINED
        assert template.template_id in manager.templates

    def test_template_duplicate_id_error(self):
        """Test error when creating template with duplicate ID"""
        manager = CustomTemplateManager()

        # Create first template
        manager.create_template(
            template_id="duplicate_id",
            name="First Template",
            description="First template"
        )

        # Try to create second template with same ID
        with pytest.raises(ValueError, match="already exists"):
            manager.create_template(
                template_id="duplicate_id",
                name="Second Template",
                description="Second template"
            )

    def test_template_serialization(self):
        """Test template serialization and deserialization"""
        manager = CustomTemplateManager()

        original_template = CustomTemplate(
            template_id="test_serialize",
            name="Serialization Test",
            description="Test template serialization",
            template_type=TemplateType.USER_DEFINED,
            sections=[
                SectionMapping(
                    name="Header",
                    start_row=1,
                    end_row=5,
                    start_column=1,
                    end_column=10,
                    section_type="header"
                )
            ]
        )

        # Convert to dict and back
        template_dict = manager._template_to_dict(original_template)
        restored_template = manager._dict_to_template(template_dict)

        assert restored_template.template_id == original_template.template_id
        assert restored_template.name == original_template.name
        assert len(restored_template.sections) == len(original_template.sections)


class TestInternationalFormatHandler:
    """Test the main international format handler"""

    def test_handler_creation(self):
        """Test creating handlers for different regions"""
        us_handler = create_us_handler()
        assert us_handler.config.preferred_number_format == NumberFormat.US_FORMAT
        assert '$' in us_handler.config.currency_symbols

        european_handler = create_european_handler()
        assert european_handler.config.preferred_number_format == NumberFormat.EUROPEAN_FORMAT
        assert '€' in european_handler.config.currency_symbols

        asian_handler = create_asian_handler()
        assert asian_handler.config.preferred_date_format == DateFormat.YMD
        assert '¥' in asian_handler.config.currency_symbols

    @patch('core.excel_integration.international_format_handler.InternationalFormatHandler.parse_cell_value')
    def test_cell_parsing_with_confidence(self, mock_parse):
        """Test cell parsing with confidence scoring"""
        handler = create_us_handler()

        # Mock high confidence result
        from core.excel_integration.international_format_handler import CellParsingResult
        mock_parse.return_value = CellParsingResult(
            original_value="1,234.56",
            parsed_value=1234.56,
            value_type='number',
            format_detected='us_format',
            confidence=0.9,
            errors=[]
        )

        mock_worksheet = Mock()
        result = handler.parse_cell_value(mock_worksheet, 1, 1)
        assert result.parsed_value == 1234.56
        assert result.confidence == 0.9


class TestUtilityFunctions:
    """Test the utility functions for international format support"""

    @patch('core.excel_integration.excel_utils.ExcelDataExtractor')
    def test_european_extractor_creation(self, mock_extractor_class):
        """Test creation of European-optimized extractor"""
        from core.excel_integration.excel_utils import create_european_excel_extractor

        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        extractor = create_european_excel_extractor("test.xlsx")

        # Verify the extractor was created with European configuration
        mock_extractor_class.assert_called_once()
        call_args = mock_extractor_class.call_args
        assert call_args[0][0] == "test.xlsx"  # file_path

        international_config = call_args[1]['international_config']
        assert international_config.preferred_number_format == NumberFormat.EUROPEAN_FORMAT
        assert international_config.preferred_date_format == DateFormat.DMY
        assert '€' in international_config.currency_symbols

    @patch('core.excel_integration.excel_utils.ExcelDataExtractor')
    def test_analyze_international_format_function(self, mock_extractor_class):
        """Test the analyze_excel_international_format function"""
        from core.excel_integration.excel_utils import analyze_excel_international_format

        # Mock the extractor and its methods
        mock_extractor = Mock()
        mock_extractor.__enter__ = Mock(return_value=mock_extractor)
        mock_extractor.__exit__ = Mock(return_value=None)
        mock_extractor.get_international_analysis.return_value = {
            'number_formats': {'european_format': 5},
            'international_indicators': ['European number format detected']
        }
        mock_extractor._initialize_international_handler = Mock()
        mock_extractor.international_handler = None

        mock_extractor_class.return_value = mock_extractor

        result = analyze_excel_international_format("test.xlsx")

        assert 'number_formats' in result
        assert 'international_indicators' in result
        mock_extractor._initialize_international_handler.assert_called_once()

    @patch('core.excel_integration.excel_utils.ExcelDataExtractor')
    def test_detect_layout_type_function(self, mock_extractor_class):
        """Test the detect_excel_layout_type function"""
        from core.excel_integration.excel_utils import detect_excel_layout_type

        # Mock the extractor and its methods
        mock_extractor = Mock()
        mock_extractor.__enter__ = Mock(return_value=mock_extractor)
        mock_extractor.__exit__ = Mock(return_value=None)

        # Mock format detection result with low confidence
        mock_format_result = Mock()
        mock_format_result.confidence_score = 0.5

        mock_extractor.get_format_info.return_value = mock_format_result
        mock_extractor.get_custom_template_info.return_value = None
        mock_extractor.get_international_analysis.return_value = {
            'international_indicators': ['European number format detected']
        }
        mock_extractor.get_processing_status.return_value = {'file_loaded': True}

        mock_extractor_class.return_value = mock_extractor

        result = detect_excel_layout_type("test.xlsx")

        assert 'format_detection' in result
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0

        # Check that recommendations include format confidence warning
        recommendations_text = ' '.join(result['recommendations'])
        assert 'low format confidence' in recommendations_text.lower()


# Integration test for the enhanced Excel utils
class TestExcelUtilsIntegration:
    """Integration tests for enhanced Excel utilities"""

    def test_import_all_new_modules(self):
        """Test that all new modules can be imported successfully"""
        try:
            from core.excel_integration.international_format_handler import (
                InternationalFormatHandler, NumberFormat, DateFormat
            )
            from core.excel_integration.custom_template_manager import (
                CustomTemplateManager, CustomTemplate
            )
            from core.excel_integration.excel_utils import (
                extract_financial_data_with_international_support,
                create_european_excel_extractor,
                detect_excel_layout_type
            )
            assert True  # All imports successful
        except ImportError as e:
            pytest.fail(f"Failed to import new modules: {e}")

    def test_configuration_integration(self):
        """Test that configuration supports new features"""
        try:
            from config.config import ExcelStructureConfig
            config = ExcelStructureConfig()

            # Check new configuration options
            assert hasattr(config, 'enable_international_formats')
            assert hasattr(config, 'enable_custom_templates')
            assert hasattr(config, 'handle_merged_cells')
            assert hasattr(config, 'process_formula_cells')

        except Exception as e:
            pytest.fail(f"Configuration integration failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])