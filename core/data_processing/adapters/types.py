"""
Adapter Type Definitions
========================

Type definitions and data structures for the standardized adapter interface.
All adapters must conform to these types to ensure consistent data flow.

This module defines:
- GeneralizedVariableDict: Standard output format for all adapters
- AdapterOutputMetadata: Metadata accompanying adapter outputs
- ValidationResult: Result of validation operations
- AdapterException: Standard exception for adapter failures
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum


class GeneralizedVariableDict(TypedDict, total=False):
    """
    Standardized output format for all financial data adapters.

    This is the canonical format that ALL adapters (Excel, yfinance, FMP,
    Alpha Vantage, Polygon) must transform their data into. Keys are
    standardized variable names from FinancialVariableRegistry.

    All financial values are in millions USD unless otherwise specified.
    All percentages are stored as decimals (0.15 = 15%).

    Required Fields:
        ticker: Company ticker symbol
        company_name: Full company name
        currency: Currency code (e.g., "USD")
        fiscal_year_end: Fiscal year end month

    Optional Fields:
        All other fields are optional and should be included if available
        from the data source.
    """

    # === METADATA (Required) ===
    ticker: str                          # Company ticker symbol
    company_name: str                    # Full company name
    currency: str                        # "USD", "EUR", etc.
    fiscal_year_end: str                 # "December", "June", etc.

    # === INCOME STATEMENT (Millions USD) ===
    revenue: Optional[float]
    cost_of_revenue: Optional[float]
    gross_profit: Optional[float]
    operating_expenses: Optional[float]
    research_and_development: Optional[float]
    selling_general_administrative: Optional[float]
    operating_income: Optional[float]
    interest_expense: Optional[float]
    interest_income: Optional[float]
    other_income_expense: Optional[float]
    income_before_tax: Optional[float]
    income_tax_expense: Optional[float]
    net_income: Optional[float]
    net_income_continuing_ops: Optional[float]
    eps_basic: Optional[float]
    eps_diluted: Optional[float]
    weighted_average_shares_basic: Optional[float]
    weighted_average_shares_diluted: Optional[float]
    ebitda: Optional[float]
    ebit: Optional[float]

    # === BALANCE SHEET (Millions USD) ===
    cash_and_cash_equivalents: Optional[float]
    short_term_investments: Optional[float]
    accounts_receivable: Optional[float]
    inventory: Optional[float]
    other_current_assets: Optional[float]
    total_current_assets: Optional[float]
    property_plant_equipment_net: Optional[float]
    goodwill: Optional[float]
    intangible_assets: Optional[float]
    long_term_investments: Optional[float]
    other_non_current_assets: Optional[float]
    total_non_current_assets: Optional[float]
    total_assets: Optional[float]
    accounts_payable: Optional[float]
    short_term_debt: Optional[float]
    current_portion_long_term_debt: Optional[float]
    accrued_liabilities: Optional[float]
    deferred_revenue_current: Optional[float]
    other_current_liabilities: Optional[float]
    total_current_liabilities: Optional[float]
    long_term_debt: Optional[float]
    deferred_revenue_non_current: Optional[float]
    deferred_tax_liabilities: Optional[float]
    other_non_current_liabilities: Optional[float]
    total_non_current_liabilities: Optional[float]
    total_liabilities: Optional[float]
    common_stock: Optional[float]
    retained_earnings: Optional[float]
    accumulated_other_comprehensive_income: Optional[float]
    total_stockholders_equity: Optional[float]
    total_liabilities_and_equity: Optional[float]

    # === CASH FLOW STATEMENT (Millions USD) ===
    net_income_cash_flow: Optional[float]
    depreciation_and_amortization: Optional[float]
    stock_based_compensation: Optional[float]
    change_in_working_capital: Optional[float]
    change_in_accounts_receivable: Optional[float]
    change_in_inventory: Optional[float]
    change_in_accounts_payable: Optional[float]
    other_operating_activities: Optional[float]
    operating_cash_flow: Optional[float]
    capital_expenditures: Optional[float]
    acquisitions: Optional[float]
    purchases_of_investments: Optional[float]
    sales_of_investments: Optional[float]
    other_investing_activities: Optional[float]
    investing_cash_flow: Optional[float]
    debt_repayment: Optional[float]
    debt_issuance: Optional[float]
    common_stock_issued: Optional[float]
    common_stock_repurchased: Optional[float]
    dividends_paid: Optional[float]
    other_financing_activities: Optional[float]
    financing_cash_flow: Optional[float]
    net_change_in_cash: Optional[float]
    free_cash_flow: Optional[float]

    # === MARKET DATA ===
    stock_price: Optional[float]
    market_cap: Optional[float]
    enterprise_value: Optional[float]
    shares_outstanding: Optional[float]
    beta: Optional[float]
    dividend_yield: Optional[float]           # As decimal (0.025 = 2.5%)
    dividend_per_share: Optional[float]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_sales: Optional[float]
    price_to_book: Optional[float]
    ev_to_revenue: Optional[float]
    ev_to_ebitda: Optional[float]

    # === FINANCIAL RATIOS ===
    # Profitability Ratios
    gross_margin: Optional[float]              # As decimal (0.40 = 40%)
    operating_margin: Optional[float]          # As decimal
    net_margin: Optional[float]                # As decimal
    return_on_assets: Optional[float]          # As decimal
    return_on_equity: Optional[float]          # As decimal
    return_on_invested_capital: Optional[float]  # As decimal
    asset_turnover: Optional[float]

    # Liquidity Ratios
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    cash_ratio: Optional[float]
    working_capital: Optional[float]           # Millions USD

    # Leverage Ratios
    debt_to_equity: Optional[float]
    debt_to_assets: Optional[float]
    equity_multiplier: Optional[float]
    interest_coverage: Optional[float]
    debt_service_coverage: Optional[float]

    # Efficiency Ratios
    inventory_turnover: Optional[float]
    days_inventory_outstanding: Optional[float]
    receivables_turnover: Optional[float]
    days_sales_outstanding: Optional[float]
    payables_turnover: Optional[float]
    days_payables_outstanding: Optional[float]
    cash_conversion_cycle: Optional[float]

    # === GROWTH METRICS (Year-over-Year) ===
    revenue_growth: Optional[float]            # As decimal (0.15 = 15% growth)
    revenue_growth_3y_avg: Optional[float]
    revenue_growth_5y_avg: Optional[float]
    earnings_growth: Optional[float]           # As decimal
    earnings_growth_3y_avg: Optional[float]
    earnings_growth_5y_avg: Optional[float]
    eps_growth: Optional[float]                # As decimal
    operating_cash_flow_growth: Optional[float]
    free_cash_flow_growth: Optional[float]
    book_value_growth: Optional[float]

    # === VALUATION METRICS ===
    price_to_earnings_growth: Optional[float]  # PEG ratio
    price_to_cash_flow: Optional[float]
    price_to_free_cash_flow: Optional[float]
    ev_to_sales: Optional[float]
    ev_to_operating_cash_flow: Optional[float]
    ev_to_free_cash_flow: Optional[float]
    earnings_yield: Optional[float]            # As decimal (inverse of P/E)
    free_cash_flow_yield: Optional[float]      # As decimal

    # === QUALITY METRICS ===
    piotroski_f_score: Optional[int]           # 0-9 financial strength score
    altman_z_score: Optional[float]            # Bankruptcy prediction
    beneish_m_score: Optional[float]           # Earnings manipulation detection
    quality_of_earnings: Optional[float]       # Cash flow / Net income
    accrual_ratio: Optional[float]

    # === COMPANY INFORMATION ===
    sector: Optional[str]                      # Technology, Healthcare, etc.
    industry: Optional[str]                    # Software, Pharmaceuticals, etc.
    country: Optional[str]                     # Country of incorporation
    exchange: Optional[str]                    # NYSE, NASDAQ, etc.
    employees: Optional[int]                   # Number of employees
    founded_year: Optional[int]
    description: Optional[str]                 # Company description
    website: Optional[str]
    ceo: Optional[str]

    # === DIVIDEND METRICS ===
    dividend_payout_ratio: Optional[float]     # As decimal
    dividend_growth_rate: Optional[float]      # As decimal
    consecutive_dividend_years: Optional[int]

    # === SHARE METRICS ===
    float_shares: Optional[float]              # Millions
    insider_ownership: Optional[float]         # As decimal (0.10 = 10%)
    institutional_ownership: Optional[float]   # As decimal
    short_interest: Optional[float]            # As decimal
    short_ratio: Optional[float]               # Days to cover

    # === DCF & VALUATION INPUTS ===
    wacc: Optional[float]                      # As decimal
    cost_of_equity: Optional[float]            # As decimal
    cost_of_debt: Optional[float]              # As decimal
    tax_rate: Optional[float]                  # As decimal
    terminal_growth_rate: Optional[float]      # As decimal
    intrinsic_value_per_share: Optional[float]
    fair_value_per_share: Optional[float]

    # === ANALYST ESTIMATES ===
    analyst_target_price: Optional[float]
    analyst_recommendation: Optional[str]      # "Buy", "Sell", "Hold"
    number_of_analysts: Optional[int]
    estimated_revenue_current_year: Optional[float]
    estimated_revenue_next_year: Optional[float]
    estimated_eps_current_year: Optional[float]
    estimated_eps_next_year: Optional[float]

    # === HISTORICAL DATA (Lists of values) ===
    historical_revenue: Optional[List[float]]
    historical_net_income: Optional[List[float]]
    historical_operating_cash_flow: Optional[List[float]]
    historical_free_cash_flow: Optional[List[float]]
    historical_eps: Optional[List[float]]
    historical_dates: Optional[List[date]]
    historical_stock_prices: Optional[List[float]]
    historical_dividends: Optional[List[float]]

    # === DATA QUALITY & METADATA ===
    data_source: Optional[str]                 # "excel", "yfinance", "fmp", etc.
    data_timestamp: Optional[datetime]         # When data was last updated
    reporting_period: Optional[str]            # "Q1 2024", "FY 2023", etc.
    reporting_period_end: Optional[date]       # Actual date of period end
    filing_date: Optional[date]                # When financials were filed
    restated: Optional[bool]                   # Whether data has been restated
    data_quality_score: Optional[float]        # 0.0 - 1.0
    completeness_score: Optional[float]        # 0.0 - 1.0
    last_updated: Optional[datetime]           # Last modification timestamp
    notes: Optional[str]                       # Additional notes or caveats


@dataclass
class AdapterOutputMetadata:
    """
    Metadata accompanying adapter output.

    Provides quality metrics, provenance information, and validation status
    for data extracted by adapters.
    """
    source: str                              # "excel", "yfinance", "fmp", etc.
    timestamp: datetime                      # When data was acquired
    quality_score: float                     # 0.0 - 1.0 data quality metric
    completeness: float                      # 0.0 - 1.0 field completeness
    validation_errors: List[str] = field(default_factory=list)
    raw_data_hash: Optional[str] = None      # Hash of raw input for change detection
    extraction_time: float = 0.0             # Time taken to extract (seconds)
    cache_hit: bool = False                  # Whether data came from cache
    api_calls_made: int = 0                  # Number of API calls required

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'quality_score': self.quality_score,
            'completeness': self.completeness,
            'validation_errors': self.validation_errors,
            'raw_data_hash': self.raw_data_hash,
            'extraction_time': self.extraction_time,
            'cache_hit': self.cache_hit,
            'api_calls_made': self.api_calls_made
        }


@dataclass
class ValidationResult:
    """
    Result of validation operation.

    Contains validation status, any errors or warnings encountered,
    and details about what was validated.
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_type: str = "general"
    details: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message"""
        self.warnings.append(warning)

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one"""
        if not other.valid:
            self.valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.details.update(other.details)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'validation_type': self.validation_type,
            'details': self.details
        }


class AdapterException(Exception):
    """
    Standard exception for adapter failures.

    Raised when an adapter encounters an error during data extraction,
    transformation, or validation.
    """

    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.source = source
        self.original_exception = original_exception
        self.details = details or {}

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.source:
            parts.append(f"Source: {self.source}")
        if self.original_exception:
            parts.append(f"Original: {str(self.original_exception)}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class AdapterStatus(Enum):
    """Status of an adapter"""
    READY = "ready"                    # Adapter is ready to use
    BUSY = "busy"                      # Currently processing a request
    ERROR = "error"                    # Last operation failed
    RATE_LIMITED = "rate_limited"      # Hit rate limit, waiting
    UNAVAILABLE = "unavailable"        # Service unavailable


@dataclass
class AdapterInfo:
    """Information about an adapter's capabilities and status"""
    adapter_type: str                  # "excel", "yfinance", etc.
    status: AdapterStatus
    supported_categories: List[str]
    requires_api_key: bool
    rate_limit_per_minute: int
    last_request_time: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return 1.0 - (self.failed_requests / self.total_requests)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'adapter_type': self.adapter_type,
            'status': self.status.value,
            'supported_categories': self.supported_categories,
            'requires_api_key': self.requires_api_key,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.success_rate
        }


# Standard required fields that all adapters must provide
REQUIRED_FIELDS = ['ticker', 'company_name', 'currency', 'fiscal_year_end']

# Categories of financial data
INCOME_STATEMENT_FIELDS = [
    'revenue', 'cost_of_revenue', 'gross_profit', 'operating_expenses',
    'research_and_development', 'selling_general_administrative',
    'operating_income', 'interest_expense', 'interest_income',
    'other_income_expense', 'income_before_tax', 'income_tax_expense',
    'net_income', 'net_income_continuing_ops', 'eps_basic', 'eps_diluted',
    'weighted_average_shares_basic', 'weighted_average_shares_diluted',
    'ebitda', 'ebit'
]

BALANCE_SHEET_FIELDS = [
    'cash_and_cash_equivalents', 'short_term_investments', 'accounts_receivable',
    'inventory', 'other_current_assets', 'total_current_assets',
    'property_plant_equipment_net', 'goodwill', 'intangible_assets',
    'long_term_investments', 'other_non_current_assets',
    'total_non_current_assets', 'total_assets', 'accounts_payable',
    'short_term_debt', 'current_portion_long_term_debt', 'accrued_liabilities',
    'deferred_revenue_current', 'other_current_liabilities',
    'total_current_liabilities', 'long_term_debt', 'deferred_revenue_non_current',
    'deferred_tax_liabilities', 'other_non_current_liabilities',
    'total_non_current_liabilities', 'total_liabilities', 'common_stock',
    'retained_earnings', 'accumulated_other_comprehensive_income',
    'total_stockholders_equity', 'total_liabilities_and_equity'
]

CASH_FLOW_FIELDS = [
    'net_income_cash_flow', 'depreciation_and_amortization',
    'stock_based_compensation', 'change_in_working_capital',
    'change_in_accounts_receivable', 'change_in_inventory',
    'change_in_accounts_payable', 'other_operating_activities',
    'operating_cash_flow', 'capital_expenditures', 'acquisitions',
    'purchases_of_investments', 'sales_of_investments',
    'other_investing_activities', 'investing_cash_flow',
    'debt_repayment', 'debt_issuance', 'common_stock_issued',
    'common_stock_repurchased', 'dividends_paid',
    'other_financing_activities', 'financing_cash_flow',
    'net_change_in_cash', 'free_cash_flow'
]

MARKET_DATA_FIELDS = [
    'stock_price', 'market_cap', 'enterprise_value', 'shares_outstanding',
    'beta', 'dividend_yield', 'dividend_per_share', 'pe_ratio',
    'forward_pe', 'peg_ratio', 'price_to_sales', 'price_to_book',
    'ev_to_revenue', 'ev_to_ebitda'
]

HISTORICAL_DATA_FIELDS = [
    'historical_revenue', 'historical_net_income',
    'historical_operating_cash_flow', 'historical_free_cash_flow',
    'historical_eps', 'historical_dates', 'historical_stock_prices',
    'historical_dividends'
]

FINANCIAL_RATIO_FIELDS = [
    # Profitability
    'gross_margin', 'operating_margin', 'net_margin', 'return_on_assets',
    'return_on_equity', 'return_on_invested_capital', 'asset_turnover',
    # Liquidity
    'current_ratio', 'quick_ratio', 'cash_ratio', 'working_capital',
    # Leverage
    'debt_to_equity', 'debt_to_assets', 'equity_multiplier',
    'interest_coverage', 'debt_service_coverage',
    # Efficiency
    'inventory_turnover', 'days_inventory_outstanding', 'receivables_turnover',
    'days_sales_outstanding', 'payables_turnover', 'days_payables_outstanding',
    'cash_conversion_cycle'
]

GROWTH_METRICS_FIELDS = [
    'revenue_growth', 'revenue_growth_3y_avg', 'revenue_growth_5y_avg',
    'earnings_growth', 'earnings_growth_3y_avg', 'earnings_growth_5y_avg',
    'eps_growth', 'operating_cash_flow_growth', 'free_cash_flow_growth',
    'book_value_growth'
]

VALUATION_METRICS_FIELDS = [
    'price_to_earnings_growth', 'price_to_cash_flow', 'price_to_free_cash_flow',
    'ev_to_sales', 'ev_to_operating_cash_flow', 'ev_to_free_cash_flow',
    'earnings_yield', 'free_cash_flow_yield'
]

QUALITY_METRICS_FIELDS = [
    'piotroski_f_score', 'altman_z_score', 'beneish_m_score',
    'quality_of_earnings', 'accrual_ratio'
]

COMPANY_INFO_FIELDS = [
    'sector', 'industry', 'country', 'exchange', 'employees',
    'founded_year', 'description', 'website', 'ceo'
]

DIVIDEND_METRICS_FIELDS = [
    'dividend_payout_ratio', 'dividend_growth_rate', 'consecutive_dividend_years'
]

SHARE_METRICS_FIELDS = [
    'float_shares', 'insider_ownership', 'institutional_ownership',
    'short_interest', 'short_ratio'
]

DCF_VALUATION_FIELDS = [
    'wacc', 'cost_of_equity', 'cost_of_debt', 'tax_rate',
    'terminal_growth_rate', 'intrinsic_value_per_share', 'fair_value_per_share'
]

ANALYST_ESTIMATE_FIELDS = [
    'analyst_target_price', 'analyst_recommendation', 'number_of_analysts',
    'estimated_revenue_current_year', 'estimated_revenue_next_year',
    'estimated_eps_current_year', 'estimated_eps_next_year'
]

DATA_QUALITY_FIELDS = [
    'data_source', 'data_timestamp', 'reporting_period', 'reporting_period_end',
    'filing_date', 'restated', 'data_quality_score', 'completeness_score',
    'last_updated', 'notes'
]

# All optional fields
ALL_OPTIONAL_FIELDS = (
    INCOME_STATEMENT_FIELDS +
    BALANCE_SHEET_FIELDS +
    CASH_FLOW_FIELDS +
    MARKET_DATA_FIELDS +
    HISTORICAL_DATA_FIELDS +
    FINANCIAL_RATIO_FIELDS +
    GROWTH_METRICS_FIELDS +
    VALUATION_METRICS_FIELDS +
    QUALITY_METRICS_FIELDS +
    COMPANY_INFO_FIELDS +
    DIVIDEND_METRICS_FIELDS +
    SHARE_METRICS_FIELDS +
    DCF_VALUATION_FIELDS +
    ANALYST_ESTIMATE_FIELDS +
    DATA_QUALITY_FIELDS
)

# Field count for documentation
TOTAL_FIELD_COUNT = len(REQUIRED_FIELDS) + len(ALL_OPTIONAL_FIELDS)
