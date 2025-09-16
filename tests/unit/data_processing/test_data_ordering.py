#!/usr/bin/env python3
"""
Test data ordering functionality
"""
import sys
import os
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.processors.data_processing import DataProcessor


def find_test_company_data():
    """Find available company data for testing."""
    data_dir = PROJECT_ROOT / "data" / "companies"
    if not data_dir.exists():
        return None

    companies = []
    for item in data_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
            fy_path = item / 'FY'
            if fy_path.exists():
                companies.append(str(item))

    return sorted(companies)[0] if companies else None


@pytest.mark.integration
@pytest.mark.excel_dependent
def test_data_chronological_ordering():
    """Test that financial data is processed in correct chronological order."""
    company_folder = find_test_company_data()

    if not company_folder:
        pytest.skip("No company data found for testing")

    # Initialize calculator
    calc = FinancialCalculator(company_folder)

    # Get FCF calculations
    fcf_results = calc.calculate_all_fcf_types()

    assert fcf_results, "FCF calculations should return results"

    # Test data processor
    processor = DataProcessor()
    processed_data = processor.prepare_fcf_data(fcf_results)

    assert processed_data, "Data processor should return processed data"

    # Check if LFCF data is in correct chronological order
    all_fcf_data = processed_data.get('all_fcf_data', {})
    assert 'LFCF' in all_fcf_data, "LFCF data should be present in processed results"

    lfcf_data = all_fcf_data['LFCF']
    years = lfcf_data.get('years', [])
    values = lfcf_data.get('values', [])

    assert years, "Years data should not be empty"
    assert values, "Values data should not be empty"
    assert len(years) == len(values), "Years and values should have same length"

    # Test that years are in ascending chronological order
    if len(years) > 1:
        years_sorted = sorted(years)
        assert years == years_sorted, f"Years should be in chronological order. Expected: {years_sorted}, Got: {years}"


@pytest.mark.unit
def test_data_processor_empty_input():
    """Test data processor handles empty input gracefully."""
    processor = DataProcessor()

    # Test with empty dict
    result = processor.prepare_fcf_data({})
    assert result is not None

    # Test with None
    result = processor.prepare_fcf_data(None)
    assert result is not None


@pytest.mark.unit
def test_data_processor_invalid_input():
    """Test data processor handles invalid input gracefully."""
    processor = DataProcessor()

    # Test with invalid data types
    invalid_inputs = ["string", 123, [], True]

    for invalid_input in invalid_inputs:
        result = processor.prepare_fcf_data(invalid_input)
        # Should not raise exception and should return something
        assert result is not None
