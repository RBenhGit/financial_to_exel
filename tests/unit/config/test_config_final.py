"""
Final Unit Tests for Configuration Module
=========================================

Tests core functionality of the configuration system with actual existing constants.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config import get_config, get_dcf_config
from config.constants import (
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_API_TIMEOUT,
    API_RETRY_ATTEMPTS,
    MIN_DATA_COMPLETENESS_RATIO,
    DEFAULT_DECIMAL_PLACES,
    FINANCIAL_PRECISION,
    MIN_VALID_YEAR,
    MAX_VALID_YEAR
)


class TestConfigurationFunctions:
    """Test configuration loading functions."""

    def test_get_config_function_exists(self):
        """Test get_config function exists and returns something."""
        config = get_config()
        assert config is not None

    def test_get_dcf_config_function_exists(self):
        """Test get_dcf_config function exists and returns something."""
        dcf_config = get_dcf_config()
        assert dcf_config is not None

    def test_config_is_callable(self):
        """Test that config functions are callable."""
        assert callable(get_config)
        assert callable(get_dcf_config)

    def test_config_returns_object(self):
        """Test that config returns object-like structure."""
        config = get_config()
        # Should be some kind of object with attributes or dict-like access
        assert hasattr(config, '__dict__') or hasattr(config, '__getitem__') or hasattr(config, '__getattr__')

    def test_dcf_config_returns_object(self):
        """Test that DCF config returns object-like structure."""
        dcf_config = get_dcf_config()
        assert hasattr(dcf_config, '__dict__') or hasattr(dcf_config, '__getitem__') or hasattr(dcf_config, '__getattr__')


class TestConfigurationConstants:
    """Test configuration constants that actually exist."""

    def test_timeout_constants_exist(self):
        """Test timeout-related constants exist and are reasonable."""
        assert DEFAULT_NETWORK_TIMEOUT is not None
        assert isinstance(DEFAULT_NETWORK_TIMEOUT, (int, float))
        assert DEFAULT_NETWORK_TIMEOUT > 0

        assert DEFAULT_API_TIMEOUT is not None
        assert isinstance(DEFAULT_API_TIMEOUT, (int, float))
        assert DEFAULT_API_TIMEOUT > 0

    def test_retry_constants(self):
        """Test retry-related constants."""
        assert API_RETRY_ATTEMPTS is not None
        assert isinstance(API_RETRY_ATTEMPTS, int)
        assert API_RETRY_ATTEMPTS > 0

    def test_data_quality_constants(self):
        """Test data quality constants."""
        assert MIN_DATA_COMPLETENESS_RATIO is not None
        assert isinstance(MIN_DATA_COMPLETENESS_RATIO, (int, float))
        assert 0 <= MIN_DATA_COMPLETENESS_RATIO <= 1

    def test_precision_constants(self):
        """Test precision-related constants."""
        assert DEFAULT_DECIMAL_PLACES is not None
        assert isinstance(DEFAULT_DECIMAL_PLACES, int)
        assert DEFAULT_DECIMAL_PLACES >= 0

        assert FINANCIAL_PRECISION is not None
        assert isinstance(FINANCIAL_PRECISION, int)
        assert FINANCIAL_PRECISION >= 0

    def test_year_validation_constants(self):
        """Test year validation constants."""
        assert MIN_VALID_YEAR is not None
        assert isinstance(MIN_VALID_YEAR, int)
        assert MIN_VALID_YEAR > 1800  # Should be reasonable

        assert MAX_VALID_YEAR is not None
        assert isinstance(MAX_VALID_YEAR, int)
        assert MAX_VALID_YEAR > MIN_VALID_YEAR
        assert MAX_VALID_YEAR < 2200  # Should be reasonable

    def test_constants_reasonable_values(self):
        """Test that constants have reasonable values."""
        # Network timeout should be 1-300 seconds
        assert 1 <= DEFAULT_NETWORK_TIMEOUT <= 300

        # API timeout should be 1-60 seconds
        assert 1 <= DEFAULT_API_TIMEOUT <= 60

        # Retry attempts should be 1-10
        assert 1 <= API_RETRY_ATTEMPTS <= 10

        # Data completeness should be between 50%-95%
        assert 0.5 <= MIN_DATA_COMPLETENESS_RATIO <= 0.95

        # Decimal places should be reasonable
        assert 0 <= DEFAULT_DECIMAL_PLACES <= 10
        assert 0 <= FINANCIAL_PRECISION <= 10

    def test_all_constants_not_none(self):
        """Test that all imported constants are not None."""
        constants = [
            DEFAULT_NETWORK_TIMEOUT,
            DEFAULT_API_TIMEOUT,
            API_RETRY_ATTEMPTS,
            MIN_DATA_COMPLETENESS_RATIO,
            DEFAULT_DECIMAL_PLACES,
            FINANCIAL_PRECISION,
            MIN_VALID_YEAR,
            MAX_VALID_YEAR
        ]

        for const in constants:
            assert const is not None


class TestConfigurationBehavior:
    """Test configuration behavior."""

    def test_repeated_config_calls_consistent(self):
        """Test that repeated calls return consistent types."""
        config1 = get_config()
        config2 = get_config()

        # Should return same type
        assert type(config1) == type(config2)

    def test_repeated_dcf_calls_consistent(self):
        """Test that repeated DCF calls return consistent types."""
        dcf1 = get_dcf_config()
        dcf2 = get_dcf_config()

        # Should return same type
        assert type(dcf1) == type(dcf2)

    def test_config_not_none(self):
        """Test that configs are not None."""
        config = get_config()
        dcf_config = get_dcf_config()

        assert config is not None
        assert dcf_config is not None

    def test_config_attribute_access(self):
        """Test configuration attribute access patterns."""
        config = get_config()

        # Try accessing data_sources if it exists
        if hasattr(config, 'data_sources'):
            data_sources = config.data_sources
            # Should not crash and return something
            assert data_sources is not None or data_sources == {} or data_sources == []

    def test_dcf_config_attribute_access(self):
        """Test DCF configuration attribute access."""
        dcf_config = get_dcf_config()

        # Try accessing common DCF attributes if they exist
        common_attrs = ['default_discount_rate', 'default_terminal_growth_rate', 'discount_rate', 'growth_rate']

        for attr in common_attrs:
            if hasattr(dcf_config, attr):
                value = getattr(dcf_config, attr)
                # Should be a number if it exists
                if value is not None:
                    assert isinstance(value, (int, float))


class TestConfigurationIntegration:
    """Test configuration integration."""

    def test_config_can_be_imported(self):
        """Test that config modules can be imported without errors."""
        # If we got here, imports worked
        assert True

    def test_constants_module_accessible(self):
        """Test that constants module is accessible."""
        # Test that we can access constants
        timeout = DEFAULT_NETWORK_TIMEOUT
        assert timeout is not None

    def test_config_functions_work_without_errors(self):
        """Test that config functions work without throwing errors."""
        try:
            config = get_config()
            dcf_config = get_dcf_config()
            assert config is not None
            assert dcf_config is not None
        except Exception as e:
            pytest.fail(f"Config functions should not raise exceptions: {e}")

    def test_configuration_types(self):
        """Test configuration return types."""
        config = get_config()
        dcf_config = get_dcf_config()

        # Should be objects (not None, str, int, etc.)
        assert not isinstance(config, (str, int, float, bool))
        assert not isinstance(dcf_config, (str, int, float, bool))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])