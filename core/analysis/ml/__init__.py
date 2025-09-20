"""
Machine Learning Integration Module
==================================

This module provides machine learning capabilities for predictive financial analysis,
integrating with the existing financial analysis framework to provide advanced
forecasting and pattern recognition capabilities.

Key Features
------------
- **Predictive Financial Modeling**: ML models for financial metric forecasting
- **Pattern Recognition**: Anomaly detection and trend analysis
- **Model Validation**: Comprehensive validation and bias testing framework
- **Integration Layer**: Seamless integration with existing financial calculations
- **Performance Monitoring**: Model performance tracking and alerting

Sub-modules
-----------
models/
    Core ML model implementations and training pipelines

validation/
    Model validation, testing, and bias detection framework

forecasting/
    Financial forecasting models and prediction engines

feature_engineering/
    Financial feature extraction and engineering utilities

integration/
    Integration layer with existing financial analysis components

Classes
-------
MLModelManager
    Central manager for ML model lifecycle and deployment

FinancialForecaster
    Main interface for financial prediction tasks

ModelValidator
    Comprehensive model validation and testing framework
"""

from .models import MLModelManager
from .forecasting import FinancialForecaster
from .validation import ModelValidator

__all__ = [
    'MLModelManager',
    'FinancialForecaster',
    'ModelValidator'
]