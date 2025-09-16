"""
Validation Orchestrator - Centralized Validation and Quality Module

This module provides a unified interface for all validation operations in the financial
analysis system. It coordinates pre-flight validation, data quality checks, and
testing framework validation.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# Import existing validation modules
from utils.input_validator import (
    PreFlightValidator, 
    ValidationLevel, 
    ValidationResult
)
from ..data_processing.data_validator import (
    FinancialDataValidator, 
    DataQualityReport,
    validate_financial_calculation_input
)
from error_handler import (
    EnhancedLogger,
    FinancialAnalysisError,
    ValidationError,
    with_error_handling
)

logger = EnhancedLogger(__name__)


class ValidationScope(Enum):
    """Defines the scope of validation to be performed"""
    
    PRE_FLIGHT = "pre_flight"          # System readiness checks
    DATA_QUALITY = "data_quality"      # Financial data validation
    CALCULATION = "calculation"        # Pre-calculation validation
    TESTING = "testing"               # Test-specific validation
    COMPREHENSIVE = "comprehensive"    # All validation types


class ValidationPriority(Enum):
    """Priority levels for validation rules"""
    
    CRITICAL = "critical"     # Must pass for system to function
    HIGH = "high"            # Should pass for reliable results
    MEDIUM = "medium"        # May impact quality but not functionality
    LOW = "low"              # Nice-to-have validation checks
    INFO = "info"            # Informational only


@dataclass
class ValidationConfig:
    """Configuration for validation orchestrator"""
    
    # Validation scope and levels
    scope: ValidationScope = ValidationScope.COMPREHENSIVE
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    
    # Priority thresholds
    min_priority: ValidationPriority = ValidationPriority.MEDIUM
    fail_on_priority: ValidationPriority = ValidationPriority.CRITICAL
    
    # Caching settings
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Network settings
    network_timeout: float = 10.0
    skip_network_validation: bool = False
    
    # Testing mode
    testing_mode: bool = False
    use_metadata_for_testing: bool = True
    
    # Reporting settings
    generate_detailed_reports: bool = True
    save_validation_logs: bool = False
    
    # Custom validation rules
    custom_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Comprehensive validation result container"""
    
    is_valid: bool
    scope: ValidationScope
    priority: ValidationPriority
    
    # Detailed results by category
    pre_flight_result: Optional[Dict[str, ValidationResult]] = None
    data_quality_result: Optional[DataQualityReport] = None
    calculation_result: Optional[Dict[str, Any]] = None
    testing_result: Optional[Dict[str, Any]] = None
    
    # Summary information
    total_errors: int = 0
    total_warnings: int = 0
    critical_failures: List[str] = field(default_factory=list)
    
    # Metadata
    validation_timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: float = 0.0
    config_used: Optional[ValidationConfig] = None
    
    # Recommendations and remediation
    remediation_steps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ValidationOrchestrator:
    """
    Central coordinator for all validation operations in the financial analysis system.
    
    This class provides a unified interface for:
    - Pre-flight system validation
    - Financial data quality validation
    - Calculation input validation
    - Testing framework validation
    """
    
    def __init__(self, config: ValidationConfig = None):
        """
        Initialize the validation orchestrator
        
        Args:
            config: Validation configuration, uses defaults if None
        """
        self.config = config or ValidationConfig()
        self.logger = EnhancedLogger(__name__)
        
        # Initialize component validators
        self._initialize_validators()
        
        # Track validation history
        self.validation_history: List[ValidationResult] = []
        
    def _initialize_validators(self):
        """Initialize all component validators"""
        try:
            # Pre-flight validator
            self.pre_flight_validator = PreFlightValidator(
                validation_level=self.config.validation_level,
                enable_caching=self.config.enable_caching,
                cache_ttl=self.config.cache_ttl,
                network_timeout=self.config.network_timeout
            )
            
            # Data quality validator
            self.data_quality_validator = FinancialDataValidator()
            
            self.logger.info("Validation orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize validation orchestrator", error=e)
            raise ValidationError(
                "Validation orchestrator initialization failed",
                error_code="ORCHESTRATOR_INIT_FAILED",
                context={'config': self.config.__dict__}
            ) from e
    
    @with_error_handling(error_type=ValidationError, return_on_error=None)
    def validate(
        self, 
        ticker: str = None,
        financial_data: Dict = None,
        calculation_inputs: Dict = None,
        scope: ValidationScope = None,
        **kwargs
    ) -> ValidationResult:
        """
        Perform comprehensive validation based on scope and configuration
        
        Args:
            ticker: Stock ticker symbol for pre-flight validation
            financial_data: Financial statement data for quality validation
            calculation_inputs: Input data for calculation validation
            scope: Override default validation scope
            **kwargs: Additional parameters for specific validators
            
        Returns:
            ValidationResult with comprehensive validation status
        """
        start_time = datetime.now()
        scope = scope or self.config.scope
        
        self.logger.info(
            f"Starting {scope.value} validation",
            context={
                'ticker': ticker,
                'has_financial_data': financial_data is not None,
                'has_calculation_inputs': calculation_inputs is not None
            }
        )
        
        # Initialize result container
        result = ValidationResult(
            is_valid=True,
            scope=scope,
            priority=self.config.min_priority,
            config_used=self.config
        )
        
        try:
            # Pre-flight validation
            if scope in [ValidationScope.PRE_FLIGHT, ValidationScope.COMPREHENSIVE]:
                result.pre_flight_result = self._validate_pre_flight(ticker, **kwargs)
                self._update_result_from_pre_flight(result)
            
            # Data quality validation
            if scope in [ValidationScope.DATA_QUALITY, ValidationScope.COMPREHENSIVE]:
                if financial_data:
                    result.data_quality_result = self._validate_data_quality(financial_data, **kwargs)
                    self._update_result_from_data_quality(result)
                else:
                    self.logger.warning("Data quality validation requested but no financial data provided")
            
            # Calculation validation
            if scope in [ValidationScope.CALCULATION, ValidationScope.COMPREHENSIVE]:
                if calculation_inputs:
                    result.calculation_result = self._validate_calculation_inputs(calculation_inputs, **kwargs)
                    self._update_result_from_calculation(result)
                else:
                    self.logger.warning("Calculation validation requested but no inputs provided")
            
            # Testing validation
            if scope in [ValidationScope.TESTING, ValidationScope.COMPREHENSIVE]:
                result.testing_result = self._validate_for_testing(**kwargs)
                self._update_result_from_testing(result)
            
            # Generate remediation and recommendations
            self._generate_remediation(result)
            
        except Exception as e:
            self.logger.error("Validation orchestration failed", error=e)
            result.is_valid = False
            result.critical_failures.append(f"Orchestration error: {str(e)}")
        
        # Calculate execution time
        end_time = datetime.now()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Store in history
        self.validation_history.append(result)
        
        self.logger.info(
            f"Validation completed: {'PASSED' if result.is_valid else 'FAILED'}",
            context={
                'execution_time_ms': result.execution_time_ms,
                'total_errors': result.total_errors,
                'total_warnings': result.total_warnings
            }
        )
        
        return result
    
    def _validate_pre_flight(self, ticker: str, **kwargs) -> Dict[str, ValidationResult]:
        """Perform pre-flight validation"""
        if not ticker:
            self.logger.warning("No ticker provided for pre-flight validation")
            ticker = "AAPL"  # Use dummy ticker for system checks
        
        return self.pre_flight_validator.validate_all(
            ticker, 
            skip_network=self.config.skip_network_validation
        )
    
    def _validate_data_quality(self, financial_data: Dict, **kwargs) -> DataQualityReport:
        """Perform financial data quality validation"""
        return self.data_quality_validator.validate_financial_statements(financial_data)
    
    def _validate_calculation_inputs(self, calculation_inputs: Dict, **kwargs) -> Dict[str, Any]:
        """Validate inputs for financial calculations"""
        validation_report = validate_financial_calculation_input(calculation_inputs)
        
        return {
            'report': validation_report,
            'is_valid': len(validation_report.errors) == 0,
            'metrics_validated': list(calculation_inputs.keys()),
            'validation_timestamp': datetime.now()
        }
    
    def _validate_for_testing(self, **kwargs) -> Dict[str, Any]:
        """Perform testing-specific validation"""
        testing_result = {
            'metadata_usage_valid': True,
            'test_data_quality': True,
            'mock_data_available': True,
            'testing_timestamp': datetime.now()
        }
        
        # Ensure metadata is only used for testing
        if self.config.testing_mode and not self.config.use_metadata_for_testing:
            self.logger.warning(
                "Testing mode enabled but metadata usage disabled",
                context={'testing_mode': self.config.testing_mode}
            )
            testing_result['metadata_usage_valid'] = False
        
        return testing_result
    
    def _update_result_from_pre_flight(self, result: ValidationResult):
        """Update main result from pre-flight validation results"""
        if not result.pre_flight_result:
            return
        
        for category, validation_result in result.pre_flight_result.items():
            if not validation_result.is_valid:
                result.total_errors += 1
                result.critical_failures.append(f"Pre-flight {category}: {validation_result.error_message}")
                
                if self.config.fail_on_priority == ValidationPriority.CRITICAL:
                    result.is_valid = False
    
    def _update_result_from_data_quality(self, result: ValidationResult):
        """Update main result from data quality validation"""
        if not result.data_quality_result:
            return
        
        result.total_errors += len(result.data_quality_result.errors)
        result.total_warnings += len(result.data_quality_result.warnings)
        
        # Add critical errors to failures
        for error in result.data_quality_result.errors:
            result.critical_failures.append(f"Data Quality: {error['message']}")
        
        # Determine if this should fail overall validation
        if (len(result.data_quality_result.errors) > 0 and 
            self.config.fail_on_priority in [ValidationPriority.CRITICAL, ValidationPriority.HIGH]):
            result.is_valid = False
    
    def _update_result_from_calculation(self, result: ValidationResult):
        """Update main result from calculation validation"""
        if not result.calculation_result:
            return
        
        calc_result = result.calculation_result
        if not calc_result.get('is_valid', True):
            result.total_errors += 1
            result.critical_failures.append("Calculation input validation failed")
            
            if self.config.fail_on_priority == ValidationPriority.CRITICAL:
                result.is_valid = False
    
    def _update_result_from_testing(self, result: ValidationResult):
        """Update main result from testing validation"""
        if not result.testing_result:
            return
        
        test_result = result.testing_result
        if not test_result.get('metadata_usage_valid', True):
            result.total_warnings += 1
            if self.config.fail_on_priority == ValidationPriority.MEDIUM:
                result.is_valid = False
    
    def _generate_remediation(self, result: ValidationResult):
        """Generate remediation steps and recommendations"""
        remediation_steps = []
        recommendations = []
        
        # Pre-flight remediation
        if result.pre_flight_result:
            for category, validation_result in result.pre_flight_result.items():
                if not validation_result.is_valid and validation_result.remediation:
                    remediation_steps.append(f"{category}: {validation_result.remediation}")
        
        # Data quality recommendations
        if result.data_quality_result and result.data_quality_result.recommendations:
            for rec in result.data_quality_result.recommendations:
                recommendations.append(f"Data Quality: {rec['message']}")
        
        # General recommendations based on error patterns
        if result.total_errors > 5:
            recommendations.append("High error count detected - consider comprehensive system review")
        
        if result.total_warnings > 10:
            recommendations.append("Many warnings detected - review data source quality")
        
        result.remediation_steps = remediation_steps
        result.recommendations = recommendations
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation operations"""
        if not self.validation_history:
            return {'message': 'No validations performed yet'}
        
        recent_validations = self.validation_history[-10:]  # Last 10 validations
        
        return {
            'total_validations': len(self.validation_history),
            'recent_validations': len(recent_validations),
            'success_rate': sum(1 for v in recent_validations if v.is_valid) / len(recent_validations) * 100,
            'average_execution_time_ms': sum(v.execution_time_ms for v in recent_validations) / len(recent_validations),
            'total_errors': sum(v.total_errors for v in recent_validations),
            'total_warnings': sum(v.total_warnings for v in recent_validations),
            'last_validation': recent_validations[-1].validation_timestamp.isoformat() if recent_validations else None
        }
    
    def clear_history(self):
        """Clear validation history"""
        self.validation_history.clear()
        self.logger.info("Validation history cleared")
    
    def save_validation_report(self, result: ValidationResult, file_path: str = None) -> str:
        """Save detailed validation report to file"""
        if file_path is None:
            timestamp = result.validation_timestamp.strftime('%Y%m%d_%H%M%S')
            file_path = f"validation_report_{timestamp}.json"
        
        import json
        
        # Convert result to serializable format
        report_data = {
            'summary': {
                'is_valid': result.is_valid,
                'scope': result.scope.value,
                'timestamp': result.validation_timestamp.isoformat(),
                'execution_time_ms': result.execution_time_ms,
                'total_errors': result.total_errors,
                'total_warnings': result.total_warnings
            },
            'critical_failures': result.critical_failures,
            'remediation_steps': result.remediation_steps,
            'recommendations': result.recommendations,
            'data_quality_summary': result.data_quality_result.get_summary() if result.data_quality_result else None
        }
        
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"Validation report saved to {file_path}")
        return file_path


# Convenience functions for common validation scenarios
def validate_system_ready(ticker: str = "AAPL") -> bool:
    """Quick system readiness check"""
    orchestrator = ValidationOrchestrator(ValidationConfig(scope=ValidationScope.PRE_FLIGHT))
    result = orchestrator.validate(ticker=ticker)
    return result.is_valid


def validate_financial_data_quality(financial_data: Dict) -> Tuple[bool, DataQualityReport]:
    """Quick financial data quality validation"""
    orchestrator = ValidationOrchestrator(ValidationConfig(scope=ValidationScope.DATA_QUALITY))
    result = orchestrator.validate(financial_data=financial_data)
    return result.is_valid, result.data_quality_result


def validate_for_production(ticker: str, financial_data: Dict, calculation_inputs: Dict) -> ValidationResult:
    """Comprehensive production validation"""
    config = ValidationConfig(
        scope=ValidationScope.COMPREHENSIVE,
        validation_level=ValidationLevel.STRICT,
        fail_on_priority=ValidationPriority.HIGH,
        generate_detailed_reports=True
    )
    
    orchestrator = ValidationOrchestrator(config)
    return orchestrator.validate(
        ticker=ticker,
        financial_data=financial_data,
        calculation_inputs=calculation_inputs
    )


def validate_for_testing(financial_data: Dict = None, use_metadata: bool = True) -> ValidationResult:
    """Testing-specific validation"""
    config = ValidationConfig(
        scope=ValidationScope.TESTING,
        testing_mode=True,
        use_metadata_for_testing=use_metadata,
        skip_network_validation=True
    )
    
    orchestrator = ValidationOrchestrator(config)
    return orchestrator.validate(financial_data=financial_data)


if __name__ == "__main__":
    # Example usage
    print("=== Validation Orchestrator Test ===")
    
    # Test system readiness
    print("\n1. Testing system readiness...")
    is_ready = validate_system_ready("AAPL")
    print(f"System ready: {is_ready}")
    
    # Test comprehensive validation
    print("\n2. Testing comprehensive validation...")
    config = ValidationConfig(scope=ValidationScope.COMPREHENSIVE)
    orchestrator = ValidationOrchestrator(config)
    
    result = orchestrator.validate(ticker="MSFT")
    print(f"Validation result: {'PASSED' if result.is_valid else 'FAILED'}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    print(f"Errors: {result.total_errors}, Warnings: {result.total_warnings}")
    
    # Print summary
    summary = orchestrator.get_validation_summary()
    print(f"\nValidation Summary: {summary}")