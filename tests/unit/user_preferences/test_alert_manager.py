"""
Tests for the alert management system

Tests alert processing, state management, and user interaction with preference validation alerts.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, AnalysisMethodology
)
from core.user_preferences.preference_validator import (
    ValidationAlert, ValidationResult, ValidationSeverity, ValidationCategory
)
from core.user_preferences.alert_manager import (
    AlertManager, AlertState, AlertConfiguration
)


class TestAlertManager:
    """Test suite for alert management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.alert_manager = AlertManager(data_directory=self.temp_dir)
        self.user_id = "test_user_123"

        # Create test preferences
        self.test_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.10,
                methodology=AnalysisMethodology.MODERATE
            )
        )

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_alert(self, **overrides) -> ValidationAlert:
        """Create a test validation alert"""
        defaults = {
            'category': ValidationCategory.FINANCIAL_CONSISTENCY,
            'severity': ValidationSeverity.WARNING,
            'title': 'Test Alert',
            'message': 'This is a test alert',
            'parameter': 'test_parameter',
            'current_value': 'test_value',
            'suggested_value': 'suggested_value',
            'explanation': 'Test explanation',
            'correction_action': 'Test correction'
        }
        defaults.update(overrides)
        return ValidationAlert(**defaults)

    def create_test_validation_result(self, alerts=None) -> ValidationResult:
        """Create a test validation result"""
        if alerts is None:
            alerts = [self.create_test_alert()]

        return ValidationResult(
            is_valid=len([a for a in alerts if a.severity == ValidationSeverity.ERROR]) == 0,
            alerts=alerts,
            recommendations=['Test recommendation'],
            optimizations=['Test optimization']
        )

    def test_alert_manager_initialization(self):
        """Test alert manager initialization"""
        assert isinstance(self.alert_manager, AlertManager)
        assert Path(self.temp_dir).exists()
        assert isinstance(self.alert_manager.configuration, AlertConfiguration)
        assert len(self.alert_manager.alert_states) == 0

    def test_process_validation_result_basic(self):
        """Test basic processing of validation results"""
        validation_result = self.create_test_validation_result()

        alerts_to_show = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        assert len(alerts_to_show) == 1
        assert alerts_to_show[0].title == 'Test Alert'

        # Check that alert state was created
        assert len(self.alert_manager.alert_states) == 1

    def test_alert_id_generation(self):
        """Test consistent alert ID generation"""
        alert = self.create_test_alert()

        id1 = self.alert_manager._generate_alert_id(alert, self.user_id)
        id2 = self.alert_manager._generate_alert_id(alert, self.user_id)

        assert id1 == id2  # Should be consistent
        assert self.user_id in id1  # Should include user ID

    def test_alert_state_tracking(self):
        """Test alert state tracking and updates"""
        validation_result = self.create_test_validation_result()

        # First time showing
        alerts1 = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts1) == 1

        # Check alert state
        alert_states = list(self.alert_manager.alert_states.values())
        assert len(alert_states) == 1
        assert alert_states[0].shown_count == 1

        # Second time showing
        alerts2 = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts2) == 1
        assert alert_states[0].shown_count == 2

    def test_alert_dismissal(self):
        """Test alert dismissal functionality"""
        validation_result = self.create_test_validation_result()

        # Show alert first
        alerts = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts) == 1

        # Get alert ID
        alert_states = list(self.alert_manager.alert_states.values())
        alert_id = alert_states[0].alert_id

        # Dismiss alert
        success = self.alert_manager.dismiss_alert(alert_id, "user_fixed_issue")
        assert success
        assert alert_states[0].dismissed_at is not None
        assert alert_states[0].user_action_taken == "user_fixed_issue"

        # Should not show dismissed alert
        alerts_after_dismiss = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts_after_dismiss) == 0

    def test_alert_snoozing(self):
        """Test alert snoozing functionality"""
        validation_result = self.create_test_validation_result()

        # Show alert first
        alerts = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts) == 1

        # Get alert ID and snooze
        alert_states = list(self.alert_manager.alert_states.values())
        alert_id = alert_states[0].alert_id

        success = self.alert_manager.snooze_alert(alert_id, hours=2)
        assert success
        assert alert_states[0].snoozed_until is not None
        assert alert_states[0].snoozed_until > datetime.now()

        # Should not show snoozed alert
        alerts_after_snooze = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts_after_snooze) == 0

    def test_show_count_limit(self):
        """Test that alerts respect show count limits"""
        # Set low show limit
        self.alert_manager.configuration.max_shows_per_alert = 2

        validation_result = self.create_test_validation_result()

        # Show alert twice (at limit)
        for _ in range(2):
            alerts = self.alert_manager.process_validation_result(
                validation_result, self.user_id, self.test_preferences
            )
            assert len(alerts) == 1

        # Third time should not show
        alerts_third = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )
        assert len(alerts_third) == 0

    def test_severity_filtering(self):
        """Test alert filtering by severity configuration"""
        # Disable info alerts
        self.alert_manager.configuration.show_info_alerts = False

        info_alert = self.create_test_alert(severity=ValidationSeverity.INFO)
        warning_alert = self.create_test_alert(severity=ValidationSeverity.WARNING, title="Warning Alert")

        validation_result = ValidationResult(
            is_valid=True,
            alerts=[info_alert, warning_alert]
        )

        alerts_to_show = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Should only show warning, not info
        assert len(alerts_to_show) == 1
        assert alerts_to_show[0].severity == ValidationSeverity.WARNING

    def test_alert_priority_sorting(self):
        """Test that alerts are sorted by priority"""
        alerts = [
            self.create_test_alert(severity=ValidationSeverity.INFO, title="Info Alert"),
            self.create_test_alert(severity=ValidationSeverity.ERROR, title="Error Alert"),
            self.create_test_alert(severity=ValidationSeverity.WARNING, title="Warning Alert")
        ]

        validation_result = ValidationResult(is_valid=False, alerts=alerts)

        alerts_to_show = self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Should be sorted by priority (error first)
        assert alerts_to_show[0].severity == ValidationSeverity.ERROR
        assert alerts_to_show[1].severity == ValidationSeverity.WARNING
        assert alerts_to_show[2].severity == ValidationSeverity.INFO

    def test_alert_enhancement(self):
        """Test alert enhancement with contextual information"""
        alert = self.create_test_alert()
        enhanced_alert = self.alert_manager._enhance_alert(alert, self.test_preferences)

        # Should add methodology context
        assert 'moderate' in enhanced_alert.explanation.lower()

    def test_alert_statistics(self):
        """Test alert statistics generation"""
        # Create and process some alerts
        validation_result = self.create_test_validation_result()

        self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Dismiss one alert
        alert_states = list(self.alert_manager.alert_states.values())
        self.alert_manager.dismiss_alert(alert_states[0].alert_id)

        # Get statistics
        stats = self.alert_manager.get_alert_statistics(self.user_id)

        assert stats['total_alerts'] == 1
        assert stats['dismissed_alerts'] == 1
        assert stats['active_alerts'] == 0
        assert stats['average_shows_per_alert'] > 0

    def test_alert_handler_registration(self):
        """Test registration and triggering of alert handlers"""
        handler_called = False
        handler_alert = None

        def test_handler(alert, user_id):
            nonlocal handler_called, handler_alert
            handler_called = True
            handler_alert = alert

        # Register handler
        self.alert_manager.register_alert_handler(
            ValidationCategory.FINANCIAL_CONSISTENCY.value,
            test_handler
        )

        # Process alert that should trigger handler
        alert = self.create_test_alert(category=ValidationCategory.FINANCIAL_CONSISTENCY)
        validation_result = ValidationResult(is_valid=True, alerts=[alert])

        self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        assert handler_called
        assert handler_alert is not None

    def test_configuration_updates(self):
        """Test alert configuration updates"""
        original_show_info = self.alert_manager.configuration.show_info_alerts

        # Update configuration
        updates = {'show_info_alerts': not original_show_info}
        success = self.alert_manager.update_configuration(updates)

        assert success
        assert self.alert_manager.configuration.show_info_alerts != original_show_info

    def test_alert_summary_generation(self):
        """Test alert summary generation"""
        # Create some alerts
        validation_result = self.create_test_validation_result()

        self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Generate summary
        summary = self.alert_manager.generate_alert_summary(self.user_id)

        assert summary['user_id'] == self.user_id
        assert summary['total_alerts'] == 1
        assert 'category_breakdown' in summary
        assert 'recent_activity' in summary
        assert 'recommendations' in summary

    def test_recent_alert_activity(self):
        """Test recent alert activity tracking"""
        # Create and process alert
        validation_result = self.create_test_validation_result()

        self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Get recent activity
        activity = self.alert_manager._get_recent_alert_activity(self.user_id)

        assert len(activity) == 1
        assert activity[0]['status'] == 'active'
        assert 'created_at' in activity[0]

    def test_state_persistence(self):
        """Test that alert states are persisted to disk"""
        # Create alert
        validation_result = self.create_test_validation_result()

        self.alert_manager.process_validation_result(
            validation_result, self.user_id, self.test_preferences
        )

        # Create new alert manager instance with same directory
        new_alert_manager = AlertManager(data_directory=self.temp_dir)

        # Should load existing states
        assert len(new_alert_manager.alert_states) == 1

    def test_configuration_persistence(self):
        """Test that configuration is persisted to disk"""
        # Update configuration
        self.alert_manager.update_configuration({'show_info_alerts': False})

        # Create new alert manager instance
        new_alert_manager = AlertManager(data_directory=self.temp_dir)

        # Should load updated configuration
        assert not new_alert_manager.configuration.show_info_alerts

    def test_auto_dismiss_after_time(self):
        """Test auto-dismiss functionality after time limit"""
        # Set short auto-dismiss time
        self.alert_manager.configuration.auto_dismiss_after_days = 0

        # Create alert state with old timestamp
        old_alert_state = AlertState(
            alert_id="old_alert",
            created_at=datetime.now() - timedelta(days=1)
        )
        self.alert_manager.alert_states["old_alert"] = old_alert_state

        # Create alert that would match this state
        alert = self.create_test_alert()

        # Should not show due to age
        should_show = self.alert_manager._should_show_alert(alert, self.user_id)
        assert not should_show

    def test_multiple_users_isolation(self):
        """Test that alerts for different users are isolated"""
        user1 = "user1"
        user2 = "user2"

        validation_result = self.create_test_validation_result()

        # Process alerts for both users
        alerts1 = self.alert_manager.process_validation_result(
            validation_result, user1, self.test_preferences
        )
        alerts2 = self.alert_manager.process_validation_result(
            validation_result, user2, self.test_preferences
        )

        assert len(alerts1) == 1
        assert len(alerts2) == 1

        # Get statistics for each user
        stats1 = self.alert_manager.get_alert_statistics(user1)
        stats2 = self.alert_manager.get_alert_statistics(user2)

        assert stats1['total_alerts'] == 1
        assert stats2['total_alerts'] == 1

        # Dismiss alert for user1
        alert_states = list(self.alert_manager.alert_states.values())
        user1_alert = next(s for s in alert_states if s.alert_id.startswith(f"{user1}_"))
        self.alert_manager.dismiss_alert(user1_alert.alert_id)

        # Should only affect user1
        stats1_after = self.alert_manager.get_alert_statistics(user1)
        stats2_after = self.alert_manager.get_alert_statistics(user2)

        assert stats1_after['dismissed_alerts'] == 1
        assert stats2_after['dismissed_alerts'] == 0


@pytest.mark.integration
class TestAlertManagerIntegration:
    """Integration tests for alert manager"""

    def test_complete_alert_workflow(self):
        """Test complete alert management workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            alert_manager = AlertManager(data_directory=temp_dir)
            user_id = "integration_test_user"

            # Create preferences with issues
            preferences = UserPreferences(
                financial=FinancialPreferences(
                    default_discount_rate=0.15,
                    default_terminal_growth_rate=0.12,  # Too high
                    methodology=AnalysisMethodology.CONSERVATIVE
                )
            )

            # Create validation result with multiple alerts
            from core.user_preferences.preference_validator import PreferenceValidator

            validator = PreferenceValidator()
            validation_result = validator.validate_preferences(preferences)

            # Process alerts
            alerts_to_show = alert_manager.process_validation_result(
                validation_result, user_id, preferences
            )

            assert len(alerts_to_show) > 0

            # Test user interactions
            if alerts_to_show:
                # Snooze first alert
                alert_states = list(alert_manager.alert_states.values())
                first_alert_id = alert_states[0].alert_id

                success = alert_manager.snooze_alert(first_alert_id, hours=1)
                assert success

                # Generate summary
                summary = alert_manager.generate_alert_summary(user_id)
                assert summary['user_id'] == user_id

                # Get statistics
                stats = alert_manager.get_alert_statistics(user_id)
                assert stats['snoozed_alerts'] > 0


if __name__ == "__main__":
    pytest.main([__file__])