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
from data_validator import FinancialDataValidator, validate_financial_calculation_input
from config import get_config, get_dcf_config

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
        
        # Data validation components
        self.data_validator = FinancialDataValidator()
        self.data_quality_report = None
        self.validation_enabled = True
        
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
        Enhanced with comprehensive validation.
        """
        if self.metrics_calculated:
            return self.metrics
            
        try:
            # Validate financial data before processing
            if self.validation_enabled:
                logger.info("Validating financial data before metrics calculation...")
                self.data_quality_report = self.data_validator.validate_financial_statements(self.financial_data)
                
                # Log validation summary
                if self.data_quality_report.errors:
                    logger.warning(f"Found {len(self.data_quality_report.errors)} validation errors")
                if self.data_quality_report.warnings:
                    logger.info(f"Found {len(self.data_quality_report.warnings)} validation warnings")
            # Get financial data once
            income_data = self.financial_data.get('income_fy', pd.DataFrame())
            balance_data = self.financial_data.get('balance_fy', pd.DataFrame())
            cashflow_data = self.financial_data.get('cashflow_fy', pd.DataFrame())
            
            # Get LTM data for latest periods
            income_ltm = self.financial_data.get('income_ltm', pd.DataFrame())
            balance_ltm = self.financial_data.get('balance_ltm', pd.DataFrame())
            cashflow_ltm = self.financial_data.get('cashflow_ltm', pd.DataFrame())
            
            # Validate data availability
            missing_data = []
            if income_data.empty:
                missing_data.append("income statement")
            if balance_data.empty:
                missing_data.append("balance sheet")
            if cashflow_data.empty:
                missing_data.append("cash flow statement")
            
            if missing_data:
                error_msg = f"Missing required financial data: {', '.join(missing_data)}"
                logger.error(error_msg)
                if self.validation_enabled:
                    self.data_validator.report.add_error(error_msg, "Data availability")
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
            # For financial statements, missing debt data means zero activity, not missing data
            debt_issued = metrics.get('debt_issued', [])
            debt_repaid = metrics.get('debt_repaid', [])
            
            # Use the length of other comprehensive metrics to determine total years
            # This ensures net borrowing covers the full reporting period
            reference_length = len(metrics.get('net_income', []))
            if reference_length == 0:
                reference_length = len(metrics.get('ebit', []))
            
            metrics['net_borrowing'] = []
            
            # Pad debt data with zeros for years without debt activity
            debt_issued_padded = debt_issued + [0] * (reference_length - len(debt_issued))
            debt_repaid_padded = debt_repaid + [0] * (reference_length - len(debt_repaid))
            
            for i in range(reference_length):
                issued = debt_issued_padded[i] if i < len(debt_issued_padded) else 0
                repaid = debt_repaid_padded[i] if i < len(debt_repaid_padded) else 0
                
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
            # Add zero working capital change for the first year (no prior year to compare)
            metrics['working_capital_changes'].append(0)
            
            # Calculate year-over-year working capital changes for subsequent years
            for i in range(1, len(current_assets)):
                wc_change = (current_assets[i] - current_liabilities[i]) - \
                           (current_assets[i-1] - current_liabilities[i-1])
                metrics['working_capital_changes'].append(wc_change)
            
            # Final validation of calculated metrics
            if self.validation_enabled:
                final_validation = validate_financial_calculation_input(metrics)
                if final_validation.errors:
                    logger.error(f"Metrics validation failed with {len(final_validation.errors)} errors")
                    for error in final_validation.errors[:3]:  # Show first 3 errors
                        logger.error(f"  - {error['message']}")
                if final_validation.warnings:
                    logger.warning(f"Metrics validation found {len(final_validation.warnings)} warnings")
            
            # Store metrics and mark as calculated
            self.metrics = metrics
            self.metrics_calculated = True
            
            logger.info(f"Calculated metrics for {len(metrics.get('working_capital_changes', []))} years")
            
            # Log data completeness summary
            self._log_metrics_completeness(metrics)
            
            return metrics
            
        except Exception as e:
            error_msg = f"Critical error calculating financial metrics: {e}"
            logger.error(error_msg)
            if self.validation_enabled:
                self.data_validator.report.add_error(error_msg, "Metrics calculation")
            return {}
    
    def _log_metrics_completeness(self, metrics):
        """
        Log a summary of metrics completeness and data quality
        """
        logger.info("\n" + "="*50)
        logger.info("METRICS CALCULATION SUMMARY")
        logger.info("="*50)
        
        for metric_name, values in metrics.items():
            if isinstance(values, list) and values:
                non_zero_count = sum(1 for v in values if v != 0)
                zero_count = len(values) - non_zero_count
                logger.info(f"{metric_name}: {len(values)} years, {non_zero_count} non-zero, {zero_count} zero")
            elif not values:
                logger.warning(f"{metric_name}: NO DATA")
        
        # Overall assessment
        total_metrics = len(metrics)
        complete_metrics = sum(1 for values in metrics.values() if values and len(values) > 0)
        completeness_rate = (complete_metrics / total_metrics * 100) if total_metrics > 0 else 0
        
        logger.info(f"\nOverall Completeness: {complete_metrics}/{total_metrics} metrics ({completeness_rate:.1f}%)")
        
        if completeness_rate >= 90:
            logger.info("✓ EXCELLENT: High data completeness")
        elif completeness_rate >= 70:
            logger.warning("⚠ GOOD: Adequate data completeness")
        else:
            logger.error("✗ POOR: Low data completeness - review source data")
        
        logger.info("="*50)
    
    def get_data_quality_report(self):
        """
        Get the current data quality report
        
        Returns:
            DataQualityReport: Current validation report
        """
        if self.data_quality_report:
            return self.data_quality_report
        else:
            return self.data_validator.report
    
    def set_validation_enabled(self, enabled: bool):
        """
        Enable or disable data validation (for performance in testing)
        
        Args:
            enabled (bool): Whether to enable validation
        """
        self.validation_enabled = enabled
        logger.info(f"Data validation {'enabled' if enabled else 'disabled'}")
    
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
            
            # Calculate FCFF - Fix indexing alignment
            fcff_values = []
            min_length = min(len(ebit_values), len(tax_rates), len(da_values), 
                           len(capex_values), len(working_capital_changes))
            
            for i in range(min_length):
                # Use consistent indexing for all components
                after_tax_ebit = ebit_values[i] * (1 - tax_rates[i])
                fcff = after_tax_ebit + da_values[i] - working_capital_changes[i] - abs(capex_values[i])
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
            
            # Calculate FCFE - Fix indexing alignment
            fcfe_values = []
            min_length = min(len(net_income_values), len(da_values), len(capex_values), 
                           len(net_borrowing_values), len(working_capital_changes))
            
            for i in range(min_length):
                # Use consistent indexing for all components
                fcfe = (net_income_values[i] + da_values[i] - working_capital_changes[i] - 
                       abs(capex_values[i]) + net_borrowing_values[i])
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
        Enhanced with comprehensive validation and reporting.
        """
        try:
            logger.info("Starting comprehensive FCF calculation with validation...")
            
            # Load financial statements first
            self.load_financial_statements()
            
            # Calculate all metrics once (this will be cached)
            metrics = self._calculate_all_metrics()
            if not metrics:
                logger.error("Failed to calculate financial metrics - check data availability and format")
                return {}
            
            # Calculate all FCF types using pre-calculated metrics
            fcff_result = self.calculate_fcf_to_firm()
            fcfe_result = self.calculate_fcf_to_equity()
            lfcf_result = self.calculate_levered_fcf()
            
            # Validate FCF calculation results
            if self.validation_enabled:
                self._validate_fcf_results({
                    'FCFF': fcff_result,
                    'FCFE': fcfe_result,
                    'LFCF': lfcf_result
                })
            
            # Automatically fetch market data if ticker was extracted
            if self.ticker_symbol and not self.current_stock_price:
                logger.info(f"Automatically fetching market data for {self.ticker_symbol}...")
                market_data = self.fetch_market_data()
                if market_data:
                    logger.info(f"Successfully fetched market data: Current Price=${self.current_stock_price:.2f}")
                else:
                    logger.warning(f"Could not fetch market data for {self.ticker_symbol}")
            
            # Generate final data quality summary
            if self.validation_enabled:
                logger.info("\nFINAL DATA QUALITY SUMMARY:")
                quality_report = self.get_data_quality_report()
                print(quality_report.get_summary())
            
            logger.info("All FCF calculations completed efficiently")
            return self.fcf_results
            
        except Exception as e:
            error_msg = f"Critical error in FCF calculations: {e}"
            logger.error(error_msg)
            if self.validation_enabled:
                self.data_validator.report.add_error(error_msg, "FCF calculation process")
            return {}
    
    def _validate_fcf_results(self, fcf_results):
        """
        Validate the calculated FCF results for reasonableness
        
        Args:
            fcf_results (dict): Dictionary of FCF calculation results
        """
        logger.info("Validating FCF calculation results...")
        
        for fcf_type, values in fcf_results.items():
            if not values:
                self.data_validator.report.add_error(f"No {fcf_type} values calculated")
                continue
            
            # Check for extreme values
            max_val = max(abs(v) for v in values)
            if max_val > 1e12:  # > 1 trillion
                self.data_validator.report.add_warning(
                    f"{fcf_type} contains extreme values (max: {max_val:,.0f})"
                )
            
            # Check for all negative values
            if all(v < 0 for v in values):
                self.data_validator.report.add_warning(
                    f"{fcf_type} has all negative values - review business fundamentals"
                )
            
            # Check for unusual volatility
            if len(values) > 1:
                std_dev = np.std(values)
                mean_val = np.mean(values)
                if mean_val != 0 and std_dev / abs(mean_val) > 2:  # High coefficient of variation
                    self.data_validator.report.add_warning(
                        f"{fcf_type} shows high volatility (CV: {std_dev/abs(mean_val):.1f})"
                    )
        
        logger.info("FCF validation completed")
    
    def _extract_metric_values(self, df, metric_name, reverse=False):
        """
        Extract values for a specific metric from financial statement DataFrame
        Enhanced with comprehensive validation and error handling
        
        Args:
            df (pd.DataFrame): Financial statement data
            metric_name (str): Name of the metric to extract
            reverse (bool): Whether to reverse the order of values
            
        Returns:
            list: List of metric values
        """
        try:
            # Validate input DataFrame
            if df.empty:
                logger.error(f"Cannot extract '{metric_name}': DataFrame is empty")
                if self.validation_enabled:
                    self.data_validator.report.add_error(f"Empty DataFrame for metric extraction: {metric_name}")
                return []
            
            # Find row containing the metric with enhanced search
            metric_row = None
            available_metrics = []
            best_match_score = 0
            best_match_row = None
            
            for idx, row in df.iterrows():
                # Check multiple columns for metric names (more flexible matching)
                metric_text = None
                for col_idx in [0, 1, 2]:  # Check first 3 columns
                    if len(row) > col_idx and pd.notna(row.iloc[col_idx]):
                        metric_text = str(row.iloc[col_idx]).strip()
                        break
                
                if metric_text:
                    available_metrics.append(metric_text)
                    
                    # Exact match (best case)
                    if metric_name.lower() == metric_text.lower():
                        metric_row = row
                        logger.debug(f"Exact match found for '{metric_name}' at row {idx}")
                        break
                    
                    # Partial match with scoring
                    if metric_name.lower() in metric_text.lower():
                        # Calculate match score based on how much of the target is in the text
                        match_score = len(metric_name) / len(metric_text)
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match_row = row
            
            # Use best match if no exact match found
            if metric_row is None and best_match_row is not None:
                metric_row = best_match_row
                logger.info(f"Using best match for '{metric_name}' with score {best_match_score:.2f}")
            
            if metric_row is None:
                error_msg = f"Metric '{metric_name}' not found in financial data"
                logger.warning(error_msg)
                
                # Enhanced debugging information
                logger.debug(f"Searched in {len(available_metrics)} available metrics")
                if available_metrics:
                    # Show closest matches for debugging
                    closest_matches = [m for m in available_metrics if any(word in m.lower() for word in metric_name.lower().split())]
                    if closest_matches:
                        logger.info(f"Possible similar metrics: {closest_matches[:5]}")
                    else:
                        logger.info(f"Available metrics (first 10): {available_metrics[:10]}")
                
                if self.validation_enabled:
                    self.data_validator.report.add_error(error_msg, f"DataFrame with {len(available_metrics)} metrics")
                return []
            
            # Extract numeric values with enhanced validation
            values = []
            empty_count = 0
            invalid_count = 0
            
            # Skip the first 3 columns which contain metadata
            for col_idx, val in enumerate(metric_row.iloc[3:], start=3):
                context = f"{metric_name}.Column{col_idx}"
                
                if pd.isna(val) or val == '':
                    empty_count += 1
                    if self.validation_enabled:
                        validated_val, is_valid = self.data_validator.validate_cell_value(val, float, True, context)
                        values.append(validated_val)
                    else:
                        values.append(0)
                else:
                    try:
                        # Enhanced numeric conversion with validation
                        if self.validation_enabled:
                            validated_val, is_valid = self.data_validator.validate_cell_value(val, float, True, context)
                            values.append(validated_val)
                            if not is_valid:
                                invalid_count += 1
                        else:
                            # Fallback to original logic if validation disabled
                            if isinstance(val, str):
                                clean_val = val.replace(',', '').replace('(', '-').replace(')', '')
                                values.append(float(clean_val))
                            else:
                                values.append(float(val))
                    except (ValueError, TypeError) as e:
                        invalid_count += 1
                        logger.warning(f"Invalid value in {context}: {val} -> {e}")
                        values.append(0)
            
            # Log data quality information
            if empty_count > 0:
                logger.info(f"'{metric_name}': {empty_count} empty values converted to 0")
            if invalid_count > 0:
                logger.warning(f"'{metric_name}': {invalid_count} invalid values converted to 0")
            
            # Validate the extracted series
            if self.validation_enabled and values:
                self.data_validator.validate_data_series(values, metric_name)
            
            # Remove trailing zeros that might represent missing future periods
            while values and values[-1] == 0:
                values.pop()
            
            if reverse:
                values = values[::-1]
            
            # Final validation
            if not values:
                logger.warning(f"No valid data extracted for '{metric_name}'")
                if self.validation_enabled:
                    self.data_validator.report.add_warning(f"No valid data extracted for {metric_name}")
            else:
                logger.debug(f"Successfully extracted {len(values)} values for '{metric_name}'")
                
            return values
            
        except Exception as e:
            error_msg = f"Critical error extracting metric '{metric_name}': {e}"
            logger.error(error_msg)
            if self.validation_enabled:
                self.data_validator.report.add_error(error_msg, "Metric extraction function")
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
        Infer ticker symbol from company name using dynamic pattern extraction
        """
        # Use pattern-based extraction instead of hardcoded mappings
        # This makes the system work with any company without maintenance
        return self._extract_ticker_from_pattern(self.company_name)
    
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
            import time
            
            # Add retry logic for rate limiting issues with longer delays
            max_retries = 5
            retry_delay = 3  # Start with 3 seconds
            
            for attempt in range(max_retries):
                try:
                    ticker = yf.Ticker(self.ticker_symbol)
                    info = ticker.info
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Rate limited, retrying in {retry_delay} seconds... (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # More gradual exponential backoff
                        continue
                    else:
                        raise e
            
            # Get company name
            company_name = info.get('longName') or info.get('shortName') or info.get('longBusinessSummary', '').split('.')[0]
            if company_name:
                self.company_name = company_name
            else:
                # Fallback to ticker symbol if no name found
                self.company_name = self.ticker_symbol
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not current_price:
                # Try to get from recent history
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Get shares outstanding and market cap with multiple fallback options
            shares_outstanding = (info.get('sharesOutstanding') or 
                                info.get('impliedSharesOutstanding') or 
                                info.get('basicAvgSharesOutstanding') or 
                                info.get('weightedAvgSharesOutstanding') or 0)
            market_cap = (info.get('marketCap') or 
                         info.get('enterpriseValue') or 
                         info.get('impliedMarketCap'))
            
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
                    # Cannot determine shares outstanding - provide manual entry guidance
                    self.shares_outstanding = 0
                    self.market_cap = 0
                    logger.warning(f"Cannot determine shares outstanding for {self.ticker_symbol}: "
                                  f"sharesOutstanding={shares_outstanding}, marketCap={market_cap}")
                    logger.info(f"Manual entry required: Visit https://finance.yahoo.com/quote/{self.ticker_symbol}/key-statistics/ "
                               f"to find shares outstanding data")
                
                return {
                    'current_price': self.current_stock_price,
                    'shares_outstanding': self.shares_outstanding,
                    'market_cap': self.market_cap,
                    'ticker_symbol': self.ticker_symbol,
                    'company_name': self.company_name
                }
            else:
                logger.warning(f"Could not fetch current price for {self.ticker_symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market data for {self.ticker_symbol}: {e}")
            if self.validation_enabled:
                error_msg = f"Could not fetch market data: {e}"
                if "429" in str(e):
                    error_msg += ". This is likely due to Yahoo Finance rate limiting. Please wait a few minutes and try again."
                self.data_validator.report.add_warning(error_msg)
            return None