# Data Flow Architecture Standardization & Composite Variable Generation
## Product Requirements Document (PRD)

---

## Document Information
- **Version**: 1.0
- **Date**: 2025-10-18
- **Author**: Financial Analysis Platform Team
- **Status**: Draft

---

## Executive Summary

This PRD formalizes the data flow architecture depicted in `docs/architecture/data_flow_design.png` to create a robust, standardized financial data processing pipeline. The core principle is: **"All adapters (API and Excel) must conform to the same global (general) dictionary variables"** ensuring consistent, traceable data flow through four distinct stages: Data Import → Infrastructure → Data Analysis → Data Export.

### Vision
Create a unified data processing architecture where:
- Every data source adapter outputs to a standardized GeneralizedVariableDict
- Composite variables are automatically generated from base variables
- All analysis components consume exclusively from the centralized VarInputData
- Export components provide consistent reporting from a single source of truth

---

## Problem Statement

### Current State Issues

1. **Adapter Inconsistency**
   - Different adapters use different output formats
   - Field naming conventions vary by source (yfinance vs FMP vs Excel)
   - No enforced contract for adapter output structure
   - Manual field mapping required in multiple locations

2. **Missing Composite Variable Generation**
   - Derived variables calculated ad-hoc throughout codebase
   - No centralized definition of variable dependencies
   - Duplicate calculation logic across modules
   - No automatic update when base variables change

3. **Infrastructure Bypass**
   - Some components access raw data directly
   - Analysis engines sometimes bypass VarInputData
   - Display components occasionally fetch data from multiple sources
   - No enforcement of single source of truth principle

4. **Data Flow Opacity**
   - Difficult to trace data from source to display
   - No clear separation of concerns between layers
   - Validation happens at multiple points inconsistently
   - Quality metrics not propagated through pipeline

### Impact

- **Development Friction**: Adding new data sources requires changes in multiple locations
- **Data Quality Risk**: Inconsistent validation leads to potential errors
- **Maintenance Burden**: Scattered calculation logic difficult to maintain
- **Testing Complexity**: No clear contracts make comprehensive testing challenging
- **Performance Issues**: Duplicate calculations and redundant data transformations

---

## Success Criteria

### Technical Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Adapter Interface Compliance | ~60% | 100% | All adapters implement BaseAdapter contract |
| Composite Variable Coverage | 0% | 90% | Derived variables auto-generated from dependencies |
| Infrastructure Bypass Incidents | ~15 locations | 0 | Zero direct data access outside VarInputData |
| Data Flow Traceability | Partial | Complete | Full lineage from source → export |
| Calculation Duplication | ~40% | <5% | Single calculation definition per metric |
| Test Coverage (Data Flow) | ~70% | >95% | End-to-end integration tests |

### Business Success Metrics

- **Time to Add New Data Source**: <4 hours (from current ~2 days)
- **Variable Addition Time**: <30 minutes (from current ~3 hours)
- **Data Quality Confidence**: >99% accuracy (from current ~92%)
- **Developer Onboarding**: <2 days to full productivity (from current ~1 week)

---

## Architecture Overview

### Four-Stage Data Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Stage 1:    │      │  Stage 2:    │      │  Stage 3:    │      │  Stage 4:    │
│ Data Import  │─────▶│Infrastructure│─────▶│Data Analysis │─────▶│ Data Export  │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
       │                     │                     │                     │
   Raw Data          Standardized           Calculated            Formatted
   Acquisition         Storage               Results              Outputs
```

### Stage 1: Data Import Layer

**Purpose**: Acquire raw data from diverse sources and transform to standardized format

**Components**:
- Raw Data Sources (Excel files, yfinance, FMP, Alpha Vantage, Polygon)
- Adapter Functions (Source-specific import logic)
- Field Mapping Engines (Source aliases → Standard names)

**Output**: GeneralizedVariableDict with standardized field names

**Key Requirement**: **All adapters MUST output identical dictionary structure**

### Stage 2: Infrastructure Layer

**Purpose**: Central storage, validation, and composite variable generation

**Components**:
- **Generalized Variables Dictionary**: Canonical schema definition
- **FinancialVariableRegistry**: Variable metadata and validation rules
- **VarInputData**: Singleton storage system
- **Generate Composite Variables**: Dependency-based calculation engine
- **UniversalDataRegistry**: Multi-layer caching system

**Key Requirement**: **Single source of truth for all financial data**

### Stage 3: Data Analysis Layer

**Purpose**: Perform financial analysis using standardized data

**Components**:
- Analysis Engines (DCF, DDM, P/B, FCF, Ratios)
- Calculation Engines (Financial metrics, ratios)
- Graphs and Tables Display Functions

**Key Requirement**: **All components consume ONLY from VarInputData**

### Stage 4: Data Export Layer

**Purpose**: Format and export analysis results

**Components**:
- Create Report and Exports
- Streamlit UI Components
- Excel Export Functions
- JSON/CSV Export Utilities

**Key Requirement**: **Consistent formatting from single data source**

---

## Detailed Requirements

## 1. Adapter Interface Standardization

### 1.1 BaseAdapter Contract

**Requirement**: All adapters MUST implement the standardized `BaseAdapter` interface

**Interface Definition**:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AdapterOutputMetadata:
    """Metadata accompanying adapter output"""
    source: str                    # "excel", "yfinance", "fmp", etc.
    timestamp: datetime            # When data was acquired
    quality_score: float          # 0.0 - 1.0 data quality metric
    completeness: float           # 0.0 - 1.0 field completeness
    validation_errors: List[str]  # Any validation issues encountered
    raw_data_hash: str            # Hash of raw input for change detection

class BaseAdapter(ABC):
    """
    Base adapter interface that ALL data source adapters must implement.
    Ensures consistent output format regardless of source.
    """

    @abstractmethod
    def extract_variables(
        self,
        ticker: str,
        period: str = "latest",
        years: int = 10
    ) -> Dict[str, Any]:
        """
        Extract financial variables from source and return standardized dict.

        Returns:
            GeneralizedVariableDict with keys matching FinancialVariableRegistry

        Raises:
            AdapterException: On extraction or transformation failures
        """
        pass

    @abstractmethod
    def get_metadata(self) -> AdapterOutputMetadata:
        """Return metadata about most recent extraction"""
        pass

    @abstractmethod
    def validate_output(self, variables: Dict[str, Any]) -> ValidationResult:
        """
        Validate output conforms to GeneralizedVariableDict schema

        Must check:
        - All keys exist in FinancialVariableRegistry
        - Data types match variable definitions
        - Units are correct and normalized
        - Required fields are present
        """
        pass

    @abstractmethod
    def get_supported_categories(self) -> List[str]:
        """Return list of VariableCategory this adapter supports"""
        pass
```

### 1.2 GeneralizedVariableDict Schema

**Requirement**: Define canonical output format for all adapters

**Schema Definition**:

```python
from typing import TypedDict, Optional, List
from datetime import date

class GeneralizedVariableDict(TypedDict, total=False):
    """
    Standardized output format for all adapters.

    Keys are standardized variable names from FinancialVariableRegistry.
    Values are normalized to standard units (millions USD, percentages as decimals).

    All adapters MUST transform their source-specific fields to this format.
    """

    # === METADATA (Required) ===
    ticker: str                          # Company ticker symbol
    company_name: str                    # Full company name
    currency: str                        # "USD", "EUR", etc.
    fiscal_year_end: str                 # "December", "June", etc.

    # === INCOME STATEMENT (Millions USD) ===
    revenue: Optional[float]
    cost_of_revenue: Optional[float]
    gross_profit: Optional[float]
    operating_expenses: Optional[float]
    research_and_development: Optional[float]
    selling_general_administrative: Optional[float]
    operating_income: Optional[float]
    interest_expense: Optional[float]
    interest_income: Optional[float]
    other_income_expense: Optional[float]
    income_before_tax: Optional[float]
    income_tax_expense: Optional[float]
    net_income: Optional[float]
    net_income_continuing_ops: Optional[float]
    eps_basic: Optional[float]
    eps_diluted: Optional[float]
    weighted_average_shares_basic: Optional[float]
    weighted_average_shares_diluted: Optional[float]
    ebitda: Optional[float]
    ebit: Optional[float]

    # === BALANCE SHEET (Millions USD) ===
    cash_and_cash_equivalents: Optional[float]
    short_term_investments: Optional[float]
    accounts_receivable: Optional[float]
    inventory: Optional[float]
    other_current_assets: Optional[float]
    total_current_assets: Optional[float]
    property_plant_equipment_net: Optional[float]
    goodwill: Optional[float]
    intangible_assets: Optional[float]
    long_term_investments: Optional[float]
    other_non_current_assets: Optional[float]
    total_non_current_assets: Optional[float]
    total_assets: Optional[float]
    accounts_payable: Optional[float]
    short_term_debt: Optional[float]
    current_portion_long_term_debt: Optional[float]
    accrued_liabilities: Optional[float]
    deferred_revenue_current: Optional[float]
    other_current_liabilities: Optional[float]
    total_current_liabilities: Optional[float]
    long_term_debt: Optional[float]
    deferred_revenue_non_current: Optional[float]
    deferred_tax_liabilities: Optional[float]
    other_non_current_liabilities: Optional[float]
    total_non_current_liabilities: Optional[float]
    total_liabilities: Optional[float]
    common_stock: Optional[float]
    retained_earnings: Optional[float]
    accumulated_other_comprehensive_income: Optional[float]
    total_stockholders_equity: Optional[float]
    total_liabilities_and_equity: Optional[float]

    # === CASH FLOW STATEMENT (Millions USD) ===
    net_income_cash_flow: Optional[float]
    depreciation_and_amortization: Optional[float]
    stock_based_compensation: Optional[float]
    change_in_working_capital: Optional[float]
    change_in_accounts_receivable: Optional[float]
    change_in_inventory: Optional[float]
    change_in_accounts_payable: Optional[float]
    other_operating_activities: Optional[float]
    operating_cash_flow: Optional[float]
    capital_expenditures: Optional[float]
    acquisitions: Optional[float]
    purchases_of_investments: Optional[float]
    sales_of_investments: Optional[float]
    other_investing_activities: Optional[float]
    investing_cash_flow: Optional[float]
    debt_repayment: Optional[float]
    debt_issuance: Optional[float]
    common_stock_issued: Optional[float]
    common_stock_repurchased: Optional[float]
    dividends_paid: Optional[float]
    other_financing_activities: Optional[float]
    financing_cash_flow: Optional[float]
    net_change_in_cash: Optional[float]
    free_cash_flow: Optional[float]

    # === MARKET DATA ===
    stock_price: Optional[float]
    market_cap: Optional[float]
    enterprise_value: Optional[float]
    shares_outstanding: Optional[float]
    beta: Optional[float]
    dividend_yield: Optional[float]           # As decimal (0.025 = 2.5%)
    dividend_per_share: Optional[float]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_sales: Optional[float]
    price_to_book: Optional[float]
    ev_to_revenue: Optional[float]
    ev_to_ebitda: Optional[float]

    # === HISTORICAL DATA (Lists of values) ===
    historical_revenue: Optional[List[float]]
    historical_net_income: Optional[List[float]]
    historical_operating_cash_flow: Optional[List[float]]
    historical_free_cash_flow: Optional[List[float]]
    historical_eps: Optional[List[float]]
    historical_dates: Optional[List[date]]
```

### 1.3 Field Mapping Requirements

**Requirement**: Each adapter maintains source-specific field mappings

**Implementation Strategy**:

1. **Centralized Alias Registry**: FinancialVariableRegistry stores source aliases
   ```python
   registry.register_variable(
       name="revenue",
       aliases={
           "yfinance": "totalRevenue",
           "fmp": "revenue",
           "alpha_vantage": "totalRevenue",
           "polygon": "revenues",
           "excel": ["Revenue", "Total Revenue", "Sales"]
       }
   )
   ```

2. **Adapter Field Resolution**:
   ```python
   class ExcelAdapter(BaseAdapter):
       def _resolve_field(self, variable_name: str) -> Optional[str]:
           """Find Excel column matching variable"""
           var_def = registry.get_variable_definition(variable_name)
           excel_aliases = var_def.aliases.get("excel", [])

           for alias in excel_aliases:
               if alias in self.excel_columns:
                   return alias
           return None
   ```

3. **Unit Normalization**: Convert all values to standard units
   - Millions USD for currency values
   - Decimals for percentages (0.15 = 15%)
   - Shares in actual count or millions (document in metadata)

### 1.4 Adapter Validation Framework

**Requirement**: Automated validation of adapter outputs

**Components**:

```python
class AdapterValidator:
    """Validates adapter output conforms to standards"""

    def validate_schema(self, output: Dict) -> ValidationResult:
        """Check all keys are valid variable names"""
        registry = get_registry()
        invalid_keys = [
            key for key in output.keys()
            if not registry.has_variable(key)
        ]
        return ValidationResult(
            valid=len(invalid_keys) == 0,
            errors=[f"Unknown variable: {key}" for key in invalid_keys]
        )

    def validate_data_types(self, output: Dict) -> ValidationResult:
        """Check values match expected types"""
        errors = []
        registry = get_registry()

        for key, value in output.items():
            var_def = registry.get_variable_definition(key)
            if not self._type_matches(value, var_def.data_type):
                errors.append(
                    f"{key}: expected {var_def.data_type}, got {type(value)}"
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_units(self, output: Dict) -> ValidationResult:
        """Check values are in correct units"""
        # Implementation checks magnitude, currency codes, etc.
        pass

    def validate_completeness(self, output: Dict) -> ValidationResult:
        """Check required fields are present"""
        required_fields = ["ticker", "company_name", "currency"]
        missing = [f for f in required_fields if f not in output]

        return ValidationResult(
            valid=len(missing) == 0,
            errors=[f"Missing required field: {f}" for f in missing]
        )
```

### 1.5 Adapter Compliance Checklist

**Requirement**: Every adapter must pass compliance verification

**Checklist**:

- [ ] Implements `BaseAdapter` interface
- [ ] `extract_variables()` returns `GeneralizedVariableDict`
- [ ] `get_metadata()` provides complete metadata
- [ ] `validate_output()` checks all requirements
- [ ] All field names match FinancialVariableRegistry
- [ ] All units normalized to standard (millions USD, decimals)
- [ ] Source-specific aliases registered in registry
- [ ] Quality score calculation implemented
- [ ] Error handling with proper exceptions
- [ ] Logging for debugging and auditing
- [ ] Unit tests with 95%+ coverage
- [ ] Integration tests with real data
- [ ] Documentation with usage examples
- [ ] Performance benchmarks documented

---

## 2. Composite Variable Generation Infrastructure

### 2.1 Composite Variable Definition

**Definition**: Composite variables are financial metrics derived from base variables using defined formulas.

**Examples**:
- `gross_margin = (gross_profit / revenue) * 100`
- `current_ratio = total_current_assets / total_current_liabilities`
- `roe = net_income / total_stockholders_equity`
- `free_cash_flow = operating_cash_flow - capital_expenditures`

### 2.2 Variable Dependency Graph

**Requirement**: Explicit dependency declaration for calculation ordering

**Implementation**:

```python
@dataclass
class CompositeVariableDefinition:
    """Definition of a composite (calculated) variable"""
    name: str
    category: VariableCategory
    dependencies: List[str]  # Variable names this depends on
    formula: str            # Human-readable formula
    calculator: Callable    # Function to calculate value
    units: Units
    description: str
    validation_rules: List[ValidationRule]

    def can_calculate(self, available_vars: Set[str]) -> bool:
        """Check if all dependencies are available"""
        return all(dep in available_vars for dep in self.dependencies)

# Example registration
registry.register_composite_variable(
    CompositeVariableDefinition(
        name="gross_margin",
        category=VariableCategory.RATIOS,
        dependencies=["gross_profit", "revenue"],
        formula="(gross_profit / revenue) * 100",
        calculator=lambda data: (data["gross_profit"] / data["revenue"]) * 100
                                if data["revenue"] != 0 else None,
        units=Units.PERCENTAGE,
        description="Gross profit as percentage of revenue",
        validation_rules=[
            RangeValidation(min_value=-100, max_value=100)
        ]
    )
)
```

### 2.3 Composite Variable Calculator Engine

**Requirement**: Automatic generation of composite variables when base data changes

**Architecture**:

```python
class CompositeVariableCalculator:
    """
    Calculates composite variables based on dependency graph.
    Ensures calculation order respects dependencies.
    """

    def __init__(self, registry: FinancialVariableRegistry):
        self.registry = registry
        self.dependency_graph = self._build_dependency_graph()
        self.calculation_order = self._topological_sort()

    def _build_dependency_graph(self) -> nx.DiGraph:
        """Build directed graph of variable dependencies"""
        graph = nx.DiGraph()

        for var in self.registry.get_composite_variables():
            graph.add_node(var.name)
            for dep in var.dependencies:
                graph.add_edge(dep, var.name)

        return graph

    def _topological_sort(self) -> List[str]:
        """Determine safe calculation order"""
        try:
            return list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXError:
            raise ValueError("Circular dependency detected in composite variables")

    def calculate_all(
        self,
        base_data: Dict[str, Any],
        ticker: str
    ) -> Dict[str, Any]:
        """
        Calculate all possible composite variables given base data.

        Args:
            base_data: GeneralizedVariableDict with base variables
            ticker: Company ticker for context

        Returns:
            Dict of calculated composite variables
        """
        available_vars = set(base_data.keys())
        calculated = {}

        for var_name in self.calculation_order:
            var_def = self.registry.get_composite_variable(var_name)

            # Skip if dependencies not available
            if not var_def.can_calculate(available_vars):
                logger.debug(
                    f"Skipping {var_name}: missing dependencies "
                    f"{set(var_def.dependencies) - available_vars}"
                )
                continue

            # Calculate value
            try:
                value = var_def.calculator({
                    **base_data,
                    **calculated  # Include previously calculated composites
                })

                # Validate result
                validation = var_def.validate(value)
                if not validation.valid:
                    logger.warning(
                        f"{ticker} {var_name} validation failed: "
                        f"{validation.errors}"
                    )
                    continue

                calculated[var_name] = value
                available_vars.add(var_name)

            except Exception as e:
                logger.error(
                    f"Error calculating {var_name} for {ticker}: {e}"
                )

        return calculated

    def calculate_incremental(
        self,
        base_data: Dict[str, Any],
        changed_variables: Set[str]
    ) -> Dict[str, Any]:
        """
        Calculate only composite variables affected by changes.
        Optimization for updates to existing data.
        """
        affected = self._find_affected_variables(changed_variables)
        # Calculate only affected variables in dependency order
        pass

    def _find_affected_variables(self, changed: Set[str]) -> Set[str]:
        """Find all composite variables that depend on changed variables"""
        affected = set()

        for var_name in changed:
            # Find all descendants in dependency graph
            if var_name in self.dependency_graph:
                descendants = nx.descendants(self.dependency_graph, var_name)
                affected.update(descendants)

        return affected
```

### 2.4 Standard Composite Variables

**Requirement**: Define standard financial metrics as composite variables

**Categories**:

**Profitability Ratios**:
- `gross_margin` = (gross_profit / revenue) × 100
- `operating_margin` = (operating_income / revenue) × 100
- `net_margin` = (net_income / revenue) × 100
- `roe` = net_income / total_stockholders_equity
- `roa` = net_income / total_assets
- `roic` = nopat / invested_capital

**Liquidity Ratios**:
- `current_ratio` = total_current_assets / total_current_liabilities
- `quick_ratio` = (current_assets - inventory) / current_liabilities
- `cash_ratio` = cash_and_equivalents / current_liabilities
- `working_capital` = current_assets - current_liabilities

**Leverage Ratios**:
- `debt_to_equity` = total_debt / total_equity
- `debt_to_assets` = total_debt / total_assets
- `interest_coverage` = operating_income / interest_expense
- `debt_service_coverage` = operating_income / (interest + principal)

**Cash Flow Metrics**:
- `fcf` = operating_cash_flow - capital_expenditures
- `fcfe` = fcf - net_borrowing + interest × (1 - tax_rate)
- `fcff` = fcf + interest × (1 - tax_rate)
- `cash_conversion_cycle` = days_sales_outstanding + days_inventory - days_payable

**Valuation Metrics**:
- `ev` = market_cap + total_debt - cash
- `ev_to_ebitda` = enterprise_value / ebitda
- `ev_to_revenue` = enterprise_value / revenue
- `price_to_sales` = market_cap / revenue
- `price_to_book` = market_cap / book_value

**Growth Metrics**:
- `revenue_growth_yoy` = (revenue_current - revenue_prior) / revenue_prior
- `eps_growth_yoy` = (eps_current - eps_prior) / eps_prior
- `fcf_growth_yoy` = (fcf_current - fcf_prior) / fcf_prior

### 2.5 Integration with VarInputData

**Requirement**: Composite variables automatically stored in VarInputData

**Implementation**:

```python
class VarInputData:
    """Enhanced with composite variable generation"""

    def set_base_variables(
        self,
        ticker: str,
        variables: GeneralizedVariableDict,
        source: str,
        period: str = "latest"
    ) -> None:
        """
        Store base variables and trigger composite calculation.

        Workflow:
        1. Store base variables
        2. Calculate composite variables
        3. Store composite variables
        4. Emit data change events
        """
        # Store base variables
        for var_name, value in variables.items():
            self._store_variable(
                ticker=ticker,
                name=var_name,
                value=value,
                source=source,
                period=period,
                variable_type="base"
            )

        # Calculate and store composite variables
        composite_calc = CompositeVariableCalculator(get_registry())
        composite_vars = composite_calc.calculate_all(
            base_data=variables,
            ticker=ticker
        )

        for var_name, value in composite_vars.items():
            self._store_variable(
                ticker=ticker,
                name=var_name,
                value=value,
                source="calculated",
                period=period,
                variable_type="composite"
            )

        # Emit change events
        self._emit_data_change_event(
            ticker=ticker,
            changed_vars=list(variables.keys()),
            composite_vars=list(composite_vars.keys())
        )

        logger.info(
            f"{ticker}: Stored {len(variables)} base vars, "
            f"calculated {len(composite_vars)} composite vars"
        )
```

---

## 3. Infrastructure Layer Requirements

### 3.1 VarInputData as Single Source of Truth

**Requirement**: ALL data access must go through VarInputData

**Enforcement Strategy**:

1. **Code Analysis**: Static analysis to detect direct data access
2. **Deprecation Warnings**: Mark old data access patterns as deprecated
3. **API Gateway Pattern**: VarInputData as only public interface
4. **Testing**: Integration tests verify single source of truth

**Anti-Patterns to Eliminate**:

```python
# ❌ WRONG: Direct DataFrame access
revenue = yf_data.financials.loc["Total Revenue"]

# ❌ WRONG: Direct Excel read
revenue = excel_df.loc["Revenue", "2023"]

# ❌ WRONG: Direct API response access
revenue = api_response["totalRevenue"]

# ✅ CORRECT: Through VarInputData
var_data = get_var_input_data()
revenue = var_data.get_variable("AAPL", "revenue", period="2023")
```

### 3.2 Data Quality Propagation

**Requirement**: Quality metrics propagate through entire pipeline

**Implementation**:

```python
@dataclass
class VariableMetadata:
    """Metadata stored with every variable value"""
    source: str                # "excel", "yfinance", "calculated"
    timestamp: datetime        # When acquired/calculated
    quality_score: float      # 0.0-1.0
    confidence: float         # 0.0-1.0
    lineage: List[str]        # Chain of transformations
    validation_status: str    # "passed", "warning", "failed"
    calculation_dependencies: Optional[List[str]]  # For composite vars

class VarInputData:
    def get_variable_with_metadata(
        self,
        ticker: str,
        name: str,
        period: str = "latest"
    ) -> Tuple[Any, VariableMetadata]:
        """Return variable value and its metadata"""
        pass
```

### 3.3 Caching Strategy

**Requirement**: Multi-layer caching with invalidation

**Layers**:
1. **L1 Memory Cache**: Hot data (most recent period)
2. **L2 Disk Cache**: Historical data (10+ years)
3. **L3 API Cache**: Rate-limited external sources

**Invalidation Rules**:
- Base variable change → Invalidate dependent composite variables
- Source data refresh → Invalidate all derived values
- TTL expiration → Configurable per variable category

---

## 4. Data Analysis Layer Requirements

### 4.1 Analysis Engine Compliance

**Requirement**: All analysis engines consume exclusively from VarInputData

**Engine Categories**:

**Valuation Engines**:
- DCF Analysis (`core/analysis/dcf/`)
- DDM Analysis (`core/analysis/ddm/`)
- P/B Analysis (`core/analysis/pb/`)
- FCF Analysis (`core/analysis/fcf_consolidated.py`)

**Calculation Engines**:
- Financial Ratios (`core/analysis/engines/financial_ratios_engine.py`)
- Financial Calculations (`core/analysis/engines/financial_calculation_engine.py`)
- Ratio Analyzer (`core/analysis/ratios/ratio_analyzer.py`)

**Advanced Analytics**:
- Risk Analysis (`core/analysis/risk/`)
- Portfolio Analysis (`core/analysis/portfolio/`)
- ML Forecasting (`core/analysis/ml/`)

**Compliance Pattern**:

```python
class DCFValuation:
    """Example compliant analysis engine"""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.var_data = get_var_input_data()

    def calculate_intrinsic_value(
        self,
        projection_years: int = 5
    ) -> Dict[str, Any]:
        """Calculate DCF intrinsic value"""

        # ✅ CORRECT: Get all data from VarInputData
        fcf_history = self.var_data.get_historical_data(
            ticker=self.ticker,
            variable="free_cash_flow",
            years=10
        )

        wacc = self.var_data.get_variable(
            ticker=self.ticker,
            variable="wacc"
        )

        terminal_growth = self.var_data.get_variable(
            ticker=self.ticker,
            variable="terminal_growth_rate"
        )

        # Perform calculations...
        intrinsic_value = self._calculate_dcf(
            fcf_history, wacc, terminal_growth
        )

        # ✅ CORRECT: Store results back to VarInputData
        self.var_data.set_variable(
            ticker=self.ticker,
            variable="dcf_intrinsic_value",
            value=intrinsic_value,
            source="dcf_analysis"
        )

        return {"intrinsic_value": intrinsic_value}
```

### 4.2 Results Storage

**Requirement**: Analysis results stored back in VarInputData

**Pattern**:
```python
# Analysis produces results
results = dcf_engine.calculate()

# Store in VarInputData with source attribution
for metric, value in results.items():
    var_data.set_variable(
        ticker=ticker,
        variable=metric,
        value=value,
        source="dcf_analysis",
        metadata={
            "analysis_date": datetime.now(),
            "assumptions": assumptions_used
        }
    )
```

---

## 5. Data Export Layer Requirements

### 5.1 Unified Export Interface

**Requirement**: All exports pull from VarInputData

**Export Formats**:
- Streamlit UI Components
- Excel Reports
- JSON/CSV Data Dumps
- PDF Reports
- REST API Responses

**Export Pattern**:

```python
class StreamlitExporter:
    """Example export component"""

    def display_financial_metrics(self, ticker: str):
        """Display metrics in Streamlit"""
        var_data = get_var_input_data()

        # Get all metrics from single source
        metrics = {
            "Revenue": var_data.get_variable(ticker, "revenue"),
            "Net Income": var_data.get_variable(ticker, "net_income"),
            "Free Cash Flow": var_data.get_variable(ticker, "free_cash_flow"),
            "Gross Margin": var_data.get_variable(ticker, "gross_margin"),
            "ROE": var_data.get_variable(ticker, "roe"),
        }

        # Display with consistent formatting
        for label, value in metrics.items():
            st.metric(label, self._format_value(value))
```

### 5.2 Consistent Formatting

**Requirement**: Standardized formatting across all exports

**Formatting Rules**:
- Currency: Millions USD with 2 decimal places
- Percentages: 2 decimal places
- Ratios: 3 decimal places
- Dates: ISO 8601 format
- Missing data: Consistent null representation

---

## 6. Migration Strategy

### 6.1 Current State Analysis

**Identification of Non-Compliant Code**:

```python
# Static analysis tool
class ComplianceAnalyzer:
    """Find code that bypasses VarInputData"""

    def find_direct_dataframe_access(self):
        """Search for .loc, .iloc, direct DataFrame operations"""
        pass

    def find_direct_api_calls(self):
        """Search for yfinance, requests calls outside adapters"""
        pass

    def find_hardcoded_calculations(self):
        """Search for calculations not using composite variables"""
        pass
```

**Current Violations** (estimated from codebase exploration):
- ~15 locations with direct DataFrame access
- ~8 analysis engines with mixed data access
- ~12 display components with embedded calculations
- ~20 duplicate calculation implementations

### 6.2 Migration Phases

**Phase 1: Adapter Standardization (Week 1-2)**
- Implement BaseAdapter for all sources
- Create GeneralizedVariableDict output
- Register field mappings in registry
- Validate adapter outputs
- Test with real data

**Phase 2: Composite Variable Infrastructure (Week 2-3)**
- Implement CompositeVariableCalculator
- Define standard composite variables
- Integrate with VarInputData
- Test calculation dependencies
- Performance optimization

**Phase 3: Analysis Engine Migration (Week 3-5)**
- Migrate DCF/DDM/P/B engines
- Migrate ratio calculators
- Migrate risk analysis
- Remove direct data access
- Comprehensive testing

**Phase 4: Display Layer Migration (Week 5-6)**
- Migrate Streamlit components
- Migrate Excel exports
- Migrate report generation
- Ensure consistent formatting
- UI/UX testing

**Phase 5: Cleanup & Optimization (Week 6-7)**
- Remove deprecated code
- Optimize caching
- Performance tuning
- Documentation updates
- Training materials

### 6.3 Backward Compatibility

**Strategy**: Gradual deprecation with adapters

```python
# Provide compatibility layer during transition
def get_revenue_old_way(ticker):
    """DEPRECATED: Use var_data.get_variable() instead"""
    warnings.warn(
        "Direct data access deprecated. Use VarInputData.",
        DeprecationWarning
    )
    var_data = get_var_input_data()
    return var_data.get_variable(ticker, "revenue")
```

---

## 7. Testing Strategy

### 7.1 Adapter Testing

**Unit Tests**:
- Field mapping correctness
- Unit normalization accuracy
- Error handling for malformed data
- Metadata generation

**Integration Tests**:
- Real Excel file processing
- Real API data extraction
- Schema validation
- Quality score calculation

**Test Coverage Target**: >95% for all adapters

### 7.2 End-to-End Data Flow Tests

**Test Scenarios**:

```python
def test_excel_to_streamlit_flow():
    """Test complete data flow: Excel → VarInputData → Streamlit"""
    # 1. Load Excel data
    adapter = ExcelAdapter()
    variables = adapter.extract_variables("AAPL", "data/AAPL_FY.xlsx")

    # 2. Store in VarInputData
    var_data = get_var_input_data()
    var_data.set_base_variables("AAPL", variables, source="excel")

    # 3. Verify composite variables calculated
    assert var_data.get_variable("AAPL", "gross_margin") is not None
    assert var_data.get_variable("AAPL", "roe") is not None

    # 4. Verify analysis can access data
    dcf = DCFValuation("AAPL")
    result = dcf.calculate_intrinsic_value()
    assert "intrinsic_value" in result

    # 5. Verify export gets consistent data
    exporter = StreamlitExporter()
    metrics = exporter.get_display_metrics("AAPL")
    assert metrics["revenue"] == variables["revenue"]

def test_api_to_analysis_flow():
    """Test API → VarInputData → Analysis → Export"""
    pass

def test_composite_variable_dependency():
    """Test composite variables calculate in correct order"""
    pass
```

### 7.3 Performance Testing

**Benchmarks**:
- Adapter extraction: <2 seconds for 10 years data
- Composite calculation: <500ms for 100+ variables
- VarInputData access: <10ms for cached data
- End-to-end flow: <10 seconds from source to display

---

## 8. Documentation Requirements

### 8.1 Developer Documentation

**Required Documents**:
1. **Adapter Development Guide**
   - How to create new adapter
   - Field mapping best practices
   - Testing requirements

2. **Composite Variable Guide**
   - How to define new composite variables
   - Dependency management
   - Validation rules

3. **Data Flow Architecture**
   - Detailed diagram with component interactions
   - Sequence diagrams for common operations
   - Error handling flows

4. **API Reference**
   - VarInputData methods
   - Registry methods
   - Adapter interfaces

### 8.2 Code Documentation

**Requirements**:
- All public methods have docstrings
- Type hints on all function signatures
- Usage examples in module docstrings
- Architecture decisions documented in ADR format

---

## 9. Success Metrics & Monitoring

### 9.1 Technical Metrics

**Data Flow Metrics**:
```python
class DataFlowMetrics:
    """Monitor data flow health"""

    adapter_success_rate: float      # % successful extractions
    composite_calculation_time: float # Average calculation time
    cache_hit_rate: float            # % data served from cache
    validation_failure_rate: float   # % validation failures
    data_freshness: timedelta        # Age of cached data
```

**Quality Metrics**:
- Data quality score distribution
- Validation failure reasons
- Missing data frequency
- Calculation errors by variable

### 9.2 Monitoring & Alerts

**Alerts**:
- Adapter failure rate >5%
- Composite calculation time >1 second
- Cache hit rate <70%
- Validation failure rate >10%
- Circular dependency detected

---

## 10. Risk Management

### 10.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Adapter output inconsistency | High | Medium | Strict schema validation, comprehensive tests |
| Circular dependencies | High | Low | Dependency graph validation at registration |
| Performance degradation | Medium | Medium | Benchmarking, incremental calculation, caching |
| Cache invalidation bugs | Medium | Medium | Thorough testing, conservative invalidation |
| Migration breaking changes | High | Medium | Gradual migration, compatibility layer |

### 10.2 Data Quality Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Source data errors | High | Multi-source validation, quality scoring |
| Unit conversion errors | High | Automated unit tests, value sanity checks |
| Missing data | Medium | Graceful degradation, clear null handling |
| Stale cached data | Medium | TTL policies, freshness monitoring |

---

## 11. Appendices

### Appendix A: Variable Naming Conventions

**Standard**: `snake_case` for all variable names

**Patterns**:
- Base metrics: `revenue`, `net_income`, `total_assets`
- Ratios: `debt_to_equity`, `price_to_book`
- Growth metrics: `revenue_growth_yoy`, `eps_growth_3y_cagr`
- Margins: `gross_margin`, `operating_margin`, `net_margin`
- Per-share: `eps_basic`, `book_value_per_share`
- Historical: `historical_revenue`, `historical_fcf`

### Appendix B: Data Sources Comparison

| Source | Coverage | Reliability | Cost | Rate Limit |
|--------|----------|-------------|------|------------|
| Excel | Custom | High | Free | N/A |
| yfinance | Good | Medium | Free | ~2000/hour |
| FMP | Excellent | High | $14-299/mo | 300-5000/min |
| Alpha Vantage | Good | High | Free-$50/mo | 5-1200/min |
| Polygon | Excellent | High | $29-399/mo | Variable |

### Appendix C: Glossary

- **Adapter**: Component that transforms source-specific data to GeneralizedVariableDict
- **Base Variable**: Raw data from source (revenue, assets, etc.)
- **Composite Variable**: Calculated from base variables (margins, ratios, etc.)
- **VarInputData**: Central storage singleton for all financial data
- **Registry**: Metadata catalog of all financial variables
- **Quality Score**: 0.0-1.0 metric of data reliability

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Author | Financial Platform Team | 2025-10-18 | |
| Technical Lead | | | |
| Product Manager | | | |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-18 | System | Initial draft |

---

**End of Document**
