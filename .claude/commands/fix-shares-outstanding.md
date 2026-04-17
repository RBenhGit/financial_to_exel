Audit and fix "Shares Outstanding: Not available" across all API sources in Ticker Mode.

## Problem

`create_ticker_mode_calculator` in `fcf_analysis_streamlit.py` always fetches market data
(price + shares) from yfinance, regardless of which financial data source the user selected.
If yfinance doesn't return `sharesOutstanding` in its `.info` dict (common for dual-class
shares like GOOG, some international tickers, or transient API issues), `calculator.shares_outstanding`
is set to 0 and the UI shows "Shares Outstanding: Not available", blocking DCF calculations.

## Architecture

The general fix has two parts, both already implemented:

### 1. `_extract_shares_from_statements(source, income_data, balance_data)`
Standalone helper (~line 1544 in `fcf_analysis_streamlit.py`) that extracts shares
from the raw API response records using each source's own field names:

```python
SHARE_FIELDS = {
    'fmp':           {'income':  ['weightedAverageShsOut', 'weightedAverageShsOutDil']},
    'alpha_vantage': {'balance': ['commonStockSharesOutstanding']},
    'twelve_data':   {'income':  ['basic_shares_outstanding', 'diluted_shares_outstanding']},
}
```

All supported APIs return records **newest-first**; `records[0]` is always the most recent.

### 2. Wiring in `create_ticker_mode_calculator`
Each `if/elif` block for a source saves its raw records:
```python
_raw_income_data, _raw_balance_data = income_data, balance_data
```

After setting `shares_outstanding = market_data.get('shares_outstanding', 0)`, the
fallback is applied if shares are still missing:
```python
if not shares_outstanding and preferred_source:
    shares_outstanding = _extract_shares_from_statements(
        preferred_source, _raw_income_data, _raw_balance_data
    )
calculator.shares_outstanding = shares_outstanding
```

## Audit Steps

1. **Find all API source blocks** in `create_ticker_mode_calculator`:
   ```
   Grep for: `elif preferred_source ==` in fcf_analysis_streamlit.py
   ```

2. **Check each source has raw data capture**:
   Every block that successfully unpacks `income_data, balance_data, cashflow_data = result`
   must also set `_raw_income_data, _raw_balance_data = income_data, balance_data`.

3. **Check `SHARE_FIELDS` covers every source**:
   Every source key in `source_type_mapping` or handled by an `elif preferred_source ==` block
   must appear in `SHARE_FIELDS` with the correct statement type and field name(s).
   - To find a new source's field name: check the API docs or grep the fetch/convert functions
     for the word "share" or "shares".

4. **Verify the fallback wiring** is still present after the `if not financial_data:` yfinance block.

## Adding a New API Source

When a new source is added (e.g., `polygon_statements`):

1. Identify which statement contains shares and what the field is called:
   ```
   Grep for shares/share in the new _fetch_* and _convert_* functions
   ```

2. Add an entry to `SHARE_FIELDS` in `_extract_shares_from_statements`:
   ```python
   'new_source': {'income': ['shares_field_name']},
   ```

3. In the new `elif preferred_source == 'new_source':` block, add after unpacking:
   ```python
   _raw_income_data, _raw_balance_data = income_data, balance_data
   ```

No other changes needed — the fallback wiring is source-agnostic.

## Key Files

- `fcf_analysis_streamlit.py` — `create_ticker_mode_calculator` (~line 1280),
  `_extract_shares_from_statements` (~line 1544)
