"""
Configuration System for Financial Analysis Application

This module provides centralized configuration to replace hardcoded values
throughout the application, making it more flexible and maintainable.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExcelStructureConfig:
    """Configuration for Excel file structure detection"""
    # Default expected positions for common data
    default_company_name_positions: List[Tuple[int, int]] = None
    default_period_end_row: int = 10
    default_period_end_column: int = 3
    
    # Data extraction ranges
    data_start_column: int = 4
    ltm_column: int = 15
    max_scan_rows: int = 59
    max_scan_columns: int = 16
    
    # Year calculation fallback
    default_projection_years: int = 10
    
    def __post_init__(self):
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
    
    def __post_init__(self):
        if self.income_metrics is None:
            self.income_metrics = {
                "Period End Date": {"target_column": 1, "set_c3": True},
                "Net Interest Expenses": {"target_column": 2},
                "EBT, Incl. Unusual Items": {"target_column": 3},
                "Income Tax Expense": {"target_column": 4},
                "Net Income to Company": {"target_column": 5},
                "EBIT": {"target_column": 6}
            }
        
        if self.balance_metrics is None:
            self.balance_metrics = {
                "Total Current Assets": {"target_column": 7},
                "Total Current Liabilities": {"target_column": 8}
            }
        
        if self.cashflow_metrics is None:
            self.cashflow_metrics = {
                "Depreciation & Amortization (CF)": {"target_column": 11},
                "Amortization of Deferred Charges (CF)": {"target_column": 12},
                "Cash from Operations": {"target_column": 13},
                "Capital Expenditures": {"target_column": 14},
                "Cash from Financing": {"target_column": 15}
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
    default_terminal_method: str = 'perpetual_growth'
    default_fcf_type: str = 'FCFE'
    
    # Growth rate calculation periods
    growth_rate_periods: List[int] = None
    
    # Sensitivity analysis defaults
    sensitivity_discount_rate_range: Tuple[float, float] = (0.08, 0.15)
    sensitivity_growth_rate_range: Tuple[float, float] = (0.0, 0.05)
    
    def __post_init__(self):
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
    ui: UIConfig = None
    
    # File paths and names
    dates_metadata_file: str = "dates_metadata.json"
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        if self.excel_structure is None:
            self.excel_structure = ExcelStructureConfig()
        if self.financial_metrics is None:
            self.financial_metrics = FinancialMetricsConfig()
        if self.dcf is None:
            self.dcf = DCFConfig()
        if self.validation is None:
            self.validation = ValidationConfig()
        if self.ui is None:
            self.ui = UIConfig()

class ConfigManager:
    """Manages application configuration loading and saving"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "app_config.json"
        self._config = None
    
    def load_config(self) -> ApplicationConfig:
        """Load configuration from file or create default"""
        if self._config is not None:
            return self._config
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # TODO: Implement proper deserialization from JSON
                # For now, use defaults and log that custom config was found
                logger.info(f"Custom configuration found at {self.config_file}")
                self._config = ApplicationConfig()
                
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_file}: {e}")
                self._config = ApplicationConfig()
        else:
            logger.info("No custom configuration found, using defaults")
            self._config = ApplicationConfig()
        
        return self._config
    
    def save_config(self, config: ApplicationConfig):
        """Save configuration to file"""
        try:
            # TODO: Implement proper serialization to JSON
            # For now, just save a placeholder
            config_data = {
                "note": "Configuration system implemented",
                "excel_structure": {
                    "data_start_column": config.excel_structure.data_start_column,
                    "ltm_column": config.excel_structure.ltm_column,
                    "max_scan_rows": config.excel_structure.max_scan_rows
                },
                "dcf": {
                    "default_discount_rate": config.dcf.default_discount_rate,
                    "default_terminal_growth_rate": config.dcf.default_terminal_growth_rate,
                    "default_projection_years": config.dcf.default_projection_years
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
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

if __name__ == "__main__":
    # Test the configuration system
    config = get_config()
    print("Configuration system loaded successfully")
    print(f"Data start column: {config.excel_structure.data_start_column}")
    print(f"Default discount rate: {config.dcf.default_discount_rate}")
    print(f"Max scan rows: {config.excel_structure.max_scan_rows}")