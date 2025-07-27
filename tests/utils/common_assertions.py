"""
Common test assertions and validation utilities.

This module provides reusable assertion functions to eliminate duplicate
validation logic across test files.
"""

import pytest
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union


def assert_fcf_data_structure(fcf_data: Dict[str, List[float]]) -> None:
    """
    Assert that FCF data has the expected structure

    Args:
        fcf_data (Dict[str, List[float]]): FCF data to validate
    """
    assert isinstance(fcf_data, dict), "FCF data must be a dictionary"

    expected_fcf_types = {'FCFF', 'FCFE', 'LFCF'}

    for fcf_type, values in fcf_data.items():
        assert fcf_type in expected_fcf_types, f"Unexpected FCF type: {fcf_type}"
        assert isinstance(values, list), f"FCF values for {fcf_type} must be a list"

        for i, value in enumerate(values):
            assert (
                isinstance(value, (int, float)) or value is None
            ), f"FCF value at index {i} for {fcf_type} must be numeric or None"


def assert_growth_rates_structure(growth_rates: Dict[str, Dict[str, float]]) -> None:
    """
    Assert that growth rates have the expected structure

    Args:
        growth_rates (Dict[str, Dict[str, float]]): Growth rates to validate
    """
    assert isinstance(growth_rates, dict), "Growth rates must be a dictionary"

    expected_period_patterns = {'1yr', '3yr', '5yr', '10yr'}

    for fcf_type, rates in growth_rates.items():
        assert isinstance(rates, dict), f"Growth rates for {fcf_type} must be a dictionary"

        for period, rate in rates.items():
            assert isinstance(period, str), f"Period {period} must be a string"
            assert period.endswith('yr'), f"Period {period} must end with 'yr'"
            assert rate is None or isinstance(
                rate, (int, float)
            ), f"Growth rate for {fcf_type} {period} must be numeric or None"


def assert_financial_dataframe(df: pd.DataFrame, min_rows: int = 1, min_cols: int = 1) -> None:
    """
    Assert that a DataFrame contains valid financial data

    Args:
        df (pd.DataFrame): DataFrame to validate
        min_rows (int): Minimum number of rows expected
        min_cols (int): Minimum number of columns expected
    """
    assert isinstance(df, pd.DataFrame), "Must be a pandas DataFrame"
    assert not df.empty, "DataFrame cannot be empty"
    assert len(df) >= min_rows, f"DataFrame must have at least {min_rows} rows"
    assert len(df.columns) >= min_cols, f"DataFrame must have at least {min_cols} columns"


def assert_numerical_values_valid(
    values: List[Union[float, int]],
    allow_negative: bool = True,
    allow_zero: bool = True,
    allow_none: bool = True,
) -> None:
    """
    Assert that a list of numerical values is valid

    Args:
        values (List[Union[float, int]]): Values to validate
        allow_negative (bool): Whether negative values are allowed
        allow_zero (bool): Whether zero values are allowed
        allow_none (bool): Whether None values are allowed
    """
    assert isinstance(values, list), "Values must be a list"

    for i, value in enumerate(values):
        if value is None:
            assert allow_none, f"None value at index {i} is not allowed"
            continue

        assert isinstance(
            value, (int, float)
        ), f"Value at index {i} must be numeric, got {type(value)}"

        # Check for invalid float values
        if isinstance(value, float):
            assert not np.isnan(value), f"NaN value at index {i} is not allowed"
            assert not np.isinf(value), f"Infinite value at index {i} is not allowed"

        if not allow_negative:
            assert value >= 0, f"Negative value {value} at index {i} is not allowed"

        if not allow_zero:
            assert value != 0, f"Zero value at index {i} is not allowed"


def assert_market_data_fields(
    market_data: Dict[str, Any], required_fields: Optional[List[str]] = None
) -> None:
    """
    Assert that market data contains required fields

    Args:
        market_data (Dict[str, Any]): Market data to validate
        required_fields (Optional[List[str]]): List of required field names
    """
    if required_fields is None:
        required_fields = [
            'symbol',
            'currentPrice',
            'marketCap',
            'sharesOutstanding',
            'enterpriseValue',
            'totalDebt',
            'totalCash',
        ]

    assert isinstance(market_data, dict), "Market data must be a dictionary"

    for field in required_fields:
        assert field in market_data, f"Required field '{field}' is missing"

        value = market_data[field]
        if field in [
            'currentPrice',
            'marketCap',
            'sharesOutstanding',
            'enterpriseValue',
            'totalDebt',
            'totalCash',
        ]:
            if value is not None:
                assert isinstance(
                    value, (int, float)
                ), f"Field '{field}' must be numeric, got {type(value)}"
                assert value >= 0, f"Field '{field}' must be non-negative"


def assert_date_sequence_valid(dates: List[Any]) -> None:
    """
    Assert that a sequence of dates is valid and chronological

    Args:
        dates (List[Any]): List of dates to validate
    """
    assert isinstance(dates, list), "Dates must be a list"
    assert len(dates) > 0, "Date list cannot be empty"

    # Convert to comparable format if needed
    comparable_dates = []
    for date in dates:
        if isinstance(date, str):
            # Try to extract year from string format like "12/31/2023"
            try:
                if '/' in date:
                    year = int(date.split('/')[-1])
                elif '-' in date:
                    year = int(date.split('-')[0])
                else:
                    year = int(date)
                comparable_dates.append(year)
            except ValueError:
                pytest.fail(f"Cannot parse date: {date}")
        elif isinstance(date, (int, float)):
            comparable_dates.append(int(date))
        else:
            pytest.fail(f"Unsupported date format: {type(date)}")

    # Check chronological order
    for i in range(1, len(comparable_dates)):
        assert (
            comparable_dates[i] >= comparable_dates[i - 1]
        ), f"Dates are not in chronological order: {comparable_dates[i-1]} > {comparable_dates[i]}"


def assert_percentage_in_range(
    percentage: float, min_val: float = -1.0, max_val: float = 10.0
) -> None:
    """
    Assert that a percentage value is within a reasonable range

    Args:
        percentage (float): Percentage value to validate (as decimal, e.g., 0.1 for 10%)
        min_val (float): Minimum allowed value
        max_val (float): Maximum allowed value
    """
    assert isinstance(percentage, (int, float)), "Percentage must be numeric"
    assert not np.isnan(percentage), "Percentage cannot be NaN"
    assert not np.isinf(percentage), "Percentage cannot be infinite"
    assert (
        min_val <= percentage <= max_val
    ), f"Percentage {percentage:.2%} is outside reasonable range [{min_val:.2%}, {max_val:.2%}]"


def assert_excel_data_integrity(df: pd.DataFrame, company_name: Optional[str] = None) -> None:
    """
    Assert that Excel data has proper integrity for financial analysis

    Args:
        df (pd.DataFrame): Excel data DataFrame
        company_name (Optional[str]): Expected company name
    """
    assert_financial_dataframe(df, min_rows=5, min_cols=4)  # Minimum viable structure

    # Check for company name in first few rows if provided
    if company_name:
        found_company = False
        for i in range(min(3, len(df))):  # Check first 3 rows
            for col in df.columns[:3]:  # Check first 3 columns
                cell_value = df.iloc[i, col] if col < len(df.columns) else None
                if cell_value and isinstance(cell_value, str):
                    if company_name.lower() in cell_value.lower():
                        found_company = True
                        break
            if found_company:
                break

        assert found_company, f"Company name '{company_name}' not found in Excel data"


def assert_dcf_results_valid(dcf_results: Dict[str, Any]) -> None:
    """
    Assert that DCF calculation results are valid

    Args:
        dcf_results (Dict[str, Any]): DCF results to validate
    """
    assert isinstance(dcf_results, dict), "DCF results must be a dictionary"

    # Check for expected fields
    expected_fields = ['enterprise_value', 'equity_value', 'fair_value_per_share']
    for field in expected_fields:
        if field in dcf_results:
            value = dcf_results[field]
            if value is not None:
                assert isinstance(value, (int, float)), f"DCF field '{field}' must be numeric"
                assert value >= 0, f"DCF field '{field}' must be non-negative"


def assert_no_duplicate_processing(results1: Any, results2: Any, tolerance: float = 1e-10) -> None:
    """
    Assert that two processing results are identical (for testing caching/deduplication)

    Args:
        results1 (Any): First result set
        results2 (Any): Second result set
        tolerance (float): Tolerance for floating point comparisons
    """
    assert type(results1) == type(results2), "Result types must be identical"

    if isinstance(results1, dict) and isinstance(results2, dict):
        assert set(results1.keys()) == set(results2.keys()), "Dictionary keys must be identical"

        for key in results1.keys():
            assert_no_duplicate_processing(results1[key], results2[key], tolerance)

    elif isinstance(results1, list) and isinstance(results2, list):
        assert len(results1) == len(results2), "List lengths must be identical"

        for i, (item1, item2) in enumerate(zip(results1, results2)):
            assert_no_duplicate_processing(item1, item2, tolerance)

    elif isinstance(results1, (int, float)) and isinstance(results2, (int, float)):
        if isinstance(results1, float) or isinstance(results2, float):
            assert (
                abs(results1 - results2) <= tolerance
            ), f"Floating point values differ by more than tolerance: {results1} vs {results2}"
        else:
            assert (
                results1 == results2
            ), f"Integer values must be exactly equal: {results1} vs {results2}"

    else:
        assert results1 == results2, f"Values must be identical: {results1} vs {results2}"


def assert_test_performance(func, max_execution_time: float = 5.0):
    """
    Assert that a function executes within a reasonable time limit

    Args:
        func: Function to test
        max_execution_time (float): Maximum allowed execution time in seconds
    """
    import time

    start_time = time.time()
    result = func()
    execution_time = time.time() - start_time

    assert (
        execution_time <= max_execution_time
    ), f"Function took {execution_time:.2f}s, which exceeds limit of {max_execution_time}s"

    return result
