# Financial Analysis Tool - Enterprise Edition

## Overview
This comprehensive financial analysis platform provides enterprise-grade tools for **Free Cash Flow (FCF) analysis**, **Discounted Cash Flow (DCF) valuation**, and **multi-source data integration** for both **US Market** and **TASE (Tel Aviv Stock Exchange)** stocks.

### 🚀 **Core Capabilities**
- **Multi-Source Data Integration**: Yahoo Finance, Alpha Vantage, Financial Modeling Prep, and Polygon.io APIs
- **Advanced FCF Analysis**: Multiple calculation methods with unified algorithms
- **Professional DCF Valuation**: 10-year projections with sensitivity analysis
- **Market Intelligence**: US Market and TASE support with currency-aware analysis
- **Portfolio Management**: Watch lists with performance tracking and analytics
- **Enterprise Features**: Rate limiting, cost management, usage tracking, and caching

### 🏗️ **System Architecture**
- **Modern Web Interface**: Streamlit-based responsive application
- **Unified Data Adapter**: Smart fallback system across multiple APIs
- **Financial Calculation Engine**: Standardized FCF/DCF algorithms
- **Data Quality Validation**: Multi-layered validation and normalization
- **Professional Reporting**: PDF generation with market-specific formatting

## 🚀 **Quick Start Guide**

### **Option 1: API Mode (Recommended)**
```bash
# 1. Install and launch
pip install -r requirements.txt
streamlit run fcf_analysis_streamlit.py

# 2. Configure API sources (optional for enhanced data)
python configure_api_keys.py

# 3. In web interface:
#    - Select "🌐 Ticker Mode (API Data)"
#    - Choose US Market or TASE (Tel Aviv)
#    - Enter ticker symbol (e.g., AAPL, MSFT, TEVA)
#    - Select preferred data source (Auto or Manual)
#    - Click "Load Company Data"
```

### **Option 2: Excel Mode (Traditional)**
```bash
# 1. Prepare folder structure
mkdir COMPANY_NAME
mkdir COMPANY_NAME/FY COMPANY_NAME/LTM

# 2. Export financial statements to folders
# 3. In web interface:
#    - Select "📁 Folder Mode (Excel Files)"
#    - Choose market and load company folder
```

### **🎯 Data Source Selection**
The system provides intelligent data source selection:

- **Auto Mode**: Tries sources in priority order (Yahoo Finance → Alpha Vantage/FMP → Polygon.io)
- **Manual Mode**: Choose your preferred API source
- **Source Tracking**: See exactly which API provided your data
- **Smart Fallback**: Automatic failover if preferred source fails

## 📊 **Analysis Modules & Features**

### **🔄 Data Integration Engine**
- **`unified_data_adapter.py`**: Core adapter with smart fallback across 4+ data sources
- **`enhanced_data_manager.py`**: Extends legacy systems with multi-API support
- **`data_sources.py`**: Provider implementations (Alpha Vantage, FMP, Polygon, Yahoo Finance)
- **`data_source_manager.py`**: Configuration, testing, and monitoring tools
- **Field Converters**: `alpha_vantage_converter.py`, `fmp_converter.py`, `polygon_converter.py`, `yfinance_converter.py`

### **💰 Financial Analysis Core**
- **`financial_calculations.py`**: Unified FCF calculation engine with multiple methodologies
- **`fcf_consolidated.py`**: Advanced FCF calculations with growth rate analysis
- **`dcf_valuation.py`**: Professional DCF valuation with 10-year projections
- **`field_normalizer.py`**: Data standardization across different API formats

### **📈 Advanced Analytics**
- **`analysis_capture.py`**: Performance analysis and benchmarking tools
- **`watch_list_manager.py`**: Portfolio tracking and watch list management
- **`watch_list_visualizer.py`**: Interactive charts and portfolio analytics

### **🎨 User Interface**
- **`fcf_analysis_streamlit.py`**: Main web application with modern responsive design
- **`report_generator.py`**: Professional PDF report generation
- **Multiple analysis tabs**: FCF Analysis, DCF Valuation, Reports, Watch Lists, Help

### **🔧 Configuration & Management**
- **`configure_api_keys.py`**: Interactive API configuration wizard
- **`config.py`**: Application settings and preferences
- **`input_validator.py`**: Multi-level data validation
- **`error_handler.py`**: Comprehensive error handling and logging

### **🧪 Testing & Quality Assurance**
- **`test_alternative_data_sources.py`**: API integration testing
- **`test_e2e_api_integration.py`**: End-to-end workflow validation
- **`test_fcf_accuracy.py`**: FCF calculation verification
- **`test_streamlit_integration.py`**: UI functionality testing
- **`test_tase_support.py`**: TASE market-specific testing

## 🌐 **API Data Sources**

### **Supported Providers**
| Provider | Free Tier | Features | Status |
|----------|-----------|----------|---------|
| **Yahoo Finance** | Unlimited | Price, fundamentals, financials | ✅ Always Available |
| **Alpha Vantage** | 25 calls/day | Complete financials, real-time data | ✅ Configured |
| **Financial Modeling Prep** | 250 calls/day | Premium fundamentals, ratios | ✅ Configured |
| **Polygon.io** | 5 calls/min | High-quality institutional data | ✅ Configured |

### **Data Source Management**
```bash
# View current configuration
python data_source_manager.py report

# Test all sources
python data_source_manager.py test --ticker AAPL

# Configure new API keys
python configure_api_keys.py

# Check usage limits
python data_source_manager.py limits
```

## 📈 **Available Analysis Types**

### **🔥 Free Cash Flow (FCF) Analysis**
The system supports **5 different FCF calculation methodologies**:

1. **FCFF (Free Cash Flow to Firm)**
   - `Operating Cash Flow - Capital Expenditures`
   - Most commonly used for enterprise valuation

2. **FCFE (Free Cash Flow to Equity)**  
   - `FCFF - Net Borrowing - Interest Expense`
   - Used for equity valuation

3. **LFCF (Levered Free Cash Flow)**
   - `Net Income + Depreciation - CapEx - Working Capital Change`
   - Alternative equity-focused calculation

4. **UFCF (Unlevered Free Cash Flow)**
   - `EBIT(1-Tax Rate) + Depreciation - CapEx - Working Capital Change`
   - Pure business cash generation

5. **OCF-Based FCF**
   - `Operating Cash Flow - Capital Expenditures`
   - Direct from cash flow statement

### **💰 DCF Valuation Models**
- **10-Year Projection Model** with terminal value
- **Sensitivity Analysis** across discount rates and growth assumptions
- **Multiple Growth Scenarios** (3-year, 5-year, terminal)
- **Enterprise and Equity Value** calculations
- **Per-Share Fair Value** with confidence intervals

### **📊 Portfolio Analytics** 
- **Watch List Management** with real-time tracking
- **Performance Metrics** and comparative analysis  
- **Risk Assessment** and portfolio optimization
- **Market Correlation** and beta analysis

### **🌍 Market Support**
- **US Market**: Full support for NYSE, NASDAQ stocks
- **TASE (Tel Aviv)**: Comprehensive Israeli market support
- **Currency Handling**: USD, ILS, Agorot with smart conversion
- **Ticker Processing**: Automatic .TA suffix for TASE stocks

## ⚙️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+ (Recommended: Python 3.9-3.11)
- 4GB+ RAM for large financial datasets
- Internet connection for API data sources

### **Quick Installation**
```bash
# 1. Clone or download the project
git clone <repository-url>
cd financial_to_exel

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys (optional but recommended)
python configure_api_keys.py

# 5. Launch application
streamlit run fcf_analysis_streamlit.py
```

### **Environment Configuration**
Create a `.env` file for additional configuration:
```bash
# Optional: Set default export directory
DEFAULT_EXPORT_DIR=./exports

# Optional: Set cache directory
CACHE_DIR=./data_cache

# Optional: Set log level
LOG_LEVEL=INFO
```

### **API Configuration**
The system works with Yahoo Finance out of the box. For enhanced features, configure additional APIs:

```bash
# Interactive configuration wizard
python configure_api_keys.py

# Manual configuration: Edit data_sources_config.json
{
  "sources": {
    "alpha_vantage": {
      "credentials": {
        "api_key": "YOUR_ALPHA_VANTAGE_KEY"
      }
    }
  }
}
```

## 🛠️ **Troubleshooting**

### **Quick Fixes for Common Issues**

| Issue | Solution |
|-------|----------|
| **Streamlit won't start** | `python -m streamlit run fcf_analysis_streamlit.py` |
| **No API sources available** | Run `python configure_api_keys.py` |
| **FCF calculation fails** | Check ticker symbol and market selection |
| **Rate limit exceeded** | Check usage with `python data_source_manager.py limits` |
| **Excel files not found** | Verify exact file names: "Income Statement.xlsx", etc. |
| **Charts not displaying** | Clear browser cache (Ctrl+Shift+R) |

### **Debug Commands**
```bash
# Test data sources
python data_source_manager.py test --ticker AAPL

# Check API configuration
python configure_api_keys.py

# View detailed logs
ls data_cache/logs/

# Validate installation
python -c "import streamlit, pandas, yfinance; print('✓ All modules imported')"
```

For detailed troubleshooting, see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md).

## 📚 **Documentation**

- **[API Reference](./API_REFERENCE.md)**: Complete programmatic API documentation
- **[Troubleshooting Guide](./TROUBLESHOOTING.md)**: Solutions for common issues
- **[API Configuration Guide](./API_CONFIGURATION_GUIDE.md)**: Detailed setup instructions
- **[Alternative Data Sources Guide](./ALTERNATIVE_DATA_SOURCES_GUIDE.md)**: Provider comparisons

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