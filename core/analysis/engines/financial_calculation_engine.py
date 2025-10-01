"""
Financial Calculation Engine - Pure Mathematical Functions
=========================================================

This module provides pure financial calculation functions isolated from data management,
I/O operations, and business logic. It serves as the mathematical core for all valuation
models in the financial analysis system.

Key Features:
- Pure mathematical functions with no side effects
- Mathematical validation and accuracy testing
- Consistent calculation interfaces across all valuation models
- Comprehensive error handling with detailed logging
- Unit-tested mathematical operations

Classes:
--------
FinancialCalculationEngine
    Main engine providing all core financial calculation functions

Mathematical Functions Available:
---------------------------------
1. Free Cash Flow Calculations (FCF, FCFE, FCFF)
2. Discounted Cash Flow (DCF) Valuations
3. Dividend Discount Model (DDM) Calculations  
4. Price-to-Book (P/B) Ratio Analysis
5. Growth Rate Calculations (CAGR, multi-period)
6. Present Value and Terminal Value Calculations
7. Financial Ratios and Metrics

Design Principles:
-----------------
- Pure functions: No external dependencies or side effects
- Immutable inputs: Functions don't modify input data
- Consistent interfaces: Standard parameter and return patterns
- Comprehensive validation: Input validation and mathematical checks
- Error isolation: Mathematical errors don't propagate to calling code
"""

import math
import logging
from typing import List, Dict, Optional, Any, Union, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """Standard result container for all calculation functions"""
    value: Union[float, List[float], Dict[str, Any]]
    is_valid: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FinancialCalculationEngine:
    """
    Pure mathematical calculation engine for financial analysis.
    
    All functions in this class are pure mathematical operations with no side effects.
    They accept numerical inputs and return calculation results without accessing
    external data sources, files, or performing I/O operations.
    """
    
    def __init__(self):
        """Initialize the calculation engine with mathematical constants and validation rules"""
        self.EPSILON = 1e-10  # Small value for floating-point comparisons
        self.MAX_GROWTH_RATE = 1.0  # 100% maximum growth rate for validation
        self.MIN_DISCOUNT_RATE = 0.001  # 0.1% minimum discount rate
        self.MAX_DISCOUNT_RATE = 0.50  # 50% maximum discount rate
        
    # =====================
    # Free Cash Flow Calculations
    # =====================
    
    def calculate_fcf_to_firm(
        self,
        ebit_values: List[float],
        tax_rates: List[float],
        depreciation_values: List[float],
        working_capital_changes: List[float],
        capex_values: List[float]
    ) -> CalculationResult:
        """
        Calculate Free Cash Flow to Firm (FCFF) from component values.
        
        Formula: FCFF = EBIT(1-Tax Rate) + Depreciation - CapEx - ΔWorking Capital
        
        Args:
            ebit_values: List of EBIT values
            tax_rates: List of tax rates (as decimals, e.g., 0.25 for 25%)
            depreciation_values: List of depreciation & amortization values
            working_capital_changes: List of working capital changes
            capex_values: List of capital expenditure values
            
        Returns:
            CalculationResult containing FCFF values or error information
        """
        try:
            # Input validation
            arrays = [ebit_values, tax_rates, depreciation_values, working_capital_changes, capex_values]
            if not all(isinstance(arr, list) for arr in arrays):
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="All inputs must be lists"
                )
            
            if not arrays or not any(arrays):
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="At least one input array must be non-empty"
                )
            
            # Find minimum length for calculation
            lengths = [len(arr) for arr in arrays if arr]
            min_length = min(lengths) if lengths else 0
            
            if min_length == 0:
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="No valid data points for calculation"
                )
            
            # Calculate FCFF for each period
            fcff_values = []
            for i in range(min_length):
                try:
                    # Get values with bounds checking
                    ebit = ebit_values[i] if i < len(ebit_values) else 0
                    tax_rate = tax_rates[i] if i < len(tax_rates) else 0
                    depreciation = depreciation_values[i] if i < len(depreciation_values) else 0
                    wc_change = working_capital_changes[i] if i < len(working_capital_changes) else 0
                    capex = capex_values[i] if i < len(capex_values) else 0
                    
                    # Validate tax rate
                    if tax_rate < 0 or tax_rate > 1:
                        logger.warning(f"Invalid tax rate {tax_rate:.3f} at index {i}, clamping to [0, 1]")
                        tax_rate = max(0, min(1, tax_rate))
                    
                    # Calculate after-tax EBIT
                    after_tax_ebit = ebit * (1 - tax_rate)
                    
                    # Calculate FCFF
                    fcff = after_tax_ebit + depreciation - abs(capex) - wc_change
                    fcff_values.append(fcff)
                    
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error calculating FCFF at index {i}: {e}")
                    fcff_values.append(0.0)
            
            return CalculationResult(
                value=fcff_values,
                is_valid=True,
                metadata={
                    'calculation_method': 'FCFF = EBIT(1-Tax) + DA - CapEx - ΔWC',
                    'periods_calculated': len(fcff_values)
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=[],
                is_valid=False,
                error_message=f"FCFF calculation failed: {str(e)}"
            )
    
    def calculate_fcf_to_equity(
        self,
        net_income_values: List[float],
        depreciation_values: List[float],
        working_capital_changes: List[float],
        capex_values: List[float],
        net_borrowing_values: List[float]
    ) -> CalculationResult:
        """
        Calculate Free Cash Flow to Equity (FCFE) from component values.
        
        Formula: FCFE = Net Income + Depreciation - CapEx - ΔWorking Capital + Net Borrowing
        
        Args:
            net_income_values: List of net income values
            depreciation_values: List of depreciation & amortization values  
            working_capital_changes: List of working capital changes
            capex_values: List of capital expenditure values
            net_borrowing_values: List of net borrowing values
            
        Returns:
            CalculationResult containing FCFE values or error information
        """
        try:
            # Input validation
            arrays = [net_income_values, depreciation_values, working_capital_changes, capex_values, net_borrowing_values]
            if not all(isinstance(arr, list) for arr in arrays):
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="All inputs must be lists"
                )
            
            lengths = [len(arr) for arr in arrays if arr]
            min_length = min(lengths) if lengths else 0
            
            if min_length == 0:
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="No valid data points for calculation"
                )
            
            # Calculate FCFE for each period
            fcfe_values = []
            for i in range(min_length):
                try:
                    net_income = net_income_values[i] if i < len(net_income_values) else 0
                    depreciation = depreciation_values[i] if i < len(depreciation_values) else 0
                    wc_change = working_capital_changes[i] if i < len(working_capital_changes) else 0
                    capex = capex_values[i] if i < len(capex_values) else 0
                    net_borrowing = net_borrowing_values[i] if i < len(net_borrowing_values) else 0
                    
                    # Calculate FCFE
                    fcfe = net_income + depreciation - abs(capex) - wc_change + net_borrowing
                    fcfe_values.append(fcfe)
                    
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error calculating FCFE at index {i}: {e}")
                    fcfe_values.append(0.0)
            
            return CalculationResult(
                value=fcfe_values,
                is_valid=True,
                metadata={
                    'calculation_method': 'FCFE = NI + DA - CapEx - ΔWC + Net Borrowing',
                    'periods_calculated': len(fcfe_values)
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=[],
                is_valid=False,
                error_message=f"FCFE calculation failed: {str(e)}"
            )
    
    def calculate_levered_fcf(
        self,
        operating_cash_flow_values: List[float],
        capex_values: List[float]
    ) -> CalculationResult:
        """
        Calculate Levered Free Cash Flow (Traditional FCF).
        
        Formula: LFCF = Operating Cash Flow - Capital Expenditures
        
        Args:
            operating_cash_flow_values: List of operating cash flow values
            capex_values: List of capital expenditure values
            
        Returns:
            CalculationResult containing LFCF values or error information
        """
        try:
            if not isinstance(operating_cash_flow_values, list) or not isinstance(capex_values, list):
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="Inputs must be lists"
                )
            
            min_length = min(len(operating_cash_flow_values), len(capex_values))
            
            if min_length == 0:
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="No valid data points for calculation"
                )
            
            # Calculate LFCF for each period
            lfcf_values = []
            for i in range(min_length):
                try:
                    ocf = operating_cash_flow_values[i]
                    capex = capex_values[i]
                    
                    # Calculate Levered FCF
                    lfcf = ocf - abs(capex)
                    lfcf_values.append(lfcf)
                    
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error calculating LFCF at index {i}: {e}")
                    lfcf_values.append(0.0)
            
            return CalculationResult(
                value=lfcf_values,
                is_valid=True,
                metadata={
                    'calculation_method': 'LFCF = Operating Cash Flow - CapEx',
                    'periods_calculated': len(lfcf_values)
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=[],
                is_valid=False,
                error_message=f"LFCF calculation failed: {str(e)}"
            )
    
    # =====================
    # Growth Rate Calculations
    # =====================
    
    def calculate_cagr(
        self,
        start_value: float,
        end_value: float,
        periods: float
    ) -> CalculationResult:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Formula: CAGR = (End Value / Start Value)^(1/periods) - 1
        
        Args:
            start_value: Starting value
            end_value: Ending value
            periods: Number of periods
            
        Returns:
            CalculationResult containing CAGR as decimal or error information
        """
        try:
            # Input validation
            if start_value is None or end_value is None or periods is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )
            
            if periods <= 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Periods must be positive"
                )
            
            if start_value == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Start value cannot be zero"
                )
            
            # Handle negative values
            if start_value < 0 or end_value < 0:
                logger.warning("Negative values in CAGR calculation may produce unexpected results")
            
            # Calculate CAGR
            ratio = end_value / start_value
            if ratio <= 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Value ratio must be positive for CAGR calculation"
                )
            
            cagr = (ratio ** (1 / periods)) - 1
            
            # Validate result
            if abs(cagr) > self.MAX_GROWTH_RATE:
                logger.warning(f"CAGR {cagr:.1%} exceeds maximum expected growth rate")
            
            return CalculationResult(
                value=cagr,
                is_valid=True,
                metadata={
                    'start_value': start_value,
                    'end_value': end_value,
                    'periods': periods,
                    'calculation_method': 'CAGR = (End/Start)^(1/periods) - 1'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"CAGR calculation failed: {str(e)}"
            )
    
    # =====================
    # DCF Calculations
    # =====================
    
    def calculate_present_value(
        self,
        future_cash_flows: List[float],
        discount_rate: float
    ) -> CalculationResult:
        """
        Calculate present values of future cash flows.
        
        Formula: PV = CF / (1 + r)^t
        
        Args:
            future_cash_flows: List of future cash flow values
            discount_rate: Discount rate as decimal (e.g., 0.1 for 10%)
            
        Returns:
            CalculationResult containing present values or error information
        """
        try:
            # Input validation
            if not isinstance(future_cash_flows, list):
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="Future cash flows must be a list"
                )
            
            if not future_cash_flows:
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message="Future cash flows list is empty"
                )
            
            # Validate discount rate
            if discount_rate < self.MIN_DISCOUNT_RATE or discount_rate > self.MAX_DISCOUNT_RATE:
                return CalculationResult(
                    value=[],
                    is_valid=False,
                    error_message=f"Discount rate {discount_rate:.1%} outside valid range [{self.MIN_DISCOUNT_RATE:.1%}, {self.MAX_DISCOUNT_RATE:.1%}]"
                )
            
            # Calculate present values
            present_values = []
            for year, cash_flow in enumerate(future_cash_flows, 1):
                try:
                    if cash_flow is None:
                        present_values.append(0.0)
                        continue
                    
                    pv = cash_flow / ((1 + discount_rate) ** year)
                    present_values.append(pv)
                    
                except (TypeError, ValueError, ZeroDivisionError) as e:
                    logger.warning(f"Error calculating PV for year {year}: {e}")
                    present_values.append(0.0)
            
            return CalculationResult(
                value=present_values,
                is_valid=True,
                metadata={
                    'discount_rate': discount_rate,
                    'periods': len(present_values),
                    'total_pv': sum(present_values),
                    'calculation_method': 'PV = CF / (1 + r)^t'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=[],
                is_valid=False,
                error_message=f"Present value calculation failed: {str(e)}"
            )
    
    def calculate_terminal_value(
        self,
        final_cash_flow: float,
        growth_rate: float,
        discount_rate: float
    ) -> CalculationResult:
        """
        Calculate terminal value using Gordon Growth Model.
        
        Formula: Terminal Value = CF × (1 + g) / (r - g)
        
        Args:
            final_cash_flow: Cash flow in the final projection year
            growth_rate: Terminal growth rate as decimal
            discount_rate: Discount rate as decimal
            
        Returns:
            CalculationResult containing terminal value or error information
        """
        try:
            # Input validation
            if final_cash_flow is None or growth_rate is None or discount_rate is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )
            
            # Validate growth rate vs discount rate
            if growth_rate >= discount_rate:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message=f"Growth rate ({growth_rate:.1%}) must be less than discount rate ({discount_rate:.1%})"
                )
            
            # Validate rates are reasonable
            if growth_rate < -0.50 or growth_rate > 0.20:
                logger.warning(f"Terminal growth rate {growth_rate:.1%} is outside typical range [-50%, 20%]")
            
            # Calculate terminal cash flow
            terminal_cf = final_cash_flow * (1 + growth_rate)
            
            # Calculate terminal value
            denominator = discount_rate - growth_rate
            if abs(denominator) < self.EPSILON:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Discount rate and growth rate are too close (denominator near zero)"
                )
            
            terminal_value = terminal_cf / denominator
            
            return CalculationResult(
                value=terminal_value,
                is_valid=True,
                metadata={
                    'final_cash_flow': final_cash_flow,
                    'terminal_cash_flow': terminal_cf,
                    'growth_rate': growth_rate,
                    'discount_rate': discount_rate,
                    'calculation_method': 'TV = CF × (1 + g) / (r - g)'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Terminal value calculation failed: {str(e)}"
            )
    
    # =====================
    # DDM Calculations
    # =====================
    
    def calculate_gordon_growth_value(
        self,
        current_dividend: float,
        growth_rate: float,
        discount_rate: float
    ) -> CalculationResult:
        """
        Calculate stock value using Gordon Growth Model.
        
        Formula: Value = D₁ / (r - g) where D₁ = D₀ × (1 + g)
        
        Args:
            current_dividend: Current dividend per share
            growth_rate: Dividend growth rate as decimal
            discount_rate: Required rate of return as decimal
            
        Returns:
            CalculationResult containing stock value or error information
        """
        try:
            # Input validation
            if current_dividend is None or growth_rate is None or discount_rate is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )
            
            if current_dividend <= 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Current dividend must be positive"
                )
            
            # Validate growth vs discount rate
            if growth_rate >= discount_rate:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message=f"Growth rate ({growth_rate:.1%}) must be less than discount rate ({discount_rate:.1%})"
                )
            
            # Calculate next year's dividend
            next_dividend = current_dividend * (1 + growth_rate)
            
            # Calculate Gordon Growth value
            denominator = discount_rate - growth_rate
            if abs(denominator) < self.EPSILON:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Discount rate and growth rate are too close"
                )
            
            value = next_dividend / denominator
            
            return CalculationResult(
                value=value,
                is_valid=True,
                metadata={
                    'current_dividend': current_dividend,
                    'next_dividend': next_dividend,
                    'growth_rate': growth_rate,
                    'discount_rate': discount_rate,
                    'calculation_method': 'Gordon Growth: V = D₁ / (r - g)'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Gordon Growth calculation failed: {str(e)}"
            )
    
    # =====================
    # P/B Calculations
    # =====================
    
    def calculate_pb_ratio(
        self,
        market_price: float,
        book_value_per_share: float
    ) -> CalculationResult:
        """
        Calculate Price-to-Book (P/B) ratio.
        
        Formula: P/B = Market Price per Share / Book Value per Share
        
        Args:
            market_price: Current market price per share
            book_value_per_share: Book value per share
            
        Returns:
            CalculationResult containing P/B ratio or error information
        """
        try:
            # Input validation
            if market_price is None or book_value_per_share is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )
            
            if market_price <= 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Market price must be positive"
                )
            
            if book_value_per_share == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Book value per share cannot be zero"
                )
            
            # Calculate P/B ratio
            pb_ratio = market_price / book_value_per_share
            
            # Validate reasonable range
            if pb_ratio < 0:
                logger.warning("Negative P/B ratio indicates negative book value")
            elif pb_ratio > 50:
                logger.warning(f"P/B ratio {pb_ratio:.1f} is extremely high")
            
            return CalculationResult(
                value=pb_ratio,
                is_valid=True,
                metadata={
                    'market_price': market_price,
                    'book_value_per_share': book_value_per_share,
                    'calculation_method': 'P/B = Market Price / Book Value per Share'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"P/B ratio calculation failed: {str(e)}"
            )
    
    def calculate_book_value_per_share(
        self,
        total_equity: float,
        shares_outstanding: float
    ) -> CalculationResult:
        """
        Calculate Book Value per Share.
        
        Formula: BVPS = Total Shareholders' Equity / Shares Outstanding
        
        Args:
            total_equity: Total shareholders' equity
            shares_outstanding: Number of shares outstanding
            
        Returns:
            CalculationResult containing BVPS or error information
        """
        try:
            # Input validation
            if total_equity is None or shares_outstanding is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )
            
            if shares_outstanding <= 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Shares outstanding must be positive"
                )
            
            # Calculate BVPS
            bvps = total_equity / shares_outstanding
            
            # Log warning for negative book value
            if bvps < 0:
                logger.warning("Negative book value per share indicates financial distress")
            
            return CalculationResult(
                value=bvps,
                is_valid=True,
                metadata={
                    'total_equity': total_equity,
                    'shares_outstanding': shares_outstanding,
                    'calculation_method': 'BVPS = Total Equity / Shares Outstanding'
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"BVPS calculation failed: {str(e)}"
            )
    
    # =====================
    # Utility Functions
    # =====================
    
    def validate_positive_values(self, values: List[float], name: str = "values") -> bool:
        """
        Validate that all values in a list are positive.
        
        Args:
            values: List of values to validate
            name: Name for error messages
            
        Returns:
            True if all values are positive, False otherwise
        """
        try:
            if not isinstance(values, list):
                return False
            
            for i, value in enumerate(values):
                if value is None or value <= 0:
                    logger.warning(f"{name}[{i}] = {value} is not positive")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating {name}: {e}")
            return False
    
    def calculate_percentile(self, value: float, values: List[float]) -> CalculationResult:
        """
        Calculate percentile ranking of a value within a list of values.
        
        Args:
            value: Value to find percentile for
            values: List of values for comparison
            
        Returns:
            CalculationResult containing percentile (0-100) or error information
        """
        try:
            if not isinstance(values, list) or not values:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Values list must be non-empty"
                )
            
            if value is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Value cannot be None"
                )
            
            # Remove None values and sort
            clean_values = [v for v in values if v is not None]
            if not clean_values:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="No valid values for percentile calculation"
                )
            
            clean_values.sort()
            
            # Count values less than or equal to target value
            count_below_or_equal = sum(1 for v in clean_values if v <= value)
            
            # Calculate percentile
            percentile = (count_below_or_equal / len(clean_values)) * 100
            
            return CalculationResult(
                value=percentile,
                is_valid=True,
                metadata={
                    'value': value,
                    'total_values': len(clean_values),
                    'values_below_or_equal': count_below_or_equal
                }
            )
            
        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Percentile calculation failed: {str(e)}"
            )

    # =====================
    # Liquidity Ratios
    # =====================

    def calculate_current_ratio(
        self,
        current_assets: float,
        current_liabilities: float
    ) -> CalculationResult:
        """
        Calculate Current Ratio for liquidity analysis.

        Formula: Current Ratio = Current Assets / Current Liabilities

        Args:
            current_assets: Total current assets
            current_liabilities: Total current liabilities

        Returns:
            CalculationResult containing current ratio or error information
        """
        try:
            # Input validation
            if current_assets is None or current_liabilities is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if current_liabilities == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            if current_assets < 0 or current_liabilities < 0:
                logger.warning("Negative values in current ratio calculation may indicate data issues")

            # Calculate current ratio
            current_ratio = current_assets / current_liabilities

            # Add interpretation warnings
            if current_ratio < 1.0:
                logger.warning(f"Current ratio {current_ratio:.2f} is below 1.0, indicating potential liquidity issues")
            elif current_ratio > 3.0:
                logger.warning(f"Current ratio {current_ratio:.2f} is very high, may indicate inefficient asset use")

            return CalculationResult(
                value=current_ratio,
                is_valid=True,
                metadata={
                    'current_assets': current_assets,
                    'current_liabilities': current_liabilities,
                    'calculation_method': 'Current Ratio = Current Assets / Current Liabilities',
                    'interpretation': self._interpret_current_ratio(current_ratio)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Current ratio calculation failed: {str(e)}"
            )

    def calculate_quick_ratio(
        self,
        current_assets: float,
        inventory: float,
        current_liabilities: float
    ) -> CalculationResult:
        """
        Calculate Quick Ratio (Acid-Test Ratio) for liquidity analysis.

        Formula: Quick Ratio = (Current Assets - Inventory) / Current Liabilities

        Args:
            current_assets: Total current assets
            inventory: Inventory value
            current_liabilities: Total current liabilities

        Returns:
            CalculationResult containing quick ratio or error information
        """
        try:
            # Input validation
            if current_assets is None or inventory is None or current_liabilities is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if current_liabilities == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            # Handle inventory exceeding current assets
            if inventory > current_assets:
                logger.warning(f"Inventory ({inventory}) exceeds current assets ({current_assets})")

            # Calculate quick assets and quick ratio
            quick_assets = current_assets - inventory
            quick_ratio = quick_assets / current_liabilities

            # Add interpretation warnings
            if quick_ratio < 0.5:
                logger.warning(f"Quick ratio {quick_ratio:.2f} is below 0.5, indicating potential liquidity concerns")
            elif quick_ratio > 2.0:
                logger.warning(f"Quick ratio {quick_ratio:.2f} is very high, may indicate excess liquid assets")

            return CalculationResult(
                value=quick_ratio,
                is_valid=True,
                metadata={
                    'current_assets': current_assets,
                    'inventory': inventory,
                    'quick_assets': quick_assets,
                    'current_liabilities': current_liabilities,
                    'calculation_method': 'Quick Ratio = (Current Assets - Inventory) / Current Liabilities',
                    'interpretation': self._interpret_quick_ratio(quick_ratio)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Quick ratio calculation failed: {str(e)}"
            )

    def calculate_cash_ratio(
        self,
        cash_and_equivalents: float,
        current_liabilities: float
    ) -> CalculationResult:
        """
        Calculate Cash Ratio for the most conservative liquidity measure.

        Formula: Cash Ratio = (Cash + Cash Equivalents) / Current Liabilities

        Args:
            cash_and_equivalents: Cash and cash equivalents
            current_liabilities: Total current liabilities

        Returns:
            CalculationResult containing cash ratio or error information
        """
        try:
            # Input validation
            if cash_and_equivalents is None or current_liabilities is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if current_liabilities == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            if cash_and_equivalents < 0:
                logger.warning("Negative cash and equivalents may indicate data errors")

            # Calculate cash ratio
            cash_ratio = cash_and_equivalents / current_liabilities

            # Add interpretation warnings
            if cash_ratio < 0.1:
                logger.warning(f"Cash ratio {cash_ratio:.2f} is below 0.1, indicating limited immediate liquidity")
            elif cash_ratio > 0.5:
                logger.warning(f"Cash ratio {cash_ratio:.2f} is very high, may indicate excess cash holdings")

            return CalculationResult(
                value=cash_ratio,
                is_valid=True,
                metadata={
                    'cash_and_equivalents': cash_and_equivalents,
                    'current_liabilities': current_liabilities,
                    'calculation_method': 'Cash Ratio = (Cash + Cash Equivalents) / Current Liabilities',
                    'interpretation': self._interpret_cash_ratio(cash_ratio)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Cash ratio calculation failed: {str(e)}"
            )

    def calculate_working_capital(
        self,
        current_assets: float,
        current_liabilities: float
    ) -> CalculationResult:
        """
        Calculate Working Capital for absolute liquidity measurement.

        Formula: Working Capital = Current Assets - Current Liabilities

        Args:
            current_assets: Total current assets
            current_liabilities: Total current liabilities

        Returns:
            CalculationResult containing working capital or error information
        """
        try:
            # Input validation
            if current_assets is None or current_liabilities is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            # Calculate working capital
            working_capital = current_assets - current_liabilities

            # Add interpretation warnings
            if working_capital < 0:
                logger.warning(f"Negative working capital {working_capital:.2f} indicates potential liquidity issues")

            return CalculationResult(
                value=working_capital,
                is_valid=True,
                metadata={
                    'current_assets': current_assets,
                    'current_liabilities': current_liabilities,
                    'calculation_method': 'Working Capital = Current Assets - Current Liabilities',
                    'interpretation': self._interpret_working_capital(working_capital, current_assets)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Working capital calculation failed: {str(e)}"
            )

    # =====================
    # Liquidity Ratio Interpretation Helpers
    # =====================

    def _interpret_current_ratio(self, ratio: float) -> str:
        """Provide interpretation of current ratio value"""
        if ratio >= 2.0:
            return "Strong liquidity position"
        elif ratio >= 1.0:
            return "Adequate liquidity"
        else:
            return "Potential liquidity concerns"

    def _interpret_quick_ratio(self, ratio: float) -> str:
        """Provide interpretation of quick ratio value"""
        if ratio >= 1.0:
            return "Strong immediate liquidity"
        elif ratio >= 0.5:
            return "Moderate liquidity"
        else:
            return "Weak immediate liquidity"

    def _interpret_cash_ratio(self, ratio: float) -> str:
        """Provide interpretation of cash ratio value"""
        if ratio >= 0.2:
            return "Strong cash position"
        elif ratio >= 0.1:
            return "Adequate cash position"
        else:
            return "Limited cash position"

    def _interpret_working_capital(self, working_capital: float, current_assets: float) -> str:
        """Provide interpretation of working capital value"""
        if working_capital <= 0:
            return "Negative working capital - potential liquidity issues"
        elif working_capital / current_assets > 0.5:
            return "Strong working capital position"
        else:
            return "Moderate working capital position"

    # =====================
    # Profitability Ratios
    # =====================

    def calculate_gross_profit_margin(
        self,
        gross_profit: float,
        revenue: float
    ) -> CalculationResult:
        """
        Calculate Gross Profit Margin for profitability analysis.

        Formula: Gross Profit Margin = Gross Profit / Revenue

        Args:
            gross_profit: Gross profit amount
            revenue: Total revenue

        Returns:
            CalculationResult containing gross profit margin as decimal or error information
        """
        try:
            # Input validation
            if gross_profit is None or revenue is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if revenue == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            if revenue < 0:
                logger.warning("Negative revenue may indicate data errors or unusual accounting treatment")

            # Calculate gross profit margin
            gross_margin = gross_profit / revenue

            # Add interpretation warnings
            if gross_margin < 0:
                logger.warning(f"Negative gross profit margin {gross_margin:.1%} indicates cost of goods sold exceeds revenue")
            elif gross_margin > 0.8:
                logger.warning(f"Gross profit margin {gross_margin:.1%} is very high, may indicate exceptional pricing power or low COGS")

            return CalculationResult(
                value=gross_margin,
                is_valid=True,
                metadata={
                    'gross_profit': gross_profit,
                    'revenue': revenue,
                    'calculation_method': 'Gross Profit Margin = Gross Profit / Revenue',
                    'interpretation': self._interpret_gross_margin(gross_margin)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Gross profit margin calculation failed: {str(e)}"
            )

    def calculate_operating_profit_margin(
        self,
        operating_income: float,
        revenue: float
    ) -> CalculationResult:
        """
        Calculate Operating Profit Margin for operational efficiency analysis.

        Formula: Operating Profit Margin = Operating Income / Revenue

        Args:
            operating_income: Operating income (EBIT)
            revenue: Total revenue

        Returns:
            CalculationResult containing operating profit margin as decimal or error information
        """
        try:
            # Input validation
            if operating_income is None or revenue is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if revenue == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            if revenue < 0:
                logger.warning("Negative revenue may indicate data errors or unusual accounting treatment")

            # Calculate operating profit margin
            operating_margin = operating_income / revenue

            # Add interpretation warnings
            if operating_margin < 0:
                logger.warning(f"Negative operating profit margin {operating_margin:.1%} indicates operating expenses exceed gross profit")
            elif operating_margin > 0.5:
                logger.warning(f"Operating profit margin {operating_margin:.1%} is very high, may indicate exceptional operational efficiency")

            return CalculationResult(
                value=operating_margin,
                is_valid=True,
                metadata={
                    'operating_income': operating_income,
                    'revenue': revenue,
                    'calculation_method': 'Operating Profit Margin = Operating Income / Revenue',
                    'interpretation': self._interpret_operating_margin(operating_margin)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Operating profit margin calculation failed: {str(e)}"
            )

    def calculate_net_profit_margin(
        self,
        net_income: float,
        revenue: float
    ) -> CalculationResult:
        """
        Calculate Net Profit Margin for overall profitability analysis.

        Formula: Net Profit Margin = Net Income / Revenue

        Args:
            net_income: Net income (after all expenses and taxes)
            revenue: Total revenue

        Returns:
            CalculationResult containing net profit margin as decimal or error information
        """
        try:
            # Input validation
            if net_income is None or revenue is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if revenue == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            if revenue < 0:
                logger.warning("Negative revenue may indicate data errors or unusual accounting treatment")

            # Calculate net profit margin
            net_margin = net_income / revenue

            # Add interpretation warnings
            if net_margin < 0:
                logger.warning(f"Negative net profit margin {net_margin:.1%} indicates the company is losing money")
            elif net_margin > 0.3:
                logger.warning(f"Net profit margin {net_margin:.1%} is very high, may indicate exceptional profitability or unusual circumstances")

            return CalculationResult(
                value=net_margin,
                is_valid=True,
                metadata={
                    'net_income': net_income,
                    'revenue': revenue,
                    'calculation_method': 'Net Profit Margin = Net Income / Revenue',
                    'interpretation': self._interpret_net_margin(net_margin)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Net profit margin calculation failed: {str(e)}"
            )

    # =====================
    # Profitability Ratio Interpretation Helpers
    # =====================

    def _interpret_gross_margin(self, margin: float) -> str:
        """Provide interpretation of gross profit margin value"""
        if margin >= 0.6:
            return "Excellent gross margin"
        elif margin >= 0.4:
            return "Strong gross margin"
        elif margin >= 0.2:
            return "Moderate gross margin"
        elif margin >= 0:
            return "Low gross margin"
        else:
            return "Negative gross margin - cost of goods sold exceeds revenue"

    def _interpret_operating_margin(self, margin: float) -> str:
        """Provide interpretation of operating profit margin value"""
        if margin >= 0.25:
            return "Excellent operating efficiency"
        elif margin >= 0.15:
            return "Strong operating efficiency"
        elif margin >= 0.05:
            return "Moderate operating efficiency"
        elif margin >= 0:
            return "Low operating efficiency"
        else:
            return "Negative operating margin - operating expenses exceed gross profit"

    def _interpret_net_margin(self, margin: float) -> str:
        """Provide interpretation of net profit margin value"""
        if margin >= 0.20:
            return "Excellent net profitability"
        elif margin >= 0.10:
            return "Strong net profitability"
        elif margin >= 0.05:
            return "Moderate net profitability"
        elif margin >= 0:
            return "Low net profitability"
        else:
            return "Negative net margin - company is losing money"

    def calculate_return_on_assets(
        self,
        net_income: float,
        total_assets: float,
        average_assets: Optional[float] = None
    ) -> CalculationResult:
        """
        Calculate Return on Assets (ROA) for asset efficiency analysis.

        Formula: ROA = Net Income / Total Assets (or Average Assets)

        Args:
            net_income: Net income for the period
            total_assets: Total assets at period end
            average_assets: Optional average assets for more accurate calculation

        Returns:
            CalculationResult containing ROA as decimal or error information
        """
        try:
            # Input validation
            if net_income is None or total_assets is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Net income and total assets cannot be None"
                )

            # Use average assets if provided, otherwise use period-end assets
            assets_denominator = average_assets if average_assets is not None else total_assets

            if assets_denominator == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Assets denominator cannot be zero"
                )

            if assets_denominator < 0:
                logger.warning("Negative total assets may indicate financial distress or data errors")

            # Calculate ROA
            roa = net_income / assets_denominator

            # Add interpretation warnings
            if roa < -0.05:
                logger.warning(f"ROA {roa:.1%} is significantly negative, indicating poor asset utilization")
            elif roa > 0.20:
                logger.warning(f"ROA {roa:.1%} is very high, may indicate exceptional asset efficiency or low asset base")

            return CalculationResult(
                value=roa,
                is_valid=True,
                metadata={
                    'net_income': net_income,
                    'total_assets': total_assets,
                    'average_assets': average_assets,
                    'assets_used': assets_denominator,
                    'calculation_method': f'ROA = Net Income / {"Average Assets" if average_assets is not None else "Total Assets"}',
                    'interpretation': self._interpret_roa(roa)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"ROA calculation failed: {str(e)}"
            )

    def _interpret_roa(self, roa: float) -> str:
        """Provide interpretation of ROA value"""
        if roa >= 0.15:
            return "Excellent asset efficiency"
        elif roa >= 0.10:
            return "Strong asset efficiency"
        elif roa >= 0.05:
            return "Moderate asset efficiency"
        elif roa >= 0:
            return "Low asset efficiency"
        else:
            return "Negative ROA - assets are not generating positive returns"

    def calculate_return_on_equity(
        self,
        net_income: float,
        shareholders_equity: float,
        average_equity: Optional[float] = None
    ) -> CalculationResult:
        """
        Calculate Return on Equity (ROE) for shareholder value analysis.

        Formula: ROE = Net Income / Shareholders' Equity (or Average Equity)

        Args:
            net_income: Net income for the period
            shareholders_equity: Shareholders' equity at period end
            average_equity: Optional average equity for more accurate calculation

        Returns:
            CalculationResult containing ROE as decimal or error information
        """
        try:
            # Input validation
            if net_income is None or shareholders_equity is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Net income and shareholders' equity cannot be None"
                )

            # Use average equity if provided, otherwise use period-end equity
            equity_denominator = average_equity if average_equity is not None else shareholders_equity

            if equity_denominator == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Shareholders' equity denominator cannot be zero"
                )

            # Special handling for negative equity scenarios
            if equity_denominator < 0:
                logger.warning("Negative shareholders' equity indicates financial distress - ROE calculation may be misleading")

            # Calculate ROE
            roe = net_income / equity_denominator

            # Add interpretation warnings for various scenarios
            if equity_denominator < 0 and net_income > 0:
                logger.warning(f"Positive net income with negative equity results in negative ROE {roe:.1%} - this is a special case requiring careful interpretation")
            elif equity_denominator < 0 and net_income < 0:
                logger.warning(f"Both net income and equity are negative, resulting in positive ROE {roe:.1%} - this does not indicate good performance")
            elif roe < -0.20:
                logger.warning(f"ROE {roe:.1%} is significantly negative, indicating poor equity utilization")
            elif roe > 0.30:
                logger.warning(f"ROE {roe:.1%} is very high, may indicate exceptional performance, high leverage, or low equity base")

            return CalculationResult(
                value=roe,
                is_valid=True,
                metadata={
                    'net_income': net_income,
                    'shareholders_equity': shareholders_equity,
                    'average_equity': average_equity,
                    'equity_used': equity_denominator,
                    'calculation_method': f'ROE = Net Income / {"Average Equity" if average_equity is not None else "Shareholders\' Equity"}',
                    'interpretation': self._interpret_roe(roe, equity_denominator < 0),
                    'negative_equity_scenario': equity_denominator < 0
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"ROE calculation failed: {str(e)}"
            )

    def _interpret_roe(self, roe: float, negative_equity: bool = False) -> str:
        """Provide interpretation of ROE value"""
        if negative_equity:
            if roe > 0:
                return "Positive ROE with negative equity - severe financial distress"
            else:
                return "Negative ROE with negative equity - severe financial distress"
        else:
            if roe >= 0.20:
                return "Excellent return on equity"
            elif roe >= 0.15:
                return "Strong return on equity"
            elif roe >= 0.10:
                return "Moderate return on equity"
            elif roe >= 0:
                return "Low return on equity"
            else:
                return "Negative ROE - equity is not generating positive returns"

    def calculate_return_on_invested_capital(
        self,
        nopat: Optional[float] = None,
        invested_capital: Optional[float] = None,
        ebit: Optional[float] = None,
        tax_rate: Optional[float] = None,
        total_assets: Optional[float] = None,
        current_liabilities: Optional[float] = None,
        equity: Optional[float] = None,
        debt: Optional[float] = None
    ) -> CalculationResult:
        """
        Calculate Return on Invested Capital (ROIC) for capital efficiency analysis.

        Formula: ROIC = NOPAT / Invested Capital
        Where:
        - NOPAT = Net Operating Profit After Tax = EBIT × (1 - Tax Rate)
        - Invested Capital = Total Assets - Current Liabilities OR Equity + Debt

        Args:
            nopat: Net Operating Profit After Tax (if pre-calculated)
            invested_capital: Invested capital amount (if pre-calculated)
            ebit: Earnings Before Interest and Taxes (for NOPAT calculation)
            tax_rate: Tax rate as decimal (for NOPAT calculation)
            total_assets: Total assets (for invested capital calculation)
            current_liabilities: Current liabilities (for invested capital calculation)
            equity: Shareholders' equity (alternative invested capital calculation)
            debt: Total debt (alternative invested capital calculation)

        Returns:
            CalculationResult containing ROIC as decimal or error information
        """
        try:
            # Calculate NOPAT if not provided
            calculated_nopat = nopat
            if calculated_nopat is None:
                if ebit is None or tax_rate is None:
                    return CalculationResult(
                        value=0.0,
                        is_valid=False,
                        error_message="Either NOPAT must be provided, or both EBIT and tax_rate must be provided for NOPAT calculation"
                    )

                # Validate tax rate
                if tax_rate < 0 or tax_rate > 1:
                    logger.warning(f"Tax rate {tax_rate:.1%} outside normal range [0%, 100%], clamping to valid range")
                    tax_rate = max(0, min(1, tax_rate))

                # Calculate NOPAT
                calculated_nopat = ebit * (1 - tax_rate)
                logger.info(f"Calculated NOPAT: {calculated_nopat:.2f} from EBIT: {ebit:.2f} and tax rate: {tax_rate:.1%}")

            # Calculate Invested Capital if not provided
            calculated_invested_capital = invested_capital
            if calculated_invested_capital is None:
                # Method 1: Total Assets - Current Liabilities
                if total_assets is not None and current_liabilities is not None:
                    calculated_invested_capital = total_assets - current_liabilities
                    logger.info(f"Calculated Invested Capital (Assets - Current Liabilities): {calculated_invested_capital:.2f}")

                # Method 2: Equity + Debt (if Method 1 not available)
                elif equity is not None and debt is not None:
                    calculated_invested_capital = equity + debt
                    logger.info(f"Calculated Invested Capital (Equity + Debt): {calculated_invested_capital:.2f}")

                else:
                    return CalculationResult(
                        value=0.0,
                        is_valid=False,
                        error_message="Either invested_capital must be provided, or (total_assets + current_liabilities), or (equity + debt) must be provided"
                    )

            # Final validation
            if calculated_nopat is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="NOPAT could not be calculated or provided"
                )

            if calculated_invested_capital is None or calculated_invested_capital == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Invested capital cannot be zero"
                )

            if calculated_invested_capital < 0:
                logger.warning("Negative invested capital may indicate financial distress or unusual capital structure")

            # Calculate ROIC
            roic = calculated_nopat / calculated_invested_capital

            # Add interpretation warnings
            if roic < -0.10:
                logger.warning(f"ROIC {roic:.1%} is significantly negative, indicating poor capital allocation")
            elif roic > 0.30:
                logger.warning(f"ROIC {roic:.1%} is very high, may indicate exceptional capital efficiency or low capital base")

            # Determine calculation method used for metadata
            nopat_method = "provided" if nopat is not None else "calculated from EBIT × (1 - tax_rate)"
            if invested_capital is not None:
                capital_method = "provided"
            elif total_assets is not None and current_liabilities is not None:
                capital_method = "calculated as Total Assets - Current Liabilities"
            else:
                capital_method = "calculated as Equity + Debt"

            return CalculationResult(
                value=roic,
                is_valid=True,
                metadata={
                    'nopat': calculated_nopat,
                    'invested_capital': calculated_invested_capital,
                    'nopat_method': nopat_method,
                    'invested_capital_method': capital_method,
                    'ebit': ebit,
                    'tax_rate': tax_rate,
                    'total_assets': total_assets,
                    'current_liabilities': current_liabilities,
                    'equity': equity,
                    'debt': debt,
                    'calculation_method': 'ROIC = NOPAT / Invested Capital',
                    'interpretation': self._interpret_roic(roic)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"ROIC calculation failed: {str(e)}"
            )

    def _interpret_roic(self, roic: float) -> str:
        """Provide interpretation of ROIC value"""
        if roic >= 0.20:
            return "Excellent capital efficiency - creating significant value"
        elif roic >= 0.15:
            return "Strong capital efficiency - creating good value"
        elif roic >= 0.10:
            return "Moderate capital efficiency - creating some value"
        elif roic >= 0.05:
            return "Low capital efficiency - minimal value creation"
        elif roic >= 0:
            return "Very low capital efficiency - barely positive returns"
        else:
            return "Negative ROIC - destroying capital value"

    # =====================
    # Leverage/Solvency Ratios
    # =====================

    def calculate_debt_to_assets_ratio(
        self,
        total_debt: float,
        total_assets: float
    ) -> CalculationResult:
        """
        Calculate Debt-to-Assets Ratio for solvency analysis.

        Formula: Debt-to-Assets Ratio = Total Debt / Total Assets

        Args:
            total_debt: Total debt (short-term + long-term debt)
            total_assets: Total assets

        Returns:
            CalculationResult containing debt-to-assets ratio as decimal or error information
        """
        try:
            # Input validation
            if total_debt is None or total_assets is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if total_assets == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Total assets cannot be zero"
                )

            if total_assets < 0:
                logger.warning("Negative total assets may indicate financial distress or data errors")

            if total_debt < 0:
                logger.warning("Negative total debt may indicate data errors or unusual accounting treatment")

            # Calculate debt-to-assets ratio
            debt_to_assets = total_debt / total_assets

            # Add interpretation warnings
            if debt_to_assets < 0:
                logger.warning(f"Negative debt-to-assets ratio {debt_to_assets:.1%} indicates unusual financial structure")
            elif debt_to_assets > 0.6:
                logger.warning(f"Debt-to-assets ratio {debt_to_assets:.1%} is high, indicating significant leverage")
            elif debt_to_assets > 1.0:
                logger.warning(f"Debt-to-assets ratio {debt_to_assets:.1%} exceeds 100%, indicating debt exceeds assets")

            return CalculationResult(
                value=debt_to_assets,
                is_valid=True,
                metadata={
                    'total_debt': total_debt,
                    'total_assets': total_assets,
                    'calculation_method': 'Debt-to-Assets Ratio = Total Debt / Total Assets',
                    'interpretation': self._interpret_debt_to_assets_ratio(debt_to_assets)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Debt-to-assets ratio calculation failed: {str(e)}"
            )

    def _interpret_debt_to_assets_ratio(self, ratio: float) -> str:
        """Provide interpretation of debt-to-assets ratio value"""
        if ratio >= 0.6:
            return "High leverage - significant debt burden"
        elif ratio >= 0.4:
            return "Moderate leverage - balanced debt structure"
        elif ratio >= 0.2:
            return "Conservative leverage - low debt burden"
        elif ratio >= 0:
            return "Very conservative - minimal debt"
        else:
            return "Negative ratio - unusual financial structure"

    def calculate_debt_to_equity_ratio(
        self,
        total_debt: float,
        total_equity: float
    ) -> CalculationResult:
        """
        Calculate Debt-to-Equity Ratio for leverage analysis.

        Formula: Debt-to-Equity Ratio = Total Debt / Total Equity

        Args:
            total_debt: Total debt (short-term + long-term debt)
            total_equity: Total shareholders' equity

        Returns:
            CalculationResult containing debt-to-equity ratio as decimal or error information
        """
        try:
            # Input validation
            if total_debt is None or total_equity is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if total_equity == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Total equity cannot be zero"
                )

            if total_debt < 0:
                logger.warning("Negative total debt may indicate data errors or unusual accounting treatment")

            # Special handling for negative equity scenarios
            if total_equity < 0:
                logger.warning("Negative total equity indicates financial distress - D/E ratio calculation may be misleading")

            # Calculate debt-to-equity ratio
            debt_to_equity = total_debt / total_equity

            # Add interpretation warnings for various scenarios
            if total_equity < 0 and total_debt > 0:
                logger.warning(f"Positive debt with negative equity results in negative D/E ratio {debt_to_equity:.2f} - indicates severe financial distress")
            elif total_equity < 0 and total_debt < 0:
                logger.warning(f"Both debt and equity are negative, resulting in D/E ratio {debt_to_equity:.2f} - unusual financial structure")
            elif debt_to_equity > 2.0:
                logger.warning(f"Debt-to-equity ratio {debt_to_equity:.2f} is high, indicating significant leverage and financial risk")
            elif debt_to_equity > 3.0:
                logger.warning(f"Debt-to-equity ratio {debt_to_equity:.2f} is very high, indicating excessive leverage")

            return CalculationResult(
                value=debt_to_equity,
                is_valid=True,
                metadata={
                    'total_debt': total_debt,
                    'total_equity': total_equity,
                    'calculation_method': 'Debt-to-Equity Ratio = Total Debt / Total Equity',
                    'interpretation': self._interpret_debt_to_equity_ratio(debt_to_equity, total_equity < 0),
                    'negative_equity_scenario': total_equity < 0
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Debt-to-equity ratio calculation failed: {str(e)}"
            )

    def _interpret_debt_to_equity_ratio(self, ratio: float, negative_equity: bool = False) -> str:
        """Provide interpretation of debt-to-equity ratio value"""
        if negative_equity:
            return "Negative equity scenario - severe financial distress"
        else:
            if ratio >= 3.0:
                return "Excessive leverage - very high financial risk"
            elif ratio >= 2.0:
                return "High leverage - significant financial risk"
            elif ratio >= 1.0:
                return "Moderate leverage - balanced capital structure"
            elif ratio >= 0.5:
                return "Conservative leverage - low financial risk"
            elif ratio >= 0:
                return "Very conservative - minimal debt"
            else:
                return "Negative ratio - unusual financial structure"

    def calculate_interest_coverage_ratio(
        self,
        ebit: float,
        interest_expense: float
    ) -> CalculationResult:
        """
        Calculate Interest Coverage Ratio for debt servicing ability analysis.

        Formula: Interest Coverage Ratio = EBIT / Interest Expense

        Args:
            ebit: Earnings Before Interest and Taxes
            interest_expense: Interest expense for the period

        Returns:
            CalculationResult containing interest coverage ratio or error information
        """
        try:
            # Input validation
            if ebit is None or interest_expense is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if interest_expense == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Interest expense cannot be zero"
                )

            if interest_expense < 0:
                logger.warning("Negative interest expense may indicate data errors or interest income")

            # Calculate interest coverage ratio
            interest_coverage = ebit / interest_expense

            # Add interpretation warnings for various scenarios
            if ebit < 0 and interest_expense > 0:
                logger.warning(f"Negative EBIT {ebit:.2f} with positive interest expense results in negative coverage ratio {interest_coverage:.2f} - indicates inability to cover interest")
            elif ebit < 0 and interest_expense < 0:
                logger.warning(f"Both EBIT and interest expense are negative, resulting in coverage ratio {interest_coverage:.2f} - unusual scenario")
            elif interest_coverage < 1.5:
                logger.warning(f"Interest coverage ratio {interest_coverage:.2f} is below 1.5, indicating potential difficulty servicing debt")
            elif interest_coverage < 2.5:
                logger.warning(f"Interest coverage ratio {interest_coverage:.2f} is below 2.5, indicating limited cushion for debt servicing")

            return CalculationResult(
                value=interest_coverage,
                is_valid=True,
                metadata={
                    'ebit': ebit,
                    'interest_expense': interest_expense,
                    'calculation_method': 'Interest Coverage Ratio = EBIT / Interest Expense',
                    'interpretation': self._interpret_interest_coverage_ratio(interest_coverage, ebit < 0),
                    'negative_ebit_scenario': ebit < 0
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Interest coverage ratio calculation failed: {str(e)}"
            )

    def _interpret_interest_coverage_ratio(self, ratio: float, negative_ebit: bool = False) -> str:
        """Provide interpretation of interest coverage ratio value"""
        if negative_ebit:
            return "Negative EBIT - unable to cover interest expense from operations"
        else:
            if ratio >= 5.0:
                return "Excellent debt servicing ability - very strong coverage"
            elif ratio >= 2.5:
                return "Strong debt servicing ability - adequate coverage"
            elif ratio >= 1.5:
                return "Moderate debt servicing ability - limited cushion"
            elif ratio >= 1.0:
                return "Weak debt servicing ability - minimal coverage"
            elif ratio >= 0:
                return "Very weak debt servicing ability - at risk of default"
            else:
                return "Negative coverage - unable to service debt from operations"

    def calculate_debt_service_coverage_ratio(
        self,
        operating_income: float,
        total_debt_service: float
    ) -> CalculationResult:
        """
        Calculate Debt Service Coverage Ratio for debt payment ability analysis.

        Formula: Debt Service Coverage Ratio = Operating Income / Total Debt Service

        Args:
            operating_income: Operating income (typically EBIT or EBITDA)
            total_debt_service: Total debt service (principal + interest payments)

        Returns:
            CalculationResult containing debt service coverage ratio or error information
        """
        try:
            # Input validation
            if operating_income is None or total_debt_service is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Input values cannot be None"
                )

            if total_debt_service == 0:
                return CalculationResult(
                    value=float('inf'),
                    is_valid=False,
                    error_message="Total debt service cannot be zero"
                )

            if total_debt_service < 0:
                logger.warning("Negative total debt service may indicate data errors or unusual accounting treatment")

            # Calculate debt service coverage ratio
            dscr = operating_income / total_debt_service

            # Add interpretation warnings for various scenarios
            if operating_income < 0 and total_debt_service > 0:
                logger.warning(f"Negative operating income {operating_income:.2f} with positive debt service results in negative DSCR {dscr:.2f} - indicates inability to service debt")
            elif operating_income < 0 and total_debt_service < 0:
                logger.warning(f"Both operating income and debt service are negative, resulting in DSCR {dscr:.2f} - unusual scenario")
            elif dscr < 1.0:
                logger.warning(f"Debt service coverage ratio {dscr:.2f} is below 1.0, indicating insufficient income to cover debt payments")
            elif dscr < 1.25:
                logger.warning(f"Debt service coverage ratio {dscr:.2f} is below 1.25, indicating potential difficulty in debt payment")

            return CalculationResult(
                value=dscr,
                is_valid=True,
                metadata={
                    'operating_income': operating_income,
                    'total_debt_service': total_debt_service,
                    'calculation_method': 'Debt Service Coverage Ratio = Operating Income / Total Debt Service',
                    'interpretation': self._interpret_debt_service_coverage_ratio(dscr, operating_income < 0),
                    'negative_operating_income_scenario': operating_income < 0
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Debt service coverage ratio calculation failed: {str(e)}"
            )

    def _interpret_debt_service_coverage_ratio(self, ratio: float, negative_operating_income: bool = False) -> str:
        """Provide interpretation of debt service coverage ratio value"""
        if negative_operating_income:
            return "Negative operating income - unable to service debt from operations"
        else:
            if ratio >= 2.0:
                return "Excellent debt payment ability - very strong coverage"
            elif ratio >= 1.25:
                return "Strong debt payment ability - adequate coverage"
            elif ratio >= 1.0:
                return "Moderate debt payment ability - minimal cushion"
            elif ratio >= 0.8:
                return "Weak debt payment ability - at risk of payment difficulties"
            elif ratio >= 0:
                return "Very weak debt payment ability - insufficient income to cover debt service"
            else:
                return "Negative coverage - unable to service debt from operations"

    # =====================
    # Activity/Efficiency Ratios
    # =====================

    def calculate_asset_turnover(
        self,
        revenue: float,
        total_assets: Optional[float] = None,
        average_assets: Optional[float] = None,
        beginning_assets: Optional[float] = None,
        ending_assets: Optional[float] = None
    ) -> CalculationResult:
        """
        Calculate Asset Turnover Ratio for asset efficiency analysis.

        Formula: Asset Turnover = Revenue / Average Total Assets

        The method accepts either:
        1. Pre-calculated average_assets
        2. Beginning and ending assets to calculate average
        3. Single period total_assets (less accurate but acceptable)

        Args:
            revenue: Revenue for the period
            total_assets: Total assets at period end (if no average provided)
            average_assets: Pre-calculated average total assets
            beginning_assets: Total assets at beginning of period
            ending_assets: Total assets at end of period

        Returns:
            CalculationResult containing asset turnover ratio or error information
        """
        try:
            # Input validation
            if revenue is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Revenue cannot be None"
                )

            if revenue == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            if revenue < 0:
                logger.warning("Negative revenue may indicate data errors or unusual accounting treatment")

            # Determine assets denominator using priority:
            # 1. Use provided average_assets
            # 2. Calculate from beginning_assets and ending_assets
            # 3. Use total_assets (single period)
            assets_denominator = None
            calculation_method = None

            if average_assets is not None:
                assets_denominator = average_assets
                calculation_method = "provided average assets"
            elif beginning_assets is not None and ending_assets is not None:
                assets_denominator = (beginning_assets + ending_assets) / 2
                calculation_method = "calculated average from beginning and ending assets"
                logger.info(f"Calculated average assets: {assets_denominator:.2f} from beginning: {beginning_assets:.2f} and ending: {ending_assets:.2f}")
            elif total_assets is not None:
                assets_denominator = total_assets
                calculation_method = "period-end assets (less accurate)"
                logger.warning("Using period-end assets instead of average - consider providing beginning and ending assets for more accurate calculation")
            else:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Either average_assets, (beginning_assets + ending_assets), or total_assets must be provided"
                )

            # Validate denominator
            if assets_denominator == 0:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Assets denominator cannot be zero"
                )

            if assets_denominator < 0:
                logger.warning("Negative assets may indicate financial distress or data errors")

            # Calculate asset turnover
            asset_turnover = revenue / assets_denominator

            # Add interpretation warnings
            if asset_turnover < 0.5:
                logger.warning(f"Asset turnover {asset_turnover:.2f} is very low, indicating inefficient asset utilization")
            elif asset_turnover > 3.0:
                logger.warning(f"Asset turnover {asset_turnover:.2f} is very high, may indicate exceptional efficiency or low asset base")

            return CalculationResult(
                value=asset_turnover,
                is_valid=True,
                metadata={
                    'revenue': revenue,
                    'assets_denominator': assets_denominator,
                    'total_assets': total_assets,
                    'average_assets': average_assets,
                    'beginning_assets': beginning_assets,
                    'ending_assets': ending_assets,
                    'calculation_method': f'Asset Turnover = Revenue / {calculation_method}',
                    'interpretation': self._interpret_asset_turnover(asset_turnover)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Asset turnover calculation failed: {str(e)}"
            )

    def _interpret_asset_turnover(self, ratio: float) -> str:
        """Provide interpretation of asset turnover ratio value"""
        if ratio >= 2.0:
            return "Excellent asset efficiency - high revenue generation per dollar of assets"
        elif ratio >= 1.0:
            return "Strong asset efficiency - good revenue generation"
        elif ratio >= 0.5:
            return "Moderate asset efficiency - average revenue generation"
        elif ratio >= 0.25:
            return "Low asset efficiency - below average revenue generation"
        elif ratio >= 0:
            return "Very low asset efficiency - poor revenue generation per dollar of assets"
        else:
            return "Negative asset turnover - unusual financial structure"

    def calculate_inventory_turnover(
        self,
        cogs: float,
        inventory: Optional[float] = None,
        average_inventory: Optional[float] = None,
        beginning_inventory: Optional[float] = None,
        ending_inventory: Optional[float] = None
    ) -> CalculationResult:
        """
        Calculate Inventory Turnover Ratio for inventory efficiency analysis.

        Formula: Inventory Turnover = COGS / Average Inventory

        The method accepts either:
        1. Pre-calculated average_inventory
        2. Beginning and ending inventory to calculate average
        3. Single period inventory (less accurate but acceptable)

        Args:
            cogs: Cost of Goods Sold for the period
            inventory: Inventory at period end (if no average provided)
            average_inventory: Pre-calculated average inventory
            beginning_inventory: Inventory at beginning of period
            ending_inventory: Inventory at end of period

        Returns:
            CalculationResult containing inventory turnover ratio or error information
        """
        try:
            # Input validation
            if cogs is None:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="COGS cannot be None"
                )

            if cogs < 0:
                logger.warning("Negative COGS may indicate data errors or unusual accounting treatment")

            # Determine inventory denominator using priority:
            # 1. Use provided average_inventory
            # 2. Calculate from beginning_inventory and ending_inventory
            # 3. Use inventory (single period)
            inventory_denominator = None
            calculation_method = None

            if average_inventory is not None:
                inventory_denominator = average_inventory
                calculation_method = "provided average inventory"
            elif beginning_inventory is not None and ending_inventory is not None:
                inventory_denominator = (beginning_inventory + ending_inventory) / 2
                calculation_method = "calculated average from beginning and ending inventory"
                logger.info(f"Calculated average inventory: {inventory_denominator:.2f} from beginning: {beginning_inventory:.2f} and ending: {ending_inventory:.2f}")
            elif inventory is not None:
                inventory_denominator = inventory
                calculation_method = "period-end inventory (less accurate)"
                logger.warning("Using period-end inventory instead of average - consider providing beginning and ending inventory for more accurate calculation")
            else:
                return CalculationResult(
                    value=0.0,
                    is_valid=False,
                    error_message="Either average_inventory, (beginning_inventory + ending_inventory), or inventory must be provided"
                )

            # Handle zero inventory (service companies or just-in-time inventory)
            if inventory_denominator == 0:
                if cogs == 0:
                    return CalculationResult(
                        value=0.0,
                        is_valid=True,
                        metadata={
                            'cogs': cogs,
                            'inventory_denominator': inventory_denominator,
                            'calculation_method': 'N/A - Zero inventory and zero COGS (likely service company)',
                            'interpretation': 'Service company or no inventory model'
                        }
                    )
                else:
                    return CalculationResult(
                        value=float('inf'),
                        is_valid=True,
                        metadata={
                            'cogs': cogs,
                            'inventory_denominator': inventory_denominator,
                            'calculation_method': 'N/A - Zero inventory with positive COGS',
                            'interpretation': 'Infinite turnover - likely just-in-time or service business model'
                        }
                    )

            if inventory_denominator < 0:
                logger.warning("Negative inventory may indicate data errors or inventory write-downs")

            # Calculate inventory turnover
            inventory_turnover = cogs / inventory_denominator

            # Add interpretation warnings
            if inventory_turnover < 2.0:
                logger.warning(f"Inventory turnover {inventory_turnover:.2f} is low, may indicate slow-moving inventory or overstocking")
            elif inventory_turnover > 20.0:
                logger.warning(f"Inventory turnover {inventory_turnover:.2f} is very high, may indicate strong efficiency or potential stockouts")

            return CalculationResult(
                value=inventory_turnover,
                is_valid=True,
                metadata={
                    'cogs': cogs,
                    'inventory_denominator': inventory_denominator,
                    'inventory': inventory,
                    'average_inventory': average_inventory,
                    'beginning_inventory': beginning_inventory,
                    'ending_inventory': ending_inventory,
                    'calculation_method': f'Inventory Turnover = COGS / {calculation_method}',
                    'interpretation': self._interpret_inventory_turnover(inventory_turnover)
                }
            )

        except Exception as e:
            return CalculationResult(
                value=0.0,
                is_valid=False,
                error_message=f"Inventory turnover calculation failed: {str(e)}"
            )

    def _interpret_inventory_turnover(self, ratio: float) -> str:
        """Provide interpretation of inventory turnover ratio value"""
        if ratio >= 12.0:
            return "Excellent inventory management - very fast turnover"
        elif ratio >= 6.0:
            return "Strong inventory management - good turnover"
        elif ratio >= 4.0:
            return "Moderate inventory management - average turnover"
        elif ratio >= 2.0:
            return "Low inventory turnover - potential overstocking"
        elif ratio >= 0:
            return "Very low inventory turnover - slow-moving inventory or obsolescence risk"
        else:
            return "Negative inventory turnover - unusual inventory accounting"