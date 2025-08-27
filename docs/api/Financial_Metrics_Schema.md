# Financial Metrics Schema - Investment Analysis Project

## Overview
This schema documents all financial metrics used in the investment analysis project located at `C:\AsusWebStorage\ran@benhur.co\MySyncFolder\python\investingAnalysis\financial_to_exel`.

## Core Financial Metrics

| Metric Name | Source of Values | Method | API Sources | Excel Field Names | Calculation/Formula |
|-------------|------------------|--------|-------------|-------------------|---------------------|
| **Operating Cash Flow** | Financial Statements - Cash Flow | Excel, API | Alpha Vantage: `operatingCashflow`, `totalCashFromOperatingActivities`<br>FMP: `operatingCashFlow`, `netCashProvidedByOperatingActivities`<br>YFinance: `Total Cash From Operating Activities`<br>Polygon: `net_cash_flow_from_operating_activities` | Operating Cash Flow, Cash Flow from Operations, Net Cash from Operating Activities | Direct from statements |
| **Capital Expenditures** | Financial Statements - Cash Flow | Excel, API | Alpha Vantage: `capitalExpenditures`, `capitalExpenditure`<br>FMP: `capitalExpenditure`, `purchasesOfPropertyPlantAndEquipment`<br>YFinance: `Capital Expenditures`<br>Polygon: `capital_expenditure`, `capex` | Capital Expenditures, CapEx, Property Plant Equipment | Direct from statements (converted to absolute value) |
| **Free Cash Flow** | Calculated | Excel, API | Calculated from components | free_cash_flow | `operating_cash_flow - abs(capital_expenditures)` |
| **Net Income** | Financial Statements - Income | Excel, API | Alpha Vantage: `netIncome`, `netIncomeFromContinuingOps`<br>FMP: `netIncome`<br>YFinance: `Net Income`, `Net Income Common Stockholders`<br>Polygon: `net_income_loss`, `income_loss_from_continuing_operations_after_tax` | Net Income, Net Earnings | Direct from statements |
| **Total Revenue** | Financial Statements - Income | Excel, API | Alpha Vantage: `totalRevenue`, `revenue`<br>FMP: `revenue`, `totalRevenue`<br>YFinance: `Total Revenue`<br>Polygon: `revenues`, `total_revenue` | Total Revenue, Revenue, Sales | Direct from statements |
| **EBIT** | Financial Statements - Income | Excel, API | Alpha Vantage: `ebit`, `operatingIncome`<br>FMP: `operatingIncome`, `incomeBeforeIncomeTaxes`<br>YFinance: `EBIT`, `Operating Income`<br>Polygon: `operating_income_loss`, `income_loss_from_continuing_operations_before_tax` | EBIT, Operating Income | Direct from statements |
| **EBITDA** | Financial Statements - Income | Excel, API | Alpha Vantage: `ebitda`<br>FMP: `ebitda`<br>YFinance: `EBITDA`<br>Polygon: `ebitda` | EBITDA | Direct from statements or calculated |
| **Total Assets** | Financial Statements - Balance Sheet | Excel, API | Alpha Vantage: `totalAssets`<br>FMP: `totalAssets`<br>YFinance: `Total Assets`<br>Polygon: `assets`, `total_assets` | Total Assets | Direct from statements |
| **Total Liabilities** | Financial Statements - Balance Sheet | Excel, API | Alpha Vantage: `totalLiab`<br>FMP: `totalLiabilities`<br>YFinance: `Total Liabilities Net Minority Interest`<br>Polygon: `liabilities`, `total_liabilities` | Total Liabilities | Direct from statements |
| **Shareholders Equity** | Financial Statements - Balance Sheet | Excel, API | Alpha Vantage: `totalStockholderEquity`, `shareholderEquity`<br>FMP: `totalStockholdersEquity`, `totalEquity`<br>YFinance: `Stockholders Equity`<br>Polygon: `equity`, `stockholders_equity` | Shareholders Equity, Total Equity | Direct from statements |

## Calculated Financial Metrics

| Metric Name | Source of Values | Method | Calculation/Formula | Purpose |
|-------------|------------------|--------|---------------------|---------|
| **FCFE (Free Cash Flow to Equity)** | Calculated | Excel, API | `Net Income + Depreciation - CapEx - Change in Working Capital - Net Debt Payments` | DCF Valuation |
| **FCFF (Free Cash Flow to Firm)** | Calculated | Excel, API | `EBIT(1-Tax Rate) + Depreciation - CapEx - Change in Working Capital` | DCF Valuation |
| **LFCF (Levered Free Cash Flow)** | Calculated | Excel, API | `Operating Cash Flow - Capital Expenditures` | Traditional FCF Analysis |
| **Book Value per Share** | Calculated | Excel, API | `Shareholders' Equity / Shares Outstanding` | P/B Ratio Analysis |
| **P/B Ratio** | Calculated | API | `Market Price per Share / Book Value per Share` | Valuation Analysis |
| **Market Capitalization** | Calculated | API | `Share Price × Shares Outstanding` | Market Valuation |

## Composite Variable Breakdowns

### Free Cash Flow Calculation Components
Based on the actual formulas used in the project:

#### FCFE (Free Cash Flow to Equity) Components
| Component | Source | Calculation | Purpose |
|-----------|--------|-------------|---------|
| **Net Income** | Income Statement | Direct from statements | Starting point for equity FCF |
| **Depreciation** | Cash Flow Statement or calculated | Non-cash expense add-back | Restore non-cash charges |
| **Capital Expenditures** | Cash Flow Statement | Direct from statements (absolute value) | Cash outflow for investments |
| **Change in Working Capital** | Balance Sheet derived | `Working Capital(Current) - Working Capital(Previous)` | Impact of working capital changes |
| **Net Debt Payments** | Cash Flow Statement | `Debt Repayments - New Debt Issuance` | Net cash flow from debt activities |

#### FCFF (Free Cash Flow to Firm) Components  
| Component | Source | Calculation | Purpose |
|-----------|--------|-------------|---------|
| **EBIT(1-Tax Rate)** | Income Statement + Tax Rate | `EBIT × (1 - Tax Rate)` | After-tax operating income |
| **Depreciation** | Cash Flow Statement or calculated | Non-cash expense add-back | Restore non-cash charges |
| **Capital Expenditures** | Cash Flow Statement | Direct from statements (absolute value) | Cash outflow for investments |
| **Change in Working Capital** | Balance Sheet derived | `Working Capital(Current) - Working Capital(Previous)` | Impact of working capital changes |

#### LFCF (Levered Free Cash Flow) Components
| Component | Source | Calculation | Purpose |
|-----------|--------|-------------|---------|
| **Operating Cash Flow** | Cash Flow Statement | Direct from statements | Cash generated from operations |
| **Capital Expenditures** | Cash Flow Statement | Direct from statements (absolute value) | Cash outflow for investments |

### Working Capital Components (Used in FCFE & FCFF)
| Component | Source | Calculation | Purpose |
|-----------|--------|-------------|---------|
| **Working Capital** | Balance Sheet | `Current Assets - Current Liabilities` | Short-term liquidity measure |
| **Change in Working Capital** | Calculated | `Working Capital(Current) - Working Capital(Previous)` | Period-over-period change impact |

## Valuation Model Metrics

### DCF (Discounted Cash Flow) Model
| Metric Name | Source | Method | Purpose |
|-------------|--------|--------|---------|
| **Discount Rate** | Configuration/User Input | Excel, API | Cost of equity for valuation |
| **Terminal Growth Rate** | Configuration/User Input | Excel, API | Long-term growth assumption |
| **Growth Rate (Years 1-5)** | Calculated/User Input | Excel, API | Near-term growth projection |
| **Growth Rate (Years 5-10)** | Calculated/User Input | Excel, API | Medium-term growth projection |
| **Terminal Value** | Calculated | Excel, API | Gordon Growth Model calculation |
| **Present Value** | Calculated | Excel, API | NPV of projected cash flows |

### DDM (Dividend Discount Model) Metrics
| Metric Name | Source | Method | Purpose |
|-------------|--------|--------|---------|
| **Dividend per Share** | API (YFinance primary) | API | Historical dividend payments |
| **Dividend Growth Rate** | Calculated | API | Historical dividend growth analysis |
| **Dividend Yield** | Calculated | API | Annual dividend / share price |
| **Payout Ratio** | Calculated | API | Dividends / Net Income |

### P/B (Price-to-Book) Analysis Metrics
| Metric Name | Source | Method | Purpose |
|-------------|--------|--------|---------|
| **Industry P/B Median** | External/Configuration | API | Industry benchmarking |
| **Historical P/B Range** | Calculated | API | 5-year P/B trend analysis |
| **P/B Percentile Ranking** | Calculated | API | Position within historical range |

## Market Data Metrics

| Metric Name | Source | Method | API Sources | Purpose |
|-------------|--------|--------|-------------|---------|
| **Stock Price** | Real-time/Historical | API | YFinance (primary), Alpha Vantage, FMP, Polygon | Current valuation |
| **Shares Outstanding** | Financial Statements | API | All sources | Market cap calculation |
| **Trading Volume** | Market Data | API | YFinance, Alpha Vantage, Polygon | Liquidity analysis |
| **52-Week High/Low** | Market Data | API | YFinance, Alpha Vantage | Price range analysis |

## Data Quality and Validation Metrics

| Metric Name | Purpose | Validation Rules |
|-------------|---------|------------------|
| **Data Completeness** | Ensure all required fields present | Min 3 years of data required |
| **Data Consistency** | Cross-validate between sources | Variance threshold checks |
| **Trend Validation** | Validate logical progression | Growth rate reasonableness |
| **Ratio Validation** | Ensure ratios within reasonable bounds | Industry-specific thresholds |

## Data Source Priority and Configuration

### Source Priority (1 = Highest)
1. **YFinance** - Primary source for market data and basic financials
2. **Alpha Vantage & FMP** - Secondary sources for comprehensive financials
3. **Polygon** - Tertiary source for additional validation
4. **Excel** - Manual input/backup source (Priority 4)

### API Configuration Details
- **Alpha Vantage**: 500 calls/month limit, 5 calls/minute
- **FMP**: 250 calls/month limit, 250 calls/hour  
- **Polygon**: 1000 calls/month limit, 5 calls/minute
- **YFinance**: Unlimited (free), rate-limited by server

### Cache Settings
- **YFinance**: 2 hours TTL
- **Alpha Vantage**: 24 hours TTL
- **FMP**: 12 hours TTL
- **Polygon**: 6 hours TTL
- **Excel**: 48 hours TTL

## File Locations and Data Structure

### Key Configuration Files
- `field_mappings.json` - API field mapping definitions
- `data_sources_config.json` - API credentials and settings
- `config.py` - Application configuration and defaults

### Data Storage Structure
- `/data/` - Watch lists and portfolio data
- `/MSFT/`, `/NVDA/`, `/TSLA/`, etc. - Company-specific analysis files
- `/data_cache/` - API response caching
- `/exports/` - Generated reports and analysis

### Supported Exchanges
- **US Markets**: NYSE, NASDAQ (via all APIs)
- **TASE (Tel Aviv)**: Supported via YFinance with `.TA` suffix
- **International**: Limited support via YFinance

## Usage Patterns

### Excel Method
- Financial statements loaded from company-specific folders
- Manual data entry and validation
- Offline analysis capability
- Used as backup/validation source

### API Method  
- Real-time data fetching from multiple sources
- Automatic field mapping and normalization
- Intelligent fallback between sources
- Comprehensive data validation

### Hybrid Approach
- Excel data for historical/audited statements
- API data for current market information
- Cross-validation between sources
- Enhanced data quality assurance