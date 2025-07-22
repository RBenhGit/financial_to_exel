"""
Input validation module for Yahoo Finance API calls and financial data processing.

This module provides comprehensive validation for ticker symbols, network connectivity,
and system dependencies before making API calls to improve error handling and prevent
unnecessary requests.
"""

import re
import socket
import requests
import importlib
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    remediation: Optional[str] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class TickerValidator:
    """Validates ticker symbol formats and characteristics."""
    
    # Common stock exchange suffixes
    EXCHANGE_SUFFIXES = {
        '.TO': 'Toronto Stock Exchange',
        '.V': 'TSX Venture Exchange',
        '.L': 'London Stock Exchange',
        '.PA': 'Euronext Paris',
        '.DE': 'Xetra',
        '.HK': 'Hong Kong Stock Exchange',
        '.T': 'Tokyo Stock Exchange',
        '.AX': 'Australian Securities Exchange',
        '.SS': 'Shanghai Stock Exchange',
        '.SZ': 'Shenzhen Stock Exchange',
        '.NS': 'National Stock Exchange of India',
        '.BO': 'Bombay Stock Exchange',
        '.SA': 'B3 Brazil Stock Exchange',
        '.ME': 'Moscow Exchange',
        '.IS': 'Borsa Istanbul'
    }
    
    # Regex patterns for different validation levels
    PATTERNS = {
        ValidationLevel.STRICT: r'^[A-Z]{1,5}(\.[A-Z]{1,3})?$',
        ValidationLevel.MODERATE: r'^[A-Z0-9.-]{1,10}$',
        ValidationLevel.PERMISSIVE: r'^[A-Z0-9.-]{1,20}$'
    }
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.pattern = re.compile(self.PATTERNS[validation_level])
    
    def validate(self, ticker: str) -> ValidationResult:
        """
        Validate a ticker symbol format.
        
        Args:
            ticker: The ticker symbol to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        if not ticker:
            return ValidationResult(
                is_valid=False,
                error_code="EMPTY_TICKER",
                error_message="Ticker symbol cannot be empty or None",
                remediation="Provide a valid ticker symbol (e.g., 'AAPL', 'MSFT.TO')"
            )
        
        if not isinstance(ticker, str):
            return ValidationResult(
                is_valid=False,
                error_code="INVALID_TYPE",
                error_message=f"Ticker must be a string, got {type(ticker).__name__}",
                remediation="Convert ticker to string format"
            )
        
        # Clean and normalize ticker
        clean_ticker = ticker.strip().upper()
        
        # Check length limits
        if len(clean_ticker) < 1:
            return ValidationResult(
                is_valid=False,
                error_code="TICKER_TOO_SHORT",
                error_message="Ticker symbol is too short (minimum 1 character)",
                remediation="Provide a ticker symbol with at least 1 character"
            )
        
        max_length = 20 if self.validation_level == ValidationLevel.PERMISSIVE else 10
        if len(clean_ticker) > max_length:
            return ValidationResult(
                is_valid=False,
                error_code="TICKER_TOO_LONG",
                error_message=f"Ticker symbol is too long (maximum {max_length} characters)",
                remediation=f"Use a shorter ticker symbol (max {max_length} characters)"
            )
        
        # Check pattern match
        if not self.pattern.match(clean_ticker):
            return ValidationResult(
                is_valid=False,
                error_code="INVALID_FORMAT",
                error_message=f"Ticker format doesn't match {self.validation_level.value} validation rules",
                remediation="Use standard ticker format (letters, numbers, dots, hyphens only)"
            )
        
        # Check for known exchange suffixes and provide warnings
        warnings = []
        if '.' in clean_ticker:
            suffix = '.' + clean_ticker.split('.', 1)[1]
            if suffix not in self.EXCHANGE_SUFFIXES and self.validation_level == ValidationLevel.STRICT:
                warnings.append(f"Unknown exchange suffix '{suffix}'. Common suffixes: {', '.join(list(self.EXCHANGE_SUFFIXES.keys())[:5])}")
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            metadata={
                'clean_ticker': clean_ticker,
                'original_ticker': ticker,
                'validation_level': self.validation_level.value,
                'has_exchange_suffix': '.' in clean_ticker
            }
        )


class NetworkValidator:
    """Validates network connectivity and external service availability."""
    
    DEFAULT_TEST_URLS = [
        'https://finance.yahoo.com',
        'https://query1.finance.yahoo.com',
        'https://www.google.com'
    ]
    
    def __init__(self, timeout: float = 10.0, test_urls: Optional[List[str]] = None):
        self.timeout = timeout
        self.test_urls = test_urls or self.DEFAULT_TEST_URLS
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def validate_dns_resolution(self, hostname: str = 'finance.yahoo.com') -> ValidationResult:
        """Test DNS resolution."""
        try:
            socket.getaddrinfo(hostname, None)
            return ValidationResult(
                is_valid=True,
                metadata={'hostname': hostname, 'test_type': 'dns_resolution'}
            )
        except socket.gaierror as e:
            return ValidationResult(
                is_valid=False,
                error_code="DNS_RESOLUTION_FAILED",
                error_message=f"DNS resolution failed for {hostname}: {str(e)}",
                remediation="Check internet connection and DNS settings"
            )
    
    def validate_http_connectivity(self) -> ValidationResult:
        """Test HTTP connectivity to financial services."""
        errors = []
        successful_urls = []
        
        for url in self.test_urls:
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if response.status_code < 400:
                    successful_urls.append(url)
                else:
                    errors.append(f"{url}: HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                errors.append(f"{url}: Connection timeout")
            except requests.exceptions.ConnectionError as e:
                errors.append(f"{url}: Connection error - {str(e)}")
            except Exception as e:
                errors.append(f"{url}: Unexpected error - {str(e)}")
        
        if successful_urls:
            warnings = [f"Some URLs failed: {', '.join(errors)}"] if errors else []
            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                metadata={
                    'successful_urls': successful_urls,
                    'failed_urls': [err.split(':')[0] for err in errors],
                    'test_type': 'http_connectivity'
                }
            )
        else:
            return ValidationResult(
                is_valid=False,
                error_code="NO_HTTP_CONNECTIVITY",
                error_message=f"All HTTP connectivity tests failed: {'; '.join(errors)}",
                remediation="Check internet connection, firewall settings, or proxy configuration"
            )
    
    def validate(self) -> ValidationResult:
        """Run comprehensive network validation."""
        # Test DNS first
        dns_result = self.validate_dns_resolution()
        if not dns_result.is_valid:
            return dns_result
        
        # Test HTTP connectivity
        http_result = self.validate_http_connectivity()
        
        # Combine results
        warnings = dns_result.warnings + http_result.warnings
        metadata = {**dns_result.metadata, **http_result.metadata}
        
        return ValidationResult(
            is_valid=http_result.is_valid,
            error_code=http_result.error_code,
            error_message=http_result.error_message,
            remediation=http_result.remediation,
            warnings=warnings,
            metadata=metadata
        )


class DependencyValidator:
    """Validates required Python packages and their versions."""
    
    REQUIRED_PACKAGES = {
        'pandas': {'min_version': '1.0.0', 'critical': True},
        'numpy': {'min_version': '1.18.0', 'critical': True},
        'yfinance': {'min_version': '0.1.70', 'critical': True},
        'requests': {'min_version': '2.20.0', 'critical': True},
        'openpyxl': {'min_version': '3.0.0', 'critical': False},
        'pyarrow': {'min_version': '5.0.0', 'critical': False}
    }
    
    def __init__(self, additional_packages: Optional[Dict[str, Dict[str, Any]]] = None):
        self.packages = self.REQUIRED_PACKAGES.copy()
        if additional_packages:
            self.packages.update(additional_packages)
    
    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get the version of an installed package."""
        try:
            module = importlib.import_module(package_name)
            return getattr(module, '__version__', None)
        except ImportError:
            return None
    
    def _compare_versions(self, current: str, required: str) -> bool:
        """Compare version strings (simplified semver comparison)."""
        def version_tuple(v):
            return tuple(map(int, (v.split(".")[:3] + ["0", "0", "0"])[:3]))
        
        try:
            return version_tuple(current) >= version_tuple(required)
        except (ValueError, AttributeError):
            return True  # If we can't parse, assume it's okay
    
    def validate_package(self, package_name: str, requirements: Dict[str, Any]) -> ValidationResult:
        """Validate a single package."""
        version = self._get_package_version(package_name)
        
        if version is None:
            error_level = "CRITICAL_PACKAGE_MISSING" if requirements.get('critical', True) else "OPTIONAL_PACKAGE_MISSING"
            return ValidationResult(
                is_valid=not requirements.get('critical', True),
                error_code=error_level,
                error_message=f"Required package '{package_name}' is not installed",
                remediation=f"Install package: pip install {package_name}>={requirements.get('min_version', '')}"
            )
        
        min_version = requirements.get('min_version')
        if min_version and not self._compare_versions(version, min_version):
            return ValidationResult(
                is_valid=False,
                error_code="PACKAGE_VERSION_TOO_OLD",
                error_message=f"Package '{package_name}' version {version} is below minimum required {min_version}",
                remediation=f"Update package: pip install --upgrade {package_name}>={min_version}"
            )
        
        return ValidationResult(
            is_valid=True,
            metadata={
                'package': package_name,
                'version': version,
                'required_version': min_version,
                'critical': requirements.get('critical', True)
            }
        )
    
    def validate(self) -> ValidationResult:
        """Validate all required packages."""
        results = {}
        critical_failures = []
        warnings = []
        
        for package_name, requirements in self.packages.items():
            result = self.validate_package(package_name, requirements)
            results[package_name] = result
            
            if not result.is_valid:
                if requirements.get('critical', True):
                    critical_failures.append(result.error_message)
                else:
                    warnings.append(result.error_message)
        
        if critical_failures:
            return ValidationResult(
                is_valid=False,
                error_code="CRITICAL_DEPENDENCIES_MISSING",
                error_message=f"Critical package validation failed: {'; '.join(critical_failures)}",
                remediation="Install missing critical packages before proceeding",
                warnings=warnings,
                metadata={'package_results': results}
            )
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            metadata={'package_results': results}
        )


class ValidationCache:
    """Simple in-memory cache for validation results."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minute default TTL
        self.ttl_seconds = ttl_seconds
        self._cache = {}
    
    def _get_cache_key(self, validator_type: str, params: Dict[str, Any]) -> str:
        """Generate cache key from validator type and parameters."""
        param_str = ','.join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{validator_type}:{param_str}"
    
    def get(self, validator_type: str, params: Dict[str, Any]) -> Optional[ValidationResult]:
        """Get cached validation result."""
        key = self._get_cache_key(validator_type, params)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.debug(f"Cache hit for {key}")
                return result
            else:
                del self._cache[key]  # Expired
        return None
    
    def set(self, validator_type: str, params: Dict[str, Any], result: ValidationResult):
        """Cache validation result."""
        key = self._get_cache_key(validator_type, params)
        self._cache[key] = (result, time.time())
        logger.debug(f"Cached result for {key}")
    
    def clear(self):
        """Clear all cached results."""
        self._cache.clear()


class PreFlightValidator:
    """Comprehensive pre-flight validation pipeline for Yahoo Finance API calls."""
    
    def __init__(
        self,
        validation_level: ValidationLevel = ValidationLevel.MODERATE,
        enable_caching: bool = True,
        cache_ttl: int = 300,
        network_timeout: float = 10.0
    ):
        self.validation_level = validation_level
        self.ticker_validator = TickerValidator(validation_level)
        self.network_validator = NetworkValidator(timeout=network_timeout)
        self.dependency_validator = DependencyValidator()
        self.cache = ValidationCache(cache_ttl) if enable_caching else None
        
    def validate_ticker(self, ticker: str, use_cache: bool = True) -> ValidationResult:
        """Validate ticker symbol with optional caching."""
        if use_cache and self.cache:
            cached = self.cache.get('ticker', {'ticker': ticker, 'level': self.validation_level.value})
            if cached:
                return cached
        
        result = self.ticker_validator.validate(ticker)
        
        if use_cache and self.cache:
            self.cache.set('ticker', {'ticker': ticker, 'level': self.validation_level.value}, result)
        
        return result
    
    def validate_network(self, use_cache: bool = True) -> ValidationResult:
        """Validate network connectivity with optional caching."""
        if use_cache and self.cache:
            cached = self.cache.get('network', {})
            if cached:
                return cached
        
        result = self.network_validator.validate()
        
        if use_cache and self.cache:
            self.cache.set('network', {}, result)
        
        return result
    
    def validate_dependencies(self, use_cache: bool = True) -> ValidationResult:
        """Validate system dependencies with optional caching."""
        if use_cache and self.cache:
            cached = self.cache.get('dependencies', {})
            if cached:
                return cached
        
        result = self.dependency_validator.validate()
        
        if use_cache and self.cache:
            self.cache.set('dependencies', {}, result)
        
        return result
    
    def validate_all(self, ticker: str, skip_network: bool = False) -> Dict[str, ValidationResult]:
        """
        Run complete validation pipeline.
        
        Args:
            ticker: Ticker symbol to validate
            skip_network: Skip network validation (useful for offline testing)
            
        Returns:
            Dictionary of validation results by category
        """
        results = {}
        
        # Validate ticker
        results['ticker'] = self.validate_ticker(ticker)
        
        # Validate dependencies
        results['dependencies'] = self.validate_dependencies()
        
        # Validate network connectivity (unless skipped)
        if not skip_network:
            results['network'] = self.validate_network()
        
        return results
    
    def is_ready_for_api_call(self, ticker: str, skip_network: bool = False) -> Tuple[bool, List[str]]:
        """
        Check if system is ready for Yahoo Finance API call.
        
        Returns:
            Tuple of (is_ready, list_of_error_messages)
        """
        results = self.validate_all(ticker, skip_network)
        
        errors = []
        for category, result in results.items():
            if not result.is_valid:
                errors.append(f"{category.upper()}: {result.error_message}")
        
        return len(errors) == 0, errors
    
    def get_remediation_steps(self, ticker: str, skip_network: bool = False) -> List[str]:
        """Get ordered list of remediation steps for validation failures."""
        results = self.validate_all(ticker, skip_network)
        
        steps = []
        for category, result in results.items():
            if not result.is_valid and result.remediation:
                steps.append(f"{category.upper()}: {result.remediation}")
        
        return steps


# Convenience functions for common validation scenarios
def validate_ticker_quick(ticker: str, level: ValidationLevel = ValidationLevel.MODERATE) -> bool:
    """Quick ticker validation returning boolean result."""
    validator = TickerValidator(level)
    return validator.validate(ticker).is_valid


def validate_system_ready(skip_network: bool = False) -> Tuple[bool, List[str]]:
    """Quick system readiness check."""
    validator = PreFlightValidator()
    return validator.is_ready_for_api_call("AAPL", skip_network)  # Use dummy ticker for system checks


if __name__ == "__main__":
    # Example usage and testing
    validator = PreFlightValidator()
    
    test_tickers = ["AAPL", "MSFT.TO", "INVALID@TICKER", "", "GOOGL"]
    
    print("=== Ticker Validation Tests ===")
    for ticker in test_tickers:
        result = validator.validate_ticker(ticker)
        print(f"{ticker:15} -> {'✓' if result.is_valid else '✗'} {result.error_message or 'Valid'}")
    
    print("\n=== System Validation ===")
    results = validator.validate_all("AAPL")
    for category, result in results.items():
        print(f"{category:12} -> {'✓' if result.is_valid else '✗'} {result.error_message or 'Valid'}")
    
    ready, errors = validator.is_ready_for_api_call("AAPL")
    print(f"\nSystem ready for API call: {'✓' if ready else '✗'}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")