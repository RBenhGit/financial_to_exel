"""
Validation Reporting and Remediation System

This module provides comprehensive reporting capabilities for validation results,
automated remediation suggestions, and actionable insights for data quality improvement.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import logging

from error_handler import EnhancedLogger
from ..data_processing.data_validator import DataQualityReport
from validation_orchestrator import ValidationResult, ValidationScope, ValidationPriority
from financial_metric_validators import MetricValidationResult


class ReportFormat(Enum):
    """Available report formats"""
    
    JSON = "json"
    HTML = "html"
    CSV = "csv"
    PDF = "pdf"
    MARKDOWN = "markdown"
    CONSOLE = "console"


class ReportType(Enum):
    """Types of validation reports"""
    
    SUMMARY = "summary"                    # High-level summary
    DETAILED = "detailed"                  # Comprehensive details
    REMEDIATION = "remediation"            # Focus on remediation steps
    METRICS = "metrics"                    # Metric-specific analysis
    TRENDING = "trending"                  # Historical trends
    COMPLIANCE = "compliance"              # Compliance and governance


class RemediationPriority(Enum):
    """Priority levels for remediation actions"""
    
    CRITICAL = "critical"     # Must be fixed immediately
    HIGH = "high"            # Should be fixed soon
    MEDIUM = "medium"        # Should be addressed
    LOW = "low"              # Nice to have fixed
    INFORMATIONAL = "informational"  # For awareness only


@dataclass
class RemediationAction:
    """Individual remediation action"""
    
    action_id: str
    title: str
    description: str
    priority: RemediationPriority
    category: str
    
    # Implementation details
    estimated_effort: str  # "5 minutes", "1 hour", "1 day", etc.
    required_skills: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # Action steps
    manual_steps: List[str] = field(default_factory=list)
    automated_fix_available: bool = False
    automation_script: Optional[str] = None
    
    # Related information
    related_errors: List[str] = field(default_factory=list)
    related_warnings: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)
    
    # Tracking
    status: str = "pending"  # pending, in_progress, completed, skipped
    assigned_to: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: Optional[datetime] = None


@dataclass
class ValidationTrend:
    """Trend analysis for validation metrics over time"""
    
    metric_name: str
    time_period: str
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Trend statistics
    trend_direction: str = "stable"  # improving, declining, stable, volatile
    improvement_rate: Optional[float] = None
    volatility: Optional[float] = None
    
    # Thresholds and alerts
    threshold_breaches: int = 0
    alert_level: str = "none"  # none, info, warning, critical


class ValidationReportGenerator:
    """
    Comprehensive validation report generator with multiple output formats
    """
    
    def __init__(self, output_directory: str = "validation_reports"):
        self.logger = EnhancedLogger(__name__)
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(exist_ok=True)
        
        # Report templates and configurations
        self.report_configs = self._initialize_report_configs()
        
        # Historical data storage
        self.historical_data: List[ValidationResult] = []
        
        # Remediation action library
        self.remediation_library: Dict[str, RemediationAction] = {}
        self._initialize_remediation_library()
    
    def _initialize_report_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize report configuration templates"""
        return {
            ReportType.SUMMARY.value: {
                'include_sections': ['executive_summary', 'key_metrics', 'critical_issues', 'recommendations'],
                'max_issues_shown': 5,
                'focus_on_critical': True
            },
            ReportType.DETAILED.value: {
                'include_sections': ['all'],
                'max_issues_shown': -1,  # Show all
                'include_raw_data': True,
                'include_statistical_analysis': True
            },
            ReportType.REMEDIATION.value: {
                'include_sections': ['remediation_actions', 'implementation_guide', 'effort_estimates'],
                'group_by_priority': True,
                'include_automation_scripts': True
            },
            ReportType.METRICS.value: {
                'include_sections': ['metric_analysis', 'quality_scores', 'trend_analysis'],
                'include_visualizations': True,
                'metric_deep_dive': True
            }
        }
    
    def _initialize_remediation_library(self):
        """Initialize library of common remediation actions"""
        
        actions = [
            RemediationAction(
                action_id="fix_missing_data",
                title="Address Missing Financial Data",
                description="Fill gaps in financial statement data using appropriate methods",
                priority=RemediationPriority.HIGH,
                category="data_completeness",
                estimated_effort="2-4 hours",
                required_skills=["data_analysis", "finance_knowledge"],
                manual_steps=[
                    "Identify the source of missing data",
                    "Check if data is available from alternative sources",
                    "Consider interpolation for minor gaps",
                    "Use industry averages for benchmarking if needed",
                    "Document any assumptions made"
                ],
                documentation_links=[
                    "https://docs.financialanalysis.com/data-gaps",
                    "https://accounting-standards.org/missing-data"
                ]
            ),
            RemediationAction(
                action_id="fix_network_connectivity",
                title="Resolve Network Connectivity Issues",
                description="Fix network connectivity problems preventing data retrieval",
                priority=RemediationPriority.CRITICAL,
                category="system_infrastructure",
                estimated_effort="15-30 minutes",
                required_skills=["network_troubleshooting"],
                manual_steps=[
                    "Check internet connection",
                    "Verify DNS resolution",
                    "Test firewall settings",
                    "Check proxy configuration",
                    "Retry with different timeout settings"
                ],
                automated_fix_available=True,
                automation_script="network_diagnostic_tool.py"
            ),
            RemediationAction(
                action_id="update_dependencies",
                title="Update Package Dependencies",
                description="Update outdated Python packages to meet minimum requirements",
                priority=RemediationPriority.MEDIUM,
                category="system_dependencies",
                estimated_effort="10-20 minutes",
                required_skills=["python_package_management"],
                manual_steps=[
                    "Review current package versions",
                    "Update packages using pip install --upgrade",
                    "Test functionality after updates",
                    "Update requirements.txt if needed"
                ],
                automated_fix_available=True,
                automation_script="update_packages.py"
            ),
            RemediationAction(
                action_id="fix_data_outliers",
                title="Address Data Outliers",
                description="Review and handle statistical outliers in financial data",
                priority=RemediationPriority.MEDIUM,
                category="data_quality",
                estimated_effort="1-2 hours",
                required_skills=["statistical_analysis", "finance_knowledge"],
                manual_steps=[
                    "Review identified outliers for business context",
                    "Verify outliers against original source data",
                    "Determine if outliers are legitimate or errors",
                    "Apply appropriate treatment (keep, adjust, or remove)",
                    "Document decisions and rationale"
                ]
            ),
            RemediationAction(
                action_id="validate_ticker_format",
                title="Fix Ticker Symbol Format Issues",
                description="Correct ticker symbol formatting to match exchange standards",
                priority=RemediationPriority.HIGH,
                category="data_format",
                estimated_effort="5-10 minutes",
                required_skills=["data_entry"],
                manual_steps=[
                    "Review invalid ticker formats",
                    "Apply standard formatting rules",
                    "Add exchange suffixes if needed (e.g., .TO for Toronto)",
                    "Validate against exchange listings",
                    "Test with data retrieval functions"
                ],
                automated_fix_available=True,
                automation_script="ticker_format_fixer.py"
            ),
            RemediationAction(
                action_id="separate_test_data",
                title="Separate Test Data from Production",
                description="Ensure test data and metadata are not used in production calculations",
                priority=RemediationPriority.CRITICAL,
                category="testing_compliance",
                estimated_effort="30 minutes - 2 hours",
                required_skills=["code_review", "testing_frameworks"],
                manual_steps=[
                    "Identify all test data usage",
                    "Review code for metadata markers",
                    "Implement proper test/production separation",
                    "Add validation checks for production mode",
                    "Update testing framework configuration"
                ]
            )
        ]
        
        for action in actions:
            self.remediation_library[action.action_id] = action
    
    def add_historical_result(self, result: ValidationResult):
        """Add validation result to historical tracking"""
        self.historical_data.append(result)
        
        # Keep only recent history (last 30 days by default)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.historical_data = [
            r for r in self.historical_data 
            if r.validation_timestamp > cutoff_date
        ]
    
    def generate_report(
        self,
        validation_result: ValidationResult,
        report_type: ReportType = ReportType.DETAILED,
        format: ReportFormat = ReportFormat.HTML,
        include_historical: bool = True,
        custom_config: Dict[str, Any] = None
    ) -> str:
        """
        Generate comprehensive validation report
        
        Args:
            validation_result: Validation result to report on
            report_type: Type of report to generate
            format: Output format for the report
            include_historical: Whether to include historical trend analysis
            custom_config: Custom configuration overrides
            
        Returns:
            Path to generated report file
        """
        self.logger.info(f"Generating {report_type.value} report in {format.value} format")
        
        # Get report configuration
        config = self.report_configs.get(report_type.value, {})
        if custom_config:
            config.update(custom_config)
        
        # Add to historical data
        if include_historical:
            self.add_historical_result(validation_result)
        
        # Generate report content
        report_data = self._compile_report_data(validation_result, config, include_historical)
        
        # Format and save report
        if format == ReportFormat.JSON:
            return self._save_json_report(report_data, validation_result.validation_timestamp)
        elif format == ReportFormat.HTML:
            return self._save_html_report(report_data, validation_result.validation_timestamp)
        elif format == ReportFormat.CSV:
            return self._save_csv_report(report_data, validation_result.validation_timestamp)
        elif format == ReportFormat.MARKDOWN:
            return self._save_markdown_report(report_data, validation_result.validation_timestamp)
        elif format == ReportFormat.CONSOLE:
            return self._print_console_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _compile_report_data(
        self,
        result: ValidationResult,
        config: Dict[str, Any],
        include_historical: bool
    ) -> Dict[str, Any]:
        """Compile comprehensive report data"""
        
        report_data = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'validation_timestamp': result.validation_timestamp.isoformat(),
                'scope': result.scope.value,
                'execution_time_ms': result.execution_time_ms,
                'overall_status': 'PASSED' if result.is_valid else 'FAILED'
            },
            'executive_summary': self._generate_executive_summary(result),
            'key_metrics': self._extract_key_metrics(result),
            'critical_issues': self._identify_critical_issues(result),
            'detailed_results': self._compile_detailed_results(result),
            'remediation_actions': self._generate_remediation_actions(result),
            'recommendations': self._generate_recommendations(result),
            'statistical_analysis': self._perform_statistical_analysis(result),
            'compliance_status': self._assess_compliance_status(result)
        }
        
        if include_historical and len(self.historical_data) > 1:
            report_data['trend_analysis'] = self._analyze_trends()
        
        return report_data
    
    def _generate_executive_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Generate executive summary of validation results"""
        return {
            'overall_status': 'PASSED' if result.is_valid else 'FAILED',
            'validation_scope': result.scope.value,
            'total_errors': result.total_errors,
            'total_warnings': result.total_warnings,
            'critical_failures': len(result.critical_failures),
            'quality_score': self._calculate_overall_quality_score(result),
            'key_findings': result.critical_failures[:3] if result.critical_failures else [],
            'immediate_actions_required': len([
                action for action in self._generate_remediation_actions(result)['actions']
                if action['priority'] in ['critical', 'high']
            ]),
            'estimated_fix_time': self._estimate_total_fix_time(result)
        }
    
    def _extract_key_metrics(self, result: ValidationResult) -> Dict[str, Any]:
        """Extract key validation metrics"""
        metrics = {
            'validation_success_rate': 100.0 if result.is_valid else 0.0,
            'error_rate': result.total_errors,
            'warning_rate': result.total_warnings,
            'execution_time_ms': result.execution_time_ms
        }
        
        # Add data quality metrics if available
        if result.data_quality_result:
            metrics.update({
                'data_completeness_score': result.data_quality_result.completeness_score,
                'data_consistency_score': result.data_quality_result.consistency_score,
                'overall_data_quality_score': result.data_quality_result.overall_score
            })
        
        return metrics
    
    def _identify_critical_issues(self, result: ValidationResult) -> List[Dict[str, Any]]:
        """Identify and categorize critical issues"""
        critical_issues = []
        
        for failure in result.critical_failures:
            issue = {
                'description': failure,
                'category': self._categorize_issue(failure),
                'severity': 'critical',
                'impact': self._assess_impact(failure),
                'suggested_action': self._suggest_immediate_action(failure)
            }
            critical_issues.append(issue)
        
        return critical_issues
    
    def _generate_remediation_actions(self, result: ValidationResult) -> Dict[str, Any]:
        """Generate comprehensive remediation actions"""
        actions = []
        
        # Map errors to remediation actions
        error_action_mapping = {
            'network': 'fix_network_connectivity',
            'missing': 'fix_missing_data',
            'ticker': 'validate_ticker_format',
            'dependency': 'update_dependencies',
            'outlier': 'fix_data_outliers',
            'test': 'separate_test_data'
        }
        
        # Analyze failures and generate actions
        for failure in result.critical_failures:
            action_id = self._map_failure_to_action(failure, error_action_mapping)
            if action_id and action_id in self.remediation_library:
                action_data = self.remediation_library[action_id]
                actions.append({
                    'action_id': action_data.action_id,
                    'title': action_data.title,
                    'description': action_data.description,
                    'priority': action_data.priority.value,
                    'category': action_data.category,
                    'estimated_effort': action_data.estimated_effort,
                    'automated_fix_available': action_data.automated_fix_available,
                    'manual_steps': action_data.manual_steps,
                    'related_error': failure
                })
        
        # Sort by priority
        priority_order = ['critical', 'high', 'medium', 'low', 'informational']
        actions.sort(key=lambda x: priority_order.index(x['priority']))
        
        return {
            'actions': actions,
            'total_actions': len(actions),
            'critical_actions': len([a for a in actions if a['priority'] == 'critical']),
            'automated_actions': len([a for a in actions if a['automated_fix_available']]),
            'estimated_total_effort': self._calculate_total_effort(actions)
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze historical trends in validation results"""
        if len(self.historical_data) < 2:
            return {'message': 'Insufficient historical data for trend analysis'}
        
        # Calculate trend metrics
        error_trend = [r.total_errors for r in self.historical_data]
        warning_trend = [r.total_warnings for r in self.historical_data]
        execution_time_trend = [r.execution_time_ms for r in self.historical_data]
        
        return {
            'data_points': len(self.historical_data),
            'time_span_days': (self.historical_data[-1].validation_timestamp - 
                             self.historical_data[0].validation_timestamp).days,
            'error_trend': {
                'current': error_trend[-1] if error_trend else 0,
                'previous': error_trend[-2] if len(error_trend) > 1 else 0,
                'direction': 'improving' if len(error_trend) > 1 and error_trend[-1] < error_trend[-2] else 'declining',
                'average': sum(error_trend) / len(error_trend) if error_trend else 0
            },
            'warning_trend': {
                'current': warning_trend[-1] if warning_trend else 0,
                'previous': warning_trend[-2] if len(warning_trend) > 1 else 0,
                'direction': 'improving' if len(warning_trend) > 1 and warning_trend[-1] < warning_trend[-2] else 'declining',
                'average': sum(warning_trend) / len(warning_trend) if warning_trend else 0
            },
            'performance_trend': {
                'current_execution_time_ms': execution_time_trend[-1] if execution_time_trend else 0,
                'average_execution_time_ms': sum(execution_time_trend) / len(execution_time_trend) if execution_time_trend else 0,
                'direction': 'improving' if len(execution_time_trend) > 1 and execution_time_trend[-1] < execution_time_trend[-2] else 'declining'
            }
        }
    
    def _save_html_report(self, report_data: Dict[str, Any], timestamp: datetime) -> str:
        """Save report as HTML file"""
        filename = f"validation_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        html_content = self._generate_html_content(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved: {filepath}")
        return str(filepath)
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for the report"""
        # Basic HTML template with embedded CSS
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Validation Report - {report_data['meta']['generated_at']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .status-pass {{ color: #28a745; font-weight: bold; }}
                .status-fail {{ color: #dc3545; font-weight: bold; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .critical {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                .warning {{ background-color: #fff3cd; border-color: #ffeaa7; }}
                .success {{ background-color: #d4edda; border-color: #c3e6cb; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Financial Data Validation Report</h1>
                <p><strong>Generated:</strong> {report_data['meta']['generated_at']}</p>
                <p><strong>Validation Time:</strong> {report_data['meta']['validation_timestamp']}</p>
                <p><strong>Status:</strong> <span class="{'status-pass' if report_data['meta']['overall_status'] == 'PASSED' else 'status-fail'}">{report_data['meta']['overall_status']}</span></p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <strong>Quality Score:</strong> {report_data['executive_summary']['quality_score']:.1f}%
                </div>
                <div class="metric">
                    <strong>Total Errors:</strong> {report_data['executive_summary']['total_errors']}
                </div>
                <div class="metric">
                    <strong>Total Warnings:</strong> {report_data['executive_summary']['total_warnings']}
                </div>
                <div class="metric">
                    <strong>Execution Time:</strong> {report_data['meta']['execution_time_ms']:.2f}ms
                </div>
            </div>
            
            {self._generate_html_critical_issues(report_data.get('critical_issues', []))}
            {self._generate_html_remediation_actions(report_data.get('remediation_actions', {}))}
            {self._generate_html_key_metrics(report_data.get('key_metrics', {}))}
            
        </body>
        </html>
        """
        return html
    
    def _generate_html_critical_issues(self, critical_issues: List[Dict[str, Any]]) -> str:
        """Generate HTML for critical issues section"""
        if not critical_issues:
            return '<div class="section success"><h2>Critical Issues</h2><p>No critical issues found!</p></div>'
        
        html = '<div class="section critical"><h2>Critical Issues</h2>'
        for issue in critical_issues:
            html += f'''
            <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 3px;">
                <strong>{issue['category'].title()}:</strong> {issue['description']}<br>
                <em>Impact:</em> {issue['impact']}<br>
                <em>Suggested Action:</em> {issue['suggested_action']}
            </div>
            '''
        html += '</div>'
        return html
    
    def _generate_html_remediation_actions(self, remediation_data: Dict[str, Any]) -> str:
        """Generate HTML for remediation actions section"""
        if not remediation_data or not remediation_data.get('actions'):
            return ''
        
        html = '<div class="section"><h2>Remediation Actions</h2>'
        html += f'<p><strong>Total Actions:</strong> {remediation_data["total_actions"]} | '
        html += f'<strong>Critical:</strong> {remediation_data["critical_actions"]} | '
        html += f'<strong>Automated:</strong> {remediation_data["automated_actions"]}</p>'
        
        html += '<table><tr><th>Priority</th><th>Action</th><th>Effort</th><th>Automated</th></tr>'
        
        for action in remediation_data['actions']:
            priority_class = 'critical' if action['priority'] == 'critical' else ''
            html += f'''
            <tr class="{priority_class}">
                <td>{action['priority'].title()}</td>
                <td><strong>{action['title']}</strong><br>{action['description']}</td>
                <td>{action['estimated_effort']}</td>
                <td>{'Yes' if action['automated_fix_available'] else 'No'}</td>
            </tr>
            '''
        
        html += '</table></div>'
        return html
    
    def _generate_html_key_metrics(self, key_metrics: Dict[str, Any]) -> str:
        """Generate HTML for key metrics section"""
        if not key_metrics:
            return ''
        
        html = '<div class="section"><h2>Key Metrics</h2><table>'
        html += '<tr><th>Metric</th><th>Value</th></tr>'
        
        for metric, value in key_metrics.items():
            formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
            html += f'<tr><td>{metric.replace("_", " ").title()}</td><td>{formatted_value}</td></tr>'
        
        html += '</table></div>'
        return html
    
    def _save_json_report(self, report_data: Dict[str, Any], timestamp: datetime) -> str:
        """Save report as JSON file"""
        filename = f"validation_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"JSON report saved: {filepath}")
        return str(filepath)
    
    def _save_markdown_report(self, report_data: Dict[str, Any], timestamp: datetime) -> str:
        """Save report as Markdown file"""
        filename = f"validation_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        markdown_content = self._generate_markdown_content(report_data)
        
        with open(filepath, 'w') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Markdown report saved: {filepath}")
        return str(filepath)
    
    def _generate_markdown_content(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown content for the report"""
        md = f"""# Financial Data Validation Report

**Generated:** {report_data['meta']['generated_at']}  
**Validation Time:** {report_data['meta']['validation_timestamp']}  
**Status:** {report_data['meta']['overall_status']}  
**Scope:** {report_data['meta']['scope']}  

## Executive Summary

- **Quality Score:** {report_data['executive_summary']['quality_score']:.1f}%
- **Total Errors:** {report_data['executive_summary']['total_errors']}
- **Total Warnings:** {report_data['executive_summary']['total_warnings']}
- **Execution Time:** {report_data['meta']['execution_time_ms']:.2f}ms

"""
        
        # Add critical issues
        if report_data.get('critical_issues'):
            md += "## Critical Issues\n\n"
            for issue in report_data['critical_issues']:
                md += f"### {issue['category'].title()}\n\n"
                md += f"**Description:** {issue['description']}\n\n"
                md += f"**Impact:** {issue['impact']}\n\n"
                md += f"**Suggested Action:** {issue['suggested_action']}\n\n"
        
        # Add remediation actions
        if report_data.get('remediation_actions', {}).get('actions'):
            md += "## Remediation Actions\n\n"
            for action in report_data['remediation_actions']['actions']:
                md += f"### {action['title']} ({action['priority'].title()} Priority)\n\n"
                md += f"{action['description']}\n\n"
                md += f"**Estimated Effort:** {action['estimated_effort']}\n\n"
                if action['manual_steps']:
                    md += "**Manual Steps:**\n"
                    for step in action['manual_steps']:
                        md += f"1. {step}\n"
                    md += "\n"
        
        return md
    
    def _print_console_report(self, report_data: Dict[str, Any]) -> str:
        """Print report to console"""
        print("=" * 60)
        print("FINANCIAL DATA VALIDATION REPORT")
        print("=" * 60)
        
        print(f"Generated: {report_data['meta']['generated_at']}")
        print(f"Status: {report_data['meta']['overall_status']}")
        print(f"Quality Score: {report_data['executive_summary']['quality_score']:.1f}%")
        print(f"Errors: {report_data['executive_summary']['total_errors']}")
        print(f"Warnings: {report_data['executive_summary']['total_warnings']}")
        
        if report_data.get('critical_issues'):
            print("\nCRITICAL ISSUES:")
            for issue in report_data['critical_issues']:
                print(f"  • {issue['description']}")
        
        if report_data.get('remediation_actions', {}).get('actions'):
            print("\nREMEDIATION ACTIONS:")
            for action in report_data['remediation_actions']['actions'][:5]:  # Show top 5
                print(f"  • [{action['priority'].upper()}] {action['title']}")
        
        print("=" * 60)
        return "console"
    
    # Helper methods
    def _calculate_overall_quality_score(self, result: ValidationResult) -> float:
        """Calculate overall quality score"""
        base_score = 100.0
        
        # Deduct for errors and warnings
        base_score -= result.total_errors * 10
        base_score -= result.total_warnings * 2
        
        # Add data quality score if available
        if result.data_quality_result:
            base_score = (base_score + result.data_quality_result.overall_score) / 2
        
        return max(0.0, min(100.0, base_score))
    
    def _categorize_issue(self, failure: str) -> str:
        """Categorize an issue based on its description"""
        failure_lower = failure.lower()
        
        if any(word in failure_lower for word in ['network', 'connectivity', 'dns', 'timeout']):
            return 'network'
        elif any(word in failure_lower for word in ['missing', 'empty', 'null']):
            return 'data_completeness'
        elif any(word in failure_lower for word in ['invalid', 'format', 'type']):
            return 'data_format'
        elif any(word in failure_lower for word in ['dependency', 'package', 'version']):
            return 'system_dependency'
        else:
            return 'general'
    
    def _assess_impact(self, failure: str) -> str:
        """Assess the impact of a failure"""
        critical_keywords = ['critical', 'fatal', 'network', 'dependency']
        high_keywords = ['missing', 'invalid', 'failed']
        
        failure_lower = failure.lower()
        
        if any(word in failure_lower for word in critical_keywords):
            return 'High - May prevent system operation'
        elif any(word in failure_lower for word in high_keywords):
            return 'Medium - May affect data quality'
        else:
            return 'Low - Minor impact on functionality'
    
    def _suggest_immediate_action(self, failure: str) -> str:
        """Suggest immediate action for a failure"""
        failure_lower = failure.lower()
        
        if 'network' in failure_lower:
            return 'Check internet connectivity and firewall settings'
        elif 'missing' in failure_lower:
            return 'Verify data sources and file availability'
        elif 'invalid' in failure_lower:
            return 'Review and correct data format'
        elif 'dependency' in failure_lower:
            return 'Update required packages and dependencies'
        else:
            return 'Review error details and consult documentation'
    
    def _map_failure_to_action(self, failure: str, mapping: Dict[str, str]) -> Optional[str]:
        """Map a failure to a remediation action"""
        failure_lower = failure.lower()
        
        for keyword, action_id in mapping.items():
            if keyword in failure_lower:
                return action_id
        
        return None
    
    def _calculate_total_effort(self, actions: List[Dict[str, Any]]) -> str:
        """Calculate total estimated effort for all actions"""
        # Simplified estimation - in practice, this would be more sophisticated
        total_minutes = 0
        
        for action in actions:
            effort = action['estimated_effort'].lower()
            if 'minute' in effort:
                # Extract number of minutes
                import re
                minutes = re.findall(r'\d+', effort)
                if minutes:
                    total_minutes += int(minutes[0])
            elif 'hour' in effort:
                # Extract number of hours
                import re
                hours = re.findall(r'\d+', effort)
                if hours:
                    total_minutes += int(hours[0]) * 60
            elif 'day' in effort:
                # Extract number of days
                import re
                days = re.findall(r'\d+', effort)
                if days:
                    total_minutes += int(days[0]) * 8 * 60  # 8 hour work day
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        elif total_minutes < 480:  # Less than 8 hours
            return f"{total_minutes // 60} hours {total_minutes % 60} minutes"
        else:
            return f"{total_minutes // 480} days {(total_minutes % 480) // 60} hours"
    
    def _estimate_total_fix_time(self, result: ValidationResult) -> str:
        """Estimate total time to fix all issues"""
        remediation_data = self._generate_remediation_actions(result)
        return remediation_data.get('estimated_total_effort', 'Unable to estimate')
    
    def _perform_statistical_analysis(self, result: ValidationResult) -> Dict[str, Any]:
        """Perform statistical analysis of validation results"""
        analysis = {
            'validation_efficiency': {
                'errors_per_second': result.total_errors / (result.execution_time_ms / 1000) if result.execution_time_ms > 0 else 0,
                'warnings_per_second': result.total_warnings / (result.execution_time_ms / 1000) if result.execution_time_ms > 0 else 0
            },
            'error_distribution': {
                'error_percentage': (result.total_errors / (result.total_errors + result.total_warnings)) * 100 if (result.total_errors + result.total_warnings) > 0 else 0,
                'warning_percentage': (result.total_warnings / (result.total_errors + result.total_warnings)) * 100 if (result.total_errors + result.total_warnings) > 0 else 0
            }
        }
        
        if result.data_quality_result:
            analysis['data_quality_breakdown'] = {
                'completeness_score': result.data_quality_result.completeness_score,
                'consistency_score': result.data_quality_result.consistency_score,
                'overall_score': result.data_quality_result.overall_score
            }
        
        return analysis
    
    def _assess_compliance_status(self, result: ValidationResult) -> Dict[str, Any]:
        """Assess compliance with validation standards"""
        return {
            'validation_passed': result.is_valid,
            'critical_failures_count': len(result.critical_failures),
            'compliance_score': self._calculate_overall_quality_score(result),
            'requirements_met': result.is_valid and result.total_errors == 0,
            'recommendations_count': len(result.recommendations)
        }


if __name__ == "__main__":
    # Example usage
    print("=== Validation Reporting System Test ===")
    
    # Create report generator
    reporter = ValidationReportGenerator()
    
    # Create mock validation result for testing
    from validation_orchestrator import ValidationResult, ValidationScope
    from ..data_processing.data_validator import DataQualityReport
    
    mock_result = ValidationResult(
        is_valid=False,
        scope=ValidationScope.COMPREHENSIVE,
        priority=ValidationPriority.HIGH,
        total_errors=3,
        total_warnings=5,
        critical_failures=[
            "Network connectivity failed",
            "Missing required financial data",
            "Invalid ticker format detected"
        ],
        execution_time_ms=1250.5,
        remediation_steps=["Fix network", "Obtain missing data"],
        recommendations=["Review data sources", "Update validation rules"]
    )
    
    # Generate different types of reports
    print("\n=== Generating Console Report ===")
    console_path = reporter.generate_report(mock_result, ReportType.SUMMARY, ReportFormat.CONSOLE)
    
    print("\n=== Generating HTML Report ===")
    html_path = reporter.generate_report(mock_result, ReportType.DETAILED, ReportFormat.HTML)
    print(f"HTML report generated: {html_path}")
    
    print("\n=== Generating JSON Report ===")
    json_path = reporter.generate_report(mock_result, ReportType.REMEDIATION, ReportFormat.JSON)
    print(f"JSON report generated: {json_path}")
    
    print("\n=== Test Complete ===")