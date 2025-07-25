"""
Alpha Vantage Data Converter

Converts Alpha Vantage API response data to standardized format for unified processing.
Maps Alpha Vantage field names to standard field names used across all APIs.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AlphaVantageConverter:
    """Converts Alpha Vantage data to standardized format"""
    
    # Field mappings from Alpha Vantage names to standard names
    FIELD_MAPPINGS = {
        # Cash Flow Statement
        "operatingCashflow": "operating_cash_flow",
        "capitalExpenditures": "capital_expenditures",
        "totalCashFromOperatingActivities": "operating_cash_flow",
        "capitalExpenditure": "capital_expenditures",
        
        # Income Statement  
        "netIncome": "net_income",
        "totalRevenue": "total_revenue",
        "operatingIncome": "operating_income",
        "ebit": "ebit",
        "ebitda": "ebitda",
        "grossProfit": "gross_profit",
        "incomeBeforeTax": "income_before_tax",
        "incomeTaxExpense": "income_tax_expense",
        
        # Balance Sheet
        "totalAssets": "total_assets",
        "totalCurrentAssets": "total_current_assets",
        "totalLiab": "total_liabilities",
        "totalCurrentLiabilities": "total_current_liabilities",
        "totalStockholderEquity": "total_stockholder_equity",
        "totalShareholderEquity": "total_stockholder_equity",
        "cash": "cash_and_equivalents",
        "cashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
        "inventory": "inventory",
        "totalDebt": "total_debt",
        "longTermDebt": "long_term_debt",
        "shortTermDebt": "short_term_debt"
    }
    
    @classmethod
    def convert_financial_data(cls, alpha_vantage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Alpha Vantage financial data to standardized format.
        
        Args:
            alpha_vantage_data: Raw data from Alpha Vantage API
            
        Returns:
            Dict with standardized field names and values
        """
        if not alpha_vantage_data:
            logger.warning("No Alpha Vantage data provided for conversion")
            return {}
        
        try:
            standardized_data = {}
            
            # Process different statement types
            for statement_type in ["cash_flow", "income_statement", "balance_sheet"]:
                statement_data = cls._extract_statement_data(alpha_vantage_data, statement_type)
                if statement_data:
                    converted = cls._convert_statement(statement_data, statement_type)
                    standardized_data.update(converted)
            
            # Add metadata
            standardized_data["source"] = "alpha_vantage"
            standardized_data["converted_at"] = datetime.now().isoformat()
            
            logger.debug(f"Alpha Vantage conversion completed. Fields: {list(standardized_data.keys())}")
            return standardized_data
            
        except Exception as e:
            logger.error(f"Alpha Vantage conversion failed: {e}")
            return {}
    
    @classmethod
    def _extract_statement_data(cls, data: Dict[str, Any], statement_type: str) -> Optional[Dict[str, Any]]:
        """Extract specific financial statement data from Alpha Vantage response"""
        
        # Map statement types to Alpha Vantage response keys
        statement_keys = {
            "cash_flow": ["annualReports", "quarterlyReports"],
            "income_statement": ["annualReports", "quarterlyReports"], 
            "balance_sheet": ["annualReports", "quarterlyReports"]
        }
        
        # Look for the statement data in the response
        for key in statement_keys.get(statement_type, []):
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                # Return the most recent report (first item)
                return data[key][0]
        
        # Also check if data is directly in the root (for single statement responses)
        if isinstance(data, dict) and any(field in data for field in cls.FIELD_MAPPINGS.keys()):
            return data
        
        return None
    
    @classmethod
    def _convert_statement(cls, statement_data: Dict[str, Any], statement_type: str) -> Dict[str, Any]:
        """Convert individual financial statement using field mappings"""
        converted = {}
        
        for alpha_field, standard_field in cls.FIELD_MAPPINGS.items():
            if alpha_field in statement_data:
                value = cls._normalize_value(statement_data[alpha_field])
                if value is not None:
                    converted[standard_field] = value
                    logger.debug(f"Mapped {alpha_field} -> {standard_field}: {value}")
        
        return converted
    
    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """Normalize financial values to consistent numeric format"""
        if value is None or value == "":
            return None
        
        if isinstance(value, str):
            # Handle special cases
            if value.upper() in ["NONE", "N/A", "-", ""]:
                return None
            
            # Remove formatting
            value = value.replace(",", "").replace("$", "").strip()
            
            try:
                return float(value)
            except ValueError:
                logger.debug(f"Could not convert string value to float: '{value}'")
                return None
        
        try:
            numeric_value = float(value)
            # Sanity check for reasonable values
            if abs(numeric_value) > 1e15:
                logger.warning(f"Suspicious large value: {numeric_value}")
                return None
            return numeric_value
        except (ValueError, TypeError):
            logger.debug(f"Could not convert value to float: {value}")
            return None
    
    @classmethod
    def extract_cash_flow_data(cls, alpha_vantage_response: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract and convert specifically cash flow data needed for FCF calculation.
        
        Args:
            alpha_vantage_response: Raw Alpha Vantage cash flow response
            
        Returns:
            Dict with operating_cash_flow and capital_expenditures
        """
        converted_data = cls.convert_financial_data(alpha_vantage_response)
        
        return {
            "operating_cash_flow": converted_data.get("operating_cash_flow"),
            "capital_expenditures": converted_data.get("capital_expenditures"),
            "source": "alpha_vantage"
        }
    
    @classmethod
    def get_supported_fields(cls) -> List[str]:
        """Get list of all supported standard field names"""
        return list(set(cls.FIELD_MAPPINGS.values()))
    
    @classmethod
    def get_alpha_vantage_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """Get Alpha Vantage field name for a given standard field name"""
        for av_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return av_field
        return None