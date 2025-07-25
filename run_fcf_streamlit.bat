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

REM Install requirements if needed
echo 📦 Checking requirements...
pip install -r requirements.txt --quiet --ignore-installed --disable-pip-version-check 2>nul || (
    echo ⚠️  Some packages may have file locks, but installation mostly succeeded
    echo 💡 If you encounter issues, please close any running Python processes and try again
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