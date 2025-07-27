# Alternative Financial Data Sources Implementation Guide

## Overview

This implementation adds support for multiple financial data sources beyond the original Excel file inputs and Yahoo Finance. The system provides automatic fallback, intelligent caching, rate limiting, and cost management across all data sources.

## Features

### ✅ Implemented Features

- **Multiple Data Sources**: Alpha Vantage, Financial Modeling Prep, Polygon.io, Excel files, Yahoo Finance
- **Unified Data Adapter Pattern**: Single interface for all data sources
- **Automatic Fallback Hierarchy**: Seamless switching between sources when one fails
- **Intelligent Caching**: TTL-based caching with quality-aware storage
- **Rate Limiting**: Per-source rate limiting to respect API limits
- **Cost Management**: Usage tracking, limits, and cost monitoring
- **Data Quality Validation**: Quality scoring and validation across sources
- **Backward Compatibility**: Full compatibility with existing CentralizedDataManager
- **Configuration Management**: Easy setup and management of API credentials

## Architecture

### Core Components

1. **`data_sources.py`** - Base classes and individual provider implementations
2. **`unified_data_adapter.py`** - Central adapter managing all data sources  
3. **`enhanced_data_manager.py`** - Enhanced version of CentralizedDataManager
4. **`data_source_manager.py`** - Configuration and management utilities

### Data Flow

```
Request → Enhanced Data Manager → Unified Data Adapter → Provider (Priority Order)
   ↓
Cache Check → Primary Source → Secondary Source → Fallback → Excel Files
   ↓
Data Quality Validation → Format Standardization → Response
```

## Quick Start

### 1. Installation

The alternative data sources are included in the existing codebase. No additional installation is required beyond the existing `requirements.txt` dependencies.

### 2. Basic Usage

```python
from enhanced_data_manager import create_enhanced_data_manager

# Create enhanced data manager (drop-in replacement)
manager = create_enhanced_data_manager()

# Fetch market data (uses multiple sources automatically)
data = manager.fetch_market_data("AAPL")

if data:
    print(f"Price: ${data['current_price']}")
    print(f"Market Cap: ${data['market_cap']}M")
    print(f"Source: {data.get('data_source', 'unknown')}")

# Check available sources
sources = manager.get_available_data_sources()
print(f"Active sources: {sources['active_sources']}/{sources['total_sources']}")

# Cleanup
manager.cleanup()
```

### 3. Configuration Setup

```python
from data_source_manager import DataSourceManager

# Interactive setup
manager = DataSourceManager()
manager.interactive_setup()  # Prompts for API keys

# Or configure programmatically
from enhanced_data_manager import create_enhanced_data_manager

manager = create_enhanced_data_manager()
success = manager.configure_enhanced_source('alpha_vantage', 'your_api_key_here')
```

## Data Sources

### Supported Sources

| Source | Type | Cost | Rate Limit | Quality | Priority |
|--------|------|------|------------|---------|----------|
| **Excel Files** | Local | Free | None | Medium | Fallback |
| **Yahoo Finance** | API | Free | ~5/min | High | Primary |
| **Alpha Vantage** | API | Free tier | 5/min, 500/month | High | Secondary |
| **Financial Modeling Prep** | API | Free tier | 250/month | Very High | Secondary |
| **Polygon.io** | API | Paid | 5/min | Excellent | Tertiary |

### Default Fallback Hierarchy

1. **Yahoo Finance** (Primary) - Fast, reliable, free
2. **Alpha Vantage** (Secondary) - Good backup, free tier available  
3. **Financial Modeling Prep** (Secondary) - High quality, limited free tier
4. **Polygon.io** (Tertiary) - Premium quality, paid service
5. **Excel Files** (Fallback) - Always available offline

## Configuration

### Configuration File Structure

The system creates `data_sources_config.json`:

```json
{
  "sources": {
    "alpha_vantage": {
      "priority": 2,
      "is_enabled": true,
      "quality_threshold": 0.8,
      "cache_ttl_hours": 24,
      "credentials": {
        "api_key": "your_key_here",
        "base_url": "https://www.alphavantage.co/query",
        "rate_limit_calls": 5,
        "rate_limit_period": 60,
        "monthly_limit": 500,
        "cost_per_call": 0.0
      }
    }
  }
}
```

### Environment Variables

You can also set API keys via environment variables:

```bash
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FMP_API_KEY=your_fmp_key
POLYGON_API_KEY=your_polygon_key
```

## API Keys Setup

### Alpha Vantage (Free Tier)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Sign up for free API key
3. Limits: 5 calls/minute, 500 calls/month
4. Configure: `manager.configure_enhanced_source('alpha_vantage', 'your_key')`

### Financial Modeling Prep (Free Tier)
1. Visit: https://financialmodelingprep.com/developer/docs
2. Sign up for free API key  
3. Limits: 250 calls/month
4. Configure: `manager.configure_enhanced_source('fmp', 'your_key')`

### Polygon.io (Paid Service)
1. Visit: https://polygon.io/pricing
2. Choose subscription plan
3. High quality, real-time data
4. Configure: `manager.configure_enhanced_source('polygon', 'your_key')`

## Usage Examples

### Example 1: Basic Market Data Fetching

```python
from enhanced_data_manager import create_enhanced_data_manager

manager = create_enhanced_data_manager()

# Fetch data for multiple tickers
tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]

for ticker in tickers:
    data = manager.fetch_market_data(ticker)
    if data:
        print(f"{ticker}: ${data['current_price']:.2f} "
              f"(Source: {data.get('data_source', 'unknown')})")
    else:
        print(f"{ticker}: Failed to fetch data")

manager.cleanup()
```

### Example 2: Testing All Sources

```python
from enhanced_data_manager import create_enhanced_data_manager

manager = create_enhanced_data_manager()

# Test all sources with AAPL
test_results = manager.test_all_sources("AAPL")

print("Source Test Results:")
for source, result in test_results['sources'].items():
    status = "PASS" if result['success'] else "FAIL"
    time_ms = result.get('response_time', 0) * 1000
    print(f"  {source}: {status} ({time_ms:.0f}ms)")

print(f"\nBest Source: {test_results['summary']['best_source']}")
print(f"Fastest Source: {test_results['summary']['fastest_source']}")

manager.cleanup()
```

### Example 3: Usage Monitoring

```python
from enhanced_data_manager import create_enhanced_data_manager

manager = create_enhanced_data_manager()

# Fetch some data
manager.fetch_market_data("AAPL")
manager.fetch_market_data("MSFT")

# Get usage report
report = manager.get_enhanced_usage_report()

print("Usage Report:")
print(f"Total API Calls: {report['enhanced_adapter']['total_calls']}")
print(f"Total Cost: ${report['enhanced_adapter']['total_cost']:.4f}")

for source, stats in report['enhanced_adapter']['sources'].items():
    if stats['total_calls'] > 0:
        print(f"\n{source}:")
        print(f"  Calls: {stats['total_calls']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print(f"  Avg Response: {stats['average_response_time']:.2f}s")

manager.cleanup()
```

### Example 4: Configuration Management

```python
from data_source_manager import DataSourceManager

# Create manager
ds_manager = DataSourceManager()

# Show current configuration
ds_manager._show_configuration_summary()

# Test sources
test_results = ds_manager.test_sources("AAPL") 

# Show usage report
ds_manager.show_usage_report()

# Check limits
warnings = ds_manager.check_limits()
if warnings:
    print("Usage warnings:")
    for warning in warnings:
        print(f"  {warning}")
```

## Integration with Existing Code

### Backward Compatibility

The `EnhancedDataManager` is a drop-in replacement for `CentralizedDataManager`:

```python
# Old code
from centralized_data_manager import CentralizedDataManager
manager = CentralizedDataManager(base_path)

# New code (backward compatible)
from enhanced_data_manager import create_enhanced_data_manager  
manager = create_enhanced_data_manager(base_path)

# All existing methods still work
data = manager.fetch_market_data("AAPL")
excel_data = manager.load_excel_data("AAPL")
cache_stats = manager.get_cache_stats()
```

### Updating Existing Applications

To update existing applications to use alternative data sources:

1. **Replace imports**:
   ```python
   # Before
   from centralized_data_manager import CentralizedDataManager
   
   # After  
   from enhanced_data_manager import create_enhanced_data_manager
   ```

2. **Update instantiation**:
   ```python
   # Before
   manager = CentralizedDataManager(base_path, cache_dir)
   
   # After
   manager = create_enhanced_data_manager(base_path, cache_dir)
   ```

3. **Optional: Configure additional sources**:
   ```python
   # Configure API sources for better reliability
   manager.configure_enhanced_source('alpha_vantage', 'your_api_key')
   ```

## Performance Considerations

### Caching Strategy

- **Excel data**: 48-hour cache TTL (rarely changes)
- **Yahoo Finance**: 2-hour cache TTL (balances freshness and calls)
- **Alpha Vantage**: 24-hour cache TTL (free tier limits)
- **Financial Modeling Prep**: 12-hour cache TTL (good quality)
- **Polygon.io**: 6-hour cache TTL (premium real-time data)

### Rate Limiting

Each source has built-in rate limiting:
- **Automatic delays** between requests
- **Exponential backoff** on rate limit errors
- **Request queuing** to respect limits
- **Fallback activation** when sources are exhausted

### Memory Usage

The system is designed for efficiency:
- **Lazy loading** of providers (only loaded when needed)
- **Memory-efficient caching** with TTL expiration
- **Background cleanup** of expired entries
- **Configurable cache limits**

## Monitoring and Troubleshooting

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Enhanced logging for data sources
logging.getLogger('enhanced_data_manager').setLevel(logging.DEBUG)
logging.getLogger('unified_data_adapter').setLevel(logging.DEBUG)
```

### Common Issues

**Issue**: "No data sources available"
- **Solution**: Check that at least one source is enabled and configured

**Issue**: "API key validation failed"  
- **Solution**: Verify API key is correct and active

**Issue**: "Rate limit exceeded"
- **Solution**: Wait for rate limit reset or configure additional sources

**Issue**: "All sources failed"
- **Solution**: Check network connectivity and API service status

### Health Check

```python
from data_source_manager import DataSourceManager

manager = DataSourceManager()

# Run comprehensive test
results = manager.test_sources("AAPL")

# Check for issues
if results['unified_adapter']['success']:
    print("System healthy")
else:
    print("System issues detected")
    # Check individual source results
```

## Cost Management

### Free Tier Monitoring

Most sources offer free tiers:

- **Alpha Vantage**: 500 calls/month free
- **Financial Modeling Prep**: 250 calls/month free  
- **Yahoo Finance**: Unlimited (rate limited)
- **Excel Files**: Always free

### Usage Tracking

```python
# Get usage report
report = manager.get_enhanced_usage_report()

# Check monthly usage
for source, stats in report['enhanced_adapter']['sources'].items():
    monthly_usage = stats['monthly_calls']
    monthly_limit = stats.get('monthly_limit', 'Unlimited')
    print(f"{source}: {monthly_usage}/{monthly_limit}")
```

### Cost Optimization Tips

1. **Configure caching appropriately** - Longer TTL reduces API calls
2. **Use multiple free sources** - Spread usage across providers  
3. **Implement request batching** - Minimize redundant calls
4. **Monitor usage regularly** - Avoid unexpected overage charges
5. **Set up usage alerts** - Get notified before hitting limits

## Testing

### Running Tests

```bash
# Basic integration test
python simple_test.py

# Comprehensive test suite (if Unicode supported)
python test_alternative_data_sources.py

# Test specific functionality
python -c "from enhanced_data_manager import create_enhanced_data_manager; m=create_enhanced_data_manager(); print(m.get_available_data_sources())"
```

### Test Coverage

Current tests cover:
- ✅ Module imports and dependencies
- ✅ Configuration system
- ✅ Enhanced data manager functionality  
- ✅ Unified data adapter operations
- ✅ Fallback hierarchy behavior
- ✅ Caching system operations
- ✅ Data quality validation
- ✅ Usage tracking and reporting
- ✅ Error handling and recovery

## Support and Maintenance

### Configuration Backup

```python
from data_source_manager import DataSourceManager

manager = DataSourceManager()
backup_file = manager.export_configuration()
print(f"Configuration backed up to: {backup_file}")
```

### Cache Maintenance

```python
# Clean expired cache entries
removed_count = manager.cleanup_cache()
print(f"Removed {removed_count} expired cache entries")
```

### Updates and Migration

The system is designed to be:
- **Forward compatible** - New sources can be added easily
- **Backward compatible** - Existing code continues to work
- **Configuration preserving** - Updates don't lose settings
- **Data preserving** - Cache and usage data persists

## Future Enhancements

Potential future improvements:
- Additional data sources (IEX Cloud, Quandl, etc.)
- Real-time data streaming
- Advanced caching strategies (Redis, database)
- Machine learning for source quality prediction
- Automated API key rotation
- Enhanced cost optimization algorithms

---

## Getting Help

If you encounter issues:

1. **Check the logs** - Enable debug logging for detailed information
2. **Run tests** - Use `simple_test.py` to verify system health  
3. **Review configuration** - Ensure API keys and settings are correct
4. **Test individual sources** - Use `DataSourceManager.test_sources()`
5. **Check API service status** - Verify external services are operational

The alternative data sources implementation provides a robust, scalable foundation for financial data access with intelligent fallback and cost management.