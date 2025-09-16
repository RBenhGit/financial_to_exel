"""
Predictive Data Quality Alerting System
======================================

This module extends the existing alerting system with predictive capabilities,
providing early warnings for potential data quality issues based on trend analysis
and machine learning-based predictions.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

# Import existing alerting infrastructure
from .alerting_system import (
    AlertSeverity, AlertType, Alert, AlertChannel,
    LogAlertChannel
)
from .health_monitor import HealthMetrics, HealthStatus

# Import advanced quality scoring
from ..advanced_data_quality_scorer import AdvancedDataQualityScorer, QualityMetrics

logger = logging.getLogger(__name__)


class PredictiveAlertType(AlertType):
    """Extended alert types for predictive alerts"""
    QUALITY_DEGRADATION_PREDICTED = "quality_degradation_predicted"
    TREND_ANOMALY_DETECTED = "trend_anomaly_detected"
    THRESHOLD_BREACH_IMMINENT = "threshold_breach_imminent"
    DATA_STALENESS_WARNING = "data_staleness_warning"
    PATTERN_DEVIATION = "pattern_deviation"


@dataclass
class PredictiveAlert(Alert):
    """Enhanced alert with predictive information"""
    prediction_confidence: float = 0.0
    time_to_impact: Optional[timedelta] = None
    predicted_severity: Optional[AlertSeverity] = None
    trend_data: Dict[str, Any] = field(default_factory=dict)
    mitigation_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert predictive alert to dictionary for serialization"""
        base_dict = super().to_dict()
        base_dict.update({
            'prediction_confidence': self.prediction_confidence,
            'time_to_impact': self.time_to_impact.total_seconds() if self.time_to_impact else None,
            'predicted_severity': self.predicted_severity.value if self.predicted_severity else None,
            'trend_data': self.trend_data,
            'mitigation_suggestions': self.mitigation_suggestions,
            'alert_type': 'predictive'
        })
        return base_dict


class PredictiveQualityAlerting:
    """
    Predictive alerting system for data quality issues
    """

    def __init__(self, quality_scorer: AdvancedDataQualityScorer, config: Dict[str, Any] = None):
        """
        Initialize predictive alerting system

        Args:
            quality_scorer: Advanced data quality scorer instance
            config: Configuration for predictive alerting
        """
        self.quality_scorer = quality_scorer
        self.config = config or self._get_default_config()
        self.alert_channels: List[AlertChannel] = []
        self.active_alerts: Set[str] = set()

        # Initialize alert history tracking
        self.alert_history_file = Path("data/cache/predictive_alerts_history.json")
        self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
        self.alert_history = self._load_alert_history()

        # Setup default log channel
        self.add_alert_channel(LogAlertChannel({'enabled': True}))

        logger.info("Predictive Quality Alerting system initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for predictive alerting"""
        return {
            'prediction_thresholds': {
                'degradation_slope': -2.0,  # Quality dropping by 2% per period
                'confidence_threshold': 0.7,  # 70% confidence required
                'time_horizon_hours': 24,
                'anomaly_std_threshold': 2.0
            },
            'alert_settings': {
                'max_alerts_per_hour': 10,
                'alert_cooldown_minutes': 30,
                'escalation_threshold_hours': 4
            },
            'trend_analysis': {
                'min_data_points': 5,
                'lookback_periods': 10,
                'seasonality_check': True
            }
        }

    def _load_alert_history(self) -> List[Dict[str, Any]]:
        """Load alert history from file"""
        try:
            if self.alert_history_file.exists():
                with open(self.alert_history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load alert history: {e}")

        return []

    def _save_alert_history(self):
        """Save alert history to file"""
        try:
            # Keep only last 1000 alerts to manage file size
            recent_history = self.alert_history[-1000:] if len(self.alert_history) > 1000 else self.alert_history

            with open(self.alert_history_file, 'w') as f:
                json.dump(recent_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alert history: {e}")

    def add_alert_channel(self, channel: AlertChannel):
        """Add an alert notification channel"""
        self.alert_channels.append(channel)

    def check_predictive_alerts(self) -> List[PredictiveAlert]:
        """
        Analyze quality trends and generate predictive alerts

        Returns:
            List of predictive alerts generated
        """
        alerts_generated = []

        try:
            # Get quality trends and predictions
            trends = self.quality_scorer.get_quality_trends()
            predictions = self.quality_scorer.predict_quality_issues()

            # Check for degradation trends
            degradation_alerts = self._check_degradation_trends(trends, predictions)
            alerts_generated.extend(degradation_alerts)

            # Check for anomaly patterns
            anomaly_alerts = self._check_anomaly_patterns()
            alerts_generated.extend(anomaly_alerts)

            # Check for threshold breach predictions
            threshold_alerts = self._check_threshold_predictions(predictions)
            alerts_generated.extend(threshold_alerts)

            # Check for data staleness
            staleness_alerts = self._check_data_staleness()
            alerts_generated.extend(staleness_alerts)

            # Process and send alerts
            for alert in alerts_generated:
                self._process_alert(alert)

            logger.info(f"Generated {len(alerts_generated)} predictive alerts")

        except Exception as e:
            logger.error(f"Error checking predictive alerts: {e}")

        return alerts_generated

    def _check_degradation_trends(self, trends: Dict[str, Any], predictions: Dict[str, Any]) -> List[PredictiveAlert]:
        """Check for quality degradation trends"""
        alerts = []

        if trends.get('status') != 'degrading':
            return alerts

        # Extract trend information
        overall_trend = trends.get('overall_trend', 0)
        current_score = trends.get('current_score', 100)
        degradation_threshold = self.config['prediction_thresholds']['degradation_slope']

        if overall_trend < degradation_threshold:
            # Calculate time to critical threshold
            critical_threshold = 60.0  # Assuming 60% as critical
            if overall_trend < 0:
                periods_to_critical = (current_score - critical_threshold) / abs(overall_trend)
                time_to_impact = timedelta(hours=periods_to_critical * 6)  # Assuming 6-hour periods
            else:
                time_to_impact = None

            alert = PredictiveAlert(
                alert_id=f"degradation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                alert_type=PredictiveAlertType.QUALITY_DEGRADATION_PREDICTED,
                severity=AlertSeverity.WARNING if current_score > 70 else AlertSeverity.CRITICAL,
                source_name="predictive_system",
                message=f"Quality degradation predicted: {overall_trend:.2f}% per period. Current: {current_score:.1f}%",
                timestamp=datetime.now(),
                metrics=self._create_dummy_metrics(current_score),
                prediction_confidence=0.8,  # High confidence for trend-based predictions
                time_to_impact=time_to_impact,
                predicted_severity=AlertSeverity.CRITICAL if overall_trend < -5 else AlertSeverity.WARNING,
                trend_data=trends,
                mitigation_suggestions=[
                    "Review data source configurations",
                    "Check for systematic data collection issues",
                    "Implement additional data validation rules",
                    "Monitor data pipelines for failures"
                ]
            )

            alerts.append(alert)

        return alerts

    def _check_anomaly_patterns(self) -> List[PredictiveAlert]:
        """Check for anomalous patterns in quality metrics"""
        alerts = []

        try:
            # Get recent quality history
            history = self.quality_scorer.quality_history

            if len(history) < self.config['trend_analysis']['min_data_points']:
                return alerts

            # Analyze recent data for anomalies
            recent_scores = [m.overall_score for m in history[-10:]]  # Last 10 measurements

            if len(recent_scores) >= 5:
                import numpy as np

                mean_score = np.mean(recent_scores[:-1])  # Exclude latest for comparison
                std_score = np.std(recent_scores[:-1])
                latest_score = recent_scores[-1]

                # Check for anomaly using z-score
                if std_score > 0:
                    z_score = abs(latest_score - mean_score) / std_score
                    anomaly_threshold = self.config['prediction_thresholds']['anomaly_std_threshold']

                    if z_score > anomaly_threshold:
                        alert = PredictiveAlert(
                            alert_id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            alert_type=PredictiveAlertType.TREND_ANOMALY_DETECTED,
                            severity=AlertSeverity.WARNING,
                            source_name="predictive_system",
                            message=f"Quality score anomaly detected: {latest_score:.1f}% (z-score: {z_score:.2f})",
                            timestamp=datetime.now(),
                            metrics=self._create_dummy_metrics(latest_score),
                            prediction_confidence=min(0.9, z_score / 10),  # Higher z-score = higher confidence
                            mitigation_suggestions=[
                                "Investigate recent changes to data sources",
                                "Check for data collection anomalies",
                                "Verify data processing pipeline integrity"
                            ]
                        )

                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking anomaly patterns: {e}")

        return alerts

    def _check_threshold_predictions(self, predictions: Dict[str, Any]) -> List[PredictiveAlert]:
        """Check for predicted threshold breaches"""
        alerts = []

        if predictions.get('status') == 'error' or predictions.get('risk_level') != 'high':
            return alerts

        current_quality = predictions.get('current_quality', 100)
        projected_quality = predictions.get('projected_quality', 100)
        prediction_hours = predictions.get('prediction_window_hours', 24)

        # Check if projected quality will breach critical threshold
        critical_threshold = 60.0
        if projected_quality < critical_threshold and current_quality >= critical_threshold:
            alert = PredictiveAlert(
                alert_id=f"threshold_breach_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                alert_type=PredictiveAlertType.THRESHOLD_BREACH_IMMINENT,
                severity=AlertSeverity.CRITICAL,
                source_name="predictive_system",
                message=f"Critical threshold breach predicted within {prediction_hours}h: {projected_quality:.1f}%",
                timestamp=datetime.now(),
                metrics=self._create_dummy_metrics(current_quality),
                prediction_confidence=0.75,
                time_to_impact=timedelta(hours=prediction_hours),
                predicted_severity=AlertSeverity.EMERGENCY,
                mitigation_suggestions=predictions.get('recommendations', [])
            )

            alerts.append(alert)

        return alerts

    def _check_data_staleness(self) -> List[PredictiveAlert]:
        """Check for data staleness issues"""
        alerts = []

        try:
            if not self.quality_scorer.quality_history:
                return alerts

            latest_metrics = self.quality_scorer.quality_history[-1]
            time_since_last = datetime.now() - latest_metrics.timestamp
            staleness_threshold = timedelta(hours=6)  # 6 hours without new data

            if time_since_last > staleness_threshold:
                alert = PredictiveAlert(
                    alert_id=f"staleness_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=PredictiveAlertType.DATA_STALENESS_WARNING,
                    severity=AlertSeverity.WARNING,
                    source_name="predictive_system",
                    message=f"Data staleness detected: {time_since_last.total_seconds() / 3600:.1f} hours since last update",
                    timestamp=datetime.now(),
                    metrics=self._create_dummy_metrics(0),
                    prediction_confidence=1.0,  # High confidence for time-based checks
                    mitigation_suggestions=[
                        "Check data pipeline status",
                        "Verify API connectivity",
                        "Review automated data collection schedules"
                    ]
                )

                alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking data staleness: {e}")

        return alerts

    def _create_dummy_metrics(self, score: float) -> HealthMetrics:
        """Create dummy health metrics for alerts"""
        # This is a simplified version for demonstration
        # In practice, this would be integrated with the actual health monitoring system
        from ..monitoring.health_monitor import HealthMetrics, HealthStatus

        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return HealthMetrics(
            response_time_ms=100.0,
            success_rate=score / 100.0,
            error_rate=(100 - score) / 100.0,
            health_status=status,
            overall_score=score
        )

    def _process_alert(self, alert: PredictiveAlert):
        """Process and send a predictive alert"""
        # Check for alert cooldown
        if not self._should_send_alert(alert):
            return

        # Add to active alerts
        self.active_alerts.add(alert.alert_id)

        # Send to all configured channels
        for channel in self.alert_channels:
            try:
                if channel.enabled:
                    success = channel.send_alert(alert)
                    if success:
                        logger.info(f"Predictive alert {alert.alert_id} sent via {channel.__class__.__name__}")
                    else:
                        logger.warning(f"Failed to send alert {alert.alert_id} via {channel.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error sending alert via {channel.__class__.__name__}: {e}")

        # Add to history
        self.alert_history.append(alert.to_dict())
        self._save_alert_history()

    def _should_send_alert(self, alert: PredictiveAlert) -> bool:
        """Check if alert should be sent based on cooldown and rate limiting"""
        # Check rate limiting
        recent_alerts = [
            a for a in self.alert_history[-50:]  # Last 50 alerts
            if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)
        ]

        max_alerts_per_hour = self.config['alert_settings']['max_alerts_per_hour']
        if len(recent_alerts) >= max_alerts_per_hour:
            logger.warning(f"Alert rate limit reached: {len(recent_alerts)}/{max_alerts_per_hour} per hour")
            return False

        # Check cooldown for similar alert types
        cooldown_minutes = self.config['alert_settings']['alert_cooldown_minutes']
        similar_alerts = [
            a for a in recent_alerts
            if a.get('alert_type') == alert.alert_type.value
            and datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(minutes=cooldown_minutes)
        ]

        if similar_alerts:
            logger.info(f"Alert {alert.alert_type.value} in cooldown period")
            return False

        return True

    def get_alert_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get summary of recent predictive alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]

        summary = {
            'total_alerts': len(recent_alerts),
            'alert_types': {},
            'severity_breakdown': {},
            'average_confidence': 0.0,
            'most_recent': None
        }

        if recent_alerts:
            # Count by type
            for alert in recent_alerts:
                alert_type = alert.get('alert_type', 'unknown')
                summary['alert_types'][alert_type] = summary['alert_types'].get(alert_type, 0) + 1

                severity = alert.get('severity', 'unknown')
                summary['severity_breakdown'][severity] = summary['severity_breakdown'].get(severity, 0) + 1

            # Calculate average confidence
            confidences = [alert.get('prediction_confidence', 0) for alert in recent_alerts]
            summary['average_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0

            # Most recent alert
            summary['most_recent'] = recent_alerts[-1]

        return summary


class StreamlitPredictiveAlertChannel(AlertChannel):
    """Alert channel that displays predictive alerts in Streamlit"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session_alerts = []

    def send_alert(self, alert: PredictiveAlert) -> bool:
        """Add alert to Streamlit session for display"""
        try:
            import streamlit as st

            # Store alert in session state
            if 'predictive_alerts' not in st.session_state:
                st.session_state.predictive_alerts = []

            st.session_state.predictive_alerts.append(alert.to_dict())

            # Keep only last 10 alerts in session
            if len(st.session_state.predictive_alerts) > 10:
                st.session_state.predictive_alerts = st.session_state.predictive_alerts[-10:]

            return True

        except Exception as e:
            self.logger.error(f"Failed to send Streamlit alert: {e}")
            return False


# Export main classes
__all__ = [
    'PredictiveQualityAlerting',
    'PredictiveAlert',
    'PredictiveAlertType',
    'StreamlitPredictiveAlertChannel'
]