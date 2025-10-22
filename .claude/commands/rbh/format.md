# Format Code

Auto-format Python code with black and isort.

**Usage**: `/rbh/format [path]`

## Steps:

1. Run black for code formatting
2. Run isort for import sorting
3. Display formatted files
4. Report any issues

## Implementation:

```bash
# Format with black
black .

# Sort imports with isort
isort .
```

Optional path from $ARGUMENTS will be used instead of `.`

## What It Does:

- Applies consistent code formatting (PEP 8)
- Sorts and organizes imports
- Removes trailing whitespace
- Standardizes quote usage
- Fixes line length issues

## Options:

```bash
# Check only (don't modify)
black --check .
isort --check-only .

# Format specific file
black path/to/file.py
```
