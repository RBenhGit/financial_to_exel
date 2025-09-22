"""
Risk Analysis Framework Usage Examples
=====================================

This module demonstrates how to use the comprehensive risk analysis framework
for financial risk assessment, including market risk, credit risk, operational risk,
and liquidity risk analysis.

Examples include:
- Basic risk assessment
- Comprehensive risk analysis
- Multi-asset risk comparison
- Risk dashboard generation
- Custom scenario analysis
- Distribution fitting
- Correlation analysis

Run this file to see practical examples of risk analysis in action.
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import risk analysis components
    from core.analysis.risk import (
        # Main engines
        IntegratedRiskEngine,
        RiskAnalysisRequest,
        create_default_risk_engine,
        quick_risk_assessment,
        compare_risk_profiles,

        # Risk types and metrics
        RiskType,
        AnalysisScope,
        RiskDimension,

        # Specialized analyzers
        IntegratedRiskTypeFramework,
        MarketRiskAnalyzer,
        CreditRiskAnalyzer,

        # Statistical models
        DistributionFitter,
        NormalDistribution,
        StudentTDistribution,

        # Scenario modeling
        ScenarioModelingFramework,
        PredefinedScenarios,

        # Correlation analysis
        CorrelationAnalyzer,
        CorrelationMethod
    )

    # Try to import financial calculator
    try:
        from core.analysis.engines.financial_calculations import FinancialCalculator
        HAS_FINANCIAL_CALCULATOR = True
    except ImportError:
        HAS_FINANCIAL_CALCULATOR = False
        print("Warning: FinancialCalculator not available. Using simulated data.")

except ImportError as e:
    print(f"Error importing risk analysis components: {e}")
    print("Please ensure the risk analysis framework is properly installed.")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_sample_returns_data(assets: list, periods: int = 252) -> pd.DataFrame:
    """Generate sample returns data for demonstration purposes."""
    np.random.seed(42)  # For reproducible results

    data = {}
    for asset in assets:
        # Generate correlated returns with different volatilities
        if asset == 'AAPL':
            returns = np.random.normal(0.0008, 0.02, periods)  # Higher volatility
        elif asset == 'MSFT':
            returns = np.random.normal(0.0006, 0.015, periods)  # Moderate volatility
        elif asset == 'GOOGL':
            returns = np.random.normal(0.0007, 0.018, periods)  # Higher volatility
        elif asset == 'SPY':
            returns = np.random.normal(0.0005, 0.012, periods)  # Lower volatility (market)
        else:
            returns = np.random.normal(0.0005, 0.016, periods)  # Default

        data[asset] = returns

    dates = pd.date_range(start='2023-01-01', periods=periods, freq='D')
    return pd.DataFrame(data, index=dates)


def example_1_basic_risk_assessment():
    """Example 1: Basic risk assessment for a single asset."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Risk Assessment")
    print("="*60)

    try:
        # Create financial calculator if available
        if HAS_FINANCIAL_CALCULATOR:
            calc = FinancialCalculator('AAPL')
        else:
            calc = None

        # Perform quick risk assessment
        logger.info("Performing quick risk assessment for AAPL...")
        risk_summary = quick_risk_assessment('AAPL', calc, risk_types=[RiskType.MARKET])

        print(f"\nRisk Assessment Results for AAPL:")
        print(f"Overall Risk Score: {risk_summary.get('overall_risk_score', 'N/A'):.1f}")
        print(f"Risk Level: {risk_summary.get('risk_level', 'Unknown')}")
        print(f"Key Risk Drivers: {', '.join(risk_summary.get('key_risk_drivers', ['None']))}")
        print(f"Analysis Date: {risk_summary.get('analysis_date', 'N/A')}")

        if 'risk_metrics' in risk_summary:
            metrics = risk_summary['risk_metrics']
            print(f"\nDetailed Risk Metrics:")
            print(f"VaR (95%): {metrics.get('var_95', 'N/A')}")
            print(f"Annual Volatility: {metrics.get('annual_volatility', 'N/A')}")
            print(f"Max Drawdown: {metrics.get('max_drawdown', 'N/A')}")
            print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")

    except Exception as e:
        print(f"Error in basic risk assessment: {e}")


def example_2_comprehensive_risk_analysis():
    """Example 2: Comprehensive risk analysis with custom request."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Comprehensive Risk Analysis")
    print("="*60)

    try:
        # Create risk engine
        logger.info("Creating comprehensive risk analysis engine...")
        risk_engine = create_default_risk_engine()

        # Create comprehensive analysis request
        request = RiskAnalysisRequest(
            asset_ids=['AAPL'],
            analysis_scope=AnalysisScope.COMPREHENSIVE,
            risk_types=[RiskType.MARKET, RiskType.CREDIT, RiskType.LIQUIDITY],
            risk_dimensions=[
                RiskDimension.STATISTICAL,
                RiskDimension.CORRELATION,
                RiskDimension.SCENARIO,
                RiskDimension.DISTRIBUTION
            ],
            confidence_levels=[0.95, 0.99],
            monte_carlo_runs=5000,
            fit_distributions=True,
            include_scenarios=True,
            scenario_names=['Base Case', 'Pessimistic Case', 'COVID-19 Pandemic']
        )

        # Perform comprehensive analysis
        logger.info("Running comprehensive risk analysis...")
        result = risk_engine.analyze_risk(request)

        print(f"\nComprehensive Risk Analysis Results:")
        print(f"Analysis ID: {result.analysis_id}")
        print(f"Overall Risk Score: {result.overall_risk_score:.1f}")
        print(f"Risk Level: {result.risk_level.level_name if result.risk_level else 'Unknown'}")
        print(f"Calculation Time: {result.calculation_time:.2f} seconds")

        # Display key risk drivers
        if result.key_risk_drivers:
            print(f"\nKey Risk Drivers:")
            for i, driver in enumerate(result.key_risk_drivers, 1):
                print(f"  {i}. {driver}")

        # Display scenario results
        if result.scenario_results:
            print(f"\nScenario Analysis Results:")
            for scenario_name, scenario_data in result.scenario_results.items():
                print(f"  Scenario: {scenario_name}")
                severity = scenario_data.get('severity', 'Unknown')
                print(f"    Severity Level: {severity}")

                portfolio_analysis = scenario_data.get('portfolio_analysis', {})
                if portfolio_analysis:
                    total_return = portfolio_analysis.get('total_return', {})
                    mean_return = total_return.get('mean', 0)
                    max_loss = total_return.get('max_loss', 0)
                    print(f"    Expected Impact: {mean_return:.2%}")
                    print(f"    Worst Case Loss: {max_loss:.2%}")

        # Generate comprehensive report
        logger.info("Generating comprehensive report...")
        report = risk_engine.generate_comprehensive_report(result.analysis_id)

        # Export report to Excel (if openpyxl is available)
        try:
            report_path = "risk_analysis_report.xlsx"
            report.export_to_excel(report_path)
            print(f"\nComprehensive report exported to: {report_path}")
        except Exception as e:
            logger.warning(f"Could not export Excel report: {e}")

        # Export report to JSON
        try:
            json_path = "risk_analysis_report.json"
            report.export_to_json(json_path)
            print(f"Report also exported to JSON: {json_path}")
        except Exception as e:
            logger.warning(f"Could not export JSON report: {e}")

    except Exception as e:
        print(f"Error in comprehensive risk analysis: {e}")
        logger.error(f"Comprehensive analysis failed: {e}")


def example_3_multi_asset_comparison():
    """Example 3: Multi-asset risk comparison."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Multi-Asset Risk Comparison")
    print("="*60)

    try:
        # Define assets to compare
        assets = ['AAPL', 'MSFT', 'GOOGL', 'SPY']

        # Create financial calculator if available
        if HAS_FINANCIAL_CALCULATOR:
            calc = FinancialCalculator()
        else:
            calc = None

        # Compare risk profiles
        logger.info(f"Comparing risk profiles for {len(assets)} assets...")
        comparison_df = compare_risk_profiles(assets, calc)

        print(f"\nRisk Profile Comparison:")
        print("=" * 80)

        # Display comparison table
        display_columns = ['asset_id', 'overall_risk_score', 'risk_level']
        if not comparison_df.empty:
            for col in display_columns:
                if col in comparison_df.columns:
                    print(f"{col:<20}", end="")
            print()
            print("-" * 80)

            for _, row in comparison_df.iterrows():
                for col in display_columns:
                    if col in comparison_df.columns:
                        value = row[col]
                        if col == 'overall_risk_score' and pd.notna(value):
                            print(f"{value:<20.1f}", end="")
                        else:
                            print(f"{str(value):<20}", end="")
                print()

        # Generate risk dashboard
        logger.info("Generating risk dashboard...")
        dashboard = risk_engine.generate_risk_dashboard(assets, calc, 'risk_dashboard.json')

        if 'error' not in dashboard:
            print(f"\nRisk Dashboard Generated:")
            print(f"  Assets Analyzed: {dashboard['metadata']['assets_analyzed']}")
            print(f"  Generation Time: {dashboard['metadata']['generation_time']}")

            if dashboard['summary_statistics']:
                stats = dashboard['summary_statistics']
                print(f"  Average Risk Score: {stats.get('avg_risk_score', 'N/A')}")
                print(f"  Highest Risk Asset: {stats.get('highest_risk_asset', 'N/A')}")
                print(f"  Lowest Risk Asset: {stats.get('lowest_risk_asset', 'N/A')}")
        else:
            print(f"Dashboard generation failed: {dashboard['error']}")

    except Exception as e:
        print(f"Error in multi-asset comparison: {e}")
        logger.error(f"Multi-asset comparison failed: {e}")


def example_4_specialized_risk_analysis():
    """Example 4: Specialized risk type analysis."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Specialized Risk Type Analysis")
    print("="*60)

    try:
        # Create specialized risk framework
        if HAS_FINANCIAL_CALCULATOR:
            calc = FinancialCalculator('AAPL')
            risk_framework = IntegratedRiskTypeFramework(calc)
        else:
            risk_framework = IntegratedRiskTypeFramework()

        asset_id = 'AAPL'

        # Analyze market risk
        logger.info(f"Analyzing market risk for {asset_id}...")
        try:
            market_risk = risk_framework.analyze_market_risk(asset_id, benchmark_id='SPY')

            print(f"\nMarket Risk Analysis for {asset_id}:")
            print(f"  Market Risk Score: {market_risk.market_risk_score():.1f}")
            print(f"  Beta: {market_risk.beta or 'N/A'}")
            print(f"  Alpha (Annualized): {market_risk.alpha or 'N/A'}")
            print(f"  R-Squared: {market_risk.r_squared or 'N/A'}")
            print(f"  Tracking Error: {market_risk.tracking_error or 'N/A'}")
            print(f"  VaR (95%): {market_risk.var_1day_95 or 'N/A'}")
            print(f"  Annual Volatility: {market_risk.realized_volatility or 'N/A'}")

        except Exception as e:
            print(f"Market risk analysis failed: {e}")

        # Analyze credit risk
        logger.info(f"Analyzing credit risk for {asset_id}...")
        try:
            credit_risk = risk_framework.analyze_credit_risk(asset_id)

            print(f"\nCredit Risk Analysis for {asset_id}:")
            print(f"  Credit Risk Score: {credit_risk.credit_risk_score():.1f}")
            print(f"  Credit Rating: {credit_risk.credit_rating or 'N/A'}")
            print(f"  Credit Score: {credit_risk.credit_score or 'N/A'}")
            print(f"  Default Probability (1Y): {credit_risk.probability_of_default_1y or 'N/A'}")
            print(f"  Debt-to-Equity: {credit_risk.debt_to_equity or 'N/A'}")
            print(f"  Interest Coverage: {credit_risk.interest_coverage or 'N/A'}")

        except Exception as e:
            print(f"Credit risk analysis failed: {e}")

        # Generate composite risk report
        logger.info("Generating composite risk report...")
        try:
            risk_report = risk_framework.generate_risk_type_report(asset_id)

            if 'error' not in risk_report:
                print(f"\nComposite Risk Report for {asset_id}:")
                print(f"  Composite Risk Score: {risk_report.get('composite_risk_score', 'N/A'):.1f}")
                print(f"  Analysis Date: {risk_report.get('analysis_date', 'N/A')}")

                risk_analysis = risk_report.get('risk_type_analysis', {})
                for risk_type, analysis in risk_analysis.items():
                    print(f"  {risk_type.title()} Risk Score: {analysis.get('risk_score', 'N/A'):.1f}")
            else:
                print(f"Risk report generation failed: {risk_report['error']}")

        except Exception as e:
            print(f"Composite risk report failed: {e}")

    except Exception as e:
        print(f"Error in specialized risk analysis: {e}")
        logger.error(f"Specialized risk analysis failed: {e}")


def example_5_distribution_fitting():
    """Example 5: Distribution fitting and statistical modeling."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Distribution Fitting and Statistical Modeling")
    print("="*60)

    try:
        # Generate sample returns data
        logger.info("Generating sample returns data...")
        assets = ['AAPL', 'MSFT', 'GOOGL']
        returns_data = generate_sample_returns_data(assets, periods=500)

        # Create distribution fitter
        fitter = DistributionFitter()

        for asset in assets:
            print(f"\nDistribution Analysis for {asset}:")
            print("-" * 40)

            asset_returns = returns_data[asset].dropna()

            # Fit multiple distributions
            fitted_distributions = fitter.fit_all_distributions(asset_returns)

            if fitted_distributions:
                print(f"Successfully fitted {len(fitted_distributions)} distributions")

                # Find best distribution
                best_dist = fitter.fit_best_distribution(asset_returns, criterion='aic')

                print(f"Best Distribution: {best_dist.distribution_type.value}")
                print(f"Distribution Parameters: {best_dist.parameters.parameters}")

                # Calculate risk metrics using fitted distribution
                var_95 = best_dist.var(0.05)
                var_99 = best_dist.var(0.01)
                mean = best_dist.mean()
                std = best_dist.std()

                print(f"Fitted Distribution Metrics:")
                print(f"  Mean: {mean:.4f}")
                print(f"  Std Dev: {std:.4f}")
                print(f"  VaR (95%): {var_95:.4f}")
                print(f"  VaR (99%): {var_99:.4f}")
                print(f"  Skewness: {best_dist.skewness():.4f}")
                print(f"  Kurtosis: {best_dist.kurtosis():.4f}")
                print(f"  Tail Behavior: {best_dist.tail_behavior().value}")

                # Compare with historical metrics
                hist_mean = asset_returns.mean()
                hist_std = asset_returns.std()
                hist_var_95 = np.percentile(asset_returns, 5)

                print(f"Historical Metrics (for comparison):")
                print(f"  Mean: {hist_mean:.4f}")
                print(f"  Std Dev: {hist_std:.4f}")
                print(f"  VaR (95%): {hist_var_95:.4f}")
            else:
                print("No distributions could be fitted")

        # Get distribution comparison table
        if hasattr(fitter, 'get_distribution_comparison'):
            try:
                comparison_table = fitter.get_distribution_comparison()
                if not comparison_table.empty:
                    print(f"\nDistribution Comparison Table:")
                    print(comparison_table.to_string(index=False))
            except Exception as e:
                logger.warning(f"Could not generate distribution comparison: {e}")

    except Exception as e:
        print(f"Error in distribution fitting: {e}")
        logger.error(f"Distribution fitting failed: {e}")


def example_6_scenario_analysis():
    """Example 6: Custom scenario analysis."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Scenario Analysis")
    print("="*60)

    try:
        # Create scenario modeling framework
        scenario_framework = ScenarioModelingFramework()

        # List available predefined scenarios
        available_scenarios = scenario_framework.list_scenarios()
        print(f"\nAvailable Predefined Scenarios ({len(available_scenarios)}):")
        for i, scenario_name in enumerate(available_scenarios[:10], 1):  # Show first 10
            print(f"  {i}. {scenario_name}")

        # Run scenario analysis on selected scenarios
        selected_scenarios = available_scenarios[:5]  # First 5 scenarios

        # Create sample portfolio data
        portfolio_data = {
            'equity_weight': 0.6,
            'bond_weight': 0.4,
            'base_volatility': 0.15
        }

        logger.info(f"Running scenario analysis on {len(selected_scenarios)} scenarios...")
        scenario_results = scenario_framework.run_scenario_analysis(
            scenario_names=selected_scenarios,
            portfolio_data=portfolio_data,
            monte_carlo_runs=1000
        )

        print(f"\nScenario Analysis Results:")
        print("=" * 60)

        for scenario_name, result in scenario_results.items():
            print(f"\nScenario: {scenario_name}")
            print(f"  Type: {result.get('scenario_type', 'Unknown')}")
            print(f"  Severity: {result.get('severity', 'Unknown')}")
            print(f"  Runs: {result.get('runs', 'Unknown')}")
            print(f"  Probability: {result.get('scenario_probability', 'N/A')}")

            portfolio_analysis = result.get('portfolio_analysis', {})
            if portfolio_analysis:
                total_return = portfolio_analysis.get('total_return', {})
                print(f"  Expected Return: {total_return.get('mean', 0):.2%}")
                print(f"  Volatility: {total_return.get('std', 0):.2%}")
                print(f"  VaR (95%): {total_return.get('var_95', 0):.2%}")
                print(f"  Max Loss: {total_return.get('max_loss', 0):.2%}")
                print(f"  Probability of Loss: {total_return.get('probability_of_loss', 0):.1%}")

        # Compare scenarios
        logger.info("Generating scenario comparison...")
        try:
            comparison_df = scenario_framework.compare_scenarios(
                selected_scenarios,
                comparison_metrics=['severity', 'max_loss', 'var_95']
            )

            if not comparison_df.empty:
                print(f"\nScenario Comparison:")
                print(comparison_df.to_string(index=False))
        except Exception as e:
            logger.warning(f"Scenario comparison failed: {e}")

    except Exception as e:
        print(f"Error in scenario analysis: {e}")
        logger.error(f"Scenario analysis failed: {e}")


def example_7_correlation_analysis():
    """Example 7: Correlation and factor analysis."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Correlation and Factor Analysis")
    print("="*60)

    try:
        # Generate sample returns data for correlation analysis
        assets = ['AAPL', 'MSFT', 'GOOGL', 'SPY', 'QQQ']
        logger.info(f"Generating correlated returns data for {len(assets)} assets...")
        returns_data = generate_sample_returns_data(assets, periods=252)

        # Create correlation analyzer
        correlation_analyzer = CorrelationAnalyzer(returns_data)

        # Calculate correlation matrices using different methods
        methods = [CorrelationMethod.PEARSON, CorrelationMethod.SPEARMAN]

        for method in methods:
            print(f"\nCorrelation Analysis - {method.value.title()} Method:")
            print("-" * 50)

            try:
                corr_matrix = correlation_analyzer.calculate_correlation_matrix(
                    method=method,
                    min_periods=30
                )

                print(f"Correlation Matrix ({corr_matrix.assets}):")
                corr_df = corr_matrix.to_dataframe()
                print(corr_df.round(3).to_string())

                # Analyze correlation properties
                print(f"\nCorrelation Analysis:")
                print(f"  Market Concentration: {corr_matrix.market_concentration():.3f}")
                print(f"  Stability Score: {corr_matrix.stability_score:.3f}")

                # Identify highly correlated pairs
                high_corr_pairs = corr_matrix.identify_highly_correlated_pairs(threshold=0.5)
                if high_corr_pairs:
                    print(f"  Highly Correlated Pairs (>0.5):")
                    for asset1, asset2, correlation in high_corr_pairs[:5]:  # Top 5
                        print(f"    {asset1} - {asset2}: {correlation:.3f}")

                # Perform hierarchical clustering
                try:
                    clusters = corr_matrix.hierarchical_clustering(n_clusters=3)
                    print(f"  Asset Clusters:")
                    cluster_groups = {}
                    for asset, cluster_id in clusters.items():
                        if cluster_id not in cluster_groups:
                            cluster_groups[cluster_id] = []
                        cluster_groups[cluster_id].append(asset)

                    for cluster_id, assets_in_cluster in cluster_groups.items():
                        print(f"    Cluster {cluster_id}: {', '.join(assets_in_cluster)}")

                except Exception as e:
                    logger.warning(f"Clustering analysis failed: {e}")

            except Exception as e:
                print(f"Correlation analysis failed for {method.value}: {e}")

        # Perform rolling correlation analysis
        try:
            print(f"\nRolling Correlation Analysis:")
            print("-" * 30)

            stability_analysis = correlation_analyzer.rolling_correlation_analysis(
                window=60,
                step=10
            )

            print(f"Correlation Trend: {stability_analysis['correlation_trend']:.6f}")
            print(f"Volatility Trend: {stability_analysis['volatility_trend']:.6f}")
            print(f"Average Correlation: {stability_analysis['avg_correlation']:.3f}")
            print(f"Correlation Volatility: {stability_analysis['correlation_volatility']:.3f}")

            regime_changes = stability_analysis.get('regime_changes', [])
            if regime_changes:
                print(f"Regime Changes Detected: {len(regime_changes)}")
                for change in regime_changes[-3:]:  # Last 3 changes
                    print(f"  {change['date'].strftime('%Y-%m-%d')}: {change['regime']} ({change['level']:.3f})")

        except Exception as e:
            logger.warning(f"Rolling correlation analysis failed: {e}")

        # Perform risk factor identification
        try:
            print(f"\nRisk Factor Analysis:")
            print("-" * 25)

            risk_factors = correlation_analyzer.identify_risk_factors(
                method='pca',
                n_factors=3
            )

            if risk_factors and risk_factors.explained_variance is not None:
                print("Factor Explained Variance:")
                for factor, variance in risk_factors.explained_variance.items():
                    print(f"  {factor}: {variance:.3f} ({variance*100:.1f}%)")

                total_explained = risk_factors.explained_variance.sum()
                print(f"  Total Explained: {total_explained:.3f} ({total_explained*100:.1f}%)")

            if risk_factors and risk_factors.identified_factors:
                print("Identified Risk Factors:")
                for factor_type, factor_info in risk_factors.identified_factors.items():
                    print(f"  {factor_type.value}: {factor_info['factor_name']}")
                    print(f"    Explained Variance: {factor_info['explained_variance']:.3f}")
                    print(f"    Factor Strength: {factor_info['factor_strength']:.3f}")

        except Exception as e:
            logger.warning(f"Risk factor analysis failed: {e}")

    except Exception as e:
        print(f"Error in correlation analysis: {e}")
        logger.error(f"Correlation analysis failed: {e}")


def run_all_examples():
    """Run all risk analysis examples."""
    print("COMPREHENSIVE RISK ANALYSIS FRAMEWORK - EXAMPLES")
    print("=" * 60)
    print("This script demonstrates the capabilities of the risk analysis framework")
    print("including market risk, credit risk, distribution fitting, scenario analysis,")
    print("and correlation analysis.")
    print()

    examples = [
        ("Basic Risk Assessment", example_1_basic_risk_assessment),
        ("Comprehensive Risk Analysis", example_2_comprehensive_risk_analysis),
        ("Multi-Asset Comparison", example_3_multi_asset_comparison),
        ("Specialized Risk Analysis", example_4_specialized_risk_analysis),
        ("Distribution Fitting", example_5_distribution_fitting),
        ("Scenario Analysis", example_6_scenario_analysis),
        ("Correlation Analysis", example_7_correlation_analysis)
    ]

    for name, example_func in examples:
        try:
            print(f"\nRunning: {name}")
            example_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
            logger.error(f"Example {name} failed: {e}")

        # Add pause between examples
        print("\n" + "-"*60 + "\n")

    print("All examples completed!")
    print("\nGenerated files:")
    print("- risk_analysis_report.xlsx (if openpyxl available)")
    print("- risk_analysis_report.json")
    print("- risk_dashboard.json")
    print("\nCheck these files for detailed analysis results.")


if __name__ == "__main__":
    run_all_examples()