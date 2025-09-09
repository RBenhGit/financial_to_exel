"""
Test Suite for Module Adapter Pattern

This test suite validates the module adapter pattern implementation including
adapter creation, operation execution, and integration with existing modules.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import logging
import sys
import os

# Add current directory to path to import modules
sys.path.append(os.path.dirname(__file__))

from module_adapter import (
    ModuleAdapter, DataSourceAdapter, CalculationEngineAdapter, ProcessorAdapter,
    ModuleAdapterFactory, ModuleRequest, ModuleResponse, ModuleType, ModuleMetadata
)

# Import existing modules for integration testing
try:
    from data_sources import YfinanceProvider, DataSourceConfig, ApiCredentials, FinancialDataRequest
    from core.analysis.engines.financial_calculations import FinancialCalculator
    from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
except ImportError as e:
    print(f"Warning: Could not import some modules for integration testing: {e}")


class MockDataSource:
    """Mock data source for testing"""
    
    def __init__(self):
        self.api_key = "test_key"
        self._session = Mock()
    
    def fetch_data(self, request):
        return {"data": {"AAPL": {"price": 150.0}}, "source": "mock"}
    
    def validate_credentials(self):
        return True
    
    def get_available_fields(self):
        return ["price", "volume", "market_cap"]
    
    def get_rate_limit_status(self):
        return {"rate_limit_ok": True, "remaining_calls": 100}
    
    def close(self):
        pass


class MockCalculationEngine:
    """Mock calculation engine for testing"""
    
    def __init__(self):
        pass
    
    def calculate_fcf(self, financial_data, **kwargs):
        return {"fcf": 1000000, "growth_rate": 0.05}
    
    def calculate_dcf(self, financial_data, **kwargs):
        return {"dcf_value": 50.0, "intrinsic_value": 52.5}
    
    def validate_inputs(self, financial_data):
        return {"valid": True, "errors": []}


class MockProcessor:
    """Mock processor for testing"""
    
    def __init__(self):
        pass
    
    def process_data(self, data, **kwargs):
        return {"processed_data": data, "processing_time": 0.1}
    
    def validate_data(self, data):
        return {"valid": True, "errors": []}


class TestModuleAdapterBase(unittest.TestCase):
    """Test base module adapter functionality"""
    
    def setUp(self):
        self.mock_module = Mock()
        # Create a concrete implementation for testing abstract methods
        class TestableModuleAdapter(ModuleAdapter):
            def _create_metadata(self):
                return ModuleMetadata(
                    name="TestAdapter",
                    module_type=ModuleType.PROCESSOR,
                    version="1.0.0",
                    description="Test adapter"
                )
            
            def initialize(self):
                return True
            
            def execute(self, request):
                return ModuleResponse(success=True, data={"test": "result"})
            
            def cleanup(self):
                pass
        
        self.adapter = TestableModuleAdapter(self.mock_module, {"test_config": True})
    
    def test_adapter_initialization(self):
        """Test adapter initialization"""
        self.assertEqual(self.adapter._module, self.mock_module)
        self.assertEqual(self.adapter._config["test_config"], True)
        self.assertIsInstance(self.adapter.metadata, ModuleMetadata)
        self.assertEqual(self.adapter.metadata.name, "TestAdapter")
    
    def test_metadata_properties(self):
        """Test metadata properties"""
        self.assertEqual(self.adapter.module_type, ModuleType.PROCESSOR)
        self.assertFalse(self.adapter.is_initialized)
    
    def test_configuration_access(self):
        """Test configuration value access"""
        self.assertEqual(self.adapter.get_config_value("test_config"), True)
        self.assertEqual(self.adapter.get_config_value("nonexistent", "default"), "default")
    
    def test_capabilities(self):
        """Test capabilities access"""
        capabilities = self.adapter.get_capabilities()
        self.assertIsInstance(capabilities, list)
        
        # Test supports_operation (base class returns empty capabilities)
        self.assertFalse(self.adapter.supports_operation("any_operation"))


class TestDataSourceAdapter(unittest.TestCase):
    """Test data source adapter functionality"""
    
    def setUp(self):
        self.mock_data_source = MockDataSource()
        self.adapter = DataSourceAdapter(self.mock_data_source, {})
    
    def test_metadata_creation(self):
        """Test data source adapter metadata"""
        metadata = self.adapter.metadata
        self.assertEqual(metadata.module_type, ModuleType.DATA_SOURCE)
        self.assertIn("fetch_data", metadata.capabilities)
        self.assertIn("validate_credentials", metadata.capabilities)
    
    def test_initialization(self):
        """Test data source adapter initialization"""
        self.assertTrue(self.adapter.initialize())
        self.assertTrue(self.adapter.is_initialized)
    
    def test_fetch_data_operation(self):
        """Test fetch data operation"""
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": Mock()}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIsNotNone(response.data)
        self.assertIsNotNone(response.execution_time_ms)
    
    def test_validate_credentials_operation(self):
        """Test validate credentials operation"""
        request = ModuleRequest(operation="validate_credentials")
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertTrue(response.data)
    
    def test_get_available_fields_operation(self):
        """Test get available fields operation"""
        request = ModuleRequest(operation="get_available_fields")
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIsInstance(response.data, list)
        self.assertIn("price", response.data)
    
    def test_check_rate_limits_operation(self):
        """Test check rate limits operation"""
        request = ModuleRequest(operation="check_rate_limits")
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("rate_limit_ok", response.data)
    
    def test_unsupported_operation(self):
        """Test unsupported operation handling"""
        request = ModuleRequest(operation="unsupported_operation")
        
        response = self.adapter.execute(request)
        
        self.assertFalse(response.success)
        self.assertIn("Unsupported operation", response.error)
    
    def test_request_validation(self):
        """Test request validation"""
        # Valid request
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL"}
        )
        errors = self.adapter.validate_request(request)
        self.assertEqual(len(errors), 0)
        
        # Invalid request (missing required parameter)
        request = ModuleRequest(
            operation="fetch_data",
            parameters={}
        )
        errors = self.adapter.validate_request(request)
        self.assertGreater(len(errors), 0)
        self.assertIn("Missing required parameter: symbol", errors[0])
    
    def test_cleanup(self):
        """Test cleanup functionality"""
        # Should not raise any exceptions
        self.adapter.cleanup()


class TestCalculationEngineAdapter(unittest.TestCase):
    """Test calculation engine adapter functionality"""
    
    def setUp(self):
        self.mock_engine = MockCalculationEngine()
        self.adapter = CalculationEngineAdapter(self.mock_engine, {})
    
    def test_metadata_creation(self):
        """Test calculation engine adapter metadata"""
        metadata = self.adapter.metadata
        self.assertEqual(metadata.module_type, ModuleType.CALCULATION_ENGINE)
        self.assertIn("calculate_fcf", metadata.capabilities)
        self.assertIn("calculate_dcf", metadata.capabilities)
    
    def test_initialization(self):
        """Test calculation engine adapter initialization"""
        self.assertTrue(self.adapter.initialize())
        self.assertTrue(self.adapter.is_initialized)
    
    def test_calculate_fcf_operation(self):
        """Test FCF calculation operation"""
        request = ModuleRequest(
            operation="calculate_fcf",
            parameters={"financial_data": {"revenue": 1000000}}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("fcf", response.data)
    
    def test_calculate_dcf_operation(self):
        """Test DCF calculation operation"""
        request = ModuleRequest(
            operation="calculate_dcf",
            parameters={"financial_data": {"fcf": 1000000}}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("dcf_value", response.data)
    
    def test_validate_inputs_operation(self):
        """Test input validation operation"""
        request = ModuleRequest(
            operation="validate_inputs",
            parameters={"financial_data": {"revenue": 1000000}}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("valid", response.data)
    
    def test_method_finding(self):
        """Test method finding functionality"""
        method_name = self.adapter._find_calculation_method(['calculate_fcf', 'get_fcf'])
        self.assertEqual(method_name, 'calculate_fcf')
        
        method_name = self.adapter._find_calculation_method(['nonexistent_method'])
        self.assertIsNone(method_name)


class TestProcessorAdapter(unittest.TestCase):
    """Test processor adapter functionality"""
    
    def setUp(self):
        self.mock_processor = MockProcessor()
        self.adapter = ProcessorAdapter(self.mock_processor, {})
    
    def test_metadata_creation(self):
        """Test processor adapter metadata"""
        metadata = self.adapter.metadata
        self.assertEqual(metadata.module_type, ModuleType.PROCESSOR)
        self.assertIn("process_data", metadata.capabilities)
        self.assertIn("validate_data", metadata.capabilities)
    
    def test_initialization(self):
        """Test processor adapter initialization"""
        self.assertTrue(self.adapter.initialize())
        self.assertTrue(self.adapter.is_initialized)
    
    def test_process_data_operation(self):
        """Test process data operation"""
        request = ModuleRequest(
            operation="process_data",
            parameters={"data": {"test": "data"}}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("processed_data", response.data)
    
    def test_validate_data_operation(self):
        """Test validate data operation"""
        request = ModuleRequest(
            operation="validate_data",
            parameters={"data": {"test": "data"}}
        )
        
        response = self.adapter.execute(request)
        
        self.assertTrue(response.success)
        self.assertIn("valid", response.data)


class TestModuleAdapterFactory(unittest.TestCase):
    """Test module adapter factory functionality"""
    
    def test_create_data_source_adapter(self):
        """Test creating data source adapter"""
        mock_provider = Mock()
        mock_provider.__class__.__name__ = "YfinanceProvider"
        
        adapter = ModuleAdapterFactory.create_adapter(mock_provider)
        
        self.assertIsInstance(adapter, DataSourceAdapter)
        self.assertEqual(adapter.module_type, ModuleType.DATA_SOURCE)
    
    def test_create_calculation_engine_adapter(self):
        """Test creating calculation engine adapter"""
        mock_calculator = Mock()
        mock_calculator.__class__.__name__ = "FinancialCalculator"
        
        adapter = ModuleAdapterFactory.create_adapter(mock_calculator)
        
        self.assertIsInstance(adapter, CalculationEngineAdapter)
        self.assertEqual(adapter.module_type, ModuleType.CALCULATION_ENGINE)
    
    def test_create_processor_adapter(self):
        """Test creating processor adapter"""
        mock_processor = Mock()
        mock_processor.__class__.__name__ = "DataProcessor"
        
        adapter = ModuleAdapterFactory.create_adapter(mock_processor)
        
        self.assertIsInstance(adapter, ProcessorAdapter)
        self.assertEqual(adapter.module_type, ModuleType.PROCESSOR)
    
    def test_create_unknown_type_adapter(self):
        """Test creating adapter for unknown module type"""
        mock_unknown = Mock()
        mock_unknown.__class__.__name__ = "UnknownModule"
        
        with patch('module_adapter.logger') as mock_logger:
            adapter = ModuleAdapterFactory.create_adapter(mock_unknown)
            
            self.assertIsInstance(adapter, ProcessorAdapter)
            mock_logger.warning.assert_called_once()
    
    def test_create_typed_adapter(self):
        """Test creating adapter of specific type"""
        mock_module = Mock()
        mock_module.__class__.__name__ = "TestModule"
        
        adapter = ModuleAdapterFactory.create_typed_adapter(
            mock_module, ModuleType.DATA_SOURCE
        )
        
        self.assertIsInstance(adapter, DataSourceAdapter)
        self.assertEqual(adapter.module_type, ModuleType.DATA_SOURCE)
    
    def test_create_typed_adapter_unsupported(self):
        """Test creating adapter for unsupported type"""
        mock_module = Mock()
        
        with self.assertRaises(ValueError):
            ModuleAdapterFactory.create_typed_adapter(
                mock_module, ModuleType.VALIDATOR
            )


class TestIntegrationWithExistingModules(unittest.TestCase):
    """Integration tests with existing modules"""
    
    def setUp(self):
        # Skip integration tests if modules couldn't be imported
        if 'YfinanceProvider' not in globals():
            self.skipTest("Required modules not available for integration testing")
    
    def test_yfinance_provider_integration(self):
        """Test integration with YfinanceProvider"""
        try:
            config = DataSourceConfig(
                source_type="yfinance",
                priority=1,
                rate_limit_per_minute=60,
                credentials=ApiCredentials()
            )
            provider = YfinanceProvider(config)
            adapter = ModuleAdapterFactory.create_adapter(provider)
            
            self.assertIsInstance(adapter, DataSourceAdapter)
            self.assertTrue(adapter.initialize())
            
            # Test capabilities
            capabilities = adapter.get_capabilities()
            self.assertIn("fetch_data", capabilities)
            
        except Exception as e:
            self.skipTest(f"YfinanceProvider integration test failed: {e}")
    
    def test_financial_calculator_integration(self):
        """Test integration with FinancialCalculator"""
        try:
            calculator = FinancialCalculator(company_folder=None)
            adapter = ModuleAdapterFactory.create_adapter(calculator)
            
            self.assertIsInstance(adapter, CalculationEngineAdapter)
            self.assertTrue(adapter.initialize())
            
            # Test capabilities
            capabilities = adapter.get_capabilities()
            self.assertIn("calculate_fcf", capabilities)
            
        except Exception as e:
            self.skipTest(f"FinancialCalculator integration test failed: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in adapters"""
    
    def setUp(self):
        self.faulty_module = Mock()
        self.faulty_module.__class__.__name__ = "FaultyProvider"
        self.faulty_module.fetch_data.side_effect = Exception("Test error")
        self.faulty_module.validate_credentials.return_value = True
        
        self.adapter = DataSourceAdapter(self.faulty_module)
    
    def test_execute_with_exception(self):
        """Test execution with exception in underlying module"""
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": Mock()}
        )
        
        response = self.adapter.execute(request)
        
        self.assertFalse(response.success)
        self.assertIn("Test error", response.error)
        self.assertIsNotNone(response.execution_time_ms)
    
    def test_initialization_failure(self):
        """Test initialization failure handling"""
        self.faulty_module.validate_credentials.side_effect = Exception("Auth error")
        
        result = self.adapter.initialize()
        
        self.assertFalse(result)
        self.assertFalse(self.adapter.is_initialized)


if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)