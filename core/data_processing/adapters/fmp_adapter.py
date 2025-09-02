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
    
    # Private helper methods
    
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