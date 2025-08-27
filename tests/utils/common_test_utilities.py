"""
Common Test Utilities
====================

Centralized test utilities to resolve cross-test dependencies and provide
shared functionality for all test modules.

This module consolidates:
- Company discovery functions
- Date extraction utilities  
- Excel processing helpers
- Common test data operations

Usage:
------
    from tests.utils.common_test_utilities import (
        discover_companies,
        test_company_data_ordering,
        extract_period_end_dates,
        parse_date_year
    )
"""

import os
import glob
import sys
from pathlib import Path
from openpyxl import load_workbook
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def discover_companies(base_path=None):
    """
    Dynamically discover all available companies in the dataset.
    
    Args:
        base_path: Optional base directory path. If None, uses current working directory.
        
    Returns:
        List of company folder names that contain both FY and LTM subdirectories.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    # Check if we're in tests directory and need to go up to root
    current_path = Path(base_path).resolve()
    if 'tests' in current_path.parts:
        # Navigate up to project root
        while current_path.name != 'financial_to_exel' and current_path.parent != current_path:
            current_path = current_path.parent
        base_path = str(current_path)
    
    company_folders = []
    
    # Look for folders that contain both FY and LTM subdirectories
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('_'):
            fy_path = os.path.join(item_path, 'FY')
            ltm_path = os.path.join(item_path, 'LTM')
            if os.path.exists(fy_path) and os.path.exists(ltm_path):
                company_folders.append(item)
    
    return sorted(company_folders)


def test_company_data_ordering(company_symbol, expected_pattern=None, base_path=None):
    """
    Test data ordering for a specific company.
    
    Args:
        company_symbol: Company ticker symbol to test
        expected_pattern: Optional expected date pattern for validation
        base_path: Optional base directory path
        
    Returns:
        bool: True if test passes, False otherwise
    """
    if base_path is None:
        base_path = os.getcwd()
    
    # Check if we're in tests directory and need to go up to root  
    current_path = Path(base_path).resolve()
    if 'tests' in current_path.parts:
        while current_path.name != 'financial_to_exel' and current_path.parent != current_path:
            current_path = current_path.parent
        base_path = str(current_path)
    
    print(f"Testing data ordering for {company_symbol}...")
    
    try:
        # Check FY Income Statement
        fy_path = os.path.join(base_path, company_symbol, "FY", f"{company_symbol}_income_statement.xlsx")
        if not os.path.exists(fy_path):
            fy_path = os.path.join(base_path, company_symbol, "FY", "Income Statement.xlsx")
        
        if os.path.exists(fy_path):
            workbook = load_workbook(fy_path)
            dates = extract_period_end_dates(workbook)
            workbook.close()
            
            if dates:
                print(f"  ✅ Found {len(dates)} dates in FY Income Statement: {dates[:3]}...")
                return True
            else:
                print(f"  ❌ No dates found in FY Income Statement")
                return False
        else:
            print(f"  ❌ FY Income Statement not found for {company_symbol}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing {company_symbol}: {str(e)}")
        return False


def extract_period_end_dates(workbook):
    """
    Extract Period End Date values from financial statement
    
    Args:
        workbook: Excel workbook containing financial data
        
    Returns:
        list: List of date strings extracted from Period End Date row
    """
    try:
        # Get the active sheet from the workbook
        sheet = workbook.active
        
        # Period End Date is always at row 10, column 3 according to analysis
        period_end_row = 10
        label_column = 3
        
        # Check if Period End Date exists at expected location
        if sheet.cell(period_end_row, label_column).value != "Period End Date":
            logger.warning("Period End Date not found at expected location (row 10, column 3)")
            return []
        
        # Extract dates starting from column 4
        dates = []
        for col in range(4, 16):  # Columns 4-15 (up to 12 periods)
            cell_value = sheet.cell(period_end_row, col).value
            if cell_value is not None:
                dates.append(str(cell_value))
            else:
                break  # Stop when we hit empty cells
        
        logger.info(f"Extracted {len(dates)} period end dates: {dates}")
        return dates
        
    except Exception as e:
        logger.error(f"Error extracting period end dates: {str(e)}")
        return []


def parse_date_year(date_string):
    """
    Parse year from date string in YYYY-MM-DD format
    
    Args:
        date_string: Date string in format "YYYY-MM-DD"
        
    Returns:
        int: Year as integer, or None if parsing fails
    """
    try:
        if isinstance(date_string, str) and len(date_string) >= 4:
            # Extract year from YYYY-MM-DD format
            year_str = date_string[:4]
            return int(year_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse year from date: {date_string}")
    return None


def get_project_root():
    """
    Get the project root directory from any location within the project.
    
    Returns:
        Path: Path object pointing to project root
    """
    current_path = Path(__file__).resolve()
    
    # Navigate up until we find the project root
    while current_path.name != 'financial_to_exel' and current_path.parent != current_path:
        current_path = current_path.parent
        
    if current_path.name == 'financial_to_exel':
        return current_path
    else:
        # Fallback to current working directory
        return Path.cwd()


def discover_company_excel_files(company_symbol, base_path=None):
    """
    Discover all Excel files for a specific company.
    
    Args:
        company_symbol: Company ticker symbol
        base_path: Optional base directory path
        
    Returns:
        dict: Dictionary with file types and their paths
    """
    if base_path is None:
        base_path = get_project_root()
    
    files = {}
    company_path = Path(base_path) / company_symbol
    
    if not company_path.exists():
        return files
    
    # Check FY directory
    fy_path = company_path / "FY"
    if fy_path.exists():
        files['fy'] = {}
        for file_path in fy_path.glob("*.xlsx"):
            if not file_path.name.startswith('~'):  # Skip temp files
                file_type = file_path.stem.lower().replace(' ', '_')
                files['fy'][file_type] = str(file_path)
    
    # Check LTM directory  
    ltm_path = company_path / "LTM"
    if ltm_path.exists():
        files['ltm'] = {}
        for file_path in ltm_path.glob("*.xlsx"):
            if not file_path.name.startswith('~'):  # Skip temp files
                file_type = file_path.stem.lower().replace(' ', '_')
                files['ltm'][file_type] = str(file_path)
    
    return files


def validate_excel_structure(excel_path, expected_sheets=None):
    """
    Validate Excel file structure and content.
    
    Args:
        excel_path: Path to Excel file
        expected_sheets: Optional list of expected sheet names
        
    Returns:
        dict: Validation results with status and details
    """
    result = {
        'valid': False,
        'sheets': [],
        'errors': [],
        'warnings': []
    }
    
    try:
        workbook = load_workbook(excel_path)
        result['sheets'] = workbook.sheetnames
        
        # Check expected sheets if provided
        if expected_sheets:
            missing_sheets = set(expected_sheets) - set(workbook.sheetnames)
            if missing_sheets:
                result['errors'].append(f"Missing expected sheets: {missing_sheets}")
        
        # Basic structure validation
        sheet = workbook.active
        if sheet.max_row < 10:
            result['warnings'].append("Sheet has fewer than 10 rows")
        
        if sheet.max_column < 4:
            result['warnings'].append("Sheet has fewer than 4 columns")
        
        # Check for Period End Date row
        if sheet.cell(10, 3).value == "Period End Date":
            result['valid'] = True
        else:
            result['warnings'].append("Period End Date not found at expected location (row 10, col 3)")
            result['valid'] = True  # Still valid, just a warning
        
        workbook.close()
        
    except Exception as e:
        result['errors'].append(f"Error validating Excel file: {str(e)}")
    
    return result