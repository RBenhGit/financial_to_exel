#!/usr/bin/env python3
"""
Quick Test Coverage Assessment
Identifies core modules that may need additional test coverage
"""

import os
from pathlib import Path

def find_core_modules():
    """Find all Python modules in the core directory"""
    core_modules = []
    for root, dirs, files in os.walk("core"):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_path = os.path.join(root, file)
                core_modules.append(module_path)
    return core_modules

def find_test_files():
    """Find all test files"""
    test_files = []
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_path = os.path.join(root, file)
                test_files.append(test_path)
    return test_files

def assess_coverage():
    """Basic assessment of test coverage"""
    print("=== TEST COVERAGE ASSESSMENT ===\n")
    
    core_modules = find_core_modules()
    test_files = find_test_files()
    
    print(f"Core modules found: {len(core_modules)}")
    print(f"Test files found: {len(test_files)}")
    print()
    
    # Key modules to check
    key_modules = [
        "core/analysis/engines/financial_calculations.py",
        "core/analysis/engines/financial_calculation_engine.py", 
        "core/analysis/dcf/dcf_valuation.py",
        "core/analysis/ddm/ddm_valuation.py",
        "core/analysis/pb/pb_calculation_engine.py",
        "core/analysis/pb/pb_historical_analysis.py",
        "core/data_processing/managers/enhanced_data_manager.py",
        "core/data_processing/managers/centralized_data_manager.py",
        "core/validation/validation_orchestrator.py"
    ]
    
    print("=== KEY MODULE TEST COVERAGE ===")
    for module in key_modules:
        if os.path.exists(module):
            # Simple heuristic: check if there's a corresponding test file
            module_name = Path(module).stem
            has_test = any(module_name in test_file for test_file in test_files)
            status = "[TESTED]" if has_test else "[NEEDS TEST]"
            print(f"{module:50} {status}")
        else:
            print(f"{module:50} [NOT FOUND]")
    
    print()
    print("=== INTEGRATION TESTS ===")
    integration_tests = [f for f in test_files if "integration" in f]
    print(f"Integration test files: {len(integration_tests)}")
    for test in integration_tests[:10]:  # Show first 10
        print(f"  - {test}")
    
    print()
    print("=== E2E TESTS ===")
    e2e_tests = [f for f in test_files if "e2e" in f]
    print(f"E2E test files: {len(e2e_tests)}")
    for test in e2e_tests:
        print(f"  - {test}")
    
    print()
    print("=== PERFORMANCE TESTS ===")
    perf_tests = [f for f in test_files if "performance" in f or "perf" in f]
    print(f"Performance test files: {len(perf_tests)}")
    for test in perf_tests:
        print(f"  - {test}")

if __name__ == "__main__":
    assess_coverage()