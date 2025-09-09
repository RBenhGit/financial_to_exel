# Project Structure Reorganization PRD

## Overview

The financial analysis project requires comprehensive reorganization to strictly follow the documented README.md schema. Current analysis reveals significant deviations from the intended architecture, with files scattered across the root directory and missing core components.

## Problem Statement

The project structure does not align with the documented schema in README.md, leading to:
- Poor maintainability due to scattered files
- Difficulty locating components
- Inconsistent organization patterns
- Missing expected directory structures
- Configuration files mixed with application code

## Goals

1. **Strict Schema Compliance**: Ensure 100% alignment with README.md documented structure
2. **Improved Maintainability**: Organize files in logical, predictable locations
3. **Enhanced Developer Experience**: Make code navigation intuitive
4. **Updated Documentation**: Reflect actual directory structure including additional components

## Success Criteria

- All files moved to appropriate directories per README.md schema
- Zero files remaining in root directory that should be elsewhere
- All expected directories present and populated correctly
- Updated README.md schema to include discovered directories
- Successful test execution after reorganization
- All imports and references updated correctly

## Technical Requirements

### 1. Core Analysis File Reorganization

**Requirement**: Move core analysis files from root to proper `core/analysis/` subdirectories

**Current Issues**:
- `dcf_valuation.py` missing from `core/analysis/dcf/`
- `ddm_valuation.py` at root level instead of `core/analysis/ddm/`
- `pb_valuation.py` at root level instead of `core/analysis/pb/`
- `fcf_consolidated.py` at root instead of `core/analysis/`
- Various calculation engines scattered

**Target Structure**:
```
core/analysis/
├── engines/
│   ├── financial_calculations.py
│   ├── financial_calculation_engine.py
│   └── calculation_engine_integration_example.py
├── dcf/
│   ├── dcf_valuation.py
│   └── debug_dcf_*.py
├── ddm/
│   └── ddm_valuation.py
├── pb/
│   ├── pb_calculation_engine.py
│   ├── pb_fair_value_calculator.py
│   ├── pb_historical_analysis.py
│   ├── pb_statistical_analysis.py
│   ├── pb_valuation.py
│   └── pb_visualizer.py
└── fcf_consolidated.py
```

### 2. Configuration File Consolidation

**Requirement**: Centralize all configuration files in `config/` directory

**Current Issues**:
- Configuration files scattered at root level
- Multiple config formats mixed together
- Duplicate configuration patterns

**Target Actions**:
- Move all `.json` config files to `config/`
- Consolidate registry configuration
- Ensure single source of truth for settings

### 3. Test File Organization

**Requirement**: Move scattered test files to proper `tests/` subdirectories

**Current Issues**:
- Numerous test files at root level
- Tests not organized by category
- Missing proper test structure alignment

**Target Structure**:
```
tests/
├── unit/
│   ├── data_processing/
│   ├── dcf/
│   ├── pb/
│   └── streamlit/
├── integration/
│   ├── api/
│   ├── data_sources/
│   └── end_to_end/
├── regression/
├── performance/
└── fixtures/
```

### 4. UI Component Restructuring

**Requirement**: Organize UI components according to schema

**Current Issues**:
- Streamlit files mixed with other components
- Missing proper UI organization
- Visualization components not properly categorized

**Target Structure**:
```
ui/
├── components/
├── layouts/
├── widgets/
├── streamlit/
│   └── fcf_analysis_streamlit.py
└── visualization/
    ├── pb_visualizer.py
    └── watch_list_visualizer.py
```

### 5. Tools and Utilities Organization

**Requirement**: Consolidate development tools and utilities

**Current Issues**:
- Diagnostic tools mixed with application code
- Utilities scattered across directories
- Missing proper tool categorization

**Target Structure**:
```
tools/
├── diagnostics/
│   ├── logs/
│   └── reports/
├── scripts/
├── utilities/
└── batch_processing/
```

### 6. Schema Documentation Update

**Requirement**: Update README.md to include discovered directories

**Additional Directories to Document**:
- `performance/` - Performance monitoring and optimization
- `reports/` - Generated analysis reports and summaries
- Enhanced `tools/` structure with batch processing
- Expanded `ui/` with streamlit and visualization subdirectories

## Implementation Plan

### Phase 1: Analysis and Preparation
- Catalog all files requiring relocation
- Identify import dependencies
- Create backup of current structure
- Prepare migration scripts

### Phase 2: Core Module Reorganization
- Move core analysis files to proper locations
- Update import statements throughout codebase
- Ensure all references are corrected
- Validate core functionality

### Phase 3: Configuration and Support File Migration
- Consolidate configuration files
- Move test files to proper directories
- Reorganize tools and utilities
- Update development scripts

### Phase 4: UI and Documentation
- Restructure UI components
- Update README.md schema
- Validate documentation accuracy
- Ensure examples work correctly

### Phase 5: Validation and Testing
- Run comprehensive test suite
- Verify all imports resolve correctly
- Validate application functionality
- Confirm schema compliance

## Risk Mitigation

- **Import Breakage**: Systematic approach to updating imports
- **Lost Functionality**: Comprehensive testing after each phase
- **Configuration Issues**: Maintain backward compatibility during transition
- **Documentation Drift**: Real-time documentation updates

## Acceptance Criteria

1. ✅ All files located per README.md schema
2. ✅ Zero root-level files that should be elsewhere
3. ✅ All tests pass after reorganization
4. ✅ Application launches and functions correctly
5. ✅ Updated README.md reflects actual structure
6. ✅ All imports resolve without errors
7. ✅ Development tools and scripts work correctly
8. ✅ Configuration files properly organized

## Timeline

- **Week 1**: Analysis, preparation, and core module reorganization
- **Week 2**: Configuration migration and test organization  
- **Week 3**: UI restructuring and documentation updates
- **Week 4**: Validation, testing, and final cleanup

## Success Metrics

- 100% schema compliance verification
- Zero import errors after migration
- All tests passing
- Successful application deployment
- Developer feedback on improved organization