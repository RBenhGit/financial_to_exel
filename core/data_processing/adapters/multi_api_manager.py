"""
Multi-API Manager with Intelligent Fallback System
==================================================

Orchestrates multiple financial data API adapters with intelligent fallback logic,
data quality scoring, and optimized source selection. This system provides a unified
interface to all financial data sources while ensuring maximum data availability
and quality through smart adapter management.

Key Features:
-------------
- **Intelligent Source Selection**: Automatically selects the best data source based on quality, cost, and availability
- **Automatic Fallback**: Seamlessly falls back to alternative sources when primary sources fail
- **Data Quality Scoring**: Assesses and compares data quality across all sources in real-time
- **Performance Optimization**: Caches results and optimizes API usage to minimize costs and latency
- **Rate Limit Management**: Intelligently manages rate limits across all APIs to prevent blocking
- **Cost Optimization**: Considers API costs and usage quotas in source selection decisions
- **Comprehensive Monitoring**: Tracks performance, reliability, and costs across all data sources
- **Configuration-Driven**: Flexible configuration for fallback hierarchies and quality thresholds

Fallback Hierarchy (Default):
-----------------------------
1. **yfinance** (Primary) - Free, comprehensive, good quality
2. **FMP** (Secondary) - Professional grade, excellent quality, paid
3. **Alpha Vantage** (Tertiary) - Good quality, free tier available
4. **Polygon** (Premium) - Institutional grade, high cost, excellent quality

Usage Example:
--------------
>>> from multi_api_manager import MultiApiManager
>>> from var_input_data import get_var_input_data
>>> 
>>> # Initialize with default configuration
>>> manager = MultiApiManager()
>>> 
>>> # Load data with automatic source selection and fallback
>>> result = manager.load_symbol_data("AAPL")
>>> print(f"Best source: {result.primary_source}")
>>> print(f"Fallback used: {result.fallback_sources}")
>>> print(f"Overall quality: {result.overall_quality:.2f}")
>>> 
>>> # Access unified data
>>> var_data = get_var_input_data()
>>> revenue = var_data.get_variable("AAPL", "total_revenue", period="2023")
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
import asyncio
import concurrent.futures
from threading import Lock

# Import all adapters
from .base_adapter import (
    BaseApiAdapter, DataSourceType, DataCategory, ExtractionResult,
    DataQualityMetrics, ApiCapabilities
)
from .yfinance_adapter import YFinanceAdapter
from .fmp_adapter import FMPAdapter
from .alpha_vantage_adapter import AlphaVantageAdapter
from .polygon_adapter import PolygonAdapter
from .twelve_data_adapter import TwelveDataAdapter

# Import project dependencies
from ..var_input_data import get_var_input_data
from ..financial_variable_registry import get_registry

# Configure logging
logger = logging.getLogger(__name__)


class SourceSelectionStrategy(Enum):
    """Strategies for selecting data sources"""
    QUALITY_FIRST = "quality_first"           # Prioritize highest quality sources
    COST_OPTIMIZED = "cost_optimized"        # Minimize API costs
    SPEED_OPTIMIZED = "speed_optimized"      # Minimize response time
    RELIABILITY_FIRST = "reliability_first"   # Prioritize most reliable sources
    BALANCED = "balanced"                     # Balance all factors


@dataclass
class SourcePriority:
    """Configuration for source priority and constraints"""
    source_type: DataSourceType
    priority: int                           # Lower number = higher priority
    max_cost_per_request: Optional[float]   # Maximum acceptable cost
    max_response_time: Optional[float]      # Maximum acceptable response time (seconds)
    min_quality_score: float = 0.7         # Minimum acceptable quality score
    enabled: bool = True                    # Whether this source is enabled
    rate_limit_buffer: float = 1.2         # Buffer factor for rate limiting


@dataclass
class MultiApiResult:
    """Result from multi-API data extraction with fallback information"""
    symbol: str
    success: bool
    primary_source: Optional[DataSourceType]
    fallback_sources: List[DataSourceType]
    total_variables_extracted: int
    total_data_points_stored: int
    categories_covered: List[DataCategory]
    periods_covered: List[str]
    overall_quality: float
    extraction_time: float
    cost_estimate: Optional[float]
    sources_attempted: List[DataSourceType]
    source_results: Dict[str, ExtractionResult]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class MultiApiManager:
    """
    Multi-API manager with intelligent fallback and optimization.
    
    This manager orchestrates multiple financial data API adapters to provide
    the best possible data quality and availability through intelligent source
    selection and automatic fallback mechanisms.
    """
    
    # Default source priorities (lower = higher priority)
    DEFAULT_SOURCE_PRIORITIES = {
        DataSourceType.YFINANCE: SourcePriority(DataSourceType.YFINANCE, 1, 0.0, 5.0),
        DataSourceType.FMP: SourcePriority(DataSourceType.FMP, 2, 0.01, 10.0),
        DataSourceType.TWELVE_DATA: SourcePriority(DataSourceType.TWELVE_DATA, 2, 0.005, 8.0),
        DataSourceType.ALPHA_VANTAGE: SourcePriority(DataSourceType.ALPHA_VANTAGE, 3, 0.0, 15.0),
        DataSourceType.POLYGON: SourcePriority(DataSourceType.POLYGON, 4, 0.05, 5.0)
    }
    
    def __init__(
        self,
        source_priorities: Optional[Dict[DataSourceType, SourcePriority]] = None,
        selection_strategy: SourceSelectionStrategy = SourceSelectionStrategy.BALANCED,
        max_fallback_attempts: int = 3,
        quality_threshold: float = 0.7,
        enable_parallel_requests: bool = False,
        api_keys: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the multi-API manager.
        
        Args:
            source_priorities: Custom source priority configuration
            selection_strategy: Strategy for selecting data sources
            max_fallback_attempts: Maximum number of fallback attempts
            quality_threshold: Minimum quality score to accept results
            enable_parallel_requests: Whether to enable parallel API requests
            api_keys: Dictionary of API keys for different services
        """
        self.source_priorities = source_priorities or self.DEFAULT_SOURCE_PRIORITIES.copy()
        self.selection_strategy = selection_strategy
        self.max_fallback_attempts = max_fallback_attempts
        self.quality_threshold = quality_threshold
        self.enable_parallel_requests = enable_parallel_requests
        self.api_keys = api_keys or {}
        
        # Initialize adapters
        self.adapters: Dict[DataSourceType, BaseApiAdapter] = {}
        self._initialize_adapters()
        
        # Performance tracking
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'fallback_usage': {source.value: 0 for source in DataSourceType},
            'quality_scores': {source.value: [] for source in DataSourceType},
            'response_times': {source.value: [] for source in DataSourceType},
            'cost_tracking': {source.value: 0.0 for source in DataSourceType}
        }
        self._stats_lock = Lock()
        
        # Cache for source availability and performance
        self._source_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info(f"MultiApiManager initialized with {len(self.adapters)} adapters")
        logger.info(f"Strategy: {selection_strategy.value}, Quality threshold: {quality_threshold}")
    
    def load_symbol_data(
        self,
        symbol: str,
        categories: Optional[List[DataCategory]] = None,
        historical_years: Optional[int] = None,
        validate_data: bool = True,
        force_source: Optional[DataSourceType] = None,
        quality_threshold: Optional[float] = None
    ) -> MultiApiResult:
        """
        Load financial data for a symbol with intelligent source selection and fallback.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            categories: Data categories to retrieve (all if None)
            historical_years: Years of historical data to retrieve. If None, each
                adapter automatically uses its own maximum available years.
            validate_data: Whether to validate data using registry definitions
            force_source: Force use of specific source (bypass selection logic)
            quality_threshold: Override default quality threshold for this request
            
        Returns:
            MultiApiResult with comprehensive results and metadata
        """
        start_time = time.time()
        symbol = symbol.upper().strip()
        quality_threshold = quality_threshold or self.quality_threshold
        
        logger.info(f"Loading data for {symbol} using multi-API manager")
        
        result = MultiApiResult(
            symbol=symbol,
            success=False,
            primary_source=None,
            fallback_sources=[],
            total_variables_extracted=0,
            total_data_points_stored=0,
            categories_covered=[],
            periods_covered=[],
            overall_quality=0.0,
            extraction_time=0.0,
            cost_estimate=0.0,
            sources_attempted=[],
            source_results={},
            errors=[],
            warnings=[],
            metadata={}
        )
        
        try:
            # Determine source priority order
            if force_source:
                source_order = [force_source]
            else:
                source_order = self._determine_source_order(symbol, categories)
            
            # Attempt data extraction with fallback
            best_result = None
            best_quality = 0.0
            
            for attempt, source_type in enumerate(source_order[:self.max_fallback_attempts + 1]):
                if source_type not in self.adapters:
                    result.warnings.append(f"Adapter for {source_type.value} not available")
                    continue
                
                logger.info(f"Attempting {source_type.value} (attempt {attempt + 1})")
                
                try:
                    # Extract data from this source
                    adapter = self.adapters[source_type]
                    extraction_result = adapter.load_symbol_data(
                        symbol=symbol,
                        categories=categories,
                        historical_years=historical_years,
                        validate_data=validate_data
                    )
                    
                    result.sources_attempted.append(source_type)
                    result.source_results[source_type.value] = extraction_result
                    
                    # Track performance
                    self._update_performance_stats(source_type, extraction_result)
                    
                    if extraction_result.success:
                        quality_score = extraction_result.quality_metrics.overall_score
                        
                        # Check if this result meets our quality threshold
                        if quality_score >= quality_threshold:
                            if attempt == 0:
                                result.primary_source = source_type
                            else:
                                result.fallback_sources.append(source_type)
                            
                            # Use this result if it's the best so far
                            if quality_score > best_quality:
                                best_result = extraction_result
                                best_quality = quality_score
                            
                            # If quality is excellent, we can stop
                            if quality_score >= 0.9:
                                logger.info(f"Excellent quality ({quality_score:.2f}) from {source_type.value}, stopping")
                                break
                        else:
                            result.warnings.append(
                                f"{source_type.value} quality ({quality_score:.2f}) below threshold ({quality_threshold:.2f})"
                            )
                    else:
                        result.errors.extend(extraction_result.errors)
                        logger.warning(f"{source_type.value} failed: {extraction_result.errors}")
                
                except Exception as e:
                    error_msg = f"Error with {source_type.value}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Compile final results
            if best_result:
                result.success = True
                result.total_variables_extracted = best_result.variables_extracted
                result.total_data_points_stored = best_result.data_points_stored
                result.categories_covered = best_result.categories_covered
                result.periods_covered = best_result.periods_covered
                result.overall_quality = best_result.quality_metrics.overall_score
                
                # Estimate costs
                result.cost_estimate = self._estimate_extraction_cost(result.sources_attempted, best_result)
            else:
                result.errors.append("All data sources failed or returned low-quality data")
            
            result.extraction_time = time.time() - start_time
            
            # Update global statistics
            with self._stats_lock:
                self._stats['total_requests'] += 1
                if result.success:
                    self._stats['successful_requests'] += 1
                
                for source in result.fallback_sources:
                    self._stats['fallback_usage'][source.value] += 1
            
            result.metadata = {
                'selection_strategy': self.selection_strategy.value,
                'quality_threshold': quality_threshold,
                'sources_available': list(self.adapters.keys()),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Multi-API extraction completed for {symbol}: "
                       f"success={result.success}, quality={result.overall_quality:.2f}, "
                       f"primary={result.primary_source.value if result.primary_source else 'None'}")
            
        except Exception as e:
            error_msg = f"Multi-API extraction failed for {symbol}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.extraction_time = time.time() - start_time
        
        return result
    
    def get_source_capabilities(self) -> Dict[str, ApiCapabilities]:
        """Get capabilities for all available sources"""
        capabilities = {}
        for source_type, adapter in self.adapters.items():
            try:
                capabilities[source_type.value] = adapter.get_capabilities()
            except Exception as e:
                logger.warning(f"Failed to get capabilities for {source_type.value}: {e}")
        
        return capabilities
    
    def validate_all_credentials(self) -> Dict[str, bool]:
        """Validate credentials for all configured adapters"""
        validation_results = {}
        
        for source_type, adapter in self.adapters.items():
            try:
                is_valid = adapter.validate_credentials()
                validation_results[source_type.value] = is_valid
                logger.info(f"{source_type.value} credentials: {'✓' if is_valid else '✗'}")
            except Exception as e:
                validation_results[source_type.value] = False
                logger.error(f"Credential validation failed for {source_type.value}: {e}")
        
        return validation_results
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics for all sources"""
        with self._stats_lock:
            stats = dict(self._stats)  # Copy current stats
        
        # Add adapter-specific statistics
        adapter_stats = {}
        for source_type, adapter in self.adapters.items():
            try:
                adapter_stats[source_type.value] = adapter.get_performance_stats()
            except Exception as e:
                logger.warning(f"Failed to get stats for {source_type.value}: {e}")
        
        # Calculate aggregate metrics
        total_requests = stats['total_requests']
        success_rate = stats['successful_requests'] / max(1, total_requests)
        
        # Calculate average quality scores
        avg_quality_scores = {}
        for source, scores in stats['quality_scores'].items():
            avg_quality_scores[source] = sum(scores) / len(scores) if scores else 0.0
        
        # Calculate average response times
        avg_response_times = {}
        for source, times in stats['response_times'].items():
            avg_response_times[source] = sum(times) / len(times) if times else 0.0
        
        return {
            'manager_stats': {
                'total_requests': total_requests,
                'success_rate': success_rate,
                'fallback_usage': stats['fallback_usage'],
                'total_cost_estimate': sum(stats['cost_tracking'].values()),
                'average_quality_scores': avg_quality_scores,
                'average_response_times': avg_response_times
            },
            'adapter_stats': adapter_stats,
            'configuration': {
                'selection_strategy': self.selection_strategy.value,
                'quality_threshold': self.quality_threshold,
                'max_fallback_attempts': self.max_fallback_attempts,
                'parallel_requests_enabled': self.enable_parallel_requests
            }
        }
    
    def update_source_priority(self, source: DataSourceType, priority: SourcePriority) -> None:
        """Update priority configuration for a specific source"""
        self.source_priorities[source] = priority
        logger.info(f"Updated priority for {source.value}: priority={priority.priority}, "
                   f"enabled={priority.enabled}")
    
    def disable_source(self, source: DataSourceType) -> None:
        """Temporarily disable a data source"""
        if source in self.source_priorities:
            self.source_priorities[source].enabled = False
            logger.info(f"Disabled source: {source.value}")
    
    def enable_source(self, source: DataSourceType) -> None:
        """Re-enable a data source"""
        if source in self.source_priorities:
            self.source_priorities[source].enabled = True
            logger.info(f"Enabled source: {source.value}")
    
    # Private helper methods
    
    def _initialize_adapters(self) -> None:
        """Initialize all available API adapters"""
        try:
            # Initialize yfinance adapter (always available)
            self.adapters[DataSourceType.YFINANCE] = YFinanceAdapter()
            logger.info("✓ yfinance adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize yfinance adapter: {e}")
        
        try:
            # Initialize FMP adapter
            fmp_key = self.api_keys.get('fmp') or self.api_keys.get('FMP_API_KEY')
            self.adapters[DataSourceType.FMP] = FMPAdapter(api_key=fmp_key)
            logger.info("✓ FMP adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize FMP adapter: {e}")
        
        try:
            # Initialize Alpha Vantage adapter
            av_key = self.api_keys.get('alpha_vantage') or self.api_keys.get('ALPHA_VANTAGE_API_KEY')
            self.adapters[DataSourceType.ALPHA_VANTAGE] = AlphaVantageAdapter(api_key=av_key)
            logger.info("✓ Alpha Vantage adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Alpha Vantage adapter: {e}")
        
        try:
            # Initialize Polygon adapter
            poly_key = self.api_keys.get('polygon') or self.api_keys.get('POLYGON_API_KEY')
            self.adapters[DataSourceType.POLYGON] = PolygonAdapter(api_key=poly_key)
            logger.info("✓ Polygon adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Polygon adapter: {e}")

        try:
            # Initialize Twelve Data adapter
            td_key = self.api_keys.get('twelve_data') or self.api_keys.get('TWELVE_DATA_API_KEY')
            self.adapters[DataSourceType.TWELVE_DATA] = TwelveDataAdapter(api_key=td_key)
            logger.info("✓ Twelve Data adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Twelve Data adapter: {e}")
    
    def _determine_source_order(
        self, 
        symbol: str, 
        categories: Optional[List[DataCategory]]
    ) -> List[DataSourceType]:
        """Determine the optimal order of sources to try based on strategy"""
        available_sources = []
        
        # Filter enabled sources
        for source_type, priority in self.source_priorities.items():
            if priority.enabled and source_type in self.adapters:
                available_sources.append((source_type, priority))
        
        if not available_sources:
            logger.error("No enabled data sources available")
            return []
        
        # Apply selection strategy
        if self.selection_strategy == SourceSelectionStrategy.QUALITY_FIRST:
            # Order by historical quality scores (descending)
            available_sources.sort(key=lambda x: self._get_avg_quality_score(x[0]), reverse=True)
        
        elif self.selection_strategy == SourceSelectionStrategy.COST_OPTIMIZED:
            # Order by cost (ascending)
            available_sources.sort(key=lambda x: x[1].max_cost_per_request or 0.0)
        
        elif self.selection_strategy == SourceSelectionStrategy.SPEED_OPTIMIZED:
            # Order by response time (ascending)
            available_sources.sort(key=lambda x: self._get_avg_response_time(x[0]))
        
        elif self.selection_strategy == SourceSelectionStrategy.RELIABILITY_FIRST:
            # Order by reliability rating (descending)
            available_sources.sort(key=lambda x: self._get_reliability_rating(x[0]), reverse=True)
        
        else:  # BALANCED strategy
            # Order by priority (ascending) with quality adjustments
            available_sources.sort(key=lambda x: x[1].priority - self._get_avg_quality_score(x[0]))
        
        source_order = [source[0] for source in available_sources]
        logger.debug(f"Source order for {symbol}: {[s.value for s in source_order]}")
        
        return source_order
    
    def _get_avg_quality_score(self, source_type: DataSourceType) -> float:
        """Get average quality score for a source"""
        scores = self._stats['quality_scores'].get(source_type.value, [])
        return sum(scores) / len(scores) if scores else 0.8  # Default assumption
    
    def _get_avg_response_time(self, source_type: DataSourceType) -> float:
        """Get average response time for a source"""
        times = self._stats['response_times'].get(source_type.value, [])
        return sum(times) / len(times) if times else 10.0  # Default assumption
    
    def _get_reliability_rating(self, source_type: DataSourceType) -> float:
        """Get reliability rating for a source"""
        if source_type in self.adapters:
            try:
                capabilities = self.adapters[source_type].get_capabilities()
                return capabilities.reliability_rating
            except Exception:
                pass
        return 0.8  # Default assumption
    
    def _update_performance_stats(self, source_type: DataSourceType, result: ExtractionResult) -> None:
        """Update performance statistics for a source"""
        with self._stats_lock:
            source_key = source_type.value
            
            # Update quality scores (keep last 100 scores)
            quality_scores = self._stats['quality_scores'][source_key]
            quality_scores.append(result.quality_metrics.overall_score)
            if len(quality_scores) > 100:
                quality_scores.pop(0)
            
            # Update response times (keep last 100 times)
            response_times = self._stats['response_times'][source_key]
            response_times.append(result.extraction_time)
            if len(response_times) > 100:
                response_times.pop(0)
    
    def _estimate_extraction_cost(
        self, 
        sources_attempted: List[DataSourceType], 
        result: ExtractionResult
    ) -> float:
        """Estimate the cost of the data extraction"""
        total_cost = 0.0
        
        for source_type in sources_attempted:
            if source_type in self.adapters:
                try:
                    capabilities = self.adapters[source_type].get_capabilities()
                    if capabilities.cost_per_request:
                        # Estimate based on number of API calls made
                        api_calls = result.metadata.get('total_api_requests', 1)
                        source_cost = capabilities.cost_per_request * api_calls
                        total_cost += source_cost
                        
                        # Track costs
                        with self._stats_lock:
                            self._stats['cost_tracking'][source_type.value] += source_cost
                except Exception:
                    pass
        
        return total_cost


# Convenience functions for common operations

def create_default_manager(api_keys: Optional[Dict[str, str]] = None) -> MultiApiManager:
    """
    Create a MultiApiManager with default configuration.
    
    Args:
        api_keys: Optional dictionary of API keys
        
    Returns:
        Configured MultiApiManager instance
    """
    return MultiApiManager(api_keys=api_keys)


def load_symbol_with_fallback(
    symbol: str,
    api_keys: Optional[Dict[str, str]] = None,
    **kwargs
) -> MultiApiResult:
    """
    Convenience function to load symbol data with intelligent fallback.
    
    Args:
        symbol: Stock symbol
        api_keys: Optional API keys dictionary
        **kwargs: Additional arguments for load_symbol_data()
        
    Returns:
        MultiApiResult with extraction results
    """
    manager = create_default_manager(api_keys)
    return manager.load_symbol_data(symbol, **kwargs)


def get_all_adapter_stats(api_keys: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Convenience function to get statistics from all adapters.
    
    Args:
        api_keys: Optional API keys dictionary
        
    Returns:
        Comprehensive statistics dictionary
    """
    manager = create_default_manager(api_keys)
    return manager.get_performance_statistics()