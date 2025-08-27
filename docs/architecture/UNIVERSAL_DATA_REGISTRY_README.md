# Universal Data Registry

## Overview

The Universal Data Registry is a centralized data acquisition and management system that serves as the single source of truth for all financial data throughout the investment analysis project. It replaces scattered data loading patterns with a unified, efficient, and maintainable data architecture.

## Key Features

### 🎯 Centralized Data Access
- Single point of access for all financial data
- Unified interface across Excel files, APIs, and cached data
- Consistent error handling and data validation

### 🚀 Intelligent Caching
- Multi-layer caching (memory + disk) with configurable TTL
- Content-based cache keys to detect data changes
- Automatic cache invalidation and cleanup
- Cache warming for frequently accessed data

### 🔄 Data Source Management
- Configurable data source priority and fallback chains
- Health monitoring for API endpoints
- Rate limiting and request optimization
- Circuit breaker pattern for failing data sources

### ✅ Data Validation & Quality
- Schema validation for all incoming data
- Data quality scoring and alerts
- Consistency checks across data sources
- Configurable validation strictness levels

### 📊 Performance Monitoring
- Comprehensive metrics tracking
- Cache hit/miss ratios
- Response time monitoring
- Data source usage statistics

### 🔧 Backward Compatibility
- Integration adapter for existing code
- Legacy interface for gradual migration
- No breaking changes to existing workflows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Universal Data Registry                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Cache     │  │ Validation  │  │  Metrics    │        │
│  │   System    │  │   Engine    │  │  Tracking   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Data Source Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Excel    │  │   Yahoo     │  │     FMP     │        │
│  │   Source    │  │  Finance    │  │    API      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                Integration Adapter Layer                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │        Legacy Compatibility Interface               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Basic Usage

```python
from universal_data_registry import get_registry, DataRequest

# Get the global registry instance
registry = get_registry()

# Request financial data
request = DataRequest(
    data_type='financial_statements',
    symbol='MSFT',
    period='annual'
)

response = registry.get_data(request)
print(f"Data source: {response.source}")
print(f"Quality score: {response.quality_score}")
```

### Convenience Functions

```python
from universal_data_registry import get_financial_data, get_market_data

# Get financial statements
financial_data = get_financial_data('AAPL', period='annual')

# Get market data
market_data = get_market_data('AAPL', period='daily', range='1y')
```

### Legacy Integration

```python
from registry_integration_adapter import get_legacy_interface

# Use existing interface with registry backend
legacy = get_legacy_interface()
statements = legacy.load_financial_statements('MSFT', './data/MSFT')
fcf_data = legacy.calculate_fcf_data('MSFT', './data/MSFT')
```

## Installation & Setup

### 1. Dependencies

```bash
pip install pyyaml requests pandas
```

### 2. Configuration

Copy the sample configuration:

```bash
cp registry_config.yaml.example registry_config.yaml
```

Edit `registry_config.yaml` to configure data sources, caching, and validation settings.

### 3. Environment Variables

Set up API keys:

```bash
export FMP_API_KEY="your_fmp_key"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
export POLYGON_API_KEY="your_polygon_key"
```

### 4. Initialize Registry

```python
from universal_data_registry import get_registry

# Initialize with default configuration
registry = get_registry()

# Or with custom configuration
registry = UniversalDataRegistry(
    cache_dir="./custom_cache",
    config=custom_config
)
```

## Configuration

### Configuration File Structure

```yaml
# Cache Configuration
cache:
  memory_size_mb: 256
  default_ttl_seconds: 3600
  disk_cache_enabled: true

# Data Source Configuration  
data_sources:
  excel:
    enabled: true
    priority: 1
    company_folder: "./data"
    
  yahoo_finance:
    enabled: true
    priority: 2
    rate_limit: 2000
    timeout: 30

# Validation Configuration
validation:
  default_level: standard
  quality_threshold: 0.8
  
# Performance Configuration
performance:
  default_timeout: 30
  max_concurrent_requests: 10
```

### Environment-Specific Overrides

```yaml
environments:
  development:
    cache:
      default_ttl_seconds: 300  # 5 minutes for development
    logging:
      level: DEBUG
      
  production:
    cache:
      memory_size_mb: 512
    security:
      data_encryption:
        enabled: true
```

## Data Sources

### Supported Data Sources

| Source | Type | Data Types | Status |
|--------|------|------------|--------|
| Excel Files | Local | Financial Statements, Ratios | ✅ Implemented |
| Yahoo Finance | API | Market Data, Prices | ✅ Implemented |
| FMP | API | Financial Statements, Ratios | 🔄 Planned |
| Alpha Vantage | API | Market Data, Fundamentals | 🔄 Planned |
| Polygon.io | API | Market Data, Prices | 🔄 Planned |

### Adding New Data Sources

1. Implement the `DataSourceInterface`:

```python
from data_source_interfaces import DataSourceInterface, DataSourceType

class CustomDataSource(DataSourceInterface):
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.CUSTOM
    
    def supports_request(self, request: DataRequest) -> bool:
        return request.data_type in ['custom_data']
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        # Implementation here
        pass
```

2. Register with the factory:

```python
from data_source_interfaces import DataSourceFactory

DataSourceFactory.register_source(DataSourceType.CUSTOM, CustomDataSource)
```

## Caching

### Cache Policies

- **DEFAULT**: Use cache if valid, fetch if not
- **NO_CACHE**: Always fetch fresh data
- **FORCE_REFRESH**: Fetch fresh and update cache
- **PREFER_CACHE**: Use cache even if stale

### Cache Configuration

```python
from universal_data_registry import DataRequest, CachePolicy

request = DataRequest(
    data_type='market_data',
    symbol='MSFT',
    period='daily',
    cache_policy=CachePolicy.FORCE_REFRESH
)
```

### Cache Management

```python
# Invalidate specific cache
registry.invalidate_cache('MSFT')

# Invalidate all cache
registry.invalidate_cache()

# Get cache metrics
metrics = registry.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']}")
```

## Data Validation

### Validation Levels

- **NONE**: No validation
- **BASIC**: Basic type and structure checks
- **STANDARD**: Quality scoring and consistency checks
- **STRICT**: Comprehensive validation with strict rules

### Custom Validation Rules

```yaml
validation:
  rules:
    financial_statements:
      required_fields:
        - revenue
        - net_income
      min_years: 3
      
    market_data:
      required_fields:
        - open
        - high
        - low
        - close
      min_data_points: 10
```

## Performance Monitoring

### Metrics Available

- **requests_total**: Total number of data requests
- **cache_hits/cache_misses**: Cache performance
- **cache_hit_rate**: Percentage of cache hits
- **average_response_time**: Average response time in seconds
- **source_usage**: Usage statistics per data source

### Monitoring Example

```python
# Get current metrics
metrics = registry.get_metrics()

# Health check
health = registry.health_check()

# Integration metrics
from registry_integration_adapter import get_integration_adapter
adapter = get_integration_adapter()
integration_metrics = adapter.get_integration_metrics()
```

## Migration Guide

### Gradual Migration Strategy

1. **Phase 1**: Use integration adapter for new code
2. **Phase 2**: Migrate existing modules one by one
3. **Phase 3**: Remove legacy fallbacks
4. **Phase 4**: Optimize for registry-native operations

### Migration Examples

#### Before (Legacy):
```python
from financial_calculations import FinancialCalculator

calculator = FinancialCalculator('./data/MSFT', 'MSFT')
calculator.load_financial_statements()
fcfe_values = calculator.calculate_fcfe()
```

#### After (Registry):
```python
from registry_integration_adapter import get_legacy_interface

legacy = get_legacy_interface()
fcf_data = legacy.calculate_fcf_data('MSFT', './data/MSFT')
fcfe_values = fcf_data['fcfe_values']
```

#### Future (Registry-Native):
```python
from universal_data_registry import get_financial_data

financial_data = get_financial_data('MSFT')
# Process financial data with registry-native calculations
```

## Error Handling

### Graceful Degradation

The registry implements multiple levels of fallback:

1. **Primary data source fails** → Try secondary sources
2. **All data sources fail** → Return cached data if available
3. **No cache available** → Return error response with details
4. **Registry fails** → Fall back to legacy data loading

### Error Response Format

```python
@dataclass
class DataResponse:
    data: Any = None
    source: DataSourceType
    timestamp: datetime
    quality_score: float = 0.0
    cache_hit: bool = False
    lineage: DataLineage
    validation_errors: List[str] = []
    performance_metrics: Dict[str, float] = {}
```

## Troubleshooting

### Common Issues

#### 1. Cache Issues
```bash
# Clear cache manually
rm -rf ./data_cache/*

# Or programmatically
registry.invalidate_cache()
```

#### 2. Configuration Issues
```bash
# Validate configuration
python -c "from registry_config_loader import load_registry_config; load_registry_config()"
```

#### 3. Data Source Issues
```python
# Check data source health
health = registry.health_check()
print(health['data_sources'])
```

#### 4. API Rate Limiting
```yaml
# Adjust rate limits in config
data_sources:
  yahoo_finance:
    rate_limit: 100  # Reduce from default
```

### Debug Mode

Enable debug mode for detailed logging:

```yaml
development:
  debug_mode: true
  verbose_logging: true

logging:
  level: DEBUG
```

## Testing

### Run Test Suite

```bash
python test_universal_data_registry.py
```

### Run Examples

```bash
python universal_data_registry_example.py
```

### Manual Testing

```python
# Test basic functionality
from universal_data_registry import get_registry
registry = get_registry()

# Test with real data
response = registry.get_data(DataRequest(
    data_type='market_data',
    symbol='MSFT',
    period='daily'
))
```

## Performance Optimization

### Best Practices

1. **Use appropriate cache policies**
   - Use `PREFER_CACHE` for historical data
   - Use `FORCE_REFRESH` sparingly
   
2. **Configure TTL by data type**
   ```yaml
   cache:
     ttl_by_type:
       financial_statements: 86400  # 24 hours
       market_data: 1800           # 30 minutes
   ```

3. **Monitor cache hit rates**
   - Aim for >90% cache hit rate
   - Adjust TTL if hit rate is low

4. **Use batch requests when possible**
   - Request multiple symbols together
   - Process data in batches

### Performance Tuning

```yaml
performance:
  max_concurrent_requests: 20  # Increase for high-throughput
  
cache:
  memory_size_mb: 512  # Increase for large datasets
  
data_sources:
  yahoo_finance:
    timeout: 10  # Reduce for faster failures
```

## Security Considerations

### API Key Management

```yaml
security:
  api_keys:
    encryption_enabled: true
    key_rotation_days: 90
    
  data_encryption:
    enabled: true
    algorithm: "AES-256"
```

### Access Control

```yaml
security:
  access_control:
    enabled: true
    allowed_symbols: ["MSFT", "AAPL", "GOOGL"]
    rate_limit_per_ip: 1000
```

## Future Enhancements

### Planned Features

- [ ] GraphQL API for external access
- [ ] Real-time data streaming
- [ ] Machine learning for data quality prediction
- [ ] Distributed caching for multi-instance deployments
- [ ] Event-driven architecture for real-time updates

### Extension Points

- Plugin architecture for new data sources
- Custom validation rules
- External monitoring integrations
- Cloud-native deployment options

## Contributing

### Adding New Data Sources

1. Fork the repository
2. Implement `DataSourceInterface`
3. Add configuration schema
4. Write tests
5. Update documentation
6. Submit pull request

### Reporting Issues

Please include:
- Configuration file (sanitized)
- Error messages and stack traces
- Steps to reproduce
- Expected vs actual behavior

## License

This project is part of the financial analysis framework. See main project LICENSE for details.

## Support

For questions and support:
- Check the troubleshooting section
- Review the examples
- Run the test suite
- Check existing issues in the project

---

**The Universal Data Registry successfully centralizes all data acquisition while maintaining backward compatibility and providing a foundation for future enhancements.**