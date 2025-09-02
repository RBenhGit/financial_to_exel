"""
Universal Data Registry
======================

Centralized data acquisition and management system that serves as the single source 
of truth for all financial data throughout the investment analysis project.

This module implements:
- Singleton data registry pattern
- Multi-layer caching (memory + disk)
- Data source management with fallbacks
- Data validation and quality monitoring
- Data lineage tracking

Classes:
    DataRequest: Request specification for data acquisition
    DataResponse: Response containing data with metadata
    CachePolicy: Caching behavior configuration
    ValidationLevel: Data validation strictness levels
    UniversalDataRegistry: Main singleton registry class
"""

import os
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import pickle

# Configure logging
logger = logging.getLogger(__name__)

class CachePolicy(Enum):
    """Cache behavior policies"""
    DEFAULT = "default"
    NO_CACHE = "no_cache"
    FORCE_REFRESH = "force_refresh"
    PREFER_CACHE = "prefer_cache"

class ValidationLevel(Enum):
    """Data validation strictness levels"""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

class DataSourceType(Enum):
    """Types of data sources"""
    EXCEL = "excel"
    API_YAHOO = "api_yahoo"
    API_FMP = "api_fmp"
    API_ALPHA_VANTAGE = "api_alpha_vantage"
    API_POLYGON = "api_polygon"
    CACHE = "cache"
    USER_INPUT = "user_input"

@dataclass
class DataLineage:
    """Track data provenance and lineage"""
    source_type: DataSourceType
    source_details: str
    timestamp: datetime
    access_count: int = 0
    quality_score: float = 1.0
    transformation_history: List[str] = field(default_factory=list)

@dataclass
class DataRequest:
    """Specification for data acquisition request"""
    data_type: str  # 'financial_statements', 'market_data', 'ratios', etc.
    symbol: str
    period: str  # 'annual', 'quarterly', 'daily', etc.
    source_preference: Optional[List[DataSourceType]] = None
    cache_policy: CachePolicy = CachePolicy.DEFAULT
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    additional_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataResponse:
    """Response containing requested data with metadata"""
    data: Any
    source: DataSourceType
    timestamp: datetime
    quality_score: float
    cache_hit: bool
    lineage: DataLineage
    validation_errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class DataCache:
    """Multi-layer caching system with memory and disk storage"""
    
    def __init__(self, cache_dir: str = "./data_cache", memory_limit_mb: int = 256):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # LRU cache implementation
        from collections import OrderedDict
        self.memory_cache: OrderedDict[str, Any] = OrderedDict()
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.cache_metadata: Dict[str, Dict] = {}
        
        # Access tracking for intelligent eviction
        self.access_counts: Dict[str, int] = {}
        self.last_access: Dict[str, datetime] = {}
        
        # Thread lock for cache operations
        self._lock = threading.RLock()
        
        # Load cache index
        self._load_cache_index()
        
    def _load_cache_index(self):
        """Load cache metadata index from disk"""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.cache_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self.cache_metadata = {}
    
    def _save_cache_index(self):
        """Save cache metadata index to disk"""
        index_file = self.cache_dir / "cache_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _generate_cache_key(self, request: DataRequest) -> str:
        """Generate unique cache key for request"""
        key_data = {
            'data_type': request.data_type,
            'symbol': request.symbol,
            'period': request.period,
            'params': request.additional_params
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, request: DataRequest) -> Optional[DataResponse]:
        """Retrieve data from cache if available and valid"""
        if request.cache_policy == CachePolicy.NO_CACHE:
            return None
            
        cache_key = self._generate_cache_key(request)
        
        with self._lock:
            # Check memory cache first
            if cache_key in self.memory_cache:
                metadata = self.cache_metadata.get(cache_key, {})
                if self._is_cache_valid(metadata):
                    # Update access tracking
                    self.access_counts[cache_key] = self.access_counts.get(cache_key, 0) + 1
                    self.last_access[cache_key] = datetime.now()
                    
                    # Move to end for LRU (most recently used)
                    self.memory_cache.move_to_end(cache_key)
                    
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    return self.memory_cache[cache_key]
                else:
                    # Remove expired memory cache entry
                    del self.memory_cache[cache_key]
                    self.access_counts.pop(cache_key, None)
                    self.last_access.pop(cache_key, None)
            
            # Check disk cache
            return self._get_from_disk(cache_key)
    
    def _get_from_disk(self, cache_key: str) -> Optional[DataResponse]:
        """Retrieve data from disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
            
        metadata = self.cache_metadata.get(cache_key, {})
        if not self._is_cache_valid(metadata):
            # Remove expired cache file
            try:
                cache_file.unlink()
                if cache_key in self.cache_metadata:
                    del self.cache_metadata[cache_key]
                    self._save_cache_index()
            except Exception as e:
                logger.warning(f"Failed to remove expired cache: {e}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                response = pickle.load(f)
                # Load into memory cache for faster future access
                self.memory_cache[cache_key] = response
                
                # Update access tracking
                self.access_counts[cache_key] = self.access_counts.get(cache_key, 0) + 1
                self.last_access[cache_key] = datetime.now()
                
                # Cleanup memory if needed
                self._cleanup_memory_cache()
                
                logger.debug(f"Cache hit (disk): {cache_key}")
                return response
        except Exception as e:
            logger.error(f"Failed to load from disk cache: {e}")
            return None
    
    def _is_cache_valid(self, metadata: Dict) -> bool:
        """Check if cached data is still valid"""
        if not metadata:
            return False
            
        expiry = metadata.get('expiry')
        if not expiry:
            return False
            
        try:
            expiry_dt = datetime.fromisoformat(expiry)
            return datetime.now() < expiry_dt
        except Exception:
            return False
    
    def put(self, request: DataRequest, response: DataResponse, ttl_seconds: int = 3600):
        """Store data in cache"""
        if request.cache_policy == CachePolicy.NO_CACHE:
            return
            
        cache_key = self._generate_cache_key(request)
        
        with self._lock:
            # Update response to indicate cache storage
            response.cache_hit = False  # This is a fresh response being cached
            
            # Store in memory cache
            self.memory_cache[cache_key] = response
            
            # Store metadata
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
            self.cache_metadata[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'expiry': expiry.isoformat(),
                'data_type': request.data_type,
                'symbol': request.symbol,
                'ttl': ttl_seconds
            }
            
            # Store on disk
            self._put_to_disk(cache_key, response)
            self._save_cache_index()
            
            # Cleanup memory if needed
            self._cleanup_memory_cache()
    
    def _put_to_disk(self, cache_key: str, response: DataResponse):
        """Store data to disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(response, f)
        except Exception as e:
            logger.error(f"Failed to save to disk cache: {e}")
    
    def _cleanup_memory_cache(self):
        """Remove old entries if memory limit exceeded using intelligent eviction"""
        # Check memory usage
        import sys
        current_size = sum(sys.getsizeof(item) for item in self.memory_cache.values())
        
        if current_size > self.memory_limit_bytes or len(self.memory_cache) > 1000:
            # Remove 25% of entries to create buffer
            target_count = int(len(self.memory_cache) * 0.75)
            items_to_remove = len(self.memory_cache) - target_count
            
            if items_to_remove > 0:
                # Combine LRU and LFU strategies
                # Get candidates by access frequency and recency
                candidates = []
                current_time = datetime.now()
                
                for key in self.memory_cache:
                    access_count = self.access_counts.get(key, 0)
                    last_used = self.last_access.get(key, current_time)
                    time_since_access = (current_time - last_used).total_seconds()
                    
                    # Lower score = higher priority for eviction
                    # Weight: 60% time since access, 40% inverse frequency
                    score = (time_since_access * 0.6) + ((1 / max(access_count, 1)) * 1000 * 0.4)
                    candidates.append((key, score))
                
                # Sort by score (highest score = first to evict)
                candidates.sort(key=lambda x: x[1], reverse=True)
                
                # Remove candidates
                for key, _ in candidates[:items_to_remove]:
                    del self.memory_cache[key]
                    self.access_counts.pop(key, None)
                    self.last_access.pop(key, None)
                
                logger.debug(f"Evicted {items_to_remove} cache entries to free memory")
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern"""
        with self._lock:
            if pattern is None:
                # Clear all cache
                self.memory_cache.clear()
                self.cache_metadata.clear()
                # Remove all cache files
                for cache_file in self.cache_dir.glob("*.pkl"):
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to remove cache file {cache_file}: {e}")
            else:
                # Pattern-based invalidation (simple implementation)
                keys_to_remove = [
                    key for key in self.cache_metadata.keys() 
                    if pattern in str(self.cache_metadata[key])
                ]
                for key in keys_to_remove:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                    if key in self.cache_metadata:
                        del self.cache_metadata[key]
                    cache_file = self.cache_dir / f"{key}.pkl"
                    if cache_file.exists():
                        try:
                            cache_file.unlink()
                        except Exception as e:
                            logger.warning(f"Failed to remove cache file: {e}")
            
            self._save_cache_index()

class UniversalDataRegistry:
    """
    Singleton registry for centralized data acquisition and management.
    
    This class provides a unified interface for accessing all types of financial data
    across the application, implementing intelligent caching, data source management,
    validation, and lineage tracking.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_dir: str = "./data_cache", config: Dict[str, Any] = None):
        """Initialize the Universal Data Registry"""
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # Configuration
        self.config = config or self._load_default_config()
        
        # Initialize caching system
        self.cache = DataCache(cache_dir, self.config.get('cache', {}).get('memory_size_mb', 256))
        
        # Data source registry
        self.data_sources: Dict[DataSourceType, Any] = {}
        
        # Performance metrics
        self.metrics = {
            'requests_total': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'source_usage': {},
            'average_response_time': 0.0
        }
        
        # Initialize default data sources
        self._initialize_data_sources()
        
        logger.info("Universal Data Registry initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or defaults"""
        try:
            from registry_config_loader import load_registry_config
            
            # Load structured configuration
            structured_config = load_registry_config()
            
            # Convert to dictionary format for backward compatibility
            return {
                'cache': {
                    'memory_size_mb': structured_config.cache.memory_size_mb,
                    'default_ttl_seconds': structured_config.cache.default_ttl_seconds,
                    'disk_cache_enabled': structured_config.cache.disk_cache_enabled
                },
                'data_sources': {
                    name: {
                        'priority': source.priority,
                        'enabled': source.enabled,
                        'company_folder': getattr(source, 'company_folder', None),
                        'timeout': source.timeout,
                        'rate_limit': source.rate_limit
                    }
                    for name, source in structured_config.data_sources.items()
                },
                'validation': {
                    'default_level': structured_config.validation.default_level,
                    'quality_threshold': structured_config.validation.quality_threshold
                },
                'performance': {
                    'default_timeout': structured_config.performance.default_timeout,
                    'max_concurrent_requests': structured_config.performance.max_concurrent_requests
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to load configuration file, using defaults: {e}")
            return {
                'cache': {
                    'memory_size_mb': 256,
                    'default_ttl_seconds': 3600,
                    'disk_cache_enabled': True
                },
                'data_sources': {
                    'excel': {'priority': 1, 'enabled': True},
                    'yahoo_finance': {'priority': 2, 'enabled': True},
                    'fmp': {'priority': 3, 'enabled': True},
                    'alpha_vantage': {'priority': 4, 'enabled': True},
                    'polygon': {'priority': 5, 'enabled': True}
                },
                'validation': {
                    'default_level': 'standard',
                    'quality_threshold': 0.8
                }
            }
    
    def _initialize_data_sources(self):
        """Initialize available data sources"""
        try:
            from data_source_interfaces import DataSourceFactory
            
            # Create all available data sources
            sources = DataSourceFactory.create_all_sources(self.config.get('data_sources', {}))
            
            # Register each source
            for source_type, source in sources.items():
                self.register_data_source(source_type, source)
                
            logger.info(f"Initialized {len(sources)} data sources")
            
        except Exception as e:
            logger.warning(f"Failed to initialize some data sources: {e}")
            # Continue with manual registration as fallback
    
    def register_data_source(self, source_type: DataSourceType, source_instance: Any):
        """Register a data source with the registry"""
        self.data_sources[source_type] = source_instance
        logger.info(f"Registered data source: {source_type}")
    
    def get_data(self, request: DataRequest) -> DataResponse:
        """
        Main method to retrieve data through the registry.
        
        This method handles:
        1. Cache checking
        2. Data source selection and fallbacks
        3. Data validation
        4. Cache storage
        5. Metrics tracking
        """
        start_time = datetime.now()
        self.metrics['requests_total'] += 1
        
        try:
            # Check cache first (unless force refresh)
            if request.cache_policy != CachePolicy.FORCE_REFRESH:
                cached_response = self.cache.get(request)
                if cached_response:
                    cached_response.cache_hit = True
                    self.metrics['cache_hits'] += 1
                    self._update_performance_metrics(start_time)
                    return cached_response
            
            # Cache miss - fetch from data sources
            self.metrics['cache_misses'] += 1
            response = self._fetch_from_sources(request)
            
            # Cache the response
            if response and request.cache_policy != CachePolicy.NO_CACHE:
                ttl = self.config['cache']['default_ttl_seconds']
                self.cache.put(request, response, ttl)
            
            self._update_performance_metrics(start_time)
            return response
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            # Return error response
            return DataResponse(
                data=None,
                source=DataSourceType.CACHE,  # Placeholder
                timestamp=datetime.now(),
                quality_score=0.0,
                cache_hit=False,
                lineage=DataLineage(
                    source_type=DataSourceType.CACHE,
                    source_details=f"Error: {str(e)}",
                    timestamp=datetime.now(),
                    quality_score=0.0
                ),
                validation_errors=[str(e)]
            )
    
    def _fetch_from_sources(self, request: DataRequest) -> DataResponse:
        """Attempt to fetch data from available sources with fallbacks"""
        # Determine source priority order
        source_order = self._get_source_priority_order(request)
        
        last_error = None
        for source_type in source_order:
            if source_type not in self.data_sources:
                continue
                
            try:
                source = self.data_sources[source_type]
                response = self._fetch_from_source(source, source_type, request)
                
                if response and self._validate_response(response, request):
                    # Update source usage metrics
                    if source_type not in self.metrics['source_usage']:
                        self.metrics['source_usage'][source_type] = 0
                    self.metrics['source_usage'][source_type] += 1
                    
                    return response
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_type}: {e}")
                last_error = e
                continue
        
        # All sources failed
        raise Exception(f"All data sources failed. Last error: {last_error}")
    
    def _get_source_priority_order(self, request: DataRequest) -> List[DataSourceType]:
        """Determine the order of data sources to try"""
        if request.source_preference:
            return request.source_preference
        
        # Use configured priority order
        sources_config = self.config.get('data_sources', {})
        enabled_sources = [
            (DataSourceType(name), config.get('priority', 999))
            for name, config in sources_config.items()
            if config.get('enabled', True)
        ]
        
        # Sort by priority (lower number = higher priority)
        enabled_sources.sort(key=lambda x: x[1])
        return [source for source, _ in enabled_sources]
    
    def _fetch_from_source(self, source: Any, source_type: DataSourceType, request: DataRequest) -> DataResponse:
        """Fetch data from a specific source"""
        try:
            # Check if source supports this request
            if hasattr(source, 'supports_request') and not source.supports_request(request):
                raise Exception(f"Source {source_type} does not support request: {request.data_type}")
            
            # Use the standardized fetch_data method
            if hasattr(source, 'fetch_data'):
                return source.fetch_data(request)
            else:
                raise Exception(f"Source {source_type} does not implement fetch_data method")
                
        except Exception as e:
            logger.error(f"Error fetching from {source_type}: {e}")
            raise e
    
    def _validate_response(self, response: DataResponse, request: DataRequest) -> bool:
        """Validate response data according to validation level"""
        if request.validation_level == ValidationLevel.NONE:
            return True
        
        # Basic validation
        if response.data is None:
            return False
        
        if request.validation_level == ValidationLevel.BASIC:
            return True
        
        # Standard validation
        if response.quality_score < self.config['validation']['quality_threshold']:
            return False
        
        # Strict validation would include additional checks
        if request.validation_level == ValidationLevel.STRICT:
            # Additional validation logic here
            pass
        
        return True
    
    def _update_performance_metrics(self, start_time: datetime):
        """Update performance tracking metrics"""
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Update rolling average
        total_requests = self.metrics['requests_total']
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        cache_hit_rate = 0.0
        if self.metrics['requests_total'] > 0:
            cache_hit_rate = self.metrics['cache_hits'] / self.metrics['requests_total']
        
        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate
        }
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        self.cache.invalidate(pattern)
        logger.info(f"Cache invalidated (pattern: {pattern})")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of all registered data sources"""
        health_status = {
            'registry_status': 'healthy',
            'cache_status': 'healthy',
            'data_sources': {}
        }
        
        for source_type, source in self.data_sources.items():
            try:
                # Attempt a simple health check if the source supports it
                if hasattr(source, 'health_check'):
                    health_status['data_sources'][source_type] = source.health_check()
                else:
                    health_status['data_sources'][source_type] = 'unknown'
            except Exception as e:
                health_status['data_sources'][source_type] = f'error: {str(e)}'
        
        return health_status


# Global registry instance accessor
def get_registry() -> UniversalDataRegistry:
    """Get the global Universal Data Registry instance"""
    return UniversalDataRegistry()


# Convenience functions for common operations
def get_financial_data(symbol: str, data_type: str = "financial_statements", 
                      period: str = "annual", **kwargs) -> DataResponse:
    """Convenience function to get financial data"""
    registry = get_registry()
    request = DataRequest(
        data_type=data_type,
        symbol=symbol,
        period=period,
        additional_params=kwargs
    )
    return registry.get_data(request)


def get_market_data(symbol: str, period: str = "daily", **kwargs) -> DataResponse:
    """Convenience function to get market data"""
    registry = get_registry()
    request = DataRequest(
        data_type="market_data",
        symbol=symbol,
        period=period,
        additional_params=kwargs
    )
    return registry.get_data(request)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize registry
    registry = get_registry()
    
    # Print initial metrics
    print("Initial metrics:", registry.get_metrics())
    
    # Print health status
    print("Health status:", registry.health_check())