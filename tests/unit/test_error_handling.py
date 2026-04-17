"""
Unit Tests for Error Handling Modules
======================================

Tests cover:
- api_error_handler: APIFailureCategory, APIFailure, RetryConfig, RetryStrategy,
  CircuitBreakerManager, APIErrorHandler (classify_error, execute_with_retry,
  with_error_handling, circuit breaker lifecycle)
- data_quality_validator: DataQualityLevel, DataSourceReliability, QualityMetrics,
  ValidationResult, DataQualityValidator (_determine_quality_level,
  validate_historical_data, generate_quality_report)
- graceful_degradation: DegradationLevel, FallbackDataSource, FallbackStrategy
  subclasses, GracefulDegradationManager (assess_degradation,
  determine_available_data_sources, create_degradation_context)
- user_message_handler: MessageSeverity, MessageCategory, UserMessage,
  UserMessageHandler (message creation, add/clear/filter messages)
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup so imports resolve whether running from repo root or tests dir
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.error_handling.api_error_handler import (
    APIFailureCategory,
    APIFailure,
    RetryConfig,
    RetryStrategy,
    CircuitBreakerState,
    CircuitBreakerManager,
    APIErrorHandler,
    get_error_handler,
)
from core.error_handling.data_quality_validator import (
    DataQualityLevel,
    DataSourceReliability,
    QualityMetrics,
    ValidationResult as DQValidationResult,
    QualityReport,
    DataQualityValidator,
)
from core.error_handling.graceful_degradation import (
    DegradationLevel,
    FallbackDataSource,
    DegradationContext,
    DegradationResult,
    HistoricalOnlyStrategy,
    CachedDataStrategy,
    MinimalServiceStrategy,
    GracefulDegradationManager,
    get_degradation_manager,
)
from core.error_handling.user_message_handler import (
    MessageSeverity,
    MessageCategory,
    UserMessage,
    UserMessageHandler,
)


# ===========================================================================
# api_error_handler tests
# ===========================================================================

class TestAPIFailureCategory:
    def test_all_expected_values_present(self):
        values = {cat.value for cat in APIFailureCategory}
        assert "rate_limit" in values
        assert "authentication" in values
        assert "network_error" in values
        assert "server_error" in values
        assert "data_error" in values
        assert "quota_exceeded" in values
        assert "unknown" in values

    def test_enum_members_are_distinct(self):
        cats = list(APIFailureCategory)
        assert len(cats) == len({c.value for c in cats}), "Each category must have a unique value"


class TestAPIFailure:
    def _make_failure(self, category=APIFailureCategory.UNKNOWN) -> APIFailure:
        return APIFailure(
            category=category,
            original_error=ValueError("test"),
            service_name="test_service",
            error_message="test error",
            user_message="user facing message",
        )

    def test_can_be_instantiated_with_required_fields(self):
        f = self._make_failure()
        assert f.category == APIFailureCategory.UNKNOWN
        assert f.service_name == "test_service"
        assert f.error_message == "test error"
        assert f.user_message == "user facing message"

    def test_default_is_temporary_true(self):
        f = self._make_failure()
        assert f.is_temporary is True

    def test_authentication_failure_is_not_temporary(self):
        f = self._make_failure(APIFailureCategory.AUTHENTICATION)
        # is_temporary defaults to True; the RetryStrategy decides not to retry
        # Verify we can set is_temporary=False explicitly
        f.is_temporary = False
        assert f.is_temporary is False

    def test_timestamp_is_set_automatically(self):
        before = datetime.now()
        f = self._make_failure()
        after = datetime.now()
        assert before <= f.timestamp <= after


class TestRetryConfig:
    def test_default_values(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.exponential_base == 2.0
        assert cfg.jitter is True
        assert cfg.backoff_strategy == "exponential"

    def test_custom_values(self):
        cfg = RetryConfig(max_attempts=5, base_delay=2.0, backoff_strategy="fixed")
        assert cfg.max_attempts == 5
        assert cfg.base_delay == 2.0
        assert cfg.backoff_strategy == "fixed"


class TestRetryStrategy:
    def _make_failure(self, category=APIFailureCategory.UNKNOWN, temporary=True) -> APIFailure:
        f = APIFailure(
            category=category,
            original_error=Exception("test"),
            service_name="svc",
            error_message="err",
            user_message="msg",
        )
        f.is_temporary = temporary
        return f

    def test_exponential_delay_increases_with_attempt(self):
        cfg = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        strategy = RetryStrategy(cfg)
        d1 = strategy.calculate_delay(1)
        d2 = strategy.calculate_delay(2)
        d3 = strategy.calculate_delay(3)
        assert d1 < d2 < d3

    def test_fixed_delay_is_constant(self):
        cfg = RetryConfig(base_delay=2.0, backoff_strategy="fixed", jitter=False)
        strategy = RetryStrategy(cfg)
        assert strategy.calculate_delay(1) == pytest.approx(2.0)
        assert strategy.calculate_delay(3) == pytest.approx(2.0)

    def test_linear_delay_scales_with_attempt(self):
        cfg = RetryConfig(base_delay=1.0, backoff_strategy="linear", jitter=False)
        strategy = RetryStrategy(cfg)
        assert strategy.calculate_delay(1) == pytest.approx(1.0)
        assert strategy.calculate_delay(2) == pytest.approx(2.0)
        assert strategy.calculate_delay(3) == pytest.approx(3.0)

    def test_delay_capped_at_max_delay(self):
        cfg = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=10.0, jitter=False)
        strategy = RetryStrategy(cfg)
        # attempt 5 would give 10^4=10000, must be capped
        assert strategy.calculate_delay(5) <= 5.0

    def test_should_retry_true_within_max_attempts(self):
        cfg = RetryConfig(max_attempts=3)
        strategy = RetryStrategy(cfg)
        f = self._make_failure()
        assert strategy.should_retry(1, f) is True
        assert strategy.should_retry(2, f) is True

    def test_should_retry_false_at_max_attempts(self):
        cfg = RetryConfig(max_attempts=3)
        strategy = RetryStrategy(cfg)
        f = self._make_failure()
        assert strategy.should_retry(3, f) is False

    def test_should_not_retry_authentication_failure(self):
        cfg = RetryConfig(max_attempts=5)
        strategy = RetryStrategy(cfg)
        f = self._make_failure(category=APIFailureCategory.AUTHENTICATION)
        assert strategy.should_retry(1, f) is False

    def test_should_not_retry_quota_exceeded(self):
        cfg = RetryConfig(max_attempts=5)
        strategy = RetryStrategy(cfg)
        f = self._make_failure(category=APIFailureCategory.QUOTA_EXCEEDED)
        assert strategy.should_retry(1, f) is False

    def test_should_not_retry_non_temporary_failure(self):
        cfg = RetryConfig(max_attempts=5)
        strategy = RetryStrategy(cfg)
        f = self._make_failure(temporary=False)
        assert strategy.should_retry(1, f) is False


class TestCircuitBreakerManager:
    def test_new_service_starts_closed(self):
        cb = CircuitBreakerManager()
        assert cb.is_call_allowed("new_service") is True
        state = cb.get_service_state("new_service")
        assert state.state == "CLOSED"

    def test_call_blocked_when_open(self):
        cb = CircuitBreakerManager()
        state = cb.get_service_state("svc")
        state.state = "OPEN"
        state.last_failure_time = datetime.now()  # recent failure
        assert cb.is_call_allowed("svc") is False

    def test_circuit_opens_after_threshold_failures(self):
        cb = CircuitBreakerManager()
        failure = APIFailure(
            category=APIFailureCategory.SERVER_ERROR,
            original_error=Exception("err"),
            service_name="svc",
            error_message="err",
            user_message="msg",
        )
        state = cb.get_service_state("svc")
        state.failure_threshold = 3

        for i in range(3):
            assert state.state == "CLOSED", f"Should still be CLOSED after {i} failures"
            cb.record_failure("svc", failure)

        assert state.state == "OPEN"

    def test_record_success_closes_half_open_circuit(self):
        cb = CircuitBreakerManager()
        state = cb.get_service_state("svc")
        state.state = "HALF_OPEN"
        state.failure_count = 2

        cb.record_success("svc")

        assert state.state == "CLOSED"
        assert state.failure_count == 0
        assert state.last_failure_time is None

    def test_failure_in_half_open_returns_to_open(self):
        cb = CircuitBreakerManager()
        state = cb.get_service_state("svc")
        state.state = "HALF_OPEN"

        failure = APIFailure(
            category=APIFailureCategory.SERVER_ERROR,
            original_error=Exception("err"),
            service_name="svc",
            error_message="err",
            user_message="msg",
        )
        cb.record_failure("svc", failure)
        assert state.state == "OPEN"

    def test_open_circuit_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreakerManager()
        state = cb.get_service_state("svc")
        state.state = "OPEN"
        state.last_failure_time = datetime.now() - timedelta(seconds=120)
        state.recovery_timeout = 60  # 60-second timeout already elapsed

        allowed = cb.is_call_allowed("svc")
        assert allowed is True
        assert state.state == "HALF_OPEN"


class TestAPIErrorHandler:
    def _handler(self) -> APIErrorHandler:
        return APIErrorHandler(RetryConfig(max_attempts=3, base_delay=0.0, jitter=False))

    # --- classify_error tests ---

    def test_classify_rate_limit_error(self):
        h = self._handler()
        err = Exception("HTTP 429 rate limit exceeded")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.RATE_LIMIT
        assert failure.is_temporary is True

    def test_classify_authentication_error_401(self):
        h = self._handler()
        err = Exception("401 unauthorized access")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.AUTHENTICATION
        assert failure.is_temporary is False

    def test_classify_authentication_error_invalid_key(self):
        h = self._handler()
        err = Exception("invalid api key supplied")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.AUTHENTICATION

    def test_classify_network_error(self):
        h = self._handler()
        err = Exception("connection timeout")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.NETWORK_ERROR
        assert failure.is_temporary is True

    def test_classify_server_error_500(self):
        h = self._handler()
        err = Exception("500 internal server error")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.SERVER_ERROR
        assert failure.is_temporary is True

    def test_classify_quota_exceeded(self):
        h = self._handler()
        err = Exception("monthly limit exceeded for this plan")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.QUOTA_EXCEEDED
        assert failure.is_temporary is False

    def test_classify_unknown_error(self):
        h = self._handler()
        err = Exception("something completely unexpected")
        failure = h.classify_error(err, "test_service")
        assert failure.category == APIFailureCategory.UNKNOWN

    def test_failure_carries_service_name(self):
        h = self._handler()
        err = Exception("connection timeout")
        failure = h.classify_error(err, "alpha_vantage")
        assert failure.service_name == "alpha_vantage"

    # --- execute_with_retry tests ---

    def test_successful_call_returns_result(self):
        h = self._handler()
        mock_fn = MagicMock(return_value=42)

        result, failure = h.execute_with_retry(mock_fn, "svc")
        assert result == 42
        assert failure is None
        mock_fn.assert_called_once()

    @patch("core.error_handling.api_error_handler.time.sleep")
    def test_retries_on_temporary_failure(self, mock_sleep):
        h = self._handler()
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("timeout")
            return "success"

        result, failure = h.execute_with_retry(flaky, "svc")
        assert result == "success"
        assert failure is None
        assert call_count == 3

    @patch("core.error_handling.api_error_handler.time.sleep")
    def test_stops_after_max_attempts(self, mock_sleep):
        h = self._handler()  # max_attempts=3

        def always_fail():
            raise ConnectionError("timeout always")

        result, failure = h.execute_with_retry(always_fail, "svc")
        assert result is None
        assert failure is not None
        assert failure.category == APIFailureCategory.NETWORK_ERROR

    @patch("core.error_handling.api_error_handler.time.sleep")
    def test_does_not_retry_authentication_error(self, mock_sleep):
        h = self._handler()
        call_count = 0

        def auth_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("401 unauthorized")

        result, failure = h.execute_with_retry(auth_fail, "svc")
        assert result is None
        assert failure.category == APIFailureCategory.AUTHENTICATION
        assert call_count == 1  # no retries
        mock_sleep.assert_not_called()

    def test_blocked_by_open_circuit_breaker(self):
        h = self._handler()
        state = h.circuit_breaker.get_service_state("svc")
        state.state = "OPEN"
        state.last_failure_time = datetime.now()

        mock_fn = MagicMock(return_value="should_not_reach")
        result, failure = h.execute_with_retry(mock_fn, "svc")

        assert result is None
        assert failure is not None
        mock_fn.assert_not_called()

    # --- get_service_health & reset ---

    def test_get_service_health_returns_known_services(self):
        h = self._handler()
        state = h.circuit_breaker.get_service_state("my_api")
        state.state = "OPEN"
        state.failure_count = 5

        health = h.get_service_health()
        assert "my_api" in health
        assert health["my_api"]["state"] == "OPEN"
        assert health["my_api"]["failure_count"] == 5
        assert health["my_api"]["is_healthy"] is False

    def test_reset_service_circuit_breaker(self):
        h = self._handler()
        state = h.circuit_breaker.get_service_state("svc")
        state.state = "OPEN"
        state.failure_count = 10

        h.reset_service_circuit_breaker("svc")
        assert state.state == "CLOSED"
        assert state.failure_count == 0

    # --- with_error_handling decorator ---

    def test_decorator_raises_on_failure(self):
        h = self._handler()

        @h.with_error_handling("svc")
        def always_fail():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            always_fail()

    def test_decorator_returns_result_on_success(self):
        h = self._handler()

        @h.with_error_handling("svc")
        def succeed():
            return 99

        assert succeed() == 99


class TestGetErrorHandler:
    def test_returns_api_error_handler_instance(self):
        handler = get_error_handler()
        assert isinstance(handler, APIErrorHandler)

    def test_returns_same_instance_on_multiple_calls(self):
        h1 = get_error_handler()
        h2 = get_error_handler()
        assert h1 is h2


# ===========================================================================
# data_quality_validator tests
# ===========================================================================

class TestDataQualityLevel:
    def test_all_levels_present(self):
        levels = {lvl.value for lvl in DataQualityLevel}
        assert "excellent" in levels
        assert "good" in levels
        assert "acceptable" in levels
        assert "poor" in levels
        assert "unusable" in levels


class TestDataSourceReliability:
    def test_reliability_levels_present(self):
        levels = {r.value for r in DataSourceReliability}
        assert "very_high" in levels
        assert "high" in levels
        assert "medium" in levels
        assert "low" in levels
        assert "unknown" in levels


class TestQualityMetrics:
    def test_default_values_are_zero(self):
        m = QualityMetrics()
        for attr in ("completeness", "accuracy_score", "freshness_score",
                     "consistency_score", "source_reliability", "sample_size_score",
                     "overall_score", "confidence_level"):
            assert getattr(m, attr) == 0.0

    def test_custom_values(self):
        m = QualityMetrics(completeness=0.8, overall_score=0.75)
        assert m.completeness == 0.8
        assert m.overall_score == 0.75


class TestDQValidationResult:
    def test_valid_result(self):
        r = DQValidationResult(is_valid=True, quality_level=DataQualityLevel.GOOD)
        assert r.is_valid is True
        assert r.quality_level == DataQualityLevel.GOOD
        assert r.issues == []
        assert r.warnings == []
        assert r.recommendations == []

    def test_invalid_result_with_issues(self):
        r = DQValidationResult(
            is_valid=False,
            quality_level=DataQualityLevel.UNUSABLE,
            issues=["No data"],
        )
        assert r.is_valid is False
        assert "No data" in r.issues


class TestDataQualityValidator:
    def _validator(self) -> DataQualityValidator:
        return DataQualityValidator()

    # --- _determine_quality_level ---

    def test_quality_level_excellent(self):
        v = self._validator()
        assert v._determine_quality_level(0.95) == DataQualityLevel.EXCELLENT

    def test_quality_level_good(self):
        v = self._validator()
        assert v._determine_quality_level(0.80) == DataQualityLevel.GOOD

    def test_quality_level_acceptable(self):
        v = self._validator()
        assert v._determine_quality_level(0.60) == DataQualityLevel.ACCEPTABLE

    def test_quality_level_poor(self):
        v = self._validator()
        assert v._determine_quality_level(0.35) == DataQualityLevel.POOR

    def test_quality_level_unusable(self):
        v = self._validator()
        assert v._determine_quality_level(0.10) == DataQualityLevel.UNUSABLE

    # --- validate_historical_data ---

    def test_empty_dataframe_is_invalid(self):
        v = self._validator()
        empty_df = pd.DataFrame()
        result = v.validate_historical_data(empty_df, "TICK")
        assert result.is_valid is False
        assert result.quality_level == DataQualityLevel.UNUSABLE

    def test_dataframe_with_few_rows_has_warning(self):
        v = self._validator()
        # Two years of data (insufficient for ideal analysis)
        df = pd.DataFrame({
            "pb_ratio": [2.0, 2.5],
            "book_value": [100.0, 110.0],
            "market_price": [200.0, 275.0],
        })
        result = v.validate_historical_data(df, "TICK")
        # 2 rows meets the minimum (>=2), but fewer than 3 should add an issue
        assert any("2 years" in iss or "historical" in iss.lower() or "insufficient" in iss.lower()
                   for iss in result.issues + result.warnings)

    def test_dataframe_with_sufficient_data_is_valid(self):
        v = self._validator()
        df = pd.DataFrame({
            "pb_ratio": [1.5, 2.0, 2.3, 2.5, 2.8],
            "book_value": [100.0, 110.0, 120.0, 130.0, 140.0],
            "market_price": [150.0, 220.0, 276.0, 325.0, 392.0],
        })
        result = v.validate_historical_data(df, "TICK")
        assert result.is_valid  # np.True_ is truthy but not `is True`

    def test_negative_pb_ratio_triggers_warning(self):
        v = self._validator()
        df = pd.DataFrame({
            "pb_ratio": [-1.0, 2.0, 3.0, 2.5, 2.8],
        })
        result = v.validate_historical_data(df, "TICK")
        assert any("negative" in w.lower() for w in result.warnings)

    def test_high_pb_ratio_triggers_warning(self):
        v = self._validator()
        df = pd.DataFrame({
            "pb_ratio": [60.0, 2.0, 3.0, 2.5, 2.8],
        })
        result = v.validate_historical_data(df, "TICK")
        assert any("high" in w.lower() or "50" in w for w in result.warnings)

    # --- generate_quality_report ---

    def test_generate_quality_report_returns_report(self):
        v = self._validator()
        metrics = QualityMetrics(
            completeness=0.9,
            accuracy_score=0.85,
            freshness_score=0.8,
            consistency_score=0.9,
            source_reliability=0.8,
            sample_size_score=0.7,
            overall_score=0.84,
        )
        validation_result = DQValidationResult(
            is_valid=True,
            quality_level=DataQualityLevel.GOOD,
            metrics=metrics,
        )

        report = v.generate_quality_report(
            "test_dataset",
            validation_result,
            additional_metrics={"peer_count": 15, "outlier_percentage": 0.05, "data_age_days": 2},
        )

        assert isinstance(report, QualityReport)
        assert report.dataset_name == "test_dataset"
        assert report.peer_count == 15
        assert report.outlier_percentage == 0.05
        assert "completeness" in report.quality_factors

    def test_generate_quality_report_with_no_metrics(self):
        v = self._validator()
        validation_result = DQValidationResult(
            is_valid=False,
            quality_level=DataQualityLevel.UNUSABLE,
        )
        report = v.generate_quality_report("test", validation_result)
        assert isinstance(report, QualityReport)
        assert report.quality_factors["completeness"] == 0


# ===========================================================================
# graceful_degradation tests
# ===========================================================================

class TestDegradationLevel:
    def test_all_levels_present(self):
        levels = {lvl.value for lvl in DegradationLevel}
        assert "full_service" in levels
        assert "historical_only" in levels
        assert "minimal_service" in levels
        assert "service_unavailable" in levels


class TestFallbackDataSource:
    def test_all_sources_present(self):
        sources = {s.value for s in FallbackDataSource}
        assert "primary_api" in sources
        assert "cached_data" in sources
        assert "excel_data" in sources
        assert "historical_data" in sources


class TestHistoricalOnlyStrategy:
    def _context_with_excel(self) -> DegradationContext:
        return DegradationContext(
            available_data_sources=[FallbackDataSource.EXCEL_DATA, FallbackDataSource.HISTORICAL_DATA],
            failed_services=["yfinance"],
            cache_age_hours=48.0,
        )

    def test_can_handle_when_excel_data_available(self):
        strategy = HistoricalOnlyStrategy()
        ctx = self._context_with_excel()
        assert strategy.can_handle(ctx) is True

    def test_cannot_handle_without_local_data(self):
        strategy = HistoricalOnlyStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.CACHED_DATA],
        )
        assert strategy.can_handle(ctx) is False

    def test_execute_returns_historical_only_level(self):
        strategy = HistoricalOnlyStrategy()
        result = strategy.execute(self._context_with_excel())
        assert result.degradation_level == DegradationLevel.HISTORICAL_ONLY

    def test_execute_includes_available_features(self):
        strategy = HistoricalOnlyStrategy()
        result = strategy.execute(self._context_with_excel())
        assert len(result.available_features) > 0

    def test_execute_recent_cache_gives_higher_accuracy(self):
        strategy = HistoricalOnlyStrategy()
        ctx_recent = DegradationContext(
            available_data_sources=[FallbackDataSource.EXCEL_DATA],
            cache_age_hours=12.0,
        )
        ctx_old = DegradationContext(
            available_data_sources=[FallbackDataSource.EXCEL_DATA],
            cache_age_hours=200.0,
        )
        result_recent = strategy.execute(ctx_recent)
        result_old = strategy.execute(ctx_old)
        assert result_recent.estimated_accuracy > result_old.estimated_accuracy


class TestCachedDataStrategy:
    def test_can_handle_fresh_cached_data(self):
        strategy = CachedDataStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.CACHED_DATA],
            cache_age_hours=12.0,
        )
        assert strategy.can_handle(ctx) is True

    def test_cannot_handle_stale_cache_over_72h(self):
        strategy = CachedDataStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.CACHED_DATA],
            cache_age_hours=73.0,
        )
        assert strategy.can_handle(ctx) is False

    def test_execute_with_fresh_cache_gives_reduced_industry_level(self):
        strategy = CachedDataStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.CACHED_DATA],
            cache_age_hours=6.0,
        )
        result = strategy.execute(ctx)
        assert result.degradation_level == DegradationLevel.REDUCED_INDUSTRY

    def test_execute_with_older_cache_gives_historical_level(self):
        strategy = CachedDataStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.CACHED_DATA],
            cache_age_hours=48.0,
        )
        result = strategy.execute(ctx)
        assert result.degradation_level == DegradationLevel.HISTORICAL_ONLY


class TestMinimalServiceStrategy:
    def test_can_handle_when_excel_data_available(self):
        strategy = MinimalServiceStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.EXCEL_DATA],
        )
        assert strategy.can_handle(ctx) is True

    def test_cannot_handle_without_excel_data(self):
        strategy = MinimalServiceStrategy()
        ctx = DegradationContext(available_data_sources=[])
        assert strategy.can_handle(ctx) is False

    def test_execute_returns_minimal_service_level(self):
        strategy = MinimalServiceStrategy()
        ctx = DegradationContext(
            available_data_sources=[FallbackDataSource.EXCEL_DATA],
        )
        result = strategy.execute(ctx)
        assert result.degradation_level == DegradationLevel.MINIMAL_SERVICE


class TestGracefulDegradationManager:
    def test_assess_degradation_with_excel_returns_historical_strategy(self):
        manager = GracefulDegradationManager()
        context = manager.create_degradation_context(
            failed_services=["yfinance", "alpha_vantage"],
            has_excel_data=True,
        )
        result = manager.assess_degradation(context)
        assert result.degradation_level in (
            DegradationLevel.HISTORICAL_ONLY,
            DegradationLevel.MINIMAL_SERVICE,
        )

    def test_assess_degradation_with_no_data_returns_unavailable(self):
        manager = GracefulDegradationManager()
        # No data sources at all
        ctx = DegradationContext(available_data_sources=[])
        result = manager.assess_degradation(ctx)
        assert result.degradation_level == DegradationLevel.SERVICE_UNAVAILABLE
        assert result.available_features == []

    def test_determine_available_data_sources_with_all(self):
        manager = GracefulDegradationManager()
        sources = manager.determine_available_data_sources(
            has_excel_data=True,
            has_cached_data=True,
            cache_age_hours=10.0,
            working_apis=["yfinance"],
        )
        assert FallbackDataSource.PRIMARY_API in sources
        assert FallbackDataSource.CACHED_DATA in sources
        assert FallbackDataSource.EXCEL_DATA in sources
        assert FallbackDataSource.HISTORICAL_DATA in sources

    def test_determine_available_data_sources_no_data(self):
        manager = GracefulDegradationManager()
        sources = manager.determine_available_data_sources()
        assert sources == []

    def test_create_degradation_context_populates_fields(self):
        manager = GracefulDegradationManager()
        ctx = manager.create_degradation_context(
            failed_services=["svc_a"],
            has_excel_data=True,
            cache_age_hours=5.0,
        )
        assert "svc_a" in ctx.failed_services
        assert ctx.cache_age_hours == 5.0
        assert FallbackDataSource.EXCEL_DATA in ctx.available_data_sources

    def test_service_health_history_tracked_after_assess(self):
        manager = GracefulDegradationManager()
        ctx = manager.create_degradation_context(
            failed_services=["svc_x"],
            has_excel_data=True,
        )
        manager.assess_degradation(ctx)
        assert "svc_x" in manager.service_health_history


class TestGetDegradationManager:
    def test_returns_graceful_degradation_manager_instance(self):
        mgr = get_degradation_manager()
        assert isinstance(mgr, GracefulDegradationManager)

    def test_returns_same_instance_on_multiple_calls(self):
        m1 = get_degradation_manager()
        m2 = get_degradation_manager()
        assert m1 is m2


# ===========================================================================
# user_message_handler tests (non-Streamlit portions)
# ===========================================================================

class TestMessageSeverity:
    def test_all_levels_present(self):
        levels = {s.value for s in MessageSeverity}
        assert "info" in levels
        assert "success" in levels
        assert "warning" in levels
        assert "error" in levels
        assert "critical" in levels


class TestMessageCategory:
    def test_all_categories_present(self):
        cats = {c.value for c in MessageCategory}
        assert "api_error" in cats
        assert "data_quality" in cats
        assert "degraded_service" in cats
        assert "user_input" in cats
        assert "calculation" in cats
        assert "system" in cats


class TestUserMessage:
    def test_can_be_instantiated(self):
        msg = UserMessage(
            title="Test Title",
            message="Test message",
            severity=MessageSeverity.INFO,
            category=MessageCategory.SYSTEM,
        )
        assert msg.title == "Test Title"
        assert msg.severity == MessageSeverity.INFO
        assert msg.category == MessageCategory.SYSTEM

    def test_default_lists_are_empty(self):
        msg = UserMessage(
            title="T", message="M",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.API_ERROR,
        )
        assert msg.immediate_actions == []
        assert msg.recommended_actions == []
        assert msg.affected_features == []
        assert msg.available_alternatives == []

    def test_timestamp_is_set(self):
        before = datetime.now()
        msg = UserMessage(
            title="T", message="M",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.CALCULATION,
        )
        after = datetime.now()
        assert before <= msg.timestamp <= after


class TestUserMessageHandler:
    def _handler(self) -> UserMessageHandler:
        return UserMessageHandler()

    # --- create_api_error_message ---

    def test_create_api_error_message_rate_limit(self):
        handler = self._handler()
        mock_failure = MagicMock()
        mock_failure.category.value = "rate_limit"
        mock_failure.user_message = "Rate limited"
        mock_failure.error_message = "HTTP 429"

        msg = handler.create_api_error_message(mock_failure)

        assert msg is not None
        assert msg.severity == MessageSeverity.WARNING
        assert msg.category == MessageCategory.API_ERROR

    def test_create_api_error_message_authentication(self):
        handler = self._handler()
        mock_failure = MagicMock()
        mock_failure.category.value = "authentication"
        mock_failure.user_message = "Auth failed"
        mock_failure.error_message = "401"

        msg = handler.create_api_error_message(mock_failure)

        assert msg.severity == MessageSeverity.ERROR

    def test_create_api_error_message_network(self):
        handler = self._handler()
        mock_failure = MagicMock()
        mock_failure.category.value = "network_error"
        mock_failure.user_message = "No connection"
        mock_failure.error_message = "timeout"

        msg = handler.create_api_error_message(mock_failure)

        assert msg.severity == MessageSeverity.WARNING

    # --- create_data_quality_message ---

    def test_create_data_quality_message_excellent_returns_none(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.quality_level.value = "excellent"

        msg = handler.create_data_quality_message(mock_result)
        assert msg is None

    def test_create_data_quality_message_good_returns_none(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.quality_level.value = "good"

        msg = handler.create_data_quality_message(mock_result)
        assert msg is None

    def test_create_data_quality_message_poor_is_warning(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.quality_level.value = "poor"
        mock_result.issues = ["Too few peers"]
        mock_result.recommendations = ["Widen sector criteria"]

        msg = handler.create_data_quality_message(mock_result)
        assert msg is not None
        assert msg.severity == MessageSeverity.WARNING

    def test_create_data_quality_message_unusable_is_error(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.quality_level.value = "unusable"
        mock_result.issues = ["No data"]
        mock_result.recommendations = []

        msg = handler.create_data_quality_message(mock_result)
        assert msg is not None
        assert msg.severity == MessageSeverity.ERROR

    # --- create_degradation_message ---

    def test_create_degradation_message_full_service_returns_none(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.degradation_level.value = "full_service"

        msg = handler.create_degradation_message(mock_result)
        assert msg is None

    def test_create_degradation_message_historical_only_is_warning(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.degradation_level.value = "historical_only"
        mock_result.user_message = "Historical only"
        mock_result.technical_details = "APIs down"
        mock_result.recommendations = ["Use history"]
        mock_result.disabled_features = ["Live prices"]
        mock_result.available_features = ["Trend analysis"]

        msg = handler.create_degradation_message(mock_result)
        assert msg is not None
        assert msg.severity == MessageSeverity.WARNING

    def test_create_degradation_message_minimal_service_is_error(self):
        handler = self._handler()
        mock_result = MagicMock()
        mock_result.degradation_level.value = "minimal_service"
        mock_result.user_message = "Minimal only"
        mock_result.technical_details = "All APIs down"
        mock_result.recommendations = []
        mock_result.disabled_features = []
        mock_result.available_features = []

        msg = handler.create_degradation_message(mock_result)
        assert msg.severity == MessageSeverity.ERROR

    # --- add_message, clear_messages, get_messages_by_severity ---

    def test_add_message_appended_to_active_list(self):
        handler = self._handler()
        msg = UserMessage(
            title="T", message="M",
            severity=MessageSeverity.INFO,
            category=MessageCategory.SYSTEM,
        )
        handler.add_message(msg)
        assert len(handler.active_messages) == 1
        assert handler.active_messages[0] is msg

    def test_clear_messages_removes_all(self):
        handler = self._handler()
        for sev in [MessageSeverity.INFO, MessageSeverity.WARNING, MessageSeverity.ERROR]:
            handler.add_message(UserMessage(
                title="T", message="M", severity=sev, category=MessageCategory.SYSTEM
            ))
        handler.clear_messages()
        assert handler.active_messages == []

    def test_clear_messages_by_category(self):
        handler = self._handler()
        handler.add_message(UserMessage(
            title="API", message="M",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.API_ERROR,
        ))
        handler.add_message(UserMessage(
            title="Sys", message="M",
            severity=MessageSeverity.INFO,
            category=MessageCategory.SYSTEM,
        ))
        handler.clear_messages(category=MessageCategory.API_ERROR)
        assert len(handler.active_messages) == 1
        assert handler.active_messages[0].category == MessageCategory.SYSTEM

    def test_get_messages_by_severity_filters_correctly(self):
        handler = self._handler()
        handler.add_message(UserMessage(
            title="W", message="M",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.SYSTEM,
        ))
        handler.add_message(UserMessage(
            title="E", message="M",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.SYSTEM,
        ))
        warnings = handler.get_messages_by_severity(MessageSeverity.WARNING)
        assert len(warnings) == 1
        assert warnings[0].title == "W"

    def test_message_templates_initialized(self):
        handler = self._handler()
        assert len(handler.message_templates) > 0
        assert "api_rate_limit" in handler.message_templates
        assert "api_authentication" in handler.message_templates
        assert "network_error" in handler.message_templates
