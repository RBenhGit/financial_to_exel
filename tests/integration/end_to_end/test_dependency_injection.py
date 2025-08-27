"""
Test suite for the dependency injection framework
"""

import pytest
import threading
import time
from unittest.mock import Mock

from dependency_injection import (
    DIContainer,
    ServiceLifetime,
    DependencyInjectionError,
    CircularDependencyError,
    ServiceNotRegisteredError,
    get_global_container,
    register_service,
    resolve_service,
    clear_global_container,
    DIContextManager,
    inject
)


# Test classes for dependency injection
class DatabaseConfig:
    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port


class Logger:
    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        self.logs.append(message)


class DataRepository:
    def __init__(self, config: DatabaseConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.logger.log("DataRepository created")
    
    def get_data(self):
        return f"Data from {self.config.host}:{self.config.port}"


class DataService:
    def __init__(self, repository: DataRepository):
        self.repository = repository
    
    def process_data(self):
        return self.repository.get_data().upper()


class TestDIContainer:
    """Test the DIContainer class"""
    
    def setup_method(self):
        """Set up fresh container for each test"""
        self.container = DIContainer()
    
    def test_register_and_resolve_simple_service(self):
        """Test basic service registration and resolution"""
        # Register service
        self.container.register(DatabaseConfig, dependencies=[])
        
        # Resolve service
        config = self.container.resolve(DatabaseConfig)
        
        assert isinstance(config, DatabaseConfig)
        assert config.host == "localhost"
        assert config.port == 5432
    
    def test_register_with_factory(self):
        """Test service registration with factory function"""
        def create_config():
            return DatabaseConfig("custom-host", 9999)
        
        self.container.register(DatabaseConfig, factory=create_config)
        
        config = self.container.resolve(DatabaseConfig)
        assert config.host == "custom-host"
        assert config.port == 9999
    
    def test_register_instance(self):
        """Test registering pre-created instance"""
        instance = DatabaseConfig("test-host", 1234)
        self.container.register_instance(DatabaseConfig, instance)
        
        resolved = self.container.resolve(DatabaseConfig)
        assert resolved is instance
    
    def test_dependency_injection(self):
        """Test automatic dependency injection"""
        # Register dependencies
        self.container.register(DatabaseConfig, dependencies=[])
        self.container.register(Logger, dependencies=[])
        self.container.register(DataRepository, dependencies=[DatabaseConfig, Logger])
        
        # Resolve service with dependencies
        repository = self.container.resolve(DataRepository)
        
        assert isinstance(repository, DataRepository)
        assert isinstance(repository.config, DatabaseConfig)
        assert isinstance(repository.logger, Logger)
        assert "DataRepository created" in repository.logger.logs
    
    def test_singleton_lifetime(self):
        """Test singleton lifetime management"""
        self.container.register(DatabaseConfig, lifetime=ServiceLifetime.SINGLETON)
        
        config1 = self.container.resolve(DatabaseConfig)
        config2 = self.container.resolve(DatabaseConfig)
        
        assert config1 is config2
    
    def test_transient_lifetime(self):
        """Test transient lifetime management"""
        self.container.register(DatabaseConfig, lifetime=ServiceLifetime.TRANSIENT)
        
        config1 = self.container.resolve(DatabaseConfig)
        config2 = self.container.resolve(DatabaseConfig)
        
        assert config1 is not config2
        assert isinstance(config1, DatabaseConfig)
        assert isinstance(config2, DatabaseConfig)
    
    def test_service_not_registered_error(self):
        """Test error when resolving unregistered service"""
        with pytest.raises(ServiceNotRegisteredError):
            self.container.resolve(DatabaseConfig)
    
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
        
        with pytest.raises(CircularDependencyError):
            self.container.resolve(ServiceA)
    
    def test_complex_dependency_chain(self):
        """Test complex dependency resolution chain"""
        self.container.register(DatabaseConfig, dependencies=[])
        self.container.register(Logger, dependencies=[])
        self.container.register(DataRepository, dependencies=[DatabaseConfig, Logger])
        self.container.register(DataService, dependencies=[DataRepository])
        
        service = self.container.resolve(DataService)
        
        assert isinstance(service, DataService)
        result = service.process_data()
        assert "LOCALHOST:5432" in result
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        self.container.register(DatabaseConfig, lifetime=ServiceLifetime.SINGLETON)
        
        results = []
        errors = []
        
        def resolve_service():
            try:
                config = self.container.resolve(DatabaseConfig)
                results.append(config)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=resolve_service) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result is results[0] for result in results)  # All should be same singleton
    
    def test_is_registered(self):
        """Test service registration check"""
        assert not self.container.is_registered(DatabaseConfig)
        
        self.container.register(DatabaseConfig)
        assert self.container.is_registered(DatabaseConfig)
    
    def test_get_registration_info(self):
        """Test getting registration information"""
        self.container.register(DataRepository, dependencies=[DatabaseConfig, Logger])
        
        info = self.container.get_registration_info(DataRepository)
        
        assert info["service_type"] == "DataRepository"
        assert info["implementation"] == "DataRepository"
        assert info["dependencies"] == ["DatabaseConfig", "Logger"]
        assert info["lifetime"] == "singleton"
        assert not info["has_instance"]
    
    def test_validate_dependencies(self):
        """Test dependency validation"""
        # Register service with missing dependency
        self.container.register(DataRepository, dependencies=[DatabaseConfig, Logger])
        
        errors = self.container.validate_dependencies()
        
        assert "DataRepository" in errors
        assert any("DatabaseConfig is not registered" in error for error in errors["DataRepository"])
        assert any("Logger is not registered" in error for error in errors["DataRepository"])
    
    def test_clear_container(self):
        """Test clearing container"""
        self.container.register(DatabaseConfig)
        assert self.container.is_registered(DatabaseConfig)
        
        self.container.clear()
        assert not self.container.is_registered(DatabaseConfig)


class TestGlobalContainer:
    """Test global container functionality"""
    
    def setup_method(self):
        clear_global_container()
    
    def teardown_method(self):
        clear_global_container()
    
    def test_global_container_registration(self):
        """Test global container service registration"""
        register_service(DatabaseConfig)
        
        config = resolve_service(DatabaseConfig)
        assert isinstance(config, DatabaseConfig)
    
    def test_context_manager(self):
        """Test DI context manager"""
        # Register service in global container
        register_service(DatabaseConfig)
        global_config = resolve_service(DatabaseConfig)
        
        # Create custom container with context manager
        custom_config = DatabaseConfig("custom", 8080)
        
        with DIContextManager() as container:
            container.register_instance(DatabaseConfig, custom_config)
            context_config = resolve_service(DatabaseConfig)
            assert context_config is custom_config
        
        # Should be back to global container
        restored_config = resolve_service(DatabaseConfig)
        assert restored_config is global_config
    
    def test_inject_decorator(self):
        """Test automatic injection decorator"""
        register_service(DatabaseConfig)
        register_service(Logger)
        
        @inject(DatabaseConfig, Logger)
        def process_with_dependencies(config: DatabaseConfig, logger: Logger, user_data: str):
            logger.log(f"Processing {user_data}")
            return f"{user_data} processed at {config.host}"
        
        result = process_with_dependencies("test data")
        assert "test data processed at localhost" in result


class TestIntegrationWithFinancialSystem:
    """Test DI integration with financial system components"""
    
    def setup_method(self):
        self.container = DIContainer()
    
    def test_financial_components_integration(self):
        """Test DI with mock financial system components"""
        # Mock financial system components
        class MarketDataProvider:
            def get_price(self, symbol: str):
                return 100.0
        
        class FinancialCalculator:
            def __init__(self, market_provider: MarketDataProvider):
                self.market_provider = market_provider
            
            def calculate_value(self, symbol: str, shares: int):
                price = self.market_provider.get_price(symbol)
                return price * shares
        
        class Portfolio:
            def __init__(self, calculator: FinancialCalculator):
                self.calculator = calculator
            
            def get_total_value(self, holdings):
                return sum(
                    self.calculator.calculate_value(symbol, shares)
                    for symbol, shares in holdings.items()
                )
        
        # Register services
        self.container.register(MarketDataProvider, dependencies=[])
        self.container.register(FinancialCalculator, dependencies=[MarketDataProvider])
        self.container.register(Portfolio, dependencies=[FinancialCalculator])
        
        # Resolve and test
        portfolio = self.container.resolve(Portfolio)
        holdings = {"AAPL": 10, "MSFT": 20}
        total_value = portfolio.get_total_value(holdings)
        
        assert total_value == 3000.0  # (10 + 20) * 100.0
    
    def test_configuration_injection(self):
        """Test configuration-based dependency injection"""
        class APIConfig:
            def __init__(self, base_url: str, api_key: str, timeout: int = 30):
                self.base_url = base_url
                self.api_key = api_key
                self.timeout = timeout
        
        class APIClient:
            def __init__(self, config: APIConfig):
                self.config = config
                self.connected = True
        
        # Register with factory for configuration
        def create_api_config():
            return APIConfig("https://api.example.com", "secret-key", 60)
        
        self.container.register(APIConfig, factory=create_api_config)
        self.container.register(APIClient, dependencies=[APIConfig])
        
        client = self.container.resolve(APIClient)
        
        assert client.config.base_url == "https://api.example.com"
        assert client.config.timeout == 60
        assert client.connected


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running dependency injection smoke tests...")
    
    # Test basic container functionality
    container = DIContainer()
    container.register(DatabaseConfig, dependencies=[])
    config = container.resolve(DatabaseConfig)
    print(f"[OK] Basic resolution: {config.host}:{config.port}")
    
    # Test global container
    register_service(Logger, dependencies=[])
    logger = resolve_service(Logger)
    logger.log("Test message")
    print(f"[OK] Global container: {len(logger.logs)} logs")
    
    # Test dependency injection
    container.register(Logger, dependencies=[])
    container.register(DataRepository, dependencies=[DatabaseConfig, Logger])
    repo = container.resolve(DataRepository)
    print(f"[OK] Dependency injection: {repo.get_data()}")
    
    print("All smoke tests passed!")