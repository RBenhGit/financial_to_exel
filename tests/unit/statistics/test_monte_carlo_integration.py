"""
Comprehensive Tests for Monte Carlo Engine Integration with Valuation Models
===========================================================================

This test suite validates the integration between the Monte Carlo simulation engine
and the DCF, DDM, and P/B valuation models, ensuring proper risk analysis
functionality with performance optimization.

Test Coverage
------------
- DCF Monte Carlo integration with actual DCF valuator
- DDM Monte Carlo integration with actual DDM valuator
- P/B Monte Carlo integration with actual P/B valuator
- Parallel processing performance and accuracy
- Error handling and fallback mechanisms
- Statistical validation of simulation results
- Performance benchmarking and optimization validation

Usage
-----
Run with pytest:
    pytest tests/unit/statistics/test_monte_carlo_integration.py -v

Run performance tests:
    pytest tests/unit/statistics/test_monte_carlo_integration.py::TestMonteCarloPerformance -v
"""

import pytest
import numpy as np
import pandas as pd
import logging
from unittest.mock import Mock, MagicMock, patch
import time
from concurrent.futures import ProcessPoolExecutor

# Import modules under test
from core.analysis.statistics.monte_carlo_engine import (
    MonteCarloEngine,
    ParameterDistribution,
    DistributionType,
    SimulationResult,
    RiskMetrics
)
from core.analysis.engines.financial_calculations import FinancialCalculator

logger = logging.getLogger(__name__)


class TestMonteCarloIntegration:
    """Test suite for Monte Carlo integration with valuation models."""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create a mock financial calculator with realistic data."""
        calc = Mock(spec=FinancialCalculator)
        calc.ticker_symbol = "MSFT"
        calc.total_revenue = 200000  # $200B
        calc.shares_outstanding = 7500000000  # 7.5B shares
        calc.earnings_per_share = 10.0
        calc.book_value_per_share = 50.0
        calc.currency = "USD"
        calc.is_tase_stock = False

        # Mock FCF results
        calc.fcf_results = {
            'FCFE': [50000, 55000, 60000, 65000, 70000],  # $50B-$70B FCF growth
            'FCFF': [52000, 57000, 62000, 67000, 72000],
            'LFCF': [48000, 53000, 58000, 63000, 68000]
        }

        return calc

    @pytest.fixture
    def monte_carlo_engine(self, mock_financial_calculator):
        """Create Monte Carlo engine with mock financial calculator."""
        engine = MonteCarloEngine(mock_financial_calculator)
        # Configure for testing (smaller chunks, limited workers)
        engine.configure_performance(
            use_parallel_processing=True,
            max_workers=2,
            chunk_size=100
        )
        return engine

    def test_dcf_monte_carlo_integration(self, monte_carlo_engine):
        """Test DCF Monte Carlo simulation with actual DCF integration."""
        # Run small simulation for testing
        result = monte_carlo_engine.simulate_dcf_valuation(
            num_simulations=500,
            revenue_growth_volatility=0.10,
            discount_rate_volatility=0.01,
            random_state=42
        )

        # Validate simulation result structure
        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0
        assert result.statistics['count'] > 0
        assert result.risk_metrics is not None

        # Validate statistical properties
        assert result.statistics['mean'] > 0
        assert result.statistics['std'] > 0
        assert result.percentiles['p50'] > 0  # Median should be positive

        # Validate risk metrics
        assert result.risk_metrics.var_5 < result.statistics['median']
        assert result.risk_metrics.upside_potential > result.statistics['median']

        logger.info(f"DCF Monte Carlo test completed: Mean=${result.statistics['mean']:.2f}, "
                   f"VaR(5%)=${result.risk_metrics.var_5:.2f}")

    def test_ddm_monte_carlo_integration(self, monte_carlo_engine):
        """Test DDM Monte Carlo simulation with actual DDM integration."""
        result = monte_carlo_engine.simulate_dividend_discount_model(
            num_simulations=300,
            dividend_growth_volatility=0.15,
            required_return_volatility=0.02,
            random_state=42
        )

        # Validate simulation result
        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0
        assert result.statistics['mean'] > 0

        # DDM-specific validations
        assert result.parameters['dividend_growth_volatility'] == 0.15
        assert result.parameters['valid_simulations'] <= result.parameters['num_simulations']

        logger.info(f"DDM Monte Carlo test completed: Mean=${result.statistics['mean']:.2f}, "
                   f"Valid sims={result.parameters['valid_simulations']}")

    def test_pb_monte_carlo_integration(self, monte_carlo_engine):
        """Test P/B Monte Carlo simulation with actual P/B integration."""
        result = monte_carlo_engine.simulate_pb_valuation(
            num_simulations=300,
            pb_ratio_volatility=0.20,
            book_value_growth_volatility=0.08,
            random_state=42
        )

        # Validate simulation result
        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0
        assert result.statistics['mean'] > 0

        # P/B-specific validations
        assert result.parameters['pb_ratio_volatility'] == 0.20
        assert result.statistics['mean'] > 20  # Should be reasonable P/B value

        logger.info(f"P/B Monte Carlo test completed: Mean=${result.statistics['mean']:.2f}")

    def test_parameter_distribution_sampling(self, monte_carlo_engine):
        """Test parameter distribution sampling accuracy."""
        # Create test distribution
        test_dist = ParameterDistribution(
            DistributionType.NORMAL,
            {'mean': 0.10, 'std': 0.02},
            'test_discount_rate'
        )

        # Sample large number for statistical validation
        samples = test_dist.sample(10000, random_state=42)

        # Validate statistical properties
        assert abs(np.mean(samples) - 0.10) < 0.005  # Within 0.5% of expected mean
        assert abs(np.std(samples) - 0.02) < 0.002   # Within 0.2% of expected std
        assert len(samples) == 10000

        logger.info(f"Parameter sampling test: mean={np.mean(samples):.4f}, std={np.std(samples):.4f}")

    def test_correlation_matrix_functionality(self, monte_carlo_engine):
        """Test correlated parameter sampling."""
        # Set up correlated parameters
        param_names = ['discount_rate', 'terminal_growth']
        correlation_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])

        monte_carlo_engine.set_correlation_matrix(param_names, correlation_matrix)

        # Validate correlation matrix storage
        assert monte_carlo_engine.correlation_matrix is not None
        assert monte_carlo_engine.correlation_params == param_names
        np.testing.assert_array_equal(monte_carlo_engine.correlation_matrix, correlation_matrix)

    def test_error_handling_and_fallbacks(self, monte_carlo_engine):
        """Test error handling and fallback mechanisms."""
        # Test with invalid parameters that should trigger fallbacks
        with patch.object(monte_carlo_engine, '_calculate_dcf_with_params', side_effect=Exception("Test error")):
            result = monte_carlo_engine.simulate_dcf_valuation(
                num_simulations=50,
                random_state=42
            )

            # Should still return valid results due to fallback
            assert isinstance(result, SimulationResult)
            assert len(result.values) > 0
            # Values should be fallback values (around 100.0)
            assert 50 < result.statistics['mean'] < 200

    def test_scenario_analysis(self, monte_carlo_engine):
        """Test scenario analysis functionality."""
        scenarios = {
            'Base Case': {
                'revenue_growth': 0.05,
                'discount_rate': 0.10,
                'terminal_growth': 0.03,
                'operating_margin': 0.20
            },
            'Optimistic': {
                'revenue_growth': 0.15,
                'discount_rate': 0.08,
                'terminal_growth': 0.04,
                'operating_margin': 0.25
            },
            'Pessimistic': {
                'revenue_growth': -0.05,
                'discount_rate': 0.12,
                'terminal_growth': 0.02,
                'operating_margin': 0.15
            }
        }

        results = monte_carlo_engine.run_scenario_analysis(scenarios, base_valuation_method='dcf')

        # Validate scenario results
        assert len(results) == 3
        assert 'Base Case' in results
        assert 'Optimistic' in results
        assert 'Pessimistic' in results

        # Optimistic should generally be higher than pessimistic
        if all(v is not None for v in results.values()):
            assert results['Optimistic'] > results['Pessimistic']

        logger.info(f"Scenario analysis results: {results}")


class TestMonteCarloPerformance:
    """Performance tests for Monte Carlo engine."""

    @pytest.fixture
    def performance_engine(self):
        """Create engine configured for performance testing."""
        calc = Mock(spec=FinancialCalculator)
        calc.ticker_symbol = "PERF"
        calc.total_revenue = 100000
        calc.shares_outstanding = 1000000000

        engine = MonteCarloEngine(calc)
        engine.configure_performance(
            use_parallel_processing=True,
            max_workers=4,
            chunk_size=1000
        )
        return engine

    def test_parallel_vs_sequential_performance(self, performance_engine):
        """Compare parallel vs sequential execution performance."""
        num_simulations = 5000

        # Test sequential execution
        performance_engine.configure_performance(use_parallel_processing=False)
        start_time = time.time()
        sequential_result = performance_engine.simulate_dcf_valuation(
            num_simulations=num_simulations,
            random_state=42
        )
        sequential_time = time.time() - start_time

        # Test parallel execution
        performance_engine.configure_performance(use_parallel_processing=True, max_workers=4)
        start_time = time.time()
        parallel_result = performance_engine.simulate_dcf_valuation(
            num_simulations=num_simulations,
            random_state=42
        )
        parallel_time = time.time() - start_time

        # Validate both produce similar statistical results
        mean_diff = abs(sequential_result.statistics['mean'] - parallel_result.statistics['mean'])
        assert mean_diff < (sequential_result.statistics['mean'] * 0.1)  # Within 10%

        # Log performance comparison
        speedup = sequential_time / parallel_time if parallel_time > 0 else 1
        logger.info(f"Performance comparison - Sequential: {sequential_time:.2f}s, "
                   f"Parallel: {parallel_time:.2f}s, Speedup: {speedup:.2f}x")

        # Parallel should be faster for large simulations (or at least not much slower)
        assert parallel_time <= sequential_time * 1.5  # Allow up to 50% overhead for small tests

    def test_large_simulation_scalability(self, performance_engine):
        """Test scalability with large number of simulations."""
        # Test with progressively larger simulation counts
        simulation_counts = [1000, 5000, 10000]
        execution_times = []

        for count in simulation_counts:
            start_time = time.time()
            result = performance_engine.simulate_dcf_valuation(
                num_simulations=count,
                random_state=42
            )
            execution_time = time.time() - start_time
            execution_times.append(execution_time)

            # Validate result quality doesn't degrade
            assert len(result.values) >= count * 0.8  # At least 80% success rate
            assert result.statistics['std'] > 0  # Should have variation

            sims_per_second = count / execution_time if execution_time > 0 else 0
            logger.info(f"{count} simulations: {execution_time:.2f}s ({sims_per_second:.0f} sims/sec)")

        # Execution time should scale sub-linearly with parallel processing
        # (i.e., doubling simulations shouldn't double time)
        if len(execution_times) >= 2:
            time_ratio = execution_times[-1] / execution_times[0]
            sim_ratio = simulation_counts[-1] / simulation_counts[0]
            efficiency = sim_ratio / time_ratio

            logger.info(f"Scalability efficiency: {efficiency:.2f} (higher is better)")
            assert efficiency > 0.5  # Should maintain at least 50% efficiency

    def test_memory_efficiency(self, performance_engine):
        """Test memory efficiency with large simulations."""
        import psutil
        import os

        # Measure memory before simulation
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Run large simulation
        result = performance_engine.simulate_dcf_valuation(
            num_simulations=10000,
            random_state=42
        )

        # Measure memory after simulation
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        # Validate memory usage is reasonable
        # Should not increase by more than 200MB for 10k simulations
        assert memory_increase < 200

        # Validate simulation completed successfully
        assert len(result.values) > 8000  # At least 80% success rate

        logger.info(f"Memory usage: {memory_before:.1f}MB -> {memory_after:.1f}MB "
                   f"(+{memory_increase:.1f}MB for 10k simulations)")

    def test_concurrent_simulation_handling(self, performance_engine):
        """Test handling of concurrent simulation requests."""
        import threading

        results = []
        exceptions = []

        def run_simulation(sim_id):
            try:
                result = performance_engine.simulate_dcf_valuation(
                    num_simulations=1000,
                    random_state=42 + sim_id
                )
                results.append((sim_id, result))
            except Exception as e:
                exceptions.append((sim_id, e))

        # Run multiple simulations concurrently
        threads = []
        for i in range(3):  # 3 concurrent simulations
            thread = threading.Thread(target=run_simulation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Validate all simulations completed successfully
        assert len(exceptions) == 0, f"Simulation exceptions: {exceptions}"
        assert len(results) == 3

        # Validate all results are reasonable
        for sim_id, result in results:
            assert isinstance(result, SimulationResult)
            assert len(result.values) > 800  # At least 80% success rate
            assert result.statistics['mean'] > 0

        logger.info(f"Concurrent simulation test completed: {len(results)} successful simulations")


class TestMonteCarloStatisticalValidation:
    """Statistical validation tests for Monte Carlo simulations."""

    @pytest.fixture
    def validation_engine(self):
        """Create engine for statistical validation."""
        calc = Mock(spec=FinancialCalculator)
        calc.ticker_symbol = "STAT"
        calc.total_revenue = 150000
        calc.shares_outstanding = 5000000000

        return MonteCarloEngine(calc)

    def test_distribution_fitting_accuracy(self, validation_engine):
        """Test automatic distribution fitting accuracy."""
        # Create synthetic historical data with known distribution
        np.random.seed(42)
        synthetic_data = pd.DataFrame({
            'revenue_growth': np.random.normal(0.08, 0.12, 100),
            'margin_data': np.random.lognormal(np.log(0.20), 0.10, 100)
        })

        # Test distribution estimation
        param_mapping = {
            'revenue_growth': 'revenue_growth',
            'operating_margin': 'margin_data'
        }

        estimated_distributions = validation_engine.estimate_parameter_distributions(
            synthetic_data, param_mapping
        )

        # Validate distribution fitting
        assert 'revenue_growth' in estimated_distributions
        assert 'operating_margin' in estimated_distributions

        # Check that estimated parameters are reasonable
        revenue_dist = estimated_distributions['revenue_growth']
        assert revenue_dist.distribution in [DistributionType.NORMAL, DistributionType.LOGNORMAL]

        logger.info(f"Distribution fitting test completed: {len(estimated_distributions)} distributions fitted")

    def test_risk_metrics_calculation(self, validation_engine):
        """Test risk metrics calculation accuracy."""
        # Run simulation with known parameters
        result = validation_engine.simulate_dcf_valuation(
            num_simulations=10000,
            revenue_growth_volatility=0.10,
            discount_rate_volatility=0.01,
            random_state=42
        )

        # Validate risk metrics mathematical properties
        assert result.risk_metrics.var_5 <= result.risk_metrics.var_1  # VaR(5%) <= VaR(1%)
        assert result.risk_metrics.cvar_5 <= result.risk_metrics.var_5  # CVaR <= VaR
        assert result.risk_metrics.upside_potential >= result.statistics['median']
        assert 0 <= result.risk_metrics.probability_of_loss <= 1

        # Validate percentile consistency
        assert result.percentiles['p5'] <= result.percentiles['p50']
        assert result.percentiles['p50'] <= result.percentiles['p95']

        # Validate confidence intervals
        ci_95 = result.percentiles['ci_95']
        assert ci_95[0] < result.statistics['median'] < ci_95[1]

        logger.info(f"Risk metrics validation completed: VaR(5%)=${result.risk_metrics.var_5:.2f}, "
                   f"CVaR(5%)=${result.risk_metrics.cvar_5:.2f}")

    def test_convergence_behavior(self, validation_engine):
        """Test Monte Carlo convergence with increasing simulations."""
        simulation_counts = [500, 1000, 2000, 5000]
        means = []
        stds = []

        for count in simulation_counts:
            result = validation_engine.simulate_dcf_valuation(
                num_simulations=count,
                random_state=42  # Same seed for comparison
            )
            means.append(result.statistics['mean'])
            stds.append(result.statistics['std'])

        # Validate convergence - later results should be more stable
        # Standard error should decrease with sqrt(n)
        for i in range(1, len(means)):
            ratio = simulation_counts[i] / simulation_counts[0]
            expected_se_ratio = 1 / np.sqrt(ratio)

            # The relative change in standard error should decrease
            if i > 1:
                mean_change = abs(means[i] - means[i-1]) / means[i-1]
                assert mean_change < 0.1  # Less than 10% change in mean

        logger.info(f"Convergence test completed - Means: {means[-2:]}, Stds: {stds[-2:]}")


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])