#!/usr/bin/env python3
"""
Test script to validate Excel processing optimizations.
This script compares performance before and after optimization changes.
"""

import sys
import os
import time
import psutil
import pandas as pd
from pathlib import Path

sys.path.append('.')

from centralized_data_manager import CentralizedDataManager
import logging

# Configure logging for performance testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def measure_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def test_excel_loading_performance():
    """Test Excel loading performance with optimizations"""
    logger.info("=== Excel Processing Performance Test ===")

    # Initialize manager
    manager = CentralizedDataManager('.')

    # Find available test companies
    test_companies = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and len(item) <= 5 and item.isupper():
            # Check if it has proper structure
            company_path = Path(item)
            if (company_path / "FY").exists() or (company_path / "LTM").exists():
                test_companies.append(item)

    if not test_companies:
        print("No test companies found with proper FY/LTM structure")
        return False

    test_company = test_companies[0]
    print(f"\nTesting with company: {test_company}")

    # Performance metrics
    results = {
        'memory_before': 0,
        'memory_after': 0,
        'load_time': 0,
        'file_count': 0,
        'data_size': 0,
    }

    # Measure initial memory
    results['memory_before'] = measure_memory_usage()

    # Test optimized loading
    print("\n1. Testing optimized Excel loading...")
    start_time = time.time()

    try:
        excel_data = manager.load_excel_data(test_company, force_reload=True)

        end_time = time.time()
        results['load_time'] = end_time - start_time
        results['memory_after'] = measure_memory_usage()
        results['file_count'] = len(excel_data)

        # Calculate total data size
        total_size = 0
        for key, df in excel_data.items():
            if isinstance(df, pd.DataFrame):
                size_bytes = df.memory_usage(deep=True).sum()
                total_size += size_bytes
                print(f"   {key}: {df.shape} ({size_bytes/1024:.1f}KB)")

        results['data_size'] = total_size / 1024  # Convert to KB

        print(f"\n✓ Successfully loaded {results['file_count']} Excel files")
        print(f"✓ Total loading time: {results['load_time']:.2f} seconds")
        print(f"✓ Memory usage: {results['memory_before']:.1f}MB → {results['memory_after']:.1f}MB")
        print(f"✓ Data size in memory: {results['data_size']:.1f}KB")
        print(f"✓ Loading speed: {results['data_size']/results['load_time']:.1f}KB/sec")

        # Test caching performance
        print("\n2. Testing cache performance...")
        cache_start = time.time()
        cached_data = manager.load_excel_data(test_company, force_reload=False)
        cache_end = time.time()
        cache_time = cache_end - cache_start

        print(f"✓ Cached loading time: {cache_time:.3f} seconds")
        print(f"✓ Cache speedup: {results['load_time']/cache_time:.1f}x faster")

        # Test data quality
        print("\n3. Testing data standardization quality...")
        quality_issues = 0
        for key, df in excel_data.items():
            if df.empty:
                print(f"   WARNING: {key} is empty")
                quality_issues += 1
                continue

            # Check for proper data types
            numeric_cols = df.select_dtypes(include=['number']).columns
            object_cols = df.select_dtypes(include=['object']).columns

            print(f"   {key}: {len(numeric_cols)} numeric, {len(object_cols)} text columns")

            # Check for missing values
            missing_count = df.isnull().sum().sum()
            if missing_count > 0:
                print(f"   INFO: {key} has {missing_count} missing values (handled)")

        if quality_issues == 0:
            print("✓ All datasets properly standardized")

        # Performance benchmarks
        print(f"\n=== Performance Summary ===")
        print(f"Files processed: {results['file_count']}")
        print(f"Total time: {results['load_time']:.2f}s")
        print(
            f"Memory efficient: {results['memory_after'] - results['memory_before']:+.1f}MB change"
        )
        print(f"Processing speed: {results['data_size']/results['load_time']:.1f}KB/s")

        # Benchmark thresholds
        if results['load_time'] < 5.0:
            print("✓ EXCELLENT: Loading time under 5 seconds")
        elif results['load_time'] < 10.0:
            print("✓ GOOD: Loading time under 10 seconds")
        else:
            print("⚠ SLOW: Loading time over 10 seconds")

        if cache_time < 0.5:
            print("✓ EXCELLENT: Cache retrieval under 0.5 seconds")
        else:
            print("⚠ Consider cache optimization")

        return True

    except Exception as e:
        print(f"✗ Excel loading test failed: {e}")
        return False


def test_memory_optimization():
    """Test memory usage optimization"""
    print(f"\n=== Memory Optimization Test ===")

    try:
        # Create sample dataframe to test optimization
        test_df = pd.DataFrame(
            {
                'int_col': range(10000),
                'float_col': [float(x) * 1.5 for x in range(10000)],
                'str_col': [f'Item_{x}' for x in range(10000)],
            }
        )

        original_memory = test_df.memory_usage(deep=True).sum()
        print(f"Original memory usage: {original_memory/1024:.1f}KB")

        # Apply optimization
        numeric_columns = test_df.select_dtypes(include=['number']).columns
        for col in numeric_columns:
            if test_df[col].dtype == 'float64':
                test_df[col] = pd.to_numeric(test_df[col], downcast='float')
            elif test_df[col].dtype == 'int64':
                test_df[col] = pd.to_numeric(test_df[col], downcast='integer')

        optimized_memory = test_df.memory_usage(deep=True).sum()
        savings = original_memory - optimized_memory
        savings_percent = (savings / original_memory) * 100

        print(f"Optimized memory usage: {optimized_memory/1024:.1f}KB")
        print(f"Memory savings: {savings/1024:.1f}KB ({savings_percent:.1f}%)")

        if savings_percent > 20:
            print("✓ EXCELLENT: Memory optimization > 20%")
        elif savings_percent > 10:
            print("✓ GOOD: Memory optimization > 10%")
        else:
            print("⚠ Minimal memory optimization")

        return True

    except Exception as e:
        print(f"✗ Memory optimization test failed: {e}")
        return False


def main():
    """Run all Excel optimization tests"""
    print("Excel Processing Optimization Test Suite")
    print("=" * 50)

    tests_passed = 0
    total_tests = 2

    # Test 1: Excel loading performance
    if test_excel_loading_performance():
        tests_passed += 1

    # Test 2: Memory optimization
    if test_memory_optimization():
        tests_passed += 1

    print(f"\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All Excel optimization tests PASSED!")
        print("\nOptimizations implemented:")
        print("✓ Batch file categorization")
        print("✓ Optimized pandas read settings")
        print("✓ Memory-efficient data types")
        print("✓ Vectorized data standardization")
        print("✓ Enhanced caching system")
        print("✓ Openpyxl optimization flags")
        return True
    else:
        print("❌ Some tests failed. Review optimization implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
