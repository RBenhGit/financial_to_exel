"""
Alert Manager for User Preference System

Manages display, persistence, and user interaction with preference validation alerts
and provides intelligent notifications about configuration issues.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from .preference_validator import ValidationAlert, ValidationResult, ValidationSeverity, ValidationCategory
from .user_profile import UserPreferences

logger = logging.getLogger(__name__)


@dataclass
class AlertState:
    """Tracks user interaction with alerts"""

    alert_id: str
    shown_count: int = 0
    dismissed_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    user_action_taken: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AlertConfiguration:
    """Configuration for alert display and behavior"""

    # Display settings
    show_info_alerts: bool = True
    show_warning_alerts: bool = True
    show_error_alerts: bool = True
    auto_dismiss_after_days: int = 7

    # Frequency settings
    max_shows_per_alert: int = 3
    snooze_duration_hours: int = 24

    # Category-specific settings
    category_settings: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'financial_consistency': {'priority': 1, 'auto_fix': True},
        'risk_assessment': {'priority': 2, 'auto_fix': False},
        'regional_currency': {'priority': 3, 'auto_fix': False},
        'methodology_params': {'priority': 2, 'auto_fix': True},
        'performance_optimization': {'priority': 4, 'auto_fix': False},
        'data_quality': {'priority': 3, 'auto_fix': False}
    })


class AlertManager:
    """Manages preference validation alerts and user notifications"""

    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the alert manager

        Args:
            data_directory: Directory to store alert state files
        """
        # Set up data directory
        if data_directory:
            self.data_dir = Path(data_directory)
        else:
            self.data_dir = Path("data") / "user_preferences" / "alerts"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Alert state tracking
        self.alert_states: Dict[str, AlertState] = {}
        self.configuration = AlertConfiguration()

        # Event handlers
        self.alert_handlers: Dict[str, Callable] = {}

        self._load_alert_states()
        self._load_configuration()

        logger.info(f"AlertManager initialized with data directory: {self.data_dir}")

    def process_validation_result(
        self,
        validation_result: ValidationResult,
        user_id: str,
        preferences: UserPreferences
    ) -> List[ValidationAlert]:
        """
        Process validation results and return alerts to display

        Args:
            validation_result: Result from preference validation
            user_id: User identifier
            preferences: Current user preferences

        Returns:
            List of alerts to display to user
        """
        # Filter alerts based on configuration and state
        alerts_to_show = []

        for alert in validation_result.alerts:
            if self._should_show_alert(alert, user_id):
                # Update alert state
                alert_id = self._generate_alert_id(alert, user_id)
                self._update_alert_state(alert_id, alert)

                # Add contextual information
                enhanced_alert = self._enhance_alert(alert, preferences)
                alerts_to_show.append(enhanced_alert)

        # Sort alerts by priority and severity
        alerts_to_show.sort(key=self._get_alert_priority, reverse=True)

        # Trigger alert handlers
        self._trigger_alert_handlers(alerts_to_show, user_id)

        logger.info(f"Processed {len(validation_result.alerts)} alerts, showing {len(alerts_to_show)} to user {user_id}")
        return alerts_to_show

    def dismiss_alert(self, alert_id: str, user_action: Optional[str] = None) -> bool:
        """
        Dismiss an alert

        Args:
            alert_id: Unique alert identifier
            user_action: Optional action taken by user

        Returns:
            True if successful
        """
        try:
            if alert_id in self.alert_states:
                self.alert_states[alert_id].dismissed_at = datetime.now()
                self.alert_states[alert_id].user_action_taken = user_action
                self._save_alert_states()
                logger.debug(f"Alert dismissed: {alert_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to dismiss alert {alert_id}: {e}")
            return False

    def snooze_alert(self, alert_id: str, hours: Optional[int] = None) -> bool:
        """
        Snooze an alert for a specified duration

        Args:
            alert_id: Unique alert identifier
            hours: Hours to snooze (uses default if None)

        Returns:
            True if successful
        """
        try:
            if alert_id in self.alert_states:
                snooze_hours = hours or self.configuration.snooze_duration_hours
                self.alert_states[alert_id].snoozed_until = (
                    datetime.now() + timedelta(hours=snooze_hours)
                )
                self._save_alert_states()
                logger.debug(f"Alert snoozed for {snooze_hours} hours: {alert_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to snooze alert {alert_id}: {e}")
            return False

    def get_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about alerts for a user

        Args:
            user_id: User identifier

        Returns:
            Dictionary with alert statistics
        """
        user_alerts = [
            state for alert_id, state in self.alert_states.items()
            if alert_id.startswith(f"{user_id}_")
        ]

        total_alerts = len(user_alerts)
        dismissed_alerts = len([a for a in user_alerts if a.dismissed_at])
        snoozed_alerts = len([
            a for a in user_alerts
            if a.snoozed_until and a.snoozed_until > datetime.now()
        ])

        return {
            'total_alerts': total_alerts,
            'dismissed_alerts': dismissed_alerts,
            'snoozed_alerts': snoozed_alerts,
            'active_alerts': total_alerts - dismissed_alerts - snoozed_alerts,
            'average_shows_per_alert': (
                sum(a.shown_count for a in user_alerts) / total_alerts
                if total_alerts > 0 else 0
            )
        }

    def register_alert_handler(self, category: str, handler: Callable) -> None:
        """
        Register a handler for specific alert categories

        Args:
            category: Alert category to handle
            handler: Function to call when category alerts are triggered
        """
        self.alert_handlers[category] = handler
        logger.debug(f"Registered alert handler for category: {category}")

    def update_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update alert configuration

        Args:
            config_updates: Dictionary of configuration updates

        Returns:
            True if successful
        """
        try:
            for key, value in config_updates.items():
                if hasattr(self.configuration, key):
                    setattr(self.configuration, key, value)

            self._save_configuration()
            logger.info("Alert configuration updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False

    def generate_alert_summary(self, user_id: str, include_historical: bool = False) -> Dict[str, Any]:
        """
        Generate a comprehensive alert summary for a user

        Args:
            user_id: User identifier
            include_historical: Include dismissed and resolved alerts

        Returns:
            Alert summary dictionary
        """
        user_alerts = [
            state for alert_id, state in self.alert_states.items()
            if alert_id.startswith(f"{user_id}_")
        ]

        if not include_historical:
            user_alerts = [
                a for a in user_alerts
                if not a.dismissed_at and (not a.snoozed_until or a.snoozed_until <= datetime.now())
            ]

        # Group by category
        category_groups = {}
        for alert_state in user_alerts:
            # Extract category from alert_id (simplified)
            category = "unknown"
            for cat in ValidationCategory:
                if cat.value in alert_state.alert_id.lower():
                    category = cat.value
                    break

            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(alert_state)

        return {
            'user_id': user_id,
            'total_alerts': len(user_alerts),
            'category_breakdown': {
                cat: len(alerts) for cat, alerts in category_groups.items()
            },
            'recent_activity': self._get_recent_alert_activity(user_id),
            'recommendations': self._generate_alert_recommendations(user_alerts)
        }

    def _should_show_alert(self, alert: ValidationAlert, user_id: str) -> bool:
        """Determine if an alert should be shown to the user"""
        alert_id = self._generate_alert_id(alert, user_id)

        # Check configuration settings
        if alert.severity == ValidationSeverity.INFO and not self.configuration.show_info_alerts:
            return False
        if alert.severity == ValidationSeverity.WARNING and not self.configuration.show_warning_alerts:
            return False
        if alert.severity == ValidationSeverity.ERROR and not self.configuration.show_error_alerts:
            return False

        # Check alert state
        if alert_id in self.alert_states:
            state = self.alert_states[alert_id]

            # Check if dismissed
            if state.dismissed_at:
                return False

            # Check if snoozed
            if state.snoozed_until and state.snoozed_until > datetime.now():
                return False

            # Check show count limit
            if state.shown_count >= self.configuration.max_shows_per_alert:
                return False

            # Check auto-dismiss after time
            time_limit = datetime.now() - timedelta(days=self.configuration.auto_dismiss_after_days)
            if state.created_at < time_limit:
                return False

        return True

    def _generate_alert_id(self, alert: ValidationAlert, user_id: str) -> str:
        """Generate a unique alert identifier"""
        # Create stable ID based on user, category, parameter, and content hash
        content_hash = hash(f"{alert.title}_{alert.message}_{alert.parameter}")
        return f"{user_id}_{alert.category.value}_{alert.parameter}_{abs(content_hash) % 10000}"

    def _update_alert_state(self, alert_id: str, alert: ValidationAlert) -> None:
        """Update the state for an alert"""
        if alert_id not in self.alert_states:
            self.alert_states[alert_id] = AlertState(alert_id=alert_id)

        self.alert_states[alert_id].shown_count += 1
        self._save_alert_states()

    def _enhance_alert(self, alert: ValidationAlert, preferences: UserPreferences) -> ValidationAlert:
        """Add contextual information to an alert"""
        # Add methodology-specific context
        methodology = preferences.financial.methodology.value
        if "methodology" not in alert.explanation.lower():
            alert.explanation += f" (Current methodology: {methodology})"

        # Add auto-fix suggestions for applicable alerts
        category_config = self.configuration.category_settings.get(alert.category.value, {})
        if category_config.get('auto_fix', False) and alert.suggested_value is not None:
            if not alert.correction_action:
                alert.correction_action = f"Auto-fix available: Set {alert.parameter} to {alert.suggested_value}"

        return alert

    def _get_alert_priority(self, alert: ValidationAlert) -> int:
        """Calculate alert priority for sorting"""
        severity_weight = {
            ValidationSeverity.CRITICAL: 1000,
            ValidationSeverity.ERROR: 500,
            ValidationSeverity.WARNING: 100,
            ValidationSeverity.INFO: 10
        }.get(alert.severity, 1)

        category_priority = self.configuration.category_settings.get(
            alert.category.value, {}
        ).get('priority', 5)

        return severity_weight + (10 - category_priority) * 10

    def _trigger_alert_handlers(self, alerts: List[ValidationAlert], user_id: str) -> None:
        """Trigger registered handlers for alerts"""
        for alert in alerts:
            handler = self.alert_handlers.get(alert.category.value)
            if handler:
                try:
                    handler(alert, user_id)
                except Exception as e:
                    logger.error(f"Alert handler failed for {alert.category.value}: {e}")

    def _get_recent_alert_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent alert activity for a user"""
        user_alerts = [
            state for alert_id, state in self.alert_states.items()
            if alert_id.startswith(f"{user_id}_")
        ]

        # Sort by most recent activity
        recent_alerts = sorted(
            user_alerts,
            key=lambda x: max(
                x.created_at,
                x.dismissed_at or datetime.min,
                x.snoozed_until or datetime.min
            ),
            reverse=True
        )[:10]  # Last 10 activities

        return [
            {
                'alert_id': state.alert_id,
                'created_at': state.created_at.isoformat(),
                'shown_count': state.shown_count,
                'status': 'dismissed' if state.dismissed_at else
                         'snoozed' if state.snoozed_until and state.snoozed_until > datetime.now() else
                         'active'
            }
            for state in recent_alerts
        ]

    def _generate_alert_recommendations(self, alert_states: List[AlertState]) -> List[str]:
        """Generate recommendations based on alert patterns"""
        recommendations = []

        # Check for patterns in dismissed alerts
        dismissed_count = len([a for a in alert_states if a.dismissed_at])
        if dismissed_count > 5:
            recommendations.append(
                "Consider reviewing alert settings - many alerts have been dismissed"
            )

        # Check for frequently shown alerts
        high_show_count = [a for a in alert_states if a.shown_count > 2]
        if high_show_count:
            recommendations.append(
                f"{len(high_show_count)} alerts shown multiple times - consider addressing root causes"
            )

        return recommendations

    def _load_alert_states(self) -> None:
        """Load alert states from disk"""
        try:
            states_file = self.data_dir / "alert_states.json"
            if states_file.exists():
                with open(states_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for alert_id, state_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'created_at' in state_data:
                        state_data['created_at'] = datetime.fromisoformat(state_data['created_at'])
                    if 'dismissed_at' in state_data and state_data['dismissed_at']:
                        state_data['dismissed_at'] = datetime.fromisoformat(state_data['dismissed_at'])
                    if 'snoozed_until' in state_data and state_data['snoozed_until']:
                        state_data['snoozed_until'] = datetime.fromisoformat(state_data['snoozed_until'])

                    self.alert_states[alert_id] = AlertState(**state_data)

                logger.debug(f"Loaded {len(self.alert_states)} alert states")
        except Exception as e:
            logger.warning(f"Failed to load alert states: {e}")

    def _save_alert_states(self) -> None:
        """Save alert states to disk"""
        try:
            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            states_file = self.data_dir / "alert_states.json"

            # Convert to serializable format
            data = {}
            for alert_id, state in self.alert_states.items():
                state_dict = {
                    'alert_id': state.alert_id,
                    'shown_count': state.shown_count,
                    'user_action_taken': state.user_action_taken,
                    'created_at': state.created_at.isoformat()
                }
                if state.dismissed_at:
                    state_dict['dismissed_at'] = state.dismissed_at.isoformat()
                if state.snoozed_until:
                    state_dict['snoozed_until'] = state.snoozed_until.isoformat()

                data[alert_id] = state_dict

            with open(states_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug("Alert states saved")
        except Exception as e:
            logger.error(f"Failed to save alert states: {e}")

    def _load_configuration(self) -> None:
        """Load alert configuration from disk"""
        try:
            config_file = self.data_dir / "alert_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Update configuration with loaded data
                for key, value in data.items():
                    if hasattr(self.configuration, key):
                        setattr(self.configuration, key, value)

                logger.debug("Alert configuration loaded")
        except Exception as e:
            logger.warning(f"Failed to load alert configuration: {e}")

    def _save_configuration(self) -> None:
        """Save alert configuration to disk"""
        try:
            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            config_file = self.data_dir / "alert_config.json"

            # Convert configuration to dict
            config_dict = {
                'show_info_alerts': self.configuration.show_info_alerts,
                'show_warning_alerts': self.configuration.show_warning_alerts,
                'show_error_alerts': self.configuration.show_error_alerts,
                'auto_dismiss_after_days': self.configuration.auto_dismiss_after_days,
                'max_shows_per_alert': self.configuration.max_shows_per_alert,
                'snooze_duration_hours': self.configuration.snooze_duration_hours,
                'category_settings': self.configuration.category_settings
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)

            logger.debug("Alert configuration saved")
        except Exception as e:
            logger.error(f"Failed to save alert configuration: {e}")


# Global instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(data_directory: Optional[str] = None) -> AlertManager:
    """
    Get the global alert manager instance

    Args:
        data_directory: Directory for alert state files

    Returns:
        AlertManager instance
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(data_directory)
    return _alert_manager


def set_alert_manager(manager: AlertManager) -> None:
    """Set a custom alert manager instance"""
    global _alert_manager
    _alert_manager = manager