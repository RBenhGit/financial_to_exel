# Fair Value Calculation Guide

## Overview

This document provides a comprehensive explanation of how the **Fair Value per Share** is calculated in the financial analysis application. The Fair Value represents the intrinsic value of a company's stock derived from a **Discounted Cash Flow (DCF) analysis**.

## System Architecture

### Primary Calculation Modules
- **`dcf_valuation.py`** - Core DCF calculation engine
- **`financial_calculations.py`** - Market data fetching via Yahoo Finance
- **`fcf_analysis.py`** - Legacy DCF implementation 
- **`fcf_analysis_streamlit.py`** - Modern Streamlit web interface

## Detailed Fair Value Calculation Process

### **Step 1: Base FCF Determination**

**Source**: `dcf_valuation.py:163`
```python
base_fcf = fcf_values[-1] if fcf_values else 0
```

**Process**:
- Uses the most recent **Free Cash Flow to Firm (FCFF)** from historical data
- **Fallback**: $100M if no historical data is available
- FCFF is calculated using: `EBIT(1-Tax Rate) + D&A - Working Capital Change - CapEx`

### **Step 2: Historical Growth Rate Analysis**

**Source**: `dcf_valuation.py:99-145`
```python
def _calculate_historical_growth_rates(self, fcf_values):
    # Calculate CAGR for 1, 3, 5 year periods
    growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
```

**Process**:
- Calculates **Compound Annual Growth Rate (CAGR)** for 1-year, 3-year, and 5-year periods
- **Growth Rate Caps**: Between -20% and +30% to prevent extreme projections
- **Default Projection Growth**: Uses 3-year CAGR as the primary growth assumption
- **Handles Negative Values**: Special logic for negative FCF transitions

### **Step 3: FCF Projections (10-Year Model)**

**Source**: `dcf_valuation.py:147-189`
```python
def _project_future_fcf(self, fcf_values, assumptions, historical_growth):
    current_fcf = current_fcf * (1 + growth_rate)
```

**Growth Rate Structure**:
- **Years 1-5**: Uses 3-year historical growth rate (or user-defined input)
- **Years 6-10**: Uses 5-year historical growth rate (or user-defined input)
- **Formula**: `FCF(year) = Previous FCF × (1 + Growth Rate)`

### **Step 4: Terminal Value Calculation**

**Source**: `dcf_valuation.py:191-219`
```python
def _calculate_terminal_value(self, projections, assumptions):
    terminal_fcf = final_fcf * (1 + assumptions['terminal_growth_rate'])
    terminal_value = terminal_fcf / (assumptions['discount_rate'] - assumptions['terminal_growth_rate'])
```

**Gordon Growth Model**:
```
Terminal FCF = Final Year FCF × (1 + Terminal Growth Rate)
Terminal Value = Terminal FCF ÷ (Discount Rate - Terminal Growth Rate)
```

**Default Values**:
- **Terminal Growth Rate**: 2.5% (perpetual growth assumption)
- **Method**: Perpetual Growth Model (alternative: Exit Multiple available in legacy code)

### **Step 5: Present Value Calculations**

**Source**: `dcf_valuation.py:221-238` & `dcf_valuation.py:67-68`
```python
def _calculate_present_values(self, future_cash_flows, discount_rate):
    pv = cash_flow / ((1 + discount_rate) ** year)

# Terminal value discounting
pv_terminal = terminal_value / ((1 + assumptions['discount_rate']) ** assumptions['projection_years'])
```

**Formulas**:
- **PV of Annual FCF**: `FCF(t) ÷ (1 + Discount Rate)^t`
- **PV of Terminal Value**: `Terminal Value ÷ (1 + Discount Rate)^10`
- **Default Discount Rate**: 10% (representing required rate of return)

### **Step 6: Enterprise Value Calculation**

**Source**: `dcf_valuation.py:71`
```python
enterprise_value = sum(pv_fcf) + pv_terminal
```

**Formula**:
```
Enterprise Value = Σ(Present Value of FCF) + Present Value of Terminal Value
```

**Components**:
- Sum of all discounted future cash flows (Years 1-10)
- Plus discounted terminal value
- Represents total firm value before debt considerations

### **Step 7: Equity Value Calculation**

**Primary Source**: `dcf_valuation.py:78`
```python
equity_value = enterprise_value  # Simplified implementation
```

**Full Implementation**: `fcf_analysis.py:1029`
```python
equity_value = enterprise_value - net_debt
```

**Formula**:
```
Equity Value = Enterprise Value - Net Debt
```

**Net Debt Estimation**:
- Estimated from financing cash flows when available
- Set to 0 if unavailable (simplified approach)
- Full implementation subtracts total debt and adds cash

### **Step 8: Market Data Acquisition**

**Source**: `financial_calculations.py:656-705`
```python
def fetch_market_data(self, ticker_symbol=None):
    import yfinance as yf
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    shares_outstanding = info.get('sharesOutstanding', 1000000)
```

**Yahoo Finance Integration**:
- **Current Stock Price**: Real-time market price
- **Market Capitalization**: Current market value
- **Shares Outstanding**: Total number of shares in circulation
- **Fallback Values**: 1M shares if data unavailable

**Calculation Method**:
```python
shares_outstanding = market_cap / current_stock_price  # When direct data unavailable
```

### **Step 9: Fair Value Per Share Calculation**

**Primary Source**: `dcf_valuation.py:79`
```python
value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0
```

**Legacy Implementation**: `fcf_analysis.py:1032`
```python
equity_value_per_share = equity_value * 1000000 / assumptions['shares_outstanding']
```

## Complete Fair Value Formula

**Mathematical Expression** (from `readme.md:88`):
```
Fair Value = [Σ(FCF(t)/(1+r)^t) + (TV/(1+r)^10) - Net Debt] × 1M / Shares Outstanding
```

**Where**:
- **FCF(t)** = Free Cash Flow in year t
- **r** = Discount rate (default 10%)
- **TV** = Terminal Value
- **Net Debt** = Estimated net debt position
- **Shares Outstanding** = From Yahoo Finance API
- **1M** = Million conversion factor (in legacy implementation)

## Default Assumptions

**Source**: `dcf_valuation.py:27-34`
```python
self.default_assumptions = {
    'discount_rate': 0.10,           # 10% required rate of return
    'terminal_growth_rate': 0.025,   # 2.5% perpetual growth
    'growth_rate_yr1_5': 0.05,       # 5% early years growth
    'growth_rate_yr5_10': 0.03,      # 3% later years growth
    'projection_years': 5,           # 5-year explicit forecast period
    'terminal_method': 'perpetual_growth'
}
```

## Data Flow Architecture

```
Historical Financial Data
           ↓
    FCF Calculation (FCFF)
           ↓
    Growth Rate Analysis
           ↓
    10-Year FCF Projections
           ↓
    Terminal Value (Gordon Growth)
           ↓
    Present Value Calculations
           ↓
    Enterprise Value
           ↓
    Equity Value (minus Net Debt)
           ↓
    Yahoo Finance Market Data
           ↓
    Fair Value per Share
```

## Key Implementation Files

### DCF Core Engine
- **`dcf_valuation.py:36`** - `calculate_dcf_projections()` - Main DCF calculation method
- **`dcf_valuation.py:191`** - `_calculate_terminal_value()` - Terminal value calculation
- **`dcf_valuation.py:221`** - `_calculate_present_values()` - Present value discounting

### Market Data Integration
- **`financial_calculations.py:656`** - `fetch_market_data()` - Yahoo Finance API integration
- **`dcf_valuation.py:240`** - `_get_market_data()` - Market data retrieval wrapper

### User Interfaces
- **`fcf_analysis_streamlit.py:480`** - `render_dcf_analysis()` - Modern web interface
- **`fcf_analysis.py:1532`** - `_calculate_dcf_valuation()` - Legacy GUI implementation

## Sensitivity Analysis

**Source**: `dcf_valuation.py:277-329`

The system includes sensitivity analysis that recalculates fair value across different:
- **Discount rates** (typically 8% to 14%)
- **Terminal growth rates** (typically 1% to 4%)

**Output**: Matrix showing upside/downside percentages relative to current market price

## Error Handling and Fallbacks

### Market Data Failures
- **Default Shares Outstanding**: 1,000,000 shares
- **Default Current Price**: $0 (marked as unavailable)
- **Graceful Degradation**: Calculation continues with estimated values

### Historical Data Issues
- **Missing FCF Data**: Uses $100M base assumption
- **Insufficient History**: Applies 5% default growth rate
- **Negative FCF Handling**: Special CAGR calculation logic

## Validation and Testing

The fair value calculation has been tested across multiple scenarios including:
- Companies with consistent positive FCF growth
- Companies with volatile or negative FCF periods
- Various market capitalizations and industries
- Different assumption sensitivity ranges

## Usage Examples

### Basic DCF Calculation
```python
dcf_valuator = DCFValuator(financial_calculator)
dcf_results = dcf_valuator.calculate_dcf_projections()
fair_value = dcf_results.get('value_per_share', 0)
```

### Custom Assumptions
```python
custom_assumptions = {
    'discount_rate': 0.12,           # 12% discount rate
    'terminal_growth_rate': 0.03,    # 3% terminal growth
    'growth_rate_yr1_5': 0.08        # 8% early growth
}
dcf_results = dcf_valuator.calculate_dcf_projections(custom_assumptions)
```

### Sensitivity Analysis
```python
discount_rates = [0.08, 0.10, 0.12, 0.14]
terminal_rates = [0.01, 0.025, 0.03, 0.04]
sensitivity = dcf_valuator.sensitivity_analysis(discount_rates, terminal_rates)
```

This comprehensive DCF model provides a robust foundation for equity valuation based on fundamental cash flow analysis and market-based inputs.