# Financial Analysis Tool - Troubleshooting Guide

## 🚨 **Common Issues & Solutions**

### **Installation & Setup Issues**

#### **Issue: Package Installation Fails**
```bash
ERROR: pip install -r requirements.txt fails
```

**Solutions:**
```bash
# 1. Update pip first
python -m pip install --upgrade pip

# 2. Use virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Install packages individually if requirements.txt fails
pip install streamlit pandas numpy yfinance requests plotly

# 4. For Windows compilation issues
pip install --only-binary=all -r requirements.txt
```

#### **Issue: Streamlit Won't Start**
```bash
ERROR: Command 'streamlit' not found
```

**Solutions:**
```bash
# 1. Verify streamlit installation
pip show streamlit

# 2. Run with python module
python -m streamlit run fcf_analysis_streamlit.py

# 3. Check PATH and virtual environment
which streamlit  # Linux/Mac
where streamlit  # Windows

# 4. Reinstall streamlit
pip uninstall streamlit
pip install streamlit
```

### **Data Source Issues**

#### **Issue: "No Data Sources Available"**
The UI shows only Yahoo Finance or no sources.

**Diagnosis:**
```bash
# Check data sources configuration
python -c "
from enhanced_data_manager import create_enhanced_data_manager
manager = create_enhanced_data_manager()
sources = manager.get_available_data_sources()
print(sources)
"
```

**Solutions:**
```bash
# 1. Configure API keys
python configure_api_keys.py

# 2. Check configuration file
cat data_sources_config.json

# 3. Verify API key format
# Alpha Vantage: 16 characters (e.g., XN0J1H61WY80Y6GX)
# FMP: 32+ characters 
# Polygon: 32+ characters

# 4. Test individual sources
python data_source_manager.py test --ticker AAPL
```

#### **Issue: API Rate Limiting**
```bash
ERROR: API rate limit exceeded
```

**Solutions:**
```bash
# 1. Check current usage
python data_source_manager.py limits

# 2. Wait for rate limit reset
# Alpha Vantage: 5 calls/minute, 500/month
# FMP: 250 calls/month
# Polygon: 5 calls/minute

# 3. Configure rate limiting
# Edit data_sources_config.json:
{
  "credentials": {
    "rate_limit_calls": 3,  # Reduce from 5
    "rate_limit_period": 60
  }
}

# 4. Use cache to reduce API calls
# System automatically caches for 2-24 hours depending on source
```

#### **Issue: Invalid API Key**
```bash
ERROR: API authentication failed
```

**Solutions:**
```bash
# 1. Verify API key validity
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"

# 2. Check key in configuration
python configure_api_keys.py
# Select option 5 to show current status

# 3. Get new API keys:
# Alpha Vantage: https://www.alphavantage.co/support/#api-key
# FMP: https://financialmodelingprep.com/developer/docs
# Polygon: https://polygon.io/

# 4. Reconfigure source
python configure_api_keys.py
```

### **Analysis & Calculation Issues**

#### **Issue: "No FCF Data Calculated"**
FCF analysis returns empty results.

**Diagnosis:**
```python
# Check financial data structure
from financial_calculations import FinancialCalculator
calc = FinancialCalculator("./COMPANY_FOLDER")
print("Financial data keys:", calc.financial_data.keys())
```

**Solutions:**
1. **For Excel Mode:**
   ```bash
   # Verify folder structure
   ls -la COMPANY_FOLDER/
   # Should have: FY/ and LTM/ folders
   
   # Check Excel files
   ls -la COMPANY_FOLDER/FY/
   ls -la COMPANY_FOLDER/LTM/
   # Should have: Income Statement.xlsx, Balance Sheet.xlsx, Cash Flow Statement.xlsx
   ```

2. **For API Mode:**
   ```python
   # Test ticker data availability
   import yfinance as yf
   ticker = yf.Ticker("AAPL")
   print("Info available:", bool(ticker.info))
   print("Cashflow available:", not ticker.cashflow.empty)
   ```

3. **Field Mapping Issues:**
   ```python
   # Check field mappings
   from field_normalizer import FieldNormalizer
   normalizer = FieldNormalizer()
   
   # Test specific source
   normalized = normalizer.normalize(raw_data, source_type="alpha_vantage")
   print("Normalized fields:", normalized.keys())
   ```

#### **Issue: DCF Valuation Fails**
```bash
ERROR: Cannot calculate DCF - missing required data
```

**Solutions:**
```python
# Check required fields for DCF
required_fields = [
    'current_stock_price',
    'shares_outstanding', 
    'fcf_results'  # At least one FCF type
]

# Verify each field
calculator = FinancialCalculator("./folder")
for field in required_fields:
    value = getattr(calculator, field, None)
    print(f"{field}: {value}")

# Manual override if needed
calculator.current_stock_price = 150.0  # Set manually
calculator.shares_outstanding = 15000000000  # Set manually
```

#### **Issue: Incorrect Currency/Market Detection**
TASE stocks show USD instead of ILS, or vice versa.

**Solutions:**
```python
# 1. Verify market selection in UI
# Make sure "TASE (Tel Aviv)" is selected for Israeli stocks

# 2. Check ticker processing
from fcf_analysis_streamlit import _apply_market_selection_to_ticker
processed = _apply_market_selection_to_ticker("TEVA", "TASE (Tel Aviv)")
print(f"Processed ticker: {processed}")  # Should be "TEVA.TA"

# 3. Manual currency override
calculator.is_tase_stock = True
calculator.currency = 'ILS'
calculator.financial_currency = 'ILS'
```

### **Performance Issues**

#### **Issue: Slow Data Loading**
Application takes a long time to load data.

**Solutions:**
```bash
# 1. Check network connectivity
ping www.alphavantage.co
ping financialmodelingprep.com

# 2. Enable caching (automatic)
# Data is cached for 2-24 hours depending on source

# 3. Use faster data sources
# Order of speed: Yahoo Finance > Alpha Vantage > FMP > Polygon

# 4. Reduce data scope
# In API mode, only request necessary data types
request = FinancialDataRequest(
    ticker="AAPL",
    data_types=['price'],  # Remove 'fundamentals' if not needed
    force_refresh=False  # Use cache when available
)
```

#### **Issue: High Memory Usage**
Application uses too much RAM.

**Solutions:**
```python
# 1. Enable cleanup
from enhanced_data_manager import create_enhanced_data_manager
manager = create_enhanced_data_manager()
# ... use manager ...
manager.cleanup()  # Always call cleanup

# 2. Limit batch operations
# Process companies one at a time instead of batch loading

# 3. Clear session state in Streamlit
# Use st.rerun() after major operations to clear memory
```

### **File & Folder Issues**

#### **Issue: "Folder Not Found" Error**
```bash
ERROR: Company folder does not exist
```

**Solutions:**
```bash
# 1. Check exact path
ls -la "/full/path/to/company/folder"

# 2. Use absolute paths
# Instead of: ./AAPL
# Use: /full/path/to/AAPL

# 3. Check permissions
chmod 755 COMPANY_FOLDER

# 4. Use forward slashes even on Windows
# Instead of: C:\data\AAPL
# Use: C:/data/AAPL
```

#### **Issue: Excel File Reading Errors**
```bash
ERROR: Could not read Excel file
```

**Solutions:**
```bash
# 1. Verify file format
file COMPANY_FOLDER/FY/Income Statement.xlsx
# Should show: Microsoft Excel 2007+

# 2. Check file names (case sensitive)
# Required exact names:
# - Income Statement.xlsx
# - Balance Sheet.xlsx  
# - Cash Flow Statement.xlsx

# 3. Verify file integrity
# Open files in Excel to ensure they're not corrupted

# 4. Check file permissions
chmod 644 *.xlsx
```

### **UI & Display Issues**

#### **Issue: Charts Not Displaying**
Plotly charts show as blank or don't render.

**Solutions:**
```bash
# 1. Update plotly
pip install --upgrade plotly

# 2. Clear browser cache
# In browser: Ctrl+Shift+R (hard refresh)

# 3. Check JavaScript console for errors
# Browser Developer Tools > Console

# 4. Try different browser
# Test in Chrome, Firefox, Safari
```

#### **Issue: Currency Symbols Not Displaying**
₪ or $ symbols show as boxes or question marks.

**Solutions:**
```bash
# 1. Check system locale
locale  # Linux/Mac
# Windows: Control Panel > Region

# 2. Update font support
# Install Unicode fonts

# 3. Browser encoding
# Ensure UTF-8 encoding in browser

# 4. Terminal encoding (for CLI tools)
export LANG=en_US.UTF-8
```

### **Watch List Issues**

#### **Issue: Watch List Data Not Updating**
Watch list shows stale prices or "N/A" values.

**Solutions:**
```python
# 1. Force refresh watch list data
from watch_list_manager import WatchListManager
manager = WatchListManager()
updated_list = manager.refresh_watchlist_data(watchlist_id, force_update=True)

# 2. Check data source connectivity
python data_source_manager.py test --ticker AAPL

# 3. Verify tickers in watch list
# Ensure ticker symbols are correct (e.g., TEVA.TA for TASE stocks)

# 4. Clear cache
rm -rf data_cache/  # Remove cache directory
```

### **Export & Reporting Issues**

#### **Issue: PDF Report Generation Fails**
```bash
ERROR: Could not generate PDF report
```

**Solutions:**
```bash
# 1. Install missing dependencies
pip install reportlab matplotlib

# 2. Check output directory permissions
mkdir -p exports
chmod 755 exports

# 3. Verify chart rendering
# Test if charts display in UI first

# 4. Check font availability
# Install system fonts for PDF generation
```

#### **Issue: Excel Export Issues**
```bash
ERROR: Could not export to Excel
```

**Solutions:**
```bash
# 1. Install Excel support
pip install openpyxl xlsxwriter

# 2. Close any open Excel files
# Ensure target Excel file is not open

# 3. Check file permissions
chmod 644 output.xlsx

# 4. Use different export location
# Try exporting to different directory
```

## 🔧 **Advanced Debugging**

### **Enable Debug Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# For specific modules
logging.getLogger('unified_data_adapter').setLevel(logging.DEBUG)
logging.getLogger('data_sources').setLevel(logging.DEBUG)
```

### **Test Individual Components**
```python
# Test data adapter
from unified_data_adapter import UnifiedDataAdapter
adapter = UnifiedDataAdapter()
response = adapter.fetch_data(FinancialDataRequest(ticker="AAPL"))
print(f"Success: {response.success}")

# Test financial calculations
from financial_calculations import FinancialCalculator
calc = FinancialCalculator("./test_folder")
results = calc.calculate_all_fcf_types()
print(f"FCF Results: {list(results.keys())}")

# Test API providers individually
from data_sources import AlphaVantageProvider
provider = AlphaVantageProvider(config)
test_response = provider.fetch_data(request)
```

### **Check System Resources**
```bash
# Check disk space
df -h

# Check memory usage
free -h  # Linux
# Windows: Task Manager > Performance

# Check network connectivity
ping google.com
nslookup financialmodelingprep.com
```

### **Validate Configuration Files**
```python
import json

# Check JSON syntax
with open('data_sources_config.json', 'r') as f:
    try:
        config = json.load(f)
        print("✓ Configuration file is valid JSON")
    except json.JSONDecodeError as e:
        print(f"✗ JSON Error: {e}")

# Check required fields
required_sources = ['alpha_vantage', 'fmp', 'polygon', 'yfinance']
for source in required_sources:
    if source in config.get('sources', {}):
        print(f"✓ {source} configuration found")
    else:
        print(f"✗ {source} configuration missing")
```

## 🆘 **Getting Help**

### **Log Collection**
When reporting issues, collect these logs:

```bash
# 1. System information
python --version
pip list | grep -E "(streamlit|pandas|yfinance|plotly)"

# 2. Configuration status
python configure_api_keys.py
# Select option 5 (Show current status)

# 3. Test results
python data_source_manager.py test --ticker AAPL > test_results.txt

# 4. Application logs
# Check data_cache/logs/ directory for detailed logs

# 5. Error reproduction
# Provide exact steps to reproduce the issue
```

### **Common Error Patterns**

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `ModuleNotFoundError: No module named 'xyz'` | Missing dependency | `pip install xyz` |
| `JSON decode error` | Corrupted config file | Delete and reconfigure |
| `API rate limit exceeded` | Too many API calls | Wait or reduce frequency |
| `File not found` | Incorrect path | Use absolute paths |
| `Permission denied` | File permissions | `chmod 755` directory |
| `No data retrieved` | Network/API issue | Check connectivity |
| `FCF calculation failed` | Missing financial data | Verify data source |
| `Chart not displaying` | Browser/JavaScript issue | Try different browser |

### **Performance Optimization**

```python
# 1. Use caching effectively
# Data is automatically cached, but you can control TTL:
config.cache_ttl_hours = 24  # Cache for 24 hours

# 2. Batch operations efficiently
tickers = ["AAPL", "MSFT", "GOOGL"]
for ticker in tickers:
    # Process one at a time to avoid memory issues
    analyze_company(ticker)
    
# 3. Cleanup resources
manager.cleanup()  # Always cleanup when done

# 4. Use specific data types
request = FinancialDataRequest(
    ticker="AAPL",
    data_types=['price'],  # Only get what you need
    force_refresh=False   # Use cache when possible
)
```

---

**Still having issues?** 

1. Check the project's GitHub issues page
2. Review the API documentation (`API_REFERENCE.md`)
3. Ensure you're using the latest version of all components
4. Try the analysis with a known working ticker (e.g., AAPL) first