"""
Comprehensive Test Suite Runner for P/B Historical Fair Value Module
===================================================================

This module provides a comprehensive test runner for all P/B historical fair value
tests including multi-source validation, caching behavior, error handling, and
performance testing.

Features:
- Organized test execution by category
- Test result reporting and analysis
- Performance metrics collection
- Coverage analysis integration
- HTML test report generation

Usage:
------
Run all tests:
    python test_suite_runner.py

Run specific test categories:
    python test_suite_runner.py --category unit
    python test_suite_runner.py --category integration
    python test_suite_runner.py --category performance

Generate coverage report:
    python test_suite_runner.py --coverage

Run tests and generate HTML report:
    python test_suite_runner.py --html-report
"""

import subprocess
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class TestSuiteRunner:
    """Comprehensive test suite runner for P/B analysis module"""
    
    def __init__(self):
        """Initialize test suite runner"""
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Test file mapping
        self.test_files = {
            'multi_source_validation': 'test_pb_multi_source_validation.py',
            'integration_tests': 'test_unified_data_adapter_integration.py',
            'existing_pb_tests': [
                'test_pb_historical_analysis.py',
                'test_pb_statistical_analysis.py',
                'test_pb_fair_value_calculator.py',
                'test_pb_integration.py'
            ]
        }
        
        # Test categories
        self.test_categories = {
            'unit': [
                'test_pb_multi_source_validation.py::TestUnitTestsForFairValueCalculations',
                'test_pb_multi_source_validation.py::TestStatisticalAnalysisValidation'
            ],
            'integration': [
                'test_pb_multi_source_validation.py::TestMultiSourceValidation',
                'test_unified_data_adapter_integration.py::TestUnifiedDataAdapterIntegration'
            ],
            'caching': [
                'test_pb_multi_source_validation.py::TestCachingBehavior',
                'test_unified_data_adapter_integration.py::TestUnifiedDataAdapterIntegration::test_cache_integration_workflow'
            ],
            'error_handling': [
                'test_pb_multi_source_validation.py::TestErrorHandlingAndFallbacks'
            ],
            'performance': [
                'test_pb_multi_source_validation.py::TestPerformanceWithLargeDatasets',
                'test_unified_data_adapter_integration.py::TestUnifiedDataAdapterIntegration::test_concurrent_requests_handling'
            ],
            'api_dependent': [
                'test_unified_data_adapter_integration.py::TestRealDataSourceIntegration'
            ]
        }
    
    def run_tests(self, category: Optional[str] = None, 
                 include_coverage: bool = False,
                 generate_html: bool = False,
                 verbose: bool = True) -> Dict[str, Any]:
        """
        Run test suite with specified options
        
        Args:
            category: Test category to run (None for all)
            include_coverage: Include coverage analysis
            generate_html: Generate HTML test report
            verbose: Verbose output
            
        Returns:
            Dict with test results and metrics
        """
        
        self.start_time = datetime.now()
        print(f"Starting P/B Historical Fair Value Test Suite at {self.start_time}")
        print("=" * 80)
        
        try:
            if category:
                results = self._run_category_tests(category, include_coverage, verbose)
            else:
                results = self._run_all_tests(include_coverage, verbose)
            
            self.end_time = datetime.now()
            
            # Generate reports
            if generate_html:
                self._generate_html_report(results)
            
            self._print_summary(results)
            
            return results
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_category_tests(self, category: str, include_coverage: bool, verbose: bool) -> Dict[str, Any]:
        """Run tests for a specific category"""
        
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}. Available: {list(self.test_categories.keys())}")
        
        print(f"Running {category.upper()} tests...")
        print("-" * 40)
        
        test_specs = self.test_categories[category]
        results = []
        
        for test_spec in test_specs:
            result = self._run_pytest_command(test_spec, include_coverage, verbose)
            results.append({
                'test_spec': test_spec,
                'result': result
            })
        
        return {
            'category': category,
            'results': results,
            'success': all(r['result']['success'] for r in results)
        }
    
    def _run_all_tests(self, include_coverage: bool, verbose: bool) -> Dict[str, Any]:
        """Run all test categories"""
        
        all_results = {}
        overall_success = True
        
        for category in self.test_categories.keys():
            if category == 'api_dependent':
                print(f"Skipping {category} tests (requires API keys)")
                continue
            
            print(f"\nRunning {category.upper()} tests...")
            print("-" * 40)
            
            category_result = self._run_category_tests(category, False, verbose)  # Coverage only at end
            all_results[category] = category_result
            
            if not category_result['success']:
                overall_success = False
        
        # Run coverage analysis if requested
        if include_coverage:
            print("\nGenerating coverage report...")
            coverage_result = self._run_coverage_analysis()
            all_results['coverage'] = coverage_result
        
        return {
            'all_categories': all_results,
            'overall_success': overall_success,
            'execution_time': (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }
    
    def _run_pytest_command(self, test_spec: str, include_coverage: bool, verbose: bool) -> Dict[str, Any]:
        """Run a pytest command and capture results"""
        
        cmd = ['python', '-m', 'pytest']
        
        # Add test specification
        cmd.append(test_spec)
        
        # Add options
        if verbose:
            cmd.append('-v')
        
        cmd.extend(['--tb=short', '--disable-warnings'])
        
        # Add coverage if requested
        if include_coverage:
            cmd.extend(['--cov=.', '--cov-report=term-missing'])
        
        # Add markers to skip slow/API tests by default
        if 'api_dependent' not in test_spec:
            cmd.extend(['-m', 'not api_dependent'])
        
        try:
            print(f"Executing: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time,
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'execution_time': 300
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis across all test files"""
        
        cmd = [
            'python', '-m', 'pytest',
            'test_pb_multi_source_validation.py',
            'test_unified_data_adapter_integration.py',
            '--cov=pb_historical_analysis',
            '--cov=unified_data_adapter',
            '--cov=pb_calculation_engine',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=json:coverage.json',
            '-m', 'not api_dependent'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for coverage
            )
            
            # Parse coverage JSON if available
            coverage_data = None
            coverage_file = self.project_root / 'coverage.json'
            if coverage_file.exists():
                try:
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not parse coverage JSON: {e}")
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'coverage_data': coverage_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_html_report(self, results: Dict[str, Any]) -> None:
        """Generate HTML test report"""
        
        try:
            # Run pytest with HTML report generation
            cmd = [
                'python', '-m', 'pytest',
                'test_pb_multi_source_validation.py',
                'test_unified_data_adapter_integration.py',
                '--html=test_report.html',
                '--self-contained-html',
                '-v',
                '-m', 'not api_dependent'
            ]
            
            subprocess.run(cmd, cwd=self.project_root, timeout=300)
            print("\nHTML test report generated: test_report.html")
            
        except Exception as e:
            print(f"Warning: Could not generate HTML report: {e}")
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print test execution summary"""
        
        print("\n" + "=" * 80)
        print("TEST SUITE EXECUTION SUMMARY")
        print("=" * 80)
        
        if 'all_categories' in results:
            # Summary for all categories
            total_categories = len(results['all_categories'])
            successful_categories = sum(1 for r in results['all_categories'].values() if r['success'])
            
            print(f"Categories executed: {total_categories}")
            print(f"Categories passed: {successful_categories}")
            print(f"Overall success: {'PASS' if results['overall_success'] else 'FAIL'}")
            
            if results.get('execution_time'):
                print(f"Total execution time: {results['execution_time']:.2f} seconds")
            
            # Category breakdown
            print("\nCategory Results:")
            for category, result in results['all_categories'].items():
                status = "PASS" if result['success'] else "FAIL"
                print(f"  {category.upper()}: {status}")
            
            # Coverage summary
            if 'coverage' in results and results['coverage']['success']:
                print("\nCoverage Analysis: COMPLETED")
                print("  HTML coverage report: htmlcov/index.html")
        
        else:
            # Summary for single category
            category = results.get('category', 'Unknown')
            status = "PASS" if results['success'] else "FAIL"
            print(f"Category: {category.upper()}")
            print(f"Result: {status}")
            
            print(f"\nTest Results:")
            for test_result in results['results']:
                test_name = test_result['test_spec'].split('::')[-1] if '::' in test_result['test_spec'] else test_result['test_spec']
                test_status = "PASS" if test_result['result']['success'] else "FAIL"
                exec_time = test_result['result'].get('execution_time', 0)
                print(f"  {test_name}: {test_status} ({exec_time:.2f}s)")
        
        print("\n" + "=" * 80)
        
        # Final recommendations
        if results.get('overall_success', results.get('success', False)):
            print("✅ All tests passed! P/B Historical Fair Value module is ready for production.")
        else:
            print("❌ Some tests failed. Please review the output above and fix issues before deployment.")
            print("\nCommon issues to check:")
            print("  - Missing dependencies (run: pip install -r requirements.txt)")
            print("  - Data source configuration issues")
            print("  - Network connectivity for API-dependent tests")
            print("  - Cache directory permissions")


def main():
    """Main entry point for test suite runner"""
    
    parser = argparse.ArgumentParser(description='P/B Historical Fair Value Test Suite Runner')
    
    parser.add_argument(
        '--category',
        choices=['unit', 'integration', 'caching', 'error_handling', 'performance', 'api_dependent'],
        help='Run specific test category'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Include coverage analysis'
    )
    
    parser.add_argument(
        '--html-report',
        action='store_true',
        help='Generate HTML test report'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    # Create and run test suite
    runner = TestSuiteRunner()
    
    results = runner.run_tests(
        category=args.category,
        include_coverage=args.coverage,
        generate_html=args.html_report,
        verbose=not args.quiet
    )
    
    # Exit with appropriate code
    if results.get('overall_success', results.get('success', False)):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()