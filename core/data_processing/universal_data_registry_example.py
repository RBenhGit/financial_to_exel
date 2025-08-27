"""
Universal Data Registry - Usage Examples
=======================================

This file demonstrates how to use the Universal Data Registry system
for centralized data acquisition in financial analysis applications.

Examples include:
- Basic data retrieval
- Configuration management
- Integration with existing code
- Error handling and fallbacks
- Performance monitoring
"""

import logging
import os
from datetime import datetime

# Configure logging for examples
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def example_basic_usage():
    """Example 1: Basic data retrieval through registry"""
    print("\n" + "="*60)
    print("Example 1: Basic Data Retrieval")
    print("="*60)
    
    from universal_data_registry import get_registry, DataRequest, CachePolicy, ValidationLevel
    
    # Get the global registry instance
    registry = get_registry()
    
    # Example 1a: Get financial statements
    print("\n1a. Requesting financial statements...")
    financial_request = DataRequest(
        data_type='financial_statements',
        symbol='MSFT',
        period='annual',
        cache_policy=CachePolicy.DEFAULT,
        validation_level=ValidationLevel.STANDARD
    )
    
    try:
        response = registry.get_data(financial_request)
        print(f"   Data source: {response.source}")
        print(f"   Quality score: {response.quality_score}")
        print(f"   Cache hit: {response.cache_hit}")
        print(f"   Data keys: {list(response.data.keys()) if response.data else 'No data'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 1b: Get market data
    print("\n1b. Requesting market data...")
    market_request = DataRequest(
        data_type='market_data',
        symbol='MSFT',
        period='daily',
        additional_params={'range': '1y'}
    )
    
    try:
        response = registry.get_data(market_request)
        print(f"   Data source: {response.source}")
        print(f"   Quality score: {response.quality_score}")
        print(f"   Cache hit: {response.cache_hit}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Show registry metrics
    print("\n1c. Registry metrics:")
    metrics = registry.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")

def example_convenience_functions():
    """Example 2: Using convenience functions"""
    print("\n" + "="*60)
    print("Example 2: Convenience Functions")
    print("="*60)
    
    from universal_data_registry import get_financial_data, get_market_data
    
    # Example 2a: Get financial data with convenience function
    print("\n2a. Using get_financial_data convenience function...")
    try:
        response = get_financial_data('AAPL', period='annual')
        print(f"   Source: {response.source}")
        print(f"   Timestamp: {response.timestamp}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2b: Get market data with convenience function
    print("\n2b. Using get_market_data convenience function...")
    try:
        response = get_market_data('AAPL', period='daily', range='6mo')
        print(f"   Source: {response.source}")
        print(f"   Quality: {response.quality_score}")
    except Exception as e:
        print(f"   Error: {e}")

def example_integration_adapter():
    """Example 3: Using integration adapter for backward compatibility"""
    print("\n" + "="*60)
    print("Example 3: Integration Adapter")
    print("="*60)
    
    from registry_integration_adapter import get_integration_adapter, get_legacy_interface
    
    # Example 3a: Using integration adapter
    print("\n3a. Using integration adapter...")
    adapter = get_integration_adapter()
    
    try:
        # This will try registry first, fallback to legacy if needed
        data = adapter.get_financial_data('MSFT', './data/MSFT')
        print(f"   Data source: {data.get('source', 'unknown')}")
        print(f"   Data keys: {list(data.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3b: Using legacy interface
    print("\n3b. Using legacy interface...")
    legacy = get_legacy_interface()
    
    try:
        # This provides exactly the same interface as before
        statements = legacy.load_financial_statements('MSFT', './data/MSFT')
        print(f"   Statement keys: {list(statements.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3c: Show integration metrics
    print("\n3c. Integration metrics:")
    metrics = adapter.get_integration_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")

def example_configuration():
    """Example 4: Configuration management"""
    print("\n" + "="*60)
    print("Example 4: Configuration Management")
    print("="*60)
    
    from registry_config_loader import load_registry_config, get_config_loader
    
    # Example 4a: Load configuration
    print("\n4a. Loading configuration...")
    try:
        config = load_registry_config()
        print(f"   Cache TTL: {config.cache.default_ttl_seconds} seconds")
        print(f"   Memory size: {config.cache.memory_size_mb} MB")
        print(f"   Validation level: {config.validation.default_level}")
        print(f"   Data sources: {list(config.data_sources.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 4b: Environment-specific configuration
    print("\n4b. Environment-specific configuration...")
    try:
        # Set environment variable
        os.environ['REGISTRY_ENV'] = 'development'
        loader = get_config_loader(environment='development')
        dev_config = loader.load_config()
        print(f"   Development cache TTL: {dev_config.cache.default_ttl_seconds}")
    except Exception as e:
        print(f"   Error: {e}")

def example_caching():
    """Example 5: Cache management"""
    print("\n" + "="*60)
    print("Example 5: Cache Management")
    print("="*60)
    
    from universal_data_registry import get_registry, DataRequest, CachePolicy
    
    registry = get_registry()
    
    # Example 5a: Force refresh (bypass cache)
    print("\n5a. Force refresh example...")
    request = DataRequest(
        data_type='market_data',
        symbol='GOOGL',
        period='daily',
        cache_policy=CachePolicy.FORCE_REFRESH
    )
    
    try:
        response = registry.get_data(request)
        print(f"   Cache hit: {response.cache_hit} (should be False)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 5b: Prefer cache
    print("\n5b. Prefer cache example...")
    request = DataRequest(
        data_type='market_data',
        symbol='GOOGL',
        period='daily',
        cache_policy=CachePolicy.PREFER_CACHE
    )
    
    try:
        response = registry.get_data(request)
        print(f"   Cache hit: {response.cache_hit}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 5c: Cache invalidation
    print("\n5c. Cache invalidation...")
    try:
        registry.invalidate_cache('GOOGL')
        print("   Cache invalidated for GOOGL")
    except Exception as e:
        print(f"   Error: {e}")

def example_error_handling():
    """Example 6: Error handling and fallbacks"""
    print("\n" + "="*60)
    print("Example 6: Error Handling and Fallbacks")
    print("="*60)
    
    from registry_integration_adapter import RegistryIntegrationAdapter
    from universal_data_registry import get_registry, DataRequest
    
    # Example 6a: Graceful handling of missing data
    print("\n6a. Handling missing data...")
    adapter = RegistryIntegrationAdapter()
    
    try:
        # This should fail gracefully
        data = adapter.get_financial_data('INVALID_SYMBOL', './nonexistent')
        print(f"   Returned: {type(data)} with keys: {list(data.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 6b: Registry fallback behavior
    print("\n6b. Registry fallback behavior...")
    registry = get_registry()
    
    try:
        request = DataRequest(
            data_type='nonexistent_type',
            symbol='TEST',
            period='annual'
        )
        response = registry.get_data(request)
        print(f"   Response type: {type(response)}")
    except Exception as e:
        print(f"   Expected error: {e}")

def example_performance_monitoring():
    """Example 7: Performance monitoring"""
    print("\n" + "="*60)
    print("Example 7: Performance Monitoring")
    print("="*60)
    
    from universal_data_registry import get_registry
    from registry_integration_adapter import get_integration_adapter
    
    registry = get_registry()
    adapter = get_integration_adapter()
    
    # Example 7a: Registry metrics
    print("\n7a. Registry performance metrics:")
    metrics = registry.get_metrics()
    print(f"   Total requests: {metrics['requests_total']}")
    print(f"   Cache hits: {metrics['cache_hits']}")
    print(f"   Cache hit rate: {metrics.get('cache_hit_rate', 0):.2%}")
    print(f"   Average response time: {metrics['average_response_time']:.3f}s")
    
    # Example 7b: Integration metrics
    print("\n7b. Integration adapter metrics:")
    int_metrics = adapter.get_integration_metrics()
    print(f"   Registry calls: {int_metrics['registry_calls']}")
    print(f"   Legacy fallbacks: {int_metrics['legacy_fallbacks']}")
    print(f"   Success ratio: {int_metrics['registry_success_ratio']:.2%}")
    
    # Example 7c: Health check
    print("\n7c. System health check:")
    health = registry.health_check()
    print(f"   Registry status: {health['registry_status']}")
    print(f"   Cache status: {health['cache_status']}")
    print(f"   Data sources: {len(health['data_sources'])} registered")

def example_financial_calculations_integration():
    """Example 8: Integration with financial calculations"""
    print("\n" + "="*60)
    print("Example 8: Financial Calculations Integration")
    print("="*60)
    
    from registry_integration_adapter import get_legacy_interface
    
    # Example 8a: FCF calculations with registry
    print("\n8a. FCF calculations using registry...")
    legacy = get_legacy_interface()
    
    try:
        # This will use registry if available, fallback to legacy
        fcf_data = legacy.calculate_fcf_data('MSFT', './data/MSFT')
        print(f"   FCF data keys: {list(fcf_data.keys())}")
        
        if 'fcfe_values' in fcf_data:
            fcfe = fcf_data['fcfe_values']
            print(f"   FCFE values: {len(fcfe) if fcfe else 0} periods")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 8b: Stock data integration
    print("\n8b. Stock data integration...")
    try:
        stock_data = legacy.get_stock_data('MSFT', period='1y')
        print(f"   Stock data source: {stock_data.get('source', 'unknown')}")
        print(f"   Data timestamp: {stock_data.get('timestamp', 'unknown')}")
    except Exception as e:
        print(f"   Error: {e}")

def run_all_examples():
    """Run all examples"""
    print("Universal Data Registry - Usage Examples")
    print("=" * 60)
    print("This demonstrates the centralized data acquisition system")
    print("that replaces scattered data loading throughout the project.")
    
    examples = [
        example_basic_usage,
        example_convenience_functions,
        example_integration_adapter,
        example_configuration,
        example_caching,
        example_error_handling,
        example_performance_monitoring,
        example_financial_calculations_integration
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample {example.__name__} failed: {e}")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nKey Benefits Demonstrated:")
    print("- Centralized data access through single registry")
    print("- Intelligent caching with configurable policies")
    print("- Backward compatibility with existing code")
    print("- Graceful error handling and fallbacks")
    print("- Performance monitoring and metrics")
    print("- Configuration-driven behavior")
    print("\nThe Universal Data Registry successfully centralizes")
    print("all data acquisition while maintaining compatibility!")

if __name__ == "__main__":
    run_all_examples()