# Run Linting Checks

Run code quality and style checks.

**Usage**: `/rbh/lint [path]`

## Steps:

1. Run flake8 for style checking
2. Check for common Python issues
3. Report violations with file locations
4. Suggest fixes where applicable

## Implementation:

```bash
# Run flake8 on entire codebase
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Run flake8 with full checks
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
```

Optional path from $ARGUMENTS will be used instead of `.`

## Alternative Tools:

- `pylint` for deeper analysis
- `mypy` for type checking
- `black --check` for formatting validation
