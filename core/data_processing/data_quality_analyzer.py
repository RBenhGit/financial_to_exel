"""
Data Quality Analyzer - Main Integration Interface
================================================

This module provides a simplified interface for integrating the advanced data quality
scoring system with financial calculation engines and the Streamlit interface.

It acts as a facade over the AdvancedDataQualityScorer, providing easy-to-use methods
for the main application components.
"""

import logging
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import pandas as pd
from datetime import datetime

from .advanced_data_quality_scorer import AdvancedDataQualityScorer, QualityMetrics
from .data_validator import DataQualityReport

logger = logging.getLogger(__name__)


@dataclass
class DataQualityIndicator:
    """Simple data quality indicator for UI display"""
    score: float  # 0-100
    level: str  # 'high', 'medium', 'low'
    color: str  # for UI display
    message: str
    details: Dict[str, float]  # breakdown by dimension
    timestamp: datetime


class DataQualityAnalyzer:
    """
    Main interface for data quality analysis and integration.

    This class provides a simplified interface over the advanced data quality
    scoring system, making it easy to integrate with financial calculations
    and UI components.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Data Quality Analyzer

        Args:
            config_path: Optional path to configuration file
        """
        self.scorer = AdvancedDataQualityScorer(config_path)
        logger.info("Data Quality Analyzer initialized")

    def analyze_financial_data(
        self,
        data: Union[Dict[str, Any], pd.DataFrame],
        source_name: str = "Unknown",
        data_context: Optional[Dict[str, Any]] = None
    ) -> DataQualityIndicator:
        """
        Analyze financial data and return a simple quality indicator

        Args:
            data: Financial data to analyze
            source_name: Name of the data source (e.g., "Excel", "yfinance", "FMP")
            data_context: Additional context about the data

        Returns:
            DataQualityIndicator with score and display information
        """
        try:
            # Get detailed quality metrics
            metrics = self.scorer.score_data_quality(
                data=data,
                source_identifier=source_name,
                data_context=data_context or {}
            )

            # Convert to simple indicator
            indicator = self._metrics_to_indicator(metrics, source_name)

            logger.info(f"Data quality analysis completed for {source_name}: {indicator.score:.1f}%")
            return indicator

        except Exception as e:
            logger.error(f"Error analyzing data quality for {source_name}: {e}")
            return self._create_error_indicator(source_name, str(e))

    def get_quality_status(self, data: Any, source_name: str = "Unknown") -> Tuple[str, str, str]:
        """
        Get a quick quality status for display purposes

        Args:
            data: Data to analyze
            source_name: Source identifier

        Returns:
            Tuple of (level, color, message) for quick display
        """
        try:
            indicator = self.analyze_financial_data(data, source_name)
            return indicator.level, indicator.color, indicator.message
        except Exception as e:
            logger.warning(f"Error getting quality status: {e}")
            return "unknown", "#999999", "Quality assessment unavailable"

    def get_data_reliability_score(self, data: Any) -> float:
        """
        Get a simple 0-100 reliability score for data

        Args:
            data: Data to score

        Returns:
            Reliability score (0-100)
        """
        try:
            metrics = self.scorer.score_data_quality(data)
            return metrics.overall_score
        except Exception:
            return 0.0

    def check_data_quality_warnings(self, data: Any, source_name: str = "Unknown") -> list:
        """
        Check for data quality warnings that should be shown to users

        Args:
            data: Data to check
            source_name: Source identifier

        Returns:
            List of warning messages
        """
        warnings = []
        try:
            indicator = self.analyze_financial_data(data, source_name)

            if indicator.score < 60:
                warnings.append(f"⚠️ Low data quality detected ({indicator.score:.0f}%)")

            if indicator.details.get('completeness', 100) < 70:
                warnings.append(f"📊 Incomplete data - {indicator.details['completeness']:.0f}% complete")

            if indicator.details.get('timeliness', 100) < 70:
                warnings.append("📅 Data may be outdated")

            if indicator.details.get('consistency', 100) < 70:
                warnings.append("🔍 Data consistency issues detected")

        except Exception as e:
            logger.warning(f"Error checking quality warnings: {e}")
            warnings.append("⚠️ Unable to assess data quality")

        return warnings

    def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for the quality dashboard display

        Returns:
            Dictionary with dashboard data
        """
        try:
            trends = self.scorer.get_quality_trends()
            predictions = self.scorer.predict_quality_issues()

            # Get recent quality history
            recent_metrics = self.scorer.quality_history[-10:] if self.scorer.quality_history else []

            dashboard_data = {
                'trends': trends,
                'predictions': predictions,
                'recent_scores': [m.overall_score for m in recent_metrics],
                'recent_timestamps': [m.timestamp.isoformat() for m in recent_metrics],
                'total_analyses': len(self.scorer.quality_history),
                'average_score': sum(m.overall_score for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'trends': {'status': 'error', 'message': 'Unable to load trends'},
                'predictions': {'status': 'error', 'message': 'Unable to generate predictions'},
                'recent_scores': [],
                'recent_timestamps': [],
                'total_analyses': 0,
                'average_score': 0
            }

    def _metrics_to_indicator(self, metrics: QualityMetrics, source_name: str) -> DataQualityIndicator:
        """Convert detailed metrics to simple indicator"""

        # Determine quality level and color
        if metrics.overall_score >= 80:
            level = "high"
            color = "#28a745"  # Green
            message = f"High quality data from {source_name}"
        elif metrics.overall_score >= 60:
            level = "medium"
            color = "#ffc107"  # Yellow
            message = f"Acceptable data quality from {source_name}"
        else:
            level = "low"
            color = "#dc3545"  # Red
            message = f"Low quality data from {source_name} - use with caution"

        # Create details breakdown
        details = {
            'completeness': metrics.completeness,
            'consistency': metrics.consistency,
            'accuracy': metrics.accuracy,
            'timeliness': metrics.timeliness,
            'validity': metrics.validity,
            'uniqueness': metrics.uniqueness
        }

        return DataQualityIndicator(
            score=metrics.overall_score,
            level=level,
            color=color,
            message=message,
            details=details,
            timestamp=metrics.timestamp
        )

    def _create_error_indicator(self, source_name: str, error_msg: str) -> DataQualityIndicator:
        """Create indicator for error cases"""
        return DataQualityIndicator(
            score=0.0,
            level="unknown",
            color="#6c757d",  # Gray
            message=f"Unable to assess quality for {source_name}",
            details={},
            timestamp=datetime.now()
        )


# Integration helper functions for easy use in other modules
def quick_quality_check(data: Any, source_name: str = "Unknown") -> Tuple[float, str]:
    """
    Quick quality check function for integration with calculation engines

    Args:
        data: Data to check
        source_name: Source identifier

    Returns:
        Tuple of (score, level) where score is 0-100 and level is 'high'/'medium'/'low'
    """
    try:
        analyzer = DataQualityAnalyzer()
        indicator = analyzer.analyze_financial_data(data, source_name)
        return indicator.score, indicator.level
    except Exception:
        return 0.0, "unknown"


def get_quality_warnings(data: Any, source_name: str = "Unknown") -> list:
    """
    Get quality warnings for data - simplified function for easy integration

    Args:
        data: Data to check
        source_name: Source identifier

    Returns:
        List of warning message strings
    """
    try:
        analyzer = DataQualityAnalyzer()
        return analyzer.check_data_quality_warnings(data, source_name)
    except Exception:
        return ["⚠️ Unable to assess data quality"]


# Export main classes and functions
__all__ = [
    'DataQualityAnalyzer',
    'DataQualityIndicator',
    'quick_quality_check',
    'get_quality_warnings'
]