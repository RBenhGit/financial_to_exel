"""
Enhanced P/B Analysis Engine - Integration Layer for Advanced Statistical Features
================================================================================

This module provides an enhanced analysis engine that integrates the existing P/B 
calculation framework with the new advanced statistical analysis capabilities.

Key Features:
- Seamless integration between historical analysis and statistical analysis
- Enhanced fair value calculation with statistical insights
- Combined reporting with all analysis components
- Backward compatibility with existing P/B modules
- Extended API for comprehensive P/B analysis

Classes:
--------
EnhancedPBAnalysisResult
    Complete result combining historical, statistical, and fair value analysis
    
EnhancedPBAnalysisEngine
    Main engine that orchestrates all P/B analysis components

Usage Example:
--------------
>>> from pb_enhanced_analysis import EnhancedPBAnalysisEngine
>>> from data_sources import DataSourceResponse
>>> 
>>> # Single call for complete P/B analysis
>>> engine = EnhancedPBAnalysisEngine()
>>> result = engine.perform_complete_analysis(response, current_book_value=25.50, years=5)
>>> 
>>> # Access all analysis components
>>> print(f"Fair Value: ${result.fair_value_result.fair_scenario.target_price:.2f}")
>>> print(f"Trend: {result.statistical_result.trend_analysis.trend_direction}")
>>> print(f"Market Timing: {result.statistical_result.market_timing_signal}")
>>> print(f"Risk Score: {result.statistical_result.volatility_analysis.overall_risk_score:.2f}")
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from data_sources import DataSourceResponse
from pb_historical_analysis import (
    PBHistoricalAnalysisEngine, 
    PBHistoricalAnalysisResult
)
from pb_fair_value_calculator import (
    PBFairValueCalculator, 
    FairValueCalculationResult,
    create_fair_value_report
)
from pb_statistical_analysis import (
    PBStatisticalAnalysisEngine,
    PBStatisticalAnalysisResult,
    create_statistical_analysis_report,
    validate_statistical_analysis_inputs
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedPBAnalysisResult:
    """
    Complete result of enhanced P/B analysis combining all analysis components.
    """
    
    success: bool
    ticker: str = ""
    analysis_date: str = ""
    
    # Core analysis results
    historical_result: Optional[PBHistoricalAnalysisResult] = None
    statistical_result: Optional[PBStatisticalAnalysisResult] = None
    fair_value_result: Optional[FairValueCalculationResult] = None
    
    # Enhanced insights (derived from combined analysis)
    investment_recommendation: str = "neutral"  # "strong_buy", "buy", "hold", "sell", "strong_sell"
    recommendation_confidence: float = 0.0      # 0.0 to 1.0
    risk_assessment: str = "moderate"           # "low", "moderate", "high", "extreme"
    
    # Key metrics summary
    current_pb_ratio: Optional[float] = None
    fair_value_estimate: Optional[float] = None
    upside_potential: Optional[float] = None
    downside_risk: Optional[float] = None
    
    # Timing and positioning insights
    market_timing_score: float = 0.0           # -1.0 to 1.0 (negative = wait, positive = act)
    position_sizing_score: float = 0.0         # 0.0 to 1.0 (suggested position size factor)
    holding_period_estimate: str = "medium"    # "short", "medium", "long"
    
    # Quality and reliability indicators
    analysis_quality_score: float = 0.0        # Overall quality of analysis
    data_reliability_score: float = 0.0        # Reliability of underlying data
    
    # Warnings and recommendations
    analysis_warnings: List[str] = field(default_factory=list)
    action_recommendations: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    
    error_message: Optional[str] = None


class EnhancedPBAnalysisEngine:
    """
    Enhanced P/B analysis engine that combines historical analysis, statistical analysis,
    and fair value calculation into a comprehensive investment analysis framework.
    """
    
    def __init__(self) -> None:
        """Initialize the enhanced P/B analysis engine with all analysis components."""
        self.historical_engine = PBHistoricalAnalysisEngine()
        self.statistical_engine = PBStatisticalAnalysisEngine()
        self.fair_value_calculator = PBFairValueCalculator()
        
        # Configuration
        self.min_confidence_for_strong_signals = 0.75
        self.min_data_quality_for_recommendations = 0.6
        
        logger.info("Enhanced P/B Analysis Engine initialized")
    
    def perform_complete_analysis(
        self, 
        response: DataSourceResponse,
        current_book_value: float,
        current_price: Optional[float] = None,
        years: int = 5,
        market_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedPBAnalysisResult:
        """Perform complete P/B analysis combining all analysis components.
        
        Args:
            response: Historical financial data from data source
            current_book_value: Current book value per share
            current_price: Current market price (fetched if not provided)
            years: Years of historical data to analyze
            market_data: Market data for correlation analysis

        Returns:
            Complete enhanced P/B analysis result with all components
        """
        try:
            logger.info(f"Starting complete P/B analysis for {years} years")
            
            # Initialize result
            result = EnhancedPBAnalysisResult(
                success=False,
                analysis_date=datetime.now().isoformat()
            )
            
            # Extract ticker from response
            ticker = response.data.get('ticker', 'Unknown') if response.data else 'Unknown'
            result.ticker = ticker
            
            # Step 1: Historical Analysis
            logger.info("Performing historical P/B analysis...")
            historical_result = self.historical_engine.analyze_historical_performance(response, years)
            result.historical_result = historical_result
            
            if not historical_result.success:
                result.error_message = f"Historical analysis failed: {historical_result.error_message}"
                return result
            
            # Step 2: Statistical Analysis
            logger.info("Performing statistical analysis...")
            statistical_result = self.statistical_engine.analyze_pb_statistics(historical_result, market_data)
            result.statistical_result = statistical_result
            
            if not statistical_result.success:
                result.analysis_warnings.append(f"Statistical analysis failed: {statistical_result.error_message}")
                # Continue with partial analysis
            
            # Step 3: Fair Value Calculation
            logger.info("Calculating fair value...")
            fair_value_result = self.fair_value_calculator.calculate_fair_value(
                historical_result, current_book_value, current_price
            )
            result.fair_value_result = fair_value_result
            
            if not fair_value_result.success:
                result.analysis_warnings.append(f"Fair value calculation failed: {fair_value_result.error_message}")
                # Continue with partial analysis
            
            # Step 4: Enhanced Analysis and Insights
            logger.info("Generating enhanced insights...")
            self._generate_enhanced_insights(result, current_price)
            
            # Step 5: Generate Recommendations
            self._generate_investment_recommendations(result)
            
            # Step 6: Quality Assessment
            self._assess_analysis_quality(result)
            
            result.success = True
            logger.info("Complete P/B analysis finished successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in complete P/B analysis: {e}")
            return EnhancedPBAnalysisResult(
                success=False,
                ticker=ticker if 'ticker' in locals() else 'Unknown',
                error_message=f"Analysis error: {str(e)}"
            )
    
    def _generate_enhanced_insights(self, result: EnhancedPBAnalysisResult, current_price: Optional[float]):
        """Generate enhanced insights by combining all analysis components."""
        try:
            # Extract key metrics
            if result.historical_result and result.historical_result.historical_data:
                latest_data = result.historical_result.historical_data[-1]
                result.current_pb_ratio = latest_data.pb_ratio
            
            if result.fair_value_result and result.fair_value_result.fair_scenario:
                result.fair_value_estimate = result.fair_value_result.fair_scenario.target_price
                
                if current_price:
                    upside = (result.fair_value_estimate - current_price) / current_price
                    result.upside_potential = max(0, upside)
                    result.downside_risk = max(0, -upside)
            
            # Market timing score (combines trend and cycle analysis)
            timing_components = []
            
            if result.statistical_result and result.statistical_result.trend_analysis:
                trend = result.statistical_result.trend_analysis
                if trend.trend_direction == "upward":
                    timing_components.append(trend.trend_strength * trend.statistical_significance)
                elif trend.trend_direction == "downward":
                    timing_components.append(-trend.trend_strength * trend.statistical_significance)
                else:
                    timing_components.append(0.0)
            
            if result.statistical_result and result.statistical_result.cycle_analysis:
                cycle = result.statistical_result.cycle_analysis
                if cycle.current_cycle_position == "trough":
                    timing_components.append(0.3)
                elif cycle.current_cycle_position == "expansion":
                    timing_components.append(0.1)
                elif cycle.current_cycle_position == "peak":
                    timing_components.append(-0.3)
                elif cycle.current_cycle_position == "contraction":
                    timing_components.append(-0.1)
            
            if timing_components:
                result.market_timing_score = max(-1.0, min(1.0, sum(timing_components) / len(timing_components)))
            
            # Position sizing score (based on confidence and risk)
            confidence_factors = []
            
            if result.fair_value_result:
                confidence_factors.append(result.fair_value_result.overall_quality_score)
            
            if result.statistical_result:
                confidence_factors.append(result.statistical_result.statistical_confidence)
            
            if result.historical_result and result.historical_result.quality_metrics:
                confidence_factors.append(result.historical_result.quality_metrics.overall_score)
            
            if confidence_factors:
                base_confidence = sum(confidence_factors) / len(confidence_factors)
                
                # Adjust for volatility
                if result.statistical_result and result.statistical_result.volatility_analysis:
                    vol_adjustment = 1.0 - (result.statistical_result.volatility_analysis.overall_risk_score * 0.3)
                    result.position_sizing_score = base_confidence * vol_adjustment
                else:
                    result.position_sizing_score = base_confidence
            
            # Risk assessment
            risk_factors = []
            
            if result.statistical_result and result.statistical_result.volatility_analysis:
                risk_factors.append(result.statistical_result.volatility_analysis.overall_risk_score)
            
            if result.fair_value_result and len(result.fair_value_result.calculation_warnings) > 2:
                risk_factors.append(0.3)  # Additional risk for calculation warnings
            
            if risk_factors:
                avg_risk = sum(risk_factors) / len(risk_factors)
                if avg_risk > 0.7:
                    result.risk_assessment = "high"
                elif avg_risk > 0.4:
                    result.risk_assessment = "moderate"
                else:
                    result.risk_assessment = "low"
            
            # Holding period estimate
            if result.statistical_result and result.statistical_result.cycle_analysis:
                cycles = result.statistical_result.cycle_analysis.cycles_detected
                avg_duration = result.statistical_result.cycle_analysis.avg_cycle_duration_months
                
                if cycles > 2 and avg_duration > 0:
                    if avg_duration < 12:
                        result.holding_period_estimate = "short"
                    elif avg_duration > 36:
                        result.holding_period_estimate = "long"
                    else:
                        result.holding_period_estimate = "medium"
            
        except Exception as e:
            logger.error(f"Error generating enhanced insights: {e}")
    
    def _generate_investment_recommendations(self, result: EnhancedPBAnalysisResult):
        """Generate investment recommendations based on combined analysis."""
        try:
            recommendation_scores = []
            confidence_scores = []
            
            # Fair value recommendation
            if result.fair_value_result and result.fair_value_result.investment_signal:
                signal = result.fair_value_result.investment_signal
                strength = result.fair_value_result.signal_strength
                
                if signal == "buy":
                    recommendation_scores.append(strength)
                elif signal == "sell":
                    recommendation_scores.append(-strength)
                elif signal == "hold":
                    recommendation_scores.append(0.0)
                else:
                    recommendation_scores.append(0.0)
                
                confidence_scores.append(result.fair_value_result.overall_quality_score)
            
            # Statistical timing recommendation
            if result.statistical_result and result.statistical_result.market_timing_signal:
                signal = result.statistical_result.market_timing_signal
                strength = result.statistical_result.signal_strength
                
                if signal == "bullish":
                    recommendation_scores.append(strength * 0.7)  # Lower weight than fair value
                elif signal == "bearish":
                    recommendation_scores.append(-strength * 0.7)
                else:
                    recommendation_scores.append(0.0)
                
                confidence_scores.append(result.statistical_result.statistical_confidence)
            
            # Market timing adjustment
            if result.market_timing_score != 0.0:
                recommendation_scores.append(result.market_timing_score * 0.5)
                confidence_scores.append(0.6)  # Moderate confidence in timing
            
            # Calculate overall recommendation
            if recommendation_scores and confidence_scores:
                weighted_score = sum(score * conf for score, conf in zip(recommendation_scores, confidence_scores))
                total_confidence = sum(confidence_scores)
                
                if total_confidence > 0:
                    overall_score = weighted_score / total_confidence
                    result.recommendation_confidence = total_confidence / len(confidence_scores)
                    
                    # Determine recommendation level
                    if overall_score > 0.4 and result.recommendation_confidence > self.min_confidence_for_strong_signals:
                        result.investment_recommendation = "strong_buy"
                    elif overall_score > 0.15:
                        result.investment_recommendation = "buy"
                    elif overall_score < -0.4 and result.recommendation_confidence > self.min_confidence_for_strong_signals:
                        result.investment_recommendation = "strong_sell"
                    elif overall_score < -0.15:
                        result.investment_recommendation = "sell"
                    else:
                        result.investment_recommendation = "hold"
            
            # Generate action recommendations
            self._generate_action_recommendations(result)
            
        except Exception as e:
            logger.error(f"Error generating investment recommendations: {e}")
            result.investment_recommendation = "neutral"
    
    def _generate_action_recommendations(self, result: EnhancedPBAnalysisResult):
        """Generate specific action recommendations."""
        try:
            # Position sizing recommendations
            if result.position_sizing_score > 0.8:
                result.action_recommendations.append("High confidence analysis supports larger position sizes")
            elif result.position_sizing_score < 0.4:
                result.action_recommendations.append("Low confidence suggests smaller position sizes or waiting")
            
            # Timing recommendations
            if result.market_timing_score > 0.3:
                result.action_recommendations.append("Market timing indicators suggest favorable entry conditions")
            elif result.market_timing_score < -0.3:
                result.action_recommendations.append("Market timing indicators suggest waiting for better entry")
            
            # Risk management recommendations
            if result.risk_assessment == "high":
                result.action_recommendations.append("High risk environment - consider defensive positioning")
                result.risk_warnings.append("Elevated volatility and risk metrics detected")
            
            # Statistical insights
            if result.statistical_result:
                if result.statistical_result.cycle_analysis and result.statistical_result.cycle_analysis.current_cycle_position == "trough":
                    result.action_recommendations.append("Cycle analysis suggests potential buying opportunity")
                elif result.statistical_result.cycle_analysis and result.statistical_result.cycle_analysis.current_cycle_position == "peak":
                    result.action_recommendations.append("Cycle analysis suggests caution or profit-taking")
                
                if result.statistical_result.trend_analysis and result.statistical_result.trend_analysis.statistical_significance > 0.8:
                    direction = result.statistical_result.trend_analysis.trend_direction
                    result.action_recommendations.append(f"Strong statistical evidence for {direction} trend")
            
            # Fair value insights
            if result.fair_value_result and result.upside_potential:
                if result.upside_potential > 0.25:
                    result.action_recommendations.append(f"Significant upside potential ({result.upside_potential:.1%})")
                elif result.downside_risk and result.downside_risk > 0.25:
                    result.action_recommendations.append(f"Significant downside risk ({result.downside_risk:.1%})")
            
            # Data quality warnings
            if result.analysis_quality_score < self.min_data_quality_for_recommendations:
                result.analysis_warnings.append("Low data quality may affect recommendation reliability")
            
        except Exception as e:
            logger.error(f"Error generating action recommendations: {e}")
    
    def _assess_analysis_quality(self, result: EnhancedPBAnalysisResult):
        """Assess overall quality of the analysis."""
        try:
            quality_scores = []
            
            # Historical analysis quality
            if result.historical_result and result.historical_result.quality_metrics:
                quality_scores.append(result.historical_result.quality_metrics.overall_score)
            
            # Statistical analysis quality
            if result.statistical_result:
                quality_scores.append(result.statistical_result.statistical_confidence)
            
            # Fair value analysis quality
            if result.fair_value_result:
                quality_scores.append(result.fair_value_result.overall_quality_score)
            
            # Calculate overall quality
            if quality_scores:
                result.analysis_quality_score = sum(quality_scores) / len(quality_scores)
            
            # Data reliability assessment
            reliability_factors = []
            
            if result.historical_result:
                data_points = result.historical_result.data_points_count
                if data_points >= 48:  # 4+ years quarterly
                    reliability_factors.append(1.0)
                elif data_points >= 24:  # 2+ years quarterly
                    reliability_factors.append(0.8)
                else:
                    reliability_factors.append(0.5)
            
            if result.historical_result and result.historical_result.quality_metrics:
                reliability_factors.append(result.historical_result.quality_metrics.pb_data_completeness)
            
            if reliability_factors:
                result.data_reliability_score = sum(reliability_factors) / len(reliability_factors)
            
            # Quality-based warnings
            if result.analysis_quality_score < 0.5:
                result.analysis_warnings.append("Low overall analysis quality")
            
            if result.data_reliability_score < 0.6:
                result.analysis_warnings.append("Data reliability concerns detected")
            
        except Exception as e:
            logger.error(f"Error assessing analysis quality: {e}")


# Utility functions for external use

def create_enhanced_analysis_report(analysis_result: EnhancedPBAnalysisResult) -> Dict[str, Any]:
    """
    Create a comprehensive report from enhanced P/B analysis results.
    
    Args:
        analysis_result (EnhancedPBAnalysisResult): Enhanced analysis results
        
    Returns:
        Dict[str, Any]: Formatted comprehensive report
    """
    try:
        if not analysis_result.success:
            return {
                'success': False,
                'error': analysis_result.error_message,
                'ticker': analysis_result.ticker
            }
        
        # Build comprehensive report
        report = {
            'success': True,
            'ticker': analysis_result.ticker,
            'analysis_date': analysis_result.analysis_date,
            
            # Executive summary
            'executive_summary': {
                'investment_recommendation': analysis_result.investment_recommendation,
                'recommendation_confidence': analysis_result.recommendation_confidence,
                'fair_value_estimate': analysis_result.fair_value_estimate,
                'upside_potential': analysis_result.upside_potential,
                'downside_risk': analysis_result.downside_risk,
                'risk_assessment': analysis_result.risk_assessment,
                'market_timing_score': analysis_result.market_timing_score,
            },
            
            # Detailed analysis components
            'historical_analysis': {},
            'statistical_analysis': {},
            'fair_value_analysis': {},
            
            # Enhanced insights
            'enhanced_insights': {
                'current_pb_ratio': analysis_result.current_pb_ratio,
                'position_sizing_score': analysis_result.position_sizing_score,
                'holding_period_estimate': analysis_result.holding_period_estimate,
                'analysis_quality_score': analysis_result.analysis_quality_score,
                'data_reliability_score': analysis_result.data_reliability_score,
            },
            
            # Recommendations and warnings
            'recommendations': {
                'action_recommendations': analysis_result.action_recommendations,
                'risk_warnings': analysis_result.risk_warnings,
                'analysis_warnings': analysis_result.analysis_warnings,
            }
        }
        
        # Add detailed component reports
        if analysis_result.historical_result:
            # Would call existing historical analysis reporting function
            report['historical_analysis'] = {
                'success': analysis_result.historical_result.success,
                'data_points': analysis_result.historical_result.data_points_count,
                'quality_score': analysis_result.historical_result.quality_metrics.overall_score if analysis_result.historical_result.quality_metrics else None,
            }
        
        if analysis_result.statistical_result:
            report['statistical_analysis'] = create_statistical_analysis_report(analysis_result.statistical_result)
        
        if analysis_result.fair_value_result:
            report['fair_value_analysis'] = create_fair_value_report(analysis_result.fair_value_result)
        
        return report
        
    except Exception as e:
        logger.error(f"Error creating enhanced analysis report: {e}")
        return {
            'success': False,
            'error': f"Report generation error: {str(e)}",
            'ticker': analysis_result.ticker if analysis_result else 'Unknown'
        }


def validate_enhanced_analysis_inputs(response: DataSourceResponse,
                                     current_book_value: float,
                                     current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Validate inputs for enhanced P/B analysis.
    
    Args:
        response (DataSourceResponse): Historical data response
        current_book_value (float): Current book value per share
        current_price (Optional[float]): Current market price
        
    Returns:
        Dict[str, Any]: Validation results
    """
    try:
        validation = {'valid': True, 'issues': [], 'recommendations': []}
        
        # Validate data response
        if not response.success or not response.data:
            validation['valid'] = False
            validation['issues'].append("Invalid or unsuccessful data response")
            return validation
        
        # Validate book value
        if current_book_value <= 0:
            validation['valid'] = False
            validation['issues'].append("Book value per share must be positive")
            return validation
        
        # Validate price if provided
        if current_price is not None and current_price <= 0:
            validation['issues'].append("Current price must be positive if provided")
        
        # Check data availability for statistical analysis
        ticker = response.data.get('ticker', 'Unknown')
        
        # Basic data structure validation
        required_fields = ['income_statements', 'balance_sheets', 'cash_flows']
        missing_fields = [field for field in required_fields if field not in response.data]
        
        if missing_fields:
            validation['issues'].append(f"Missing required data fields: {missing_fields}")
        
        # Recommendations
        if not validation['issues']:
            validation['recommendations'].append("All inputs appear valid for enhanced P/B analysis")
        
        if current_price is None:
            validation['recommendations'].append("Providing current market price will enable more comprehensive analysis")
        
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation error: {str(e)}"],
            'recommendations': ["Check input data format and completeness"]
        }


# Quick analysis function for simple use cases
def quick_pb_analysis(response: DataSourceResponse,
                     current_book_value: float,
                     current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Perform quick P/B analysis with simplified output.
    
    Args:
        response (DataSourceResponse): Historical data
        current_book_value (float): Current book value per share  
        current_price (Optional[float]): Current market price
        
    Returns:
        Dict[str, Any]: Simplified analysis results
    """
    try:
        # Perform full analysis
        engine = EnhancedPBAnalysisEngine()
        result = engine.perform_complete_analysis(response, current_book_value, current_price)
        
        if not result.success:
            return {'success': False, 'error': result.error_message}
        
        # Return simplified summary
        return {
            'success': True,
            'ticker': result.ticker,
            'recommendation': result.investment_recommendation,
            'confidence': result.recommendation_confidence,
            'fair_value': result.fair_value_estimate,
            'current_pb': result.current_pb_ratio,
            'upside_potential': result.upside_potential,
            'risk_level': result.risk_assessment,
            'market_timing': result.market_timing_score,
            'key_recommendations': result.action_recommendations[:3],  # Top 3
            'warnings': result.analysis_warnings[:2] if result.analysis_warnings else []  # Top 2
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Quick analysis error: {str(e)}"
        }