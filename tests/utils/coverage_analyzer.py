"""
Coverage Analysis Tool for Task #70
Analyzes test coverage across core components of the unified data system
"""
import sys
import os
from pathlib import Path
import ast
import json
import time

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class CoverageAnalyzer:
    """Analyzes test coverage for unified data system components"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.core_modules = [
            "core/data_processing/financial_variable_registry.py",
            "core/data_processing/var_input_data.py",
            "core/data_processing/standard_financial_variables.py",
            "core/analysis/engines/financial_calculations.py"
        ]
        self.test_files = []
        self.coverage_data = {}
    
    def find_test_files(self):
        """Find all test files in the project"""
        tests_dir = self.project_root / "tests"
        self.test_files = list(tests_dir.glob("**/test_*.py"))
        print(f"[INFO] Found {len(self.test_files)} test files")
        return len(self.test_files)
    
    def analyze_module_functions(self, module_path):
        """Analyze functions and classes in a module"""
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            functions = []
            classes = []
            methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    # Find methods in the class
                    for class_node in node.body:
                        if isinstance(class_node, ast.FunctionDef):
                            if not class_node.name.startswith('_'):
                                methods.append(f"{node.name}.{class_node.name}")
            
            return {
                "functions": functions,
                "classes": classes, 
                "methods": methods,
                "total_testable": len(functions) + len(methods)
            }
            
        except Exception as e:
            print(f"[ERROR] Could not analyze {module_path}: {e}")
            return {"functions": [], "classes": [], "methods": [], "total_testable": 0}
    
    def analyze_test_coverage(self, test_file):
        """Analyze what a test file covers"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for test functions
            test_functions = []
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_functions.append(node.name)
            
            # Simple heuristic: look for imports and function calls
            covered_items = []
            lines = content.split('\\n')
            
            for line in lines:
                line = line.strip()
                # Look for function calls and class instantiations
                if any(keyword in line for keyword in ['assert', 'test_', 'mock', 'patch']):
                    # Extract potential function/method names
                    words = line.split()
                    for word in words:
                        if '(' in word and not word.startswith('test_'):
                            func_name = word.split('(')[0]
                            if func_name and not func_name.startswith('_'):
                                covered_items.append(func_name)
            
            return {
                "test_functions": test_functions,
                "covered_items": list(set(covered_items)),
                "test_count": len(test_functions)
            }
            
        except Exception as e:
            print(f"[ERROR] Could not analyze test file {test_file}: {e}")
            return {"test_functions": [], "covered_items": [], "test_count": 0}
    
    def calculate_coverage_metrics(self):
        """Calculate coverage metrics for each core module"""
        print("[INFO] Analyzing coverage metrics...")
        
        total_testable_items = 0
        total_covered_items = 0
        
        for module_rel_path in self.core_modules:
            module_path = self.project_root / module_rel_path
            
            if not module_path.exists():
                print(f"[SKIP] Module not found: {module_rel_path}")
                continue
            
            print(f"[ANALYZE] {module_rel_path}")
            
            # Analyze module structure
            module_analysis = self.analyze_module_functions(module_path)
            
            # Find related test files
            module_name = module_path.stem
            related_tests = []
            for test_file in self.test_files:
                if module_name in test_file.name or any(keyword in test_file.name for keyword in ['unified', 'comprehensive']):
                    related_tests.append(test_file)
            
            # Analyze test coverage
            covered_by_tests = set()
            total_test_functions = 0
            
            for test_file in related_tests:
                test_analysis = self.analyze_test_coverage(test_file)
                covered_by_tests.update(test_analysis["covered_items"])
                total_test_functions += test_analysis["test_count"]
            
            # Calculate coverage percentage
            testable_items = set(module_analysis["functions"] + module_analysis["methods"])
            covered_items = testable_items.intersection(covered_by_tests)
            
            coverage_percent = 0
            if testable_items:
                coverage_percent = len(covered_items) / len(testable_items) * 100
            
            self.coverage_data[module_rel_path] = {
                "module_analysis": module_analysis,
                "testable_items": list(testable_items),
                "covered_items": list(covered_items),
                "coverage_percent": coverage_percent,
                "test_files": [str(tf.relative_to(self.project_root)) for tf in related_tests],
                "test_function_count": total_test_functions
            }
            
            total_testable_items += len(testable_items)
            total_covered_items += len(covered_items)
            
            print(f"  Functions: {len(module_analysis['functions'])}")
            print(f"  Methods: {len(module_analysis['methods'])}")
            print(f"  Testable items: {len(testable_items)}")
            print(f"  Covered items: {len(covered_items)}")
            print(f"  Coverage: {coverage_percent:.1f}%")
            print(f"  Related tests: {len(related_tests)}")
            print()
        
        # Calculate overall coverage
        overall_coverage = 0
        if total_testable_items > 0:
            overall_coverage = total_covered_items / total_testable_items * 100
        
        return overall_coverage
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("="*60)
        print("COVERAGE ANALYSIS REPORT - TASK #70")
        print("="*60)
        
        # Find test files
        test_count = self.find_test_files()
        
        # Calculate coverage
        overall_coverage = self.calculate_coverage_metrics()
        
        print("SUMMARY:")
        print(f"Total test files: {test_count}")
        print(f"Core modules analyzed: {len(self.core_modules)}")
        print(f"Overall coverage: {overall_coverage:.1f}%")
        
        # Module-by-module breakdown
        print("\\nMODULE BREAKDOWN:")
        for module, data in self.coverage_data.items():
            coverage = data["coverage_percent"]
            status = "EXCELLENT" if coverage >= 90 else "GOOD" if coverage >= 70 else "NEEDS IMPROVEMENT"
            print(f"  {module}: {coverage:.1f}% [{status}]")
        
        # Coverage target analysis
        target_coverage = 90.0
        modules_meeting_target = sum(1 for data in self.coverage_data.values() if data["coverage_percent"] >= target_coverage)
        
        print(f"\\nTARGET ANALYSIS (>={target_coverage}% coverage):")
        print(f"Modules meeting target: {modules_meeting_target}/{len(self.coverage_data)}")
        
        if overall_coverage >= target_coverage:
            print(f"[EXCELLENT] Overall coverage target MET ({overall_coverage:.1f}%)")
        elif overall_coverage >= 70:
            print(f"[GOOD] Good coverage achieved ({overall_coverage:.1f}%)")
        else:
            print(f"[NEEDS WORK] Coverage below target ({overall_coverage:.1f}%)")
        
        # Save detailed report
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_coverage": overall_coverage,
            "target_coverage": target_coverage,
            "modules_meeting_target": modules_meeting_target,
            "total_modules": len(self.coverage_data),
            "total_test_files": test_count,
            "module_coverage": self.coverage_data
        }
        
        report_path = self.project_root / "tests" / "coverage_analysis_report.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\\nDetailed report saved to: {report_path}")
        except Exception as e:
            print(f"\\nWarning: Could not save report: {e}")
        
        return overall_coverage >= 70  # Success if >= 70% coverage

def main():
    """Main entry point"""
    analyzer = CoverageAnalyzer()
    success = analyzer.generate_coverage_report()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())