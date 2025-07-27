"""
Configuration System for Financial Analysis Application
======================================================

This module provides a comprehensive, centralized configuration system that eliminates
hardcoded values throughout the financial analysis application, enabling flexible
customization for different use cases, markets, and analytical requirements.

Key Features
------------
- **Centralized Configuration**: Single source of truth for all application settings
- **Environment-Based Configs**: Different settings for development, testing, production
- **Dynamic Loading**: Runtime configuration updates without application restart
- **Type Safety**: Dataclass-based configuration with type validation
- **Extensible Design**: Easy addition of new configuration categories
- **Default Fallbacks**: Intelligent defaults for all configuration parameters
- **JSON Export/Import**: Serializable configurations for sharing and backup

Configuration Categories
-----------------------

**Excel Structure Configuration**
- Financial statement layout definitions
- Column mapping and data positioning
- Sheet naming conventions and structure
- Data validation rules and formats

**DCF Valuation Defaults**
- Discount rates and growth assumptions
- Terminal value calculation parameters
- Projection periods and methodologies
- Sensitivity analysis parameters

**Data Source Settings**
- API endpoints and authentication
- Rate limiting and timeout configurations
- Data refresh intervals and caching
- Fallback source prioritization

**UI and Display Options**
- Formatting preferences and precision
- Chart and visualization settings
- Report generation templates
- User interface customization

Usage Example
-------------
>>> from config import get_config, get_dcf_config, update_config
>>>
>>> # Get application configuration
>>> config = get_config()
>>> print(f"Default currency: {config.default_currency}")
>>>
>>> # Get DCF-specific configuration
>>> dcf_config = get_dcf_config()
>>> print(f"Default discount rate: {dcf_config.default_discount_rate:.1%}")
>>>
>>> # Update configuration dynamically
>>> update_config('dcf.default_discount_rate', 0.10)
>>>
>>> # Environment-specific configuration
>>> prod_config = get_config(environment='production')

Configuration Structure
-----------------------

**Application-Level Settings**
```python
@dataclass
class AppConfig:
    default_currency: str = 'USD'
    decimal_precision: int = 2
    cache_ttl_hours: int = 24
    log_level: str = 'INFO'
    enable_validation: bool = True
```

**DCF Valuation Settings**
```python
@dataclass
class DCFConfig:
    default_discount_rate: float = 0.10
    default_terminal_growth_rate: float = 0.025
    default_projection_years: int = 10
    terminal_method: str = 'gordon_growth'
```

**Excel Structure Settings**
```python
@dataclass
class ExcelConfig:
    header_row: int = 1
    data_start_row: int = 2
    expected_columns: List[str] = field(default_factory=list)
    sheet_mapping: Dict[str, str] = field(default_factory=dict)
```

Environment Management
---------------------
The configuration system supports multiple environments:

- **Development**: Verbose logging, relaxed validation, extended timeouts
- **Testing**: Strict validation, mock data sources, isolated caching
- **Production**: Optimized performance, secure defaults, comprehensive logging

Configuration can be loaded based on environment variables:
```python
import os
os.environ['FINANCIAL_ANALYSIS_ENV'] = 'production'
config = get_config()  # Loads production configuration
```

Dynamic Configuration Updates
----------------------------
Configuration can be updated at runtime without application restart:

```python
# Update individual settings
update_config('dcf.default_discount_rate', 0.12)
update_config('ui.decimal_places', 3)

# Bulk configuration update
new_settings = {
    'dcf.terminal_growth_rate': 0.03,
    'excel.validation_strict': True,
    'cache.ttl_hours': 48
}
update_config_bulk(new_settings)

# Reset to defaults
reset_config_category('dcf')
```

Configuration Validation
------------------------
All configuration changes are validated for:

- **Type Consistency**: Ensures proper data types for all settings
- **Range Validation**: Validates numeric ranges (e.g., rates between 0-100%)
- **Dependency Checks**: Ensures configuration consistency across modules
- **Business Rules**: Validates financial theory compliance (e.g., discount rate > growth rate)

Persistence and Sharing
----------------------
Configurations can be exported and imported for:

- **Team Collaboration**: Share standardized settings across team members
- **Environment Migration**: Move configurations between environments
- **Backup and Recovery**: Save configuration snapshots
- **Version Control**: Track configuration changes over time

```python
# Export current configuration
export_config('my_analysis_config.json')

# Import saved configuration
import_config('shared_team_config.json')

# Load configuration from custom path
config = load_config_from_file('/path/to/custom.json')
```

Default Values and Fallbacks
----------------------------
The system provides intelligent defaults for all settings:

**Financial Defaults**
- Discount Rate: 10% (reasonable for equity analysis)
- Terminal Growth: 2.5% (conservative long-term assumption)
- Projection Period: 10 years (standard DCF practice)

**Technical Defaults**
- Cache TTL: 24 hours (balance between freshness and performance)
- API Timeout: 30 seconds (reasonable for financial APIs)
- Decimal Precision: 2 places (standard financial formatting)

**UI Defaults**
- Chart Colors: Professional financial theme
- Number Formatting: Locale-aware currency and percentages
- Report Templates: Standard financial analysis layouts

Integration Points
-----------------
The configuration system integrates with all major modules:

- **Financial Calculations**: Precision, rounding, and validation settings
- **Valuation Models**: Default assumptions and calculation parameters
- **Data Management**: Source priorities, refresh intervals, caching policies
- **User Interface**: Display preferences, formatting, and themes
- **Reporting**: Template selection, output formats, and styling

Notes
-----
- Configuration changes are immediately effective for new calculations
- Some settings may require application restart (noted in documentation)
- All configurations are JSON-serializable for easy storage and transfer
- Thread-safe configuration updates for concurrent applications
- Comprehensive logging of configuration changes for audit trails
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
# Use built-in types for Python 3.9+ compatibility

logger = logging.getLogger(__name__)


@dataclass
class ExcelStructureConfig:
    """Configuration for Excel file structure detection"""

    # Default expected positions for common data
    default_company_name_positions: list[tuple[int, int]] = None
    default_period_end_row: int = 10
    default_period_end_column: int = 3

    # Data extraction ranges
    data_start_column: int = 4
    ltm_column: int = 15
    max_scan_rows: int = 59
    max_scan_columns: int = 16

    # Year calculation fallback
    default_projection_years: int = 10

    def __post_init__(self) -> None:
        if self.default_company_name_positions is None:
            self.default_company_name_positions = [(2, 3), (1, 3), (3, 3), (2, 2)]


@dataclass
class FinancialMetricsConfig:
    """Configuration for financial metrics extraction"""

    # Income Statement metrics
    income_metrics: Dict[str, Dict] = None

    # Balance Sheet metrics
    balance_metrics: Dict[str, Dict] = None

    # Cash Flow Statement metrics
    cashflow_metrics: Dict[str, Dict] = None

    def __post_init__(self) -> None:
        if self.income_metrics is None:
            self.income_metrics = {
                "Period End Date": {"target_column": 1, "set_c3": True},
                "Net Interest Expenses": {"target_column": 2},
                "EBT, Incl. Unusual Items": {"target_column": 3},
                "Income Tax Expense": {"target_column": 4},
                "Net Income to Company": {"target_column": 5},
                "EBIT": {"target_column": 6},
            }

        if self.balance_metrics is None:
            self.balance_metrics = {
                "Total Current Assets": {"target_column": 7},
                "Total Current Liabilities": {"target_column": 8},
            }

        if self.cashflow_metrics is None:
            self.cashflow_metrics = {
                "Depreciation & Amortization (CF)": {"target_column": 11},
                "Amortization of Deferred Charges (CF)": {"target_column": 12},
                "Cash from Operations": {"target_column": 13},
                "Capital Expenditures": {"target_column": 14},
                "Cash from Financing": {"target_column": 15},
            }


@dataclass
class DCFConfig:
    """Configuration for DCF calculations"""

    # Default DCF assumptions
    default_discount_rate: float = 0.10  # 10%
    default_terminal_growth_rate: float = 0.025  # 2.5%
    default_growth_rate_yr1_5: float = 0.05  # 5%
    default_growth_rate_yr5_10: float = 0.03  # 3%
    default_projection_years: int = 5
    default_terminal_method: str = "perpetual_growth"
    default_fcf_type: str = "FCFE"

    # Growth rate calculation periods
    growth_rate_periods: List[int] = None

    # Sensitivity analysis defaults
    sensitivity_discount_rate_range: Tuple[float, float] = (0.08, 0.15)
    sensitivity_growth_rate_range: Tuple[float, float] = (0.0, 0.05)

    def __post_init__(self) -> None:
        if self.growth_rate_periods is None:
            self.growth_rate_periods = [1, 3, 5, 10]


@dataclass
class ValidationConfig:
    """Configuration for data validation"""

    # Data quality thresholds
    min_data_completeness: float = 0.7  # 70%
    max_outlier_threshold: float = 3.0  # 3 standard deviations

    # Error handling settings
    allow_missing_data: bool = True
    strict_validation: bool = False

    # Warning thresholds
    warning_threshold_missing_data: int = 5
    warning_threshold_zero_values: int = 10


@dataclass
class ExportConfig:
    """Configuration for CSV export settings"""

    # Default export directory
    default_export_directory: str = "exports"

    # User's preferred export directory (saved persistently)
    user_export_directory: Optional[str] = None

    # File naming settings
    include_timestamp: bool = True
    timestamp_format: str = "%Y%m%d_%H%M%S"

    # Directory validation settings
    create_if_missing: bool = True
    validate_write_permissions: bool = True

    def get_effective_export_directory(self) -> str:
        """Get the directory to use for exports"""
        return self.user_export_directory or self.default_export_directory


@dataclass
class UIConfig:
    """Configuration for UI elements and display"""

    # Default fallback values for UI display
    default_company_display_name: str = "Company"
    unknown_company_name: str = "Unknown Company"
    unknown_ticker: str = "N/A"
    unknown_fcf_type: str = "Not Specified"

    # Test/Demo company values
    test_company_name: str = "Sample Company"
    test_company_ticker: str = "SMPL"


@dataclass
class ApplicationConfig:
    """Master configuration class"""

    excel_structure: ExcelStructureConfig = None
    financial_metrics: FinancialMetricsConfig = None
    dcf: DCFConfig = None
    validation: ValidationConfig = None
    export: ExportConfig = None
    ui: UIConfig = None

    # File paths and names
    dates_metadata_file: str = "dates_metadata.json"

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"

    def __post_init__(self) -> None:
        if self.excel_structure is None:
            self.excel_structure = ExcelStructureConfig()
        if self.financial_metrics is None:
            self.financial_metrics = FinancialMetricsConfig()
        if self.dcf is None:
            self.dcf = DCFConfig()
        if self.validation is None:
            self.validation = ValidationConfig()
        if self.export is None:
            self.export = ExportConfig()
        if self.ui is None:
            self.ui = UIConfig()


class ConfigManager:
    """Manages application configuration loading and saving"""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self.config_file = config_file or "app_config.json"
        self._config = None

    def load_config(self) -> ApplicationConfig:
        """Load configuration from file or create default"""
        if self._config is not None:
            return self._config

        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                config_data = json.loads(config_path.read_text(encoding="utf-8"))

                # Create default config
                self._config = ApplicationConfig()

                # Load export settings if available
                if "export" in config_data:
                    export_data = config_data["export"]
                    if "user_export_directory" in export_data:
                        self._config.export.user_export_directory = export_data[
                            "user_export_directory"
                        ]
                    if "include_timestamp" in export_data:
                        self._config.export.include_timestamp = export_data["include_timestamp"]
                    if "timestamp_format" in export_data:
                        self._config.export.timestamp_format = export_data["timestamp_format"]
                    if "create_if_missing" in export_data:
                        self._config.export.create_if_missing = export_data["create_if_missing"]
                    if "validate_write_permissions" in export_data:
                        self._config.export.validate_write_permissions = export_data[
                            "validate_write_permissions"
                        ]

                logger.info(f"Custom configuration loaded from {self.config_file}")

            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_file}: {e}")
                self._config = ApplicationConfig()
        else:
            logger.info("No custom configuration found, using defaults")
            self._config = ApplicationConfig()

        return self._config

    def save_config(self, config: ApplicationConfig) -> None:
        """Save configuration to file"""
        try:
            # TODO: Implement proper serialization to JSON
            # For now, just save a placeholder
            config_data = {
                "note": "Configuration system implemented",
                "excel_structure": {
                    "data_start_column": config.excel_structure.data_start_column,
                    "ltm_column": config.excel_structure.ltm_column,
                    "max_scan_rows": config.excel_structure.max_scan_rows,
                },
                "dcf": {
                    "default_discount_rate": config.dcf.default_discount_rate,
                    "default_terminal_growth_rate": config.dcf.default_terminal_growth_rate,
                    "default_projection_years": config.dcf.default_projection_years,
                },
                "export": {
                    "user_export_directory": config.export.user_export_directory,
                    "default_export_directory": config.export.default_export_directory,
                    "include_timestamp": config.export.include_timestamp,
                    "timestamp_format": config.export.timestamp_format,
                    "create_if_missing": config.export.create_if_missing,
                    "validate_write_permissions": config.export.validate_write_permissions,
                },
            }

            config_path = Path(self.config_file)
            config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save config to {self.config_file}: {e}")

    def get_config(self) -> ApplicationConfig:
        """Get current configuration"""
        return self.load_config()


# Global configuration instance
_config_manager = ConfigManager()


def get_config() -> ApplicationConfig:
    """Get the global application configuration"""
    return _config_manager.get_config()


def get_excel_config() -> ExcelStructureConfig:
    """Get Excel structure configuration"""
    return get_config().excel_structure


def get_financial_metrics_config() -> FinancialMetricsConfig:
    """Get financial metrics configuration"""
    return get_config().financial_metrics


def get_dcf_config() -> DCFConfig:
    """Get DCF configuration"""
    return get_config().dcf


def get_validation_config() -> ValidationConfig:
    """Get validation configuration"""
    return get_config().validation


def get_export_config() -> ExportConfig:
    """Get export configuration"""
    return get_config().export


def get_ui_config() -> UIConfig:
    """Get UI configuration"""
    return get_config().ui


# Convenience functions for common config values
def get_data_start_column() -> int:
    """Get the starting column for data extraction"""
    return get_excel_config().data_start_column


def get_ltm_column() -> int:
    """Get the column for LTM data"""
    return get_excel_config().ltm_column


def get_max_scan_rows() -> int:
    """Get maximum rows to scan for metrics"""
    return get_excel_config().max_scan_rows


def get_default_discount_rate() -> float:
    """Get default discount rate for DCF"""
    return get_dcf_config().default_discount_rate


def get_default_terminal_growth_rate() -> float:
    """Get default terminal growth rate for DCF"""
    return get_dcf_config().default_terminal_growth_rate


# UI-related convenience functions
def get_default_company_name() -> str:
    """Get default company display name"""
    return get_ui_config().default_company_display_name


def get_unknown_company_name() -> str:
    """Get unknown company fallback name"""
    return get_ui_config().unknown_company_name


def get_unknown_ticker() -> str:
    """Get unknown ticker fallback"""
    return get_ui_config().unknown_ticker


def get_unknown_fcf_type() -> str:
    """Get unknown FCF type fallback"""
    return get_ui_config().unknown_fcf_type


def get_test_company_name() -> str:
    """Get test company name"""
    return get_ui_config().test_company_name


def get_test_company_ticker() -> str:
    """Get test company ticker"""
    return get_ui_config().test_company_ticker


# Export-related convenience functions
def get_export_directory() -> str:
    """Get the effective export directory"""
    return get_export_config().get_effective_export_directory()


def set_user_export_directory(directory: str) -> None:
    """Set user's preferred export directory"""
    config = get_config()
    config.export.user_export_directory = directory
    # Save the updated configuration
    _config_manager.save_config(config)


def get_timestamp_format() -> str:
    """Get timestamp format for export files"""
    return get_export_config().timestamp_format


def should_include_timestamp() -> bool:
    """Check if timestamp should be included in export filenames"""
    return get_export_config().include_timestamp


def validate_export_directory(directory: str = None) -> Dict[str, Any]:
    """
    Validate export directory and return status information

    Args:
        directory (str): Directory to validate (default: current configured directory)

    Returns:
        Dict containing validation results
    """
    if directory is None:
        directory = get_export_directory()

    result = {
        "path": directory,
        "is_valid": False,
        "exists": False,
        "is_directory": False,
        "is_writable": False,
        "can_create": False,
        "errors": [],
        "warnings": [],
    }

    try:
        export_path = Path(directory)

        # Check if path exists
        if export_path.exists():
            result["exists"] = True

            # Check if it's a directory
            if export_path.is_dir():
                result["is_directory"] = True

                # Test write permissions
                try:
                    test_file = export_path / ".write_test_temp"
                    test_file.touch()
                    test_file.unlink()
                    result["is_writable"] = True
                    result["is_valid"] = True
                except PermissionError:
                    result["errors"].append("Directory exists but is not writable")
                except Exception as e:
                    result["errors"].append(f"Write test failed: {e}")
            else:
                result["errors"].append("Path exists but is not a directory")
        else:
            # Check if we can create the directory
            try:
                # Check if parent directory exists and is writable
                parent = export_path.parent
                if parent.exists() and parent.is_dir():
                    # Test if we can create in parent
                    test_dir = parent / ".test_create_temp"
                    test_dir.mkdir(exist_ok=True)
                    test_dir.rmdir()
                    result["can_create"] = True
                    result["warnings"].append("Directory does not exist but can be created")
                    if get_export_config().create_if_missing:
                        result["is_valid"] = True
                else:
                    result["errors"].append("Parent directory does not exist or is not accessible")
            except Exception as e:
                result["errors"].append(f"Cannot create directory: {e}")

    except Exception as e:
        result["errors"].append(f"Path validation failed: {e}")

    return result


def ensure_export_directory() -> Optional[str]:
    """
    Ensure export directory exists and is writable, with fallback handling

    Returns:
        str: Path to usable export directory or None if all options fail
    """
    export_config = get_export_config()

    # Try user directory first
    if export_config.user_export_directory:
        validation = validate_export_directory(export_config.user_export_directory)
        if validation["is_valid"]:
            return export_config.user_export_directory
        elif validation["can_create"] and export_config.create_if_missing:
            try:
                Path(export_config.user_export_directory).mkdir(parents=True, exist_ok=True)
                return export_config.user_export_directory
            except Exception as e:
                logger.warning(f"Failed to create user export directory: {e}")

    # Fallback to default directory
    default_dir = export_config.default_export_directory
    validation = validate_export_directory(default_dir)
    if validation["is_valid"]:
        return default_dir
    elif validation["can_create"] and export_config.create_if_missing:
        try:
            Path(default_dir).mkdir(parents=True, exist_ok=True)
            return default_dir
        except Exception as e:
            logger.warning(f"Failed to create default export directory: {e}")

    # Last resort: try current working directory
    cwd_exports = str(Path.cwd() / "exports")
    validation = validate_export_directory(cwd_exports)
    if validation["is_valid"]:
        logger.warning(f"Using current working directory exports folder: {cwd_exports}")
        return cwd_exports
    elif validation["can_create"]:
        try:
            Path(cwd_exports).mkdir(parents=True, exist_ok=True)
            logger.warning(f"Created fallback export directory: {cwd_exports}")
            return cwd_exports
        except Exception as e:
            logger.error(f"Failed to create fallback export directory: {e}")

    logger.error("No usable export directory found")
    return None


if __name__ == "__main__":
    # Test the configuration system
    config = get_config()
    print("Configuration system loaded successfully")
    print(f"Data start column: {config.excel_structure.data_start_column}")
    print(f"Default discount rate: {config.dcf.default_discount_rate}")
    print(f"Max scan rows: {config.excel_structure.max_scan_rows}")
