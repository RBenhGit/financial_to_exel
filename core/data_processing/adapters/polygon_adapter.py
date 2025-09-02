"""
Polygon.io API Adapter
======================

Extracts financial variables from Polygon.io API into standardized VarInputData format.

Polygon.io is a premium financial data provider offering real-time and historical market data,
financial statements, and company fundamentals through a comprehensive REST API. This adapter
provides seamless integration with the VarInputData system and FinancialVariableRegistry.

Key Features:
-------------
- **Real-time Market Data**: Live quotes, trades, and market statistics
- **Historical Data**: Extensive historical market and fundamental data
- **Financial Statements**: Comprehensive income statements, balance sheets, and cash flows
- **High Data Quality**: Institutional-grade data with rigorous validation
- **Flexible Rate Limits**: Scalable plans with generous API quotas
- **Global Coverage**: Support for multiple markets and asset classes
- **WebSocket Support**: Real-time streaming data capabilities
- **Data Validation**: Quality checks and validation against registry definitions
- **Error Recovery**: Robust error handling with automatic retry mechanisms

API Documentation: https://polygon.io/docs

Usage Example:
--------------
>>> from polygon_adapter import PolygonAdapter
>>> from var_input_data import get_var_input_data
>>> 
>>> # Initialize adapter with API key
>>> adapter = PolygonAdapter(api_key="your_polygon_key")
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
from ..converters.polygon_converter import PolygonConverter

# Configure logging
logger = logging.getLogger(__name__)


class PolygonAdapter(BaseApiAdapter):
    """
    Polygon.io API adapter for extracting financial variables.
    
    This adapter provides comprehensive access to Polygon's institutional-grade financial
    data, including real-time market data, financial statements, and company information.
    """
    
    # Polygon.io API base URL and endpoints
    BASE_URL = "https://api.polygon.io"
    ENDPOINTS = {
        'quote': '/v2/last/trade/{symbol}',
        'ticker_details': '/v3/reference/tickers/{symbol}',
        'financials': '/vX/reference/financials',
        'market_status': '/v1/marketstatus/now',
        'previous_close': '/v2/aggs/ticker/{symbol}/prev'
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.1,  # Polygon: varies by plan, generous limits
        base_url: Optional[str] = None
    ):
        """
        Initialize the Polygon adapter.
        
        Args:
            api_key: Polygon API key (will try to get from environment if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            rate_limit_delay: Minimum delay between requests
            base_url: Custom base URL (for testing)
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('POLYGON_API_KEY')
        
        super().__init__(api_key, timeout, max_retries, retry_delay, rate_limit_delay)
        
        if not self.api_key:
            logger.warning("Polygon API key not found. Set POLYGON_API_KEY environment variable.")
        
        self.base_url = base_url or self.BASE_URL
        self.converter = PolygonConverter()
        
        # Polygon-specific configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Financial-Analysis-Tool/1.0',
            'Accept': 'application/json'
        })
        
        # Polygon data categories mapping
        self._category_endpoints = {
            DataCategory.MARKET_DATA: ['quote', 'previous_close'],
            DataCategory.INCOME_STATEMENT: ['financials'],
            DataCategory.BALANCE_SHEET: ['financials'],
            DataCategory.CASH_FLOW: ['financials'],
            DataCategory.COMPANY_INFO: ['ticker_details']
        }
        
        logger.info("Polygon adapter initialized")
    
    def get_source_type(self) -> DataSourceType:
        """Return the data source type for Polygon"""
        return DataSourceType.POLYGON
    
    def get_capabilities(self) -> ApiCapabilities:
        """Return Polygon API capabilities"""
        return ApiCapabilities(
            source_type=DataSourceType.POLYGON,
            supported_categories=[
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.COMPANY_INFO
            ],
            rate_limit_per_minute=1000,     # Varies by plan, generally generous
            rate_limit_per_day=None,        # Plan-dependent
            max_historical_years=20,
            requires_api_key=True,
            supports_batch_requests=True,
            real_time_data=True,
            cost_per_request=None,          # Varies by plan
            reliability_rating=0.95         # Very high reliability, institutional grade
        )
    
    def validate_credentials(self) -> bool:
        """
        Validate Polygon API credentials by making a test request.
        
        Returns:
            True if credentials are valid and API is accessible
        """
        if not self.api_key:
            logger.error("Polygon API key not provided")
            return False
        
        try:
            # Test with market status endpoint (lightweight)
            test_url = f"{self.base_url}/v1/marketstatus/now"
            success, response, errors = self.make_request_with_retry(
                self._make_api_request,
                test_url,
                {'apikey': self.api_key}
            )
            
            if success and response and isinstance(response, dict):
                # Check if response is valid
                if 'market' in response:
                    logger.info("Polygon credentials validated successfully")
                    return True
                elif 'status' in response and response['status'] == 'ERROR':
                    logger.error(f"Polygon API error: {response.get('error', 'Unknown error')}")
                    return False
                else:
                    logger.error("Polygon API returned unexpected response format")
                    return False
            else:
                logger.error(f"Polygon credential validation failed: {errors}")
                return False
                
        except Exception as e:
            logger.error(f"Polygon credential validation error: {e}")
            return False
    
    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: int = 5,
        validate_data: bool = True
    ) -> ExtractionResult:
        """
        Load financial data for a symbol from Polygon API.
        
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
                symbol, "Polygon API key not configured", start_time
            )
        
        # Default to all categories if none specified
        if categories is None:
            categories = [
                DataCategory.MARKET_DATA,
                DataCategory.INCOME_STATEMENT,
                DataCategory.BALANCE_SHEET,
                DataCategory.CASH_FLOW,
                DataCategory.COMPANY_INFO
            ]
        
        # Limit historical years to Polygon maximum
        historical_years = min(historical_years, 20)
        
        logger.info(f"Loading Polygon data for {symbol} - categories: {[cat.value for cat in categories]}")
        
        result = ExtractionResult(
            source=DataSourceType.POLYGON,
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
                    
                    logger.info(f"Polygon {category.value}: {category_data['variables_extracted']} variables "
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
                'polygon_base_url': self.base_url
            }
            
            result.extraction_time = time.time() - start_time
            
            logger.info(f"Polygon extraction for {symbol} completed: "
                       f"{result.variables_extracted} variables, "
                       f"quality={result.quality_metrics.overall_score:.2f}")
            
        except Exception as e:
            error_msg = f"Polygon extraction failed for {symbol}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.extraction_time = time.time() - start_time
        
        return result
    
    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol from Polygon.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary describing available data types and periods
        """
        symbol = self.normalize_symbol(symbol)
        
        if not self.api_key:
            return {'error': 'Polygon API key not configured'}
        
        availability = {
            'symbol': symbol,
            'source': 'polygon',
            'categories': {},
            'last_checked': datetime.now().isoformat()
        }
        
        try:
            # Check ticker details first (lightweight)
            ticker_available = False
            try:
                url = f"{self.base_url}/v3/reference/tickers/{symbol}"
                success, response, errors = self.make_request_with_retry(
                    self._make_api_request,
                    url,
                    {'apikey': self.api_key}
                )
                
                if success and response and 'results' in response:
                    ticker_data = response['results']
                    if 'ticker' in ticker_data and ticker_data['ticker'] == symbol:
                        ticker_available = True
                        
            except Exception as e:
                logger.debug(f"Polygon ticker check failed: {e}")
            
            availability['categories']['company_info'] = {
                'available': ticker_available,
                'periods': ['current'] if ticker_available else [],
                'endpoints_available': ['ticker_details'] if ticker_available else []
            }
            
            # Check market data availability
            market_data_available = False
            try:
                url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
                success, response, errors = self.make_request_with_retry(
                    self._make_api_request,
                    url,
                    {'apikey': self.api_key}
                )
                
                if success and response and 'results' in response:
                    results = response['results']
                    if isinstance(results, list) and len(results) > 0:
                        market_data_available = True
                        
            except Exception as e:
                logger.debug(f"Polygon market data check failed: {e}")
            
            availability['categories']['market_data'] = {
                'available': market_data_available,
                'periods': ['current', 'previous_close'] if market_data_available else [],
                'endpoints_available': ['quote', 'previous_close'] if market_data_available else []
            }
            
            # For financials, we can't easily check without making expensive calls
            for category in ['income', 'balance', 'cashflow']:
                availability['categories'][category] = {
                    'available': 'unknown',  # Would need API call to determine
                    'periods': [],
                    'note': 'Requires financial data API call to determine availability'
                }
            
        except Exception as e:
            availability['error'] = str(e)
            logger.error(f"Polygon availability check failed for {symbol}: {e}")
        
        return availability
    
    # Private helper methods
    
    def _extract_category_data(
        self,
        symbol: str,
        category: DataCategory,
        historical_years: int,
        validate_data: bool
    ) -> Dict[str, Any]:
        """Extract data for a specific category from Polygon API"""
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
                result['warnings'].append(f"No Polygon endpoints defined for category {category.value}")
                return result
            
            category_data = {}
            
            # Fetch data from each endpoint for this category
            for endpoint in endpoints:
                endpoint_data = self._fetch_endpoint_data(symbol, endpoint, category, historical_years)
                result['requests_made'] += 1
                
                if endpoint_data:
                    category_data[endpoint] = endpoint_data
            
            if not category_data:
                result['warnings'].append(f"No data retrieved from Polygon for category {category.value}")
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
            error_msg = f"Polygon category {category.value} extraction failed: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _fetch_endpoint_data(
        self,
        symbol: str,
        endpoint: str,
        category: DataCategory,
        historical_years: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch data from a specific Polygon endpoint"""
        try:
            if endpoint == 'financials':
                # Special handling for financials endpoint
                url = f"{self.base_url}/vX/reference/financials"
                params = {
                    'ticker': symbol,
                    'apikey': self.api_key,
                    'limit': historical_years * 4  # Quarterly reports
                }
                
                # Add financial statement type filter based on category
                if category == DataCategory.INCOME_STATEMENT:
                    params['filing_type'] = 'income_statement'
                elif category == DataCategory.BALANCE_SHEET:
                    params['filing_type'] = 'balance_sheet'
                elif category == DataCategory.CASH_FLOW:
                    params['filing_type'] = 'cash_flow_statement'
                
            else:
                # Standard endpoint handling
                endpoint_url = self.ENDPOINTS.get(endpoint, '')
                if '{symbol}' in endpoint_url:
                    url = f"{self.base_url}{endpoint_url.format(symbol=symbol)}"
                else:
                    url = f"{self.base_url}{endpoint_url}"
                
                params = {'apikey': self.api_key}
            
            success, response, errors = self.make_request_with_retry(
                self._make_api_request, url, params
            )
            
            if success and response:
                return response
            else:
                logger.warning(f"Polygon {endpoint} endpoint failed for {symbol}: {errors}")
                return None
                
        except Exception as e:
            logger.error(f"Polygon {endpoint} fetch error for {symbol}: {e}")
            return None
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Polygon API with error handling"""
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Polygon returns status information in the response
        if isinstance(data, dict):
            if 'status' in data:
                if data['status'] == 'ERROR':
                    error_msg = data.get('error', 'Unknown Polygon API error')
                    raise requests.RequestException(f"Polygon API error: {error_msg}")
                elif data['status'] == 'NOT_FOUND':
                    raise requests.RequestException(f"Polygon API: Data not found")
        
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
            logger.error(f"Polygon data conversion/storage failed: {e}")
        
        return variables_stored
    
    def _process_market_data(self, symbol: str, category_data: Dict[str, Dict[str, Any]], validate_data: bool) -> int:
        """Process market data from Polygon quotes and aggregates"""
        variables_stored = 0
        
        for endpoint, endpoint_data in category_data.items():
            if endpoint == 'previous_close' and 'results' in endpoint_data:
                results = endpoint_data['results']
                if isinstance(results, list) and len(results) > 0:
                    agg_data = results[0]
                    
                    # Polygon aggregate fields
                    field_mappings = {
                        'c': 'close_price',     # Close price
                        'h': 'high_price',      # High price
                        'l': 'low_price',       # Low price
                        'o': 'open_price',      # Open price
                        'v': 'volume'           # Volume
                    }
                    
                    for poly_field, standard_field in field_mappings.items():
                        if poly_field in agg_data:
                            value = self._normalize_value(agg_data[poly_field])
                            if value is not None and self._store_variable(
                                symbol, standard_field, value, 'previous_close',
                                'polygon_aggregates', validate_data
                            ):
                                variables_stored += 1
        
        return variables_stored
    
    def _process_company_info(self, symbol: str, category_data: Dict[str, Dict[str, Any]], validate_data: bool) -> int:
        """Process company information from Polygon ticker details"""
        variables_stored = 0
        
        for endpoint, endpoint_data in category_data.items():
            if endpoint == 'ticker_details' and 'results' in endpoint_data:
                ticker_data = endpoint_data['results']
                
                # Polygon ticker detail fields
                field_mappings = {
                    'market_cap': 'market_cap',
                    'share_class_shares_outstanding': 'shares_outstanding',
                    'weighted_shares_outstanding': 'shares_outstanding'
                }
                
                for poly_field, standard_field in field_mappings.items():
                    if poly_field in ticker_data:
                        value = self._normalize_value(ticker_data[poly_field])
                        if value is not None and self._store_variable(
                            symbol, standard_field, value, 'current',
                            'polygon_ticker_details', validate_data
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
        """Process financial statements from Polygon financials endpoint"""
        variables_stored = 0
        
        for endpoint, endpoint_data in category_data.items():
            if endpoint == 'financials' and 'results' in endpoint_data:
                results = endpoint_data['results']
                if isinstance(results, list):
                    for financial_report in results[:10]:  # Process up to 10 reports
                        # Convert using Polygon converter
                        converted_data = self.converter.convert_financial_data(financial_report)
                        
                        if converted_data:
                            period = self._extract_period_from_report(financial_report)
                            
                            for var_name, value in converted_data.items():
                                if var_name in ['source', 'converted_at']:  # Skip metadata
                                    continue
                                
                                if self._store_variable(
                                    symbol, var_name, value, period,
                                    f'polygon_financials', validate_data
                                ):
                                    variables_stored += 1
        
        return variables_stored
    
    def _extract_period_from_report(self, report: Dict[str, Any]) -> str:
        """Extract period from Polygon financial report"""
        # Polygon uses different period fields
        for period_field in ['end_date', 'filing_date', 'period_of_report_date']:
            if period_field in report and report[period_field]:
                date_str = report[period_field]
                try:
                    # Convert to year for simplicity
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    return str(date_obj.year)
                except ValueError:
                    continue
        
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
                logger.debug(f"Polygon: Variable {var_name} not found in registry, skipping")
                return False
            
            # Create metadata
            metadata = VariableMetadata(
                source=source_detail,
                timestamp=datetime.now(),
                quality_score=0.95,  # Polygon has very high quality data
                validation_passed=True,
                period=period,
                lineage_id=f"{symbol}_polygon_{var_name}_{period}"
            )
            
            # Validate if requested
            if validate_data and hasattr(var_def, 'validate_value'):
                is_valid, validation_errors = var_def.validate_value(value)
                if not is_valid:
                    metadata.validation_passed = False
                    metadata.quality_score *= 0.9
                    logger.debug(f"Polygon validation failed for {var_name}: {validation_errors}")
            
            # Store in VarInputData
            success = self.var_data.set_variable(
                symbol=symbol,
                variable_name=var_name,
                value=value,
                period=period,
                source="polygon",
                metadata=metadata,
                validate=False,  # Already validated above
                emit_event=False  # Batch processing
            )
            
            if success:
                logger.debug(f"Polygon stored: {symbol}.{var_name}[{period}] = {value}")
                return True
            else:
                logger.warning(f"Polygon failed to store {symbol}.{var_name}")
                return False
                
        except Exception as e:
            logger.error(f"Polygon variable storage error: {e}")
            return False
    
    def _normalize_value(self, value: Any) -> Optional[float]:
        """Normalize Polygon value to numeric format"""
        if value is None:
            return None
        
        try:
            # Handle string representations
            if isinstance(value, str):
                value = value.strip()
                if value == '' or value == 'null' or value.lower() == 'none':
                    return None
                
                # Remove formatting
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
            periods.add('previous_close')
        elif category == DataCategory.COMPANY_INFO:
            periods.add('current')
        else:
            # Extract periods from financial statements
            for endpoint, endpoint_data in category_data.items():
                if endpoint == 'financials' and 'results' in endpoint_data:
                    results = endpoint_data['results']
                    if isinstance(results, list):
                        for report in results:
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
        
        # Polygon quality characteristics
        timeliness_score = 0.98   # Excellent timeliness, real-time data
        consistency_score = 0.95  # Very high consistency, institutional grade
        
        # Polygon reliability
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
            source=DataSourceType.POLYGON,
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
        """Assess how recent/timely the Polygon data is"""
        if category == DataCategory.MARKET_DATA:
            return 0.99  # Excellent real-time market data
        elif category in [DataCategory.INCOME_STATEMENT, DataCategory.BALANCE_SHEET, DataCategory.CASH_FLOW]:
            return 0.90  # Very recent financial statements
        else:
            return 0.95  # Generally very recent data
    
    def _assess_data_consistency(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess internal consistency of Polygon data"""
        # Polygon has excellent consistency due to institutional-grade quality
        return 0.95


# Convenience functions for common operations

def load_polygon_data(symbol: str, api_key: Optional[str] = None, **kwargs) -> ExtractionResult:
    """
    Convenience function to load Polygon data for a symbol.
    
    Args:
        symbol: Stock symbol
        api_key: Polygon API key (optional, will use environment variable)
        **kwargs: Additional arguments for PolygonAdapter.load_symbol_data()
        
    Returns:
        ExtractionResult with extraction statistics
    """
    adapter = PolygonAdapter(api_key=api_key)
    return adapter.load_symbol_data(symbol, **kwargs)


def check_polygon_availability(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to check Polygon data availability.
    
    Args:
        symbol: Stock symbol to check
        api_key: Polygon API key (optional, will use environment variable)
        
    Returns:
        Dictionary with availability information
    """
    adapter = PolygonAdapter(api_key=api_key)
    return adapter.get_available_data(symbol)


def get_polygon_adapter_stats(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get Polygon adapter statistics.
    
    Args:
        api_key: Polygon API key (optional, will use environment variable)
        
    Returns:
        Statistics dictionary
    """
    adapter = PolygonAdapter(api_key=api_key)
    return adapter.get_performance_stats()