"""
Calculation Engine Integration Example
=====================================

This example demonstrates how existing modules can be updated to use the new
Financial Calculation Engine while maintaining backward compatibility.

Example shows:
1. How to refactor existing calculation methods to use the engine
2. How to maintain the same API while using pure calculation functions
3. Error handling and validation integration
4. Performance improvements from isolated calculations
"""

from typing import List, Dict, Any, Optional
import logging

from financial_calculation_engine import FinancialCalculationEngine, CalculationResult

logger = logging.getLogger(__name__)


class ModernizedFinancialCalculator:
    """
    Example of how to refactor an existing financial calculator to use
    the new calculation engine while maintaining the original API.
    """
    
    def __init__(self, ticker_symbol: str):
        """Initialize with calculation engine"""
        self.ticker_symbol = ticker_symbol
        self.calculation_engine = FinancialCalculationEngine()
        
        # Store calculation results for reuse
        self.fcf_results = {}
        self.validation_enabled = True
        self.financial_scale_factor = 1.0  # For backward compatibility
    
    def calculate_fcf_to_firm(self) -> List[float]:
        """
        REFACTORED: Calculate FCFF using the pure calculation engine.
        
        This method maintains the same API as the original but delegates
        mathematical calculations to the engine.
        """
        try:
            # Get pre-calculated metrics (original data extraction logic)
            metrics = self._get_metrics_from_data_sources()
            if not metrics:
                logger.warning("No metrics available for FCFF calculation")
                return []
            
            # Extract required components
            ebit_values = metrics.get('ebit', [])
            tax_rates = metrics.get('tax_rates', [])
            da_values = metrics.get('depreciation_amortization', [])
            capex_values = metrics.get('capex', [])
            working_capital_changes = metrics.get('working_capital_changes', [])
            
            # Use the calculation engine for pure mathematical computation
            result = self.calculation_engine.calculate_fcf_to_firm(
                ebit_values=ebit_values,
                tax_rates=tax_rates,
                depreciation_values=da_values,
                working_capital_changes=working_capital_changes,
                capex_values=capex_values
            )
            
            # Handle result from engine
            if not result.is_valid:
                logger.error(f"FCFF calculation failed: {result.error_message}")
                return []
            
            # Apply business logic (scaling, storage, etc.)
            scaled_values = [value * self.financial_scale_factor for value in result.value]
            self.fcf_results['FCFF'] = scaled_values
            
            logger.info(f"FCFF calculated using engine: {len(result.value)} periods")
            return scaled_values
            
        except Exception as e:
            logger.error(f"Error in FCFF calculation: {e}")
            return []
    
    def calculate_all_fcf_types(self) -> Dict[str, List[float]]:
        """
        Calculate all FCF types using the calculation engine.
        Shows how multiple calculations can use the engine efficiently.
        """
        try:
            metrics = self._get_metrics_from_data_sources()
            if not metrics:
                return {}
            
            results = {}
            
            # Calculate FCFF using engine
            fcff_result = self.calculation_engine.calculate_fcf_to_firm(
                ebit_values=metrics.get('ebit', []),
                tax_rates=metrics.get('tax_rates', []),
                depreciation_values=metrics.get('depreciation_amortization', []),
                working_capital_changes=metrics.get('working_capital_changes', []),
                capex_values=metrics.get('capex', [])
            )
            
            if fcff_result.is_valid:
                results['FCFF'] = [v * self.financial_scale_factor for v in fcff_result.value]
                logger.info(f"FCFF: {fcff_result.metadata['periods_calculated']} periods")
            
            # Calculate FCFE using engine
            fcfe_result = self.calculation_engine.calculate_fcf_to_equity(
                net_income_values=metrics.get('net_income', []),
                depreciation_values=metrics.get('depreciation_amortization', []),
                working_capital_changes=metrics.get('working_capital_changes', []),
                capex_values=metrics.get('capex', []),
                net_borrowing_values=metrics.get('net_borrowing', [])
            )
            
            if fcfe_result.is_valid:
                results['FCFE'] = [v * self.financial_scale_factor for v in fcfe_result.value]
                logger.info(f"FCFE: {fcfe_result.metadata['periods_calculated']} periods")
            
            # Calculate LFCF using engine
            lfcf_result = self.calculation_engine.calculate_levered_fcf(
                operating_cash_flow_values=metrics.get('operating_cash_flow', []),
                capex_values=metrics.get('capex', [])
            )
            
            if lfcf_result.is_valid:
                results['LFCF'] = [v * self.financial_scale_factor for v in lfcf_result.value]
                logger.info(f"LFCF: {lfcf_result.metadata['periods_calculated']} periods")
            
            # Store for reuse
            self.fcf_results.update(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating FCF types: {e}")
            return {}
    
    def calculate_growth_rates(self, values: List[float], periods: List[int] = None) -> Dict[str, float]:
        """
        Calculate growth rates using the engine's CAGR function.
        Shows how utility functions can be leveraged.
        """
        if not values or len(values) < 2:
            return {}
        
        if periods is None:
            periods = [1, 3, 5]
        
        growth_rates = {}
        
        for period in periods:
            if len(values) > period:
                start_value = values[-period - 1]  # Start from period+1 ago
                end_value = values[-1]  # Most recent value
                
                # Use engine for CAGR calculation
                result = self.calculation_engine.calculate_cagr(
                    start_value=start_value,
                    end_value=end_value,
                    periods=period
                )
                
                if result.is_valid:
                    growth_rates[f'{period}_year'] = result.value
                    logger.info(f"{period}-year CAGR: {result.value:.1%}")
                else:
                    logger.warning(f"{period}-year CAGR failed: {result.error_message}")
        
        return growth_rates
    
    def _get_metrics_from_data_sources(self) -> Dict[str, List[float]]:
        """
        Mock method representing data extraction from various sources.
        In practice, this would contain the original data loading logic.
        """
        # This would contain the original complex data extraction logic
        # For demonstration, return sample data
        return {
            'ebit': [100.0, 110.0, 121.0, 133.1, 146.4],
            'tax_rates': [0.25, 0.25, 0.25, 0.25, 0.25],
            'depreciation_amortization': [10.0, 11.0, 12.1, 13.3, 14.6],
            'working_capital_changes': [5.0, 5.5, 6.1, 6.7, 7.4],
            'capex': [20.0, 22.0, 24.2, 26.6, 29.3],
            'net_income': [75.0, 82.5, 90.8, 99.9, 109.9],
            'operating_cash_flow': [95.0, 104.5, 115.0, 126.5, 139.2],
            'net_borrowing': [5.0, 3.0, 2.0, -1.0, -2.0]
        }


class ModernizedDCFValuator:
    """
    Example of how DCF valuation can be refactored to use the calculation engine.
    """
    
    def __init__(self, financial_calculator):
        self.financial_calculator = financial_calculator
        self.calculation_engine = FinancialCalculationEngine()
    
    def calculate_dcf_valuation(
        self,
        fcf_values: List[float],
        discount_rate: float = 0.10,
        terminal_growth_rate: float = 0.03
    ) -> Dict[str, Any]:
        """
        Calculate DCF valuation using the calculation engine.
        
        Shows how complex valuations can leverage multiple engine functions.
        """
        try:
            if not fcf_values:
                return {'error': 'No FCF values provided'}
            
            # Use most recent FCF as base for projections (simplified example)
            base_fcf = fcf_values[-1]
            
            # Project future cash flows (simplified 5-year projection)
            projected_growth_rates = [0.10, 0.08, 0.06, 0.05, 0.04]  # Declining growth
            projected_fcf = []
            current_fcf = base_fcf
            
            for growth_rate in projected_growth_rates:
                current_fcf *= (1 + growth_rate)
                projected_fcf.append(current_fcf)
            
            # Calculate present values using engine
            pv_result = self.calculation_engine.calculate_present_value(
                future_cash_flows=projected_fcf,
                discount_rate=discount_rate
            )
            
            if not pv_result.is_valid:
                return {'error': f'Present value calculation failed: {pv_result.error_message}'}
            
            # Calculate terminal value using engine
            terminal_result = self.calculation_engine.calculate_terminal_value(
                final_cash_flow=projected_fcf[-1],
                growth_rate=terminal_growth_rate,
                discount_rate=discount_rate
            )
            
            if not terminal_result.is_valid:
                return {'error': f'Terminal value calculation failed: {terminal_result.error_message}'}
            
            # Calculate present value of terminal value
            terminal_years = len(projected_fcf)
            terminal_pv = terminal_result.value / ((1 + discount_rate) ** terminal_years)
            
            # Sum all present values
            total_pv_operations = sum(pv_result.value)
            total_enterprise_value = total_pv_operations + terminal_pv
            
            return {
                'base_fcf': base_fcf,
                'projected_fcf': projected_fcf,
                'present_values': pv_result.value,
                'terminal_value': terminal_result.value,
                'terminal_pv': terminal_pv,
                'total_pv_operations': total_pv_operations,
                'enterprise_value': total_enterprise_value,
                'discount_rate': discount_rate,
                'terminal_growth_rate': terminal_growth_rate,
                'calculation_metadata': {
                    'pv_metadata': pv_result.metadata,
                    'terminal_metadata': terminal_result.metadata
                }
            }
            
        except Exception as e:
            return {'error': f'DCF calculation failed: {str(e)}'}


def integration_example():
    """
    Demonstrate the integration and benefits of the calculation engine.
    """
    print("=== Financial Calculation Engine Integration Example ===\n")
    
    # Initialize modernized calculator
    calc = ModernizedFinancialCalculator("AAPL")
    
    # Calculate FCF using engine
    print("1. Calculating FCFF using engine:")
    fcff_values = calc.calculate_fcf_to_firm()
    print(f"   FCFF Values: {[f'{v:.1f}M' for v in fcff_values]}\n")
    
    # Calculate all FCF types
    print("2. Calculating all FCF types:")
    all_fcf = calc.calculate_all_fcf_types()
    for fcf_type, values in all_fcf.items():
        print(f"   {fcf_type}: {[f'{v:.1f}M' for v in values]}")
    print()
    
    # Calculate growth rates
    print("3. Calculating growth rates using engine:")
    growth_rates = calc.calculate_growth_rates(fcff_values)
    for period, rate in growth_rates.items():
        print(f"   {period} CAGR: {rate:.1%}")
    print()
    
    # DCF valuation using engine
    print("4. DCF Valuation using engine:")
    dcf = ModernizedDCFValuator(calc)
    dcf_result = dcf.calculate_dcf_valuation(fcff_values)
    
    if 'error' not in dcf_result:
        print(f"   Enterprise Value: ${dcf_result['enterprise_value']:.1f}M")
        print(f"   Terminal Value: ${dcf_result['terminal_value']:.1f}M")
        print(f"   Operations PV: ${dcf_result['total_pv_operations']:.1f}M")
    else:
        print(f"   Error: {dcf_result['error']}")
    
    print("\n=== Benefits of Using Calculation Engine ===")
    print("✓ Pure mathematical functions - easy to test")
    print("✓ Consistent error handling across all calculations")
    print("✓ Detailed metadata for each calculation")
    print("✓ Mathematical validation built-in")
    print("✓ Reusable across different valuation models")
    print("✓ Performance optimized for large datasets")


if __name__ == "__main__":
    integration_example()