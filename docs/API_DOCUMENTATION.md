# Financial Analysis Application - API Documentation

## 🌐 API Overview

The Financial Analysis Application provides a comprehensive programmatic interface for accessing financial calculations, valuations, and data processing capabilities. This API documentation covers both internal module APIs and external data source integrations.

## 📡 External Data Source APIs

### 1. Yahoo Finance (yfinance) Integration

**Purpose**: Primary free data source for market data and financial statements
**Priority**: Secondary (after Excel files)
**Rate Limits**: Built-in throttling, approximately 2000 requests/hour

#### Configuration
```python
from core.data_processing.adapters.yfinance_adapter import YFinanceAdapter

adapter = YFinanceAdapter()
adapter.configure({
    'timeout': 30,
    'retry_attempts': 3,
    'retry_delay': 1.0
})
```

#### Available Data
- **Market Data**: Current price, market cap, shares outstanding
- **Financial Statements**: Income statement, balance sheet, cash flow
- **Historical Data**: Price history, dividend history
- **Company Info**: Sector, industry, business description

#### Example Usage
```python
# Get market data
market_data = adapter.get_market_data('AAPL')
print(f"Current Price: ${market_data['current_price']}")
print(f"Market Cap: ${market_data['market_cap']:,.0f}")

# Get financial statements
financials = adapter.get_financial_statements('AAPL')
revenue = financials['income_statement']['Total Revenue']
```

### 2. Alpha Vantage API Integration

**Purpose**: Professional-grade financial data with extended coverage
**Priority**: Tertiary fallback
**Rate Limits**: 5 calls/minute (free), 75 calls/minute (premium)

#### Configuration
```python
from core.data_processing.adapters.alpha_vantage_adapter import AlphaVantageAdapter

adapter = AlphaVantageAdapter(api_key='YOUR_API_KEY')
adapter.configure({
    'rate_limit': 5,  # calls per minute
    'timeout': 60,
    'premium': False  # Set True for premium account
})
```

#### Available Endpoints
- **TIME_SERIES_DAILY**: Daily price and volume data
- **INCOME_STATEMENT**: Annual and quarterly income statements
- **BALANCE_SHEET**: Balance sheet data
- **CASH_FLOW**: Cash flow statements
- **OVERVIEW**: Company overview and key metrics

#### Example Usage
```python
# Get company overview
overview = adapter.get_company_overview('MSFT')
pe_ratio = overview.get('PERatio', 'N/A')

# Get financial statements
income_stmt = adapter.get_income_statement('MSFT', period='annual')
```

### 3. Financial Modeling Prep (FMP) API

**Purpose**: Comprehensive financial data with real-time updates
**Priority**: Quaternary fallback
**Rate Limits**: 250 calls/day (free), unlimited (premium)

#### Configuration
```python
from core.data_processing.adapters.fmp_adapter import FMPAdapter

adapter = FMPAdapter(api_key='YOUR_API_KEY')
adapter.configure({
    'base_url': 'https://financialmodelingprep.com/api/v3',
    'timeout': 30,
    'rate_limit': 250  # daily limit
})
```

#### Available Data
- **Real-time Quotes**: Live market data
- **Financial Ratios**: Comprehensive ratio analysis
- **DCF Valuations**: FMP's DCF calculations for comparison
- **Insider Trading**: Insider transaction data
- **Analyst Estimates**: Consensus estimates and recommendations

### 4. Polygon.io API Integration

**Purpose**: Real-time and historical market data
**Priority**: Final fallback
**Rate Limits**: 5 calls/minute (free), higher limits for paid plans

#### Configuration
```python
from core.data_processing.adapters.polygon_adapter import PolygonAdapter

adapter = PolygonAdapter(api_key='YOUR_API_KEY')
adapter.configure({
    'base_url': 'https://api.polygon.io',
    'timeout': 30
})
```

## 🔧 Core Financial Analysis APIs

### 1. Financial Calculator Engine

**Location**: `core/analysis/engines/financial_calculations.py`

#### Main Class: FinancialCalculator

##### Initialization
```python
from core.analysis.engines.financial_calculations import FinancialCalculator

calculator = FinancialCalculator()
calculator.set_ticker_symbol('AAPL')
calculator.set_data_directory('/path/to/data/companies/AAPL')
```

##### Core FCF Methods

###### calculate_fcfe()
```python
def calculate_fcfe(
    self,
    operating_cash_flow: float,
    capital_expenditures: float,
    net_debt_issued: float = 0.0,
    preferred_dividends: float = 0.0
) -> float:
    """
    Calculate Free Cash Flow to Equity

    Args:
        operating_cash_flow: Cash from operations
        capital_expenditures: Capital investments (usually negative)
        net_debt_issued: Net new debt issued (positive) or repaid (negative)
        preferred_dividends: Preferred dividend payments

    Returns:
        FCFE value in currency units

    Example:
        fcfe = calculator.calculate_fcfe(
            operating_cash_flow=50000,
            capital_expenditures=-10000,
            net_debt_issued=2000
        )
        # Returns: 42000
    """
```

###### calculate_fcff()
```python
def calculate_fcff(
    self,
    operating_cash_flow: float,
    capital_expenditures: float,
    tax_rate: float = 0.25,
    interest_expense: float = 0.0
) -> float:
    """
    Calculate Free Cash Flow to Firm

    Args:
        operating_cash_flow: Cash from operations
        capital_expenditures: Capital investments
        tax_rate: Corporate tax rate (0.0 to 1.0)
        interest_expense: Interest payments (for tax shield)

    Returns:
        FCFF value in currency units

    Example:
        fcff = calculator.calculate_fcff(
            operating_cash_flow=50000,
            capital_expenditures=-10000,
            tax_rate=0.25,
            interest_expense=3000
        )
        # Returns: 40750 (includes tax shield)
    """
```

###### calculate_levered_fcf()
```python
def calculate_levered_fcf(
    self,
    net_income: float,
    depreciation: float,
    capital_expenditures: float,
    working_capital_change: float
) -> float:
    """
    Calculate Levered Free Cash Flow

    Args:
        net_income: Net income from income statement
        depreciation: Depreciation and amortization
        capital_expenditures: Capital investments
        working_capital_change: Change in working capital

    Returns:
        Levered FCF value

    Example:
        levered_fcf = calculator.calculate_levered_fcf(
            net_income=30000,
            depreciation=5000,
            capital_expenditures=-10000,
            working_capital_change=-2000
        )
        # Returns: 27000
    """
```

##### Financial Ratio Methods

###### calculate_pe_ratio()
```python
def calculate_pe_ratio(
    self,
    price_per_share: float,
    earnings_per_share: float
) -> Optional[float]:
    """
    Calculate Price-to-Earnings ratio

    Returns:
        P/E ratio or None if EPS is zero/negative
    """
```

###### calculate_pb_ratio()
```python
def calculate_pb_ratio(
    self,
    price_per_share: float,
    book_value_per_share: float
) -> Optional[float]:
    """
    Calculate Price-to-Book ratio

    Returns:
        P/B ratio or None if book value is zero/negative
    """
```

##### Valuation Methods

###### calculate_enterprise_value()
```python
def calculate_enterprise_value(
    self,
    market_cap: float,
    total_debt: float,
    cash_and_equivalents: float
) -> float:
    """
    Calculate Enterprise Value

    Formula: Market Cap + Total Debt - Cash

    Returns:
        Enterprise value in currency units
    """
```

### 2. DCF Valuation Engine

**Location**: `core/analysis/dcf/dcf_valuation.py`

#### Main Class: DCFValuator

##### Initialization
```python
from core.analysis.dcf.dcf_valuation import DCFValuator

valuator = DCFValuator()
```

##### Core Methods

###### calculate_dcf_value()
```python
def calculate_dcf_value(
    self,
    cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float,
    terminal_year_cf: float
) -> Dict[str, float]:
    """
    Calculate DCF valuation

    Args:
        cash_flows: List of projected annual cash flows
        discount_rate: WACC or required rate of return (0.0 to 1.0)
        terminal_growth_rate: Long-term growth rate (0.0 to 1.0)
        terminal_year_cf: Cash flow in final forecast year

    Returns:
        Dictionary containing:
        - 'pv_cash_flows': Present value of forecast period cash flows
        - 'terminal_value': Terminal value
        - 'enterprise_value': Total enterprise value
        - 'fair_value_per_share': Equity value per share

    Example:
        result = valuator.calculate_dcf_value(
            cash_flows=[10000, 11000, 12100, 13310, 14641],
            discount_rate=0.10,
            terminal_growth_rate=0.025,
            terminal_year_cf=14641
        )
    """
```

### 3. DDM Valuation Engine

**Location**: `core/analysis/ddm/ddm_valuation.py`

#### Main Class: DDMValuator

##### Gordon Growth Model
```python
def gordon_growth_model(
    self,
    current_dividend: float,
    growth_rate: float,
    required_return: float
) -> float:
    """
    Calculate value using Gordon Growth DDM

    Formula: Value = D1 / (r - g)

    Args:
        current_dividend: Most recent dividend payment
        growth_rate: Expected dividend growth rate (0.0 to 1.0)
        required_return: Required rate of return (0.0 to 1.0)

    Returns:
        Intrinsic value per share

    Example:
        value = valuator.gordon_growth_model(
            current_dividend=2.50,
            growth_rate=0.05,
            required_return=0.10
        )
        # Returns: 52.50
    """
```

##### Two-Stage DDM
```python
def two_stage_ddm(
    self,
    current_dividend: float,
    high_growth_rate: float,
    high_growth_years: int,
    stable_growth_rate: float,
    required_return: float
) -> Dict[str, float]:
    """
    Calculate two-stage DDM value

    Returns:
        Dictionary with stage values and total value
    """
```

### 4. P/B Analysis Engine

**Location**: `core/analysis/pb/pb_valuation.py`

#### Main Class: PBValuator

##### Historical Analysis
```python
def analyze_historical_pb(
    self,
    ticker: str,
    years: int = 10
) -> Dict[str, Any]:
    """
    Perform historical P/B analysis

    Args:
        ticker: Stock ticker symbol
        years: Number of historical years to analyze

    Returns:
        Dictionary containing:
        - 'historical_data': List of P/B ratios by year
        - 'statistics': Mean, median, percentiles
        - 'current_ratio': Current P/B ratio
        - 'percentile_rank': Current ratio percentile
        - 'quality_score': Data quality assessment
    """
```

## 🔄 Data Processing APIs

### 1. Enhanced Data Manager

**Location**: `core/data_processing/managers/enhanced_data_manager.py`

#### Main Class: EnhancedDataManager

##### Multi-Source Data Fetching
```python
from core.data_processing.managers.enhanced_data_manager import EnhancedDataManager

manager = EnhancedDataManager()

# Automatic source selection with fallback
data = manager.fetch_market_data('AAPL')
# Tries: Excel → yfinance → Alpha Vantage → FMP → Polygon

# Get data with source preference
data = manager.fetch_financial_statements(
    ticker='AAPL',
    preferred_source='yfinance'
)
```

##### Quality Assessment
```python
def assess_data_quality(
    self,
    data: Dict[str, Any],
    data_type: str
) -> Dict[str, Any]:
    """
    Assess data quality and assign score

    Returns:
        {
            'overall_score': 85.0,
            'completeness': 90.0,
            'consistency': 80.0,
            'accuracy': 85.0,
            'timeliness': 90.0,
            'issues': ['Minor data gaps in historical data'],
            'recommendations': ['Verify recent quarter data']
        }
    """
```

### 2. Universal Data Registry

**Location**: `core/data_processing/processors/universal_data_registry.py`

#### Configuration-Driven Data Management
```python
from core.data_processing.processors.universal_data_registry import UniversalDataRegistry

registry = UniversalDataRegistry()

# Register data source with configuration
registry.register_source('custom_api', {
    'adapter_class': 'CustomAPIAdapter',
    'priority': 3,
    'quality_threshold': 75.0,
    'rate_limit': 100,
    'timeout': 30
})

# Get standardized data
standardized_data = registry.get_standardized_data('AAPL', 'financial_statements')
```

## 🔧 Configuration APIs

### 1. Application Configuration

**Location**: `config/config.py`

#### Configuration Classes
```python
from config.config import get_config, get_dcf_config

# Get application configuration
app_config = get_config()
print(f"API Timeout: {app_config.api_timeout}")
print(f"Cache Expiry: {app_config.cache_expiry_hours}")

# Get DCF-specific configuration
dcf_config = get_dcf_config()
print(f"Default Discount Rate: {dcf_config.default_discount_rate}")
print(f"Terminal Growth Rate: {dcf_config.default_terminal_growth_rate}")
```

### 2. Constants and Settings

**Location**: `config/constants.py`

#### Financial Constants
```python
from config.constants import (
    FINANCIAL_SCALE_FACTOR,
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_TERMINAL_GROWTH_RATE,
    STATEMENT_NAMES
)

# Use constants in calculations
scaled_value = raw_value / FINANCIAL_SCALE_FACTOR
```

## 🚀 Integration Examples

### Example 1: Complete FCF Analysis Workflow

```python
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.managers.enhanced_data_manager import EnhancedDataManager

# Initialize components
calculator = FinancialCalculator()
data_manager = EnhancedDataManager()

# Set up analysis
ticker = 'AAPL'
calculator.set_ticker_symbol(ticker)

# Fetch data with automatic fallback
try:
    # Try to get data from multiple sources
    financial_data = data_manager.fetch_financial_statements(ticker)
    market_data = data_manager.fetch_market_data(ticker)

    # Assess data quality
    quality = data_manager.assess_data_quality(financial_data, 'financial_statements')
    print(f"Data quality score: {quality['overall_score']}")

    if quality['overall_score'] >= 75:
        # Proceed with analysis
        ocf = financial_data['cash_flow']['Operating Cash Flow']
        capex = financial_data['cash_flow']['Capital Expenditures']

        # Calculate FCF types
        fcfe = calculator.calculate_fcfe(ocf, capex)
        fcff = calculator.calculate_fcff(ocf, capex)
        levered_fcf = calculator.calculate_levered_fcf(
            financial_data['income']['Net Income'],
            financial_data['income']['Depreciation'],
            capex,
            financial_data['balance_sheet']['Working Capital Change']
        )

        print(f"FCFE: ${fcfe:,.0f}")
        print(f"FCFF: ${fcff:,.0f}")
        print(f"Levered FCF: ${levered_fcf:,.0f}")

    else:
        print(f"Data quality too low: {quality['overall_score']}")
        print(f"Issues: {quality['issues']}")

except Exception as e:
    print(f"Analysis failed: {e}")
```

### Example 2: Portfolio Valuation Analysis

```python
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.portfolio.portfolio_optimization import PortfolioOptimizer

# Portfolio of stocks to analyze
portfolio_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
portfolio_weights = [0.25, 0.25, 0.20, 0.20, 0.10]

# Initialize components
calculator = FinancialCalculator()
dcf_valuator = DCFValuator()
optimizer = PortfolioOptimizer()

portfolio_results = {}

# Analyze each position
for ticker in portfolio_tickers:
    try:
        # Set up calculator for this ticker
        calculator.set_ticker_symbol(ticker)

        # Get required data (with automatic fallback)
        if calculator.has_required_data():
            # Calculate FCF and growth metrics
            fcf_data = calculator.calculate_all_fcf_types()

            # Perform DCF valuation
            dcf_result = dcf_valuator.calculate_comprehensive_dcf(ticker)

            # Store results
            portfolio_results[ticker] = {
                'fcf_data': fcf_data,
                'dcf_valuation': dcf_result,
                'current_price': calculator.get_current_price(),
                'fair_value': dcf_result['fair_value_per_share']
            }

            print(f"{ticker}: Fair Value ${dcf_result['fair_value_per_share']:.2f}")

    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")

# Optimize portfolio allocation
if len(portfolio_results) >= 3:
    optimization_result = optimizer.optimize_portfolio(
        tickers=list(portfolio_results.keys()),
        target_return=0.12,
        risk_tolerance='moderate'
    )

    print(f"\nOptimized Allocation:")
    for ticker, weight in optimization_result['optimal_weights'].items():
        print(f"{ticker}: {weight:.1%}")
```

## 🔍 Error Handling and Best Practices

### Standard Error Handling
```python
from core.data_processing.exceptions import (
    DataSourceException,
    RateLimitException,
    ValidationException
)

try:
    data = data_manager.fetch_market_data('INVALID_TICKER')
except DataSourceException as e:
    print(f"Data source error: {e}")
    # Implement fallback logic
except RateLimitException as e:
    print(f"Rate limit exceeded: {e}")
    # Implement retry with backoff
except ValidationException as e:
    print(f"Data validation failed: {e}")
    # Request user input or use alternative data
```

### API Response Format Standards
All APIs return standardized response format:
```python
{
    'success': True,
    'data': {...},
    'metadata': {
        'source': 'yfinance',
        'timestamp': '2024-01-01T12:00:00Z',
        'quality_score': 85.0
    },
    'errors': [],
    'warnings': ['Minor data gap in Q3 2023']
}
```

### Rate Limiting Best Practices
```python
from core.data_processing.rate_limiting import RateLimiter

# Configure rate limiter
limiter = RateLimiter(
    calls_per_minute=60,
    calls_per_hour=1000,
    calls_per_day=10000
)

# Use with API calls
@limiter.limit
def api_call():
    return make_request()
```

---

*This API documentation provides comprehensive coverage of all programmatic interfaces available in the Financial Analysis Application. For specific implementation details, refer to the inline code documentation and test suites.*