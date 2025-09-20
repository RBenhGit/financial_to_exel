# API Integration & Data Source Configuration Guide

## Overview

Phase 2's data management system provides sophisticated multi-source data integration with automatic fallbacks, intelligent caching, and comprehensive error handling. This guide covers all aspects of API configuration, data source management, and integration patterns.

## Data Source Architecture

### **Hierarchical Data Source System**
```
Priority 1: yfinance (Free, Real-time)
Priority 2: Alpha Vantage / FMP (Premium APIs)
Priority 3: Polygon (Professional-grade)
Priority 4: Excel Files (Local/Manual data)
```

### **Intelligent Fallback Logic**
- **Primary Source Failure**: Automatically attempts next highest priority source
- **Partial Data**: Combines data from multiple sources to fill gaps
- **Quality Assessment**: Validates data quality and selects best available source
- **Cache Integration**: Leverages cached data when APIs are unavailable

---

## Supported Data Sources

### 1. **yfinance** (Priority 1 - Free)

#### **Overview**
- **Cost**: Free, no API key required
- **Best For**: Real-time stock prices, basic financial data, market data
- **Rate Limits**: Reasonable usage expected
- **Coverage**: Global markets with focus on major exchanges

#### **Configuration**
```json
"yfinance": {
  "priority": 1,
  "is_enabled": true,
  "quality_threshold": 0.8,
  "cache_ttl_hours": 2
}
```

#### **Available Data**
- Real-time and historical stock prices
- Market capitalizations and trading volumes
- Basic financial ratios and metrics
- Dividend information and splits
- Company profile information

### 2. **Alpha Vantage** (Priority 2 - Freemium)

#### **Overview**
- **Free Tier**: 25 requests/day, 5 requests/minute
- **Premium**: Higher limits with paid plans
- **Best For**: Fundamental analysis, financial statements
- **Strengths**: Comprehensive economic data, reliable service

#### **Setup Instructions**
1. **Get API Key**: Visit https://www.alphavantage.co/support/#api-key
2. **Configure**: Edit `config/data_sources_config.json`
3. **Replace API Key**: Update the `api_key` field
4. **Enable**: Set `is_enabled: true`

#### **Configuration Example**
```json
"alpha_vantage": {
  "priority": 2,
  "is_enabled": true,
  "quality_threshold": 0.8,
  "cache_ttl_hours": 24,
  "credentials": {
    "api_key": "YOUR_ALPHA_VANTAGE_KEY",
    "base_url": "https://www.alphavantage.co/query",
    "rate_limit_calls": 5,
    "rate_limit_period": 60,
    "timeout": 30,
    "retry_attempts": 3,
    "cost_per_call": 0.0,
    "monthly_limit": 500,
    "is_active": true
  }
}
```

#### **Available Data**
- **Time Series Data**: Daily, weekly, monthly stock prices
- **Fundamental Data**: Income statements, balance sheets, cash flow
- **Economic Indicators**: GDP, inflation, employment data
- **Technical Indicators**: Moving averages, RSI, MACD
- **Real-time Data**: Intraday pricing (premium)

### 3. **Financial Modeling Prep (FMP)** (Priority 2 - Freemium)

#### **Overview**
- **Free Tier**: 250 requests/day
- **Premium**: Extended limits and features
- **Best For**: Comprehensive financial statements, ratios
- **Strengths**: Detailed financial data, good coverage

#### **Setup Instructions**
1. **Register**: https://financialmodelingprep.com/developer/docs
2. **Get API Key**: From dashboard after registration
3. **Configure**: Update `config/data_sources_config.json`
4. **Test**: Verify connection with sample request

#### **Configuration Example**
```json
"fmp": {
  "priority": 2,
  "is_enabled": true,
  "quality_threshold": 0.85,
  "cache_ttl_hours": 12,
  "credentials": {
    "api_key": "YOUR_FMP_API_KEY",
    "base_url": "https://financialmodelingprep.com/api/v3",
    "rate_limit_calls": 250,
    "rate_limit_period": 3600,
    "timeout": 30,
    "retry_attempts": 3,
    "cost_per_call": 0.0,
    "monthly_limit": 250,
    "is_active": true
  }
}
```

#### **Available Data**
- **Financial Statements**: Complete income statements, balance sheets, cash flows
- **Financial Ratios**: Comprehensive ratio calculations
- **Company Profiles**: Detailed company information
- **Market Data**: Stock prices, market caps, trading data
- **Earnings Data**: EPS, guidance, estimates

### 4. **Polygon** (Priority 3 - Professional)

#### **Overview**
- **Free Tier**: Limited requests with delayed data
- **Professional**: Real-time data, higher limits
- **Best For**: Professional-grade market data, options data
- **Strengths**: High-quality data, excellent uptime

#### **Setup Instructions**
1. **Register**: https://polygon.io/
2. **Choose Plan**: Free or paid based on needs
3. **Get API Key**: From account dashboard
4. **Configure**: Update configuration file

#### **Configuration Example**
```json
"polygon": {
  "priority": 3,
  "is_enabled": true,
  "quality_threshold": 0.9,
  "cache_ttl_hours": 1,
  "credentials": {
    "api_key": "YOUR_POLYGON_API_KEY",
    "base_url": "https://api.polygon.io",
    "rate_limit_calls": 1000,
    "rate_limit_period": 3600,
    "timeout": 30,
    "retry_attempts": 3,
    "cost_per_call": 0.001,
    "monthly_limit": 50000,
    "is_active": true
  }
}
```

#### **Available Data**
- **Real-time Market Data**: Live stock prices, options data
- **Historical Data**: Comprehensive historical datasets
- **Market Events**: Dividends, splits, earnings dates
- **Reference Data**: Company profiles, ticker information
- **News Data**: Financial news and sentiment analysis

### 5. **Excel Files** (Priority 4 - Local)

#### **Overview**
- **Cost**: Free (local files)
- **Best For**: Manual data entry, private companies, custom analysis
- **Format**: Standardized Excel templates
- **Location**: `data/companies/{TICKER}/`

#### **Directory Structure**
```
data/companies/AAPL/
├── FY/                    # Fiscal Year data
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx
│   └── Cash Flow Statement.xlsx
└── LTM/                   # Last Twelve Months data
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx
```

#### **Supported Formats**
- **Income Statement**: Revenue, expenses, net income
- **Balance Sheet**: Assets, liabilities, equity
- **Cash Flow Statement**: Operating, investing, financing cash flows
- **Custom Sheets**: Additional financial data

---

## Configuration Management

### **Primary Configuration File**
**Location**: `config/data_sources_config.json`

### **Configuration Structure**
```json
{
  "sources": {
    "source_name": {
      "priority": 1,              // Lower = higher priority
      "is_enabled": true,         // Enable/disable source
      "quality_threshold": 0.8,   // Minimum quality score
      "cache_ttl_hours": 24,     // Cache expiration
      "credentials": {
        "api_key": "...",         // API credentials
        "base_url": "...",        // API endpoint
        "rate_limit_calls": 100,  // Rate limit
        "rate_limit_period": 3600,// Rate limit window
        "timeout": 30,            // Request timeout
        "retry_attempts": 3,      // Retry logic
        "cost_per_call": 0.0,     // Cost tracking
        "monthly_limit": 1000,    // Usage limits
        "is_active": true         // Active status
      }
    }
  },
  "global_settings": {
    "default_timeout": 30,
    "max_concurrent_requests": 5,
    "cache_enabled": true,
    "quality_logging": true
  }
}
```

### **Environment Variables**
For sensitive API keys, use environment variables:
```bash
# .env file
ALPHA_VANTAGE_API_KEY=your_key_here
FMP_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

### **Configuration Validation**
The system automatically validates configuration on startup:
- **API Key Format**: Validates key format and length
- **URL Accessibility**: Tests API endpoint connectivity
- **Rate Limits**: Verifies rate limit settings
- **Credentials**: Tests API authentication

---

## Advanced Data Management

### **Enhanced Data Manager**
**Location**: `core/data_processing/enhanced_data_manager.py`

#### **Key Features**
- **Multi-Source Orchestration**: Manages multiple data sources intelligently
- **Quality Assessment**: Evaluates and scores data quality
- **Automatic Fallbacks**: Seamless switching between sources
- **Cache Management**: Intelligent caching with expiration
- **Error Recovery**: Robust error handling and retry logic

#### **Usage Example**
```python
from core.data_processing.enhanced_data_manager import EnhancedDataManager

# Initialize with configuration
data_manager = EnhancedDataManager()

# Get comprehensive data with automatic fallbacks
data = data_manager.get_comprehensive_financial_data(
    ticker="AAPL",
    data_types=["price", "fundamentals", "ratios"],
    prefer_realtime=True
)

# Check data quality and sources
quality_score = data_manager.assess_data_quality(data)
sources_used = data_manager.get_last_sources_used()
```

### **Universal Data Registry**
**Location**: `core/data_processing/universal_data_registry.py`

#### **Purpose**
Centralized configuration-driven data management system that abstracts data source complexity.

#### **Key Features**
- **Configuration-Driven**: Define data mappings in configuration files
- **Standard Variables**: Unified variable naming across sources
- **Quality Scoring**: Automatic data quality assessment
- **Source Tracking**: Complete data lineage tracking
- **Validation**: Comprehensive data validation rules

#### **Configuration Example**
```yaml
# registry_config.yaml
standard_variables:
  revenue:
    excel_mapping: "Total Revenue"
    api_mappings:
      yfinance: "totalRevenue"
      alpha_vantage: "revenue"
      fmp: "revenue"
    validation_rules:
      - type: "positive"
      - type: "reasonable_growth"
        max_change: 2.0
```

### **Intelligent Caching System**

#### **Multi-Tier Caching**
1. **Memory Cache**: Fast access for frequently used data
2. **Disk Cache**: Persistent cache for expensive API calls
3. **Database Cache**: Long-term storage for historical data

#### **Cache Configuration**
```python
# Cache settings per data source
cache_config = {
    "yfinance": {"ttl_hours": 2, "max_size_mb": 100},
    "alpha_vantage": {"ttl_hours": 24, "max_size_mb": 500},
    "fmp": {"ttl_hours": 12, "max_size_mb": 300},
    "polygon": {"ttl_hours": 1, "max_size_mb": 200}
}
```

#### **Cache Management**
- **Automatic Expiration**: Time-based cache invalidation
- **Size Limits**: Prevents excessive memory usage
- **Priority System**: Keeps most valuable data cached
- **Manual Control**: Clear cache when needed

---

## Rate Limiting & API Management

### **Rate Limiting Strategy**
**Location**: `core/data_processing/rate_limiting/`

#### **Features**
- **Per-Source Limits**: Individual limits for each API
- **Global Throttling**: System-wide request management
- **Intelligent Queuing**: Queue requests when limits approached
- **Cost Tracking**: Monitor API usage costs
- **Usage Analytics**: Track API utilization patterns

#### **Configuration**
```json
"rate_limiting": {
  "global_max_concurrent": 5,
  "per_source_limits": {
    "alpha_vantage": {"calls": 5, "period": 60},
    "fmp": {"calls": 250, "period": 3600},
    "polygon": {"calls": 1000, "period": 3600}
  },
  "queue_settings": {
    "max_queue_size": 100,
    "timeout_seconds": 300
  }
}
```

### **API Health Monitoring**
- **Response Time Tracking**: Monitor API performance
- **Error Rate Monitoring**: Track API reliability
- **Uptime Assessment**: Evaluate API availability
- **Automatic Fallbacks**: Switch sources on failures

---

## Error Handling & Resilience

### **Comprehensive Error Handling**

#### **Error Categories**
1. **Network Errors**: Connection timeouts, DNS failures
2. **API Errors**: Rate limits, authentication failures
3. **Data Errors**: Invalid formats, missing data
4. **System Errors**: Memory issues, disk space

#### **Error Response Strategies**
```python
# Example error handling configuration
error_strategies = {
    "network_timeout": "retry_with_backoff",
    "rate_limit_exceeded": "queue_and_wait",
    "invalid_api_key": "disable_source",
    "data_format_error": "fallback_to_next_source",
    "insufficient_quota": "use_cache_if_available"
}
```

### **Fallback Mechanisms**
- **Source Prioritization**: Automatic failover to next source
- **Partial Data Acceptance**: Use incomplete but valid data
- **Cache Fallback**: Use cached data when APIs fail
- **Graceful Degradation**: Continue with reduced functionality

### **Logging & Monitoring**
- **Detailed Error Logs**: Complete error tracking
- **Performance Metrics**: API response time monitoring
- **Usage Statistics**: Track API consumption patterns
- **Quality Metrics**: Monitor data quality scores

---

## Integration Patterns

### **Data Loading Patterns**

#### **1. Single-Source Loading**
```python
# Load from specific source
calculator = FinancialCalculator(ticker="AAPL")
calculator.load_financial_data(source="alpha_vantage")
```

#### **2. Multi-Source Loading**
```python
# Load with automatic fallbacks
calculator = FinancialCalculator(ticker="AAPL")
calculator.enable_multi_source_mode()
financial_data = calculator.load_comprehensive_data()
```

#### **3. Priority-Based Loading**
```python
# Load with custom priorities
data = calculator.load_financial_data(
    preferred_sources=["fmp", "alpha_vantage", "yfinance"]
)
```

### **Data Quality Assessment**
```python
# Assess data quality
quality_report = calculator.assess_data_quality()
# Returns: quality_score, completeness, accuracy, timeliness
```

### **Cache Management**
```python
# Manual cache control
calculator.clear_cache(source="alpha_vantage")
calculator.preload_cache(tickers=["AAPL", "MSFT", "GOOGL"])
```

---

## Troubleshooting Guide

### **Common Issues**

#### **API Key Problems**
- **Invalid Key**: Check key format and activation
- **Expired Key**: Renew API subscription
- **Wrong Permissions**: Verify key has required permissions
- **Rate Limits**: Monitor usage and upgrade if needed

#### **Data Quality Issues**
- **Missing Data**: Check source coverage for specific metrics
- **Inconsistent Data**: Verify data mapping configuration
- **Stale Data**: Check cache expiration settings
- **Format Errors**: Validate API response formats

#### **Performance Issues**
- **Slow Loading**: Optimize cache settings and reduce concurrent requests
- **Memory Usage**: Clear cache and reduce data retention
- **Network Timeouts**: Increase timeout settings or check connectivity

### **Diagnostic Tools**

#### **API Status Monitor**
```python
from tools.diagnostics.api_monitor import APIStatusMonitor

monitor = APIStatusMonitor()
status_report = monitor.check_all_apis()
# Returns: connectivity, latency, error_rates, quota_usage
```

#### **Data Quality Dashboard**
- **Real-time Monitoring**: Live data quality metrics
- **Historical Trends**: Data quality over time
- **Source Comparison**: Compare quality across sources
- **Alert System**: Notifications for quality degradation

#### **Configuration Validator**
```python
from tools.validation.config_validator import ConfigValidator

validator = ConfigValidator()
validation_report = validator.validate_configuration()
# Returns: valid_config, warnings, errors, recommendations
```

---

## Best Practices

### **Configuration Management**
- **Version Control**: Keep configuration files in version control
- **Environment Separation**: Separate dev/test/prod configurations
- **Sensitive Data**: Use environment variables for API keys
- **Documentation**: Document all configuration changes

### **API Usage Optimization**
- **Batch Requests**: Group multiple data requests when possible
- **Cache Utilization**: Leverage caching to reduce API calls
- **Off-Peak Usage**: Schedule heavy operations during off-peak hours
- **Monitor Quotas**: Track usage to avoid unexpected overages

### **Data Quality Assurance**
- **Validation Rules**: Implement comprehensive data validation
- **Cross-Source Verification**: Compare data across sources
- **Manual Spot Checks**: Periodically verify critical calculations
- **Quality Monitoring**: Set up automated quality alerts

### **Error Management**
- **Graceful Degradation**: Design systems to work with partial data
- **User Communication**: Clearly communicate data limitations
- **Retry Logic**: Implement intelligent retry mechanisms
- **Fallback Plans**: Always have backup data sources

---

## Migration & Updates

### **API Version Updates**
- **Version Pinning**: Pin to specific API versions for stability
- **Testing**: Test new versions in development environments
- **Gradual Rollout**: Phase migrations across different components
- **Rollback Plans**: Maintain ability to revert to previous versions

### **Configuration Migration**
- **Schema Validation**: Validate configuration schema changes
- **Data Migration**: Migrate existing cache and configuration data
- **Backward Compatibility**: Maintain compatibility where possible
- **Update Documentation**: Keep documentation current with changes

---

*This guide provides comprehensive coverage of API integration and data source configuration for Phase 2's advanced data management system, enabling reliable and efficient financial data processing.*