"""
Value-at-Risk (VaR) and Conditional VaR Calculations
==================================================

This module implements comprehensive Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR)
calculations using multiple methodologies for financial risk assessment. It integrates with
the existing Monte Carlo simulation framework to provide robust risk quantification.

Key Features:
- **Parametric VaR**: Normal and t-distribution based calculations
- **Historical Simulation VaR**: Non-parametric approach using historical data
- **Monte Carlo VaR**: Integration with existing Monte Carlo simulation engine
- **Conditional VaR (Expected Shortfall)**: Expected loss beyond VaR threshold
- **Confidence Interval Estimation**: Bootstrap and analytical confidence intervals
- **Backtesting Framework**: Model validation and performance assessment

Classes:
--------
VaRMethodology
    Enumeration of supported VaR calculation methods

VaRResult
    Container for VaR calculation results and statistics

VaRCalculator
    Main class for comprehensive VaR calculations

VaRBacktester
    Framework for VaR model validation and backtesting

Usage Example:
--------------
>>> from core.analysis.risk.var_calculations import VaRCalculator, VaRMethodology
>>> import pandas as pd
>>> import numpy as np
>>>
>>> # Prepare returns data
>>> returns = pd.Series(np.random.normal(-0.001, 0.02, 1000))
>>>
>>> # Initialize VaR calculator
>>> var_calc = VaRCalculator()
>>>
>>> # Calculate VaR using multiple methods
>>> parametric_result = var_calc.calculate_parametric_var(returns, confidence_level=0.95)
>>> historical_result = var_calc.calculate_historical_var(returns, confidence_level=0.95)
>>> monte_carlo_result = var_calc.calculate_monte_carlo_var(returns, confidence_level=0.95)
>>>
>>> print(f"Parametric VaR (95%): {parametric_result.var_estimate:.4f}")
>>> print(f"Historical VaR (95%): {historical_result.var_estimate:.4f}")
>>> print(f"Monte Carlo VaR (95%): {monte_carlo_result.var_estimate:.4f}")

Financial Theory:
-----------------
Value-at-Risk (VaR) quantifies the maximum expected loss over a specific time horizon
at a given confidence level. It answers: "What is the worst expected loss over X days
with Y% confidence?"

1. **Parametric VaR**: Assumes returns follow a specific distribution (normal, t-distribution)
2. **Historical Simulation**: Uses actual historical returns without distributional assumptions
3. **Monte Carlo VaR**: Uses simulated scenarios to estimate risk
4. **Conditional VaR**: Average loss beyond the VaR threshold (tail risk measure)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings
from scipy import stats
from scipy.optimize import minimize_scalar
import logging

# Import existing Monte Carlo framework
from ..statistics.monte_carlo_engine import MonteCarloEngine, SimulationResult

logger = logging.getLogger(__name__)


class VaRMethodology(Enum):
    """Supported VaR calculation methodologies."""
    PARAMETRIC_NORMAL = "parametric_normal"
    PARAMETRIC_T_DIST = "parametric_t_distribution"
    HISTORICAL_SIMULATION = "historical_simulation"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"  # Higher moment expansion
    EXTREME_VALUE = "extreme_value"    # EVT-based approach


@dataclass
class VaRResult:
    """
    Container for VaR calculation results and associated statistics.

    Attributes:
        methodology: VaR calculation method used
        confidence_level: Confidence level for VaR calculation
        var_estimate: VaR estimate (positive value representing loss)
        cvar_estimate: Conditional VaR estimate (Expected Shortfall)
        var_confidence_interval: Confidence interval for VaR estimate
        cvar_confidence_interval: Confidence interval for CVaR estimate
        expected_return: Expected return used in calculation
        volatility: Volatility estimate used in calculation
        statistics: Additional statistical measures
        methodology_params: Parameters specific to the methodology
        calculation_metadata: Metadata about the calculation process
    """
    methodology: VaRMethodology
    confidence_level: float
    var_estimate: float
    cvar_estimate: float
    var_confidence_interval: Optional[Tuple[float, float]] = None
    cvar_confidence_interval: Optional[Tuple[float, float]] = None
    expected_return: Optional[float] = None
    volatility: Optional[float] = None
    statistics: Dict[str, float] = field(default_factory=dict)
    methodology_params: Dict[str, Any] = field(default_factory=dict)
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate additional derived metrics."""
        self._calculate_derived_metrics()

    def _calculate_derived_metrics(self):
        """Calculate derived risk metrics."""
        # VaR ratio (CVaR / VaR)
        if self.var_estimate != 0:
            self.statistics['cvar_var_ratio'] = self.cvar_estimate / abs(self.var_estimate)
        else:
            self.statistics['cvar_var_ratio'] = 1.0

        # Tail risk measure
        if self.expected_return is not None:
            self.statistics['tail_expectation'] = self.cvar_estimate - self.expected_return
            self.statistics['var_multiple'] = abs(self.var_estimate) / abs(self.expected_return) if self.expected_return != 0 else 0

        # Risk concentration (how much worse CVaR is than VaR)
        excess_tail_risk = self.cvar_estimate - abs(self.var_estimate)
        self.statistics['excess_tail_risk'] = excess_tail_risk

    def summary_table(self) -> pd.DataFrame:
        """Generate summary table of VaR results."""
        data = {
            'Metric': [
                'VaR Estimate',
                'CVaR Estimate',
                'Expected Return',
                'Volatility',
                'CVaR/VaR Ratio',
                'Tail Expectation',
                'Excess Tail Risk'
            ],
            'Value': [
                self.var_estimate,
                self.cvar_estimate,
                self.expected_return or 0,
                self.volatility or 0,
                self.statistics.get('cvar_var_ratio', 0),
                self.statistics.get('tail_expectation', 0),
                self.statistics.get('excess_tail_risk', 0)
            ],
            'Description': [
                f'Maximum expected loss at {self.confidence_level*100:.1f}% confidence',
                f'Expected loss beyond VaR threshold',
                'Expected portfolio return',
                'Portfolio volatility (annualized)',
                'Ratio of CVaR to VaR (tail risk concentration)',
                'Expected tail loss relative to expected return',
                'Additional risk beyond VaR threshold'
            ]
        }
        return pd.DataFrame(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'methodology': self.methodology.value,
            'confidence_level': self.confidence_level,
            'var_estimate': self.var_estimate,
            'cvar_estimate': self.cvar_estimate,
            'var_confidence_interval': self.var_confidence_interval,
            'cvar_confidence_interval': self.cvar_confidence_interval,
            'expected_return': self.expected_return,
            'volatility': self.volatility,
            'statistics': self.statistics,
            'methodology_params': self.methodology_params,
            'calculation_metadata': self.calculation_metadata
        }


class VaRCalculator:
    """
    Comprehensive Value-at-Risk calculator supporting multiple methodologies.

    This class implements various VaR calculation approaches and integrates with
    the existing Monte Carlo simulation framework for comprehensive risk assessment.
    """

    def __init__(self, monte_carlo_engine: Optional[MonteCarloEngine] = None):
        """
        Initialize VaR calculator.

        Args:
            monte_carlo_engine: MonteCarloEngine instance for Monte Carlo VaR calculations
        """
        self.monte_carlo_engine = monte_carlo_engine
        self.bootstrap_samples = 1000
        self.random_state: Optional[int] = None

        logger.info("VaR Calculator initialized")

    def calculate_parametric_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        distribution: str = 'normal',
        window_size: Optional[int] = None,
        bootstrap_ci: bool = True
    ) -> VaRResult:
        """
        Calculate parametric VaR assuming a specific distribution.

        Args:
            returns: Historical returns data
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95% VaR)
            distribution: 'normal' or 't_distribution'
            window_size: Rolling window size (None for full sample)
            bootstrap_ci: Whether to calculate bootstrap confidence intervals

        Returns:
            VaRResult with parametric VaR estimates
        """
        # Validate confidence level
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        logger.info(f"Calculating parametric VaR ({distribution}) at {confidence_level*100:.1f}% confidence")

        # Prepare data
        if window_size:
            returns_sample = returns.tail(window_size).dropna()
        else:
            returns_sample = returns.dropna()

        if len(returns_sample) < 30:
            raise ValueError("Insufficient data for parametric VaR calculation (minimum 30 observations)")

        # Calculate sample statistics
        mu = returns_sample.mean()
        sigma = returns_sample.std(ddof=1)

        # Determine methodology
        if distribution == 'normal':
            methodology = VaRMethodology.PARAMETRIC_NORMAL
            # Normal distribution VaR
            z_score = stats.norm.ppf(1 - confidence_level)
            var_estimate = -(mu + z_score * sigma)

            # CVaR for normal distribution (analytical formula)
            phi_z = stats.norm.pdf(z_score)
            cvar_estimate = -(mu - sigma * phi_z / (1 - confidence_level))

            params = {
                'distribution': 'normal',
                'mean': mu,
                'std': sigma,
                'z_score': z_score
            }

        elif distribution == 't_distribution':
            methodology = VaRMethodology.PARAMETRIC_T_DIST

            # Fit t-distribution
            try:
                # Estimate degrees of freedom using method of moments
                sample_kurtosis = stats.kurtosis(returns_sample, fisher=False)
                if sample_kurtosis > 3:
                    # Estimate df from excess kurtosis
                    df = 4 + 6 / (sample_kurtosis - 3) if sample_kurtosis > 3 else 30
                    df = max(4, min(df, 30))  # Reasonable bounds
                else:
                    df = 30  # Default to high df (close to normal)

                # Calculate VaR using t-distribution
                t_score = stats.t.ppf(1 - confidence_level, df)
                var_estimate = -(mu + t_score * sigma)

                # CVaR for t-distribution (simplified approximation)
                # Use a scaling factor based on t-distribution vs normal
                normal_z = stats.norm.ppf(1 - confidence_level)
                scaling_factor = t_score / normal_z if normal_z != 0 else 1.0

                # Approximate CVaR using normal formula with scaling
                phi_z = stats.norm.pdf(normal_z)
                cvar_estimate = -(mu - sigma * scaling_factor * phi_z / (1 - confidence_level))

                params = {
                    'distribution': 't_distribution',
                    'mean': mu,
                    'std': sigma,
                    'degrees_freedom': df,
                    't_score': t_score,
                    'sample_kurtosis': sample_kurtosis
                }

            except Exception as e:
                logger.warning(f"t-distribution fitting failed, falling back to normal: {e}")
                # Fall back to normal distribution
                return self.calculate_parametric_var(
                    returns, confidence_level, 'normal', window_size, bootstrap_ci
                )
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")

        # Calculate confidence intervals using bootstrap if requested
        var_ci = None
        cvar_ci = None

        if bootstrap_ci:
            try:
                var_ci, cvar_ci = self._bootstrap_parametric_ci(
                    returns_sample, confidence_level, distribution, mu, sigma
                )
            except Exception as e:
                logger.warning(f"Bootstrap confidence intervals failed: {e}")

        # Additional statistics
        statistics = {
            'sample_size': len(returns_sample),
            'sample_mean': mu,
            'sample_std': sigma,
            'sample_skewness': stats.skew(returns_sample),
            'sample_kurtosis': stats.kurtosis(returns_sample),
            'jarque_bera_stat': stats.jarque_bera(returns_sample)[0],
            'jarque_bera_pvalue': stats.jarque_bera(returns_sample)[1]
        }

        # Metadata
        metadata = {
            'calculation_date': pd.Timestamp.now(),
            'data_start_date': returns_sample.index[0] if hasattr(returns_sample.index, '__getitem__') else None,
            'data_end_date': returns_sample.index[-1] if hasattr(returns_sample.index, '__getitem__') else None,
            'window_size': window_size,
            'annualization_factor': 252
        }

        return VaRResult(
            methodology=methodology,
            confidence_level=confidence_level,
            var_estimate=var_estimate,
            cvar_estimate=cvar_estimate,
            var_confidence_interval=var_ci,
            cvar_confidence_interval=cvar_ci,
            expected_return=mu,
            volatility=sigma * np.sqrt(252),  # Annualized
            statistics=statistics,
            methodology_params=params,
            calculation_metadata=metadata
        )

    def calculate_historical_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        window_size: Optional[int] = None,
        bootstrap_ci: bool = True
    ) -> VaRResult:
        """
        Calculate VaR using historical simulation (non-parametric approach).

        Args:
            returns: Historical returns data
            confidence_level: Confidence level for VaR
            window_size: Rolling window size (None for full sample)
            bootstrap_ci: Whether to calculate bootstrap confidence intervals

        Returns:
            VaRResult with historical simulation VaR estimates
        """
        # Validate confidence level
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        logger.info(f"Calculating historical simulation VaR at {confidence_level*100:.1f}% confidence")

        # Prepare data
        if window_size:
            returns_sample = returns.tail(window_size).dropna()
        else:
            returns_sample = returns.dropna()

        if len(returns_sample) < 50:
            raise ValueError("Insufficient data for historical VaR calculation (minimum 50 observations)")

        # Sort returns for percentile calculation
        sorted_returns = returns_sample.sort_values()
        n = len(sorted_returns)

        # Calculate VaR as historical percentile
        var_percentile = (1 - confidence_level) * 100
        var_estimate = -np.percentile(sorted_returns, var_percentile)

        # Calculate CVaR as average of returns below VaR threshold
        var_threshold = -var_estimate
        tail_returns = sorted_returns[sorted_returns <= var_threshold]

        if len(tail_returns) > 0:
            cvar_estimate = -tail_returns.mean()
        else:
            # If no observations in tail, use the VaR estimate
            cvar_estimate = var_estimate

        # Calculate sample statistics
        mu = returns_sample.mean()
        sigma = returns_sample.std(ddof=1)

        # Bootstrap confidence intervals
        var_ci = None
        cvar_ci = None

        if bootstrap_ci:
            try:
                var_ci, cvar_ci = self._bootstrap_historical_ci(
                    returns_sample, confidence_level
                )
            except Exception as e:
                logger.warning(f"Bootstrap confidence intervals failed: {e}")

        # Additional statistics
        statistics = {
            'sample_size': len(returns_sample),
            'tail_observations': len(tail_returns),
            'tail_percentage': len(tail_returns) / n * 100,
            'sample_mean': mu,
            'sample_std': sigma,
            'sample_skewness': stats.skew(returns_sample),
            'sample_kurtosis': stats.kurtosis(returns_sample),
            'sample_min': returns_sample.min(),
            'sample_max': returns_sample.max()
        }

        # Methodology parameters
        params = {
            'method': 'historical_simulation',
            'percentile_used': var_percentile,
            'actual_var_rank': n - len(sorted_returns[sorted_returns <= var_threshold]),
            'interpolation_method': 'linear'
        }

        # Metadata
        metadata = {
            'calculation_date': pd.Timestamp.now(),
            'data_start_date': returns_sample.index[0] if hasattr(returns_sample.index, '__getitem__') else None,
            'data_end_date': returns_sample.index[-1] if hasattr(returns_sample.index, '__getitem__') else None,
            'window_size': window_size,
            'sort_method': 'ascending'
        }

        return VaRResult(
            methodology=VaRMethodology.HISTORICAL_SIMULATION,
            confidence_level=confidence_level,
            var_estimate=var_estimate,
            cvar_estimate=cvar_estimate,
            var_confidence_interval=var_ci,
            cvar_confidence_interval=cvar_ci,
            expected_return=mu,
            volatility=sigma * np.sqrt(252),  # Annualized
            statistics=statistics,
            methodology_params=params,
            calculation_metadata=metadata
        )

    def calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        distribution_fit: str = 'auto',
        random_state: Optional[int] = None
    ) -> VaRResult:
        """
        Calculate VaR using Monte Carlo simulation.

        Args:
            returns: Historical returns data for parameter estimation
            confidence_level: Confidence level for VaR
            num_simulations: Number of Monte Carlo simulations
            distribution_fit: Distribution to fit ('auto', 'normal', 't_distribution', 'skewed_t')
            random_state: Random seed for reproducibility

        Returns:
            VaRResult with Monte Carlo VaR estimates
        """
        # Validate inputs
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        if num_simulations < 100:
            raise ValueError("Number of simulations must be at least 100")

        logger.info(f"Calculating Monte Carlo VaR at {confidence_level*100:.1f}% confidence ({num_simulations} simulations)")

        if random_state:
            np.random.seed(random_state)
            self.random_state = random_state

        # Prepare data
        returns_sample = returns.dropna()
        if len(returns_sample) < 30:
            raise ValueError("Insufficient data for Monte Carlo VaR calculation (minimum 30 observations)")

        # Fit distribution to data
        if distribution_fit == 'auto':
            # Choose best fitting distribution
            distribution_fit = self._select_best_distribution(returns_sample)
            logger.info(f"Auto-selected distribution: {distribution_fit}")

        # Generate Monte Carlo simulations
        if distribution_fit == 'normal':
            mu = returns_sample.mean()
            sigma = returns_sample.std(ddof=1)
            simulated_returns = np.random.normal(mu, sigma, num_simulations)
            fit_params = {'mean': mu, 'std': sigma}

        elif distribution_fit == 't_distribution':
            # Fit t-distribution
            params = stats.t.fit(returns_sample)
            df, loc, scale = params
            simulated_returns = stats.t.rvs(df, loc, scale, size=num_simulations)
            fit_params = {'degrees_freedom': df, 'location': loc, 'scale': scale}

        elif distribution_fit == 'skewed_t':
            # Fit skewed t-distribution (if available)
            try:
                from scipy.stats import skewnorm
                params = skewnorm.fit(returns_sample)
                a, loc, scale = params
                simulated_returns = skewnorm.rvs(a, loc, scale, size=num_simulations)
                fit_params = {'skewness': a, 'location': loc, 'scale': scale}
            except ImportError:
                logger.warning("Skewed-t distribution not available, using normal distribution")
                return self.calculate_monte_carlo_var(
                    returns, confidence_level, num_simulations, 'normal', random_state
                )
        else:
            raise ValueError(f"Unsupported distribution: {distribution_fit}")

        # Calculate VaR and CVaR from simulated returns
        sorted_simulations = np.sort(simulated_returns)
        var_index = int((1 - confidence_level) * num_simulations)

        var_estimate = -sorted_simulations[var_index]

        # CVaR is average of worst (1-confidence_level) portion
        tail_simulations = sorted_simulations[:var_index]
        cvar_estimate = -np.mean(tail_simulations) if len(tail_simulations) > 0 else var_estimate

        # Calculate confidence intervals using simulation variability
        var_ci, cvar_ci = self._monte_carlo_confidence_intervals(
            simulated_returns, confidence_level
        )

        # Sample statistics
        mu = returns_sample.mean()
        sigma = returns_sample.std(ddof=1)

        # Additional statistics
        statistics = {
            'sample_size': len(returns_sample),
            'simulations_count': num_simulations,
            'tail_simulations': len(tail_simulations),
            'simulation_mean': np.mean(simulated_returns),
            'simulation_std': np.std(simulated_returns),
            'simulation_skewness': stats.skew(simulated_returns),
            'simulation_kurtosis': stats.kurtosis(simulated_returns),
            'convergence_metric': self._check_simulation_convergence(simulated_returns, var_estimate)
        }

        # Methodology parameters
        params = {
            'method': 'monte_carlo',
            'distribution': distribution_fit,
            'fit_parameters': fit_params,
            'num_simulations': num_simulations,
            'random_state': random_state
        }

        # Metadata
        metadata = {
            'calculation_date': pd.Timestamp.now(),
            'data_start_date': returns_sample.index[0] if hasattr(returns_sample.index, '__getitem__') else None,
            'data_end_date': returns_sample.index[-1] if hasattr(returns_sample.index, '__getitem__') else None,
            'simulation_time': None,  # Could be measured
            'convergence_achieved': statistics['convergence_metric'] < 0.01  # Threshold for convergence
        }

        return VaRResult(
            methodology=VaRMethodology.MONTE_CARLO,
            confidence_level=confidence_level,
            var_estimate=var_estimate,
            cvar_estimate=cvar_estimate,
            var_confidence_interval=var_ci,
            cvar_confidence_interval=cvar_ci,
            expected_return=mu,
            volatility=sigma * np.sqrt(252),  # Annualized
            statistics=statistics,
            methodology_params=params,
            calculation_metadata=metadata
        )

    def calculate_cornish_fisher_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        window_size: Optional[int] = None
    ) -> VaRResult:
        """
        Calculate VaR using Cornish-Fisher expansion (adjusts for skewness and kurtosis).

        Args:
            returns: Historical returns data
            confidence_level: Confidence level for VaR
            window_size: Rolling window size (None for full sample)

        Returns:
            VaRResult with Cornish-Fisher VaR estimates
        """
        logger.info(f"Calculating Cornish-Fisher VaR at {confidence_level*100:.1f}% confidence")

        # Prepare data
        if window_size:
            returns_sample = returns.tail(window_size).dropna()
        else:
            returns_sample = returns.dropna()

        if len(returns_sample) < 30:
            raise ValueError("Insufficient data for Cornish-Fisher VaR calculation")

        # Calculate sample moments
        mu = returns_sample.mean()
        sigma = returns_sample.std(ddof=1)
        skewness = stats.skew(returns_sample)
        kurtosis = stats.kurtosis(returns_sample, fisher=True)  # Excess kurtosis

        # Standard normal quantile
        z = stats.norm.ppf(1 - confidence_level)

        # Cornish-Fisher adjustment
        z_cf = (z +
                (z**2 - 1) * skewness / 6 +
                (z**3 - 3*z) * kurtosis / 24 -
                (2*z**3 - 5*z) * skewness**2 / 36)

        # Calculate VaR
        var_estimate = -(mu + z_cf * sigma)

        # CVaR approximation using modified normal distribution
        # This is an approximation - exact CVaR for Cornish-Fisher is complex
        phi_z_cf = stats.norm.pdf(z_cf)
        cvar_estimate = -(mu - sigma * phi_z_cf / (1 - confidence_level))

        # Additional statistics
        statistics = {
            'sample_size': len(returns_sample),
            'sample_mean': mu,
            'sample_std': sigma,
            'sample_skewness': skewness,
            'sample_kurtosis': kurtosis,
            'normal_z_score': z,
            'cornish_fisher_z_score': z_cf,
            'cf_adjustment': z_cf - z
        }

        # Methodology parameters
        params = {
            'method': 'cornish_fisher',
            'adjustment_terms': 'skewness_kurtosis',
            'normal_quantile': z,
            'adjusted_quantile': z_cf
        }

        # Metadata
        metadata = {
            'calculation_date': pd.Timestamp.now(),
            'window_size': window_size,
            'higher_moments_used': ['skewness', 'kurtosis']
        }

        return VaRResult(
            methodology=VaRMethodology.CORNISH_FISHER,
            confidence_level=confidence_level,
            var_estimate=var_estimate,
            cvar_estimate=cvar_estimate,
            expected_return=mu,
            volatility=sigma * np.sqrt(252),
            statistics=statistics,
            methodology_params=params,
            calculation_metadata=metadata
        )

    def _bootstrap_parametric_ci(
        self,
        returns: pd.Series,
        confidence_level: float,
        distribution: str,
        mu: float,
        sigma: float
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate bootstrap confidence intervals for parametric VaR."""
        var_estimates = []
        cvar_estimates = []

        n = len(returns)

        for _ in range(self.bootstrap_samples):
            # Bootstrap sample
            bootstrap_sample = returns.sample(n, replace=True)

            # Recalculate parameters
            boot_mu = bootstrap_sample.mean()
            boot_sigma = bootstrap_sample.std(ddof=1)

            if distribution == 'normal':
                z_score = stats.norm.ppf(1 - confidence_level)
                boot_var = -(boot_mu + z_score * boot_sigma)
                phi_z = stats.norm.pdf(z_score)
                boot_cvar = -(boot_mu - boot_sigma * phi_z / (1 - confidence_level))
            else:  # t_distribution
                # Simplified - use same df as original
                sample_kurtosis = stats.kurtosis(bootstrap_sample, fisher=False)
                df = max(4, min(4 + 6 / max(sample_kurtosis - 3, 0.1), 30))
                t_score = stats.t.ppf(1 - confidence_level, df)
                boot_var = -(boot_mu + t_score * boot_sigma)
                boot_cvar = boot_var * 1.2  # Approximation

            var_estimates.append(boot_var)
            cvar_estimates.append(boot_cvar)

        # Calculate confidence intervals (95% CI for the estimates)
        var_ci = (np.percentile(var_estimates, 2.5), np.percentile(var_estimates, 97.5))
        cvar_ci = (np.percentile(cvar_estimates, 2.5), np.percentile(cvar_estimates, 97.5))

        return var_ci, cvar_ci

    def _bootstrap_historical_ci(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate bootstrap confidence intervals for historical VaR."""
        var_estimates = []
        cvar_estimates = []

        n = len(returns)
        var_percentile = (1 - confidence_level) * 100

        for _ in range(self.bootstrap_samples):
            # Bootstrap sample
            bootstrap_sample = returns.sample(n, replace=True)

            # Calculate VaR and CVaR
            boot_var = -np.percentile(bootstrap_sample, var_percentile)
            var_threshold = -boot_var
            tail_returns = bootstrap_sample[bootstrap_sample <= var_threshold]
            boot_cvar = -tail_returns.mean() if len(tail_returns) > 0 else boot_var

            var_estimates.append(boot_var)
            cvar_estimates.append(boot_cvar)

        # Calculate confidence intervals
        var_ci = (np.percentile(var_estimates, 2.5), np.percentile(var_estimates, 97.5))
        cvar_ci = (np.percentile(cvar_estimates, 2.5), np.percentile(cvar_estimates, 97.5))

        return var_ci, cvar_ci

    def _monte_carlo_confidence_intervals(
        self,
        simulated_returns: np.ndarray,
        confidence_level: float,
        num_sub_samples: int = 100
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate confidence intervals from Monte Carlo simulation variability."""
        var_estimates = []
        cvar_estimates = []

        simulation_size = len(simulated_returns)
        sub_sample_size = simulation_size // num_sub_samples

        for i in range(num_sub_samples):
            start_idx = i * sub_sample_size
            end_idx = start_idx + sub_sample_size
            sub_sample = simulated_returns[start_idx:end_idx]

            sorted_sub = np.sort(sub_sample)
            var_index = int((1 - confidence_level) * len(sub_sample))

            sub_var = -sorted_sub[var_index]
            tail_sims = sorted_sub[:var_index]
            sub_cvar = -np.mean(tail_sims) if len(tail_sims) > 0 else sub_var

            var_estimates.append(sub_var)
            cvar_estimates.append(sub_cvar)

        # Calculate confidence intervals
        var_ci = (np.percentile(var_estimates, 2.5), np.percentile(var_estimates, 97.5))
        cvar_ci = (np.percentile(cvar_estimates, 2.5), np.percentile(cvar_estimates, 97.5))

        return var_ci, cvar_ci

    def _select_best_distribution(self, returns: pd.Series) -> str:
        """Select best fitting distribution using information criteria."""
        distributions = ['normal', 't_distribution']
        best_dist = 'normal'
        best_score = float('inf')

        for dist in distributions:
            try:
                if dist == 'normal':
                    params = stats.norm.fit(returns)
                    log_likelihood = np.sum(stats.norm.logpdf(returns, *params))
                    # AIC = -2 * log_likelihood + 2 * num_params
                    aic = -2 * log_likelihood + 2 * 2  # 2 parameters for normal

                elif dist == 't_distribution':
                    params = stats.t.fit(returns)
                    log_likelihood = np.sum(stats.t.logpdf(returns, *params))
                    aic = -2 * log_likelihood + 2 * 3  # 3 parameters for t-dist

                if aic < best_score:
                    best_score = aic
                    best_dist = dist

            except Exception:
                continue

        return best_dist

    def _check_simulation_convergence(
        self,
        simulated_returns: np.ndarray,
        final_var: float,
        check_points: List[int] = None
    ) -> float:
        """Check convergence of Monte Carlo simulation."""
        if check_points is None:
            check_points = [1000, 2000, 5000, len(simulated_returns)//2, len(simulated_returns)]

        var_evolution = []

        for n in check_points:
            if n <= len(simulated_returns):
                subset = simulated_returns[:n]
                sorted_subset = np.sort(subset)
                var_index = int(0.05 * n)  # 95% VaR
                var_at_n = -sorted_subset[var_index] if var_index < len(sorted_subset) else final_var
                var_evolution.append(var_at_n)

        if len(var_evolution) > 1:
            # Calculate relative change in final portion
            relative_changes = [abs(var_evolution[i] - var_evolution[i-1]) / abs(var_evolution[i-1])
                              for i in range(1, len(var_evolution)) if var_evolution[i-1] != 0]
            return np.mean(relative_changes) if relative_changes else 0.0

        return 0.0

    def compare_methodologies(
        self,
        returns: pd.Series,
        confidence_levels: List[float] = None,
        methodologies: List[VaRMethodology] = None
    ) -> pd.DataFrame:
        """
        Compare VaR estimates across different methodologies and confidence levels.

        Args:
            returns: Historical returns data
            confidence_levels: List of confidence levels to test
            methodologies: List of VaR methodologies to compare

        Returns:
            DataFrame with comparison results
        """
        if confidence_levels is None:
            confidence_levels = [0.90, 0.95, 0.99]

        if methodologies is None:
            methodologies = [
                VaRMethodology.PARAMETRIC_NORMAL,
                VaRMethodology.PARAMETRIC_T_DIST,
                VaRMethodology.HISTORICAL_SIMULATION,
                VaRMethodology.MONTE_CARLO,
                VaRMethodology.CORNISH_FISHER
            ]

        results = []

        for confidence_level in confidence_levels:
            for methodology in methodologies:
                try:
                    if methodology == VaRMethodology.PARAMETRIC_NORMAL:
                        result = self.calculate_parametric_var(returns, confidence_level, 'normal', bootstrap_ci=False)
                    elif methodology == VaRMethodology.PARAMETRIC_T_DIST:
                        result = self.calculate_parametric_var(returns, confidence_level, 't_distribution', bootstrap_ci=False)
                    elif methodology == VaRMethodology.HISTORICAL_SIMULATION:
                        result = self.calculate_historical_var(returns, confidence_level, bootstrap_ci=False)
                    elif methodology == VaRMethodology.MONTE_CARLO:
                        result = self.calculate_monte_carlo_var(returns, confidence_level, num_simulations=5000)
                    elif methodology == VaRMethodology.CORNISH_FISHER:
                        result = self.calculate_cornish_fisher_var(returns, confidence_level)
                    else:
                        continue

                    results.append({
                        'Methodology': methodology.value,
                        'Confidence_Level': f"{confidence_level*100:.0f}%",
                        'VaR_Estimate': result.var_estimate,
                        'CVaR_Estimate': result.cvar_estimate,
                        'CVaR_VaR_Ratio': result.statistics.get('cvar_var_ratio', np.nan)
                    })

                except Exception as e:
                    logger.warning(f"Failed to calculate {methodology.value} VaR at {confidence_level}: {e}")
                    continue

        comparison_df = pd.DataFrame(results)

        if not comparison_df.empty:
            # Pivot for easier comparison
            pivot_var = comparison_df.pivot(index='Methodology', columns='Confidence_Level', values='VaR_Estimate')
            pivot_cvar = comparison_df.pivot(index='Methodology', columns='Confidence_Level', values='CVaR_Estimate')

            # Add summary statistics
            pivot_var.loc['Mean'] = pivot_var.mean()
            pivot_var.loc['Std'] = pivot_var.std()

            logger.info("VaR methodology comparison completed")
            return pivot_var

        return pd.DataFrame()


class VaRBacktester:
    """
    Framework for VaR model validation and backtesting.

    Implements standard backtesting procedures to validate VaR model accuracy
    including violation rate tests, independence tests, and conditional coverage tests.
    """

    def __init__(self):
        """Initialize VaR backtester."""
        self.test_results = {}
        logger.info("VaR Backtester initialized")

    def backtest_var_model(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Perform comprehensive VaR model backtesting.

        Args:
            returns: Actual returns
            var_estimates: VaR estimates (positive values)
            confidence_level: VaR confidence level

        Returns:
            Dictionary with backtesting results
        """
        logger.info(f"Backtesting VaR model with {len(returns)} observations")

        # Align data
        aligned_data = pd.DataFrame({
            'returns': returns,
            'var_estimates': var_estimates
        }).dropna()

        if len(aligned_data) < 100:
            raise ValueError("Insufficient data for backtesting (minimum 100 observations)")

        actual_returns = aligned_data['returns']
        var_forecasts = aligned_data['var_estimates']

        # Calculate violations (where loss exceeds VaR)
        violations = (actual_returns < -var_forecasts).astype(int)

        # Basic statistics
        num_observations = len(violations)
        num_violations = violations.sum()
        violation_rate = num_violations / num_observations
        expected_violation_rate = 1 - confidence_level

        # 1. Unconditional Coverage Test (Kupiec Test)
        kupiec_result = self._kupiec_test(num_violations, num_observations, expected_violation_rate)

        # 2. Independence Test (Christoffersen)
        independence_result = self._independence_test(violations)

        # 3. Conditional Coverage Test (Combined)
        conditional_coverage_result = self._conditional_coverage_test(
            num_violations, num_observations, expected_violation_rate, violations
        )

        # 4. Additional diagnostics
        clustering_metric = self._calculate_violation_clustering(violations)
        magnitude_test = self._magnitude_test(actual_returns, var_forecasts, violations)

        results = {
            'basic_statistics': {
                'num_observations': num_observations,
                'num_violations': num_violations,
                'violation_rate': violation_rate,
                'expected_violation_rate': expected_violation_rate,
                'excess_violations': num_violations - (expected_violation_rate * num_observations)
            },
            'kupiec_test': kupiec_result,
            'independence_test': independence_result,
            'conditional_coverage_test': conditional_coverage_result,
            'violation_clustering': clustering_metric,
            'magnitude_test': magnitude_test,
            'overall_assessment': self._overall_model_assessment(
                kupiec_result, independence_result, conditional_coverage_result
            )
        }

        self.test_results[pd.Timestamp.now()] = results
        return results

    def _kupiec_test(
        self,
        violations: int,
        observations: int,
        expected_rate: float
    ) -> Dict[str, Any]:
        """Kupiec unconditional coverage test."""
        if violations == 0 or violations == observations:
            return {
                'statistic': np.nan,
                'p_value': np.nan,
                'critical_value': 3.841,  # 95% chi-square critical value
                'reject_null': False,
                'interpretation': 'Test inconclusive (boundary case)'
            }

        # Likelihood ratio test statistic
        observed_rate = violations / observations

        # Log-likelihood under null (expected rate)
        ll_null = (violations * np.log(expected_rate) +
                  (observations - violations) * np.log(1 - expected_rate))

        # Log-likelihood under alternative (observed rate)
        ll_alt = (violations * np.log(observed_rate) +
                 (observations - violations) * np.log(1 - observed_rate))

        lr_statistic = -2 * (ll_null - ll_alt)

        # Chi-square test with 1 degree of freedom
        p_value = 1 - stats.chi2.cdf(lr_statistic, df=1)
        critical_value = stats.chi2.ppf(0.95, df=1)  # 95% critical value

        reject_null = lr_statistic > critical_value

        return {
            'statistic': lr_statistic,
            'p_value': p_value,
            'critical_value': critical_value,
            'reject_null': reject_null,
            'interpretation': 'Reject model (incorrect coverage)' if reject_null else 'Accept model (correct coverage)'
        }

    def _independence_test(self, violations: pd.Series) -> Dict[str, Any]:
        """Test independence of violations (Christoffersen)."""
        # Create transition matrix
        v = violations.values
        n = len(v)

        if n < 2:
            return {'statistic': np.nan, 'p_value': np.nan, 'reject_null': False}

        # Count transitions
        n00 = np.sum((v[:-1] == 0) & (v[1:] == 0))  # No violation -> No violation
        n01 = np.sum((v[:-1] == 0) & (v[1:] == 1))  # No violation -> Violation
        n10 = np.sum((v[:-1] == 1) & (v[1:] == 0))  # Violation -> No violation
        n11 = np.sum((v[:-1] == 1) & (v[1:] == 1))  # Violation -> Violation

        if n01 + n11 == 0 or n10 + n11 == 0:
            return {
                'statistic': np.nan,
                'p_value': np.nan,
                'critical_value': 3.841,
                'reject_null': False,
                'interpretation': 'Test inconclusive (insufficient transitions)'
            }

        # Conditional probabilities
        pi_01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
        pi_11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
        pi = (n01 + n11) / (n - 1)  # Overall violation rate

        # Likelihood ratio test
        if pi_01 > 0 and pi_11 > 0 and pi > 0 and (1 - pi_01) > 0 and (1 - pi_11) > 0 and (1 - pi) > 0:
            ll_unrestricted = (n00 * np.log(1 - pi_01) + n01 * np.log(pi_01) +
                              n10 * np.log(1 - pi_11) + n11 * np.log(pi_11))
            ll_restricted = ((n00 + n10) * np.log(1 - pi) + (n01 + n11) * np.log(pi))

            lr_statistic = -2 * (ll_restricted - ll_unrestricted)
        else:
            lr_statistic = 0

        p_value = 1 - stats.chi2.cdf(lr_statistic, df=1)
        critical_value = stats.chi2.ppf(0.95, df=1)
        reject_null = lr_statistic > critical_value

        return {
            'statistic': lr_statistic,
            'p_value': p_value,
            'critical_value': critical_value,
            'reject_null': reject_null,
            'interpretation': 'Reject independence' if reject_null else 'Accept independence'
        }

    def _conditional_coverage_test(
        self,
        violations: int,
        observations: int,
        expected_rate: float,
        violation_series: pd.Series
    ) -> Dict[str, Any]:
        """Conditional coverage test (combination of Kupiec and independence)."""
        kupiec_result = self._kupiec_test(violations, observations, expected_rate)
        independence_result = self._independence_test(violation_series)

        # Combined test statistic
        lr_uc = kupiec_result['statistic'] if not np.isnan(kupiec_result['statistic']) else 0
        lr_ind = independence_result['statistic'] if not np.isnan(independence_result['statistic']) else 0

        lr_cc = lr_uc + lr_ind

        # Chi-square test with 2 degrees of freedom
        p_value = 1 - stats.chi2.cdf(lr_cc, df=2)
        critical_value = stats.chi2.ppf(0.95, df=2)
        reject_null = lr_cc > critical_value

        return {
            'statistic': lr_cc,
            'p_value': p_value,
            'critical_value': critical_value,
            'reject_null': reject_null,
            'interpretation': 'Reject model (poor conditional coverage)' if reject_null else 'Accept model (good conditional coverage)'
        }

    def _calculate_violation_clustering(self, violations: pd.Series) -> Dict[str, Any]:
        """Calculate metrics for violation clustering."""
        v = violations.values
        n = len(v)

        if n < 10:
            return {'clustering_metric': np.nan, 'max_cluster_size': 0}

        # Find violation clusters (consecutive violations)
        clusters = []
        current_cluster = 0

        for violation in v:
            if violation == 1:
                current_cluster += 1
            else:
                if current_cluster > 0:
                    clusters.append(current_cluster)
                current_cluster = 0

        if current_cluster > 0:
            clusters.append(current_cluster)

        max_cluster_size = max(clusters) if clusters else 0
        avg_cluster_size = np.mean(clusters) if clusters else 0
        num_clusters = len(clusters)

        # Clustering metric: ratio of largest cluster to expected
        expected_max_cluster = np.log(n) / np.log(2)  # Rough approximation
        clustering_metric = max_cluster_size / expected_max_cluster if expected_max_cluster > 0 else 0

        return {
            'clustering_metric': clustering_metric,
            'max_cluster_size': max_cluster_size,
            'avg_cluster_size': avg_cluster_size,
            'num_clusters': num_clusters,
            'interpretation': 'High clustering' if clustering_metric > 2 else 'Normal clustering'
        }

    def _magnitude_test(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        violations: pd.Series
    ) -> Dict[str, Any]:
        """Test magnitude of losses during violations."""
        violation_returns = returns[violations == 1]
        violation_vars = var_estimates[violations == 1]

        if len(violation_returns) == 0:
            return {
                'avg_excess_loss': 0,
                'max_excess_loss': 0,
                'interpretation': 'No violations to analyze'
            }

        # Calculate excess losses during violations
        excess_losses = -violation_returns - violation_vars

        avg_excess_loss = excess_losses.mean()
        max_excess_loss = excess_losses.max()
        std_excess_loss = excess_losses.std()

        # Simple test: are excess losses reasonable?
        # Large excess losses suggest the VaR model underestimates tail risk
        severity_score = avg_excess_loss / var_estimates.mean() if var_estimates.mean() != 0 else 0

        interpretation = 'Severe violations (large excess losses)' if severity_score > 0.5 else 'Moderate violations'

        return {
            'avg_excess_loss': avg_excess_loss,
            'max_excess_loss': max_excess_loss,
            'std_excess_loss': std_excess_loss,
            'severity_score': severity_score,
            'interpretation': interpretation
        }

    def _overall_model_assessment(
        self,
        kupiec_result: Dict,
        independence_result: Dict,
        conditional_coverage_result: Dict
    ) -> Dict[str, Any]:
        """Provide overall assessment of VaR model performance."""
        tests_passed = 0
        total_tests = 0

        # Check each test
        if not np.isnan(kupiec_result.get('statistic', np.nan)):
            total_tests += 1
            if not kupiec_result.get('reject_null', True):
                tests_passed += 1

        if not np.isnan(independence_result.get('statistic', np.nan)):
            total_tests += 1
            if not independence_result.get('reject_null', True):
                tests_passed += 1

        if not np.isnan(conditional_coverage_result.get('statistic', np.nan)):
            total_tests += 1
            if not conditional_coverage_result.get('reject_null', True):
                tests_passed += 1

        pass_rate = tests_passed / total_tests if total_tests > 0 else 0

        if pass_rate >= 0.67:
            overall_rating = 'Good'
            recommendation = 'Model performs well and can be used for risk management'
        elif pass_rate >= 0.33:
            overall_rating = 'Fair'
            recommendation = 'Model has some issues, consider improvements or alternative approaches'
        else:
            overall_rating = 'Poor'
            recommendation = 'Model fails multiple tests, recommend using alternative VaR methodology'

        return {
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'pass_rate': pass_rate,
            'overall_rating': overall_rating,
            'recommendation': recommendation
        }


# Integration function with existing Monte Carlo engine
def integrate_var_with_monte_carlo(
    monte_carlo_result: SimulationResult,
    confidence_levels: List[float] = None
) -> Dict[str, VaRResult]:
    """
    Convert Monte Carlo simulation results to VaR format.

    Args:
        monte_carlo_result: SimulationResult from MonteCarloEngine
        confidence_levels: List of confidence levels to calculate

    Returns:
        Dictionary mapping confidence levels to VaRResult objects
    """
    if confidence_levels is None:
        confidence_levels = [0.90, 0.95, 0.99]

    var_results = {}

    # Handle empty results
    if len(monte_carlo_result.values) == 0:
        for confidence_level in confidence_levels:
            var_result = VaRResult(
                methodology=VaRMethodology.MONTE_CARLO,
                confidence_level=confidence_level,
                var_estimate=0.0,
                cvar_estimate=0.0,
                expected_return=0.0,
                volatility=0.0,
                statistics={
                    'simulations_used': 0,
                    'integration_source': 'monte_carlo_engine',
                    'empty_result': True
                },
                methodology_params={
                    'original_parameters': monte_carlo_result.parameters,
                    'integration_method': 'direct_conversion'
                },
                calculation_metadata={
                    'integration_date': pd.Timestamp.now(),
                    'source_engine': 'MonteCarloEngine',
                    'warning': 'Empty simulation results'
                }
            )
            var_results[f"{confidence_level*100:.0f}%"] = var_result
        return var_results

    for confidence_level in confidence_levels:
        # Calculate VaR from simulation values
        sorted_values = np.sort(monte_carlo_result.values)
        var_index = int((1 - confidence_level) * len(sorted_values))

        var_estimate = -sorted_values[var_index] if var_index < len(sorted_values) else 0

        # CVaR calculation
        tail_values = sorted_values[:var_index]
        cvar_estimate = -np.mean(tail_values) if len(tail_values) > 0 else var_estimate

        # Create VaRResult
        var_result = VaRResult(
            methodology=VaRMethodology.MONTE_CARLO,
            confidence_level=confidence_level,
            var_estimate=var_estimate,
            cvar_estimate=cvar_estimate,
            expected_return=monte_carlo_result.statistics.get('mean', 0),
            volatility=monte_carlo_result.statistics.get('std', 0),
            statistics={
                'simulations_used': len(monte_carlo_result.values),
                'integration_source': 'monte_carlo_engine'
            },
            methodology_params={
                'original_parameters': monte_carlo_result.parameters,
                'integration_method': 'direct_conversion'
            },
            calculation_metadata={
                'integration_date': pd.Timestamp.now(),
                'source_engine': 'MonteCarloEngine'
            }
        )

        var_results[f"{confidence_level*100:.0f}%"] = var_result

    return var_results