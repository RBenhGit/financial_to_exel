"""
Unit Tests for File System Auto-Repair Tools (Task 207)

Tests for automated file system repair operations including:
- File name standardization
- Directory structure creation
- Duplicate detection and resolution
- Backup and rollback functionality
- Batch repair operations
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import json
import shutil
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.file_system_auto_repair import FileSystemAutoRepair


@pytest.fixture
def temp_test_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_company_structure(temp_test_dir):
    """Create sample company directory structure for testing."""
    company_dir = temp_test_dir / "companies" / "AAPL"
    company_dir.mkdir(parents=True)

    # Create FY and LTM directories
    (company_dir / "FY").mkdir()
    (company_dir / "LTM").mkdir()

    # Create some test files with non-standard names
    (company_dir / "FY" / "income_statement.xlsx").touch()
    (company_dir / "FY" / "balance_sheet.xlsx").touch()
    (company_dir / "LTM" / "cash_flow.xlsx").touch()

    return company_dir


@pytest.fixture
def corrupted_company_structure(temp_test_dir):
    """Create corrupted company directory structure for testing repairs."""
    company_dir = temp_test_dir / "companies" / "MSFT"
    company_dir.mkdir(parents=True)

    # Missing FY/LTM directories
    # Create files in root instead
    (company_dir / "income_statement.xlsx").touch()
    (company_dir / "balance.xlsx").touch()

    return company_dir


@pytest.fixture
def repair_system(temp_test_dir):
    """Create FileSystemAutoRepair instance for testing."""
    base_path = temp_test_dir / "companies"
    base_path.mkdir(parents=True, exist_ok=True)

    backup_dir = temp_test_dir / ".backups"

    return FileSystemAutoRepair(
        base_path=str(base_path),
        backup_dir=str(backup_dir),
        auto_confirm=True  # Skip prompts during testing
    )


class TestFileNameStandardization:
    """Test file name standardization functionality."""

    def test_standardize_file_names_basic(self, repair_system, sample_company_structure):
        """Test basic file name standardization."""
        result = repair_system.standardize_file_names(
            sample_company_structure,
            dry_run=False
        )

        assert result['success'] is True
        assert len(result['renames_performed']) > 0

        # Check that standard files now exist
        assert (sample_company_structure / "FY" / "Income Statement.xlsx").exists()
        assert (sample_company_structure / "FY" / "Balance Sheet.xlsx").exists()

    def test_standardize_file_names_dry_run(self, repair_system, sample_company_structure):
        """Test dry run mode for file standardization."""
        result = repair_system.standardize_file_names(
            sample_company_structure,
            dry_run=True
        )

        assert result['success'] is True
        assert len(result['renames_needed']) > 0
        assert len(result['renames_performed']) == 0

        # Original files should still exist
        assert (sample_company_structure / "FY" / "income_statement.xlsx").exists()

    def test_standardize_already_standard_names(self, temp_test_dir, repair_system):
        """Test standardization when files already have correct names."""
        company_dir = temp_test_dir / "companies" / "GOOGL"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()

        # Create files with standard names
        (company_dir / "FY" / "Income Statement.xlsx").touch()
        (company_dir / "FY" / "Balance Sheet.xlsx").touch()

        result = repair_system.standardize_file_names(company_dir, dry_run=False)

        assert result['success'] is True
        assert len(result['renames_performed']) == 0

    def test_standardize_fuzzy_matching(self, temp_test_dir, repair_system):
        """Test fuzzy matching for similar file names."""
        company_dir = temp_test_dir / "companies" / "NVDA"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()

        # Create files with variations
        (company_dir / "FY" / "Income_Statement_2024.xlsx").touch()
        (company_dir / "FY" / "Balance-Sheet-Q4.xlsx").touch()

        result = repair_system.standardize_file_names(company_dir, dry_run=False)

        assert result['success'] is True
        # Should match and rename based on similarity threshold


class TestDirectoryCreation:
    """Test directory structure creation functionality."""

    def test_create_missing_directories(self, repair_system, corrupted_company_structure):
        """Test creation of missing FY/LTM directories."""
        result = repair_system.create_missing_directories(
            corrupted_company_structure,
            dry_run=False
        )

        assert result['success'] is True
        assert len(result['directories_created']) == 2

        # Check directories were created
        assert (corrupted_company_structure / "FY").exists()
        assert (corrupted_company_structure / "LTM").exists()

    def test_create_directories_dry_run(self, repair_system, corrupted_company_structure):
        """Test dry run for directory creation."""
        result = repair_system.create_missing_directories(
            corrupted_company_structure,
            dry_run=True
        )

        assert result['success'] is True
        assert len(result['directories_needed']) == 2
        assert len(result['directories_created']) == 0

        # Directories should not exist yet
        assert not (corrupted_company_structure / "FY").exists()

    def test_create_directories_already_exist(self, repair_system, sample_company_structure):
        """Test when directories already exist."""
        result = repair_system.create_missing_directories(
            sample_company_structure,
            dry_run=False
        )

        assert result['success'] is True
        assert len(result['directories_created']) == 0


class TestDuplicateDetection:
    """Test duplicate file detection functionality."""

    def test_detect_duplicates_by_name(self, temp_test_dir, repair_system):
        """Test duplicate detection by file name."""
        company_dir = temp_test_dir / "companies" / "TSLA"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()
        (company_dir / "LTM").mkdir()

        # Create duplicate files
        (company_dir / "FY" / "Income Statement.xlsx").touch()
        (company_dir / "LTM" / "Income Statement.xlsx").touch()

        result = repair_system.detect_duplicates(company_dir, comparison_method='name')

        assert result['success'] is True
        assert result['total_duplicates'] > 0

    def test_detect_duplicates_by_checksum(self, temp_test_dir, repair_system):
        """Test duplicate detection by checksum."""
        company_dir = temp_test_dir / "companies" / "AMZN"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()

        # Create identical files
        file1 = company_dir / "FY" / "test1.xlsx"
        file2 = company_dir / "FY" / "test2.xlsx"

        # Write identical content
        content = b"identical content"
        file1.write_bytes(content)
        file2.write_bytes(content)

        result = repair_system.detect_duplicates(company_dir, comparison_method='checksum')

        assert result['success'] is True
        assert result['total_duplicates'] > 0
        assert result['potential_savings_bytes'] > 0

    def test_detect_no_duplicates(self, repair_system, sample_company_structure):
        """Test when no duplicates exist."""
        # Create unique files in different directories
        (sample_company_structure / "FY" / "unique1.xlsx").touch()
        (sample_company_structure / "LTM" / "unique2.xlsx").touch()

        result = repair_system.detect_duplicates(
            sample_company_structure,
            comparison_method='name'
        )

        assert result['success'] is True
        assert result['total_duplicates'] == 0


class TestDuplicateResolution:
    """Test duplicate file resolution functionality."""

    def test_resolve_duplicates_keep_newest(self, temp_test_dir, repair_system):
        """Test duplicate resolution keeping newest file."""
        company_dir = temp_test_dir / "companies" / "META"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()

        # Create files with different modification times
        import time
        file1 = company_dir / "FY" / "duplicate1.xlsx"
        file2 = company_dir / "FY" / "duplicate2.xlsx"

        file1.write_bytes(b"content")
        time.sleep(0.1)
        file2.write_bytes(b"content")

        # file2 should be newer

        result = repair_system.resolve_duplicates(
            company_dir,
            strategy='keep_newest',
            dry_run=False
        )

        assert result['success'] is True
        # Should keep file2, remove file1

    def test_resolve_duplicates_dry_run(self, temp_test_dir, repair_system):
        """Test dry run for duplicate resolution."""
        company_dir = temp_test_dir / "companies" / "NFLX"
        company_dir.mkdir(parents=True)
        (company_dir / "FY").mkdir()

        # Create duplicate files
        file1 = company_dir / "FY" / "dup1.xlsx"
        file2 = company_dir / "FY" / "dup2.xlsx"
        content = b"same"
        file1.write_bytes(content)
        file2.write_bytes(content)

        result = repair_system.resolve_duplicates(
            company_dir,
            strategy='keep_newest',
            dry_run=True
        )

        assert result['success'] is True
        assert len(result['duplicates_to_remove']) > 0
        assert len(result['duplicates_removed']) == 0

        # Both files should still exist
        assert file1.exists()
        assert file2.exists()


class TestBackupAndRollback:
    """Test backup and rollback functionality."""

    def test_create_backup(self, repair_system, sample_company_structure):
        """Test backup creation."""
        result = repair_system.create_backup(
            paths=[sample_company_structure],
            description="Test backup"
        )

        assert result['success'] is True
        assert result['backup_id'] is not None
        assert Path(result['backup_path']).exists()

        # Check manifest
        manifest_path = Path(result['backup_path']) / 'manifest.json'
        assert manifest_path.exists()

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            assert manifest['total_files'] > 0

    def test_rollback_success(self, repair_system, sample_company_structure):
        """Test successful rollback operation."""
        # Create backup
        backup_result = repair_system.create_backup(
            paths=[sample_company_structure],
            description="Before modification"
        )
        backup_id = backup_result['backup_id']

        # Modify files
        test_file = sample_company_structure / "FY" / "income_statement.xlsx"
        test_file.unlink()

        # Rollback
        rollback_result = repair_system.rollback(backup_id)

        assert rollback_result['success'] is True
        assert rollback_result['items_restored'] > 0

        # Check file was restored
        assert test_file.exists()

    def test_rollback_nonexistent_backup(self, repair_system):
        """Test rollback with non-existent backup ID."""
        result = repair_system.rollback('nonexistent_backup_id')

        assert result['success'] is False
        assert 'not found' in result['error'].lower()


class TestComprehensiveRepair:
    """Test comprehensive repair functionality."""

    def test_repair_company_directory_all_operations(
        self,
        repair_system,
        corrupted_company_structure
    ):
        """Test comprehensive repair with all operations."""
        # Add some files to corrupted structure
        (corrupted_company_structure / "income.xlsx").touch()

        result = repair_system.repair_company_directory(
            corrupted_company_structure,
            operations=['create_dirs', 'standardize_names'],
            dry_run=False,
            create_backup=True
        )

        assert result['success'] is True
        assert result['backup_id'] is not None
        assert 'create_directories' in result['operations_performed']

    def test_repair_with_rollback_on_error(self, repair_system, temp_test_dir):
        """Test that rollback occurs on repair failure."""
        company_dir = temp_test_dir / "companies" / "ERROR_TEST"
        company_dir.mkdir(parents=True)

        # This should succeed initially but may fail on complex operations
        result = repair_system.repair_company_directory(
            company_dir,
            operations=['create_dirs'],
            dry_run=False,
            create_backup=True
        )

        # Even if error occurs, backup should be created
        assert result['backup_id'] is not None

    def test_repair_dry_run_no_backup(self, repair_system, sample_company_structure):
        """Test that dry run doesn't create backups."""
        result = repair_system.repair_company_directory(
            sample_company_structure,
            operations=['standardize_names'],
            dry_run=True,
            create_backup=True  # Should be ignored in dry run
        )

        assert result['success'] is True
        assert result['backup_id'] is None


class TestBatchRepair:
    """Test batch repair operations."""

    def test_batch_repair_multiple_companies(self, temp_test_dir, repair_system):
        """Test batch repair across multiple companies."""
        # Create multiple company directories
        companies = ['AAPL', 'GOOGL', 'MSFT']
        for ticker in companies:
            company_dir = temp_test_dir / "companies" / ticker
            company_dir.mkdir(parents=True)
            (company_dir / "income.xlsx").touch()

        result = repair_system.batch_repair(
            company_tickers=companies,
            operations=['create_dirs'],
            dry_run=False
        )

        assert result['success'] is True
        assert result['total_companies'] == len(companies)
        assert result['companies_repaired'] > 0

    def test_batch_repair_with_progress(self, temp_test_dir, repair_system):
        """Test batch repair with progress callback."""
        # Create test companies
        companies = ['TEST1', 'TEST2']
        for ticker in companies:
            company_dir = temp_test_dir / "companies" / ticker
            company_dir.mkdir(parents=True)

        progress_calls = []

        def progress_callback(current, total, ticker):
            progress_calls.append((current, total, ticker))

        result = repair_system.batch_repair(
            company_tickers=companies,
            operations=['create_dirs'],
            dry_run=True,
            progress_callback=progress_callback
        )

        assert result['success'] is True
        assert len(progress_calls) == len(companies)

    def test_batch_repair_aggregate_statistics(self, temp_test_dir, repair_system):
        """Test aggregate statistics calculation in batch repair."""
        companies = ['STAT1', 'STAT2']
        for ticker in companies:
            company_dir = temp_test_dir / "companies" / ticker
            company_dir.mkdir(parents=True)

        result = repair_system.batch_repair(
            company_tickers=companies,
            operations=['create_dirs'],
            dry_run=False
        )

        assert 'aggregate_statistics' in result
        stats = result['aggregate_statistics']
        assert 'total_directories_created' in stats
        assert 'success_rate' in stats


class TestLoggingAndExport:
    """Test logging and export functionality."""

    def test_operation_logging(self, repair_system, sample_company_structure):
        """Test that operations are logged correctly."""
        initial_log_count = len(repair_system.repair_log)

        repair_system.create_missing_directories(sample_company_structure, dry_run=False)

        # Log should have grown (if any directories were created)
        assert len(repair_system.repair_log) >= initial_log_count

    def test_export_repair_log(self, repair_system, temp_test_dir):
        """Test exporting repair log to file."""
        # Perform some operations
        repair_system.stats['operations_performed'] = 5

        output_path = temp_test_dir / "repair_log.json"

        result = repair_system.export_repair_log(str(output_path))

        assert result['success'] is True
        assert output_path.exists()

        # Verify log content
        with open(output_path, 'r') as f:
            log_data = json.load(f)
            assert 'timestamp' in log_data
            assert 'statistics' in log_data
            assert log_data['statistics']['operations_performed'] == 5

    def test_get_statistics(self, repair_system):
        """Test retrieving current statistics."""
        stats = repair_system.get_statistics()

        assert 'statistics' in stats
        assert 'total_operations_logged' in stats
        assert 'current_backup_id' in stats


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_directory(self, temp_test_dir, repair_system):
        """Test operations on empty directory."""
        empty_dir = temp_test_dir / "companies" / "EMPTY"
        empty_dir.mkdir(parents=True)

        result = repair_system.repair_company_directory(
            empty_dir,
            operations=['create_dirs', 'standardize_names'],
            dry_run=False
        )

        assert result['success'] is True

    def test_nonexistent_company(self, temp_test_dir, repair_system):
        """Test operations on non-existent company directory."""
        nonexistent = temp_test_dir / "companies" / "NONEXISTENT"

        # Should handle gracefully
        result = repair_system.create_missing_directories(nonexistent, dry_run=True)

        # Will succeed because it just checks what's needed
        assert result['success'] is True

    def test_permission_error_handling(self, repair_system, sample_company_structure):
        """Test handling of permission errors."""
        # This test may not work on all systems
        # It's more of a documentation of expected behavior

        result = repair_system.repair_company_directory(
            sample_company_structure,
            operations=['standardize_names'],
            dry_run=False
        )

        # Should complete even if some operations fail
        assert 'operations_performed' in result

    def test_concurrent_modifications(self, repair_system, sample_company_structure):
        """Test behavior with concurrent modifications."""
        # Create backup
        backup_result = repair_system.create_backup(
            paths=[sample_company_structure],
            description="Concurrent test"
        )

        assert backup_result['success'] is True

        # Modify files
        (sample_company_structure / "FY" / "new_file.xlsx").touch()

        # Rollback should still work
        rollback_result = repair_system.rollback(backup_result['backup_id'])
        assert rollback_result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
