"""
Correlation Analysis and Risk Factor Identification
==================================================

This module provides advanced correlation analysis and risk factor identification
capabilities for financial risk assessment. It integrates with the Monte Carlo
engine and portfolio framework to provide comprehensive correlation-based risk analysis.

Key Features:
- Dynamic correlation calculation with multiple methods
- Risk factor identification using statistical techniques
- Correlation regime detection and analysis
- Multi-asset correlation matrix construction
- Factor-based risk decomposition
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class CorrelationMethod(Enum):
    """Methods for calculating correlations."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    ROLLING = "rolling"
    EXPONENTIAL = "exponential"
    ROBUST = "robust"


class RiskFactorType(Enum):
    """Types of risk factors."""
    MARKET = "market"           # Broad market movements
    SECTOR = "sector"           # Industry/sector specific
    SIZE = "size"              # Market cap effects
    VALUE = "value"            # Value vs growth
    MOMENTUM = "momentum"       # Price momentum
    VOLATILITY = "volatility"   # Volatility regime
    INTEREST_RATE = "interest_rate"  # Interest rate sensitivity
    CURRENCY = "currency"       # Currency exposure
    COMMODITY = "commodity"     # Commodity exposure
    CREDIT = "credit"          # Credit risk
    LIQUIDITY = "liquidity"    # Liquidity risk


@dataclass
class CorrelationMatrix:
    """
    Advanced correlation matrix with statistical analysis.

    Provides correlation calculations, statistical significance testing,
    and correlation stability analysis for risk assessment.
    """
    assets: List[str]
    correlation_matrix: np.ndarray
    method: CorrelationMethod
    calculation_date: pd.Timestamp = field(default_factory=pd.Timestamp.now)

    # Statistical properties
    p_values: Optional[np.ndarray] = None
    confidence_intervals: Optional[Dict[str, Tuple[float, float]]] = None

    # Correlation stability metrics
    stability_score: Optional[float] = None
    regime_indicators: Optional[Dict[str, Any]] = None

    # Clustering analysis
    asset_clusters: Optional[Dict[str, int]] = None
    cluster_labels: Optional[List[int]] = None

    def __post_init__(self):
        """Validate and enhance correlation matrix after initialization."""
        self._validate_matrix()
        self._calculate_stability_metrics()

    def _validate_matrix(self):
        """Validate correlation matrix properties."""
        if self.correlation_matrix.shape[0] != len(self.assets):
            raise ValueError("Matrix size must match number of assets")

        if not np.allclose(self.correlation_matrix, self.correlation_matrix.T):
            logger.warning("Correlation matrix is not symmetric, correcting...")
            self.correlation_matrix = (self.correlation_matrix + self.correlation_matrix.T) / 2

        # Check diagonal elements
        diag_elements = np.diag(self.correlation_matrix)
        if not np.allclose(diag_elements, 1.0, atol=1e-6):
            logger.warning("Diagonal elements are not 1.0, normalizing...")
            np.fill_diagonal(self.correlation_matrix, 1.0)

        # Check eigenvalues for positive semi-definiteness
        eigenvalues = np.linalg.eigvals(self.correlation_matrix)
        if np.any(eigenvalues < -1e-8):
            logger.warning("Correlation matrix is not positive semi-definite")

    def _calculate_stability_metrics(self):
        """Calculate correlation stability metrics."""
        # Average absolute correlation
        off_diag = self.correlation_matrix[np.triu_indices_from(self.correlation_matrix, k=1)]
        avg_correlation = np.mean(np.abs(off_diag))

        # Correlation dispersion
        correlation_std = np.std(off_diag)

        # Stability score (lower variance = higher stability)
        self.stability_score = 1.0 / (1.0 + correlation_std) if correlation_std > 0 else 1.0

    def hierarchical_clustering(self, n_clusters: int = None, method: str = 'ward') -> Dict[str, int]:
        """
        Perform hierarchical clustering on correlation matrix.

        Args:
            n_clusters: Number of clusters (auto-determined if None)
            method: Linkage method for clustering

        Returns:
            Dictionary mapping asset names to cluster labels
        """
        # Convert correlation to distance
        distance_matrix = np.sqrt(2 * (1 - np.abs(self.correlation_matrix)))

        # Perform hierarchical clustering
        linkage_matrix = linkage(distance_matrix, method=method)

        # Determine number of clusters if not specified
        if n_clusters is None:
            # Use elbow method or dendrogram analysis
            n_clusters = min(max(2, len(self.assets) // 3), 8)

        # Get cluster labels
        self.cluster_labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')

        # Create asset-to-cluster mapping
        self.asset_clusters = {
            asset: int(cluster_id)
            for asset, cluster_id in zip(self.assets, self.cluster_labels)
        }

        return self.asset_clusters

    def identify_highly_correlated_pairs(self, threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """Identify asset pairs with high correlation."""
        high_corr_pairs = []
        n = len(self.assets)

        for i in range(n):
            for j in range(i + 1, n):
                corr_value = self.correlation_matrix[i, j]
                if abs(corr_value) >= threshold:
                    high_corr_pairs.append((self.assets[i], self.assets[j], corr_value))

        return sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True)

    def market_concentration(self) -> float:
        """Calculate how concentrated correlations are (average correlation)."""
        off_diag = self.correlation_matrix[np.triu_indices_from(self.correlation_matrix, k=1)]
        return np.mean(off_diag)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert correlation matrix to DataFrame."""
        return pd.DataFrame(
            self.correlation_matrix,
            index=self.assets,
            columns=self.assets
        )


@dataclass
class RiskFactorIdentifier:
    """
    Advanced risk factor identification using statistical techniques.

    Identifies and analyzes risk factors that drive asset returns and correlations
    using methods like PCA, factor analysis, and regime detection.
    """
    returns_data: pd.DataFrame
    factor_method: str = 'pca'  # 'pca', 'factor_analysis', 'custom'

    # Factor analysis results
    factors: Optional[pd.DataFrame] = None
    factor_loadings: Optional[pd.DataFrame] = None
    explained_variance: Optional[pd.Series] = None

    # Risk factor classification
    identified_factors: Dict[RiskFactorType, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize factor analysis."""
        if self.returns_data is not None:
            self.identify_factors()

    def identify_factors(self, n_factors: Optional[int] = None) -> Dict[RiskFactorType, Dict[str, Any]]:
        """
        Identify risk factors using statistical decomposition.

        Args:
            n_factors: Number of factors to extract (auto-determined if None)

        Returns:
            Dictionary of identified risk factors with their properties
        """
        logger.info(f"Identifying risk factors using {self.factor_method} method")

        if self.returns_data.empty:
            return {}

        # Standardize returns data
        scaler = StandardScaler()
        standardized_returns = scaler.fit_transform(self.returns_data.fillna(0))

        # Determine number of factors
        if n_factors is None:
            n_factors = self._determine_optimal_factors(standardized_returns)

        # Apply factor analysis method
        if self.factor_method == 'pca':
            self._apply_pca(standardized_returns, n_factors)
        elif self.factor_method == 'factor_analysis':
            self._apply_factor_analysis(standardized_returns, n_factors)

        # Classify factors by type
        self._classify_risk_factors()

        return self.identified_factors

    def _determine_optimal_factors(self, data: np.ndarray) -> int:
        """Determine optimal number of factors using various criteria."""
        # Apply PCA to get eigenvalues
        pca = PCA()
        pca.fit(data)
        eigenvalues = pca.explained_variance_

        # Kaiser criterion (eigenvalues > 1)
        kaiser_factors = np.sum(eigenvalues > 1)

        # Scree plot criterion (elbow method)
        variance_ratios = pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(variance_ratios)

        # Find elbow point
        elbow_point = 1
        for i in range(1, len(variance_ratios) - 1):
            if (variance_ratios[i-1] - variance_ratios[i]) > (variance_ratios[i] - variance_ratios[i+1]):
                elbow_point = i
                break

        # 80% variance criterion
        variance_80_factors = np.argmax(cumulative_variance >= 0.80) + 1

        # Use conservative estimate
        optimal_factors = min(kaiser_factors, elbow_point + 1, variance_80_factors)
        optimal_factors = max(2, min(optimal_factors, data.shape[1] // 2))

        logger.info(f"Optimal factors: Kaiser={kaiser_factors}, Elbow={elbow_point}, "
                   f"80%Var={variance_80_factors}, Selected={optimal_factors}")

        return optimal_factors

    def _apply_pca(self, data: np.ndarray, n_factors: int):
        """Apply Principal Component Analysis."""
        pca = PCA(n_components=n_factors)
        self.factors = pd.DataFrame(
            pca.fit_transform(data),
            index=self.returns_data.index,
            columns=[f'PC{i+1}' for i in range(n_factors)]
        )

        self.factor_loadings = pd.DataFrame(
            pca.components_.T,
            index=self.returns_data.columns,
            columns=[f'PC{i+1}' for i in range(n_factors)]
        )

        self.explained_variance = pd.Series(
            pca.explained_variance_ratio_,
            index=[f'PC{i+1}' for i in range(n_factors)]
        )

    def _apply_factor_analysis(self, data: np.ndarray, n_factors: int):
        """Apply Factor Analysis."""
        try:
            fa = FactorAnalysis(n_components=n_factors, random_state=42)
            self.factors = pd.DataFrame(
                fa.fit_transform(data),
                index=self.returns_data.index,
                columns=[f'Factor{i+1}' for i in range(n_factors)]
            )

            self.factor_loadings = pd.DataFrame(
                fa.components_.T,
                index=self.returns_data.columns,
                columns=[f'Factor{i+1}' for i in range(n_factors)]
            )

            # Calculate explained variance for factor analysis
            total_variance = np.var(data, axis=0).sum()
            factor_variances = np.var(self.factors.values, axis=0)
            self.explained_variance = pd.Series(
                factor_variances / total_variance,
                index=[f'Factor{i+1}' for i in range(n_factors)]
            )

        except Exception as e:
            logger.warning(f"Factor analysis failed: {e}, falling back to PCA")
            self._apply_pca(data, n_factors)

    def _classify_risk_factors(self):
        """Classify identified factors by risk type."""
        if self.factor_loadings is None:
            return

        for factor_name in self.factor_loadings.columns:
            loadings = self.factor_loadings[factor_name].abs()

            # Identify assets with highest loadings
            top_assets = loadings.nlargest(5)

            # Classify based on loading patterns and asset characteristics
            factor_type = self._infer_factor_type(factor_name, top_assets, loadings)

            self.identified_factors[factor_type] = {
                'factor_name': factor_name,
                'explained_variance': self.explained_variance[factor_name] if self.explained_variance is not None else 0,
                'top_assets': top_assets.to_dict(),
                'loading_concentration': loadings.std(),
                'factor_strength': loadings.max()
            }

    def _infer_factor_type(self, factor_name: str, top_assets: pd.Series, all_loadings: pd.Series) -> RiskFactorType:
        """
        Infer factor type based on loading patterns and asset characteristics.

        This is a simplified classification - in practice would use sector data,
        market cap information, and other asset characteristics.
        """
        # Default classification logic - would be enhanced with real asset metadata
        loading_concentration = all_loadings.std()
        max_loading = all_loadings.max()

        if loading_concentration < 0.1:
            return RiskFactorType.MARKET  # Broad market factor
        elif max_loading > 0.8:
            return RiskFactorType.SECTOR  # Concentrated sector factor
        elif 'PC1' in factor_name or 'Factor1' in factor_name:
            return RiskFactorType.MARKET  # First factor usually market
        else:
            # Assign other types based on factor order and characteristics
            factor_types = [RiskFactorType.SIZE, RiskFactorType.VALUE,
                           RiskFactorType.MOMENTUM, RiskFactorType.VOLATILITY]
            factor_idx = int(factor_name[-1]) - 1 if factor_name[-1].isdigit() else 0
            return factor_types[factor_idx % len(factor_types)]


class CorrelationAnalyzer:
    """
    Comprehensive correlation analysis for financial risk assessment.

    Provides advanced correlation calculation, analysis, and risk factor
    identification capabilities for portfolio and individual asset analysis.
    """

    def __init__(self, returns_data: Optional[pd.DataFrame] = None):
        """
        Initialize correlation analyzer.

        Args:
            returns_data: DataFrame with asset returns data (optional)
        """
        self.returns_data = returns_data
        self.correlation_matrices: Dict[str, CorrelationMatrix] = {}
        self.risk_factors: Optional[RiskFactorIdentifier] = None

        logger.info("Correlation Analyzer initialized")

    def calculate_correlation_matrix(
        self,
        method: CorrelationMethod = CorrelationMethod.PEARSON,
        window: Optional[int] = None,
        min_periods: int = 30
    ) -> CorrelationMatrix:
        """
        Calculate correlation matrix using specified method.

        Args:
            method: Correlation calculation method
            window: Rolling window size (for rolling correlations)
            min_periods: Minimum observations required

        Returns:
            CorrelationMatrix object with analysis results
        """
        if self.returns_data is None or self.returns_data.empty:
            raise ValueError("Returns data required for correlation calculation")

        logger.info(f"Calculating correlation matrix using {method.value} method")

        # Clean data
        clean_data = self.returns_data.dropna(how='all').fillna(0)

        if len(clean_data) < min_periods:
            raise ValueError(f"Insufficient data: {len(clean_data)} < {min_periods}")

        # Calculate correlation based on method
        if method == CorrelationMethod.PEARSON:
            corr_matrix = clean_data.corr(method='pearson').values
        elif method == CorrelationMethod.SPEARMAN:
            corr_matrix = clean_data.corr(method='spearman').values
        elif method == CorrelationMethod.KENDALL:
            corr_matrix = clean_data.corr(method='kendall').values
        elif method == CorrelationMethod.ROLLING:
            if window is None:
                window = min(60, len(clean_data) // 2)
            rolling_corr = clean_data.rolling(window=window, min_periods=min_periods).corr()
            corr_matrix = rolling_corr.groupby(level=1).mean().values
        elif method == CorrelationMethod.EXPONENTIAL:
            # Exponentially weighted correlation
            span = window or 30
            ewm_corr = clean_data.ewm(span=span).corr()
            corr_matrix = ewm_corr.groupby(level=1).mean().values
        else:
            corr_matrix = clean_data.corr(method='pearson').values

        # Create correlation matrix object
        correlation_obj = CorrelationMatrix(
            assets=list(clean_data.columns),
            correlation_matrix=corr_matrix,
            method=method
        )

        # Store for later reference
        self.correlation_matrices[method.value] = correlation_obj

        return correlation_obj

    def rolling_correlation_analysis(
        self,
        window: int = 60,
        step: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze correlation stability over time using rolling windows.

        Args:
            window: Rolling window size
            step: Step size between windows

        Returns:
            Dictionary with correlation stability analysis
        """
        if self.returns_data is None:
            raise ValueError("Returns data required")

        logger.info(f"Performing rolling correlation analysis (window={window}, step={step})")

        clean_data = self.returns_data.dropna(how='all').fillna(0)
        correlation_timeline = []
        dates = []

        for start_idx in range(0, len(clean_data) - window + 1, step):
            end_idx = start_idx + window
            window_data = clean_data.iloc[start_idx:end_idx]

            if len(window_data) >= window * 0.8:  # At least 80% of window filled
                corr_matrix = window_data.corr().values

                # Calculate summary statistics
                off_diag = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
                avg_corr = np.mean(off_diag)
                corr_std = np.std(off_diag)

                correlation_timeline.append({
                    'date': window_data.index[-1],
                    'avg_correlation': avg_corr,
                    'correlation_std': corr_std,
                    'max_correlation': np.max(off_diag),
                    'min_correlation': np.min(off_diag)
                })

        timeline_df = pd.DataFrame(correlation_timeline)

        # Analyze trends
        correlation_trend = np.polyfit(range(len(timeline_df)), timeline_df['avg_correlation'], 1)[0]
        volatility_trend = np.polyfit(range(len(timeline_df)), timeline_df['correlation_std'], 1)[0]

        return {
            'timeline': timeline_df,
            'correlation_trend': correlation_trend,
            'volatility_trend': volatility_trend,
            'avg_correlation': timeline_df['avg_correlation'].mean(),
            'correlation_volatility': timeline_df['avg_correlation'].std(),
            'regime_changes': self._detect_correlation_regimes(timeline_df)
        }

    def _detect_correlation_regimes(self, timeline_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect correlation regime changes using statistical methods."""
        if len(timeline_df) < 20:
            return []

        correlation_series = timeline_df['avg_correlation']

        # Simple regime detection using rolling mean crossovers
        short_ma = correlation_series.rolling(window=5).mean()
        long_ma = correlation_series.rolling(window=20).mean()

        regime_changes = []
        current_regime = 'normal'

        for i in range(len(short_ma)):
            if pd.isna(short_ma.iloc[i]) or pd.isna(long_ma.iloc[i]):
                continue

            if short_ma.iloc[i] > long_ma.iloc[i] * 1.1 and current_regime != 'high':
                current_regime = 'high'
                regime_changes.append({
                    'date': timeline_df.iloc[i]['date'],
                    'regime': 'high_correlation',
                    'level': short_ma.iloc[i]
                })
            elif short_ma.iloc[i] < long_ma.iloc[i] * 0.9 and current_regime != 'low':
                current_regime = 'low'
                regime_changes.append({
                    'date': timeline_df.iloc[i]['date'],
                    'regime': 'low_correlation',
                    'level': short_ma.iloc[i]
                })

        return regime_changes

    def identify_risk_factors(self, method: str = 'pca', n_factors: Optional[int] = None) -> RiskFactorIdentifier:
        """
        Identify risk factors driving asset correlations.

        Args:
            method: Factor identification method ('pca' or 'factor_analysis')
            n_factors: Number of factors to extract

        Returns:
            RiskFactorIdentifier with factor analysis results
        """
        if self.returns_data is None:
            raise ValueError("Returns data required for factor analysis")

        self.risk_factors = RiskFactorIdentifier(
            returns_data=self.returns_data,
            factor_method=method
        )

        self.risk_factors.identify_factors(n_factors)

        return self.risk_factors

    def correlation_stress_test(
        self,
        stress_scenarios: Dict[str, float]
    ) -> Dict[str, CorrelationMatrix]:
        """
        Test correlation stability under stress scenarios.

        Args:
            stress_scenarios: Dictionary of scenario names to correlation shocks

        Returns:
            Dictionary of stressed correlation matrices
        """
        base_corr = self.correlation_matrices.get('pearson')
        if base_corr is None:
            base_corr = self.calculate_correlation_matrix()

        stressed_matrices = {}

        for scenario_name, shock_factor in stress_scenarios.items():
            # Apply correlation shock (simplified stress test)
            stressed_matrix = base_corr.correlation_matrix.copy()

            # Increase off-diagonal correlations by shock factor
            off_diag_mask = ~np.eye(stressed_matrix.shape[0], dtype=bool)
            stressed_matrix[off_diag_mask] *= (1 + shock_factor)

            # Ensure matrix remains valid correlation matrix
            stressed_matrix = np.clip(stressed_matrix, -0.99, 0.99)
            np.fill_diagonal(stressed_matrix, 1.0)

            stressed_matrices[scenario_name] = CorrelationMatrix(
                assets=base_corr.assets,
                correlation_matrix=stressed_matrix,
                method=base_corr.method
            )

        return stressed_matrices