# RBH Project Commands

Project-specific commands for the financial analysis codebase.

**Arguments**: $ARGUMENTS

## Available Commands

### Git Workflow
- `/rbh/git-push <message>` - Add, commit, and push changes

### Testing & Quality
- `/rbh/run-tests` - Run test suite
- `/rbh/run-tests-coverage` - Run tests with coverage report
- `/rbh/lint` - Run linting checks
- `/rbh/format` - Format code with black/isort

### Application Launch
- `/rbh/run-app` - Start the Streamlit application
- `/rbh/run-fcf` - Run FCF analysis Streamlit app

### Data & Cache
- `/rbh/clear-cache` - Clear data cache
- `/rbh/refresh-data` - Refresh cached financial data

## Usage Examples

```bash
/rbh/git-push "feat: add new risk analysis module"
/rbh/run-tests
/rbh/run-app
/rbh/clear-cache
```

## Command Details

Use tab completion: `/rbh/` and press Tab to see all commands.

For git workflow help, see: `/rbh/git-push`
