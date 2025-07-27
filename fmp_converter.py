"""
Financial Modeling Prep (FMP) Data Converter

Converts FMP API response data to standardized format for unified processing.
Maps FMP field names to standard field names used across all APIs.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FMPConverter:
    """Converts Financial Modeling Prep data to standardized format"""

    # Field mappings from FMP names to standard names
    FIELD_MAPPINGS = {
        # Cash Flow Statement
        "operatingCashFlow": "operating_cash_flow",
        "netCashProvidedByOperatingActivities": "operating_cash_flow",
        "capitalExpenditure": "capital_expenditures",
        "capitalExpenditures": "capital_expenditures",
        "purchasesOfPropertyPlantAndEquipment": "capital_expenditures",
        "freeCashFlow": "free_cash_flow",
        # Income Statement
        "netIncome": "net_income",
        "revenue": "total_revenue",
        "totalRevenue": "total_revenue",
        "operatingIncome": "operating_income",
        "ebitda": "ebitda",
        "ebit": "ebit",
        "grossProfit": "gross_profit",
        "incomeBeforeIncomeTaxes": "income_before_tax",
        "incomeTaxExpense": "income_tax_expense",
        "eps": "earnings_per_share",
        "epsdiluted": "earnings_per_share_diluted",
        # Balance Sheet
        "totalAssets": "total_assets",
        "totalCurrentAssets": "total_current_assets",
        "totalLiabilities": "total_liabilities",
        "totalCurrentLiabilities": "total_current_liabilities",
        "totalStockholdersEquity": "total_stockholder_equity",
        "totalEquity": "total_stockholder_equity",
        "cashAndCashEquivalents": "cash_and_equivalents",
        "cashAndShortTermInvestments": "cash_and_equivalents",
        "inventory": "inventory",
        "totalDebt": "total_debt",
        "longTermDebt": "long_term_debt",
        "shortTermDebt": "short_term_debt",
        # Ratios and Metrics
        "peRatio": "pe_ratio",
        "priceToBookRatio": "pb_ratio",
        "dividendYield": "dividend_yield",
        "bookValuePerShare": "book_value_per_share",
        "marketCap": "market_cap",
    }

    @classmethod
    def convert_financial_data(cls, fmp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert FMP financial data to standardized format.

        Args:
            fmp_data: Raw data from FMP API (can be single object or array)

        Returns:
            Dict with standardized field names and values
        """
        if not fmp_data:
            logger.warning("No FMP data provided for conversion")
            return {}

        try:
            # FMP often returns arrays - take the most recent (first item)
            if isinstance(fmp_data, list) and len(fmp_data) > 0:
                data_to_convert = fmp_data[0]
            elif isinstance(fmp_data, dict):
                data_to_convert = fmp_data
            else:
                logger.error(f"Unexpected FMP data format: {type(fmp_data)}")
                return {}

            standardized_data = {}

            # Convert all mapped fields
            for fmp_field, standard_field in cls.FIELD_MAPPINGS.items():
                if fmp_field in data_to_convert:
                    value = cls._normalize_value(data_to_convert[fmp_field])
                    if value is not None:
                        standardized_data[standard_field] = value
                        logger.debug(f"FMP: Mapped {fmp_field} -> {standard_field}: {value}")

            # Add metadata
            standardized_data["source"] = "fmp"
            standardized_data["converted_at"] = datetime.now().isoformat()

            # Add original date info if available
            if "date" in data_to_convert:
                standardized_data["report_date"] = data_to_convert["date"]
            elif "calendarYear" in data_to_convert:
                standardized_data["report_year"] = data_to_convert["calendarYear"]

            logger.debug(f"FMP conversion completed. Fields: {list(standardized_data.keys())}")
            return standardized_data

        except Exception as e:
            logger.error(f"FMP conversion failed: {e}")
            return {}

    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """Normalize financial values to consistent numeric format"""
        if value is None or value == "":
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
                logger.debug(f"Could not convert FMP string value to float: '{value}'")
                return None

        try:
            numeric_value = float(value)
            # Sanity check for reasonable values
            if abs(numeric_value) > 1e15:
                logger.warning(f"FMP: Suspicious large value: {numeric_value}")
                return None
            return numeric_value
        except (ValueError, TypeError):
            logger.debug(f"Could not convert FMP value to float: {value}")
            return None

    @classmethod
    def extract_cash_flow_data(
        cls, fmp_cashflow_response: Dict[str, Any]
    ) -> Dict[str, Optional[float]]:
        """
        Extract and convert specifically cash flow data needed for FCF calculation.

        Args:
            fmp_cashflow_response: Raw FMP cash flow response

        Returns:
            Dict with operating_cash_flow and capital_expenditures
        """
        converted_data = cls.convert_financial_data(fmp_cashflow_response)

        return {
            "operating_cash_flow": converted_data.get("operating_cash_flow"),
            "capital_expenditures": converted_data.get("capital_expenditures"),
            "free_cash_flow": converted_data.get(
                "free_cash_flow"
            ),  # FMP sometimes provides this directly
            "source": "fmp",
        }

    @classmethod
    def convert_income_statement(cls, fmp_income_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FMP income statement data specifically"""
        return cls.convert_financial_data(fmp_income_data)

    @classmethod
    def convert_balance_sheet(cls, fmp_balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FMP balance sheet data specifically"""
        return cls.convert_financial_data(fmp_balance_data)

    @classmethod
    def convert_profile_data(cls, fmp_profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FMP company profile data"""
        if not fmp_profile_data:
            return {}

        # FMP profile is usually an array
        if isinstance(fmp_profile_data, list) and len(fmp_profile_data) > 0:
            profile = fmp_profile_data[0]
        else:
            profile = fmp_profile_data

        standardized = {}

        # Map profile-specific fields
        profile_mappings = {
            "mktCap": "market_cap",
            "pe": "pe_ratio",
            "beta": "beta",
            "lastDiv": "dividend_yield",
            "sector": "sector",
            "industry": "industry",
            "country": "country",
            "companyName": "company_name",
            "description": "description",
        }

        for fmp_field, standard_field in profile_mappings.items():
            if fmp_field in profile:
                value = profile[fmp_field]
                if fmp_field in ["mktCap", "pe", "beta", "lastDiv"]:
                    value = cls._normalize_value(value)
                standardized[standard_field] = value

        standardized["source"] = "fmp_profile"
        return standardized

    @classmethod
    def get_supported_fields(cls) -> List[str]:
        """Get list of all supported standard field names"""
        return list(set(cls.FIELD_MAPPINGS.values()))

    @classmethod
    def get_fmp_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """Get FMP field name for a given standard field name"""
        for fmp_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return fmp_field
        return None
