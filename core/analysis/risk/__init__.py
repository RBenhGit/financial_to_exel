"""
Risk Analysis Module
==================

This module provides comprehensive risk analysis capabilities for financial instruments,
portfolios, and investment strategies. It integrates with the existing Monte Carlo engine
and portfolio framework to provide advanced risk assessment tools.

Key Components:
- RiskAnalysisFramework: Core risk analysis engine
- RiskMetrics: Statistical risk measurement and calculations
- ScenarioModeling: Flexible scenario analysis framework
- CorrelationAnalysis: Risk factor identification and correlation modeling
- StressTesting: Extreme condition and tail risk analysis

Usage:
    >>> from core.analysis.risk import RiskAnalysisFramework
    >>> from core.analysis.engines.financial_calculations import FinancialCalculator
    >>>
    >>> calc = FinancialCalculator('AAPL')
    >>> risk_analyzer = RiskAnalysisFramework(calc)
    >>> risk_report = risk_analyzer.comprehensive_risk_analysis()
"""

from .risk_framework import RiskAnalysisFramework
from .risk_metrics import (
    RiskType, RiskMetrics, RiskLevel,
    PortfolioRiskMetrics, AssetRiskProfile
)
from .scenario_modeling import (
    ScenarioModelingFramework, ScenarioType,
    PredefinedScenarios, CustomScenario
)
from .correlation_analysis import (
    CorrelationAnalyzer, RiskFactorIdentifier,
    CorrelationMatrix
)
from .stress_testing_framework import (
    StressTestingFramework, HistoricalStressScenarios,
    HypotheticalStressScenarios, ExtreemeValueAnalyzer,
    RegimeSwitchingAnalyzer, StressScenarioType,
    MarketRegime, run_quick_stress_test
)

__all__ = [
    'RiskAnalysisFramework',
    'RiskType', 'RiskMetrics', 'RiskLevel',
    'PortfolioRiskMetrics', 'AssetRiskProfile',
    'ScenarioModelingFramework', 'ScenarioType',
    'PredefinedScenarios', 'CustomScenario',
    'CorrelationAnalyzer', 'RiskFactorIdentifier',
    'CorrelationMatrix',
    'StressTestingFramework', 'HistoricalStressScenarios',
    'HypotheticalStressScenarios', 'ExtreemeValueAnalyzer',
    'RegimeSwitchingAnalyzer', 'StressScenarioType',
    'MarketRegime', 'run_quick_stress_test'
]