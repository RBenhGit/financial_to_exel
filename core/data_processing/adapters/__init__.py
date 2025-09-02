"""
Data Processing Adapters Module
==============================

This module contains data source adapters that bridge different data formats
into the standardized VarInputData storage system.

Available Adapters:
------------------
- ExcelDataAdapter: Extract financial variables from Excel files
- YFinanceAdapter: Extract financial variables from Yahoo Finance API
- FMPAdapter: Extract financial variables from Financial Modeling Prep API
- AlphaVantageAdapter: Extract financial variables from Alpha Vantage API
- PolygonAdapter: Extract financial variables from Polygon.io API

Multi-API System:
-----------------
- MultiApiManager: Intelligent fallback system managing all API adapters
- BaseApiAdapter: Abstract base class for all API adapters
- Data quality scoring and automatic source selection
"""

# Base adapter interface
from .base_adapter import (
    BaseApiAdapter,
    DataSourceType,
    DataCategory,
    ExtractionResult,
    DataQualityMetrics,
    ApiCapabilities
)

# Individual adapters
from .excel_adapter import ExcelDataAdapter
from .yfinance_adapter import (
    YFinanceAdapter,
    YFinanceExtractionResult,
    YFinanceDataQuality,
    load_yfinance_data,
    check_yfinance_availability,
    get_yfinance_adapter_stats
)
from .fmp_adapter import (
    FMPAdapter,
    load_fmp_data,
    check_fmp_availability,
    get_fmp_adapter_stats
)
from .alpha_vantage_adapter import (
    AlphaVantageAdapter,
    load_alpha_vantage_data,
    check_alpha_vantage_availability,
    get_alpha_vantage_adapter_stats
)
from .polygon_adapter import (
    PolygonAdapter,
    load_polygon_data,
    check_polygon_availability,
    get_polygon_adapter_stats
)

# Multi-API management system
from .multi_api_manager import (
    MultiApiManager,
    MultiApiResult,
    SourceSelectionStrategy,
    SourcePriority,
    create_default_manager,
    load_symbol_with_fallback,
    get_all_adapter_stats
)

__all__ = [
    # Base adapter interface
    'BaseApiAdapter',
    'DataSourceType',
    'DataCategory',
    'ExtractionResult',
    'DataQualityMetrics',
    'ApiCapabilities',
    
    # Excel Adapter
    'ExcelDataAdapter',
    
    # YFinance Adapter
    'YFinanceAdapter',
    'YFinanceExtractionResult',
    'YFinanceDataQuality',
    'load_yfinance_data',
    'check_yfinance_availability',
    'get_yfinance_adapter_stats',
    
    # FMP Adapter
    'FMPAdapter',
    'load_fmp_data',
    'check_fmp_availability',
    'get_fmp_adapter_stats',
    
    # Alpha Vantage Adapter
    'AlphaVantageAdapter',
    'load_alpha_vantage_data',
    'check_alpha_vantage_availability',
    'get_alpha_vantage_adapter_stats',
    
    # Polygon Adapter
    'PolygonAdapter',
    'load_polygon_data',
    'check_polygon_availability',
    'get_polygon_adapter_stats',
    
    # Multi-API Manager
    'MultiApiManager',
    'MultiApiResult',
    'SourceSelectionStrategy',
    'SourcePriority',
    'create_default_manager',
    'load_symbol_with_fallback',
    'get_all_adapter_stats'
]