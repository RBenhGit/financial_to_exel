"""
Base Converter Interface
========================

Abstract base class that ALL API converters must implement.
This enforces a consistent interface across all data source converters.

Any new converter added to the system MUST:
1. Inherit from BaseConverter
2. Define FIELD_MAPPINGS class attribute
3. Implement all abstract classmethods below
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseConverter(ABC):
    """
    Abstract base class for all API data converters.

    All converters transform raw API responses into the project's standardized
    field-name format. Subclasses MUST define FIELD_MAPPINGS and implement the
    abstract methods.

    Required class attribute:
        FIELD_MAPPINGS (Dict[str, str]): Maps API-specific field names to
            project-standard snake_case field names.

    Usage pattern:
        class MyApiConverter(BaseConverter):
            FIELD_MAPPINGS = {"apiField": "standard_field", ...}

            @classmethod
            def convert_financial_data(cls, data):
                ...
    """

    # Subclasses MUST define this at class level
    FIELD_MAPPINGS: Dict[str, str] = {}

    @classmethod
    @abstractmethod
    def convert_financial_data(cls, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a raw API response to the project's standardized field names.

        Must include 'source' (str) and 'converted_at' (ISO timestamp) in the
        returned dict. Returns empty dict on failure — never raises.

        Args:
            api_data: Raw response dict from the external API.

        Returns:
            Dict with standardized field names and normalized numeric values.
        """

    @classmethod
    @abstractmethod
    def extract_cash_flow_data(cls, api_data: Any) -> Dict[str, Optional[float]]:
        """
        Extract the FCF components from an API response.

        Must return a dict with AT LEAST these keys (values may be None if
        the API does not provide them):
            - operating_cash_flow (float | None)
            - capital_expenditures (float | None)
            - free_cash_flow (float | None)  — derived if not directly available
            - source (str)

        Args:
            api_data: Raw API response (type may vary by API, e.g. DataFrame for yfinance).

        Returns:
            Dict with FCF components.
        """

    @classmethod
    @abstractmethod
    def get_supported_fields(cls) -> List[str]:
        """
        Return a sorted list of all project-standard field names this converter
        can produce.

        Returns:
            Sorted list of unique standard field name strings.
        """

    @classmethod
    def get_api_field_for_standard(cls, standard_field: str) -> Optional[str]:
        """
        Reverse lookup: return the API-specific field name for a given standard
        field name, or None if not mapped.

        The default implementation searches FIELD_MAPPINGS values.
        Subclasses MAY override for performance or if multiple API fields map
        to the same standard field (returns the first match).

        Args:
            standard_field: A project-standard field name (snake_case).

        Returns:
            The API field name string, or None if not found.
        """
        for api_field, std_field in cls.FIELD_MAPPINGS.items():
            if std_field == standard_field:
                return api_field
        return None

    @classmethod
    def _normalize_value(cls, value: Any) -> Optional[float]:
        """
        Normalize a raw API value to float, or return None if not convertible.

        Handles:
        - None / empty string / common null sentinels ("N/A", "None", "NULL", "-")
        - Strings with currency symbols or thousand separators ("$1,234.56")
        - Percentage strings ("12.5%")
        - pandas NaN / numpy nan (optional — only if pandas is importable)
        - Sanity guard: values with abs > 1e15 are treated as data errors

        Subclasses MAY override but SHOULD call super() or replicate this logic.

        Args:
            value: Any raw value from the API response.

        Returns:
            float if conversion succeeds, None otherwise.
        """
        if value is None:
            return None

        # pandas NaN guard (import is optional — not all converters need pandas)
        try:
            import pandas as pd
            if pd.isna(value):
                return None
        except (ImportError, TypeError, ValueError):
            pass

        # Empty / sentinel strings
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.lower() in {"", "none", "n/a", "na", "null", "-", "--", "nan"}:
                return None
            # Remove formatting characters
            cleaned = cleaned.replace(",", "").replace("$", "").replace("%", "")
            try:
                numeric = float(cleaned)
            except (ValueError, TypeError):
                logger.debug(f"BaseConverter: cannot convert string to float: {value!r}")
                return None
        else:
            try:
                numeric = float(value)
            except (ValueError, TypeError):
                logger.debug(f"BaseConverter: cannot convert value to float: {value!r}")
                return None

        # Sanity guard against obviously corrupt data
        if abs(numeric) > 1e15:
            logger.warning(f"BaseConverter: suspiciously large value ({numeric}), returning None")
            return None

        return numeric

    @classmethod
    def _build_standard_result(cls, converted: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """
        Attach required metadata fields to a converted result dict.

        Args:
            converted: Already-converted data dict.
            source_name: The short name of the data source (e.g. 'alpha_vantage').

        Returns:
            The same dict with 'source' and 'converted_at' added.
        """
        converted["source"] = source_name
        converted["converted_at"] = datetime.now().isoformat()
        return converted
