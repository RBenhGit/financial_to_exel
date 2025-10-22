"""
yfinance API Adapter
===================

Extracts financial variables from yfinance API into standardized GeneralizedVariableDict format.

This adapter provides a unified interface for retrieving financial data from Yahoo Finance
via the yfinance library, implementing the BaseApiAdapter interface for consistent behavior
across all data sources. It handles field mapping, data validation, quality scoring, and
historical data alignment.

Key Features:
-------------
- **BaseAdapter Compliance**: Implements BaseApiAdapter interface for consistent API
- **GeneralizedVariableDict Output**: Returns standardized dictionary format
- **Field Mapping**: Maps yfinance response fields to standard variable names using registry aliases
- **Multi-Statement Support**: Handles income statement, balance sheet, and cash flow data
- **Market Data Integration**: Extracts current market data (price, market cap, ratios)
- **Historical Alignment**: Handles missing periods and data gap management
- **Rate Limiting**: Built-in retry logic and timeout handling
- **Data Quality Assessment**: Scores data quality based on completeness and validation
- **Error Recovery**: Robust error handling with fallback mechanisms
- **Comprehensive Validation**: Uses AdapterValidator for output validation

Usage Example:
--------------
>>> from yfinance_adapter import YFinanceAdapter
>>>
>>> # Initialize adapter
>>> adapter = YFinanceAdapter()
>>>
>>> # Extract variables in standardized format
>>> variables = adapter.extract_variables("AAPL", period="latest")
>>> print(f"Revenue: ${variables.get('revenue')}M")
>>> print(f"Market Cap: ${variables.get('market_cap')}M")
>>>
>>> # Get extraction metadata
>>> metadata = adapter.get_extraction_metadata()
>>> print(f"Quality Score: {metadata.quality_score:.2%}")
>>> print(f"Completeness: {metadata.completeness:.2%}")
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import yfinance as yf
from requests.exceptions import RequestException, Timeout

# Import BaseAdapter and types
from .base_adapter import (
    BaseApiAdapter,
    DataSourceType,
    DataCategory,
    ApiCapabilities,
    ExtractionResult,
    DataQualityMetrics
)
from .types import (
    GeneralizedVariableDict,
    AdapterOutputMetadata,
    ValidationResult,
    AdapterException,
    AdapterStatus,
    REQUIRED_FIELDS
)
from .adapter_validator import AdapterValidator, ValidationLevel

# Import project dependencies
from ..var_input_data import (
    get_var_input_data,
    VarInputData,
    VariableMetadata,
    DataChangeEvent
)
from ..financial_variable_registry import (
    get_registry,
    FinancialVariableRegistry,
    VariableCategory,
    DataType,
    Units
)
from ..converters.yfinance_converter import YfinanceConverter

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class YFinanceExtractionResult:
    """Result of extracting variables from yfinance for a symbol"""
    symbol: str
    variables_extracted: int
    data_points_stored: int
    periods_covered: List[str]
    market_data_retrieved: bool
    quality_score: float
    extraction_time: float
    errors: List[str]
    source_info: Dict[str, Any]


@dataclass
class YFinanceDataQuality:
    """Data quality assessment for yfinance data"""
    completeness_score: float      # Percentage of expected fields present
    timeliness_score: float        # How recent the data is
    consistency_score: float       # Internal consistency checks
    overall_score: float           # Weighted overall quality score
    issues: List[str]              # List of quality issues found


class YFinanceAdapter(BaseApiAdapter):
    """
    yfinance API Adapter implementing BaseApiAdapter interface.

    This class provides a standardized interface for extracting financial data from
    Yahoo Finance, returning GeneralizedVariableDict output that conforms to the
    adapter specification. It integrates with VarInputData for persistence and
    FinancialVariableRegistry for validation.

    Inherits from BaseApiAdapter and implements all required abstract methods:
    - get_source_type()
    - get_capabilities()
    - validate_credentials()
    - load_symbol_data()
    - get_available_data()
    - extract_variables()
    - get_extraction_metadata()
    - validate_output()
    - get_supported_variable_categories()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,  # yfinance doesn't require API key
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize the yfinance adapter.

        Args:
            api_key: Not used for yfinance (included for BaseAdapter compatibility)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            rate_limit_delay: Delay between requests to avoid rate limiting
        """
        # Initialize base adapter
        super().__init__(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            rate_limit_delay=rate_limit_delay
        )

        # yfinance-specific initialization
        self.converter = YfinanceConverter()
        self.validator = AdapterValidator(level=ValidationLevel.MODERATE)

        # Data mapping configuration
        self._statement_methods = {
            'income': 'financials',
            'balance': 'balance_sheet',
            'cashflow': 'cashflow'
        }

        logger.info(f"YFinanceAdapter initialized with timeout={timeout}s, retries={max_retries}")

    # =========================================================================
    # BaseApiAdapter Abstract Method Implementations
    # =========================================================================

    def get_source_type(self) -> DataSourceType:
        """Return the data source type for this adapter"""
        return DataSourceType.YFINANCE

    def get_capabilities(self) -> ApiCapabilities:
        """Return the capabilities of this API adapter"""
        return ApiCapabilities(
            source_type=DataSourceType.YFINANCE,
            supported_categories=[
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.FINANCIAL_RATIOS,
                DataCategory.COMPANY_INFO
            ],
            rate_limit_per_minute=60,  # Conservative estimate
            rate_limit_per_day=2000,  # Conservative estimate
            max_historical_years=10,
            requires_api_key=False,
            supports_batch_requests=False,
            real_time_data=True,
            cost_per_request=0.0,  # Free API
            reliability_rating=0.85  # Generally reliable but can have gaps
        )

    def validate_credentials(self) -> bool:
        """
        Validate API credentials and connectivity.

        yfinance doesn't require credentials, so we just test connectivity
        by trying to fetch a well-known symbol.

        Returns:
            True if yfinance is accessible
        """
        try:
            test_ticker = yf.Ticker("AAPL")
            info = test_ticker.info
            # If we can access basic info, yfinance is working
            return info is not None and len(info) > 0
        except Exception as e:
            logger.error(f"yfinance connectivity test failed: {e}")
            return False

    def extract_variables(
        self,
        symbol: str,
        period: str = "latest",
        historical_years: int = 10
    ) -> GeneralizedVariableDict:
        """
        Extract financial variables from yfinance and return standardized dict.

        This is the core method that extracts data from yfinance and transforms it
        into the standardized GeneralizedVariableDict format.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: Period identifier ("latest", "2023", "2023-Q1", etc.)
            historical_years: Number of years of historical data to include

        Returns:
            GeneralizedVariableDict with standardized variable names and values

        Raises:
            AdapterException: On extraction or transformation failures
        """
        start_time = time.time()
        symbol = self.normalize_symbol(symbol)

        logger.info(f"Extracting variables for {symbol}, period={period}")

        try:
            # Initialize output dictionary with required fields
            variables: GeneralizedVariableDict = {
                'ticker': symbol,
                'company_name': '',
                'currency': 'USD',
                'fiscal_year_end': 'December',
                'data_source': 'yfinance',
                'data_timestamp': datetime.now(),
                'reporting_period': period
            }

            # Create yfinance ticker object
            ticker = self._create_ticker(symbol)
            if ticker is None:
                raise AdapterException(
                    f"Failed to create yfinance ticker for {symbol}",
                    source="yfinance"
                )

            # Extract market data (current/latest)
            if period == "latest" or period == "current":
                self._extract_market_data_to_dict(ticker, symbol, variables)

            # Extract financial statement data
            if period == "latest":
                # For "latest", get the most recent period from each statement
                self._extract_latest_financial_data_to_dict(ticker, symbol, variables, historical_years)
            else:
                # For specific period, extract that period's data
                self._extract_period_financial_data_to_dict(ticker, symbol, period, variables)

            # Extract historical data if requested
            if historical_years > 0:
                self._extract_historical_data_to_dict(ticker, symbol, historical_years, variables)

            # Calculate composite variables if needed
            composite_vars = self.generate_composite_variables(variables)
            variables.update(composite_vars)

            # Store metadata
            extraction_time = time.time() - start_time
            completeness = self.calculate_completeness_score(variables)

            self._last_metadata = AdapterOutputMetadata(
                source="yfinance",
                timestamp=datetime.now(),
                quality_score=0.85,  # Will be calculated properly in validation
                completeness=completeness,
                validation_errors=[],
                extraction_time=extraction_time,
                api_calls_made=self._stats['requests_made']
            )

            self._stats['symbols_processed'] += 1

            logger.info(f"Successfully extracted {len([v for v in variables.values() if v is not None])} "
                       f"variables for {symbol} in {extraction_time:.2f}s")

            return variables

        except Exception as e:
            logger.error(f"Failed to extract variables for {symbol}: {e}")
            raise AdapterException(
                f"Failed to extract variables for {symbol}",
                source="yfinance",
                original_exception=e
            )

    def get_extraction_metadata(self) -> AdapterOutputMetadata:
        """
        Return metadata about the most recent extraction operation.

        Returns:
            AdapterOutputMetadata for the last extraction
        """
        if self._last_metadata is None:
            # Return default metadata if no extraction has been performed
            return AdapterOutputMetadata(
                source="yfinance",
                timestamp=datetime.now(),
                quality_score=0.0,
                completeness=0.0,
                validation_errors=["No extraction performed yet"],
                extraction_time=0.0,
                api_calls_made=0
            )
        return self._last_metadata

    def validate_output(self, variables: GeneralizedVariableDict) -> ValidationResult:
        """
        Validate that output conforms to GeneralizedVariableDict schema.

        Args:
            variables: Dictionary to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        # Use the validator to perform comprehensive validation
        validation_report = self.validator.validate(variables, include_quality_score=True)

        # Convert ValidationReport to ValidationResult
        result = ValidationResult(
            valid=validation_report.valid,
            validation_type="comprehensive"
        )

        # Add errors and warnings
        for error in validation_report.errors:
            result.add_error(f"{error.field}: {error.message}")

        for warning in validation_report.warnings:
            result.add_warning(f"{warning.field}: {warning.message}")

        # Add details
        result.details['quality_score'] = validation_report.quality_score
        result.details['completeness_score'] = validation_report.completeness_score
        result.details['consistency_score'] = validation_report.consistency_score
        result.details['fields_validated'] = validation_report.fields_validated
        result.details['fields_passed'] = validation_report.fields_passed
        result.details['fields_failed'] = validation_report.fields_failed

        return result

    def get_supported_variable_categories(self) -> List[str]:
        """
        Return list of variable categories this adapter supports.

        Returns:
            List of supported category names
        """
        return [
            'income_statement',
            'balance_sheet',
            'cash_flow',
            'market_data',
            'financial_ratios',
            'company_info',
            'historical_data',
            'growth_metrics'
        ]

    # =========================================================================
    # Original YFinanceAdapter Methods (Legacy Compatibility)
    # =========================================================================

    def load_symbol_data(
        self,
        symbol: str,
        include_financials: bool = True,
        include_balance_sheet: bool = True,
        include_cashflow: bool = True,
        include_market_data: bool = True,
        historical_years: int = 5,
        validate_data: bool = True
    ) -> YFinanceExtractionResult:
        """
        Load all available financial data for a symbol from yfinance.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            include_financials: Whether to load income statement data
            include_balance_sheet: Whether to load balance sheet data
            include_cashflow: Whether to load cash flow data
            include_market_data: Whether to load current market data
            historical_years: Years of historical data to retrieve
            validate_data: Whether to validate data using registry definitions
            
        Returns:
            YFinanceExtractionResult with loading statistics and results
        """
        start_time = time.time()
        symbol = symbol.upper().strip()
        
        logger.info(f"Loading yfinance data for {symbol}")
        
        result = YFinanceExtractionResult(
            symbol=symbol,
            variables_extracted=0,
            data_points_stored=0,
            periods_covered=[],
            market_data_retrieved=False,
            quality_score=0.0,
            extraction_time=0.0,
            errors=[],
            source_info={}
        )
        
        try:
            # Create yfinance ticker object
            ticker = self._create_ticker(symbol)
            if ticker is None:
                result.errors.append(f"Failed to create yfinance ticker for {symbol}")
                return result
            
            # Load market data first (fastest)
            if include_market_data:
                market_result = self._extract_market_data(ticker, symbol, validate_data)
                result.variables_extracted += market_result['variables_extracted']
                result.data_points_stored += market_result['data_points_stored']
                result.market_data_retrieved = market_result['success']
                if market_result.get('errors'):
                    result.errors.extend(market_result['errors'])
                result.source_info['market_data'] = market_result
            
            # Load financial statements
            financial_results = {}
            
            if include_financials:
                financial_results['income'] = self._extract_financial_statement(
                    ticker, symbol, 'income', historical_years, validate_data
                )
            
            if include_balance_sheet:
                financial_results['balance'] = self._extract_financial_statement(
                    ticker, symbol, 'balance', historical_years, validate_data
                )
            
            if include_cashflow:
                financial_results['cashflow'] = self._extract_financial_statement(
                    ticker, symbol, 'cashflow', historical_years, validate_data
                )
            
            # Aggregate results from financial statements
            all_periods = set()
            for stmt_name, stmt_result in financial_results.items():
                if stmt_result:
                    result.variables_extracted += stmt_result['variables_extracted']
                    result.data_points_stored += stmt_result['data_points_stored']
                    all_periods.update(stmt_result.get('periods_covered', []))
                    if stmt_result.get('errors'):
                        result.errors.extend(stmt_result['errors'])
                    result.source_info[stmt_name] = stmt_result
            
            result.periods_covered = sorted(list(all_periods), reverse=True)
            
            # Calculate overall data quality
            quality_assessment = self._assess_data_quality(financial_results, result.market_data_retrieved)
            result.quality_score = quality_assessment.overall_score
            if quality_assessment.issues:
                result.errors.extend(quality_assessment.issues)
            
            # Update global statistics
            self._stats['symbols_processed'] += 1
            self._stats['variables_extracted'] += result.variables_extracted
            self._stats['data_points_stored'] += result.data_points_stored
            
            result.extraction_time = time.time() - start_time
            
            logger.info(f"Completed yfinance data load for {symbol}: "
                       f"{result.variables_extracted} variables, "
                       f"{result.data_points_stored} data points, "
                       f"quality={result.quality_score:.2f}")
            
        except Exception as e:
            error_msg = f"Failed to load yfinance data for {symbol}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.extraction_time = time.time() - start_time
        
        return result
    
    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol without loading it all.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary describing available data types and periods
        """
        symbol = symbol.upper().strip()
        
        try:
            ticker = self._create_ticker(symbol)
            if ticker is None:
                return {'error': f'Failed to create ticker for {symbol}'}
            
            availability = {
                'symbol': symbol,
                'market_data_available': False,
                'statements_available': {},
                'info_fields': [],
                'last_checked': datetime.now().isoformat()
            }
            
            # Check market data availability
            try:
                info = ticker.info
                if info and len(info) > 5:  # Basic threshold for valid info
                    availability['market_data_available'] = True
                    availability['info_fields'] = list(info.keys())
            except Exception as e:
                logger.debug(f"Market data not available for {symbol}: {e}")
            
            # Check financial statements availability
            for stmt_name, method_name in self._statement_methods.items():
                try:
                    time.sleep(self.rate_limit_delay)  # Rate limiting
                    data = self._safe_api_call(ticker, method_name)
                    if data is not None and not data.empty:
                        availability['statements_available'][stmt_name] = {
                            'periods': list(data.columns),
                            'fields': list(data.index)
                        }
                    else:
                        availability['statements_available'][stmt_name] = None
                except Exception as e:
                    logger.debug(f"{stmt_name} data not available for {symbol}: {e}")
                    availability['statements_available'][stmt_name] = None
            
            return availability
            
        except Exception as e:
            logger.error(f"Error checking data availability for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_adapter_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the adapter's operations"""
        var_data_stats = self.var_data.get_statistics()
        
        return {
            'adapter_stats': dict(self._stats),
            'var_data_stats': var_data_stats,
            'registry_info': {
                'total_variables': len(self.variable_registry.list_all_variables()),
                'categories': [cat.value for cat in VariableCategory]
            },
            'performance_metrics': {
                'avg_api_calls_per_symbol': (
                    self._stats['api_calls_made'] / max(1, self._stats['symbols_processed'])
                ),
                'success_rate': (
                    1 - (self._stats['api_failures'] / max(1, self._stats['api_calls_made']))
                ),
                'retry_rate': (
                    self._stats['retry_attempts'] / max(1, self._stats['api_calls_made'])
                )
            }
        }
    
    # =========================================================================
    # Helper Methods for extract_variables() Implementation
    # =========================================================================

    def _extract_market_data_to_dict(
        self,
        ticker: yf.Ticker,
        symbol: str,
        variables: GeneralizedVariableDict
    ) -> None:
        """Extract market data from yfinance ticker.info into GeneralizedVariableDict"""
        try:
            info = self._safe_api_call(ticker, 'info')
            if not info:
                logger.warning(f"No market data available for {symbol}")
                return

            # Map standard fields from yfinance info
            field_mapping = {
                # Company info
                'longName': 'company_name',
                'shortName': 'company_name',
                'currency': 'currency',
                'sector': 'sector',
                'industry': 'industry',
                'country': 'country',
                'exchange': 'exchange',
                'website': 'website',
                'longBusinessSummary': 'description',
                'fullTimeEmployees': 'employees',

                # Market data
                'currentPrice': 'stock_price',
                'regularMarketPrice': 'stock_price',
                'marketCap': 'market_cap',
                'enterpriseValue': 'enterprise_value',
                'sharesOutstanding': 'shares_outstanding',
                'beta': 'beta',
                'dividendYield': 'dividend_yield',
                'trailingAnnualDividendRate': 'dividend_per_share',

                # Valuation ratios
                'trailingPE': 'pe_ratio',
                'forwardPE': 'forward_pe',
                'pegRatio': 'peg_ratio',
                'priceToBook': 'price_to_book',
                'priceToSalesTrailing12Months': 'price_to_sales',
                'enterpriseToRevenue': 'ev_to_revenue',
                'enterpriseToEbitda': 'ev_to_ebitda',

                # Financial ratios
                'profitMargins': 'net_margin',
                'grossMargins': 'gross_margin',
                'operatingMargins': 'operating_margin',
                'returnOnAssets': 'return_on_assets',
                'returnOnEquity': 'return_on_equity',
                'currentRatio': 'current_ratio',
                'quickRatio': 'quick_ratio',
                'debtToEquity': 'debt_to_equity',

                # Growth metrics
                'revenueGrowth': 'revenue_growth',
                'earningsGrowth': 'earnings_growth',
            }

            # Extract and map fields
            for yf_field, std_field in field_mapping.items():
                if yf_field in info and info[yf_field] is not None:
                    value = info[yf_field]

                    # Normalize based on type
                    if std_field in ['market_cap', 'enterprise_value']:
                        # Convert to millions
                        variables[std_field] = float(value) / 1_000_000 if value else None
                    elif std_field == 'shares_outstanding':
                        # Convert to millions
                        variables[std_field] = float(value) / 1_000_000 if value else None
                    elif std_field in ['employees']:
                        variables[std_field] = int(value) if value else None
                    elif std_field in ['company_name', 'sector', 'industry', 'country', 'exchange', 'website', 'description']:
                        variables[std_field] = str(value) if value else None
                    else:
                        variables[std_field] = float(value) if value else None

            logger.debug(f"Extracted market data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting market data for {symbol}: {e}")

    def _extract_latest_financial_data_to_dict(
        self,
        ticker: yf.Ticker,
        symbol: str,
        variables: GeneralizedVariableDict,
        historical_years: int
    ) -> None:
        """Extract the most recent period from each financial statement"""
        try:
            # Extract from income statement
            financials = self._safe_api_call(ticker, 'financials')
            if financials is not None and not financials.empty:
                latest_period = financials.columns[0]
                self._map_statement_to_dict(financials, latest_period, variables, 'income')

            # Extract from balance sheet
            balance_sheet = self._safe_api_call(ticker, 'balance_sheet')
            if balance_sheet is not None and not balance_sheet.empty:
                latest_period = balance_sheet.columns[0]
                self._map_statement_to_dict(balance_sheet, latest_period, variables, 'balance')

            # Extract from cash flow
            cashflow = self._safe_api_call(ticker, 'cashflow')
            if cashflow is not None and not cashflow.empty:
                latest_period = cashflow.columns[0]
                self._map_statement_to_dict(cashflow, latest_period, variables, 'cashflow')

            logger.debug(f"Extracted latest financial data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting latest financial data for {symbol}: {e}")

    def _extract_period_financial_data_to_dict(
        self,
        ticker: yf.Ticker,
        symbol: str,
        period: str,
        variables: GeneralizedVariableDict
    ) -> None:
        """Extract specific period data from financial statements"""
        try:
            # Try to match period in each statement
            for stmt_type, method in self._statement_methods.items():
                data = self._safe_api_call(ticker, method)
                if data is None or data.empty:
                    continue

                # Find matching period
                for col in data.columns:
                    if str(col).startswith(period) or period in str(col):
                        self._map_statement_to_dict(data, col, variables, stmt_type)
                        break

            logger.debug(f"Extracted period {period} financial data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting period {period} data for {symbol}: {e}")

    def _extract_historical_data_to_dict(
        self,
        ticker: yf.Ticker,
        symbol: str,
        historical_years: int,
        variables: GeneralizedVariableDict
    ) -> None:
        """Extract historical data arrays"""
        try:
            # Get historical financials
            financials = self._safe_api_call(ticker, 'financials')
            if financials is not None and not financials.empty:
                # Extract revenue history
                if 'Total Revenue' in financials.index:
                    revenue_series = financials.loc['Total Revenue']
                    variables['historical_revenue'] = [float(v) / 1_000_000 for v in revenue_series.values if pd.notna(v)]
                    variables['historical_dates'] = [col.date() for col in financials.columns]

                # Extract net income history
                if 'Net Income' in financials.index:
                    ni_series = financials.loc['Net Income']
                    variables['historical_net_income'] = [float(v) / 1_000_000 for v in ni_series.values if pd.notna(v)]

            # Get historical cash flow
            cashflow = self._safe_api_call(ticker, 'cashflow')
            if cashflow is not None and not cashflow.empty:
                # Extract operating cash flow history
                if 'Operating Cash Flow' in cashflow.index:
                    ocf_series = cashflow.loc['Operating Cash Flow']
                    variables['historical_operating_cash_flow'] = [float(v) / 1_000_000 for v in ocf_series.values if pd.notna(v)]

                # Extract free cash flow history
                if 'Free Cash Flow' in cashflow.index:
                    fcf_series = cashflow.loc['Free Cash Flow']
                    variables['historical_free_cash_flow'] = [float(v) / 1_000_000 for v in fcf_series.values if pd.notna(v)]

            logger.debug(f"Extracted historical data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting historical data for {symbol}: {e}")

    def _map_statement_to_dict(
        self,
        data: pd.DataFrame,
        period: Any,
        variables: GeneralizedVariableDict,
        statement_type: str
    ) -> None:
        """Map financial statement data to GeneralizedVariableDict"""
        # Define field mappings for each statement type
        income_mapping = {
            'Total Revenue': 'revenue',
            'Cost Of Revenue': 'cost_of_revenue',
            'Gross Profit': 'gross_profit',
            'Operating Expense': 'operating_expenses',
            'Research And Development': 'research_and_development',
            'Selling General And Administrative': 'selling_general_administrative',
            'Operating Income': 'operating_income',
            'Interest Expense': 'interest_expense',
            'Other Income Expense': 'other_income_expense',
            'Income Before Tax': 'income_before_tax',
            'Tax Provision': 'income_tax_expense',
            'Net Income': 'net_income',
            'Basic EPS': 'eps_basic',
            'Diluted EPS': 'eps_diluted',
            'EBITDA': 'ebitda',
            'EBIT': 'ebit'
        }

        balance_mapping = {
            'Cash And Cash Equivalents': 'cash_and_cash_equivalents',
            'Short Term Investments': 'short_term_investments',
            'Accounts Receivable': 'accounts_receivable',
            'Inventory': 'inventory',
            'Other Current Assets': 'other_current_assets',
            'Current Assets': 'total_current_assets',
            'Net PPE': 'property_plant_equipment_net',
            'Goodwill': 'goodwill',
            'Intangible Assets': 'intangible_assets',
            'Long Term Investments': 'long_term_investments',
            'Other Non Current Assets': 'other_non_current_assets',
            'Total Non Current Assets': 'total_non_current_assets',
            'Total Assets': 'total_assets',
            'Accounts Payable': 'accounts_payable',
            'Short Term Debt': 'short_term_debt',
            'Current Debt': 'current_portion_long_term_debt',
            'Other Current Liabilities': 'other_current_liabilities',
            'Current Liabilities': 'total_current_liabilities',
            'Long Term Debt': 'long_term_debt',
            'Other Non Current Liabilities': 'other_non_current_liabilities',
            'Total Non Current Liabilities': 'total_non_current_liabilities',
            'Total Liabilities': 'total_liabilities',
            'Common Stock': 'common_stock',
            'Retained Earnings': 'retained_earnings',
            'Stockholders Equity': 'total_stockholders_equity',
            'Total Equity Gross Minority Interest': 'total_stockholders_equity'
        }

        cashflow_mapping = {
            'Operating Cash Flow': 'operating_cash_flow',
            'Depreciation And Amortization': 'depreciation_and_amortization',
            'Stock Based Compensation': 'stock_based_compensation',
            'Change In Working Capital': 'change_in_working_capital',
            'Change In Receivables': 'change_in_accounts_receivable',
            'Change In Inventory': 'change_in_inventory',
            'Change In Payables': 'change_in_accounts_payable',
            'Capital Expenditure': 'capital_expenditures',
            'Investing Cash Flow': 'investing_cash_flow',
            'Repayment Of Debt': 'debt_repayment',
            'Issuance Of Debt': 'debt_issuance',
            'Repurchase Of Capital Stock': 'common_stock_repurchased',
            'Common Stock Issuance': 'common_stock_issued',
            'Common Stock Dividend Paid': 'dividends_paid',
            'Financing Cash Flow': 'financing_cash_flow',
            'Free Cash Flow': 'free_cash_flow'
        }

        # Select appropriate mapping
        if statement_type == 'income':
            field_map = income_mapping
        elif statement_type == 'balance':
            field_map = balance_mapping
        elif statement_type == 'cashflow':
            field_map = cashflow_mapping
        else:
            return

        # Map fields
        for yf_field, std_field in field_map.items():
            if yf_field in data.index:
                value = data.loc[yf_field, period]
                if pd.notna(value):
                    # Convert to millions (yfinance returns actual values)
                    variables[std_field] = float(value) / 1_000_000

    # =========================================================================
    # Private helper methods
    # =========================================================================

    def _create_ticker(self, symbol: str) -> Optional[yf.Ticker]:
        """Create yfinance ticker object with error handling"""
        try:
            ticker = yf.Ticker(symbol)
            # Test that ticker is valid by checking if info is accessible
            _ = ticker.info.get('symbol')  # Light test
            return ticker
        except Exception as e:
            logger.error(f"Failed to create yfinance ticker for {symbol}: {e}")
            return None
    
    def _extract_market_data(
        self,
        ticker: yf.Ticker,
        symbol: str,
        validate: bool
    ) -> Dict[str, Any]:
        """Extract market data from yfinance ticker.info"""
        result = {
            'success': False,
            'variables_extracted': 0,
            'data_points_stored': 0,
            'errors': []
        }
        
        try:
            info = self._safe_api_call(ticker, 'info')
            if not info:
                result['errors'].append("No market data available from yfinance info")
                return result
            
            # Convert using the converter
            converted_data = self.converter.convert_info_data(info)
            if not converted_data:
                result['errors'].append("Failed to convert market data")
                return result
            
            # Store each variable in VarInputData
            variables_stored = 0
            for var_name, value in converted_data.items():
                if var_name in ['source', 'converted_at']:  # Skip metadata
                    continue
                
                # Get variable definition for validation
                var_def = self.variable_registry.get_variable_definition(var_name)
                if not var_def:
                    logger.debug(f"Variable {var_name} not found in registry, skipping")
                    continue
                
                # Create metadata
                metadata = VariableMetadata(
                    source="yfinance_market",
                    timestamp=datetime.now(),
                    quality_score=self._calculate_market_data_quality(info, var_name),
                    validation_passed=True,
                    period="current",
                    lineage_id=f"{symbol}_yfinance_market_{var_name}"
                )
                
                # Validate if requested
                if validate and hasattr(var_def, 'validate_value'):
                    is_valid, errors = var_def.validate_value(value)
                    if not is_valid:
                        metadata.validation_passed = False
                        metadata.quality_score *= 0.8
                        logger.debug(f"Validation failed for {var_name}: {errors}")
                
                # Store in VarInputData
                success = self.var_data.set_variable(
                    symbol=symbol,
                    variable_name=var_name,
                    value=value,
                    period="current",
                    source="yfinance",
                    metadata=metadata,
                    validate=False,  # Already validated above
                    emit_event=True
                )
                
                if success:
                    variables_stored += 1
                    logger.debug(f"Stored market data {symbol}.{var_name} = {value}")
                else:
                    result['errors'].append(f"Failed to store {var_name}")
            
            result['success'] = variables_stored > 0
            result['variables_extracted'] = variables_stored
            result['data_points_stored'] = variables_stored
            
            logger.debug(f"Extracted {variables_stored} market data variables for {symbol}")
            
        except Exception as e:
            error_msg = f"Error extracting market data for {symbol}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _extract_financial_statement(
        self,
        ticker: yf.Ticker,
        symbol: str,
        statement_type: str,
        historical_years: int,
        validate: bool
    ) -> Optional[Dict[str, Any]]:
        """Extract financial statement data from yfinance"""
        method_name = self._statement_methods.get(statement_type)
        if not method_name:
            logger.error(f"Unknown statement type: {statement_type}")
            return None
        
        result = {
            'statement_type': statement_type,
            'variables_extracted': 0,
            'data_points_stored': 0,
            'periods_covered': [],
            'errors': []
        }
        
        try:
            # Get statement data with retry logic
            data = self._safe_api_call(ticker, method_name)
            if data is None or data.empty:
                result['errors'].append(f"No {statement_type} data available")
                return result
            
            # Limit to requested historical years
            if len(data.columns) > historical_years:
                data = data.iloc[:, :historical_years]
            
            # Convert using the converter
            converted_data = self.converter.convert_financial_data(data)
            if not converted_data:
                result['errors'].append(f"Failed to convert {statement_type} data")
                return result
            
            # Get relevant variables for this statement type
            relevant_variables = self._get_relevant_variables_for_statement(statement_type)
            
            # Process each period (column) in the data
            periods = list(data.columns)
            result['periods_covered'] = [str(p) for p in periods]
            
            for period_idx, period in enumerate(periods):
                period_str = str(period)
                
                # Process each variable for this period
                for var_name in relevant_variables:
                    var_def = self.variable_registry.get_variable_definition(var_name)
                    if not var_def:
                        continue
                    
                    # Check if variable has data for this period
                    value = self._extract_variable_from_dataframe(data, var_def, period)
                    if value is None:
                        continue
                    
                    # Create metadata
                    metadata = VariableMetadata(
                        source=f"yfinance_{statement_type}",
                        timestamp=datetime.now(),
                        quality_score=self._calculate_statement_quality(data, var_name, period_str),
                        validation_passed=True,
                        period=period_str,
                        lineage_id=f"{symbol}_yfinance_{statement_type}_{var_name}_{period_str}"
                    )
                    
                    # Validate if requested
                    if validate and hasattr(var_def, 'validate_value'):
                        is_valid, errors = var_def.validate_value(value)
                        if not is_valid:
                            metadata.validation_passed = False
                            metadata.quality_score *= 0.7
                            logger.debug(f"Validation failed for {var_name}[{period_str}]: {errors}")
                    
                    # Store in VarInputData
                    success = self.var_data.set_variable(
                        symbol=symbol,
                        variable_name=var_name,
                        value=value,
                        period=period_str,
                        source="yfinance",
                        metadata=metadata,
                        validate=False,
                        emit_event=False  # Batch update, emit at end
                    )
                    
                    if success:
                        result['variables_extracted'] += 1
                        result['data_points_stored'] += 1
                        logger.debug(f"Stored {symbol}.{var_name}[{period_str}] = {value}")
            
            logger.info(f"Extracted {result['variables_extracted']} variables from {statement_type} "
                       f"for {symbol} across {len(periods)} periods")
            
        except Exception as e:
            error_msg = f"Error extracting {statement_type} data for {symbol}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _get_relevant_variables_for_statement(self, statement_type: str) -> List[str]:
        """Get variables relevant for a specific statement type from registry"""
        category_mapping = {
            'income': [VariableCategory.INCOME_STATEMENT],
            'balance': [VariableCategory.BALANCE_SHEET],
            'cashflow': [VariableCategory.CASH_FLOW]
        }
        
        relevant_categories = category_mapping.get(statement_type, [])
        all_variables = self.variable_registry.list_all_variables()
        
        relevant_variables = []
        for var_name in all_variables:
            var_def = self.variable_registry.get_variable_definition(var_name)
            if var_def and var_def.category in relevant_categories:
                relevant_variables.append(var_name)
        
        return relevant_variables
    
    def _extract_variable_from_dataframe(
        self,
        data: pd.DataFrame,
        var_def: Any,
        period: Any
    ) -> Optional[float]:
        """Extract a specific variable from yfinance DataFrame using registry aliases"""
        # Try direct field mapping from converter
        yf_field = self.converter.get_yfinance_field_for_standard(var_def.name)
        if yf_field and yf_field in data.index:
            value = data.loc[yf_field, period]
            return self._normalize_numeric_value(value)
        
        # Try aliases from variable definition
        if hasattr(var_def, 'aliases') and var_def.aliases:
            if 'yfinance' in var_def.aliases:
                yf_aliases = var_def.aliases['yfinance']
                if isinstance(yf_aliases, str):
                    yf_aliases = [yf_aliases]
                
                for alias in yf_aliases:
                    if alias in data.index:
                        value = data.loc[alias, period]
                        return self._normalize_numeric_value(value)
        
        # Try fuzzy matching with common variations
        for index_name in data.index:
            if self._is_field_match(str(index_name), var_def.name):
                value = data.loc[index_name, period]
                return self._normalize_numeric_value(value)
        
        return None
    
    def _is_field_match(self, yf_field: str, var_name: str) -> bool:
        """Check if yfinance field name matches variable name with fuzzy matching"""
        yf_normalized = yf_field.lower().replace(' ', '_').replace('-', '_')
        var_normalized = var_name.lower().replace('_', ' ')
        
        # Direct match
        if yf_normalized == var_name.lower():
            return True
        
        # Word matching (at least 2 common words)
        yf_words = set(yf_normalized.replace('_', ' ').split())
        var_words = set(var_normalized.split())
        common_words = yf_words & var_words
        
        return len(common_words) >= min(2, max(1, len(var_words) * 0.6))
    
    def _normalize_numeric_value(self, value: Any) -> Optional[float]:
        """Normalize value to float with pandas NaN handling"""
        if value is None or pd.isna(value):
            return None
        
        try:
            numeric_value = float(value)
            if abs(numeric_value) > 1e15:  # Sanity check
                return None
            return numeric_value
        except (ValueError, TypeError):
            return None
    
    def _safe_api_call(self, ticker: yf.Ticker, method: str) -> Any:
        """Make yfinance API call with retry logic and error handling"""
        for attempt in range(self.max_retries + 1):
            try:
                self._stats['api_calls_made'] += 1
                
                if method == 'info':
                    result = ticker.info
                elif method == 'financials':
                    result = ticker.financials
                elif method == 'balance_sheet':
                    result = ticker.balance_sheet
                elif method == 'cashflow':
                    result = ticker.cashflow
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                return result
                
            except (RequestException, Timeout) as e:
                self._stats['retry_attempts'] += 1
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"yfinance API call failed (attempt {attempt + 1}), "
                                 f"retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"yfinance API call failed after {self.max_retries + 1} attempts: {e}")
                    self._stats['api_failures'] += 1
                    return None
            except Exception as e:
                logger.error(f"Unexpected error in yfinance API call: {e}")
                self._stats['api_failures'] += 1
                return None
        
        return None
    
    def _calculate_market_data_quality(self, info: Dict[str, Any], var_name: str) -> float:
        """Calculate quality score for market data variable"""
        base_score = 0.9  # yfinance market data is generally reliable
        
        # Check if value exists and is reasonable
        if var_name not in info or info[var_name] is None:
            return 0.0
        
        # Adjust for data age (if lastUpdate field exists)
        if 'lastUpdate' in info:
            try:
                last_update = datetime.fromtimestamp(info['lastUpdate'])
                age_days = (datetime.now() - last_update).days
                if age_days > 7:  # Data older than a week
                    base_score *= max(0.5, 1 - (age_days / 365))
            except (ValueError, TypeError, KeyError):
                pass
        
        return min(1.0, base_score)
    
    def _calculate_statement_quality(self, data: pd.DataFrame, var_name: str, period: str) -> float:
        """Calculate quality score for financial statement variable"""
        base_score = 0.8  # yfinance historical data is generally good but not perfect
        
        # Check data completeness for this variable across periods
        if var_name not in data.index:
            return 0.0
        
        var_row = data.loc[var_name]
        non_null_count = var_row.count()
        total_periods = len(var_row)
        
        if total_periods > 0:
            completeness = non_null_count / total_periods
            base_score = base_score * (0.5 + 0.5 * completeness)
        
        # Adjust for period age
        try:
            if isinstance(period, str) and len(period) == 4 and period.isdigit():
                period_year = int(period)
                current_year = datetime.now().year
                age_years = current_year - period_year
                if age_years > 1:  # Older data is less reliable
                    base_score *= max(0.7, 1 - (age_years * 0.05))
        except (ValueError, TypeError):
            pass
        
        return min(1.0, base_score)
    
    def _assess_data_quality(
        self,
        financial_results: Dict[str, Any],
        market_data_success: bool
    ) -> YFinanceDataQuality:
        """Assess overall data quality for the extraction"""
        completeness_scores = []
        timeliness_scores = []
        consistency_issues = []
        
        # Assess completeness
        total_expected_statements = 3  # income, balance, cashflow
        successful_statements = sum(1 for result in financial_results.values() if result and result['variables_extracted'] > 0)
        completeness_scores.append(successful_statements / total_expected_statements)
        
        if market_data_success:
            completeness_scores.append(1.0)
        else:
            completeness_scores.append(0.0)
        
        # Assess timeliness (check if we have recent data)
        has_current_period = any(
            result and result.get('periods_covered') and 
            any(self._is_recent_period(p) for p in result['periods_covered'])
            for result in financial_results.values()
        )
        timeliness_scores.append(1.0 if has_current_period else 0.6)
        
        # Check for consistency issues
        period_counts = []
        for result in financial_results.values():
            if result and result.get('periods_covered'):
                period_counts.append(len(result['periods_covered']))
        
        if period_counts and max(period_counts) - min(period_counts) > 2:
            consistency_issues.append("Inconsistent period coverage across statements")
        
        # Calculate overall scores
        completeness_score = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
        timeliness_score = sum(timeliness_scores) / len(timeliness_scores) if timeliness_scores else 0.0
        consistency_score = 1.0 if not consistency_issues else 0.8
        
        # Weighted overall score
        overall_score = (
            completeness_score * 0.5 +
            timeliness_score * 0.3 +
            consistency_score * 0.2
        )
        
        return YFinanceDataQuality(
            completeness_score=completeness_score,
            timeliness_score=timeliness_score,
            consistency_score=consistency_score,
            overall_score=overall_score,
            issues=consistency_issues
        )
    
    def _is_recent_period(self, period: str) -> bool:
        """Check if a period string represents recent data (within 2 years)"""
        try:
            current_year = datetime.now().year
            if period.isdigit() and len(period) == 4:
                return current_year - int(period) <= 2
            # Add more period format checks as needed
            return False
        except (ValueError, TypeError):
            return False


# Convenience functions for common operations

def load_yfinance_data(
    symbol: str,
    **kwargs
) -> YFinanceExtractionResult:
    """
    Convenience function to load yfinance data for a symbol.
    
    Args:
        symbol: Stock symbol
        **kwargs: Additional arguments for YFinanceAdapter.load_symbol_data()
        
    Returns:
        YFinanceExtractionResult with extraction statistics
    """
    adapter = YFinanceAdapter()
    return adapter.load_symbol_data(symbol, **kwargs)


def check_yfinance_availability(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to check yfinance data availability.
    
    Args:
        symbol: Stock symbol to check
        
    Returns:
        Dictionary with availability information
    """
    adapter = YFinanceAdapter()
    return adapter.get_available_data(symbol)


def get_yfinance_adapter_stats() -> Dict[str, Any]:
    """
    Convenience function to get yfinance adapter statistics.
    
    Returns:
        Statistics dictionary
    """
    adapter = YFinanceAdapter()
    return adapter.get_adapter_statistics()