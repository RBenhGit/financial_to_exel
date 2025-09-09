"""
Financial Analysis Package
=========================

A comprehensive financial analysis package for DCF valuation, FCF analysis,
and financial data processing.

Core Modules:
    config: Configuration management system
    data_processing: Data loading and processing utilities
    centralized_data_manager: Unified data management
    dcf_valuation: DCF valuation calculations
    financial_calculations: Core financial calculation functions
    fcf_analysis_streamlit: Streamlit web interface

Analysis Modules:
    pb_valuation: Price-to-Book analysis
    ddm_valuation: Dividend Discount Model
    watch_list_manager: Portfolio and watch list management

Data Sources:
    yfinance_converter: Yahoo Finance data adapter
    alpha_vantage_converter: Alpha Vantage data adapter
    fmp_converter: Financial Modeling Prep adapter
    polygon_converter: Polygon.io data adapter

Utilities:
    input_validator: Data validation utilities
    error_handler: Error handling and logging
    yfinance_logger: Detailed API logging
"""

__version__ = "1.0.1"
__author__ = "Financial Analysis Team"

# Core imports for easy access
from .config.config import get_config, get_dcf_config, get_export_config
from .core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from .core.data_processing.processors.data_processing import DataProcessor
from .core.analysis.dcf.dcf_valuation import DCFValuator
from .core.analysis.engines.financial_calculations import FinancialCalculator

# Analysis tools
from .core.analysis.pb.pb_valuation import PBValuator
from .core.analysis.ddm.ddm_valuation import DDMValuator
from .core.data_processing.managers.watch_list_manager import WatchListManager

__all__ = [
    # Core classes
    "CentralizedDataManager",
    "DataProcessor",
    "DCFValuator",
    "FinancialCalculator",
    # Analysis tools
    "PBValuator",
    "DDMValuator",
    "WatchListManager",
    # Configuration
    "get_config",
    "get_dcf_config",
    "get_export_config",
]
