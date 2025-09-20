"""
Test Suite for VaR Calculations Module
=====================================

This module contains comprehensive tests for the VaR (Value-at-Risk) calculations
implementation, including parametric, historical simulation, Monte Carlo, and
backtesting functionality.

Test Categories:
- Parametric VaR tests (normal and t-distribution)
- Historical simulation VaR tests
- Monte Carlo VaR tests
- Cornish-Fisher VaR tests
- Confidence interval tests
- Backtesting framework tests
- Integration tests with Monte Carlo engine
- Edge case and error handling tests
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import warnings

# Import the modules to test
from core.analysis.risk.var_calculations import (
    VaRCalculator, VaRResult, VaRMethodology, VaRBacktester,
    integrate_var_with_monte_carlo
)
from core.analysis.statistics.monte_carlo_engine import SimulationResult

# Suppress warnings for cleaner test output
warnings.filterwarnings('ignore')


class TestVaRCalculator:
    """Test suite for VaRCalculator class."""

    @pytest.fixture
    def sample_returns(self):
        """Generate sample returns data for testing."""
        np.random.seed(42)  # For reproducible tests
        # Generate 1000 daily returns with mean=0.0005, std=0.02
        returns = pd.Series(
            np.random.normal(0.0005, 0.02, 1000),
            index=pd.date_range('2020-01-01', periods=1000, freq='D'),
            name='returns'
        )
        return returns

    @pytest.fixture
    def negative_skew_returns(self):
        """Generate returns with negative skew (tail risk)."""
        np.random.seed(42)
        # Mix normal returns with occasional large negative returns
        normal_returns = np.random.normal(0.001, 0.015, 950)
        crash_returns = np.random.normal(-0.05, 0.01, 50)
        all_returns = np.concatenate([normal_returns, crash_returns])
        np.random.shuffle(all_returns)

        return pd.Series(
            all_returns,
            index=pd.date_range('2020-01-01', periods=1000, freq='D'),
            name='skewed_returns'
        )

    @pytest.fixture
    def var_calculator(self):
        """Create VaRCalculator instance."""
        return VaRCalculator()

    def test_parametric_var_normal(self, var_calculator, sample_returns):
        """Test parametric VaR calculation with normal distribution."""
        result = var_calculator.calculate_parametric_var(
            sample_returns,
            confidence_level=0.95,
            distribution='normal',
            bootstrap_ci=False
        )

        # Assertions
        assert isinstance(result, VaRResult)
        assert result.methodology == VaRMethodology.PARAMETRIC_NORMAL
        assert result.confidence_level == 0.95
        assert result.var_estimate > 0  # VaR should be positive (representing loss)
        assert result.cvar_estimate > result.var_estimate  # CVaR should be higher than VaR
        assert result.expected_return is not None
        assert result.volatility is not None

        # Check that VaR is reasonable (should be around 2-4% for daily returns)
        assert 0.01 < result.var_estimate < 0.10

        # Verify statistics are populated
        assert 'sample_size' in result.statistics
        assert result.statistics['sample_size'] == len(sample_returns)

    def test_parametric_var_t_distribution(self, var_calculator, sample_returns):
        """Test parametric VaR calculation with t-distribution."""
        result = var_calculator.calculate_parametric_var(
            sample_returns,
            confidence_level=0.95,
            distribution='t_distribution',
            bootstrap_ci=False
        )

        # Assertions
        assert result.methodology == VaRMethodology.PARAMETRIC_T_DIST
        assert result.var_estimate > 0
        assert result.cvar_estimate > result.var_estimate
        assert 'degrees_freedom' in result.methodology_params

    def test_historical_var(self, var_calculator, sample_returns):
        """Test historical simulation VaR calculation."""
        result = var_calculator.calculate_historical_var(
            sample_returns,
            confidence_level=0.95,
            bootstrap_ci=False
        )

        # Assertions
        assert result.methodology == VaRMethodology.HISTORICAL_SIMULATION
        assert result.var_estimate > 0
        assert result.cvar_estimate >= result.var_estimate
        assert 'percentile_used' in result.methodology_params
        assert abs(result.methodology_params['percentile_used'] - 5.0) < 1e-10  # 1-0.95 = 0.05 = 5%

        # Check tail statistics
        assert 'tail_observations' in result.statistics
        tail_obs = result.statistics['tail_observations']
        total_obs = result.statistics['sample_size']
        expected_tail = int(0.05 * total_obs)
        assert abs(tail_obs - expected_tail) <= 2  # Allow some tolerance

    def test_monte_carlo_var(self, var_calculator, sample_returns):
        """Test Monte Carlo VaR calculation."""
        result = var_calculator.calculate_monte_carlo_var(
            sample_returns,
            confidence_level=0.95,
            num_simulations=5000,
            distribution_fit='normal',
            random_state=42
        )

        # Assertions
        assert result.methodology == VaRMethodology.MONTE_CARLO
        assert result.var_estimate > 0
        assert result.cvar_estimate > result.var_estimate
        assert result.methodology_params['num_simulations'] == 5000
        assert 'simulations_count' in result.statistics

        # Check convergence
        assert 'convergence_metric' in result.statistics

    def test_cornish_fisher_var(self, var_calculator, sample_returns):
        """Test Cornish-Fisher VaR calculation."""
        result = var_calculator.calculate_cornish_fisher_var(
            sample_returns,
            confidence_level=0.95
        )

        # Assertions
        assert result.methodology == VaRMethodology.CORNISH_FISHER
        assert result.var_estimate > 0
        assert 'normal_z_score' in result.statistics
        assert 'cornish_fisher_z_score' in result.statistics
        assert 'cf_adjustment' in result.statistics

    def test_confidence_intervals_bootstrap(self, var_calculator, sample_returns):
        """Test bootstrap confidence intervals."""
        result = var_calculator.calculate_parametric_var(
            sample_returns,
            confidence_level=0.95,
            distribution='normal',
            bootstrap_ci=True
        )

        # Check that confidence intervals exist
        assert result.var_confidence_interval is not None
        assert result.cvar_confidence_interval is not None

        # Check interval structure
        var_ci = result.var_confidence_interval
        cvar_ci = result.cvar_confidence_interval

        assert len(var_ci) == 2
        assert len(cvar_ci) == 2
        assert var_ci[0] < var_ci[1]  # Lower bound < Upper bound
        assert cvar_ci[0] < cvar_ci[1]

        # VaR estimate should be within confidence interval
        assert var_ci[0] <= result.var_estimate <= var_ci[1]

    def test_multiple_confidence_levels(self, var_calculator, sample_returns):
        """Test VaR calculation at different confidence levels."""
        confidence_levels = [0.90, 0.95, 0.99]
        results = []

        for cl in confidence_levels:
            result = var_calculator.calculate_parametric_var(
                sample_returns,
                confidence_level=cl,
                bootstrap_ci=False
            )
            results.append((cl, result.var_estimate, result.cvar_estimate))

        # VaR should increase with confidence level
        for i in range(1, len(results)):
            assert results[i][1] > results[i-1][1]  # VaR increases
            assert results[i][2] > results[i-1][2]  # CVaR increases

    def test_methodology_comparison(self, var_calculator, sample_returns):
        """Test comparison across methodologies."""
        comparison_df = var_calculator.compare_methodologies(
            sample_returns,
            confidence_levels=[0.95],
            methodologies=[
                VaRMethodology.PARAMETRIC_NORMAL,
                VaRMethodology.HISTORICAL_SIMULATION,
                VaRMethodology.MONTE_CARLO
            ]
        )

        # Check that comparison DataFrame is created
        assert isinstance(comparison_df, pd.DataFrame)
        assert not comparison_df.empty
        assert '95%' in comparison_df.columns

    def test_insufficient_data_error(self, var_calculator):
        """Test error handling with insufficient data."""
        short_returns = pd.Series(np.random.normal(0, 0.02, 10))

        with pytest.raises(ValueError, match="Insufficient data"):
            var_calculator.calculate_parametric_var(short_returns)

    def test_edge_case_all_positive_returns(self, var_calculator):
        """Test VaR calculation with all positive returns."""
        positive_returns = pd.Series(np.abs(np.random.normal(0.01, 0.005, 100)))

        result = var_calculator.calculate_historical_var(
            positive_returns,
            confidence_level=0.95,
            bootstrap_ci=False
        )

        # VaR can be negative for all positive returns (indicates expected gain, not loss)
        # The important thing is that calculation completes successfully
        assert isinstance(result.var_estimate, (int, float))
        assert isinstance(result.cvar_estimate, (int, float))
        assert result.statistics['sample_size'] == 100

    def test_extreme_confidence_levels(self, var_calculator, sample_returns):
        """Test VaR at extreme confidence levels."""
        # Test very high confidence level
        result_99_9 = var_calculator.calculate_historical_var(
            sample_returns,
            confidence_level=0.999,
            bootstrap_ci=False
        )

        # Test moderate confidence level
        result_90 = var_calculator.calculate_historical_var(
            sample_returns,
            confidence_level=0.90,
            bootstrap_ci=False
        )

        # VaR at 99.9% should be much higher than at 90%
        assert result_99_9.var_estimate > result_90.var_estimate

    def test_window_size_parameter(self, var_calculator, sample_returns):
        """Test VaR calculation with different window sizes."""
        # Full sample
        result_full = var_calculator.calculate_parametric_var(
            sample_returns,
            window_size=None,
            bootstrap_ci=False
        )

        # Rolling window
        result_window = var_calculator.calculate_parametric_var(
            sample_returns,
            window_size=250,
            bootstrap_ci=False
        )

        # Both should produce valid results
        assert result_full.var_estimate > 0
        assert result_window.var_estimate > 0

        # Check sample sizes in statistics
        assert result_full.statistics['sample_size'] == len(sample_returns)
        assert result_window.statistics['sample_size'] == 250

    def test_random_state_reproducibility(self, var_calculator, sample_returns):
        """Test reproducibility with random state."""
        result1 = var_calculator.calculate_monte_carlo_var(
            sample_returns,
            num_simulations=1000,
            random_state=42
        )

        result2 = var_calculator.calculate_monte_carlo_var(
            sample_returns,
            num_simulations=1000,
            random_state=42
        )

        # Results should be identical
        assert abs(result1.var_estimate - result2.var_estimate) < 1e-10
        assert abs(result1.cvar_estimate - result2.cvar_estimate) < 1e-10


class TestVaRResult:
    """Test suite for VaRResult class."""

    @pytest.fixture
    def sample_var_result(self):
        """Create sample VaRResult for testing."""
        return VaRResult(
            methodology=VaRMethodology.PARAMETRIC_NORMAL,
            confidence_level=0.95,
            var_estimate=0.032,
            cvar_estimate=0.041,
            expected_return=0.0008,
            volatility=0.15,
            statistics={
                'sample_size': 1000,
                'sample_mean': 0.0008,
                'sample_std': 0.02
            }
        )

    def test_var_result_initialization(self, sample_var_result):
        """Test VaRResult initialization and derived metrics."""
        result = sample_var_result

        # Check basic attributes
        assert result.methodology == VaRMethodology.PARAMETRIC_NORMAL
        assert result.confidence_level == 0.95
        assert result.var_estimate == 0.032
        assert result.cvar_estimate == 0.041

        # Check derived metrics are calculated
        assert 'cvar_var_ratio' in result.statistics
        assert 'tail_expectation' in result.statistics
        assert 'excess_tail_risk' in result.statistics

        # CVaR/VaR ratio should be > 1
        assert result.statistics['cvar_var_ratio'] > 1

    def test_summary_table_creation(self, sample_var_result):
        """Test summary table generation."""
        summary_df = sample_var_result.summary_table()

        assert isinstance(summary_df, pd.DataFrame)
        assert 'Metric' in summary_df.columns
        assert 'Value' in summary_df.columns
        assert 'Description' in summary_df.columns
        assert len(summary_df) > 0

        # Check that key metrics are included
        metrics = summary_df['Metric'].tolist()
        assert 'VaR Estimate' in metrics
        assert 'CVaR Estimate' in metrics

    def test_to_dict_serialization(self, sample_var_result):
        """Test dictionary serialization."""
        result_dict = sample_var_result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'methodology' in result_dict
        assert 'confidence_level' in result_dict
        assert 'var_estimate' in result_dict
        assert 'cvar_estimate' in result_dict

        # Check methodology is string (serializable)
        assert isinstance(result_dict['methodology'], str)


class TestVaRBacktester:
    """Test suite for VaRBacktester class."""

    @pytest.fixture
    def backtester(self):
        """Create VaRBacktester instance."""
        return VaRBacktester()

    @pytest.fixture
    def backtest_data(self):
        """Generate realistic backtest data."""
        np.random.seed(42)

        # Generate 500 days of returns
        returns = pd.Series(
            np.random.normal(-0.0002, 0.018, 500),
            index=pd.date_range('2020-01-01', periods=500, freq='D'),
            name='returns'
        )

        # Generate VaR estimates (slightly underestimating risk)
        # True 95% VaR should be around 3%, estimate around 2.8%
        var_estimates = pd.Series(
            np.random.normal(0.028, 0.003, 500),
            index=returns.index,
            name='var_estimates'
        )

        return returns, var_estimates

    def test_basic_backtest_statistics(self, backtester, backtest_data):
        """Test basic backtesting statistics."""
        returns, var_estimates = backtest_data

        results = backtester.backtest_var_model(
            returns, var_estimates, confidence_level=0.95
        )

        # Check basic structure
        assert 'basic_statistics' in results
        assert 'kupiec_test' in results
        assert 'independence_test' in results

        basic_stats = results['basic_statistics']
        assert 'num_observations' in basic_stats
        assert 'num_violations' in basic_stats
        assert 'violation_rate' in basic_stats
        assert 'expected_violation_rate' in basic_stats

        # Check reasonable violation rate (should be around 5% for 95% VaR)
        violation_rate = basic_stats['violation_rate']
        assert 0.02 <= violation_rate <= 0.12  # Allow reasonable range

    def test_kupiec_test(self, backtester, backtest_data):
        """Test Kupiec unconditional coverage test."""
        returns, var_estimates = backtest_data

        results = backtester.backtest_var_model(
            returns, var_estimates, confidence_level=0.95
        )

        kupiec = results['kupiec_test']
        assert 'statistic' in kupiec
        assert 'p_value' in kupiec
        assert 'critical_value' in kupiec
        assert 'reject_null' in kupiec
        assert 'interpretation' in kupiec

        # Check that test produces reasonable results
        if not np.isnan(kupiec['statistic']):
            assert kupiec['statistic'] >= 0
            assert 0 <= kupiec['p_value'] <= 1

    def test_independence_test(self, backtester, backtest_data):
        """Test independence test for violation clustering."""
        returns, var_estimates = backtest_data

        results = backtester.backtest_var_model(
            returns, var_estimates, confidence_level=0.95
        )

        independence = results['independence_test']
        assert 'statistic' in independence
        assert 'reject_null' in independence
        assert 'interpretation' in independence

    def test_violation_clustering(self, backtester):
        """Test violation clustering detection."""
        # Create data with clustered violations
        returns = pd.Series(np.random.normal(0, 0.02, 200))
        var_estimates = pd.Series([0.03] * 200)  # Constant VaR estimate

        # Inject clustered violations (consecutive bad days)
        returns.iloc[50:55] = -0.05  # 5 consecutive bad days
        returns.iloc[100:103] = -0.04  # 3 consecutive bad days

        results = backtester.backtest_var_model(
            returns, var_estimates, confidence_level=0.95
        )

        clustering = results['violation_clustering']
        assert 'clustering_metric' in clustering
        assert 'max_cluster_size' in clustering
        assert 'interpretation' in clustering

        # Should detect clustering
        assert clustering['max_cluster_size'] >= 3

    def test_overall_assessment(self, backtester, backtest_data):
        """Test overall model assessment."""
        returns, var_estimates = backtest_data

        results = backtester.backtest_var_model(
            returns, var_estimates, confidence_level=0.95
        )

        assessment = results['overall_assessment']
        assert 'tests_passed' in assessment
        assert 'total_tests' in assessment
        assert 'pass_rate' in assessment
        assert 'overall_rating' in assessment
        assert 'recommendation' in assessment

        # Check rating is one of expected values
        rating = assessment['overall_rating']
        assert rating in ['Good', 'Fair', 'Poor']

    def test_insufficient_data_for_backtest(self, backtester):
        """Test error handling with insufficient data for backtesting."""
        short_returns = pd.Series(np.random.normal(0, 0.02, 50))
        short_var = pd.Series(np.random.normal(0.03, 0.005, 50))

        with pytest.raises(ValueError, match="Insufficient data for backtesting"):
            backtester.backtest_var_model(short_returns, short_var)


class TestMonteCarloIntegration:
    """Test suite for Monte Carlo engine integration."""

    @pytest.fixture
    def mock_simulation_result(self):
        """Create mock SimulationResult for testing."""
        # Generate sample simulation values
        np.random.seed(42)
        values = np.random.normal(100, 20, 10000)  # DCF values around $100

        return SimulationResult(
            values=values,
            parameters={'num_simulations': 10000},
            statistics={'mean': np.mean(values), 'std': np.std(values)}
        )

    def test_monte_carlo_integration(self, mock_simulation_result):
        """Test integration with Monte Carlo simulation results."""
        var_results = integrate_var_with_monte_carlo(
            mock_simulation_result,
            confidence_levels=[0.95, 0.99]
        )

        # Check structure
        assert isinstance(var_results, dict)
        assert '95%' in var_results
        assert '99%' in var_results

        # Check VaR results
        var_95 = var_results['95%']
        var_99 = var_results['99%']

        assert isinstance(var_95, VaRResult)
        assert isinstance(var_99, VaRResult)

        # 99% VaR should be higher than 95% VaR
        assert var_99.var_estimate > var_95.var_estimate
        assert var_99.cvar_estimate > var_95.cvar_estimate

        # Check methodology
        assert var_95.methodology == VaRMethodology.MONTE_CARLO
        assert var_99.methodology == VaRMethodology.MONTE_CARLO

    def test_integration_with_empty_results(self):
        """Test integration with empty simulation results."""
        # Create a mock object instead of using SimulationResult directly
        # to avoid issues with empty array statistics calculation
        class MockEmptyResult:
            def __init__(self):
                self.values = np.array([])
                self.parameters = {}
                self.statistics = {}

        empty_result = MockEmptyResult()

        var_results = integrate_var_with_monte_carlo(empty_result)

        # Should handle gracefully
        assert isinstance(var_results, dict)

        # Check that all results have empty indicators
        for var_result in var_results.values():
            assert var_result.statistics.get('empty_result', False) == True


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and error handling."""

    def test_all_zero_returns(self):
        """Test VaR calculation with all zero returns."""
        zero_returns = pd.Series([0.0] * 100)
        calculator = VaRCalculator()

        result = calculator.calculate_historical_var(
            zero_returns, confidence_level=0.95, bootstrap_ci=False
        )

        # Should handle gracefully
        assert result.var_estimate == 0
        assert result.cvar_estimate == 0

    def test_single_extreme_outlier(self):
        """Test VaR calculation with extreme outlier."""
        normal_returns = pd.Series(np.random.normal(0.001, 0.01, 999))
        outlier_return = pd.Series([-0.5])  # 50% loss

        returns_with_outlier = pd.concat([normal_returns, outlier_return])
        calculator = VaRCalculator()

        result = calculator.calculate_historical_var(
            returns_with_outlier, confidence_level=0.95, bootstrap_ci=False
        )

        # VaR should be significantly affected by outlier
        assert result.var_estimate > 0.01  # Should be higher than normal

    def test_missing_data_handling(self):
        """Test handling of missing data."""
        # Create larger dataset with NaN values
        base_returns = np.random.normal(0.001, 0.02, 100)
        base_returns[10:15] = np.nan  # Insert some NaN values
        base_returns[50:52] = np.nan  # Insert more NaN values

        returns_with_nan = pd.Series(base_returns)
        calculator = VaRCalculator()

        # Should handle NaN values gracefully
        result = calculator.calculate_parametric_var(
            returns_with_nan, bootstrap_ci=False
        )

        # Should only use non-NaN values
        expected_sample_size = 93  # 100 - 7 NaN values
        assert result.statistics['sample_size'] == expected_sample_size

    def test_invalid_confidence_level(self):
        """Test error handling for invalid confidence levels."""
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        calculator = VaRCalculator()

        # Test confidence level > 1
        with pytest.raises((ValueError, AssertionError)):
            calculator.calculate_parametric_var(returns, confidence_level=1.5)

        # Test confidence level < 0
        with pytest.raises((ValueError, AssertionError)):
            calculator.calculate_parametric_var(returns, confidence_level=-0.1)

    def test_unsupported_distribution(self):
        """Test error handling for unsupported distribution."""
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        calculator = VaRCalculator()

        with pytest.raises(ValueError, match="Unsupported distribution"):
            calculator.calculate_parametric_var(
                returns, distribution='unsupported_dist'
            )


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])