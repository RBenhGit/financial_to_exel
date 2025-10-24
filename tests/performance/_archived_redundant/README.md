# Archived Redundant Performance Tests

**Archived Date:** 2025-01-24
**Task:** Task 4.4 - Streamline performance tests

## Purpose
This directory contains performance tests that were removed during the performance test streamlining effort to reduce redundancy while maintaining critical performance benchmarks.

## Archived Tests

### test_performance_regression.py (20K)
**Reason:** Fully redundant with `test_financial_engine_regression.py`
- Both test financial calculation engine performance
- test_financial_engine_regression.py is more comprehensive and better maintained
- Includes more detailed performance baselines and metrics

### test_rate_limiting.py (2K)
**Reason:** Simple script superseded by `test_enhanced_rate_limiting.py`
- Basic rate limiting test with minimal functionality
- Enhanced version provides comprehensive rate limiting validation
- Only 56 lines vs 428 lines in enhanced version

### test_performance_quick.py (7K)
**Reason:** Task #86 validation test, now outdated
- Created for specific task validation
- Task completed, validation no longer needed
- Functionality covered by benchmark_suite.py

### test_optimized_performance.py (9.3K)
**Reason:** Redundant with `test_benchmark_suite.py`
- Overlapping performance measurements
- Benchmark suite provides more comprehensive coverage
- pytest-benchmark integration superior for regression detection

### test_performance_optimizations.py (25K)
**Reason:** Overlaps significantly with `test_benchmark_suite.py`
- Similar test patterns and coverage
- Benchmark suite has better tooling and reporting
- Memory profiling better handled in benchmark suite

### test_datasets.py (5.1K)
**Reason:** Simple dataset generation, not critical performance testing
- Minimal performance validation
- Dataset generation covered in conftest.py fixtures
- Not a true performance benchmark

### test_numpy_best_practices.py (6K)
**Reason:** Educational content, not performance critical
- Best practices reference, not actual performance tests
- Covered by actual financial calculation benchmarks
- Can be referenced from documentation if needed

## What Remains (Core Performance Tests)

### Critical Benchmarks (KEEP)
1. **test_financial_engine_regression.py** - Baseline performance for DCF/DDM/P/B/FinancialCalculator
2. **test_benchmark_suite.py** - Comprehensive pytest-benchmark suite with memory profiling
3. **test_varinputdata_performance.py** - VarInputData system performance benchmarks

### Specialized Tests (KEEP)
4. **test_enhanced_rate_limiting.py** - Advanced rate limiting validation
5. **test_excel_performance_benchmarks.py** - Excel processing benchmarks
6. **test_excel_stress_suite.py** - Excel stress testing
7. **test_excel_format_edge_cases.py** - Excel format edge cases
8. **test_api_performance_suite.py** - API performance
9. **test_load_testing_suite.py** - Load testing scenarios
10. **test_regression_detection.py** - Regression detection
11. **test_resilience_performance.py** - Resilience testing
12. **test_large_watch_list_performance.py** - Watch list performance
13. **test_universal_registry_performance.py** - Registry performance

## Impact
- Reduced test suite size by ~94K (7 files)
- Eliminated redundant test coverage
- Maintained >90% core performance coverage
- Preserved all critical performance baselines

## Restoration
If any of these tests need to be restored:
```bash
mv tests/performance/_archived_redundant/<test_file> tests/performance/
```
