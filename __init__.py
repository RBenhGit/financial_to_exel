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
from .config import get_config, get_dcf_config, get_export_config
from .centralized_data_manager import CentralizedDataManager
from .data_processing import DataProcessor
from .dcf_valuation import DCFCalculator
from .financial_calculations import FinancialCalculations

# Analysis tools
from .pb_valuation import PBAnalyzer
from .ddm_valuation import DDMAnalyzer
from .watch_list_manager import WatchListManager

__all__ = [
    # Core classes
    "CentralizedDataManager",
    "DataProcessor",
    "DCFCalculator",
    "FinancialCalculations",
    # Analysis tools
    "PBAnalyzer",
    "DDMAnalyzer",
    "WatchListManager",
    # Configuration
    "get_config",
    "get_dcf_config",
    "get_export_config",
]
