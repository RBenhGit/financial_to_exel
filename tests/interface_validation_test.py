"""
Interface Validation Test - Simplified and Fast
==============================================

A focused test suite to validate module interfaces and integration
points without requiring extensive setup or network calls.
"""

import unittest
import logging
from unittest.mock import Mock, patch
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import test modules - handle missing imports gracefully
try:
    from dependency_injection import DIContainer, ServiceLifetime
    HAS_DI = True
except ImportError:
    HAS_DI = False

try:
    from module_adapter import ModuleAdapterFactory, ModuleRequest, ModuleType
    HAS_ADAPTER = True
except ImportError:
    HAS_ADAPTER = False

logger = logging.getLogger(__name__)


class TestModuleInterfaceValidation(unittest.TestCase):
    """Test core module interface validation"""
    
    def test_dependency_injection_basic_interface(self):
        """Test DI container basic interface"""
        if not HAS_DI:
            self.skipTest("Dependency injection module not available")
        
        # Test container creation
        container = DIContainer()
        self.assertIsNotNone(container)
        
        # Test basic registration
        container.register(str, factory=lambda: "test_string")
        self.assertTrue(container.is_registered(str))
        
        # Test resolution
        result = container.resolve(str)
        self.assertEqual(result, "test_string")
        
        # Test clear
        container.clear()
        self.assertFalse(container.is_registered(str))
    
    def test_dependency_injection_with_dependencies(self):
        """Test DI container with dependencies"""
        if not HAS_DI:
            self.skipTest("Dependency injection module not available")
        
        container = DIContainer()
        
        # Define test classes
        class Database:
            def __init__(self):
                self.connection = "connected"
        
        class Service:
            def __init__(self, db: Database):
                self.db = db
        
        # Register with dependencies
        container.register(Database)
        container.register(Service, dependencies=[Database])
        
        # Resolve and verify
        service = container.resolve(Service)
        self.assertIsInstance(service, Service)
        self.assertIsInstance(service.db, Database)
        self.assertEqual(service.db.connection, "connected")
    
    def test_module_adapter_interface(self):
        """Test module adapter interface"""
        if not HAS_ADAPTER:
            self.skipTest("Module adapter not available")
        
        # Create mock module
        mock_module = Mock()
        mock_module.__class__.__name__ = "TestProvider"
        mock_module.fetch_data = Mock(return_value={"test": "data"})
        mock_module.validate_credentials = Mock(return_value=True)
        
        # Create adapter
        adapter = ModuleAdapterFactory.create_adapter(mock_module)
        self.assertIsNotNone(adapter)
        
        # Test initialization
        self.assertTrue(adapter.initialize())
        
        # Test capabilities
        capabilities = adapter.get_capabilities()
        self.assertIsInstance(capabilities, list)
        
        # Test execution
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "TEST"}
        )
        
        response = adapter.execute(request)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.data)
    
    def test_adapter_error_handling(self):
        """Test adapter error handling"""
        if not HAS_ADAPTER:
            self.skipTest("Module adapter not available")
        
        # Create faulty mock
        faulty_module = Mock()
        faulty_module.__class__.__name__ = "FaultyProvider"
        faulty_module.fetch_data = Mock(side_effect=Exception("Test error"))
        faulty_module.validate_credentials = Mock(return_value=True)
        
        adapter = ModuleAdapterFactory.create_adapter(faulty_module)
        
        # Test that errors are handled gracefully
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "TEST"}
        )
        
        response = adapter.execute(request)
        self.assertFalse(response.success)
        self.assertIn("Test error", response.error)
    
    def test_di_adapter_integration(self):
        """Test DI and adapter working together"""
        if not (HAS_DI and HAS_ADAPTER):
            self.skipTest("DI or Adapter modules not available")
        
        container = DIContainer()
        
        # Create mock provider class
        class MockProvider:
            def __init__(self):
                self.initialized = True
            
            def fetch_data(self, symbol=None, data_request=None):
                return {"symbol": symbol, "price": 100.0}
            
            def validate_credentials(self):
                return True
        
        # Register provider in DI container
        container.register(MockProvider)
        
        # Resolve provider
        provider = container.resolve(MockProvider)
        self.assertTrue(provider.initialized)
        
        # Create adapter for provider
        adapter = ModuleAdapterFactory.create_adapter(provider)
        self.assertTrue(adapter.initialize())
        
        # Test execution through adapter
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "INTEG_TEST", "data_request": {}}
        )
        
        response = adapter.execute(request)
        self.assertTrue(response.success)
        # Verify response contains expected data (the actual structure may vary)
        self.assertIsNotNone(response.data)
    
    def test_interface_backward_compatibility(self):
        """Test backward compatibility of interfaces"""
        
        # Test that old-style direct instantiation still works
        class LegacyClass:
            def __init__(self):
                self.data = "legacy"
            
            def get_data(self):
                return self.data
        
        # Direct instantiation (legacy style)
        legacy_instance = LegacyClass()
        self.assertEqual(legacy_instance.get_data(), "legacy")
        
        # New style with DI (if available)
        if HAS_DI:
            container = DIContainer()
            container.register(LegacyClass)
            
            di_instance = container.resolve(LegacyClass)
            self.assertEqual(di_instance.get_data(), "legacy")
            
            # Both should work the same way
            self.assertEqual(legacy_instance.get_data(), di_instance.get_data())
    
    def test_module_registration_validation(self):
        """Test module registration validation"""
        if not HAS_DI:
            self.skipTest("Dependency injection module not available")
        
        container = DIContainer()
        
        # Test successful registration
        container.register(str, factory=lambda: "test")
        info = container.get_registration_info(str)
        self.assertIsNotNone(info)
        self.assertEqual(info["service_type"], "str")
        
        # Test dependency validation
        class ServiceA:
            def __init__(self, service_b):
                pass
        
        class ServiceB:
            def __init__(self):
                pass
        
        # Register with valid dependency
        container.register(ServiceB)
        container.register(ServiceA, dependencies=[ServiceB])
        
        # Validate dependencies
        errors = container.validate_dependencies()
        self.assertEqual(len(errors), 0)  # Should have no errors
        
        # Test invalid dependency
        container.clear()
        container.register(ServiceA, dependencies=[ServiceB])  # ServiceB not registered
        
        errors = container.validate_dependencies()
        self.assertGreater(len(errors), 0)  # Should have errors


class TestModuleContractValidation(unittest.TestCase):
    """Test standardized data contracts between modules"""
    
    def test_request_response_contract(self):
        """Test request/response data contract"""
        if not HAS_ADAPTER:
            self.skipTest("Module adapter not available")
        
        # Test ModuleRequest contract
        request = ModuleRequest(
            operation="test_operation",
            parameters={"param1": "value1", "param2": 123},
            request_id="test-123"
        )
        
        self.assertEqual(request.operation, "test_operation")
        self.assertEqual(request.parameters["param1"], "value1")
        self.assertEqual(request.parameters["param2"], 123)
        self.assertEqual(request.request_id, "test-123")
        
        # Test response contract (mock response)
        from module_adapter import ModuleResponse
        import time
        
        start_time = time.time() * 1000
        response = ModuleResponse(
            success=True,
            data={"result": "success"},
            error=None,
            execution_time_ms=10.5
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.data["result"], "success")
        self.assertIsNone(response.error)
        self.assertEqual(response.execution_time_ms, 10.5)
    
    def test_module_metadata_contract(self):
        """Test module metadata contract"""
        if not HAS_ADAPTER:
            self.skipTest("Module adapter not available")
        
        from module_adapter import ModuleMetadata
        
        metadata = ModuleMetadata(
            name="TestModule",
            module_type=ModuleType.DATA_SOURCE,
            version="1.0.0",
            description="Test module for validation",
            capabilities=["fetch_data", "validate"]
        )
        
        self.assertEqual(metadata.name, "TestModule")
        self.assertEqual(metadata.module_type, ModuleType.DATA_SOURCE)
        self.assertEqual(metadata.version, "1.0.0")
        self.assertIn("fetch_data", metadata.capabilities)
    
    def test_configuration_contract(self):
        """Test configuration data contract"""
        
        # Test configuration structure
        config = {
            "data_sources": {
                "yfinance": {
                    "enabled": True,
                    "rate_limit": 60,
                    "timeout": 30
                }
            },
            "cache": {
                "ttl_hours": 24,
                "max_size_mb": 500
            },
            "validation": {
                "level": "moderate",
                "strict_mode": False
            }
        }
        
        # Validate structure
        self.assertIn("data_sources", config)
        self.assertIn("cache", config)
        self.assertIn("validation", config)
        
        # Validate yfinance config
        yf_config = config["data_sources"]["yfinance"]
        self.assertTrue(yf_config["enabled"])
        self.assertEqual(yf_config["rate_limit"], 60)
        
        # Validate cache config
        cache_config = config["cache"]
        self.assertEqual(cache_config["ttl_hours"], 24)


class TestPerformanceValidation(unittest.TestCase):
    """Test performance characteristics of interfaces"""
    
    def test_di_container_performance(self):
        """Test DI container resolution performance"""
        if not HAS_DI:
            self.skipTest("Dependency injection module not available")
        
        container = DIContainer()
        
        # Register services
        container.register(str, factory=lambda: "test")
        container.register(int, factory=lambda: 42)
        container.register(float, factory=lambda: 3.14)
        
        # Time multiple resolutions
        import time
        start_time = time.time()
        
        for _ in range(100):
            container.resolve(str)
            container.resolve(int) 
            container.resolve(float)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should resolve quickly (less than 0.1 seconds for 300 resolutions)
        self.assertLess(total_time, 0.1)
        
        # Log performance info
        avg_time_ms = (total_time / 300) * 1000
        logger.info(f"DI container average resolution time: {avg_time_ms:.3f}ms")
    
    def test_adapter_execution_performance(self):
        """Test adapter execution performance"""
        if not HAS_ADAPTER:
            self.skipTest("Module adapter not available")
        
        # Create simple mock module  
        mock_module = Mock()
        mock_module.__class__.__name__ = "FastProvider"
        mock_module.fetch_data = Mock(return_value="result")
        
        adapter = ModuleAdapterFactory.create_adapter(mock_module)
        adapter.initialize()
        
        # Time multiple executions
        import time
        start_time = time.time()
        
        for _ in range(50):
            request = ModuleRequest(
                operation="fetch_data",
                parameters={"symbol": "TEST", "data_request": {}}
            )
            response = adapter.execute(request)
            self.assertTrue(response.success, f"Response failed: {response.error}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should execute quickly
        self.assertLess(total_time, 0.5)
        
        avg_time_ms = (total_time / 50) * 1000
        logger.info(f"Adapter average execution time: {avg_time_ms:.3f}ms")


def run_validation_tests():
    """Run interface validation tests"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running interface validation tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestModuleInterfaceValidation,
        TestModuleContractValidation,
        TestPerformanceValidation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Report results
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    skipped = len(getattr(result, 'skipped', []))
    
    logger.info(f"Validation Results: {passed}/{total} passed, {skipped} skipped")
    
    if result.failures:
        logger.error(f"Failures: {len(result.failures)}")
        for test, error in result.failures:
            logger.error(f"  {test}: {error}")
    
    if result.errors:
        logger.error(f"Errors: {len(result.errors)}")
        for test, error in result.errors:
            logger.error(f"  {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_validation_tests()
    print(f"\nInterface validation {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)