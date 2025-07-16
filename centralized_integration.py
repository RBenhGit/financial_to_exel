"""
Centralized Integration Layer

This module provides compatibility between the centralized data system
and the existing financial_calculations.py module, ensuring seamless
integration while maintaining backward compatibility.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from centralized_data_manager import CentralizedDataManager
from centralized_data_processor import CentralizedDataProcessor
from financial_calculations import FinancialCalculator

logger = logging.getLogger(__name__)

class CentralizedFinancialCalculator(FinancialCalculator):
    """
    Enhanced FinancialCalculator that uses the centralized data system
    while maintaining full compatibility with existing code.
    """
    
    def __init__(self, company_folder: str, validation_enabled: bool = True):
        """
        Initialize with centralized data system integration.
        
        Args:
            company_folder (str): Path to company folder
            validation_enabled (bool): Enable data validation
        """
        # Initialize the parent class with correct signature
        super().__init__(company_folder)
        
        # Set validation flag manually
        self.validation_enabled = validation_enabled
        
        # Initialize centralized components
        base_path = Path(company_folder).parent
        self.data_manager = CentralizedDataManager(str(base_path))
        self.data_processor = CentralizedDataProcessor(self.data_manager)
        
        # Extract company name from folder path
        self.company_name = Path(company_folder).name
        
        logger.info(f"Centralized Financial Calculator initialized for {self.company_name}")
    
    def load_financial_statements(self):
        """
        Override to use centralized data loading with caching.
        """
        logger.info(f"Loading financial statements using centralized system for {self.company_name}")
        
        try:
            # Use centralized data manager to load Excel data
            excel_data = self.data_manager.load_excel_data(self.company_name)
            
            # Convert to format expected by parent class
            self.financial_data = excel_data
            
            # Set flags
            self.statements_loaded = True
            
            logger.info(f"Successfully loaded {len(excel_data)} financial datasets using centralized system")
            
        except Exception as e:
            logger.error(f"Error loading financial statements: {e}")
            self.statements_loaded = False
            raise
    
    def fetch_market_data(self, ticker_symbol: str = None) -> Optional[Dict[str, Any]]:
        """
        Override to use centralized market data fetching with caching.
        """
        if ticker_symbol:
            self.ticker_symbol = ticker_symbol.upper()
        
        if not self.ticker_symbol:
            # Try to auto-extract from company name
            self.ticker_symbol = self.company_name.upper()
        
        logger.info(f"Fetching market data using centralized system for {self.ticker_symbol}")
        
        try:
            # Use centralized data manager for market data
            market_data = self.data_manager.fetch_market_data(self.ticker_symbol)
            
            if market_data:
                # Update instance variables to maintain compatibility
                self.current_stock_price = market_data.get('current_price', 0)
                self.shares_outstanding = market_data.get('shares_outstanding', 0)
                self.market_cap = market_data.get('market_cap', 0) * 1000000  # Convert back to actual value
                self.company_name = market_data.get('company_name', self.company_name)
                
                logger.info(f"Successfully fetched market data using centralized system")
                return market_data
            else:
                logger.warning(f"Market data fetch failed for {self.ticker_symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def calculate_all_fcf_types(self) -> Dict[str, Any]:
        """
        Enhanced FCF calculation using centralized processing with fallback.
        """
        logger.info(f"Calculating FCF using centralized system for {self.company_name}")
        
        try:
            # Try centralized calculation first
            fcf_result = self.data_processor.calculate_fcf(self.company_name)
            
            if fcf_result.success and fcf_result.data:
                # Convert to format expected by existing code
                fcf_data = fcf_result.data
                
                # Automatically fetch market data if not already available
                if not hasattr(self, 'current_stock_price') or not self.current_stock_price:
                    self.fetch_market_data()
                
                result = {
                    'FCFF': fcf_data.fcff,
                    'FCFE': fcf_data.fcfe,
                    'LFCF': fcf_data.lfcf,
                    'years': fcf_data.years,
                    'growth_rates': fcf_data.growth_rates,
                    'averages': fcf_data.averages,
                    'current_stock_price': getattr(self, 'current_stock_price', 0),
                    'shares_outstanding': getattr(self, 'shares_outstanding', 0),
                    'market_cap': getattr(self, 'market_cap', 0),
                    'company_name': self.company_name,
                    'ticker_symbol': getattr(self, 'ticker_symbol', self.company_name),
                    'calculation_method': 'centralized',
                    'data_quality_report': getattr(self, 'data_quality_report', None)
                }
                
                logger.info(f"Successfully calculated FCF using centralized system")
                return result
            else:
                logger.warning("Centralized FCF calculation failed, falling back to original method")
                # Fall back to original calculation
                return super().calculate_all_fcf_types()
                
        except Exception as e:
            logger.error(f"Error in centralized FCF calculation: {e}")
            logger.info("Falling back to original FCF calculation method")
            # Fall back to original calculation
            return super().calculate_all_fcf_types()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the centralized data system.
        """
        try:
            cache_stats = self.data_manager.get_cache_stats()
            processing_stats = self.data_processor.get_processing_statistics()
            
            return {
                'centralized_system': {
                    'cache_stats': cache_stats,
                    'processing_stats': processing_stats,
                    'company': self.company_name,
                    'ticker': getattr(self, 'ticker_symbol', 'N/A')
                },
                'compatibility_mode': True
            }
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {'error': str(e)}
    
    def clear_cache(self, cache_type: str = 'all'):
        """
        Clear centralized system cache.
        """
        try:
            self.data_manager.clear_cache(cache_type)
            logger.info(f"Cleared {cache_type} cache for centralized system")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

def create_centralized_calculator(company_folder: str, validation_enabled: bool = True) -> CentralizedFinancialCalculator:
    """
    Factory function to create a centralized financial calculator.
    
    Args:
        company_folder (str): Path to company folder
        validation_enabled (bool): Enable data validation
        
    Returns:
        CentralizedFinancialCalculator: Enhanced calculator instance
    """
    return CentralizedFinancialCalculator(company_folder, validation_enabled)

def migrate_existing_code(original_calculator: FinancialCalculator) -> CentralizedFinancialCalculator:
    """
    Migrate an existing FinancialCalculator to use the centralized system.
    
    Args:
        original_calculator (FinancialCalculator): Existing calculator instance
        
    Returns:
        CentralizedFinancialCalculator: Migrated calculator instance
    """
    # Create new centralized calculator
    centralized_calc = CentralizedFinancialCalculator(
        original_calculator.company_folder,
        original_calculator.validation_enabled
    )
    
    # Transfer any existing state
    if hasattr(original_calculator, 'ticker_symbol'):
        centralized_calc.ticker_symbol = original_calculator.ticker_symbol
    if hasattr(original_calculator, 'current_stock_price'):
        centralized_calc.current_stock_price = original_calculator.current_stock_price
    if hasattr(original_calculator, 'shares_outstanding'):
        centralized_calc.shares_outstanding = original_calculator.shares_outstanding
    if hasattr(original_calculator, 'market_cap'):
        centralized_calc.market_cap = original_calculator.market_cap
    
    logger.info(f"Successfully migrated calculator to centralized system")
    return centralized_calc

# Backward compatibility function
def get_enhanced_calculator(company_folder: str, validation_enabled: bool = True):
    """
    Get an enhanced calculator that uses the centralized system.
    This function maintains backward compatibility while providing enhanced features.
    """
    return create_centralized_calculator(company_folder, validation_enabled)