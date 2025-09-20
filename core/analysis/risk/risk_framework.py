"""
Risk Analysis Framework
======================

This module provides the main risk analysis framework that integrates all risk
assessment capabilities including Monte Carlo simulation, correlation analysis,
scenario modeling, and comprehensive risk reporting.

The framework serves as the central coordinator for risk analysis operations,
providing a unified interface for risk assessment across portfolios and individual assets.

Key Features:
- Comprehensive risk analysis engine
- Integration with Monte Carlo simulation
- Portfolio and individual asset risk assessment
- Scenario analysis and stress testing
- Risk reporting and visualization
- Multi-source data integration
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
import logging
from datetime import datetime, date

# Import risk analysis components
from .risk_metrics import (
    RiskType, RiskMetrics, RiskLevel, AssetRiskProfile,
    PortfolioRiskMetrics, RiskFactorModel
)
from .correlation_analysis import (
    CorrelationAnalyzer, CorrelationMatrix, CorrelationMethod,
    RiskFactorIdentifier, RiskFactorType
)
from .scenario_modeling import (
    ScenarioModelingFramework, CustomScenario, ScenarioType,
    PredefinedScenarios
)

# Import existing framework components
from ..statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult
from ..portfolio.portfolio_models import Portfolio, PortfolioHolding

logger = logging.getLogger(__name__)


@dataclass
class RiskAnalysisConfig:
    """Configuration for risk analysis framework."""
    # Monte Carlo settings
    default_simulations: int = 10000
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99, 0.995])

    # Correlation analysis settings
    correlation_methods: List[CorrelationMethod] = field(default_factory=lambda: [
        CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN
    ])
    rolling_window: int = 252  # 1 year of daily data
    min_periods: int = 30

    # Risk factor settings
    max_risk_factors: int = 10
    factor_method: str = 'pca'

    # Scenario analysis settings
    include_predefined_scenarios: bool = True
    scenario_monte_carlo_runs: int = 1000

    # Reporting settings
    currency: str = "USD"
    report_format: str = "comprehensive"  # 'summary', 'detailed', 'comprehensive'


@dataclass
class RiskAnalysisResult:
    """
    Comprehensive risk analysis results.

    Contains all risk analysis outputs including metrics, scenario results,
    correlation analysis, and risk factor identification.
    """
    analysis_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Asset/Portfolio identification
    asset_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    analysis_type: str = "comprehensive"  # 'asset', 'portfolio', 'comprehensive'

    # Core risk metrics
    risk_metrics: Optional[RiskMetrics] = None
    asset_risk_profile: Optional[AssetRiskProfile] = None
    portfolio_risk_metrics: Optional[PortfolioRiskMetrics] = None

    # Monte Carlo results
    monte_carlo_results: Dict[str, SimulationResult] = field(default_factory=dict)

    # Correlation analysis
    correlation_matrices: Dict[str, CorrelationMatrix] = field(default_factory=dict)
    correlation_stability: Optional[Dict[str, Any]] = None

    # Risk factor analysis
    risk_factors: Optional[RiskFactorIdentifier] = None
    factor_model: Optional[RiskFactorModel] = None

    # Scenario analysis
    scenario_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    stress_test_results: Dict[str, Any] = field(default_factory=dict)

    # Risk attribution
    risk_attribution: Dict[str, float] = field(default_factory=dict)
    marginal_risk_contributions: Dict[str, float] = field(default_factory=dict)

    # Summary metrics
    overall_risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    key_risk_drivers: List[str] = field(default_factory=list)

    # Metadata
    config_used: Optional[RiskAnalysisConfig] = None
    calculation_time: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def summary_table(self) -> pd.DataFrame:
        """Generate summary table of key risk metrics."""
        summary_data = []

        if self.risk_metrics:
            summary_data.append({
                'Metric': 'Value at Risk (95%)',
                'Value': self.risk_metrics.var_1day_95,
                'Unit': '%'
            })
            summary_data.append({
                'Metric': 'Annual Volatility',
                'Value': self.risk_metrics.annual_volatility,
                'Unit': '%'
            })
            summary_data.append({
                'Metric': 'Maximum Drawdown',
                'Value': self.risk_metrics.max_drawdown,
                'Unit': '%'
            })
            summary_data.append({
                'Metric': 'Sharpe Ratio',
                'Value': self.risk_metrics.sharpe_ratio,
                'Unit': 'Ratio'
            })

        if self.overall_risk_score:
            summary_data.append({
                'Metric': 'Overall Risk Score',
                'Value': self.overall_risk_score,
                'Unit': 'Score (0-100)'
            })

        return pd.DataFrame(summary_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary for serialization."""
        return {
            'analysis_id': self.analysis_id,
            'analysis_date': self.analysis_date.isoformat(),
            'asset_id': self.asset_id,
            'portfolio_id': self.portfolio_id,
            'analysis_type': self.analysis_type,
            'risk_metrics': self.risk_metrics.to_dict() if self.risk_metrics else None,
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.level_name if self.risk_level else None,
            'key_risk_drivers': self.key_risk_drivers,
            'scenario_results': self.scenario_results,
            'calculation_time': self.calculation_time,
            'warnings': self.warnings
        }


class RiskAnalysisFramework:
    """
    Comprehensive risk analysis framework for financial risk assessment.

    This is the main class that coordinates all risk analysis operations,
    providing a unified interface for comprehensive risk assessment of
    portfolios and individual financial assets.
    """

    def __init__(
        self,
        financial_calculator=None,
        config: Optional[RiskAnalysisConfig] = None
    ):
        """
        Initialize risk analysis framework.

        Args:
            financial_calculator: FinancialCalculator instance for data access
            config: Risk analysis configuration
        """
        self.financial_calculator = financial_calculator
        self.config = config or RiskAnalysisConfig()

        # Initialize component frameworks
        self.monte_carlo_engine = MonteCarloEngine(financial_calculator)
        self.correlation_analyzer = CorrelationAnalyzer()
        self.scenario_framework = ScenarioModelingFramework()

        # Analysis cache
        self.analysis_cache: Dict[str, RiskAnalysisResult] = {}

        logger.info("Risk Analysis Framework initialized")

    def comprehensive_risk_analysis(
        self,
        asset_id: Optional[str] = None,
        portfolio: Optional[Portfolio] = None,
        returns_data: Optional[pd.DataFrame] = None,
        analysis_id: Optional[str] = None
    ) -> RiskAnalysisResult:
        """
        Perform comprehensive risk analysis for asset or portfolio.

        Args:
            asset_id: Asset identifier for individual asset analysis
            portfolio: Portfolio object for portfolio analysis
            returns_data: Historical returns data
            analysis_id: Unique identifier for this analysis

        Returns:
            RiskAnalysisResult with comprehensive risk assessment
        """
        start_time = datetime.now()

        if analysis_id is None:
            analysis_id = f"risk_analysis_{start_time.strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting comprehensive risk analysis: {analysis_id}")

        # Initialize result object
        result = RiskAnalysisResult(
            analysis_id=analysis_id,
            asset_id=asset_id,
            portfolio_id=portfolio.portfolio_id if portfolio else None,
            analysis_type="portfolio" if portfolio else "asset",
            config_used=self.config
        )

        try:
            # Step 1: Prepare data
            if returns_data is None:
                returns_data = self._prepare_returns_data(asset_id, portfolio)

            if returns_data is None or returns_data.empty:
                result.warnings.append("No returns data available for analysis")
                return result

            # Step 2: Basic risk metrics calculation
            result.risk_metrics = self._calculate_basic_risk_metrics(returns_data)

            # Step 3: Monte Carlo simulation
            if self.financial_calculator or portfolio:
                result.monte_carlo_results = self._run_monte_carlo_analysis(
                    asset_id, portfolio, returns_data
                )

            # Step 4: Correlation analysis
            if len(returns_data.columns) > 1:
                result.correlation_matrices, result.correlation_stability = self._analyze_correlations(
                    returns_data
                )

                # Step 5: Risk factor identification
                result.risk_factors = self._identify_risk_factors(returns_data)

            # Step 6: Scenario analysis
            result.scenario_results = self._run_scenario_analysis(asset_id, portfolio, returns_data)

            # Step 7: Risk attribution (for portfolios)
            if portfolio:
                result.risk_attribution, result.marginal_risk_contributions = self._calculate_risk_attribution(
                    portfolio, returns_data
                )

            # Step 8: Calculate overall risk assessment
            result.overall_risk_score = self._calculate_overall_risk_score(result)
            result.risk_level = RiskLevel.from_percentile(result.overall_risk_score)
            result.key_risk_drivers = self._identify_key_risk_drivers(result)

            # Cache result
            self.analysis_cache[analysis_id] = result

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            result.warnings.append(f"Analysis failed: {str(e)}")

        finally:
            end_time = datetime.now()
            result.calculation_time = (end_time - start_time).total_seconds()

        logger.info(f"Risk analysis completed in {result.calculation_time:.2f} seconds")
        return result

    def _prepare_returns_data(
        self,
        asset_id: Optional[str],
        portfolio: Optional[Portfolio]
    ) -> Optional[pd.DataFrame]:
        """Prepare returns data for analysis."""
        if portfolio:
            # Get returns for portfolio holdings
            # This would integrate with the portfolio framework
            return None  # Placeholder

        elif asset_id and self.financial_calculator:
            # Get individual asset returns
            # This would integrate with the financial calculator
            return None  # Placeholder

        return None

    def _calculate_basic_risk_metrics(self, returns_data: pd.DataFrame) -> RiskMetrics:
        """Calculate basic risk metrics from returns data."""
        logger.info("Calculating basic risk metrics")

        if returns_data.empty:
            return RiskMetrics()

        # Calculate for single asset or portfolio returns
        if len(returns_data.columns) == 1:
            returns = returns_data.iloc[:, 0].dropna()
        else:
            # Use equally weighted portfolio returns as default
            returns = returns_data.mean(axis=1).dropna()

        if len(returns) < 30:
            logger.warning("Insufficient data for risk metrics calculation")
            return RiskMetrics()

        # Calculate metrics
        annual_factor = 252  # Assume daily returns

        # Volatility metrics
        annual_volatility = returns.std() * np.sqrt(annual_factor)
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(annual_factor) if len(downside_returns) > 0 else 0
        upside_returns = returns[returns > 0]
        upside_volatility = upside_returns.std() * np.sqrt(annual_factor) if len(upside_returns) > 0 else 0

        # VaR calculations
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        var_995 = np.percentile(returns, 0.5)

        # CVaR calculations
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        cvar_99 = returns[returns <= var_99].mean() if len(returns[returns <= var_99]) > 0 else var_99

        # Drawdown calculation
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdowns.min()

        # Distribution metrics
        from scipy import stats
        skewness = stats.skew(returns.dropna())
        kurtosis = stats.kurtosis(returns.dropna())

        # Risk-adjusted returns
        excess_returns = returns - 0.02/252  # Assume 2% risk-free rate
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(annual_factor) if returns.std() > 0 else 0
        sortino_ratio = excess_returns.mean() / downside_volatility * np.sqrt(annual_factor) if downside_volatility > 0 else 0

        # Additional metrics
        tail_ratio = np.percentile(returns, 95) / np.percentile(returns, 5) if np.percentile(returns, 5) != 0 else 0
        probability_of_loss = len(returns[returns < 0]) / len(returns)

        return RiskMetrics(
            var_1day_95=var_95,
            var_1day_99=var_99,
            var_1day_995=var_995,
            cvar_1day_95=cvar_95,
            cvar_1day_99=cvar_99,
            annual_volatility=annual_volatility,
            downside_volatility=downside_volatility,
            upside_volatility=upside_volatility,
            max_drawdown=max_drawdown,
            skewness=skewness,
            kurtosis=kurtosis,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            tail_ratio=tail_ratio,
            probability_of_loss=probability_of_loss
        )

    def _run_monte_carlo_analysis(
        self,
        asset_id: Optional[str],
        portfolio: Optional[Portfolio],
        returns_data: pd.DataFrame
    ) -> Dict[str, SimulationResult]:
        """Run Monte Carlo simulations for risk analysis."""
        logger.info("Running Monte Carlo analysis")

        results = {}

        try:
            if self.financial_calculator:
                # DCF Monte Carlo
                dcf_result = self.monte_carlo_engine.simulate_dcf_valuation(
                    num_simulations=self.config.default_simulations
                )
                results['dcf_valuation'] = dcf_result

                # DDM Monte Carlo
                ddm_result = self.monte_carlo_engine.simulate_dividend_discount_model(
                    num_simulations=self.config.default_simulations
                )
                results['ddm_valuation'] = ddm_result

        except Exception as e:
            logger.warning(f"Monte Carlo simulation failed: {e}")

        return results

    def _analyze_correlations(
        self,
        returns_data: pd.DataFrame
    ) -> Tuple[Dict[str, CorrelationMatrix], Optional[Dict[str, Any]]]:
        """Analyze correlations between assets."""
        logger.info("Analyzing correlations")

        self.correlation_analyzer.returns_data = returns_data
        correlation_matrices = {}

        # Calculate correlation matrices using different methods
        for method in self.config.correlation_methods:
            try:
                corr_matrix = self.correlation_analyzer.calculate_correlation_matrix(
                    method=method,
                    min_periods=self.config.min_periods
                )
                correlation_matrices[method.value] = corr_matrix
            except Exception as e:
                logger.warning(f"Correlation calculation failed for {method.value}: {e}")

        # Rolling correlation analysis
        stability_analysis = None
        try:
            stability_analysis = self.correlation_analyzer.rolling_correlation_analysis(
                window=self.config.rolling_window
            )
        except Exception as e:
            logger.warning(f"Correlation stability analysis failed: {e}")

        return correlation_matrices, stability_analysis

    def _identify_risk_factors(self, returns_data: pd.DataFrame) -> Optional[RiskFactorIdentifier]:
        """Identify risk factors driving returns."""
        logger.info("Identifying risk factors")

        try:
            return self.correlation_analyzer.identify_risk_factors(
                method=self.config.factor_method,
                n_factors=min(self.config.max_risk_factors, len(returns_data.columns) // 2)
            )
        except Exception as e:
            logger.warning(f"Risk factor identification failed: {e}")
            return None

    def _run_scenario_analysis(
        self,
        asset_id: Optional[str],
        portfolio: Optional[Portfolio],
        returns_data: pd.DataFrame
    ) -> Dict[str, Dict[str, Any]]:
        """Run scenario analysis and stress testing."""
        logger.info("Running scenario analysis")

        if not self.config.include_predefined_scenarios:
            return {}

        # Get predefined scenarios
        scenario_names = self.scenario_framework.list_scenarios()

        # Prepare portfolio data for scenario analysis
        portfolio_data = {}
        if portfolio:
            # This would extract portfolio weights and characteristics
            portfolio_data = {
                'equity_weight': 0.6,  # Placeholder
                'bond_weight': 0.4,    # Placeholder
                'base_volatility': 0.15  # Placeholder
            }

        try:
            return self.scenario_framework.run_scenario_analysis(
                scenario_names=scenario_names[:5],  # Limit to top 5 scenarios
                portfolio_data=portfolio_data,
                monte_carlo_runs=self.config.scenario_monte_carlo_runs
            )
        except Exception as e:
            logger.warning(f"Scenario analysis failed: {e}")
            return {}

    def _calculate_risk_attribution(
        self,
        portfolio: Portfolio,
        returns_data: pd.DataFrame
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calculate risk attribution for portfolio holdings."""
        logger.info("Calculating risk attribution")

        # Placeholder implementation
        # In practice, this would use portfolio optimization techniques
        risk_attribution = {}
        marginal_contributions = {}

        if hasattr(portfolio, 'holdings'):
            equal_weight = 1.0 / len(portfolio.holdings)
            for holding in portfolio.holdings:
                risk_attribution[holding.asset_id] = equal_weight
                marginal_contributions[holding.asset_id] = equal_weight

        return risk_attribution, marginal_contributions

    def _calculate_overall_risk_score(self, result: RiskAnalysisResult) -> float:
        """Calculate overall risk score (0-100)."""
        risk_components = []

        # Volatility component (30% weight)
        if result.risk_metrics and result.risk_metrics.annual_volatility:
            vol_score = min(result.risk_metrics.annual_volatility * 100, 100)
            risk_components.append(('volatility', vol_score, 0.30))

        # VaR component (25% weight)
        if result.risk_metrics and result.risk_metrics.var_1day_95:
            var_score = min(abs(result.risk_metrics.var_1day_95) * 100, 100)
            risk_components.append(('var', var_score, 0.25))

        # Correlation component (20% weight)
        if result.correlation_matrices:
            # Use average correlation as risk indicator
            pearson_matrix = result.correlation_matrices.get('pearson')
            if pearson_matrix:
                avg_corr = pearson_matrix.market_concentration()
                corr_score = abs(avg_corr) * 100
                risk_components.append(('correlation', corr_score, 0.20))

        # Scenario component (15% weight)
        if result.scenario_results:
            # Use worst-case scenario impact
            max_loss = 0
            for scenario_result in result.scenario_results.values():
                portfolio_analysis = scenario_result.get('portfolio_analysis', {})
                total_return = portfolio_analysis.get('total_return', {})
                scenario_loss = abs(total_return.get('max_loss', 0))
                max_loss = max(max_loss, scenario_loss)

            scenario_score = min(max_loss * 100, 100)
            risk_components.append(('scenario', scenario_score, 0.15))

        # Drawdown component (10% weight)
        if result.risk_metrics and result.risk_metrics.max_drawdown:
            drawdown_score = min(abs(result.risk_metrics.max_drawdown) * 100, 100)
            risk_components.append(('drawdown', drawdown_score, 0.10))

        if not risk_components:
            return 50.0  # Default moderate risk

        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in risk_components)
        total_weight = sum(weight for _, _, weight in risk_components)

        return total_score / total_weight if total_weight > 0 else 50.0

    def _identify_key_risk_drivers(self, result: RiskAnalysisResult) -> List[str]:
        """Identify key risk drivers from analysis results."""
        drivers = []

        # High volatility
        if result.risk_metrics and result.risk_metrics.annual_volatility and result.risk_metrics.annual_volatility > 0.25:
            drivers.append("High Volatility")

        # Large downside risk
        if result.risk_metrics and result.risk_metrics.var_1day_95 and result.risk_metrics.var_1day_95 < -0.05:
            drivers.append("Significant Downside Risk")

        # High correlation
        if result.correlation_matrices:
            pearson_matrix = result.correlation_matrices.get('pearson')
            if pearson_matrix and pearson_matrix.market_concentration() > 0.7:
                drivers.append("High Asset Correlation")

        # Concentrated risk factors
        if result.risk_factors and result.risk_factors.identified_factors:
            if len(result.risk_factors.identified_factors) <= 3:
                drivers.append("Concentrated Risk Factors")

        # Scenario vulnerability
        if result.scenario_results:
            high_impact_scenarios = 0
            for scenario_result in result.scenario_results.values():
                portfolio_analysis = scenario_result.get('portfolio_analysis', {})
                total_return = portfolio_analysis.get('total_return', {})
                if total_return.get('max_loss', 0) < -0.2:  # More than 20% loss
                    high_impact_scenarios += 1

            if high_impact_scenarios > 2:
                drivers.append("Scenario Vulnerability")

        return drivers[:5]  # Return top 5 drivers

    def get_analysis_result(self, analysis_id: str) -> Optional[RiskAnalysisResult]:
        """Retrieve cached analysis result."""
        return self.analysis_cache.get(analysis_id)

    def list_analyses(self) -> List[str]:
        """List all cached analysis IDs."""
        return list(self.analysis_cache.keys())

    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self.analysis_cache.clear()
        logger.info("Analysis cache cleared")

    def export_analysis(self, analysis_id: str, file_path: str) -> None:
        """Export analysis result to file."""
        result = self.analysis_cache.get(analysis_id)
        if not result:
            raise ValueError(f"Analysis {analysis_id} not found")

        import json
        with open(file_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Analysis {analysis_id} exported to {file_path}")

    def generate_risk_report(
        self,
        analysis_id: str,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate formatted risk report."""
        result = self.analysis_cache.get(analysis_id)
        if not result:
            raise ValueError(f"Analysis {analysis_id} not found")

        report = {
            'executive_summary': {
                'analysis_id': result.analysis_id,
                'analysis_date': result.analysis_date.strftime('%Y-%m-%d %H:%M:%S'),
                'overall_risk_score': result.overall_risk_score,
                'risk_level': result.risk_level.level_name if result.risk_level else 'Unknown',
                'key_risk_drivers': result.key_risk_drivers
            }
        }

        if report_type in ['detailed', 'comprehensive']:
            report['detailed_metrics'] = result.risk_metrics.to_dict() if result.risk_metrics else {}

        if report_type == 'comprehensive':
            report['scenario_analysis'] = result.scenario_results
            report['correlation_analysis'] = {
                name: {
                    'stability_score': matrix.stability_score,
                    'market_concentration': matrix.market_concentration()
                }
                for name, matrix in result.correlation_matrices.items()
            }

        return report