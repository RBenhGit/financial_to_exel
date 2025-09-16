@echo off
:: Financial Analysis - Windows Startup Script
:: This batch file ensures proper Unicode setup and launches the application

title Financial Analysis Application

echo ========================================
echo Financial Analysis - Windows Launcher  
echo ========================================

:: Set UTF-8 code page for console
chcp 65001 > nul

:: Set Python UTF-8 environment
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Change to the application directory
cd /d "%~dp0"

:: Check if Python is available
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Starting Financial Analysis Application...
echo.
echo Press Ctrl+C to stop the application
echo ========================================

:: Run the Windows-optimized launcher
python run_streamlit_windows.py

:: Pause to show any error messages
if %errorlevel% neq 0 (
    echo.
    echo Application ended with error code: %errorlevel%
    pause
)