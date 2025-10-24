"""
Risk Analysis Framework Integration Example
==========================================

This module demonstrates how to use the Risk Analysis Framework with the existing
financial analysis system. It provides practical examples of risk assessment for
both individual assets and portfolios.

Usage Examples:
- Individual asset risk analysis
- Portfolio risk assessment
- Scenario analysis and stress testing
- Risk factor identification
- Comprehensive risk reporting
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the risk analysis framework
from core.analysis.risk.risk_framework import RiskAnalysisFramework, RiskAnalysisConfig
from core.analysis.risk.risk_metrics import RiskType, RiskLevel
from core.analysis.risk.scenario_modeling import CustomScenario, ScenarioParameter, ScenarioType, ScenarioSeverity
from core.analysis.risk.correlation_analysis import CorrelationMethod

# Import existing framework components
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.portfolio.portfolio_models import Portfolio, PortfolioHolding

logger = logging.getLogger(__name__)


def create_sample_returns_data(
    tickers: List[str],
    periods: int = 252,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Create sample returns data for demonstration purposes.

    Args:
        tickers: List of asset tickers
        periods: Number of periods (default: 252 trading days)
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with simulated daily returns
    """
    np.random.seed(random_seed)

    # Create date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=periods + 50)  # Extra days for weekends
    date_range = pd.bdate_range(start=start_date, end=end_date)[:periods]

    # Simulate returns with different characteristics
    returns_data = {}

    for i, ticker in enumerate(tickers):
        # Different return characteristics for each asset
        base_return = 0.0008 + i * 0.0002  # Slightly different expected returns
        volatility = 0.015 + i * 0.005      # Different volatilities

        # Generate correlated returns
        if i == 0:
            # First asset - market-like returns
            returns = np.random.normal(base_return, volatility, periods)
        else:
            # Subsequent assets - correlated with first asset
            market_component = returns_data[tickers[0]] * (0.3 + i * 0.1)
            idiosyncratic = np.random.normal(0, volatility * 0.7, periods)
            returns = base_return + market_component + idiosyncratic

        returns_data[ticker] = returns

    return pd.DataFrame(returns_data, index=date_range)


def example_individual_asset_analysis():
    """Demonstrate risk analysis for an individual asset."""
    print("\n" + "="*60)
    print("INDIVIDUAL ASSET RISK ANALYSIS EXAMPLE")
    print("="*60)

    # Initialize financial calculator (placeholder)
    # In practice, this would be initialized with real data
    try:
        calculator = FinancialCalculator("AAPL")  # Placeholder
    except:
        calculator = None
        print("Note: Using mock data (FinancialCalculator not available)")

    # Configure risk analysis
    config = RiskAnalysisConfig(
        default_simulations=5000,
        confidence_levels=[0.95, 0.99],
        rolling_window=60,
        include_predefined_scenarios=True
    )

    # Initialize risk framework
    risk_framework = RiskAnalysisFramework(
        financial_calculator=calculator,
        config=config
    )

    # Create sample returns data
    returns_data = create_sample_returns_data(['AAPL'], periods=252)

    print(f"Analyzing asset: AAPL")
    print(f"Data period: {returns_data.index[0].date()} to {returns_data.index[-1].date()}")
    print(f"Number of observations: {len(returns_data)}")

    # Run comprehensive risk analysis
    result = risk_framework.comprehensive_risk_analysis(
        asset_id="AAPL",
        returns_data=returns_data,
        analysis_id="aapl_risk_analysis"
    )

    # Display results
    print(f"\nRisk Analysis Results:")
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Overall Risk Score: {result.overall_risk_score:.1f}/100")
    print(f"Risk Level: {result.risk_level.level_name if result.risk_level else 'Unknown'}")

    if result.risk_metrics:
        print(f"\nKey Risk Metrics:")
        print(f"  Annual Volatility: {result.risk_metrics.annual_volatility:.2%}")
        print(f"  Value at Risk (95%): {result.risk_metrics.var_1day_95:.2%}")
        print(f"  Maximum Drawdown: {result.risk_metrics.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {result.risk_metrics.sharpe_ratio:.2f}")
        print(f"  Probability of Loss: {result.risk_metrics.probability_of_loss:.2%}")

    if result.key_risk_drivers:
        print(f"\nKey Risk Drivers:")
        for driver in result.key_risk_drivers:
            print(f"  - {driver}")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    print(f"\nAnalysis completed in {result.calculation_time:.2f} seconds")

    return result


def example_portfolio_risk_analysis():
    """Demonstrate risk analysis for a portfolio."""
    print("\n" + "="*60)
    print("PORTFOLIO RISK ANALYSIS EXAMPLE")
    print("="*60)

    # Create sample portfolio
    holdings = [
        PortfolioHolding(asset_id="AAPL", weight=0.25, shares=100),
        PortfolioHolding(asset_id="MSFT", weight=0.25, shares=80),
        PortfolioHolding(asset_id="GOOGL", weight=0.20, shares=50),
        PortfolioHolding(asset_id="AMZN", weight=0.15, shares=30),
        PortfolioHolding(asset_id="TSLA", weight=0.15, shares=40)
    ]

    portfolio = Portfolio(
        portfolio_id="tech_portfolio",
        name="Technology Portfolio",
        holdings=holdings
    )

    # Create sample returns data for portfolio assets
    tickers = [holding.asset_id for holding in holdings]
    returns_data = create_sample_returns_data(tickers, periods=252)

    print(f"Analyzing portfolio: {portfolio.name}")
    print(f"Number of holdings: {len(portfolio.holdings)}")
    print(f"Assets: {', '.join(tickers)}")

    # Configure risk analysis
    config = RiskAnalysisConfig(
        default_simulations=3000,
        correlation_methods=[CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN],
        max_risk_factors=5
    )

    # Initialize risk framework
    risk_framework = RiskAnalysisFramework(config=config)

    # Run comprehensive portfolio risk analysis
    result = risk_framework.comprehensive_risk_analysis(
        portfolio=portfolio,
        returns_data=returns_data,
        analysis_id="tech_portfolio_analysis"
    )

    # Display results
    print(f"\nPortfolio Risk Analysis Results:")
    print(f"Overall Risk Score: {result.overall_risk_score:.1f}/100")
    print(f"Risk Level: {result.risk_level.level_name if result.risk_level else 'Unknown'}")

    if result.risk_metrics:
        print(f"\nPortfolio Risk Metrics:")
        print(f"  Annual Volatility: {result.risk_metrics.annual_volatility:.2%}")
        print(f"  Value at Risk (95%): {result.risk_metrics.var_1day_95:.2%}")
        print(f"  Conditional VaR (95%): {result.risk_metrics.cvar_1day_95:.2%}")
        print(f"  Maximum Drawdown: {result.risk_metrics.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {result.risk_metrics.sharpe_ratio:.2f}")

    # Correlation analysis
    if result.correlation_matrices:
        print(f"\nCorrelation Analysis:")
        pearson_matrix = result.correlation_matrices.get('pearson')
        if pearson_matrix:
            print(f"  Average Correlation: {pearson_matrix.market_concentration():.2f}")
            print(f"  Correlation Stability: {pearson_matrix.stability_score:.2f}")

            # Identify highly correlated pairs
            high_corr_pairs = pearson_matrix.identify_highly_correlated_pairs(threshold=0.7)
            if high_corr_pairs:
                print(f"  Highly Correlated Pairs (>70%):")
                for asset1, asset2, corr in high_corr_pairs[:3]:  # Show top 3
                    print(f"    {asset1} - {asset2}: {corr:.2f}")

    # Risk factor analysis
    if result.risk_factors and result.risk_factors.identified_factors:
        print(f"\nRisk Factor Analysis:")
        print(f"  Number of factors identified: {len(result.risk_factors.identified_factors)}")

        for factor_type, factor_info in list(result.risk_factors.identified_factors.items())[:3]:
            print(f"  {factor_type.value.title()} Factor:")
            print(f"    Explained Variance: {factor_info['explained_variance']:.1%}")
            print(f"    Factor Strength: {factor_info['factor_strength']:.2f}")

    # Scenario analysis
    if result.scenario_results:
        print(f"\nScenario Analysis Results:")
        for scenario_name, scenario_result in list(result.scenario_results.items())[:3]:
            print(f"  {scenario_name}:")
            portfolio_analysis = scenario_result.get('portfolio_analysis', {})
            total_return = portfolio_analysis.get('total_return', {})
            if total_return:
                print(f"    Expected Impact: {total_return.get('mean', 0):.2%}")
                print(f"    Worst Case (5%): {total_return.get('var_95', 0):.2%}")

    return result


def example_custom_scenario_analysis():
    """Demonstrate custom scenario creation and analysis."""
    print("\n" + "="*60)
    print("CUSTOM SCENARIO ANALYSIS EXAMPLE")
    print("="*60)

    # Create custom scenario
    custom_scenario = CustomScenario(
        name="Tech Sector Correction",
        description="Technology sector correction with increased volatility",
        scenario_type=ScenarioType.STRESS,
        severity=ScenarioSeverity.MODERATE
    )

    # Add parameters to scenario
    custom_scenario.add_parameter(ScenarioParameter(
        name="tech_return",
        variable_type="return",
        base_value=0.0,
        shock_value=-0.25,  # 25% decline
        shock_type="relative",
        description="Technology sector decline"
    ))

    custom_scenario.add_parameter(ScenarioParameter(
        name="volatility_spike",
        variable_type="volatility",
        base_value=0.20,
        shock_value=0.40,
        shock_type="absolute",
        description="Volatility increase"
    ))

    custom_scenario.add_parameter(ScenarioParameter(
        name="correlation_increase",
        variable_type="correlation",
        base_value=0.4,
        shock_value=0.8,
        shock_type="absolute",
        description="Asset correlation increase"
    ))

    # Initialize scenario framework
    risk_framework = RiskAnalysisFramework()

    # Add custom scenario
    risk_framework.scenario_framework.add_scenario(custom_scenario)

    print(f"Created custom scenario: {custom_scenario.name}")
    print(f"Scenario type: {custom_scenario.scenario_type.value}")
    print(f"Severity: {custom_scenario.severity.description}")
    print(f"Parameters: {len(custom_scenario.parameters)}")

    # Generate scenario values
    scenario_values = custom_scenario.generate_scenario_values()

    print(f"\nScenario Parameter Values:")
    for param_name, value in scenario_values.items():
        param = custom_scenario.parameters[param_name]
        if param.shock_type == "relative":
            print(f"  {param_name}: {value:.2%} (change from base: {(value/param.base_value - 1):.2%})")
        else:
            print(f"  {param_name}: {value:.3f} (change from base: {value - param.base_value:+.3f})")

    # Run scenario analysis on sample portfolio
    portfolio_data = {
        'equity_weight': 0.8,
        'bond_weight': 0.2,
        'base_volatility': 0.15
    }

    scenario_results = risk_framework.scenario_framework.run_scenario_analysis(
        scenario_names=[custom_scenario.name],
        portfolio_data=portfolio_data,
        monte_carlo_runs=1000
    )

    if scenario_results:
        result = scenario_results[custom_scenario.name]
        print(f"\nScenario Analysis Results:")
        print(f"  Monte Carlo runs: {result['runs']}")

        portfolio_analysis = result.get('portfolio_analysis', {})
        if portfolio_analysis:
            total_return = portfolio_analysis.get('total_return', {})
            print(f"  Expected portfolio impact: {total_return.get('mean', 0):.2%}")
            print(f"  Standard deviation: {total_return.get('std', 0):.2%}")
            print(f"  Value at Risk (95%): {total_return.get('var_95', 0):.2%}")
            print(f"  Maximum loss: {total_return.get('max_loss', 0):.2%}")
            print(f"  Probability of loss: {total_return.get('probability_of_loss', 0):.1%}")

    return custom_scenario, scenario_results


def example_correlation_analysis():
    """Demonstrate advanced correlation analysis."""
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS EXAMPLE")
    print("="*60)

    # Create sample data with different correlation regimes
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'SPY']
    returns_data = create_sample_returns_data(tickers, periods=500)

    # Initialize correlation analyzer
    risk_framework = RiskAnalysisFramework()
    risk_framework.correlation_analyzer.returns_data = returns_data

    print(f"Analyzing correlations for {len(tickers)} assets")
    print(f"Data period: {returns_data.index[0].date()} to {returns_data.index[-1].date()}")

    # Calculate correlation matrices using different methods
    methods = [CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN]
    correlation_matrices = {}

    for method in methods:
        corr_matrix = risk_framework.correlation_analyzer.calculate_correlation_matrix(method)
        correlation_matrices[method.value] = corr_matrix
        print(f"\n{method.value.title()} Correlation Analysis:")
        print(f"  Average correlation: {corr_matrix.market_concentration():.3f}")
        print(f"  Stability score: {corr_matrix.stability_score:.3f}")

        # Identify highly correlated pairs
        high_corr_pairs = corr_matrix.identify_highly_correlated_pairs(threshold=0.6)
        if high_corr_pairs:
            print(f"  Highly correlated pairs (>60%):")
            for asset1, asset2, corr in high_corr_pairs[:3]:
                print(f"    {asset1} - {asset2}: {corr:.3f}")

    # Rolling correlation analysis
    stability_analysis = risk_framework.correlation_analyzer.rolling_correlation_analysis(
        window=60, step=10
    )

    print(f"\nRolling Correlation Analysis:")
    print(f"  Average correlation: {stability_analysis['avg_correlation']:.3f}")
    print(f"  Correlation volatility: {stability_analysis['correlation_volatility']:.3f}")
    print(f"  Correlation trend: {stability_analysis['correlation_trend']:+.4f}")

    if stability_analysis['regime_changes']:
        print(f"  Regime changes detected: {len(stability_analysis['regime_changes'])}")
        for regime in stability_analysis['regime_changes'][:2]:  # Show first 2
            print(f"    {regime['date'].date()}: {regime['regime']} ({regime['level']:.3f})")

    # Risk factor identification
    risk_factors = risk_framework.correlation_analyzer.identify_risk_factors(
        method='pca', n_factors=3
    )

    if risk_factors and risk_factors.identified_factors:
        print(f"\nRisk Factor Analysis:")
        print(f"  Factors identified: {len(risk_factors.identified_factors)}")

        total_variance_explained = 0
        for factor_type, factor_info in risk_factors.identified_factors.items():
            variance = factor_info['explained_variance']
            total_variance_explained += variance
            print(f"  {factor_type.value.title()} Factor: {variance:.1%} variance explained")

        print(f"  Total variance explained: {total_variance_explained:.1%}")

    return correlation_matrices, stability_analysis, risk_factors


def run_all_examples():
    """Run all risk analysis examples."""
    print("RISK ANALYSIS FRAMEWORK - COMPREHENSIVE EXAMPLES")
    print("="*80)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Example 1: Individual asset analysis
        asset_result = example_individual_asset_analysis()

        # Example 2: Portfolio risk analysis
        portfolio_result = example_portfolio_risk_analysis()

        # Example 3: Custom scenario analysis
        custom_scenario, scenario_results = example_custom_scenario_analysis()

        # Example 4: Correlation analysis
        corr_matrices, stability, risk_factors = example_correlation_analysis()

        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)

        # Summary
        print("\nSummary of Examples:")
        print(f"1. Individual Asset Analysis: {asset_result.analysis_id}")
        print(f"   - Risk Score: {asset_result.overall_risk_score:.1f}/100")
        print(f"   - Risk Level: {asset_result.risk_level.level_name if asset_result.risk_level else 'Unknown'}")

        print(f"\n2. Portfolio Analysis: {portfolio_result.analysis_id}")
        print(f"   - Risk Score: {portfolio_result.overall_risk_score:.1f}/100")
        print(f"   - Risk Level: {portfolio_result.risk_level.level_name if portfolio_result.risk_level else 'Unknown'}")

        print(f"\n3. Custom Scenario: {custom_scenario.name}")
        print(f"   - Severity: {custom_scenario.severity.description}")
        print(f"   - Parameters: {len(custom_scenario.parameters)}")

        print(f"\n4. Correlation Analysis:")
        print(f"   - Methods tested: {len(corr_matrices)}")
        print(f"   - Risk factors identified: {len(risk_factors.identified_factors) if risk_factors else 0}")

        return {
            'asset_analysis': asset_result,
            'portfolio_analysis': portfolio_result,
            'custom_scenario': custom_scenario,
            'correlation_analysis': (corr_matrices, stability, risk_factors)
        }

    except Exception as e:
        print(f"\nError during examples execution: {e}")
        logger.error(f"Examples failed: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # Run examples when script is executed directly
    results = run_all_examples()

    if results:
        print(f"\nRisk Analysis Framework examples completed successfully!")
        print(f"Check the detailed output above for comprehensive analysis results.")
    else:
        print(f"\nExamples execution failed. Check logs for details.")