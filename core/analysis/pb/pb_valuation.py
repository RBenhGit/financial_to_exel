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
>>> from core.analysis.pb.pb_valuation import PBValuator
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
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
- **Primary**: VarInputData centralized variable system for market and financial data
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
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from enum import Enum

# Import IndustryDataService for real-time industry benchmarking with caching
try:
    from core.data_sources.industry_data_service import IndustryDataService
except ImportError:
    IndustryDataService = None

# Import var_input_data system for centralized variable access
try:
    from core.data_processing.var_input_data import get_var_input_data
except ImportError:
    get_var_input_data = None

# Import performance monitoring utilities
try:
    from utils.performance_monitor import performance_timer, ProgressTracker
except ImportError:
    # Fallback if performance monitor isn't available
    def performance_timer(operation_name: str, **kwargs):
        def decorator(func):
            return func
        return decorator
    ProgressTracker = None

logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """
    Enum for graduated data quality levels in P/B historical analysis
    """
    HIGH = "high"          # Excel equity + Excel shares + exact price date
    GOOD = "good"          # Excel equity + current shares + close price date  
    ACCEPTABLE = "acceptable"  # Estimated values with clear attribution
    LOW = "low"            # Limited data with high uncertainty
    UNUSABLE = "unusable"  # Insufficient data for meaningful analysis
    
    def __str__(self):
        return self.value.title()
    
    @property
    def score(self) -> int:
        """Numeric score for quality level (higher is better)"""
        scores = {
            DataQualityLevel.HIGH: 100,
            DataQualityLevel.GOOD: 80, 
            DataQualityLevel.ACCEPTABLE: 60,
            DataQualityLevel.LOW: 40,
            DataQualityLevel.UNUSABLE: 0
        }
        return scores[self]
    
    @property
    def description(self) -> str:
        """Description of data quality level"""
        descriptions = {
            DataQualityLevel.HIGH: "Excel equity + Excel shares + exact price date",
            DataQualityLevel.GOOD: "Excel equity + current shares + close price date",
            DataQualityLevel.ACCEPTABLE: "Estimated values with clear attribution", 
            DataQualityLevel.LOW: "Limited data with high uncertainty",
            DataQualityLevel.UNUSABLE: "Insufficient data for meaningful analysis"
        }
        return descriptions[self]


def assess_pb_data_quality(
    equity_source: str,
    shares_source: str, 
    price_match_quality: str,
    equity_value: Optional[float] = None,
    shares_value: Optional[float] = None,
    price_value: Optional[float] = None
) -> Tuple[DataQualityLevel, Dict[str, Any]]:
    """
    Assess the data quality level for a P/B calculation data point
    
    Args:
        equity_source: Source of equity data ('excel', 'api', 'estimated', 'unavailable')
        shares_source: Source of shares data ('excel_historical', 'excel_current', 'api', 'estimated', 'unavailable') 
        price_match_quality: Quality of price date match ('exact', 'close', 'approximate', 'poor')
        equity_value: Actual equity value (for validation)
        shares_value: Actual shares value (for validation)
        price_value: Actual price value (for validation)
    
    Returns:
        Tuple of (DataQualityLevel, detailed_assessment_dict)
    """
    assessment = {
        'equity_source': equity_source,
        'shares_source': shares_source,
        'price_match_quality': price_match_quality,
        'data_completeness': {},
        'quality_factors': []
    }
    
    # Check data completeness
    assessment['data_completeness'] = {
        'has_equity': equity_value is not None and equity_value > 0,
        'has_shares': shares_value is not None and shares_value > 0, 
        'has_price': price_value is not None and price_value > 0
    }
    
    # If any core data is missing, mark as unusable
    if not all(assessment['data_completeness'].values()):
        assessment['quality_factors'].append('missing_core_data')
        return DataQualityLevel.UNUSABLE, assessment
    
    # Determine quality level based on data sources and accuracy
    if (equity_source == 'excel' and 
        shares_source == 'excel_historical' and 
        price_match_quality == 'exact'):
        assessment['quality_factors'].extend(['excel_equity', 'historical_shares', 'exact_price'])
        return DataQualityLevel.HIGH, assessment
        
    elif (equity_source == 'excel' and 
          shares_source in ['excel_current', 'excel_historical'] and 
          price_match_quality in ['exact', 'close']):
        assessment['quality_factors'].extend(['excel_equity', 'excel_shares', 'good_price_match'])
        return DataQualityLevel.GOOD, assessment
        
    elif (equity_source == 'excel' and 
          shares_source in ['excel_current', 'api'] and 
          price_match_quality in ['close', 'approximate']):
        assessment['quality_factors'].extend(['excel_equity', 'reasonable_shares', 'acceptable_price'])
        return DataQualityLevel.ACCEPTABLE, assessment
        
    elif (equity_source in ['excel', 'api'] and 
          shares_source in ['excel_current', 'api', 'estimated'] and 
          price_match_quality in ['approximate', 'close']):
        assessment['quality_factors'].extend(['some_reliable_data', 'estimated_components'])
        return DataQualityLevel.LOW, assessment
        
    else:
        assessment['quality_factors'].append('poor_data_quality')
        return DataQualityLevel.UNUSABLE, assessment


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

        # Initialize var_input_data system if available
        if get_var_input_data:
            try:
                self.var_input_data = get_var_input_data()
                logger.info("PB valuator initialized with var_input_data centralized variable system")
            except Exception as e:
                logger.warning(f"Failed to initialize var_input_data: {e}")
                self.var_input_data = None
        else:
            self.var_input_data = None
            logger.debug("var_input_data not available, using traditional data access")

        # Initialize IndustryDataService for real-time industry benchmarking with caching
        if IndustryDataService:
            try:
                self.industry_service = IndustryDataService()
                logger.info("PB valuator initialized with IndustryDataService for cached industry benchmarking")
            except Exception as e:
                logger.warning(f"Failed to initialize IndustryDataService: {e}")
                self.industry_service = None
        else:
            self.industry_service = None
            logger.debug("IndustryDataService not available, using static benchmarks")

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

    @performance_timer("pb_full_analysis", include_args=True, save_metrics=True)
    def calculate_pb_analysis(self, ticker_symbol: str = None, progress_callback=None) -> Dict[str, Any]:
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
        progress_callback : callable, optional
            Callback function for progress updates. Should accept (current, total, message) parameters.

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
            # Initialize progress tracking with 6 main steps
            if ProgressTracker and progress_callback:
                progress_tracker = ProgressTracker(6, "P/B Analysis")
                progress_tracker.add_callback(progress_callback)
            else:
                progress_tracker = None
            
            # Use ticker from financial calculator if not provided
            if not ticker_symbol:
                ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)

            if not ticker_symbol:
                logger.error("No ticker symbol available for P/B analysis")
                return {
                    'error': 'ticker_unavailable',
                    'error_message': 'Ticker symbol is required for P/B analysis',
                }

            # Step 1: Get current market data
            if progress_tracker:
                progress_tracker.update(1, "Fetching market data...")
            
            market_data = self._get_market_data(ticker_symbol)
            if not market_data or 'current_price' not in market_data:
                return {
                    'error': 'market_data_unavailable',
                    'error_message': 'Unable to fetch current market data',
                }

            # Step 2: Calculate book value per share
            if progress_tracker:
                progress_tracker.update(1, "Calculating book value per share...")
            
            book_value_per_share = self._calculate_book_value_per_share()
            if book_value_per_share is None:
                return {
                    'error': 'book_value_unavailable',
                    'error_message': 'Unable to calculate book value per share',
                }

            # Calculate current P/B ratio
            current_price = market_data['current_price']
            pb_ratio = current_price / book_value_per_share if book_value_per_share > 0 else None

            # Store P/B ratio in var_input_data if available
            if self.var_input_data and pb_ratio is not None:
                try:
                    ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
                    if ticker_symbol:
                        self.var_input_data.set_variable(
                            ticker_symbol,
                            "pb_ratio",
                            pb_ratio,
                            source="calculated",
                            metadata={
                                "calculation_method": "current_price / book_value_per_share",
                                "dependencies": ["current_price", "book_value_per_share"],
                                "calculated_by": "pb_valuation_module"
                            }
                        )
                except Exception as e:
                    logger.debug(f"Failed to store P/B ratio in var_input_data: {e}")

            # Calculate market cap correctly (price × shares) instead of relying on API value
            # Some APIs provide market cap in thousands or millions, causing display issues
            shares_outstanding = market_data.get('shares_outstanding', 0)
            calculated_market_cap = (
                current_price * shares_outstanding
                if (current_price and shares_outstanding)
                else market_data.get('market_cap', 0)
            )

            # Step 3: Get industry information and comparison
            if progress_tracker:
                progress_tracker.update(1, "Analyzing industry benchmarks...")
            
            industry_info = self._get_industry_info(ticker_symbol)
            industry_comparison = self._compare_to_industry(
                pb_ratio, industry_info.get('industry_key', 'Default'), ticker_symbol
            )

            # Step 4: Historical P/B analysis
            if progress_tracker:
                progress_tracker.update(1, "Analyzing historical P/B trends...")
            
            historical_analysis = self._analyze_historical_pb(ticker_symbol, years=5)

            # Step 5: P/B based valuation ranges
            if progress_tracker:
                progress_tracker.update(1, "Calculating valuation ranges...")
                
            valuation_analysis = self._calculate_pb_valuation(
                book_value_per_share, industry_info.get('industry_key', 'Default')
            )

            # Step 6: Risk assessment
            if progress_tracker:
                progress_tracker.update(1, "Performing risk assessment...")
                
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

            # Complete progress tracking
            if progress_tracker:
                progress_tracker.complete(f"P/B analysis completed for {ticker_symbol}")
            
            logger.info(
                f"P/B Analysis completed for {ticker_symbol}: P/B = {pb_ratio:.2f}"
                if pb_ratio
                else f"P/B Analysis completed for {ticker_symbol}: Book value calculation failed"
            )
            return result

        except Exception as e:
            logger.error(f"Error in P/B analysis: {e}")
            return {'error': 'calculation_failed', 'error_message': str(e)}

    @performance_timer("pb_book_value_calculation")
    def _calculate_book_value_per_share(self) -> Optional[float]:
        """
        Calculate book value per share from multiple data sources with enhanced fallback

        Returns:
            float or None: Book value per share
        """
        try:
            book_value_per_share = None
            data_source_used = None
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)

            # Try var_input_data first if available
            if self.var_input_data and ticker_symbol:
                try:
                    book_value_per_share = self._calculate_bvps_from_var_input_data(ticker_symbol)
                    if book_value_per_share:
                        data_source_used = "var_input_data"
                        logger.info(
                            f"Successfully calculated BVPS from var_input_data: ${book_value_per_share:.2f}"
                        )
                except Exception as e:
                    logger.warning(f"var_input_data BVPS calculation failed: {e}")

            # Try enhanced data manager if var_input_data failed
            if not book_value_per_share and self.enhanced_data_manager:
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

    def _calculate_bvps_from_var_input_data(self, ticker_symbol: str) -> Optional[float]:
        """
        Calculate book value per share using var_input_data system

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            float or None: Book value per share from var_input_data
        """
        try:
            # Try to get book_value_per_share directly if it exists as calculated variable
            book_value_per_share = self.var_input_data.get_variable(
                ticker_symbol, "book_value_per_share"
            )
            if book_value_per_share and book_value_per_share > 0:
                logger.info(f"Retrieved BVPS directly from var_input_data: ${book_value_per_share:.2f}")
                return book_value_per_share

            # Calculate from components if direct BVPS not available
            book_value = self.var_input_data.get_variable(ticker_symbol, "book_value")
            shares_outstanding = self.var_input_data.get_variable(ticker_symbol, "shares_outstanding")

            if book_value and shares_outstanding and shares_outstanding > 0:
                # Calculate BVPS and store it as a calculated variable
                calculated_bvps = book_value / shares_outstanding
                
                # Store the calculated value back into var_input_data for future use
                self.var_input_data.set_variable(
                    ticker_symbol,
                    "book_value_per_share", 
                    calculated_bvps,
                    source="calculated",
                    metadata={
                        "calculation_method": "book_value / shares_outstanding",
                        "dependencies": ["book_value", "shares_outstanding"],
                        "calculated_by": "pb_valuation_module"
                    }
                )
                
                logger.info(f"Calculated BVPS from var_input_data: Book Value=${book_value:,.0f}, Shares={shares_outstanding/1000000:.1f}M, BVPS=${calculated_bvps:.2f}")
                return calculated_bvps

            # Alternative: try shareholders_equity
            shareholders_equity = self.var_input_data.get_variable(ticker_symbol, "shareholders_equity")
            if shareholders_equity and shares_outstanding and shares_outstanding > 0:
                calculated_bvps = shareholders_equity / shares_outstanding
                
                # Store the calculated value
                self.var_input_data.set_variable(
                    ticker_symbol,
                    "book_value_per_share",
                    calculated_bvps,
                    source="calculated",
                    metadata={
                        "calculation_method": "shareholders_equity / shares_outstanding",
                        "dependencies": ["shareholders_equity", "shares_outstanding"],
                        "calculated_by": "pb_valuation_module"
                    }
                )
                
                logger.info(f"Calculated BVPS from shareholders equity: Equity=${shareholders_equity:,.0f}, Shares={shares_outstanding/1000000:.1f}M, BVPS=${calculated_bvps:.2f}")
                return calculated_bvps

            logger.info(f"Insufficient data in var_input_data for BVPS calculation: book_value={book_value}, shareholders_equity={shareholders_equity}, shares_outstanding={shares_outstanding}")
            return None

        except Exception as e:
            logger.warning(f"Error calculating BVPS from var_input_data: {e}")
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
            'shareholders\' equity',
            'stockholders\' equity',
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

        # Track all potential matches for debugging
        potential_matches = []
        
        for year_data in balance_sheet_data.values():
            if isinstance(year_data, dict):
                for key, value in year_data.items():
                    if isinstance(key, str) and isinstance(value, (int, float)):
                        key_lower = key.lower().strip()
                        
                        # Remove common punctuation and extra spaces for better matching
                        key_normalized = key_lower.replace('(', '').replace(')', '').replace(',', '').replace('  ', ' ').strip()

                        # First pass: exact matching
                        for equity_keyword in equity_keywords:
                            if equity_keyword in key_normalized:
                                logger.info(f"Found shareholders' equity (exact match): {key} = ${value:.1f}M")
                                logger.debug(f"Matched keyword: '{equity_keyword}' in field: '{key_normalized}'")
                                return abs(value)  # Ensure positive value
                        
                        # Second pass: fuzzy matching for partial matches
                        # Check if key contains equity-related terms but didn't match exactly
                        equity_indicators = ['equity', 'book', 'worth', 'capital']
                        if any(indicator in key_normalized for indicator in equity_indicators):
                            potential_matches.append((key, value, key_normalized))
                            logger.debug(f"Potential equity field detected: {key} = ${value:.1f}M")

        # If no exact match found, try fuzzy matching on potential matches
        if potential_matches:
            # Filter out obvious non-equity fields
            filtered_matches = []
            exclude_patterns = [
                'liability', 'liabilities', 'debt', 'payable', 'receivable', 
                'asset', 'assets', 'cash', 'inventory', 'revenue', 'income',
                'expense', 'cost', 'depreciation', 'amortization', 'goodwill'
            ]
            
            for key, value, key_normalized in potential_matches:
                if not any(exclude in key_normalized for exclude in exclude_patterns):
                    filtered_matches.append((key, value, key_normalized))
                    
            if filtered_matches:
                # Use the first filtered match as a fallback
                key, value, key_normalized = filtered_matches[0]
                logger.warning(f"Using fuzzy match for shareholders' equity: {key} = ${value:.1f}M")
                logger.debug(f"Selected from {len(filtered_matches)} potential matches")
                return abs(value)

        # Log all available fields for debugging
        all_fields = []
        for year_data in balance_sheet_data.values():
            if isinstance(year_data, dict):
                for key in year_data.keys():
                    if isinstance(key, str):
                        all_fields.append(key)
        
        logger.warning("Could not find shareholders' equity in balance sheet data")
        logger.debug(f"Available fields: {', '.join(set(all_fields))}")
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
            market_data = {}

            # Try var_input_data first if available
            if self.var_input_data:
                try:
                    current_price = self.var_input_data.get_variable(ticker_symbol, "current_price")
                    market_cap = self.var_input_data.get_variable(ticker_symbol, "market_cap")
                    shares_outstanding = self.var_input_data.get_variable(ticker_symbol, "shares_outstanding")
                    
                    if current_price:
                        market_data['current_price'] = current_price
                    if market_cap:
                        market_data['market_cap'] = market_cap
                    if shares_outstanding:
                        market_data['shares_outstanding'] = shares_outstanding

                    # If we got the essential data, use var_input_data
                    if current_price and (market_cap or shares_outstanding):
                        # Calculate market_cap if not available but we have price and shares
                        if not market_cap and current_price and shares_outstanding:
                            calculated_market_cap = current_price * shares_outstanding
                            market_data['market_cap'] = calculated_market_cap
                            
                            # Store the calculated market cap
                            self.var_input_data.set_variable(
                                ticker_symbol,
                                "market_cap",
                                calculated_market_cap,
                                source="calculated",
                                metadata={
                                    "calculation_method": "current_price * shares_outstanding",
                                    "dependencies": ["current_price", "shares_outstanding"],
                                    "calculated_by": "pb_valuation_module"
                                }
                            )

                        logger.debug(f"Using market data from var_input_data: price=${current_price:.2f}, market_cap=${market_data.get('market_cap', 0):,.0f}")
                        return market_data
                    else:
                        logger.debug("Insufficient market data in var_input_data, trying other sources")
                
                except Exception as e:
                    logger.warning(f"Error retrieving market data from var_input_data: {e}")

            # Use financial calculator's enhanced market data fetching if available
            if hasattr(self.financial_calculator, 'fetch_market_data'):
                market_data = self.financial_calculator.fetch_market_data(ticker_symbol)
                if market_data:
                    logger.debug("Using enhanced market data from financial calculator")
                    
                    # Store retrieved data in var_input_data for future use
                    if self.var_input_data:
                        try:
                            for key, value in market_data.items():
                                if key in ['current_price', 'market_cap', 'shares_outstanding'] and value:
                                    self.var_input_data.set_variable(ticker_symbol, key, value, source="api")
                        except Exception as e:
                            logger.debug(f"Failed to store market data in var_input_data: {e}")
                    
                    return market_data

            # Try enhanced data manager directly if financial calculator doesn't have it
            if self.enhanced_data_manager:
                try:
                    market_data = self.enhanced_data_manager.fetch_market_data(ticker_symbol)
                    if market_data:
                        logger.debug("Using market data from enhanced data manager")
                        
                        # Store in var_input_data
                        if self.var_input_data:
                            try:
                                for key, value in market_data.items():
                                    if key in ['current_price', 'market_cap', 'shares_outstanding'] and value:
                                        self.var_input_data.set_variable(ticker_symbol, key, value, source="api")
                            except Exception as e:
                                logger.debug(f"Failed to store enhanced market data in var_input_data: {e}")
                        
                        return market_data
                except Exception as e:
                    logger.warning(f"Enhanced data manager market data fetch failed: {e}")

            # No fallback - data should be available through VarInputData
            logger.warning(f"Market data not available through VarInputData for {ticker_symbol}")
            logger.info("Ensure data is loaded via adapters (Excel, API) before analysis")

            # Return None to indicate data is missing rather than silently using fallback
            return None

        except Exception as e:
            logger.error(f"Error fetching market data for {ticker_symbol}: {e}")
            return None

    def _get_industry_info(self, ticker_symbol: str) -> Dict[str, str]:
        """
        Get industry information for the ticker using VarInputData

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            dict: Industry information
        """
        try:
            # Try to get sector and industry from VarInputData
            if self.var_input_data:
                sector = self.var_input_data.get_variable(ticker_symbol, 'sector')
                industry = self.var_input_data.get_variable(ticker_symbol, 'industry')

                if sector:
                    industry_key = self._map_to_benchmark_industry(sector)

                    logger.info(
                        f"Industry detection for {ticker_symbol}: sector='{sector}', mapped to '{industry_key}'"
                    )

                    return {
                        'industry': industry or 'Unknown',
                        'sector': sector,
                        'industry_key': industry_key,
                    }

            # If data not available, warn and return defaults
            logger.warning(f"Sector/industry information not available for {ticker_symbol}")
            logger.info("Ensure company metadata is loaded via adapters before analysis")
            return {'industry': 'Unknown', 'sector': 'Unknown', 'industry_key': 'Default'}

        except Exception as e:
            logger.warning(f"Could not fetch industry info for {ticker_symbol}: {e}")
            return {'industry': 'Unknown', 'sector': 'Unknown', 'industry_key': 'Default'}

    def _map_to_benchmark_industry(self, sector: str) -> str:
        """
        Map sector name to our benchmark industry categories

        Args:
            sector (str): Sector name from data source

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

    @performance_timer("pb_industry_comparison", include_args=True)
    def _compare_to_industry(self, pb_ratio: Optional[float], industry_key: str, ticker_symbol: str = None) -> Dict[str, Any]:
        """
        Compare P/B ratio to industry benchmarks using real-time industry data when available

        Args:
            pb_ratio (float or None): Current P/B ratio
            industry_key (str): Industry category key
            ticker_symbol (str, optional): Ticker symbol for real-time industry data

        Returns:
            dict: Industry comparison results with cache status
        """
        if pb_ratio is None:
            return {'error': 'pb_ratio_unavailable'}

        # Try to get real-time industry statistics with caching
        industry_stats = None
        cache_info = {'data_source': 'static', 'cache_used': False}
        
        if self.industry_service and ticker_symbol:
            try:
                industry_stats = self.industry_service.get_industry_pb_statistics(ticker_symbol)
                if industry_stats:
                    cache_info['data_source'] = 'real_time'
                    cache_info['cache_used'] = True
                    cache_info['peer_count'] = industry_stats.peer_count
                    cache_info['data_quality'] = industry_stats.data_quality_score
                    cache_info['last_updated'] = industry_stats.last_updated.isoformat() if industry_stats.last_updated else None
                    logger.info(f"Using real-time industry data for {ticker_symbol}: {industry_stats.peer_count} peers")
            except Exception as e:
                logger.warning(f"Failed to fetch real-time industry data for {ticker_symbol}: {e}")

        # Use real-time data if available, otherwise fall back to static benchmarks
        if industry_stats:
            benchmarks = {
                'median': industry_stats.median_pb,
                'low': industry_stats.q1_pb or (industry_stats.median_pb * 0.6 if industry_stats.median_pb else 1.0),
                'high': industry_stats.q3_pb or (industry_stats.median_pb * 1.8 if industry_stats.median_pb else 3.0)
            }
            cache_info['sector'] = industry_stats.sector
            cache_info['industry'] = industry_stats.industry
        else:
            benchmarks = self.industry_benchmarks.get(industry_key, self.industry_benchmarks['Default'])
            cache_info['data_source'] = 'static_fallback'

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

        result = {
            'industry_key': industry_key,
            'benchmarks': benchmarks,
            'current_pb': pb_ratio,
            'position': position,
            'percentile': percentile,
            'discount_premium_to_median': discount_premium,
            'analysis': self._generate_industry_analysis(pb_ratio, benchmarks, position),
            'cache_info': cache_info,
        }

        # Store industry comparison result in var_input_data for reference
        if self.var_input_data and ticker_symbol:
            try:
                self.var_input_data.set_variable(
                    ticker_symbol,
                    "pb_industry_comparison",
                    result,
                    source="calculated",
                    metadata={
                        "calculation_method": f"industry_comparison({industry_key})",
                        "data_source": cache_info.get('data_source', 'static'),
                        "peer_count": cache_info.get('peer_count', 0),
                        "quality_score": cache_info.get('data_quality', 0.8),
                        "calculated_by": "pb_valuation_module"
                    }
                )
                
                # Also store individual industry benchmarks as separate variables for easy access
                for benchmark_type, value in benchmarks.items():
                    self.var_input_data.set_variable(
                        ticker_symbol,
                        f"pb_industry_{benchmark_type}",
                        value,
                        source="industry_data",
                        metadata={
                            "industry": industry_key,
                            "data_source": cache_info.get('data_source', 'static'),
                            "calculated_by": "pb_valuation_module"
                        }
                    )
                    
                logger.debug(f"Stored industry comparison data for {ticker_symbol} in var_input_data")
            except Exception as e:
                logger.debug(f"Failed to store industry comparison in var_input_data: {e}")

        return result

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

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the industry data cache status
        
        Returns:
            dict: Cache information including file count, TTL, and status
        """
        if self.industry_service:
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

    def clear_industry_cache(self, ticker: Optional[str] = None):
        """
        Clear the industry data cache
        
        Args:
            ticker: Specific ticker to clear, or None to clear all
        """
        if self.industry_service:
            try:
                self.industry_service.clear_cache(ticker)
                logger.info(f"Cleared industry cache{' for ' + ticker if ticker else ''}")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
        else:
            logger.warning("IndustryDataService not available - cannot clear cache")

    @performance_timer("pb_historical_analysis", include_args=True)
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
            # Check if we have cached historical analysis in var_input_data
            cache_key = f"historical_pb_analysis_{years}y"
            if self.var_input_data:
                try:
                    cached_analysis = self.var_input_data.get_variable(ticker_symbol, cache_key)
                    if cached_analysis:
                        cached_metadata = self.var_input_data.get_variable_metadata(ticker_symbol, cache_key)
                        # Check if cache is still fresh (less than 1 day old)
                        if cached_metadata and cached_metadata.timestamp:
                            cache_age = datetime.now() - cached_metadata.timestamp
                            if cache_age.days < 1:
                                logger.info(f"Using cached historical P/B analysis (age: {cache_age})")
                                return cached_analysis
                except Exception as e:
                    logger.debug(f"Could not retrieve cached historical analysis: {e}")

            # Get historical price and book value data from VarInputData
            # Request more years than needed to ensure we have data for older Excel years
            if not self.var_input_data:
                logger.error("VarInputData not available for historical P/B analysis")
                return {'error': 'var_input_data_not_available'}

            # Get historical price data from VarInputData
            try:
                hist_price_data = self.var_input_data.get_historical_data(
                    ticker_symbol, 'stock_price', years=max(years, 10)
                )

                if not hist_price_data:
                    logger.warning(f"No historical price data available for {ticker_symbol}")
                    return {'error': 'no_historical_data'}

                # Convert to DataFrame for compatibility with existing calculation methods
                import pandas as pd
                hist_prices = pd.DataFrame(hist_price_data, columns=['Date', 'Close'])
                hist_prices['Date'] = pd.to_datetime(hist_prices['Date'])
                hist_prices.set_index('Date', inplace=True)

            except Exception as e:
                logger.error(f"Failed to retrieve historical price data: {e}")
                return {'error': 'no_historical_data', 'error_message': str(e)}

            # Try Excel-based historical P/B calculation first (if in Excel mode)
            historical_pb = []
            if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
                logger.info("Attempting historical P/B calculation using Excel annual data")
                historical_pb = self._calculate_historical_pb_ratios_from_excel(hist_prices, ticker_symbol)

            # Fall back to VarInputData quarterly book value data if Excel method failed
            if not historical_pb:
                logger.info("Falling back to VarInputData for quarterly book value data")

                try:
                    # Get historical book value data
                    hist_book_value = self.var_input_data.get_historical_data(
                        ticker_symbol, 'book_value', years=max(years, 10)
                    )
                    hist_shares = self.var_input_data.get_historical_data(
                        ticker_symbol, 'shares_outstanding', years=max(years, 10)
                    )

                    if not hist_book_value or not hist_shares:
                        logger.warning("Insufficient book value or shares outstanding historical data")
                        return {'error': 'no_fundamental_data'}

                    # Convert to DataFrames for compatibility
                    quarterly_bs = pd.DataFrame(hist_book_value, columns=['Date', 'Book Value'])
                    quarterly_bs['Date'] = pd.to_datetime(quarterly_bs['Date'])
                    quarterly_bs.set_index('Date', inplace=True)
                    quarterly_bs = quarterly_bs.T  # Transpose to match expected format

                    shares_df = pd.DataFrame(hist_shares, columns=['Date', 'Shares Outstanding'])
                    shares_df['Date'] = pd.to_datetime(shares_df['Date'])
                    shares_df.set_index('Date', inplace=True)
                    shares_df = shares_df.T  # Transpose to match expected format

                    # Calculate historical P/B ratios using VarInputData
                    historical_pb = self._calculate_historical_pb_ratios(hist_prices, quarterly_bs, shares_df)

                except Exception as e:
                    logger.error(f"Failed to retrieve historical fundamental data: {e}")
                    return {'error': 'no_fundamental_data', 'error_message': str(e)}

            if not historical_pb:
                return {'error': 'pb_calculation_failed'}

            # Statistical analysis
            pb_values = [
                entry['pb_ratio'] for entry in historical_pb if entry['pb_ratio'] is not None
            ]

            if len(pb_values) < 2:
                return {'error': 'insufficient_data'}

            # Enhanced statistics with quality information
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

            # Quality analysis summary
            quality_summary = self._analyze_data_quality_summary(historical_pb)

            # Trend analysis
            trend_analysis = self._analyze_pb_trend(pb_values)

            result = {
                'period': f'{years} years',
                'data_points': len(pb_values),
                'total_years_processed': len([entry for entry in historical_pb]),
                'historical_data': historical_pb[-20:],  # Last 20 data points
                'quality_summary': quality_summary,
                'statistics': stats,
                'trend_analysis': trend_analysis,
                'interpretation': self._interpret_historical_pb(stats, trend_analysis),
                'data_quality_notes': self._generate_quality_notes(quality_summary),
            }

            # Cache the result in var_input_data for future use
            if self.var_input_data:
                try:
                    cache_key = f"historical_pb_analysis_{years}y"
                    self.var_input_data.set_variable(
                        ticker_symbol,
                        cache_key,
                        result,
                        source="calculated",
                        metadata={
                            "calculation_method": f"historical_pb_analysis({years}_years)",
                            "data_points": len(pb_values),
                            "quality_score": quality_summary.get('overall_quality', 0.8),
                            "calculated_by": "pb_valuation_module"
                        }
                    )
                    logger.debug(f"Cached historical P/B analysis for {ticker_symbol} ({years} years)")
                except Exception as e:
                    logger.debug(f"Failed to cache historical analysis: {e}")

            return result

        except Exception as e:
            logger.error(f"Error in historical P/B analysis: {e}")
            return {'error': 'analysis_failed', 'error_message': str(e)}

    def _calculate_single_pb_data_point(
        self, date_data: Tuple, quarterly_bs: pd.DataFrame, shares_info: pd.DataFrame
    ) -> Optional[Dict]:
        """
        Calculate a single P/B data point for parallel processing
        
        Args:
            date_data: Tuple of (date, price_row)
            quarterly_bs: Quarterly balance sheet data
            shares_info: Shares outstanding historical data
            
        Returns:
            dict: Single P/B data point or None if calculation fails
        """
        date, price_row = date_data
        
        try:
            price = price_row['Close']

            # Convert date to timezone-naive for comparison (fix timezone mismatch issue)
            date_naive = date.tz_localize(None) if date.tz is not None else date

            # Find closest balance sheet date
            closest_bs_date = None
            for bs_date in quarterly_bs.columns:
                # Convert balance sheet date to timezone-naive if needed
                bs_date_naive = bs_date.tz_localize(None) if bs_date.tz is not None else bs_date
                if bs_date_naive <= date_naive:
                    if closest_bs_date is None or bs_date_naive > (closest_bs_date.tz_localize(None) if closest_bs_date.tz is not None else closest_bs_date):
                        closest_bs_date = bs_date

            if closest_bs_date is None:
                return None

            # Get shareholders' equity
            bs_data = quarterly_bs[closest_bs_date]
            equity = None

            # Look for equity in balance sheet (expanded field list)
            equity_fields = [
                'Stockholders Equity',
                'Total Stockholder Equity',
                'Total Equity',
                'Common Stock Equity',
                'Shareholders Equity',
                'Total Shareholders Equity',
            ]
            for field in equity_fields:
                if field in bs_data.index and pd.notna(bs_data[field]):
                    equity = bs_data[field]
                    break

            if equity is None or equity <= 0:
                return None

            # Get shares outstanding for this period
            shares = None
            if shares_info is not None and not shares_info.empty:
                # Handle both Series and DataFrame formats for shares_info
                if isinstance(shares_info, pd.Series):
                    # Convert Series to DataFrame format for consistency
                    shares_df = pd.DataFrame({'BasicShares': shares_info})
                else:
                    shares_df = shares_info
                
                # Find closest shares data
                shares_dates = shares_df.index
                closest_shares_date = None
                for shares_date in shares_dates:
                    # Convert shares date to timezone-naive for comparison
                    shares_date_naive = shares_date.tz_localize(None) if shares_date.tz is not None else shares_date
                    if shares_date_naive <= date_naive:
                        if closest_shares_date is None or shares_date_naive > (closest_shares_date.tz_localize(None) if closest_shares_date.tz is not None else closest_shares_date):
                            closest_shares_date = shares_date

                if closest_shares_date is not None:
                    # Try different column names for shares outstanding
                    shares_columns = ['BasicShares', 'Shares', 'SharesOutstanding', shares_df.columns[0]]
                    for col in shares_columns:
                        if col in shares_df.columns:
                            shares_raw = shares_df.loc[closest_shares_date, col]
                            # If it's a Series, take the first/most recent value
                            if isinstance(shares_raw, pd.Series):
                                shares = shares_raw.iloc[0] if len(shares_raw) > 0 else None
                            else:
                                shares = shares_raw
                            if shares is not None:
                                break
                    
                    # If still no shares found and it's a Series, use the value directly
                    if shares is None and isinstance(shares_info, pd.Series):
                        shares_raw = shares_info.loc[closest_shares_date] if closest_shares_date in shares_info.index else None
                        if isinstance(shares_raw, pd.Series):
                            shares = shares_raw.iloc[0] if len(shares_raw) > 0 else None
                        else:
                            shares = shares_raw

            if shares is None or shares <= 0:
                return None

            # Calculate book value per share and P/B ratio
            book_value_per_share = equity / shares
            pb_ratio = price / book_value_per_share if book_value_per_share > 0 else None

            if pb_ratio is None:
                return None

            return {
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'book_value_per_share': book_value_per_share,
                'pb_ratio': pb_ratio,
                'equity': equity,
                'shares_outstanding': shares,
            }
            
        except Exception as e:
            logger.debug(f"Error calculating P/B for {date}: {e}")
            return None

    def _calculate_historical_pb_ratios(
        self, hist_prices: pd.DataFrame, quarterly_bs: pd.DataFrame, ticker
    ) -> List[Dict]:
        """
        Calculate historical P/B ratios from price and balance sheet data with parallel processing

        Args:
            hist_prices (pd.DataFrame): Historical price data
            quarterly_bs (pd.DataFrame): Quarterly balance sheet data
            shares_df (pd.DataFrame): Historical shares outstanding data

        Returns:
            list: Historical P/B data points
        """
        historical_pb = []

        try:
            # Get shares outstanding history
            shares_info = ticker.get_shares_full()
            
            # Prepare data for parallel processing
            date_data_list = [(date, price_row) for date, price_row in hist_prices.iterrows()]
            
            # Use parallel processing for better performance
            max_workers = min(4, len(date_data_list))  # Limit workers to avoid overwhelming APIs
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_date = {
                    executor.submit(self._calculate_single_pb_data_point, date_data, quarterly_bs, shares_info): date_data[0]
                    for date_data in date_data_list
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_date):
                    try:
                        result = future.result()
                        if result is not None:
                            historical_pb.append(result)
                    except Exception as e:
                        date = future_to_date[future]
                        logger.debug(f"Failed to calculate P/B for {date}: {e}")
            
            # Sort by date to maintain chronological order
            historical_pb.sort(key=lambda x: x['date'])

            return historical_pb

        except Exception as e:
            logger.error(f"Error calculating historical P/B ratios: {e}")
            return []

    def _calculate_historical_pb_ratios_from_excel(
        self, hist_prices: pd.DataFrame, ticker_symbol: str
    ) -> List[Dict]:
        """
        Calculate historical P/B ratios using Excel annual data with graduated quality scoring
        
        This method now uses graduated quality scoring instead of binary pass/fail validation.
        Data points are included with their quality level rather than being completely excluded.
        
        Args:
            hist_prices (pd.DataFrame): Historical price data from API
            ticker_symbol (str): Stock ticker symbol
            
        Returns:
            list: Historical P/B data points with quality assessments
        """
        historical_pb = []
        quality_stats = {'high': 0, 'good': 0, 'acceptable': 0, 'low': 0, 'unusable': 0}
        
        try:
            # Get annual balance sheet data from Excel
            balance_data = self.financial_calculator.financial_data.get('balance_fy', pd.DataFrame())
            if balance_data.empty:
                logger.warning("No Excel balance sheet data available for historical P/B calculation")
                return []
                
            # Get the years from the Excel data (column headers)
            if hasattr(balance_data, 'columns'):
                excel_years = balance_data.columns.tolist()
            else:
                logger.warning("Excel balance sheet data has no columns")
                return []
                
            logger.info(f"Found {len(excel_years)} years of Excel balance sheet data for historical P/B: {excel_years}")
            
            # Set up interpolation context for enhanced shares extraction
            # Filter to valid year column identifiers (skip metadata columns)
            valid_years = [year for year in excel_years if isinstance(year, str) and 
                          (year.startswith('FY') or year in ['LTM']) and 
                          year not in ['', 'nan']]
            
            if valid_years:
                logger.info(f"Setting up interpolation context with valid years: {valid_years}")
                self._available_years_for_interpolation = True
                self._all_available_years = valid_years
            else:
                self._available_years_for_interpolation = False
                self._all_available_years = []
                logger.warning("No valid year identifiers found for interpolation context")
            
            # For each year in Excel data, assess data quality and calculate P/B if possible
            for year in excel_years:
                try:
                    year_assessment = self._assess_year_data_quality(
                        year, balance_data, hist_prices, ticker_symbol
                    )
                    
                    # Skip invalid/empty year columns
                    if year is None or year == '' or pd.isna(year):
                        logger.debug(f"Skipping invalid year column: {year}")
                        continue
                    
                    # Track what data was available vs used for comprehensive logging
                    data_availability_log = {
                        'year': year,
                        'equity_attempted': [],
                        'equity_found': None,
                        'shares_attempted': [],
                        'shares_found': None,
                        'price_search_result': None
                    }
                    
                    # Convert year to datetime for price matching
                    actual_year = None
                    price = None
                    closest_price_date = None
                    price_match_quality = 'unavailable'
                    
                    if isinstance(year, (int, float)):
                        actual_year = int(year)
                        year_end = pd.Timestamp(f"{actual_year}-12-31")
                    elif isinstance(year, str):
                        # Handle 'FY-N' format where N is years back from current
                        if year.startswith('FY-'):
                            try:
                                years_back = int(year.replace('FY-', ''))
                                current_year = datetime.now().year
                                actual_year = current_year - years_back
                                year_end = pd.Timestamp(f"{actual_year}-12-31")
                            except ValueError:
                                logger.warning(f"Could not parse year format: {year}")
                                continue
                        elif year == 'FY':
                            # Current year
                            actual_year = datetime.now().year
                            year_end = pd.Timestamp(f"{actual_year}-12-31")
                        else:
                            # Try direct parsing
                            year_end = pd.Timestamp(year)
                            actual_year = year_end.year
                    
                    # Find price data with quality assessment
                    if actual_year:
                        price, closest_price_date, price_match_quality = self._find_historical_price_with_quality(
                            hist_prices, year_end, actual_year
                        )
                        data_availability_log['price_search_result'] = {
                            'target_date': year_end.strftime('%Y-%m-%d'),
                            'found_date': closest_price_date.strftime('%Y-%m-%d') if closest_price_date else None,
                            'price': price,
                            'match_quality': price_match_quality
                        }
                    
                    # Extract equity from Excel with quality tracking
                    equity, equity_source, equity_field_used = self._extract_equity_with_quality_tracking(
                        balance_data, year, data_availability_log
                    )
                    
                    # Get shares outstanding with quality tracking  
                    shares, shares_source = self._extract_shares_with_quality_tracking(
                        year, actual_year, data_availability_log
                    )
                    
                    # Assess overall data quality for this data point
                    quality_level, quality_assessment = assess_pb_data_quality(
                        equity_source=equity_source,
                        shares_source=shares_source,
                        price_match_quality=price_match_quality,
                        equity_value=equity,
                        shares_value=shares,
                        price_value=price
                    )
                    
                    # Update quality statistics
                    quality_stats[quality_level.value] += 1
                    
                    # Comprehensive logging of data quality assessment
                    logger.info(f"Year {year} (actual: {actual_year}) - Quality: {quality_level} ({quality_level.score}/100)")
                    logger.info(f"  Data sources: Equity={equity_source}, Shares={shares_source}, Price={price_match_quality}")
                    logger.info(f"  Quality factors: {', '.join(quality_assessment.get('quality_factors', []))}")
                    logger.info(f"  Data availability log: {data_availability_log}")
                    
                    # Include data point if quality is acceptable or better (not unusable)
                    if quality_level != DataQualityLevel.UNUSABLE:
                        # Calculate book value per share and P/B ratio
                        book_value_per_share = equity * 1_000_000 / shares  # Convert equity to actual currency units
                        pb_ratio = price / book_value_per_share if book_value_per_share > 0 else None
                        
                        if pb_ratio is not None:
                            data_point = {
                                'date': closest_price_date.strftime('%Y-%m-%d'),
                                'year': year,
                                'actual_year': actual_year,
                                'price': price,
                                'book_value_per_share': book_value_per_share,
                                'pb_ratio': pb_ratio,
                                'shares_outstanding': shares,
                                'equity': equity * 1_000_000,  # Store in actual currency units
                                'data_source': 'excel_annual',
                                'quality_level': quality_level.value,
                                'quality_score': quality_level.score,
                                'quality_description': quality_level.description,
                                'quality_assessment': quality_assessment,
                                'data_availability_log': data_availability_log
                            }
                            
                            historical_pb.append(data_point)
                            
                            logger.info(f"✓ Included P/B for {year}: P/B={pb_ratio:.2f}, Quality={quality_level} ({quality_level.score}/100)")
                    else:
                        logger.warning(f"✗ Excluded {year} due to unusable data quality: {quality_assessment.get('quality_factors', [])}")
                
                except Exception as e:
                    logger.warning(f"Error processing year {year} for historical P/B: {e}")
                    quality_stats['unusable'] += 1
                    continue
            
            # Log overall quality statistics
            total_years = len(excel_years)
            logger.info(f"Historical P/B Quality Summary for {ticker_symbol}:")
            logger.info(f"  Total years processed: {total_years}")
            logger.info(f"  High Quality: {quality_stats['high']} ({quality_stats['high']/total_years*100:.1f}%)")
            logger.info(f"  Good Quality: {quality_stats['good']} ({quality_stats['good']/total_years*100:.1f}%)")
            logger.info(f"  Acceptable Quality: {quality_stats['acceptable']} ({quality_stats['acceptable']/total_years*100:.1f}%)")
            logger.info(f"  Low Quality: {quality_stats['low']} ({quality_stats['low']/total_years*100:.1f}%)")
            logger.info(f"  Unusable: {quality_stats['unusable']} ({quality_stats['unusable']/total_years*100:.1f}%)")
            logger.info(f"  Data points included: {len(historical_pb)}")
                    
            return historical_pb
            
        except Exception as e:
            logger.error(f"Error calculating historical P/B ratios from Excel: {e}")
            return []

    def _assess_year_data_quality(
        self, year, balance_data: pd.DataFrame, hist_prices: pd.DataFrame, ticker_symbol: str
    ) -> Dict[str, Any]:
        """
        Preliminary assessment of data availability for a given year
        
        Args:
            year: Year identifier from Excel data
            balance_data: Balance sheet DataFrame
            hist_prices: Historical price data
            ticker_symbol: Stock ticker symbol
            
        Returns:
            dict: Preliminary assessment of data availability
        """
        # This could be expanded for pre-filtering or optimization
        # For now, return basic structure
        return {
            'year': year,
            'has_balance_data': year in balance_data.columns if not balance_data.empty else False,
            'price_data_available': not hist_prices.empty
        }

    def _find_historical_price_with_quality(
        self, hist_prices: pd.DataFrame, year_end: pd.Timestamp, actual_year: int
    ) -> Tuple[Optional[float], Optional[pd.Timestamp], str]:
        """
        Find historical price data with quality assessment
        
        Args:
            hist_prices: Historical price DataFrame
            year_end: Target date (year end)
            actual_year: Actual year number
            
        Returns:
            Tuple of (price, date_found, quality_level)
        """
        try:
            # Handle timezone issues by making year_end timezone-aware if needed
            if hist_prices.index.tz is not None:
                year_end = year_end.tz_localize(hist_prices.index.tz)
            elif year_end.tz is not None:
                year_end = year_end.tz_localize(None)
            
            # Try to find price within different time windows, assessing quality
            
            # Exact match (within 1 week)
            exact_window = hist_prices[
                (hist_prices.index >= year_end - pd.DateOffset(days=7)) & 
                (hist_prices.index <= year_end + pd.DateOffset(days=7))
            ]
            
            if not exact_window.empty:
                closest_date = min(exact_window.index, key=lambda x: abs((x - year_end).days))
                price = exact_window.loc[closest_date, 'Close']
                days_diff = abs((closest_date - year_end).days)
                
                if days_diff <= 1:
                    return price, closest_date, 'exact'
                elif days_diff <= 7:
                    return price, closest_date, 'close'
            
            # Close match (within 1 month) 
            close_window = hist_prices[
                (hist_prices.index >= year_end - pd.DateOffset(months=1)) & 
                (hist_prices.index <= year_end + pd.DateOffset(months=1))
            ]
            
            if not close_window.empty:
                closest_date = min(close_window.index, key=lambda x: abs((x - year_end).days))
                price = close_window.loc[closest_date, 'Close']
                return price, closest_date, 'close'
            
            # Approximate match (within 6 months)
            approx_window = hist_prices[
                (hist_prices.index >= year_end - pd.DateOffset(months=6)) & 
                (hist_prices.index <= year_end + pd.DateOffset(months=6))
            ]
            
            if not approx_window.empty:
                closest_date = min(approx_window.index, key=lambda x: abs((x - year_end).days))
                price = approx_window.loc[closest_date, 'Close']
                return price, closest_date, 'approximate'
            
            # Poor match (any data available)
            if not hist_prices.empty:
                closest_date = min(hist_prices.index, key=lambda x: abs((x - year_end).days))
                price = hist_prices.loc[closest_date, 'Close']
                return price, closest_date, 'poor'
            
            return None, None, 'unavailable'
            
        except Exception as e:
            logger.warning(f"Error finding historical price for year {actual_year}: {e}")
            return None, None, 'unavailable'

    def _extract_equity_with_quality_tracking(
        self, balance_data: pd.DataFrame, year, data_availability_log: Dict
    ) -> Tuple[Optional[float], str, Optional[str]]:
        """
        Extract equity with comprehensive quality tracking
        
        Args:
            balance_data: Balance sheet DataFrame
            year: Year identifier
            data_availability_log: Log dict to update with attempts
            
        Returns:
            Tuple of (equity_value, source_type, field_name_used)
        """
        equity_fields = [
            'Total Equity',  # This is the main one found at row 42
            'Common Equity',  # Alternative at row 38
            'Total Stockholder Equity',
            'Stockholders Equity',
            'Total Shareholders\' Equity',
            'Shareholders\' Equity',
            'Shareholder Equity',
            'Stockholder Equity'
        ]
        
        data_availability_log['equity_attempted'] = equity_fields.copy()
        
        for field in equity_fields:
            try:
                # Use the financial calculator's extraction method directly on balance data
                temp_balance_data = self.financial_calculator.financial_data.get('balance_fy', pd.DataFrame())
                if not temp_balance_data.empty:
                    equity_values = self.financial_calculator._extract_metric_values(temp_balance_data, field)
                    if equity_values and len(equity_values) > 0:
                        # Find the corresponding year index
                        year_columns = temp_balance_data.columns.tolist()
                        if year in year_columns:
                            year_idx = year_columns.index(year)
                            if year_idx < len(equity_values):
                                equity = equity_values[year_idx]
                                if equity and equity != 0:
                                    data_availability_log['equity_found'] = {
                                        'field': field,
                                        'value': equity,
                                        'source': 'excel'
                                    }
                                    logger.debug(f"Found equity using field '{field}': {equity}")
                                    return equity, 'excel', field
            except Exception as e:
                logger.debug(f"Could not extract {field} for {year}: {e}")
                continue
        
        data_availability_log['equity_found'] = None
        return None, 'unavailable', None

    def _extract_shares_with_quality_tracking(
        self, year, actual_year: Optional[int], data_availability_log: Dict
    ) -> Tuple[Optional[float], str]:
        """
        Extract shares outstanding with enhanced quality tracking and fallback hierarchy
        
        Implements robust fallback hierarchy:
        1) Year-specific shares from Excel income statement
        2) Interpolated shares for missing years (if enough data points available)
        3) Current shares outstanding as last resort
        4) Skip year if no reliable shares data
        
        Args:
            year: Year identifier from Excel
            actual_year: Actual year number
            data_availability_log: Log dict to update with attempts
            
        Returns:
            Tuple of (shares_value, source_type)
        """
        data_availability_log['shares_attempted'] = []
        data_availability_log['shares_methods_tried'] = []
        
        # PRIORITY 1: Try year-specific shares extraction
        data_availability_log['shares_attempted'].append('excel_year_specific')
        data_availability_log['shares_methods_tried'].append('Year-specific extraction')
        
        if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding_by_year'):
            try:
                year_specific_shares = self.financial_calculator._extract_excel_shares_outstanding_by_year(year)
                if year_specific_shares and year_specific_shares > 0:
                    data_availability_log['shares_found'] = {
                        'source': 'excel_year_specific',
                        'field': 'Weighted Average Basic Shares Out',
                        'value': year_specific_shares,
                        'quality': 'high',
                        'method': f'Direct extraction from column {year}'
                    }
                    logger.info(f"Found year-specific shares for {year}: {year_specific_shares:,.0f}")
                    return year_specific_shares, 'excel_year_specific'
            except Exception as e:
                logger.debug(f"Year-specific shares extraction failed for {year}: {e}")
        
        # PRIORITY 2: Try interpolation if we have context of other years
        if hasattr(self, '_available_years_for_interpolation') and self._available_years_for_interpolation:
            data_availability_log['shares_attempted'].append('interpolation_attempt')
            data_availability_log['shares_methods_tried'].append('Interpolation between available years')
            
            try:
                # Get shares data for surrounding years to enable interpolation
                years_to_check = [year]  # Start with current year
                # Add surrounding years if they exist in available years
                if hasattr(self, '_all_available_years'):
                    available_years = self._all_available_years
                    # Add years around the target year for interpolation context
                    if 'FY' in available_years:
                        years_to_check.append('FY')
                    for i in range(1, 6):  # Check FY-1 through FY-5
                        fy_minus = f'FY-{i}'
                        if fy_minus in available_years and fy_minus not in years_to_check:
                            years_to_check.append(fy_minus)
                
                if hasattr(self.financial_calculator, '_get_shares_outstanding_with_interpolation'):
                    shares_data = self.financial_calculator._get_shares_outstanding_with_interpolation(
                        years_to_check, 
                        logger_context=f"P/B historical analysis for {year}"
                    )
                    
                    if year in shares_data and shares_data[year]['value'] is not None:
                        shares_info = shares_data[year]
                        shares_value = shares_info['value']
                        source_type = shares_info['source']
                        
                        if shares_value > 0:
                            data_availability_log['shares_found'] = {
                                'source': source_type,
                                'field': 'Weighted Average Basic Shares Out',
                                'value': shares_value,
                                'quality': shares_info['quality'],
                                'method': shares_info['method']
                            }
                            logger.info(f"Using {source_type} shares for {year}: {shares_value:,.0f}")
                            return shares_value, source_type
            except Exception as e:
                logger.debug(f"Interpolation attempt failed for {year}: {e}")
        
        # PRIORITY 3: Fallback to current shares outstanding from Excel
        data_availability_log['shares_attempted'].append('excel_current_fallback')
        data_availability_log['shares_methods_tried'].append('Current shares outstanding fallback')
        
        if hasattr(self.financial_calculator, '_extract_excel_shares_outstanding'):
            try:
                current_shares = self.financial_calculator._extract_excel_shares_outstanding()
                if current_shares and current_shares > 0:
                    data_availability_log['shares_found'] = {
                        'source': 'excel_current_fallback',
                        'field': 'Weighted Average Basic Shares Out',
                        'value': current_shares,
                        'quality': 'low',
                        'method': 'Using current shares outstanding as fallback'
                    }
                    logger.info(f"Using current Excel shares fallback for {year}: {current_shares:,.0f}")
                    return current_shares, 'excel_current_fallback'
            except Exception as e:
                logger.debug(f"Could not extract current Excel shares: {e}")
        
        # PRIORITY 4: Skip year if no reliable shares data
        data_availability_log['shares_found'] = {
            'source': 'unavailable',
            'field': None,
            'value': None,
            'quality': 'none',
            'method': 'No reliable shares data found - year skipped'
        }
        logger.warning(f"No reliable shares outstanding data available for {year} - skipping this year from P/B analysis")
        return None, 'unavailable'

    def _analyze_data_quality_summary(self, historical_pb: List[Dict]) -> Dict[str, Any]:
        """
        Analyze overall data quality for the historical P/B dataset
        
        Args:
            historical_pb: List of historical P/B data points with quality info
            
        Returns:
            dict: Quality summary statistics and breakdown
        """
        if not historical_pb:
            return {
                'total_data_points': 0,
                'quality_distribution': {},
                'average_quality_score': 0,
                'quality_trend': 'insufficient_data'
            }
        
        # Count by quality level
        quality_counts = {}
        quality_scores = []
        
        for entry in historical_pb:
            quality_level = entry.get('quality_level', 'unknown')
            quality_score = entry.get('quality_score', 0)
            
            quality_counts[quality_level] = quality_counts.get(quality_level, 0) + 1
            quality_scores.append(quality_score)
        
        total_points = len(historical_pb)
        quality_distribution = {
            level: {
                'count': count,
                'percentage': (count / total_points) * 100
            }
            for level, count in quality_counts.items()
        }
        
        # Calculate average quality score
        avg_quality_score = np.mean(quality_scores) if quality_scores else 0
        
        # Assess quality trend (are more recent data points higher quality?)
        quality_trend = 'stable'
        if len(quality_scores) >= 3:
            recent_scores = quality_scores[-3:]
            older_scores = quality_scores[:-3]
            if older_scores and recent_scores:
                recent_avg = np.mean(recent_scores)
                older_avg = np.mean(older_scores)
                if recent_avg > older_avg + 10:
                    quality_trend = 'improving'
                elif recent_avg < older_avg - 10:
                    quality_trend = 'declining'
        
        # Data source breakdown
        data_sources = {}
        for entry in historical_pb:
            source = entry.get('data_source', 'unknown')
            data_sources[source] = data_sources.get(source, 0) + 1
        
        # Most common quality factors
        quality_factors = {}
        for entry in historical_pb:
            factors = entry.get('quality_assessment', {}).get('quality_factors', [])
            for factor in factors:
                quality_factors[factor] = quality_factors.get(factor, 0) + 1
        
        return {
            'total_data_points': total_points,
            'quality_distribution': quality_distribution,
            'average_quality_score': avg_quality_score,
            'quality_trend': quality_trend,
            'data_sources': data_sources,
            'common_quality_factors': quality_factors,
            'has_high_quality_data': 'high' in quality_counts and quality_counts['high'] > 0,
            'usable_data_percentage': ((total_points - quality_counts.get('unusable', 0)) / total_points) * 100 if total_points > 0 else 0
        }

    def _generate_quality_notes(self, quality_summary: Dict[str, Any]) -> List[str]:
        """
        Generate user-friendly quality notes based on quality summary
        
        Args:
            quality_summary: Quality summary from _analyze_data_quality_summary
            
        Returns:
            list: List of quality notes for users
        """
        notes = []
        
        if not quality_summary or quality_summary.get('total_data_points', 0) == 0:
            return ['No historical P/B data available for quality assessment.']
        
        total_points = quality_summary.get('total_data_points', 0)
        avg_score = quality_summary.get('average_quality_score', 0)
        distribution = quality_summary.get('quality_distribution', {})
        
        # Overall quality assessment
        if avg_score >= 80:
            notes.append(f"Excellent data quality with average score of {avg_score:.0f}/100.")
        elif avg_score >= 60:
            notes.append(f"Good data quality with average score of {avg_score:.0f}/100.")
        elif avg_score >= 40:
            notes.append(f"Fair data quality with average score of {avg_score:.0f}/100. Results should be interpreted with caution.")
        else:
            notes.append(f"Poor data quality with average score of {avg_score:.0f}/100. Results have high uncertainty.")
        
        # Quality level breakdown
        high_quality = distribution.get('high', {}).get('count', 0)
        good_quality = distribution.get('good', {}).get('count', 0)
        acceptable_quality = distribution.get('acceptable', {}).get('count', 0)
        
        if high_quality > 0:
            notes.append(f"{high_quality} data points have high quality (Excel equity + historical shares + precise price matching).")
        
        if good_quality > 0:
            notes.append(f"{good_quality} data points have good quality (Excel equity + current shares + close price matching).")
        
        if acceptable_quality > 0:
            notes.append(f"{acceptable_quality} data points have acceptable quality with estimated components.")
        
        # Data completeness
        usable_pct = quality_summary.get('usable_data_percentage', 0)
        if usable_pct >= 90:
            notes.append(f"High data completeness: {usable_pct:.1f}% of years have usable data.")
        elif usable_pct >= 70:
            notes.append(f"Good data completeness: {usable_pct:.1f}% of years have usable data.")
        else:
            notes.append(f"Limited data completeness: Only {usable_pct:.1f}% of years have usable data.")
        
        # Quality trend
        trend = quality_summary.get('quality_trend', 'stable')
        if trend == 'improving':
            notes.append("Data quality is improving for more recent years.")
        elif trend == 'declining':
            notes.append("Data quality is declining for more recent years.")
        
        # Data source diversity
        sources = quality_summary.get('data_sources', {})
        if len(sources) > 1:
            source_list = list(sources.keys())
            notes.append(f"Data sourced from: {', '.join(source_list)}.")
        
        return notes

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

    def calculate_fair_value(self, historical_data: Optional[Dict[str, Any]] = None, book_value_per_share: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate P/B ratio based fair value estimation
        
        This method calculates fair value estimates based on P/B ratio analysis using
        industry benchmarks and historical P/B trends.
        
        Parameters
        ----------
        historical_data : dict, optional
            Historical P/B analysis data. If None, will be calculated automatically.
            
        book_value_per_share : float, optional
            Book value per share for calculations. If None, will be calculated from
            financial data.
            
        Returns
        -------
        dict
            Fair value calculation results containing:
            
            - fair_value_estimate : float
                Primary fair value estimate based on industry median P/B
            - valuation_range : dict
                Conservative, fair value, and optimistic estimates
            - current_pb_ratio : float
                Current P/B ratio
            - book_value_per_share : float
                Book value per share used in calculations
            - industry_benchmarks : dict
                Industry P/B benchmarks used
            - upside_downside : dict
                Potential upside/downside vs current price
            - confidence_level : str
                Confidence assessment (High/Medium/Low)
            - methodology : str
                Description of fair value calculation method
                
        Example
        -------
        >>> pb_valuator = PBValuator(financial_calculator)
        >>> result = pb_valuator.calculate_fair_value()
        >>> print(f"Fair Value: ${result['fair_value_estimate']:.2f}")
        >>> print(f"Current P/B: {result['current_pb_ratio']:.2f}")
        >>> 
        >>> # With historical data for enhanced accuracy
        >>> historical = pb_valuator._analyze_historical_pb('AAPL', years=5)
        >>> result = pb_valuator.calculate_fair_value(historical, 25.50)
        
        Notes
        -----
        Fair value is calculated using industry median P/B ratio applied to current
        book value per share. Historical trends and volatility are considered for
        confidence assessment.
        """
        try:
            # Get ticker symbol
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
            if not ticker_symbol:
                return {
                    'error': 'ticker_unavailable',
                    'error_message': 'Ticker symbol is required for fair value calculation'
                }

            # Calculate book value per share if not provided
            if book_value_per_share is None:
                book_value_per_share = self._calculate_book_value_per_share()
                
            if book_value_per_share is None or book_value_per_share <= 0:
                return {
                    'error': 'book_value_unavailable', 
                    'error_message': 'Unable to calculate book value per share for fair value estimation'
                }

            # Get current market data
            market_data = self._get_market_data(ticker_symbol)
            if not market_data:
                return {
                    'error': 'market_data_unavailable',
                    'error_message': 'Unable to fetch current market data for fair value calculation'
                }

            current_price = market_data.get('current_price', 0)
            current_pb_ratio = current_price / book_value_per_share if book_value_per_share > 0 else None

            # Get industry information and benchmarks
            industry_info = self._get_industry_info(ticker_symbol)
            industry_key = industry_info.get('industry_key', 'Default')
            benchmarks = self.industry_benchmarks.get(industry_key, self.industry_benchmarks['Default'])

            # Calculate fair value using industry median P/B
            fair_value_estimate = book_value_per_share * benchmarks['median']

            # Calculate valuation range using industry P/B range
            valuation_range = {
                'conservative': book_value_per_share * benchmarks['low'],
                'fair_value': fair_value_estimate,
                'optimistic': book_value_per_share * benchmarks['high']
            }

            # Calculate upside/downside potential
            upside_downside = {}
            if current_price > 0:
                upside_downside = {
                    'conservative_upside': (valuation_range['conservative'] - current_price) / current_price,
                    'fair_value_upside': (fair_value_estimate - current_price) / current_price,
                    'optimistic_upside': (valuation_range['optimistic'] - current_price) / current_price
                }

            # Use historical data if provided, otherwise calculate it
            if historical_data is None and ticker_symbol:
                try:
                    historical_data = self._analyze_historical_pb(ticker_symbol, years=5)
                except Exception as e:
                    logger.warning(f"Could not calculate historical P/B data: {e}")
                    historical_data = {}

            # Assess confidence level based on data quality and historical volatility
            confidence_level = self._assess_fair_value_confidence(
                current_pb_ratio, benchmarks, historical_data, market_data
            )

            # Prepare result
            result = {
                'fair_value_estimate': fair_value_estimate,
                'valuation_range': valuation_range,
                'current_price': current_price,
                'current_pb_ratio': current_pb_ratio,
                'book_value_per_share': book_value_per_share,
                'industry_benchmarks': benchmarks,
                'industry_info': industry_info,
                'upside_downside': upside_downside,
                'confidence_level': confidence_level,
                'historical_context': historical_data.get('statistics', {}) if historical_data else {},
                'methodology': f'Fair value calculated using industry median P/B ({benchmarks["median"]:.2f}) applied to book value per share',
                'calculation_date': datetime.now().isoformat(),
                'currency': getattr(self.financial_calculator, 'currency', 'USD'),
                'ticker_symbol': ticker_symbol
            }

            logger.info(f"Fair value calculation completed for {ticker_symbol}")
            logger.info(f"Fair value estimate: ${fair_value_estimate:.2f} (P/B: {benchmarks['median']:.2f} × BVPS: ${book_value_per_share:.2f})")
            
            return result

        except Exception as e:
            logger.error(f"Error in fair value calculation: {e}")
            return {
                'error': 'calculation_failed',
                'error_message': str(e),
                'ticker_symbol': ticker_symbol if 'ticker_symbol' in locals() else None
            }

    def _assess_fair_value_confidence(
        self, 
        current_pb_ratio: Optional[float], 
        benchmarks: Dict[str, float], 
        historical_data: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> str:
        """
        Assess confidence level for fair value calculation
        
        Args:
            current_pb_ratio: Current P/B ratio
            benchmarks: Industry benchmarks
            historical_data: Historical P/B analysis
            market_data: Current market data
            
        Returns:
            str: Confidence level (High/Medium/Low)
        """
        confidence_factors = []
        
        try:
            # Factor 1: Data quality
            if current_pb_ratio is not None and market_data.get('current_price', 0) > 0:
                confidence_factors.append('price_data_available')
            
            # Factor 2: Industry benchmark relevance
            industry_key = getattr(self, '_last_industry_key', 'Default')
            if industry_key != 'Default':
                confidence_factors.append('industry_specific_benchmarks')
            
            # Factor 3: Historical data quality
            if historical_data and 'statistics' in historical_data:
                stats = historical_data['statistics']
                if stats.get('std', float('inf')) < 2.0:  # Low volatility
                    confidence_factors.append('stable_historical_pb')
                    
            # Factor 4: Current P/B within reasonable range
            if current_pb_ratio and 0.1 <= current_pb_ratio <= 15.0:
                confidence_factors.append('reasonable_current_pb')
                
            # Factor 5: Market data completeness
            required_market_fields = ['current_price', 'market_cap', 'shares_outstanding']
            if all(market_data.get(field, 0) > 0 for field in required_market_fields):
                confidence_factors.append('complete_market_data')
            
            # Determine confidence level
            factor_count = len(confidence_factors)
            if factor_count >= 4:
                return 'High'
            elif factor_count >= 2:
                return 'Medium'
            else:
                return 'Low'
                
        except Exception as e:
            logger.warning(f"Error assessing fair value confidence: {e}")
            return 'Low'
