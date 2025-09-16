"""
Alerting System for Data Source Health Monitoring
===============================================

Provides comprehensive alerting capabilities for data source health issues,
including configurable thresholds, multiple notification channels, and alert management.
"""

import logging
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart

from .health_monitor import HealthMetrics, HealthStatus


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of alerts that can be triggered"""
    RESPONSE_TIME_HIGH = "response_time_high"
    SUCCESS_RATE_LOW = "success_rate_low"
    DATA_QUALITY_LOW = "data_quality_low"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    ERROR_RATE_HIGH = "error_rate_high"
    AVAILABILITY_LOW = "availability_low"


@dataclass
class Alert:
    """Container for alert information"""

    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    source_name: str
    message: str
    timestamp: datetime
    metrics: HealthMetrics
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization"""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'source_name': self.source_name,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_timestamp': self.resolved_timestamp.isoformat() if self.resolved_timestamp else None,
            'metadata': self.metadata,
            'metrics_summary': {
                'response_time_ms': self.metrics.response_time_ms,
                'success_rate': self.metrics.success_rate,
                'health_status': self.metrics.health_status.value,
                'overall_score': self.metrics.overall_score
            }
        }


class AlertChannel:
    """Base class for alert notification channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert through this channel.

        Args:
            alert: Alert to send

        Returns:
            True if alert was sent successfully
        """
        raise NotImplementedError


class LogAlertChannel(AlertChannel):
    """Alert channel that writes to log files"""

    def send_alert(self, alert: Alert) -> bool:
        """Send alert to log"""
        try:
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.CRITICAL: logging.CRITICAL,
                AlertSeverity.EMERGENCY: logging.CRITICAL
            }.get(alert.severity, logging.WARNING)

            self.logger.log(
                log_level,
                f"[{alert.severity.value.upper()}] {alert.source_name}: {alert.message}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send log alert: {e}")
            return False


class EmailAlertChannel(AlertChannel):
    """Alert channel that sends email notifications"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email', 'alerts@financialanalysis.com')
        self.to_emails = config.get('to_emails', [])
        self.use_tls = config.get('use_tls', True)

    def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            if not self.to_emails:
                self.logger.warning("No email recipients configured")
                return False

            # Create email message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] Data Source Alert: {alert.source_name}"

            # Create email body
            body = self._create_email_body(alert)
            msg.attach(MimeText(body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"Email alert sent for {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

    def _create_email_body(self, alert: Alert) -> str:
        """Create formatted email body for alert"""
        severity_colors = {
            AlertSeverity.INFO: '#17a2b8',
            AlertSeverity.WARNING: '#ffc107',
            AlertSeverity.CRITICAL: '#dc3545',
            AlertSeverity.EMERGENCY: '#6f42c1'
        }

        color = severity_colors.get(alert.severity, '#6c757d')

        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h2>Data Source Alert</h2>
                    <p><strong>{alert.severity.value.upper()}</strong></p>
                </div>

                <div style="padding: 20px; background-color: #f8f9fa;">
                    <h3>Alert Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td><strong>Source:</strong></td><td>{alert.source_name}</td></tr>
                        <tr><td><strong>Type:</strong></td><td>{alert.alert_type.value}</td></tr>
                        <tr><td><strong>Time:</strong></td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                        <tr><td><strong>Message:</strong></td><td>{alert.message}</td></tr>
                    </table>
                </div>

                <div style="padding: 20px; background-color: #ffffff;">
                    <h3>Health Metrics</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td><strong>Health Status:</strong></td><td>{alert.metrics.health_status.value}</td></tr>
                        <tr><td><strong>Overall Score:</strong></td><td>{alert.metrics.overall_score:.1f}%</td></tr>
                        <tr><td><strong>Response Time:</strong></td><td>{alert.metrics.response_time_ms:.0f}ms</td></tr>
                        <tr><td><strong>Success Rate:</strong></td><td>{alert.metrics.success_rate * 100:.1f}%</td></tr>
                        <tr><td><strong>Data Quality:</strong></td><td>{alert.metrics.data_quality_score * 100:.1f}%</td></tr>
                        <tr><td><strong>Availability:</strong></td><td>{alert.metrics.availability_percentage:.1f}%</td></tr>
                    </table>
                </div>

                <div style="padding: 20px; background-color: #e9ecef; text-align: center;">
                    <p><small>This alert was generated by the Financial Analysis Data Source Monitoring System</small></p>
                </div>
            </div>
        </body>
        </html>
        """


class WebhookAlertChannel(AlertChannel):
    """Alert channel that sends webhook notifications"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.timeout = config.get('timeout', 10)

    def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook"""
        try:
            import requests

            if not self.webhook_url:
                self.logger.warning("No webhook URL configured")
                return False

            payload = {
                'alert': alert.to_dict(),
                'timestamp': datetime.now().isoformat()
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            self.logger.info(f"Webhook alert sent for {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False


class AlertingSystem:
    """
    Comprehensive alerting system for data source health monitoring.

    Manages alert rules, thresholds, channels, and alert lifecycle.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the alerting system.

        Args:
            config: Configuration dictionary for alerting settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.AlertingSystem")

        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_alerts: Set[str] = set()

        # Alert channels
        self.channels: List[AlertChannel] = []
        self._setup_channels()

        # Alert thresholds
        self.thresholds = self._load_thresholds()

        # Alert rules
        self.alert_rules: Dict[AlertType, Callable[[HealthMetrics], bool]] = {
            AlertType.RESPONSE_TIME_HIGH: self._check_response_time,
            AlertType.SUCCESS_RATE_LOW: self._check_success_rate,
            AlertType.DATA_QUALITY_LOW: self._check_data_quality,
            AlertType.SOURCE_UNAVAILABLE: self._check_availability,
            AlertType.CONSECUTIVE_FAILURES: self._check_consecutive_failures,
            AlertType.ERROR_RATE_HIGH: self._check_error_rate,
            AlertType.AVAILABILITY_LOW: self._check_availability_low,
        }

        # Suppression settings
        self.suppression_duration = timedelta(
            minutes=self.config.get('suppression_duration_minutes', 15)
        )
        self.max_alerts_per_hour = self.config.get('max_alerts_per_hour', 10)

        # Storage
        self.alerts_file = Path(self.config.get('alerts_file', 'data/cache/alerts.json'))
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("Alerting system initialized")

    def _setup_channels(self) -> None:
        """Setup alert notification channels"""
        channels_config = self.config.get('channels', {})

        # Log channel (always enabled)
        if channels_config.get('log', {}).get('enabled', True):
            self.channels.append(LogAlertChannel(channels_config.get('log', {})))

        # Email channel
        if channels_config.get('email', {}).get('enabled', False):
            self.channels.append(EmailAlertChannel(channels_config.get('email', {})))

        # Webhook channel
        if channels_config.get('webhook', {}).get('enabled', False):
            self.channels.append(WebhookAlertChannel(channels_config.get('webhook', {})))

        self.logger.info(f"Configured {len(self.channels)} alert channels")

    def _load_thresholds(self) -> Dict[str, Any]:
        """Load alert thresholds from configuration"""
        default_thresholds = {
            'response_time_ms': 5000,  # 5 seconds
            'success_rate_min': 0.9,  # 90%
            'data_quality_min': 0.8,  # 80%
            'availability_min': 0.95,  # 95%
            'consecutive_failures_max': 5,
            'error_rate_max': 0.1,  # 10%
        }

        user_thresholds = self.config.get('thresholds', {})
        return {**default_thresholds, **user_thresholds}

    def check_metrics_for_alerts(self, metrics: HealthMetrics) -> List[Alert]:
        """
        Check health metrics against alert rules and generate alerts.

        Args:
            metrics: Health metrics to check

        Returns:
            List of generated alerts
        """
        generated_alerts = []

        for alert_type, rule_func in self.alert_rules.items():
            try:
                if rule_func(metrics):
                    alert = self._create_alert(alert_type, metrics)
                    if alert and not self._is_suppressed(alert):
                        generated_alerts.append(alert)
                        self._process_alert(alert)
            except Exception as e:
                self.logger.error(f"Error checking alert rule {alert_type}: {e}")

        return generated_alerts

    def _create_alert(self, alert_type: AlertType, metrics: HealthMetrics) -> Optional[Alert]:
        """Create an alert from metrics and alert type"""
        alert_id = f"{metrics.source_name}_{alert_type.value}_{int(metrics.timestamp.timestamp())}"

        # Check if similar alert already exists
        similar_alert_id = f"{metrics.source_name}_{alert_type.value}"
        if any(aid.startswith(similar_alert_id) for aid in self.active_alerts.keys()):
            return None  # Don't create duplicate alerts

        severity = self._determine_severity(alert_type, metrics)
        message = self._generate_alert_message(alert_type, metrics)

        return Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            source_name=metrics.source_name,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics,
            metadata={'threshold_violation': True}
        )

    def _determine_severity(self, alert_type: AlertType, metrics: HealthMetrics) -> AlertSeverity:
        """Determine alert severity based on type and metrics"""
        if metrics.health_status == HealthStatus.UNAVAILABLE:
            return AlertSeverity.EMERGENCY
        elif metrics.health_status == HealthStatus.CRITICAL:
            return AlertSeverity.CRITICAL
        elif alert_type in [AlertType.SOURCE_UNAVAILABLE, AlertType.CONSECUTIVE_FAILURES]:
            return AlertSeverity.CRITICAL
        elif metrics.health_status == HealthStatus.DEGRADED:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    def _generate_alert_message(self, alert_type: AlertType, metrics: HealthMetrics) -> str:
        """Generate human-readable alert message"""
        messages = {
            AlertType.RESPONSE_TIME_HIGH: f"Response time is {metrics.response_time_ms:.0f}ms (threshold: {self.thresholds['response_time_ms']}ms)",
            AlertType.SUCCESS_RATE_LOW: f"Success rate is {metrics.success_rate * 100:.1f}% (threshold: {self.thresholds['success_rate_min'] * 100:.1f}%)",
            AlertType.DATA_QUALITY_LOW: f"Data quality score is {metrics.data_quality_score * 100:.1f}% (threshold: {self.thresholds['data_quality_min'] * 100:.1f}%)",
            AlertType.SOURCE_UNAVAILABLE: f"Data source is unavailable (health status: {metrics.health_status.value})",
            AlertType.CONSECUTIVE_FAILURES: f"Consecutive failures: {metrics.consecutive_failures} (threshold: {self.thresholds['consecutive_failures_max']})",
            AlertType.ERROR_RATE_HIGH: f"Error rate is {metrics.error_rate * 100:.1f}% (threshold: {self.thresholds['error_rate_max'] * 100:.1f}%)",
            AlertType.AVAILABILITY_LOW: f"Availability is {metrics.availability_percentage:.1f}% (threshold: {self.thresholds['availability_min'] * 100:.1f}%)",
        }
        return messages.get(alert_type, f"Alert triggered for {alert_type.value}")

    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed"""
        suppression_key = f"{alert.source_name}_{alert.alert_type.value}"
        return suppression_key in self.suppressed_alerts

    def _process_alert(self, alert: Alert) -> None:
        """Process and send an alert"""
        # Add to active alerts
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        # Send through all channels
        for channel in self.channels:
            try:
                if channel.enabled:
                    channel.send_alert(alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert via {type(channel).__name__}: {e}")

        # Apply suppression
        suppression_key = f"{alert.source_name}_{alert.alert_type.value}"
        self.suppressed_alerts.add(suppression_key)

        self.logger.info(f"Processed alert: {alert.alert_id}")

    def resolve_alert(self, alert_id: str, resolution_message: str = "") -> bool:
        """
        Resolve an active alert.

        Args:
            alert_id: ID of the alert to resolve
            resolution_message: Optional resolution message

        Returns:
            True if alert was resolved successfully
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_timestamp = datetime.now()
        alert.metadata['resolution_message'] = resolution_message

        # Remove from active alerts
        del self.active_alerts[alert_id]

        # Remove suppression
        suppression_key = f"{alert.source_name}_{alert.alert_type.value}"
        self.suppressed_alerts.discard(suppression_key)

        self.logger.info(f"Resolved alert: {alert_id}")
        return True

    def get_active_alerts(self, source_name: Optional[str] = None) -> List[Alert]:
        """Get list of active alerts, optionally filtered by source"""
        alerts = list(self.active_alerts.values())
        if source_name:
            alerts = [alert for alert in alerts if alert.source_name == source_name]
        return alerts

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alert status"""
        active_alerts = list(self.active_alerts.values())
        severity_counts = {
            severity.value: sum(1 for alert in active_alerts if alert.severity == severity)
            for severity in AlertSeverity
        }

        return {
            'total_active_alerts': len(active_alerts),
            'severity_breakdown': severity_counts,
            'suppressed_count': len(self.suppressed_alerts),
            'total_alerts_today': len([
                alert for alert in self.alert_history
                if alert.timestamp.date() == datetime.now().date()
            ]),
            'last_updated': datetime.now().isoformat()
        }

    # Alert rule functions
    def _check_response_time(self, metrics: HealthMetrics) -> bool:
        """Check if response time exceeds threshold"""
        return metrics.response_time_ms > self.thresholds['response_time_ms']

    def _check_success_rate(self, metrics: HealthMetrics) -> bool:
        """Check if success rate is below threshold"""
        return metrics.success_rate < self.thresholds['success_rate_min']

    def _check_data_quality(self, metrics: HealthMetrics) -> bool:
        """Check if data quality is below threshold"""
        return metrics.data_quality_score < self.thresholds['data_quality_min']

    def _check_availability(self, metrics: HealthMetrics) -> bool:
        """Check if source is unavailable"""
        return metrics.health_status == HealthStatus.UNAVAILABLE

    def _check_consecutive_failures(self, metrics: HealthMetrics) -> bool:
        """Check if consecutive failures exceed threshold"""
        return metrics.consecutive_failures > self.thresholds['consecutive_failures_max']

    def _check_error_rate(self, metrics: HealthMetrics) -> bool:
        """Check if error rate exceeds threshold"""
        return metrics.error_rate > self.thresholds['error_rate_max']

    def _check_availability_low(self, metrics: HealthMetrics) -> bool:
        """Check if availability is below threshold"""
        return (metrics.availability_percentage / 100) < self.thresholds['availability_min']

    def save_alerts(self) -> None:
        """Save alerts to persistent storage"""
        try:
            data = {
                'active_alerts': [alert.to_dict() for alert in self.active_alerts.values()],
                'alert_history': [alert.to_dict() for alert in self.alert_history[-100:]],  # Keep last 100
                'timestamp': datetime.now().isoformat()
            }

            with open(self.alerts_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self.logger.debug(f"Saved alerts to {self.alerts_file}")

        except Exception as e:
            self.logger.error(f"Failed to save alerts: {e}")

    def cleanup_old_alerts(self) -> None:
        """Remove old alerts from history"""
        cutoff_time = datetime.now() - timedelta(days=7)
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

        # Clean up suppression
        self.suppressed_alerts.clear()

        self.logger.info("Cleaned up old alerts and suppressions")