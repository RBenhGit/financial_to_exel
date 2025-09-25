"""
Analysis Capture Module
=======================

Module for capturing and storing financial analysis results from various
valuation methods (DCF, DDM, P/B) for portfolio management and tracking.

This module provides functionality to:
- Capture analysis results in a standardized format
- Store results in watch lists and portfolios
- Track analysis history and performance
- Export results for reporting
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AnalysisCapture:
    """
    Class for capturing and managing financial analysis results
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize analysis capture system

        Args:
            storage_path: Path to store analysis results (defaults to data/analysis_results)
        """
        self.storage_path = Path(storage_path or "data/analysis_results")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def capture_dcf_analysis(
        self,
        ticker: str,
        company_name: str,
        dcf_results: Dict[str, Any],
        watch_list_name: Optional[str] = None
    ) -> bool:
        """
        Capture DCF analysis results

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            dcf_results: DCF analysis results dictionary
            watch_list_name: Optional watch list to add to

        Returns:
            bool: Success status
        """
        try:
            analysis_data = {
                'analysis_type': 'DCF',
                'ticker': ticker,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'results': dcf_results,
                'watch_list': watch_list_name
            }

            filename = f"dcf_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_path / filename

            with open(filepath, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            logger.info(f"DCF analysis captured for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Failed to capture DCF analysis for {ticker}: {e}")
            return False

    def capture_ddm_analysis(
        self,
        ticker: str,
        company_name: str,
        ddm_results: Dict[str, Any],
        watch_list_name: Optional[str] = None
    ) -> bool:
        """
        Capture DDM analysis results

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            ddm_results: DDM analysis results dictionary
            watch_list_name: Optional watch list to add to

        Returns:
            bool: Success status
        """
        try:
            analysis_data = {
                'analysis_type': 'DDM',
                'ticker': ticker,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'results': ddm_results,
                'watch_list': watch_list_name
            }

            filename = f"ddm_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_path / filename

            with open(filepath, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            logger.info(f"DDM analysis captured for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Failed to capture DDM analysis for {ticker}: {e}")
            return False

    def capture_pb_analysis(
        self,
        ticker: str,
        company_name: str,
        pb_results: Dict[str, Any],
        watch_list_name: Optional[str] = None
    ) -> bool:
        """
        Capture P/B analysis results

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            pb_results: P/B analysis results dictionary
            watch_list_name: Optional watch list to add to

        Returns:
            bool: Success status
        """
        try:
            analysis_data = {
                'analysis_type': 'PB',
                'ticker': ticker,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'results': pb_results,
                'watch_list': watch_list_name
            }

            filename = f"pb_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_path / filename

            with open(filepath, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            logger.info(f"P/B analysis captured for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Failed to capture P/B analysis for {ticker}: {e}")
            return False

    def get_analysis_history(
        self,
        ticker: Optional[str] = None,
        analysis_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get analysis history

        Args:
            ticker: Filter by ticker (optional)
            analysis_type: Filter by analysis type (optional)

        Returns:
            List of analysis records
        """
        try:
            results = []
            for file_path in self.storage_path.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Apply filters
                    if ticker and data.get('ticker') != ticker:
                        continue
                    if analysis_type and data.get('analysis_type') != analysis_type:
                        continue

                    results.append(data)

                except Exception as e:
                    logger.warning(f"Failed to load analysis file {file_path}: {e}")

            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return results

        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []

    def capture_to_multiple_lists(
        self,
        ticker: str,
        company_name: str,
        analysis_results: Dict[str, Any],
        watch_list_names: List[str],
        analysis_type: str = "DCF",
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Capture analysis results to multiple watch lists

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            analysis_results: Analysis results from any valuator
            watch_list_names: List of watch list names to capture to
            analysis_type: Type of analysis ("DCF", "DDM", "PB")
            market_data: Market data (price, etc.)

        Returns:
            Dict mapping watch list names to success status
        """
        results = {}

        for watch_list_name in watch_list_names:
            try:
                # Use the appropriate capture method based on analysis type
                if analysis_type.upper() == "DCF":
                    success = self.capture_dcf_analysis(
                        ticker=ticker,
                        company_name=company_name,
                        dcf_results=analysis_results,
                        watch_list_name=watch_list_name
                    )
                elif analysis_type.upper() == "DDM":
                    success = self.capture_ddm_analysis(
                        ticker=ticker,
                        company_name=company_name,
                        ddm_results=analysis_results,
                        watch_list_name=watch_list_name
                    )
                elif analysis_type.upper() == "PB":
                    success = self.capture_pb_analysis(
                        ticker=ticker,
                        company_name=company_name,
                        pb_results=analysis_results,
                        watch_list_name=watch_list_name
                    )
                else:
                    logger.warning(f"Unknown analysis type: {analysis_type}")
                    success = False

                results[watch_list_name] = success

            except Exception as e:
                logger.error(
                    f"Error capturing {analysis_type} to watch list '{watch_list_name}': {e}"
                )
                results[watch_list_name] = False

        return results


# Global instance for easy access
analysis_capture = AnalysisCapture()