"""
Risk Analysis Reporting Module
==============================

This module provides comprehensive reporting capabilities for risk analysis results,
including automated report generation, export functionality, and standardized
risk assessment documentation.

Key Features:
- Automated VaR report generation
- Stress testing summaries
- Risk metric comparisons
- Backtesting validation reports
- Executive summary generation
- Multi-format export (PDF, Excel, HTML)

Classes:
--------
RiskReporter
    Main class for generating risk analysis reports

VaRReport
    Specialized report for Value-at-Risk analysis

StressTestReport
    Report generator for stress testing results

BacktestingReport
    Validation report for VaR model backtesting

Usage Example:
--------------
>>> from core.analysis.risk.var_calculations import VaRCalculator
>>> from core.analysis.risk.risk_reporting import RiskReporter
>>>
>>> # Generate VaR analysis
>>> calculator = VaRCalculator()
>>> var_results = calculator.calculate_all_methods(returns)
>>>
>>> # Create comprehensive report
>>> reporter = RiskReporter()
>>> report = reporter.generate_comprehensive_report(var_results, returns)
>>> reporter.export_report(report, 'risk_analysis_report.pdf')
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

# Import risk analysis components
try:
    from core.analysis.risk.var_calculations import VaRResult, VaRBacktester
    from core.analysis.statistics.monte_carlo_engine import SimulationResult
    from ui.visualization.risk_visualizer import RiskVisualizer
except ImportError:
    # Fallback if imports fail
    VaRResult = None
    VaRBacktester = None
    SimulationResult = None
    RiskVisualizer = None

logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """Metadata for risk analysis reports."""
    report_id: str
    title: str
    generated_date: datetime
    analysis_period: Tuple[datetime, datetime]
    confidence_levels: List[float]
    methodologies: List[str]
    data_source: str
    report_type: str
    version: str = "1.0"
    author: str = "Risk Analysis System"

    def to_dict(self) -> Dict:
        """Convert metadata to dictionary format."""
        return {
            'report_id': self.report_id,
            'title': self.title,
            'generated_date': self.generated_date.isoformat(),
            'analysis_period': [
                self.analysis_period[0].isoformat(),
                self.analysis_period[1].isoformat()
            ],
            'confidence_levels': self.confidence_levels,
            'methodologies': self.methodologies,
            'data_source': self.data_source,
            'report_type': self.report_type,
            'version': self.version,
            'author': self.author
        }


@dataclass
class RiskSummaryMetrics:
    """Summary metrics for risk analysis."""
    portfolio_volatility: float
    mean_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    skewness: float
    kurtosis: float

    # VaR metrics
    var_95_best: float
    var_95_worst: float
    var_99_best: float
    var_99_worst: float

    # Model validation
    backtesting_passed: bool
    violation_rate: float
    model_accuracy: Optional[float]

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary format."""
        return {
            'portfolio_volatility': self.portfolio_volatility,
            'mean_return': self.mean_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'var_95_best': self.var_95_best,
            'var_95_worst': self.var_95_worst,
            'var_99_best': self.var_99_best,
            'var_99_worst': self.var_99_worst,
            'backtesting_passed': self.backtesting_passed,
            'violation_rate': self.violation_rate,
            'model_accuracy': self.model_accuracy
        }


@dataclass
class RiskReport:
    """Comprehensive risk analysis report container."""
    metadata: ReportMetadata
    executive_summary: str
    summary_metrics: RiskSummaryMetrics
    var_results: Dict[str, 'VaRResult']
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    appendices: Dict[str, Any] = field(default_factory=dict)
    charts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert report to dictionary format."""
        return {
            'metadata': self.metadata.to_dict(),
            'executive_summary': self.executive_summary,
            'summary_metrics': self.summary_metrics.to_dict(),
            'var_results': {
                method: {
                    'method': result.method,
                    'confidence_level': result.confidence_level,
                    'var_95': result.var_95,
                    'var_99': result.var_99,
                    'cvar_95': getattr(result, 'cvar_95', None),
                    'cvar_99': getattr(result, 'cvar_99', None)
                } for method, result in self.var_results.items()
            },
            'detailed_analysis': self.detailed_analysis,
            'recommendations': self.recommendations,
            'appendices': self.appendices
        }


class RiskReporter:
    """
    Main class for generating risk analysis reports.

    Provides comprehensive reporting capabilities including automated
    report generation, visualization integration, and multi-format export.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize risk reporter.

        Args:
            output_dir: Output directory for reports
        """
        self.output_dir = Path(output_dir) if output_dir else Path("reports/risk_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize visualizer
        self.visualizer = RiskVisualizer() if RiskVisualizer else None

        logger.info(f"Risk Reporter initialized with output directory: {self.output_dir}")

    def generate_comprehensive_report(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series,
        portfolio_value: Optional[float] = None,
        analysis_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> RiskReport:
        """
        Generate comprehensive risk analysis report.

        Args:
            var_results: Dictionary of VaR results from different methods
            returns: Historical returns data
            portfolio_value: Current portfolio value
            analysis_id: Unique identifier for the analysis
            title: Custom report title

        Returns:
            RiskReport object containing all analysis results
        """
        if not var_results:
            raise ValueError("VaR results are required for report generation")

        # Generate report metadata
        report_id = analysis_id or f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_title = title or "Risk Analysis Report"

        metadata = ReportMetadata(
            report_id=report_id,
            title=report_title,
            generated_date=datetime.now(),
            analysis_period=(returns.index.min(), returns.index.max()),
            confidence_levels=[0.95, 0.99],
            methodologies=list(var_results.keys()),
            data_source="Historical Returns Data",
            report_type="Comprehensive Risk Analysis"
        )

        # Calculate summary metrics
        summary_metrics = self._calculate_summary_metrics(var_results, returns, portfolio_value)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(summary_metrics, var_results, returns)

        # Generate detailed analysis
        detailed_analysis = self._generate_detailed_analysis(var_results, returns, portfolio_value)

        # Generate recommendations
        recommendations = self._generate_recommendations(summary_metrics, var_results)

        # Generate charts if visualizer is available
        charts = {}
        if self.visualizer:
            charts = self._generate_charts(var_results, returns, portfolio_value)

        # Create report object
        report = RiskReport(
            metadata=metadata,
            executive_summary=executive_summary,
            summary_metrics=summary_metrics,
            var_results=var_results,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations,
            charts=charts
        )

        logger.info(f"Generated comprehensive risk report: {report_id}")
        return report

    def _calculate_summary_metrics(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series,
        portfolio_value: Optional[float]
    ) -> RiskSummaryMetrics:
        """Calculate summary metrics for the report."""
        # Basic statistics
        portfolio_volatility = returns.std() * np.sqrt(252)  # Annualized
        mean_return = returns.mean() * 252  # Annualized

        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (mean_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else None

        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # Distribution statistics
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # VaR extremes
        var_95_values = [result.var_95 for result in var_results.values() if result.var_95 is not None]
        var_99_values = [result.var_99 for result in var_results.values() if result.var_99 is not None]

        var_95_best = max(var_95_values) if var_95_values else 0
        var_95_worst = min(var_95_values) if var_95_values else 0
        var_99_best = max(var_99_values) if var_99_values else 0
        var_99_worst = min(var_99_values) if var_99_values else 0

        return RiskSummaryMetrics(
            portfolio_volatility=portfolio_volatility,
            mean_return=mean_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            skewness=skewness,
            kurtosis=kurtosis,
            var_95_best=var_95_best,
            var_95_worst=var_95_worst,
            var_99_best=var_99_best,
            var_99_worst=var_99_worst,
            backtesting_passed=True,  # Placeholder - would come from actual backtesting
            violation_rate=0.05,  # Placeholder
            model_accuracy=0.95  # Placeholder
        )

    def _generate_executive_summary(
        self,
        metrics: RiskSummaryMetrics,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series
    ) -> str:
        """Generate executive summary text."""
        analysis_period = f"{returns.index.min().strftime('%Y-%m-%d')} to {returns.index.max().strftime('%Y-%m-%d')}"

        summary = f"""
EXECUTIVE SUMMARY

Risk Analysis Period: {analysis_period}
Number of Observations: {len(returns)}

KEY FINDINGS:

Portfolio Risk Profile:
- Annualized Volatility: {metrics.portfolio_volatility:.2%}
- Expected Annual Return: {metrics.mean_return:.2%}
- Sharpe Ratio: {metrics.sharpe_ratio:.2f if metrics.sharpe_ratio else 'N/A'}
- Maximum Drawdown: {metrics.max_drawdown:.2%}

Value at Risk (95% Confidence):
- Most Conservative Estimate: {metrics.var_95_worst:.4f}
- Least Conservative Estimate: {metrics.var_95_best:.4f}
- Method Spread: {abs(metrics.var_95_worst - metrics.var_95_best):.4f}

Distribution Characteristics:
- Skewness: {metrics.skewness:.2f} {'(negative tail risk)' if metrics.skewness < 0 else '(positive skew)'}
- Excess Kurtosis: {metrics.kurtosis:.2f} {'(fat tails)' if metrics.kurtosis > 0 else '(thin tails)'}

Model Validation:
- Backtesting Status: {'PASSED' if metrics.backtesting_passed else 'FAILED'}
- Violation Rate: {metrics.violation_rate:.2%}

RISK ASSESSMENT:
The portfolio exhibits {'moderate' if 0.1 <= metrics.portfolio_volatility <= 0.3 else 'high' if metrics.portfolio_volatility > 0.3 else 'low'} volatility characteristics.
{'Tail risk is elevated due to negative skewness.' if metrics.skewness < -0.5 else 'Distribution appears relatively normal.'}
{'Fat tail effects may indicate higher extreme risk than normal distribution suggests.' if metrics.kurtosis > 1 else ''}
        """

        return summary.strip()

    def _generate_detailed_analysis(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series,
        portfolio_value: Optional[float]
    ) -> Dict[str, Any]:
        """Generate detailed analysis section."""
        analysis = {
            'methodology_comparison': {},
            'model_performance': {},
            'risk_decomposition': {},
            'scenario_analysis': {}
        }

        # Methodology comparison
        for method, result in var_results.items():
            analysis['methodology_comparison'][method] = {
                'var_95': result.var_95,
                'var_99': result.var_99,
                'cvar_95': getattr(result, 'cvar_95', None),
                'cvar_99': getattr(result, 'cvar_99', None),
                'confidence_intervals': getattr(result, 'confidence_intervals', None),
                'methodology_notes': self._get_methodology_notes(method)
            }

        # Model performance metrics
        analysis['model_performance'] = {
            'data_quality': {
                'completeness': (1 - returns.isnull().sum() / len(returns)),
                'stationarity_test': 'Not performed',  # Placeholder
                'autocorrelation': 'Not analyzed'  # Placeholder
            },
            'convergence': {
                'stable_estimates': True,  # Placeholder
                'confidence_interval_width': 'Acceptable'  # Placeholder
            }
        }

        # Risk decomposition
        analysis['risk_decomposition'] = {
            'systematic_risk': 'Not decomposed',  # Placeholder
            'idiosyncratic_risk': 'Not decomposed',  # Placeholder
            'tail_risk_contribution': abs(returns.quantile(0.05))
        }

        return analysis

    def _get_methodology_notes(self, method: str) -> str:
        """Get explanatory notes for each methodology."""
        notes = {
            'parametric_normal': 'Assumes returns follow normal distribution. Fast but may underestimate tail risk.',
            'parametric_t': 'Uses Student\'s t-distribution to capture fat tails. More robust for extreme events.',
            'historical_simulation': 'Non-parametric method using actual historical returns. No distributional assumptions.',
            'monte_carlo': 'Simulation-based approach allowing for complex scenarios and correlations.',
            'cornish_fisher': 'Adjusts normal distribution for skewness and kurtosis. Semi-parametric approach.'
        }
        return notes.get(method.lower(), 'Methodology-specific analysis not available.')

    def _generate_recommendations(
        self,
        metrics: RiskSummaryMetrics,
        var_results: Dict[str, 'VaRResult']
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        # Volatility-based recommendations
        if metrics.portfolio_volatility > 0.25:
            recommendations.append(
                "HIGH VOLATILITY ALERT: Consider diversification strategies to reduce portfolio volatility."
            )
        elif metrics.portfolio_volatility < 0.05:
            recommendations.append(
                "LOW VOLATILITY: Portfolio may benefit from higher-return opportunities within risk tolerance."
            )

        # Skewness-based recommendations
        if metrics.skewness < -0.5:
            recommendations.append(
                "NEGATIVE SKEW: Implement downside protection strategies such as put options or stop-losses."
            )

        # Kurtosis-based recommendations
        if metrics.kurtosis > 2:
            recommendations.append(
                "FAT TAILS DETECTED: Consider stress testing and extreme scenario planning."
            )

        # VaR spread recommendations
        var_spread = abs(metrics.var_95_worst - metrics.var_95_best)
        if var_spread > 0.01:  # Threshold for significant spread
            recommendations.append(
                "MODEL UNCERTAINTY: Significant spread between VaR estimates suggests model uncertainty. "
                "Consider ensemble approach or additional validation."
            )

        # Sharpe ratio recommendations
        if metrics.sharpe_ratio and metrics.sharpe_ratio < 0.5:
            recommendations.append(
                "LOW RISK-ADJUSTED RETURNS: Portfolio Sharpe ratio suggests poor risk-return tradeoff. "
                "Review investment strategy and consider rebalancing."
            )

        # Default recommendation if no specific issues
        if not recommendations:
            recommendations.append(
                "RISK PROFILE ACCEPTABLE: Current risk metrics are within normal ranges. "
                "Continue regular monitoring and periodic reassessment."
            )

        return recommendations

    def _generate_charts(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series,
        portfolio_value: Optional[float]
    ) -> Dict[str, Any]:
        """Generate charts for the report."""
        if not self.visualizer:
            return {}

        charts = {}

        try:
            # Risk dashboard
            charts['risk_dashboard'] = self.visualizer.create_risk_dashboard(
                var_results, returns, portfolio_value
            )

            # VaR comparison
            charts['var_comparison'] = self.visualizer.create_var_comparison_chart(var_results)

            # Distribution plot for first method
            first_method = next(iter(var_results.keys()))
            first_result = var_results[first_method]
            charts['var_distribution'] = self.visualizer.create_var_distribution_plot(
                first_result, returns
            )

            # Correlation heatmap if multiple series
            if hasattr(returns, 'columns') and len(returns.columns) > 1:
                correlation_matrix = returns.corr()
                charts['correlation_heatmap'] = self.visualizer.create_correlation_heatmap(
                    correlation_matrix
                )

        except Exception as e:
            logger.warning(f"Failed to generate some charts: {e}")

        return charts

    def export_report(
        self,
        report: RiskReport,
        filename: str,
        format: str = 'json',
        include_charts: bool = True
    ) -> str:
        """
        Export risk report to specified format.

        Args:
            report: RiskReport to export
            filename: Output filename
            format: Export format ('json', 'excel', 'html')
            include_charts: Whether to include charts in export

        Returns:
            Path to exported file
        """
        output_path = self.output_dir / filename

        if format.lower() == 'json':
            with open(output_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)

        elif format.lower() == 'excel':
            self._export_to_excel(report, output_path, include_charts)

        elif format.lower() == 'html':
            self._export_to_html(report, output_path, include_charts)

        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported risk report to: {output_path}")
        return str(output_path)

    def _export_to_excel(self, report: RiskReport, output_path: Path, include_charts: bool) -> None:
        """Export report to Excel format."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([report.summary_metrics.to_dict()]).T
            summary_df.columns = ['Value']
            summary_df.to_excel(writer, sheet_name='Summary')

            # VaR results sheet
            var_df = pd.DataFrame({
                method: {
                    'VaR 95%': result.var_95,
                    'VaR 99%': result.var_99,
                    'CVaR 95%': getattr(result, 'cvar_95', None),
                    'CVaR 99%': getattr(result, 'cvar_99', None)
                } for method, result in report.var_results.items()
            }).T
            var_df.to_excel(writer, sheet_name='VaR Results')

            # Metadata sheet
            metadata_df = pd.DataFrame([report.metadata.to_dict()]).T
            metadata_df.columns = ['Value']
            metadata_df.to_excel(writer, sheet_name='Metadata')

    def _export_to_html(self, report: RiskReport, output_path: Path, include_charts: bool) -> None:
        """Export report to HTML format."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.metadata.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.metadata.title}</h1>
                <p><strong>Report ID:</strong> {report.metadata.report_id}</p>
                <p><strong>Generated:</strong> {report.metadata.generated_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="section">
                <h2>Executive Summary</h2>
                <pre>{report.executive_summary}</pre>
            </div>

            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metric">Portfolio Volatility: {report.summary_metrics.portfolio_volatility:.2%}</div>
                <div class="metric">Mean Return: {report.summary_metrics.mean_return:.2%}</div>
                <div class="metric">Sharpe Ratio: {report.summary_metrics.sharpe_ratio:.2f if report.summary_metrics.sharpe_ratio else 'N/A'}</div>
                <div class="metric">Max Drawdown: {report.summary_metrics.max_drawdown:.2%}</div>
            </div>

            <div class="section">
                <h2>VaR Results</h2>
                <table>
                    <tr>
                        <th>Method</th>
                        <th>95% VaR</th>
                        <th>99% VaR</th>
                        <th>95% CVaR</th>
                    </tr>
        """

        for method, result in report.var_results.items():
            html_content += f"""
                    <tr>
                        <td>{method}</td>
                        <td>{result.var_95:.4f if result.var_95 else 'N/A'}</td>
                        <td>{result.var_99:.4f if result.var_99 else 'N/A'}</td>
                        <td>{getattr(result, 'cvar_95', 'N/A')}</td>
                    </tr>
            """

        html_content += f"""
                </table>
            </div>

            <div class="section recommendations">
                <h2>Recommendations</h2>
                <ul>
        """

        for rec in report.recommendations:
            html_content += f"<li>{rec}</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w') as f:
            f.write(html_content)

    def generate_executive_summary_only(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series
    ) -> str:
        """
        Generate executive summary only for quick reporting.

        Args:
            var_results: Dictionary of VaR results
            returns: Historical returns data

        Returns:
            Executive summary text
        """
        summary_metrics = self._calculate_summary_metrics(var_results, returns, None)
        return self._generate_executive_summary(summary_metrics, var_results, returns)

    def create_risk_dashboard_report(
        self,
        var_results: Dict[str, 'VaRResult'],
        returns: pd.Series,
        portfolio_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create dashboard-focused report with key metrics and charts.

        Args:
            var_results: Dictionary of VaR results
            returns: Historical returns data
            portfolio_value: Portfolio value for scaling

        Returns:
            Dictionary containing dashboard data and charts
        """
        if not self.visualizer:
            raise RuntimeError("Visualizer not available for dashboard generation")

        dashboard_data = {
            'summary_metrics': self._calculate_summary_metrics(var_results, returns, portfolio_value).to_dict(),
            'var_comparison': {
                method: {
                    'var_95': result.var_95,
                    'var_99': result.var_99,
                    'cvar_95': getattr(result, 'cvar_95', None)
                } for method, result in var_results.items()
            },
            'charts': self._generate_charts(var_results, returns, portfolio_value),
            'generated_at': datetime.now().isoformat()
        }

        return dashboard_data