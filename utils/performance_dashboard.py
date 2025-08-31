"""
Performance monitoring dashboard utilities for Streamlit applications.

This module provides UI components to display performance metrics, timing data,
and optimization insights for financial analysis operations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path

from .performance_monitor import get_performance_monitor, get_all_performance_stats


def render_performance_dashboard(show_in_sidebar: bool = False):
    """
    Render a comprehensive performance monitoring dashboard.
    
    Args:
        show_in_sidebar: Whether to render in sidebar or main area
    """
    container = st.sidebar if show_in_sidebar else st
    
    with container.expander("📊 Performance Monitor", expanded=False):
        st.subheader("⚡ Performance Metrics")
        
        # Get current performance data
        monitor = get_performance_monitor()
        stats = get_all_performance_stats()
        
        if not stats:
            st.info("No performance data available yet. Run some calculations to see metrics.")
            return
        
        # Performance overview
        col1, col2, col3 = st.columns(3)
        
        total_operations = sum(stat['count'] for stat in stats.values())
        total_time = sum(stat['total_time'] for stat in stats.values())
        avg_time_per_op = total_time / total_operations if total_operations > 0 else 0
        
        with col1:
            st.metric(
                label="Total Operations",
                value=f"{total_operations:,}",
                help="Total number of timed operations"
            )
        
        with col2:
            st.metric(
                label="Total Time",
                value=f"{total_time:.2f}s",
                help="Total execution time for all operations"
            )
        
        with col3:
            st.metric(
                label="Avg Time/Op",
                value=f"{avg_time_per_op:.3f}s",
                help="Average time per operation"
            )
        
        st.markdown("---")
        
        # Operations breakdown
        st.subheader("📈 Operations Breakdown")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["⏱️ Timing", "📊 Statistics", "🔍 Details"])
        
        with tab1:
            _render_timing_charts(stats)
        
        with tab2:
            _render_statistics_table(stats)
        
        with tab3:
            _render_detailed_metrics(monitor)


def _render_timing_charts(stats: Dict[str, Dict[str, float]]):
    """Render timing visualization charts."""
    if not stats:
        st.info("No timing data available")
        return
    
    # Prepare data for charts
    operations = list(stats.keys())
    avg_times = [stat['avg_time'] * 1000 for stat in stats.values()]  # Convert to ms
    total_times = [stat['total_time'] for stat in stats.values()]
    counts = [stat['count'] for stat in stats.values()]
    
    # Average execution time chart
    fig1 = px.bar(
        x=operations,
        y=avg_times,
        title="Average Execution Time by Operation",
        labels={'x': 'Operation', 'y': 'Average Time (ms)'},
        color=avg_times,
        color_continuous_scale='Viridis'
    )
    fig1.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Total time vs operation count
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=counts,
        y=total_times,
        mode='markers+text',
        text=operations,
        textposition='top center',
        marker=dict(
            size=avg_times,
            color=avg_times,
            colorscale='Viridis',
            colorbar=dict(title="Avg Time (ms)"),
            sizemode='diameter',
            sizeref=2.*max(avg_times)/(40.**2),
            sizemin=4
        ),
        hovertemplate="<b>%{text}</b><br>" +
                      "Count: %{x}<br>" +
                      "Total Time: %{y:.3f}s<br>" +
                      "Avg Time: %{marker.color:.1f}ms<extra></extra>"
    ))
    
    fig2.update_layout(
        title="Total Time vs Operation Count (Bubble size = Avg Time)",
        xaxis_title="Operation Count",
        yaxis_title="Total Time (seconds)",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)


def _render_statistics_table(stats: Dict[str, Dict[str, float]]):
    """Render detailed statistics table."""
    if not stats:
        st.info("No statistics available")
        return
    
    # Prepare table data
    table_data = []
    for operation, stat in stats.items():
        table_data.append({
            'Operation': operation,
            'Count': stat['count'],
            'Total Time (s)': f"{stat['total_time']:.3f}",
            'Avg Time (ms)': f"{stat['avg_time_ms']:.1f}",
            'Min Time (s)': f"{stat['min_time']:.3f}",
            'Max Time (s)': f"{stat['max_time']:.3f}",
        })
    
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    styled_df = df.style.format({
        'Count': '{:,}',
    }).background_gradient(
        subset=['Avg Time (ms)'], 
        cmap='RdYlGn_r'  # Red for slow, green for fast
    )
    
    st.dataframe(styled_df, use_container_width=True, height=300)
    
    # Performance insights
    st.subheader("💡 Performance Insights")
    
    # Find slowest operations
    sorted_by_avg_time = sorted(stats.items(), key=lambda x: x[1]['avg_time'], reverse=True)
    slowest_op = sorted_by_avg_time[0] if sorted_by_avg_time else None
    
    if slowest_op:
        op_name, op_stats = slowest_op
        st.warning(
            f"🐌 **Slowest Operation**: {op_name} "
            f"(avg: {op_stats['avg_time_ms']:.1f}ms, "
            f"max: {op_stats['max_time']:.3f}s)"
        )
    
    # Find most frequent operations
    sorted_by_count = sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)
    most_frequent = sorted_by_count[0] if sorted_by_count else None
    
    if most_frequent:
        op_name, op_stats = most_frequent
        st.info(
            f"🔄 **Most Frequent Operation**: {op_name} "
            f"({op_stats['count']} times, "
            f"total: {op_stats['total_time']:.2f}s)"
        )
    
    # Performance tips
    with st.expander("🚀 Performance Tips", expanded=False):
        st.markdown("""
        **Optimization Opportunities:**
        
        1. **Caching**: Implement caching for frequently called operations
        2. **Parallel Processing**: Use concurrent execution for I/O-bound operations  
        3. **Rate Limiting**: Balance API call frequency vs. response time
        4. **Data Preprocessing**: Cache intermediate calculations
        5. **Background Jobs**: Move long-running tasks to background processing
        
        **Monitoring Best Practices:**
        
        - Monitor operations that exceed 1000ms average time
        - Look for operations with high variance (max >> avg)
        - Track total time for frequently called operations
        - Set up alerts for performance degradation
        """)


def _render_detailed_metrics(monitor):
    """Render detailed performance metrics."""
    if not monitor.metrics:
        st.info("No detailed metrics available")
        return
    
    st.subheader("📋 Recent Operations")
    
    # Show recent operations in a table
    recent_metrics = sorted(monitor.metrics, key=lambda x: x.end_time, reverse=True)[:20]
    
    table_data = []
    for metric in recent_metrics:
        table_data.append({
            'Operation': metric.operation_name,
            'Duration (ms)': f"{metric.duration_ms:.1f}",
            'Timestamp': datetime.fromtimestamp(metric.end_time).strftime("%H:%M:%S"),
            'Metadata': str(metric.metadata) if metric.metadata else "None"
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    
    # Operation timeline
    if len(recent_metrics) > 1:
        st.subheader("⏰ Operation Timeline")
        
        timeline_data = []
        for metric in recent_metrics:
            timeline_data.append({
                'Operation': metric.operation_name,
                'Start': datetime.fromtimestamp(metric.start_time),
                'End': datetime.fromtimestamp(metric.end_time),
                'Duration': metric.duration_ms
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values('Start')
        
        fig = px.timeline(
            timeline_df,
            x_start='Start',
            x_end='End',
            y='Operation',
            color='Duration',
            color_continuous_scale='Viridis',
            title='Recent Operations Timeline'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_performance_metrics_card(operation_stats: Optional[Dict[str, float]] = None):
    """
    Render a compact performance metrics card for specific operations.
    
    Args:
        operation_stats: Statistics for a specific operation
    """
    if not operation_stats:
        return
    
    st.markdown("#### ⚡ Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Executions",
            value=f"{operation_stats.get('count', 0):,}",
            help="Number of times this operation was executed"
        )
    
    with col2:
        avg_time_ms = operation_stats.get('avg_time_ms', 0)
        st.metric(
            label="Avg Time",
            value=f"{avg_time_ms:.1f}ms",
            help="Average execution time"
        )
    
    with col3:
        min_time_ms = operation_stats.get('min_time', 0) * 1000
        st.metric(
            label="Best Time",
            value=f"{min_time_ms:.1f}ms",
            help="Fastest execution time"
        )
    
    with col4:
        max_time_ms = operation_stats.get('max_time', 0) * 1000
        st.metric(
            label="Worst Time",
            value=f"{max_time_ms:.1f}ms",
            help="Slowest execution time"
        )


def save_performance_report(file_path: Optional[Path] = None) -> Path:
    """
    Save a comprehensive performance report to file.
    
    Args:
        file_path: Optional path for the report file
        
    Returns:
        Path to the saved report file
    """
    if file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = Path(f"performance_report_{timestamp}.json")
    
    monitor = get_performance_monitor()
    stats = get_all_performance_stats()
    
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_operations': sum(stat['count'] for stat in stats.values()),
            'total_time': sum(stat['total_time'] for stat in stats.values()),
            'operation_count': len(stats)
        },
        'statistics': stats,
        'recent_metrics': [
            {
                'operation_name': metric.operation_name,
                'duration': metric.duration,
                'duration_ms': metric.duration_ms,
                'timestamp': metric.end_time,
                'metadata': metric.metadata
            }
            for metric in sorted(monitor.metrics, key=lambda x: x.end_time, reverse=True)[:50]
        ]
    }
    
    with open(file_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return file_path


def clear_performance_data():
    """Clear all collected performance data."""
    monitor = get_performance_monitor()
    monitor.clear_metrics()
    st.success("✅ Performance data cleared!")


# Streamlit UI integration functions
def add_performance_sidebar():
    """Add performance monitoring to the sidebar."""
    render_performance_dashboard(show_in_sidebar=True)


def add_performance_controls():
    """Add performance monitoring controls."""
    with st.expander("⚙️ Performance Controls", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Report", help="Export performance metrics to JSON file"):
                try:
                    report_path = save_performance_report()
                    st.success(f"📁 Performance report saved to: {report_path}")
                except Exception as e:
                    st.error(f"Failed to save report: {e}")
        
        with col2:
            if st.button("🗑️ Clear Data", help="Clear all performance metrics"):
                clear_performance_data()