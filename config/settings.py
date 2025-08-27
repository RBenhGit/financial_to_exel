"""
Environment-Based Settings Configuration
========================================

This module provides environment-specific configuration management for the
financial analysis application. It supports development, testing, and production
environments with appropriate defaults and overrides.

Features:
- Environment detection from environment variables
- Cascading configuration (base -> environment -> user overrides)
- Runtime configuration validation
- Secure handling of API keys and sensitive data
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from .constants import (
    # Environment constants
    ENV_DEVELOPMENT, ENV_TESTING, ENV_PRODUCTION,
    ENV_VAR_ENVIRONMENT, ENV_VAR_LOG_LEVEL, ENV_VAR_CACHE_DIR,
    
    # API constants
    DEFAULT_NETWORK_TIMEOUT, DEFAULT_API_TIMEOUT,
    ALPHA_VANTAGE_BASE_URL, FMP_BASE_URL, POLYGON_BASE_URL,
    
    # API key environment variables
    ENV_ALPHA_VANTAGE_KEY, ENV_FMP_KEY, ENV_POLYGON_KEY,
    
    # Default directories
    DEFAULT_EXPORT_DIR, DEFAULT_DATA_DIR, DEFAULT_CACHE_DIR, DEFAULT_LOG_DIR,
    
    # Logging
    LOG_LEVEL_INFO, DEFAULT_LOG_FORMAT,
    
    # Cache settings
    DEFAULT_CACHE_TTL
)

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported environment types"""
    DEVELOPMENT = ENV_DEVELOPMENT
    TESTING = ENV_TESTING  
    PRODUCTION = ENV_PRODUCTION


@dataclass
class ApiConfig:
    """API configuration settings"""
    
    # Timeout settings
    network_timeout: float = DEFAULT_NETWORK_TIMEOUT
    api_timeout: float = DEFAULT_API_TIMEOUT
    
    # Enhanced Rate limiting
    rate_limit_delay: float = 1.0
    max_retries: int = 7
    backoff_factor: float = 2.0
    base_delay: float = 3.0
    max_delay: float = 120.0
    jitter_enabled: bool = True
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 300  # 5 minutes
    circuit_breaker_success_threshold: int = 3
    
    # Request queue settings
    request_queue_enabled: bool = True
    max_queue_size: int = 100
    queue_timeout: float = 60.0
    min_request_spacing: float = 0.5  # Minimum seconds between requests
    
    # Adaptive rate limiting
    adaptive_rate_limiting: bool = True
    rate_limit_header_respect: bool = True
    dynamic_backoff_enabled: bool = True
    
    # Fallback configuration
    fallback_quick_switch: bool = True
    fallback_threshold_failures: int = 3
    parallel_source_queries: bool = False
    
    # API endpoints
    alpha_vantage_url: str = ALPHA_VANTAGE_BASE_URL
    fmp_url: str = FMP_BASE_URL
    polygon_url: str = POLYGON_BASE_URL
    
    # API keys (loaded from environment)
    alpha_vantage_key: Optional[str] = field(default=None, init=False)
    fmp_key: Optional[str] = field(default=None, init=False)
    polygon_key: Optional[str] = field(default=None, init=False)
    
    def __post_init__(self):
        """Load API keys from environment variables"""
        self.alpha_vantage_key = os.getenv(ENV_ALPHA_VANTAGE_KEY)
        self.fmp_key = os.getenv(ENV_FMP_KEY)  
        self.polygon_key = os.getenv(ENV_POLYGON_KEY)


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    
    # Cache directory
    cache_dir: str = DEFAULT_CACHE_DIR
    
    # TTL settings (seconds)
    default_ttl: int = DEFAULT_CACHE_TTL
    price_ttl: int = 900  # 15 minutes
    financial_data_ttl: int = 21600  # 6 hours
    metadata_ttl: int = 604800  # 7 days
    
    # Extended TTL during rate limiting (seconds)
    rate_limited_price_ttl: int = 3600  # 1 hour during rate limits
    rate_limited_financial_ttl: int = 43200  # 12 hours during rate limits
    rate_limited_market_data_ttl: int = 7200  # 2 hours during rate limits
    emergency_cache_extension: bool = True
    
    # Size limits
    max_entries: int = 1000
    max_size_mb: int = 100
    
    # Enable/disable caching
    enabled: bool = True
    
    def __post_init__(self):
        """Override cache directory from environment if specified"""
        env_cache_dir = os.getenv(ENV_VAR_CACHE_DIR)
        if env_cache_dir:
            self.cache_dir = env_cache_dir


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    
    # Log level
    log_level: str = LOG_LEVEL_INFO
    
    # Log format
    log_format: str = DEFAULT_LOG_FORMAT
    
    # File settings
    log_dir: str = DEFAULT_LOG_DIR
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Console logging
    console_logging: bool = True
    file_logging: bool = True
    
    def __post_init__(self):
        """Override log level from environment if specified"""
        env_log_level = os.getenv(ENV_VAR_LOG_LEVEL)
        if env_log_level:
            self.log_level = env_log_level.upper()


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    
    # SQLite settings for watch lists
    db_dir: str = DEFAULT_DATA_DIR
    watch_lists_db: str = "watch_lists.db"
    
    # Connection settings
    timeout: float = 30.0
    
    # Backup settings
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    def get_db_path(self) -> Path:
        """Get full path to database file"""
        return Path(self.db_dir) / self.watch_lists_db


@dataclass
class SecurityConfig:
    """Security and validation settings"""
    
    # Input validation
    strict_validation: bool = False
    max_input_length: int = 1000
    
    # File security
    allow_file_uploads: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = field(default_factory=lambda: ['.xlsx', '.xls', '.csv'])
    
    # API security
    hide_api_keys_in_logs: bool = True
    mask_sensitive_data: bool = True


@dataclass
class PerformanceConfig:
    """Performance and optimization settings"""
    
    # Parallel processing
    enable_multiprocessing: bool = False
    max_workers: int = 4
    
    # Memory management
    max_memory_mb: int = 2048
    gc_threshold: int = 1000
    
    # Data processing
    chunk_size: int = 1000
    batch_size: int = 100


@dataclass
class EnvironmentSettings:
    """Complete environment-specific settings"""
    
    environment: Environment = Environment.DEVELOPMENT
    
    # Configuration components
    api: ApiConfig = field(default_factory=ApiConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Directory settings
    export_dir: str = DEFAULT_EXPORT_DIR
    data_dir: str = DEFAULT_DATA_DIR
    
    # Feature flags
    enable_experimental_features: bool = False
    enable_detailed_logging: bool = False
    enable_profiling: bool = False
    
    @classmethod
    def for_development(cls) -> 'EnvironmentSettings':
        """Create development environment settings"""
        settings = cls(environment=Environment.DEVELOPMENT)
        
        # Development-specific overrides
        settings.logging.log_level = "DEBUG"
        settings.logging.console_logging = True
        settings.cache.enabled = True
        settings.security.strict_validation = False
        settings.enable_detailed_logging = True
        settings.enable_experimental_features = True
        settings.performance.enable_multiprocessing = False
        
        return settings
    
    @classmethod
    def for_testing(cls) -> 'EnvironmentSettings':
        """Create testing environment settings"""
        settings = cls(environment=Environment.TESTING)
        
        # Testing-specific overrides
        settings.logging.log_level = "WARNING"
        settings.logging.file_logging = False
        settings.cache.enabled = False
        settings.security.strict_validation = True
        settings.database.db_dir = "test_data"
        settings.export_dir = "test_exports"
        settings.api.network_timeout = 5.0  # Faster timeouts for tests
        settings.performance.enable_multiprocessing = False
        
        return settings
    
    @classmethod
    def for_production(cls) -> 'EnvironmentSettings':
        """Create production environment settings"""
        settings = cls(environment=Environment.PRODUCTION)
        
        # Production-specific overrides
        settings.logging.log_level = "INFO"
        settings.logging.console_logging = False
        settings.logging.file_logging = True
        settings.cache.enabled = True
        settings.security.strict_validation = True
        settings.security.hide_api_keys_in_logs = True
        settings.security.mask_sensitive_data = True
        settings.enable_experimental_features = False
        settings.enable_detailed_logging = False
        settings.performance.enable_multiprocessing = True
        settings.performance.max_workers = 2  # Conservative for production
        
        return settings


class SettingsManager:
    """Manages application settings across environments"""
    
    _instance: Optional['SettingsManager'] = None
    _settings: Optional[EnvironmentSettings] = None
    
    def __new__(cls) -> 'SettingsManager':
        """Singleton pattern to ensure single settings instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize settings manager"""
        if self._settings is None:
            self._settings = self._load_settings()
    
    def _load_settings(self) -> EnvironmentSettings:
        """Load settings based on current environment"""
        env_name = os.getenv(ENV_VAR_ENVIRONMENT, ENV_DEVELOPMENT).lower()
        
        try:
            if env_name == ENV_DEVELOPMENT:
                settings = EnvironmentSettings.for_development()
            elif env_name == ENV_TESTING:
                settings = EnvironmentSettings.for_testing()
            elif env_name == ENV_PRODUCTION:
                settings = EnvironmentSettings.for_production()
            else:
                logger.warning(f"Unknown environment '{env_name}', using development")
                settings = EnvironmentSettings.for_development()
            
            logger.info(f"Loaded {env_name} environment settings")
            return settings
            
        except Exception as e:
            logger.error(f"Failed to load environment settings: {e}")
            logger.info("Falling back to development settings")
            return EnvironmentSettings.for_development()
    
    def get_settings(self) -> EnvironmentSettings:
        """Get current settings"""
        return self._settings
    
    def reload_settings(self) -> None:
        """Reload settings from environment"""
        logger.info("Reloading settings from environment")
        self._settings = self._load_settings()
    
    def update_setting(self, path: str, value: Any) -> None:
        """
        Update a specific setting using dot notation
        
        Args:
            path: Setting path like 'api.network_timeout' or 'cache.enabled'
            value: New value for the setting
        """
        try:
            parts = path.split('.')
            obj = self._settings
            
            # Navigate to the parent object
            for part in parts[:-1]:
                obj = getattr(obj, part)
            
            # Set the final attribute
            setattr(obj, parts[-1], value)
            logger.info(f"Updated setting {path} = {value}")
            
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to update setting {path}: {e}")
            raise ValueError(f"Invalid setting path: {path}")
    
    def get_setting(self, path: str) -> Any:
        """
        Get a specific setting using dot notation
        
        Args:
            path: Setting path like 'api.network_timeout'
            
        Returns:
            Setting value
        """
        try:
            parts = path.split('.')
            obj = self._settings
            
            for part in parts:
                obj = getattr(obj, part)
            
            return obj
            
        except AttributeError as e:
            logger.error(f"Failed to get setting {path}: {e}")
            raise ValueError(f"Invalid setting path: {path}")
    
    def validate_settings(self) -> Dict[str, List[str]]:
        """
        Validate current settings and return any issues
        
        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        issues = {'errors': [], 'warnings': []}
        
        try:
            settings = self._settings
            
            # Validate API settings
            if settings.api.network_timeout <= 0:
                issues['errors'].append("API network timeout must be positive")
            
            if settings.api.network_timeout > 300:  # 5 minutes
                issues['warnings'].append("API network timeout is very high (>5 minutes)")
            
            # Validate cache settings
            if settings.cache.max_size_mb <= 0:
                issues['errors'].append("Cache max size must be positive")
                
            if settings.cache.max_size_mb > 1000:  # 1GB
                issues['warnings'].append("Cache size is very large (>1GB)")
            
            # Validate directories
            for dir_name, dir_path in [
                ('export', settings.export_dir),
                ('data', settings.data_dir),
                ('cache', settings.cache.cache_dir),
                ('log', settings.logging.log_dir)
            ]:
                if not dir_path:
                    issues['errors'].append(f"{dir_name} directory cannot be empty")
            
            # Check API key availability (warnings only)
            if not settings.api.alpha_vantage_key:
                issues['warnings'].append("Alpha Vantage API key not configured")
            if not settings.api.fmp_key:
                issues['warnings'].append("Financial Modeling Prep API key not configured")
            
        except Exception as e:
            issues['errors'].append(f"Settings validation failed: {e}")
        
        return issues


# Global settings manager instance
_settings_manager = SettingsManager()


def get_settings() -> EnvironmentSettings:
    """Get current environment settings"""
    return _settings_manager.get_settings()


def reload_settings() -> None:
    """Reload settings from environment"""
    _settings_manager.reload_settings()


def update_setting(path: str, value: Any) -> None:
    """Update a specific setting"""
    _settings_manager.update_setting(path, value)


def get_setting(path: str) -> Any:
    """Get a specific setting"""
    return _settings_manager.get_setting(path)


def validate_settings() -> Dict[str, List[str]]:
    """Validate current settings"""
    return _settings_manager.validate_settings()


def get_api_config() -> ApiConfig:
    """Get API configuration"""
    return get_settings().api


def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return get_settings().cache


def get_logging_config() -> LoggingConfig:
    """Get logging configuration"""
    return get_settings().logging


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_settings().database


def get_security_config() -> SecurityConfig:
    """Get security configuration"""  
    return get_settings().security


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration"""
    return get_settings().performance


# Environment detection utilities
def is_development() -> bool:
    """Check if running in development environment"""
    return get_settings().environment == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_settings().environment == Environment.TESTING


def is_production() -> bool:
    """Check if running in production environment"""
    return get_settings().environment == Environment.PRODUCTION


def get_current_environment() -> str:
    """Get current environment name"""
    return get_settings().environment.value