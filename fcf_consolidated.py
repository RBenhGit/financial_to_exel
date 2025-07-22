"""
Consolidated FCF Calculations Module

This module consolidates all FCF-related calculations to eliminate
duplicate code and ensure consistent calculations across the application.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from config import get_dcf_config

logger = logging.getLogger(__name__)

class FCFCalculator:
    """
    Consolidated FCF calculator that handles all FCF calculation types
    and related metrics consistently across the application.
    """
    
    def __init__(self):
        """Initialize the FCF calculator"""
        self.dcf_config = get_dcf_config()
    
    def calculate_fcf_growth_rates(self, fcf_results: Dict[str, List[float]], periods: List[int] = None) -> Dict[str, Dict[str, float]]:
        """
        Calculate FCF growth rates for all FCF types across different periods
        
        Args:
            fcf_results (Dict[str, List[float]]): FCF results by type
            periods (List[int]): List of periods to calculate growth rates for
            
        Returns:
            Dict[str, Dict[str, float]]: Growth rates by FCF type and period
        """
        if periods is None:
            periods = self.dcf_config.growth_rate_periods
        
        growth_rates = {}
        
        # Calculate for each FCF type
        for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
            if fcf_type in fcf_results and fcf_results[fcf_type]:
                values = fcf_results[fcf_type]
                growth_rates[fcf_type] = self._calculate_growth_rates_for_values(values, periods)
        
        # Calculate average growth rates
        if growth_rates:
            growth_rates['Average'] = self._calculate_average_growth_rates(growth_rates, periods)
        
        return growth_rates
    
    def _calculate_growth_rates_for_values(self, values: List[float], periods: List[int]) -> Dict[str, float]:
        """
        Calculate growth rates for a specific set of values
        
        Args:
            values (List[float]): FCF values
            periods (List[int]): Periods to calculate growth rates for
            
        Returns:
            Dict[str, float]: Growth rates by period
        """
        growth_rates = {}
        
        for period in periods:
            if len(values) >= period + 1:
                try:
                    start_value = values[-(period + 1)]
                    end_value = values[-1]
                    
                    if start_value != 0 and start_value is not None and end_value is not None:
                        # Calculate annualized growth rate
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        # Handle negative cash flows
                        if end_value < 0 and start_value > 0:
                            growth_rate = -growth_rate
                        elif end_value > 0 and start_value < 0:
                            growth_rate = abs(growth_rate)
                        
                        growth_rates[f'{period}yr'] = growth_rate
                    else:
                        growth_rates[f'{period}yr'] = None
                except Exception as e:
                    logger.warning(f"Error calculating {period}yr growth rate: {e}")
                    growth_rates[f'{period}yr'] = None
            else:
                growth_rates[f'{period}yr'] = None
        
        return growth_rates
    
    def _calculate_average_growth_rates(self, growth_rates: Dict[str, Dict[str, float]], periods: List[int]) -> Dict[str, float]:
        """
        Calculate average growth rates across all FCF types
        
        Args:
            growth_rates (Dict[str, Dict[str, float]]): Growth rates by FCF type
            periods (List[int]): Periods to calculate averages for
            
        Returns:
            Dict[str, float]: Average growth rates by period
        """
        average_growth_rates = {}
        
        for period in periods:
            period_key = f'{period}yr'
            period_rates = []
            
            for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
                if fcf_type in growth_rates and period_key in growth_rates[fcf_type]:
                    rate = growth_rates[fcf_type][period_key]
                    if rate is not None:
                        period_rates.append(rate)
            
            if period_rates:
                average_growth_rates[period_key] = sum(period_rates) / len(period_rates)
            else:
                average_growth_rates[period_key] = None
        
        return average_growth_rates
    
    def calculate_fcf_metrics_summary(self, fcf_results: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Calculate comprehensive FCF metrics summary
        
        Args:
            fcf_results (Dict[str, List[float]]): FCF results by type
            
        Returns:
            Dict[str, Any]: Comprehensive FCF metrics
        """
        summary = {
            'latest_values': {},
            'growth_rates': {},
            'statistics': {},
            'average_fcf': {}
        }
        
        # Calculate latest values
        for fcf_type, values in fcf_results.items():
            if values:
                summary['latest_values'][fcf_type] = values[-1]
        
        # Calculate growth rates
        summary['growth_rates'] = self.calculate_fcf_growth_rates(fcf_results)
        
        # Calculate statistics
        for fcf_type, values in fcf_results.items():
            if values:
                summary['statistics'][fcf_type] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'count': len(values)
                }
        
        # Calculate average FCF across all methods
        summary['average_fcf'] = self._calculate_average_fcf_series(fcf_results)
        
        return summary
    
    def _calculate_average_fcf_series(self, fcf_results: Dict[str, List[float]]) -> List[float]:
        """
        Calculate average FCF across all calculation methods for each year
        
        Args:
            fcf_results (Dict[str, List[float]]): FCF results by type
            
        Returns:
            List[float]: Average FCF values by year
        """
        if not fcf_results:
            return []
        
        # Get the maximum length to determine the number of years
        max_length = max(len(values) for values in fcf_results.values() if values)
        
        average_fcf = []
        for i in range(max_length):
            year_values = []
            for fcf_type, values in fcf_results.items():
                if values and i < len(values) and values[i] is not None:
                    year_values.append(values[i])
            
            if year_values:
                average_fcf.append(sum(year_values) / len(year_values))
            else:
                average_fcf.append(None)
        
        return average_fcf
    
    def format_fcf_data_for_display(self, fcf_results: Dict[str, List[float]], years: List[int] = None) -> pd.DataFrame:
        """
        Format FCF data for display in tables and charts
        
        Args:
            fcf_results (Dict[str, List[float]]): FCF results by type
            years (List[int]): Years corresponding to the data
            
        Returns:
            pd.DataFrame: Formatted FCF data
        """
        if not fcf_results:
            return pd.DataFrame()
        
        # Determine years if not provided
        if years is None:
            max_length = max(len(values) for values in fcf_results.values() if values)
            from datetime import datetime
            current_year = datetime.now().year
            years = list(range(current_year - max_length + 1, current_year + 1))
        
        # Prepare data for DataFrame
        data = {'Year': years}
        
        # Add FCF columns
        for fcf_type, values in fcf_results.items():
            if values:
                # Pad or truncate values to match years length
                if len(values) < len(years):
                    padded_values = [None] * (len(years) - len(values)) + values
                else:
                    padded_values = values[-len(years):]
                
                data[f'{fcf_type} ($M)'] = padded_values
        
        # Add average FCF column
        average_fcf = self._calculate_average_fcf_series(fcf_results)
        if average_fcf:
            if len(average_fcf) < len(years):
                padded_avg = [None] * (len(years) - len(average_fcf)) + average_fcf
            else:
                padded_avg = average_fcf[-len(years):]
            
            data['Average FCF ($M)'] = padded_avg
        
        return pd.DataFrame(data)
    
    def get_fcf_recommendation(self, fcf_results: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Get FCF-based investment recommendation
        
        Args:
            fcf_results (Dict[str, List[float]]): FCF results by type
            
        Returns:
            Dict[str, Any]: FCF recommendation analysis
        """
        recommendation = {
            'overall_trend': 'neutral',
            'growth_quality': 'fair',
            'consistency': 'moderate',
            'recommendation': 'hold',
            'key_metrics': {},
            'warnings': []
        }
        
        if not fcf_results:
            recommendation['warnings'].append("No FCF data available for analysis")
            return recommendation
        
        # Calculate key metrics
        metrics = self.calculate_fcf_metrics_summary(fcf_results)
        recommendation['key_metrics'] = metrics
        
        # Analyze trends
        growth_rates = metrics['growth_rates']
        if 'Average' in growth_rates:
            avg_growth = growth_rates['Average']
            
            # Check 5-year growth if available
            if '5yr' in avg_growth and avg_growth['5yr'] is not None:
                five_year_growth = avg_growth['5yr']
                if five_year_growth > 0.15:  # >15% growth
                    recommendation['overall_trend'] = 'positive'
                    recommendation['growth_quality'] = 'excellent'
                elif five_year_growth > 0.05:  # >5% growth
                    recommendation['overall_trend'] = 'positive'
                    recommendation['growth_quality'] = 'good'
                elif five_year_growth > 0:  # Positive growth
                    recommendation['overall_trend'] = 'positive'
                    recommendation['growth_quality'] = 'fair'
                else:  # Negative growth
                    recommendation['overall_trend'] = 'negative'
                    recommendation['growth_quality'] = 'poor'
        
        # Check consistency
        latest_values = metrics['latest_values']
        if len(latest_values) >= 2:
            fcf_range = max(latest_values.values()) - min(latest_values.values())
            avg_fcf = sum(latest_values.values()) / len(latest_values)
            
            if avg_fcf > 0:
                variability = fcf_range / avg_fcf
                if variability < 0.2:  # Low variability
                    recommendation['consistency'] = 'high'
                elif variability < 0.5:  # Moderate variability
                    recommendation['consistency'] = 'moderate'
                else:  # High variability
                    recommendation['consistency'] = 'low'
                    recommendation['warnings'].append("High variability between FCF calculation methods")
        
        # Generate final recommendation
        if recommendation['overall_trend'] == 'positive' and recommendation['consistency'] == 'high':
            recommendation['recommendation'] = 'buy'
        elif recommendation['overall_trend'] == 'negative' or recommendation['consistency'] == 'low':
            recommendation['recommendation'] = 'sell'
        else:
            recommendation['recommendation'] = 'hold'
        
        return recommendation

# Utility functions for backward compatibility
def calculate_fcf_growth_rates(fcf_results: Dict[str, List[float]], periods: List[int] = None) -> Dict[str, Dict[str, float]]:
    """
    Utility function for calculating FCF growth rates
    
    Args:
        fcf_results (Dict[str, List[float]]): FCF results by type
        periods (List[int]): Periods to calculate growth rates for
        
    Returns:
        Dict[str, Dict[str, float]]: Growth rates by FCF type and period
    """
    calculator = FCFCalculator()
    return calculator.calculate_fcf_growth_rates(fcf_results, periods)

def format_fcf_data_for_display(fcf_results: Dict[str, List[float]], years: List[int] = None) -> pd.DataFrame:
    """
    Utility function for formatting FCF data for display
    
    Args:
        fcf_results (Dict[str, List[float]]): FCF results by type
        years (List[int]): Years corresponding to the data
        
    Returns:
        pd.DataFrame: Formatted FCF data
    """
    calculator = FCFCalculator()
    return calculator.format_fcf_data_for_display(fcf_results, years)

def get_fcf_recommendation(fcf_results: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Utility function for getting FCF-based recommendation
    
    Args:
        fcf_results (Dict[str, List[float]]): FCF results by type
        
    Returns:
        Dict[str, Any]: FCF recommendation analysis
    """
    calculator = FCFCalculator()
    return calculator.get_fcf_recommendation(fcf_results)

if __name__ == "__main__":
    # Test the consolidated FCF calculator
    sample_fcf_results = {
        'LFCF': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        'FCFE': [900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800],
        'FCFF': [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    }
    
    calculator = FCFCalculator()
    
    # Test growth rate calculation
    growth_rates = calculator.calculate_fcf_growth_rates(sample_fcf_results)
    print("Growth rates:", growth_rates)
    
    # Test metrics summary
    metrics = calculator.calculate_fcf_metrics_summary(sample_fcf_results)
    print("Metrics summary:", metrics)
    
    # Test formatting
    df = calculator.format_fcf_data_for_display(sample_fcf_results)
    print("Formatted data:\n", df)
    
    # Test recommendation
    recommendation = calculator.get_fcf_recommendation(sample_fcf_results)
    print("Recommendation:", recommendation)