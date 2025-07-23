# 📊 Watch Lists - Complete User Guide

## Overview

The Watch Lists feature transforms the FCF Analysis Tool from a single-company calculator into a comprehensive portfolio management and analysis platform. It provides automatic capture of DCF analysis results with powerful visualization and export capabilities.

---

## 🎯 Key Features

### 📋 **Multi-List Management**
- Create unlimited watch lists for different investment themes
- Organize stocks by sector, strategy, or any custom criteria
- Track description and creation dates for each list

### 🔄 **Automatic Analysis Capture**
- DCF results automatically saved when analysis capture is enabled
- Complete audit trail of all valuations over time
- No manual data entry required

### 📈 **Advanced Visualization**
- Interactive upside/downside bar charts with performance indicators
- Performance distribution histograms
- Historical trend analysis for individual stocks
- Color-coded performance categories

### 📥 **Flexible Export Options**
- Current view export (latest analysis per stock)
- Complete historical data export (all analyses)
- Individual stock history export
- Multiple CSV format options

---

## 🚀 Getting Started

### Step 1: Create Your First Watch List
1. Navigate to the **📊 Watch Lists** tab
2. Go to **📋 Manage Lists** sub-tab
3. Enter a descriptive name (e.g., "Tech Growth Stocks", "Value Plays", "High Dividend")
4. Add an optional description
5. Click **Create Watch List**

### Step 2: Enable Analysis Capture
1. Go to **⚙️ Capture Settings** sub-tab
2. Select your newly created watch list as active
3. Click **✅ Enable Capture**
4. Your watch list is now ready to automatically capture DCF analyses

### Step 3: Run DCF Analyses
1. Perform DCF analyses as usual in the **💰 DCF Valuation** tab
2. Results are automatically captured to your active watch list
3. Each new analysis for the same stock updates the current valuation
4. Historical data is preserved in the database

---

## 📊 Understanding View Modes

### 🎯 **Latest Analysis Only** (Default)
- Shows the most recent valuation for each stock
- Perfect for current portfolio decision-making
- Eliminates duplicate entries in charts and tables
- **Best for**: Daily monitoring, quick performance overview

### 📚 **All Historical Data**
- Shows every analysis ever captured for all stocks
- Reveals valuation changes over time
- Enables trend analysis and historical comparison
- **Best for**: Research, tracking valuation evolution

---

## 📈 Visualization Features

### 🎨 **Performance Bar Chart**
- **Green bars**: Undervalued stocks (positive upside)
- **Red bars**: Overvalued stocks (negative upside)
- **Reference lines**: -20%, -10%, 0%, +10%, +20% thresholds
- **Hover details**: Complete stock information on mouseover

### 📊 **Investment Categories**
- **Strong Buy**: >20% upside potential
- **Buy**: 10-20% upside potential  
- **Hold**: -10% to +10% (fairly valued)
- **Sell**: -10% to -20% downside
- **Strong Sell**: >20% overvalued

### 📈 **Historical Trends** (Historical View Only)
- Time series charts showing valuation changes
- Individual stock trend analysis
- Multi-stock comparison capabilities
- Trend identification for timing decisions

---

## 💾 Export Capabilities

### 📥 **Current View Export**
```
Exports: Latest analysis for each stock
Format: CSV with current valuations
Use case: Share current portfolio positions
Filename: WatchListName_current.csv
```

### 📊 **Full History Export**  
```
Exports: Complete analysis history for all stocks
Format: CSV with timestamps and evolution
Use case: Research, backtesting, audit trails
Filename: WatchListName_full_history_YYYYMMDD_HHMMSS.csv
```

### 📈 **Individual Stock History**
```
Exports: Complete timeline for selected stock
Format: CSV with all historical analyses
Use case: Deep dive into specific stock valuation changes
Filename: WatchListName_TICKER_history_YYYYMMDD_HHMMSS.csv
```

---

## ⚙️ Advanced Features

### 🔄 **Analysis Replacement Logic**
- New DCF analysis for existing stock **replaces** it in graphical view
- Original analysis **preserved** in database for historical reference
- Ticker column shows analysis count: "AAPL (3 analyses)" 
- Switch to "All Historical Data" to see complete timeline

### 📊 **Performance Metrics**
- **Total Stocks**: Number of unique stocks in watch list
- **Average Upside/Downside**: Mean performance across portfolio
- **Undervalued/Overvalued Counts**: Distribution of opportunities
- **Category Breakdown**: Strong Buy/Buy/Hold/Sell/Strong Sell counts

### 🎯 **Multi-List Strategy Examples**
```
• "High Growth Tech" - Growth stocks with >15% revenue growth
• "Dividend Aristocrats" - Stable dividend payers
• "Value Opportunities" - Low P/E with strong fundamentals  
• "International Exposure" - Non-US market stocks
• "Watchlist - Research" - Stocks under investigation
```

---

## 🛠️ Best Practices

### 📋 **List Organization**
- Use descriptive, specific names for watch lists
- Create separate lists for different investment strategies
- Regularly review and update list descriptions
- Delete unused lists to maintain organization

### 🔄 **Analysis Workflow**
1. Set active watch list before starting analysis sessions
2. Enable capture to automatically save results
3. Review captured data in "Latest Analysis Only" mode
4. Use "All Historical Data" for research and trends
5. Export data regularly for backup and sharing

### 📊 **Performance Review Schedule**
- **Weekly**: Check performance summary metrics
- **Monthly**: Review category distributions and rebalance
- **Quarterly**: Analyze historical trends for timing patterns
- **Annually**: Export full history for tax and reporting purposes

---

## 🚨 Important Notes

### 💾 **Data Persistence**
- All data stored in local SQLite database (`data/watch_lists.db`)
- JSON backup maintained (`data/watch_lists.json`)
- Data survives application restarts and updates
- Regular backups recommended for important data

### 🔒 **Data Privacy**
- All data stored locally on your machine
- No cloud synchronization or external sharing
- Complete control over your analysis data
- Export functionality for manual backup/sharing

### ⚡ **Performance Considerations**
- Optimized SQL queries for fast data retrieval
- Efficient storage of large historical datasets
- Responsive interface even with 100+ stocks per list
- Automatic indexing for ticker and date searches

---

## 🆘 Troubleshooting

### ❌ **Analysis Not Capturing**
1. Verify watch list is set as active in Capture Settings
2. Ensure analysis capture is enabled (green status)
3. Complete DCF analysis fully before expecting capture
4. Check that company folder is properly loaded

### 📊 **Charts Not Displaying**
1. Verify watch list contains analysis data
2. Try switching between Latest/Historical view modes
3. Refresh browser if using web interface
4. Check for JavaScript errors in browser console

### 📥 **Export Issues**
1. Ensure `exports/` directory has write permissions
2. Check available disk space for CSV files
3. Try individual stock export if full export fails
4. Verify watch list contains data before exporting

---

## 💡 Pro Tips

### 🎯 **Efficient Workflow**
- Create watch lists **before** starting analysis sessions
- Use keyboard shortcuts for faster navigation between tabs
- Keep capture enabled for consistent data collection
- Review performance metrics regularly for portfolio insights

### 📊 **Advanced Analysis**
- Compare multiple watch lists for sector analysis
- Use historical view to identify seasonal patterns
- Export data to Excel for additional calculations
- Track changes in discount rates and assumptions over time

### 🔄 **Maintenance**
- Periodically clean up test or experimental watch lists
- Update watch list descriptions as strategies evolve
- Export historical data before major application updates
- Monitor database size and export old data if needed

---

## 📝 Data Formats

### **Watch List Export CSV Columns**
```
Current View Export:
- Ticker: Stock symbol with analysis count
- Company: Company name
- Current Price: Latest market price ($)
- Fair Value: DCF calculated fair value ($)
- Upside/Downside: Percentage difference (%)
- Discount Rate: DCF discount rate (%)
- FCF Type: FCFE/FCFF/LFCF
- Analysis Date: Date of analysis (YYYY-MM-DD)

Historical Export (Additional):
- Analysis Date: Full timestamp with time
- All historical records for each stock
```

### **Database Schema**
```sql
watch_lists:
- id, name, description, created_date, updated_date

analysis_records:
- id, watch_list_id, ticker, company_name, analysis_date
- current_price, fair_value, discount_rate, terminal_growth_rate
- upside_downside_pct, fcf_type, dcf_assumptions, analysis_metadata
```

---

*The Watch Lists feature transforms your investment analysis workflow from individual stock evaluation to comprehensive portfolio management. Start with one watch list and expand your system as your investment process grows!*

---

## Quick Reference Card

### Essential Commands
- **Create Watch List**: Watch Lists → Manage Lists → Enter name → Create
- **Enable Capture**: Watch Lists → Capture Settings → Select list → Enable
- **Switch Views**: Watch Lists → View Analysis → Latest/Historical toggle
- **Export Current**: Watch Lists → View Analysis → Download Current View
- **Export History**: Watch Lists → View Analysis → Export Full History

### Key Shortcuts
- Latest view = Clean portfolio overview
- Historical view = Research and trends
- Analysis count in ticker = Multiple valuations exist
- Green bars = Undervalued opportunities
- Red bars = Overvalued warnings