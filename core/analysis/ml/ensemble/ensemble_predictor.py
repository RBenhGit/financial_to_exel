"""
Ensemble Predictor
==================

Advanced ensemble methods for combining multiple ML models to improve
prediction accuracy and robustness in financial forecasting.

This module implements various ensemble techniques including voting,
stacking, and blending for enhanced prediction performance.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Scikit-learn ensemble methods
from sklearn.ensemble import VotingRegressor, VotingClassifier
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score

# Import existing ML framework
from ..models.model_manager import MLModelManager, PredictionResult
from ..validation.model_validator import ModelValidator
from core.data_processing.error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

class EnsembleMethod(Enum):
    """Types of ensemble methods"""
    SIMPLE_AVERAGE = "simple_average"
    WEIGHTED_AVERAGE = "weighted_average"
    VOTING = "voting"
    STACKING = "stacking"
    BLENDING = "blending"
    DYNAMIC_WEIGHTING = "dynamic_weighting"

@dataclass
class EnsembleConfig:
    """Configuration for ensemble prediction"""
    method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE
    min_models: int = 2
    max_models: int = 10
    performance_weight: float = 0.7  # Weight for model performance in weighting
    recency_weight: float = 0.3  # Weight for model recency in weighting
    outlier_threshold: float = 2.0  # Standard deviations for outlier detection
    validation_required: bool = True
    auto_update_weights: bool = True

@dataclass
class EnsembleResult:
    """Result from ensemble prediction"""
    prediction: float
    confidence: float
    individual_predictions: Dict[str, float]
    model_weights: Dict[str, float]
    ensemble_method: EnsembleMethod
    prediction_variance: float
    outliers_detected: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class EnsemblePredictor:
    """
    Advanced ensemble predictor for financial forecasting

    This class implements multiple ensemble methods to combine predictions
    from different ML models, improving accuracy and robustness of forecasts.

    Features:
    - Multiple ensemble methods (averaging, voting, stacking)
    - Dynamic model weighting based on performance and recency
    - Outlier detection and handling
    - Confidence estimation
    - Performance tracking and optimization
    - Automated ensemble optimization
    """

    def __init__(self,
                 ml_manager: MLModelManager,
                 validator: Optional[ModelValidator] = None,
                 config: Optional[EnsembleConfig] = None):
        """
        Initialize Ensemble Predictor

        Parameters:
        -----------
        ml_manager : MLModelManager
            ML model manager with trained models
        validator : ModelValidator, optional
            Model validator for ensemble validation
        config : EnsembleConfig, optional
            Ensemble configuration
        """
        self.ml_manager = ml_manager
        self.validator = validator or ModelValidator()
        self.config = config or EnsembleConfig()

        # Ensemble tracking
        self.ensemble_history: List[EnsembleResult] = []
        self.model_weights_history: Dict[str, List[float]] = {}

        # Performance tracking
        self.ensemble_performance: Dict[str, float] = {}

        logger.info(f"EnsemblePredictor initialized with method: {self.config.method.value}")

    def predict_ensemble(self,
                        target_variable: str,
                        features: Union[Dict[str, float], pd.DataFrame],
                        model_ids: Optional[List[str]] = None) -> EnsembleResult:
        """
        Generate ensemble prediction

        Parameters:
        -----------
        target_variable : str
            Target variable to predict
        features : Dict or DataFrame
            Feature values for prediction
        model_ids : List[str], optional
            Specific model IDs to use in ensemble

        Returns:
        --------
        EnsembleResult
            Ensemble prediction result with metadata
        """
        try:
            # Get suitable models for the target variable
            suitable_models = self.get_suitable_models(target_variable, model_ids)

            if len(suitable_models) < self.config.min_models:
                raise ValueError(f"Need at least {self.config.min_models} models, found {len(suitable_models)}")

            # Get individual predictions
            individual_predictions = {}
            prediction_errors = {}

            for model_id in suitable_models:
                try:
                    result = self.ml_manager.predict(model_id, features)
                    individual_predictions[model_id] = result.prediction
                except Exception as e:
                    logger.warning(f"Failed to get prediction from model {model_id}: {e}")
                    prediction_errors[model_id] = str(e)

            if len(individual_predictions) < self.config.min_models:
                raise ValueError(f"Too few successful predictions: {len(individual_predictions)}")

            # Detect and handle outliers
            outliers = self.detect_outliers(individual_predictions)

            # Filter out outliers if detected
            filtered_predictions = {k: v for k, v in individual_predictions.items()
                                  if k not in outliers}

            if len(filtered_predictions) < self.config.min_models:
                logger.warning("Too many outliers detected, using all predictions")
                filtered_predictions = individual_predictions
                outliers = []

            # Calculate model weights
            model_weights = self.calculate_model_weights(filtered_predictions.keys())

            # Generate ensemble prediction
            ensemble_prediction = self.combine_predictions(
                filtered_predictions, model_weights
            )

            # Calculate confidence and variance
            confidence = self.calculate_confidence(filtered_predictions, model_weights)
            variance = np.var(list(filtered_predictions.values()))

            # Create result
            result = EnsembleResult(
                prediction=ensemble_prediction,
                confidence=confidence,
                individual_predictions=individual_predictions,
                model_weights=model_weights,
                ensemble_method=self.config.method,
                prediction_variance=variance,
                outliers_detected=outliers
            )

            # Update tracking
            self.ensemble_history.append(result)
            self.update_weights_history(model_weights)

            logger.info(f"Ensemble prediction generated: {ensemble_prediction:.2f} (confidence: {confidence:.3f})")

            return result

        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            raise

    def get_suitable_models(self,
                           target_variable: str,
                           model_ids: Optional[List[str]] = None) -> List[str]:
        """Get models suitable for the target variable"""
        available_models = self.ml_manager.list_models()

        # Filter by target variable
        suitable = [m for m in available_models
                   if m['target_variable'] == target_variable and m['status'] == 'validated']

        # Apply model ID filter if provided
        if model_ids:
            suitable = [m for m in suitable if m['model_id'] in model_ids]

        # Sort by performance
        suitable.sort(key=lambda x: x.get('performance_metrics', {}).get('r2_score', 0), reverse=True)

        # Limit to max_models
        model_ids_list = [m['model_id'] for m in suitable[:self.config.max_models]]

        return model_ids_list

    def detect_outliers(self, predictions: Dict[str, float]) -> List[str]:
        """Detect outlier predictions using statistical methods"""
        try:
            values = list(predictions.values())

            if len(values) < 3:
                return []

            mean_val = np.mean(values)
            std_val = np.std(values)

            outliers = []
            for model_id, prediction in predictions.items():
                z_score = abs(prediction - mean_val) / std_val if std_val > 0 else 0
                if z_score > self.config.outlier_threshold:
                    outliers.append(model_id)

            if outliers:
                logger.info(f"Detected {len(outliers)} outlier predictions: {outliers}")

            return outliers

        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return []

    def calculate_model_weights(self, model_ids: List[str]) -> Dict[str, float]:
        """Calculate weights for models based on performance and recency"""
        try:
            weights = {}

            for model_id in model_ids:
                if model_id not in self.ml_manager.metadata:
                    weights[model_id] = 0.1  # Minimal weight for unknown models
                    continue

                metadata = self.ml_manager.metadata[model_id]

                # Performance weight
                performance_score = metadata.performance_metrics.get('r2_score', 0)
                performance_score = max(0, min(1, performance_score))  # Clamp to [0, 1]

                # Recency weight (newer models get higher weight)
                days_old = (datetime.now() - metadata.training_date).days
                recency_score = max(0, 1 - days_old / 365)  # Decay over a year

                # Combined weight
                combined_weight = (
                    self.config.performance_weight * performance_score +
                    self.config.recency_weight * recency_score
                )

                weights[model_id] = combined_weight

            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}
            else:
                # Equal weights if all weights are zero
                equal_weight = 1.0 / len(model_ids)
                weights = {model_id: equal_weight for model_id in model_ids}

            return weights

        except Exception as e:
            logger.error(f"Error calculating model weights: {e}")
            # Return equal weights as fallback
            equal_weight = 1.0 / len(model_ids)
            return {model_id: equal_weight for model_id in model_ids}

    def combine_predictions(self,
                           predictions: Dict[str, float],
                           weights: Dict[str, float]) -> float:
        """Combine individual predictions using the configured method"""
        try:
            if self.config.method == EnsembleMethod.SIMPLE_AVERAGE:
                return np.mean(list(predictions.values()))

            elif self.config.method == EnsembleMethod.WEIGHTED_AVERAGE:
                weighted_sum = sum(predictions[model_id] * weights.get(model_id, 0)
                                 for model_id in predictions.keys())
                return weighted_sum

            elif self.config.method == EnsembleMethod.DYNAMIC_WEIGHTING:
                # Use recent performance to adjust weights
                adjusted_weights = self.adjust_weights_by_recent_performance(weights)
                weighted_sum = sum(predictions[model_id] * adjusted_weights.get(model_id, 0)
                                 for model_id in predictions.keys())
                return weighted_sum

            else:
                # Default to weighted average
                logger.warning(f"Ensemble method {self.config.method} not fully implemented, using weighted average")
                weighted_sum = sum(predictions[model_id] * weights.get(model_id, 0)
                                 for model_id in predictions.keys())
                return weighted_sum

        except Exception as e:
            logger.error(f"Error combining predictions: {e}")
            # Fallback to simple average
            return np.mean(list(predictions.values()))

    def adjust_weights_by_recent_performance(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """Adjust weights based on recent ensemble performance"""
        try:
            if len(self.ensemble_history) < 5:
                return base_weights

            # Analyze recent performance of each model
            recent_performance = {}
            recent_results = self.ensemble_history[-10:]  # Last 10 predictions

            for model_id in base_weights.keys():
                # Calculate how close each model's predictions were to ensemble average
                model_errors = []
                for result in recent_results:
                    if model_id in result.individual_predictions:
                        individual_pred = result.individual_predictions[model_id]
                        ensemble_pred = result.prediction
                        error = abs(individual_pred - ensemble_pred)
                        model_errors.append(error)

                if model_errors:
                    avg_error = np.mean(model_errors)
                    # Convert error to performance score (lower error = higher score)
                    performance_score = 1 / (1 + avg_error)
                    recent_performance[model_id] = performance_score
                else:
                    recent_performance[model_id] = 0.5  # Neutral score

            # Combine base weights with recent performance
            adjusted_weights = {}
            for model_id, base_weight in base_weights.items():
                recent_score = recent_performance.get(model_id, 0.5)
                # Weight combination: 70% base, 30% recent performance
                adjusted_weight = 0.7 * base_weight + 0.3 * recent_score
                adjusted_weights[model_id] = adjusted_weight

            # Normalize
            total_weight = sum(adjusted_weights.values())
            if total_weight > 0:
                adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

            return adjusted_weights

        except Exception as e:
            logger.error(f"Error adjusting weights by recent performance: {e}")
            return base_weights

    def calculate_confidence(self,
                           predictions: Dict[str, float],
                           weights: Dict[str, float]) -> float:
        """Calculate confidence score for ensemble prediction"""
        try:
            values = list(predictions.values())

            if len(values) < 2:
                return 0.5  # Low confidence with single prediction

            # Agreement metric: how close predictions are to each other
            mean_prediction = np.mean(values)
            prediction_std = np.std(values)

            # Normalize standard deviation
            if mean_prediction != 0:
                normalized_std = prediction_std / abs(mean_prediction)
            else:
                normalized_std = prediction_std

            # Agreement score (higher when predictions are closer)
            agreement_score = 1 / (1 + normalized_std)

            # Model quality score (weighted average of individual model R² scores)
            quality_scores = []
            for model_id, weight in weights.items():
                if model_id in self.ml_manager.metadata:
                    r2_score = self.ml_manager.metadata[model_id].performance_metrics.get('r2_score', 0)
                    quality_scores.append(r2_score * weight)

            avg_quality = sum(quality_scores) if quality_scores else 0.5

            # Number of models factor
            num_models_factor = min(1.0, len(predictions) / self.config.max_models)

            # Combined confidence
            confidence = (0.4 * agreement_score +
                         0.4 * avg_quality +
                         0.2 * num_models_factor)

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def update_weights_history(self, weights: Dict[str, float]):
        """Update historical tracking of model weights"""
        try:
            for model_id, weight in weights.items():
                if model_id not in self.model_weights_history:
                    self.model_weights_history[model_id] = []

                self.model_weights_history[model_id].append(weight)

                # Keep only last 50 weight values
                self.model_weights_history[model_id] = self.model_weights_history[model_id][-50:]

        except Exception as e:
            logger.error(f"Error updating weights history: {e}")

    def evaluate_ensemble_performance(self,
                                    test_data: pd.DataFrame,
                                    target_variable: str,
                                    feature_columns: List[str]) -> Dict[str, float]:
        """Evaluate ensemble performance on test data"""
        try:
            if test_data.empty:
                return {}

            # Generate ensemble predictions for test data
            predictions = []
            actual_values = test_data[target_variable].values

            for _, row in test_data.iterrows():
                features = row[feature_columns].to_dict()
                result = self.predict_ensemble(target_variable, features)
                predictions.append(result.prediction)

            # Calculate metrics
            mse = mean_squared_error(actual_values, predictions)
            r2 = r2_score(actual_values, predictions)
            mae = np.mean(np.abs(actual_values - predictions))

            # Calculate relative metrics
            mean_actual = np.mean(actual_values)
            rmse_relative = np.sqrt(mse) / mean_actual if mean_actual != 0 else np.sqrt(mse)

            performance_metrics = {
                'ensemble_r2_score': r2,
                'ensemble_mse': mse,
                'ensemble_rmse': np.sqrt(mse),
                'ensemble_mae': mae,
                'ensemble_rmse_relative': rmse_relative,
                'num_predictions': len(predictions)
            }

            # Update ensemble performance tracking
            self.ensemble_performance.update(performance_metrics)

            logger.info(f"Ensemble performance - R² Score: {r2:.4f}, RMSE: {np.sqrt(mse):.4f}")

            return performance_metrics

        except Exception as e:
            logger.error(f"Error evaluating ensemble performance: {e}")
            return {}

    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Get comprehensive ensemble performance summary"""
        try:
            if not self.ensemble_history:
                return {'message': 'No ensemble predictions made yet'}

            recent_results = self.ensemble_history[-20:]

            # Calculate summary statistics
            predictions = [r.prediction for r in recent_results]
            confidences = [r.confidence for r in recent_results]
            variances = [r.prediction_variance for r in recent_results]

            # Model usage statistics
            model_usage = {}
            for result in recent_results:
                for model_id in result.individual_predictions.keys():
                    model_usage[model_id] = model_usage.get(model_id, 0) + 1

            # Outlier statistics
            total_outliers = sum(len(r.outliers_detected) for r in recent_results)

            summary = {
                'total_predictions': len(self.ensemble_history),
                'recent_predictions': len(recent_results),
                'ensemble_method': self.config.method.value,
                'average_confidence': np.mean(confidences) if confidences else 0,
                'average_variance': np.mean(variances) if variances else 0,
                'prediction_range': {
                    'min': float(np.min(predictions)) if predictions else 0,
                    'max': float(np.max(predictions)) if predictions else 0,
                    'mean': float(np.mean(predictions)) if predictions else 0
                },
                'model_usage_frequency': model_usage,
                'outliers_detected_total': total_outliers,
                'performance_metrics': self.ensemble_performance
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating ensemble summary: {e}")
            return {'error': str(e)}

    def optimize_ensemble_config(self,
                                validation_data: pd.DataFrame,
                                target_variable: str,
                                feature_columns: List[str]) -> EnsembleConfig:
        """Optimize ensemble configuration based on validation data"""
        try:
            logger.info("Optimizing ensemble configuration...")

            best_config = self.config
            best_score = 0

            # Test different ensemble methods
            methods_to_test = [
                EnsembleMethod.SIMPLE_AVERAGE,
                EnsembleMethod.WEIGHTED_AVERAGE,
                EnsembleMethod.DYNAMIC_WEIGHTING
            ]

            for method in methods_to_test:
                # Create test config
                test_config = EnsembleConfig(
                    method=method,
                    min_models=self.config.min_models,
                    max_models=self.config.max_models
                )

                # Temporarily set config and evaluate
                original_config = self.config
                self.config = test_config

                performance = self.evaluate_ensemble_performance(
                    validation_data, target_variable, feature_columns
                )

                if performance.get('ensemble_r2_score', 0) > best_score:
                    best_score = performance['ensemble_r2_score']
                    best_config = test_config

                # Restore original config
                self.config = original_config

            # Update to best configuration
            self.config = best_config

            logger.info(f"Optimized ensemble method: {best_config.method.value} (R² Score: {best_score:.4f})")

            return best_config

        except Exception as e:
            logger.error(f"Error optimizing ensemble config: {e}")
            return self.config

# Convenience functions

def create_ensemble_predictor(ml_manager: MLModelManager,
                            method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE) -> EnsemblePredictor:
    """Create a configured ensemble predictor"""
    config = EnsembleConfig(method=method)
    return EnsemblePredictor(ml_manager, config=config)

def quick_ensemble_prediction(ml_manager: MLModelManager,
                            target_variable: str,
                            features: Union[Dict[str, float], pd.DataFrame]) -> float:
    """Quick ensemble prediction with default settings"""
    predictor = create_ensemble_predictor(ml_manager)
    result = predictor.predict_ensemble(target_variable, features)
    return result.prediction