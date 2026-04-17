"""
Financial Metric Validators - Comprehensive Data Quality Checks

This module provides specialized validators for financial metrics, ensuring
data quality, consistency, and business rule compliance for financial calculations.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from utils.error_handler import EnhancedLogger, ValidationError
from ..data_processing.data_validator import DataQualityReport


class MetricCategory(Enum):
    """Categories of financial metrics"""
    
    PROFITABILITY = "profitability"       # Net Income, ROE, ROA, etc.
    LIQUIDITY = "liquidity"               # Current Ratio, Quick Ratio, etc.
    LEVERAGE = "leverage"                 # Debt ratios, Coverage ratios
    EFFICIENCY = "efficiency"             # Turnover ratios, Asset utilization
    GROWTH = "growth"                     # Revenue growth, Earnings growth
    VALUATION = "valuation"               # P/E, P/B, EV/EBITDA
    CASH_FLOW = "cash_flow"               # Operating CF, Free CF, etc.
    BALANCE_SHEET = "balance_sheet"       # Assets, Liabilities, Equity
    INCOME_STATEMENT = "income_statement" # Revenue, Expenses, Margins


@dataclass
class MetricValidationRule:
    """Validation rule for a specific financial metric"""
    
    metric_name: str
    category: MetricCategory
    
    # Validation thresholds
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_years_required: int = 3
    
    # Quality checks
    allow_negative: bool = True
    allow_zero: bool = True
    require_increasing_trend: bool = False
    require_positive_trend: bool = False
    
    # Outlier detection
    outlier_threshold_std: float = 3.0  # Standard deviations
    max_year_over_year_change: float = 5.0  # 500% maximum change
    
    # Business logic
    seasonal_adjustment: bool = False
    currency_adjustment: bool = False
    inflation_adjustment: bool = False
    
    # Cross-metric relationships
    related_metrics: List[str] = field(default_factory=list)
    inverse_relationship: List[str] = field(default_factory=list)
    ratio_components: List[str] = field(default_factory=list)


@dataclass
class MetricValidationResult:
    """Result of metric validation"""
    
    metric_name: str
    is_valid: bool
    quality_score: float  # 0-100
    
    # Validation details (set after construction)
    values_validated: int = 0
    missing_values: int = 0
    outliers_detected: int = 0
    trend_issues: int = 0
    
    # Specific findings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Statistical summary
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_deviation: Optional[float] = None
    coefficient_of_variation: Optional[float] = None
    
    # Trend analysis
    trend_direction: Optional[str] = None  # 'increasing', 'decreasing', 'stable', 'volatile'
    compound_annual_growth_rate: Optional[float] = None
    
    # Metadata
    validation_timestamp: datetime = field(default_factory=datetime.now)


class FinancialMetricValidator:
    """
    Comprehensive validator for financial metrics with business rule compliance
    """
    
    def __init__(self):
        self.logger = EnhancedLogger(__name__)
        self.validation_rules: Dict[str, MetricValidationRule] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default validation rules for common financial metrics"""
        
        # Revenue validation
        self.validation_rules['Revenue'] = MetricValidationRule(
            metric_name='Revenue',
            category=MetricCategory.INCOME_STATEMENT,
            min_value=0,  # Revenue should be positive
            allow_negative=False,
            allow_zero=False,
            max_year_over_year_change=2.0,  # 200% max growth
            require_positive_trend=False  # Can be declining
        )
        
        # Net Income validation
        self.validation_rules['Net Income'] = MetricValidationRule(
            metric_name='Net Income',
            category=MetricCategory.PROFITABILITY,
            allow_negative=True,  # Companies can have losses
            allow_zero=True,
            max_year_over_year_change=10.0,  # Can be very volatile
            related_metrics=['Revenue', 'EBIT', 'EBT']
        )
        
        # EBIT validation
        self.validation_rules['EBIT'] = MetricValidationRule(
            metric_name='EBIT',
            category=MetricCategory.PROFITABILITY,
            allow_negative=True,
            max_year_over_year_change=5.0,
            related_metrics=['Revenue', 'Net Income']
        )
        
        # Cash from Operations validation
        self.validation_rules['Cash from Operations'] = MetricValidationRule(
            metric_name='Cash from Operations',
            category=MetricCategory.CASH_FLOW,
            allow_negative=True,  # Can be negative in some periods
            max_year_over_year_change=3.0,
            related_metrics=['Net Income']
        )
        
        # Capital Expenditure validation
        self.validation_rules['Capital Expenditure'] = MetricValidationRule(
            metric_name='Capital Expenditure',
            category=MetricCategory.CASH_FLOW,
            max_value=0,  # CapEx is typically reported as negative
            allow_negative=True,
            allow_zero=True,
            max_year_over_year_change=2.0
        )
        
        # Total Current Assets validation
        self.validation_rules['Total Current Assets'] = MetricValidationRule(
            metric_name='Total Current Assets',
            category=MetricCategory.BALANCE_SHEET,
            min_value=0,
            allow_negative=False,
            max_year_over_year_change=1.5,
            related_metrics=['Total Assets']
        )
        
        # Total Current Liabilities validation
        self.validation_rules['Total Current Liabilities'] = MetricValidationRule(
            metric_name='Total Current Liabilities',
            category=MetricCategory.BALANCE_SHEET,
            min_value=0,
            allow_negative=False,
            max_year_over_year_change=2.0,
            related_metrics=['Total Liabilities']
        )
        
        # Depreciation & Amortization validation
        self.validation_rules['Depreciation & Amortization'] = MetricValidationRule(
            metric_name='Depreciation & Amortization',
            category=MetricCategory.CASH_FLOW,
            min_value=0,
            allow_negative=False,
            max_year_over_year_change=1.5
        )
    
    def add_validation_rule(self, rule: MetricValidationRule):
        """Add a custom validation rule"""
        self.validation_rules[rule.metric_name] = rule
        self.logger.info(f"Added validation rule for {rule.metric_name}")
    
    def validate_metric(
        self, 
        metric_name: str, 
        values: List[float], 
        years: List[int] = None
    ) -> MetricValidationResult:
        """
        Validate a specific financial metric
        
        Args:
            metric_name: Name of the metric
            values: List of metric values over time
            years: Corresponding years (optional)
            
        Returns:
            MetricValidationResult with validation details
        """
        self.logger.info(f"Validating metric: {metric_name}")
        
        # Get validation rule
        rule = self.validation_rules.get(metric_name)
        if not rule:
            self.logger.warning(f"No validation rule found for {metric_name}, using defaults")
            rule = MetricValidationRule(
                metric_name=metric_name,
                category=MetricCategory.INCOME_STATEMENT  # Default category
            )
        
        # Initialize result
        result = MetricValidationResult(
            metric_name=metric_name,
            is_valid=True,
            quality_score=100.0
        )
        
        # Basic data validation
        if not values or len(values) == 0:
            result.is_valid = False
            result.quality_score = 0.0
            result.errors.append(f"No data available for {metric_name}")
            return result
        
        # Convert to numpy array for calculations
        clean_values = []
        missing_count = 0
        
        for i, value in enumerate(values):
            if pd.isna(value) or value is None:
                missing_count += 1
                if not rule.allow_zero:
                    result.warnings.append(f"Missing value at position {i}")
            else:
                try:
                    clean_value = float(value)
                    clean_values.append(clean_value)
                except (ValueError, TypeError):
                    result.errors.append(f"Invalid value at position {i}: {value}")
                    missing_count += 1
        
        result.missing_values = missing_count
        result.values_validated = len(clean_values)
        
        if len(clean_values) < rule.min_years_required:
            result.is_valid = False
            result.errors.append(
                f"Insufficient data: {len(clean_values)} years, minimum {rule.min_years_required} required"
            )
        
        if not clean_values:
            result.quality_score = 0.0
            return result
        
        # Statistical calculations
        values_array = np.array(clean_values)
        result.mean_value = float(np.mean(values_array))
        result.median_value = float(np.median(values_array))
        result.std_deviation = float(np.std(values_array))
        
        if result.mean_value != 0:
            result.coefficient_of_variation = result.std_deviation / abs(result.mean_value)
        
        # Value range validation
        self._validate_value_ranges(result, clean_values, rule)
        
        # Outlier detection
        self._detect_outliers(result, clean_values, rule)
        
        # Trend analysis
        self._analyze_trends(result, clean_values, rule)
        
        # Year-over-year change validation
        if len(clean_values) > 1:
            self._validate_yoy_changes(result, clean_values, rule)
        
        # Calculate final quality score
        result.quality_score = self._calculate_quality_score(result, rule)
        
        self.logger.info(
            f"Metric validation completed: {metric_name}, "
            f"Score: {result.quality_score:.1f}, Valid: {result.is_valid}"
        )
        
        return result
    
    def _validate_value_ranges(self, result: MetricValidationResult, values: List[float], rule: MetricValidationRule):
        """Validate values are within acceptable ranges"""
        for i, value in enumerate(values):
            # Check minimum value
            if rule.min_value is not None and value < rule.min_value:
                result.errors.append(f"Value below minimum at position {i}: {value} < {rule.min_value}")
                result.is_valid = False
            
            # Check maximum value
            if rule.max_value is not None and value > rule.max_value:
                result.errors.append(f"Value above maximum at position {i}: {value} > {rule.max_value}")
                result.is_valid = False
            
            # Check negative values
            if not rule.allow_negative and value < 0:
                result.warnings.append(f"Negative value detected at position {i}: {value}")
            
            # Check zero values
            if not rule.allow_zero and value == 0:
                result.warnings.append(f"Zero value detected at position {i}")
    
    def _detect_outliers(self, result: MetricValidationResult, values: List[float], rule: MetricValidationRule):
        """Detect statistical outliers in the data"""
        if len(values) < 3:
            return
        
        values_array = np.array(values)
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)
        
        if std_val == 0:
            return  # No variation in data
        
        outlier_count = 0
        for i, value in enumerate(values):
            z_score = abs(value - mean_val) / std_val
            if z_score > rule.outlier_threshold_std:
                result.warnings.append(f"Statistical outlier at position {i}: {value} (z-score: {z_score:.2f})")
                outlier_count += 1
        
        result.outliers_detected = outlier_count
    
    def _analyze_trends(self, result: MetricValidationResult, values: List[float], rule: MetricValidationRule):
        """Analyze trends in the data"""
        if len(values) < 2:
            return
        
        # Calculate compound annual growth rate (CAGR)
        first_value = values[0]
        last_value = values[-1]
        periods = len(values) - 1
        
        if first_value > 0 and last_value > 0:
            cagr = ((last_value / first_value) ** (1 / periods)) - 1
            result.compound_annual_growth_rate = cagr
        
        # Determine trend direction
        increasing_periods = 0
        decreasing_periods = 0
        
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increasing_periods += 1
            elif values[i] < values[i-1]:
                decreasing_periods += 1
        
        total_periods = len(values) - 1
        if increasing_periods > 0.7 * total_periods:
            result.trend_direction = 'increasing'
        elif decreasing_periods > 0.7 * total_periods:
            result.trend_direction = 'decreasing'
        elif result.coefficient_of_variation and result.coefficient_of_variation > 0.3:
            result.trend_direction = 'volatile'
        else:
            result.trend_direction = 'stable'
        
        # Check trend requirements
        if rule.require_increasing_trend and result.trend_direction != 'increasing':
            result.warnings.append(f"Expected increasing trend but found {result.trend_direction}")
        
        if rule.require_positive_trend and result.compound_annual_growth_rate and result.compound_annual_growth_rate < 0:
            result.warnings.append(f"Expected positive growth but CAGR is {result.compound_annual_growth_rate:.2%}")
    
    def _validate_yoy_changes(self, result: MetricValidationResult, values: List[float], rule: MetricValidationRule):
        """Validate year-over-year changes"""
        excessive_changes = 0
        
        for i in range(1, len(values)):
            if values[i-1] != 0:
                yoy_change = abs((values[i] - values[i-1]) / values[i-1])
                if yoy_change > rule.max_year_over_year_change:
                    result.warnings.append(
                        f"Excessive YoY change between positions {i-1} and {i}: "
                        f"{yoy_change:.1%} (max: {rule.max_year_over_year_change:.1%})"
                    )
                    excessive_changes += 1
        
        if excessive_changes > len(values) * 0.3:  # More than 30% of periods have excessive changes
            result.warnings.append("High volatility detected: multiple periods with excessive changes")
    
    def _calculate_quality_score(self, result: MetricValidationResult, rule: MetricValidationRule) -> float:
        """Calculate overall quality score for the metric"""
        base_score = 100.0
        
        # Deduct for errors (severe impact)
        base_score -= len(result.errors) * 20
        
        # Deduct for warnings (moderate impact)
        base_score -= len(result.warnings) * 5
        
        # Deduct for missing values
        if result.values_validated > 0:
            missing_percentage = result.missing_values / (result.values_validated + result.missing_values)
            base_score -= missing_percentage * 30
        
        # Deduct for outliers
        if result.values_validated > 0:
            outlier_percentage = result.outliers_detected / result.values_validated
            base_score -= outlier_percentage * 15
        
        # Bonus for sufficient data
        if result.values_validated >= rule.min_years_required * 2:
            base_score += 5  # Bonus for having plenty of data
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, base_score))
    
    def validate_metric_relationships(
        self, 
        metrics: Dict[str, List[float]]
    ) -> Dict[str, List[str]]:
        """
        Validate relationships between related metrics
        
        Args:
            metrics: Dictionary of metric names to their values
            
        Returns:
            Dictionary of metric names to relationship validation issues
        """
        relationship_issues = {}
        
        for metric_name, values in metrics.items():
            rule = self.validation_rules.get(metric_name)
            if not rule or not rule.related_metrics:
                continue
            
            issues = []
            
            # Check relationships with related metrics
            for related_metric in rule.related_metrics:
                if related_metric not in metrics:
                    issues.append(f"Related metric '{related_metric}' not available for validation")
                    continue
                
                related_values = metrics[related_metric]
                
                # Perform relationship-specific validations
                issues.extend(self._validate_specific_relationships(
                    metric_name, values, related_metric, related_values
                ))
            
            if issues:
                relationship_issues[metric_name] = issues
        
        return relationship_issues
    
    def _validate_specific_relationships(
        self,
        metric1: str,
        values1: List[float],
        metric2: str,
        values2: List[float]
    ) -> List[str]:
        """Validate specific relationships between two metrics"""
        issues = []
        
        # Net Income should generally be less than Revenue
        if metric1 == "Net Income" and metric2 == "Revenue":
            for i, (ni, rev) in enumerate(zip(values1, values2)):
                if ni > rev and ni > 0 and rev > 0:
                    issues.append(f"Net Income exceeds Revenue at position {i}: {ni} > {rev}")
        
        # EBIT should generally be between Net Income and Revenue
        if metric1 == "EBIT" and metric2 == "Net Income":
            for i, (ebit, ni) in enumerate(zip(values1, values2)):
                if ebit < ni and ebit > 0 and ni > 0:
                    issues.append(f"EBIT less than Net Income at position {i}: {ebit} < {ni}")
        
        # Cash from Operations vs Net Income correlation
        if (metric1 == "Cash from Operations" and metric2 == "Net Income") or \
           (metric1 == "Net Income" and metric2 == "Cash from Operations"):
            
            # Calculate correlation if enough data points
            if len(values1) >= 3 and len(values2) >= 3:
                try:
                    correlation = np.corrcoef(values1[:min(len(values1), len(values2))], 
                                           values2[:min(len(values1), len(values2))])[0, 1]
                    if abs(correlation) < 0.3:
                        issues.append(f"Low correlation between {metric1} and {metric2}: {correlation:.2f}")
                except:
                    pass  # Skip if correlation calculation fails
        
        return issues
    
    def generate_comprehensive_report(
        self, 
        metrics: Dict[str, List[float]]
    ) -> DataQualityReport:
        """
        Generate comprehensive validation report for all metrics
        
        Args:
            metrics: Dictionary of metric names to their values
            
        Returns:
            DataQualityReport with comprehensive validation results
        """
        report = DataQualityReport()
        
        # Validate each metric individually
        metric_results = {}
        total_quality_score = 0.0
        valid_metrics = 0
        
        for metric_name, values in metrics.items():
            result = self.validate_metric(metric_name, values)
            metric_results[metric_name] = result
            
            # Add errors and warnings to report
            for error in result.errors:
                report.add_error(f"{metric_name}: {error}", context=metric_name)
            
            for warning in result.warnings:
                report.add_warning(f"{metric_name}: {warning}", context=metric_name)
            
            # Add suggestions as recommendations
            for suggestion in result.suggestions:
                report.add_recommendation(f"{metric_name}: {suggestion}")
            
            if result.is_valid:
                total_quality_score += result.quality_score
                valid_metrics += 1
        
        # Validate metric relationships
        relationship_issues = self.validate_metric_relationships(metrics)
        for metric_name, issues in relationship_issues.items():
            for issue in issues:
                report.add_warning(f"Relationship issue - {metric_name}: {issue}", context="relationships")
        
        # Calculate overall scores
        if valid_metrics > 0:
            report.completeness_score = (valid_metrics / len(metrics)) * 100
            report.consistency_score = total_quality_score / valid_metrics
        else:
            report.completeness_score = 0.0
            report.consistency_score = 0.0
        
        report.overall_score = (report.completeness_score * 0.4) + (report.consistency_score * 0.6)
        
        # Add summary recommendation
        if report.overall_score < 70:
            report.add_recommendation(
                "Overall data quality is below acceptable threshold. "
                "Review data sources and collection processes.",
                priority="high"
            )
        
        return report


if __name__ == "__main__":
    # Example usage
    print("=== Financial Metric Validator Test ===")
    
    # Create validator
    validator = FinancialMetricValidator()
    
    # Test data
    test_metrics = {
        'Revenue': [1000, 1100, 1200, 1300, 1450],
        'Net Income': [100, 110, 90, 130, 145],
        'Cash from Operations': [120, 125, 110, 140, 150],
        'Capital Expenditure': [-50, -55, -60, -52, -58]
    }
    
    # Validate each metric
    print("\n=== Individual Metric Validation ===")
    for metric_name, values in test_metrics.items():
        result = validator.validate_metric(metric_name, values)
        print(f"\n{metric_name}:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Quality Score: {result.quality_score:.1f}")
        print(f"  Trend: {result.trend_direction}")
        print(f"  CAGR: {result.compound_annual_growth_rate:.2%}" if result.compound_annual_growth_rate else "  CAGR: N/A")
        
        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")
    
    # Generate comprehensive report
    print("\n=== Comprehensive Report ===")
    report = validator.generate_comprehensive_report(test_metrics)
    print(report.get_summary())
    
    print("\n=== Test Complete ===")