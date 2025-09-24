"""
End-to-end integration tests for ML forecasting pipeline.

Tests the complete ML workflow from data loading through prediction and validation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine
from core.analysis.ml.forecasting.financial_forecaster import FinancialForecaster
from core.analysis.ml.models.model_manager import MLModelManager
from core.analysis.ml.validation.model_validator import ModelValidator
from core.analysis.ml.automation.model_retraining_pipeline import ModelRetrainingPipeline
from core.analysis.ml.ensemble.ensemble_predictor import EnsemblePredictor


class TestMLEndToEnd:
    """End-to-end tests for ML integration pipeline."""

    @pytest.fixture
    def sample_financial_data(self):
        """Create sample financial data for testing."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='Q')
        return pd.DataFrame({
            'date': dates,
            'fcf': np.random.uniform(1000, 5000, len(dates)),
            'revenue': np.random.uniform(10000, 50000, len(dates)),
            'net_income': np.random.uniform(500, 2500, len(dates)),
            'capex': np.random.uniform(200, 1000, len(dates)),
            'working_capital_change': np.random.uniform(-500, 500, len(dates))
        })

    @pytest.fixture
    def mock_financial_calculator(self, sample_financial_data):
        """Create mock financial calculator with sample data."""
        calculator = Mock(spec=FinancialCalculationEngine)

        # Mock FCF calculation results
        fcf_results = {
            'consolidated': {
                'operating_cash_flow': sample_financial_data['fcf'].iloc[-1] + 500,
                'capex': sample_financial_data['capex'].iloc[-1],
                'fcf': sample_financial_data['fcf'].iloc[-1]
            }
        }
        calculator.calculate_all_fcf_types.return_value = fcf_results

        # Mock financial statements data
        calculator.income_statements = sample_financial_data[['date', 'revenue', 'net_income']].copy()
        calculator.cash_flow_statements = sample_financial_data[['date', 'fcf', 'capex']].copy()
        calculator.balance_sheets = sample_financial_data[['date', 'working_capital_change']].copy()

        return calculator

    @pytest.fixture
    def financial_forecaster(self, mock_financial_calculator):
        """Create financial forecaster with mock calculator."""
        return FinancialForecaster(financial_calculator=mock_financial_calculator)

    def test_complete_forecasting_workflow(self, financial_forecaster, sample_financial_data):
        """Test complete forecasting workflow from data to prediction."""
        ticker = "TEST"

        # Test data loading and preprocessing
        fcf_data = financial_forecaster._get_historical_fcf_data(ticker)
        assert isinstance(fcf_data, pd.DataFrame)
        assert not fcf_data.empty
        assert 'fcf' in fcf_data.columns

        # Test model training
        model, metrics = financial_forecaster.train_fcf_model(ticker, periods=8)
        assert model is not None
        assert isinstance(metrics, dict)
        assert 'r2_score' in metrics
        assert 'mse' in metrics

        # Test prediction
        predictions = financial_forecaster.forecast_fcf(ticker, periods=4)
        assert isinstance(predictions, dict)
        assert 'predictions' in predictions
        assert 'confidence_intervals' in predictions
        assert len(predictions['predictions']) == 4

    def test_model_validation_workflow(self, financial_forecaster):
        """Test model validation and bias testing."""
        ticker = "TEST"

        # Train model
        model, _ = financial_forecaster.train_fcf_model(ticker, periods=8)

        # Create validator
        validator = ModelValidator()

        # Test cross-validation
        cv_results = validator.cross_validate_model(model, financial_forecaster._get_historical_fcf_data(ticker))
        assert isinstance(cv_results, dict)
        assert 'mean_score' in cv_results
        assert 'std_score' in cv_results

        # Test bias testing
        bias_results = validator.test_model_bias(model, financial_forecaster._get_historical_fcf_data(ticker))
        assert isinstance(bias_results, dict)
        assert 'bias_detected' in bias_results

    def test_ensemble_prediction_workflow(self, financial_forecaster):
        """Test ensemble prediction workflow."""
        ticker = "TEST"

        # Train multiple models
        models = []
        for i in range(3):
            model, _ = financial_forecaster.train_fcf_model(ticker, periods=8)
            models.append(model)

        # Create ensemble predictor
        ensemble = EnsemblePredictor(models)

        # Test ensemble prediction
        test_data = financial_forecaster._get_historical_fcf_data(ticker).tail(4)
        predictions = ensemble.predict_ensemble(test_data)

        assert isinstance(predictions, dict)
        assert 'ensemble_prediction' in predictions
        assert 'confidence_score' in predictions
        assert 'individual_predictions' in predictions

    @pytest.mark.slow
    def test_automated_retraining_workflow(self, financial_forecaster):
        """Test automated retraining pipeline."""
        ticker = "TEST"

        # Create temporary model storage
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "models"
            model_dir.mkdir()

            # Train initial model
            initial_model, _ = financial_forecaster.train_fcf_model(ticker, periods=8)

            # Create retraining pipeline
            pipeline = ModelRetrainingPipeline(
                model_storage_path=str(model_dir),
                performance_threshold=0.8
            )

            # Test pipeline initialization
            pipeline.initialize_model(ticker, initial_model)

            # Test performance monitoring
            current_data = financial_forecaster._get_historical_fcf_data(ticker)
            needs_retraining = pipeline.should_retrain_model(ticker, current_data)
            assert isinstance(needs_retraining, bool)

            # Test retraining if needed
            if needs_retraining:
                retrained_model = pipeline.retrain_model(ticker, current_data)
                assert retrained_model is not None

    def test_ml_ui_data_integration(self, financial_forecaster):
        """Test that ML UI components can integrate with financial data."""
        ticker = "TEST"

        # Simulate UI data requests
        fcf_data = financial_forecaster._get_historical_fcf_data(ticker)
        revenue_data = financial_forecaster._get_historical_revenue_data(ticker)

        # Verify data format for UI consumption
        assert isinstance(fcf_data, pd.DataFrame)
        assert isinstance(revenue_data, pd.DataFrame)
        assert not fcf_data.empty
        assert not revenue_data.empty

        # Test model training for UI
        model, metrics = financial_forecaster.train_fcf_model(ticker, periods=8)
        assert 'r2_score' in metrics
        assert 'mse' in metrics
        assert 'mae' in metrics

        # Test forecasting for UI
        forecast_results = financial_forecaster.forecast_fcf(ticker, periods=4)
        assert 'predictions' in forecast_results
        assert 'confidence_intervals' in forecast_results
        assert len(forecast_results['predictions']) == 4

    def test_error_handling_and_fallbacks(self, financial_forecaster):
        """Test error handling and fallback mechanisms."""
        # Test with invalid ticker
        with pytest.raises(Exception):
            financial_forecaster.train_fcf_model("INVALID_TICKER", periods=8)

        # Test with insufficient data
        try:
            # This should handle gracefully or raise informative error
            financial_forecaster.train_fcf_model("TEST", periods=100)
        except Exception as e:
            assert "insufficient data" in str(e).lower() or "not enough" in str(e).lower()

    def test_model_persistence_and_loading(self, financial_forecaster):
        """Test model persistence and loading capabilities."""
        ticker = "TEST"

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / f"{ticker}_model.pkl"

            # Train and save model
            model, metrics = financial_forecaster.train_fcf_model(ticker, periods=8)

            # Create model manager for persistence
            model_manager = MLModelManager()
            model_manager.save_model(model, str(model_path), {"ticker": ticker, "metrics": metrics})

            # Verify model file exists
            assert model_path.exists()

            # Load model and verify
            loaded_model, loaded_metadata = model_manager.load_model(str(model_path))
            assert loaded_model is not None
            assert loaded_metadata["ticker"] == ticker
            assert "metrics" in loaded_metadata

    def test_performance_metrics_accuracy(self, financial_forecaster):
        """Test accuracy of performance metrics calculations."""
        ticker = "TEST"

        # Train model
        model, metrics = financial_forecaster.train_fcf_model(ticker, periods=8)

        # Verify metrics are reasonable
        assert 0 <= metrics.get('r2_score', -1) <= 1  # R² should be between 0 and 1 for good models
        assert metrics.get('mse', float('inf')) >= 0  # MSE should be non-negative
        assert metrics.get('mae', float('inf')) >= 0  # MAE should be non-negative

        # Test prediction accuracy on known data
        test_data = financial_forecaster._get_historical_fcf_data(ticker).tail(2)
        predictions = financial_forecaster.forecast_fcf(ticker, periods=2)

        # Predictions should be reasonable relative to historical data
        historical_mean = test_data['fcf'].mean()
        pred_values = predictions['predictions']

        # Predictions shouldn't be wildly different from historical data
        for pred in pred_values:
            assert abs(pred - historical_mean) < historical_mean * 2  # Within 200% of historical mean

    @pytest.mark.integration
    def test_full_pipeline_integration(self, financial_forecaster):
        """Test full pipeline from raw data to final predictions."""
        ticker = "TEST"

        # Step 1: Data preparation
        fcf_data = financial_forecaster._get_historical_fcf_data(ticker)
        assert not fcf_data.empty

        # Step 2: Model training with validation
        model, training_metrics = financial_forecaster.train_fcf_model(ticker, periods=8)
        validator = ModelValidator()
        validation_results = validator.cross_validate_model(model, fcf_data)

        # Step 3: Ensemble creation
        models = [model]
        for _ in range(2):
            additional_model, _ = financial_forecaster.train_fcf_model(ticker, periods=8)
            models.append(additional_model)

        ensemble = EnsemblePredictor(models)

        # Step 4: Final predictions
        test_data = fcf_data.tail(4)
        ensemble_predictions = ensemble.predict_ensemble(test_data)

        # Step 5: Verify complete pipeline results
        assert training_metrics['r2_score'] is not None
        assert validation_results['mean_score'] is not None
        assert ensemble_predictions['ensemble_prediction'] is not None
        assert ensemble_predictions['confidence_score'] > 0

        # Verify ensemble improves or matches individual predictions
        individual_preds = ensemble_predictions['individual_predictions']
        ensemble_pred = ensemble_predictions['ensemble_prediction']

        # Ensemble prediction should be within reasonable range of individual predictions
        if len(individual_preds) > 1:
            pred_range = max(individual_preds) - min(individual_preds)
            assert min(individual_preds) <= ensemble_pred <= max(individual_preds) or pred_range < 0.1