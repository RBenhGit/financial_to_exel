# FCF Mathematical Reference Guide

## Table of Contents
1. [Core FCF Formulas](#core-fcf-formulas)
2. [Component Calculations](#component-calculations)
3. [DCF Valuation Mathematics](#dcf-valuation-mathematics)
4. [Growth Rate Calculations](#growth-rate-calculations)
5. [Edge Case Handling](#edge-case-handling)
6. [Validation Rules](#validation-rules)

---

## Core FCF Formulas

### 1. Free Cash Flow to Firm (FCFF)

**Standard Formula:**
```
FCFF = EBIT × (1 - Tax Rate) + Depreciation & Amortization - ΔWorking Capital - Capital Expenditures
```

**Component Breakdown:**
- **After-Tax EBIT**: `EBIT × (1 - Tax Rate)`
- **Non-Cash Additions**: `+ Depreciation & Amortization`
- **Working Capital Impact**: `- ΔWorking Capital`
- **Capital Investments**: `- |Capital Expenditures|`

**Implementation Logic:**
```python
# Tax rate calculation with safety bounds
tax_rate = min(abs(tax_expense) / abs(ebt), 0.35) if ebt != 0 else 0.25

# FCFF calculation
after_tax_ebit = ebit * (1 - tax_rate)
fcff = after_tax_ebit + depreciation_amortization - working_capital_change - abs(capex)
```

**Mathematical Properties:**
- **Unit**: Millions of currency (already scaled in source data)
- **Sign Convention**: Positive FCFF indicates cash generation
- **Time Period**: Annual calculation for each fiscal year

### 2. Free Cash Flow to Equity (FCFE)

**Standard Formula:**
```
FCFE = Net Income + Depreciation & Amortization - ΔWorking Capital - Capital Expenditures + Net Borrowing
```

**Component Breakdown:**
- **Starting Point**: `Net Income` (after-tax, after-interest)
- **Non-Cash Additions**: `+ Depreciation & Amortization`
- **Working Capital Impact**: `- ΔWorking Capital`
- **Capital Investments**: `- |Capital Expenditures|`
- **Financing Adjustment**: `+ Net Borrowing`

**Implementation Logic:**
```python
# FCFE calculation
fcfe = net_income + depreciation_amortization - working_capital_change - abs(capex) + net_borrowing
```

**Mathematical Properties:**
- **Relationship to FCFF**: `FCFE = FCFF - Interest × (1 - Tax Rate) + Net Borrowing`
- **Equity Perspective**: Considers financing decisions impact
- **Dividend Capacity**: Positive FCFE indicates potential for distributions

### 3. Levered Free Cash Flow (LFCF)

**Standard Formula:**
```
LFCF = Cash from Operations - Capital Expenditures
```

**Component Breakdown:**
- **Operating Base**: `Cash from Operations` (includes working capital effects)
- **Investment Deduction**: `- |Capital Expenditures|`

**Implementation Logic:**
```python
# Simplified calculation
lfcf = operating_cash_flow - abs(capex)
```

**Mathematical Properties:**
- **Simplest Calculation**: Direct from cash flow statement
- **Already Levered**: Includes interest payments in operating cash flow
- **Quick Assessment**: Useful for rapid liquidity evaluation

---

## Component Calculations

### Working Capital Change (ΔWorking Capital)

**Formula:**
```
ΔWorking Capital = (Current Assetsᵢ - Current Liabilitiesᵢ) - (Current Assetsᵢ₋₁ - Current Liabilitiesᵢ₋₁)
```

**Step-by-Step Calculation:**
```python
# For each year i (starting from year 2)
working_capital_current = current_assets[i] - current_liabilities[i]
working_capital_previous = current_assets[i-1] - current_liabilities[i-1]
wc_change = working_capital_current - working_capital_previous
```

**Interpretation:**
- **Positive ΔWC**: Cash used (working capital increase)
- **Negative ΔWC**: Cash generated (working capital decrease)
- **Impact on FCF**: Subtracted from FCF (positive change reduces FCF)

### Tax Rate Calculation

**Dynamic Tax Rate Formula:**
```
Tax Rate = min(|Income Tax Expense| / |Earnings Before Tax|, 0.35)
```

**Implementation with Edge Cases:**
```python
def calculate_tax_rate(tax_expense, ebt):
    if ebt == 0:
        return 0.25  # Default 25% tax rate
    
    tax_rate = abs(tax_expense) / abs(ebt)
    return min(tax_rate, 0.35)  # Cap at 35%
```

**Rationale:**
- **Dynamic Calculation**: Uses actual company tax rates
- **Upper Bound**: 35% cap prevents anomalies from distorting results
- **Default Fallback**: 25% when EBT is zero
- **Absolute Values**: Handles negative income scenarios

### Capital Expenditure Treatment

**Formula:**
```
CapEx Impact = -|Capital Expenditures|
```

**Implementation:**
```python
capex_impact = -abs(capex_value)
```

**Rationale:**
- **Always Negative**: CapEx always reduces free cash flow
- **Absolute Value**: Ensures consistent treatment regardless of sign convention
- **Cash Outflow**: Represents actual cash spent on assets

---

## DCF Valuation Mathematics

### Present Value of FCF Projections

**Formula:**
```
PV(FCFᵢ) = FCFᵢ / (1 + r)ᵢ
```

Where:
- `FCFᵢ` = Free cash flow in year i
- `r` = Discount rate (WACC)
- `i` = Year number (1, 2, 3, ...)

**Implementation:**
```python
def calculate_present_values(future_cash_flows, discount_rate):
    pv_fcf = []
    for i, fcf in enumerate(future_cash_flows, 1):
        pv = fcf / ((1 + discount_rate) ** i)
        pv_fcf.append(pv)
    return pv_fcf
```

### Terminal Value Calculation

**Gordon Growth Model:**
```
Terminal Value = FCF₁₀ × (1 + g) / (r - g)
```

Where:
- `FCF₁₀` = Final year projected FCF
- `g` = Terminal growth rate
- `r` = Discount rate

**Present Value of Terminal Value:**
```
PV(Terminal Value) = Terminal Value / (1 + r)ⁿ
```

Where `n` = number of projection years

**Implementation:**
```python
def calculate_terminal_value(final_fcf, growth_rate, discount_rate, projection_years):
    terminal_fcf = final_fcf * (1 + growth_rate)
    terminal_value = terminal_fcf / (discount_rate - growth_rate)
    pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
    return terminal_value, pv_terminal
```

### Enterprise and Equity Value

**Enterprise Value:**
```
Enterprise Value = Σ PV(FCFᵢ) + PV(Terminal Value)
```

**Equity Value (Simplified):**
```
Equity Value = Enterprise Value - Net Debt
```

**Note**: Current implementation uses simplified approach where `Equity Value = Enterprise Value`

**Per-Share Value:**
```
Value per Share = Equity Value / Shares Outstanding
```

---

## Growth Rate Calculations

### Annualized Growth Rate

**Formula:**
```
Growth Rate = (|End Value| / |Start Value|)^(1/n) - 1
```

Where `n` = number of years in the period

**Implementation:**
```python
def calculate_growth_rate(start_value, end_value, periods):
    if start_value == 0:
        return 0
    
    growth_rate = (abs(end_value) / abs(start_value)) ** (1 / periods) - 1
    
    # Handle negative cash flow scenarios
    if end_value < 0 and start_value > 0:
        growth_rate = -growth_rate
    elif end_value > 0 and start_value < 0:
        growth_rate = abs(growth_rate)
    
    return growth_rate
```

### Multi-Period Growth Analysis

**Periods Analyzed:**
- 1-Year Growth: `(FCF₂₀₂₄ / FCF₂₀₂₃) - 1`
- 3-Year Growth: `(FCF₂₀₂₄ / FCF₂₀₂₁)^(1/3) - 1`
- 5-Year Growth: `(FCF₂₀₂₄ / FCF₂₀₁₉)^(1/5) - 1`
- 10-Year Growth: `(FCF₂₀₂₄ / FCF₂₀₁₄)^(1/10) - 1`

---

## Edge Case Handling

### Negative Cash Flows

**Scenario 1: Negative Starting Value, Positive Ending**
```python
if start_value < 0 and end_value > 0:
    # Improvement from negative to positive
    growth_rate = abs(calculated_growth_rate)
```

**Scenario 2: Positive Starting Value, Negative Ending**
```python
if start_value > 0 and end_value < 0:
    # Deterioration from positive to negative
    growth_rate = -abs(calculated_growth_rate)
```

**Scenario 3: Both Negative Values**
```python
if start_value < 0 and end_value < 0:
    # Use absolute values for calculation
    growth_rate = (abs(end_value) / abs(start_value)) ** (1/periods) - 1
    # Sign adjustment based on magnitude change
```

### Zero and Missing Values

**Zero Starting Value:**
```python
if start_value == 0:
    return 0  # Cannot calculate meaningful growth rate
```

**Missing Data Points:**
```python
if len(values) < period + 1:
    continue  # Skip this period calculation
```

**Invalid Metrics:**
```python
try:
    metric_value = float(clean_value)
except (ValueError, TypeError):
    metric_value = 0  # Use zero for invalid values
```

### Division by Zero Protection

**Tax Rate Calculation:**
```python
tax_rate = abs(tax_expense) / abs(ebt) if ebt != 0 else default_tax_rate
```

**Growth Rate Calculation:**
```python
if start_value == 0 or discount_rate == growth_rate:
    return fallback_value
```

---

## Validation Rules

### Data Quality Checks

**File Structure Validation:**
```python
required_folders = ['FY', 'LTM']
required_files = ['Income Statement', 'Balance Sheet', 'Cash Flow Statement']
```

**Metric Availability:**
```python
required_metrics = {
    'FCFF': ['EBIT', 'Income Tax Expense', 'EBT', 'Depreciation & Amortization'],
    'FCFE': ['Net Income', 'Depreciation & Amortization', 'Cash from Financing'],
    'LFCF': ['Cash from Operations', 'Capital Expenditure']
}
```

### Calculation Bounds

**Tax Rate Bounds:**
```python
MIN_TAX_RATE = 0.0
MAX_TAX_RATE = 0.35
DEFAULT_TAX_RATE = 0.25
```

**Growth Rate Bounds:**
```python
MIN_GROWTH_RATE = -0.99  # -99% (company near bankruptcy)
MAX_GROWTH_RATE = 5.0    # 500% (extreme growth scenarios)
```

**DCF Assumption Bounds:**
```python
MIN_DISCOUNT_RATE = 0.01     # 1%
MAX_DISCOUNT_RATE = 0.50     # 50%
MIN_TERMINAL_GROWTH = -0.10  # -10%
MAX_TERMINAL_GROWTH = 0.10   # 10%
```

### Data Consistency Checks

**Array Length Validation:**
```python
def validate_array_lengths(arrays):
    lengths = [len(arr) for arr in arrays if arr]
    if len(set(lengths)) > 1:
        logger.warning(f"Inconsistent array lengths: {lengths}")
        return False
    return True
```

**Temporal Ordering:**
```python
def validate_temporal_order(years):
    return all(years[i] <= years[i+1] for i in range(len(years)-1))
```

### Mathematical Constraints

**Gordon Growth Model Validity:**
```python
def validate_gordon_growth(discount_rate, growth_rate):
    if growth_rate >= discount_rate:
        raise ValueError("Growth rate must be less than discount rate")
    return True
```

**FCF Reasonableness:**
```python
def validate_fcf_magnitude(fcf_values, revenue_values):
    # FCF should generally be less than revenue
    for fcf, revenue in zip(fcf_values, revenue_values):
        if abs(fcf) > abs(revenue) * 2:  # FCF > 200% of revenue
            logger.warning(f"Unusually high FCF: {fcf} vs Revenue: {revenue}")
```

---

## Implementation Notes

### Numerical Precision
- **Floating Point**: All calculations use Python `float` (64-bit precision)
- **Rounding**: Display values rounded to 1 decimal place for millions
- **Intermediate Calculations**: Full precision maintained throughout

### Performance Optimizations
- **Vectorized Operations**: Use NumPy arrays where possible
- **Lazy Evaluation**: Calculate only requested FCF types
- **Memoization**: Cache expensive calculations

### Error Propagation
- **Graceful Degradation**: Continue with available data when some metrics missing
- **Error Logging**: Comprehensive logging for debugging
- **User Feedback**: Clear error messages for data quality issues

This mathematical reference provides the precise formulas and implementation details for all FCF calculations in the application, ensuring accuracy and consistency across all analytical workflows.