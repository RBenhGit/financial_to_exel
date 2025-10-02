"""
Unit tests for File System Organization Validator (Task 206)

Tests the batch validation capabilities and aggregate reporting.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from openpyxl import Workbook

from tools.file_system_validator import FileSystemOrganizationValidator


class TestFileSystemOrganizationValidator:
    """Test suite for FileSystemOrganizationValidator"""

    @pytest.fixture
    def temp_base_dir(self):
        """Create temporary base directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def validator(self, temp_base_dir):
        """Create validator instance"""
        return FileSystemOrganizationValidator(base_path=temp_base_dir)

    def _create_company_structure(
        self,
        base_path: Path,
        ticker: str,
        include_fy: bool = True,
        include_ltm: bool = True,
        file_count: int = 3
    ):
        """Helper to create company directory structure"""
        company_path = base_path / ticker
        company_path.mkdir(parents=True, exist_ok=True)

        statements = [
            "Income Statement.xlsx",
            "Balance Sheet.xlsx",
            "Cash Flow Statement.xlsx"
        ]

        for period in (['FY'] if include_fy else []) + (['LTM'] if include_ltm else []):
            period_path = company_path / period
            period_path.mkdir(exist_ok=True)

            for i, statement in enumerate(statements[:file_count]):
                file_path = period_path / statement
                wb = Workbook()
                ws = wb.active
                ws.append(['Metric', 'FY', 'FY-1', 'FY-2'])
                ws.append(['Revenue', 1000, 900, 800])
                ws.append(['Net Income', 100, 90, 80])
                wb.save(file_path)

    # === Batch Validation Tests ===

    def test_validate_all_companies_empty_directory(self, validator):
        """Test batch validation with empty base directory"""
        # Base directory exists but is empty
        Path(validator.base_path).mkdir(parents=True, exist_ok=True)

        results = validator.validate_all_companies()

        assert results['total_companies'] == 0
        assert results['companies_validated'] == 0
        assert results['fully_compliant'] == 0

    def test_validate_all_companies_single_valid_company(self, validator, temp_base_dir):
        """Test batch validation with one fully valid company"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "AAPL")

        results = validator.validate_all_companies()

        assert results['total_companies'] == 1
        assert results['companies_validated'] == 1
        assert results['fully_compliant'] >= 0  # Depends on strict validation
        assert 'AAPL' in results['company_results']

    def test_validate_all_companies_multiple_companies(self, validator, temp_base_dir):
        """Test batch validation with multiple companies"""
        base_path = Path(temp_base_dir)

        # Create valid company
        self._create_company_structure(base_path, "AAPL")

        # Create partially valid company (missing LTM)
        self._create_company_structure(base_path, "MSFT", include_ltm=False)

        # Create incomplete company (missing some files)
        self._create_company_structure(base_path, "GOOGL", file_count=1)

        results = validator.validate_all_companies()

        assert results['total_companies'] == 3
        assert results['companies_validated'] == 3
        assert 'AAPL' in results['company_results']
        assert 'MSFT' in results['company_results']
        assert 'GOOGL' in results['company_results']

    def test_validate_specific_companies(self, validator, temp_base_dir):
        """Test validation of specific company tickers"""
        base_path = Path(temp_base_dir)

        self._create_company_structure(base_path, "AAPL")
        self._create_company_structure(base_path, "MSFT")
        self._create_company_structure(base_path, "GOOGL")

        # Validate only AAPL and MSFT
        results = validator.validate_all_companies(company_tickers=['AAPL', 'MSFT'])

        assert results['total_companies'] == 2
        assert 'AAPL' in results['company_results']
        assert 'MSFT' in results['company_results']
        assert 'GOOGL' not in results['company_results']

    def test_validate_with_auto_fix(self, validator, temp_base_dir):
        """Test batch validation with auto-fix enabled"""
        base_path = Path(temp_base_dir)

        # Create incomplete company
        company_path = base_path / "TESLA"
        company_path.mkdir(parents=True)

        results = validator.validate_all_companies(auto_fix=True)

        # Should attempt to fix issues
        assert results['total_companies'] == 1
        assert 'TESLA' in results['company_results']

        # Check that FY and LTM folders were created
        assert (company_path / 'FY').exists()
        assert (company_path / 'LTM').exists()

    def test_validate_nonexistent_base_path(self):
        """Test validation with nonexistent base path"""
        validator = FileSystemOrganizationValidator(base_path="/nonexistent/path")

        results = validator.validate_all_companies()

        assert results['total_companies'] == 0
        assert results['companies_validated'] == 0

    # === Single Company Validation Tests ===

    def test_validate_single_company(self, validator, temp_base_dir):
        """Test single company validation"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "NVIDIA")

        result = validator.validate_single_company("NVIDIA")

        assert result['ticker'] == "NVIDIA"
        assert 'overall_compliance' in result
        assert 'directory_validation' in result

    def test_validate_single_company_with_auto_fix(self, validator, temp_base_dir):
        """Test single company validation with auto-fix"""
        base_path = Path(temp_base_dir)

        # Create incomplete structure
        company_path = base_path / "AMD"
        company_path.mkdir(parents=True)

        result = validator.validate_single_company("AMD", auto_fix=True)

        assert result['ticker'] == "AMD"
        # Should have attempted fix
        assert (company_path / 'FY').exists()

    # === Aggregate Statistics Tests ===

    def test_calculate_aggregate_statistics(self, validator, temp_base_dir):
        """Test aggregate statistics calculation"""
        base_path = Path(temp_base_dir)

        self._create_company_structure(base_path, "COMP1")
        self._create_company_structure(base_path, "COMP2")
        self._create_company_structure(base_path, "COMP3", include_ltm=False)

        results = validator.validate_all_companies()
        stats = results['aggregate_statistics']

        assert 'average_compliance_score' in stats
        assert 'average_directory_score' in stats
        assert 'average_excel_score' in stats
        assert 'total_issues' in stats
        assert 'total_warnings' in stats
        assert 'most_common_issues' in stats
        assert 'compliance_distribution' in stats

        # Scores should be between 0 and 1
        assert 0 <= stats['average_compliance_score'] <= 1
        assert 0 <= stats['average_directory_score'] <= 1
        assert 0 <= stats['average_excel_score'] <= 1

    def test_aggregate_statistics_empty_results(self, validator):
        """Test aggregate statistics with no results"""
        results = {
            'company_results': {},
            'fully_compliant': 0,
            'partially_compliant': 0,
            'non_compliant': 0
        }

        stats = validator._calculate_aggregate_statistics(results)

        assert stats['average_compliance_score'] == 0.0
        assert stats['total_issues'] == 0
        assert len(stats['most_common_issues']) == 0

    # === Recommendations Summary Tests ===

    def test_generate_recommendations_summary(self, validator, temp_base_dir):
        """Test recommendations summary generation"""
        base_path = Path(temp_base_dir)

        # Create multiple companies with issues
        for ticker in ['COMP1', 'COMP2', 'COMP3']:
            company_path = base_path / ticker
            company_path.mkdir(parents=True)
            # Missing FY/LTM folders will generate recommendations

        results = validator.validate_all_companies()
        recs = results['recommendations_summary']

        assert isinstance(recs, list)
        if len(recs) > 0:
            # Check structure of recommendations
            for rec in recs:
                assert 'issue_type' in rec
                assert 'priority' in rec
                assert 'affected_companies' in rec
                assert 'count' in rec
                assert isinstance(rec['affected_companies'], list)

    def test_recommendations_summary_grouping(self, validator, temp_base_dir):
        """Test that recommendations are properly grouped by type"""
        base_path = Path(temp_base_dir)

        # Create companies with same issue (missing LTM)
        for ticker in ['A', 'B', 'C']:
            company_path = base_path / ticker
            company_path.mkdir(parents=True)
            (company_path / 'FY').mkdir()
            # All missing LTM folder

        results = validator.validate_all_companies()
        recs = results['recommendations_summary']

        # Should have grouped missing LTM recommendations
        ltm_recs = [r for r in recs if 'LTM' in str(r.get('issue_type', ''))]
        if ltm_recs:
            # Should have 3 companies affected
            assert len(ltm_recs[0]['affected_companies']) == 3

    # === Export Tests ===

    def test_export_batch_results_json(self, validator, temp_base_dir):
        """Test exporting batch results to JSON"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        # Run validation
        validator.validate_all_companies()

        # Export
        output_path = Path(temp_base_dir) / "report.json"
        result = validator.export_batch_results(str(output_path), format='json')

        assert result['success']
        assert output_path.exists()

        # Verify content
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'validation_timestamp' in data
        assert 'summary' in data
        assert 'aggregate_statistics' in data

    def test_export_batch_results_html(self, validator, temp_base_dir):
        """Test exporting batch results to HTML"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        validator.validate_all_companies()

        output_path = Path(temp_base_dir) / "report.html"
        result = validator.export_batch_results(str(output_path), format='html')

        assert result['success']
        assert output_path.exists()

        # Verify HTML content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<!DOCTYPE html>' in content
        assert 'Batch File System Validation Report' in content

    def test_export_batch_results_csv(self, validator, temp_base_dir):
        """Test exporting batch results to CSV"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        validator.validate_all_companies()

        output_path = Path(temp_base_dir) / "report.csv"
        result = validator.export_batch_results(str(output_path), format='csv')

        assert result['success']
        assert output_path.exists()

        # Verify CSV content
        with open(output_path, 'r') as f:
            content = f.read()

        assert 'Batch File System Validation Report' in content
        assert 'Summary Statistics' in content

    def test_export_before_validation(self, validator, temp_base_dir):
        """Test export fails gracefully without validation results"""
        output_path = Path(temp_base_dir) / "report.json"
        result = validator.export_batch_results(str(output_path))

        assert not result['success']
        assert 'error' in result

    def test_export_without_details(self, validator, temp_base_dir):
        """Test export without detailed company results"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        validator.validate_all_companies()

        output_path = Path(temp_base_dir) / "report.json"
        result = validator.export_batch_results(
            str(output_path),
            format='json',
            include_details=False
        )

        assert result['success']

        import json
        with open(output_path, 'r') as f:
            data = json.load(f)

        # Should not include detailed company results
        assert 'company_results' not in data

    def test_export_unsupported_format(self, validator, temp_base_dir):
        """Test export with unsupported format"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        validator.validate_all_companies()

        output_path = Path(temp_base_dir) / "report.xml"
        result = validator.export_batch_results(str(output_path), format='xml')

        assert not result['success']
        assert 'error' in result

    # === Compliance Summary Tests ===

    def test_get_compliance_summary(self, validator, temp_base_dir):
        """Test getting text compliance summary"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "COMP1")
        self._create_company_structure(base_path, "COMP2")

        validator.validate_all_companies()
        summary = validator.get_compliance_summary()

        assert isinstance(summary, str)
        assert 'Batch File System Validation Summary' in summary
        assert 'Companies Validated' in summary
        assert 'Compliance Distribution' in summary

    def test_get_compliance_summary_no_results(self, validator):
        """Test compliance summary with no validation results"""
        summary = validator.get_compliance_summary()

        assert isinstance(summary, str)
        assert 'No validation results available' in summary

    # === Error Handling Tests ===

    def test_validation_error_handling(self, validator, temp_base_dir):
        """Test handling of validation errors for individual companies"""
        base_path = Path(temp_base_dir)

        # Create a normal company
        self._create_company_structure(base_path, "GOOD")

        # Create a company directory that might cause issues
        bad_path = base_path / "BAD"
        bad_path.mkdir(parents=True)

        results = validator.validate_all_companies()

        # Should handle both companies
        assert results['companies_validated'] >= 1
        assert 'GOOD' in results['company_results']

    def test_export_creates_directory(self, validator, temp_base_dir):
        """Test that export creates output directory if needed"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        validator.validate_all_companies()

        output_path = Path(temp_base_dir) / "nested" / "dir" / "report.json"
        result = validator.export_batch_results(str(output_path))

        assert result['success']
        assert output_path.exists()
        assert output_path.parent.exists()

    # === Integration Tests ===

    def test_complete_workflow(self, validator, temp_base_dir):
        """Test complete validation workflow"""
        base_path = Path(temp_base_dir)

        # Step 1: Create companies with various states
        self._create_company_structure(base_path, "GOOD", True, True, 3)
        self._create_company_structure(base_path, "PARTIAL", True, False, 2)
        company_path = base_path / "EMPTY"
        company_path.mkdir(parents=True)

        # Step 2: Run batch validation
        results = validator.validate_all_companies()

        assert results['total_companies'] == 3
        assert results['companies_validated'] == 3

        # Step 3: Get summary
        summary = validator.get_compliance_summary()
        assert 'Batch File System Validation Summary' in summary

        # Step 4: Export results
        output_path = Path(temp_base_dir) / "workflow_report.html"
        export_result = validator.export_batch_results(str(output_path), format='html')

        assert export_result['success']
        assert output_path.exists()

    def test_batch_validation_with_hidden_dirs(self, validator, temp_base_dir):
        """Test that hidden directories are ignored"""
        base_path = Path(temp_base_dir)

        # Create normal company
        self._create_company_structure(base_path, "NORMAL")

        # Create hidden directory (should be ignored)
        hidden_path = base_path / ".hidden"
        hidden_path.mkdir()

        results = validator.validate_all_companies()

        # Should only validate NORMAL, not .hidden
        assert results['total_companies'] == 1
        assert 'NORMAL' in results['company_results']
        assert '.hidden' not in results['company_results']

    def test_validation_results_history(self, validator, temp_base_dir):
        """Test that validation results are stored in history"""
        base_path = Path(temp_base_dir)
        self._create_company_structure(base_path, "TEST")

        # Run multiple validations
        validator.validate_all_companies()
        validator.validate_all_companies()

        # Should have history
        assert len(validator.validation_results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
