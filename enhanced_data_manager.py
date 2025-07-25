"""
Enhanced Data Manager Integration

This module extends the existing CentralizedDataManager to integrate with the new
unified data adapter system, providing seamless access to multiple data sources
while maintaining compatibility with existing code.

Features:
- Extends existing CentralizedDataManager
- Integrates with UnifiedDataAdapter
- Maintains backward compatibility
- Enhanced market data fetching with multiple sources
- Intelligent fallback and caching
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Import existing data manager
from centralized_data_manager import CentralizedDataManager

# Import new unified adapter system
from unified_data_adapter import UnifiedDataAdapter
from data_sources import DataSourceType, FinancialDataRequest, DataSourceResponse

logger = logging.getLogger(__name__)

class EnhancedDataManager(CentralizedDataManager):
    """
    Enhanced data manager that extends CentralizedDataManager with multiple data sources.
    
    This class maintains full backward compatibility while adding support for
    Alpha Vantage, Financial Modeling Prep, Polygon.io, and other data sources.
    """
    
    def __init__(self, base_path: str, cache_dir: str = "data_cache", validation_level=None):
        """
        Initialize the enhanced data manager.
        
        Args:
            base_path (str): Base directory path for data files
            cache_dir (str): Directory for caching data
            validation_level: Level of input validation strictness
        """
        # Initialize parent class
        if validation_level is None:
            from input_validator import ValidationLevel
            validation_level = ValidationLevel.MODERATE
        
        super().__init__(base_path, cache_dir, validation_level)
        
        # Initialize unified data adapter
        self.unified_adapter = UnifiedDataAdapter(
            config_file=str(Path(base_path) / "data_sources_config.json"),
            base_path=base_path
        )
        
        # Track which method is being used for market data
        self._data_source_used = None
        
        logger.info("Enhanced Data Manager initialized with multiple data sources")
    
    def fetch_market_data(self, ticker: str, force_reload: bool = False, skip_validation: bool = False) -> Optional[Dict[str, Any]]:
        """
        Enhanced market data fetching using multiple sources with fallback.
        
        This method first tries the new unified adapter system, then falls back
        to the original yfinance implementation for backward compatibility.
        
        Args:
            ticker (str): Stock ticker symbol
            force_reload (bool): Force reload even if cached data exists
            skip_validation (bool): Skip pre-flight validation
            
        Returns:
            Optional[Dict[str, Any]]: Market data or None if failed
        """
        logger.info(f"Fetching market data for {ticker} using enhanced sources")
        
        # Create request for unified adapter
        request = FinancialDataRequest(
            ticker=ticker,
            data_types=['price', 'fundamentals'],
            force_refresh=force_reload
        )
        
        # Try unified adapter first (with multiple sources)
        try:
            response = self.unified_adapter.fetch_data(request)
            
            if response.success and response.data:
                self._data_source_used = response.source_type.value if response.source_type else 'unified_adapter'
                
                # Convert unified adapter response to legacy format
                standardized_data = self._convert_to_legacy_format(response.data, ticker)
                
                if standardized_data:
                    logger.info(f"Successfully fetched data from {self._data_source_used} for {ticker}")
                    
                    # Cache using parent's caching mechanism
                    params = {'ticker': ticker.upper()}
                    cache_key = self._generate_cache_key('market_data', params)
                    self.cache_data(cache_key, standardized_data, f'enhanced_{self._data_source_used}', expiry_hours=2)
                    
                    return standardized_data
        
        except Exception as e:
            logger.warning(f"Unified adapter failed for {ticker}: {e}")
        
        # Fallback to original yfinance implementation
        logger.info(f"Falling back to original yfinance implementation for {ticker}")
        self._data_source_used = 'yfinance_fallback'
        
        try:
            return super().fetch_market_data(ticker, force_reload, skip_validation)
        except Exception as e:
            logger.error(f"All market data sources failed for {ticker}: {e}")
            return None
    
    def _convert_to_legacy_format(self, data: Dict[str, Any], ticker: str) -> Optional[Dict[str, Any]]:
        """
        Convert unified adapter response to legacy CentralizedDataManager format.
        
        Args:
            data (Dict[str, Any]): Data from unified adapter
            ticker (str): Stock ticker symbol
            
        Returns:
            Optional[Dict[str, Any]]: Data in legacy format
        """
        try:
            # Base structure matching original format
            legacy_data = {
                'ticker': ticker.upper(),
                'company_name': data.get('company_name', ticker.upper()),
                'currency': data.get('currency', 'USD'),
                'last_updated': data.get('last_updated', datetime.now().isoformat()),
                'data_source': data.get('source', self._data_source_used or 'enhanced')
            }
            
            # Map price data
            if 'current_price' in data:
                legacy_data['current_price'] = float(data['current_price'])
            elif 'price' in data:
                legacy_data['current_price'] = float(data['price'])
            else:
                # Try to extract from nested structures
                for key, value in data.items():
                    if isinstance(value, dict) and 'price' in value:
                        legacy_data['current_price'] = float(value['price'])
                        break
            
            # Map market cap (convert to millions if needed)
            if 'market_cap' in data:
                market_cap = data['market_cap']
                if isinstance(market_cap, (int, float)):
                    # If value is very large, assume it's in actual dollars and convert to millions
                    if market_cap > 10000:  # Likely in actual dollars
                        legacy_data['market_cap'] = market_cap / 1000000
                    else:  # Already in millions
                        legacy_data['market_cap'] = market_cap
                else:
                    legacy_data['market_cap'] = 0
            
            # Map shares outstanding
            if 'shares_outstanding' in data:
                legacy_data['shares_outstanding'] = float(data['shares_outstanding'])
            
            # Calculate missing values if possible
            if ('current_price' in legacy_data and 'market_cap' in legacy_data and 
                legacy_data['current_price'] > 0 and legacy_data['market_cap'] > 0 and 
                'shares_outstanding' not in legacy_data):
                # Calculate shares outstanding from market cap and price
                # market_cap is in millions, so multiply by 1M and divide by price
                calculated_shares = (legacy_data['market_cap'] * 1000000) / legacy_data['current_price']
                legacy_data['shares_outstanding'] = calculated_shares
            
            elif ('current_price' in legacy_data and 'shares_outstanding' in legacy_data and 
                  legacy_data['current_price'] > 0 and legacy_data['shares_outstanding'] > 0 and 
                  'market_cap' not in legacy_data):
                # Calculate market cap from price and shares
                calculated_market_cap = (legacy_data['current_price'] * legacy_data['shares_outstanding']) / 1000000
                legacy_data['market_cap'] = calculated_market_cap
            
            # Ensure we have at least price data
            if 'current_price' not in legacy_data or legacy_data['current_price'] <= 0:
                logger.warning(f"No valid price data found for {ticker}")
                return None
            
            # Add additional fields from alternative sources if available
            additional_fields = [
                'pe_ratio', 'pb_ratio', 'dividend_yield', 'eps', 'beta',
                'revenue_ttm', 'profit_margin', 'sector', 'industry'
            ]
            
            for field in additional_fields:
                if field in data and data[field] is not None:
                    legacy_data[field] = data[field]
            
            return legacy_data
            
        except Exception as e:
            logger.error(f"Failed to convert data to legacy format for {ticker}: {e}")
            return None
    
    def get_available_data_sources(self) -> Dict[str, Any]:
        """
        Get information about available data sources and their status.
        
        Returns:
            Dict[str, Any]: Information about configured data sources
        """
        sources_info = {
            'enhanced_sources': {},
            'fallback_available': True,
            'total_sources': 0,
            'active_sources': 0
        }
        
        # Get information from unified adapter
        try:
            for source_type, config in self.unified_adapter.configurations.items():
                source_info = {
                    'type': source_type.value,
                    'enabled': config.is_enabled,
                    'priority': config.priority.value,
                    'has_credentials': config.credentials is not None and bool(config.credentials.api_key) if config.credentials else False,
                    'quality_threshold': config.quality_threshold
                }
                
                if config.credentials:
                    source_info.update({
                        'rate_limit': f"{config.credentials.rate_limit_calls}/{config.credentials.rate_limit_period}s",
                        'monthly_limit': config.credentials.monthly_limit,
                        'cost_per_call': config.credentials.cost_per_call
                    })
                
                sources_info['enhanced_sources'][source_type.value] = source_info
                sources_info['total_sources'] += 1
                
                if config.is_enabled:
                    sources_info['active_sources'] += 1
        
        except Exception as e:
            logger.warning(f"Failed to get enhanced sources info: {e}")
        
        return sources_info
    
    def get_enhanced_usage_report(self) -> Dict[str, Any]:
        """
        Get comprehensive usage report including both enhanced and legacy sources.
        
        Returns:
            Dict[str, Any]: Combined usage report
        """
        report = {
            'enhanced_adapter': {},
            'legacy_fallback': {},
            'combined_stats': {}
        }
        
        # Get enhanced adapter usage
        try:
            enhanced_report = self.unified_adapter.get_usage_report()
            report['enhanced_adapter'] = enhanced_report
        except Exception as e:
            logger.warning(f"Failed to get enhanced usage report: {e}")
            report['enhanced_adapter'] = {'error': str(e)}
        
        # Get legacy cache stats
        try:
            cache_stats = self.get_cache_stats()
            report['legacy_fallback'] = {
                'cache_stats': cache_stats,
                'yfinance_available': True
            }
        except Exception as e:
            logger.warning(f"Failed to get legacy stats: {e}")
            report['legacy_fallback'] = {'error': str(e)}
        
        # Calculate combined statistics
        try:
            enhanced_stats = report['enhanced_adapter']
            if 'total_calls' in enhanced_stats and 'total_cost' in enhanced_stats:
                report['combined_stats'] = {
                    'total_api_calls': enhanced_stats['total_calls'],
                    'total_cost': enhanced_stats['total_cost'],
                    'sources_available': len(report['enhanced_adapter'].get('sources', {})) + 1,  # +1 for yfinance
                    'last_data_source_used': self._data_source_used or 'unknown'
                }
        except Exception as e:
            logger.warning(f"Failed to calculate combined stats: {e}")
        
        return report
    
    def configure_enhanced_source(self, source_name: str, api_key: str, **kwargs) -> bool:
        """
        Configure an enhanced data source.
        
        Args:
            source_name (str): Name of the data source ('alpha_vantage', 'fmp', 'polygon')
            api_key (str): API key for the source
            **kwargs: Additional configuration options
            
        Returns:
            bool: True if configuration successful
        """
        try:
            source_type_map = {
                'alpha_vantage': DataSourceType.ALPHA_VANTAGE,
                'fmp': DataSourceType.FINANCIAL_MODELING_PREP,
                'financial_modeling_prep': DataSourceType.FINANCIAL_MODELING_PREP,
                'polygon': DataSourceType.POLYGON,
                'polygon.io': DataSourceType.POLYGON
            }
            
            source_type = source_type_map.get(source_name.lower())
            if not source_type:
                logger.error(f"Unknown source name: {source_name}")
                return False
            
            success = self.unified_adapter.configure_source(source_type, api_key, **kwargs)
            
            if success:
                logger.info(f"Successfully configured {source_name}")
            else:
                logger.error(f"Failed to configure {source_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error configuring {source_name}: {e}")
            return False
    
    def test_all_sources(self, ticker: str = "AAPL") -> Dict[str, Any]:
        """
        Test all available data sources and return results.
        
        Args:
            ticker (str): Ticker symbol to test with
            
        Returns:
            Dict[str, Any]: Test results for all sources
        """
        test_results = {
            'ticker': ticker,
            'test_timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {}
        }
        
        # Test enhanced sources
        try:
            request = FinancialDataRequest(ticker=ticker, force_refresh=True)
            
            for source_type, provider in self.unified_adapter.providers.items():
                try:
                    start_time = datetime.now()
                    response = provider.fetch_data(request)
                    end_time = datetime.now()
                    
                    test_results['sources'][source_type.value] = {
                        'success': response.success,
                        'response_time': (end_time - start_time).total_seconds(),
                        'quality_score': response.quality_metrics.overall_score if response.quality_metrics else 0,
                        'api_calls_used': response.api_calls_used,
                        'cost_incurred': response.cost_incurred,
                        'error': response.error_message if not response.success else None,
                        'data_points': len(response.data) if response.data else 0
                    }
                    
                except Exception as e:
                    test_results['sources'][source_type.value] = {
                        'success': False,
                        'error': str(e)
                    }
        
        except Exception as e:
            logger.error(f"Error testing enhanced sources: {e}")
        
        # Test legacy yfinance fallback
        try:
            start_time = datetime.now()
            legacy_data = super().fetch_market_data(ticker, force_reload=True, skip_validation=True)
            end_time = datetime.now()
            
            test_results['sources']['yfinance_legacy'] = {
                'success': legacy_data is not None,
                'response_time': (end_time - start_time).total_seconds(),
                'data_points': len(legacy_data) if legacy_data else 0,
                'error': None if legacy_data else 'No data returned'
            }
            
        except Exception as e:
            test_results['sources']['yfinance_legacy'] = {
                'success': False,
                'error': str(e)
            }
        
        # Calculate summary
        successful_sources = sum(1 for result in test_results['sources'].values() if result.get('success', False))
        total_sources = len(test_results['sources'])
        
        test_results['summary'] = {
            'total_sources': total_sources,
            'successful_sources': successful_sources,
            'success_rate': successful_sources / total_sources if total_sources > 0 else 0,
            'best_source': None,
            'fastest_source': None
        }
        
        # Find best and fastest sources
        successful_sources_data = [(name, data) for name, data in test_results['sources'].items() 
                                 if data.get('success', False)]
        
        if successful_sources_data:
            # Best by quality score
            best = max(successful_sources_data, 
                      key=lambda x: x[1].get('quality_score', 0), 
                      default=None)
            if best:
                test_results['summary']['best_source'] = best[0]
            
            # Fastest by response time
            fastest = min(successful_sources_data, 
                         key=lambda x: x[1].get('response_time', float('inf')), 
                         default=None)
            if fastest:
                test_results['summary']['fastest_source'] = fastest[0]
        
        return test_results
    
    def cleanup(self):
        """Enhanced cleanup that handles both legacy and new systems"""
        try:
            # Cleanup unified adapter
            self.unified_adapter.cleanup()
            logger.info("Enhanced data adapter cleanup completed")
        except Exception as e:
            logger.error(f"Enhanced cleanup error: {e}")
        
        # Call parent cleanup
        try:
            if hasattr(super(), 'cleanup'):
                super().cleanup()
        except:
            pass  # Parent might not have cleanup method
    
    def __del__(self):
        """Enhanced destructor"""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction

# Convenience function to create enhanced data manager
def create_enhanced_data_manager(base_path: str = ".", cache_dir: str = "data_cache") -> EnhancedDataManager:
    """
    Create an enhanced data manager with reasonable defaults.
    
    Args:
        base_path (str): Base path for data files
        cache_dir (str): Cache directory name
        
    Returns:
        EnhancedDataManager: Configured enhanced data manager
    """
    try:
        from input_validator import ValidationLevel
        validation_level = ValidationLevel.MODERATE
    except ImportError:
        validation_level = None
    
    return EnhancedDataManager(base_path, cache_dir, validation_level)

# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create enhanced data manager
    manager = create_enhanced_data_manager()
    
    # Show available sources
    sources = manager.get_available_data_sources()
    print("Available data sources:")
    for source, info in sources['enhanced_sources'].items():
        print(f"  {source}: {'✓' if info['enabled'] else '✗'} (Priority: {info['priority']})")
    
    # Test with a sample ticker
    print(f"\nTesting data fetch for AAPL...")
    data = manager.fetch_market_data("AAPL")
    
    if data:
        print(f"✓ Successfully fetched data from {manager._data_source_used}")
        print(f"  Price: ${data.get('current_price', 'N/A')}")
        print(f"  Market Cap: ${data.get('market_cap', 'N/A')}M")
    else:
        print("✗ Failed to fetch data")
    
    # Cleanup
    manager.cleanup()