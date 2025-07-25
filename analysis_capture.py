"""
Analysis Capture System

This module provides hooks and capture mechanisms for automatically saving
DCF analysis results to watch lists when analyses are performed.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from watch_list_manager import WatchListManager

logger = logging.getLogger(__name__)

class AnalysisCapture:
    """
    Captures and stores analysis results automatically
    """
    
    def __init__(self):
        """Initialize analysis capture system"""
        self.watch_list_manager = WatchListManager()
        self.capture_enabled = True
        self.current_watch_list = None
        self.current_watch_lists = []
    
    def set_current_watch_list(self, watch_list_name: str):
        """
        Set the current watch list for automatic capture
        
        Args:
            watch_list_name (str): Name of watch list to capture to
        """
        self.current_watch_list = watch_list_name
        logger.info(f"Set current watch list for capture: {watch_list_name}")
    
    def set_multiple_watch_lists(self, watch_list_names: List[str]):
        """
        Set multiple watch lists for automatic capture
        
        Args:
            watch_list_names (list): List of watch list names to capture to
        """
        self.current_watch_lists = watch_list_names
        if watch_list_names:
            self.current_watch_list = watch_list_names[0]  # Keep primary for compatibility
        logger.info(f"Set multiple watch lists for capture: {watch_list_names}")
    
    def enable_capture(self):
        """Enable automatic analysis capture"""
        self.capture_enabled = True
        logger.info("Analysis capture enabled")
    
    def disable_capture(self):
        """Disable automatic analysis capture"""
        self.capture_enabled = False
        logger.info("Analysis capture disabled")
    
    def capture_dcf_analysis(self, 
                           ticker: str,
                           company_name: str,
                           dcf_results: Dict,
                           market_data: Dict = None,
                           watch_list_name: str = None) -> bool:
        """
        Capture DCF analysis results and save to watch list
        
        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            dcf_results (dict): DCF analysis results from DCFValuator
            market_data (dict): Market data (price, etc.)
            watch_list_name (str): Specific watch list name (optional)
            
        Returns:
            bool: True if captured successfully
        """
        if not self.capture_enabled:
            logger.debug("Analysis capture is disabled")
            return False
        
        # Use provided watch list or current watch list
        target_watch_list = watch_list_name or self.current_watch_list
        
        if not target_watch_list:
            logger.debug("No watch list specified for capture")
            return False
        
        try:
            # Extract key data from DCF results
            analysis_data = self._extract_analysis_data(
                ticker, company_name, dcf_results, market_data
            )
            
            # Save to watch list
            success = self.watch_list_manager.add_analysis_to_watch_list(
                target_watch_list, analysis_data
            )
            
            if success:
                logger.info(f"Captured analysis for {ticker} to watch list '{target_watch_list}'")
            else:
                logger.error(f"Failed to capture analysis for {ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error capturing analysis for {ticker}: {e}")
            return False
    
    def capture_to_multiple_lists(self, 
                                 ticker: str,
                                 company_name: str,
                                 dcf_results: Dict,
                                 watch_list_names: List[str],
                                 market_data: Dict = None) -> Dict[str, bool]:
        """
        Capture DCF analysis results to multiple watch lists
        
        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            dcf_results (dict): DCF analysis results from DCFValuator
            watch_list_names (list): List of watch list names to capture to
            market_data (dict): Market data (price, etc.)
            
        Returns:
            dict: Success status for each watch list {watch_list_name: success_bool}
        """
        results = {}
        
        for watch_list_name in watch_list_names:
            try:
                success = self.capture_dcf_analysis(
                    ticker=ticker,
                    company_name=company_name,
                    dcf_results=dcf_results,
                    market_data=market_data,
                    watch_list_name=watch_list_name
                )
                results[watch_list_name] = success
                
            except Exception as e:
                logger.error(f"Error capturing to watch list '{watch_list_name}': {e}")
                results[watch_list_name] = False
        
        return results
    
    def _extract_analysis_data(self, 
                              ticker: str,
                              company_name: str,
                              dcf_results: Dict,
                              market_data: Dict = None) -> Dict:
        """
        Extract relevant data from DCF results for storage
        
        Args:
            ticker (str): Stock ticker
            company_name (str): Company name
            dcf_results (dict): DCF analysis results
            market_data (dict): Market data
            
        Returns:
            dict: Extracted analysis data
        """
        # Get current price from market data or DCF results
        current_price = 0.0
        if market_data and 'current_price' in market_data:
            current_price = market_data['current_price']
        elif 'market_data' in dcf_results and dcf_results['market_data']:
            current_price = dcf_results['market_data'].get('current_price', 0.0)
        
        # Get fair value (value per share)
        fair_value = dcf_results.get('value_per_share', 0.0)
        
        # Get assumptions
        assumptions = dcf_results.get('assumptions', {})
        discount_rate = assumptions.get('discount_rate', 0.0)
        terminal_growth_rate = assumptions.get('terminal_growth_rate', 0.0)
        
        # Get FCF type
        fcf_type = dcf_results.get('fcf_type', 'FCFE')
        
        # Prepare metadata
        metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'enterprise_value': dcf_results.get('enterprise_value', 0.0),
            'equity_value': dcf_results.get('equity_value', 0.0),
            'terminal_value': dcf_results.get('terminal_value', 0.0),
            'pv_terminal': dcf_results.get('pv_terminal', 0.0),
            'currency': dcf_results.get('currency', 'USD'),
            'is_tase_stock': dcf_results.get('is_tase_stock', False),
            'projection_years': assumptions.get('projection_years', 10)
        }
        
        # Add TASE-specific data if applicable
        if dcf_results.get('is_tase_stock'):
            metadata.update({
                'value_per_share_agorot': dcf_results.get('value_per_share_agorot'),
                'value_per_share_shekels': dcf_results.get('value_per_share_shekels'),
                'currency_note': dcf_results.get('currency_note', '')
            })
        
        # Prepare complete analysis data
        analysis_data = {
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'fair_value': fair_value,
            'discount_rate': discount_rate,
            'terminal_growth_rate': terminal_growth_rate,
            'fcf_type': fcf_type,
            'dcf_assumptions': assumptions,
            'metadata': metadata
        }
        
        return analysis_data
    
    def create_analysis_hook(self):
        """
        Create a decorator function that can be used to hook into DCF calculations
        
        Returns:
            function: Decorator function for automatic capture
        """
        def capture_decorator(func):
            """Decorator to automatically capture DCF analysis results"""
            def wrapper(*args, **kwargs):
                # Execute original function
                result = func(*args, **kwargs)
                
                # Try to capture results if capture is enabled
                if self.capture_enabled and self.current_watch_list and result:
                    try:
                        # Extract ticker and company name from context
                        # This might need adjustment based on how the DCF function is called
                        ticker = kwargs.get('ticker', 'UNKNOWN')
                        company_name = kwargs.get('company_name', '')
                        
                        # Capture the analysis
                        self.capture_dcf_analysis(
                            ticker=ticker,
                            company_name=company_name,
                            dcf_results=result
                        )
                    except Exception as e:
                        logger.warning(f"Failed to auto-capture analysis: {e}")
                
                return result
            
            return wrapper
        
        return capture_decorator
    
    def manual_capture_from_streamlit_session(self, session_state: Dict) -> bool:
        """
        Manually capture analysis from Streamlit session state
        
        Args:
            session_state (dict): Streamlit session state containing analysis data
            
        Returns:
            bool: True if captured successfully
        """
        try:
            # Extract data from session state
            ticker = session_state.get('ticker', 'UNKNOWN')
            company_name = session_state.get('company_name', '')
            dcf_results = session_state.get('dcf_results', {})
            market_data = session_state.get('market_data', {})
            
            if not dcf_results:
                logger.warning("No DCF results found in session state")
                return False
            
            return self.capture_dcf_analysis(
                ticker=ticker,
                company_name=company_name,
                dcf_results=dcf_results,
                market_data=market_data
            )
            
        except Exception as e:
            logger.error(f"Error capturing from session state: {e}")
            return False
    
    def get_capture_status(self) -> Dict:
        """
        Get current capture system status
        
        Returns:
            dict: Capture system status information
        """
        return {
            'capture_enabled': self.capture_enabled,
            'current_watch_list': self.current_watch_list,
            'available_watch_lists': [wl['name'] for wl in self.watch_list_manager.list_watch_lists()]
        }

# Global instance for easy access
analysis_capture = AnalysisCapture()