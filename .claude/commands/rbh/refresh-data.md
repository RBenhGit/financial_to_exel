# Refresh Financial Data

Clear cache and refresh all financial data from APIs.

**Usage**: `/rbh/refresh-data [symbols]`

## Steps:

1. Clear existing cache
2. Fetch fresh data from financial APIs
3. Update cache with new data
4. Verify data integrity
5. Report updated symbols

## Implementation:

```bash
# Clear cache first
rm -rf data_cache/disk/*.cache

# Run data refresh script (if exists)
python scripts/refresh_data.py

# Or run main app which will fetch fresh data
python main.py --refresh
```

## Arguments:

Optional symbols from $ARGUMENTS (e.g., "AAPL MSFT GOOGL")

## What Gets Refreshed:

- Stock prices
- Fundamental data
- Market data
- Financial statements
- Valuation metrics

## Note:

Be aware of API rate limits when refreshing large amounts of data.
