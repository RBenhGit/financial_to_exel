"""
Module Adapter Pattern - Usage Examples

This file demonstrates how to use the module adapter pattern to standardize
interactions between different types of modules in the financial analysis system.
"""

import logging
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from module_adapter import (
    ModuleAdapterFactory, 
    ModuleRequest, 
    ModuleResponse, 
    ModuleType,
    DataSourceAdapter,
    CalculationEngineAdapter,
    ProcessorAdapter
)

# Import existing modules
try:
    from data_sources import YfinanceProvider, DataSourceConfig, ApiCredentials
    from core.analysis.engines.financial_calculations import FinancialCalculator
    from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
    MODULES_AVAILABLE = False  # Force use of mock modules for demo
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModuleAdapterDemo:
    """Demonstration class for module adapter pattern usage"""
    
    def __init__(self):
        self.adapters = {}
        
    def setup_data_source_adapter(self):
        """Demonstrate setting up a data source adapter"""
        if not MODULES_AVAILABLE:
            print("Modules not available, creating mock data source")
            return self._create_mock_data_source_adapter()
            
        try:
            # Create YfinanceProvider configuration
            config = DataSourceConfig(
                source_type="yfinance",
                priority=1,
                rate_limit_per_minute=60,
                credentials=ApiCredentials()
            )
            
            # Create provider instance
            provider = YfinanceProvider(config)
            
            # Create adapter using factory
            adapter = ModuleAdapterFactory.create_adapter(provider)
            
            # Initialize adapter
            if adapter.initialize():
                self.adapters['yfinance'] = adapter
                logger.info(f"Data source adapter initialized: {adapter.metadata.name}")
                return adapter
            else:
                logger.error("Failed to initialize data source adapter")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up data source adapter: {e}")
            return None
    
    def _create_mock_data_source_adapter(self):
        """Create mock data source adapter for demo purposes"""
        class MockDataSource:
            def __init__(self):
                self.__class__.__name__ = "YfinanceProvider"
            
            def validate_credentials(self):
                return True
            
            def fetch_data(self, request):
                return {
                    "data": {
                        "AAPL": {
                            "price": 150.0,
                            "volume": 1000000,
                            "market_cap": 2500000000000
                        }
                    },
                    "source": "mock_yfinance"
                }
            
            def get_available_fields(self):
                return ["price", "volume", "market_cap", "pe_ratio"]
            
            def get_rate_limit_status(self):
                return {"rate_limit_ok": True, "remaining_calls": 100}
        
        mock_source = MockDataSource()
        adapter = ModuleAdapterFactory.create_adapter(mock_source)
        
        if adapter.initialize():
            self.adapters['mock_yfinance'] = adapter
            logger.info(f"Mock data source adapter initialized: {adapter.metadata.name}")
            return adapter
        return None
    
    def setup_calculation_engine_adapter(self):
        """Demonstrate setting up a calculation engine adapter"""
        if not MODULES_AVAILABLE:
            print("Modules not available, creating mock calculation engine")
            return self._create_mock_calculation_adapter()
            
        try:
            # Create FinancialCalculator instance
            calculator = FinancialCalculator(company_folder=None)
            
            # Create adapter using factory
            adapter = ModuleAdapterFactory.create_adapter(calculator)
            
            # Initialize adapter
            if adapter.initialize():
                self.adapters['financial_calculator'] = adapter
                logger.info(f"Calculation engine adapter initialized: {adapter.metadata.name}")
                return adapter
            else:
                logger.error("Failed to initialize calculation engine adapter")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up calculation engine adapter: {e}")
            return None
    
    def _create_mock_calculation_adapter(self):
        """Create mock calculation engine adapter for demo purposes"""
        class MockCalculator:
            def __init__(self):
                self.__class__.__name__ = "FinancialCalculator"
            
            def calculate_fcf(self, financial_data, **kwargs):
                revenue = financial_data.get("revenue", 1000000)
                return {
                    "fcf": revenue * 0.1,
                    "fcf_margin": 0.1,
                    "growth_rate": 0.05
                }
            
            def calculate_dcf(self, financial_data, **kwargs):
                fcf = financial_data.get("fcf", 100000)
                return {
                    "dcf_value": fcf * 15,
                    "intrinsic_value": fcf * 15.5,
                    "discount_rate": 0.08
                }
            
            def validate_inputs(self, financial_data):
                required_fields = ["revenue", "operating_income"]
                missing = [f for f in required_fields if f not in financial_data]
                return {
                    "valid": len(missing) == 0,
                    "errors": [f"Missing field: {f}" for f in missing],
                    "warnings": []
                }
        
        mock_calculator = MockCalculator()
        adapter = ModuleAdapterFactory.create_adapter(mock_calculator)
        
        if adapter.initialize():
            self.adapters['mock_calculator'] = adapter
            logger.info(f"Mock calculation engine adapter initialized: {adapter.metadata.name}")
            return adapter
        return None
    
    def setup_processor_adapter(self):
        """Demonstrate setting up a processor adapter"""
        if not MODULES_AVAILABLE:
            print("Creating mock processor")
            return self._create_mock_processor_adapter()
            
        try:
            # Create CentralizedDataManager instance
            manager = CentralizedDataManager(base_folder="data")
            
            # Create adapter using factory
            adapter = ModuleAdapterFactory.create_adapter(manager)
            
            # Initialize adapter
            if adapter.initialize():
                self.adapters['data_manager'] = adapter
                logger.info(f"Processor adapter initialized: {adapter.metadata.name}")
                return adapter
            else:
                logger.error("Failed to initialize processor adapter")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up processor adapter: {e}")
            return None
    
    def _create_mock_processor_adapter(self):
        """Create mock processor adapter for demo purposes"""
        class MockProcessor:
            def __init__(self):
                self.__class__.__name__ = "CentralizedDataManager"
            
            def process_data(self, data, **kwargs):
                processed = {
                    "original_data": data,
                    "processed_at": datetime.now().isoformat(),
                    "processing_options": kwargs,
                    "data_quality_score": 0.95
                }
                return {
                    "processed_data": processed,
                    "processing_time": 0.15,
                    "status": "success"
                }
            
            def validate_data(self, data):
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "data_completeness": 0.98
                }
        
        mock_processor = MockProcessor()
        adapter = ModuleAdapterFactory.create_adapter(mock_processor)
        
        if adapter.initialize():
            self.adapters['mock_processor'] = adapter
            logger.info(f"Mock processor adapter initialized: {adapter.metadata.name}")
            return adapter
        return None
    
    def demonstrate_data_source_operations(self):
        """Demonstrate data source adapter operations"""
        logger.info("\n=== Data Source Operations Demo ===")
        
        adapter = self.adapters.get('yfinance') or self.adapters.get('mock_yfinance')
        if not adapter:
            logger.error("No data source adapter available")
            return
        
        # 1. Check capabilities
        logger.info(f"Capabilities: {adapter.get_capabilities()}")
        
        # 2. Validate credentials
        request = ModuleRequest(operation="validate_credentials")
        response = adapter.execute(request)
        logger.info(f"Credential validation: {response.success}")
        
        # 3. Get available fields
        request = ModuleRequest(operation="get_available_fields")
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Available fields: {response.data}")
        
        # 4. Check rate limits
        request = ModuleRequest(operation="check_rate_limits")
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Rate limit status: {response.data}")
        
        # 5. Fetch data
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": None}
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Data fetched successfully, execution time: {response.execution_time_ms}ms")
            logger.info(f"Sample data: {str(response.data)[:200]}...")
        else:
            logger.error(f"Data fetch failed: {response.error}")
    
    def demonstrate_calculation_operations(self):
        """Demonstrate calculation engine adapter operations"""
        logger.info("\n=== Calculation Engine Operations Demo ===")
        
        adapter = self.adapters.get('financial_calculator') or self.adapters.get('mock_calculator')
        if not adapter:
            logger.error("No calculation engine adapter available")
            return
        
        # Sample financial data
        financial_data = {
            "revenue": 5000000,
            "operating_income": 1000000,
            "fcf": 800000,
            "shares_outstanding": 1000000
        }
        
        # 1. Validate inputs
        request = ModuleRequest(
            operation="validate_inputs",
            parameters={"financial_data": financial_data}
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Input validation: {response.data}")
        
        # 2. Calculate FCF
        request = ModuleRequest(
            operation="calculate_fcf",
            parameters={"financial_data": financial_data}
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"FCF calculation: {response.data}")
            logger.info(f"Execution time: {response.execution_time_ms}ms")
        
        # 3. Calculate DCF
        request = ModuleRequest(
            operation="calculate_dcf",
            parameters={"financial_data": financial_data}
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"DCF calculation: {response.data}")
    
    def demonstrate_processor_operations(self):
        """Demonstrate processor adapter operations"""
        logger.info("\n=== Processor Operations Demo ===")
        
        adapter = self.adapters.get('data_manager') or self.adapters.get('mock_processor')
        if not adapter:
            logger.error("No processor adapter available")
            return
        
        # Sample data to process
        data = {
            "company": "AAPL",
            "financials": {
                "revenue": 5000000,
                "expenses": 4000000,
                "net_income": 1000000
            },
            "market_data": {
                "price": 150.0,
                "volume": 1000000
            }
        }
        
        # 1. Validate data
        request = ModuleRequest(
            operation="validate_data",
            parameters={"data": data}
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Data validation: {response.data}")
        
        # 2. Process data
        request = ModuleRequest(
            operation="process_data",
            parameters={
                "data": data,
                "normalize": True,
                "clean_outliers": True
            }
        )
        response = adapter.execute(request)
        if response.success:
            logger.info(f"Data processed successfully")
            logger.info(f"Processing metadata: {response.data.get('processing_time', 'N/A')}")
            logger.info(f"Execution time: {response.execution_time_ms}ms")
    
    def demonstrate_error_handling(self):
        """Demonstrate error handling in adapters"""
        logger.info("\n=== Error Handling Demo ===")
        
        adapter = self.adapters.get('yfinance') or self.adapters.get('mock_yfinance')
        if not adapter:
            logger.error("No adapter available for error handling demo")
            return
        
        # 1. Invalid operation
        request = ModuleRequest(operation="invalid_operation")
        response = adapter.execute(request)
        logger.info(f"Invalid operation response: success={response.success}, error={response.error}")
        
        # 2. Missing required parameters
        request = ModuleRequest(
            operation="fetch_data",
            parameters={}  # Missing required 'symbol' parameter
        )
        response = adapter.execute(request)
        logger.info(f"Missing parameters response: success={response.success}, error={response.error}")
    
    def demonstrate_unified_workflow(self):
        """Demonstrate a complete workflow using multiple adapters"""
        logger.info("\n=== Unified Workflow Demo ===")
        
        # Get adapters
        data_adapter = self.adapters.get('yfinance') or self.adapters.get('mock_yfinance')
        calc_adapter = self.adapters.get('financial_calculator') or self.adapters.get('mock_calculator')
        proc_adapter = self.adapters.get('data_manager') or self.adapters.get('mock_processor')
        
        if not all([data_adapter, calc_adapter, proc_adapter]):
            logger.error("Not all adapters available for workflow demo")
            return
        
        logger.info("Starting unified workflow...")
        
        # Step 1: Fetch market data
        request = ModuleRequest(
            operation="fetch_data",
            parameters={"symbol": "AAPL", "data_request": None}
        )
        data_response = data_adapter.execute(request)
        
        if not data_response.success:
            logger.error(f"Data fetch failed: {data_response.error}")
            return
        
        logger.info("✓ Market data fetched")
        
        # Step 2: Process the raw data
        request = ModuleRequest(
            operation="process_data",
            parameters={
                "data": data_response.data,
                "clean": True,
                "validate": True
            }
        )
        proc_response = proc_adapter.execute(request)
        
        if not proc_response.success:
            logger.error(f"Data processing failed: {proc_response.error}")
            return
        
        logger.info("✓ Data processed and validated")
        
        # Step 3: Perform financial calculations
        financial_data = {
            "revenue": 5000000,
            "operating_income": 1000000,
            "fcf": 800000
        }
        
        request = ModuleRequest(
            operation="calculate_fcf",
            parameters={"financial_data": financial_data}
        )
        calc_response = calc_adapter.execute(request)
        
        if not calc_response.success:
            logger.error(f"Calculation failed: {calc_response.error}")
            return
        
        logger.info("✓ Financial calculations completed")
        
        # Summary
        total_time = (
            data_response.execution_time_ms + 
            proc_response.execution_time_ms + 
            calc_response.execution_time_ms
        )
        
        logger.info(f"\n📊 Workflow Summary:")
        logger.info(f"   Total execution time: {total_time:.2f}ms")
        logger.info(f"   Steps completed: 3/3")
        logger.info(f"   Final FCF result: {calc_response.data}")
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        logger.info("🚀 Starting Module Adapter Pattern Demo\n")
        
        # Setup all adapters
        logger.info("Setting up adapters...")
        self.setup_data_source_adapter()
        self.setup_calculation_engine_adapter()
        self.setup_processor_adapter()
        
        # Run demonstrations
        self.demonstrate_data_source_operations()
        self.demonstrate_calculation_operations()
        self.demonstrate_processor_operations()
        self.demonstrate_error_handling()
        self.demonstrate_unified_workflow()
        
        logger.info("\n✅ Demo completed successfully!")
        
        # Cleanup
        logger.info("\nCleaning up adapters...")
        for name, adapter in self.adapters.items():
            try:
                adapter.cleanup()
                logger.info(f"✓ Cleaned up {name}")
            except Exception as e:
                logger.warning(f"Warning during cleanup of {name}: {e}")


def main():
    """Main function to run the demonstration"""
    demo = ModuleAdapterDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()