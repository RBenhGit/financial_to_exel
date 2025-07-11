"""
Financial Calculations Module

This module contains core financial calculation logic extracted from the FCF analysis tool.
It provides FCF calculations, DCF valuation, and related financial metrics.
"""

import os
import pandas as pd
import numpy as np
from openpyxl import load_workbook
import logging
from datetime import datetime
from scipy import stats
import yfinance as yf

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialCalculator:
    """
    Core financial calculations for FCF analysis and DCF valuation
    """
    
    def __init__(self, company_folder):
        """
        Initialize financial calculator with company folder path
        
        Args:
            company_folder (str): Path to company folder containing FY and LTM subfolders
        """
        self.company_folder = company_folder
        self.company_name = os.path.basename(company_folder) if company_folder else "Unknown"
        self.financial_data = {}
        self.fcf_results = {}
        self.ticker_symbol = None
        self.current_stock_price = None
        self.market_cap = None
        
    def load_financial_statements(self):
        """
        Load financial statements from Excel files
        """
        try:
            # Define file paths
            fy_folder = os.path.join(self.company_folder, 'FY')
            ltm_folder = os.path.join(self.company_folder, 'LTM')
            
            # Load FY statements
            for file_name in os.listdir(fy_folder):
                if 'Income Statement' in file_name:
                    self.financial_data['income_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
                elif 'Balance Sheet' in file_name:
                    self.financial_data['balance_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
                elif 'Cash Flow Statement' in file_name:
                    self.financial_data['cashflow_fy'] = self._load_excel_data(os.path.join(fy_folder, file_name))
            
            # Load LTM statements
            for file_name in os.listdir(ltm_folder):
                if 'Income Statement' in file_name:
                    self.financial_data['income_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                elif 'Balance Sheet' in file_name:
                    self.financial_data['balance_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                elif 'Cash Flow Statement' in file_name:
                    self.financial_data['cashflow_ltm'] = self._load_excel_data(os.path.join(ltm_folder, file_name))
                    
            logger.info("Financial statements loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading financial statements: {e}")
            raise
    
    def _load_excel_data(self, file_path):
        """
        Load Excel data and convert to DataFrame
        
        Args:
            file_path (str): Path to Excel file
            
        Returns:
            pd.DataFrame: Financial data
        """
        try:
            wb = load_workbook(filename=file_path)
            sheet = wb.active
            
            # Convert to list of lists, then to DataFrame
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append(row)
            
            # Create DataFrame with first row as headers if possible
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data)
                
            return df
            
        except Exception as e:
            logger.error(f"Error loading Excel file {file_path}: {e}")
            return pd.DataFrame()
    
    def calculate_fcf_to_firm(self):
        """
        Calculate Free Cash Flow to Firm (FCFF)
        FCFF = EBIT(1-Tax Rate) + Depreciation & Amortization - Change in Working Capital - Capital Expenditures
        """
        try:
            # Get financial data
            income_data = self.financial_data.get('income_fy', pd.DataFrame())
            balance_data = self.financial_data.get('balance_fy', pd.DataFrame())
            cashflow_data = self.financial_data.get('cashflow_fy', pd.DataFrame())
            
            if income_data.empty or balance_data.empty or cashflow_data.empty:
                logger.warning("Missing financial data for FCFF calculation")
                return []
            
            # Extract EBIT and tax data
            ebit_values = self._extract_metric_values(income_data, "EBIT", reverse=True)
            tax_values = self._extract_metric_values(income_data, "Income Tax Expense", reverse=True)
            ebt_values = self._extract_metric_values(income_data, "EBT", reverse=True)
            
            # Calculate tax rate
            tax_rates = []
            for i in range(len(ebt_values)):
                if ebt_values[i] != 0:
                    tax_rate = abs(tax_values[i]) / abs(ebt_values[i])
                    tax_rates.append(min(tax_rate, 0.35))  # Cap at 35%
                else:
                    tax_rates.append(0.25)  # Default tax rate
            
            # Extract other metrics
            da_values = self._extract_metric_values(cashflow_data, "Depreciation & Amortization", reverse=True)
            current_assets_values = self._extract_metric_values(balance_data, "Total Current Assets", reverse=True)
            current_liabilities_values = self._extract_metric_values(balance_data, "Total Current Liabilities", reverse=True)
            capex_values = self._extract_metric_values(cashflow_data, "Capital Expenditure", reverse=True)
            
            # Calculate working capital changes
            working_capital_changes = []
            for i in range(1, len(current_assets_values)):
                wc_change = (current_assets_values[i] - current_liabilities_values[i]) - \
                           (current_assets_values[i-1] - current_liabilities_values[i-1])
                working_capital_changes.append(wc_change)
            
            # Calculate FCFF
            fcff_values = []
            for i in range(len(working_capital_changes)):
                if i < len(ebit_values) and i < len(tax_rates) and i < len(da_values) and i < len(capex_values):
                    after_tax_ebit = ebit_values[i+1] * (1 - tax_rates[i+1])
                    fcff = after_tax_ebit + da_values[i+1] - working_capital_changes[i] - abs(capex_values[i+1])
                    fcff_values.append(fcff)
            
            self.fcf_results['FCFF'] = fcff_values
            logger.info(f"FCFF calculated: {len(fcff_values)} years")
            return fcff_values
            
        except Exception as e:
            logger.error(f"Error calculating FCFF: {e}")
            return []
    
    def calculate_fcf_to_equity(self):
        """
        Calculate Free Cash Flow to Equity (FCFE)
        FCFE = Net Income + Depreciation & Amortization - Change in Working Capital - Capital Expenditures + Net Borrowing
        """
        try:
            # Get financial data
            income_data = self.financial_data.get('income_fy', pd.DataFrame())
            balance_data = self.financial_data.get('balance_fy', pd.DataFrame())
            cashflow_data = self.financial_data.get('cashflow_fy', pd.DataFrame())
            
            if income_data.empty or balance_data.empty or cashflow_data.empty:
                logger.warning("Missing financial data for FCFE calculation")
                return []
            
            # Extract metrics
            net_income_values = self._extract_metric_values(income_data, "Net Income", reverse=True)
            da_values = self._extract_metric_values(cashflow_data, "Depreciation & Amortization", reverse=True)
            current_assets_values = self._extract_metric_values(balance_data, "Total Current Assets", reverse=True)
            current_liabilities_values = self._extract_metric_values(balance_data, "Total Current Liabilities", reverse=True)
            capex_values = self._extract_metric_values(cashflow_data, "Capital Expenditure", reverse=True)
            financing_values = self._extract_metric_values(cashflow_data, "Cash from Financing", reverse=True)
            
            # Calculate working capital changes
            working_capital_changes = []
            for i in range(1, len(current_assets_values)):
                wc_change = (current_assets_values[i] - current_liabilities_values[i]) - \
                           (current_assets_values[i-1] - current_liabilities_values[i-1])
                working_capital_changes.append(wc_change)
            
            # Calculate FCFE
            fcfe_values = []
            for i in range(len(working_capital_changes)):
                if (i+1 < len(net_income_values) and i+1 < len(da_values) and 
                    i+1 < len(capex_values) and i+1 < len(financing_values)):
                    fcfe = (net_income_values[i+1] + da_values[i+1] - working_capital_changes[i] - 
                           abs(capex_values[i+1]) + financing_values[i+1])
                    fcfe_values.append(fcfe)
            
            self.fcf_results['FCFE'] = fcfe_values
            logger.info(f"FCFE calculated: {len(fcfe_values)} years")
            return fcfe_values
            
        except Exception as e:
            logger.error(f"Error calculating FCFE: {e}")
            return []
    
    def calculate_levered_fcf(self):
        """
        Calculate Levered Free Cash Flow (LFCF)
        LFCF = Cash from Operations - Capital Expenditures
        """
        try:
            # Get cash flow data
            cashflow_data = self.financial_data.get('cashflow_fy', pd.DataFrame())
            
            if cashflow_data.empty:
                logger.warning("Missing cash flow data for LFCF calculation")
                return []
            
            # Extract metrics
            operating_cash_flow_values = self._extract_metric_values(cashflow_data, "Cash from Operations", reverse=True)
            capex_values = self._extract_metric_values(cashflow_data, "Capital Expenditure", reverse=True)
            
            # Calculate LFCF
            lfcf_values = []
            for i in range(len(operating_cash_flow_values)):
                if i < len(capex_values):
                    lfcf = operating_cash_flow_values[i] - abs(capex_values[i])
                    lfcf_values.append(lfcf)
            
            self.fcf_results['LFCF'] = lfcf_values
            logger.info(f"LFCF calculated: {len(lfcf_values)} years")
            return lfcf_values
            
        except Exception as e:
            logger.error(f"Error calculating LFCF: {e}")
            return []
    
    def calculate_all_fcf_types(self):
        """
        Calculate all three FCF types and store results
        """
        try:
            # Load financial statements first
            self.load_financial_statements()
            
            # Calculate all FCF types
            self.calculate_fcf_to_firm()
            self.calculate_fcf_to_equity()
            self.calculate_levered_fcf()
            
            logger.info("All FCF calculations completed")
            return self.fcf_results
            
        except Exception as e:
            logger.error(f"Error in FCF calculations: {e}")
            return {}
    
    def _extract_metric_values(self, df, metric_name, reverse=False):
        """
        Extract values for a specific metric from financial statement DataFrame
        
        Args:
            df (pd.DataFrame): Financial statement data
            metric_name (str): Name of the metric to extract
            reverse (bool): Whether to reverse the order of values
            
        Returns:
            list: List of metric values
        """
        try:
            # Find row containing the metric
            metric_row = None
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]) and metric_name.lower() in str(row.iloc[0]).lower():
                    metric_row = row
                    break
            
            if metric_row is None:
                logger.warning(f"Metric '{metric_name}' not found in financial data")
                return []
            
            # Extract numeric values (skip the first column which is the metric name)
            values = []
            for val in metric_row.iloc[1:]:
                if pd.notna(val) and val != '':
                    try:
                        # Handle different numeric formats
                        if isinstance(val, str):
                            # Remove commas and convert to float
                            clean_val = val.replace(',', '').replace('(', '-').replace(')', '')
                            values.append(float(clean_val))
                        else:
                            values.append(float(val))
                    except (ValueError, TypeError):
                        values.append(0)
            
            if reverse:
                values = values[::-1]
                
            return values
            
        except Exception as e:
            logger.error(f"Error extracting metric '{metric_name}': {e}")
            return []
    
    def calculate_growth_rates(self, values, periods=[1, 3, 5, 10]):
        """
        Calculate annualized growth rates for different periods
        
        Args:
            values (list): List of values to calculate growth rates for
            periods (list): List of periods to calculate growth rates for
            
        Returns:
            dict: Dictionary of growth rates by period
        """
        growth_rates = {}
        
        try:
            for period in periods:
                if len(values) >= period + 1:
                    start_value = values[-(period + 1)]
                    end_value = values[-1]
                    
                    if start_value != 0:
                        # Calculate annualized growth rate: (end/start)^(1/period) - 1
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        # Handle negative cash flows
                        if end_value < 0 and start_value > 0:
                            growth_rate = -growth_rate
                        elif end_value > 0 and start_value < 0:
                            growth_rate = abs(growth_rate)
                            
                        growth_rates[f"{period}Y"] = growth_rate
                    else:
                        growth_rates[f"{period}Y"] = 0
                        
        except Exception as e:
            logger.error(f"Error calculating growth rates: {e}")
            
        return growth_rates