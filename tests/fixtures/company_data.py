"""
Company data fixture for centralized company discovery and management in tests.

This module eliminates the duplicate company discovery logic found across multiple test files.
"""

import os
import glob
from typing import List, Dict, Optional
import pandas as pd


class CompanyDataFixture:
    """Centralized company data discovery and management for tests"""

    def __init__(self):
        """Initialize company data fixture"""
        self._companies_cache = None
        self._excel_files_cache = {}

    def find_companies(self) -> List[str]:
        """
        Centralized company discovery logic to replace duplicate implementations

        Returns:
            List[str]: List of company ticker symbols
        """
        if self._companies_cache is None:
            # Standard company discovery pattern used across multiple test files
            companies = []
            for item in os.listdir('.'):
                if (
                    os.path.isdir(item)
                    and len(item) <= 5
                    and item.isupper()
                    and item not in ['__pycache__', '.git', 'tests']
                ):
                    companies.append(item)

            # Sort for consistent ordering
            self._companies_cache = sorted(companies)

        return self._companies_cache

    def get_company_excel_files(self, company: str) -> Dict[str, List[str]]:
        """
        Get Excel files for a specific company

        Args:
            company (str): Company ticker symbol

        Returns:
            Dict[str, List[str]]: Dictionary of statement type to file paths
        """
        if company not in self._excel_files_cache:
            excel_files = {'FY': [], 'LTM': []}

            company_folder = company
            if os.path.exists(company_folder):
                for period in ['FY', 'LTM']:
                    period_folder = os.path.join(company_folder, period)
                    if os.path.exists(period_folder):
                        excel_files[period] = glob.glob(os.path.join(period_folder, "*.xlsx"))

            self._excel_files_cache[company] = excel_files

        return self._excel_files_cache[company]

    def get_statement_file(self, company: str, period: str, statement_type: str) -> Optional[str]:
        """
        Get specific financial statement file

        Args:
            company (str): Company ticker symbol
            period (str): 'FY' or 'LTM'
            statement_type (str): Type of statement ('Income', 'Balance', 'Cash Flow')

        Returns:
            Optional[str]: Path to Excel file if found
        """
        excel_files = self.get_company_excel_files(company)

        for file_path in excel_files.get(period, []):
            if statement_type.lower() in file_path.lower():
                return file_path

        return None

    def validate_company_structure(self, company: str) -> Dict[str, bool]:
        """
        Validate company folder structure

        Args:
            company (str): Company ticker symbol

        Returns:
            Dict[str, bool]: Validation results
        """
        validation = {
            'has_fy_folder': False,
            'has_ltm_folder': False,
            'has_income_fy': False,
            'has_balance_fy': False,
            'has_cashflow_fy': False,
            'has_income_ltm': False,
            'has_balance_ltm': False,
            'has_cashflow_ltm': False,
            'is_complete': False,
        }

        company_folder = company
        if not os.path.exists(company_folder):
            return validation

        # Check for FY and LTM folders
        fy_folder = os.path.join(company_folder, 'FY')
        ltm_folder = os.path.join(company_folder, 'LTM')

        validation['has_fy_folder'] = os.path.exists(fy_folder)
        validation['has_ltm_folder'] = os.path.exists(ltm_folder)

        # Check for required statements
        statement_types = {
            'income': ['Income Statement', 'Income'],
            'balance': ['Balance Sheet', 'Balance'],
            'cashflow': ['Cash Flow Statement', 'Cash Flow'],
        }

        for period, folder in [('fy', fy_folder), ('ltm', ltm_folder)]:
            if os.path.exists(folder):
                files = os.listdir(folder)

                for stmt_key, stmt_patterns in statement_types.items():
                    found = any(
                        any(pattern.lower() in f.lower() for pattern in stmt_patterns)
                        for f in files
                    )
                    validation[f'has_{stmt_key}_{period}'] = found

        # Check if structure is complete
        required_keys = [
            'has_fy_folder',
            'has_ltm_folder',
            'has_income_fy',
            'has_balance_fy',
            'has_cashflow_fy',
            'has_income_ltm',
            'has_balance_ltm',
            'has_cashflow_ltm',
        ]

        validation['is_complete'] = all(validation[key] for key in required_keys)

        return validation

    def get_test_companies(self, require_complete: bool = True) -> List[str]:
        """
        Get companies suitable for testing

        Args:
            require_complete (bool): Only return companies with complete structure

        Returns:
            List[str]: List of company tickers suitable for testing
        """
        companies = self.find_companies()

        if not require_complete:
            return companies

        # Filter to only complete companies
        complete_companies = []
        for company in companies:
            validation = self.validate_company_structure(company)
            if validation['is_complete']:
                complete_companies.append(company)

        return complete_companies

    def clear_cache(self):
        """Clear internal caches for fresh discovery"""
        self._companies_cache = None
        self._excel_files_cache = {}
