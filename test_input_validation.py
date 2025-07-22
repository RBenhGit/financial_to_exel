"""
Comprehensive test suite for the input validation system.

This module tests all aspects of the input validation system including
ticker validation, network connectivity checks, dependency verification,
and integration with the centralized data manager.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
import time
import socket
import requests
from input_validator import (
    TickerValidator, 
    NetworkValidator, 
    DependencyValidator,
    PreFlightValidator,
    ValidationLevel,
    ValidationResult,
    ValidationCache,
    validate_ticker_quick,
    validate_system_ready
)
from centralized_data_manager import CentralizedDataManager


class TestTickerValidator(unittest.TestCase):
    """Test ticker symbol validation functionality."""
    
    def setUp(self):
        self.validator_strict = TickerValidator(ValidationLevel.STRICT)
        self.validator_moderate = TickerValidator(ValidationLevel.MODERATE)
        self.validator_permissive = TickerValidator(ValidationLevel.PERMISSIVE)
    
    def test_valid_tickers(self):
        """Test validation of valid ticker symbols."""
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        for ticker in valid_tickers:
            with self.subTest(ticker=ticker):
                result = self.validator_moderate.validate(ticker)
                self.assertTrue(result.is_valid, f"Ticker {ticker} should be valid")
                self.assertIsNone(result.error_code)
                self.assertEqual(result.metadata['clean_ticker'], ticker)
    
    def test_tickers_with_exchange_suffixes(self):
        """Test validation of tickers with exchange suffixes."""
        exchange_tickers = ["SHOP.TO", "ASML.AS", "NVO.L", "SAP.DE"]
        
        for ticker in exchange_tickers:
            with self.subTest(ticker=ticker):
                result = self.validator_moderate.validate(ticker)
                self.assertTrue(result.is_valid, f"Ticker {ticker} should be valid")
                self.assertTrue(result.metadata['has_exchange_suffix'])
    
    def test_invalid_tickers(self):
        """Test validation of invalid ticker symbols."""
        invalid_cases = [
            ("", "EMPTY_TICKER"),
            (None, "EMPTY_TICKER"),
            ("AP@PL", "INVALID_FORMAT"),
            ("A" * 25, "TICKER_TOO_LONG"),
            (123, "INVALID_TYPE"),
            ("AAPL$", "INVALID_FORMAT")
        ]
        
        for ticker, expected_error in invalid_cases:
            with self.subTest(ticker=ticker):
                result = self.validator_moderate.validate(ticker)
                self.assertFalse(result.is_valid, f"Ticker {ticker} should be invalid")
                self.assertEqual(result.error_code, expected_error)
                self.assertIsNotNone(result.remediation)
    
    def test_validation_levels(self):
        """Test different validation strictness levels."""
        test_ticker = "TEST123.XY"
        
        # Strict should be more restrictive
        strict_result = self.validator_strict.validate(test_ticker)
        moderate_result = self.validator_moderate.validate(test_ticker)
        permissive_result = self.validator_permissive.validate(test_ticker)
        
        # All should handle basic valid cases
        simple_ticker = "AAPL"
        for validator in [self.validator_strict, self.validator_moderate, self.validator_permissive]:
            result = validator.validate(simple_ticker)
            self.assertTrue(result.is_valid)
    
    def test_case_normalization(self):
        """Test that tickers are properly normalized to uppercase."""
        result = self.validator_moderate.validate("aapl")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata['clean_ticker'], "AAPL")
        self.assertEqual(result.metadata['original_ticker'], "aapl")
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly trimmed."""
        result = self.validator_moderate.validate("  AAPL  ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata['clean_ticker'], "AAPL")


class TestNetworkValidator(unittest.TestCase):
    """Test network connectivity validation functionality."""
    
    def setUp(self):
        self.validator = NetworkValidator(timeout=5.0)
    
    @patch('socket.getaddrinfo')
    def test_dns_resolution_success(self, mock_getaddrinfo):
        """Test successful DNS resolution."""
        mock_getaddrinfo.return_value = [('family', 'type', 'proto', 'canonname', 'sockaddr')]
        
        result = self.validator.validate_dns_resolution()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata['test_type'], 'dns_resolution')
    
    @patch('socket.getaddrinfo')
    def test_dns_resolution_failure(self, mock_getaddrinfo):
        """Test DNS resolution failure."""
        mock_getaddrinfo.side_effect = socket.gaierror("Name resolution failed")
        
        result = self.validator.validate_dns_resolution()
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "DNS_RESOLUTION_FAILED")
        self.assertIn("Check internet connection", result.remediation)
    
    @patch.object(NetworkValidator, '_session')
    def test_http_connectivity_success(self, mock_session):
        """Test successful HTTP connectivity."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        validator = NetworkValidator(test_urls=['https://example.com'])
        validator._session = mock_session
        
        result = validator.validate_http_connectivity()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.metadata['successful_urls']), 1)
    
    @patch.object(NetworkValidator, '_session')
    def test_http_connectivity_failure(self, mock_session):
        """Test HTTP connectivity failure."""
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        validator = NetworkValidator(test_urls=['https://example.com'])
        validator._session = mock_session
        
        result = validator.validate_http_connectivity()
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "NO_HTTP_CONNECTIVITY")
    
    @patch.object(NetworkValidator, '_session')
    def test_http_connectivity_timeout(self, mock_session):
        """Test HTTP connectivity timeout."""
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        validator = NetworkValidator(test_urls=['https://example.com'])
        validator._session = mock_session
        
        result = validator.validate_http_connectivity()
        self.assertFalse(result.is_valid)
        self.assertIn("timeout", str(result.error_message).lower())


class TestDependencyValidator(unittest.TestCase):
    """Test dependency validation functionality."""
    
    def setUp(self):
        self.validator = DependencyValidator()
    
    @patch('importlib.import_module')
    def test_package_exists_with_version(self, mock_import):
        """Test validation of existing package with version."""
        mock_module = MagicMock()
        mock_module.__version__ = "1.5.0"
        mock_import.return_value = mock_module
        
        result = self.validator.validate_package('pandas', {'min_version': '1.0.0', 'critical': True})
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata['version'], "1.5.0")
    
    @patch('importlib.import_module')
    def test_package_missing_critical(self, mock_import):
        """Test validation of missing critical package."""
        mock_import.side_effect = ImportError("No module named 'missing_package'")
        
        result = self.validator.validate_package('missing_package', {'critical': True})
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "CRITICAL_PACKAGE_MISSING")
        self.assertIn("pip install", result.remediation)
    
    @patch('importlib.import_module')
    def test_package_missing_optional(self, mock_import):
        """Test validation of missing optional package."""
        mock_import.side_effect = ImportError("No module named 'optional_package'")
        
        result = self.validator.validate_package('optional_package', {'critical': False})
        self.assertTrue(result.is_valid)  # Should be valid for optional packages
        self.assertEqual(result.error_code, "OPTIONAL_PACKAGE_MISSING")
    
    @patch('importlib.import_module')
    def test_package_version_too_old(self, mock_import):
        """Test validation of package with outdated version."""
        mock_module = MagicMock()
        mock_module.__version__ = "0.9.0"
        mock_import.return_value = mock_module
        
        result = self.validator.validate_package('pandas', {'min_version': '1.0.0', 'critical': True})
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "PACKAGE_VERSION_TOO_OLD")
        self.assertIn("upgrade", result.remediation)
    
    def test_version_comparison(self):
        """Test version comparison logic."""
        self.assertTrue(self.validator._compare_versions("1.5.0", "1.0.0"))
        self.assertTrue(self.validator._compare_versions("2.0.0", "1.9.9"))
        self.assertFalse(self.validator._compare_versions("0.9.0", "1.0.0"))
        self.assertTrue(self.validator._compare_versions("1.0.0", "1.0.0"))


class TestValidationCache(unittest.TestCase):
    """Test validation result caching functionality."""
    
    def setUp(self):
        self.cache = ValidationCache(ttl_seconds=2)
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        result = ValidationResult(is_valid=True, metadata={'test': 'data'})
        
        self.cache.set('test_validator', {'param': 'value'}, result)
        cached_result = self.cache.get('test_validator', {'param': 'value'})
        
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result.is_valid)
        self.assertEqual(cached_result.metadata['test'], 'data')
    
    def test_cache_expiry(self):
        """Test cache expiration functionality."""
        result = ValidationResult(is_valid=True)
        
        self.cache.set('test_validator', {'param': 'value'}, result)
        
        # Should be available immediately
        cached = self.cache.get('test_validator', {'param': 'value'})
        self.assertIsNotNone(cached)
        
        # Wait for expiry
        time.sleep(2.1)
        
        # Should be expired now
        cached = self.cache.get('test_validator', {'param': 'value'})
        self.assertIsNone(cached)
    
    def test_cache_key_generation(self):
        """Test cache key generation with different parameters."""
        result = ValidationResult(is_valid=True)
        
        # Different parameter order should generate same key
        self.cache.set('test', {'a': 1, 'b': 2}, result)
        cached = self.cache.get('test', {'b': 2, 'a': 1})
        self.assertIsNotNone(cached)
    
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        result = ValidationResult(is_valid=True)
        
        self.cache.set('test', {'param': 'value'}, result)
        self.assertIsNotNone(self.cache.get('test', {'param': 'value'}))
        
        self.cache.clear()
        self.assertIsNone(self.cache.get('test', {'param': 'value'}))


class TestPreFlightValidator(unittest.TestCase):
    """Test the comprehensive pre-flight validation pipeline."""
    
    def setUp(self):
        self.validator = PreFlightValidator()
    
    def test_ticker_validation_integration(self):
        """Test ticker validation through pre-flight validator."""
        result = self.validator.validate_ticker("AAPL")
        self.assertTrue(result.is_valid)
        
        result = self.validator.validate_ticker("INVALID@TICKER")
        self.assertFalse(result.is_valid)
    
    @patch.object(NetworkValidator, 'validate')
    @patch.object(DependencyValidator, 'validate')
    def test_complete_validation_pipeline(self, mock_dep_validate, mock_net_validate):
        """Test the complete validation pipeline."""
        mock_net_validate.return_value = ValidationResult(is_valid=True)
        mock_dep_validate.return_value = ValidationResult(is_valid=True)
        
        results = self.validator.validate_all("AAPL")
        
        self.assertIn('ticker', results)
        self.assertIn('network', results)
        self.assertIn('dependencies', results)
        
        self.assertTrue(results['ticker'].is_valid)
        self.assertTrue(results['network'].is_valid)
        self.assertTrue(results['dependencies'].is_valid)
    
    @patch.object(NetworkValidator, 'validate')
    @patch.object(DependencyValidator, 'validate')
    def test_api_readiness_check(self, mock_dep_validate, mock_net_validate):
        """Test API readiness check functionality."""
        mock_net_validate.return_value = ValidationResult(is_valid=True)
        mock_dep_validate.return_value = ValidationResult(is_valid=True)
        
        is_ready, errors = self.validator.is_ready_for_api_call("AAPL")
        self.assertTrue(is_ready)
        self.assertEqual(len(errors), 0)
        
        # Test with validation failure
        mock_dep_validate.return_value = ValidationResult(
            is_valid=False, 
            error_message="Missing dependency"
        )
        
        is_ready, errors = self.validator.is_ready_for_api_call("AAPL")
        self.assertFalse(is_ready)
        self.assertGreater(len(errors), 0)
    
    def test_validation_caching(self):
        """Test that validation results are properly cached."""
        # Enable caching
        validator = PreFlightValidator(enable_caching=True, cache_ttl=10)
        
        # First call should populate cache
        result1 = validator.validate_ticker("AAPL")
        
        # Second call should use cache (we can't easily verify this without mocking,
        # but we can at least ensure consistent results)
        result2 = validator.validate_ticker("AAPL")
        
        self.assertEqual(result1.is_valid, result2.is_valid)
    
    def test_remediation_steps(self):
        """Test remediation steps generation."""
        # This requires mocking failures to test remediation
        with patch.object(self.validator.ticker_validator, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                error_message="Invalid ticker",
                remediation="Fix the ticker format"
            )
            
            steps = self.validator.get_remediation_steps("INVALID")
            self.assertGreater(len(steps), 0)
            self.assertIn("TICKER", steps[0])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for common validation scenarios."""
    
    def test_validate_ticker_quick(self):
        """Test quick ticker validation function."""
        self.assertTrue(validate_ticker_quick("AAPL"))
        self.assertFalse(validate_ticker_quick("INVALID@TICKER"))
        self.assertFalse(validate_ticker_quick(""))
    
    @patch.object(PreFlightValidator, 'is_ready_for_api_call')
    def test_validate_system_ready(self, mock_is_ready):
        """Test system readiness check function."""
        mock_is_ready.return_value = (True, [])
        
        is_ready, errors = validate_system_ready()
        self.assertTrue(is_ready)
        self.assertEqual(len(errors), 0)
        
        mock_is_ready.return_value = (False, ["Network error"])
        is_ready, errors = validate_system_ready()
        self.assertFalse(is_ready)
        self.assertGreater(len(errors), 0)


class TestCentralizedDataManagerIntegration(unittest.TestCase):
    """Test integration with CentralizedDataManager."""
    
    def setUp(self):
        # Create a temporary directory for testing
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CentralizedDataManager(self.temp_dir, validation_level=ValidationLevel.MODERATE)
    
    def test_validation_integration(self):
        """Test that validation is properly integrated into data manager."""
        # Test ticker validation method
        result = self.manager.validate_ticker("AAPL")
        self.assertTrue(result.is_valid)
        
        result = self.manager.validate_ticker("INVALID@")
        self.assertFalse(result.is_valid)
    
    def test_system_readiness_check(self):
        """Test system readiness check through data manager."""
        is_ready = self.manager.is_system_ready("AAPL", skip_network=True)
        self.assertIsInstance(is_ready, bool)
    
    def test_validation_config_access(self):
        """Test access to validation configuration."""
        config = self.manager.get_validation_config()
        self.assertIn('validation_level', config)
        self.assertIn('network_timeout', config)
        self.assertEqual(config['validation_level'], 'moderate')
    
    @patch.object(PreFlightValidator, 'is_ready_for_api_call')
    def test_market_data_with_validation_failure(self, mock_is_ready):
        """Test market data fetching with validation failure."""
        mock_is_ready.return_value = (False, ["Validation failed"])
        
        result = self.manager.fetch_market_data("INVALID", skip_validation=False)
        self.assertIsNone(result)
    
    @patch.object(PreFlightValidator, 'is_ready_for_api_call')
    def test_market_data_skip_validation(self, mock_is_ready):
        """Test market data fetching with validation skipped."""
        # This should not call validation at all
        with patch('yfinance.Ticker') as mock_yf:
            mock_stock = MagicMock()
            mock_stock.info = {'symbol': 'AAPL', 'shortName': 'Apple Inc.'}
            mock_yf.return_value = mock_stock
            
            result = self.manager.fetch_market_data("AAPL", skip_validation=True)
            
            # Validation should not have been called
            mock_is_ready.assert_not_called()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
    
    # Example of how to run specific test categories
    print("\n=== Running Ticker Validation Tests ===")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTickerValidator)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    print("\n=== Running Integration Tests ===")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCentralizedDataManagerIntegration)
    unittest.TextTestRunner(verbosity=2).run(suite)