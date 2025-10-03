"""
Validation Module
=================

Provides validation capabilities for the financial analysis system.
"""

from .excel_file_validator import (
    ExcelFileValidator,
    FileValidationResult,
    BatchValidationResult,
    ValidationSeverity,
    FileType,
    validate_excel_file,
    validate_company,
    print_validation_report
)

__all__ = [
    'ExcelFileValidator',
    'FileValidationResult',
    'BatchValidationResult',
    'ValidationSeverity',
    'FileType',
    'validate_excel_file',
    'validate_company',
    'print_validation_report'
]
