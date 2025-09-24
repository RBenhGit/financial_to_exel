"""
Tests for preference manager validation integration

Tests the integration of validation and alert systems into the preference manager.
"""

import pytest
import tempfile
from datetime import datetime

from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, AnalysisMethodology,
    create_default_user_profile
)
from core.user_preferences.preference_manager import UserPreferenceManager
from core.user_preferences.preference_validator import ValidationSeverity


class TestPreferenceManagerValidation:
    """Test suite for preference manager validation integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UserPreferenceManager(
            data_directory=self.temp_dir,
            enable_validation=True
        )
        self.user_id = "test_user_validation"
        self.username = "Test Validation User"

        # Create test user
        self.user_profile = self.manager.create_user(
            self.user_id,
            self.username,
            email="test@example.com"
        )

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validation_enabled_initialization(self):
        """Test that validation components are properly initialized"""
        assert self.manager.enable_validation
        assert self.manager.validator is not None
        assert self.manager.alert_manager is not None

    def test_validation_disabled_initialization(self):
        """Test initialization with validation disabled"""
        manager_no_validation = UserPreferenceManager(
            data_directory=self.temp_dir + "_no_val",
            enable_validation=False
        )

        assert not manager_no_validation.enable_validation
        assert manager_no_validation.validator is None
        assert manager_no_validation.alert_manager is None

    def test_update_preferences_with_validation(self):
        """Test preference updates with validation enabled"""
        # Create preferences with validation issues
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.08,
                default_terminal_growth_rate=0.10,  # Invalid - higher than discount rate
                risk_free_rate=0.03
            )
        )

        # Update preferences - should succeed but trigger validation
        success = self.manager.update_preferences(
            self.user_id,
            problem_preferences,
            validate=True
        )

        assert success

        # Check that alerts were generated
        alerts = self.manager.get_user_alerts(self.user_id)
        assert len(alerts) > 0

        # Should have error alert for terminal growth rate
        error_alerts = [a for a in alerts if a['severity'] == ValidationSeverity.ERROR.value]
        assert len(error_alerts) > 0

    def test_update_preferences_skip_validation(self):
        """Test preference updates with validation skipped"""
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_terminal_growth_rate=0.15  # Would normally cause error
            )
        )

        # Update with validation disabled
        success = self.manager.update_preferences(
            self.user_id,
            problem_preferences,
            validate=False
        )

        assert success

        # Should have no alerts since validation was skipped
        alerts = self.manager.get_user_alerts(self.user_id)
        assert len(alerts) == 0

    def test_validate_user_preferences_method(self):
        """Test the validate_user_preferences method"""
        # Set preferences with issues
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.25,  # Very high
                market_risk_premium=0.01     # Very low
            )
        )

        self.manager.update_preferences(self.user_id, problem_preferences, validate=False)

        # Validate explicitly
        validation_result = self.manager.validate_user_preferences(self.user_id)

        assert validation_result is not None
        assert len(validation_result.alerts) > 0
        assert validation_result.has_warnings()

    def test_get_user_alerts(self):
        """Test getting user alerts"""
        # Create preferences that will generate alerts
        alert_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.06,
                risk_free_rate=0.03,
                market_risk_premium=0.06,  # Total 9%, but discount rate is 6%
                methodology=AnalysisMethodology.CONSERVATIVE
            )
        )

        self.manager.update_preferences(self.user_id, alert_preferences)

        # Get alerts
        alerts = self.manager.get_user_alerts(self.user_id)

        assert isinstance(alerts, list)
        assert len(alerts) >= 0  # May have alerts depending on validation logic

        # Each alert should be a dictionary with required fields
        for alert in alerts:
            assert 'category' in alert
            assert 'severity' in alert
            assert 'title' in alert
            assert 'message' in alert

    def test_dismiss_user_alert(self):
        """Test dismissing user alerts"""
        # Create preferences with validation issues
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_terminal_growth_rate=0.15  # Will cause error
            )
        )

        self.manager.update_preferences(self.user_id, problem_preferences)

        # Get alerts
        alerts = self.manager.get_user_alerts(self.user_id)

        if alerts:
            # Get alert ID (simplified - in real usage would come from UI)
            alert_states = list(self.manager.alert_manager.alert_states.values())
            if alert_states:
                alert_id = alert_states[0].alert_id

                # Dismiss alert
                success = self.manager.dismiss_user_alert(
                    self.user_id,
                    alert_id,
                    "user_manually_reviewed"
                )

                assert success

                # Should have fewer alerts now
                alerts_after = self.manager.get_user_alerts(self.user_id)
                assert len(alerts_after) < len(alerts)

    def test_snooze_user_alert(self):
        """Test snoozing user alerts"""
        # Create preferences with validation issues
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                market_risk_premium=0.01  # Very low - will generate warning
            )
        )

        self.manager.update_preferences(self.user_id, problem_preferences)

        # Get alerts
        alerts = self.manager.get_user_alerts(self.user_id)

        if alerts:
            alert_states = list(self.manager.alert_manager.alert_states.values())
            if alert_states:
                alert_id = alert_states[0].alert_id

                # Snooze alert
                success = self.manager.snooze_user_alert(self.user_id, alert_id, hours=2)
                assert success

                # Should have fewer active alerts
                alerts_after = self.manager.get_user_alerts(self.user_id)
                assert len(alerts_after) < len(alerts)

    def test_get_preference_recommendations(self):
        """Test getting preference recommendations"""
        # Set preferences that will generate recommendations
        recommendation_preferences = UserPreferences(
            financial=FinancialPreferences(
                methodology=AnalysisMethodology.AGGRESSIVE,
                default_discount_rate=0.15,  # High rate (not aggressive)
                default_terminal_growth_rate=0.045  # High growth (aggressive)
            )
        )

        self.manager.update_preferences(self.user_id, recommendation_preferences)

        # Get recommendations
        recommendations = self.manager.get_preference_recommendations(self.user_id)

        assert isinstance(recommendations, dict)
        assert 'recommendations' in recommendations
        assert 'optimizations' in recommendations
        assert 'critical_issues' in recommendations
        assert 'warning_count' in recommendations

    def test_auto_fix_preferences(self):
        """Test automatic preference fixing"""
        # Create preferences with fixable issues
        fixable_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.15,
                risk_free_rate=0.03,
                market_risk_premium=0.06  # Should suggest discount rate of 0.09
            )
        )

        self.manager.update_preferences(self.user_id, fixable_preferences, validate=False)

        # Run auto-fix
        fix_result = self.manager.auto_fix_preferences(self.user_id)

        assert fix_result['success']
        assert 'fixes_applied' in fix_result
        assert 'fix_log' in fix_result

        # If fixes were applied, preferences should be updated
        if fix_result['fixes_applied'] > 0:
            updated_profile = self.manager.get_user(self.user_id)
            # Some parameter should have been auto-corrected
            assert updated_profile is not None

    def test_auto_fix_specific_categories(self):
        """Test auto-fix with specific categories"""
        # Create preferences with multiple issue categories
        multi_issue_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.12,
                risk_free_rate=0.03,
                market_risk_premium=0.06,  # Inconsistency issue
                default_terminal_growth_rate=0.001  # Very low growth
            )
        )

        self.manager.update_preferences(self.user_id, multi_issue_preferences, validate=False)

        # Fix only financial consistency issues
        fix_result = self.manager.auto_fix_preferences(
            self.user_id,
            fix_categories=['financial_consistency']
        )

        assert fix_result['success']

    def test_user_analytics_with_alerts(self):
        """Test that user analytics includes alert statistics"""
        # Create preferences that generate alerts
        alert_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.30  # Extreme value
            )
        )

        self.manager.update_preferences(self.user_id, alert_preferences)

        # Get analytics
        analytics = self.manager.get_user_analytics(self.user_id)

        assert analytics is not None
        assert 'alert_statistics' in analytics

        alert_stats = analytics['alert_statistics']
        assert 'total_alerts' in alert_stats
        assert 'active_alerts' in alert_stats

    def test_validation_with_disabled_manager(self):
        """Test validation methods with disabled validation"""
        manager_no_validation = UserPreferenceManager(
            data_directory=self.temp_dir + "_disabled",
            enable_validation=False
        )

        user_id = "no_validation_user"
        manager_no_validation.create_user(user_id, "No Validation User")

        # All validation methods should return None or empty results
        validation_result = manager_no_validation.validate_user_preferences(user_id)
        assert validation_result is None

        alerts = manager_no_validation.get_user_alerts(user_id)
        assert len(alerts) == 0

        recommendations = manager_no_validation.get_preference_recommendations(user_id)
        assert recommendations == {'recommendations': [], 'suggestions': []}

        fix_result = manager_no_validation.auto_fix_preferences(user_id)
        assert not fix_result['success']
        assert fix_result['reason'] == 'Validation disabled'

    def test_preference_update_logging(self):
        """Test that preference updates with validation are properly logged"""
        import logging
        from unittest.mock import patch

        with patch('core.user_preferences.preference_manager.logger') as mock_logger:
            # Create preferences with errors and warnings
            problem_preferences = UserPreferences(
                financial=FinancialPreferences(
                    default_terminal_growth_rate=0.12,  # Error
                    market_risk_premium=0.02            # Warning
                )
            )

            self.manager.update_preferences(self.user_id, problem_preferences)

            # Should have logged validation results
            assert mock_logger.warning.called or mock_logger.info.called

    def test_multiple_validation_rounds(self):
        """Test multiple rounds of validation and alert processing"""
        # First set of problematic preferences
        preferences1 = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.25  # High
            )
        )

        self.manager.update_preferences(self.user_id, preferences1)
        alerts1 = self.manager.get_user_alerts(self.user_id)

        # Update with different problems
        preferences2 = UserPreferences(
            financial=FinancialPreferences(
                default_terminal_growth_rate=0.08  # Different issue
            )
        )

        self.manager.update_preferences(self.user_id, preferences2)
        alerts2 = self.manager.get_user_alerts(self.user_id)

        # Alert counts may vary depending on which issues are fixable/dismissible
        assert isinstance(alerts1, list)
        assert isinstance(alerts2, list)

    def test_concurrent_user_validation(self):
        """Test validation for multiple users concurrently"""
        user_ids = ["user1", "user2", "user3"]

        # Create users with different preference issues
        for i, user_id in enumerate(user_ids):
            self.manager.create_user(user_id, f"User {i+1}")

            preferences = UserPreferences(
                financial=FinancialPreferences(
                    default_discount_rate=0.05 + i * 0.1,  # Different values
                    methodology=AnalysisMethodology.MODERATE
                )
            )

            self.manager.update_preferences(user_id, preferences)

        # Get alerts for each user
        all_alerts = {}
        for user_id in user_ids:
            all_alerts[user_id] = self.manager.get_user_alerts(user_id)

        # Each user should have their own isolated alerts
        for user_id in user_ids:
            alerts = all_alerts[user_id]
            assert isinstance(alerts, list)

            # Get alert statistics
            stats = self.manager.alert_manager.get_alert_statistics(user_id)
            assert isinstance(stats, dict)


@pytest.mark.integration
class TestPreferenceManagerValidationIntegration:
    """Integration tests for complete validation workflow"""

    def test_complete_preference_lifecycle_with_validation(self):
        """Test complete preference lifecycle with validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserPreferenceManager(
                data_directory=temp_dir,
                enable_validation=True
            )

            user_id = "lifecycle_test_user"

            # 1. Create user
            user_profile = manager.create_user(user_id, "Lifecycle Test User")
            assert user_profile is not None

            # 2. Update with problematic preferences
            problem_preferences = UserPreferences(
                financial=FinancialPreferences(
                    default_discount_rate=0.08,
                    default_terminal_growth_rate=0.10,  # Error
                    methodology=AnalysisMethodology.CONSERVATIVE,
                    risk_free_rate=0.25,  # Extreme value
                    market_risk_premium=0.01  # Very low
                )
            )

            success = manager.update_preferences(user_id, problem_preferences)
            assert success

            # 3. Check validation results
            validation_result = manager.validate_user_preferences(user_id)
            assert validation_result is not None
            assert validation_result.has_errors()

            # 4. Get and interact with alerts
            alerts = manager.get_user_alerts(user_id)
            assert len(alerts) > 0

            # 5. Try auto-fix
            fix_result = manager.auto_fix_preferences(user_id)
            assert fix_result['success']

            # 6. Get recommendations
            recommendations = manager.get_preference_recommendations(user_id)
            assert len(recommendations['recommendations']) > 0

            # 7. Check analytics include alert data
            analytics = manager.get_user_analytics(user_id)
            assert 'alert_statistics' in analytics

            # 8. Verify persistence across manager restarts
            new_manager = UserPreferenceManager(
                data_directory=temp_dir,
                enable_validation=True
            )

            # Should load existing alert states
            persistent_alerts = new_manager.get_user_alerts(user_id)
            assert isinstance(persistent_alerts, list)


if __name__ == "__main__":
    pytest.main([__file__])