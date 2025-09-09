#!/usr/bin/env python3
"""
Comprehensive test runner for the Financial Analysis Application.

This script provides various test execution scenarios with proper configuration
and reporting for different development and CI/CD needs.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class TestRunner:
    """Test runner with different execution strategies."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        os.chdir(self.project_root)
    
    def run_basic_tests(self):
        """Run basic smoke tests to verify core functionality."""
        print("Running Basic Tests...")
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_basic.py",
            "-v", "--tb=short"
        ]
        return self._execute_command(cmd)
    
    def run_unit_tests(self, fail_fast=True, timeout=30):
        """Run unit tests with optional fail-fast behavior."""
        print("[UNIT] Running Unit Tests...")
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v", "--tb=short",
            f"--timeout={timeout}"
        ]
        
        if fail_fast:
            cmd.append("-x")
        
        return self._execute_command(cmd)
    
    def run_integration_tests(self, timeout=60):
        """Run integration tests with extended timeout."""
        print("🔗 Running Integration Tests...")
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v", "--tb=short",
            f"--timeout={timeout}",
            "-k", "not yfinance"  # Skip yfinance tests that require network
        ]
        return self._execute_command(cmd)
    
    def run_performance_tests(self, optimized=True):
        """Run performance tests with optional optimized version."""
        print("[PERF] Running Performance Tests...")
        
        if optimized:
            # Run optimized performance tests
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/performance/test_optimized_performance.py",
                "-v", "--tb=short",
                "--timeout=60",
                "-m", "performance"
            ]
        else:
            # Run all performance tests (may be slow)
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/performance/",
                "-v", "--tb=short",
                "--timeout=180",
                "-m", "performance"
            ]
        
        return self._execute_command(cmd)
    
    def run_e2e_tests(self, headless=True):
        """Run E2E tests with Playwright."""
        print("[E2E] Running E2E Tests...")
        
        # Check if Streamlit is running
        if not self._check_streamlit_running():
            print("[WARN]  Starting Streamlit application for E2E tests...")
            streamlit_proc = self._start_streamlit()
            if not streamlit_proc:
                print("[FAIL] Failed to start Streamlit. Skipping E2E tests.")
                return False
        else:
            streamlit_proc = None
        
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/e2e/test_streamlit_app.py::test_app_loads_successfully",
                "-v", "--tb=short",
                "--browser=chromium"
            ]
            
            if headless:
                cmd.extend(["--headed=false"])
            
            result = self._execute_command(cmd)
            
        finally:
            if streamlit_proc:
                streamlit_proc.terminate()
        
        return result
    
    def run_regression_tests(self):
        """Run regression tests to ensure bug fixes."""
        print("🔄 Running Regression Tests...")
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/regression/",
            "-v", "--tb=short",
            "--timeout=60"
        ]
        return self._execute_command(cmd)
    
    def run_quick_suite(self):
        """Run a quick test suite for rapid feedback."""
        print("🚀 Running Quick Test Suite...")
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_basic.py",
            "tests/unit/test_financial_calculations.py",
            "tests/integration/api/test_api_behavior.py",
            "-v", "--tb=short",
            "--timeout=30",
            "-x"  # Stop on first failure
        ]
        return self._execute_command(cmd)
    
    def run_comprehensive_suite(self, skip_slow=True):
        """Run comprehensive test suite."""
        print("📋 Running Comprehensive Test Suite...")
        
        tests_to_skip = []
        if skip_slow:
            tests_to_skip.extend(["slow", "e2e"])
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v", "--tb=short",
            "--timeout=120"
        ]
        
        if tests_to_skip:
            skip_expr = " and ".join([f"not {marker}" for marker in tests_to_skip])
            cmd.extend(["-m", skip_expr])
        
        return self._execute_command(cmd)
    
    def run_with_coverage(self):
        """Run tests with coverage reporting."""
        print("[COV] Running Tests with Coverage...")
        
        try:
            import pytest_cov
        except ImportError:
            print("[FAIL] pytest-cov not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest-cov"])
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "tests/integration/",
            "--cov=core",
            "--cov=config",
            "--cov=utils",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v", "--tb=short"
        ]
        return self._execute_command(cmd)
    
    def _execute_command(self, cmd):
        """Execute a command and return success status."""
        print(f"[EXEC] Executing: {' '.join(cmd)}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            result = subprocess.run(cmd, check=False, capture_output=False)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"[OK] Success! Completed in {execution_time:.2f}s")
                return True
            else:
                print(f"[FAIL] Failed with exit code {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print("[WARN] Interrupted by user")
            return False
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            return False
    
    def _check_streamlit_running(self, port=8501):
        """Check if Streamlit is running on the specified port."""
        try:
            import requests
            response = requests.get(f"http://localhost:{port}", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _start_streamlit(self):
        """Start Streamlit application for testing."""
        try:
            cmd = [
                sys.executable, "-m", "streamlit", "run", "ui/streamlit/fcf_analysis_streamlit.py",
                "--server.port=8501",
                "--server.headless=true",
                "--server.runOnSave=false",
                "--logger.level=error"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for startup
            for _ in range(30):
                if self._check_streamlit_running():
                    return proc
                time.sleep(1)
            
            proc.terminate()
            return None
            
        except Exception as e:
            print(f"Error starting Streamlit: {e}")
            return None


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Financial Analysis Test Runner")
    parser.add_argument("suite", nargs="?", default="quick", 
                       choices=["basic", "unit", "integration", "performance", "e2e", 
                               "regression", "quick", "comprehensive", "coverage"],
                       help="Test suite to run")
    parser.add_argument("--headed", action="store_true", 
                       help="Run E2E tests with visible browser")
    parser.add_argument("--fail-fast", action="store_true", 
                       help="Stop on first failure")
    parser.add_argument("--timeout", type=int, default=60,
                       help="Test timeout in seconds")
    parser.add_argument("--include-slow", action="store_true",
                       help="Include slow tests in comprehensive suite")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("Financial Analysis Test Runner")
    print("=" * 50)
    
    success = False
    
    if args.suite == "basic":
        success = runner.run_basic_tests()
    elif args.suite == "unit":
        success = runner.run_unit_tests(fail_fast=args.fail_fast, timeout=args.timeout)
    elif args.suite == "integration":
        success = runner.run_integration_tests(timeout=args.timeout)
    elif args.suite == "performance":
        success = runner.run_performance_tests(optimized=True)
    elif args.suite == "e2e":
        success = runner.run_e2e_tests(headless=not args.headed)
    elif args.suite == "regression":
        success = runner.run_regression_tests()
    elif args.suite == "quick":
        success = runner.run_quick_suite()
    elif args.suite == "comprehensive":
        success = runner.run_comprehensive_suite(skip_slow=not args.include_slow)
    elif args.suite == "coverage":
        success = runner.run_with_coverage()
    
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] All tests completed successfully!")
        sys.exit(0)
    else:
        print("[ERROR] Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()