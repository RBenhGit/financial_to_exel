# Real-Time Price Service - User Guide

## 📈 Overview

The Real-Time Price Service provides live stock price data from multiple financial API sources with intelligent caching, fallback mechanisms, and seamless Streamlit integration.

## 🚀 Features

### Multi-Source Data Fetching
- **🟢 yfinance (Primary)** - Free and reliable for most stocks
- **🟡 Alpha Vantage (Secondary)** - Professional grade data with API key
- **🟠 Financial Modeling Prep (Tertiary)** - Comprehensive financial data  
- **🔴 Polygon.io (Fallback)** - High-quality market data

### Smart Caching System
- **⏰ 15-minute cache** by default to reduce API calls
- **🔄 Manual refresh** option to get latest prices
- **💾 Persistent storage** survives app restarts
- **📊 Cache status** indicators show data freshness

### Key Capabilities
- 🚀 **Concurrent fetching** for multiple tickers
- 🔄 **Automatic fallback** when primary sources fail
- 📈 **Real-time updates** with change indicators
- 💰 **Market cap** and **volume** information
- 📱 **Mobile-friendly** responsive design

## 🛠️ Setup & Configuration

### Environment Variables

Set up API keys in your environment or `.env` file:

```bash
# Optional - for enhanced data sources
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FMP_API_KEY=your_fmp_key_here  
POLYGON_API_KEY=your_polygon_key_here

# yfinance works without API keys
```

### Installation

The service is automatically available when the following files are present:
- `core/data_sources/real_time_price_service.py`
- `core/data_sources/price_service_integration.py`

## 📊 Using the Real-Time Prices Tab

### Basic Usage

1. **Navigate to Real-Time Prices Tab**
   - Launch the Streamlit app: `python run_streamlit_app.py`
   - Click on the "📈 Real-Time Prices" tab

2. **Add Tickers to Watch List**
   - Enter ticker symbols (comma-separated): `AAPL, MSFT, GOOGL`
   - Click "➕ Add" to add to your watch list
   - Remove tickers with the "❌" button

3. **View Live Prices**
   - Prices update automatically with 15-minute caching
   - Use "🔄 Refresh Prices" for latest data
   - Green/Red indicators show price changes

### Advanced Features

#### Watch List Integration
- **Select existing watch lists** from dropdown
- **Automatic price fetching** for watch list tickers
- **CSV download** of current prices with timestamps

#### Cache Management
- **View cache status** - entries, size, freshness
- **Clear cache** to force fresh API calls  
- **Refresh cache** to update all cached data

## 🔧 Integration with Existing Features

### Watch List Analysis Enhancement

The service integrates with the existing Watch Lists tab:

1. **In Watch Lists → View Analysis**
2. **Enable "📊 Show Real-Time Prices"** checkbox
3. **Current market prices** display alongside analysis
4. **Real-time price table** with refresh capability

### Programmatic Usage

```python
# Simple price fetching
from core.data_sources.price_service_integration import get_current_price_simple

price = get_current_price_simple("AAPL")
print(f"AAPL: ${price:.2f}")

# Multiple prices
prices = get_current_prices_simple(["AAPL", "MSFT", "GOOGL"])
for ticker, price in prices.items():
    if price:
        print(f"{ticker}: ${price:.2f}")
```

### Async Usage

```python
import asyncio
from core.data_sources.real_time_price_service import get_current_price

async def fetch_prices():
    price = await get_current_price("AAPL", force_refresh=True)
    return price

price = asyncio.run(fetch_prices())
```

## 📋 API Reference

### Core Classes

#### `RealTimePriceService`
Main service class for price fetching with caching and fallback logic.

```python
service = RealTimePriceService(cache_ttl_minutes=15)

# Get single price
price_data = await service.get_real_time_price("AAPL")

# Get multiple prices  
prices = await service.get_multiple_prices(["AAPL", "MSFT"])

# Cache management
service.clear_cache("AAPL")  # Clear specific ticker
service.clear_cache()       # Clear all cache
```

#### `StreamlitPriceIntegration`
Streamlit-specific integration utilities.

```python
integration = StreamlitPriceIntegration()

# Sync methods for Streamlit
price_data = integration.get_single_price_sync("AAPL")
prices = integration.get_prices_sync(["AAPL", "MSFT"])

# UI components
integration.display_price_table(tickers)
integration.display_price_metrics("AAPL")
```

### Data Structures

#### `PriceData`
```python
@dataclass
class PriceData:
    ticker: str
    current_price: float
    change_percent: float = 0.0
    volume: int = 0
    market_cap: float = 0.0
    timestamp: datetime = None
    source: str = "unknown"
    currency: str = "USD"
    last_updated: datetime = None
    cache_hit: bool = False
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_price_service.py
```

The test suite covers:
- ✅ Module imports
- ✅ Synchronous wrapper functions
- ✅ Asynchronous functions  
- ✅ RealTimePriceService class
- ✅ Streamlit integration components
- ✅ Caching functionality
- ✅ Multiple data source fallback

## 🔧 Troubleshooting

### Common Issues

#### "Real-time price service is not available"
- **Cause**: Module import failed
- **Solution**: Ensure all required files are present and dependencies installed

#### "No providers initialized"  
- **Cause**: No API keys configured and yfinance import failed
- **Solution**: Install yfinance: `pip install yfinance`

#### Slow price fetching
- **Cause**: API rate limiting or network issues
- **Solution**: Enable caching, check internet connection, verify API keys

#### Cache not working
- **Cause**: Insufficient disk permissions or corrupted cache files
- **Solution**: Check write permissions to `data/cache/prices/` directory

### Data Source Troubleshooting

| Source | Issue | Solution |
|--------|--------|----------|
| yfinance | Import error | `pip install yfinance` |
| Alpha Vantage | Invalid API key | Check `ALPHA_VANTAGE_API_KEY` environment variable |
| FMP | Rate limit exceeded | Check API key limits, enable caching |
| Polygon | 401 Unauthorized | Verify `POLYGON_API_KEY` is valid |

## 📈 Performance Optimization

### Caching Best Practices
- **Use default 15-minute cache** for most use cases
- **Force refresh sparingly** to avoid hitting API limits  
- **Clear cache selectively** rather than full clears
- **Monitor cache status** to optimize performance

### API Usage Optimization
- **Set up multiple API keys** for redundancy
- **Monitor API call usage** to avoid limits
- **Use concurrent fetching** for multiple tickers
- **Enable persistent caching** for better performance

## 🔄 Updates & Maintenance

### Cache Maintenance
- Cache automatically expires after TTL
- Persistent cache files stored in `data/cache/prices/`
- Manual cleanup via UI or `clear_cache()` method

### API Key Rotation
- Update environment variables
- Restart Streamlit app to pick up new keys
- Test with `test_price_service.py`

### Monitoring
- Check cache status regularly via UI
- Monitor API call usage to avoid limits
- Review logs for error patterns

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Run the test suite to identify specific problems
3. Review logs for detailed error messages
4. Ensure all dependencies are installed and API keys are configured

---

*This service integrates seamlessly with the existing FCF Analysis toolkit while providing modern, efficient real-time price data capabilities.*