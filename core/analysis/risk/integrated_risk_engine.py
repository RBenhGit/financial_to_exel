"""
Integrated Risk Analysis Engine
==============================

This module provides a comprehensive, integrated risk analysis engine that combines
all risk analysis components into a unified framework for financial risk assessment.
It coordinates between multiple risk analysis modules to provide complete risk evaluation.

Key Features:
- Unified risk analysis interface
- Integration with probability distributions, correlation analysis, and scenario modeling
- Support for multiple risk types (market, credit, operational, liquidity)
- Advanced statistical modeling and factor analysis
- Real-time risk monitoring and alerting
- Comprehensive risk reporting and visualization

Classes:
--------
IntegratedRiskEngine
    Main orchestrator for all risk analysis operations

RiskAnalysisRequest
    Request specification for risk analysis

ComprehensiveRiskReport
    Unified risk reporting framework

Usage Example:
--------------
>>> from core.analysis.risk.integrated_risk_engine import IntegratedRiskEngine
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize risk engine
>>> calc = FinancialCalculator('AAPL')
>>> risk_engine = IntegratedRiskEngine(calc)
>>>
>>> # Run comprehensive risk analysis
>>> request = RiskAnalysisRequest(
>>>     analysis_type='comprehensive',
>>>     risk_types=['market', 'credit'],
>>>     confidence_levels=[0.95, 0.99],
>>>     time_horizons=[1, 5, 22]
>>> )
>>>
>>> result = risk_engine.analyze_risk(request)
>>> print(f"Overall risk score: {result.overall_risk_score}")
>>>
>>> # Generate risk report
>>> report = risk_engine.generate_comprehensive_report(result.analysis_id)
>>> report.export_to_excel('risk_analysis_report.xlsx')
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import warnings

# Import risk analysis components
from .risk_framework import RiskAnalysisFramework, RiskAnalysisResult, RiskAnalysisConfig
from .risk_metrics import RiskType, RiskLevel, RiskMetrics, AssetRiskProfile, PortfolioRiskMetrics
from .correlation_analysis import CorrelationAnalyzer, CorrelationMatrix, CorrelationMethod
from .scenario_modeling import ScenarioModelingFramework, CustomScenario, ScenarioType
from .sensitivity_analysis import SensitivityAnalyzer, SensitivityResult
from .probability_distributions import (
    DistributionFitter, ProbabilityDistribution, DistributionType, CopulaModel
)

# Import supporting modules
from ..statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult
from ...data_processing.monitoring.alerting_system import AlertingSystem, Alert, AlertSeverity

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class AnalysisScope(Enum):
    """Scope of risk analysis."""
    ASSET = "asset"
    PORTFOLIO = "portfolio"
    SECTOR = "sector"
    MARKET = "market"
    COMPREHENSIVE = "comprehensive"


class RiskDimension(Enum):
    """Dimensions of risk analysis."""
    STATISTICAL = "statistical"        # Statistical risk metrics (VaR, CVaR, etc.)
    CORRELATION = "correlation"        # Correlation-based risk
    SCENARIO = "scenario"             # Scenario analysis
    SENSITIVITY = "sensitivity"       # Sensitivity analysis
    FACTOR = "factor"                # Factor-based risk
    DISTRIBUTION = "distribution"     # Distribution modeling
    TAIL = "tail"                    # Tail risk analysis


@dataclass
class RiskAnalysisRequest:
    """
    Comprehensive specification for risk analysis requests.

    Defines all parameters and requirements for a risk analysis operation,
    including analysis scope, risk types, statistical requirements, and output preferences.
    """
    # Analysis identification
    request_id: str = field(default_factory=lambda: f"risk_req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    requester: str = "system"

    # Analysis scope and type
    analysis_scope: AnalysisScope = AnalysisScope.COMPREHENSIVE
    risk_types: List[RiskType] = field(default_factory=lambda: [RiskType.MARKET, RiskType.CREDIT])
    risk_dimensions: List[RiskDimension] = field(default_factory=lambda: [
        RiskDimension.STATISTICAL, RiskDimension.CORRELATION, RiskDimension.SCENARIO
    ])

    # Asset/Portfolio specification
    asset_ids: Optional[List[str]] = None
    portfolio_id: Optional[str] = None
    benchmark_id: Optional[str] = None

    # Statistical parameters
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    time_horizons: List[int] = field(default_factory=lambda: [1, 5, 22])  # Days
    monte_carlo_runs: int = 10000

    # Distribution modeling
    fit_distributions: bool = True
    distribution_types: Optional[List[DistributionType]] = None

    # Correlation analysis
    correlation_methods: List[CorrelationMethod] = field(default_factory=lambda: [
        CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN
    ])
    rolling_correlation: bool = True
    correlation_window: int = 60

    # Scenario analysis
    include_scenarios: bool = True
    scenario_names: Optional[List[str]] = None
    custom_scenarios: Optional[List[CustomScenario]] = None

    # Sensitivity analysis
    sensitivity_analysis: bool = True
    sensitivity_parameters: Optional[Dict[str, Any]] = None

    # Factor analysis
    factor_analysis: bool = True
    max_factors: int = 5
    factor_method: str = 'pca'

    # Output specifications
    generate_report: bool = True
    export_format: List[str] = field(default_factory=lambda: ['json', 'excel'])
    include_visualizations: bool = True

    # Advanced options
    tail_analysis: bool = True
    copula_modeling: bool = False
    stress_testing: bool = True

    # Validation and constraints
    max_analysis_time: int = 300  # Maximum analysis time in seconds

    def __post_init__(self):
        """Validate request parameters."""
        if not self.asset_ids and not self.portfolio_id:
            raise ValueError("Either asset_ids or portfolio_id must be specified")

        if any(cl <= 0 or cl >= 1 for cl in self.confidence_levels):
            raise ValueError("Confidence levels must be between 0 and 1")

        if any(th <= 0 for th in self.time_horizons):
            raise ValueError("Time horizons must be positive")


@dataclass
class ComprehensiveRiskReport:
    """
    Unified risk reporting framework that aggregates all risk analysis results
    into a comprehensive, structured report with multiple output formats.
    """
    report_id: str
    analysis_request: RiskAnalysisRequest
    risk_analysis_result: RiskAnalysisResult

    # Report sections
    executive_summary: Dict[str, Any] = field(default_factory=dict)
    risk_metrics_summary: Dict[str, Any] = field(default_factory=dict)
    distribution_analysis: Dict[str, Any] = field(default_factory=dict)
    correlation_analysis: Dict[str, Any] = field(default_factory=dict)
    scenario_analysis: Dict[str, Any] = field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = field(default_factory=dict)
    factor_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    generation_time: datetime = field(default_factory=datetime.now)
    report_version: str = "1.0"

    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of risk analysis."""
        result = self.risk_analysis_result

        summary = {
            'analysis_overview': {
                'analysis_id': result.analysis_id,
                'analysis_date': result.analysis_date.strftime('%Y-%m-%d %H:%M:%S'),
                'analysis_scope': self.analysis_request.analysis_scope.value,
                'assets_analyzed': len(self.analysis_request.asset_ids or []),
                'calculation_time': result.calculation_time
            },
            'key_findings': {
                'overall_risk_score': result.overall_risk_score,
                'risk_level': result.risk_level.level_name if result.risk_level else 'Unknown',
                'key_risk_drivers': result.key_risk_drivers[:3],  # Top 3 drivers
                'high_priority_alerts': self._identify_high_priority_alerts()
            },
            'risk_metrics_highlights': self._extract_risk_highlights(),
            'scenario_impact_summary': self._summarize_scenario_impacts(),
            'recommendations_summary': self._generate_quick_recommendations()
        }

        self.executive_summary = summary
        return summary

    def _identify_high_priority_alerts(self) -> List[Dict[str, Any]]:
        """Identify high-priority risk alerts."""
        alerts = []
        result = self.risk_analysis_result

        # Check for extreme risk levels
        if result.overall_risk_score and result.overall_risk_score > 80:
            alerts.append({
                'type': 'extreme_risk',
                'severity': 'high',
                'message': f'Overall risk score ({result.overall_risk_score:.1f}) indicates extreme risk exposure',
                'recommendation': 'Consider immediate risk reduction measures'
            })

        # Check for high correlations
        if result.correlation_matrices:
            for method, corr_matrix in result.correlation_matrices.items():
                avg_corr = corr_matrix.market_concentration()
                if abs(avg_corr) > 0.8:
                    alerts.append({
                        'type': 'high_correlation',
                        'severity': 'medium',
                        'message': f'High asset correlations detected ({avg_corr:.2f})',
                        'recommendation': 'Consider diversification to reduce concentration risk'
                    })

        # Check for extreme scenario vulnerabilities
        if result.scenario_results:
            for scenario_name, scenario_result in result.scenario_results.items():
                portfolio_analysis = scenario_result.get('portfolio_analysis', {})
                total_return = portfolio_analysis.get('total_return', {})
                max_loss = total_return.get('max_loss', 0)

                if abs(max_loss) > 0.3:  # More than 30% loss
                    alerts.append({
                        'type': 'scenario_vulnerability',
                        'severity': 'high',
                        'message': f'Severe vulnerability to {scenario_name} scenario ({max_loss:.1%} potential loss)',
                        'recommendation': 'Consider scenario-specific hedging strategies'
                    })

        return alerts[:5]  # Return top 5 alerts

    def _extract_risk_highlights(self) -> Dict[str, Any]:
        """Extract key risk metrics for executive summary."""
        result = self.risk_analysis_result
        highlights = {}

        if result.risk_metrics:
            rm = result.risk_metrics
            highlights.update({
                'value_at_risk_95': f"{rm.var_1day_95:.2%}" if rm.var_1day_95 else "N/A",
                'annual_volatility': f"{rm.annual_volatility:.2%}" if rm.annual_volatility else "N/A",
                'max_drawdown': f"{rm.max_drawdown:.2%}" if rm.max_drawdown else "N/A",
                'sharpe_ratio': f"{rm.sharpe_ratio:.2f}" if rm.sharpe_ratio else "N/A"
            })

        return highlights

    def _summarize_scenario_impacts(self) -> Dict[str, Any]:
        """Summarize scenario analysis impacts."""
        result = self.risk_analysis_result

        if not result.scenario_results:
            return {'message': 'No scenario analysis available'}

        scenario_summary = {}
        worst_case = {'scenario': '', 'loss': 0}
        best_case = {'scenario': '', 'gain': 0}

        for scenario_name, scenario_result in result.scenario_results.items():
            portfolio_analysis = scenario_result.get('portfolio_analysis', {})
            total_return = portfolio_analysis.get('total_return', {})

            mean_return = total_return.get('mean', 0)
            max_loss = total_return.get('max_loss', 0)

            scenario_summary[scenario_name] = {
                'expected_impact': f"{mean_return:.2%}",
                'worst_case': f"{max_loss:.2%}",
                'probability': scenario_result.get('scenario_probability', 'N/A')
            }

            if abs(max_loss) > abs(worst_case['loss']):
                worst_case = {'scenario': scenario_name, 'loss': max_loss}

            if mean_return > best_case['gain']:
                best_case = {'scenario': scenario_name, 'gain': mean_return}

        return {
            'scenario_details': scenario_summary,
            'worst_case_scenario': worst_case,
            'best_case_scenario': best_case,
            'scenarios_analyzed': len(result.scenario_results)
        }

    def _generate_quick_recommendations(self) -> List[str]:
        """Generate quick actionable recommendations."""
        recommendations = []
        result = self.risk_analysis_result

        # Risk score based recommendations
        if result.overall_risk_score:
            if result.overall_risk_score > 75:
                recommendations.append("Immediate risk reduction required - consider position sizing and hedging")
            elif result.overall_risk_score > 50:
                recommendations.append("Monitor risk levels closely and prepare contingency plans")
            else:
                recommendations.append("Risk levels appear manageable, maintain current monitoring")

        # Correlation based recommendations
        if result.correlation_matrices:
            for method, corr_matrix in result.correlation_matrices.items():
                avg_corr = abs(corr_matrix.market_concentration())
                if avg_corr > 0.7:
                    recommendations.append("High correlations detected - enhance diversification strategy")
                    break

        # Factor concentration recommendations
        if result.risk_factors and result.risk_factors.identified_factors:
            if len(result.risk_factors.identified_factors) <= 2:
                recommendations.append("Risk concentrated in few factors - consider broader exposure")

        return recommendations[:3]  # Top 3 recommendations

    def export_to_json(self, file_path: str) -> None:
        """Export report to JSON format."""
        report_data = {
            'report_metadata': {
                'report_id': self.report_id,
                'generation_time': self.generation_time.isoformat(),
                'report_version': self.report_version
            },
            'analysis_request': {
                'request_id': self.analysis_request.request_id,
                'analysis_scope': self.analysis_request.analysis_scope.value,
                'risk_types': [rt.value for rt in self.analysis_request.risk_types],
                'confidence_levels': self.analysis_request.confidence_levels,
                'time_horizons': self.analysis_request.time_horizons
            },
            'executive_summary': self.executive_summary,
            'risk_analysis_result': self.risk_analysis_result.to_dict(),
            'detailed_sections': {
                'risk_metrics_summary': self.risk_metrics_summary,
                'distribution_analysis': self.distribution_analysis,
                'correlation_analysis': self.correlation_analysis,
                'scenario_analysis': self.scenario_analysis,
                'sensitivity_analysis': self.sensitivity_analysis,
                'factor_analysis': self.factor_analysis,
                'recommendations': self.recommendations
            }
        }

        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Risk report exported to JSON: {file_path}")

    def export_to_excel(self, file_path: str) -> None:
        """Export report to Excel format with multiple sheets."""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Executive Summary sheet
                if self.executive_summary:
                    exec_summary_df = self._flatten_dict_to_dataframe(
                        self.executive_summary, 'Executive Summary'
                    )
                    exec_summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)

                # Risk Metrics sheet
                if self.risk_analysis_result.risk_metrics:
                    risk_metrics_df = pd.DataFrame([self.risk_analysis_result.risk_metrics.to_dict()])
                    risk_metrics_df.to_excel(writer, sheet_name='Risk Metrics', index=False)

                # Correlation Analysis sheet
                if self.risk_analysis_result.correlation_matrices:
                    corr_data = []
                    for method, corr_matrix in self.risk_analysis_result.correlation_matrices.items():
                        corr_df = corr_matrix.to_dataframe()
                        corr_df.to_excel(writer, sheet_name=f'Correlation_{method}')

                # Scenario Analysis sheet
                if self.risk_analysis_result.scenario_results:
                    scenario_df = pd.DataFrame(self.risk_analysis_result.scenario_results).T
                    scenario_df.to_excel(writer, sheet_name='Scenario Analysis')

                # Monte Carlo Results sheet
                if self.risk_analysis_result.monte_carlo_results:
                    mc_summary = []
                    for analysis_type, mc_result in self.risk_analysis_result.monte_carlo_results.items():
                        if hasattr(mc_result, 'statistics'):
                            mc_summary.append({
                                'analysis_type': analysis_type,
                                **mc_result.statistics
                            })

                    if mc_summary:
                        mc_df = pd.DataFrame(mc_summary)
                        mc_df.to_excel(writer, sheet_name='Monte Carlo Results', index=False)

            logger.info(f"Risk report exported to Excel: {file_path}")

        except Exception as e:
            logger.error(f"Failed to export Excel report: {e}")
            raise

    def _flatten_dict_to_dataframe(self, data_dict: Dict[str, Any], section_name: str) -> pd.DataFrame:
        """Flatten nested dictionary to DataFrame for Excel export."""
        flattened_data = []

        def flatten_recursive(obj, parent_key='', sep='_'):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{sep}{key}" if parent_key else key
                    if isinstance(value, (dict, list)):
                        flatten_recursive(value, new_key, sep)
                    else:
                        flattened_data.append({
                            'Section': section_name,
                            'Metric': new_key,
                            'Value': str(value)
                        })
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else f"item_{i}"
                    flatten_recursive(item, new_key, sep)

        flatten_recursive(data_dict)
        return pd.DataFrame(flattened_data)


class IntegratedRiskEngine:
    """
    Comprehensive integrated risk analysis engine that coordinates all risk
    analysis components to provide unified, sophisticated risk assessment capabilities.
    """

    def __init__(
        self,
        financial_calculator=None,
        config: Optional[RiskAnalysisConfig] = None
    ):
        """
        Initialize integrated risk engine with all components.

        Args:
            financial_calculator: FinancialCalculator instance for data access
            config: Risk analysis configuration
        """
        self.financial_calculator = financial_calculator
        self.config = config or RiskAnalysisConfig()

        # Initialize component frameworks
        self.risk_framework = RiskAnalysisFramework(financial_calculator, config)
        self.correlation_analyzer = CorrelationAnalyzer()
        self.scenario_framework = ScenarioModelingFramework()
        self.monte_carlo_engine = MonteCarloEngine(financial_calculator) if financial_calculator else None
        self.distribution_fitter = DistributionFitter()
        self.sensitivity_analyzer = SensitivityAnalyzer(financial_calculator) if financial_calculator else None
        self.alerting_system = AlertingSystem()

        # Analysis cache and state management
        self.analysis_cache: Dict[str, RiskAnalysisResult] = {}
        self.report_cache: Dict[str, ComprehensiveRiskReport] = {}
        self.active_alerts: List[Alert] = []

        logger.info("Integrated Risk Engine initialized with all components")

    def analyze_risk(self, request: RiskAnalysisRequest) -> RiskAnalysisResult:
        """
        Execute comprehensive risk analysis based on request specification.

        Args:
            request: Risk analysis request with all parameters

        Returns:
            Comprehensive risk analysis result
        """
        start_time = datetime.now()
        logger.info(f"Starting comprehensive risk analysis: {request.request_id}")

        # Validate request
        self._validate_request(request)

        try:
            # Prepare data for analysis
            returns_data = self._prepare_analysis_data(request)

            if returns_data is None or returns_data.empty:
                logger.warning("No data available for risk analysis")
                return self._create_empty_result(request)

            # Execute core risk framework analysis
            result = self.risk_framework.comprehensive_risk_analysis(
                asset_id=request.asset_ids[0] if request.asset_ids else None,
                returns_data=returns_data,
                analysis_id=request.request_id
            )

            # Enhance with additional analysis dimensions
            result = self._enhance_with_distribution_analysis(result, returns_data, request)
            result = self._enhance_with_correlation_analysis(result, returns_data, request)
            result = self._enhance_with_scenario_analysis(result, returns_data, request)
            result = self._enhance_with_sensitivity_analysis(result, request)
            result = self._enhance_with_factor_analysis(result, returns_data, request)

            # Perform advanced analysis if requested
            if request.tail_analysis:
                result = self._enhance_with_tail_analysis(result, returns_data)

            if request.copula_modeling and len(returns_data.columns) > 1:
                result = self._enhance_with_copula_modeling(result, returns_data)

            # Update overall risk assessment with enhanced analysis
            result.overall_risk_score = self._recalculate_comprehensive_risk_score(result)
            result.risk_level = RiskLevel.from_percentile(result.overall_risk_score)
            result.key_risk_drivers = self._identify_comprehensive_risk_drivers(result)

            # Cache result
            self.analysis_cache[request.request_id] = result

            # Check for alerts
            self._evaluate_risk_alerts(result, request)

            end_time = datetime.now()
            result.calculation_time = (end_time - start_time).total_seconds()

            logger.info(f"Risk analysis completed in {result.calculation_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            raise

    def generate_comprehensive_report(self, analysis_id: str) -> ComprehensiveRiskReport:
        """
        Generate comprehensive risk report from analysis result.

        Args:
            analysis_id: Analysis ID to generate report for

        Returns:
            Comprehensive risk report
        """
        logger.info(f"Generating comprehensive risk report for analysis: {analysis_id}")

        # Get analysis result
        result = self.analysis_cache.get(analysis_id)
        if not result:
            raise ValueError(f"Analysis result not found: {analysis_id}")

        # Create report
        report_id = f"report_{analysis_id}"

        # Find corresponding request (simplified lookup)
        request = RiskAnalysisRequest(request_id=analysis_id)  # Placeholder

        report = ComprehensiveRiskReport(
            report_id=report_id,
            analysis_request=request,
            risk_analysis_result=result
        )

        # Generate all report sections
        report.generate_executive_summary()
        report.risk_metrics_summary = self._generate_risk_metrics_section(result)
        report.distribution_analysis = self._generate_distribution_section(result)
        report.correlation_analysis = self._generate_correlation_section(result)
        report.scenario_analysis = self._generate_scenario_section(result)
        report.sensitivity_analysis = self._generate_sensitivity_section(result)
        report.factor_analysis = self._generate_factor_section(result)
        report.recommendations = self._generate_recommendations_section(result)

        # Cache report
        self.report_cache[report_id] = report

        logger.info(f"Comprehensive risk report generated: {report_id}")
        return report

    def _prepare_analysis_data(self, request: RiskAnalysisRequest) -> Optional[pd.DataFrame]:
        """Prepare returns data for analysis."""
        if not self.financial_calculator:
            logger.warning("No financial calculator available for data preparation")
            return None

        # This would integrate with the financial calculator to get returns data
        # For now, return placeholder
        return None

    def _enhance_with_distribution_analysis(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResult:
        """Enhance analysis with distribution fitting and modeling."""
        if not request.fit_distributions:
            return result

        logger.debug("Enhancing analysis with distribution modeling")

        try:
            fitted_distributions = {}

            for column in returns_data.columns:
                series_data = returns_data[column].dropna()

                if len(series_data) < 30:
                    continue

                # Fit best distribution
                best_dist = self.distribution_fitter.fit_best_distribution(
                    series_data,
                    distributions=request.distribution_types
                )

                fitted_distributions[column] = {
                    'distribution_type': best_dist.distribution_type.value,
                    'parameters': best_dist.parameters.parameters,
                    'moments': {
                        'mean': best_dist.mean(),
                        'std': best_dist.std(),
                        'skewness': best_dist.skewness(),
                        'kurtosis': best_dist.kurtosis()
                    },
                    'tail_behavior': best_dist.tail_behavior().value,
                    'var_estimates': {
                        f'var_{int(cl*100)}': best_dist.var(1-cl)
                        for cl in request.confidence_levels
                    }
                }

            # Store distribution analysis in result
            if not hasattr(result, 'distribution_analysis'):
                result.distribution_analysis = {}

            result.distribution_analysis['fitted_distributions'] = fitted_distributions
            result.distribution_analysis['fitting_summary'] = {
                'assets_fitted': len(fitted_distributions),
                'fitting_method': 'automatic_selection',
                'distribution_comparison': self.distribution_fitter.get_distribution_comparison().to_dict()
            }

        except Exception as e:
            logger.warning(f"Distribution analysis failed: {e}")
            result.warnings.append(f"Distribution analysis failed: {str(e)}")

        return result

    def _enhance_with_correlation_analysis(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResult:
        """Enhance analysis with advanced correlation analysis."""
        if len(returns_data.columns) <= 1:
            return result

        logger.debug("Enhancing analysis with correlation analysis")

        try:
            self.correlation_analyzer.returns_data = returns_data

            # Calculate correlation matrices for requested methods
            for method in request.correlation_methods:
                corr_matrix = self.correlation_analyzer.calculate_correlation_matrix(
                    method=method,
                    min_periods=self.config.min_periods
                )
                result.correlation_matrices[method.value] = corr_matrix

            # Rolling correlation analysis if requested
            if request.rolling_correlation:
                stability_analysis = self.correlation_analyzer.rolling_correlation_analysis(
                    window=request.correlation_window
                )
                result.correlation_stability = stability_analysis

            # Factor analysis if requested
            if request.factor_analysis:
                risk_factors = self.correlation_analyzer.identify_risk_factors(
                    method=request.factor_method,
                    n_factors=request.max_factors
                )
                result.risk_factors = risk_factors

        except Exception as e:
            logger.warning(f"Correlation analysis enhancement failed: {e}")
            result.warnings.append(f"Correlation analysis failed: {str(e)}")

        return result

    def _enhance_with_scenario_analysis(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResult:
        """Enhance analysis with scenario modeling."""
        if not request.include_scenarios:
            return result

        logger.debug("Enhancing analysis with scenario analysis")

        try:
            # Determine scenarios to analyze
            scenario_names = request.scenario_names or self.scenario_framework.list_scenarios()[:5]

            # Add custom scenarios if provided
            if request.custom_scenarios:
                for custom_scenario in request.custom_scenarios:
                    self.scenario_framework.add_scenario(custom_scenario)
                    scenario_names.append(custom_scenario.name)

            # Run scenario analysis
            scenario_results = self.scenario_framework.run_scenario_analysis(
                scenario_names=scenario_names,
                portfolio_data=self._extract_portfolio_data(returns_data),
                monte_carlo_runs=min(request.monte_carlo_runs, 5000)  # Limit for performance
            )

            result.scenario_results.update(scenario_results)

        except Exception as e:
            logger.warning(f"Scenario analysis enhancement failed: {e}")
            result.warnings.append(f"Scenario analysis failed: {str(e)}")

        return result

    def _enhance_with_sensitivity_analysis(
        self,
        result: RiskAnalysisResult,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResult:
        """Enhance analysis with sensitivity analysis."""
        if not request.sensitivity_analysis or not self.sensitivity_analyzer:
            return result

        logger.debug("Enhancing analysis with sensitivity analysis")

        try:
            # Define sensitivity parameters if not provided
            if not request.sensitivity_parameters:
                sensitivity_params = {
                    'discount_rate': {'base': 0.10, 'range': (0.06, 0.15), 'steps': 11},
                    'revenue_growth': {'base': 0.05, 'range': (-0.05, 0.15), 'steps': 11},
                    'terminal_growth': {'base': 0.03, 'range': (0.01, 0.05), 'steps': 11}
                }
            else:
                sensitivity_params = request.sensitivity_parameters

            # Run sensitivity analysis
            sensitivity_result = self.sensitivity_analyzer.one_way_sensitivity(
                'dcf', sensitivity_params
            )

            # Store sensitivity results
            if not hasattr(result, 'sensitivity_results'):
                result.sensitivity_results = {}

            result.sensitivity_results['one_way_analysis'] = {
                'most_sensitive_parameter': sensitivity_result.get_most_sensitive_parameter(),
                'sensitivity_rankings': sensitivity_result.parameter_rankings,
                'elasticity_analysis': sensitivity_result.elasticities
            }

        except Exception as e:
            logger.warning(f"Sensitivity analysis enhancement failed: {e}")
            result.warnings.append(f"Sensitivity analysis failed: {str(e)}")

        return result

    def _enhance_with_factor_analysis(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResult:
        """Enhance analysis with factor analysis (if not already done in correlation)."""
        if not request.factor_analysis or result.risk_factors is not None:
            return result  # Already done in correlation analysis

        logger.debug("Enhancing analysis with factor analysis")

        try:
            from .correlation_analysis import RiskFactorIdentifier

            risk_factors = RiskFactorIdentifier(
                returns_data=returns_data,
                factor_method=request.factor_method
            )

            risk_factors.identify_factors(request.max_factors)
            result.risk_factors = risk_factors

        except Exception as e:
            logger.warning(f"Factor analysis enhancement failed: {e}")
            result.warnings.append(f"Factor analysis failed: {str(e)}")

        return result

    def _enhance_with_tail_analysis(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame
    ) -> RiskAnalysisResult:
        """Enhance analysis with tail risk analysis."""
        logger.debug("Enhancing analysis with tail risk analysis")

        try:
            tail_analysis = {}

            for column in returns_data.columns:
                series_data = returns_data[column].dropna()

                if len(series_data) < 50:
                    continue

                # Extreme value analysis
                from scipy.stats import genextreme

                # Fit extreme value distribution to tail
                threshold = np.percentile(series_data, 5)  # Lower 5% tail
                tail_data = series_data[series_data <= threshold]

                if len(tail_data) > 10:
                    c, loc, scale = genextreme.fit(tail_data)

                    tail_analysis[column] = {
                        'tail_index': c,
                        'tail_location': loc,
                        'tail_scale': scale,
                        'extreme_var_99_9': genextreme.ppf(0.001, c, loc, scale),
                        'tail_observations': len(tail_data)
                    }

            if not hasattr(result, 'tail_analysis'):
                result.tail_analysis = {}

            result.tail_analysis = tail_analysis

        except Exception as e:
            logger.warning(f"Tail analysis enhancement failed: {e}")
            result.warnings.append(f"Tail analysis failed: {str(e)}")

        return result

    def _enhance_with_copula_modeling(
        self,
        result: RiskAnalysisResult,
        returns_data: pd.DataFrame
    ) -> RiskAnalysisResult:
        """Enhance analysis with copula modeling."""
        logger.debug("Enhancing analysis with copula modeling")

        try:
            copula_model = CopulaModel()
            copula_model.fit(returns_data)

            # Generate samples for risk assessment
            copula_samples = copula_model.sample(1000)

            # Calculate tail dependence
            tail_dependence = copula_model.tail_dependence()

            if not hasattr(result, 'copula_analysis'):
                result.copula_analysis = {}

            result.copula_analysis = {
                'copula_type': copula_model.copula_type,
                'tail_dependence': tail_dependence,
                'marginal_distributions': {
                    var: dist.distribution_type.value
                    for var, dist in copula_model.marginal_distributions.items()
                },
                'dependency_structure': copula_model.dependency_parameters
            }

        except Exception as e:
            logger.warning(f"Copula modeling enhancement failed: {e}")
            result.warnings.append(f"Copula modeling failed: {str(e)}")

        return result

    def _recalculate_comprehensive_risk_score(self, result: RiskAnalysisResult) -> float:
        """Recalculate overall risk score with all analysis dimensions."""
        risk_components = []

        # Base risk framework score (40% weight)
        if hasattr(result, 'overall_risk_score') and result.overall_risk_score:
            risk_components.append(('base_framework', result.overall_risk_score, 0.40))

        # Distribution analysis component (15% weight)
        if hasattr(result, 'distribution_analysis'):
            dist_analysis = result.distribution_analysis.get('fitted_distributions', {})
            if dist_analysis:
                # Average tail risk across assets
                tail_risk_scores = []
                for asset, dist_info in dist_analysis.items():
                    tail_behavior = dist_info.get('tail_behavior', 'light')
                    if tail_behavior == 'heavy':
                        tail_risk_scores.append(80)
                    elif tail_behavior == 'fat':
                        tail_risk_scores.append(60)
                    else:
                        tail_risk_scores.append(40)

                if tail_risk_scores:
                    avg_tail_risk = np.mean(tail_risk_scores)
                    risk_components.append(('distribution_risk', avg_tail_risk, 0.15))

        # Enhanced correlation component (20% weight)
        if result.correlation_matrices and result.correlation_stability:
            correlation_volatility = result.correlation_stability.get('correlation_volatility', 0)
            correlation_risk = min(correlation_volatility * 1000, 100)  # Scale to 0-100
            risk_components.append(('correlation_instability', correlation_risk, 0.20))

        # Tail analysis component (15% weight)
        if hasattr(result, 'tail_analysis'):
            tail_indices = []
            for asset, tail_info in result.tail_analysis.items():
                tail_index = abs(tail_info.get('tail_index', 0))
                tail_indices.append(min(tail_index * 50, 100))  # Scale to 0-100

            if tail_indices:
                avg_tail_index = np.mean(tail_indices)
                risk_components.append(('tail_risk', avg_tail_index, 0.15))

        # Copula dependency component (10% weight)
        if hasattr(result, 'copula_analysis'):
            copula_info = result.copula_analysis
            tail_dep = copula_info.get('tail_dependence', {})
            avg_tail_dep = (tail_dep.get('lower_tail', 0) + tail_dep.get('upper_tail', 0)) / 2
            tail_dep_risk = avg_tail_dep * 100
            risk_components.append(('tail_dependence', tail_dep_risk, 0.10))

        if not risk_components:
            return 50.0  # Default moderate risk

        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in risk_components)
        total_weight = sum(weight for _, _, weight in risk_components)

        return total_score / total_weight if total_weight > 0 else 50.0

    def _identify_comprehensive_risk_drivers(self, result: RiskAnalysisResult) -> List[str]:
        """Identify comprehensive risk drivers from enhanced analysis."""
        drivers = []

        # Add base framework drivers
        if hasattr(result, 'key_risk_drivers'):
            drivers.extend(result.key_risk_drivers[:2])

        # Add distribution-based drivers
        if hasattr(result, 'distribution_analysis'):
            dist_analysis = result.distribution_analysis.get('fitted_distributions', {})
            heavy_tail_assets = [
                asset for asset, info in dist_analysis.items()
                if info.get('tail_behavior') in ['heavy', 'extreme']
            ]
            if heavy_tail_assets:
                drivers.append(f"Heavy tail distributions ({len(heavy_tail_assets)} assets)")

        # Add correlation instability drivers
        if result.correlation_stability:
            correlation_volatility = result.correlation_stability.get('correlation_volatility', 0)
            if correlation_volatility > 0.1:
                drivers.append("Correlation instability")

        # Add tail dependence drivers
        if hasattr(result, 'copula_analysis'):
            tail_dep = result.copula_analysis.get('tail_dependence', {})
            avg_tail_dep = (tail_dep.get('lower_tail', 0) + tail_dep.get('upper_tail', 0)) / 2
            if avg_tail_dep > 0.3:
                drivers.append("High tail dependence")

        return drivers[:5]  # Return top 5 drivers

    def _validate_request(self, request: RiskAnalysisRequest) -> None:
        """Validate risk analysis request."""
        if not request.asset_ids and not request.portfolio_id:
            raise ValueError("Either asset_ids or portfolio_id must be specified")

    def _create_empty_result(self, request: RiskAnalysisRequest) -> RiskAnalysisResult:
        """Create empty risk analysis result when no data is available."""
        return RiskAnalysisResult(
            analysis_id=request.request_id,
            warnings=["No data available for risk analysis"]
        )

    def _extract_portfolio_data(self, returns_data: pd.DataFrame) -> Dict[str, float]:
        """Extract portfolio data for scenario analysis."""
        # Simplified portfolio data extraction
        return {
            'equity_weight': 0.6,  # Placeholder
            'bond_weight': 0.4,    # Placeholder
            'base_volatility': returns_data.std().mean() if not returns_data.empty else 0.15
        }

    def _evaluate_risk_alerts(self, result: RiskAnalysisResult, request: RiskAnalysisRequest) -> None:
        """Evaluate risk analysis results for alert conditions."""
        try:
            # Check for extreme risk score
            if result.overall_risk_score and result.overall_risk_score > 80:
                alert = Alert(
                    condition_id="extreme_risk_score",
                    severity=AlertSeverity.HIGH,
                    message=f"Extreme risk score detected: {result.overall_risk_score:.1f}",
                    threshold=80.0,
                    current_value=result.overall_risk_score
                )
                self.alerting_system.evaluate_condition(alert, {"risk_score": result.overall_risk_score})

            # Check for high VaR
            if result.risk_metrics and result.risk_metrics.var_1day_95:
                var_95 = abs(result.risk_metrics.var_1day_95)
                if var_95 > 0.05:  # More than 5% daily VaR
                    alert = Alert(
                        condition_id="high_var_95",
                        severity=AlertSeverity.MEDIUM,
                        message=f"High VaR detected: {var_95:.2%}",
                        threshold=0.05,
                        current_value=var_95
                    )
                    self.alerting_system.evaluate_condition(alert, {"var_95": var_95})

        except Exception as e:
            logger.warning(f"Alert evaluation failed: {e}")

    # Report generation helper methods
    def _generate_risk_metrics_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate risk metrics section for report."""
        if not result.risk_metrics:
            return {'message': 'No risk metrics available'}

        return result.risk_metrics.to_dict()

    def _generate_distribution_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate distribution analysis section for report."""
        if not hasattr(result, 'distribution_analysis'):
            return {'message': 'No distribution analysis available'}

        return result.distribution_analysis

    def _generate_correlation_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate correlation analysis section for report."""
        section = {}

        if result.correlation_matrices:
            section['correlation_matrices'] = {
                method: {
                    'avg_correlation': matrix.market_concentration(),
                    'stability_score': matrix.stability_score,
                    'highly_correlated_pairs': matrix.identify_highly_correlated_pairs(0.7)
                }
                for method, matrix in result.correlation_matrices.items()
            }

        if result.correlation_stability:
            section['stability_analysis'] = result.correlation_stability

        return section if section else {'message': 'No correlation analysis available'}

    def _generate_scenario_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate scenario analysis section for report."""
        if not result.scenario_results:
            return {'message': 'No scenario analysis available'}

        return result.scenario_results

    def _generate_sensitivity_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate sensitivity analysis section for report."""
        if not hasattr(result, 'sensitivity_results'):
            return {'message': 'No sensitivity analysis available'}

        return result.sensitivity_results

    def _generate_factor_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate factor analysis section for report."""
        if not result.risk_factors:
            return {'message': 'No factor analysis available'}

        return {
            'identified_factors': {
                factor_type.value: factor_info
                for factor_type, factor_info in result.risk_factors.identified_factors.items()
            },
            'explained_variance': result.risk_factors.explained_variance.to_dict() if result.risk_factors.explained_variance is not None else {}
        }

    def _generate_recommendations_section(self, result: RiskAnalysisResult) -> Dict[str, Any]:
        """Generate recommendations section for report."""
        recommendations = {
            'immediate_actions': [],
            'medium_term_strategies': [],
            'long_term_considerations': [],
            'monitoring_priorities': []
        }

        # Generate recommendations based on analysis results
        if result.overall_risk_score:
            if result.overall_risk_score > 80:
                recommendations['immediate_actions'].append(
                    "Immediate risk reduction required - review position sizes and implement hedging"
                )
            elif result.overall_risk_score > 60:
                recommendations['medium_term_strategies'].append(
                    "Enhanced risk monitoring and contingency planning recommended"
                )

        # Add more specific recommendations based on analysis components
        if result.correlation_matrices:
            for method, matrix in result.correlation_matrices.items():
                if abs(matrix.market_concentration()) > 0.7:
                    recommendations['medium_term_strategies'].append(
                        "High correlations detected - consider diversification enhancement"
                    )

        if hasattr(result, 'distribution_analysis'):
            recommendations['monitoring_priorities'].append(
                "Monitor distribution changes and tail risk evolution"
            )

        return recommendations