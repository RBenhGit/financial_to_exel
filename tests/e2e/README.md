# End-to-End (E2E) Tests

This directory contains E2E tests for the Financial Analysis Streamlit application using Playwright.

## Test Structure

- `test_streamlit_app.py` - Basic application functionality tests
- `test_analysis_workflows.py` - Specific analysis workflow tests (FCF, DCF, DDM, P/B)
- `test_performance.py` - Performance and reliability tests
- `conftest.py` - Test configuration and fixtures
- `run_e2e_tests.py` - Test runner script

## Prerequisites

1. Install Playwright and dependencies:
   ```bash
   pip install playwright pytest-playwright
   python -m playwright install
   ```

2. Ensure test data exists in `data/companies/` directory with company folders (MSFT, NVDA, TSLA, etc.)

## Running Tests

### Run All E2E Tests
```bash
# Using the test runner script
python tests/e2e/run_e2e_tests.py

# Using pytest directly
pytest tests/e2e/ -m e2e
```

### Run Specific Test Suites
```bash
# Basic functionality tests
python tests/e2e/run_e2e_tests.py basic

# Analysis workflow tests  
python tests/e2e/run_e2e_tests.py workflows

# Performance tests
python tests/e2e/run_e2e_tests.py performance
```

### Run Individual Test Files
```bash
pytest tests/e2e/test_streamlit_app.py -v
pytest tests/e2e/test_analysis_workflows.py -v
pytest tests/e2e/test_performance.py -v
```

## Test Configuration

- **Browser**: Chromium (headless by default)
- **Base URL**: http://localhost:8501
- **Timeout**: 30 seconds per test
- **Viewport**: 1280x720

## Test Markers

- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.streamlit` - Streamlit-specific tests
- `@pytest.mark.slow` - Long-running tests

## Debugging Tests

To run tests with visible browser (headed mode):
```bash
pytest tests/e2e/ --headed=true
```

To run with specific browser:
```bash
pytest tests/e2e/ --browser=firefox
pytest tests/e2e/ --browser=webkit
```

## Test Coverage

The E2E tests cover:

1. **Application Loading**
   - App startup and initialization
   - Navigation and UI elements
   - Error handling

2. **Analysis Workflows**
   - FCF analysis with Excel data
   - DCF valuation calculations
   - P/B historical analysis
   - DDM analysis (if available)

3. **Data Handling**
   - Ticker selection
   - Data import/export functionality
   - Error recovery mechanisms

4. **Performance**
   - Load times
   - Analysis response times
   - Memory stability
   - Concurrent usage simulation

## Troubleshooting

### Common Issues

1. **Streamlit won't start**: Ensure no other Streamlit process is running on port 8501
2. **Tests timeout**: Check if the application is properly loading data files
3. **Browser not found**: Run `python -m playwright install` to install browser binaries
4. **Test data missing**: Ensure company data exists in `data/companies/` directory

### Debug Mode

For debugging, you can:
1. Set `--headed=true` to see the browser
2. Add `page.pause()` in test code to pause execution
3. Use `--tb=long` for detailed error traces
4. Check Streamlit logs for application errors

## CI/CD Integration

The test runner script (`run_e2e_tests.py`) is designed to work in CI environments:
- Automatically starts/stops Streamlit
- Handles process cleanup
- Returns proper exit codes
- Supports headless execution