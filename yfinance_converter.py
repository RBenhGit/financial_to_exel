"""
yfinance Data Converter

Converts yfinance (Yahoo Finance) data to standardized format for unified processing.
Maps yfinance field names to standard field names used across all APIs.
Handles both DataFrame and dictionary formats from yfinance.
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class YfinanceConverter:
    """Converts yfinance data to standardized format"""
    
    # Field mappings from yfinance names to standard names
    FIELD_MAPPINGS = {
        # Cash Flow Statement
        "Total Cash From Operating Activities": "operating_cash_flow",
        "Cash Flow From Continuing Operating Activities": "operating_cash_flow",
        "Operating Cash Flow": "operating_cash_flow",
        "Capital Expenditures": "capital_expenditures",
        "Capital Expenditure": "capital_expenditures",
        "Free Cash Flow": "free_cash_flow",
        
        # Income Statement
        "Net Income": "net_income",
        "Net Income Common Stockholders": "net_income",
        "Net Income Applicable To Common Shares": "net_income",
        "Total Revenue": "total_revenue",
        "Revenue": "total_revenue",
        "Operating Income": "operating_income",
        "EBIT": "ebit",
        "EBITDA": "ebitda",
        "Gross Profit": "gross_profit",
        "Pretax Income": "income_before_tax",
        "Income Before Tax": "income_before_tax",
        "Tax Provision": "income_tax_expense",
        "Income Tax Expense": "income_tax_expense",
        "Basic EPS": "earnings_per_share",
        "Diluted EPS": "earnings_per_share_diluted",
        
        # Balance Sheet
        "Total Assets": "total_assets",
        "Current Assets": "total_current_assets",
        "Total Current Assets": "total_current_assets",
        "Total Liabilities Net Minority Interest": "total_liabilities",
        "Total Liab": "total_liabilities",
        "Current Liabilities": "total_current_liabilities",
        "Total Current Liabilities": "total_current_liabilities",
        "Stockholders Equity": "total_stockholder_equity",
        "Total Stockholder Equity": "total_stockholder_equity",
        "Cash And Cash Equivalents": "cash_and_equivalents",
        "Cash": "cash_and_equivalents",
        "Inventory": "inventory",
        "Total Debt": "total_debt",
        "Long Term Debt": "long_term_debt",
        "Short Term Debt": "short_term_debt",
        
        # From info dict
        "marketCap": "market_cap",
        "trailingPE": "pe_ratio",
        "priceToBook": "pb_ratio",
        "dividendYield": "dividend_yield",
        "beta": "beta",
        "bookValue": "book_value_per_share",
        "trailingEps": "earnings_per_share",
        "forwardEps": "forward_eps",
        "totalRevenue": "total_revenue",
        "profitMargins": "profit_margin"
    }
    
    @classmethod
    def convert_financial_data(cls, yfinance_data: Any) -> Dict[str, Any]:
        """
        Convert yfinance financial data to standardized format.
        
        Args:
            yfinance_data: Raw data from yfinance (DataFrame, dict, or other)
            
        Returns:
            Dict with standardized field names and values
        """
        if yfinance_data is None:
            logger.warning("No yfinance data provided for conversion")
            return {}
        
        try:
            standardized_data = {}
            
            if isinstance(yfinance_data, pd.DataFrame):
                standardized_data = cls._convert_dataframe(yfinance_data)
            elif isinstance(yfinance_data, dict):
                standardized_data = cls._convert_dict(yfinance_data)
            else:
                logger.warning(f"Unsupported yfinance data type: {type(yfinance_data)}")
                return {}
            
            # Add metadata
            standardized_data["source"] = "yfinance"
            standardized_data["converted_at"] = datetime.now().isoformat()
            
            logger.debug(f"yfinance conversion completed. Fields: {list(standardized_data.keys())}")
            return standardized_data
            
        except Exception as e:
            logger.error(f"yfinance conversion failed: {e}")
            return {}
    
    @classmethod
    def _convert_dataframe(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert pandas DataFrame from yfinance to standardized format"""
        if df.empty:
            return {}
        
        standardized = {}
        
        # Get the most recent data (first column)
        latest_column = df.columns[0] if len(df.columns) > 0 else None
        if latest_column is None:
            return {}
        
        # Map each field
        for yf_field, standard_field in cls.FIELD_MAPPINGS.items():
            if yf_field in df.index:
                value = df.loc[yf_field, latest_column]
                normalized_value = cls._normalize_value(value)
                if normalized_value is not None:
                    standardized[standard_field] = normalized_value
                    logger.debug(f"yfinance DataFrame: Mapped {yf_field} -> {standard_field}: {normalized_value}")
        
        # Add period information
        standardized["report_period"] = str(latest_column)
        
        return standardized
    
    @classmethod
    def _convert_dict(cls, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dictionary from yfinance (like .info) to standardized format"""
        standardized = {}
        
        for yf_field, standard_field in cls.FIELD_MAPPINGS.items():
            if yf_field in data_dict:
                value = data_dict[yf_field]
                normalized_value = cls._normalize_value(value)
                if normalized_value is not None:
                    standardized[standard_field] = normalized_value
                    logger.debug(f"yfinance dict: Mapped {yf_field} -> {standard_field}: {normalized_value}")
        
        # Copy some non-numeric fields as-is
        text_fields = {
            "sector": "sector",
            "industry": "industry", 
            "country": "country",
            "longName": "company_name",
            "longBusinessSummary": "description",
            "currency": "currency"
        }
        
        for yf_field, standard_field in text_fields.items():
            if yf_field in data_dict and data_dict[yf_field]:
                standardized[standard_field] = data_dict[yf_field]
        
        return standardized
    
    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """Normalize financial values to consistent numeric format"""
        if value is None:
            return None
        
        # Handle pandas NaN
        if pd.isna(value):
            return None
        
        if isinstance(value, str):
            # Handle special cases
            if value.upper() in ["NONE", "N/A", "-", "", "NULL"]:
                return None
            
            # Remove formatting
            value = value.replace(",", "").replace("$", "").replace("%", "").strip()
            
            try:
                return float(value)
            except ValueError:
                logger.debug(f"Could not convert yfinance string value to float: '{value}'")
                return None
        
        try:
            numeric_value = float(value)
            # Sanity check for reasonable values
            if abs(numeric_value) > 1e15:
                logger.warning(f"yfinance: Suspicious large value: {numeric_value}")
                return None
            return numeric_value
        except (ValueError, TypeError):
            logger.debug(f"Could not convert yfinance value to float: {value}")
            return None
    
    @classmethod
    def extract_cash_flow_data(cls, yfinance_cashflow: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Extract and convert specifically cash flow data needed for FCF calculation.
        
        Args:
            yfinance_cashflow: yfinance cashflow DataFrame
            
        Returns:
            Dict with operating_cash_flow and capital_expenditures
        """
        converted_data = cls.convert_financial_data(yfinance_cashflow)
        
        return {
            "operating_cash_flow": converted_data.get("operating_cash_flow"),
            "capital_expenditures": converted_data.get("capital_expenditures"),
            "free_cash_flow": converted_data.get("free_cash_flow"),
            "source": "yfinance"
        }
    
    @classmethod
    def convert_info_data(cls, yfinance_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert yfinance .info dictionary specifically"""
        return cls.convert_financial_data(yfinance_info)
    
    @classmethod
    def convert_financials(cls, yfinance_financials: pd.DataFrame) -> Dict[str, Any]:
        """Convert yfinance financials (income statement) DataFrame"""
        return cls.convert_financial_data(yfinance_financials)
    
    @classmethod
    def convert_balance_sheet(cls, yfinance_balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Convert yfinance balance sheet DataFrame"""
        return cls.convert_financial_data(yfinance_balance_sheet)
    
    @classmethod
    def handle_quarterly_vs_annual(cls, annual_data: pd.DataFrame, 
                                 quarterly_data: pd.DataFrame, 
                                 prefer_quarterly: bool = False) -> Dict[str, Any]:
        """
        Handle both quarterly and annual data from yfinance.
        
        Args:
            annual_data: Annual financial data DataFrame
            quarterly_data: Quarterly financial data DataFrame
            prefer_quarterly: Whether to prefer quarterly over annual data
            
        Returns:
            Dict with standardized field names and values
        """
        if prefer_quarterly and not quarterly_data.empty:
            result = cls.convert_financial_data(quarterly_data)
            result["data_period"] = "quarterly"
        elif not annual_data.empty:
            result = cls.convert_financial_data(annual_data)
            result["data_period"] = "annual"
        elif not quarterly_data.empty:
            result = cls.convert_financial_data(quarterly_data)
            result["data_period"] = "quarterly"
        else:
            logger.warning("Both annual and quarterly yfinance data are empty")
            return {}
        
        return result
    
    @classmethod
    def get_supported_fields(cls) -> List[str]:
        """Get list of all supported standard field names"""
        return list(set(cls.FIELD_MAPPINGS.values()))
    
    @classmethod
    def get_yfinance_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """Get yfinance field name for a given standard field name"""
        for yf_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return yf_field
        return None