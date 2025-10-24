"""
Stress Testing Framework Example Usage
======================================

This example demonstrates how to use the comprehensive stress testing framework
for analyzing portfolio and asset performance under extreme market conditions.

Examples include:
- Running historical stress scenarios
- Creating custom stress tests
- Analyzing tail risk with extreme value theory
- Generating comprehensive stress test reports
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the stress testing framework
from core.analysis.risk.stress_testing_framework import (
    StressTestingFramework,
    HistoricalStressScenarios,
    HypotheticalStressScenarios,
    run_quick_stress_test,
    StressScenarioDefinition,
    StressScenarioType,
    ScenarioSeverity
)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def generate_sample_data():
    """Generate sample market data for demonstration."""
    np.random.seed(42)

    # Generate 3 years of daily returns with some market regimes
    n_days = 1095
    dates = pd.date_range(start='2021-01-01', periods=n_days, freq='D')

    # Create realistic return patterns with volatility clustering
    returns = []
    vol_regime = 0.015  # Base volatility

    for i in range(n_days):
        # Add regime changes to simulate market conditions
        if 200 <= i < 280:  # Crisis period (COVID-like)
            mean_return = -0.002
            vol_regime = 0.035
        elif 700 <= i < 730:  # Mini correction
            mean_return = -0.001
            vol_regime = 0.025
        elif 900 <= i < 950:  # Growth period
            mean_return = 0.0015
            vol_regime = 0.012
        else:  # Normal market
            mean_return = 0.0008
            vol_regime = 0.015

        # Add some autocorrelation in volatility
        if i > 0:
            vol_regime = 0.95 * vol_regime + 0.05 * np.random.exponential(0.015)

        daily_return = np.random.normal(mean_return, vol_regime)
        returns.append(daily_return)

    market_returns = pd.Series(returns, index=dates, name='market_returns')

    # Create sample portfolio data
    portfolio_data = {
        'equity_weight': 0.70,
        'bond_weight': 0.25,
        'cash_weight': 0.05,
        'base_volatility': 0.18,  # Annual volatility
        'holdings': [
            {'asset_id': 'AAPL', 'weight': 0.12, 'asset_type': 'equity', 'sector': 'technology'},
            {'asset_id': 'MSFT', 'weight': 0.10, 'asset_type': 'equity', 'sector': 'technology'},
            {'asset_id': 'GOOGL', 'weight': 0.08, 'asset_type': 'equity', 'sector': 'technology'},
            {'asset_id': 'AMZN', 'weight': 0.08, 'asset_type': 'equity', 'sector': 'technology'},
            {'asset_id': 'JPM', 'weight': 0.06, 'asset_type': 'equity', 'sector': 'financial'},
            {'asset_id': 'BAC', 'weight': 0.04, 'asset_type': 'equity', 'sector': 'financial'},
            {'asset_id': 'JNJ', 'weight': 0.06, 'asset_type': 'equity', 'sector': 'healthcare'},
            {'asset_id': 'PFE', 'weight': 0.04, 'asset_type': 'equity', 'sector': 'healthcare'},
            {'asset_id': 'XOM', 'weight': 0.04, 'asset_type': 'equity', 'sector': 'energy'},
            {'asset_id': 'CVX', 'weight': 0.03, 'asset_type': 'equity', 'sector': 'energy'},
            {'asset_id': 'KO', 'weight': 0.03, 'asset_type': 'equity', 'sector': 'consumer_staples'},
            {'asset_id': 'PG', 'weight': 0.02, 'asset_type': 'equity', 'sector': 'consumer_staples'},
            {'asset_id': 'BND', 'weight': 0.15, 'asset_type': 'bond'},
            {'asset_id': 'TLT', 'weight': 0.10, 'asset_type': 'bond'},
            {'asset_id': 'CASH', 'weight': 0.05, 'asset_type': 'cash'}
        ]
    }

    return market_returns, portfolio_data


def example_quick_stress_test():
    """Demonstrate the quick stress test functionality."""
    print("=" * 60)
    print("QUICK STRESS TEST EXAMPLE")
    print("=" * 60)

    # Generate sample data
    market_returns, _ = generate_sample_data()

    print(f"Testing with {len(market_returns)} days of market data")
    print(f"Sample period: {market_returns.index[0].date()} to {market_returns.index[-1].date()}")
    print(f"Mean daily return: {market_returns.mean():.4f}")
    print(f"Daily volatility: {market_returns.std():.4f}")
    print()

    # Run quick stress test with default scenarios
    print("Running quick stress test with default scenarios...")
    results = run_quick_stress_test(market_returns)

    print(f"\nStress test completed. Analyzed {len(results)} scenarios:")

    # Display results
    for scenario_name, result in results.items():
        print(f"\n📊 {scenario_name.upper()}:")
        print(f"   Portfolio Impact: {result.portfolio_value_impact:.2%}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Recovery Time: {result.time_to_recovery} months")
        print(f"   Scenario Type: {result.scenario_definition.scenario_type.value}")

        if result.var_change:
            var_95_change = result.var_change.get('var_95_change', 0)
            print(f"   VaR (95%) Change: {var_95_change:.4f}")


def example_comprehensive_stress_test():
    """Demonstrate comprehensive stress testing with all features."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE STRESS TEST EXAMPLE")
    print("=" * 60)

    # Generate sample data
    market_returns, portfolio_data = generate_sample_data()

    # Initialize stress testing framework
    framework = StressTestingFramework()

    print("🔧 Stress Testing Framework initialized")
    print(f"📈 Portfolio composition:")
    print(f"   Equity: {portfolio_data['equity_weight']:.0%}")
    print(f"   Bonds: {portfolio_data['bond_weight']:.0%}")
    print(f"   Cash: {portfolio_data['cash_weight']:.0%}")
    print(f"   Number of holdings: {len(portfolio_data['holdings'])}")
    print()

    # Run comprehensive stress test
    print("🚀 Running comprehensive stress test...")
    print("   - All historical scenarios")
    print("   - All hypothetical scenarios")
    print("   - Tail risk analysis (Extreme Value Theory)")
    print("   - Regime-switching analysis")
    print()

    results = framework.run_comprehensive_stress_test(
        portfolio_data=portfolio_data,
        asset_returns=market_returns,
        scenarios=None,  # Test all scenarios
        include_tail_analysis=True,
        include_regime_analysis=True
    )

    print(f"✅ Stress test completed! Analyzed {len(results)} scenarios")

    # Analyze results
    analyze_stress_test_results(results)

    # Generate comprehensive report
    print("\n📋 Generating comprehensive stress test report...")
    report = framework.generate_stress_test_report(results)
    display_stress_test_report(report)

    return results, framework


def example_custom_stress_scenario():
    """Demonstrate creating and testing custom stress scenarios."""
    print("\n" + "=" * 60)
    print("CUSTOM STRESS SCENARIO EXAMPLE")
    print("=" * 60)

    # Create a custom stress scenario
    custom_scenario = StressScenarioDefinition(
        name="Climate Change Impact",
        scenario_type=StressScenarioType.HYPOTHETICAL_EXTREME,
        severity=ScenarioSeverity.SEVERE,
        description="Severe climate event causing global economic disruption",
        equity_shock=-0.28,  # 28% equity decline
        bond_shock=0.12,     # Flight to safety
        volatility_multiplier=2.8,
        correlation_shift=0.35,
        gdp_shock=-0.02,
        commodity_shock=0.30,  # Commodity price spike
        duration_months=8,
        recovery_months=30,
        probability=0.012,
        data_source="Climate risk models and IPCC scenarios"
    )

    print(f"🌍 Custom Scenario Created: {custom_scenario.name}")
    print(f"   Description: {custom_scenario.description}")
    print(f"   Equity Shock: {custom_scenario.equity_shock:.1%}")
    print(f"   Duration: {custom_scenario.duration_months} months")
    print(f"   Recovery: {custom_scenario.recovery_months} months")
    print(f"   Annual Probability: {custom_scenario.probability:.1%}")
    print()

    # Generate sample data
    market_returns, portfolio_data = generate_sample_data()

    # Initialize framework and add custom scenario
    framework = StressTestingFramework()
    framework.hypothetical_scenarios["climate_change"] = custom_scenario

    # Test the custom scenario
    print("🧪 Testing custom scenario...")
    results = framework.run_comprehensive_stress_test(
        portfolio_data=portfolio_data,
        asset_returns=market_returns,
        scenarios=["climate_change"],
        include_tail_analysis=False,
        include_regime_analysis=False
    )

    # Display results
    if "climate_change" in results:
        result = results["climate_change"]
        print(f"\n📊 Custom Scenario Results:")
        print(f"   Portfolio Value Impact: {result.portfolio_value_impact:.2%}")
        print(f"   Maximum Drawdown: {result.max_drawdown:.2%}")
        print(f"   Estimated Recovery Time: {result.time_to_recovery} months")

        # Show sector impacts
        if result.sector_impacts:
            print(f"\n   Sector-Level Impacts:")
            for sector, impact in result.sector_impacts.items():
                print(f"     {sector.title()}: {impact:.2%}")


def example_tail_risk_analysis():
    """Demonstrate extreme value theory and tail risk analysis."""
    print("\n" + "=" * 60)
    print("TAIL RISK ANALYSIS EXAMPLE")
    print("=" * 60)

    # Generate sample data with fat tails
    market_returns, _ = generate_sample_data()

    # Add some extreme events to demonstrate tail analysis
    np.random.seed(123)
    extreme_dates = np.random.choice(market_returns.index, 15, replace=False)
    for date in extreme_dates:
        if np.random.rand() > 0.5:
            market_returns.loc[date] = -0.08  # Extreme loss
        else:
            market_returns.loc[date] = 0.06   # Extreme gain

    print(f"📊 Analyzing tail risk for {len(market_returns)} observations")
    print(f"📉 Added {len(extreme_dates)} extreme events for demonstration")
    print()

    # Initialize framework
    framework = StressTestingFramework()

    # Run tail risk analysis
    print("🔍 Performing Extreme Value Theory analysis...")
    tail_metrics = framework.evt_analyzer.analyze_tail_risk(market_returns)

    print(f"\n📈 Tail Risk Analysis Results:")
    print(f"   Threshold (95th percentile): {tail_metrics.threshold:.4f}")
    print(f"   Extreme Event Probability: {tail_metrics.extreme_event_probability:.2%}")
    print(f"   Tail Index: {tail_metrics.tail_index:.3f}")
    print(f"   Number of Exceedances: {len(tail_metrics.exceedances)}")

    print(f"\n🎯 Tail VaR Estimates:")
    for level, var_estimate in tail_metrics.tail_var_estimates.items():
        cvar_estimate = tail_metrics.tail_cvar_estimates.get(level, 0)
        print(f"   {level}: VaR = {var_estimate:.4f}, CVaR = {cvar_estimate:.4f}")

    # Show extreme value distribution parameters
    if tail_metrics.extreme_value_params:
        print(f"\n🔧 Extreme Value Distribution Parameters:")
        for param, value in tail_metrics.extreme_value_params.items():
            print(f"   {param.title()}: {value:.4f}")


def analyze_stress_test_results(results):
    """Analyze and display stress test results."""
    print(f"\n📊 STRESS TEST RESULTS ANALYSIS")
    print("-" * 40)

    # Sort results by impact severity
    sorted_results = sorted(
        results.items(),
        key=lambda x: abs(x[1].portfolio_value_impact),
        reverse=True
    )

    print(f"🔴 TOP 5 MOST SEVERE SCENARIOS:")
    for i, (scenario_name, result) in enumerate(sorted_results[:5], 1):
        print(f"   {i}. {scenario_name}")
        print(f"      Impact: {result.portfolio_value_impact:.2%}")
        print(f"      Max Drawdown: {result.max_drawdown:.2%}")
        print(f"      Recovery: {result.time_to_recovery} months")
        print(f"      Type: {result.scenario_definition.scenario_type.value}")
        print()

    # Calculate summary statistics
    impacts = [result.portfolio_value_impact for result in results.values()]
    drawdowns = [result.max_drawdown for result in results.values()]
    recovery_times = [result.time_to_recovery for result in results.values() if result.time_to_recovery]

    print(f"📈 SUMMARY STATISTICS:")
    print(f"   Average Impact: {np.mean(impacts):.2%}")
    print(f"   Worst Case Impact: {np.min(impacts):.2%}")
    print(f"   Average Max Drawdown: {np.mean(drawdowns):.2%}")
    print(f"   Average Recovery Time: {np.mean(recovery_times):.1f} months")

    # Count scenario types
    scenario_types = {}
    for result in results.values():
        scenario_type = result.scenario_definition.scenario_type.value
        scenario_types[scenario_type] = scenario_types.get(scenario_type, 0) + 1

    print(f"\n🏷️  SCENARIO BREAKDOWN:")
    for scenario_type, count in scenario_types.items():
        print(f"   {scenario_type.title()}: {count} scenarios")


def display_stress_test_report(report):
    """Display formatted stress test report."""
    print(f"\n📋 COMPREHENSIVE STRESS TEST REPORT")
    print("=" * 50)

    # Executive Summary
    exec_summary = report['executive_summary']
    print(f"📅 Analysis Date: {exec_summary['analysis_date']}")
    print(f"📊 Total Scenarios: {exec_summary['total_scenarios']}")
    print(f"🔴 Worst Case Scenario: {exec_summary['worst_case_scenario']}")
    print(f"💥 Maximum Loss: {exec_summary['maximum_loss']:.2%}")

    # Risk Ranking
    if 'risk_ranking' in report and report['risk_ranking']:
        print(f"\n🥇 RISK RANKING (Top 5):")
        for rank_info in report['risk_ranking'][:5]:
            print(f"   {rank_info['rank']}. {rank_info['scenario']}")
            print(f"      Impact: {rank_info['impact']:.2%}")
            print(f"      Probability: {rank_info['probability']:.1%}")

    # Recommendations
    if 'recommendations' in report and report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"   {i}. {recommendation}")


def example_scenario_comparison():
    """Compare different types of stress scenarios."""
    print("\n" + "=" * 60)
    print("SCENARIO COMPARISON EXAMPLE")
    print("=" * 60)

    # Generate sample data
    market_returns, portfolio_data = generate_sample_data()

    # Initialize framework
    framework = StressTestingFramework()

    # Compare specific scenarios
    comparison_scenarios = [
        "financial_crisis_2008",
        "covid19_pandemic",
        "dotcom_crash",
        "extreme_inflation",
        "geopolitical_crisis"
    ]

    print(f"🔍 Comparing {len(comparison_scenarios)} stress scenarios:")
    for scenario in comparison_scenarios:
        print(f"   - {scenario}")
    print()

    # Run comparison
    results = framework.run_comprehensive_stress_test(
        portfolio_data=portfolio_data,
        asset_returns=market_returns,
        scenarios=comparison_scenarios,
        include_tail_analysis=False,
        include_regime_analysis=False
    )

    # Create comparison table
    comparison_data = []
    for scenario_name in comparison_scenarios:
        if scenario_name in results:
            result = results[scenario_name]
            comparison_data.append({
                'Scenario': scenario_name.replace('_', ' ').title(),
                'Type': result.scenario_definition.scenario_type.value.title(),
                'Portfolio Impact': f"{result.portfolio_value_impact:.2%}",
                'Max Drawdown': f"{result.max_drawdown:.2%}",
                'Recovery (months)': result.time_to_recovery,
                'Annual Probability': f"{result.scenario_definition.probability:.2%}",
                'Severity': result.scenario_definition.severity.value[1]
            })

    # Display comparison table
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        print("📊 SCENARIO COMPARISON TABLE:")
        print(df.to_string(index=False))

        # Show insights
        print(f"\n🔍 KEY INSIGHTS:")

        # Find worst impact
        impacts = [float(row['Portfolio Impact'].rstrip('%'))/100 for row in comparison_data]
        worst_idx = np.argmin(impacts)
        print(f"   • Most severe: {comparison_data[worst_idx]['Scenario']}")

        # Find longest recovery
        recoveries = [row['Recovery (months)'] for row in comparison_data]
        longest_recovery_idx = np.argmax(recoveries)
        print(f"   • Longest recovery: {comparison_data[longest_recovery_idx]['Scenario']}")

        # Find highest probability
        probs = [float(row['Annual Probability'].rstrip('%'))/100 for row in comparison_data]
        highest_prob_idx = np.argmax(probs)
        print(f"   • Highest probability: {comparison_data[highest_prob_idx]['Scenario']}")


def main():
    """Run all stress testing examples."""
    print("🚀 STRESS TESTING FRAMEWORK DEMONSTRATION")
    print("==========================================")
    print("This demonstration shows comprehensive stress testing capabilities")
    print("including historical scenarios, tail risk analysis, and custom scenarios.")
    print()

    try:
        # Run examples
        example_quick_stress_test()

        results, framework = example_comprehensive_stress_test()

        example_custom_stress_scenario()

        example_tail_risk_analysis()

        example_scenario_comparison()

        print("\n" + "=" * 60)
        print("✅ ALL STRESS TESTING EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("🎯 Key Features Demonstrated:")
        print("   ✓ Historical stress scenarios (2008 crisis, COVID-19, etc.)")
        print("   ✓ Hypothetical extreme scenarios")
        print("   ✓ Extreme Value Theory tail risk analysis")
        print("   ✓ Regime-switching models")
        print("   ✓ Custom scenario creation")
        print("   ✓ Comprehensive reporting")
        print("   ✓ Scenario comparison analysis")
        print()
        print("📚 The stress testing framework is ready for production use!")

        return results, framework

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    results, framework = main()