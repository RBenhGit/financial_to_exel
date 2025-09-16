"""
Advanced Statistical Analysis for Financial Ratios
===================================================

Provides sophisticated statistical analysis capabilities for financial ratios
including trend analysis, volatility measurement, and correlation analysis.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Results of trend analysis for a ratio"""
    ratio_name: str
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1, strength of trend
    slope: float
    r_squared: float
    p_value: float
    volatility: float
    periods_analyzed: int
    is_significant: bool


@dataclass
class VolatilityMetrics:
    """Volatility analysis results"""
    ratio_name: str
    standard_deviation: float
    coefficient_of_variation: float
    value_at_risk_95: float  # 95% VaR
    maximum_drawdown: float
    volatility_percentile: float  # Relative to industry


@dataclass
class SeasonalityAnalysis:
    """Seasonality analysis results"""
    ratio_name: str
    has_seasonality: bool
    seasonal_strength: float
    peak_period: Optional[str]
    trough_period: Optional[str]
    seasonal_pattern: Dict[str, float] = field(default_factory=dict)


@dataclass
class CorrelationMatrix:
    """Correlation analysis between ratios"""
    correlation_matrix: np.ndarray
    ratio_names: List[str]
    significant_correlations: List[Tuple[str, str, float, float]]  # ratio1, ratio2, correlation, p_value


class RatioStatisticalAnalysis:
    """Advanced statistical analysis engine for financial ratios"""

    def __init__(self, confidence_level: float = 0.95):
        """Initialize with confidence level for statistical tests"""
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def analyze_trend(self, ratio_values: List[float], periods: Optional[List[datetime]] = None,
                     ratio_name: str = "unknown") -> TrendAnalysis:
        """
        Perform comprehensive trend analysis on ratio values

        Args:
            ratio_values: Historical ratio values
            periods: Optional datetime periods (if None, uses index)
            ratio_name: Name of the ratio being analyzed

        Returns:
            TrendAnalysis object with detailed trend information
        """
        if len(ratio_values) < 3:
            logger.warning(f"Insufficient data for trend analysis: {len(ratio_values)} points")
            return TrendAnalysis(
                ratio_name=ratio_name,
                trend_direction="insufficient_data",
                trend_strength=0.0,
                slope=0.0,
                r_squared=0.0,
                p_value=1.0,
                volatility=0.0,
                periods_analyzed=len(ratio_values),
                is_significant=False
            )

        # Clean data
        clean_data = self._clean_data(ratio_values)
        if len(clean_data) < 3:
            return TrendAnalysis(
                ratio_name=ratio_name,
                trend_direction="insufficient_clean_data",
                trend_strength=0.0,
                slope=0.0,
                r_squared=0.0,
                p_value=1.0,
                volatility=0.0,
                periods_analyzed=len(clean_data),
                is_significant=False
            )

        # Perform linear regression
        X = np.arange(len(clean_data)).reshape(-1, 1)
        y = np.array(clean_data)

        model = LinearRegression()
        model.fit(X, y)

        # Calculate statistics
        y_pred = model.predict(X)
        slope = model.coef_[0]
        r_squared = model.score(X, y)

        # Statistical significance test
        n = len(clean_data)
        t_stat = slope / (np.sqrt(np.sum((y - y_pred) ** 2) / (n - 2)) /
                         np.sqrt(np.sum((X.flatten() - np.mean(X)) ** 2)))
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

        # Determine trend direction and strength
        is_significant = p_value < self.alpha
        trend_strength = abs(slope) / np.mean(clean_data) if np.mean(clean_data) != 0 else 0

        if is_significant:
            if slope > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"
        else:
            trend_direction = "stable"

        # Calculate volatility
        volatility = np.std(clean_data) / np.mean(clean_data) if np.mean(clean_data) != 0 else 0

        return TrendAnalysis(
            ratio_name=ratio_name,
            trend_direction=trend_direction,
            trend_strength=min(trend_strength, 1.0),
            slope=slope,
            r_squared=r_squared,
            p_value=p_value,
            volatility=volatility,
            periods_analyzed=len(clean_data),
            is_significant=is_significant
        )

    def analyze_volatility(self, ratio_values: List[float], ratio_name: str = "unknown",
                          industry_benchmark_std: Optional[float] = None) -> VolatilityMetrics:
        """
        Analyze volatility characteristics of ratio values

        Args:
            ratio_values: Historical ratio values
            ratio_name: Name of the ratio
            industry_benchmark_std: Industry standard deviation for comparison

        Returns:
            VolatilityMetrics object
        """
        if len(ratio_values) < 2:
            logger.warning(f"Insufficient data for volatility analysis: {len(ratio_values)} points")
            return VolatilityMetrics(
                ratio_name=ratio_name,
                standard_deviation=0.0,
                coefficient_of_variation=0.0,
                value_at_risk_95=0.0,
                maximum_drawdown=0.0,
                volatility_percentile=50.0
            )

        clean_data = self._clean_data(ratio_values)
        if len(clean_data) < 2:
            return VolatilityMetrics(
                ratio_name=ratio_name,
                standard_deviation=0.0,
                coefficient_of_variation=0.0,
                value_at_risk_95=0.0,
                maximum_drawdown=0.0,
                volatility_percentile=50.0
            )

        values = np.array(clean_data)

        # Calculate basic volatility metrics
        std_dev = np.std(values)
        mean_value = np.mean(values)
        coeff_variation = std_dev / mean_value if mean_value != 0 else np.inf

        # Value at Risk (95% confidence)
        var_95 = np.percentile(values, 5) if len(values) > 1 else values[0]

        # Maximum drawdown
        max_drawdown = self._calculate_maximum_drawdown(values)

        # Volatility percentile relative to industry (if available)
        volatility_percentile = 50.0  # Default
        if industry_benchmark_std is not None and industry_benchmark_std > 0:
            # Simple percentile calculation
            if std_dev <= industry_benchmark_std * 0.8:
                volatility_percentile = 25.0  # Low volatility
            elif std_dev >= industry_benchmark_std * 1.2:
                volatility_percentile = 75.0  # High volatility
            else:
                volatility_percentile = 50.0  # Average volatility

        return VolatilityMetrics(
            ratio_name=ratio_name,
            standard_deviation=std_dev,
            coefficient_of_variation=coeff_variation,
            value_at_risk_95=var_95,
            maximum_drawdown=max_drawdown,
            volatility_percentile=volatility_percentile
        )

    def analyze_seasonality(self, ratio_values: List[float], periods: List[datetime],
                           ratio_name: str = "unknown") -> SeasonalityAnalysis:
        """
        Analyze seasonal patterns in ratio values

        Args:
            ratio_values: Historical ratio values
            periods: Corresponding datetime periods
            ratio_name: Name of the ratio

        Returns:
            SeasonalityAnalysis object
        """
        if len(ratio_values) != len(periods) or len(ratio_values) < 8:
            logger.warning(f"Insufficient data for seasonality analysis: {len(ratio_values)} points")
            return SeasonalityAnalysis(
                ratio_name=ratio_name,
                has_seasonality=False,
                seasonal_strength=0.0,
                peak_period=None,
                trough_period=None
            )

        try:
            df = pd.DataFrame({
                'date': periods,
                'value': ratio_values
            })
            df = df.dropna()

            if len(df) < 8:
                return SeasonalityAnalysis(
                    ratio_name=ratio_name,
                    has_seasonality=False,
                    seasonal_strength=0.0,
                    peak_period=None,
                    trough_period=None
                )

            # Extract quarterly patterns
            df['quarter'] = df['date'].dt.quarter
            quarterly_means = df.groupby('quarter')['value'].mean()

            # Test for significant seasonal variation
            quarterly_values = [df[df['quarter'] == q]['value'].tolist() for q in range(1, 5)]
            quarterly_values = [q for q in quarterly_values if len(q) > 0]

            if len(quarterly_values) >= 3:
                # ANOVA test for seasonal differences
                try:
                    f_stat, p_value = stats.f_oneway(*quarterly_values)
                    has_seasonality = p_value < self.alpha
                except:
                    has_seasonality = False
                    f_stat = 0.0
            else:
                has_seasonality = False
                f_stat = 0.0

            # Calculate seasonal strength
            overall_mean = df['value'].mean()
            seasonal_variance = quarterly_means.var()
            total_variance = df['value'].var()
            seasonal_strength = seasonal_variance / total_variance if total_variance > 0 else 0.0

            # Find peak and trough periods
            peak_quarter = quarterly_means.idxmax() if len(quarterly_means) > 0 else None
            trough_quarter = quarterly_means.idxmin() if len(quarterly_means) > 0 else None

            quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
            peak_period = quarter_names.get(peak_quarter) if peak_quarter else None
            trough_period = quarter_names.get(trough_quarter) if trough_quarter else None

            # Create seasonal pattern dictionary
            seasonal_pattern = {
                quarter_names[q]: quarterly_means[q] for q in quarterly_means.index
            }

            return SeasonalityAnalysis(
                ratio_name=ratio_name,
                has_seasonality=has_seasonality,
                seasonal_strength=min(seasonal_strength, 1.0),
                peak_period=peak_period,
                trough_period=trough_period,
                seasonal_pattern=seasonal_pattern
            )

        except Exception as e:
            logger.error(f"Error in seasonality analysis: {e}")
            return SeasonalityAnalysis(
                ratio_name=ratio_name,
                has_seasonality=False,
                seasonal_strength=0.0,
                peak_period=None,
                trough_period=None
            )

    def analyze_correlation(self, ratios_data: Dict[str, List[float]],
                           min_correlation: float = 0.3) -> CorrelationMatrix:
        """
        Analyze correlations between different ratios

        Args:
            ratios_data: Dictionary of ratio_name -> values
            min_correlation: Minimum correlation to be considered significant

        Returns:
            CorrelationMatrix object
        """
        if len(ratios_data) < 2:
            logger.warning("Need at least 2 ratios for correlation analysis")
            return CorrelationMatrix(
                correlation_matrix=np.array([]),
                ratio_names=[],
                significant_correlations=[]
            )

        try:
            # Create DataFrame
            df_data = {}
            min_length = float('inf')

            for ratio_name, values in ratios_data.items():
                clean_values = self._clean_data(values)
                if len(clean_values) > 0:
                    df_data[ratio_name] = clean_values
                    min_length = min(min_length, len(clean_values))

            # Ensure all series have same length
            for ratio_name in df_data:
                df_data[ratio_name] = df_data[ratio_name][:min_length]

            if min_length < 3:
                logger.warning("Insufficient data for correlation analysis")
                return CorrelationMatrix(
                    correlation_matrix=np.array([]),
                    ratio_names=[],
                    significant_correlations=[]
                )

            df = pd.DataFrame(df_data)
            correlation_matrix = df.corr().values
            ratio_names = list(df.columns)

            # Find significant correlations
            significant_correlations = []
            n = len(ratio_names)

            for i in range(n):
                for j in range(i + 1, n):
                    corr_value = correlation_matrix[i, j]

                    if abs(corr_value) >= min_correlation:
                        # Calculate p-value for correlation
                        try:
                            _, p_value = stats.pearsonr(df.iloc[:, i], df.iloc[:, j])
                        except:
                            p_value = 0.05  # Default if calculation fails

                        significant_correlations.append((
                            ratio_names[i],
                            ratio_names[j],
                            corr_value,
                            p_value
                        ))

            return CorrelationMatrix(
                correlation_matrix=correlation_matrix,
                ratio_names=ratio_names,
                significant_correlations=significant_correlations
            )

        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return CorrelationMatrix(
                correlation_matrix=np.array([]),
                ratio_names=[],
                significant_correlations=[]
            )

    def _clean_data(self, values: List[float]) -> List[float]:
        """Clean data by removing NaN, infinite, and extreme outliers"""
        clean_values = []

        for value in values:
            if isinstance(value, (int, float)) and np.isfinite(value):
                clean_values.append(float(value))

        # Remove extreme outliers (beyond 3 standard deviations)
        if len(clean_values) > 3:
            mean_val = np.mean(clean_values)
            std_val = np.std(clean_values)

            if std_val > 0:
                filtered_values = []
                for value in clean_values:
                    if abs(value - mean_val) <= 3 * std_val:
                        filtered_values.append(value)

                if len(filtered_values) >= len(clean_values) * 0.8:  # Keep if we retain 80%+ of data
                    clean_values = filtered_values

        return clean_values

    def _calculate_maximum_drawdown(self, values: np.ndarray) -> float:
        """Calculate maximum drawdown from peak to trough"""
        if len(values) < 2:
            return 0.0

        running_max = np.maximum.accumulate(values)
        drawdowns = (values - running_max) / running_max

        return abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

    def generate_comprehensive_report(self, ratios_data: Dict[str, List[float]],
                                    periods: Optional[List[datetime]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive statistical report for all ratios

        Args:
            ratios_data: Dictionary of ratio_name -> values
            periods: Optional datetime periods

        Returns:
            Dictionary containing all analysis results
        """
        report = {
            'summary': {
                'total_ratios': len(ratios_data),
                'analysis_date': datetime.now().isoformat(),
                'confidence_level': self.confidence_level
            },
            'trend_analysis': {},
            'volatility_analysis': {},
            'seasonality_analysis': {},
            'correlation_analysis': {}
        }

        # Individual ratio analysis
        for ratio_name, values in ratios_data.items():
            if len(values) > 0:
                # Trend analysis
                trend = self.analyze_trend(values, periods, ratio_name)
                report['trend_analysis'][ratio_name] = trend

                # Volatility analysis
                volatility = self.analyze_volatility(values, ratio_name)
                report['volatility_analysis'][ratio_name] = volatility

                # Seasonality analysis (if periods provided)
                if periods and len(periods) == len(values):
                    seasonality = self.analyze_seasonality(values, periods, ratio_name)
                    report['seasonality_analysis'][ratio_name] = seasonality

        # Correlation analysis
        correlation = self.analyze_correlation(ratios_data)
        report['correlation_analysis'] = correlation

        # Summary statistics
        improving_ratios = sum(1 for trend in report['trend_analysis'].values()
                             if trend.trend_direction == "improving")
        declining_ratios = sum(1 for trend in report['trend_analysis'].values()
                             if trend.trend_direction == "declining")

        report['summary'].update({
            'improving_ratios': improving_ratios,
            'declining_ratios': declining_ratios,
            'stable_ratios': len(ratios_data) - improving_ratios - declining_ratios,
            'high_volatility_ratios': sum(1 for vol in report['volatility_analysis'].values()
                                        if vol.coefficient_of_variation > 0.3),
            'significant_correlations': len(correlation.significant_correlations)
        })

        return report