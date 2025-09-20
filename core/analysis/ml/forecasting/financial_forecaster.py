"""
Financial Forecaster
====================

Main interface for financial forecasting using machine learning models.
Provides high-level forecasting capabilities that integrate seamlessly
with the existing financial analysis framework.

This module serves as the primary entry point for financial predictions,
coordinating between different forecasting models and providing a unified
interface for predictive analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

# Import existing framework components
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuation
from core.analysis.ddm.ddm_valuation import DDMValuation
from core.data_processing.error_handler import handle_calculation_error

# Import ML components
from ..models.model_manager import MLModelManager, PredictionResult

logger = logging.getLogger(__name__)

@dataclass
class ForecastResult:
    """Comprehensive forecast result with uncertainty quantification"""
    ticker: str
    metric: str
    forecast_values: List[float]
    forecast_periods: List[str]
    confidence_intervals: List[Tuple[float, float]]
    forecast_date: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    accuracy_metrics: Dict[str, float] = field(default_factory=dict)
    assumptions: Dict[str, Any] = field(default_factory=dict)
    risk_factors: List[str] = field(default_factory=list)

@dataclass
class ValuationForecast:
    """Forecast for company valuation metrics"""
    ticker: str
    dcf_forecast: Optional[ForecastResult] = None
    ddm_forecast: Optional[ForecastResult] = None
    fcf_forecast: Optional[ForecastResult] = None
    revenue_forecast: Optional[ForecastResult] = None
    combined_valuation_range: Optional[Tuple[float, float]] = None
    forecast_reliability: float = 0.0

class FinancialForecaster:
    """
    Main interface for financial forecasting using machine learning

    This class provides comprehensive forecasting capabilities for financial
    metrics, integrating with existing valuation models and the ML framework
    to provide predictive insights for investment analysis.

    Features:
    - Revenue and growth forecasting
    - Free cash flow predictions
    - DCF and DDM valuation forecasts
    - Market condition predictions
    - Risk-adjusted forecasting
    - Integration with existing financial calculations
    """

    def __init__(self,
                 financial_calculator: Optional[FinancialCalculator] = None,
                 ml_manager: Optional[MLModelManager] = None):
        """
        Initialize Financial Forecaster

        Parameters:
        -----------
        financial_calculator : FinancialCalculator, optional
            Existing financial calculator for data integration
        ml_manager : MLModelManager, optional
            ML model manager for advanced predictions
        """
        self.financial_calculator = financial_calculator or FinancialCalculator()
        self.ml_manager = ml_manager or MLModelManager(self.financial_calculator)

        # Cache for frequently used data
        self._data_cache: Dict[str, pd.DataFrame] = {}

        logger.info("FinancialForecaster initialized")

    def forecast_fcf(self,
                    ticker: str,
                    periods: int = 5,
                    confidence_level: float = 0.95) -> ForecastResult:
        """
        Forecast Free Cash Flow for specified periods

        Parameters:
        -----------
        ticker : str
            Stock ticker symbol
        periods : int
            Number of periods to forecast
        confidence_level : float
            Confidence level for prediction intervals

        Returns:
        --------
        ForecastResult
            FCF forecast with uncertainty quantification
        """
        try:
            # Get historical FCF data
            historical_data = self._get_historical_fcf_data(ticker)

            if historical_data.empty:
                raise ValueError(f"No historical FCF data available for {ticker}")

            # Feature engineering for FCF prediction
            features = self._engineer_fcf_features(historical_data)

            # Check if we have a trained FCF model, otherwise train one
            fcf_model_id = self._get_or_train_fcf_model(ticker, features)

            # Generate forecasts
            forecast_values = []
            confidence_intervals = []
            forecast_periods = []

            base_date = datetime.now()

            for period in range(1, periods + 1):
                # Prepare features for this forecast period
                period_features = self._prepare_forecast_features(
                    features, period, historical_data
                )

                # Make prediction
                prediction_result = self.ml_manager.predict(fcf_model_id, period_features)

                forecast_values.append(prediction_result.prediction)

                # Calculate confidence interval (simplified approach)
                uncertainty = prediction_result.uncertainty_score or 0.1
                prediction_std = abs(prediction_result.prediction) * uncertainty
                z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%

                ci_lower = prediction_result.prediction - z_score * prediction_std
                ci_upper = prediction_result.prediction + z_score * prediction_std
                confidence_intervals.append((ci_lower, ci_upper))

                # Forecast period label
                forecast_date = base_date + timedelta(days=365 * period)
                forecast_periods.append(f"FY{forecast_date.year}")

            # Calculate accuracy metrics based on historical performance
            accuracy_metrics = self._calculate_forecast_accuracy(fcf_model_id)

            # Identify key assumptions and risk factors
            assumptions = {
                'model_type': 'ML-based FCF prediction',
                'historical_periods': len(historical_data),
                'confidence_level': confidence_level
            }

            risk_factors = [
                'Model based on historical patterns',
                'Economic conditions may change',
                'Company strategy changes not accounted',
                'Market disruptions possible'
            ]

            result = ForecastResult(
                ticker=ticker,
                metric='Free Cash Flow',
                forecast_values=forecast_values,
                forecast_periods=forecast_periods,
                confidence_intervals=confidence_intervals,
                model_used=fcf_model_id,
                accuracy_metrics=accuracy_metrics,
                assumptions=assumptions,
                risk_factors=risk_factors
            )

            logger.info(f"FCF forecast completed for {ticker}: {periods} periods")

            return result

        except Exception as e:
            logger.error(f"Error forecasting FCF for {ticker}: {e}")
            return handle_calculation_error(e, f"FCF forecasting for {ticker}")

    def forecast_valuation(self,
                          ticker: str,
                          forecast_periods: int = 5) -> ValuationForecast:
        """
        Comprehensive valuation forecast combining multiple methods

        Parameters:
        -----------
        ticker : str
            Stock ticker symbol
        forecast_periods : int
            Number of periods for forecast

        Returns:
        --------
        ValuationForecast
            Comprehensive valuation forecast
        """
        try:
            result = ValuationForecast(ticker=ticker)

            # FCF forecast for DCF valuation
            result.fcf_forecast = self.forecast_fcf(ticker, forecast_periods)

            # Revenue forecast
            result.revenue_forecast = self.forecast_revenue(ticker, forecast_periods)

            # DCF valuation forecast
            if result.fcf_forecast:
                result.dcf_forecast = self._forecast_dcf_valuation(
                    ticker, result.fcf_forecast
                )

            # DDM forecast (if applicable)
            try:
                result.ddm_forecast = self._forecast_ddm_valuation(ticker, forecast_periods)
            except Exception as e:
                logger.warning(f"DDM forecast not available for {ticker}: {e}")

            # Combined valuation range
            if result.dcf_forecast and result.fcf_forecast:
                result.combined_valuation_range = self._calculate_combined_valuation_range(
                    result.dcf_forecast, result.ddm_forecast
                )

            # Calculate forecast reliability
            result.forecast_reliability = self._calculate_forecast_reliability(result)

            logger.info(f"Comprehensive valuation forecast completed for {ticker}")

            return result

        except Exception as e:
            logger.error(f"Error in valuation forecast for {ticker}: {e}")
            return handle_calculation_error(e, f"Valuation forecasting for {ticker}")

    def forecast_revenue(self,
                        ticker: str,
                        periods: int = 5,
                        confidence_level: float = 0.95) -> ForecastResult:
        """
        Forecast revenue growth for specified periods

        Parameters:
        -----------
        ticker : str
            Stock ticker symbol
        periods : int
            Number of periods to forecast
        confidence_level : float
            Confidence level for prediction intervals

        Returns:
        --------
        ForecastResult
            Revenue forecast with uncertainty quantification
        """
        try:
            # Get historical revenue data
            historical_data = self._get_historical_revenue_data(ticker)

            if historical_data.empty:
                raise ValueError(f"No historical revenue data available for {ticker}")

            # Simple growth rate forecasting (can be enhanced with ML models)
            revenue_values = historical_data['revenue'].values
            growth_rates = np.diff(revenue_values) / revenue_values[:-1]

            # Calculate average growth rate and volatility
            avg_growth = np.mean(growth_rates)
            growth_volatility = np.std(growth_rates)

            # Generate forecasts
            forecast_values = []
            confidence_intervals = []
            forecast_periods = []

            last_revenue = revenue_values[-1]
            base_date = datetime.now()

            for period in range(1, periods + 1):
                # Apply growth rate with some randomness
                forecasted_revenue = last_revenue * ((1 + avg_growth) ** period)
                forecast_values.append(forecasted_revenue)

                # Confidence intervals based on volatility
                z_score = 1.96 if confidence_level == 0.95 else 2.58
                ci_range = forecasted_revenue * growth_volatility * z_score * np.sqrt(period)

                ci_lower = forecasted_revenue - ci_range
                ci_upper = forecasted_revenue + ci_range
                confidence_intervals.append((ci_lower, ci_upper))

                # Forecast period label
                forecast_date = base_date + timedelta(days=365 * period)
                forecast_periods.append(f"FY{forecast_date.year}")

            result = ForecastResult(
                ticker=ticker,
                metric='Revenue',
                forecast_values=forecast_values,
                forecast_periods=forecast_periods,
                confidence_intervals=confidence_intervals,
                model_used='Growth Rate Model',
                accuracy_metrics={'avg_growth_rate': avg_growth, 'volatility': growth_volatility},
                assumptions={'growth_model': 'Historical average growth rate'},
                risk_factors=['Market conditions', 'Competition', 'Economic factors']
            )

            logger.info(f"Revenue forecast completed for {ticker}: {periods} periods")

            return result

        except Exception as e:
            logger.error(f"Error forecasting revenue for {ticker}: {e}")
            return handle_calculation_error(e, f"Revenue forecasting for {ticker}")

    def _get_historical_fcf_data(self, ticker: str) -> pd.DataFrame:
        """Get historical FCF data from financial calculator"""
        try:
            # Check cache first
            cache_key = f"{ticker}_fcf_historical"
            if cache_key in self._data_cache:
                return self._data_cache[cache_key]

            # Use financial calculator to get FCF data
            if self.financial_calculator:
                # This would integrate with existing data extraction methods
                # For now, create a placeholder structure
                data = pd.DataFrame()  # Placeholder

                self._data_cache[cache_key] = data
                return data

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting historical FCF data for {ticker}: {e}")
            return pd.DataFrame()

    def _get_historical_revenue_data(self, ticker: str) -> pd.DataFrame:
        """Get historical revenue data"""
        try:
            cache_key = f"{ticker}_revenue_historical"
            if cache_key in self._data_cache:
                return self._data_cache[cache_key]

            # Use financial calculator to get revenue data
            if self.financial_calculator:
                # This would integrate with existing data extraction methods
                data = pd.DataFrame()  # Placeholder

                self._data_cache[cache_key] = data
                return data

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting historical revenue data for {ticker}: {e}")
            return pd.DataFrame()

    def _engineer_fcf_features(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for FCF prediction"""
        features = historical_data.copy()

        # Add technical features like moving averages, growth rates, etc.
        if 'fcf' in features.columns:
            features['fcf_growth'] = features['fcf'].pct_change()
            features['fcf_ma_3'] = features['fcf'].rolling(window=3).mean()

        return features.fillna(0)

    def _get_or_train_fcf_model(self, ticker: str, features: pd.DataFrame) -> str:
        """Get existing FCF model or train a new one"""
        # Check for existing model
        existing_models = self.ml_manager.list_models()
        fcf_models = [m for m in existing_models if m['target_variable'] == 'fcf']

        if fcf_models:
            # Use the most recent model
            latest_model = max(fcf_models, key=lambda x: x['training_date'])
            return latest_model['model_id']

        # Train new model if no existing model found
        if len(features) > 10:  # Minimum data requirement
            feature_columns = [col for col in features.columns if col != 'fcf']
            model_id = self.ml_manager.train_financial_predictor(
                target_variable='fcf',
                feature_columns=feature_columns,
                data=features,
                ticker=ticker
            )
            return model_id

        # Fallback: return empty string if can't train
        return ""

    def _prepare_forecast_features(self,
                                 features: pd.DataFrame,
                                 period: int,
                                 historical_data: pd.DataFrame) -> Dict[str, float]:
        """Prepare features for a specific forecast period"""
        # Use the last available data point as base
        if not features.empty:
            last_row = features.iloc[-1]
            return last_row.to_dict()

        return {}

    def _calculate_forecast_accuracy(self, model_id: str) -> Dict[str, float]:
        """Calculate forecast accuracy metrics for a model"""
        if model_id and model_id in self.ml_manager.metadata:
            return self.ml_manager.metadata[model_id].performance_metrics

        return {'accuracy': 0.0, 'r2_score': 0.0}

    def _forecast_dcf_valuation(self,
                               ticker: str,
                               fcf_forecast: ForecastResult) -> ForecastResult:
        """Generate DCF valuation forecast based on FCF predictions"""
        try:
            # Use existing DCF valuation with forecasted FCF values
            dcf_valuator = DCFValuation()

            # Calculate DCF value using forecasted FCF
            # This is a simplified implementation
            discount_rate = 0.10  # Placeholder - should be calculated
            terminal_growth = 0.03  # Placeholder

            dcf_values = []
            for i, fcf in enumerate(fcf_forecast.forecast_values):
                discounted_value = fcf / ((1 + discount_rate) ** (i + 1))
                dcf_values.append(discounted_value)

            # Terminal value calculation
            terminal_fcf = fcf_forecast.forecast_values[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            terminal_value_discounted = terminal_value / ((1 + discount_rate) ** len(fcf_forecast.forecast_values))

            total_dcf_value = sum(dcf_values) + terminal_value_discounted

            result = ForecastResult(
                ticker=ticker,
                metric='DCF Valuation',
                forecast_values=[total_dcf_value],
                forecast_periods=['Total DCF Value'],
                confidence_intervals=[(total_dcf_value * 0.8, total_dcf_value * 1.2)],
                model_used='DCF with ML FCF Forecast',
                assumptions={'discount_rate': discount_rate, 'terminal_growth': terminal_growth}
            )

            return result

        except Exception as e:
            logger.error(f"Error in DCF valuation forecast: {e}")
            return None

    def _forecast_ddm_valuation(self, ticker: str, periods: int) -> ForecastResult:
        """Generate DDM valuation forecast"""
        try:
            # Use existing DDM valuation
            ddm_valuator = DDMValuation()

            # Placeholder implementation
            result = ForecastResult(
                ticker=ticker,
                metric='DDM Valuation',
                forecast_values=[0.0],  # Placeholder
                forecast_periods=['DDM Value'],
                confidence_intervals=[(0.0, 0.0)],
                model_used='DDM Model'
            )

            return result

        except Exception as e:
            logger.error(f"Error in DDM valuation forecast: {e}")
            return None

    def _calculate_combined_valuation_range(self,
                                          dcf_forecast: ForecastResult,
                                          ddm_forecast: Optional[ForecastResult]) -> Tuple[float, float]:
        """Calculate combined valuation range from multiple methods"""
        valuations = []

        if dcf_forecast and dcf_forecast.forecast_values:
            valuations.extend(dcf_forecast.forecast_values)

        if ddm_forecast and ddm_forecast.forecast_values:
            valuations.extend(ddm_forecast.forecast_values)

        if valuations:
            return (min(valuations), max(valuations))

        return (0.0, 0.0)

    def _calculate_forecast_reliability(self, valuation_forecast: ValuationForecast) -> float:
        """Calculate overall forecast reliability score"""
        reliability_factors = []

        # FCF forecast reliability
        if valuation_forecast.fcf_forecast:
            fcf_accuracy = valuation_forecast.fcf_forecast.accuracy_metrics.get('r2_score', 0.0)
            reliability_factors.append(fcf_accuracy)

        # Data availability
        data_quality = 0.8  # Placeholder - should assess actual data quality

        reliability_factors.append(data_quality)

        # Return average reliability
        return np.mean(reliability_factors) if reliability_factors else 0.0