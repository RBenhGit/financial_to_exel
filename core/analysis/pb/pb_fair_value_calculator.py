"""
Fair Value Calculation Engine Based on Historical P/B Patterns
============================================================

This module implements the core fair value calculation algorithm using historical P/B 
performance patterns with weighted calculations, scenario analysis, and quality-adjusted confidence.

Key Features:
- Base Algorithm: Book Value × Historical Median P/B
- Weighted Calculation: Recent quarters weighted higher with exponential decay
- Scenario Analysis: Conservative/Fair/Optimistic using historical quartiles
- Quality Integration: Adjust confidence based on DataQualityMetrics
- Statistical Validation: Valuation ranges with significance testing

Classes:
--------
FairValueScenario
    Individual valuation scenario (Conservative/Fair/Optimistic)
    
FairValueCalculationResult
    Complete result of fair value calculation with all scenarios and metadata
    
PBFairValueCalculator
    Main calculator engine for P/B-based fair value estimation

Usage Example:
--------------
>>> from pb_fair_value_calculator import PBFairValueCalculator
>>> from pb_historical_analysis import PBHistoricalAnalysisEngine
>>> from data_sources import DataSourceResponse
>>> 
>>> # Get historical analysis first
>>> historical_engine = PBHistoricalAnalysisEngine()
>>> historical_result = historical_engine.analyze_historical_performance(response, years=5)
>>> 
>>> # Calculate fair value
>>> calculator = PBFairValueCalculator()
>>> fair_value = calculator.calculate_fair_value(historical_result, current_book_value=25.50)
>>> print(f"Fair Value: ${fair_value.fair_scenario.target_price:.2f}")
>>> print(f"Range: ${fair_value.conservative_scenario.target_price:.2f} - ${fair_value.optimistic_scenario.target_price:.2f}")
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from statistics import median, stdev
import warnings
try:
    from scipy import stats
except ImportError:
    # Fallback for environments without scipy
    class stats:
        @staticmethod
        def t_ppf(q, df):
            # Simple approximation for t-distribution critical value
            return 1.96 if df > 30 else 2.0

from ...data_sources.interfaces.data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics
from .pb_historical_analysis import PBHistoricalAnalysisResult, PBHistoricalQualityMetrics, PBStatisticalSummary

logger = logging.getLogger(__name__)


@dataclass
class FairValueScenario:
    """
    Individual valuation scenario with P/B-based fair value estimation.
    """
    
    scenario_name: str  # "Conservative", "Fair", "Optimistic"
    pb_multiple: float = 0.0  # P/B ratio used for this scenario
    book_value_per_share: float = 0.0  # Current book value per share
    target_price: float = 0.0  # Calculated fair value price
    confidence_level: float = 0.0  # Confidence in this scenario (0-1)
    
    # Statistical backing
    percentile_basis: float = 0.0  # Historical percentile this scenario represents
    weight_factor: float = 0.0  # Quality-adjusted weight applied
    data_points_used: int = 0  # Number of historical points used
    
    # Risk metrics
    downside_risk: float = 0.0  # Potential downside from current price
    upside_potential: float = 0.0  # Potential upside from current price
    volatility_adjusted: bool = False  # Whether volatility adjustment was applied


@dataclass
class FairValueCalculationResult:
    """
    Complete result of fair value calculation with all scenarios and metadata.
    """
    
    success: bool
    ticker: str = ""
    calculation_date: str = ""
    current_price: Optional[float] = None
    current_book_value: Optional[float] = None
    
    # Core scenarios
    conservative_scenario: Optional[FairValueScenario] = None
    fair_scenario: Optional[FairValueScenario] = None  # Primary fair value estimate
    optimistic_scenario: Optional[FairValueScenario] = None
    
    # Weighted calculation details
    weighted_pb_multiple: float = 0.0  # Quality and time-weighted P/B
    exponential_decay_factor: float = 0.0  # Decay factor used for recent weighting
    quality_adjustment_factor: float = 0.0  # Overall quality adjustment
    
    # Statistical validation
    statistical_significance: float = 0.0  # Statistical significance of estimate
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # 95% confidence interval
    r_squared: float = 0.0  # Goodness of fit for historical P/B model
    
    # Recommendation
    investment_signal: str = "neutral"  # "buy", "sell", "hold", "neutral"
    signal_strength: float = 0.0  # Strength of signal (0-1)
    margin_of_safety: float = 0.0  # Margin of safety from current price
    
    # Data quality and warnings
    overall_quality_score: float = 0.0
    calculation_warnings: List[str] = field(default_factory=list)
    methodology_notes: List[str] = field(default_factory=list)
    
    error_message: Optional[str] = None


class PBFairValueCalculator:
    """
    Engine for calculating fair value based on historical P/B performance patterns.
    
    This calculator uses the historical P/B analysis to determine fair value estimates
    with weighted calculations, scenario analysis, and quality-adjusted confidence levels.
    """
    
    def __init__(self, decay_factor: float = 0.85, min_data_points: int = 12) -> None:
        """Initialize the fair value calculator with weighting parameters.
        
        Args:
            decay_factor: Exponential decay factor for time weighting (0-1)
            min_data_points: Minimum historical data points required for calculation
        """
        self.decay_factor = decay_factor
        self.min_data_points = min_data_points
        self.confidence_threshold = 0.7  # Minimum quality for strong signals
        
        logger.info("P/B Fair Value Calculator initialized")
    
    def calculate_fair_value(self, historical_analysis: PBHistoricalAnalysisResult, 
                           current_book_value: float,
                           current_price: Optional[float] = None) -> FairValueCalculationResult:
        """
        Calculate fair value based on historical P/B analysis.
        
        Args:
            historical_analysis (PBHistoricalAnalysisResult): Historical P/B analysis results
            current_book_value (float): Current book value per share
            current_price (Optional[float]): Current market price for comparison
            
        Returns:
            FairValueCalculationResult: Complete fair value calculation results
        """
        try:
            logger.info(f"Calculating fair value for {historical_analysis.ticker}")
            
            # Initialize result
            result = FairValueCalculationResult(
                success=False,
                ticker=historical_analysis.ticker,
                calculation_date=datetime.now().isoformat(),
                current_book_value=current_book_value,
                current_price=current_price
            )
            
            # Validate inputs
            validation_result = self._validate_inputs(historical_analysis, current_book_value)
            if not validation_result['valid']:
                result.error_message = validation_result['error']
                result.calculation_warnings.extend(validation_result['warnings'])
                return result
            
            # Extract quality metrics
            quality_metrics = historical_analysis.quality_metrics
            statistics = historical_analysis.statistics
            
            result.overall_quality_score = quality_metrics.overall_score if quality_metrics else 0.5
            
            # Calculate weighted P/B multiple with exponential decay
            weighted_pb = self._calculate_weighted_pb_multiple(historical_analysis)
            result.weighted_pb_multiple = weighted_pb['multiple']
            result.exponential_decay_factor = weighted_pb['decay_factor']
            result.quality_adjustment_factor = weighted_pb['quality_factor']
            
            # Calculate scenario-based fair values
            scenarios = self._calculate_scenario_analysis(historical_analysis, current_book_value)
            result.conservative_scenario = scenarios['conservative']
            result.fair_scenario = scenarios['fair']
            result.optimistic_scenario = scenarios['optimistic']
            
            # Perform statistical validation
            validation = self._calculate_statistical_validation(historical_analysis, result)
            result.statistical_significance = validation['significance']
            result.confidence_interval = validation['confidence_interval']
            result.r_squared = validation['r_squared']
            
            # Generate investment signal and recommendation
            recommendation = self._generate_investment_recommendation(result, current_price)
            result.investment_signal = recommendation['signal']
            result.signal_strength = recommendation['strength']
            result.margin_of_safety = recommendation['margin_of_safety']
            
            # Add calculation notes and warnings
            self._add_methodology_notes(result, historical_analysis)
            
            result.success = True
            logger.info(f"Fair value calculation completed: ${result.fair_scenario.target_price:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating fair value: {e}")
            return FairValueCalculationResult(
                success=False,
                ticker=historical_analysis.ticker if historical_analysis else "Unknown",
                error_message=f"Calculation error: {str(e)}"
            )
    
    def _validate_inputs(self, historical_analysis: PBHistoricalAnalysisResult, 
                        current_book_value: float) -> Dict[str, Any]:
        """Validate inputs for fair value calculation"""
        try:
            validation = {'valid': True, 'error': None, 'warnings': []}
            
            # Check historical analysis
            if not historical_analysis.success:
                validation['valid'] = False
                validation['error'] = "Historical analysis was unsuccessful"
                return validation
            
            if historical_analysis.data_points_count < self.min_data_points:
                validation['warnings'].append(f"Limited historical data ({historical_analysis.data_points_count} points)")
                if historical_analysis.data_points_count < 6:
                    validation['valid'] = False
                    validation['error'] = "Insufficient historical data for reliable calculation"
                    return validation
            
            # Check book value
            if current_book_value <= 0:
                validation['valid'] = False
                validation['error'] = "Invalid book value per share"
                return validation
            
            # Check data quality
            if historical_analysis.quality_metrics and historical_analysis.quality_metrics.overall_score < 0.3:
                validation['warnings'].append("Very low data quality score")
            
            # Check for statistical validity
            if not historical_analysis.statistics:
                validation['warnings'].append("No statistical summary available")
            elif historical_analysis.statistics.std_pb > historical_analysis.statistics.mean_pb * 2:
                validation['warnings'].append("High P/B volatility may reduce reliability")
            
            return validation
            
        except Exception as e:
            return {'valid': False, 'error': f"Validation error: {str(e)}", 'warnings': []}
    
    def _calculate_weighted_pb_multiple(self, historical_analysis: PBHistoricalAnalysisResult) -> Dict[str, float]:
        """
        Calculate quality and time-weighted P/B multiple with exponential decay.
        """
        try:
            pb_data = historical_analysis.historical_data
            quality_metrics = historical_analysis.quality_metrics
            
            if not pb_data:
                return {'multiple': 0.0, 'decay_factor': self.decay_factor, 'quality_factor': 0.5}
            
            # Sort by date (most recent first)
            sorted_data = sorted(pb_data, key=lambda x: pd.to_datetime(x.date), reverse=True)
            
            # Extract valid P/B ratios with their positions (recent = lower index)
            valid_ratios = []
            valid_positions = []
            
            for i, dp in enumerate(sorted_data):
                if dp.pb_ratio and dp.pb_ratio > 0:
                    valid_ratios.append(dp.pb_ratio)
                    valid_positions.append(i)
            
            if not valid_ratios:
                return {'multiple': 0.0, 'decay_factor': self.decay_factor, 'quality_factor': 0.5}
            
            # Exponential time weighting: more recent P/B ratios get higher weight
            # Formula: weight = decay_factor^position, where position 0 = most recent
            # Example: with decay_factor=0.85, weights are [1.0, 0.85, 0.72, 0.61, ...]
            weights = []
            for pos in valid_positions:
                weight = self.decay_factor ** pos
                weights.append(weight)
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
            else:
                weights = [1.0 / len(weights)] * len(weights)
            
            # Apply quality adjustment
            quality_factor = quality_metrics.overall_score if quality_metrics else 0.7
            quality_adjusted_weights = [w * quality_factor for w in weights]
            
            # Calculate weighted P/B multiple
            weighted_pb = sum(ratio * weight for ratio, weight in zip(valid_ratios, quality_adjusted_weights))
            
            # Ensure reasonable bounds
            if weighted_pb <= 0:
                weighted_pb = historical_analysis.statistics.median_pb if historical_analysis.statistics else 1.0
            
            return {
                'multiple': weighted_pb,
                'decay_factor': self.decay_factor,
                'quality_factor': quality_factor
            }
            
        except Exception as e:
            logger.error(f"Error calculating weighted P/B multiple: {e}")
            # Fallback to median
            if historical_analysis.statistics and historical_analysis.statistics.median_pb > 0:
                return {'multiple': historical_analysis.statistics.median_pb, 'decay_factor': self.decay_factor, 'quality_factor': 0.5}
            return {'multiple': 1.0, 'decay_factor': self.decay_factor, 'quality_factor': 0.5}
    
    def _calculate_scenario_analysis(self, historical_analysis: PBHistoricalAnalysisResult, 
                                   current_book_value: float) -> Dict[str, FairValueScenario]:
        """
        Calculate Conservative/Fair/Optimistic scenarios using historical quartiles.
        """
        try:
            statistics = historical_analysis.statistics
            quality_score = historical_analysis.quality_metrics.overall_score if historical_analysis.quality_metrics else 0.7
            data_points = historical_analysis.data_points_count
            
            # Define scenarios based on historical percentiles
            scenarios = {}
            
            # Conservative Scenario (25th percentile)
            conservative_pb = statistics.p25_pb if statistics and statistics.p25_pb > 0 else 1.0
            scenarios['conservative'] = FairValueScenario(
                scenario_name="Conservative",
                pb_multiple=conservative_pb,
                book_value_per_share=current_book_value,
                target_price=conservative_pb * current_book_value,
                confidence_level=quality_score * 0.9,  # Slightly more confident in conservative estimates
                percentile_basis=25.0,
                weight_factor=quality_score,
                data_points_used=data_points
            )
            
            # Fair Scenario (Median/50th percentile with quality weighting)
            fair_pb = statistics.quality_weighted_mean if statistics and statistics.quality_weighted_mean > 0 else statistics.median_pb if statistics else 1.0
            scenarios['fair'] = FairValueScenario(
                scenario_name="Fair",
                pb_multiple=fair_pb,
                book_value_per_share=current_book_value,
                target_price=fair_pb * current_book_value,
                confidence_level=quality_score,
                percentile_basis=50.0,
                weight_factor=quality_score,
                data_points_used=data_points
            )
            
            # Optimistic Scenario (75th percentile)
            optimistic_pb = statistics.p75_pb if statistics and statistics.p75_pb > 0 else fair_pb * 1.3
            scenarios['optimistic'] = FairValueScenario(
                scenario_name="Optimistic",
                pb_multiple=optimistic_pb,
                book_value_per_share=current_book_value,
                target_price=optimistic_pb * current_book_value,
                confidence_level=quality_score * 0.8,  # Less confident in optimistic estimates
                percentile_basis=75.0,
                weight_factor=quality_score,
                data_points_used=data_points
            )
            
            # Calculate risk metrics for each scenario
            current_price = None
            for scenario in scenarios.values():
                if current_price:  # If we have current price for comparison
                    scenario.upside_potential = max(0, (scenario.target_price - current_price) / current_price)
                    scenario.downside_risk = max(0, (current_price - scenario.target_price) / current_price)
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error calculating scenario analysis: {e}")
            # Fallback scenarios
            fallback_pb = 1.5
            return {
                'conservative': FairValueScenario("Conservative", fallback_pb * 0.8, current_book_value, fallback_pb * 0.8 * current_book_value, 0.5),
                'fair': FairValueScenario("Fair", fallback_pb, current_book_value, fallback_pb * current_book_value, 0.5),
                'optimistic': FairValueScenario("Optimistic", fallback_pb * 1.3, current_book_value, fallback_pb * 1.3 * current_book_value, 0.4)
            }
    
    def _calculate_statistical_validation(self, historical_analysis: PBHistoricalAnalysisResult, 
                                        result: FairValueCalculationResult) -> Dict[str, Any]:
        """
        Calculate statistical significance and confidence intervals.
        """
        try:
            validation = {'significance': 0.0, 'confidence_interval': (0.0, 0.0), 'r_squared': 0.0}
            
            pb_data = historical_analysis.historical_data
            statistics = historical_analysis.statistics
            
            if not pb_data or not statistics:
                return validation
            
            # Extract valid P/B ratios
            valid_ratios = [dp.pb_ratio for dp in pb_data if dp.pb_ratio and dp.pb_ratio > 0]
            
            if len(valid_ratios) < 3:
                return validation
            
            # Calculate statistical significance based on data consistency
            mean_pb = statistics.mean_pb
            std_pb = statistics.std_pb
            
            if std_pb > 0:
                # Calculate coefficient of variation (lower = more consistent = higher significance)
                cv = std_pb / mean_pb
                validation['significance'] = max(0.0, min(1.0, 1.0 - cv))
            
            # Calculate 95% confidence interval around fair value estimate
            if result.fair_scenario and len(valid_ratios) > 1:
                n = len(valid_ratios)
                std_err = std_pb / np.sqrt(n)
                margin_of_error = stats.t.ppf(0.975, n-1) * std_err  # 95% confidence
                
                fair_pb = result.fair_scenario.pb_multiple
                lower_bound = (fair_pb - margin_of_error) * result.current_book_value
                upper_bound = (fair_pb + margin_of_error) * result.current_book_value
                
                validation['confidence_interval'] = (max(0, lower_bound), upper_bound)
            
            # R-squared approximation based on trend analysis
            if historical_analysis.trend_analysis:
                validation['r_squared'] = historical_analysis.trend_analysis.r_squared
            
            return validation
            
        except Exception as e:
            logger.error(f"Error calculating statistical validation: {e}")
            return {'significance': 0.0, 'confidence_interval': (0.0, 0.0), 'r_squared': 0.0}
    
    def _generate_investment_recommendation(self, result: FairValueCalculationResult, 
                                          current_price: Optional[float]) -> Dict[str, Any]:
        """
        Generate investment signal and recommendation based on fair value vs current price.
        """
        try:
            recommendation = {'signal': 'neutral', 'strength': 0.0, 'margin_of_safety': 0.0}
            
            if not current_price or not result.fair_scenario:
                return recommendation
            
            fair_value = result.fair_scenario.target_price
            confidence = result.fair_scenario.confidence_level
            quality = result.overall_quality_score
            
            # Calculate margin of safety
            margin_of_safety = (fair_value - current_price) / current_price
            recommendation['margin_of_safety'] = margin_of_safety
            
            # Determine signal based on margin of safety and confidence
            min_confidence = 0.6
            
            if confidence >= min_confidence and quality >= self.confidence_threshold:
                if margin_of_safety > 0.15:  # 15% undervalued
                    recommendation['signal'] = 'buy'
                    recommendation['strength'] = min(1.0, margin_of_safety * 2)
                elif margin_of_safety < -0.15:  # 15% overvalued
                    recommendation['signal'] = 'sell'
                    recommendation['strength'] = min(1.0, abs(margin_of_safety) * 2)
                elif abs(margin_of_safety) < 0.05:  # Within 5% of fair value
                    recommendation['signal'] = 'hold'
                    recommendation['strength'] = 0.3
                else:
                    recommendation['signal'] = 'neutral'
                    recommendation['strength'] = 0.2
            else:
                # Low confidence - neutral signal
                recommendation['signal'] = 'neutral'
                recommendation['strength'] = max(0.1, confidence * quality)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating investment recommendation: {e}")
            return {'signal': 'neutral', 'strength': 0.0, 'margin_of_safety': 0.0}
    
    def _add_methodology_notes(self, result: FairValueCalculationResult, 
                             historical_analysis: PBHistoricalAnalysisResult) -> None:
        """
        Add methodology notes and warnings to the result.
        """
        try:
            # Methodology notes
            result.methodology_notes.append("Fair value calculated using historical P/B performance patterns")
            result.methodology_notes.append(f"Exponential decay factor: {result.exponential_decay_factor:.3f}")
            result.methodology_notes.append(f"Quality adjustment factor: {result.quality_adjustment_factor:.3f}")
            
            if result.fair_scenario:
                result.methodology_notes.append(f"Primary estimate uses quality-weighted mean P/B: {result.fair_scenario.pb_multiple:.2f}")
            
            # Calculation warnings based on data quality and characteristics
            if result.overall_quality_score < 0.6:
                result.calculation_warnings.append("Low data quality may affect reliability")
            
            if historical_analysis.data_points_count < 16:  # Less than 4 years quarterly
                result.calculation_warnings.append("Limited historical data for robust analysis")
            
            if historical_analysis.statistics and historical_analysis.statistics.std_pb > historical_analysis.statistics.mean_pb:
                result.calculation_warnings.append("High P/B volatility increases uncertainty")
            
            if historical_analysis.trend_analysis and historical_analysis.trend_analysis.trend_strength > 0.7:
                result.calculation_warnings.append("Strong trend detected - fair value may be transitioning")
            
            # Quality-specific warnings
            if historical_analysis.quality_metrics:
                qm = historical_analysis.quality_metrics
                if qm.pb_data_completeness < 0.8:
                    result.calculation_warnings.append("Incomplete P/B historical data")
                if qm.temporal_consistency < 0.7:
                    result.calculation_warnings.append("Irregular data intervals")
                if qm.outlier_detection_score < 0.8:
                    result.calculation_warnings.append("Potential outliers in historical data")
            
            # Statistical significance warnings
            if result.statistical_significance < 0.5:
                result.calculation_warnings.append("Low statistical significance")
            
            if result.r_squared < 0.3:
                result.calculation_warnings.append("Weak historical trend correlation")
            
        except Exception as e:
            logger.error(f"Error adding methodology notes: {e}")


# Utility functions for external use

def create_fair_value_report(calculation_result: FairValueCalculationResult) -> Dict[str, Any]:
    """
    Create a comprehensive report from fair value calculation results.
    
    Args:
        calculation_result (FairValueCalculationResult): Calculation results
        
    Returns:
        Dict[str, Any]: Formatted report dictionary
    """
    try:
        if not calculation_result.success:
            return {
                'success': False,
                'error': calculation_result.error_message,
                'ticker': calculation_result.ticker
            }
        
        report = {
            'success': True,
            'ticker': calculation_result.ticker,
            'calculation_date': calculation_result.calculation_date,
            'current_price': calculation_result.current_price,
            'current_book_value': calculation_result.current_book_value,
            
            'fair_value_estimate': {
                'target_price': calculation_result.fair_scenario.target_price if calculation_result.fair_scenario else None,
                'pb_multiple': calculation_result.fair_scenario.pb_multiple if calculation_result.fair_scenario else None,
                'confidence_level': calculation_result.fair_scenario.confidence_level if calculation_result.fair_scenario else None,
            },
            
            'valuation_scenarios': {
                'conservative': {
                    'target_price': calculation_result.conservative_scenario.target_price if calculation_result.conservative_scenario else None,
                    'pb_multiple': calculation_result.conservative_scenario.pb_multiple if calculation_result.conservative_scenario else None,
                    'percentile_basis': calculation_result.conservative_scenario.percentile_basis if calculation_result.conservative_scenario else None,
                },
                'optimistic': {
                    'target_price': calculation_result.optimistic_scenario.target_price if calculation_result.optimistic_scenario else None,
                    'pb_multiple': calculation_result.optimistic_scenario.pb_multiple if calculation_result.optimistic_scenario else None,
                    'percentile_basis': calculation_result.optimistic_scenario.percentile_basis if calculation_result.optimistic_scenario else None,
                }
            },
            
            'investment_recommendation': {
                'signal': calculation_result.investment_signal,
                'strength': calculation_result.signal_strength,
                'margin_of_safety': calculation_result.margin_of_safety,
            },
            
            'statistical_validation': {
                'significance': calculation_result.statistical_significance,
                'confidence_interval': calculation_result.confidence_interval,
                'r_squared': calculation_result.r_squared,
                'overall_quality_score': calculation_result.overall_quality_score,
            },
            
            'methodology': {
                'weighted_pb_multiple': calculation_result.weighted_pb_multiple,
                'exponential_decay_factor': calculation_result.exponential_decay_factor,
                'quality_adjustment_factor': calculation_result.quality_adjustment_factor,
                'notes': calculation_result.methodology_notes
            },
            
            'warnings': calculation_result.calculation_warnings
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Error creating fair value report: {e}")
        return {
            'success': False,
            'error': f"Report generation error: {str(e)}",
            'ticker': calculation_result.ticker if calculation_result else 'Unknown'
        }


def validate_fair_value_inputs(current_book_value: float, 
                              current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Validate inputs for fair value calculation.
    
    Args:
        current_book_value (float): Current book value per share
        current_price (Optional[float]): Current market price
        
    Returns:
        Dict[str, Any]: Validation results
    """
    try:
        validation = {'valid': True, 'issues': [], 'recommendations': []}
        
        # Validate book value
        if current_book_value <= 0:
            validation['valid'] = False
            validation['issues'].append("Book value per share must be positive")
            return validation
        
        if current_book_value > 1000:
            validation['issues'].append("Very high book value - verify data accuracy")
        
        # Validate current price if provided
        if current_price is not None:
            if current_price <= 0:
                validation['issues'].append("Current price must be positive")
            elif current_price > current_book_value * 20:
                validation['issues'].append("Very high P/B ratio - analysis may be less reliable")
        
        # Recommendations
        if not validation['issues']:
            validation['recommendations'].append("Inputs appear valid for fair value calculation")
        
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation error: {str(e)}"],
            'recommendations': ["Check input data format and values"]
        }