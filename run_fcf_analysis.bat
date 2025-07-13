@echo off
echo Free Cash Flow Analysis Tool
echo ==========================
echo.
echo Installing required packages...
pip install matplotlib pandas numpy openpyxl

echo.
echo Starting FCF Analysis...
python fcf_analysis_windows.py

pause