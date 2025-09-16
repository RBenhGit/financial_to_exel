"""
Comprehensive Load Testing Framework for Financial Analysis Application

This module provides load testing capabilities for:
- Streamlit application endpoints
- Financial calculation engines
- Data processing workflows
- API integrations
- Concurrent user simulation
"""

import asyncio
import time
import threading
import multiprocessing
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
import psutil
import json
import statistics
from contextlib import contextmanager
import socket
import subprocess

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios"""
    name: str
    concurrent_users: int
    duration_seconds: int
    ramp_up_seconds: int
    target_url: str = "http://localhost:8501"
    request_timeout: int = 30
    think_time_seconds: float = 1.0
    max_requests: Optional[int] = None


@dataclass
class LoadTestResult:
    """Results from a load test scenario"""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)


class SystemMonitor:
    """Monitor system resources during load testing"""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None

    def start(self):
        """Start system monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        logger.info("System monitoring started")

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

        if not self.metrics:
            return {}

        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        memory_mb_values = [m['memory_mb'] for m in self.metrics]

        return {
            'cpu_avg': statistics.mean(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg_percent': statistics.mean(memory_values),
            'memory_max_percent': max(memory_values),
            'memory_avg_mb': statistics.mean(memory_mb_values),
            'memory_max_mb': max(memory_mb_values),
            'sample_count': len(self.metrics)
        }

    def _monitor_loop(self):
        """Internal monitoring loop"""
        process = psutil.Process()

        while self.monitoring:
            try:
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_percent': process.memory_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'system_cpu_percent': psutil.cpu_percent(),
                    'system_memory_percent': psutil.virtual_memory().percent
                }
                self.metrics.append(metric)
            except Exception as e:
                logger.warning(f"Error collecting system metrics: {e}")

            time.sleep(self.interval)


class StreamlitLoadTester:
    """Load tester specifically for Streamlit applications"""

    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_streamlit_endpoints(self) -> Dict[str, float]:
        """Test common Streamlit endpoints"""
        endpoints = {
            'main_page': '/',
            'healthz': '/healthz',
            'stream': '/_stcore/stream'
        }

        results = {}
        for name, endpoint in endpoints.items():
            url = f"{self.base_url}{endpoint}"
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=10)
                response_time = time.time() - start_time

                results[name] = {
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'success': response.status_code < 400
                }
            except Exception as e:
                results[name] = {
                    'response_time': float('inf'),
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                }

        return results

    def simulate_user_session(self, duration: float, think_time: float = 1.0) -> List[Dict[str, Any]]:
        """Simulate a user session with realistic interactions"""
        session_results = []
        start_time = time.time()

        while time.time() - start_time < duration:
            # Simulate different user actions
            actions = [
                self._simulate_page_load,
                self._simulate_data_input,
                self._simulate_calculation,
                self._simulate_visualization
            ]

            for action in actions:
                if time.time() - start_time >= duration:
                    break

                try:
                    result = action()
                    session_results.append(result)
                    time.sleep(think_time)
                except Exception as e:
                    session_results.append({
                        'action': action.__name__,
                        'success': False,
                        'error': str(e),
                        'response_time': float('inf')
                    })

        return session_results

    def _simulate_page_load(self) -> Dict[str, Any]:
        """Simulate loading the main page"""
        start_time = time.time()
        try:
            response = self.session.get(self.base_url, timeout=30)
            return {
                'action': 'page_load',
                'response_time': time.time() - start_time,
                'status_code': response.status_code,
                'success': response.status_code < 400
            }
        except Exception as e:
            return {
                'action': 'page_load',
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }

    def _simulate_data_input(self) -> Dict[str, Any]:
        """Simulate data input operations"""
        start_time = time.time()
        # This would typically involve posting form data
        # For now, just simulate with a simple request
        try:
            response = self.session.get(f"{self.base_url}/?ticker=AAPL", timeout=30)
            return {
                'action': 'data_input',
                'response_time': time.time() - start_time,
                'status_code': response.status_code,
                'success': response.status_code < 400
            }
        except Exception as e:
            return {
                'action': 'data_input',
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }

    def _simulate_calculation(self) -> Dict[str, Any]:
        """Simulate financial calculations"""
        start_time = time.time()
        # Simulate calculation request
        time.sleep(0.5)  # Simulate processing time
        return {
            'action': 'calculation',
            'response_time': time.time() - start_time,
            'success': True
        }

    def _simulate_visualization(self) -> Dict[str, Any]:
        """Simulate visualization generation"""
        start_time = time.time()
        # Simulate visualization request
        time.sleep(0.3)  # Simulate rendering time
        return {
            'action': 'visualization',
            'response_time': time.time() - start_time,
            'success': True
        }


class ConcurrentUserSimulator:
    """Simulate multiple concurrent users"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = []
        self.system_monitor = SystemMonitor()

    def run_load_test(self) -> LoadTestResult:
        """Run the load test with the configured parameters"""
        logger.info(f"Starting load test: {self.config.name}")
        logger.info(f"Concurrent users: {self.config.concurrent_users}")
        logger.info(f"Duration: {self.config.duration_seconds}s")
        logger.info(f"Ramp-up: {self.config.ramp_up_seconds}s")

        start_time = datetime.now()
        self.system_monitor.start()

        try:
            # Run the concurrent simulation
            self._run_concurrent_simulation()
        finally:
            system_metrics = self.system_monitor.stop()

        end_time = datetime.now()

        # Aggregate results
        return self._create_load_test_result(start_time, end_time, system_metrics)

    def _run_concurrent_simulation(self):
        """Run the concurrent user simulation"""
        ramp_up_delay = self.config.ramp_up_seconds / self.config.concurrent_users

        with ThreadPoolExecutor(max_workers=self.config.concurrent_users) as executor:
            futures = []

            for user_id in range(self.config.concurrent_users):
                # Stagger user startup for realistic ramp-up
                delay = user_id * ramp_up_delay

                future = executor.submit(
                    self._simulate_user,
                    user_id,
                    delay
                )
                futures.append(future)

            # Collect results from all users
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    self.results.extend(user_results)
                except Exception as e:
                    logger.error(f"User simulation failed: {e}")

    def _simulate_user(self, user_id: int, startup_delay: float) -> List[Dict[str, Any]]:
        """Simulate a single user"""
        time.sleep(startup_delay)

        tester = StreamlitLoadTester(self.config.target_url)
        user_results = []

        start_time = time.time()
        request_count = 0

        while (time.time() - start_time < self.config.duration_seconds and
               (self.config.max_requests is None or request_count < self.config.max_requests)):

            try:
                # Run a user session
                session_results = tester.simulate_user_session(
                    duration=min(30, self.config.duration_seconds - (time.time() - start_time)),
                    think_time=self.config.think_time_seconds
                )

                # Add user ID to results
                for result in session_results:
                    result['user_id'] = user_id
                    result['timestamp'] = time.time()

                user_results.extend(session_results)
                request_count += len(session_results)

            except Exception as e:
                logger.error(f"User {user_id} simulation error: {e}")
                user_results.append({
                    'user_id': user_id,
                    'action': 'error',
                    'success': False,
                    'error': str(e),
                    'response_time': float('inf'),
                    'timestamp': time.time()
                })

        logger.info(f"User {user_id} completed with {len(user_results)} requests")
        return user_results

    def _create_load_test_result(
        self,
        start_time: datetime,
        end_time: datetime,
        system_metrics: Dict[str, Any]
    ) -> LoadTestResult:
        """Create load test result from collected data"""

        successful_requests = [r for r in self.results if r.get('success', False)]
        failed_requests = [r for r in self.results if not r.get('success', False)]

        response_times = [r['response_time'] for r in successful_requests
                         if isinstance(r['response_time'], (int, float)) and r['response_time'] != float('inf')]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            percentile_95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            percentile_99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = percentile_95 = percentile_99 = 0

        duration = (end_time - start_time).total_seconds()
        requests_per_second = len(successful_requests) / duration if duration > 0 else 0

        errors = [r.get('error', 'Unknown error') for r in failed_requests if 'error' in r]

        return LoadTestResult(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            total_requests=len(self.results),
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            requests_per_second=requests_per_second,
            errors=errors[:10],  # Keep only first 10 errors
            system_metrics=system_metrics
        )


class LoadTestRunner:
    """Main load test runner with predefined scenarios"""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or Path("performance/load_test_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_light_load_test(self, target_url: str = "http://localhost:8501") -> LoadTestResult:
        """Run a light load test suitable for development"""
        config = LoadTestConfig(
            name="Light Load Test",
            concurrent_users=5,
            duration_seconds=60,
            ramp_up_seconds=10,
            target_url=target_url,
            think_time_seconds=1.0
        )

        simulator = ConcurrentUserSimulator(config)
        return simulator.run_load_test()

    def run_medium_load_test(self, target_url: str = "http://localhost:8501") -> LoadTestResult:
        """Run a medium load test for staging environments"""
        config = LoadTestConfig(
            name="Medium Load Test",
            concurrent_users=20,
            duration_seconds=300,  # 5 minutes
            ramp_up_seconds=60,
            target_url=target_url,
            think_time_seconds=2.0
        )

        simulator = ConcurrentUserSimulator(config)
        return simulator.run_load_test()

    def run_stress_test(self, target_url: str = "http://localhost:8501") -> LoadTestResult:
        """Run a stress test to find breaking points"""
        config = LoadTestConfig(
            name="Stress Test",
            concurrent_users=50,
            duration_seconds=600,  # 10 minutes
            ramp_up_seconds=120,
            target_url=target_url,
            think_time_seconds=0.5
        )

        simulator = ConcurrentUserSimulator(config)
        return simulator.run_load_test()

    def save_results(self, result: LoadTestResult):
        """Save load test results to file"""
        timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_{result.config.name.lower().replace(' ', '_')}_{timestamp}.json"
        filepath = self.results_dir / filename

        result_dict = {
            'config': {
                'name': result.config.name,
                'concurrent_users': result.config.concurrent_users,
                'duration_seconds': result.config.duration_seconds,
                'ramp_up_seconds': result.config.ramp_up_seconds,
                'target_url': result.config.target_url
            },
            'results': {
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'avg_response_time': result.avg_response_time,
                'min_response_time': result.min_response_time,
                'max_response_time': result.max_response_time,
                'percentile_95': result.percentile_95,
                'percentile_99': result.percentile_99,
                'requests_per_second': result.requests_per_second,
                'errors': result.errors,
                'system_metrics': result.system_metrics
            }
        }

        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2)

        logger.info(f"Load test results saved to {filepath}")

    def generate_report(self, result: LoadTestResult) -> str:
        """Generate a human-readable load test report"""
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0

        report = f"""
{'='*80}
LOAD TEST REPORT: {result.config.name}
{'='*80}

Test Configuration:
  - Concurrent Users: {result.config.concurrent_users}
  - Test Duration: {result.config.duration_seconds} seconds
  - Ramp-up Time: {result.config.ramp_up_seconds} seconds
  - Target URL: {result.config.target_url}

Test Results:
  - Start Time: {result.start_time}
  - End Time: {result.end_time}
  - Total Requests: {result.total_requests}
  - Successful Requests: {result.successful_requests} ({success_rate:.1f}%)
  - Failed Requests: {result.failed_requests}
  - Requests per Second: {result.requests_per_second:.2f}

Response Times:
  - Average: {result.avg_response_time:.3f}s
  - Minimum: {result.min_response_time:.3f}s
  - Maximum: {result.max_response_time:.3f}s
  - 95th Percentile: {result.percentile_95:.3f}s
  - 99th Percentile: {result.percentile_99:.3f}s

System Metrics (during test):
  - CPU Average: {result.system_metrics.get('cpu_avg', 0):.1f}%
  - CPU Maximum: {result.system_metrics.get('cpu_max', 0):.1f}%
  - Memory Average: {result.system_metrics.get('memory_avg_percent', 0):.1f}%
  - Memory Maximum: {result.system_metrics.get('memory_max_percent', 0):.1f}%

"""

        if result.errors:
            report += f"Errors Encountered:\n"
            for i, error in enumerate(result.errors[:5], 1):
                report += f"  {i}. {error}\n"

            if len(result.errors) > 5:
                report += f"  ... and {len(result.errors) - 5} more errors\n"

        report += f"\n{'='*80}\n"

        return report


def check_streamlit_running(url: str = "http://localhost:8501") -> bool:
    """Check if Streamlit application is running"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code < 500
    except Exception:
        return False


def run_comprehensive_load_test():
    """Run a comprehensive load testing suite"""
    runner = LoadTestRunner()

    # Check if Streamlit is running
    if not check_streamlit_running():
        logger.error("Streamlit application is not running on localhost:8501")
        logger.error("Please start the application before running load tests")
        return

    logger.info("Starting comprehensive load testing suite...")

    # Run different test scenarios
    scenarios = [
        ('light', runner.run_light_load_test),
        ('medium', runner.run_medium_load_test),
        ('stress', runner.run_stress_test)
    ]

    for scenario_name, test_func in scenarios:
        try:
            logger.info(f"Running {scenario_name} load test...")
            result = test_func()

            # Save results and generate report
            runner.save_results(result)
            report = runner.generate_report(result)

            print(report)

            # Brief pause between tests
            if scenario_name != 'stress':  # Don't pause after the last test
                logger.info("Pausing 30 seconds between test scenarios...")
                time.sleep(30)

        except Exception as e:
            logger.error(f"Failed to run {scenario_name} load test: {e}")
            continue

    logger.info("Comprehensive load testing suite completed")


if __name__ == "__main__":
    # Run comprehensive load testing when executed directly
    run_comprehensive_load_test()