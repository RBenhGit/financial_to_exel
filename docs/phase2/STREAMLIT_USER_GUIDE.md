# Streamlit Financial Analysis Platform - User Guide

## Overview

The Streamlit Financial Analysis Platform provides a comprehensive, web-based interface for sophisticated financial analysis. This guide covers all features and workflows available in Phase 2 of the platform.

## Getting Started

### 1. Launching the Application

#### **Method 1: Python Command**
```bash
cd /path/to/financial_to_excel
python ui/streamlit/fcf_analysis_streamlit.py
```

#### **Method 2: Batch Script (Windows)**
```bash
run_fcf_streamlit.bat
```

#### **Method 3: Streamlit Command**
```bash
streamlit run ui/streamlit/fcf_analysis_streamlit.py
```

The application will open in your default web browser at `http://localhost:8501`

### 2. Application Structure

The interface features a **tabbed layout** with different analysis modules:

**Without Data Loaded:**
- 🔍 **Company Search** - Discover and search companies
- 📊 **Watch Lists** - Manage saved company lists
- 📈 **Real-Time Prices** - Live market data (if available)
- 📚 **Help & Guide** - Documentation and tutorials
- 🏠 **Welcome** - Getting started information

**With Data Loaded (Full Analysis Suite):**
- 🔍 **Company Search** - Company discovery tools
- 📈 **FCF Analysis** - Free Cash Flow calculations
- 💰 **DCF Valuation** - Discounted Cash Flow modeling
- 🏆 **DDM Valuation** - Dividend Discount Model analysis
- 📊 **P/B Analysis** - Price-to-Book ratio analysis
- 🧮 **Financial Ratios** - Comprehensive ratio analysis
- 📊 **Financial Trends** - Trend visualization and analysis
- 🔄 **Company Comparison** - Multi-company comparison tools
- 📄 **Generate Report** - Export and reporting features
- 📊 **Watch Lists** - Portfolio management
- 📈 **Real-Time Prices** - Live market monitoring
- 🚀 **Performance Monitor** - System performance tracking
- ⚙️ **User Preferences** - Personalization settings
- 🤝 **Collaboration** - Team collaboration features
- 📚 **Help & Guide** - Documentation and support

---

## Data Loading & Configuration

### **Sidebar Data Configuration**

The sidebar provides centralized data source management:

#### **Data Source Selection**
1. **Excel-First Mode**: Prioritizes Excel data with API fallback
2. **API-First Mode**: Uses APIs primarily with Excel fallback
3. **Auto Mode**: Intelligently selects best available source

#### **Company Data Input**

**Option 1: Excel File Upload**
1. Click **"Browse files"** in the sidebar
2. Select company folder containing:
   - `Income Statement.xlsx`
   - `Balance Sheet.xlsx`
   - `Cash Flow Statement.xlsx`
3. Files should be organized in `FY/` (Fiscal Year) or `LTM/` (Last Twelve Months) subfolders

**Option 2: Ticker Symbol Entry**
1. Enter ticker symbol (e.g., "AAPL", "MSFT")
2. System automatically fetches data from configured APIs
3. Supports US and international markets

**Option 3: Manual Data Entry**
1. Use data input forms for custom analysis
2. Enter financial statement data directly
3. Suitable for private companies or custom scenarios

#### **API Configuration**
Configure API keys in the sidebar for enhanced data access:
- **yfinance**: Free market data (no key required)
- **Alpha Vantage**: Premium financial data
- **FMP (Financial Modeling Prep)**: Comprehensive financial APIs
- **Polygon**: Real-time and historical market data

---

## Core Analysis Modules

### 1. 📈 **FCF Analysis Tab**

#### **Purpose**
Calculate and analyze Free Cash Flow using multiple methodologies.

#### **Key Features**

**FCF Calculation Methods:**
- **FCFE (Free Cash Flow to Equity)**: Cash available to shareholders
- **FCFF (Free Cash Flow to Firm)**: Cash available to all capital providers
- **Levered FCF**: Debt-adjusted cash flow calculations

**Analysis Components:**
- Historical FCF trends and growth rates
- FCF yield and margin analysis
- FCF stability and predictability metrics
- Growth rate projections and sustainability

#### **How to Use**
1. Load company data via sidebar
2. Navigate to **FCF Analysis** tab
3. Review automatic calculations and metrics
4. Adjust parameters using interactive controls
5. Export results or save to watch list

**Visual Elements:**
- FCF trend charts with multiple years
- Growth rate visualization
- FCF component breakdown
- Comparison with industry benchmarks

### 2. 💰 **DCF Valuation Tab**

#### **Purpose**
Comprehensive Discounted Cash Flow modeling with multiple terminal value methods.

#### **Key Features**

**DCF Model Options:**
- **FCFE Model**: Equity-focused valuation
- **FCFF Model**: Enterprise-wide valuation
- **Custom Parameters**: User-defined assumptions

**Terminal Value Methods:**
- **Perpetual Growth**: Constant growth assumption
- **Exit Multiple**: Multiple-based terminal value
- **H-Model**: Variable growth transition

#### **Workflow**
1. **Model Selection**: Choose DCF approach (FCFE/FCFF)
2. **Projection Setup**: Set forecast period (typically 5-10 years)
3. **Growth Assumptions**: Define revenue and FCF growth rates
4. **Terminal Value**: Select terminal value method and parameters
5. **Discount Rate**: Set or calculate WACC/Cost of Equity
6. **Sensitivity Analysis**: Test key assumptions and scenarios

**Interactive Controls:**
- Growth rate sliders
- Terminal value parameter adjustments
- Discount rate modification
- Scenario comparison toggles

**Output Displays:**
- Intrinsic value per share
- Present value breakdown
- Sensitivity tables and charts
- Valuation range analysis

### 3. 🏆 **DDM Valuation Tab**

#### **Purpose**
Dividend Discount Model analysis with automatic model selection based on dividend patterns.

#### **Key Features**

**DDM Models Available:**
- **Gordon Growth Model**: Single-stage constant growth
- **Two-Stage Model**: High growth then stable growth
- **H-Model**: Gradual transition between growth phases
- **Automatic Selection**: Algorithm chooses optimal model

**Dividend Analysis:**
- Historical dividend trends
- Payout ratio analysis
- Dividend sustainability assessment
- Growth rate calculations

#### **Step-by-Step Usage**
1. **Dividend Data Review**: Examine historical dividend payments
2. **Model Selection**: Choose or accept automatic model recommendation
3. **Parameter Setting**: Define growth rates and required returns
4. **Sustainability Check**: Review dividend coverage ratios
5. **Valuation Results**: Analyze intrinsic value estimates

**Unique Features:**
- Dividend sustainability scoring
- Automatic model recommendation engine
- Risk-adjusted required return calculation
- Historical dividend yield analysis

### 4. 📊 **P/B Analysis Tab**

#### **Purpose**
Price-to-Book ratio analysis with historical trends and industry comparisons.

#### **Key Features**

**P/B Analysis Components:**
- **Historical P/B Trends**: Multi-year ratio analysis
- **Industry Benchmarking**: Peer comparison analysis
- **Fair Value Estimation**: P/B-based intrinsic values
- **Statistical Validation**: Confidence intervals and regression

**Advanced Analytics:**
- **Regression Analysis**: P/B trend significance testing
- **Outlier Detection**: Identification of unusual periods
- **Confidence Intervals**: Statistical validity measures
- **Quality Adjustments**: Book value quality considerations

#### **Usage Workflow**
1. **Historical Analysis**: Review P/B trends over time
2. **Industry Context**: Compare with sector peers
3. **Fair Value Calculation**: Generate P/B-based valuations
4. **Statistical Validation**: Assess reliability of estimates
5. **Investment Implications**: Interpret relative attractiveness

### 5. 🧮 **Financial Ratios Tab**

#### **Purpose**
Comprehensive financial ratio analysis across multiple categories.

#### **Ratio Categories**

**Profitability Ratios:**
- Gross, Operating, and Net Profit Margins
- Return on Assets (ROA) and Return on Equity (ROE)
- Return on Invested Capital (ROIC)

**Liquidity Ratios:**
- Current Ratio and Quick Ratio
- Cash Ratio and Operating Cash Flow Ratio

**Leverage Ratios:**
- Debt-to-Equity and Debt-to-Assets
- Interest Coverage and Debt Service Coverage

**Efficiency Ratios:**
- Asset Turnover and Inventory Turnover
- Receivables Turnover and Working Capital Management

**Valuation Ratios:**
- P/E, P/B, P/S, and EV/EBITDA
- PEG Ratio and Dividend Yield

### 6. 📊 **Financial Trends Tab**

#### **Purpose**
Interactive visualization and trend analysis of key financial metrics.

#### **Visualization Features**
- **Interactive Charts**: Zoom, pan, and filter capabilities
- **Multi-Metric Displays**: Compare multiple ratios simultaneously
- **Trend Lines**: Statistical trend analysis with projections
- **Seasonal Adjustments**: Account for cyclical patterns

### 7. 🔄 **Company Comparison Tab**

#### **Purpose**
Side-by-side comparison of multiple companies across key metrics.

#### **Comparison Features**
- **Multi-Company Analysis**: Compare 2-10 companies simultaneously
- **Standardized Metrics**: Normalized ratios for fair comparison
- **Industry Benchmarking**: Sector-specific comparisons
- **Visual Comparisons**: Charts and tables for easy analysis

---

## Advanced Features

### **Real-Time Data Integration**
- Live stock price updates
- Market data synchronization
- Automated data refresh
- Real-time alerts and notifications

### **Performance Monitoring**
- Calculation performance tracking
- Data source response times
- System resource utilization
- Error rate monitoring

### **Export and Reporting**
- **PDF Reports**: Professional analysis reports
- **Excel Export**: Raw data and calculations
- **CSV Downloads**: Data for external analysis
- **Chart Export**: High-resolution graphics

### **Collaboration Features** (if available)
- **Shared Analysis**: Team collaboration tools
- **Comments and Notes**: Annotation capabilities
- **Version Control**: Track analysis changes
- **Permission Management**: Access control

### **User Preferences**
- **Display Customization**: Themes and layouts
- **Default Parameters**: Preset calculation assumptions
- **Data Source Preferences**: API priority settings
- **Notification Settings**: Alert preferences

---

## Troubleshooting & Best Practices

### **Common Issues**

**Data Loading Problems:**
- Verify Excel file format and structure
- Check API key configuration
- Ensure ticker symbol is valid
- Review file path permissions

**Performance Issues:**
- Clear browser cache
- Reduce analysis timeframe
- Simplify visualizations
- Check system resources

**Calculation Errors:**
- Verify input data quality
- Check for missing financial statements
- Review parameter assumptions
- Validate ticker symbol format

### **Best Practices**

**Data Quality:**
- Use consistent data sources
- Validate key metrics manually
- Cross-reference with multiple sources
- Maintain data version control

**Analysis Workflow:**
- Start with FCF analysis for baseline understanding
- Progress through valuation methods systematically
- Compare results across different models
- Document assumptions and reasoning

**Performance Optimization:**
- Load data once per session
- Use caching for repeated calculations
- Minimize simultaneous analyses
- Regular session state cleanup

---

## Keyboard Shortcuts & Tips

### **Navigation Shortcuts**
- **Tab Navigation**: Use browser tab key to navigate controls
- **Enter**: Execute calculations in input fields
- **Escape**: Close modal dialogs and popups

### **Efficiency Tips**
- **Bookmark Frequently Used Settings**: Save common parameter configurations
- **Use Watch Lists**: Save companies for quick access
- **Export Templates**: Create standardized report formats
- **Batch Processing**: Analyze multiple companies efficiently

---

## Getting Help

### **In-App Resources**
- **Help & Guide Tab**: Comprehensive documentation
- **Tooltips**: Hover over elements for context help
- **Status Indicators**: Visual feedback on data quality and calculations

### **External Resources**
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive technical documentation
- **Community**: User forums and discussion groups

---

*This user guide provides comprehensive coverage of the Streamlit Financial Analysis Platform's capabilities, enabling users to leverage the full power of Phase 2's advanced financial analysis tools.*