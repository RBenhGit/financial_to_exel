"""
Directory Structure Validation Helper

Provides comprehensive validation and guidance for FY/LTM directory structure requirements.
This module centralizes directory structure validation logic and provides helpful error messages.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DirectoryStructureValidator:
    """
    Comprehensive directory structure validator for financial data folders.

    Validates the required FY/LTM directory structure and provides
    detailed guidance for fixing any issues found.
    """

    # Required financial statement files
    REQUIRED_STATEMENT_FILES = [
        "Income Statement.xlsx",
        "Balance Sheet.xlsx",
        "Cash Flow Statement.xlsx"
    ]

    # Alternative acceptable file patterns
    ALTERNATIVE_FILE_PATTERNS = {
        "Income Statement.xlsx": [
            "income_statement.xlsx",
            "Income Statement.xlsx",
            "income.xlsx",
            "IS.xlsx"
        ],
        "Balance Sheet.xlsx": [
            "balance_sheet.xlsx",
            "Balance Sheet.xlsx",
            "balance.xlsx",
            "BS.xlsx"
        ],
        "Cash Flow Statement.xlsx": [
            "cash_flow_statement.xlsx",
            "Cash Flow Statement.xlsx",
            "cash_flow.xlsx",
            "CF.xlsx",
            "cashflow.xlsx"
        ]
    }

    def __init__(self):
        """Initialize the validator"""
        self.validation_history = []

    def validate_company_directory(
        self,
        company_path: str,
        strict_mode: bool = False,
        suggest_fixes: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of company directory structure.

        Args:
            company_path: Path to the company directory
            strict_mode: If True, requires exact file names
            suggest_fixes: If True, includes fix suggestions in response

        Returns:
            Dictionary with detailed validation results and guidance
        """
        company_path = Path(company_path)
        validation_result = {
            'is_valid': False,
            'company_path': str(company_path),
            'exists': False,
            'issues': [],
            'warnings': [],
            'missing_folders': [],
            'missing_files': [],
            'found_files': {},
            'suggestions': [],
            'structure_score': 0.0,  # 0-1 score indicating structure completeness
            'validation_summary': '',
        }

        # Check if company directory exists
        if not company_path.exists():
            validation_result['issues'].append({
                'type': 'missing_directory',
                'message': f"Company directory does not exist: {company_path}",
                'severity': 'error',
                'fix_suggestion': self._get_directory_creation_guide(company_path) if suggest_fixes else None
            })
            validation_result['validation_summary'] = "Company directory not found"
            return validation_result

        validation_result['exists'] = True

        # Check for required period folders
        period_folders = ['FY', 'LTM']
        existing_folders = []

        for period in period_folders:
            period_path = company_path / period
            if period_path.exists():
                existing_folders.append(period)
                validation_result['found_files'][period] = self._scan_folder_files(period_path)
            else:
                validation_result['missing_folders'].append(period)
                validation_result['issues'].append({
                    'type': 'missing_folder',
                    'message': f"Missing required folder: {period}/",
                    'severity': 'error',
                    'fix_suggestion': self._get_folder_creation_guide(period) if suggest_fixes else None
                })

        # Validate files in existing folders
        for period in existing_folders:
            period_path = company_path / period
            missing_statements = self._validate_period_folder(
                period_path, period, strict_mode
            )

            if missing_statements:
                for missing_statement in missing_statements:
                    validation_result['missing_files'].append(f"{period}/{missing_statement}")
                    validation_result['issues'].append({
                        'type': 'missing_file',
                        'message': f"Missing statement file: {period}/{missing_statement}",
                        'severity': 'error' if strict_mode else 'warning',
                        'fix_suggestion': self._get_file_guidance(missing_statement) if suggest_fixes else None
                    })

        # Calculate structure completeness score
        validation_result['structure_score'] = self._calculate_structure_score(
            len(existing_folders), len(period_folders),
            validation_result['found_files']
        )

        # Determine overall validity
        validation_result['is_valid'] = (
            len(validation_result['missing_folders']) == 0 and
            (len(validation_result['missing_files']) == 0 or not strict_mode)
        )

        # Generate helpful suggestions
        if suggest_fixes and not validation_result['is_valid']:
            validation_result['suggestions'] = self._generate_fix_suggestions(validation_result)

        # Create validation summary
        validation_result['validation_summary'] = self._create_validation_summary(validation_result)

        # Store validation for history tracking
        self.validation_history.append(validation_result)

        return validation_result

    def _scan_folder_files(self, folder_path: Path) -> List[str]:
        """Scan folder and return list of Excel files found"""
        try:
            return [f.name for f in folder_path.iterdir()
                   if f.is_file() and f.suffix.lower() in ['.xlsx', '.xls']]
        except Exception as e:
            logger.warning(f"Error scanning folder {folder_path}: {e}")
            return []

    def _validate_period_folder(self, period_path: Path, period: str, strict_mode: bool) -> List[str]:
        """
        Validate files in a specific period folder (FY or LTM).

        Returns list of missing required statement files.
        """
        missing_statements = []
        found_files = self._scan_folder_files(period_path)

        for required_file in self.REQUIRED_STATEMENT_FILES:
            file_found = False

            if strict_mode:
                # Exact match required
                file_found = required_file in found_files
            else:
                # Check for alternative patterns
                patterns = self.ALTERNATIVE_FILE_PATTERNS.get(required_file, [required_file])
                for pattern in patterns:
                    if any(pattern.lower() in found_file.lower() for found_file in found_files):
                        file_found = True
                        break

            if not file_found:
                missing_statements.append(required_file)

        return missing_statements

    def _calculate_structure_score(self, existing_folders: int, total_folders: int, found_files: Dict) -> float:
        """Calculate a 0-1 score representing directory structure completeness"""
        if total_folders == 0:
            return 0.0

        # Folder score (40% of total)
        folder_score = existing_folders / total_folders * 0.4

        # File score (60% of total)
        file_score = 0.0
        total_possible_files = len(self.REQUIRED_STATEMENT_FILES) * total_folders
        total_found_files = sum(len(files) for files in found_files.values())

        if total_possible_files > 0:
            file_score = min(total_found_files / total_possible_files, 1.0) * 0.6

        return min(folder_score + file_score, 1.0)

    def _get_directory_creation_guide(self, company_path: Path) -> str:
        """Generate guide for creating the company directory structure"""
        return f"""
To create the required directory structure:

1. Create the main company folder:
   {company_path}

2. Inside the company folder, create two subfolders:
   • FY/   (for Full Year financial statements)
   • LTM/  (for Last Twelve Months statements)

3. Add the required Excel files to each subfolder:
   • Income Statement.xlsx
   • Balance Sheet.xlsx
   • Cash Flow Statement.xlsx

Complete structure:
{company_path}/
├── FY/
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx
│   └── Cash Flow Statement.xlsx
└── LTM/
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx
        """

    def _get_folder_creation_guide(self, folder_name: str) -> str:
        """Generate guide for creating a specific period folder"""
        purpose = {
            'FY': 'Full Year financial statements (annual data)',
            'LTM': 'Last Twelve Months financial statements (rolling 12-month data)'
        }.get(folder_name, 'Financial statements')

        return f"""
Create the {folder_name}/ folder for {purpose}:

1. Create folder: {folder_name}/
2. Add required Excel files:
   • Income Statement.xlsx
   • Balance Sheet.xlsx
   • Cash Flow Statement.xlsx

Each Excel file should contain:
   • Column headers like 'FY', 'FY-1', 'FY-2', etc.
   • Financial data organized by year/period
   • Proper metric labels in the first column
        """

    def _get_file_guidance(self, filename: str) -> str:
        """Generate guidance for creating a specific Excel file"""
        file_guidance = {
            "Income Statement.xlsx": """
Income Statement should contain:
• Revenue/Sales figures
• Cost of revenues/COGS
• Operating expenses (R&D, SG&A)
• Operating income/EBIT
• Interest expenses
• Net income
• Column headers: FY, FY-1, FY-2, etc.
            """,
            "Balance Sheet.xlsx": """
Balance Sheet should contain:
• Current assets (cash, receivables, inventory)
• Total assets
• Current liabilities
• Long-term debt
• Shareholders' equity
• Column headers: FY, FY-1, FY-2, etc.
            """,
            "Cash Flow Statement.xlsx": """
Cash Flow Statement should contain:
• Cash from operations
• Capital expenditures
• Free cash flow
• Debt issuance/repayment
• Dividend payments
• Column headers: FY, FY-1, FY-2, etc.
            """
        }

        return file_guidance.get(filename, f"Create {filename} with proper financial data and FY column headers.")

    def _generate_fix_suggestions(self, validation_result: Dict) -> List[str]:
        """Generate actionable fix suggestions based on validation results"""
        suggestions = []

        if not validation_result['exists']:
            suggestions.append("Create the company directory at the specified path")
            suggestions.append("Set up the complete FY/LTM folder structure")
            return suggestions

        if validation_result['missing_folders']:
            for folder in validation_result['missing_folders']:
                suggestions.append(f"Create the {folder}/ subfolder")
                suggestions.append(f"Add required Excel files to the {folder}/ folder")

        if validation_result['missing_files']:
            file_types = set()
            for missing_file in validation_result['missing_files']:
                file_type = missing_file.split('/')[-1]
                file_types.add(file_type)

            for file_type in file_types:
                suggestions.append(f"Create or fix the {file_type} file")

        # Add general suggestions based on structure score
        score = validation_result['structure_score']
        if score < 0.3:
            suggestions.append("Consider using the provided directory structure template")
        elif score < 0.7:
            suggestions.append("Review Excel file formats and column headers")

        return suggestions

    def _create_validation_summary(self, validation_result: Dict) -> str:
        """Create a concise validation summary message"""
        if validation_result['is_valid']:
            return "✅ Directory structure is valid and complete"

        issues = len(validation_result['issues'])
        score = validation_result['structure_score']

        if not validation_result['exists']:
            return "❌ Company directory not found"
        elif score < 0.3:
            return f"❌ Major structure issues found ({issues} problems)"
        elif score < 0.7:
            return f"⚠️ Structure partially complete ({issues} issues remaining)"
        else:
            return f"⚠️ Minor structure issues ({issues} issues to resolve)"

    def create_directory_structure_from_template(
        self,
        company_path: str,
        company_name: str = None
    ) -> Dict[str, Any]:
        """
        Create the complete directory structure from template.

        Args:
            company_path: Path where to create the structure
            company_name: Optional company name for folder naming

        Returns:
            Dictionary with creation results
        """
        company_path = Path(company_path)
        creation_result = {
            'success': False,
            'created_folders': [],
            'created_files': [],
            'errors': []
        }

        try:
            # Create main company folder
            company_path.mkdir(parents=True, exist_ok=True)
            creation_result['created_folders'].append(str(company_path))

            # Create period folders
            for period in ['FY', 'LTM']:
                period_path = company_path / period
                period_path.mkdir(exist_ok=True)
                creation_result['created_folders'].append(str(period_path))

                # Create placeholder Excel files with basic structure
                for statement_file in self.REQUIRED_STATEMENT_FILES:
                    file_path = period_path / statement_file
                    if not file_path.exists():
                        self._create_template_excel_file(file_path, statement_file, period, company_name)
                        creation_result['created_files'].append(str(file_path))

            creation_result['success'] = True
            logger.info(f"Successfully created directory structure at {company_path}")

        except Exception as e:
            error_msg = f"Failed to create directory structure: {str(e)}"
            creation_result['errors'].append(error_msg)
            logger.error(error_msg)

        return creation_result

    def _create_template_excel_file(self, file_path: Path, statement_type: str, period: str, company_name: str = None):
        """Create a template Excel file with basic structure"""
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill

            # Create workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = statement_type.replace('.xlsx', '')

            # Add headers
            headers = ['Metric'] + [f'FY-{i}' for i in range(9, -1, -1)] + ['FY']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

            # Add sample rows based on statement type
            if "Income Statement" in statement_type:
                sample_rows = ["Revenue", "Cost of Revenues", "Gross Profit", "Operating Expenses",
                              "Operating Income", "Interest Expense", "Net Income"]
            elif "Balance Sheet" in statement_type:
                sample_rows = ["Total Current Assets", "Total Assets", "Total Current Liabilities",
                              "Long-term Debt", "Total Shareholders Equity"]
            elif "Cash Flow" in statement_type:
                sample_rows = ["Cash from Operations", "Capital Expenditures", "Free Cash Flow",
                              "Net Borrowings", "Dividends Paid"]
            else:
                sample_rows = ["Sample Metric 1", "Sample Metric 2", "Sample Metric 3"]

            # Add sample rows
            for row, metric in enumerate(sample_rows, 2):
                ws.cell(row=row, column=1, value=metric)

            # Add instruction note
            instruction = f"""
INSTRUCTIONS:
1. Replace sample metrics with actual {statement_type.replace('.xlsx', '')} data
2. Fill in historical data under FY-9 through FY columns
3. Ensure all financial figures are in consistent units (e.g., millions)
4. {period} = {'Full Year data' if period == 'FY' else 'Last Twelve Months data'}
{f'5. Company: {company_name}' if company_name else ''}

This is a template file - please replace with your actual financial data.
            """

            ws.cell(row=len(sample_rows) + 4, column=1, value=instruction)

            # Save the file
            wb.save(file_path)
            logger.debug(f"Created template Excel file: {file_path}")

        except ImportError:
            # If openpyxl not available, create a simple CSV
            try:
                import csv
                csv_path = file_path.with_suffix('.csv')
                with open(csv_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    headers = ['Metric'] + [f'FY-{i}' for i in range(9, -1, -1)] + ['FY']
                    writer.writerow(headers)
                    writer.writerow(['Sample Metric', ''] * len(headers[1:]))
                logger.debug(f"Created template CSV file: {csv_path} (Excel not available)")
            except Exception as e:
                logger.warning(f"Could not create template file {file_path}: {e}")

        except Exception as e:
            logger.warning(f"Could not create template Excel file {file_path}: {e}")

    def get_validation_help_text(self) -> str:
        """Get comprehensive help text for directory structure requirements"""
        return """
📁 Financial Data Directory Structure Requirements

REQUIRED STRUCTURE:
CompanyName/
├── FY/                     (Full Year Financial Statements)
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx
│   └── Cash Flow Statement.xlsx
└── LTM/                    (Last Twelve Months Statements)
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx

📋 EXCEL FILE REQUIREMENTS:
• Column headers: 'FY', 'FY-1', 'FY-2', etc. (historical periods)
• First column: Metric names (e.g., "Revenue", "Net Income")
• Data rows: Financial values for each period
• Format: .xlsx (Excel 2007+)

📊 STATEMENT CONTENT GUIDELINES:

Income Statement:
• Revenue, Cost of Revenues, Gross Profit
• Operating Expenses (R&D, SG&A)
• Operating Income, Interest Expense, Net Income

Balance Sheet:
• Current Assets, Total Assets
• Current Liabilities, Long-term Debt
• Shareholders' Equity

Cash Flow Statement:
• Cash from Operations, Capital Expenditures
• Free Cash Flow, Debt Changes, Dividends

💡 TIPS:
• Ensure consistent units (e.g., all values in millions)
• Include at least 3-5 years of historical data
• Use standard accounting terminology
• Keep metric names consistent across periods
        """


# Convenience functions for common operations

def validate_company_directory(company_path: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to validate a company directory structure.

    Args:
        company_path: Path to company directory
        **kwargs: Additional arguments for DirectoryStructureValidator

    Returns:
        Validation results dictionary
    """
    validator = DirectoryStructureValidator()
    return validator.validate_company_directory(company_path, **kwargs)


def create_directory_structure_template(company_path: str, company_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to create directory structure from template.

    Args:
        company_path: Path where to create structure
        company_name: Optional company name

    Returns:
        Creation results dictionary
    """
    validator = DirectoryStructureValidator()
    return validator.create_directory_structure_from_template(company_path, company_name)


def get_directory_structure_help() -> str:
    """
    Get comprehensive help text for directory structure requirements.

    Returns:
        Help text string
    """
    validator = DirectoryStructureValidator()
    return validator.get_validation_help_text()