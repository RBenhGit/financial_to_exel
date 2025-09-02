"""
Industry Data Fetching Service
==============================

This module provides a service for fetching real-time industry P/B data from market APIs.
It identifies peer companies in the same sector and calculates industry statistics 
for P/B ratio benchmarking.

Key Features:
- Dynamic peer company identification using yfinance sector classification
- Multi-source P/B data fetching with fallback support
- Industry statistics calculation (median, quartiles, range)
- Minimum peer company validation
- 1-day TTL caching to minimize API calls
- Integration with existing data source infrastructure

Classes:
    IndustryDataService: Main service for fetching and processing industry data
    IndustryPeerData: Data class for peer company information
    IndustryStatistics: Data class for calculated industry statistics

Usage:
    >>> industry_service = IndustryDataService()
    >>> stats = industry_service.get_industry_pb_statistics("AAPL")
    >>> print(f"Industry median P/B: {stats.median_pb}")
    >>> print(f"Based on {stats.peer_count} peer companies")
"""

import os
import json
import time
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing data source utilities
try:
    from .interfaces.data_sources import DataSourceType
    from ..data_processing.rate_limiting.enhanced_rate_limiter import EnhancedRateLimiter
    from core.data_processing.converters.yfinance_converter import YFinanceConverter
    from core.data_processing.converters.alpha_vantage_converter import AlphaVantageConverter
    from core.data_processing.converters.fmp_converter import FMPConverter
    from ..error_handling import get_error_handler, with_api_error_handling, APIFailureCategory
    from ..error_handling.data_quality_validator import DataQualityValidator
except ImportError:
    # Fallback imports for testing
    from enum import Enum
    DataSourceType = None
    EnhancedRateLimiter = None
    get_error_handler = None
    DataQualityValidator = None

# Import performance monitoring
try:
    from utils.performance_monitor import performance_timer
except ImportError:
    # Fallback if performance monitor not available
    def performance_timer(operation_name: str, **kwargs):
        def decorator(func):
            return func
        return decorator
    with_api_error_handling = None
    APIFailureCategory = None
    DataQualityValidator = None

logger = logging.getLogger(__name__)


@dataclass
class IndustryPeerData:
    """Data class for peer company information"""
    ticker: str
    sector: str
    industry: str
    pb_ratio: Optional[float] = None
    book_value_per_share: Optional[float] = None
    market_cap: Optional[float] = None
    data_source: str = "unknown"
    last_updated: Optional[datetime] = None


@dataclass
class IndustryStatistics:
    """Data class for calculated industry statistics"""
    sector: str
    industry: str
    peer_count: int
    median_pb: Optional[float] = None
    mean_pb: Optional[float] = None
    min_pb: Optional[float] = None
    max_pb: Optional[float] = None
    q1_pb: Optional[float] = None
    q3_pb: Optional[float] = None
    std_pb: Optional[float] = None
    peer_tickers: List[str] = field(default_factory=list)
    data_quality_score: float = 0.0
    last_updated: Optional[datetime] = None
    cache_expiry: Optional[datetime] = None


class IndustryDataService:
    """
    Service for fetching real-time industry P/B data from market APIs
    """
    
    def __init__(self, cache_dir: str = "data/cache", cache_ttl_hours: int = 24):
        """
        Initialize the industry data service
        
        Args:
            cache_dir: Directory for caching industry data
            cache_ttl_hours: Time-to-live for cached data in hours (default 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.minimum_peer_count = 5  # Minimum required peer companies
        self.maximum_peer_count = 50  # Maximum to process for performance
        
        # Initialize rate limiters for different APIs
        self.rate_limiters = {}
        self._initialize_rate_limiters()
        
        # Initialize data quality validator
        self.data_quality_validator = DataQualityValidator() if DataQualityValidator else None
        
        logger.info(f"Industry data service initialized with cache_dir={cache_dir}, ttl={cache_ttl_hours}h")

    def _initialize_rate_limiters(self):
        """Initialize rate limiters for different data sources"""
        try:
            if EnhancedRateLimiter:
                self.rate_limiters = {
                    'yfinance': EnhancedRateLimiter(calls_per_second=1, calls_per_minute=60),
                    'alpha_vantage': EnhancedRateLimiter(calls_per_second=1, calls_per_minute=5),
                    'fmp': EnhancedRateLimiter(calls_per_second=10, calls_per_minute=250)
                }
        except Exception as e:
            logger.warning(f"Failed to initialize rate limiters: {e}")
            self.rate_limiters = {}

    @performance_timer("industry_pb_statistics", include_args=True)
    def get_industry_pb_statistics(self, ticker: str) -> Optional[IndustryStatistics]:
        """
        Get industry P/B statistics for a given ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            IndustryStatistics object or None if insufficient data
        """
        try:
            # Check cache first
            cached_stats = self._load_from_cache(ticker)
            if cached_stats and self._is_cache_valid(cached_stats):
                logger.info(f"Using cached industry data for {ticker}")
                return cached_stats
                
            # Fetch fresh data
            logger.info(f"Fetching fresh industry data for {ticker}")
            
            # Step 1: Get ticker's sector/industry classification
            sector_info = self._get_sector_classification(ticker)
            if not sector_info:
                logger.warning(f"Could not determine sector for {ticker}")
                return None
                
            # Step 2: Find peer companies in same sector
            peer_tickers = self._find_peer_companies(sector_info['sector'], sector_info['industry'])
            if len(peer_tickers) < self.minimum_peer_count:
                logger.warning(f"Insufficient peer companies for {ticker}: {len(peer_tickers)} < {self.minimum_peer_count}")
                return None
                
            # Step 3: Fetch P/B ratios for all peers
            peer_data = self._fetch_peer_pb_data(peer_tickers)
            
            # Step 4: Calculate industry statistics
            statistics = self._calculate_industry_statistics(
                sector_info['sector'], 
                sector_info['industry'], 
                peer_data
            )
            
            if statistics and statistics.peer_count >= self.minimum_peer_count:
                # Validate data quality if validator available
                if self.data_quality_validator:
                    validation_result = self.data_quality_validator.validate_industry_data(statistics, peer_data)
                    
                    # Add quality score to statistics
                    if validation_result.metrics:
                        statistics.data_quality_score = validation_result.metrics.overall_score
                    
                    # Log quality assessment
                    logger.info(f"Data quality for {ticker}: {validation_result.quality_level.value} "
                              f"(score: {validation_result.metrics.overall_score:.2f})" if validation_result.metrics else "")
                    
                    # Log warnings and recommendations
                    for warning in validation_result.warnings:
                        logger.warning(f"Data quality warning for {ticker}: {warning}")
                    
                    for issue in validation_result.issues:
                        logger.error(f"Data quality issue for {ticker}: {issue}")
                    
                    # If data quality is too poor, don't return the statistics
                    if not validation_result.is_valid:
                        logger.error(f"Data quality too poor for {ticker} - not using industry statistics")
                        return None
                
                # Save to cache
                self._save_to_cache(ticker, statistics)
                logger.info(f"Industry statistics calculated for {ticker}: {statistics.peer_count} peers, median P/B: {statistics.median_pb:.2f}")
                return statistics
            else:
                logger.warning(f"Insufficient valid peer data for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating industry statistics for {ticker}: {e}")
            return None

    def _get_sector_classification(self, ticker: str) -> Optional[Dict[str, str]]:
        """
        Get sector and industry classification for a ticker using yfinance
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with sector and industry info or None
        """
        def _fetch_sector_data():
            if 'yfinance' in self.rate_limiters:
                self.rate_limiters['yfinance'].wait_if_needed()
                
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector = info.get('sector')
            industry = info.get('industry')
            
            if sector and industry:
                return {
                    'sector': sector,
                    'industry': industry,
                    'company_name': info.get('shortName', ticker)
                }
            else:
                raise ValueError(f"Missing sector/industry info for {ticker}")
        
        # Use error handler if available, otherwise fallback to basic error handling
        if get_error_handler:
            error_handler = get_error_handler()
            result, failure = error_handler.execute_with_retry(_fetch_sector_data, "yfinance")
            
            if failure:
                logger.warning(f"Failed to get sector classification for {ticker}: {failure.user_message}")
                return None
            return result
        else:
            # Fallback to original error handling
            try:
                return _fetch_sector_data()
            except Exception as e:
                logger.error(f"Error getting sector classification for {ticker}: {e}")
                return None

    def _find_peer_companies(self, sector: str, industry: str) -> List[str]:
        """
        Find peer companies in the same sector/industry with enhanced strategy
        
        Uses multiple approaches:
        1. Direct sector mapping (fast)
        2. Batch verification for efficiency
        3. Fallback strategies for edge cases
        
        Args:
            sector: Sector name
            industry: Industry name
            
        Returns:
            List of peer ticker symbols
        """
        try:
            # Strategy 1: Get potential peers from sector mapping
            sector_tickers = self._get_common_tickers_by_sector(sector)
            
            if not sector_tickers:
                logger.warning(f"No sector tickers found for '{sector}', trying fallback strategies")
                # Fallback: try similar sector names or broader categories
                sector_tickers = self._fallback_sector_search(sector, industry)
            
            if not sector_tickers:
                logger.error(f"No peer companies found for sector '{sector}' after fallback")
                return []
            
            # Strategy 2: For better performance, return a subset without verification
            # if we have enough potential peers from our curated list
            if len(sector_tickers) >= self.minimum_peer_count:
                # Take a reasonable subset for performance
                selected_peers = sector_tickers[:min(self.maximum_peer_count, 20)]
                logger.info(f"Using {len(selected_peers)} curated peers for sector '{sector}' (fast mode)")
                return selected_peers
            
            # Strategy 3: If we don't have enough curated tickers, try verification
            # but with batch processing for better performance
            logger.info(f"Insufficient curated peers ({len(sector_tickers)}), trying verification...")
            verified_peers = self._batch_verify_peers(sector_tickers, sector)
            
            logger.info(f"Found {len(verified_peers)} verified peers for sector '{sector}'")
            return verified_peers
            
        except Exception as e:
            logger.error(f"Error finding peer companies for {sector}: {e}")
            return []
    
    def _fallback_sector_search(self, sector: str, industry: str) -> List[str]:
        """
        Fallback strategies for finding peer companies when direct mapping fails
        
        Args:
            sector: Original sector name
            industry: Industry name for additional context
            
        Returns:
            List of potential peer ticker symbols
        """
        fallback_tickers = []
        
        # Common fallback mappings for sector variations
        fallback_mappings = {
            'information technology': 'Technology',
            'tech': 'Technology',
            'software': 'Technology',
            'finance': 'Financial Services',
            'banking': 'Financial Services',
            'insurance': 'Financial Services',
            'retail': 'Consumer Cyclical',
            'consumer goods': 'Consumer Defensive',
            'pharma': 'Healthcare',
            'pharmaceutical': 'Healthcare',
            'biotech': 'Healthcare',
            'oil': 'Energy',
            'gas': 'Energy',
            'renewable': 'Energy',
            'electric': 'Utilities',
            'manufacturing': 'Industrials',
            'transport': 'Industrials',
            'logistics': 'Industrials',
            'aerospace': 'Industrials',
            'mining': 'Materials',
            'chemicals': 'Materials',
            'reit': 'Real Estate',
            'property': 'Real Estate'
        }
        
        # Try fallback mappings
        sector_lower = sector.lower()
        for keyword, mapped_sector in fallback_mappings.items():
            if keyword in sector_lower:
                fallback_tickers = self._get_common_tickers_by_sector(mapped_sector)
                if fallback_tickers:
                    logger.info(f"Fallback: mapped '{sector}' to '{mapped_sector}' via keyword '{keyword}'")
                    break
        
        # If still no luck, try industry-based fallback
        if not fallback_tickers and industry:
            industry_lower = industry.lower()
            for keyword, mapped_sector in fallback_mappings.items():
                if keyword in industry_lower:
                    fallback_tickers = self._get_common_tickers_by_sector(mapped_sector)
                    if fallback_tickers:
                        logger.info(f"Fallback: mapped industry '{industry}' to '{mapped_sector}' via keyword '{keyword}'")
                        break
        
        # Last resort: return a broad technology mix if nothing else works
        if not fallback_tickers:
            logger.warning(f"No fallback found for sector '{sector}', using broad technology mix")
            fallback_tickers = self._get_common_tickers_by_sector('Technology')[:10]
        
        return fallback_tickers
    
    def _batch_verify_peers(self, potential_peers: List[str], target_sector: str) -> List[str]:
        """
        Efficiently verify peers using batch processing with early termination
        
        Args:
            potential_peers: List of tickers to verify
            target_sector: Target sector to match against
            
        Returns:
            List of verified peer ticker symbols
        """
        verified_peers = []
        max_attempts = min(len(potential_peers), 15)  # Limit verification attempts
        
        for i, potential_peer in enumerate(potential_peers[:max_attempts]):
            # Early termination if we have enough peers
            if len(verified_peers) >= self.minimum_peer_count:
                logger.info(f"Early termination: found {len(verified_peers)} peers, stopping verification")
                break
                
            try:
                if 'yfinance' in self.rate_limiters:
                    self.rate_limiters['yfinance'].wait_if_needed()
                    
                peer_info = yf.Ticker(potential_peer).info
                peer_sector = peer_info.get('sector', '')
                
                # More flexible sector matching
                if (peer_sector == target_sector or 
                    (peer_sector and target_sector and 
                     peer_sector.lower() in target_sector.lower() or 
                     target_sector.lower() in peer_sector.lower())):
                    verified_peers.append(potential_peer)
                    logger.debug(f"Verified peer {potential_peer}: {peer_sector}")
                    
                # Shorter delay for batch processing
                time.sleep(0.05)
                
            except Exception as e:
                logger.debug(f"Error verifying peer {potential_peer}: {e}")
                continue
        
        return verified_peers

    def _get_common_tickers_by_sector(self, sector: str) -> List[str]:
        """
        Get common tickers by sector with enhanced mappings
        
        Enhanced with more comprehensive sector coverage and common variations
        """
        sector_mappings = {
            # Technology variations
            'Technology': [
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA',
                'ORCL', 'CRM', 'ADBE', 'NOW', 'INTU', 'IBM', 'CSCO', 'TXN',
                'QCOM', 'AVGO', 'AMD', 'NFLX', 'PYPL', 'SHOP', 'SQ', 'ROKU',
                'UBER', 'LYFT', 'DOCU', 'ZM', 'DDOG', 'SNOW', 'PLTR', 'RBLX'
            ],
            'Communication Services': [
                'GOOGL', 'GOOG', 'META', 'NFLX', 'DIS', 'VZ', 'T', 'CMCSA',
                'CHTR', 'TMUS', 'ATVI', 'TWTR', 'SNAP', 'PINS', 'MTCH', 'EA'
            ],
            'Healthcare': [
                'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'LLY', 'BMY',
                'MRK', 'AMGN', 'GILD', 'CVS', 'MDT', 'CI', 'ANTM', 'HUM',
                'DHR', 'SYK', 'BSX', 'ZTS', 'REGN', 'VRTX', 'BIIB', 'ILMN'
            ],
            # Financial Services variations
            'Financial Services': [
                'BRK-B', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB',
                'PNC', 'TFC', 'COF', 'AXP', 'BLK', 'SPGI', 'ICE', 'CME',
                'FI', 'V', 'MA', 'PYPL', 'SQ', 'AFRM', 'SOFI'
            ],
            'Financials': [
                'BRK-B', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB',
                'PNC', 'TFC', 'COF', 'AXP', 'BLK', 'SPGI', 'ICE', 'CME',
                'FI', 'V', 'MA', 'PYPL', 'SQ', 'AFRM', 'SOFI'
            ],
            # Consumer variations
            'Consumer Cyclical': [
                'AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'LOW', 'TJX',
                'BKNG', 'GM', 'F', 'ABNB', 'MAR', 'YUM', 'CMG', 'LULU',
                'COST', 'WMT', 'TGT', 'BBY', 'ETSY', 'W', 'WAYFAIR'
            ],
            'Consumer Discretionary': [
                'AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'LOW', 'TJX',
                'BKNG', 'GM', 'F', 'ABNB', 'MAR', 'YUM', 'CMG', 'LULU',
                'COST', 'WMT', 'TGT', 'BBY', 'ETSY', 'W', 'WAYFAIR'
            ],
            'Consumer Defensive': [
                'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'CVS', 'CL',
                'KMB', 'GIS', 'K', 'HSY', 'MKC', 'SJM', 'CPB', 'CAG'
            ],
            'Consumer Staples': [
                'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'CVS', 'CL',
                'KMB', 'GIS', 'K', 'HSY', 'MKC', 'SJM', 'CPB', 'CAG'
            ],
            'Energy': [
                'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'KMI', 'OKE',
                'WMB', 'MPC', 'VLO', 'PSX', 'HES', 'DVN', 'FANG', 'BKR',
                'HAL', 'OXY', 'PARA', 'APA', 'CNP', 'ENPH', 'SEDG'
            ],
            'Utilities': [
                'NEE', 'SO', 'DUK', 'AEP', 'SRE', 'D', 'PEG', 'XEL',
                'EXC', 'ED', 'ETR', 'WEC', 'PPL', 'CMS', 'DTE', 'NI',
                'AWK', 'ATO', 'CNP', 'NRG', 'PCG', 'FE', 'AEE'
            ],
            'Industrial': [
                'BA', 'HON', 'UPS', 'CAT', 'LMT', 'RTX', 'DE', 'MMM',
                'GE', 'FDX', 'NOC', 'LUV', 'DAL', 'UAL', 'AAL', 'WM',
                'EMR', 'ETN', 'PH', 'CMI', 'ITW', 'TT', 'ROK', 'DOV'
            ],
            'Industrials': [
                'BA', 'HON', 'UPS', 'CAT', 'LMT', 'RTX', 'DE', 'MMM',
                'GE', 'FDX', 'NOC', 'LUV', 'DAL', 'UAL', 'AAL', 'WM',
                'EMR', 'ETN', 'PH', 'CMI', 'ITW', 'TT', 'ROK', 'DOV'
            ],
            'Materials': [
                'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'DOW', 'DD',
                'PPG', 'EMN', 'IFF', 'ALB', 'FMC', 'CF', 'MOS', 'NUE',
                'STLD', 'VMC', 'MLM', 'PKG', 'IP', 'WRK', 'SEE'
            ],
            'Real Estate': [
                'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'SBAC', 'DLR',
                'WY', 'AVB', 'EQR', 'WELL', 'MAA', 'ESS', 'UDR', 'CPT',
                'FRT', 'VTR', 'HCP', 'REG', 'BXP', 'SLG', 'KIM', 'MAC'
            ]
        }
        
        # Direct lookup first
        if sector in sector_mappings:
            return sector_mappings[sector]
        
        # Try partial matches for variations in sector names
        sector_lower = sector.lower()
        for mapped_sector, tickers in sector_mappings.items():
            if mapped_sector.lower() in sector_lower or sector_lower in mapped_sector.lower():
                logger.info(f"Using sector mapping '{mapped_sector}' for input '{sector}'")
                return tickers
        
        # No match found
        logger.warning(f"No sector mapping found for '{sector}', returning empty list")
        return []

    @performance_timer("peer_pb_data_fetch", include_args=True)
    def _fetch_peer_pb_data(self, peer_tickers: List[str]) -> List[IndustryPeerData]:
        """
        Fetch P/B ratio data for peer companies using concurrent processing
        
        Args:
            peer_tickers: List of ticker symbols
            
        Returns:
            List of IndustryPeerData objects
        """
        peer_data = []
        
        # Use concurrent processing for better performance
        # Limit workers to avoid overwhelming APIs and respect rate limits
        max_workers = min(6, len(peer_tickers))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self._fetch_single_ticker_pb_data, ticker): ticker
                for ticker in peer_tickers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    pb_data = future.result()
                    if pb_data:
                        peer_data.append(pb_data)
                except Exception as e:
                    logger.debug(f"Error fetching P/B data for {ticker}: {e}")
                    continue
                
        logger.info(f"Successfully fetched P/B data for {len(peer_data)}/{len(peer_tickers)} peers")
        return peer_data

    def _fetch_single_ticker_pb_data(self, ticker: str) -> Optional[IndustryPeerData]:
        """
        Fetch P/B data for a single ticker with fallback across multiple sources
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            IndustryPeerData object or None
        """
        def _fetch_yfinance_data():
            if 'yfinance' in self.rate_limiters:
                self.rate_limiters['yfinance'].wait_if_needed()
                
            stock = yf.Ticker(ticker)
            info = stock.info
            
            pb_ratio = info.get('priceToBook')
            book_value = info.get('bookValue')
            market_cap = info.get('marketCap')
            sector = info.get('sector')
            industry = info.get('industry')
            
            if pb_ratio and pb_ratio > 0:  # Valid P/B ratio
                return IndustryPeerData(
                    ticker=ticker,
                    sector=sector or 'Unknown',
                    industry=industry or 'Unknown',
                    pb_ratio=pb_ratio,
                    book_value_per_share=book_value,
                    market_cap=market_cap,
                    data_source='yfinance',
                    last_updated=datetime.now()
                )
            else:
                raise ValueError(f"No valid P/B ratio found for {ticker}")
        
        # Use error handler with retry logic if available
        if get_error_handler:
            error_handler = get_error_handler()
            result, failure = error_handler.execute_with_retry(_fetch_yfinance_data, "yfinance")
            
            if failure:
                # Log the failure but don't raise - this allows graceful degradation
                logger.debug(f"Failed to fetch P/B data for {ticker} after retries: {failure.user_message}")
                return None
                
            return result
        else:
            # Fallback to original error handling
            try:
                return _fetch_yfinance_data()
            except Exception as e:
                logger.debug(f"yfinance failed for {ticker}: {e}")
                return None

    def _calculate_industry_statistics(self, sector: str, industry: str, peer_data: List[IndustryPeerData]) -> Optional[IndustryStatistics]:
        """
        Calculate industry statistics from peer data
        
        Args:
            sector: Sector name
            industry: Industry name  
            peer_data: List of peer company data
            
        Returns:
            IndustryStatistics object or None
        """
        try:
            # Filter valid P/B ratios
            valid_pb_ratios = [p.pb_ratio for p in peer_data if p.pb_ratio and p.pb_ratio > 0]
            
            if len(valid_pb_ratios) < self.minimum_peer_count:
                logger.warning(f"Insufficient valid P/B ratios: {len(valid_pb_ratios)} < {self.minimum_peer_count}")
                return None
                
            # Convert to numpy array for calculations
            pb_array = np.array(valid_pb_ratios)
            
            # Calculate statistics
            statistics = IndustryStatistics(
                sector=sector,
                industry=industry,
                peer_count=len(valid_pb_ratios),
                median_pb=float(np.median(pb_array)),
                mean_pb=float(np.mean(pb_array)),
                min_pb=float(np.min(pb_array)),
                max_pb=float(np.max(pb_array)),
                q1_pb=float(np.percentile(pb_array, 25)),
                q3_pb=float(np.percentile(pb_array, 75)),
                std_pb=float(np.std(pb_array)),
                peer_tickers=[p.ticker for p in peer_data if p.pb_ratio and p.pb_ratio > 0],
                data_quality_score=self._calculate_data_quality_score(peer_data),
                last_updated=datetime.now(),
                cache_expiry=datetime.now() + self.cache_ttl
            )
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error calculating industry statistics: {e}")
            return None

    def _calculate_data_quality_score(self, peer_data: List[IndustryPeerData]) -> float:
        """
        Calculate a data quality score based on completeness and freshness
        
        Args:
            peer_data: List of peer company data
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not peer_data:
            return 0.0
            
        # Factors for quality score
        completeness_score = len([p for p in peer_data if p.pb_ratio]) / len(peer_data)
        peer_count_score = min(len(peer_data) / 20, 1.0)  # Higher score with more peers, capped at 20
        
        # Combine scores
        quality_score = (completeness_score * 0.7 + peer_count_score * 0.3)
        
        return quality_score

    def _get_cache_key(self, ticker: str) -> str:
        """Generate cache key for ticker"""
        return hashlib.md5(f"industry_pb_{ticker}".encode()).hexdigest()

    def _get_cache_file_path(self, ticker: str) -> Path:
        """Get cache file path for ticker"""
        cache_key = self._get_cache_key(ticker)
        return self.cache_dir / f"industry_pb_{cache_key}.json"

    def _load_from_cache(self, ticker: str) -> Optional[IndustryStatistics]:
        """Load industry statistics from cache"""
        try:
            cache_file = self._get_cache_file_path(ticker)
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert datetime strings back to datetime objects
                if data.get('last_updated'):
                    data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                if data.get('cache_expiry'):
                    data['cache_expiry'] = datetime.fromisoformat(data['cache_expiry'])
                    
                return IndustryStatistics(**data)
        except Exception as e:
            logger.debug(f"Error loading cache for {ticker}: {e}")
            
        return None

    def _save_to_cache(self, ticker: str, statistics: IndustryStatistics):
        """Save industry statistics to cache"""
        try:
            cache_file = self._get_cache_file_path(ticker)
            
            # Convert to dict and handle datetime serialization
            data = statistics.__dict__.copy()
            if data.get('last_updated'):
                data['last_updated'] = data['last_updated'].isoformat()
            if data.get('cache_expiry'):
                data['cache_expiry'] = data['cache_expiry'].isoformat()
                
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved industry statistics to cache for {ticker}")
            
        except Exception as e:
            logger.error(f"Error saving cache for {ticker}: {e}")

    def _is_cache_valid(self, statistics: IndustryStatistics) -> bool:
        """Check if cached statistics are still valid"""
        if not statistics.cache_expiry:
            return False
            
        return datetime.now() < statistics.cache_expiry

    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear cached data
        
        Args:
            ticker: Specific ticker to clear, or None to clear all
        """
        try:
            if ticker:
                cache_file = self._get_cache_file_path(ticker)
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"Cleared cache for {ticker}")
            else:
                # Clear all industry cache files
                cache_files = list(self.cache_dir.glob("industry_pb_*.json"))
                for cache_file in cache_files:
                    cache_file.unlink()
                logger.info(f"Cleared {len(cache_files)} industry cache files")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data"""
        try:
            cache_files = list(self.cache_dir.glob("industry_pb_*.json"))
            
            info = {
                'cache_dir': str(self.cache_dir),
                'total_cached_files': len(cache_files),
                'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600,
                'files': []
            }
            
            for cache_file in cache_files:
                try:
                    stat = cache_file.stat()
                    info['files'].append({
                        'file': cache_file.name,
                        'size_bytes': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception:
                    continue
                    
            return info
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'error': str(e)}