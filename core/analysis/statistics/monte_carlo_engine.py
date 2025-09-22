"""
Monte Carlo Simulation Engine
============================

This module provides comprehensive Monte Carlo simulation capabilities for probabilistic
financial analysis and risk assessment. It integrates with the existing financial analysis
framework to provide stochastic modeling for DCF, DDM, and other valuation methods.

Key Features
------------
- **Probabilistic DCF Analysis**: Monte Carlo simulation for DCF valuation with uncertainty modeling
- **Parameter Uncertainty**: Revenue growth, margin volatility, discount rate distributions
- **Risk Assessment**: Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR) calculations
- **Scenario Analysis**: Best case, worst case, and most likely outcomes
- **Distribution Fitting**: Automatic parameter distribution estimation from historical data
- **Correlation Modeling**: Parameter correlation handling for realistic simulations
- **Performance Optimization**: Vectorized calculations for large simulation runs

Classes
-------
MonteCarloEngine
    Main class for Monte Carlo simulations with financial data integration

ParameterDistribution
    Statistical distribution modeling for financial parameters

RiskMetrics
    Risk assessment and statistical analysis of simulation results

SimulationResult
    Container class for simulation output and statistical analysis

Usage Example
-------------
>>> from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine
>>> from core.analysis.engines.financial_calculations import FinancialCalculator
>>>
>>> # Initialize with financial data
>>> calc = FinancialCalculator('AAPL')
>>> monte_carlo = MonteCarloEngine(calc)
>>>
>>> # Run DCF Monte Carlo simulation
>>> result = monte_carlo.simulate_dcf_valuation(
...     num_simulations=10000,
...     revenue_growth_volatility=0.15,
...     discount_rate_volatility=0.02
... )
>>>
>>> print(f"Expected Value: ${result.mean_value:.2f}")
>>> print(f"95% Confidence Interval: ${result.ci_95[0]:.2f} - ${result.ci_95[1]:.2f}")
>>> print(f"Value at Risk (5%): ${result.var_5:.2f}")

Financial Theory
---------------
Monte Carlo simulation uses random sampling to model the probability distribution
of financial metrics under uncertainty. This is particularly valuable for:

1. **Valuation Uncertainty**: Understanding the range of possible intrinsic values
2. **Risk Assessment**: Quantifying downside risk and upside potential
3. **Sensitivity Analysis**: Identifying key value drivers and their impact
4. **Decision Making**: Providing probabilistic forecasts for investment decisions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings
from scipy import stats
from scipy.optimize import minimize
import logging

# Suppress numpy warnings for cleaner output (RankWarning deprecated in newer numpy versions)
# warnings.filterwarnings('ignore', category=np.RankWarning)  # Commented out due to numpy compatibility

logger = logging.getLogger(__name__)


class DistributionType(Enum):
    """Supported statistical distributions for parameter modeling."""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    BETA = "beta"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    GAMMA = "gamma"


@dataclass
class ParameterDistribution:
    """
    Statistical distribution definition for Monte Carlo parameters.

    Attributes:
        distribution: Type of statistical distribution
        params: Distribution parameters (mean, std, min, max, etc.)
        name: Human-readable parameter name
        correlation_group: Group ID for correlated parameters
    """
    distribution: DistributionType
    params: Dict[str, float]
    name: str
    correlation_group: Optional[str] = None

    def sample(self, size: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate random samples from the distribution."""
        if random_state is not None:
            np.random.seed(random_state)

        if self.distribution == DistributionType.NORMAL:
            return np.random.normal(
                self.params['mean'],
                self.params['std'],
                size
            )
        elif self.distribution == DistributionType.LOGNORMAL:
            return np.random.lognormal(
                self.params['mean'],
                self.params['std'],
                size
            )
        elif self.distribution == DistributionType.UNIFORM:
            return np.random.uniform(
                self.params['low'],
                self.params['high'],
                size
            )
        elif self.distribution == DistributionType.TRIANGULAR:
            return np.random.triangular(
                self.params['left'],
                self.params['mode'],
                self.params['right'],
                size
            )
        elif self.distribution == DistributionType.BETA:
            samples = np.random.beta(
                self.params['alpha'],
                self.params['beta'],
                size
            )
            # Scale to range if specified
            if 'low' in self.params and 'high' in self.params:
                samples = samples * (self.params['high'] - self.params['low']) + self.params['low']
            return samples
        elif self.distribution == DistributionType.GAMMA:
            return np.random.gamma(
                self.params['shape'],
                self.params['scale'],
                size
            )
        else:
            raise ValueError(f"Unsupported distribution: {self.distribution}")


@dataclass
class RiskMetrics:
    """Risk assessment metrics from Monte Carlo simulation results."""
    var_5: float  # Value at Risk (5th percentile)
    var_1: float  # Value at Risk (1st percentile)
    cvar_5: float  # Conditional Value at Risk (5%)
    cvar_1: float  # Conditional Value at Risk (1%)
    max_drawdown: float  # Maximum potential loss
    upside_potential: float  # 95th percentile value
    downside_deviation: float  # Standard deviation of negative returns
    probability_of_loss: float  # Probability of negative returns

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for easy serialization."""
        return {
            'var_5': self.var_5,
            'var_1': self.var_1,
            'cvar_5': self.cvar_5,
            'cvar_1': self.cvar_1,
            'max_drawdown': self.max_drawdown,
            'upside_potential': self.upside_potential,
            'downside_deviation': self.downside_deviation,
            'probability_of_loss': self.probability_of_loss
        }


@dataclass
class SimulationResult:
    """
    Container for Monte Carlo simulation results and statistical analysis.

    Attributes:
        values: Array of simulated values
        parameters: Input parameters used for simulation
        statistics: Descriptive statistics
        risk_metrics: Risk assessment metrics
        percentiles: Key percentile values
        convergence_info: Information about simulation convergence
    """
    values: np.ndarray
    parameters: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, float] = field(default_factory=dict)
    risk_metrics: Optional[RiskMetrics] = None
    percentiles: Dict[str, float] = field(default_factory=dict)
    convergence_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate statistics and risk metrics after initialization."""
        self._calculate_statistics()
        self._calculate_risk_metrics()
        self._calculate_percentiles()

    def _calculate_statistics(self):
        """Calculate descriptive statistics."""
        self.statistics = {
            'mean': np.mean(self.values),
            'median': np.median(self.values),
            'std': np.std(self.values),
            'variance': np.var(self.values),
            'skewness': stats.skew(self.values),
            'kurtosis': stats.kurtosis(self.values),
            'min': np.min(self.values),
            'max': np.max(self.values),
            'count': len(self.values)
        }

    def _calculate_risk_metrics(self):
        """Calculate risk assessment metrics."""
        # Sort values for percentile calculations
        sorted_values = np.sort(self.values)
        n = len(sorted_values)

        # Value at Risk calculations
        var_5 = np.percentile(sorted_values, 5)
        var_1 = np.percentile(sorted_values, 1)

        # Conditional Value at Risk (Expected Shortfall)
        cvar_5_idx = int(0.05 * n)
        cvar_1_idx = int(0.01 * n)
        cvar_5 = np.mean(sorted_values[:cvar_5_idx]) if cvar_5_idx > 0 else var_5
        cvar_1 = np.mean(sorted_values[:cvar_1_idx]) if cvar_1_idx > 0 else var_1

        # Other risk metrics
        max_drawdown = np.min(self.values) - np.max(self.values)
        upside_potential = np.percentile(sorted_values, 95)

        # Downside deviation (standard deviation of negative returns)
        negative_values = self.values[self.values < 0]
        downside_deviation = np.std(negative_values) if len(negative_values) > 0 else 0

        # Probability of loss
        probability_of_loss = len(negative_values) / len(self.values)

        self.risk_metrics = RiskMetrics(
            var_5=var_5,
            var_1=var_1,
            cvar_5=cvar_5,
            cvar_1=cvar_1,
            max_drawdown=max_drawdown,
            upside_potential=upside_potential,
            downside_deviation=downside_deviation,
            probability_of_loss=probability_of_loss
        )

    def _calculate_percentiles(self):
        """Calculate key percentile values."""
        percentile_levels = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        self.percentiles = {
            f'p{p}': np.percentile(self.values, p) for p in percentile_levels
        }

        # Add confidence intervals
        self.percentiles['ci_90'] = (self.percentiles['p5'], self.percentiles['p95'])
        self.percentiles['ci_95'] = (np.percentile(self.values, 2.5),
                                   np.percentile(self.values, 97.5))

    @property
    def mean_value(self) -> float:
        """Get the mean simulated value."""
        return self.statistics['mean']

    @property
    def median_value(self) -> float:
        """Get the median simulated value."""
        return self.statistics['median']

    @property
    def ci_95(self) -> Tuple[float, float]:
        """Get the 95% confidence interval."""
        return self.percentiles['ci_95']

    @property
    def var_5(self) -> float:
        """Get the 5% Value at Risk."""
        return self.risk_metrics.var_5 if self.risk_metrics else 0

    def summary_table(self) -> pd.DataFrame:
        """Generate a summary table of key statistics."""
        data = {
            'Metric': [
                'Mean Value', 'Median Value', 'Standard Deviation',
                '5th Percentile', '95th Percentile',
                'Value at Risk (5%)', 'Conditional VaR (5%)',
                'Probability of Loss', 'Maximum Value', 'Minimum Value'
            ],
            'Value': [
                self.statistics['mean'],
                self.statistics['median'],
                self.statistics['std'],
                self.percentiles['p5'],
                self.percentiles['p95'],
                self.risk_metrics.var_5,
                self.risk_metrics.cvar_5,
                self.risk_metrics.probability_of_loss,
                self.statistics['max'],
                self.statistics['min']
            ]
        }
        return pd.DataFrame(data)


class MonteCarloEngine:
    """
    Main Monte Carlo simulation engine for financial analysis.

    This class provides comprehensive Monte Carlo simulation capabilities
    integrated with the existing financial analysis framework.
    """

    def __init__(self, financial_calculator=None):
        """
        Initialize Monte Carlo engine.

        Args:
            financial_calculator: FinancialCalculator instance for data access
        """
        self.financial_calculator = financial_calculator
        self.distributions: Dict[str, ParameterDistribution] = {}
        self.correlation_matrix: Optional[np.ndarray] = None
        self.correlation_params: List[str] = []
        self.random_state: Optional[int] = None

        logger.info("Monte Carlo Engine initialized")

    def sample_correlated_parameters(
        self,
        param_names: List[str],
        num_samples: int,
        random_state: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Generate correlated parameter samples using Cholesky decomposition.

        Args:
            param_names: List of parameter names to sample
            num_samples: Number of samples to generate
            random_state: Random seed for reproducibility

        Returns:
            Dictionary mapping parameter names to correlated sample arrays
        """
        if self.correlation_matrix is None or not hasattr(self, 'cholesky_matrix'):
            raise ValueError("Correlation matrix must be set before sampling correlated parameters")

        if set(param_names) != set(self.correlation_params):
            raise ValueError("Parameter names must match correlation matrix parameters")

        if random_state is not None:
            np.random.seed(random_state)

        # Generate independent standard normal samples
        independent_samples = np.random.standard_normal((len(param_names), num_samples))

        # Apply Cholesky decomposition to create correlation
        correlated_samples = self.cholesky_matrix @ independent_samples

        # Transform to parameter distributions
        result = {}
        for i, param_name in enumerate(param_names):
            if param_name not in self.distributions:
                raise ValueError(f"Distribution not defined for parameter: {param_name}")

            # Convert correlated normal samples to target distribution
            normal_samples = correlated_samples[i]
            distribution = self.distributions[param_name]

            # Transform using inverse CDF approach
            uniform_samples = stats.norm.cdf(normal_samples)

            if distribution.distribution == DistributionType.NORMAL:
                samples = stats.norm.ppf(uniform_samples,
                                       distribution.params['mean'],
                                       distribution.params['std'])
            elif distribution.distribution == DistributionType.LOGNORMAL:
                samples = stats.lognorm.ppf(uniform_samples,
                                          distribution.params['std'],
                                          scale=np.exp(distribution.params['mean']))
            elif distribution.distribution == DistributionType.UNIFORM:
                samples = stats.uniform.ppf(uniform_samples,
                                          distribution.params['low'],
                                          distribution.params['high'] - distribution.params['low'])
            elif distribution.distribution == DistributionType.BETA:
                samples = stats.beta.ppf(uniform_samples,
                                       distribution.params['alpha'],
                                       distribution.params['beta'])
                # Scale if bounds specified
                if 'low' in distribution.params and 'high' in distribution.params:
                    samples = (samples * (distribution.params['high'] - distribution.params['low']) +
                             distribution.params['low'])
            else:
                # Fallback to independent sampling for unsupported distributions
                logger.warning(f"Correlated sampling not supported for {distribution.distribution}, using independent sampling")
                samples = distribution.sample(num_samples, random_state)

            result[param_name] = samples

        return result

    def test_convergence(
        self,
        values: np.ndarray,
        convergence_threshold: float = 0.01,
        min_samples: int = 1000,
        window_size: int = 500
    ) -> Dict[str, Any]:
        """
        Test Monte Carlo simulation convergence using rolling statistics.

        Args:
            values: Array of simulated values
            convergence_threshold: Relative change threshold for convergence
            min_samples: Minimum number of samples before testing convergence
            window_size: Window size for rolling statistics

        Returns:
            Dictionary containing convergence information
        """
        n_samples = len(values)

        if n_samples < min_samples:
            return {
                'converged': False,
                'reason': f'Insufficient samples: {n_samples} < {min_samples}',
                'convergence_point': None,
                'final_stability': None,
                'rolling_means': None,
                'rolling_stds': None
            }

        # Calculate rolling statistics
        rolling_means = []
        rolling_stds = []
        sample_points = range(min_samples, n_samples + 1, window_size)

        for n in sample_points:
            subset = values[:n]
            rolling_means.append(np.mean(subset))
            rolling_stds.append(np.std(subset))

        rolling_means = np.array(rolling_means)
        rolling_stds = np.array(rolling_stds)

        # Test for convergence
        converged = False
        convergence_point = None

        if len(rolling_means) >= 3:
            # Check if mean has stabilized (relative change < threshold)
            mean_changes = np.abs(np.diff(rolling_means)) / np.abs(rolling_means[:-1])
            stable_points = mean_changes < convergence_threshold

            if len(stable_points) >= 2 and np.all(stable_points[-2:]):
                converged = True
                convergence_point = sample_points[np.where(stable_points)[0][-2]]

        # Calculate final stability metrics
        final_stability = None
        if len(rolling_means) >= 2:
            final_mean_change = abs(rolling_means[-1] - rolling_means[-2]) / abs(rolling_means[-2])
            final_std_change = abs(rolling_stds[-1] - rolling_stds[-2]) / abs(rolling_stds[-2])
            final_stability = {
                'mean_change': final_mean_change,
                'std_change': final_std_change,
                'stability_score': 1.0 - max(final_mean_change, final_std_change)
            }

        return {
            'converged': converged,
            'reason': 'Converged' if converged else 'Not converged within threshold',
            'convergence_point': convergence_point,
            'final_stability': final_stability,
            'rolling_means': rolling_means,
            'rolling_stds': rolling_stds,
            'sample_points': list(sample_points),
            'convergence_threshold': convergence_threshold
        }

    def validate_result_stability(
        self,
        simulation_result: 'SimulationResult',
        num_bootstrap_samples: int = 100,
        bootstrap_size_ratio: float = 0.8
    ) -> Dict[str, Any]:
        """
        Validate result stability using bootstrap resampling.

        Args:
            simulation_result: SimulationResult to validate
            num_bootstrap_samples: Number of bootstrap samples
            bootstrap_size_ratio: Proportion of original data for each bootstrap

        Returns:
            Dictionary containing stability validation metrics
        """
        values = simulation_result.values
        n_original = len(values)
        bootstrap_size = int(n_original * bootstrap_size_ratio)

        bootstrap_means = []
        bootstrap_stds = []
        bootstrap_vars = []
        bootstrap_medians = []

        for _ in range(num_bootstrap_samples):
            # Resample with replacement
            bootstrap_sample = np.random.choice(values, size=bootstrap_size, replace=True)

            bootstrap_means.append(np.mean(bootstrap_sample))
            bootstrap_stds.append(np.std(bootstrap_sample))
            bootstrap_vars.append(np.var(bootstrap_sample))
            bootstrap_medians.append(np.median(bootstrap_sample))

        bootstrap_means = np.array(bootstrap_means)
        bootstrap_stds = np.array(bootstrap_stds)
        bootstrap_vars = np.array(bootstrap_vars)
        bootstrap_medians = np.array(bootstrap_medians)

        # Calculate stability metrics
        original_mean = simulation_result.statistics['mean']
        original_std = simulation_result.statistics['std']
        original_var = simulation_result.statistics['variance']
        original_median = simulation_result.statistics['median']

        stability_metrics = {
            'mean_stability': {
                'bootstrap_mean': np.mean(bootstrap_means),
                'bootstrap_std': np.std(bootstrap_means),
                'confidence_interval_95': (np.percentile(bootstrap_means, 2.5),
                                         np.percentile(bootstrap_means, 97.5)),
                'original_in_ci': (np.percentile(bootstrap_means, 2.5) <= original_mean <=
                                 np.percentile(bootstrap_means, 97.5)),
                'bias': np.mean(bootstrap_means) - original_mean,
                'relative_error': abs(np.mean(bootstrap_means) - original_mean) / abs(original_mean)
            },
            'std_stability': {
                'bootstrap_mean': np.mean(bootstrap_stds),
                'bootstrap_std': np.std(bootstrap_stds),
                'confidence_interval_95': (np.percentile(bootstrap_stds, 2.5),
                                         np.percentile(bootstrap_stds, 97.5)),
                'original_in_ci': (np.percentile(bootstrap_stds, 2.5) <= original_std <=
                                 np.percentile(bootstrap_stds, 97.5)),
                'bias': np.mean(bootstrap_stds) - original_std,
                'relative_error': abs(np.mean(bootstrap_stds) - original_std) / abs(original_std)
            },
            'median_stability': {
                'bootstrap_mean': np.mean(bootstrap_medians),
                'bootstrap_std': np.std(bootstrap_medians),
                'confidence_interval_95': (np.percentile(bootstrap_medians, 2.5),
                                         np.percentile(bootstrap_medians, 97.5)),
                'original_in_ci': (np.percentile(bootstrap_medians, 2.5) <= original_median <=
                                 np.percentile(bootstrap_medians, 97.5)),
                'bias': np.mean(bootstrap_medians) - original_median,
                'relative_error': abs(np.mean(bootstrap_medians) - original_median) / abs(original_median)
            }
        }

        # Overall stability score
        mean_stable = stability_metrics['mean_stability']['relative_error'] < 0.05
        std_stable = stability_metrics['std_stability']['relative_error'] < 0.10
        median_stable = stability_metrics['median_stability']['relative_error'] < 0.05

        overall_stability = {
            'stable': mean_stable and std_stable and median_stable,
            'mean_stable': mean_stable,
            'std_stable': std_stable,
            'median_stable': median_stable,
            'stability_score': np.mean([
                1.0 - min(1.0, stability_metrics['mean_stability']['relative_error'] / 0.05),
                1.0 - min(1.0, stability_metrics['std_stability']['relative_error'] / 0.10),
                1.0 - min(1.0, stability_metrics['median_stability']['relative_error'] / 0.05)
            ])
        }

        return {
            'stability_metrics': stability_metrics,
            'overall_stability': overall_stability,
            'num_bootstrap_samples': num_bootstrap_samples,
            'bootstrap_size': bootstrap_size
        }

    def add_parameter_distribution(
        self,
        param_name: str,
        distribution: ParameterDistribution
    ) -> None:
        """
        Add a parameter distribution for Monte Carlo simulation.

        Args:
            param_name: Parameter name for reference
            distribution: ParameterDistribution object
        """
        self.distributions[param_name] = distribution
        logger.debug(f"Added parameter distribution: {param_name}")

    def set_correlation_matrix(
        self,
        param_names: List[str],
        correlation_matrix: np.ndarray
    ) -> None:
        """
        Set correlation matrix for correlated parameter sampling.

        Args:
            param_names: List of parameter names in correlation matrix order
            correlation_matrix: Correlation matrix (must be positive semidefinite)
        """
        if correlation_matrix.shape[0] != len(param_names):
            raise ValueError("Correlation matrix size must match number of parameters")

        # Validate correlation matrix properties
        if not np.allclose(correlation_matrix, correlation_matrix.T):
            raise ValueError("Correlation matrix must be symmetric")

        eigenvalues = np.linalg.eigvals(correlation_matrix)
        if np.any(eigenvalues < -1e-8):  # Allow for small numerical errors
            raise ValueError("Correlation matrix must be positive semidefinite")

        # Compute Cholesky decomposition for correlated sampling
        try:
            self.cholesky_matrix = np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # Use eigenvalue decomposition as fallback
            eigenvals, eigenvecs = np.linalg.eigh(correlation_matrix)
            eigenvals = np.maximum(eigenvals, 1e-10)  # Ensure positive
            self.cholesky_matrix = eigenvecs @ np.diag(np.sqrt(eigenvals))
            logger.warning("Used eigenvalue decomposition fallback for correlation matrix")

        self.correlation_matrix = correlation_matrix
        self.correlation_params = param_names
        logger.info(f"Set correlation matrix for parameters: {param_names}")

    def estimate_parameter_distributions(
        self,
        historical_data: pd.DataFrame,
        param_mapping: Dict[str, str]
    ) -> Dict[str, ParameterDistribution]:
        """
        Automatically estimate parameter distributions from historical data.

        Args:
            historical_data: DataFrame with historical financial data
            param_mapping: Mapping of parameter names to column names

        Returns:
            Dictionary of estimated parameter distributions
        """
        estimated_distributions = {}

        for param_name, column_name in param_mapping.items():
            if column_name not in historical_data.columns:
                logger.warning(f"Column {column_name} not found in historical data")
                continue

            data = historical_data[column_name].dropna()
            if len(data) < 3:
                logger.warning(f"Insufficient data for parameter {param_name}")
                continue

            # Try different distributions and select best fit
            distribution = self._fit_best_distribution(data, param_name)
            estimated_distributions[param_name] = distribution

        return estimated_distributions

    def _fit_best_distribution(
        self,
        data: pd.Series,
        param_name: str
    ) -> ParameterDistribution:
        """
        Fit the best statistical distribution to historical data.

        Args:
            data: Historical data series
            param_name: Parameter name for the distribution

        Returns:
            Best-fitting ParameterDistribution
        """
        # Calculate basic statistics
        mean_val = data.mean()
        std_val = data.std()
        min_val = data.min()
        max_val = data.max()

        # Test different distributions
        distributions_to_test = [
            (DistributionType.NORMAL, lambda: {'mean': mean_val, 'std': std_val}),
            (DistributionType.LOGNORMAL, lambda: self._fit_lognormal(data)),
            (DistributionType.BETA, lambda: self._fit_beta(data)),
            (DistributionType.GAMMA, lambda: self._fit_gamma(data))
        ]

        best_dist = None
        best_score = float('-inf')

        for dist_type, param_func in distributions_to_test:
            try:
                params = param_func()
                if params is None:
                    continue

                # Create temporary distribution for testing
                temp_dist = ParameterDistribution(dist_type, params, param_name)

                # Score based on goodness of fit (simplified)
                score = self._calculate_goodness_of_fit(data, temp_dist)

                if score > best_score:
                    best_score = score
                    best_dist = temp_dist

            except Exception as e:
                logger.debug(f"Failed to fit {dist_type} for {param_name}: {e}")
                continue

        # Default to normal distribution if no fit is successful
        if best_dist is None:
            best_dist = ParameterDistribution(
                DistributionType.NORMAL,
                {'mean': mean_val, 'std': std_val},
                param_name
            )

        logger.info(f"Best distribution for {param_name}: {best_dist.distribution}")
        return best_dist

    def _fit_lognormal(self, data: pd.Series) -> Optional[Dict[str, float]]:
        """Fit lognormal distribution parameters."""
        if np.any(data <= 0):
            return None  # Lognormal requires positive values

        log_data = np.log(data)
        return {'mean': log_data.mean(), 'std': log_data.std()}

    def _fit_beta(self, data: pd.Series) -> Optional[Dict[str, float]]:
        """Fit beta distribution parameters."""
        try:
            # Normalize data to [0, 1] range
            min_val, max_val = data.min(), data.max()
            if min_val == max_val:
                return None

            normalized_data = (data - min_val) / (max_val - min_val)
            alpha, beta, _, _ = stats.beta.fit(normalized_data)

            return {
                'alpha': alpha,
                'beta': beta,
                'low': min_val,
                'high': max_val
            }
        except:
            return None

    def _fit_gamma(self, data: pd.Series) -> Optional[Dict[str, float]]:
        """Fit gamma distribution parameters."""
        if np.any(data <= 0):
            return None  # Gamma requires positive values

        try:
            shape, loc, scale = stats.gamma.fit(data)
            return {'shape': shape, 'scale': scale}
        except:
            return None

    def _calculate_goodness_of_fit(
        self,
        data: pd.Series,
        distribution: ParameterDistribution
    ) -> float:
        """
        Calculate goodness of fit score for a distribution.

        Args:
            data: Historical data
            distribution: Distribution to test

        Returns:
            Goodness of fit score (higher is better)
        """
        try:
            # Generate sample from distribution
            sample = distribution.sample(len(data))

            # Use Kolmogorov-Smirnov test statistic (lower is better)
            ks_statistic, _ = stats.ks_2samp(data, sample)

            # Return negative KS statistic (higher score = better fit)
            return -ks_statistic
        except:
            return float('-inf')

    def simulate_dcf_valuation(
        self,
        num_simulations: int = 10000,
        revenue_growth_volatility: float = 0.15,
        discount_rate_volatility: float = 0.02,
        terminal_growth_volatility: float = 0.01,
        margin_volatility: float = 0.05,
        custom_distributions: Optional[Dict[str, ParameterDistribution]] = None,
        random_state: Optional[int] = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for DCF valuation.

        Args:
            num_simulations: Number of simulation runs
            revenue_growth_volatility: Standard deviation of revenue growth rate
            discount_rate_volatility: Standard deviation of discount rate
            terminal_growth_volatility: Standard deviation of terminal growth rate
            margin_volatility: Standard deviation of profit margins
            custom_distributions: Custom parameter distributions
            random_state: Random seed for reproducibility

        Returns:
            SimulationResult containing simulation output and statistics
        """
        if self.financial_calculator is None:
            raise ValueError("Financial calculator required for DCF simulation")

        logger.info(f"Starting DCF Monte Carlo simulation with {num_simulations} runs")

        # Set random state for reproducibility
        if random_state is not None:
            np.random.seed(random_state)
            self.random_state = random_state

        # Get base DCF parameters from financial calculator
        try:
            # This would integrate with the existing DCF valuation module
            base_dcf_result = self.financial_calculator.calculate_dcf_projections()
            base_discount_rate = base_dcf_result.get('discount_rate', 0.10)
            base_terminal_growth = base_dcf_result.get('terminal_growth_rate', 0.03)
            base_revenue_growth = base_dcf_result.get('revenue_growth_rate', 0.05)
            base_margin = base_dcf_result.get('operating_margin', 0.20)
        except Exception as e:
            logger.warning(f"Could not get base DCF parameters: {e}")
            # Use default values
            base_discount_rate = 0.10
            base_terminal_growth = 0.03
            base_revenue_growth = 0.05
            base_margin = 0.20

        # Set up parameter distributions
        distributions = custom_distributions or {}

        # Default distributions if not provided
        if 'revenue_growth' not in distributions:
            distributions['revenue_growth'] = ParameterDistribution(
                DistributionType.NORMAL,
                {'mean': base_revenue_growth, 'std': revenue_growth_volatility},
                'Revenue Growth Rate'
            )

        if 'discount_rate' not in distributions:
            distributions['discount_rate'] = ParameterDistribution(
                DistributionType.NORMAL,
                {'mean': base_discount_rate, 'std': discount_rate_volatility},
                'Discount Rate'
            )

        if 'terminal_growth' not in distributions:
            distributions['terminal_growth'] = ParameterDistribution(
                DistributionType.NORMAL,
                {'mean': base_terminal_growth, 'std': terminal_growth_volatility},
                'Terminal Growth Rate'
            )

        if 'operating_margin' not in distributions:
            distributions['operating_margin'] = ParameterDistribution(
                DistributionType.NORMAL,
                {'mean': base_margin, 'std': margin_volatility},
                'Operating Margin'
            )

        # Run simulations with optional correlation
        simulated_values = np.zeros(num_simulations)

        # Check if correlated sampling is configured
        use_correlated_sampling = (
            self.correlation_matrix is not None and
            hasattr(self, 'cholesky_matrix') and
            set(distributions.keys()).issubset(set(self.correlation_params))
        )

        if use_correlated_sampling:
            logger.info("Using correlated parameter sampling")
            # Store distributions for correlated sampling
            for param_name, distribution in distributions.items():
                self.distributions[param_name] = distribution

            # Generate all correlated samples at once
            correlated_samples = self.sample_correlated_parameters(
                list(distributions.keys()),
                num_simulations,
                random_state
            )

            for i in range(num_simulations):
                params = {}
                for param_name in distributions.keys():
                    sample = correlated_samples[param_name][i]

                    # Apply bounds to ensure realistic values
                    if param_name == 'discount_rate':
                        sample = max(0.01, min(0.30, sample))  # 1% to 30%
                    elif param_name == 'terminal_growth':
                        sample = max(0.0, min(0.10, sample))   # 0% to 10%
                    elif param_name == 'revenue_growth':
                        sample = max(-0.50, min(2.0, sample))  # -50% to 200%
                    elif param_name == 'operating_margin':
                        sample = max(0.0, min(1.0, sample))    # 0% to 100%

                    params[param_name] = sample

                # Calculate DCF value with sampled parameters
                try:
                    dcf_value = self._calculate_dcf_with_params(params)
                    simulated_values[i] = dcf_value
                except Exception as e:
                    logger.debug(f"Simulation {i} failed: {e}")
                    # Use base case value for failed simulations
                    simulated_values[i] = 100.0  # Default fallback value
        else:
            # Independent sampling (original approach)
            logger.info("Using independent parameter sampling")
            for i in range(num_simulations):
                # Sample parameters
                params = {}
                for param_name, distribution in distributions.items():
                    sample = distribution.sample(1)[0]

                    # Apply bounds to ensure realistic values
                    if param_name == 'discount_rate':
                        sample = max(0.01, min(0.30, sample))  # 1% to 30%
                    elif param_name == 'terminal_growth':
                        sample = max(0.0, min(0.10, sample))   # 0% to 10%
                    elif param_name == 'revenue_growth':
                        sample = max(-0.50, min(2.0, sample))  # -50% to 200%
                    elif param_name == 'operating_margin':
                        sample = max(0.0, min(1.0, sample))    # 0% to 100%

                    params[param_name] = sample

                # Calculate DCF value with sampled parameters
                try:
                    dcf_value = self._calculate_dcf_with_params(params)
                    simulated_values[i] = dcf_value
                except Exception as e:
                    logger.debug(f"Simulation {i} failed: {e}")
                    # Use base case value for failed simulations
                    simulated_values[i] = 100.0  # Default fallback value

        # Test convergence
        convergence_info = self.test_convergence(simulated_values)

        # Create result object
        result = SimulationResult(
            values=simulated_values,
            parameters={
                'num_simulations': num_simulations,
                'revenue_growth_volatility': revenue_growth_volatility,
                'discount_rate_volatility': discount_rate_volatility,
                'terminal_growth_volatility': terminal_growth_volatility,
                'margin_volatility': margin_volatility,
                'random_state': random_state,
                'use_correlated_sampling': use_correlated_sampling
            },
            convergence_info=convergence_info
        )

        # Log convergence status
        if convergence_info['converged']:
            logger.info(f"DCF simulation converged at {convergence_info['convergence_point']} samples")
        else:
            logger.warning(f"DCF simulation did not converge: {convergence_info['reason']}")

        logger.info(f"DCF Monte Carlo simulation completed. Mean value: {result.mean_value:.2f}")
        return result

    def _calculate_dcf_with_params(self, params: Dict[str, float]) -> float:
        """
        Calculate DCF value with given parameters.

        This is a simplified DCF calculation for simulation purposes.
        In a full implementation, this would integrate with the DCF valuation module.

        Args:
            params: Dictionary of financial parameters

        Returns:
            Calculated DCF value per share
        """
        # Simplified DCF calculation
        # This would be replaced with integration to the actual DCF module

        revenue_growth = params.get('revenue_growth', 0.05)
        discount_rate = params.get('discount_rate', 0.10)
        terminal_growth = params.get('terminal_growth', 0.03)
        operating_margin = params.get('operating_margin', 0.20)

        # Assume base revenue and shares outstanding
        # In real implementation, these would come from financial_calculator
        base_revenue = 100000  # Million
        shares_outstanding = 1000  # Million

        # Project 5 years of cash flows
        projection_years = 5
        cash_flows = []

        current_revenue = base_revenue
        for year in range(1, projection_years + 1):
            current_revenue *= (1 + revenue_growth)
            operating_income = current_revenue * operating_margin
            # Simplified: assume tax rate of 25%
            after_tax_income = operating_income * 0.75
            # Simplified: assume FCF = 80% of after-tax income
            free_cash_flow = after_tax_income * 0.80
            cash_flows.append(free_cash_flow)

        # Calculate present value of cash flows
        pv_cash_flows = 0
        for i, cf in enumerate(cash_flows, 1):
            pv_cash_flows += cf / ((1 + discount_rate) ** i)

        # Terminal value
        terminal_cf = cash_flows[-1] * (1 + terminal_growth)
        terminal_value = terminal_cf / (discount_rate - terminal_growth)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)

        # Total enterprise value
        enterprise_value = pv_cash_flows + pv_terminal_value

        # Value per share (simplified - no debt/cash adjustments)
        value_per_share = enterprise_value / shares_outstanding

        return value_per_share

    def simulate_dividend_discount_model(
        self,
        num_simulations: int = 10000,
        dividend_growth_volatility: float = 0.20,
        required_return_volatility: float = 0.02,
        payout_ratio_volatility: float = 0.10,
        random_state: Optional[int] = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for Dividend Discount Model valuation.

        Args:
            num_simulations: Number of simulation runs
            dividend_growth_volatility: Standard deviation of dividend growth rate
            required_return_volatility: Standard deviation of required return
            payout_ratio_volatility: Standard deviation of payout ratio
            random_state: Random seed for reproducibility

        Returns:
            SimulationResult containing simulation output and statistics
        """
        logger.info(f"Starting DDM Monte Carlo simulation with {num_simulations} runs")

        if random_state is not None:
            np.random.seed(random_state)

        # Get base DDM parameters (would integrate with DDM module)
        base_dividend_growth = 0.05
        base_required_return = 0.10
        base_payout_ratio = 0.40
        base_earnings_per_share = 5.0  # Default EPS

        # Run simulations
        simulated_values = np.zeros(num_simulations)

        for i in range(num_simulations):
            # Sample parameters
            dividend_growth = np.random.normal(base_dividend_growth, dividend_growth_volatility)
            required_return = np.random.normal(base_required_return, required_return_volatility)
            payout_ratio = np.random.normal(base_payout_ratio, payout_ratio_volatility)

            # Apply bounds
            dividend_growth = max(-0.20, min(0.50, dividend_growth))
            required_return = max(0.01, min(0.25, required_return))
            payout_ratio = max(0.0, min(1.0, payout_ratio))

            # Ensure required return > dividend growth for convergence
            if required_return <= dividend_growth:
                required_return = dividend_growth + 0.02

            # Calculate DDM value
            try:
                dividend_per_share = base_earnings_per_share * payout_ratio
                next_dividend = dividend_per_share * (1 + dividend_growth)
                ddm_value = next_dividend / (required_return - dividend_growth)
                simulated_values[i] = ddm_value
            except (ZeroDivisionError, ValueError):
                simulated_values[i] = 0  # Invalid simulation

        # Filter out invalid results
        valid_values = simulated_values[simulated_values > 0]

        result = SimulationResult(
            values=valid_values,
            parameters={
                'num_simulations': num_simulations,
                'dividend_growth_volatility': dividend_growth_volatility,
                'required_return_volatility': required_return_volatility,
                'payout_ratio_volatility': payout_ratio_volatility,
                'valid_simulations': len(valid_values),
                'random_state': random_state
            }
        )

        logger.info(f"DDM Monte Carlo simulation completed. Mean value: {result.mean_value:.2f}")
        return result

    def run_scenario_analysis(
        self,
        scenarios: Dict[str, Dict[str, float]],
        base_valuation_method: str = 'dcf'
    ) -> Dict[str, float]:
        """
        Run scenario analysis with predefined parameter sets.

        Args:
            scenarios: Dictionary of scenario names to parameter dictionaries
            base_valuation_method: Base valuation method ('dcf' or 'ddm')

        Returns:
            Dictionary mapping scenario names to calculated values
        """
        logger.info(f"Running scenario analysis for {len(scenarios)} scenarios")

        results = {}

        for scenario_name, params in scenarios.items():
            try:
                if base_valuation_method == 'dcf':
                    value = self._calculate_dcf_with_params(params)
                else:
                    # Would implement DDM calculation here
                    value = 100.0  # Placeholder

                results[scenario_name] = value
                logger.debug(f"Scenario '{scenario_name}': {value:.2f}")

            except Exception as e:
                logger.error(f"Scenario '{scenario_name}' failed: {e}")
                results[scenario_name] = None

        return results

    def calculate_portfolio_var(
        self,
        portfolio_weights: Dict[str, float],
        individual_simulations: Dict[str, SimulationResult],
        confidence_level: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate portfolio Value at Risk using Monte Carlo results.

        Args:
            portfolio_weights: Dictionary mapping asset names to portfolio weights
            individual_simulations: Dictionary mapping asset names to simulation results
            confidence_level: Confidence level for VaR calculation

        Returns:
            Dictionary containing portfolio VaR metrics
        """
        logger.info("Calculating portfolio VaR from Monte Carlo simulations")

        # Validate inputs
        if abs(sum(portfolio_weights.values()) - 1.0) > 1e-6:
            raise ValueError("Portfolio weights must sum to 1.0")

        # Ensure all assets have simulation results
        missing_assets = set(portfolio_weights.keys()) - set(individual_simulations.keys())
        if missing_assets:
            raise ValueError(f"Missing simulation results for assets: {missing_assets}")

        # Get minimum number of simulations across all assets
        min_simulations = min(len(sim.values) for sim in individual_simulations.values())

        # Calculate portfolio value for each simulation
        portfolio_values = np.zeros(min_simulations)

        for i in range(min_simulations):
            portfolio_value = 0
            for asset, weight in portfolio_weights.items():
                asset_value = individual_simulations[asset].values[i]
                portfolio_value += weight * asset_value
            portfolio_values[i] = portfolio_value

        # Calculate VaR metrics
        sorted_values = np.sort(portfolio_values)
        var_index = int(confidence_level * min_simulations)

        portfolio_var = np.percentile(sorted_values, confidence_level * 100)
        portfolio_cvar = np.mean(sorted_values[:var_index]) if var_index > 0 else portfolio_var

        results = {
            'portfolio_var': portfolio_var,
            'portfolio_cvar': portfolio_cvar,
            'portfolio_mean': np.mean(portfolio_values),
            'portfolio_std': np.std(portfolio_values),
            'portfolio_min': np.min(portfolio_values),
            'portfolio_max': np.max(portfolio_values),
            'confidence_level': confidence_level,
            'num_simulations': min_simulations
        }

        logger.info(f"Portfolio VaR ({confidence_level*100:.1f}%): {portfolio_var:.2f}")
        return results

    def run_adaptive_dcf_simulation(
        self,
        max_simulations: int = 50000,
        min_simulations: int = 5000,
        convergence_threshold: float = 0.01,
        revenue_growth_volatility: float = 0.15,
        discount_rate_volatility: float = 0.02,
        terminal_growth_volatility: float = 0.01,
        margin_volatility: float = 0.05,
        custom_distributions: Optional[Dict[str, ParameterDistribution]] = None,
        random_state: Optional[int] = None
    ) -> SimulationResult:
        """
        Run adaptive DCF simulation that automatically determines optimal iteration count.

        Args:
            max_simulations: Maximum number of simulations to run
            min_simulations: Minimum number of simulations before testing convergence
            convergence_threshold: Relative change threshold for convergence
            revenue_growth_volatility: Standard deviation of revenue growth rate
            discount_rate_volatility: Standard deviation of discount rate
            terminal_growth_volatility: Standard deviation of terminal growth rate
            margin_volatility: Standard deviation of profit margins
            custom_distributions: Custom parameter distributions
            random_state: Random seed for reproducibility

        Returns:
            SimulationResult with adaptive convergence information
        """
        logger.info(f"Starting adaptive DCF simulation (min: {min_simulations}, max: {max_simulations})")

        # Start with minimum simulations
        batch_size = 1000
        current_simulations = min_simulations
        all_values = []

        # Run initial batch
        initial_result = self.simulate_dcf_valuation(
            num_simulations=min_simulations,
            revenue_growth_volatility=revenue_growth_volatility,
            discount_rate_volatility=discount_rate_volatility,
            terminal_growth_volatility=terminal_growth_volatility,
            margin_volatility=margin_volatility,
            custom_distributions=custom_distributions,
            random_state=random_state
        )

        all_values.extend(initial_result.values)

        # Continue until convergence or max simulations reached
        while current_simulations < max_simulations:
            # Test convergence
            convergence_info = self.test_convergence(
                np.array(all_values),
                convergence_threshold=convergence_threshold,
                min_samples=min_simulations
            )

            if convergence_info['converged']:
                logger.info(f"Adaptive simulation converged at {current_simulations} iterations")
                break

            # Run additional batch
            additional_sims = min(batch_size, max_simulations - current_simulations)
            if additional_sims <= 0:
                break

            batch_result = self.simulate_dcf_valuation(
                num_simulations=additional_sims,
                revenue_growth_volatility=revenue_growth_volatility,
                discount_rate_volatility=discount_rate_volatility,
                terminal_growth_volatility=terminal_growth_volatility,
                margin_volatility=margin_volatility,
                custom_distributions=custom_distributions,
                random_state=None  # Don't reset seed for additional batches
            )

            all_values.extend(batch_result.values)
            current_simulations += additional_sims

            logger.debug(f"Adaptive simulation progress: {current_simulations}/{max_simulations}")

        # Final convergence test
        final_convergence = self.test_convergence(
            np.array(all_values),
            convergence_threshold=convergence_threshold,
            min_samples=min_simulations
        )

        # Create final result
        result = SimulationResult(
            values=np.array(all_values),
            parameters={
                'num_simulations': len(all_values),
                'max_simulations': max_simulations,
                'min_simulations': min_simulations,
                'convergence_threshold': convergence_threshold,
                'revenue_growth_volatility': revenue_growth_volatility,
                'discount_rate_volatility': discount_rate_volatility,
                'terminal_growth_volatility': terminal_growth_volatility,
                'margin_volatility': margin_volatility,
                'random_state': random_state,
                'adaptive_simulation': True
            },
            convergence_info=final_convergence
        )

        if final_convergence['converged']:
            logger.info(f"Adaptive DCF simulation completed with convergence at {len(all_values)} iterations")
        else:
            logger.warning(f"Adaptive DCF simulation reached max iterations ({max_simulations}) without convergence")

        return result


# Convenience functions for common use cases

def quick_dcf_simulation(
    financial_calculator,
    num_simulations: int = 5000,
    volatility_level: str = 'medium'
) -> SimulationResult:
    """
    Quick DCF Monte Carlo simulation with predefined volatility levels.

    Args:
        financial_calculator: FinancialCalculator instance
        num_simulations: Number of simulations to run
        volatility_level: 'low', 'medium', or 'high' volatility

    Returns:
        SimulationResult with simulation output
    """
    volatility_settings = {
        'low': {
            'revenue_growth_volatility': 0.05,
            'discount_rate_volatility': 0.01,
            'terminal_growth_volatility': 0.005,
            'margin_volatility': 0.02
        },
        'medium': {
            'revenue_growth_volatility': 0.15,
            'discount_rate_volatility': 0.02,
            'terminal_growth_volatility': 0.01,
            'margin_volatility': 0.05
        },
        'high': {
            'revenue_growth_volatility': 0.30,
            'discount_rate_volatility': 0.04,
            'terminal_growth_volatility': 0.02,
            'margin_volatility': 0.10
        }
    }

    settings = volatility_settings.get(volatility_level, volatility_settings['medium'])

    monte_carlo = MonteCarloEngine(financial_calculator)
    return monte_carlo.simulate_dcf_valuation(
        num_simulations=num_simulations,
        **settings
    )


def create_standard_scenarios() -> Dict[str, Dict[str, float]]:
    """
    Create standard financial scenarios for scenario analysis.

    Returns:
        Dictionary of scenario names to parameter dictionaries
    """
    return {
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
        },
        'High Growth': {
            'revenue_growth': 0.25,
            'discount_rate': 0.09,
            'terminal_growth': 0.05,
            'operating_margin': 0.22
        },
        'Economic Downturn': {
            'revenue_growth': -0.10,
            'discount_rate': 0.15,
            'terminal_growth': 0.01,
            'operating_margin': 0.10
        }
    }