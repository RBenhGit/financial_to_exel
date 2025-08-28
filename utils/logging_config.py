"""
Centralized Logging Configuration for Financial Analysis Application

This module provides comprehensive logging setup using Loguru for enhanced
debugging, error tracking, and API call monitoring throughout the application.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import streamlit as st


class LoggingConfig:
    """Centralized logging configuration and management"""

    def __init__(self, app_name: str = "FinancialAnalysis"):
        self.app_name = app_name
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self._setup_complete = False

    def setup_logging(self, debug_mode: bool = False, log_to_file: bool = True) -> None:
        """
        Setup comprehensive logging configuration
        
        Args:
            debug_mode: Enable debug level logging
            log_to_file: Enable file logging
        """
        if self._setup_complete:
            return

        # Remove default handler
        logger.remove()

        # Console logging with colors and structured format
        log_level = "DEBUG" if debug_mode else "INFO"
        
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

        if log_to_file:
            # General application log
            logger.add(
                self.log_dir / "app_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                level=log_level,
                rotation="1 day",
                retention="30 days",
                backtrace=True,
                diagnose=True
            )

            # API-specific log for debugging data source issues
            logger.add(
                self.log_dir / "api_calls_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | API | {message}",
                level="DEBUG",
                rotation="1 day",
                retention="7 days",
                filter=lambda record: "API" in record["extra"].get("context", ""),
                backtrace=True
            )

            # Error-only log for production monitoring
            logger.add(
                self.log_dir / "errors_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                level="ERROR",
                rotation="1 week",
                retention="60 days",
                backtrace=True,
                diagnose=True
            )

        self._setup_complete = True
        logger.info(f"Logging initialized for {self.app_name}", extra={"context": "SYSTEM"})

    def get_api_logger(self) -> Any:
        """Get logger specifically configured for API calls"""
        return logger.bind(context="API")

    def get_data_logger(self) -> Any:
        """Get logger specifically configured for data processing"""
        return logger.bind(context="DATA")

    def get_streamlit_logger(self) -> Any:
        """Get logger specifically configured for Streamlit UI"""
        return logger.bind(context="UI")

    def log_api_call(self, provider: str, endpoint: str, ticker: str, 
                     status: str, response_time: float, error: Optional[str] = None) -> None:
        """
        Log API call with structured data for monitoring
        
        Args:
            provider: API provider name (e.g., 'FMP', 'AlphaVantage')
            endpoint: API endpoint called
            ticker: Stock ticker requested
            status: 'SUCCESS' or 'FAILED'
            response_time: Time taken for the call in seconds
            error: Error message if failed
        """
        api_logger = self.get_api_logger()
        
        log_data = {
            "provider": provider,
            "endpoint": endpoint,
            "ticker": ticker,
            "status": status,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": None  # Will be filled by loguru
        }

        if status == "SUCCESS":
            api_logger.info(f"API_CALL | {provider} | {ticker} | {response_time:.2f}s | SUCCESS", **log_data)
        else:
            log_data["error"] = error
            api_logger.error(f"API_CALL | {provider} | {ticker} | {response_time:.2f}s | FAILED: {error}", **log_data)

    def log_data_processing(self, step: str, ticker: str, input_size: int, 
                           output_size: int, success: bool, error: Optional[str] = None) -> None:
        """
        Log data processing steps for debugging pipeline issues
        
        Args:
            step: Processing step name (e.g., 'data_conversion', 'fcf_calculation')
            ticker: Stock ticker being processed
            input_size: Size of input data
            output_size: Size of output data (0 if failed)
            success: Whether the step succeeded
            error: Error message if failed
        """
        data_logger = self.get_data_logger()
        
        log_data = {
            "step": step,
            "ticker": ticker,
            "input_size": input_size,
            "output_size": output_size,
            "success": success
        }

        if success:
            data_logger.info(f"DATA_PROCESSING | {step} | {ticker} | {input_size}→{output_size} | SUCCESS", **log_data)
        else:
            log_data["error"] = error
            data_logger.error(f"DATA_PROCESSING | {step} | {ticker} | {input_size}→{output_size} | FAILED: {error}", **log_data)

    @staticmethod
    def setup_streamlit_logging() -> None:
        """Setup logging for Streamlit application context"""
        # Configure Streamlit logging to work with Loguru
        import logging
        
        # Intercept standard logging and redirect to Loguru
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                # Find caller from where originated the logging call
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

        # Replace streamlit's logger
        streamlit_logger = logging.getLogger("streamlit")
        streamlit_logger.handlers = [InterceptHandler()]


# Global logging instance
_logging_config = LoggingConfig()


def setup_app_logging(debug_mode: bool = None) -> LoggingConfig:
    """
    Initialize application-wide logging
    
    Args:
        debug_mode: Enable debug logging. If None, determines from environment
    
    Returns:
        LoggingConfig instance
    """
    if debug_mode is None:
        # Check if we're in development mode
        debug_mode = (
            os.getenv("DEBUG", "").lower() in ["true", "1", "yes"] or
            os.getenv("ENVIRONMENT", "").lower() == "development"
        )
    
    _logging_config.setup_logging(debug_mode=debug_mode, log_to_file=True)
    _logging_config.setup_streamlit_logging()
    
    return _logging_config


def get_logger() -> Any:
    """Get the main application logger"""
    return logger


def get_api_logger() -> Any:
    """Get API-specific logger"""
    return _logging_config.get_api_logger()


def get_data_logger() -> Any:
    """Get data processing logger"""
    return _logging_config.get_data_logger()


def get_streamlit_logger() -> Any:
    """Get Streamlit UI logger"""
    return _logging_config.get_streamlit_logger()


# Convenience function for structured exception logging
def log_exception(context: str, error: Exception, **kwargs) -> None:
    """
    Log exception with full context and traceback
    
    Args:
        context: Context where error occurred
        error: The exception object
        **kwargs: Additional context data
    """
    logger.bind(context=context).exception(f"Exception in {context}: {str(error)}", **kwargs)


# Export the logging configuration instance
__all__ = [
    'LoggingConfig',
    'setup_app_logging',
    'get_logger',
    'get_api_logger', 
    'get_data_logger',
    'get_streamlit_logger',
    'log_exception'
]