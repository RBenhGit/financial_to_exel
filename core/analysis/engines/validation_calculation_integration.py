"""
Validation-Calculation Integration Module

This module provides seamless integration between the validation framework and
the financial calculation engines, ensuring all calculations are performed on
validated, high-quality data with comprehensive error handling.
"""

from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import functools

from error_handler import EnhancedLogger, ValidationError, CalculationError, with_error_handling
from validation_orchestrator import ValidationOrchestrator, ValidationConfig, ValidationScope, ValidationResult
from financial_metric_validators import FinancialMetricValidator, MetricValidationResult
from testing_validation_framework import TestingValidationFramework, get_testing_framework
from validation_registry import get_validation_registry
from financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class CalculationValidationLevel(Enum):
    """Levels of validation to apply before calculations"""
    
    NONE = "none"                    # No validation
    BASIC = "basic"                  # Basic input validation only
    STANDARD = "standard"            # Standard validation with metrics
    COMPREHENSIVE = "comprehensive"  # Full validation including testing framework
    STRICT = "strict"                # Strictest validation with all checks


@dataclass
class ValidatedCalculationResult:
    """Result container for validated calculations"""
    
    # Calculation results
    calculation_result: CalculationResult
    
    # Validation information
    validation_passed: bool
    validation_result: Optional[ValidationResult] = None
    pre_calculation_validation: Optional[Dict[str, Any]] = None
    post_calculation_validation: Optional[Dict[str, Any]] = None
    
    # Quality metrics
    input_quality_score: float = 0.0
    output_quality_score: float = 0.0
    overall_confidence: float = 0.0
    
    # Metadata
    validation_level: CalculationValidationLevel = CalculationValidationLevel.STANDARD
    calculation_timestamp: datetime = field(default_factory=datetime.now)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    
    # Issues and recommendations
    validation_warnings: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    quality_recommendations: List[str] = field(default_factory=list)


class ValidatedFinancialCalculationEngine:
    """
    Enhanced financial calculation engine with integrated validation
    
    This class wraps the pure FinancialCalculationEngine with comprehensive
    validation capabilities, ensuring all calculations are performed on
    high-quality, validated data.
    """
    
    def __init__(
        self,
        validation_level: CalculationValidationLevel = CalculationValidationLevel.STANDARD,
        strict_mode: bool = False,
        auto_remediation: bool = False
    ):
        """
        Initialize the validated calculation engine
        
        Args:
            validation_level: Level of validation to apply
            strict_mode: Whether to fail on validation warnings
            auto_remediation: Whether to attempt automatic data remediation
        """
        self.logger = EnhancedLogger(__name__)
        
        # Core components
        self.calculation_engine = FinancialCalculationEngine()
        self.validation_orchestrator = ValidationOrchestrator()
        self.metric_validator = FinancialMetricValidator()
        self.testing_framework = get_testing_framework()
        self.validation_registry = get_validation_registry()
        
        # Configuration
        self.validation_level = validation_level
        self.strict_mode = strict_mode
        self.auto_remediation = auto_remediation
        
        # Calculation history for trend analysis
        self.calculation_history: List[ValidatedCalculationResult] = []
        
        # Performance metrics
        self.performance_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'validation_failures': 0,
            'calculation_failures': 0,
            'average_validation_time_ms': 0.0,
            'average_calculation_time_ms': 0.0
        }
        
        self.logger.info(f"Initialized ValidatedFinancialCalculationEngine with validation level: {validation_level.value}")
    
    def validate_calculation_inputs(
        self,
        input_data: Dict[str, Any],
        calculation_type: str,
        metadata: Dict[str, Any] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate inputs before performing financial calculations
        
        Args:
            input_data: Dictionary of input data for calculation
            calculation_type: Type of calculation being performed
            metadata: Additional metadata about the calculation
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        validation_start = datetime.now()
        validation_details = {
            'validation_level': self.validation_level.value,
            'calculation_type': calculation_type,
            'validation_timestamp': validation_start.isoformat(),
            'input_metrics': {},
            'validation_results': {},
            'quality_scores': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Skip validation if level is NONE
            if self.validation_level == CalculationValidationLevel.NONE:
                validation_details['validation_skipped'] = True
                return True, validation_details
            
            # Basic input validation
            if not self._validate_basic_inputs(input_data, validation_details):
                return False, validation_details
            
            # Testing framework validation (metadata usage check)
            if self.validation_level in [CalculationValidationLevel.COMPREHENSIVE, CalculationValidationLevel.STRICT]:
                testing_valid, testing_issues = self._validate_testing_compliance(input_data, metadata)
                validation_details['testing_validation'] = {
                    'is_valid': testing_valid,
                    'issues': testing_issues
                }
                
                if not testing_valid and self.validation_level == CalculationValidationLevel.STRICT:
                    validation_details['issues'].extend(testing_issues)
                    return False, validation_details
            
            # Metric-level validation
            if self.validation_level in [CalculationValidationLevel.STANDARD, CalculationValidationLevel.COMPREHENSIVE, CalculationValidationLevel.STRICT]:
                metric_validation_results = self._validate_financial_metrics(input_data, validation_details)
                validation_details['metric_validation'] = metric_validation_results
                
                # Check if metric validation passed
                failed_metrics = [
                    metric for metric, result in metric_validation_results.items()
                    if isinstance(result, dict) and not result.get('is_valid', True)
                ]
                
                if failed_metrics:
                    validation_details['issues'].append(f"Failed metric validation: {', '.join(failed_metrics)}")
                    if self.strict_mode or self.validation_level == CalculationValidationLevel.STRICT:
                        return False, validation_details
            
            # Comprehensive validation using orchestrator
            if self.validation_level in [CalculationValidationLevel.COMPREHENSIVE, CalculationValidationLevel.STRICT]:
                orchestrator_result = self._perform_comprehensive_validation(input_data, metadata)
                validation_details['comprehensive_validation'] = {
                    'is_valid': orchestrator_result.is_valid,
                    'quality_score': orchestrator_result.total_errors + orchestrator_result.total_warnings,
                    'execution_time_ms': orchestrator_result.execution_time_ms
                }
                
                if not orchestrator_result.is_valid and self.validation_level == CalculationValidationLevel.STRICT:
                    validation_details['issues'].extend(orchestrator_result.critical_failures)
                    return False, validation_details
            
            # Calculate overall validation time
            validation_end = datetime.now()
            validation_details['validation_time_ms'] = (validation_end - validation_start).total_seconds() * 1000
            
            # Determine overall validation status
            has_critical_issues = any(
                'critical' in issue.lower() or 'error' in issue.lower()
                for issue in validation_details['issues']
            )
            
            is_valid = not has_critical_issues
            
            if not is_valid and self.auto_remediation:
                is_valid = self._attempt_auto_remediation(input_data, validation_details)
            
            self.logger.info(
                f"Input validation completed for {calculation_type}: {'PASSED' if is_valid else 'FAILED'}",
                context={
                    'validation_time_ms': validation_details['validation_time_ms'],
                    'issues_count': len(validation_details['issues'])
                }
            )
            
            return is_valid, validation_details
            
        except Exception as e:
            self.logger.error(f"Input validation failed with exception: {str(e)}", error=e)
            validation_details['validation_exception'] = str(e)
            return False, validation_details
    
    def perform_validated_calculation(
        self,
        calculation_function: Callable,
        input_data: Dict[str, Any],
        calculation_type: str,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> ValidatedCalculationResult:
        """
        Perform a financial calculation with comprehensive validation
        
        Args:
            calculation_function: The calculation function to execute
            input_data: Input data for the calculation
            calculation_type: Type of calculation being performed
            metadata: Additional metadata
            **kwargs: Additional arguments for the calculation function
            
        Returns:
            ValidatedCalculationResult with calculation and validation information
        """
        calculation_start = datetime.now()
        
        # Initialize result container
        result = ValidatedCalculationResult(
            calculation_result=CalculationResult(value=None, is_valid=False),
            validation_passed=False,
            validation_level=self.validation_level,
            calculation_timestamp=calculation_start
        )
        
        try:
            # Update performance stats
            self.performance_stats['total_calculations'] += 1
            
            # Pre-calculation validation
            validation_passed, validation_details = self.validate_calculation_inputs(
                input_data, calculation_type, metadata
            )
            
            result.pre_calculation_validation = validation_details
            result.validation_passed = validation_passed
            result.input_quality_score = self._calculate_input_quality_score(validation_details)
            
            # Extract validation issues
            result.validation_errors = [
                issue for issue in validation_details.get('issues', [])
                if 'error' in issue.lower() or 'critical' in issue.lower()
            ]
            result.validation_warnings = [
                issue for issue in validation_details.get('issues', [])
                if 'warning' in issue.lower() and issue not in result.validation_errors
            ]
            
            # Proceed with calculation if validation passed or not in strict mode
            if validation_passed or (not self.strict_mode and self.validation_level != CalculationValidationLevel.STRICT):
                
                # Log calculation attempt
                self.logger.info(
                    f"Executing {calculation_type} calculation",
                    context={
                        'validation_passed': validation_passed,
                        'input_quality_score': result.input_quality_score
                    }
                )
                
                # Execute the calculation
                calculation_result = self._execute_calculation_safely(
                    calculation_function, input_data, **kwargs
                )
                
                result.calculation_result = calculation_result
                
                # Post-calculation validation
                if calculation_result.is_valid:
                    result.post_calculation_validation = self._validate_calculation_output(
                        calculation_result, calculation_type, input_data
                    )
                    result.output_quality_score = self._calculate_output_quality_score(
                        calculation_result, result.post_calculation_validation
                    )
                    
                    self.performance_stats['successful_calculations'] += 1
                else:
                    self.performance_stats['calculation_failures'] += 1
                    result.validation_errors.append(f"Calculation failed: {calculation_result.error_message}")
            
            else:
                # Validation failed and we're in strict mode
                self.performance_stats['validation_failures'] += 1
                result.calculation_result = CalculationResult(
                    value=None,
                    is_valid=False,
                    error_message="Calculation skipped due to validation failure"
                )
                result.validation_errors.append("Pre-calculation validation failed in strict mode")
            
            # Calculate overall confidence score
            result.overall_confidence = self._calculate_confidence_score(result)
            
            # Generate quality recommendations
            result.quality_recommendations = self._generate_quality_recommendations(result)
            
            # Add to calculation history
            self.calculation_history.append(result)
            
            # Update performance statistics
            calculation_end = datetime.now()
            execution_time = (calculation_end - calculation_start).total_seconds() * 1000
            self._update_performance_stats(execution_time, validation_details.get('validation_time_ms', 0))
            
            self.logger.info(
                f"Validated calculation completed: {calculation_type}",
                context={
                    'success': result.calculation_result.is_valid,
                    'confidence': result.overall_confidence,
                    'execution_time_ms': execution_time
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validated calculation failed: {calculation_type}", error=e)
            result.calculation_result = CalculationResult(
                value=None,
                is_valid=False,
                error_message=f"Calculation exception: {str(e)}"
            )
            result.validation_errors.append(f"Exception during calculation: {str(e)}")
            return result
    
    # Convenience methods for common calculations
    
    @with_error_handling(error_type=CalculationError, return_on_error=None)
    def calculate_validated_fcf(
        self,
        financial_data: Dict[str, List[float]],
        metadata: Dict[str, Any] = None
    ) -> ValidatedCalculationResult:
        """Calculate Free Cash Flow with validation"""
        
        def fcf_calculation(data):
            required_keys = ['EBIT', 'Tax_Rate', 'Depreciation', 'Working_Capital_Change', 'CapEx']
            
            # Extract and validate required data
            ebit_values = data.get('EBIT', [])
            tax_rates = data.get('Tax_Rate', [])
            depreciation = data.get('Depreciation', [])
            wc_changes = data.get('Working_Capital_Change', [])
            capex = data.get('CapEx', [])
            
            return self.calculation_engine.calculate_fcf_to_firm(
                ebit_values, tax_rates, depreciation, wc_changes, capex
            )
        
        return self.perform_validated_calculation(
            fcf_calculation,
            financial_data,
            "Free Cash Flow",
            metadata
        )
    
    @with_error_handling(error_type=CalculationError, return_on_error=None)
    def calculate_validated_dcf(
        self,
        financial_data: Dict[str, List[float]],
        discount_rate: float,
        terminal_growth_rate: float,
        metadata: Dict[str, Any] = None
    ) -> ValidatedCalculationResult:
        """Calculate DCF valuation with validation"""
        
        def dcf_calculation(data):
            fcf_values = data.get('FCF', [])
            return self.calculation_engine.calculate_dcf_valuation(
                fcf_values, discount_rate, terminal_growth_rate
            )
        
        return self.perform_validated_calculation(
            dcf_calculation,
            financial_data,
            "DCF Valuation",
            metadata,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate
        )
    
    # Private helper methods
    
    def _validate_basic_inputs(self, input_data: Dict[str, Any], validation_details: Dict[str, Any]) -> bool:
        """Perform basic input validation"""
        if not input_data:
            validation_details['issues'].append("Input data is empty or None")
            return False
        
        if not isinstance(input_data, dict):
            validation_details['issues'].append("Input data must be a dictionary")
            return False
        
        # Check for required numeric data
        numeric_keys = []
        for key, value in input_data.items():
            if isinstance(value, (list, tuple)):
                if not all(isinstance(item, (int, float)) or item is None for item in value):
                    validation_details['issues'].append(f"Non-numeric values in {key}")
                    return False
                numeric_keys.append(key)
        
        validation_details['input_metrics']['numeric_fields'] = len(numeric_keys)
        validation_details['input_metrics']['total_fields'] = len(input_data)
        
        return True
    
    def _validate_testing_compliance(
        self, 
        input_data: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate testing compliance and metadata usage"""
        issues = []
        
        # Check if we're using test data in production
        for key, value in input_data.items():
            valid, violations = self.testing_framework.validate_metadata_usage(
                key, "calculation_input"
            )
            if not valid:
                issues.extend(violations)
        
        # Validate data structure
        data_valid, data_violations = self.testing_framework.validate_data_structure(
            input_data, "calculation_inputs"
        )
        if not data_valid:
            issues.extend(data_violations)
        
        return len(issues) == 0, issues
    
    def _validate_financial_metrics(
        self, 
        input_data: Dict[str, Any], 
        validation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate financial metrics using the metric validator"""
        metric_results = {}
        
        for metric_name, values in input_data.items():
            if isinstance(values, (list, tuple)) and values:
                # Filter out None values for validation
                clean_values = [v for v in values if v is not None]
                
                if clean_values:
                    result = self.metric_validator.validate_metric(metric_name, clean_values)
                    metric_results[metric_name] = {
                        'is_valid': result.is_valid,
                        'quality_score': result.quality_score,
                        'errors': result.errors,
                        'warnings': result.warnings,
                        'trend_direction': result.trend_direction
                    }
                    
                    # Add to validation details
                    if result.errors:
                        validation_details['issues'].extend([f"{metric_name}: {error}" for error in result.errors])
                    if result.warnings:
                        validation_details['issues'].extend([f"{metric_name}: {warning}" for warning in result.warnings])
        
        return metric_results
    
    def _perform_comprehensive_validation(
        self, 
        input_data: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Perform comprehensive validation using the orchestrator"""
        
        # Configure validation for calculations
        config = ValidationConfig(
            scope=ValidationScope.CALCULATION,
            validation_level=self.validation_registry.validation_level,
            fail_on_priority=self.validation_registry.fail_on_priority if self.strict_mode else None,
            testing_mode=True,  # Enable testing validation
            use_metadata_for_testing=True
        )
        
        orchestrator = ValidationOrchestrator(config)
        
        return orchestrator.validate(
            calculation_inputs=input_data,
            **metadata if metadata else {}
        )
    
    def _execute_calculation_safely(
        self,
        calculation_function: Callable,
        input_data: Dict[str, Any],
        **kwargs
    ) -> CalculationResult:
        """Execute calculation function with error handling"""
        try:
            # Execute the calculation function
            if kwargs:
                return calculation_function(input_data, **kwargs)
            else:
                return calculation_function(input_data)
                
        except Exception as e:
            self.logger.error(f"Calculation execution failed", error=e)
            return CalculationResult(
                value=None,
                is_valid=False,
                error_message=f"Calculation error: {str(e)}"
            )
    
    def _validate_calculation_output(
        self,
        calculation_result: CalculationResult,
        calculation_type: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate calculation output"""
        post_validation = {
            'output_type': type(calculation_result.value).__name__,
            'has_result': calculation_result.value is not None,
            'result_valid': calculation_result.is_valid,
            'issues': []
        }
        
        # Check for reasonable output values
        if calculation_result.is_valid and calculation_result.value is not None:
            if isinstance(calculation_result.value, (int, float)):
                # Check for reasonable ranges
                if abs(calculation_result.value) > 1e15:  # 1 quadrillion
                    post_validation['issues'].append("Output value extremely large, may indicate calculation error")
                
                if calculation_result.value != calculation_result.value:  # NaN check
                    post_validation['issues'].append("Output contains NaN values")
                
                if math.isinf(calculation_result.value):
                    post_validation['issues'].append("Output contains infinite values")
        
        return post_validation
    
    def _calculate_input_quality_score(self, validation_details: Dict[str, Any]) -> float:
        """Calculate quality score for input data"""
        base_score = 100.0
        
        # Deduct for issues
        issues = validation_details.get('issues', [])
        error_count = len([issue for issue in issues if 'error' in issue.lower()])
        warning_count = len([issue for issue in issues if 'warning' in issue.lower()])
        
        base_score -= error_count * 20  # Errors have high impact
        base_score -= warning_count * 5  # Warnings have moderate impact
        
        # Consider metric validation results
        metric_validation = validation_details.get('metric_validation', {})
        if metric_validation:
            metric_scores = [
                result.get('quality_score', 0) 
                for result in metric_validation.values()
                if isinstance(result, dict) and 'quality_score' in result
            ]
            if metric_scores:
                avg_metric_score = sum(metric_scores) / len(metric_scores)
                base_score = (base_score + avg_metric_score) / 2
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_output_quality_score(
        self,
        calculation_result: CalculationResult,
        post_validation: Dict[str, Any]
    ) -> float:
        """Calculate quality score for output data"""
        if not calculation_result.is_valid:
            return 0.0
        
        base_score = 100.0
        
        # Deduct for post-validation issues
        issues = post_validation.get('issues', [])
        base_score -= len(issues) * 15
        
        # Check if we have a valid result
        if not post_validation.get('has_result', False):
            base_score -= 30
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_confidence_score(self, result: ValidatedCalculationResult) -> float:
        """Calculate overall confidence score"""
        if not result.calculation_result.is_valid:
            return 0.0
        
        # Weighted average of input and output quality
        input_weight = 0.6
        output_weight = 0.4
        
        confidence = (result.input_quality_score * input_weight + 
                     result.output_quality_score * output_weight)
        
        # Reduce confidence for validation errors
        if result.validation_errors:
            confidence *= 0.8  # 20% reduction for errors
        
        # Slight reduction for warnings
        if result.validation_warnings:
            confidence *= 0.95  # 5% reduction for warnings
        
        return max(0.0, min(100.0, confidence))
    
    def _generate_quality_recommendations(self, result: ValidatedCalculationResult) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        if result.input_quality_score < 70:
            recommendations.append("Input data quality is below optimal threshold. Review data sources and validation results.")
        
        if result.validation_errors:
            recommendations.append("Address validation errors to improve calculation reliability.")
        
        if len(result.validation_warnings) > 5:
            recommendations.append("Multiple validation warnings detected. Consider data quality improvements.")
        
        if result.overall_confidence < 80:
            recommendations.append("Overall confidence is below 80%. Review input data and validation results.")
        
        if not result.validation_passed:
            recommendations.append("Pre-calculation validation failed. Ensure input data meets quality requirements.")
        
        return recommendations
    
    def _attempt_auto_remediation(
        self,
        input_data: Dict[str, Any],
        validation_details: Dict[str, Any]
    ) -> bool:
        """Attempt automatic remediation of validation issues"""
        
        # This is a placeholder for auto-remediation logic
        # In practice, this would implement specific remediation strategies
        
        self.logger.info("Auto-remediation not yet implemented")
        return False
    
    def _update_performance_stats(self, execution_time_ms: float, validation_time_ms: float):
        """Update performance statistics"""
        total_calcs = self.performance_stats['total_calculations']
        
        # Update average execution time
        current_avg = self.performance_stats['average_calculation_time_ms']
        self.performance_stats['average_calculation_time_ms'] = (
            (current_avg * (total_calcs - 1) + execution_time_ms) / total_calcs
        )
        
        # Update average validation time
        current_val_avg = self.performance_stats['average_validation_time_ms']
        self.performance_stats['average_validation_time_ms'] = (
            (current_val_avg * (total_calcs - 1) + validation_time_ms) / total_calcs
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance statistics report"""
        total = self.performance_stats['total_calculations']
        if total == 0:
            return {'message': 'No calculations performed yet'}
        
        return {
            'total_calculations': total,
            'success_rate': (self.performance_stats['successful_calculations'] / total) * 100,
            'validation_failure_rate': (self.performance_stats['validation_failures'] / total) * 100,
            'calculation_failure_rate': (self.performance_stats['calculation_failures'] / total) * 100,
            'average_execution_time_ms': self.performance_stats['average_calculation_time_ms'],
            'average_validation_time_ms': self.performance_stats['average_validation_time_ms'],
            'validation_level': self.validation_level.value,
            'strict_mode': self.strict_mode
        }


if __name__ == "__main__":
    # Example usage
    print("=== Validated Financial Calculation Engine Test ===")
    
    # Create validated calculation engine
    engine = ValidatedFinancialCalculationEngine(
        validation_level=CalculationValidationLevel.COMPREHENSIVE,
        strict_mode=False
    )
    
    # Test data
    test_financial_data = {
        'EBIT': [1000, 1100, 1200, 1300, 1400],
        'Tax_Rate': [0.25, 0.25, 0.24, 0.24, 0.23],
        'Depreciation': [100, 110, 120, 125, 130],
        'Working_Capital_Change': [50, 60, 55, 70, 65],
        'CapEx': [200, 220, 240, 230, 250]
    }
    
    # Perform validated FCF calculation
    print("\n=== Testing Validated FCF Calculation ===")
    fcf_result = engine.calculate_validated_fcf(test_financial_data)
    
    print(f"Calculation Success: {fcf_result.calculation_result.is_valid}")
    print(f"Validation Passed: {fcf_result.validation_passed}")
    print(f"Input Quality Score: {fcf_result.input_quality_score:.1f}")
    print(f"Overall Confidence: {fcf_result.overall_confidence:.1f}")
    print(f"Validation Errors: {len(fcf_result.validation_errors)}")
    print(f"Validation Warnings: {len(fcf_result.validation_warnings)}")
    
    if fcf_result.calculation_result.is_valid:
        print(f"FCF Values: {fcf_result.calculation_result.value}")
    
    # Test with test data (should trigger testing validation)
    print("\n=== Testing with Mock Data ===")
    test_data_with_mock = {
        'EBIT_mock': [1000, 1100, 1200],  # Contains 'mock' identifier
        'Tax_Rate': [0.25, 0.25, 0.24],
        'Depreciation_test': [100, 110, 120]  # Contains 'test' identifier
    }
    
    mock_result = engine.calculate_validated_fcf(test_data_with_mock)
    print(f"Mock Data Validation Passed: {mock_result.validation_passed}")
    print(f"Mock Data Confidence: {mock_result.overall_confidence:.1f}")
    
    # Get performance report
    print("\n=== Performance Report ===")
    perf_report = engine.get_performance_report()
    for key, value in perf_report.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    print("\n=== Test Complete ===")