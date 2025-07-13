# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application for financial analysis that automates the transfer of 10-year financial data from Investing.com Excel exports into a DCF (Discounted Cash Flow) analysis template. The tool extracts data from Income Statements, Balance Sheets, and Cash Flow Statements to populate a predefined Excel template for valuation analysis.

## Project Structure

### Core Applications
- `CopyDataNew.py` - Main application script that orchestrates the entire data extraction and DCF population process
- `fcf_analysis_streamlit.py` - **Streamlit-based FCF analysis application**

### Modular Architecture
- `financial_calculations.py` - Core financial calculation logic (FCF calculations, growth rates)
- `dcf_valuation.py` - DCF valuation engine (projections, terminal value, sensitivity analysis)
- `data_processing.py` - Data processing utilities and Plotly visualization functions
- `data_validator.py` - Comprehensive data validation and quality reporting
- `report_generator.py` - PDF report generation using ReportLab
- `run_streamlit_app.py` - Application launcher with requirements checking

### Application Launchers
- `run_fcf_streamlit.bat` - Windows batch script for Streamlit app

### Configuration
- `requirements.txt` - Python dependencies (includes Streamlit, Plotly, ReportLab packages)
- `.env.example` - Environment configuration template with DCF settings
- `readme.md` - Detailed workflow documentation and usage instructions

### Sample Data Available
- `GOOG/` - Alphabet Inc Class C
- `MSFT/` - Microsoft Corporation
- `NVDA/` - NVIDIA Corporation
- `TSLA/` - Tesla Inc
- `V/` - Visa Inc Class A

Each company folder contains:
  - `FY/` - Fiscal Year financial statements (10-year historical data)
  - `LTM/` - Latest Twelve Months financial statements (3-year recent data)

## Key Components

### CopyDataNew.py Architecture
The main script follows this workflow:
1. **File Selection Phase**: Uses tkinter dialogs to select DCF template and source financial files
2. **Data Categorization**: Automatically categorizes files by type (Balance Sheet, Cash Flow, Income Statement)
3. **Workbook Loading**: Loads all Excel files using openpyxl
4. **Data Extraction**: Maps specific financial metrics from source files to target DCF template
5. **Output Generation**: Saves populated DCF file with company-specific naming

### CopyDataNew.py Financial Metrics Extracted
- **Income Statement**: Net Interest Expenses, EBT, Income Tax, Net Income, EBIT
- **Balance Sheet**: Total Current Assets, Total Current Liabilities  
- **Cash Flow**: Depreciation & Amortization, Cash from Operations, CapEx, Cash from Financing

### FCF Analysis Capabilities
The Streamlit application provides comprehensive financial analysis capabilities:

#### **Three FCF Calculation Methods**
- **FCFF (Free Cash Flow to Firm)**: `EBIT(1-Tax Rate) + D&A - Working Capital Change - CapEx`
- **FCFE (Free Cash Flow to Equity)**: `Net Income + D&A - Working Capital Change - CapEx + Net Borrowing`  
- **LFCF (Levered Free Cash Flow)**: `Operating Cash Flow - CapEx`

#### **DCF Valuation Features**
- **10-year FCF projections** with variable growth rates by period
- **Terminal value calculation** using Gordon Growth Model
- **Enterprise to equity value bridge** with debt and cash adjustments
- **Sensitivity analysis** with interactive heatmaps
- **Automatic ticker data integration** via Yahoo Finance API

#### **Advanced Analysis**
- **Growth trend analysis** across 1-10 year periods with linear regression
- **Data validation and quality scoring** with comprehensive reporting
- **Professional PDF report generation** with charts and analysis
- **Interactive Plotly visualizations** (Streamlit version)
- **Waterfall charts** for valuation breakdown

## Common Commands

### Installation and Setup
```bash
pip install -r requirements.txt
```

### Running the Applications

#### Excel Data Transfer Tool
```bash
python CopyDataNew.py
```

The application will open GUI dialogs for:
1. Selecting DCF template file
2. Selecting FY folder (containing 10-year historical data)
3. Selecting LTM folder (containing recent quarterly/annual data)
4. Choosing output directory for the generated DCF file

#### FCF Analysis Application

#### Streamlit Application
```bash
python run_streamlit_app.py
# OR
streamlit run fcf_analysis_streamlit.py
# OR (Windows)
run_fcf_streamlit.bat
```

Features:
- **Professional web interface** with responsive design
- **Interactive Plotly charts** with hover details and zoom functionality
- **Real-time parameter adjustments** for discount rates and growth assumptions
- **PDF report generation** with comprehensive analysis and charts
- **Data validation reporting** with quality scores and missing data alerts
- **Yahoo Finance integration** for automatic ticker data and current stock prices

## Data Requirements

### Expected File Structure
```
<TICKER>/
├── FY/
│   ├── <Company> - Income Statement.xlsx
│   ├── <Company> - Balance Sheet.xlsx
│   └── <Company> - Cash Flow Statement.xlsx
└── LTM/
    ├── <Company> - Income Statement.xlsx
    ├── <Company> - Balance Sheet.xlsx
    └── <Company> - Cash Flow Statement.xlsx
```

### File Naming Conventions
Files must contain specific keywords for automatic categorization:
- Files with "Balance" → Balance Sheet
- Files with "Cash" → Cash Flow Statement  
- Files with "Income" → Income Statement

## Error Handling

The application includes comprehensive error handling:
- Missing file validation with detailed logging
- Workbook loading error recovery
- Alternative filename generation for output files
- Company name sanitization for file paths

## Dependencies

### Core Dependencies (from requirements.txt)
- `openpyxl>=3.0.0` - Excel file manipulation and data extraction
- `pandas>=1.3.0` - Data analysis and manipulation  
- `numpy>=1.20.0` - Numerical computing and array operations
- `scipy>=1.7.0` - Scientific computing (linear regression analysis)
- `yfinance>=0.2.0` - Yahoo Finance API for stock data
- `streamlit>=1.28.0` - Web-based UI framework
- `plotly>=5.15.0` - Interactive visualizations and charts
- `reportlab>=4.0.0` - PDF report generation
- `kaleido>=0.2.1` - Static image export for Plotly charts

### Built-in Libraries
- `tkinter` - GUI file/folder selection dialogs
- `os` - File system operations
- `datetime` - Date and time handling
- `logging` - Application logging and debugging

## Environment Configuration

### Default Settings (.env.example)
- **Discount Rate**: 10%
- **Terminal Growth Rate**: 2.5%
- **Projection Years**: 5 (extendable to 10)
- **Chart DPI**: 300
- **Excel Engine**: openpyxl

## Architecture Notes

### Code Organization
- **Modular design** with separate modules for calculations, validation, and visualization
- **Clean separation** between data processing, analysis logic, and UI components
- **Streamlit-based interface** with modern web UI and interactive components
- **Comprehensive error handling** with logging throughout all modules

### Data Processing Pipeline
1. **File categorization** by keywords (Balance, Cash, Income)
2. **Data extraction** from standardized Investing.com Excel formats
3. **Data validation** with quality scoring and missing data detection
4. **Financial calculations** using multiple FCF methodologies
5. **DCF modeling** with flexible growth assumptions and sensitivity analysis
6. **Visualization and reporting** through interactive charts and PDF generation

### Key Technical Features
- **Yahoo Finance integration** for real-time stock data and automatic ticker lookup
- **Plotly integration** for interactive, exportable charts with hover details
- **ReportLab PDF generation** for professional analysis reports
- **Comprehensive data validation** with quality metrics and recommendations
- **Environment-based configuration** supporting customizable default parameters

## Data Quality Requirements
- Financial statements should cover at least 3 years for meaningful trend analysis
- Excel files must follow Investing.com export format structure
- Company folder structure (FY/LTM) is required for both tools to function properly
- Missing data is handled gracefully with quality reporting and alternative calculation methods