# Free Cash Flow (FCF) Calculation Guide

## Overview

This document provides a comprehensive explanation of how **Free Cash Flow (FCF)** is calculated in the financial analysis application. The system implements **three distinct FCF methodologies**, each serving different analytical purposes and valuation approaches.

## System Architecture

### Primary FCF Calculation Modules
- **`financial_calculations.py`** - Modern, optimized FCF calculation engine
- **`fcf_analysis.py`** - Legacy FCF implementation with GUI
- **`fcf_analysis_streamlit.py`** - Streamlit web interface
- **`data_processing.py`** - Visualization and analysis tools

## Three FCF Calculation Methods

The application calculates three different types of Free Cash Flow:

### **1. Free Cash Flow to Firm (FCFF) 🏢**

**Purpose**: Measures cash flow available to all capital providers (debt and equity holders)
**Use Case**: Enterprise valuation and DCF analysis

#### **Modern Implementation** (`financial_calculations.py:277-311`)

**Formula**:
```
FCFF = EBIT(1 - Tax Rate) + Depreciation & Amortization - Working Capital Change - Capital Expenditures
```

**Source Code**:
```python
def calculate_fcf_to_firm(self):
    # Get pre-calculated metrics
    metrics = self._calculate_all_metrics()
    
    ebit_values = metrics.get('ebit', [])
    tax_rates = metrics.get('tax_rates', [])
    da_values = metrics.get('depreciation_amortization', [])
    capex_values = metrics.get('capex', [])
    working_capital_changes = metrics.get('working_capital_changes', [])
    
    # Calculate FCFF
    for i in range(len(working_capital_changes)):
        after_tax_ebit = ebit_values[i+1] * (1 - tax_rates[i+1])
        fcff = after_tax_ebit + da_values[i+1] - working_capital_changes[i] - abs(capex_values[i+1])
        fcff_values.append(fcff)
```

#### **Legacy Implementation** (`fcf_analysis.py:434-469`)

**Updated Implementation** (Now uses modern working capital):
- **Unified Working Capital**: Uses actual balance sheet changes like modern implementation
- Applies 1M multiplier for currency conversion
- Default tax rate of 25% if calculation fails
- **No Fallback**: Requires balance sheet data for accurate calculation

**Source Code**:
```python
def calculate_fcf_to_firm(self):
    # Calculate working capital changes using modern method
    wc_changes = self._calculate_working_capital_changes()
    
    # Calculate tax rate from revenue and tax expense
    tax_rate = abs(tax_expense) / revenue if revenue != 0 else 0.25
    
    # Get actual working capital change for this year
    wc_change = wc_changes[i] if i < len(wc_changes) else 0
    
    # Calculate FCFF (multiply by 1M)
    fcff = (ebit * (1 - tax_rate) + depreciation - wc_change - capex) * 1000000
```

### **2. Free Cash Flow to Equity (FCFE) 👥**

**Purpose**: Measures cash flow available specifically to equity holders
**Use Case**: Equity valuation and dividend capacity analysis

#### **Modern Implementation** (`financial_calculations.py:313-350`)

**Formula**:
```
FCFE = Net Income + Depreciation & Amortization - Working Capital Change - Capital Expenditures + Net Borrowing
```

**Source Code**:
```python
def calculate_fcf_to_equity(self):
    net_income_values = metrics.get('net_income', [])
    da_values = metrics.get('depreciation_amortization', [])
    capex_values = metrics.get('capex', [])
    net_borrowing_values = metrics.get('net_borrowing', [])
    working_capital_changes = metrics.get('working_capital_changes', [])
    
    fcfe = (net_income_values[i+1] + da_values[i+1] - working_capital_changes[i] - 
           abs(capex_values[i+1]) + net_borrowing_values[i+1])
```

**Key Innovation**: Uses **Net Borrowing** (debt issued - debt repaid) instead of total financing cash flow to exclude equity transactions and dividend payments.

#### **Updated Legacy Implementation** (`fcf_analysis.py:471-505`)

**Updated Features**:
- **Unified Working Capital**: Now uses actual balance sheet changes like modern implementation
- Estimates net borrowing from total financing cash flow: `max(0, financing_cf)`
- Applies 1M multiplier
- **No Fallback**: Requires balance sheet data for accurate calculation

### **3. Levered Free Cash Flow (LFCF) ⚡**

**Purpose**: Direct cash flow measurement from operations
**Use Case**: Operational efficiency and cash generation analysis

#### **Both Implementations** (Consistent across versions)

**Formula**:
```
LFCF = Cash from Operations - Capital Expenditures
```

**Modern Source** (`financial_calculations.py:352-381`):
```python
def calculate_levered_fcf(self):
    operating_cash_flow_values = metrics.get('operating_cash_flow', [])
    capex_values = metrics.get('capex', [])
    
    lfcf = operating_cash_flow_values[i] - abs(capex_values[i])
```

**Legacy Source** (`fcf_analysis.py:507-532`):
```python
def calculate_levered_fcf(self):
    lfcf = (operating_cf - capex) * 1000000  # With 1M multiplier
```

## Data Extraction and Sources

### **Financial Statement Loading**

**Source**: `financial_calculations.py:50-85`

The system loads three types of financial statements:
1. **Income Statement** → EBIT, Net Income, Tax Expense, Revenue
2. **Balance Sheet** → Current Assets, Current Liabilities
3. **Cash Flow Statement** → Depreciation & Amortization, Operating Cash Flow, CapEx, Financing Activities

**File Structure Expected**:
```
<TICKER>/
├── FY/
│   ├── <Company> - Income Statement.xlsx
│   ├── <Company> - Balance Sheet.xlsx
│   └── <Company> - Cash Flow Statement.xlsx
└── LTM/
    ├── <Company> - Income Statement.xlsx
    ├── <Company> - Balance Sheet.xlsx
    └── <Company> - Cash Flow Statement.xlsx
```

### **Metric Extraction Process**

**Source**: `financial_calculations.py:131-170`

```python
def _extract_metric_with_ltm(self, fy_data, ltm_data, metric_name):
    # Extract FY historical data
    fy_values = self._extract_metric_values(fy_data, metric_name, reverse=True)
    
    # Extract LTM data if available
    ltm_values = self._extract_metric_values(ltm_data, metric_name, reverse=True)
    
    # Combine: FY historical (all but last) + most recent LTM value
    combined_values = fy_values[:-1] + [ltm_values[-1]]
```

**Data Integration Strategy**:
- **Historical Data**: Uses 10-year FY (Fiscal Year) data
- **Latest Data**: Replaces most recent FY with LTM (Latest Twelve Months) data
- **Fallback**: Uses FY data only if LTM unavailable

### **Specific Metric Extractions**

**Source**: `financial_calculations.py:204-220`

```python
# Income Statement Metrics
metrics['ebit'] = self._extract_metric_with_ltm(income_data, income_ltm, "EBIT")
metrics['net_income'] = self._extract_metric_with_ltm(income_data, income_ltm, "Net Income")
metrics['tax_expense'] = self._extract_metric_with_ltm(income_data, income_ltm, "Income Tax Expense")

# Balance Sheet Metrics
metrics['current_assets'] = self._extract_metric_with_ltm(balance_data, balance_ltm, "Total Current Assets")
metrics['current_liabilities'] = self._extract_metric_with_ltm(balance_data, balance_ltm, "Total Current Liabilities")

# Cash Flow Statement Metrics
metrics['depreciation_amortization'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Depreciation & Amortization")
metrics['operating_cash_flow'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Cash from Operations")
metrics['capex'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Capital Expenditure")
```

### **Excel Data Parsing**

**Source**: `financial_calculations.py:420-478`

```python
def _extract_metric_values(self, df, metric_name, reverse=False):
    # Find row containing the metric in column 3 (index 2)
    for idx, row in df.iterrows():
        metric_text = str(row.iloc[2]) if len(row) > 2 else str(row.iloc[0])
        if metric_name.lower() in metric_text.lower():
            metric_row = row
            break
    
    # Extract numeric values (skip first 3 metadata columns)
    for val in metric_row.iloc[3:]:
        if pd.notna(val) and val != '':
            # Handle different numeric formats
            clean_val = val.replace(',', '').replace('(', '-').replace(')', '')
            values.append(float(clean_val))
```

**Data Processing Features**:
- **Automatic Format Detection**: Handles commas, parentheses (negative values)
- **Column Structure**: Expects metric names in column 3, data in columns 4+
- **Missing Data Handling**: Substitutes 0 for invalid values
- **Reverse Ordering**: Returns chronological order (oldest to newest)

## Advanced Calculations

### **Working Capital Change Calculation**

**Modern Implementation** (`financial_calculations.py:260-264`):
```python
# Calculate year-over-year working capital changes
for i in range(len(current_assets) - 1):
    wc_current_year = current_assets[i+1] - current_liabilities[i+1]
    wc_previous_year = current_assets[i] - current_liabilities[i]
    wc_change = wc_current_year - wc_previous_year
    metrics['working_capital_changes'].append(wc_change)
```

**Formula**: `Working Capital Change = (Current Assets - Current Liabilities)ₜ - (Current Assets - Current Liabilities)ₜ₋₁`

### **Tax Rate Calculation**

**Modern Implementation** (`financial_calculations.py:225-237`):
```python
# Calculate effective tax rates
for i in range(len(ebt_values)):
    if ebt_values[i] > 0:
        tax_rate = abs(tax_expense_values[i]) / ebt_values[i]
        # Cap tax rate between 0% and 50%
        tax_rate = min(max(tax_rate, 0), 0.50)
    else:
        tax_rate = 0.25  # Default 25%
    tax_rates.append(tax_rate)
```

**Features**:
- **Effective Tax Rate**: `Tax Rate = Tax Expense ÷ EBT`
- **Rate Capping**: Limited between 0% and 50%
- **Default Fallback**: 25% when EBT ≤ 0

### **Net Borrowing Calculation**

**Modern Implementation** (`financial_calculations.py:218-220`):
```python
metrics['debt_issued'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Long-Term Debt Issued")
metrics['debt_repaid'] = self._extract_metric_with_ltm(cashflow_data, cashflow_ltm, "Long-Term Debt Repaid")

# Calculate net borrowing
for i in range(len(debt_issued)):
    net_borrowing = debt_issued[i] - abs(debt_repaid[i])
    metrics['net_borrowing'].append(net_borrowing)
```

**Formula**: `Net Borrowing = Debt Issued - Debt Repaid`

## Performance Optimizations

### **Metric Caching System**

**Source**: `financial_calculations.py:175-185`

```python
def _calculate_all_metrics(self):
    # Check if metrics are already calculated and cached
    if self.metrics_calculated and self.metrics:
        logger.debug("Using cached financial metrics")
        return self.metrics
    
    # Calculate all metrics in one pass
    self.metrics = self._perform_metric_calculations()
    self.metrics_calculated = True
    return self.metrics
```

**Benefits**:
- **O(1) Cache Access**: Subsequent FCF calculations are nearly instant
- **Single Pass Computation**: All metrics calculated together once
- **Memory Efficiency**: Avoids redundant Excel file processing

### **Efficient Data Loading**

**Source**: `financial_calculations.py:87-127`

```python
def _load_excel_data(self, file_path):
    wb = load_workbook(filename=file_path)
    sheet = wb.active
    
    # Find header row containing 'FY-9', 'FY-8', etc.
    for i, row in enumerate(data):
        if any('FY-' in str(cell) for cell in row if cell):
            header_row_idx = i
            break
    
    df = pd.DataFrame(data_rows, columns=headers)
```

## Error Handling and Validation

### **Data Quality Checks**

**Missing Data Handling**:
- **Metric Not Found**: Logs warning and returns empty list
- **Invalid Values**: Substitutes 0 for non-numeric data
- **File Load Errors**: Raises exception with detailed error message

**Calculation Safeguards**:
- **Division by Zero**: Default tax rates and working capital assumptions
- **Negative Values**: Absolute value for CapEx, proper handling for debt
- **Array Length Mismatches**: Index bounds checking in all loops

### **Logging and Debugging**

**Comprehensive Logging** throughout calculations:
```python
logger.info(f"FCFF calculated: {len(fcff_values)} years")
logger.debug(f"FCFF {year}: EBIT={ebit}, Tax Rate={tax_rate:.2%}, FCFF={fcff/1000000:.2f}M")
logger.warning(f"Metric '{metric_name}' not found in financial data")
logger.error(f"Error calculating FCFF: {e}")
```

## FCF Calculation Workflow

### **Complete Calculation Pipeline**

```
1. Load Financial Statements
   ├── Income Statement (EBIT, Net Income, Tax Expense)
   ├── Balance Sheet (Current Assets/Liabilities)
   └── Cash Flow Statement (D&A, Operating CF, CapEx)
           ↓
2. Extract and Combine Metrics
   ├── FY Historical Data (10 years)
   ├── LTM Latest Data (most recent)
   └── Combined Timeline
           ↓
3. Calculate Derived Metrics
   ├── Tax Rates (Tax Expense ÷ EBT)
   ├── Working Capital Changes (YoY differences)
   └── Net Borrowing (Debt Issued - Repaid)
           ↓
4. Compute FCF Values
   ├── FCFF: EBIT(1-Tax) + D&A - WC Change - CapEx
   ├── FCFE: Net Income + D&A - WC Change - CapEx + Net Borrowing
   └── LFCF: Operating CF - CapEx
           ↓
5. Store and Cache Results
   └── FCF Results Dictionary
```

### **Data Flow Example**

**For FCFF Calculation**:
```python
# Year 2023 Example Calculation
after_tax_ebit = 1500 * (1 - 0.25)  # EBIT: $1,500M, Tax Rate: 25%
depreciation = 200                   # D&A: $200M
wc_change = 50                      # Working Capital increase: $50M
capex = 300                         # CapEx: $300M

fcff = 1125 + 200 - 50 - 300       # FCFF = $975M
```

## Key Differences: Modern vs Updated Legacy Implementation

| Aspect | Modern Implementation | Updated Legacy Implementation |
|--------|----------------------|-------------------------------|
| **Working Capital** | Actual YoY balance sheet changes | **✅ Now unified - uses actual YoY balance sheet changes** |
| **Tax Rate** | Effective rate from tax expense/EBT | Revenue-based calculation (tax expense/revenue) |
| **Net Borrowing** | Separate debt issued/repaid tracking | Estimated from total financing CF |
| **Caching** | Comprehensive metric caching | No caching system |
| **Data Integration** | FY + LTM combined timeline | Individual year processing |
| **Error Handling** | Robust validation and fallbacks | **✅ Enhanced - strict validation, no fallbacks** |
| **Currency** | Native values | 1M multiplier applied |

**✅ Major Improvement**: Both implementations now use the same working capital calculation methodology, ensuring consistent and accurate FCF calculations across all interfaces. Balance sheet data is required for all FCF calculations - no simplified fallbacks are used.

## Usage and Applications

### **Primary Use Cases**

1. **DCF Valuation**: FCFF values feed into enterprise valuation models
2. **Credit Analysis**: FCFE shows cash available to equity holders
3. **Operational Assessment**: LFCF measures core cash generation
4. **Trend Analysis**: Multi-year FCF patterns for growth rate estimation
5. **Sensitivity Analysis**: Multiple scenarios with different assumptions

### **Integration with Other Modules**

- **`dcf_valuation.py`**: Uses FCFF for enterprise value calculations
- **`data_processing.py`**: Creates FCF visualization charts
- **`fcf_analysis_streamlit.py`**: Provides interactive web interface
- **Growth Analysis**: Calculates 1, 3, 5, and 10-year FCF growth rates

This comprehensive FCF calculation system provides robust, accurate, and efficient cash flow analysis across multiple methodologies, supporting sophisticated financial valuation and analysis workflows.