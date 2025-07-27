@echo off
echo 🚀 Starting FCF Analysis Tool (Streamlit Version)
echo.
echo 📊 Modern Web-Based Financial Analysis Dashboard
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Smart dependency checking - only install if needed
echo 📦 Checking requirements...

REM Check if requirements.txt changed or packages missing
set REQUIREMENTS_CHANGED=0
set PACKAGES_MISSING=0

REM Quick check for key packages to determine if install is needed
python -c "import streamlit, pandas, plotly, openpyxl, numpy, scipy, yfinance, alpha_vantage, polygon, kaleido" 2>nul || set PACKAGES_MISSING=1

REM Compare requirements.txt modification time with last install (simple approach)
if not exist ".last_install_time" set REQUIREMENTS_CHANGED=1
if exist ".last_install_time" (
    for %%I in (requirements.txt) do (
        for %%J in (.last_install_time) do (
            if %%~tI gtr %%~tJ set REQUIREMENTS_CHANGED=1
        )
    )
)

REM Install only if needed
if %PACKAGES_MISSING%==1 (
    echo 🔄 Installing missing packages...
    pip install -r requirements.txt --quiet --disable-pip-version-check --prefer-binary --only-binary=:all: 2>nul || (
        echo ⚠️  Some packages may have file locks, but installation mostly succeeded
    )
    echo. > .last_install_time
) else if %REQUIREMENTS_CHANGED%==1 (
    echo 🔄 Requirements updated, installing...
    pip install -r requirements.txt --quiet --disable-pip-version-check --prefer-binary --only-binary=:all: 2>nul || (
        echo ⚠️  Some packages may have file locks, but installation mostly succeeded
    )
    echo. > .last_install_time
) else (
    echo ✅ All packages up to date
)

REM Launch the Streamlit application
echo.
echo 🌐 Launching application...
echo The tool will open in your web browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

python run_streamlit_app.py

echo.
echo 👋 Application closed
pause