"""
Centralized Data Processing Module

This module provides centralized financial data processing capabilities
that work with the CentralizedDataManager to eliminate redundancy and
provide consistent data processing across the application.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from scipy import stats
import json

from centralized_data_manager import CentralizedDataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result container for data processing operations"""
    data: Any
    success: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

@dataclass
class FinancialMetrics:
    """Standardized financial metrics container"""
    ebit: List[float]
    net_income: List[float]
    tax_expense: List[float]
    ebt: List[float]
    current_assets: List[float]
    current_liabilities: List[float]
    depreciation_amortization: List[float]
    operating_cash_flow: List[float]
    capex: List[float]
    debt_issued: List[float]
    debt_repaid: List[float]
    net_borrowing: List[float]
    tax_rates: List[float]
    working_capital_changes: List[float]
    years: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'ebit': self.ebit,
            'net_income': self.net_income,
            'tax_expense': self.tax_expense,
            'ebt': self.ebt,
            'current_assets': self.current_assets,
            'current_liabilities': self.current_liabilities,
            'depreciation_amortization': self.depreciation_amortization,
            'operating_cash_flow': self.operating_cash_flow,
            'capex': self.capex,
            'debt_issued': self.debt_issued,
            'debt_repaid': self.debt_repaid,
            'net_borrowing': self.net_borrowing,
            'tax_rates': self.tax_rates,
            'working_capital_changes': self.working_capital_changes,
            'years': self.years
        }

@dataclass
class FCFResults:
    """Free Cash Flow calculation results"""
    fcff: List[float]  # Free Cash Flow to Firm
    fcfe: List[float]  # Free Cash Flow to Equity
    lfcf: List[float]  # Levered Free Cash Flow
    years: List[str]
    growth_rates: Dict[str, List[float]]
    averages: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'fcff': self.fcff,
            'fcfe': self.fcfe,
            'lfcf': self.lfcf,
            'years': self.years,
            'growth_rates': self.growth_rates,
            'averages': self.averages
        }

class CentralizedDataProcessor:
    """
    Centralized data processing engine that works with CentralizedDataManager
    to provide consistent financial data processing across the application.
    
    Features:
    - Standardized metric extraction and calculation
    - Cached FCF calculations
    - Growth rate analysis
    - Data quality validation
    - Comprehensive error handling
    """
    
    def __init__(self, data_manager: CentralizedDataManager):
        """
        Initialize the centralized data processor.
        
        Args:
            data_manager (CentralizedDataManager): Data manager instance
        """
        self.data_manager = data_manager
        self.processing_config = {
            'max_tax_rate': 0.35,
            'default_tax_rate': 0.25,
            'growth_rate_periods': [1, 3, 5, 10],
            'outlier_threshold': 3.0,  # Standard deviations
            'missing_value_strategy': 'interpolate'
        }
        
        logger.info("Centralized Data Processor initialized")
    
    def extract_financial_metrics(self, company_folder: str, force_reload: bool = False) -> ProcessingResult:
        """
        Extract and standardize financial metrics from company data.
        
        Args:
            company_folder (str): Company folder name
            force_reload (bool): Force reload even if cached
            
        Returns:
            ProcessingResult: Standardized financial metrics
        """
        # Generate cache key
        cache_key = self.data_manager._generate_cache_key('financial_metrics', {'company': company_folder})
        
        # Check cache first
        if not force_reload:
            cached_result = self.data_manager.get_cached_data(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached financial metrics for {company_folder}")
                return cached_result
        
        logger.info(f"Extracting financial metrics for {company_folder}")
        
        try:
            # Load financial data
            financial_data = self.data_manager.load_excel_data(company_folder)
            
            # Initialize result containers
            errors = []
            warnings = []
            
            # Validate required data availability
            required_datasets = ['income_fy', 'balance_fy', 'cashflow_fy']
            missing_datasets = [ds for ds in required_datasets if ds not in financial_data or financial_data[ds].empty]
            
            if missing_datasets:
                error_msg = f"Missing required datasets: {', '.join(missing_datasets)}"
                errors.append(error_msg)
                return ProcessingResult(
                    data=None,
                    success=False,
                    errors=errors,
                    warnings=warnings,
                    metadata={'company': company_folder}
                )
            
            # Extract metrics from each dataset
            metrics = self._extract_all_metrics(financial_data, errors, warnings)
            
            # Create standardized metrics object
            financial_metrics = FinancialMetrics(**metrics)
            
            # Create result
            result = ProcessingResult(
                data=financial_metrics,
                success=True,
                errors=errors,
                warnings=warnings,
                metadata={
                    'company': company_folder,
                    'extraction_time': datetime.now().isoformat(),
                    'years_processed': len(metrics.get('years', [])),
                    'metrics_count': len([k for k in metrics.keys() if k != 'years'])
                }
            )
            
            # Cache the result
            self.data_manager.cache_data(cache_key, result, 'financial_metrics', expiry_hours=24)
            
            logger.info(f"Successfully extracted financial metrics for {company_folder}")
            return result
            
        except Exception as e:
            error_msg = f"Error extracting financial metrics: {str(e)}"
            logger.error(error_msg)
            return ProcessingResult(
                data=None,
                success=False,
                errors=[error_msg],
                warnings=[],
                metadata={'company': company_folder}
            )
    
    def _extract_all_metrics(self, financial_data: Dict[str, pd.DataFrame], 
                           errors: List[str], warnings: List[str]) -> Dict[str, List[float]]:
        """Extract all financial metrics from loaded data"""
        
        # Get data by type
        income_fy = financial_data.get('income_fy', pd.DataFrame())
        balance_fy = financial_data.get('balance_fy', pd.DataFrame())
        cashflow_fy = financial_data.get('cashflow_fy', pd.DataFrame())
        
        # Get LTM data if available
        income_ltm = financial_data.get('income_ltm', pd.DataFrame())
        balance_ltm = financial_data.get('balance_ltm', pd.DataFrame())
        cashflow_ltm = financial_data.get('cashflow_ltm', pd.DataFrame())
        
        # Extract metrics with LTM integration
        metrics = {}
        
        # Income statement metrics
        metrics['ebit'] = self._extract_metric_with_ltm(income_fy, income_ltm, "EBIT", errors, warnings)
        metrics['net_income'] = self._extract_metric_with_ltm(income_fy, income_ltm, "Net Income", errors, warnings)
        metrics['tax_expense'] = self._extract_metric_with_ltm(income_fy, income_ltm, "Income Tax Expense", errors, warnings)
        metrics['ebt'] = self._extract_metric_with_ltm(income_fy, income_ltm, "EBT", errors, warnings)
        
        # Balance sheet metrics
        metrics['current_assets'] = self._extract_metric_with_ltm(balance_fy, balance_ltm, "Total Current Assets", errors, warnings)
        metrics['current_liabilities'] = self._extract_metric_with_ltm(balance_fy, balance_ltm, "Total Current Liabilities", errors, warnings)
        
        # Cash flow metrics
        metrics['depreciation_amortization'] = self._extract_metric_with_ltm(cashflow_fy, cashflow_ltm, "Depreciation & Amortization", errors, warnings)
        metrics['operating_cash_flow'] = self._extract_metric_with_ltm(cashflow_fy, cashflow_ltm, "Cash from Operations", errors, warnings)
        metrics['capex'] = self._extract_metric_with_ltm(cashflow_fy, cashflow_ltm, "Capital Expenditure", errors, warnings)
        metrics['debt_issued'] = self._extract_metric_with_ltm(cashflow_fy, cashflow_ltm, "Long-Term Debt Issued", errors, warnings)
        metrics['debt_repaid'] = self._extract_metric_with_ltm(cashflow_fy, cashflow_ltm, "Long-Term Debt Repaid", errors, warnings)
        
        # Calculate derived metrics
        metrics['net_borrowing'] = self._calculate_net_borrowing(metrics['debt_issued'], metrics['debt_repaid'])
        metrics['tax_rates'] = self._calculate_tax_rates(metrics['ebt'], metrics['tax_expense'])
        metrics['working_capital_changes'] = self._calculate_working_capital_changes(
            metrics['current_assets'], metrics['current_liabilities']
        )
        
        # Generate years array
        reference_length = len(metrics.get('net_income', []))
        current_year = datetime.now().year
        metrics['years'] = [str(current_year - i) for i in range(reference_length - 1, -1, -1)]
        
        return metrics
    
    def _extract_metric_with_ltm(self, fy_data: pd.DataFrame, ltm_data: pd.DataFrame, 
                                metric_name: str, errors: List[str], warnings: List[str]) -> List[float]:
        """Extract metric values combining FY and LTM data"""
        try:
            # Extract FY data
            fy_values = self._extract_metric_values(fy_data, metric_name)
            
            # Extract LTM data if available
            ltm_values = []
            if not ltm_data.empty:
                ltm_values = self._extract_metric_values(ltm_data, metric_name)
            
            # Combine data
            if fy_values and ltm_values:
                # Use FY historical + most recent LTM
                combined_values = fy_values[:-1] + [ltm_values[-1]]
                return combined_values
            elif fy_values:
                return fy_values
            else:
                warnings.append(f"No data available for {metric_name}")
                return []
                
        except Exception as e:
            errors.append(f"Error extracting {metric_name}: {str(e)}")
            return []
    
    def _extract_metric_values(self, df: pd.DataFrame, metric_name: str) -> List[float]:
        """Extract metric values from DataFrame using existing format expectations"""
        if df.empty:
            return []
        
        # Find the metric row using enhanced search (matching existing logic)
        metric_row = None
        best_match_score = 0
        best_match_row = None
        
        for idx, row in df.iterrows():
            # Check first 3 columns for metric names (matching existing logic)
            metric_text = None
            for col_idx in [0, 1, 2]:
                if len(row) > col_idx and pd.notna(row.iloc[col_idx]):
                    metric_text = str(row.iloc[col_idx]).strip()
                    break
            
            if metric_text:
                # Exact match (best case)
                if metric_name.lower() == metric_text.lower():
                    metric_row = idx
                    break
                
                # Partial match with scoring
                if metric_name.lower() in metric_text.lower():
                    match_score = len(metric_name) / len(metric_text)
                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match_row = idx
        
        # Use best match if no exact match found
        if metric_row is None and best_match_row is not None and best_match_score > 0.3:
            metric_row = best_match_row
        
        if metric_row is None:
            return []
        
        # Extract numeric values from columns 3 onwards (matching existing logic)
        values = []
        row_data = df.iloc[metric_row]
        
        # Skip the first 3 columns which contain metadata
        for col_idx in range(3, len(df.columns)):
            try:
                val = row_data.iloc[col_idx]
                if pd.isna(val) or val == '' or val == '-':
                    values.append(0.0)
                else:
                    # Enhanced numeric conversion
                    if isinstance(val, str):
                        val = val.replace(',', '').replace('$', '').replace('%', '').replace('(', '-').replace(')', '')
                    values.append(float(val))
            except (ValueError, TypeError, IndexError):
                values.append(0.0)
        
        # Reverse the order to get chronological order (oldest to newest)
        return list(reversed(values))
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity score"""
        # Simple Jaccard similarity
        set1 = set(str1.split())
        set2 = set(str2.split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0
    
    def _calculate_net_borrowing(self, debt_issued: List[float], debt_repaid: List[float]) -> List[float]:
        """Calculate net borrowing from debt issued and repaid"""
        max_length = max(len(debt_issued), len(debt_repaid))
        
        # Pad shorter lists with zeros
        debt_issued_padded = debt_issued + [0.0] * (max_length - len(debt_issued))
        debt_repaid_padded = debt_repaid + [0.0] * (max_length - len(debt_repaid))
        
        # Calculate net borrowing
        net_borrowing = []
        for i in range(max_length):
            issued = debt_issued_padded[i] if i < len(debt_issued_padded) else 0.0
            repaid = debt_repaid_padded[i] if i < len(debt_repaid_padded) else 0.0
            net_borrowing.append(issued + repaid)  # repaid is already negative
        
        return net_borrowing
    
    def _calculate_tax_rates(self, ebt: List[float], tax_expense: List[float]) -> List[float]:
        """Calculate effective tax rates"""
        tax_rates = []
        for i in range(len(ebt)):
            if ebt[i] != 0:
                tax_rate = abs(tax_expense[i]) / abs(ebt[i])
                tax_rates.append(min(tax_rate, self.processing_config['max_tax_rate']))
            else:
                tax_rates.append(self.processing_config['default_tax_rate'])
        return tax_rates
    
    def _calculate_working_capital_changes(self, current_assets: List[float], 
                                         current_liabilities: List[float]) -> List[float]:
        """Calculate working capital changes"""
        changes = [0.0]  # First year has no change
        
        for i in range(1, len(current_assets)):
            wc_change = ((current_assets[i] - current_liabilities[i]) - 
                        (current_assets[i-1] - current_liabilities[i-1]))
            changes.append(wc_change)
        
        return changes
    
    def calculate_fcf(self, company_folder: str, force_reload: bool = False) -> ProcessingResult:
        """
        Calculate all Free Cash Flow types with caching.
        
        Args:
            company_folder (str): Company folder name
            force_reload (bool): Force reload even if cached
            
        Returns:
            ProcessingResult: FCF calculation results
        """
        # Generate cache key
        cache_key = self.data_manager._generate_cache_key('fcf_results', {'company': company_folder})
        
        # Check cache first
        if not force_reload:
            cached_result = self.data_manager.get_cached_data(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached FCF results for {company_folder}")
                return cached_result
        
        logger.info(f"Calculating FCF for {company_folder}")
        
        try:
            # Get financial metrics
            metrics_result = self.extract_financial_metrics(company_folder, force_reload)
            
            if not metrics_result.success:
                return ProcessingResult(
                    data=None,
                    success=False,
                    errors=metrics_result.errors,
                    warnings=metrics_result.warnings,
                    metadata={'company': company_folder}
                )
            
            metrics = metrics_result.data
            
            # Calculate FCF types
            fcff = self._calculate_fcff(metrics)
            fcfe = self._calculate_fcfe(metrics)
            lfcf = self._calculate_lfcf(metrics)
            
            # Calculate growth rates
            growth_rates = {
                'FCFF': self._calculate_growth_rates(fcff),
                'FCFE': self._calculate_growth_rates(fcfe),
                'LFCF': self._calculate_growth_rates(lfcf)
            }
            
            # Calculate averages
            averages = {
                'FCFF': np.mean(fcff) if fcff else 0,
                'FCFE': np.mean(fcfe) if fcfe else 0,
                'LFCF': np.mean(lfcf) if lfcf else 0
            }
            
            # Create FCF results
            fcf_results = FCFResults(
                fcff=fcff,
                fcfe=fcfe,
                lfcf=lfcf,
                years=metrics.years,
                growth_rates=growth_rates,
                averages=averages
            )
            
            # Create result
            result = ProcessingResult(
                data=fcf_results,
                success=True,
                errors=metrics_result.errors,
                warnings=metrics_result.warnings,
                metadata={
                    'company': company_folder,
                    'calculation_time': datetime.now().isoformat(),
                    'years_calculated': len(fcff),
                    'fcf_types': 3
                }
            )
            
            # Cache the result
            self.data_manager.cache_data(cache_key, result, 'fcf_results', expiry_hours=24)
            
            logger.info(f"Successfully calculated FCF for {company_folder}")
            return result
            
        except Exception as e:
            error_msg = f"Error calculating FCF: {str(e)}"
            logger.error(error_msg)
            return ProcessingResult(
                data=None,
                success=False,
                errors=[error_msg],
                warnings=[],
                metadata={'company': company_folder}
            )
    
    def _calculate_fcff(self, metrics: FinancialMetrics) -> List[float]:
        """Calculate Free Cash Flow to Firm"""
        if not metrics.ebit:
            return []
        
        fcff = []
        for i in range(len(metrics.ebit)):
            fcff_value = (metrics.ebit[i] * (1 - metrics.tax_rates[i]) + 
                         metrics.depreciation_amortization[i] - 
                         metrics.working_capital_changes[i] - 
                         abs(metrics.capex[i]))
            fcff.append(fcff_value)
        return fcff
    
    def _calculate_fcfe(self, metrics: FinancialMetrics) -> List[float]:
        """Calculate Free Cash Flow to Equity"""
        if not metrics.net_income:
            return []
        
        fcfe = []
        for i in range(len(metrics.net_income)):
            fcfe_value = (metrics.net_income[i] + 
                         metrics.depreciation_amortization[i] - 
                         metrics.working_capital_changes[i] - 
                         abs(metrics.capex[i]) + 
                         metrics.net_borrowing[i])
            fcfe.append(fcfe_value)
        return fcfe
    
    def _calculate_lfcf(self, metrics: FinancialMetrics) -> List[float]:
        """Calculate Levered Free Cash Flow"""
        if not metrics.operating_cash_flow:
            return []
        
        lfcf = []
        for i in range(len(metrics.operating_cash_flow)):
            lfcf_value = metrics.operating_cash_flow[i] - abs(metrics.capex[i])
            lfcf.append(lfcf_value)
        return lfcf
    
    def _calculate_growth_rates(self, values: List[float]) -> List[float]:
        """Calculate year-over-year growth rates"""
        if len(values) < 2:
            return []
        
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                growth_rate = (values[i] - values[i-1]) / abs(values[i-1])
                growth_rates.append(growth_rate)
            else:
                growth_rates.append(0.0)
        
        return growth_rates
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from data manager"""
        cache_stats = self.data_manager.get_cache_stats()
        
        # Add processing-specific stats
        processing_stats = {
            'config': self.processing_config,
            'supported_metrics': [
                'ebit', 'net_income', 'tax_expense', 'ebt',
                'current_assets', 'current_liabilities',
                'depreciation_amortization', 'operating_cash_flow',
                'capex', 'debt_issued', 'debt_repaid'
            ],
            'fcf_types': ['FCFF', 'FCFE', 'LFCF'],
            'growth_rate_periods': self.processing_config['growth_rate_periods']
        }
        
        return {
            'cache_stats': cache_stats,
            'processing_stats': processing_stats
        }