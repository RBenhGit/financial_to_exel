"""
Registry Integration Adapter
===========================

This module provides integration between the Universal Data Registry and existing 
calculation modules. It acts as a bridge layer that allows gradual migration from
the current data access patterns to the centralized registry system.

Classes:
    RegistryIntegrationAdapter: Main adapter for integrating with existing modules
    LegacyDataInterface: Compatibility layer for legacy data access patterns
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from core.data_processing.universal_data_registry import (
    UniversalDataRegistry, DataRequest, DataResponse, 
    CachePolicy, ValidationLevel, get_registry
)
from core.data_sources.interfaces.data_source_interfaces import DataSourceType

logger = logging.getLogger(__name__)

class RegistryIntegrationAdapter:
    """
    Adapter class that provides integration between the Universal Data Registry
    and existing calculation modules, enabling gradual migration.
    """
    
    def __init__(self, registry: UniversalDataRegistry = None):
        """Initialize the integration adapter"""
        self.registry = registry or get_registry()
        self.legacy_mode = False  # Flag to enable legacy fallback
        
        # Track integration metrics
        self.registry_calls = 0
        self.legacy_fallbacks = 0
        
    def get_financial_data(self, symbol: str, company_folder: str = None, 
                          data_types: List[str] = None) -> Dict[str, Any]:
        """
        Get financial data with automatic fallback to legacy systems.
        
        This method attempts to use the Universal Data Registry first,
        falling back to existing methods if needed for compatibility.
        
        Args:
            symbol: Stock symbol
            company_folder: Path to company data folder (for Excel fallback)
            data_types: List of specific data types to retrieve
            
        Returns:
            Dictionary containing financial data in legacy format
        """
        try:
            # Attempt to use Universal Data Registry
            return self._get_data_via_registry(symbol, company_folder, data_types)
            
        except Exception as e:
            logger.warning(f"Registry failed for {symbol}, falling back to legacy: {e}")
            self.legacy_fallbacks += 1
            
            # Fallback to legacy data loading
            return self._get_data_via_legacy(symbol, company_folder, data_types)
    
    def _get_data_via_registry(self, symbol: str, company_folder: str = None,
                              data_types: List[str] = None) -> Dict[str, Any]:
        """Get data using the Universal Data Registry"""
        self.registry_calls += 1
        
        # Default data types if not specified
        if data_types is None:
            data_types = ['financial_statements']
        
        # Configure registry data source if company folder is provided
        if company_folder:
            self._configure_excel_source(company_folder)
        
        combined_data = {}
        
        for data_type in data_types:
            try:
                # Create data request
                request = DataRequest(
                    data_type=data_type,
                    symbol=symbol,
                    period='annual',  # Default to annual
                    cache_policy=CachePolicy.DEFAULT,
                    validation_level=ValidationLevel.STANDARD
                )
                
                # Fetch data through registry
                response = self.registry.get_data(request)
                
                if response and response.data:
                    combined_data[data_type] = response.data
                    
                    # Store metadata for lineage tracking
                    combined_data[f'{data_type}_metadata'] = {
                        'source': response.source.value,
                        'timestamp': response.timestamp,
                        'quality_score': response.quality_score,
                        'cache_hit': response.cache_hit
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to get {data_type} for {symbol}: {e}")
                continue
        
        # Convert to legacy format
        return self._convert_to_legacy_format(combined_data, symbol)
    
    def _configure_excel_source(self, company_folder: str):
        """Configure Excel data source with company folder"""
        try:
            # Update Excel source configuration
            excel_source = self.registry.data_sources.get(DataSourceType.EXCEL)
            if excel_source and hasattr(excel_source, 'company_folder'):
                excel_source.company_folder = os.path.dirname(company_folder)
        except Exception as e:
            logger.warning(f"Failed to configure Excel source: {e}")
    
    def _get_data_via_legacy(self, symbol: str, company_folder: str = None,
                            data_types: List[str] = None) -> Dict[str, Any]:
        """Fallback to legacy data loading methods"""
        try:
            # Import here to avoid circular dependencies
            from core.analysis.engines.financial_calculations import FinancialCalculator
            
            # Create legacy calculator
            calculator = FinancialCalculator(
                company_folder=company_folder,
                symbol=symbol
            )
            
            # Load data using legacy methods
            calculator.load_financial_statements()
            
            # Extract data in legacy format
            return {
                'income_statement': getattr(calculator, 'income_statement_data', {}),
                'balance_sheet': getattr(calculator, 'balance_sheet_data', {}),
                'cash_flow': getattr(calculator, 'cash_flow_data', {}),
                'data_point_dates': getattr(calculator, 'data_point_dates', {}),
                'source': 'legacy',
                'calculator_instance': calculator
            }
            
        except Exception as e:
            logger.error(f"Legacy fallback failed for {symbol}: {e}")
            return {}
    
    def _convert_to_legacy_format(self, registry_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Convert registry response format to legacy format"""
        legacy_data = {
            'symbol': symbol,
            'source': 'registry',
            'timestamp': datetime.now()
        }
        
        # Extract financial statements if available
        if 'financial_statements' in registry_data:
            statements = registry_data['financial_statements']
            legacy_data.update({
                'income_statement': statements.get('income_statement', {}),
                'balance_sheet': statements.get('balance_sheet', {}),
                'cash_flow': statements.get('cash_flow', {}),
                'data_point_dates': statements.get('dates', {})
            })
        
        # Add metadata
        for key, value in registry_data.items():
            if key.endswith('_metadata'):
                legacy_data[key] = value
        
        return legacy_data
    
    def get_market_data(self, symbol: str, period: str = 'daily', 
                       range_param: str = '1y') -> Dict[str, Any]:
        """
        Get market data with registry integration.
        
        Args:
            symbol: Stock symbol
            period: Data period (daily, weekly, monthly)
            range_param: Data range (1y, 2y, 5y, etc.)
            
        Returns:
            Market data in standardized format
        """
        try:
            self.registry_calls += 1
            
            request = DataRequest(
                data_type='market_data',
                symbol=symbol,
                period=period,
                additional_params={'range': range_param}
            )
            
            response = self.registry.get_data(request)
            
            if response and response.data:
                return {
                    'data': response.data,
                    'source': response.source.value,
                    'timestamp': response.timestamp,
                    'quality_score': response.quality_score,
                    'cache_hit': response.cache_hit
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            self.legacy_fallbacks += 1
            return self._get_market_data_legacy(symbol, period, range_param)
    
    def _get_market_data_legacy(self, symbol: str, period: str, range_param: str) -> Dict[str, Any]:
        """Legacy fallback for market data"""
        try:
            # Import here to avoid circular dependencies
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=range_param, interval=period)
            
            return {
                'data': data.to_dict(),
                'source': 'yfinance_legacy',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Legacy market data fallback failed: {e}")
            return {}
    
    def invalidate_cache(self, symbol: str = None, data_type: str = None):
        """Invalidate cache for specific symbol or data type"""
        if symbol or data_type:
            pattern = f"{symbol}_{data_type}" if symbol and data_type else (symbol or data_type)
            self.registry.invalidate_cache(pattern)
        else:
            self.registry.invalidate_cache()
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get metrics about registry vs legacy usage"""
        total_calls = self.registry_calls + self.legacy_fallbacks
        registry_ratio = self.registry_calls / total_calls if total_calls > 0 else 0
        
        return {
            'registry_calls': self.registry_calls,
            'legacy_fallbacks': self.legacy_fallbacks,
            'total_calls': total_calls,
            'registry_success_ratio': registry_ratio,
            'registry_metrics': self.registry.get_metrics()
        }


class LegacyDataInterface:
    """
    Compatibility layer that provides the exact same interface as existing
    data access methods while internally using the Universal Data Registry.
    """
    
    def __init__(self, adapter: RegistryIntegrationAdapter = None):
        """Initialize legacy interface"""
        self.adapter = adapter or RegistryIntegrationAdapter()
    
    def load_financial_statements(self, symbol: str, company_folder: str) -> Dict[str, Any]:
        """Legacy-compatible method for loading financial statements"""
        return self.adapter.get_financial_data(
            symbol=symbol,
            company_folder=company_folder,
            data_types=['financial_statements']
        )
    
    def get_stock_data(self, symbol: str, period: str = '1y') -> Dict[str, Any]:
        """Legacy-compatible method for getting stock data"""
        return self.adapter.get_market_data(
            symbol=symbol,
            period='daily',
            range_param=period
        )
    
    def calculate_fcf_data(self, symbol: str, company_folder: str) -> Dict[str, Any]:
        """Legacy-compatible FCF calculation with registry integration"""
        # Get financial data through registry
        financial_data = self.adapter.get_financial_data(
            symbol=symbol,
            company_folder=company_folder,
            data_types=['financial_statements']
        )
        
        if not financial_data:
            return {}
        
        # If we have a calculator instance from legacy fallback, use it
        if 'calculator_instance' in financial_data:
            calculator = financial_data['calculator_instance']
            try:
                return {
                    'fcfe_values': calculator.calculate_fcfe(),
                    'fcff_values': calculator.calculate_fcff(),
                    'lfcf_values': calculator.calculate_levered_fcf(),
                    'data_point_dates': getattr(calculator, 'data_point_dates', {})
                }
            except Exception as e:
                logger.error(f"FCF calculation failed: {e}")
                return {}
        
        # If we have registry data, create a temporary calculator
        try:
            from core.analysis.engines.financial_calculations import FinancialCalculator
            
            calculator = FinancialCalculator(
                company_folder=company_folder,
                symbol=symbol
            )
            
            # Inject registry data into calculator
            calculator.income_statement_data = financial_data.get('income_statement', {})
            calculator.balance_sheet_data = financial_data.get('balance_sheet', {})
            calculator.cash_flow_data = financial_data.get('cash_flow', {})
            calculator.data_point_dates = financial_data.get('data_point_dates', {})
            
            return {
                'fcfe_values': calculator.calculate_fcfe(),
                'fcff_values': calculator.calculate_fcff(),
                'lfcf_values': calculator.calculate_levered_fcf(),
                'data_point_dates': calculator.data_point_dates
            }
            
        except Exception as e:
            logger.error(f"FCF calculation with registry data failed: {e}")
            return {}


# Global adapter instance for easy access
_global_adapter = None

def get_integration_adapter() -> RegistryIntegrationAdapter:
    """Get the global integration adapter instance"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = RegistryIntegrationAdapter()
    return _global_adapter

def get_legacy_interface() -> LegacyDataInterface:
    """Get a legacy-compatible interface"""
    return LegacyDataInterface(get_integration_adapter())


# Convenience functions for backward compatibility
def load_financial_data_unified(symbol: str, company_folder: str = None) -> Dict[str, Any]:
    """Unified function for loading financial data with registry integration"""
    adapter = get_integration_adapter()
    return adapter.get_financial_data(symbol, company_folder)

def get_market_data_unified(symbol: str, period: str = 'daily', range_param: str = '1y') -> Dict[str, Any]:
    """Unified function for getting market data with registry integration"""
    adapter = get_integration_adapter()
    return adapter.get_market_data(symbol, period, range_param)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test integration adapter
    adapter = RegistryIntegrationAdapter()
    
    # Test data loading (will fallback to legacy if registry fails)
    print("Testing financial data loading...")
    data = adapter.get_financial_data("MSFT", "./data/MSFT")
    print(f"Data keys: {list(data.keys())}")
    
    # Print integration metrics
    print("\nIntegration metrics:", adapter.get_integration_metrics())