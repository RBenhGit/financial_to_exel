# Financial API Diagnostic Report
Generated on: 2025-09-16 09:19:19

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
- Response time: 0.74s
- Data completeness: complete

### info - ✅ SUCCESS
- Response time: 0.47s
- Data completeness: complete

### financials - ✅ SUCCESS
- Response time: 0.33s
- Data completeness: complete

### balance_sheet - ✅ SUCCESS
- Response time: 0.35s
- Data completeness: partial
- Missing fields: Total Stockholder Equity

### cashflow - ✅ SUCCESS
- Response time: 0.32s
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