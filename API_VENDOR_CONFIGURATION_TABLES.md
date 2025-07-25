# API Vendor Configuration Tables for Financial Data Sources

## Overview
This document provides comprehensive configuration tables for each API vendor, including endpoint mappings, parameter mappings, rate limits, and implementation requirements for DCF calculations.

---

## 1. Alpha Vantage API Configuration

### **Basic Information**
| Property | Value |
|----------|--------|
| **Base URL** | `https://www.alphavantage.co/query` |
| **API Key** | `XN0J1H61WY80Y6GX` |
| **Status** | ✅ Active & Configured |
| **Free Tier** | 25 calls/day, 5 calls/minute |
| **Documentation** | https://www.alphavantage.co/documentation/ |

### **Financial Statement Endpoints**
| Statement Type | Function Parameter | DCF Data Available | Implementation Status |
|----------------|-------------------|-------------------|---------------------|
| **Income Statement** | `INCOME_STATEMENT` | ✅ Full | ❌ Not Implemented |
| **Balance Sheet** | `BALANCE_SHEET` | ✅ Full | ❌ Not Implemented |
| **Cash Flow** | `CASH_FLOW` | ✅ Full | ❌ Not Implemented |
| **Company Overview** | `OVERVIEW` | ✅ Partial | ✅ Implemented |

### **API Endpoint Structure**
```
https://www.alphavantage.co/query?function={FUNCTION}&symbol={TICKER}&apikey={API_KEY}
```

### **DCF Parameter Mapping**
| DCF Required | Alpha Vantage Field | Data Type | Statement |
|--------------|-------------------|-----------|-----------|
| **EBIT** | `ebit` | Number | Income |
| **Net Income** | `netIncome` | Number | Income |
| **Income Tax Expense** | `incomeTaxExpense` | Number | Income |
| **EBT** | `incomeBeforeTax` | Number | Income |
| **Total Current Assets** | `totalCurrentAssets` | Number | Balance |
| **Total Current Liabilities** | `totalCurrentLiabilities` | Number | Balance |
| **Total Debt** | `totalShareholderEquity` | Number | Balance |
| **Cash & Cash Equivalents** | `cashAndCashEquivalentsAtCarryingValue` | Number | Balance |
| **Operating Cash Flow** | `operatingCashflow` | Number | Cash Flow |
| **Capital Expenditure** | `capitalExpenditures` | Number | Cash Flow |
| **Depreciation & Amortization** | `depreciationDepletionAndAmortization` | Number | Cash Flow |

### **Rate Limiting Configuration**
| Parameter | Value |
|-----------|--------|
| **Rate Limit** | 5 calls/minute |
| **Daily Limit** | 25 calls/day |
| **Monthly Limit** | 500 calls/month |
| **Cost per Call** | $0.00 (Free) |
| **Timeout** | 30 seconds |
| **Retry Attempts** | 3 |

### **Data Quality & Coverage**
| Metric | Value |
|--------|--------|
| **Historical Years** | 20+ years |
| **Reporting Periods** | Annual & Quarterly |
| **Data Freshness** | 1-2 days after earnings |
| **Quality Score** | 0.8/1.0 |
| **Reliability** | High |

### **Implementation Requirements**
```python
# Missing implementation needed in AlphaVantageProvider.fetch_data():
elif data_type == 'income_statement':
    income_data = self._fetch_income_statement(request.ticker, request.period)
elif data_type == 'balance_sheet':
    balance_data = self._fetch_balance_sheet(request.ticker, request.period)
elif data_type == 'cash_flow':
    cashflow_data = self._fetch_cash_flow(request.ticker, request.period)
```

---

## 2. Financial Modeling Prep (FMP) API Configuration

### **Basic Information**
| Property | Value |
|----------|--------|
| **Base URL** | `https://financialmodelingprep.com/api/v3` |
| **API Key** | `MrOambcgnMbbgAkZXaMfRWCaDGEedGdl` |
| **Status** | ✅ Active & Configured |
| **Free Tier** | 250 calls/day |
| **Documentation** | https://financialmodelingprep.com/developer/docs |

### **Financial Statement Endpoints**
| Statement Type | Endpoint | DCF Data Available | Implementation Status |
|----------------|----------|-------------------|---------------------|
| **Income Statement** | `/income-statement/{ticker}` | ✅ Full | ❌ Not Implemented |
| **Balance Sheet** | `/balance-sheet-statement/{ticker}` | ✅ Full | ❌ Not Implemented |
| **Cash Flow** | `/cash-flow-statement/{ticker}` | ✅ Full | ❌ Not Implemented |
| **Company Profile** | `/profile/{ticker}` | ✅ Partial | ✅ Implemented |

### **API Endpoint Structure**
```
https://financialmodelingprep.com/api/v3/{ENDPOINT}/{TICKER}?limit={LIMIT}&apikey={API_KEY}
```

### **DCF Parameter Mapping**
| DCF Required | FMP Field | Data Type | Statement |
|--------------|-----------|-----------|-----------|
| **EBIT** | `operatingIncome` | Number | Income |
| **Net Income** | `netIncome` | Number | Income |
| **Income Tax Expense** | `incomeTaxExpense` | Number | Income |
| **EBT** | `incomeBeforeTax` | Number | Income |
| **Total Current Assets** | `totalCurrentAssets` | Number | Balance |
| **Total Current Liabilities** | `totalCurrentLiabilities` | Number | Balance |
| **Total Debt** | `totalDebt` | Number | Balance |
| **Cash & Cash Equivalents** | `cashAndCashEquivalents` | Number | Balance |
| **Operating Cash Flow** | `operatingCashFlow` | Number | Cash Flow |
| **Capital Expenditure** | `capitalExpenditure` | Number | Cash Flow |
| **Depreciation & Amortization** | `depreciationAndAmortization` | Number | Cash Flow |

### **Rate Limiting Configuration**
| Parameter | Value |
|-----------|--------|
| **Rate Limit** | 250 calls/hour |
| **Daily Limit** | 250 calls/day |
| **Monthly Limit** | 250 calls/month |
| **Cost per Call** | $0.00 (Free) |
| **Timeout** | 30 seconds |
| **Retry Attempts** | 3 |

### **Data Quality & Coverage**
| Metric | Value |
|--------|--------|
| **Historical Years** | 30+ years |
| **Reporting Periods** | Annual & Quarterly |
| **Data Freshness** | Same day as filing |
| **Quality Score** | 0.85/1.0 |
| **Reliability** | Very High |

### **Implementation Requirements**
```python
# Missing implementation needed in FinancialModelingPrepProvider.fetch_data():
elif data_type == 'income_statement':
    income_data = self._fetch_income_statement(request.ticker, request.period, request.limit)
elif data_type == 'balance_sheet':
    balance_data = self._fetch_balance_sheet(request.ticker, request.period, request.limit)
elif data_type == 'cash_flow':
    cashflow_data = self._fetch_cash_flow(request.ticker, request.period, request.limit)
```

---

## 3. Polygon.io API Configuration

### **Basic Information**
| Property | Value |
|----------|--------|
| **Base URL** | `https://api.polygon.io` |
| **API Key** | `[Not Configured]` |
| **Status** | ❌ Inactive (No API Key) |
| **Free Tier** | 5 calls/minute |
| **Documentation** | https://polygon.io/docs |

### **Financial Statement Endpoints**
| Statement Type | Endpoint | DCF Data Available | Implementation Status |
|----------------|----------|-------------------|---------------------|
| **Financials** | `/vX/reference/financials` | ✅ Limited | ❌ Not Implemented |
| **Company Details** | `/v3/reference/tickers/{ticker}` | ✅ Partial | ✅ Implemented |

### **API Endpoint Structure**
```
https://api.polygon.io/{ENDPOINT}?ticker={TICKER}&apikey={API_KEY}
```

### **DCF Parameter Mapping**
| DCF Required | Polygon Field | Data Type | Statement |
|--------------|---------------|-----------|-----------|
| **EBIT** | `operating_income` | Number | Financials |
| **Net Income** | `net_income_loss` | Number | Financials |
| **Revenue** | `revenues` | Number | Financials |
| **Total Assets** | `assets` | Number | Financials |
| **Operating Cash Flow** | `net_cash_flow_from_operating_activities` | Number | Financials |

### **Rate Limiting Configuration**
| Parameter | Value |
|-----------|--------|
| **Rate Limit** | 5 calls/minute |
| **Daily Limit** | 1000 calls/day |
| **Monthly Limit** | 1000 calls/month |
| **Cost per Call** | $0.003 |
| **Timeout** | 30 seconds |
| **Retry Attempts** | 3 |

### **Data Quality & Coverage**
| Metric | Value |
|--------|--------|
| **Historical Years** | 10+ years |
| **Reporting Periods** | Annual & Quarterly |
| **Data Freshness** | Real-time |
| **Quality Score** | 0.9/1.0 |
| **Reliability** | Excellent |

### **Implementation Requirements**
```python
# Implementation needed - requires API key first
# Limited financial statement coverage compared to others
```

---

## 4. Yahoo Finance (yfinance) Configuration

### **Basic Information**
| Property | Value |
|----------|--------|
| **Library** | `yfinance` Python package |
| **API Key** | Not required |
| **Status** | ✅ Active |
| **Rate Limits** | ~5 calls/minute (unofficial) |
| **Documentation** | https://pypi.org/project/yfinance/ |

### **Financial Statement Access**
| Statement Type | yfinance Property | DCF Data Available | Implementation Status |
|----------------|------------------|-------------------|---------------------|
| **Income Statement** | `stock.income_stmt` | ✅ Full | ✅ Available |
| **Balance Sheet** | `stock.balance_sheet` | ✅ Full | ✅ Available |
| **Cash Flow** | `stock.cashflow` | ✅ Full | ✅ Available |
| **Info/Fundamentals** | `stock.info` | ✅ Extensive | ✅ Available |

### **DCF Parameter Mapping**
| DCF Required | yfinance Field | Data Type | Statement |
|--------------|----------------|-----------|-----------|
| **EBIT** | `EBIT` or `Normalized EBITDA` | Number | Income |
| **Net Income** | `Net Income From Continuing Operation Net Minority Interest` | Number | Income |
| **Tax Provision** | `Tax Provision` | Number | Income |
| **Pretax Income** | `Pretax Income` | Number | Income |
| **Current Assets** | `Total Non Current Assets` | Number | Balance |
| **Current Liabilities** | `Total Non Current Liabilities Net Minority Interest` | Number | Balance |
| **Total Debt** | `Total Debt` | Number | Balance |
| **Cash** | `Cash Cash Equivalents And Short Term Investments` | Number | Balance |
| **Operating Cash Flow** | `Operating Cash Flow` | Number | Cash Flow |
| **Capital Expenditure** | `Capital Expenditure` | Number | Cash Flow |
| **Depreciation** | `Depreciation Amortization Depletion` | Number | Cash Flow |

### **Rate Limiting Configuration**
| Parameter | Value |
|-----------|--------|
| **Rate Limit** | ~5 calls/minute |
| **Daily Limit** | Unlimited (with delays) |
| **Cost per Call** | $0.00 (Free) |
| **Timeout** | Variable |
| **Retry Logic** | Built-in |

### **Data Quality & Coverage**
| Metric | Value |
|--------|--------|
| **Historical Years** | 5+ years |
| **Reporting Periods** | Annual |
| **Data Freshness** | 1-2 days |
| **Quality Score** | 0.8/1.0 |
| **Reliability** | Good (with rate limiting) |

### **Implementation Status**
```python
# ✅ Already accessible directly:
import yfinance as yf
stock = yf.Ticker("AAPL")
income_stmt = stock.income_stmt      # Pandas DataFrame
balance_sheet = stock.balance_sheet  # Pandas DataFrame  
cash_flow = stock.cashflow          # Pandas DataFrame
```

---

## Summary Table: API Vendor Comparison

| Vendor | API Key Required | Financial Statements | DCF Coverage | Rate Limit | Cost | Status |
|--------|------------------|---------------------|--------------|------------|------|---------|
| **Alpha Vantage** | ✅ XN0J1H61WY80Y6GX | ✅ Full (3 endpoints) | 100% | 25/day | Free | ❌ Not Implemented |
| **Financial Modeling Prep** | ✅ MrOambcgnMbbgAkZXaMfRWCaDGEedGdl | ✅ Full (3 endpoints) | 100% | 250/day | Free | ❌ Not Implemented |
| **Polygon.io** | ❌ No Key | ✅ Limited (1 endpoint) | 60% | 5/min | $0.003/call | ❌ Not Implemented |
| **yfinance** | ❌ Not Required | ✅ Full (Built-in) | 100% | ~5/min | Free | ✅ Available |

## Priority Implementation Order
1. **yfinance** - Already available, just needs integration
2. **Financial Modeling Prep** - Highest quality, already configured  
3. **Alpha Vantage** - Good coverage, already configured
4. **Polygon.io** - Requires API key setup first

The API infrastructure is in place with proper authentication, but the financial statement endpoint implementations are missing from the provider classes.