# Input Variables Reference Guide

This comprehensive guide documents all input variables required for each analysis type in the Financial Analysis Application.

## 📈 FCF Analysis

### Data Source Requirements
| Requirement | Description | Location |
|-------------|-------------|----------|
| **Financial Statements** | Excel files: Income Statement, Balance Sheet, Cash Flow Statement | Company folder → FY/LTM subfolders |
| **File Structure** | Organized in FY (Full Year) and LTM (Last Twelve Months) folders | Main app → Load Company Data |
| **Market Data** | Current stock price and market cap | Auto-fetched via ticker symbol |

### Financial Statement Input Variables

#### FCFF (Free Cash Flow to Firm) Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| FCFF | EBIT | Income Statement |
| FCFF | Income Tax Expense | Income Statement |
| FCFF | Depreciation & Amortization | Cash Flow Statement |
| FCFF | Total Current Assets | Balance Sheet |
| FCFF | Total Current Liabilities | Balance Sheet |
| FCFF | Capital Expenditure | Cash Flow Statement |

**Formula**: FCFF = EBIT(1-Tax Rate) + Depreciation & Amortization - Change in Working Capital - Capital Expenditures

#### FCFE (Free Cash Flow to Equity) Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| FCFE | Net Income | Income Statement |
| FCFE | Depreciation & Amortization | Cash Flow Statement |
| FCFE | Total Current Assets | Balance Sheet |
| FCFE | Total Current Liabilities | Balance Sheet |
| FCFE | Capital Expenditure | Cash Flow Statement |
| FCFE | Long-Term Debt Issued | Cash Flow Statement |
| FCFE | Long-Term Debt Repaid | Cash Flow Statement |

**Formula**: FCFE = Net Income + Depreciation & Amortization - Change in Working Capital - Capital Expenditures + Net Borrowing

#### LFCF (Levered Free Cash Flow) Calculation  
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| LFCF | Cash from Operations | Cash Flow Statement |
| LFCF | Capital Expenditure | Cash Flow Statement |

**Formula**: LFCF = Cash from Operations - Capital Expenditures

#### Working Capital Change Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Change in Working Capital | Total Current Assets (Current Year) | Balance Sheet |
| Change in Working Capital | Total Current Liabilities (Current Year) | Balance Sheet |
| Change in Working Capital | Total Current Assets (Previous Year) | Balance Sheet |
| Change in Working Capital | Total Current Liabilities (Previous Year) | Balance Sheet |

**Formula**: Change in WC = (Current Assets - Current Liabilities)Current - (Current Assets - Current Liabilities)Previous

### Calculated Outputs
- **FCFF** (Free Cash Flow to Firm)
- **FCFE** (Free Cash Flow to Equity) 
- **LFCF** (Levered Free Cash Flow)
- Growth rates (1-year, 3-year, 5-year)

---

## 💰 DCF Valuation

### Required Data Sources
| Data Source | Description | Location |
|-------------|-------------|----------|
| **FCF Results** | From FCF Analysis tab | Must run FCF Analysis first |
| **Market Data** | Current stock price, shares outstanding | Auto-fetched via ticker |

### Financial Statement Input Variables (Inherited from FCF Analysis)

#### DCF Calculation Base Data
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| DCF Base FCF | FCFE/FCFF/LFCF Values | FCF Analysis Results |
| DCF Base FCF | Historical Growth Rates | Calculated from FCF data |
| Enterprise Value | Current Stock Price | Market Data (yfinance) |
| Enterprise Value | Shares Outstanding | Market Data (yfinance) |
| Enterprise Value | Market Capitalization | Market Data (yfinance) |

### User Input Variables

| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **FCF Type** | Selectbox | FCFE | FCFE, FCFF, LFCF | DCF Tab → Configuration | ✅ |
| **Growth Rate (Years 1-5)** | Number Input | Historical 5yr avg | -50% to 100% | DCF Tab → Growth Assumptions | ✅ |
| **Growth Rate (Years 6-10)** | Number Input | Historical 10yr avg | -50% to 50% | DCF Tab → Growth Assumptions | ✅ |
| **Terminal Growth Rate** | Number Input | 3.0% | 0% to 10% | DCF Tab → Growth Assumptions | ✅ |
| **Discount Rate (WACC)** | Number Input | 10.0% | 5% to 30% | DCF Tab → Valuation Assumptions | ✅ |
| **Projection Period** | Selectbox | 10 years | 5, 7, 10 years | DCF Tab → Valuation Assumptions | ✅ |
| **Terminal Method** | Selectbox | Growth Method | Growth Method, Multiple Method | DCF Tab → Valuation Assumptions | ✅ |

### Sensitivity Analysis (Optional)
| Variable | Input Type | Default | Range | Location |
|----------|------------|---------|-------|-----------|
| **Min Discount Rate** | Number Input | 8.0% | User defined | DCF Tab → Sensitivity Analysis |
| **Max Discount Rate** | Number Input | 15.0% | User defined | DCF Tab → Sensitivity Analysis |
| **Min Growth Rate** | Number Input | 0.0% | User defined | DCF Tab → Sensitivity Analysis |
| **Max Growth Rate** | Number Input | 5.0% | User defined | DCF Tab → Sensitivity Analysis |

---

## 🏆 DDM Valuation

### Required Data Sources
| Data Source | Description | Location |
|-------------|-------------|----------|
| **Dividend History** | Historical dividend payments | Auto-fetched via yfinance API |
| **Market Data** | Current stock price, shares outstanding | Auto-fetched via ticker |
| **Financial Statements** | For payout ratio calculations | Company folder (if available) |

### Financial Statement Input Variables

#### Dividend Data Collection
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Historical Dividends | Dividends Per Share | yfinance API |
| Historical Dividends | Annual Dividend Payments | yfinance API |
| Dividend Validation | Dividends Paid | Cash Flow Statement |
| Dividend Validation | Net Income | Income Statement |
| Dividend Validation | Earnings Per Share | Income Statement |
| Market Data | Current Stock Price | Market Data (yfinance) |
| Market Data | Shares Outstanding | Market Data (yfinance) |
| Market Data | Market Capitalization | Market Data (yfinance) |

#### Payout Ratio Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Payout Ratio | Total Dividends Paid | Cash Flow Statement |
| Payout Ratio | Net Income | Income Statement |
| Payout Ratio | Shares Outstanding | Market Data |

**Formula**: Payout Ratio = (Dividends Paid / Net Income) × 100%

#### Dividend Growth Rate Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Growth Calculation | Current Year Dividend | Dividend History |
| Growth Calculation | Previous Year Dividend | Dividend History |
| Growth Calculation | 3-Year Historical Average | Calculated from history |
| Growth Calculation | 5-Year Historical Average | Calculated from history |

### User Input Variables

| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Discount Rate** | Number Input | 10.0% | 1% to 30% | DDM Tab → Required Rate of Return | ✅ |
| **Model Type** | Selectbox | Auto | Auto, Gordon, Two-Stage, Multi-Stage | DDM Tab → Required Rate of Return | ✅ |
| **Stage 1 Growth** | Number Input | 8.0% | -10% to 50% | DDM Tab → Growth Rates | ✅ |
| **Stage 2 Growth** | Number Input | 4.0% | -5% to 25% | DDM Tab → Growth Rates | ✅ |
| **Terminal Growth** | Number Input | 3.0% | 0% to 10% | DDM Tab → Growth Rates | ✅ |
| **Stage 1 Years** | Number Input | 5 | 1 to 15 | DDM Tab → Time Periods | ✅ |
| **Stage 2 Years** | Number Input | 5 | 1 to 15 | DDM Tab → Time Periods | ✅ |

### Model Selection Logic (Auto Mode)
- **Gordon Growth**: Mature companies with consistent dividend growth < 7%
- **Two-Stage**: Companies with moderate growth (7-15%) and good dividend history
- **Multi-Stage**: High growth companies (>15%) with complex growth patterns

### Sensitivity Analysis (Optional)
| Variable | Input Type | Default | Range | Location |
|----------|------------|---------|-------|-----------|
| **Min Discount Rate** | Number Input | 8.0% | User defined | DDM Tab → Sensitivity Analysis |
| **Max Discount Rate** | Number Input | 15.0% | User defined | DDM Tab → Sensitivity Analysis |
| **Min Growth Rate** | Number Input | 0.0% | User defined | DDM Tab → Sensitivity Analysis |
| **Max Growth Rate** | Number Input | 8.0% | User defined | DDM Tab → Sensitivity Analysis |

---

## 📊 P/B Analysis

### Required Data Sources
| Data Source | Description | Location |
|-------------|-------------|----------|
| **Market Data** | Current stock price, shares outstanding | Auto-fetched via ticker |
| **Balance Sheet** | Book value, total equity | Financial statements or API |
| **Industry Data** | Sector/industry classification | Auto-detected via ticker |

### Financial Statement Input Variables

#### Book Value Per Share Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Book Value | Total Shareholders' Equity | Balance Sheet |
| Book Value | Total Stockholders' Equity | Balance Sheet |
| Book Value | Total Equity | Balance Sheet |
| Book Value | Common Stockholders' Equity | Balance Sheet |
| Book Value | Book Value | Balance Sheet |
| Book Value | Net Worth | Balance Sheet |
| Market Data | Shares Outstanding | Market Data (yfinance) |
| Market Data | Current Stock Price | Market Data (yfinance) |

**Formula**: Book Value Per Share = Total Shareholders' Equity ÷ Shares Outstanding

#### P/B Ratio Calculation
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| P/B Ratio | Current Stock Price | Market Data |
| P/B Ratio | Book Value Per Share | Calculated from Balance Sheet |

**Formula**: P/B Ratio = Current Stock Price ÷ Book Value Per Share

#### Industry Comparison Data
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Industry Classification | Sector Information | Market Data (yfinance) |
| Industry Classification | Industry Group | Market Data (yfinance) |
| Peer Analysis | Comparable Companies | Auto-detected by sector |
| Historical P/B | Historical Price Data | Market Data (yfinance) |
| Historical P/B | Historical Book Values | Financial statements |

### User Input Variables

| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Ticker Symbol** | Auto-detected | From loaded data | Valid ticker | P/B Tab → Auto-populated | ✅ |
| **Current Price** | Number Input | Auto-fetched | > 0 | P/B Tab → Market Data Override | ❌ |

### Industry Benchmarks (Built-in)
| Industry | Median P/B | Low Range | High Range |
|----------|------------|-----------|-------------|
| **Technology** | 3.5 | 1.5 | 8.0 |
| **Healthcare** | 2.8 | 1.2 | 6.0 |
| **Financial Services** | 1.2 | 0.8 | 2.0 |
| **Consumer Cyclical** | 2.0 | 0.8 | 4.5 |
| **Consumer Defensive** | 2.5 | 1.2 | 4.0 |
| **Industrial** | 2.2 | 1.0 | 4.0 |
| **Energy** | 1.5 | 0.5 | 3.0 |
| **Utilities** | 1.8 | 1.0 | 2.5 |
| **Real Estate** | 1.4 | 0.8 | 2.2 |
| **Materials** | 1.8 | 0.9 | 3.5 |

---

## 📄 Report Generation

### Required Data Sources
| Data Source | Description | Location |
|-------------|-------------|----------|
| **Completed Analysis** | FCF, DCF, DDM, or P/B results | Must run desired analyses first |
| **Company Data** | Name, ticker, financial metrics | Loaded company data |

### User Input Variables

| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Report Sections** | Checkboxes | All selected | Multiple options | Report Tab → Select Sections | ✅ |
| **Export Format** | Selectbox | PDF | PDF, CSV, Excel | Report Tab → Export Options | ✅ |
| **Include Charts** | Checkbox | True | True/False | Report Tab → Export Options | ❌ |
| **Output Directory** | File Browser | Auto-detected | Valid path | Report Tab → Export Location | ❌ |

### Available Report Sections
- Executive Summary
- FCF Analysis Results
- DCF Valuation Details
- DDM Valuation (if applicable)
- P/B Analysis
- Sensitivity Analysis
- Charts and Visualizations
- Assumptions and Methodology

---

## 📊 Watch Lists

### Data Source Requirements
| Data Source | Description | Location |
|-------------|-------------|----------|
| **Watch List Database** | SQLite database file | data/watch_lists.db |
| **Market Data** | Real-time prices for tracked stocks | Auto-fetched via APIs |

### Database Schema Input Variables

#### Watch Lists Table
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Watch Lists | ID (Primary Key) | Auto-generated |
| Watch Lists | Name | User Input |
| Watch Lists | Description | User Input |
| Watch Lists | Created Date | System Timestamp |
| Watch Lists | Updated Date | System Timestamp |

#### Analysis Records Table  
| Variable Name | Input | Source of Input |
|---------------|-------|-----------------|
| Analysis Records | Watch List ID (Foreign Key) | Database Reference |
| Analysis Records | Ticker Symbol | User Input |
| Analysis Records | Company Name | Market Data API |
| Analysis Records | Analysis Date | System Timestamp |
| Analysis Records | Current Price | Market Data (yfinance) |
| Analysis Records | Fair Value | DCF/DDM/P/B Analysis |
| Analysis Records | Discount Rate | User Configuration |
| Analysis Records | Terminal Growth Rate | User Configuration |
| Analysis Records | Upside/Downside % | Calculated Result |
| Analysis Records | FCF Type | User Selection |
| Analysis Records | DCF Assumptions | Analysis Configuration |
| Analysis Records | Analysis Metadata | System Generated |
| Analysis Records | P/B Ratio | P/B Analysis Result |
| Analysis Records | Book Value Per Share | Balance Sheet Data |
| Analysis Records | P/B Industry Median | Industry Benchmarks |
| Analysis Records | P/B Valuation Fair | P/B Analysis Result |

### User Input Variables

#### Creating/Managing Watch Lists
| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Watch List Name** | Text Input | None | 1-50 characters | Watch Lists Tab → Create New | ✅ |
| **Description** | Text Area | None | Optional | Watch Lists Tab → Create New | ❌ |

#### Adding Stocks
| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Ticker Symbol** | Text Input | None | Valid ticker | Watch Lists Tab → Add Stock | ✅ |
| **Target Price** | Number Input | None | > 0 | Watch Lists Tab → Add Stock | ❌ |
| **Notes** | Text Area | None | Optional | Watch Lists Tab → Add Stock | ❌ |

#### Analysis and Tracking
| Variable | Input Type | Default | Range | Location | Required |
|----------|------------|---------|-------|-----------|----------|
| **Selected Watch List** | Selectbox | First available | Existing lists | Watch Lists Tab → Analysis | ✅ |
| **Analysis Type** | Selectbox | All | FCF, DCF, DDM, P/B | Watch Lists Tab → Batch Analysis | ✅ |
| **Export Format** | Selectbox | CSV | CSV, Excel | Watch Lists Tab → Export | ❌ |

---

## 🔧 System Configuration

### API Configuration (Optional)
| Variable | Description | Location | Required |
|----------|-------------|----------|----------|
| **yfinance** | Built-in market data | Automatic | ✅ |
| **Alternative APIs** | FMP, Alpha Vantage, Polygon | config files | ❌ |

### Application Settings
| Variable | Input Type | Default | Location | Required |
|----------|------------|---------|-----------|----------|
| **Default Export Directory** | File Browser | ./exports | Settings | ❌ |
| **Currency Display** | Selectbox | USD | Settings | ❌ |
| **Precision (Decimal Places)** | Number Input | 2 | Settings | ❌ |

---

## 📁 Data Input Methods

### Method 1: Excel File Structure
```
Company_Name/
├── FY/
│   ├── Company_Name - Income Statement.xlsx
│   ├── Company_Name - Balance Sheet.xlsx
│   └── Company_Name - Cash Flow Statement.xlsx
└── LTM/
    ├── Company_Name - Income Statement.xlsx
    ├── Company_Name - Balance Sheet.xlsx
    └── Company_Name - Cash Flow Statement.xlsx
```

### Method 2: Ticker Symbol Entry
- Enter ticker symbol in main interface
- System auto-fetches financial data via APIs
- Supports US markets and TASE (Tel Aviv Stock Exchange)

### Method 3: Watch List Import
- Import tickers from existing watch lists
- Batch analysis capabilities
- Historical tracking and monitoring

---

## ⚠️ Important Notes

### Data Quality Requirements
1. **Financial Statements**: Must have consistent date ranges and complete data
2. **Dividend History**: Minimum 3 years for DDM analysis
3. **Market Data**: Current prices required for accurate valuations

### Calculation Dependencies
1. **DCF Analysis**: Requires completed FCF Analysis
2. **DDM Analysis**: Requires dividend-paying stocks
3. **P/B Analysis**: Requires balance sheet data
4. **Report Generation**: Requires completed analyses

### Error Handling
- Missing data fields will show warnings
- Invalid input ranges are automatically constrained
- Fallback calculations used when primary data unavailable

### Performance Notes
- Large datasets may take longer to process
- Sensitivity analysis generates multiple calculations
- Real-time market data fetching may introduce delays

---

## 📋 Summary: Complete Input Variables Map

### Financial Statement Line Items by Analysis

#### FCF Analysis Required Fields
| Excel Field Name | Statement | Used In |
|------------------|-----------|---------|
| **EBIT** | Income Statement | FCFF |
| **Net Income** | Income Statement | FCFE |
| **Income Tax Expense** | Income Statement | FCFF |
| **EBT** | Income Statement | Tax Rate Calculation |
| **Depreciation & Amortization** | Cash Flow Statement | FCFF, FCFE, LFCF |
| **Cash from Operations** | Cash Flow Statement | LFCF |
| **Capital Expenditure** | Cash Flow Statement | FCFF, FCFE, LFCF |
| **Total Current Assets** | Balance Sheet | Working Capital |
| **Total Current Liabilities** | Balance Sheet | Working Capital |
| **Long-Term Debt Issued** | Cash Flow Statement | FCFE Net Borrowing |
| **Long-Term Debt Repaid** | Cash Flow Statement | FCFE Net Borrowing |

#### P/B Analysis Required Fields
| Excel Field Name | Statement | Used In |
|------------------|-----------|---------|
| **Total Shareholders' Equity** | Balance Sheet | Book Value Per Share |
| **Total Stockholders' Equity** | Balance Sheet | Book Value Per Share |
| **Total Equity** | Balance Sheet | Book Value Per Share |
| **Common Stockholders' Equity** | Balance Sheet | Book Value Per Share |
| **Book Value** | Balance Sheet | Book Value Per Share |
| **Net Worth** | Balance Sheet | Book Value Per Share |

#### DDM Analysis Required Fields
| Data Field | Source | Used In |
|------------|--------|---------|
| **Dividends Per Share** | yfinance API | Dividend History |
| **Annual Dividend Payments** | yfinance API | Dividend History |
| **Dividends Paid** | Cash Flow Statement | Payout Ratio |
| **Earnings Per Share** | Income Statement | Payout Ratio |

### Market Data Dependencies
| Analysis | Market Data Required | API Source |
|----------|---------------------|------------|
| **FCF Analysis** | Current Price, Market Cap | yfinance |
| **DCF Valuation** | Current Price, Shares Outstanding | yfinance |
| **DDM Valuation** | Current Price, Shares Outstanding, Dividend History | yfinance |
| **P/B Analysis** | Current Price, Shares Outstanding, Industry Data | yfinance |
| **Watch Lists** | Real-time Prices, Company Names | yfinance |

### Data Validation Requirements
| Analysis | Minimum Data | Quality Checks |
|----------|--------------|----------------|
| **FCF Analysis** | 3 years financial statements | Complete Income, Balance, Cash Flow |
| **DCF Valuation** | FCF calculation results | Positive FCF values, valid growth rates |
| **DDM Valuation** | 3 years dividend history | Consistent dividend payments |
| **P/B Analysis** | Current balance sheet | Positive book value |
| **Watch Lists** | Valid ticker symbols | Market data availability |

### Critical Formula Dependencies
| Formula | Required Inputs | Data Quality Impact |
|---------|----------------|-------------------|
| **FCFF** = EBIT(1-Tax) + D&A - ΔWC - CapEx | EBIT, Tax Rate, D&A, Current Assets/Liabilities, CapEx | High - Missing any component invalidates calculation |
| **FCFE** = NI + D&A - ΔWC - CapEx + Net Borrowing | Net Income, D&A, Current Assets/Liabilities, CapEx, Debt Changes | High - Missing any component invalidates calculation |
| **LFCF** = Operating CF - CapEx | Operating Cash Flow, Capital Expenditure | Medium - Simpler calculation, fewer dependencies |
| **P/B Ratio** = Price / Book Value Per Share | Stock Price, Shareholders' Equity, Shares Outstanding | Medium - Market data dependent |
| **DDM Value** = Dividends / (r - g) | Dividend History, Required Return, Growth Rate | High - Very sensitive to growth rate assumptions |

This reference guide provides complete documentation of all input variables and requirements across the entire Financial Analysis Application, with detailed mapping of financial statement line items to specific calculations.