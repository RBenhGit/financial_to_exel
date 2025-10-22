# Clear Data Cache

Clear cached financial data and force fresh data retrieval.

**Usage**: `/rbh/clear-cache [type]`

## Steps:

1. Identify cache directories
2. Remove cached files safely
3. Confirm cache clearing
4. Optionally preserve specific cache types

## Implementation:

```bash
# Clear disk cache
rm -rf data_cache/disk/*.cache

# Clear JSON price cache
rm -rf data/cache/prices/*.json

# Clear all cache
rm -rf data_cache/
rm -rf data/cache/
```

## Cache Types (optional argument):

- `disk` - Clear disk cache only (data_cache/disk/)
- `prices` - Clear price cache only (data/cache/prices/)
- `all` - Clear all caches (default)

## Examples:

```bash
/rbh/clear-cache           # Clear everything
/rbh/clear-cache disk      # Clear disk cache only
/rbh/clear-cache prices    # Clear price data only
```

## Safety:

- Only removes .cache and .json files
- Preserves directory structure
- Creates backup before clearing (optional)
