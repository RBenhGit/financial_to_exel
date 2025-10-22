"""
Alpha Vantage API Adapter
=========================

Extracts financial variables from Alpha Vantage API into standardized VarInputData format.

Alpha Vantage is a leading provider of free and premium financial market data, offering
real-time and historical stock market data through a comprehensive REST API. This adapter
provides seamless integration with the VarInputData system and FinancialVariableRegistry.

Key Features:
-------------
- **Comprehensive Market Data**: Real-time quotes, historical prices, and technical indicators
- **Fundamental Data**: Financial statements, company overviews, and earnings reports
- **Global Coverage**: Support for international markets and currencies
- **Free Tier Available**: Generous free tier with rate limits
- **Reliable Service**: Long-established API with high uptime
- **Rate Limit Compliance**: Intelligent rate limiting to stay within API quotas
- **Data Validation**: Quality checks and validation against registry definitions
- **Error Recovery**: Robust error handling with automatic retry mechanisms

API Documentation: https://www.alphavantage.co/documentation/

Usage Example:
--------------
>>> from alpha_vantage_adapter import AlphaVantageAdapter
>>> from var_input_data import get_var_input_data
>>> 
>>> # Initialize adapter with API key
>>> adapter = AlphaVantageAdapter(api_key="your_alpha_vantage_key")
>>> 
>>> # Load comprehensive data for a symbol
>>> result = adapter.load_symbol_data("AAPL", historical_years=5)
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
from ..converters.alpha_vantage_converter import AlphaVantageConverter

# Configure logging
logger = logging.getLogger(__name__)


class AlphaVantageAdapter(BaseApiAdapter):
    """
    Alpha Vantage API adapter for extracting financial variables.
    
    This adapter provides comprehensive access to Alpha Vantage's financial data,
    including market quotes, financial statements, and company information.
    """
    
    # Alpha Vantage API base URL and functions
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Alpha Vantage function mappings
    API_FUNCTIONS = {
        'quote': 'GLOBAL_QUOTE',
        'overview': 'OVERVIEW',
        'income': 'INCOME_STATEMENT',
        'balance': 'BALANCE_SHEET',
        'cashflow': 'CASH_FLOW',
        'earnings': 'EARNINGS'
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.5,
        rate_limit_delay: float = 12.0,  # Alpha Vantage free: 5 calls/minute = 12s between calls
        base_url: Optional[str] = None
    ):
        """
        Initialize the Alpha Vantage adapter.
        
        Args:
            api_key: Alpha Vantage API key (will try to get from environment if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            rate_limit_delay: Minimum delay between requests (free tier: 5/min)
            base_url: Custom base URL (for testing)
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        super().__init__(api_key, timeout, max_retries, retry_delay, rate_limit_delay)
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
        
        self.base_url = base_url or self.BASE_URL
        self.converter = AlphaVantageConverter()
        
        # Alpha Vantage-specific configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Financial-Analysis-Tool/1.0',
            'Accept': 'application/json'
        })
        
        # Alpha Vantage data categories mapping
        self._category_functions = {
            DataCategory.MARKET_DATA: ['quote'],
            DataCategory.INCOME_STATEMENT: ['income'],
            DataCategory.BALANCE_SHEET: ['balance'],
            DataCategory.CASH_FLOW: ['cashflow'],
            DataCategory.COMPANY_INFO: ['overview', 'earnings']
        }
        
        logger.info("Alpha Vantage adapter initialized")
    
    def get_source_type(self) -> DataSourceType:
        """Return the data source type for Alpha Vantage"""
        return DataSourceType.ALPHA_VANTAGE
    
    def get_capabilities(self) -> ApiCapabilities:
        """Return Alpha Vantage API capabilities"""
        return ApiCapabilities(
            source_type=DataSourceType.ALPHA_VANTAGE,
            supported_categories=[
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.COMPANY_INFO
            ],
            rate_limit_per_minute=5,        # Free tier: 5 calls/minute
            rate_limit_per_day=500,         # Free tier: 500 calls/day
            max_historical_years=20,
            requires_api_key=True,
            supports_batch_requests=False,  # One symbol at a time
            real_time_data=True,
            cost_per_request=0.0,           # Free tier available
            reliability_rating=0.85         # Good reliability, established service
        )
    
    def validate_credentials(self) -> bool:
        """
        Validate Alpha Vantage API credentials by making a test request.
        
        Returns:
            True if credentials are valid and API is accessible
        """
        if not self.api_key:
            logger.error("Alpha Vantage API key not provided")
            return False
        
        try:
            # Test with a simple quote request
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': 'AAPL',
                    'apikey': self.api_key
                }
            )
            
            if success and response and isinstance(response, dict):
                # Check if response is valid (not an error message)
                if 'Global Quote' in response:
                    quote_data = response['Global Quote']
                    if '01. symbol' in quote_data and quote_data['01. symbol'] == 'AAPL':
                        logger.info("Alpha Vantage credentials validated successfully")
                        return True
                elif 'Error Message' in response:
                    logger.error(f"Alpha Vantage API error: {response['Error Message']}")
                    return False
                elif 'Note' in response:
                    logger.warning(f"Alpha Vantage rate limit: {response['Note']}")
                    return True  # Valid key, just rate limited
                else:
                    logger.error("Alpha Vantage API returned unexpected response format")
                    return False
            else:
                logger.error(f"Alpha Vantage credential validation failed: {errors}")
                return False
                
        except Exception as e:
            logger.error(f"Alpha Vantage credential validation error: {e}")
            return False
    
    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: int = 5,
        validate_data: bool = True
    ) -> ExtractionResult:
        """
        Load financial data for a symbol from Alpha Vantage API.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            categories: List of data categories to retrieve (all if None)
            historical_years: Years of historical data to retrieve (max 20)
            validate_data: Whether to validate data using registry definitions
            
        Returns:
            ExtractionResult with detailed results and metrics
        """
        start_time = time.time()
        symbol = self.normalize_symbol(symbol)
        
        if not self.api_key:
            return self._create_failed_result(
                symbol, "Alpha Vantage API key not configured", start_time
            )
        
        # Default to supported categories if none specified
        if categories is None:
            categories = [
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.COMPANY_INFO
            ]
        
        # Limit historical years to Alpha Vantage maximum
        historical_years = min(historical_years, 20)
        
        logger.info(f"Loading Alpha Vantage data for {symbol} - categories: {[cat.value for cat in categories]}")
        
        result = ExtractionResult(
            source=DataSourceType.ALPHA_VANTAGE,
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
                    
                    logger.info(f"Alpha Vantage {category.value}: {category_data['variables_extracted']} variables "
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
                'alpha_vantage_base_url': self.base_url,
                'rate_limit_delay': self.rate_limit_delay
            }
            
            result.extraction_time = time.time() - start_time
            
            logger.info(f"Alpha Vantage extraction for {symbol} completed: "
                       f"{result.variables_extracted} variables, "
                       f"quality={result.quality_metrics.overall_score:.2f}")
            
        except Exception as e:
            error_msg = f"Alpha Vantage extraction failed for {symbol}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.extraction_time = time.time() - start_time
        
        return result
    
    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol from Alpha Vantage.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary describing available data types and periods
        """
        symbol = self.normalize_symbol(symbol)
        
        if not self.api_key:
            return {'error': 'Alpha Vantage API key not configured'}
        
        availability = {
            'symbol': symbol,
            'source': 'alpha_vantage',
            'categories': {},
            'last_checked': datetime.now().isoformat()
        }
        
        try:
            # Check quote first (fastest and most reliable)
            quote_available = False
            try:
                success, response, errors = self.make_request_with_retry(
                    self._make_api_request,
                    {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': symbol,
                        'apikey': self.api_key
                    }
                )
                
                if success and response and 'Global Quote' in response:
                    quote_data = response['Global Quote']
                    if '01. symbol' in quote_data:
                        quote_available = True
                        
            except Exception as e:
                logger.debug(f"Alpha Vantage quote check failed: {e}")
            
            availability['categories']['market_data'] = {
                'available': quote_available,
                'periods': ['current'] if quote_available else [],
                'functions_available': ['GLOBAL_QUOTE'] if quote_available else []
            }
            
            # For other categories, we can't easily check without using more API calls
            # So we'll report them as "unknown" to avoid hitting rate limits
            for category in ['income', 'balance', 'cashflow', 'info']:
                availability['categories'][category] = {
                    'available': 'unknown',  # Would need API call to determine
                    'periods': [],
                    'note': 'Requires API call to determine availability'
                }
            
        except Exception as e:
            availability['error'] = str(e)
            logger.error(f"Alpha Vantage availability check failed for {symbol}: {e}")
        
        return availability

    def extract_variables(
        self,
        symbol: str,
        period: str = "latest",
        historical_years: int = 10
    ) -> 'GeneralizedVariableDict':
        """
        Extract financial variables from Alpha Vantage and return standardized dict.

        This is the core method that extracts data from Alpha Vantage API and transforms it
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

        logger.info(f"Extracting variables for {symbol} from Alpha Vantage, period={period}")

        if not self.api_key:
            raise AdapterException(
                "Alpha Vantage API key not configured",
                source="alpha_vantage",
                details={'symbol': symbol}
            )

        try:
            # Initialize output dictionary with required fields
            variables: GeneralizedVariableDict = {
                'ticker': symbol,
                'company_name': '',
                'currency': 'USD',
                'fiscal_year_end': 'December',
                'data_source': 'alpha_vantage',
                'data_timestamp': datetime.now(),
                'reporting_period': period
            }

            # Extract company overview
            self._extract_av_overview_to_dict(symbol, variables)

            # Extract quote/market data
            self._extract_av_quote_to_dict(symbol, variables)

            # Extract financial statement data
            if period == "latest":
                # Get the most recent period from each statement
                self._extract_av_latest_financials_to_dict(symbol, variables, historical_years)
            else:
                # Get specific period
                self._extract_av_period_financials_to_dict(symbol, period, variables)

            # Extract earnings data
            self._extract_av_earnings_to_dict(symbol, variables)

            # Extract historical data arrays
            if historical_years > 0:
                self._extract_av_historical_to_dict(symbol, historical_years, variables)

            # Generate composite variables
            composite_vars = self.generate_composite_variables(variables)
            variables.update(composite_vars)

            # Store metadata
            extraction_time = time.time() - start_time
            completeness = self.calculate_completeness_score(variables)

            self._last_metadata = AdapterOutputMetadata(
                source="alpha_vantage",
                timestamp=datetime.now(),
                quality_score=0.80,  # Alpha Vantage has good quality free data
                completeness=completeness,
                validation_errors=[],
                extraction_time=extraction_time,
                api_calls_made=self._stats['requests_made']
            )

            self._stats['symbols_processed'] += 1

            logger.info(f"Successfully extracted {len([v for v in variables.values() if v is not None])} "
                       f"variables for {symbol} from Alpha Vantage in {extraction_time:.2f}s")

            return variables

        except Exception as e:
            logger.error(f"Failed to extract variables for {symbol} from Alpha Vantage: {e}")
            raise AdapterException(
                f"Failed to extract variables for {symbol}",
                source="alpha_vantage",
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
                source="alpha_vantage",
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
            'company_info',
            'historical_data',
            'earnings_data'
        ]

    # =========================================================================
    # Helper Methods for extract_variables() Implementation
    # =========================================================================

    def _extract_av_overview_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract company overview data from Alpha Vantage into GeneralizedVariableDict"""
        try:
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )

            if not success or not response or isinstance(response, dict) and 'Error Message' in response:
                logger.warning(f"No Alpha Vantage overview data for {symbol}")
                return

            # Map fields from Alpha Vantage overview
            variables['company_name'] = response.get('Name', '')
            variables['description'] = response.get('Description')
            variables['sector'] = response.get('Sector')
            variables['industry'] = response.get('Industry')
            variables['exchange'] = response.get('Exchange')
            variables['currency'] = response.get('Currency', 'USD')
            variables['country'] = response.get('Country')
            variables['fiscal_year_end'] = response.get('FiscalYearEnd', 'December')

            # Market data from overview
            if response.get('MarketCapitalization'):
                variables['market_cap'] = float(response['MarketCapitalization']) / 1_000_000
            if response.get('SharesOutstanding'):
                variables['shares_outstanding'] = float(response['SharesOutstanding']) / 1_000_000

            # Valuation ratios from overview
            variables['pe_ratio'] = float(response['PERatio']) if response.get('PERatio') and response['PERatio'] != 'None' else None
            variables['forward_pe'] = float(response['ForwardPE']) if response.get('ForwardPE') and response['ForwardPE'] != 'None' else None
            variables['peg_ratio'] = float(response['PEGRatio']) if response.get('PEGRatio') and response['PEGRatio'] != 'None' else None
            variables['price_to_book'] = float(response['PriceToBookRatio']) if response.get('PriceToBookRatio') and response['PriceToBookRatio'] != 'None' else None
            variables['price_to_sales'] = float(response['PriceToSalesRatioTTM']) if response.get('PriceToSalesRatioTTM') and response['PriceToSalesRatioTTM'] != 'None' else None
            variables['ev_to_ebitda'] = float(response['EVToEBITDA']) if response.get('EVToEBITDA') and response['EVToEBITDA'] != 'None' else None
            variables['ev_to_revenue'] = float(response['EVToRevenue']) if response.get('EVToRevenue') and response['EVToRevenue'] != 'None' else None

            # Financial ratios from overview
            variables['gross_margin'] = float(response['GrossProfitTTM']) / float(response['RevenueTTM']) if response.get('GrossProfitTTM') and response.get('RevenueTTM') else None
            variables['operating_margin'] = float(response['OperatingMarginTTM']) if response.get('OperatingMarginTTM') and response['OperatingMarginTTM'] != 'None' else None
            variables['net_margin'] = float(response['ProfitMargin']) if response.get('ProfitMargin') and response['ProfitMargin'] != 'None' else None
            variables['return_on_assets'] = float(response['ReturnOnAssetsTTM']) if response.get('ReturnOnAssetsTTM') and response['ReturnOnAssetsTTM'] != 'None' else None
            variables['return_on_equity'] = float(response['ReturnOnEquityTTM']) if response.get('ReturnOnEquityTTM') and response['ReturnOnEquityTTM'] != 'None' else None

            # Growth metrics
            variables['revenue_growth'] = float(response['QuarterlyRevenueGrowthYOY']) if response.get('QuarterlyRevenueGrowthYOY') and response['QuarterlyRevenueGrowthYOY'] != 'None' else None
            variables['earnings_growth'] = float(response['QuarterlyEarningsGrowthYOY']) if response.get('QuarterlyEarningsGrowthYOY') and response['QuarterlyEarningsGrowthYOY'] != 'None' else None

            # Dividend data
            variables['dividend_per_share'] = float(response['DividendPerShare']) if response.get('DividendPerShare') and response['DividendPerShare'] != 'None' else None
            variables['dividend_yield'] = float(response['DividendYield']) if response.get('DividendYield') and response['DividendYield'] != 'None' else None

            # Other metrics
            variables['beta'] = float(response['Beta']) if response.get('Beta') and response['Beta'] != 'None' else None
            variables['eps_diluted'] = float(response['DilutedEPSTTM']) if response.get('DilutedEPSTTM') and response['DilutedEPSTTM'] != 'None' else None
            variables['book_value_per_share'] = float(response['BookValue']) if response.get('BookValue') and response['BookValue'] != 'None' else None

            logger.debug(f"Extracted Alpha Vantage overview for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting Alpha Vantage overview for {symbol}: {e}")

    def _extract_av_quote_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract quote/market data from Alpha Vantage into GeneralizedVariableDict"""
        try:
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )

            if not success or not response or 'Global Quote' not in response:
                logger.warning(f"No Alpha Vantage quote data for {symbol}")
                return

            quote = response['Global Quote']

            # Map quote fields (Alpha Vantage uses numbered keys)
            variables['stock_price'] = float(quote.get('05. price', 0)) if quote.get('05. price') else None
            variables['stock_price_change'] = float(quote.get('09. change', 0)) if quote.get('09. change') else None
            variables['stock_price_change_percent'] = float(quote.get('10. change percent', '0').rstrip('%')) if quote.get('10. change percent') else None

            logger.debug(f"Extracted Alpha Vantage quote for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting Alpha Vantage quote for {symbol}: {e}")

    def _extract_av_latest_financials_to_dict(
        self,
        symbol: str,
        variables: 'GeneralizedVariableDict',
        historical_years: int
    ) -> None:
        """Extract latest period from Alpha Vantage financial statements"""
        try:
            # Income statement
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'INCOME_STATEMENT',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )
            if success and response and 'annualReports' in response and len(response['annualReports']) > 0:
                self._map_av_income_to_dict(response['annualReports'][0], variables)

            # Balance sheet
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'BALANCE_SHEET',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )
            if success and response and 'annualReports' in response and len(response['annualReports']) > 0:
                self._map_av_balance_to_dict(response['annualReports'][0], variables)

            # Cash flow
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'CASH_FLOW',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )
            if success and response and 'annualReports' in response and len(response['annualReports']) > 0:
                self._map_av_cashflow_to_dict(response['annualReports'][0], variables)

            logger.debug(f"Extracted latest Alpha Vantage financials for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting latest Alpha Vantage financials for {symbol}: {e}")

    def _extract_av_period_financials_to_dict(
        self,
        symbol: str,
        period: str,
        variables: 'GeneralizedVariableDict'
    ) -> None:
        """Extract specific period from Alpha Vantage financial statements"""
        try:
            # Try to extract from each statement for the specified period
            for func_name in ['INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW']:
                success, response, _ = self.make_request_with_retry(
                    self._make_api_request,
                    {
                        'function': func_name,
                        'symbol': symbol,
                        'apikey': self.api_key
                    }
                )

                if not success or not response or 'annualReports' not in response:
                    continue

                # Find matching period
                for report in response['annualReports']:
                    if 'fiscalDateEnding' in report and period in report['fiscalDateEnding']:
                        if func_name == 'INCOME_STATEMENT':
                            self._map_av_income_to_dict(report, variables)
                        elif func_name == 'BALANCE_SHEET':
                            self._map_av_balance_to_dict(report, variables)
                        elif func_name == 'CASH_FLOW':
                            self._map_av_cashflow_to_dict(report, variables)
                        break

            logger.debug(f"Extracted Alpha Vantage period {period} financials for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting Alpha Vantage period {period} financials for {symbol}: {e}")

    def _extract_av_earnings_to_dict(self, symbol: str, variables: 'GeneralizedVariableDict') -> None:
        """Extract earnings data from Alpha Vantage into GeneralizedVariableDict"""
        try:
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'EARNINGS',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )

            if not success or not response or 'annualEarnings' not in response:
                logger.warning(f"No Alpha Vantage earnings for {symbol}")
                return

            # Get latest annual earnings
            if len(response['annualEarnings']) > 0:
                latest = response['annualEarnings'][0]
                if latest.get('reportedEPS') and latest['reportedEPS'] != 'None':
                    variables['eps_reported'] = float(latest['reportedEPS'])

            logger.debug(f"Extracted Alpha Vantage earnings for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting Alpha Vantage earnings for {symbol}: {e}")

    def _extract_av_historical_to_dict(
        self,
        symbol: str,
        historical_years: int,
        variables: 'GeneralizedVariableDict'
    ) -> None:
        """Extract historical data arrays from Alpha Vantage"""
        try:
            # Get historical income statements
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'INCOME_STATEMENT',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )

            if success and response and 'annualReports' in response:
                reports = response['annualReports'][:historical_years]
                variables['historical_revenue'] = [
                    float(r.get('totalRevenue', 0)) / 1_000_000
                    for r in reports if r.get('totalRevenue') and r['totalRevenue'] != 'None'
                ]
                variables['historical_net_income'] = [
                    float(r.get('netIncome', 0)) / 1_000_000
                    for r in reports if r.get('netIncome') and r['netIncome'] != 'None'
                ]
                variables['historical_dates'] = [
                    datetime.strptime(r['fiscalDateEnding'], '%Y-%m-%d').date()
                    for r in reports if r.get('fiscalDateEnding')
                ]

            # Get historical cash flows
            success, response, _ = self.make_request_with_retry(
                self._make_api_request,
                {
                    'function': 'CASH_FLOW',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )

            if success and response and 'annualReports' in response:
                reports = response['annualReports'][:historical_years]
                variables['historical_operating_cash_flow'] = [
                    float(r.get('operatingCashflow', 0)) / 1_000_000
                    for r in reports if r.get('operatingCashflow') and r['operatingCashflow'] != 'None'
                ]

            logger.debug(f"Extracted Alpha Vantage historical data for {symbol}")

        except Exception as e:
            logger.error(f"Error extracting Alpha Vantage historical data for {symbol}: {e}")

    def _map_av_income_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map Alpha Vantage income statement data to GeneralizedVariableDict"""
        try:
            def safe_float(value):
                if value is None or value == 'None' or value == '':
                    return None
                try:
                    return float(value) / 1_000_000
                except (ValueError, TypeError):
                    return None

            variables['revenue'] = safe_float(data.get('totalRevenue'))
            variables['cost_of_revenue'] = safe_float(data.get('costOfRevenue'))
            variables['gross_profit'] = safe_float(data.get('grossProfit'))
            variables['research_and_development'] = safe_float(data.get('researchAndDevelopment'))
            variables['selling_general_administrative'] = safe_float(data.get('sellingGeneralAndAdministrative'))
            variables['operating_expenses'] = safe_float(data.get('operatingExpenses'))
            variables['operating_income'] = safe_float(data.get('operatingIncome'))
            variables['interest_expense'] = safe_float(data.get('interestExpense'))
            variables['interest_income'] = safe_float(data.get('interestIncome'))
            variables['income_before_tax'] = safe_float(data.get('incomeBeforeTax'))
            variables['income_tax_expense'] = safe_float(data.get('incomeTaxExpense'))
            variables['net_income'] = safe_float(data.get('netIncome'))
            variables['ebitda'] = safe_float(data.get('ebitda'))
        except Exception as e:
            logger.error(f"Error mapping Alpha Vantage income statement: {e}")

    def _map_av_balance_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map Alpha Vantage balance sheet data to GeneralizedVariableDict"""
        try:
            def safe_float(value):
                if value is None or value == 'None' or value == '':
                    return None
                try:
                    return float(value) / 1_000_000
                except (ValueError, TypeError):
                    return None

            variables['cash_and_cash_equivalents'] = safe_float(data.get('cashAndCashEquivalentsAtCarryingValue'))
            variables['short_term_investments'] = safe_float(data.get('shortTermInvestments'))
            variables['accounts_receivable'] = safe_float(data.get('currentNetReceivables'))
            variables['inventory'] = safe_float(data.get('inventory'))
            variables['other_current_assets'] = safe_float(data.get('otherCurrentAssets'))
            variables['total_current_assets'] = safe_float(data.get('totalCurrentAssets'))
            variables['property_plant_equipment_net'] = safe_float(data.get('propertyPlantEquipment'))
            variables['goodwill'] = safe_float(data.get('goodwill'))
            variables['intangible_assets'] = safe_float(data.get('intangibleAssets'))
            variables['long_term_investments'] = safe_float(data.get('longTermInvestments'))
            variables['other_non_current_assets'] = safe_float(data.get('otherNonCurrentAssets'))
            variables['total_non_current_assets'] = safe_float(data.get('totalNonCurrentAssets'))
            variables['total_assets'] = safe_float(data.get('totalAssets'))
            variables['accounts_payable'] = safe_float(data.get('currentAccountsPayable'))
            variables['short_term_debt'] = safe_float(data.get('shortTermDebt'))
            variables['other_current_liabilities'] = safe_float(data.get('otherCurrentLiabilities'))
            variables['total_current_liabilities'] = safe_float(data.get('totalCurrentLiabilities'))
            variables['long_term_debt'] = safe_float(data.get('longTermDebt'))
            variables['other_non_current_liabilities'] = safe_float(data.get('otherNonCurrentLiabilities'))
            variables['total_non_current_liabilities'] = safe_float(data.get('totalNonCurrentLiabilities'))
            variables['total_liabilities'] = safe_float(data.get('totalLiabilities'))
            variables['common_stock'] = safe_float(data.get('commonStock'))
            variables['retained_earnings'] = safe_float(data.get('retainedEarnings'))
            variables['total_stockholders_equity'] = safe_float(data.get('totalShareholderEquity'))
        except Exception as e:
            logger.error(f"Error mapping Alpha Vantage balance sheet: {e}")

    def _map_av_cashflow_to_dict(self, data: Dict[str, Any], variables: 'GeneralizedVariableDict') -> None:
        """Map Alpha Vantage cash flow data to GeneralizedVariableDict"""
        try:
            def safe_float(value):
                if value is None or value == 'None' or value == '':
                    return None
                try:
                    return float(value) / 1_000_000
                except (ValueError, TypeError):
                    return None

            variables['operating_cash_flow'] = safe_float(data.get('operatingCashflow'))
            variables['depreciation_and_amortization'] = safe_float(data.get('depreciationDepletionAndAmortization'))
            variables['change_in_working_capital'] = safe_float(data.get('changeInOperatingLiabilities'))
            variables['change_in_accounts_receivable'] = safe_float(data.get('changeInReceivables'))
            variables['change_in_inventory'] = safe_float(data.get('changeInInventory'))
            variables['capital_expenditures'] = safe_float(data.get('capitalExpenditures'))
            variables['investing_cash_flow'] = safe_float(data.get('cashflowFromInvestment'))
            variables['dividends_paid'] = safe_float(data.get('dividendPayout'))
            variables['financing_cash_flow'] = safe_float(data.get('cashflowFromFinancing'))

            # Calculate free cash flow if not directly available
            if variables.get('operating_cash_flow') and variables.get('capital_expenditures'):
                variables['free_cash_flow'] = variables['operating_cash_flow'] - abs(variables['capital_expenditures'])
        except Exception as e:
            logger.error(f"Error mapping Alpha Vantage cash flow: {e}")

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
        """Extract data for a specific category from Alpha Vantage API"""
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
            functions = self._category_functions.get(category, [])
            if not functions:
                result['warnings'].append(f"No Alpha Vantage functions defined for category {category.value}")
                return result
            
            category_data = {}
            
            # Fetch data from each function for this category
            for function_key in functions:
                function_data = self._fetch_function_data(symbol, function_key)
                result['requests_made'] += 1
                
                if function_data:
                    category_data[function_key] = function_data
                
                # Be respectful of rate limits - add delay between requests
                if len(functions) > 1:
                    time.sleep(self.rate_limit_delay)
            
            if not category_data:
                result['warnings'].append(f"No data retrieved from Alpha Vantage for category {category.value}")
                return result
            
            # Convert and store data
            variables_stored = self._convert_and_store_category_data(
                symbol, category, category_data, validate_data
            )
            
            result['success'] = variables_stored > 0
            result['variables_extracted'] = variables_stored
            result['data_points_stored'] = variables_stored
            
            # Extract periods covered
            result['periods_covered'] = self._extract_periods_from_data(category_data, category)
            
        except Exception as e:
            error_msg = f"Alpha Vantage category {category.value} extraction failed: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _fetch_function_data(self, symbol: str, function_key: str) -> Optional[Dict[str, Any]]:
        """Fetch data from a specific Alpha Vantage function"""
        try:
            function_name = self.API_FUNCTIONS.get(function_key)
            if not function_name:
                logger.error(f"Unknown Alpha Vantage function key: {function_key}")
                return None
            
            params = {
                'function': function_name,
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            success, response, errors = self.make_request_with_retry(
                self._make_api_request, params
            )
            
            if success and response:
                return response
            else:
                logger.warning(f"Alpha Vantage {function_key} failed for {symbol}: {errors}")
                return None
                
        except Exception as e:
            logger.error(f"Alpha Vantage {function_key} fetch error for {symbol}: {e}")
            return None
    
    def _make_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Alpha Vantage API with error handling"""
        response = self.session.get(self.base_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Alpha Vantage returns error information in specific fields
        if isinstance(data, dict):
            if 'Error Message' in data:
                raise requests.RequestException(f"Alpha Vantage API error: {data['Error Message']}")
            elif 'Note' in data and 'rate limit' in data['Note'].lower():
                # Rate limit hit
                self._stats['rate_limit_hits'] += 1
                raise requests.RequestException(f"Alpha Vantage rate limit: {data['Note']}")
        
        return data
    
    def _convert_and_store_category_data(
        self,
        symbol: str,
        category: DataCategory,
        category_data: Dict[str, Dict[str, Any]],
        validate_data: bool
    ) -> int:
        """Convert category data and store in VarInputData"""
        variables_stored = 0
        
        try:
            # Handle different data structures for different categories
            if category == DataCategory.MARKET_DATA:
                variables_stored = self._process_market_data(symbol, category_data, validate_data)
            elif category == DataCategory.COMPANY_INFO:
                variables_stored = self._process_company_info(symbol, category_data, validate_data)
            else:
                # Financial statements (income, balance, cashflow)
                variables_stored = self._process_financial_statements(symbol, category, category_data, validate_data)
            
        except Exception as e:
            logger.error(f"Alpha Vantage data conversion/storage failed: {e}")
        
        return variables_stored
    
    def _process_market_data(self, symbol: str, category_data: Dict[str, Dict[str, Any]], validate_data: bool) -> int:
        """Process market data from Alpha Vantage quote"""
        variables_stored = 0
        
        for function_key, function_data in category_data.items():
            if function_key == 'quote' and 'Global Quote' in function_data:
                quote_data = function_data['Global Quote']
                
                # Alpha Vantage uses numbered fields in quotes
                field_mappings = {
                    '05. price': 'current_price',
                    '06. volume': 'volume',
                    '10. change percent': 'change_percent'
                }
                
                for av_field, standard_field in field_mappings.items():
                    if av_field in quote_data:
                        value = self._normalize_value(quote_data[av_field])
                        if value is not None and self._store_variable(
                            symbol, standard_field, value, 'current', 
                            'alpha_vantage_quote', validate_data
                        ):
                            variables_stored += 1
        
        return variables_stored
    
    def _process_company_info(self, symbol: str, category_data: Dict[str, Dict[str, Any]], validate_data: bool) -> int:
        """Process company information from Alpha Vantage overview"""
        variables_stored = 0
        
        for function_key, function_data in category_data.items():
            if function_key == 'overview' and isinstance(function_data, dict):
                # Alpha Vantage overview has direct field mappings
                field_mappings = {
                    'MarketCapitalization': 'market_cap',
                    'PERatio': 'pe_ratio',
                    'PriceToBookRatio': 'pb_ratio',
                    'DividendYield': 'dividend_yield',
                    'EPS': 'earnings_per_share',
                    'Beta': 'beta'
                }
                
                for av_field, standard_field in field_mappings.items():
                    if av_field in function_data:
                        value = self._normalize_value(function_data[av_field])
                        if value is not None and self._store_variable(
                            symbol, standard_field, value, 'current',
                            'alpha_vantage_overview', validate_data
                        ):
                            variables_stored += 1
        
        return variables_stored
    
    def _process_financial_statements(
        self, 
        symbol: str, 
        category: DataCategory, 
        category_data: Dict[str, Dict[str, Any]], 
        validate_data: bool
    ) -> int:
        """Process financial statements from Alpha Vantage"""
        variables_stored = 0
        
        for function_key, function_data in category_data.items():
            if not isinstance(function_data, dict):
                continue
            
            # Alpha Vantage returns financial statements in specific structure
            statement_keys = {
                'income': 'annualReports',
                'balance': 'annualReports',
                'cashflow': 'annualReports'
            }
            
            statement_key = statement_keys.get(function_key)
            if statement_key and statement_key in function_data:
                annual_reports = function_data[statement_key]
                if isinstance(annual_reports, list):
                    for report in annual_reports[:5]:  # Process up to 5 years
                        # Convert using Alpha Vantage converter
                        converted_data = self.converter.convert_financial_data({function_key: report})
                        
                        if converted_data:
                            period = self._extract_period_from_report(report)
                            
                            for var_name, value in converted_data.items():
                                if var_name in ['source', 'converted_at']:  # Skip metadata
                                    continue
                                
                                if self._store_variable(
                                    symbol, var_name, value, period,
                                    f'alpha_vantage_{function_key}', validate_data
                                ):
                                    variables_stored += 1
        
        return variables_stored
    
    def _extract_period_from_report(self, report: Dict[str, Any]) -> str:
        """Extract period from Alpha Vantage financial report"""
        # Alpha Vantage uses 'fiscalDateEnding' for period identification
        if 'fiscalDateEnding' in report:
            date_str = report['fiscalDateEnding']
            try:
                # Convert to year for simplicity
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return str(date_obj.year)
            except ValueError:
                pass
        
        return 'unknown'
    
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
                logger.debug(f"Alpha Vantage: Variable {var_name} not found in registry, skipping")
                return False
            
            # Create metadata
            metadata = VariableMetadata(
                source=source_detail,
                timestamp=datetime.now(),
                quality_score=0.8,  # Alpha Vantage generally has good quality data
                validation_passed=True,
                period=period,
                lineage_id=f"{symbol}_alpha_vantage_{var_name}_{period}"
            )
            
            # Validate if requested
            if validate_data and hasattr(var_def, 'validate_value'):
                is_valid, validation_errors = var_def.validate_value(value)
                if not is_valid:
                    metadata.validation_passed = False
                    metadata.quality_score *= 0.7
                    logger.debug(f"Alpha Vantage validation failed for {var_name}: {validation_errors}")
            
            # Store in VarInputData
            success = self.var_data.set_variable(
                symbol=symbol,
                variable_name=var_name,
                value=value,
                period=period,
                source="alpha_vantage",
                metadata=metadata,
                validate=False,  # Already validated above
                emit_event=False  # Batch processing
            )
            
            if success:
                logger.debug(f"Alpha Vantage stored: {symbol}.{var_name}[{period}] = {value}")
                return True
            else:
                logger.warning(f"Alpha Vantage failed to store {symbol}.{var_name}")
                return False
                
        except Exception as e:
            logger.error(f"Alpha Vantage variable storage error: {e}")
            return False
    
    def _normalize_value(self, value: Any) -> Optional[float]:
        """Normalize Alpha Vantage value to numeric format"""
        if value is None or value == 'None':
            return None
        
        try:
            # Handle string representations
            if isinstance(value, str):
                value = value.strip()
                if value == '' or value == 'None' or value == '-':
                    return None
                
                # Remove percentage signs and convert
                if value.endswith('%'):
                    return float(value[:-1]) / 100
                
                # Remove other formatting
                value = value.replace(',', '').replace('$', '')
            
            numeric_value = float(value)
            if abs(numeric_value) > 1e15:  # Sanity check
                return None
            return numeric_value
            
        except (ValueError, TypeError):
            return None
    
    def _extract_periods_from_data(
        self, 
        category_data: Dict[str, Dict[str, Any]], 
        category: DataCategory
    ) -> List[str]:
        """Extract all periods covered by the category data"""
        periods = set()
        
        if category == DataCategory.MARKET_DATA:
            periods.add('current')
        else:
            # Extract periods from financial statements
            for function_key, function_data in category_data.items():
                if isinstance(function_data, dict) and 'annualReports' in function_data:
                    annual_reports = function_data['annualReports']
                    if isinstance(annual_reports, list):
                        for report in annual_reports:
                            period = self._extract_period_from_report(report)
                            periods.add(period)
        
        return sorted(list(periods), reverse=True)
    
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
        
        # Alpha Vantage quality characteristics
        timeliness_score = 0.85   # Good timeliness, frequent updates
        consistency_score = 0.82  # Generally consistent but some data gaps
        
        # Alpha Vantage reliability
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
            'assessment_time': datetime.now().isoformat(),
            'rate_limit_hits': self._stats.get('rate_limit_hits', 0)
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
            source=DataSourceType.ALPHA_VANTAGE,
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
        """Assess how recent/timely the Alpha Vantage data is"""
        if category == DataCategory.MARKET_DATA:
            return 0.95  # Very recent market data
        elif category in [DataCategory.INCOME_STATEMENT, DataCategory.BALANCE_SHEET, DataCategory.CASH_FLOW]:
            return 0.75  # Financial statements updated less frequently
        else:
            return 0.85  # Generally recent data
    
    def _assess_data_consistency(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess internal consistency of Alpha Vantage data"""
        # Alpha Vantage has good consistency but occasional gaps
        return 0.82


# Convenience functions for common operations

def load_alpha_vantage_data(symbol: str, api_key: Optional[str] = None, **kwargs) -> ExtractionResult:
    """
    Convenience function to load Alpha Vantage data for a symbol.
    
    Args:
        symbol: Stock symbol
        api_key: Alpha Vantage API key (optional, will use environment variable)
        **kwargs: Additional arguments for AlphaVantageAdapter.load_symbol_data()
        
    Returns:
        ExtractionResult with extraction statistics
    """
    adapter = AlphaVantageAdapter(api_key=api_key)
    return adapter.load_symbol_data(symbol, **kwargs)


def check_alpha_vantage_availability(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to check Alpha Vantage data availability.
    
    Args:
        symbol: Stock symbol to check
        api_key: Alpha Vantage API key (optional, will use environment variable)
        
    Returns:
        Dictionary with availability information
    """
    adapter = AlphaVantageAdapter(api_key=api_key)
    return adapter.get_available_data(symbol)


def get_alpha_vantage_adapter_stats(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get Alpha Vantage adapter statistics.
    
    Args:
        api_key: Alpha Vantage API key (optional, will use environment variable)
        
    Returns:
        Statistics dictionary
    """
    adapter = AlphaVantageAdapter(api_key=api_key)
    return adapter.get_performance_stats()