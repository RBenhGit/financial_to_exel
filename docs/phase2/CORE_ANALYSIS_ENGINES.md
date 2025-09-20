# Core Analysis Engines Documentation

## Overview

Phase 2's core analysis engines provide comprehensive financial valuation capabilities through specialized, modular components. Each engine focuses on a specific valuation methodology while integrating seamlessly with the centralized `FinancialCalculator` system.

## 1. FinancialCalculator - Central Engine

**Location**: `core/analysis/engines/financial_calculations.py`

### Purpose
The central calculation engine that orchestrates all financial calculations and provides a unified interface for data loading, processing, and analysis.

### Key Features

#### **Multi-Type FCF Calculations**
```python
# FCFE (Free Cash Flow to Equity)
fcfe = calculator.calculate_fcfe(ticker)
# Formula: Net Income + Depreciation - CapEx - ΔWorking Capital - Net Debt Payments

# FCFF (Free Cash Flow to Firm)
fcff = calculator.calculate_fcff(ticker)
# Formula: EBIT(1-Tax Rate) + Depreciation - CapEx - ΔWorking Capital

# Levered FCF
levered_fcf = calculator.calculate_levered_fcf(ticker)
# Formula: FCFE considering debt financing effects
```

#### **Automated Data Loading**
```python
# Excel-based financial statement processing
calculator = FinancialCalculator(ticker="AAPL")
financial_data = calculator.load_financial_data()

# Supports multiple file formats:
# - Income Statement.xlsx
# - Balance Sheet.xlsx
# - Cash Flow Statement.xlsx
```

#### **Multi-Source Integration**
```python
# Enhanced data manager with API fallbacks
calculator.enable_api_integration()
data = calculator.get_comprehensive_data(
    sources=['excel', 'yfinance', 'alpha_vantage']
)
```

### Data Validation & Quality Control
- **Automatic Validation**: Checks for data consistency and completeness
- **Error Recovery**: Intelligent fallback mechanisms when data is missing
- **Quality Scoring**: Assigns quality scores to data sources
- **Currency Handling**: Multi-currency support with exchange rate conversion

---

## 2. DCF (Discounted Cash Flow) Engine

**Location**: `core/analysis/dcf/dcf_valuation.py`

### Purpose
Comprehensive DCF valuation with multiple terminal value methods and sensitivity analysis capabilities.

### Key Components

#### **DCF Models Supported**
1. **FCFE Model**: Free Cash Flow to Equity approach
2. **FCFF Model**: Free Cash Flow to Firm approach
3. **Levered FCF Model**: Debt-adjusted cash flow modeling

#### **Terminal Value Calculation Methods**
```python
# 1. Perpetual Growth Method
terminal_value = calculator.terminal_value_perpetual_growth(
    final_fcf=1000000,
    growth_rate=0.03,
    discount_rate=0.10
)

# 2. Exit Multiple Method
terminal_value = calculator.terminal_value_exit_multiple(
    final_metric=500000,  # Revenue, EBITDA, etc.
    exit_multiple=15.0
)

# 3. H-Model (Two-stage growth)
terminal_value = calculator.h_model_terminal_value(
    initial_growth=0.15,
    long_term_growth=0.03,
    transition_period=10
)
```

#### **Advanced Features**
- **Monte Carlo Integration**: Probabilistic analysis with uncertainty modeling
- **Sensitivity Analysis**: Parameter sensitivity across key variables
- **Scenario Modeling**: Best/Base/Worst case analysis
- **WACC Calculation**: Automated cost of capital computation

### Example Usage
```python
from core.analysis.dcf.dcf_valuation import DCFValuator

# Initialize DCF analysis
dcf = DCFValuator(ticker="AAPL")

# Run comprehensive DCF analysis
dcf_results = dcf.calculate_dcf_valuation(
    projection_years=10,
    terminal_growth_rate=0.03,
    discount_rate=0.10
)

# Results include:
# - Present value of projected cash flows
# - Terminal value
# - Enterprise value
# - Equity value per share
```

---

## 3. DDM (Dividend Discount Model) Engine

**Location**: `core/analysis/ddm/ddm_valuation.py`

### Purpose
Sophisticated dividend discount modeling with automatic model selection based on dividend patterns and company characteristics.

### Supported DDM Models

#### **1. Gordon Growth Model (Single-Stage)**
```python
# Constant growth dividend model
ddm_value = calculator.gordon_growth_model(
    current_dividend=2.50,
    growth_rate=0.05,
    required_return=0.10
)
# Formula: D1 / (r - g)
```

#### **2. Two-Stage Growth Model**
```python
# High growth followed by stable growth
ddm_value = calculator.two_stage_ddm(
    current_dividend=2.50,
    high_growth_rate=0.15,
    high_growth_periods=5,
    stable_growth_rate=0.05,
    required_return=0.10
)
```

#### **3. H-Model (Variable Growth)**
```python
# Gradual transition from high to stable growth
ddm_value = calculator.h_model_ddm(
    current_dividend=2.50,
    initial_growth=0.15,
    long_term_growth=0.05,
    transition_period=10,
    required_return=0.10
)
```

### Advanced DDM Features

#### **Automatic Model Selection**
```python
# Analyzes dividend history to select optimal model
recommended_model = calculator.recommend_ddm_model(ticker="KO")
# Considers: dividend stability, growth patterns, payout ratios
```

#### **Dividend Sustainability Analysis**
```python
# Evaluates dividend sustainability
sustainability = calculator.analyze_dividend_sustainability(
    ticker="JNJ",
    years_analysis=10
)
# Includes: payout ratio trends, earnings coverage, free cash flow coverage
```

#### **Risk-Adjusted Returns**
```python
# Beta-based risk adjustments
risk_adjusted_return = calculator.calculate_required_return(
    risk_free_rate=0.03,
    market_return=0.10,
    beta=1.2
)
```

---

## 4. P/B (Price-to-Book) Analysis Engine

**Location**: `core/analysis/pb/pb_calculation_engine.py`

### Purpose
Comprehensive P/B ratio analysis with historical trending, industry comparisons, and fair value estimations.

### Key Features

#### **Historical P/B Analysis**
```python
from core.analysis.pb.pb_calculation_engine import PBCalculationEngine

# Multi-year P/B trend analysis
pb_engine = PBCalculationEngine(ticker="AAPL")
historical_analysis = pb_engine.analyze_historical_pb(years=10)

# Results include:
# - Historical P/B ratios
# - Trend analysis
# - Statistical measures (mean, median, std dev)
# - Confidence intervals
```

#### **Industry Benchmarking**
```python
# Industry peer comparison
industry_analysis = pb_engine.industry_pb_comparison(
    ticker="AAPL",
    industry_peers=["GOOGL", "MSFT", "META"]
)
```

#### **Fair Value Estimation**
```python
# P/B-based fair value calculation
fair_value = pb_engine.calculate_pb_fair_value(
    book_value_per_share=25.00,
    historical_average_pb=3.5,
    current_pb=4.2
)
```

#### **Statistical Analysis**
```python
# Advanced statistical validation
stats = pb_engine.statistical_analysis(
    ticker="AAPL",
    confidence_level=0.95
)
# Includes: regression analysis, correlation studies, outlier detection
```

### P/B Engine Components

#### **1. Fair Value Calculator**
**Location**: `core/analysis/pb/pb_fair_value_calculator.py`
- Book value-based valuation
- Historical P/B averaging
- Industry-adjusted valuations
- Risk-premium adjustments

#### **2. Statistical Analysis Module**
**Location**: `core/analysis/pb/pb_statistical_analysis.py`
- Regression analysis
- Confidence interval calculations
- Trend significance testing
- Outlier detection and handling

#### **3. Enhanced Analysis Framework**
**Location**: `core/analysis/pb/pb_enhanced_analysis.py`
- Multi-factor P/B modeling
- Economic cycle adjustments
- Quality score integration
- Performance attribution

---

## Integration & Usage Patterns

### **Unified Engine Access**
```python
from core.analysis.engines.financial_calculations import FinancialCalculator

# Single point of access for all calculations
calculator = FinancialCalculator(ticker="AAPL")

# Access all engines through unified interface
dcf_value = calculator.get_dcf_valuation()
ddm_value = calculator.get_ddm_valuation()
pb_analysis = calculator.get_pb_analysis()
```

### **Multi-Model Comparison**
```python
# Comprehensive valuation comparison
valuation_summary = calculator.comprehensive_valuation_analysis()
# Returns: DCF, DDM, P/B values with confidence metrics
```

### **Performance Optimization**
- **Caching**: Intelligent caching of expensive calculations
- **Parallel Processing**: Concurrent data fetching and calculations
- **Lazy Loading**: On-demand calculation execution
- **Memory Management**: Efficient memory usage for large datasets

### **Error Handling & Validation**
- **Data Quality Checks**: Comprehensive data validation
- **Graceful Degradation**: Fallback mechanisms for missing data
- **Detailed Logging**: Comprehensive audit trail
- **User Notifications**: Clear error messages and recommendations

---

## Testing & Validation

Each engine includes comprehensive test coverage:
- **Unit Tests**: Individual method and function testing
- **Integration Tests**: Cross-engine interaction testing
- **Performance Tests**: Load and stress testing
- **Accuracy Tests**: Validation against known benchmarks

### Test Locations
- `tests/unit/dcf/` - DCF engine tests
- `tests/unit/ddm/` - DDM engine tests
- `tests/unit/pb/` - P/B analysis tests
- `tests/integration/engines/` - Cross-engine integration tests

---

*The core analysis engines represent the technical foundation of Phase 2's advanced financial analysis capabilities, providing professional-grade valuation tools with institutional-quality accuracy and reliability.*