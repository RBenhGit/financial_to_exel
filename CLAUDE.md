# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application for financial analysis that automates the transfer of 10-year financial data from Investing.com Excel exports into a DCF (Discounted Cash Flow) analysis template. The tool extracts data from Income Statements, Balance Sheets, and Cash Flow Statements to populate a predefined Excel template for valuation analysis.

## Project Structure

### Core Applications
- `CopyDataNew.py` - Main application script that orchestrates the entire data extraction and DCF population process
- `fcf_analysis.py` - Legacy FCF analysis tool with matplotlib-based UI
- `fcf_analysis_streamlit.py` - **Modern Streamlit-based FCF analysis application** (recommended)

### Modular Architecture (New)
- `financial_calculations.py` - Core financial calculation logic (FCF calculations, growth rates)
- `dcf_valuation.py` - DCF valuation engine (projections, terminal value, sensitivity analysis)
- `data_processing.py` - Data processing utilities and Plotly visualization functions
- `run_streamlit_app.py` - Application launcher with requirements checking
- `test_modernization.py` - Comprehensive test suite for the modernized application

### Templates and Configuration
- `FCF_Analysis_Temp1.xlsx` - DCF calculation template file (referenced in readme but not tracked in git)
- `requirements.txt` - Python dependencies (includes new Streamlit and Plotly packages)
- `readme.md` - Detailed workflow documentation and usage instructions

### Data Folders
- `<TICKER>/` - Company-specific folders containing financial data:
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

### fcf_analysis.py Features
The advanced FCF analysis tool provides comprehensive financial analysis capabilities:

#### **FCF Analysis Tab**
- **Three FCF Calculation Methods**:
  - FCFF (Free Cash Flow to Firm): EBIT(1-Tax Rate) + D&A - Working Capital Change - CapEx
  - FCFE (Free Cash Flow to Equity): Net Income + D&A - Working Capital Change - CapEx + Net Borrowing  
  - LFCF (Levered Free Cash Flow): Operating Cash Flow - CapEx
- **Interactive Line Plots**: Historical FCF trends with linear regression fits
- **Comprehensive Slope Analysis**: 1-10 year annualized growth rates with color-coded table
- **Slope Visualization Graph**: Comparison of growth trends across different time periods

#### **DCF Analysis Tab**
- **Automated DCF Valuation**: Uses historical FCF data to project future cash flows
- **Intelligent Assumptions**: Growth rates calculated from 3-year historical trends
- **Waterfall Chart**: Visual breakdown from FCF projections to equity value
- **Sensitivity Analysis**: Interactive heatmap showing valuation sensitivity to discount rate and growth rate changes
- **Professional DCF Components**:
  - 5-year FCF projections
  - Terminal value calculation (Gordon Growth Model)
  - Present value discounting
  - Enterprise to equity value bridge

#### **Interactive Features**
- **Tab-Based Interface**: Switch between FCF and DCF analysis
- **Dynamic Visualizations**: Real-time updates based on company data
- **Export Capabilities**: Save analysis as high-resolution images

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

#### Advanced FCF Analysis Tool

#### Modern Streamlit Application (Recommended)
```bash
python run_streamlit_app.py
# OR
streamlit run fcf_analysis_streamlit.py
# OR (Windows)
run_fcf_streamlit.bat
```

The modern web-based application provides:
- **Professional Web Interface**: Responsive design that works on any device
- **Interactive Tabs**: Clean FCF and DCF analysis sections
- **Real-time Updates**: Dynamic calculations when parameters change
- **Enhanced Visualizations**: Interactive Plotly charts with hover details
- **Export Capabilities**: Download charts and data in multiple formats
- **Better User Experience**: Intuitive forms, validation, and error handling

#### Legacy Matplotlib Application
```bash
python fcf_analysis.py
```

The legacy application will:
1. Open GUI dialog to select company folder (containing FY and LTM subfolders)
2. Automatically load and analyze financial statements
3. Display matplotlib-based tabbed interface with FCF and DCF analysis
4. Allow switching between analysis views and exporting results

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

### Core Dependencies
- `openpyxl` - Excel file manipulation and data extraction
- `pandas` - Data analysis and manipulation  
- `numpy` - Numerical computing and array operations
- `matplotlib` - Plotting and visualization framework
- `scipy` - Scientific computing (linear regression analysis)
- `tkinter` - GUI file/folder selection dialogs (built-in Python library)

### Standard Libraries
- `os` - File system operations
- `datetime` - Date and time handling
- `logging` - Application logging and debugging

## Usage Notes

### FCF Analysis Tool Features
- **Automated Financial Statement Processing**: Intelligently categorizes and loads Excel files
- **Multiple FCF Methodologies**: Provides three different FCF calculation approaches for comprehensive analysis
- **Growth Trend Analysis**: Calculates annualized growth rates across 1-10 year periods
- **Professional DCF Valuation**: Generates enterprise and equity valuations with sensitivity analysis
- **Interactive Visualization**: Tab-based interface for seamless analysis workflow

### Data Quality Requirements
- Financial statements should cover at least 3 years for meaningful trend analysis
- Excel files must follow Investing.com export format structure
- Company folder structure (FY/LTM) is required for both tools to function properly