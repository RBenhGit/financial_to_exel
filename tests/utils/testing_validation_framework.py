"""
Testing Validation Framework - Ensures Metadata is Used Only for Testing

This module provides a comprehensive testing framework that validates test environments,
ensures metadata separation, and prevents test data leakage into production calculations.
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import os
import inspect
import ast
import sys
from pathlib import Path
from datetime import datetime
import logging
import threading
from contextlib import contextmanager

from error_handler import EnhancedLogger, ValidationError


class TestingMode(Enum):
    """Testing mode levels"""
    
    PRODUCTION = "production"      # No test data allowed
    DEVELOPMENT = "development"    # Test data allowed in dev
    UNIT_TEST = "unit_test"       # Full test mode
    INTEGRATION_TEST = "integration_test"  # Integration testing
    MOCK_MODE = "mock_mode"       # Using mock data


class MetadataSource(Enum):
    """Sources of metadata that should only be used in testing"""
    
    MOCK_DATA = "mock_data"                    # Mock/fake data
    TEST_FIXTURES = "test_fixtures"            # Test fixture data
    SAMPLE_DATA = "sample_data"                # Sample/example data
    SYNTHETIC_DATA = "synthetic_data"          # Generated synthetic data
    CACHED_TEST_DATA = "cached_test_data"      # Cached test results
    DEMO_DATA = "demo_data"                    # Demo/presentation data


@dataclass
class MetadataMarker:
    """Marker that identifies metadata/test data"""
    
    source: MetadataSource
    identifier: str
    description: str
    allowed_modes: List[TestingMode] = field(default_factory=lambda: [TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST])
    created_timestamp: datetime = field(default_factory=datetime.now)
    
    def is_allowed_in_mode(self, mode: TestingMode) -> bool:
        """Check if metadata is allowed in the given mode"""
        return mode in self.allowed_modes


@dataclass
class TestingContext:
    """Current testing context and environment"""
    
    mode: TestingMode
    allow_metadata: bool
    test_session_id: str
    started_at: datetime = field(default_factory=datetime.now)
    
    # Environment detection
    is_pytest_session: bool = False
    is_unittest_session: bool = False
    is_development_environment: bool = False
    is_production_environment: bool = False
    
    # Metadata tracking
    metadata_usage_log: List[Dict[str, Any]] = field(default_factory=list)
    violations_detected: List[str] = field(default_factory=list)


class TestingValidationFramework:
    """
    Framework for validating test environments and ensuring metadata separation
    
    This framework provides:
    1. Environment detection and validation
    2. Metadata usage tracking and control
    3. Test data separation enforcement
    4. Production safety checks
    """
    
    # Thread-local storage for testing contexts
    _local = threading.local()
    
    def __init__(self):
        self.logger = EnhancedLogger(__name__)
        
        # Registry of metadata markers
        self.metadata_registry: Dict[str, MetadataMarker] = {}
        
        # Default metadata markers
        self._initialize_default_markers()
        
        # Current context (thread-safe)
        self._current_context: Optional[TestingContext] = None
        
        # Global settings
        self.strict_mode = True  # Fail on violations
        self.log_all_usage = True  # Log all metadata usage
        
    def _initialize_default_markers(self):
        """Initialize default metadata markers"""
        
        # Common test data markers
        markers = [
            MetadataMarker(
                source=MetadataSource.MOCK_DATA,
                identifier="_mock",
                description="Mock data identifier",
                allowed_modes=[TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST, TestingMode.MOCK_MODE]
            ),
            MetadataMarker(
                source=MetadataSource.TEST_FIXTURES,
                identifier="_test",
                description="Test fixture identifier",
                allowed_modes=[TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST]
            ),
            MetadataMarker(
                source=MetadataSource.SAMPLE_DATA,
                identifier="_sample",
                description="Sample data identifier",
                allowed_modes=[TestingMode.DEVELOPMENT, TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST]
            ),
            MetadataMarker(
                source=MetadataSource.DEMO_DATA,
                identifier="_demo",
                description="Demo/presentation data",
                allowed_modes=[TestingMode.DEVELOPMENT, TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST]
            ),
            MetadataMarker(
                source=MetadataSource.SYNTHETIC_DATA,
                identifier="_synthetic",
                description="Generated synthetic data",
                allowed_modes=[TestingMode.DEVELOPMENT, TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST]
            ),
            MetadataMarker(
                source=MetadataSource.CACHED_TEST_DATA,
                identifier="_cached_test",
                description="Cached test data",
                allowed_modes=[TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST]
            )
        ]
        
        for marker in markers:
            self.metadata_registry[marker.identifier] = marker
    
    def register_metadata_marker(self, marker: MetadataMarker):
        """Register a new metadata marker"""
        self.metadata_registry[marker.identifier] = marker
        self.logger.info(f"Registered metadata marker: {marker.identifier}")
    
    def detect_testing_environment(self) -> TestingMode:
        """Detect the current testing environment"""
        
        # Check for pytest
        if 'pytest' in sys.modules or '_pytest' in sys.modules:
            return TestingMode.UNIT_TEST
        
        # Check for unittest
        if any('unittest' in str(frame.filename) for frame in inspect.stack()):
            return TestingMode.UNIT_TEST
        
        # Check for development indicators
        if (os.getenv('ENVIRONMENT') in ['dev', 'development'] or 
            os.getenv('DEBUG') == 'True' or
            'test' in os.getcwd().lower()):
            return TestingMode.DEVELOPMENT
        
        # Check for production indicators
        if (os.getenv('ENVIRONMENT') == 'production' or
            os.getenv('PROD') == 'True'):
            return TestingMode.PRODUCTION
        
        # Default to development if uncertain
        return TestingMode.DEVELOPMENT
    
    @contextmanager
    def testing_context(
        self, 
        mode: TestingMode, 
        allow_metadata: bool = None,
        session_id: str = None
    ):
        """
        Context manager for setting testing mode
        
        Args:
            mode: Testing mode to set
            allow_metadata: Whether to allow metadata usage
            session_id: Unique session identifier
        """
        if allow_metadata is None:
            allow_metadata = mode in [TestingMode.UNIT_TEST, TestingMode.INTEGRATION_TEST, TestingMode.DEVELOPMENT]
        
        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create new context
        context = TestingContext(
            mode=mode,
            allow_metadata=allow_metadata,
            test_session_id=session_id,
            is_pytest_session='pytest' in sys.modules,
            is_unittest_session='unittest' in sys.modules,
            is_development_environment=mode == TestingMode.DEVELOPMENT,
            is_production_environment=mode == TestingMode.PRODUCTION
        )
        
        # Store previous context
        previous_context = getattr(self._local, 'context', None)
        self._local.context = context
        self._current_context = context
        
        try:
            self.logger.info(
                f"Entering testing context: {mode.value}, metadata allowed: {allow_metadata}",
                context={'session_id': session_id}
            )
            yield context
        finally:
            # Restore previous context
            if previous_context:
                self._local.context = previous_context
                self._current_context = previous_context
            else:
                self._local.context = None
                self._current_context = None
            
            self.logger.info(
                f"Exiting testing context: {mode.value}",
                context={'session_id': session_id, 'violations': len(context.violations_detected)}
            )
    
    def get_current_context(self) -> Optional[TestingContext]:
        """Get the current testing context"""
        return getattr(self._local, 'context', self._current_context)
    
    def is_metadata_identifier(self, identifier: str) -> bool:
        """Check if an identifier contains metadata markers"""
        identifier_lower = identifier.lower()
        
        # Check registered markers
        for marker_id in self.metadata_registry.keys():
            if marker_id.lower() in identifier_lower:
                return True
        
        # Check common patterns
        test_patterns = [
            'test_', '_test', 'mock_', '_mock', 'sample_', '_sample',
            'demo_', '_demo', 'fake_', '_fake', 'dummy_', '_dummy',
            'fixture_', '_fixture', 'synthetic_', '_synthetic'
        ]
        
        return any(pattern in identifier_lower for pattern in test_patterns)
    
    def validate_metadata_usage(
        self, 
        identifier: str, 
        data_source: str = "unknown",
        context_info: Dict[str, Any] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate whether metadata usage is allowed in current context
        
        Args:
            identifier: The identifier being checked
            data_source: Source of the data
            context_info: Additional context information
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        current_context = self.get_current_context()
        
        # If no context is set, auto-detect
        if not current_context:
            detected_mode = self.detect_testing_environment()
            current_context = TestingContext(
                mode=detected_mode,
                allow_metadata=detected_mode != TestingMode.PRODUCTION,
                test_session_id="auto_detected"
            )
            self._current_context = current_context
        
        # Check if identifier contains metadata markers
        if not self.is_metadata_identifier(identifier):
            return True, []  # Not metadata, always allowed
        
        # Log metadata usage
        usage_entry = {
            'identifier': identifier,
            'data_source': data_source,
            'mode': current_context.mode.value,
            'allowed': current_context.allow_metadata,
            'timestamp': datetime.now().isoformat(),
            'context_info': context_info or {}
        }
        current_context.metadata_usage_log.append(usage_entry)
        
        if self.log_all_usage:
            self.logger.info(
                f"Metadata usage detected: {identifier}",
                context=usage_entry
            )
        
        # Check if metadata is allowed in current mode
        if not current_context.allow_metadata:
            violation = f"Metadata usage not allowed in {current_context.mode.value} mode: {identifier}"
            violations.append(violation)
            current_context.violations_detected.append(violation)
            
            if self.strict_mode:
                self.logger.error(violation, context=usage_entry)
            else:
                self.logger.warning(violation, context=usage_entry)
        
        # Check specific marker constraints
        for marker_id, marker in self.metadata_registry.items():
            if marker_id.lower() in identifier.lower():
                if not marker.is_allowed_in_mode(current_context.mode):
                    violation = (f"Metadata marker '{marker_id}' not allowed in {current_context.mode.value} mode. "
                               f"Allowed modes: {[m.value for m in marker.allowed_modes]}")
                    violations.append(violation)
                    current_context.violations_detected.append(violation)
        
        return len(violations) == 0, violations
    
    def validate_function_call(self, func: callable, *args, **kwargs) -> Tuple[bool, List[str]]:
        """
        Validate function call for metadata usage
        
        Args:
            func: Function being called
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Get function details
        func_name = getattr(func, '__name__', str(func))
        func_module = getattr(func, '__module__', 'unknown')
        
        # Check function name
        valid, func_violations = self.validate_metadata_usage(
            func_name,
            f"function:{func_module}",
            {'function_type': 'callable'}
        )
        violations.extend(func_violations)
        
        # Check arguments
        for i, arg in enumerate(args):
            if isinstance(arg, str):
                arg_valid, arg_violations = self.validate_metadata_usage(
                    arg,
                    f"function_arg:{func_name}",
                    {'arg_position': i, 'arg_type': 'positional'}
                )
                violations.extend(arg_violations)
        
        # Check keyword arguments
        for key, value in kwargs.items():
            # Check key name
            key_valid, key_violations = self.validate_metadata_usage(
                key,
                f"function_kwarg_key:{func_name}",
                {'kwarg_name': key, 'arg_type': 'keyword_key'}
            )
            violations.extend(key_violations)
            
            # Check value if string
            if isinstance(value, str):
                val_valid, val_violations = self.validate_metadata_usage(
                    value,
                    f"function_kwarg_value:{func_name}",
                    {'kwarg_name': key, 'arg_type': 'keyword_value'}
                )
                violations.extend(val_violations)
        
        return len(violations) == 0, violations
    
    def validate_data_structure(self, data: Any, data_name: str = "data") -> Tuple[bool, List[str]]:
        """
        Validate data structure for metadata usage
        
        Args:
            data: Data structure to validate
            data_name: Name/identifier for the data
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Validate data name
        valid, name_violations = self.validate_metadata_usage(
            data_name,
            "data_structure",
            {'data_type': type(data).__name__}
        )
        violations.extend(name_violations)
        
        # Validate dictionary keys
        if isinstance(data, dict):
            for key in data.keys():
                if isinstance(key, str):
                    key_valid, key_violations = self.validate_metadata_usage(
                        key,
                        f"dict_key:{data_name}",
                        {'container_type': 'dictionary'}
                    )
                    violations.extend(key_violations)
        
        # Validate pandas DataFrame columns
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                for column in data.columns:
                    if isinstance(column, str):
                        col_valid, col_violations = self.validate_metadata_usage(
                            column,
                            f"dataframe_column:{data_name}",
                            {'container_type': 'dataframe'}
                        )
                        violations.extend(col_violations)
        except ImportError:
            pass  # pandas not available
        
        return len(violations) == 0, violations
    
    def create_test_data_guard(self, data_identifier: str, metadata_source: MetadataSource) -> callable:
        """
        Create a decorator that guards against test data usage in production
        
        Args:
            data_identifier: Identifier for the test data
            metadata_source: Source type of the metadata
            
        Returns:
            Decorator function
        """
        def decorator(func: callable) -> callable:
            def wrapper(*args, **kwargs):
                # Validate metadata usage
                valid, violations = self.validate_metadata_usage(
                    data_identifier,
                    f"guarded_function:{func.__name__}",
                    {
                        'metadata_source': metadata_source.value,
                        'guarded': True
                    }
                )
                
                if not valid and self.strict_mode:
                    raise ValidationError(
                        f"Test data usage not allowed in current context: {data_identifier}",
                        error_code="TEST_DATA_VIOLATION",
                        context={
                            'violations': violations,
                            'function': func.__name__,
                            'metadata_source': metadata_source.value
                        }
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report"""
        current_context = self.get_current_context()
        
        if not current_context:
            return {
                'status': 'no_active_context',
                'message': 'No testing context currently active'
            }
        
        return {
            'context': {
                'mode': current_context.mode.value,
                'allow_metadata': current_context.allow_metadata,
                'session_id': current_context.test_session_id,
                'started_at': current_context.started_at.isoformat(),
                'environment_flags': {
                    'pytest': current_context.is_pytest_session,
                    'unittest': current_context.is_unittest_session,
                    'development': current_context.is_development_environment,
                    'production': current_context.is_production_environment
                }
            },
            'metadata_usage': {
                'total_usage_events': len(current_context.metadata_usage_log),
                'violations_detected': len(current_context.violations_detected),
                'recent_usage': current_context.metadata_usage_log[-10:] if current_context.metadata_usage_log else [],
                'all_violations': current_context.violations_detected
            },
            'registry': {
                'registered_markers': len(self.metadata_registry),
                'markers': [
                    {
                        'identifier': marker.identifier,
                        'source': marker.source.value,
                        'description': marker.description,
                        'allowed_modes': [mode.value for mode in marker.allowed_modes]
                    }
                    for marker in self.metadata_registry.values()
                ]
            },
            'settings': {
                'strict_mode': self.strict_mode,
                'log_all_usage': self.log_all_usage
            }
        }


# Global framework instance
_framework_instance: Optional[TestingValidationFramework] = None


def get_testing_framework() -> TestingValidationFramework:
    """Get the global testing validation framework instance"""
    global _framework_instance
    if _framework_instance is None:
        _framework_instance = TestingValidationFramework()
    return _framework_instance


# Convenience functions
def validate_metadata_usage(identifier: str, data_source: str = "unknown") -> bool:
    """Quick metadata usage validation"""
    framework = get_testing_framework()
    valid, violations = framework.validate_metadata_usage(identifier, data_source)
    return valid


def test_data_only(metadata_source: MetadataSource = MetadataSource.TEST_FIXTURES):
    """Decorator to mark functions as test-data-only"""
    framework = get_testing_framework()
    return framework.create_test_data_guard(
        f"test_data_function_{metadata_source.value}",
        metadata_source
    )


@contextmanager
def production_mode():
    """Context manager for production mode"""
    framework = get_testing_framework()
    with framework.testing_context(TestingMode.PRODUCTION, allow_metadata=False):
        yield


@contextmanager
def testing_mode():
    """Context manager for testing mode"""
    framework = get_testing_framework()
    with framework.testing_context(TestingMode.UNIT_TEST, allow_metadata=True):
        yield


if __name__ == "__main__":
    # Example usage
    print("=== Testing Validation Framework Test ===")
    
    framework = TestingValidationFramework()
    
    # Test environment detection
    detected_mode = framework.detect_testing_environment()
    print(f"Detected environment: {detected_mode.value}")
    
    # Test with production context
    print("\n=== Production Context Test ===")
    with framework.testing_context(TestingMode.PRODUCTION):
        valid, violations = framework.validate_metadata_usage("test_data_input", "user_input")
        print(f"Test data in production - Valid: {valid}")
        if violations:
            print(f"Violations: {violations}")
    
    # Test with testing context
    print("\n=== Testing Context Test ===")
    with framework.testing_context(TestingMode.UNIT_TEST):
        valid, violations = framework.validate_metadata_usage("test_data_input", "test_fixture")
        print(f"Test data in testing - Valid: {valid}")
        
        # Test function validation
        def sample_function(ticker, use_mock_data=False):
            return f"Processing {ticker} with mock: {use_mock_data}"
        
        func_valid, func_violations = framework.validate_function_call(
            sample_function, "AAPL", use_mock_data=True
        )
        print(f"Function call validation - Valid: {func_valid}")
    
    # Get validation report
    print("\n=== Validation Report ===")
    report = framework.get_validation_report()
    print(f"Context: {report['context']['mode']}")
    print(f"Metadata usage events: {report['metadata_usage']['total_usage_events']}")
    print(f"Violations detected: {report['metadata_usage']['violations_detected']}")
    
    # Test decorator
    print("\n=== Test Data Guard Decorator ===")
    @test_data_only(MetadataSource.MOCK_DATA)
    def mock_data_function():
        return "This function uses mock data"
    
    with framework.testing_context(TestingMode.UNIT_TEST):
        try:
            result = mock_data_function()
            print(f"Mock function in test mode: {result}")
        except ValidationError as e:
            print(f"Validation error: {e}")
    
    with framework.testing_context(TestingMode.PRODUCTION):
        try:
            result = mock_data_function()
            print(f"Mock function in production: {result}")
        except ValidationError as e:
            print(f"Validation error in production: {e}")
    
    print("\n=== Test Complete ===")