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