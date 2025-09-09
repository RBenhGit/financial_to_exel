"""
Configuration Package for Financial Analysis Application
=======================================================

This package provides centralized configuration management with support for:
- Environment-specific settings (development, testing, production)
- Constants and magic number elimination
- Runtime configuration updates
- Settings validation

Main Components:
- constants.py: All hardcoded values and magic numbers
- settings.py: Environment-based configuration management
- Legacy config.py integration for backward compatibility

Usage:
    from config import get_settings, get_api_config
    from config.constants import DEFAULT_DISCOUNT_RATE
    
    settings = get_settings()
    api_config = get_api_config()
"""

# Import key components for easy access
from .constants import *
from .settings import (
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
    update_setting,
    get_setting,
    validate_settings,
    reload_settings
)

# For backward compatibility with existing code that imports from config.py
# Re-export the legacy functions from parent directory config.py
try:
    import sys
    import importlib.util
    from pathlib import Path
    
    config_py_path = Path(__file__).parent / "config.py"
    spec = importlib.util.spec_from_file_location("legacy_config", config_py_path)
    legacy_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_config)
    
    # Import from the loaded module
    get_config = legacy_config.get_config
    get_dcf_config = legacy_config.get_dcf_config
    get_excel_config = legacy_config.get_excel_config
    get_financial_metrics_config = legacy_config.get_financial_metrics_config
    get_validation_config = legacy_config.get_validation_config
    get_export_config = legacy_config.get_export_config
    get_ui_config = legacy_config.get_ui_config
    get_default_company_name = legacy_config.get_default_company_name
    get_unknown_company_name = legacy_config.get_unknown_company_name
    get_unknown_ticker = legacy_config.get_unknown_ticker
    get_export_directory = legacy_config.get_export_directory
    set_user_export_directory = legacy_config.set_user_export_directory
    ensure_export_directory = legacy_config.ensure_export_directory
    get_data_start_column = legacy_config.get_data_start_column
    get_ltm_column = legacy_config.get_ltm_column
    get_max_scan_rows = legacy_config.get_max_scan_rows
    get_default_discount_rate = legacy_config.get_default_discount_rate
    get_default_terminal_growth_rate = legacy_config.get_default_terminal_growth_rate
    get_unknown_fcf_type = legacy_config.get_unknown_fcf_type
    get_test_company_name = legacy_config.get_test_company_name
    get_test_company_ticker = legacy_config.get_test_company_ticker
    get_timestamp_format = legacy_config.get_timestamp_format
    ApplicationConfig = legacy_config.ApplicationConfig
    DCFConfig = legacy_config.DCFConfig
    ExcelStructureConfig = legacy_config.ExcelStructureConfig
    FinancialMetricsConfig = legacy_config.FinancialMetricsConfig
    ValidationConfig = legacy_config.ValidationConfig
    ExportConfig = legacy_config.ExportConfig
    UIConfig = legacy_config.UIConfig
    ConfigManager = legacy_config.ConfigManager
    
    # Mark as available for import
    __all__ = [
        # New configuration system
        'get_settings',
        'get_api_config',
        'get_cache_config',
        'get_logging_config', 
        'get_database_config',
        'get_security_config',
        'get_performance_config',
        'is_development',
        'is_testing',
        'is_production',
        'get_current_environment',
        'update_setting',
        'get_setting',
        'validate_settings',
        'reload_settings',
        
        # Legacy configuration (backward compatibility)
        'get_config',
        'get_dcf_config',
        'get_excel_config',
        'get_financial_metrics_config',
        'get_validation_config',
        'get_export_config',
        'get_ui_config',
        'get_default_company_name',
        'get_unknown_company_name',
        'get_unknown_ticker',
        'get_export_directory',
        'set_user_export_directory',
        'ensure_export_directory',
        'get_data_start_column',
        'get_ltm_column',
        'get_max_scan_rows',
        'get_default_discount_rate',
        'get_default_terminal_growth_rate',
        'get_unknown_fcf_type',
        'get_test_company_name',
        'get_test_company_ticker',
        'get_timestamp_format',
        'ApplicationConfig',
        'DCFConfig',
        'ExcelStructureConfig',
        'FinancialMetricsConfig',
        'ValidationConfig',
        'ExportConfig',
        'UIConfig',
        'ConfigManager'
    ]
    
except ImportError as e:
    # If legacy config.py is not available or has issues
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Legacy config.py import failed: {e}")
    
    # Provide minimal compatibility
    __all__ = [
        'get_settings',
        'get_api_config', 
        'get_cache_config',
        'get_logging_config',
        'get_database_config', 
        'get_security_config',
        'get_performance_config',
        'is_development',
        'is_testing',
        'is_production',
        'get_current_environment',
        'update_setting',
        'get_setting',
        'validate_settings',
        'reload_settings'
    ]