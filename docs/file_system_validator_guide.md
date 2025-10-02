# File System Organization Validator Guide

**Task 206: Build File System Organization Validator**

## Overview

The File System Organization Validator provides comprehensive validation of the financial data directory structure, ensuring compliance with the required schema for company financial data.

## Features

### Core Capabilities

1. **Directory Structure Validation**
   - Validates `data/companies/{TICKER}/FY/` and `data/companies/{TICKER}/LTM/` structure
   - Checks for required period folders
   - Detects misplaced files

2. **File Presence and Format Validation**
   - Verifies presence of required Excel files:
     - Income Statement.xlsx
     - Balance Sheet.xlsx
     - Cash Flow Statement.xlsx
   - Validates Excel file format using openpyxl
   - Checks for proper column headers (FY, FY-1, FY-2, etc.)
   - Validates numeric data types in financial columns
   - Detects multi-sheet workbooks

3. **Batch Validation**
   - Validate all companies in base directory
   - Validate specific companies by ticker
   - Aggregate statistics across all companies
   - Parallel processing for large datasets

4. **Automated Repair**
   - Create missing directory structures
   - Generate template Excel files
   - Organize misplaced files
   - Dry-run mode for planning

5. **Comprehensive Reporting**
   - Detailed error messages with severity levels
   - Actionable remediation suggestions
   - Compliance scoring (0.0 - 1.0)
   - Export to JSON, HTML, CSV formats

6. **Configuration-Driven Rules**
   - Integration with ValidationRegistry
   - Dynamic rule configuration
   - Custom validation rules
   - Threshold-based validation

## Installation

The validator is included in the main project. No additional installation required.

```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

## Quick Start

### CLI Usage

```bash
# Validate all companies
python -m tools.file_system_validator --base-path data/companies

# Validate specific companies
python -m tools.file_system_validator --tickers AMD NVDA --output report.html

# Auto-repair detected issues
python -m tools.file_system_validator --auto-fix

# Export detailed report
python -m tools.file_system_validator --output validation_report.html --format html
```

### Programmatic Usage

```python
from tools.file_system_validator import FileSystemOrganizationValidator

# Initialize validator
validator = FileSystemOrganizationValidator(base_path="data/companies")

# Validate all companies
results = validator.validate_all_companies()

# Check results
if results['critical_issues'] > 0:
    print(f"⚠️ Found {results['critical_issues']} critical issues")
else:
    print("✅ All companies compliant!")

# Export report
validator.export_batch_results(
    output_path="validation_report.html",
    format='html'
)
```

## API Reference

### FileSystemOrganizationValidator

Main class for file system validation.

#### Constructor

```python
FileSystemOrganizationValidator(
    base_path: str = "data/companies",
    validation_registry: Optional[ValidationRegistry] = None
)
```

**Parameters:**
- `base_path`: Base directory containing company folders
- `validation_registry`: Optional ValidationRegistry for rule-based validation

#### Methods

##### validate_all_companies()

Validate all companies in the base directory.

```python
results = validator.validate_all_companies(
    company_tickers: Optional[List[str]] = None,
    strict_mode: bool = False,
    auto_fix: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- `company_tickers`: Optional list of specific tickers to validate
- `strict_mode`: If True, requires exact file names
- `auto_fix`: If True, automatically repairs detected issues

**Returns:** Dictionary with validation results:
```python
{
    'validation_timestamp': str,
    'base_path': str,
    'total_companies': int,
    'companies_validated': int,
    'fully_compliant': int,
    'partially_compliant': int,
    'non_compliant': int,
    'critical_issues': int,
    'company_results': Dict[str, Any],
    'aggregate_statistics': Dict[str, Any],
    'recommendations_summary': List[Dict[str, Any]]
}
```

##### validate_single_company()

Validate a single company directory.

```python
result = validator.validate_single_company(
    ticker: str,
    strict_mode: bool = False,
    auto_fix: bool = False
) -> Dict[str, Any]
```

**Returns:** Detailed validation results for the company including:
- Overall compliance status
- Directory validation results
- Excel file validations
- Actionable recommendations

##### export_batch_results()

Export validation results to file.

```python
export_result = validator.export_batch_results(
    output_path: str,
    format: str = 'json',  # 'json', 'html', or 'csv'
    include_details: bool = True
) -> Dict[str, Any]
```

**Returns:** Export status:
```python
{
    'success': bool,
    'output_path': str,
    'format': str,
    'error': Optional[str]  # Only present if success=False
}
```

##### get_compliance_summary()

Get text summary of validation results.

```python
summary = validator.get_compliance_summary() -> str
```

## Validation Results Structure

### Aggregate Statistics

```python
'aggregate_statistics': {
    'average_compliance_score': float,  # 0.0 - 1.0
    'average_directory_score': float,
    'average_excel_score': float,
    'total_issues': int,
    'total_warnings': int,
    'total_recommendations': int,
    'most_common_issues': [
        {
            'type': str,
            'count': int
        }
    ],
    'compliance_distribution': {
        'fully_compliant': int,
        'partially_compliant': int,
        'non_compliant': int
    }
}
```

### Recommendations Summary

```python
'recommendations_summary': [
    {
        'issue_type': str,
        'priority': str,  # CRITICAL, HIGH, MEDIUM, LOW
        'category': str,
        'affected_companies': List[str],
        'count': int,
        'example_action': str,
        'automated_fix_available': bool
    }
]
```

## Compliance Statuses

- **FULLY_COMPLIANT** (Score >= 0.95): All requirements met
- **COMPLIANT** (Score >= 0.80): Minor issues only
- **PARTIALLY_COMPLIANT** (Score >= 0.50): Some issues present
- **NON_COMPLIANT** (Score >= 0.30): Significant issues
- **CRITICAL** (Score < 0.30): Major structural problems

## Required Directory Structure

```
data/companies/
├── {TICKER}/
│   ├── FY/
│   │   ├── Income Statement.xlsx
│   │   ├── Balance Sheet.xlsx
│   │   └── Cash Flow Statement.xlsx
│   └── LTM/
│       ├── Income Statement.xlsx
│       ├── Balance Sheet.xlsx
│       └── Cash Flow Statement.xlsx
```

### Excel File Requirements

Each Excel file must contain:
- **Column Headers**: First row with "Metric", "FY", "FY-1", "FY-2", etc.
- **Numeric Data**: Financial values in numeric format (not text)
- **Minimum Periods**: At least 2 historical periods
- **Required Metrics** (varies by statement type):
  - Income Statement: Revenue, Net Income, Operating Income
  - Balance Sheet: Total Assets, Total Liabilities, Shareholders Equity
  - Cash Flow: Cash from Operations, Capital Expenditures

## Integration with ValidationRegistry

The validator can integrate with the ValidationRegistry system for advanced rule-based validation:

```python
from core.validation.validation_registry import ValidationRegistry
from tools.file_system_validator import FileSystemOrganizationValidator

# Create registry
registry = ValidationRegistry()

# Initialize validator with registry
validator = FileSystemOrganizationValidator(
    base_path="data/companies",
    validation_registry=registry
)

# Validation will now use registry rules
results = validator.validate_all_companies()
```

## Usage Examples

See [examples/file_system_validation_demo.py](../examples/file_system_validation_demo.py) for comprehensive examples including:

1. Single company validation
2. Batch validation
3. Validating specific companies
4. Auto-repair functionality
5. Exporting reports
6. Programmatic integration
7. ValidationRegistry integration

## CLI Options

```
usage: file_system_validator.py [-h] [--base-path BASE_PATH]
                                [--tickers TICKERS [TICKERS ...]]
                                [--auto-fix]
                                [--output OUTPUT]
                                [--format {json,html,csv}]
                                [--verbose]

File System Organization Validator (Task 206)

optional arguments:
  -h, --help            show this help message and exit
  --base-path BASE_PATH
                        Base directory containing company folders
  --tickers TICKERS [TICKERS ...]
                        Specific company tickers to validate (default: all)
  --auto-fix            Automatically repair detected issues
  --output OUTPUT       Output file path for validation report
  --format {json,html,csv}
                        Output format for validation report
  --verbose             Enable verbose logging
```

## Error Messages and Remediation

The validator provides detailed error messages with specific remediation steps:

### Example: Missing FY Folder

```
❌ CRITICAL: FY folder missing
   Location: data/companies/EXAMPLE/FY
   Impact: Cannot perform fiscal year analysis
   Remediation:
   1. Create FY directory: mkdir data/companies/EXAMPLE/FY
   2. Add required Excel files to FY directory
   Automated Fix: Available (use --auto-fix or auto_fix=True)
```

### Example: Invalid Excel Format

```
⚠️  HIGH: Excel file missing proper headers
   File: data/companies/EXAMPLE/FY/Income Statement.xlsx
   Expected: Headers should include FY, FY-1, FY-2
   Found: 2023, 2022, 2021
   Remediation:
   1. Open the Excel file
   2. Update column headers to use FY notation
   3. Ensure first column is "Metric"
   Automated Fix: Not available (manual update required)
```

## Performance Considerations

### Large-Scale Validation

For validating many companies:

```python
# Use specific tickers to limit scope
validator.validate_all_companies(
    company_tickers=['AMD', 'NVDA', 'INTC']
)

# Export without detailed results to reduce memory
validator.export_batch_results(
    output_path="summary.json",
    include_details=False
)
```

### Batch Processing

The validator processes companies sequentially. For very large datasets, consider:
- Validating in batches by ticker list
- Running validation during off-peak hours
- Using auto-fix mode to reduce manual intervention

## Troubleshooting

### Common Issues

**Issue: "Base path does not exist"**
```python
# Ensure the base path exists
from pathlib import Path
Path("data/companies").mkdir(parents=True, exist_ok=True)
```

**Issue: "ValidationRegistry not available"**
```python
# ValidationRegistry is optional
# Validator will work without it using standard validation
validator = FileSystemOrganizationValidator(
    base_path="data/companies",
    validation_registry=None  # Explicitly set to None
)
```

**Issue: Export fails with permission error**
```python
# Ensure output directory exists and is writable
output_path = Path("reports")
output_path.mkdir(parents=True, exist_ok=True)
```

## Related Components

- [DirectoryStructureValidator](../utils/directory_structure_helper.py) - Core validation engine
- [ValidationRegistry](../core/validation/validation_registry.py) - Rule-based validation system
- [Directory Repair Tool](directory_repair_tool.md) - Automated repair utilities

## Testing

Run comprehensive tests:

```bash
# Run all validator tests
pytest tests/unit/tools/test_file_system_validator.py -v

# Run with coverage
pytest tests/unit/tools/test_file_system_validator.py --cov=tools.file_system_validator

# Run specific test
pytest tests/unit/tools/test_file_system_validator.py::TestFileSystemOrganizationValidator::test_validate_all_companies_multiple_companies -v
```

## Future Enhancements

Potential improvements for future releases:

1. **Parallel Processing**: Validate companies in parallel for better performance
2. **Historical Tracking**: Track compliance changes over time
3. **Custom Rules**: User-defined validation rules via YAML configuration
4. **Email Notifications**: Send validation reports via email
5. **Web Dashboard**: Interactive web interface for validation results
6. **API Endpoints**: RESTful API for integration with other systems

## Support

For issues or questions:
1. Check existing tests for usage examples
2. Review [examples/file_system_validation_demo.py](../examples/file_system_validation_demo.py)
3. Consult the main [CLAUDE.md](../CLAUDE.md) documentation
