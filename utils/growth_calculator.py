"""
Unified Growth Rate Calculator

This module consolidates all growth rate calculation logic that was duplicated
across multiple files (data_processing.py, financial_calculations.py, 
fcf_consolidated.py, centralized_data_processor.py, dcf_valuation.py).
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Any, Union

logger = logging.getLogger(__name__)


class GrowthRateCalculator:
    """
    Centralized calculator for all types of growth rates in the financial analysis system.
    
    This class eliminates the duplicate growth rate calculation logic found across
    5+ different modules in the original codebase.
    """
    
    def __init__(self):
        """Initialize the growth rate calculator"""
        self.default_periods = [1, 3, 5, 10]  # Standard growth rate periods
        
    def calculate_cagr(self, start_value: Union[float, int], end_value: Union[float, int], 
                      periods: Union[float, int]) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate (CAGR) between two values
        
        Args:
            start_value: Starting value
            end_value: Ending value  
            periods: Number of periods
            
        Returns:
            CAGR as decimal (e.g., 0.1 for 10%) or None if calculation impossible
        """
        try:
            # Handle edge cases
            if start_value is None or end_value is None or periods is None:
                return None
            
            if periods <= 0:
                return None
            
            if start_value == 0:
                return None  # Division by zero
            
            # Convert to absolute values for calculation
            abs_start = abs(start_value)
            abs_end = abs(end_value)
            
            # Calculate base growth rate
            growth_rate = (abs_end / abs_start) ** (1 / periods) - 1
            
            # Handle sign changes (negative cash flows, etc.)
            if self._values_have_opposite_signs(start_value, end_value):
                growth_rate = -growth_rate
            elif start_value < 0 and end_value < 0:
                # Both negative: use absolute value of growth rate  
                growth_rate = abs(growth_rate)
            
            return growth_rate
            
        except Exception as e:
            logger.warning(f"Error calculating CAGR: {e}")
            return None
    
    def calculate_growth_rates_for_series(self, values: List[Union[float, int]], 
                                        periods: Optional[List[int]] = None) -> Dict[str, Optional[float]]:
        """
        Calculate growth rates for a time series of values over different periods
        
        Args:
            values: List of time series values (earliest to latest)
            periods: List of periods to calculate growth rates for
            
        Returns:
            Dictionary mapping period strings (e.g., '1yr', '3yr') to growth rates
        """
        if periods is None:
            periods = self.default_periods
            
        growth_rates = {}
        
        if not values or len(values) < 2:
            # Insufficient data for growth calculations
            return {f'{period}yr': None for period in periods}
        
        for period in periods:
            if len(values) >= period + 1:
                # Get values for this period calculation
                start_value = values[-(period + 1)]  # period + 1 positions from end
                end_value = values[-1]              # Latest value
                
                cagr = self.calculate_cagr(start_value, end_value, period)
                growth_rates[f'{period}yr'] = cagr
            else:
                # Not enough data for this period
                growth_rates[f'{period}yr'] = None
        
        return growth_rates
    
    def calculate_fcf_growth_rates(self, fcf_data: Dict[str, List[Union[float, int]]], 
                                  periods: Optional[List[int]] = None) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Calculate growth rates for all FCF types
        
        This method consolidates the FCF growth rate logic found in:
        - data_processing.py
        - fcf_consolidated.py  
        - centralized_data_processor.py
        
        Args:
            fcf_data: Dictionary mapping FCF types to value lists
            periods: List of periods to calculate for
            
        Returns:
            Nested dictionary: fcf_type -> period -> growth_rate
        """
        if periods is None:
            periods = self.default_periods
            
        growth_rates = {}
        
        # Calculate for each FCF type
        for fcf_type, values in fcf_data.items():
            if values:  # Only process non-empty value lists
                growth_rates[fcf_type] = self.calculate_growth_rates_for_series(values, periods)
        
        # Calculate average growth rates across FCF types
        if growth_rates:
            growth_rates['Average'] = self._calculate_average_growth_rates(growth_rates, periods)
        
        return growth_rates
    
    def calculate_historical_growth_rates(self, financial_metrics: Dict[str, List[Union[float, int]]], 
                                        periods: Optional[List[int]] = None) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Calculate historical growth rates for financial metrics
        
        Args:
            financial_metrics: Dictionary mapping metric names to historical values
            periods: Periods to calculate growth rates for
            
        Returns:
            Nested dictionary: metric_name -> period -> growth_rate
        """
        if periods is None:
            periods = self.default_periods
            
        growth_rates = {}
        
        for metric_name, values in financial_metrics.items():
            growth_rates[metric_name] = self.calculate_growth_rates_for_series(values, periods)
        
        return growth_rates
    
    def _calculate_average_growth_rates(self, growth_rates: Dict[str, Dict[str, Optional[float]]], 
                                      periods: List[int]) -> Dict[str, Optional[float]]:
        """
        Calculate average growth rates across multiple series
        
        Args:
            growth_rates: Growth rates by series and period
            periods: List of periods
            
        Returns:
            Dictionary mapping period strings to average growth rates
        """
        average_growth_rates = {}
        
        # Exclude 'Average' key if it already exists to avoid recursion
        data_keys = [key for key in growth_rates.keys() if key != 'Average']
        
        for period in periods:
            period_key = f'{period}yr'
            period_rates = []
            
            for series_name in data_keys:
                if series_name in growth_rates and period_key in growth_rates[series_name]:
                    rate = growth_rates[series_name][period_key]
                    if rate is not None and np.isfinite(rate):
                        period_rates.append(rate)
            
            if period_rates:
                average_growth_rates[period_key] = sum(period_rates) / len(period_rates)
            else:
                average_growth_rates[period_key] = None
        
        return average_growth_rates
    
    def _values_have_opposite_signs(self, value1: Union[float, int], value2: Union[float, int]) -> bool:
        """
        Check if two values have opposite signs
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            True if values have opposite signs
        """
        if value1 is None or value2 is None:
            return False
        
        return (value1 > 0 and value2 < 0) or (value1 < 0 and value2 > 0)
    
    def validate_growth_rate(self, growth_rate: Optional[float], 
                           min_reasonable: float = -0.9,  # -90%
                           max_reasonable: float = 5.0)   -> bool:  # 500%
        """
        Validate that a calculated growth rate is reasonable
        
        Args:
            growth_rate: Growth rate to validate
            min_reasonable: Minimum reasonable growth rate
            max_reasonable: Maximum reasonable growth rate
            
        Returns:
            True if growth rate is reasonable
        """
        if growth_rate is None:
            return True  # None is acceptable (insufficient data)
        
        if not isinstance(growth_rate, (int, float)):
            return False
        
        if not np.isfinite(growth_rate):
            return False  # NaN or infinite
        
        return min_reasonable <= growth_rate <= max_reasonable
    
    def get_growth_rate_statistics(self, growth_rates: Dict[str, Optional[float]]) -> Dict[str, Any]:
        """
        Calculate statistics for a set of growth rates
        
        Args:
            growth_rates: Dictionary of growth rates by period
            
        Returns:
            Dictionary with statistics (mean, median, std, etc.)
        """
        # Filter out None values
        valid_rates = [rate for rate in growth_rates.values() if rate is not None and np.isfinite(rate)]
        
        if not valid_rates:
            return {
                'count': 0,
                'mean': None,
                'median': None,
                'std': None,
                'min': None,
                'max': None
            }
        
        return {
            'count': len(valid_rates),
            'mean': np.mean(valid_rates),
            'median': np.median(valid_rates),
            'std': np.std(valid_rates),
            'min': np.min(valid_rates),
            'max': np.max(valid_rates)
        }
    
    def format_growth_rate(self, growth_rate: Optional[float], 
                          as_percentage: bool = True,
                          decimal_places: int = 1) -> str:
        """
        Format growth rate for display
        
        Args:
            growth_rate: Growth rate to format
            as_percentage: Whether to display as percentage
            decimal_places: Number of decimal places
            
        Returns:
            Formatted string
        """
        if growth_rate is None:
            return "N/A"
        
        if not np.isfinite(growth_rate):
            return "N/A"
        
        if as_percentage:
            return f"{growth_rate * 100:.{decimal_places}f}%"
        else:
            return f"{growth_rate:.{decimal_places}f}"