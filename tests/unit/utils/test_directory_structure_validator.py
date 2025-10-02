"""
Unit tests for DirectoryStructureValidator (Task 180)

Tests the enhanced directory structure validation system including:
- Directory structure validation
- Excel file format validation
- Compliance reporting
- Actionable recommendations
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from openpyxl import Workbook

from utils.directory_structure_helper import (
    DirectoryStructureValidator,
    validate_company_directory,
    create_directory_structure_template
)


class TestDirectoryStructureValidator:
    """Test suite for DirectoryStructureValidator"""

    @pytest.fixture
    def temp_company_dir(self):
        """Create temporary company directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return DirectoryStructureValidator()

    @pytest.fixture
    def valid_company_structure(self, temp_company_dir):
        """Create a valid company directory structure"""
        company_path = Path(temp_company_dir) / "TEST"
        company_path.mkdir(parents=True, exist_ok=True)

        for period in ['FY', 'LTM']:
            period_path = company_path / period
            period_path.mkdir(exist_ok=True)

            for statement in ["Income Statement.xlsx", "Balance Sheet.xlsx", "Cash Flow Statement.xlsx"]:
                file_path = period_path / statement
                self._create_valid_excel_file(file_path, statement)

        return company_path

    def _create_valid_excel_file(self, file_path: Path, statement_type: str):
        """Helper to create a valid Excel file with proper structure"""
        wb = Workbook()
        ws = wb.active

        # Add proper column headers
        headers = ['Metric', 'FY', 'FY-1', 'FY-2', 'FY-3']
        ws.append(headers)

        # Add sample data based on statement type
        if "Income Statement" in statement_type:
            ws.append(['Revenue', 1000, 900, 800, 700])
            ws.append(['Net Income', 100, 90, 80, 70])
            ws.append(['Operating Income', 150, 135, 120, 105])
        elif "Balance Sheet" in statement_type:
            ws.append(['Total Assets', 5000, 4500, 4000, 3500])
            ws.append(['Total Liabilities', 3000, 2700, 2400, 2100])
            ws.append(['Shareholders Equity', 2000, 1800, 1600, 1400])
        elif "Cash Flow" in statement_type:
            ws.append(['Cash from Operations', 200, 180, 160, 140])
            ws.append(['Capital Expenditures', 50, 45, 40, 35])

        wb.save(file_path)

    # === Basic Directory Validation Tests ===

    def test_validate_nonexistent_directory(self, validator):
        """Test validation of nonexistent company directory"""
        result = validator.validate_company_directory("/nonexistent/path/FAKE")

        assert not result['is_valid']
        assert not result['exists']
        assert len(result['issues']) > 0
        assert any('does not exist' in issue['message'] for issue in result['issues'])

    def test_validate_valid_directory_structure(self, validator, valid_company_structure):
        """Test validation of properly structured company directory"""
        result = validator.validate_company_directory(str(valid_company_structure))

        assert result['is_valid']
        assert result['exists']
        assert len(result['missing_folders']) == 0
        assert result['structure_score'] > 0.8
        assert '✅' in result['validation_summary']

    def test_validate_missing_fy_folder(self, validator, temp_company_dir):
        """Test validation when FY folder is missing"""
        company_path = Path(temp_company_dir) / "TEST_NO_FY"
        company_path.mkdir(parents=True)

        # Only create LTM folder
        ltm_path = company_path / "LTM"
        ltm_path.mkdir()

        result = validator.validate_company_directory(str(company_path))

        assert not result['is_valid']
        assert 'FY' in result['missing_folders']
        assert len([i for i in result['issues'] if 'FY' in i['message']]) > 0

    def test_validate_missing_ltm_folder(self, validator, temp_company_dir):
        """Test validation when LTM folder is missing"""
        company_path = Path(temp_company_dir) / "TEST_NO_LTM"
        company_path.mkdir(parents=True)

        # Only create FY folder
        fy_path = company_path / "FY"
        fy_path.mkdir()

        result = validator.validate_company_directory(str(company_path))

        assert not result['is_valid']
        assert 'LTM' in result['missing_folders']
        assert len([i for i in result['issues'] if 'LTM' in i['message']]) > 0

    def test_validate_missing_excel_files(self, validator, temp_company_dir):
        """Test validation when Excel files are missing"""
        company_path = Path(temp_company_dir) / "TEST_NO_FILES"
        company_path.mkdir(parents=True)

        # Create folders but no files
        for period in ['FY', 'LTM']:
            (company_path / period).mkdir()

        result = validator.validate_company_directory(str(company_path), strict_mode=True)

        assert not result['is_valid']
        assert len(result['missing_files']) > 0
        assert result['structure_score'] < 0.5

    def test_structure_score_calculation(self, validator, temp_company_dir):
        """Test structure completeness score calculation"""
        company_path = Path(temp_company_dir) / "TEST_SCORE"
        company_path.mkdir(parents=True)

        # Create only FY folder with only 1 file
        fy_path = company_path / "FY"
        fy_path.mkdir()
        self._create_valid_excel_file(fy_path / "Income Statement.xlsx", "Income Statement.xlsx")

        result = validator.validate_company_directory(str(company_path))

        # Should have partial score: 1 folder out of 2, 1 file out of 6
        assert 0.1 < result['structure_score'] < 0.5

    # === Excel File Format Validation Tests ===

    def test_validate_excel_file_format_valid(self, validator, temp_company_dir):
        """Test validation of properly formatted Excel file"""
        file_path = Path(temp_company_dir) / "test.xlsx"
        self._create_valid_excel_file(file_path, "Income Statement.xlsx")

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        assert result['is_valid']
        assert result['exists']
        assert result['readable']
        assert result['has_data']
        assert result['has_proper_headers']
        assert len(result['detected_periods']) >= 1
        assert 'FY' in str(result['detected_periods'])

    def test_validate_excel_file_nonexistent(self, validator):
        """Test validation of nonexistent Excel file"""
        result = validator.validate_excel_file_format(
            Path("/nonexistent/file.xlsx"),
            "Income Statement.xlsx"
        )

        assert not result['is_valid']
        assert not result['exists']
        assert len(result['issues']) > 0

    def test_validate_excel_file_empty(self, validator, temp_company_dir):
        """Test validation of empty Excel file"""
        file_path = Path(temp_company_dir) / "empty.xlsx"
        wb = Workbook()
        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        assert not result['is_valid']
        assert result['exists']
        assert result['readable']
        assert not result['has_data']

    def test_validate_excel_file_missing_headers(self, validator, temp_company_dir):
        """Test validation of Excel file without proper column headers"""
        file_path = Path(temp_company_dir) / "no_headers.xlsx"
        wb = Workbook()
        ws = wb.active

        # Add data without FY headers
        ws.append(['Metric', '2023', '2022', '2021'])
        ws.append(['Revenue', 1000, 900, 800])

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        assert result['readable']
        assert result['has_data']
        assert not result['has_proper_headers']
        assert len([w for w in result['warnings'] if 'headers' in w['message']]) > 0

    def test_validate_excel_insufficient_periods(self, validator, temp_company_dir):
        """Test validation with insufficient historical periods"""
        file_path = Path(temp_company_dir) / "few_periods.xlsx"
        wb = Workbook()
        ws = wb.active

        # Only 2 periods (below recommended 3)
        ws.append(['Metric', 'FY', 'FY-1'])
        ws.append(['Revenue', 1000, 900])

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        warnings = [w for w in result['warnings'] if 'insufficient' in w['type']]
        assert len(warnings) > 0

    def test_validate_required_metrics_income_statement(self, validator, temp_company_dir):
        """Test validation of required metrics in Income Statement"""
        file_path = Path(temp_company_dir) / "incomplete_is.xlsx"
        wb = Workbook()
        ws = wb.active

        # Add headers but missing some required metrics
        ws.append(['Metric', 'FY', 'FY-1', 'FY-2'])
        ws.append(['Revenue', 1000, 900, 800])
        # Missing: Net Income, Operating Income

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        # Should have warnings about missing metrics
        metric_warnings = [w for w in result['warnings'] if 'missing_metric' in w['type']]
        assert len(metric_warnings) > 0

    # === Comprehensive Directory Structure Validation Tests ===

    def test_validate_directory_structure_method(self, validator, valid_company_structure):
        """Test the main validate_directory_structure method"""
        # Extract ticker from path
        ticker = valid_company_structure.name

        # Run validation
        report = validator.validate_directory_structure(
            ticker,
            base_path=str(valid_company_structure.parent)
        )

        assert report['ticker'] == ticker
        assert 'validation_timestamp' in report
        assert 'directory_validation' in report
        assert 'excel_validations' in report
        assert 'overall_compliance' in report
        assert 'actionable_recommendations' in report

        # Check overall compliance
        compliance = report['overall_compliance']
        assert compliance['status'] in ['COMPLIANT', 'PARTIALLY_COMPLIANT', 'NON_COMPLIANT']
        assert 'overall_score' in compliance
        assert 'directory_score' in compliance
        assert 'excel_score' in compliance

    def test_compliance_score_calculation(self, validator, valid_company_structure):
        """Test compliance score calculation"""
        ticker = valid_company_structure.name

        report = validator.validate_directory_structure(
            ticker,
            base_path=str(valid_company_structure.parent)
        )

        compliance = report['overall_compliance']

        # Valid structure should have high compliance
        assert compliance['overall_score'] >= 0.8
        assert compliance['status'] in ['COMPLIANT', 'PARTIALLY_COMPLIANT']
        assert compliance['total_issues'] == 0 or compliance['total_issues'] is not None

    def test_actionable_recommendations_generation(self, validator, temp_company_dir):
        """Test generation of actionable recommendations"""
        company_path = Path(temp_company_dir) / "INCOMPLETE"
        company_path.mkdir(parents=True)

        # Create only FY folder, missing LTM
        fy_path = company_path / "FY"
        fy_path.mkdir()

        report = validator.validate_directory_structure(
            "INCOMPLETE",
            base_path=temp_company_dir
        )

        recommendations = report['actionable_recommendations']

        # Should have recommendations for missing LTM folder
        assert len(recommendations) > 0
        assert any('LTM' in rec['action'] or 'missing' in rec['action'].lower()
                   for rec in recommendations)
        assert all('priority' in rec for rec in recommendations)
        assert all('category' in rec for rec in recommendations)
        assert all('impact' in rec for rec in recommendations)

    def test_excel_validations_in_comprehensive_report(self, validator, valid_company_structure):
        """Test that Excel file validations are included in comprehensive report"""
        ticker = valid_company_structure.name

        report = validator.validate_directory_structure(
            ticker,
            base_path=str(valid_company_structure.parent)
        )

        excel_validations = report['excel_validations']

        # Should have validations for all 6 files (FY and LTM, 3 statements each)
        assert len(excel_validations) == 6

        # Check keys are in expected format
        for key in excel_validations.keys():
            assert '/' in key  # Should be "FY/Income Statement.xlsx" format

        # All should be valid
        all_valid = all(v['is_valid'] for v in excel_validations.values())
        assert all_valid

    # === Directory Template Creation Tests ===

    def test_create_directory_structure_template(self, validator, temp_company_dir):
        """Test automated directory structure creation"""
        company_path = Path(temp_company_dir) / "NEW_COMPANY"

        result = validator.create_directory_structure_from_template(
            str(company_path),
            company_name="New Company Inc"
        )

        assert result['success']
        assert len(result['created_folders']) >= 3  # Main + FY + LTM
        assert len(result['created_files']) >= 6  # 3 files × 2 periods

        # Verify structure was created
        assert company_path.exists()
        assert (company_path / "FY").exists()
        assert (company_path / "LTM").exists()
        assert (company_path / "FY" / "Income Statement.xlsx").exists()

    # === Convenience Function Tests ===

    def test_validate_company_directory_convenience_function(self, valid_company_structure):
        """Test convenience function for directory validation"""
        result = validate_company_directory(str(valid_company_structure))

        assert result['is_valid']
        assert result['exists']

    def test_create_directory_structure_template_convenience_function(self, temp_company_dir):
        """Test convenience function for template creation"""
        company_path = Path(temp_company_dir) / "TEMPLATE_TEST"

        result = create_directory_structure_template(
            str(company_path),
            company_name="Template Test Co"
        )

        assert result['success']
        assert company_path.exists()

    # === Edge Cases and Error Handling ===

    def test_validation_with_special_characters_in_path(self, validator, temp_company_dir):
        """Test validation with special characters in path"""
        company_path = Path(temp_company_dir) / "COMP@NY-123_TEST"
        company_path.mkdir(parents=True)

        result = validator.validate_company_directory(str(company_path))

        # Should handle special characters without errors
        assert 'company_path' in result
        assert result['exists']

    def test_validation_history_tracking(self, validator, valid_company_structure):
        """Test that validation history is tracked"""
        initial_history_length = len(validator.validation_history)

        validator.validate_company_directory(str(valid_company_structure))

        assert len(validator.validation_history) == initial_history_length + 1

    def test_corrupted_excel_file_handling(self, validator, temp_company_dir):
        """Test handling of corrupted/unreadable Excel files"""
        file_path = Path(temp_company_dir) / "corrupted.xlsx"

        # Create a file that isn't actually a valid Excel file
        with open(file_path, 'w') as f:
            f.write("This is not an Excel file")

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        assert not result['is_valid']
        assert result['exists']
        assert not result['readable'] or len(result['issues']) > 0


    # === Task 180.1: Enhanced Excel Validation Tests ===

    def test_validate_numeric_data_types(self, validator, temp_company_dir):
        """Test numeric data type validation in Excel files"""
        file_path = Path(temp_company_dir) / "numeric_test.xlsx"
        wb = Workbook()
        ws = wb.active

        # Add headers and numeric data
        ws.append(['Metric', 'FY', 'FY-1', 'FY-2'])
        ws.append(['Revenue', 1000, 900, 800])
        ws.append(['Net Income', 100, 90, 80])

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        # Should detect numeric data
        assert result['has_numeric_data']
        assert 'data_type_validation' in result
        assert result['data_type_validation']['total_numeric_columns'] >= 3

    def test_validate_non_numeric_data_warning(self, validator, temp_company_dir):
        """Test detection of non-numeric data in financial columns"""
        file_path = Path(temp_company_dir) / "non_numeric_test.xlsx"
        wb = Workbook()
        ws = wb.active

        # Add headers with mixed data types
        ws.append(['Metric', 'FY', 'FY-1', 'FY-2'])
        ws.append(['Revenue', 'N/A', 900, 800])
        ws.append(['Net Income', 'TBD', 'Pending', 80])

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        # Should detect non-numeric data
        non_numeric_warnings = [w for w in result['warnings'] if w['type'] == 'non_numeric_data']
        assert len(non_numeric_warnings) > 0
        assert 'non_numeric_data_cells' in result
        assert len(result['non_numeric_data_cells']) > 0

    def test_sheet_detection(self, validator, temp_company_dir):
        """Test Excel workbook sheet detection"""
        file_path = Path(temp_company_dir) / "multi_sheet.xlsx"
        wb = Workbook()

        # Create multiple sheets
        wb.active.title = "Income Statement"
        ws1 = wb.active
        ws1.append(['Metric', 'FY', 'FY-1'])
        ws1.append(['Revenue', 1000, 900])

        ws2 = wb.create_sheet("Balance Sheet")
        ws2.append(['Metric', 'FY', 'FY-1'])
        ws2.append(['Assets', 5000, 4500])

        wb.save(file_path)

        result = validator.validate_excel_file_format(file_path, "Income Statement.xlsx")

        # Should detect multiple sheets
        assert result['sheet_count'] == 2
        assert 'Income Statement' in result['sheet_names']
        assert 'Balance Sheet' in result['sheet_names']

    def test_multi_sheet_validation(self, validator, temp_company_dir):
        """Test validation of all sheets in workbook"""
        file_path = Path(temp_company_dir) / "multi_sheet_validate.xlsx"
        wb = Workbook()

        # Create multiple sheets with different data
        wb.active.title = "Sheet1"
        ws1 = wb.active
        ws1.append(['Metric', 'FY', 'FY-1'])
        ws1.append(['Revenue', 1000, 900])

        ws2 = wb.create_sheet("Sheet2")
        ws2.append(['Metric', '2023', '2022'])  # No FY headers
        ws2.append(['Assets', 5000, 4500])

        wb.save(file_path)

        result = validator.validate_excel_file_format(
            file_path,
            "Income Statement.xlsx",
            validate_all_sheets=True
        )

        # Should validate all sheets
        assert 'sheet_validations' in result
        assert 'Sheet1' in result['sheet_validations']
        assert 'Sheet2' in result['sheet_validations']

        # Sheet1 should have FY headers
        assert result['sheet_validations']['Sheet1']['has_fy_headers']

        # Sheet2 should not have FY headers
        assert not result['sheet_validations']['Sheet2']['has_fy_headers']


    # === Task 180.2: Automated Repair and Organization Tests ===

    def test_repair_directory_structure_creates_missing_folders(self, validator, temp_company_dir):
        """Test automated repair creates missing FY/LTM folders"""
        company_path = Path(temp_company_dir) / "REPAIR_TEST"

        # Don't create the directory - let repair do it
        result = validator.repair_directory_structure(
            str(company_path),
            create_missing=True
        )

        assert result['success']
        assert len(result['created_folders']) >= 3  # Company + FY + LTM
        assert company_path.exists()
        assert (company_path / 'FY').exists()
        assert (company_path / 'LTM').exists()

    def test_repair_directory_structure_creates_template_files(self, validator, temp_company_dir):
        """Test repair creates template Excel files for missing statements"""
        company_path = Path(temp_company_dir) / "TEMPLATE_REPAIR"
        company_path.mkdir(parents=True)
        (company_path / 'FY').mkdir()
        (company_path / 'LTM').mkdir()

        result = validator.repair_directory_structure(
            str(company_path),
            create_missing=True
        )

        assert result['success']
        # Should create 6 files (3 statements × 2 periods)
        assert len(result['created_files']) == 6

        # Verify files exist
        assert (company_path / 'FY' / 'Income Statement.xlsx').exists()
        assert (company_path / 'LTM' / 'Balance Sheet.xlsx').exists()

    def test_organize_misplaced_files_from_root(self, validator, temp_company_dir):
        """Test organization of Excel files in root directory"""
        company_path = Path(temp_company_dir) / "ORGANIZE_ROOT"
        company_path.mkdir(parents=True)

        # Create misplaced file in root
        wb = Workbook()
        ws = wb.active
        ws.append(['Metric', 'FY', 'FY-1'])
        ws.append(['Revenue', 1000, 900])

        misplaced_file = company_path / "Income Statement.xlsx"
        wb.save(misplaced_file)

        result = validator.repair_directory_structure(
            str(company_path),
            organize_files=True,
            create_missing=True
        )

        assert result['success']
        assert len(result['moved_files']) > 0

        # File should be moved to FY folder by default
        assert (company_path / 'FY' / 'Income Statement.xlsx').exists()
        assert not misplaced_file.exists()

    def test_organize_files_wrong_period_folder(self, validator, temp_company_dir):
        """Test moving files between FY and LTM folders based on filename"""
        company_path = Path(temp_company_dir) / "WRONG_PERIOD"
        company_path.mkdir(parents=True)
        (company_path / 'FY').mkdir()
        (company_path / 'LTM').mkdir()

        # Create LTM file in FY folder
        wb = Workbook()
        ws = wb.active
        ws.append(['Metric', 'FY', 'FY-1'])
        ws.append(['Revenue', 1000, 900])

        wrong_file = company_path / 'FY' / 'LTM Income Statement.xlsx'
        wb.save(wrong_file)

        result = validator.repair_directory_structure(
            str(company_path),
            organize_files=True
        )

        assert result['success']
        # File should be moved from FY to LTM
        assert (company_path / 'LTM' / 'LTM Income Statement.xlsx').exists()
        assert not wrong_file.exists()

    def test_auto_fix_dry_run(self, validator, temp_company_dir):
        """Test auto-fix dry run mode (no actual changes)"""
        company_path = Path(temp_company_dir) / "DRYRUN_TEST"

        # Don't create directory
        result = validator.auto_fix_directory_structure(
            str(company_path),
            dry_run=True
        )

        assert result['dry_run']
        assert len(result['planned_actions']) > 0
        assert len(result['executed_actions']) == 0
        # Directory should not be created
        assert not Path(company_path).exists()

    def test_auto_fix_execution(self, validator, temp_company_dir):
        """Test auto-fix actually executes planned actions"""
        company_path = Path(temp_company_dir) / "AUTOFIX_TEST"

        result = validator.auto_fix_directory_structure(
            str(company_path),
            dry_run=False
        )

        assert not result['dry_run']
        assert len(result['executed_actions']) > 0
        # Directory should be created
        assert Path(company_path).exists()
        assert (Path(company_path) / 'FY').exists()

    def test_check_file_exists_with_alternatives(self, validator, temp_company_dir):
        """Test alternative filename pattern detection"""
        test_folder = Path(temp_company_dir) / "ALT_TEST"
        test_folder.mkdir(parents=True)

        # Create file with alternative name
        wb = Workbook()
        wb.save(test_folder / "income_statement.xlsx")

        # Should detect alternative pattern
        exists = validator._check_file_exists_with_alternatives(
            test_folder,
            "Income Statement.xlsx"
        )

        assert exists

    def test_repair_doesnt_overwrite_existing_files(self, validator, temp_company_dir):
        """Test that repair doesn't overwrite existing files"""
        company_path = Path(temp_company_dir) / "NO_OVERWRITE"
        company_path.mkdir(parents=True)
        fy_path = company_path / 'FY'
        fy_path.mkdir()

        # Create an existing file
        wb = Workbook()
        ws = wb.active
        ws.append(['Existing', 'Data'])
        existing_file = fy_path / 'Income Statement.xlsx'
        wb.save(existing_file)

        # Run repair
        result = validator.repair_directory_structure(
            str(company_path),
            create_missing=True
        )

        # Original file should still exist and not be in created_files list
        assert existing_file.exists()
        assert str(existing_file) not in result['created_files']


class TestRealWorldScenarios:
    """Test realistic scenarios with actual company directory patterns"""

    @pytest.fixture
    def validator(self):
        return DirectoryStructureValidator()

    @pytest.fixture
    def temp_company_dir(self):
        """Create temporary company directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_real_company_pattern_with_company_name_prefix(self, validator, temp_company_dir):
        """Test files with company name prefix (e.g., 'Microsoft Corporation - Income Statement.xlsx')"""
        company_path = Path(temp_company_dir) / "MSFT"
        company_path.mkdir(parents=True)

        fy_path = company_path / "FY"
        fy_path.mkdir()

        # Create files with company name prefix (common pattern)
        wb = Workbook()
        ws = wb.active
        ws.append(['Metric', 'FY', 'FY-1', 'FY-2'])
        ws.append(['Revenue', 1000, 900, 800])

        file_path = fy_path / "Microsoft Corporation - Income Statement.xlsx"
        wb.save(file_path)

        # Validation should still work with alternative file patterns
        result = validator.validate_company_directory(str(company_path), strict_mode=False)

        # Should find the file using alternative patterns
        assert 'FY' in result['found_files']
        assert len(result['found_files']['FY']) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
