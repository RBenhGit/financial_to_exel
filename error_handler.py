"""
Enhanced Error Handling and Logging Module

This module provides comprehensive error handling, logging, and debugging
utilities to make the application more robust and easier to troubleshoot.
"""

import logging
import sys
import traceback
import functools
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
from pathlib import Path
from config import get_config

class FinancialAnalysisError(Exception):
    """Base exception class for financial analysis errors"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary for logging"""
        return {
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'type': self.__class__.__name__
        }

class ExcelDataError(FinancialAnalysisError):
    """Error related to Excel data processing"""
    pass

class ValidationError(FinancialAnalysisError):
    """Error related to data validation"""
    pass

class CalculationError(FinancialAnalysisError):
    """Error related to financial calculations"""
    pass

class ConfigurationError(FinancialAnalysisError):
    """Error related to configuration"""
    pass

class EnhancedLogger:
    """Enhanced logging utility with structured logging and error tracking"""
    
    def __init__(self, name: str, log_file: str = None):
        """
        Initialize enhanced logger
        
        Args:
            name (str): Logger name
            log_file (str): Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.error_history = []
        self.warning_history = []
        self.log_file = log_file
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._configure_logger()
    
    def _configure_logger(self):
        """Configure the logger with appropriate handlers and formatters"""
        config = get_config()
        
        # Set log level
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            config.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, context: Dict = None, **kwargs):
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Dict = None, **kwargs):
        """Log info message with context"""
        self._log_with_context(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Dict = None, **kwargs):
        """Log warning message with context and track in history"""
        self._log_with_context(logging.WARNING, message, context, **kwargs)
        self.warning_history.append({
            'message': message,
            'context': context or {},
            'timestamp': datetime.now(),
            'kwargs': kwargs
        })
    
    def error(self, message: str, context: Dict = None, error: Exception = None, **kwargs):
        """Log error message with context and track in history"""
        self._log_with_context(logging.ERROR, message, context, error=error, **kwargs)
        self.error_history.append({
            'message': message,
            'context': context or {},
            'error': str(error) if error else None,
            'timestamp': datetime.now(),
            'kwargs': kwargs
        })
    
    def critical(self, message: str, context: Dict = None, error: Exception = None, **kwargs):
        """Log critical message with context"""
        self._log_with_context(logging.CRITICAL, message, context, error=error, **kwargs)
        self.error_history.append({
            'message': message,
            'context': context or {},
            'error': str(error) if error else None,
            'timestamp': datetime.now(),
            'kwargs': kwargs,
            'level': 'CRITICAL'
        })
    
    def _log_with_context(self, level: int, message: str, context: Dict = None, error: Exception = None, **kwargs):
        """Log message with structured context"""
        # Build structured log entry
        log_entry = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'kwargs': kwargs
        }
        
        # Add error details if provided
        if error:
            log_entry['error'] = {
                'type': error.__class__.__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }
        
        # Log the structured entry
        self.logger.log(level, json.dumps(log_entry, default=str))
    
    def log_function_call(self, func_name: str, args: tuple = None, kwargs: dict = None, result: Any = None, error: Exception = None):
        """Log function call details for debugging"""
        log_entry = {
            'function': func_name,
            'args': str(args) if args else None,
            'kwargs': kwargs or {},
            'result_type': type(result).__name__ if result is not None else None,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            self.error(f"Function {func_name} failed", context=log_entry, error=error)
        else:
            self.debug(f"Function {func_name} completed", context=log_entry)
    
    def get_error_summary(self) -> Dict:
        """Get summary of errors and warnings"""
        return {
            'total_errors': len(self.error_history),
            'total_warnings': len(self.warning_history),
            'recent_errors': self.error_history[-5:] if self.error_history else [],
            'recent_warnings': self.warning_history[-5:] if self.warning_history else []
        }
    
    def save_error_log(self, file_path: str = None):
        """Save error history to file"""
        if file_path is None:
            file_path = f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        log_data = {
            'summary': self.get_error_summary(),
            'errors': self.error_history,
            'warnings': self.warning_history,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        self.info(f"Error log saved to {file_path}")

def with_error_handling(error_type: type = FinancialAnalysisError, 
                       return_on_error: Any = None,
                       log_errors: bool = True,
                       re_raise: bool = False):
    """
    Decorator for enhanced error handling
    
    Args:
        error_type: Type of error to catch and convert
        return_on_error: Value to return on error
        log_errors: Whether to log errors
        re_raise: Whether to re-raise the error after handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = EnhancedLogger(func.__module__)
            
            try:
                logger.debug(f"Calling function {func.__name__}", 
                           context={'args': str(args), 'kwargs': kwargs})
                
                result = func(*args, **kwargs)
                
                logger.debug(f"Function {func.__name__} completed successfully", 
                           context={'result_type': type(result).__name__})
                
                return result
                
            except Exception as e:
                error_context = {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': kwargs,
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
                
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}", 
                               context=error_context, error=e)
                
                if re_raise:
                    if isinstance(e, FinancialAnalysisError):
                        raise
                    else:
                        # Convert to custom error type
                        raise error_type(f"Error in {func.__name__}: {str(e)}", 
                                       context=error_context) from e
                
                return return_on_error
        
        return wrapper
    return decorator

def validate_excel_file(file_path: str) -> bool:
    """
    Validate Excel file exists and is accessible
    
    Args:
        file_path (str): Path to Excel file
        
    Returns:
        bool: True if file is valid
        
    Raises:
        ExcelDataError: If file is invalid
    """
    logger = EnhancedLogger(__name__)
    
    if not file_path:
        raise ExcelDataError("Excel file path is empty", error_code="EMPTY_PATH")
    
    path = Path(file_path)
    
    if not path.exists():
        raise ExcelDataError(f"Excel file not found: {file_path}", 
                           error_code="FILE_NOT_FOUND",
                           context={'file_path': file_path})
    
    if not path.is_file():
        raise ExcelDataError(f"Path is not a file: {file_path}", 
                           error_code="NOT_A_FILE",
                           context={'file_path': file_path})
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        raise ExcelDataError(f"File is not an Excel file: {file_path}", 
                           error_code="INVALID_EXTENSION",
                           context={'file_path': file_path})
    
    logger.info(f"Excel file validation passed: {file_path}")
    return True

def validate_financial_data(data: Any, data_type: str, required_fields: List[str] = None) -> bool:
    """
    Validate financial data structure
    
    Args:
        data: Data to validate
        data_type (str): Type of data being validated
        required_fields (List[str]): Required fields in the data
        
    Returns:
        bool: True if data is valid
        
    Raises:
        ValidationError: If data is invalid
    """
    logger = EnhancedLogger(__name__)
    
    if data is None:
        raise ValidationError(f"{data_type} data is None", 
                            error_code="NULL_DATA",
                            context={'data_type': data_type})
    
    if required_fields:
        missing_fields = []
        if isinstance(data, dict):
            missing_fields = [field for field in required_fields if field not in data]
        elif hasattr(data, '__dict__'):
            missing_fields = [field for field in required_fields if not hasattr(data, field)]
        
        if missing_fields:
            raise ValidationError(f"Missing required fields in {data_type}: {missing_fields}", 
                                error_code="MISSING_FIELDS",
                                context={'data_type': data_type, 'missing_fields': missing_fields})
    
    logger.debug(f"Financial data validation passed for {data_type}")
    return True

def handle_calculation_error(func_name: str, error: Exception, context: Dict = None) -> None:
    """
    Handle calculation errors with proper logging and context
    
    Args:
        func_name (str): Name of the function where error occurred
        error (Exception): The error that occurred
        context (Dict): Additional context about the error
    """
    logger = EnhancedLogger(__name__)
    
    error_context = {
        'function': func_name,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        **(context or {})
    }
    
    logger.error(f"Calculation error in {func_name}", context=error_context, error=error)
    
    # Save detailed error log for debugging
    logger.save_error_log(f"calculation_error_{func_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

def create_error_summary(errors: List[Dict], warnings: List[Dict]) -> Dict:
    """
    Create comprehensive error summary
    
    Args:
        errors (List[Dict]): List of error records
        warnings (List[Dict]): List of warning records
        
    Returns:
        Dict: Error summary
    """
    summary = {
        'total_errors': len(errors),
        'total_warnings': len(warnings),
        'error_types': {},
        'warning_types': {},
        'critical_errors': [],
        'recommendations': []
    }
    
    # Categorize errors
    for error in errors:
        error_type = error.get('type', 'Unknown')
        summary['error_types'][error_type] = summary['error_types'].get(error_type, 0) + 1
        
        if error.get('level') == 'CRITICAL':
            summary['critical_errors'].append(error)
    
    # Categorize warnings
    for warning in warnings:
        warning_type = warning.get('type', 'Unknown')
        summary['warning_types'][warning_type] = summary['warning_types'].get(warning_type, 0) + 1
    
    # Generate recommendations
    if summary['total_errors'] > 0:
        summary['recommendations'].append("Review error logs and fix critical issues before proceeding")
    
    if summary['total_warnings'] > 10:
        summary['recommendations'].append("High number of warnings detected - consider data quality review")
    
    if 'ExcelDataError' in summary['error_types']:
        summary['recommendations'].append("Excel file format issues detected - verify file structure")
    
    return summary

# Global logger instance
global_logger = EnhancedLogger(__name__)

# Convenience functions
def log_info(message: str, context: Dict = None, **kwargs):
    """Log info message using global logger"""
    global_logger.info(message, context, **kwargs)

def log_warning(message: str, context: Dict = None, **kwargs):
    """Log warning message using global logger"""
    global_logger.warning(message, context, **kwargs)

def log_error(message: str, context: Dict = None, error: Exception = None, **kwargs):
    """Log error message using global logger"""
    global_logger.error(message, context, error, **kwargs)

def log_debug(message: str, context: Dict = None, **kwargs):
    """Log debug message using global logger"""
    global_logger.debug(message, context, **kwargs)

if __name__ == "__main__":
    # Test the error handling system
    logger = EnhancedLogger(__name__)
    
    # Test normal logging
    logger.info("Testing enhanced logging system")
    logger.warning("This is a test warning", context={'test': True})
    
    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Test error occurred", error=e, context={'test_context': 'example'})
    
    # Test decorator
    @with_error_handling(error_type=CalculationError, return_on_error=0)
    def test_function(x, y):
        if x == 0:
            raise ValueError("Division by zero")
        return y / x
    
    result = test_function(0, 10)  # Should handle error and return 0
    print(f"Result: {result}")
    
    # Test validation
    try:
        validate_excel_file("nonexistent.xlsx")
    except ExcelDataError as e:
        print(f"Validation error: {e}")
    
    # Print error summary
    summary = logger.get_error_summary()
    print(f"Error summary: {summary}")