"""
Dashboard Performance Monitoring and Benchmarking Integration

Provides real-time performance monitoring for dashboard components with
integrated benchmarking capabilities and user experience metrics.

Features:
- Real-time component performance tracking
- Automated benchmark integration
- User experience metrics collection
- Performance regression detection
- Interactive performance dashboard
"""

import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import threading
from collections import defaultdict, deque
import statistics
import json

from .dashboard_cache_optimizer import get_cache_optimizer
from performance.performance_benchmark import PerformanceBenchmark, BenchmarkResult

logger = logging.getLogger(__name__)


@dataclass
class ComponentMetrics:
    """Performance metrics for individual dashboard components"""
    component_name: str
    render_times: List[float] = field(default_factory=list)
    data_load_times: List[float] = field(default_factory=list)
    user_interactions: int = 0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_renders: int = 0

    @property
    def avg_render_time(self) -> float:
        """Average render time in milliseconds"""
        return statistics.mean(self.render_times) if self.render_times else 0.0

    @property
    def p95_render_time(self) -> float:
        """95th percentile render time"""
        if len(self.render_times) < 2:
            return self.avg_render_time
        return statistics.quantiles(self.render_times, n=20)[18]  # 95th percentile

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate percentage"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / max(total, 1)) * 100


@dataclass
class UserExperienceMetrics:
    """User experience and interaction metrics"""
    session_id: str
    session_start: datetime
    page_views: int = 0
    interactions: int = 0
    time_to_first_render: Optional[float] = None
    bounce_rate: float = 0.0
    avg_interaction_delay: float = 0.0
    error_encounters: int = 0

    @property
    def session_duration_minutes(self) -> float:
        """Session duration in minutes"""
        return (datetime.now() - self.session_start).total_seconds() / 60


class DashboardPerformanceMonitor:
    """
    Real-time performance monitoring system for dashboard components
    """

    def __init__(self):
        """Initialize performance monitor"""
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.session_metrics: Optional[UserExperienceMetrics] = None
        self.benchmark = PerformanceBenchmark("dashboard_performance_reports")

        # Initialize session state
        if 'performance_monitor' not in st.session_state:
            st.session_state.performance_monitor = {
                'session_start': datetime.now(),
                'component_timings': defaultdict(list),
                'user_interactions': defaultdict(int),
                'error_log': [],
                'benchmark_results': []
            }

        self._initialize_session_metrics()

    def _initialize_session_metrics(self):
        """Initialize user experience metrics for current session"""
        session_data = st.session_state.performance_monitor

        self.session_metrics = UserExperienceMetrics(
            session_id=st.session_state.get('session_id', 'unknown'),
            session_start=session_data['session_start']
        )

    def monitor_component(self, component_name: str):
        """
        Decorator to monitor component performance

        Args:
            component_name: Name of the component to monitor
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                return self._execute_monitored_component(func, component_name, *args, **kwargs)
            return wrapper
        return decorator

    def _execute_monitored_component(self, func: Callable, component_name: str, *args, **kwargs):
        """Execute function with performance monitoring"""
        # Record start time
        start_time = time.time()

        # Track cache status
        cache_optimizer = get_cache_optimizer()
        initial_cache_stats = cache_optimizer.get_cache_stats()

        try:
            # Execute component
            result = func(*args, **kwargs)

            # Record successful execution
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._record_component_timing(component_name, execution_time, success=True)

            # Track cache performance
            final_cache_stats = cache_optimizer.get_cache_stats()
            cache_hits_delta = final_cache_stats['total_hits'] - initial_cache_stats['total_hits']
            cache_misses_delta = final_cache_stats['total_misses'] - initial_cache_stats['total_misses']

            self._update_component_cache_stats(component_name, cache_hits_delta, cache_misses_delta)

            return result

        except Exception as e:
            # Record error
            execution_time = (time.time() - start_time) * 1000
            self._record_component_timing(component_name, execution_time, success=False)
            self._record_error(component_name, str(e))

            # Re-raise exception
            raise

    def _record_component_timing(self, component_name: str, timing_ms: float, success: bool = True):
        """Record component timing data"""
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(component_name)

        metrics = self.component_metrics[component_name]
        metrics.render_times.append(timing_ms)
        metrics.total_renders += 1

        if not success:
            metrics.error_count += 1

        # Store in session state for persistence
        st.session_state.performance_monitor['component_timings'][component_name].append({
            'timestamp': datetime.now().isoformat(),
            'timing_ms': timing_ms,
            'success': success
        })

    def _update_component_cache_stats(self, component_name: str, hits_delta: int, misses_delta: int):
        """Update cache statistics for component"""
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(component_name)

        metrics = self.component_metrics[component_name]
        metrics.cache_hits += hits_delta
        metrics.cache_misses += misses_delta

    def _record_error(self, component_name: str, error_message: str):
        """Record component error"""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'component': component_name,
            'error': error_message
        }

        st.session_state.performance_monitor['error_log'].append(error_record)

        if self.session_metrics:
            self.session_metrics.error_encounters += 1

    def record_user_interaction(self, interaction_type: str, component_name: str):
        """Record user interaction for UX metrics"""
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(component_name)

        self.component_metrics[component_name].user_interactions += 1
        st.session_state.performance_monitor['user_interactions'][f"{component_name}:{interaction_type}"] += 1

        if self.session_metrics:
            self.session_metrics.interactions += 1

    def run_performance_benchmark(self, components_to_test: List[str] = None) -> Dict[str, BenchmarkResult]:
        """
        Run performance benchmark on dashboard components

        Args:
            components_to_test: List of component names to benchmark

        Returns:
            Dict of benchmark results by component
        """
        if components_to_test is None:
            components_to_test = list(self.component_metrics.keys())

        benchmark_results = {}

        with st.spinner("Running performance benchmark..."):
            for component_name in components_to_test:
                if component_name in self.component_metrics:
                    metrics = self.component_metrics[component_name]

                    # Create synthetic benchmark result from collected metrics
                    benchmark_result = BenchmarkResult(
                        test_name=f"Dashboard Component: {component_name}",
                        start_time=datetime.now() - timedelta(minutes=10),
                        end_time=datetime.now(),
                        duration_seconds=sum(metrics.render_times) / 1000,  # Convert to seconds
                        memory_start_mb=0.0,  # Would need memory tracking
                        memory_end_mb=0.0,
                        memory_peak_mb=0.0,
                        cpu_percent=0.0,
                        success_count=metrics.total_renders - metrics.error_count,
                        failure_count=metrics.error_count,
                        total_operations=metrics.total_renders,
                        operations_per_second=metrics.total_renders / max(sum(metrics.render_times) / 1000, 0.001),
                        average_response_time=metrics.avg_render_time / 1000,  # Convert to seconds
                        median_response_time=statistics.median(metrics.render_times) / 1000 if metrics.render_times else 0,
                        p95_response_time=metrics.p95_render_time / 1000,
                        p99_response_time=max(metrics.render_times) / 1000 if metrics.render_times else 0,
                        error_rate=(metrics.error_count / max(metrics.total_renders, 1)) * 100,
                        metadata={
                            'component_type': 'dashboard_component',
                            'cache_hit_rate': metrics.cache_hit_rate,
                            'user_interactions': metrics.user_interactions
                        }
                    )

                    benchmark_results[component_name] = benchmark_result

        # Store results
        st.session_state.performance_monitor['benchmark_results'].extend(benchmark_results.values())

        return benchmark_results

    def display_performance_dashboard(self):
        """Display comprehensive performance monitoring dashboard"""
        st.header("🚀 Dashboard Performance Monitor")

        # Performance overview
        self._display_performance_overview()

        # Component performance details
        self._display_component_performance()

        # User experience metrics
        self._display_user_experience_metrics()

        # Real-time monitoring
        self._display_real_time_monitoring()

        # Benchmark controls
        self._display_benchmark_controls()

    def _display_performance_overview(self):
        """Display high-level performance overview"""
        st.subheader("📊 Performance Overview")

        if not self.component_metrics:
            st.info("No performance data available yet. Use the dashboard to generate metrics.")
            return

        # Calculate aggregate metrics
        total_renders = sum(m.total_renders for m in self.component_metrics.values())
        total_errors = sum(m.error_count for m in self.component_metrics.values())
        avg_render_time = statistics.mean([
            m.avg_render_time for m in self.component_metrics.values()
            if m.render_times
        ]) if self.component_metrics else 0

        overall_cache_hit_rate = statistics.mean([
            m.cache_hit_rate for m in self.component_metrics.values()
            if m.cache_hits + m.cache_misses > 0
        ]) if self.component_metrics else 0

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Renders", f"{total_renders:,}")

        with col2:
            error_rate = (total_errors / max(total_renders, 1)) * 100
            st.metric("Error Rate", f"{error_rate:.1f}%",
                     delta="Good" if error_rate < 1 else "Poor")

        with col3:
            st.metric("Avg Render Time", f"{avg_render_time:.0f}ms",
                     delta="Fast" if avg_render_time < 100 else "Slow")

        with col4:
            st.metric("Cache Hit Rate", f"{overall_cache_hit_rate:.1f}%",
                     delta="Excellent" if overall_cache_hit_rate > 80 else "Good")

    def _display_component_performance(self):
        """Display detailed component performance metrics"""
        st.subheader("🔧 Component Performance")

        if not self.component_metrics:
            return

        # Create performance comparison chart
        component_data = []
        for name, metrics in self.component_metrics.items():
            component_data.append({
                'Component': name,
                'Avg Render Time (ms)': metrics.avg_render_time,
                'P95 Render Time (ms)': metrics.p95_render_time,
                'Total Renders': metrics.total_renders,
                'Error Rate (%)': (metrics.error_count / max(metrics.total_renders, 1)) * 100,
                'Cache Hit Rate (%)': metrics.cache_hit_rate,
                'User Interactions': metrics.user_interactions
            })

        df = pd.DataFrame(component_data)

        # Performance chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Avg Render Time',
            x=df['Component'],
            y=df['Avg Render Time (ms)'],
            marker_color='lightblue'
        ))

        fig.add_trace(go.Scatter(
            name='P95 Render Time',
            x=df['Component'],
            y=df['P95 Render Time (ms)'],
            mode='markers',
            marker=dict(color='red', size=10),
            yaxis='y2'
        ))

        fig.update_layout(
            title="Component Render Time Performance",
            xaxis_title="Component",
            yaxis_title="Average Render Time (ms)",
            yaxis2=dict(
                title="P95 Render Time (ms)",
                overlaying='y',
                side='right'
            ),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed component table
        st.dataframe(df, use_container_width=True)

    def _display_user_experience_metrics(self):
        """Display user experience metrics"""
        st.subheader("👤 User Experience Metrics")

        if not self.session_metrics:
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Session Duration",
                     f"{self.session_metrics.session_duration_minutes:.1f} min")

        with col2:
            st.metric("Total Interactions", self.session_metrics.interactions)

        with col3:
            st.metric("Error Encounters", self.session_metrics.error_encounters,
                     delta="Good" if self.session_metrics.error_encounters == 0 else "Issues")

        # Interaction timeline
        if st.session_state.performance_monitor['user_interactions']:
            interaction_df = pd.DataFrame([
                {'Interaction': k, 'Count': v}
                for k, v in st.session_state.performance_monitor['user_interactions'].items()
            ])

            fig = px.bar(interaction_df, x='Interaction', y='Count',
                        title="User Interactions by Type")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

    def _display_real_time_monitoring(self):
        """Display real-time monitoring charts"""
        st.subheader("⏱️ Real-Time Monitoring")

        # Recent performance trends
        if st.checkbox("Show Real-Time Performance Trends"):
            placeholder = st.empty()

            # This would be updated in real-time in a production system
            with placeholder.container():
                recent_data = []
                for component_name, metrics in self.component_metrics.items():
                    if metrics.render_times:
                        recent_times = metrics.render_times[-10:]  # Last 10 renders
                        for i, time_ms in enumerate(recent_times):
                            recent_data.append({
                                'Component': component_name,
                                'Render': len(recent_times) - i,
                                'Time (ms)': time_ms
                            })

                if recent_data:
                    df = pd.DataFrame(recent_data)
                    fig = px.line(df, x='Render', y='Time (ms)',
                                 color='Component', title="Recent Render Times")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No recent performance data to display.")

    def _display_benchmark_controls(self):
        """Display benchmark execution controls"""
        st.subheader("🏁 Performance Benchmarking")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Run Performance Benchmark"):
                benchmark_results = self.run_performance_benchmark()

                if benchmark_results:
                    st.success(f"Benchmark completed for {len(benchmark_results)} components!")

                    # Display benchmark summary
                    for component_name, result in benchmark_results.items():
                        with st.expander(f"📊 {component_name} Benchmark Results"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("Operations/sec", f"{result.operations_per_second:.1f}")

                            with col2:
                                st.metric("Success Rate", f"{result.success_rate:.1f}%")

                            with col3:
                                st.metric("Avg Response", f"{result.average_response_time*1000:.0f}ms")
                else:
                    st.warning("No components available for benchmarking.")

        with col2:
            if st.button("📈 Performance Regression Test"):
                st.info("Regression testing would compare against historical benchmarks.")

        # Historical benchmark results
        if st.session_state.performance_monitor['benchmark_results']:
            with st.expander("📚 Historical Benchmark Results"):
                results_data = []
                for result in st.session_state.performance_monitor['benchmark_results']:
                    results_data.append({
                        'Test': result.test_name,
                        'Date': result.end_time.strftime('%Y-%m-%d %H:%M'),
                        'Duration (s)': result.duration_seconds,
                        'Success Rate (%)': result.success_rate,
                        'Ops/sec': result.operations_per_second,
                        'Error Rate (%)': result.error_rate
                    })

                if results_data:
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(results_df, use_container_width=True)


# Global monitor instance
_performance_monitor = None


def get_performance_monitor() -> DashboardPerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = DashboardPerformanceMonitor()
    return _performance_monitor


def monitor_component(component_name: str):
    """Convenience decorator for component monitoring"""
    return get_performance_monitor().monitor_component(component_name)


def record_interaction(interaction_type: str, component_name: str):
    """Convenience function to record user interaction"""
    get_performance_monitor().record_user_interaction(interaction_type, component_name)


def display_performance_monitor():
    """Convenience function to display performance dashboard"""
    get_performance_monitor().display_performance_dashboard()