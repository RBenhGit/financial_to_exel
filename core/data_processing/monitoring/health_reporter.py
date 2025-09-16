"""
Health Reporting and Dashboard Components
=======================================

Provides reporting capabilities and dashboard components for data source health monitoring,
including real-time status displays, historical trend analysis, and export functionality.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

from .health_monitor import DataSourceHealthMonitor, HealthMetrics, HealthStatus
from .alerting_system import AlertingSystem, Alert, AlertSeverity


class HealthReporter:
    """
    Health reporting system for generating reports and analytics.

    Provides various report formats including JSON, CSV, HTML, and PDF exports
    of health monitoring data and trends.
    """

    def __init__(self, health_monitor: DataSourceHealthMonitor, alerting_system: AlertingSystem):
        """
        Initialize the health reporter.

        Args:
            health_monitor: Health monitoring system instance
            alerting_system: Alerting system instance
        """
        self.health_monitor = health_monitor
        self.alerting_system = alerting_system
        self.logger = logging.getLogger(f"{__name__}.HealthReporter")

    def generate_health_report(self, format: str = 'json', hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive health report.

        Args:
            format: Report format ('json', 'csv', 'html')
            hours: Number of hours of historical data to include

        Returns:
            Health report data
        """
        current_metrics = self.health_monitor.get_all_health_metrics()
        summary = self.health_monitor.get_health_summary()
        active_alerts = self.alerting_system.get_active_alerts()
        alert_summary = self.alerting_system.get_alert_summary()

        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_period_hours': hours,
                'format': format
            },
            'system_health_summary': summary,
            'data_sources': {
                name: self._format_metrics_for_report(metrics)
                for name, metrics in current_metrics.items()
            },
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'alert_summary': alert_summary,
            'historical_trends': self._get_historical_trends(hours),
            'performance_insights': self._generate_performance_insights(current_metrics),
            'recommendations': self._generate_recommendations(current_metrics, active_alerts)
        }

        if format == 'csv':
            return self._convert_to_csv_data(report)
        elif format == 'html':
            return self._convert_to_html_report(report)
        else:
            return report

    def _format_metrics_for_report(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """Format metrics for inclusion in report"""
        return {
            'source_type': metrics.source_type.value,
            'health_status': metrics.health_status.value,
            'overall_score': round(metrics.overall_score, 2),
            'response_time_ms': round(metrics.response_time_ms, 2),
            'success_rate': round(metrics.success_rate, 3),
            'data_quality_score': round(metrics.data_quality_score, 3),
            'availability_percentage': round(metrics.availability_percentage, 2),
            'total_requests': metrics.total_requests,
            'failed_requests': metrics.failed_requests,
            'consecutive_failures': metrics.consecutive_failures,
            'last_error': metrics.last_error,
            'last_updated': metrics.timestamp.isoformat()
        }

    def _get_historical_trends(self, hours: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get historical trend data for all sources"""
        trends = {}
        for source_name in self.health_monitor.monitored_sources.keys():
            history = self.health_monitor.get_metrics_history(source_name, hours)
            trends[source_name] = [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'response_time_ms': metric.response_time_ms,
                    'success_rate': metric.success_rate,
                    'overall_score': metric.overall_score,
                    'health_status': metric.health_status.value
                }
                for metric in history
            ]
        return trends

    def _generate_performance_insights(self, metrics: Dict[str, HealthMetrics]) -> Dict[str, Any]:
        """Generate performance insights from current metrics"""
        if not metrics:
            return {}

        response_times = [m.response_time_ms for m in metrics.values()]
        success_rates = [m.success_rate for m in metrics.values()]
        quality_scores = [m.data_quality_score for m in metrics.values()]

        best_performing = max(metrics.items(), key=lambda x: x[1].overall_score)
        worst_performing = min(metrics.items(), key=lambda x: x[1].overall_score)

        return {
            'avg_response_time_ms': round(sum(response_times) / len(response_times), 2),
            'avg_success_rate': round(sum(success_rates) / len(success_rates), 3),
            'avg_quality_score': round(sum(quality_scores) / len(quality_scores), 3),
            'best_performing_source': {
                'name': best_performing[0],
                'score': round(best_performing[1].overall_score, 2)
            },
            'worst_performing_source': {
                'name': worst_performing[0],
                'score': round(worst_performing[1].overall_score, 2)
            },
            'sources_healthy': len([m for m in metrics.values() if m.health_status == HealthStatus.HEALTHY]),
            'sources_degraded': len([m for m in metrics.values() if m.health_status == HealthStatus.DEGRADED]),
            'sources_critical': len([m for m in metrics.values() if m.health_status == HealthStatus.CRITICAL])
        }

    def _generate_recommendations(self, metrics: Dict[str, HealthMetrics], alerts: List[Alert]) -> List[str]:
        """Generate actionable recommendations based on current state"""
        recommendations = []

        # Check for high response times
        slow_sources = [name for name, m in metrics.items() if m.response_time_ms > 5000]
        if slow_sources:
            recommendations.append(f"Consider optimizing or adding caching for slow sources: {', '.join(slow_sources)}")

        # Check for low success rates
        unreliable_sources = [name for name, m in metrics.items() if m.success_rate < 0.9]
        if unreliable_sources:
            recommendations.append(f"Investigate reliability issues with: {', '.join(unreliable_sources)}")

        # Check for low quality scores
        poor_quality_sources = [name for name, m in metrics.items() if m.data_quality_score < 0.8]
        if poor_quality_sources:
            recommendations.append(f"Review data quality for: {', '.join(poor_quality_sources)}")

        # Check for critical alerts
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append(f"Address {len(critical_alerts)} critical alerts immediately")

        # Check for consecutive failures
        failing_sources = [name for name, m in metrics.items() if m.consecutive_failures > 3]
        if failing_sources:
            recommendations.append(f"Check failover mechanisms for: {', '.join(failing_sources)}")

        return recommendations

    def _convert_to_csv_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Convert report data to CSV-friendly format"""
        # Create DataFrames for different sections
        sources_data = []
        for name, data in report['data_sources'].items():
            row = {'source_name': name, **data}
            sources_data.append(row)

        alerts_data = []
        for alert in report['active_alerts']:
            alerts_data.append({
                'alert_id': alert['alert_id'],
                'source_name': alert['source_name'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                'message': alert['message'],
                'timestamp': alert['timestamp']
            })

        return {
            'sources_df': pd.DataFrame(sources_data),
            'alerts_df': pd.DataFrame(alerts_data),
            'summary': report['system_health_summary'],
            'metadata': report['report_metadata']
        }

    def _convert_to_html_report(self, report: Dict[str, Any]) -> str:
        """Convert report to HTML format"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Source Health Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .source {{ margin: 10px 0; padding: 10px; border: 1px solid #dee2e6; border-radius: 5px; }}
                .healthy {{ border-left: 5px solid #28a745; }}
                .degraded {{ border-left: 5px solid #ffc107; }}
                .critical {{ border-left: 5px solid #dc3545; }}
                .unavailable {{ border-left: 5px solid #6c757d; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .alert {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .alert-critical {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
                .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Data Source Health Report</h1>
                <p>Generated: {report['report_metadata']['generated_at']}</p>
                <p>Report Period: {report['report_metadata']['report_period_hours']} hours</p>
            </div>

            <div class="summary">
                <h2>System Health Summary</h2>
                <p><strong>Overall Status:</strong> {report['system_health_summary']['overall_status']}</p>
                <p><strong>Average Score:</strong> {report['system_health_summary']['average_score']:.1f}%</p>
                <p><strong>Total Sources:</strong> {report['system_health_summary']['sources_count']}</p>
                <p><strong>Healthy:</strong> {report['system_health_summary']['healthy_sources']},
                   <strong>Degraded:</strong> {report['system_health_summary']['degraded_sources']},
                   <strong>Critical:</strong> {report['system_health_summary']['critical_sources']}</p>
            </div>

            <h2>Data Sources</h2>
        """

        # Add data sources
        for name, data in report['data_sources'].items():
            status_class = data['health_status']
            html += f"""
            <div class="source {status_class}">
                <h3>{name}</h3>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Health Status</td><td>{data['health_status']}</td></tr>
                    <tr><td>Overall Score</td><td>{data['overall_score']}%</td></tr>
                    <tr><td>Response Time</td><td>{data['response_time_ms']}ms</td></tr>
                    <tr><td>Success Rate</td><td>{data['success_rate'] * 100:.1f}%</td></tr>
                    <tr><td>Data Quality</td><td>{data['data_quality_score'] * 100:.1f}%</td></tr>
                    <tr><td>Availability</td><td>{data['availability_percentage']}%</td></tr>
                </table>
            </div>
            """

        # Add active alerts
        if report['active_alerts']:
            html += "<h2>Active Alerts</h2>"
            for alert in report['active_alerts']:
                alert_class = 'alert-critical' if alert['severity'] in ['critical', 'emergency'] else 'alert-warning'
                html += f"""
                <div class="alert {alert_class}">
                    <strong>{alert['source_name']}</strong> - {alert['severity'].upper()}<br>
                    {alert['message']}<br>
                    <small>{alert['timestamp']}</small>
                </div>
                """

        # Add recommendations
        if report['recommendations']:
            html += "<h2>Recommendations</h2><ul>"
            for rec in report['recommendations']:
                html += f"<li>{rec}</li>"
            html += "</ul>"

        html += """
        </body>
        </html>
        """
        return html

    def export_report(self, filepath: str, format: str = 'json', hours: int = 24) -> bool:
        """
        Export health report to file.

        Args:
            filepath: Path to save the report
            format: Export format ('json', 'csv', 'html')
            hours: Hours of historical data to include

        Returns:
            True if export was successful
        """
        try:
            report = self.generate_health_report(format, hours)

            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format == 'csv':
                # Export multiple CSV files
                base_path = Path(filepath).with_suffix('')
                report['sources_df'].to_csv(f"{base_path}_sources.csv", index=False)
                report['alerts_df'].to_csv(f"{base_path}_alerts.csv", index=False)

                # Save summary as JSON
                with open(f"{base_path}_summary.json", 'w') as f:
                    json.dump({
                        'summary': report['summary'],
                        'metadata': report['metadata']
                    }, f, indent=2, default=str)
            elif format == 'html':
                with open(filepath, 'w') as f:
                    f.write(report)

            self.logger.info(f"Health report exported to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export health report: {e}")
            return False


class HealthDashboard:
    """
    Streamlit-based health monitoring dashboard.

    Provides real-time visualization of data source health metrics,
    historical trends, and alert management.
    """

    def __init__(self, health_monitor: DataSourceHealthMonitor, alerting_system: AlertingSystem):
        """
        Initialize the health dashboard.

        Args:
            health_monitor: Health monitoring system instance
            alerting_system: Alerting system instance
        """
        self.health_monitor = health_monitor
        self.alerting_system = alerting_system
        self.reporter = HealthReporter(health_monitor, alerting_system)

    def render_dashboard(self) -> None:
        """Render the complete health monitoring dashboard"""
        st.set_page_config(
            page_title="Data Source Health Monitor",
            page_icon="📊",
            layout="wide"
        )

        st.title("📊 Data Source Health Monitor")
        st.markdown("Real-time monitoring of financial data source health and performance")

        # Auto-refresh
        if st.button("🔄 Refresh Data"):
            self.health_monitor.perform_health_checks()

        # Get current data
        current_metrics = self.health_monitor.get_all_health_metrics()
        summary = self.health_monitor.get_health_summary()
        active_alerts = self.alerting_system.get_active_alerts()

        # Main dashboard sections
        self._render_overview_section(summary)
        self._render_sources_section(current_metrics)
        self._render_alerts_section(active_alerts)
        self._render_trends_section(current_metrics)
        self._render_reports_section()

    def _render_overview_section(self, summary: Dict[str, Any]) -> None:
        """Render system overview section"""
        st.subheader("🎯 System Overview")

        if not summary or summary.get('status') == 'no_data':
            st.warning("No health data available. Data sources may not be configured or monitored yet.")
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Overall Status",
                summary.get('overall_status', 'unknown').title(),
                delta=None
            )

        with col2:
            st.metric(
                "Average Score",
                f"{summary.get('average_score', 0):.1f}%",
                delta=None
            )

        with col3:
            st.metric(
                "Total Sources",
                summary.get('sources_count', 0),
                delta=None
            )

        with col4:
            st.metric(
                "Healthy Sources",
                summary.get('healthy_sources', 0),
                delta=f"-{summary.get('critical_sources', 0)}" if summary.get('critical_sources', 0) > 0 else None,
                delta_color="inverse"
            )

        # Status breakdown chart
        if summary.get('sources_count', 0) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Healthy', 'Degraded', 'Critical', 'Unavailable'],
                values=[
                    summary.get('healthy_sources', 0),
                    summary.get('degraded_sources', 0),
                    summary.get('critical_sources', 0),
                    summary.get('unavailable_sources', 0)
                ],
                hole=0.3,
                marker_colors=['#28a745', '#ffc107', '#dc3545', '#6c757d']
            )])
            fig.update_layout(title="Source Health Distribution", height=300)
            st.plotly_chart(fig, use_container_width=True)

    def _render_sources_section(self, metrics: Dict[str, HealthMetrics]) -> None:
        """Render individual data sources section"""
        st.subheader("📡 Data Sources")

        if not metrics:
            st.info("No data sources are currently being monitored.")
            return

        for source_name, metric in metrics.items():
            with st.expander(f"{source_name} - {metric.health_status.value.title()}",
                           expanded=metric.health_status in [HealthStatus.CRITICAL, HealthStatus.UNAVAILABLE]):

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Overall Score", f"{metric.overall_score:.1f}%")
                    st.metric("Success Rate", f"{metric.success_rate * 100:.1f}%")

                with col2:
                    st.metric("Response Time", f"{metric.response_time_ms:.0f}ms")
                    st.metric("Data Quality", f"{metric.data_quality_score * 100:.1f}%")

                with col3:
                    st.metric("Availability", f"{metric.availability_percentage:.1f}%")
                    st.metric("Consecutive Failures", metric.consecutive_failures)

                # Additional details
                if metric.last_error:
                    st.error(f"Last Error: {metric.last_error}")

                if metric.error_types:
                    st.write("**Error Types:**")
                    for error_type, count in metric.error_types.items():
                        st.write(f"- {error_type}: {count}")

    def _render_alerts_section(self, alerts: List[Alert]) -> None:
        """Render active alerts section"""
        st.subheader("🚨 Active Alerts")

        if not alerts:
            st.success("No active alerts - all systems operational!")
            return

        # Group alerts by severity
        critical_alerts = [a for a in alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]
        warning_alerts = [a for a in alerts if a.severity == AlertSeverity.WARNING]

        if critical_alerts:
            st.error(f"⚠️ {len(critical_alerts)} Critical Alerts")
            for alert in critical_alerts:
                st.error(f"**{alert.source_name}**: {alert.message}")

        if warning_alerts:
            st.warning(f"⚠️ {len(warning_alerts)} Warning Alerts")
            for alert in warning_alerts:
                st.warning(f"**{alert.source_name}**: {alert.message}")

        # Alert resolution interface
        st.write("**Alert Management**")
        alert_ids = [alert.alert_id for alert in alerts]
        selected_alert = st.selectbox("Select alert to resolve:", [""] + alert_ids)

        if selected_alert:
            resolution_message = st.text_input("Resolution message (optional):")
            if st.button("Resolve Alert"):
                if self.alerting_system.resolve_alert(selected_alert, resolution_message):
                    st.success(f"Alert {selected_alert} resolved successfully!")
                    st.experimental_rerun()

    def _render_trends_section(self, metrics: Dict[str, HealthMetrics]) -> None:
        """Render historical trends section"""
        st.subheader("📈 Historical Trends")

        if not metrics:
            st.info("No trend data available.")
            return

        # Time range selection
        hours = st.slider("Historical period (hours):", 1, 168, 24)

        # Get historical data
        trends_data = self.reporter._get_historical_trends(hours)

        if not any(trends_data.values()):
            st.info("No historical data available for the selected period.")
            return

        # Create trend charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Response Time', 'Success Rate', 'Overall Score', 'Health Status'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        colors = px.colors.qualitative.Set1

        for i, (source_name, data) in enumerate(trends_data.items()):
            if not data:
                continue

            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            color = colors[i % len(colors)]

            # Response time
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['response_time_ms'],
                          name=f"{source_name} Response Time", line=dict(color=color)),
                row=1, col=1
            )

            # Success rate
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['success_rate'],
                          name=f"{source_name} Success Rate", line=dict(color=color)),
                row=1, col=2
            )

            # Overall score
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['overall_score'],
                          name=f"{source_name} Score", line=dict(color=color)),
                row=2, col=1
            )

        fig.update_layout(height=600, title_text="Data Source Performance Trends")
        st.plotly_chart(fig, use_container_width=True)

    def _render_reports_section(self) -> None:
        """Render reports and export section"""
        st.subheader("📋 Reports & Export")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Generate Health Report**")
            format_option = st.selectbox("Report Format:", ["json", "html", "csv"])
            hours_option = st.number_input("Hours of data:", min_value=1, max_value=168, value=24)

            if st.button("Generate Report"):
                report = self.reporter.generate_health_report(format_option, hours_option)

                if format_option == "json":
                    st.json(report)
                elif format_option == "html":
                    st.components.v1.html(report, height=600, scrolling=True)
                else:  # CSV
                    st.write("**Sources Data:**")
                    st.dataframe(report['sources_df'])
                    st.write("**Alerts Data:**")
                    st.dataframe(report['alerts_df'])

        with col2:
            st.write("**Export Options**")
            if st.button("Export Current Report"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"health_report_{timestamp}.{format_option}"

                if self.reporter.export_report(filename, format_option, hours_option):
                    st.success(f"Report exported to {filename}")
                else:
                    st.error("Failed to export report")

        # Performance insights
        st.write("**Performance Insights**")
        current_metrics = self.health_monitor.get_all_health_metrics()
        if current_metrics:
            insights = self.reporter._generate_performance_insights(current_metrics)
            st.json(insights)

        # Recommendations
        st.write("**Recommendations**")
        active_alerts = self.alerting_system.get_active_alerts()
        recommendations = self.reporter._generate_recommendations(current_metrics, active_alerts)
        if recommendations:
            for rec in recommendations:
                st.info(rec)
        else:
            st.success("No recommendations - system is performing well!")