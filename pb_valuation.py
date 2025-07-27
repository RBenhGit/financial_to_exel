"""
Price-to-Book (P/B) Valuation Module
===================================

This module provides comprehensive Price-to-Book ratio analysis capabilities for
fundamental valuation, including industry benchmarking, historical trend analysis,
and book value quality assessment for investment decision-making.

Key Features
------------
- Comprehensive P/B ratio calculation and analysis
- Industry-specific benchmarking with sector comparisons
- Historical P/B trend analysis and percentile ranking
- Book value per share calculation from multiple data sources
- Valuation assessment using industry P/B multiples
- Risk assessment including book value quality metrics
- Integration with enhanced multi-source data management
- Automated report generation with investment insights

Classes
-------
PBValuator
    Main class for performing P/B ratio analysis and valuation

P/B Analysis Components
----------------------

**Current P/B Calculation**
    - Book Value per Share = Shareholders' Equity / Shares Outstanding
    - P/B Ratio = Market Price per Share / Book Value per Share
    - Market capitalization validation and consistency checks

**Industry Benchmarking**
    - Sector-specific P/B ratio benchmarks (median, low, high)
    - Percentile ranking within industry peer group
    - Industry position assessment (undervalued, fair, overvalued)

**Historical Analysis**
    - 5-year historical P/B trend analysis
    - Statistical metrics (min, max, mean, percentile ranking)
    - Trend direction and volatility assessment

**Valuation Assessment**
    - Fair value estimates using industry median P/B
    - Upside/downside potential calculation
    - Conservative and optimistic valuation scenarios

Usage Example
-------------
>>> from pb_valuation import PBValuator
>>> from financial_calculations import FinancialCalculator
>>>
>>> # Initialize with financial data
>>> calc = FinancialCalculator('BRK-B')  # Berkshire Hathaway
>>> pb = PBValuator(calc)
>>>
>>> # Comprehensive P/B analysis
>>> result = pb.calculate_pb_analysis()
>>> print(f"Current P/B: {result['pb_ratio']:.2f}")
>>> print(f"Book Value: ${result['book_value_per_share']:.2f}")
>>> print(f"Industry Position: {result['industry_comparison']['position']}")
>>>
>>> # Historical context
>>> historical = result['historical_analysis']
>>> print(f"5-Year P/B Range: {historical['min_pb']:.2f} - {historical['max_pb']:.2f}")
>>>
>>> # Valuation assessment
>>> valuation = result['valuation_assessment']
>>> print(f"Fair Value Estimate: ${valuation['fair_value_estimate']:.2f}")

Industry Benchmarks
-------------------
The module includes comprehensive industry-specific P/B benchmarks:

**Technology**: Median 3.5 (Range: 1.5 - 8.0)
    High P/B due to intellectual property and growth expectations

**Financial Services**: Median 1.2 (Range: 0.8 - 2.0)
    Lower P/B reflecting asset-heavy business models

**Healthcare**: Median 2.8 (Range: 1.2 - 6.0)
    Moderate P/B with premium for innovation and patents

**Utilities**: Median 1.8 (Range: 1.0 - 2.5)
    Stable P/B ratios reflecting regulated, asset-intensive operations

**Energy**: Median 1.5 (Range: 0.5 - 3.0)
    Cyclical P/B ratios influenced by commodity prices

Book Value Calculation
---------------------
The module calculates book value per share using multiple approaches:

1. **Primary Method**: Shareholders' equity from balance sheet
2. **API Integration**: Multi-source data validation
3. **Enhanced Data**: Cross-verification across data providers
4. **Quality Assessment**: Book value reliability scoring

Calculation steps:
- Extract shareholders' equity (total equity - preferred equity)
- Obtain shares outstanding (basic or diluted)
- Calculate BVPS = Shareholders' Equity / Shares Outstanding
- Validate results across multiple data sources

Financial Theory and Applications
--------------------------------

**Value Investing Perspective**
P/B ratio is fundamental to value investing strategies:
- P/B < 1.0 may indicate undervaluation or distress
- Historical P/B context helps identify relative value
- Asset-heavy industries typically have lower P/B ratios

**Limitations and Considerations**
- Book value may not reflect fair value of assets
- Intangible assets often not fully captured
- Accounting policies can affect book value calculation
- Industry context is crucial for proper interpretation

**Best Use Cases**
- Financial institutions (banks, insurance companies)
- Asset-heavy industries (utilities, real estate)
- Value screening and relative valuation
- Historical trend analysis and market timing

Risk Assessment Framework
------------------------
The module provides comprehensive risk assessment:

**Book Value Quality**
- Asset composition analysis
- Intangible asset proportion
- Accounting policy considerations

**Market Risk Factors**
- P/B volatility assessment
- Industry cycle positioning
- Relative valuation metrics

**Investment Considerations**
- Growth vs. value characteristics
- Asset turnover efficiency
- Return on equity relationship

Data Sources and Validation
---------------------------
- **Primary**: yfinance market and financial data
- **Enhanced**: Multi-API data aggregation (FMP, Alpha Vantage, Polygon)
- **Validation**: Cross-source data verification
- **Quality Control**: Outlier detection and data consistency checks

Notes
-----
- All monetary values maintain consistent units across calculations
- Historical analysis uses quarterly data points for trend assessment
- Industry benchmarks updated based on market evolution
- Risk assessment considers both quantitative and qualitative factors
- Integration with other valuation modules for comprehensive analysis
"""

import numpy as np
import pandas as pd
import logging
import yfinance as yf
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PBValuator:
    """
    Handles Price-to-Book ratio valuation analysis and industry comparisons
    """

    def __init__(self, financial_calculator):
        """
        Initialize P/B valuator with financial calculator

        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator
        self.industry_data_cache = {}
        self.historical_data_cache = {}

        # Get enhanced data manager if available
        self.enhanced_data_manager = getattr(financial_calculator, 'enhanced_data_manager', None)
        if self.enhanced_data_manager:
            logger.info("PB valuator initialized with enhanced multi-source data access")

        # Industry P/B benchmarks (typical ranges by sector)
        self.industry_benchmarks = {
            'Technology': {'median': 3.5, 'low': 1.5, 'high': 8.0},
            'Healthcare': {'median': 2.8, 'low': 1.2, 'high': 6.0},
            'Financial Services': {'median': 1.2, 'low': 0.8, 'high': 2.0},
            'Consumer Cyclical': {'median': 2.0, 'low': 0.8, 'high': 4.5},
            'Consumer Defensive': {'median': 2.5, 'low': 1.2, 'high': 4.0},
            'Industrial': {'median': 2.2, 'low': 1.0, 'high': 4.0},
            'Energy': {'median': 1.5, 'low': 0.5, 'high': 3.0},
            'Utilities': {'median': 1.8, 'low': 1.0, 'high': 2.5},
            'Real Estate': {'median': 1.4, 'low': 0.8, 'high': 2.2},
            'Materials': {'median': 1.8, 'low': 0.9, 'high': 3.5},
            'Communication Services': {'median': 2.8, 'low': 1.0, 'high': 5.5},
            'Default': {'median': 2.0, 'low': 1.0, 'high': 4.0},
        }

    def calculate_pb_analysis(self, ticker_symbol: str = None) -> Dict[str, Any]:
        """
        Calculate comprehensive Price-to-Book (P/B) ratio analysis and valuation.

        This method performs a complete P/B analysis including current ratio calculation,
        industry benchmarking, historical trend analysis, and valuation assessment using
        book value as a fundamental metric for investment evaluation.

        Parameters
        ----------
        ticker_symbol : str, optional
            Stock ticker symbol for analysis. If None, uses ticker from financial_calculator.
            Example: 'AAPL', 'MSFT', 'BRK-B'

        Returns
        -------
        dict
            Comprehensive P/B analysis results containing:

            - pb_ratio : float
                Current Price-to-Book ratio (Market Price / Book Value per Share)
            - book_value_per_share : float
                Calculated book value per share from balance sheet data
            - current_price : float
                Current market price per share
            - market_cap : float
                Current market capitalization
            - industry_comparison : dict
                Comparison with industry P/B benchmarks and percentile ranking
            - historical_analysis : dict
                Historical P/B trend analysis over specified time period
            - valuation_assessment : dict
                Fair value estimates based on industry P/B multiples
            - risk_assessment : dict
                Assessment of P/B-related investment risks and considerations
            - quality_metrics : dict
                Book value quality indicators and reliability metrics
            - market_data : dict
                Current market information and key statistics

        Examples
        --------
        Basic P/B analysis:

        >>> pb_valuator = PBValuator(financial_calculator)
        >>> result = pb_valuator.calculate_pb_analysis('AAPL')
        >>> print(f"Current P/B: {result['pb_ratio']:.2f}")
        >>> print(f"Book Value per Share: ${result['book_value_per_share']:.2f}")

        Industry comparison analysis:

        >>> result = pb_valuator.calculate_pb_analysis('JPM')
        >>> industry_comp = result['industry_comparison']
        >>> print(f"Industry Position: {industry_comp['position']}")
        >>> print(f"Industry Median P/B: {industry_comp['benchmarks']['median']:.2f}")

        Historical trend analysis:

        >>> result = pb_valuator.calculate_pb_analysis('MSFT')
        >>> historical = result['historical_analysis']
        >>> print(f"5-Year P/B Range: {historical['min_pb']:.2f} - {historical['max_pb']:.2f}")
        >>> print(f"Current vs Historical: {historical['percentile_rank']:.0f}th percentile")

        Notes
        -----
        - Book value calculated from shareholders' equity and shares outstanding
        - Industry benchmarks based on sector-specific P/B ratio ranges
        - Historical analysis covers 5-year period with quarterly data points
        - Valuation assessment considers both current and historical context
        - Risk assessment includes book value quality and market conditions
        - Returns error information if required data is unavailable

        P/B Ratio Interpretation
        -----------------------
        - P/B < 1.0: Trading below book value (potential value or distress)
        - P/B 1.0-3.0: Typical range for many industries
        - P/B > 3.0: Premium valuation (growth expectations or intangible assets)
        - Industry context is crucial for proper interpretation

        Raises
        ------
        Returns error dict with 'error' and 'error_message' keys if:
        - Ticker symbol is unavailable or invalid
        - Market data cannot be retrieved
        - Book value per share cannot be calculated
        - Essential financial data is missing
        """
        try:
            # Use ticker from financial calculator if not provided
            if not ticker_symbol:
                ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)

            if not ticker_symbol:
                logger.error("No ticker symbol available for P/B analysis")
                return {
                    'error': 'ticker_unavailable',
                    'error_message': 'Ticker symbol is required for P/B analysis',
                }

            # Get current market data
            market_data = self._get_market_data(ticker_symbol)
            if not market_data or 'current_price' not in market_data:
                return {
                    'error': 'market_data_unavailable',
                    'error_message': 'Unable to fetch current market data',
                }

            # Calculate book value per share
            book_value_per_share = self._calculate_book_value_per_share()
            if book_value_per_share is None:
                return {
                    'error': 'book_value_unavailable',
                    'error_message': 'Unable to calculate book value per share',
                }

            # Calculate current P/B ratio
            current_price = market_data['current_price']
            pb_ratio = current_price / book_value_per_share if book_value_per_share > 0 else None

            # Calculate market cap correctly (price × shares) instead of relying on API value
            # Some APIs provide market cap in thousands or millions, causing display issues
            shares_outstanding = market_data.get('shares_outstanding', 0)
            calculated_market_cap = (
                current_price * shares_outstanding
                if (current_price and shares_outstanding)
                else market_data.get('market_cap', 0)
            )

            # Get industry information
            industry_info = self._get_industry_info(ticker_symbol)
            industry_comparison = self._compare_to_industry(
                pb_ratio, industry_info.get('industry_key', 'Default')
            )

            # Historical P/B analysis
            historical_analysis = self._analyze_historical_pb(ticker_symbol, years=5)

            # P/B based valuation ranges
            valuation_analysis = self._calculate_pb_valuation(
                book_value_per_share, industry_info.get('industry_key', 'Default')
            )

            # Risk assessment
            risk_assessment = self._assess_pb_risks(
                pb_ratio, book_value_per_share, historical_analysis
            )

            result = {
                'ticker_symbol': ticker_symbol,
                'analysis_date': datetime.now().isoformat(),
                'current_data': {
                    'current_price': current_price,
                    'book_value_per_share': book_value_per_share,
                    'pb_ratio': pb_ratio,
                    'shares_outstanding': shares_outstanding,
                    'market_cap': calculated_market_cap,
                },
                'industry_info': industry_info,
                'industry_comparison': industry_comparison,
                'historical_analysis': historical_analysis,
                'valuation_analysis': valuation_analysis,
                'risk_assessment': risk_assessment,
                'currency': getattr(self.financial_calculator, 'currency', 'USD'),
                'is_tase_stock': getattr(self.financial_calculator, 'is_tase_stock', False),
            }

            logger.info(
                f"P/B Analysis completed for {ticker_symbol}: P/B = {pb_ratio:.2f}"
                if pb_ratio
                else f"P/B Analysis completed for {ticker_symbol}: Book value calculation failed"
            )
            return result

        except Exception as e:
            logger.error(f"Error in P/B analysis: {e}")
            return {'error': 'calculation_failed', 'error_message': str(e)}

    def _calculate_book_value_per_share(self) -> Optional[float]:
        """
        Calculate book value per share from multiple data sources with enhanced fallback

        Returns:
            float or None: Book value per share
        """
        try:
            book_value_per_share = None
            data_source_used = None

            # Try enhanced data manager first if available
            if self.enhanced_data_manager:
                try:
                    book_value_per_share = self._calculate_bvps_from_enhanced_data()
                    if book_value_per_share:
                        data_source_used = "enhanced_data_manager"
                        logger.info(
                            f"Successfully calculated BVPS from enhanced data manager: ${book_value_per_share:.2f}"
                        )
                except Exception as e:
                    logger.warning(f"Enhanced data manager BVPS calculation failed: {e}")

            # Fallback to financial calculator's balance sheet data
            if not book_value_per_share:
                book_value_per_share = self._calculate_bvps_from_statements()
                if book_value_per_share:
                    data_source_used = "financial_statements"
                    logger.info(
                        f"Successfully calculated BVPS from financial statements: ${book_value_per_share:.2f}"
                    )

            # Log data source used
            if book_value_per_share and data_source_used:
                logger.info(
                    f"Book value per share calculation used data source: {data_source_used}"
                )

            return book_value_per_share

        except Exception as e:
            logger.error(f"Error calculating book value per share: {e}")
            return None

    def _calculate_bvps_from_enhanced_data(self) -> Optional[float]:
        """
        Calculate book value per share using enhanced data manager

        Returns:
            float or None: Book value per share from enhanced data
        """
        try:
            if not self.enhanced_data_manager:
                return None

            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
            if not ticker_symbol:
                return None

            # Import required modules for enhanced data request
            from data_sources import FinancialDataRequest

            # Create request for balance sheet data
            request = FinancialDataRequest(
                ticker=ticker_symbol,
                data_types=['balance_sheet', 'fundamentals'],
                force_refresh=False,
            )

            # Fetch data through unified adapter
            response = self.enhanced_data_manager.unified_adapter.fetch_data(request)

            if not response.success or not response.data:
                logger.info(
                    f"Enhanced data manager returned no balance sheet data for {ticker_symbol}"
                )
                return None

            # Extract shareholders' equity from API response
            shareholders_equity = self._extract_equity_from_api_response(response.data)
            if not shareholders_equity:
                return None

            # Get shares outstanding (try API first, then financial calculator)
            shares_outstanding = self._get_shares_outstanding_from_api(response.data)
            if not shares_outstanding:
                shares_outstanding = getattr(self.financial_calculator, 'shares_outstanding', None)

            if not shares_outstanding or shares_outstanding <= 0:
                logger.warning(
                    "Cannot calculate BVPS from enhanced data: shares outstanding unavailable"
                )
                return None

            # Calculate book value per share
            # API data is typically in actual currency units (not millions)
            book_value_per_share = shareholders_equity / shares_outstanding

            logger.info(
                f"Enhanced BVPS calculation: Equity=${shareholders_equity:,.0f}, Shares={shares_outstanding/1000000:.1f}M, BVPS=${book_value_per_share:.2f}"
            )
            return book_value_per_share

        except Exception as e:
            logger.warning(f"Error calculating BVPS from enhanced data: {e}")
            return None

    def _extract_equity_from_api_response(self, api_data) -> Optional[float]:
        """
        Extract shareholders' equity from API response data

        Args:
            api_data (dict): Raw API response data

        Returns:
            float or None: Shareholders' equity value
        """
        try:
            if not api_data:
                return None

            # Debug: log key data types for troubleshooting
            logger.debug(
                f"API data structure - keys: {list(api_data.keys()) if isinstance(api_data, dict) else type(api_data)}"
            )

            # Look for balance sheet data in various formats
            balance_sheet_data = None
            if 'balance_sheet' in api_data:
                balance_sheet_data = api_data['balance_sheet']
                logger.debug(f"Found balance_sheet of type: {type(balance_sheet_data)}")

                # Handle balance sheet as list (common in Alpha Vantage format)
                if isinstance(balance_sheet_data, list) and balance_sheet_data:
                    logger.debug(f"Balance sheet is list with {len(balance_sheet_data)} entries")
                    # Use most recent entry (usually first in list)
                    recent_bs = balance_sheet_data[0] if balance_sheet_data else {}
                    logger.debug(
                        f"Recent balance sheet keys: {list(recent_bs.keys()) if isinstance(recent_bs, dict) else type(recent_bs)}"
                    )

                    # Look for equity in the recent balance sheet entry
                    if isinstance(recent_bs, dict):
                        for field_name, value in recent_bs.items():
                            if isinstance(field_name, str) and isinstance(value, (int, float, str)):
                                field_lower = (
                                    str(field_name).lower().replace('_', ' ').replace('-', ' ')
                                )

                                # Check if this looks like an equity field
                                equity_keywords = [
                                    'total stockholder equity',
                                    'stockholder equity',
                                    'shareholders equity',
                                    'total equity',
                                    'equity',
                                    'stockholders equity',
                                    'common stockholder equity',
                                ]

                                for keyword in equity_keywords:
                                    if keyword in field_lower:
                                        try:
                                            equity_value = (
                                                float(str(value).replace(',', ''))
                                                if isinstance(value, str)
                                                else float(value)
                                            )
                                            if equity_value > 0:
                                                logger.info(
                                                    f"Found shareholders' equity in list format: {field_name} = ${equity_value:,.0f}"
                                                )
                                                return equity_value
                                        except (ValueError, TypeError):
                                            continue
            elif 'financials' in api_data and 'balance_sheet' in api_data['financials']:
                balance_sheet_data = api_data['financials']['balance_sheet']
            elif 'fundamentals' in api_data:
                # Some APIs provide equity directly in fundamentals
                fundamentals = api_data['fundamentals']
                equity_fields = [
                    'total_shareholders_equity',
                    'shareholders_equity',
                    'stockholders_equity',
                    'total_equity',
                    'book_value_total',
                    'total_stockholders_equity',
                ]

                for field in equity_fields:
                    if field in fundamentals and fundamentals[field]:
                        equity_value = fundamentals[field]
                        if isinstance(equity_value, (int, float)) and equity_value > 0:
                            return float(equity_value)

            if not balance_sheet_data:
                return None

            # Extract equity from balance sheet structure
            equity_keywords = [
                'total_shareholders_equity',
                'shareholders_equity',
                'stockholders_equity',
                'total_equity',
                'total_stockholders_equity',
                'common_stockholders_equity',
                'book_value',
                'net_worth',
                'owners_equity',
            ]

            # Handle different balance sheet formats
            if isinstance(balance_sheet_data, dict):
                # Look for equity in current period or most recent data
                for period, period_data in balance_sheet_data.items():
                    if isinstance(period_data, dict):
                        for field_name, value in period_data.items():
                            if isinstance(field_name, str) and isinstance(value, (int, float)):
                                field_lower = field_name.lower().replace('_', ' ').replace('-', ' ')

                                for keyword in equity_keywords:
                                    keyword_normalized = keyword.lower().replace('_', ' ')
                                    if keyword_normalized in field_lower and value > 0:
                                        logger.info(
                                            f"Found shareholders' equity in API data: {field_name} = ${value:,.0f}"
                                        )
                                        return float(value)

                # Also check at the top level
                for field_name, value in balance_sheet_data.items():
                    if isinstance(field_name, str) and isinstance(value, (int, float)):
                        field_lower = field_name.lower().replace('_', ' ').replace('-', ' ')

                        for keyword in equity_keywords:
                            keyword_normalized = keyword.lower().replace('_', ' ')
                            if keyword_normalized in field_lower and value > 0:
                                logger.info(
                                    f"Found shareholders' equity in API data: {field_name} = ${value:,.0f}"
                                )
                                return float(value)

            logger.warning("Could not find shareholders' equity in API balance sheet data")
            return None

        except Exception as e:
            logger.error(f"Error extracting equity from API response: {e}")
            return None

    def _get_shares_outstanding_from_api(self, api_data) -> Optional[float]:
        """
        Extract shares outstanding from API response data

        Args:
            api_data (dict): Raw API response data

        Returns:
            float or None: Shares outstanding
        """
        try:
            if not api_data:
                return None

            # Look for shares outstanding in various places
            shares_fields = [
                'shares_outstanding',
                'common_shares_outstanding',
                'weighted_average_shares',
                'basic_shares_outstanding',
                'diluted_shares_outstanding',
            ]

            # Check fundamentals first
            if 'fundamentals' in api_data:
                fundamentals = api_data['fundamentals']
                for field in shares_fields:
                    if field in fundamentals and fundamentals[field]:
                        shares = fundamentals[field]
                        if isinstance(shares, (int, float)) and shares > 0:
                            return float(shares)

            # Check balance sheet data
            if 'balance_sheet' in api_data:
                balance_sheet = api_data['balance_sheet']
                if isinstance(balance_sheet, dict):
                    for period, period_data in balance_sheet.items():
                        if isinstance(period_data, dict):
                            for field in shares_fields:
                                if field in period_data and period_data[field]:
                                    shares = period_data[field]
                                    if isinstance(shares, (int, float)) and shares > 0:
                                        return float(shares)

            return None

        except Exception as e:
            logger.warning(f"Error extracting shares outstanding from API: {e}")
            return None

    def _calculate_bvps_from_statements(self) -> Optional[float]:
        """
        Calculate book value per share from financial statements (fallback method)

        Returns:
            float or None: Book value per share from statements
        """
        try:
            # Get balance sheet data
            balance_sheet_data = self.financial_calculator.financial_data.get('Balance Sheet', {})
            if not balance_sheet_data:
                # Try alternative key names
                for key in ['balance_fy', 'balance_ltm', 'balance_sheet']:
                    balance_sheet_data = self.financial_calculator.financial_data.get(key, {})
                    if balance_sheet_data:
                        break

            if not balance_sheet_data:
                logger.warning("No balance sheet data available for book value calculation")
                return None

            # Find shareholders' equity
            shareholders_equity = self._extract_shareholders_equity(balance_sheet_data)
            if shareholders_equity is None:
                logger.warning("Could not extract shareholders' equity from balance sheet")
                return None

            # Get shares outstanding
            shares_outstanding = getattr(self.financial_calculator, 'shares_outstanding', None)
            if not shares_outstanding or shares_outstanding <= 0:
                # Try to get from market data
                market_data = self._get_market_data(self.financial_calculator.ticker_symbol)
                shares_outstanding = market_data.get('shares_outstanding', 0) if market_data else 0

            if not shares_outstanding or shares_outstanding <= 0:
                logger.warning(
                    "Cannot calculate book value per share: shares outstanding unavailable"
                )
                return None

            # Calculate book value per share
            # Note: shareholders_equity is typically in millions, convert to actual currency units
            equity_actual = shareholders_equity * 1_000_000  # Convert millions to actual units
            book_value_per_share = equity_actual / shares_outstanding

            logger.info(
                f"Book value calculation: Equity=${shareholders_equity:.1f}M, Shares={shares_outstanding/1000000:.1f}M, BVPS=${book_value_per_share:.2f}"
            )
            return book_value_per_share

        except Exception as e:
            logger.error(f"Error calculating book value per share: {e}")
            return None

    def _extract_shareholders_equity(self, balance_sheet_data: Dict) -> Optional[float]:
        """
        Extract shareholders' equity from balance sheet data

        Args:
            balance_sheet_data (dict): Balance sheet data

        Returns:
            float or None: Shareholders' equity in millions
        """
        equity_keywords = [
            'shareholders equity',
            'stockholders equity',
            'shareholders\' equity',
            'stockholders\' equity',
            'total equity',
            'total shareholders equity',
            'total stockholders equity',
            'total stockholder equity',
            'stockholder equity',  # Added variants without 's'
            'book value',
            'net worth',
            'owners equity',
            'equity attributable to shareholders',
            'total equity attributable to shareholders',
            'common stockholders equity',
            'common stockholder equity',  # Added variant without 's'
        ]

        for year_data in balance_sheet_data.values():
            if isinstance(year_data, dict):
                for key, value in year_data.items():
                    if isinstance(key, str) and isinstance(value, (int, float)):
                        key_lower = key.lower().strip()

                        for equity_keyword in equity_keywords:
                            if equity_keyword in key_lower:
                                logger.info(f"Found shareholders' equity: {key} = ${value:.1f}M")
                                return abs(value)  # Ensure positive value

        logger.warning("Could not find shareholders' equity in balance sheet data")
        return None

    def _get_market_data(self, ticker_symbol: str) -> Optional[Dict]:
        """
        Get current market data for the ticker using enhanced data sources

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            dict or None: Market data
        """
        try:
            # Use financial calculator's enhanced market data fetching if available
            if hasattr(self.financial_calculator, 'fetch_market_data'):
                market_data = self.financial_calculator.fetch_market_data(ticker_symbol)
                if market_data:
                    logger.debug("Using enhanced market data from financial calculator")
                    return market_data

            # Try enhanced data manager directly if financial calculator doesn't have it
            if self.enhanced_data_manager:
                try:
                    market_data = self.enhanced_data_manager.fetch_market_data(ticker_symbol)
                    if market_data:
                        logger.debug("Using market data from enhanced data manager")
                        return market_data
                except Exception as e:
                    logger.warning(f"Enhanced data manager market data fetch failed: {e}")

            # Fallback to yfinance
            logger.info("Falling back to yfinance for market data")
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            return {
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'market_cap': info.get('marketCap', 0),
                'shares_outstanding': info.get(
                    'sharesOutstanding', info.get('impliedSharesOutstanding', 0)
                ),
                'book_value': info.get(
                    'bookValue', 0
                ),  # yfinance calculated book value for comparison
                'price_to_book': info.get('priceToBook', 0),  # yfinance P/B ratio for comparison
            }

        except Exception as e:
            logger.error(f"Error fetching market data for {ticker_symbol}: {e}")
            return None

    def _get_industry_info(self, ticker_symbol: str) -> Dict[str, str]:
        """
        Get industry information for the ticker

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            dict: Industry information
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            sector = info.get('sector', 'Unknown')
            industry_key = self._map_to_benchmark_industry(sector)

            logger.info(
                f"Industry detection for {ticker_symbol}: sector='{sector}', mapped to '{industry_key}'"
            )

            return {
                'industry': info.get('industry', 'Unknown'),
                'sector': sector,
                'industry_key': industry_key,
            }

        except Exception as e:
            logger.warning(f"Could not fetch industry info for {ticker_symbol}: {e}")
            return {'industry': 'Unknown', 'sector': 'Unknown', 'industry_key': 'Default'}

    def _map_to_benchmark_industry(self, sector: str) -> str:
        """
        Map yfinance sector to our benchmark industry categories

        Args:
            sector (str): Sector from yfinance

        Returns:
            str: Mapped industry key
        """
        sector_mapping = {
            'Technology': 'Technology',
            'Healthcare': 'Healthcare',
            'Financial Services': 'Financial Services',
            'Consumer Cyclical': 'Consumer Cyclical',
            'Consumer Defensive': 'Consumer Defensive',
            'Industrials': 'Industrial',
            'Energy': 'Energy',
            'Utilities': 'Utilities',
            'Real Estate': 'Real Estate',
            'Basic Materials': 'Materials',
            'Communication Services': 'Communication Services',
        }

        return sector_mapping.get(sector, 'Default')

    def _compare_to_industry(self, pb_ratio: Optional[float], industry_key: str) -> Dict[str, Any]:
        """
        Compare P/B ratio to industry benchmarks

        Args:
            pb_ratio (float or None): Current P/B ratio
            industry_key (str): Industry category key

        Returns:
            dict: Industry comparison results
        """
        if pb_ratio is None:
            return {'error': 'pb_ratio_unavailable'}

        benchmarks = self.industry_benchmarks.get(industry_key, self.industry_benchmarks['Default'])

        # Determine position relative to industry
        if pb_ratio < benchmarks['low']:
            position = 'Below Industry Range'
            percentile = 'Bottom 25%'
        elif pb_ratio > benchmarks['high']:
            position = 'Above Industry Range'
            percentile = 'Top 25%'
        elif pb_ratio < benchmarks['median']:
            position = 'Below Industry Median'
            percentile = '25-50%'
        else:
            position = 'Above Industry Median'
            percentile = '50-75%'

        # Calculate discount/premium to median
        discount_premium = (pb_ratio - benchmarks['median']) / benchmarks['median']

        return {
            'industry_key': industry_key,
            'benchmarks': benchmarks,
            'current_pb': pb_ratio,
            'position': position,
            'percentile': percentile,
            'discount_premium_to_median': discount_premium,
            'analysis': self._generate_industry_analysis(pb_ratio, benchmarks, position),
        }

    def _generate_industry_analysis(self, pb_ratio: float, benchmarks: Dict, position: str) -> str:
        """
        Generate textual analysis of industry comparison

        Args:
            pb_ratio (float): Current P/B ratio
            benchmarks (dict): Industry benchmarks
            position (str): Position relative to industry

        Returns:
            str: Analysis text
        """
        if position == 'Below Industry Range':
            return f"Trading at P/B of {pb_ratio:.2f}, significantly below industry low of {benchmarks['low']:.2f}. May indicate undervaluation or fundamental issues."
        elif position == 'Above Industry Range':
            return f"Trading at P/B of {pb_ratio:.2f}, significantly above industry high of {benchmarks['high']:.2f}. May indicate overvaluation or premium quality."
        elif position == 'Below Industry Median':
            return f"Trading at P/B of {pb_ratio:.2f}, below industry median of {benchmarks['median']:.2f}. Potentially attractive relative to peers."
        else:
            return f"Trading at P/B of {pb_ratio:.2f}, above industry median of {benchmarks['median']:.2f}. Trading at premium to peers."

    def _analyze_historical_pb(self, ticker_symbol: str, years: int = 5) -> Dict[str, Any]:
        """
        Analyze historical P/B ratio trends

        Args:
            ticker_symbol (str): Stock ticker symbol
            years (int): Number of years of historical data

        Returns:
            dict: Historical P/B analysis
        """
        try:
            # Get historical price and book value data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            ticker = yf.Ticker(ticker_symbol)

            # Get historical price data
            hist_prices = ticker.history(
                start=start_date, end=end_date, interval='3mo'
            )  # Quarterly data

            if hist_prices.empty:
                return {'error': 'no_historical_data'}

            # Get quarterly fundamentals for book value
            quarterly_bs = ticker.quarterly_balance_sheet

            if quarterly_bs.empty:
                return {'error': 'no_fundamental_data'}

            # Calculate historical P/B ratios
            historical_pb = self._calculate_historical_pb_ratios(hist_prices, quarterly_bs, ticker)

            if not historical_pb:
                return {'error': 'pb_calculation_failed'}

            # Statistical analysis
            pb_values = [
                entry['pb_ratio'] for entry in historical_pb if entry['pb_ratio'] is not None
            ]

            if len(pb_values) < 2:
                return {'error': 'insufficient_data'}

            stats = {
                'min': min(pb_values),
                'max': max(pb_values),
                'mean': np.mean(pb_values),
                'median': np.median(pb_values),
                'std': np.std(pb_values),
                'current_percentile': (
                    self._calculate_percentile(pb_values[-1], pb_values) if pb_values else None
                ),
            }

            # Trend analysis
            trend_analysis = self._analyze_pb_trend(pb_values)

            return {
                'period': f'{years} years',
                'data_points': len(pb_values),
                'historical_data': historical_pb[-20:],  # Last 20 quarters
                'statistics': stats,
                'trend_analysis': trend_analysis,
                'interpretation': self._interpret_historical_pb(stats, trend_analysis),
            }

        except Exception as e:
            logger.error(f"Error in historical P/B analysis: {e}")
            return {'error': 'analysis_failed', 'error_message': str(e)}

    def _calculate_historical_pb_ratios(
        self, hist_prices: pd.DataFrame, quarterly_bs: pd.DataFrame, ticker
    ) -> List[Dict]:
        """
        Calculate historical P/B ratios from price and balance sheet data

        Args:
            hist_prices (pd.DataFrame): Historical price data
            quarterly_bs (pd.DataFrame): Quarterly balance sheet data
            ticker: yfinance ticker object

        Returns:
            list: Historical P/B data points
        """
        historical_pb = []

        try:
            # Get shares outstanding history
            shares_info = ticker.get_shares_full()

            for date, price_row in hist_prices.iterrows():
                try:
                    price = price_row['Close']

                    # Find closest balance sheet date
                    closest_bs_date = None
                    for bs_date in quarterly_bs.columns:
                        if bs_date <= date:
                            if closest_bs_date is None or bs_date > closest_bs_date:
                                closest_bs_date = bs_date

                    if closest_bs_date is None:
                        continue

                    # Get shareholders' equity
                    bs_data = quarterly_bs[closest_bs_date]
                    equity = None

                    # Look for equity in balance sheet
                    equity_fields = [
                        'Total Stockholder Equity',
                        'Stockholders Equity',
                        'Total Equity',
                    ]
                    for field in equity_fields:
                        if field in bs_data.index and pd.notna(bs_data[field]):
                            equity = bs_data[field]
                            break

                    if equity is None or equity <= 0:
                        continue

                    # Get shares outstanding for this period
                    shares = None
                    if shares_info is not None and not shares_info.empty:
                        # Find closest shares data
                        shares_dates = shares_info.index
                        closest_shares_date = None
                        for shares_date in shares_dates:
                            if shares_date <= date:
                                if closest_shares_date is None or shares_date > closest_shares_date:
                                    closest_shares_date = shares_date

                        if closest_shares_date is not None:
                            shares = shares_info.loc[closest_shares_date]

                    # Fallback to current shares if historical not available
                    if shares is None or shares <= 0:
                        shares = getattr(self.financial_calculator, 'shares_outstanding', None)
                        if not shares:
                            ticker_info = ticker.info
                            shares = ticker_info.get(
                                'sharesOutstanding', ticker_info.get('impliedSharesOutstanding', 0)
                            )

                    if shares and shares > 0:
                        book_value_per_share = equity / shares
                        pb_ratio = (
                            price / book_value_per_share if book_value_per_share > 0 else None
                        )

                        historical_pb.append(
                            {
                                'date': date.strftime('%Y-%m-%d'),
                                'price': price,
                                'book_value_per_share': book_value_per_share,
                                'pb_ratio': pb_ratio,
                                'shares_outstanding': shares,
                            }
                        )

                except Exception as e:
                    logger.debug(f"Error processing historical data for {date}: {e}")
                    continue

            return historical_pb

        except Exception as e:
            logger.error(f"Error calculating historical P/B ratios: {e}")
            return []

    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """
        Calculate percentile of a value within a list of values

        Args:
            value (float): Value to find percentile for
            values (list): List of values

        Returns:
            float: Percentile (0-100)
        """
        return (sum(1 for v in values if v <= value) / len(values)) * 100

    def _analyze_pb_trend(self, pb_values: List[float]) -> Dict[str, Any]:
        """
        Analyze trend in P/B values

        Args:
            pb_values (list): List of P/B values over time

        Returns:
            dict: Trend analysis
        """
        if len(pb_values) < 3:
            return {'trend': 'insufficient_data'}

        # Calculate linear trend
        x = np.arange(len(pb_values))
        coeffs = np.polyfit(x, pb_values, 1)
        slope = coeffs[0]

        # Determine trend direction
        if abs(slope) < 0.01:  # Less than 1% change per period
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        # Calculate volatility
        volatility = np.std(pb_values) / np.mean(pb_values) if np.mean(pb_values) > 0 else 0

        return {
            'trend': trend,
            'slope': slope,
            'volatility': volatility,
            'recent_vs_historical': (
                pb_values[-1] / np.mean(pb_values[:-1]) - 1 if len(pb_values) > 1 else 0
            ),
        }

    def _interpret_historical_pb(self, stats: Dict, trend_analysis: Dict) -> str:
        """
        Generate interpretation of historical P/B analysis

        Args:
            stats (dict): Statistical summary
            trend_analysis (dict): Trend analysis

        Returns:
            str: Interpretation text
        """
        current_pb = stats.get('mean', 0)  # Using mean as proxy for current
        percentile = stats.get('current_percentile', 50)
        trend = trend_analysis.get('trend', 'stable')

        interpretation = f"Current P/B is at {percentile:.0f}th percentile of historical range. "

        if percentile < 25:
            interpretation += "Trading near historical lows. "
        elif percentile > 75:
            interpretation += "Trading near historical highs. "
        else:
            interpretation += "Trading within normal historical range. "

        if trend == 'increasing':
            interpretation += "P/B ratio has been trending upward."
        elif trend == 'decreasing':
            interpretation += "P/B ratio has been trending downward."
        else:
            interpretation += "P/B ratio has been relatively stable."

        return interpretation

    def _calculate_pb_valuation(
        self, book_value_per_share: float, industry_key: str
    ) -> Dict[str, Any]:
        """
        Calculate valuation ranges based on P/B analysis

        Args:
            book_value_per_share (float): Current book value per share
            industry_key (str): Industry category

        Returns:
            dict: Valuation analysis based on P/B
        """
        benchmarks = self.industry_benchmarks.get(industry_key, self.industry_benchmarks['Default'])

        return {
            'book_value_per_share': book_value_per_share,
            'valuation_ranges': {
                'conservative': book_value_per_share * benchmarks['low'],
                'fair_value': book_value_per_share * benchmarks['median'],
                'optimistic': book_value_per_share * benchmarks['high'],
            },
            'methodology': 'Based on industry P/B ratio benchmarks',
            'industry_benchmarks': benchmarks,
        }

    def _assess_pb_risks(
        self,
        pb_ratio: Optional[float],
        book_value_per_share: Optional[float],
        historical_analysis: Dict,
    ) -> Dict[str, Any]:
        """
        Assess risks related to P/B analysis

        Args:
            pb_ratio (float or None): Current P/B ratio
            book_value_per_share (float or None): Book value per share
            historical_analysis (dict): Historical P/B analysis

        Returns:
            dict: Risk assessment
        """
        risks = []
        risk_level = 'Low'

        if pb_ratio is None:
            risks.append("Unable to calculate P/B ratio")
            risk_level = 'High'
            return {'risks': risks, 'risk_level': risk_level}

        if book_value_per_share is None or book_value_per_share <= 0:
            risks.append("Negative or zero book value indicates potential financial distress")
            risk_level = 'High'

        if pb_ratio < 0.5:
            risks.append(
                "Extremely low P/B ratio may indicate market skepticism about asset values"
            )
            risk_level = 'High' if risk_level != 'High' else risk_level
        elif pb_ratio > 10:
            risks.append("Very high P/B ratio suggests significant premium valuation")
            risk_level = 'High' if risk_level != 'High' else risk_level

        # Historical volatility risk
        if (
            'statistics' in historical_analysis
            and historical_analysis['statistics'].get('std', 0) > 1
        ):
            risks.append("High historical P/B volatility indicates uncertain valuation")
            risk_level = 'Medium' if risk_level == 'Low' else risk_level

        # Trend risk
        if 'trend_analysis' in historical_analysis:
            trend = historical_analysis['trend_analysis'].get('trend')
            if trend == 'decreasing':
                risks.append("Declining P/B trend may indicate deteriorating fundamentals")
                risk_level = 'Medium' if risk_level == 'Low' else risk_level

        if not risks:
            risks.append("No significant P/B-related risks identified")

        return {
            'risks': risks,
            'risk_level': risk_level,
            'risk_score': len([r for r in risks if 'High' in risk_level]) * 3
            + len([r for r in risks if 'Medium' in risk_level]) * 2
            + len([r for r in risks if 'Low' in risk_level]) * 1,
        }

    def create_pb_summary_report(self, pb_analysis: Dict) -> str:
        """
        Create a summary report of P/B analysis

        Args:
            pb_analysis (dict): P/B analysis results

        Returns:
            str: Formatted summary report
        """
        if 'error' in pb_analysis:
            return f"P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error')}"

        ticker = pb_analysis.get('ticker_symbol', 'Unknown')
        current_data = pb_analysis.get('current_data', {})
        pb_ratio = current_data.get('pb_ratio')

        if pb_ratio is None:
            return f"P/B Analysis for {ticker}: Unable to calculate P/B ratio"

        report = f"P/B Analysis Summary for {ticker}\n"
        report += "=" * 40 + "\n\n"

        # Current metrics
        report += f"Current Price: ${current_data.get('current_price', 0):.2f}\n"
        report += f"Book Value per Share: ${current_data.get('book_value_per_share', 0):.2f}\n"
        report += f"P/B Ratio: {pb_ratio:.2f}\n\n"

        # Industry comparison
        industry_comp = pb_analysis.get('industry_comparison', {})
        if 'position' in industry_comp:
            report += f"Industry Position: {industry_comp['position']}\n"
            report += f"Industry Analysis: {industry_comp.get('analysis', 'N/A')}\n\n"

        # Valuation ranges
        valuation = pb_analysis.get('valuation_analysis', {})
        if 'valuation_ranges' in valuation:
            ranges = valuation['valuation_ranges']
            report += "P/B Based Valuation Ranges:\n"
            report += f"  Conservative: ${ranges.get('conservative', 0):.2f}\n"
            report += f"  Fair Value: ${ranges.get('fair_value', 0):.2f}\n"
            report += f"  Optimistic: ${ranges.get('optimistic', 0):.2f}\n\n"

        # Risk assessment
        risk_assess = pb_analysis.get('risk_assessment', {})
        if 'risk_level' in risk_assess:
            report += f"Risk Level: {risk_assess['risk_level']}\n"
            risks = risk_assess.get('risks', [])
            if risks:
                report += "Key Risks:\n"
                for risk in risks[:3]:  # Top 3 risks
                    report += f"  • {risk}\n"

        return report
