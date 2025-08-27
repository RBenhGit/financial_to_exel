"""
Test Data Generation Utilities
==============================

Creates realistic financial statement Excel files for integration tests.
Addresses Task #28: Create Test Data Infrastructure for Integration Tests

This module provides utilities to generate mock Excel financial data that:
1. Follows the expected file structure (FY/ and LTM/ folders)
2. Uses realistic financial data patterns
3. Supports various financial scenarios (growth, distress, etc.)
4. Creates temporary directories for test isolation
5. Handles cleanup after tests complete
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

# Add pandas and openpyxl imports with error handling
try:
    import pandas as pd
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    HAS_EXCEL_SUPPORT = True
except ImportError as e:
    print(f"Warning: Excel support not available: {e}")
    HAS_EXCEL_SUPPORT = False

logger = logging.getLogger(__name__)


class TestDataScenario:
    """Represents a specific financial scenario for test data generation"""
    
    HEALTHY_GROWTH = "healthy_growth"
    FINANCIAL_DISTRESS = "financial_distress"
    MATURE_STABLE = "mature_stable"
    HIGH_GROWTH = "high_growth"
    DECLINING = "declining"
    CYCLICAL = "cyclical"


class FinancialDataGenerator:
    """Generates realistic financial statement data for testing"""
    
    def __init__(self, scenario: str = TestDataScenario.HEALTHY_GROWTH):
        self.scenario = scenario
        self.base_year = 2021
        self.years = [2021, 2022, 2023]
        self.company_templates = self._define_company_templates()
    
    def _define_company_templates(self) -> Dict[str, Dict]:
        """Define financial templates for different scenarios"""
        return {
            TestDataScenario.HEALTHY_GROWTH: {
                "revenue_growth": [0.15, 0.12, 0.10],  # 15%, 12%, 10% growth
                "operating_margin": [0.25, 0.26, 0.27],  # Improving margins
                "capex_percent": [0.08, 0.07, 0.06],  # CapEx as % of revenue
                "tax_rate": 0.21,
                "debt_to_equity": 0.3,
                "current_ratio": 2.5,
                "base_revenue": 10_000_000_000  # $10B base revenue
            },
            TestDataScenario.FINANCIAL_DISTRESS: {
                "revenue_growth": [-0.05, -0.10, -0.15],  # Declining revenue
                "operating_margin": [0.05, 0.02, -0.03],  # Deteriorating margins
                "capex_percent": [0.12, 0.15, 0.08],  # Erratic CapEx
                "tax_rate": 0.15,  # Lower due to losses
                "debt_to_equity": 1.5,  # High debt
                "current_ratio": 0.8,  # Liquidity issues
                "base_revenue": 5_000_000_000  # $5B base revenue
            },
            TestDataScenario.HIGH_GROWTH: {
                "revenue_growth": [0.35, 0.40, 0.30],  # High growth
                "operating_margin": [0.15, 0.18, 0.20],  # Scaling margins
                "capex_percent": [0.15, 0.12, 0.10],  # Heavy investment initially
                "tax_rate": 0.21,
                "debt_to_equity": 0.2,
                "current_ratio": 3.0,
                "base_revenue": 2_000_000_000  # $2B base revenue
            },
            TestDataScenario.MATURE_STABLE: {
                "revenue_growth": [0.03, 0.04, 0.03],  # Low steady growth
                "operating_margin": [0.30, 0.31, 0.30],  # Stable high margins
                "capex_percent": [0.04, 0.04, 0.04],  # Maintenance CapEx
                "tax_rate": 0.21,
                "debt_to_equity": 0.4,
                "current_ratio": 2.0,
                "base_revenue": 50_000_000_000  # $50B base revenue
            },
            TestDataScenario.DECLINING: {
                "revenue_growth": [-0.08, -0.12, -0.18],  # Steady decline
                "operating_margin": [0.10, 0.08, 0.05],  # Shrinking margins
                "capex_percent": [0.06, 0.04, 0.02],  # Reduced investment
                "tax_rate": 0.15,  # Lower due to reduced profits
                "debt_to_equity": 0.8,  # Moderate debt
                "current_ratio": 1.5,  # Adequate liquidity
                "base_revenue": 8_000_000_000  # $8B base revenue
            },
            TestDataScenario.CYCLICAL: {
                "revenue_growth": [0.20, -0.10, 0.15],  # Cyclical pattern
                "operating_margin": [0.22, 0.12, 0.25],  # Variable margins
                "capex_percent": [0.10, 0.05, 0.12],  # Cyclical investment
                "tax_rate": 0.21,
                "debt_to_equity": 0.5,
                "current_ratio": 2.2,
                "base_revenue": 12_000_000_000  # $12B base revenue
            }
        }
    
    def generate_income_statement(self) -> pd.DataFrame:
        """Generate realistic income statement data"""
        template = self.company_templates[self.scenario]
        base_revenue = template["base_revenue"]
        
        data = []
        current_revenue = base_revenue
        
        for i, year in enumerate(self.years):
            if i > 0:
                current_revenue *= (1 + template["revenue_growth"][i-1])
            
            operating_margin = template["operating_margin"][i]
            operating_income = current_revenue * operating_margin
            
            # Calculate other income statement items
            cogs = current_revenue * (1 - operating_margin - 0.15)  # Assume 15% for SG&A
            sga = current_revenue * 0.15
            depreciation = current_revenue * 0.03
            ebit = operating_income
            interest_expense = current_revenue * 0.01
            pre_tax_income = ebit - interest_expense
            tax_expense = max(0, pre_tax_income * template["tax_rate"])
            net_income = pre_tax_income - tax_expense
            
            data.append({
                "Year": year,
                "Revenue": round(current_revenue),
                "Cost of Goods Sold": round(cogs),
                "Gross Profit": round(current_revenue - cogs),
                "Selling, General & Administrative": round(sga),
                "Depreciation & Amortization": round(depreciation),
                "Operating Income": round(operating_income),
                "Interest Expense": round(interest_expense),
                "Pre-tax Income": round(pre_tax_income),
                "Tax Expense": round(tax_expense),
                "Net Income": round(net_income)
            })
        
        return pd.DataFrame(data)
    
    def generate_balance_sheet(self) -> pd.DataFrame:
        """Generate realistic balance sheet data"""
        template = self.company_templates[self.scenario]
        income_data = self.generate_income_statement()
        
        data = []
        for i, year in enumerate(self.years):
            revenue = income_data.iloc[i]["Revenue"]
            net_income = income_data.iloc[i]["Net Income"]
            
            # Assets
            cash = revenue * 0.15  # Cash as % of revenue
            receivables = revenue * 0.08  # A/R
            inventory = revenue * 0.12 if self.scenario != TestDataScenario.MATURE_STABLE else revenue * 0.05
            current_assets = cash + receivables + inventory
            
            ppe = revenue * 0.8  # Property, plant & equipment
            intangibles = revenue * 0.3
            total_assets = current_assets + ppe + intangibles
            
            # Liabilities
            payables = revenue * 0.06
            accrued = revenue * 0.04
            current_liabilities = payables + accrued
            current_debt = current_assets / template["current_ratio"] - current_liabilities
            current_liabilities += max(0, current_debt)
            
            long_term_debt = total_assets * template["debt_to_equity"] / (1 + template["debt_to_equity"])
            total_liabilities = current_liabilities + long_term_debt
            
            # Equity
            shareholders_equity = total_assets - total_liabilities
            retained_earnings = shareholders_equity * 0.7
            
            data.append({
                "Year": year,
                # Assets
                "Cash and Cash Equivalents": round(cash),
                "Accounts Receivable": round(receivables),
                "Inventory": round(inventory),
                "Current Assets": round(current_assets),
                "Property, Plant & Equipment": round(ppe),
                "Intangible Assets": round(intangibles),
                "Total Assets": round(total_assets),
                # Liabilities
                "Accounts Payable": round(payables),
                "Accrued Liabilities": round(accrued),
                "Current Liabilities": round(current_liabilities),
                "Long-term Debt": round(long_term_debt),
                "Total Liabilities": round(total_liabilities),
                # Equity
                "Shareholders' Equity": round(shareholders_equity),
                "Retained Earnings": round(retained_earnings)
            })
        
        return pd.DataFrame(data)
    
    def generate_cash_flow_statement(self) -> pd.DataFrame:
        """Generate realistic cash flow statement data"""
        template = self.company_templates[self.scenario]
        income_data = self.generate_income_statement()
        balance_data = self.generate_balance_sheet()
        
        data = []
        for i, year in enumerate(self.years):
            net_income = income_data.iloc[i]["Net Income"]
            revenue = income_data.iloc[i]["Revenue"]
            depreciation = income_data.iloc[i]["Depreciation & Amortization"]
            
            # Operating Cash Flow components
            working_capital_change = revenue * 0.01 * (-1 if i > 0 else 0)  # WC investment
            operating_cash_flow = net_income + depreciation + working_capital_change
            
            # Investing Cash Flow
            capex = revenue * template["capex_percent"][i] * -1  # Negative for cash outflow
            acquisitions = 0  # Assume no acquisitions for simplicity
            investing_cash_flow = capex + acquisitions
            
            # Financing Cash Flow
            debt_change = 0 if i == 0 else revenue * 0.02 * (1 if self.scenario == TestDataScenario.FINANCIAL_DISTRESS else -0.5)
            dividend_payments = max(0, net_income * 0.3) * -1 if net_income > 0 else 0
            financing_cash_flow = debt_change + dividend_payments
            
            # Free Cash Flow calculation
            free_cash_flow = operating_cash_flow + capex
            
            data.append({
                "Year": year,
                # Operating Activities
                "Net Income": round(net_income),
                "Depreciation & Amortization": round(depreciation),
                "Working Capital Changes": round(working_capital_change),
                "Operating Cash Flow": round(operating_cash_flow),
                # Investing Activities
                "Capital Expenditures": round(capex),
                "Acquisitions": round(acquisitions),
                "Investing Cash Flow": round(investing_cash_flow),
                # Financing Activities
                "Debt Changes": round(debt_change),
                "Dividend Payments": round(dividend_payments),
                "Financing Cash Flow": round(financing_cash_flow),
                # Calculated metrics
                "Free Cash Flow": round(free_cash_flow),
                "Net Change in Cash": round(operating_cash_flow + investing_cash_flow + financing_cash_flow)
            })
        
        return pd.DataFrame(data)


class TestDataInfrastructure:
    """Main class for managing test data infrastructure"""
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        self.base_temp_dir = base_temp_dir or tempfile.mkdtemp(prefix="financial_test_")
        self.active_directories = []
        self.data_generator = FinancialDataGenerator()
        logger.info(f"Test data infrastructure initialized at: {self.base_temp_dir}")
    
    def create_company_test_data(self, 
                                company_name: str, 
                                scenario: str = TestDataScenario.HEALTHY_GROWTH,
                                include_ltm: bool = True) -> str:
        """
        Create complete test data structure for a company
        
        Returns:
            str: Path to created company directory
        """
        if not HAS_EXCEL_SUPPORT:
            raise ImportError("Excel support (pandas, openpyxl) required for test data generation")
        
        # Create company directory structure
        company_dir = Path(self.base_temp_dir) / company_name
        fy_dir = company_dir / "FY"
        ltm_dir = company_dir / "LTM" 
        
        fy_dir.mkdir(parents=True, exist_ok=True)
        if include_ltm:
            ltm_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate financial data
        self.data_generator.scenario = scenario
        
        # Create Excel files
        self._create_excel_file(fy_dir / f"{company_name} - Income Statement.xlsx", 
                               self.data_generator.generate_income_statement())
        
        self._create_excel_file(fy_dir / f"{company_name} - Balance Sheet.xlsx", 
                               self.data_generator.generate_balance_sheet())
        
        self._create_excel_file(fy_dir / f"{company_name} - Cash Flow Statement.xlsx", 
                               self.data_generator.generate_cash_flow_statement())
        
        # Create LTM files (use latest year data)
        if include_ltm:
            # For LTM, we'll use the same data but marked as "LTM" 
            ltm_income = self.data_generator.generate_income_statement().iloc[-1:].copy()
            ltm_income["Year"] = "LTM"
            
            ltm_balance = self.data_generator.generate_balance_sheet().iloc[-1:].copy()
            ltm_balance["Year"] = "LTM"
            
            ltm_cashflow = self.data_generator.generate_cash_flow_statement().iloc[-1:].copy()
            ltm_cashflow["Year"] = "LTM"
            
            self._create_excel_file(ltm_dir / f"{company_name} - Income Statement.xlsx", ltm_income)
            self._create_excel_file(ltm_dir / f"{company_name} - Balance Sheet.xlsx", ltm_balance)
            self._create_excel_file(ltm_dir / f"{company_name} - Cash Flow Statement.xlsx", ltm_cashflow)
        
        self.active_directories.append(str(company_dir))
        logger.info(f"Created test data for {company_name} with scenario: {scenario}")
        return str(company_dir)
    
    def _create_excel_file(self, file_path: Path, dataframe: pd.DataFrame):
        """Create an Excel file from a pandas DataFrame with proper formatting"""
        try:
            with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
                
                # Format the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                
                # Style the header row
                header_font = Font(bold=True)
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.debug(f"Created Excel file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error creating Excel file {file_path}: {e}")
            raise
    
    def create_multiple_test_companies(self, companies: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create test data for multiple companies with different scenarios
        
        Args:
            companies: List of dicts with 'name' and 'scenario' keys
            
        Returns:
            Dict mapping company names to their directory paths
        """
        results = {}
        for company in companies:
            company_name = company['name']
            scenario = company.get('scenario', TestDataScenario.HEALTHY_GROWTH)
            include_ltm = company.get('include_ltm', True)
            
            path = self.create_company_test_data(company_name, scenario, include_ltm)
            results[company_name] = path
        
        return results
    
    def create_edge_case_test_data(self) -> Dict[str, str]:
        """Create test data for all edge case scenarios"""
        edge_case_companies = [
            {"name": "HEALTHY_CORP", "scenario": TestDataScenario.HEALTHY_GROWTH},
            {"name": "DISTRESSED_CORP", "scenario": TestDataScenario.FINANCIAL_DISTRESS},
            {"name": "GROWTH_CORP", "scenario": TestDataScenario.HIGH_GROWTH},
            {"name": "MATURE_CORP", "scenario": TestDataScenario.MATURE_STABLE},
            {"name": "DECLINING_CORP", "scenario": TestDataScenario.DECLINING},
            {"name": "TEST_CORP", "scenario": TestDataScenario.HEALTHY_GROWTH, "include_ltm": False},  # No LTM data
        ]
        
        return self.create_multiple_test_companies(edge_case_companies)
    
    def cleanup(self):
        """Clean up all created test directories"""
        if os.path.exists(self.base_temp_dir):
            try:
                shutil.rmtree(self.base_temp_dir)
                logger.info(f"Cleaned up test data directory: {self.base_temp_dir}")
            except Exception as e:
                logger.warning(f"Error cleaning up test directory {self.base_temp_dir}: {e}")
        
        self.active_directories.clear()
    
    def get_test_data_path(self) -> str:
        """Get the base path for test data"""
        return self.base_temp_dir
    
    def copy_msft_template(self, company_name: str) -> str:
        """Copy MSFT data structure as a template for a test company"""
        msft_path = Path.cwd() / "MSFT"
        if not msft_path.exists():
            raise FileNotFoundError("MSFT template directory not found")
        
        company_dir = Path(self.base_temp_dir) / company_name
        shutil.copytree(msft_path, company_dir)
        
        self.active_directories.append(str(company_dir))
        logger.info(f"Copied MSFT template to {company_name}")
        return str(company_dir)


# Convenience functions for common use cases

def create_test_data_for_integration_tests() -> TestDataInfrastructure:
    """Create comprehensive test data for integration tests"""
    infrastructure = TestDataInfrastructure()
    
    # Create edge case test data
    infrastructure.create_edge_case_test_data()
    
    logger.info("Integration test data infrastructure created successfully")
    return infrastructure


def create_temporary_company_data(company_name: str, 
                                 scenario: str = TestDataScenario.HEALTHY_GROWTH) -> tuple[TestDataInfrastructure, str]:
    """
    Create temporary test data for a single company
    
    Returns:
        tuple: (TestDataInfrastructure instance, company directory path)
    """
    infrastructure = TestDataInfrastructure()
    company_path = infrastructure.create_company_test_data(company_name, scenario)
    
    return infrastructure, company_path


# Context manager for automatic cleanup

class TemporaryTestData:
    """Context manager for automatic test data cleanup"""
    
    def __init__(self, companies: Optional[List[Dict[str, Any]]] = None):
        self.companies = companies
        self.infrastructure = None
        self.company_paths = {}
    
    def __enter__(self):
        self.infrastructure = TestDataInfrastructure()
        
        if self.companies:
            self.company_paths = self.infrastructure.create_multiple_test_companies(self.companies)
        else:
            self.company_paths = self.infrastructure.create_edge_case_test_data()
        
        return self.infrastructure, self.company_paths
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.infrastructure:
            self.infrastructure.cleanup()


if __name__ == "__main__":
    # Demo usage
    print("Test Data Generator Demo")
    print("=" * 50)
    
    # Create test infrastructure
    with TemporaryTestData() as (infrastructure, company_paths):
        print(f"Test data created at: {infrastructure.get_test_data_path()}")
        print(f"Created {len(company_paths)} test companies:")
        
        for company, path in company_paths.items():
            print(f"  - {company}: {path}")
            
            # Verify files exist
            fy_dir = Path(path) / "FY"
            if fy_dir.exists():
                excel_files = list(fy_dir.glob("*.xlsx"))
                print(f"    FY Excel files: {len(excel_files)}")
        
        print("\nTest data infrastructure demo completed successfully!")