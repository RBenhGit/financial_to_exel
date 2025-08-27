"""
Standardized Data Contracts Module
=================================

This module defines unified data interfaces and contracts for financial data exchange
between all modules in the valuation analysis system. It provides standardized field
names, data types, validation schemas, and response formats to ensure consistent
data flow and minimal coupling between components.

Key Features
------------
- **Unified Data Models**: Standard dataclasses for all financial data types
- **Field Standardization**: Consistent field names across all data sources
- **Type Safety**: Strong typing for all financial metrics and calculations
- **Validation Schemas**: Built-in data validation and quality checks
- **Version Compatibility**: Schema versioning for backward compatibility
- **Documentation**: Self-documenting contracts with field descriptions

Usage Example
-------------
>>> from data_contracts import FinancialStatement, MarketData, CalculationResult
>>> 
>>> # Standard financial statement data
>>> stmt = FinancialStatement(
...     ticker="AAPL",
...     period="2023",
...     revenue=394328000000,
...     net_income=96995000000
... )
>>> 
>>> # Unified market data
>>> market = MarketData(
...     ticker="AAPL", 
...     price=189.95,
...     market_cap=2_950_000_000_000
... )
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union, Literal
from enum import Enum
import numpy as np
from decimal import Decimal

# Schema version for backward compatibility
SCHEMA_VERSION = "1.0.0"


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # 95%+ completeness, high accuracy
    GOOD = "good"           # 85-94% completeness, good accuracy  
    FAIR = "fair"           # 75-84% completeness, moderate accuracy
    POOR = "poor"           # <75% completeness, low accuracy
    UNKNOWN = "unknown"     # Quality not assessed


class DataSourceType(Enum):
    """Standardized data source types"""
    EXCEL = "excel"
    API_YFINANCE = "yfinance"
    API_ALPHA_VANTAGE = "alpha_vantage"
    API_FMP = "financial_modeling_prep"
    API_POLYGON = "polygon"
    USER_INPUT = "user_input"
    CALCULATED = "calculated"
    CACHED = "cached"


class PeriodType(Enum):
    """Financial reporting periods"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "ttm"  # Trailing Twelve Months
    LTM = "ltm"  # Last Twelve Months
    DAILY = "daily"
    MONTHLY = "monthly"


class CurrencyCode(Enum):
    """ISO currency codes"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    ILS = "ILS"  # Israeli Shekel for TASE support
    CAD = "CAD"


@dataclass
class DataQualityMetrics:
    """Standardized data quality assessment"""
    completeness: float = 0.0      # 0-1, percentage of non-null fields
    accuracy: float = 0.0          # 0-1, estimated accuracy score
    timeliness: float = 0.0        # 0-1, how recent/current the data is
    consistency: float = 0.0       # 0-1, consistency with other sources
    overall_quality: DataQuality = DataQuality.UNKNOWN
    
    def __post_init__(self):
        """Calculate overall quality rating"""
        avg_score = (self.completeness + self.accuracy + 
                    self.timeliness + self.consistency) / 4
        
        if avg_score >= 0.95:
            self.overall_quality = DataQuality.EXCELLENT
        elif avg_score >= 0.85:
            self.overall_quality = DataQuality.GOOD
        elif avg_score >= 0.75:
            self.overall_quality = DataQuality.FAIR
        else:
            self.overall_quality = DataQuality.POOR


@dataclass 
class MetadataInfo:
    """Standard metadata for all data contracts"""
    schema_version: str = SCHEMA_VERSION
    source_type: DataSourceType = DataSourceType.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    data_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    source_identifier: Optional[str] = None  # e.g., "yfinance_v1.2.3"
    request_id: Optional[str] = None         # For traceability


@dataclass
class FinancialStatement:
    """Standardized financial statement data contract"""
    
    # Identity
    ticker: str
    company_name: Optional[str] = None
    period: str = "2023"  # e.g., "2023", "2023Q4"
    period_type: PeriodType = PeriodType.ANNUAL
    currency: CurrencyCode = CurrencyCode.USD
    fiscal_year_end: Optional[date] = None
    
    # Income Statement (in base currency units, e.g., USD)
    revenue: Optional[float] = None
    total_revenue: Optional[float] = None  # Alias for revenue
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebit: Optional[float] = None           # Earnings Before Interest & Tax
    ebitda: Optional[float] = None         # EBIT + Depreciation & Amortization
    interest_expense: Optional[float] = None
    pretax_income: Optional[float] = None
    tax_expense: Optional[float] = None
    net_income: Optional[float] = None
    earnings_per_share: Optional[float] = None
    diluted_eps: Optional[float] = None
    shares_outstanding: Optional[float] = None
    weighted_avg_shares: Optional[float] = None
    
    # Cash Flow Statement
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    capex: Optional[float] = None          # Alias for capital_expenditures
    free_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    
    # Balance Sheet
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    short_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    retained_earnings: Optional[float] = None
    book_value: Optional[float] = None
    tangible_book_value: Optional[float] = None
    working_capital: Optional[float] = None
    
    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)
    
    def __post_init__(self):
        """Validate and standardize data after initialization"""
        # Set aliases
        if self.total_revenue and not self.revenue:
            self.revenue = self.total_revenue
        elif self.revenue and not self.total_revenue:
            self.total_revenue = self.revenue
            
        if self.capex and not self.capital_expenditures:
            self.capital_expenditures = self.capex
        elif self.capital_expenditures and not self.capex:
            self.capex = self.capital_expenditures
            
        # Calculate derived metrics if missing
        if not self.working_capital and self.current_assets and self.current_liabilities:
            self.working_capital = self.current_assets - self.current_liabilities


@dataclass
class MarketData:
    """Standardized market data contract"""
    
    # Identity
    ticker: str
    exchange: Optional[str] = None
    currency: CurrencyCode = CurrencyCode.USD
    data_date: Optional[date] = None
    
    # Price Data
    price: Optional[float] = None          # Current/closing price
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    previous_close: Optional[float] = None
    
    # Market Metrics
    market_cap: Optional[float] = None     # In currency units
    enterprise_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    
    # Valuation Ratios
    pe_ratio: Optional[float] = None       # Price-to-Earnings
    pb_ratio: Optional[float] = None       # Price-to-Book
    ps_ratio: Optional[float] = None       # Price-to-Sales
    peg_ratio: Optional[float] = None      # Price/Earnings to Growth
    ev_revenue: Optional[float] = None     # EV/Revenue
    ev_ebitda: Optional[float] = None      # EV/EBITDA
    
    # Dividend Information
    dividend_yield: Optional[float] = None  # As decimal (0.025 = 2.5%)
    dividend_per_share: Optional[float] = None
    dividend_payout_ratio: Optional[float] = None
    
    # Technical Indicators
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    moving_avg_50: Optional[float] = None
    moving_avg_200: Optional[float] = None
    
    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


@dataclass
class CalculationResult:
    """Standardized calculation result contract"""
    
    # Identity
    ticker: str
    calculation_type: str                  # e.g., "DCF", "DDM", "FCF_Analysis"
    calculation_date: datetime = field(default_factory=datetime.now)
    
    # Primary Results
    intrinsic_value: Optional[float] = None
    fair_value: Optional[float] = None     # Alias for intrinsic_value
    current_price: Optional[float] = None
    upside_downside: Optional[float] = None  # Percentage difference
    recommendation: Optional[str] = None    # "BUY", "HOLD", "SELL"
    
    # Supporting Calculations
    discount_rate: Optional[float] = None   # WACC or required return
    terminal_growth_rate: Optional[float] = None
    risk_free_rate: Optional[float] = None
    market_risk_premium: Optional[float] = None
    
    # Cash Flow Projections (list of annual values)
    projected_cash_flows: Optional[List[float]] = None
    terminal_value: Optional[float] = None
    present_value_factors: Optional[List[float]] = None
    
    # Sensitivity Analysis
    sensitivity_ranges: Optional[Dict[str, List[float]]] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    
    # Quality Assessment
    calculation_quality: DataQuality = DataQuality.UNKNOWN
    data_completeness: float = 0.0
    assumptions_used: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.fair_value and not self.intrinsic_value:
            self.intrinsic_value = self.fair_value
        elif self.intrinsic_value and not self.fair_value:
            self.fair_value = self.intrinsic_value
            
        if self.intrinsic_value and self.current_price:
            self.upside_downside = ((self.intrinsic_value / self.current_price) - 1) * 100


@dataclass
class ValidationResult:
    """Result of data validation operations"""
    
    is_valid: bool
    field_name: str
    expected_type: str
    actual_value: Any
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    validation_rule: Optional[str] = None
    
    
@dataclass  
class DataRequest:
    """Standardized request for financial data"""
    
    ticker: str
    data_types: List[str] = field(default_factory=lambda: ["fundamentals", "market"])
    period_type: PeriodType = PeriodType.ANNUAL
    periods_requested: int = 5             # Number of historical periods
    include_current: bool = True
    force_refresh: bool = False
    
    # Source preferences
    preferred_sources: Optional[List[DataSourceType]] = None
    exclude_sources: Optional[List[DataSourceType]] = None
    quality_threshold: DataQuality = DataQuality.FAIR
    
    # Request metadata
    request_id: str = field(default_factory=lambda: f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    requester: Optional[str] = None
    timeout_seconds: int = 30


@dataclass
class DataResponse:
    """Standardized response for financial data requests"""
    
    request_id: str
    success: bool
    ticker: str
    
    # Data payload
    financial_statements: Optional[List[FinancialStatement]] = None
    market_data: Optional[MarketData] = None
    calculation_results: Optional[List[CalculationResult]] = None
    
    # Response metadata
    sources_used: List[DataSourceType] = field(default_factory=list)
    response_time_ms: float = 0.0
    cache_hit: bool = False
    data_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


# Field mapping dictionaries for data source standardization
FIELD_MAPPINGS = {
    "yfinance": {
        "totalRevenue": "revenue",
        "operatingCashFlow": "operating_cash_flow", 
        "capitalExpenditures": "capital_expenditures",
        "marketCap": "market_cap",
        "bookValue": "book_value",
        "priceToBook": "pb_ratio",
        "forwardPE": "pe_ratio",
        "dividendYield": "dividend_yield",
        "beta": "beta"
    },
    "alpha_vantage": {
        "totalRevenue": "revenue",
        "netIncome": "net_income", 
        "totalAssets": "total_assets",
        "totalLiabilities": "total_liabilities"
    },
    "fmp": {
        "revenue": "revenue",
        "netIncome": "net_income",
        "operatingCashFlow": "operating_cash_flow",
        "capex": "capital_expenditures"
    }
}


def standardize_field_names(data: Dict[str, Any], source_type: DataSourceType) -> Dict[str, Any]:
    """
    Standardize field names from various data sources to our unified schema
    
    Args:
        data: Raw data dictionary from source
        source_type: The data source type
        
    Returns:
        Dictionary with standardized field names
    """
    if source_type.value not in FIELD_MAPPINGS:
        return data
        
    mapping = FIELD_MAPPINGS[source_type.value]
    standardized = {}
    
    for key, value in data.items():
        # Use mapping if available, otherwise keep original key
        standard_key = mapping.get(key, key)
        standardized[standard_key] = value
        
    return standardized


def validate_contract(contract: Union[FinancialStatement, MarketData, CalculationResult]) -> List[ValidationResult]:
    """
    Validate a data contract instance for completeness and correctness
    
    Args:
        contract: The data contract instance to validate
        
    Returns:
        List of validation results
    """
    results = []
    
    # Basic validation - ticker must be present and valid
    if not contract.ticker or len(contract.ticker.strip()) == 0:
        results.append(ValidationResult(
            is_valid=False,
            field_name="ticker",
            expected_type="str",
            actual_value=contract.ticker,
            error_message="Ticker is required and cannot be empty"
        ))
    
    # Type-specific validation
    if isinstance(contract, FinancialStatement):
        results.extend(_validate_financial_statement(contract))
    elif isinstance(contract, MarketData):
        results.extend(_validate_market_data(contract))
    elif isinstance(contract, CalculationResult):
        results.extend(_validate_calculation_result(contract))
        
    return results


def _validate_financial_statement(stmt: FinancialStatement) -> List[ValidationResult]:
    """Validate financial statement specific rules"""
    results = []
    
    # Revenue should be positive for most companies
    if stmt.revenue is not None and stmt.revenue < 0:
        results.append(ValidationResult(
            is_valid=False,
            field_name="revenue",
            expected_type="positive float",
            actual_value=stmt.revenue,
            warning_message="Revenue is negative - please verify"
        ))
    
    # Basic accounting equation check: Assets = Liabilities + Equity
    if all(x is not None for x in [stmt.total_assets, stmt.total_liabilities, stmt.shareholders_equity]):
        expected_assets = stmt.total_liabilities + stmt.shareholders_equity
        if abs(stmt.total_assets - expected_assets) / stmt.total_assets > 0.05:  # 5% tolerance
            results.append(ValidationResult(
                is_valid=False,
                field_name="balance_sheet",
                expected_type="balanced equation",
                actual_value=f"Assets: {stmt.total_assets}, Liab+Equity: {expected_assets}",
                warning_message="Balance sheet equation doesn't balance within 5% tolerance"
            ))
            
    return results


def _validate_market_data(market: MarketData) -> List[ValidationResult]:
    """Validate market data specific rules"""  
    results = []
    
    # Price should be positive
    if market.price is not None and market.price <= 0:
        results.append(ValidationResult(
            is_valid=False,
            field_name="price", 
            expected_type="positive float",
            actual_value=market.price,
            error_message="Stock price must be positive"
        ))
    
    # Market cap consistency check
    if all(x is not None for x in [market.price, market.shares_outstanding, market.market_cap]):
        calculated_market_cap = market.price * market.shares_outstanding
        if abs(market.market_cap - calculated_market_cap) / market.market_cap > 0.10:  # 10% tolerance
            results.append(ValidationResult(
                is_valid=False,
                field_name="market_cap",
                expected_type="price * shares",
                actual_value=market.market_cap,
                warning_message=f"Market cap inconsistent with price×shares: {calculated_market_cap}"
            ))
            
    return results


def _validate_calculation_result(calc: CalculationResult) -> List[ValidationResult]:
    """Validate calculation result specific rules"""
    results = []
    
    # Fair value should be positive
    if calc.fair_value is not None and calc.fair_value <= 0:
        results.append(ValidationResult(
            is_valid=False,
            field_name="fair_value",
            expected_type="positive float",
            actual_value=calc.fair_value,
            error_message="Fair value should be positive"
        ))
    
    # Discount rate should be reasonable (0-50%)
    if calc.discount_rate is not None:
        if calc.discount_rate < 0 or calc.discount_rate > 0.5:
            results.append(ValidationResult(
                is_valid=False,
                field_name="discount_rate", 
                expected_type="0.0 to 0.5",
                actual_value=calc.discount_rate,
                warning_message="Discount rate seems unreasonable (should be 0-50%)"
            ))
            
    return results