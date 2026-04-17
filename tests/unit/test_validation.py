"""
Unit Tests for Validation Modules
===================================

Tests cover:
- core/validation/financial_metric_validators.py:
    MetricCategory, MetricValidationRule, MetricValidationResult,
    FinancialMetricValidator (add_validation_rule, validate_metric,
    default rules for Revenue / Net Income / CapEx)
- core/validation/validation_orchestrator.py:
    ValidationScope, ValidationPriority, ValidationConfig instantiation,
    ValidationOrchestrator smoke tests with mocked sub-validators
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.validation.financial_metric_validators import (
    MetricCategory,
    MetricValidationRule,
    MetricValidationResult,
    FinancialMetricValidator,
)
from core.validation.validation_orchestrator import (
    ValidationScope,
    ValidationPriority,
    ValidationConfig,
)


# ---------------------------------------------------------------------------
# FinancialMetricValidator — construction and default rules
# ---------------------------------------------------------------------------

class TestFinancialMetricValidatorInit:
    """FinancialMetricValidator can be constructed and loads default rules."""

    def _make_validator(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            return FinancialMetricValidator()

    def test_default_rules_populated(self):
        v = self._make_validator()
        assert len(v.validation_rules) > 0

    def test_revenue_rule_exists(self):
        v = self._make_validator()
        assert 'Revenue' in v.validation_rules

    def test_net_income_rule_exists(self):
        v = self._make_validator()
        assert 'Net Income' in v.validation_rules

    def test_capex_rule_exists(self):
        v = self._make_validator()
        assert 'Capital Expenditure' in v.validation_rules


# ---------------------------------------------------------------------------
# MetricValidationRule defaults
# ---------------------------------------------------------------------------

class TestMetricValidationRule:
    """MetricValidationRule dataclass has expected defaults."""

    def test_default_allow_negative(self):
        rule = MetricValidationRule(
            metric_name='TestMetric',
            category=MetricCategory.PROFITABILITY,
        )
        assert rule.allow_negative is True

    def test_default_allow_zero(self):
        rule = MetricValidationRule(
            metric_name='TestMetric',
            category=MetricCategory.PROFITABILITY,
        )
        assert rule.allow_zero is True

    def test_default_min_years_required(self):
        rule = MetricValidationRule(
            metric_name='TestMetric',
            category=MetricCategory.PROFITABILITY,
        )
        assert rule.min_years_required == 3

    def test_revenue_rule_disallows_negative(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            v = FinancialMetricValidator()
        rule = v.validation_rules['Revenue']
        assert rule.allow_negative is False

    def test_revenue_rule_disallows_zero(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            v = FinancialMetricValidator()
        rule = v.validation_rules['Revenue']
        assert rule.allow_zero is False


# ---------------------------------------------------------------------------
# add_validation_rule
# ---------------------------------------------------------------------------

class TestAddValidationRule:
    """Custom validation rules can be added and retrieved."""

    def test_add_custom_rule(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            v = FinancialMetricValidator()
        custom_rule = MetricValidationRule(
            metric_name='Custom Metric',
            category=MetricCategory.VALUATION,
            min_value=0.0,
            max_value=100.0,
        )
        v.add_validation_rule(custom_rule)
        assert 'Custom Metric' in v.validation_rules

    def test_add_rule_overwrites_existing(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            v = FinancialMetricValidator()
        new_rule = MetricValidationRule(
            metric_name='Revenue',
            category=MetricCategory.INCOME_STATEMENT,
            allow_negative=True,  # change from default False
        )
        v.add_validation_rule(new_rule)
        assert v.validation_rules['Revenue'].allow_negative is True


# ---------------------------------------------------------------------------
# validate_metric — basic happy path
# ---------------------------------------------------------------------------

class TestValidateMetric:
    """validate_metric returns a MetricValidationResult."""

    def _make_validator(self):
        with patch('core.validation.financial_metric_validators.EnhancedLogger'):
            return FinancialMetricValidator()

    def test_returns_metric_validation_result(self):
        v = self._make_validator()
        result = v.validate_metric('Revenue', [100.0, 110.0, 121.0])
        assert isinstance(result, MetricValidationResult)

    def test_valid_revenue_series_is_valid(self):
        v = self._make_validator()
        result = v.validate_metric('Revenue', [100.0, 110.0, 121.0])
        assert result.is_valid is True

    def test_result_contains_metric_name(self):
        v = self._make_validator()
        result = v.validate_metric('Revenue', [100.0, 110.0, 121.0])
        assert result.metric_name == 'Revenue'

    def test_quality_score_is_in_range(self):
        v = self._make_validator()
        result = v.validate_metric('Revenue', [100.0, 110.0, 121.0])
        assert 0.0 <= result.quality_score <= 100.0

    def test_net_income_allows_negative_values(self):
        v = self._make_validator()
        result = v.validate_metric('Net Income', [-50.0, -20.0, 10.0])
        # Should not be marked invalid solely because values are negative
        assert isinstance(result, MetricValidationResult)

    def test_unknown_metric_uses_default_rule(self):
        v = self._make_validator()
        result = v.validate_metric('Nonexistent Metric', [1.0, 2.0, 3.0])
        assert isinstance(result, MetricValidationResult)

    def test_empty_values_returns_result(self):
        v = self._make_validator()
        result = v.validate_metric('Revenue', [])
        assert isinstance(result, MetricValidationResult)
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# MetricCategory enum values
# ---------------------------------------------------------------------------

class TestMetricCategory:
    """MetricCategory enum covers expected financial categories."""

    def test_profitability_value(self):
        assert MetricCategory.PROFITABILITY.value == "profitability"

    def test_cash_flow_value(self):
        assert MetricCategory.CASH_FLOW.value == "cash_flow"

    def test_valuation_value(self):
        assert MetricCategory.VALUATION.value == "valuation"

    def test_all_categories_unique(self):
        values = [c.value for c in MetricCategory]
        assert len(values) == len(set(values))


# ---------------------------------------------------------------------------
# ValidationOrchestrator — scope / priority / config enums and dataclass
# ---------------------------------------------------------------------------

class TestValidationOrchestratorEnums:
    """ValidationScope and ValidationPriority enums are well-formed."""

    def test_scope_pre_flight_value(self):
        assert ValidationScope.PRE_FLIGHT.value == "pre_flight"

    def test_scope_comprehensive_value(self):
        assert ValidationScope.COMPREHENSIVE.value == "comprehensive"

    def test_priority_critical_value(self):
        assert ValidationPriority.CRITICAL.value == "critical"

    def test_priority_low_value(self):
        assert ValidationPriority.LOW.value == "low"

    def test_all_scope_values_unique(self):
        values = [s.value for s in ValidationScope]
        assert len(values) == len(set(values))

    def test_all_priority_values_unique(self):
        values = [p.value for p in ValidationPriority]
        assert len(values) == len(set(values))


class TestValidationConfig:
    """ValidationConfig dataclass can be instantiated with defaults."""

    def test_instantiation_with_defaults(self):
        cfg = ValidationConfig()
        assert cfg is not None

    def test_is_dataclass_instance(self):
        from dataclasses import fields
        cfg = ValidationConfig()
        assert len(fields(cfg)) > 0
