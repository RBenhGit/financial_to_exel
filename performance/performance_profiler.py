"""
Performance Profiler for Financial Analysis Application

This module provides comprehensive performance profiling including:
- Memory usage monitoring
- CPU usage tracking
- Import timing analysis
- Function-level profiling
- Streamlit-specific performance metrics
"""

import time
import psutil
import gc
import sys
import logging
import cProfile
import pstats
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
import tracemalloc
import weakref

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: datetime
    memory_mb: float
    cpu_percent: float
    operation_name: str
    duration_seconds: float
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportAnalysis:
    """Analysis of import performance"""
    module_name: str
    import_time_seconds: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float


class PerformanceProfiler:
    """Comprehensive performance profiler for the financial analysis application"""

    def __init__(self, enable_memory_tracking: bool = True):
        self.enable_memory_tracking = enable_memory_tracking
        self.metrics: List[PerformanceMetrics] = []
        self.import_analyses: List[ImportAnalysis] = []
        self._start_time = time.time()
        self._process = psutil.Process()

        if self.enable_memory_tracking:
            tracemalloc.start()

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self._process.memory_info().rss / 1024 / 1024

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return self._process.cpu_percent()

    @contextmanager
    def profile_operation(self, operation_name: str, **additional_data):
        """Context manager for profiling an operation"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        start_cpu = self.get_cpu_usage()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.get_memory_usage()

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                memory_mb=end_memory,
                cpu_percent=start_cpu,
                operation_name=operation_name,
                duration_seconds=end_time - start_time,
                additional_data={
                    'memory_delta_mb': end_memory - start_memory,
                    'start_memory_mb': start_memory,
                    **additional_data
                }
            )

            self.metrics.append(metrics)
            logger.info(f"Operation '{operation_name}' completed in {metrics.duration_seconds:.3f}s, "
                       f"Memory: {metrics.memory_mb:.1f}MB (+{metrics.additional_data['memory_delta_mb']:.1f}MB)")

    def profile_imports(self, modules_to_test: List[str]) -> Dict[str, ImportAnalysis]:
        """Profile import performance for specified modules"""
        results = {}

        for module_name in modules_to_test:
            if module_name in sys.modules:
                # Module already imported, skip
                continue

            memory_before = self.get_memory_usage()
            start_time = time.time()

            try:
                __import__(module_name)
                import_time = time.time() - start_time
                memory_after = self.get_memory_usage()

                analysis = ImportAnalysis(
                    module_name=module_name,
                    import_time_seconds=import_time,
                    memory_before_mb=memory_before,
                    memory_after_mb=memory_after,
                    memory_delta_mb=memory_after - memory_before
                )

                self.import_analyses.append(analysis)
                results[module_name] = analysis

                logger.info(f"Import '{module_name}': {import_time:.3f}s, "
                           f"Memory: +{analysis.memory_delta_mb:.1f}MB")

            except ImportError as e:
                logger.warning(f"Failed to import '{module_name}': {e}")

        return results

    def profile_function(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a specific function call"""
        pr = cProfile.Profile()

        with self.profile_operation(f"function_{func.__name__}"):
            pr.enable()
            try:
                result = func(*args, **kwargs)
            finally:
                pr.disable()

        # Generate profile statistics
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions

        # Store profile data
        self.metrics[-1].additional_data['profile_stats'] = s.getvalue()

        return result

    def analyze_memory_leaks(self) -> Dict[str, Any]:
        """Analyze potential memory leaks"""
        if not self.enable_memory_tracking:
            return {"error": "Memory tracking not enabled"}

        current, peak = tracemalloc.get_traced_memory()
        top_stats = tracemalloc.take_snapshot().statistics('lineno')

        return {
            "current_memory_mb": current / 1024 / 1024,
            "peak_memory_mb": peak / 1024 / 1024,
            "top_memory_consumers": [
                {
                    "filename": stat.traceback.format()[0],
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                }
                for stat in top_stats[:10]
            ]
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": psutil.virtual_memory().total / 1024**3,
            "memory_available_gb": psutil.virtual_memory().available / 1024**3,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent if sys.platform != 'win32' else psutil.disk_usage('C:').percent,
            "python_version": sys.version,
            "process_memory_mb": self.get_memory_usage(),
            "process_cpu_percent": self.get_cpu_usage()
        }

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive performance report"""
        report_lines = [
            "=" * 80,
            "FINANCIAL ANALYSIS APPLICATION - PERFORMANCE REPORT",
            "=" * 80,
            f"Generated: {datetime.now().isoformat()}",
            f"Total profiling time: {time.time() - self._start_time:.2f} seconds",
            "",
            "SYSTEM INFORMATION",
            "-" * 40
        ]

        system_info = self.get_system_info()
        for key, value in system_info.items():
            report_lines.append(f"{key}: {value}")

        report_lines.extend([
            "",
            "IMPORT ANALYSIS",
            "-" * 40
        ])

        if self.import_analyses:
            for analysis in sorted(self.import_analyses, key=lambda x: x.import_time_seconds, reverse=True):
                report_lines.append(
                    f"{analysis.module_name}: {analysis.import_time_seconds:.3f}s "
                    f"(+{analysis.memory_delta_mb:.1f}MB)"
                )
        else:
            report_lines.append("No import analysis performed")

        report_lines.extend([
            "",
            "OPERATION PERFORMANCE",
            "-" * 40
        ])

        if self.metrics:
            for metric in sorted(self.metrics, key=lambda x: x.duration_seconds, reverse=True):
                report_lines.append(
                    f"{metric.operation_name}: {metric.duration_seconds:.3f}s "
                    f"({metric.memory_mb:.1f}MB, CPU: {metric.cpu_percent:.1f}%)"
                )
        else:
            report_lines.append("No operations profiled")

        # Memory leak analysis
        if self.enable_memory_tracking:
            report_lines.extend([
                "",
                "MEMORY ANALYSIS",
                "-" * 40
            ])

            memory_analysis = self.analyze_memory_leaks()
            report_lines.append(f"Current memory usage: {memory_analysis.get('current_memory_mb', 0):.1f}MB")
            report_lines.append(f"Peak memory usage: {memory_analysis.get('peak_memory_mb', 0):.1f}MB")

            if 'top_memory_consumers' in memory_analysis:
                report_lines.append("\nTop memory consumers:")
                for consumer in memory_analysis['top_memory_consumers'][:5]:
                    report_lines.append(f"  {consumer['filename']}: {consumer['size_mb']:.2f}MB")

        report = "\n".join(report_lines)

        if output_path:
            output_path.write_text(report)
            logger.info(f"Performance report written to {output_path}")

        return report

    def cleanup(self):
        """Cleanup profiler resources"""
        if self.enable_memory_tracking:
            tracemalloc.stop()


# Convenience functions for common profiling tasks
def profile_streamlit_startup():
    """Profile Streamlit application startup"""
    profiler = PerformanceProfiler()

    # Profile common imports
    common_modules = [
        'streamlit',
        'pandas',
        'numpy',
        'matplotlib.pyplot',
        'plotly.graph_objects',
        'core.analysis.engines.financial_calculations',
        'core.analysis.dcf.dcf_valuation',
        'core.analysis.ddm.ddm_valuation',
        'core.analysis.pb.pb_valuation'
    ]

    with profiler.profile_operation("streamlit_imports"):
        profiler.profile_imports(common_modules)

    return profiler


def profile_data_loading(data_path: str):
    """Profile data loading operations"""
    profiler = PerformanceProfiler()

    with profiler.profile_operation("excel_data_loading", data_path=data_path):
        try:
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calculator = FinancialCalculator(data_path)
        except Exception as e:
            logger.error(f"Error loading data from {data_path}: {e}")

    return profiler


def run_comprehensive_profile():
    """Run comprehensive performance profiling"""
    profiler = PerformanceProfiler()

    logger.info("Starting comprehensive performance profiling...")

    # Profile system baseline
    with profiler.profile_operation("system_baseline"):
        time.sleep(0.1)  # Small delay to establish baseline

    # Profile imports
    startup_profiler = profile_streamlit_startup()
    profiler.metrics.extend(startup_profiler.metrics)
    profiler.import_analyses.extend(startup_profiler.import_analyses)

    # Generate and save report
    report_path = Path("performance_report.txt")
    report = profiler.generate_report(report_path)

    logger.info("Comprehensive profiling completed")
    print(report)

    return profiler


if __name__ == "__main__":
    # Run comprehensive profiling when executed directly
    run_comprehensive_profile()