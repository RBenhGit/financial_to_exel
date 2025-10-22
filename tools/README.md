# File System Tools

This directory contains comprehensive tools for managing and maintaining the file system organization for financial data.

## Available Tools

### 1. File System Organization Validator (`file_system_validator.py`)

**Purpose:** Comprehensive validation system for file system organization compliance.

**Features:**
- Batch validation for multiple companies
- Configuration-driven validation rules
- Detailed error reporting with remediation suggestions
- Integration with DirectoryStructureValidator
- Export to JSON, HTML, and CSV formats

**Usage:**
```bash
# Validate all companies
python tools/file_system_validator.py --base-path data/companies

# Validate specific companies
python tools/file_system_validator.py --tickers AAPL GOOGL MSFT

# Auto-fix detected issues
python tools/file_system_validator.py --auto-fix

# Export validation report
python tools/file_system_validator.py --output validation_report.html --format html
```

**Programmatic API:**
```python
from tools.file_system_validator import FileSystemOrganizationValidator

validator = FileSystemOrganizationValidator(base_path="data/companies")

# Validate all companies
results = validator.validate_all_companies(auto_fix=False)

# Validate single company
result = validator.validate_single_company(ticker="AAPL")

# Export results
validator.export_batch_results(
    output_path="reports/validation.html",
    format="html"
)
```

---

### 2. File System Auto-Repair Tools (`file_system_auto_repair.py`)

**Purpose:** Automated tools to fix common file system organization issues with comprehensive backup and rollback capabilities.

**Features:**

#### Core Capabilities
- **File Name Standardization**: Automatically rename files to match standard conventions
- **Directory Structure Creation**: Create missing FY/LTM directories
- **Duplicate Detection**: Find duplicate files by checksum, name, or content
- **Duplicate Resolution**: Remove duplicates with multiple strategies
- **Backup & Rollback**: Complete backup system with manifest and rollback
- **Batch Operations**: Repair multiple companies in one operation
- **Comprehensive Logging**: Track all operations with timestamps

#### Safety Features
- Mandatory backups before destructive operations
- User confirmation prompts
- Dry-run preview mode
- Automatic rollback on failure
- MD5 checksums for verification

**Usage:**

```bash
# Preview changes (dry run)
python tools/file_system_auto_repair.py --company AAPL --dry-run

# Repair single company
python tools/file_system_auto_repair.py --company AAPL --auto-confirm

# Repair with specific operations
python tools/file_system_auto_repair.py --company AAPL \
    --operations standardize_names create_dirs

# Batch repair all companies
python tools/file_system_auto_repair.py --batch --operations create_dirs

# Rollback to previous backup
python tools/file_system_auto_repair.py --rollback 20251022_143025_123456

# Export repair log
python tools/file_system_auto_repair.py --batch --export-log repair_log.json
```

**Programmatic API:**
```python
from pathlib import Path
from tools.file_system_auto_repair import FileSystemAutoRepair

# Initialize repair system
repair_system = FileSystemAutoRepair(
    base_path="data/companies",
    backup_dir=".backups",
    auto_confirm=False  # Prompt user for confirmations
)

# Repair single company
result = repair_system.repair_company_directory(
    company_path=Path("data/companies/AAPL"),
    operations=['create_dirs', 'standardize_names', 'remove_duplicates'],
    dry_run=False,
    create_backup=True
)

if result['success']:
    print(f"Backup ID: {result['backup_id']}")
    for op_name, op_result in result['operations_performed'].items():
        print(f"{op_name}: {len(op_result.get('renames_performed', []))} changes")
else:
    # Automatic rollback on failure
    print(f"Errors: {result['errors']}")

# Batch repair multiple companies
batch_result = repair_system.batch_repair(
    company_tickers=['AAPL', 'GOOGL', 'MSFT'],
    operations=['standardize_names'],
    dry_run=False,
    progress_callback=lambda c, t, ticker: print(f"[{c}/{t}] {ticker}")
)

print(f"Success rate: {batch_result['aggregate_statistics']['success_rate']}%")

# Rollback if needed
if not result['success'] and result['backup_id']:
    rollback_result = repair_system.rollback(result['backup_id'])
    print(f"Rollback: {rollback_result['items_restored']} items restored")
```

**Repair Operations:**

1. **standardize_names**: Rename files to standard conventions
   - `income_statement.xlsx` → `Income Statement.xlsx`
   - `balance_sheet.xlsx` → `Balance Sheet.xlsx`
   - `cash_flow.xlsx` → `Cash Flow Statement.xlsx`

2. **create_dirs**: Create missing FY/LTM directories
   - Ensures proper directory structure
   - Creates parent directories as needed

3. **remove_duplicates**: Detect and remove duplicate files
   - Strategies: keep_newest, keep_oldest, manual
   - Reports space savings

**Duplicate Detection Methods:**

- **checksum**: MD5 hash comparison (most reliable)
- **name**: Filename matching (finds same-named files in different locations)
- **content**: Byte-level comparison

**Backup System:**

Backups are stored in `.backups/` with the following structure:
```
.backups/
├── 20251022_143025_123456/
│   ├── manifest.json        # Backup metadata
│   └── AAPL/               # Backed up files
│       ├── FY/
│       └── LTM/
```

Manifest includes:
- Timestamp and description
- File checksums (MD5)
- File sizes and counts
- Original/backup path mapping

---

## Integrated Workflow: Validate → Repair → Re-validate

```python
from tools.file_system_validator import FileSystemOrganizationValidator
from tools.file_system_auto_repair import FileSystemAutoRepair

# Step 1: Validate
validator = FileSystemOrganizationValidator(base_path="data/companies")
validation = validator.validate_single_company('AAPL')

compliance = validation['overall_compliance']
print(f"Initial compliance: {compliance['overall_score']}")

# Step 2: Auto-repair if needed
if compliance['status'] != 'FULLY_COMPLIANT':
    repair_system = FileSystemAutoRepair(base_path="data/companies", auto_confirm=True)

    result = repair_system.repair_company_directory(
        company_path=Path("data/companies/AAPL"),
        operations=['create_dirs', 'standardize_names'],
        create_backup=True
    )

    if result['success']:
        print(f"✅ Repair completed! Backup: {result['backup_id']}")

        # Step 3: Re-validate
        new_validation = validator.validate_single_company('AAPL')
        new_compliance = new_validation['overall_compliance']

        print(f"New compliance: {new_compliance['overall_score']}")
        print(f"Issues fixed: {compliance['total_issues'] - new_compliance['total_issues']}")
```

## Examples and Demos

See `examples/` directory for comprehensive demos:

- **file_system_validation_demo.py**: Validation examples
- **file_system_auto_repair_demo.py**: Interactive repair demos with 5 scenarios

Run the demos:
```bash
# Validation demo
python examples/file_system_validation_demo.py

# Auto-repair interactive demo
python examples/file_system_auto_repair_demo.py
```

## Testing

Comprehensive test suites are available:

```bash
# Test validator
pytest tests/unit/validation/test_file_system_validator.py -v

# Test auto-repair tools
pytest tests/unit/tools/test_file_system_auto_repair.py -v

# Run all tests
pytest tests/unit/tools/ -v
```

## Best Practices

### 1. Always Use Dry Run First
```python
# Preview changes before applying
result = repair_system.repair_company_directory(
    company_path=company_path,
    dry_run=True  # Preview only
)

# Review what would change
print(result['operations_performed'])

# Then apply if satisfied
result = repair_system.repair_company_directory(
    company_path=company_path,
    dry_run=False,
    create_backup=True
)
```

### 2. Enable Backups for Safety
```python
# Always create backups for destructive operations
result = repair_system.repair_company_directory(
    company_path=company_path,
    create_backup=True  # IMPORTANT
)

# Keep backup ID for potential rollback
backup_id = result['backup_id']
```

### 3. Validate Before and After
```python
# Validate → Repair → Re-validate pattern
initial_validation = validator.validate_single_company(ticker)
repair_result = repair_system.repair_company_directory(company_path)
final_validation = validator.validate_single_company(ticker)

# Compare improvement
improvement = (
    initial_validation['overall_compliance']['overall_score'] -
    final_validation['overall_compliance']['overall_score']
)
```

### 4. Use Progress Callbacks for Batch
```python
def show_progress(current, total, ticker):
    percentage = (current / total) * 100
    print(f"[{current}/{total}] ({percentage:.0f}%) {ticker}")

batch_result = repair_system.batch_repair(
    company_tickers=tickers,
    progress_callback=show_progress
)
```

### 5. Export Logs for Audit Trails
```python
# Export repair operations for documentation
repair_system.export_repair_log("reports/repair_log.json")

# Export validation results
validator.export_batch_results(
    output_path="reports/validation.html",
    format="html"
)
```

## Troubleshooting

### Issue: Permission Denied

**Solution:** Run with appropriate permissions or check file locks:
```bash
# Windows: Run as administrator if needed
# Linux/Mac: Check file ownership and permissions
```

### Issue: Backup Failed

**Solution:** Check available disk space and backup directory permissions:
```python
backup_dir = Path(".backups")
backup_dir.mkdir(parents=True, exist_ok=True)
```

### Issue: Rollback Not Working

**Solution:** Verify backup ID exists:
```python
# List available backups
backup_dir = Path(".backups")
backups = list(backup_dir.iterdir())
print(f"Available backups: {[b.name for b in backups]}")
```

### Issue: Too Many Duplicates Detected

**Solution:** Review detection method and adjust strategy:
```python
# Use checksum for most accurate detection
duplicates = repair_system.detect_duplicates(
    company_path,
    comparison_method='checksum'  # Most reliable
)

# Manual resolution for complex cases
result = repair_system.resolve_duplicates(
    company_path,
    strategy='manual',  # Interactive selection
    dry_run=False
)
```

## Performance

- **Validation**: ~100ms per company
- **File Name Standardization**: ~10ms per file
- **Duplicate Detection (checksum)**: ~50ms per file
- **Backup Creation**: ~200ms per 100 files
- **Batch Operations**: ~1s per company (average)

## Contributing

When adding new repair operations:

1. Add to `FileSystemAutoRepair` class
2. Include dry-run support
3. Add backup/rollback capability
4. Create comprehensive tests
5. Update this README
6. Add example to demo script

## Related Documentation

- [Task 206: File System Organization Validator](../.taskmaster/docs/task_206_implementation_summary.md)
- [Task 207: File System Auto-Repair Tools](../.taskmaster/docs/task_207_implementation_summary.md)
- [Directory Structure Helper](../utils/directory_structure_helper.py)
- [Validation Registry](../core/validation/validation_registry.py)
