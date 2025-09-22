"""
Probability Distribution Framework for Financial Risk Analysis
============================================================

This module provides comprehensive probability distribution modeling capabilities
for financial variables, supporting various distribution types commonly used in
risk analysis, Monte Carlo simulation, and stress testing.

Key Features:
- Support for multiple probability distributions (Normal, Log-Normal, Student's t, etc.)
- Parameter estimation from historical data
- Distribution fitting and goodness-of-fit testing
- Tail risk analysis and extreme value distributions
- Copula models for multivariate dependencies
- Custom distribution creation and transformation

Classes:
--------
DistributionType: Enum of supported distribution types
ProbabilityDistribution: Base class for probability distributions
FinancialDistribution: Specialized distributions for financial variables
DistributionFitter: Automated distribution fitting from data
CopulaModel: Multivariate dependency modeling

Usage Example:
--------------
>>> from core.analysis.risk.probability_distributions import DistributionFitter
>>> import pandas as pd
>>>
>>> # Load returns data
>>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
>>>
>>> # Fit distribution automatically
>>> fitter = DistributionFitter()
>>> best_dist = fitter.fit_best_distribution(returns)
>>> print(f"Best distribution: {best_dist.distribution_type}")
>>>
>>> # Generate samples
>>> samples = best_dist.sample(1000)
>>> var_95 = best_dist.var(0.05)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
from scipy import stats
from scipy.optimize import minimize
from scipy.special import gamma
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class DistributionType(Enum):
    """Supported probability distribution types for financial modeling."""
    NORMAL = "normal"
    LOG_NORMAL = "log_normal"
    STUDENT_T = "student_t"
    SKEWED_T = "skewed_t"
    GENERALIZED_ERROR = "ged"
    EXPONENTIAL = "exponential"
    GAMMA = "gamma"
    BETA = "beta"
    WEIBULL = "weibull"
    PARETO = "pareto"
    LAPLACE = "laplace"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    GUMBEL = "gumbel"
    LEVY = "levy"
    STABLE = "stable"


class TailBehavior(Enum):
    """Classification of distribution tail behavior."""
    LIGHT_TAIL = "light"      # Exponential decay (e.g., Normal)
    HEAVY_TAIL = "heavy"      # Power law decay (e.g., Student's t)
    FAT_TAIL = "fat"         # Heavier than normal (e.g., Laplace)
    EXTREME_TAIL = "extreme"  # Very heavy tails (e.g., Cauchy)


@dataclass
class DistributionParameters:
    """Container for distribution parameters with validation."""
    parameters: Dict[str, float]
    parameter_names: List[str] = field(default_factory=list)
    confidence_intervals: Optional[Dict[str, Tuple[float, float]]] = None
    standard_errors: Optional[Dict[str, float]] = None

    def __post_init__(self):
        """Validate parameters after initialization."""
        if not self.parameter_names:
            self.parameter_names = list(self.parameters.keys())

    def get_parameter(self, name: str, default: float = 0.0) -> float:
        """Get parameter value with default fallback."""
        return self.parameters.get(name, default)

    def update_parameter(self, name: str, value: float) -> None:
        """Update a parameter value."""
        self.parameters[name] = value
        if name not in self.parameter_names:
            self.parameter_names.append(name)


class ProbabilityDistribution(ABC):
    """
    Abstract base class for probability distributions.

    Provides common interface for all distribution types used in
    financial risk analysis and Monte Carlo simulation.
    """

    def __init__(
        self,
        distribution_type: DistributionType,
        parameters: DistributionParameters,
        name: Optional[str] = None
    ):
        """
        Initialize probability distribution.

        Args:
            distribution_type: Type of distribution
            parameters: Distribution parameters
            name: Optional name for the distribution
        """
        self.distribution_type = distribution_type
        self.parameters = parameters
        self.name = name or distribution_type.value
        self.fitted_data: Optional[pd.Series] = None
        self.goodness_of_fit: Optional[Dict[str, float]] = None

        logger.debug(f"Initialized {self.distribution_type.value} distribution")

    @abstractmethod
    def pdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Probability density function."""
        pass

    @abstractmethod
    def cdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Cumulative distribution function."""
        pass

    @abstractmethod
    def ppf(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Percent point function (inverse CDF)."""
        pass

    @abstractmethod
    def sample(self, size: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate random samples from distribution."""
        pass

    def mean(self) -> float:
        """Calculate distribution mean."""
        # Default implementation using numerical integration
        return self.moment(1)

    def variance(self) -> float:
        """Calculate distribution variance."""
        return self.moment(2) - self.moment(1) ** 2

    def std(self) -> float:
        """Calculate distribution standard deviation."""
        return np.sqrt(self.variance())

    def skewness(self) -> float:
        """Calculate distribution skewness."""
        mu = self.mean()
        sigma = self.std()
        if sigma == 0:
            return 0.0

        third_moment = self.moment(3)
        return (third_moment - 3 * mu * sigma**2 - mu**3) / (sigma**3)

    def kurtosis(self) -> float:
        """Calculate distribution kurtosis."""
        mu = self.mean()
        sigma = self.std()
        if sigma == 0:
            return 3.0

        fourth_moment = self.moment(4)
        return (fourth_moment - 4 * mu * self.moment(3) +
                6 * mu**2 * sigma**2 + 3 * mu**4) / (sigma**4)

    def moment(self, n: int) -> float:
        """Calculate nth moment of distribution."""
        # Numerical integration for general case
        from scipy.integrate import quad

        def integrand(x):
            return x**n * self.pdf(x)

        # Determine integration bounds
        if hasattr(self, '_support'):
            lower, upper = self._support()
        else:
            lower, upper = -10, 10  # Default bounds

        try:
            result, _ = quad(integrand, lower, upper)
            return result
        except:
            return np.nan

    def var(self, alpha: float) -> float:
        """
        Calculate Value at Risk at given confidence level.

        Args:
            alpha: Confidence level (e.g., 0.05 for 95% VaR)

        Returns:
            VaR value
        """
        return self.ppf(alpha)

    def cvar(self, alpha: float) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).

        Args:
            alpha: Confidence level

        Returns:
            CVaR value
        """
        var_value = self.var(alpha)

        # Numerical integration for CVaR
        from scipy.integrate import quad

        def integrand(x):
            return x * self.pdf(x)

        # Integrate from -inf to VaR
        if hasattr(self, '_support'):
            lower, _ = self._support()
        else:
            lower = -10

        try:
            integral, _ = quad(integrand, lower, var_value)
            return integral / alpha if alpha > 0 else var_value
        except:
            return var_value

    def tail_probability(self, threshold: float, tail: str = 'lower') -> float:
        """
        Calculate tail probability beyond threshold.

        Args:
            threshold: Threshold value
            tail: 'lower' or 'upper' tail

        Returns:
            Probability of exceeding threshold
        """
        if tail == 'lower':
            return self.cdf(threshold)
        else:
            return 1 - self.cdf(threshold)

    def quantile_range(self, lower_q: float, upper_q: float) -> Tuple[float, float]:
        """Get quantile range between two percentiles."""
        return self.ppf(lower_q), self.ppf(upper_q)

    def tail_behavior(self) -> TailBehavior:
        """Classify tail behavior of distribution."""
        # Default classification based on distribution type
        heavy_tail_distributions = {
            DistributionType.STUDENT_T, DistributionType.PARETO,
            DistributionType.STABLE, DistributionType.LEVY
        }

        fat_tail_distributions = {
            DistributionType.LAPLACE, DistributionType.SKEWED_T,
            DistributionType.GENERALIZED_ERROR
        }

        if self.distribution_type in heavy_tail_distributions:
            return TailBehavior.HEAVY_TAIL
        elif self.distribution_type in fat_tail_distributions:
            return TailBehavior.FAT_TAIL
        else:
            return TailBehavior.LIGHT_TAIL

    def to_dict(self) -> Dict[str, Any]:
        """Convert distribution to dictionary for serialization."""
        return {
            'distribution_type': self.distribution_type.value,
            'parameters': self.parameters.parameters,
            'name': self.name,
            'tail_behavior': self.tail_behavior().value,
            'moments': {
                'mean': self.mean(),
                'std': self.std(),
                'skewness': self.skewness(),
                'kurtosis': self.kurtosis()
            }
        }


class NormalDistribution(ProbabilityDistribution):
    """Normal (Gaussian) distribution implementation."""

    def __init__(self, mu: float = 0.0, sigma: float = 1.0, name: str = "Normal"):
        """
        Initialize Normal distribution.

        Args:
            mu: Mean parameter
            sigma: Standard deviation parameter
            name: Distribution name
        """
        parameters = DistributionParameters({
            'mu': mu,
            'sigma': sigma
        })
        super().__init__(DistributionType.NORMAL, parameters, name)

        self.mu = mu
        self.sigma = sigma
        self.dist = stats.norm(loc=mu, scale=sigma)

    def pdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Probability density function."""
        return self.dist.pdf(x)

    def cdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Cumulative distribution function."""
        return self.dist.cdf(x)

    def ppf(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Percent point function."""
        return self.dist.ppf(q)

    def sample(self, size: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate random samples."""
        return self.dist.rvs(size=size, random_state=random_state)

    def mean(self) -> float:
        """Distribution mean."""
        return self.mu

    def variance(self) -> float:
        """Distribution variance."""
        return self.sigma ** 2

    def skewness(self) -> float:
        """Distribution skewness (always 0 for normal)."""
        return 0.0

    def kurtosis(self) -> float:
        """Distribution kurtosis (always 3 for normal)."""
        return 3.0


class StudentTDistribution(ProbabilityDistribution):
    """Student's t-distribution implementation for heavy-tailed modeling."""

    def __init__(self, df: float, loc: float = 0.0, scale: float = 1.0, name: str = "Student-t"):
        """
        Initialize Student's t-distribution.

        Args:
            df: Degrees of freedom
            loc: Location parameter
            scale: Scale parameter
            name: Distribution name
        """
        parameters = DistributionParameters({
            'df': df,
            'loc': loc,
            'scale': scale
        })
        super().__init__(DistributionType.STUDENT_T, parameters, name)

        self.df = df
        self.loc = loc
        self.scale = scale
        self.dist = stats.t(df=df, loc=loc, scale=scale)

    def pdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Probability density function."""
        return self.dist.pdf(x)

    def cdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Cumulative distribution function."""
        return self.dist.cdf(x)

    def ppf(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Percent point function."""
        return self.dist.ppf(q)

    def sample(self, size: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate random samples."""
        return self.dist.rvs(size=size, random_state=random_state)

    def mean(self) -> float:
        """Distribution mean."""
        if self.df > 1:
            return self.loc
        else:
            return np.nan

    def variance(self) -> float:
        """Distribution variance."""
        if self.df > 2:
            return self.scale ** 2 * self.df / (self.df - 2)
        else:
            return np.inf if self.df > 1 else np.nan

    def skewness(self) -> float:
        """Distribution skewness."""
        if self.df > 3:
            return 0.0  # Symmetric distribution
        else:
            return np.nan

    def kurtosis(self) -> float:
        """Distribution kurtosis."""
        if self.df > 4:
            return 3 + 6 / (self.df - 4)
        else:
            return np.inf if self.df > 2 else np.nan


class LogNormalDistribution(ProbabilityDistribution):
    """Log-normal distribution for positive financial variables."""

    def __init__(self, mu: float = 0.0, sigma: float = 1.0, name: str = "Log-Normal"):
        """
        Initialize Log-normal distribution.

        Args:
            mu: Mean of underlying normal distribution
            sigma: Standard deviation of underlying normal distribution
            name: Distribution name
        """
        parameters = DistributionParameters({
            'mu': mu,
            'sigma': sigma
        })
        super().__init__(DistributionType.LOG_NORMAL, parameters, name)

        self.mu = mu
        self.sigma = sigma
        self.dist = stats.lognorm(s=sigma, scale=np.exp(mu))

    def pdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Probability density function."""
        return self.dist.pdf(x)

    def cdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Cumulative distribution function."""
        return self.dist.cdf(x)

    def ppf(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Percent point function."""
        return self.dist.ppf(q)

    def sample(self, size: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate random samples."""
        return self.dist.rvs(size=size, random_state=random_state)

    def mean(self) -> float:
        """Distribution mean."""
        return np.exp(self.mu + self.sigma ** 2 / 2)

    def variance(self) -> float:
        """Distribution variance."""
        exp_sigma2 = np.exp(self.sigma ** 2)
        return (exp_sigma2 - 1) * np.exp(2 * self.mu + self.sigma ** 2)


class DistributionFitter:
    """
    Automated distribution fitting and selection for financial data.

    Fits multiple distribution types to data and selects the best fit
    based on various goodness-of-fit criteria.
    """

    def __init__(self):
        """Initialize distribution fitter."""
        self.fitted_distributions: Dict[DistributionType, ProbabilityDistribution] = {}
        self.fit_statistics: Dict[DistributionType, Dict[str, float]] = {}

        # Available distributions for fitting
        self.available_distributions = {
            DistributionType.NORMAL: self._fit_normal,
            DistributionType.STUDENT_T: self._fit_student_t,
            DistributionType.LOG_NORMAL: self._fit_log_normal,
            DistributionType.LAPLACE: self._fit_laplace,
            DistributionType.GENERALIZED_ERROR: self._fit_ged
        }

    def fit_all_distributions(
        self,
        data: pd.Series,
        distributions: Optional[List[DistributionType]] = None
    ) -> Dict[DistributionType, ProbabilityDistribution]:
        """
        Fit all available distributions to data.

        Args:
            data: Time series data to fit
            distributions: Specific distributions to fit (all if None)

        Returns:
            Dictionary of fitted distributions
        """
        logger.info("Fitting multiple distributions to data")

        data_clean = data.dropna()
        if len(data_clean) < 30:
            logger.warning(f"Limited data for fitting: {len(data_clean)} observations")

        distributions_to_fit = distributions or list(self.available_distributions.keys())

        for dist_type in distributions_to_fit:
            if dist_type in self.available_distributions:
                try:
                    fitted_dist = self.available_distributions[dist_type](data_clean)
                    self.fitted_distributions[dist_type] = fitted_dist

                    # Calculate goodness of fit
                    self.fit_statistics[dist_type] = self._calculate_goodness_of_fit(
                        data_clean, fitted_dist
                    )

                    logger.debug(f"Successfully fitted {dist_type.value} distribution")

                except Exception as e:
                    logger.warning(f"Failed to fit {dist_type.value}: {e}")
                    continue

        return self.fitted_distributions

    def fit_best_distribution(
        self,
        data: pd.Series,
        criterion: str = 'aic',
        distributions: Optional[List[DistributionType]] = None
    ) -> ProbabilityDistribution:
        """
        Fit and select the best distribution based on specified criterion.

        Args:
            data: Time series data to fit
            criterion: Selection criterion ('aic', 'bic', 'ks', 'ad')
            distributions: Specific distributions to consider

        Returns:
            Best fitting distribution
        """
        logger.info(f"Finding best distribution using {criterion} criterion")

        # Fit all distributions
        fitted_dists = self.fit_all_distributions(data, distributions)

        if not fitted_dists:
            logger.warning("No distributions successfully fitted, using Normal distribution")
            return self._fit_normal(data)

        # Select best based on criterion
        best_dist_type = None
        best_score = np.inf if criterion in ['aic', 'bic'] else 0

        for dist_type, stats_dict in self.fit_statistics.items():
            if criterion not in stats_dict:
                continue

            score = stats_dict[criterion]

            if criterion in ['aic', 'bic']:
                # Lower is better
                if score < best_score:
                    best_score = score
                    best_dist_type = dist_type
            else:
                # Higher is better (p-values)
                if score > best_score:
                    best_score = score
                    best_dist_type = dist_type

        if best_dist_type is None:
            logger.warning("Could not determine best distribution, using Normal")
            return self._fit_normal(data)

        logger.info(f"Best distribution: {best_dist_type.value} ({criterion}={best_score:.4f})")
        return self.fitted_distributions[best_dist_type]

    def _fit_normal(self, data: pd.Series) -> NormalDistribution:
        """Fit normal distribution."""
        mu, sigma = stats.norm.fit(data)
        return NormalDistribution(mu=mu, sigma=sigma)

    def _fit_student_t(self, data: pd.Series) -> StudentTDistribution:
        """Fit Student's t-distribution."""
        df, loc, scale = stats.t.fit(data)
        return StudentTDistribution(df=df, loc=loc, scale=scale)

    def _fit_log_normal(self, data: pd.Series) -> LogNormalDistribution:
        """Fit log-normal distribution (for positive data only)."""
        if (data <= 0).any():
            # Shift data to positive values
            data_shifted = data - data.min() + 1e-6
            shape, loc, scale = stats.lognorm.fit(data_shifted, floc=0)
            mu = np.log(scale)
            sigma = shape
        else:
            shape, loc, scale = stats.lognorm.fit(data, floc=0)
            mu = np.log(scale)
            sigma = shape

        return LogNormalDistribution(mu=mu, sigma=sigma)

    def _fit_laplace(self, data: pd.Series) -> ProbabilityDistribution:
        """Fit Laplace distribution."""
        loc, scale = stats.laplace.fit(data)

        parameters = DistributionParameters({
            'loc': loc,
            'scale': scale
        })

        # Create generic distribution wrapper
        class LaplaceDistribution(ProbabilityDistribution):
            def __init__(self, loc, scale):
                super().__init__(DistributionType.LAPLACE, parameters, "Laplace")
                self.dist = stats.laplace(loc=loc, scale=scale)

            def pdf(self, x): return self.dist.pdf(x)
            def cdf(self, x): return self.dist.cdf(x)
            def ppf(self, q): return self.dist.ppf(q)
            def sample(self, size, random_state=None): return self.dist.rvs(size=size, random_state=random_state)

        return LaplaceDistribution(loc, scale)

    def _fit_ged(self, data: pd.Series) -> ProbabilityDistribution:
        """Fit Generalized Error Distribution (placeholder)."""
        # Simplified GED fitting using normal as approximation
        mu, sigma = stats.norm.fit(data)

        parameters = DistributionParameters({
            'mu': mu,
            'sigma': sigma,
            'nu': 2.0  # Shape parameter (2 = normal)
        })

        # Create generic distribution wrapper
        class GEDDistribution(ProbabilityDistribution):
            def __init__(self, mu, sigma, nu=2.0):
                super().__init__(DistributionType.GENERALIZED_ERROR, parameters, "GED")
                # Use normal approximation for now
                self.dist = stats.norm(loc=mu, scale=sigma)

            def pdf(self, x): return self.dist.pdf(x)
            def cdf(self, x): return self.dist.cdf(x)
            def ppf(self, q): return self.dist.ppf(q)
            def sample(self, size, random_state=None): return self.dist.rvs(size=size, random_state=random_state)

        return GEDDistribution(mu, sigma)

    def _calculate_goodness_of_fit(
        self,
        data: pd.Series,
        distribution: ProbabilityDistribution
    ) -> Dict[str, float]:
        """Calculate various goodness-of-fit statistics."""
        try:
            # Generate theoretical quantiles
            sorted_data = np.sort(data.values)
            n = len(sorted_data)

            # Theoretical probabilities
            theoretical_probs = (np.arange(1, n + 1) - 0.5) / n
            theoretical_quantiles = distribution.ppf(theoretical_probs)

            # Kolmogorov-Smirnov test
            ks_stat = np.max(np.abs(distribution.cdf(sorted_data) - theoretical_probs))
            ks_pvalue = stats.ksone.sf(ks_stat, n)

            # Calculate log-likelihood
            log_likelihood = np.sum(np.log(distribution.pdf(data.values) + 1e-10))

            # AIC and BIC
            k = len(distribution.parameters.parameters)  # Number of parameters
            aic = 2 * k - 2 * log_likelihood
            bic = k * np.log(n) - 2 * log_likelihood

            # Anderson-Darling test (simplified)
            ad_stat = -n - np.mean(
                (2 * np.arange(1, n + 1) - 1) *
                (np.log(distribution.cdf(sorted_data)) + np.log(1 - distribution.cdf(sorted_data[::-1])))
            )

            return {
                'aic': aic,
                'bic': bic,
                'log_likelihood': log_likelihood,
                'ks_statistic': ks_stat,
                'ks_pvalue': ks_pvalue,
                'ad_statistic': ad_stat
            }

        except Exception as e:
            logger.warning(f"Error calculating goodness-of-fit: {e}")
            return {'aic': np.inf, 'bic': np.inf, 'log_likelihood': -np.inf}

    def get_distribution_comparison(self) -> pd.DataFrame:
        """Get comparison table of fitted distributions."""
        comparison_data = []

        for dist_type, stats_dict in self.fit_statistics.items():
            dist_data = {
                'distribution': dist_type.value,
                'aic': stats_dict.get('aic', np.inf),
                'bic': stats_dict.get('bic', np.inf),
                'log_likelihood': stats_dict.get('log_likelihood', -np.inf),
                'ks_statistic': stats_dict.get('ks_statistic', np.nan),
                'ks_pvalue': stats_dict.get('ks_pvalue', np.nan)
            }

            # Add distribution moments
            if dist_type in self.fitted_distributions:
                dist = self.fitted_distributions[dist_type]
                dist_data.update({
                    'mean': dist.mean(),
                    'std': dist.std(),
                    'skewness': dist.skewness(),
                    'kurtosis': dist.kurtosis()
                })

            comparison_data.append(dist_data)

        return pd.DataFrame(comparison_data).sort_values('aic')


@dataclass
class CopulaModel:
    """
    Copula model for multivariate dependency modeling.

    Provides dependency modeling between financial variables that goes
    beyond linear correlation, capturing tail dependencies and non-linear relationships.
    """
    copula_type: str = "gaussian"  # "gaussian", "t", "clayton", "gumbel", "frank"
    marginal_distributions: Dict[str, ProbabilityDistribution] = field(default_factory=dict)
    dependency_parameters: Dict[str, float] = field(default_factory=dict)

    def fit(self, data: pd.DataFrame) -> None:
        """Fit copula model to multivariate data."""
        logger.info(f"Fitting {self.copula_type} copula to {data.shape[1]} variables")

        # Fit marginal distributions
        fitter = DistributionFitter()
        for column in data.columns:
            best_dist = fitter.fit_best_distribution(data[column])
            self.marginal_distributions[column] = best_dist

        # Transform to uniform margins (pseudo-observations)
        uniform_data = pd.DataFrame(index=data.index)
        for column in data.columns:
            uniform_data[column] = self.marginal_distributions[column].cdf(data[column])

        # Fit copula parameters (simplified implementation)
        if self.copula_type == "gaussian":
            # Gaussian copula uses correlation matrix
            from scipy.stats import norm
            gaussian_data = norm.ppf(uniform_data.clip(1e-6, 1-1e-6))
            correlation_matrix = gaussian_data.corr().values
            self.dependency_parameters['correlation_matrix'] = correlation_matrix

        logger.info("Copula fitting completed")

    def sample(self, n_samples: int, random_state: Optional[int] = None) -> pd.DataFrame:
        """Generate samples from fitted copula model."""
        if random_state:
            np.random.seed(random_state)

        variable_names = list(self.marginal_distributions.keys())

        if self.copula_type == "gaussian":
            # Generate correlated uniform samples via Gaussian copula
            correlation_matrix = self.dependency_parameters.get('correlation_matrix')
            if correlation_matrix is None:
                correlation_matrix = np.eye(len(variable_names))

            # Generate multivariate normal samples
            gaussian_samples = np.random.multivariate_normal(
                mean=np.zeros(len(variable_names)),
                cov=correlation_matrix,
                size=n_samples
            )

            # Transform to uniform
            from scipy.stats import norm
            uniform_samples = norm.cdf(gaussian_samples)

            # Transform to original marginals
            samples = pd.DataFrame(columns=variable_names)
            for i, var_name in enumerate(variable_names):
                marginal_dist = self.marginal_distributions[var_name]
                samples[var_name] = marginal_dist.ppf(uniform_samples[:, i])

            return samples

        else:
            # Fallback to independent sampling
            samples = pd.DataFrame(index=range(n_samples), columns=variable_names)
            for var_name in variable_names:
                samples[var_name] = self.marginal_distributions[var_name].sample(n_samples, random_state)
            return samples

    def tail_dependence(self) -> Dict[str, float]:
        """Calculate tail dependence coefficients."""
        # Simplified calculation for Gaussian copula
        if self.copula_type == "gaussian":
            # Gaussian copula has zero tail dependence
            return {'lower_tail': 0.0, 'upper_tail': 0.0}
        else:
            return {'lower_tail': np.nan, 'upper_tail': np.nan}