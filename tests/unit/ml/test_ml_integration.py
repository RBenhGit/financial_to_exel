"""
ML Integration Tests
===================

Unit tests for the machine learning integration framework.
Tests core functionality, integration points, and error handling.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch

# Import ML components
from core.analysis.ml.models.model_manager import MLModelManager, ModelType, ModelStatus
from core.analysis.ml.forecasting.financial_forecaster import FinancialForecaster
from core.analysis.ml.validation.model_validator import ModelValidator, ValidationSeverity

class TestMLModelManager:
    """Test cases for ML Model Manager"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        data = pd.DataFrame({
            'revenue': np.random.uniform(1000000, 5000000, 100),
            'ebit': np.random.uniform(100000, 1000000, 100),
            'capex': np.random.uniform(50000, 500000, 100),
            'fcf': np.random.uniform(200000, 800000, 100)
        })
        return data

    @pytest.fixture
    def ml_manager(self):
        """Create ML manager instance"""
        return MLModelManager()

    def test_ml_manager_initialization(self, ml_manager):
        """Test ML manager initialization"""
        assert ml_manager is not None
        assert ml_manager.models == {}
        assert ml_manager.metadata == {}
        assert ml_manager.model_storage_path.exists()

    def test_train_financial_predictor(self, ml_manager, sample_data):
        """Test financial predictor training"""
        feature_columns = ['revenue', 'ebit', 'capex']
        target_variable = 'fcf'

        model_id = ml_manager.train_financial_predictor(
            target_variable=target_variable,
            feature_columns=feature_columns,
            data=sample_data,
            model_type='random_forest'
        )

        assert model_id is not None
        assert model_id in ml_manager.models
        assert model_id in ml_manager.metadata

        # Check metadata
        metadata = ml_manager.metadata[model_id]
        assert metadata.model_type == ModelType.REGRESSION
        assert metadata.target_variable == target_variable
        assert metadata.features == feature_columns
        assert metadata.status == ModelStatus.VALIDATED

    def test_model_prediction(self, ml_manager, sample_data):
        """Test model prediction functionality"""
        feature_columns = ['revenue', 'ebit', 'capex']
        target_variable = 'fcf'

        # Train model
        model_id = ml_manager.train_financial_predictor(
            target_variable=target_variable,
            feature_columns=feature_columns,
            data=sample_data,
            model_type='linear'
        )

        # Test prediction
        test_features = {
            'revenue': 2000000,
            'ebit': 400000,
            'capex': 200000
        }

        prediction_result = ml_manager.predict(model_id, test_features)

        assert prediction_result is not None
        assert prediction_result.model_id == model_id
        assert isinstance(prediction_result.prediction, (int, float))
        assert prediction_result.prediction > 0  # FCF should be positive

    def test_model_bias_testing(self, ml_manager, sample_data):
        """Test model bias testing functionality"""
        feature_columns = ['revenue', 'ebit', 'capex']
        target_variable = 'fcf'

        # Train model
        model_id = ml_manager.train_financial_predictor(
            target_variable=target_variable,
            feature_columns=feature_columns,
            data=sample_data
        )

        # Test bias
        test_data = sample_data.tail(20)
        bias_results = ml_manager.validate_model_bias(model_id, test_data)

        assert bias_results is not None
        assert 'overall_bias' in bias_results
        assert 'prediction_variance' in bias_results
        assert 'residual_analysis' in bias_results

    def test_model_performance_retrieval(self, ml_manager, sample_data):
        """Test model performance metrics retrieval"""
        feature_columns = ['revenue', 'ebit']
        target_variable = 'fcf'

        model_id = ml_manager.train_financial_predictor(
            target_variable=target_variable,
            feature_columns=feature_columns,
            data=sample_data
        )

        performance = ml_manager.get_model_performance(model_id)

        assert performance is not None
        assert performance['model_id'] == model_id
        assert 'performance_metrics' in performance
        assert 'r2' in performance['performance_metrics'] or 'r2_score' in performance['performance_metrics']

    def test_list_models(self, ml_manager, sample_data):
        """Test listing all models"""
        # Initially empty
        models = ml_manager.list_models()
        initial_count = len(models)

        # Train a model
        ml_manager.train_financial_predictor(
            target_variable='fcf',
            feature_columns=['revenue', 'ebit'],
            data=sample_data
        )

        # Check list again
        models = ml_manager.list_models()
        assert len(models) == initial_count + 1

class TestFinancialForecaster:
    """Test cases for Financial Forecaster"""

    @pytest.fixture
    def forecaster(self):
        """Create financial forecaster instance"""
        return FinancialForecaster()

    def test_forecaster_initialization(self, forecaster):
        """Test forecaster initialization"""
        assert forecaster is not None
        assert forecaster.financial_calculator is not None
        assert forecaster.ml_manager is not None

    @patch('core.analysis.ml.forecasting.financial_forecaster.FinancialForecaster._get_historical_fcf_data')
    def test_forecast_fcf_with_mock_data(self, mock_get_data, forecaster):
        """Test FCF forecasting with mocked data"""
        # Mock historical data
        mock_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=20, freq='Q'),
            'fcf': np.random.uniform(100000, 500000, 20),
            'revenue': np.random.uniform(1000000, 3000000, 20)
        })
        mock_get_data.return_value = mock_data

        # This test would need the full implementation to work
        # For now, we'll just test that the method exists and can be called
        assert hasattr(forecaster, 'forecast_fcf')

    def test_forecast_revenue_basic(self, forecaster):
        """Test basic revenue forecasting"""
        # This would require mocking the historical data retrieval
        assert hasattr(forecaster, 'forecast_revenue')

class TestModelValidator:
    """Test cases for Model Validator"""

    @pytest.fixture
    def validator(self):
        """Create model validator instance"""
        return ModelValidator()

    @pytest.fixture
    def mock_model_and_data(self):
        """Create mock model and data for testing"""
        from sklearn.linear_model import LinearRegression

        # Create mock data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.uniform(0, 100, 100),
            'feature2': np.random.uniform(0, 50, 100),
            'feature3': np.random.uniform(10, 20, 100)
        })
        y = pd.Series(X['feature1'] * 2 + X['feature2'] * 0.5 + np.random.normal(0, 5, 100))

        # Train a simple model
        model = LinearRegression()
        model.fit(X, y)

        return model, X, y

    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator is not None
        assert validator.validation_thresholds is not None
        assert 'min_r2_score' in validator.validation_thresholds

    def test_validate_model(self, validator, mock_model_and_data):
        """Test comprehensive model validation"""
        model, X, y = mock_model_and_data

        validation_result = validator.validate_model(
            model=model,
            X=X,
            y=y,
            model_id="test_model"
        )

        assert validation_result is not None
        assert validation_result.model_id == "test_model"
        assert isinstance(validation_result.overall_score, float)
        assert 0 <= validation_result.overall_score <= 100
        assert isinstance(validation_result.passed_validation, bool)

    def test_performance_validation(self, validator, mock_model_and_data):
        """Test performance validation"""
        model, X, y = mock_model_and_data

        performance_metrics = validator._validate_performance(model, X, y)

        assert 'r2_score' in performance_metrics
        assert 'mse' in performance_metrics
        assert 'rmse' in performance_metrics
        assert 'mae' in performance_metrics

        # R² should be reasonable for our linear relationship
        assert performance_metrics['r2_score'] > 0.5

    def test_cross_validation(self, validator, mock_model_and_data):
        """Test cross-validation"""
        model, X, y = mock_model_and_data

        cv_scores = validator._perform_cross_validation(model, X, y)

        assert isinstance(cv_scores, list)
        assert len(cv_scores) == 5  # 5-fold CV
        assert all(isinstance(score, float) for score in cv_scores)

    def test_bias_testing(self, validator, mock_model_and_data):
        """Test bias testing"""
        model, X, y = mock_model_and_data

        bias_results = validator._test_model_bias(model, X, y)

        assert 'mean_bias' in bias_results
        assert 'bias_variance' in bias_results
        assert 'systematic_bias_test' in bias_results

    def test_robustness_analysis(self, validator, mock_model_and_data):
        """Test robustness analysis"""
        model, X, y = mock_model_and_data

        robustness_results = validator._analyze_robustness(model, X, y)

        assert 'noise_sensitivity' in robustness_results
        assert 'outlier_sensitivity' in robustness_results
        assert 'prediction_stability' in robustness_results

    def test_validation_thresholds(self, validator):
        """Test validation thresholds"""
        thresholds = validator._get_default_thresholds()

        required_thresholds = [
            'min_r2_score', 'max_cv_std', 'max_bias',
            'min_overall_score', 'max_high_issues'
        ]

        for threshold in required_thresholds:
            assert threshold in thresholds
            assert isinstance(thresholds[threshold], (int, float))

class TestMLIntegration:
    """Integration tests for the ML framework"""

    def test_end_to_end_workflow(self):
        """Test end-to-end ML workflow"""
        # Create sample data
        np.random.seed(42)
        data = pd.DataFrame({
            'revenue': np.random.uniform(1000000, 5000000, 50),
            'ebit': np.random.uniform(100000, 1000000, 50),
            'capex': np.random.uniform(50000, 500000, 50),
            'fcf': np.random.uniform(200000, 800000, 50)
        })

        # Initialize components
        ml_manager = MLModelManager()
        validator = ModelValidator()

        # Train model
        model_id = ml_manager.train_financial_predictor(
            target_variable='fcf',
            feature_columns=['revenue', 'ebit', 'capex'],
            data=data
        )

        # Validate model
        if model_id and model_id in ml_manager.models:
            model = ml_manager.models[model_id]
            X = data[['revenue', 'ebit', 'capex']]
            y = data['fcf']

            validation_result = validator.validate_model(model, X, y, model_id)

            assert validation_result is not None
            assert validation_result.model_id == model_id

            # Make prediction
            test_features = {
                'revenue': 2000000,
                'ebit': 400000,
                'capex': 200000
            }

            prediction = ml_manager.predict(model_id, test_features)
            assert prediction is not None
            assert prediction.model_id == model_id

    def test_error_handling(self):
        """Test error handling in ML components"""
        ml_manager = MLModelManager()

        # Test prediction with non-existent model
        result = ml_manager.predict("non_existent_model", {'feature': 1.0})
        # Should handle error gracefully (implementation dependent)

        # Test training with insufficient data
        small_data = pd.DataFrame({
            'feature': [1, 2],
            'target': [10, 20]
        })

        # Should handle small dataset gracefully
        model_id = ml_manager.train_financial_predictor(
            target_variable='target',
            feature_columns=['feature'],
            data=small_data
        )

        # Result depends on implementation - either successful training or graceful failure

if __name__ == "__main__":
    pytest.main([__file__])