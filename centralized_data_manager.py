"""
Centralized Data Collection and Processing Manager

This module centralizes all data collection, processing, and caching operations
to eliminate redundancy and improve maintainability across the application.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import time
from functools import lru_cache
import hashlib

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
    
    def __init__(self, base_path: str, cache_dir: str = "data_cache"):
        """
        Initialize the centralized data manager.
        
        Args:
            base_path (str): Base directory path for data files
            cache_dir (str): Directory for caching data
        """
        self.base_path = Path(base_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache for fast access
        self._memory_cache: Dict[str, DataCacheEntry] = {}
        
        # Data standardization settings
        self.data_config = {
            'value_scale': 1000000,  # Store values in millions
            'date_format': '%Y-%m-%d',
            'decimal_places': 2,
            'missing_value_fill': 0
        }
        
        # Market data rate limiting with more conservative delays
        self._last_market_request = datetime.min
        self._market_request_delay = 3.0  # seconds
        
        # Load existing cache from disk
        self._load_persistent_cache()
        
        logger.info(f"Centralized Data Manager initialized for {base_path}")
    
    def _generate_cache_key(self, source: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key for data"""
        key_string = f"{source}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_persistent_cache(self):
        """Load cache from disk"""
        cache_file = self.cache_dir / "cache_index.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
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
                        'timestamp': entry.timestamp.isoformat(),
                        'hash_key': entry.hash_key,
                        'source': entry.source,
                        'expiry_hours': entry.expiry_hours
                    }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache if available and not expired"""
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for key: {cache_key}")
                return entry.data
            else:
                logger.debug(f"Cache expired for key: {cache_key}")
                del self._memory_cache[cache_key]
        return None
    
    def cache_data(self, cache_key: str, data: Any, source: str, expiry_hours: int = 24):
        """Store data in cache"""
        entry = DataCacheEntry(
            data=data,
            timestamp=datetime.now(),
            hash_key=cache_key,
            source=source,
            expiry_hours=expiry_hours
        )
        self._memory_cache[cache_key] = entry
        logger.debug(f"Cached data for key: {cache_key}")
    
    def load_excel_data(self, company_folder: str, force_reload: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Centralized Excel data loading with caching and standardization.
        
        Args:
            company_folder (str): Company folder name (e.g., 'TSLA', 'MSFT')
            force_reload (bool): Force reload even if cached data exists
            
        Returns:
            Dict[str, pd.DataFrame]: Standardized financial data
        """
        params = {'company_folder': company_folder}
        cache_key = self._generate_cache_key('excel_data', params)
        
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
            
            # Load FY (historical) data
            fy_path = company_path / "FY"
            if fy_path.exists():
                excel_data.update(self._load_excel_folder(fy_path, suffix='_fy'))
            
            # Load LTM (latest) data
            ltm_path = company_path / "LTM"
            if ltm_path.exists():
                excel_data.update(self._load_excel_folder(ltm_path, suffix='_ltm'))
            
            # Standardize data formats
            standardized_data = self._standardize_excel_data(excel_data)
            
            # Cache the results
            self.cache_data(cache_key, standardized_data, 'excel_data', expiry_hours=24)
            
            logger.info(f"Successfully loaded {len(standardized_data)} Excel datasets for {company_folder}")
            return standardized_data
            
        except Exception as e:
            logger.error(f"Error loading Excel data for {company_folder}: {e}")
            raise
    
    def _load_excel_folder(self, folder_path: Path, suffix: str) -> Dict[str, pd.DataFrame]:
        """Load Excel files from a specific folder"""
        excel_data = {}
        
        for excel_file in folder_path.glob("*.xlsx"):
            filename = excel_file.stem.lower()
            
            # Categorize files by type
            if 'balance' in filename:
                key = f'balance{suffix}'
            elif 'cash' in filename:
                key = f'cashflow{suffix}'
            elif 'income' in filename:
                key = f'income{suffix}'
            else:
                continue
            
            try:
                # Load Excel file
                df = pd.read_excel(excel_file, engine='openpyxl')
                excel_data[key] = df
                logger.debug(f"Loaded {excel_file.name} as {key}")
                
            except Exception as e:
                logger.error(f"Error loading {excel_file}: {e}")
                continue
        
        return excel_data
    
    def _standardize_excel_data(self, excel_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Standardize Excel data formats across all datasets"""
        standardized = {}
        
        for key, df in excel_data.items():
            if df.empty:
                continue
                
            # Create a copy for standardization - NO CONVERSION TO MILLIONS YET
            # The existing financial_calculations.py expects raw data
            df_std = df.copy()
            
            # Standardize column names (remove extra spaces, normalize case)
            df_std.columns = df_std.columns.str.strip()
            
            # Handle missing values but don't convert to millions yet
            df_std = df_std.fillna(self.data_config['missing_value_fill'])
            
            # Store standardized data
            standardized[key] = df_std
            
        return standardized
    
    def fetch_market_data(self, ticker: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Centralized market data fetching with rate limiting and caching.
        
        Args:
            ticker (str): Stock ticker symbol
            force_reload (bool): Force reload even if cached data exists
            
        Returns:
            Optional[Dict[str, Any]]: Market data or None if failed
        """
        params = {'ticker': ticker.upper()}
        cache_key = self._generate_cache_key('market_data', params)
        
        # Check cache first
        if not force_reload:
            cached_data = self.get_cached_data(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached market data for {ticker}")
                return cached_data
        
        # Rate limiting
        time_since_last = (datetime.now() - self._last_market_request).total_seconds()
        if time_since_last < self._market_request_delay:
            sleep_time = self._market_request_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        logger.info(f"Fetching market data for {ticker}")
        
        try:
            import yfinance as yf
            
            # Retry logic for rate limiting with longer delays
            max_retries = 5
            retry_delay = 3
            
            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Extract market data with multiple fallbacks
                    market_data = self._extract_market_data(info, stock)
                    
                    if market_data:
                        # Cache the results
                        self.cache_data(cache_key, market_data, 'market_data', expiry_hours=1)
                        self._last_market_request = datetime.now()
                        
                        logger.info(f"Successfully fetched market data for {ticker}")
                        return market_data
                    
                    break
                    
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Rate limited, retrying in {retry_delay} seconds... (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    else:
                        raise e
            
            logger.warning(f"Failed to fetch market data for {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data for {ticker}: {e}")
            return None
    
    def _extract_market_data(self, info: Dict[str, Any], stock) -> Optional[Dict[str, Any]]:
        """Extract and standardize market data from yfinance response"""
        try:
            # Get current price with fallbacks
            current_price = (info.get('currentPrice') or 
                           info.get('regularMarketPrice') or 
                           info.get('previousClose'))
            
            # Try historical data if no current price
            if not current_price:
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Get shares outstanding with multiple fallbacks
            shares_outstanding = (info.get('sharesOutstanding') or 
                                info.get('impliedSharesOutstanding') or 
                                info.get('basicAvgSharesOutstanding') or 
                                info.get('weightedAvgSharesOutstanding'))
            
            # Get market cap with fallbacks
            market_cap = (info.get('marketCap') or 
                         info.get('enterpriseValue'))
            
            # Calculate missing values if possible
            if current_price and market_cap and not shares_outstanding:
                shares_outstanding = market_cap / current_price
            elif current_price and shares_outstanding and not market_cap:
                market_cap = current_price * shares_outstanding
            
            if not current_price:
                return None
            
            # Standardize to millions
            return {
                'ticker': info.get('symbol', '').upper(),
                'company_name': (info.get('longName') or 
                               info.get('shortName') or 
                               info.get('symbol', '')),
                'current_price': float(current_price),
                'shares_outstanding': float(shares_outstanding) if shares_outstanding else 0,
                'market_cap': float(market_cap) / self.data_config['value_scale'] if market_cap else 0,
                'currency': info.get('currency', 'USD'),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting market data: {e}")
            return None
    
    def get_company_data(self, company_folder: str, include_market_data: bool = True) -> Dict[str, Any]:
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
            'ticker': ticker,
            'financial_data': financial_data,
            'market_data': None,
            'metadata': {
                'data_collection_time': datetime.now().isoformat(),
                'data_source': 'centralized_data_manager',
                'financial_data_count': len(financial_data)
            }
        }
        
        # Add market data if requested
        if include_market_data:
            market_data = self.fetch_market_data(ticker)
            result['market_data'] = market_data
            if market_data:
                result['metadata']['market_data_available'] = True
            else:
                result['metadata']['market_data_available'] = False
        
        return result
    
    def clear_cache(self, cache_type: str = 'all'):
        """
        Clear cached data.
        
        Args:
            cache_type (str): Type of cache to clear ('all', 'excel_data', 'market_data')
        """
        if cache_type == 'all':
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
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'source_breakdown': source_counts,
            'cache_directory': str(self.cache_dir)
        }
    
    def __del__(self):
        """Cleanup and save cache on destruction"""
        try:
            self._save_persistent_cache()
        except:
            pass  # Ignore errors during cleanup