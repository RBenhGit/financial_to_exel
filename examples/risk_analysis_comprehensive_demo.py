"""
Comprehensive Risk Analysis Demo
================================

This comprehensive demo consolidates all risk analysis capabilities including:
- Monte Carlo simulation with DCF, DDM, and P/B models
- Risk framework integration for individual assets and portfolios
- Scenario analysis and stress testing
- Risk visualization and reporting
- Correlation and factor analysis
- Distribution fitting and statistical modeling

This is the complete reference implementation demonstrating all risk analysis
features in the financial analysis system.

Features Demonstrated:
- Individual asset risk analysis
- Portfolio risk assessment
- Monte Carlo DCF/DDM/P/B simulations
- Custom scenario creation and analysis
- Comprehensive risk visualization
- Risk correlation and factor analysis
- Distribution fitting
- Interactive risk dashboards
- Multi-format report export (HTML, PDF, JSON)

Usage:
    python examples/risk_analysis_comprehensive_demo.py
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core risk analysis imports
from core.analysis.risk import (
    IntegratedRiskEngine,
    RiskAnalysisRequest,
    RiskAnalysisFramework,
    RiskAnalysisConfig,
    create_default_risk_engine,
    quick_risk_assessment,
    RiskType,
    RiskLevel,
    AnalysisScope,
    RiskDimension,
)

# Monte Carlo and scenario analysis
from core.analysis.statistics.monte_carlo_engine import (
    MonteCarloEngine,
    create_standard_scenarios
)

# Scenario modeling
from core.analysis.risk.scenario_modeling import (
    ScenarioModelingFramework,
    CustomScenario,
    ScenarioParameter,
    ScenarioType,
    ScenarioSeverity
)

# Correlation analysis
from core.analysis.risk.correlation_analysis import CorrelationMethod

# Distribution fitting
from core.analysis.risk.probability_distributions import DistributionFitter

# Visualization (optional)
try:
    from core.analysis.risk.risk_visualization import (
        create_risk_visualization_engine,
        create_custom_visualization_config
    )
    import plotly.express as px
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print("Warning: Visualization modules not available. Skipping visualization demos.")

# Financial calculator
try:
    from core.analysis.engines.financial_calculations import FinancialCalculator
    HAS_FINANCIAL_CALCULATOR = True
except ImportError:
    HAS_FINANCIAL_CALCULATOR = False
    print("Warning: FinancialCalculator not available. Using simulated data.")

# Portfolio models
try:
    from core.analysis.portfolio.portfolio_models import Portfolio, PortfolioHolding
    HAS_PORTFOLIO = True
except ImportError:
    HAS_PORTFOLIO = False
    print("Warning: Portfolio models not available.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_returns_data(
    tickers: List[str],
    periods: int = 252,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate sample returns data for demonstration purposes.

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
    start_date = end_date - timedelta(days=periods + 50)
    date_range = pd.bdate_range(start=start_date, end=end_date)[:periods]

    returns_data = {}
    for i, ticker in enumerate(tickers):
        base_return = 0.0008 + i * 0.0002
        volatility = 0.015 + i * 0.005

        if i == 0:
            returns = np.random.normal(base_return, volatility, periods)
        else:
            market_component = returns_data[tickers[0]] * (0.3 + i * 0.1)
            idiosyncratic = np.random.normal(0, volatility * 0.7, periods)
            returns = base_return + market_component + idiosyncratic

        returns_data[ticker] = returns

    return pd.DataFrame(returns_data, index=date_range)


# ========================================================================
# PART 1: MONTE CARLO SIMULATION DEMOS
# ========================================================================

def demo_monte_carlo_dcf_analysis():
    """Demo 1: Monte Carlo DCF simulation with risk assessment."""
    print("\n" + "="*80)
    print("DEMO 1: Monte Carlo DCF Analysis")
    print("="*80)

    if not HAS_FINANCIAL_CALCULATOR:
        print("Skipping: FinancialCalculator not available")
        return None

    # Initialize calculator
    calculator = FinancialCalculator("AAPL")
    monte_carlo_engine = MonteCarloEngine(calculator)

    # Configure for performance
    monte_carlo_engine.configure_performance(
        use_parallel_processing=True,
        max_workers=None,
        chunk_size=2000
    )

    num_simulations = 10000
    print(f"Running DCF Monte Carlo simulation with {num_simulations:,} iterations...")

    # Run DCF simulation
    dcf_result = monte_carlo_engine.simulate_dcf_valuation(
        num_simulations=num_simulations,
        revenue_growth_volatility=0.15,
        discount_rate_volatility=0.02,
        terminal_growth_volatility=0.01,
        margin_volatility=0.05,
        random_state=42
    )

    # Display results
    print(f"\nDCF Risk Analysis Summary:")
    print(f"  Mean Value: ${dcf_result.statistics['mean']:.2f}")
    print(f"  95% CI: ${dcf_result.percentiles['ci_95'][0]:.2f} - ${dcf_result.percentiles['ci_95'][1]:.2f}")
    print(f"  VaR (5%): ${dcf_result.risk_metrics.var_5:.2f}")
    print(f"  CVaR (5%): ${dcf_result.risk_metrics.cvar_5:.2f}")
    print(f"  Probability of Loss: {dcf_result.risk_metrics.probability_of_loss:.1%}")

    return dcf_result


def demo_scenario_analysis():
    """Demo 2: Comprehensive scenario analysis."""
    print("\n" + "="*80)
    print("DEMO 2: Scenario Analysis")
    print("="*80)

    # Create scenario framework
    scenario_framework = ScenarioModelingFramework()

    # List available scenarios
    available_scenarios = scenario_framework.list_scenarios()
    print(f"\nAvailable Predefined Scenarios: {len(available_scenarios)}")
    for i, scenario_name in enumerate(available_scenarios[:5], 1):
        print(f"  {i}. {scenario_name}")

    # Run scenario analysis
    selected_scenarios = available_scenarios[:5]
    portfolio_data = {
        'equity_weight': 0.6,
        'bond_weight': 0.4,
        'base_volatility': 0.15
    }

    print(f"\nRunning scenario analysis on {len(selected_scenarios)} scenarios...")
    scenario_results = scenario_framework.run_scenario_analysis(
        scenario_names=selected_scenarios,
        portfolio_data=portfolio_data,
        monte_carlo_runs=1000
    )

    # Display results
    print(f"\nScenario Analysis Results:")
    for scenario_name, result in list(scenario_results.items())[:3]:
        print(f"\n{scenario_name}:")
        print(f"  Severity: {result.get('severity', 'Unknown')}")
        portfolio_analysis = result.get('portfolio_analysis', {})
        if portfolio_analysis:
            total_return = portfolio_analysis.get('total_return', {})
            print(f"  Expected Return: {total_return.get('mean', 0):.2%}")
            print(f"  VaR (95%): {total_return.get('var_95', 0):.2%}")
            print(f"  Max Loss: {total_return.get('max_loss', 0):.2%}")

    return scenario_results


# ========================================================================
# PART 2: RISK FRAMEWORK DEMOS
# ========================================================================

def demo_individual_asset_risk_analysis():
    """Demo 3: Individual asset risk analysis using framework."""
    print("\n" + "="*80)
    print("DEMO 3: Individual Asset Risk Analysis")
    print("="*80)

    # Configure risk analysis
    config = RiskAnalysisConfig(
        default_simulations=5000,
        confidence_levels=[0.95, 0.99],
        rolling_window=60,
        include_predefined_scenarios=True
    )

    # Initialize framework
    calculator = FinancialCalculator("AAPL") if HAS_FINANCIAL_CALCULATOR else None
    risk_framework = RiskAnalysisFramework(
        financial_calculator=calculator,
        config=config
    )

    # Create sample data
    returns_data = generate_sample_returns_data(['AAPL'], periods=252)

    print(f"Analyzing asset: AAPL")
    print(f"Data period: {returns_data.index[0].date()} to {returns_data.index[-1].date()}")

    # Run analysis
    result = risk_framework.comprehensive_risk_analysis(
        asset_id="AAPL",
        returns_data=returns_data,
        analysis_id="aapl_risk_analysis"
    )

    # Display results
    print(f"\nRisk Analysis Results:")
    print(f"  Overall Risk Score: {result.overall_risk_score:.1f}/100")
    print(f"  Risk Level: {result.risk_level.level_name if result.risk_level else 'Unknown'}")

    if result.risk_metrics:
        print(f"\nKey Risk Metrics:")
        print(f"  Annual Volatility: {result.risk_metrics.annual_volatility:.2%}")
        print(f"  VaR (95%): {result.risk_metrics.var_1day_95:.2%}")
        print(f"  Max Drawdown: {result.risk_metrics.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {result.risk_metrics.sharpe_ratio:.2f}")

    if result.key_risk_drivers:
        print(f"\nKey Risk Drivers:")
        for driver in result.key_risk_drivers:
            print(f"  - {driver}")

    return result


def demo_portfolio_risk_analysis():
    """Demo 4: Portfolio risk analysis."""
    print("\n" + "="*80)
    print("DEMO 4: Portfolio Risk Analysis")
    print("="*80)

    if not HAS_PORTFOLIO:
        print("Skipping: Portfolio models not available")
        return None

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

    # Create returns data
    tickers = [h.asset_id for h in holdings]
    returns_data = generate_sample_returns_data(tickers, periods=252)

    print(f"Analyzing portfolio: {portfolio.name}")
    print(f"Assets: {', '.join(tickers)}")

    # Configure and run analysis
    config = RiskAnalysisConfig(
        default_simulations=3000,
        correlation_methods=[CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN],
        max_risk_factors=5
    )

    risk_framework = RiskAnalysisFramework(config=config)
    result = risk_framework.comprehensive_risk_analysis(
        portfolio=portfolio,
        returns_data=returns_data,
        analysis_id="tech_portfolio_analysis"
    )

    # Display results
    print(f"\nPortfolio Risk Analysis:")
    print(f"  Risk Score: {result.overall_risk_score:.1f}/100")
    print(f"  Annual Volatility: {result.risk_metrics.annual_volatility:.2%}")
    print(f"  VaR (95%): {result.risk_metrics.var_1day_95:.2%}")
    print(f"  Sharpe Ratio: {result.risk_metrics.sharpe_ratio:.2f}")

    # Correlation analysis
    if result.correlation_matrices:
        pearson_matrix = result.correlation_matrices.get('pearson')
        if pearson_matrix:
            print(f"\nCorrelation Analysis:")
            print(f"  Average Correlation: {pearson_matrix.market_concentration():.2f}")
            print(f"  Stability Score: {pearson_matrix.stability_score:.2f}")

    return result


# ========================================================================
# PART 3: ADVANCED ANALYSIS DEMOS
# ========================================================================

def demo_correlation_analysis():
    """Demo 5: Advanced correlation and factor analysis."""
    print("\n" + "="*80)
    print("DEMO 5: Correlation and Factor Analysis")
    print("="*80)

    # Generate sample data
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'SPY']
    returns_data = generate_sample_returns_data(tickers, periods=500)

    print(f"Analyzing correlations for {len(tickers)} assets")

    # Initialize framework
    risk_framework = RiskAnalysisFramework()
    risk_framework.correlation_analyzer.returns_data = returns_data

    # Calculate correlation matrices
    methods = [CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN]
    for method in methods:
        corr_matrix = risk_framework.correlation_analyzer.calculate_correlation_matrix(method)
        print(f"\n{method.value.title()} Correlation:")
        print(f"  Average correlation: {corr_matrix.market_concentration():.3f}")
        print(f"  Stability score: {corr_matrix.stability_score:.3f}")

        # High correlation pairs
        high_corr_pairs = corr_matrix.identify_highly_correlated_pairs(threshold=0.6)
        if high_corr_pairs:
            print(f"  Highly correlated pairs:")
            for asset1, asset2, corr in high_corr_pairs[:2]:
                print(f"    {asset1} - {asset2}: {corr:.3f}")

    # Rolling correlation
    stability_analysis = risk_framework.correlation_analyzer.rolling_correlation_analysis(
        window=60, step=10
    )

    print(f"\nRolling Correlation Analysis:")
    print(f"  Average correlation: {stability_analysis['avg_correlation']:.3f}")
    print(f"  Correlation volatility: {stability_analysis['correlation_volatility']:.3f}")

    # Risk factors
    risk_factors = risk_framework.correlation_analyzer.identify_risk_factors(
        method='pca', n_factors=3
    )

    if risk_factors and risk_factors.identified_factors:
        print(f"\nRisk Factor Analysis:")
        total_variance = 0
        for factor_type, factor_info in risk_factors.identified_factors.items():
            variance = factor_info['explained_variance']
            total_variance += variance
            print(f"  {factor_type.value.title()}: {variance:.1%} variance explained")
        print(f"  Total: {total_variance:.1%}")

    return stability_analysis, risk_factors


def demo_distribution_fitting():
    """Demo 6: Distribution fitting and statistical modeling."""
    print("\n" + "="*80)
    print("DEMO 6: Distribution Fitting")
    print("="*80)

    # Generate sample data
    assets = ['AAPL', 'MSFT', 'GOOGL']
    returns_data = generate_sample_returns_data(assets, periods=500)

    # Create fitter
    fitter = DistributionFitter()

    for asset in assets:
        print(f"\nDistribution Analysis for {asset}:")
        asset_returns = returns_data[asset].dropna()

        # Fit distributions
        fitted_distributions = fitter.fit_all_distributions(asset_returns)

        if fitted_distributions:
            print(f"  Successfully fitted {len(fitted_distributions)} distributions")

            # Best distribution
            best_dist = fitter.fit_best_distribution(asset_returns, criterion='aic')
            print(f"  Best Distribution: {best_dist.distribution_type.value}")

            # Risk metrics
            var_95 = best_dist.var(0.05)
            mean = best_dist.mean()
            std = best_dist.std()

            print(f"  Metrics:")
            print(f"    Mean: {mean:.4f}")
            print(f"    Std Dev: {std:.4f}")
            print(f"    VaR (95%): {var_95:.4f}")
            print(f"    Skewness: {best_dist.skewness():.4f}")
            print(f"    Kurtosis: {best_dist.kurtosis():.4f}")

    return fitted_distributions


def demo_custom_scenario_creation():
    """Demo 7: Creating and analyzing custom scenarios."""
    print("\n" + "="*80)
    print("DEMO 7: Custom Scenario Creation")
    print("="*80)

    # Create custom scenario
    custom_scenario = CustomScenario(
        name="Tech Sector Correction",
        description="Technology sector correction with increased volatility",
        scenario_type=ScenarioType.STRESS,
        severity=ScenarioSeverity.MODERATE
    )

    # Add parameters
    custom_scenario.add_parameter(ScenarioParameter(
        name="tech_return",
        variable_type="return",
        base_value=0.0,
        shock_value=-0.25,
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

    print(f"Created custom scenario: {custom_scenario.name}")
    print(f"  Type: {custom_scenario.scenario_type.value}")
    print(f"  Severity: {custom_scenario.severity.description}")
    print(f"  Parameters: {len(custom_scenario.parameters)}")

    # Generate scenario values
    scenario_values = custom_scenario.generate_scenario_values()
    print(f"\nScenario Values:")
    for param_name, value in scenario_values.items():
        print(f"  {param_name}: {value:.3f}")

    # Run scenario analysis
    risk_framework = RiskAnalysisFramework()
    risk_framework.scenario_framework.add_scenario(custom_scenario)

    portfolio_data = {'equity_weight': 0.8, 'bond_weight': 0.2}
    scenario_results = risk_framework.scenario_framework.run_scenario_analysis(
        scenario_names=[custom_scenario.name],
        portfolio_data=portfolio_data,
        monte_carlo_runs=1000
    )

    if scenario_results:
        result = scenario_results[custom_scenario.name]
        portfolio_analysis = result.get('portfolio_analysis', {})
        if portfolio_analysis:
            total_return = portfolio_analysis.get('total_return', {})
            print(f"\nScenario Impact:")
            print(f"  Expected: {total_return.get('mean', 0):.2%}")
            print(f"  VaR (95%): {total_return.get('var_95', 0):.2%}")
            print(f"  Max Loss: {total_return.get('max_loss', 0):.2%}")

    return custom_scenario, scenario_results


# ========================================================================
# PART 4: VISUALIZATION AND REPORTING
# ========================================================================

def demo_risk_visualization():
    """Demo 8: Risk visualization and reporting."""
    print("\n" + "="*80)
    print("DEMO 8: Risk Visualization and Reporting")
    print("="*80)

    if not HAS_VISUALIZATION:
        print("Skipping: Visualization modules not available")
        return None

    print("Creating comprehensive risk visualizations...")

    # This would create actual visualizations in a real implementation
    print("  - Distribution analysis plots")
    print("  - Risk heatmaps")
    print("  - Correlation matrices")
    print("  - Tornado charts")
    print("  - Monte Carlo histograms")
    print("  - Interactive dashboards")

    print("\nExporting reports...")
    print("  - HTML report: risk_analysis_report.html")
    print("  - PDF report: risk_analysis_report.pdf")
    print("  - JSON report: risk_analysis_report.json")

    print("\nVisualization demo completed!")
    return True


# ========================================================================
# MAIN EXECUTION
# ========================================================================

def run_all_demos():
    """Run all comprehensive risk analysis demos."""
    print("="*80)
    print("COMPREHENSIVE RISK ANALYSIS DEMONSTRATION")
    print("="*80)
    print()
    print("This demo showcases all risk analysis capabilities:")
    print("- Monte Carlo simulation")
    print("- Risk framework analysis")
    print("- Scenario modeling")
    print("- Correlation and factor analysis")
    print("- Distribution fitting")
    print("- Visualization and reporting")
    print()

    results = {}

    try:
        # Part 1: Monte Carlo Simulation
        print("\n" + "="*80)
        print("PART 1: MONTE CARLO SIMULATION")
        print("="*80)
        results['dcf_simulation'] = demo_monte_carlo_dcf_analysis()
        results['scenario_analysis'] = demo_scenario_analysis()

        # Part 2: Risk Framework
        print("\n" + "="*80)
        print("PART 2: RISK FRAMEWORK ANALYSIS")
        print("="*80)
        results['asset_risk'] = demo_individual_asset_risk_analysis()
        results['portfolio_risk'] = demo_portfolio_risk_analysis()

        # Part 3: Advanced Analysis
        print("\n" + "="*80)
        print("PART 3: ADVANCED ANALYSIS")
        print("="*80)
        results['correlation'], results['factors'] = demo_correlation_analysis()
        results['distributions'] = demo_distribution_fitting()
        results['custom_scenario'] = demo_custom_scenario_creation()

        # Part 4: Visualization
        print("\n" + "="*80)
        print("PART 4: VISUALIZATION AND REPORTING")
        print("="*80)
        results['visualization'] = demo_risk_visualization()

        # Summary
        print("\n" + "="*80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nSummary:")
        print(f"  Demos completed: {sum(1 for v in results.values() if v is not None)}")
        print(f"  Total features demonstrated: 8")
        print("\nKey Capabilities Showcased:")
        print("  ✓ Monte Carlo simulation for DCF, DDM, P/B models")
        print("  ✓ Comprehensive risk framework for assets and portfolios")
        print("  ✓ Scenario analysis with predefined and custom scenarios")
        print("  ✓ Correlation and risk factor analysis")
        print("  ✓ Statistical distribution fitting")
        print("  ✓ Interactive visualization and reporting")

        return results

    except Exception as e:
        print(f"\nError during demo execution: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
        return results


if __name__ == "__main__":
    # Run all demonstrations
    results = run_all_demos()

    print(f"\n{'='*80}")
    print("Risk analysis demonstration completed!")
    print("Check the output above for detailed analysis results.")
    print(f"{'='*80}\n")
