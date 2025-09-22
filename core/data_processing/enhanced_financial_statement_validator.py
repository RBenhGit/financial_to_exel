"""
Enhanced Financial Statement Validator
=====================================

This module provides comprehensive validation for financial statements including:
- Cross-statement consistency checks (balance sheet equations, cash flow reconciliation)
- Range validation with business rule constraints
- Data completeness scoring integrated with existing quality scorer
- Cross-period validation for historical data consistency

Key Features:
- Balance sheet equation validation (Assets = Liabilities + Equity)
- Cash flow reconciliation checks
- Income statement reasonableness validation
- Cross-period trend analysis and anomaly detection
- Business rule constraints for financial metrics
- Integration with existing FinancialDataValidator and AdvancedDataQualityScorer
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

from .data_validator import FinancialDataValidator, DataQualityReport
from .advanced_data_quality_scorer import AdvancedDataQualityScorer, QualityMetrics

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks"""
    BALANCE_SHEET_EQUATION = "balance_sheet_equation"
    CASH_FLOW_RECONCILIATION = "cash_flow_reconciliation"
    INCOME_STATEMENT_CONSISTENCY = "income_statement_consistency"
    CROSS_PERIOD_VALIDATION = "cross_period_validation"
    BUSINESS_RULE_CONSTRAINTS = "business_rule_constraints"
    DATA_COMPLETENESS = "data_completeness"


@dataclass
class ValidationIssue:
    """Container for a validation issue"""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    details: str
    affected_metrics: List[str]
    suggested_fix: str
    confidence_score: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FinancialStatementValidationReport:
    """Comprehensive validation report for financial statements"""
    overall_score: float = 0.0
    total_checks_performed: int = 0
    issues_found: List[ValidationIssue] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)

    # Category-specific scores
    balance_sheet_score: float = 0.0
    cash_flow_score: float = 0.0
    income_statement_score: float = 0.0
    cross_period_score: float = 0.0
    business_rules_score: float = 0.0
    completeness_score: float = 0.0

    # Data quality integration
    quality_metrics: Optional[QualityMetrics] = None
    base_data_quality_report: Optional[DataQualityReport] = None

    validation_timestamp: datetime = field(default_factory=datetime.now)

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity level"""
        return [issue for issue in self.issues_found if issue.severity == severity]

    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues filtered by category"""
        return [issue for issue in self.issues_found if issue.category == category]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues"""
        return any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues_found)

    def get_summary(self) -> str:
        """Generate a human-readable summary"""
        critical_count = len(self.get_issues_by_severity(ValidationSeverity.CRITICAL))
        error_count = len(self.get_issues_by_severity(ValidationSeverity.ERROR))
        warning_count = len(self.get_issues_by_severity(ValidationSeverity.WARNING))

        summary = [
            f"\n{'='*60}",
            f"FINANCIAL STATEMENT VALIDATION REPORT",
            f"Timestamp: {self.validation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*60}",
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Total Checks: {self.total_checks_performed}",
            f"",
            f"Issues Summary:",
            f"- Critical: {critical_count}",
            f"- Errors: {error_count}",
            f"- Warnings: {warning_count}",
            f"",
            f"Category Scores:",
            f"- Balance Sheet: {self.balance_sheet_score:.1f}/100",
            f"- Cash Flow: {self.cash_flow_score:.1f}/100",
            f"- Income Statement: {self.income_statement_score:.1f}/100",
            f"- Cross-Period: {self.cross_period_score:.1f}/100",
            f"- Business Rules: {self.business_rules_score:.1f}/100",
            f"- Completeness: {self.completeness_score:.1f}/100"
        ]

        if critical_count > 0:
            summary.append(f"\nCRITICAL ISSUES:")
            for issue in self.get_issues_by_severity(ValidationSeverity.CRITICAL)[:3]:
                summary.append(f"  • {issue.message}")

        if error_count > 0:
            summary.append(f"\nERRORS:")
            for issue in self.get_issues_by_severity(ValidationSeverity.ERROR)[:3]:
                summary.append(f"  • {issue.message}")

        summary.append(f"{'='*60}")
        return "\n".join(summary)


class EnhancedFinancialStatementValidator:
    """
    Enhanced financial statement validator with comprehensive validation capabilities
    """

    def __init__(self):
        """Initialize the enhanced validator"""
        self.base_validator = FinancialDataValidator()
        self.quality_scorer = AdvancedDataQualityScorer()
        self.validation_rules = self._initialize_validation_rules()

        logger.info("Enhanced Financial Statement Validator initialized")

    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules and thresholds"""
        return {
            # Balance sheet equation tolerances
            "balance_sheet_tolerance": 0.01,  # 1% tolerance for rounding differences

            # Cash flow reconciliation tolerances
            "cash_flow_tolerance": 0.05,  # 5% tolerance for reconciliation differences

            # Business rule constraints
            "business_rules": {
                # Assets should be positive
                "positive_assets": ["Total Current Assets", "Total Assets", "Cash and Cash Equivalents"],

                # Some liabilities can be negative (prepaid expenses, etc.)
                "allow_negative_liabilities": ["Deferred Tax Liabilities"],

                # Revenue growth constraints
                "max_reasonable_growth": 5.0,  # 500% year-over-year growth
                "min_reasonable_growth": -0.9,  # -90% year-over-year decline

                # Profitability constraints
                "profit_margin_bounds": (-2.0, 5.0),  # -200% to 500% margin range

                # Debt ratios
                "max_debt_to_equity": 10.0,  # Maximum 10:1 debt-to-equity ratio

                # Working capital
                "min_current_ratio": 0.1,  # Minimum current ratio
                "max_current_ratio": 50.0,  # Maximum current ratio
            },

            # Cross-period validation
            "cross_period": {
                "min_periods_required": 3,
                "outlier_threshold": 3.0,  # Standard deviations for outlier detection
                "trend_analysis_periods": 5,
            },

            # Completeness requirements
            "completeness": {
                "critical_metrics": [
                    "Net Income", "Total Assets", "Total Current Liabilities",
                    "Cash from Operations", "Revenue"
                ],
                "min_completeness_score": 80.0,
                "min_data_points_per_metric": 3,
            }
        }

    def validate_financial_statements(
        self,
        financial_data: Dict[str, Any],
        source_identifier: str = "",
        include_quality_scoring: bool = True
    ) -> FinancialStatementValidationReport:
        """
        Perform comprehensive validation of financial statements

        Args:
            financial_data: Dictionary containing financial statement data
            source_identifier: Identifier for the data source
            include_quality_scoring: Whether to include advanced quality scoring

        Returns:
            FinancialStatementValidationReport with validation results
        """
        logger.info(f"Starting enhanced financial statement validation for: {source_identifier}")

        # Initialize report
        report = FinancialStatementValidationReport()

        try:
            # Step 1: Basic data validation using existing validator
            report.base_data_quality_report = self.base_validator.validate_financial_statements(financial_data)

            # Step 2: Advanced quality scoring if requested
            if include_quality_scoring:
                report.quality_metrics = self.quality_scorer.score_data_quality(
                    financial_data, source_identifier
                )
                report.completeness_score = report.quality_metrics.completeness

            # Step 3: Balance sheet equation validation
            self._validate_balance_sheet_equation(financial_data, report)

            # Step 4: Cash flow reconciliation validation
            self._validate_cash_flow_reconciliation(financial_data, report)

            # Step 5: Income statement consistency validation
            self._validate_income_statement_consistency(financial_data, report)

            # Step 6: Cross-period validation
            self._validate_cross_period_consistency(financial_data, report)

            # Step 7: Business rule constraints validation
            self._validate_business_rule_constraints(financial_data, report)

            # Step 8: Data completeness validation
            self._validate_data_completeness(financial_data, report)

            # Step 9: Calculate overall score
            self._calculate_overall_score(report)

            logger.info(f"Validation completed. Overall score: {report.overall_score:.1f}")

        except Exception as e:
            logger.error(f"Error during enhanced validation: {e}")
            self._add_issue(
                report, ValidationCategory.DATA_COMPLETENESS, ValidationSeverity.CRITICAL,
                f"Validation process failed: {str(e)}",
                "Critical error occurred during validation process",
                [], "Review data structure and format"
            )

        return report

    def _validate_balance_sheet_equation(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate balance sheet equation: Assets = Liabilities + Equity"""
        try:
            balance_data = financial_data.get('balance_fy', {})
            if not balance_data:
                self._add_issue(
                    report, ValidationCategory.BALANCE_SHEET_EQUATION, ValidationSeverity.ERROR,
                    "No balance sheet data available for equation validation",
                    "Balance sheet data is missing or empty",
                    [], "Ensure balance sheet data is properly loaded"
                )
                return

            # Extract key balance sheet components
            assets = self._extract_metric_values(balance_data, "Total Assets")
            liabilities = self._extract_metric_values(balance_data, "Total Liabilities")
            equity = self._extract_metric_values(balance_data, "Total Stockholders' Equity")

            if not assets or not liabilities or not equity:
                missing_items = []
                if not assets: missing_items.append("Total Assets")
                if not liabilities: missing_items.append("Total Liabilities")
                if not equity: missing_items.append("Total Stockholders' Equity")

                self._add_issue(
                    report, ValidationCategory.BALANCE_SHEET_EQUATION, ValidationSeverity.ERROR,
                    f"Missing balance sheet components: {', '.join(missing_items)}",
                    "Cannot validate balance sheet equation without all components",
                    missing_items, "Ensure all balance sheet components are present in data"
                )
                return

            # Validate equation for each period
            equation_issues = 0
            tolerance = self.validation_rules["balance_sheet_tolerance"]

            for i, (asset_val, liability_val, equity_val) in enumerate(zip(assets, liabilities, equity)):
                if None in [asset_val, liability_val, equity_val]:
                    continue

                try:
                    asset_val = float(asset_val)
                    liability_val = float(liability_val)
                    equity_val = float(equity_val)

                    left_side = asset_val
                    right_side = liability_val + equity_val

                    if right_side != 0:
                        relative_error = abs(left_side - right_side) / abs(right_side)
                    else:
                        relative_error = abs(left_side - right_side)

                    if relative_error > tolerance:
                        equation_issues += 1
                        self._add_issue(
                            report, ValidationCategory.BALANCE_SHEET_EQUATION, ValidationSeverity.WARNING,
                            f"Balance sheet equation imbalance in period {i+1}",
                            f"Assets ({asset_val:,.0f}) ≠ Liabilities + Equity ({right_side:,.0f}), "
                            f"difference: {relative_error:.1%}",
                            ["Total Assets", "Total Liabilities", "Total Stockholders' Equity"],
                            "Review balance sheet figures for calculation errors or missing items"
                        )

                except (ValueError, TypeError, ZeroDivisionError) as e:
                    self._add_issue(
                        report, ValidationCategory.BALANCE_SHEET_EQUATION, ValidationSeverity.WARNING,
                        f"Cannot validate balance sheet equation for period {i+1}",
                        f"Data conversion error: {str(e)}",
                        ["Total Assets", "Total Liabilities", "Total Stockholders' Equity"],
                        "Check data format and ensure numeric values"
                    )

            # Calculate balance sheet score
            total_periods = max(len(assets), len(liabilities), len(equity))
            if total_periods > 0:
                report.balance_sheet_score = max(0, 100 - (equation_issues / total_periods * 50))
            else:
                report.balance_sheet_score = 0

            if equation_issues == 0:
                report.passed_checks.append("Balance sheet equation validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in balance sheet equation validation: {e}")
            self._add_issue(
                report, ValidationCategory.BALANCE_SHEET_EQUATION, ValidationSeverity.ERROR,
                "Balance sheet equation validation failed",
                f"Validation error: {str(e)}",
                [], "Review balance sheet data structure"
            )

    def _validate_cash_flow_reconciliation(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate cash flow statement reconciliation"""
        try:
            cashflow_data = financial_data.get('cashflow_fy', {})
            balance_data = financial_data.get('balance_fy', {})

            if not cashflow_data:
                self._add_issue(
                    report, ValidationCategory.CASH_FLOW_RECONCILIATION, ValidationSeverity.WARNING,
                    "No cash flow data available for reconciliation",
                    "Cash flow statement data is missing",
                    [], "Ensure cash flow statement data is included"
                )
                return

            # Extract cash flow components
            operating_cash_flow = self._extract_metric_values(cashflow_data, "Cash from Operations")
            investing_cash_flow = self._extract_metric_values(cashflow_data, "Cash from Investing")
            financing_cash_flow = self._extract_metric_values(cashflow_data, "Cash from Financing")

            # Extract cash positions from balance sheet if available
            cash_beginning = None
            cash_ending = None
            if balance_data:
                cash_values = self._extract_metric_values(balance_data, "Cash and Cash Equivalents")
                if cash_values and len(cash_values) > 1:
                    # For reconciliation, we need consecutive periods
                    cash_ending = cash_values[:-1]  # Most recent periods
                    cash_beginning = cash_values[1:]  # Previous periods

            reconciliation_issues = 0
            tolerance = self.validation_rules["cash_flow_tolerance"]

            # Validate cash flow reconciliation
            if all([operating_cash_flow, investing_cash_flow, financing_cash_flow]):
                for i, (op_cf, inv_cf, fin_cf) in enumerate(zip(
                    operating_cash_flow, investing_cash_flow, financing_cash_flow
                )):
                    if None in [op_cf, inv_cf, fin_cf]:
                        continue

                    try:
                        op_cf = float(op_cf) if op_cf is not None else 0
                        inv_cf = float(inv_cf) if inv_cf is not None else 0
                        fin_cf = float(fin_cf) if fin_cf is not None else 0

                        net_cash_flow = op_cf + inv_cf + fin_cf

                        # If we have balance sheet cash data, validate reconciliation
                        if cash_beginning and cash_ending and i < len(cash_beginning) and i < len(cash_ending):
                            try:
                                beginning_cash = float(cash_beginning[i])
                                ending_cash = float(cash_ending[i])
                                expected_ending = beginning_cash + net_cash_flow

                                if ending_cash != 0:
                                    reconciliation_error = abs(ending_cash - expected_ending) / abs(ending_cash)
                                else:
                                    reconciliation_error = abs(ending_cash - expected_ending)

                                if reconciliation_error > tolerance:
                                    reconciliation_issues += 1
                                    self._add_issue(
                                        report, ValidationCategory.CASH_FLOW_RECONCILIATION, ValidationSeverity.WARNING,
                                        f"Cash flow reconciliation issue in period {i+1}",
                                        f"Beginning cash ({beginning_cash:,.0f}) + Net cash flow ({net_cash_flow:,.0f}) "
                                        f"≠ Ending cash ({ending_cash:,.0f}), error: {reconciliation_error:.1%}",
                                        ["Cash from Operations", "Cash from Investing", "Cash from Financing", "Cash and Cash Equivalents"],
                                        "Review cash flow calculations and balance sheet cash positions"
                                    )
                            except (ValueError, TypeError, ZeroDivisionError):
                                pass

                        # Check for reasonable cash flow patterns
                        if abs(net_cash_flow) > 1e12:  # Extremely large cash flows
                            self._add_issue(
                                report, ValidationCategory.CASH_FLOW_RECONCILIATION, ValidationSeverity.WARNING,
                                f"Unusually large net cash flow in period {i+1}",
                                f"Net cash flow of {net_cash_flow:,.0f} appears unreasonably large",
                                ["Cash from Operations", "Cash from Investing", "Cash from Financing"],
                                "Review cash flow figures for potential unit errors"
                            )

                    except (ValueError, TypeError) as e:
                        reconciliation_issues += 1
                        self._add_issue(
                            report, ValidationCategory.CASH_FLOW_RECONCILIATION, ValidationSeverity.WARNING,
                            f"Cash flow data validation error in period {i+1}",
                            f"Cannot validate cash flows: {str(e)}",
                            ["Cash from Operations", "Cash from Investing", "Cash from Financing"],
                            "Check cash flow data format and ensure numeric values"
                        )

            # Calculate cash flow score
            total_periods = max(len(operating_cash_flow or []), len(investing_cash_flow or []), len(financing_cash_flow or []))
            if total_periods > 0:
                report.cash_flow_score = max(0, 100 - (reconciliation_issues / total_periods * 30))
            else:
                report.cash_flow_score = 50  # Neutral score if no data

            if reconciliation_issues == 0 and total_periods > 0:
                report.passed_checks.append("Cash flow reconciliation validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in cash flow reconciliation validation: {e}")
            self._add_issue(
                report, ValidationCategory.CASH_FLOW_RECONCILIATION, ValidationSeverity.ERROR,
                "Cash flow reconciliation validation failed",
                f"Validation error: {str(e)}",
                [], "Review cash flow statement data structure"
            )

    def _validate_income_statement_consistency(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate income statement internal consistency"""
        try:
            income_data = financial_data.get('income_fy', {})
            if not income_data:
                self._add_issue(
                    report, ValidationCategory.INCOME_STATEMENT_CONSISTENCY, ValidationSeverity.WARNING,
                    "No income statement data available for consistency validation",
                    "Income statement data is missing",
                    [], "Ensure income statement data is included"
                )
                return

            # Extract key income statement components
            revenue = self._extract_metric_values(income_data, "Revenue")
            gross_profit = self._extract_metric_values(income_data, "Gross Profit")
            operating_income = self._extract_metric_values(income_data, "EBIT")
            net_income = self._extract_metric_values(income_data, "Net Income")

            consistency_issues = 0

            # Validate gross profit vs revenue relationship
            if revenue and gross_profit:
                for i, (rev, gp) in enumerate(zip(revenue, gross_profit)):
                    if None in [rev, gp]:
                        continue

                    try:
                        rev = float(rev)
                        gp = float(gp)

                        # Gross profit should not exceed revenue (except in rare cases)
                        if rev > 0 and gp > rev * 1.1:  # Allow 10% tolerance for rounding
                            consistency_issues += 1
                            self._add_issue(
                                report, ValidationCategory.INCOME_STATEMENT_CONSISTENCY, ValidationSeverity.WARNING,
                                f"Gross profit exceeds revenue in period {i+1}",
                                f"Gross profit ({gp:,.0f}) > Revenue ({rev:,.0f})",
                                ["Revenue", "Gross Profit"],
                                "Review gross profit calculation and cost of goods sold"
                            )

                        # Check for negative gross margins that are too extreme
                        if rev > 0:
                            gross_margin = gp / rev
                            if gross_margin < -2.0:  # -200% margin
                                consistency_issues += 1
                                self._add_issue(
                                    report, ValidationCategory.INCOME_STATEMENT_CONSISTENCY, ValidationSeverity.WARNING,
                                    f"Extremely negative gross margin in period {i+1}",
                                    f"Gross margin: {gross_margin:.1%}",
                                    ["Revenue", "Gross Profit"],
                                    "Review cost of goods sold and revenue recognition"
                                )

                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

            # Validate operating income vs gross profit relationship
            if gross_profit and operating_income:
                for i, (gp, oi) in enumerate(zip(gross_profit, operating_income)):
                    if None in [gp, oi]:
                        continue

                    try:
                        gp = float(gp)
                        oi = float(oi)

                        # Operating income should generally not exceed gross profit by a large margin
                        if gp > 0 and oi > gp * 1.5:  # Allow 50% tolerance
                            consistency_issues += 1
                            self._add_issue(
                                report, ValidationCategory.INCOME_STATEMENT_CONSISTENCY, ValidationSeverity.WARNING,
                                f"Operating income significantly exceeds gross profit in period {i+1}",
                                f"Operating income ({oi:,.0f}) > 1.5 × Gross profit ({gp:,.0f})",
                                ["Gross Profit", "EBIT"],
                                "Review operating expense calculations and non-operating income"
                            )

                    except (ValueError, TypeError):
                        pass

            # Calculate income statement score
            total_checks = 0
            if revenue and gross_profit:
                total_checks += len(revenue)
            if gross_profit and operating_income:
                total_checks += len(gross_profit)

            if total_checks > 0:
                report.income_statement_score = max(0, 100 - (consistency_issues / total_checks * 40))
            else:
                report.income_statement_score = 50  # Neutral score if no data

            if consistency_issues == 0 and total_checks > 0:
                report.passed_checks.append("Income statement consistency validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in income statement consistency validation: {e}")
            self._add_issue(
                report, ValidationCategory.INCOME_STATEMENT_CONSISTENCY, ValidationSeverity.ERROR,
                "Income statement consistency validation failed",
                f"Validation error: {str(e)}",
                [], "Review income statement data structure"
            )

    def _validate_cross_period_consistency(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate consistency across time periods"""
        try:
            cross_period_rules = self.validation_rules["cross_period"]
            min_periods = cross_period_rules["min_periods_required"]
            outlier_threshold = cross_period_rules["outlier_threshold"]

            cross_period_issues = 0
            total_metrics_checked = 0

            # Check each statement type
            for statement_name, statement_data in financial_data.items():
                if not statement_data:
                    continue

                # Extract all metrics from this statement
                for metric_name, values in statement_data.items():
                    if not isinstance(values, (list, tuple)) or len(values) < min_periods:
                        continue

                    # Convert to numeric values
                    numeric_values = []
                    for val in values:
                        try:
                            if val is not None and val != '':
                                numeric_values.append(float(val))
                            else:
                                numeric_values.append(None)
                        except (ValueError, TypeError):
                            numeric_values.append(None)

                    # Skip if insufficient valid data
                    valid_values = [v for v in numeric_values if v is not None]
                    if len(valid_values) < min_periods:
                        continue

                    total_metrics_checked += 1

                    # Check for outliers using z-score
                    if len(valid_values) >= 3:
                        mean_val = np.mean(valid_values)
                        std_val = np.std(valid_values)

                        if std_val > 0:
                            for i, val in enumerate(numeric_values):
                                if val is not None:
                                    z_score = abs(val - mean_val) / std_val
                                    if z_score > outlier_threshold:
                                        cross_period_issues += 1
                                        self._add_issue(
                                            report, ValidationCategory.CROSS_PERIOD_VALIDATION, ValidationSeverity.WARNING,
                                            f"Statistical outlier detected in {metric_name}",
                                            f"Period {i+1} value ({val:,.0f}) is {z_score:.1f} standard deviations from mean",
                                            [metric_name],
                                            "Review data for potential data entry errors or extraordinary events",
                                            confidence_score=min(1.0, z_score / outlier_threshold)
                                        )

                    # Check for unreasonable growth rates
                    for i in range(1, len(numeric_values)):
                        if numeric_values[i] is not None and numeric_values[i-1] is not None:
                            prev_val = numeric_values[i-1]
                            curr_val = numeric_values[i]

                            if prev_val != 0:
                                growth_rate = (curr_val - prev_val) / abs(prev_val)

                                max_growth = self.validation_rules["business_rules"]["max_reasonable_growth"]
                                min_growth = self.validation_rules["business_rules"]["min_reasonable_growth"]

                                if growth_rate > max_growth or growth_rate < min_growth:
                                    cross_period_issues += 1
                                    self._add_issue(
                                        report, ValidationCategory.CROSS_PERIOD_VALIDATION, ValidationSeverity.WARNING,
                                        f"Extreme growth rate in {metric_name}",
                                        f"Period {i} to {i+1}: {growth_rate:.1%} growth "
                                        f"(from {prev_val:,.0f} to {curr_val:,.0f})",
                                        [metric_name],
                                        "Verify data accuracy and consider if extreme growth is justified"
                                    )

            # Calculate cross-period score
            if total_metrics_checked > 0:
                report.cross_period_score = max(0, 100 - (cross_period_issues / total_metrics_checked * 20))
            else:
                report.cross_period_score = 50

            if cross_period_issues == 0 and total_metrics_checked > 0:
                report.passed_checks.append("Cross-period consistency validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in cross-period validation: {e}")
            self._add_issue(
                report, ValidationCategory.CROSS_PERIOD_VALIDATION, ValidationSeverity.ERROR,
                "Cross-period validation failed",
                f"Validation error: {str(e)}",
                [], "Review time series data structure"
            )

    def _validate_business_rule_constraints(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate business rule constraints"""
        try:
            business_rules = self.validation_rules["business_rules"]
            rule_violations = 0
            total_rule_checks = 0

            # Check positive asset constraints
            for asset_metric in business_rules["positive_assets"]:
                values = self._find_metric_in_statements(financial_data, asset_metric)
                if values:
                    for i, val in enumerate(values):
                        if val is not None:
                            try:
                                val = float(val)
                                total_rule_checks += 1
                                if val < 0:
                                    rule_violations += 1
                                    self._add_issue(
                                        report, ValidationCategory.BUSINESS_RULE_CONSTRAINTS, ValidationSeverity.WARNING,
                                        f"Negative value for {asset_metric}",
                                        f"Period {i+1}: {val:,.0f} (assets should be positive)",
                                        [asset_metric],
                                        "Review asset calculations and ensure proper classification"
                                    )
                            except (ValueError, TypeError):
                                pass

            # Check profitability ratios
            income_data = financial_data.get('income_fy', {})
            if income_data:
                revenue = self._extract_metric_values(income_data, "Revenue")
                net_income = self._extract_metric_values(income_data, "Net Income")

                if revenue and net_income:
                    min_margin, max_margin = business_rules["profit_margin_bounds"]
                    for i, (rev, ni) in enumerate(zip(revenue, net_income)):
                        if None in [rev, ni]:
                            continue

                        try:
                            rev = float(rev)
                            ni = float(ni)
                            total_rule_checks += 1

                            if rev > 0:
                                margin = ni / rev
                                if margin < min_margin or margin > max_margin:
                                    rule_violations += 1
                                    self._add_issue(
                                        report, ValidationCategory.BUSINESS_RULE_CONSTRAINTS, ValidationSeverity.WARNING,
                                        f"Extreme profit margin in period {i+1}",
                                        f"Net margin: {margin:.1%} (bounds: {min_margin:.0%} to {max_margin:.0%})",
                                        ["Revenue", "Net Income"],
                                        "Review profitability calculations for reasonableness"
                                    )
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

            # Check debt-to-equity ratio
            balance_data = financial_data.get('balance_fy', {})
            if balance_data:
                total_debt = self._extract_metric_values(balance_data, "Total Liabilities")
                total_equity = self._extract_metric_values(balance_data, "Total Stockholders' Equity")

                if total_debt and total_equity:
                    max_debt_equity = business_rules["max_debt_to_equity"]
                    for i, (debt, equity) in enumerate(zip(total_debt, total_equity)):
                        if None in [debt, equity]:
                            continue

                        try:
                            debt = float(debt)
                            equity = float(equity)
                            total_rule_checks += 1

                            if equity > 0:
                                debt_to_equity = debt / equity
                                if debt_to_equity > max_debt_equity:
                                    rule_violations += 1
                                    self._add_issue(
                                        report, ValidationCategory.BUSINESS_RULE_CONSTRAINTS, ValidationSeverity.WARNING,
                                        f"High debt-to-equity ratio in period {i+1}",
                                        f"Debt-to-equity: {debt_to_equity:.1f}x (max: {max_debt_equity:.1f}x)",
                                        ["Total Liabilities", "Total Stockholders' Equity"],
                                        "Review debt levels and capital structure"
                                    )
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

            # Check current ratio
            if balance_data:
                current_assets = self._extract_metric_values(balance_data, "Total Current Assets")
                current_liabilities = self._extract_metric_values(balance_data, "Total Current Liabilities")

                if current_assets and current_liabilities:
                    min_ratio = business_rules["min_current_ratio"]
                    max_ratio = business_rules["max_current_ratio"]

                    for i, (assets, liabilities) in enumerate(zip(current_assets, current_liabilities)):
                        if None in [assets, liabilities]:
                            continue

                        try:
                            assets = float(assets)
                            liabilities = float(liabilities)
                            total_rule_checks += 1

                            if liabilities > 0:
                                current_ratio = assets / liabilities
                                if current_ratio < min_ratio or current_ratio > max_ratio:
                                    severity = ValidationSeverity.WARNING if current_ratio < min_ratio else ValidationSeverity.INFO
                                    rule_violations += 1
                                    self._add_issue(
                                        report, ValidationCategory.BUSINESS_RULE_CONSTRAINTS, severity,
                                        f"Current ratio outside normal range in period {i+1}",
                                        f"Current ratio: {current_ratio:.2f} (range: {min_ratio:.2f} to {max_ratio:.2f})",
                                        ["Total Current Assets", "Total Current Liabilities"],
                                        "Review working capital management"
                                    )
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

            # Calculate business rules score
            if total_rule_checks > 0:
                report.business_rules_score = max(0, 100 - (rule_violations / total_rule_checks * 25))
            else:
                report.business_rules_score = 50

            if rule_violations == 0 and total_rule_checks > 0:
                report.passed_checks.append("Business rule constraints validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in business rule validation: {e}")
            self._add_issue(
                report, ValidationCategory.BUSINESS_RULE_CONSTRAINTS, ValidationSeverity.ERROR,
                "Business rule validation failed",
                f"Validation error: {str(e)}",
                [], "Review financial data for business rule compliance"
            )

    def _validate_data_completeness(self, financial_data: Dict[str, Any], report: FinancialStatementValidationReport):
        """Validate data completeness"""
        try:
            completeness_rules = self.validation_rules["completeness"]
            critical_metrics = completeness_rules["critical_metrics"]
            min_completeness = completeness_rules["min_completeness_score"]
            min_data_points = completeness_rules["min_data_points_per_metric"]

            completeness_issues = 0
            total_critical_metrics = len(critical_metrics)
            found_critical_metrics = 0

            for metric_name in critical_metrics:
                values = self._find_metric_in_statements(financial_data, metric_name)
                if values:
                    found_critical_metrics += 1

                    # Check number of data points
                    valid_data_points = sum(1 for v in values if v is not None and v != '')
                    if valid_data_points < min_data_points:
                        completeness_issues += 1
                        self._add_issue(
                            report, ValidationCategory.DATA_COMPLETENESS, ValidationSeverity.WARNING,
                            f"Insufficient data points for critical metric: {metric_name}",
                            f"Found {valid_data_points} valid data points, minimum required: {min_data_points}",
                            [metric_name],
                            "Ensure sufficient historical data is available"
                        )
                else:
                    completeness_issues += 1
                    self._add_issue(
                        report, ValidationCategory.DATA_COMPLETENESS, ValidationSeverity.ERROR,
                        f"Critical metric missing: {metric_name}",
                        "Required financial metric not found in any statement",
                        [metric_name],
                        "Ensure all critical financial metrics are included in data"
                    )

            # Calculate completeness score based on critical metrics found
            if total_critical_metrics > 0:
                critical_metrics_score = (found_critical_metrics / total_critical_metrics) * 100
            else:
                critical_metrics_score = 100

            # Use quality scorer completeness if available, otherwise use critical metrics score
            if report.quality_metrics:
                report.completeness_score = report.quality_metrics.completeness
            else:
                report.completeness_score = max(0, critical_metrics_score - (completeness_issues * 10))

            # Add issue if completeness score is too low
            if report.completeness_score < min_completeness:
                self._add_issue(
                    report, ValidationCategory.DATA_COMPLETENESS, ValidationSeverity.WARNING,
                    f"Overall data completeness below threshold",
                    f"Completeness score: {report.completeness_score:.1f}%, minimum: {min_completeness:.1f}%",
                    critical_metrics,
                    "Improve data collection and ensure all required metrics are captured"
                )

            if completeness_issues == 0:
                report.passed_checks.append("Data completeness validation")

            report.total_checks_performed += 1

        except Exception as e:
            logger.error(f"Error in data completeness validation: {e}")
            self._add_issue(
                report, ValidationCategory.DATA_COMPLETENESS, ValidationSeverity.ERROR,
                "Data completeness validation failed",
                f"Validation error: {str(e)}",
                [], "Review data structure for completeness requirements"
            )

    def _extract_metric_values(self, statement_data: Dict[str, Any], metric_name: str) -> Optional[List]:
        """Extract values for a specific metric from statement data"""
        # Try exact match first
        if metric_name in statement_data:
            return statement_data[metric_name]

        # Try partial match
        for key, values in statement_data.items():
            if metric_name.lower() in key.lower():
                return values

        return None

    def _find_metric_in_statements(self, financial_data: Dict[str, Any], metric_name: str) -> Optional[List]:
        """Find a metric in any of the financial statements"""
        for statement_name, statement_data in financial_data.items():
            if statement_data:
                values = self._extract_metric_values(statement_data, metric_name)
                if values:
                    return values
        return None

    def _add_issue(
        self,
        report: FinancialStatementValidationReport,
        category: ValidationCategory,
        severity: ValidationSeverity,
        message: str,
        details: str,
        affected_metrics: List[str],
        suggested_fix: str,
        confidence_score: float = 1.0
    ):
        """Add a validation issue to the report"""
        issue = ValidationIssue(
            category=category,
            severity=severity,
            message=message,
            details=details,
            affected_metrics=affected_metrics,
            suggested_fix=suggested_fix,
            confidence_score=confidence_score
        )
        report.issues_found.append(issue)

        # Log the issue
        if severity == ValidationSeverity.CRITICAL:
            logger.critical(f"CRITICAL: {message} - {details}")
        elif severity == ValidationSeverity.ERROR:
            logger.error(f"ERROR: {message} - {details}")
        elif severity == ValidationSeverity.WARNING:
            logger.warning(f"WARNING: {message} - {details}")
        else:
            logger.info(f"INFO: {message} - {details}")

    def _calculate_overall_score(self, report: FinancialStatementValidationReport):
        """Calculate the overall validation score"""
        # Weight the different category scores
        weights = {
            'balance_sheet': 0.20,
            'cash_flow': 0.15,
            'income_statement': 0.15,
            'cross_period': 0.20,
            'business_rules': 0.15,
            'completeness': 0.15
        }

        weighted_score = (
            report.balance_sheet_score * weights['balance_sheet'] +
            report.cash_flow_score * weights['cash_flow'] +
            report.income_statement_score * weights['income_statement'] +
            report.cross_period_score * weights['cross_period'] +
            report.business_rules_score * weights['business_rules'] +
            report.completeness_score * weights['completeness']
        )

        # Apply penalty for critical issues
        critical_issues = len(report.get_issues_by_severity(ValidationSeverity.CRITICAL))
        error_issues = len(report.get_issues_by_severity(ValidationSeverity.ERROR))

        # Reduce score based on severity of issues
        penalty = (critical_issues * 20) + (error_issues * 10)

        report.overall_score = max(0, min(100, weighted_score - penalty))


# Export the main validator class
__all__ = [
    'EnhancedFinancialStatementValidator',
    'FinancialStatementValidationReport',
    'ValidationIssue',
    'ValidationSeverity',
    'ValidationCategory'
]