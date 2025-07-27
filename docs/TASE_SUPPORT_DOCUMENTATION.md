# Tel Aviv Stock Exchange (TASE) Support Documentation

## Overview

This document describes the comprehensive support for Tel Aviv Stock Exchange (TASE) stocks that has been implemented in the financial analysis system. The implementation handles the unique currency characteristics of Israeli stocks where:

- **Stock prices** are quoted in **Agorot (ILA)** - 1/100 of a Shekel
- **Financial reports** are in **millions of Shekels (ILS)**, except per-share values which are in Agorot (ILA)
- The system automatically detects currency from yfinance and selects appropriate valuation types

## Key Features

### 1. Automatic TASE Stock Detection

The system automatically detects TASE stocks using multiple criteria:
- Ticker symbols ending with `.TA` (e.g., `TEVA.TA`, `CHKP.TA`)
- Currency information from yfinance indicating `ILS` (Israeli Shekel)
- Financial currency metadata

### 2. Currency Conversion Utilities

#### Core Conversion Functions
- `convert_agorot_to_shekel(agorot_value)`: Converts Agorot to Shekels (÷ 100)
- `convert_shekel_to_agorot(shekel_value)`: Converts Shekels to Agorot (× 100)
- `get_price_in_shekels()`: Returns stock price in Shekels for TASE stocks
- `get_price_in_agorot()`: Returns stock price in Agorot for TASE stocks

#### Currency Information Retrieval
- `get_currency_info()`: Comprehensive currency information including both currency formats for TASE stocks

### 3. Enhanced Market Data Fetching

The `fetch_market_data()` method has been enhanced to:
- Detect TASE stocks automatically
- Extract currency information from yfinance
- Log currency handling information for debugging
- Store currency metadata in the financial calculator instance

### 4. DCF Valuation with Currency Handling

#### TASE-Specific Valuation Logic
- **Enterprise/Equity Values**: Calculated in millions of ILS
- **Per-Share Values**: Provided in both Agorot and Shekels
- **Currency Conversion**: Proper scaling from millions ILS to per-share Agorot
  - Formula: `equity_value_millions_ILS × 1,000,000 × 100 / shares_outstanding`

#### DCF Results Enhancement
The DCF calculation results now include:
- `is_tase_stock`: Boolean flag indicating TASE stock
- `currency`: Primary currency (ILS for TASE stocks)  
- `value_per_share_agorot`: Fair value in Agorot
- `value_per_share_shekels`: Fair value in Shekels
- `currency_note`: Explanatory note about currency units

### 5. Streamlit Interface Updates

#### Enhanced Display
- **Current Price**: Shows both Agorot and Shekels for TASE stocks
- **Fair Value**: Displays primary value in Agorot with Shekel equivalent
- **Currency Symbols**: Uses ₪ symbol for Israeli Shekels
- **Tooltips**: Helpful hover information showing currency conversions

#### Example Display Format
```
Current Price: 1,500 ILA (≈ 15.00 ₪)
Fair Value (DCF): 2,000 ILA (≈ 20.00 ₪)
```

## Implementation Details

### File Modifications

#### 1. `financial_calculations.py`
- Added currency properties to `FinancialCalculator` class
- Enhanced `fetch_market_data()` with TASE detection
- Added currency conversion utility methods
- Added currency information storage

#### 2. `dcf_valuation.py`
- Modified per-share calculation logic for TASE stocks
- Added currency-specific logging and result formatting
- Enhanced market data retrieval with currency information
- Added TASE-specific fields to DCF results

#### 3. `fcf_analysis_streamlit.py`
- Updated price and valuation displays for TASE currencies
- Added currency-aware metric displays
- Enhanced sidebar information with dual currency format
- Added tooltips for currency conversion information

### Testing

#### Comprehensive Test Suite (`test_tase_support.py`)
- **Currency Conversion**: Tests Agorot ↔ Shekel conversions
- **TASE Detection**: Validates automatic detection logic
- **Price Handling**: Tests price display in both currencies
- **DCF Integration**: Verifies currency handling in valuations
- **Currency Info**: Tests currency information retrieval
- **Financial Values**: Tests normalization for TASE stocks

All tests pass successfully, validating the implementation.

## Usage Examples

### 1. Analyzing a TASE Stock

```python
from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator

# Load TASE stock data
calculator = FinancialCalculator("path/to/teva_company_folder")
calculator.fetch_market_data("TEVA.TA")

# The system automatically detects this as a TASE stock
print(f"Is TASE stock: {calculator.is_tase_stock}")
print(f"Price in Agorot: {calculator.get_price_in_agorot()}")
print(f"Price in Shekels: {calculator.get_price_in_shekels()}")

# DCF Valuation with proper currency handling
valuator = DCFValuator(calculator)
dcf_results = valuator.calculate_dcf_projections()

print(f"Fair value: {dcf_results['value_per_share_agorot']:.0f} ILA")
print(f"Fair value: {dcf_results['value_per_share_shekels']:.2f} ₪")
```

### 2. Currency Information

```python
# Get comprehensive currency information
currency_info = calculator.get_currency_info()
print(currency_info)

# Output for TASE stock:
# {
#   'currency': 'ILS',
#   'financial_currency': 'ILS', 
#   'is_tase_stock': True,
#   'price_in_agorot': 1500.0,
#   'price_in_shekels': 15.0,
#   'currency_note': 'TASE stocks: Prices in Agorot (ILA), Financials in millions Shekels (ILS)'
# }
```

## Technical Considerations

### Currency Unit Consistency
- **Financial Statements**: Always in millions ILS
- **Stock Prices**: Always in Agorot (from yfinance)
- **Per-Share Calculations**: Properly scaled to account for currency differences
- **Display**: Dual format with primary in Agorot, secondary in Shekels

### Error Handling
- Graceful fallback for non-TASE stocks
- Null value handling in currency conversions
- Logging for debugging currency detection issues
- Validation of currency consistency

### Performance Impact
- Minimal overhead for non-TASE stocks
- Currency detection integrated into existing market data fetch
- No additional API calls required

## Future Enhancements

### Potential Improvements
1. **Exchange Rate Integration**: Real-time USD↔ILS conversion for international comparison
2. **Additional Exchanges**: Support for other exchanges with currency complexities
3. **Historical Currency Data**: Track currency changes over time
4. **Reporting Enhancements**: Currency-aware report generation
5. **Batch Processing**: Efficient handling of multiple TASE stocks

### Configuration Options
Consider adding configuration options for:
- Default display currency preferences
- Currency symbol customization
- Exchange rate data sources
- Regional formatting preferences

## Conclusion

The TASE support implementation provides comprehensive handling of Israeli stock currency complexities while maintaining full compatibility with existing functionality. The system automatically detects TASE stocks and applies appropriate currency handling throughout the valuation process, from data fetching through final display.

All valuation methods (DCF, P/B, DDM) now work correctly with TASE stocks, providing accurate per-share valuations in the appropriate currency units while maintaining clear display formatting for users.