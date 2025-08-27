"""
Module Adapter Pattern Implementation

This module provides a unified adapter interface for standardizing interactions between
different module types (data sources, calculation engines, processors, etc.) with
consistent interfaces and minimal coupling.

Features:
- Universal module adapter interface
- Standardized data contracts
- Dependency injection support
- Module lifecycle management
- Error handling and logging
- Configuration management
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import inspect

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
ModuleConfig = Dict[str, Any]
ModuleResult = Dict[str, Any]


class ModuleType(Enum):
    """Enum defining different module types in the system"""
    DATA_SOURCE = "data_source"
    CALCULATION_ENGINE = "calculation_engine"
    PROCESSOR = "processor"
    VALIDATOR = "validator"
    EXPORT_HANDLER = "export_handler"
    CACHE_MANAGER = "cache_manager"


@dataclass
class ModuleMetadata:
    """Metadata describing a module's capabilities and requirements"""
    name: str
    module_type: ModuleType
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModuleRequest:
    """Standardized request format for module operations"""
    operation: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleResponse:
    """Standardized response format from module operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    request_id: Optional[str] = None


class ModuleAdapter(ABC, Generic[T]):
    """
    Abstract base class for all module adapters.
    
    Provides a standardized interface for interacting with different types
    of modules while hiding their implementation details.
    """
    
    def __init__(self, module: T, config: Optional[ModuleConfig] = None):
        """
        Initialize adapter with the underlying module and configuration.
        
        Args:
            module: The underlying module instance
            config: Optional configuration for the adapter
        """
        self._module = module
        self._config = config or {}
        self._metadata = self._create_metadata()
        self._initialized = False
        
    @property
    def metadata(self) -> ModuleMetadata:
        """Get module metadata"""
        return self._metadata
        
    @property
    def module_type(self) -> ModuleType:
        """Get the module type"""
        return self._metadata.module_type
        
    @property
    def is_initialized(self) -> bool:
        """Check if module is initialized"""
        return self._initialized
        
    @abstractmethod
    def _create_metadata(self) -> ModuleMetadata:
        """Create metadata for the module. Must be implemented by subclasses."""
        pass
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the module. Must be implemented by subclasses.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
        
    @abstractmethod
    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """
        Execute a module operation. Must be implemented by subclasses.
        
        Args:
            request: Standardized request object
            
        Returns:
            ModuleResponse: Standardized response object
        """
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources. Must be implemented by subclasses."""
        pass
        
    def validate_request(self, request: ModuleRequest) -> List[str]:
        """
        Validate request against module's input schema.
        
        Args:
            request: Request to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self._metadata.input_schema:
            return errors  # No schema to validate against
            
        # Basic validation - can be extended with jsonschema
        required_params = self._metadata.input_schema.get('required', [])
        for param in required_params:
            if param not in request.parameters:
                errors.append(f"Missing required parameter: {param}")
                
        return errors
        
    def _validate_operation_request(self, request: ModuleRequest) -> List[str]:
        """
        Validate request for specific operation (can be overridden by subclasses).
        
        Args:
            request: Request to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self.validate_request(request)
        
    def get_capabilities(self) -> List[str]:
        """Get list of module capabilities"""
        return self._metadata.capabilities.copy()
        
    def supports_operation(self, operation: str) -> bool:
        """Check if module supports a specific operation"""
        return operation in self._metadata.capabilities
        
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        return self._config.get(key, default)


class DataSourceAdapter(ModuleAdapter):
    """Adapter for data source modules"""
    
    def _create_metadata(self) -> ModuleMetadata:
        """Create metadata for data source"""
        return ModuleMetadata(
            name=f"{self._module.__class__.__name__}Adapter",
            module_type=ModuleType.DATA_SOURCE,
            version="1.0.0",
            description=f"Data source adapter for {self._module.__class__.__name__}",
            capabilities=[
                "fetch_data", "validate_credentials", "get_available_fields",
                "check_rate_limits", "get_usage_statistics"
            ],
            input_schema={
                "required": ["symbol"],
                "optional": ["start_date", "end_date", "data_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "dict"},
                    "metadata": {"type": "dict"},
                    "source": {"type": "string"}
                }
            }
        )
        
    def initialize(self) -> bool:
        """Initialize data source"""
        try:
            if hasattr(self._module, 'validate_credentials'):
                self._initialized = self._module.validate_credentials()
            else:
                self._initialized = True
            
            if self._initialized:
                logger.info(f"Data source adapter {self.metadata.name} initialized successfully")
            else:
                logger.error(f"Failed to initialize data source adapter {self.metadata.name}")
                
            return self._initialized
            
        except Exception as e:
            logger.error(f"Error initializing data source adapter: {str(e)}")
            return False
            
    def _validate_operation_request(self, request: ModuleRequest) -> List[str]:
        """Validate request for specific data source operation"""
        errors = []
        
        # Only fetch_data operation requires symbol parameter
        if request.operation == "fetch_data":
            if "symbol" not in request.parameters:
                errors.append("Missing required parameter: symbol")
                
        return errors
            
    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute data source operation"""
        start_time = datetime.now()
        
        # Validate request (operation-specific)
        validation_errors = self._validate_operation_request(request)
        if validation_errors:
            return ModuleResponse(
                success=False,
                error=f"Validation failed: {'; '.join(validation_errors)}",
                request_id=request.request_id
            )
            
        try:
            operation = request.operation
            
            if operation == "fetch_data":
                result = self._fetch_data(request)
            elif operation == "validate_credentials":
                result = self._validate_credentials()
            elif operation == "get_available_fields":
                result = self._get_available_fields()
            elif operation == "check_rate_limits":
                result = self._check_rate_limits()
            elif operation == "get_usage_statistics":
                result = self._get_usage_statistics()
            else:
                return ModuleResponse(
                    success=False,
                    error=f"Unsupported operation: {operation}",
                    request_id=request.request_id
                )
                
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModuleResponse(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error executing data source operation {operation}: {str(e)}")
            
            return ModuleResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
    def _fetch_data(self, request: ModuleRequest) -> Any:
        """Fetch data from the underlying provider"""
        if hasattr(self._module, 'fetch_data'):
            # Assume the module expects a request object
            return self._module.fetch_data(request.parameters.get('data_request'))
        else:
            # Fallback to direct parameter passing
            return self._module.get_data(**request.parameters)
            
    def _validate_credentials(self) -> bool:
        """Validate credentials"""
        if hasattr(self._module, 'validate_credentials'):
            return self._module.validate_credentials()
        return True
        
    def _get_available_fields(self) -> List[str]:
        """Get available data fields"""
        if hasattr(self._module, 'get_available_fields'):
            return self._module.get_available_fields()
        return []
        
    def _check_rate_limits(self) -> Dict[str, Any]:
        """Check rate limit status"""
        if hasattr(self._module, 'get_rate_limit_status'):
            return self._module.get_rate_limit_status()
        return {"rate_limit_ok": True}
        
    def _get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        if hasattr(self._module, 'get_usage_stats'):
            return self._module.get_usage_stats()
        return {}
        
    def cleanup(self) -> None:
        """Cleanup data source resources"""
        if hasattr(self._module, 'close'):
            self._module.close()
        if hasattr(self._module, '_session'):
            self._module._session.close()


class CalculationEngineAdapter(ModuleAdapter):
    """Adapter for calculation engine modules"""
    
    def _create_metadata(self) -> ModuleMetadata:
        """Create metadata for calculation engine"""
        return ModuleMetadata(
            name=f"{self._module.__class__.__name__}Adapter",
            module_type=ModuleType.CALCULATION_ENGINE,
            version="1.0.0",
            description=f"Calculation engine adapter for {self._module.__class__.__name__}",
            capabilities=[
                "calculate_fcf", "calculate_dcf", "calculate_pb_ratio",
                "calculate_growth_rates", "validate_inputs", "get_calculation_parameters"
            ],
            input_schema={
                "required": ["financial_data"],
                "optional": ["calculation_parameters", "validation_level"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "calculations": {"type": "dict"},
                    "metadata": {"type": "dict"},
                    "validation_results": {"type": "dict"}
                }
            }
        )
        
    def initialize(self) -> bool:
        """Initialize calculation engine"""
        try:
            # Most calculation engines don't need explicit initialization
            self._initialized = True
            logger.info(f"Calculation engine adapter {self.metadata.name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing calculation engine adapter: {str(e)}")
            return False
            
    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute calculation engine operation"""
        start_time = datetime.now()
        
        # Validate request
        validation_errors = self.validate_request(request)
        if validation_errors:
            return ModuleResponse(
                success=False,
                error=f"Validation failed: {'; '.join(validation_errors)}",
                request_id=request.request_id
            )
            
        try:
            operation = request.operation
            
            if operation == "calculate_fcf":
                result = self._calculate_fcf(request)
            elif operation == "calculate_dcf":
                result = self._calculate_dcf(request)
            elif operation == "calculate_pb_ratio":
                result = self._calculate_pb_ratio(request)
            elif operation == "calculate_growth_rates":
                result = self._calculate_growth_rates(request)
            elif operation == "validate_inputs":
                result = self._validate_inputs(request)
            elif operation == "get_calculation_parameters":
                result = self._get_calculation_parameters()
            else:
                return ModuleResponse(
                    success=False,
                    error=f"Unsupported operation: {operation}",
                    request_id=request.request_id
                )
                
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModuleResponse(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error executing calculation engine operation {operation}: {str(e)}")
            
            return ModuleResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
    def _calculate_fcf(self, request: ModuleRequest) -> Any:
        """Calculate free cash flow"""
        method_name = self._find_calculation_method(['calculate_fcf', 'get_fcf', 'fcf_analysis'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("FCF calculation not available in underlying module")
        
    def _calculate_dcf(self, request: ModuleRequest) -> Any:
        """Calculate DCF valuation"""
        method_name = self._find_calculation_method(['calculate_dcf', 'dcf_valuation', 'get_dcf_value'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("DCF calculation not available in underlying module")
        
    def _calculate_pb_ratio(self, request: ModuleRequest) -> Any:
        """Calculate P/B ratio analysis"""
        method_name = self._find_calculation_method(['calculate_pb', 'pb_analysis', 'get_pb_ratio'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("P/B calculation not available in underlying module")
        
    def _calculate_growth_rates(self, request: ModuleRequest) -> Any:
        """Calculate growth rates"""
        method_name = self._find_calculation_method(['calculate_growth', 'growth_analysis', 'get_growth_rates'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("Growth rate calculation not available in underlying module")
        
    def _validate_inputs(self, request: ModuleRequest) -> Dict[str, Any]:
        """Validate calculation inputs"""
        if hasattr(self._module, 'validate_inputs'):
            return self._module.validate_inputs(request.parameters['financial_data'])
        return {"valid": True, "errors": []}
        
    def _get_calculation_parameters(self) -> Dict[str, Any]:
        """Get available calculation parameters"""
        if hasattr(self._module, 'get_parameters'):
            return self._module.get_parameters()
        return {}
        
    def _find_calculation_method(self, method_names: List[str]) -> Optional[str]:
        """Find available calculation method from list of possibilities"""
        for name in method_names:
            if hasattr(self._module, name):
                return name
        return None
        
    def _call_with_appropriate_params(self, method, parameters: Dict[str, Any]) -> Any:
        """Call method with appropriate parameters based on its signature"""
        sig = inspect.signature(method)
        filtered_params = {}
        
        for param_name in sig.parameters:
            if param_name in parameters:
                filtered_params[param_name] = parameters[param_name]
                
        return method(**filtered_params)
        
    def cleanup(self) -> None:
        """Cleanup calculation engine resources"""
        # Most calculation engines don't need explicit cleanup
        pass


class ProcessorAdapter(ModuleAdapter):
    """Adapter for data processor modules"""
    
    def _create_metadata(self) -> ModuleMetadata:
        """Create metadata for processor"""
        return ModuleMetadata(
            name=f"{self._module.__class__.__name__}Adapter",
            module_type=ModuleType.PROCESSOR,
            version="1.0.0",
            description=f"Processor adapter for {self._module.__class__.__name__}",
            capabilities=[
                "process_data", "transform_data", "validate_data",
                "normalize_data", "aggregate_data"
            ],
            input_schema={
                "required": ["data"],
                "optional": ["processing_options", "output_format"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "processed_data": {"type": "dict"},
                    "processing_metadata": {"type": "dict"}
                }
            }
        )
        
    def initialize(self) -> bool:
        """Initialize processor"""
        try:
            self._initialized = True
            logger.info(f"Processor adapter {self.metadata.name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing processor adapter: {str(e)}")
            return False
            
    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute processor operation"""
        start_time = datetime.now()
        
        # Validate request
        validation_errors = self.validate_request(request)
        if validation_errors:
            return ModuleResponse(
                success=False,
                error=f"Validation failed: {'; '.join(validation_errors)}",
                request_id=request.request_id
            )
            
        try:
            operation = request.operation
            
            if operation == "process_data":
                result = self._process_data(request)
            elif operation == "transform_data":
                result = self._transform_data(request)
            elif operation == "validate_data":
                result = self._validate_data(request)
            elif operation == "normalize_data":
                result = self._normalize_data(request)
            elif operation == "aggregate_data":
                result = self._aggregate_data(request)
            else:
                return ModuleResponse(
                    success=False,
                    error=f"Unsupported operation: {operation}",
                    request_id=request.request_id
                )
                
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModuleResponse(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error executing processor operation {operation}: {str(e)}")
            
            return ModuleResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                request_id=request.request_id
            )
            
    def _process_data(self, request: ModuleRequest) -> Any:
        """Process data using underlying module"""
        method_name = self._find_method(['process_data', 'process', 'transform'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("Data processing not available in underlying module")
        
    def _transform_data(self, request: ModuleRequest) -> Any:
        """Transform data"""
        method_name = self._find_method(['transform_data', 'transform'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("Data transformation not available in underlying module")
        
    def _validate_data(self, request: ModuleRequest) -> Any:
        """Validate data"""
        method_name = self._find_method(['validate_data', 'validate'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        return {"valid": True, "errors": []}
        
    def _normalize_data(self, request: ModuleRequest) -> Any:
        """Normalize data"""
        method_name = self._find_method(['normalize_data', 'normalize'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("Data normalization not available in underlying module")
        
    def _aggregate_data(self, request: ModuleRequest) -> Any:
        """Aggregate data"""
        method_name = self._find_method(['aggregate_data', 'aggregate'])
        if method_name:
            method = getattr(self._module, method_name)
            return self._call_with_appropriate_params(method, request.parameters)
        raise NotImplementedError("Data aggregation not available in underlying module")
        
    def _find_method(self, method_names: List[str]) -> Optional[str]:
        """Find available method from list of possibilities"""
        for name in method_names:
            if hasattr(self._module, name):
                return name
        return None
        
    def _call_with_appropriate_params(self, method, parameters: Dict[str, Any]) -> Any:
        """Call method with appropriate parameters based on its signature"""
        sig = inspect.signature(method)
        filtered_params = {}
        
        for param_name in sig.parameters:
            if param_name in parameters:
                filtered_params[param_name] = parameters[param_name]
                
        return method(**filtered_params)
        
    def cleanup(self) -> None:
        """Cleanup processor resources"""
        if hasattr(self._module, 'cleanup'):
            self._module.cleanup()


class ModuleAdapterFactory:
    """Factory class for creating appropriate module adapters"""
    
    @staticmethod
    def create_adapter(module: Any, config: Optional[ModuleConfig] = None) -> ModuleAdapter:
        """
        Create appropriate adapter for the given module.
        
        Args:
            module: Module instance to wrap
            config: Optional configuration for the adapter
            
        Returns:
            Appropriate ModuleAdapter subclass
            
        Raises:
            ValueError: If module type cannot be determined
        """
        module_class_name = module.__class__.__name__.lower()
        
        # Determine module type based on class name patterns
        if any(pattern in module_class_name for pattern in ['provider', 'datasource', 'source']):
            return DataSourceAdapter(module, config)
        elif any(pattern in module_class_name for pattern in ['calculator', 'engine', 'calculation']):
            return CalculationEngineAdapter(module, config)
        elif any(pattern in module_class_name for pattern in ['processor', 'manager', 'handler']):
            return ProcessorAdapter(module, config)
        else:
            # Default to processor adapter for unknown types
            logger.warning(f"Unknown module type for {module_class_name}, defaulting to ProcessorAdapter")
            return ProcessorAdapter(module, config)
    
    @staticmethod
    def create_typed_adapter(
        module: Any, 
        adapter_type: ModuleType, 
        config: Optional[ModuleConfig] = None
    ) -> ModuleAdapter:
        """
        Create adapter of specific type.
        
        Args:
            module: Module instance to wrap
            adapter_type: Specific adapter type to create
            config: Optional configuration for the adapter
            
        Returns:
            Appropriate ModuleAdapter subclass
            
        Raises:
            ValueError: If adapter type is not supported
        """
        if adapter_type == ModuleType.DATA_SOURCE:
            return DataSourceAdapter(module, config)
        elif adapter_type == ModuleType.CALCULATION_ENGINE:
            return CalculationEngineAdapter(module, config)
        elif adapter_type == ModuleType.PROCESSOR:
            return ProcessorAdapter(module, config)
        else:
            raise ValueError(f"Unsupported adapter type: {adapter_type}")