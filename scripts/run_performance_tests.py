#!/usr/bin/env python3
"""
Performance Test Suite Runner
============================

Comprehensive script for running the performance test suite with various configurations
and generating detailed performance reports.

Usage:
    # Run all performance tests
    python scripts/run_performance_tests.py

    # Run specific test category
    python scripts/run_performance_tests.py --category benchmark

    # Run with baseline comparison
    python scripts/run_performance_tests.py --compare-baseline

    # Run with memory profiling
    python scripts/run_performance_tests.py --memory-profile

    # Generate performance report
    python scripts/run_performance_tests.py --report-only
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import psutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PerformanceTestRunner:
    """Manages performance test execution and reporting"""

    def __init__(self):
        self.project_root = project_root
        self.performance_dir = self.project_root / "tests" / "performance"
        self.results_dir = self.project_root / "performance_results"
        self.results_dir.mkdir(exist_ok=True)

    def run_benchmark_tests(self, save_baseline: bool = False, compare_baseline: bool = False) -> Dict[str, Any]:
        """Run pytest-benchmark tests"""
        print("🚀 Running benchmark tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_benchmark_suite.py"),
            "--benchmark-only",
            "-v"
        ]

        if save_baseline:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cmd.extend(["--benchmark-save", f"baseline_{timestamp}"])

        if compare_baseline:
            cmd.extend(["--benchmark-compare", "baseline"])

        result = self._run_command(cmd)
        return {
            "category": "benchmark",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_load_tests(self) -> Dict[str, Any]:
        """Run load and stress tests"""
        print("📈 Running load tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_load_testing_suite.py"),
            "-v",
            "-m", "not stress_test"  # Run normal load tests, not stress tests
        ]

        result = self._run_command(cmd)
        return {
            "category": "load_testing",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests (high load scenarios)"""
        print("💪 Running stress tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_load_testing_suite.py"),
            "-v",
            "-m", "stress_test"
        ]

        result = self._run_command(cmd)
        return {
            "category": "stress_testing",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_excel_stress_tests(self) -> Dict[str, Any]:
        """Run Excel processing stress tests"""
        print("📊 Running Excel stress tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_excel_stress_suite.py"),
            "-v"
        ]

        result = self._run_command(cmd)
        return {
            "category": "excel_stress",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_api_performance_tests(self) -> Dict[str, Any]:
        """Run API performance tests"""
        print("🌐 Running API performance tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_api_performance_suite.py"),
            "-v",
            "-m", "not real_api"  # Use mock APIs by default
        ]

        result = self._run_command(cmd)
        return {
            "category": "api_performance",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_regression_detection(self) -> Dict[str, Any]:
        """Run regression detection tests"""
        print("🔍 Running regression detection tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_regression_detection.py"),
            "-v"
        ]

        result = self._run_command(cmd)
        return {
            "category": "regression_detection",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_memory_profile_tests(self) -> Dict[str, Any]:
        """Run tests with memory profiling"""
        print("🧠 Running memory profiling tests...")

        try:
            import memory_profiler
        except ImportError:
            print("⚠️  memory-profiler not available, skipping memory profiling tests")
            return {
                "category": "memory_profiling",
                "success": False,
                "error": "memory-profiler not installed"
            }

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_benchmark_suite.py::TestMemoryBenchmarks"),
            "-v",
            "-s"  # Show print statements for memory profiling output
        ]

        result = self._run_command(cmd)
        return {
            "category": "memory_profiling",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_existing_performance_tests(self) -> Dict[str, Any]:
        """Run existing performance tests to ensure compatibility"""
        print("🔄 Running existing performance tests...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.performance_dir / "test_performance_regression.py"),
            "-v"
        ]

        result = self._run_command(cmd)
        return {
            "category": "existing_performance",
            "success": result.returncode == 0,
            "duration": getattr(result, 'duration', 0),
            "output": result.stdout if hasattr(result, 'stdout') else ""
        }

    def run_all_tests(self, save_baseline: bool = False, compare_baseline: bool = False, include_stress: bool = False) -> List[Dict[str, Any]]:
        """Run comprehensive performance test suite"""
        print("🎯 Running comprehensive performance test suite...")
        print("=" * 60)

        results = []

        # Core benchmark tests
        results.append(self.run_benchmark_tests(save_baseline, compare_baseline))

        # Load testing
        results.append(self.run_load_tests())

        # Excel stress tests
        results.append(self.run_excel_stress_tests())

        # API performance tests
        results.append(self.run_api_performance_tests())

        # Regression detection
        results.append(self.run_regression_detection())

        # Memory profiling
        results.append(self.run_memory_profile_tests())

        # Existing performance tests
        results.append(self.run_existing_performance_tests())

        # Stress tests (optional, as they take longer)
        if include_stress:
            results.append(self.run_stress_tests())

        return results

    def generate_performance_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive performance report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # System information
        system_info = {
            "timestamp": timestamp,
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown"
        }

        report_lines = [
            "Performance Test Suite Report",
            "=" * 50,
            f"Generated: {timestamp}",
            "",
            "System Information:",
            f"  Python Version: {system_info['python_version']}",
            f"  Platform: {system_info['platform']}",
            f"  CPU Cores: {system_info['cpu_count']}",
            f"  Memory: {system_info['memory_gb']} GB",
            f"  CPU Frequency: {system_info['cpu_freq_mhz']} MHz",
            "",
            "Test Results Summary:",
            "-" * 25
        ]

        # Summary statistics
        total_tests = len(results)
        successful_tests = len([r for r in results if r.get('success', False)])
        failed_tests = total_tests - successful_tests
        total_duration = sum(r.get('duration', 0) for r in results)

        report_lines.extend([
            f"Total test categories: {total_tests}",
            f"Successful: {successful_tests}",
            f"Failed: {failed_tests}",
            f"Total duration: {total_duration:.2f} seconds",
            f"Success rate: {(successful_tests/total_tests*100):.1f}%",
            ""
        ])

        # Detailed results
        report_lines.append("Detailed Results:")
        report_lines.append("-" * 20)

        for result in results:
            category = result.get('category', 'unknown')
            success = result.get('success', False)
            duration = result.get('duration', 0)
            status = "✅ PASS" if success else "❌ FAIL"

            report_lines.append(f"{category.upper()}: {status} ({duration:.2f}s)")

            if not success and 'error' in result:
                report_lines.append(f"  Error: {result['error']}")

            if 'output' in result and result['output']:
                # Include first few lines of output for context
                output_lines = result['output'].split('\n')[:3]
                for line in output_lines:
                    if line.strip():
                        report_lines.append(f"  {line.strip()}")

            report_lines.append("")

        # Recommendations
        report_lines.extend([
            "Recommendations:",
            "-" * 15
        ])

        if failed_tests > 0:
            report_lines.append("• Review failed test categories and address issues")

        if successful_tests == total_tests:
            report_lines.append("• ✅ All performance tests passed successfully!")
            report_lines.append("• Consider running stress tests for additional validation")

        report_lines.extend([
            "• Monitor performance metrics over time",
            "• Set up automated performance regression detection",
            "• Consider performance optimization for slow operations",
            "",
            "Next Steps:",
            "• Save current results as baseline: --save-baseline",
            "• Compare future runs against baseline: --compare-baseline",
            "• Run stress tests: --include-stress",
            ""
        ])

        return "\n".join(report_lines)

    def save_results(self, results: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Save test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_results_{timestamp}.json"

        filepath = self.results_dir / filename

        results_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            },
            "results": results
        }

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)

        return str(filepath)

    def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run command and measure execution time"""
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            result.duration = time.time() - start_time
            return result

        except subprocess.TimeoutExpired:
            print(f"⚠️  Command timed out after 5 minutes: {' '.join(cmd)}")
            result = subprocess.CompletedProcess(cmd, 1, "", "Timeout")
            result.duration = time.time() - start_time
            return result

        except Exception as e:
            print(f"❌ Error running command: {e}")
            result = subprocess.CompletedProcess(cmd, 1, "", str(e))
            result.duration = time.time() - start_time
            return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Performance Test Suite Runner")

    parser.add_argument(
        "--category",
        choices=["benchmark", "load", "stress", "excel", "api", "regression", "memory", "existing", "all"],
        default="all",
        help="Test category to run"
    )

    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save benchmark results as baseline"
    )

    parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Compare results against baseline"
    )

    parser.add_argument(
        "--include-stress",
        action="store_true",
        help="Include stress tests (longer execution time)"
    )

    parser.add_argument(
        "--memory-profile",
        action="store_true",
        help="Run with memory profiling"
    )

    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report from existing results"
    )

    parser.add_argument(
        "--output",
        help="Output file for results"
    )

    args = parser.parse_args()

    runner = PerformanceTestRunner()

    if args.report_only:
        print("📊 Generating performance report from existing results...")
        # This would load and process existing results
        print("No existing results found. Run tests first.")
        return

    print("🏃‍♂️ Starting Performance Test Suite")
    print(f"Project Root: {runner.project_root}")
    print(f"Performance Tests: {runner.performance_dir}")
    print(f"Results Directory: {runner.results_dir}")
    print("")

    # Run tests based on category
    if args.category == "all":
        results = runner.run_all_tests(
            save_baseline=args.save_baseline,
            compare_baseline=args.compare_baseline,
            include_stress=args.include_stress
        )
    else:
        # Run specific category
        category_map = {
            "benchmark": runner.run_benchmark_tests,
            "load": runner.run_load_tests,
            "stress": runner.run_stress_tests,
            "excel": runner.run_excel_stress_tests,
            "api": runner.run_api_performance_tests,
            "regression": runner.run_regression_detection,
            "memory": runner.run_memory_profile_tests,
            "existing": runner.run_existing_performance_tests
        }

        test_func = category_map.get(args.category)
        if test_func:
            if args.category == "benchmark":
                result = test_func(args.save_baseline, args.compare_baseline)
            else:
                result = test_func()
            results = [result]
        else:
            print(f"❌ Unknown category: {args.category}")
            return

    # Generate and display report
    report = runner.generate_performance_report(results)
    print("\n" + "="*60)
    print(report)

    # Save results
    results_file = runner.save_results(results, args.output)
    print(f"📁 Results saved to: {results_file}")

    # Exit with appropriate code
    failed_tests = len([r for r in results if not r.get('success', False)])
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    main()