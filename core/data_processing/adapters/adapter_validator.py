"""
Adapter Validation Framework
=============================

Comprehensive validation framework for adapter outputs that validates:
- Schema compliance against GeneralizedVariableDict
- Data type correctness
- Business rule compliance
- Data quality and completeness
- Cross-field consistency
- Temporal consistency

Supports configurable validation levels (strict, moderate, lenient) and
generates detailed validation reports with quality scores.

Usage Example
-------------
>>> from adapter_validator import AdapterValidator, ValidationLevel
>>> from types import GeneralizedVariableDict
>>>
>>> validator = AdapterValidator(level=ValidationLevel.STRICT)
>>> data: GeneralizedVariableDict = {
...     "ticker": "AAPL",
...     "company_name": "Apple Inc.",
...     "currency": "USD",
...     "fiscal_year_end": "September",
...     "revenue": 394328,
...     "net_income": 99803
... }
>>>
>>> result = validator.validate(data)
>>> print(f"Valid: {result.valid}")
>>> print(f"Quality Score: {result.quality_score:.2%}")
>>> print(f"Errors: {result.errors}")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from enum import Enum
import math

from .types import (
    GeneralizedVariableDict,
    ValidationResult,
    REQUIRED_FIELDS
)

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = "strict"      # All rules enforced, no tolerance for issues
    MODERATE = "moderate"  # Required fields enforced, warnings for issues
    LENIENT = "lenient"    # Only critical errors, most issues as warnings


class ValidationCategory(Enum):
    """Categories of validation checks"""
    REQUIRED_FIELDS = "required_fields"
    DATA_TYPES = "data_types"
    VALUE_RANGES = "value_ranges"
    CROSS_FIELD_CONSISTENCY = "cross_field_consistency"
    TEMPORAL_CONSISTENCY = "temporal_consistency"
    BUSINESS_RULES = "business_rules"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    category: ValidationCategory
    severity: str  # "error" or "warning"
    field: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    rule_name: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    valid: bool
    quality_score: float                    # 0.0 - 1.0
    completeness_score: float               # 0.0 - 1.0
    consistency_score: float                # 0.0 - 1.0
    overall_score: float                    # 0.0 - 1.0

    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    fields_validated: int = 0
    fields_passed: int = 0
    fields_failed: int = 0
    fields_missing: int = 0

    validation_level: ValidationLevel = ValidationLevel.MODERATE
    validation_timestamp: datetime = field(default_factory=datetime.now)

    details: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, issue: ValidationIssue):
        """Add an error"""
        issue.severity = "error"
        self.errors.append(issue)
        self.valid = False
        self.fields_failed += 1

    def add_warning(self, issue: ValidationIssue):
        """Add a warning"""
        issue.severity = "warning"
        self.warnings.append(issue)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'valid': self.valid,
            'quality_score': self.quality_score,
            'completeness_score': self.completeness_score,
            'consistency_score': self.consistency_score,
            'overall_score': self.overall_score,
            'errors': [
                {
                    'category': e.category.value,
                    'severity': e.severity,
                    'field': e.field,
                    'message': e.message,
                    'expected': e.expected,
                    'actual': e.actual,
                    'rule_name': e.rule_name
                }
                for e in self.errors
            ],
            'warnings': [
                {
                    'category': w.category.value,
                    'severity': w.severity,
                    'field': w.field,
                    'message': w.message,
                    'expected': w.expected,
                    'actual': w.actual,
                    'rule_name': w.rule_name
                }
                for w in self.warnings
            ],
            'fields_validated': self.fields_validated,
            'fields_passed': self.fields_passed,
            'fields_failed': self.fields_failed,
            'fields_missing': self.fields_missing,
            'validation_level': self.validation_level.value,
            'validation_timestamp': self.validation_timestamp.isoformat(),
            'details': self.details
        }


class AdapterValidator:
    """
    Comprehensive validator for adapter outputs.

    Validates GeneralizedVariableDict outputs from adapters against:
    - Schema compliance (required fields, optional fields)
    - Data type correctness
    - Business rules (accounting equations, ratio ranges, etc.)
    - Cross-field consistency
    - Temporal consistency

    Supports configurable validation levels and generates detailed reports.
    """

    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize validator with specified validation level.

        Args:
            level: Validation strictness level
        """
        self.level = level

        # Define expected types for fields
        self._field_types = self._build_field_type_map()

        # Define value range constraints
        self._value_ranges = self._build_value_ranges()

        # Define business rules
        self._business_rules = self._build_business_rules()

        logger.info(f"AdapterValidator initialized with level: {level.value}")

    def _build_field_type_map(self) -> Dict[str, type]:
        """Build map of expected types for each field"""
        return {
            # Metadata
            'ticker': str,
            'company_name': str,
            'currency': str,
            'fiscal_year_end': str,
            'sector': str,
            'industry': str,
            'country': str,
            'exchange': str,
            'description': str,
            'website': str,
            'ceo': str,
            'analyst_recommendation': str,
            'reporting_period': str,
            'data_source': str,
            'notes': str,

            # Integers
            'employees': int,
            'founded_year': int,
            'piotroski_f_score': int,
            'consecutive_dividend_years': int,
            'number_of_analysts': int,

            # Floats (financial values)
            'revenue': float,
            'net_income': float,
            'total_assets': float,
            'total_liabilities': float,
            'total_stockholders_equity': float,
            'operating_cash_flow': float,
            'free_cash_flow': float,
            'market_cap': float,
            'stock_price': float,

            # Dates
            'reporting_period_end': date,
            'filing_date': date,

            # Datetime
            'data_timestamp': datetime,
            'last_updated': datetime,

            # Booleans
            'restated': bool,
        }

    def _build_value_ranges(self) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
        """Build value range constraints (min, max) for fields"""
        return {
            # Ratios and percentages (stored as decimals)
            'gross_margin': (0.0, 1.0),
            'operating_margin': (-1.0, 1.0),  # Can be negative
            'net_margin': (-1.0, 1.0),
            'return_on_assets': (-1.0, 2.0),
            'return_on_equity': (-2.0, 3.0),
            'return_on_invested_capital': (-1.0, 2.0),
            'dividend_yield': (0.0, 0.5),  # 0-50%
            'dividend_payout_ratio': (0.0, 2.0),  # Can exceed 100% temporarily
            'insider_ownership': (0.0, 1.0),
            'institutional_ownership': (0.0, 1.0),
            'short_interest': (0.0, 1.0),
            'tax_rate': (0.0, 1.0),

            # Quality scores
            'data_quality_score': (0.0, 1.0),
            'completeness_score': (0.0, 1.0),
            'quality_of_earnings': (0.0, 10.0),

            # Ratios (non-percentage)
            'current_ratio': (0.0, 100.0),
            'quick_ratio': (0.0, 100.0),
            'debt_to_equity': (0.0, 50.0),
            'debt_to_assets': (0.0, 1.0),
            'pe_ratio': (-100.0, 1000.0),  # Can be negative or very high
            'peg_ratio': (0.0, 10.0),
            'price_to_book': (0.0, 100.0),

            # Scores
            'piotroski_f_score': (0, 9),
            'altman_z_score': (-10.0, 50.0),

            # Financial values (millions) - minimum validation only
            'revenue': (0.0, None),
            'total_assets': (0.0, None),
            'market_cap': (0.0, None),
            'shares_outstanding': (0.0, None),
        }

    def _build_business_rules(self) -> List[Tuple[str, Callable[[GeneralizedVariableDict], Tuple[bool, str]]]]:
        """
        Build list of business rules to validate.

        Returns list of (rule_name, validation_function) tuples.
        Validation function returns (is_valid, error_message)
        """
        rules = []

        # Rule: Assets = Liabilities + Equity
        def balance_sheet_equation(data: GeneralizedVariableDict) -> Tuple[bool, str]:
            assets = data.get('total_assets')
            liabilities = data.get('total_liabilities')
            equity = data.get('total_stockholders_equity')

            if all(v is not None for v in [assets, liabilities, equity]):
                calculated_total = liabilities + equity
                tolerance = max(abs(assets) * 0.01, 1.0)  # 1% or $1M tolerance

                if abs(assets - calculated_total) > tolerance:
                    return False, (
                        f"Balance sheet equation violation: "
                        f"Assets ({assets:.2f}) ` Liabilities ({liabilities:.2f}) + "
                        f"Equity ({equity:.2f}) = {calculated_total:.2f}"
                    )
            return True, ""

        rules.append(("balance_sheet_equation", balance_sheet_equation))

        # Rule: Gross Profit = Revenue - COGS
        def gross_profit_check(data: GeneralizedVariableDict) -> Tuple[bool, str]:
            revenue = data.get('revenue')
            cogs = data.get('cost_of_revenue')
            gross_profit = data.get('gross_profit')

            if all(v is not None for v in [revenue, cogs, gross_profit]):
                expected = revenue - cogs
                tolerance = max(abs(expected) * 0.01, 1.0)

                if abs(gross_profit - expected) > tolerance:
                    return False, (
                        f"Gross profit calculation error: "
                        f"Expected {expected:.2f} (Revenue {revenue:.2f} - COGS {cogs:.2f}), "
                        f"got {gross_profit:.2f}"
                    )
            return True, ""

        rules.append(("gross_profit_check", gross_profit_check))

        # Rule: Market Cap consistency
        def market_cap_check(data: GeneralizedVariableDict) -> Tuple[bool, str]:
            market_cap = data.get('market_cap')
            stock_price = data.get('stock_price')
            shares = data.get('shares_outstanding')

            if all(v is not None for v in [market_cap, stock_price, shares]):
                expected = stock_price * shares
                tolerance = max(abs(expected) * 0.05, 1.0)  # 5% tolerance

                if abs(market_cap - expected) > tolerance:
                    return False, (
                        f"Market cap inconsistency: "
                        f"Expected {expected:.2f} (Price {stock_price:.2f} � Shares {shares:.2f}), "
                        f"got {market_cap:.2f}"
                    )
            return True, ""

        rules.append(("market_cap_check", market_cap_check))

        # Rule: Free Cash Flow = Operating CF - CapEx
        def free_cash_flow_check(data: GeneralizedVariableDict) -> Tuple[bool, str]:
            fcf = data.get('free_cash_flow')
            ocf = data.get('operating_cash_flow')
            capex = data.get('capital_expenditures')

            if all(v is not None for v in [fcf, ocf, capex]):
                # CapEx is usually negative, so we add
                expected = ocf + capex if capex < 0 else ocf - capex
                tolerance = max(abs(expected) * 0.01, 1.0)

                if abs(fcf - expected) > tolerance:
                    return False, (
                        f"Free cash flow calculation error: "
                        f"Expected {expected:.2f} (OCF {ocf:.2f} - CapEx {abs(capex):.2f}), "
                        f"got {fcf:.2f}"
                    )
            return True, ""

        rules.append(("free_cash_flow_check", free_cash_flow_check))

        # Rule: Current Ratio calculation
        def current_ratio_check(data: GeneralizedVariableDict) -> Tuple[bool, str]:
            ratio = data.get('current_ratio')
            current_assets = data.get('total_current_assets')
            current_liabilities = data.get('total_current_liabilities')

            if all(v is not None for v in [ratio, current_assets, current_liabilities]):
                if current_liabilities == 0:
                    return True, ""  # Can't validate

                expected = current_assets / current_liabilities
                tolerance = max(expected * 0.01, 0.01)

                if abs(ratio - expected) > tolerance:
                    return False, (
                        f"Current ratio calculation error: "
                        f"Expected {expected:.2f} (Assets {current_assets:.2f} / "
                        f"Liabilities {current_liabilities:.2f}), got {ratio:.2f}"
                    )
            return True, ""

        rules.append(("current_ratio_check", current_ratio_check))

        return rules

    def validate_schema_compliance(
        self,
        data: GeneralizedVariableDict,
        report: ValidationReport
    ) -> None:
        """
        Validate that required fields are present.

        Args:
            data: Data to validate
            report: Report to update with findings
        """
        for field in REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                issue = ValidationIssue(
                    category=ValidationCategory.REQUIRED_FIELDS,
                    severity="error",
                    field=field,
                    message=f"Required field '{field}' is missing or None"
                )
                report.add_error(issue)
                report.fields_missing += 1
            else:
                report.fields_passed += 1

        report.fields_validated += len(REQUIRED_FIELDS)

    def validate_data_types(
        self,
        data: GeneralizedVariableDict,
        report: ValidationReport
    ) -> None:
        """
        Validate that field values have correct data types.

        Args:
            data: Data to validate
            report: Report to update with findings
        """
        for field, value in data.items():
            if value is None:
                continue  # Skip None values

            expected_type = self._field_types.get(field)
            if expected_type is None:
                continue  # Unknown field, skip type check

            report.fields_validated += 1

            # Check type
            if not isinstance(value, expected_type):
                issue = ValidationIssue(
                    category=ValidationCategory.DATA_TYPES,
                    severity="error",
                    field=field,
                    message=f"Type mismatch: expected {expected_type.__name__}, got {type(value).__name__}",
                    expected=expected_type.__name__,
                    actual=type(value).__name__
                )

                if self.level == ValidationLevel.STRICT:
                    report.add_error(issue)
                else:
                    report.add_warning(issue)
                    report.fields_passed += 1
            else:
                report.fields_passed += 1

    def validate_value_ranges(
        self,
        data: GeneralizedVariableDict,
        report: ValidationReport
    ) -> None:
        """
        Validate that numeric values are within expected ranges.

        Args:
            data: Data to validate
            report: Report to update with findings
        """
        for field, (min_val, max_val) in self._value_ranges.items():
            value = data.get(field)

            if value is None:
                continue

            report.fields_validated += 1

            # Check if numeric
            if not isinstance(value, (int, float)):
                continue

            # Check min
            if min_val is not None and value < min_val:
                issue = ValidationIssue(
                    category=ValidationCategory.VALUE_RANGES,
                    severity="error",
                    field=field,
                    message=f"Value {value} is below minimum {min_val}",
                    expected=f">= {min_val}",
                    actual=value
                )

                if self.level == ValidationLevel.STRICT:
                    report.add_error(issue)
                else:
                    report.add_warning(issue)
                    report.fields_passed += 1
                continue

            # Check max
            if max_val is not None and value > max_val:
                issue = ValidationIssue(
                    category=ValidationCategory.VALUE_RANGES,
                    severity="warning",
                    field=field,
                    message=f"Value {value} exceeds maximum {max_val}",
                    expected=f"<= {max_val}",
                    actual=value
                )
                report.add_warning(issue)

            report.fields_passed += 1

    def validate_business_rules(
        self,
        data: GeneralizedVariableDict,
        report: ValidationReport
    ) -> None:
        """
        Validate business rules and cross-field consistency.

        Args:
            data: Data to validate
            report: Report to update with findings
        """
        for rule_name, rule_func in self._business_rules:
            try:
                is_valid, error_msg = rule_func(data)

                if not is_valid:
                    issue = ValidationIssue(
                        category=ValidationCategory.BUSINESS_RULES,
                        severity="error",
                        field="multiple",
                        message=error_msg,
                        rule_name=rule_name
                    )

                    if self.level == ValidationLevel.LENIENT:
                        report.add_warning(issue)
                    else:
                        report.add_error(issue)

            except Exception as e:
                logger.warning(f"Business rule '{rule_name}' failed with exception: {e}")

    def generate_quality_score(
        self,
        data: GeneralizedVariableDict,
        report: ValidationReport
    ) -> float:
        """
        Generate overall quality score (0.0 - 1.0).

        Args:
            data: Data that was validated
            report: Validation report with findings

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Calculate completeness score
        total_possible_fields = 150  # Approximate total fields in schema
        present_fields = sum(1 for v in data.values() if v is not None)
        completeness = min(present_fields / total_possible_fields, 1.0)
        report.completeness_score = completeness

        # Calculate consistency score based on errors/warnings
        total_checks = report.fields_validated
        if total_checks == 0:
            consistency = 0.0
        else:
            # Errors count more than warnings
            error_penalty = len(report.errors) * 2
            warning_penalty = len(report.warnings)
            total_penalties = error_penalty + warning_penalty

            consistency = max(1.0 - (total_penalties / total_checks), 0.0)

        report.consistency_score = consistency

        # Calculate quality score (weighted average)
        # 40% completeness, 60% consistency
        quality_score = (0.4 * completeness) + (0.6 * consistency)
        report.quality_score = quality_score

        # Overall score considers if validation passed
        if report.valid:
            report.overall_score = quality_score
        else:
            # Penalize failed validation
            report.overall_score = quality_score * 0.5

        return report.overall_score

    def validate(
        self,
        data: GeneralizedVariableDict,
        include_quality_score: bool = True
    ) -> ValidationReport:
        """
        Perform comprehensive validation on adapter output.

        Args:
            data: GeneralizedVariableDict to validate
            include_quality_score: Whether to calculate quality score

        Returns:
            ValidationReport with all findings
        """
        logger.info(f"Starting validation with level: {self.level.value}")

        report = ValidationReport(
            valid=True,  # Assume valid until proven otherwise
            quality_score=0.0,
            completeness_score=0.0,
            consistency_score=0.0,
            overall_score=0.0,
            validation_level=self.level
        )

        # Run validation checks
        self.validate_schema_compliance(data, report)
        self.validate_data_types(data, report)
        self.validate_value_ranges(data, report)
        self.validate_business_rules(data, report)

        # Generate quality score
        if include_quality_score:
            self.generate_quality_score(data, report)

        # Add summary to details
        report.details['total_fields_in_data'] = len(data)
        report.details['non_null_fields'] = sum(1 for v in data.values() if v is not None)
        report.details['validation_level'] = self.level.value

        logger.info(
            f"Validation complete: valid={report.valid}, "
            f"quality_score={report.quality_score:.2%}, "
            f"errors={len(report.errors)}, warnings={len(report.warnings)}"
        )

        return report

    def __repr__(self) -> str:
        """String representation"""
        return f"AdapterValidator(level={self.level.value})"


# ============================================================================
# Convenience Functions
# ============================================================================

# Global validator instance (singleton pattern)
_default_validator: Optional[AdapterValidator] = None


def get_validator(level: ValidationLevel = ValidationLevel.MODERATE) -> AdapterValidator:
    """
    Get or create a global AdapterValidator instance.

    This provides a convenient way to access a shared validator instance
    throughout the application.

    Args:
        level: Validation level (only used if creating new instance)

    Returns:
        AdapterValidator instance
    """
    global _default_validator

    if _default_validator is None:
        _default_validator = AdapterValidator(level=level)

    return _default_validator
