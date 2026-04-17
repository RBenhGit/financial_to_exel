# Add New API Data Source

Integrate a new financial data API into the system following the established architecture.

## Architecture Overview

The system has three layers for each API source:
1. **Converter** (`core/data_processing/converters/`) — maps raw API fields → standard field names
2. **Adapter** (`core/data_processing/adapters/`) — fetches data from the API, uses the Converter
3. **Provider** (`core/data_sources/interfaces/data_sources.py`) — integrates with the unified data manager

## Step-by-Step Process

### Step 1 — Create the Converter

Create `core/data_processing/converters/{api_name}_converter.py`:

```python
from typing import Any, Dict, List, Optional
from .base_converter import BaseConverter
import logging

logger = logging.getLogger(__name__)

class {ApiName}Converter(BaseConverter):
    """Converts {ApiName} API responses to standardized format."""

    # Map API field names → project standard field names (snake_case)
    FIELD_MAPPINGS = {
        "apiFieldName": "standard_field_name",
        # ... all API fields
    }

    @classmethod
    def convert_financial_data(cls, api_data: Dict[str, Any]) -> Dict[str, Any]:
        if not api_data:
            return {}
        try:
            converted = {}
            for api_field, value in api_data.items():
                standard_name = cls.FIELD_MAPPINGS.get(api_field, api_field)
                normalized = cls._normalize_value(value)
                if normalized is not None:
                    converted[standard_name] = normalized
            return cls._build_standard_result(converted, "{api_name}")
        except Exception as exc:
            logger.error(f"{ApiName}Converter.convert_financial_data error: {exc}")
            return {}

    @classmethod
    def extract_cash_flow_data(cls, api_data: Any) -> Dict[str, Optional[float]]:
        result = {
            "operating_cash_flow": None,
            "capital_expenditures": None,
            "free_cash_flow": None,
            "source": "{api_name}",
        }
        if not api_data:
            return result
        try:
            converted = cls.convert_financial_data(api_data)
            result["operating_cash_flow"] = converted.get("operating_cash_flow")
            result["capital_expenditures"] = converted.get("capital_expenditures")
            result["free_cash_flow"] = converted.get("free_cash_flow")
            # Derive FCF if components available but direct value missing
            if result["free_cash_flow"] is None:
                ocf = result["operating_cash_flow"]
                capex = result["capital_expenditures"]
                if ocf is not None and capex is not None:
                    result["free_cash_flow"] = ocf - abs(capex)
        except Exception as exc:
            logger.error(f"{ApiName}Converter.extract_cash_flow_data error: {exc}")
        return result

    @classmethod
    def get_supported_fields(cls) -> List[str]:
        return sorted(set(cls.FIELD_MAPPINGS.values()))
```

**Checklist for the converter:**
- [ ] Inherits from `BaseConverter`
- [ ] `FIELD_MAPPINGS` covers all major fields: `operating_cash_flow`, `capital_expenditures`, `net_income`, `total_revenue`, `total_assets`, `total_liabilities`, `total_stockholder_equity`
- [ ] `convert_financial_data()` uses `_normalize_value()` for all numeric fields
- [ ] `extract_cash_flow_data()` returns dict with all three FCF keys
- [ ] `get_supported_fields()` returns sorted list of standard field names
- [ ] `_build_standard_result()` called to add `source` and `converted_at` metadata

### Step 2 — Create the Adapter

Create `core/data_processing/adapters/{api_name}_adapter.py` following the pattern of `fmp_adapter.py`.

Key requirements:
- Inherits from `BaseApiAdapter`
- Reads API key from environment variable `{API_NAME}_API_KEY`
- Implements `load_symbol_data(ticker, historical_years)` 
- Uses the converter: `from ..converters.{api_name}_converter import {ApiName}Converter`
- Implements `get_capabilities()` returning `ApiCapabilities`
- Provides module-level helpers: `load_{api_name}_data()`, `check_{api_name}_availability()`, `get_{api_name}_adapter_stats()`

### Step 3 — Register the Converter in `__init__.py`

Add to `core/data_processing/converters/__init__.py`:
```python
from .{api_name}_converter import {ApiName}Converter
```
And add `"{ApiName}Converter"` to `__all__`.

### Step 4 — Register the Adapter in `__init__.py`

Add to `core/data_processing/adapters/__init__.py`:
```python
from .{api_name}_adapter import (
    {ApiName}Adapter,
    load_{api_name}_data,
    check_{api_name}_availability,
    get_{api_name}_adapter_stats,
)
```
Update module docstring and `__all__`.

### Step 5 — Register as a DataSourceType

In `core/data_sources/interfaces/data_sources.py`, add to the `DataSourceType` enum:
```python
{API_NAME_UPPER} = "{api_name_lower}"
```

### Step 6 — Create the Provider

In `core/data_sources/interfaces/data_sources.py`, add a new provider class:

```python
class {ApiName}Provider(FinancialDataProvider):
    """Provider for {ApiName} API."""

    def __init__(self, config: DataSourceConfig) -> None:
        super().__init__(config)
        self.base_url = "https://api.{apiname}.com"

    def validate_credentials(self) -> bool:
        if not self.config.credentials or not self.config.credentials.api_key:
            return False
        try:
            # Make a lightweight test call
            response = self._session.get(
                f"{self.base_url}/test",
                params={"apikey": self.config.credentials.api_key},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        response = DataSourceResponse(success=False, source_type=DataSourceType.{API_NAME_UPPER})
        start_time = datetime.now()
        try:
            self._enforce_rate_limit()
            data: Dict[str, Any] = {}

            if "financial_statements" in request.data_types:
                statements = self._fetch_financial_statements(request.ticker)
                if statements:
                    data.update(statements)

            if "price" in request.data_types:
                price_data = self._fetch_price_data(request.ticker)
                if price_data:
                    data.update(price_data)

            if data:
                response.success = True
                response.data = data
                response.quality_metrics = self._calculate_quality_metrics(data)
            else:
                response.error_message = "No data returned"

        except Exception as e:
            response.error_message = str(e)
            logger.error(f"{ApiName}Provider.fetch_data error: {e}")
        finally:
            response.response_time = (datetime.now() - start_time).total_seconds()
        return response

    def _fetch_price_data(self, ticker: str) -> Optional[Dict]:
        ...

    def _fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        from core.data_processing.converters.{api_name}_converter import {ApiName}Converter
        ...
```

### Step 7 — Add to Configuration

Add the new source to `core/data_sources/data_sources_config.json`:
```json
"{api_name}": {
    "priority": 3,
    "is_enabled": true,
    "quality_threshold": 0.80,
    "cache_ttl_hours": 12,
    "credentials": {
        "api_key": "",
        "base_url": "https://api.example.com",
        "rate_limit_calls": 100,
        "rate_limit_period": 60,
        "timeout": 30,
        "retry_attempts": 3,
        "cost_per_call": 0.0,
        "monthly_limit": 10000,
        "is_active": false
    }
}
```

### Step 8 — Add API Key to Environment

Add to `.env.example`:
```
{API_NAME_UPPER}_API_KEY=your_{api_name}_api_key_here
```

### Step 9 — Write Tests

Create `tests/unit/test_{api_name}_adapter.py` following the pattern of `tests/unit/test_yfinance_adapter.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from core.data_processing.adapters.{api_name}_adapter import {ApiName}Adapter
from core.data_processing.converters.{api_name}_converter import {ApiName}Converter

class Test{ApiName}Converter:
    def test_convert_financial_data_basic(self): ...
    def test_extract_cash_flow_data(self): ...
    def test_get_supported_fields(self): ...
    def test_normalize_value_handles_nulls(self): ...
    def test_normalize_value_handles_strings(self): ...

class Test{ApiName}Adapter:
    def test_load_symbol_data(self): ...
    def test_handles_api_error(self): ...
    def test_check_availability(self): ...
```

## Quick Validation Checklist

After completing all steps, verify:

```bash
# 1. Import the converter
python -c "from core.data_processing.converters.{api_name}_converter import {ApiName}Converter; print('OK')"

# 2. Import the adapter
python -c "from core.data_processing.adapters.{api_name}_adapter import {ApiName}Adapter; print('OK')"

# 3. Check it appears in the adapters module
python -c "from core.data_processing.adapters import {ApiName}Adapter; print('OK')"

# 4. Run the unit tests
pytest tests/unit/test_{api_name}_adapter.py -v

# 5. Verify the converter interface
python -c "
from core.data_processing.converters.{api_name}_converter import {ApiName}Converter
from core.data_processing.converters.base_converter import BaseConverter
assert issubclass({ApiName}Converter, BaseConverter)
assert hasattr({ApiName}Converter, 'FIELD_MAPPINGS')
assert hasattr({ApiName}Converter, 'convert_financial_data')
assert hasattr({ApiName}Converter, 'extract_cash_flow_data')
assert hasattr({ApiName}Converter, 'get_supported_fields')
print('All checks passed!')
"
```

## Standard Field Names Reference

All converters MUST map to these project-standard names where available:

| Category | Standard Field Name |
|----------|-------------------|
| Cash Flow | `operating_cash_flow`, `capital_expenditures`, `free_cash_flow` |
| Income | `net_income`, `total_revenue`, `gross_profit`, `operating_income`, `ebitda`, `ebit` |
| Balance Sheet | `total_assets`, `total_liabilities`, `total_stockholder_equity`, `cash_and_equivalents`, `total_debt`, `long_term_debt` |
| Per Share | `earnings_per_share`, `book_value_per_share`, `dividends_per_share` |
| Market | `current_price`, `market_cap`, `pe_ratio`, `pb_ratio`, `beta`, `dividend_yield` |
| Company | `company_name`, `ticker`, `sector`, `industry`, `exchange` |

## Common Pitfalls

- **Import paths**: Always use absolute imports from project root or relative imports — never bare `from converter_name import ...`
- **Null values**: Use `_normalize_value()` for every numeric field — never pass raw strings through
- **FCF derivation**: If the API provides `operating_cash_flow` and `capital_expenditures` but not `free_cash_flow`, derive it as `ocf - abs(capex)`
- **Field name conflicts**: If two API fields map to the same standard field, keep the more precise one
- **Rate limiting**: Always call `self._enforce_rate_limit()` before any API call in the provider
