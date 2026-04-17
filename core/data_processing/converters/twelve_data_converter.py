"""
Twelve Data Converter
=====================

Converts Twelve Data API response fields to the project's standardized field names.
Follows the same pattern as FMPConverter, AlphaVantageConverter, and PolygonConverter.

Twelve Data field names (verified from official Go/PHP client struct definitions):
  https://twelvedata.com/docs

IMPORTANT — nested response structure
--------------------------------------
Twelve Data financial statements return nested objects rather than flat records:

  income_statement: most scalars at top level; operating_expense{} and
                    non_operating_interest{} are nested one level.
  balance_sheet:    current_assets{}, non_current_assets{}, current_liabilities{},
                    non_current_liabilities{}, shareholders_equity{} are all nested;
                    total_assets and total_liabilities are top-level scalars.
  cash_flow:        operating_activities{}, investing_activities{}, and
                    financing_activities{} are nested; free_cash_flow, end_cash_position,
                    income_tax_paid, interest_paid are top-level scalars.

The _flatten_record() helper promotes sub-fields one level up so FIELD_MAPPINGS can
address every value with a simple snake_case key.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_converter import BaseConverter

logger = logging.getLogger(__name__)


class TwelveDataConverter(BaseConverter):
    """Converts Twelve Data API responses to standardized format."""

    # Maps Twelve Data field names → project standard field names
    # Keys reflect ACTUAL API field names (verified from struct definitions).
    FIELD_MAPPINGS = {
        # ── Income Statement (top-level + flattened from operating_expense /
        #    non_operating_interest) ──────────────────────────────────────────
        "sales": "total_revenue",                           # primary revenue field
        "revenue": "total_revenue",
        "total_revenue": "total_revenue",
        "cost_of_goods": "cost_of_revenue",
        "gross_profit": "gross_profit",
        "operating_income": "operating_income",
        "ebitda": "ebitda",
        "pretax_income": "income_before_tax",               # actual TD field
        "income_tax": "income_tax_expense",                 # actual TD field
        "net_income": "net_income",
        "net_income_continuous_operations": "net_income_cont_ops",
        "minority_interests": "minority_interest",
        "preferred_stock_dividends": "preferred_dividends",
        # Per-share (top-level)
        "eps_basic": "earnings_per_share",                  # actual TD field
        "eps_diluted": "earnings_per_share_diluted",        # actual TD field
        "basic_shares_outstanding": "shares_outstanding_basic",
        "diluted_shares_outstanding": "shares_outstanding_diluted",
        # Flattened from operating_expense{}
        "research_and_development": "research_development",
        "selling_general_and_administrative": "selling_general_administrative",
        "other_operating_expenses": "other_operating_expenses",
        # ── Balance Sheet (mostly flattened from nested sub-objects) ─────────
        # Top-level scalars
        "total_assets": "total_assets",
        "total_liabilities": "total_liabilities",
        "total_equity_gross_minority_interest": "total_stockholder_equity",
        # Flattened from current_assets{}
        "cash_and_cash_equivalents": "cash_and_equivalents",   # actual TD field
        "cash": "cash",
        "other_short_term_investments": "short_term_investments",
        "accounts_receivable": "accounts_receivable",
        "inventory": "inventory",
        "prepaid_assets": "prepaid_assets",
        "total_current_assets": "total_current_assets",        # actual TD field
        # Flattened from non_current_assets{}
        "goodwill": "goodwill",
        "intangible_assets": "intangible_assets",
        "total_non_current_assets": "total_non_current_assets",
        # Flattened from current_liabilities{}
        "accounts_payable": "accounts_payable",
        "short_term_debt": "short_term_debt",
        "total_current_liabilities": "total_current_liabilities",  # actual TD field
        # Flattened from non_current_liabilities{}
        "long_term_debt": "long_term_debt",
        "total_non_current_liabilities": "total_non_current_liabilities",
        # Flattened from shareholders_equity{}
        "total_shareholders_equity": "total_stockholder_equity",   # actual TD field
        "retained_earnings": "retained_earnings",
        "common_stock": "common_stock",
        "additional_paid_in_capital": "additional_paid_in_capital",
        "treasury_stock": "treasury_stock",
        # ── Cash Flow (top-level scalars + flattened from activity sub-objects)
        # Top-level scalars
        "free_cash_flow": "free_cash_flow",
        "end_cash_position": "end_cash_position",
        "income_tax_paid": "income_tax_paid",
        "interest_paid": "interest_paid",
        # Flattened from operating_activities{}
        "operating_cash_flow": "operating_cash_flow",              # actual TD field
        "depreciation": "depreciation_amortization",               # actual TD field
        "stock_based_compensation": "stock_based_compensation",
        "deferred_taxes": "deferred_taxes",
        # Flattened from investing_activities{}
        "capital_expenditures": "capital_expenditures",            # actual TD field
        "net_acquisitions": "net_acquisitions",
        "purchase_of_investments": "purchase_of_investments",
        "sale_of_investments": "sale_of_investments",
        "investing_cash_flow": "investing_cash_flow",
        # Flattened from financing_activities{}
        "long_term_debt_issuance": "long_term_debt_issuance",      # actual TD field
        "long_term_debt_payments": "long_term_debt_payments",      # actual TD field
        "short_term_debt_issuance": "short_term_debt_issuance",
        "common_stock_issuance": "common_stock_issuance",
        "common_stock_repurchase": "common_stock_repurchase",
        "common_dividends": "dividends_paid",                       # actual TD field
        "financing_cash_flow": "financing_cash_flow",
        # ── Market / Quote ───────────────────────────────────────────────────
        "close": "current_price",
        "price": "current_price",
        "market_cap": "market_cap",
        "enterprise_value": "enterprise_value",
        "pe_ratio": "pe_ratio",
        "pb_ratio": "pb_ratio",
        "ps_ratio": "ps_price_to_sales",
        "ev_to_ebitda": "ev_to_ebitda",
        "dividend_yield": "dividend_yield",
        "dividend_per_share": "dividends_per_share",
        "book_value_per_share": "book_value_per_share",
        "fifty_two_week_high": "fifty_two_week_high",
        "fifty_two_week_low": "fifty_two_week_low",
        "beta": "beta",
        "volume": "volume",
        "average_volume": "average_volume",
        # ── Company Info ─────────────────────────────────────────────────────
        "name": "company_name",
        "symbol": "ticker",
        "exchange": "exchange",
        "currency": "currency",
        "country": "country",
        "sector": "sector",
        "industry": "industry",
        "employees": "full_time_employees",
        "description": "business_summary",
        "website": "website",
        "ceo": "ceo",
    }

    # Twelve Data financial statement endpoints return data under these keys
    STATEMENT_DATA_KEYS = {
        "income_statement": "income_statement",
        "balance_sheet": "balance_sheet",
        "cash_flow": "cash_flow",
        "statistics": "statistics",
    }

    @classmethod
    def convert_financial_data(cls, twelve_data_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a single Twelve Data record to standardized field names.

        Handles the nested structure Twelve Data uses for financial statements:
        nested sub-objects (e.g. current_assets{}, operating_activities{}) are
        flattened one level before mapping so all fields are reachable.

        Args:
            twelve_data_response: Single record dict from Twelve Data API

        Returns:
            Dict with standardized field names; empty dict on failure.
        """
        if not twelve_data_response:
            logger.warning("TwelveDataConverter: empty response received")
            return {}

        try:
            # Unwrap statement-level wrapper if present (e.g. {"income_statement": {...}})
            data = cls._unwrap_response(twelve_data_response)
            # Flatten one level of nesting so sub-object fields become top-level
            flat = cls._flatten_record(data)

            converted: Dict[str, Any] = {}
            for field, value in flat.items():
                if value is None:
                    continue
                standard_name = cls.FIELD_MAPPINGS.get(field, field)
                coerced = cls._normalize_value(value)
                converted[standard_name] = coerced

            converted["source"] = "twelve_data"
            converted["converted_at"] = datetime.now().isoformat()
            return converted

        except Exception as exc:
            logger.error(f"TwelveDataConverter.convert_financial_data error: {exc}")
            return {}

    @classmethod
    def convert_quote(cls, quote_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a /quote endpoint response (real-time price data)."""
        return cls.convert_financial_data(quote_response)

    @classmethod
    def convert_income_statement(cls, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert /income_statement response (annual or quarterly array)."""
        return cls._convert_statement_list(response, "income_statement")

    @classmethod
    def convert_balance_sheet(cls, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert /balance_sheet response."""
        return cls._convert_statement_list(response, "balance_sheet")

    @classmethod
    def convert_cash_flow(cls, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert /cash_flow response."""
        return cls._convert_statement_list(response, "cash_flow")

    @classmethod
    def convert_statistics(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert /statistics response (fundamental ratios)."""
        if not response:
            return {}
        stats = response.get("statistics", response)
        return cls.convert_financial_data(stats)

    @classmethod
    def extract_cash_flow_data(cls, api_data: Any) -> Dict[str, Optional[float]]:
        """
        Extract FCF components from a Twelve Data cash flow API response.

        Args:
            api_data: Raw dict from the /cash_flow endpoint.

        Returns:
            Dict with operating_cash_flow, capital_expenditures, free_cash_flow, source.
        """
        result: Dict[str, Optional[float]] = {
            "operating_cash_flow": None,
            "capital_expenditures": None,
            "free_cash_flow": None,
            "source": "twelve_data",
        }
        if not api_data:
            return result
        try:
            # Unwrap and flatten the response
            data = cls._unwrap_response(api_data) if isinstance(api_data, dict) else api_data
            if isinstance(data, list):
                data = data[0] if data else {}
            flat = cls._flatten_record(data)

            result["operating_cash_flow"] = cls._normalize_value(
                flat.get("operating_cash_flow") or flat.get("net_cash_from_operating_activities")
            )
            result["capital_expenditures"] = cls._normalize_value(
                flat.get("capital_expenditures") or flat.get("capital_expenditure")
            )
            result["free_cash_flow"] = cls._normalize_value(
                flat.get("free_cash_flow")
            )

            # Derive FCF if components are available but direct value is missing
            if result["free_cash_flow"] is None:
                ocf = result["operating_cash_flow"]
                capex = result["capital_expenditures"]
                if ocf is not None and capex is not None:
                    result["free_cash_flow"] = ocf - abs(capex)

        except Exception as exc:
            logger.error(f"TwelveDataConverter.extract_cash_flow_data error: {exc}")

        return result

    @classmethod
    def get_supported_fields(cls) -> List[str]:
        """Return sorted list of all standard field names this converter can produce."""
        return sorted(set(cls.FIELD_MAPPINGS.values()))

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Promote nested dict values one level up.

        Twelve Data financial statement records contain sub-objects for groups
        of related fields (e.g. current_assets{}, operating_activities{}).
        This helper merges those sub-fields into the parent dict so that
        FIELD_MAPPINGS can use simple, flat key names.

        Top-level scalar fields always take precedence over same-named sub-fields.
        """
        flat: Dict[str, Any] = {}
        # First pass: collect sub-fields (lower priority)
        for key, value in record.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in flat:
                        flat[subkey] = subvalue
        # Second pass: top-level scalars override sub-fields
        for key, value in record.items():
            if not isinstance(value, dict):
                flat[key] = value
        return flat

    @classmethod
    def _unwrap_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unwrap a statement-level envelope key (e.g. {'income_statement': {...}}).
        Returns the inner dict if found; otherwise returns the original dict.
        Only unwraps when the value is a plain dict (not a list — lists are
        handled by _convert_statement_list).
        """
        for key in cls.STATEMENT_DATA_KEYS.values():
            if key in response and isinstance(response[key], dict):
                return response[key]
        return response

    @classmethod
    def _convert_statement_list(
        cls, response: Dict[str, Any], wrapper_key: str
    ) -> List[Dict[str, Any]]:
        """
        Convert a statement endpoint that returns a list of periods.

        Args:
            response: Raw API response
            wrapper_key: The key under which the list lives (e.g. 'income_statement')

        Returns:
            List of converted period dicts, most-recent first.
        """
        if not response:
            return []

        try:
            items = response.get(wrapper_key, response)
            if isinstance(items, dict):
                items = [items]
            if not isinstance(items, list):
                return []

            converted_list = []
            for item in items:
                converted = cls.convert_financial_data(item)
                # Preserve the fiscal date for period tracking
                for date_field in ("fiscal_date", "date", "period", "fiscal_year"):
                    if date_field in item:
                        converted["period_date"] = str(item[date_field])
                        break
                converted_list.append(converted)

            return converted_list

        except Exception as exc:
            logger.error(f"TwelveDataConverter._convert_statement_list error: {exc}")
            return []

    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """
        Normalize a raw value to float, or return None.

        Extends BaseConverter._normalize_value() with Twelve Data-specific
        handling. Non-numeric string values that cannot be converted are
        returned as None (not passed through), consistent with other converters.
        """
        return super()._normalize_value(value)

    @classmethod
    def get_standard_field(cls, twelve_data_field: str) -> str:
        """Return the standard field name for a given Twelve Data field name."""
        return cls.FIELD_MAPPINGS.get(twelve_data_field, twelve_data_field)

    @classmethod
    def get_api_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """Reverse lookup: return Twelve Data field name for a standard field."""
        for api_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return api_field
        return None
