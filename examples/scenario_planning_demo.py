"""
Comprehensive Scenario Planning and Sensitivity Analysis Demo
============================================================

This demo script showcases the unified scenario planning interface that integrates
all existing scenario analysis capabilities of the financial analysis framework.

Features Demonstrated:
- Unified scenario planning interface
- Integration of scenario modeling, sensitivity analysis, and Monte Carlo simulation
- Multiple valuation methods (DCF, DDM, P/B)
- Custom scenario creation and three-point analysis
- Automated recommendations and risk assessment
- Interactive visualization capabilities

Usage:
python examples/scenario_planning_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Import the unified scenario planning interface
    from core.analysis.scenario_planning_interface import (
        UnifiedScenarioPlanner,
        ScenarioPlanningConfig,
        AnalysisScope,
        quick_scenario_planning_analysis,
        create_economic_scenario_comparison
    )
    from core.analysis.engines.financial_calculations import FinancialCalculator

    print("✅ Successfully imported unified scenario planning components")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed and the project structure is correct")
    sys.exit(1)


def demonstrate_basic_scenario_analysis(ticker: str = "AAPL"):
    """Demonstrate basic scenario planning analysis."""
    print(f"\n{'='*60}")
    print("BASIC SCENARIO PLANNING ANALYSIS")
    print(f"{'='*60}")

    try:
        # Initialize financial calculator
        calc = FinancialCalculator(ticker)
        planner = UnifiedScenarioPlanner(calc)

        print(f"📊 Running basic scenario analysis for {ticker}...")

        # Run basic analysis
        result = planner.run_comprehensive_scenario_analysis(
            scenarios=['Base Case', 'Optimistic Case', 'Pessimistic Case'],
            valuation_methods=['dcf'],
            include_sensitivity=False,
            include_monte_carlo=False,
            analysis_scope=AnalysisScope.BASIC
        )

        # Display results
        print(f"\n🎯 Expected DCF Value: ${result.expected_value:.2f}")
        print(f"📈 95% Confidence Interval: ${result.confidence_interval_95[0]:.2f} - ${result.confidence_interval_95[1]:.2f}")
        print(f"📉 Downside Risk: ${result.scenario_results['dcf'].downside_risk:.2f}")
        print(f"📈 Upside Potential: ${result.scenario_results['dcf'].upside_potential:.2f}")

        # Show scenario breakdown
        print(f"\n📋 Scenario Breakdown:")
        for scenario_name, value in result.scenario_results['dcf'].scenario_values.items():
            probability = result.scenario_results['dcf'].probabilities[scenario_name]
            print(f"  {scenario_name}: ${value:.2f} (Probability: {probability:.1%})")

        print("✅ Basic scenario analysis completed successfully")
        return result

    except Exception as e:
        print(f"❌ Basic scenario analysis failed: {e}")
        return None


def demonstrate_comprehensive_scenario_analysis(ticker: str = "AAPL"):
    """Demonstrate comprehensive scenario planning with sensitivity and Monte Carlo."""
    print(f"\n{'='*60}")
    print("COMPREHENSIVE SCENARIO PLANNING ANALYSIS")
    print(f"{'='*60}")

    try:
        # Initialize components
        calc = FinancialCalculator(ticker)
        planner = UnifiedScenarioPlanner(calc)

        print(f"🔬 Running comprehensive analysis for {ticker}...")
        print("  - Multiple valuation methods (DCF, DDM)")
        print("  - Sensitivity analysis")
        print("  - Monte Carlo simulation (10,000 runs)")

        # Run comprehensive analysis
        result = planner.run_comprehensive_scenario_analysis(
            scenarios=['Base Case', 'Optimistic Case', 'Pessimistic Case', 'Economic Expansion', 'Recession'],
            valuation_methods=['dcf', 'ddm'],
            include_sensitivity=True,
            include_monte_carlo=True,
            monte_carlo_simulations=10000,
            analysis_scope=AnalysisScope.COMPREHENSIVE
        )

        # Display comprehensive results
        print(f"\n🎯 VALUATION RESULTS:")
        for method in result.config.valuation_methods:
            if method in result.scenario_results:
                scenario_result = result.scenario_results[method]
                print(f"  {method.upper()} Expected Value: ${scenario_result.expected_value:.2f}")
                print(f"  {method.upper()} 95% CI: ${scenario_result.confidence_interval_95[0]:.2f} - ${scenario_result.confidence_interval_95[1]:.2f}")

        # Sensitivity analysis results
        print(f"\n🔍 SENSITIVITY ANALYSIS:")
        for method in result.config.valuation_methods:
            if method in result.sensitivity_results:
                most_sensitive = result.sensitivity_results[method].get_most_sensitive_parameter()
                if most_sensitive:
                    print(f"  {method.upper()} Most Sensitive Parameter: {most_sensitive.replace('_', ' ').title()}")

        # Monte Carlo results
        print(f"\n🎲 MONTE CARLO RESULTS:")
        for method in result.config.valuation_methods:
            if method in result.monte_carlo_results:
                mc_result = result.monte_carlo_results[method]
                print(f"  {method.upper()} Monte Carlo Mean: ${mc_result.mean_value:.2f}")
                print(f"  {method.upper()} Value at Risk (5%): ${mc_result.var_5:.2f}")
                print(f"  {method.upper()} Convergence: {mc_result.convergence_info.get('converged', 'Unknown')}")

        # AI Recommendations
        print(f"\n🤖 AI RECOMMENDATIONS:")
        for i, recommendation in enumerate(result.recommendations, 1):
            print(f"  {i}. {recommendation}")

        # Summary table
        print(f"\n📊 SUMMARY TABLE:")
        summary_df = result.get_summary_table()
        print(summary_df.to_string(index=False))

        print("✅ Comprehensive scenario analysis completed successfully")
        return result

    except Exception as e:
        print(f"❌ Comprehensive scenario analysis failed: {e}")
        return None


def demonstrate_custom_scenario_analysis(ticker: str = "AAPL"):
    """Demonstrate custom scenario creation and analysis."""
    print(f"\n{'='*60}")
    print("CUSTOM SCENARIO ANALYSIS")
    print(f"{'='*60}")

    try:
        calc = FinancialCalculator(ticker)
        planner = UnifiedScenarioPlanner(calc)

        print(f"🎛️ Creating custom scenarios for {ticker}...")

        # Define custom scenarios
        custom_scenarios = {
            "AI Boom Scenario": {
                "revenue_growth": 0.25,
                "discount_rate": 0.08,
                "terminal_growth": 0.05,
                "operating_margin": 0.30
            },
            "Regulatory Pressure": {
                "revenue_growth": 0.03,
                "discount_rate": 0.12,
                "terminal_growth": 0.02,
                "operating_margin": 0.15
            },
            "Market Saturation": {
                "revenue_growth": 0.01,
                "discount_rate": 0.10,
                "terminal_growth": 0.025,
                "operating_margin": 0.18
            }
        }

        # Run custom scenario analysis
        result = planner.create_custom_scenario_analysis(
            custom_scenarios=custom_scenarios,
            valuation_method='dcf'
        )

        # Display results
        print(f"\n🎯 CUSTOM SCENARIO RESULTS:")
        print(f"Expected DCF Value: ${result.expected_value:.2f}")

        print(f"\n📋 Individual Scenario Values:")
        for scenario_name, value in result.scenario_results['dcf'].scenario_values.items():
            probability = result.scenario_results['dcf'].probabilities[scenario_name]
            print(f"  {scenario_name}: ${value:.2f} (Probability: {probability:.1%})")

        print("✅ Custom scenario analysis completed successfully")
        return result

    except Exception as e:
        print(f"❌ Custom scenario analysis failed: {e}")
        return None


def demonstrate_three_point_analysis(ticker: str = "AAPL"):
    """Demonstrate three-point scenario analysis."""
    print(f"\n{'='*60}")
    print("THREE-POINT SCENARIO ANALYSIS")
    print(f"{'='*60}")

    try:
        calc = FinancialCalculator(ticker)
        planner = UnifiedScenarioPlanner(calc)

        print(f"📊 Running three-point analysis for {ticker}...")

        # Define base parameters and ranges
        base_parameters = {
            "revenue_growth": 0.08,
            "discount_rate": 0.10,
            "terminal_growth": 0.03,
            "operating_margin": 0.22
        }

        parameter_ranges = {
            "revenue_growth": (0.03, 0.15),  # Pessimistic to Optimistic
            "discount_rate": (0.12, 0.08),   # Pessimistic (higher) to Optimistic (lower)
            "terminal_growth": (0.02, 0.04),
            "operating_margin": (0.18, 0.26)
        }

        # Run three-point analysis
        result = planner.run_three_point_analysis(
            base_parameters=base_parameters,
            parameter_ranges=parameter_ranges,
            valuation_method='dcf'
        )

        # Display results
        print(f"\n🎯 THREE-POINT ANALYSIS RESULTS:")
        print(f"Expected DCF Value: ${result.expected_value:.2f}")
        print(f"95% Confidence Interval: ${result.confidence_interval_95[0]:.2f} - ${result.confidence_interval_95[1]:.2f}")

        print(f"\n📊 Scenario Breakdown:")
        for scenario_name, value in result.scenario_results['dcf'].scenario_values.items():
            probability = result.scenario_results['dcf'].probabilities[scenario_name]
            print(f"  {scenario_name}: ${value:.2f} (Probability: {probability:.1%})")

        print("✅ Three-point analysis completed successfully")
        return result

    except Exception as e:
        print(f"❌ Three-point analysis failed: {e}")
        return None


def demonstrate_quick_analysis_functions(ticker: str = "AAPL"):
    """Demonstrate quick analysis convenience functions."""
    print(f"\n{'='*60}")
    print("QUICK ANALYSIS FUNCTIONS")
    print(f"{'='*60}")

    try:
        calc = FinancialCalculator(ticker)

        print(f"⚡ Running quick analyses for {ticker}...")

        # Quick comprehensive analysis
        print(f"\n🔬 Quick Comprehensive Analysis:")
        comp_result = quick_scenario_planning_analysis(calc, "comprehensive")
        print(f"  Expected Value: ${comp_result.expected_value:.2f}")
        print(f"  Most Sensitive Parameter: {comp_result.most_sensitive_parameter or 'N/A'}")

        # Economic scenario comparison
        print(f"\n🏛️ Economic Scenario Comparison:")
        comparison_df = create_economic_scenario_comparison(calc)
        print(comparison_df.to_string(index=False))

        print("✅ Quick analysis functions completed successfully")
        return comp_result, comparison_df

    except Exception as e:
        print(f"❌ Quick analysis functions failed: {e}")
        return None, None


def demonstrate_scenario_comparison(ticker: str = "AAPL"):
    """Demonstrate scenario group comparison."""
    print(f"\n{'='*60}")
    print("SCENARIO GROUP COMPARISON")
    print(f"{'='*60}")

    try:
        calc = FinancialCalculator(ticker)
        planner = UnifiedScenarioPlanner(calc)

        print(f"🔄 Comparing scenario groups for {ticker}...")

        # Define scenario groups
        scenario_groups = {
            'Baseline Scenarios': ['Base Case', 'Economic Expansion'],
            'Growth Scenarios': ['Optimistic Case', 'High Growth'],
            'Stress Scenarios': ['Pessimistic Case', 'Recession'],
            'Crisis Scenarios': ['2008 Financial Crisis', 'COVID-19 Pandemic']
        }

        # Run comparison
        comparison_df = planner.compare_scenarios(scenario_groups, 'dcf')

        # Display results
        print(f"\n📊 SCENARIO GROUP COMPARISON:")
        print(comparison_df.to_string(index=False))

        # Find best and worst performing groups
        if not comparison_df.empty:
            best_group = comparison_df.loc[comparison_df['Expected Value'].idxmax(), 'Scenario Group']
            worst_group = comparison_df.loc[comparison_df['Expected Value'].idxmin(), 'Scenario Group']

            print(f"\n🏆 Best Performing Group: {best_group}")
            print(f"🔻 Worst Performing Group: {worst_group}")

        print("✅ Scenario comparison completed successfully")
        return comparison_df

    except Exception as e:
        print(f"❌ Scenario comparison failed: {e}")
        return None


def run_comprehensive_demo():
    """Run the complete demonstration of scenario planning capabilities."""
    print("🚀 COMPREHENSIVE SCENARIO PLANNING AND SENSITIVITY ANALYSIS DEMO")
    print("=" * 80)
    print("This demo showcases the unified scenario planning interface that integrates")
    print("all existing analysis components into a streamlined workflow.")
    print("=" * 80)

    # Configuration
    ticker = "AAPL"  # Can be changed to test with different companies

    try:
        # Run all demonstrations
        results = {}

        # 1. Basic scenario analysis
        results['basic'] = demonstrate_basic_scenario_analysis(ticker)

        # 2. Comprehensive scenario analysis
        results['comprehensive'] = demonstrate_comprehensive_scenario_analysis(ticker)

        # 3. Custom scenario analysis
        results['custom'] = demonstrate_custom_scenario_analysis(ticker)

        # 4. Three-point analysis
        results['three_point'] = demonstrate_three_point_analysis(ticker)

        # 5. Quick analysis functions
        quick_result, comparison_df = demonstrate_quick_analysis_functions(ticker)
        results['quick'] = quick_result
        results['comparison'] = comparison_df

        # 6. Scenario group comparison
        results['group_comparison'] = demonstrate_scenario_comparison(ticker)

        # Final summary
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")

        successful_demos = [name for name, result in results.items() if result is not None]
        failed_demos = [name for name, result in results.items() if result is None]

        print(f"✅ Successful Demonstrations: {len(successful_demos)}")
        for demo in successful_demos:
            print(f"   - {demo.replace('_', ' ').title()}")

        if failed_demos:
            print(f"\n❌ Failed Demonstrations: {len(failed_demos)}")
            for demo in failed_demos:
                print(f"   - {demo.replace('_', ' ').title()}")

        print(f"\n🎯 KEY CAPABILITIES DEMONSTRATED:")
        print("   - Unified interface for all scenario planning components")
        print("   - Integration of scenario modeling, sensitivity analysis, and Monte Carlo")
        print("   - Support for multiple valuation methods (DCF, DDM, P/B)")
        print("   - Custom scenario creation and three-point analysis")
        print("   - Automated recommendations and risk assessment")
        print("   - Performance optimization with caching")

        print(f"\n📈 The unified scenario planning interface successfully orchestrates")
        print(f"   all existing financial analysis components into a comprehensive,")
        print(f"   streamlined workflow for advanced scenario-based valuation analysis.")

    except Exception as e:
        print(f"\n❌ Demo execution failed: {e}")
        logger.exception("Demo execution error")

    print(f"\n🏁 Demo completed. Thank you for exploring the unified scenario planning capabilities!")


if __name__ == "__main__":
    run_comprehensive_demo()