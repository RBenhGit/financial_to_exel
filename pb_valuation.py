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
                                    'shareholder equity',
                                    'shareowners equity',
                                    'common equity',
                                    'book value',
                                    'net worth',
                                    'owners equity',
                                    'equity attributable to shareholders',
                                    'common shareholders equity',
                                    'total shareholders equity',
                                    'net equity',
                                    'shareholders funds',
                                    'equity capital'
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
                # Standard underscore variations for API data
                'total_shareholders_equity',
                'shareholders_equity',
                'stockholders_equity',
                'total_equity',
                'total_stockholders_equity',
                'common_stockholders_equity',
                'book_value',
                'net_worth',
                'owners_equity',
                'shareowners_equity',
                'total_shareowners_equity',
                'stockholder_equity',
                'shareholder_equity',
                'common_equity',
                'common_stock_equity',
                'equity_attributable_to_shareholders',
                'equity_attributable_to_stockholders',
                'total_equity_attributable_to_shareholders',
                'total_equity_attributable_to_stockholders',
                'net_equity',
                'total_net_equity',
                'shareholders_funds',
                'stockholders_funds',
                'equity_capital',
                'tangible_book_value',
                'net_book_value',
                'common_shareholders_equity',
                'common_shareholder_equity',
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
            # Use safe checking for DataFrame/dict
            balance_sheet_empty = (balance_sheet_data is None or 
                                 (hasattr(balance_sheet_data, 'empty') and balance_sheet_data.empty) or 
                                 (isinstance(balance_sheet_data, dict) and not balance_sheet_data))
            
            if balance_sheet_empty:
                # Try alternative key names
                for key in ['balance_fy', 'balance_ltm', 'balance_sheet']:
                    balance_sheet_data = self.financial_calculator.financial_data.get(key, {})
                    # Check if we found valid data
                    if balance_sheet_data is not None:
                        if hasattr(balance_sheet_data, 'empty') and not balance_sheet_data.empty:
                            break  # Found non-empty DataFrame
                        elif isinstance(balance_sheet_data, dict) and balance_sheet_data:
                            break  # Found non-empty dict

            # Handle both DataFrame and dict formats
            if balance_sheet_data is None or (hasattr(balance_sheet_data, 'empty') and balance_sheet_data.empty) or (isinstance(balance_sheet_data, dict) and not balance_sheet_data):
                logger.warning("No balance sheet data available for book value calculation")
                return None

            # Find shareholders' equity
            shareholders_equity = self._extract_shareholders_equity(balance_sheet_data)
            if shareholders_equity is None:
                logger.warning("Could not extract shareholders' equity from balance sheet")
                return None

            # Get shares outstanding - prioritize Excel method
            shares_outstanding = None
            shares_data_source = "unknown"
            
            # PRIORITY 1: Try Excel-specific shares outstanding extraction
            if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
                shares_outstanding = self.financial_calculator._extract_excel_shares_outstanding()
                if shares_outstanding and shares_outstanding > 0:
                    shares_data_source = "excel_income_statement"
                    logger.info(f"Using Excel shares outstanding from Income Statement: {shares_outstanding:,.0f}")
            
            # PRIORITY 2: Fallback to cached shares outstanding
            if not shares_outstanding or shares_outstanding <= 0:
                shares_outstanding = getattr(self.financial_calculator, 'shares_outstanding', None)
                if shares_outstanding and shares_outstanding > 0:
                    shares_data_source = "cached_financial_calculator"
            
            # PRIORITY 3: Fallback to market data
            if not shares_outstanding or shares_outstanding <= 0:
                market_data = self._get_market_data(self.financial_calculator.ticker_symbol)
                shares_outstanding = market_data.get('shares_outstanding', 0) if market_data else 0
                if shares_outstanding and shares_outstanding > 0:
                    shares_data_source = "market_data_api"

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
                f"Book value calculation: Equity=${shareholders_equity:.1f}M, Shares={shares_outstanding/1000000:.1f}M, BVPS=${book_value_per_share:.2f} (shares source: {shares_data_source})"
            )
            return book_value_per_share

        except Exception as e:
            logger.error(f"Error calculating book value per share: {e}")
            return None

    def _extract_shareholders_equity(self, balance_sheet_data) -> Optional[float]:
        """
        Extract shareholders' equity from balance sheet data

        Args:
            balance_sheet_data: Balance sheet data (dict or DataFrame)

        Returns:
            float or None: Shareholders' equity in millions
        """
        equity_keywords = [
            # Standard variations
            'shareholders equity',
            'stockholders equity',
            'shareholders\' equity',
            'stockholders\' equity',
            'total equity',
            'total shareholders equity',
            'total stockholders equity',
            'total stockholder equity',
            'stockholder equity',
            'shareholder equity',
            
            # Common international variations
            'shareowners equity',
            'shareowners\' equity',
            'owners equity',
            'owners\' equity',
            
            # Financial statement variations
            'equity attributable to shareholders',
            'equity attributable to stockholders',
            'equity attributable to shareowners',
            'total equity attributable to shareholders',
            'total equity attributable to stockholders',
            'total equity attributable to shareowners',
            
            # Common equity variations
            'common equity',
            'common stock equity',
            'common shareholders equity',
            'common stockholders equity',
            'common stockholder equity',
            'common shareholder equity',
            
            # Book value variations
            'book value',
            'book value of equity',
            'book value of common equity',
            'tangible book value',
            'net book value',
            
            # Other standard terms
            'net worth',
            'net equity',
            'total net equity',
            'shareholders funds',
            'stockholders funds',
            'equity capital',
            'share capital and reserves',
            
            # Parenthetical and formatted variations
            'equity (total)',
            'total (equity)',
            'shareholders equity (total)',
            'stockholders equity (total)',
            'total shareholders\' equity',
            'total stockholders\' equity',
            
            # Abbreviated variations
            'shrhldrs equity',
            'stkhldr equity',
            'sh equity',
            'stk equity',
            
            # International/Regional variations
            'shareholders\' funds',
            'stockholders\' funds',
            'proprietors equity',
            'members equity',
            'partners equity'
        ]

        try:
            # Handle pandas DataFrame format
            if hasattr(balance_sheet_data, 'index') and hasattr(balance_sheet_data, 'columns'):
                # This is a DataFrame - search through all columns for row labels
                import pandas as pd
                
                # Search through each column to find row labels
                for col_idx in range(min(5, balance_sheet_data.shape[1])):  # Check first 5 columns
                    col_data = balance_sheet_data.iloc[:, col_idx]
                    
                    # Look for equity-related entries in this column
                    for row_idx, cell_value in enumerate(col_data):
                        if isinstance(cell_value, str) and cell_value.strip():
                            row_name_lower = cell_value.lower().strip()
                            
                            for equity_keyword in equity_keywords:
                                if equity_keyword in row_name_lower:
                                    # Found equity row, get the most recent financial value
                                    row_data = balance_sheet_data.iloc[row_idx]
                                    
                                    # Look for the most recent year column (typically rightmost FY column)
                                    for col in reversed(balance_sheet_data.columns):
                                        if isinstance(col, str) and col.startswith('FY'):
                                            col_position = balance_sheet_data.columns.get_loc(col)
                                            raw_value = row_data.iloc[col_position]
                                            if pd.notna(raw_value):
                                                # Try to convert to float (handles string numbers with commas)
                                                try:
                                                    if isinstance(raw_value, str):
                                                        # Remove commas and convert
                                                        clean_value = raw_value.replace(',', '').strip()
                                                        value = float(clean_value)
                                                    else:
                                                        value = float(raw_value)
                                                    
                                                    if value != 0:
                                                        logger.info(f"Found shareholders' equity in DataFrame: {cell_value} (row {row_idx}) = ${value:.1f}M")
                                                        return abs(value)  # Ensure positive value
                                                except (ValueError, TypeError):
                                                    continue
                                    
                                    # If no FY columns found, use rightmost numeric column
                                    for col in reversed(balance_sheet_data.columns):
                                        if col is not None:
                                            try:
                                                col_position = balance_sheet_data.columns.get_loc(col)
                                                raw_value = row_data.iloc[col_position]
                                                if pd.notna(raw_value):
                                                    # Try to convert to float (handles string numbers with commas)
                                                    try:
                                                        if isinstance(raw_value, str):
                                                            clean_value = raw_value.replace(',', '').strip()
                                                            value = float(clean_value)
                                                        else:
                                                            value = float(raw_value)
                                                        
                                                        if value != 0:
                                                            logger.info(f"Found shareholders' equity in DataFrame: {cell_value} = ${value:.1f}M")
                                                            return abs(value)
                                                    except (ValueError, TypeError):
                                                        continue
                                            except:
                                                continue
                                        
            # Handle dictionary format (original logic)  
            elif isinstance(balance_sheet_data, dict):
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
            
        except Exception as e:
            logger.error(f"Error extracting shareholders' equity: {e}")
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
        Compare P/B ratio to industry benchmarks (dynamic data required)

        Args:
            pb_ratio (float or None): Current P/B ratio
            industry_key (str): Industry category key

        Returns:
            dict: Industry comparison results or unavailable indicator
        """
        if pb_ratio is None:
            return {'error': 'pb_ratio_unavailable'}

        # Static industry benchmarks removed - dynamic data required
        return {
            'industry_key': industry_key,
            'current_pb': pb_ratio,
            'error': 'industry_benchmarks_unavailable',
            'message': 'Industry comparison requires dynamic data fetching service',
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
            # Request more years than needed to ensure we have data for older Excel years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=max(years * 365, 10 * 365))  # At least 10 years of price data

            ticker = yf.Ticker(ticker_symbol)

            # Get historical price data
            hist_prices = ticker.history(
                start=start_date, end=end_date, interval='3mo'
            )  # Quarterly data

            if hist_prices.empty:
                return {'error': 'no_historical_data'}

            # Try Excel-based historical P/B calculation first (if in Excel mode)
            historical_pb = []
            if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
                logger.info("Attempting historical P/B calculation using Excel annual data")
                historical_pb = self._calculate_historical_pb_ratios_from_excel(hist_prices, ticker_symbol)
                
            # Fall back to API quarterly data if Excel method failed or not in Excel mode
            if not historical_pb:
                logger.info("Falling back to API quarterly data for historical P/B calculation")
                # Get quarterly fundamentals for book value
                quarterly_bs = ticker.quarterly_balance_sheet

                if quarterly_bs.empty:
                    return {'error': 'no_fundamental_data'}

                # Calculate historical P/B ratios using API quarterly data
                historical_pb = self._calculate_historical_pb_ratios(hist_prices, quarterly_bs, ticker)

            if not historical_pb:
                return {'error': 'pb_calculation_failed'}

            # Statistical analysis with enhanced comprehensive statistics
            pb_values = [
                entry['pb_ratio'] for entry in historical_pb if entry['pb_ratio'] is not None
            ]

            # Minimum data points validation (requirement: at least 5 data points for meaningful analysis)
            min_required_points = 5
            if len(pb_values) < min_required_points:
                return {
                    'error': 'insufficient_data_points',
                    'message': f'Insufficient data for meaningful analysis. Found {len(pb_values)} data points, minimum {min_required_points} required.',
                    'data_points_found': len(pb_values),
                    'minimum_required': min_required_points
                }

            # Calculate comprehensive statistics
            pb_array = np.array(pb_values)
            
            # Basic statistics
            min_pb = float(np.min(pb_array))
            max_pb = float(np.max(pb_array)) 
            mean_pb = float(np.mean(pb_array))
            median_pb = float(np.median(pb_array))
            std_pb = float(np.std(pb_array))
            
            # Enhanced statistics - Volatility calculation
            # Coefficient of variation (volatility as percentage of mean)
            volatility = (std_pb / mean_pb * 100) if mean_pb > 0 else 0
            
            # Additional percentile analysis
            percentile_25 = float(np.percentile(pb_array, 25))
            percentile_75 = float(np.percentile(pb_array, 75))
            interquartile_range = percentile_75 - percentile_25
            
            # Current value percentile
            current_percentile = (
                self._calculate_percentile(pb_values[-1], pb_values) if pb_values else None
            )

            stats = {
                'data_points_count': len(pb_values),
                'time_range_years': years,
                'min': min_pb,
                'max': max_pb,
                'mean': mean_pb,
                'median': median_pb,
                'std_deviation': std_pb,
                'volatility_coefficient': volatility,
                'percentile_25': percentile_25,
                'percentile_75': percentile_75,
                'interquartile_range': interquartile_range,
                'current_percentile': current_percentile,
                'range_span': max_pb - min_pb,
                'mean_deviation_from_median': abs(mean_pb - median_pb),
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

    def _calculate_historical_pb_ratios_from_excel(
        self, hist_prices: pd.DataFrame, ticker_symbol: str
    ) -> List[Dict]:
        """
        Calculate historical P/B ratios using Excel annual data instead of quarterly API data
        
        Args:
            hist_prices (pd.DataFrame): Historical price data from API
            ticker_symbol (str): Stock ticker symbol
            
        Returns:
            list: Historical P/B data points using Excel annual data
        """
        historical_pb = []
        
        try:
            # Get annual balance sheet data from Excel
            balance_data = self.financial_calculator.financial_data.get('balance_fy', pd.DataFrame())
            if balance_data.empty:
                logger.warning("No Excel balance sheet data available for historical P/B calculation")
                return []
            
            # Load fiscal year-end dates from metadata file
            fiscal_year_dates = self._load_fiscal_year_dates()
            if not fiscal_year_dates:
                logger.warning("No fiscal year-end dates available, falling back to calendar year assumptions")
                return []
            
            # Get the year columns from the Excel data (should be FY-N format or actual years)
            if hasattr(balance_data, 'columns'):
                excel_columns = balance_data.columns.tolist()
            else:
                logger.warning("Excel balance sheet data has no columns")
                return []
                
            logger.info(f"Found {len(excel_columns)} columns in Excel balance sheet data")
            
            # Filter for year columns (exclude metric names)
            year_columns = []
            for col in excel_columns:
                if isinstance(col, str):
                    if col.startswith('FY') or col.isdigit():
                        year_columns.append(col)
                elif isinstance(col, (int, float)):
                    year_columns.append(col)
            
            logger.info(f"Identified {len(year_columns)} year columns: {year_columns}")
            
            # For each year column in Excel data, find the corresponding price and calculate P/B
            for year_idx, year_col in enumerate(year_columns):
                try:
                    # Skip invalid/empty year columns
                    if year_col is None or year_col == '' or pd.isna(year_col):
                        continue
                    
                    # Get the corresponding fiscal year-end date
                    fiscal_year_end_date = None
                    actual_year = None
                    
                    if isinstance(year_col, (int, float)):
                        actual_year = int(year_col)
                    elif isinstance(year_col, str):
                        if year_col.startswith('FY-'):
                            try:
                                years_back = int(year_col.replace('FY-', ''))
                                current_year = datetime.now().year
                                actual_year = current_year - years_back
                            except ValueError:
                                logger.warning(f"Could not parse year format: {year_col}")
                                continue
                        elif year_col == 'FY':
                            actual_year = datetime.now().year
                        elif year_col.isdigit():
                            actual_year = int(year_col)
                    
                    # Use fiscal year-end date from metadata if available for this year
                    if actual_year and str(actual_year) in [str(pd.Timestamp(date).year) for date in fiscal_year_dates['fy_dates']]:
                        # Find the matching fiscal year-end date
                        for fy_date in fiscal_year_dates['fy_dates']:
                            if pd.Timestamp(fy_date).year == actual_year:
                                fiscal_year_end_date = pd.Timestamp(fy_date)
                                break
                    
                    if not fiscal_year_end_date:
                        logger.warning(f"No fiscal year-end date found for year {actual_year}")
                        continue
                        
                    # Enhanced correlated stock price matching with fallback logic
                    price, actual_price_date, date_selection_log = self._find_best_price_match(
                        hist_prices, fiscal_year_end_date, actual_year
                    )
                    
                    if price is None:
                        logger.warning(f"No suitable price found for fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')} (year {actual_year})")
                        continue
                        
                    # Log the transparency information
                    logger.info(date_selection_log)
                    
                    # Extract equity from Excel balance sheet for this year column
                    bs_data = balance_data[year_col]
                    equity = None
                    
                    # Look for equity fields in the balance sheet data - use correct field names from Visa Excel structure
                    equity_fields = [
                        'Total Equity',  # This is the main one found at row 42
                        'Common Equity',  # Alternative at row 38
                        'Total Stockholder Equity',
                        'Stockholders Equity',
                        'Total Shareholders\' Equity',
                        'Shareholders\' Equity'
                    ]
                    
                    for field in equity_fields:
                        try:
                            # Use the financial calculator's extraction method directly on balance data
                            temp_balance_data = self.financial_calculator.financial_data.get('balance_fy', pd.DataFrame())
                            if not temp_balance_data.empty:
                                equity_values = self.financial_calculator._extract_metric_values(temp_balance_data, field)
                                if equity_values and len(equity_values) > 0:
                                    # Find the corresponding year column index
                                    if year_col in year_columns:
                                        year_idx = year_columns.index(year_col)
                                        if year_idx < len(equity_values):
                                            equity = equity_values[year_idx]
                                            if equity and equity != 0:
                                                logger.info(f"Found equity for {year_col} (fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')}) using field '{field}': {equity}")
                                                break
                        except Exception as e:
                            logger.debug(f"Could not extract {field} for {year_col}: {e}")
                            continue
                            
                    if equity is None or equity <= 0:
                        logger.warning(f"No valid equity found for year column {year_col} (fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')})")
                        continue
                        
                    # Get shares outstanding for this year using Excel data
                    # Try to extract shares outstanding from income statement for this year
                    income_data = self.financial_calculator.financial_data.get('income_fy', pd.DataFrame())
                    shares = None
                    
                    if not income_data.empty and year_col in income_data.columns:
                        try:
                            # Use the financial calculator's extraction method directly on income data
                            temp_income_data = self.financial_calculator.financial_data.get('income_fy', pd.DataFrame())
                            if not temp_income_data.empty:
                                shares_values = self.financial_calculator._extract_metric_values(temp_income_data, "Weighted Average Basic Shares Out")
                                if shares_values and len(shares_values) > 0:
                                    # Find the corresponding year column index
                                    income_year_columns = temp_income_data.columns.tolist()
                                    if year_col in income_year_columns:
                                        year_idx = income_year_columns.index(year_col)
                                        if year_idx < len(shares_values) and shares_values[year_idx] > 0:
                                            shares_raw = shares_values[year_idx]
                                            # Convert millions to actual count
                                            shares = shares_raw * 1_000_000
                                            logger.info(f"Found shares outstanding for {year_col} (fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')}): {shares:,.0f}")
                        except Exception as e:
                            logger.debug(f"Could not extract shares outstanding for {year_col}: {e}")
                    
                    # Fallback to current shares outstanding if historical not available
                    if not shares or shares <= 0:
                        shares = self.financial_calculator._extract_excel_shares_outstanding()
                        if shares:
                            logger.info(f"Using current shares outstanding for {year_col} (fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')}): {shares:,.0f}")
                    
                    if not shares or shares <= 0:
                        logger.warning(f"No valid shares outstanding found for year column {year_col} (fiscal year ending {fiscal_year_end_date.strftime('%Y-%m-%d')})")
                        continue
                        
                    # Calculate book value per share and P/B ratio
                    book_value_per_share = equity * 1_000_000 / shares  # Convert equity to actual currency units
                    pb_ratio = price / book_value_per_share if book_value_per_share > 0 else None
                    
                    if pb_ratio is not None:
                        historical_pb.append({
                            'date': actual_price_date.strftime('%Y-%m-%d'),
                            'fiscal_year_end': fiscal_year_end_date.strftime('%Y-%m-%d'),
                            'price': price,
                            'book_value_per_share': book_value_per_share,
                            'pb_ratio': pb_ratio,
                            'shares_outstanding': shares,
                            'equity': equity * 1_000_000,  # Store in actual currency units
                            'data_source': 'excel_annual_with_correlated_price_matching',
                            'year_column': year_col,
                            'actual_year': actual_year,
                            'price_date_used': actual_price_date.strftime('%Y-%m-%d'),
                            'fiscal_year_end_target': fiscal_year_end_date.strftime('%Y-%m-%d'),
                            'price_date_difference_days': (actual_price_date - fiscal_year_end_date).days,
                        })
                        
                        logger.info(f"P/B calculated for FY{actual_year}: Price=${price:.2f}, BVPS=${book_value_per_share:.2f}, P/B={pb_ratio:.2f}")
                
                except Exception as e:
                    logger.warning(f"Error processing year column {year_col} for historical P/B: {e}")
                    continue
                    
            logger.info(f"Successfully calculated {len(historical_pb)} historical P/B data points from Excel data")
            return historical_pb
            
        except Exception as e:
            logger.error(f"Error calculating historical P/B ratios from Excel: {e}")
            return []

    def _find_best_price_match(self, hist_prices: pd.DataFrame, fiscal_year_end_date: pd.Timestamp, 
                              actual_year: int) -> Tuple[Optional[float], Optional[pd.Timestamp], str]:
        """
        Find the best stock price match for fiscal year-end date with sophisticated fallback logic
        
        Args:
            hist_prices (pd.DataFrame): Historical price data
            fiscal_year_end_date (pd.Timestamp): Target fiscal year-end date
            actual_year (int): The fiscal year being processed
            
        Returns:
            tuple: (price, actual_date_used, transparency_log_message)
        """
        try:
            # Handle timezone issues by making fiscal_year_end_date timezone-aware if needed
            if hist_prices.index.tz is not None:
                if fiscal_year_end_date.tz is None:
                    fiscal_year_end_date = fiscal_year_end_date.tz_localize(hist_prices.index.tz)
            elif fiscal_year_end_date.tz is not None:
                fiscal_year_end_date = fiscal_year_end_date.tz_localize(None)
            
            # STEP 1: Try exact fiscal year-end date match
            if fiscal_year_end_date in hist_prices.index:
                price = hist_prices.loc[fiscal_year_end_date, 'Close']
                log_msg = (f"EXACT MATCH: Using price ${price:.2f} from exact fiscal year-end date "
                          f"{fiscal_year_end_date.strftime('%Y-%m-%d')} for FY{actual_year}")
                return price, fiscal_year_end_date, log_msg
            
            # STEP 2: Look for the previous closest trading date within ±30 days
            # Define search window (±30 days but prioritize dates before fiscal year-end)
            search_start = fiscal_year_end_date - pd.DateOffset(days=30)
            search_end = fiscal_year_end_date + pd.DateOffset(days=30)
            
            # Ensure we don't use future dates relative to fiscal year-end
            current_date = pd.Timestamp.now().normalize()
            if search_end > current_date:
                search_end = current_date
                
            # Get price data within the search window
            price_window = hist_prices[
                (hist_prices.index >= search_start) & 
                (hist_prices.index <= search_end)
            ]
            
            if price_window.empty:
                log_msg = (f"NO MATCH: No price data found within ±30 days of fiscal year-end "
                          f"{fiscal_year_end_date.strftime('%Y-%m-%d')} for FY{actual_year}")
                return None, None, log_msg
            
            # STEP 3: Find the best available date with preference for dates on or before fiscal year-end
            available_dates = price_window.index.tolist()
            
            # Split dates into before/on and after fiscal year-end
            dates_before_or_on = [date for date in available_dates if date <= fiscal_year_end_date]
            dates_after = [date for date in available_dates if date > fiscal_year_end_date]
            
            selected_date = None
            selection_reason = ""
            
            # Preference 1: Use the closest date before or on fiscal year-end
            if dates_before_or_on:
                selected_date = max(dates_before_or_on)  # Most recent date before or on fiscal year-end
                days_diff = (fiscal_year_end_date - selected_date).days
                selection_reason = f"BEFORE/ON FYE (-{days_diff} days)"
                
            # Preference 2: If no dates before, use the closest date after fiscal year-end
            elif dates_after:
                selected_date = min(dates_after)  # Earliest date after fiscal year-end
                days_diff = (selected_date - fiscal_year_end_date).days
                selection_reason = f"AFTER FYE (+{days_diff} days)"
            
            if selected_date is None:
                log_msg = (f"ALGORITHM ERROR: Could not select date from available data "
                          f"for fiscal year-end {fiscal_year_end_date.strftime('%Y-%m-%d')} FY{actual_year}")
                return None, None, log_msg
            
            # STEP 4: Ensure no future dates relative to balance sheet date
            if selected_date > fiscal_year_end_date + pd.DateOffset(days=30):
                log_msg = (f"FUTURE DATE REJECTED: Selected date {selected_date.strftime('%Y-%m-%d')} "
                          f"is too far after fiscal year-end {fiscal_year_end_date.strftime('%Y-%m-%d')} for FY{actual_year}")
                return None, None, log_msg
            
            price = price_window.loc[selected_date, 'Close']
            
            # STEP 5: Generate detailed transparency log
            log_msg = (f"FALLBACK MATCH ({selection_reason}): Using price ${price:.2f} from "
                      f"{selected_date.strftime('%Y-%m-%d')} for fiscal year-end "
                      f"{fiscal_year_end_date.strftime('%Y-%m-%d')} FY{actual_year} "
                      f"[{len(available_dates)} dates available in ±30 day window]")
            
            return price, selected_date, log_msg
            
        except Exception as e:
            error_msg = (f"ERROR in price matching for fiscal year-end "
                        f"{fiscal_year_end_date.strftime('%Y-%m-%d')} FY{actual_year}: {e}")
            logger.error(error_msg)
            return None, None, error_msg

    def _load_fiscal_year_dates(self) -> Optional[Dict]:
        """
        Load fiscal year-end dates from dates_metadata.json file
        
        Returns:
            dict or None: Dictionary containing fiscal year dates and metadata
        """
        try:
            # Import required modules 
            import json
            from pathlib import Path
            
            # Look for dates_metadata.json file
            metadata_path = Path("dates_metadata.json")
            if not metadata_path.exists():
                logger.warning("dates_metadata.json file not found - cannot extract fiscal year-end dates")
                return None
                
            # Load the metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Validate required fields
            if 'fy_dates' not in metadata or not metadata['fy_dates']:
                logger.warning("No fiscal year dates found in metadata file")
                return None
                
            logger.info(f"Loaded {len(metadata['fy_dates'])} fiscal year-end dates from metadata")
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading fiscal year-end dates from metadata: {e}")
            return None

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
        Analyze comprehensive trend in P/B values with enhanced volatility and direction analysis

        Args:
            pb_values (list): List of P/B values over time

        Returns:
            dict: Enhanced trend analysis with comprehensive statistics
        """
        if len(pb_values) < 3:
            return {'trend': 'insufficient_data', 'error': 'Need at least 3 data points for trend analysis'}

        pb_array = np.array(pb_values)
        
        # Linear trend analysis (primary)
        x = np.arange(len(pb_values))
        coeffs = np.polyfit(x, pb_values, 1)
        slope = coeffs[0]
        r_squared = np.corrcoef(x, pb_values)[0, 1] ** 2
        
        # Enhanced trend direction classification
        slope_threshold = 0.01  # 1% change per period
        if abs(slope) < slope_threshold:
            trend_direction = 'stable'
            trend_strength = 'weak'
        else:
            trend_strength = 'strong' if abs(slope) > slope_threshold * 3 else 'moderate'
            if slope > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'

        # Comprehensive volatility analysis
        mean_pb = np.mean(pb_values)
        std_pb = np.std(pb_values)
        
        # Multiple volatility measures
        coefficient_of_variation = (std_pb / mean_pb * 100) if mean_pb > 0 else 0
        max_drawdown = self._calculate_max_drawdown(pb_values)
        volatility_classification = self._classify_volatility(coefficient_of_variation)
        
        # Trend consistency analysis
        rolling_trends = []
        window_size = max(3, len(pb_values) // 3)  # Use 1/3 of data as window
        for i in range(len(pb_values) - window_size + 1):
            window = pb_values[i:i + window_size]
            window_x = np.arange(len(window))
            window_slope = np.polyfit(window_x, window, 1)[0]
            rolling_trends.append('up' if window_slope > slope_threshold else 'down' if window_slope < -slope_threshold else 'flat')
        
        trend_consistency = len(set(rolling_trends)) == 1 if rolling_trends else False
        
        # Recent vs historical comparison (enhanced)
        recent_period = max(1, len(pb_values) // 4)  # Last quarter of data
        recent_mean = np.mean(pb_values[-recent_period:]) if recent_period < len(pb_values) else pb_values[-1]
        historical_mean = np.mean(pb_values[:-recent_period]) if recent_period < len(pb_values) else np.mean(pb_values[:-1])
        
        recent_vs_historical = (recent_mean / historical_mean - 1) if historical_mean > 0 else 0
        
        # Momentum analysis
        momentum = (pb_values[-1] - pb_values[0]) / pb_values[0] if pb_values[0] > 0 else 0
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'trend_consistency': trend_consistency,
            'linear_slope': float(slope),
            'r_squared': float(r_squared),
            'coefficient_of_variation': float(coefficient_of_variation),
            'volatility_classification': volatility_classification,
            'max_drawdown': float(max_drawdown),
            'recent_vs_historical': float(recent_vs_historical),
            'momentum': float(momentum),
            'trend_periods_analyzed': len(rolling_trends),
            'dominant_rolling_trend': max(set(rolling_trends), key=rolling_trends.count) if rolling_trends else 'unknown',
            # Legacy compatibility
            'trend': trend_direction,
            'slope': float(slope),
            'volatility': float(coefficient_of_variation / 100),  # Convert back to decimal for compatibility
        }

    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """
        Calculate maximum drawdown from peak in the P/B values
        
        Args:
            values (list): List of P/B values
            
        Returns:
            float: Maximum drawdown as percentage
        """
        if len(values) < 2:
            return 0.0
            
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown * 100  # Return as percentage

    def _classify_volatility(self, coefficient_of_variation: float) -> str:
        """
        Classify volatility level based on coefficient of variation
        
        Args:
            coefficient_of_variation (float): Coefficient of variation as percentage
            
        Returns:
            str: Volatility classification
        """
        if coefficient_of_variation < 10:
            return 'low'
        elif coefficient_of_variation < 25:
            return 'moderate'
        elif coefficient_of_variation < 40:
            return 'high'
        else:
            return 'very_high'

    def _interpret_historical_pb(self, stats: Dict, trend_analysis: Dict) -> str:
        """
        Generate comprehensive interpretation of historical P/B analysis

        Args:
            stats (dict): Enhanced statistical summary
            trend_analysis (dict): Comprehensive trend analysis

        Returns:
            str: Detailed interpretation text
        """
        # Extract key metrics
        percentile = stats.get('current_percentile', 50)
        volatility = stats.get('volatility_coefficient', 0)
        data_points = stats.get('data_points_count', 0)
        time_range = stats.get('time_range_years', 5)
        
        # Enhanced trend analysis metrics
        trend_direction = trend_analysis.get('trend_direction', 'stable')
        trend_strength = trend_analysis.get('trend_strength', 'weak')
        volatility_class = trend_analysis.get('volatility_classification', 'moderate')
        max_drawdown = trend_analysis.get('max_drawdown', 0)
        momentum = trend_analysis.get('momentum', 0)
        
        # Build comprehensive interpretation
        interpretation = f"Historical P/B Analysis ({time_range} years, {data_points} data points):\n"
        
        # Percentile position analysis
        if percentile < 10:
            interpretation += f"• Current P/B at {percentile:.0f}th percentile - extremely low historically, potential deep value or distress signal.\n"
        elif percentile < 25:
            interpretation += f"• Current P/B at {percentile:.0f}th percentile - trading near historical lows, potentially attractive valuation.\n"
        elif percentile > 90:
            interpretation += f"• Current P/B at {percentile:.0f}th percentile - extremely high historically, significant premium valuation.\n"
        elif percentile > 75:
            interpretation += f"• Current P/B at {percentile:.0f}th percentile - trading near historical highs, elevated valuation.\n"
        else:
            interpretation += f"• Current P/B at {percentile:.0f}th percentile - trading within normal historical range.\n"
        
        # Trend analysis interpretation
        if trend_direction == 'increasing':
            interpretation += f"• P/B trend: {trend_strength} upward trend"
            if momentum > 0.2:
                interpretation += " with strong positive momentum"
            interpretation += ".\n"
        elif trend_direction == 'decreasing':
            interpretation += f"• P/B trend: {trend_strength} downward trend"
            if momentum < -0.2:
                interpretation += " with strong negative momentum"
            interpretation += ".\n"
        else:
            interpretation += f"• P/B trend: relatively stable with {trend_strength} variations.\n"
        
        # Volatility analysis
        interpretation += f"• Volatility: {volatility_class} ({volatility:.1f}% coefficient of variation)"
        if max_drawdown > 30:
            interpretation += f", with significant maximum drawdown of {max_drawdown:.1f}%"
        interpretation += ".\n"
        
        # Statistical insights
        pb_range = stats.get('range_span', 0)
        iqr = stats.get('interquartile_range', 0)
        if pb_range > 0 and iqr > 0:
            interpretation += f"• P/B range: {pb_range:.2f} total span, with middle 50% within {iqr:.2f} range.\n"
        
        # Investment implications
        interpretation += "\nInvestment Implications:\n"
        if percentile < 25 and trend_direction == 'increasing':
            interpretation += "• Potential value opportunity - low historical valuation with improving trend.\n"
        elif percentile > 75 and trend_direction == 'decreasing':
            interpretation += "• Caution warranted - high historical valuation with declining trend.\n"
        elif volatility_class in ['high', 'very_high']:
            interpretation += "• High volatility suggests uncertain valuation environment requiring careful analysis.\n"
        elif volatility_class == 'low' and trend_direction == 'stable':
            interpretation += "• Stable valuation pattern indicates predictable P/B behavior.\n"
        
        return interpretation.strip()

    def _calculate_pb_valuation(
        self, book_value_per_share: float, industry_key: str
    ) -> Dict[str, Any]:
        """
        Calculate valuation ranges based on P/B analysis (static benchmarks removed)

        Args:
            book_value_per_share (float): Current book value per share
            industry_key (str): Industry category

        Returns:
            dict: Valuation analysis (historical-only without static benchmarks)
        """
        # Static industry benchmarks removed - focus on historical analysis
        # Calculate historical implied prices using P/B statistics
        historical_implied_prices = self._calculate_historical_implied_prices(
            book_value_per_share, industry_key
        )
        
        return {
            'book_value_per_share': book_value_per_share,
            'industry_key': industry_key,
            'historical_implied_prices': historical_implied_prices,
            'error': 'static_benchmarks_removed',
            'message': 'Industry-based valuation requires dynamic data service',
            'methodology': 'Static industry benchmarks eliminated - use historical P/B analysis instead',
        }

    def _calculate_historical_implied_prices(
        self, book_value_per_share: float, industry_key: str
    ) -> Dict[str, Any]:
        """
        Calculate current implied stock prices using historical P/B statistics
        
        Uses Current Book Value per Share × Historical P/B Statistics (Min, Mean, Median, Max)
        to generate implied price scenarios with upside/downside percentages vs current stock price.
        
        Args:
            book_value_per_share (float): Current book value per share
            industry_key (str): Industry category key
            
        Returns:
            dict: Historical implied price calculations
        """
        try:
            if not book_value_per_share or book_value_per_share <= 0:
                return {
                    'error': 'invalid_book_value',
                    'message': 'Valid book value per share required for historical implied price calculation'
                }
            
            # Get ticker symbol for historical analysis
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
            if not ticker_symbol:
                return {
                    'error': 'ticker_unavailable',
                    'message': 'Ticker symbol required for historical P/B analysis'
                }
            
            # Get historical P/B analysis with comprehensive statistics
            historical_analysis = self._analyze_historical_pb(ticker_symbol, years=5)
            
            if 'error' in historical_analysis:
                return {
                    'error': 'historical_data_unavailable',
                    'message': f'Could not retrieve historical P/B data: {historical_analysis.get("error_message", "Unknown error")}'
                }
            
            statistics = historical_analysis.get('statistics', {})
            if not statistics:
                return {
                    'error': 'no_statistics',
                    'message': 'No historical P/B statistics available for implied price calculation'
                }
            
            # Get current market price for comparison
            market_data = self._get_market_data(ticker_symbol)
            current_price = market_data.get('current_price', 0) if market_data else 0
            
            if not current_price or current_price <= 0:
                return {
                    'error': 'current_price_unavailable',
                    'message': 'Current market price required for upside/downside calculation'
                }
            
            # Calculate implied prices using historical P/B statistics
            implied_scenarios = {}
            pb_stats = {
                'min': statistics.get('min'),
                'mean': statistics.get('mean'), 
                'median': statistics.get('median'),
                'max': statistics.get('max')
            }
            
            # Additional percentile-based scenarios
            pb_stats['25th_percentile'] = statistics.get('percentile_25')
            pb_stats['75th_percentile'] = statistics.get('percentile_75')
            
            for scenario_name, pb_value in pb_stats.items():
                if pb_value and pb_value > 0:
                    implied_price = book_value_per_share * pb_value
                    upside_downside = ((implied_price / current_price) - 1) * 100
                    
                    # Format scenario description
                    scenario_display_name = {
                        'min': 'Historical Minimum',
                        'mean': 'Historical Mean', 
                        'median': 'Historical Median',
                        'max': 'Historical Maximum',
                        '25th_percentile': 'Historical 25th Percentile',
                        '75th_percentile': 'Historical 75th Percentile'
                    }.get(scenario_name, scenario_name.replace('_', ' ').title())
                    
                    # Create formatted description as specified in requirements
                    upside_downside_str = f"{'+' if upside_downside >= 0 else ''}{upside_downside:.1f}%"
                    formatted_description = f"At {scenario_display_name} P/B ({pb_value:.1f}x): ${implied_price:.2f} ({upside_downside_str} vs current)"
                    
                    implied_scenarios[scenario_name] = {
                        'pb_ratio': pb_value,
                        'implied_price': implied_price,
                        'current_price': current_price,
                        'upside_downside_pct': upside_downside,
                        'formatted_description': formatted_description,
                        'scenario_name': scenario_display_name
                    }
            
            if not implied_scenarios:
                return {
                    'error': 'no_valid_scenarios',
                    'message': 'No valid P/B statistics available for implied price calculation'
                }
            
            # Generate methodology explanation
            methodology_text = self._generate_implied_price_methodology(
                book_value_per_share, statistics, len(historical_analysis.get('historical_data', []))
            )
            
            # Calculate summary statistics
            implied_prices = [scenario['implied_price'] for scenario in implied_scenarios.values()]
            upside_downsides = [scenario['upside_downside_pct'] for scenario in implied_scenarios.values()]
            
            summary = {
                'book_value_per_share': book_value_per_share,
                'current_price': current_price,
                'implied_price_range': {
                    'min': min(implied_prices),
                    'max': max(implied_prices),
                    'span': max(implied_prices) - min(implied_prices)
                },
                'upside_downside_range': {
                    'min': min(upside_downsides),
                    'max': max(upside_downsides),
                    'span': max(upside_downsides) - min(upside_downsides)
                },
                'scenario_count': len(implied_scenarios)
            }
            
            return {
                'ticker_symbol': ticker_symbol,
                'analysis_date': datetime.now().isoformat(),
                'book_value_per_share': book_value_per_share,
                'current_price': current_price,
                'historical_period': historical_analysis.get('period', '5 years'),
                'data_points': historical_analysis.get('data_points', 0),
                'implied_scenarios': implied_scenarios,
                'summary': summary,
                'methodology': methodology_text,
                'historical_statistics': statistics
            }
            
        except Exception as e:
            logger.error(f"Error calculating historical implied prices: {e}")
            return {
                'error': 'calculation_failed',
                'error_message': str(e)
            }
    
    def _generate_implied_price_methodology(
        self, book_value_per_share: float, statistics: Dict, data_points: int
    ) -> str:
        """
        Generate explanatory methodology text for historical implied price calculation
        
        Args:
            book_value_per_share (float): Current book value per share
            statistics (dict): Historical P/B statistics
            data_points (int): Number of historical data points used
            
        Returns:
            str: Methodology explanation text
        """
        methodology = f"""
Historical Implied Price Methodology:

This analysis calculates potential stock price scenarios based on historical Price-to-Book (P/B) ratio patterns. 

Calculation Method:
• Current Book Value per Share: ${book_value_per_share:.2f}
• Historical P/B Analysis Period: {statistics.get('time_range_years', 5)} years ({data_points} data points)
• Implied Price Formula: Book Value per Share × Historical P/B Ratio

Statistical Foundation:
• Historical P/B Range: {statistics.get('min', 0):.2f}x to {statistics.get('max', 0):.2f}x
• Mean P/B: {statistics.get('mean', 0):.2f}x | Median P/B: {statistics.get('median', 0):.2f}x
• P/B Volatility: {statistics.get('volatility_coefficient', 0):.1f}% (coefficient of variation)

Investment Interpretation:
• Scenarios below current price suggest potential undervaluation
• Scenarios above current price indicate potential upside based on historical norms
• Wide ranges suggest higher valuation uncertainty
• Consider fundamentals, market conditions, and business quality alongside P/B analysis

Note: This analysis assumes historical P/B patterns provide insight into potential future valuation ranges. 
Past performance does not guarantee future results. Book value may not reflect fair value of assets.
""".strip()
        
        return methodology

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

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the industry data cache status
        
        Returns:
            dict: Cache information including file count, TTL, and status
        """
        if hasattr(self, 'industry_service') and self.industry_service:
            try:
                return self.industry_service.get_cache_info()
            except Exception as e:
                logger.error(f"Error getting cache info: {e}")
                return {'error': str(e)}
        else:
            return {
                'service_available': False,
                'message': 'IndustryDataService not available - using static benchmarks'
            }
