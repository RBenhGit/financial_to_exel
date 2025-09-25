"""
Simple Performance Test Runner
==============================

A simplified performance test runner that establishes baseline metrics for critical
financial engine operations without requiring complex mocking or external dependencies.
"""

import time
import psutil
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@dataclass
class SimplePerformanceResult:
    """Simple performance test result"""
    test_name: str
    duration_seconds: float
    memory_start_mb: float
    memory_end_mb: float
    cpu_percent: float
    operations_count: int
    success_count: int

    @property
    def memory_delta_mb(self) -> float:
        return self.memory_end_mb - self.memory_start_mb

    @property
    def success_rate(self) -> float:
        return (self.success_count / max(self.operations_count, 1)) * 100

    @property
    def ops_per_second(self) -> float:
        return self.operations_count / max(self.duration_seconds, 0.001)


class SimplePerformanceRunner:
    """Simple performance test runner"""

    def __init__(self):
        self.results = {}
        self.reports_dir = Path("performance_reports")
        self.reports_dir.mkdir(exist_ok=True)

    def run_all_tests(self):
        """Run all performance tests"""
        print("="*60)
        print("FINANCIAL ENGINE PERFORMANCE BASELINE TESTS")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System: {psutil.cpu_count()} cores, {psutil.virtual_memory().total / 1024**3:.1f}GB RAM")
        print("="*60)

        # Run computational performance tests
        self.test_mathematical_operations()
        self.test_data_processing()
        self.test_financial_calculations()
        self.test_memory_operations()

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

    def test_mathematical_operations(self):
        """Test mathematical operations performance"""
        print("Testing mathematical operations...")

        memory_start = self._get_memory_mb()
        start_time = time.time()
        success_count = 0

        # Simulate financial calculations
        for i in range(10000):
            try:
                # FCF calculation simulation
                cash_ops = 1000000 + i
                capex = 200000 + (i * 10)
                fcf = cash_ops - capex

                # Growth rate calculation
                prev_value = 1000 + i
                curr_value = 1100 + i
                growth_rate = (curr_value - prev_value) / prev_value

                # DCF present value calculation
                future_value = 50000 + i
                discount_rate = 0.10
                years = 5
                present_value = future_value / ((1 + discount_rate) ** years)

                success_count += 1
            except Exception:
                pass

        end_time = time.time()
        memory_end = self._get_memory_mb()

        self.results["mathematical_operations"] = SimplePerformanceResult(
            test_name="mathematical_operations",
            duration_seconds=end_time - start_time,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            cpu_percent=self._get_cpu_percent(),
            operations_count=10000,
            success_count=success_count
        )

        print(f"  [OK] Mathematical operations: {self.results['mathematical_operations'].ops_per_second:.0f} ops/sec")

    def test_data_processing(self):
        """Test data processing performance"""
        print("Testing data processing...")

        memory_start = self._get_memory_mb()
        start_time = time.time()
        success_count = 0

        # Create test data
        test_data = []
        for i in range(1000):
            try:
                # Simulate financial data processing
                financial_record = {
                    'year': 2020 + (i % 5),
                    'revenue': 1000000 + (i * 50000),
                    'expenses': 600000 + (i * 30000),
                    'net_income': None
                }

                # Process the record
                financial_record['net_income'] = financial_record['revenue'] - financial_record['expenses']
                financial_record['margin'] = financial_record['net_income'] / financial_record['revenue']

                test_data.append(financial_record)
                success_count += 1
            except Exception:
                pass

        # Aggregate calculations
        for i in range(100):
            try:
                total_revenue = sum(record['revenue'] for record in test_data)
                avg_margin = sum(record['margin'] for record in test_data) / len(test_data)
                growth_rates = []

                for j in range(1, len(test_data)):
                    prev_rev = test_data[j-1]['revenue']
                    curr_rev = test_data[j]['revenue']
                    growth_rates.append((curr_rev - prev_rev) / prev_rev)

                success_count += 1
            except Exception:
                pass

        end_time = time.time()
        memory_end = self._get_memory_mb()

        self.results["data_processing"] = SimplePerformanceResult(
            test_name="data_processing",
            duration_seconds=end_time - start_time,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            cpu_percent=self._get_cpu_percent(),
            operations_count=1100,  # 1000 + 100
            success_count=success_count
        )

        print(f"  [OK] Data processing: {self.results['data_processing'].ops_per_second:.0f} ops/sec")

    def test_financial_calculations(self):
        """Test financial calculations performance"""
        print("Testing financial calculations...")

        memory_start = self._get_memory_mb()
        start_time = time.time()
        success_count = 0

        # Test different financial calculation scenarios
        for i in range(5000):
            try:
                # DCF calculation simulation
                cash_flows = [50000 + (j * 5000) for j in range(5)]
                discount_rate = 0.10
                terminal_growth = 0.03

                # Calculate present values
                present_values = []
                for j, cf in enumerate(cash_flows):
                    pv = cf / ((1 + discount_rate) ** (j + 1))
                    present_values.append(pv)

                # Terminal value
                terminal_cf = cash_flows[-1] * (1 + terminal_growth)
                terminal_value = terminal_cf / (discount_rate - terminal_growth)
                terminal_pv = terminal_value / ((1 + discount_rate) ** len(cash_flows))

                # Total enterprise value
                enterprise_value = sum(present_values) + terminal_pv

                # DDM calculation simulation
                dividend = 2.50
                growth_rate = 0.05
                required_return = 0.12
                ddm_value = dividend * (1 + growth_rate) / (required_return - growth_rate)

                # P/B calculation simulation
                book_value = 45.0
                market_price = 55.0
                pb_ratio = market_price / book_value

                success_count += 1
            except Exception:
                pass

        end_time = time.time()
        memory_end = self._get_memory_mb()

        self.results["financial_calculations"] = SimplePerformanceResult(
            test_name="financial_calculations",
            duration_seconds=end_time - start_time,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            cpu_percent=self._get_cpu_percent(),
            operations_count=5000,
            success_count=success_count
        )

        print(f"  [OK] Financial calculations: {self.results['financial_calculations'].ops_per_second:.0f} ops/sec")

    def test_memory_operations(self):
        """Test memory-intensive operations"""
        print("Testing memory operations...")

        memory_start = self._get_memory_mb()
        start_time = time.time()
        success_count = 0

        # Create and manipulate large datasets
        datasets = []
        for i in range(50):
            try:
                # Create large financial dataset
                dataset = {
                    'company_data': [
                        {
                            'year': 2020 + (j % 5),
                            'metrics': [random_value for random_value in range(j, j + 100)]
                        }
                        for j in range(200)  # 200 years of data per dataset
                    ]
                }

                # Process the dataset
                for company in dataset['company_data']:
                    company['avg_metric'] = sum(company['metrics']) / len(company['metrics'])
                    company['growth'] = (company['metrics'][-1] - company['metrics'][0]) / company['metrics'][0] if company['metrics'][0] != 0 else 0

                datasets.append(dataset)
                success_count += 1

                # Clean up periodically to test memory management
                if i % 10 == 0:
                    datasets = datasets[-5:]  # Keep only last 5 datasets

            except Exception:
                pass

        end_time = time.time()
        memory_end = self._get_memory_mb()

        self.results["memory_operations"] = SimplePerformanceResult(
            test_name="memory_operations",
            duration_seconds=end_time - start_time,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            cpu_percent=self._get_cpu_percent(),
            operations_count=50,
            success_count=success_count
        )

        print(f"  [OK] Memory operations: {self.results['memory_operations'].memory_delta_mb:.1f}MB delta")

    def save_results(self):
        """Save performance results"""
        timestamp = datetime.now()
        results_file = self.reports_dir / f"baseline_performance_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

        # Convert results to serializable format
        serializable_results = {}
        for test_name, result in self.results.items():
            serializable_results[test_name] = asdict(result)

        # Add system information
        report_data = {
            'timestamp': timestamp.isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / 1024**3,
                'python_version': sys.version,
                'platform': os.name
            },
            'results': serializable_results,
            'baselines_established': {
                'mathematical_operations_baseline': serializable_results.get('mathematical_operations', {}).get('ops_per_second', 0),
                'data_processing_baseline': serializable_results.get('data_processing', {}).get('ops_per_second', 0),
                'financial_calculations_baseline': serializable_results.get('financial_calculations', {}).get('ops_per_second', 0),
                'memory_operations_baseline': serializable_results.get('memory_operations', {}).get('memory_delta_mb', 0)
            }
        }

        # Save to file
        with open(results_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\nResults saved to: {results_file}")

        # Also save as baseline file for future comparisons
        baseline_file = self.reports_dir / "performance_baselines.json"
        with open(baseline_file, 'w') as f:
            json.dump(report_data['baselines_established'], f, indent=2)

    def print_summary(self):
        """Print performance summary"""
        print("\n" + "="*60)
        print("PERFORMANCE BASELINE SUMMARY")
        print("="*60)

        for test_name, result in self.results.items():
            print(f"\n{test_name.replace('_', ' ').title()}:")
            print(f"  Duration: {result.duration_seconds:.3f}s")
            print(f"  Operations/sec: {result.ops_per_second:.0f}")
            print(f"  Memory delta: {result.memory_delta_mb:.1f}MB")
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  CPU usage: {result.cpu_percent:.1f}%")

        # Check for any concerning results
        warnings = []

        for test_name, result in self.results.items():
            if result.success_rate < 95.0:
                warnings.append(f"Low success rate in {test_name}: {result.success_rate:.1f}%")

            if result.memory_delta_mb > 50.0:
                warnings.append(f"High memory usage in {test_name}: {result.memory_delta_mb:.1f}MB")

        if warnings:
            print(f"\n[WARNING] Issues detected:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print(f"\n[OK] All performance metrics within acceptable ranges")

        print("="*60)

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            return psutil.Process().memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0


def main():
    """Main entry point"""
    runner = SimplePerformanceRunner()

    try:
        runner.run_all_tests()
        print(f"\n[SUCCESS] Performance baseline establishment completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Performance testing interrupted by user")
        return 1

    except Exception as e:
        print(f"\n[ERROR] Error during performance testing: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())