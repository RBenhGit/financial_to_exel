"""
Dependency Injection Integration Example for Financial Analysis System
====================================================================

This module demonstrates how to integrate the lightweight DI framework
with the existing financial analysis components to reduce coupling
and improve testability.

Example usage patterns for:
- Data source configuration
- Calculation engine dependencies
- Analysis module orchestration
- Testing with mock dependencies
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from dependency_injection import (
    DIContainer, 
    ServiceLifetime, 
    get_global_container,
    register_service,
    resolve_service,
    inject
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration classes
class DatabaseConfig:
    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "financial_data"):
        self.host = host
        self.port = port
        self.database = database
        
    def get_connection_string(self) -> str:
        return f"postgresql://{self.host}:{self.port}/{self.database}"


class APIConfig:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30, rate_limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit = rate_limit


class CacheConfig:
    def __init__(self, cache_dir: str = "data_cache", ttl_hours: int = 24, max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.max_size_mb = max_size_mb
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)


# Financial system components with DI
class MarketDataProvider:
    """Enhanced market data provider with configuration injection"""
    
    def __init__(self, api_config: APIConfig, cache_config: CacheConfig):
        self.api_config = api_config
        self.cache_config = cache_config
        self.session_active = False
        logger.info(f"MarketDataProvider initialized with API: {api_config.base_url}")
    
    def get_stock_price(self, ticker: str) -> float:
        # Simulate API call with configuration
        logger.debug(f"Fetching price for {ticker} from {self.api_config.base_url}")
        # In real implementation, would use self.api_config for actual API calls
        return 150.0 + hash(ticker) % 100  # Mock price
    
    def get_market_data(self, ticker: str) -> Dict[str, Any]:
        return {
            "ticker": ticker,
            "price": self.get_stock_price(ticker),
            "currency": "USD",
            "source": "api"
        }


class DataCacheService:
    """Caching service with configuration injection"""
    
    def __init__(self, cache_config: CacheConfig):
        self.config = cache_config
        self.cache = {}
        logger.info(f"DataCacheService initialized with cache dir: {cache_config.cache_dir}")
    
    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = value
        logger.debug(f"Cached data for key: {key}")


class FinancialCalculator:
    """Financial calculations with dependency injection"""
    
    def __init__(self, market_data_provider: MarketDataProvider, cache_service: DataCacheService):
        self.market_provider = market_data_provider
        self.cache = cache_service
        logger.info("FinancialCalculator initialized with dependencies")
    
    def calculate_portfolio_value(self, holdings: Dict[str, int]) -> float:
        """Calculate total portfolio value"""
        total_value = 0.0
        
        for ticker, shares in holdings.items():
            # Try cache first
            cache_key = f"price_{ticker}"
            price = self.cache.get(cache_key)
            
            if price is None:
                price = self.market_provider.get_stock_price(ticker)
                self.cache.set(cache_key, price)
            
            total_value += price * shares
            logger.debug(f"{ticker}: {shares} shares @ ${price} = ${price * shares}")
        
        return total_value
    
    def calculate_dcf_value(self, ticker: str, cash_flows: list, discount_rate: float) -> float:
        """DCF calculation with market data integration"""
        market_data = self.market_provider.get_market_data(ticker)
        
        # Simplified DCF calculation
        dcf_value = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows, 1))
        
        logger.info(f"DCF value for {ticker}: ${dcf_value:.2f} (market price: ${market_data['price']})")
        return dcf_value


class ReportGenerator:
    """Report generation with full dependency injection"""
    
    def __init__(self, calculator: FinancialCalculator, db_config: DatabaseConfig):
        self.calculator = calculator
        self.db_config = db_config
        logger.info("ReportGenerator initialized")
    
    def generate_portfolio_report(self, holdings: Dict[str, int]) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        total_value = self.calculator.calculate_portfolio_value(holdings)
        
        report = {
            "timestamp": "2024-01-15",
            "total_value": total_value,
            "holdings_count": len(holdings),
            "total_shares": sum(holdings.values()),
            "database_connection": self.db_config.get_connection_string(),
            "holdings": holdings
        }
        
        logger.info(f"Generated report: ${total_value:.2f} total value")
        return report


class AnalysisOrchestrator:
    """Main orchestrator using dependency injection"""
    
    def __init__(self, report_generator: ReportGenerator):
        self.report_generator = report_generator
        logger.info("AnalysisOrchestrator initialized")
    
    def run_full_analysis(self, portfolio_data: Dict[str, int]) -> Dict[str, Any]:
        """Run complete financial analysis"""
        logger.info("Starting full financial analysis")
        
        # Generate report using injected dependencies
        report = self.report_generator.generate_portfolio_report(portfolio_data)
        
        # Add analysis metadata
        report["analysis_type"] = "full_portfolio"
        report["modules_used"] = ["market_data", "calculations", "reporting"]
        
        return report


def setup_production_container() -> DIContainer:
    """Set up production dependency container"""
    container = DIContainer()
    
    # Register configurations
    def create_api_config():
        return APIConfig(
            base_url="https://api.financialdata.com",
            api_key="prod_api_key_123",
            timeout=45,
            rate_limit=200
        )
    
    def create_cache_config():
        return CacheConfig(
            cache_dir="production_cache",
            ttl_hours=6,
            max_size_mb=1000
        )
    
    def create_db_config():
        return DatabaseConfig(
            host="prod-db.company.com",
            port=5432,
            database="financial_prod"
        )
    
    # Register all services with proper dependencies
    container.register(APIConfig, factory=create_api_config)
    container.register(CacheConfig, factory=create_cache_config)  
    container.register(DatabaseConfig, factory=create_db_config)
    
    container.register(DataCacheService, dependencies=[CacheConfig])
    container.register(MarketDataProvider, dependencies=[APIConfig, CacheConfig])
    container.register(FinancialCalculator, dependencies=[MarketDataProvider, DataCacheService])
    container.register(ReportGenerator, dependencies=[FinancialCalculator, DatabaseConfig])
    container.register(AnalysisOrchestrator, dependencies=[ReportGenerator])
    
    logger.info("Production container configured")
    return container


def setup_testing_container() -> DIContainer:
    """Set up testing container with mock dependencies"""
    container = DIContainer()
    
    # Mock configurations for testing
    api_config = APIConfig("http://mock-api", "test_key", 10, 1000)
    cache_config = CacheConfig("test_cache", 1, 10)
    db_config = DatabaseConfig("localhost", 5432, "test_db")
    
    # Register as instances for consistent testing
    container.register_instance(APIConfig, api_config)
    container.register_instance(CacheConfig, cache_config)
    container.register_instance(DatabaseConfig, db_config)
    
    # Register services
    container.register(DataCacheService, dependencies=[CacheConfig])
    container.register(MarketDataProvider, dependencies=[APIConfig, CacheConfig])
    container.register(FinancialCalculator, dependencies=[MarketDataProvider, DataCacheService])
    container.register(ReportGenerator, dependencies=[FinancialCalculator, DatabaseConfig])
    container.register(AnalysisOrchestrator, dependencies=[ReportGenerator])
    
    logger.info("Testing container configured")
    return container


def demonstrate_global_container_usage():
    """Demonstrate using global container with decorators"""
    
    # Set up global container
    register_service(APIConfig, factory=lambda: APIConfig("https://global-api.com", "global_key"))
    register_service(CacheConfig, factory=lambda: CacheConfig("global_cache"))
    register_service(DataCacheService, dependencies=[CacheConfig])
    register_service(MarketDataProvider, dependencies=[APIConfig, CacheConfig])
    
    # Use decorator for automatic injection
    @inject(MarketDataProvider)
    def get_stock_info(market_provider: MarketDataProvider, ticker: str) -> Dict[str, Any]:
        return market_provider.get_market_data(ticker)
    
    # Function automatically gets MarketDataProvider injected
    stock_info = get_stock_info("AAPL")
    logger.info(f"Stock info via global container: {stock_info}")
    
    return stock_info


def run_production_example():
    """Run example with production container"""
    logger.info("=== Production Example ===")
    
    container = setup_production_container()
    
    # Resolve the main orchestrator (all dependencies resolved automatically)
    orchestrator = container.resolve(AnalysisOrchestrator)
    
    # Run analysis
    portfolio = {"AAPL": 100, "MSFT": 50, "GOOGL": 25}
    report = orchestrator.run_full_analysis(portfolio)
    
    logger.info(f"Production analysis complete: {report['total_value']:.2f}")
    return report


def run_testing_example():
    """Run example with testing container"""
    logger.info("=== Testing Example ===")
    
    container = setup_testing_container()
    
    # Get individual components for testing
    calculator = container.resolve(FinancialCalculator)
    
    # Test specific functionality
    portfolio = {"TEST1": 10, "TEST2": 20}
    total_value = calculator.calculate_portfolio_value(portfolio)
    
    logger.info(f"Test calculation complete: {total_value:.2f}")
    return total_value


def demonstrate_lifecycle_management():
    """Demonstrate service lifecycle management"""
    logger.info("=== Lifecycle Management Demo ===")
    
    container = DIContainer()
    
    # Register same service with different lifetimes
    container.register(CacheConfig, 
                      factory=lambda: CacheConfig("singleton_cache"), 
                      lifetime=ServiceLifetime.SINGLETON)
    
    # Resolve multiple times - should get same instance
    cache1 = container.resolve(CacheConfig)
    cache2 = container.resolve(CacheConfig)
    
    logger.info(f"Singleton test: same instance = {cache1 is cache2}")
    
    # Register as transient
    container.clear()
    container.register(CacheConfig, 
                      factory=lambda: CacheConfig("transient_cache"), 
                      lifetime=ServiceLifetime.TRANSIENT)
    
    # Resolve multiple times - should get different instances
    cache3 = container.resolve(CacheConfig)
    cache4 = container.resolve(CacheConfig)
    
    logger.info(f"Transient test: different instances = {cache3 is not cache4}")


if __name__ == "__main__":
    print("Dependency Injection Integration Examples")
    print("=" * 50)
    
    try:
        # Run all examples
        prod_report = run_production_example()
        test_value = run_testing_example()
        global_info = demonstrate_global_container_usage()
        demonstrate_lifecycle_management()
        
        print("\nAll examples completed successfully!")
        print(f"Production report value: ${prod_report['total_value']:.2f}")
        print(f"Test calculation value: ${test_value:.2f}")
        print(f"Global container ticker: {global_info['ticker']}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise