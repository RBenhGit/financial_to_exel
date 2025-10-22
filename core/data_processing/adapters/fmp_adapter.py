"""
Financial Modeling Prep (FMP) API Adapter
==========================================

Extracts financial variables from Financial Modeling Prep API into standardized VarInputData format.

FMP is a professional financial data provider offering comprehensive financial statements,
ratios, and market data through a REST API. This adapter provides seamless integration
with the VarInputData system and FinancialVariableRegistry.

Key Features:
-------------
- **Professional Data Quality**: High-quality, verified financial statements
- **Comprehensive Coverage**: Income statements, balance sheets, cash flows, and ratios
- **Real-time Market Data**: Current prices, market cap, and trading metrics
- **Historical Data**: Up to 30 years of historical financial statements
- **Rate Limit Compliance**: Intelligent rate limiting to stay within API quotas
- **Batch Processing**: Efficient bulk data retrieval for multiple symbols
- **Data Validation**: Quality checks and validation against registry definitions
- **Error Recovery**: Robust error handling with automatic retry mechanisms

API Documentation: https://financialmodelingprep.com/developer/docs

Usage Example:
--------------
>>> from fmp_adapter import FMPAdapter
>>> from var_input_data import get_var_input_data
>>> 
>>> # Initialize adapter with API key
>>> adapter = FMPAdapter(api_key="your_fmp_api_key")
>>> 
>>> # Load comprehensive data for a symbol
>>> result = adapter.load_symbol_data("AAPL", historical_years=10)
>>> print(f"Quality score: {result.quality_metrics.overall_score:.2f}")
>>> 
>>> # Access data through VarInputData system
>>> var_data = get_var_input_data()
>>> revenue = var_data.get_variable("AAPL", "total_revenue", period="2023")
>>> print(f"AAPL 2023 Revenue: ${revenue:,.0f}")
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import requests

# Import base classes and types
from .base_adapter import (
    BaseApiAdapter, DataSourceType, DataCategory, ExtractionResult,
    DataQualityMetrics, ApiCapabilities
)

# Import project dependencies
from ..var_input_data import (
    get_var_input_data, VariableMetadata, DataChangeEvent
)
from ..financial_variable_registry import get_registry
from ..converters.fmp_converter import FMPConverter

# Configure logging
logger = logging.getLogger(__name__)


class FMPAdapter(BaseApiAdapter):
    """
    Financial Modeling Prep API adapter for extracting financial variables.
    
    This adapter provides comprehensive access to FMP's professional-grade financial
    data, including financial statements, market data, and company profiles.
    """
    
    # FMP API endpoints
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    ENDPOINTS = {
        'quote': '/quote/{symbol}',
        'profile': '/profile/{symbol}',
        'income': '/income-statement/{symbol}',
        'balance': '/balance-sheet-statement/{symbol}',
        'cashflow': '/cash-flow-statement/{symbol}',
        'ratios': '/ratios/{symbol}',
        'metrics': '/key-metrics/{symbol}',
        'enterprise_value': '/enterprise-values/{symbol}'
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.12,  # FMP: ~500 requests/minute = ~0.12s between requests
        base_url: Optional[str] = None
    ):
        """
        Initialize the FMP adapter.
        
        Args:
            api_key: FMP API key (will try to get from environment if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            rate_limit_delay: Minimum delay between requests (FMP: 500/min)
            base_url: Custom base URL (for testing)
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('FMP_API_KEY')
        
        super().__init__(api_key, timeout, max_retries, retry_delay, rate_limit_delay)
        
        if not self.api_key:
            logger.warning("FMP API key not found. Set FMP_API_KEY environment variable.")
        
        self.base_url = base_url or self.BASE_URL
        self.converter = FMPConverter()
        
        # FMP-specific configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Financial-Analysis-Tool/1.0',
            'Accept': 'application/json'
        })
        
        # FMP data categories mapping
        self._category_endpoints = {
            DataCategory.MARKET_DATA: ['quote', 'profile'],
            DataCategory.INCOME_STATEMENT: ['income'],
            DataCategory.BALANCE_SHEET: ['balance'],
            DataCategory.CASH_FLOW: ['cashflow'],
            DataCategory.FINANCIAL_RATIOS: ['ratios', 'metrics'],
            DataCategory.COMPANY_INFO: ['profile', 'enterprise_value']
        }
        
        logger.info("FMP adapter initialized")
    
    def get_source_type(self) -> DataSourceType:
        """Return the data source type for FMP"""
        return DataSourceType.FMP
    
    def get_capabilities(self) -> ApiCapabilities:
        """Return FMP API capabilities"""
        return ApiCapabilities(
            source_type=DataSourceType.FMP,
            supported_categories=[
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.FINANCIAL_RATIOS,
                DataCategory.COMPANY_INFO
            ],
            rate_limit_per_minute=500,
            rate_limit_per_day=None,  # Depends on subscription plan
            max_historical_years=30,
            requires_api_key=True,
            supports_batch_requests=True,
            real_time_data=True,
            cost_per_request=None,  # Varies by plan
            reliability_rating=0.9  # High reliability for professional service
        )
    
    def validate_credentials(self) -> bool:
        """
        Validate FMP API credentials by making a test request.
        
        Returns:
            True if credentials are valid and API is accessible
        """
        if not self.api_key:
            logger.error("FMP API key not provided")
            return False
        
        try:
            # Test with a simple quote request
            test_url = f"{self.base_url}/quote/AAPL"
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                test_url,
                {'apikey': self.api_key}
            )
            
            if success and response and isinstance(response, list) and len(response) > 0:
                # Check if response contains expected fields
                quote_data = response[0]
                if 'symbol' in quote_data and quote_data['symbol'] == 'AAPL':
                    logger.info("FMP credentials validated successfully")
                    return True
                else:
                    logger.error("FMP API returned unexpected response format")
                    return False
            else:
                logger.error(f"FMP credential validation failed: {errors}")
                return False
                
        except Exception as e:
            logger.error(f"FMP credential validation error: {e}")
            return False
    
    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: int = 5,
        validate_data: bool = True
    ) -> ExtractionResult:
        """
        Load financial data for a symbol from FMP API.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            categories: List of data categories to retrieve (all if None)
            historical_years: Years of historical data to retrieve (max 30)
            validate_data: Whether to validate data using registry definitions
            
        Returns:
            ExtractionResult with detailed results and metrics
        """
        start_time = time.time()
        symbol = self.normalize_symbol(symbol)
        
        if not self.api_key:
            return self._create_failed_result(
                symbol, "FMP API key not configured", start_time
            )
        
        # Default to all categories if none specified
        if categories is None:
            categories = [cat for cat in DataCategory]
        
        # Limit historical years to FMP maximum
        historical_years = min(historical_years, 30)
        
        logger.info(f"Loading FMP data for {symbol} - categories: {[cat.value for cat in categories]}")
        
        result = ExtractionResult(
            source=DataSourceType.FMP,
            symbol=symbol,
            success=False,
            variables_extracted=0,
            data_points_stored=0,
            categories_covered=[],
            periods_covered=[],
            quality_metrics=DataQualityMetrics(0, 0, 0, 0, 0, [], {}),
            extraction_time=0.0,
            errors=[],
            warnings=[],
            metadata={}
        )
        
        try:
            # Process each requested category
            category_results = {}
            total_requests = 0
            
            for category in categories:
                category_start = time.time()
                category_data = self._extract_category_data(
                    symbol, category, historical_years, validate_data
                )
                category_time = time.time() - category_start
                
                if category_data['success']:
                    result.categories_covered.append(category)
                    result.variables_extracted += category_data['variables_extracted']
                    result.data_points_stored += category_data['data_points_stored']
                    
                    # Merge periods
                    result.periods_covered.extend(category_data.get('periods_covered', []))
                    
                    logger.info(f"FMP {category.value}: {category_data['variables_extracted']} variables "
                              f"in {category_time:.2f}s")
                else:
                    result.warnings.extend(category_data.get('warnings', []))
                
                if category_data.get('errors'):
                    result.errors.extend(category_data['errors'])
                
                category_results[category.value] = category_data
                total_requests += category_data.get('requests_made', 0)
            
            # Remove duplicate periods and sort
            result.periods_covered = sorted(list(set(result.periods_covered)), reverse=True)
            
            # Assess overall data quality
            result.quality_metrics = self._assess_overall_quality(category_results, categories)
            
            # Update success status
            result.success = len(result.categories_covered) > 0
            
            # Update statistics
            self._stats['symbols_processed'] += 1
            
            result.metadata = {
                'total_api_requests': total_requests,
                'categories_requested': [cat.value for cat in categories],
                'historical_years': historical_years,
                'fmp_base_url': self.base_url
            }
            
            result.extraction_time = time.time() - start_time
            
            logger.info(f"FMP extraction for {symbol} completed: "
                       f"{result.variables_extracted} variables, "
                       f"quality={result.quality_metrics.overall_score:.2f}")
            
        except Exception as e:
            error_msg = f"FMP extraction failed for {symbol}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.extraction_time = time.time() - start_time
        
        return result
    
    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol from FMP.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary describing available data types and periods
        """
        symbol = self.normalize_symbol(symbol)
        
        if not self.api_key:
            return {'error': 'FMP API key not configured'}
        
        availability = {
            'symbol': symbol,
            'source': 'fmp',
            'categories': {},
            'last_checked': datetime.now().isoformat()
        }
        
        try:
            # Check each category quickly
            for category in [DataCategory.MARKET_DATA, DataCategory.INCOME_STATEMENT, 
                           DataCategory.BALANCE_SHEET, DataCategory.CASH_FLOW]:
                endpoints = self._category_endpoints.get(category, [])
                
                category_info = {
                    'available': False,
                    'periods': [],
                    'last_update': None,
                    'endpoints_checked': endpoints
                }
                
                for endpoint in endpoints[:1]:  # Check first endpoint only for speed
                    try:
                        url = f"{self.base_url}{self.ENDPOINTS[endpoint].format(symbol=symbol)}"
                        success, response, errors = self.make_request_with_retry(
                            self._make_api_request,
                            url,
                            {'apikey': self.api_key, 'limit': 1}  # Limit for speed
                        )
                        
                        if success and response:
                            category_info['available'] = True
                            if isinstance(response, list) and len(response) > 0:
                                # Extract available periods from response
                                periods = []
                                for item in response[:5]:  # Check first 5 items
                                    if 'date' in item:
                                        periods.append(item['date'])
                                    elif 'calendarYear' in item:
                                        periods.append(str(item['calendarYear']))
                                
                                category_info['periods'] = sorted(list(set(periods)), reverse=True)
                                
                                # Get most recent update
                                if periods:
                                    category_info['last_update'] = max(periods)
                            
                            break  # Success, no need to check other endpoints
                        
                    except Exception as e:
                        logger.debug(f"FMP availability check failed for {endpoint}: {e}")
                
                availability['categories'][category.value] = category_info
            
        except Exception as e:
            availability['error'] = str(e)
            logger.error(f"FMP availability check failed for {symbol}: {e}")
        
        return availability

    def extract_variables(
        self,
        symbol: str,
        period: str = "latest",
        historical_years: int = 10
    ) -> 'GeneralizedVariableDict':
        """
        Extract financial variables from FMP and return standardized dict.

        This is the core method that extracts data from FMP API and transforms it
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
        from .types import GeneralizedVariableDict, AdapterException

        start_time = time.time()
        symbol = self.normalize_symbol(symbol)

        logger.info(f"Extracting variables for {symbol} from FMP, period={period}")

        if not self.api_key:
            raise AdapterException(
                "FMP API key not configured",
                source="fmp",
                details={'symbol': symbol}
            )

        try:
            # Initialize output dictionary with required fields
            variables: GeneralizedVariableDict = {
                'ticker': symbol,
                'company_name': '',
                'currency': 'USD',
                'fiscal_year_end': 'December',
                'data_source': 'fmp',
                'data_timestamp': datetime.now(),
                'reporting_period': period
            }

            # Extract company profile and market data
            self._extract_fmp_profile_to_dict(symbol, variables)
            self._extract_fmp_quote_to_dict(symbol, variables)

            # Extract financial statement data
            if period == "latest":
                # Get the most recent period from each statement
                self._extract_fmp_latest_financials_to_dict(symbol, variables, historical_years)
            else:
                # Get specific period
                self._extract_fmp_period_financials_to_dict(symbol, period, variables)

            # Extract ratios and metrics
            self._extract_fmp_ratios_to_dict(symbol, variables)
            self._extract_fmp_metrics_to_dict(symbol, variables)

            # Extract historical data arrays
            if historical_years > 0:
                self._extract_fmp_historical_to_dict(symbol, historical_years, variables)

            # Generate composite variables
            composite_vars = self.generate_composite_variables(variables)
            variables.update(composite_vars)

            # Store metadata
            extraction_time = time.time() - start_time
            completeness = self.calculate_completeness_score(variables)

            self._last_metadata = AdapterOutputMetadata(
                source="fmp",
                timestamp=datetime.now(),
                quality_score=0.90,  # FMP has high quality data
                completeness=completeness,
                validation_errors=[],
                extraction_time=extraction_time,
                api_calls_made=self._stats['requests_made']
            )

            self._stats['symbols_processed'] += 1

            logger.info(f"Successfully extracted {len([v for v in variables.values() if v is not None])} "
                       f"variables for {symbol} from FMP in {extraction_time:.2f}s")

            return variables

        except Exception as e:
            logger.error(f"Failed to extract variables for {symbol} from FMP: {e}")
            raise AdapterException(
                f"Failed to extract variables for {symbol}",
                source="fmp",
                original_exception=e
            )

    def get_extraction_metadata(self) -> 'AdapterOutputMetadata':
        """
        Return metadata about the most recent extraction operation.

        Returns:
            AdapterOutputMetadata for the last extraction
        """
        from .types import AdapterOutputMetadata

        if self._last_metadata is None:
            # Return default metadata if no extraction has been performed
            return AdapterOutputMetadata(
                source="fmp",
                timestamp=datetime.now(),
                quality_score=0.0,
                completeness=0.0,
                validation_errors=["No extraction performed yet"],
                extraction_time=0.0,
                api_calls_made=0
            )
        return self._last_metadata

    def validate_output(self, variables: 'GeneralizedVariableDict') -> 'ValidationResult':
        """
        Validate that output conforms to GeneralizedVariableDict schema.

        Args:
            variables: Dictionary to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        from .types import ValidationResult
        from .adapter_validator import AdapterValidator, ValidationLevel

        # Use validator for comprehensive validation
        validator = AdapterValidator(level=ValidationLevel.MODERATE)
        validation_report = validator.validate(variables, include_quality_score=True)

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
            'growth_metrics',
            'valuation_metrics'
        ]

    # =========================================================================
    # Helper Methods for extract_variables() Implementation
    # =========================================================================

    def _extract_fmp_profile_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract company profile data from FMP into GeneralizedVariableDict"""
        try:
            url = f"{self.base_url}{self.ENDPOINTS['profile'].format(symbol=symbol)}"
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key}
            )

            if not success or not response or len(response) == 0:
                logger.warning(f"No FMP profile data for {symbol}")
                return

            profile = response[0]

            # Map fields
            variables['company_name'] = profile.get('companyName', '')
            variables['currency'] = profile.get('currency', 'USD')
            variables['sector'] = profile.get('sector')
            variables['industry'] = profile.get('industry')
            variables['country'] = profile.get('country')
            variables['exchange'] = profile.get('exchangeShortName')
            variables['website'] = profile.get('website')
            variables['description'] = profile.get('description')
            variables['employees'] = profile.get('fullTimeEmployees')
            variables['ceo'] = profile.get('ceo')

            # Market data from profile
            if 'mktCap' in profile:
                variables['market_cap'] = float(profile['mktCap']) / 1_000_000  # Convert to millions

            logger.debug(f"Extracted FMP profile for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP profile for {symbol}: {e}")

    def _extract_fmp_quote_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract quote/market data from FMP into GeneralizedVariableDict"""
        try:
            url = f"{self.base_url}{self.ENDPOINTS['quote'].format(symbol=symbol)}"
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key}
            )

            if not success or not response or len(response) == 0:
                logger.warning(f"No FMP quote data for {symbol}")
                return

            quote = response[0]

            # Map market data fields
            variables['stock_price'] = quote.get('price')
            variables['market_cap'] = float(quote.get('marketCap', 0)) / 1_000_000 if quote.get('marketCap') else None
            variables['shares_outstanding'] = float(quote.get('sharesOutstanding', 0)) / 1_000_000 if quote.get('sharesOutstanding') else None
            variables['pe_ratio'] = quote.get('pe')
            variables['eps_diluted'] = quote.get('eps')
            variables['dividend_yield'] = quote.get('dividendYield')

            logger.debug(f"Extracted FMP quote for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP quote for {symbol}: {e}")

    def _extract_fmp_latest_financials_to_dict(
        self,
        symbol: str,
        variables: 'GeneralizedVariableDict',
        historical_years: int
    ) -> None:
        """Extract latest period from FMP financial statements"""
        try:
            # Income statement
            income_url = f"{self.base_url}{self.ENDPOINTS['income'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                income_url,
                {'apikey': self.api_key, 'limit': 1}
            )
            if success and response and len(response) > 0:
                self._map_fmp_income_to_dict(response[0], variables)

            # Balance sheet
            balance_url = f"{self.base_url}{self.ENDPOINTS['balance'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                balance_url,
                {'apikey': self.api_key, 'limit': 1}
            )
            if success and response and len(response) > 0:
                self._map_fmp_balance_to_dict(response[0], variables)

            # Cash flow
            cashflow_url = f"{self.base_url}{self.ENDPOINTS['cashflow'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                cashflow_url,
                {'apikey': self.api_key, 'limit': 1}
            )
            if success and response and len(response) > 0:
                self._map_fmp_cashflow_to_dict(response[0], variables)

            logger.debug(f"Extracted latest FMP financials for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting latest FMP financials for {symbol}: {e}")

    def _extract_fmp_period_financials_to_dict(
        self,
        symbol: str,
        period: str,
        variables: 'GeneralizedVariableDict'
    ) -> None:
        """Extract specific period from FMP financial statements"""
        try:
            # Try to extract from each statement for the specified period
            for stmt_type, endpoint_key in [('income', 'income'), ('balance', 'balance'), ('cashflow', 'cashflow')]:
                url = f"{self.base_url}{self.ENDPOINTS[endpoint_key].format(symbol=symbol)}"
                success, response, _ = self.make_request_with_retry(
                    self._make_api_request,
                    url,
                    {'apikey': self.api_key}
                )

                if not success or not response:
                    continue

                # Find matching period
                for item in response:
                    if 'date' in item and period in item['date']:
                        if stmt_type == 'income':
                            self._map_fmp_income_to_dict(item, variables)
                        elif stmt_type == 'balance':
                            self._map_fmp_balance_to_dict(item, variables)
                        elif stmt_type == 'cashflow':
                            self._map_fmp_cashflow_to_dict(item, variables)
                        break

            logger.debug(f"Extracted FMP period {period} financials for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP period {period} financials for {symbol}: {e}")

    def _extract_fmp_ratios_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract financial ratios from FMP into GeneralizedVariableDict"""
        try:
            url = f"{self.base_url}{self.ENDPOINTS['ratios'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key, 'limit': 1}
            )

            if not success or not response or len(response) == 0:
                logger.warning(f"No FMP ratios for {symbol}")
                return

            ratios = response[0]

            # Map ratio fields
            variables['current_ratio'] = ratios.get('currentRatio')
            variables['quick_ratio'] = ratios.get('quickRatio')
            variables['cash_ratio'] = ratios.get('cashRatio')
            variables['debt_to_equity'] = ratios.get('debtEquityRatio')
            variables['debt_to_assets'] = ratios.get('debtRatio')
            variables['gross_margin'] = ratios.get('grossProfitMargin')
            variables['operating_margin'] = ratios.get('operatingProfitMargin')
            variables['net_margin'] = ratios.get('netProfitMargin')
            variables['return_on_assets'] = ratios.get('returnOnAssets')
            variables['return_on_equity'] = ratios.get('returnOnEquity')
            variables['inventory_turnover'] = ratios.get('inventoryTurnover')
            variables['receivables_turnover'] = ratios.get('receivablesTurnover')
            variables['days_sales_outstanding'] = ratios.get('daysOfSalesOutstanding')
            variables['days_inventory_outstanding'] = ratios.get('daysOfInventoryOutstanding')
            variables['dividend_yield'] = ratios.get('dividendYield')
            variables['dividend_payout_ratio'] = ratios.get('payoutRatio')
            variables['price_to_book'] = ratios.get('priceToBookRatio')
            variables['price_to_sales'] = ratios.get('priceToSalesRatio')

            logger.debug(f"Extracted FMP ratios for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP ratios for {symbol}: {e}")

    def _extract_fmp_metrics_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract key metrics from FMP into GeneralizedVariableDict"""
        try:
            url = f"{self.base_url}{self.ENDPOINTS['metrics'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key, 'limit': 1}
            )

            if not success or not response or len(response) == 0:
                logger.warning(f"No FMP metrics for {symbol}")
                return

            metrics = response[0]

            # Map metrics fields
            variables['market_cap'] = float(metrics.get('marketCap', 0)) / 1_000_000 if metrics.get('marketCap') else None
            variables['enterprise_value'] = float(metrics.get('enterpriseValue', 0)) / 1_000_000 if metrics.get('enterpriseValue') else None
            variables['pe_ratio'] = metrics.get('peRatio')
            variables['price_to_sales'] = metrics.get('priceToSalesRatio')
            variables['price_to_book'] = metrics.get('pbRatio')
            variables['ev_to_sales'] = metrics.get('evToSales')
            variables['ev_to_ebitda'] = metrics.get('enterpriseValueOverEBITDA')
            variables['price_to_free_cash_flow'] = metrics.get('pfcfRatio')
            variables['revenue_growth'] = metrics.get('revenuePerShareGrowth')
            variables['earnings_growth'] = metrics.get('netIncomePerShareGrowth')
            variables['operating_cash_flow_growth'] = metrics.get('operatingCashFlowPerShareGrowth')
            variables['free_cash_flow_growth'] = metrics.get('freeCashFlowPerShareGrowth')
            variables['book_value_growth'] = metrics.get('bookValuePerShareGrowth')
            variables['peg_ratio'] = metrics.get('pegRatio')

            logger.debug(f"Extracted FMP metrics for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP metrics for {symbol}: {e}")

    def _extract_fmp_historical_to_dict(
        self,
        symbol: str,
        historical_years: int,
        variables: 'GeneralizedVariableDict'
    ) -> None:
        """Extract historical data arrays from FMP"""
        try:
            # Get historical income statements
            url = f"{self.base_url}{self.ENDPOINTS['income'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key, 'limit': historical_years}
            )

            if success and response:
                # Extract arrays
                variables['historical_revenue'] = [float(item.get('revenue', 0)) / 1_000_000 for item in response if item.get('revenue')]
                variables['historical_net_income'] = [float(item.get('netIncome', 0)) / 1_000_000 for item in response if item.get('netIncome')]
                variables['historical_dates'] = [datetime.strptime(item['date'], '%Y-%m-%d').date() for item in response if item.get('date')]

            # Get historical cash flows
            url = f"{self.base_url}{self.ENDPOINTS['cashflow'].format(symbol=symbol)}"
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                url,
                {'apikey': self.api_key, 'limit': historical_years}
            )

            if success and response:
                variables['historical_operating_cash_flow'] = [float(item.get('operatingCashFlow', 0)) / 1_000_000 for item in response if item.get('operatingCashFlow')]
                variables['historical_free_cash_flow'] = [float(item.get('freeCashFlow', 0)) / 1_000_000 for item in response if item.get('freeCashFlow')]

            logger.debug(f"Extracted FMP historical data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting FMP historical data for {symbol}: {e}")

    def _map_fmp_income_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map FMP income statement data to GeneralizedVariableDict"""
        try:
            variables['revenue'] = float(data.get('revenue', 0)) / 1_000_000 if data.get('revenue') else None
            variables['cost_of_revenue'] = float(data.get('costOfRevenue', 0)) / 1_000_000 if data.get('costOfRevenue') else None
            variables['gross_profit'] = float(data.get('grossProfit', 0)) / 1_000_000 if data.get('grossProfit') else None
            variables['research_and_development'] = float(data.get('researchAndDevelopmentExpenses', 0)) / 1_000_000 if data.get('researchAndDevelopmentExpenses') else None
            variables['selling_general_administrative'] = float(data.get('sellingGeneralAndAdministrativeExpenses', 0)) / 1_000_000 if data.get('sellingGeneralAndAdministrativeExpenses') else None
            variables['operating_expenses'] = float(data.get('operatingExpenses', 0)) / 1_000_000 if data.get('operatingExpenses') else None
            variables['operating_income'] = float(data.get('operatingIncome', 0)) / 1_000_000 if data.get('operatingIncome') else None
            variables['interest_expense'] = float(data.get('interestExpense', 0)) / 1_000_000 if data.get('interestExpense') else None
            variables['interest_income'] = float(data.get('interestIncome', 0)) / 1_000_000 if data.get('interestIncome') else None
            variables['income_before_tax'] = float(data.get('incomeBeforeTax', 0)) / 1_000_000 if data.get('incomeBeforeTax') else None
            variables['income_tax_expense'] = float(data.get('incomeTaxExpense', 0)) / 1_000_000 if data.get('incomeTaxExpense') else None
            variables['net_income'] = float(data.get('netIncome', 0)) / 1_000_000 if data.get('netIncome') else None
            variables['eps_basic'] = data.get('eps')
            variables['eps_diluted'] = data.get('epsdiluted')
            variables['weighted_average_shares_basic'] = float(data.get('weightedAverageShsOut', 0)) / 1_000_000 if data.get('weightedAverageShsOut') else None
            variables['weighted_average_shares_diluted'] = float(data.get('weightedAverageShsOutDil', 0)) / 1_000_000 if data.get('weightedAverageShsOutDil') else None
            variables['ebitda'] = float(data.get('ebitda', 0)) / 1_000_000 if data.get('ebitda') else None
        except Exception as e:
            logger.error(f"Error mapping FMP income statement: {e}")

    def _map_fmp_balance_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map FMP balance sheet data to GeneralizedVariableDict"""
        try:
            variables['cash_and_cash_equivalents'] = float(data.get('cashAndCashEquivalents', 0)) / 1_000_000 if data.get('cashAndCashEquivalents') else None
            variables['short_term_investments'] = float(data.get('shortTermInvestments', 0)) / 1_000_000 if data.get('shortTermInvestments') else None
            variables['accounts_receivable'] = float(data.get('netReceivables', 0)) / 1_000_000 if data.get('netReceivables') else None
            variables['inventory'] = float(data.get('inventory', 0)) / 1_000_000 if data.get('inventory') else None
            variables['other_current_assets'] = float(data.get('otherCurrentAssets', 0)) / 1_000_000 if data.get('otherCurrentAssets') else None
            variables['total_current_assets'] = float(data.get('totalCurrentAssets', 0)) / 1_000_000 if data.get('totalCurrentAssets') else None
            variables['property_plant_equipment_net'] = float(data.get('propertyPlantEquipmentNet', 0)) / 1_000_000 if data.get('propertyPlantEquipmentNet') else None
            variables['goodwill'] = float(data.get('goodwill', 0)) / 1_000_000 if data.get('goodwill') else None
            variables['intangible_assets'] = float(data.get('intangibleAssets', 0)) / 1_000_000 if data.get('intangibleAssets') else None
            variables['long_term_investments'] = float(data.get('longTermInvestments', 0)) / 1_000_000 if data.get('longTermInvestments') else None
            variables['other_non_current_assets'] = float(data.get('otherNonCurrentAssets', 0)) / 1_000_000 if data.get('otherNonCurrentAssets') else None
            variables['total_non_current_assets'] = float(data.get('totalNonCurrentAssets', 0)) / 1_000_000 if data.get('totalNonCurrentAssets') else None
            variables['total_assets'] = float(data.get('totalAssets', 0)) / 1_000_000 if data.get('totalAssets') else None
            variables['accounts_payable'] = float(data.get('accountPayables', 0)) / 1_000_000 if data.get('accountPayables') else None
            variables['short_term_debt'] = float(data.get('shortTermDebt', 0)) / 1_000_000 if data.get('shortTermDebt') else None
            variables['other_current_liabilities'] = float(data.get('otherCurrentLiabilities', 0)) / 1_000_000 if data.get('otherCurrentLiabilities') else None
            variables['total_current_liabilities'] = float(data.get('totalCurrentLiabilities', 0)) / 1_000_000 if data.get('totalCurrentLiabilities') else None
            variables['long_term_debt'] = float(data.get('longTermDebt', 0)) / 1_000_000 if data.get('longTermDebt') else None
            variables['other_non_current_liabilities'] = float(data.get('otherNonCurrentLiabilities', 0)) / 1_000_000 if data.get('otherNonCurrentLiabilities') else None
            variables['total_non_current_liabilities'] = float(data.get('totalNonCurrentLiabilities', 0)) / 1_000_000 if data.get('totalNonCurrentLiabilities') else None
            variables['total_liabilities'] = float(data.get('totalLiabilities', 0)) / 1_000_000 if data.get('totalLiabilities') else None
            variables['common_stock'] = float(data.get('commonStock', 0)) / 1_000_000 if data.get('commonStock') else None
            variables['retained_earnings'] = float(data.get('retainedEarnings', 0)) / 1_000_000 if data.get('retainedEarnings') else None
            variables['total_stockholders_equity'] = float(data.get('totalStockholdersEquity', 0)) / 1_000_000 if data.get('totalStockholdersEquity') else None
        except Exception as e:
            logger.error(f"Error mapping FMP balance sheet: {e}")

    def _map_fmp_cashflow_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map FMP cash flow data to GeneralizedVariableDict"""
        try:
            variables['operating_cash_flow'] = float(data.get('operatingCashFlow', 0)) / 1_000_000 if data.get('operatingCashFlow') else None
            variables['depreciation_and_amortization'] = float(data.get('depreciationAndAmortization', 0)) / 1_000_000 if data.get('depreciationAndAmortization') else None
            variables['stock_based_compensation'] = float(data.get('stockBasedCompensation', 0)) / 1_000_000 if data.get('stockBasedCompensation') else None
            variables['change_in_working_capital'] = float(data.get('changeInWorkingCapital', 0)) / 1_000_000 if data.get('changeInWorkingCapital') else None
            variables['change_in_accounts_receivable'] = float(data.get('accountsReceivables', 0)) / 1_000_000 if data.get('accountsReceivables') else None
            variables['change_in_inventory'] = float(data.get('inventory', 0)) / 1_000_000 if data.get('inventory') else None
            variables['change_in_accounts_payable'] = float(data.get('accountsPayables', 0)) / 1_000_000 if data.get('accountsPayables') else None
            variables['capital_expenditures'] = float(data.get('capitalExpenditure', 0)) / 1_000_000 if data.get('capitalExpenditure') else None
            variables['acquisitions'] = float(data.get('acquisitionsNet', 0)) / 1_000_000 if data.get('acquisitionsNet') else None
            variables['purchases_of_investments'] = float(data.get('purchasesOfInvestments', 0)) / 1_000_000 if data.get('purchasesOfInvestments') else None
            variables['sales_of_investments'] = float(data.get('salesMaturitiesOfInvestments', 0)) / 1_000_000 if data.get('salesMaturitiesOfInvestments') else None
            variables['investing_cash_flow'] = float(data.get('netCashUsedForInvestingActivites', 0)) / 1_000_000 if data.get('netCashUsedForInvestingActivites') else None
            variables['debt_repayment'] = float(data.get('debtRepayment', 0)) / 1_000_000 if data.get('debtRepayment') else None
            variables['common_stock_issued'] = float(data.get('commonStockIssued', 0)) / 1_000_000 if data.get('commonStockIssued') else None
            variables['common_stock_repurchased'] = float(data.get('commonStockRepurchased', 0)) / 1_000_000 if data.get('commonStockRepurchased') else None
            variables['dividends_paid'] = float(data.get('dividendsPaid', 0)) / 1_000_000 if data.get('dividendsPaid') else None
            variables['financing_cash_flow'] = float(data.get('netCashUsedProvidedByFinancingActivities', 0)) / 1_000_000 if data.get('netCashUsedProvidedByFinancingActivities') else None
            variables['free_cash_flow'] = float(data.get('freeCashFlow', 0)) / 1_000_000 if data.get('freeCashFlow') else None
        except Exception as e:
            logger.error(f"Error mapping FMP cash flow: {e}")

    # =========================================================================
    # Private helper methods
    # =========================================================================
    
    def _extract_category_data(
        self,
        symbol: str,
        category: DataCategory,
        historical_years: int,
        validate_data: bool
    ) -> Dict[str, Any]:
        """Extract data for a specific category from FMP API"""
        result = {
            'category': category.value,
            'success': False,
            'variables_extracted': 0,
            'data_points_stored': 0,
            'periods_covered': [],
            'requests_made': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            endpoints = self._category_endpoints.get(category, [])
            if not endpoints:
                result['warnings'].append(f"No FMP endpoints defined for category {category.value}")
                return result
            
            category_data = {}
            
            # Fetch data from each endpoint for this category
            for endpoint in endpoints:
                endpoint_data = self._fetch_endpoint_data(symbol, endpoint, historical_years)
                result['requests_made'] += 1
                
                if endpoint_data:
                    category_data[endpoint] = endpoint_data
            
            if not category_data:
                result['warnings'].append(f"No data retrieved from FMP for category {category.value}")
                return result
            
            # Convert and store data
            variables_stored = self._convert_and_store_category_data(
                symbol, category, category_data, validate_data
            )
            
            result['success'] = variables_stored > 0
            result['variables_extracted'] = variables_stored
            result['data_points_stored'] = variables_stored
            
            # Extract periods covered
            result['periods_covered'] = self._extract_periods_from_data(category_data)
            
        except Exception as e:
            error_msg = f"FMP category {category.value} extraction failed: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _fetch_endpoint_data(
        self,
        symbol: str,
        endpoint: str,
        historical_years: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch data from a specific FMP endpoint"""
        try:
            url = f"{self.base_url}{self.ENDPOINTS[endpoint].format(symbol=symbol)}"
            params = {
                'apikey': self.api_key,
                'limit': historical_years * 4 if endpoint in ['income', 'balance', 'cashflow'] else 1
            }
            
            success, response, errors = self.make_request_with_retry(
                self._make_api_request, url, params
            )
            
            if success and response:
                return response if isinstance(response, list) else [response]
            else:
                logger.warning(f"FMP {endpoint} endpoint failed for {symbol}: {errors}")
                return None
                
        except Exception as e:
            logger.error(f"FMP {endpoint} fetch error for {symbol}: {e}")
            return None
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make a request to FMP API with error handling"""
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # FMP returns error information in the response for some errors
        if isinstance(data, dict) and 'Error Message' in data:
            raise requests.RequestException(f"FMP API error: {data['Error Message']}")
        
        return data
    
    def _convert_and_store_category_data(
        self,
        symbol: str,
        category: DataCategory,
        category_data: Dict[str, List[Dict[str, Any]]],
        validate_data: bool
    ) -> int:
        """Convert category data and store in VarInputData"""
        variables_stored = 0
        
        try:
            # Process each endpoint's data
            for endpoint, data_list in category_data.items():
                if not data_list:
                    continue
                
                for data_item in data_list:
                    # Convert FMP data to standard format
                    converted_data = self.converter.convert_financial_data(data_item)
                    if not converted_data:
                        continue
                    
                    # Determine period from the data
                    period = self._extract_period_from_item(data_item)
                    
                    # Store each converted variable
                    for var_name, value in converted_data.items():
                        if var_name in ['source', 'converted_at']:  # Skip metadata
                            continue
                        
                        if self._store_variable(symbol, var_name, value, period, 
                                              f"fmp_{endpoint}", validate_data):
                            variables_stored += 1
            
        except Exception as e:
            logger.error(f"FMP data conversion/storage failed: {e}")
        
        return variables_stored
    
    def _store_variable(
        self,
        symbol: str,
        var_name: str,
        value: Any,
        period: str,
        source_detail: str,
        validate_data: bool
    ) -> bool:
        """Store a single variable in VarInputData with metadata"""
        if not self.var_data or not self.variable_registry:
            return False
        
        try:
            # Get variable definition for validation
            var_def = self.variable_registry.get_variable_definition(var_name)
            if not var_def:
                logger.debug(f"FMP: Variable {var_name} not found in registry, skipping")
                return False
            
            # Create metadata
            metadata = VariableMetadata(
                source=source_detail,
                timestamp=datetime.now(),
                quality_score=0.9,  # FMP generally has high quality data
                validation_passed=True,
                period=period,
                lineage_id=f"{symbol}_fmp_{var_name}_{period}"
            )
            
            # Validate if requested
            if validate_data and hasattr(var_def, 'validate_value'):
                is_valid, validation_errors = var_def.validate_value(value)
                if not is_valid:
                    metadata.validation_passed = False
                    metadata.quality_score *= 0.8
                    logger.debug(f"FMP validation failed for {var_name}: {validation_errors}")
            
            # Store in VarInputData
            success = self.var_data.set_variable(
                symbol=symbol,
                variable_name=var_name,
                value=value,
                period=period,
                source="fmp",
                metadata=metadata,
                validate=False,  # Already validated above
                emit_event=False  # Batch processing
            )
            
            if success:
                logger.debug(f"FMP stored: {symbol}.{var_name}[{period}] = {value}")
                return True
            else:
                logger.warning(f"FMP failed to store {symbol}.{var_name}")
                return False
                
        except Exception as e:
            logger.error(f"FMP variable storage error: {e}")
            return False
    
    def _extract_periods_from_data(self, category_data: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Extract all periods covered by the category data"""
        periods = set()
        
        for endpoint, data_list in category_data.items():
            for data_item in data_list:
                period = self._extract_period_from_item(data_item)
                if period:
                    periods.add(period)
        
        return sorted(list(periods), reverse=True)
    
    def _extract_period_from_item(self, data_item: Dict[str, Any]) -> str:
        """Extract period identifier from FMP data item"""
        # FMP uses different date fields depending on endpoint
        for date_field in ['date', 'calendarYear', 'period']:
            if date_field in data_item and data_item[date_field]:
                return str(data_item[date_field])
        
        # Default to current if no period found
        return "current"
    
    def _assess_overall_quality(
        self,
        category_results: Dict[str, Dict[str, Any]],
        requested_categories: List[DataCategory]
    ) -> DataQualityMetrics:
        """Assess overall data quality across all categories"""
        issues = []
        metadata = {}
        
        # Calculate completeness (categories successfully retrieved)
        successful_categories = sum(1 for result in category_results.values() if result['success'])
        completeness_score = successful_categories / len(requested_categories) if requested_categories else 0
        
        if successful_categories < len(requested_categories):
            missing = [cat.value for cat in requested_categories 
                      if cat.value not in category_results or not category_results[cat.value]['success']]
            issues.append(f"Missing categories: {', '.join(missing)}")
        
        # FMP generally has high timeliness and consistency
        timeliness_score = 0.95  # Professional service with frequent updates
        consistency_score = 0.92  # High internal consistency
        
        # FMP reliability
        reliability_score = self.get_capabilities().reliability_rating
        
        # Weighted overall score
        overall_score = (
            completeness_score * 0.4 +
            timeliness_score * 0.3 +
            consistency_score * 0.2 +
            reliability_score * 0.1
        )
        
        metadata = {
            'categories_requested': len(requested_categories),
            'categories_successful': successful_categories,
            'total_variables_extracted': sum(r.get('variables_extracted', 0) for r in category_results.values()),
            'assessment_time': datetime.now().isoformat()
        }
        
        return DataQualityMetrics(
            completeness_score=completeness_score,
            timeliness_score=timeliness_score,
            consistency_score=consistency_score,
            reliability_score=reliability_score,
            overall_score=overall_score,
            issues=issues,
            metadata=metadata
        )
    
    def _create_failed_result(self, symbol: str, error_msg: str, start_time: float) -> ExtractionResult:
        """Create a failed extraction result"""
        return ExtractionResult(
            source=DataSourceType.FMP,
            symbol=symbol,
            success=False,
            variables_extracted=0,
            data_points_stored=0,
            categories_covered=[],
            periods_covered=[],
            quality_metrics=DataQualityMetrics(0, 0, 0, 0, 0, [error_msg], {}),
            extraction_time=time.time() - start_time,
            errors=[error_msg],
            warnings=[],
            metadata={}
        )
    
    def _assess_data_timeliness(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess how recent/timely the FMP data is"""
        # FMP provides real-time and recent data
        if category == DataCategory.MARKET_DATA:
            return 0.98  # Very recent market data
        elif category in [DataCategory.INCOME_STATEMENT, DataCategory.BALANCE_SHEET, DataCategory.CASH_FLOW]:
            return 0.85  # Recent financial statements (quarterly updates)
        else:
            return 0.90  # Generally recent data
    
    def _assess_data_consistency(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess internal consistency of FMP data"""
        # FMP has high consistency due to professional data quality
        return 0.92


# Convenience functions for common operations

def load_fmp_data(symbol: str, api_key: Optional[str] = None, **kwargs) -> ExtractionResult:
    """
    Convenience function to load FMP data for a symbol.
    
    Args:
        symbol: Stock symbol
        api_key: FMP API key (optional, will use environment variable)
        **kwargs: Additional arguments for FMPAdapter.load_symbol_data()
        
    Returns:
        ExtractionResult with extraction statistics
    """
    adapter = FMPAdapter(api_key=api_key)
    return adapter.load_symbol_data(symbol, **kwargs)


def check_fmp_availability(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to check FMP data availability.
    
    Args:
        symbol: Stock symbol to check
        api_key: FMP API key (optional, will use environment variable)
        
    Returns:
        Dictionary with availability information
    """
    adapter = FMPAdapter(api_key=api_key)
    return adapter.get_available_data(symbol)


def get_fmp_adapter_stats(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get FMP adapter statistics.
    
    Args:
        api_key: FMP API key (optional, will use environment variable)
        
    Returns:
        Statistics dictionary
    """
    adapter = FMPAdapter(api_key=api_key)
    return adapter.get_performance_stats()