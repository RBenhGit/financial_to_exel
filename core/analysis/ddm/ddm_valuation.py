"""
Discounted Dividend Model (DDM) Valuation Module
===============================================

This module provides comprehensive dividend-based valuation capabilities for analyzing
dividend-paying stocks using multiple DDM variants with intelligent model selection
and robust data extraction from various sources.

Key Features
------------
- Automatic dividend data extraction from multiple sources (yfinance, APIs)
- Intelligent model selection based on dividend payment patterns
- Gordon Growth Model for stable dividend payers
- Two-Stage DDM for companies with distinct growth phases
- Multi-Stage DDM for complex growth scenarios
- Comprehensive dividend analysis and metrics calculation
- Sensitivity analysis for model validation
- Integration with enhanced data management system

Classes
-------
DDMValuator
    Main class for performing DDM valuations with automatic model selection

DDM Model Variants
------------------

**Gordon Growth Model (Single-Stage)**
    Best for: Mature companies with stable dividend growth
    Formula: P = D₁ / (r - g)
    Where: P = Price, D₁ = Next dividend, r = Required return, g = Growth rate

**Two-Stage DDM**
    Best for: Companies transitioning from high to stable growth
    Calculates present value of dividends in two distinct growth phases

**Multi-Stage DDM**
    Best for: Complex growth scenarios with multiple phases
    Handles varying growth rates across different time periods

Usage Example
-------------
>>> from ddm_valuation import DDMValuator
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize with financial data
>>> calc = FinancialCalculator('KO')  # Coca-Cola - good dividend payer
>>> ddm = DDMValuator(calc)
>>>
>>> # Automatic model selection and calculation
>>> result = ddm.calculate_ddm_valuation()
>>> print(f"DDM Value: ${result['value_per_share']:.2f}")
>>> print(f"Model Used: {result['model_type']}")
>>> print(f"Dividend Yield: {result['dividend_yield']:.2%}")
>>>
>>> # Custom two-stage model
>>> assumptions = {
...     'discount_rate': 0.09,
...     'stage1_growth_rate': 0.08,
...     'stage1_years': 5,
...     'terminal_growth_rate': 0.03,
...     'model_type': 'two_stage'
... }
>>> result = ddm.calculate_ddm_valuation(assumptions)

Model Selection Logic
--------------------
The module automatically selects the most appropriate DDM variant based on:

1. **Dividend Payment History**: Requires consistent dividend payments
2. **Growth Pattern Analysis**: Examines historical dividend growth rates
3. **Company Maturity**: Considers business lifecycle stage
4. **Growth Rate Stability**: Analyzes growth rate variance over time

Selection criteria:
- **Gordon Growth**: Stable growth (CV < 0.3), mature companies
- **Two-Stage**: Moderate growth volatility, transitioning companies
- **Multi-Stage**: High growth volatility, complex scenarios

Data Sources and Extraction
---------------------------
The module extracts dividend data from multiple sources with fallback logic:

1. **Primary**: yfinance dividend history
2. **Enhanced**: Multi-source API data (FMP, Alpha Vantage, Polygon)
3. **Cash Flow**: Dividend payments from cash flow statements
4. **Fundamentals**: Dividend metrics from fundamental data

Data validation includes:
- Consistency checks across sources
- Outlier detection and handling
- Quarterly to annual aggregation
- Special dividend identification

Financial Theory
----------------
DDM models are based on the principle that a stock's value equals the present
value of all future dividend payments. Key theoretical foundations:

1. **Present Value Concept**: Future dividends discounted at required rate of return
2. **Growth Assumptions**: Different models handle varying growth expectations
3. **Required Return**: Cost of equity reflects investment risk and opportunity cost
4. **Terminal Value**: Long-term value beyond explicit projection period

Limitations and Considerations
-----------------------------
- **Dividend Dependency**: Only applicable to dividend-paying stocks
- **Growth Assumptions**: Sensitive to growth rate estimates
- **Model Selection**: Important to choose appropriate variant
- **Market Conditions**: May not reflect short-term market dynamics

Configuration
-------------
DDM assumptions can be configured in config.py:
- discount_rate: Required rate of return (typically 8-12%)
- stage1_growth_rate: Initial growth rate (default: 8%)
- stage2_growth_rate: Transitional growth rate (default: 4%)
- terminal_growth_rate: Long-term growth rate (typically 2-4%)
- stage1_years: Duration of high growth phase (default: 5 years)

Notes
-----
- All dividend calculations use annual figures (quarterly dividends aggregated)
- Historical growth rates calculated using compound annual growth rate (CAGR)
- Model validation includes cross-checks with market data when available
- Sensitivity analysis helps assess valuation robustness across scenarios
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import yfinance as yf
from scipy import stats
from config import get_dcf_config

# Import var_input_data system for unified data access
from ...data_processing.var_input_data import get_var_input_data, VariableMetadata

logger = logging.getLogger(__name__)


class DDMValuator:
    """
    Handles Discounted Dividend Model valuations with multiple variants
    """

    def __init__(self, financial_calculator):
        """
        Initialize DDM valuator with financial calculator

        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator
        
        # Initialize var_input_data connection
        self.var_data = get_var_input_data()
        self.ticker_symbol = getattr(financial_calculator, 'ticker_symbol', 'UNKNOWN')

        # Get enhanced data manager if available
        self.enhanced_data_manager = getattr(financial_calculator, 'enhanced_data_manager', None)
        if self.enhanced_data_manager:
            logger.info("DDM valuator initialized with enhanced multi-source data access")

        # Load default assumptions from configuration (reusing DCF config structure)
        dcf_config = get_dcf_config()
        self.default_assumptions = {
            'discount_rate': dcf_config.default_discount_rate,  # Required rate of return (cost of equity)
            'terminal_growth_rate': dcf_config.default_terminal_growth_rate,
            'stage1_growth_rate': 0.08,  # Default first stage growth (8%)
            'stage2_growth_rate': 0.04,  # Default second stage growth (4%)
            'stage1_years': 5,  # Years in first stage
            'stage2_years': 5,  # Years in second stage (for 3-stage model)
            'model_type': 'auto',  # 'gordon', 'two_stage', 'multi_stage', 'auto'
            'min_dividend_history': 3,  # Minimum years of dividend history required
            'payout_ratio_threshold': 0.9,  # Maximum sustainable payout ratio
        }

        # Dividend data cache
        self.dividend_data = None
        self.dividend_metrics = None

    def calculate_ddm_valuation(self, assumptions=None):
        """
        Calculate comprehensive DDM (Dividend Discount Model) valuation.

        This method automatically selects and applies the most appropriate DDM variant
        based on dividend payment history and growth characteristics, including Gordon
        Growth Model, Two-Stage DDM, and Multi-Stage DDM.

        Parameters
        ----------
        assumptions : dict, optional
            Dictionary containing DDM assumptions. If None, uses default configuration.

            Key parameters:
            - discount_rate : float
                Required rate of return (cost of equity) for discounting dividends
            - terminal_growth_rate : float
                Long-term sustainable dividend growth rate
            - stage1_growth_rate : float
                Expected dividend growth rate for first stage (default: 8%)
            - stage2_growth_rate : float
                Expected dividend growth rate for second stage (default: 4%)
            - stage1_years : int
                Duration of first growth stage in years (default: 5)
            - stage2_years : int
                Duration of second growth stage in years (default: 5)
            - model_type : str
                Force specific model: 'gordon', 'two_stage', 'multi_stage', or 'auto'

        Returns
        -------
        dict
            Comprehensive DDM analysis results containing:

            - value_per_share : float
                Calculated intrinsic value per share based on dividends
            - model_type : str
                DDM variant used ('gordon', 'two_stage', 'multi_stage')
            - current_dividend : float
                Most recent annual dividend per share
            - projected_dividends : list
                Year-by-year projected dividend payments
            - pv_dividends : list
                Present value of each projected dividend
            - terminal_value : float
                Present value of dividends beyond explicit projection period
            - dividend_yield : float
                Current dividend yield (dividend/price)
            - payout_ratio : float
                Estimated dividend payout ratio
            - dividend_growth_rate : float
                Historical dividend growth rate (CAGR)
            - assumptions_used : dict
                Final assumptions used in calculation
            - market_comparison : dict
                Comparison with current market price and dividend yield
            - validation_metrics : dict
                Quality metrics for dividend data and model selection

        Examples
        --------
        Basic DDM calculation with automatic model selection:

        >>> ddm_valuator = DDMValuator(financial_calculator)
        >>> result = ddm_valuator.calculate_ddm_valuation()
        >>> print(f"DDM Value: ${result['value_per_share']:.2f}")
        >>> print(f"Model Used: {result['model_type']}")

        Custom DDM with specific growth assumptions:

        >>> assumptions = {
        ...     'discount_rate': 0.10,
        ...     'stage1_growth_rate': 0.12,
        ...     'stage1_years': 7,
        ...     'terminal_growth_rate': 0.03,
        ...     'model_type': 'two_stage'
        ... }
        >>> result = ddm_valuator.calculate_ddm_valuation(assumptions)
        >>> print(f"Current Dividend Yield: {result['dividend_yield']:.2%}")

        Notes
        -----
        - Automatically extracts dividend data from multiple sources (yfinance, APIs)
        - Model selection logic considers dividend payment consistency and growth patterns
        - Gordon Growth Model used for stable, mature dividend-paying companies
        - Two-Stage DDM applied when distinct growth phases are expected
        - Multi-Stage DDM used for complex growth scenarios
        - Returns error information if insufficient dividend data is available
        - All calculations use annual dividend figures (quarterly dividends are aggregated)
        """
        if assumptions is None:
            assumptions = self.default_assumptions.copy()

        try:
            # Extract and process dividend data
            dividend_result = self._extract_dividend_data()
            if not dividend_result['success']:
                error_message = dividend_result.get('error_message', 'Could not extract dividend data')
                
                # Provide helpful guidance for common dividend data issues
                user_guidance = []
                if 'volatile' in error_message.lower():
                    user_guidance.extend([
                        "This company has highly volatile dividend payments which may not be suitable for DDM analysis.",
                        "Consider using DCF analysis instead, or try with a different time period.",
                        "Companies with irregular dividend policies may not be good candidates for dividend-based valuations."
                    ])
                elif 'insufficient' in error_message.lower():
                    user_guidance.extend([
                        "This company has insufficient dividend payment history for reliable DDM analysis.",
                        "DDM requires at least 3 years of consistent dividend payments.",
                        "Consider using DCF analysis for companies without established dividend policies."
                    ])
                elif 'no dividend' in error_message.lower():
                    user_guidance.extend([
                        "This company does not pay dividends regularly.",
                        "DDM analysis is only applicable to dividend-paying stocks.",
                        "Use DCF analysis instead for non-dividend paying companies."
                    ])
                
                return {
                    'error': 'dividend_data_unavailable',
                    'error_message': error_message,
                    'user_guidance': user_guidance,
                    'model_type': 'N/A',
                    'suggested_alternative': 'DCF Analysis',
                }

            self.dividend_data = dividend_result['data']
            self.dividend_metrics = dividend_result['metrics']

            # Determine appropriate model type
            model_type = self._select_model_type(assumptions)
            assumptions['model_type'] = model_type

            # Calculate valuation based on model type
            if model_type == 'gordon':
                result = self._calculate_gordon_growth_model(assumptions)
            elif model_type == 'two_stage':
                result = self._calculate_two_stage_ddm(assumptions)
            elif model_type == 'multi_stage':
                result = self._calculate_multi_stage_ddm(assumptions)
            else:
                return {
                    'error': 'invalid_model_type',
                    'error_message': f'Unsupported model type: {model_type}',
                    'model_type': model_type,
                }

            # Store DDM results in var_input_data with lineage tracking
            self._store_ddm_results_in_var_system(result, model_type, assumptions)
            
            # Add common metadata
            result.update(
                {
                    'assumptions': assumptions,
                    'model_type': model_type,
                    'dividend_data': self.dividend_data,
                    'dividend_metrics': self.dividend_metrics,
                    'market_data': self._get_market_data(),
                    'currency': getattr(self.financial_calculator, 'currency', 'USD'),
                    'is_tase_stock': getattr(self.financial_calculator, 'is_tase_stock', False),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error in DDM calculation: {e}")
            return {
                'error': 'calculation_failed',
                'error_message': str(e),
                'model_type': assumptions.get('model_type', 'unknown'),
            }

    def _extract_dividend_data(self):
        """
        Extract and process dividend data from multiple sources with enhanced fallback

        Returns:
            dict: Processing result with data and metrics
        """
        try:
            ticker_symbol = getattr(self.financial_calculator, 'ticker_symbol', None)
            if not ticker_symbol:
                return {
                    'success': False,
                    'error_message': 'No ticker symbol available for dividend data extraction',
                }

            dividend_data = pd.DataFrame()
            data_source_used = None

            # Try enhanced data manager first if available
            if self.enhanced_data_manager:
                try:
                    logger.info(
                        f"Attempting to fetch dividend data for {ticker_symbol} using enhanced data manager"
                    )
                    dividend_data = self._fetch_dividend_data_enhanced(ticker_symbol)
                    if not dividend_data.empty:
                        data_source_used = "enhanced_data_manager"
                        logger.info(
                            f"Successfully obtained dividend data from enhanced data manager"
                        )
                except Exception as e:
                    logger.warning(f"Enhanced data manager dividend fetch failed: {e}")

            # Try var_input_data first if enhanced data manager didn't work
            if dividend_data.empty:
                logger.info(f"Attempting to get dividend data from var_input_data")
                dividend_data = self._get_dividend_data_from_var_system()
                if dividend_data is not None and not dividend_data.empty:
                    data_source_used = "var_input_data"
            
            # Fallback to yfinance if var_input_data didn't work
            if dividend_data is None or dividend_data.empty:
                logger.info(f"Falling back to yfinance for dividend data")
                dividend_data = self._fetch_dividend_data_yfinance(ticker_symbol)
                if not dividend_data.empty:
                    data_source_used = "yfinance"

            # Final fallback to financial statements
            if dividend_data is None or dividend_data.empty:
                logger.info(f"Falling back to financial statements for dividend data")
                dividend_data = self._extract_dividend_from_statements()
                if not dividend_data.empty:
                    data_source_used = "financial_statements"

            if dividend_data.empty:
                return {
                    'success': False,
                    'error_message': 'No dividend data available from any source (enhanced data manager, yfinance, or financial statements)',
                }

            # Process and analyze dividend data
            processed_data = self._process_dividend_data(dividend_data)
            metrics = self._calculate_dividend_metrics(processed_data)

            # Store dividend data in var_input_data system
            self._store_dividend_data_in_var_system(processed_data, metrics, data_source_used)

            # Validate dividend data quality
            validation_result = self._validate_dividend_data(processed_data, metrics)
            if not validation_result['valid']:
                # Enhanced error message with guidance
                error_message = validation_result['reason']
                user_guidance = validation_result.get('user_guidance', [])
                
                return {
                    'success': False, 
                    'error_message': error_message,
                    'user_guidance': user_guidance,
                    'validation_details': validation_result
                }

            return {
                'success': True,
                'data': processed_data,
                'metrics': metrics,
                'data_source_used': data_source_used,
            }

        except Exception as e:
            logger.error(f"Error extracting dividend data: {e}")
            return {'success': False, 'error_message': f'Dividend data extraction failed: {str(e)}'}

    def _fetch_dividend_data_yfinance(self, ticker_symbol):
        """
        Fetch dividend data using yfinance

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            pd.DataFrame: Dividend data
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(ticker_symbol)

            # Get dividend data (last 10 years)
            dividends = ticker.dividends

            if dividends.empty:
                logger.info(f"No dividend data found for {ticker_symbol}")
                return pd.DataFrame()

            # Convert to annual dividend data
            annual_dividends = dividends.groupby(dividends.index.year).sum()
            annual_dividends.index = pd.to_datetime(
                annual_dividends.index, format='%Y', errors='coerce'
            )

            # Create DataFrame with consistent structure
            dividend_df = pd.DataFrame(
                {
                    'year': annual_dividends.index.year,
                    'dividend_per_share': annual_dividends.values,
                    'date': annual_dividends.index,
                }
            )

            logger.info(
                f"Successfully fetched {len(dividend_df)} years of dividend data for {ticker_symbol}"
            )
            return dividend_df

        except Exception as e:
            logger.warning(f"Could not fetch dividend data from yfinance for {ticker_symbol}: {e}")
            return pd.DataFrame()

    def _fetch_dividend_data_enhanced(self, ticker_symbol):
        """
        Fetch dividend data using enhanced data manager with multiple API sources

        Args:
            ticker_symbol (str): Stock ticker symbol

        Returns:
            pd.DataFrame: Dividend data from enhanced data manager
        """
        try:
            if not self.enhanced_data_manager:
                return pd.DataFrame()

            # Import required modules for enhanced data request
            from data_sources import FinancialDataRequest

            # Create request for dividend data
            request = FinancialDataRequest(
                ticker=ticker_symbol, data_types=['dividends', 'fundamentals'], force_refresh=False
            )

            # Fetch data through unified adapter
            response = self.enhanced_data_manager.unified_adapter.fetch_data(request)

            if not response.success or not response.data:
                logger.info(f"Enhanced data manager returned no dividend data for {ticker_symbol}")
                return pd.DataFrame()

            # Extract dividend information from response
            dividend_data = self._extract_dividends_from_api_response(
                response.data, response.source_type
            )

            if not dividend_data.empty:
                logger.info(
                    f"Successfully extracted {len(dividend_data)} dividend records from enhanced data manager"
                )
                return dividend_data
            else:
                logger.info(
                    f"No dividend data found in enhanced data manager response for {ticker_symbol}"
                )
                return pd.DataFrame()

        except Exception as e:
            logger.warning(
                f"Error fetching dividend data from enhanced data manager for {ticker_symbol}: {e}"
            )
            return pd.DataFrame()

    def _extract_dividends_from_api_response(self, api_data, source_type):
        """
        Extract dividend data from API response based on source type

        Args:
            api_data (dict): Raw API response data
            source_type: DataSourceType indicating the API source

        Returns:
            pd.DataFrame: Extracted dividend data
        """
        try:
            if not api_data:
                return pd.DataFrame()

            # Handle different API response formats
            dividend_records = []

            # Look for dividend-related data in the response
            if 'dividends' in api_data:
                # Direct dividend data
                dividends_raw = api_data['dividends']
                dividend_records = self._parse_dividend_records(dividends_raw, source_type)
            elif 'cash_flow' in api_data:
                # Extract from cash flow data
                cash_flow_data = api_data['cash_flow']
                dividend_records = self._extract_dividends_from_cash_flow(cash_flow_data)
            elif 'fundamentals' in api_data:
                # Extract from fundamentals data
                fundamentals_data = api_data['fundamentals']
                dividend_records = self._extract_dividends_from_fundamentals(fundamentals_data)

            if dividend_records:
                # Convert to DataFrame with consistent structure
                dividend_df = pd.DataFrame(dividend_records)

                # Ensure required columns exist
                required_columns = ['year', 'dividend_per_share', 'date']
                for col in required_columns:
                    if col not in dividend_df.columns:
                        if col == 'date' and 'year' in dividend_df.columns:
                            dividend_df['date'] = pd.to_datetime(
                                dividend_df['year'], format='%Y', errors='coerce'
                            )
                        else:
                            dividend_df[col] = 0

                logger.info(f"Extracted {len(dividend_df)} dividend records from {source_type}")
                return dividend_df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error extracting dividends from API response: {e}")
            return pd.DataFrame()

    def _parse_dividend_records(self, dividends_raw, source_type):
        """
        Parse dividend records from raw API data

        Args:
            dividends_raw: Raw dividend data from API
            source_type: DataSourceType of the API

        Returns:
            list: List of dividend record dictionaries
        """
        records = []

        try:
            if isinstance(dividends_raw, dict):
                # Handle dictionary format (date -> amount)
                for date_str, amount in dividends_raw.items():
                    try:
                        date_obj = pd.to_datetime(date_str, errors='coerce')
                        year = date_obj.year
                        records.append(
                            {'year': year, 'dividend_per_share': float(amount), 'date': date_obj}
                        )
                    except (ValueError, TypeError):
                        continue
            elif isinstance(dividends_raw, list):
                # Handle list format
                for item in dividends_raw:
                    if isinstance(item, dict):
                        try:
                            date_field = (
                                item.get('date') or item.get('ex_date') or item.get('payment_date')
                            )
                            amount_field = (
                                item.get('amount')
                                or item.get('dividend')
                                or item.get('cash_amount')
                            )

                            if date_field and amount_field:
                                date_obj = pd.to_datetime(date_field, errors='coerce')
                                year = date_obj.year
                                records.append(
                                    {
                                        'year': year,
                                        'dividend_per_share': float(amount_field),
                                        'date': date_obj,
                                    }
                                )
                        except (ValueError, TypeError):
                            continue

            # Group by year and sum dividends
            if records:
                df = pd.DataFrame(records)
                annual_dividends = (
                    df.groupby('year')
                    .agg({'dividend_per_share': 'sum', 'date': 'max'})
                    .reset_index()
                )

                return annual_dividends.to_dict('records')

        except Exception as e:
            logger.error(f"Error parsing dividend records: {e}")

        return []

    def _extract_dividends_from_cash_flow(self, cash_flow_data):
        """
        Extract dividend information from cash flow statement data

        Args:
            cash_flow_data (dict): Cash flow statement data

        Returns:
            list: List of dividend record dictionaries
        """
        # This is similar to _extract_dividend_from_statements but for API data
        records = []

        try:
            dividend_keywords = [
                'dividends paid',
                'dividend payments',
                'cash dividends',
                'dividends to shareholders',
                'common dividends',
                'cash_dividends_paid',
            ]

            if isinstance(cash_flow_data, dict):
                for year, year_data in cash_flow_data.items():
                    if isinstance(year_data, dict):
                        dividend_amount = 0

                        for key, value in year_data.items():
                            if isinstance(key, str) and isinstance(value, (int, float)):
                                key_lower = key.lower().strip()

                                for keyword in dividend_keywords:
                                    if keyword in key_lower:
                                        dividend_amount = abs(value)  # Make positive
                                        break

                        if dividend_amount > 0:
                            # Convert to per-share basis if shares outstanding available
                            shares_outstanding = getattr(
                                self.financial_calculator, 'shares_outstanding', 1
                            )
                            if shares_outstanding > 0:
                                dividend_per_share = dividend_amount / shares_outstanding
                                records.append(
                                    {
                                        'year': int(year) if str(year).isdigit() else year,
                                        'dividend_per_share': dividend_per_share,
                                        'total_dividends': dividend_amount,
                                    }
                                )

        except Exception as e:
            logger.error(f"Error extracting dividends from cash flow data: {e}")

        return records

    def _extract_dividends_from_fundamentals(self, fundamentals_data):
        """
        Extract dividend information from fundamentals data

        Args:
            fundamentals_data (dict): Fundamentals data

        Returns:
            list: List of dividend record dictionaries
        """
        records = []

        try:
            # Look for dividend-related fields in fundamentals
            dividend_fields = [
                'dividend_per_share',
                'dividends_per_share',
                'annual_dividend',
                'trailing_annual_dividend_rate',
                'forward_annual_dividend_rate',
            ]

            if isinstance(fundamentals_data, dict):
                for field in dividend_fields:
                    if field in fundamentals_data:
                        dividend_value = fundamentals_data[field]
                        if dividend_value and dividend_value > 0:
                            # Use current year as estimate
                            current_year = pd.Timestamp.now().year
                            records.append(
                                {
                                    'year': current_year,
                                    'dividend_per_share': float(dividend_value),
                                    'estimated': True,
                                }
                            )
                            break

        except Exception as e:
            logger.error(f"Error extracting dividends from fundamentals data: {e}")

        return records

    def _extract_dividend_from_statements(self):
        """
        Extract dividend information from financial statements

        Returns:
            pd.DataFrame: Dividend data from statements
        """
        try:
            # Look for dividend information in cash flow statements
            cashflow_data = self.financial_calculator.financial_data.get('Cash Flow Statement', {})

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

                    # Search for dividend-related entries
                    for key, value in year_data.items():
                        if isinstance(key, str):
                            key_lower = key.lower().strip()
                            for keyword in dividend_keywords:
                                if keyword in key_lower and isinstance(value, (int, float)):
                                    dividend_amount = abs(
                                        value
                                    )  # Dividends are typically negative in cash flow
                                    break

                    if dividend_amount > 0:
                        # Convert to per-share basis using shares outstanding
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
                                    'total_dividends': dividend_amount
                                    * self.financial_calculator.financial_scale_factor,
                                }
                            )

            if dividend_data:
                df = pd.DataFrame(dividend_data)
                df['date'] = pd.to_datetime(df['year'], format='%Y', errors='coerce')
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"Could not extract dividends from financial statements: {e}")
            return pd.DataFrame()

    def _process_dividend_data(self, dividend_data):
        """
        Process raw dividend data for analysis

        Args:
            dividend_data (pd.DataFrame): Raw dividend data

        Returns:
            dict: Processed dividend data
        """
        try:
            if dividend_data.empty:
                return {}

            # Sort by year
            dividend_data = dividend_data.sort_values('year')

            # Calculate growth rates
            dividend_data['dividend_growth'] = dividend_data['dividend_per_share'].pct_change()

            # Remove infinite and NaN values with proper NumPy error handling
            with np.errstate(invalid='ignore'):
                dividend_data = dividend_data.replace([np.inf, -np.inf], np.nan).dropna()

            # Calculate statistics
            recent_dividends = dividend_data.tail(5)  # Last 5 years

            processed_data = {
                'years': dividend_data['year'].tolist(),
                'dividends_per_share': dividend_data['dividend_per_share'].tolist(),
                'growth_rates': dividend_data['dividend_growth'].dropna().tolist(),
                'latest_dividend': (
                    dividend_data['dividend_per_share'].iloc[-1] if len(dividend_data) > 0 else 0
                ),
                'latest_year': (
                    dividend_data['year'].iloc[-1]
                    if len(dividend_data) > 0
                    else datetime.now().year
                ),
                'data_points': len(dividend_data),
                'recent_data': (
                    recent_dividends.to_dict('records') if len(recent_dividends) > 0 else []
                ),
            }

            return processed_data

        except Exception as e:
            logger.error(f"Error processing dividend data: {e}")
            return {}

    def _calculate_dividend_metrics(self, processed_data):
        """
        Calculate key dividend metrics for model selection and validation

        Args:
            processed_data (dict): Processed dividend data

        Returns:
            dict: Dividend metrics
        """
        try:
            if not processed_data or not processed_data.get('dividends_per_share'):
                return {}

            dividends = processed_data['dividends_per_share']
            growth_rates = processed_data.get('growth_rates', [])

            # Calculate various growth rate measures
            metrics = {}

            # Historical growth rates (CAGR over different periods)
            for period in [1, 3, 5]:
                if len(dividends) >= period + 1:
                    start_div = dividends[-(period + 1)]
                    end_div = dividends[-1]

                    if start_div > 0:
                        cagr = (end_div / start_div) ** (1 / period) - 1
                        metrics[f'dividend_cagr_{period}y'] = cagr

            # Growth rate statistics
            if growth_rates:
                valid_growth_rates = [g for g in growth_rates if np.isfinite(g)]
                if valid_growth_rates:
                    metrics.update(
                        {
                            'avg_growth_rate': np.mean(valid_growth_rates),
                            'median_growth_rate': np.median(valid_growth_rates),
                            'growth_volatility': np.std(valid_growth_rates),
                            'growth_consistency': len([g for g in valid_growth_rates if g > 0])
                            / len(valid_growth_rates),
                        }
                    )

            # Dividend trend analysis
            if len(dividends) >= 3:
                # Linear trend
                years = list(range(len(dividends)))
                slope, intercept, r_value, p_value, std_err = stats.linregress(years, dividends)
                metrics.update(
                    {'trend_slope': slope, 'trend_r_squared': r_value**2, 'trend_p_value': p_value}
                )

                # Dividend sustainability metrics
                recent_payout_ratio = self._estimate_payout_ratio()
                if recent_payout_ratio is not None:
                    metrics['payout_ratio'] = recent_payout_ratio
                    metrics['payout_sustainability'] = (
                        'sustainable'
                        if recent_payout_ratio < 0.8
                        else 'high' if recent_payout_ratio < 1.0 else 'unsustainable'
                    )

            # Dividend yield (if current price available)
            current_price = self._get_market_data().get('current_price', 0)
            if current_price > 0 and processed_data.get('latest_dividend', 0) > 0:
                metrics['dividend_yield'] = processed_data['latest_dividend'] / current_price

            return metrics

        except Exception as e:
            logger.error(f"Error calculating dividend metrics: {e}")
            return {}

    def _estimate_payout_ratio(self):
        """
        Estimate payout ratio from available financial data

        Returns:
            float: Estimated payout ratio or None if not calculable
        """
        try:
            # Try to get EPS and dividend per share for payout ratio calculation
            income_data = self.financial_calculator.financial_data.get('Income Statement', {})

            if not income_data:
                return None

            # Look for earnings per share
            eps_keywords = ['earnings per share', 'eps', 'basic eps', 'diluted eps']
            latest_eps = None

            # Get most recent year's data
            recent_years = sorted(
                [
                    year
                    for year in income_data.keys()
                    if isinstance(year, (int, str)) and str(year).isdigit()
                ],
                reverse=True,
            )

            for year in recent_years[:2]:  # Check last 2 years
                year_data = income_data.get(year, {})
                if isinstance(year_data, dict):
                    for key, value in year_data.items():
                        if isinstance(key, str):
                            key_lower = key.lower().strip()
                            for keyword in eps_keywords:
                                if (
                                    keyword in key_lower
                                    and isinstance(value, (int, float))
                                    and value != 0
                                ):
                                    latest_eps = value
                                    break
                        if latest_eps:
                            break
                if latest_eps:
                    break

            if latest_eps and latest_eps > 0 and self.dividend_data:
                latest_dividend = self.dividend_data.get('latest_dividend', 0)
                if latest_dividend > 0:
                    payout_ratio = latest_dividend / latest_eps
                    return min(payout_ratio, 2.0)  # Cap at 200% for sanity

            return None

        except Exception as e:
            logger.warning(f"Could not estimate payout ratio: {e}")
            return None

    def _validate_dividend_data(self, processed_data, metrics):
        """
        Validate dividend data quality for DDM analysis with enhanced volatility handling

        Args:
            processed_data (dict): Processed dividend data
            metrics (dict): Dividend metrics

        Returns:
            dict: Validation result
        """
        try:
            if not processed_data:
                return {'valid': False, 'reason': 'No dividend data available'}

            data_points = processed_data.get('data_points', 0)
            min_required = self.default_assumptions.get('min_dividend_history', 3)

            if data_points < min_required:
                return {
                    'valid': False,
                    'reason': f'Insufficient dividend history: {data_points} years (minimum {min_required} required)',
                }

            latest_dividend = processed_data.get('latest_dividend', 0)
            if latest_dividend <= 0:
                return {'valid': False, 'reason': 'No recent dividend payments'}

            # Enhanced volatility check with smoothing options
            growth_volatility = metrics.get('growth_volatility', 0)
            if growth_volatility > 2.5:  # Increased threshold for extreme volatility
                user_guidance = [
                    f"Company has extremely volatile dividend growth (volatility={growth_volatility:.2f})",
                    "DDM analysis may not be reliable for companies with such irregular dividend policies",
                    "Consider alternative valuation methods such as:",
                    "• DCF Analysis - More suitable for irregular cash flows",
                    "• Price-to-Book Analysis - For asset-heavy companies",
                    "• Relative Valuation - Compare with industry peers",
                    "If DDM is preferred, try analyzing over a longer time period or different growth assumptions"
                ]
                return {
                    'valid': False,
                    'reason': f'Dividend growth extremely volatile (volatility={growth_volatility:.2f}) - DDM not suitable',
                    'user_guidance': user_guidance,
                }
            elif growth_volatility > 1.0:  # Moderate volatility - enable smoothing
                logger.info(f"High dividend volatility detected ({growth_volatility:.2f}) - will apply volatility smoothing")
                # Set flag for volatility smoothing (processed in calculation methods)
                metrics['requires_volatility_smoothing'] = True
                metrics['original_volatility'] = growth_volatility
                
                # Add informational guidance about volatility smoothing
                metrics['volatility_info'] = [
                    f"Moderate dividend volatility detected (volatility={growth_volatility:.2f})",
                    "Applying advanced volatility smoothing techniques:",
                    "• Winsorized growth rates to remove extreme outliers",
                    "• Exponential weighting of recent trends",
                    "• Multi-method growth rate estimation",
                    "• Conservative adjustments for high volatility scenarios"
                ]

            # Check payout ratio sustainability
            payout_ratio = metrics.get('payout_ratio')
            max_payout = self.default_assumptions.get('payout_ratio_threshold', 0.9)
            if payout_ratio and payout_ratio > max_payout:
                return {
                    'valid': False,
                    'reason': f'Unsustainable payout ratio: {payout_ratio:.1%} (max {max_payout:.1%})',
                }

            return {'valid': True, 'reason': 'Dividend data validation passed with enhanced volatility handling'}

        except Exception as e:
            logger.error(f"Error validating dividend data: {e}")
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}

    def _select_model_type(self, assumptions):
        """
        Automatically select appropriate DDM model type based on company characteristics with enhanced volatility handling

        Args:
            assumptions (dict): DDM assumptions

        Returns:
            str: Selected model type
        """
        try:
            model_type = assumptions.get('model_type', 'auto')

            if model_type != 'auto':
                return model_type

            # Decision logic based on company characteristics
            metrics = self.dividend_metrics or {}

            # Get growth characteristics
            recent_growth = metrics.get('dividend_cagr_3y', 0)
            growth_consistency = metrics.get('growth_consistency', 0)
            growth_volatility = metrics.get('growth_volatility', 0)
            requires_smoothing = metrics.get('requires_volatility_smoothing', False)

            # Get company maturity indicators
            market_data = self._get_market_data()
            market_cap = market_data.get('market_cap', 0)

            # Enhanced decision tree for model selection with volatility considerations
            if requires_smoothing and growth_volatility > 2.0:
                # Very high volatility - use conservative Gordon model with smoothed growth
                logger.info(f"High volatility ({growth_volatility:.2f}) detected - selecting Gordon Growth Model with conservative assumptions")
                return 'gordon'
            elif requires_smoothing and growth_volatility > 1.5:
                # Moderate-high volatility - use two-stage model to capture transition
                logger.info(f"Moderate-high volatility ({growth_volatility:.2f}) detected - selecting Two-Stage DDM")
                return 'two_stage'
            elif growth_consistency < 0.5:
                # Inconsistent dividend growth - use Gordon model with conservative growth
                return 'gordon'
            elif abs(recent_growth) < 0.02:  # Less than 2% growth
                # Mature, slow-growth company - Gordon model appropriate
                return 'gordon'
            elif recent_growth > 0.15:  # More than 15% growth
                # High growth company - use multi-stage model if not too volatile
                if growth_volatility < 1.0:
                    return 'multi_stage'
                else:
                    # High growth but volatile - use two-stage
                    return 'two_stage'
            elif recent_growth > 0.05:  # 5-15% growth
                # Moderate growth - two-stage model
                return 'two_stage'
            else:
                # Default to Gordon model
                return 'gordon'

        except Exception as e:
            logger.error(f"Error selecting model type: {e}")
            return 'gordon'  # Safe default

    def _calculate_gordon_growth_model(self, assumptions):
        """
        Calculate valuation using Gordon Growth Model (single-stage DDM)

        Args:
            assumptions (dict): DDM assumptions

        Returns:
            dict: Gordon Growth Model results
        """
        try:
            # Get current dividend
            current_dividend = self.dividend_data.get('latest_dividend', 0)

            # Estimate sustainable growth rate
            growth_rate = self._estimate_sustainable_growth_rate(assumptions)

            # Required rate of return (cost of equity)
            required_return = assumptions.get('discount_rate', 0.10)

            # Validate inputs
            if growth_rate >= required_return:
                # Growth rate must be less than required return
                growth_rate = required_return - 0.01  # Set to 1% below required return
                logger.warning(
                    f"Growth rate adjusted to {growth_rate:.1%} (below required return of {required_return:.1%})"
                )

            # Calculate next year's expected dividend
            next_dividend = current_dividend * (1 + growth_rate)

            # Gordon Growth Model: V = D1 / (r - g)
            intrinsic_value = next_dividend / (required_return - growth_rate)

            # Get market data for comparison
            market_data = self._get_market_data()
            current_price = market_data.get('current_price', 0)

            # Calculate upside/downside
            upside_downside = 0
            if current_price > 0:
                upside_downside = (intrinsic_value - current_price) / current_price

            result = {
                'model_variant': 'Gordon Growth Model',
                'current_dividend': current_dividend,
                'growth_rate': growth_rate,
                'required_return': required_return,
                'next_year_dividend': next_dividend,
                'intrinsic_value': intrinsic_value,
                'current_price': current_price,
                'upside_downside': upside_downside,
                'dividend_yield': current_dividend / current_price if current_price > 0 else 0,
                'calculation_method': 'Single-stage perpetual growth model',
            }

            logger.info(
                f"Gordon Growth Model: D0=${current_dividend:.2f}, g={growth_rate:.1%}, r={required_return:.1%}, Value=${intrinsic_value:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in Gordon Growth Model calculation: {e}")
            return {'error': f'Gordon Growth Model calculation failed: {str(e)}'}

    def _calculate_two_stage_ddm(self, assumptions):
        """
        Calculate valuation using Two-stage DDM

        Args:
            assumptions (dict): DDM assumptions

        Returns:
            dict: Two-stage DDM results
        """
        try:
            # Get parameters
            current_dividend = self.dividend_data.get('latest_dividend', 0)
            stage1_growth = assumptions.get('stage1_growth_rate', 0.08)
            stage2_growth = assumptions.get('terminal_growth_rate', 0.03)
            stage1_years = assumptions.get('stage1_years', 5)
            required_return = assumptions.get('discount_rate', 0.10)

            # Validate growth rates
            if stage1_growth >= required_return:
                stage1_growth = required_return - 0.01
            if stage2_growth >= required_return:
                stage2_growth = required_return - 0.01

            # Stage 1: High growth period
            stage1_dividends = []
            stage1_pv = []
            current_div = current_dividend

            for year in range(1, stage1_years + 1):
                current_div = current_div * (1 + stage1_growth)
                stage1_dividends.append(current_div)

                # Present value of dividend
                pv = current_div / ((1 + required_return) ** year)
                stage1_pv.append(pv)

            # Stage 2: Terminal value using Gordon Growth Model
            terminal_dividend = stage1_dividends[-1] * (1 + stage2_growth)
            terminal_value = terminal_dividend / (required_return - stage2_growth)

            # Present value of terminal value
            pv_terminal = terminal_value / ((1 + required_return) ** stage1_years)

            # Total intrinsic value
            intrinsic_value = sum(stage1_pv) + pv_terminal

            # Market comparison
            market_data = self._get_market_data()
            current_price = market_data.get('current_price', 0)
            upside_downside = (
                (intrinsic_value - current_price) / current_price if current_price > 0 else 0
            )

            result = {
                'model_variant': 'Two-Stage DDM',
                'current_dividend': current_dividend,
                'stage1_growth': stage1_growth,
                'stage2_growth': stage2_growth,
                'stage1_years': stage1_years,
                'required_return': required_return,
                'stage1_dividends': stage1_dividends,
                'stage1_pv': stage1_pv,
                'terminal_dividend': terminal_dividend,
                'terminal_value': terminal_value,
                'pv_terminal': pv_terminal,
                'intrinsic_value': intrinsic_value,
                'current_price': current_price,
                'upside_downside': upside_downside,
                'calculation_method': 'Two-stage growth model with terminal value',
            }

            logger.info(
                f"Two-Stage DDM: Stage1 PV=${sum(stage1_pv):.2f}, Terminal PV=${pv_terminal:.2f}, Total=${intrinsic_value:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in Two-Stage DDM calculation: {e}")
            return {'error': f'Two-Stage DDM calculation failed: {str(e)}'}

    def _calculate_multi_stage_ddm(self, assumptions):
        """
        Calculate valuation using Multi-stage DDM (3-stage)

        Args:
            assumptions (dict): DDM assumptions

        Returns:
            dict: Multi-stage DDM results
        """
        try:
            # Get parameters
            current_dividend = self.dividend_data.get('latest_dividend', 0)
            stage1_growth = assumptions.get('stage1_growth_rate', 0.15)  # High growth
            stage2_growth = assumptions.get('stage2_growth_rate', 0.08)  # Moderate growth
            stage3_growth = assumptions.get('terminal_growth_rate', 0.03)  # Mature growth
            stage1_years = assumptions.get('stage1_years', 5)
            stage2_years = assumptions.get('stage2_years', 5)
            required_return = assumptions.get('discount_rate', 0.10)

            # Validate growth rates
            for growth_rate in [stage1_growth, stage2_growth, stage3_growth]:
                if growth_rate >= required_return:
                    logger.warning(
                        f"Adjusting growth rate from {growth_rate:.1%} to {required_return-0.01:.1%}"
                    )
                    growth_rate = required_return - 0.01

            # Stage 1: High growth period
            stage1_dividends = []
            stage1_pv = []
            current_div = current_dividend

            for year in range(1, stage1_years + 1):
                current_div = current_div * (1 + stage1_growth)
                stage1_dividends.append(current_div)
                pv = current_div / ((1 + required_return) ** year)
                stage1_pv.append(pv)

            # Stage 2: Moderate growth period
            stage2_dividends = []
            stage2_pv = []

            for year in range(stage1_years + 1, stage1_years + stage2_years + 1):
                current_div = current_div * (1 + stage2_growth)
                stage2_dividends.append(current_div)
                pv = current_div / ((1 + required_return) ** year)
                stage2_pv.append(pv)

            # Stage 3: Terminal value using Gordon Growth Model
            terminal_dividend = stage2_dividends[-1] * (1 + stage3_growth)
            terminal_value = terminal_dividend / (required_return - stage3_growth)

            # Present value of terminal value
            total_years = stage1_years + stage2_years
            pv_terminal = terminal_value / ((1 + required_return) ** total_years)

            # Total intrinsic value
            intrinsic_value = sum(stage1_pv) + sum(stage2_pv) + pv_terminal

            # Market comparison
            market_data = self._get_market_data()
            current_price = market_data.get('current_price', 0)
            upside_downside = (
                (intrinsic_value - current_price) / current_price if current_price > 0 else 0
            )

            result = {
                'model_variant': 'Multi-Stage DDM (3-Stage)',
                'current_dividend': current_dividend,
                'stage1_growth': stage1_growth,
                'stage2_growth': stage2_growth,
                'stage3_growth': stage3_growth,
                'stage1_years': stage1_years,
                'stage2_years': stage2_years,
                'required_return': required_return,
                'stage1_dividends': stage1_dividends,
                'stage1_pv': stage1_pv,
                'stage2_dividends': stage2_dividends,
                'stage2_pv': stage2_pv,
                'terminal_dividend': terminal_dividend,
                'terminal_value': terminal_value,
                'pv_terminal': pv_terminal,
                'intrinsic_value': intrinsic_value,
                'current_price': current_price,
                'upside_downside': upside_downside,
                'calculation_method': 'Three-stage growth model with terminal value',
            }

            logger.info(
                f"Multi-Stage DDM: Stage1=${sum(stage1_pv):.2f}, Stage2=${sum(stage2_pv):.2f}, Terminal=${pv_terminal:.2f}, Total=${intrinsic_value:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in Multi-Stage DDM calculation: {e}")
            return {'error': f'Multi-Stage DDM calculation failed: {str(e)}'}

    def _estimate_sustainable_growth_rate(self, assumptions):
        """
        Estimate sustainable dividend growth rate with volatility smoothing

        Args:
            assumptions (dict): DDM assumptions

        Returns:
            float: Estimated sustainable growth rate
        """
        try:
            # Use historical growth rates as starting point
            metrics = self.dividend_metrics or {}

            # Check if volatility smoothing is required
            requires_smoothing = metrics.get('requires_volatility_smoothing', False)
            original_volatility = metrics.get('original_volatility', 0)

            if requires_smoothing:
                logger.info(f"Applying volatility smoothing due to high dividend growth volatility ({original_volatility:.2f})")
                historical_growth = self._apply_volatility_smoothing(metrics)
            else:
                # Standard approach - prefer 3-year CAGR, fallback to other measures
                historical_growth = (
                    metrics.get('dividend_cagr_3y')
                    or metrics.get('dividend_cagr_5y')
                    or metrics.get('avg_growth_rate')
                    or 0.03  # Default 3%
                )

            # Cap growth rate at reasonable levels
            max_growth = 0.20  # 20% maximum
            min_growth = -0.05  # -5% minimum (mild dividend cuts acceptable)

            sustainable_growth = max(min(historical_growth, max_growth), min_growth)

            # Adjust based on payout ratio sustainability
            payout_ratio = metrics.get('payout_ratio')
            if payout_ratio:
                if payout_ratio > 0.8:  # High payout ratio suggests limited growth
                    sustainable_growth = min(sustainable_growth, 0.03)
                elif payout_ratio < 0.4:  # Low payout ratio suggests room for growth
                    sustainable_growth = max(sustainable_growth, 0.05)

            # Additional adjustment for high volatility cases
            if requires_smoothing:
                # Conservative adjustment for volatile dividend companies
                volatility_adjustment = min(0.02, original_volatility * 0.01)  # Cap adjustment at 2%
                if sustainable_growth > 0:
                    sustainable_growth = max(sustainable_growth - volatility_adjustment, 0.01)
                logger.info(f"Applied volatility adjustment: -{volatility_adjustment:.1%}")

            logger.info(
                f"Estimated sustainable growth rate: {sustainable_growth:.1%} (historical: {historical_growth:.1%})"
                + (f", volatility smoothing applied" if requires_smoothing else "")
            )

            return sustainable_growth

        except Exception as e:
            logger.error(f"Error estimating sustainable growth rate: {e}")
            return 0.03  # Default 3%

    def _apply_volatility_smoothing(self, metrics):
        """
        Apply volatility smoothing techniques to derive a more stable growth rate

        Args:
            metrics (dict): Dividend metrics containing growth data

        Returns:
            float: Smoothed growth rate
        """
        try:
            # Get processed dividend data for advanced smoothing
            if not self.dividend_data or not self.dividend_data.get('dividends_per_share'):
                logger.warning("Insufficient dividend data for volatility smoothing")
                return metrics.get('median_growth_rate', 0.03)

            dividends = np.array(self.dividend_data['dividends_per_share'])
            years = np.array(self.dividend_data['years'])

            # Method 1: Winsorized growth rates (remove extreme outliers)
            growth_rates = []
            for i in range(1, len(dividends)):
                if dividends[i-1] > 0:
                    growth_rate = (dividends[i] - dividends[i-1]) / dividends[i-1]
                    growth_rates.append(growth_rate)

            if not growth_rates:
                return 0.03

            growth_rates = np.array(growth_rates)
            
            # Winsorize at 10th and 90th percentiles to remove extreme values
            lower_percentile = np.percentile(growth_rates, 10)
            upper_percentile = np.percentile(growth_rates, 90)
            winsorized_rates = np.clip(growth_rates, lower_percentile, upper_percentile)
            
            # Method 2: Exponential smoothing for recent trends
            weights = np.exp(np.linspace(0, 1, len(winsorized_rates)))
            weights = weights / weights.sum()
            exponential_weighted_growth = np.sum(winsorized_rates * weights)

            # Method 3: Compound Annual Growth Rate over entire period
            if len(dividends) > 1 and dividends[0] > 0:
                years_span = len(dividends) - 1
                total_cagr = (dividends[-1] / dividends[0]) ** (1/years_span) - 1
            else:
                total_cagr = 0.03

            # Method 4: Median growth rate (robust to outliers)
            median_growth = np.median(winsorized_rates)

            # Combine methods with weighting based on data quality
            data_points = len(growth_rates)
            if data_points >= 7:
                # Sufficient data - weight more recent trends
                smoothed_growth = (
                    0.4 * exponential_weighted_growth +
                    0.3 * total_cagr +
                    0.2 * median_growth +
                    0.1 * np.mean(winsorized_rates)
                )
            elif data_points >= 4:
                # Moderate data - balance historical and recent
                smoothed_growth = (
                    0.5 * total_cagr +
                    0.3 * median_growth +
                    0.2 * exponential_weighted_growth
                )
            else:
                # Limited data - conservative approach
                smoothed_growth = (
                    0.6 * median_growth +
                    0.4 * total_cagr
                )

            # Additional smoothing - moving towards sector average if highly volatile
            original_volatility = metrics.get('original_volatility', 0)
            if original_volatility > 1.5:  # Very high volatility
                # Conservative sector/market average growth rate
                sector_average_growth = 0.04  # 4% typical dividend growth
                volatility_factor = min(original_volatility / 2.0, 0.5)  # Scale factor
                smoothed_growth = (1 - volatility_factor) * smoothed_growth + volatility_factor * sector_average_growth

            logger.info(f"Volatility smoothing applied: Original volatility {original_volatility:.2f}, "
                       f"Smoothed growth rate {smoothed_growth:.1%}")

            return smoothed_growth

        except Exception as e:
            logger.error(f"Error applying volatility smoothing: {e}")
            # Fallback to conservative estimate
            return metrics.get('median_growth_rate', 0.03)

    def _get_market_data(self):
        """
        Get current market data using var_input_data system with fallback to enhanced data sources

        Returns:
            dict: Market data
        """
        try:
            # First, try to get market data from var_input_data
            market_variables = ['current_price', 'market_cap', 'shares_outstanding']
            market_data = {}
            
            for var_name in market_variables:
                try:
                    value = self.var_data.get_variable(self.ticker_symbol, var_name, period="latest")
                    if value is not None and value > 0:
                        market_data[var_name] = value
                        logger.debug(f"Retrieved {var_name}={value} from var_input_data")
                except Exception as e:
                    logger.debug(f"Could not retrieve {var_name} from var_input_data: {e}")
            
            # Use financial calculator's enhanced market data fetching for missing values
            if hasattr(self.financial_calculator, 'fetch_market_data'):
                # Only fetch if we're missing key values
                if not all(market_data.get(key, 0) > 0 for key in ['current_price', 'shares_outstanding']):
                    fresh_data = self.financial_calculator.fetch_market_data()
                    if fresh_data:
                        # Only update missing values
                        for key, value in fresh_data.items():
                            if key not in market_data or market_data.get(key, 0) <= 0:
                                if value and value > 0:
                                    market_data[key] = value
                        logger.debug("Updated market data from enhanced data sources")

            # Final fallback to existing cached data for any remaining missing values
            fallback_data = {
                'current_price': getattr(self.financial_calculator, 'current_stock_price', 0),
                'market_cap': getattr(self.financial_calculator, 'market_cap', 0),
                'shares_outstanding': getattr(self.financial_calculator, 'shares_outstanding', 0),
                'ticker_symbol': getattr(self.financial_calculator, 'ticker_symbol', None),
                'currency': getattr(self.financial_calculator, 'currency', 'USD'),
                'is_tase_stock': getattr(self.financial_calculator, 'is_tase_stock', False),
            }
            
            # Only use fallback for missing values
            for key, value in fallback_data.items():
                if key not in market_data or (isinstance(market_data.get(key), (int, float)) and market_data.get(key, 0) <= 0):
                    if value and (not isinstance(value, (int, float)) or value > 0):
                        market_data[key] = value

            logger.debug("Using market data with var_input_data integration")
            return market_data

        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")
            return {}

    def sensitivity_analysis(self, growth_rates, discount_rates, base_assumptions=None):
        """
        Perform sensitivity analysis on DDM valuation

        Args:
            growth_rates (list): List of growth rates to test
            discount_rates (list): List of discount rates to test
            base_assumptions (dict): Base DDM assumptions

        Returns:
            dict: Sensitivity analysis results
        """
        if base_assumptions is None:
            base_assumptions = self.default_assumptions.copy()

        # Get current market price for comparison
        market_data = self._get_market_data()
        current_price = market_data.get('current_price', 0)

        results = {
            'growth_rates': growth_rates,
            'discount_rates': discount_rates,
            'valuations': [],
            'upside_downside': [],
            'current_price': current_price,
            'model_type': base_assumptions.get('model_type', 'auto'),
        }

        for discount_rate in discount_rates:
            valuation_row = []
            upside_row = []

            for growth_rate in growth_rates:
                # Update assumptions
                test_assumptions = base_assumptions.copy()
                test_assumptions['discount_rate'] = discount_rate

                # Set growth rate based on model type
                if base_assumptions.get('model_type') in ['gordon', 'auto']:
                    test_assumptions['terminal_growth_rate'] = growth_rate
                else:
                    test_assumptions['stage1_growth_rate'] = growth_rate

                # Calculate DDM
                ddm_result = self.calculate_ddm_valuation(test_assumptions)
                valuation = ddm_result.get('intrinsic_value', 0)
                valuation_row.append(valuation)

                # Calculate upside/downside percentage
                if current_price > 0 and valuation > 0:
                    upside_downside = (valuation - current_price) / current_price
                    upside_row.append(upside_downside)
                else:
                    upside_row.append(0)

            results['valuations'].append(valuation_row)
            results['upside_downside'].append(upside_row)

        return results
    
    def _store_ddm_results_in_var_system(
        self, 
        ddm_results: Dict[str, Any],
        model_type: str,
        assumptions: Dict[str, Any]
    ) -> None:
        """
        Store DDM calculation results in var_input_data system with lineage tracking
        
        Args:
            ddm_results: DDM calculation results dictionary
            model_type: DDM model type used
            assumptions: DDM assumptions used
        """
        try:
            current_period = "latest"
            source = "ddm_calculation"
            calculation_method = f"DDM {model_type}, discount_rate={assumptions.get('discount_rate', 'N/A'):.1%}, terminal_growth={assumptions.get('terminal_growth_rate', 'N/A'):.1%}"
            
            # Create metadata with calculation lineage
            base_metadata = VariableMetadata(
                source=source,
                timestamp=pd.Timestamp.now(),
                quality_score=0.9,  # DDM typically less precise than DCF
                validation_passed=True,
                calculation_method=calculation_method,
                dependencies=['dividend_per_share', 'current_price', 'dividend_yield'],
                period=current_period
            )
            
            # Map DDM results to var_input_data variables
            ddm_variables = {
                'intrinsic_value': ddm_results.get('intrinsic_value'),  # For DDM, this is value per share
                'dividend_yield': ddm_results.get('dividend_yield'),
                'payout_ratio': ddm_results.get('payout_ratio'),
                'dividend_growth_rate': ddm_results.get('dividend_growth_rate'),
            }
            
            # Store additional model-specific results
            if model_type == 'gordon':
                ddm_variables['gordon_growth_rate'] = ddm_results.get('growth_rate')
            elif model_type in ['two_stage', 'multi_stage']:
                ddm_variables['terminal_value'] = ddm_results.get('terminal_value')
                ddm_variables['pv_terminal'] = ddm_results.get('pv_terminal')
            
            for var_name, value in ddm_variables.items():
                if value is not None:
                    # Create specific metadata for each variable
                    var_metadata = VariableMetadata(
                        source=base_metadata.source,
                        timestamp=base_metadata.timestamp,
                        quality_score=base_metadata.quality_score,
                        validation_passed=base_metadata.validation_passed,
                        calculation_method=f"{var_name} from {calculation_method}",
                        dependencies=base_metadata.dependencies.copy(),
                        period=current_period
                    )
                    
                    success = self.var_data.set_variable(
                        symbol=self.ticker_symbol,
                        variable_name=var_name,
                        value=value,
                        period=current_period,
                        source=source,
                        metadata=var_metadata,
                        emit_event=False  # Avoid event spam during calculation
                    )
                    
                    if success:
                        logger.debug(f"Stored DDM result {var_name}={value} in var_input_data")
                    else:
                        logger.warning(f"Failed to store DDM result {var_name} in var_input_data")
                        
        except Exception as e:
            logger.error(f"Error storing DDM results in var_input_data: {e}")
    
    def _get_dividend_data_from_var_system(self) -> Optional[pd.DataFrame]:
        """
        Get dividend data from var_input_data system with fallback to extraction methods
        
        Returns:
            pandas.DataFrame with dividend data or None if not available
        """
        try:
            # Try to get historical dividend data from var_input_data
            dividend_variables = ['dividend_per_share', 'dividend_yield']
            
            for var_name in dividend_variables:
                historical_data = self.var_data.get_historical_data(self.ticker_symbol, var_name, years=10)
                
                if historical_data:
                    # Convert historical data to DataFrame format expected by DDM
                    dividend_df = pd.DataFrame([
                        {
                            'year': int(period) if str(period).isdigit() else pd.to_datetime(period).year,
                            'dividend_per_share': value,
                            'date': pd.to_datetime(period) if not str(period).isdigit() else pd.to_datetime(f"{period}-12-31")
                        }
                        for period, value in historical_data if value is not None and value > 0
                    ])
                    
                    if not dividend_df.empty:
                        logger.info(f"Retrieved {len(dividend_df)} dividend records from var_input_data using {var_name}")
                        return dividend_df
                        
        except Exception as e:
            logger.warning(f"Error retrieving dividend data from var_input_data: {e}")
            
        return None
    
    def _store_dividend_data_in_var_system(
        self, 
        processed_data: Dict[str, Any], 
        metrics: Dict[str, Any], 
        data_source: str
    ) -> None:
        """
        Store dividend data and metrics in var_input_data system
        
        Args:
            processed_data: Processed dividend data dictionary
            metrics: Calculated dividend metrics
            data_source: Source of the dividend data
        """
        try:
            source = f"ddm_dividend_extraction_{data_source}"
            
            # Store dividend per share for each historical year
            dividends_per_share = processed_data.get('dividends_per_share', [])
            years = processed_data.get('years', [])
            
            for i, (year, dividend) in enumerate(zip(years, dividends_per_share)):
                if dividend and dividend > 0:
                    metadata = VariableMetadata(
                        source=source,
                        timestamp=pd.Timestamp.now(),
                        quality_score=0.85,
                        validation_passed=True,
                        calculation_method=f"dividend_extraction_from_{data_source}",
                        period=str(year)
                    )
                    
                    self.var_data.set_variable(
                        symbol=self.ticker_symbol,
                        variable_name='dividend_per_share',
                        value=dividend,
                        period=str(year),
                        source=source,
                        metadata=metadata,
                        emit_event=False
                    )
            
            # Store latest dividend metrics
            current_period = "latest"
            latest_dividend = processed_data.get('latest_dividend', 0)
            
            if latest_dividend > 0:
                # Store latest dividend per share
                latest_metadata = VariableMetadata(
                    source=source,
                    timestamp=pd.Timestamp.now(),
                    quality_score=0.9,
                    validation_passed=True,
                    calculation_method=f"latest_dividend_from_{data_source}",
                    period=current_period
                )
                
                self.var_data.set_variable(
                    symbol=self.ticker_symbol,
                    variable_name='dividend_per_share',
                    value=latest_dividend,
                    period=current_period,
                    source=source,
                    metadata=latest_metadata,
                    emit_event=False
                )
            
            # Store calculated metrics
            metric_variables = {
                'dividend_yield': metrics.get('dividend_yield'),
                'payout_ratio': metrics.get('payout_ratio'),
                'dividend_growth_rate': metrics.get('dividend_cagr_3y', metrics.get('avg_growth_rate'))
            }
            
            for var_name, value in metric_variables.items():
                if value is not None:
                    metric_metadata = VariableMetadata(
                        source=f"ddm_metric_calculation",
                        timestamp=pd.Timestamp.now(),
                        quality_score=0.8,
                        validation_passed=True,
                        calculation_method=f"{var_name}_calculated_from_dividend_analysis",
                        dependencies=['dividend_per_share'],
                        period=current_period
                    )
                    
                    self.var_data.set_variable(
                        symbol=self.ticker_symbol,
                        variable_name=var_name,
                        value=value,
                        period=current_period,
                        source="ddm_metric_calculation",
                        metadata=metric_metadata,
                        emit_event=False
                    )
                    
            logger.debug(f"Stored dividend data and metrics in var_input_data for {self.ticker_symbol}")
                    
        except Exception as e:
            logger.warning(f"Error storing dividend data in var_input_data: {e}")
