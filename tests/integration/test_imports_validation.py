#!/usr/bin/env python3
"""
Import Validation Script
========================

This script systematically tests all important imports after project reorganization
to identify any broken import paths that need fixing.
"""

import sys
import traceback
from typing import List, Tuple

def test_import(module_name: str, from_module: str = None) -> Tuple[bool, str]:
    """Test importing a module and return success status and error message."""
    try:
        if from_module:
            exec(f"from {from_module} import {module_name}")
        else:
            exec(f"import {module_name}")
        return True, "Success"
    except Exception as e:
        return False, str(e)

def main():
    """Run comprehensive import validation tests."""
    print("=" * 60)
    print("PROJECT REORGANIZATION - IMPORT VALIDATION")
    print("=" * 60)
    
    # Test results
    tests = []
    
    print("\n1. CORE APPLICATION MODULES")
    print("-" * 40)
    
    # Main application modules
    tests.append(("fcf_analysis_streamlit", None))
    tests.append(("config", None))
    tests.append(("report_generator", None))
    
    print("\n2. UNIVERSAL DATA REGISTRY SYSTEM")
    print("-" * 40)
    
    # Universal Data Registry
    tests.append(("UniversalDataRegistry", "core.data_processing.universal_data_registry"))
    tests.append(("RegistryIntegrationAdapter", "registry_integration_adapter"))
    tests.append(("DataSourceInterface", "core.data_sources.interfaces.data_source_interfaces"))
    
    print("\n3. CALCULATION ENGINES")
    print("-" * 40)
    
    # Calculation engines
    tests.append(("FinancialCalculationEngine", "core.analysis.engines.financial_calculation_engine"))
    tests.append(("PBCalculationEngine", "core.analysis.pb.pb_calculation_engine"))
    tests.append(("PBFairValueCalculator", "core.analysis.pb.pb_fair_value_calculator"))
    
    print("\n4. TESTING FRAMEWORK")
    print("-" * 40)
    
    # Test framework
    tests.append(("test_suite_runner", "tests"))
    
    print("\n5. CONFIGURATION SYSTEM")  
    print("-" * 40)
    
    # Configuration loading
    tests.append(("registry_config_loader", None))
    
    # Run all tests
    passed = 0
    failed = 0
    
    for module, from_module in tests:
        success, error = test_import(module, from_module)
        if success:
            print(f"[OK] {module} {'from ' + from_module if from_module else ''}")
            passed += 1
        else:
            print(f"[FAIL] {module} {'from ' + from_module if from_module else ''}")
            print(f"   Error: {error}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"IMPORT VALIDATION RESULTS")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)