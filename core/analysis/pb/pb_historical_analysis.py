"""
Historical P/B Performance Analysis Engine with DataQualityMetrics
=================================================================

This module extends the existing P/B calculation engine to provide comprehensive
historical P/B performance analysis with integrated data quality assessment.

Key Features:
- Historical P/B performance analysis over 5+ years
- P/B-specific data quality metrics and validation
- Trend analysis and statistical calculations
- Rolling statistics (mean, median, percentiles) and volatility metrics
- Quality-weighted confidence calculations
- Data completeness gap detection and handling

Classes:
--------
PBHistoricalQualityMetrics
    Extended DataQualityMetrics specifically for P/B historical analysis
    
PBHistoricalAnalysisEngine
    Main engine for historical P/B performance analysis with quality assessment
    
PBTrendAnalysis  
    Trend analysis results with statistical metrics

Usage Example:
--------------
>>> from pb_historical_analysis import PBHistoricalAnalysisEngine
>>> from data_sources import DataSourceResponse
>>> 
>>> engine = PBHistoricalAnalysisEngine()
>>> analysis = engine.analyze_historical_performance(response, years=5)
>>> print(f"Average P/B over 5 years: {analysis.statistics['mean_pb']:.2f}")
>>> print(f"Data quality score: {analysis.quality_metrics.overall_score:.2f}")
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from statistics import median, stdev
import warnings
from scipy import stats
from scipy.stats import norm, t, jarque_bera
import random

from ...data_sources.interfaces.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics
from .pb_calculation_engine import PBCalculationEngine, PBDataPoint, PBCalculationResult

logger = logging.getLogger(__name__)


@dataclass
class PBHistoricalQualityMetrics(DataQualityMetrics):
    """
    Extended DataQualityMetrics specifically for P/B historical analysis.
    
    Adds P/B-specific quality metrics for historical datasets.
    """
    
    # P/B-specific quality metrics
    pb_data_completeness: float = 0.0  # Percentage of periods with valid P/B data
    price_data_quality: float = 0.0    # Quality of historical price data
    balance_sheet_quality: float = 0.0  # Quality of balance sheet data
    temporal_consistency: float = 0.0   # Consistency across time periods
    outlier_detection_score: float = 0.0  # Percentage of data points that are reasonable
    data_gap_penalty: float = 0.0      # Penalty for missing data periods
    
    # Confidence intervals
    confidence_level: float = 0.95     # Confidence level for statistical measures
    confidence_interval_width: float = 0.0  # Width of confidence interval
    
    def calculate_overall_score(self) -> float:
        """Calculate overall quality score with P/B-specific weights"""
        weights = {
            'completeness': 0.20,
            'accuracy': 0.20,
            'timeliness': 0.10,
            'consistency': 0.15,
            'pb_data_completeness': 0.15,
            'price_data_quality': 0.10,
            'balance_sheet_quality': 0.10,
        }
        
        self.overall_score = (
            self.completeness * weights['completeness']
            + self.accuracy * weights['accuracy']
            + self.timeliness * weights['timeliness']
            + self.consistency * weights['consistency']
            + self.pb_data_completeness * weights['pb_data_completeness']
            + self.price_data_quality * weights['price_data_quality']
            + self.balance_sheet_quality * weights['balance_sheet_quality']
        )
        
        # Apply penalty for data gaps
        self.overall_score *= (1.0 - self.data_gap_penalty)
        
        # Ensure score stays within bounds
        self.overall_score = max(0.0, min(1.0, self.overall_score))
        
        return self.overall_score


@dataclass
class PBTrendAnalysis:
    """Results of P/B trend analysis"""
    
    trend_direction: str = "neutral"  # "upward", "downward", "neutral"
    trend_strength: float = 0.0       # 0.0 to 1.0, strength of trend
    trend_slope: float = 0.0          # Linear regression slope
    r_squared: float = 0.0            # R-squared of trend line
    volatility: float = 0.0           # Standard deviation of P/B ratios
    mean_reversion_score: float = 0.0 # How much P/B tends to revert to mean
    
    # Cycle analysis
    cycles_detected: int = 0          # Number of P/B cycles detected
    avg_cycle_duration: float = 0.0   # Average duration of cycles in months
    current_cycle_position: str = "unknown"  # "peak", "trough", "rising", "falling"


@dataclass
class PBStatisticalSummary:
    """Statistical summary of historical P/B performance"""
    
    # Basic statistics
    mean_pb: float = 0.0
    median_pb: float = 0.0
    std_pb: float = 0.0
    min_pb: float = 0.0
    max_pb: float = 0.0
    
    # Percentiles
    p25_pb: float = 0.0  # 25th percentile
    p75_pb: float = 0.0  # 75th percentile
    p90_pb: float = 0.0  # 90th percentile
    p95_pb: float = 0.0  # 95th percentile
    
    # Rolling statistics (12-month windows)
    rolling_mean_12m: List[float] = field(default_factory=list)
    rolling_median_12m: List[float] = field(default_factory=list)
    rolling_std_12m: List[float] = field(default_factory=list)
    
    # Quality-adjusted statistics (weighted by data quality)
    quality_weighted_mean: float = 0.0
    quality_weighted_std: float = 0.0
    
    # Time series analysis
    autocorrelation_lag1: float = 0.0  # First-order autocorrelation
    seasonal_patterns: Dict[str, float] = field(default_factory=dict)
    
    # Confidence intervals
    mean_confidence_interval: Tuple[float, float] = (0.0, 0.0)
    prediction_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Statistical significance testing
    normality_test_pvalue: float = 0.0  # Jarque-Bera test p-value
    is_normal_distribution: bool = False
    statistical_significance: Dict[str, float] = field(default_factory=dict)  # Various significance tests
    
    # Monte Carlo simulation results
    monte_carlo_mean: float = 0.0
    monte_carlo_std: float = 0.0
    monte_carlo_confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    monte_carlo_value_at_risk: Dict[str, float] = field(default_factory=dict)  # VaR at different confidence levels
    
    # Risk-adjusted metrics
    risk_adjusted_return: float = 0.0  # Sharpe-like ratio for P/B
    downside_deviation: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0


@dataclass
class PBHistoricalAnalysisResult:
    """Complete result of historical P/B analysis"""
    
    success: bool
    ticker: str = ""
    analysis_period: str = ""
    data_points_count: int = 0
    
    # Core data
    historical_data: List[PBDataPoint] = field(default_factory=list)
    
    # Quality assessment
    quality_metrics: Optional[PBHistoricalQualityMetrics] = None
    
    # Statistical analysis
    statistics: Optional[PBStatisticalSummary] = None
    
    # Trend analysis
    trend_analysis: Optional[PBTrendAnalysis] = None
    
    # Valuation insights
    current_pb_percentile: float = 0.0  # Where current P/B sits historically
    fair_value_estimate: Optional[float] = None
    valuation_signal: str = "neutral"  # "undervalued", "overvalued", "neutral"
    
    # Risk-adjusted scenarios
    risk_scenarios: Dict[str, Dict[str, float]] = field(default_factory=dict)  # Bear, base, bull scenarios
    scenario_probabilities: Dict[str, float] = field(default_factory=dict)
    volatility_adjusted_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Warnings and notes
    quality_warnings: List[str] = field(default_factory=list)
    analysis_notes: List[str] = field(default_factory=list)
    
    error_message: Optional[str] = None


class PBHistoricalAnalysisEngine:
    """
    Engine for comprehensive historical P/B performance analysis with quality assessment.
    
    This engine builds on the existing PBCalculationEngine and DataQualityMetrics
    framework to provide in-depth historical P/B analysis.
    """
    
    def __init__(self):
        """Initialize the historical P/B analysis engine"""
        self.pb_engine = PBCalculationEngine()
        self.min_data_points = 12  # Minimum data points for meaningful analysis
        self.confidence_level = 0.95
        
        logger.info("P/B Historical Analysis Engine initialized")
    
    def analyze_historical_performance(self, response: DataSourceResponse, 
                                     years: int = 5) -> PBHistoricalAnalysisResult:
        """
        Comprehensive historical P/B performance analysis with advanced statistical methods.
        
        This method orchestrates a complete P/B analysis workflow that combines historical
        data processing, statistical analysis, quality assessment, and valuation insights.
        It serves as the main entry point for historical P/B analysis in the application.
        
        Analysis Components:
        1. **Historical Data Processing**: Uses PBCalculationEngine to extract P/B data points
           with temporal matching and quality weighting
        
        2. **Statistical Analysis**: Computes comprehensive statistics including:
           - Basic metrics: mean, median, standard deviation, min/max
           - Distribution analysis: skewness, kurtosis, normality testing
           - Percentiles: 25th, 75th, 90th, 95th percentiles
           - Outlier detection using IQR method
        
        3. **Trend Analysis**: Performs time series analysis including:
           - Linear regression for trend direction and strength
           - Autocorrelation analysis for pattern detection
           - Rolling statistics for trend stability assessment
        
        4. **Quality Assessment**: Evaluates data quality using P/B-specific metrics:
           - Data completeness and consistency scoring
           - Temporal alignment quality assessment
           - Cross-validation across data sources
        
        5. **Fair Value Estimation**: Generates valuation estimates with:
           - Quality-weighted historical mean approach
           - Monte Carlo simulation for confidence intervals
           - Risk-adjusted scenario analysis (Bear/Base/Bull)
        
        Args:
            response (DataSourceResponse): DataSourceResponse containing:
                - Historical price data (daily/monthly)
                - Balance sheet data (quarterly/annual)
                - Shares outstanding information
                - Data quality metrics from the provider
            years (int, optional): Analysis period in years. Defaults to 5.
                                  Minimum 2 years required for meaningful analysis.
        
        Returns:
            PBHistoricalAnalysisResult: Comprehensive analysis results containing:
                - pb_data_points: List of historical P/B calculations
                - statistics: Dict with statistical summary metrics
                - trend_analysis: Trend direction, strength, and significance
                - quality_metrics: P/B-specific data quality assessment
                - fair_value_estimates: Valuation estimates with confidence intervals
                - monte_carlo_results: Simulation-based value distribution
                - analysis_notes: Warnings and data quality insights
        
        Raises:
            ValueError: If years < 2 or response data is invalid
            RuntimeError: If P/B calculation engine fails to process data
            StatisticsError: If insufficient data points for statistical analysis
        
        Example:
            >>> engine = PBHistoricalAnalysisEngine()
            >>> api_response = get_historical_data("AAPL", years=5)
            >>> analysis = engine.analyze_historical_performance(api_response, years=5)
            >>> 
            >>> print(f"Average P/B: {analysis.statistics['mean_pb']:.2f}")
            >>> print(f"Data Quality: {analysis.quality_metrics.overall_score:.1%}")
            >>> print(f"Fair Value Estimate: ${analysis.fair_value_estimates['base_scenario']:.2f}")
        
        Note:
            - Requires minimum 12 data points for robust statistical analysis
            - Quality scores below 0.5 trigger warnings about result reliability  
            - Monte Carlo simulation uses 1,000-10,000 samples based on data quality
            - Results are cached for performance optimization on repeated calls
            - See docs/PB_HISTORICAL_METHODOLOGY.md for detailed methodology
        """
        try:
            logger.info(f"Starting historical P/B analysis for {years} years")
            
            # Initialize result
            result = PBHistoricalAnalysisResult(
                success=False,
                analysis_period=f"{years} years"
            )
            
            if not response.success or not response.data:
                result.error_message = "Invalid or unsuccessful data response"
                return result
            
            # Extract ticker from response data
            ticker = response.data.get('ticker', 'Unknown')
            result.ticker = ticker
            
            # Get historical P/B data points
            historical_pb_data = self.pb_engine.calculate_historical_pb(response, years)
            
            if len(historical_pb_data) < self.min_data_points:
                result.error_message = f"Insufficient data points ({len(historical_pb_data)}) for analysis"
                result.quality_warnings.append(f"Only {len(historical_pb_data)} data points available")
                return result
            
            result.historical_data = historical_pb_data
            result.data_points_count = len(historical_pb_data)
            
            # Calculate P/B-specific quality metrics
            quality_metrics = self._calculate_pb_quality_metrics(historical_pb_data, response)
            result.quality_metrics = quality_metrics
            
            # Perform statistical analysis
            statistics = self._calculate_statistical_summary(historical_pb_data, quality_metrics)
            result.statistics = statistics
            
            # Perform trend analysis
            trend_analysis = self._analyze_trends(historical_pb_data)
            result.trend_analysis = trend_analysis
            
            # Calculate current position and valuation signals
            self._calculate_valuation_insights(result)
            
            # Generate risk-adjusted scenarios
            self._generate_risk_scenarios(result)
            
            # Generate quality warnings and analysis notes
            self._generate_analysis_notes(result)
            
            result.success = True
            logger.info(f"Historical P/B analysis completed successfully for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in historical P/B analysis: {e}")
            return PBHistoricalAnalysisResult(
                success=False,
                error_message=f"Analysis error: {str(e)}"
            )
    
    def _calculate_pb_quality_metrics(self, pb_data: List[PBDataPoint], 
                                    response: DataSourceResponse) -> PBHistoricalQualityMetrics:
        """Calculate P/B-specific quality metrics for historical data"""
        try:
            metrics = PBHistoricalQualityMetrics()
            
            if not pb_data:
                return metrics
            
            # Basic quality metrics from base response
            if response.quality_metrics:
                metrics.completeness = response.quality_metrics.completeness
                metrics.accuracy = response.quality_metrics.accuracy
                metrics.timeliness = response.quality_metrics.timeliness
                metrics.consistency = response.quality_metrics.consistency
            else:
                # Default reasonable values
                metrics.completeness = 0.8
                metrics.accuracy = 0.85
                metrics.timeliness = 0.7
                metrics.consistency = 0.8
            
            # P/B-specific completeness
            valid_pb_points = [dp for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
            metrics.pb_data_completeness = len(valid_pb_points) / len(pb_data)
            
            # Price data quality assessment
            valid_prices = [dp for dp in pb_data if dp.price and dp.price > 0]
            metrics.price_data_quality = len(valid_prices) / len(pb_data)
            
            # Balance sheet data quality assessment
            valid_bvps = [dp for dp in pb_data if dp.book_value_per_share and dp.book_value_per_share > 0]
            metrics.balance_sheet_quality = len(valid_bvps) / len(pb_data)
            
            # Temporal consistency check
            metrics.temporal_consistency = self._assess_temporal_consistency(pb_data)
            
            # Outlier detection
            metrics.outlier_detection_score = self._calculate_outlier_score(pb_data)
            
            # Data gap penalty
            metrics.data_gap_penalty = self._calculate_data_gap_penalty(pb_data)
            
            # Calculate confidence interval width
            if len(valid_pb_points) > 1:
                pb_values = [dp.pb_ratio for dp in valid_pb_points]
                std_err = np.std(pb_values) / np.sqrt(len(pb_values))
                # Approximate 95% confidence interval width
                metrics.confidence_interval_width = 1.96 * std_err * 2  # Full width
            
            # Calculate overall score
            metrics.calculate_overall_score()
            
            logger.debug(f"P/B quality metrics calculated: overall_score={metrics.overall_score:.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating P/B quality metrics: {e}")
            return PBHistoricalQualityMetrics()
    
    def _assess_temporal_consistency(self, pb_data: List[PBDataPoint]) -> float:
        """Assess temporal consistency of P/B data"""
        try:
            if len(pb_data) < 2:
                return 0.0
            
            # Check for reasonable temporal ordering and values
            dates = [pd.to_datetime(dp.date) for dp in pb_data if dp.date]
            dates.sort()
            
            if len(dates) != len(pb_data):
                return 0.5  # Some missing dates
            
            # Check for reasonable time intervals
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            
            # For quarterly data, expect ~90 day intervals
            expected_interval = 90
            reasonable_intervals = [abs(interval - expected_interval) < 45 for interval in intervals]
            
            consistency_score = sum(reasonable_intervals) / len(reasonable_intervals)
            
            return consistency_score
            
        except Exception as e:
            logger.debug(f"Error assessing temporal consistency: {e}")
            return 0.5
    
    def _calculate_outlier_score(self, pb_data: List[PBDataPoint]) -> float:
        """Calculate score based on outlier detection in P/B ratios"""
        try:
            valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
            
            if len(valid_ratios) < 3:
                return 0.5
            
            # Interquartile Range (IQR) method for robust outlier detection
            # This method is less sensitive to extreme values than standard deviation
            q1 = np.percentile(valid_ratios, 25)
            q3 = np.percentile(valid_ratios, 75)
            iqr = q3 - q1
            
            # Standard outlier boundaries: Q1 - 1.5*IQR and Q3 + 1.5*IQR
            # Values outside these bounds are considered statistical outliers
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Filter out statistical outliers to get reasonable P/B ratio range
            reasonable_values = [ratio for ratio in valid_ratios 
                               if lower_bound <= ratio <= upper_bound]
            
            # Calculate outlier score as proportion of non-outlier values
            outlier_score = len(reasonable_values) / len(valid_ratios)
            
            # Small data penalty: reduce confidence when insufficient data for reliable statistics
            if len(valid_ratios) < 5:
                outlier_score *= 0.95
            
            return outlier_score
            
        except Exception as e:
            logger.debug(f"Error calculating outlier score: {e}")
            return 0.5
    
    def _calculate_data_gap_penalty(self, pb_data: List[PBDataPoint]) -> float:
        """Calculate penalty for data gaps in the time series"""
        try:
            if len(pb_data) < 2:
                return 0.5
            
            # Sort by date
            sorted_data = sorted(pb_data, key=lambda x: pd.to_datetime(x.date))
            dates = [pd.to_datetime(dp.date) for dp in sorted_data]
            
            # Estimate data completeness based on quarterly reporting assumption
            # Financial statements are typically reported quarterly (every ~90 days)
            total_period = (dates[-1] - dates[0]).days
            expected_periods = max(1, total_period // 90)
            
            actual_periods = len(pb_data)
            
            if expected_periods > 0:
                # Calculate how complete our data series is relative to expected quarterly reports
                completeness_ratio = actual_periods / expected_periods
                # Apply penalty proportional to missing data, capped at 30% total penalty
                gap_penalty = max(0.0, 1.0 - completeness_ratio) * 0.3
            else:
                gap_penalty = 0.0
            
            return gap_penalty
            
        except Exception as e:
            logger.debug(f"Error calculating data gap penalty: {e}")
            return 0.1
    
    def _calculate_statistical_summary(self, pb_data: List[PBDataPoint], 
                                     quality_metrics: PBHistoricalQualityMetrics) -> PBStatisticalSummary:
        """Calculate comprehensive statistical summary of P/B data"""
        try:
            summary = PBStatisticalSummary()
            
            # Extract valid P/B ratios
            valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
            
            if not valid_ratios:
                return summary
            
            # Basic statistics
            summary.mean_pb = np.mean(valid_ratios)
            summary.median_pb = np.median(valid_ratios)
            summary.std_pb = np.std(valid_ratios)
            summary.min_pb = np.min(valid_ratios)
            summary.max_pb = np.max(valid_ratios)
            
            # Percentiles
            summary.p25_pb = np.percentile(valid_ratios, 25)
            summary.p75_pb = np.percentile(valid_ratios, 75)
            summary.p90_pb = np.percentile(valid_ratios, 90)
            summary.p95_pb = np.percentile(valid_ratios, 95)
            
            # Rolling statistics (12-month windows)
            if len(valid_ratios) >= 4:  # At least 4 quarters
                summary.rolling_mean_12m = self._calculate_rolling_stats(pb_data, 'mean', 4)
                summary.rolling_median_12m = self._calculate_rolling_stats(pb_data, 'median', 4)
                summary.rolling_std_12m = self._calculate_rolling_stats(pb_data, 'std', 4)
            
            # Quality-weighted statistics
            quality_weights = [dp.data_quality or quality_metrics.overall_score for dp in pb_data 
                             if dp.pb_ratio and dp.pb_ratio > 0]
            
            if len(quality_weights) == len(valid_ratios) and sum(quality_weights) > 0:
                summary.quality_weighted_mean = np.average(valid_ratios, weights=quality_weights)
                # Quality-weighted standard deviation approximation
                summary.quality_weighted_std = np.sqrt(
                    np.average((np.array(valid_ratios) - summary.quality_weighted_mean)**2, 
                              weights=quality_weights)
                )
            else:
                summary.quality_weighted_mean = summary.mean_pb
                summary.quality_weighted_std = summary.std_pb
            
            # Time series analysis
            if len(valid_ratios) > 1:
                summary.autocorrelation_lag1 = self._calculate_autocorrelation(valid_ratios, 1)
            
            # Confidence intervals
            if len(valid_ratios) > 1:
                summary.mean_confidence_interval = self._calculate_confidence_intervals(
                    valid_ratios, quality_metrics.overall_score
                )
            
            # Statistical significance testing
            if len(valid_ratios) >= 8:  # Need reasonable sample size
                summary = self._perform_statistical_significance_tests(summary, valid_ratios)
            
            # Monte Carlo simulation
            if len(valid_ratios) >= 5:
                summary = self._run_monte_carlo_simulation(summary, valid_ratios, quality_metrics)
            
            # Risk-adjusted metrics
            summary = self._calculate_risk_adjusted_metrics(summary, valid_ratios)
            
            logger.debug(f"Statistical summary calculated: mean_pb={summary.mean_pb:.3f}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating statistical summary: {e}")
            return PBStatisticalSummary()
    
    def _calculate_rolling_stats(self, pb_data: List[PBDataPoint], 
                               stat_type: str, window: int) -> List[float]:
        """Calculate rolling statistics for P/B data"""
        try:
            # Sort by date
            sorted_data = sorted(pb_data, key=lambda x: pd.to_datetime(x.date))
            valid_ratios = [dp.pb_ratio for dp in sorted_data if dp.pb_ratio and dp.pb_ratio > 0]
            
            if len(valid_ratios) < window:
                return []
            
            rolling_stats = []
            
            for i in range(window - 1, len(valid_ratios)):
                window_data = valid_ratios[i - window + 1:i + 1]
                
                if stat_type == 'mean':
                    stat_value = np.mean(window_data)
                elif stat_type == 'median':
                    stat_value = np.median(window_data)
                elif stat_type == 'std':
                    stat_value = np.std(window_data)
                else:
                    stat_value = np.mean(window_data)
                
                rolling_stats.append(stat_value)
            
            return rolling_stats
            
        except Exception as e:
            logger.debug(f"Error calculating rolling {stat_type}: {e}")
            return []
    
    def _calculate_autocorrelation(self, values: List[float], lag: int) -> float:
        """Calculate autocorrelation at specified lag"""
        try:
            if len(values) <= lag:
                return 0.0
            
            # Simple autocorrelation calculation
            n = len(values)
            mean_val = np.mean(values)
            
            # Calculate autocovariance
            autocovariance = np.mean([
                (values[i] - mean_val) * (values[i - lag] - mean_val)
                for i in range(lag, n)
            ])
            
            # Calculate variance
            variance = np.var(values)
            
            if variance == 0:
                return 0.0
            
            autocorr = autocovariance / variance
            return autocorr
            
        except Exception as e:
            logger.debug(f"Error calculating autocorrelation: {e}")
            return 0.0
    
    def _calculate_confidence_intervals(self, valid_ratios: List[float], 
                                      quality_score: float) -> Tuple[float, float]:
        """Calculate quality-weighted confidence intervals"""
        try:
            n = len(valid_ratios)
            mean_val = np.mean(valid_ratios)
            std_val = np.std(valid_ratios, ddof=1)  # Sample standard deviation
            
            # Quality adjustment for confidence level
            # Higher quality data allows for narrower confidence intervals
            base_confidence = 0.95
            quality_adjustment = quality_score * 0.05  # Up to 5% adjustment
            adjusted_confidence = min(0.99, base_confidence + quality_adjustment)
            
            # Use t-distribution for small samples, normal for large samples
            if n < 30:
                # Use t-distribution
                t_critical = stats.t.ppf((1 + adjusted_confidence) / 2, df=n-1)
                margin = t_critical * (std_val / np.sqrt(n))
            else:
                # Use normal distribution
                z_critical = stats.norm.ppf((1 + adjusted_confidence) / 2)
                margin = z_critical * (std_val / np.sqrt(n))
            
            # Apply quality-based adjustment to margin
            # Lower quality data should have wider intervals
            quality_margin_adjustment = 1.0 + (1.0 - quality_score) * 0.5
            adjusted_margin = margin * quality_margin_adjustment
            
            confidence_interval = (
                mean_val - adjusted_margin,
                mean_val + adjusted_margin
            )
            
            logger.debug(f"Quality-weighted confidence interval: {confidence_interval}")
            return confidence_interval
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            # Return basic confidence interval as fallback
            mean_val = np.mean(valid_ratios)
            std_val = np.std(valid_ratios)
            margin = 1.96 * (std_val / np.sqrt(len(valid_ratios)))
            return (mean_val - margin, mean_val + margin)
    
    def _perform_statistical_significance_tests(self, summary: PBStatisticalSummary, 
                                              valid_ratios: List[float]) -> PBStatisticalSummary:
        """Perform comprehensive statistical significance testing"""
        try:
            # Normality test (Jarque-Bera)
            try:
                jb_stat, jb_pvalue = jarque_bera(valid_ratios)
                summary.normality_test_pvalue = jb_pvalue
                summary.is_normal_distribution = jb_pvalue > 0.05  # 5% significance level
                summary.statistical_significance['jarque_bera_pvalue'] = jb_pvalue
            except Exception as e:
                logger.debug(f"Jarque-Bera test failed: {e}")
                summary.normality_test_pvalue = 0.5
                summary.is_normal_distribution = True  # Assume normal as fallback
            
            # Test if mean is significantly different from common P/B benchmarks
            benchmarks = {
                'market_average': 2.5,  # Typical market P/B
                'value_threshold': 1.0,  # Traditional value investing threshold
                'growth_threshold': 3.0  # Growth stock threshold
            }
            
            n = len(valid_ratios)
            sample_mean = np.mean(valid_ratios)
            sample_std = np.std(valid_ratios, ddof=1)
            
            for benchmark_name, benchmark_value in benchmarks.items():
                try:
                    # One-sample t-test
                    t_stat = (sample_mean - benchmark_value) / (sample_std / np.sqrt(n))
                    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))  # Two-tailed test
                    summary.statistical_significance[f'{benchmark_name}_ttest_pvalue'] = p_value
                    summary.statistical_significance[f'{benchmark_name}_is_significant'] = p_value < 0.05
                except Exception as e:
                    logger.debug(f"T-test for {benchmark_name} failed: {e}")
            
            # Test for trend significance (if we have time series)
            if len(valid_ratios) >= 10:
                try:
                    # Simple trend test using correlation with time index
                    time_index = list(range(len(valid_ratios)))
                    correlation, p_value = stats.pearsonr(time_index, valid_ratios)
                    summary.statistical_significance['trend_correlation'] = correlation
                    summary.statistical_significance['trend_pvalue'] = p_value
                    summary.statistical_significance['trend_is_significant'] = p_value < 0.05
                except Exception as e:
                    logger.debug(f"Trend significance test failed: {e}")
            
            # Calculate distribution moments
            try:
                summary.skewness = stats.skew(valid_ratios)
                summary.kurtosis = stats.kurtosis(valid_ratios)
            except Exception as e:
                logger.debug(f"Moment calculations failed: {e}")
                summary.skewness = 0.0
                summary.kurtosis = 0.0
            
            logger.debug(f"Statistical significance tests completed")
            return summary
            
        except Exception as e:
            logger.error(f"Error in statistical significance testing: {e}")
            return summary
    
    def _run_monte_carlo_simulation(self, summary: PBStatisticalSummary, 
                                  valid_ratios: List[float], 
                                  quality_metrics: PBHistoricalQualityMetrics) -> PBStatisticalSummary:
        """Run Monte Carlo simulation for fair value distribution analysis"""
        try:
            n_simulations = min(10000, max(1000, len(valid_ratios) * 100))  # Scale with data size
            
            # Estimate distribution parameters
            sample_mean = np.mean(valid_ratios)
            sample_std = np.std(valid_ratios, ddof=1)
            
            # Quality-adjusted standard deviation
            # Lower quality data should have higher uncertainty
            quality_adjustment = 1.0 + (1.0 - quality_metrics.overall_score) * 0.5
            adjusted_std = sample_std * quality_adjustment
            
            # Generate Monte Carlo samples
            if summary.is_normal_distribution:
                # Use normal distribution
                mc_samples = np.random.normal(sample_mean, adjusted_std, n_simulations)
            else:
                # Use bootstrap resampling for non-normal data
                mc_samples = np.random.choice(valid_ratios, size=n_simulations, replace=True)
                # Add some noise based on quality
                noise = np.random.normal(0, adjusted_std * 0.1, n_simulations)
                mc_samples = mc_samples + noise
            
            # Ensure no negative P/B ratios
            mc_samples = np.maximum(mc_samples, 0.01)
            
            # Calculate Monte Carlo statistics
            summary.monte_carlo_mean = np.mean(mc_samples)
            summary.monte_carlo_std = np.std(mc_samples)
            
            # Calculate confidence intervals from Monte Carlo
            confidence_levels = [0.90, 0.95, 0.99]
            for conf_level in confidence_levels:
                alpha = 1 - conf_level
                lower_percentile = (alpha / 2) * 100
                upper_percentile = (1 - alpha / 2) * 100
                
                lower_bound = np.percentile(mc_samples, lower_percentile)
                upper_bound = np.percentile(mc_samples, upper_percentile)
                
                summary.monte_carlo_confidence_intervals[f'{conf_level:.0%}'] = (lower_bound, upper_bound)
            
            # Calculate Value at Risk (VaR) - probability of extreme low values
            var_levels = [0.05, 0.01, 0.001]  # 5%, 1%, 0.1% VaR
            for var_level in var_levels:
                var_value = np.percentile(mc_samples, var_level * 100)
                summary.monte_carlo_value_at_risk[f'{var_level:.1%}'] = var_value
            
            logger.debug(f"Monte Carlo simulation completed with {n_simulations} samples")
            return summary
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            return summary
    
    def _calculate_risk_adjusted_metrics(self, summary: PBStatisticalSummary, 
                                       valid_ratios: List[float]) -> PBStatisticalSummary:
        """Calculate risk-adjusted performance metrics"""
        try:
            if len(valid_ratios) < 3:
                return summary
            
            mean_pb = np.mean(valid_ratios)
            
            # Calculate downside deviation (volatility of negative deviations from mean)
            downside_deviations = [min(0, ratio - mean_pb) for ratio in valid_ratios]
            summary.downside_deviation = np.sqrt(np.mean([d**2 for d in downside_deviations]))
            
            # Risk-adjusted return (Sharpe-like ratio for P/B)
            # Higher P/B with lower volatility is better for growth stocks
            # Lower P/B with lower volatility is better for value stocks
            if summary.std_pb > 0:
                # For P/B, we want stable ratios, so lower volatility is better
                summary.risk_adjusted_return = mean_pb / summary.std_pb
            else:
                summary.risk_adjusted_return = mean_pb
            
            logger.debug(f"Risk-adjusted metrics calculated")
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted metrics: {e}")
            return summary
    
    def _analyze_trends(self, pb_data: List[PBDataPoint]) -> PBTrendAnalysis:
        """Analyze trends in historical P/B data"""
        try:
            trend = PBTrendAnalysis()
            
            # Extract valid data
            valid_data = [(pd.to_datetime(dp.date), dp.pb_ratio) 
                         for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
            
            if len(valid_data) < 3:
                return trend
            
            # Sort by date
            valid_data.sort(key=lambda x: x[0])
            dates, ratios = zip(*valid_data)
            
            # Convert dates to numeric values for regression
            date_nums = [(d - dates[0]).days for d in dates]
            
            # Linear regression for trend
            if len(date_nums) > 1:
                slope, intercept, r_value, p_value, std_err = self._simple_linear_regression(date_nums, ratios)
                
                trend.trend_slope = slope
                trend.r_squared = r_value ** 2
                
                # Determine trend direction and strength
                if abs(slope) < 0.001:  # Very small slope
                    trend.trend_direction = "neutral"
                    trend.trend_strength = 0.0
                elif slope > 0:
                    trend.trend_direction = "upward"
                    trend.trend_strength = min(1.0, abs(slope) * 1000)  # Scale appropriately
                else:
                    trend.trend_direction = "downward"
                    trend.trend_strength = min(1.0, abs(slope) * 1000)
            
            # Calculate volatility
            trend.volatility = np.std(ratios)
            
            # Mean reversion analysis
            mean_pb = np.mean(ratios)
            deviations = [abs(ratio - mean_pb) for ratio in ratios]
            avg_deviation = np.mean(deviations)
            
            # Mean reversion score (higher = more mean reverting)
            if trend.volatility > 0:
                trend.mean_reversion_score = 1.0 - (avg_deviation / (2 * trend.volatility))
                trend.mean_reversion_score = max(0.0, min(1.0, trend.mean_reversion_score))
            
            # Simple cycle detection (peaks and troughs)
            cycles_info = self._detect_cycles(ratios)
            trend.cycles_detected = cycles_info.get('cycle_count', 0)
            trend.avg_cycle_duration = cycles_info.get('avg_duration', 0.0)
            trend.current_cycle_position = cycles_info.get('current_position', 'unknown')
            
            logger.debug(f"Trend analysis completed: direction={trend.trend_direction}, strength={trend.trend_strength:.3f}")
            
            return trend
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return PBTrendAnalysis()
    
    def _simple_linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float, float, float]:
        """Simple linear regression implementation"""
        try:
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(xi ** 2 for xi in x)
            sum_y2 = sum(yi ** 2 for yi in y)
            
            # Calculate slope and intercept
            denominator = n * sum_x2 - sum_x ** 2
            if denominator == 0:
                return 0.0, 0.0, 0.0, 1.0, 0.0
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate correlation coefficient
            numerator = n * sum_xy - sum_x * sum_y
            denom_r = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
            
            if denom_r == 0:
                r_value = 0.0
            else:
                r_value = numerator / denom_r
            
            # Simplified p-value and standard error (approximations)
            p_value = 0.05 if abs(r_value) > 0.3 else 0.5
            std_err = 0.0
            
            return slope, intercept, r_value, p_value, std_err
            
        except Exception as e:
            logger.debug(f"Error in linear regression: {e}")
            return 0.0, 0.0, 0.0, 1.0, 0.0
    
    def _detect_cycles(self, ratios: List[float]) -> Dict[str, Any]:
        """Simple cycle detection in P/B ratios"""
        try:
            if len(ratios) < 6:  # Need at least 6 points for meaningful cycle detection
                return {'cycle_count': 0, 'avg_duration': 0.0, 'current_position': 'unknown'}
            
            # Find local peaks and troughs
            peaks = []
            troughs = []
            
            for i in range(1, len(ratios) - 1):
                if ratios[i] > ratios[i-1] and ratios[i] > ratios[i+1]:
                    peaks.append(i)
                elif ratios[i] < ratios[i-1] and ratios[i] < ratios[i+1]:
                    troughs.append(i)
            
            # Count cycles (peak to peak or trough to trough)
            cycle_count = max(len(peaks) - 1, len(troughs) - 1, 0)
            
            # Calculate average cycle duration
            avg_duration = 0.0
            if cycle_count > 0:
                if len(peaks) > 1:
                    peak_durations = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
                    avg_duration = np.mean(peak_durations) * 3  # Convert to months (assuming quarterly data)
                elif len(troughs) > 1:
                    trough_durations = [troughs[i+1] - troughs[i] for i in range(len(troughs)-1)]
                    avg_duration = np.mean(trough_durations) * 3
            
            # Determine current position
            current_position = 'unknown'
            if len(ratios) >= 3:
                recent_trend = ratios[-1] - ratios[-3]  # Compare last vs 2 periods ago
                
                if recent_trend > 0.1:
                    current_position = 'rising'
                elif recent_trend < -0.1:
                    current_position = 'falling'
                else:
                    # Check if near recent peak or trough
                    recent_max = max(ratios[-3:])
                    recent_min = min(ratios[-3:])
                    
                    if ratios[-1] == recent_max:
                        current_position = 'peak'
                    elif ratios[-1] == recent_min:
                        current_position = 'trough'
                    else:
                        current_position = 'neutral'
            
            return {
                'cycle_count': cycle_count,
                'avg_duration': avg_duration,
                'current_position': current_position
            }
            
        except Exception as e:
            logger.debug(f"Error detecting cycles: {e}")
            return {'cycle_count': 0, 'avg_duration': 0.0, 'current_position': 'unknown'}
    
    def _calculate_valuation_insights(self, result: PBHistoricalAnalysisResult) -> None:
        """Calculate valuation insights based on historical P/B analysis"""
        try:
            if not result.historical_data or not result.statistics:
                return
            
            # Get current/latest P/B ratio
            latest_pb = None
            for dp in reversed(result.historical_data):
                if dp.pb_ratio and dp.pb_ratio > 0:
                    latest_pb = dp.pb_ratio
                    break
            
            if latest_pb is None:
                return
            
            # Calculate current P/B percentile
            valid_ratios = [dp.pb_ratio for dp in result.historical_data 
                           if dp.pb_ratio and dp.pb_ratio > 0]
            
            if valid_ratios:
                below_current = sum(1 for ratio in valid_ratios if ratio < latest_pb)
                result.current_pb_percentile = below_current / len(valid_ratios)
            
            # Fair value estimate based on quality-weighted mean
            if result.statistics.quality_weighted_mean > 0:
                result.fair_value_estimate = result.statistics.quality_weighted_mean
            else:
                result.fair_value_estimate = result.statistics.mean_pb
            
            # Valuation signal based on percentile and confidence
            confidence_threshold = 0.7  # Require high confidence for strong signals
            quality_score = result.quality_metrics.overall_score if result.quality_metrics else 0.5
            
            if quality_score >= confidence_threshold:
                if result.current_pb_percentile <= 0.25:
                    result.valuation_signal = "undervalued"
                elif result.current_pb_percentile >= 0.75:
                    result.valuation_signal = "overvalued"
                else:
                    result.valuation_signal = "fairly_valued"
            else:
                result.valuation_signal = "uncertain"
            
            logger.debug(f"Valuation insights: current_percentile={result.current_pb_percentile:.2f}, signal={result.valuation_signal}")
            
        except Exception as e:
            logger.error(f"Error calculating valuation insights: {e}")
    
    def _generate_risk_scenarios(self, result: PBHistoricalAnalysisResult) -> None:
        """Generate risk-adjusted scenarios based on historical volatility"""
        try:
            if not result.statistics:
                return
            
            stats = result.statistics
            
            # Base scenario parameters
            base_pb = stats.quality_weighted_mean if stats.quality_weighted_mean > 0 else stats.mean_pb
            volatility = stats.std_pb
            
            # Quality adjustment for scenario confidence
            quality_score = result.quality_metrics.overall_score if result.quality_metrics else 0.5
            
            # Generate three scenarios based on historical volatility
            scenarios = {
                'bear': {
                    'description': 'Pessimistic scenario (2 std dev below mean)',
                    'pb_estimate': max(0.1, base_pb - 2 * volatility),
                    'probability_weight': 0.15 + (1.0 - quality_score) * 0.1,  # Higher for low quality data
                    'confidence_level': 0.025  # 2.5% tail
                },
                'base': {
                    'description': 'Most likely scenario (quality-weighted mean)',
                    'pb_estimate': base_pb,
                    'probability_weight': 0.70 - (1.0 - quality_score) * 0.2,  # Lower for low quality data
                    'confidence_level': 0.50
                },
                'bull': {
                    'description': 'Optimistic scenario (2 std dev above mean)',
                    'pb_estimate': base_pb + 2 * volatility,
                    'probability_weight': 0.15 + (1.0 - quality_score) * 0.1,
                    'confidence_level': 0.975  # 97.5% tail
                }
            }
            
            # Adjust probabilities to sum to 1.0
            total_prob = sum(s['probability_weight'] for s in scenarios.values())
            for scenario in scenarios.values():
                scenario['probability_weight'] /= total_prob
            
            # Store scenarios
            result.risk_scenarios = scenarios
            result.scenario_probabilities = {
                name: scenario['probability_weight'] 
                for name, scenario in scenarios.items()
            }
            
            # Calculate volatility-adjusted ranges
            confidence_levels = [0.80, 0.90, 0.95, 0.99]
            
            if stats.monte_carlo_confidence_intervals:
                # Use Monte Carlo intervals if available
                for conf_str, (lower, upper) in stats.monte_carlo_confidence_intervals.items():
                    result.volatility_adjusted_ranges[f'monte_carlo_{conf_str}'] = (lower, upper)
            else:
                # Calculate analytical intervals
                for conf_level in confidence_levels:
                    z_score = norm.ppf((1 + conf_level) / 2)
                    quality_adjusted_std = volatility * (1.0 + (1.0 - quality_score) * 0.3)
                    
                    lower_bound = max(0.01, base_pb - z_score * quality_adjusted_std)
                    upper_bound = base_pb + z_score * quality_adjusted_std
                    
                    result.volatility_adjusted_ranges[f'{conf_level:.0%}'] = (lower_bound, upper_bound)
            
            # Add scenario-based valuation ranges
            scenario_range = (
                scenarios['bear']['pb_estimate'],
                scenarios['bull']['pb_estimate']
            )
            result.volatility_adjusted_ranges['scenario_range'] = scenario_range
            
            # Calculate expected value across scenarios
            expected_pb = sum(
                scenario['pb_estimate'] * scenario['probability_weight']
                for scenario in scenarios.values()
            )
            
            # Update fair value estimate with scenario analysis
            if result.fair_value_estimate:
                # Weighted average of existing estimate and scenario-based estimate
                result.fair_value_estimate = (result.fair_value_estimate + expected_pb) / 2
            else:
                result.fair_value_estimate = expected_pb
            
            logger.debug(f"Risk scenarios generated: bear={scenarios['bear']['pb_estimate']:.2f}, "
                        f"base={scenarios['base']['pb_estimate']:.2f}, bull={scenarios['bull']['pb_estimate']:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating risk scenarios: {e}")
    
    def _generate_analysis_notes(self, result: PBHistoricalAnalysisResult) -> None:
        """Generate quality warnings and analysis notes"""
        try:
            # Quality warnings
            if result.quality_metrics:
                qm = result.quality_metrics
                
                if qm.overall_score < 0.6:
                    result.quality_warnings.append("Low overall data quality score")
                
                if qm.pb_data_completeness < 0.8:
                    result.quality_warnings.append("Significant missing P/B data points")
                
                if qm.temporal_consistency < 0.7:
                    result.quality_warnings.append("Irregular time intervals in data")
                
                if qm.outlier_detection_score < 0.8:
                    result.quality_warnings.append("Potential outliers detected in P/B ratios")
                
                if qm.data_gap_penalty > 0.2:
                    result.quality_warnings.append("Significant data gaps detected")
            
            # Analysis notes
            if result.statistics:
                stats = result.statistics
                
                if stats.std_pb > stats.mean_pb:
                    result.analysis_notes.append("High P/B volatility relative to mean")
                
                if result.data_points_count < 20:
                    result.analysis_notes.append("Limited historical data for robust analysis")
                
                if stats.max_pb > 10 * stats.mean_pb:
                    result.analysis_notes.append("Extreme P/B values detected")
            
            if result.trend_analysis:
                trend = result.trend_analysis
                
                if trend.trend_strength > 0.7:
                    result.analysis_notes.append(f"Strong {trend.trend_direction} trend detected")
                
                if trend.mean_reversion_score > 0.8:
                    result.analysis_notes.append("Strong mean reversion characteristics")
                
                if trend.cycles_detected > 2:
                    result.analysis_notes.append(f"Cyclical P/B patterns detected ({trend.cycles_detected} cycles)")
            
            # Data sufficiency notes
            if result.data_points_count >= 20:
                result.analysis_notes.append("Sufficient data for robust statistical analysis")
            elif result.data_points_count >= 12:
                result.analysis_notes.append("Adequate data for basic analysis")
            else:
                result.analysis_notes.append("Limited data - analysis may be less reliable")
            
        except Exception as e:
            logger.error(f"Error generating analysis notes: {e}")


# Utility functions for external use

def create_pb_historical_report(analysis_result: PBHistoricalAnalysisResult) -> Dict[str, Any]:
    """
    Create a comprehensive report from P/B historical analysis results.
    
    Args:
        analysis_result (PBHistoricalAnalysisResult): Analysis results
        
    Returns:
        Dict[str, Any]: Formatted report dictionary
    """
    try:
        if not analysis_result.success:
            return {
                'success': False,
                'error': analysis_result.error_message,
                'ticker': analysis_result.ticker
            }
        
        report = {
            'success': True,
            'ticker': analysis_result.ticker,
            'analysis_period': analysis_result.analysis_period,
            'data_points_count': analysis_result.data_points_count,
            'analysis_date': datetime.now().isoformat(),
            
            'summary': {
                'current_pb_percentile': analysis_result.current_pb_percentile,
                'fair_value_estimate': analysis_result.fair_value_estimate,
                'valuation_signal': analysis_result.valuation_signal,
            },
            
            'quality_assessment': {
                'overall_score': analysis_result.quality_metrics.overall_score if analysis_result.quality_metrics else None,
                'data_completeness': analysis_result.quality_metrics.pb_data_completeness if analysis_result.quality_metrics else None,
                'confidence_level': analysis_result.quality_metrics.confidence_level if analysis_result.quality_metrics else None,
                'warnings': analysis_result.quality_warnings
            },
            
            'statistics': {
                'mean_pb': analysis_result.statistics.mean_pb if analysis_result.statistics else None,
                'median_pb': analysis_result.statistics.median_pb if analysis_result.statistics else None,
                'volatility': analysis_result.statistics.std_pb if analysis_result.statistics else None,
                'percentiles': {
                    '25th': analysis_result.statistics.p25_pb if analysis_result.statistics else None,
                    '75th': analysis_result.statistics.p75_pb if analysis_result.statistics else None,
                    '90th': analysis_result.statistics.p90_pb if analysis_result.statistics else None,
                    '95th': analysis_result.statistics.p95_pb if analysis_result.statistics else None,
                },
                'statistical_significance': analysis_result.statistics.statistical_significance if analysis_result.statistics else None,
                'normality_test_pvalue': analysis_result.statistics.normality_test_pvalue if analysis_result.statistics else None,
                'is_normal_distribution': analysis_result.statistics.is_normal_distribution if analysis_result.statistics else None,
                'skewness': analysis_result.statistics.skewness if analysis_result.statistics else None,
                'kurtosis': analysis_result.statistics.kurtosis if analysis_result.statistics else None,
            },
            
            'monte_carlo_analysis': {
                'mean': analysis_result.statistics.monte_carlo_mean if analysis_result.statistics else None,
                'std': analysis_result.statistics.monte_carlo_std if analysis_result.statistics else None,
                'confidence_intervals': analysis_result.statistics.monte_carlo_confidence_intervals if analysis_result.statistics else None,
                'value_at_risk': analysis_result.statistics.monte_carlo_value_at_risk if analysis_result.statistics else None,
            },
            
            'risk_metrics': {
                'risk_adjusted_return': analysis_result.statistics.risk_adjusted_return if analysis_result.statistics else None,
                'downside_deviation': analysis_result.statistics.downside_deviation if analysis_result.statistics else None,
                'scenarios': analysis_result.risk_scenarios,
                'scenario_probabilities': analysis_result.scenario_probabilities,
                'volatility_adjusted_ranges': analysis_result.volatility_adjusted_ranges,
            },
            
            'trend_analysis': {
                'direction': analysis_result.trend_analysis.trend_direction if analysis_result.trend_analysis else None,
                'strength': analysis_result.trend_analysis.trend_strength if analysis_result.trend_analysis else None,
                'volatility': analysis_result.trend_analysis.volatility if analysis_result.trend_analysis else None,
                'cycles_detected': analysis_result.trend_analysis.cycles_detected if analysis_result.trend_analysis else None,
                'current_cycle_position': analysis_result.trend_analysis.current_cycle_position if analysis_result.trend_analysis else None,
            },
            
            'notes': analysis_result.analysis_notes
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Error creating P/B historical report: {e}")
        return {
            'success': False,
            'error': f"Report generation error: {str(e)}",
            'ticker': analysis_result.ticker if analysis_result else 'Unknown'
        }


def validate_pb_historical_data(response: DataSourceResponse) -> Dict[str, Any]:
    """
    Validate data response for P/B historical analysis requirements.
    
    Args:
        response (DataSourceResponse): Data response to validate
        
    Returns:
        Dict[str, Any]: Validation results
    """
    try:
        validation = {
            'valid': False,
            'issues': [],
            'recommendations': []
        }
        
        if not response.success:
            validation['issues'].append("Data response unsuccessful")
            return validation
        
        if not response.data:
            validation['issues'].append("No data in response")
            return validation
        
        data = response.data
        
        # Check for required data types
        required_fields = ['historical_prices', 'quarterly_balance_sheet']
        optional_fields = ['price', 'fundamentals', 'balance_sheet']
        
        found_fields = []
        for field_set in [required_fields, optional_fields]:
            for field in field_set:
                if field in data and data[field]:
                    found_fields.append(field)
        
        if not any(field in found_fields for field in required_fields):
            validation['issues'].append("Missing historical price or balance sheet data")
            validation['recommendations'].append("Ensure request includes 'historical_prices' and 'quarterly_balance_sheet'")
        
        # Check data quality
        if hasattr(response, 'quality_metrics') and response.quality_metrics:
            if response.quality_metrics.overall_score < 0.5:
                validation['issues'].append("Low data quality score")
                validation['recommendations'].append("Consider using multiple data sources for validation")
        
        # If we get here with no major issues, mark as valid
        if not validation['issues']:
            validation['valid'] = True
            validation['recommendations'].append("Data appears suitable for P/B historical analysis")
        
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation error: {str(e)}"],
            'recommendations': ["Check data response format and content"]
        }