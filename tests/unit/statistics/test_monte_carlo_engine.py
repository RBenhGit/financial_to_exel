"""
Unit Tests for Monte Carlo Simulation Engine
==========================================

This module contains comprehensive unit tests for the Monte Carlo simulation engine,
covering statistical distributions, simulation logic, risk metrics calculation,
and integration with financial analysis components.

Test Coverage
-------------
- ParameterDistribution class and sampling methods
- MonteCarloEngine simulation logic
- SimulationResult statistical calculations
- Risk metrics computation (VaR, CVaR, etc.)
- DCF integration functionality
- Error handling and edge cases

Usage
-----
Run tests with: pytest tests/unit/statistics/test_monte_carlo_engine.py -v
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the classes to test
try:
    from core.analysis.statistics.monte_carlo_engine import (
        MonteCarloEngine,
        ParameterDistribution,
        DistributionType,
        SimulationResult,
        RiskMetrics,
        quick_dcf_simulation,
        create_standard_scenarios
    )
    MONTE_CARLO_AVAILABLE = True
except ImportError:
    MONTE_CARLO_AVAILABLE = False
    pytest.skip("Monte Carlo engine not available", allow_module_level=True)


class TestParameterDistribution:
    """Test suite for ParameterDistribution class."""

    def test_normal_distribution_creation(self):
        """Test creation of normal distribution."""
        dist = ParameterDistribution(
            distribution=DistributionType.NORMAL,
            params={'mean': 0.05, 'std': 0.02},
            name='Test Distribution'
        )

        assert dist.distribution == DistributionType.NORMAL
        assert dist.params['mean'] == 0.05
        assert dist.params['std'] == 0.02
        assert dist.name == 'Test Distribution'

    def test_normal_distribution_sampling(self):
        """Test normal distribution sampling."""
        dist = ParameterDistribution(
            distribution=DistributionType.NORMAL,
            params={'mean': 0.10, 'std': 0.02},
            name='Revenue Growth'
        )

        samples = dist.sample(1000, random_state=42)

        assert len(samples) == 1000
        assert abs(np.mean(samples) - 0.10) < 0.01  # Should be close to mean
        assert abs(np.std(samples) - 0.02) < 0.01   # Should be close to std

    def test_uniform_distribution_sampling(self):
        """Test uniform distribution sampling."""
        dist = ParameterDistribution(
            distribution=DistributionType.UNIFORM,
            params={'low': 0.05, 'high': 0.15},
            name='Discount Range'
        )

        samples = dist.sample(1000, random_state=42)

        assert len(samples) == 1000
        assert np.all(samples >= 0.05)
        assert np.all(samples <= 0.15)
        assert abs(np.mean(samples) - 0.10) < 0.01  # Should be near midpoint

    def test_beta_distribution_sampling(self):
        """Test beta distribution sampling."""
        dist = ParameterDistribution(
            distribution=DistributionType.BETA,
            params={'alpha': 2, 'beta': 3, 'low': 0, 'high': 1},
            name='Operating Margin'
        )

        samples = dist.sample(1000, random_state=42)

        assert len(samples) == 1000
        assert np.all(samples >= 0)
        assert np.all(samples <= 1)

    def test_triangular_distribution_sampling(self):
        """Test triangular distribution sampling."""
        dist = ParameterDistribution(
            distribution=DistributionType.TRIANGULAR,
            params={'left': 0.02, 'mode': 0.05, 'right': 0.08},
            name='Terminal Growth'
        )

        samples = dist.sample(1000, random_state=42)

        assert len(samples) == 1000
        assert np.all(samples >= 0.02)
        assert np.all(samples <= 0.08)

    def test_unsupported_distribution_raises_error(self):
        """Test that unsupported distribution raises ValueError."""
        dist = ParameterDistribution(
            distribution="unsupported",  # Invalid distribution type
            params={},
            name='Invalid'
        )

        with pytest.raises(ValueError, match="Unsupported distribution"):
            dist.sample(100)


class TestSimulationResult:
    """Test suite for SimulationResult class."""

    def test_simulation_result_initialization(self):
        """Test SimulationResult initialization and automatic calculations."""
        # Create test data with known statistical properties
        np.random.seed(42)
        test_values = np.random.normal(100, 20, 1000)

        result = SimulationResult(
            values=test_values,
            parameters={'test_param': 'test_value'}
        )

        # Check that statistics were calculated
        assert 'mean' in result.statistics
        assert 'median' in result.statistics
        assert 'std' in result.statistics
        assert 'variance' in result.statistics

        # Check that values are reasonable
        assert abs(result.statistics['mean'] - 100) < 5  # Should be near 100
        assert abs(result.statistics['std'] - 20) < 5    # Should be near 20

    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation."""
        # Create test data with known distribution
        test_values = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

        result = SimulationResult(values=test_values)

        # Check risk metrics
        assert result.risk_metrics is not None
        assert result.risk_metrics.var_5 == 10  # 5% of 10 values = 0.5, rounds to first value
        assert result.risk_metrics.upside_potential == 100  # 95th percentile

    def test_percentiles_calculation(self):
        """Test percentile calculations."""
        test_values = np.arange(1, 101)  # Values from 1 to 100

        result = SimulationResult(values=test_values)

        # Check key percentiles
        assert result.percentiles['p50'] == 50.5  # Median
        assert result.percentiles['p25'] == 25.75  # 25th percentile
        assert result.percentiles['p75'] == 75.25  # 75th percentile

    def test_summary_table_generation(self):
        """Test summary table generation."""
        test_values = np.random.normal(100, 15, 1000)

        result = SimulationResult(values=test_values)
        summary_df = result.summary_table()

        assert isinstance(summary_df, pd.DataFrame)
        assert 'Metric' in summary_df.columns
        assert 'Value' in summary_df.columns
        assert len(summary_df) > 0

    def test_properties_access(self):
        """Test property accessors."""
        test_values = np.array([10, 20, 30, 40, 50])

        result = SimulationResult(values=test_values)

        assert result.mean_value == 30
        assert result.median_value == 30
        assert isinstance(result.ci_95, tuple)
        assert len(result.ci_95) == 2


class TestMonteCarloEngine:
    """Test suite for MonteCarloEngine class."""

    def test_engine_initialization(self):
        """Test Monte Carlo engine initialization."""
        mock_calculator = Mock()
        engine = MonteCarloEngine(mock_calculator)

        assert engine.financial_calculator == mock_calculator
        assert isinstance(engine.distributions, dict)
        assert len(engine.distributions) == 0

    def test_add_parameter_distribution(self):
        """Test adding parameter distributions."""
        engine = MonteCarloEngine()

        dist = ParameterDistribution(
            distribution=DistributionType.NORMAL,
            params={'mean': 0.05, 'std': 0.02},
            name='Revenue Growth'
        )

        engine.add_parameter_distribution('revenue_growth', dist)

        assert 'revenue_growth' in engine.distributions
        assert engine.distributions['revenue_growth'] == dist

    def test_correlation_matrix_setting(self):
        """Test correlation matrix setting and validation."""
        engine = MonteCarloEngine()

        # Valid correlation matrix
        correlation_matrix = np.array([
            [1.0, 0.3],
            [0.3, 1.0]
        ])
        param_names = ['param1', 'param2']

        engine.set_correlation_matrix(param_names, correlation_matrix)

        assert engine.correlation_matrix is not None
        assert engine.correlation_params == param_names

    def test_invalid_correlation_matrix_raises_error(self):
        """Test that invalid correlation matrix raises ValueError."""
        engine = MonteCarloEngine()

        # Non-symmetric matrix
        invalid_matrix = np.array([
            [1.0, 0.3],
            [0.5, 1.0]  # Should be 0.3 for symmetry
        ])
        param_names = ['param1', 'param2']

        with pytest.raises(ValueError, match="symmetric"):
            engine.set_correlation_matrix(param_names, invalid_matrix)

    def test_dcf_simulation_basic(self):
        """Test basic DCF simulation functionality."""
        mock_calculator = Mock()
        mock_calculator.calculate_dcf_projections.return_value = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'revenue_growth_rate': 0.05,
            'operating_margin': 0.20
        }

        engine = MonteCarloEngine(mock_calculator)

        # Run small simulation for testing
        result = engine.simulate_dcf_valuation(
            num_simulations=100,
            revenue_growth_volatility=0.05,
            discount_rate_volatility=0.01,
            random_state=42
        )

        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0
        assert result.statistics['mean'] > 0  # Should have positive valuation

    def test_ddm_simulation_basic(self):
        """Test basic DDM simulation functionality."""
        engine = MonteCarloEngine()

        result = engine.simulate_dividend_discount_model(
            num_simulations=100,
            dividend_growth_volatility=0.10,
            required_return_volatility=0.01,
            random_state=42
        )

        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0
        assert result.statistics['mean'] > 0

    def test_scenario_analysis(self):
        """Test scenario analysis functionality."""
        engine = MonteCarloEngine()

        scenarios = {
            'Base Case': {
                'revenue_growth': 0.05,
                'discount_rate': 0.10,
                'terminal_growth': 0.03,
                'operating_margin': 0.20
            },
            'Bull Case': {
                'revenue_growth': 0.15,
                'discount_rate': 0.08,
                'terminal_growth': 0.04,
                'operating_margin': 0.25
            }
        }

        results = engine.run_scenario_analysis(scenarios, 'dcf')

        assert isinstance(results, dict)
        assert 'Base Case' in results
        assert 'Bull Case' in results
        assert results['Bull Case'] > results['Base Case']  # Bull case should have higher value

    def test_portfolio_var_calculation(self):
        """Test portfolio VaR calculation."""
        engine = MonteCarloEngine()

        # Create mock simulation results
        portfolio_weights = {'AAPL': 0.6, 'MSFT': 0.4}

        # Mock simulation results
        aapl_result = SimulationResult(values=np.random.normal(150, 30, 1000))
        msft_result = SimulationResult(values=np.random.normal(100, 20, 1000))

        individual_simulations = {
            'AAPL': aapl_result,
            'MSFT': msft_result
        }

        var_results = engine.calculate_portfolio_var(
            portfolio_weights,
            individual_simulations,
            confidence_level=0.05
        )

        assert isinstance(var_results, dict)
        assert 'portfolio_var' in var_results
        assert 'portfolio_cvar' in var_results
        assert 'portfolio_mean' in var_results


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_quick_dcf_simulation(self):
        """Test quick DCF simulation function."""
        mock_calculator = Mock()

        result = quick_dcf_simulation(
            mock_calculator,
            num_simulations=100,
            volatility_level='medium'
        )

        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0

    def test_create_standard_scenarios(self):
        """Test standard scenarios creation."""
        scenarios = create_standard_scenarios()

        assert isinstance(scenarios, dict)
        assert 'Base Case' in scenarios
        assert 'Optimistic' in scenarios
        assert 'Pessimistic' in scenarios

        # Check that scenarios have required parameters
        for scenario_name, params in scenarios.items():
            assert 'revenue_growth' in params
            assert 'discount_rate' in params
            assert 'terminal_growth' in params
            assert 'operating_margin' in params


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and error handling."""

    def test_empty_simulation_values(self):
        """Test handling of empty simulation values."""
        with pytest.raises(Exception):  # Should raise some kind of error
            SimulationResult(values=np.array([]))

    def test_single_value_simulation(self):
        """Test handling of single-value simulation."""
        result = SimulationResult(values=np.array([100.0]))

        assert result.statistics['mean'] == 100.0
        assert result.statistics['std'] == 0.0
        assert result.risk_metrics is not None

    def test_negative_simulation_values(self):
        """Test handling of negative simulation values."""
        negative_values = np.array([-10, -5, 0, 5, 10])

        result = SimulationResult(values=negative_values)

        assert result.statistics['mean'] == 0.0
        assert result.risk_metrics is not None
        assert result.risk_metrics.probability_of_loss > 0

    def test_extreme_volatility_parameters(self):
        """Test simulation with extreme volatility parameters."""
        engine = MonteCarloEngine()

        # Very high volatility should still produce reasonable results
        result = engine.simulate_dcf_valuation(
            num_simulations=100,
            revenue_growth_volatility=1.0,  # 100% volatility
            discount_rate_volatility=0.10,
            random_state=42
        )

        assert isinstance(result, SimulationResult)
        assert len(result.values) > 0

    def test_invalid_portfolio_weights(self):
        """Test portfolio VaR with invalid weights."""
        engine = MonteCarloEngine()

        # Weights don't sum to 1
        invalid_weights = {'AAPL': 0.6, 'MSFT': 0.5}  # Sums to 1.1
        mock_simulations = {
            'AAPL': SimulationResult(values=np.array([100, 110, 120])),
            'MSFT': SimulationResult(values=np.array([80, 90, 100]))
        }

        with pytest.raises(ValueError, match="sum to 1.0"):
            engine.calculate_portfolio_var(invalid_weights, mock_simulations)


class TestIntegrationWithFinancialCalculator:
    """Test suite for integration with FinancialCalculator."""

    def test_monte_carlo_with_mock_calculator(self):
        """Test Monte Carlo integration with mocked financial calculator."""
        mock_calculator = Mock()
        mock_calculator.calculate_dcf_projections.return_value = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'revenue_growth_rate': 0.05,
            'operating_margin': 0.20
        }

        engine = MonteCarloEngine(mock_calculator)

        result = engine.simulate_dcf_valuation(
            num_simulations=50,
            random_state=42
        )

        assert isinstance(result, SimulationResult)
        assert mock_calculator.calculate_dcf_projections.called

    def test_parameter_estimation_from_mock_data(self):
        """Test parameter estimation with mock historical data."""
        # This would test the parameter estimation functionality
        # when integrated with actual financial calculator data
        pass  # Placeholder for more complex integration tests


@pytest.fixture
def sample_simulation_result():
    """Fixture providing a sample simulation result for testing."""
    np.random.seed(42)
    values = np.random.normal(100, 20, 1000)
    return SimulationResult(
        values=values,
        parameters={'num_simulations': 1000, 'test_mode': True}
    )


@pytest.fixture
def sample_monte_carlo_engine():
    """Fixture providing a configured Monte Carlo engine for testing."""
    engine = MonteCarloEngine()

    # Add some sample distributions
    revenue_dist = ParameterDistribution(
        distribution=DistributionType.NORMAL,
        params={'mean': 0.05, 'std': 0.02},
        name='Revenue Growth'
    )

    discount_dist = ParameterDistribution(
        distribution=DistributionType.NORMAL,
        params={'mean': 0.10, 'std': 0.01},
        name='Discount Rate'
    )

    engine.add_parameter_distribution('revenue_growth', revenue_dist)
    engine.add_parameter_distribution('discount_rate', discount_dist)

    return engine


class TestWithFixtures:
    """Test suite using fixtures."""

    def test_sample_result_properties(self, sample_simulation_result):
        """Test sample simulation result properties."""
        result = sample_simulation_result

        assert abs(result.mean_value - 100) < 5
        assert result.statistics['count'] == 1000
        assert result.risk_metrics is not None

    def test_sample_engine_configuration(self, sample_monte_carlo_engine):
        """Test sample engine configuration."""
        engine = sample_monte_carlo_engine

        assert len(engine.distributions) == 2
        assert 'revenue_growth' in engine.distributions
        assert 'discount_rate' in engine.distributions


# Performance and stress tests
class TestPerformance:
    """Test suite for performance characteristics."""

    @pytest.mark.slow
    def test_large_simulation_performance(self):
        """Test performance with large number of simulations."""
        engine = MonteCarloEngine()

        # This test would be marked as slow and might be skipped in regular test runs
        result = engine.simulate_dcf_valuation(
            num_simulations=10000,
            random_state=42
        )

        assert isinstance(result, SimulationResult)
        assert len(result.values) == 10000

    def test_memory_usage_with_large_simulations(self):
        """Test that large simulations don't cause memory issues."""
        # This would monitor memory usage during large simulations
        pass  # Placeholder for memory monitoring tests


# Integration test markers
pytestmark = [
    pytest.mark.unit,  # Mark all tests in this module as unit tests
]

# Conditional test execution
if not MONTE_CARLO_AVAILABLE:
    pytest.skip("Monte Carlo engine not available", allow_module_level=True)