# Import Dependency Analysis - Task #112

## Critical Import Dependencies Requiring Updates

### 1. FCF_CONSOLIDATED IMPORTS
**Status**: CRITICAL - Core functionality dependency

**Files importing fcf_consolidated.py**:
- `ui/streamlit/fcf_analysis_streamlit.py:30` → **HIGH PRIORITY**
- `test_improvements.py:36` → Will move to tests/unit/
- `tests/unit/test_improvements.py:36` → Already in correct location
- `tests/unit/test_financial_calculations.py:14` → Already in correct location
- `docs/API_REFERENCE.md:291` → Documentation reference

**Required Updates**:
```python
# BEFORE: from fcf_consolidated import 
# AFTER:  from core.analysis.fcf_consolidated import
```

---

### 2. P/B ANALYSIS ENGINE IMPORTS
**Status**: HIGH PRIORITY - Multiple interconnected modules

**Files importing P/B modules**:
- `core/analysis/pb/pb_historical_analysis.py:51` → Internal cross-reference
- `core/analysis/pb/pb_fair_value_calculator.py:62` → Internal cross-reference
- `pb_historical_analysis.py:51` → **ROOT LEVEL DUPLICATE** (to be moved)
- `pb_fair_value_calculator.py:62` → **ROOT LEVEL DUPLICATE** (to be moved)
- Multiple test files in tests/unit/pb/

**Import Chain Dependencies**:
```
pb_fair_value_calculator → pb_historical_analysis → pb_calculation_engine
```

---

### 3. FINANCIAL CALCULATION ENGINE IMPORTS
**Status**: CRITICAL - Core calculation engine

**Files importing financial_calculation_engine**:
- Multiple test files
- Core analysis modules
- Validation systems

---

### 4. DATA PROCESSING MODULE IMPORTS
**Status**: HIGH PRIORITY - Data infrastructure

**Key Files Affected**:
- `core/analysis/engines/financial_calculations.py:222` → data_validator
- `core/data_processing/managers/enhanced_data_manager.py:26` → unified_data_adapter
- `data_source_bridge.py:23` → enhanced_data_manager
- Multiple test files

---

### 5. MAIN APPLICATION IMPORT PATTERNS
**File**: `ui/streamlit/fcf_analysis_streamlit.py`

**Current Imports to Update**:
```python
# Line 30 - CRITICAL UPDATE NEEDED
from core.analysis.fcf_consolidated import FCFCalculator, calculate_fcf_growth_rates
```

**Additional App Dependencies**:
- Multiple core.analysis imports (already correct)
- Tool and utility imports (will need updates)

---

## IMPORT UPDATE PLAN BY PHASE

### Phase 1: Core Analysis Modules
**Before moving files, update these imports**:

1. **fcf_consolidated.py moves**:
   - Update `ui/streamlit/fcf_analysis_streamlit.py:30`
   - Update any remaining root-level imports

2. **P/B modules move**:
   - Internal cross-references in core/analysis/pb/ (already correct)
   - Remove duplicate root-level files
   - Update test imports

3. **financial_calculation_engine.py moves**:
   - Update validation systems
   - Update test imports

### Phase 2: Data Processing Modules
**After Phase 1 complete**:

1. **data_validator.py moves**:
   - Update core/analysis/engines/financial_calculations.py
   - Update validation systems

2. **unified_data_adapter.py moves**:
   - Update enhanced_data_manager imports

3. **Data managers move**:
   - Update bridge and integration files

### Phase 3: Utilities and Tools
**Low priority but systematic**:

1. **Utility imports**: Update paths in core modules
2. **Tool imports**: Update script references
3. **Configuration imports**: Update config loading

---

## FILES REQUIRING IMMEDIATE ATTENTION AFTER MOVES

### 1. Main Application Files
```
ui/streamlit/fcf_analysis_streamlit.py      - PRIMARY APPLICATION
```

### 2. Core Integration Files
```
core/analysis/engines/financial_calculations.py   - Core calculation engine
core/data_processing/managers/enhanced_data_manager.py - Data management
core/validation/validation_orchestrator.py         - Validation systems
```

### 3. Test Files (80+ files)
```
tests/unit/pb/*.py                        - P/B specific tests
tests/unit/test_financial_calculations.py - Financial calculation tests
tests/unit/test_improvements.py          - General improvement tests
```

---

## DUPLICATION ANALYSIS

### Root-Level Duplicates Found
These files exist both at root level AND in correct core/ locations:

```
ROOT LEVEL                    CORE LOCATION                           ACTION
pb_calculation_engine.py   →  core/analysis/pb/pb_calculation_engine.py    DELETE ROOT
pb_fair_value_calculator.py → core/analysis/pb/pb_fair_value_calculator.py DELETE ROOT  
pb_historical_analysis.py  →  core/analysis/pb/pb_historical_analysis.py   DELETE ROOT
pb_statistical_analysis.py →  core/analysis/pb/pb_statistical_analysis.py  DELETE ROOT
```

**IMPORTANT**: Verify core/ versions are current before deleting root versions.

---

## CRITICAL IMPORT CHAINS TO PRESERVE

### Chain 1: Core Analysis Flow
```
ui/streamlit/fcf_analysis_streamlit.py
  ↓
core/analysis/fcf_consolidated.py (MOVING)
  ↓
core/analysis/engines/financial_calculations.py
  ↓
core/data_processing/data_validator.py (MOVING)
```

### Chain 2: P/B Analysis Flow  
```
core/analysis/pb/pb_fair_value_calculator.py
  ↓
core/analysis/pb/pb_historical_analysis.py
  ↓  
core/analysis/pb/pb_calculation_engine.py
```

### Chain 3: Data Management Flow
```
core/data_processing/managers/enhanced_data_manager.py (MOVING)
  ↓
core/data_processing/unified_data_adapter.py (MOVING)
  ↓
core/data_sources/interfaces/data_sources.py (MOVING)
```

---

## AUTOMATED IMPORT UPDATE SCRIPT NEEDED

**Recommended approach**: Create script to automatically update imports during move:

```python
IMPORT_MAPPING = {
    'fcf_consolidated': 'core.analysis.fcf_consolidated',
    'pb_calculation_engine': 'core.analysis.pb.pb_calculation_engine',
    'pb_fair_value_calculator': 'core.analysis.pb.pb_fair_value_calculator',
    'pb_historical_analysis': 'core.analysis.pb.pb_historical_analysis', 
    'pb_statistical_analysis': 'core.analysis.pb.pb_statistical_analysis',
    'financial_calculation_engine': 'core.analysis.engines.financial_calculation_engine',
    'data_validator': 'core.data_processing.data_validator',
    'unified_data_adapter': 'core.data_processing.unified_data_adapter',
    # ... continue for all moved modules
}
```

---

## VALIDATION REQUIREMENTS

After each phase:
1. **Import verification**: Check all imports resolve correctly
2. **Application test**: Verify main Streamlit app launches
3. **Test suite**: Run affected test categories
4. **Integration test**: Verify end-to-end functionality

---

**Status**: Import dependency mapping complete
**Next Phase**: Create migration execution plan with dependency order