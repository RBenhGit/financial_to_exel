# File Reorganization Analysis - Task #112

## Executive Summary
This document provides a comprehensive inventory of all misplaced files in the project root directory and their target destinations according to the README.md schema.

## Current Status
- **Total Root-Level Files Analyzed**: 150+ files
- **Files Requiring Movement**: 120+ files
- **Categories Identified**: 8 major categories

---

## 1. CORE ANALYSIS FILES → `core/analysis/`

### Core FCF Analysis
```
fcf_consolidated.py → core/analysis/fcf_consolidated.py
```

### P/B Analysis Engine Files → `core/analysis/pb/`
```
pb_calculation_engine.py → core/analysis/pb/pb_calculation_engine.py
pb_fair_value_calculator.py → core/analysis/pb/pb_fair_value_calculator.py
pb_historical_analysis.py → core/analysis/pb/pb_historical_analysis.py
pb_statistical_analysis.py → core/analysis/pb/pb_statistical_analysis.py
```

### Financial Calculation Engines → `core/analysis/engines/`
```
financial_calculation_engine.py → core/analysis/engines/financial_calculation_engine.py
```

---

## 2. DATA PROCESSING FILES → `core/data_processing/`

### Data Processing Core
```
data_validator.py → core/data_processing/data_validator.py
unified_data_adapter.py → core/data_processing/unified_data_adapter.py
```

### Data Processing Processors → `core/data_processing/processors/`
```
centralized_data_processor.py → core/data_processing/processors/centralized_data_processor.py
```

### Data Processing Managers → `core/data_processing/managers/`
```
enhanced_data_manager.py → core/data_processing/managers/enhanced_data_manager.py
```

### API Data Converters → `core/data_processing/converters/`
```
fmp_converter.py → core/data_processing/converters/fmp_converter.py
polygon_converter.py → core/data_processing/converters/polygon_converter.py
```

---

## 3. DATA SOURCES → `core/data_sources/interfaces/`

### Data Source Interfaces
```
data_sources.py → core/data_sources/interfaces/data_sources.py
data_source_manager.py → core/data_sources/interfaces/data_source_manager.py
data_source_bridge.py → core/data_sources/interfaces/data_source_bridge.py
```

---

## 4. CONFIGURATION FILES → `config/`

### JSON Configuration Files
```
data_sources_config.json → config/data_sources_config.json
nonexistent_config.json → config/nonexistent_config.json (review for deletion)
```

---

## 5. DIAGNOSTIC TOOLS → `tools/diagnostics/`

### Diagnostic and Debug Tools
```
api_diagnostic_tool.py → tools/diagnostics/api_diagnostic_tool.py
trace_dcf_bug.py → tools/diagnostics/trace_dcf_bug.py
```

---

## 6. UTILITY TOOLS → `tools/utilities/`

### Utility Scripts
```
check_market_cap.py → tools/utilities/check_market_cap.py
```

---

## 7. SETUP TOOLS → `tools/setup/`

### Development Setup
```
setup_dev_tools.py → tools/setup/setup_dev_tools.py
```

---

## 8. GENERAL UTILITIES → `utils/`

### Utility Functions
```
yfinance_logger.py → utils/yfinance_logger.py
field_normalizer.py → utils/field_normalizer.py
registry_config_loader.py → utils/registry_config_loader.py
```

---

## 9. DEVELOPMENT SCRIPTS → `tools/scripts/`

### Runtime and Development Scripts
```
run_tests.py → tools/scripts/run_tests.py
run_streamlit_windows.py → tools/scripts/run_streamlit_windows.py
simple_test.py → tools/scripts/simple_test.py
simple_test_mapping.py → tools/scripts/simple_test_mapping.py
```

---

## 10. PERFORMANCE TESTS → `tests/performance/`

### Performance Testing Files
```
simple_performance_test.py → tests/performance/simple_performance_test.py
test_performance_optimizations.py → tests/performance/test_performance_optimizations.py
test_performance_quick.py → tests/performance/test_performance_quick.py
test_numpy_best_practices.py → tests/performance/test_numpy_best_practices.py
simple_varinputdata_performance_test.py → tests/performance/simple_varinputdata_performance_test.py
test_universal_registry_performance.py → tests/performance/test_universal_registry_performance.py
test_varinputdata_performance.py → tests/performance/test_varinputdata_performance.py
```

---

## 11. UNIT TESTS BY CATEGORY

### DCF Unit Tests → `tests/unit/dcf/`
```
test_dcf_debug.py → tests/unit/dcf/test_dcf_debug.py
test_dcf_msft.py → tests/unit/dcf/test_dcf_msft.py
test_dcf_scaling_fix.py → tests/unit/dcf/test_dcf_scaling_fix.py
test_dcf_units_fix.py → tests/unit/dcf/test_dcf_units_fix.py
test_dcf_validation.py → tests/unit/dcf/test_dcf_validation.py
test_dcf_ddm_integration.py → tests/unit/dcf/test_dcf_ddm_integration.py
```

### P/B Unit Tests → `tests/unit/pb/`
```
test_pb_analysis.py → tests/unit/pb/test_pb_analysis.py
test_pb_comprehensive.py → tests/unit/pb/test_pb_comprehensive.py
test_pb_enhanced.py → tests/unit/pb/test_pb_enhanced.py
test_pb_simple.py → tests/unit/pb/test_pb_simple.py
test_pb_fix.py → tests/unit/pb/test_pb_fix.py
```

### Data Processing Unit Tests → `tests/unit/data_processing/`
```
test_data_processing.py → tests/unit/data_processing/test_data_processing.py
test_data_ordering.py → tests/unit/data_processing/test_data_ordering.py
test_alternative_data_sources.py → tests/unit/data_processing/test_alternative_data_sources.py
test_capture_functionality.py → tests/unit/data_processing/test_capture_functionality.py
test_corrected_capture.py → tests/unit/data_processing/test_corrected_capture.py
test_backward_compatibility.py → tests/unit/data_processing/test_backward_compatibility.py
test_market_data_equality.py → tests/unit/data_processing/test_market_data_equality.py
```

### Streamlit Unit Tests → `tests/unit/streamlit/`
```
test_streamlit_ddm_integration.py → tests/unit/streamlit/test_streamlit_ddm_integration.py
test_streamlit_integration.py → tests/unit/streamlit/test_streamlit_integration.py
test_streamlit_pb_integration.py → tests/unit/streamlit/test_streamlit_pb_integration.py
test_streamlit_pb.py → tests/unit/streamlit/test_streamlit_pb.py
```

### General Unit Tests → `tests/unit/`
```
test_ddm_implementation.py → tests/unit/test_ddm_implementation.py
test_fcf_unified.py → tests/unit/test_fcf_unified.py
test_hardcoded_removal.py → tests/unit/test_hardcoded_removal.py
test_units_consistency.py → tests/unit/test_units_consistency.py
test_field_mapping_fix.py → tests/unit/test_field_mapping_fix.py
test_input_validation.py → tests/unit/test_input_validation.py
test_market_cap_fix.py → tests/unit/test_market_cap_fix.py
test_rate_limiting.py → tests/unit/test_rate_limiting.py
test_yfinance_enhancement.py → tests/unit/test_yfinance_enhancement.py
test_yfinance_logging.py → tests/unit/test_yfinance_logging.py
test_tase_support.py → tests/unit/test_tase_support.py
test_visualization.py → tests/unit/test_visualization.py
test_report_generator.py → tests/unit/test_report_generator.py
test_ticker_fcf.py → tests/unit/test_ticker_fcf.py
test_metadata_creation.py → tests/unit/test_metadata_creation.py
test_nvda_equality.py → tests/unit/test_nvda_equality.py
test_complete_fcf_fix.py → tests/unit/test_complete_fcf_fix.py
test_improvements.py → tests/unit/test_improvements.py
```

---

## 12. INTEGRATION TESTS

### API Integration Tests → `tests/integration/api/`
```
test_api_behavior.py → tests/integration/api/test_api_behavior.py
test_e2e_api_integration.py → tests/integration/api/test_e2e_api_integration.py
test_enhanced_api_integration.py → tests/integration/api/test_enhanced_api_integration.py
test_yfinance_adapter.py → tests/integration/api/test_yfinance_adapter.py
```

### End-to-End Integration Tests → `tests/integration/end_to_end/`
```
test_centralized_system.py → tests/integration/end_to_end/test_centralized_system.py
test_integration.py → tests/integration/end_to_end/test_integration.py
test_comprehensive.py → tests/integration/end_to_end/test_comprehensive.py
test_with_registry.py → tests/integration/end_to_end/test_with_registry.py
```

### Excel Integration Tests → `tests/integration/excel/`
```
test_excel_extraction.py → tests/integration/excel/test_excel_extraction.py
test_excel_optimization.py → tests/integration/excel/test_excel_optimization.py
test_excel_adapter.py → tests/integration/excel/test_excel_adapter.py
test_excel_simple.py → tests/integration/excel/test_excel_simple.py
test_msft_excel_dcf.py → tests/integration/excel/test_msft_excel_dcf.py
```

---

## 13. REGRESSION TESTS → `tests/regression/`

### Regression Test Files
```
test_critical_edge_cases.py → tests/regression/test_critical_edge_cases.py
test_edge_cases_comprehensive.py → tests/regression/test_edge_cases_comprehensive.py
test_edge_cases_simple.py → tests/regression/test_edge_cases_simple.py
test_fcf_accuracy.py → tests/regression/test_fcf_accuracy.py
test_enhanced_dividend_extraction.py → tests/regression/test_enhanced_dividend_extraction.py
```

### Special Analysis Tests
```
test_equity_detection.py → tests/regression/test_equity_detection.py
test_extraction.py → tests/regression/test_extraction.py
test_date_extraction.py → tests/regression/test_date_extraction.py
```

---

## 14. DEMOS AND EXAMPLES → `docs/guides/`

### Demo Files
```
demo_financial_variable_registry.py → docs/guides/demo_financial_variable_registry.py
demo_standard_variables.py → docs/guides/demo_standard_variables.py
register_variables.py → docs/guides/register_variables.py
```

### Integration Examples
```
dependency_injection.py → docs/guides/dependency_injection.py
module_adapter.py → docs/guides/module_adapter.py
registry_integration_adapter.py → docs/guides/registry_integration_adapter.py
```

---

## 15. CACHING AND PERFORMANCE TESTS → `tests/performance/`

### Caching Tests
```
test_price_caching_enhancements.py → tests/performance/test_price_caching_enhancements.py
test_price_service.py → tests/performance/test_price_service.py
```

---

## IMPORT DEPENDENCIES TO UPDATE

### High-Priority Import Updates Needed:
1. **Core Analysis Imports**: Any imports from fcf_consolidated, pb_*, financial_calculation_engine
2. **Data Processing Imports**: Imports from data_validator, unified_data_adapter, centralized_data_processor
3. **Data Sources Imports**: Imports from data_sources, data_source_manager, data_source_bridge
4. **Converter Imports**: Imports from fmp_converter, polygon_converter
5. **Test Imports**: All test files importing moved modules
6. **Streamlit App Imports**: Main application imports in fcf_analysis_streamlit.py
7. **Configuration Loading**: Registry config loader imports

### Files With Heavy Import Dependencies:
- `fcf_analysis_streamlit.py` (main Streamlit app)
- All test files
- `run_streamlit_windows.py`
- Configuration files
- Any existing core/ module files

---

## MIGRATION PRIORITY ORDER

### Phase 1: Core Analysis (High Risk)
1. Move core analysis engines first
2. Update imports in main application
3. Test core functionality

### Phase 2: Data Processing (Medium Risk)
1. Move data processing modules
2. Update related imports
3. Test data loading

### Phase 3: Utilities & Tools (Low Risk)
1. Move utility and tool files
2. Update script references
3. Test development workflows

### Phase 4: Tests (Low Risk)
1. Move test files by category
2. Update test imports
3. Run full test suite

### Phase 5: Configuration & Cleanup (Low Risk)
1. Move configuration files
2. Update configuration loading
3. Clean up any remaining files

---

## CRITICAL DEPENDENCIES TO MONITOR

### Import Chains to Track:
1. `fcf_analysis_streamlit.py` → Core analysis modules
2. Test files → Core modules being tested
3. `FinancialCalculator` → Data processing modules
4. Configuration systems → Moved config files
5. API integrations → Converter modules

### Files Requiring Immediate Attention After Moves:
- `__init__.py` files in new directories
- Main application entry points
- Import statements across all modules
- Configuration file path references

---

**Status**: Analysis Complete - Ready for Phase 1 Implementation
**Next Action**: Begin with Core Analysis file moves (Task #113)