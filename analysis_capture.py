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

    def capture_analysis(
        self,
        ticker: str,
        company_name: str,
        analysis_results: Dict,
        analysis_type: str = "DCF",
        market_data: Dict = None,
        watch_list_name: str = None,
    ) -> bool:
        """
        Capture any type of analysis results and save to watch list

        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            analysis_results (dict): Analysis results from any valuator
            analysis_type (str): Type of analysis ("DCF", "DDM", "PB")
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
            # Extract key data from analysis results based on type
            analysis_data = self._extract_analysis_data_by_type(
                ticker, company_name, analysis_results, analysis_type, market_data
            )

            # Save to watch list
            success = self.watch_list_manager.add_analysis_to_watch_list(
                target_watch_list, analysis_data
            )

            if success:
                logger.info(
                    f"Captured {analysis_type} analysis for {ticker} to watch list '{target_watch_list}'"
                )
            else:
                logger.error(f"Failed to capture {analysis_type} analysis for {ticker}")

            return success

        except Exception as e:
            logger.error(f"Error capturing {analysis_type} analysis for {ticker}: {e}")
            return False

    def capture_dcf_analysis(
        self,
        ticker: str,
        company_name: str,
        dcf_results: Dict,
        market_data: Dict = None,
        watch_list_name: str = None,
    ) -> bool:
        """
        Capture DCF analysis results and save to watch list (legacy method)

        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            dcf_results (dict): DCF analysis results from DCFValuator
            market_data (dict): Market data (price, etc.)
            watch_list_name (str): Specific watch list name (optional)

        Returns:
            bool: True if captured successfully
        """
        # Use the new unified capture method
        return self.capture_analysis(
            ticker=ticker,
            company_name=company_name,
            analysis_results=dcf_results,
            analysis_type="DCF",
            market_data=market_data,
            watch_list_name=watch_list_name,
        )

    def capture_ddm_analysis(
        self,
        ticker: str,
        company_name: str,
        ddm_results: Dict,
        market_data: Dict = None,
        watch_list_name: str = None,
    ) -> bool:
        """
        Capture DDM analysis results and save to watch list

        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            ddm_results (dict): DDM analysis results from DDMValuator
            market_data (dict): Market data (price, etc.)
            watch_list_name (str): Specific watch list name (optional)

        Returns:
            bool: True if captured successfully
        """
        return self.capture_analysis(
            ticker=ticker,
            company_name=company_name,
            analysis_results=ddm_results,
            analysis_type="DDM",
            market_data=market_data,
            watch_list_name=watch_list_name,
        )

    def capture_pb_analysis(
        self,
        ticker: str,
        company_name: str,
        pb_results: Dict,
        market_data: Dict = None,
        watch_list_name: str = None,
    ) -> bool:
        """
        Capture P/B analysis results and save to watch list

        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            pb_results (dict): P/B analysis results from PBValuator
            market_data (dict): Market data (price, etc.)
            watch_list_name (str): Specific watch list name (optional)

        Returns:
            bool: True if captured successfully
        """
        return self.capture_analysis(
            ticker=ticker,
            company_name=company_name,
            analysis_results=pb_results,
            analysis_type="PB",
            market_data=market_data,
            watch_list_name=watch_list_name,
        )

    def capture_to_multiple_lists(
        self,
        ticker: str,
        company_name: str,
        analysis_results: Dict,
        watch_list_names: List[str],
        analysis_type: str = "DCF",
        market_data: Dict = None,
    ) -> Dict[str, bool]:
        """
        Capture analysis results to multiple watch lists

        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name
            analysis_results (dict): Analysis results from any valuator
            watch_list_names (list): List of watch list names to capture to
            analysis_type (str): Type of analysis ("DCF", "DDM", "PB")
            market_data (dict): Market data (price, etc.)

        Returns:
            dict: Success status for each watch list {watch_list_name: success_bool}
        """
        results = {}

        for watch_list_name in watch_list_names:
            try:
                success = self.capture_analysis(
                    ticker=ticker,
                    company_name=company_name,
                    analysis_results=analysis_results,
                    analysis_type=analysis_type,
                    market_data=market_data,
                    watch_list_name=watch_list_name,
                )
                results[watch_list_name] = success

            except Exception as e:
                logger.error(
                    f"Error capturing {analysis_type} to watch list '{watch_list_name}': {e}"
                )
                results[watch_list_name] = False

        return results

    def _extract_analysis_data_by_type(
        self,
        ticker: str,
        company_name: str,
        analysis_results: Dict,
        analysis_type: str,
        market_data: Dict = None,
    ) -> Dict:
        """
        Extract relevant data from analysis results based on analysis type

        Args:
            ticker (str): Stock ticker
            company_name (str): Company name
            analysis_results (dict): Analysis results
            analysis_type (str): Type of analysis ("DCF", "DDM", "PB")
            market_data (dict): Market data

        Returns:
            dict: Extracted analysis data for watch list storage
        """
        if analysis_type == "DCF":
            return self._extract_dcf_data(ticker, company_name, analysis_results, market_data)
        elif analysis_type == "DDM":
            return self._extract_ddm_data(ticker, company_name, analysis_results, market_data)
        elif analysis_type == "PB":
            return self._extract_pb_data(ticker, company_name, analysis_results, market_data)
        else:
            # Fallback to DCF format for unknown types
            return self._extract_dcf_data(ticker, company_name, analysis_results, market_data)

    def _extract_analysis_data(
        self, ticker: str, company_name: str, dcf_results: Dict, market_data: Dict = None
    ) -> Dict:
        """
        Legacy method for DCF data extraction (for backward compatibility)
        """
        return self._extract_dcf_data(ticker, company_name, dcf_results, market_data)

    def _extract_dcf_data(
        self, ticker: str, company_name: str, dcf_results: Dict, market_data: Dict = None
    ) -> Dict:
        """
        Extract relevant data from DCF results for storage

        Args:
            ticker (str): Stock ticker
            company_name (str): Company name
            dcf_results (dict): DCF analysis results
            market_data (dict): Market data

        Returns:
            dict: Extracted DCF analysis data
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
            'projection_years': assumptions.get('projection_years', 10),
        }

        # Add TASE-specific data if applicable
        if dcf_results.get('is_tase_stock'):
            metadata.update(
                {
                    'value_per_share_agorot': dcf_results.get('value_per_share_agorot'),
                    'value_per_share_shekels': dcf_results.get('value_per_share_shekels'),
                    'currency_note': dcf_results.get('currency_note', ''),
                }
            )

        # Prepare complete analysis data
        analysis_data = {
            'analysis_type': 'DCF',
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'fair_value': fair_value,
            'discount_rate': discount_rate,
            'terminal_growth_rate': terminal_growth_rate,
            'fcf_type': fcf_type,
            'dcf_assumptions': assumptions,
            'metadata': metadata,
        }

        return analysis_data

    def _extract_ddm_data(
        self, ticker: str, company_name: str, ddm_results: Dict, market_data: Dict = None
    ) -> Dict:
        """
        Extract relevant data from DDM results for storage

        Args:
            ticker (str): Stock ticker
            company_name (str): Company name
            ddm_results (dict): DDM analysis results
            market_data (dict): Market data

        Returns:
            dict: Extracted DDM analysis data
        """
        # Get current price from market data or DDM results
        current_price = 0.0
        if market_data and 'current_price' in market_data:
            current_price = market_data['current_price']
        elif 'market_data' in ddm_results and ddm_results['market_data']:
            current_price = ddm_results['market_data'].get('current_price', 0.0)
        elif 'current_price' in ddm_results:
            current_price = ddm_results.get('current_price', 0.0)

        # Get intrinsic value
        intrinsic_value = ddm_results.get('intrinsic_value', 0.0)

        # Get assumptions
        assumptions = ddm_results.get('assumptions', {})
        model_type = ddm_results.get('model_type', 'Unknown')
        discount_rate = assumptions.get('discount_rate', 0.0)
        growth_rate = assumptions.get('terminal_growth_rate', 0.0)

        # Get dividend data
        current_dividend = ddm_results.get('current_dividend', 0.0)
        dividend_yield = current_dividend / current_price if current_price > 0 else 0.0

        # Prepare metadata
        metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'model_type': model_type,
            'model_variant': ddm_results.get('model_variant', ''),
            'current_dividend': current_dividend,
            'dividend_yield': dividend_yield,
            'currency': ddm_results.get('currency', 'USD'),
            'is_tase_stock': ddm_results.get('is_tase_stock', False),
            'upside_downside': ddm_results.get('upside_downside', 0.0),
            'calculation_method': ddm_results.get('calculation_method', ''),
            'dividend_metrics': ddm_results.get('dividend_metrics', {}),
        }

        # Prepare complete analysis data
        analysis_data = {
            'analysis_type': 'DDM',
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'fair_value': intrinsic_value,
            'discount_rate': discount_rate,
            'growth_rate': growth_rate,
            'current_dividend': current_dividend,
            'dividend_yield': dividend_yield,
            'ddm_assumptions': assumptions,
            'metadata': metadata,
        }

        return analysis_data

    def _extract_pb_data(
        self, ticker: str, company_name: str, pb_results: Dict, market_data: Dict = None
    ) -> Dict:
        """
        Extract relevant data from P/B results for storage

        Args:
            ticker (str): Stock ticker
            company_name (str): Company name
            pb_results (dict): P/B analysis results
            market_data (dict): Market data

        Returns:
            dict: Extracted P/B analysis data
        """
        # Get current data
        current_data = pb_results.get('current_data', {})
        current_price = current_data.get('current_price', 0.0)

        # Override with market_data if provided
        if market_data and 'current_price' in market_data:
            current_price = market_data['current_price']

        # Get P/B metrics
        pb_ratio = current_data.get('pb_ratio', 0.0)
        book_value_per_share = current_data.get('book_value_per_share', 0.0)

        # Get valuation analysis
        valuation_analysis = pb_results.get('valuation_analysis', {})
        valuation_ranges = valuation_analysis.get('valuation_ranges', {})
        fair_value = valuation_ranges.get('fair_value', 0.0)

        # Get industry comparison
        industry_comparison = pb_results.get('industry_comparison', {})
        industry_position = industry_comparison.get('position', 'Unknown')

        # Get risk assessment
        risk_assessment = pb_results.get('risk_assessment', {})
        risk_level = risk_assessment.get('risk_level', 'Unknown')

        # Prepare metadata
        metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'pb_ratio': pb_ratio,
            'book_value_per_share': book_value_per_share,
            'valuation_ranges': valuation_ranges,
            'industry_position': industry_position,
            'industry_info': pb_results.get('industry_info', {}),
            'risk_level': risk_level,
            'currency': pb_results.get('currency', 'USD'),
            'is_tase_stock': pb_results.get('is_tase_stock', False),
            'historical_analysis': pb_results.get('historical_analysis', {}),
            'risk_assessment': risk_assessment,
        }

        # Prepare complete analysis data
        analysis_data = {
            'analysis_type': 'PB',
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'fair_value': fair_value,
            'pb_ratio': pb_ratio,
            'book_value_per_share': book_value_per_share,
            'industry_position': industry_position,
            'risk_level': risk_level,
            'valuation_ranges': valuation_ranges,
            'pb_analysis': pb_results,
            'metadata': metadata,
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
                            ticker=ticker, company_name=company_name, dcf_results=result
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
                market_data=market_data,
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
            'available_watch_lists': [
                wl['name'] for wl in self.watch_list_manager.list_watch_lists()
            ],
        }


# Global instance for easy access
analysis_capture = AnalysisCapture()
