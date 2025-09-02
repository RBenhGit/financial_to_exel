"""
Core Data Processing Module
===========================

This package contains the core data processing components for financial analysis,
including variable registry, data contracts, validation, and processing pipelines.
"""

# Import key classes for easy access
from .financial_variable_registry import (
    FinancialVariableRegistry,
    VariableDefinition,
    VariableCategory,
    DataType,
    Units,
    ValidationRule,
    get_registry
)

from .data_contracts import (
    FinancialStatement,
    MarketData,
    CalculationResult,
    DataQuality,
    DataSourceType,
    PeriodType,
    CurrencyCode,
    DataQualityMetrics,
    MetadataInfo
)

__all__ = [
    # Variable Registry
    'FinancialVariableRegistry',
    'VariableDefinition', 
    'VariableCategory',
    'DataType',
    'Units',
    'ValidationRule',
    'get_registry',
    
    # Data Contracts
    'FinancialStatement',
    'MarketData',
    'CalculationResult',
    'DataQuality',
    'DataSourceType', 
    'PeriodType',
    'CurrencyCode',
    'DataQualityMetrics',
    'MetadataInfo'
]