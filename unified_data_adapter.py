"""
Unified Data Adapter Module

This module provides a unified interface for accessing financial data from multiple sources
with automatic fallback, caching, rate limiting, and cost management.

Features:
- Unified data access interface
- Automatic source fallback hierarchy
- Intelligent caching with TTL
- Rate limiting across all sources
- Cost tracking and management
- Data quality assessment
- Usage analytics and reporting
"""

import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import time

from data_sources import (
    DataSourceType, DataSourcePriority, DataSourceConfig, ApiCredentials,
    FinancialDataRequest, DataSourceResponse, DataQualityMetrics,
    AlphaVantageProvider, FinancialModelingPrepProvider, PolygonProvider, ExcelDataProvider, YfinanceProvider
)

logger = logging.getLogger(__name__)

@dataclass
class UsageStatistics:
    """Track usage statistics for cost management"""
    source_type: DataSourceType
    total_calls: int = 0
    total_cost: float = 0.0
    successful_calls: int = 0
    failed_calls: int = 0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    monthly_calls: int = 0
    monthly_cost: float = 0.0
    
    def update_stats(self, response: DataSourceResponse):
        """Update statistics with new response"""
        self.total_calls += 1
        self.total_cost += response.cost_incurred
        self.last_used = datetime.now()
        
        if response.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        # Update average response time
        total_time = self.average_response_time * (self.total_calls - 1) + response.response_time
        self.average_response_time = total_time / self.total_calls
        
        # Monthly tracking (reset if new month)
        now = datetime.now()
        if (self.last_used and 
            (now.month != self.last_used.month or now.year != self.last_used.year)):
            self.monthly_calls = 0
            self.monthly_cost = 0.0
        
        self.monthly_calls += 1
        self.monthly_cost += response.cost_incurred

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Dict[str, Any]
    timestamp: datetime
    source_type: DataSourceType
    quality_score: float
    ttl_hours: int = 24
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() - self.timestamp > timedelta(hours=self.ttl_hours)
    
    def is_stale(self, stale_threshold_hours: int = 6) -> bool:
        """Check if cache entry is getting stale"""
        return datetime.now() - self.timestamp > timedelta(hours=stale_threshold_hours)

class UnifiedDataAdapter:
    """
    Unified adapter for accessing financial data from multiple sources.
    
    Provides automatic fallback, caching, rate limiting, and cost management
    across all configured data sources.
    """
    
    def __init__(self, config_file: str = "data_sources_config.json", base_path: str = "."):
        """
        Initialize the unified data adapter.
        
        Args:
            config_file (str): Path to configuration file
            base_path (str): Base path for Excel files
        """
        self.config_file = Path(config_file)
        self.base_path = Path(base_path)
        self.providers: Dict[DataSourceType, Any] = {}
        self.configurations: Dict[DataSourceType, DataSourceConfig] = {}
        self.usage_stats: Dict[DataSourceType, UsageStatistics] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        
        # Load configuration
        self._load_configuration()
        
        # Initialize providers
        self._initialize_providers()
        
        # Load cache from disk
        self._load_cache()
        
        # Load usage statistics
        self._load_usage_stats()
        
        logger.info(f"Unified Data Adapter initialized with {len(self.providers)} providers")
    
    def _load_configuration(self):
        """Load data source configurations"""
        default_config = self._get_default_configuration()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for source_name, source_config in config_data.get('sources', {}).items():
                    try:
                        source_type = DataSourceType(source_name)
                        priority = DataSourcePriority(source_config.get('priority', 2))
                        
                        credentials = None
                        if 'credentials' in source_config:
                            cred_data = source_config['credentials']
                            credentials = ApiCredentials(
                                api_key=cred_data.get('api_key', ''),
                                base_url=cred_data.get('base_url', ''),
                                rate_limit_calls=cred_data.get('rate_limit_calls', 5),
                                rate_limit_period=cred_data.get('rate_limit_period', 60),
                                timeout=cred_data.get('timeout', 30),
                                retry_attempts=cred_data.get('retry_attempts', 3),
                                cost_per_call=cred_data.get('cost_per_call', 0.0),
                                monthly_limit=cred_data.get('monthly_limit', 1000),
                                is_active=cred_data.get('is_active', True)
                            )
                        
                        config = DataSourceConfig(
                            source_type=source_type,
                            priority=priority,
                            credentials=credentials,
                            is_enabled=source_config.get('is_enabled', True),
                            quality_threshold=source_config.get('quality_threshold', 0.8),
                            cache_ttl_hours=source_config.get('cache_ttl_hours', 24)
                        )
                        
                        self.configurations[source_type] = config
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid configuration for {source_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self.configurations = default_config
        else:
            logger.info("No configuration file found, using defaults")
            self.configurations = default_config
            self._save_configuration()
    
    def _get_default_configuration(self) -> Dict[DataSourceType, DataSourceConfig]:
        """Get default configuration for all data sources"""
        return {
            DataSourceType.EXCEL: DataSourceConfig(
                source_type=DataSourceType.EXCEL,
                priority=DataSourcePriority.FALLBACK,
                is_enabled=True,
                quality_threshold=0.7,
                cache_ttl_hours=48
            ),
            DataSourceType.YFINANCE: DataSourceConfig(
                source_type=DataSourceType.YFINANCE,
                priority=DataSourcePriority.PRIMARY,
                is_enabled=True,
                quality_threshold=0.8,
                cache_ttl_hours=2
            ),
            DataSourceType.ALPHA_VANTAGE: DataSourceConfig(
                source_type=DataSourceType.ALPHA_VANTAGE,
                priority=DataSourcePriority.SECONDARY,
                credentials=ApiCredentials(
                    api_key="",  # User needs to configure
                    base_url="https://www.alphavantage.co/query",
                    rate_limit_calls=5,
                    rate_limit_period=60,
                    cost_per_call=0.0,  # Free tier
                    monthly_limit=500
                ),
                is_enabled=False,  # Disabled until API key is configured
                quality_threshold=0.8,
                cache_ttl_hours=24
            ),
            DataSourceType.FINANCIAL_MODELING_PREP: DataSourceConfig(
                source_type=DataSourceType.FINANCIAL_MODELING_PREP,
                priority=DataSourcePriority.SECONDARY,
                credentials=ApiCredentials(
                    api_key="",  # User needs to configure
                    base_url="https://financialmodelingprep.com/api/v3",
                    rate_limit_calls=250,
                    rate_limit_period=3600,  # Per hour
                    cost_per_call=0.0,  # Free tier
                    monthly_limit=250
                ),
                is_enabled=False,  # Disabled until API key is configured
                quality_threshold=0.85,
                cache_ttl_hours=12
            ),
            DataSourceType.POLYGON: DataSourceConfig(
                source_type=DataSourceType.POLYGON,
                priority=DataSourcePriority.TERTIARY,
                credentials=ApiCredentials(
                    api_key="",  # User needs to configure
                    base_url="https://api.polygon.io",
                    rate_limit_calls=5,
                    rate_limit_period=60,
                    cost_per_call=0.003,  # Paid service
                    monthly_limit=1000
                ),
                is_enabled=False,  # Disabled until API key is configured
                quality_threshold=0.9,
                cache_ttl_hours=6
            )
        }
    
    def _save_configuration(self):
        """Save current configuration to file"""
        try:
            config_data = {
                'sources': {},
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            for source_type, config in self.configurations.items():
                source_data = {
                    'priority': config.priority.value,
                    'is_enabled': config.is_enabled,
                    'quality_threshold': config.quality_threshold,
                    'cache_ttl_hours': config.cache_ttl_hours
                }
                
                if config.credentials:
                    source_data['credentials'] = {
                        'api_key': config.credentials.api_key,
                        'base_url': config.credentials.base_url,
                        'rate_limit_calls': config.credentials.rate_limit_calls,
                        'rate_limit_period': config.credentials.rate_limit_period,
                        'timeout': config.credentials.timeout,
                        'retry_attempts': config.credentials.retry_attempts,
                        'cost_per_call': config.credentials.cost_per_call,
                        'monthly_limit': config.credentials.monthly_limit,
                        'is_active': config.credentials.is_active
                    }
                
                config_data['sources'][source_type.value] = source_data
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _initialize_providers(self):
        """Initialize data providers based on configuration"""
        for source_type, config in self.configurations.items():
            if not config.is_enabled:
                continue
            
            try:
                if source_type == DataSourceType.ALPHA_VANTAGE:
                    if config.credentials and config.credentials.api_key:
                        self.providers[source_type] = AlphaVantageProvider(config)
                        
                elif source_type == DataSourceType.FINANCIAL_MODELING_PREP:
                    if config.credentials and config.credentials.api_key:
                        self.providers[source_type] = FinancialModelingPrepProvider(config)
                        
                elif source_type == DataSourceType.POLYGON:
                    if config.credentials and config.credentials.api_key:
                        self.providers[source_type] = PolygonProvider(config)
                        
                elif source_type == DataSourceType.EXCEL:
                    self.providers[source_type] = ExcelDataProvider(config, str(self.base_path))
                    
                elif source_type == DataSourceType.YFINANCE:
                    # yfinance doesn't require API credentials
                    self.providers[source_type] = YfinanceProvider(config)
                
                # Initialize usage statistics
                if source_type not in self.usage_stats:
                    self.usage_stats[source_type] = UsageStatistics(source_type=source_type)
                    
                logger.info(f"Initialized {source_type.value} provider")
                
            except Exception as e:
                logger.error(f"Failed to initialize {source_type.value} provider: {e}")
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_file = self.base_path / "unified_data_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for key, entry_data in cache_data.items():
                    try:
                        entry = CacheEntry(
                            data=entry_data['data'],
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            source_type=DataSourceType(entry_data['source_type']),
                            quality_score=entry_data['quality_score'],
                            ttl_hours=entry_data.get('ttl_hours', 24)
                        )
                        
                        # Only load non-expired entries
                        if not entry.is_expired():
                            self.cache[key] = entry
                            
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid cache entry {key}: {e}")
                        continue
                
                logger.info(f"Loaded {len(self.cache)} cache entries")
                
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            cache_file = self.base_path / "unified_data_cache.json"
            cache_data = {}
            
            for key, entry in self.cache.items():
                if not entry.is_expired():
                    cache_data[key] = {
                        'data': entry.data,
                        'timestamp': entry.timestamp.isoformat(),
                        'source_type': entry.source_type.value,
                        'quality_score': entry.quality_score,
                        'ttl_hours': entry.ttl_hours
                    }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_usage_stats(self):
        """Load usage statistics from disk"""
        stats_file = self.base_path / "usage_statistics.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    stats_data = json.load(f)
                
                for source_name, stat_data in stats_data.items():
                    try:
                        source_type = DataSourceType(source_name)
                        stats = UsageStatistics(
                            source_type=source_type,
                            total_calls=stat_data.get('total_calls', 0),
                            total_cost=stat_data.get('total_cost', 0.0),
                            successful_calls=stat_data.get('successful_calls', 0),
                            failed_calls=stat_data.get('failed_calls', 0),
                            average_response_time=stat_data.get('average_response_time', 0.0),
                            monthly_calls=stat_data.get('monthly_calls', 0),
                            monthly_cost=stat_data.get('monthly_cost', 0.0)
                        )
                        
                        if stat_data.get('last_used'):
                            stats.last_used = datetime.fromisoformat(stat_data['last_used'])
                        
                        self.usage_stats[source_type] = stats
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid usage stat {source_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to load usage statistics: {e}")
    
    def _save_usage_stats(self):
        """Save usage statistics to disk"""
        try:
            stats_file = self.base_path / "usage_statistics.json"
            stats_data = {}
            
            for source_type, stats in self.usage_stats.items():
                stats_data[source_type.value] = {
                    'total_calls': stats.total_calls,
                    'total_cost': stats.total_cost,
                    'successful_calls': stats.successful_calls,
                    'failed_calls': stats.failed_calls,
                    'average_response_time': stats.average_response_time,
                    'monthly_calls': stats.monthly_calls,
                    'monthly_cost': stats.monthly_cost,
                    'last_used': stats.last_used.isoformat() if stats.last_used else None
                }
            
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save usage statistics: {e}")
    
    def _generate_cache_key(self, request: FinancialDataRequest) -> str:
        """Generate cache key for request"""
        key_data = {
            'ticker': request.ticker.upper(),
            'data_types': sorted(request.data_types),
            'period': request.period,
            'limit': request.limit
        }
        key_string = json.dumps(key_data, sort_keys=True)
        import hashlib
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_sorted_providers(self) -> List[Tuple[DataSourceType, Any]]:
        """Get providers sorted by priority"""
        provider_priorities = []
        
        for source_type, provider in self.providers.items():
            config = self.configurations.get(source_type)
            if config and config.is_enabled:
                # Check cost and usage limits
                stats = self.usage_stats.get(source_type)
                if self._can_use_provider(source_type, stats):
                    provider_priorities.append((config.priority.value, source_type, provider))
        
        # Sort by priority (lower number = higher priority)
        provider_priorities.sort(key=lambda x: x[0])
        
        return [(source_type, provider) for _, source_type, provider in provider_priorities]
    
    def _can_use_provider(self, source_type: DataSourceType, stats: Optional[UsageStatistics]) -> bool:
        """Check if provider can be used based on limits"""
        config = self.configurations.get(source_type)
        if not config or not config.credentials:
            return source_type == DataSourceType.EXCEL  # Excel doesn't need credentials
        
        if not config.credentials.is_active:
            return False
        
        if stats:
            # Check monthly limits
            if stats.monthly_calls >= config.credentials.monthly_limit:
                logger.warning(f"{source_type.value} monthly limit reached")
                return False
        
        return True
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """
        Fetch financial data using the best available source.
        
        Args:
            request (FinancialDataRequest): Data request parameters
            
        Returns:
            DataSourceResponse: Response with data or error information
        """
        with self._lock:
            # Check cache first (unless force refresh requested)
            if not request.force_refresh:
                cache_key = self._generate_cache_key(request)
                if cache_key in self.cache:
                    entry = self.cache[cache_key]
                    if not entry.is_expired():
                        logger.info(f"Cache hit for {request.ticker}")
                        response = DataSourceResponse(
                            success=True,
                            data=entry.data,
                            source_type=entry.source_type,
                            cache_hit=True
                        )
                        response.quality_metrics = DataQualityMetrics()
                        response.quality_metrics.overall_score = entry.quality_score
                        return response
            
            # Try providers in priority order
            sorted_providers = self._get_sorted_providers()
            
            for source_type, provider in sorted_providers:
                try:
                    logger.info(f"Trying {source_type.value} for {request.ticker}")
                    
                    response = provider.fetch_data(request)
                    
                    # Update usage statistics
                    if source_type in self.usage_stats:
                        self.usage_stats[source_type].update_stats(response)
                    
                    if response.success:
                        # Cache successful response
                        if response.data and response.quality_metrics:
                            config = self.configurations.get(source_type)
                            cache_key = self._generate_cache_key(request)
                            
                            entry = CacheEntry(
                                data=response.data,
                                timestamp=datetime.now(),
                                source_type=source_type,
                                quality_score=response.quality_metrics.overall_score,
                                ttl_hours=config.cache_ttl_hours if config else 24
                            )
                            
                            self.cache[cache_key] = entry
                        
                        logger.info(f"Successfully fetched data from {source_type.value}")
                        return response
                    else:
                        logger.warning(f"{source_type.value} failed: {response.error_message}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error with {source_type.value}: {e}")
                    continue
            
            # All providers failed
            logger.error(f"All data sources failed for {request.ticker}")
            return DataSourceResponse(
                success=False,
                error_message="All configured data sources failed"
            )
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive usage report"""
        report = {
            'total_cost': sum(stats.total_cost for stats in self.usage_stats.values()),
            'total_calls': sum(stats.total_calls for stats in self.usage_stats.values()),
            'monthly_cost': sum(stats.monthly_cost for stats in self.usage_stats.values()),
            'monthly_calls': sum(stats.monthly_calls for stats in self.usage_stats.values()),
            'sources': {},
            'cache_stats': {
                'total_entries': len(self.cache),
                'expired_entries': sum(1 for entry in self.cache.values() if entry.is_expired()),
                'cache_hit_rate': 0.0  # Would need to track hits vs misses
            }
        }
        
        for source_type, stats in self.usage_stats.items():
            config = self.configurations.get(source_type)
            report['sources'][source_type.value] = {
                'total_calls': stats.total_calls,
                'successful_calls': stats.successful_calls,
                'failed_calls': stats.failed_calls,
                'success_rate': stats.successful_calls / stats.total_calls if stats.total_calls > 0 else 0,
                'total_cost': stats.total_cost,
                'monthly_calls': stats.monthly_calls,
                'monthly_cost': stats.monthly_cost,
                'monthly_limit': config.credentials.monthly_limit if config and config.credentials else None,
                'average_response_time': stats.average_response_time,
                'last_used': stats.last_used.isoformat() if stats.last_used else None
            }
        
        return report
    
    def configure_source(self, source_type: DataSourceType, api_key: str, **kwargs):
        """Configure a data source with API key and options"""
        if source_type not in self.configurations:
            logger.error(f"Unknown source type: {source_type}")
            return False
        
        config = self.configurations[source_type]
        
        if config.credentials:
            config.credentials.api_key = api_key
            
            # Update optional parameters
            for key, value in kwargs.items():
                if hasattr(config.credentials, key):
                    setattr(config.credentials, key, value)
            
            config.credentials.is_active = True
            config.is_enabled = True
            
            # Re-initialize provider
            try:
                if source_type == DataSourceType.ALPHA_VANTAGE:
                    self.providers[source_type] = AlphaVantageProvider(config)
                elif source_type == DataSourceType.FINANCIAL_MODELING_PREP:
                    self.providers[source_type] = FinancialModelingPrepProvider(config)
                elif source_type == DataSourceType.POLYGON:
                    self.providers[source_type] = PolygonProvider(config)
                
                # Validate credentials
                if self.providers[source_type].validate_credentials():
                    logger.info(f"Successfully configured {source_type.value}")
                    self._save_configuration()
                    return True
                else:
                    logger.error(f"Invalid credentials for {source_type.value}")
                    config.is_enabled = False
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to configure {source_type.value}: {e}")
                return False
        
        return False
    
    def cleanup(self):
        """Clean up resources and save state"""
        try:
            self._save_cache()
            self._save_usage_stats()
            logger.info("Data adapter cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction