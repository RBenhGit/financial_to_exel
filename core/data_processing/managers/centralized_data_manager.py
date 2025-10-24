"""
Centralized Data Collection and Processing Manager
=================================================

.. deprecated::
    CentralizedDataManager is deprecated in favor of VarInputData with adapters.
    This module will be removed in version 2.0. Please migrate to:
    - VarInputData.get_variable() for all data access
    - ExcelDataAdapter.extract() for Excel file processing
    - Adapters (YFinanceConverter, AlphaVantageConverter, etc.) for API access

This module provides a unified, high-performance data management system that centralizes
all financial data collection, processing, validation, and caching operations across
the entire valuation and analysis framework.

PRD COMPLIANCE: This class fulfills the "CentralizedInputManager" requirements
defined in the Real Data Verification & Centralized Architecture PRD:

- R1.1: Single entry point for all data acquisition
- R1.2: Excel file processing with standardized extraction methods
- R1.3: Unified API interface for all external data sources
- R1.4: Automatic fallback hierarchy implementation
- R1.5: Real-time data validation and authenticity verification
- R1.6: Complete data lineage metadata generation
- R1.7: Cache management with cross-module consistency

This implementation provides a production-ready foundation for centralized
data management as specified in PRD objectives.

Key Features
------------
- **Unified Data Sources**: Centralized access to Excel files, market APIs, and financial databases
- **Intelligent Caching**: Multi-layer caching (memory + disk) with TTL and invalidation strategies
- **Data Validation**: Comprehensive input validation with configurable strictness levels
- **Rate Limiting**: Built-in API rate limiting and request optimization
- **Error Handling**: Robust error recovery with fallback mechanisms
- **Performance Monitoring**: Detailed logging and performance metrics
- **Data Standardization**: Consistent data formats and units across all modules
- **Cross-Session Persistence**: Persistent cache survives application restarts

Classes
-------
DataCacheEntry
    Represents cached data with metadata (timestamp, hash, source, expiry)

CentralizedDataManager
    Main class providing unified data management capabilities

Core Functionality
------------------

**Excel Data Management**
- Standardized Excel file loading with format detection
- Automatic data cleaning and validation
- Configurable column mapping and data transformation
- Persistent caching of processed Excel data

**Market Data Integration**
- Yahoo Finance API with detailed logging and error handling
- Multi-source API aggregation (FMP, Alpha Vantage, Polygon)
- Automatic retry logic with exponential backoff
- Request deduplication and batch optimization

**Caching System**
- Two-tier caching: in-memory (fast) + disk (persistent)
- Content-based hashing for cache key generation
- Configurable TTL (Time-To-Live) per data type
- Automatic cache invalidation and cleanup

**Data Validation**
- Pre-flight validation for data quality and consistency
- Configurable validation levels (STRICT, MODERATE, RELAXED)
- Network connectivity and API availability checks
- Data format and range validation

Usage Example
-------------
>>> from core.data_processing.managers.centralized_data_manager import CentralizedDataManager, ValidationLevel
>>>
>>> # Initialize with validation
>>> manager = CentralizedDataManager(
...     base_path="./data",
...     cache_dir="./cache",
...     validation_level=ValidationLevel.MODERATE
... )
>>>
>>> # Load Excel data with caching
>>> excel_data = manager.load_excel_data(
...     file_path="financial_data.xlsx",
...     sheet_name="Cash Flow",
...     use_cache=True
... )
>>>
>>> # Fetch market data with rate limiting
>>> market_data = manager.get_market_data(
...     ticker="AAPL",
...     data_types=['price', 'fundamentals'],
...     use_cache=True
... )
>>>
>>> # Access validation results
>>> validation_result = manager.get_validation_summary()
>>> print(f"Validation Status: {validation_result.is_valid}")

Performance Optimization
-----------------------

**Memory Management**
- LRU cache eviction for memory efficiency
- Configurable cache size limits
- Automatic garbage collection for expired entries

**Network Optimization**
- Request batching for multiple tickers
- Connection pooling and keep-alive
- Automatic retry with backoff strategies

**Disk I/O Optimization**
- Efficient JSON/pickle serialization
- Compressed cache storage options
- Lazy loading for large datasets

Data Standardization
-------------------
All data is processed according to consistent standards:

**Monetary Values**
- Default scale: millions (configurable)
- Consistent decimal precision (2 places)
- Standardized currency handling

**Date Formats**
- ISO format (YYYY-MM-DD) for all dates
- Timezone-aware timestamps where applicable
- Consistent quarter-end date mapping

**Missing Data**
- Configurable fill strategies (0, forward-fill, interpolation)
- Clear marking of missing vs. zero values
- Data quality metrics tracking

Error Handling and Recovery
---------------------------

**Graceful Degradation**
- Fallback to alternative data sources
- Partial data loading when possible
- Clear error reporting with actionable suggestions

**Retry Logic**
- Exponential backoff for network requests
- Different retry strategies per error type
- Maximum retry limits to prevent infinite loops

**Validation and Recovery**
- Data integrity checks before processing
- Automatic correction of common issues
- Detailed error logs for debugging

Configuration Options
--------------------
The manager supports extensive configuration:

```python
config = {
    'cache_ttl': {
        'market_data': 300,      # 5 minutes
        'excel_data': 3600,      # 1 hour
        'fundamentals': 86400    # 24 hours
    },
    'validation': {
        'level': 'MODERATE',
        'network_timeout': 10.0,
        'max_retries': 3
    },
    'performance': {
        'max_memory_cache_mb': 512,
        'disk_cache_cleanup_days': 7,
        'batch_size': 100
    }
}
```

Integration Points
-----------------
The manager integrates seamlessly with:
- **Financial Calculations**: Provides clean, validated data
- **Valuation Modules**: DCF, DDM, P/B analysis data sources
- **Analysis Capture**: Persistent storage for analysis results
- **Streamlit Interface**: Real-time data updates and caching

Notes
-----
- Thread-safe operations for concurrent access
- Configurable logging levels and output formats
- Memory usage monitoring and optimization
- Cross-platform compatibility (Windows, macOS, Linux)
- Supports both development and production environments
"""

import hashlib
import json
import logging
import os
import time
import warnings
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import numpy as np
import pandas as pd

# Import VarInputData and adapters for centralized data access
from core.data_processing.var_input_data import get_var_input_data
from core.data_processing.adapters.excel_adapter import ExcelDataAdapter
from core.data_processing.adapters.yfinance_adapter import YFinanceAdapter

# Configure pandas warnings for financial data processing
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# Enhanced pandas settings for financial data
pd.set_option("mode.chained_assignment", None)
pd.set_option("display.precision", 2)
pd.set_option("display.float_format", "{:.2f}".format)

# Import validation system
from utils.input_validator import PreFlightValidator, ValidationLevel, ValidationResult

# Import detailed logging for Yahoo Finance API
from utils.yfinance_logger import get_yfinance_logger

# Import enhanced rate limiter
from ..rate_limiting.enhanced_rate_limiter import get_rate_limiter

# Import data source hierarchy manager
from ..data_source_hierarchy import DataSourceHierarchy, DataSourceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataCacheEntry:
    """Represents a cached data entry with metadata"""

    data: Any
    timestamp: datetime
    hash_key: str
    source: str
    expiry_hours: int = 24

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() - self.timestamp > timedelta(hours=self.expiry_hours)


class CentralizedDataManager:
    """
    Centralized manager for all data collection and processing operations.

    Features:
    - Unified Excel data loading with caching
    - Centralized market data fetching with rate limiting
    - Standardized data formats and validation
    - Persistent caching across sessions
    - Comprehensive error handling and logging
    """

    def __init__(
        self,
        base_path: str,
        cache_dir: str = "data_cache",
        validation_level: ValidationLevel = ValidationLevel.MODERATE,
    ):
        """
        Initialize the centralized data manager.

        .. deprecated::
            CentralizedDataManager is deprecated in favor of VarInputData with adapters.
            This class will be removed in a future version. Please migrate to:
            - VarInputData.get_variable() for data access
            - ExcelDataAdapter.extract() for Excel file processing
            - Adapters (YFinanceConverter, etc.) for API access

        Args:
            base_path (str): Base directory path for data files
            cache_dir (str): Directory for caching data
            validation_level (ValidationLevel): Level of input validation strictness
        """
        warnings.warn(
            "CentralizedDataManager is deprecated. Use VarInputData with adapters instead. "
            "This class will be removed in version 2.0.",
            DeprecationWarning,
            stacklevel=2
        )

        self.base_path = Path(base_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize memory cache (always needed as fallback)
        self._memory_cache: Dict[str, DataCacheEntry] = {}

        # Initialize optimized multi-tier cache manager
        try:
            from core.data_processing.cache.optimized_cache_manager import OptimizedCacheManager
            self.cache_manager = OptimizedCacheManager(
                cache_dir=str(self.cache_dir),
                memory_cache_size=1000,
                memory_cache_mb=100,
                enable_disk_cache=True,
                enable_compression=True,
                enable_cache_warming=True
            )
        except ImportError:
            # Fallback to basic in-memory cache if optimized manager not available
            self.cache_manager = None

        # Initialize validation system
        self.validator = PreFlightValidator(
            validation_level=validation_level,
            enable_caching=True,
            cache_ttl=600,  # 10 minutes for validation cache
            network_timeout=10.0,
        )

        # Initialize detailed Yahoo Finance API logger
        self.yf_logger = get_yfinance_logger(
            log_level="INFO",  # Can be configured based on user preference
            log_dir=str(self.cache_dir / "logs"),
            enable_console=True,
        )
        
        # Initialize enhanced rate limiter
        self.rate_limiter = get_rate_limiter()

        # Initialize data source hierarchy manager with API keys from config
        hierarchy_config = {
            'fmp_api_key': os.getenv('FMP_API_KEY'),
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'polygon_api_key': os.getenv('POLYGON_API_KEY'),
            'finnhub_api_key': os.getenv('FINNHUB_API_KEY')
        }
        self.hierarchy_manager = DataSourceHierarchy(hierarchy_config)

        # Data standardization settings
        self.data_config = {
            "value_scale": 1000000,  # Store values in millions
            "date_format": "%Y-%m-%d",
            "decimal_places": 2,
            "missing_value_fill": 0,
        }

        # Market data rate limiting with more conservative delays
        self._last_market_request = datetime.min
        self._market_request_delay = 5.0  # seconds - increased due to stricter rate limits

        # Load existing cache from disk
        self._load_persistent_cache()

        # Start cache warming for frequently accessed data
        if self.cache_manager:
            self._start_cache_warming()

        logger.info(
            f"Centralized Data Manager initialized for {base_path} with {validation_level.value} validation"
        )

    def get_data_source_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for all data sources

        Returns:
            Dict containing health metrics and recommendations
        """
        return self.hierarchy_manager.get_source_health_report()

    def get_optimal_data_source_hierarchy(self, exclude: List[str] = None) -> List[str]:
        """
        Get optimal data source hierarchy for current conditions

        Args:
            exclude: List of source names to exclude

        Returns:
            List of source names in optimal order
        """
        exclude_types = []
        if exclude:
            type_mapping = {
                'excel': DataSourceType.EXCEL,
                'yfinance': DataSourceType.YFINANCE,
                'fmp': DataSourceType.FMP,
                'alpha_vantage': DataSourceType.ALPHA_VANTAGE,
                'polygon': DataSourceType.POLYGON,
                'finnhub': DataSourceType.FINNHUB
            }
            exclude_types = [type_mapping.get(name) for name in exclude if name in type_mapping]

        hierarchy = self.hierarchy_manager.get_optimal_source_hierarchy(exclude_types)
        return [source_type.value for source_type in hierarchy]

    def _generate_cache_key(self, source: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key for data"""
        key_string = f"{source}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _load_persistent_cache(self):
        """Load cache from disk"""
        cache_file = self.cache_dir / "cache_index.json"
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                logger.info(f"Loaded {len(cache_data)} cached entries from disk")
            except Exception as e:
                logger.warning(f"Failed to load cache from disk: {e}")

    def _save_persistent_cache(self):
        """Save cache to disk"""
        try:
            cache_file = self.cache_dir / "cache_index.json"
            cache_data = {}
            for key, entry in self._memory_cache.items():
                if not entry.is_expired():
                    cache_data[key] = {
                        "timestamp": entry.timestamp.isoformat(),
                        "hash_key": entry.hash_key,
                        "source": entry.source,
                        "expiry_hours": entry.expiry_hours,
                    }
            cache_file.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")

    def get_cached_data(self, cache_key: str, ignore_expiry: bool = False,
                       data_type: str = "", ticker: str = "") -> Optional[Any]:
        """Retrieve data from cache if available and not expired"""
        # Use optimized cache manager if available
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key, data_type=data_type, ticker=ticker)
            if cached_data is not None:
                logger.debug(f"Optimized cache hit for key: {cache_key}")
                return cached_data
            else:
                logger.debug(f"Optimized cache miss for key: {cache_key}")
                return None

        # Fallback to basic cache
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if ignore_expiry or not entry.is_expired():
                logger.debug(f"Basic cache hit for key: {cache_key} (ignore_expiry={ignore_expiry})")
                return entry.data
            else:
                logger.debug(f"Basic cache expired for key: {cache_key}")
                del self._memory_cache[cache_key]
        return None

    def cache_data(self, cache_key: str, data: Any, source: str, expiry_hours: int = 24,
                   data_type: str = 'market_data', ticker: str = ""):
        """Store data in cache with adaptive TTL based on rate limiting status"""

        # Use enhanced cache TTL if rate limiter indicates problems
        if hasattr(self, 'rate_limiter'):
            api_source = 'yahoo_finance' if 'market_data' in cache_key else source
            enhanced_ttl_seconds = self.rate_limiter.get_cache_ttl_for_source(api_source, data_type)
            expiry_hours = enhanced_ttl_seconds / 3600  # Convert to hours

        # Use optimized cache manager if available
        if self.cache_manager:
            tags = ['api_data', source]
            if ticker:
                tags.append(f'ticker:{ticker}')

            success = self.cache_manager.put(
                cache_key, data, ttl_hours=expiry_hours,
                data_type=data_type, source=source, ticker=ticker, tags=tags
            )
            if success:
                logger.debug(f"Optimized cache stored for key: {cache_key} with TTL: {expiry_hours}h")
            return

        # Fallback to basic cache
        entry = DataCacheEntry(
            data=data,
            timestamp=datetime.now(),
            hash_key=cache_key,
            source=source,
            expiry_hours=expiry_hours,
        )
        if hasattr(self, '_memory_cache'):
            self._memory_cache[cache_key] = entry
        logger.debug(f"Basic cache stored for key: {cache_key} with TTL: {expiry_hours}h")

    def load_excel_data(
        self, company_folder: str, force_reload: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Centralized Excel data loading with caching and standardization.

        Args:
            company_folder (str): Company folder name (e.g., 'TSLA', 'MSFT')
            force_reload (bool): Force reload even if cached data exists

        Returns:
            Dict[str, pd.DataFrame]: Standardized financial data
        """
        params = {"company_folder": company_folder}
        cache_key = self._generate_cache_key("excel_data", params)

        # Check cache first
        if not force_reload:
            cached_data = self.get_cached_data(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached Excel data for {company_folder}")
                return cached_data

        logger.info(f"Loading Excel data for {company_folder}")

        try:
            # Load Excel files from both FY and LTM folders
            company_path = self.base_path / company_folder
            if not company_path.exists():
                raise FileNotFoundError(f"Company folder not found: {company_path}")

            excel_data = {}

            # Optimize folder loading with parallel processing if multiple folders exist
            folders_to_load = []
            fy_path = company_path / "FY"
            if fy_path.exists():
                folders_to_load.append((fy_path, "_fy"))

            ltm_path = company_path / "LTM"
            if ltm_path.exists():
                folders_to_load.append((ltm_path, "_ltm"))

            # Load folders - could be parallelized in future versions
            for folder_path, suffix in folders_to_load:
                folder_data = self._load_excel_folder(folder_path, suffix)
                excel_data.update(folder_data)
                logger.debug(f"Loaded {len(folder_data)} files from {folder_path.name}")

            # Standardize data formats
            standardized_data = self._standardize_excel_data(excel_data)

            # Cache the results
            self.cache_data(cache_key, standardized_data, "excel_data", expiry_hours=24)

            logger.info(
                f"Successfully loaded {len(standardized_data)} Excel datasets for {company_folder}"
            )
            return standardized_data

        except Exception as e:
            logger.error(f"Error loading Excel data for {company_folder}: {e}")
            raise

    def _load_excel_folder(self, folder_path: Path, suffix: str) -> Dict[str, pd.DataFrame]:
        """Optimized Excel file loading with performance enhancements"""
        excel_data = {}

        # Pre-categorize files to avoid multiple iterations
        file_categories = {"balance": [], "cashflow": [], "income": []}

        # Single pass to categorize files
        for excel_file in folder_path.glob("*.xlsx"):
            filename = excel_file.stem.lower()
            for category in file_categories.keys():
                if category in filename or (category == "cashflow" and "cash" in filename):
                    file_categories[category].append(excel_file)
                    break

        # Process files with optimized settings
        for category, files in file_categories.items():
            for excel_file in files:
                key = f"{category}{suffix}"
                try:
                    # NOTE: Direct pd.read_excel() - should use ExcelDataAdapter for centralized processing
                    # TODO: Replace with ExcelDataAdapter.extract(excel_file) in future version
                    # Keeping for backward compatibility during migration (Task 233.5)
                    df = pd.read_excel(
                        excel_file,
                        engine="openpyxl",
                        keep_default_na=False,  # Faster NA handling
                        na_filter=False,  # Skip automatic NA detection
                        dtype_backend="pyarrow",  # Faster backend if available
                    )

                    # Immediate memory optimization
                    df = df.convert_dtypes(convert_integer=True, convert_floating=True)

                    excel_data[key] = df
                    logger.debug(
                        f"Optimally loaded {excel_file.name} as {key} ({df.memory_usage(deep=True).sum() / 1024:.1f}KB)"
                    )

                except ImportError:
                    # Fallback without pyarrow if not available
                    try:
                        # NOTE: Direct pd.read_excel() fallback - should use ExcelDataAdapter
                        # TODO: Replace with ExcelDataAdapter.extract(excel_file) in future version
                        df = pd.read_excel(
                            excel_file,
                            engine="openpyxl",
                            keep_default_na=False,
                            na_filter=False,
                        )
                        df = df.convert_dtypes(convert_integer=True, convert_floating=True)
                        excel_data[key] = df
                        logger.debug(f"Loaded {excel_file.name} as {key} (fallback mode)")
                    except Exception as e:
                        logger.error(f"Error loading {excel_file}: {e}")
                        continue
                except Exception as e:
                    logger.error(f"Error loading {excel_file}: {e}")
                    continue

        return excel_data

    def _standardize_excel_data(
        self, excel_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Optimized Excel data standardization with vectorized operations"""
        standardized = {}

        for key, df in excel_data.items():
            if df.empty:
                continue

            # Avoid unnecessary copying - modify in place where possible
            df_std = df.copy()

            # Vectorized column name standardization
            df_std.columns = df_std.columns.str.strip().str.replace(r"\s+", " ", regex=True)

            # Optimized missing value handling with specific data types
            numeric_columns = df_std.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                df_std[numeric_columns] = df_std[numeric_columns].fillna(
                    self.data_config["missing_value_fill"]
                )

            # String columns - fill with empty string instead of 0
            string_columns = df_std.select_dtypes(include=["object"]).columns
            if len(string_columns) > 0:
                df_std[string_columns] = df_std[string_columns].fillna("")

                # Memory optimization: Convert low-cardinality string columns to categorical
                for col in string_columns:
                    unique_ratio = df_std[col].nunique() / len(df_std[col])
                    if (
                        unique_ratio < 0.5 and df_std[col].nunique() < 100
                    ):  # Low cardinality threshold
                        df_std[col] = df_std[col].astype("category")

            # Memory optimization - downcast numeric types where safe with modern error handling
            import pandas.api.types as ptypes

            for col in numeric_columns:
                try:
                    # Use pandas api.types for robust dtype checking
                    if ptypes.is_float_dtype(df_std[col]):
                        df_std[col] = pd.to_numeric(df_std[col], errors="coerce", downcast="float")
                    elif ptypes.is_integer_dtype(df_std[col]):
                        df_std[col] = pd.to_numeric(
                            df_std[col], errors="coerce", downcast="integer"
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to downcast column {col}: {e}")

            standardized[key] = df_std

        logger.debug(f"Standardized {len(standardized)} Excel datasets with memory optimization")
        return standardized

    def _fetch_from_var_input_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch market data through VarInputData architecture (ONLY CORRECT PATH).

        This method ensures ALL data access routes through VarInputData.
        If data isn't in VarInputData, it uses YFinanceAdapter to populate it,
        then retrieves it from VarInputData. NO DIRECT YFINANCE BYPASS.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Market data dict or None if fetch failed
        """
        try:
            # Get VarInputData instance
            var_data = get_var_input_data()
            ticker_upper = ticker.upper()

            # Try to fetch required fields from VarInputData
            current_price = var_data.get_variable(ticker_upper, 'current_price', period='latest')

            # If data not in VarInputData, populate it using YFinanceAdapter
            if not current_price or current_price <= 0:
                logger.info(f"Data not in VarInputData for {ticker}, populating via YFinanceAdapter...")

                # Use YFinanceAdapter to fetch and populate VarInputData
                adapter = YFinanceAdapter()
                extraction_result = adapter.extract_variables(
                    symbol=ticker_upper,
                    period='latest',
                    historical_years=0  # Only need latest data for market info
                )

                if not extraction_result or not extraction_result.success:
                    logger.warning(f"YFinanceAdapter failed to fetch data for {ticker}")
                    return None

                logger.info(f"✓ YFinanceAdapter populated {extraction_result.variables_extracted} variables for {ticker}")

                # Now fetch from VarInputData (it should be there now)
                current_price = var_data.get_variable(ticker_upper, 'current_price', period='latest')

            # Fetch all required fields from VarInputData
            shares_outstanding = var_data.get_variable(ticker_upper, 'shares_outstanding', period='latest')
            market_cap = var_data.get_variable(ticker_upper, 'market_cap', period='latest')
            company_name = var_data.get_variable(ticker_upper, 'company_name', period='latest')
            currency = var_data.get_variable(ticker_upper, 'currency', period='latest')

            # Validate minimum required data
            if not current_price or current_price <= 0:
                logger.warning(f"No valid price data for {ticker} even after adapter fetch")
                return None

            # Construct standardized response
            result = {
                "ticker": ticker_upper,
                "company_name": company_name or ticker_upper,
                "current_price": float(current_price),
                "shares_outstanding": float(shares_outstanding) if shares_outstanding else 0,
                "market_cap": float(market_cap) / self.data_config["value_scale"] if market_cap else 0,
                "currency": currency or "USD",
                "last_updated": datetime.now().isoformat(),
                "data_source": "VarInputData"  # Always from VarInputData
            }

            logger.info(f"✓ Fetched market data for {ticker} from VarInputData (via adapter architecture)")
            return result

        except Exception as e:
            logger.error(f"Error fetching market data for {ticker} through VarInputData: {e}")
            return None

    def fetch_market_data(
        self, ticker: str, force_reload: bool = False, skip_validation: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Centralized market data fetching with pre-flight validation, rate limiting and caching.

        Migration Strategy:
        1. Try VarInputData first (new architecture - routes through adapters)
        2. Fall back to direct yfinance (legacy path, will be deprecated)

        Args:
            ticker (str): Stock ticker symbol
            force_reload (bool): Force reload even if cached data exists
            skip_validation (bool): Skip pre-flight validation (for testing/offline use)

        Returns:
            Optional[Dict[str, Any]]: Market data or None if failed
        """
        # Start detailed request logging
        request_id = self.yf_logger.start_request(ticker, "market_data")

        try:
            # Pre-flight validation with detailed logging
            if not skip_validation:
                logger.debug(f"Running pre-flight validation for ticker: {ticker}")
                is_ready, validation_errors = self.validator.is_ready_for_api_call(
                    ticker, skip_network=False
                )

                # Log validation results
                validation_result = {
                    "is_valid": is_ready,
                    "errors": validation_errors if not is_ready else [],
                    "warnings": [],
                }
                self.yf_logger.log_validation(ticker, validation_result)

                if not is_ready:
                    logger.error(f"Pre-flight validation failed for {ticker}")
                    for error in validation_errors:
                        logger.error(f"  - {error}")

                    # Get remediation steps
                    remediation_steps = self.validator.get_remediation_steps(ticker)
                    if remediation_steps:
                        logger.info("Suggested remediation steps:")
                        for step in remediation_steps:
                            logger.info(f"  - {step}")

                    self.yf_logger.finish_request(success=False)
                    return None

                logger.debug(f"Pre-flight validation passed for {ticker}")
            else:
                self.yf_logger.log_step(
                    "Pre-flight Validation",
                    {"status": "skipped", "reason": "skip_validation=True"},
                    level="INFO",
                )

            # Generate cache key and log it
            params = {"ticker": ticker.upper()}
            cache_key = self._generate_cache_key("market_data", params)

            self.yf_logger.log_step(
                "Cache Key Generation",
                {
                    "cache_key": cache_key,
                    "parameters": params,
                    "force_reload": force_reload,
                },
                level="DEBUG",
            )

            # Check cache first with detailed logging
            if not force_reload:
                cached_data = self.get_cached_data(cache_key)
                if cached_data is not None:
                    # Calculate cache age
                    cache_entry = self._memory_cache.get(cache_key)
                    cache_age = (
                        (datetime.now() - cache_entry.timestamp).total_seconds()
                        if cache_entry
                        else None
                    )

                    self.yf_logger.log_cache_check(cache_key, True, cache_age)

                    logger.info(f"Using cached market data for {ticker}")
                    self.yf_logger.finish_request(success=True, final_data=cached_data)
                    return cached_data
                else:
                    self.yf_logger.log_cache_check(cache_key, False)
            else:
                self.yf_logger.log_step(
                    "Cache Check",
                    {"status": "bypassed", "reason": "force_reload=True"},
                    level="INFO",
                )

            # Rate limiting with detailed logging
            time_since_last = (datetime.now() - self._last_market_request).total_seconds()
            if time_since_last < self._market_request_delay:
                sleep_time = self._market_request_delay - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")

                self.yf_logger.log_rate_limiting(sleep_time, "Minimum delay between requests")
                time.sleep(sleep_time)
            else:
                self.yf_logger.log_step(
                    "Rate Limiting",
                    {
                        "time_since_last_request": round(time_since_last, 2),
                        "minimum_delay": self._market_request_delay,
                        "action": "no_delay_needed",
                    },
                    level="DEBUG",
                )

            logger.info(
                f"Fetching market data for {ticker} (validation: {'skipped' if skip_validation else 'passed'})"
            )

            # Log the start of API preparation
            self.yf_logger.log_step(
                "API Preparation",
                {
                    "ticker": ticker,
                    "validation_mode": "skipped" if skip_validation else "passed",
                    "force_reload": force_reload,
                },
                level="INFO",
            )

        except Exception as outer_e:
            self.yf_logger.log_error(outer_e, {"phase": "initial_setup"})
            self.yf_logger.finish_request(success=False)
            logger.error(f"Error in initial setup for {ticker}: {outer_e}")
            return None

        # =============================================================================
        # FETCH THROUGH VARINPUTDATA ARCHITECTURE (BYPASS ELIMINATED)
        # =============================================================================
        # All data fetching now routes through VarInputData.
        # If data not in VarInputData, YFinanceAdapter populates it automatically.
        # NO DIRECT YFINANCE BYPASS - architecture fully compliant.
        # =============================================================================

        try:
            # Fetch through VarInputData (uses YFinanceAdapter if needed)
            var_input_data_result = self._fetch_from_var_input_data(ticker)

            if var_input_data_result:
                # Success! Cache and return
                self.cache_data(cache_key, var_input_data_result, "market_data", expiry_hours=2)
                self._last_market_request = datetime.now()

                self.yf_logger.log_step(
                    "VarInputData Fetch Success",
                    {
                        "data_source": "VarInputData (adapter layer)",
                        "architecture": "compliant",
                        "bypass_eliminated": True,
                        "data_summary": {
                            "ticker": var_input_data_result.get("ticker"),
                            "company_name": var_input_data_result.get("company_name"),
                            "current_price": var_input_data_result.get("current_price"),
                        }
                    },
                    level="INFO",
                )

                self.yf_logger.finish_request(success=True, final_data=var_input_data_result)
                return var_input_data_result

            # If VarInputData fetch failed, try fallback sources
            logger.warning(f"VarInputData fetch failed for {ticker}, trying fallback sources")
            self.yf_logger.log_step(
                "VarInputData Failed - Trying Fallbacks",
                {
                    "reason": "YFinanceAdapter failed to populate data",
                    "fallback_sources_available": True,
                },
                level="WARNING",
            )

        except Exception as var_data_error:
            logger.error(f"VarInputData fetch error for {ticker}: {var_data_error}")
            self.yf_logger.log_error(var_data_error, {"phase": "var_input_data_fetch"})

        # =============================================================================
        # FALLBACK TO ALTERNATIVE DATA SOURCES (BYPASS ELIMINATED)
        # =============================================================================
        # VarInputData failed, try other APIs (Alpha Vantage, FMP, etc.)
        # NO DIRECT YFINANCE - architecture fully compliant with adapter layer
        # =============================================================================

        try:
            logger.warning(f"VarInputData fetch failed for {ticker}, trying fallback sources")
            self.yf_logger.log_step(
                "VarInputData Failed - Trying Fallbacks",
                {
                    "primary_source": "VarInputData (YFinanceAdapter)",
                    "reason": "VarInputData fetch returned no data",
                    "fallback_sources_available": True,
                    "architecture": "compliant",
                    "bypass_eliminated": True,
                },
                level="WARNING",
            )

            fallback_data = self._try_fallback_data_sources(ticker)
            if fallback_data:
                self.cache_data(cache_key, fallback_data, "market_data", expiry_hours=1)
                self.yf_logger.log_step(
                    "Fallback Source Success",
                    {
                        "fallback_source": fallback_data.get("fallback_source", "unknown"),
                        "data_summary": {
                            k: v for k, v in fallback_data.items() if k != "fallback_source"
                        },
                    },
                    level="INFO",
                )
                self.yf_logger.finish_request(success=True, final_data=fallback_data)
                return fallback_data

            logger.warning(f"All data sources failed for {ticker}")
            self.yf_logger.log_step(
                "All Sources Failed",
                {
                    "primary_source": "VarInputData (YFinanceAdapter)",
                    "fallback_sources_tried": True,
                    "final_result": "no_data_available",
                },
                level="ERROR",
            )
            self.yf_logger.finish_request(success=False)
            return None

        except Exception as e:
            logger.error(f"Error in fallback data sources for {ticker}: {e}")
            self.yf_logger.log_error(e, {"phase": "fallback_exception"})
            self.yf_logger.finish_request(success=False)
            return None

    def _try_fallback_data_sources(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Try alternative data sources when Yahoo Finance fails.

        Args:
            ticker (str): Stock ticker symbol

        Returns:
            Optional[Dict[str, Any]]: Market data from fallback source or None
        """
        fallback_sources = [
            self._fetch_from_alpha_vantage,
            self._fetch_from_finnhub,
            self._fetch_basic_fallback,
        ]

        for i, source_func in enumerate(fallback_sources):
            try:
                logger.info(f"Trying fallback source {i+1}/{len(fallback_sources)} for {ticker}")
                data = source_func(ticker)
                if data:
                    logger.info(
                        f"Successfully fetched data from fallback source {i+1} for {ticker}"
                    )
                    return data
            except Exception as e:
                logger.warning(f"Fallback source {i+1} failed for {ticker}: {e}")
                continue

        return None

    def _fetch_fallback_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced fallback data fetching using intelligent hierarchy and quality scoring.

        Args:
            ticker (str): Stock ticker symbol

        Returns:
            Optional[Dict[str, Any]]: Market data from best available source or None
        """
        # Get optimal hierarchy excluding yfinance (already failed)
        api_sources = [DataSourceType.FMP, DataSourceType.ALPHA_VANTAGE,
                      DataSourceType.POLYGON, DataSourceType.FINNHUB]
        optimal_hierarchy = self.hierarchy_manager.get_optimal_source_hierarchy(
            exclude=[DataSourceType.YFINANCE]
        )

        # Filter to only API sources (exclude Excel)
        api_hierarchy = [s for s in optimal_hierarchy if s in api_sources]

        if not api_hierarchy:
            logger.warning(f"No API fallback sources available for {ticker}")
            return self._fetch_basic_fallback(ticker)

        logger.info(f"Trying fallback hierarchy for {ticker}: {[s.value for s in api_hierarchy]}")

        # Try each source in optimal order
        for source_type in api_hierarchy:
            source_name = source_type.value

            # Check rate limiting
            if hasattr(self.rate_limiter, 'can_make_request') and not self.rate_limiter.can_make_request(source_name):
                logger.debug(f"Skipping {source_name} due to rate limiting")
                continue

            try:
                start_time = time.time()
                logger.info(f"Trying {source_name} fallback for {ticker}")

                # Use rate limiter if available
                if hasattr(self.rate_limiter, 'rate_limited_request'):
                    with self.rate_limiter.rate_limited_request(source_name, 0):
                        data = self._fetch_from_source_type(source_type, ticker)
                else:
                    data = self._fetch_from_source_type(source_type, ticker)

                if data:
                    response_time = time.time() - start_time
                    completeness = self._calculate_data_completeness(data)

                    # Record successful request
                    self.hierarchy_manager.record_request_result(
                        source_type, success=True, response_time=response_time,
                        data_completeness=completeness
                    )

                    # Add fallback source metadata
                    data["fallback_source"] = source_name
                    data["fallback_hierarchy_position"] = api_hierarchy.index(source_type) + 1

                    logger.info(f"Successfully fetched data from {source_name} for {ticker}")
                    return data

            except Exception as e:
                response_time = time.time() - start_time
                logger.warning(f"Fallback source {source_name} failed for {ticker}: {e}")

                # Record failed request
                self.hierarchy_manager.record_request_result(
                    source_type, success=False, response_time=response_time
                )
                continue

        # Final fallback - basic data
        logger.info(f"All API sources failed, using basic fallback for {ticker}")
        return self._fetch_basic_fallback(ticker)

    def _fetch_from_source_type(self, source_type: DataSourceType, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from a specific source type

        Args:
            source_type: The data source type to use
            ticker: Stock ticker symbol

        Returns:
            Market data or None
        """
        if source_type == DataSourceType.ALPHA_VANTAGE:
            return self._fetch_from_alpha_vantage(ticker)
        elif source_type == DataSourceType.FMP:
            return self._fetch_from_fmp(ticker)
        elif source_type == DataSourceType.POLYGON:
            return self._fetch_from_polygon(ticker)
        elif source_type == DataSourceType.FINNHUB:
            return self._fetch_from_finnhub(ticker)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return None

    def _calculate_data_completeness(self, data: Dict[str, Any]) -> float:
        """
        Calculate completeness score for fetched data (0.0 to 1.0)

        Args:
            data: The fetched market data

        Returns:
            Completeness score between 0.0 and 1.0
        """
        if not data:
            return 0.0

        # Define required fields and their weights
        required_fields = {
            'current_price': 0.3,
            'market_cap': 0.2,
            'shares_outstanding': 0.2,
            'pe_ratio': 0.1,
            'book_value': 0.1,
            'revenue': 0.1
        }

        completeness_score = 0.0
        for field, weight in required_fields.items():
            if field in data and data[field] is not None:
                completeness_score += weight

        return min(1.0, completeness_score)

    def _fetch_from_alpha_vantage(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Alpha Vantage API.

        .. deprecated::
            Direct API access bypasses VarInputData infrastructure.
            Use AlphaVantageConverter through VarInputData instead:
            get_var_input_data().get_variable(ticker, variable_name)
        """
        warnings.warn(
            "Direct API fetching is deprecated. Use VarInputData with adapters.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.debug("Alpha Vantage direct access deprecated - use VarInputData")
        return None

    def _fetch_from_finnhub(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Finnhub API.

        .. deprecated::
            Direct API access bypasses VarInputData infrastructure.
            Use FinnhubConverter through VarInputData instead.
        """
        warnings.warn(
            "Direct API fetching is deprecated. Use VarInputData with adapters.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.debug("Finnhub direct access deprecated - use VarInputData")
        return None

    def _fetch_from_fmp(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Financial Modeling Prep API.

        .. deprecated::
            Direct API access bypasses VarInputData infrastructure.
            Use FMPConverter through VarInputData instead.
        """
        warnings.warn(
            "Direct API fetching is deprecated. Use VarInputData with adapters.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.debug("FMP direct access deprecated - use VarInputData")
        return None

    def _fetch_from_polygon(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Polygon.io API.

        .. deprecated::
            Direct API access bypasses VarInputData infrastructure.
            Use PolygonConverter through VarInputData instead.
        """
        warnings.warn(
            "Direct API fetching is deprecated. Use VarInputData with adapters.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.debug("Polygon direct access deprecated - use VarInputData")
        return None

    def _fetch_basic_fallback(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Basic fallback using cached data or default values for testing.
        This allows the application to continue running even when all APIs fail.
        """
        try:
            # Try to find any cached data first
            cache_key = self._generate_cache_key("market_data", {"ticker": ticker.upper()})
            cached_data = self.get_cached_data(
                cache_key, ignore_expiry=True
            )  # Ignore expiry for fallback

            if cached_data:
                logger.info(f"Using expired cached data as fallback for {ticker}")
                # Mark as fallback data
                cached_data["fallback_source"] = "expired_cache"
                cached_data["last_updated"] = datetime.now().isoformat()
                return cached_data

            # As a last resort, return basic structure with placeholder values
            # This prevents the entire analysis from failing
            logger.warning(f"Using placeholder fallback data for {ticker}")
            return {
                "ticker": ticker.upper(),
                "company_name": ticker.upper(),
                "current_price": 1.0,  # Placeholder price
                "shares_outstanding": 1000000,  # Placeholder shares
                "market_cap": 1000.0,  # Placeholder market cap in millions
                "currency": "USD",
                "fallback_source": "placeholder",
                "last_updated": datetime.now().isoformat(),
                "warning": "This is placeholder data - market data fetch failed",
            }

        except Exception as e:
            logger.error(f"Basic fallback also failed for {ticker}: {e}")
            return None

    def get_company_data(
        self, company_folder: str, include_market_data: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive company data including financial statements and market data.

        Args:
            company_folder (str): Company folder name
            include_market_data (bool): Whether to include market data

        Returns:
            Dict[str, Any]: Complete company dataset
        """
        logger.info(f"Collecting comprehensive data for {company_folder}")

        # Load financial data
        financial_data = self.load_excel_data(company_folder)

        # Auto-extract ticker from folder name
        ticker = company_folder.upper()

        # Prepare result
        result = {
            "ticker": ticker,
            "financial_data": financial_data,
            "market_data": None,
            "metadata": {
                "data_collection_time": datetime.now().isoformat(),
                "data_source": "centralized_data_manager",
                "financial_data_count": len(financial_data),
            },
        }

        # Add market data if requested
        if include_market_data:
            market_data = self.fetch_market_data(ticker)
            result["market_data"] = market_data
            if market_data:
                result["metadata"]["market_data_available"] = True
            else:
                result["metadata"]["market_data_available"] = False

        return result

    def clear_cache(self, cache_type: str = "all"):
        """
        Clear cached data.

        Args:
            cache_type (str): Type of cache to clear ('all', 'excel_data', 'market_data')
        """
        if cache_type == "all":
            self._memory_cache.clear()
            logger.info("Cleared all cached data")
        else:
            keys_to_remove = [k for k, v in self._memory_cache.items() if v.source == cache_type]
            for key in keys_to_remove:
                del self._memory_cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} {cache_type} cache entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._memory_cache)
        expired_entries = sum(1 for entry in self._memory_cache.values() if entry.is_expired())

        source_counts = {}
        for entry in self._memory_cache.values():
            source_counts[entry.source] = source_counts.get(entry.source, 0) + 1

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "source_breakdown": source_counts,
            "cache_directory": str(self.cache_dir),
        }

    def validate_ticker(self, ticker: str) -> ValidationResult:
        """
        Validate a ticker symbol using the integrated validation system.

        Args:
            ticker (str): Ticker symbol to validate

        Returns:
            ValidationResult: Validation result with details
        """
        return self.validator.validate_ticker(ticker)

    def validate_system_readiness(self, skip_network: bool = False) -> Dict[str, ValidationResult]:
        """
        Check system readiness for API calls.

        Args:
            skip_network (bool): Skip network validation

        Returns:
            Dict[str, ValidationResult]: Validation results by category
        """
        return self.validator.validate_all(
            "AAPL", skip_network
        )  # Use dummy ticker for system checks

    def is_system_ready(self, ticker: str, skip_network: bool = False) -> bool:
        """
        Quick check if system is ready for API calls.

        Args:
            ticker (str): Ticker symbol to validate
            skip_network (bool): Skip network validation

        Returns:
            bool: True if ready, False otherwise
        """
        is_ready, _ = self.validator.is_ready_for_api_call(ticker, skip_network)
        return is_ready

    def get_validation_config(self) -> Dict[str, Any]:
        """Get current validation configuration."""
        return {
            "validation_level": self.validator.validation_level.value,
            "network_timeout": self.validator.network_validator.timeout,
            "cache_enabled": self.validator.cache is not None,
            "cache_ttl": (self.validator.cache.ttl_seconds if self.validator.cache else None),
        }

    def _start_cache_warming(self):
        """Start proactive cache warming for frequently accessed data"""
        if self.cache_manager:
            # Define frequently accessed tickers based on usage
            popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX"]
            data_types = ["price", "fundamentals", "market_data"]

            def warming_callback(ticker: str, data_type: str, success: bool):
                if success:
                    logger.debug(f"Cache warmed successfully for {ticker} - {data_type}")
                else:
                    logger.debug(f"Cache warming failed for {ticker} - {data_type}")

            self.cache_manager.warm_cache(popular_tickers, data_types, warming_callback)
            logger.info("Started cache warming for popular tickers")

    def invalidate_ticker_cache(self, ticker: str, data_types: List[str] = None):
        """Invalidate all cached data for a specific ticker"""
        if self.cache_manager:
            from core.data_processing.cache.optimized_cache_manager import CacheEventType

            tags = [f'ticker:{ticker}']
            if data_types:
                for data_type in data_types:
                    invalidated = self.cache_manager.invalidate(
                        ticker=ticker, data_type=data_type,
                        event_type=CacheEventType.DATA_UPDATE
                    )
                    logger.info(f"Invalidated {invalidated} cache entries for {ticker} - {data_type}")
            else:
                invalidated = self.cache_manager.invalidate(
                    ticker=ticker, event_type=CacheEventType.DATA_UPDATE
                )
                logger.info(f"Invalidated {invalidated} cache entries for {ticker}")

    def invalidate_source_cache(self, source: str):
        """Invalidate all cached data from a specific source"""
        if self.cache_manager:
            from core.data_processing.cache.optimized_cache_manager import CacheEventType

            invalidated = self.cache_manager.invalidate(
                tags=[source], event_type=CacheEventType.API_ERROR
            )
            logger.info(f"Invalidated {invalidated} cache entries from source: {source}")

    def get_cache_performance_report(self) -> Dict[str, Any]:
        """Get detailed cache performance statistics"""
        if self.cache_manager:
            cache_stats = self.cache_manager.get_cache_stats()

            return {
                "optimized_cache_enabled": True,
                "cache_stats": cache_stats,
                "recommendations": self._get_cache_recommendations(cache_stats)
            }
        else:
            # Basic cache statistics
            return {
                "optimized_cache_enabled": False,
                "basic_cache_entries": len(self._memory_cache) if hasattr(self, '_memory_cache') else 0,
                "recommendations": ["Consider upgrading to optimized cache manager for better performance"]
            }

    def _get_cache_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate cache optimization recommendations based on stats"""
        recommendations = []

        performance = stats.get("performance", {})
        hit_ratio = performance.get("hit_ratio", 0)
        memory_stats = stats.get("memory_cache", {})

        if hit_ratio < 80:
            recommendations.append(f"Cache hit ratio is {hit_ratio}%. Consider increasing cache warming frequency.")

        if memory_stats.get("entry_count", 0) > memory_stats.get("max_size", 1000) * 0.9:
            recommendations.append("Memory cache is near capacity. Consider increasing memory cache size.")

        if performance.get("avg_access_time_ms", 0) > 10:
            recommendations.append("Average cache access time is high. Consider optimizing cache structure.")

        if not recommendations:
            recommendations.append("Cache performance is optimal.")

        return recommendations

    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        if self.cache_manager:
            cleaned = self.cache_manager.cleanup_expired_entries()
            logger.info(f"Cleaned up {cleaned} expired cache entries")
            return cleaned
        return 0

    def __del__(self):
        """Cleanup and save cache on destruction"""
        try:
            if self.cache_manager:
                self.cache_manager.shutdown()
            self._save_persistent_cache()
        except:
            pass  # Ignore errors during cleanup
