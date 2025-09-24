"""
Preference Validation and Alert System

Intelligent validation of user preference combinations with alerts for potentially
suboptimal configurations and educational explanations for recommendations.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .user_profile import UserPreferences, FinancialPreferences, AnalysisMethodology, RegionPreference

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation alerts"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks"""
    FINANCIAL_CONSISTENCY = "financial_consistency"
    RISK_ASSESSMENT = "risk_assessment"
    REGIONAL_CURRENCY = "regional_currency"
    METHODOLOGY_PARAMS = "methodology_params"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DATA_QUALITY = "data_quality"


@dataclass
class ValidationAlert:
    """A validation alert with details and recommendations"""

    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    message: str
    parameter: str
    current_value: Any
    suggested_value: Optional[Any] = None
    explanation: str = ""
    historical_context: Optional[str] = None
    correction_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary format"""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'parameter': self.parameter,
            'current_value': self.current_value,
            'suggested_value': self.suggested_value,
            'explanation': self.explanation,
            'historical_context': self.historical_context,
            'correction_action': self.correction_action,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ValidationResult:
    """Result of preference validation"""

    is_valid: bool
    alerts: List[ValidationAlert] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    optimizations: List[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if validation has any errors"""
        return any(alert.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                  for alert in self.alerts)

    def has_warnings(self) -> bool:
        """Check if validation has any warnings"""
        return any(alert.severity == ValidationSeverity.WARNING for alert in self.alerts)

    def get_alerts_by_severity(self, severity: ValidationSeverity) -> List[ValidationAlert]:
        """Get alerts filtered by severity"""
        return [alert for alert in self.alerts if alert.severity == severity]

    def get_alerts_by_category(self, category: ValidationCategory) -> List[ValidationAlert]:
        """Get alerts filtered by category"""
        return [alert for alert in self.alerts if alert.category == category]


class PreferenceValidator:
    """Validates user preferences and provides intelligent alerts"""

    def __init__(self):
        """Initialize the preference validator"""
        # Historical market data ranges for validation
        self.historical_ranges = {
            'risk_free_rate': (0.0, 0.08),  # 0% to 8%
            'market_risk_premium': (0.03, 0.12),  # 3% to 12%
            'discount_rate': (0.05, 0.20),  # 5% to 20%
            'terminal_growth_rate': (0.01, 0.05),  # 1% to 5%
            'projection_years': (3, 10)  # 3 to 10 years
        }

        # Regional economic indicators
        self.regional_indicators = {
            RegionPreference.NORTH_AMERICA: {
                'typical_risk_free': 0.03,
                'typical_market_premium': 0.06,
                'growth_range': (0.02, 0.035)
            },
            RegionPreference.EUROPE: {
                'typical_risk_free': 0.02,
                'typical_market_premium': 0.055,
                'growth_range': (0.015, 0.03)
            },
            RegionPreference.ASIA_PACIFIC: {
                'typical_risk_free': 0.025,
                'typical_market_premium': 0.07,
                'growth_range': (0.025, 0.045)
            },
            RegionPreference.EMERGING_MARKETS: {
                'typical_risk_free': 0.04,
                'typical_market_premium': 0.08,
                'growth_range': (0.03, 0.055)
            },
            RegionPreference.ISRAEL: {
                'typical_risk_free': 0.035,
                'typical_market_premium': 0.065,
                'growth_range': (0.025, 0.04)
            }
        }

        # Methodology-specific parameter expectations
        self.methodology_expectations = {
            AnalysisMethodology.CONSERVATIVE: {
                'discount_rate_multiplier': 1.1,  # 10% higher
                'terminal_growth_max': 0.025,
                'risk_adjustment': 1.2
            },
            AnalysisMethodology.MODERATE: {
                'discount_rate_multiplier': 1.0,
                'terminal_growth_max': 0.035,
                'risk_adjustment': 1.0
            },
            AnalysisMethodology.AGGRESSIVE: {
                'discount_rate_multiplier': 0.9,  # 10% lower
                'terminal_growth_max': 0.045,
                'risk_adjustment': 0.8
            }
        }

    def validate_preferences(self, preferences: UserPreferences) -> ValidationResult:
        """
        Comprehensive validation of user preferences

        Args:
            preferences: User preferences to validate

        Returns:
            ValidationResult with alerts and recommendations
        """
        result = ValidationResult(is_valid=True, alerts=[])

        # Run all validation checks
        self._validate_financial_consistency(preferences.financial, result)
        self._validate_risk_parameters(preferences.financial, result)
        self._validate_regional_currency_alignment(preferences.financial, result)
        self._validate_methodology_parameters(preferences.financial, result)
        self._validate_data_source_configuration(preferences.data_sources, result)
        self._validate_performance_settings(preferences, result)

        # Determine overall validity
        result.is_valid = not result.has_errors()

        # Generate recommendations
        self._generate_recommendations(preferences, result)

        logger.info(f"Preference validation completed: {len(result.alerts)} alerts generated")
        return result

    def _validate_financial_consistency(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate financial parameter consistency"""

        # Check discount rate vs components
        implied_discount_rate = financial.risk_free_rate + financial.market_risk_premium
        if abs(financial.default_discount_rate - implied_discount_rate) > 0.02:  # 2% tolerance
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.FINANCIAL_CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                title="Discount Rate Inconsistency",
                message="Discount rate doesn't align with risk-free rate + market risk premium",
                parameter="default_discount_rate",
                current_value=financial.default_discount_rate,
                suggested_value=round(implied_discount_rate, 3),
                explanation=(
                    "The discount rate should typically equal the risk-free rate plus "
                    "market risk premium for consistency in CAPM-based valuations."
                ),
                correction_action="Adjust discount rate to match risk-free + market premium"
            ))

        # Check terminal growth vs discount rate
        if financial.default_terminal_growth_rate >= financial.default_discount_rate:
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.FINANCIAL_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                title="Invalid Terminal Growth Rate",
                message="Terminal growth rate cannot exceed discount rate",
                parameter="default_terminal_growth_rate",
                current_value=financial.default_terminal_growth_rate,
                suggested_value=min(0.03, financial.default_discount_rate * 0.5),
                explanation=(
                    "Terminal growth rate must be less than discount rate for DCF models "
                    "to converge. Rates equal to or above discount rate create infinite valuations."
                ),
                correction_action="Reduce terminal growth rate below discount rate"
            ))

        # Check extreme parameter values
        self._validate_parameter_ranges(financial, result)

    def _validate_parameter_ranges(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate parameters are within reasonable historical ranges"""

        checks = [
            ('risk_free_rate', financial.risk_free_rate, 'Risk-Free Rate'),
            ('market_risk_premium', financial.market_risk_premium, 'Market Risk Premium'),
            ('discount_rate', financial.default_discount_rate, 'Discount Rate'),
            ('terminal_growth_rate', financial.default_terminal_growth_rate, 'Terminal Growth Rate'),
            ('projection_years', financial.default_projection_years, 'Projection Years')
        ]

        for param_name, value, display_name in checks:
            if param_name in self.historical_ranges:
                min_val, max_val = self.historical_ranges[param_name]

                if value < min_val:
                    # Calculate percentage difference safely
                    if min_val > 0:
                        pct_diff = f"{((min_val - value) / min_val):.1%} below"
                    else:
                        pct_diff = f"{abs(value - min_val):.3f} units below"

                    result.alerts.append(ValidationAlert(
                        category=ValidationCategory.FINANCIAL_CONSISTENCY,
                        severity=ValidationSeverity.WARNING,
                        title=f"Low {display_name}",
                        message=f"{display_name} is below typical historical range",
                        parameter=param_name,
                        current_value=value,
                        suggested_value=min_val,
                        explanation=f"Historical {display_name.lower()} typically ranges from {min_val:.1%} to {max_val:.1%}",
                        historical_context=f"Current value is {pct_diff} historical minimum"
                    ))
                elif value > max_val:
                    severity = ValidationSeverity.ERROR if value > max_val * 1.5 else ValidationSeverity.WARNING

                    # Calculate percentage difference safely
                    if max_val > 0:
                        pct_diff = f"{((value - max_val) / max_val):.1%} above"
                    else:
                        pct_diff = f"{abs(value - max_val):.3f} units above"

                    result.alerts.append(ValidationAlert(
                        category=ValidationCategory.FINANCIAL_CONSISTENCY,
                        severity=severity,
                        title=f"High {display_name}",
                        message=f"{display_name} exceeds typical historical range",
                        parameter=param_name,
                        current_value=value,
                        suggested_value=max_val,
                        explanation=f"Historical {display_name.lower()} typically ranges from {min_val:.1%} to {max_val:.1%}",
                        historical_context=f"Current value is {pct_diff} historical maximum"
                    ))

    def _validate_risk_parameters(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate risk assessment parameters"""

        # Check risk-free rate vs market risk premium relationship
        if financial.market_risk_premium < 0.03:  # Less than 3%
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.RISK_ASSESSMENT,
                severity=ValidationSeverity.WARNING,
                title="Low Market Risk Premium",
                message="Market risk premium appears low for equity investments",
                parameter="market_risk_premium",
                current_value=financial.market_risk_premium,
                suggested_value=0.06,
                explanation=(
                    "Equity risk premiums below 3% are historically rare and may "
                    "underestimate the risk of equity investments."
                ),
                historical_context="Long-term equity risk premiums typically range from 4-8%"
            ))

        # Validate country risk consideration for international investments
        if not financial.use_country_risk_premium and any(
            region in financial.preferred_regions
            for region in [RegionPreference.EMERGING_MARKETS, RegionPreference.ASIA_PACIFIC]
        ):
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.RISK_ASSESSMENT,
                severity=ValidationSeverity.INFO,
                title="Consider Country Risk Premium",
                message="Country risk premium recommended for international investments",
                parameter="use_country_risk_premium",
                current_value=False,
                suggested_value=True,
                explanation=(
                    "Country risk premiums help adjust for additional risks in "
                    "international and emerging market investments."
                ),
                correction_action="Enable country risk premium for international analysis"
            ))

    def _validate_regional_currency_alignment(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate regional and currency preference alignment"""

        # Define regional currency expectations
        regional_currencies = {
            RegionPreference.NORTH_AMERICA: ['USD', 'CAD'],
            RegionPreference.EUROPE: ['EUR', 'GBP', 'CHF'],
            RegionPreference.ASIA_PACIFIC: ['JPY', 'AUD'],
            RegionPreference.ISRAEL: ['ILS'],
            RegionPreference.EMERGING_MARKETS: ['USD']  # Often USD-denominated
        }

        primary_currency = financial.primary_currency.value

        for region in financial.preferred_regions:
            if region in regional_currencies:
                expected_currencies = regional_currencies[region]
                if primary_currency not in expected_currencies:
                    result.alerts.append(ValidationAlert(
                        category=ValidationCategory.REGIONAL_CURRENCY,
                        severity=ValidationSeverity.INFO,
                        title="Currency-Region Mismatch",
                        message=f"{primary_currency} may not align with {region.value} investments",
                        parameter="primary_currency",
                        current_value=primary_currency,
                        suggested_value=expected_currencies[0],
                        explanation=(
                            f"Consider using {' or '.join(expected_currencies)} for "
                            f"{region.value} focused analysis to avoid currency conversion complexity."
                        )
                    ))

        # Validate regional parameters
        self._validate_regional_parameters(financial, result)

    def _validate_regional_parameters(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate parameters against regional economic indicators"""

        for region in financial.preferred_regions:
            if region in self.regional_indicators:
                indicators = self.regional_indicators[region]

                # Check risk-free rate alignment
                typical_rf = indicators['typical_risk_free']
                if abs(financial.risk_free_rate - typical_rf) > 0.015:  # 1.5% tolerance
                    result.alerts.append(ValidationAlert(
                        category=ValidationCategory.REGIONAL_CURRENCY,
                        severity=ValidationSeverity.INFO,
                        title=f"Risk-Free Rate for {region.value}",
                        message=f"Risk-free rate differs from typical {region.value} rates",
                        parameter="risk_free_rate",
                        current_value=financial.risk_free_rate,
                        suggested_value=typical_rf,
                        explanation=(
                            f"Typical risk-free rate for {region.value} is around {typical_rf:.1%}. "
                            "Consider regional economic conditions."
                        )
                    ))

                # Check terminal growth alignment
                growth_min, growth_max = indicators['growth_range']
                if not (growth_min <= financial.default_terminal_growth_rate <= growth_max):
                    suggested_growth = (growth_min + growth_max) / 2
                    result.alerts.append(ValidationAlert(
                        category=ValidationCategory.REGIONAL_CURRENCY,
                        severity=ValidationSeverity.INFO,
                        title=f"Terminal Growth for {region.value}",
                        message=f"Terminal growth may not reflect {region.value} economic outlook",
                        parameter="default_terminal_growth_rate",
                        current_value=financial.default_terminal_growth_rate,
                        suggested_value=suggested_growth,
                        explanation=(
                            f"Typical long-term growth for {region.value} ranges from "
                            f"{growth_min:.1%} to {growth_max:.1%}."
                        )
                    ))

    def _validate_methodology_parameters(self, financial: FinancialPreferences, result: ValidationResult):
        """Validate parameters align with chosen methodology"""

        methodology = financial.methodology
        if methodology in self.methodology_expectations:
            expectations = self.methodology_expectations[methodology]

            # Calculate expected discount rate
            base_rate = financial.risk_free_rate + financial.market_risk_premium
            expected_discount_rate = base_rate * expectations['discount_rate_multiplier']

            if abs(financial.default_discount_rate - expected_discount_rate) > 0.02:
                result.alerts.append(ValidationAlert(
                    category=ValidationCategory.METHODOLOGY_PARAMS,
                    severity=ValidationSeverity.INFO,
                    title=f"Discount Rate for {methodology.value} Methodology",
                    message=f"Discount rate may not reflect {methodology.value} approach",
                    parameter="default_discount_rate",
                    current_value=financial.default_discount_rate,
                    suggested_value=round(expected_discount_rate, 3),
                    explanation=(
                        f"{methodology.value.title()} methodology typically uses "
                        f"{'higher' if expectations['discount_rate_multiplier'] > 1 else 'lower'} "
                        "discount rates to reflect risk tolerance."
                    )
                ))

            # Check terminal growth rate limits
            max_terminal_growth = expectations['terminal_growth_max']
            if financial.default_terminal_growth_rate > max_terminal_growth:
                result.alerts.append(ValidationAlert(
                    category=ValidationCategory.METHODOLOGY_PARAMS,
                    severity=ValidationSeverity.WARNING,
                    title=f"High Terminal Growth for {methodology.value}",
                    message=f"Terminal growth exceeds {methodology.value} methodology guidelines",
                    parameter="default_terminal_growth_rate",
                    current_value=financial.default_terminal_growth_rate,
                    suggested_value=max_terminal_growth,
                    explanation=(
                        f"{methodology.value.title()} methodology typically caps terminal "
                        f"growth at {max_terminal_growth:.1%} for prudent valuation."
                    )
                ))

    def _validate_data_source_configuration(self, data_sources, result: ValidationResult):
        """Validate data source preferences"""

        # Check cache duration vs auto-refresh settings
        if data_sources.auto_refresh_data and data_sources.cache_duration_hours > 24:
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.DATA_QUALITY,
                severity=ValidationSeverity.INFO,
                title="Cache Duration with Auto-Refresh",
                message="Long cache duration may conflict with auto-refresh",
                parameter="cache_duration_hours",
                current_value=data_sources.cache_duration_hours,
                suggested_value=6,
                explanation=(
                    "Auto-refresh is more effective with shorter cache durations "
                    "to ensure data freshness."
                ),
                correction_action="Reduce cache duration to 6-12 hours for auto-refresh"
            ))

        # Validate API timeout vs retry attempts
        total_timeout = data_sources.api_timeout_seconds * data_sources.max_retry_attempts
        if total_timeout > 300:  # 5 minutes total
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.PERFORMANCE_OPTIMIZATION,
                severity=ValidationSeverity.WARNING,
                title="Long API Timeout Configuration",
                message="Combined timeout and retries may cause long delays",
                parameter="api_timeout_seconds",
                current_value=data_sources.api_timeout_seconds,
                suggested_value=15,
                explanation=(
                    f"Total potential wait time is {total_timeout} seconds. "
                    "Consider reducing timeout or retry attempts for better user experience."
                )
            ))

    def _validate_performance_settings(self, preferences: UserPreferences, result: ValidationResult):
        """Validate performance-related settings"""

        # Check display settings that might impact performance
        if (preferences.display.animation_enabled and
            preferences.watch_lists.max_companies_per_list > 100):
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.PERFORMANCE_OPTIMIZATION,
                severity=ValidationSeverity.INFO,
                title="Performance Impact Warning",
                message="Animations with large watchlists may impact performance",
                parameter="animation_enabled",
                current_value=True,
                suggested_value=False,
                explanation=(
                    "Disabling animations can improve performance when working "
                    "with large datasets or watchlists."
                )
            ))

        # Check auto-refresh settings
        if (preferences.watch_lists.auto_refresh_enabled and
            preferences.watch_lists.refresh_interval_minutes < 15):
            result.alerts.append(ValidationAlert(
                category=ValidationCategory.PERFORMANCE_OPTIMIZATION,
                severity=ValidationSeverity.WARNING,
                title="Frequent Auto-Refresh",
                message="Very frequent refresh may impact API rate limits",
                parameter="refresh_interval_minutes",
                current_value=preferences.watch_lists.refresh_interval_minutes,
                suggested_value=30,
                explanation=(
                    "Frequent API calls may hit rate limits and increase costs. "
                    "30-60 minute intervals are typically sufficient for most use cases."
                )
            ))

    def _generate_recommendations(self, preferences: UserPreferences, result: ValidationResult):
        """Generate overall recommendations based on validation results"""

        error_count = len(result.get_alerts_by_severity(ValidationSeverity.ERROR))
        warning_count = len(result.get_alerts_by_severity(ValidationSeverity.WARNING))

        if error_count > 0:
            result.recommendations.append(
                f"Address {error_count} critical parameter issue(s) before running analysis"
            )

        if warning_count > 2:
            result.recommendations.append(
                "Consider reviewing methodology selection for better parameter alignment"
            )

        # Methodology-specific recommendations
        methodology = preferences.financial.methodology
        if methodology == AnalysisMethodology.CONSERVATIVE:
            result.recommendations.append(
                "Conservative approach: Consider higher discount rates and lower terminal growth"
            )
        elif methodology == AnalysisMethodology.AGGRESSIVE:
            result.recommendations.append(
                "Aggressive approach: Validate assumptions against historical precedents"
            )

        # Regional recommendations
        regions = preferences.financial.preferred_regions
        if len(regions) > 2:
            result.recommendations.append(
                "Multiple regions selected: Consider separate analysis for each region"
            )

        # Performance optimizations
        if any(alert.category == ValidationCategory.PERFORMANCE_OPTIMIZATION
               for alert in result.alerts):
            result.optimizations.append(
                "Performance optimizations available - see detailed alerts"
            )


def validate_user_preferences(preferences: UserPreferences) -> ValidationResult:
    """
    Convenience function to validate user preferences

    Args:
        preferences: User preferences to validate

    Returns:
        ValidationResult with alerts and recommendations
    """
    validator = PreferenceValidator()
    return validator.validate_preferences(preferences)


def get_historical_performance_feedback(
    preferences: UserPreferences,
    historical_results: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Provide historical performance feedback on preference choices

    Args:
        preferences: Current user preferences
        historical_results: Optional historical analysis results

    Returns:
        List of feedback messages
    """
    feedback = []

    # Simulated historical performance analysis
    # In a real implementation, this would analyze actual historical results

    methodology = preferences.financial.methodology
    discount_rate = preferences.financial.default_discount_rate

    if methodology == AnalysisMethodology.CONSERVATIVE:
        if discount_rate > 0.12:
            feedback.append(
                "Historical data suggests conservative discount rates above 12% "
                "may lead to undervaluation in stable market conditions"
            )
    elif methodology == AnalysisMethodology.AGGRESSIVE:
        if discount_rate < 0.08:
            feedback.append(
                "Aggressive strategies with very low discount rates historically "
                "show higher volatility in valuation accuracy"
            )

    # Regional performance feedback
    for region in preferences.financial.preferred_regions:
        if region == RegionPreference.EMERGING_MARKETS:
            feedback.append(
                "Emerging market analysis benefits from country risk premiums "
                "for more accurate historical correlation"
            )

    return feedback