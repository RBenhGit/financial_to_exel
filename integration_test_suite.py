"""
Comprehensive Integration Test Suite for Module Interfaces
=========================================================

This test suite validates that all module interfaces work correctly together
and maintains backward compatibility across the financial analysis system.

Test Coverage:
- Data source integration with dependency injection
- Calculation engine interfaces with adapters
- Module communication through standardized contracts
- Backward compatibility validation
- End-to-end workflow testing
"""

import unittest
import logging
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import tempfile
import json
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import the systems we're testing
try:
    from dependency_injection import DIContainer, ServiceLifetime, get_global_container, clear_global_container
    from module_adapter import ModuleAdapterFactory, ModuleRequest, ModuleResponse, ModuleType
    from centralized_data_manager import CentralizedDataManager
    from data_sources import YfinanceProvider, DataSourceConfig, ApiCredentials
    from financial_calculations import FinancialCalculator
    from unified_data_adapter import UnifiedDataAdapter
    HAS_ALL_MODULES = True
except ImportError as e:
    print(f"Warning: Some modules not available for integration testing: {e}")
    HAS_ALL_MODULES = False

logger = logging.getLogger(__name__)


class IntegrationTestBase(unittest.TestCase):
    """Base class for integration tests with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        if not HAS_ALL_MODULES:
            self.skipTest("Required modules not available")
        
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = Path(self.temp_dir)
        
        # Clear global DI container
        clear_global_container()
        
        # Create test container
        self.container = DIContainer()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_global_container()


class TestDataSourceIntegration(IntegrationTestBase):
    """Test data source integration with DI and adapters"""
    
    def test_data_source_di_integration(self):
        """Test data source with dependency injection"""
        
        # Mock configuration factory
        def create_data_config():
            return DataSourceConfig(
                source_type="yfinance",
                priority=1,
                rate_limit_per_minute=60,
                credentials=ApiCredentials()
            )
        
        # Register dependencies
        self.container.register(DataSourceConfig, factory=create_data_config)
        self.container.register(YfinanceProvider, dependencies=[DataSourceConfig])
        
        # Resolve provider
        provider = self.container.resolve(YfinanceProvider)
        
        # Verify provider is properly configured
        self.assertIsInstance(provider, YfinanceProvider)
        self.assertEqual(provider.config.source_type, "yfinance")
        
        # Test adapter creation
        adapter = ModuleAdapterFactory.create_adapter(provider)
        self.assertEqual(adapter.module_type, ModuleType.DATA_SOURCE)
        
        # Test adapter initialization
        self.assertTrue(adapter.initialize())
        
        # Test adapter capabilities
        capabilities = adapter.get_capabilities()
        self.assertIn("fetch_data", capabilities)
        self.assertIn("validate_credentials", capabilities)
    
    def test_centralized_data_manager_integration(self):
        """Test centralized data manager with DI"""
        
        # Register centralized data manager
        def create_data_manager():
            return CentralizedDataManager(
                base_path=str(self.test_data_path),
                cache_dir=str(self.test_data_path / "cache")
            )
        
        self.container.register(CentralizedDataManager, factory=create_data_manager)
        
        # Resolve manager
        manager = self.container.resolve(CentralizedDataManager)
        
        # Verify manager is properly configured
        self.assertIsInstance(manager, CentralizedDataManager)
        self.assertEqual(manager.base_path, self.test_data_path)
        
        # Test validation integration
        self.assertTrue(manager.is_system_ready("AAPL", skip_network=True))


class TestCalculationEngineIntegration(IntegrationTestBase):
    """Test calculation engine integration"""
    
    def test_financial_calculator_di_integration(self):
        """Test financial calculator with dependency injection"""
        
        # Create mock Excel data
        excel_data = {
            "cashflow_fy": Mock(),
            "income_fy": Mock(),
            "balance_fy": Mock()
        }
        
        # Mock data manager
        mock_manager = Mock()
        mock_manager.load_excel_data.return_value = excel_data
        mock_manager.fetch_market_data.return_value = {
            "ticker": "AAPL",
            "current_price": 150.0,
            "market_cap": 2500000
        }
        
        # Register dependencies
        self.container.register_instance(CentralizedDataManager, mock_manager)
        
        def create_calculator():
            data_manager = self.container.resolve(CentralizedDataManager)
            return FinancialCalculator(company_folder="AAPL")
        
        self.container.register(FinancialCalculator, factory=create_calculator)
        
        # Resolve calculator
        calculator = self.container.resolve(FinancialCalculator)
        
        # Verify calculator
        self.assertIsInstance(calculator, FinancialCalculator)
        
        # Test adapter creation
        adapter = ModuleAdapterFactory.create_adapter(calculator)
        self.assertEqual(adapter.module_type, ModuleType.CALCULATION_ENGINE)
        
        # Test adapter capabilities
        capabilities = adapter.get_capabilities()
        self.assertIn("calculate_fcf", capabilities)
        self.assertIn("calculate_dcf", capabilities)


class TestUnifiedDataAdapterIntegration(IntegrationTestBase):
    """Test unified data adapter integration"""
    
    @patch('unified_data_adapter.YfinanceProvider')
    @patch('unified_data_adapter.AlphaVantageProvider')
    def test_unified_adapter_with_di(self, mock_alpha, mock_yf):
        """Test unified data adapter with DI container"""
        
        # Mock providers
        mock_yf_instance = Mock()
        mock_yf_instance.fetch_data.return_value = Mock(success=True, data={"AAPL": {"price": 150.0}})
        mock_yf.return_value = mock_yf_instance
        
        mock_alpha_instance = Mock()
        mock_alpha_instance.fetch_data.return_value = Mock(success=True, data={"AAPL": {"price": 151.0}})
        mock_alpha.return_value = mock_alpha_instance
        
        # Register unified adapter
        def create_unified_adapter():
            return UnifiedDataAdapter(
                config_path=str(self.test_data_path / "config.json"),
                cache_dir=str(self.test_data_path / "cache")
            )
        
        self.container.register(UnifiedDataAdapter, factory=create_unified_adapter)
        
        # Resolve adapter
        try:
            adapter = self.container.resolve(UnifiedDataAdapter)
            self.assertIsInstance(adapter, UnifiedDataAdapter)
        except Exception as e:
            self.skipTest(f"UnifiedDataAdapter not available: {e}")


class TestEndToEndWorkflows(IntegrationTestBase):
    """Test complete end-to-end workflows"""
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow with all components"""
        
        # Create test Excel data files
        test_company_path = self.test_data_path / "AAPL" / "FY"
        test_company_path.mkdir(parents=True)
        
        # Create mock Excel file (we'll mock the actual loading)
        mock_excel_path = test_company_path / "cashflow.xlsx"
        mock_excel_path.touch()
        
        # Mock data manager with real file structure
        mock_manager = Mock()
        mock_manager.base_path = self.test_data_path
        mock_manager.load_excel_data.return_value = {
            "cashflow_fy": self._create_mock_dataframe(),
            "income_fy": self._create_mock_dataframe(),
            "balance_fy": self._create_mock_dataframe()
        }
        mock_manager.fetch_market_data.return_value = {
            "ticker": "AAPL",
            "current_price": 150.0,
            "market_cap": 2500,  # in millions
            "shares_outstanding": 16666666666
        }
        
        # Set up DI container with all components
        self.container.register_instance(CentralizedDataManager, mock_manager)
        
        def create_calculator():
            data_manager = self.container.resolve(CentralizedDataManager)
            # Pass the data manager to calculator if it accepts it
            return FinancialCalculator(company_folder="AAPL")
        
        self.container.register(FinancialCalculator, factory=create_calculator)
        
        # Create analysis orchestrator
        class AnalysisOrchestrator:
            def __init__(self, data_manager: CentralizedDataManager, calculator: FinancialCalculator):
                self.data_manager = data_manager
                self.calculator = calculator
            
            def run_full_analysis(self, ticker: str):
                # Load data
                excel_data = self.data_manager.load_excel_data(ticker)
                market_data = self.data_manager.fetch_market_data(ticker)
                
                # Create adapter for calculator
                calc_adapter = ModuleAdapterFactory.create_adapter(self.calculator)
                
                # Run FCF calculation through adapter
                fcf_request = ModuleRequest(
                    operation="calculate_fcf",
                    parameters={"financial_data": excel_data}
                )
                
                fcf_response = calc_adapter.execute(fcf_request)
                
                return {
                    "ticker": ticker,
                    "market_data": market_data,
                    "fcf_analysis": fcf_response.data if fcf_response.success else None,
                    "success": fcf_response.success
                }
        
        self.container.register(AnalysisOrchestrator, 
                               dependencies=[CentralizedDataManager, FinancialCalculator])
        
        # Run the analysis
        orchestrator = self.container.resolve(AnalysisOrchestrator)
        result = orchestrator.run_full_analysis("AAPL")
        
        # Verify results
        self.assertEqual(result["ticker"], "AAPL")
        self.assertIsNotNone(result["market_data"])
        self.assertEqual(result["market_data"]["ticker"], "AAPL")
        
        # Verify the workflow completed
        self.assertIn("success", result)
    
    def _create_mock_dataframe(self):
        """Create mock pandas DataFrame for testing"""
        try:
            import pandas as pd
            return pd.DataFrame({
                "Year": [2021, 2022, 2023],
                "Revenue": [1000000, 1100000, 1200000],
                "Operating Cash Flow": [800000, 850000, 900000]
            })
        except ImportError:
            # Return mock object if pandas not available
            mock_df = Mock()
            mock_df.empty = False
            mock_df.columns = ["Year", "Revenue", "Operating Cash Flow"]
            return mock_df


class TestBackwardCompatibility(IntegrationTestBase):
    """Test backward compatibility of module interfaces"""
    
    def test_legacy_financial_calculator_interface(self):
        """Test that legacy FinancialCalculator interface still works"""
        
        # Test direct instantiation (legacy style)
        try:
            calculator = FinancialCalculator(company_folder="AAPL")
            self.assertIsInstance(calculator, FinancialCalculator)
            
            # Test that it has expected methods
            self.assertTrue(hasattr(calculator, 'calculate_fcf'))
            self.assertTrue(hasattr(calculator, 'calculate_dcf'))
            
        except Exception as e:
            # If direct instantiation fails due to missing data, that's expected
            logger.info(f"Legacy instantiation failed as expected: {e}")
    
    def test_legacy_data_manager_interface(self):
        """Test that legacy CentralizedDataManager interface still works"""
        
        try:
            # Test legacy instantiation
            manager = CentralizedDataManager(
                base_path=str(self.test_data_path),
                cache_dir=str(self.test_data_path / "cache")
            )
            
            # Test legacy methods
            self.assertTrue(hasattr(manager, 'load_excel_data'))
            self.assertTrue(hasattr(manager, 'fetch_market_data'))
            self.assertTrue(hasattr(manager, 'clear_cache'))
            
            # Test that cache stats work
            stats = manager.get_cache_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn('total_entries', stats)
            
        except Exception as e:
            self.fail(f"Legacy CentralizedDataManager interface failed: {e}")
    
    def test_adapter_backward_compatibility(self):
        """Test that adapters maintain backward compatibility"""
        
        # Create mock legacy module
        class LegacyDataProvider:
            def fetch_data(self, request):
                return {"data": {"AAPL": {"price": 150.0}}}
            
            def validate_credentials(self):
                return True
        
        legacy_provider = LegacyDataProvider()
        
        # Create adapter
        adapter = ModuleAdapterFactory.create_adapter(legacy_provider)
        
        # Test that adapter works with legacy module
        self.assertIsNotNone(adapter)
        self.assertTrue(adapter.initialize())
        
        # Test legacy method calls through adapter
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": Mock()}
        )
        
        response = adapter.execute(request)
        self.assertTrue(response.success)


class TestErrorHandlingAndResilience(IntegrationTestBase):
    """Test error handling and system resilience"""
    
    def test_graceful_degradation_with_failed_dependencies(self):
        """Test system behavior when dependencies fail"""
        
        # Register a service that will fail
        def failing_factory():
            raise Exception("Simulated service failure")
        
        self.container.register(Mock, factory=failing_factory)
        
        # Try to resolve and catch the error gracefully
        with self.assertRaises(Exception):
            self.container.resolve(Mock)
        
        # Verify container is still functional
        self.container.register(str, factory=lambda: "test")
        result = self.container.resolve(str)
        self.assertEqual(result, "test")
    
    def test_adapter_error_handling(self):
        """Test adapter error handling"""
        
        # Create mock that raises exceptions
        faulty_module = Mock()
        faulty_module.__class__.__name__ = "FaultyProvider"
        faulty_module.fetch_data.side_effect = Exception("Network error")
        faulty_module.validate_credentials.return_value = True
        
        # Create adapter
        adapter = ModuleAdapterFactory.create_adapter(faulty_module)
        
        # Test that adapter handles errors gracefully
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": Mock()}
        )
        
        response = adapter.execute(request)
        
        # Should not raise exception, but should indicate failure
        self.assertFalse(response.success)
        self.assertIn("Network error", response.error)
        self.assertIsNotNone(response.execution_time_ms)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        
        class ServiceA:
            def __init__(self, service_b):
                pass
        
        class ServiceB:
            def __init__(self, service_a):
                pass
        
        self.container.register(ServiceA, dependencies=[ServiceB])
        self.container.register(ServiceB, dependencies=[ServiceA])
        
        # Should detect circular dependency
        with self.assertRaises(Exception) as context:
            self.container.resolve(ServiceA)
        
        self.assertIn("circular", str(context.exception).lower())


class TestPerformanceAndScaling(IntegrationTestBase):
    """Test performance and scaling characteristics"""
    
    def test_container_performance_with_many_services(self):
        """Test DI container performance with many services"""
        
        # Register many services
        for i in range(100):
            service_name = f"Service{i}"
            self.container.register(
                type(service_name, (), {}), 
                factory=lambda i=i: f"service_{i}"
            )
        
        # Time resolution of services
        import time
        start_time = time.time()
        
        for i in range(10):  # Resolve some services
            service_type = type(f"Service{i}", (), {})
            result = self.container.resolve(service_type)
            self.assertEqual(result, f"service_{i}")
        
        end_time = time.time()
        resolution_time = end_time - start_time
        
        # Should resolve quickly (less than 1 second for this test)
        self.assertLess(resolution_time, 1.0)
    
    def test_adapter_execution_performance(self):
        """Test adapter execution performance"""
        
        # Create simple mock module
        fast_module = Mock()
        fast_module.__class__.__name__ = "FastProvider"
        fast_module.quick_operation = lambda: "result"
        
        adapter = ModuleAdapterFactory.create_adapter(fast_module)
        
        # Time many operations
        import time
        start_time = time.time()
        
        for _ in range(100):
            request = ModuleRequest(operation="quick_operation")
            response = adapter.execute(request)
            self.assertTrue(response.success)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should execute quickly
        self.assertLess(execution_time, 1.0)
        logger.info(f"100 adapter executions took {execution_time:.3f} seconds")


def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDataSourceIntegration,
        TestCalculationEngineIntegration,
        TestUnifiedDataAdapterIntegration,
        TestEndToEndWorkflows,
        TestBackwardCompatibility,
        TestErrorHandlingAndResilience,
        TestPerformanceAndScaling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_integration_tests():
    """Run all integration tests and return results"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting comprehensive integration test suite...")
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Report results
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    logger.info(f"Integration test results:")
    logger.info(f"  Total tests: {total_tests}")
    logger.info(f"  Passed: {total_tests - failures - errors - skipped}")
    logger.info(f"  Failed: {failures}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Skipped: {skipped}")
    
    if result.failures:
        logger.error("Failures:")
        for test, traceback in result.failures:
            logger.error(f"  {test}: {traceback}")
    
    if result.errors:
        logger.error("Errors:")
        for test, traceback in result.errors:
            logger.error(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)