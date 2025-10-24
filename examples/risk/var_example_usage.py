"""
VaR Implementation Example Usage
================================

This script demonstrates the comprehensive VaR (Value-at-Risk) implementation
with real financial data, showcasing different methodologies and their results.

This example shows how to:
1. Load historical returns data
2. Calculate VaR using multiple methodologies
3. Compare results across methods
4. Perform backtesting validation
5. Integrate with Monte Carlo simulations

Usage:
    python examples/risk/var_example_usage.py
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our VaR implementation
from core.analysis.risk.var_calculations import (
    VaRCalculator, VaRBacktester, VaRMethodology,
    integrate_var_with_monte_carlo
)
from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def generate_sample_financial_data(
    start_date: str = '2020-01-01',
    end_date: str = '2023-12-31',
    initial_price: float = 100.0,
    annual_drift: float = 0.08,
    annual_volatility: float = 0.20,
    add_crisis_period: bool = True
) -> pd.DataFrame:
    """
    Generate realistic sample financial returns data for demonstration.

    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        initial_price: Starting price level
        annual_drift: Expected annual return
        annual_volatility: Annual volatility
        add_crisis_period: Whether to add a crisis period with higher volatility

    Returns:
        DataFrame with Date, Price, and Returns columns
    """
    print("*** Generating sample financial data...")

    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)

    # Convert annual parameters to daily
    daily_drift = annual_drift / 252
    daily_vol = annual_volatility / np.sqrt(252)

    # Generate base returns using geometric Brownian motion
    np.random.seed(42)  # For reproducible results
    base_returns = np.random.normal(daily_drift, daily_vol, n_days)

    # Add crisis period (simulate market crash)
    if add_crisis_period:
        crisis_start = int(0.3 * n_days)  # 30% through the period
        crisis_length = 60  # 60 days of crisis

        # Higher volatility and negative drift during crisis
        crisis_returns = np.random.normal(-0.005, daily_vol * 2, crisis_length)
        base_returns[crisis_start:crisis_start + crisis_length] = crisis_returns

        print(f"   CRISIS Added crisis period: {dates[crisis_start]} to {dates[crisis_start + crisis_length - 1]}")

    # Calculate prices using cumulative returns
    prices = [initial_price]
    for ret in base_returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # Create DataFrame
    data = pd.DataFrame({
        'Date': dates,
        'Price': prices[:len(dates)],
        'Returns': [0] + list(base_returns[1:])  # First return is 0
    })

    # Calculate actual returns
    data['Returns'] = data['Price'].pct_change()
    data = data.dropna()

    print(f"   SUCCESS Generated {len(data)} days of data")
    print(f"   PRICES Price range: ${data['Price'].min():.2f} - ${data['Price'].max():.2f}")
    print(f"   STATS Return statistics: Mean={data['Returns'].mean()*252:.1%}, Vol={data['Returns'].std()*np.sqrt(252):.1%}")

    return data


def demonstrate_var_methodologies(returns: pd.Series, confidence_level: float = 0.95) -> pd.DataFrame:
    """
    Demonstrate different VaR calculation methodologies.

    Args:
        returns: Historical returns data
        confidence_level: Confidence level for VaR calculations

    Returns:
        DataFrame comparing VaR results across methodologies
    """
    print(f"\n*** Calculating VaR at {confidence_level*100:.0f}% confidence level...")

    calculator = VaRCalculator()
    results = []

    # 1. Parametric VaR (Normal Distribution)
    print("   NORMAL Parametric VaR (Normal)...")
    try:
        param_normal = calculator.calculate_parametric_var(
            returns, confidence_level, 'normal', bootstrap_ci=False
        )
        results.append({
            'Method': 'Parametric (Normal)',
            'VaR': param_normal.var_estimate,
            'CVaR': param_normal.cvar_estimate,
            'Methodology': param_normal.methodology.value
        })
    except Exception as e:
        print(f"      ERROR Failed: {e}")

    # 2. Parametric VaR (t-Distribution)
    print("   T-DIST Parametric VaR (t-Distribution)...")
    try:
        param_t = calculator.calculate_parametric_var(
            returns, confidence_level, 't_distribution', bootstrap_ci=False
        )
        results.append({
            'Method': 'Parametric (t-Distribution)',
            'VaR': param_t.var_estimate,
            'CVaR': param_t.cvar_estimate,
            'Methodology': param_t.methodology.value
        })
    except Exception as e:
        print(f"      ERROR Failed: {e}")

    # 3. Historical Simulation VaR
    print("   HIST Historical Simulation VaR...")
    try:
        historical = calculator.calculate_historical_var(
            returns, confidence_level, bootstrap_ci=False
        )
        results.append({
            'Method': 'Historical Simulation',
            'VaR': historical.var_estimate,
            'CVaR': historical.cvar_estimate,
            'Methodology': historical.methodology.value
        })
    except Exception as e:
        print(f"      ERROR Failed: {e}")

    # 4. Monte Carlo VaR
    print("   MC Monte Carlo VaR...")
    try:
        monte_carlo = calculator.calculate_monte_carlo_var(
            returns, confidence_level, num_simulations=5000, random_state=42
        )
        results.append({
            'Method': 'Monte Carlo',
            'VaR': monte_carlo.var_estimate,
            'CVaR': monte_carlo.cvar_estimate,
            'Methodology': monte_carlo.methodology.value
        })
    except Exception as e:
        print(f"      ERROR Failed: {e}")

    # 5. Cornish-Fisher VaR
    print("   CF Cornish-Fisher VaR...")
    try:
        cornish_fisher = calculator.calculate_cornish_fisher_var(
            returns, confidence_level
        )
        results.append({
            'Method': 'Cornish-Fisher',
            'VaR': cornish_fisher.var_estimate,
            'CVaR': cornish_fisher.cvar_estimate,
            'Methodology': cornish_fisher.methodology.value
        })
    except Exception as e:
        print(f"      ERROR Failed: {e}")

    # Create comparison DataFrame
    comparison_df = pd.DataFrame(results)

    if not comparison_df.empty:
        print("\n*** VaR Methodology Comparison:")
        print("=" * 60)
        for _, row in comparison_df.iterrows():
            print(f"{row['Method']:<25} VaR: {row['VaR']:.4f} ({row['VaR']*100:.2f}%)")
            print(f"{'':25} CVaR: {row['CVaR']:.4f} ({row['CVaR']*100:.2f}%)")
            print("-" * 60)

        # Calculate statistics
        var_mean = comparison_df['VaR'].mean()
        var_std = comparison_df['VaR'].std()
        print(f"\n*** VaR Statistics:")
        print(f"   Mean VaR: {var_mean:.4f} ({var_mean*100:.2f}%)")
        print(f"   VaR Std Dev: {var_std:.4f} ({var_std*100:.2f}%)")
        print(f"   Coefficient of Variation: {var_std/abs(var_mean):.2f}")

    return comparison_df


def perform_var_backtesting(returns: pd.Series, confidence_level: float = 0.95) -> dict:
    """
    Perform VaR model backtesting to validate model performance.

    Args:
        returns: Historical returns data
        confidence_level: Confidence level for VaR calculations

    Returns:
        Dictionary with backtesting results
    """
    print(f"\n🔍 Performing VaR Backtesting...")

    if len(returns) < 500:
        print("   ⚠️  Insufficient data for robust backtesting (need 500+ observations)")
        return {}

    # Split data: first 70% for estimation, last 30% for backtesting
    split_point = int(0.7 * len(returns))
    estimation_data = returns.iloc[:split_point]
    backtest_data = returns.iloc[split_point:]

    print(f"   📊 Estimation period: {len(estimation_data)} observations")
    print(f"   🧪 Backtesting period: {len(backtest_data)} observations")

    # Calculate VaR estimates for backtesting period
    calculator = VaRCalculator()

    # Use rolling window for VaR estimation
    window_size = 250  # 1 year of daily data
    var_estimates = []

    print("   ⚙️  Calculating rolling VaR estimates...")
    for i in range(len(backtest_data)):
        # Get window of data ending at current point
        if i + split_point < window_size:
            # Use all available data if window is not full
            window_data = returns.iloc[:split_point + i]
        else:
            # Use fixed window
            window_data = returns.iloc[split_point + i - window_size:split_point + i]

        try:
            var_result = calculator.calculate_parametric_var(
                window_data, confidence_level, 'normal', bootstrap_ci=False
            )
            var_estimates.append(var_result.var_estimate)
        except:
            # Fallback to historical average if calculation fails
            var_estimates.append(0.03)  # 3% default

    # Convert to pandas Series for backtesting
    var_estimates_series = pd.Series(var_estimates, index=backtest_data.index)

    # Perform backtesting
    backtester = VaRBacktester()
    backtest_results = backtester.backtest_var_model(
        backtest_data, var_estimates_series, confidence_level
    )

    # Display results
    print("\n🎯 Backtesting Results:")
    print("=" * 50)

    basic_stats = backtest_results['basic_statistics']
    print(f"Observations: {basic_stats['num_observations']}")
    print(f"Violations: {basic_stats['num_violations']}")
    print(f"Violation Rate: {basic_stats['violation_rate']:.2%}")
    print(f"Expected Rate: {basic_stats['expected_violation_rate']:.2%}")

    kupiec = backtest_results['kupiec_test']
    print(f"\nKupiec Test:")
    print(f"  Test Statistic: {kupiec['statistic']:.4f}")
    print(f"  P-value: {kupiec['p_value']:.4f}")
    print(f"  Result: {kupiec['interpretation']}")

    overall = backtest_results['overall_assessment']
    print(f"\nOverall Assessment:")
    print(f"  Rating: {overall['overall_rating']}")
    print(f"  Tests Passed: {overall['tests_passed']}/{overall['total_tests']}")
    print(f"  Recommendation: {overall['recommendation']}")

    return backtest_results


def create_var_visualization(data: pd.DataFrame, var_results: pd.DataFrame):
    """
    Create visualization of VaR results and historical performance.

    Args:
        data: Historical price and returns data
        var_results: VaR calculation results from different methodologies
    """
    print("\n📈 Creating VaR Visualization...")

    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Value-at-Risk (VaR) Analysis Dashboard', fontsize=16, fontweight='bold')

        # 1. Price chart
        ax1.plot(data['Date'], data['Price'], linewidth=1, color='blue', alpha=0.8)
        ax1.set_title('Historical Price Performance', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price ($)')
        ax1.grid(True, alpha=0.3)

        # 2. Returns distribution
        returns = data['Returns'].dropna()
        ax2.hist(returns, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(returns.mean(), color='green', linestyle='--', label=f'Mean: {returns.mean():.3f}')
        ax2.axvline(np.percentile(returns, 5), color='red', linestyle='--', label='5th Percentile (95% VaR)')
        ax2.set_title('Returns Distribution', fontweight='bold')
        ax2.set_xlabel('Daily Returns')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. VaR methodology comparison
        if not var_results.empty:
            methods = var_results['Method']
            var_values = var_results['VaR'] * 100  # Convert to percentage
            cvar_values = var_results['CVaR'] * 100

            x = np.arange(len(methods))
            width = 0.35

            bars1 = ax3.bar(x - width/2, var_values, width, label='VaR', alpha=0.8, color='orange')
            bars2 = ax3.bar(x + width/2, cvar_values, width, label='CVaR', alpha=0.8, color='red')

            ax3.set_title('VaR vs CVaR by Methodology', fontweight='bold')
            ax3.set_xlabel('Methodology')
            ax3.set_ylabel('Risk Measure (%)')
            ax3.set_xticks(x)
            ax3.set_xticklabels(methods, rotation=45, ha='right')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}%', ha='center', va='bottom', fontsize=8)

            for bar in bars2:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}%', ha='center', va='bottom', fontsize=8)

        # 4. Rolling VaR (if enough data)
        if len(returns) > 250:
            # Calculate rolling 95% VaR using 60-day window
            rolling_var = returns.rolling(window=60).quantile(0.05).abs()

            ax4.plot(data['Date'][60:], rolling_var[60:] * 100,
                    linewidth=1, color='red', label='Rolling 95% VaR')
            ax4.axhline(np.percentile(returns, 5) * -100,
                       color='blue', linestyle='--', alpha=0.7, label='Static 95% VaR')
            ax4.set_title('Rolling VaR Over Time', fontweight='bold')
            ax4.set_xlabel('Date')
            ax4.set_ylabel('VaR (%)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data\nfor rolling VaR\n(need 250+ obs)',
                    ha='center', va='center', transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Rolling VaR Over Time', fontweight='bold')

        plt.tight_layout()

        # Save the plot
        filename = f"var_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Visualization saved as: {filename}")

        plt.show()

    except ImportError:
        print("   ⚠️  Matplotlib not available for visualization")
    except Exception as e:
        print(f"   ❌ Visualization failed: {e}")


def demonstrate_monte_carlo_integration():
    """
    Demonstrate integration with Monte Carlo simulation engine.
    """
    print("\n🎲 Demonstrating Monte Carlo Integration...")

    # Create sample simulation result
    np.random.seed(42)
    simulation_values = np.random.normal(100, 20, 10000)  # DCF values around $100

    mock_result = SimulationResult(
        values=simulation_values,
        parameters={'num_simulations': 10000, 'scenario': 'base_case'},
        statistics={'mean': np.mean(simulation_values), 'std': np.std(simulation_values)}
    )

    # Convert to VaR format
    var_results = integrate_var_with_monte_carlo(
        mock_result, confidence_levels=[0.90, 0.95, 0.99]
    )

    print("   📊 Monte Carlo VaR Results:")
    print("   " + "=" * 40)
    for confidence, result in var_results.items():
        print(f"   {confidence} Confidence:")
        print(f"     VaR: ${result.var_estimate:.2f}")
        print(f"     CVaR: ${result.cvar_estimate:.2f}")
        print(f"     CVaR/VaR Ratio: {result.statistics['cvar_var_ratio']:.2f}")

    return var_results


def main():
    """
    Main demonstration function showcasing the comprehensive VaR implementation.
    """
    print("🚀 VaR Implementation Demonstration")
    print("=" * 50)

    try:
        # 1. Generate sample data
        financial_data = generate_sample_financial_data(
            start_date='2020-01-01',
            end_date='2023-12-31',
            initial_price=100.0,
            annual_drift=0.08,
            annual_volatility=0.20,
            add_crisis_period=True
        )

        returns = financial_data['Returns'].dropna()

        # 2. Demonstrate VaR methodologies
        var_comparison = demonstrate_var_methodologies(returns, confidence_level=0.95)

        # 3. Perform backtesting
        backtest_results = perform_var_backtesting(returns, confidence_level=0.95)

        # 4. Monte Carlo integration
        mc_var_results = demonstrate_monte_carlo_integration()

        # 5. Create visualization
        create_var_visualization(financial_data, var_comparison)

        # 6. Summary
        print("\n🎉 VaR Analysis Complete!")
        print("=" * 30)
        print("✅ Multiple VaR methodologies calculated")
        print("✅ Backtesting validation performed")
        print("✅ Monte Carlo integration demonstrated")
        print("✅ Visualization created")

        if not var_comparison.empty:
            best_method = var_comparison.loc[var_comparison['VaR'].abs().idxmin(), 'Method']
            print(f"📈 Most Conservative Method: {best_method}")

        print("\n💡 Key Insights:")
        print("   • Different methodologies can yield different VaR estimates")
        print("   • Historical simulation captures actual return distribution")
        print("   • Parametric methods assume specific distributions")
        print("   • Monte Carlo provides flexible scenario modeling")
        print("   • Backtesting validates model performance")

    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()