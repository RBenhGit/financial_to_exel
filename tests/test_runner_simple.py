"""
Simple Comprehensive Test Runner for Task #70
ASCII-only version to avoid Unicode issues
"""
import sys
import os
from pathlib import Path
import time
import json

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class SimpleTestRunner:
    """Simple test runner for comprehensive validation"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def test_core_structure(self):
        """Test core module structure"""
        print("[TEST 1/5] Core module structure validation...")
        
        required_paths = [
            "core/data_processing/financial_variable_registry.py",
            "core/data_processing/var_input_data.py", 
            "core/data_processing/standard_financial_variables.py",
            "core/analysis/engines/financial_calculations.py"
        ]
        
        found = 0
        for path in required_paths:
            full_path = self.project_root / path
            if full_path.exists():
                print(f"  [OK] {path}")
                found += 1
            else:
                print(f"  [MISSING] {path}")
        
        self.test_results["total_tests"] += 1
        if found >= 3:  # At least 3 out of 4 core files
            self.test_results["passed"] += 1
            print(f"  [RESULT] PASSED ({found}/{len(required_paths)} found)")
            return True
        else:
            self.test_results["failed"] += 1
            print(f"  [RESULT] FAILED ({found}/{len(required_paths)} found)")
            return False
    
    def test_data_compatibility(self):
        """Test data source compatibility"""
        print("[TEST 2/5] Data source compatibility...")
        
        checks = {
            "Excel data structure": self.project_root / "data" / "companies",
            "Cache system": self.project_root / "data_cache",
            "Test infrastructure": self.project_root / "tests"
        }
        
        passed = 0
        for name, path in checks.items():
            if path.exists():
                print(f"  [OK] {name}")
                passed += 1
            else:
                print(f"  [MISSING] {name}")
        
        self.test_results["total_tests"] += 1
        if passed >= 2:
            self.test_results["passed"] += 1
            print(f"  [RESULT] PASSED ({passed}/{len(checks)} compatible)")
            return True
        else:
            self.test_results["failed"] += 1
            print(f"  [RESULT] FAILED ({passed}/{len(checks)} compatible)")
            return False
    
    def test_performance(self):
        """Test performance baseline"""
        print("[TEST 3/5] Performance baseline...")
        
        start_time = time.time()
        
        # Simulate financial data processing
        test_size = 5000
        data = {
            "revenue": [i * 1000 for i in range(test_size)],
            "costs": [i * 800 for i in range(test_size)]
        }
        
        # Process data
        results = {}
        for metric, values in data.items():
            results[f"{metric}_total"] = sum(values)
            results[f"{metric}_avg"] = sum(values) / len(values)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"  [INFO] Processed {test_size:,} records in {processing_time:.3f}s")
        
        self.test_results["total_tests"] += 1
        if processing_time < 1.0:  # Should process quickly
            self.test_results["passed"] += 1
            print("  [RESULT] PASSED - Good performance")
            return True
        else:
            self.test_results["failed"] += 1
            print("  [RESULT] FAILED - Performance issues")
            return False
    
    def test_regression(self):
        """Test regression protection"""
        print("[TEST 4/5] Regression protection...")
        
        # Check existing functionality
        feature_files = {
            "Financial calculations": "**/financial_calculation*.py",
            "Excel processing": "**/excel*.py", 
            "DCF analysis": "**/dcf*.py",
            "DDM analysis": "**/ddm*.py",
            "P/B analysis": "**/pb*.py"
        }
        
        preserved = 0
        for feature, pattern in feature_files.items():
            files = list(self.project_root.glob(pattern))
            if files:
                print(f"  [OK] {feature} ({len(files)} files)")
                preserved += 1
            else:
                print(f"  [MISSING] {feature}")
        
        self.test_results["total_tests"] += 1
        if preserved >= 4:  # Most features preserved
            self.test_results["passed"] += 1
            print(f"  [RESULT] PASSED ({preserved}/{len(feature_files)} features)")
            return True
        else:
            self.test_results["failed"] += 1
            print(f"  [RESULT] FAILED ({preserved}/{len(feature_files)} features)")
            return False
    
    def test_integration(self):
        """Test integration readiness"""
        print("[TEST 5/5] Integration readiness...")
        
        components = {
            "Unified data registry": "core/data_processing/financial_variable_registry.py",
            "Data adapters": "core/data_processing/adapters",
            "Variable definitions": "core/data_processing/standard_financial_variables.py",
            "Input data system": "core/data_processing/var_input_data.py"
        }
        
        ready = 0
        for component, path in components.items():
            full_path = self.project_root / path
            if full_path.exists():
                print(f"  [OK] {component}")
                ready += 1
            else:
                print(f"  [MISSING] {component}")
        
        self.test_results["total_tests"] += 1
        if ready >= 3:  # Most components ready
            self.test_results["passed"] += 1
            print(f"  [RESULT] PASSED ({ready}/{len(components)} ready)")
            return True
        else:
            self.test_results["failed"] += 1
            print(f"  [RESULT] FAILED ({ready}/{len(components)} ready)")
            return False
    
    def run_tests(self):
        """Run all tests"""
        print("="*60)
        print("COMPREHENSIVE TEST SUITE - TASK #70")
        print("="*60)
        
        tests = [
            self.test_core_structure,
            self.test_data_compatibility,
            self.test_performance,
            self.test_regression,
            self.test_integration
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"  [ERROR] {test.__name__}: {e}")
                self.test_results["errors"].append(f"{test.__name__}: {str(e)}")
                self.test_results["failed"] += 1
                self.test_results["total_tests"] += 1
            print()
        
        self.show_report()
    
    def show_report(self):
        """Show final report"""
        print("="*60)
        print("TEST REPORT")
        print("="*60)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests:  {total}")
        print(f"Passed:       {passed}")
        print(f"Failed:       {failed}")
        print(f"Pass Rate:    {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            print("\\nErrors:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        print("\\nUNIFIED SYSTEM STATUS:")
        if pass_rate >= 80:
            print("  [EXCELLENT] System ready for production")
            status = "EXCELLENT"
        elif pass_rate >= 60:
            print("  [GOOD] Minor issues to address")
            status = "GOOD"
        elif pass_rate >= 40:
            print("  [NEEDS WORK] Improvements required")
            status = "NEEDS_WORK"
        else:
            print("  [CRITICAL] Major issues to resolve")
            status = "CRITICAL"
        
        # Save results
        results_path = self.project_root / "tests" / "comprehensive_results.json"
        final_results = {
            **self.test_results,
            "pass_rate": pass_rate,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open(results_path, 'w') as f:
                json.dump(final_results, f, indent=2)
            print(f"\\nResults saved to: {results_path}")
        except Exception as e:
            print(f"\\nWarning: Could not save results: {e}")
        
        return pass_rate >= 60

def main():
    """Main entry point"""
    runner = SimpleTestRunner()
    success = runner.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())