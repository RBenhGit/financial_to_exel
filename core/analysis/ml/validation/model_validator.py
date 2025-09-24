"""
Model Validator
===============

Comprehensive validation framework for machine learning models in financial analysis.
Provides systematic validation procedures including cross-validation, performance
testing, bias detection, and robustness analysis.

This validator ensures that ML models meet the high standards required for
financial decision-making applications.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)

# Import existing framework components
from core.data_processing.error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    issue_type: str
    severity: ValidationSeverity
    description: str
    recommendation: str
    metric_value: Optional[float] = None

@dataclass
class ValidationResult:
    """Comprehensive validation result"""
    model_id: str
    validation_date: datetime
    overall_score: float  # 0-100 scale
    performance_metrics: Dict[str, float]
    cross_validation_scores: List[float]
    bias_test_results: Dict[str, Any]
    robustness_results: Dict[str, Any]
    issues: List[ValidationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    passed_validation: bool = True

class ModelValidator:
    """
    Comprehensive validation framework for ML models

    This class provides systematic validation procedures to ensure model
    reliability, accuracy, and fairness in financial analysis applications.

    Features:
    - Cross-validation with time series considerations
    - Performance metric analysis
    - Bias detection and fairness testing
    - Robustness analysis under different conditions
    - Comprehensive validation reporting
    - Integration with existing error handling
    """

    def __init__(self,
                 validation_thresholds: Optional[Dict[str, float]] = None,
                 enable_time_series_validation: bool = True):
        """
        Initialize Model Validator

        Parameters:
        -----------
        validation_thresholds : Dict[str, float], optional
            Custom thresholds for validation metrics
        enable_time_series_validation : bool
            Whether to use time series-aware validation
        """
        self.validation_thresholds = validation_thresholds or self._get_default_thresholds()
        self.enable_time_series_validation = enable_time_series_validation

        logger.info("ModelValidator initialized with comprehensive validation framework")

    def validate_model(self,
                      model: Any,
                      X: pd.DataFrame,
                      y: pd.Series,
                      model_id: str,
                      model_metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Perform comprehensive model validation

        Parameters:
        -----------
        model : Any
            Trained model to validate
        X : pd.DataFrame
            Feature data
        y : pd.Series
            Target data
        model_id : str
            Model identifier
        model_metadata : Dict[str, Any], optional
            Additional model metadata

        Returns:
        --------
        ValidationResult
            Comprehensive validation results
        """
        try:
            logger.info(f"Starting comprehensive validation for model {model_id}")

            # Initialize validation result
            validation_result = ValidationResult(
                model_id=model_id,
                validation_date=datetime.now(),
                overall_score=0.0,
                performance_metrics={},
                cross_validation_scores=[],
                bias_test_results={},
                robustness_results={}
            )

            # 1. Performance Validation
            performance_metrics = self._validate_performance(model, X, y)
            validation_result.performance_metrics = performance_metrics

            # 2. Cross-Validation
            cv_scores = self._perform_cross_validation(model, X, y)
            validation_result.cross_validation_scores = cv_scores

            # 3. Bias Testing
            bias_results = self._test_model_bias(model, X, y)
            validation_result.bias_test_results = bias_results

            # 4. Robustness Analysis
            robustness_results = self._analyze_robustness(model, X, y)
            validation_result.robustness_results = robustness_results

            # 5. Issue Detection
            issues = self._detect_validation_issues(validation_result)
            validation_result.issues = issues

            # 6. Generate Recommendations
            recommendations = self._generate_recommendations(validation_result)
            validation_result.recommendations = recommendations

            # 7. Calculate Overall Score
            overall_score = self._calculate_overall_score(validation_result)
            validation_result.overall_score = overall_score

            # 8. Determine Pass/Fail Status
            validation_result.passed_validation = self._determine_validation_status(validation_result)

            logger.info(f"Validation completed for model {model_id}. Score: {overall_score:.2f}")

            return validation_result

        except Exception as e:
            logger.error(f"Error in model validation: {e}")
            raise

    def _validate_performance(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Validate model performance metrics"""
        try:
            # Make predictions
            y_pred = model.predict(X)

            # Calculate regression metrics
            metrics = {
                'r2_score': r2_score(y, y_pred),
                'mse': mean_squared_error(y, y_pred),
                'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                'mae': mean_absolute_error(y, y_pred),
                'mape': np.mean(np.abs((y - y_pred) / y)) * 100  # Mean Absolute Percentage Error
            }

            # Add relative metrics
            metrics['rmse_relative'] = metrics['rmse'] / np.mean(y)
            metrics['mae_relative'] = metrics['mae'] / np.mean(y)

            return metrics

        except Exception as e:
            logger.error(f"Error in performance validation: {e}")
            return {}

    def _perform_cross_validation(self, model: Any, X: pd.DataFrame, y: pd.Series) -> List[float]:
        """Perform cross-validation with time series considerations"""
        try:
            if self.enable_time_series_validation and len(X) > 20:
                # Use TimeSeriesSplit for time series data
                cv = TimeSeriesSplit(n_splits=5)
                cv_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            else:
                # Standard cross-validation
                cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

            return cv_scores.tolist()

        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
            return []

    def _test_model_bias(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Test model for bias and fairness issues"""
        try:
            y_pred = model.predict(X)
            residuals = y - y_pred

            bias_results = {
                'mean_bias': np.mean(residuals),
                'bias_variance': np.var(residuals),
                'systematic_bias_test': self._test_systematic_bias(residuals),
                'feature_bias_analysis': self._analyze_feature_bias(model, X, y),
                'temporal_bias': self._test_temporal_bias(residuals, X)
            }

            return bias_results

        except Exception as e:
            logger.error(f"Error in bias testing: {e}")
            return {}

    def _analyze_robustness(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Analyze model robustness under different conditions"""
        try:
            robustness_results = {
                'noise_sensitivity': self._test_noise_sensitivity(model, X, y),
                'outlier_sensitivity': self._test_outlier_sensitivity(model, X, y),
                'feature_importance_stability': self._test_feature_stability(model, X, y),
                'prediction_stability': self._test_prediction_stability(model, X)
            }

            return robustness_results

        except Exception as e:
            logger.error(f"Error in robustness analysis: {e}")
            return {}

    def _test_systematic_bias(self, residuals: np.ndarray) -> Dict[str, float]:
        """Test for systematic bias patterns"""
        from scipy import stats

        # Normality test
        shapiro_stat, shapiro_p = stats.shapiro(residuals[:5000] if len(residuals) > 5000 else residuals)

        # Runs test for randomness
        median_residual = np.median(residuals)
        runs, runs_p = self._runs_test(residuals > median_residual)

        return {
            'normality_p_value': shapiro_p,
            'randomness_p_value': runs_p,
            'bias_trend': self._calculate_bias_trend(residuals)
        }

    def _analyze_feature_bias(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Analyze bias across different feature ranges"""
        feature_bias = {}

        # Test bias across feature quantiles
        for column in X.columns:
            if X[column].dtype in ['int64', 'float64']:
                try:
                    quartiles = pd.qcut(X[column], q=4, duplicates='drop')
                    y_pred = model.predict(X)
                    residuals = y - y_pred

                    bias_by_quartile = []
                    for quartile in quartiles.cat.categories:
                        mask = quartiles == quartile
                        if mask.sum() > 0:
                            quartile_bias = np.mean(residuals[mask])
                            bias_by_quartile.append(quartile_bias)

                    if bias_by_quartile:
                        feature_bias[column] = {
                            'max_bias_difference': max(bias_by_quartile) - min(bias_by_quartile),
                            'bias_variance': np.var(bias_by_quartile)
                        }

                except Exception:
                    continue

        return feature_bias

    def _test_temporal_bias(self, residuals: np.ndarray, X: pd.DataFrame) -> Dict[str, float]:
        """Test for temporal bias patterns"""
        # Simple trend test
        indices = np.arange(len(residuals))
        correlation = np.corrcoef(indices, residuals)[0, 1]

        return {
            'temporal_correlation': correlation,
            'trend_significance': abs(correlation) > 0.1  # Simple threshold
        }

    def _test_noise_sensitivity(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Test model sensitivity to input noise"""
        try:
            # Original predictions
            y_pred_original = model.predict(X)
            original_score = r2_score(y, y_pred_original)

            # Add noise and test
            noise_levels = [0.01, 0.05, 0.1]
            sensitivity_scores = {}

            for noise_level in noise_levels:
                # Add Gaussian noise
                X_noisy = X + np.random.normal(0, noise_level * X.std(), X.shape)
                y_pred_noisy = model.predict(X_noisy)
                noisy_score = r2_score(y, y_pred_noisy)

                sensitivity_scores[f'noise_{noise_level}'] = abs(original_score - noisy_score)

            return sensitivity_scores

        except Exception as e:
            logger.error(f"Error in noise sensitivity test: {e}")
            return {}

    def _test_outlier_sensitivity(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Test model sensitivity to outliers"""
        try:
            # Original performance
            y_pred_original = model.predict(X)
            original_score = r2_score(y, y_pred_original)

            # Introduce outliers
            X_outliers = X.copy()
            outlier_indices = np.random.choice(X.index, size=max(1, len(X) // 20), replace=False)

            for col in X.columns:
                if X[col].dtype in ['int64', 'float64']:
                    outlier_value = X[col].mean() + 3 * X[col].std()
                    X_outliers.loc[outlier_indices, col] = outlier_value

            y_pred_outliers = model.predict(X_outliers)
            outlier_score = r2_score(y, y_pred_outliers)

            return {
                'outlier_sensitivity': abs(original_score - outlier_score),
                'outlier_impact_percentage': ((original_score - outlier_score) / original_score) * 100
            }

        except Exception as e:
            logger.error(f"Error in outlier sensitivity test: {e}")
            return {}

    def _test_feature_stability(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Test stability of feature importance"""
        if not hasattr(model, 'feature_importances_'):
            return {'feature_stability': 0.0}

        try:
            original_importance = model.feature_importances_

            # Retrain on bootstrap samples
            n_bootstrap = 5
            importance_variations = []

            for _ in range(n_bootstrap):
                bootstrap_indices = np.random.choice(X.index, size=len(X), replace=True)
                X_bootstrap = X.loc[bootstrap_indices]
                y_bootstrap = y.loc[bootstrap_indices]

                # Clone and retrain model
                from sklearn.base import clone
                model_bootstrap = clone(model)
                model_bootstrap.fit(X_bootstrap, y_bootstrap)

                if hasattr(model_bootstrap, 'feature_importances_'):
                    importance_diff = np.mean(np.abs(original_importance - model_bootstrap.feature_importances_))
                    importance_variations.append(importance_diff)

            return {
                'feature_stability': 1.0 - np.mean(importance_variations) if importance_variations else 1.0
            }

        except Exception as e:
            logger.error(f"Error in feature stability test: {e}")
            return {'feature_stability': 0.0}

    def _test_prediction_stability(self, model: Any, X: pd.DataFrame) -> Dict[str, float]:
        """Test stability of predictions"""
        try:
            # Multiple predictions with small perturbations
            original_pred = model.predict(X)

            variations = []
            for _ in range(5):
                # Small random perturbation
                X_perturbed = X + np.random.normal(0, 0.001 * X.std(), X.shape)
                perturbed_pred = model.predict(X_perturbed)
                variation = np.mean(np.abs(original_pred - perturbed_pred))
                variations.append(variation)

            return {
                'prediction_stability': 1.0 / (1.0 + np.mean(variations))
            }

        except Exception as e:
            logger.error(f"Error in prediction stability test: {e}")
            return {'prediction_stability': 0.0}

    def _detect_validation_issues(self, validation_result: ValidationResult) -> List[ValidationIssue]:
        """Detect validation issues based on results"""
        issues = []

        # Performance issues
        r2_score = validation_result.performance_metrics.get('r2_score', 0)
        if r2_score < self.validation_thresholds['min_r2_score']:
            issues.append(ValidationIssue(
                issue_type='poor_performance',
                severity=ValidationSeverity.HIGH,
                description=f"R² score ({r2_score:.3f}) below threshold ({self.validation_thresholds['min_r2_score']})",
                recommendation="Consider feature engineering, model tuning, or alternative algorithms",
                metric_value=r2_score
            ))

        # Cross-validation consistency
        cv_scores = validation_result.cross_validation_scores
        if cv_scores and np.std(cv_scores) > self.validation_thresholds['max_cv_std']:
            issues.append(ValidationIssue(
                issue_type='cv_inconsistency',
                severity=ValidationSeverity.MEDIUM,
                description=f"High cross-validation variance ({np.std(cv_scores):.3f})",
                recommendation="Model performance is inconsistent across folds. Consider regularization or more data",
                metric_value=np.std(cv_scores)
            ))

        # Bias issues
        mean_bias = validation_result.bias_test_results.get('mean_bias', 0)
        if abs(mean_bias) > self.validation_thresholds['max_bias']:
            issues.append(ValidationIssue(
                issue_type='systematic_bias',
                severity=ValidationSeverity.HIGH,
                description=f"Systematic bias detected ({mean_bias:.3f})",
                recommendation="Model shows systematic bias. Review features and training data",
                metric_value=mean_bias
            ))

        return issues

    def _generate_recommendations(self, validation_result: ValidationResult) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Extract recommendation from issues
        for issue in validation_result.issues:
            recommendations.append(issue.recommendation)

        # General recommendations
        if validation_result.overall_score < 70:
            recommendations.append("Overall model performance is below acceptable threshold. Consider comprehensive model review.")

        if not validation_result.cross_validation_scores:
            recommendations.append("Cross-validation results missing. Implement proper validation procedures.")

        return recommendations

    def _calculate_overall_score(self, validation_result: ValidationResult) -> float:
        """Calculate overall validation score (0-100)"""
        try:
            scores = []

            # Performance score (40% weight)
            r2_score = validation_result.performance_metrics.get('r2_score', 0)
            performance_score = max(0, min(100, r2_score * 100))
            scores.append(performance_score * 0.4)

            # Cross-validation consistency (20% weight)
            cv_scores = validation_result.cross_validation_scores
            if cv_scores:
                cv_consistency = max(0, min(100, (1 - np.std(cv_scores)) * 100))
                scores.append(cv_consistency * 0.2)

            # Bias score (25% weight)
            mean_bias = abs(validation_result.bias_test_results.get('mean_bias', 0))
            bias_score = max(0, min(100, (1 - min(1, mean_bias)) * 100))
            scores.append(bias_score * 0.25)

            # Robustness score (15% weight)
            robustness_metrics = validation_result.robustness_results
            if robustness_metrics:
                stability_scores = [
                    robustness_metrics.get('prediction_stability', {}).get('prediction_stability', 0),
                    robustness_metrics.get('feature_importance_stability', {}).get('feature_stability', 0)
                ]
                robustness_score = np.mean([s for s in stability_scores if s > 0]) * 100
                scores.append(robustness_score * 0.15)

            return sum(scores)

        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0

    def _determine_validation_status(self, validation_result: ValidationResult) -> bool:
        """Determine if model passes validation"""
        # Critical issues automatically fail
        critical_issues = [issue for issue in validation_result.issues
                          if issue.severity == ValidationSeverity.CRITICAL]

        if critical_issues:
            return False

        # Overall score threshold
        if validation_result.overall_score < self.validation_thresholds['min_overall_score']:
            return False

        # High severity issues count
        high_issues = [issue for issue in validation_result.issues
                      if issue.severity == ValidationSeverity.HIGH]

        if len(high_issues) > self.validation_thresholds['max_high_issues']:
            return False

        return True

    def _get_default_thresholds(self) -> Dict[str, float]:
        """Get default validation thresholds"""
        return {
            'min_r2_score': 0.6,
            'max_cv_std': 0.2,
            'max_bias': 0.1,
            'min_overall_score': 70.0,
            'max_high_issues': 2
        }

    def _runs_test(self, binary_sequence: np.ndarray) -> Tuple[int, float]:
        """Perform runs test for randomness"""
        try:
            # Count runs
            runs = 1
            for i in range(1, len(binary_sequence)):
                if binary_sequence[i] != binary_sequence[i-1]:
                    runs += 1

            # Calculate expected runs and variance
            n1 = np.sum(binary_sequence)
            n2 = len(binary_sequence) - n1

            if n1 == 0 or n2 == 0:
                return runs, 1.0  # No variation

            expected_runs = (2 * n1 * n2) / (n1 + n2) + 1
            variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2) ** 2 * (n1 + n2 - 1))

            if variance == 0:
                return runs, 1.0

            # Z-score
            z_score = (runs - expected_runs) / np.sqrt(variance)

            # Two-tailed p-value (approximate)
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

            return runs, p_value

        except Exception:
            return 0, 1.0

    def _calculate_bias_trend(self, residuals: np.ndarray) -> float:
        """Calculate trend in residuals"""
        try:
            indices = np.arange(len(residuals))
            correlation = np.corrcoef(indices, residuals)[0, 1]
            return correlation
        except Exception:
            return 0.0