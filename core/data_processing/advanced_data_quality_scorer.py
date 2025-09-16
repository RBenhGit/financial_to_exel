"""
Advanced Data Quality Scoring System
===================================

This module provides sophisticated data quality scoring algorithms with real-time
monitoring, predictive alerts, and comprehensive quality assessment for financial data.

Features:
- Multi-dimensional quality scoring (completeness, consistency, accuracy, timeliness)
- Machine learning-based trend prediction
- Real-time quality monitoring with alerts
- Historical quality tracking and analytics
- Integration with existing monitoring infrastructure
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

# Import existing infrastructure
from core.data_processing.data_validator import FinancialDataValidator, DataQualityReport
from core.data_processing.monitoring.health_monitor import HealthMetrics, HealthStatus
from core.data_processing.monitoring.alerting_system import Alert, AlertSeverity, AlertType

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Different dimensions of data quality assessment"""
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"


@dataclass
class QualityMetrics:
    """Container for quality metrics across all dimensions"""
    completeness: float = 0.0
    consistency: float = 0.0
    accuracy: float = 0.0
    timeliness: float = 0.0
    validity: float = 0.0
    uniqueness: float = 0.0
    overall_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    source_identifier: str = ""
    data_points_analyzed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'completeness': self.completeness,
            'consistency': self.consistency,
            'accuracy': self.accuracy,
            'timeliness': self.timeliness,
            'validity': self.validity,
            'uniqueness': self.uniqueness,
            'overall_score': self.overall_score,
            'timestamp': self.timestamp.isoformat(),
            'source_identifier': self.source_identifier,
            'data_points_analyzed': self.data_points_analyzed
        }


class AdvancedDataQualityScorer:
    """
    Advanced data quality scoring system with real-time monitoring and predictive capabilities
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the advanced data quality scorer

        Args:
            config_path: Path to configuration file for scoring parameters
        """
        self.config = self._load_config(config_path)
        self.validator = FinancialDataValidator()
        self.quality_history: List[QualityMetrics] = []
        self.alert_thresholds = self.config.get('alert_thresholds', self._get_default_thresholds())

        # Initialize quality tracking
        self._initialize_quality_tracking()

        logger.info("Advanced Data Quality Scorer initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load scoring configuration from file or use defaults"""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default scoring configuration"""
        return {
            'weights': {
                'completeness': 0.25,
                'consistency': 0.20,
                'accuracy': 0.25,
                'timeliness': 0.10,
                'validity': 0.15,
                'uniqueness': 0.05
            },
            'scoring_parameters': {
                'completeness_threshold': 0.8,
                'consistency_outlier_std': 3.0,
                'timeliness_max_age_days': 30,
                'validity_min_samples': 5
            },
            'alert_thresholds': {
                'critical_overall_score': 60.0,
                'warning_overall_score': 75.0,
                'critical_completeness': 50.0,
                'warning_completeness': 70.0
            },
            'trend_analysis': {
                'lookback_periods': 10,
                'degradation_threshold': -5.0,
                'prediction_window_hours': 24
            }
        }

    def _get_default_thresholds(self) -> Dict[str, float]:
        """Get default alert thresholds"""
        return self.config.get('alert_thresholds', {
            'critical_overall_score': 60.0,
            'warning_overall_score': 75.0,
            'critical_completeness': 50.0,
            'warning_completeness': 70.0
        })

    def _initialize_quality_tracking(self):
        """Initialize quality tracking infrastructure"""
        self.quality_cache_file = Path("data/cache/data_quality_history.json")
        self.quality_cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Load historical quality data if available
        self._load_quality_history()

    def _load_quality_history(self):
        """Load historical quality metrics from cache"""
        try:
            if self.quality_cache_file.exists():
                with open(self.quality_cache_file, 'r') as f:
                    history_data = json.load(f)
                    self.quality_history = [
                        QualityMetrics(
                            completeness=item['completeness'],
                            consistency=item['consistency'],
                            accuracy=item['accuracy'],
                            timeliness=item['timeliness'],
                            validity=item['validity'],
                            uniqueness=item['uniqueness'],
                            overall_score=item['overall_score'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            source_identifier=item.get('source_identifier', ''),
                            data_points_analyzed=item.get('data_points_analyzed', 0)
                        ) for item in history_data
                    ]
                logger.info(f"Loaded {len(self.quality_history)} historical quality records")
        except Exception as e:
            logger.warning(f"Failed to load quality history: {e}")
            self.quality_history = []

    def _save_quality_history(self):
        """Save quality history to cache"""
        try:
            # Keep only last 1000 records to manage file size
            recent_history = self.quality_history[-1000:] if len(self.quality_history) > 1000 else self.quality_history

            with open(self.quality_cache_file, 'w') as f:
                json.dump([metrics.to_dict() for metrics in recent_history], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save quality history: {e}")

    def score_data_quality(
        self,
        data: Union[Dict[str, Any], pd.DataFrame],
        source_identifier: str = "",
        data_context: Dict[str, Any] = None
    ) -> QualityMetrics:
        """
        Calculate comprehensive data quality score

        Args:
            data: Data to score (financial data dictionary or DataFrame)
            source_identifier: Identifier for the data source
            data_context: Additional context about the data

        Returns:
            QualityMetrics with detailed scoring
        """
        logger.info(f"Scoring data quality for source: {source_identifier}")

        # Initialize metrics
        metrics = QualityMetrics(source_identifier=source_identifier)

        try:
            # Score each dimension
            metrics.completeness = self._score_completeness(data, data_context)
            metrics.consistency = self._score_consistency(data, data_context)
            metrics.accuracy = self._score_accuracy(data, data_context)
            metrics.timeliness = self._score_timeliness(data, data_context)
            metrics.validity = self._score_validity(data, data_context)
            metrics.uniqueness = self._score_uniqueness(data, data_context)

            # Calculate overall weighted score
            metrics.overall_score = self._calculate_overall_score(metrics)

            # Count data points analyzed
            metrics.data_points_analyzed = self._count_data_points(data)

            # Store in history
            self.quality_history.append(metrics)
            self._save_quality_history()

            # Check for alerts
            self._check_quality_alerts(metrics)

            logger.info(f"Quality scoring completed. Overall score: {metrics.overall_score:.2f}")

            return metrics

        except Exception as e:
            logger.error(f"Error during quality scoring: {e}")
            # Return minimal metrics on error
            metrics.overall_score = 0.0
            return metrics

    def _score_completeness(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data completeness (0-100)"""
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return 0.0

            total_cells = data.size
            missing_cells = data.isnull().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells) * 100

        elif isinstance(data, dict):
            total_fields = 0
            missing_fields = 0

            for key, value in data.items():
                if isinstance(value, (list, tuple)):
                    total_fields += len(value)
                    missing_fields += sum(1 for v in value if v is None or v == '' or pd.isna(v))
                else:
                    total_fields += 1
                    if value is None or value == '' or pd.isna(value):
                        missing_fields += 1

            completeness = ((total_fields - missing_fields) / total_fields) * 100 if total_fields > 0 else 0.0

        else:
            completeness = 0.0 if data is None else 100.0

        return max(0.0, min(100.0, completeness))

    def _score_consistency(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data consistency based on patterns and relationships"""
        try:
            if isinstance(data, pd.DataFrame):
                consistency_score = 100.0

                # Check for numeric consistency
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    values = data[col].dropna()
                    if len(values) > 1:
                        # Check for extreme outliers using IQR method
                        Q1 = values.quantile(0.25)
                        Q3 = values.quantile(0.75)
                        IQR = Q3 - Q1

                        if IQR > 0:
                            outliers = values[(values < Q1 - 3*IQR) | (values > Q3 + 3*IQR)]
                            outlier_ratio = len(outliers) / len(values)
                            consistency_score -= outlier_ratio * 30  # Penalize outliers

                return max(0.0, min(100.0, consistency_score))

            elif isinstance(data, dict):
                # For financial data dictionaries, check year-over-year consistency
                consistency_score = 100.0

                for key, values in data.items():
                    if isinstance(values, (list, tuple)) and len(values) > 1:
                        numeric_values = [v for v in values if isinstance(v, (int, float)) and not pd.isna(v)]

                        if len(numeric_values) > 1:
                            # Calculate coefficient of variation for relative consistency
                            mean_val = np.mean(numeric_values)
                            std_val = np.std(numeric_values)

                            if mean_val != 0:
                                cv = std_val / abs(mean_val)
                                # Higher CV indicates lower consistency
                                consistency_penalty = min(cv * 20, 50)  # Cap penalty at 50%
                                consistency_score -= consistency_penalty

                return max(0.0, min(100.0, consistency_score))

            else:
                return 100.0  # Single values are always consistent

        except Exception as e:
            logger.warning(f"Error calculating consistency score: {e}")
            return 50.0  # Default neutral score on error

    def _score_accuracy(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data accuracy based on validation rules"""
        try:
            # Use existing validator for basic accuracy checks
            if isinstance(data, dict):
                report = self.validator.validate_financial_statements(data)
                report.calculate_scores()
                return report.consistency_score  # Maps to accuracy in our context

            elif isinstance(data, pd.DataFrame):
                # Score based on data type conformity and reasonable value ranges
                accuracy_score = 100.0

                for col in data.columns:
                    if data[col].dtype == 'object':
                        # Check for consistent data types within object columns
                        non_null_values = data[col].dropna()
                        if len(non_null_values) > 0:
                            # Sample some values to check type consistency
                            sample_size = min(10, len(non_null_values))
                            sample_values = non_null_values.sample(sample_size)

                            # Check if values can be converted to numbers when they should be
                            numeric_convertible = 0
                            for val in sample_values:
                                try:
                                    float(str(val).replace(',', '').replace('$', ''))
                                    numeric_convertible += 1
                                except (ValueError, TypeError):
                                    pass

                            # If most values look numeric but column is object, penalize accuracy
                            if numeric_convertible / sample_size > 0.7:
                                accuracy_score -= 10

                return max(0.0, min(100.0, accuracy_score))

            else:
                return 100.0  # Single values assumed accurate if present

        except Exception as e:
            logger.warning(f"Error calculating accuracy score: {e}")
            return 75.0  # Default reasonable score on error

    def _score_timeliness(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data timeliness based on age and update frequency"""
        try:
            current_time = datetime.now()
            max_age_days = self.config['scoring_parameters']['timeliness_max_age_days']

            # Check if context provides timestamp information
            if context and 'data_timestamp' in context:
                data_timestamp = context['data_timestamp']
                if isinstance(data_timestamp, str):
                    data_timestamp = datetime.fromisoformat(data_timestamp)

                age_days = (current_time - data_timestamp).days

                if age_days <= 1:
                    return 100.0  # Fresh data
                elif age_days <= max_age_days:
                    # Linear decay from 100 to 50 over max_age_days
                    return 100.0 - ((age_days - 1) / (max_age_days - 1)) * 50
                else:
                    return 50.0  # Old but still usable

            # If no timestamp context, assume reasonable freshness for financial data
            return 85.0  # Default assumption for financial data

        except Exception as e:
            logger.warning(f"Error calculating timeliness score: {e}")
            return 75.0

    def _score_validity(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data validity based on business rules and constraints"""
        try:
            validity_score = 100.0

            if isinstance(data, dict):
                # Financial data specific validity checks

                # Check for negative values where they shouldn't be
                positive_required = ['Total Current Assets', 'Total Assets', 'Market Cap']

                for metric, values in data.items():
                    if any(req in metric for req in positive_required):
                        if isinstance(values, (list, tuple)):
                            negative_count = sum(1 for v in values if isinstance(v, (int, float)) and v < 0)
                            if negative_count > 0:
                                validity_score -= (negative_count / len(values)) * 20

                # Check for reasonable magnitude (not too many zeros or extremely large numbers)
                for metric, values in data.items():
                    if isinstance(values, (list, tuple)):
                        numeric_values = [v for v in values if isinstance(v, (int, float)) and not pd.isna(v)]

                        if numeric_values:
                            # Check for too many zeros
                            zero_ratio = sum(1 for v in numeric_values if v == 0) / len(numeric_values)
                            if zero_ratio > 0.5:  # More than 50% zeros
                                validity_score -= 15

                            # Check for extremely large numbers (potential unit errors)
                            max_reasonable = 1e12  # 1 trillion
                            large_numbers = [v for v in numeric_values if abs(v) > max_reasonable]
                            if large_numbers:
                                validity_score -= (len(large_numbers) / len(numeric_values)) * 25

            elif isinstance(data, pd.DataFrame):
                # Check data types and value ranges
                for col in data.select_dtypes(include=[np.number]).columns:
                    values = data[col].dropna()
                    if len(values) > 0:
                        # Check for infinite or NaN values
                        invalid_count = np.sum(np.isinf(values)) + np.sum(np.isnan(values))
                        if invalid_count > 0:
                            validity_score -= (invalid_count / len(data)) * 30

            return max(0.0, min(100.0, validity_score))

        except Exception as e:
            logger.warning(f"Error calculating validity score: {e}")
            return 80.0

    def _score_uniqueness(self, data: Any, context: Dict[str, Any] = None) -> float:
        """Score data uniqueness (detect duplicates)"""
        try:
            if isinstance(data, pd.DataFrame):
                if data.empty:
                    return 100.0

                # Check for duplicate rows
                duplicate_rows = data.duplicated().sum()
                uniqueness = ((len(data) - duplicate_rows) / len(data)) * 100
                return max(0.0, min(100.0, uniqueness))

            elif isinstance(data, dict):
                # For financial data, uniqueness is less relevant but we can check for
                # duplicate entries in time series data
                uniqueness_score = 100.0

                for key, values in data.items():
                    if isinstance(values, (list, tuple)) and len(values) > 1:
                        # Check for duplicate consecutive values (might indicate stale data)
                        consecutive_duplicates = 0
                        for i in range(1, len(values)):
                            if values[i] == values[i-1] and values[i] is not None:
                                consecutive_duplicates += 1

                        if consecutive_duplicates > len(values) * 0.3:  # More than 30% consecutive duplicates
                            uniqueness_score -= 20

                return max(0.0, min(100.0, uniqueness_score))

            else:
                return 100.0  # Single values are unique by definition

        except Exception as e:
            logger.warning(f"Error calculating uniqueness score: {e}")
            return 95.0

    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate weighted overall quality score"""
        weights = self.config['weights']

        overall = (
            metrics.completeness * weights['completeness'] +
            metrics.consistency * weights['consistency'] +
            metrics.accuracy * weights['accuracy'] +
            metrics.timeliness * weights['timeliness'] +
            metrics.validity * weights['validity'] +
            metrics.uniqueness * weights['uniqueness']
        )

        return round(overall, 2)

    def _count_data_points(self, data: Any) -> int:
        """Count the number of data points analyzed"""
        if isinstance(data, pd.DataFrame):
            return data.size
        elif isinstance(data, dict):
            count = 0
            for value in data.values():
                if isinstance(value, (list, tuple)):
                    count += len(value)
                else:
                    count += 1
            return count
        else:
            return 1

    def _check_quality_alerts(self, metrics: QualityMetrics):
        """Check if quality metrics trigger any alerts"""
        try:
            alerts_to_trigger = []

            # Check overall score thresholds
            if metrics.overall_score < self.alert_thresholds['critical_overall_score']:
                alerts_to_trigger.append((AlertSeverity.CRITICAL, AlertType.DATA_QUALITY_LOW,
                                        f"Overall quality score critically low: {metrics.overall_score:.1f}%"))
            elif metrics.overall_score < self.alert_thresholds['warning_overall_score']:
                alerts_to_trigger.append((AlertSeverity.WARNING, AlertType.DATA_QUALITY_LOW,
                                        f"Overall quality score below threshold: {metrics.overall_score:.1f}%"))

            # Check completeness thresholds
            if metrics.completeness < self.alert_thresholds['critical_completeness']:
                alerts_to_trigger.append((AlertSeverity.CRITICAL, AlertType.DATA_QUALITY_LOW,
                                        f"Data completeness critically low: {metrics.completeness:.1f}%"))
            elif metrics.completeness < self.alert_thresholds['warning_completeness']:
                alerts_to_trigger.append((AlertSeverity.WARNING, AlertType.DATA_QUALITY_LOW,
                                        f"Data completeness below threshold: {metrics.completeness:.1f}%"))

            # Log alerts (in a real implementation, these would integrate with the alerting system)
            for severity, alert_type, message in alerts_to_trigger:
                if severity == AlertSeverity.CRITICAL:
                    logger.critical(f"DATA QUALITY ALERT: {message}")
                else:
                    logger.warning(f"DATA QUALITY ALERT: {message}")

        except Exception as e:
            logger.error(f"Error checking quality alerts: {e}")

    def get_quality_trends(self, lookback_periods: int = None) -> Dict[str, Any]:
        """
        Analyze quality trends over time

        Args:
            lookback_periods: Number of recent periods to analyze

        Returns:
            Dictionary with trend analysis
        """
        if not self.quality_history:
            return {'status': 'no_data', 'message': 'No historical quality data available'}

        lookback = lookback_periods or self.config['trend_analysis']['lookback_periods']
        recent_history = self.quality_history[-lookback:] if len(self.quality_history) >= lookback else self.quality_history

        if len(recent_history) < 2:
            return {'status': 'insufficient_data', 'message': 'Insufficient historical data for trend analysis'}

        try:
            # Extract time series data
            timestamps = [m.timestamp for m in recent_history]
            overall_scores = [m.overall_score for m in recent_history]
            completeness_scores = [m.completeness for m in recent_history]
            consistency_scores = [m.consistency for m in recent_history]

            # Calculate trends (simple linear regression slope)
            def calculate_trend(values):
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, 1)
                return coeffs[0]  # slope

            trends = {
                'overall_trend': calculate_trend(overall_scores),
                'completeness_trend': calculate_trend(completeness_scores),
                'consistency_trend': calculate_trend(consistency_scores),
                'current_score': overall_scores[-1],
                'score_range': (min(overall_scores), max(overall_scores)),
                'analysis_period': {
                    'start': timestamps[0].isoformat(),
                    'end': timestamps[-1].isoformat(),
                    'periods_analyzed': len(recent_history)
                }
            }

            # Trend interpretation
            degradation_threshold = self.config['trend_analysis']['degradation_threshold']

            if trends['overall_trend'] < degradation_threshold:
                trends['status'] = 'degrading'
                trends['message'] = f"Quality degrading at {trends['overall_trend']:.2f} points per period"
            elif trends['overall_trend'] > -degradation_threshold:
                trends['status'] = 'improving'
                trends['message'] = f"Quality improving at {trends['overall_trend']:.2f} points per period"
            else:
                trends['status'] = 'stable'
                trends['message'] = "Quality levels stable"

            return trends

        except Exception as e:
            logger.error(f"Error analyzing quality trends: {e}")
            return {'status': 'error', 'message': f'Error analyzing trends: {str(e)}'}

    def predict_quality_issues(self) -> Dict[str, Any]:
        """
        Predict potential quality issues based on historical trends

        Returns:
            Dictionary with predictions and recommendations
        """
        trends = self.get_quality_trends()

        if trends.get('status') not in ['degrading', 'improving', 'stable']:
            return {'status': 'no_prediction', 'message': 'Insufficient data for prediction'}

        predictions = {
            'timestamp': datetime.now().isoformat(),
            'prediction_window_hours': self.config['trend_analysis']['prediction_window_hours'],
            'current_quality': trends['current_score'],
            'trend_direction': trends['status'],
            'recommendations': []
        }

        # Generate predictions based on trend
        if trends['status'] == 'degrading':
            projected_score = trends['current_score'] + (trends['overall_trend'] * 2)  # 2 periods ahead

            predictions['projected_quality'] = max(0, projected_score)
            predictions['risk_level'] = 'high' if projected_score < 60 else 'medium'

            predictions['recommendations'].extend([
                "Monitor data sources more frequently",
                "Review data validation rules",
                "Check for systematic data collection issues",
                "Consider implementing additional data quality checks"
            ])

        elif trends['status'] == 'improving':
            projected_score = trends['current_score'] + (trends['overall_trend'] * 2)

            predictions['projected_quality'] = min(100, projected_score)
            predictions['risk_level'] = 'low'

            predictions['recommendations'].extend([
                "Continue current data quality practices",
                "Document successful quality improvements",
                "Monitor for stability in improvements"
            ])

        else:  # stable
            predictions['projected_quality'] = trends['current_score']
            predictions['risk_level'] = 'low' if trends['current_score'] > 75 else 'medium'

            predictions['recommendations'].extend([
                "Maintain current quality monitoring",
                "Periodic review of data quality thresholds"
            ])

        return predictions


# Export main classes
__all__ = [
    'AdvancedDataQualityScorer',
    'QualityMetrics',
    'QualityDimension'
]