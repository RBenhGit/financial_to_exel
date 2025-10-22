"""
File System Auto-Repair Tools (Task 207)

Automated tools to fix common file system organization issues with
comprehensive backup, rollback, and logging capabilities.

Features:
- File name standardization utilities
- Directory structure creation and repair
- Duplicate file detection and resolution
- Missing file identification with user prompts
- Backup creation before modifications
- Rollback capabilities for failed repairs
- Comprehensive logging and progress tracking
- User confirmation prompts for destructive operations
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import shutil
import json
from datetime import datetime
import hashlib
import difflib

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.directory_structure_helper import DirectoryStructureValidator

logger = logging.getLogger(__name__)


class FileSystemAutoRepair:
    """
    Automated file system repair tools with backup and rollback capabilities.

    Provides comprehensive repair operations for common file system organization
    issues while maintaining safety through backups and detailed logging.
    """

    # Standard file name mappings for repairs
    STANDARD_FILE_NAMES = {
        "Income Statement.xlsx": [
            "income_statement.xlsx", "income statement.xlsx",
            "income.xlsx", "IS.xlsx", "is.xlsx",
            "profit_loss.xlsx", "P&L.xlsx"
        ],
        "Balance Sheet.xlsx": [
            "balance_sheet.xlsx", "balance sheet.xlsx",
            "balance.xlsx", "BS.xlsx", "bs.xlsx",
            "statement_of_financial_position.xlsx"
        ],
        "Cash Flow Statement.xlsx": [
            "cash_flow_statement.xlsx", "cash flow statement.xlsx",
            "cash_flow.xlsx", "cashflow.xlsx",
            "CF.xlsx", "cf.xlsx", "cash_flows.xlsx"
        ]
    }

    def __init__(
        self,
        base_path: str = "data/companies",
        backup_dir: str = ".backups",
        auto_confirm: bool = False
    ):
        """
        Initialize auto-repair system.

        Args:
            base_path: Base directory containing company folders
            backup_dir: Directory for storing backups
            auto_confirm: If True, skip user confirmation prompts
        """
        self.base_path = Path(base_path)
        self.backup_dir = Path(backup_dir)
        self.auto_confirm = auto_confirm
        self.validator = DirectoryStructureValidator()

        # Repair operation log
        self.repair_log: List[Dict[str, Any]] = []
        self.current_backup_id: Optional[str] = None

        # Statistics
        self.stats = {
            'operations_performed': 0,
            'files_renamed': 0,
            'directories_created': 0,
            'duplicates_removed': 0,
            'backups_created': 0,
            'rollbacks_performed': 0
        }

    def create_backup(
        self,
        paths: List[Path],
        description: str = "Auto-repair backup"
    ) -> Dict[str, Any]:
        """
        Create backup of specified paths before modifications.

        Args:
            paths: List of paths to backup
            description: Description of the backup

        Returns:
            Dictionary with backup details
        """
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.current_backup_id = backup_id

        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        backup_manifest = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'backed_up_paths': [],
            'total_files': 0,
            'total_size_bytes': 0
        }

        try:
            for path in paths:
                if not path.exists():
                    logger.warning(f"Path does not exist for backup: {path}")
                    continue

                # Calculate relative path from base
                try:
                    relative_path = path.relative_to(self.base_path)
                except ValueError:
                    relative_path = Path(path.name)

                backup_target = backup_path / relative_path

                if path.is_file():
                    backup_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, backup_target)
                    file_size = path.stat().st_size

                    backup_manifest['backed_up_paths'].append({
                        'original': str(path),
                        'backup': str(backup_target),
                        'type': 'file',
                        'size_bytes': file_size,
                        'checksum': self._calculate_checksum(path)
                    })

                    backup_manifest['total_files'] += 1
                    backup_manifest['total_size_bytes'] += file_size

                elif path.is_dir():
                    shutil.copytree(path, backup_target, dirs_exist_ok=True)

                    # Count files in directory
                    file_count = sum(1 for _ in path.rglob('*') if _.is_file())
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

                    backup_manifest['backed_up_paths'].append({
                        'original': str(path),
                        'backup': str(backup_target),
                        'type': 'directory',
                        'file_count': file_count,
                        'total_size_bytes': total_size
                    })

                    backup_manifest['total_files'] += file_count
                    backup_manifest['total_size_bytes'] += total_size

            # Save manifest
            manifest_path = backup_path / 'manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(backup_manifest, f, indent=2)

            self.stats['backups_created'] += 1

            logger.info(f"Backup created: {backup_id} ({backup_manifest['total_files']} files)")

            return {
                'success': True,
                'backup_id': backup_id,
                'backup_path': str(backup_path),
                'manifest': backup_manifest
            }

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def rollback(self, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Rollback to a previous backup.

        Args:
            backup_id: ID of backup to restore. If None, uses most recent.

        Returns:
            Dictionary with rollback results
        """
        if backup_id is None:
            backup_id = self.current_backup_id

        if backup_id is None:
            return {
                'success': False,
                'error': 'No backup ID specified and no current backup available'
            }

        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup not found: {backup_id}'
            }

        # Load manifest
        manifest_path = backup_path / 'manifest.json'
        if not manifest_path.exists():
            return {
                'success': False,
                'error': 'Backup manifest not found'
            }

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        try:
            restored_count = 0

            for item in manifest['backed_up_paths']:
                original_path = Path(item['original'])
                backup_item_path = Path(item['backup'])

                if not backup_item_path.exists():
                    logger.warning(f"Backup item not found: {backup_item_path}")
                    continue

                # Remove current version if exists
                if original_path.exists():
                    if original_path.is_file():
                        original_path.unlink()
                    elif original_path.is_dir():
                        shutil.rmtree(original_path)

                # Restore from backup
                if item['type'] == 'file':
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_item_path, original_path)
                elif item['type'] == 'directory':
                    shutil.copytree(backup_item_path, original_path, dirs_exist_ok=True)

                restored_count += 1

            self.stats['rollbacks_performed'] += 1

            logger.info(f"Rollback completed: {restored_count} items restored from {backup_id}")

            return {
                'success': True,
                'backup_id': backup_id,
                'items_restored': restored_count,
                'manifest': manifest
            }

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def standardize_file_names(
        self,
        company_path: Path,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Standardize file names to match expected conventions.

        Args:
            company_path: Path to company directory
            dry_run: If True, only report changes without executing

        Returns:
            Dictionary with standardization results
        """
        result = {
            'success': True,
            'company': company_path.name,
            'renames_performed': [],
            'renames_needed': [],
            'errors': []
        }

        try:
            # Search for files that match alternative patterns
            for standard_name, alternatives in self.STANDARD_FILE_NAMES.items():
                # Check FY and LTM directories
                for period_dir in ['FY', 'LTM']:
                    period_path = company_path / period_dir

                    if not period_path.exists():
                        continue

                    # Check if standard file already exists
                    standard_file = period_path / standard_name
                    if standard_file.exists():
                        continue

                    # Look for alternatives
                    for alt_pattern in alternatives:
                        for file in period_path.glob(f"*{alt_pattern.split('.')[-2]}*.xlsx"):
                            # Use fuzzy matching to confirm similarity
                            similarity = difflib.SequenceMatcher(
                                None,
                                file.name.lower(),
                                alt_pattern.lower()
                            ).ratio()

                            if similarity > 0.6:  # 60% similarity threshold
                                rename_info = {
                                    'from': str(file),
                                    'to': str(standard_file),
                                    'period': period_dir,
                                    'similarity': round(similarity, 2)
                                }

                                if dry_run:
                                    result['renames_needed'].append(rename_info)
                                else:
                                    # Confirm with user unless auto_confirm is True
                                    if not self.auto_confirm:
                                        response = input(
                                            f"\nRename '{file.name}' to '{standard_name}' "
                                            f"in {period_dir}? (y/n): "
                                        )
                                        if response.lower() != 'y':
                                            continue

                                    # Perform rename
                                    file.rename(standard_file)
                                    result['renames_performed'].append(rename_info)
                                    self.stats['files_renamed'] += 1

                                    # Log operation
                                    self._log_operation(
                                        operation='rename',
                                        details=rename_info
                                    )

                                break  # Found match, move to next standard file

        except Exception as e:
            logger.error(f"File name standardization failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))

        return result

    def create_missing_directories(
        self,
        company_path: Path,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create missing FY/LTM directory structure.

        Args:
            company_path: Path to company directory
            dry_run: If True, only report what would be created

        Returns:
            Dictionary with directory creation results
        """
        result = {
            'success': True,
            'company': company_path.name,
            'directories_created': [],
            'directories_needed': [],
            'errors': []
        }

        required_dirs = ['FY', 'LTM']

        try:
            for dir_name in required_dirs:
                dir_path = company_path / dir_name

                if not dir_path.exists():
                    if dry_run:
                        result['directories_needed'].append(str(dir_path))
                    else:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        result['directories_created'].append(str(dir_path))
                        self.stats['directories_created'] += 1

                        # Log operation
                        self._log_operation(
                            operation='create_directory',
                            details={'path': str(dir_path)}
                        )

                        logger.info(f"Created directory: {dir_path}")

        except Exception as e:
            logger.error(f"Directory creation failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))

        return result

    def detect_duplicates(
        self,
        company_path: Path,
        comparison_method: str = 'checksum'
    ) -> Dict[str, Any]:
        """
        Detect duplicate files within company directory.

        Args:
            company_path: Path to company directory
            comparison_method: Method for comparison ('checksum', 'name', 'content')

        Returns:
            Dictionary with duplicate detection results
        """
        result = {
            'success': True,
            'company': company_path.name,
            'duplicates_found': [],
            'total_duplicates': 0,
            'potential_savings_bytes': 0
        }

        try:
            if comparison_method == 'checksum':
                duplicates = self._find_duplicates_by_checksum(company_path)
            elif comparison_method == 'name':
                duplicates = self._find_duplicates_by_name(company_path)
            else:
                duplicates = self._find_duplicates_by_content(company_path)

            result['duplicates_found'] = duplicates
            result['total_duplicates'] = len(duplicates)

            # Calculate potential savings
            for dup_group in duplicates:
                if len(dup_group['files']) > 1:
                    file_size = Path(dup_group['files'][0]).stat().st_size
                    # Savings = size * (number of duplicates - 1)
                    result['potential_savings_bytes'] += file_size * (len(dup_group['files']) - 1)

        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            result['success'] = False
            result['error'] = str(e)

        return result

    def resolve_duplicates(
        self,
        company_path: Path,
        strategy: str = 'keep_newest',
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Resolve duplicate files using specified strategy.

        Args:
            company_path: Path to company directory
            strategy: Resolution strategy ('keep_newest', 'keep_oldest', 'manual')
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with duplicate resolution results
        """
        result = {
            'success': True,
            'company': company_path.name,
            'duplicates_removed': [],
            'duplicates_to_remove': [],
            'space_freed_bytes': 0
        }

        try:
            # Detect duplicates first
            detection_result = self.detect_duplicates(company_path)

            if not detection_result['success']:
                return detection_result

            for dup_group in detection_result['duplicates_found']:
                files = [Path(f) for f in dup_group['files']]

                if len(files) <= 1:
                    continue

                # Determine which file to keep
                if strategy == 'keep_newest':
                    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    keep_file = files[0]
                    remove_files = files[1:]
                elif strategy == 'keep_oldest':
                    files.sort(key=lambda f: f.stat().st_mtime)
                    keep_file = files[0]
                    remove_files = files[1:]
                elif strategy == 'manual':
                    print(f"\nDuplicate files found:")
                    for i, f in enumerate(files, 1):
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        print(f"  {i}. {f.name} (modified: {mtime})")

                    choice = input(f"Which file to keep? (1-{len(files)}): ")
                    try:
                        keep_idx = int(choice) - 1
                        keep_file = files[keep_idx]
                        remove_files = [f for i, f in enumerate(files) if i != keep_idx]
                    except (ValueError, IndexError):
                        logger.warning("Invalid choice, skipping duplicate group")
                        continue
                else:
                    logger.error(f"Unknown strategy: {strategy}")
                    continue

                # Remove duplicates
                for remove_file in remove_files:
                    file_size = remove_file.stat().st_size

                    removal_info = {
                        'file': str(remove_file),
                        'kept': str(keep_file),
                        'size_bytes': file_size
                    }

                    if dry_run:
                        result['duplicates_to_remove'].append(removal_info)
                    else:
                        remove_file.unlink()
                        result['duplicates_removed'].append(removal_info)
                        result['space_freed_bytes'] += file_size
                        self.stats['duplicates_removed'] += 1

                        # Log operation
                        self._log_operation(
                            operation='remove_duplicate',
                            details=removal_info
                        )

        except Exception as e:
            logger.error(f"Duplicate resolution failed: {e}")
            result['success'] = False
            result['error'] = str(e)

        return result

    def repair_company_directory(
        self,
        company_path: Path,
        operations: Optional[List[str]] = None,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive repair of company directory.

        Args:
            company_path: Path to company directory
            operations: List of operations to perform. If None, performs all.
                       Options: ['standardize_names', 'create_dirs', 'remove_duplicates']
            dry_run: If True, only report changes without executing
            create_backup: If True, creates backup before modifications

        Returns:
            Dictionary with comprehensive repair results
        """
        if operations is None:
            operations = ['standardize_names', 'create_dirs', 'remove_duplicates']

        result = {
            'success': True,
            'company': company_path.name,
            'timestamp': datetime.now().isoformat(),
            'operations_performed': {},
            'backup_id': None,
            'errors': []
        }

        try:
            # Create backup if requested and not dry run
            if create_backup and not dry_run:
                backup_result = self.create_backup(
                    paths=[company_path],
                    description=f"Before repair: {company_path.name}"
                )

                if backup_result['success']:
                    result['backup_id'] = backup_result['backup_id']
                else:
                    logger.error("Backup creation failed, aborting repair")
                    result['success'] = False
                    result['errors'].append(backup_result.get('error', 'Backup failed'))
                    return result

            # Perform requested operations
            if 'create_dirs' in operations:
                dir_result = self.create_missing_directories(company_path, dry_run=dry_run)
                result['operations_performed']['create_directories'] = dir_result
                if not dir_result['success']:
                    result['errors'].extend(dir_result.get('errors', []))

            if 'standardize_names' in operations:
                rename_result = self.standardize_file_names(company_path, dry_run=dry_run)
                result['operations_performed']['standardize_names'] = rename_result
                if not rename_result['success']:
                    result['errors'].extend(rename_result.get('errors', []))

            if 'remove_duplicates' in operations:
                dup_result = self.resolve_duplicates(
                    company_path,
                    strategy='keep_newest',
                    dry_run=dry_run
                )
                result['operations_performed']['remove_duplicates'] = dup_result
                if not dup_result['success']:
                    result['errors'].append(dup_result.get('error', 'Duplicate removal failed'))

            self.stats['operations_performed'] += 1

        except Exception as e:
            logger.error(f"Repair operation failed: {e}")
            result['success'] = False
            result['errors'].append(str(e))

            # Attempt rollback if backup was created
            if result['backup_id'] and not dry_run:
                logger.info("Attempting rollback due to error...")
                rollback_result = self.rollback(result['backup_id'])
                result['rollback_performed'] = rollback_result['success']

        return result

    def batch_repair(
        self,
        company_tickers: Optional[List[str]] = None,
        operations: Optional[List[str]] = None,
        dry_run: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Perform batch repair operations across multiple companies.

        Args:
            company_tickers: List of tickers to repair. If None, repairs all.
            operations: List of operations to perform
            dry_run: If True, only reports changes
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with batch repair results
        """
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_companies': 0,
            'companies_repaired': 0,
            'companies_failed': 0,
            'company_results': {},
            'aggregate_statistics': {}
        }

        # Determine companies to repair
        if company_tickers:
            companies = [
                self.base_path / ticker
                for ticker in company_tickers
                if (self.base_path / ticker).exists()
            ]
        else:
            if self.base_path.exists():
                companies = [
                    d for d in self.base_path.iterdir()
                    if d.is_dir() and not d.name.startswith('.')
                ]
            else:
                result['success'] = False
                result['error'] = f"Base path does not exist: {self.base_path}"
                return result

        result['total_companies'] = len(companies)

        # Repair each company
        for i, company_path in enumerate(companies, 1):
            ticker = company_path.name

            if progress_callback:
                progress_callback(i, len(companies), ticker)

            try:
                company_result = self.repair_company_directory(
                    company_path=company_path,
                    operations=operations,
                    dry_run=dry_run,
                    create_backup=not dry_run
                )

                result['company_results'][ticker] = company_result

                if company_result['success']:
                    result['companies_repaired'] += 1
                else:
                    result['companies_failed'] += 1

            except Exception as e:
                logger.error(f"Error repairing {ticker}: {e}")
                result['company_results'][ticker] = {
                    'success': False,
                    'error': str(e)
                }
                result['companies_failed'] += 1

        # Calculate aggregate statistics
        result['aggregate_statistics'] = self._calculate_batch_statistics(result)

        return result

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _find_duplicates_by_checksum(self, directory: Path) -> List[Dict[str, Any]]:
        """Find duplicate files by checksum."""
        checksums: Dict[str, List[str]] = {}

        for file_path in directory.rglob('*.xlsx'):
            if file_path.is_file():
                checksum = self._calculate_checksum(file_path)
                if checksum not in checksums:
                    checksums[checksum] = []
                checksums[checksum].append(str(file_path))

        # Return only groups with duplicates
        duplicates = [
            {'checksum': cs, 'files': files}
            for cs, files in checksums.items()
            if len(files) > 1
        ]

        return duplicates

    def _find_duplicates_by_name(self, directory: Path) -> List[Dict[str, Any]]:
        """Find duplicate files by name."""
        names: Dict[str, List[str]] = {}

        for file_path in directory.rglob('*.xlsx'):
            if file_path.is_file():
                name = file_path.name
                if name not in names:
                    names[name] = []
                names[name].append(str(file_path))

        duplicates = [
            {'name': name, 'files': files}
            for name, files in names.items()
            if len(files) > 1
        ]

        return duplicates

    def _find_duplicates_by_content(self, directory: Path) -> List[Dict[str, Any]]:
        """Find duplicate files by exact content match."""
        # Similar to checksum method for Excel files
        return self._find_duplicates_by_checksum(directory)

    def _log_operation(self, operation: str, details: Dict[str, Any]):
        """Log repair operation to history."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details
        }
        self.repair_log.append(log_entry)

    def _calculate_batch_statistics(self, batch_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate statistics for batch operations."""
        stats = {
            'total_files_renamed': 0,
            'total_directories_created': 0,
            'total_duplicates_removed': 0,
            'total_space_freed_bytes': 0,
            'success_rate': 0.0
        }

        for ticker, company_result in batch_result['company_results'].items():
            if 'operations_performed' in company_result:
                ops = company_result['operations_performed']

                # Count renames
                if 'standardize_names' in ops:
                    stats['total_files_renamed'] += len(
                        ops['standardize_names'].get('renames_performed', [])
                    )

                # Count directories created
                if 'create_directories' in ops:
                    stats['total_directories_created'] += len(
                        ops['create_directories'].get('directories_created', [])
                    )

                # Count duplicates removed
                if 'remove_duplicates' in ops:
                    stats['total_duplicates_removed'] += len(
                        ops['remove_duplicates'].get('duplicates_removed', [])
                    )
                    stats['total_space_freed_bytes'] += ops['remove_duplicates'].get(
                        'space_freed_bytes', 0
                    )

        # Calculate success rate
        if batch_result['total_companies'] > 0:
            stats['success_rate'] = round(
                (batch_result['companies_repaired'] / batch_result['total_companies']) * 100,
                2
            )

        return stats

    def export_repair_log(self, output_path: str) -> Dict[str, Any]:
        """Export repair operation log to file."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            log_data = {
                'timestamp': datetime.now().isoformat(),
                'total_operations': len(self.repair_log),
                'statistics': self.stats,
                'operations': self.repair_log
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)

            return {
                'success': True,
                'output_path': str(output_path),
                'operations_logged': len(self.repair_log)
            }

        except Exception as e:
            logger.error(f"Log export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get current repair statistics."""
        return {
            'statistics': self.stats,
            'total_operations_logged': len(self.repair_log),
            'current_backup_id': self.current_backup_id
        }


def main():
    """CLI entry point for file system auto-repair tools."""
    import argparse

    parser = argparse.ArgumentParser(
        description='File System Auto-Repair Tools (Task 207)'
    )

    parser.add_argument(
        '--base-path',
        default='data/companies',
        help='Base directory containing company folders'
    )
    parser.add_argument(
        '--company',
        help='Specific company ticker to repair'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Repair all companies in base path'
    )
    parser.add_argument(
        '--operations',
        nargs='+',
        choices=['standardize_names', 'create_dirs', 'remove_duplicates'],
        help='Specific operations to perform (default: all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )
    parser.add_argument(
        '--auto-confirm',
        action='store_true',
        help='Skip user confirmation prompts'
    )
    parser.add_argument(
        '--rollback',
        help='Rollback to specified backup ID'
    )
    parser.add_argument(
        '--export-log',
        help='Export repair log to specified file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize auto-repair system
    repair_system = FileSystemAutoRepair(
        base_path=args.base_path,
        auto_confirm=args.auto_confirm
    )

    # Handle rollback
    if args.rollback:
        print(f"Rolling back to backup: {args.rollback}")
        result = repair_system.rollback(args.rollback)

        if result['success']:
            print(f"✅ Rollback successful: {result['items_restored']} items restored")
        else:
            print(f"❌ Rollback failed: {result.get('error')}")
        return

    # Perform repair operations
    if args.batch:
        print("Starting batch repair operation...")

        def progress_callback(current, total, ticker):
            print(f"[{current}/{total}] Repairing: {ticker}")

        result = repair_system.batch_repair(
            operations=args.operations,
            dry_run=args.dry_run,
            progress_callback=progress_callback
        )

        print(f"\n{'=' * 60}")
        print("Batch Repair Complete")
        print(f"{'=' * 60}")
        print(f"Total Companies: {result['total_companies']}")
        print(f"Successfully Repaired: {result['companies_repaired']}")
        print(f"Failed: {result['companies_failed']}")

        stats = result['aggregate_statistics']
        print(f"\nAggregate Statistics:")
        print(f"  Files Renamed: {stats['total_files_renamed']}")
        print(f"  Directories Created: {stats['total_directories_created']}")
        print(f"  Duplicates Removed: {stats['total_duplicates_removed']}")
        print(f"  Space Freed: {stats['total_space_freed_bytes'] / 1024 / 1024:.2f} MB")
        print(f"  Success Rate: {stats['success_rate']}%")

    elif args.company:
        company_path = Path(args.base_path) / args.company

        if not company_path.exists():
            print(f"❌ Company directory not found: {company_path}")
            sys.exit(1)

        print(f"Repairing company: {args.company}")
        if args.dry_run:
            print("(DRY RUN - no changes will be made)")

        result = repair_system.repair_company_directory(
            company_path=company_path,
            operations=args.operations,
            dry_run=args.dry_run,
            create_backup=not args.no_backup
        )

        if result['success']:
            print(f"\n✅ Repair completed for {args.company}")

            if result['backup_id']:
                print(f"Backup ID: {result['backup_id']}")

            for op_name, op_result in result['operations_performed'].items():
                print(f"\n{op_name}:")
                if 'renames_performed' in op_result:
                    print(f"  Files renamed: {len(op_result['renames_performed'])}")
                if 'directories_created' in op_result:
                    print(f"  Directories created: {len(op_result['directories_created'])}")
                if 'duplicates_removed' in op_result:
                    print(f"  Duplicates removed: {len(op_result['duplicates_removed'])}")
        else:
            print(f"\n❌ Repair failed for {args.company}")
            for error in result.get('errors', []):
                print(f"  Error: {error}")
    else:
        parser.print_help()
        print("\nError: Must specify either --company or --batch")
        sys.exit(1)

    # Export log if requested
    if args.export_log:
        log_result = repair_system.export_repair_log(args.export_log)
        if log_result['success']:
            print(f"\n📝 Repair log exported to: {log_result['output_path']}")
        else:
            print(f"\n❌ Log export failed: {log_result.get('error')}")

    # Display statistics
    stats = repair_system.get_statistics()
    print(f"\n{'=' * 60}")
    print("Session Statistics:")
    print(f"{'=' * 60}")
    for key, value in stats['statistics'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")


if __name__ == '__main__':
    main()
