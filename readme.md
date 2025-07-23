# Financial Analysis Tool

## Overview
This comprehensive financial analysis application provides sophisticated tools for **Free Cash Flow (FCF) analysis** and **Discounted Cash Flow (DCF) valuation** for both **US Market** and **TASE (Tel Aviv Stock Exchange)** stocks. 

The system includes:
- **CopyDataNew.py**: Legacy script for Excel data transfer and DCF template management
- **Streamlit Web Application**: Modern interface with multi-market support, automatic ticker processing, and currency-aware analysis

Key features include automatic currency handling (USD for US stocks, ILS/Agorot for TASE stocks), smart ticker processing (automatic .TA suffix for TASE stocks), and comprehensive DCF valuation with market-appropriate formatting.

## Modern Streamlit Application Workflow (Recommended)

### Quick Start - Multi-Market Support
1. **Select Market**: Choose US Market or TASE (Tel Aviv) from the sidebar radio buttons
2. **Prepare Data**: Create company folder with FY/ and LTM/ subfolders
3. **Load Analysis**: Select company folder in the web interface
4. **Review Results**: View FCF analysis and DCF valuation with market-appropriate currency

### Market-Specific Examples

#### US Market Example (Apple - AAPL)
```bash
# 1. Create folder structure
mkdir AAPL
mkdir AAPL/FY AAPL/LTM

# 2. Export financial statements from investing.com (USD millions)
# 3. Launch application
python run_streamlit_app.py

# 4. In web interface:
#    - Select "US Market" 
#    - Load AAPL folder
#    - System processes as "AAPL" ticker
#    - Results display in USD currency
```

#### TASE Market Example (Teva - TEVA)
```bash
# 1. Create folder structure  
mkdir TEVA
mkdir TEVA/FY TEVA/LTM

# 2. Export financial statements from investing.com (ILS millions)
# 3. Launch application
python run_streamlit_app.py

# 4. In web interface:
#    - Select "TASE (Tel Aviv)"
#    - Load TEVA folder  
#    - System processes "TEVA" → "TEVA.TA"
#    - Results display in ILS/Agorot currency
```

## Legacy Workflow (CopyDataNew.py)
1. Create parent folder mkdir <Ticker name> (GOOG)
2. Create sub folders FY (Fiscal Year) and LTM (Latest Twelve Month) using the mkdir command
3. Export from investing.com the 10yr income statement, Balance Sheet, Cashflow Statement into the <FY> folder.
4. Export from investing.com the 3yr latest twelve month income statement, Cashflow Statement into the <LTM> folder.
5. Export from investing.com the 3yr quarterly Balance Sheet into the <LTM> folder.
6. If needed install the requirements using the command: pip install -r requirements.txt
7. Run the program with the command: python CopyDataNew.py 
8. Step I: a search window will be opened asking for the template DCF file. Locate the file and continue.
9. Step II: a search window will be opened asking for the FY folder. Select it and continue.
10. Step III: a search window will be opened asking for the LTM folder. Select it and continue.
11. Step IV: a search window will be opened asking for the folder where the output DCF file will be saved. 
    It is recommended to save it in the parent Ticker folder.

## Modern FCF Analysis Application Features
The Streamlit web application provides:
- **Multi-Market Support**: US Market and TASE (Tel Aviv) stock analysis
- **Smart Ticker Processing**: Automatic .TA suffix handling for TASE stocks
- **Currency Awareness**: USD for US stocks, ILS/Agorot for TASE stocks  
- **Interactive FCF calculations**: FCFF, FCFE, LFCF with market-appropriate currency display
- **DCF valuation**: Customizable assumptions with currency-aware formatting
- **Market-Specific Examples**: Built-in guidance for both US and TASE markets
- **Sensitivity analysis and scenario testing**: Advanced financial modeling
- **Professional charts and visualizations**: Plotly-based interactive charts
- **PDF report generation**: Market-aware report formatting

## DCF Fair Value Calculation Methodology

### Overview
The DCF (Discounted Cash Flow) analysis in this application uses a comprehensive 10-year projection model with terminal value calculation to determine the fair value per share of a company.

### Calculation Process

#### **1. Base FCF Determination**
- Uses the most recent Free Cash Flow to Firm (FCFF) value from historical data
- Falls back to $100M if no historical data is available

#### **2. Growth Rate Assumptions**
- **Years 1-5**: Uses 3-year historical growth rate (or user input)
- **Years 5-10**: Uses 5-year historical growth rate (or user input)  
- **Terminal Growth**: Default 3% perpetual growth rate (user adjustable)

#### **3. 10-Year FCF Projections**
Each year's FCF is calculated as:
```
FCF(year) = Previous FCF × (1 + Growth Rate)
```

#### **4. Terminal Value Calculation (Gordon Growth Model)**
```
Terminal Value = FCF₁₁ / (Discount Rate - Terminal Growth Rate)
```
Where FCF₁₁ = Final projected FCF × (1 + Terminal Growth Rate)

#### **5. Present Value Calculations**
- **PV of each FCF**: `FCF(t) / (1 + Discount Rate)^t`
- **PV of Terminal Value**: `Terminal Value / (1 + Discount Rate)^10`

#### **6. Enterprise Value**
```
Enterprise Value = Sum of all PV of FCF + PV of Terminal Value
```

#### **7. Equity Value**
```
Equity Value = Enterprise Value - Net Debt
```
*Note: Net debt is estimated from financing cash flows or set to 0 if unavailable*

#### **8. Fair Value Per Share**
```
Fair Value Per Share = Equity Value × 1,000,000 / Shares Outstanding
```

### Key Components

**Shares Outstanding**: Determined via Yahoo Finance API using:
```
Shares Outstanding = Market Cap / Current Stock Price
```

**Discount Rate**: Default 12% (user adjustable)

**Terminal Growth Rate**: Default 3% (user adjustable)

### Complete DCF Formula
```
Fair Value = [Σ(FCF(t)/(1+r)^t) + (TV/(1+r)^10) - Net Debt] × 1M / Shares Outstanding
```

Where:
- FCF(t) = Free Cash Flow in year t
- r = Discount rate (Required Rate of Return)
- TV = Terminal Value
- Net Debt = Estimated net debt position

### Sensitivity Analysis
The system includes sensitivity analysis that recalculates the fair value across different discount rates and growth rate assumptions to show how sensitive the valuation is to key assumptions.

## Included files and folders
15. DCF calculation template file: FCF_Analysis_temp1.xlsx
16. An Example folder GOOG with sub folders.