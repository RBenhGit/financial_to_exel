# Financial Analysis Tool - API Reference

## Overview
This document provides comprehensive API reference for the Financial Analysis Tool's programmatic interfaces and data source integrations.

## 🔄 **Core Data Adapter APIs**

### UnifiedDataAdapter
The central data integration hub supporting multiple financial data providers.

```python
from unified_data_adapter import UnifiedDataAdapter
from data_sources import FinancialDataRequest, DataSourceType

# Initialize adapter
adapter = UnifiedDataAdapter(config_file="data_sources_config.json")

# Create data request
request = FinancialDataRequest(
    ticker="AAPL",
    data_types=['price', 'fundamentals'],
    force_refresh=True
)

# Fetch data with automatic fallback
response = adapter.fetch_data(request)

if response.success:
    print(f"Data from: {response.source_type.value}")
    print(f"Quality score: {response.quality_metrics.overall_score}")
    print(f"Price: {response.data['current_price']}")
```

#### Key Methods
- **`fetch_data(request)`**: Fetch data with smart fallback
- **`configure_source(source_type, api_key, **kwargs)`**: Configure API provider
- **`get_usage_report()`**: Get comprehensive usage statistics
- **`test_source(source_type, ticker)`**: Test specific data source
- **`cleanup()`**: Clean up resources and save cache

### EnhancedDataManager
Extended data manager with backward compatibility and multi-source support.

```python
from enhanced_data_manager import create_enhanced_data_manager

# Create enhanced manager
manager = create_enhanced_data_manager()

# Fetch market data (tries multiple sources)
market_data = manager.fetch_market_data("AAPL", force_reload=True)

# Get available sources
sources_info = manager.get_available_data_sources()
print(f"Active sources: {sources_info['active_sources']}")

# Test all sources
test_results = manager.test_all_sources("MSFT")
print(f"Success rate: {test_results['summary']['success_rate']:.1%}")
```

## 💰 **Financial Calculation APIs**

### FinancialCalculator
Core financial analysis engine with unified FCF calculation methods.

```python
from financial_calculations import FinancialCalculator

# Initialize with company folder
calculator = FinancialCalculator("./AAPL")

# Calculate all FCF types
fcf_results = calculator.calculate_all_fcf_types()

# Access specific FCF calculations
fcff = fcf_results.get('FCFF', {})
fcfe = fcf_results.get('FCFE', {})
lfcf = fcf_results.get('LFCF', {})

print(f"FCFF (Latest): ${fcff.get('latest_value', 0):.1f}M")
print(f"Growth Rate: {fcff.get('growth_rate', 0):.1%}")
```

### DCF Valuation
Professional discounted cash flow valuation with sensitivity analysis.

```python
from dcf_valuation import DCFValuator
from financial_calculations import FinancialCalculator

# Initialize
calculator = FinancialCalculator("./AAPL")
dcf_valuator = DCFValuator(calculator)

# Perform DCF analysis
dcf_results = dcf_valuator.calculate_dcf_valuation(
    discount_rate=0.12,
    terminal_growth_rate=0.03,
    projection_years=10
)

print(f"Fair Value: ${dcf_results['fair_value_per_share']:.2f}")
print(f"Current Price: ${dcf_results['current_price']:.2f}")
print(f"Upside: {dcf_results['upside_percentage']:.1%}")

# Sensitivity analysis
sensitivity = dcf_valuator.sensitivity_analysis(
    discount_rates=[0.10, 0.12, 0.14],
    terminal_growth_rates=[0.02, 0.03, 0.04]
)
```

## 📊 **Portfolio Management APIs**

### WatchListManager
Portfolio tracking and watch list management system.

```python
from watch_list_manager import WatchListManager

# Initialize manager
watch_manager = WatchListManager()

# Create new watch list
tech_watchlist = watch_manager.create_watchlist(
    name="Tech Giants",
    description="Major technology companies"
)

# Add securities
watch_manager.add_security(tech_watchlist['id'], "AAPL", target_price=180.0)
watch_manager.add_security(tech_watchlist['id'], "MSFT", target_price=350.0)
watch_manager.add_security(tech_watchlist['id'], "GOOGL", target_price=140.0)

# Get performance analysis
performance = watch_manager.get_performance_analysis(tech_watchlist['id'])
print(f"Total Return: {performance['total_return']:.1%}")
print(f"Best Performer: {performance['best_performer']}")
```

### AnalysisCapture
Performance benchmarking and analysis capture system.

```python
from analysis_capture import analysis_capture

# Capture analysis session
@analysis_capture
def perform_dcf_analysis(ticker):
    # Your analysis code here
    calculator = FinancialCalculator(f"./{ticker}")
    fcf_results = calculator.calculate_all_fcf_types()
    return fcf_results

# Execute with automatic capture
results = perform_dcf_analysis("AAPL")

# View captured metrics
print(f"Execution time: {results.metadata['execution_time']:.2f}s")
print(f"Data quality: {results.metadata['data_quality']:.1%}")
```

## 🌐 **Data Source Provider APIs**

### Alpha Vantage Provider
Enterprise-grade financial data with comprehensive fundamentals.

```python
from data_sources import AlphaVantageProvider, DataSourceConfig, DataSourceType
from data_sources import ApiCredentials, DataSourcePriority

# Configure Alpha Vantage
config = DataSourceConfig(
    source_type=DataSourceType.ALPHA_VANTAGE,
    priority=DataSourcePriority.PRIMARY,
    credentials=ApiCredentials(
        api_key="YOUR_API_KEY",
        base_url="https://www.alphavantage.co/query",
        rate_limit_calls=5,
        rate_limit_period=60
    )
)

provider = AlphaVantageProvider(config)

# Fetch data
request = FinancialDataRequest(ticker="AAPL", data_types=['price', 'fundamentals'])
response = provider.fetch_data(request)

print(f"Success: {response.success}")
print(f"API calls: {response.api_calls_used}")
print(f"Quality: {response.quality_metrics.overall_score:.2f}")
```

### Financial Modeling Prep Provider
High-quality financial statements and ratios.

```python
from data_sources import FinancialModelingPrepProvider

# Configure FMP
fmp_config = DataSourceConfig(
    source_type=DataSourceType.FINANCIAL_MODELING_PREP,
    priority=DataSourcePriority.SECONDARY,
    credentials=ApiCredentials(
        api_key="YOUR_FMP_KEY",
        base_url="https://financialmodelingprep.com/api/v3",
        monthly_limit=250
    )
)

provider = FinancialModelingPrepProvider(fmp_config)
response = provider.fetch_data(request)
```

### Polygon.io Provider
Institutional-grade market data with real-time capabilities.

```python
from data_sources import PolygonProvider

# Configure Polygon
polygon_config = DataSourceConfig(
    source_type=DataSourceType.POLYGON,
    priority=DataSourcePriority.TERTIARY,
    credentials=ApiCredentials(
        api_key="YOUR_POLYGON_KEY",
        base_url="https://api.polygon.io",
        cost_per_call=0.003,
        rate_limit_calls=5
    )
)

provider = PolygonProvider(polygon_config)
response = provider.fetch_data(request)
```

## 🔧 **Configuration Management APIs**

### Data Source Configuration
Programmatic configuration of API providers with enhanced date tracking.

```python
from data_source_manager import DataSourceManager

# Initialize manager
manager = DataSourceManager(base_path=".")

# Configure source programmatically
success = manager.adapter.configure_source(
    DataSourceType.ALPHA_VANTAGE,
    api_key="YOUR_KEY",
    rate_limit_calls=5,
    monthly_limit=500
)

# Test configuration
test_results = manager.test_sources("AAPL")
print(f"Sources working: {test_results['unified_adapter']['success']}")

# Get usage report with date tracking
usage = manager.show_usage_report()
```

### Enhanced Date Tracking System
New date correlation system that tracks latest report dates across all data sources.

```python
from enhanced_data_manager import create_enhanced_data_manager

# Initialize enhanced manager with date tracking
manager = create_enhanced_data_manager()

# Fetch data with automatic date extraction
market_data = manager.fetch_market_data("AAPL", force_reload=True)

# Access date information
print(f"Latest Report Date: {market_data.get('latest_report_date')}")
print(f"Data Source: {market_data.get('data_source')}")
print(f"Report Period: {market_data.get('report_period')}")

# Date correlation for multiple sources
date_info = manager.get_date_correlation("MSFT")
print(f"API Date: {date_info.get('api_date')}")
print(f"Excel Date: {date_info.get('excel_date')}")
print(f"Correlation Status: {date_info.get('correlation_status')}")
```

### Field Normalization
Standardize data across different API formats with date correlation.

```python
from field_normalizer import FieldNormalizer

# Initialize normalizer with date tracking
normalizer = FieldNormalizer()

# Normalize data from different sources
alpha_vantage_data = {...}  # Raw Alpha Vantage response
normalized_data = normalizer.normalize(alpha_vantage_data, source_type="alpha_vantage")

# Access standardized fields with date information
print(f"Revenue: {normalized_data.get('total_revenue')}")
print(f"Free Cash Flow: {normalized_data.get('free_cash_flow')}")
print(f"Market Cap: {normalized_data.get('market_capitalization')}")
print(f"Report Date: {normalized_data.get('report_date')}")
print(f"Period End Date: {normalized_data.get('period_end_date')}")
```

## 📈 **Advanced Analytics APIs**

### FCF Growth Analysis
Comprehensive growth rate calculation and trend analysis.

```python
from fcf_consolidated import calculate_fcf_growth_rates

# Calculate growth rates
growth_data = calculate_fcf_growth_rates(
    fcf_values=[1000, 1100, 1200, 1400, 1500],  # FCF in millions
    years=[2019, 2020, 2021, 2022, 2023]
)

print(f"3-Year CAGR: {growth_data['cagr_3_year']:.1%}")
print(f"5-Year CAGR: {growth_data['cagr_5_year']:.1%}")
print(f"Recent Growth: {growth_data['recent_growth']:.1%}")
```

### Report Generation
Professional PDF report generation with market-specific formatting.

```python
from report_generator import FCFReportGenerator

# Initialize report generator
generator = FCFReportGenerator(
    financial_calculator=calculator,
    dcf_valuator=dcf_valuator
)

# Generate comprehensive report
report_path = generator.generate_comprehensive_report(
    company_name="Apple Inc.",
    output_dir="./reports"
)

print(f"Report saved: {report_path}")
```

## 🔍 **Data Validation APIs**

### Input Validator
Multi-level data validation with configurable strictness.

```python
from input_validator import InputValidator, ValidationLevel

# Initialize validator
validator = InputValidator(ValidationLevel.STRICT)

# Validate ticker symbol
is_valid = validator.validate_ticker("AAPL")
print(f"Ticker valid: {is_valid}")

# Validate financial data
validation_result = validator.validate_financial_data({
    'total_revenue': 365817,
    'operating_cash_flow': 99584,
    'capital_expenditures': -10708
})

if validation_result.is_valid:
    print("Data validation passed")
else:
    print(f"Validation errors: {validation_result.errors}")
```

## ⚠️ **Error Handling**

### Comprehensive Error Management
Structured error handling with detailed logging.

```python
from error_handler import ErrorHandler, FinancialDataError

# Initialize error handler
error_handler = ErrorHandler()

try:
    # Financial operations
    result = some_financial_calculation()
except FinancialDataError as e:
    # Handle financial-specific errors
    error_handler.handle_error(e, context="DCF Calculation")
    fallback_result = error_handler.get_fallback_value()
except Exception as e:
    # Handle general errors
    error_handler.log_error(e, severity="ERROR")

# Get error summary
error_summary = error_handler.get_error_summary()
print(f"Total errors: {error_summary['total_errors']}")
```

## 🎯 **Usage Examples**

### Complete Analysis Workflow
```python
from enhanced_data_manager import create_enhanced_data_manager
from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator

def analyze_company(ticker):
    # 1. Fetch market data
    manager = create_enhanced_data_manager()
    market_data = manager.fetch_market_data(ticker)
    
    if not market_data:
        return {"error": "Could not fetch market data"}
    
    # 2. Prepare financial calculator
    calculator = FinancialCalculator(f"temp_{ticker}")
    calculator.current_stock_price = market_data['current_price']
    calculator.market_cap = market_data['market_cap']
    calculator.shares_outstanding = market_data['shares_outstanding']
    
    # 3. Calculate FCF
    fcf_results = calculator.calculate_all_fcf_types()
    
    # 4. Perform DCF valuation
    dcf_valuator = DCFValuator(calculator)
    dcf_results = dcf_valuator.calculate_dcf_valuation()
    
    # 5. Return comprehensive results
    return {
        "ticker": ticker,
        "market_data": market_data,
        "fcf_analysis": fcf_results,
        "dcf_valuation": dcf_results,
        "data_source": manager._data_source_used
    }

# Execute analysis
results = analyze_company("AAPL")
print(f"Fair Value: ${results['dcf_valuation']['fair_value_per_share']:.2f}")
```

### Batch Analysis
```python
def batch_analyze(tickers):
    """Analyze multiple companies in batch"""
    manager = create_enhanced_data_manager()
    results = {}
    
    for ticker in tickers:
        try:
            print(f"Analyzing {ticker}...")
            results[ticker] = analyze_company(ticker)
        except Exception as e:
            results[ticker] = {"error": str(e)}
    
    manager.cleanup()
    return results

# Analyze portfolio
portfolio = ["AAPL", "MSFT", "GOOGL", "AMZN"]
analysis_results = batch_analyze(portfolio)

# Summary
for ticker, result in analysis_results.items():
    if "error" not in result:
        fair_value = result['dcf_valuation']['fair_value_per_share']
        current_price = result['market_data']['current_price']
        upside = (fair_value - current_price) / current_price * 100
        print(f"{ticker}: Fair Value ${fair_value:.2f}, Upside {upside:.1f}%")
```

## 🔒 **Security & Rate Limiting**

### API Rate Limiting
All providers implement intelligent rate limiting:

```python
# Rate limits are automatically enforced
provider = AlphaVantageProvider(config)

# Multiple rapid calls are automatically throttled
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    response = provider.fetch_data(FinancialDataRequest(ticker=ticker))
    # Automatic delays inserted to respect rate limits
```

### Credential Management
Secure handling of API credentials:

```python
# Credentials are never logged or exposed
config = DataSourceConfig(
    source_type=DataSourceType.ALPHA_VANTAGE,
    credentials=ApiCredentials(
        api_key="SECURE_KEY_HERE",  # Handled securely
        is_active=True
    )
)

# Validation without exposing keys
is_valid = provider.validate_credentials()  # Returns boolean only
```

## 📚 **Additional Resources**

- **Configuration Guide**: See `API_CONFIGURATION_GUIDE.md` for detailed setup instructions
- **Data Sources Guide**: See `ALTERNATIVE_DATA_SOURCES_GUIDE.md` for provider comparisons
- **Troubleshooting**: See main README.md troubleshooting section
- **Examples**: Check `example_usage.py` for practical implementation examples

---

For more information, see the complete documentation in the project repository.