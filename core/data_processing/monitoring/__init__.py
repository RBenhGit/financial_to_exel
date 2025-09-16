"""
Data Source Health Monitoring Module
==================================

This module provides comprehensive monitoring and alerting capabilities for all data sources
in the financial analysis system, including Excel files, API endpoints, and cached data.

Main Components:
    - DataSourceHealthMonitor: Central monitoring coordinator
    - HealthMetrics: Metrics collection and analysis
    - AlertingSystem: Performance degradation notifications
    - HealthReporter: Dashboard and reporting utilities
"""

from .health_monitor import DataSourceHealthMonitor, HealthMetrics
from .alerting_system import AlertingSystem, AlertSeverity, Alert
from .health_reporter import HealthReporter, HealthDashboard

__all__ = [
    'DataSourceHealthMonitor',
    'HealthMetrics',
    'AlertingSystem',
    'AlertSeverity',
    'Alert',
    'HealthReporter',
    'HealthDashboard'
]