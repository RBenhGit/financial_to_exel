"""
Test data validation functionality
"""
import pytest
from data_sources import FinancialDataRequest, DataQualityMetrics


def test_financial_data_request_creation():
    """Test basic FinancialDataRequest creation and validation"""
    
    # Test basic creation
    request = FinancialDataRequest(ticker="AAPL")
    assert request.ticker == "AAPL"
    assert request.data_types == ['price', 'fundamentals']
    assert request.period == 'annual'
    assert request.limit == 10
    assert request.force_refresh == False
    
    # Test custom parameters
    custom_request = FinancialDataRequest(
        ticker="MSFT",
        data_types=['price', 'fundamentals', 'ratios'],
        period='quarterly',
        limit=20,
        force_refresh=True
    )
    
    assert custom_request.ticker == "MSFT"
    assert custom_request.data_types == ['price', 'fundamentals', 'ratios']
    assert custom_request.period == 'quarterly'
    assert custom_request.limit == 20
    assert custom_request.force_refresh == True


def test_data_quality_metrics():
    """Test DataQualityMetrics functionality"""
    
    # Test default creation
    metrics = DataQualityMetrics()
    assert metrics.completeness == 0.0
    assert metrics.accuracy == 0.0
    assert metrics.timeliness == 0.0
    assert metrics.consistency == 0.0
    assert metrics.overall_score == 0.0
    
    # Test with custom values
    custom_metrics = DataQualityMetrics(
        completeness=0.95,
        accuracy=0.88,
        timeliness=0.92,
        consistency=0.85
    )
    
    assert custom_metrics.completeness == 0.95
    assert custom_metrics.accuracy == 0.88
    assert custom_metrics.timeliness == 0.92
    assert custom_metrics.consistency == 0.85
    
    # Test overall score calculation
    custom_metrics.calculate_overall_score()
    # Should be average of the four components
    expected_score = (0.95 + 0.88 + 0.92 + 0.85) / 4
    assert abs(custom_metrics.overall_score - expected_score) < 0.01  # More lenient tolerance


def test_error_handler_validation():
    """Test error handler validation functions"""
    from error_handler import validate_financial_data, ValidationError
    
    # Test with valid data - should not raise exception
    valid_data = {
        'revenue': 1000000,
        'expenses': 800000,
        'net_income': 200000
    }
    
    try:
        result = validate_financial_data(
            valid_data, 
            'income_statement',
            required_fields=['revenue', 'expenses', 'net_income']
        )
        assert result == True  # Should return True if no exception
    except ValidationError:
        pytest.fail("Valid data should not raise ValidationError")
    
    # Test with invalid data (missing field) - should raise exception
    invalid_data = {
        'revenue': 1000000,
        'expenses': 800000
        # missing net_income
    }
    
    with pytest.raises(ValidationError):
        validate_financial_data(
            invalid_data,
            'income_statement', 
            required_fields=['revenue', 'expenses', 'net_income']
        )


def test_excel_file_validation():
    """Test Excel file validation functionality"""
    from error_handler import validate_excel_file, ExcelDataError
    
    # Test with non-existent file - should raise exception
    with pytest.raises(ExcelDataError):
        validate_excel_file("nonexistent_file.xlsx")
    
    # Test with invalid extension - should raise exception  
    with pytest.raises(ExcelDataError):
        validate_excel_file("test_file.txt")


def test_error_classes():
    """Test custom error classes"""
    from error_handler import (
        FinancialAnalysisError,
        ExcelDataError, 
        ValidationError,
        CalculationError
    )
    
    # Test error class hierarchy
    assert issubclass(ExcelDataError, FinancialAnalysisError)
    assert issubclass(ValidationError, FinancialAnalysisError)
    assert issubclass(CalculationError, FinancialAnalysisError)
    
    # Test error creation
    try:
        raise ValidationError("Test validation error")
    except ValidationError as e:
        assert str(e) == "Test validation error"
        assert isinstance(e, FinancialAnalysisError)
    
    try:
        raise CalculationError("Test calculation error")
    except CalculationError as e:
        assert str(e) == "Test calculation error"
        assert isinstance(e, FinancialAnalysisError)