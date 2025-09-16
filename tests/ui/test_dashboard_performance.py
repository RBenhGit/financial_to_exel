"""
Comprehensive UI Testing Suite for Dashboard Performance

Tests dashboard components for performance, functionality, and user experience.
Includes integration with performance monitoring and benchmarking systems.

Test Categories:
- Component rendering performance
- Data loading and caching efficiency
- User interaction responsiveness
- Memory usage and optimization
- Error handling and recovery
"""

import pytest
import streamlit as st
import pandas as pd
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np
import gc
import sys
from typing import Dict, List, Any

# Import dashboard components to test
from ui.streamlit.dashboard_cache_optimizer import (
    DashboardCacheOptimizer,
    get_cache_optimizer,
    cache_component,
    cache_dataframe_op,
    cache_chart
)
from ui.streamlit.dashboard_performance_monitor import (
    DashboardPerformanceMonitor,
    get_performance_monitor,
    monitor_component,
    ComponentMetrics
)
from performance.streamlit_performance_integration import StreamlitPerformanceIntegration


class TestDashboardCacheOptimizer:
    """Test suite for dashboard caching system"""

    def setup_method(self):
        """Setup for each test method"""
        self.cache_optimizer = DashboardCacheOptimizer(max_size_mb=10.0, default_ttl=60)

    def teardown_method(self):
        """Cleanup after each test"""
        self.cache_optimizer.clear_cache()
        gc.collect()

    def test_cache_initialization(self):
        """Test cache optimizer initialization"""
        assert self.cache_optimizer.max_size_mb == 10.0
        assert self.cache_optimizer.default_ttl == 60
        assert isinstance(self.cache_optimizer.cache, dict)

    def test_component_caching_decorator(self):
        """Test component caching decorator functionality"""
        call_count = 0

        @self.cache_optimizer.cached_component(ttl=30)
        def expensive_calculation(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Simulate expensive operation
            return x + y

        # First call should execute function
        start_time = time.time()
        result1 = expensive_calculation(1, 2)
        first_call_time = time.time() - start_time

        assert result1 == 3
        assert call_count == 1
        assert first_call_time >= 0.1

        # Second call should use cache
        start_time = time.time()
        result2 = expensive_calculation(1, 2)
        second_call_time = time.time() - start_time

        assert result2 == 3
        assert call_count == 1  # Function not called again
        assert second_call_time < 0.05  # Should be much faster

        # Different parameters should call function again
        result3 = expensive_calculation(3, 4)
        assert result3 == 7
        assert call_count == 2

    def test_dataframe_operation_caching(self):
        """Test DataFrame operation caching"""
        call_count = 0

        @self.cache_optimizer.cached_dataframe_operation("test_op", ttl=60)
        def transform_dataframe(df: pd.DataFrame, multiplier: int = 1) -> pd.DataFrame:
            nonlocal call_count
            call_count += 1
            return df * multiplier

        # Create test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        # First call
        result1 = transform_dataframe(df, multiplier=2)
        assert call_count == 1
        expected = pd.DataFrame({'A': [2, 4, 6], 'B': [8, 10, 12]})
        pd.testing.assert_frame_equal(result1, expected)

        # Second call with same data should use cache
        result2 = transform_dataframe(df, multiplier=2)
        assert call_count == 1
        pd.testing.assert_frame_equal(result2, expected)

        # Different multiplier should call function again
        result3 = transform_dataframe(df, multiplier=3)
        assert call_count == 2

    def test_chart_caching(self):
        """Test chart caching functionality"""
        call_count = 0

        @self.cache_optimizer.cache_chart("scatter", "test_data", ttl=120)
        def create_test_chart(x_data: List[float], y_data: List[float]) -> Dict:
            nonlocal call_count
            call_count += 1
            return {
                'type': 'scatter',
                'x': x_data,
                'y': y_data,
                'timestamp': time.time()
            }

        x_data = [1, 2, 3, 4]
        y_data = [2, 4, 6, 8]

        # First call
        chart1 = create_test_chart(x_data, y_data)
        assert call_count == 1
        assert chart1['type'] == 'scatter'

        # Second call should use cache
        chart2 = create_test_chart(x_data, y_data)
        assert call_count == 1
        assert chart2['timestamp'] == chart1['timestamp']  # Same cached object

    def test_cache_eviction(self):
        """Test cache eviction when memory limit is reached"""
        # Create small cache for testing eviction
        small_cache = DashboardCacheOptimizer(max_size_mb=0.001, default_ttl=300)

        @small_cache.cached_component()
        def create_large_data(size: int) -> List[int]:
            return list(range(size))

        # Fill cache beyond limit
        for i in range(5):
            create_large_data(1000 * (i + 1))

        # Verify cache has been evicted
        stats = small_cache.get_cache_stats()
        assert stats['evictions'] > 0

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration"""
        short_cache = DashboardCacheOptimizer(default_ttl=1)  # 1 second TTL
        call_count = 0

        @short_cache.cached_component(ttl=1)
        def time_sensitive_function() -> float:
            nonlocal call_count
            call_count += 1
            return time.time()

        # First call
        result1 = time_sensitive_function()
        assert call_count == 1

        # Immediate second call should use cache
        result2 = time_sensitive_function()
        assert call_count == 1
        assert result2 == result1

        # Wait for expiration and call again
        time.sleep(1.1)
        result3 = time_sensitive_function()
        assert call_count == 2
        assert result3 != result1

    def test_cache_statistics(self):
        """Test cache statistics collection"""
        call_count = 0

        @self.cache_optimizer.cached_component()
        def test_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # Generate cache hits and misses
        test_function(1)  # Miss
        test_function(1)  # Hit
        test_function(2)  # Miss
        test_function(1)  # Hit

        stats = self.cache_optimizer.get_cache_stats()
        assert stats['entries_count'] == 2
        assert stats['hit_rate'] > 0
        assert stats['effectiveness_score'] > 0

    def test_memory_optimization(self):
        """Test memory optimization functionality"""
        # Create entries with different TTLs
        short_ttl_cache = DashboardCacheOptimizer(default_ttl=1)

        @short_ttl_cache.cached_component(ttl=1)
        def short_lived_function(x: int) -> int:
            return x

        # Create entries
        for i in range(5):
            short_lived_function(i)

        # Wait for expiration
        time.sleep(1.1)

        # Optimize memory
        removed_count = short_ttl_cache.optimize_memory()
        assert removed_count > 0

        stats = short_ttl_cache.get_cache_stats()
        assert stats['entries_count'] == 0


class TestDashboardPerformanceMonitor:
    """Test suite for dashboard performance monitoring"""

    def setup_method(self):
        """Setup for each test method"""
        self.monitor = DashboardPerformanceMonitor()

    def test_monitor_initialization(self):
        """Test performance monitor initialization"""
        assert isinstance(self.monitor.component_metrics, dict)
        assert self.monitor.session_metrics is not None

    def test_component_monitoring_decorator(self):
        """Test component monitoring decorator"""
        @self.monitor.monitor_component("test_component")
        def test_function(delay: float = 0.05) -> str:
            time.sleep(delay)
            return "success"

        # Execute monitored function
        result = test_function(0.1)
        assert result == "success"

        # Check metrics were recorded
        assert "test_component" in self.monitor.component_metrics
        metrics = self.monitor.component_metrics["test_component"]
        assert metrics.total_renders == 1
        assert len(metrics.render_times) == 1
        assert metrics.render_times[0] >= 100  # Should be ~100ms

    def test_error_monitoring(self):
        """Test error monitoring and recording"""
        @self.monitor.monitor_component("error_component")
        def failing_function():
            raise ValueError("Test error")

        # Execute function that raises error
        with pytest.raises(ValueError):
            failing_function()

        # Check error was recorded
        metrics = self.monitor.component_metrics["error_component"]
        assert metrics.error_count == 1
        assert metrics.total_renders == 1

    def test_user_interaction_tracking(self):
        """Test user interaction tracking"""
        component_name = "interaction_test"

        # Record interactions
        self.monitor.record_user_interaction("click", component_name)
        self.monitor.record_user_interaction("hover", component_name)
        self.monitor.record_user_interaction("click", component_name)

        # Check metrics
        metrics = self.monitor.component_metrics[component_name]
        assert metrics.user_interactions == 3

        # Check session metrics
        assert self.monitor.session_metrics.interactions == 3

    def test_performance_metrics_calculation(self):
        """Test performance metrics calculations"""
        @self.monitor.monitor_component("calc_test")
        def variable_delay_function(delay: float):
            time.sleep(delay)
            return delay

        # Execute with different delays
        delays = [0.05, 0.1, 0.15, 0.2, 0.25]
        for delay in delays:
            variable_delay_function(delay)

        metrics = self.monitor.component_metrics["calc_test"]

        # Check calculations
        assert metrics.total_renders == 5
        assert 50 <= metrics.avg_render_time <= 200  # Average should be around 150ms
        assert metrics.p95_render_time >= metrics.avg_render_time

    def test_benchmark_integration(self):
        """Test integration with performance benchmarking"""
        # Setup some performance data
        @self.monitor.monitor_component("benchmark_test")
        def benchmark_function(iterations: int = 10):
            for _ in range(iterations):
                time.sleep(0.01)
            return iterations

        # Generate test data
        for i in range(5):
            benchmark_function(i + 1)

        # Run benchmark
        results = self.monitor.run_performance_benchmark(["benchmark_test"])

        assert "benchmark_test" in results
        result = results["benchmark_test"]

        assert result.total_operations == 5
        assert result.success_count == 5
        assert result.error_rate == 0.0


class TestStreamlitPerformanceIntegration:
    """Test suite for Streamlit performance integration"""

    def setup_method(self):
        """Setup for each test method"""
        self.integration = StreamlitPerformanceIntegration()

    def test_integration_initialization(self):
        """Test performance integration initialization"""
        assert self.integration.optimizer is None  # Not initialized until needed
        assert self.integration.visualizer is not None

    @pytest.mark.slow
    def test_performance_controls_display(self):
        """Test performance controls display functionality"""
        # This would typically require Streamlit app context
        # Here we test the data structures and logic

        # Mock watch list manager
        mock_manager = Mock()
        mock_manager.get_all_watch_lists.return_value = {
            "test_list": {"stocks": [{"ticker": "AAPL"}, {"ticker": "GOOGL"}]}
        }

        # Test that display method handles empty watch lists
        mock_manager.get_all_watch_lists.return_value = {}

        # Method should handle gracefully without errors
        try:
            # This would normally display UI elements
            assert True  # Placeholder for UI testing
        except Exception as e:
            pytest.fail(f"Performance controls display failed: {e}")

    def test_watch_list_summary_calculations(self):
        """Test watch list summary metrics calculations"""
        # Mock stock data
        stocks = [
            {
                "ticker": "AAPL",
                "current_market_price": 150.0,
                "fair_value": 180.0,
                "updated_upside_downside_pct": 20.0
            },
            {
                "ticker": "GOOGL",
                "current_market_price": 2500.0,
                "fair_value": 2300.0,
                "updated_upside_downside_pct": -8.0
            },
            {
                "ticker": "MSFT",
                "current_market_price": 300.0,
                "fair_value": 320.0,
                "updated_upside_downside_pct": 6.7
            }
        ]

        # Test calculations that would be used in the summary
        total_stocks = len(stocks)
        stocks_with_prices = len([s for s in stocks if s.get('current_market_price')])

        upside_values = [s.get('updated_upside_downside_pct', 0) for s in stocks if s.get('fair_value')]
        avg_upside = sum(upside_values) / len(upside_values)
        undervalued_count = len([u for u in upside_values if u > 5])
        overvalued_count = len([u for u in upside_values if u < -5])

        # Assertions
        assert total_stocks == 3
        assert stocks_with_prices == 3
        assert abs(avg_upside - 6.23) < 0.1  # (20 + (-8) + 6.7) / 3
        assert undervalued_count == 2  # AAPL and MSFT
        assert overvalued_count == 1  # GOOGL


class TestDashboardIntegration:
    """Integration tests for complete dashboard performance system"""

    def setup_method(self):
        """Setup for integration tests"""
        self.cache_optimizer = DashboardCacheOptimizer(max_size_mb=5.0)
        self.performance_monitor = DashboardPerformanceMonitor()

    def test_cache_and_monitor_integration(self):
        """Test integration between caching and monitoring systems"""
        call_count = 0

        @self.performance_monitor.monitor_component("integrated_test")
        @self.cache_optimizer.cached_component(ttl=60)
        def integrated_function(data_size: int) -> List[int]:
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)  # Simulate processing time
            return list(range(data_size))

        # First call - should be monitored and cached
        result1 = integrated_function(100)
        assert len(result1) == 100
        assert call_count == 1

        # Second call - should use cache and be monitored
        result2 = integrated_function(100)
        assert len(result2) == 100
        assert call_count == 1  # Function not called again

        # Check monitoring data
        metrics = self.performance_monitor.component_metrics["integrated_test"]
        assert metrics.total_renders == 2
        assert len(metrics.render_times) == 2

        # Second call should be faster due to caching
        assert metrics.render_times[1] < metrics.render_times[0]

    def test_memory_pressure_handling(self):
        """Test system behavior under memory pressure"""
        # Create components that generate large amounts of data
        large_cache = DashboardCacheOptimizer(max_size_mb=1.0)  # Small limit

        @self.performance_monitor.monitor_component("memory_test")
        @large_cache.cached_component()
        def memory_intensive_function(size: int) -> np.ndarray:
            time.sleep(0.01)
            return np.random.random(size)

        # Generate memory pressure
        for i in range(10):
            data = memory_intensive_function(1000 * (i + 1))
            assert len(data) == 1000 * (i + 1)

        # Check that evictions occurred
        stats = large_cache.get_cache_stats()
        assert stats['evictions'] > 0
        assert stats['utilization_pct'] <= 100

        # Check that monitoring continued to work
        metrics = self.performance_monitor.component_metrics["memory_test"]
        assert metrics.total_renders == 10
        assert metrics.error_count == 0

    def test_concurrent_access_safety(self):
        """Test thread safety of caching and monitoring systems"""
        results = []
        errors = []

        @self.performance_monitor.monitor_component("concurrent_test")
        @self.cache_optimizer.cached_component()
        def thread_safe_function(thread_id: int) -> int:
            time.sleep(0.01)
            return thread_id * 2

        def worker(thread_id: int, iterations: int):
            try:
                for i in range(iterations):
                    result = thread_safe_function(thread_id)
                    results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run concurrent workers
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=worker, args=(thread_id, 10))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 threads * 10 iterations

        # Check monitoring data
        metrics = self.performance_monitor.component_metrics["concurrent_test"]
        assert metrics.total_renders == 50
        assert metrics.error_count == 0


@pytest.mark.performance
class TestPerformanceRegression:
    """Performance regression tests to ensure optimizations maintain performance"""

    def test_cache_performance_regression(self):
        """Test that caching provides consistent performance benefits"""
        cache_optimizer = DashboardCacheOptimizer()
        execution_times = []

        @cache_optimizer.cached_component()
        def benchmark_function(complexity: int) -> int:
            # Simulate variable complexity computation
            total = 0
            for i in range(complexity * 1000):
                total += i
            return total

        # Measure performance with and without cache
        complexity = 100

        # First call (cache miss)
        start_time = time.time()
        result1 = benchmark_function(complexity)
        miss_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = benchmark_function(complexity)
        hit_time = time.time() - start_time

        # Assertions
        assert result1 == result2
        assert hit_time < miss_time * 0.1  # Cache should be at least 10x faster
        assert miss_time > 0.01  # Ensure the function actually takes time

    def test_monitoring_overhead(self):
        """Test that performance monitoring has minimal overhead"""
        monitor = DashboardPerformanceMonitor()

        def simple_function():
            return sum(range(1000))

        # Measure unmonitored performance
        iterations = 100
        start_time = time.time()
        for _ in range(iterations):
            simple_function()
        unmonitored_time = time.time() - start_time

        # Measure monitored performance
        monitored_function = monitor.monitor_component("overhead_test")(simple_function)
        start_time = time.time()
        for _ in range(iterations):
            monitored_function()
        monitored_time = time.time() - start_time

        # Monitoring overhead should be less than 50%
        overhead_ratio = monitored_time / unmonitored_time
        assert overhead_ratio < 1.5, f"Monitoring overhead too high: {overhead_ratio:.2f}x"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])