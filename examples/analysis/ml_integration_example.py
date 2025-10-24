"""
ML Integration Example
=====================

Comprehensive example demonstrating how to use the ML integration framework
with the existing financial analysis system.

This example shows:
1. Setting up ML models for financial prediction
2. Training and validating models
3. Making forecasts and predictions
4. Integrating with existing DCF/DDM workflows
5. Model validation and bias testing

Usage:
------
python examples/analysis/ml_integration_example.py
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing financial framework
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.ddm.ddm_valuation import DDMValuator

# Import ML framework
from core.analysis.ml.models.model_manager import MLModelManager
from core.analysis.ml.forecasting.financial_forecaster import FinancialForecaster
from core.analysis.ml.validation.model_validator import ModelValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_financial_data(ticker: str = "DEMO") -> pd.DataFrame:
    """
    Create sample financial data for demonstration

    In real usage, this would come from the FinancialCalculator
    """
    np.random.seed(42)  # For reproducible results

    # Generate 10 years of quarterly data
    periods = 40
    dates = pd.date_range(start='2014-01-01', periods=periods, freq='Q')

    # Base revenue with growth and seasonality
    base_revenue = 1000000000  # $1B starting revenue
    growth_rate = 0.08  # 8% annual growth

    revenue = []
    for i in range(periods):
        # Annual growth with quarterly seasonality
        year_factor = (1 + growth_rate) ** (i / 4)
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 4)  # 10% seasonal variation
        noise_factor = 1 + np.random.normal(0, 0.05)  # 5% random noise

        quarterly_revenue = base_revenue * year_factor * seasonal_factor * noise_factor
        revenue.append(quarterly_revenue)

    # Generate correlated financial metrics
    data = pd.DataFrame({
        'date': dates,
        'revenue': revenue,
        'operating_expenses': [r * np.random.uniform(0.6, 0.8) for r in revenue],
        'depreciation': [r * np.random.uniform(0.03, 0.05) for r in revenue],
        'capex': [r * np.random.uniform(0.04, 0.08) for r in revenue],
        'working_capital_change': [r * np.random.uniform(-0.02, 0.02) for r in revenue],
        'tax_rate': [np.random.uniform(0.21, 0.25) for _ in revenue],
        'stock_price': [50 + i * 2 + np.random.normal(0, 5) for i in range(periods)]
    })

    # Calculate derived metrics
    data['ebit'] = data['revenue'] - data['operating_expenses'] - data['depreciation']
    data['net_income'] = data['ebit'] * (1 - data['tax_rate'])
    data['fcf'] = (data['net_income'] + data['depreciation'] -
                   data['capex'] - data['working_capital_change'])

    # Calculate financial ratios and growth rates
    data['revenue_growth'] = data['revenue'].pct_change()
    data['fcf_growth'] = data['fcf'].pct_change()
    data['margin_ebit'] = data['ebit'] / data['revenue']
    data['margin_net'] = data['net_income'] / data['revenue']

    # Add moving averages as features
    data['revenue_ma_4'] = data['revenue'].rolling(window=4).mean()
    data['fcf_ma_4'] = data['fcf'].rolling(window=4).mean()

    # Clean up missing values
    data = data.fillna(data.median())

    return data

def demonstrate_ml_training():
    """Demonstrate ML model training and validation"""

    logger.info("=== ML Training Demonstration ===")

    # 1. Initialize components
    logger.info("Initializing ML components...")

    # Create financial calculator (in real usage, this would load real data)
    financial_calc = FinancialCalculator()

    # Initialize ML manager
    ml_manager = MLModelManager(financial_calc)

    # Initialize model validator
    validator = ModelValidator()

    # 2. Prepare training data
    logger.info("Preparing training data...")
    sample_data = create_sample_financial_data("DEMO")

    # Define features and target for FCF prediction
    feature_columns = [
        'revenue', 'ebit', 'margin_ebit', 'margin_net',
        'revenue_growth', 'capex', 'working_capital_change',
        'revenue_ma_4'
    ]
    target_variable = 'fcf'

    # Prepare data (remove rows with missing values)
    training_data = sample_data[feature_columns + [target_variable]].dropna()

    logger.info(f"Training data shape: {training_data.shape}")
    logger.info(f"Features: {feature_columns}")
    logger.info(f"Target: {target_variable}")

    # 3. Train ML model
    logger.info("Training FCF prediction model...")

    model_id = ml_manager.train_financial_predictor(
        target_variable=target_variable,
        feature_columns=feature_columns,
        data=training_data,
        ticker="DEMO",
        model_type="random_forest"
    )

    if model_id:
        logger.info(f"Model trained successfully: {model_id}")

        # 4. Validate the model
        logger.info("Performing comprehensive model validation...")

        model = ml_manager.models[model_id]
        X = training_data[feature_columns]
        y = training_data[target_variable]

        validation_result = validator.validate_model(model, X, y, model_id)

        logger.info(f"Validation Score: {validation_result.overall_score:.2f}/100")
        logger.info(f"Model passed validation: {validation_result.passed_validation}")

        if validation_result.issues:
            logger.warning("Validation Issues Found:")
            for issue in validation_result.issues:
                logger.warning(f"  - {issue.issue_type}: {issue.description}")

        if validation_result.recommendations:
            logger.info("Recommendations:")
            for rec in validation_result.recommendations:
                logger.info(f"  - {rec}")

        # 5. Test predictions
        logger.info("Testing model predictions...")

        # Use the last few data points for prediction
        test_features = training_data[feature_columns].iloc[-5:].mean().to_dict()

        prediction_result = ml_manager.predict(model_id, test_features)

        logger.info(f"Sample Prediction: ${prediction_result.prediction:,.0f}")
        if prediction_result.feature_importance:
            logger.info("Top feature importances:")
            sorted_features = sorted(prediction_result.feature_importance.items(),
                                   key=lambda x: x[1], reverse=True)
            for feature, importance in sorted_features[:3]:
                logger.info(f"  - {feature}: {importance:.3f}")

        # 6. Bias testing
        logger.info("Performing bias testing...")

        bias_results = ml_manager.validate_model_bias(model_id, training_data.iloc[-10:])

        if bias_results:
            logger.info(f"Overall bias: {bias_results.get('overall_bias', 0):.6f}")
            logger.info(f"Residual std: {bias_results.get('residual_analysis', {}).get('residual_std', 0):.6f}")

        return model_id

    else:
        logger.error("Model training failed")
        return None

def demonstrate_financial_forecasting():
    """Demonstrate financial forecasting capabilities"""

    logger.info("\n=== Financial Forecasting Demonstration ===")

    # Initialize forecaster
    logger.info("Initializing Financial Forecaster...")

    financial_calc = FinancialCalculator()
    forecaster = FinancialForecaster(financial_calc)

    # For demonstration, we'll create a simplified forecast
    # In real usage, this would integrate with trained models and real data

    logger.info("Creating sample forecast for demonstration...")

    # Simulate a forecast result
    from core.analysis.ml.forecasting.financial_forecaster import ForecastResult

    # Sample FCF forecast
    fcf_forecast = ForecastResult(
        ticker="DEMO",
        metric="Free Cash Flow",
        forecast_values=[500000000, 550000000, 600000000, 650000000, 700000000],
        forecast_periods=["FY2025", "FY2026", "FY2027", "FY2028", "FY2029"],
        confidence_intervals=[
            (450000000, 550000000),
            (500000000, 600000000),
            (550000000, 650000000),
            (600000000, 700000000),
            (650000000, 750000000)
        ],
        model_used="ML-based FCF Prediction",
        accuracy_metrics={"r2_score": 0.85, "mape": 8.5},
        assumptions={"model_type": "Random Forest", "confidence_level": 0.95},
        risk_factors=["Market volatility", "Economic conditions", "Competition"]
    )

    logger.info("FCF Forecast Results:")
    for i, (period, value, ci) in enumerate(zip(fcf_forecast.forecast_periods,
                                               fcf_forecast.forecast_values,
                                               fcf_forecast.confidence_intervals)):
        logger.info(f"  {period}: ${value:,.0f} (CI: ${ci[0]:,.0f} - ${ci[1]:,.0f})")

    # Demonstrate integration with DCF valuation
    logger.info("\nIntegrating forecast with DCF valuation...")

    # Simple DCF calculation using forecasted FCF
    discount_rate = 0.10
    terminal_growth = 0.03

    # Present value of forecasted cash flows
    pv_fcf = sum(fcf / (1 + discount_rate) ** (i + 1)
                 for i, fcf in enumerate(fcf_forecast.forecast_values))

    # Terminal value
    terminal_fcf = fcf_forecast.forecast_values[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / (1 + discount_rate) ** len(fcf_forecast.forecast_values)

    enterprise_value = pv_fcf + pv_terminal

    logger.info(f"PV of Forecast FCF: ${pv_fcf:,.0f}")
    logger.info(f"Terminal Value: ${terminal_value:,.0f}")
    logger.info(f"PV of Terminal Value: ${pv_terminal:,.0f}")
    logger.info(f"Total Enterprise Value: ${enterprise_value:,.0f}")

    return fcf_forecast

def demonstrate_model_monitoring():
    """Demonstrate model performance monitoring"""

    logger.info("\n=== Model Monitoring Demonstration ===")

    # Initialize ML manager
    ml_manager = MLModelManager()

    # List all available models
    logger.info("Available ML Models:")
    models = ml_manager.list_models()

    if not models:
        logger.info("  No models found. Train a model first using demonstrate_ml_training()")
        return

    for model_info in models:
        logger.info(f"  Model ID: {model_info['model_id']}")
        logger.info(f"    Target: {model_info['target_variable']}")
        logger.info(f"    Type: {model_info['model_type']}")
        logger.info(f"    Training Date: {model_info['training_date']}")
        logger.info(f"    Status: {model_info['status']}")

        # Performance metrics
        perf = model_info.get('performance_metrics', {})
        if perf:
            logger.info(f"    Performance: R² = {perf.get('r2', 0):.3f}, "
                       f"RMSE = {perf.get('rmse', 0):.2f}")

        # Bias test results
        bias = model_info.get('bias_test_results', {})
        if bias:
            logger.info(f"    Bias: {bias.get('mean_bias', 0):.6f}")

        logger.info("")

def run_comprehensive_example():
    """Run the complete ML integration example"""

    logger.info("Starting Comprehensive ML Integration Example")
    logger.info("=" * 60)

    try:
        # 1. Model Training and Validation
        model_id = demonstrate_ml_training()

        # 2. Financial Forecasting
        forecast_result = demonstrate_financial_forecasting()

        # 3. Model Monitoring
        demonstrate_model_monitoring()

        logger.info("\n" + "=" * 60)
        logger.info("ML Integration Example Completed Successfully!")

        # Summary
        logger.info("\nSummary:")
        logger.info("✓ ML model training and validation framework")
        logger.info("✓ Financial forecasting capabilities")
        logger.info("✓ Integration with existing DCF/DDM workflows")
        logger.info("✓ Comprehensive model validation and bias testing")
        logger.info("✓ Model performance monitoring")

        logger.info("\nNext Steps:")
        logger.info("- Integrate with real financial data sources")
        logger.info("- Implement additional ML model types")
        logger.info("- Add automated model retraining")
        logger.info("- Enhance forecasting accuracy with ensemble methods")
        logger.info("- Implement production monitoring and alerting")

    except Exception as e:
        logger.error(f"Error in ML integration example: {e}")
        raise

if __name__ == "__main__":
    run_comprehensive_example()