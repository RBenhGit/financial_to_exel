"""
Financial Forecasting Module
============================

Advanced forecasting capabilities for financial metrics using machine learning
and statistical models. Integrates with existing financial analysis framework
to provide predictive insights for investment decision making.

Classes
-------
FinancialForecaster
    Main interface for financial predictions

TimeSeriesForecaster
    Specialized time series forecasting models

RegressionForecaster
    Regression-based forecasting models

EnsembleForecaster
    Ensemble forecasting combining multiple models
"""

from .financial_forecaster import FinancialForecaster

__all__ = [
    'FinancialForecaster'
]