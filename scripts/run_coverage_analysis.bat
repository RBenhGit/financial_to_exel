@echo off
REM Automated Coverage Analysis Script for Windows
REM This script runs tests with coverage and generates analysis reports

echo Starting comprehensive coverage analysis...
echo.

REM Activate virtual environment
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please ensure venv exists.
    pause
    exit /b 1
)

REM Clear previous coverage data
echo Cleaning previous coverage data...
if exist coverage.json del coverage.json
if exist htmlcov rmdir /s /q htmlcov

REM Run basic tests with coverage (quick baseline)
echo Running basic tests with coverage for baseline...
pytest tests/test_basic.py --cov=core --cov=config --cov=utils --cov-report=html --cov-report=term-missing --cov-report=json || goto :error

REM Run unit tests with coverage (more comprehensive, but excluding problematic tests)
echo.
echo Running unit tests with coverage...
echo This may take several minutes...
pytest tests/unit/ -x --cov=core --cov=config --cov=utils --cov-report=html --cov-report=term-missing --cov-report=json --cov-append --timeout=60 || echo "Some unit tests failed, continuing with analysis..."

REM Generate coverage analysis report
echo.
echo Generating coverage analysis report...
python tools/coverage_analysis.py || goto :error

REM Open coverage reports
echo.
echo Coverage analysis complete!
echo.
echo Reports generated:
echo   - HTML Report: htmlcov/index.html
echo   - Analysis Report: reports/coverage_analysis_report.md
echo   - JSON Data: coverage.json
echo.

REM Ask if user wants to open reports
set /p choice="Open HTML coverage report in browser? (y/n): "
if /i "%choice%"=="y" start htmlcov/index.html

set /p choice="Open analysis report in notepad? (y/n): "
if /i "%choice%"=="y" start notepad reports/coverage_analysis_report.md

echo.
echo Coverage analysis workflow completed successfully!
pause
exit /b 0

:error
echo.
echo An error occurred during coverage analysis!
echo Please check the output above for details.
pause
exit /b 1