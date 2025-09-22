"""
Comprehensive Risk Analysis Framework
====================================

This package provides a complete risk analysis framework for financial analysis,
integrating multiple risk types, statistical models, and advanced analysis techniques.

Key Components:
- Risk framework and metrics
- Probability distribution modeling
- Correlation analysis and factor identification
- Scenario modeling and stress testing
- Sensitivity analysis
- Multiple risk types (market, credit, operational, liquidity)
- Integrated risk analysis engine
- Comprehensive reporting

Quick Start:
-----------
>>> from core.analysis.risk import IntegratedRiskEngine, RiskAnalysisRequest
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize components
>>> calc = FinancialCalculator('AAPL')
>>> risk_engine = IntegratedRiskEngine(calc)
>>>
>>> # Create analysis request
>>> request = RiskAnalysisRequest(
>>>     asset_ids=['AAPL'],
>>>     analysis_scope=AnalysisScope.COMPREHENSIVE,
>>>     risk_types=[RiskType.MARKET, RiskType.CREDIT]
>>> )
>>>
>>> # Perform analysis
>>> result = risk_engine.analyze_risk(request)
>>> print(f"Overall risk score: {result.overall_risk_score}")
>>>
>>> # Generate report
>>> report = risk_engine.generate_comprehensive_report(result.analysis_id)
>>> report.export_to_excel('risk_report.xlsx')
"""

# Core risk framework components
from .risk_framework import (
    RiskAnalysisFramework,
    RiskAnalysisResult,
    RiskAnalysisConfig
)

from .risk_metrics import (
    RiskType,
    RiskLevel,
    RiskMetrics,
    AssetRiskProfile,
    PortfolioRiskMetrics,
    RiskFactorModel
)

# Statistical and probability components
from .probability_distributions import (
    DistributionType,
    ProbabilityDistribution,
    NormalDistribution,
    StudentTDistribution,
    LogNormalDistribution,
    DistributionFitter,
    CopulaModel,
    TailBehavior
)

# Correlation and factor analysis
from .correlation_analysis import (
    CorrelationAnalyzer,
    CorrelationMatrix,
    CorrelationMethod,
    RiskFactorIdentifier,
    RiskFactorType
)

# Scenario modeling
from .scenario_modeling import (
    ScenarioModelingFramework,
    CustomScenario,
    ScenarioType,
    ScenarioSeverity,
    ScenarioParameter,
    PredefinedScenarios
)

# Sensitivity analysis
from .sensitivity_analysis import (
    SensitivityAnalyzer,
    SensitivityResult,
    SensitivityParameter,
    SensitivityMethod
)

# Specialized risk types
from .risk_type_models import (
    IntegratedRiskTypeFramework,
    MarketRiskAnalyzer,
    CreditRiskAnalyzer,
    OperationalRiskAnalyzer,
    LiquidityRiskAnalyzer,
    MarketRiskResult,
    CreditRiskResult,
    OperationalRiskResult,
    LiquidityRiskResult,
    MarketRiskFactor,
    CreditRiskLevel,
    LiquidityRiskMetric
)

# Integrated risk engine
from .integrated_risk_engine import (
    IntegratedRiskEngine,
    RiskAnalysisRequest,
    ComprehensiveRiskReport,
    AnalysisScope,
    RiskDimension
)

# Legacy stress testing components (if exists)
try:
    from .stress_testing_framework import (
        StressTestingFramework, HistoricalStressScenarios,
        HypotheticalStressScenarios, ExtreemeValueAnalyzer,
        RegimeSwitchingAnalyzer, StressScenarioType,
        MarketRegime, run_quick_stress_test
    )
    _HAS_LEGACY_STRESS_TESTING = True
except ImportError:
    _HAS_LEGACY_STRESS_TESTING = False

# Utility functions
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

# Package metadata
__version__ = "1.0.0"
__author__ = "Financial Analysis Team"
__description__ = "Comprehensive Risk Analysis Framework for Financial Analysis"

# Export all main classes for easy access
__all__ = [
    # Core Framework
    'RiskAnalysisFramework',
    'IntegratedRiskEngine',
    'RiskAnalysisRequest',
    'ComprehensiveRiskReport',
    'RiskAnalysisResult',
    'RiskAnalysisConfig',

    # Risk Types and Metrics
    'RiskType',
    'RiskLevel',
    'RiskMetrics',
    'AssetRiskProfile',
    'PortfolioRiskMetrics',
    'RiskFactorModel',

    # Statistical Models
    'DistributionType',
    'ProbabilityDistribution',
    'NormalDistribution',
    'StudentTDistribution',
    'LogNormalDistribution',
    'DistributionFitter',
    'CopulaModel',
    'TailBehavior',

    # Correlation Analysis
    'CorrelationAnalyzer',
    'CorrelationMatrix',
    'CorrelationMethod',
    'RiskFactorIdentifier',
    'RiskFactorType',

    # Scenario Modeling
    'ScenarioModelingFramework',
    'CustomScenario',
    'ScenarioType',
    'ScenarioSeverity',
    'ScenarioParameter',
    'PredefinedScenarios',

    # Sensitivity Analysis
    'SensitivityAnalyzer',
    'SensitivityResult',
    'SensitivityParameter',
    'SensitivityMethod',

    # Specialized Risk Types
    'IntegratedRiskTypeFramework',
    'MarketRiskAnalyzer',
    'CreditRiskAnalyzer',
    'OperationalRiskAnalyzer',
    'LiquidityRiskAnalyzer',
    'MarketRiskResult',
    'CreditRiskResult',
    'OperationalRiskResult',
    'LiquidityRiskResult',
    'MarketRiskFactor',
    'CreditRiskLevel',
    'LiquidityRiskMetric',

    # Enums and Constants
    'AnalysisScope',
    'RiskDimension',

    # Utility Functions
    'create_default_risk_engine',
    'quick_risk_assessment',
    'compare_risk_profiles',
    'generate_risk_dashboard'
]

# Add legacy stress testing components if available
if _HAS_LEGACY_STRESS_TESTING:
    __all__.extend([
        'StressTestingFramework', 'HistoricalStressScenarios',
        'HypotheticalStressScenarios', 'ExtreemeValueAnalyzer',
        'RegimeSwitchingAnalyzer', 'StressScenarioType',
        'MarketRegime', 'run_quick_stress_test'
    ])


def create_default_risk_engine(financial_calculator=None) -> IntegratedRiskEngine:
    """
    Create a pre-configured integrated risk engine with default settings.

    Args:
        financial_calculator: Optional FinancialCalculator instance

    Returns:
        Configured IntegratedRiskEngine instance

    Example:
        >>> calc = FinancialCalculator('AAPL')
        >>> risk_engine = create_default_risk_engine(calc)
        >>> # Engine is ready to use with default configuration
    """
    logger.info("Creating default risk engine configuration")

    # Create default configuration
    config = RiskAnalysisConfig(
        default_simulations=10000,
        confidence_levels=[0.90, 0.95, 0.99],
        correlation_methods=[CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN],
        rolling_window=252,
        include_predefined_scenarios=True,
        scenario_monte_carlo_runs=5000
    )

    # Initialize engine
    engine = IntegratedRiskEngine(financial_calculator, config)

    logger.info("Default risk engine created successfully")
    return engine


def quick_risk_assessment(
    asset_id: str,
    financial_calculator=None,
    risk_types: Optional[List[RiskType]] = None
) -> Dict[str, Any]:
    """
    Perform quick risk assessment for a single asset.

    Args:
        asset_id: Asset identifier
        financial_calculator: FinancialCalculator instance
        risk_types: Risk types to analyze (default: MARKET, CREDIT)

    Returns:
        Dictionary with quick risk assessment results

    Example:
        >>> calc = FinancialCalculator('AAPL')
        >>> risk_summary = quick_risk_assessment('AAPL', calc)
        >>> print(f"Risk Level: {risk_summary['risk_level']}")
    """
    logger.info(f"Performing quick risk assessment for {asset_id}")

    if risk_types is None:
        risk_types = [RiskType.MARKET, RiskType.CREDIT]

    try:
        # Create risk engine
        engine = create_default_risk_engine(financial_calculator)

        # Create simple request
        request = RiskAnalysisRequest(
            asset_ids=[asset_id],
            analysis_scope=AnalysisScope.ASSET,
            risk_types=risk_types,
            confidence_levels=[0.95],
            monte_carlo_runs=5000,
            generate_report=False
        )

        # Perform analysis
        result = engine.analyze_risk(request)

        # Extract key metrics
        summary = {
            'asset_id': asset_id,
            'overall_risk_score': result.overall_risk_score,
            'risk_level': result.risk_level.level_name if result.risk_level else 'Unknown',
            'key_risk_drivers': result.key_risk_drivers,
            'analysis_date': result.analysis_date.isoformat(),
            'calculation_time': result.calculation_time
        }

        # Add specific risk metrics if available
        if result.risk_metrics:
            summary['risk_metrics'] = {
                'var_95': result.risk_metrics.var_1day_95,
                'annual_volatility': result.risk_metrics.annual_volatility,
                'max_drawdown': result.risk_metrics.max_drawdown,
                'sharpe_ratio': result.risk_metrics.sharpe_ratio
            }

        return summary

    except Exception as e:
        logger.error(f"Quick risk assessment failed for {asset_id}: {e}")
        return {
            'asset_id': asset_id,
            'error': str(e),
            'overall_risk_score': 50.0,
            'risk_level': 'Unknown'
        }


def compare_risk_profiles(
    asset_ids: List[str],
    financial_calculator=None,
    comparison_metrics: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Compare risk profiles across multiple assets.

    Args:
        asset_ids: List of asset identifiers
        financial_calculator: FinancialCalculator instance
        comparison_metrics: Metrics to compare (default: common risk metrics)

    Returns:
        DataFrame with risk comparison across assets

    Example:
        >>> calc = FinancialCalculator()
        >>> comparison = compare_risk_profiles(['AAPL', 'MSFT', 'GOOGL'], calc)
        >>> print(comparison[['asset_id', 'overall_risk_score', 'risk_level']])
    """
    logger.info(f"Comparing risk profiles for {len(asset_ids)} assets")

    if comparison_metrics is None:
        comparison_metrics = [
            'overall_risk_score', 'risk_level', 'var_95', 'annual_volatility',
            'max_drawdown', 'sharpe_ratio', 'key_risk_drivers'
        ]

    comparison_data = []

    for asset_id in asset_ids:
        try:
            # Perform quick risk assessment
            risk_summary = quick_risk_assessment(asset_id, financial_calculator)

            # Flatten risk metrics for comparison
            comparison_row = {'asset_id': asset_id}

            for metric in comparison_metrics:
                if metric in risk_summary:
                    comparison_row[metric] = risk_summary[metric]
                elif metric in risk_summary.get('risk_metrics', {}):
                    comparison_row[metric] = risk_summary['risk_metrics'][metric]
                else:
                    comparison_row[metric] = None

            comparison_data.append(comparison_row)

        except Exception as e:
            logger.warning(f"Risk comparison failed for {asset_id}: {e}")
            # Add placeholder data
            comparison_row = {'asset_id': asset_id, 'error': str(e)}
            for metric in comparison_metrics:
                comparison_row[metric] = None
            comparison_data.append(comparison_row)

    comparison_df = pd.DataFrame(comparison_data)

    # Sort by risk score if available
    if 'overall_risk_score' in comparison_df.columns:
        comparison_df = comparison_df.sort_values('overall_risk_score', ascending=False, na_position='last')

    logger.info(f"Risk profile comparison completed for {len(comparison_data)} assets")
    return comparison_df


def generate_risk_dashboard(
    asset_ids: List[str],
    financial_calculator=None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate interactive risk dashboard data for multiple assets.

    Args:
        asset_ids: List of asset identifiers
        financial_calculator: FinancialCalculator instance
        output_path: Optional path to save dashboard data

    Returns:
        Dictionary with dashboard data and configuration

    Example:
        >>> calc = FinancialCalculator()
        >>> dashboard = generate_risk_dashboard(['AAPL', 'MSFT'], calc)
        >>> # Use dashboard['charts'] for visualization
    """
    logger.info(f"Generating risk dashboard for {len(asset_ids)} assets")

    try:
        # Get risk comparison data
        comparison_df = compare_risk_profiles(asset_ids, financial_calculator)

        # Create dashboard structure
        dashboard = {
            'metadata': {
                'generation_time': pd.Timestamp.now().isoformat(),
                'assets_analyzed': len(asset_ids),
                'asset_ids': asset_ids
            },
            'summary_statistics': {},
            'comparison_data': comparison_df.to_dict('records'),
            'charts': {},
            'risk_level_distribution': {}
        }

        # Calculate summary statistics if data is available
        if 'overall_risk_score' in comparison_df.columns:
            valid_scores = comparison_df['overall_risk_score'].dropna()
            if len(valid_scores) > 0:
                dashboard['summary_statistics'] = {
                    'avg_risk_score': valid_scores.mean(),
                    'highest_risk_asset': comparison_df.loc[comparison_df['overall_risk_score'].idxmax(), 'asset_id'],
                    'lowest_risk_asset': comparison_df.loc[comparison_df['overall_risk_score'].idxmin(), 'asset_id']
                }

        # Create chart configurations
        if 'overall_risk_score' in comparison_df.columns:
            dashboard['charts']['risk_score_comparison'] = {
                'type': 'bar_chart',
                'data': comparison_df[['asset_id', 'overall_risk_score']].dropna().to_dict('records'),
                'title': 'Risk Score Comparison',
                'x_axis': 'asset_id',
                'y_axis': 'overall_risk_score'
            }

        # Save dashboard data if path provided
        if output_path:
            import json
            with open(output_path, 'w') as f:
                json.dump(dashboard, f, indent=2, default=str)
            logger.info(f"Risk dashboard data saved to {output_path}")

        return dashboard

    except Exception as e:
        logger.error(f"Risk dashboard generation failed: {e}")
        return {
            'error': str(e),
            'metadata': {
                'generation_time': pd.Timestamp.now().isoformat(),
                'assets_analyzed': len(asset_ids),
                'asset_ids': asset_ids
            }
        }


# Package initialization
logger.info(f"Risk Analysis Framework v{__version__} initialized")
logger.info("Available components: Risk Framework, Statistical Models, Correlation Analysis, Scenario Modeling, Specialized Risk Types")