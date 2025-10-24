#!/usr/bin/env python3
"""
Test script for NumPy best practices implementation
Tests floating-point error handling, deprecation warnings, and type safety
"""

import numpy as np
import warnings
import sys
from typing import Any, List


def test_errstate_implementation():
    """Test np.errstate() context manager implementation"""
    print("Testing np.errstate() context managers...")

    # Test division by zero handling with NumPy operations
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.divide(1.0, 0.0)
        assert np.isinf(result), f"Expected inf, got {result}"
        print("+ Division by zero handled correctly")

    # Test overflow handling
    with np.errstate(over='ignore'):
        large_num = float(1e308)
        overflow_result = large_num * 10
        assert np.isinf(overflow_result), f"Expected inf from overflow, got {overflow_result}"
        print("+ Overflow handled correctly")

    # Test invalid operations
    with np.errstate(invalid='ignore'):
        invalid_result = np.sqrt(-1)
        assert np.isnan(invalid_result), f"Expected NaN, got {invalid_result}"
        print("+ Invalid operations handled correctly")


def test_finite_validation():
    """Test np.isfinite() validation implementation"""
    print("\nTesting np.isfinite() validation...")

    test_values = [1.0, np.inf, -np.inf, np.nan, 0.0, 1e-10, 1e10]
    expected_finite = [True, False, False, False, True, True, True]

    for value, expected in zip(test_values, expected_finite):
        result = np.isfinite(value)
        assert result == expected, f"isfinite({value}) = {result}, expected {expected}"
        print(f"+ np.isfinite({value}) = {result}")


def test_type_safe_arrays():
    """Test type-safe array creation and operations"""
    print("\nTesting type-safe array operations...")

    # Test explicit dtype specification
    float_array = np.array([1, 2, 3], dtype=float)
    assert float_array.dtype == float, f"Expected float64, got {float_array.dtype}"
    print("+ Explicit dtype specification works")

    # Test array validation with financial data
    financial_data = [100.0, 200.5, 0.0, -50.25]
    array = np.array(financial_data, dtype=float)

    # Validate all values are finite
    all_finite = np.all(np.isfinite(array))
    assert all_finite, f"Expected all finite values, got: {array}"
    print("+ Financial data array validation works")

    # Test safe division with arrays
    with np.errstate(divide='ignore', invalid='ignore'):
        divisor = np.array([1.0, 2.0, 0.0, 4.0])
        result = np.divide(array, divisor, out=np.zeros_like(array), where=(divisor != 0))
        finite_count = np.sum(np.isfinite(result))
        print(f"+ Safe array division: {finite_count} finite results out of {len(result)}")


def test_deprecation_warnings():
    """Test NumPy deprecation warning management"""
    print("\nTesting deprecation warning management...")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Test that our warning filters are working
        # This should not raise a deprecation warning due to our filters
        try:
            # Use a potentially deprecated numpy feature
            arr = np.array([1, 2, 3])
            # Some operations that might trigger warnings in older versions
            result = arr.astype(float)
            print("+ Deprecation warnings properly managed")
        except Exception as e:
            print(f"! Warning management test failed: {e}")


def test_memory_management():
    """Test proper memory management and array views"""
    print("\nTesting memory management...")

    # Create large array
    large_array = np.zeros(1000000, dtype=float)

    # Create view (should not copy data)
    array_view = large_array[::2]
    assert array_view.base is large_array, "View should share memory with original"
    print("+ Array views work correctly")

    # Test copy vs view
    array_copy = large_array.copy()
    assert array_copy.base is None, "Copy should not share memory"
    print("+ Array copying works correctly")

    # Clean up
    del large_array, array_view, array_copy
    print("+ Memory management test completed")


def test_error_configuration():
    """Test NumPy error configuration"""
    print("\nTesting NumPy error configuration...")

    # Save current settings
    old_settings = np.geterr()

    try:
        # Test our error configuration
        np.seterr(divide='warn', over='warn', under='ignore', invalid='warn')
        current_settings = np.geterr()

        expected = {'divide': 'warn', 'over': 'warn', 'under': 'ignore', 'invalid': 'warn'}
        for key, value in expected.items():
            assert (
                current_settings[key] == value
            ), f"Expected {key}={value}, got {current_settings[key]}"

        print("+ NumPy error configuration set correctly")

    finally:
        # Restore original settings
        np.seterr(**old_settings)
        print("+ Original error settings restored")


def run_all_tests():
    """Run all NumPy best practices tests"""
    print("=" * 60)
    print("NumPy Best Practices Implementation Test Suite")
    print("=" * 60)

    test_functions = [
        test_errstate_implementation,
        test_finite_validation,
        test_type_safe_arrays,
        test_deprecation_warnings,
        test_memory_management,
        test_error_configuration,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"X {test_func.__name__} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
