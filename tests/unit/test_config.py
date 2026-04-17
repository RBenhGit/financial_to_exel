"""
Unit Tests for Configuration Modules
======================================

Tests cover:
- config/constants.py: Authoritative constant values
- config/settings.py: ApiConfig defaults, environment variable overrides,
  EnvironmentSettings factory methods, SettingsManager, helper functions
"""

import os
import sys
import pytest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import constants
from config.settings import (
    ApiConfig,
    CacheConfig,
    LoggingConfig,
    DatabaseConfig,
    SecurityConfig,
    PerformanceConfig,
    EnvironmentSettings,
    Environment,
    SettingsManager,
    get_settings,
    get_api_config,
    get_cache_config,
    get_logging_config,
    get_database_config,
    get_security_config,
    get_performance_config,
    is_development,
    is_testing,
    is_production,
    get_current_environment,
    validate_settings,
    update_setting,
    get_setting,
)


# ===========================================================================
# constants.py — authoritative values
# ===========================================================================

class TestFinancialCalculationConstants:
    def test_default_projection_years_is_10(self):
        assert constants.DEFAULT_PROJECTION_YEARS == 10

    def test_default_discount_rate_is_0_10(self):
        assert constants.DEFAULT_DISCOUNT_RATE == pytest.approx(0.10)

    def test_default_terminal_growth_rate_is_0_025(self):
        assert constants.DEFAULT_TERMINAL_GROWTH_RATE == pytest.approx(0.025)


class TestAPIConstants:
    def test_api_retry_attempts_is_3(self):
        assert constants.API_RETRY_ATTEMPTS == 3

    def test_default_rate_limit_delay_is_1_0(self):
        assert constants.DEFAULT_RATE_LIMIT_DELAY == pytest.approx(1.0)


class TestDataQualityConstants:
    def test_min_data_completeness_ratio_is_0_7(self):
        assert constants.MIN_DATA_COMPLETENESS_RATIO == pytest.approx(0.7)

    def test_max_outlier_standard_deviations_is_3(self):
        assert constants.MAX_OUTLIER_STANDARD_DEVIATIONS == pytest.approx(3.0)


class TestHTTPStatusCodes:
    def test_http_ok_is_200(self):
        assert constants.HTTP_OK == 200

    def test_http_not_found_is_404(self):
        assert constants.HTTP_NOT_FOUND == 404

    def test_http_rate_limited_is_429(self):
        assert constants.HTTP_RATE_LIMITED == 429

    def test_http_server_error_is_500(self):
        assert constants.HTTP_SERVER_ERROR == 500


class TestGrowthRateBounds:
    def test_min_discount_rate(self):
        assert constants.MIN_DISCOUNT_RATE == pytest.approx(0.01)

    def test_max_discount_rate(self):
        assert constants.MAX_DISCOUNT_RATE == pytest.approx(0.50)

    def test_min_growth_rate(self):
        assert constants.MIN_GROWTH_RATE == pytest.approx(-0.10)

    def test_max_growth_rate(self):
        assert constants.MAX_GROWTH_RATE == pytest.approx(0.30)


class TestCacheTTLConstants:
    def test_default_cache_ttl_is_24_hours(self):
        assert constants.DEFAULT_CACHE_TTL == 24 * 3600

    def test_price_cache_ttl_is_15_minutes(self):
        assert constants.PRICE_CACHE_TTL == 15 * 60

    def test_financial_data_cache_ttl_is_6_hours(self):
        assert constants.FINANCIAL_DATA_CACHE_TTL == 6 * 3600


class TestEnvironmentVariableNames:
    def test_alpha_vantage_env_var_name(self):
        assert constants.ENV_ALPHA_VANTAGE_KEY == "ALPHA_VANTAGE_API_KEY"

    def test_fmp_env_var_name(self):
        assert constants.ENV_FMP_KEY == "FMP_API_KEY"

    def test_polygon_env_var_name(self):
        assert constants.ENV_POLYGON_KEY == "POLYGON_API_KEY"


class TestRetryConstants:
    def test_max_retry_attempts(self):
        assert constants.MAX_RETRY_ATTEMPTS == 3

    def test_initial_retry_delay(self):
        assert constants.INITIAL_RETRY_DELAY == pytest.approx(1.0)

    def test_max_retry_delay(self):
        assert constants.MAX_RETRY_DELAY == pytest.approx(60.0)


class TestExcelConstants:
    def test_excel_extensions(self):
        assert ".xlsx" in constants.EXCEL_EXTENSIONS
        assert ".xls" in constants.EXCEL_EXTENSIONS

    def test_default_header_row(self):
        assert constants.DEFAULT_HEADER_ROW == 1

    def test_default_data_start_row(self):
        assert constants.DEFAULT_DATA_START_ROW == 2


class TestStatisticalConstants:
    def test_confidence_95_percent(self):
        assert constants.CONFIDENCE_95_PERCENT == pytest.approx(0.95)

    def test_z_score_95_percent(self):
        assert constants.Z_SCORE_95_PERCENT == pytest.approx(1.96)

    def test_min_sample_size(self):
        assert constants.MIN_SAMPLE_SIZE == 5


# ===========================================================================
# settings.py — ApiConfig defaults and env overrides
# ===========================================================================

class TestApiConfigDefaults:
    """ApiConfig must be instantiable with no arguments and carry sensible defaults."""

    def test_can_be_instantiated_with_no_args(self):
        cfg = ApiConfig()
        assert cfg is not None

    def test_network_timeout_default(self):
        cfg = ApiConfig()
        # Uses DEFAULT_NETWORK_TIMEOUT from constants
        assert cfg.network_timeout == pytest.approx(constants.DEFAULT_NETWORK_TIMEOUT)

    def test_api_timeout_default(self):
        cfg = ApiConfig()
        assert cfg.api_timeout == pytest.approx(constants.DEFAULT_API_TIMEOUT)

    def test_circuit_breaker_enabled_by_default(self):
        cfg = ApiConfig()
        assert cfg.circuit_breaker_enabled is True

    def test_jitter_enabled_by_default(self):
        cfg = ApiConfig()
        assert cfg.jitter_enabled is True

    def test_alpha_vantage_url_matches_constant(self):
        cfg = ApiConfig()
        assert cfg.alpha_vantage_url == constants.ALPHA_VANTAGE_BASE_URL

    def test_fmp_url_matches_constant(self):
        cfg = ApiConfig()
        assert cfg.fmp_url == constants.FMP_BASE_URL

    def test_polygon_url_matches_constant(self):
        cfg = ApiConfig()
        assert cfg.polygon_url == constants.POLYGON_BASE_URL


class TestApiConfigEnvVarOverrides:
    """ApiConfig reads API keys from environment variables via __post_init__."""

    def test_alpha_vantage_key_read_from_env(self):
        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "av_test_key_123"}):
            cfg = ApiConfig()
        assert cfg.alpha_vantage_key == "av_test_key_123"

    def test_fmp_key_read_from_env(self):
        with patch.dict(os.environ, {"FMP_API_KEY": "fmp_test_key_456"}):
            cfg = ApiConfig()
        assert cfg.fmp_key == "fmp_test_key_456"

    def test_polygon_key_read_from_env(self):
        with patch.dict(os.environ, {"POLYGON_API_KEY": "poly_test_key_789"}):
            cfg = ApiConfig()
        assert cfg.polygon_key == "poly_test_key_789"

    def test_keys_are_none_when_env_not_set(self):
        env_without_keys = {k: v for k, v in os.environ.items()
                            if k not in {"ALPHA_VANTAGE_API_KEY", "FMP_API_KEY", "POLYGON_API_KEY"}}
        with patch.dict(os.environ, env_without_keys, clear=True):
            cfg = ApiConfig()
        assert cfg.alpha_vantage_key is None
        assert cfg.fmp_key is None
        assert cfg.polygon_key is None

    def test_multiple_keys_simultaneously(self):
        env_vars = {
            "ALPHA_VANTAGE_API_KEY": "av_multi",
            "FMP_API_KEY": "fmp_multi",
            "POLYGON_API_KEY": "poly_multi",
        }
        with patch.dict(os.environ, env_vars):
            cfg = ApiConfig()
        assert cfg.alpha_vantage_key == "av_multi"
        assert cfg.fmp_key == "fmp_multi"
        assert cfg.polygon_key == "poly_multi"


class TestCacheConfigDefaults:
    def test_can_be_instantiated(self):
        cfg = CacheConfig()
        assert cfg is not None

    def test_cache_enabled_by_default(self):
        cfg = CacheConfig()
        assert cfg.enabled is True

    def test_default_cache_dir(self):
        cfg = CacheConfig()
        assert cfg.cache_dir == constants.DEFAULT_CACHE_DIR

    def test_cache_dir_overridden_by_env(self):
        with patch.dict(os.environ, {"FINANCIAL_ANALYSIS_CACHE_DIR": "/custom/cache"}):
            cfg = CacheConfig()
        assert cfg.cache_dir == "/custom/cache"


class TestLoggingConfigDefaults:
    def test_can_be_instantiated(self):
        cfg = LoggingConfig()
        assert cfg is not None

    def test_default_log_level(self):
        cfg = LoggingConfig()
        assert cfg.log_level == constants.LOG_LEVEL_INFO

    def test_log_level_overridden_by_env(self):
        with patch.dict(os.environ, {"FINANCIAL_ANALYSIS_LOG_LEVEL": "debug"}):
            cfg = LoggingConfig()
        assert cfg.log_level == "DEBUG"


class TestEnvironmentSettingsFactories:
    """Test factory classmethods that create environment-specific settings."""

    def test_for_development_sets_debug_logging(self):
        settings = EnvironmentSettings.for_development()
        assert settings.logging.log_level == "DEBUG"
        assert settings.environment == Environment.DEVELOPMENT

    def test_for_development_enables_experimental_features(self):
        settings = EnvironmentSettings.for_development()
        assert settings.enable_experimental_features is True

    def test_for_testing_disables_cache(self):
        settings = EnvironmentSettings.for_testing()
        assert settings.cache.enabled is False
        assert settings.environment == Environment.TESTING

    def test_for_testing_disables_file_logging(self):
        settings = EnvironmentSettings.for_testing()
        assert settings.logging.file_logging is False

    def test_for_testing_has_faster_timeouts(self):
        settings = EnvironmentSettings.for_testing()
        dev_settings = EnvironmentSettings.for_development()
        assert settings.api.network_timeout <= dev_settings.api.network_timeout

    def test_for_production_disables_console_logging(self):
        settings = EnvironmentSettings.for_production()
        assert settings.logging.console_logging is False
        assert settings.environment == Environment.PRODUCTION

    def test_for_production_enables_strict_validation(self):
        settings = EnvironmentSettings.for_production()
        assert settings.security.strict_validation is True

    def test_for_production_disables_experimental_features(self):
        settings = EnvironmentSettings.for_production()
        assert settings.enable_experimental_features is False

    def test_default_instantiation_creates_api_config(self):
        settings = EnvironmentSettings()
        assert isinstance(settings.api, ApiConfig)

    def test_default_instantiation_creates_cache_config(self):
        settings = EnvironmentSettings()
        assert isinstance(settings.cache, CacheConfig)


class TestSettingsManagerSingleton:
    """SettingsManager uses singleton pattern; resetting _instance enables isolation."""

    def _reset_singleton(self):
        """Reset the singleton so each test gets a fresh instance."""
        SettingsManager._instance = None
        SettingsManager._settings = None

    def test_returns_same_instance(self):
        sm1 = SettingsManager()
        sm2 = SettingsManager()
        assert sm1 is sm2

    def test_get_settings_returns_environment_settings(self):
        sm = SettingsManager()
        settings = sm.get_settings()
        assert isinstance(settings, EnvironmentSettings)

    def test_loads_development_settings_by_default(self):
        self._reset_singleton()
        env = {k: v for k, v in os.environ.items() if k != "FINANCIAL_ANALYSIS_ENV"}
        with patch.dict(os.environ, env, clear=True):
            sm = SettingsManager()
        settings = sm.get_settings()
        assert settings.environment == Environment.DEVELOPMENT

    def test_loads_testing_settings_from_env(self):
        self._reset_singleton()
        with patch.dict(os.environ, {"FINANCIAL_ANALYSIS_ENV": "testing"}):
            sm = SettingsManager()
        settings = sm.get_settings()
        assert settings.environment == Environment.TESTING

    def test_loads_production_settings_from_env(self):
        self._reset_singleton()
        with patch.dict(os.environ, {"FINANCIAL_ANALYSIS_ENV": "production"}):
            sm = SettingsManager()
        settings = sm.get_settings()
        assert settings.environment == Environment.PRODUCTION

    def test_update_and_get_setting_round_trip(self):
        sm = SettingsManager()
        # Update a numeric setting and verify it was applied
        sm.update_setting("api.network_timeout", 99.0)
        assert sm.get_setting("api.network_timeout") == pytest.approx(99.0)

    def test_invalid_setting_path_raises_value_error(self):
        sm = SettingsManager()
        with pytest.raises(ValueError):
            sm.get_setting("nonexistent.path.deeply.nested")

    def test_validate_settings_returns_dict_with_errors_and_warnings(self):
        sm = SettingsManager()
        result = sm.validate_settings()
        assert isinstance(result, dict)
        assert "errors" in result
        assert "warnings" in result


class TestHelperFunctions:
    """Test module-level convenience functions that delegate to SettingsManager."""

    def test_get_settings_returns_environment_settings(self):
        settings = get_settings()
        assert isinstance(settings, EnvironmentSettings)

    def test_get_api_config_returns_api_config(self):
        cfg = get_api_config()
        assert isinstance(cfg, ApiConfig)

    def test_get_cache_config_returns_cache_config(self):
        cfg = get_cache_config()
        assert isinstance(cfg, CacheConfig)

    def test_get_logging_config_returns_logging_config(self):
        cfg = get_logging_config()
        assert isinstance(cfg, LoggingConfig)

    def test_get_database_config_returns_database_config(self):
        cfg = get_database_config()
        assert isinstance(cfg, DatabaseConfig)

    def test_get_security_config_returns_security_config(self):
        cfg = get_security_config()
        assert isinstance(cfg, SecurityConfig)

    def test_get_performance_config_returns_performance_config(self):
        cfg = get_performance_config()
        assert isinstance(cfg, PerformanceConfig)

    def test_validate_settings_returns_dict(self):
        result = validate_settings()
        assert isinstance(result, dict)
        assert "errors" in result and "warnings" in result

    def test_get_current_environment_returns_string(self):
        env = get_current_environment()
        assert isinstance(env, str)
        assert env in ("development", "testing", "production")

    def test_exactly_one_environment_flag_is_true(self):
        # Exactly one of is_development / is_testing / is_production should be True
        flags = [is_development(), is_testing(), is_production()]
        assert sum(flags) == 1

    def test_update_setting_and_get_setting(self):
        # Round-trip: update then read back
        update_setting("api.rate_limit_delay", 7.5)
        assert get_setting("api.rate_limit_delay") == pytest.approx(7.5)


class TestDatabaseConfig:
    def test_get_db_path_combines_dir_and_filename(self):
        cfg = DatabaseConfig(db_dir="custom_dir", watch_lists_db="lists.db")
        path = cfg.get_db_path()
        assert "custom_dir" in str(path)
        assert "lists.db" in str(path)


class TestSecurityConfigDefaults:
    def test_can_be_instantiated(self):
        cfg = SecurityConfig()
        assert cfg is not None

    def test_allowed_extensions_include_xlsx(self):
        cfg = SecurityConfig()
        assert ".xlsx" in cfg.allowed_extensions

    def test_hide_api_keys_in_logs_default(self):
        cfg = SecurityConfig()
        assert cfg.hide_api_keys_in_logs is True
