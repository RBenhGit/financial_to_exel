"""
Performance monitoring utilities for financial analysis calculations.

This module provides decorators and utilities for tracking execution times,
monitoring progress, and optimizing performance of calculation-heavy operations.
"""

import time
import logging
import functools
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Container for performance measurement data."""
    
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return self.duration * 1000


class PerformanceMonitor:
    """
    Central performance monitoring system for tracking and analyzing
    execution times across the financial analysis toolkit.
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        self.metrics: List[PerformanceMetric] = []
        self.active_operations: Dict[str, float] = {}
        self.log_file = log_file or Path("performance_metrics.json")
        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor")
        
        # Statistics tracking
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
    
    def start_timer(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start timing an operation and return a timer ID."""
        timer_id = f"{operation_name}_{len(self.active_operations)}"
        self.active_operations[timer_id] = time.perf_counter()
        
        if metadata:
            self.logger.info(f"Started {operation_name} with metadata: {metadata}")
        else:
            self.logger.info(f"Started {operation_name}")
            
        return timer_id
    
    def stop_timer(self, timer_id: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """Stop timing and record the metric."""
        if timer_id not in self.active_operations:
            raise ValueError(f"Timer {timer_id} not found in active operations")
        
        start_time = self.active_operations.pop(timer_id)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Extract operation name from timer_id
        operation_name = "_".join(timer_id.split("_")[:-1])
        
        metric = PerformanceMetric(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        self.operation_stats[operation_name].append(duration)
        
        self.logger.info(f"Completed {operation_name} in {duration:.3f}s")
        
        return metric
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for a specific operation."""
        durations = self.operation_stats.get(operation_name, [])
        
        if not durations:
            return {}
        
        return {
            "count": len(durations),
            "total_time": sum(durations),
            "avg_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
            "avg_time_ms": (sum(durations) / len(durations)) * 1000,
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {op_name: self.get_operation_stats(op_name) 
                for op_name in self.operation_stats.keys()}
    
    def save_metrics(self) -> None:
        """Save performance metrics to JSON file."""
        try:
            data = {
                "metrics": [
                    {
                        "operation_name": metric.operation_name,
                        "duration": metric.duration,
                        "duration_ms": metric.duration_ms,
                        "timestamp": metric.end_time,
                        "metadata": metric.metadata
                    }
                    for metric in self.metrics
                ],
                "statistics": self.get_all_stats()
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved {len(self.metrics)} metrics to {self.log_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.operation_stats.clear()
        self.active_operations.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def performance_timer(operation_name: str, include_args: bool = False, save_metrics: bool = True):
    """
    Decorator to automatically time function execution and collect performance metrics.
    
    Args:
        operation_name: Name to identify this operation in metrics
        include_args: Whether to include function arguments in metadata
        save_metrics: Whether to save metrics to file after each operation
    
    Example:
        @performance_timer("pb_historical_analysis")
        def analyze_historical_pb(self, ticker: str, years: int):
            # Function implementation
            pass
    """
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Prepare metadata
            metadata = {"function": func.__name__}
            
            if include_args:
                # Include serializable arguments
                try:
                    metadata["args"] = [str(arg) for arg in args if not callable(arg)]
                    metadata["kwargs"] = {k: str(v) for k, v in kwargs.items() 
                                        if not callable(v)}
                except Exception:
                    # Fallback if serialization fails
                    metadata["args_count"] = len(args)
                    metadata["kwargs_count"] = len(kwargs)
            
            # Time the operation
            timer_id = _performance_monitor.start_timer(operation_name, metadata)
            
            try:
                result = func(*args, **kwargs)
                _performance_monitor.stop_timer(timer_id, {"success": True})
                
                if save_metrics:
                    _performance_monitor.save_metrics()
                
                return result
                
            except Exception as e:
                _performance_monitor.stop_timer(timer_id, {
                    "success": False, 
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                if save_metrics:
                    _performance_monitor.save_metrics()
                
                raise
        
        return wrapper
    return decorator


class ProgressTracker:
    """
    Progress tracking utility for long-running operations with callback support.
    """
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.callbacks: List[Callable[[int, int, str], None]] = []
        self.start_time = time.perf_counter()
    
    def add_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Add a progress callback function that receives (current, total, message)."""
        self.callbacks.append(callback)
    
    def update(self, step_increment: int = 1, message: str = "") -> None:
        """Update progress by specified steps."""
        self.current_step = min(self.current_step + step_increment, self.total_steps)
        
        # Calculate progress percentage
        progress_pct = (self.current_step / self.total_steps) * 100
        
        # Calculate estimated time remaining
        elapsed = time.perf_counter() - self.start_time
        if self.current_step > 0:
            estimated_total = elapsed * (self.total_steps / self.current_step)
            eta = estimated_total - elapsed
            eta_str = f" (ETA: {eta:.1f}s)" if eta > 1 else ""
        else:
            eta_str = ""
        
        # Create status message
        if not message:
            message = f"{self.operation_name}: {self.current_step}/{self.total_steps}{eta_str}"
        
        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(self.current_step, self.total_steps, message)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Progress callback failed: {e}")
    
    def complete(self, message: str = "") -> None:
        """Mark operation as complete."""
        self.current_step = self.total_steps
        
        elapsed = time.perf_counter() - self.start_time
        final_message = message or f"{self.operation_name} completed in {elapsed:.2f}s"
        
        for callback in self.callbacks:
            try:
                callback(self.total_steps, self.total_steps, final_message)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Progress callback failed: {e}")


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor


def reset_performance_monitor() -> None:
    """Reset the global performance monitor (useful for testing)."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()


# Convenience functions for quick timing
def time_operation(operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Start timing an operation. Returns timer ID for stopping."""
    return _performance_monitor.start_timer(operation_name, metadata)


def stop_timing(timer_id: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
    """Stop timing an operation."""
    return _performance_monitor.stop_timer(timer_id, metadata)


def get_operation_stats(operation_name: str) -> Dict[str, float]:
    """Get performance statistics for an operation."""
    return _performance_monitor.get_operation_stats(operation_name)


def get_all_performance_stats() -> Dict[str, Dict[str, float]]:
    """Get all performance statistics."""
    return _performance_monitor.get_all_stats()