# Financial API Diagnostic Report
Generated on: 2025-07-25 16:26:49

## Executive Summary
- APIs tested: yfinance
- Total API calls: 5
- Successful calls: 5
- Success rate: 100.0%

## YFINANCE API Results
- Endpoints tested: 5
- Successful: 5
- Success rate: 100.0%

### history - ✅ SUCCESS
- Response time: 5.71s
- Data completeness: complete

### info - ✅ SUCCESS
- Response time: 0.33s
- Data completeness: complete

### financials - ✅ SUCCESS
- Response time: 0.30s
- Data completeness: complete

### balance_sheet - ✅ SUCCESS
- Response time: 0.34s
- Data completeness: partial
- Missing fields: Total Stockholder Equity

### cashflow - ✅ SUCCESS
- Response time: 2.27s
- Data completeness: partial
- Missing fields: Capital Expenditures

## ALPHA_VANTAGE API Results
- No results (API not tested or unavailable)

## FMP API Results
- No results (API not tested or unavailable)

## Field Availability Matrix
| Field | yfinance | Alpha Vantage | FMP |
|-------|----------|---------------|-----|
| market_cap | ✅ | ❌ | ❌ |
| pe_ratio | ✅ | ❌ | ❌ |
| pb_ratio | ✅ | ❌ | ❌ |
| dividend_yield | ✅ | ❌ | ❌ |
| eps | ✅ | ❌ | ❌ |
| revenue | ✅ | ❌ | ❌ |
| profit_margin | ✅ | ❌ | ❌ |
| beta | ✅ | ❌ | ❌ |
| sector | ✅ | ❌ | ❌ |
| industry | ✅ | ❌ | ❌ |

## Recommendations
- All APIs are functioning well. Continue monitoring for any changes.