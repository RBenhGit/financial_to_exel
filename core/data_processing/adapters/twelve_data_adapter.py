"""
Twelve Data API Adapter
=======================

Extracts financial variables from the Twelve Data API into the project's
standardized VarInputData format, following the same adapter pattern as
FMPAdapter, AlphaVantageAdapter, and PolygonAdapter.

Twelve Data (paid tier) provides:
- Real-time and historical market data
- Financial statements (income, balance sheet, cash flow)
- Fundamental ratios and statistics
- Up to 20 years of annual / quarterly history

API Documentation: https://twelvedata.com/docs
Rate limits (standard paid plan): 500 requests/minute, 10 000 requests/day

Environment variable for API key: TWELVE_DATA_API_KEY

Usage Example:
--------------
>>> from core.data_processing.adapters.twelve_data_adapter import TwelveDataAdapter
>>> adapter = TwelveDataAdapter()          # reads TWELVE_DATA_API_KEY from env
>>> result = adapter.load_symbol_data("AAPL", historical_years=5)
>>> print(f"Quality: {result.quality_metrics.overall_score:.2f}")
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from .base_adapter import (
    ApiCapabilities,
    BaseApiAdapter,
    DataCategory,
    DataQualityMetrics,
    DataSourceType,
    ExtractionResult,
)
from ..converters.twelve_data_converter import TwelveDataConverter
from ..var_input_data import get_var_input_data, VariableMetadata
from ..financial_variable_registry import get_registry

logger = logging.getLogger(__name__)


class TwelveDataAdapter(BaseApiAdapter):
    """
    Twelve Data API adapter.

    Retrieves financial statements, real-time quotes, and fundamental
    statistics from the Twelve Data REST API and stores them in the
    project's VarInputData system.
    """

    BASE_URL = "https://api.twelvedata.com"

    ENDPOINTS = {
        "quote": "/quote",
        "profile": "/symbol_info",
        "income": "/income_statement",
        "balance": "/balance_sheet",
        "cashflow": "/cash_flow",
        "statistics": "/statistics",
        "time_series": "/time_series",
    }

    # Maps DataCategory → list of endpoint keys to query
    CATEGORY_ENDPOINTS: Dict[DataCategory, List[str]] = {
        DataCategory.MARKET_DATA: ["quote", "statistics"],
        DataCategory.INCOME_STATEMENT: ["income"],
        DataCategory.BALANCE_SHEET: ["balance"],
        DataCategory.CASH_FLOW: ["cashflow"],
        DataCategory.FINANCIAL_RATIOS: ["statistics"],
        DataCategory.COMPANY_INFO: ["profile"],
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.12,   # 500 req/min → ~0.12 s between calls
        base_url: Optional[str] = None,
    ) -> None:
        if api_key is None:
            api_key = os.getenv("TWELVE_DATA_API_KEY")

        super().__init__(api_key, timeout, max_retries, retry_delay, rate_limit_delay)

        if not self.api_key:
            logger.warning(
                "TwelveDataAdapter: no API key found. "
                "Set the TWELVE_DATA_API_KEY environment variable."
            )

        self.base_url = base_url or self.BASE_URL
        self.converter = TwelveDataConverter()

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "FinancialAnalysisTool/1.0", "Accept": "application/json"}
        )

        logger.info("TwelveDataAdapter initialized")

    # ── Public interface (required by BaseApiAdapter) ────────────────────────

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.TWELVE_DATA

    def get_capabilities(self) -> ApiCapabilities:
        return ApiCapabilities(
            source_type=DataSourceType.TWELVE_DATA,
            supported_categories=[
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.FINANCIAL_RATIOS,
                DataCategory.COMPANY_INFO,
            ],
            rate_limit_per_minute=500,
            rate_limit_per_day=10_000,
            max_historical_years=20,
            requires_api_key=True,
            supports_batch_requests=True,
            real_time_data=True,
            cost_per_request=None,       # subscription-based
            reliability_rating=0.92,
        )

    def validate_credentials(self) -> bool:
        """Validate the API key with a lightweight AAPL quote request."""
        if not self.api_key:
            logger.error("TwelveDataAdapter.validate_credentials: no API key")
            return False
        try:
            url = f"{self.base_url}{self.ENDPOINTS['quote']}"
            success, response, errors = self.make_request_with_retry(
                self._make_api_request, url, {"symbol": "AAPL", "apikey": self.api_key}
            )
            if success and response and "symbol" in response:
                logger.info("TwelveDataAdapter: credentials validated successfully")
                return True
            logger.error(f"TwelveDataAdapter.validate_credentials failed: {errors}")
            return False
        except Exception as exc:
            logger.error(f"TwelveDataAdapter.validate_credentials error: {exc}")
            return False

    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: Optional[int] = None,
        validate_data: bool = True,
    ) -> ExtractionResult:
        """
        Load financial data for *symbol* from Twelve Data.

        Args:
            symbol: Ticker symbol (e.g. "AAPL")
            categories: Data categories to fetch; defaults to all.
            historical_years: Number of annual fiscal years to retrieve. If None,
                uses the maximum available for this API (20 years).
            validate_data: Whether to validate values against registry definitions.

        Returns:
            ExtractionResult with success/failure details and quality metrics.
        """
        start_time = time.time()
        symbol = self.normalize_symbol(symbol)

        if not self.api_key:
            return self._failed_result(symbol, "No API key configured", start_time)

        if categories is None:
            categories = list(DataCategory)

        max_years = self.get_capabilities().max_historical_years
        historical_years = min(historical_years, max_years) if historical_years is not None else max_years

        result = ExtractionResult(
            source=DataSourceType.TWELVE_DATA,
            symbol=symbol,
            success=False,
            variables_extracted=0,
            data_points_stored=0,
            categories_covered=[],
            periods_covered=[],
            quality_metrics=DataQualityMetrics(0, 0, 0, 0, 0, [], {}),
            extraction_time=0.0,
            errors=[],
            warnings=[],
            metadata={},
        )

        category_results: Dict[str, Dict[str, Any]] = {}
        total_requests = 0

        for category in categories:
            cat_result = self._fetch_category(
                symbol, category, historical_years, validate_data
            )
            category_results[category.value] = cat_result
            total_requests += cat_result.get("requests_made", 0)

            if cat_result["success"]:
                result.categories_covered.append(category)
                result.variables_extracted += cat_result["variables_extracted"]
                result.data_points_stored += cat_result["data_points_stored"]
                result.periods_covered.extend(cat_result.get("periods_covered", []))
                logger.debug(
                    "TwelveData %s %s: %d variables",
                    symbol,
                    category.value,
                    cat_result["variables_extracted"],
                )
            else:
                result.warnings.extend(cat_result.get("warnings", []))

            result.errors.extend(cat_result.get("errors", []))

        result.periods_covered = sorted(set(result.periods_covered), reverse=True)
        result.quality_metrics = self._assess_quality(
            category_results, categories, len(result.categories_covered)
        )
        result.success = bool(result.categories_covered)
        result.extraction_time = time.time() - start_time
        result.metadata = {
            "total_api_requests": total_requests,
            "categories_requested": [c.value for c in categories],
            "historical_years": historical_years,
        }

        self._stats["symbols_processed"] = self._stats.get("symbols_processed", 0) + 1
        logger.info(
            "TwelveData %s: %d vars, quality=%.2f, %.2fs",
            symbol,
            result.variables_extracted,
            result.quality_metrics.overall_score,
            result.extraction_time,
        )
        return result

    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """Check which data categories are available for *symbol*."""
        symbol = self.normalize_symbol(symbol)
        availability: Dict[str, Any] = {
            "symbol": symbol,
            "source": "twelve_data",
            "categories": {},
            "checked_at": datetime.now().isoformat(),
        }

        if not self.api_key:
            availability["error"] = "No API key configured"
            return availability

        probe_categories = [
            DataCategory.MARKET_DATA,
            DataCategory.INCOME_STATEMENT,
        ]
        for cat in probe_categories:
            endpoints = self.CATEGORY_ENDPOINTS.get(cat, [])
            available = False
            for ep_key in endpoints[:1]:
                url = f"{self.base_url}{self.ENDPOINTS[ep_key]}"
                try:
                    success, resp, _ = self.make_request_with_retry(
                        self._make_api_request,
                        url,
                        {"symbol": symbol, "apikey": self.api_key},
                    )
                    if success and resp:
                        available = True
                        break
                except Exception:
                    pass
            availability["categories"][cat.value] = {"available": available}

        return availability

    # ── Private helpers ──────────────────────────────────────────────────────

    def _fetch_category(
        self,
        symbol: str,
        category: DataCategory,
        historical_years: int,
        validate_data: bool,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "category": category.value,
            "success": False,
            "variables_extracted": 0,
            "data_points_stored": 0,
            "periods_covered": [],
            "requests_made": 0,
            "errors": [],
            "warnings": [],
        }

        endpoints = self.CATEGORY_ENDPOINTS.get(category, [])
        if not endpoints:
            result["warnings"].append(f"No endpoints defined for {category.value}")
            return result

        raw_data: Dict[str, Any] = {}
        for ep_key in endpoints:
            ep_url = f"{self.base_url}{self.ENDPOINTS[ep_key]}"
            params = self._build_params(symbol, ep_key, historical_years)
            try:
                success, response, errors = self.make_request_with_retry(
                    self._make_api_request, ep_url, params
                )
                result["requests_made"] += 1
                if success and response:
                    raw_data[ep_key] = response
                else:
                    result["warnings"].extend(errors or [])
            except Exception as exc:
                result["errors"].append(
                    f"TwelveData {ep_key} error for {symbol}: {exc}"
                )

        if not raw_data:
            result["warnings"].append(f"No raw data retrieved for {category.value}")
            return result

        # Convert and store
        stored = self._convert_and_store(symbol, category, raw_data, validate_data)
        result["success"] = stored > 0
        result["variables_extracted"] = stored
        result["data_points_stored"] = stored
        result["periods_covered"] = self._extract_periods(raw_data)
        return result

    def _build_params(
        self, symbol: str, endpoint_key: str, historical_years: int
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"symbol": symbol, "apikey": self.api_key}
        if endpoint_key in {"income", "balance", "cashflow"}:
            params["period"] = "annual"
            params["limit"] = historical_years
        return params

    def _make_api_request(
        self, url: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("status") == "error":
            raise requests.RequestException(
                f"Twelve Data API error: {data.get('message', 'unknown')}"
            )
        return data

    def _convert_and_store(
        self,
        symbol: str,
        category: DataCategory,
        raw_data: Dict[str, Dict[str, Any]],
        validate_data: bool,
    ) -> int:
        stored = 0
        for ep_key, response in raw_data.items():
            if not response:
                continue
            # Statement endpoints return lists; quote/statistics return dicts
            items = self._normalize_to_list(ep_key, response)
            for item in items:
                period = self._extract_period(item)
                converted = self.converter.convert_financial_data(item)
                for field, value in converted.items():
                    if field in {"source", "converted_at", "period_date"}:
                        continue
                    if self._store_variable(
                        symbol, field, value, period,
                        f"twelve_data_{ep_key}", validate_data
                    ):
                        stored += 1
        return stored

    def _normalize_to_list(
        self, endpoint_key: str, response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Unwrap Twelve Data statement arrays; wrap flat dicts into a 1-item list."""
        statement_keys = {"income": "income_statement", "balance": "balance_sheet",
                          "cashflow": "cash_flow"}
        wrapper = statement_keys.get(endpoint_key)
        if wrapper:
            items = response.get(wrapper, response)
            if isinstance(items, list):
                return items
            if isinstance(items, dict):
                return [items]
        if isinstance(response, list):
            return response
        return [response]

    def _store_variable(
        self,
        symbol: str,
        var_name: str,
        value: Any,
        period: str,
        source_detail: str,
        validate_data: bool,
    ) -> bool:
        var_data = get_var_input_data()
        registry = get_registry()
        if not var_data or not registry:
            return False
        try:
            var_def = registry.get_variable_definition(var_name)
            if not var_def:
                return False

            quality_score = 0.92
            validation_passed = True
            if validate_data and hasattr(var_def, "validate_value"):
                is_valid, _ = var_def.validate_value(value)
                if not is_valid:
                    validation_passed = False
                    quality_score *= 0.8

            metadata = VariableMetadata(
                source=source_detail,
                timestamp=datetime.now(),
                quality_score=quality_score,
                validation_passed=validation_passed,
                period=period,
                lineage_id=f"{symbol}_twelve_data_{var_name}_{period}",
            )
            return var_data.set_variable(
                symbol=symbol,
                variable_name=var_name,
                value=value,
                period=period,
                source="twelve_data",
                metadata=metadata,
                validate=False,
                emit_event=False,
            )
        except Exception as exc:
            logger.debug("TwelveData _store_variable error (%s): %s", var_name, exc)
            return False

    def _extract_periods(self, raw_data: Dict[str, Any]) -> List[str]:
        periods: set = set()
        for items in raw_data.values():
            if isinstance(items, list):
                for item in items:
                    p = self._extract_period(item)
                    if p:
                        periods.add(p)
            elif isinstance(items, dict):
                p = self._extract_period(items)
                if p:
                    periods.add(p)
        return sorted(periods, reverse=True)

    @staticmethod
    def _extract_period(item: Dict[str, Any]) -> str:
        for key in ("date", "fiscal_date", "period", "fiscal_year", "year"):
            val = item.get(key)
            if val:
                return str(val)
        return "current"

    def _assess_quality(
        self,
        category_results: Dict[str, Dict[str, Any]],
        requested: List[DataCategory],
        successful_count: int,
    ) -> DataQualityMetrics:
        total = len(requested) or 1
        completeness = successful_count / total
        issues: List[str] = []
        if successful_count < total:
            missing = [
                c.value for c in requested
                if not category_results.get(c.value, {}).get("success")
            ]
            issues.append(f"Missing categories: {', '.join(missing)}")
        timeliness = 0.95
        consistency = 0.92
        reliability = self.get_capabilities().reliability_rating
        overall = (
            completeness * 0.40
            + timeliness * 0.30
            + consistency * 0.20
            + reliability * 0.10
        )
        return DataQualityMetrics(
            completeness_score=completeness,
            timeliness_score=timeliness,
            consistency_score=consistency,
            reliability_score=reliability,
            overall_score=overall,
            issues=issues,
            metadata={},
        )

    def _failed_result(
        self, symbol: str, reason: str, start_time: float
    ) -> ExtractionResult:
        return ExtractionResult(
            source=DataSourceType.TWELVE_DATA,
            symbol=symbol,
            success=False,
            variables_extracted=0,
            data_points_stored=0,
            categories_covered=[],
            periods_covered=[],
            quality_metrics=DataQualityMetrics(0, 0, 0, 0, 0, [reason], {}),
            extraction_time=time.time() - start_time,
            errors=[reason],
            warnings=[],
            metadata={},
        )
