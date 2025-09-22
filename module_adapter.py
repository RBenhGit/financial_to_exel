"""
Module Adapter Pattern Implementation
=====================================

This module provides adapter pattern implementations for integrating various
components of the financial analysis system. It enables unified interfaces
for different types of modules and services.

Key Components:
- ModuleAdapter base class for creating adapters
- Specialized adapters for data sources, calculation engines, and processors
- Request/Response pattern for standardized communication
- Factory pattern for adapter creation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """Types of modules that can be adapted"""
    DATA_SOURCE = "data_source"
    CALCULATION_ENGINE = "calculation_engine"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"
    VALIDATOR = "validator"


@dataclass
class ModuleMetadata:
    """Metadata for module operations"""
    module_type: ModuleType
    module_name: str
    version: str = "1.0.0"
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleRequest:
    """Standardized request for module operations"""
    operation: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[ModuleMetadata] = None
    request_id: Optional[str] = None


@dataclass
class ModuleResponse:
    """Standardized response from module operations"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    metadata: Optional[ModuleMetadata] = None
    request_id: Optional[str] = None
    execution_time: Optional[float] = None


class ModuleAdapter(ABC):
    """
    Base adapter class for module integration
    """

    def __init__(self, module_instance: Any, module_type: ModuleType):
        """
        Initialize the adapter

        Args:
            module_instance: The actual module instance to adapt
            module_type: Type of module being adapted
        """
        self.module_instance = module_instance
        self.module_type = module_type
        self.metadata = ModuleMetadata(
            module_type=module_type,
            module_name=module_instance.__class__.__name__
        )

    @abstractmethod
    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """
        Execute a module operation

        Args:
            request: The request to execute

        Returns:
            ModuleResponse with results
        """
        pass

    def validate_request(self, request: ModuleRequest) -> bool:
        """
        Validate a module request

        Args:
            request: Request to validate

        Returns:
            True if valid, False otherwise
        """
        return request.operation is not None

    def create_response(
        self,
        success: bool,
        data: Any = None,
        error_message: Optional[str] = None,
        request: Optional[ModuleRequest] = None,
        execution_time: Optional[float] = None
    ) -> ModuleResponse:
        """
        Create a standardized response

        Args:
            success: Whether operation succeeded
            data: Response data
            error_message: Error message if failed
            request: Original request
            execution_time: Execution time in seconds

        Returns:
            ModuleResponse
        """
        return ModuleResponse(
            success=success,
            data=data,
            error_message=error_message,
            metadata=self.metadata,
            request_id=request.request_id if request else None,
            execution_time=execution_time
        )


class DataSourceAdapter(ModuleAdapter):
    """
    Adapter for data source modules
    """

    def __init__(self, data_source_instance: Any):
        super().__init__(data_source_instance, ModuleType.DATA_SOURCE)

    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute data source operations"""
        start_time = datetime.now()

        try:
            if not self.validate_request(request):
                return self.create_response(
                    False,
                    error_message="Invalid request",
                    request=request
                )

            operation = request.operation.lower()
            params = request.parameters

            if operation == "fetch_data":
                result = self._fetch_data(params)
            elif operation == "get_market_data":
                result = self._get_market_data(params)
            elif operation == "get_historical_data":
                result = self._get_historical_data(params)
            else:
                return self.create_response(
                    False,
                    error_message=f"Unsupported operation: {operation}",
                    request=request
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            return self.create_response(
                True,
                data=result,
                request=request,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Data source adapter error: {e}")
            return self.create_response(
                False,
                error_message=str(e),
                request=request,
                execution_time=execution_time
            )

    def _fetch_data(self, params: Dict[str, Any]) -> Any:
        """Fetch data using the adapted data source"""
        if hasattr(self.module_instance, 'fetch_data'):
            return self.module_instance.fetch_data(**params)
        elif hasattr(self.module_instance, 'get_data'):
            return self.module_instance.get_data(**params)
        else:
            raise AttributeError("Data source does not have a supported fetch method")

    def _get_market_data(self, params: Dict[str, Any]) -> Any:
        """Get market data"""
        if hasattr(self.module_instance, 'get_market_data'):
            return self.module_instance.get_market_data(**params)
        else:
            return self._fetch_data(params)

    def _get_historical_data(self, params: Dict[str, Any]) -> Any:
        """Get historical data"""
        if hasattr(self.module_instance, 'get_historical_data'):
            return self.module_instance.get_historical_data(**params)
        else:
            return self._fetch_data(params)


class CalculationEngineAdapter(ModuleAdapter):
    """
    Adapter for calculation engine modules
    """

    def __init__(self, calculation_engine_instance: Any):
        super().__init__(calculation_engine_instance, ModuleType.CALCULATION_ENGINE)

    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute calculation engine operations"""
        start_time = datetime.now()

        try:
            if not self.validate_request(request):
                return self.create_response(
                    False,
                    error_message="Invalid request",
                    request=request
                )

            operation = request.operation.lower()
            params = request.parameters

            if operation == "calculate_dcf":
                result = self._calculate_dcf(params)
            elif operation == "calculate_ddm":
                result = self._calculate_ddm(params)
            elif operation == "calculate_pb":
                result = self._calculate_pb(params)
            elif operation == "calculate_fcf":
                result = self._calculate_fcf(params)
            else:
                return self.create_response(
                    False,
                    error_message=f"Unsupported operation: {operation}",
                    request=request
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            return self.create_response(
                True,
                data=result,
                request=request,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Calculation engine adapter error: {e}")
            return self.create_response(
                False,
                error_message=str(e),
                request=request,
                execution_time=execution_time
            )

    def _calculate_dcf(self, params: Dict[str, Any]) -> Any:
        """Calculate DCF valuation"""
        if hasattr(self.module_instance, 'calculate_dcf_projections'):
            return self.module_instance.calculate_dcf_projections(**params)
        elif hasattr(self.module_instance, 'calculate_dcf_valuation'):
            return self.module_instance.calculate_dcf_valuation(**params)
        else:
            raise AttributeError("Engine does not support DCF calculations")

    def _calculate_ddm(self, params: Dict[str, Any]) -> Any:
        """Calculate DDM valuation"""
        if hasattr(self.module_instance, 'calculate_ddm_valuation'):
            return self.module_instance.calculate_ddm_valuation(**params)
        else:
            raise AttributeError("Engine does not support DDM calculations")

    def _calculate_pb(self, params: Dict[str, Any]) -> Any:
        """Calculate P/B analysis"""
        if hasattr(self.module_instance, 'calculate_pb_analysis'):
            return self.module_instance.calculate_pb_analysis(**params)
        else:
            raise AttributeError("Engine does not support P/B calculations")

    def _calculate_fcf(self, params: Dict[str, Any]) -> Any:
        """Calculate FCF"""
        if hasattr(self.module_instance, 'calculate_fcf'):
            return self.module_instance.calculate_fcf(**params)
        else:
            raise AttributeError("Engine does not support FCF calculations")


class ProcessorAdapter(ModuleAdapter):
    """
    Adapter for data processor modules
    """

    def __init__(self, processor_instance: Any):
        super().__init__(processor_instance, ModuleType.PROCESSOR)

    def execute(self, request: ModuleRequest) -> ModuleResponse:
        """Execute processor operations"""
        start_time = datetime.now()

        try:
            if not self.validate_request(request):
                return self.create_response(
                    False,
                    error_message="Invalid request",
                    request=request
                )

            operation = request.operation.lower()
            params = request.parameters

            if operation == "process_data":
                result = self._process_data(params)
            elif operation == "validate_data":
                result = self._validate_data(params)
            elif operation == "transform_data":
                result = self._transform_data(params)
            else:
                return self.create_response(
                    False,
                    error_message=f"Unsupported operation: {operation}",
                    request=request
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            return self.create_response(
                True,
                data=result,
                request=request,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Processor adapter error: {e}")
            return self.create_response(
                False,
                error_message=str(e),
                request=request,
                execution_time=execution_time
            )

    def _process_data(self, params: Dict[str, Any]) -> Any:
        """Process data using the adapted processor"""
        if hasattr(self.module_instance, 'process_data'):
            return self.module_instance.process_data(**params)
        elif hasattr(self.module_instance, 'process'):
            return self.module_instance.process(**params)
        else:
            raise AttributeError("Processor does not have a supported process method")

    def _validate_data(self, params: Dict[str, Any]) -> Any:
        """Validate data"""
        if hasattr(self.module_instance, 'validate_data'):
            return self.module_instance.validate_data(**params)
        elif hasattr(self.module_instance, 'validate'):
            return self.module_instance.validate(**params)
        else:
            raise AttributeError("Processor does not support validation")

    def _transform_data(self, params: Dict[str, Any]) -> Any:
        """Transform data"""
        if hasattr(self.module_instance, 'transform_data'):
            return self.module_instance.transform_data(**params)
        elif hasattr(self.module_instance, 'transform'):
            return self.module_instance.transform(**params)
        else:
            raise AttributeError("Processor does not support transformation")


class ModuleAdapterFactory:
    """
    Factory for creating module adapters
    """

    @staticmethod
    def create_adapter(
        module_instance: Any,
        module_type: Optional[ModuleType] = None
    ) -> ModuleAdapter:
        """
        Create an appropriate adapter for a module instance

        Args:
            module_instance: The module instance to adapt
            module_type: Optional module type hint

        Returns:
            Appropriate ModuleAdapter subclass

        Raises:
            ValueError: If module type cannot be determined or is unsupported
        """
        # Auto-detect module type if not provided
        if module_type is None:
            module_type = ModuleAdapterFactory._detect_module_type(module_instance)

        # Create appropriate adapter
        if module_type == ModuleType.DATA_SOURCE:
            return DataSourceAdapter(module_instance)
        elif module_type == ModuleType.CALCULATION_ENGINE:
            return CalculationEngineAdapter(module_instance)
        elif module_type == ModuleType.PROCESSOR:
            return ProcessorAdapter(module_instance)
        else:
            raise ValueError(f"Unsupported module type: {module_type}")

    @staticmethod
    def _detect_module_type(module_instance: Any) -> ModuleType:
        """
        Detect the module type based on available methods

        Args:
            module_instance: Module instance to analyze

        Returns:
            Detected ModuleType

        Raises:
            ValueError: If module type cannot be determined
        """
        class_name = module_instance.__class__.__name__.lower()

        # Check for data source indicators
        data_source_indicators = ['fetch_data', 'get_data', 'get_market_data']
        if any(hasattr(module_instance, method) for method in data_source_indicators):
            return ModuleType.DATA_SOURCE

        # Check for calculation engine indicators
        calc_indicators = ['calculate_dcf', 'calculate_ddm', 'calculate_pb']
        if any(hasattr(module_instance, method) for method in calc_indicators):
            return ModuleType.CALCULATION_ENGINE

        # Check for processor indicators
        processor_indicators = ['process_data', 'process', 'transform_data']
        if any(hasattr(module_instance, method) for method in processor_indicators):
            return ModuleType.PROCESSOR

        # Check class name patterns
        if any(keyword in class_name for keyword in ['source', 'provider', 'fetcher']):
            return ModuleType.DATA_SOURCE
        elif any(keyword in class_name for keyword in ['calculator', 'engine', 'valuator']):
            return ModuleType.CALCULATION_ENGINE
        elif any(keyword in class_name for keyword in ['processor', 'manager', 'handler']):
            return ModuleType.PROCESSOR

        raise ValueError(f"Cannot determine module type for {module_instance.__class__.__name__}")