"""
Preference Validation System Example

Demonstrates the preference validation and alert system functionality
including parameter consistency checks, intelligent alerts, and auto-fixing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.user_preferences.user_profile import (
    UserPreferences, FinancialPreferences, AnalysisMethodology,
    CurrencyPreference, RegionPreference
)
from core.user_preferences.preference_manager import UserPreferenceManager
from core.user_preferences.preference_validator import validate_user_preferences


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_alerts(alerts):
    """Print alerts in a formatted way"""
    if not alerts:
        print("[OK] No alerts - preferences look good!")
        return

    severity_icons = {
        'info': '[INFO]',
        'warning': '[WARNING]',
        'error': '[ERROR]',
        'critical': '[CRITICAL]'
    }

    for alert in alerts:
        icon = severity_icons.get(alert.get('severity', 'info'), '[?]')
        print(f"\n{icon} {alert['title']}")
        print(f"   Category: {alert['category']}")
        print(f"   Message: {alert['message']}")

        if alert.get('suggested_value'):
            print(f"   Current: {alert['current_value']}")
            print(f"   Suggested: {alert['suggested_value']}")

        if alert.get('explanation'):
            print(f"   Explanation: {alert['explanation']}")


def demonstrate_basic_validation():
    """Demonstrate basic preference validation"""
    print_section("Basic Preference Validation")

    # Create preferences with some issues
    preferences = UserPreferences(
        financial=FinancialPreferences(
            default_discount_rate=0.15,           # 15% - high
            default_terminal_growth_rate=0.08,    # 8% - potentially too high
            risk_free_rate=0.03,                  # 3%
            market_risk_premium=0.06,             # 6% - total should be 9%, not 15%
            methodology=AnalysisMethodology.CONSERVATIVE
        )
    )

    print("Testing preferences with potential issues:")
    print(f"- Discount Rate: {preferences.financial.default_discount_rate:.1%}")
    print(f"- Terminal Growth: {preferences.financial.default_terminal_growth_rate:.1%}")
    print(f"- Risk-Free Rate: {preferences.financial.risk_free_rate:.1%}")
    print(f"- Market Risk Premium: {preferences.financial.market_risk_premium:.1%}")
    print(f"- Methodology: {preferences.financial.methodology.value}")

    # Validate preferences
    validation_result = validate_user_preferences(preferences)

    print(f"\nValidation Results:")
    print(f"- Overall Valid: {validation_result.is_valid}")
    print(f"- Total Alerts: {len(validation_result.alerts)}")
    print(f"- Errors: {len(validation_result.get_alerts_by_severity('error'))}")
    print(f"- Warnings: {len(validation_result.get_alerts_by_severity('warning'))}")
    print(f"- Info: {len(validation_result.get_alerts_by_severity('info'))}")

    # Show detailed alerts
    print("\nDetailed Alerts:")
    alert_dicts = [alert.to_dict() for alert in validation_result.alerts]
    print_alerts(alert_dicts)

    # Show recommendations
    if validation_result.recommendations:
        print("\n[RECOMMENDATIONS] Recommendations:")
        for rec in validation_result.recommendations:
            print(f"   - {rec}")


def demonstrate_critical_errors():
    """Demonstrate critical validation errors"""
    print_section("Critical Validation Errors")

    # Create preferences with critical errors
    invalid_preferences = UserPreferences(
        financial=FinancialPreferences(
            default_discount_rate=0.05,          # 5%
            default_terminal_growth_rate=0.08,   # 8% - HIGHER than discount rate (invalid!)
            risk_free_rate=0.12,                 # 12% - unrealistically high
            market_risk_premium=0.01             # 1% - very low
        )
    )

    print("Testing preferences with critical errors:")
    print(f"- Discount Rate: {invalid_preferences.financial.default_discount_rate:.1%}")
    print(f"- Terminal Growth: {invalid_preferences.financial.default_terminal_growth_rate:.1%} (HIGHER than discount rate!)")

    validation_result = validate_user_preferences(invalid_preferences)

    print(f"\nValidation Results:")
    print(f"- Overall Valid: {validation_result.is_valid}")
    print(f"- Has Errors: {validation_result.has_errors()}")

    # Show only error alerts
    error_alerts = [alert.to_dict() for alert in validation_result.get_alerts_by_severity('error')]
    if error_alerts:
        print("\n[CRITICAL] Critical Errors:")
        print_alerts(error_alerts)


def demonstrate_regional_validation():
    """Demonstrate regional preference validation"""
    print_section("Regional Preference Validation")

    # Create preferences for Israel market with USD currency
    israel_preferences = UserPreferences(
        financial=FinancialPreferences(
            preferred_regions=[RegionPreference.ISRAEL],
            primary_currency=CurrencyPreference.USD,  # Mismatch with Israel
            risk_free_rate=0.01,                      # Too low for Israel
            default_terminal_growth_rate=0.05,        # Too high for Israel
            use_country_risk_premium=False            # Should be True for international
        )
    )

    print("Testing Israel market preferences with potential mismatches:")
    print(f"- Regions: {[r.value for r in israel_preferences.financial.preferred_regions]}")
    print(f"- Currency: {israel_preferences.financial.primary_currency.value}")
    print(f"- Risk-Free Rate: {israel_preferences.financial.risk_free_rate:.1%}")
    print(f"- Country Risk Premium: {israel_preferences.financial.use_country_risk_premium}")

    validation_result = validate_user_preferences(israel_preferences)

    # Show regional/currency alerts
    regional_alerts = [alert.to_dict() for alert in validation_result.get_alerts_by_category('regional_currency')]
    risk_alerts = [alert.to_dict() for alert in validation_result.get_alerts_by_category('risk_assessment')]

    if regional_alerts:
        print("\n[REGIONAL] Regional/Currency Alerts:")
        print_alerts(regional_alerts)

    if risk_alerts:
        print("\n[RISK] Risk Assessment Alerts:")
        print_alerts(risk_alerts)


def demonstrate_methodology_alignment():
    """Demonstrate methodology parameter alignment"""
    print_section("Methodology Parameter Alignment")

    methodologies = [
        AnalysisMethodology.CONSERVATIVE,
        AnalysisMethodology.MODERATE,
        AnalysisMethodology.AGGRESSIVE
    ]

    for methodology in methodologies:
        print(f"\n--- {methodology.value.upper()} Methodology ---")

        # Use same base parameters but different methodology
        preferences = UserPreferences(
            financial=FinancialPreferences(
                methodology=methodology,
                default_discount_rate=0.10,          # 10% - fixed
                default_terminal_growth_rate=0.04,   # 4% - may be too high for conservative
                risk_free_rate=0.03,
                market_risk_premium=0.07
            )
        )

        validation_result = validate_user_preferences(preferences)
        methodology_alerts = [
            alert.to_dict() for alert in validation_result.get_alerts_by_category('methodology_params')
        ]

        if methodology_alerts:
            print_alerts(methodology_alerts)
        else:
            print("[OK] Parameters align well with methodology")


def demonstrate_preference_manager_integration():
    """Demonstrate preference manager with validation"""
    print_section("Preference Manager with Validation")

    import tempfile

    # Create preference manager with validation enabled
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = UserPreferenceManager(
            data_directory=temp_dir,
            enable_validation=True
        )

        user_id = "demo_user"
        print(f"Creating user: {user_id}")

        # Create user
        user_profile = manager.create_user(user_id, "Demo User", "demo@example.com")

        # Update with problematic preferences
        problem_preferences = UserPreferences(
            financial=FinancialPreferences(
                default_discount_rate=0.12,
                risk_free_rate=0.03,
                market_risk_premium=0.06,  # Should total 9%, not 12%
                default_terminal_growth_rate=0.06,
                methodology=AnalysisMethodology.AGGRESSIVE
            )
        )

        print("\nUpdating preferences (validation will run automatically)...")
        success = manager.update_preferences(user_id, problem_preferences)
        print(f"Update successful: {success}")

        # Get alerts
        alerts = manager.get_user_alerts(user_id)
        print(f"\nGenerated {len(alerts)} alerts:")
        print_alerts(alerts)

        # Get recommendations
        recommendations = manager.get_preference_recommendations(user_id)
        print(f"\n[RECOMMENDATIONS] Intelligent Recommendations:")
        print(f"- Critical Issues: {recommendations['critical_issues']}")
        print(f"- Warnings: {recommendations['warning_count']}")
        print(f"- Info Alerts: {recommendations['info_count']}")

        for rec in recommendations['recommendations']:
            print(f"   - {rec}")

        # Try auto-fix
        print(f"\n[AUTO-FIX] Attempting Auto-Fix...")
        fix_result = manager.auto_fix_preferences(user_id)
        print(f"Auto-fix successful: {fix_result['success']}")
        print(f"Fixes applied: {fix_result['fixes_applied']}")

        if fix_result['fix_log']:
            print("Fix log:")
            for log_entry in fix_result['fix_log']:
                print(f"   - {log_entry}")

        # Check alerts after auto-fix
        alerts_after_fix = manager.get_user_alerts(user_id)
        print(f"\nAlerts after auto-fix: {len(alerts_after_fix)}")

        # Get user analytics
        analytics = manager.get_user_analytics(user_id)
        if 'alert_statistics' in analytics:
            alert_stats = analytics['alert_statistics']
            print(f"\n[STATISTICS] Alert Statistics:")
            print(f"- Total Alerts: {alert_stats['total_alerts']}")
            print(f"- Active Alerts: {alert_stats['active_alerts']}")
            print(f"- Dismissed Alerts: {alert_stats['dismissed_alerts']}")


def main():
    """Run all demonstrations"""
    print("Preference Validation System Demonstration")
    print("This example shows how the validation system helps users optimize their financial analysis preferences.")

    try:
        demonstrate_basic_validation()
        demonstrate_critical_errors()
        demonstrate_regional_validation()
        demonstrate_methodology_alignment()
        demonstrate_preference_manager_integration()

        print_section("Summary")
        print("The preference validation system provides:")
        print("[OK] Real-time validation of financial parameters")
        print("[OK] Intelligent alerts with educational explanations")
        print("[OK] Automatic fixing of common issues")
        print("[OK] Regional and methodology-specific guidance")
        print("[OK] Historical performance context")
        print("[OK] User-friendly alert management")

    except Exception as e:
        print(f"\n[ERROR] Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()