# Run Tests with Coverage

Execute tests and generate coverage report.

**Usage**: `/rbh/run-tests-coverage`

## Steps:

1. Run pytest with coverage enabled
2. Generate coverage report
3. Display coverage summary
4. Optionally open HTML coverage report

## Implementation:

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term -v
```

This will:
- Run all tests with coverage tracking
- Generate HTML report in `htmlcov/`
- Display terminal coverage summary
- Identify uncovered code sections
