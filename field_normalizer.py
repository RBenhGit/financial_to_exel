"""
Field Normalizer Module

This module provides field normalization functionality to handle different naming conventions
across various financial data APIs. It maps standard field names to API-specific variants
and provides robust data extraction with fallback mechanisms.

Features:
- Centralized field mapping configuration
- Robust data extraction with multiple fallback options
- Support for nested data structures
- Comprehensive logging for debugging
- Data type validation and conversion
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class FieldNormalizer:
    """
    Normalizes field access across different financial data APIs.
    
    This class handles the complexity of different naming conventions and data structures
    used by various financial data providers (Alpha Vantage, FMP, yfinance, Polygon, Excel).
    """
    
    def __init__(self, mappings_file: str = "field_mappings.json"):
        """
        Initialize the field normalizer with mapping configuration.
        
        Args:
            mappings_file (str): Path to the field mappings JSON configuration file
        """
        self.mappings_file = Path(mappings_file)
        self.mappings = {}
        self.standard_fields = {}
        self.calculation_rules = {}
        self.data_structure_hints = {}
        
        self._load_mappings()
    
    def _load_mappings(self):
        """Load field mappings from configuration file"""
        try:
            if self.mappings_file.exists():
                with open(self.mappings_file, 'r') as f:
                    config = json.load(f)
                
                self.standard_fields = config.get('standard_fields', {})
                self.mappings = config.get('api_mappings', {})
                self.calculation_rules = config.get('calculation_rules', {})
                self.data_structure_hints = config.get('data_structure_hints', {})
                
                logger.info(f"Loaded field mappings from {self.mappings_file}")
            else:
                logger.error(f"Field mappings file not found: {self.mappings_file}")
                self._create_default_mappings()
                
        except Exception as e:
            logger.error(f"Failed to load field mappings: {e}")
            self._create_default_mappings()
    
    def _create_default_mappings(self):
        """Create basic default mappings if configuration file is missing"""
        self.standard_fields = {
            "operating_cash_flow": "operating_cash_flow",
            "capital_expenditures": "capital_expenditures",
            "free_cash_flow": "free_cash_flow"
        }
        
        self.mappings = {
            "alpha_vantage": {
                "operating_cash_flow": ["operatingCashflow"],
                "capital_expenditures": ["capitalExpenditures"]
            },
            "fmp": {
                "operating_cash_flow": ["operatingCashFlow"],
                "capital_expenditures": ["capitalExpenditure"]
            },
            "yfinance": {
                "operating_cash_flow": ["Total Cash From Operating Activities"],
                "capital_expenditures": ["Capital Expenditures"]
            }
        }
    
    def extract_field_value(self, data: Any, standard_field: str, api_source: str, 
                          context: str = "unknown") -> Optional[float]:
        """
        Extract a field value from data using API-specific field mappings.
        
        Args:
            data: The data structure to extract from (dict, DataFrame, etc.)
            standard_field: The standardized field name to extract
            api_source: The API source identifier (alpha_vantage, fmp, etc.)
            context: Additional context for logging (statement type, ticker, etc.)
            
        Returns:
            float: The extracted and normalized field value, or None if not found
        """
        if not data:
            logger.warning(f"No data provided for field extraction: {standard_field}")
            return None
        
        # Get field name variants for this API
        field_variants = self.mappings.get(api_source, {}).get(standard_field, [])
        
        if not field_variants:
            logger.warning(f"No field mappings found for {standard_field} in {api_source}")
            return None
        
        logger.debug(f"Attempting to extract {standard_field} from {api_source} using variants: {field_variants}")
        
        # Try each field variant
        for field_name in field_variants:
            try:
                value = self._extract_value_by_type(data, field_name, api_source)
                if value is not None:
                    # Convert and validate the value
                    normalized_value = self._normalize_numeric_value(value)
                    if normalized_value is not None:
                        logger.debug(f"Successfully extracted {standard_field}={normalized_value} using field '{field_name}' from {api_source}")
                        return normalized_value
                    else:
                        logger.debug(f"Field '{field_name}' found but value could not be normalized: {value}")
                
            except Exception as e:
                logger.debug(f"Failed to extract field '{field_name}' from {api_source}: {e}")
                continue
        
        logger.warning(f"Could not extract {standard_field} from {api_source} data (context: {context})")
        return None
    
    def _extract_value_by_type(self, data: Any, field_name: str, api_source: str) -> Any:
        """
        Extract value from data based on the data type and API source.
        
        Args:
            data: The data structure (dict, DataFrame, list, etc.)
            field_name: The field name to extract
            api_source: The API source for structure-specific handling
            
        Returns:
            The extracted value or None if not found
        """
        if isinstance(data, dict):
            return self._extract_from_dict(data, field_name, api_source)
        elif isinstance(data, pd.DataFrame):
            return self._extract_from_dataframe(data, field_name, api_source)
        elif isinstance(data, list) and len(data) > 0:
            # Try the first item in the list (most recent data)
            return self._extract_value_by_type(data[0], field_name, api_source)
        else:
            logger.debug(f"Unsupported data type for extraction: {type(data)}")
            return None
    
    def _extract_from_dict(self, data: dict, field_name: str, api_source: str) -> Any:
        """Extract value from dictionary with nested structure support"""
        # Direct key access
        if field_name in data:
            return data[field_name]
        
        # Case-insensitive search
        for key, value in data.items():
            if key.lower() == field_name.lower():
                return value
        
        # Handle nested structures based on API hints
        structure_hints = self.data_structure_hints.get(api_source, {})
        
        # For Alpha Vantage, try nested report structures
        if api_source == "alpha_vantage":
            for report_type in ["annualReports", "quarterlyReports"]:
                if report_type in data and isinstance(data[report_type], list) and len(data[report_type]) > 0:
                    nested_value = self._extract_from_dict(data[report_type][0], field_name, api_source)
                    if nested_value is not None:
                        return nested_value
        
        # Recursive search in nested dictionaries
        for key, value in data.items():
            if isinstance(value, dict):
                nested_result = self._extract_from_dict(value, field_name, api_source)
                if nested_result is not None:
                    return nested_result
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                nested_result = self._extract_from_dict(value[0], field_name, api_source)
                if nested_result is not None:
                    return nested_result
        
        return None
    
    def _extract_from_dataframe(self, data: pd.DataFrame, field_name: str, api_source: str) -> Any:
        """Extract value from pandas DataFrame (typically yfinance data)"""
        if data.empty:
            return None
        
        # Try direct index access
        if field_name in data.index:
            # Get the most recent value (first column)
            latest_col = data.columns[0] if len(data.columns) > 0 else None
            if latest_col is not None:
                value = data.loc[field_name, latest_col]
                return value if pd.notna(value) else None
        
        # Case-insensitive search
        for idx in data.index:
            if str(idx).lower() == field_name.lower():
                latest_col = data.columns[0] if len(data.columns) > 0 else None
                if latest_col is not None:
                    value = data.loc[idx, latest_col]
                    return value if pd.notna(value) else None
        
        return None
    
    def _normalize_numeric_value(self, value: Any) -> Optional[float]:
        """
        Normalize and validate numeric values.
        
        Args:
            value: The value to normalize
            
        Returns:
            float: Normalized numeric value or None if invalid
        """
        if value is None:
            return None
        
        # Handle pandas NaN
        if pd.isna(value):
            return None
        
        # Handle string representations
        if isinstance(value, str):
            # Remove common formatting
            value = value.replace(',', '').replace('$', '').replace('%', '').strip()
            
            # Handle empty strings
            if not value or value.lower() in ['n/a', 'na', 'none', '-']:
                return None
            
            try:
                value = float(value)
            except ValueError:
                logger.debug(f"Could not convert string to float: '{value}'")
                return None
        
        # Convert to float
        try:
            numeric_value = float(value)
            
            # Validate reasonable range (in millions/billions)
            if abs(numeric_value) > 1e15:  # Sanity check for extremely large values
                logger.warning(f"Suspiciously large value detected: {numeric_value}")
                return None
            
            return numeric_value
            
        except (ValueError, TypeError):
            logger.debug(f"Could not convert value to float: {value} (type: {type(value)})")
            return None
    
    def calculate_free_cash_flow(self, operating_cash_flow: Optional[float], 
                                capital_expenditures: Optional[float], 
                                api_source: str) -> Optional[float]:
        """
        Calculate Free Cash Flow using normalized values.
        
        Args:
            operating_cash_flow: Operating cash flow value
            capital_expenditures: Capital expenditures value  
            api_source: API source for handling CapEx sign conventions
            
        Returns:
            float: Calculated Free Cash Flow or None if inputs are invalid
        """
        if operating_cash_flow is None or capital_expenditures is None:
            logger.warning(f"Cannot calculate FCF: OCF={operating_cash_flow}, CapEx={capital_expenditures}")
            return None
        
        # Handle different CapEx sign conventions
        capex_sign_rules = self.calculation_rules.get('capex_sign_handling', {})
        capex_handling = capex_sign_rules.get(api_source, 'negative_reported')
        
        if capex_handling == 'negative_reported':
            # CapEx is reported as negative, so we add it (subtracting a negative)
            if capital_expenditures > 0:
                logger.debug(f"CapEx expected to be negative for {api_source}, but got positive: {capital_expenditures}")
            free_cash_flow = operating_cash_flow + capital_expenditures  # Adding negative CapEx
        else:
            # CapEx is reported as positive, so we subtract it
            free_cash_flow = operating_cash_flow - abs(capital_expenditures)
        
        logger.debug(f"FCF calculation for {api_source}: OCF({operating_cash_flow}) - CapEx({capital_expenditures}) = {free_cash_flow}")
        
        return free_cash_flow
    
    def extract_financial_metrics(self, data: Dict[str, Any], api_source: str, 
                                ticker: str = "unknown") -> Dict[str, Optional[float]]:
        """
        Extract multiple financial metrics from data.
        
        Args:
            data: Financial data from API
            api_source: API source identifier
            ticker: Ticker symbol for logging context
            
        Returns:
            dict: Dictionary of extracted financial metrics
        """
        metrics = {}
        context = f"{ticker} ({api_source})"
        
        # Extract core metrics
        for standard_field in self.standard_fields.keys():
            if standard_field != "free_cash_flow":  # FCF is calculated, not extracted
                metrics[standard_field] = self.extract_field_value(
                    data, standard_field, api_source, context
                )
        
        # Calculate Free Cash Flow if we have the required components
        if 'operating_cash_flow' in metrics and 'capital_expenditures' in metrics:
            metrics['free_cash_flow'] = self.calculate_free_cash_flow(
                metrics['operating_cash_flow'],
                metrics['capital_expenditures'], 
                api_source
            )
        
        # Log results
        extracted_count = sum(1 for v in metrics.values() if v is not None)
        logger.info(f"Extracted {extracted_count}/{len(metrics)} metrics for {context}")
        
        if extracted_count == 0:
            logger.warning(f"No metrics could be extracted for {context}")
        
        return metrics
    
    def get_available_fields(self, api_source: str) -> List[str]:
        """Get list of available standard fields for an API source"""
        return list(self.mappings.get(api_source, {}).keys())
    
    def get_field_variants(self, api_source: str, standard_field: str) -> List[str]:
        """Get field name variants for a specific API and field"""
        return self.mappings.get(api_source, {}).get(standard_field, [])