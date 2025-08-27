@echo off
REM E2E Test Runner for Financial Analysis Application
REM Usage: run_e2e_tests.bat [test_suite]
REM   test_suite: basic, workflows, performance (optional)

setlocal enabledelayedexpansion

echo Starting E2E Tests for Financial Analysis Application
echo =====================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Check if Playwright is installed
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo Installing Playwright...
    pip install playwright pytest-playwright
    python -m playwright install
)

REM Run tests based on argument
if "%1"=="" (
    echo Running all E2E tests...
    python tests\e2e\run_e2e_tests.py
) else (
    echo Running %1 test suite...
    python tests\e2e\run_e2e_tests.py %1
)

if errorlevel 1 (
    echo.
    echo E2E Tests FAILED
    echo Check the output above for details
    exit /b 1
) else (
    echo.
    echo E2E Tests PASSED
    echo All tests completed successfully
)

endlocal