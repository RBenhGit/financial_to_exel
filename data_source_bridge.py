"""
Data Source Bridge Module

This module provides a unified bridge between financial analysis modules (DDM, PB, etc.)
and various data sources (APIs, Excel files, enhanced data manager).

Features:
- Unified interface for all analysis modules
- Automatic data source prioritization and fallback
- Data quality assessment and validation
- Comprehensive error handling and logging
- Support for both real-time API data and offline Excel analysis
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
from pathlib import Path

# Import existing components
from financial_calculations import FinancialCalculator
from enhanced_data_manager import EnhancedDataManager
from data_sources import FinancialDataRequest, DataSourceType

logger = logging.getLogger(__name__)


class DataSourceBridge:
    """
    Bridge class that provides unified data access for financial analysis modules.

    This class abstracts away the complexity of multiple data sources and provides
    a simple interface for analysis modules to get the data they need.
    """

    def __init__(
        self,
        financial_calculator: FinancialCalculator,
        enhanced_data_manager: Optional[EnhancedDataManager] = None,
    ):
        """
        Initialize the data source bridge

        Args:
            financial_calculator (FinancialCalculator): Core financial calculator instance
            enhanced_data_manager (EnhancedDataManager, optional): Enhanced data manager for API access
        """
        self.financial_calculator = financial_calculator
        self.enhanced_data_manager = enhanced_data_manager or getattr(
            financial_calculator, 'enhanced_data_manager', None
        )

        # Data source priority (higher priority sources are tried first)
        self.data_source_priority = [
            'enhanced_data_manager',
            'financial_calculator_api',
            'financial_statements',
            'yfinance_fallback',
        ]

        # Cache for frequently accessed data
        self.data_cache = {}
        self.cache_timestamps = {}
        self.cache_ttl_seconds = 300  # 5 minutes cache TTL

        logger.info("DataSourceBridge initialized with available data sources")
        self._log_available_sources()

    def _log_available_sources(self):
        """Log which data sources are available"""
        available_sources = []

        if self.enhanced_data_manager:
            available_sources.append("Enhanced Data Manager (Multi-API)")
        if hasattr(self.financial_calculator, 'fetch_market_data'):
            available_sources.append("Financial Calculator API Access")
        if self.financial_calculator.financial_data:
            available_sources.append("Excel Financial Statements")

        available_sources.append("yfinance (Fallback)")

        logger.info(f"Available data sources: {', '.join(available_sources)}")

    def get_market_data(
        self, ticker_symbol: str = None, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get market data with automatic source fallback

        Args:
            ticker_symbol (str, optional): Ticker symbol, uses financial calculator's if not provided
            force_refresh (bool): Force refresh even if cached data exists

        Returns:
            Dict containing market data or None if all sources fail
        """
        if not ticker_symbol:
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)

        if not ticker_symbol:
            logger.error("No ticker symbol available for market data fetch")
            return None

        cache_key = f"market_data_{ticker_symbol}"

        # Check cache if not forcing refresh
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug(f"Using cached market data for {ticker_symbol}")
            return self.data_cache[cache_key]

        # Try each data source in priority order
        for source in self.data_source_priority:
            try:
                market_data = self._fetch_market_data_from_source(ticker_symbol, source)
                if market_data:
                    # Cache the successful result
                    self.data_cache[cache_key] = market_data
                    self.cache_timestamps[cache_key] = datetime.now()

                    logger.info(
                        f"Successfully fetched market data for {ticker_symbol} from {source}"
                    )
                    return market_data
            except Exception as e:
                logger.warning(f"Market data fetch from {source} failed: {e}")
                continue

        logger.error(f"All market data sources failed for {ticker_symbol}")
        return None

    def get_dividend_data(
        self, ticker_symbol: str = None, years: int = 10
    ) -> Optional[pd.DataFrame]:
        """
        Get dividend data with automatic source fallback

        Args:
            ticker_symbol (str, optional): Ticker symbol
            years (int): Number of years of dividend history to fetch

        Returns:
            DataFrame with dividend data or None if all sources fail
        """
        if not ticker_symbol:
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)

        if not ticker_symbol:
            logger.error("No ticker symbol available for dividend data fetch")
            return None

        cache_key = f"dividend_data_{ticker_symbol}_{years}"

        # Check cache
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached dividend data for {ticker_symbol}")
            return self.data_cache[cache_key]

        # Try enhanced data manager first
        if self.enhanced_data_manager:
            try:
                dividend_data = self._fetch_dividend_data_enhanced(ticker_symbol)
                if not dividend_data.empty:
                    self.data_cache[cache_key] = dividend_data
                    self.cache_timestamps[cache_key] = datetime.now()
                    logger.info(f"Successfully fetched dividend data from enhanced data manager")
                    return dividend_data
            except Exception as e:
                logger.warning(f"Enhanced data manager dividend fetch failed: {e}")

        # Fallback to yfinance
        try:
            import yfinance as yf

            ticker = yf.Ticker(ticker_symbol)
            dividends = ticker.dividends

            if not dividends.empty:
                # Convert to annual dividend data
                annual_dividends = dividends.groupby(dividends.index.year).sum()
                dividend_df = pd.DataFrame(
                    {
                        'year': annual_dividends.index,
                        'dividend_per_share': annual_dividends.values,
                        'date': pd.to_datetime(
                            annual_dividends.index, format='%Y', errors='coerce'
                        ),
                    }
                )

                self.data_cache[cache_key] = dividend_df
                self.cache_timestamps[cache_key] = datetime.now()
                logger.info(f"Successfully fetched dividend data from yfinance")
                return dividend_df
        except Exception as e:
            logger.error(f"yfinance dividend fetch failed: {e}")

        # Final fallback to financial statements
        try:
            dividend_data = self._extract_dividends_from_statements()
            if not dividend_data.empty:
                self.data_cache[cache_key] = dividend_data
                self.cache_timestamps[cache_key] = datetime.now()
                logger.info(f"Successfully extracted dividend data from financial statements")
                return dividend_data
        except Exception as e:
            logger.error(f"Financial statements dividend extraction failed: {e}")

        logger.error(f"All dividend data sources failed for {ticker_symbol}")
        return None

    def get_balance_sheet_data(self, latest_only: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get balance sheet data with source prioritization

        Args:
            latest_only (bool): Whether to return only the latest period data

        Returns:
            Dict containing balance sheet data or None if unavailable
        """
        cache_key = f"balance_sheet_{latest_only}"

        # Check cache
        if self._is_cache_valid(cache_key):
            return self.data_cache[cache_key]

        # Try enhanced data manager first
        if self.enhanced_data_manager:
            try:
                ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
                if ticker_symbol:
                    balance_sheet_data = self._fetch_balance_sheet_enhanced(
                        ticker_symbol, latest_only
                    )
                    if balance_sheet_data:
                        self.data_cache[cache_key] = balance_sheet_data
                        self.cache_timestamps[cache_key] = datetime.now()
                        logger.info(
                            "Successfully fetched balance sheet data from enhanced data manager"
                        )
                        return balance_sheet_data
            except Exception as e:
                logger.warning(f"Enhanced data manager balance sheet fetch failed: {e}")

        # Fallback to financial calculator's data
        try:
            balance_sheet_data = self._get_balance_sheet_from_statements(latest_only)
            if balance_sheet_data:
                self.data_cache[cache_key] = balance_sheet_data
                self.cache_timestamps[cache_key] = datetime.now()
                logger.info("Successfully retrieved balance sheet data from financial statements")
                return balance_sheet_data
        except Exception as e:
            logger.error(f"Financial statements balance sheet retrieval failed: {e}")

        logger.error("All balance sheet data sources failed")
        return None

    def get_comprehensive_financial_data(self) -> Dict[str, Any]:
        """
        Get comprehensive financial data for analysis modules

        Returns:
            Dict containing all available financial data with metadata
        """
        return {
            'market_data': self.get_market_data(),
            'dividend_data': self.get_dividend_data(),
            'balance_sheet_data': self.get_balance_sheet_data(),
            'financial_statements': self.financial_calculator.get_standardized_financial_data(),
            'data_quality': self._assess_data_quality(),
            'available_sources': self._get_available_sources_summary(),
            'last_updated': datetime.now().isoformat(),
        }

    def validate_data_for_analysis(self, analysis_type: str) -> Dict[str, Any]:
        """
        Validate that sufficient data is available for specific analysis types

        Args:
            analysis_type (str): Type of analysis ('ddm', 'pb', 'dcf', etc.)

        Returns:
            Dict with validation results and recommendations
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'data_sources_used': [],
            'completeness_score': 0.0,
        }

        if analysis_type.lower() == 'ddm':
            validation_result = self._validate_ddm_data()
        elif analysis_type.lower() == 'pb':
            validation_result = self._validate_pb_data()
        elif analysis_type.lower() == 'dcf':
            validation_result = self._validate_dcf_data()
        else:
            validation_result['errors'].append(f"Unknown analysis type: {analysis_type}")
            validation_result['valid'] = False

        return validation_result

    def _fetch_market_data_from_source(
        self, ticker_symbol: str, source: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch market data from a specific source"""
        if source == 'enhanced_data_manager' and self.enhanced_data_manager:
            return self.enhanced_data_manager.fetch_market_data(ticker_symbol)
        elif source == 'financial_calculator_api':
            if hasattr(self.financial_calculator, 'fetch_market_data'):
                return self.financial_calculator.fetch_market_data(ticker_symbol)
        elif source == 'yfinance_fallback':
            return self._fetch_market_data_yfinance(ticker_symbol)

        return None

    def _fetch_market_data_yfinance(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch market data using yfinance as fallback"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            return {
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'market_cap': info.get('marketCap', 0),
                'shares_outstanding': info.get(
                    'sharesOutstanding', info.get('impliedSharesOutstanding', 0)
                ),
                'currency': info.get('currency', 'USD'),
                'source': 'yfinance',
            }
        except Exception as e:
            logger.error(f"yfinance market data fetch failed: {e}")
            return None

    def _fetch_dividend_data_enhanced(self, ticker_symbol: str) -> pd.DataFrame:
        """Fetch dividend data using enhanced data manager"""
        try:
            request = FinancialDataRequest(
                ticker=ticker_symbol, data_types=['dividends', 'fundamentals'], force_refresh=False
            )

            response = self.enhanced_data_manager.unified_adapter.fetch_data(request)

            if response.success and response.data:
                # Extract dividend data from API response
                dividend_records = []
                api_data = response.data

                if 'dividends' in api_data:
                    dividends_raw = api_data['dividends']
                    dividend_records = self._parse_api_dividend_data(dividends_raw)

                if dividend_records:
                    return pd.DataFrame(dividend_records)

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Enhanced dividend data fetch failed: {e}")
            return pd.DataFrame()

    def _parse_api_dividend_data(self, dividends_raw) -> List[Dict]:
        """Parse dividend data from API response"""
        records = []

        try:
            if isinstance(dividends_raw, dict):
                for date_str, amount in dividends_raw.items():
                    try:
                        date_obj = pd.to_datetime(date_str, errors='coerce')
                        year = date_obj.year
                        records.append(
                            {'year': year, 'dividend_per_share': float(amount), 'date': date_obj}
                        )
                    except (ValueError, TypeError):
                        continue

            # Group by year and sum if multiple payments per year
            if records:
                df = pd.DataFrame(records)
                annual_dividends = (
                    df.groupby('year')
                    .agg({'dividend_per_share': 'sum', 'date': 'max'})
                    .reset_index()
                )
                return annual_dividends.to_dict('records')

        except Exception as e:
            logger.error(f"Error parsing API dividend data: {e}")

        return []

    def _extract_dividends_from_statements(self) -> pd.DataFrame:
        """Extract dividend data from financial statements"""
        try:
            cashflow_data = self.financial_calculator.financial_data.get('Cash Flow Statement', {})
            if not cashflow_data:
                cashflow_data = self.financial_calculator.financial_data.get('cashflow_fy', {})

            if not cashflow_data:
                return pd.DataFrame()

            dividend_keywords = [
                'dividends paid',
                'dividend payments',
                'cash dividends',
                'dividends to shareholders',
                'common dividends',
            ]

            dividend_data = []

            for year, year_data in cashflow_data.items():
                if isinstance(year_data, dict):
                    dividend_amount = 0

                    for key, value in year_data.items():
                        if isinstance(key, str) and isinstance(value, (int, float)):
                            key_lower = key.lower().strip()
                            for keyword in dividend_keywords:
                                if keyword in key_lower:
                                    dividend_amount = abs(value)
                                    break

                    if dividend_amount > 0:
                        shares_outstanding = getattr(
                            self.financial_calculator, 'shares_outstanding', 1
                        )
                        if shares_outstanding > 0:
                            dividend_per_share = (
                                dividend_amount * self.financial_calculator.financial_scale_factor
                            ) / shares_outstanding
                            dividend_data.append(
                                {
                                    'year': year,
                                    'dividend_per_share': dividend_per_share,
                                    'date': pd.to_datetime(f"{year}-12-31", errors='coerce'),
                                }
                            )

            return pd.DataFrame(dividend_data) if dividend_data else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error extracting dividends from statements: {e}")
            return pd.DataFrame()

    def _fetch_balance_sheet_enhanced(
        self, ticker_symbol: str, latest_only: bool
    ) -> Optional[Dict]:
        """Fetch balance sheet data using enhanced data manager"""
        try:
            request = FinancialDataRequest(
                ticker=ticker_symbol,
                data_types=['balance_sheet', 'fundamentals'],
                force_refresh=False,
            )

            response = self.enhanced_data_manager.unified_adapter.fetch_data(request)

            if response.success and response.data:
                balance_sheet_data = response.data.get('balance_sheet', {})
                if balance_sheet_data:
                    if latest_only:
                        # Return only the most recent period
                        if isinstance(balance_sheet_data, dict):
                            latest_period = (
                                max(balance_sheet_data.keys())
                                if balance_sheet_data.keys()
                                else None
                            )
                            if latest_period:
                                return {latest_period: balance_sheet_data[latest_period]}
                    else:
                        return balance_sheet_data

            return None

        except Exception as e:
            logger.error(f"Enhanced balance sheet fetch failed: {e}")
            return None

    def _get_balance_sheet_from_statements(self, latest_only: bool) -> Optional[Dict]:
        """Get balance sheet data from financial statements"""
        try:
            balance_sheet_data = self.financial_calculator.financial_data.get('Balance Sheet', {})
            if not balance_sheet_data:
                balance_sheet_data = self.financial_calculator.financial_data.get('balance_fy', {})

            if balance_sheet_data and latest_only:
                # Return only the most recent period
                if isinstance(balance_sheet_data, dict):
                    years = [
                        year for year in balance_sheet_data.keys() if isinstance(year, (int, str))
                    ]
                    if years:
                        latest_year = max(years)
                        return {latest_year: balance_sheet_data[latest_year]}

            return balance_sheet_data

        except Exception as e:
            logger.error(f"Error getting balance sheet from statements: {e}")
            return None

    def _validate_ddm_data(self) -> Dict[str, Any]:
        """Validate data availability for DDM analysis"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'data_sources_used': [],
            'completeness_score': 0.0,
        }

        # Check for dividend data
        dividend_data = self.get_dividend_data()
        if dividend_data is None or dividend_data.empty:
            result['errors'].append("No dividend data available - DDM analysis not possible")
            result['valid'] = False
        elif len(dividend_data) < 3:
            result['warnings'].append(
                f"Limited dividend history ({len(dividend_data)} years) - results may be unreliable"
            )
            result['completeness_score'] += 0.3
        else:
            result['completeness_score'] += 0.6
            result['data_sources_used'].append("dividend_data")

        # Check for market data
        market_data = self.get_market_data()
        if market_data and market_data.get('current_price', 0) > 0:
            result['completeness_score'] += 0.3
            result['data_sources_used'].append("market_data")
        else:
            result['warnings'].append(
                "No current market price - DDM valuation cannot be compared to market"
            )

        # Check for shares outstanding
        shares = getattr(self.financial_calculator, 'shares_outstanding', 0)
        if shares > 0:
            result['completeness_score'] += 0.1
        else:
            result['warnings'].append(
                "Shares outstanding not available - may affect per-share calculations"
            )

        if result['completeness_score'] < 0.5:
            result['valid'] = False
            result['errors'].append("Insufficient data quality for reliable DDM analysis")

        return result

    def _validate_pb_data(self) -> Dict[str, Any]:
        """Validate data availability for P/B analysis"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'data_sources_used': [],
            'completeness_score': 0.0,
        }

        # Check for balance sheet data
        balance_sheet_data = self.get_balance_sheet_data()
        if not balance_sheet_data:
            result['errors'].append("No balance sheet data available - P/B analysis not possible")
            result['valid'] = False
        else:
            result['completeness_score'] += 0.4
            result['data_sources_used'].append("balance_sheet")

        # Check for market data
        market_data = self.get_market_data()
        if market_data and market_data.get('current_price', 0) > 0:
            result['completeness_score'] += 0.3
            result['data_sources_used'].append("market_data")
        else:
            result['errors'].append("No current market price - P/B ratio cannot be calculated")
            result['valid'] = False

        # Check for shares outstanding
        shares = getattr(self.financial_calculator, 'shares_outstanding', 0)
        if shares > 0:
            result['completeness_score'] += 0.3
        else:
            result['errors'].append(
                "Shares outstanding not available - book value per share cannot be calculated"
            )
            result['valid'] = False

        return result

    def _validate_dcf_data(self) -> Dict[str, Any]:
        """Validate data availability for DCF analysis"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'data_sources_used': [],
            'completeness_score': 0.0,
        }

        # Check for cash flow data
        metrics = self.financial_calculator._calculate_all_metrics()
        if not metrics or not metrics.get('operating_cash_flow'):
            result['errors'].append("No cash flow data available - DCF analysis not possible")
            result['valid'] = False
        else:
            result['completeness_score'] += 0.5
            result['data_sources_used'].append("cash_flow_statements")

        # Check for historical data depth
        if metrics:
            ocf_length = len(metrics.get('operating_cash_flow', []))
            if ocf_length >= 5:
                result['completeness_score'] += 0.3
            elif ocf_length >= 3:
                result['completeness_score'] += 0.2
                result['warnings'].append(
                    "Limited historical data - projections may be less reliable"
                )
            else:
                result['warnings'].append(
                    "Very limited historical data - DCF results should be interpreted cautiously"
                )

        # Check for market data
        market_data = self.get_market_data()
        if market_data:
            result['completeness_score'] += 0.2
            result['data_sources_used'].append("market_data")

        return result

    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality across all sources"""
        quality_assessment = {
            'overall_score': 0.0,
            'source_scores': {},
            'coverage': {},
            'freshness': {},
            'reliability': {},
        }

        # Assess each data source
        sources_assessed = 0
        total_score = 0.0

        # Market data quality
        market_data = self.get_market_data()
        if market_data:
            market_score = self._score_market_data_quality(market_data)
            quality_assessment['source_scores']['market_data'] = market_score
            total_score += market_score
            sources_assessed += 1

        # Financial statements quality
        if self.financial_calculator.financial_data:
            statements_score = self._score_statements_quality()
            quality_assessment['source_scores']['financial_statements'] = statements_score
            total_score += statements_score
            sources_assessed += 1

        # Calculate overall score
        if sources_assessed > 0:
            quality_assessment['overall_score'] = total_score / sources_assessed

        return quality_assessment

    def _score_market_data_quality(self, market_data: Dict) -> float:
        """Score market data quality (0.0 to 1.0)"""
        score = 0.0

        if market_data.get('current_price', 0) > 0:
            score += 0.4
        if market_data.get('market_cap', 0) > 0:
            score += 0.3
        if market_data.get('shares_outstanding', 0) > 0:
            score += 0.3

        return score

    def _score_statements_quality(self) -> float:
        """Score financial statements quality (0.0 to 1.0)"""
        score = 0.0
        statements = ['income_fy', 'balance_fy', 'cashflow_fy']

        for statement in statements:
            if statement in self.financial_calculator.financial_data:
                data = self.financial_calculator.financial_data[statement]
                if not data.empty if hasattr(data, 'empty') else bool(data):
                    score += 0.33

        return score

    def _get_available_sources_summary(self) -> Dict[str, bool]:
        """Get summary of available data sources"""
        return {
            'enhanced_data_manager': self.enhanced_data_manager is not None,
            'financial_calculator_api': hasattr(self.financial_calculator, 'fetch_market_data'),
            'excel_statements': bool(self.financial_calculator.financial_data),
            'yfinance_fallback': True,  # Always available
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.data_cache:
            return False

        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False

        age_seconds = (datetime.now() - timestamp).total_seconds()
        return age_seconds < self.cache_ttl_seconds

    def clear_cache(self):
        """Clear all cached data"""
        self.data_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Data source bridge cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_items': len(self.data_cache),
            'cache_keys': list(self.data_cache.keys()),
            'oldest_cache_age_seconds': (
                min(
                    [(datetime.now() - ts).total_seconds() for ts in self.cache_timestamps.values()]
                )
                if self.cache_timestamps
                else 0
            ),
            'cache_ttl_seconds': self.cache_ttl_seconds,
        }
