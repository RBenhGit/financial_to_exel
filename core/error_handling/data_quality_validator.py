"""
Data Quality Validation and Scoring Module
==========================================

This module provides comprehensive data quality validation and scoring for financial analysis.
It evaluates completeness, accuracy, freshness, and consistency of financial data from various sources.

Features:
- Multi-dimensional quality scoring
- Industry comparison validation
- Historical data consistency checks
- Missing data impact assessment
- Data source reliability scoring
- Quality-based confidence intervals

Classes:
    DataQualityValidator: Main validation and scoring engine
    QualityMetrics: Data class for quality measurements
    QualityReport: Comprehensive quality assessment report
    ValidationResult: Result of data validation checks
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """Data quality levels for classification"""
    EXCELLENT = "excellent"      # 90-100% quality score
    GOOD = "good"               # 70-89% quality score
    ACCEPTABLE = "acceptable"    # 50-69% quality score
    POOR = "poor"               # 25-49% quality score
    UNUSABLE = "unusable"       # 0-24% quality score


class DataSourceReliability(Enum):
    """Reliability ratings for different data sources"""
    VERY_HIGH = "very_high"     # Premium APIs, verified data
    HIGH = "high"               # Established free APIs
    MEDIUM = "medium"           # Secondary sources, calculated data
    LOW = "low"                 # Unverified or outdated sources
    UNKNOWN = "unknown"         # Source reliability not assessed


@dataclass
class QualityMetrics:
    """Data class for quality measurement components"""
    completeness: float = 0.0           # Percentage of non-missing values
    accuracy_score: float = 0.0         # Estimated accuracy based on cross-validation
    freshness_score: float = 0.0        # Recency of data updates
    consistency_score: float = 0.0      # Internal consistency checks
    source_reliability: float = 0.0     # Data source reliability
    sample_size_score: float = 0.0      # Adequacy of sample size
    overall_score: float = 0.0          # Weighted overall quality score
    confidence_level: float = 0.0       # Statistical confidence in the data


@dataclass
class ValidationResult:
    """Result of data validation checks"""
    is_valid: bool
    quality_level: DataQualityLevel
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Optional[QualityMetrics] = None


@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    dataset_name: str
    validation_result: ValidationResult
    peer_count: int
    missing_data_percentage: float
    outlier_percentage: float
    data_age_days: float
    source_breakdown: Dict[str, int] = field(default_factory=dict)
    quality_factors: Dict[str, float] = field(default_factory=dict)
    improvement_suggestions: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class DataQualityValidator:
    """
    Comprehensive data quality validator for financial data
    """
    
    def __init__(self):
        self.source_reliability_map = {
            'yfinance': DataSourceReliability.HIGH,
            'alpha_vantage': DataSourceReliability.VERY_HIGH,
            'fmp': DataSourceReliability.HIGH,
            'polygon': DataSourceReliability.VERY_HIGH,
            'manual': DataSourceReliability.MEDIUM,
            'calculated': DataSourceReliability.MEDIUM,
            'cached': DataSourceReliability.HIGH,
            'excel': DataSourceReliability.HIGH,
            'unknown': DataSourceReliability.UNKNOWN
        }
        
        # Quality scoring weights
        self.quality_weights = {
            'completeness': 0.25,
            'accuracy': 0.20,
            'freshness': 0.15,
            'consistency': 0.15,
            'source_reliability': 0.15,
            'sample_size': 0.10
        }
    
    def validate_industry_data(self, industry_stats, peer_data: List[Dict]) -> ValidationResult:
        """
        Validate industry comparison data quality
        
        Args:
            industry_stats: IndustryStatistics object
            peer_data: List of peer company data dictionaries
            
        Returns:
            ValidationResult with quality assessment
        """
        try:
            metrics = self._calculate_quality_metrics(industry_stats, peer_data)
            quality_level = self._determine_quality_level(metrics.overall_score)
            
            issues = []
            warnings = []
            recommendations = []
            
            # Check minimum peer count
            if industry_stats.peer_count < 5:
                issues.append(f"Insufficient peer companies: {industry_stats.peer_count} < 5")
                recommendations.append("Consider expanding sector criteria to find more peer companies")
            elif industry_stats.peer_count < 10:
                warnings.append(f"Low peer count may affect statistical reliability: {industry_stats.peer_count}")
                recommendations.append("Additional peer companies would improve statistical confidence")
            
            # Check data completeness
            if metrics.completeness < 0.7:
                issues.append(f"Poor data completeness: {metrics.completeness:.1%}")
                recommendations.append("Consider using additional data sources for missing values")
            elif metrics.completeness < 0.9:
                warnings.append(f"Moderate data completeness: {metrics.completeness:.1%}")
            
            # Check data freshness
            if metrics.freshness_score < 0.5:
                warnings.append("Data may be outdated - consider refreshing from sources")
                recommendations.append("Update data sources to ensure current market conditions")
            
            # Check for outliers
            if hasattr(industry_stats, 'std_pb') and industry_stats.std_pb:
                cv = industry_stats.std_pb / industry_stats.mean_pb if industry_stats.mean_pb else 0
                if cv > 1.0:  # High coefficient of variation
                    warnings.append(f"High variability in P/B ratios (CV: {cv:.2f})")
                    recommendations.append("Consider sub-industry analysis or outlier investigation")
            
            # Overall validation
            is_valid = (
                industry_stats.peer_count >= 3 and  # Absolute minimum
                metrics.completeness >= 0.3 and     # Basic completeness
                metrics.overall_score >= 0.25       # Minimum usable quality
            )
            
            if not is_valid:
                issues.append("Data quality too poor for reliable industry comparison")
                recommendations.append("Fallback to historical-only analysis recommended")
            
            return ValidationResult(
                is_valid=is_valid,
                quality_level=quality_level,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Error validating industry data: {e}")
            return ValidationResult(
                is_valid=False,
                quality_level=DataQualityLevel.UNUSABLE,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Unable to assess data quality - manual review required"]
            )
    
    def validate_historical_data(self, historical_data: pd.DataFrame, ticker: str) -> ValidationResult:
        """
        Validate historical financial data quality
        
        Args:
            historical_data: DataFrame with historical financial data
            ticker: Stock ticker symbol
            
        Returns:
            ValidationResult with quality assessment
        """
        try:
            if historical_data.empty:
                return ValidationResult(
                    is_valid=False,
                    quality_level=DataQualityLevel.UNUSABLE,
                    issues=["No historical data available"],
                    recommendations=["Obtain historical financial data for analysis"]
                )
            
            metrics = self._calculate_historical_quality_metrics(historical_data)
            quality_level = self._determine_quality_level(metrics.overall_score)
            
            issues = []
            warnings = []
            recommendations = []
            
            # Check data span
            years_of_data = len(historical_data)
            if years_of_data < 3:
                issues.append(f"Insufficient historical data: {years_of_data} years < 3")
                recommendations.append("Obtain at least 3 years of historical data for trend analysis")
            elif years_of_data < 5:
                warnings.append(f"Limited historical data: {years_of_data} years")
                recommendations.append("5+ years of data would improve trend reliability")
            
            # Check for missing critical values
            critical_columns = ['pb_ratio', 'book_value', 'market_price']
            missing_critical = []
            
            for col in critical_columns:
                if col in historical_data.columns:
                    missing_pct = historical_data[col].isnull().mean()
                    if missing_pct > 0.3:
                        missing_critical.append(f"{col}: {missing_pct:.1%} missing")
            
            if missing_critical:
                issues.append(f"Critical data missing: {', '.join(missing_critical)}")
                recommendations.append("Fill missing values using interpolation or alternative sources")
            
            # Check for data consistency
            if 'pb_ratio' in historical_data.columns:
                pb_values = historical_data['pb_ratio'].dropna()
                if len(pb_values) > 0:
                    negative_count = (pb_values < 0).sum()
                    extreme_count = (pb_values > 50).sum()  # Unusually high P/B ratios
                    
                    if negative_count > 0:
                        warnings.append(f"Found {negative_count} negative P/B ratios")
                        recommendations.append("Review negative P/B ratios - may indicate losses")
                    
                    if extreme_count > 0:
                        warnings.append(f"Found {extreme_count} extremely high P/B ratios (>50)")
                        recommendations.append("Investigate high P/B ratios for data accuracy")
            
            is_valid = (
                years_of_data >= 2 and
                metrics.completeness >= 0.5 and
                metrics.overall_score >= 0.3
            )
            
            return ValidationResult(
                is_valid=is_valid,
                quality_level=quality_level,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Error validating historical data for {ticker}: {e}")
            return ValidationResult(
                is_valid=False,
                quality_level=DataQualityLevel.UNUSABLE,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Manual data review required"]
            )
    
    def _calculate_quality_metrics(self, industry_stats, peer_data: List[Dict]) -> QualityMetrics:
        """Calculate comprehensive quality metrics for industry data"""
        try:
            # Completeness: ratio of valid data points
            total_peers = len(peer_data)
            valid_pb_count = sum(1 for p in peer_data if p.get('pb_ratio') and p['pb_ratio'] > 0)
            completeness = valid_pb_count / total_peers if total_peers > 0 else 0
            
            # Accuracy: based on cross-validation and source reliability
            source_scores = []
            for peer in peer_data:
                source = peer.get('data_source', 'unknown')
                reliability = self.source_reliability_map.get(source, DataSourceReliability.UNKNOWN)
                if reliability == DataSourceReliability.VERY_HIGH:
                    source_scores.append(1.0)
                elif reliability == DataSourceReliability.HIGH:
                    source_scores.append(0.8)
                elif reliability == DataSourceReliability.MEDIUM:
                    source_scores.append(0.6)
                elif reliability == DataSourceReliability.LOW:
                    source_scores.append(0.4)
                else:
                    source_scores.append(0.2)
            
            source_reliability = np.mean(source_scores) if source_scores else 0.2
            
            # Freshness: based on data age
            freshness_score = self._calculate_freshness_score(peer_data)
            
            # Consistency: statistical consistency checks
            consistency_score = self._calculate_consistency_score(industry_stats, peer_data)
            
            # Sample size adequacy
            sample_size_score = min(total_peers / 20, 1.0)  # Optimal around 20 peers
            
            # Accuracy estimation (simplified)
            accuracy_score = (source_reliability + consistency_score) / 2
            
            # Overall weighted score
            overall_score = (
                completeness * self.quality_weights['completeness'] +
                accuracy_score * self.quality_weights['accuracy'] +
                freshness_score * self.quality_weights['freshness'] +
                consistency_score * self.quality_weights['consistency'] +
                source_reliability * self.quality_weights['source_reliability'] +
                sample_size_score * self.quality_weights['sample_size']
            )
            
            # Confidence level based on sample size and completeness
            confidence_level = min(completeness * sample_size_score * 1.2, 0.95)
            
            return QualityMetrics(
                completeness=completeness,
                accuracy_score=accuracy_score,
                freshness_score=freshness_score,
                consistency_score=consistency_score,
                source_reliability=source_reliability,
                sample_size_score=sample_size_score,
                overall_score=overall_score,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return QualityMetrics()  # Return default (all zeros)
    
    def _calculate_historical_quality_metrics(self, historical_data: pd.DataFrame) -> QualityMetrics:
        """Calculate quality metrics for historical data"""
        try:
            # Completeness
            total_cells = historical_data.size
            non_null_cells = historical_data.count().sum()
            completeness = non_null_cells / total_cells if total_cells > 0 else 0
            
            # Freshness (assume data is ordered by date, most recent first)
            freshness_score = 1.0  # Historical data freshness is about completeness of recent data
            if 'date' in historical_data.columns or 'year' in historical_data.columns:
                # Could implement more sophisticated freshness scoring here
                pass
            
            # Consistency checks
            consistency_score = 0.8  # Default good consistency for historical data
            
            # Source reliability (historical data generally reliable)
            source_reliability = 0.8
            
            # Sample size (years of data)
            years_of_data = len(historical_data)
            sample_size_score = min(years_of_data / 10, 1.0)  # Optimal around 10 years
            
            # Accuracy (based on consistency and completeness)
            accuracy_score = (consistency_score + completeness) / 2
            
            # Overall score
            overall_score = (
                completeness * self.quality_weights['completeness'] +
                accuracy_score * self.quality_weights['accuracy'] +
                freshness_score * self.quality_weights['freshness'] +
                consistency_score * self.quality_weights['consistency'] +
                source_reliability * self.quality_weights['source_reliability'] +
                sample_size_score * self.quality_weights['sample_size']
            )
            
            confidence_level = min(completeness * sample_size_score, 0.95)
            
            return QualityMetrics(
                completeness=completeness,
                accuracy_score=accuracy_score,
                freshness_score=freshness_score,
                consistency_score=consistency_score,
                source_reliability=source_reliability,
                sample_size_score=sample_size_score,
                overall_score=overall_score,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Error calculating historical quality metrics: {e}")
            return QualityMetrics()
    
    def _calculate_freshness_score(self, peer_data: List[Dict]) -> float:
        """Calculate freshness score based on data age"""
        try:
            now = datetime.now()
            age_scores = []
            
            for peer in peer_data:
                last_updated = peer.get('last_updated')
                if last_updated:
                    if isinstance(last_updated, str):
                        last_updated = datetime.fromisoformat(last_updated)
                    
                    age_hours = (now - last_updated).total_seconds() / 3600
                    
                    if age_hours <= 1:
                        age_scores.append(1.0)
                    elif age_hours <= 24:
                        age_scores.append(0.9)
                    elif age_hours <= 168:  # 1 week
                        age_scores.append(0.7)
                    elif age_hours <= 720:  # 1 month
                        age_scores.append(0.5)
                    else:
                        age_scores.append(0.2)
                else:
                    age_scores.append(0.5)  # Unknown age, moderate score
            
            return np.mean(age_scores) if age_scores else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating freshness score: {e}")
            return 0.5
    
    def _calculate_consistency_score(self, industry_stats, peer_data: List[Dict]) -> float:
        """Calculate internal consistency score"""
        try:
            if not peer_data or not industry_stats:
                return 0.0
            
            valid_pb_ratios = [p.get('pb_ratio') for p in peer_data if p.get('pb_ratio') and p['pb_ratio'] > 0]
            
            if len(valid_pb_ratios) < 2:
                return 0.0
            
            # Check if calculated statistics match raw data
            calculated_median = np.median(valid_pb_ratios)
            reported_median = getattr(industry_stats, 'median_pb', None)
            
            if reported_median:
                median_diff = abs(calculated_median - reported_median) / reported_median
                if median_diff < 0.01:  # Within 1%
                    return 1.0
                elif median_diff < 0.05:  # Within 5%
                    return 0.8
                elif median_diff < 0.1:   # Within 10%
                    return 0.6
                else:
                    return 0.3
            
            return 0.7  # Default moderate consistency if can't verify
            
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.5
    
    def _determine_quality_level(self, overall_score: float) -> DataQualityLevel:
        """Determine quality level from overall score"""
        if overall_score >= 0.9:
            return DataQualityLevel.EXCELLENT
        elif overall_score >= 0.7:
            return DataQualityLevel.GOOD
        elif overall_score >= 0.5:
            return DataQualityLevel.ACCEPTABLE
        elif overall_score >= 0.25:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.UNUSABLE
    
    def generate_quality_report(self, dataset_name: str, validation_result: ValidationResult, 
                              additional_metrics: Dict[str, Any] = None) -> QualityReport:
        """Generate comprehensive quality report"""
        try:
            additional_metrics = additional_metrics or {}
            
            return QualityReport(
                dataset_name=dataset_name,
                validation_result=validation_result,
                peer_count=additional_metrics.get('peer_count', 0),
                missing_data_percentage=1.0 - (validation_result.metrics.completeness if validation_result.metrics else 0),
                outlier_percentage=additional_metrics.get('outlier_percentage', 0),
                data_age_days=additional_metrics.get('data_age_days', 0),
                source_breakdown=additional_metrics.get('source_breakdown', {}),
                quality_factors={
                    'completeness': validation_result.metrics.completeness if validation_result.metrics else 0,
                    'accuracy': validation_result.metrics.accuracy_score if validation_result.metrics else 0,
                    'freshness': validation_result.metrics.freshness_score if validation_result.metrics else 0,
                    'consistency': validation_result.metrics.consistency_score if validation_result.metrics else 0,
                    'source_reliability': validation_result.metrics.source_reliability if validation_result.metrics else 0,
                    'sample_size': validation_result.metrics.sample_size_score if validation_result.metrics else 0
                },
                improvement_suggestions=validation_result.recommendations
            )
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return QualityReport(
                dataset_name=dataset_name,
                validation_result=validation_result,
                peer_count=0,
                missing_data_percentage=1.0,
                outlier_percentage=0,
                data_age_days=0,
                improvement_suggestions=["Error generating quality report - manual review required"]
            )