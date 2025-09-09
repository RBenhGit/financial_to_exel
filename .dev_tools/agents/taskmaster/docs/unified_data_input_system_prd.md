# Unified Financial Data Input System (var_input_data) - Product Requirements Document

## Executive Summary

Create a centralized `var_input_data` system that serves as the single source of truth for all financial variables throughout the financial analysis application. This system will unify data input from both Excel files and API sources, providing a consistent interface for data access, calculation, and display.

## Problem Statement

Currently, financial data is scattered across multiple modules with different access patterns:
- Excel data loading has custom logic in various files
- API data fetching uses different patterns and variable names
- Financial calculations access data through multiple interfaces
- Display logic duplicates data access patterns
- No centralized definition of financial variables
- Inconsistent data validation and transformation

## Success Criteria

1. All financial variables accessible through single `var_input_data` interface
2. Transparent switching between Excel and API data sources
3. Calculated variables automatically stored in central system
4. Zero data duplication across the application
5. Consistent data validation and quality monitoring
6. Performance improvement through intelligent caching
7. Easy addition of new financial variables and data sources

## User Stories

### As a Developer
- I want to access any financial variable through `var_input_data.get_variable("revenue")` regardless of data source
- I want to add new calculated variables that automatically integrate with the display system
- I want consistent data validation across all data sources

### As a Financial Analyst
- I want to seamlessly switch between Excel and API data without changing analysis logic
- I want calculated metrics to be automatically available for display and further analysis
- I want confidence that all displayed data comes from the same validated source

## Technical Requirements

### Core Components

#### 1. Financial Variable Registry
**Purpose**: Define and manage all financial variables
**Location**: `core/data_processing/financial_variable_registry.py`
**Requirements**:
- Variable definitions with metadata (type, units, validation rules)
- Categorization by financial statement type
- Dependency mapping for calculated variables
- Variable aliases for different data sources

#### 2. var_input_data Core System
**Purpose**: Central variable storage and access
**Location**: `core/data_processing/var_input_data.py`
**Requirements**:
- Singleton pattern for global access
- Integration with Universal Data Registry
- Thread-safe operations
- Historical data management (10+ years)
- Real-time data updates

#### 3. Data Source Adapters
**Purpose**: Standardize data from different sources
**Requirements**:
- Excel adapter for FY/LTM file structures
- API adapters for yfinance, FMP, Alpha Vantage, Polygon
- Automatic field mapping to standard variables
- Data quality validation and scoring

#### 4. Variable Processor
**Purpose**: Transform raw data to standardized format
**Requirements**:
- Unit normalization (millions, billions, percentages)
- Data type conversion and validation
- Missing data handling and interpolation
- Historical data alignment and gap filling

#### 5. Calculation Engine Integration
**Purpose**: Store calculated results in var_input_data
**Requirements**:
- Dependency resolution for calculation order
- Incremental updates when base data changes
- Result caching and invalidation
- Performance monitoring

### Financial Variable Categories

#### Core Financial Statement Variables
- **Income Statement**: Revenue, Operating Income, Net Income, EPS, Operating Expenses, Interest Expense, Tax Expense
- **Balance Sheet**: Total Assets, Total Liabilities, Shareholders Equity, Current Assets, Current Liabilities, Long-term Debt, Cash and Cash Equivalents
- **Cash Flow Statement**: Operating Cash Flow, Investing Cash Flow, Financing Cash Flow, Capital Expenditures, Working Capital Changes

#### Market Data Variables
- Stock Price (Current, Historical)
- Market Capitalization
- Shares Outstanding
- Trading Volume
- Beta
- Dividend Yield

#### Calculated Ratios and Metrics
- **Profitability**: ROE, ROA, ROIC, Gross Margin, Operating Margin, Net Margin
- **Liquidity**: Current Ratio, Quick Ratio, Cash Ratio
- **Leverage**: Debt-to-Equity, Interest Coverage, Debt Service Coverage
- **Valuation**: P/E, P/B, EV/EBITDA, P/S, PEG

#### Free Cash Flow Variants
- FCFF (Free Cash Flow to Firm)
- FCFE (Free Cash Flow to Equity)
- LFCF (Levered Free Cash Flow)
- Unlevered Free Cash Flow

#### DCF and Valuation Components
- WACC (Weighted Average Cost of Capital)
- Terminal Growth Rate
- Discount Rate
- Terminal Value
- Present Value of Cash Flows
- Intrinsic Value per Share

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
**Objective**: Establish foundational components

#### Tasks:
1. Create FinancialVariableRegistry class with variable definitions
2. Implement var_input_data core storage system
3. Define all current financial variables from codebase analysis
4. Create variable metadata schema
5. Implement basic variable validation rules
6. Set up unit tests for core components

### Phase 2: Excel Integration (Week 2)
**Objective**: Integrate Excel data sources

#### Tasks:
1. Create Excel data source adapter
2. Map Excel column headers to standard variable names
3. Handle 10-year FY data structure
4. Handle LTM data structure
5. Implement Excel data validation
6. Create Excel data transformation pipeline
7. Test with existing Excel files

### Phase 3: API Integration (Week 3)
**Objective**: Integrate API data sources

#### Tasks:
1. Create yfinance API adapter
2. Create FMP API adapter
3. Create Alpha Vantage API adapter
4. Create Polygon API adapter
5. Implement intelligent API fallback logic
6. Add API rate limiting and error handling
7. Test with real API data

### Phase 4: Calculation Engine Integration (Week 4)
**Objective**: Connect calculation results to var_input_data

#### Tasks:
1. Modify FCF calculations to use var_input_data
2. Modify DCF calculations to use var_input_data
3. Modify DDM calculations to use var_input_data
4. Modify P/B analysis to use var_input_data
5. Implement calculation result storage
6. Add dependency resolution for composite variables
7. Test calculation pipeline integration

### Phase 5: Display Integration (Week 5)
**Objective**: Update all display components

#### Tasks:
1. Update Streamlit metrics to use var_input_data
2. Update chart components to use var_input_data
3. Update financial statements display
4. Update ratio analysis display
5. Update valuation summary display
6. Test UI with both Excel and API data
7. Ensure backward compatibility

### Phase 6: Testing and Optimization (Week 6)
**Objective**: Comprehensive testing and performance optimization

#### Tasks:
1. Create comprehensive unit test suite
2. Create integration test scenarios
3. Performance testing with large datasets
4. Memory usage optimization
5. Cache strategy refinement
6. Error handling improvements
7. Documentation and user guides

## Technical Specifications

### Key Classes and Interfaces

```python
class FinancialVariableRegistry:
    def register_variable(self, name: str, definition: VariableDefinition)
    def get_variable_definition(self, name: str) -> VariableDefinition
    def get_variables_by_category(self, category: str) -> List[str]
    def validate_value(self, name: str, value: Any) -> ValidationResult

class VarInputData:
    def get_variable(self, name: str, period: str = 'latest') -> Any
    def set_variable(self, name: str, value: Any, metadata: Dict = None)
    def get_historical_data(self, name: str, years: int = 10) -> List[Any]
    def get_available_variables(self) -> List[str]
    def calculate_composite_variables(self) -> None
    def clear_cache(self, pattern: str = None) -> None

class DataSourceAdapter:
    def extract_variables(self, raw_data: Any) -> Dict[str, Any]
    def validate_data(self, variables: Dict) -> ValidationResult
    def get_data_quality_score(self) -> float
```

### Data Flow Architecture

```
Excel Files → Excel Adapter → Variable Processor → var_input_data
API Sources → API Adapter → Variable Processor → var_input_data
var_input_data → Calculation Engine → Calculated Results → var_input_data
var_input_data → Display Components (Charts, Metrics, Tables)
```

### Configuration

#### Variable Registry Configuration
- Variable definitions in YAML/JSON format
- Metadata includes: data type, units, validation rules, category, description
- Configurable aliases for different data source field names

#### Caching Strategy
- Memory cache for frequently accessed variables
- Disk cache for historical data
- Configurable TTL per variable type
- Automatic cache invalidation on data updates

#### Data Source Priority
- Configurable preference order for data sources
- Automatic fallback on source failures
- Data quality scoring for source selection

## Non-Functional Requirements

### Performance
- Variable access under 10ms for cached data
- Initial data loading under 30 seconds for 10 years of data
- Memory usage under 512MB for typical company dataset
- Support for concurrent access by multiple analysis threads

### Reliability
- 99.9% uptime for data access operations
- Graceful degradation on API failures
- Automatic retry with exponential backoff
- Comprehensive error logging and monitoring

### Scalability
- Support for 1000+ financial variables
- Handle 50+ companies simultaneously
- Extensible architecture for new data sources
- Configurable resource limits

### Security
- API key management and rotation
- Data encryption for cached sensitive information
- Audit logging for data access patterns
- Rate limiting compliance for external APIs

## Success Metrics

### Technical Metrics
- Code duplication reduction: >80%
- Data access performance improvement: >50%
- Memory usage reduction: >30%
- Test coverage: >90%

### User Experience Metrics
- Developer onboarding time reduction: >60%
- Time to add new financial variables: <2 hours
- Data source switching time: <5 minutes
- Analysis setup time reduction: >40%

## Risk Mitigation

### Technical Risks
- **Data inconsistency**: Implement comprehensive validation and quality scoring
- **Performance degradation**: Extensive performance testing and optimization
- **API rate limits**: Intelligent caching and request batching
- **Memory leaks**: Regular memory profiling and optimization

### Business Risks
- **User resistance**: Maintain backward compatibility during transition
- **Data quality issues**: Multi-source validation and quality monitoring
- **API dependency**: Multiple fallback sources and graceful degradation

## Migration Strategy

### Backward Compatibility
- Keep existing interfaces during transition period
- Gradual migration with feature flags
- Comprehensive testing at each migration step
- Rollback plan for each phase

### Training and Documentation
- Developer documentation with examples
- Migration guide for existing code
- Best practices documentation
- Video tutorials for common use cases

## Acceptance Criteria

### Phase 1 Completion
- [ ] FinancialVariableRegistry created with 100+ variable definitions
- [ ] var_input_data core system operational
- [ ] Unit tests achieving >90% coverage
- [ ] Performance benchmarks established

### Phase 2 Completion
- [ ] Excel adapter processing FY and LTM files correctly
- [ ] All Excel variables mapped to standard names
- [ ] Excel data validation catching common errors
- [ ] Integration tests passing with real Excel files

### Phase 3 Completion
- [ ] All API adapters functional with fallback logic
- [ ] API rate limiting preventing service blocks
- [ ] Data quality scoring operational
- [ ] API integration tests passing

### Phase 4 Completion
- [ ] All calculation engines using var_input_data
- [ ] Calculated results automatically stored
- [ ] Dependency resolution working correctly
- [ ] Calculation performance maintained or improved

### Phase 5 Completion
- [ ] Streamlit UI using var_input_data exclusively
- [ ] No direct data access in display components
- [ ] UI tests passing with both data sources
- [ ] User experience unchanged or improved

### Phase 6 Completion
- [ ] All tests passing with >90% coverage
- [ ] Performance requirements met
- [ ] Documentation complete
- [ ] Production deployment successful

This PRD provides a comprehensive roadmap for implementing the unified financial data input system while maintaining system reliability and user experience.