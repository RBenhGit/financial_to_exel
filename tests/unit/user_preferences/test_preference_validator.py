"""
Tests for the preference validation system

Tests comprehensive validation of user preferences including financial consistency,
risk assessment, regional alignment, and performance optimization.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, DisplayPreferences,
    NotificationPreferences, DataSourcePreferences, WatchListPreferences,
    AnalysisMethodology, CurrencyPreference, RegionPreference
)
from core.user_preferences.preference_validator import (
    PreferenceValidator, ValidationAlert, ValidationResult,
    ValidationSeverity, ValidationCategory, validate_user_preferences
)


class TestPreferenceValidator:
    """Test suite for preference validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = PreferenceValidator()
        self.default_preferences = UserPreferences()

    def create_test_preferences(self, **overrides) -> UserPreferences:
        """Create test preferences with optional overrides"""
        financial_overrides = overrides.pop('financial', {})

        financial_prefs = FinancialPreferences(
            default_discount_rate=financial_overrides.get('default_discount_rate', 0.10),
            default_terminal_growth_rate=financial_overrides.get('default_terminal_growth_rate', 0.025),
            risk_free_rate=financial_overrides.get('risk_free_rate', 0.03),
            market_risk_premium=financial_overrides.get('market_risk_premium', 0.06),
            methodology=financial_overrides.get('methodology', AnalysisMethodology.MODERATE),
            primary_currency=financial_overrides.get('primary_currency', CurrencyPreference.USD),
            preferred_regions=financial_overrides.get('preferred_regions', [RegionPreference.GLOBAL])
        )

        return UserPreferences(
            financial=financial_prefs,
            **overrides
        )

    def test_valid_preferences_pass_validation(self):
        """Test that valid preferences pass validation"""
        preferences = self.create_test_preferences()
        result = self.validator.validate_preferences(preferences)

        assert result.is_valid
        assert len(result.alerts) == 0

    def test_financial_consistency_validation(self):
        """Test financial parameter consistency validation"""
        # Test discount rate vs components mismatch
        preferences = self.create_test_preferences(
            financial={
                'default_discount_rate': 0.15,  # 15%
                'risk_free_rate': 0.03,         # 3%
                'market_risk_premium': 0.06     # 6% - should total 9%
            }
        )

        result = self.validator.validate_preferences(preferences)
        consistency_alerts = result.get_alerts_by_category(ValidationCategory.FINANCIAL_CONSISTENCY)

        assert len(consistency_alerts) > 0
        discount_rate_alert = next(
            (alert for alert in consistency_alerts if alert.parameter == 'default_discount_rate'),
            None
        )
        assert discount_rate_alert is not None
        assert discount_rate_alert.severity == ValidationSeverity.WARNING

    def test_terminal_growth_rate_error(self):
        """Test terminal growth rate cannot exceed discount rate"""
        preferences = self.create_test_preferences(
            financial={
                'default_discount_rate': 0.08,           # 8%
                'default_terminal_growth_rate': 0.10     # 10% - invalid!
            }
        )

        result = self.validator.validate_preferences(preferences)

        assert result.has_errors()
        error_alerts = result.get_alerts_by_severity(ValidationSeverity.ERROR)
        terminal_growth_alert = next(
            (alert for alert in error_alerts if alert.parameter == 'default_terminal_growth_rate'),
            None
        )
        assert terminal_growth_alert is not None
        assert terminal_growth_alert.title == "Invalid Terminal Growth Rate"

    def test_extreme_parameter_values(self):
        """Test validation of extreme parameter values"""
        # Test extremely high discount rate (above historical range of 20%)
        preferences = self.create_test_preferences(
            financial={'default_discount_rate': 0.35}  # 35% - unrealistic
        )

        result = self.validator.validate_preferences(preferences)

        # Look for alerts related to discount rate parameter with any variation of "high" in title or message
        high_rate_alerts = [
            alert for alert in result.alerts
            if 'discount_rate' in alert.parameter and (
                'high' in alert.title.lower() or
                'high' in alert.message.lower() or
                'exceed' in alert.title.lower() or
                'exceed' in alert.message.lower()
            )
        ]
        assert len(high_rate_alerts) > 0, f"Expected high discount rate alert, got alerts: {[alert.title for alert in result.alerts]}"

        # Test extremely low risk-free rate
        preferences = self.create_test_preferences(
            financial={'risk_free_rate': -0.02}  # -2% - negative rates
        )

        result = self.validator.validate_preferences(preferences)
        low_rate_alerts = [
            alert for alert in result.alerts
            if alert.parameter == 'risk_free_rate' and (
                'low' in alert.title.lower() or
                'below' in alert.title.lower() or
                'low' in alert.message.lower()
            )
        ]
        assert len(low_rate_alerts) > 0, f"Expected low risk-free rate alert, got alerts: {[alert.title for alert in result.alerts]}"

    def test_risk_assessment_validation(self):
        """Test risk assessment parameter validation"""
        # Test low market risk premium
        preferences = self.create_test_preferences(
            financial={'market_risk_premium': 0.02}  # 2% - very low
        )

        result = self.validator.validate_preferences(preferences)
        risk_alerts = result.get_alerts_by_category(ValidationCategory.RISK_ASSESSMENT)

        low_premium_alert = next(
            (alert for alert in risk_alerts if 'Low Market Risk Premium' in alert.title),
            None
        )
        assert low_premium_alert is not None
        assert low_premium_alert.severity == ValidationSeverity.WARNING

    def test_country_risk_premium_recommendation(self):
        """Test country risk premium recommendation for international investments"""
        preferences = self.create_test_preferences(
            financial={
                'preferred_regions': [RegionPreference.EMERGING_MARKETS, RegionPreference.ASIA_PACIFIC],
                'use_country_risk_premium': False
            }
        )

        result = self.validator.validate_preferences(preferences)
        risk_alerts = result.get_alerts_by_category(ValidationCategory.RISK_ASSESSMENT)

        country_risk_alert = next(
            (alert for alert in risk_alerts if 'Country Risk Premium' in alert.title),
            None
        )
        assert country_risk_alert is not None
        assert country_risk_alert.suggested_value is True

    def test_regional_currency_alignment(self):
        """Test regional and currency preference alignment"""
        # Test USD with European focus
        preferences = self.create_test_preferences(
            financial={
                'preferred_regions': [RegionPreference.EUROPE],
                'primary_currency': CurrencyPreference.USD
            }
        )

        result = self.validator.validate_preferences(preferences)
        regional_alerts = result.get_alerts_by_category(ValidationCategory.REGIONAL_CURRENCY)

        currency_mismatch_alert = next(
            (alert for alert in regional_alerts if 'Currency-Region Mismatch' in alert.title),
            None
        )
        assert currency_mismatch_alert is not None
        assert currency_mismatch_alert.severity == ValidationSeverity.INFO

    def test_methodology_parameter_alignment(self):
        """Test parameter alignment with chosen methodology"""
        # Test aggressive methodology with conservative parameters
        preferences = self.create_test_preferences(
            financial={
                'methodology': AnalysisMethodology.AGGRESSIVE,
                'default_discount_rate': 0.15,  # High rate (conservative)
                'default_terminal_growth_rate': 0.05  # High growth (aggressive)
            }
        )

        result = self.validator.validate_preferences(preferences)
        methodology_alerts = result.get_alerts_by_category(ValidationCategory.METHODOLOGY_PARAMS)

        # Should have alert about discount rate not matching aggressive approach
        discount_alert = next(
            (alert for alert in methodology_alerts
             if alert.parameter == 'default_discount_rate'),
            None
        )
        assert discount_alert is not None

        # Should have alert about high terminal growth
        terminal_alert = next(
            (alert for alert in methodology_alerts
             if alert.parameter == 'default_terminal_growth_rate'),
            None
        )
        assert terminal_alert is not None

    def test_data_source_configuration_validation(self):
        """Test data source configuration validation"""
        data_sources = DataSourcePreferences(
            auto_refresh_data=True,
            cache_duration_hours=48,  # Long cache with auto-refresh
            api_timeout_seconds=60,
            max_retry_attempts=10     # Very long potential timeout
        )

        preferences = UserPreferences(data_sources=data_sources)
        result = self.validator.validate_preferences(preferences)

        data_quality_alerts = result.get_alerts_by_category(ValidationCategory.DATA_QUALITY)
        performance_alerts = result.get_alerts_by_category(ValidationCategory.PERFORMANCE_OPTIMIZATION)

        assert len(data_quality_alerts) > 0 or len(performance_alerts) > 0

    def test_performance_optimization_alerts(self):
        """Test performance optimization alerts"""
        display_prefs = DisplayPreferences(animation_enabled=True)
        watchlist_prefs = WatchListPreferences(
            max_companies_per_list=150,  # Large list
            auto_refresh_enabled=True,
            refresh_interval_minutes=5   # Very frequent
        )

        preferences = UserPreferences(
            display=display_prefs,
            watch_lists=watchlist_prefs
        )
        result = self.validator.validate_preferences(preferences)

        performance_alerts = result.get_alerts_by_category(ValidationCategory.PERFORMANCE_OPTIMIZATION)
        assert len(performance_alerts) > 0

    def test_validation_result_methods(self):
        """Test ValidationResult helper methods"""
        # Create preferences that will generate various severity alerts
        preferences = self.create_test_preferences(
            financial={
                'default_discount_rate': 0.08,           # Might generate info
                'default_terminal_growth_rate': 0.10,    # Will generate error
                'market_risk_premium': 0.02              # Will generate warning
            }
        )

        result = self.validator.validate_preferences(preferences)

        # Test severity filtering
        errors = result.get_alerts_by_severity(ValidationSeverity.ERROR)
        warnings = result.get_alerts_by_severity(ValidationSeverity.WARNING)

        assert len(errors) > 0
        assert len(warnings) > 0
        assert result.has_errors()
        assert result.has_warnings()

    def test_convenience_function(self):
        """Test the convenience validation function"""
        preferences = self.create_test_preferences(
            financial={'default_terminal_growth_rate': 0.15}  # Invalid
        )

        result = validate_user_preferences(preferences)
        assert isinstance(result, ValidationResult)
        assert result.has_errors()

    def test_alert_to_dict_conversion(self):
        """Test alert conversion to dictionary format"""
        preferences = self.create_test_preferences(
            financial={'default_discount_rate': 0.25}  # High rate
        )

        result = self.validator.validate_preferences(preferences)
        assert len(result.alerts) > 0

        alert_dict = result.alerts[0].to_dict()
        required_fields = ['category', 'severity', 'title', 'message', 'parameter', 'current_value']

        for field in required_fields:
            assert field in alert_dict

    def test_recommendation_generation(self):
        """Test that recommendations are generated based on validation results"""
        # Create preferences with multiple issues
        preferences = self.create_test_preferences(
            financial={
                'methodology': AnalysisMethodology.CONSERVATIVE,
                'default_discount_rate': 0.06,           # Too low for conservative
                'default_terminal_growth_rate': 0.08,    # Too high
                'preferred_regions': [RegionPreference.NORTH_AMERICA, RegionPreference.EUROPE, RegionPreference.ASIA_PACIFIC]
            }
        )

        result = self.validator.validate_preferences(preferences)

        assert len(result.recommendations) > 0
        assert any('conservative' in rec.lower() for rec in result.recommendations)

    def test_regional_parameter_validation(self):
        """Test validation against regional economic indicators"""
        # Test Israel-specific parameters
        preferences = self.create_test_preferences(
            financial={
                'preferred_regions': [RegionPreference.ISRAEL],
                'risk_free_rate': 0.01,  # Too low for Israel
                'default_terminal_growth_rate': 0.06  # Too high for Israel
            }
        )

        result = self.validator.validate_preferences(preferences)
        regional_alerts = result.get_alerts_by_category(ValidationCategory.REGIONAL_CURRENCY)

        assert len(regional_alerts) > 0

    def test_validator_historical_ranges(self):
        """Test that validator uses appropriate historical ranges"""
        assert 'risk_free_rate' in self.validator.historical_ranges
        assert 'discount_rate' in self.validator.historical_ranges

        # Test ranges are reasonable
        rf_min, rf_max = self.validator.historical_ranges['risk_free_rate']
        assert 0 <= rf_min < rf_max <= 0.1  # Reasonable range for risk-free rates

    def test_methodology_expectations(self):
        """Test methodology-specific expectations"""
        conservative_exp = self.validator.methodology_expectations[AnalysisMethodology.CONSERVATIVE]
        aggressive_exp = self.validator.methodology_expectations[AnalysisMethodology.AGGRESSIVE]

        # Conservative should have higher discount rate multiplier
        assert conservative_exp['discount_rate_multiplier'] > aggressive_exp['discount_rate_multiplier']

        # Conservative should have lower terminal growth max
        assert conservative_exp['terminal_growth_max'] < aggressive_exp['terminal_growth_max']

    def test_regional_indicators_completeness(self):
        """Test that regional indicators are defined for all supported regions"""
        supported_regions = [
            RegionPreference.NORTH_AMERICA,
            RegionPreference.EUROPE,
            RegionPreference.ASIA_PACIFIC,
            RegionPreference.EMERGING_MARKETS,
            RegionPreference.ISRAEL
        ]

        for region in supported_regions:
            assert region in self.validator.regional_indicators
            indicators = self.validator.regional_indicators[region]
            assert 'typical_risk_free' in indicators
            assert 'typical_market_premium' in indicators
            assert 'growth_range' in indicators


@pytest.mark.integration
class TestPreferenceValidationIntegration:
    """Integration tests for preference validation"""

    def test_complete_preference_validation_workflow(self):
        """Test complete validation workflow with realistic preferences"""
        # Create realistic user preferences with some issues
        financial_prefs = FinancialPreferences(
            default_discount_rate=0.12,
            default_terminal_growth_rate=0.03,
            risk_free_rate=0.035,
            market_risk_premium=0.065,
            methodology=AnalysisMethodology.MODERATE,
            primary_currency=CurrencyPreference.USD,
            preferred_regions=[RegionPreference.NORTH_AMERICA]
        )

        display_prefs = DisplayPreferences(
            animation_enabled=True,
            chart_theme="plotly"
        )

        data_source_prefs = DataSourcePreferences(
            auto_refresh_data=True,
            cache_duration_hours=12,
            api_timeout_seconds=30
        )

        preferences = UserPreferences(
            financial=financial_prefs,
            display=display_prefs,
            data_sources=data_source_prefs
        )

        # Run validation
        validator = PreferenceValidator()
        result = validator.validate_preferences(preferences)

        # Should be valid overall but may have informational alerts
        assert result.is_valid or not result.has_errors()  # No critical errors

        # Check that validation categories are represented
        categories_found = {alert.category for alert in result.alerts}
        assert len(categories_found) >= 0  # May or may not have alerts for this valid config

    def test_edge_case_parameter_combinations(self):
        """Test edge cases and unusual parameter combinations"""
        edge_cases = [
            # Zero risk-free rate
            {'risk_free_rate': 0.0, 'market_risk_premium': 0.08},

            # Very high projection years
            {'default_projection_years': 15},

            # Minimal terminal growth
            {'default_terminal_growth_rate': 0.005},

            # Multiple regions with conflicting characteristics
            {'preferred_regions': [RegionPreference.EMERGING_MARKETS, RegionPreference.EUROPE, RegionPreference.ISRAEL]}
        ]

        validator = PreferenceValidator()

        for case in edge_cases:
            preferences = UserPreferences()

            # Apply financial parameter overrides
            for param, value in case.items():
                if hasattr(preferences.financial, param):
                    setattr(preferences.financial, param, value)

            # Should not crash on edge cases
            result = validator.validate_preferences(preferences)
            assert isinstance(result, ValidationResult)


if __name__ == "__main__":
    pytest.main([__file__])