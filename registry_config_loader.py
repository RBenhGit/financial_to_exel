"""
Registry Configuration Loader
============================

This module handles loading and managing configuration for the Universal Data Registry.
It supports YAML configuration files, environment variable overrides, and 
environment-specific settings.

Classes:
    RegistryConfig: Configuration data class
    ConfigLoader: Configuration loading and management
"""

import os
import yaml
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    memory_size_mb: int = 256
    disk_cache_enabled: bool = True
    disk_cache_path: str = "./data_cache"
    default_ttl_seconds: int = 3600
    ttl_by_type: Dict[str, int] = field(default_factory=dict)
    cleanup_interval_hours: int = 24
    max_cache_size_gb: int = 2

@dataclass
class DataSourceConfig:
    """Data source configuration settings"""
    enabled: bool = True
    priority: int = 1
    base_url: str = ""
    api_key_env: Optional[str] = None
    rate_limit: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    supported_types: List[str] = field(default_factory=list)
    company_folder: Optional[str] = None
    validation: str = "standard"

@dataclass
class ValidationConfig:
    """Data validation configuration"""
    default_level: str = "standard"
    quality_threshold: float = 0.8
    min_data_points: int = 3
    rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    default_timeout: int = 30
    max_concurrent_requests: int = 10
    circuit_breaker: Dict[str, Any] = field(default_factory=dict)
    retry: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    file_logging: Dict[str, Any] = field(default_factory=dict)
    structured_logging: Dict[str, Any] = field(default_factory=dict)
    metrics_logging: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegistryConfig:
    """Complete registry configuration"""
    cache: CacheConfig = field(default_factory=CacheConfig)
    data_sources: Dict[str, DataSourceConfig] = field(default_factory=dict)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    development: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    integration: Dict[str, Any] = field(default_factory=dict)

class ConfigLoader:
    """
    Configuration loader for the Universal Data Registry.
    
    Handles loading configuration from YAML files, environment variables,
    and provides environment-specific overrides.
    """
    
    def __init__(self, config_file: str = "registry_config.yaml", 
                 environment: str = None):
        """
        Initialize configuration loader.
        
        Args:
            config_file: Path to the YAML configuration file
            environment: Environment name (development, production, testing)
        """
        self.config_file = config_file
        self.environment = environment or os.getenv('REGISTRY_ENV', 'development')
        self._config_cache = None
        
    def load_config(self, force_reload: bool = False) -> RegistryConfig:
        """
        Load configuration from file and environment.
        
        Args:
            force_reload: Force reload even if config is cached
            
        Returns:
            Complete registry configuration
        """
        if self._config_cache and not force_reload:
            return self._config_cache
        
        try:
            # Load base configuration from YAML
            base_config = self._load_yaml_config()
            
            # Apply environment-specific overrides
            config_dict = self._apply_environment_overrides(base_config)
            
            # Apply environment variable overrides
            config_dict = self._apply_env_var_overrides(config_dict)
            
            # Convert to structured configuration
            config = self._dict_to_config(config_dict)
            
            # Validate configuration
            self._validate_config(config)
            
            # Cache the configuration
            self._config_cache = config
            
            logger.info(f"Configuration loaded successfully for environment: {self.environment}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return default configuration as fallback
            return self._get_default_config()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Configuration file {self.config_file} not found, using defaults")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.debug(f"Loaded configuration from {self.config_file}")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            return {}
    
    def _apply_environment_overrides(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment-specific configuration overrides"""
        config = base_config.copy()
        
        environments = config.get('environments', {})
        env_config = environments.get(self.environment, {})
        
        if env_config:
            logger.debug(f"Applying {self.environment} environment overrides")
            config = self._deep_merge(config, env_config)
        
        return config
    
    def _apply_env_var_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Common environment variable mappings
        env_mappings = {
            'REGISTRY_CACHE_TTL': ('cache', 'default_ttl_seconds'),
            'REGISTRY_CACHE_SIZE': ('cache', 'memory_size_mb'),
            'REGISTRY_LOG_LEVEL': ('logging', 'level'),
            'REGISTRY_DEBUG': ('development', 'debug_mode'),
            'REGISTRY_COMPANY_FOLDER': ('data_sources', 'excel', 'company_folder'),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_value(config, config_path, self._convert_env_value(env_value))
        
        # Handle API keys
        for source_name, source_config in config.get('data_sources', {}).items():
            if isinstance(source_config, dict) and 'api_key_env' in source_config:
                api_key_env = source_config['api_key_env']
                api_key = os.getenv(api_key_env)
                if api_key:
                    source_config['api_key'] = api_key
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _set_nested_value(self, config: Dict[str, Any], path: tuple, value: Any):
        """Set a value in a nested dictionary using a path tuple"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> RegistryConfig:
        """Convert configuration dictionary to structured config object"""
        # Cache configuration
        cache_dict = config_dict.get('cache', {})
        cache_config = CacheConfig(
            memory_size_mb=cache_dict.get('memory_size_mb', 256),
            disk_cache_enabled=cache_dict.get('disk_cache_enabled', True),
            disk_cache_path=cache_dict.get('disk_cache_path', './data_cache'),
            default_ttl_seconds=cache_dict.get('default_ttl_seconds', 3600),
            ttl_by_type=cache_dict.get('ttl_by_type', {}),
            cleanup_interval_hours=cache_dict.get('cleanup_interval_hours', 24),
            max_cache_size_gb=cache_dict.get('max_cache_size_gb', 2)
        )
        
        # Data sources configuration
        data_sources = {}
        sources_dict = config_dict.get('data_sources', {})
        for name, source_dict in sources_dict.items():
            if isinstance(source_dict, dict):
                data_sources[name] = DataSourceConfig(
                    enabled=source_dict.get('enabled', True),
                    priority=source_dict.get('priority', 1),
                    base_url=source_dict.get('base_url', ''),
                    api_key_env=source_dict.get('api_key_env'),
                    rate_limit=source_dict.get('rate_limit', 100),
                    timeout=source_dict.get('timeout', 30),
                    retry_attempts=source_dict.get('retry_attempts', 3),
                    retry_delay=source_dict.get('retry_delay', 1),
                    supported_types=source_dict.get('supported_types', []),
                    company_folder=source_dict.get('company_folder'),
                    validation=source_dict.get('validation', 'standard')
                )
        
        # Validation configuration
        validation_dict = config_dict.get('validation', {})
        validation_config = ValidationConfig(
            default_level=validation_dict.get('default_level', 'standard'),
            quality_threshold=validation_dict.get('quality_threshold', 0.8),
            min_data_points=validation_dict.get('min_data_points', 3),
            rules=validation_dict.get('rules', {})
        )
        
        # Performance configuration
        performance_dict = config_dict.get('performance', {})
        performance_config = PerformanceConfig(
            default_timeout=performance_dict.get('default_timeout', 30),
            max_concurrent_requests=performance_dict.get('max_concurrent_requests', 10),
            circuit_breaker=performance_dict.get('circuit_breaker', {}),
            retry=performance_dict.get('retry', {})
        )
        
        # Logging configuration
        logging_dict = config_dict.get('logging', {})
        logging_config = LoggingConfig(
            level=logging_dict.get('level', 'INFO'),
            file_logging=logging_dict.get('file_logging', {}),
            structured_logging=logging_dict.get('structured_logging', {}),
            metrics_logging=logging_dict.get('metrics_logging', {})
        )
        
        return RegistryConfig(
            cache=cache_config,
            data_sources=data_sources,
            validation=validation_config,
            performance=performance_config,
            logging=logging_config,
            development=config_dict.get('development', {}),
            security=config_dict.get('security', {}),
            integration=config_dict.get('integration', {})
        )
    
    def _validate_config(self, config: RegistryConfig):
        """Validate configuration settings"""
        # Validate cache settings
        if config.cache.memory_size_mb <= 0:
            raise ValueError("Cache memory size must be positive")
        
        if config.cache.default_ttl_seconds <= 0:
            raise ValueError("Default TTL must be positive")
        
        # Validate data source priorities
        priorities = [ds.priority for ds in config.data_sources.values()]
        if len(priorities) != len(set(priorities)):
            logger.warning("Duplicate data source priorities detected")
        
        # Validate validation settings
        if not 0 <= config.validation.quality_threshold <= 1:
            raise ValueError("Quality threshold must be between 0 and 1")
        
        logger.debug("Configuration validation passed")
    
    def _get_default_config(self) -> RegistryConfig:
        """Get default configuration as fallback"""
        logger.info("Using default configuration")
        return RegistryConfig()
    
    def save_config(self, config: RegistryConfig, output_file: str = None):
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration to save
            output_file: Output file path (defaults to original config file)
        """
        output_path = output_file or self.config_file
        
        # Convert config to dictionary
        config_dict = self._config_to_dict(config)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                yaml.dump(config_dict, file, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _config_to_dict(self, config: RegistryConfig) -> Dict[str, Any]:
        """Convert structured config to dictionary"""
        # This is a simplified implementation
        # In practice, you might want to use dataclass serialization
        return {
            'cache': {
                'memory_size_mb': config.cache.memory_size_mb,
                'disk_cache_enabled': config.cache.disk_cache_enabled,
                'disk_cache_path': config.cache.disk_cache_path,
                'default_ttl_seconds': config.cache.default_ttl_seconds,
                'ttl_by_type': config.cache.ttl_by_type,
                'cleanup_interval_hours': config.cache.cleanup_interval_hours,
                'max_cache_size_gb': config.cache.max_cache_size_gb
            },
            'validation': {
                'default_level': config.validation.default_level,
                'quality_threshold': config.validation.quality_threshold,
                'min_data_points': config.validation.min_data_points,
                'rules': config.validation.rules
            },
            'performance': {
                'default_timeout': config.performance.default_timeout,
                'max_concurrent_requests': config.performance.max_concurrent_requests,
                'circuit_breaker': config.performance.circuit_breaker,
                'retry': config.performance.retry
            },
            'logging': {
                'level': config.logging.level,
                'file_logging': config.logging.file_logging,
                'structured_logging': config.logging.structured_logging,
                'metrics_logging': config.logging.metrics_logging
            },
            'development': config.development,
            'security': config.security,
            'integration': config.integration
        }


# Global configuration loader instance
_config_loader = None

def get_config_loader(config_file: str = "registry_config.yaml", 
                     environment: str = None) -> ConfigLoader:
    """Get the global configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_file, environment)
    return _config_loader

def load_registry_config(config_file: str = "registry_config.yaml", 
                        environment: str = None) -> RegistryConfig:
    """Convenience function to load registry configuration"""
    loader = get_config_loader(config_file, environment)
    return loader.load_config()


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    config = load_registry_config()
    
    print(f"Cache TTL: {config.cache.default_ttl_seconds}")
    print(f"Memory size: {config.cache.memory_size_mb} MB")
    print(f"Validation level: {config.validation.default_level}")
    print(f"Data sources: {list(config.data_sources.keys())}")