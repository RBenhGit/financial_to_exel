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

from .composite_variable_registry import (
    CompositeVariableRegistry,
    CalculationFormula,
    create_standard_formula_registry,
    create_standard_dependency_graph,
    create_standard_calculator
)

from .composite_variable_dependency_graph import (
    CompositeVariableDependencyGraph,
    VariableNode
)

from .composite_variable_calculator import (
    CompositeVariableCalculator,
    CalculationContext,
    CalculationResult as CompositeCalculationResult
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
    'MetadataInfo',

    # Composite Variables
    'CompositeVariableRegistry',
    'CalculationFormula',
    'create_standard_formula_registry',
    'create_standard_dependency_graph',
    'create_standard_calculator',
    'CompositeVariableDependencyGraph',
    'VariableNode',
    'CompositeVariableCalculator',
    'CalculationContext',
    'CompositeCalculationResult'
]