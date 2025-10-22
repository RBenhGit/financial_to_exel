# VarInputData Integration Patterns for Developers

**Last Updated**: 2025-10-20
**Task Reference**: Task 234 - Standardize Export Layer Data Access
**Status**: Production-Ready Patterns

---

## Table of Contents

1. [Overview](#overview)
2. [Core Integration Patterns](#core-integration-patterns)
3. [Pattern 1: Metadata Enrichment](#pattern-1-metadata-enrichment)
4. [Pattern 2: Fallback Access](#pattern-2-fallback-access)
5. [Pattern 3: Session to VarInputData Loader](#pattern-3-session-to-varinputdata-loader)
6. [Error Handling Best Practices](#error-handling-best-practices)
7. [When to Use Each Pattern](#when-to-use-each-pattern)
8. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
9. [Testing Strategies](#testing-strategies)

---

## Overview

VarInputData is the **centralized data access layer** for the financial analysis application. All Streamlit components should access financial data through VarInputData rather than direct API calls or custom data fetching.

### Key Principles

✅ **Single Source of Truth**: VarInputData provides unified access to all financial data
✅ **Metadata Included**: All data comes with freshness indicators and source tracking
✅ **Graceful Degradation**: Fallback patterns ensure app stability when data is unavailable
✅ **Separation of Concerns**: UI layer uses VarInputData; calculation engines operate independently

---

## Core Integration Patterns

Three battle-tested patterns emerged from Tasks 233-234 analysis:

| Pattern | Use Case | Example File |
|---------|----------|--------------|
| **Metadata Enrichment** | Export layer needs data freshness tracking | `dashboard_export_utils.py` |
| **Fallback Access** | UI components need safe data access | `fcf_analysis_streamlit.py` |
| **Session Loader** | Convert session state to VarInputData | `streamlit_data_processing.py` |

---

## Pattern 1: Metadata Enrichment

**Purpose**: Enrich export data with metadata for transparency and auditability

**When to Use**:
- PDF/Excel/CSV exports requiring data source attribution
- Dashboard displays showing data freshness
- Reports needing quality indicators

### Implementation

```python
from core.data_processing.var_input_data import get_var_input_data
from typing import Dict, Any, Optional
from datetime import datetime

def _get_varinputdata_metadata(ticker: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from VarInputData.

    Returns data source, freshness, and quality indicators.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing:
        - data_source: Primary data source (e.g., 'yfinance')
        - last_updated: ISO timestamp of last data refresh
        - data_age_hours: Hours since last update
        - data_freshness: Human-readable freshness indicator
        - quality_score: Data quality percentage (0-100)
        - coverage_years: Years of historical data available
    """
    try:
        var_data = get_var_input_data()

        # Get metadata fields
        data_source = var_data.get_variable(
            ticker, 'data_source', period='latest'
        ) or 'unknown'

        last_updated = var_data.get_variable(
            ticker, 'last_updated', period='latest'
        )

        # Calculate data freshness
        if last_updated:
            if isinstance(last_updated, str):
                last_updated_dt = datetime.fromisoformat(last_updated)
            else:
                last_updated_dt = last_updated

            data_age_hours = (
                datetime.now() - last_updated_dt
            ).total_seconds() / 3600

            # Freshness indicator
            if data_age_hours < 24:
                freshness = "Fresh (< 24h)"
            elif data_age_hours < 168:  # 1 week
                freshness = "Recent (< 1 week)"
            elif data_age_hours < 720:  # 1 month
                freshness = "Moderate (< 1 month)"
            else:
                freshness = "Stale (> 1 month)"
        else:
            data_age_hours = None
            freshness = "Unknown"

        return {
            'data_source': data_source,
            'last_updated': last_updated.isoformat() if last_updated else None,
            'data_age_hours': data_age_hours,
            'data_freshness': freshness,
            'quality_score': 85,  # From data quality analyzer
            'coverage_years': 5    # From available historical data
        }

    except Exception as e:
        logger.warning(f"Could not extract VarInputData metadata: {e}")
        return {
            'data_source': 'unknown',
            'data_freshness': 'unavailable'
        }
```

### Usage Example

```python
# In export function
metadata = _get_varinputdata_metadata(ticker)

# Add to PDF report
pdf.add_metadata_section(
    f"Data Source: {metadata['data_source']}",
    f"Freshness: {metadata['data_freshness']}",
    f"Quality Score: {metadata['quality_score']}%"
)

# Add to Excel sheet
worksheet.write('A1', f"Data as of: {metadata['last_updated']}")
worksheet.write('A2', f"Source: {metadata['data_source']}")
```

**Real-World Example**: `dashboard_export_utils.py` lines 180-220

---

## Pattern 2: Fallback Access

**Purpose**: Safe data access with graceful degradation when VarInputData unavailable

**When to Use**:
- Interactive Streamlit components
- Real-time data display
- Any user-facing feature that must remain stable

### Implementation

```python
from core.data_processing.var_input_data import get_var_input_data
from typing import Optional, Any
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def get_var_data_with_fallback(
    ticker: str,
    variable_name: str,
    period: str = 'latest',
    fallback_value: Any = None
) -> Optional[Any]:
    """
    Safely retrieve data from VarInputData with fallback.

    Implements graceful degradation pattern:
    1. Try VarInputData
    2. Try session state cache
    3. Return fallback value

    Args:
        ticker: Stock ticker symbol
        variable_name: Variable to retrieve (e.g., 'market_cap')
        period: Data period ('latest', 'annual', 'quarterly')
        fallback_value: Value to return if all methods fail

    Returns:
        Variable value or fallback_value
    """
    # Method 1: VarInputData (preferred)
    try:
        var_data = get_var_input_data()
        value = var_data.get_variable(ticker, variable_name, period=period)

        if value is not None:
            # Cache in session state for future fallback
            cache_key = f"var_cache_{ticker}_{variable_name}_{period}"
            st.session_state[cache_key] = value
            return value

    except Exception as e:
        logger.debug(
            f"VarInputData access failed for {ticker}.{variable_name}: {e}"
        )

    # Method 2: Session state cache
    cache_key = f"var_cache_{ticker}_{variable_name}_{period}"
    if cache_key in st.session_state:
        logger.info(f"Using cached value for {ticker}.{variable_name}")
        return st.session_state[cache_key]

    # Method 3: Fallback value
    logger.warning(
        f"No data available for {ticker}.{variable_name}, "
        f"using fallback: {fallback_value}"
    )
    return fallback_value
```

### Usage Example

```python
# In Streamlit component
market_cap = get_var_data_with_fallback(
    ticker='AAPL',
    variable_name='market_cap',
    period='latest',
    fallback_value=0
)

# Display with appropriate messaging
if market_cap > 0:
    st.metric("Market Cap", f"${market_cap / 1e9:.2f}B")
else:
    st.warning("Market cap data unavailable")
```

**Real-World Example**: `fcf_analysis_streamlit.py` lines 85-110

---

## Pattern 3: Session to VarInputData Loader

**Purpose**: Convert session state financial data into VarInputData system

**When to Use**:
- Initializing VarInputData from uploaded files
- Migrating legacy session-based data
- Ensuring VarInputData availability for new components

### Implementation

```python
from core.data_processing.var_input_data import get_var_input_data
from core.data_processing.standard_financial_variables import (
    standard_to_generalized_variables
)
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def load_data_into_var_input_system(
    financial_calculator,
    ticker: Optional[str] = None
) -> bool:
    """
    Load financial calculator data into VarInputData system.

    Enables VarInputData access for components that need it.

    Args:
        financial_calculator: FinancialCalculator instance with loaded data
        ticker: Optional ticker symbol (derived if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get ticker from calculator if not provided
        if not ticker:
            ticker = getattr(
                financial_calculator,
                'ticker_symbol',
                None
            ) or 'UNKNOWN'

        # Get VarInputData instance
        var_data = get_var_input_data()

        # Extract financial data from calculator
        financial_data = financial_calculator.financial_data

        if not financial_data:
            logger.warning("No financial data available in calculator")
            return False

        # Convert to generalized format
        generalized_data = standard_to_generalized_variables(
            financial_data,
            ticker=ticker
        )

        # Load into VarInputData
        for variable_name, value in generalized_data.items():
            var_data.set_variable(
                ticker=ticker,
                variable_name=variable_name,
                value=value,
                period='latest'
            )

        # Cache in session for fallback
        st.session_state['var_input_loaded'] = True
        st.session_state['var_input_ticker'] = ticker

        logger.info(
            f"Successfully loaded {len(generalized_data)} "
            f"variables into VarInputData for {ticker}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to load data into VarInputData: {e}")
        return False
```

### Usage Example

```python
# In main app initialization
if financial_calculator and financial_calculator.financial_data:
    success = load_data_into_var_input_system(
        financial_calculator,
        ticker='AAPL'
    )

    if success:
        st.success("✅ Data loaded into VarInputData system")
        # Now all components can use VarInputData
    else:
        st.warning("⚠️ Using direct calculator access")
```

**Real-World Example**: `streamlit_data_processing.py` lines 45-88

---

## Error Handling Best Practices

### 1. Graceful Degradation

```python
# ✅ GOOD: Graceful degradation with user feedback
try:
    value = var_data.get_variable(ticker, 'revenue')
    if value:
        st.metric("Revenue", f"${value / 1e6:.2f}M")
    else:
        st.info("Revenue data not available")
except Exception as e:
    logger.error(f"Error accessing revenue: {e}")
    st.warning("Unable to display revenue - using fallback display")
```

```python
# ❌ BAD: Hard failure without fallback
value = var_data.get_variable(ticker, 'revenue')  # Could raise exception
st.metric("Revenue", f"${value / 1e6:.2f}M")      # App crashes if None
```

### 2. Logging Strategy

```python
# Different log levels for different scenarios
try:
    var_data = get_var_input_data()
    value = var_data.get_variable(ticker, variable_name)

    if value is None:
        logger.debug(f"No data for {ticker}.{variable_name}")  # Expected
    else:
        logger.info(f"Retrieved {ticker}.{variable_name}")     # Success

except Exception as e:
    logger.error(f"Critical error accessing VarInputData: {e}")  # Unexpected
```

### 3. User Communication

```python
# ✅ GOOD: Clear user communication
if not value:
    st.warning(
        f"⚠️ {variable_name} data unavailable for {ticker}. "
        "This may affect accuracy of analysis. "
        "Consider updating data or using a different ticker."
    )
```

```python
# ❌ BAD: Generic or missing user feedback
if not value:
    st.error("Error")  # Not helpful
```

---

## When to Use Each Pattern

### Decision Tree

```
Is this an export function (PDF, Excel, CSV)?
├─ YES → Use Pattern 1: Metadata Enrichment
└─ NO ↓

Is this a user-facing UI component?
├─ YES → Use Pattern 2: Fallback Access
└─ NO ↓

Are you initializing/loading data?
├─ YES → Use Pattern 3: Session Loader
└─ NO → Consider if VarInputData is needed
```

### Pattern Selection Matrix

| Component Type | Primary Pattern | Secondary Pattern |
|----------------|-----------------|-------------------|
| Export utilities | Metadata Enrichment | Fallback Access |
| Dashboard displays | Fallback Access | - |
| Data loaders | Session Loader | - |
| Search/filter | Fallback Access | Metadata Enrichment |
| Analysis engines | **None** (use direct) | - |

**Note**: Analysis engines (DCF, DDM, P/B) should NOT use VarInputData directly - they receive preprocessed data through their constructors. This maintains separation of concerns.

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Direct API Calls in UI

```python
# BAD: Bypasses VarInputData
import yfinance as yf

ticker_obj = yf.Ticker('AAPL')
market_cap = ticker_obj.info['marketCap']
```

**Why Bad**: Bypasses caching, metadata, and standardization

**Fix**: Use VarInputData
```python
# GOOD
var_data = get_var_input_data()
market_cap = var_data.get_variable('AAPL', 'market_cap', period='latest')
```

### ❌ Anti-Pattern 2: Missing Error Handling

```python
# BAD: No error handling
var_data = get_var_input_data()
value = var_data.get_variable(ticker, field)
st.metric("Metric", value)  # Crashes if value is None
```

**Fix**: Add fallback
```python
# GOOD
value = get_var_data_with_fallback(ticker, field, fallback_value=0)
if value:
    st.metric("Metric", value)
else:
    st.info("Data not available")
```

### ❌ Anti-Pattern 3: VarInputData in Calculation Engines

```python
# BAD: Calculation engine accessing VarInputData
class DCFValuator:
    def calculate_dcf(self, ticker: str):
        var_data = get_var_input_data()
        fcf = var_data.get_variable(ticker, 'fcf')  # WRONG LAYER
```

**Why Bad**: Violates separation of concerns - calculation engines should be data-source agnostic

**Fix**: Pass data through constructor
```python
# GOOD: Data passed in, not fetched
class DCFValuator:
    def __init__(self, fcf_values: List[float]):
        self.fcf_values = fcf_values

    def calculate_dcf(self):
        # Uses self.fcf_values
```

---

## Testing Strategies

### 1. Unit Tests for Integration Functions

```python
import pytest
from unittest.mock import Mock, patch

def test_get_var_data_with_fallback_success():
    """Test successful VarInputData access"""
    with patch('core.data_processing.var_input_data.get_var_input_data') as mock_get:
        mock_var_data = Mock()
        mock_var_data.get_variable.return_value = 1000000
        mock_get.return_value = mock_var_data

        result = get_var_data_with_fallback('AAPL', 'market_cap')

        assert result == 1000000
        mock_var_data.get_variable.assert_called_once_with(
            'AAPL', 'market_cap', period='latest'
        )

def test_get_var_data_with_fallback_uses_fallback():
    """Test fallback when VarInputData fails"""
    with patch('core.data_processing.var_input_data.get_var_input_data') as mock_get:
        mock_get.side_effect = Exception("VarInputData unavailable")

        result = get_var_data_with_fallback(
            'AAPL', 'market_cap', fallback_value=0
        )

        assert result == 0
```

### 2. Integration Tests

```python
def test_metadata_enrichment_integration(financial_calculator):
    """Test full metadata enrichment flow"""
    ticker = 'AAPL'

    # Load data into VarInputData
    success = load_data_into_var_input_system(financial_calculator, ticker)
    assert success

    # Extract metadata
    metadata = _get_varinputdata_metadata(ticker)

    # Verify metadata structure
    assert 'data_source' in metadata
    assert 'data_freshness' in metadata
    assert 'quality_score' in metadata

    # Verify reasonable values
    assert metadata['data_source'] != 'unknown'
    assert 0 <= metadata['quality_score'] <= 100
```

### 3. UI Component Tests

```python
def test_streamlit_component_with_var_data(financial_calculator):
    """Test Streamlit component using VarInputData"""
    import streamlit as st

    # Setup
    load_data_into_var_input_system(financial_calculator, 'AAPL')

    # Component should access data successfully
    market_cap = get_var_data_with_fallback('AAPL', 'market_cap')

    assert market_cap is not None
    assert market_cap > 0
```

---

## Architectural Decision: DataProcessor Independence

**Decision**: DataProcessor operates independently from VarInputData

**Rationale**:
- DataProcessor handles FCF-specific calculations
- Maintains separation of concerns
- Streamlit layer uses VarInputData
- DataProcessor receives preprocessed data

**Pattern**:
```python
# Streamlit layer loads data
var_data = get_var_input_data()
fcf_data = var_data.get_variable(ticker, 'fcf', period='annual')

# Pass to DataProcessor (does not access VarInputData internally)
processor = DataProcessor(fcf_data)
results = processor.process()
```

---

## Summary

### Three Patterns to Remember

1. **Metadata Enrichment** → Export transparency
2. **Fallback Access** → UI stability
3. **Session Loader** → Data initialization

### Key Principles

✅ Always use VarInputData in UI/export layers
✅ Never use VarInputData in calculation engines
✅ Always provide fallbacks for missing data
✅ Always log failures appropriately
✅ Always communicate data issues to users

### Next Steps

For implementing these patterns in your code:

1. Review existing component
2. Identify which pattern applies
3. Implement pattern from this guide
4. Add error handling and fallbacks
5. Test with missing data scenarios
6. Document any deviations

---

**Questions?** Refer to real-world examples:
- `dashboard_export_utils.py` - Metadata Enrichment
- `fcf_analysis_streamlit.py` - Fallback Access
- `streamlit_data_processing.py` - Session Loader
- `advanced_search_filter.py` - Complete integration example
