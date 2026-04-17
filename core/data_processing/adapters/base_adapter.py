"""
Base API Adapter Interface
==========================

Abstract base class defining the standardized interface for all financial data API adapters.
This ensures consistent behavior across different data sources (yfinance, FMP, Alpha Vantage, Polygon)
and enables seamless intelligent fallback between sources.

The adapter pattern provides:
- Standardized data extraction interface
- Consistent error handling and retry logic
- Rate limiting and performance monitoring
- Data quality assessment and scoring
- Intelligent fallback capabilities

Key Features:
-------------
- **Unified Interface**: All adapters implement the same methods and return consistent data structures
- **Quality Scoring**: Each adapter assesses and scores data quality for intelligent source selection
- **Rate Limiting**: Built-in rate limiting to comply with API restrictions
- **Error Recovery**: Robust error handling with automatic retry mechanisms
- **Performance Metrics**: Comprehensive statistics tracking for monitoring and optimization
- **Extensible Design**: Easy addition of new data sources following the established pattern

Usage:
------
>>> from fmp_adapter import FMPAdapter
>>> adapter = FMPAdapter(api_key="your_key")
>>> result = adapter.load_symbol_data("AAPL")
>>> print(f"Quality score: {result.quality_score}")
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration of supported data source types"""
    YFINANCE = "yfinance"
    FMP = "fmp"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    TWELVE_DATA = "twelve_data"
    EXCEL = "excel"


class DataCategory(Enum):
    """Categories of financial data that can be extracted"""
    MARKET_DATA = "market_data"          # Current price, market cap, ratios
    INCOME_STATEMENT = "income"          # Revenue, expenses, net income
    BALANCE_SHEET = "balance"            # Assets, liabilities, equity
    CASH_FLOW = "cashflow"              # Operating, investing, financing cash flows
    FINANCIAL_RATIOS = "ratios"         # Calculated ratios and metrics
    COMPANY_INFO = "info"               # Company profile, sector, industry


@dataclass
class DataQualityMetrics:
    """Metrics for assessing data quality from an API source"""
    completeness_score: float           # Percentage of expected fields present (0-1)
    timeliness_score: float            # How recent the data is (0-1)
    consistency_score: float           # Internal consistency checks (0-1)
    reliability_score: float           # Historical API reliability (0-1)
    overall_score: float               # Weighted overall quality score (0-1)
    issues: List[str]                  # List of quality issues identified
    metadata: Dict[str, Any]           # Additional quality metadata


@dataclass
class ExtractionResult:
    """Result of extracting data from an API source"""
    source: DataSourceType
    symbol: str
    success: bool
    variables_extracted: int
    data_points_stored: int
    categories_covered: List[DataCategory]
    periods_covered: List[str]
    quality_metrics: DataQualityMetrics
    extraction_time: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    raw_response_size: Optional[int] = None
    cache_hit: bool = False


@dataclass
class ApiCapabilities:
    """Describes what an API adapter can provide"""
    source_type: DataSourceType
    supported_categories: List[DataCategory]
    rate_limit_per_minute: int
    rate_limit_per_day: Optional[int]
    max_historical_years: int
    requires_api_key: bool
    supports_batch_requests: bool
    real_time_data: bool
    cost_per_request: Optional[float]
    reliability_rating: float           # Historical reliability (0-1)


class BaseApiAdapter(ABC):
    """
    Abstract base class for all financial data API adapters.
    
    This class defines the standard interface that all adapters must implement,
    ensuring consistency across different data sources and enabling intelligent
    fallback mechanisms.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.1
    ):
        """
        Initialize the base adapter with common configuration.
        
        Args:
            api_key: API key for authentication (if required)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Base delay between retries in seconds (exponential backoff)
            rate_limit_delay: Minimum delay between requests to avoid rate limiting
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        
        # Performance and reliability tracking
        self._stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'total_response_time': 0.0,
            'cache_hits': 0,
            'rate_limit_hits': 0,
            'symbols_processed': 0,
            'last_request_time': 0.0
        }
        
        # Initialize registry and data storage connections
        try:
            from ..financial_variable_registry import get_registry
            from ..var_input_data import get_var_input_data
            
            self.variable_registry = get_registry()
            self.var_data = get_var_input_data()
        except ImportError as e:
            logger.warning(f"Could not initialize registry/var_data: {e}")
            self.variable_registry = None
            self.var_data = None
        
        logger.info(f"{self.get_source_type().value} adapter initialized")
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    def get_source_type(self) -> DataSourceType:
        """Return the data source type for this adapter"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ApiCapabilities:
        """Return the capabilities of this API adapter"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate API credentials and connectivity.
        
        Returns:
            True if credentials are valid and API is accessible
        """
        pass
    
    @abstractmethod
    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: Optional[int] = None,
        validate_data: bool = True
    ) -> ExtractionResult:
        """
        Load financial data for a symbol from the API source.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            categories: List of data categories to retrieve (all if None)
            historical_years: Years of historical data to retrieve. If None,
                uses the maximum available for this API source.
            validate_data: Whether to validate data using registry definitions

        Returns:
            ExtractionResult with detailed results and metrics
        """
        pass
    
    @abstractmethod
    def get_available_data(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol without loading it all.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary describing available data types and periods
        """
        pass
    
    # Common utility methods available to all adapters
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics for this adapter"""
        if self._stats['requests_made'] > 0:
            avg_response_time = self._stats['total_response_time'] / self._stats['requests_made']
            success_rate = 1 - (self._stats['requests_failed'] / self._stats['requests_made'])
        else:
            avg_response_time = 0.0
            success_rate = 0.0
        
        capabilities = self.get_capabilities()
        
        return {
            'source_type': self.get_source_type().value,
            'requests_made': self._stats['requests_made'],
            'requests_failed': self._stats['requests_failed'],
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate': self._stats['cache_hits'] / max(1, self._stats['requests_made']),
            'rate_limit_hits': self._stats['rate_limit_hits'],
            'symbols_processed': self._stats['symbols_processed'],
            'reliability_rating': capabilities.reliability_rating,
            'last_request_time': self._stats['last_request_time']
        }
    
    def enforce_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary"""
        current_time = time.time()
        time_since_last_request = current_time - self._stats['last_request_time']
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self._stats['last_request_time'] = time.time()
    
    def make_request_with_retry(
        self,
        request_func,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, List[str]]:
        """
        Execute a request function with automatic retry logic.
        
        Args:
            request_func: Function to call for the actual request
            *args: Arguments to pass to the request function
            **kwargs: Keyword arguments to pass to the request function
            
        Returns:
            Tuple of (success, result, errors)
        """
        errors = []
        
        for attempt in range(self.max_retries + 1):
            try:
                self.enforce_rate_limit()
                self._stats['requests_made'] += 1
                
                start_time = time.time()
                result = request_func(*args, **kwargs)
                response_time = time.time() - start_time
                
                self._stats['total_response_time'] += response_time
                
                return True, result, errors
                
            except Exception as e:
                error_msg = f"Request attempt {attempt + 1} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
                self._stats['requests_failed'] += 1
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts")
        
        return False, None, errors
    
    def calculate_data_quality(
        self,
        data: Dict[str, Any],
        expected_fields: List[str],
        category: DataCategory
    ) -> DataQualityMetrics:
        """
        Calculate data quality metrics for extracted data.
        
        Args:
            data: Extracted data dictionary
            expected_fields: List of expected field names
            category: Data category being assessed
            
        Returns:
            DataQualityMetrics object with quality assessment
        """
        issues = []
        metadata = {}
        
        # Calculate completeness score
        if expected_fields:
            present_fields = [field for field in expected_fields if field in data and data[field] is not None]
            completeness_score = len(present_fields) / len(expected_fields)
            missing_fields = [field for field in expected_fields if field not in present_fields]
            if missing_fields:
                issues.append(f"Missing fields: {', '.join(missing_fields)}")
        else:
            completeness_score = 1.0 if data else 0.0
        
        # Calculate timeliness score (implementation depends on data structure)
        timeliness_score = self._assess_data_timeliness(data, category)
        
        # Calculate consistency score
        consistency_score = self._assess_data_consistency(data, category)
        
        # Get adapter's reliability rating
        capabilities = self.get_capabilities()
        reliability_score = capabilities.reliability_rating
        
        # Calculate weighted overall score
        overall_score = (
            completeness_score * 0.4 +
            timeliness_score * 0.3 +
            consistency_score * 0.2 +
            reliability_score * 0.1
        )
        
        metadata.update({
            'fields_expected': len(expected_fields) if expected_fields else 0,
            'fields_present': len([k for k, v in data.items() if v is not None]) if data else 0,
            'assessment_time': datetime.now().isoformat()
        })
        
        return DataQualityMetrics(
            completeness_score=completeness_score,
            timeliness_score=timeliness_score,
            consistency_score=consistency_score,
            reliability_score=reliability_score,
            overall_score=overall_score,
            issues=issues,
            metadata=metadata
        )
    
    def _assess_data_timeliness(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess how recent/timely the data is (to be overridden by subclasses)"""
        # Default implementation returns 0.8 (reasonably recent)
        # Subclasses should override with source-specific logic
        return 0.8
    
    def _assess_data_consistency(self, data: Dict[str, Any], category: DataCategory) -> float:
        """Assess internal consistency of the data (to be overridden by subclasses)"""
        # Default implementation returns 0.9 (generally consistent)
        # Subclasses should implement source-specific consistency checks
        return 0.9
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this API source"""
        return symbol.upper().strip()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.get_source_type().value})"