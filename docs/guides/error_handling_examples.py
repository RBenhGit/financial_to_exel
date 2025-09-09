"""
Error Handling Examples
=======================

This module demonstrates how to use the enhanced error handling system
across different parts of the financial analysis application.
"""

from error_handler import (
    # Exception classes
    DataSourceError,
    ValidationError,
    DCFCalculationError,
    MissingDataError,
    InvalidDataError,
    
    # Validation functions
    validate_required_fields,
    validate_numeric_range,
    validate_positive_number,
    require_data,
    require_positive,
    
    # Context managers and decorators
    error_context,
    with_error_handling,
    fail_fast_validation,
    
    # Logging utilities
    get_module_logger,
    setup_consistent_logging,
    get_error_statistics,
    
    # Error handling utilities
    handle_financial_error,
    safe_operation
)
import logging


def example_data_validation():
    """Example of using validation functions with proper error handling"""
    logger = get_module_logger(__name__)
    
    # Example: Validate financial data structure
    try:
        financial_data = {
            "revenue": 1000000,
            "expenses": 750000,
            "growth_rate": 5.5,
            # "net_income": missing field
        }
        
        # Validate required fields - this will raise MissingDataError
        validate_required_fields(
            financial_data, 
            required_fields=["revenue", "expenses", "net_income"],
            data_type="financial_statements"
        )
        
    except MissingDataError as e:
        logger.error(f"Validation failed: {e.user_message}")
        logger.info(f"Recovery suggestions: {e.recovery_suggestions}")
        return None
    
    return financial_data


def example_dcf_calculation(financial_data):
    """Example of DCF calculation with error handling"""
    
    @fail_fast_validation(
        lambda args, kwargs: require_data(args[0], "financial_data"),
        lambda args, kwargs: require_positive(args[0].get("free_cash_flow", 0), "free_cash_flow")
    )
    def calculate_dcf_value(data):
        """Calculate DCF value with input validation"""
        
        with error_context("dcf_calculation", company=data.get("company", "Unknown")):
            # Simulate DCF calculation
            fcf = data["free_cash_flow"]
            discount_rate = data.get("discount_rate", 0.10)
            growth_rate = data.get("growth_rate", 0.03)
            
            # Validate rates
            validate_numeric_range(discount_rate, "discount_rate", 0.01, 0.50)
            validate_numeric_range(growth_rate, "growth_rate", -0.10, 0.30)
            
            if discount_rate <= growth_rate:
                raise DCFCalculationError(
                    f"Discount rate ({discount_rate:.1%}) must be greater than growth rate ({growth_rate:.1%})",
                    error_code="INVALID_RATE_RELATIONSHIP",
                    context={
                        "discount_rate": discount_rate,
                        "growth_rate": growth_rate
                    },
                    recovery_suggestions=[
                        "Increase discount rate or decrease growth rate",
                        "Review financial assumptions"
                    ]
                )
            
            # Calculate terminal value
            terminal_fcf = fcf * (1 + growth_rate)
            terminal_value = terminal_fcf / (discount_rate - growth_rate)
            
            return {
                "terminal_value": terminal_value,
                "terminal_fcf": terminal_fcf,
                "assumptions": {
                    "discount_rate": discount_rate,
                    "growth_rate": growth_rate
                }
            }
    
    try:
        return calculate_dcf_value(financial_data)
    except Exception as e:
        # Handle any unexpected errors
        return safe_operation(
            lambda: calculate_dcf_value(financial_data),
            operation_name="dcf_calculation_fallback",
            default_return={"error": "Calculation failed", "message": str(e)}
        )


def example_api_data_fetching(symbol: str):
    """Example of API data fetching with comprehensive error handling"""
    logger = get_module_logger(__name__)
    
    with error_context("api_data_fetch", symbol=symbol):
        try:
            # Validate input
            require_data(symbol, "stock_symbol")
            
            if not isinstance(symbol, str) or len(symbol) < 1:
                raise InvalidDataError(
                    f"Invalid stock symbol: {symbol}",
                    error_code="INVALID_SYMBOL",
                    context={"symbol": symbol},
                    recovery_suggestions=["Provide a valid stock symbol (e.g., 'AAPL', 'MSFT')"]
                )
            
            # Simulate API call that might fail
            if symbol.upper() == "INVALID":
                raise DataSourceError(
                    f"API returned no data for symbol: {symbol}",
                    error_code="NO_DATA_FOUND",
                    context={"symbol": symbol, "api": "mock_api"},
                    recovery_suggestions=[
                        "Check if the symbol is correct",
                        "Try again later",
                        "Use a different data source"
                    ]
                )
            
            # Mock successful response
            return {
                "symbol": symbol.upper(),
                "price": 150.25,
                "volume": 1000000,
                "market_cap": 2500000000
            }
            
        except Exception as e:
            # Convert to financial error with context
            financial_error = handle_financial_error(
                e, 
                operation="api_data_fetch",
                context={"symbol": symbol, "api_provider": "mock_api"}
            )
            raise financial_error


@with_error_handling(
    error_type=ValidationError,
    return_on_error=None,
    log_errors=True,
    re_raise=True
)
def example_excel_processing(file_path: str):
    """Example of Excel processing with decorator-based error handling"""
    
    # Validate file path
    require_data(file_path, "excel_file_path")
    
    # This would normally process Excel file
    # For demo, we'll just validate the path format
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        raise ValidationError(
            f"Invalid Excel file extension: {file_path}",
            error_code="INVALID_FILE_TYPE",
            recovery_suggestions=["Use .xlsx or .xls file format"]
        )
    
    return {"status": "success", "file": file_path}


def demonstrate_error_handling():
    """Demonstrate various error handling scenarios"""
    
    # Set up consistent logging
    setup_consistent_logging(
        log_level="INFO",
        enable_file_logging=False  # Set to True to enable file logging
    )
    
    logger = get_module_logger(__name__)
    logger.info("Starting error handling demonstrations")
    
    print("=== Error Handling Examples ===\n")
    
    # Example 1: Data validation
    print("1. Data Validation Example:")
    result = example_data_validation()
    if result is None:
        print("   [PASS] Missing data was properly detected and handled\n")
    
    # Example 2: DCF calculation with validation
    print("2. DCF Calculation Example:")
    try:
        dcf_data = {
            "company": "Example Corp",
            "free_cash_flow": 100000000,
            "discount_rate": 0.10,
            "growth_rate": 0.03
        }
        result = example_dcf_calculation(dcf_data)
        print(f"   [PASS] DCF calculation successful: Terminal Value = ${result['terminal_value']:,.0f}\n")
    except Exception as e:
        print(f"   [FAIL] DCF calculation failed: {e}\n")
    
    # Example 3: API data fetching
    print("3. API Data Fetching Examples:")
    
    # Successful case
    try:
        data = example_api_data_fetching("AAPL")
        print(f"   [PASS] Successfully fetched data for {data['symbol']}: ${data['price']}\n")
    except Exception as e:
        print(f"   [FAIL] API fetch failed: {e}\n")
    
    # Failed case
    try:
        data = example_api_data_fetching("INVALID")
        print(f"   Unexpected success: {data}")
    except DataSourceError as e:
        print(f"   [PASS] API error properly handled: {e.user_message}")
        print(f"     Recovery suggestions: {', '.join(e.recovery_suggestions)}\n")
    
    # Example 4: Excel processing with decorator
    print("4. Excel Processing Example:")
    try:
        result = example_excel_processing("data.xlsx")
        print(f"   [PASS] Excel processing successful: {result['status']}\n")
    except ValidationError as e:
        print(f"   [FAIL] Excel processing failed: {e.user_message}\n")
    
    # Show error statistics
    print("5. Error Statistics:")
    stats = get_error_statistics()
    print(f"   Total operations: {stats['total_operations']}")
    print(f"   Failed operations: {stats['failed_operations']}")
    print(f"   Success rate: {stats['success_rate_percent']}%")
    print(f"   Total errors: {stats['total_errors']}")
    print(f"   Total warnings: {stats['total_warnings']}")
    if stats['error_breakdown']:
        print(f"   Error types: {stats['error_breakdown']}")
    
    logger.info("Error handling demonstrations completed")


if __name__ == "__main__":
    demonstrate_error_handling()