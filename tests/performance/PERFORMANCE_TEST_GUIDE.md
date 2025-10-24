# Performance Test Suite Guide

**Last Updated:** 2025-01-24
**Maintainer:** Development Team

## Overview
This directory contains streamlined performance benchmarks for the financial analysis system. Tests have been optimized to eliminate redundancy while maintaining comprehensive performance coverage.

## Core Performance Benchmarks

### 1. Financial Engine Regression Tests
**File:** `test_financial_engine_regression.py` (28K)
**Purpose:** Baseline performance tests for critical financial calculation engines
**Coverage:**
- FinancialCalculator core operations and FCF calculations
- DCF valuation engine with multi-stage projections
- DDM valuation engine with dividend analysis
- P/B valuation engine with historical analysis
- Memory usage and resource management

**Performance Baselines:**
- FinancialCalculator FCF calculation: < 0.001s per iteration
- DCF valuation: < 0.1s for 5-year projection
- DDM valuation: < 0.05s for dividend analysis
- P/B historical analysis: < 0.2s for 10-year history

**Run:** `pytest tests/performance/test_financial_engine_regression.py -v`

### 2. Comprehensive Benchmark Suite
**File:** `test_benchmark_suite.py` (37K)
**Purpose:** pytest-benchmark integrated comprehensive performance suite
**Coverage:**
- Financial calculator initialization and data loading
- FCF calculation benchmarks
- Multiple FCF types (FCFE, FCFF, LFCF)
- Financial metrics calculation
- DCF and Monte Carlo valuation
- P/B analysis and historical P/B
- Data validation performance
- Large dataset processing
- Concurrent calculations
- Thread safety verification
- Memory usage profiling
- Memory leak detection

**Features:**
- Automated regression detection with `--benchmark-save/--benchmark-compare`
- Memory profiling integration
- Parametrized tests for different data sizes (small/medium/large)
- Concurrent and thread safety testing

**Run:**
```bash
# Basic benchmarks
pytest tests/performance/test_benchmark_suite.py --benchmark-only

# Save baseline
pytest tests/performance/test_benchmark_suite.py --benchmark-only --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/test_benchmark_suite.py --benchmark-only --benchmark-compare=baseline

# With memory profiling
pytest tests/performance/test_benchmark_suite.py --benchmark-only --memprof
```

### 3. VarInputData Performance Benchmarks
**File:** `test_varinputdata_performance.py` (29K)
**Purpose:** Comprehensive VarInputData system performance analysis
**Coverage:**
- Basic get/set operations performance
- Concurrent access and thread safety
- Memory optimization effectiveness
- Lazy loading performance
- Historical data management
- Cache hit/miss ratios
- Eviction strategy performance

**Metrics:**
- Operations per second
- Memory delta and peak usage
- Cache hit rates
- GC runs and memory evictions
- Response time (average and P95)
- Thread safety overhead

**Run:**
```bash
python tests/performance/test_varinputdata_performance.py
# or
pytest tests/performance/test_varinputdata_performance.py -v
```

## Specialized Performance Tests

### 4. Rate Limiting Performance
**File:** `test_enhanced_rate_limiting.py` (17K)
**Purpose:** Advanced rate limiting validation for API calls
**Coverage:**
- Yahoo Finance rate limiting
- Fallback mechanisms
- API quota management
- Request throttling

### 5. Excel Processing Performance
**Files:**
- `test_excel_performance_benchmarks.py` (29K) - Excel data processing benchmarks
- `test_excel_stress_suite.py` (33K) - Stress testing for large Excel files
- `test_excel_format_edge_cases.py` (36K) - Edge cases and format variations

**Purpose:** Validate Excel processing performance and robustness
**Coverage:**
- Large file handling (10MB+)
- Multiple sheet processing
- Format detection and parsing
- Data extraction speed

### 6. Load and Stress Testing
**File:** `test_load_testing_suite.py` (28K)
**Purpose:** System performance under load
**Coverage:**
- Concurrent user simulation
- High-volume data processing
- System resource limits
- Performance degradation patterns

### 7. API Performance
**File:** `test_api_performance_suite.py` (27K)
**Purpose:** API adapter performance benchmarks
**Coverage:**
- Data source adapter response times
- Batch processing performance
- Error handling overhead

### 8. Regression Detection
**File:** `test_regression_detection.py` (26K)
**Purpose:** Automated performance regression detection
**Coverage:**
- Historical baseline comparison
- Performance metric tracking
- Degradation alerts

### 9. Resilience Performance
**File:** `test_resilience_performance.py` (20K)
**Purpose:** System resilience under adverse conditions
**Coverage:**
- Error recovery performance
- Fallback mechanism speed
- System stability under failures

### 10. Watch List Performance
**File:** `test_large_watch_list_performance.py` (23K)
**Purpose:** Large watch list handling
**Coverage:**
- 100+ stock watch lists
- Concurrent analysis
- Memory management for large datasets

### 11. Registry Performance
**File:** `test_universal_registry_performance.py` (15K)
**Purpose:** Universal registry performance
**Coverage:**
- Registration and lookup speed
- Concurrent registry access
- Memory footprint

## Test Fixtures

**File:** `conftest.py` (7.3K)
**Purpose:** Shared fixtures and test data generation
**Provides:**
- `mock_external_api` - Mock external API calls
- `performance_monitor` - System performance monitoring
- `sample_performance_data` - Optimized test data
- `temp_test_data` - Temporary directory structures
- Timeout fixtures (fast/medium/slow)
- Mock yfinance, requests, and Excel data

## Running Performance Tests

### Run All Performance Tests
```bash
pytest tests/performance/ -v
```

### Run Specific Test File
```bash
pytest tests/performance/test_financial_engine_regression.py -v
```

### Run Only Benchmarks
```bash
pytest tests/performance/ --benchmark-only
```

### Run with Coverage
```bash
pytest tests/performance/ --cov=core --cov-report=term
```

### Generate Performance Report
```bash
pytest tests/performance/test_benchmark_suite.py --benchmark-only --benchmark-sort=mean --benchmark-columns=min,max,mean,stddev,median,ops,rounds
```

## Performance Baselines and Thresholds

### Memory Thresholds
- Calculator initialization: < 20MB growth
- FCF calculations (1000 iterations): < 5MB growth
- Large dataset processing: < 50MB growth
- Memory leak tolerance: < 10MB per 100 operations

### Speed Thresholds
- FCF calculation: < 1ms per operation
- DCF valuation: < 100ms for 5-year projection
- Data validation: < 5s for 20 years of data
- Concurrent operations: > 90% success rate

### Cache Performance
- Minimum hit rate: 50%
- Optimal hit rate: > 80%
- Maximum evictions: < 10% of operations

## Archived Tests

Redundant tests removed during streamlining (2025-01-24):
- `test_performance_regression.py` - Redundant with test_financial_engine_regression.py
- `test_rate_limiting.py` - Superseded by test_enhanced_rate_limiting.py
- `test_performance_quick.py` - Task validation test, outdated
- `test_optimized_performance.py` - Redundant with benchmark_suite.py
- `test_performance_optimizations.py` - Overlaps with benchmark_suite.py
- `test_datasets.py` - Dataset generation, not performance critical
- `test_numpy_best_practices.py` - Educational, not benchmarking

See `_archived_redundant/README.md` for details.

## Best Practices

1. **Baseline Establishment**: Always run benchmarks before optimization to establish baseline
2. **Regression Detection**: Use `--benchmark-save` and `--benchmark-compare` for tracking
3. **Isolation**: Clear caches and run GC before critical benchmarks
4. **Repeatability**: Run benchmarks multiple times to account for variance
5. **Resource Monitoring**: Monitor memory, CPU, and I/O during tests
6. **Documentation**: Update baselines when intentional changes are made

## Maintenance

### Adding New Performance Tests
1. Use existing fixtures from `conftest.py`
2. Follow naming convention: `test_<component>_<aspect>_performance.py`
3. Include docstrings with performance baselines
4. Add memory monitoring for resource-intensive tests
5. Update this guide with new test coverage

### Updating Baselines
When intentional performance improvements are made:
1. Run comprehensive benchmark suite
2. Save new baseline: `--benchmark-save=v<version>`
3. Document changes in git commit
4. Update this guide with new thresholds

## Troubleshooting

### Test Timeouts
- Check timeout fixtures: `fast_timeout`, `medium_timeout`, `slow_timeout`
- Adjust pytest timeout with `--timeout=<seconds>`

### Memory Issues
- Ensure proper cleanup with `gc.collect()`
- Use context managers for resource management
- Monitor with `performance_monitor` fixture

### Inconsistent Results
- Run multiple iterations
- Check for background processes
- Use `pytest-benchmark` repeat parameter
- Consider system load and resource availability

## Contact
For questions or issues with performance tests, contact the development team or create an issue in the project repository.
