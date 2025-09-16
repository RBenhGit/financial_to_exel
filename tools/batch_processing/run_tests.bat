@echo off
REM Comprehensive Test Runner for Financial Analysis Application
REM Usage: run_tests.bat [test_suite] [options]

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo 🧪 Financial Analysis Test Runner
echo ====================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and ensure it's in your PATH
    exit /b 1
)

REM Check if pytest is available
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pytest not found. Installing...
    pip install pytest pytest-timeout
    if errorlevel 1 (
        echo ❌ Failed to install pytest
        exit /b 1
    )
)

REM Parse command line arguments
set TEST_SUITE=%1
if "%TEST_SUITE%"=="" set TEST_SUITE=quick

REM Map test suite names to descriptions
set SUITE_DESC=Quick Test Suite
if "%TEST_SUITE%"=="basic" set SUITE_DESC=Basic Smoke Tests
if "%TEST_SUITE%"=="unit" set SUITE_DESC=Unit Tests
if "%TEST_SUITE%"=="integration" set SUITE_DESC=Integration Tests
if "%TEST_SUITE%"=="performance" set SUITE_DESC=Performance Tests
if "%TEST_SUITE%"=="e2e" set SUITE_DESC=End-to-End Tests
if "%TEST_SUITE%"=="regression" set SUITE_DESC=Regression Tests
if "%TEST_SUITE%"=="comprehensive" set SUITE_DESC=Comprehensive Test Suite
if "%TEST_SUITE%"=="coverage" set SUITE_DESC=Tests with Coverage

echo Running: !SUITE_DESC!
echo.

REM Execute the Python test runner
python tools\scripts\run_tests.py %*

set EXIT_CODE=!ERRORLEVEL!

echo.
if !EXIT_CODE! equ 0 (
    echo ✅ Test execution completed successfully!
    echo.
    echo 📋 Available test suites:
    echo   basic        - Basic smoke tests
    echo   unit         - Unit tests only
    echo   integration  - Integration tests
    echo   performance  - Performance tests
    echo   e2e          - End-to-end browser tests
    echo   regression   - Regression tests
    echo   quick        - Quick test suite (default)
    echo   comprehensive - Full test suite
    echo   coverage     - Tests with coverage reporting
    echo.
    echo 🔧 Additional options:
    echo   --headed     - Run E2E tests with visible browser
    echo   --fail-fast  - Stop on first failure
    echo   --timeout N  - Set timeout to N seconds
    echo.
    echo Examples:
    echo   run_tests.bat unit --fail-fast
    echo   run_tests.bat e2e --headed
    echo   run_tests.bat comprehensive --include-slow
) else (
    echo ❌ Test execution failed!
    echo.
    echo 🔍 Troubleshooting tips:
    echo   1. Check if all dependencies are installed: pip install -r requirements.txt
    echo   2. For E2E tests, ensure Playwright is installed: pip install playwright
    echo   3. Run with --fail-fast to stop at first failure for easier debugging
    echo   4. Check individual test categories: run_tests.bat basic
    echo.
    echo 📝 For detailed logs, run: python run_tests.py %TEST_SUITE% 2^>^&1 ^| tee test_output.log
)

endlocal
exit /b !EXIT_CODE!