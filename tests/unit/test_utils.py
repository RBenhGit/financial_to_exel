"""
Unit Tests for Utility Modules
================================

Covers pure-function and unit-testable logic in:

- utils/growth_calculator.py — GrowthRateCalculator:
    calculate_cagr, calculate_growth_rates_for_series, calculate_fcf_growth_rates,
    validate_growth_rate, get_growth_rate_statistics, format_growth_rate,
    _values_have_opposite_signs

- utils/input_validator.py — TickerValidator, ValidationResult, ValidationCache,
    DependencyValidator (_compare_versions), validate_ticker_quick,
    PreFlightValidator (ticker validation path, cache integration)

- utils/field_normalizer.py — FieldNormalizer._normalize_numeric_value,
    calculate_free_cash_flow (pure math path), get_field_variants,
    get_available_fields

- utils/encoding_utils.py — get_default_encoding, get_csv_encoding,
    get_json_encoding, validate_unicode_support, get_system_encoding_info

- utils/error_handler.py — FinancialAnalysisError hierarchy, create_error_summary,
    with_error_handling decorator (pure logic path)
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ---------------------------------------------------------------------------
# growth_calculator
# ---------------------------------------------------------------------------

from utils.growth_calculator import GrowthRateCalculator


class TestGrowthRateCalculatorCAGR:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_simple_doubling_over_one_period(self):
        calc = self._calc()
        result = calc.calculate_cagr(100, 200, 1)
        assert result == pytest.approx(1.0)  # 100% growth

    def test_10_percent_cagr_over_5_years(self):
        calc = self._calc()
        # 100 * (1.10)^5 = 161.05
        result = calc.calculate_cagr(100.0, 161.05, 5)
        assert result == pytest.approx(0.10, rel=1e-3)

    def test_zero_periods_returns_none(self):
        calc = self._calc()
        assert calc.calculate_cagr(100, 200, 0) is None

    def test_negative_periods_returns_none(self):
        calc = self._calc()
        assert calc.calculate_cagr(100, 200, -1) is None

    def test_zero_start_value_returns_none(self):
        calc = self._calc()
        assert calc.calculate_cagr(0, 100, 3) is None

    def test_none_inputs_return_none(self):
        calc = self._calc()
        assert calc.calculate_cagr(None, 100, 3) is None
        assert calc.calculate_cagr(100, None, 3) is None
        assert calc.calculate_cagr(100, 100, None) is None

    def test_both_negative_values_returns_positive_growth(self):
        # Both negative: e.g., losses that grew from -50 to -100 over 2 years
        calc = self._calc()
        result = calc.calculate_cagr(-50, -100, 2)
        assert result is not None
        assert result >= 0  # Implementation returns abs(growth_rate) for both-negative

    def test_sign_change_positive_to_negative_returns_negative_rate(self):
        calc = self._calc()
        result = calc.calculate_cagr(100, -100, 1)
        assert result is not None
        assert result <= 0  # -0.0 is returned for equal absolute values across sign change


class TestGrowthRatesForSeries:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_returns_none_for_insufficient_data(self):
        calc = self._calc()
        result = calc.calculate_growth_rates_for_series([100], [1, 3])
        assert result["1yr"] is None
        assert result["3yr"] is None

    def test_empty_list_returns_none_for_all_periods(self):
        calc = self._calc()
        result = calc.calculate_growth_rates_for_series([], [1, 3])
        assert all(v is None for v in result.values())

    def test_1yr_growth_from_series(self):
        calc = self._calc()
        # 100 → 110 in 1 year = 10%
        result = calc.calculate_growth_rates_for_series([80, 90, 100, 110], [1])
        assert result["1yr"] == pytest.approx(0.10, rel=1e-3)

    def test_period_without_enough_data_is_none(self):
        calc = self._calc()
        # Only 2 values → can compute 1yr but not 5yr
        result = calc.calculate_growth_rates_for_series([100, 110], [1, 5])
        assert result["1yr"] is not None
        assert result["5yr"] is None

    def test_default_periods_used_when_none_given(self):
        calc = self._calc()
        result = calc.calculate_growth_rates_for_series([100, 110, 121, 133, 146, 161])
        assert "1yr" in result
        assert "3yr" in result
        assert "5yr" in result


class TestFCFGrowthRates:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_calculates_for_each_fcf_type(self):
        calc = self._calc()
        fcf_data = {
            "FCFF": [100, 110, 121, 133, 146],
            "FCFE": [80, 88, 97, 107, 118],
        }
        result = calc.calculate_fcf_growth_rates(fcf_data, periods=[1, 3])
        assert "FCFF" in result
        assert "FCFE" in result

    def test_includes_average_across_types(self):
        calc = self._calc()
        fcf_data = {
            "FCFF": [100, 110, 121],
            "FCFE": [80, 88, 97],
        }
        result = calc.calculate_fcf_growth_rates(fcf_data, periods=[1])
        assert "Average" in result

    def test_average_is_between_min_and_max_rates(self):
        calc = self._calc()
        fcf_data = {
            "A": [100, 120],  # 20%
            "B": [100, 110],  # 10%
        }
        result = calc.calculate_fcf_growth_rates(fcf_data, periods=[1])
        avg = result["Average"]["1yr"]
        assert avg == pytest.approx(0.15, rel=1e-3)  # mean of 20% and 10%

    def test_empty_series_not_included(self):
        calc = self._calc()
        fcf_data = {
            "FCFF": [100, 110],
            "EMPTY": [],
        }
        result = calc.calculate_fcf_growth_rates(fcf_data, periods=[1])
        assert "FCFF" in result
        # Empty series should not produce a key (skipped)
        assert "EMPTY" not in result


class TestValidateGrowthRate:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_none_is_acceptable(self):
        assert self._calc().validate_growth_rate(None) is True

    def test_normal_rate_is_valid(self):
        assert self._calc().validate_growth_rate(0.10) is True

    def test_rate_above_max_is_invalid(self):
        # Default max_reasonable=5.0 (500%)
        assert self._calc().validate_growth_rate(6.0) is False

    def test_rate_below_min_is_invalid(self):
        # Default min_reasonable=-0.9 (-90%)
        assert self._calc().validate_growth_rate(-1.0) is False

    def test_nan_is_invalid(self):
        import math
        assert self._calc().validate_growth_rate(float('nan')) is False

    def test_infinity_is_invalid(self):
        assert self._calc().validate_growth_rate(float('inf')) is False

    def test_non_numeric_is_invalid(self):
        assert self._calc().validate_growth_rate("0.10") is False

    def test_boundary_min_is_valid(self):
        assert self._calc().validate_growth_rate(-0.9) is True

    def test_boundary_max_is_valid(self):
        assert self._calc().validate_growth_rate(5.0) is True


class TestGrowthRateStatistics:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_all_none_returns_empty_stats(self):
        calc = self._calc()
        result = calc.get_growth_rate_statistics({"1yr": None, "3yr": None})
        assert result["count"] == 0
        assert result["mean"] is None

    def test_stats_with_valid_rates(self):
        calc = self._calc()
        rates = {"1yr": 0.10, "3yr": 0.12, "5yr": 0.08}
        result = calc.get_growth_rate_statistics(rates)
        assert result["count"] == 3
        assert result["mean"] == pytest.approx(0.10, rel=1e-3)
        assert result["min"] == pytest.approx(0.08)
        assert result["max"] == pytest.approx(0.12)

    def test_stats_ignore_none_values(self):
        calc = self._calc()
        rates = {"1yr": 0.10, "3yr": None, "5yr": 0.20}
        result = calc.get_growth_rate_statistics(rates)
        assert result["count"] == 2
        assert result["mean"] == pytest.approx(0.15)


class TestFormatGrowthRate:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_none_returns_na(self):
        assert self._calc().format_growth_rate(None) == "N/A"

    def test_infinity_returns_na(self):
        assert self._calc().format_growth_rate(float('inf')) == "N/A"

    def test_percentage_format(self):
        result = self._calc().format_growth_rate(0.105, as_percentage=True, decimal_places=1)
        assert result == "10.5%"

    def test_decimal_format(self):
        result = self._calc().format_growth_rate(0.105, as_percentage=False, decimal_places=2)
        assert result == "0.10"

    def test_zero_growth(self):
        result = self._calc().format_growth_rate(0.0)
        assert result == "0.0%"


class TestValuesHaveOppositeSigns:
    def _calc(self) -> GrowthRateCalculator:
        return GrowthRateCalculator()

    def test_positive_negative(self):
        assert self._calc()._values_have_opposite_signs(10, -5) is True

    def test_negative_positive(self):
        assert self._calc()._values_have_opposite_signs(-3, 7) is True

    def test_both_positive(self):
        assert self._calc()._values_have_opposite_signs(5, 10) is False

    def test_both_negative(self):
        assert self._calc()._values_have_opposite_signs(-5, -10) is False

    def test_none_values(self):
        assert self._calc()._values_have_opposite_signs(None, 5) is False
        assert self._calc()._values_have_opposite_signs(5, None) is False


# ---------------------------------------------------------------------------
# input_validator — TickerValidator
# ---------------------------------------------------------------------------

from utils.input_validator import (
    TickerValidator,
    ValidationLevel,
    ValidationResult as IVValidationResult,
    ValidationCache,
    DependencyValidator,
    validate_ticker_quick,
    PreFlightValidator,
)


class TestTickerValidatorStrict:
    def _validator(self) -> TickerValidator:
        return TickerValidator(ValidationLevel.STRICT)

    def test_valid_short_ticker(self):
        result = self._validator().validate("AAPL")
        assert result.is_valid is True

    def test_valid_ticker_with_exchange_suffix(self):
        result = self._validator().validate("RY.TO")
        assert result.is_valid is True

    def test_empty_string_invalid(self):
        result = self._validator().validate("")
        assert result.is_valid is False
        assert result.error_code == "EMPTY_TICKER"

    def test_none_invalid(self):
        result = self._validator().validate(None)
        assert result.is_valid is False

    def test_lowercase_ticker_normalised_in_strict(self):
        # Strict mode normalises lowercase to uppercase, so 'aapl' -> 'AAPL' is valid
        result = self._validator().validate("aapl")
        assert result.metadata.get("clean_ticker") == "AAPL"

    def test_too_long_ticker_invalid(self):
        result = self._validator().validate("TOOLONGTICKER")
        assert result.is_valid is False
        assert result.error_code in ("TICKER_TOO_LONG", "INVALID_FORMAT")

    def test_special_chars_invalid(self):
        result = self._validator().validate("INVALID@TICKER")
        assert result.is_valid is False

    def test_valid_result_carries_metadata(self):
        result = self._validator().validate("MSFT")
        assert result.is_valid is True
        assert result.metadata is not None
        assert result.metadata["clean_ticker"] == "MSFT"


class TestTickerValidatorModerate:
    def _validator(self) -> TickerValidator:
        return TickerValidator(ValidationLevel.MODERATE)

    def test_valid_ticker(self):
        assert self._validator().validate("IBM").is_valid is True

    def test_ticker_with_numbers_valid_in_moderate(self):
        # E.g., "BRK.B" — moderate allows letters/numbers
        assert self._validator().validate("BRK.B").is_valid is True

    def test_spaces_invalid(self):
        # Leading/trailing spaces are stripped before validation; interior spaces fail pattern
        result = self._validator().validate("BRK B")
        assert result.is_valid is False

    def test_non_string_invalid(self):
        result = self._validator().validate(12345)
        assert result.is_valid is False
        assert result.error_code == "INVALID_TYPE"


class TestValidateTicker_Quick:
    def test_valid_ticker_returns_true(self):
        assert validate_ticker_quick("AAPL") is True

    def test_invalid_ticker_returns_false(self):
        assert validate_ticker_quick("") is False

    def test_uses_moderate_level_by_default(self):
        # Moderate allows BRK.B
        assert validate_ticker_quick("BRK.B", ValidationLevel.MODERATE) is True


class TestValidationResult:
    def test_default_lists_populated_in_post_init(self):
        r = IVValidationResult(is_valid=True)
        assert r.warnings == []
        assert r.metadata == {}

    def test_error_fields_accessible(self):
        r = IVValidationResult(
            is_valid=False,
            error_code="TEST_CODE",
            error_message="Something went wrong",
            remediation="Fix it",
        )
        assert r.error_code == "TEST_CODE"
        assert r.error_message == "Something went wrong"
        assert r.remediation == "Fix it"


class TestValidationCache:
    def test_cache_hit_returns_stored_result(self):
        cache = ValidationCache(ttl_seconds=60)
        result = IVValidationResult(is_valid=True)
        cache.set("ticker", {"symbol": "AAPL"}, result)
        retrieved = cache.get("ticker", {"symbol": "AAPL"})
        assert retrieved is result

    def test_cache_miss_returns_none(self):
        cache = ValidationCache(ttl_seconds=60)
        result = cache.get("ticker", {"symbol": "UNKNOWN"})
        assert result is None

    def test_expired_cache_entry_returns_none(self):
        cache = ValidationCache(ttl_seconds=1)
        result = IVValidationResult(is_valid=True)
        cache.set("ticker", {"symbol": "AAPL"}, result)
        # Manually expire by setting timestamp in the past
        key = cache._get_cache_key("ticker", {"symbol": "AAPL"})
        cache._cache[key] = (result, time.time() - 10)
        assert cache.get("ticker", {"symbol": "AAPL"}) is None

    def test_clear_removes_all_entries(self):
        cache = ValidationCache(ttl_seconds=60)
        cache.set("t", {"k": "v"}, IVValidationResult(is_valid=True))
        cache.clear()
        assert cache.get("t", {"k": "v"}) is None


class TestDependencyValidatorVersionComparison:
    """Test the pure version comparison logic."""

    def _validator(self) -> DependencyValidator:
        return DependencyValidator()

    def test_higher_version_passes(self):
        v = self._validator()
        assert v._compare_versions("2.0.0", "1.0.0") is True

    def test_equal_version_passes(self):
        v = self._validator()
        assert v._compare_versions("1.5.0", "1.5.0") is True

    def test_lower_version_fails(self):
        v = self._validator()
        assert v._compare_versions("1.0.0", "2.0.0") is False

    def test_patch_version_comparison(self):
        v = self._validator()
        assert v._compare_versions("1.0.5", "1.0.3") is True

    def test_unparseable_version_returns_true(self):
        v = self._validator()
        assert v._compare_versions("unparseable", "1.0.0") is True


class TestPreFlightValidatorTickerPath:
    """Test the ticker validation path of PreFlightValidator (no network calls)."""

    def test_valid_ticker_passes(self):
        pf = PreFlightValidator()
        result = pf.validate_ticker("AAPL", use_cache=False)
        assert result.is_valid is True

    def test_invalid_ticker_fails(self):
        pf = PreFlightValidator()
        result = pf.validate_ticker("", use_cache=False)
        assert result.is_valid is False

    def test_cache_stores_and_retrieves(self):
        pf = PreFlightValidator(enable_caching=True, cache_ttl=60)
        result1 = pf.validate_ticker("IBM", use_cache=True)
        result2 = pf.validate_ticker("IBM", use_cache=True)
        assert result1.is_valid == result2.is_valid

    def test_validate_all_skips_network_when_requested(self):
        pf = PreFlightValidator()
        results = pf.validate_all("GOOG", skip_network=True)
        assert "ticker" in results
        assert "network" not in results
        assert "dependencies" in results

    def test_is_ready_for_api_call_valid_ticker_no_network(self):
        pf = PreFlightValidator()
        ready, errors = pf.is_ready_for_api_call("AAPL", skip_network=True)
        # May not be fully ready due to dependency versions, but no ticker errors
        ticker_errors = [e for e in errors if "TICKER" in e]
        assert ticker_errors == []

    def test_is_ready_for_api_call_invalid_ticker(self):
        pf = PreFlightValidator()
        ready, errors = pf.is_ready_for_api_call("", skip_network=True)
        assert ready is False
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# field_normalizer — pure calculation helpers
# ---------------------------------------------------------------------------

from utils.field_normalizer import FieldNormalizer


class TestFieldNormalizerNormalizeNumericValue:
    """_normalize_numeric_value is a pure function with no I/O."""

    def _normalizer(self) -> FieldNormalizer:
        # The constructor tries to load a JSON file; we patch the loader to avoid I/O
        fn = FieldNormalizer.__new__(FieldNormalizer)
        fn.mappings_file = MagicMock()
        fn.mappings_file.exists.return_value = False
        fn.mappings = {}
        fn.standard_fields = {}
        fn.calculation_rules = {}
        fn.data_structure_hints = {}
        fn._create_default_mappings()
        return fn

    def test_integer_value(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(42) == pytest.approx(42.0)

    def test_float_value(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(3.14) == pytest.approx(3.14)

    def test_string_integer(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("1000") == pytest.approx(1000.0)

    def test_string_with_commas(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("1,000,000") == pytest.approx(1_000_000.0)

    def test_string_with_dollar_sign(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("$50.25") == pytest.approx(50.25)

    def test_string_na_returns_none(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("N/A") is None
        assert fn._normalize_numeric_value("na") is None
        assert fn._normalize_numeric_value("none") is None

    def test_empty_string_returns_none(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("") is None

    def test_none_returns_none(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(None) is None

    def test_extremely_large_value_returns_none(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(2e15) is None

    def test_negative_value(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(-500.0) == pytest.approx(-500.0)

    def test_zero(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value(0) == pytest.approx(0.0)

    def test_non_numeric_string_returns_none(self):
        fn = self._normalizer()
        assert fn._normalize_numeric_value("hello") is None


class TestFieldNormalizerCalculateFCF:
    """calculate_free_cash_flow pure math."""

    def _normalizer(self) -> FieldNormalizer:
        fn = FieldNormalizer.__new__(FieldNormalizer)
        fn.mappings_file = MagicMock()
        fn.mappings_file.exists.return_value = False
        fn.mappings = {}
        fn.standard_fields = {}
        fn.calculation_rules = {}
        fn.data_structure_hints = {}
        fn._create_default_mappings()
        return fn

    def test_fcf_with_negative_capex(self):
        fn = self._normalizer()
        # negative_reported convention: FCF = OCF + CapEx (CapEx is negative)
        result = fn.calculate_free_cash_flow(
            operating_cash_flow=500.0,
            capital_expenditures=-100.0,
            api_source="yfinance",  # uses default negative_reported
        )
        assert result == pytest.approx(400.0)

    def test_fcf_with_positive_capex_positive_convention(self):
        fn = self._normalizer()
        # If the calculation_rules don't specify a special convention, falls back to negative_reported
        # Test with explicitly set calculation rule
        fn.calculation_rules = {"capex_sign_handling": {"fmp": "positive_reported"}}
        result = fn.calculate_free_cash_flow(
            operating_cash_flow=500.0,
            capital_expenditures=100.0,
            api_source="fmp",
        )
        # positive_reported: FCF = OCF - abs(CapEx)
        assert result == pytest.approx(400.0)

    def test_none_ocf_returns_none(self):
        fn = self._normalizer()
        assert fn.calculate_free_cash_flow(None, -100.0, "yfinance") is None

    def test_none_capex_returns_none(self):
        fn = self._normalizer()
        assert fn.calculate_free_cash_flow(500.0, None, "yfinance") is None


class TestFieldNormalizerMappingHelpers:
    def _normalizer_with_mappings(self) -> FieldNormalizer:
        fn = FieldNormalizer.__new__(FieldNormalizer)
        fn.mappings_file = MagicMock()
        fn.mappings_file.exists.return_value = False
        fn.mappings = {
            "yfinance": {
                "operating_cash_flow": ["Total Cash From Operating Activities"],
                "capital_expenditures": ["Capital Expenditures"],
            }
        }
        fn.standard_fields = {"operating_cash_flow": "operating_cash_flow"}
        fn.calculation_rules = {}
        fn.data_structure_hints = {}
        return fn

    def test_get_available_fields_returns_list(self):
        fn = self._normalizer_with_mappings()
        fields = fn.get_available_fields("yfinance")
        assert "operating_cash_flow" in fields
        assert "capital_expenditures" in fields

    def test_get_available_fields_unknown_source_returns_empty(self):
        fn = self._normalizer_with_mappings()
        fields = fn.get_available_fields("unknown_api")
        assert fields == []

    def test_get_field_variants_returns_variants(self):
        fn = self._normalizer_with_mappings()
        variants = fn.get_field_variants("yfinance", "operating_cash_flow")
        assert "Total Cash From Operating Activities" in variants

    def test_get_field_variants_unknown_field_returns_empty(self):
        fn = self._normalizer_with_mappings()
        variants = fn.get_field_variants("yfinance", "nonexistent_field")
        assert variants == []


# ---------------------------------------------------------------------------
# encoding_utils
# ---------------------------------------------------------------------------

from utils.encoding_utils import (
    get_default_encoding,
    get_csv_encoding,
    get_json_encoding,
    validate_unicode_support,
    get_system_encoding_info,
)


class TestEncodingUtils:
    def test_get_json_encoding_always_utf8(self):
        assert get_json_encoding() == "utf-8"

    def test_get_csv_encoding_returns_string(self):
        result = get_csv_encoding()
        assert isinstance(result, str)
        assert "utf" in result.lower()

    def test_get_default_encoding_returns_string(self):
        result = get_default_encoding()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_default_encoding_on_windows(self):
        with patch("utils.encoding_utils.sys") as mock_sys:
            mock_sys.platform = "win32"
            result = get_default_encoding()
        assert result == "utf-8-sig"

    def test_get_default_encoding_on_linux(self):
        with patch("utils.encoding_utils.sys") as mock_sys:
            mock_sys.platform = "linux"
            result = get_default_encoding()
        assert result == "utf-8"

    def test_get_csv_encoding_on_windows(self):
        with patch("utils.encoding_utils.sys") as mock_sys:
            mock_sys.platform = "win32"
            result = get_csv_encoding()
        assert result == "utf-8-sig"

    def test_get_csv_encoding_on_non_windows(self):
        with patch("utils.encoding_utils.sys") as mock_sys:
            mock_sys.platform = "linux"
            result = get_csv_encoding()
        assert result == "utf-8"

    def test_validate_unicode_support_returns_true(self):
        # Standard Python should handle Unicode correctly
        assert validate_unicode_support() is True

    def test_get_system_encoding_info_returns_dict(self):
        info = get_system_encoding_info()
        assert isinstance(info, dict)
        required_keys = [
            "platform", "default_encoding", "filesystem_encoding",
            "recommended_csv", "recommended_json", "recommended_default",
        ]
        for key in required_keys:
            assert key in info, f"Missing key: {key}"

    def test_encoding_info_json_encoding_is_utf8(self):
        info = get_system_encoding_info()
        assert info["recommended_json"] == "utf-8"


# ---------------------------------------------------------------------------
# error_handler (utils/error_handler.py)
# ---------------------------------------------------------------------------

# The error_handler module imports from 'config' at module level which may
# trigger SettingsManager initialization. Import it carefully.
try:
    from utils.error_handler import (
        FinancialAnalysisError,
        ExcelDataError,
        ValidationError,
        CalculationError,
        ConfigurationError,
        with_error_handling,
        create_error_summary,
        validate_financial_data,
    )
    _error_handler_available = True
except Exception:
    _error_handler_available = False


@pytest.mark.skipif(not _error_handler_available, reason="utils.error_handler not importable")
class TestFinancialAnalysisErrorHierarchy:
    def test_base_error_can_be_raised_and_caught(self):
        with pytest.raises(FinancialAnalysisError):
            raise FinancialAnalysisError("base error")

    def test_base_error_has_message_attribute(self):
        err = FinancialAnalysisError("something went wrong", error_code="ERR001")
        assert err.message == "something went wrong"
        assert err.error_code == "ERR001"

    def test_base_error_has_timestamp(self):
        from datetime import datetime
        err = FinancialAnalysisError("test")
        assert isinstance(err.timestamp, datetime)

    def test_to_dict_contains_required_keys(self):
        err = FinancialAnalysisError("test", error_code="T001", context={"key": "value"})
        d = err.to_dict()
        assert "message" in d
        assert "error_code" in d
        assert "context" in d
        assert "timestamp" in d
        assert "type" in d

    def test_excel_data_error_is_subclass(self):
        with pytest.raises(FinancialAnalysisError):
            raise ExcelDataError("Excel problem")

    def test_validation_error_is_subclass(self):
        with pytest.raises(FinancialAnalysisError):
            raise ValidationError("Validation problem")

    def test_calculation_error_is_subclass(self):
        with pytest.raises(FinancialAnalysisError):
            raise CalculationError("Calculation problem")

    def test_configuration_error_is_subclass(self):
        with pytest.raises(FinancialAnalysisError):
            raise ConfigurationError("Config problem")

    def test_errors_can_be_distinguished_by_type(self):
        errors = [
            ExcelDataError("e1"),
            ValidationError("e2"),
            CalculationError("e3"),
        ]
        excel_errs = [e for e in errors if isinstance(e, ExcelDataError)]
        calc_errs = [e for e in errors if isinstance(e, CalculationError)]
        assert len(excel_errs) == 1
        assert len(calc_errs) == 1


@pytest.mark.skipif(not _error_handler_available, reason="utils.error_handler not importable")
class TestCreateErrorSummary:
    def test_empty_errors_and_warnings(self):
        result = create_error_summary([], [])
        assert result["total_errors"] == 0
        assert result["total_warnings"] == 0
        assert result["recommendations"] == []

    def test_counts_errors_correctly(self):
        errors = [{"type": "ExcelDataError"}, {"type": "ValidationError"}, {"type": "ExcelDataError"}]
        result = create_error_summary(errors, [])
        assert result["total_errors"] == 3
        assert result["error_types"]["ExcelDataError"] == 2

    def test_counts_warnings_correctly(self):
        warnings = [{"type": "DataWarning"}, {"type": "DataWarning"}]
        result = create_error_summary([], warnings)
        assert result["total_warnings"] == 2

    def test_recommendation_for_errors(self):
        errors = [{"type": "SomeError"}]
        result = create_error_summary(errors, [])
        assert len(result["recommendations"]) > 0

    def test_recommendation_for_high_warning_count(self):
        warnings = [{"type": "W"}] * 11
        result = create_error_summary([], warnings)
        assert any("warning" in r.lower() for r in result["recommendations"])

    def test_excel_error_gives_specific_recommendation(self):
        errors = [{"type": "ExcelDataError"}]
        result = create_error_summary(errors, [])
        assert any("excel" in r.lower() or "Excel" in r for r in result["recommendations"])

    def test_critical_errors_extracted(self):
        errors = [
            {"type": "E", "level": "CRITICAL"},
            {"type": "E"},
        ]
        result = create_error_summary(errors, [])
        assert len(result["critical_errors"]) == 1


@pytest.mark.skipif(not _error_handler_available, reason="utils.error_handler not importable")
class TestWithErrorHandlingDecorator:
    def test_successful_function_returns_result(self):
        @with_error_handling(error_type=CalculationError, return_on_error=None)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_error_returns_fallback_value(self):
        @with_error_handling(error_type=CalculationError, return_on_error=-1)
        def divide(a, b):
            return a / b

        result = divide(10, 0)
        assert result == -1

    def test_re_raise_option_raises_custom_error(self):
        @with_error_handling(error_type=CalculationError, re_raise=True)
        def fail():
            raise ValueError("original error")

        with pytest.raises((ValueError, CalculationError)):
            fail()

    def test_financial_analysis_error_re_raised_as_is(self):
        @with_error_handling(error_type=CalculationError, re_raise=True)
        def raise_financial_error():
            raise CalculationError("already the right type")

        with pytest.raises(CalculationError):
            raise_financial_error()

    def test_decorated_function_preserves_name(self):
        @with_error_handling()
        def my_function():
            pass

        assert my_function.__name__ == "my_function"


@pytest.mark.skipif(not _error_handler_available, reason="utils.error_handler not importable")
class TestValidateFinancialData:
    def test_none_data_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_financial_data(None, "test_data")

    def test_valid_dict_with_required_fields_passes(self):
        data = {"revenue": 100, "net_income": 20}
        result = validate_financial_data(data, "income_statement", required_fields=["revenue"])
        assert result is True

    def test_missing_required_field_raises_validation_error(self):
        data = {"revenue": 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_financial_data(data, "income_statement", required_fields=["revenue", "net_income"])
        assert "net_income" in str(exc_info.value)

    def test_no_required_fields_passes_for_non_none_data(self):
        result = validate_financial_data({"any": "data"}, "generic")
        assert result is True
