"""
Portfolio Analysis Module
========================

This module provides comprehensive portfolio-level analysis capabilities including
portfolio construction, optimization, performance measurement, and risk analysis.

Components:
- portfolio_models: Core data structures for portfolio management
- portfolio_company_integration: Integration with existing financial analysis
- portfolio_rebalancing: Position sizing and rebalancing algorithms
- portfolio_strategies: Predefined strategy templates and screening
- portfolio_optimization: Modern portfolio theory optimization algorithms
- black_litterman: Black-Litterman model for enhanced optimization
- portfolio_performance_analytics: Comprehensive performance measurement and attribution
- portfolio_backtesting: Historical simulation and strategy validation framework

Key Features:
- Multiple portfolio types (Growth, Value, Dividend, Balanced, etc.)
- Modern Portfolio Theory optimization (Mean-Variance, Risk Parity, etc.)
- Black-Litterman model with investor views
- Efficient frontier calculation
- Sophisticated rebalancing algorithms with transaction cost optimization
- Integration with existing FinancialCalculator and data sources
- Risk management and performance attribution
- Strategy templates for common investment approaches
"""

from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    RebalancingStrategy,
    PositionSizingMethod,
    PortfolioMetrics,
    PortfolioAnalysisResult,
    validate_portfolio,
    create_sample_portfolio
)

from .portfolio_company_integration import (
    PortfolioCompanyData,
    PortfolioCompanyIntegrator
)

from .portfolio_rebalancing import (
    PortfolioRebalancer,
    PositionSizer,
    RebalancingTransaction,
    RebalancingPlan
)

from .portfolio_strategies import (
    PortfolioTemplate,
    PortfolioStrategyFactory,
    PortfolioScreener,
    create_portfolio_from_template
)

from .company_comparison import (
    MultiCompanyComparator,
    ComparisonMatrix,
    CompanyMetrics,
    ComparisonMetric,
    ComparisonType
)

from .relative_valuation import (
    RelativeValuationAnalyzer,
    RelativeValuationResult,
    ValuationBenchmark,
    ValuationMultiple
)

from .growth_trend_analysis import (
    GrowthTrendAnalyzer,
    CompanyGrowthProfile,
    GrowthComparisonResult,
    GrowthMetrics,
    GrowthMetricType,
    TrendDirection
)

from .portfolio_optimization import (
    PortfolioOptimizer,
    OptimizationObjective,
    OptimizationMethod,
    OptimizationConstraints,
    OptimizationResult,
    create_sample_optimization_data,
    create_optimization_constraints_from_portfolio,
    apply_optimization_to_portfolio
)

from .black_litterman import (
    BlackLittermanOptimizer,
    BlackLittermanInputs,
    BlackLittermanResult,
    InvestorView,
    ViewType,
    create_absolute_view,
    create_relative_view,
    create_sample_bl_optimization,
    integrate_black_litterman_with_portfolio
)

from .portfolio_performance_analytics import (
    PortfolioPerformanceAnalyzer,
    PerformanceMetrics,
    AttributionAnalysis,
    PerformancePeriod,
    create_sample_performance_data
)

from .portfolio_backtesting import (
    BacktestEngine,
    BacktestResult,
    BacktestPeriod,
    TransactionCostModel,
    RegimeAnalyzer,
    StressTester,
    MarketRegime,
    StressScenario,
    create_sample_backtest
)

__all__ = [
    # Core Models
    'Portfolio',
    'PortfolioHolding',
    'PortfolioType',
    'RebalancingStrategy',
    'PositionSizingMethod',
    'PortfolioMetrics',
    'PortfolioAnalysisResult',
    'validate_portfolio',
    'create_sample_portfolio',

    # Company Integration
    'PortfolioCompanyData',
    'PortfolioCompanyIntegrator',

    # Rebalancing
    'PortfolioRebalancer',
    'PositionSizer',
    'RebalancingTransaction',
    'RebalancingPlan',

    # Strategies
    'PortfolioTemplate',
    'PortfolioStrategyFactory',
    'PortfolioScreener',
    'create_portfolio_from_template',

    # Multi-Company Comparison
    'MultiCompanyComparator',
    'ComparisonMatrix',
    'CompanyMetrics',
    'ComparisonMetric',
    'ComparisonType',

    # Relative Valuation
    'RelativeValuationAnalyzer',
    'RelativeValuationResult',
    'ValuationBenchmark',
    'ValuationMultiple',

    # Growth Analysis
    'GrowthTrendAnalyzer',
    'CompanyGrowthProfile',
    'GrowthComparisonResult',
    'GrowthMetrics',
    'GrowthMetricType',
    'TrendDirection',

    # Portfolio Optimization
    'PortfolioOptimizer',
    'OptimizationObjective',
    'OptimizationMethod',
    'OptimizationConstraints',
    'OptimizationResult',
    'create_sample_optimization_data',
    'create_optimization_constraints_from_portfolio',
    'apply_optimization_to_portfolio',

    # Black-Litterman
    'BlackLittermanOptimizer',
    'BlackLittermanInputs',
    'BlackLittermanResult',
    'InvestorView',
    'ViewType',
    'create_absolute_view',
    'create_relative_view',
    'create_sample_bl_optimization',
    'integrate_black_litterman_with_portfolio',

    # Performance Analytics
    'PortfolioPerformanceAnalyzer',
    'PerformanceMetrics',
    'AttributionAnalysis',
    'PerformancePeriod',
    'create_sample_performance_data',

    # Backtesting Framework
    'BacktestEngine',
    'BacktestResult',
    'BacktestPeriod',
    'TransactionCostModel',
    'RegimeAnalyzer',
    'StressTester',
    'MarketRegime',
    'StressScenario',
    'create_sample_backtest'
]