# API Configuration Guide

## Current Issue Status

✅ **FIXED**: Ticker mode now continues to FCF Analysis tab.

The issue where ticker mode displayed ticker price and shares outstanding but didn't continue to the FCF Analysis tab has been resolved. The app now properly shows all analysis tabs when using ticker mode.

## How to Configure API Keys

Your system currently has 3 alternative data sources available, but they're disabled because no API keys are configured:

### Current Status:
- **ALPHA_VANTAGE**: [DISABLED] | [NO KEY]
- **FMP**: [DISABLED] | [NO KEY]  
- **POLYGON**: [DISABLED] | [NO KEY]

### 1. Alpha Vantage (Recommended for Free Tier)

**Get API Key**: https://www.alphavantage.co/support/#api-key
- **Free Tier**: 25 requests/day, 5 requests/minute
- **Best for**: Basic financial data and market quotes

**To Configure**:
1. Get your free API key from Alpha Vantage
2. Edit `data_sources_config.json` 
3. Find the `alpha_vantage` section
4. Replace `"api_key": ""` with `"api_key": "YOUR_API_KEY"`
5. Change `"is_enabled": false` to `"is_enabled": true`

Example:
```json
"alpha_vantage": {
  "priority": 2,
  "is_enabled": true,
  "credentials": {
    "api_key": "YOUR_ALPHA_VANTAGE_KEY_HERE"
  }
}
```

### 2. Financial Modeling Prep (Best Features)

**Get API Key**: https://financialmodelingprep.com/developer/docs
- **Free Tier**: 250 requests/day
- **Best for**: Comprehensive financial statements and ratios

**To Configure**:
```json
"fmp": {
  "priority": 2, 
  "is_enabled": true,
  "credentials": {
    "api_key": "YOUR_FMP_KEY_HERE"
  }
}
```

### 3. Polygon.io (Real-time Data)

**Get API Key**: https://polygon.io/
- **Free Tier**: 5 requests/minute
- **Best for**: Real-time market data

**To Configure**:
```json
"polygon": {
  "priority": 3,
  "is_enabled": true, 
  "credentials": {
    "api_key": "YOUR_POLYGON_KEY_HERE"
  }
}
```

## Quick Setup (Recommended)

1. **Run the configuration script**:
   ```bash
   python configure_api_keys.py
   ```

2. **Or manually edit the config file**:
   - Open `data_sources_config.json`
   - Add your API keys to the `"api_key"` fields
   - Change `"is_enabled": false` to `"is_enabled": true`

3. **Test your configuration**:
   ```bash
   python configure_api_keys.py
   # Choose option 4 to test all sources
   ```

## Data Source Priority

The system tries data sources in this order:
1. **YFinance** (Priority 1) - Free, no API key needed
2. **Alpha Vantage/FMP** (Priority 2) - With API keys
3. **Polygon** (Priority 3) - With API key  
4. **Excel Files** (Priority 4) - Local files as fallback

## Testing Your Setup

After configuring API keys, test with:

```bash
streamlit run fcf_analysis_streamlit.py
```

1. Select "Ticker Mode"
2. Enter a stock symbol (e.g., AAPL)
3. You should now see:
   - Market data (price, shares outstanding)
   - **FCF Analysis tab** (this was the original issue - now fixed!)
   - All other analysis tabs

## Troubleshooting

### Issue: "Ticker mode doesn't continue to FCF Analysis tab"
**Status**: ✅ **FIXED** - This was a bug in the tab visibility logic that has been resolved.

### Issue: "Want to use alternative data sources"
**Solution**: Configure API keys as shown above. The system will automatically use the best available source.

### Issue: "API calls failing"
**Check**:
1. API key is correct
2. API key has remaining quota
3. Internet connection is working
4. Run the test configuration script

## Cost Management

All recommended providers have generous free tiers:
- **Alpha Vantage**: 25 requests/day (sufficient for personal use)
- **FMP**: 250 requests/day (very generous)
- **Polygon**: 5 requests/minute (good for real-time needs)

The system automatically caches data to minimize API usage.

## Next Steps

1. ✅ Ticker mode FCF issue is fixed
2. 📊 Configure API keys for enhanced data sources (optional)
3. 🚀 Start analyzing stocks with ticker mode

The core functionality works with just YFinance (no API key needed). API keys are only needed for enhanced features and alternative data sources.