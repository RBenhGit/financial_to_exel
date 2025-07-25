"""
Polygon.io Data Converter

Converts Polygon.io API response data to standardized format for unified processing.
Maps Polygon field names to standard field names used across all APIs.
Handles Polygon's nested financial data structure.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class PolygonConverter:
    """Converts Polygon.io data to standardized format"""
    
    # Field mappings from Polygon names to standard names
    FIELD_MAPPINGS = {
        # Cash Flow Statement
        "net_cash_flow_from_operating_activities": "operating_cash_flow",
        "operating_cash_flow": "operating_cash_flow",
        "cash_flow_from_operating_activities": "operating_cash_flow",
        "capital_expenditure": "capital_expenditures",
        "capital_expenditures": "capital_expenditures",
        "capex": "capital_expenditures",
        
        # Income Statement
        "net_income_loss": "net_income",
        "net_income": "net_income",
        "income_loss_from_continuing_operations_after_tax": "net_income",
        "revenues": "total_revenue",
        "total_revenue": "total_revenue",
        "operating_income_loss": "operating_income",
        "income_loss_from_continuing_operations_before_tax": "income_before_tax",
        "income_tax_expense_benefit": "income_tax_expense",
        "basic_earnings_per_share": "earnings_per_share",
        "diluted_earnings_per_share": "earnings_per_share_diluted",
        
        # Balance Sheet
        "assets": "total_assets",
        "total_assets": "total_assets",
        "current_assets": "total_current_assets",
        "liabilities": "total_liabilities", 
        "total_liabilities": "total_liabilities",
        "current_liabilities": "total_current_liabilities",
        "equity": "total_stockholder_equity",
        "stockholders_equity": "total_stockholder_equity",
        "cash_and_cash_equivalents": "cash_and_equivalents",
        "inventories": "inventory",
        "inventory": "inventory",
        
        # Market data fields
        "market_cap": "market_cap",
        "share_class_shares_outstanding": "shares_outstanding"
    }
    
    @classmethod
    def convert_financial_data(cls, polygon_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Polygon.io financial data to standardized format.
        
        Args:
            polygon_data: Raw data from Polygon.io API
            
        Returns:
            Dict with standardized field names and values
        """
        if not polygon_data:
            logger.warning("No Polygon data provided for conversion")
            return {}
        
        try:
            standardized_data = {}
            
            # Handle different Polygon response structures
            if "results" in polygon_data:
                # Handle financials API response
                results = polygon_data["results"]
                if isinstance(results, list) and len(results) > 0:
                    # Take the most recent financial data
                    financial_data = results[0]
                    standardized_data = cls._convert_financials_result(financial_data)
                elif isinstance(results, dict):
                    standardized_data = cls._convert_ticker_details(results)
            else:
                # Direct data structure
                standardized_data = cls._convert_direct_data(polygon_data)
            
            # Add metadata
            standardized_data["source"] = "polygon"
            standardized_data["converted_at"] = datetime.now().isoformat()
            
            logger.debug(f"Polygon conversion completed. Fields: {list(standardized_data.keys())}")
            return standardized_data
            
        except Exception as e:
            logger.error(f"Polygon conversion failed: {e}")
            return {}
    
    @classmethod
    def _convert_financials_result(cls, financial_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Polygon financials API result"""
        standardized = {}
        
        # Extract from financials nested structure
        if "financials" in financial_result:
            financials = financial_result["financials"]
            
            # Process different statement types
            for statement_type in ["cash_flow_statement", "income_statement", "balance_sheet"]:
                if statement_type in financials:
                    statement_data = financials[statement_type]
                    converted = cls._convert_statement_data(statement_data)
                    standardized.update(converted)
        
        # Add period information
        if "fiscal_year" in financial_result:
            standardized["report_year"] = financial_result["fiscal_year"]
        if "fiscal_period" in financial_result:
            standardized["report_period"] = financial_result["fiscal_period"]
        
        return standardized
    
    @classmethod
    def _convert_ticker_details(cls, ticker_details: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Polygon ticker details response"""
        standardized = {}
        
        # Map ticker details fields
        for polygon_field, standard_field in cls.FIELD_MAPPINGS.items():
            if polygon_field in ticker_details:
                value = cls._normalize_value(ticker_details[polygon_field])
                if value is not None:
                    standardized[standard_field] = value
        
        # Copy text fields
        text_fields = {
            "description": "description",
            "name": "company_name",
            "market": "market",
            "locale": "locale",
            "currency_name": "currency"
        }
        
        for polygon_field, standard_field in text_fields.items():
            if polygon_field in ticker_details:
                standardized[standard_field] = ticker_details[polygon_field]
        
        return standardized
    
    @classmethod
    def _convert_direct_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert direct Polygon data structure"""
        standardized = {}
        
        for polygon_field, standard_field in cls.FIELD_MAPPINGS.items():
            if polygon_field in data:
                value = cls._normalize_value(data[polygon_field])
                if value is not None:
                    standardized[standard_field] = value
                    logger.debug(f"Polygon: Mapped {polygon_field} -> {standard_field}: {value}")
        
        return standardized
    
    @classmethod
    def _convert_statement_data(cls, statement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert individual financial statement data from Polygon"""
        standardized = {}
        
        # Polygon uses nested structure with "value" keys
        for polygon_field, standard_field in cls.FIELD_MAPPINGS.items():
            if polygon_field in statement_data:
                field_data = statement_data[polygon_field]
                
                # Handle nested value structure
                if isinstance(field_data, dict) and "value" in field_data:
                    value = cls._normalize_value(field_data["value"])
                else:
                    value = cls._normalize_value(field_data)
                
                if value is not None:
                    standardized[standard_field] = value
                    logger.debug(f"Polygon statement: Mapped {polygon_field} -> {standard_field}: {value}")
        
        return standardized
    
    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """Normalize financial values to consistent numeric format"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Handle special cases
            if value.upper() in ["NONE", "N/A", "-", "", "NULL"]:
                return None
            
            # Remove formatting
            value = value.replace(",", "").replace("$", "").strip()
            
            try:
                return float(value)
            except ValueError:
                logger.debug(f"Could not convert Polygon string value to float: '{value}'")
                return None
        
        try:
            numeric_value = float(value)
            # Sanity check for reasonable values
            if abs(numeric_value) > 1e15:
                logger.warning(f"Polygon: Suspicious large value: {numeric_value}")
                return None
            return numeric_value
        except (ValueError, TypeError):
            logger.debug(f"Could not convert Polygon value to float: {value}")
            return None
    
    @classmethod
    def extract_cash_flow_data(cls, polygon_financials_response: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract and convert specifically cash flow data needed for FCF calculation.
        
        Args:
            polygon_financials_response: Raw Polygon financials response
            
        Returns:
            Dict with operating_cash_flow and capital_expenditures
        """
        converted_data = cls.convert_financial_data(polygon_financials_response)
        
        return {
            "operating_cash_flow": converted_data.get("operating_cash_flow"),
            "capital_expenditures": converted_data.get("capital_expenditures"),
            "source": "polygon"
        }
    
    @classmethod
    def convert_last_trade_data(cls, polygon_trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Polygon last trade data"""
        if not polygon_trade_data or "results" not in polygon_trade_data:
            return {}
        
        results = polygon_trade_data["results"]
        
        standardized = {
            "current_price": cls._normalize_value(results.get("p")),  # price
            "volume": cls._normalize_value(results.get("s")),  # size
            "timestamp": results.get("t"),  # timestamp
            "source": "polygon_trade"
        }
        
        return {k: v for k, v in standardized.items() if v is not None}
    
    @classmethod
    def get_supported_fields(cls) -> List[str]:
        """Get list of all supported standard field names"""
        return list(set(cls.FIELD_MAPPINGS.values()))
    
    @classmethod
    def get_polygon_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """Get Polygon field name for a given standard field name"""
        for polygon_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return polygon_field
        return None
    
    @classmethod
    def is_premium_data_available(cls, polygon_response: Dict[str, Any]) -> bool:
        """
        Check if Polygon response contains premium financial data.
        
        Polygon's basic tier has limited financial data access.
        """
        if not polygon_response:
            return False
        
        # Check for financial statement data
        if "results" in polygon_response:
            results = polygon_response["results"]
            if isinstance(results, list) and len(results) > 0:
                return "financials" in results[0]
            elif isinstance(results, dict):
                return "financials" in results
        
        return False