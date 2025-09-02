"""
VarInputData Core Storage System
================================

Centralized variable storage and access system that serves as the single source of truth
for all financial variables throughout the investment analysis platform.

This module implements:
- Singleton pattern for unified data access
- Thread-safe operations for concurrent access
- Integration with Universal Data Registry for caching
- Historical data management with 10+ years support
- Data validation using FinancialVariableRegistry
- Event system for data updates and cache invalidation
- Metadata tracking for data quality and lineage

Key Features:
------------
- **Unified Interface**: Single entry point for all financial variable access
- **Multi-Source Support**: Seamlessly integrates Excel files and API data sources
- **Historical Data**: Complete time-series support with efficient storage
- **Data Validation**: Built-in validation using FinancialVariableRegistry
- **Performance**: Intelligent caching with the Universal Data Registry
- **Event System**: Real-time notifications for data changes
- **Thread Safety**: Concurrent access support with proper locking

Usage Example:
--------------
>>> from var_input_data import get_var_input_data
>>> 
>>> # Get the singleton instance
>>> var_data = get_var_input_data()
>>> 
>>> # Set a variable value
>>> var_data.set_variable("AAPL", "revenue", 394328, source="excel", period="2023")
>>> 
>>> # Get a variable value
>>> revenue = var_data.get_variable("AAPL", "revenue", period="2023")
>>> print(f"AAPL Revenue 2023: ${revenue}M")
>>> 
>>> # Get historical data
>>> revenue_history = var_data.get_historical_data("AAPL", "revenue", years=5)
>>> print(f"5-year revenue trend: {revenue_history}")
"""

import json
import logging
import threading
import time
import weakref
import sys
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Set, Tuple
from weakref import WeakSet
import psutil
import gc

# Import project dependencies
from .financial_variable_registry import (
    get_registry,
    FinancialVariableRegistry,
    VariableDefinition,
    VariableCategory,
    DataType,
    Units
)

from .universal_data_registry import (
    UniversalDataRegistry,
    DataRequest,
    DataResponse,
    CachePolicy,
    ValidationLevel,
    DataSourceType
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LazyLoadConfig:
    """Configuration for lazy loading behavior"""
    enable_lazy_loading: bool = True
    memory_threshold_mb: int = 512  # Trigger lazy loading when memory usage exceeds this
    max_cached_symbols: int = 50    # Maximum symbols to keep in memory
    max_periods_per_variable: int = 20  # Maximum periods to cache per variable
    eviction_policy: str = "lru"    # "lru", "lfu", "ttl"
    auto_gc_interval_seconds: int = 300  # Run garbage collection every 5 minutes


class DataChangeEvent(Enum):
    """Types of data change events"""
    VARIABLE_SET = "variable_set"
    VARIABLE_UPDATED = "variable_updated"
    VARIABLE_DELETED = "variable_deleted"
    HISTORICAL_DATA_ADDED = "historical_data_added"
    CACHE_CLEARED = "cache_cleared"
    BULK_UPDATE = "bulk_update"


@dataclass
class VariableMetadata:
    """Metadata associated with a variable value"""
    source: str                        # Source of the data (excel, api, calculated)
    timestamp: datetime               # When the data was set/updated
    quality_score: float = 1.0        # Data quality score (0.0 to 1.0)
    validation_passed: bool = True    # Whether validation was successful
    calculation_method: str = ""      # How calculated variables were derived
    dependencies: List[str] = field(default_factory=list)  # Variables this depends on
    lineage_id: str = ""             # Unique identifier for data lineage tracking
    period: str = ""                 # Time period (2023, Q1-2023, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization"""
        return {
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'quality_score': self.quality_score,
            'validation_passed': self.validation_passed,
            'calculation_method': self.calculation_method,
            'dependencies': self.dependencies,
            'lineage_id': self.lineage_id,
            'period': self.period
        }


@dataclass
class VariableValue:
    """Container for variable value with metadata"""
    value: Any
    metadata: VariableMetadata
    
    def __post_init__(self):
        """Ensure metadata timestamp is set"""
        if not hasattr(self.metadata, 'timestamp') or self.metadata.timestamp is None:
            self.metadata.timestamp = datetime.now()


@dataclass 
class HistoricalDataPoint:
    """Single point in historical time series"""
    symbol: str
    variable_name: str
    period: str
    value: Any
    metadata: VariableMetadata
    
    def __post_init__(self):
        """Validate and normalize the data point"""
        if not self.symbol or not self.variable_name or not self.period:
            raise ValueError("Symbol, variable_name, and period are required")
        
        # Normalize symbol to uppercase
        self.symbol = self.symbol.upper()
        
        # Normalize variable name to lowercase
        self.variable_name = self.variable_name.lower()


class VarInputDataEventSystem:
    """Event system for data change notifications"""
    
    def __init__(self):
        self._listeners: Dict[DataChangeEvent, WeakSet] = {
            event_type: WeakSet() for event_type in DataChangeEvent
        }
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: DataChangeEvent, callback: Callable) -> None:
        """Subscribe to a specific event type"""
        with self._lock:
            self._listeners[event_type].add(callback)
            logger.debug(f"Added event listener for {event_type.value}")
    
    def unsubscribe(self, event_type: DataChangeEvent, callback: Callable) -> None:
        """Unsubscribe from a specific event type"""
        with self._lock:
            self._listeners[event_type].discard(callback)
            logger.debug(f"Removed event listener for {event_type.value}")
    
    def emit(self, event_type: DataChangeEvent, **kwargs) -> None:
        """Emit an event to all subscribers"""
        with self._lock:
            listeners = list(self._listeners[event_type])  # Create snapshot
        
        # Call listeners outside the lock to prevent deadlocks
        for callback in listeners:
            try:
                callback(event_type=event_type, **kwargs)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type.value}: {e}")


class LazyLoadManager:
    """Manages lazy loading and memory optimization for VarInputData"""
    
    def __init__(self, config: LazyLoadConfig = None):
        self.config = config or LazyLoadConfig()
        self._access_times: Dict[str, datetime] = OrderedDict()  # LRU tracking
        self._access_counts: Dict[str, int] = defaultdict(int)   # LFU tracking
        self._lock = threading.RLock()
        self._last_gc_time = datetime.now()
        
    def track_access(self, key: str) -> None:
        """Track access for eviction policies"""
        with self._lock:
            self._access_times[key] = datetime.now()
            self._access_counts[key] += 1
            # Move to end for LRU
            self._access_times.move_to_end(key)
    
    def should_lazy_load(self) -> bool:
        """Determine if lazy loading should be triggered"""
        if not self.config.enable_lazy_loading:
            return False
            
        # Check memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        return memory_mb > self.config.memory_threshold_mb
    
    def get_eviction_candidates(self, data_dict: Dict, target_count: int) -> List[str]:
        """Get keys to evict based on configured policy"""
        if len(data_dict) <= target_count:
            return []
            
        candidates = []
        excess_count = len(data_dict) - target_count
        
        if self.config.eviction_policy == "lru":
            # Evict least recently used
            sorted_keys = list(self._access_times.keys())
            candidates = sorted_keys[:excess_count]
        elif self.config.eviction_policy == "lfu":
            # Evict least frequently used
            sorted_items = sorted(self._access_counts.items(), key=lambda x: x[1])
            candidates = [key for key, _ in sorted_items[:excess_count]]
        elif self.config.eviction_policy == "ttl":
            # Evict oldest entries
            candidates = list(data_dict.keys())[:excess_count]
            
        return candidates
    
    def should_run_gc(self) -> bool:
        """Check if garbage collection should be run"""
        time_since_gc = datetime.now() - self._last_gc_time
        return time_since_gc.total_seconds() > self.config.auto_gc_interval_seconds
    
    def run_gc(self) -> Dict[str, Any]:
        """Run garbage collection and return statistics"""
        logger.debug("Running garbage collection")
        
        # Get memory info before GC
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # Run garbage collection
        collected_objects = gc.collect()
        
        # Get memory info after GC
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_freed = memory_before - memory_after
        
        self._last_gc_time = datetime.now()
        
        stats = {
            'collected_objects': collected_objects,
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_freed_mb': memory_freed,
            'gc_timestamp': self._last_gc_time.isoformat()
        }
        
        logger.info(f"GC completed: freed {memory_freed:.1f}MB, collected {collected_objects} objects")
        return stats


class VarInputData:
    """
    Centralized variable storage and access system with thread-safe operations.
    
    This singleton class provides the main interface for all financial variable
    operations throughout the application, including:
    - Variable storage and retrieval with lazy loading
    - Historical data management with intelligent caching
    - Data validation and quality monitoring  
    - Event notifications for data changes
    - Integration with caching systems
    - Memory optimization with LRU/LFU eviction policies
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation with double-checked locking"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, lazy_config: LazyLoadConfig = None):
        """Initialize the VarInputData system if not already initialized"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        
        # Core data storage
        # Structure: {symbol: {variable_name: {period: VariableValue}}}
        self._data: Dict[str, Dict[str, Dict[str, VariableValue]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        
        # Historical data storage for time-series analysis
        # Structure: {symbol: {variable_name: [HistoricalDataPoint]}}
        self._historical_data: Dict[str, Dict[str, List[HistoricalDataPoint]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Thread safety
        self._data_lock = threading.RLock()
        
        # Initialize registries and systems
        self._variable_registry = get_registry()
        self._data_registry = UniversalDataRegistry()
        self._event_system = VarInputDataEventSystem()
        
        # Initialize lazy loading manager
        self._lazy_manager = LazyLoadManager(lazy_config)
        
        # Performance tracking with additional lazy loading metrics
        self._access_stats = {
            'get_operations': 0,
            'set_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0,
            'lazy_loads': 0,
            'memory_evictions': 0,
            'gc_runs': 0
        }
        self._stats_lock = threading.Lock()
        
        # Track loaded symbols for memory management
        self._loaded_symbols: Set[str] = set()
        
        logger.info("VarInputData system initialized with lazy loading support")
    
    def get_variable(
        self, 
        symbol: str, 
        variable_name: str, 
        period: str = "latest",
        include_metadata: bool = False,
        use_cache: bool = True,
        force_load: bool = False
    ) -> Union[Any, Tuple[Any, VariableMetadata]]:
        """
        Get a variable value for a specific symbol and period with lazy loading.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            variable_name: Name of the financial variable (e.g., "revenue")
            period: Time period ("latest", "2023", "Q1-2023", etc.)
            include_metadata: Whether to return metadata with the value
            use_cache: Whether to use cached data if available
            force_load: Force loading even if lazy loading is enabled
            
        Returns:
            Variable value, or tuple of (value, metadata) if include_metadata=True
            Returns None if variable not found
        """
        with self._stats_lock:
            self._access_stats['get_operations'] += 1
        
        # Normalize inputs
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        # Track access for lazy loading
        access_key = f"{symbol}:{variable_name}:{period}"
        self._lazy_manager.track_access(access_key)
        
        # Validate variable exists in registry
        var_def = self._variable_registry.get_variable_definition(variable_name)
        if not var_def:
            logger.warning(f"Variable '{variable_name}' not found in registry")
            return None
        
        # Check if we should trigger memory optimization
        self._check_and_optimize_memory()
        
        with self._data_lock:
            # Check if we have the data in memory
            if symbol in self._data and variable_name in self._data[symbol]:
                if period == "latest":
                    # Get the most recent period for this variable
                    periods = sorted(self._data[symbol][variable_name].keys(), reverse=True)
                    if periods:
                        period = periods[0]
                        
                if period in self._data[symbol][variable_name]:
                    with self._stats_lock:
                        self._access_stats['cache_hits'] += 1
                    
                    var_value = self._data[symbol][variable_name][period]
                    logger.debug(f"Retrieved {symbol}.{variable_name}[{period}] from memory cache")
                    
                    if include_metadata:
                        return var_value.value, var_value.metadata
                    return var_value.value
            
            # Data not in memory cache - check if lazy loading should apply
            if not force_load and self._lazy_manager.should_lazy_load() and not self._is_priority_data(symbol, variable_name):
                # Skip loading for non-priority data to preserve memory
                logger.debug(f"Skipping lazy load for {symbol}.{variable_name}[{period}] due to memory constraints")
                return None
            
            # Data not in memory cache
            with self._stats_lock:
                self._access_stats['cache_misses'] += 1
                if not force_load and self._lazy_manager.should_lazy_load():
                    self._access_stats['lazy_loads'] += 1
        
        # Try to load from Universal Data Registry if use_cache is enabled
        if use_cache:
            try:
                data_value = self._load_from_registry(symbol, variable_name, period)
                if data_value is not None:
                    # Track the symbol as loaded
                    self._loaded_symbols.add(symbol)
                    
                    if include_metadata:
                        return data_value
                    return data_value[0] if isinstance(data_value, tuple) else data_value
            except Exception as e:
                logger.error(f"Error loading from Universal Data Registry: {e}")
        
        logger.debug(f"Variable {symbol}.{variable_name}[{period}] not found")
        return None
    
    def set_variable(
        self,
        symbol: str,
        variable_name: str,
        value: Any,
        period: str = "latest",
        source: str = "manual",
        metadata: Optional[VariableMetadata] = None,
        validate: bool = True,
        emit_event: bool = True
    ) -> bool:
        """
        Set a variable value for a specific symbol and period.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            variable_name: Name of the financial variable (e.g., "revenue")
            value: The value to set
            period: Time period ("latest", "2023", "Q1-2023", etc.)
            source: Source of the data ("excel", "api", "calculated", "manual")
            metadata: Optional metadata object
            validate: Whether to validate the value
            emit_event: Whether to emit change event
            
        Returns:
            True if successful, False otherwise
        """
        with self._stats_lock:
            self._access_stats['set_operations'] += 1
        
        # Normalize inputs
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        # Get variable definition for validation
        var_def = self._variable_registry.get_variable_definition(variable_name)
        if not var_def:
            logger.error(f"Cannot set unknown variable '{variable_name}'. Register it first.")
            return False
        
        # Validate the value if requested
        if validate:
            is_valid, errors = var_def.validate_value(value)
            if not is_valid:
                with self._stats_lock:
                    self._access_stats['validation_failures'] += 1
                logger.warning(f"Validation failed for {symbol}.{variable_name}: {errors}")
                # Continue anyway but mark as validation failed
        
        # Create or update metadata
        if metadata is None:
            metadata = VariableMetadata(
                source=source,
                timestamp=datetime.now(),
                quality_score=1.0 if validate and is_valid else 0.8,
                validation_passed=not validate or is_valid,
                period=period
            )
        
        # Create variable value object
        var_value = VariableValue(value=value, metadata=metadata)
        
        # Store the data
        with self._data_lock:
            # Determine if this is an update or new value
            is_update = (
                symbol in self._data and 
                variable_name in self._data[symbol] and 
                period in self._data[symbol][variable_name]
            )
            
            # Check if we need to evict data before storing
            self._check_and_evict_data(symbol, variable_name)
            
            # Store the value
            self._data[symbol][variable_name][period] = var_value
            
            # Track the symbol as loaded
            self._loaded_symbols.add(symbol)
            
            # Add to historical data if it's not already there
            self._add_to_historical_data(symbol, variable_name, period, value, metadata)
            
            logger.debug(f"{'Updated' if is_update else 'Set'} {symbol}.{variable_name}[{period}] = {value}")
        
        # Emit change event
        if emit_event:
            event_type = DataChangeEvent.VARIABLE_UPDATED if is_update else DataChangeEvent.VARIABLE_SET
            self._event_system.emit(
                event_type,
                symbol=symbol,
                variable_name=variable_name,
                period=period,
                value=value,
                metadata=metadata
            )
        
        return True
    
    def get_historical_data(
        self,
        symbol: str,
        variable_name: str,
        years: int = 10,
        include_metadata: bool = False
    ) -> List[Union[Tuple[str, Any], Tuple[str, Any, VariableMetadata]]]:
        """
        Get historical data for a variable across multiple time periods.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            variable_name: Name of the financial variable (e.g., "revenue")
            years: Number of years of data to retrieve (default 10)
            include_metadata: Whether to include metadata for each data point
            
        Returns:
            List of tuples: [(period, value), ...] or [(period, value, metadata), ...] 
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        with self._data_lock:
            if symbol not in self._historical_data or variable_name not in self._historical_data[symbol]:
                logger.debug(f"No historical data found for {symbol}.{variable_name}")
                return []
            
            historical_points = self._historical_data[symbol][variable_name]
            
            # Sort by period (most recent first)
            sorted_points = sorted(
                historical_points, 
                key=lambda x: self._parse_period_for_sorting(x.period), 
                reverse=True
            )
            
            # Limit to requested number of years
            if years > 0:
                sorted_points = sorted_points[:years]
            
            # Format results
            results = []
            for point in sorted_points:
                if include_metadata:
                    results.append((point.period, point.value, point.metadata))
                else:
                    results.append((point.period, point.value))
            
            logger.debug(f"Retrieved {len(results)} historical points for {symbol}.{variable_name}")
            return results
    
    def clear_cache(
        self,
        symbol: Optional[str] = None,
        variable_name: Optional[str] = None,
        clear_registry_cache: bool = True,
        emit_event: bool = True
    ) -> None:
        """
        Clear cached data for specified symbol/variable or all data.
        
        Args:
            symbol: Specific symbol to clear (None for all)
            variable_name: Specific variable to clear (None for all)
            clear_registry_cache: Whether to also clear Universal Data Registry cache
            emit_event: Whether to emit cache cleared event
        """
        with self._data_lock:
            if symbol is None:
                # Clear all data
                cleared_symbols = len(self._data)
                self._data.clear()
                self._historical_data.clear()
                logger.info(f"Cleared all cached data for {cleared_symbols} symbols")
                
                # Clear Universal Data Registry cache if requested
                if clear_registry_cache:
                    try:
                        self._data_registry.cache.invalidate()  # Clear all cache
                        logger.info("Cleared Universal Data Registry cache")
                    except Exception as e:
                        logger.error(f"Error clearing Universal Data Registry cache: {e}")
                        
            else:
                symbol = symbol.upper().strip()
                if symbol in self._data:
                    if variable_name is None:
                        # Clear all variables for this symbol
                        cleared_vars = len(self._data[symbol])
                        del self._data[symbol]
                        if symbol in self._historical_data:
                            del self._historical_data[symbol]
                        logger.info(f"Cleared {cleared_vars} variables for symbol {symbol}")
                        
                        # Clear Universal Data Registry cache for this symbol
                        if clear_registry_cache:
                            try:
                                self._data_registry.cache.invalidate(pattern=symbol)
                                logger.debug(f"Cleared Universal Data Registry cache for {symbol}")
                            except Exception as e:
                                logger.error(f"Error clearing registry cache for {symbol}: {e}")
                                
                    else:
                        # Clear specific variable for this symbol
                        variable_name = variable_name.lower().strip()
                        if variable_name in self._data[symbol]:
                            del self._data[symbol][variable_name]
                            if (symbol in self._historical_data and 
                                variable_name in self._historical_data[symbol]):
                                del self._historical_data[symbol][variable_name]
                            logger.info(f"Cleared {symbol}.{variable_name} from cache")
                            
                            # Clear Universal Data Registry cache for this specific variable
                            if clear_registry_cache:
                                try:
                                    pattern = f"{symbol}_{variable_name}"
                                    self._data_registry.cache.invalidate(pattern=pattern)
                                    logger.debug(f"Cleared registry cache for {symbol}.{variable_name}")
                                except Exception as e:
                                    logger.error(f"Error clearing registry cache for {symbol}.{variable_name}: {e}")
        
        # Emit event
        if emit_event:
            self._event_system.emit(
                DataChangeEvent.CACHE_CLEARED,
                symbol=symbol,
                variable_name=variable_name
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the VarInputData system including memory usage"""
        with self._data_lock:
            symbol_count = len(self._data)
            variable_count = sum(len(variables) for variables in self._data.values())
            total_data_points = sum(
                len(periods) 
                for symbol_vars in self._data.values() 
                for periods in symbol_vars.values()
            )
            
            historical_count = sum(
                len(data_points)
                for symbol_data in self._historical_data.values()
                for data_points in symbol_data.values()
            )
        
        # Get memory information
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        with self._stats_lock:
            stats = {
                'data_storage': {
                    'symbols': symbol_count,
                    'loaded_symbols': len(self._loaded_symbols),
                    'unique_variables': variable_count,
                    'total_data_points': total_data_points,
                    'historical_data_points': historical_count
                },
                'performance': dict(self._access_stats),
                'cache_hit_rate': (
                    self._access_stats['cache_hits'] / 
                    max(1, self._access_stats['cache_hits'] + self._access_stats['cache_misses'])
                ),
                'memory': {
                    'current_usage_mb': memory_mb,
                    'threshold_mb': self._lazy_manager.config.memory_threshold_mb,
                    'lazy_loading_active': self._lazy_manager.should_lazy_load(),
                    'eviction_policy': self._lazy_manager.config.eviction_policy,
                    'max_cached_symbols': self._lazy_manager.config.max_cached_symbols
                },
                'system_info': {
                    'initialized': self._initialized,
                    'variable_registry_size': len(self._variable_registry.list_all_variables()),
                    'event_listeners': sum(
                        len(listeners) for listeners in self._event_system._listeners.values()
                    ),
                    'python_version': sys.version.split()[0],
                    'gc_counts': gc.get_count()
                }
            }
        
        return stats
    
    def bulk_update(
        self,
        data: Dict[str, Dict[str, Dict[str, Any]]],
        source: str = "bulk_import",
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Bulk update multiple variables at once.
        
        Args:
            data: Nested dict {symbol: {variable_name: {period: value}}}
            source: Source identifier for all data
            validate: Whether to validate all values
            
        Returns:
            Dictionary with success/failure statistics
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Temporarily disable individual events for performance
        for symbol, variables in data.items():
            for variable_name, periods in variables.items():
                for period, value in periods.items():
                    success = self.set_variable(
                        symbol=symbol,
                        variable_name=variable_name,
                        value=value,
                        period=period,
                        source=source,
                        validate=validate,
                        emit_event=False  # Disable individual events
                    )
                    
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to set {symbol}.{variable_name}[{period}]")
        
        # Emit single bulk update event
        self._event_system.emit(
            DataChangeEvent.BULK_UPDATE,
            data_count=results['successful'],
            source=source
        )
        
        logger.info(f"Bulk update completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def subscribe_to_events(self, event_type: DataChangeEvent, callback: Callable) -> None:
        """Subscribe to data change events"""
        self._event_system.subscribe(event_type, callback)
    
    def unsubscribe_from_events(self, event_type: DataChangeEvent, callback: Callable) -> None:
        """Unsubscribe from data change events"""  
        self._event_system.unsubscribe(event_type, callback)
    
    def get_available_symbols(self) -> List[str]:
        """Get list of all symbols with data in the system"""
        with self._data_lock:
            return sorted(list(self._data.keys()))
    
    def get_available_variables(self, symbol: Optional[str] = None) -> List[str]:
        """
        Get list of available variables for a symbol or all variables.
        
        Args:
            symbol: Specific symbol to check (None for all variables across all symbols)
            
        Returns:
            List of variable names
        """
        with self._data_lock:
            if symbol is None:
                # Get all unique variable names across all symbols
                all_variables = set()
                for symbol_data in self._data.values():
                    all_variables.update(symbol_data.keys())
                return sorted(list(all_variables))
            else:
                symbol = symbol.upper().strip()
                if symbol in self._data:
                    return sorted(list(self._data[symbol].keys()))
                return []
    
    def get_available_periods(self, symbol: str, variable_name: str) -> List[str]:
        """
        Get list of available periods for a specific symbol and variable.
        
        Args:
            symbol: Stock symbol
            variable_name: Name of the financial variable
            
        Returns:
            List of period strings, sorted by most recent first
        """
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        with self._data_lock:
            if (symbol in self._data and 
                variable_name in self._data[symbol]):
                periods = list(self._data[symbol][variable_name].keys())
                return sorted(periods, key=self._parse_period_for_sorting, reverse=True)
            return []
    
    def has_variable(self, symbol: str, variable_name: str, period: str = "latest") -> bool:
        """
        Check if a variable exists for a symbol and period.
        
        Args:
            symbol: Stock symbol
            variable_name: Name of the financial variable  
            period: Time period
            
        Returns:
            True if variable exists, False otherwise
        """
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        with self._data_lock:
            if symbol not in self._data or variable_name not in self._data[symbol]:
                return False
                
            if period == "latest":
                return len(self._data[symbol][variable_name]) > 0
            else:
                return period in self._data[symbol][variable_name]
    
    def update_metadata(
        self,
        symbol: str,
        variable_name: str,
        period: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an existing variable.
        
        Args:
            symbol: Stock symbol
            variable_name: Name of the financial variable
            period: Time period
            metadata_updates: Dictionary of metadata fields to update
            
        Returns:
            True if successful, False if variable not found
        """
        symbol = symbol.upper().strip()
        variable_name = variable_name.lower().strip()
        
        with self._data_lock:
            if (symbol not in self._data or 
                variable_name not in self._data[symbol] or
                period not in self._data[symbol][variable_name]):
                return False
            
            var_value = self._data[symbol][variable_name][period]
            
            # Update metadata fields
            for field, value in metadata_updates.items():
                if hasattr(var_value.metadata, field):
                    setattr(var_value.metadata, field, value)
            
            # Update timestamp to reflect metadata change
            var_value.metadata.timestamp = datetime.now()
            
            logger.debug(f"Updated metadata for {symbol}.{variable_name}[{period}]")
            return True
    
    def export_data(
        self, 
        symbol: Optional[str] = None,
        include_metadata: bool = True,
        format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """
        Export stored data to JSON format.
        
        Args:
            symbol: Specific symbol to export (None for all)
            include_metadata: Whether to include metadata in export
            format: Export format ("json" or "dict")
            
        Returns:
            JSON string or dictionary with exported data
        """
        with self._data_lock:
            export_data = {}
            
            symbols_to_export = [symbol.upper()] if symbol else list(self._data.keys())
            
            for sym in symbols_to_export:
                if sym not in self._data:
                    continue
                    
                export_data[sym] = {}
                for var_name, periods in self._data[sym].items():
                    export_data[sym][var_name] = {}
                    for period, var_value in periods.items():
                        if include_metadata:
                            export_data[sym][var_name][period] = {
                                'value': var_value.value,
                                'metadata': var_value.metadata.to_dict()
                            }
                        else:
                            export_data[sym][var_name][period] = var_value.value
            
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                return export_data
    
    # Private helper methods for lazy loading and memory optimization
    
    def _is_priority_data(self, symbol: str, variable_name: str) -> bool:
        """Determine if data should be prioritized for loading"""
        # Priority data: recent periods, core financial metrics
        priority_variables = {'revenue', 'net_income', 'total_assets', 'total_debt', 'cash', 'free_cash_flow'}
        return variable_name.lower() in priority_variables
    
    def _check_and_optimize_memory(self) -> None:
        """Check memory usage and optimize if needed"""
        # Run garbage collection if needed
        if self._lazy_manager.should_run_gc():
            with self._stats_lock:
                self._access_stats['gc_runs'] += 1
            self._lazy_manager.run_gc()
        
        # Check if we need to evict symbols
        if len(self._loaded_symbols) > self._lazy_manager.config.max_cached_symbols:
            self._evict_symbols()
    
    def _check_and_evict_data(self, symbol: str, variable_name: str) -> None:
        """Check if we need to evict data before storing new data"""
        with self._data_lock:
            if symbol in self._data and variable_name in self._data[symbol]:
                periods = self._data[symbol][variable_name]
                if len(periods) > self._lazy_manager.config.max_periods_per_variable:
                    # Evict older periods
                    candidates = self._lazy_manager.get_eviction_candidates(
                        periods, 
                        self._lazy_manager.config.max_periods_per_variable
                    )
                    for period_key in candidates:
                        if period_key in periods:
                            del periods[period_key]
                            logger.debug(f"Evicted period {period_key} for {symbol}.{variable_name}")
                    
                    with self._stats_lock:
                        self._access_stats['memory_evictions'] += len(candidates)
    
    def _evict_symbols(self) -> None:
        """Evict less frequently accessed symbols from memory"""
        with self._data_lock:
            # Get symbols to evict
            target_count = int(self._lazy_manager.config.max_cached_symbols * 0.8)  # Remove 20% buffer
            candidates = self._lazy_manager.get_eviction_candidates(
                self._data, 
                target_count
            )
            
            evicted_count = 0
            for symbol in candidates:
                if symbol in self._data:
                    # Remove symbol data
                    del self._data[symbol]
                    if symbol in self._historical_data:
                        del self._historical_data[symbol]
                    self._loaded_symbols.discard(symbol)
                    evicted_count += 1
                    logger.debug(f"Evicted symbol {symbol} from memory cache")
            
            if evicted_count > 0:
                with self._stats_lock:
                    self._access_stats['memory_evictions'] += evicted_count
                logger.info(f"Evicted {evicted_count} symbols to free memory")
    
    def _add_to_historical_data(
        self,
        symbol: str,
        variable_name: str,
        period: str,
        value: Any,
        metadata: VariableMetadata
    ) -> None:
        """Add a data point to historical storage"""
        data_point = HistoricalDataPoint(
            symbol=symbol,
            variable_name=variable_name,
            period=period,
            value=value,
            metadata=metadata
        )
        
        # Check if this data point already exists
        existing_points = self._historical_data[symbol][variable_name]
        for i, existing_point in enumerate(existing_points):
            if existing_point.period == period:
                # Update existing point
                existing_points[i] = data_point
                return
        
        # Add new point
        self._historical_data[symbol][variable_name].append(data_point)
        
        # Keep historical data sorted and limited (e.g., last 50 years)
        if len(existing_points) > 50:
            # Sort by period and keep most recent
            sorted_points = sorted(
                existing_points,
                key=lambda x: self._parse_period_for_sorting(x.period),
                reverse=True
            )
            self._historical_data[symbol][variable_name] = sorted_points[:50]
    
    def _parse_period_for_sorting(self, period: str) -> int:
        """Parse period string into integer for sorting (most recent first)"""
        try:
            # Handle different period formats
            if period == "latest":
                return 999999  # Latest should sort first
            elif period.isdigit() and len(period) == 4:  # Year format like "2023"
                return int(period)
            elif "Q" in period:  # Quarter format like "Q1-2023"
                parts = period.split("-")
                if len(parts) == 2:
                    quarter_part = parts[0].replace("Q", "")
                    year_part = parts[1]
                    return int(year_part) * 10 + int(quarter_part)
            else:
                # Try to extract year from other formats
                import re
                year_match = re.search(r'20\d{2}', period)
                if year_match:
                    return int(year_match.group())
        except (ValueError, IndexError):
            pass
        
        # Default to 0 for unparseable periods
        return 0
    
    def _load_from_registry(
        self,
        symbol: str,
        variable_name: str,
        period: str
    ) -> Optional[Union[Any, Tuple[Any, VariableMetadata]]]:
        """Load data from Universal Data Registry"""
        try:
            # Create data request for Universal Data Registry
            request = DataRequest(
                data_type="financial_variable",
                symbol=symbol,
                period=period,
                additional_params={
                    "variable_name": variable_name
                }
            )
            
            # Try to get data from Universal Data Registry
            response = self._data_registry.get_data(request)
            
            if response and response.data is not None:
                # Convert DataResponse to our format
                metadata = VariableMetadata(
                    source=response.source.value if hasattr(response.source, 'value') else str(response.source),
                    timestamp=response.timestamp,
                    quality_score=response.quality_score,
                    validation_passed=len(response.validation_errors) == 0,
                    period=period,
                    lineage_id=getattr(response.lineage, 'source_details', '')
                )
                
                # Store in memory cache for future access
                var_value = VariableValue(value=response.data, metadata=metadata)
                with self._data_lock:
                    self._data[symbol][variable_name][period] = var_value
                    self._add_to_historical_data(symbol, variable_name, period, response.data, metadata)
                
                logger.debug(f"Loaded {symbol}.{variable_name}[{period}] from Universal Data Registry")
                return response.data, metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading from Universal Data Registry: {e}")
            return None


# Singleton access function
def get_var_input_data() -> VarInputData:
    """
    Get the singleton VarInputData instance.
    
    Returns:
        The singleton VarInputData instance
    """
    return VarInputData()


# Convenience functions for common operations

def get_variable(symbol: str, variable_name: str, period: str = "latest") -> Any:
    """Convenience function to get a variable value"""
    return get_var_input_data().get_variable(symbol, variable_name, period)


def set_variable(
    symbol: str, 
    variable_name: str, 
    value: Any, 
    period: str = "latest",
    source: str = "manual"
) -> bool:
    """Convenience function to set a variable value"""
    return get_var_input_data().set_variable(symbol, variable_name, value, period, source)


def get_historical_data(symbol: str, variable_name: str, years: int = 10) -> List[Tuple[str, Any]]:
    """Convenience function to get historical data"""
    return get_var_input_data().get_historical_data(symbol, variable_name, years)


def clear_cache(symbol: Optional[str] = None, variable_name: Optional[str] = None) -> None:
    """Convenience function to clear cache"""
    get_var_input_data().clear_cache(symbol, variable_name)


# Export main classes and functions
__all__ = [
    'VarInputData',
    'get_var_input_data',
    'VariableMetadata',
    'VariableValue',
    'HistoricalDataPoint',
    'DataChangeEvent',
    'get_variable',
    'set_variable', 
    'get_historical_data',
    'clear_cache'
]