"""
Test script for unified FCF calculations across all APIs

Tests the new converter system and unified FCF calculation to ensure
consistent results across Alpha Vantage, FMP, yfinance, and Polygon APIs.
"""

import logging
from typing import Dict, Any
from alpha_vantage_converter import AlphaVantageConverter
from fmp_converter import FMPConverter
from yfinance_converter import YfinanceConverter
from polygon_converter import PolygonConverter
from financial_calculations import calculate_unified_fcf

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alpha_vantage_converter():
    """Test Alpha Vantage data conversion and FCF calculation"""
    print("\n=== Testing Alpha Vantage Converter ===")
    
    # Mock Alpha Vantage data structure
    mock_alpha_vantage_data = {
        "operatingCashflow": "50000000",
        "capitalExpenditures": "-20000000",
        "netIncome": "30000000",
        "totalRevenue": "200000000"
    }
    
    # Test conversion
    standardized = AlphaVantageConverter.convert_financial_data(mock_alpha_vantage_data)
    print(f"Alpha Vantage standardized data: {standardized}")
    
    # Test FCF calculation
    fcf_result = calculate_unified_fcf(standardized)
    print(f"Alpha Vantage FCF result: {fcf_result}")
    
    return fcf_result

def test_fmp_converter():
    """Test FMP data conversion and FCF calculation"""
    print("\n=== Testing FMP Converter ===")
    
    # Mock FMP data structure (array format)
    mock_fmp_data = [{
        "operatingCashFlow": 50000000,
        "capitalExpenditure": -20000000,
        "netIncome": 30000000,
        "revenue": 200000000,
        "calendarYear": 2023
    }]
    
    # Test conversion
    standardized = FMPConverter.convert_financial_data(mock_fmp_data)
    print(f"FMP standardized data: {standardized}")
    
    # Test FCF calculation
    fcf_result = calculate_unified_fcf(standardized)
    print(f"FMP FCF result: {fcf_result}")
    
    return fcf_result

def test_yfinance_converter():
    """Test yfinance data conversion and FCF calculation"""
    print("\n=== Testing yfinance Converter ===")
    
    # Mock yfinance data structure (dict format)
    mock_yfinance_data = {
        "Total Cash From Operating Activities": 50000000,
        "Capital Expenditures": -20000000,
        "Net Income": 30000000,
        "Total Revenue": 200000000,
        "marketCap": 1000000000
    }
    
    # Test conversion
    standardized = YfinanceConverter.convert_financial_data(mock_yfinance_data)
    print(f"yfinance standardized data: {standardized}")
    
    # Test FCF calculation
    fcf_result = calculate_unified_fcf(standardized)
    print(f"yfinance FCF result: {fcf_result}")
    
    return fcf_result

def test_polygon_converter():
    """Test Polygon data conversion and FCF calculation"""
    print("\n=== Testing Polygon Converter ===")
    
    # Mock Polygon data structure (nested format)
    mock_polygon_data = {
        "results": [{
            "financials": {
                "cash_flow_statement": {
                    "net_cash_flow_from_operating_activities": {"value": 50000000},
                    "capital_expenditure": {"value": -20000000}
                },
                "income_statement": {
                    "net_income_loss": {"value": 30000000},
                    "revenues": {"value": 200000000}
                }
            },
            "fiscal_year": 2023
        }]
    }
    
    # Test conversion
    standardized = PolygonConverter.convert_financial_data(mock_polygon_data)
    print(f"Polygon standardized data: {standardized}")
    
    # Test FCF calculation
    fcf_result = calculate_unified_fcf(standardized)
    print(f"Polygon FCF result: {fcf_result}")
    
    return fcf_result

def test_fcf_consistency():
    """Test that all APIs produce consistent FCF results for same underlying data"""
    print("\n=== Testing FCF Consistency Across APIs ===")
    
    # Run all tests
    alpha_vantage_result = test_alpha_vantage_converter()
    fmp_result = test_fmp_converter()
    yfinance_result = test_yfinance_converter()
    polygon_result = test_polygon_converter()
    
    # Extract FCF values
    fcf_values = {
        "Alpha Vantage": alpha_vantage_result.get("free_cash_flow") if alpha_vantage_result else None,
        "FMP": fmp_result.get("free_cash_flow") if fmp_result else None,
        "yfinance": yfinance_result.get("free_cash_flow") if yfinance_result else None,
        "Polygon": polygon_result.get("free_cash_flow") if polygon_result else None
    }
    
    print(f"\nFCF Values Comparison:")
    for api, fcf_value in fcf_values.items():
        print(f"  {api}: {fcf_value}")
    
    # Check consistency (allowing for small floating point differences)
    valid_values = [v for v in fcf_values.values() if v is not None]
    if valid_values:
        expected_fcf = 30000000.0  # OCF 50M - CapEx 20M = 30M
        tolerance = 1000.0  # Allow 1K difference for floating point
        
        consistent = all(abs(v - expected_fcf) <= tolerance for v in valid_values)
        print(f"\nConsistency Check: {'PASS' if consistent else 'FAIL'}")
        print(f"Expected FCF: {expected_fcf}")
        print(f"All values within tolerance: {consistent}")
        
        return consistent
    else:
        print("\nNo valid FCF values found - CHECK CONVERTERS!")
        return False

def test_error_handling():
    """Test error handling in converters"""
    print("\n=== Testing Error Handling ===")
    
    # Test with empty data
    empty_results = []
    for converter_name, converter_class in [
        ("Alpha Vantage", AlphaVantageConverter),
        ("FMP", FMPConverter), 
        ("yfinance", YfinanceConverter),
        ("Polygon", PolygonConverter)
    ]:
        try:
            result = converter_class.convert_financial_data({})
            fcf_result = calculate_unified_fcf(result)
            empty_results.append((converter_name, fcf_result))
            print(f"{converter_name} empty data handling: {fcf_result}")
        except Exception as e:
            print(f"{converter_name} error handling: {e}")
            empty_results.append((converter_name, None))
    
    # Test with invalid data
    invalid_data = {"invalid_field": "not_a_number"}
    for converter_name, converter_class in [
        ("Alpha Vantage", AlphaVantageConverter),
        ("FMP", FMPConverter),
        ("yfinance", YfinanceConverter), 
        ("Polygon", PolygonConverter)
    ]:
        try:
            result = converter_class.convert_financial_data(invalid_data)
            fcf_result = calculate_unified_fcf(result)
            print(f"{converter_name} invalid data handling: {fcf_result}")
        except Exception as e:
            print(f"{converter_name} invalid data error: {e}")

if __name__ == "__main__":
    print("Testing Unified FCF Calculation System")
    print("=====================================")
    
    try:
        # Run consistency test
        consistency_passed = test_fcf_consistency()
        
        # Run error handling test
        test_error_handling()
        
        print(f"\n=== SUMMARY ===")
        print(f"Consistency Test: {'PASS' if consistency_passed else 'FAIL'}")
        print(f"Overall Status: {'SUCCESS' if consistency_passed else 'NEEDS INVESTIGATION'}")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nTest execution failed: {e}")