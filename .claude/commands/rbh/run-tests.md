# Run Test Suite

Execute the project's test suite.

**Usage**: `/rbh/run-tests [filter]`

## Steps:

1. Navigate to project root if needed
2. Run pytest with appropriate flags
3. Display test results summary
4. Report any failures with details

## Examples:

```bash
/rbh/run-tests                    # Run all tests
/rbh/run-tests tests/unit         # Run unit tests only
/rbh/run-tests -k test_dcf        # Run tests matching pattern
```

## Implementation:

```bash
pytest tests/ -v --tb=short
```

Optional filters from $ARGUMENTS will be appended to the pytest command.
