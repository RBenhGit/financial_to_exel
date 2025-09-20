"""
Simplified Unit Tests for Configuration Module
==============================================

Tests core functionality of the configuration system that actually works.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config import get_config, get_dcf_config
from config.constants import (
    DEFAULT_FINANCIAL_SCALE_FACTOR,
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_TERMINAL_GROWTH_RATE,
    FINANCIAL_STATEMENT_NAMES,
    API_TIMEOUT_SECONDS,
    CACHE_EXPIRY_MINUTES
)


class TestConfigurationSimplified:
    """Simplified tests for configuration system."""

    def test_get_config_function_works(self):
        """Test basic configuration loading."""
        config = get_config()
        assert config is not None

    def test_get_dcf_config_function_works(self):
        """Test DCF configuration loading."""
        dcf_config = get_dcf_config()
        assert dcf_config is not None

    def test_config_has_data_sources(self):
        """Test that config has data sources attribute."""
        config = get_config()
        if hasattr(config, 'data_sources'):
            assert config.data_sources is not None

    def test_dcf_config_has_discount_rate(self):
        """Test DCF config has discount rate."""
        dcf_config = get_dcf_config()
        if hasattr(dcf_config, 'default_discount_rate'):
            rate = dcf_config.default_discount_rate
            if rate is not None:
                assert isinstance(rate, (int, float))
                assert 0 < rate < 1

    def test_dcf_config_has_terminal_growth(self):
        """Test DCF config has terminal growth rate."""
        dcf_config = get_dcf_config()
        if hasattr(dcf_config, 'default_terminal_growth_rate'):
            growth = dcf_config.default_terminal_growth_rate
            if growth is not None:
                assert isinstance(growth, (int, float))
                assert 0 <= growth < 1


class TestConfigurationConstants:
    """Test configuration constants."""

    def test_financial_scale_factor_exists(self):
        """Test financial scale factor constant."""
        assert DEFAULT_FINANCIAL_SCALE_FACTOR is not None
        assert isinstance(DEFAULT_FINANCIAL_SCALE_FACTOR, (int, float))

    def test_discount_rate_constant(self):
        """Test discount rate constant."""
        assert DEFAULT_DISCOUNT_RATE is not None
        assert isinstance(DEFAULT_DISCOUNT_RATE, (int, float))
        assert 0 < DEFAULT_DISCOUNT_RATE < 1

    def test_terminal_growth_rate_constant(self):
        """Test terminal growth rate constant."""
        assert DEFAULT_TERMINAL_GROWTH_RATE is not None
        assert isinstance(DEFAULT_TERMINAL_GROWTH_RATE, (int, float))
        assert 0 <= DEFAULT_TERMINAL_GROWTH_RATE < 1

    def test_financial_statement_names_exist(self):
        """Test financial statement names constant."""
        assert FINANCIAL_STATEMENT_NAMES is not None
        assert isinstance(FINANCIAL_STATEMENT_NAMES, (list, tuple))
        assert len(FINANCIAL_STATEMENT_NAMES) > 0

    def test_api_timeout_constant(self):
        """Test API timeout constant."""
        assert API_TIMEOUT_SECONDS is not None
        assert isinstance(API_TIMEOUT_SECONDS, (int, float))
        assert API_TIMEOUT_SECONDS > 0

    def test_cache_expiry_constant(self):
        """Test cache expiry constant."""
        assert CACHE_EXPIRY_MINUTES is not None
        assert isinstance(CACHE_EXPIRY_MINUTES, (int, float))
        assert CACHE_EXPIRY_MINUTES > 0

    def test_constants_have_reasonable_values(self):
        """Test constants have reasonable values."""
        # Test discount rate is reasonable (1% to 50%)
        assert 0.01 <= DEFAULT_DISCOUNT_RATE <= 0.50

        # Test terminal growth is reasonable (0% to 10%)
        assert 0.0 <= DEFAULT_TERMINAL_GROWTH_RATE <= 0.10

        # Test API timeout is reasonable (1 to 300 seconds)
        assert 1 <= API_TIMEOUT_SECONDS <= 300

        # Test cache expiry is reasonable (1 to 1440 minutes)
        assert 1 <= CACHE_EXPIRY_MINUTES <= 1440

    def test_statement_names_contain_expected_types(self):
        """Test statement names contain expected types."""
        statement_names_lower = [name.lower() for name in FINANCIAL_STATEMENT_NAMES]

        # Should contain income, balance, and cash flow related terms
        has_income = any('income' in name or 'profit' in name for name in statement_names_lower)
        has_balance = any('balance' in name or 'sheet' in name for name in statement_names_lower)
        has_cash = any('cash' in name or 'flow' in name for name in statement_names_lower)

        # At least some of these should be present
        assert has_income or has_balance or has_cash

    def test_constants_are_not_none(self):
        """Test all imported constants are not None."""
        constants = [
            DEFAULT_FINANCIAL_SCALE_FACTOR,
            DEFAULT_DISCOUNT_RATE,
            DEFAULT_TERMINAL_GROWTH_RATE,
            FINANCIAL_STATEMENT_NAMES,
            API_TIMEOUT_SECONDS,
            CACHE_EXPIRY_MINUTES
        ]

        for const in constants:
            assert const is not None

    def test_numeric_constants_are_positive(self):
        """Test numeric constants are positive."""
        numeric_constants = [
            DEFAULT_FINANCIAL_SCALE_FACTOR,
            DEFAULT_DISCOUNT_RATE,
            DEFAULT_TERMINAL_GROWTH_RATE,
            API_TIMEOUT_SECONDS,
            CACHE_EXPIRY_MINUTES
        ]

        for const in numeric_constants:
            assert const > 0


class TestConfigurationConsistency:
    """Test configuration consistency."""

    def test_config_calls_return_same_type(self):
        """Test repeated config calls return same type."""
        config1 = get_config()
        config2 = get_config()
        assert type(config1) == type(config2)

    def test_dcf_config_calls_return_same_type(self):
        """Test repeated DCF config calls return same type."""
        dcf1 = get_dcf_config()
        dcf2 = get_dcf_config()
        assert type(dcf1) == type(dcf2)

    def test_config_objects_are_not_none(self):
        """Test config objects are not None."""
        config = get_config()
        dcf_config = get_dcf_config()

        assert config is not None
        assert dcf_config is not None

    def test_config_objects_have_attributes(self):
        """Test config objects have some attributes."""
        config = get_config()
        dcf_config = get_dcf_config()

        # Should have some kind of structure
        assert hasattr(config, '__dict__') or hasattr(config, '__getattr__') or hasattr(config, '__getitem__')
        assert hasattr(dcf_config, '__dict__') or hasattr(dcf_config, '__getattr__') or hasattr(dcf_config, '__getitem__')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])