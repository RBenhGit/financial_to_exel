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
import re

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
        self.shares_outstanding = None
        
        # Automatically extract ticker symbol from folder structure
        self._auto_extract_ticker()
        
        # Cached metrics to avoid redundant calculations
        self.metrics = {}
        self.metrics_calculated = False
        
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
            
            # Clear cached metrics when new data is loaded
            self.metrics = {}
            self.metrics_calculated = False
            
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
            
            # Find the header row (contains 'FY-9', 'FY-8', etc.)
            header_row_idx = None
            for i, row in enumerate(data):
                if row and any('FY-' in str(cell) or 'FY' == str(cell) for cell in row if cell):
                    header_row_idx = i
                    break
            
            if header_row_idx is not None:
                # Use the header row and all data after it
                headers = data[header_row_idx]
                data_rows = data[header_row_idx + 1:]
                df = pd.DataFrame(data_rows, columns=headers)
            else:
                # Fallback to old method
                if len(data) > 1:
                    df = pd.DataFrame(data[1:], columns=data[0])
                else:
                    df = pd.DataFrame(data)
                
            return df
            
        except Exception as e:
            logger.error(f"Error loading Excel file {file_path}: {e}")
            return pd.DataFrame()
    
    def _extract_metric_with_ltm(self, fy_data, ltm_data, metric_name):
        """
        Extract metric values combining FY historical data with LTM latest data.
        Replaces the most recent FY data point with the most recent LTM value.
        
        Args:
            fy_data (pd.DataFrame): Fiscal year financial data
            ltm_data (pd.DataFrame): Latest twelve months financial data
            metric_name (str): Name of the metric to extract
            
        Returns:
            list: Combined metric values (FY historical + LTM latest)
        """
        try:
            # Extract FY historical data
            fy_values = self._extract_metric_values(fy_data, metric_name, reverse=True)
            
            # Extract LTM data if available
            ltm_values = []
            if not ltm_data.empty:
                ltm_values = self._extract_metric_values(ltm_data, metric_name, reverse=True)
            
            # Combine FY and LTM data
            if fy_values and ltm_values:
                # Use FY historical data (all but last) + most recent LTM value
                combined_values = fy_values[:-1] + [ltm_values[-1]]
                logger.debug(f"{metric_name}: Combined FY historical ({len(fy_values)-1} years) + LTM latest ({ltm_values[-1]:.1f})")
                return combined_values
            elif fy_values:
                # Fallback to FY data only if no LTM available
                logger.warning(f"{metric_name}: No LTM data available, using FY data only")
                return fy_values
            else:
                # No data available
                logger.warning(f"{metric_name}: No data available in FY or LTM")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting {metric_name} with LTM integration: {e}")
            # Fallback to FY data only
            return self._extract_metric_values(fy_data, metric_name, reverse=True)
    
    def _calculate_all_metrics(self):
        """
        Calculate all financial metrics needed for FCF calculations in one pass.
        This eliminates redundant calculations across different FCF methods.
        Uses LTM (Latest Twelve Months) data for the most recent data point.
        """
        if self.metrics_calculated:
            return self.metrics
            
        try:
            # Get financial data once
            income_data = self.financial_data.get('income_fy', pd.DataFrame())
            balance_data = self.financial_data.get('balance_fy', pd.DataFrame())
            cashflow_data = self.financial_data.get('cashflow_fy', pd.DataFrame())
            
            # Get LTM data for latest periods
            income_ltm = self.financial_data.get('income_ltm', pd.DataFrame())
            balance_ltm = self.financial_data.get('balance_ltm', pd.DataFrame())
            cashflow_ltm = self.financial_data.get('cashflow_ltm', pd.DataFrame())
            
            # Validate data availability
            if income_data.empty or balance_data.empty or cashflow_data.empty:
                logger.warning("Missing financial data for metrics calculation")
                return {}
            
            logger.info("Calculating all financial metrics with LTM data integration...")
            
            # Extract all required metrics once
            metrics = {}
            
            # Income statement metrics (FY historical + LTM latest)
            metrics['ebit'] = self._extract_metric_with_ltm(income_data, income_ltm, "EBIT")
            metrics['net_income'] = self._extract_metric_with_ltm(income_data, income_ltm, "Net Income")
            metrics['tax_expense'] = self._extract_metric_with_ltm(income_data, income_ltm, "Income Tax Expense")
            metrics['ebt'] = self._extract_metric_with_ltm(income_data, income_ltm, "EBT")
            
            # Balance sheet metrics (FY historical + LTM latest)
            metrics['current_assets'] = self._extract_metric_with_ltm(balance_data, balance_ltm, "Total Current Assets")
            metrics['current_liabilities'] = self._extract_metric_with_ltm(balance_data, balance_ltm, "Total Current Liabilities")
            
            # Cash flow statement metrics (FY historical + LTM latest)
            metrics['depreciation_amortization'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Depreciation & Amortization")
            metrics['operating_cash_flow'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Cash from Operations")
            metrics['capex'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Capital Expenditure")
            
            # Extract specific debt financing components for accurate FCFE calculation
            metrics['debt_issued'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Long-Term Debt Issued")
            metrics['debt_repaid'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Long-Term Debt Repaid")
            
            # Calculate derived metrics
            
            # Net Borrowing calculation (debt issued - debt repaid)
            debt_issued = metrics.get('debt_issued', [])
            debt_repaid = metrics.get('debt_repaid', [])
            
            metrics['net_borrowing'] = []
            max_length = max(len(debt_issued), len(debt_repaid)) if debt_issued or debt_repaid else 0
            
            for i in range(max_length):
                issued = debt_issued[i] if i < len(debt_issued) else 0
                repaid = debt_repaid[i] if i < len(debt_repaid) else 0
                
                # Handle NaN values (treat as 0)
                if pd.isna(issued) or issued == '':
                    issued = 0
                if pd.isna(repaid) or repaid == '':
                    repaid = 0
                    
                net_borrowing = float(issued) + float(repaid)  # repaid is already negative
                metrics['net_borrowing'].append(net_borrowing)
            
            # Tax rates calculation
            metrics['tax_rates'] = []
            ebt_values = metrics['ebt']
            tax_values = metrics['tax_expense']
            
            for i in range(len(ebt_values)):
                if ebt_values[i] != 0:
                    tax_rate = abs(tax_values[i]) / abs(ebt_values[i])
                    metrics['tax_rates'].append(min(tax_rate, 0.35))  # Cap at 35%
                else:
                    metrics['tax_rates'].append(0.25)  # Default tax rate
            
            # Working capital changes calculation
            current_assets = metrics['current_assets']
            current_liabilities = metrics['current_liabilities']
            
            metrics['working_capital_changes'] = []
            for i in range(1, len(current_assets)):
                wc_change = (current_assets[i] - current_liabilities[i]) - \
                           (current_assets[i-1] - current_liabilities[i-1])
                metrics['working_capital_changes'].append(wc_change)
            
            # Store metrics and mark as calculated
            self.metrics = metrics
            self.metrics_calculated = True
            
            logger.info(f"Calculated metrics for {len(metrics['working_capital_changes'])} years")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating financial metrics: {e}")
            return {}
    
    def calculate_fcf_to_firm(self):
        """
        Calculate Free Cash Flow to Firm (FCFF)
        FCFF = EBIT(1-Tax Rate) + Depreciation & Amortization - Change in Working Capital - Capital Expenditures
        """
        try:
            # Get pre-calculated metrics
            metrics = self._calculate_all_metrics()
            if not metrics:
                logger.warning("No metrics available for FCFF calculation")
                return []
            
            # Extract required metrics
            ebit_values = metrics.get('ebit', [])
            tax_rates = metrics.get('tax_rates', [])
            da_values = metrics.get('depreciation_amortization', [])
            capex_values = metrics.get('capex', [])
            working_capital_changes = metrics.get('working_capital_changes', [])
            
            # Calculate FCFF
            fcff_values = []
            for i in range(len(working_capital_changes)):
                if (i+1 < len(ebit_values) and i+1 < len(tax_rates) and 
                    i+1 < len(da_values) and i+1 < len(capex_values)):
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
        
        Note: Uses Net Borrowing (debt issued - debt repaid) instead of total financing cash flow
        to exclude equity transactions and dividend payments from the calculation.
        """
        try:
            # Get pre-calculated metrics
            metrics = self._calculate_all_metrics()
            if not metrics:
                logger.warning("No metrics available for FCFE calculation")
                return []
            
            # Extract required metrics
            net_income_values = metrics.get('net_income', [])
            da_values = metrics.get('depreciation_amortization', [])
            capex_values = metrics.get('capex', [])
            net_borrowing_values = metrics.get('net_borrowing', [])
            working_capital_changes = metrics.get('working_capital_changes', [])
            
            # Calculate FCFE
            fcfe_values = []
            for i in range(len(working_capital_changes)):
                if (i+1 < len(net_income_values) and i+1 < len(da_values) and 
                    i+1 < len(capex_values) and i+1 < len(net_borrowing_values)):
                    fcfe = (net_income_values[i+1] + da_values[i+1] - working_capital_changes[i] - 
                           abs(capex_values[i+1]) + net_borrowing_values[i+1])
                    fcfe_values.append(fcfe)
            
            self.fcf_results['FCFE'] = fcfe_values
            logger.info(f"FCFE calculated: {len(fcfe_values)} years using Net Borrowing")
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
            # Get pre-calculated metrics
            metrics = self._calculate_all_metrics()
            if not metrics:
                logger.warning("No metrics available for LFCF calculation")
                return []
            
            # Extract required metrics
            operating_cash_flow_values = metrics.get('operating_cash_flow', [])
            capex_values = metrics.get('capex', [])
            
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
        Calculate all three FCF types and store results.
        This method now efficiently calculates all metrics once and then computes FCF values.
        Also automatically fetches market data if ticker is available.
        """
        try:
            # Load financial statements first
            self.load_financial_statements()
            
            # Calculate all metrics once (this will be cached)
            metrics = self._calculate_all_metrics()
            if not metrics:
                logger.error("Failed to calculate financial metrics")
                return {}
            
            # Calculate all FCF types using pre-calculated metrics
            self.calculate_fcf_to_firm()
            self.calculate_fcf_to_equity()
            self.calculate_levered_fcf()
            
            # Automatically fetch market data if ticker was extracted
            if self.ticker_symbol and not self.current_stock_price:
                logger.info(f"Automatically fetching market data for {self.ticker_symbol}...")
                market_data = self.fetch_market_data()
                if market_data:
                    logger.info(f"Successfully fetched market data: Current Price=${self.current_stock_price:.2f}")
                else:
                    logger.warning(f"Could not fetch market data for {self.ticker_symbol}")
            
            logger.info("All FCF calculations completed efficiently")
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
            available_metrics = []
            
            for idx, row in df.iterrows():
                # Check the 3rd column (index 2) for metric names
                metric_text = None
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    metric_text = str(row.iloc[2])
                elif pd.notna(row.iloc[0]):
                    metric_text = str(row.iloc[0])
                
                if metric_text:
                    available_metrics.append(metric_text)
                    if metric_name.lower() in metric_text.lower():
                        metric_row = row
                        break
            
            if metric_row is None:
                logger.warning(f"Metric '{metric_name}' not found in financial data")
                logger.info(f"Available metrics: {available_metrics[:10]}...")  # Show first 10 for debugging
                return []
            
            # Extract numeric values (skip the first 3 columns which contain metadata)
            values = []
            for val in metric_row.iloc[3:]:
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
    
    def _auto_extract_ticker(self):
        """
        Automatically extract ticker symbol from company folder and financial data
        """
        if not self.company_folder:
            return
        
        # Method 1: Extract from folder name (most reliable)
        folder_name = os.path.basename(self.company_folder.rstrip('/'))
        
        # Check if folder name looks like a ticker (1-5 uppercase letters)
        if re.match(r'^[A-Z]{1,5}$', folder_name):
            self.ticker_symbol = folder_name
            logger.info(f"Auto-extracted ticker from folder name: {self.ticker_symbol}")
            return
        
        # Method 2: Try to infer from company name using mappings
        inferred_ticker = self._infer_ticker_from_company_name()
        if inferred_ticker:
            self.ticker_symbol = inferred_ticker
            logger.info(f"Auto-extracted ticker from company name mapping: {self.ticker_symbol}")
            return
        
        # Method 3: Pattern-based extraction from folder name
        pattern_ticker = self._extract_ticker_from_pattern(folder_name)
        if pattern_ticker:
            self.ticker_symbol = pattern_ticker
            logger.info(f"Auto-extracted ticker from pattern analysis: {self.ticker_symbol}")
            return
        
        logger.warning(f"Could not auto-extract ticker for company: {self.company_name}")
    
    def _infer_ticker_from_company_name(self):
        """
        Infer ticker symbol from company name using known mappings
        """
        # Common company name to ticker mappings
        name_to_ticker_map = {
            "alphabet inc class c": "GOOG",
            "alphabet inc class a": "GOOGL", 
            "tesla inc": "TSLA",
            "apple inc": "AAPL",
            "microsoft corporation": "MSFT",
            "amazon.com inc": "AMZN",
            "meta platforms inc": "META",
            "netflix inc": "NFLX",
            "visa inc": "V",
            "mastercard incorporated": "MA",
            "nvidia corporation": "NVDA",
            "berkshire hathaway inc": "BRK.B",
            "johnson & johnson": "JNJ",
            "unitedhealth group incorporated": "UNH",
            "jpmorgan chase & co": "JPM",
            "exxon mobil corporation": "XOM",
            "procter & gamble company": "PG",
            "bank of america corp": "BAC",
            "abbvie inc": "ABBV",
            "eli lilly and company": "LLY",
            "coca-cola company": "KO",
            "pepsico inc": "PEP",
            "walmart inc": "WMT",
            "home depot inc": "HD",
            "pfizer inc": "PFE",
            "verizon communications inc": "VZ",
            "at&t inc": "T",
            "intel corporation": "INTC",
            "cisco systems inc": "CSCO",
            "chevron corporation": "CVX",
            "merck & co inc": "MRK"
        }
        
        company_name_lower = self.company_name.lower()
        
        # Direct mapping lookup
        if company_name_lower in name_to_ticker_map:
            return name_to_ticker_map[company_name_lower]
        
        # Partial matching for company abbreviations
        abbreviation_map = {
            "alphabet": "GOOG",
            "tesla": "TSLA",
            "apple": "AAPL", 
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "meta": "META",
            "netflix": "NFLX",
            "visa": "V",
            "mastercard": "MA",
            "nvidia": "NVDA",
            "berkshire": "BRK.B",
            "johnson": "JNJ",
            "unitedhealth": "UNH",
            "jpmorgan": "JPM",
            "exxon": "XOM",
            "procter": "PG",
            "abbvie": "ABBV",
            "lilly": "LLY",
            "coca-cola": "KO",
            "pepsi": "PEP",
            "walmart": "WMT",
            "pfizer": "PFE",
            "verizon": "VZ",
            "intel": "INTC",
            "cisco": "CSCO",
            "chevron": "CVX",
            "merck": "MRK"
        }
        
        for company_key, ticker in abbreviation_map.items():
            if company_key in company_name_lower:
                return ticker
        
        return None
    
    def _extract_ticker_from_pattern(self, folder_name):
        """
        Extract ticker using pattern analysis
        """
        # If folder name has numbers or special chars, might be a company code
        # Try to find ticker-like patterns within it
        
        # Look for uppercase letter sequences
        matches = re.findall(r'[A-Z]{1,5}', folder_name.upper())
        
        # Filter out common non-ticker patterns
        excluded_patterns = {'INC', 'CORP', 'LLC', 'LTD', 'CO', 'CLASS'}
        
        for match in matches:
            if match not in excluded_patterns and len(match) <= 5:
                return match
        
        # If folder name is mixed case/has numbers, try extracting letters only
        letters_only = re.sub(r'[^A-Za-z]', '', folder_name).upper()
        if 1 <= len(letters_only) <= 5:
            return letters_only
        
        return None
    
    def fetch_market_data(self, ticker_symbol=None):
        """
        Fetch current market data using yfinance
        
        Args:
            ticker_symbol (str): Stock ticker symbol
            
        Returns:
            dict: Market data or None if failed
        """
        if ticker_symbol:
            self.ticker_symbol = ticker_symbol.upper()
        
        if not self.ticker_symbol:
            logger.warning("No ticker symbol available for market data fetch")
            return None
        
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.ticker_symbol)
            info = ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not current_price:
                # Try to get from recent history
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Get shares outstanding and market cap
            shares_outstanding = info.get('sharesOutstanding', 0)  # No default fallback
            market_cap = info.get('marketCap')
            
            if current_price:
                self.current_stock_price = float(current_price)
                
                # Handle shares outstanding - either direct or calculated from market cap
                if shares_outstanding and shares_outstanding > 0:
                    self.shares_outstanding = shares_outstanding
                    self.market_cap = market_cap or (current_price * shares_outstanding)
                    logger.info(f"Fetched market data for {self.ticker_symbol}: "
                               f"Price=${self.current_stock_price:.2f}, "
                               f"Shares={self.shares_outstanding/1000000:.1f}M (direct)")
                elif market_cap and market_cap > 0:
                    # Calculate shares outstanding from market cap
                    self.shares_outstanding = market_cap / current_price
                    self.market_cap = market_cap
                    logger.info(f"Fetched market data for {self.ticker_symbol}: "
                               f"Price=${self.current_stock_price:.2f}, "
                               f"Shares={self.shares_outstanding/1000000:.1f}M (calculated from market cap)")
                else:
                    # Cannot determine shares outstanding
                    self.shares_outstanding = 0
                    self.market_cap = 0
                    logger.warning(f"Cannot determine shares outstanding for {self.ticker_symbol}: "
                                  f"sharesOutstanding={shares_outstanding}, marketCap={market_cap}")
                
                return {
                    'current_price': self.current_stock_price,
                    'shares_outstanding': self.shares_outstanding,
                    'market_cap': self.market_cap,
                    'ticker_symbol': self.ticker_symbol
                }
            else:
                logger.warning(f"Could not fetch current price for {self.ticker_symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market data for {self.ticker_symbol}: {e}")
            return None