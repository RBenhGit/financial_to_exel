# Testing Standards & Best Practices

## Test Organization Structure

### Directory Layout
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
├── integration/             # Integration tests (slower, real dependencies)
├── api/                     # API-dependent tests
├── fixtures/                # Reusable test data and helpers
└── utils/                   # Common test utilities
```

### File Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestFinancialCalculations`)
- Test methods: `test_*` (e.g., `test_calculate_fcf_growth_rates`)

## AAA Pattern Implementation

All tests must follow the **Arrange-Act-Assert** pattern:

```python
def test_fcf_growth_calculation(self, sample_fcf_data):
    """Test FCF growth rate calculations"""
    # ARRANGE: Set up test data and dependencies
    calculator = FCFCalculator()
    expected_types = ['FCFF', 'FCFE', 'LFCF', 'Average']
    
    # ACT: Execute the functionality under test
    growth_rates = calculator.calculate_fcf_growth_rates(sample_fcf_data)
    
    # ASSERT: Verify the results
    for fcf_type in expected_types:
        if fcf_type in growth_rates:
            assert isinstance(growth_rates[fcf_type], dict)
            assert all(period in growth_rates[fcf_type] for period in ['1yr', '3yr', '5yr'])
```

## Test Categories & Markers

### Required Markers
```python
@pytest.mark.unit           # Fast, isolated tests
@pytest.mark.integration    # Tests with real dependencies
@pytest.mark.slow          # Tests taking >5 seconds
@pytest.mark.api_dependent  # Tests requiring API access
@pytest.mark.excel_dependent # Tests requiring Excel files
```

### Running Tests by Category
```bash
# Run only unit tests
pytest -m "unit"

# Skip slow tests
pytest -m "not slow"

# Skip API-dependent tests (for offline work)
pytest -m "not api_dependent"
```

## Fixture Standards

### Use Centralized Fixtures
All common test data should use fixtures from `tests/fixtures/`:

```python
def test_financial_calculation(self, sample_fcf_data, mock_config):
    """Use centralized fixtures instead of inline test data"""
    calculator = FCFCalculator(config=mock_config)
    result = calculator.calculate_fcf_growth_rates(sample_fcf_data)
    assert result is not None
```

### Fixture Scope Guidelines
- `session`: Expensive setup (database connections, large datasets)
- `module`: Shared across all tests in a file
- `function`: Default, isolated per test

## Error Handling Test Standards

### Test All Error Scenarios
```python
def test_empty_data_handling(self):
    """Test handling of empty data inputs"""
    calculator = FCFCalculator()
    
    # Test with empty data
    empty_data = {}
    result = calculator.calculate_fcf_growth_rates(empty_data)
    
    # Should handle gracefully, not crash
    assert isinstance(result, dict)

def test_malformed_data_handling(self):
    """Test handling of malformed data"""
    calculator = FCFCalculator()
    
    # Test with malformed data
    bad_data = {'FCFF': [None, 'invalid', float('inf')]}
    
    # Should either handle gracefully or raise specific exception
    try:
        result = calculator.calculate_fcf_growth_rates(bad_data)
        assert isinstance(result, dict)
    except Exception as e:
        assert isinstance(e, (ValueError, TypeError))
```

## Parameterized Test Standards

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize(
    "values,periods,expected_length",
    [
        ([100, 110, 121], [1, 2], 2),
        ([50, 75, 100, 125], [1, 2, 3], 3),
        ([200], [1], 0),  # Insufficient data
    ],
)
def test_growth_rate_periods(self, values, periods, expected_length):
    """Test growth rate calculations for different periods"""
    calculator = FCFCalculator()
    growth_rates = calculator._calculate_growth_rates_for_values(values, periods)
    
    assert len(growth_rates) == len(periods)
    non_none_values = [rate for rate in growth_rates.values() if rate is not None]
    assert len(non_none_values) <= expected_length
```

## Mock Usage Standards

### Use Specific Mock Types
```python
from unittest.mock import Mock, patch, MagicMock

# For simple objects
mock_obj = Mock(spec=ExpectedClass)

# For complex behavior
mock_obj = MagicMock()
mock_obj.method.return_value = expected_value

# For patching
@patch('module.function_name')
def test_with_mock(self, mock_function):
    mock_function.return_value = test_value
    # ... test implementation
```

## Performance Test Standards

### Mark Performance Tests
```python
@pytest.mark.slow
@pytest.mark.performance
def test_large_dataset_performance(self):
    """Test performance with large datasets"""
    start_time = time.time()
    
    # Generate large test dataset
    large_data = MockDataGenerator.generate_large_dataset(size=10000)
    
    # Execute operation
    result = processor.process_large_data(large_data)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Performance assertions
    assert execution_time < 30  # Should complete within 30 seconds
    assert result is not None
```

## Test Data Standards

### Use Realistic Test Data
```python
# Good: Realistic financial data
sample_fcf_data = {
    'FCFF': [1000000, 1100000, 1210000],  # In actual currency units
    'FCFE': [950000, 1045000, 1149500],
}

# Avoid: Unrealistic or toy data
bad_sample = {'FCFF': [1, 2, 3]}  # Too simple, not realistic
```

### Test Edge Cases
```python
def test_edge_cases(self):
    """Test edge cases and boundary conditions"""
    calculator = FCFCalculator()
    
    # Test with zero values
    zero_data = {'FCFF': [0, 100, 200]}
    result = calculator.calculate_fcf_growth_rates(zero_data)
    assert result is not None
    
    # Test with negative values
    negative_data = {'FCFF': [-100, 50, 200]}
    result = calculator.calculate_fcf_growth_rates(negative_data)
    assert result is not None
    
    # Test with infinite values
    inf_data = {'FCFF': [float('inf'), 100, 200]}
    result = calculator.calculate_fcf_growth_rates(inf_data)
    assert result is not None
```

## Code Coverage Standards

### Target Coverage Levels
- **Unit tests**: 90%+ line coverage
- **Integration tests**: 80%+ line coverage
- **Critical business logic**: 95%+ line coverage

### Running Coverage
```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

## Test Execution Standards

### Local Development
```bash
# Quick test run (unit tests only)
pytest -m "unit and not slow"

# Full test run (skip API tests)
pytest -m "not api_dependent"

# Performance tests
pytest -m "slow"
```

### CI/CD Pipeline
```bash
# Complete test suite with coverage
pytest --cov=. --cov-report=xml --cov-fail-under=80 -m "not api_dependent"
```

## Quality Gates

### Pre-commit Requirements
All code must pass:
1. **Linting**: `ruff check .`
2. **Type checking**: `mypy .`
3. **Unit tests**: `pytest -m "unit"`
4. **Integration tests**: `pytest -m "integration and not api_dependent"`

### Release Requirements
All code must pass:
1. **Full test suite**: `pytest -m "not api_dependent"`
2. **Code coverage**: 80%+ overall
3. **Performance tests**: All within acceptable limits
4. **Type safety**: Zero mypy errors

## Common Anti-Patterns to Avoid

### ❌ Bad Test Practices
```python
# Don't test implementation details
def test_internal_method_called(self):
    with patch.object(calculator, '_internal_method') as mock:
        calculator.public_method()
        mock.assert_called_once()  # Testing implementation, not behavior

# Don't have overly complex test logic
def test_complex_scenario(self):
    for i in range(100):
        if i % 2 == 0:
            # Complex logic in test
            pass

# Don't ignore specific exception types
def test_error_handling(self):
    try:
        risky_operation()
    except:  # Too broad
        pass
```

### ✅ Good Test Practices
```python
# Test behavior, not implementation
def test_growth_rate_calculation_accuracy(self):
    """Test that growth rates are calculated correctly"""
    calculator = FCFCalculator()
    known_data = {'FCFF': [100, 110, 121]}  # 10% annual growth
    
    growth_rates = calculator.calculate_fcf_growth_rates(known_data)
    
    # Test the actual business logic result
    assert abs(growth_rates['FCFF']['1yr'] - 0.1) < 0.001

# Keep tests simple and focused
def test_single_responsibility(self):
    """Each test should test one specific behavior"""
    calculator = FCFCalculator()
    result = calculator.calculate_specific_metric(test_data)
    assert result.is_valid

# Be specific about expected exceptions
def test_invalid_input_raises_value_error(self):
    """Test that invalid input raises specific exception"""
    calculator = FCFCalculator()
    
    with pytest.raises(ValueError, match="Input data cannot be empty"):
        calculator.calculate_fcf_growth_rates({})
```

## Test Maintenance

### Regular Reviews
- Review test suite monthly for obsolete tests
- Update fixtures when data structures change
- Refactor tests that become too complex
- Archive deprecated test files

### Performance Monitoring
- Track test execution times
- Identify and optimize slow tests
- Use appropriate test markers
- Consider test parallelization for large suites

---

*This document should be reviewed and updated as testing practices evolve.*