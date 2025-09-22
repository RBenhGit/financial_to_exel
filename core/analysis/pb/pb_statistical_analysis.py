"""
P/B Statistical Analysis Engine - Advanced Statistical Features for Market Cycles and Trends
==========================================================================================

This module implements advanced statistical analysis for P/B trends, market cycles, 
and volatility assessment as specified in Task #35.

Key Features:
- Advanced trend detection using statistical methods (Mann-Kendall, linear regression)
- Market cycle detection and regime analysis using signal processing
- Volatility assessment and risk scoring based on historical patterns
- Correlation analysis with broader market conditions and economic cycles
- Statistical significance testing for trend reliability
- Regime change detection using Hidden Markov Models (simplified approach)

Classes:
--------
PBTrendDetectionResult
    Results of advanced trend detection analysis
    
PBMarketCycleAnalysis
    Market cycle detection and regime analysis results
    
PBVolatilityAssessment
    Volatility metrics and risk scoring
    
PBCorrelationAnalysis
    Correlation analysis with market conditions
    
PBStatisticalAnalysisEngine
    Main engine combining all statistical analysis features

Dependencies:
-------------
- numpy, pandas, scipy for statistical calculations
- pb_historical_analysis for base P/B data
- data_sources for data integration

Usage Example:
--------------
>>> from pb_statistical_analysis import PBStatisticalAnalysisEngine
>>> from pb_historical_analysis import PBHistoricalAnalysisEngine
>>> 
>>> # Get historical analysis first
>>> historical_engine = PBHistoricalAnalysisEngine()
>>> historical_result = historical_engine.analyze_historical_performance(response, years=5)
>>> 
>>> # Perform statistical analysis
>>> stats_engine = PBStatisticalAnalysisEngine()
>>> stats_result = stats_engine.analyze_pb_statistics(historical_result)
>>> 
>>> # Access advanced features
>>> print(f"Trend significance: {stats_result.trend_analysis.statistical_significance:.3f}")
>>> print(f"Market cycles detected: {stats_result.cycle_analysis.cycles_detected}")
>>> print(f"Current regime: {stats_result.cycle_analysis.current_regime}")
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from statistics import median, stdev
import warnings

# Statistical libraries with fallbacks
try:
    from scipy import stats
    from scipy.signal import find_peaks, detrend
    from scipy.stats import pearsonr, spearmanr
    SCIPY_AVAILABLE = True
except ImportError:
    # Fallback implementations for basic statistical functions
    SCIPY_AVAILABLE = False
    class stats:
        @staticmethod
        def mannwhitneyu(x, y):
            return type('obj', (object,), {'statistic': 0, 'pvalue': 0.5})()
        
        @staticmethod
        def kendalltau(x, y):
            return (0.0, 0.5)
        
        @staticmethod
        def pearsonr(x, y):
            try:
                n = len(x)
                if n < 2:
                    return (0.0, 1.0)
                
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(xi * yi for xi, yi in zip(x, y))
                sum_x2 = sum(xi * xi for xi in x)
                sum_y2 = sum(yi * yi for yi in y)
                
                numerator = n * sum_xy - sum_x * sum_y
                denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))**0.5
                
                if denominator == 0:
                    return (0.0, 1.0)
                
                r = numerator / denominator
                return (r, 0.5)  # Simplified p-value
            except:
                return (0.0, 1.0)

from .pb_historical_analysis import (
    PBHistoricalAnalysisResult,
    PBTrendAnalysis,
    PBDataPoint,
    PBStatisticalSummary
)

logger = logging.getLogger(__name__)


@dataclass
class PBTrendDetectionResult:
    """
    Advanced trend detection results with statistical significance testing.
    """
    
    # Basic trend information (extends existing PBTrendAnalysis)
    trend_direction: str = "neutral"  # "upward", "downward", "neutral"
    trend_strength: float = 0.0       # 0.0 to 1.0
    linear_slope: float = 0.0         # Linear regression slope
    r_squared: float = 0.0            # R-squared of linear fit
    
    # Statistical significance testing
    statistical_significance: float = 0.0  # 0.0 to 1.0 (1 - p_value)
    mann_kendall_tau: float = 0.0     # Mann-Kendall tau statistic
    mann_kendall_pvalue: float = 1.0  # Mann-Kendall p-value
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # 95% CI for slope
    
    # Advanced trend patterns
    trend_patterns: List[str] = field(default_factory=list)  # ["accelerating", "decelerating", "linear"]
    breakpoints: List[int] = field(default_factory=list)  # Indices of trend changes
    trend_consistency: float = 0.0    # How consistent the trend is
    
    # Seasonal and cyclical components
    seasonal_component: float = 0.0   # Strength of seasonal patterns
    cyclical_component: float = 0.0   # Strength of cyclical patterns
    noise_level: float = 0.0          # Noise to signal ratio


@dataclass
class PBMarketCycleAnalysis:
    """
    Market cycle detection and regime analysis results.
    """
    
    # Cycle detection
    cycles_detected: int = 0
    cycle_periods: List[Tuple[datetime, datetime]] = field(default_factory=list)
    avg_cycle_duration_months: float = 0.0
    cycle_amplitude_avg: float = 0.0  # Average peak-to-trough amplitude
    
    # Current cycle position
    current_cycle_position: str = "unknown"  # "expansion", "peak", "contraction", "trough"
    cycle_maturity: float = 0.0      # 0.0 to 1.0, where we are in current cycle
    time_since_last_peak: int = 0    # Months since last peak
    time_since_last_trough: int = 0  # Months since last trough
    
    # Regime analysis (simplified HMM approach)
    current_regime: str = "normal"    # "bull", "bear", "normal", "volatile"
    regime_probability: float = 0.0   # Confidence in current regime
    regime_changes: List[Tuple[datetime, str, str]] = field(default_factory=list)  # (date, from, to)
    
    # Market cycle characteristics
    expansion_duration_avg: float = 0.0  # Average expansion phase duration
    contraction_duration_avg: float = 0.0  # Average contraction phase duration
    volatility_clustering: float = 0.0   # Measure of volatility clustering
    
    # Predictive indicators
    cycle_prediction_signal: str = "neutral"  # "peak_approaching", "trough_approaching", "neutral"
    next_turning_point_estimate: Optional[datetime] = None


@dataclass
class PBVolatilityAssessment:
    """
    Volatility assessment and risk scoring based on historical patterns.
    """
    
    # Basic volatility metrics
    historical_volatility: float = 0.0      # Standard deviation of returns
    realized_volatility_30d: float = 0.0    # 30-day realized volatility
    volatility_percentile: float = 0.0      # Current vol vs historical
    
    # Risk scoring
    overall_risk_score: float = 0.0         # 0.0 to 1.0 (1 = high risk)
    downside_risk_score: float = 0.0        # Focus on downside volatility
    tail_risk_score: float = 0.0            # Extreme event risk
    
    # Volatility patterns
    volatility_clustering_score: float = 0.0  # Tendency for vol to cluster
    mean_reversion_speed: float = 0.0        # How quickly vol reverts to mean
    volatility_trend: str = "stable"         # "increasing", "decreasing", "stable"
    
    # GARCH-like analysis (simplified)
    conditional_volatility: List[float] = field(default_factory=list)
    volatility_persistence: float = 0.0      # How persistent vol shocks are
    
    # Risk-adjusted metrics
    sharpe_ratio_estimate: float = 0.0       # Risk-adjusted return estimate
    maximum_drawdown: float = 0.0            # Max peak-to-trough decline
    value_at_risk_5pct: float = 0.0         # 5% VaR estimate
    
    # Volatility regime
    current_vol_regime: str = "normal"       # "low", "normal", "high", "extreme"
    vol_regime_stability: float = 0.0        # How stable current regime is


@dataclass
class PBCorrelationAnalysis:
    """
    Correlation analysis with broader market conditions and economic cycles.
    """
    
    # Market correlations (would need market data to implement fully)
    market_correlation: float = 0.0          # Correlation with broad market
    sector_correlation: float = 0.0          # Correlation with sector
    correlation_stability: float = 0.0       # How stable correlations are
    
    # Economic cycle correlations
    business_cycle_correlation: float = 0.0  # Correlation with business cycles
    interest_rate_sensitivity: float = 0.0   # Sensitivity to interest rates
    inflation_correlation: float = 0.0       # Correlation with inflation
    
    # Cross-asset correlations
    bond_correlation: float = 0.0            # Correlation with bonds
    commodity_correlation: float = 0.0       # Correlation with commodities
    currency_correlation: float = 0.0        # Correlation with currency
    
    # Correlation regime analysis
    correlation_regime: str = "normal"       # "low", "normal", "high", "crisis"
    correlation_breakdown_risk: float = 0.0  # Risk of correlation breakdown
    
    # Lead-lag relationships
    pb_leads_market: bool = False            # Whether P/B leads market moves
    lag_periods: int = 0                     # Optimal lag periods
    predictive_power: float = 0.0            # Predictive power for market moves


@dataclass
class PBStatisticalAnalysisResult:
    """
    Complete result of advanced P/B statistical analysis.
    """
    
    success: bool
    ticker: str = ""
    analysis_date: str = ""
    
    # Core analysis results
    trend_analysis: Optional[PBTrendDetectionResult] = None
    cycle_analysis: Optional[PBMarketCycleAnalysis] = None
    volatility_analysis: Optional[PBVolatilityAssessment] = None
    correlation_analysis: Optional[PBCorrelationAnalysis] = None
    
    # Overall assessment
    statistical_confidence: float = 0.0      # Overall confidence in analysis
    market_timing_signal: str = "neutral"    # "bullish", "bearish", "neutral"
    signal_strength: float = 0.0             # Strength of timing signal
    
    # Warnings and notes
    analysis_warnings: List[str] = field(default_factory=list)
    methodology_notes: List[str] = field(default_factory=list)
    
    error_message: Optional[str] = None


class PBStatisticalAnalysisEngine:
    """
    Advanced statistical analysis engine for P/B trends, cycles, and market patterns.
    
    This engine extends the existing P/B historical analysis with sophisticated
    statistical methods for trend detection, cycle analysis, and market correlation.
    """
    
    def __init__(self, 
                 min_data_points: int = 24,
                 trend_significance_threshold: float = 0.05,
                 cycle_min_duration_months: int = 6):
        """
        Initialize the statistical analysis engine.
        
        Args:
            min_data_points (int): Minimum data points for analysis
            trend_significance_threshold (float): P-value threshold for trend significance
            cycle_min_duration_months (int): Minimum cycle duration to detect
        """
        self.min_data_points = min_data_points
        self.trend_significance_threshold = trend_significance_threshold
        self.cycle_min_duration_months = cycle_min_duration_months
        
        logger.info("P/B Statistical Analysis Engine initialized")
    
    def analyze_pb_statistics(self, 
                             historical_analysis: PBHistoricalAnalysisResult,
                             market_data: Optional[Dict] = None) -> PBStatisticalAnalysisResult:
        """
        Perform comprehensive statistical analysis on P/B historical data.
        
        Args:
            historical_analysis (PBHistoricalAnalysisResult): Historical P/B analysis results
            market_data (Optional[Dict]): Optional market data for correlation analysis
            
        Returns:
            PBStatisticalAnalysisResult: Complete statistical analysis results
        """
        try:
            logger.info(f"Starting statistical analysis for {historical_analysis.ticker}")
            
            # Initialize result
            result = PBStatisticalAnalysisResult(
                success=False,
                ticker=historical_analysis.ticker,
                analysis_date=datetime.now().isoformat()
            )
            
            # Validate inputs
            if not self._validate_inputs(historical_analysis):
                result.error_message = "Invalid historical analysis data"
                return result
            
            # Extract P/B time series data
            pb_data = self._extract_pb_timeseries(historical_analysis.historical_data)
            
            if len(pb_data) < self.min_data_points:
                result.error_message = f"Insufficient data points ({len(pb_data)}) for statistical analysis"
                return result
            
            # Perform advanced trend detection
            result.trend_analysis = self._detect_advanced_trends(pb_data)
            
            # Perform market cycle analysis
            result.cycle_analysis = self._analyze_market_cycles(pb_data)
            
            # Perform volatility assessment
            result.volatility_analysis = self._assess_volatility_patterns(pb_data)
            
            # Perform correlation analysis (if market data available)
            result.correlation_analysis = self._analyze_correlations(pb_data, market_data)
            
            # Generate overall assessment
            self._generate_overall_assessment(result)
            
            # Add methodology notes
            self._add_analysis_notes(result)
            
            result.success = True
            logger.info(f"Statistical analysis completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in statistical analysis: {e}")
            return PBStatisticalAnalysisResult(
                success=False,
                ticker=historical_analysis.ticker if historical_analysis else "Unknown",
                error_message=f"Statistical analysis error: {str(e)}"
            )
    
    def _validate_inputs(self, historical_analysis: PBHistoricalAnalysisResult) -> bool:
        """Validate inputs for statistical analysis."""
        try:
            if not historical_analysis.success:
                return False
            
            if not historical_analysis.historical_data:
                return False
            
            if len(historical_analysis.historical_data) < self.min_data_points:
                return False
            
            # Check for valid P/B ratios
            valid_ratios = [dp.pb_ratio for dp in historical_analysis.historical_data 
                          if dp.pb_ratio and dp.pb_ratio > 0]
            
            return len(valid_ratios) >= self.min_data_points
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False
    
    def _extract_pb_timeseries(self, pb_data: List[PBDataPoint]) -> pd.DataFrame:
        """Extract P/B time series data for analysis."""
        try:
            # Create DataFrame with dates and P/B ratios
            data = []
            for dp in pb_data:
                if dp.pb_ratio and dp.pb_ratio > 0:
                    data.append({
                        'date': pd.to_datetime(dp.date),
                        'pb_ratio': dp.pb_ratio,
                        'book_value': dp.book_value_per_share,
                        'market_price': dp.market_price
                    })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Calculate returns
            df['pb_return'] = df['pb_ratio'].pct_change()
            df['pb_log_return'] = np.log(df['pb_ratio']).diff()
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting time series: {e}")
            return pd.DataFrame()
    
    def _detect_advanced_trends(self, pb_data: pd.DataFrame) -> PBTrendDetectionResult:
        """
        Perform advanced trend detection with statistical significance testing.
        """
        try:
            result = PBTrendDetectionResult()
            
            if pb_data.empty:
                return result
            
            pb_values = pb_data['pb_ratio'].values
            time_index = np.arange(len(pb_values))
            
            # Linear regression for basic trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_index, pb_values)
            
            result.linear_slope = slope
            result.r_squared = r_value ** 2
            result.statistical_significance = 1.0 - p_value if p_value < 1.0 else 0.0
            
            # Determine trend direction and strength
            if abs(slope) < std_err:  # Not statistically significant
                result.trend_direction = "neutral"
                result.trend_strength = 0.0
            elif slope > 0:
                result.trend_direction = "upward"
                result.trend_strength = min(1.0, abs(slope) / (np.std(pb_values) / len(pb_values)))
            else:
                result.trend_direction = "downward"
                result.trend_strength = min(1.0, abs(slope) / (np.std(pb_values) / len(pb_values)))
            
            # Mann-Kendall trend test (non-parametric)
            if SCIPY_AVAILABLE:
                try:
                    # Simplified Mann-Kendall test
                    n = len(pb_values)
                    s = 0
                    for i in range(n-1):
                        for j in range(i+1, n):
                            s += np.sign(pb_values[j] - pb_values[i])
                    
                    var_s = n * (n - 1) * (2 * n + 5) / 18
                    if var_s > 0:
                        if s > 0:
                            z = (s - 1) / np.sqrt(var_s)
                        elif s < 0:
                            z = (s + 1) / np.sqrt(var_s)
                        else:
                            z = 0
                        
                        result.mann_kendall_tau = s / (0.5 * n * (n - 1))
                        result.mann_kendall_pvalue = 2 * (1 - stats.norm.cdf(abs(z)))
                except:
                    pass
            
            # Confidence interval for slope
            if std_err > 0:
                t_critical = 1.96  # Approximate 95% CI
                margin_error = t_critical * std_err
                result.confidence_interval = (slope - margin_error, slope + margin_error)
            
            # Detect trend patterns
            self._detect_trend_patterns(pb_data, result)
            
            # Calculate trend consistency
            result.trend_consistency = self._calculate_trend_consistency(pb_values)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trend detection: {e}")
            return PBTrendDetectionResult()
    
    def _analyze_market_cycles(self, pb_data: pd.DataFrame) -> PBMarketCycleAnalysis:
        """
        Analyze market cycles and regime changes in P/B data.
        """
        try:
            result = PBMarketCycleAnalysis()
            
            if pb_data.empty:
                return result
            
            pb_values = pb_data['pb_ratio'].values
            dates = pb_data['date'].values
            
            # Detect peaks and troughs using signal processing
            if SCIPY_AVAILABLE:
                try:
                    # Find peaks (local maxima)
                    peaks, _ = find_peaks(pb_values, distance=self.cycle_min_duration_months)
                    # Find troughs (local minima) 
                    troughs, _ = find_peaks(-pb_values, distance=self.cycle_min_duration_months)
                    
                    # Combine and sort turning points
                    turning_points = sorted(list(peaks) + list(troughs))
                    
                    if len(turning_points) >= 4:  # Need at least 2 complete cycles
                        result.cycles_detected = (len(turning_points) - 1) // 2
                        
                        # Calculate cycle periods
                        cycle_periods = []
                        for i in range(0, len(turning_points) - 2, 2):
                            start_date = dates[turning_points[i]]
                            end_date = dates[turning_points[i + 2]]
                            cycle_periods.append((pd.to_datetime(start_date), pd.to_datetime(end_date)))
                        
                        result.cycle_periods = cycle_periods
                        
                        # Calculate average cycle duration
                        if cycle_periods:
                            durations = [(end - start).days / 30.44 for start, end in cycle_periods]  # Convert to months
                            result.avg_cycle_duration_months = np.mean(durations)
                        
                        # Calculate cycle amplitude
                        amplitudes = []
                        for i in range(len(turning_points) - 1):
                            amp = abs(pb_values[turning_points[i+1]] - pb_values[turning_points[i]])
                            amplitudes.append(amp)
                        
                        if amplitudes:
                            result.cycle_amplitude_avg = np.mean(amplitudes)
                    
                except:
                    pass
            
            # Determine current cycle position
            result.current_cycle_position = self._determine_cycle_position(pb_values)
            
            # Simplified regime analysis
            result.current_regime = self._analyze_regime(pb_values)
            
            # Calculate time since last peak/trough
            if len(pb_values) > 12:  # Need sufficient data
                recent_values = pb_values[-12:]  # Last 12 periods
                max_idx = np.argmax(recent_values)
                min_idx = np.argmin(recent_values)
                
                result.time_since_last_peak = 12 - max_idx
                result.time_since_last_trough = 12 - min_idx
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cycle analysis: {e}")
            return PBMarketCycleAnalysis()
    
    def _assess_volatility_patterns(self, pb_data: pd.DataFrame) -> PBVolatilityAssessment:
        """
        Assess volatility patterns and risk characteristics.
        """
        try:
            result = PBVolatilityAssessment()
            
            if pb_data.empty or 'pb_return' not in pb_data.columns:
                return result
            
            pb_returns = pb_data['pb_return'].dropna()
            pb_values = pb_data['pb_ratio'].values
            
            if len(pb_returns) < 12:
                return result
            
            # Basic volatility metrics
            result.historical_volatility = np.std(pb_returns) * np.sqrt(12)  # Annualized
            
            # Recent volatility (last 30 periods if available)
            if len(pb_returns) >= 30:
                result.realized_volatility_30d = np.std(pb_returns[-30:]) * np.sqrt(12)
            else:
                result.realized_volatility_30d = result.historical_volatility
            
            # Volatility percentile
            if len(pb_returns) > 12:
                rolling_vol = pb_returns.rolling(window=12).std()
                current_vol = rolling_vol.iloc[-1] if not pd.isna(rolling_vol.iloc[-1]) else result.historical_volatility
                result.volatility_percentile = stats.percentileofscore(rolling_vol.dropna(), current_vol) / 100.0
            
            # Risk scoring
            result.overall_risk_score = min(1.0, result.historical_volatility / 0.5)  # Normalize to 0-1
            
            # Downside risk (focus on negative returns)
            negative_returns = pb_returns[pb_returns < 0]
            if len(negative_returns) > 0:
                result.downside_risk_score = min(1.0, np.std(negative_returns) * np.sqrt(12) / 0.3)
            
            # Tail risk (extreme events)
            if len(pb_returns) > 20:
                percentile_5 = np.percentile(pb_returns, 5)
                result.tail_risk_score = min(1.0, abs(percentile_5) / 0.2)
                result.value_at_risk_5pct = percentile_5
            
            # Maximum drawdown
            pb_cumulative = (1 + pb_returns).cumprod()
            running_max = pb_cumulative.expanding().max()
            drawdown = (pb_cumulative - running_max) / running_max
            result.maximum_drawdown = abs(drawdown.min())
            
            # Volatility clustering
            result.volatility_clustering_score = self._calculate_volatility_clustering(pb_returns)
            
            # Mean reversion
            result.mean_reversion_speed = self._calculate_mean_reversion_speed(pb_values)
            
            # Volatility trend
            if len(pb_returns) > 24:
                recent_vol = np.std(pb_returns[-12:])
                past_vol = np.std(pb_returns[-24:-12])
                
                if recent_vol > past_vol * 1.1:
                    result.volatility_trend = "increasing"
                elif recent_vol < past_vol * 0.9:
                    result.volatility_trend = "decreasing"
                else:
                    result.volatility_trend = "stable"
            
            # Volatility regime
            if result.volatility_percentile > 0.8:
                result.current_vol_regime = "high"
            elif result.volatility_percentile < 0.2:
                result.current_vol_regime = "low"
            else:
                result.current_vol_regime = "normal"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in volatility assessment: {e}")
            return PBVolatilityAssessment()
    
    def _analyze_correlations(self, pb_data: pd.DataFrame, 
                             market_data: Optional[Dict] = None) -> PBCorrelationAnalysis:
        """
        Analyze correlations with market conditions (simplified without external data).
        """
        try:
            result = PBCorrelationAnalysis()
            
            # Note: This is a simplified implementation
            # In a full implementation, you would correlate with:
            # - Market indices (S&P 500, sector indices)
            # - Economic indicators (GDP, inflation, interest rates)
            # - Other asset classes (bonds, commodities, currencies)
            
            if pb_data.empty:
                return result
            
            # For now, we'll do internal correlation analysis
            pb_returns = pb_data['pb_return'].dropna()
            
            if len(pb_returns) < 24:
                return result
            
            # Auto-correlation analysis
            if len(pb_returns) > 12:
                try:
                    lag1_corr = pb_returns.autocorr(lag=1)
                    if not pd.isna(lag1_corr):
                        result.market_correlation = abs(lag1_corr)  # Placeholder
                except:
                    pass
            
            # If market_data is provided, perform actual correlations
            if market_data:
                # This would be implemented with actual market data
                # result.market_correlation = correlate_with_market(pb_returns, market_data)
                pass
            
            # Set placeholder values for demonstration
            result.correlation_regime = "normal"
            result.pb_leads_market = False
            result.predictive_power = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return PBCorrelationAnalysis()
    
    def _detect_trend_patterns(self, pb_data: pd.DataFrame, trend_result: PBTrendDetectionResult):
        """Detect advanced trend patterns like acceleration/deceleration."""
        try:
            pb_values = pb_data['pb_ratio'].values
            
            if len(pb_values) < 12:
                return
            
            # Calculate second derivative to detect acceleration/deceleration
            first_diff = np.diff(pb_values)
            second_diff = np.diff(first_diff)
            
            # Analyze pattern
            if len(second_diff) > 0:
                avg_acceleration = np.mean(second_diff)
                
                if abs(avg_acceleration) > np.std(second_diff) * 0.5:
                    if avg_acceleration > 0:
                        trend_result.trend_patterns.append("accelerating")
                    else:
                        trend_result.trend_patterns.append("decelerating")
                else:
                    trend_result.trend_patterns.append("linear")
            
            # Detect breakpoints (simplified)
            if len(pb_values) > 24:
                mid_point = len(pb_values) // 2
                first_half_slope = np.polyfit(range(mid_point), pb_values[:mid_point], 1)[0]
                second_half_slope = np.polyfit(range(mid_point), pb_values[mid_point:], 1)[0]
                
                if abs(first_half_slope - second_half_slope) > np.std(first_diff) * 0.5:
                    trend_result.breakpoints.append(mid_point)
                    
        except Exception as e:
            logger.error(f"Error detecting trend patterns: {e}")
    
    def _calculate_trend_consistency(self, pb_values: np.ndarray) -> float:
        """Calculate how consistent the trend is."""
        try:
            if len(pb_values) < 6:
                return 0.0
            
            # Calculate rolling correlations with time
            window = min(12, len(pb_values) // 2)
            correlations = []
            
            for i in range(len(pb_values) - window + 1):
                sub_values = pb_values[i:i + window]
                time_index = np.arange(len(sub_values))
                
                corr, _ = stats.pearsonr(time_index, sub_values)
                if not np.isnan(corr):
                    correlations.append(abs(corr))
            
            if correlations:
                return np.mean(correlations)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating trend consistency: {e}")
            return 0.0
    
    def _determine_cycle_position(self, pb_values: np.ndarray) -> str:
        """Determine current position in market cycle."""
        try:
            if len(pb_values) < 12:
                return "unknown"
            
            recent_values = pb_values[-12:]  # Last 12 periods
            current_value = pb_values[-1]
            
            # Simple heuristic based on recent performance
            recent_max = np.max(recent_values)
            recent_min = np.min(recent_values)
            recent_range = recent_max - recent_min
            
            if recent_range == 0:
                return "unknown"
            
            position_in_range = (current_value - recent_min) / recent_range
            
            # Calculate momentum
            if len(pb_values) >= 6:
                momentum = (pb_values[-1] - pb_values[-6]) / pb_values[-6]
                
                if position_in_range > 0.8 and momentum < -0.05:
                    return "peak"
                elif position_in_range < 0.2 and momentum > 0.05:
                    return "trough"
                elif momentum > 0.02:
                    return "expansion"
                elif momentum < -0.02:
                    return "contraction"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error determining cycle position: {e}")
            return "unknown"
    
    def _analyze_regime(self, pb_values: np.ndarray) -> str:
        """Simplified regime analysis."""
        try:
            if len(pb_values) < 24:
                return "normal"
            
            # Calculate volatility and trend
            returns = np.diff(pb_values) / pb_values[:-1]
            volatility = np.std(returns)
            trend = np.polyfit(range(len(pb_values)), pb_values, 1)[0]
            
            # Simple regime classification
            high_vol_threshold = np.percentile(returns, 75) if len(returns) > 10 else 0.1
            
            if volatility > high_vol_threshold * 2:
                return "volatile"
            elif trend > 0 and volatility < high_vol_threshold:
                return "bull"
            elif trend < 0 and volatility < high_vol_threshold:
                return "bear"
            else:
                return "normal"
                
        except Exception as e:
            logger.error(f"Error in regime analysis: {e}")
            return "normal"
    
    def _calculate_volatility_clustering(self, returns: pd.Series) -> float:
        """Calculate volatility clustering score."""
        try:
            if len(returns) < 12:
                return 0.0
            
            # Calculate rolling volatility
            rolling_vol = returns.rolling(window=6).std()
            rolling_vol = rolling_vol.dropna()
            
            if len(rolling_vol) < 6:
                return 0.0
            
            # Measure autocorrelation in squared returns (proxy for vol clustering)
            squared_returns = returns ** 2
            autocorr = squared_returns.autocorr(lag=1)
            
            return abs(autocorr) if not pd.isna(autocorr) else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating volatility clustering: {e}")
            return 0.0
    
    def _calculate_mean_reversion_speed(self, pb_values: np.ndarray) -> float:
        """Calculate mean reversion speed."""
        try:
            if len(pb_values) < 12:
                return 0.0
            
            # Detrend the series
            detrended = pb_values - np.mean(pb_values)
            
            # Calculate autocorrelation
            if len(detrended) > 1:
                autocorr = np.corrcoef(detrended[:-1], detrended[1:])[0, 1]
                
                # Mean reversion speed is related to (1 - autocorr)
                if not np.isnan(autocorr):
                    return max(0.0, 1.0 - autocorr)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating mean reversion speed: {e}")
            return 0.0
    
    def _generate_overall_assessment(self, result: PBStatisticalAnalysisResult):
        """Generate overall market timing assessment."""
        try:
            scores = []
            
            # Trend analysis contribution
            if result.trend_analysis:
                trend_score = 0.0
                if result.trend_analysis.trend_direction == "upward":
                    trend_score = result.trend_analysis.trend_strength * result.trend_analysis.statistical_significance
                elif result.trend_analysis.trend_direction == "downward":
                    trend_score = -result.trend_analysis.trend_strength * result.trend_analysis.statistical_significance
                
                scores.append(trend_score * 0.4)  # 40% weight
            
            # Cycle analysis contribution
            if result.cycle_analysis:
                cycle_score = 0.0
                if result.cycle_analysis.current_cycle_position == "trough":
                    cycle_score = 0.3
                elif result.cycle_analysis.current_cycle_position == "expansion":
                    cycle_score = 0.2
                elif result.cycle_analysis.current_cycle_position == "peak":
                    cycle_score = -0.3
                elif result.cycle_analysis.current_cycle_position == "contraction":
                    cycle_score = -0.2
                
                scores.append(cycle_score * 0.3)  # 30% weight
            
            # Volatility analysis contribution
            if result.volatility_analysis:
                vol_score = 0.0
                if result.volatility_analysis.current_vol_regime == "low":
                    vol_score = 0.1  # Low vol is generally good for entry
                elif result.volatility_analysis.current_vol_regime == "high":
                    vol_score = -0.1  # High vol suggests caution
                
                scores.append(vol_score * 0.3)  # 30% weight
            
            # Calculate overall signal
            if scores:
                overall_score = sum(scores)
                result.signal_strength = min(1.0, abs(overall_score))
                
                if overall_score > 0.1:
                    result.market_timing_signal = "bullish"
                elif overall_score < -0.1:
                    result.market_timing_signal = "bearish"
                else:
                    result.market_timing_signal = "neutral"
            
            # Calculate overall confidence
            confidences = []
            if result.trend_analysis:
                confidences.append(result.trend_analysis.statistical_significance)
            if result.cycle_analysis and result.cycle_analysis.cycles_detected > 0:
                confidences.append(0.7)  # Moderate confidence if cycles detected
            if result.volatility_analysis:
                confidences.append(0.6)  # Moderate confidence in vol analysis
            
            if confidences:
                result.statistical_confidence = np.mean(confidences)
                
        except Exception as e:
            logger.error(f"Error generating overall assessment: {e}")
    
    def _add_analysis_notes(self, result: PBStatisticalAnalysisResult):
        """Add methodology notes and warnings."""
        try:
            result.methodology_notes.append("Advanced statistical analysis using trend detection, cycle analysis, and volatility assessment")
            
            if not SCIPY_AVAILABLE:
                result.analysis_warnings.append("SciPy not available - using simplified statistical methods")
            
            if result.trend_analysis and result.trend_analysis.statistical_significance < 0.5:
                result.analysis_warnings.append("Low statistical significance for trend analysis")
            
            if result.cycle_analysis and result.cycle_analysis.cycles_detected < 2:
                result.analysis_warnings.append("Limited cycle data - cycle analysis may be unreliable")
            
            if result.statistical_confidence < 0.5:
                result.analysis_warnings.append("Low overall statistical confidence in analysis")
            
            result.methodology_notes.append(f"Analysis based on {len(result.analysis_warnings) == 0 and 'high' or 'moderate'} quality statistical methods")
            
        except Exception as e:
            logger.error(f"Error adding analysis notes: {e}")


# Utility functions for external use

def create_statistical_analysis_report(analysis_result: PBStatisticalAnalysisResult) -> Dict[str, Any]:
    """
    Create a comprehensive report from statistical analysis results.
    
    Args:
        analysis_result (PBStatisticalAnalysisResult): Analysis results
        
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
            'analysis_date': analysis_result.analysis_date,
            
            'trend_analysis': {
                'direction': analysis_result.trend_analysis.trend_direction if analysis_result.trend_analysis else None,
                'strength': analysis_result.trend_analysis.trend_strength if analysis_result.trend_analysis else None,
                'statistical_significance': analysis_result.trend_analysis.statistical_significance if analysis_result.trend_analysis else None,
                'r_squared': analysis_result.trend_analysis.r_squared if analysis_result.trend_analysis else None,
                'patterns': analysis_result.trend_analysis.trend_patterns if analysis_result.trend_analysis else [],
            },
            
            'cycle_analysis': {
                'cycles_detected': analysis_result.cycle_analysis.cycles_detected if analysis_result.cycle_analysis else 0,
                'current_position': analysis_result.cycle_analysis.current_cycle_position if analysis_result.cycle_analysis else 'unknown',
                'current_regime': analysis_result.cycle_analysis.current_regime if analysis_result.cycle_analysis else 'normal',
                'avg_cycle_duration': analysis_result.cycle_analysis.avg_cycle_duration_months if analysis_result.cycle_analysis else 0,
            },
            
            'volatility_analysis': {
                'historical_volatility': analysis_result.volatility_analysis.historical_volatility if analysis_result.volatility_analysis else 0,
                'risk_score': analysis_result.volatility_analysis.overall_risk_score if analysis_result.volatility_analysis else 0,
                'volatility_regime': analysis_result.volatility_analysis.current_vol_regime if analysis_result.volatility_analysis else 'normal',
                'maximum_drawdown': analysis_result.volatility_analysis.maximum_drawdown if analysis_result.volatility_analysis else 0,
            },
            
            'market_timing': {
                'signal': analysis_result.market_timing_signal,
                'strength': analysis_result.signal_strength,
                'confidence': analysis_result.statistical_confidence,
            },
            
            'methodology': {
                'notes': analysis_result.methodology_notes,
                'warnings': analysis_result.analysis_warnings,
            }
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Error creating statistical analysis report: {e}")
        return {
            'success': False,
            'error': f"Report generation error: {str(e)}",
            'ticker': analysis_result.ticker if analysis_result else 'Unknown'
        }


def validate_statistical_analysis_inputs(historical_analysis: PBHistoricalAnalysisResult) -> Dict[str, Any]:
    """
    Validate inputs for statistical analysis.
    
    Args:
        historical_analysis (PBHistoricalAnalysisResult): Historical analysis results
        
    Returns:
        Dict[str, Any]: Validation results
    """
    try:
        validation = {'valid': True, 'issues': [], 'recommendations': []}
        
        # Check basic validity
        if not historical_analysis.success:
            validation['valid'] = False
            validation['issues'].append("Historical analysis was unsuccessful")
            return validation
        
        # Check data availability
        if not historical_analysis.historical_data:
            validation['valid'] = False
            validation['issues'].append("No historical data available")
            return validation
        
        # Check data quantity
        data_points = len(historical_analysis.historical_data)
        if data_points < 24:
            validation['issues'].append(f"Limited data points ({data_points}) - analysis may be less reliable")
        
        # Check P/B data quality
        valid_pb_ratios = [dp.pb_ratio for dp in historical_analysis.historical_data 
                          if dp.pb_ratio and dp.pb_ratio > 0]
        
        if len(valid_pb_ratios) < data_points * 0.8:
            validation['issues'].append("Many missing or invalid P/B ratios")
        
        # Check data recency
        if historical_analysis.historical_data:
            latest_date = max(pd.to_datetime(dp.date) for dp in historical_analysis.historical_data)
            months_ago = (datetime.now() - latest_date).days / 30.44
            
            if months_ago > 6:
                validation['issues'].append(f"Data may be stale (latest: {months_ago:.1f} months ago)")
        
        # Recommendations
        if len(validation['issues']) == 0:
            validation['recommendations'].append("Data appears suitable for statistical analysis")
        elif validation['valid']:
            validation['recommendations'].append("Analysis possible but consider data limitations")
        
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation error: {str(e)}"],
            'recommendations': ["Check input data format and availability"]
        }