"""
Real-Time Price Fetching Service

This module provides a unified service for fetching real-time price data from multiple
financial API sources with caching, fallback logic, and manual refresh capabilities.

Features:
- Multi-source price fetching (yfinance, Alpha Vantage, FMP, Polygon)
- 15-minute intelligent caching with timestamps
- Manual refresh capability
- Graceful degradation and fallback logic
- Background price update capability
- Error handling and logging
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing data source infrastructure
from .interfaces.data_sources import (
    DataSourceType, 
    DataSourcePriority, 
    ApiCredentials, 
    DataSourceConfig, 
    FinancialDataRequest, 
    DataSourceResponse,
    AlphaVantageProvider,
    FinancialModelingPrepProvider,
    PolygonProvider,
    YfinanceProvider
)

# Import enhanced logging
try:
    from utils.logging_config import get_api_logger, get_data_logger, log_exception
    logger = get_api_logger()
    data_logger = get_data_logger()
except ImportError:
    # Fallback to standard logging if utils not available
    import logging
    logger = logging.getLogger(__name__)
    data_logger = logger
    
    def log_exception(context, exception, **kwargs):
        logger.error(f"Exception in {context}: {exception}", exc_info=True)


@dataclass
class PriceData:
    """Container for real-time price data"""
    ticker: str
    current_price: float
    change_percent: float = 0.0
    volume: int = 0
    market_cap: float = 0.0
    timestamp: datetime = None
    source: str = "unknown"
    currency: str = "USD"
    last_updated: datetime = None
    cache_hit: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class PriceCacheEntry:
    """Cache entry for price data with metadata"""
    price_data: PriceData
    cached_at: datetime
    expires_at: datetime
    source_priority: int
    fetch_success: bool = True
    error_message: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at
    
    def is_fresh(self, max_age_minutes: int = 15) -> bool:
        """Check if cache entry is still fresh"""
        age = (datetime.now() - self.cached_at).total_seconds() / 60
        return age <= max_age_minutes


class RealTimePriceService:
    """
    Real-time price fetching service with multi-source support and intelligent caching
    """
    
    def __init__(self, cache_dir: Optional[str] = None, cache_ttl_minutes: int = 15):
        """
        Initialize the Real-Time Price Service
        
        Args:
            cache_dir: Directory for persistent cache (optional)
            cache_ttl_minutes: Cache time-to-live in minutes (default: 15)
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache/prices")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for fast access
        self._memory_cache: Dict[str, PriceCacheEntry] = {}
        
        # Configuration for data source providers
        self._providers: Dict[DataSourceType, Any] = {}
        self._provider_configs: Dict[DataSourceType, DataSourceConfig] = {}
        
        # Thread pool for concurrent API calls
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize data source providers
        self._initialize_providers()
        
        logger.info(f"RealTimePriceService initialized with cache TTL: {cache_ttl_minutes} minutes")
    
    def _initialize_providers(self):
        """Initialize all available data source providers with configuration"""
        
        # yfinance (highest priority - free and reliable)
        yf_config = DataSourceConfig(
            source_type=DataSourceType.YFINANCE,
            priority=DataSourcePriority.PRIMARY,
            is_enabled=True,
            cache_ttl_hours=1
        )
        try:
            self._providers[DataSourceType.YFINANCE] = YfinanceProvider(yf_config)
            self._provider_configs[DataSourceType.YFINANCE] = yf_config
            logger.debug("yfinance provider initialized successfully")
        except Exception as e:
            logger.warning(f"yfinance provider initialization failed: {e}")
        
        # Alpha Vantage (secondary)
        av_api_key = self._get_api_key("ALPHA_VANTAGE_API_KEY")
        if av_api_key:
            av_credentials = ApiCredentials(
                api_key=av_api_key,
                base_url="https://www.alphavantage.co/query",
                rate_limit_calls=5,
                rate_limit_period=60,
                cost_per_call=0.0
            )
            av_config = DataSourceConfig(
                source_type=DataSourceType.ALPHA_VANTAGE,
                priority=DataSourcePriority.SECONDARY,
                credentials=av_credentials,
                is_enabled=True
            )
            try:
                self._providers[DataSourceType.ALPHA_VANTAGE] = AlphaVantageProvider(av_config)
                self._provider_configs[DataSourceType.ALPHA_VANTAGE] = av_config
                logger.debug("Alpha Vantage provider initialized successfully")
            except Exception as e:
                logger.warning(f"Alpha Vantage provider initialization failed: {e}")
        
        # Financial Modeling Prep (tertiary)
        fmp_api_key = self._get_api_key("FMP_API_KEY")
        if fmp_api_key:
            fmp_credentials = ApiCredentials(
                api_key=fmp_api_key,
                base_url="https://financialmodelingprep.com/api/v3",
                rate_limit_calls=250,
                rate_limit_period=60,
                cost_per_call=0.0
            )
            fmp_config = DataSourceConfig(
                source_type=DataSourceType.FINANCIAL_MODELING_PREP,
                priority=DataSourcePriority.TERTIARY,
                credentials=fmp_credentials,
                is_enabled=True
            )
            try:
                self._providers[DataSourceType.FINANCIAL_MODELING_PREP] = FinancialModelingPrepProvider(fmp_config)
                self._provider_configs[DataSourceType.FINANCIAL_MODELING_PREP] = fmp_config
                logger.debug("Financial Modeling Prep provider initialized successfully")
            except Exception as e:
                logger.warning(f"Financial Modeling Prep provider initialization failed: {e}")
        
        # Polygon.io (fallback)
        polygon_api_key = self._get_api_key("POLYGON_API_KEY")
        if polygon_api_key:
            polygon_credentials = ApiCredentials(
                api_key=polygon_api_key,
                base_url="https://api.polygon.io",
                rate_limit_calls=5,
                rate_limit_period=60,
                cost_per_call=0.0
            )
            polygon_config = DataSourceConfig(
                source_type=DataSourceType.POLYGON,
                priority=DataSourcePriority.FALLBACK,
                credentials=polygon_credentials,
                is_enabled=True
            )
            try:
                self._providers[DataSourceType.POLYGON] = PolygonProvider(polygon_config)
                self._provider_configs[DataSourceType.POLYGON] = polygon_config
                logger.debug("Polygon provider initialized successfully")
            except Exception as e:
                logger.warning(f"Polygon provider initialization failed: {e}")
        
        if not self._providers:
            logger.error("No data source providers could be initialized!")
        else:
            logger.info(f"Initialized {len(self._providers)} data source providers")
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from environment or configuration"""
        import os
        return os.getenv(key_name)
    
    async def get_real_time_price(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """
        Get real-time price data for a ticker with caching support
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Force refresh from API, bypassing cache
            
        Returns:
            PriceData object or None if all sources fail
        """
        ticker = ticker.upper()
        logger.info(f"Fetching real-time price for {ticker}, force_refresh={force_refresh}")
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self._get_cached_price(ticker)
            if cached_data and cached_data.is_fresh(self.cache_ttl_minutes):
                logger.debug(f"Returning cached price for {ticker}")
                cached_data.price_data.cache_hit = True
                return cached_data.price_data
        
        # Fetch fresh data from providers
        price_data = await self._fetch_price_from_providers(ticker)
        
        if price_data:
            # Cache the successful result
            self._cache_price_data(ticker, price_data)
            logger.info(f"Successfully fetched and cached price for {ticker}: ${price_data.current_price:.2f}")
        else:
            logger.error(f"Failed to fetch price for {ticker} from any source")
            
            # Try to return stale cache data as fallback
            cached_data = self._get_cached_price(ticker)
            if cached_data:
                logger.warning(f"Returning stale cached price for {ticker}")
                cached_data.price_data.cache_hit = True
                return cached_data.price_data
        
        return price_data
    
    async def get_multiple_prices(self, tickers: List[str], force_refresh: bool = False) -> Dict[str, Optional[PriceData]]:
        """
        Get real-time prices for multiple tickers concurrently
        
        Args:
            tickers: List of ticker symbols
            force_refresh: Force refresh from API, bypassing cache
            
        Returns:
            Dictionary mapping tickers to PriceData objects
        """
        logger.info(f"Fetching prices for {len(tickers)} tickers")
        
        # Create concurrent tasks for all tickers
        tasks = []
        for ticker in tickers:
            task = asyncio.create_task(self.get_real_time_price(ticker, force_refresh))
            tasks.append((ticker.upper(), task))
        
        # Wait for all tasks to complete
        results = {}
        for ticker, task in tasks:
            try:
                results[ticker] = await task
            except Exception as e:
                logger.error(f"Failed to fetch price for {ticker}: {e}")
                results[ticker] = None
        
        return results
    
    async def _fetch_price_from_providers(self, ticker: str) -> Optional[PriceData]:
        """
        Fetch price data from providers in priority order with fallback logic
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            PriceData object or None if all providers fail
        """
        # Sort providers by priority
        sorted_providers = sorted(
            self._providers.items(),
            key=lambda x: self._provider_configs[x[0]].priority.value
        )
        
        logger.debug(f"Trying {len(sorted_providers)} providers for {ticker}")
        
        for source_type, provider in sorted_providers:
            if not self._provider_configs[source_type].is_enabled:
                continue
                
            try:
                logger.debug(f"Fetching price for {ticker} from {source_type.value}")
                
                # Create request for price data only
                request = FinancialDataRequest(
                    ticker=ticker,
                    data_types=['price'],
                    force_refresh=True
                )
                
                # Fetch data from provider
                response = provider.fetch_data(request)
                
                if response.success and response.data:
                    # Convert provider response to PriceData
                    price_data = self._convert_to_price_data(ticker, response, source_type)
                    if price_data:
                        logger.debug(f"Successfully fetched price for {ticker} from {source_type.value}: ${price_data.current_price:.2f}")
                        return price_data
                else:
                    logger.warning(f"Provider {source_type.value} failed for {ticker}: {response.error_message}")
                    
            except Exception as e:
                logger.error(f"Provider {source_type.value} error for {ticker}: {e}")
                log_exception(f"RealTimePriceService_{source_type.value}", e, ticker=ticker)
                continue
        
        logger.error(f"All providers failed for {ticker}")
        return None
    
    def _convert_to_price_data(self, ticker: str, response: DataSourceResponse, source_type: DataSourceType) -> Optional[PriceData]:
        """Convert provider response to standardized PriceData"""
        try:
            data = response.data
            if not data:
                return None
            
            # Extract price information from different provider formats
            current_price = data.get('current_price', 0.0)
            if current_price <= 0:
                # Try alternative price fields
                current_price = data.get('price', data.get('last_price', 0.0))
            
            if current_price <= 0:
                logger.warning(f"No valid price found in {source_type.value} response for {ticker}")
                return None
            
            price_data = PriceData(
                ticker=ticker,
                current_price=float(current_price),
                change_percent=float(data.get('change_percent', 0.0)),
                volume=int(data.get('volume', 0)),
                market_cap=float(data.get('market_cap', 0.0)),
                source=f"{source_type.value}_price",
                last_updated=datetime.now()
            )
            
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to convert {source_type.value} response for {ticker}: {e}")
            log_exception("PriceDataConversion", e, ticker=ticker, source_type=source_type.value)
            return None
    
    def _get_cached_price(self, ticker: str) -> Optional[PriceCacheEntry]:
        """Get cached price data for a ticker"""
        # Check in-memory cache first
        if ticker in self._memory_cache:
            entry = self._memory_cache[ticker]
            if not entry.is_expired():
                return entry
            else:
                # Remove expired entry
                del self._memory_cache[ticker]
        
        # Check persistent cache
        return self._load_from_persistent_cache(ticker)
    
    def _cache_price_data(self, ticker: str, price_data: PriceData):
        """Cache price data in both memory and persistent storage"""
        expires_at = datetime.now() + timedelta(minutes=self.cache_ttl_minutes)
        
        cache_entry = PriceCacheEntry(
            price_data=price_data,
            cached_at=datetime.now(),
            expires_at=expires_at,
            source_priority=self._get_source_priority(price_data.source),
            fetch_success=True
        )
        
        # Store in memory cache
        self._memory_cache[ticker] = cache_entry
        
        # Store in persistent cache
        self._save_to_persistent_cache(ticker, cache_entry)
        
        logger.debug(f"Cached price data for {ticker}, expires at {expires_at}")
    
    def _get_source_priority(self, source: str) -> int:
        """Get priority value for data source"""
        source_priorities = {
            'yfinance': 1,
            'alpha_vantage': 2,
            'fmp': 3,
            'financial_modeling_prep': 3,
            'polygon': 4
        }
        
        for key, priority in source_priorities.items():
            if key in source.lower():
                return priority
        return 5  # Unknown source gets lowest priority
    
    def _load_from_persistent_cache(self, ticker: str) -> Optional[PriceCacheEntry]:
        """Load cached price data from persistent storage"""
        cache_file = self.cache_dir / f"{ticker}_price.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Reconstruct cache entry
            price_data = PriceData(
                ticker=cache_data['price_data']['ticker'],
                current_price=cache_data['price_data']['current_price'],
                change_percent=cache_data['price_data']['change_percent'],
                volume=cache_data['price_data']['volume'],
                market_cap=cache_data['price_data']['market_cap'],
                timestamp=datetime.fromisoformat(cache_data['price_data']['timestamp']),
                source=cache_data['price_data']['source'],
                currency=cache_data['price_data'].get('currency', 'USD'),
                last_updated=datetime.fromisoformat(cache_data['price_data']['last_updated'])
            )
            
            cache_entry = PriceCacheEntry(
                price_data=price_data,
                cached_at=datetime.fromisoformat(cache_data['cached_at']),
                expires_at=datetime.fromisoformat(cache_data['expires_at']),
                source_priority=cache_data['source_priority'],
                fetch_success=cache_data.get('fetch_success', True),
                error_message=cache_data.get('error_message')
            )
            
            # Check if still valid
            if not cache_entry.is_expired():
                # Move to memory cache for faster access
                self._memory_cache[ticker] = cache_entry
                return cache_entry
            else:
                # Remove expired cache file
                cache_file.unlink()
                
        except Exception as e:
            logger.warning(f"Failed to load persistent cache for {ticker}: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
        
        return None
    
    def _save_to_persistent_cache(self, ticker: str, cache_entry: PriceCacheEntry):
        """Save price data to persistent cache"""
        cache_file = self.cache_dir / f"{ticker}_price.json"
        
        try:
            # Convert cache entry to serializable format
            cache_data = {
                'price_data': {
                    'ticker': cache_entry.price_data.ticker,
                    'current_price': cache_entry.price_data.current_price,
                    'change_percent': cache_entry.price_data.change_percent,
                    'volume': cache_entry.price_data.volume,
                    'market_cap': cache_entry.price_data.market_cap,
                    'timestamp': cache_entry.price_data.timestamp.isoformat(),
                    'source': cache_entry.price_data.source,
                    'currency': cache_entry.price_data.currency,
                    'last_updated': cache_entry.price_data.last_updated.isoformat()
                },
                'cached_at': cache_entry.cached_at.isoformat(),
                'expires_at': cache_entry.expires_at.isoformat(),
                'source_priority': cache_entry.source_priority,
                'fetch_success': cache_entry.fetch_success,
                'error_message': cache_entry.error_message
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save persistent cache for {ticker}: {e}")
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear cached price data
        
        Args:
            ticker: Specific ticker to clear, or None to clear all cache
        """
        if ticker:
            ticker = ticker.upper()
            # Clear from memory
            self._memory_cache.pop(ticker, None)
            
            # Clear from persistent storage
            cache_file = self.cache_dir / f"{ticker}_price.json"
            if cache_file.exists():
                cache_file.unlink()
                
            logger.info(f"Cleared cache for {ticker}")
        else:
            # Clear all cache
            self._memory_cache.clear()
            
            # Clear all persistent cache files
            for cache_file in self.cache_dir.glob("*_price.json"):
                cache_file.unlink()
                
            logger.info("Cleared all price cache")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        memory_count = len(self._memory_cache)
        persistent_count = len(list(self.cache_dir.glob("*_price.json")))
        
        # Count fresh vs expired entries
        fresh_count = 0
        expired_count = 0
        
        for entry in self._memory_cache.values():
            if entry.is_fresh(self.cache_ttl_minutes):
                fresh_count += 1
            else:
                expired_count += 1
        
        return {
            'memory_cache_entries': memory_count,
            'persistent_cache_entries': persistent_count,
            'fresh_entries': fresh_count,
            'expired_entries': expired_count,
            'cache_ttl_minutes': self.cache_ttl_minutes,
            'providers_initialized': len(self._providers),
            'cache_directory': str(self.cache_dir)
        }
    
    def refresh_prices_background(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Refresh prices for tickers in the background (non-blocking)
        
        Args:
            tickers: List of ticker symbols to refresh
            
        Returns:
            Dictionary of ticker -> success status
        """
        logger.info(f"Starting background refresh for {len(tickers)} tickers")
        
        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            future_to_ticker = {}
            for ticker in tickers:
                future = executor.submit(self._sync_fetch_price, ticker)
                future_to_ticker[future] = ticker.upper()
            
            # Collect results as they complete
            for future in as_completed(future_to_ticker, timeout=30):
                ticker = future_to_ticker[future]
                try:
                    price_data = future.result()
                    results[ticker] = price_data is not None
                    if price_data:
                        self._cache_price_data(ticker, price_data)
                        logger.debug(f"Background refresh succeeded for {ticker}")
                    else:
                        logger.warning(f"Background refresh failed for {ticker}")
                except Exception as e:
                    logger.error(f"Background refresh error for {ticker}: {e}")
                    results[ticker] = False
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Background refresh completed: {success_count}/{len(tickers)} successful")
        
        return results
    
    def _sync_fetch_price(self, ticker: str) -> Optional[PriceData]:
        """Synchronous wrapper for fetching price data (for thread pool)"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._fetch_price_from_providers(ticker))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync fetch error for {ticker}: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self._executor.shutdown(wait=True)
        logger.info("RealTimePriceService shutdown completed")


# Convenience functions for easy integration

def create_price_service(cache_dir: Optional[str] = None, cache_ttl_minutes: int = 15) -> RealTimePriceService:
    """
    Factory function to create a RealTimePriceService instance
    
    Args:
        cache_dir: Directory for persistent cache
        cache_ttl_minutes: Cache time-to-live in minutes
        
    Returns:
        Configured RealTimePriceService instance
    """
    return RealTimePriceService(cache_dir=cache_dir, cache_ttl_minutes=cache_ttl_minutes)


async def get_current_price(ticker: str, force_refresh: bool = False) -> Optional[float]:
    """
    Quick function to get current price for a ticker
    
    Args:
        ticker: Stock ticker symbol
        force_refresh: Force refresh from API
        
    Returns:
        Current price as float or None if failed
    """
    async with create_price_service() as service:
        price_data = await service.get_real_time_price(ticker, force_refresh)
        return price_data.current_price if price_data else None


async def get_current_prices(tickers: List[str], force_refresh: bool = False) -> Dict[str, Optional[float]]:
    """
    Quick function to get current prices for multiple tickers
    
    Args:
        tickers: List of ticker symbols
        force_refresh: Force refresh from API
        
    Returns:
        Dictionary mapping tickers to prices (or None if failed)
    """
    async with create_price_service() as service:
        price_data_dict = await service.get_multiple_prices(tickers, force_refresh)
        return {
            ticker: data.current_price if data else None 
            for ticker, data in price_data_dict.items()
        }


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    
    async def test_price_service():
        """Test the price service with sample tickers"""
        async with create_price_service() as service:
            print("Real-Time Price Service Test")
            print("=" * 40)
            
            # Test single ticker
            print(f"Cache status: {service.get_cache_status()}")
            
            ticker = "AAPL"
            price_data = await service.get_real_time_price(ticker)
            if price_data:
                print(f"{ticker}: ${price_data.current_price:.2f} (Source: {price_data.source})")
                print(f"Change: {price_data.change_percent:.2f}%, Volume: {price_data.volume:,}")
            
            # Test multiple tickers
            tickers = ["MSFT", "GOOGL", "AMZN"]
            prices = await service.get_multiple_prices(tickers)
            
            print("\nMultiple ticker test:")
            for ticker, data in prices.items():
                if data:
                    print(f"{ticker}: ${data.current_price:.2f} (Cache: {data.cache_hit})")
                else:
                    print(f"{ticker}: Failed to fetch")
            
            print(f"\nFinal cache status: {service.get_cache_status()}")
    
    # Run test if executed directly
    asyncio.run(test_price_service())