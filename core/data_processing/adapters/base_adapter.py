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
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

# Import new types
from .types import (
    GeneralizedVariableDict,
    AdapterOutputMetadata,
    ValidationResult,
    AdapterException,
    AdapterStatus,
    AdapterInfo,
    REQUIRED_FIELDS
)

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration of supported data source types"""
    YFINANCE = "yfinance"
    FMP = "fmp"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
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

        # Thread-safety lock for concurrent access
        self._lock = threading.RLock()

        # Adapter status tracking
        self._status = AdapterStatus.READY

        # Last extraction metadata
        self._last_metadata: Optional[AdapterOutputMetadata] = None

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
        historical_years: int = 5,
        validate_data: bool = True
    ) -> ExtractionResult:
        """
        Load financial data for a symbol from the API source.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            categories: List of data categories to retrieve (all if None)
            historical_years: Years of historical data to retrieve
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

    @abstractmethod
    def extract_variables(
        self,
        symbol: str,
        period: str = "latest",
        historical_years: int = 10
    ) -> GeneralizedVariableDict:
        """
        Extract financial variables from source and return standardized dict.

        This is the core method that all adapters must implement. It should
        extract data from the source (API or file) and transform it into the
        standardized GeneralizedVariableDict format.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: Period identifier ("latest", "2023", "2023-Q1", etc.)
            historical_years: Number of years of historical data to include

        Returns:
            GeneralizedVariableDict with standardized variable names and values

        Raises:
            AdapterException: On extraction or transformation failures
        """
        pass

    @abstractmethod
    def get_extraction_metadata(self) -> AdapterOutputMetadata:
        """
        Return metadata about the most recent extraction operation.

        This metadata includes quality scores, completeness metrics,
        validation errors, and timing information.

        Returns:
            AdapterOutputMetadata for the last extraction
        """
        pass

    @abstractmethod
    def validate_output(self, variables: GeneralizedVariableDict) -> ValidationResult:
        """
        Validate that output conforms to GeneralizedVariableDict schema.

        This method should check:
        - All keys exist in FinancialVariableRegistry
        - Data types match variable definitions
        - Units are correct and normalized
        - Required fields are present
        - Value ranges are reasonable

        Args:
            variables: Dictionary to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        pass

    @abstractmethod
    def get_supported_variable_categories(self) -> List[str]:
        """
        Return list of variable categories this adapter supports.

        Categories can include: 'income_statement', 'balance_sheet',
        'cash_flow', 'market_data', 'ratios', etc.

        Returns:
            List of supported category names
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

    def get_status(self) -> AdapterStatus:
        """Get current adapter status (thread-safe)"""
        with self._lock:
            return self._status

    def set_status(self, status: AdapterStatus) -> None:
        """Set adapter status (thread-safe)"""
        with self._lock:
            self._status = status
            logger.debug(f"{self.get_source_type().value} adapter status: {status.value}")

    def get_adapter_info(self) -> AdapterInfo:
        """Get comprehensive adapter information"""
        capabilities = self.get_capabilities()
        with self._lock:
            return AdapterInfo(
                adapter_type=self.get_source_type().value,
                status=self._status,
                supported_categories=self.get_supported_variable_categories(),
                requires_api_key=capabilities.requires_api_key,
                rate_limit_per_minute=capabilities.rate_limit_per_minute,
                last_request_time=datetime.fromtimestamp(self._stats['last_request_time']) if self._stats['last_request_time'] > 0 else None,
                total_requests=self._stats['requests_made'],
                failed_requests=self._stats['requests_failed']
            )

    def validate_required_fields(self, variables: GeneralizedVariableDict) -> ValidationResult:
        """
        Validate that required fields are present in the output.

        Args:
            variables: Dictionary to validate

        Returns:
            ValidationResult indicating if required fields are present
        """
        result = ValidationResult(valid=True, validation_type="required_fields")

        missing_fields = [
            field for field in REQUIRED_FIELDS
            if field not in variables or variables[field] is None
        ]

        if missing_fields:
            result.valid = False
            for field in missing_fields:
                result.add_error(f"Required field missing: {field}")

        result.details['missing_count'] = len(missing_fields)
        result.details['required_count'] = len(REQUIRED_FIELDS)

        return result

    def validate_data_types(self, variables: GeneralizedVariableDict) -> ValidationResult:
        """
        Validate that variable data types match registry definitions.

        Args:
            variables: Dictionary to validate

        Returns:
            ValidationResult indicating type validation status
        """
        result = ValidationResult(valid=True, validation_type="data_types")

        if not self.variable_registry:
            result.add_warning("Variable registry not available for type validation")
            return result

        type_errors = []

        for var_name, value in variables.items():
            if value is None:
                continue  # None values are acceptable

            var_def = self.variable_registry.get_variable_definition(var_name)
            if not var_def:
                continue  # Skip variables not in registry

            # Check type compatibility
            expected_type = var_def.data_type.value if hasattr(var_def.data_type, 'value') else str(var_def.data_type)
            actual_type = type(value).__name__

            if not self._is_type_compatible(value, expected_type):
                error_msg = f"{var_name}: expected {expected_type}, got {actual_type}"
                type_errors.append(error_msg)
                result.add_error(error_msg)

        result.details['type_errors_count'] = len(type_errors)

        return result

    def _is_type_compatible(self, value: Any, expected_type: str) -> bool:
        """Check if value is compatible with expected type"""
        if expected_type in ('float', 'percentage', 'currency'):
            return isinstance(value, (int, float))
        elif expected_type == 'integer':
            return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
        elif expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'date':
            return isinstance(value, (datetime, str))  # Accept datetime or ISO string
        else:
            return True  # Unknown type, allow it

    def calculate_completeness_score(self, variables: GeneralizedVariableDict) -> float:
        """
        Calculate completeness score for extracted variables.

        Score is based on the percentage of expected fields that are present
        and have non-None values.

        Args:
            variables: Dictionary of extracted variables

        Returns:
            Completeness score between 0.0 and 1.0
        """
        from .types import ALL_OPTIONAL_FIELDS

        # Count non-None values
        present_count = sum(
            1 for field in ALL_OPTIONAL_FIELDS
            if field in variables and variables[field] is not None
        )

        total_count = len(ALL_OPTIONAL_FIELDS)

        return present_count / total_count if total_count > 0 else 0.0

    def generate_composite_variables(
        self,
        variables: GeneralizedVariableDict
    ) -> Dict[str, float]:
        """
        Generate composite/derived variables from base variables.

        This method calculates derived metrics like:
        - Free cash flow (if not already present)
        - Gross profit margin
        - Operating margin
        - Net profit margin
        - EBITDA (if not already present)
        - Current ratio
        - Debt to equity ratio

        Args:
            variables: Base variables dictionary

        Returns:
            Dictionary of composite variables
        """
        composite = {}

        # Free Cash Flow = Operating Cash Flow - Capital Expenditures
        if 'free_cash_flow' not in variables or variables['free_cash_flow'] is None:
            ocf = variables.get('operating_cash_flow')
            capex = variables.get('capital_expenditures')
            if ocf is not None and capex is not None:
                composite['free_cash_flow'] = ocf - abs(capex)

        # Gross Profit = Revenue - Cost of Revenue
        if 'gross_profit' not in variables or variables['gross_profit'] is None:
            revenue = variables.get('revenue')
            cogs = variables.get('cost_of_revenue')
            if revenue is not None and cogs is not None:
                composite['gross_profit'] = revenue - cogs

        # EBITDA = Operating Income + Depreciation & Amortization
        if 'ebitda' not in variables or variables['ebitda'] is None:
            op_income = variables.get('operating_income')
            da = variables.get('depreciation_and_amortization')
            if op_income is not None and da is not None:
                composite['ebitda'] = op_income + da

        # Net Debt = Total Debt - Cash
        total_debt = (variables.get('short_term_debt') or 0) + (variables.get('long_term_debt') or 0)
        cash = variables.get('cash_and_cash_equivalents')
        if total_debt > 0 and cash is not None:
            composite['net_debt'] = total_debt - cash

        # Working Capital = Current Assets - Current Liabilities
        current_assets = variables.get('total_current_assets')
        current_liabilities = variables.get('total_current_liabilities')
        if current_assets is not None and current_liabilities is not None:
            composite['working_capital'] = current_assets - current_liabilities

        logger.debug(f"Generated {len(composite)} composite variables")

        return composite

    def safe_extract_with_lock(
        self,
        symbol: str,
        period: str = "latest",
        historical_years: int = 10
    ) -> GeneralizedVariableDict:
        """
        Thread-safe wrapper for extract_variables.

        Args:
            symbol: Stock symbol
            period: Period identifier
            historical_years: Years of historical data

        Returns:
            GeneralizedVariableDict with extracted variables

        Raises:
            AdapterException: If extraction fails
        """
        with self._lock:
            try:
                self.set_status(AdapterStatus.BUSY)
                start_time = time.time()

                result = self.extract_variables(symbol, period, historical_years)

                # Generate composite variables
                composite_vars = self.generate_composite_variables(result)
                result.update(composite_vars)

                # Calculate metadata
                extraction_time = time.time() - start_time
                completeness = self.calculate_completeness_score(result)

                # Validate output
                validation_result = self.validate_output(result)

                # Store metadata
                self._last_metadata = AdapterOutputMetadata(
                    source=self.get_source_type().value,
                    timestamp=datetime.now(),
                    quality_score=self.calculate_data_quality(result, [], DataCategory.MARKET_DATA).overall_score,
                    completeness=completeness,
                    validation_errors=validation_result.errors,
                    extraction_time=extraction_time,
                    api_calls_made=self._stats['requests_made']
                )

                self.set_status(AdapterStatus.READY)

                return result

            except Exception as e:
                self.set_status(AdapterStatus.ERROR)
                logger.error(f"Extraction failed for {symbol}: {e}")
                raise AdapterException(
                    f"Failed to extract variables for {symbol}",
                    source=self.get_source_type().value,
                    original_exception=e
                )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.get_source_type().value})"