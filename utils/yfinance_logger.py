"""
Yahoo Finance API Request Logger

This module provides comprehensive logging for Yahoo Finance API requests,
tracking each step of the process from ticker validation to data extraction.
"""

import logging
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os


class YFinanceLogger:
    """
    Specialized logger for Yahoo Finance API requests with step-by-step monitoring.

    Features:
    - Request lifecycle tracking
    - Performance metrics
    - Data extraction logging
    - Configurable verbosity levels
    - Log rotation and management
    """

    def __init__(
        self,
        name: str = "yfinance_api",
        log_level: str = "INFO",
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
    ):
        """
        Initialize the Yahoo Finance logger.

        Args:
            name (str): Logger name
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
            log_dir (str): Directory for log files
            max_file_size (int): Maximum log file size in bytes
            backup_count (int): Number of backup files to keep
            enable_console (bool): Whether to enable console logging
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        self.simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'
        )

        # Setup file handler with rotation
        log_file = self.log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(file_handler)

        # Setup console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self.simple_formatter)
            self.logger.addHandler(console_handler)

        # Request tracking
        self._current_request = None
        self._request_start_time = None
        self._step_times = []

        self.logger.info(f"YFinance Logger initialized - Level: {log_level}, LogDir: {log_dir}")

    def start_request(self, ticker: str, request_type: str = "market_data") -> str:
        """
        Start tracking a new API request.

        Args:
            ticker (str): Stock ticker symbol
            request_type (str): Type of request being made

        Returns:
            str: Request ID for tracking
        """
        request_id = f"{ticker}_{request_type}_{int(time.time())}"
        self._current_request = {
            'request_id': request_id,
            'ticker': ticker,
            'request_type': request_type,
            'start_time': datetime.now(),
            'steps': [],
            'performance_metrics': {},
        }
        self._request_start_time = time.time()
        self._step_times = []

        self.logger.info("=" * 80)
        self.logger.info(f"🚀 STARTING API REQUEST | Request ID: {request_id}")
        self.logger.info(f"   Ticker: {ticker}")
        self.logger.info(f"   Type: {request_type}")
        self.logger.info(
            f"   Start Time: {self._current_request['start_time'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.logger.info("=" * 80)

        return request_id

    def log_step(self, step_name: str, details: Dict[str, Any], level: str = "INFO") -> None:
        """
        Log a step in the API request process.

        Args:
            step_name (str): Name of the current step
            details (Dict[str, Any]): Step details and values
            level (str): Log level for this step
        """
        if not self._current_request:
            self.logger.warning("No active request to log step for")
            return

        current_time = time.time()
        step_duration = current_time - (
            self._step_times[-1] if self._step_times else self._request_start_time
        )
        self._step_times.append(current_time)

        step_info = {
            'step_name': step_name,
            'timestamp': datetime.now().isoformat(),
            'duration_ms': round(step_duration * 1000, 2),
            'details': details,
        }

        self._current_request['steps'].append(step_info)

        log_method = getattr(self.logger, level.lower())
        log_method(f"📋 STEP: {step_name}")
        log_method(f"   ⏱️  Duration: {step_duration:.3f}s")

        # Log details in a structured way
        if details:
            log_method("   📊 Details:")
            for key, value in details.items():
                # Truncate very long values for readability
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                elif isinstance(value, (dict, list)):
                    try:
                        value = json.dumps(value, indent=2)[:500]
                        if len(json.dumps(value)) > 500:
                            value += "..."
                    except:
                        value = str(value)[:200] + "..."

                log_method(f"      {key}: {value}")

    def log_validation(self, ticker: str, validation_result: Dict[str, Any]) -> None:
        """Log ticker validation results."""
        self.log_step(
            "Pre-flight Validation",
            {
                'ticker': ticker,
                'is_valid': validation_result.get('is_valid', False),
                'validation_errors': validation_result.get('errors', []),
                'validation_warnings': validation_result.get('warnings', []),
            },
            level="INFO" if validation_result.get('is_valid', False) else "WARNING",
        )

    def log_cache_check(
        self, cache_key: str, cache_hit: bool, cache_age: Optional[float] = None
    ) -> None:
        """Log cache hit/miss information."""
        details = {
            'cache_key': cache_key,
            'cache_hit': cache_hit,
            'cache_age_hours': round(cache_age / 3600, 2) if cache_age else None,
        }

        self.log_step(f"Cache {'Hit' if cache_hit else 'Miss'}", details, level="DEBUG")

    def log_rate_limiting(self, delay_seconds: float, reason: str) -> None:
        """Log rate limiting delays."""
        self.log_step(
            "Rate Limiting", {'delay_seconds': delay_seconds, 'reason': reason}, level="INFO"
        )

    def log_api_request(self, url: str, headers: Dict[str, str], timeout: tuple) -> None:
        """Log outgoing API request details."""
        self.log_step(
            "API Request",
            {
                'url': url,
                'headers': {
                    k: v
                    for k, v in headers.items()
                    if k.lower() not in ['authorization', 'api-key']
                },
                'timeout': timeout,
            },
            level="DEBUG",
        )

    def log_api_response(self, status_code: int, response_size: int, response_time: float) -> None:
        """Log API response information."""
        self.log_step(
            "API Response",
            {
                'status_code': status_code,
                'response_size_bytes': response_size,
                'response_time_ms': round(response_time * 1000, 2),
            },
            level="INFO" if status_code == 200 else "WARNING",
        )

    def log_data_extraction(self, extraction_results: Dict[str, Any]) -> None:
        """Log data extraction and processing results."""
        self.log_step("Data Extraction", extraction_results, level="INFO")

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log errors with context and traceback."""
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc(),
        }

        self.log_step("Error Occurred", error_details, level="ERROR")

    def log_retry_attempt(self, attempt: int, max_attempts: int, delay: float, reason: str) -> None:
        """Log retry attempts."""
        self.log_step(
            f"Retry Attempt {attempt}/{max_attempts}",
            {
                'attempt': attempt,
                'max_attempts': max_attempts,
                'delay_seconds': delay,
                'reason': reason,
            },
            level="WARNING",
        )

    def finish_request(self, success: bool, final_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Finish tracking the current request and log summary.

        Args:
            success (bool): Whether the request was successful
            final_data (Optional[Dict[str, Any]]): Final extracted data
        """
        if not self._current_request:
            self.logger.warning("No active request to finish")
            return

        total_time = time.time() - self._request_start_time

        # Calculate performance metrics
        self._current_request['performance_metrics'] = {
            'total_duration_seconds': round(total_time, 3),
            'total_steps': len(self._current_request['steps']),
            'success': success,
            'end_time': datetime.now().isoformat(),
        }

        # Log final summary
        status_emoji = "✅" if success else "❌"
        self.logger.info("=" * 80)
        self.logger.info(
            f"{status_emoji} REQUEST COMPLETED | Status: {'SUCCESS' if success else 'FAILED'}"
        )
        self.logger.info(f"   Request ID: {self._current_request['request_id']}")
        self.logger.info(f"   Total Duration: {total_time:.3f}s")
        self.logger.info(f"   Steps Completed: {len(self._current_request['steps'])}")

        if final_data:
            self.logger.info("   📊 Final Data Summary:")
            for key, value in final_data.items():
                if isinstance(value, (int, float)):
                    self.logger.info(f"      {key}: {value:,}")
                else:
                    self.logger.info(f"      {key}: {str(value)[:100]}...")

        self.logger.info("=" * 80)

        # Reset tracking
        self._current_request = None
        self._request_start_time = None
        self._step_times = []

    def get_current_request_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of current request for debugging."""
        return self._current_request.copy() if self._current_request else None

    def set_log_level(self, level: str) -> None:
        """Change the logging level dynamically."""
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.info(f"Log level changed to: {level.upper()}")

    def export_request_log(self, request_id: str, output_file: str) -> bool:
        """Export request log to JSON file."""
        if not self._current_request or self._current_request['request_id'] != request_id:
            return False

        try:
            with open(output_file, 'w') as f:
                json.dump(self._current_request, f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Failed to export request log: {e}")
            return False


# Global logger instance
_global_logger = None


def get_yfinance_logger(
    log_level: str = "INFO", log_dir: str = "logs", enable_console: bool = True
) -> YFinanceLogger:
    """Get or create global YFinance logger instance."""
    global _global_logger

    if _global_logger is None:
        _global_logger = YFinanceLogger(
            log_level=log_level, log_dir=log_dir, enable_console=enable_console
        )

    return _global_logger
