"""
Unit tests for EnsemblePredictor.

Tests ensemble prediction methods, confidence estimation, and model weighting.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from core.analysis.ml.ensemble.ensemble_predictor import EnsemblePredictor


class TestEnsemblePredictor:
    """Unit tests for EnsemblePredictor class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        return pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'target': np.random.randn(100)
        })

    @pytest.fixture
    def trained_models(self, sample_data):
        """Create trained models for ensemble testing."""
        X = sample_data[['feature1', 'feature2', 'feature3']]
        y = sample_data['target']

        models = []

        # Linear regression model
        lr_model = LinearRegression()
        lr_model.fit(X, y)
        models.append(lr_model)

        # Random forest model
        rf_model = RandomForestRegressor(n_estimators=10, random_state=42)
        rf_model.fit(X, y)
        models.append(rf_model)

        # Another linear regression with different features
        lr_model2 = LinearRegression()
        lr_model2.fit(X[['feature1', 'feature2']], y)
        models.append(lr_model2)

        return models

    @pytest.fixture
    def ensemble_predictor(self, trained_models):
        """Create EnsemblePredictor with trained models."""
        return EnsemblePredictor(trained_models)

    def test_initialization(self, trained_models):
        """Test EnsemblePredictor initialization."""
        ensemble = EnsemblePredictor(trained_models)

        assert ensemble.models == trained_models
        assert len(ensemble.model_weights) == len(trained_models)
        assert all(weight == 1.0 for weight in ensemble.model_weights)
        assert ensemble.performance_history == {}

    def test_initialization_with_weights(self, trained_models):
        """Test initialization with custom weights."""
        custom_weights = [0.5, 1.0, 0.8]
        ensemble = EnsemblePredictor(trained_models, model_weights=custom_weights)

        assert ensemble.model_weights == custom_weights

    def test_initialization_invalid_weights(self, trained_models):
        """Test initialization with invalid weights."""
        invalid_weights = [0.5, 1.0]  # Wrong length

        with pytest.raises(ValueError):
            EnsemblePredictor(trained_models, model_weights=invalid_weights)

    def test_simple_average_prediction(self, ensemble_predictor, sample_data):
        """Test simple average ensemble prediction."""
        test_data = sample_data.tail(10)

        result = ensemble_predictor._simple_average(test_data)

        assert isinstance(result, np.ndarray)
        assert len(result) == 10

        # Verify it's actually an average
        individual_preds = []
        for model in ensemble_predictor.models:
            if hasattr(model, 'predict'):
                if len(test_data.columns) >= 3:
                    pred = model.predict(test_data[['feature1', 'feature2', 'feature3']])
                else:
                    pred = model.predict(test_data[['feature1', 'feature2']])
                individual_preds.append(pred)

        if individual_preds:
            expected_avg = np.mean(individual_preds, axis=0)
            np.testing.assert_array_almost_equal(result, expected_avg, decimal=5)

    def test_weighted_average_prediction(self, ensemble_predictor, sample_data):
        """Test weighted average ensemble prediction."""
        test_data = sample_data.tail(10)

        # Set custom weights
        ensemble_predictor.model_weights = [0.5, 1.0, 0.3]

        result = ensemble_predictor._weighted_average(test_data)

        assert isinstance(result, np.ndarray)
        assert len(result) == 10

        # Result should be different from simple average due to weighting
        simple_avg = ensemble_predictor._simple_average(test_data)
        assert not np.array_equal(result, simple_avg)

    def test_dynamic_weighting_prediction(self, ensemble_predictor, sample_data):
        """Test dynamic weighting ensemble prediction."""
        test_data = sample_data.tail(10)

        # Add some performance history
        ensemble_predictor.performance_history = {
            0: [0.8, 0.85, 0.82],  # Model 0 performance
            1: [0.9, 0.88, 0.91],  # Model 1 performance
            2: [0.7, 0.75, 0.73]   # Model 2 performance
        }

        result = ensemble_predictor._dynamic_weighting(test_data)

        assert isinstance(result, np.ndarray)
        assert len(result) == 10

        # Best performing model (1) should have higher weight
        weights = ensemble_predictor._calculate_dynamic_weights()
        assert weights[1] >= weights[0]
        assert weights[1] >= weights[2]

    def test_calculate_dynamic_weights(self, ensemble_predictor):
        """Test dynamic weight calculation."""
        # Test with no performance history
        weights = ensemble_predictor._calculate_dynamic_weights()
        expected_equal_weights = [1.0] * len(ensemble_predictor.models)
        assert weights == expected_equal_weights

        # Test with performance history
        ensemble_predictor.performance_history = {
            0: [0.8, 0.85, 0.82],
            1: [0.9, 0.88, 0.91],
            2: [0.7, 0.75, 0.73]
        }

        weights = ensemble_predictor._calculate_dynamic_weights()

        # Weights should sum to approximately number of models
        assert abs(sum(weights) - len(ensemble_predictor.models)) < 0.1

        # Best performing model should have highest weight
        best_model_idx = max(range(len(weights)), key=lambda i: weights[i])
        assert best_model_idx == 1  # Model 1 has best performance

    def test_detect_outliers(self, ensemble_predictor, sample_data):
        """Test outlier detection in predictions."""
        test_data = sample_data.tail(10)

        # Get individual predictions
        individual_preds = []
        for model in ensemble_predictor.models:
            if len(test_data.columns) >= 3:
                pred = model.predict(test_data[['feature1', 'feature2', 'feature3']])
            else:
                pred = model.predict(test_data[['feature1', 'feature2']])
            individual_preds.append(pred)

        # Test outlier detection
        outlier_indices = ensemble_predictor._detect_outliers(individual_preds, threshold=2.0)

        assert isinstance(outlier_indices, set)
        assert all(isinstance(idx, int) for idx in outlier_indices)
        assert all(0 <= idx < len(individual_preds) for idx in outlier_indices)

    def test_calculate_confidence_score(self, ensemble_predictor, sample_data):
        """Test confidence score calculation."""
        test_data = sample_data.tail(10)

        # Get individual predictions
        individual_preds = []
        for model in ensemble_predictor.models:
            if len(test_data.columns) >= 3:
                pred = model.predict(test_data[['feature1', 'feature2', 'feature3']])
            else:
                pred = model.predict(test_data[['feature1', 'feature2']])
            individual_preds.append(pred)

        confidence = ensemble_predictor._calculate_confidence_score(individual_preds)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

        # With only 3 models and similar predictions, confidence should be reasonable
        assert confidence > 0.1  # Should have some confidence

    def test_predict_ensemble_complete_workflow(self, ensemble_predictor, sample_data):
        """Test complete ensemble prediction workflow."""
        test_data = sample_data.tail(5)

        # Use the actual method signature
        result = ensemble_predictor.predict_ensemble(
            target_variable="target",
            features=test_data[['feature1', 'feature2', 'feature3']]
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert 'ensemble_prediction' in result
        assert 'confidence_score' in result
        assert 'individual_predictions' in result
        assert 'method_used' in result

        # Verify data types and shapes
        assert isinstance(result['ensemble_prediction'], np.ndarray)
        assert len(result['ensemble_prediction']) == 5
        assert isinstance(result['confidence_score'], float)
        assert 0.0 <= result['confidence_score'] <= 1.0
        assert isinstance(result['individual_predictions'], list)
        assert len(result['individual_predictions']) == len(ensemble_predictor.models)

    def test_predict_ensemble_with_outliers(self, sample_data):
        """Test ensemble prediction with outlier models."""
        # Create models with one that produces outlier predictions
        X = sample_data[['feature1', 'feature2', 'feature3']]
        y = sample_data['target']

        models = []

        # Normal models
        lr1 = LinearRegression()
        lr1.fit(X, y)
        models.append(lr1)

        lr2 = LinearRegression()
        lr2.fit(X, y)
        models.append(lr2)

        # Mock outlier model
        outlier_model = Mock()
        outlier_model.predict.return_value = np.array([1000.0] * 5)  # Extreme predictions
        models.append(outlier_model)

        ensemble = EnsemblePredictor(models)
        test_data = sample_data.tail(5)

        result = ensemble.predict_ensemble(test_data)

        # Should still produce reasonable results despite outlier
        assert isinstance(result, dict)
        assert 'ensemble_prediction' in result

        # Outlier should be detected and confidence should be lower
        assert result['confidence_score'] < 0.9  # Should be lower due to disagreement

    def test_update_performance_history(self, ensemble_predictor):
        """Test performance history update."""
        model_idx = 0
        score = 0.85

        ensemble_predictor.update_performance_history(model_idx, score)

        assert model_idx in ensemble_predictor.performance_history
        assert ensemble_predictor.performance_history[model_idx] == [score]

        # Add another score
        ensemble_predictor.update_performance_history(model_idx, 0.88)
        assert ensemble_predictor.performance_history[model_idx] == [score, 0.88]

        # Test with max_history_length
        for i in range(10):
            ensemble_predictor.update_performance_history(model_idx, 0.9)

        # Should not exceed max length (default 10)
        assert len(ensemble_predictor.performance_history[model_idx]) <= 10

    def test_get_model_performance_stats(self, ensemble_predictor):
        """Test model performance statistics."""
        # Add performance history
        ensemble_predictor.performance_history = {
            0: [0.8, 0.85, 0.82, 0.88],
            1: [0.9, 0.88, 0.91, 0.89],
            2: [0.7, 0.75, 0.73, 0.78]
        }

        stats = ensemble_predictor.get_model_performance_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 3

        for model_idx, model_stats in stats.items():
            assert 'mean_performance' in model_stats
            assert 'std_performance' in model_stats
            assert 'recent_performance' in model_stats
            assert isinstance(model_stats['mean_performance'], float)
            assert isinstance(model_stats['std_performance'], float)
            assert isinstance(model_stats['recent_performance'], float)

    def test_optimize_ensemble_weights(self, ensemble_predictor, sample_data):
        """Test ensemble weight optimization."""
        # Add performance history
        ensemble_predictor.performance_history = {
            0: [0.8, 0.85, 0.82],
            1: [0.9, 0.88, 0.91],
            2: [0.7, 0.75, 0.73]
        }

        original_weights = ensemble_predictor.model_weights.copy()
        ensemble_predictor.optimize_ensemble_weights()

        # Weights should be updated based on performance
        assert ensemble_predictor.model_weights != original_weights

        # Best performing model should have higher weight
        best_model_idx = 1  # Model 1 has best performance
        assert ensemble_predictor.model_weights[best_model_idx] >= max(
            ensemble_predictor.model_weights[0],
            ensemble_predictor.model_weights[2]
        )

    def test_empty_models_list(self):
        """Test ensemble with empty models list."""
        with pytest.raises(ValueError):
            EnsemblePredictor([])

    def test_single_model_ensemble(self, sample_data):
        """Test ensemble with single model."""
        X = sample_data[['feature1', 'feature2', 'feature3']]
        y = sample_data['target']

        model = LinearRegression()
        model.fit(X, y)

        ensemble = EnsemblePredictor([model])
        test_data = sample_data.tail(5)

        result = ensemble.predict_ensemble(test_data)

        # Should work with single model
        assert isinstance(result, dict)
        assert 'ensemble_prediction' in result
        assert len(result['individual_predictions']) == 1

        # Confidence should be high with single model (no disagreement)
        assert result['confidence_score'] >= 0.5

    def test_prediction_methods_consistency(self, ensemble_predictor, sample_data):
        """Test consistency between different prediction methods."""
        test_data = sample_data.tail(5)

        # Test each method
        simple_pred = ensemble_predictor._simple_average(test_data)
        weighted_pred = ensemble_predictor._weighted_average(test_data)

        # With equal weights, weighted average should equal simple average
        ensemble_predictor.model_weights = [1.0, 1.0, 1.0]
        weighted_pred_equal = ensemble_predictor._weighted_average(test_data)

        np.testing.assert_array_almost_equal(simple_pred, weighted_pred_equal, decimal=5)

        # With different weights, should be different
        ensemble_predictor.model_weights = [0.5, 1.0, 2.0]
        weighted_pred_diff = ensemble_predictor._weighted_average(test_data)

        assert not np.array_equal(simple_pred, weighted_pred_diff)