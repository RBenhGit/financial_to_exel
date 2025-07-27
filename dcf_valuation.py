"""
DCF (Discounted Cash Flow) Valuation Module
==========================================

This module provides comprehensive DCF valuation capabilities for financial analysis,
including multi-stage growth projections, terminal value calculations, and sensitivity analysis.

Key Features
------------
- Multiple Free Cash Flow types support (FCFE, FCFF, LFCF)
- Multi-stage growth modeling (years 1-5, 5-10, terminal)
- Automated historical growth rate calculation
- Terminal value calculation using Gordon Growth Model
- Comprehensive sensitivity analysis with market price comparison
- Configurable assumptions with intelligent defaults

Classes
-------
DCFValuator
    Main class for performing DCF valuations with sensitivity analysis

Usage Example
-------------
>>> from dcf_valuation import DCFValuator
>>> from financial_calculations import FinancialCalculator
>>>
>>> # Initialize with financial data
>>> calc = FinancialCalculator('AAPL')
>>> dcf = DCFValuator(calc)
>>>
>>> # Basic DCF calculation
>>> result = dcf.calculate_dcf_projections()
>>> print(f"Intrinsic Value: ${result['value_per_share']:.2f}")
>>>
>>> # Sensitivity analysis
>>> discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
>>> growth_rates = [0.03, 0.05, 0.07, 0.09, 0.11]
>>> sensitivity = dcf.sensitivity_analysis(discount_rates, growth_rates)

Financial Theory
----------------
The DCF model values a company based on the present value of its projected future
cash flows. The model uses the following key components:

1. **Free Cash Flow Projection**: Historical cash flows are analyzed to project
   future cash flows using multi-stage growth assumptions.

2. **Terminal Value**: The value beyond the explicit projection period is
   calculated using the Gordon Growth Model: TV = FCF_terminal × (1 + g) / (r - g)

3. **Present Value Calculation**: All future cash flows and terminal value are
   discounted to present value using the cost of equity or WACC.

4. **Equity Value**: Enterprise value minus net debt equals equity value, which
   is divided by shares outstanding to get value per share.

Configuration
-------------
DCF assumptions are loaded from config.py and can be overridden:
- discount_rate: Cost of equity/WACC (typically 8-12%)
- terminal_growth_rate: Long-term growth rate (typically 2-4%)
- growth_rate_yr1_5: Near-term growth rate
- growth_rate_yr5_10: Medium-term growth rate
- projection_years: Explicit projection period (typically 10 years)

Notes
-----
- All monetary values maintain the same units as input financial data
- The module handles negative cash flows with appropriate growth logic
- Historical growth rates use compound annual growth rate (CAGR) methodology
- Sensitivity analysis helps assess valuation robustness across scenarios
"""

import numpy as np
import pandas as pd
import logging
from functools import lru_cache
from scipy import stats
from typing import Dict, Any, Optional, List, Union, Tuple
from config import get_dcf_config

logger = logging.getLogger(__name__)


class DCFValuator:
    """
    Handles DCF valuation calculations and projections
    """

    def __init__(self, financial_calculator: Any) -> None:
        """
        Initialize DCF valuator with financial calculator

        Args:
            financial_calculator: FinancialCalculator instance with loaded data
        """
        self.financial_calculator = financial_calculator
        # Load default assumptions from configuration
        dcf_config = get_dcf_config()
        self.default_assumptions = {
            'discount_rate': dcf_config.default_discount_rate,
            'terminal_growth_rate': dcf_config.default_terminal_growth_rate,
            'growth_rate_yr1_5': dcf_config.default_growth_rate_yr1_5,
            'growth_rate_yr5_10': dcf_config.default_growth_rate_yr5_10,
            'projection_years': dcf_config.default_projection_years,
            'terminal_method': dcf_config.default_terminal_method,
            'fcf_type': dcf_config.default_fcf_type,
        }

    def calculate_dcf_projections(
        self, assumptions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive DCF (Discounted Cash Flow) projections and valuation.

        This method performs a complete DCF analysis including historical growth calculation,
        future cash flow projections, terminal value calculation, and present value computation
        to determine the intrinsic value per share.

        Parameters
        ----------
        assumptions : dict, optional
            Dictionary containing DCF assumptions. If None, uses default configuration.

            Key parameters:
            - discount_rate : float
                Cost of equity/WACC for discounting future cash flows (default: from config)
            - terminal_growth_rate : float
                Perpetual growth rate for terminal value (default: from config)
            - growth_rate_yr1_5 : float
                Expected growth rate for years 1-5 (default: from config)
            - growth_rate_yr5_10 : float
                Expected growth rate for years 5-10 (default: from config)
            - projection_years : int
                Number of years to project explicitly (default: 10)
            - terminal_method : str
                Terminal value method: 'gordon_growth' or 'exit_multiple'
            - fcf_type : str
                Free cash flow type: 'FCFE', 'FCFF', or 'LFCF' (default: 'FCFE')

        Returns
        -------
        dict
            Comprehensive DCF analysis results containing:

            - value_per_share : float
                Calculated intrinsic value per share
            - enterprise_value : float
                Total enterprise value
            - equity_value : float
                Total equity value (enterprise value - net debt)
            - projected_fcf : list
                Year-by-year projected free cash flows
            - pv_fcf : list
                Present value of each projected cash flow
            - terminal_value : float
                Calculated terminal value
            - pv_terminal : float
                Present value of terminal value
            - assumptions_used : dict
                Final assumptions used in calculation
            - historical_growth : dict
                Historical growth rates calculated from past data
            - summary : dict
                Key metrics and ratios

        Examples
        --------
        Basic DCF calculation with default assumptions:

        >>> dcf_valuator = DCFValuator(financial_calculator)
        >>> result = dcf_valuator.calculate_dcf_projections()
        >>> print(f"Intrinsic value: ${result['value_per_share']:.2f}")

        Custom DCF with specific assumptions:

        >>> assumptions = {
        ...     'discount_rate': 0.10,
        ...     'terminal_growth_rate': 0.025,
        ...     'growth_rate_yr1_5': 0.15,
        ...     'projection_years': 10
        ... }
        >>> result = dcf_valuator.calculate_dcf_projections(assumptions)
        >>> print(f"Enterprise Value: ${result['enterprise_value']:,.0f}")

        Notes
        -----
        - The method automatically selects the best available FCF type (FCFE > FCFF > LFCF)
        - Historical growth rates are calculated using compound annual growth rate (CAGR)
        - Terminal value calculation defaults to Gordon Growth Model
        - All monetary values are returned in the same units as input financial data
        - Negative or zero cash flows are handled with special logic for growth calculations
        """
        if assumptions is None:
            assumptions = self.default_assumptions.copy()

        try:
            # Get FCF data (use selected FCF type, default to FCFE)
            fcf_type = assumptions.get('fcf_type', 'FCFE')
            fcf_values = self.financial_calculator.fcf_results.get(fcf_type, [])

            # If FCFE is not available, try FCFF as fallback, then LFCF
            if not fcf_values:
                for fallback_type in ['FCFF', 'LFCF']:
                    fallback_values = self.financial_calculator.fcf_results.get(fallback_type, [])
                    if fallback_values:
                        fcf_type = fallback_type
                        fcf_values = fallback_values
                        logger.info(f"FCFE not available, using {fcf_type} as fallback")
                        break

            if not fcf_values:
                logger.error(f"No {fcf_type} data available for DCF calculation")
                return {}

            # Calculate historical growth rates (cache-friendly)
            historical_growth = self._calculate_historical_growth_rates(tuple(fcf_values))

            # Project future FCF
            projections = self._project_future_fcf(fcf_values, assumptions, historical_growth)

            # Calculate terminal value
            terminal_value = self._calculate_terminal_value(projections, assumptions)

            # Calculate present values
            pv_fcf = self._calculate_present_values(
                projections['projected_fcf'], assumptions['discount_rate']
            )
            pv_terminal = terminal_value / (
                (1 + assumptions['discount_rate']) ** assumptions['projection_years']
            )

            # DEBUG: Additional validation of terminal value calculation
            logger.info(f"DEBUG PV TERMINAL:")
            logger.info(f"  Terminal value (undiscounted): {terminal_value/1000000:.2f}M")
            logger.info(
                f"  Discount factor: {((1 + assumptions['discount_rate']) ** assumptions['projection_years']):.3f}"
            )
            logger.info(f"  PV terminal: {pv_terminal/1000000:.3f}M")

            # Validate terminal value is reasonable
            if (
                terminal_value > 0 and pv_terminal < terminal_value / 1000
            ):  # PV should be much smaller than undiscounted
                logger.info("Terminal value present value calculation appears correct")
            else:
                logger.warning(
                    f"Terminal value calculation may be incorrect: undiscounted={terminal_value:.2f}, pv={pv_terminal:.2f}"
                )

            # Debug: Log projection values
            logger.info(f"Projection Details:")
            logger.info(f"  Base FCF: ${projections.get('base_fcf', 0)/1000000:.1f}M")
            logger.info(
                f"  Projected FCF: {[f'${v/1000000:.1f}M' for v in projections.get('projected_fcf', [])]}"
            )
            logger.info(f"  Terminal Value: ${terminal_value/1000000:.1f}M")
            logger.info(f"  PV of FCF: {[f'${v/1000000:.1f}M' for v in pv_fcf]}")
            logger.info(f"  PV Terminal: ${pv_terminal/1000000:.1f}M")

            # Get market data if available
            market_data = self._get_market_data()

            # Calculate enterprise and equity value based on FCF type
            if fcf_type == 'FCFE':
                # FCFE is already equity value - no need for enterprise value calculation
                # DEBUG: Add detailed logging to track the summation bug
                sum_pv_fcf = sum(pv_fcf)
                logger.info(f"DEBUG: Individual PV values: {[f'{v/1000000:.2f}M' for v in pv_fcf]}")
                logger.info(f"DEBUG: sum(pv_fcf) = {sum_pv_fcf/1000000:.2f}M")
                logger.info(f"DEBUG: pv_terminal = {pv_terminal/1000000:.3f}M")
                logger.info(f"DEBUG: sum_pv_fcf type: {type(sum_pv_fcf)}, value: {sum_pv_fcf}")
                logger.info(f"DEBUG: pv_terminal type: {type(pv_terminal)}, value: {pv_terminal}")

                # CRITICAL FIX: Ensure proper calculation without precision loss
                equity_value = float(sum_pv_fcf) + float(pv_terminal)
                logger.info(
                    f"DEBUG: equity_value = {sum_pv_fcf/1000000:.2f}M + {pv_terminal/1000000:.3f}M = {equity_value/1000000:.2f}M"
                )
                logger.info(
                    f"DEBUG: equity_value type: {type(equity_value)}, value: {equity_value}"
                )

                # Additional validation
                if equity_value < 100000:  # Less than 100B (clearly wrong for Microsoft)
                    logger.error(
                        f"CRITICAL ERROR: Equity value {equity_value/1000000:.2f}M is suspiciously low!"
                    )
                    logger.error(f"Expected: >1,000,000M for large cap companies like MSFT")
                    logger.error(
                        f"Sum components: {sum_pv_fcf} + {pv_terminal} = {sum_pv_fcf + pv_terminal}"
                    )
                else:
                    logger.info(
                        f"Equity value validation: {equity_value/1000000:.2f}M appears reasonable"
                    )

                enterprise_value = None  # Not applicable for FCFE
                logger.info(
                    f"FCFE Calculation: PV of FCF = ${sum_pv_fcf/1000000:.1f}M, PV Terminal = ${pv_terminal/1000000:.1f}M"
                )
            else:
                # FCFF and LFCF represent enterprise value - need to convert to equity
                enterprise_value = sum(pv_fcf) + pv_terminal

                # Get net debt for enterprise to equity conversion
                net_debt = self._get_net_debt()
                equity_value = enterprise_value - net_debt
                logger.info(
                    f"{fcf_type} Calculation: Enterprise Value = ${enterprise_value/1000000:.1f}M, Net Debt = ${net_debt/1000000:.1f}M"
                )

            # Calculate per-share values - require valid shares outstanding
            shares_outstanding = market_data.get('shares_outstanding', 0)

            # Calculate shares outstanding from market cap if not directly available
            if shares_outstanding <= 0:
                current_price = market_data.get('current_price', 0)
                market_cap = market_data.get('market_cap', 0)

                if current_price > 0 and market_cap > 0:
                    shares_outstanding = market_cap / current_price
                    logger.info(
                        f"Calculated shares outstanding from market data: {shares_outstanding/1000000:.1f}M shares"
                    )
                else:
                    # No fallback - DCF calculation cannot proceed without shares outstanding
                    logger.error(
                        "Cannot determine shares outstanding: no direct data or market cap/price available"
                    )
                    return {
                        'error': 'shares_outstanding_unavailable',
                        'error_message': 'Shares outstanding cannot be determined. Please ensure ticker symbol is correct and market data is available.',
                        'fcf_type': fcf_type,
                        'market_data': market_data,
                    }

            # Validate shares outstanding is reasonable
            if shares_outstanding <= 0:
                logger.error(f"Invalid shares outstanding: {shares_outstanding}")
                return {
                    'error': 'invalid_shares_outstanding',
                    'error_message': f'Invalid shares outstanding value: {shares_outstanding}',
                    'fcf_type': fcf_type,
                    'market_data': market_data,
                }

            # Handle currency-specific per-share calculations
            is_tase_stock = getattr(self.financial_calculator, 'is_tase_stock', False)
            currency = getattr(self.financial_calculator, 'currency', 'USD')

            if is_tase_stock:
                # For TASE stocks: equity_value is in millions ILS, need per-share in Agorot (ILA)
                # 1 ILS = 100 ILA, so millions ILS to total ILA = millions * 1,000,000 * 100
                equity_value_total_agorot = (
                    equity_value * 1000000 * 100
                )  # Convert millions ILS to total Agorot
                value_per_share = (
                    equity_value_total_agorot / shares_outstanding
                )  # Per share in Agorot

                # Also calculate per-share in Shekels for reference
                value_per_share_shekels = value_per_share / 100.0

                logger.info(f"TASE DCF Calculation Summary:")
                logger.info(f"  FCF Type: {fcf_type}")
                logger.info(
                    f"  Enterprise Value: {enterprise_value:.1f}M ILS"
                    if enterprise_value
                    else "N/A (FCFE)"
                )
                logger.info(
                    f"  Net Debt: {self._get_net_debt():.1f}M ILS"
                    if fcf_type != 'FCFE'
                    else "N/A (FCFE)"
                )
                logger.info(f"  Equity Value: {equity_value:.1f}M ILS")
                logger.info(f"  Shares Outstanding: {shares_outstanding/1000000:.1f}M")
                logger.info(
                    f"  Value per Share: {value_per_share:.0f} Agorot ({value_per_share_shekels:.2f} ILS)"
                )
            else:
                # For non-TASE stocks: standard USD/other currency calculation
                equity_value_actual_currency = (
                    equity_value * 1000000
                )  # Convert millions to actual currency units
                value_per_share = equity_value_actual_currency / shares_outstanding

                logger.info(f"DCF Calculation Summary:")
                logger.info(f"  FCF Type: {fcf_type}")
                logger.info(
                    f"  Enterprise Value: {enterprise_value/1000000:.1f}M {currency}"
                    if enterprise_value
                    else "N/A (FCFE)"
                )
                logger.info(
                    f"  Net Debt: {self._get_net_debt()/1000000:.1f}M {currency}"
                    if fcf_type != 'FCFE'
                    else "N/A (FCFE)"
                )
                logger.info(f"  Equity Value: {equity_value/1000000:.1f}M {currency}")
                logger.info(
                    f"  Equity Value (actual): {equity_value_actual_currency/1000000:.1f}M {currency}"
                )
                logger.info(f"  Shares Outstanding: {shares_outstanding/1000000:.1f}M")
                logger.info(f"  Value per Share: {value_per_share:.2f} {currency}")

            # Prepare return dictionary with currency information
            result = {
                'assumptions': assumptions,
                'fcf_type': fcf_type,
                'historical_growth': historical_growth,
                'projections': projections,
                'terminal_value': terminal_value,
                'pv_fcf': pv_fcf,
                'pv_terminal': pv_terminal,
                'enterprise_value': (
                    enterprise_value if enterprise_value is not None else equity_value
                ),  # For FCFE, show equity value as enterprise value
                'equity_value': equity_value,
                'value_per_share': value_per_share,
                'market_data': market_data,
                'net_debt': self._get_net_debt() if fcf_type != 'FCFE' else 0,
                'years': list(range(1, assumptions['projection_years'] + 1)),
                'currency': currency,
                'is_tase_stock': is_tase_stock,
            }

            # Add TASE-specific information
            if is_tase_stock and value_per_share:
                result.update(
                    {
                        'value_per_share_agorot': value_per_share,
                        'value_per_share_shekels': value_per_share / 100.0,
                        'currency_note': 'Values in millions ILS, per-share in Agorot (ILA)',
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error in DCF calculation: {e}")
            return {}

    @lru_cache(maxsize=128)
    def _calculate_historical_growth_rates(self, fcf_values: tuple) -> Dict[str, float]:
        """
        Calculate historical growth rates from FCF data

        Args:
            fcf_values (list): Historical FCF values

        Returns:
            dict: Historical growth rates
        """
        growth_rates = {}

        try:
            # Calculate growth rates for different periods
            periods = [1, 3, 5]

            for period in periods:
                if len(fcf_values) >= period + 1:
                    start_value = fcf_values[-(period + 1)]
                    end_value = fcf_values[-1]

                    if start_value != 0:
                        # Calculate CAGR
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1

                        # Handle negative values
                        if end_value < 0 and start_value > 0:
                            growth_rate = -growth_rate
                        elif end_value > 0 and start_value < 0:
                            growth_rate = abs(growth_rate)

                        growth_rates[f"{period}Y_CAGR"] = growth_rate
                    else:
                        growth_rates[f"{period}Y_CAGR"] = 0

            # Calculate average growth rate for projections
            if fcf_values and len(fcf_values) >= 3:
                avg_growth = growth_rates.get('3Y_CAGR', 0.05)  # Default 5%
                growth_rates['projection_growth'] = min(
                    max(avg_growth, -0.20), 0.30
                )  # Cap between -20% and 30%
            else:
                growth_rates['projection_growth'] = 0.05

        except Exception as e:
            logger.error(f"Error calculating historical growth rates: {e}")
            growth_rates = {'projection_growth': 0.05}

        return growth_rates

    def _project_future_fcf(
        self,
        fcf_values: List[float],
        assumptions: Dict[str, Any],
        historical_growth: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Project future FCF based on assumptions and historical data

        Args:
            fcf_values (list): Historical FCF values
            assumptions (dict): DCF assumptions
            historical_growth (dict): Historical growth rates

        Returns:
            dict: Projected FCF values and growth rates
        """
        if not fcf_values:
            return {'projected_fcf': [], 'growth_rates': []}

        # Get base FCF (latest year)
        base_fcf = fcf_values[-1] if fcf_values else 0

        # DEBUG: Log base FCF information
        logger.info(f"DEBUG FCF PROJECTION:")
        logger.info(f"  Historical FCF values: {[f'{v/1000000:.1f}M' for v in fcf_values]}")
        logger.info(f"  Base FCF (latest): {base_fcf/1000000:.2f}M")
        logger.info(f"  Base FCF raw value: {base_fcf}")

        # Use historical growth if available, otherwise use assumptions
        growth_yr1_5 = assumptions.get(
            'growth_rate_yr1_5', historical_growth.get('projection_growth', 0.05)
        )
        growth_yr5_10 = assumptions.get('growth_rate_yr5_10', 0.03)

        projected_fcf = []
        growth_rates = []

        # Project FCF for specified years
        current_fcf = base_fcf
        for year in range(1, assumptions['projection_years'] + 1):
            # Use different growth rates for different periods
            if year <= 5:
                growth_rate = growth_yr1_5
            else:
                growth_rate = growth_yr5_10

            current_fcf = current_fcf * (1 + growth_rate)
            projected_fcf.append(current_fcf)
            growth_rates.append(growth_rate)

        return {'projected_fcf': projected_fcf, 'growth_rates': growth_rates, 'base_fcf': base_fcf}

    def _calculate_terminal_value(
        self, projections: Dict[str, Any], assumptions: Dict[str, Any]
    ) -> float:
        """
        Calculate terminal value using perpetual growth model

        Args:
            projections (dict): FCF projections
            assumptions (dict): DCF assumptions

        Returns:
            float: Terminal value
        """
        try:
            if not projections['projected_fcf']:
                return 0

            # Get final year FCF
            final_fcf = projections['projected_fcf'][-1]

            # DEBUG: Add detailed logging to track terminal value calculation bug
            logger.info(f"DEBUG TERMINAL VALUE:")
            logger.info(f"  Final year FCF: {final_fcf:.2f} (type: {type(final_fcf)})")
            logger.info(f"  Terminal growth rate: {assumptions['terminal_growth_rate']:.3f}")
            logger.info(f"  Discount rate: {assumptions['discount_rate']:.3f}")

            # Calculate terminal FCF (growing at terminal growth rate)
            terminal_fcf = final_fcf * (1 + assumptions['terminal_growth_rate'])
            logger.info(f"  Terminal FCF (Year 11): {terminal_fcf:.2f}")

            # Calculate terminal value using Gordon Growth Model
            denominator = assumptions['discount_rate'] - assumptions['terminal_growth_rate']
            terminal_value = terminal_fcf / denominator
            logger.info(f"  Denominator: {denominator:.3f}")
            logger.info(f"  Terminal value (undiscounted): {terminal_value:.2f}")

            return terminal_value

        except Exception as e:
            logger.error(f"Error calculating terminal value: {e}")
            return 0

    def _calculate_present_values(
        self, future_cash_flows: List[float], discount_rate: float
    ) -> List[float]:
        """
        Calculate present values of future cash flows

        Args:
            future_cash_flows (list): Future cash flow projections
            discount_rate (float): Discount rate

        Returns:
            list: Present values of cash flows
        """
        present_values = []

        for year, cash_flow in enumerate(future_cash_flows, 1):
            pv = cash_flow / ((1 + discount_rate) ** year)
            present_values.append(pv)

        return present_values

    def _get_market_data(self) -> Dict[str, Any]:
        """
        Get market data for the company using improved fetching method

        Returns:
            dict: Market data (shares outstanding, current price, etc.)
        """
        # Default values - no fallback for shares outstanding
        market_data = {
            'shares_outstanding': 0,  # No default - must be acquired or calculated
            'current_price': 0,  # No default price (0 means unavailable)
            'market_cap': 0,
            'ticker_symbol': None,
            'currency': 'USD',
            'is_tase_stock': False,
        }

        try:
            # Use financial calculator's market data if available
            if (
                hasattr(self.financial_calculator, 'ticker_symbol')
                and self.financial_calculator.ticker_symbol
            ):
                # Try to fetch fresh market data
                fresh_data = self.financial_calculator.fetch_market_data()

                if fresh_data:
                    market_data.update(fresh_data)
                else:
                    # Fall back to any existing data
                    market_data.update(
                        {
                            'shares_outstanding': getattr(
                                self.financial_calculator, 'shares_outstanding', 1000000
                            ),
                            'current_price': getattr(
                                self.financial_calculator, 'current_stock_price', 0
                            ),
                            'market_cap': getattr(self.financial_calculator, 'market_cap', 0),
                            'ticker_symbol': self.financial_calculator.ticker_symbol,
                            'currency': getattr(self.financial_calculator, 'currency', 'USD'),
                            'is_tase_stock': getattr(
                                self.financial_calculator, 'is_tase_stock', False
                            ),
                        }
                    )

        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")

        return market_data

    def _get_net_debt(self) -> float:
        """
        Calculate net debt from balance sheet data for enterprise to equity value conversion

        Returns:
            float: Net debt (total debt - cash and equivalents) in millions
        """
        try:
            # Get balance sheet data from financial calculator
            balance_sheet_data = self.financial_calculator.financial_data.get('Balance Sheet', {})

            if not balance_sheet_data:
                logger.warning("No balance sheet data available for net debt calculation")
                return 0

            # Extract financial metrics (values should already be in millions)
            total_debt = 0
            cash_and_equivalents = 0

            # Look for debt items (common names in financial statements)
            debt_keywords = [
                'total debt',
                'total_debt',
                'debt',
                'long term debt',
                'long_term_debt',
                'long-term debt',
                'short term debt',
                'short_term_debt',
                'short-term debt',
                'borrowings',
                'total borrowings',
                'notes payable',
                'bonds payable',
            ]

            # Look for cash items
            cash_keywords = [
                'cash',
                'cash and cash equivalents',
                'cash_and_cash_equivalents',
                'cash and equivalents',
                'total cash',
                'liquid assets',
            ]

            # Search for debt in balance sheet data
            for year_data in balance_sheet_data.values():
                if isinstance(year_data, dict):
                    # Find debt items
                    for key, value in year_data.items():
                        if isinstance(key, str):
                            key_lower = key.lower().strip()

                            # Check for debt
                            for debt_keyword in debt_keywords:
                                if debt_keyword in key_lower and isinstance(value, (int, float)):
                                    total_debt = max(
                                        total_debt, abs(value)
                                    )  # Take the latest/largest debt value
                                    break

                            # Check for cash
                            for cash_keyword in cash_keywords:
                                if cash_keyword in key_lower and isinstance(value, (int, float)):
                                    cash_and_equivalents = max(
                                        cash_and_equivalents, abs(value)
                                    )  # Take the latest/largest cash value
                                    break

            # Calculate net debt
            net_debt = total_debt - cash_and_equivalents

            logger.info(
                f"Net debt calculation: Total Debt=${total_debt:.1f}M, Cash=${cash_and_equivalents:.1f}M, Net Debt=${net_debt:.1f}M"
            )

            return net_debt

        except Exception as e:
            logger.error(f"Error calculating net debt: {e}")
            return 0  # Default to zero net debt if calculation fails

    def sensitivity_analysis(
        self,
        discount_rates: List[float],
        growth_rates: List[float],
        base_assumptions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive sensitivity analysis on DCF valuation.

        This method tests the impact of varying discount rates and growth rates on
        the calculated intrinsic value, providing insights into valuation sensitivity
        and risk assessment relative to current market price.

        Parameters
        ----------
        discount_rates : list of float
            List of discount rates (cost of equity/WACC) to test.
            Typically ranges from -2% to +2% around base assumption.
            Example: [0.08, 0.09, 0.10, 0.11, 0.12]

        growth_rates : list of float
            List of growth rates to test for FCF projections.
            Applied to the primary growth rate parameter (growth_rate_yr1_5).
            Example: [0.03, 0.05, 0.07, 0.09, 0.11]

        base_assumptions : dict, optional
            Base DCF assumptions to use as starting point. If None, uses
            the instance's default assumptions. Only discount_rate and
            growth_rate_yr1_5 are varied; other assumptions remain constant.

        Returns
        -------
        dict
            Sensitivity analysis results containing:

            - discount_rates : list
                Copy of input discount rates tested
            - terminal_growth_rates : list
                Copy of input growth rates tested (maintains compatibility)
            - valuations : list of list
                2D matrix of calculated valuations [discount_rate][growth_rate]
            - upside_downside : list of list
                2D matrix of upside/downside percentages vs current market price
            - current_price : float
                Current market price used for upside/downside calculations

        Examples
        --------
        Basic sensitivity analysis:

        >>> discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        >>> growth_rates = [0.03, 0.05, 0.07, 0.09, 0.11]
        >>> sensitivity = dcf_valuator.sensitivity_analysis(discount_rates, growth_rates)
        >>> print(f"Base case valuation range: ${min(min(row) for row in sensitivity['valuations']):.2f} - ${max(max(row) for row in sensitivity['valuations']):.2f}")

        Custom sensitivity with specific assumptions:

        >>> base_assumptions = {'terminal_growth_rate': 0.025, 'projection_years': 10}
        >>> sensitivity = dcf_valuator.sensitivity_analysis(
        ...     discount_rates=[0.09, 0.10, 0.11],
        ...     growth_rates=[0.05, 0.07, 0.09],
        ...     base_assumptions=base_assumptions
        ... )
        >>> upside_matrix = sensitivity['upside_downside']
        >>> print(f"Maximum upside: {max(max(row) for row in upside_matrix):.1%}")

        Notes
        -----
        - Results are particularly useful for creating sensitivity tables and heatmaps
        - Upside/downside calculations require valid current market price (> 0)
        - If market price is unavailable, upside_downside values will be 0
        - Growth rates are applied to years 1-5; years 5-10 use separate assumption
        - Terminal growth rate and other parameters remain constant during analysis
        """
        if base_assumptions is None:
            base_assumptions = self.default_assumptions.copy()

        # Get current market price for comparison
        market_data = self._get_market_data()
        current_price = market_data.get('current_price', 0)

        results = {
            'discount_rates': discount_rates,
            'terminal_growth_rates': growth_rates,  # Keep same key for compatibility with heatmap
            'valuations': [],
            'upside_downside': [],
            'current_price': current_price,
        }

        for discount_rate in discount_rates:
            valuation_row = []
            upside_row = []

            for growth_rate in growth_rates:
                # Update assumptions
                test_assumptions = base_assumptions.copy()
                test_assumptions['discount_rate'] = discount_rate
                test_assumptions['growth_rate_yr1_5'] = growth_rate  # Update main growth rate

                # Calculate DCF
                dcf_result = self.calculate_dcf_projections(test_assumptions)
                valuation = dcf_result.get('value_per_share', 0)
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
