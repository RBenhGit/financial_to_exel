"""
DCF Valuation Module

This module contains DCF (Discounted Cash Flow) valuation logic and calculations.
"""

import numpy as np
import pandas as pd
import logging
from scipy import stats
from config import get_dcf_config

logger = logging.getLogger(__name__)

class DCFValuator:
    """
    Handles DCF valuation calculations and projections
    """
    
    def __init__(self, financial_calculator):
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
            'fcf_type': dcf_config.default_fcf_type
        }
    
    def calculate_dcf_projections(self, assumptions=None):
        """
        Calculate DCF projections and valuation
        
        Args:
            assumptions (dict): DCF assumptions (discount rate, growth rates, etc.)
            
        Returns:
            dict: DCF analysis results
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
            
            # Calculate historical growth rates
            historical_growth = self._calculate_historical_growth_rates(fcf_values)
            
            # Project future FCF
            projections = self._project_future_fcf(fcf_values, assumptions, historical_growth)
            
            # Calculate terminal value
            terminal_value = self._calculate_terminal_value(projections, assumptions)
            
            # Calculate present values
            pv_fcf = self._calculate_present_values(projections['projected_fcf'], assumptions['discount_rate'])
            pv_terminal = terminal_value / ((1 + assumptions['discount_rate']) ** assumptions['projection_years'])
            
            # Debug: Log projection values
            logger.info(f"Projection Details:")
            logger.info(f"  Base FCF: ${projections.get('base_fcf', 0)/1000000:.1f}M")
            logger.info(f"  Projected FCF: {[f'${v/1000000:.1f}M' for v in projections.get('projected_fcf', [])]}")
            logger.info(f"  Terminal Value: ${terminal_value/1000000:.1f}M")
            logger.info(f"  PV of FCF: {[f'${v/1000000:.1f}M' for v in pv_fcf]}")
            logger.info(f"  PV Terminal: ${pv_terminal/1000000:.1f}M")
            
            # Get market data if available
            market_data = self._get_market_data()
            
            # Calculate enterprise and equity value based on FCF type
            if fcf_type == 'FCFE':
                # FCFE is already equity value - no need for enterprise value calculation
                equity_value = sum(pv_fcf) + pv_terminal
                enterprise_value = None  # Not applicable for FCFE
                logger.info(f"FCFE Calculation: PV of FCF = ${sum(pv_fcf)/1000000:.1f}M, PV Terminal = ${pv_terminal/1000000:.1f}M")
            else:
                # FCFF and LFCF represent enterprise value - need to convert to equity
                enterprise_value = sum(pv_fcf) + pv_terminal
                
                # Get net debt for enterprise to equity conversion
                net_debt = self._get_net_debt()
                equity_value = enterprise_value - net_debt
                logger.info(f"{fcf_type} Calculation: Enterprise Value = ${enterprise_value/1000000:.1f}M, Net Debt = ${net_debt/1000000:.1f}M")
            
            # Calculate per-share values - require valid shares outstanding
            shares_outstanding = market_data.get('shares_outstanding', 0)
            
            # Calculate shares outstanding from market cap if not directly available
            if shares_outstanding <= 0:
                current_price = market_data.get('current_price', 0)
                market_cap = market_data.get('market_cap', 0)
                
                if current_price > 0 and market_cap > 0:
                    shares_outstanding = market_cap / current_price
                    logger.info(f"Calculated shares outstanding from market data: {shares_outstanding/1000000:.1f}M shares")
                else:
                    # No fallback - DCF calculation cannot proceed without shares outstanding
                    logger.error("Cannot determine shares outstanding: no direct data or market cap/price available")
                    return {
                        'error': 'shares_outstanding_unavailable',
                        'error_message': 'Shares outstanding cannot be determined. Please ensure ticker symbol is correct and market data is available.',
                        'fcf_type': fcf_type,
                        'market_data': market_data
                    }
            
            # Validate shares outstanding is reasonable
            if shares_outstanding <= 0:
                logger.error(f"Invalid shares outstanding: {shares_outstanding}")
                return {
                    'error': 'invalid_shares_outstanding',
                    'error_message': f'Invalid shares outstanding value: {shares_outstanding}',
                    'fcf_type': fcf_type,
                    'market_data': market_data
                }
            
            # Convert equity value from millions to actual dollars for per-share calculation
            # equity_value is in millions, shares_outstanding is in actual count
            equity_value_actual_dollars = equity_value * 1000000  # Convert millions to actual dollars
            value_per_share = equity_value_actual_dollars / shares_outstanding
            
            # Log calculation details for debugging
            logger.info(f"DCF Calculation Summary:")
            logger.info(f"  FCF Type: {fcf_type}")
            logger.info(f"  Enterprise Value: ${enterprise_value/1000000:.1f}M" if enterprise_value else "N/A (FCFE)")
            logger.info(f"  Net Debt: ${self._get_net_debt()/1000000:.1f}M" if fcf_type != 'FCFE' else "N/A (FCFE)")
            logger.info(f"  Equity Value: ${equity_value/1000000:.1f}M")
            logger.info(f"  Equity Value (actual $): ${equity_value_actual_dollars/1000000000:.1f}B")
            logger.info(f"  Shares Outstanding: {shares_outstanding/1000000:.1f}M")
            logger.info(f"  Value per Share: ${value_per_share:.2f}")
            
            return {
                'assumptions': assumptions,
                'fcf_type': fcf_type,
                'historical_growth': historical_growth,
                'projections': projections,
                'terminal_value': terminal_value,
                'pv_fcf': pv_fcf,
                'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value if enterprise_value is not None else equity_value,  # For FCFE, show equity value as enterprise value
                'equity_value': equity_value,
                'value_per_share': value_per_share,
                'market_data': market_data,
                'net_debt': self._get_net_debt() if fcf_type != 'FCFE' else 0,
                'years': list(range(1, assumptions['projection_years'] + 1))
            }
            
        except Exception as e:
            logger.error(f"Error in DCF calculation: {e}")
            return {}
    
    def _calculate_historical_growth_rates(self, fcf_values):
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
                growth_rates['projection_growth'] = min(max(avg_growth, -0.20), 0.30)  # Cap between -20% and 30%
            else:
                growth_rates['projection_growth'] = 0.05
                
        except Exception as e:
            logger.error(f"Error calculating historical growth rates: {e}")
            growth_rates = {'projection_growth': 0.05}
            
        return growth_rates
    
    def _project_future_fcf(self, fcf_values, assumptions, historical_growth):
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
        
        # Use historical growth if available, otherwise use assumptions
        growth_yr1_5 = assumptions.get('growth_rate_yr1_5', historical_growth.get('projection_growth', 0.05))
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
        
        return {
            'projected_fcf': projected_fcf,
            'growth_rates': growth_rates,
            'base_fcf': base_fcf
        }
    
    def _calculate_terminal_value(self, projections, assumptions):
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
            
            # Calculate terminal FCF (growing at terminal growth rate)
            terminal_fcf = final_fcf * (1 + assumptions['terminal_growth_rate'])
            
            # Calculate terminal value using Gordon Growth Model
            terminal_value = terminal_fcf / (assumptions['discount_rate'] - assumptions['terminal_growth_rate'])
            
            return terminal_value
            
        except Exception as e:
            logger.error(f"Error calculating terminal value: {e}")
            return 0
    
    def _calculate_present_values(self, future_cash_flows, discount_rate):
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
    
    def _get_market_data(self):
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
            'ticker_symbol': None
        }
        
        try:
            # Use financial calculator's market data if available
            if hasattr(self.financial_calculator, 'ticker_symbol') and self.financial_calculator.ticker_symbol:
                # Try to fetch fresh market data
                fresh_data = self.financial_calculator.fetch_market_data()
                
                if fresh_data:
                    market_data.update(fresh_data)
                else:
                    # Fall back to any existing data
                    market_data.update({
                        'shares_outstanding': getattr(self.financial_calculator, 'shares_outstanding', 1000000),
                        'current_price': getattr(self.financial_calculator, 'current_stock_price', 0),
                        'market_cap': getattr(self.financial_calculator, 'market_cap', 0),
                        'ticker_symbol': self.financial_calculator.ticker_symbol
                    })
                
        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")
            
        return market_data
    
    def _get_net_debt(self):
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
                'total debt', 'total_debt', 'debt', 
                'long term debt', 'long_term_debt', 'long-term debt',
                'short term debt', 'short_term_debt', 'short-term debt',
                'borrowings', 'total borrowings',
                'notes payable', 'bonds payable'
            ]
            
            # Look for cash items
            cash_keywords = [
                'cash', 'cash and cash equivalents', 'cash_and_cash_equivalents',
                'cash and equivalents', 'total cash', 'liquid assets'
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
                                    total_debt = max(total_debt, abs(value))  # Take the latest/largest debt value
                                    break
                            
                            # Check for cash
                            for cash_keyword in cash_keywords:
                                if cash_keyword in key_lower and isinstance(value, (int, float)):
                                    cash_and_equivalents = max(cash_and_equivalents, abs(value))  # Take the latest/largest cash value
                                    break
            
            # Calculate net debt
            net_debt = total_debt - cash_and_equivalents
            
            logger.info(f"Net debt calculation: Total Debt=${total_debt:.1f}M, Cash=${cash_and_equivalents:.1f}M, Net Debt=${net_debt:.1f}M")
            
            return net_debt
            
        except Exception as e:
            logger.error(f"Error calculating net debt: {e}")
            return 0  # Default to zero net debt if calculation fails
    
    def sensitivity_analysis(self, discount_rates, growth_rates, base_assumptions=None):
        """
        Perform sensitivity analysis on DCF valuation with price-based results
        
        Args:
            discount_rates (list): List of discount rates to test
            growth_rates (list): List of growth rates to test (for FCF projections)
            base_assumptions (dict): Base DCF assumptions
            
        Returns:
            dict: Sensitivity analysis results with upside/downside percentages
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
            'current_price': current_price
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