@echo off
echo Starting FCF Analysis Application...
echo.

REM Check if port 8501 is available, if not use 8502
netstat -an | findstr ":8501" >nul
if %errorlevel%==0 (
    echo Port 8501 is busy, trying port 8502...
    python -m streamlit run ui/streamlit/fcf_analysis_streamlit.py --server.port=8502
) else (
    echo Using default port 8501...
    python -m streamlit run ui/streamlit/fcf_analysis_streamlit.py --server.port=8501
)

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start the application.
    echo Please ensure all dependencies are installed by running:
    echo pip install -r requirements.txt
    echo.
    pause
)