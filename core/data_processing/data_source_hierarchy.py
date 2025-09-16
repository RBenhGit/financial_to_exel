"""
Enhanced Data Source Hierarchy Manager
=====================================

Implements intelligent data source fallback with quality scoring, health monitoring,
and dynamic source selection for resilient financial data acquisition.

Features:
- Dynamic data source quality scoring
- Intelligent fallback hierarchy based on performance metrics
- Connection pooling and rate limiting integration
- Comprehensive error classification and recovery
- Data source health monitoring with circuit breaker patterns
"""

import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Available data source types with priority and characteristics"""
    EXCEL = "excel"
    YFINANCE = "yfinance"
    FMP = "fmp"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    FINNHUB = "finnhub"


class DataQuality(Enum):
    """Data quality levels for scoring"""
    EXCELLENT = 5
    GOOD = 4
    ADEQUATE = 3
    POOR = 2
    UNRELIABLE = 1


@dataclass
class DataSourceMetrics:
    """Performance and quality metrics for a data source"""
    source_type: DataSourceType
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    data_completeness: float = 1.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    cost_per_request: float = 0.0
    rate_limit_remaining: int = 1000
    is_available: bool = True
    quality_score: float = 5.0

    def update_success(self, response_time: float, completeness: float = 1.0):
        """Update metrics after successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()

        # Update running averages
        self.success_rate = self.successful_requests / self.total_requests
        self.avg_response_time = (
            (self.avg_response_time * (self.successful_requests - 1) + response_time)
            / self.successful_requests
        )
        self.data_completeness = min(
            (self.data_completeness * 0.9 + completeness * 0.1), 1.0
        )
        self._update_quality_score()

    def update_failure(self):
        """Update metrics after failed request"""
        self.total_requests += 1
        self.consecutive_failures += 1
        self.last_failure = datetime.now()

        if self.total_requests > 0:
            self.success_rate = self.successful_requests / self.total_requests

        # Degrade quality score on consecutive failures
        if self.consecutive_failures >= 3:
            self.quality_score = max(1.0, self.quality_score - 0.5)

        self._update_quality_score()

    def _update_quality_score(self):
        """Calculate composite quality score based on multiple factors"""
        # Weight factors: reliability (40%), speed (20%), completeness (25%), availability (15%)
        reliability_score = self.success_rate * 5
        speed_score = max(1.0, 5.0 - (self.avg_response_time / 2.0))  # Penalize slow responses
        completeness_score = self.data_completeness * 5
        availability_score = 5.0 if self.is_available else 1.0

        self.quality_score = (
            reliability_score * 0.4 +
            speed_score * 0.2 +
            completeness_score * 0.25 +
            availability_score * 0.15
        )

        # Apply penalty for consecutive failures
        if self.consecutive_failures > 0:
            penalty = min(2.0, self.consecutive_failures * 0.5)
            self.quality_score = max(1.0, self.quality_score - penalty)


@dataclass
class FallbackTrigger:
    """Conditions that trigger fallback to next data source"""
    max_response_time: float = 10.0  # seconds
    min_success_rate: float = 0.8
    max_consecutive_failures: int = 3
    min_data_completeness: float = 0.5
    rate_limit_threshold: int = 10  # requests remaining

    def should_fallback(self, metrics: DataSourceMetrics) -> Tuple[bool, str]:
        """
        Check if fallback should be triggered based on metrics

        Returns:
            Tuple[bool, str]: (should_fallback, reason)
        """
        if not metrics.is_available:
            return True, "source_unavailable"

        if metrics.consecutive_failures >= self.max_consecutive_failures:
            return True, f"consecutive_failures_{metrics.consecutive_failures}"

        if metrics.success_rate < self.min_success_rate and metrics.total_requests > 5:
            return True, f"low_success_rate_{metrics.success_rate:.2f}"

        if metrics.avg_response_time > self.max_response_time and metrics.successful_requests > 3:
            return True, f"slow_response_{metrics.avg_response_time:.1f}s"

        if metrics.data_completeness < self.min_data_completeness:
            return True, f"incomplete_data_{metrics.data_completeness:.2f}"

        if metrics.rate_limit_remaining < self.rate_limit_threshold:
            return True, f"rate_limit_low_{metrics.rate_limit_remaining}"

        return False, ""


class DataSourceHierarchy:
    """
    Intelligent data source hierarchy manager with quality-based fallback selection
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration"""
        self.config = config or {}
        self.metrics: Dict[DataSourceType, DataSourceMetrics] = {}
        self.fallback_trigger = FallbackTrigger()
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize default data source metrics"""
        # Define base hierarchy with default priorities and characteristics
        source_defaults = {
            DataSourceType.EXCEL: {
                'cost_per_request': 0.0,
                'quality_score': 5.0,
                'is_available': True
            },
            DataSourceType.YFINANCE: {
                'cost_per_request': 0.0,
                'quality_score': 4.5,
                'is_available': True
            },
            DataSourceType.FMP: {
                'cost_per_request': 0.01,
                'quality_score': 4.0,
                'is_available': self.config.get('fmp_api_key') is not None
            },
            DataSourceType.ALPHA_VANTAGE: {
                'cost_per_request': 0.0,
                'quality_score': 3.5,
                'is_available': self.config.get('alpha_vantage_api_key') is not None
            },
            DataSourceType.POLYGON: {
                'cost_per_request': 0.003,
                'quality_score': 4.8,
                'is_available': self.config.get('polygon_api_key') is not None
            },
            DataSourceType.FINNHUB: {
                'cost_per_request': 0.0,
                'quality_score': 3.8,
                'is_available': self.config.get('finnhub_api_key') is not None
            }
        }

        for source_type, defaults in source_defaults.items():
            self.metrics[source_type] = DataSourceMetrics(
                source_type=source_type,
                **defaults
            )

        logger.info(f"Initialized {len(self.metrics)} data sources")

    def get_optimal_source_hierarchy(self, exclude: List[DataSourceType] = None) -> List[DataSourceType]:
        """
        Get optimal data source hierarchy based on current quality scores and availability

        Args:
            exclude: List of sources to exclude from hierarchy

        Returns:
            List[DataSourceType]: Ordered list of sources to try
        """
        exclude = exclude or []
        available_sources = []

        for source_type, metrics in self.metrics.items():
            if source_type in exclude:
                continue

            # Check if source should be excluded due to fallback triggers
            should_fallback, reason = self.fallback_trigger.should_fallback(metrics)
            if should_fallback:
                logger.debug(f"Excluding {source_type.value} from hierarchy: {reason}")
                continue

            available_sources.append((source_type, metrics))

        # Sort by composite score (quality score weighted by cost and availability)
        def calculate_composite_score(source_metrics: DataSourceMetrics) -> float:
            quality = source_metrics.quality_score
            cost_penalty = min(2.0, source_metrics.cost_per_request * 100)
            availability_bonus = 1.0 if source_metrics.is_available else -5.0
            recency_bonus = 0.0

            # Bonus for recent successful requests
            if source_metrics.last_success:
                hours_since_success = (datetime.now() - source_metrics.last_success).total_seconds() / 3600
                recency_bonus = max(0, 1.0 - (hours_since_success / 24))  # Decay over 24 hours

            return quality - cost_penalty + availability_bonus + recency_bonus

        available_sources.sort(key=lambda x: calculate_composite_score(x[1]), reverse=True)

        hierarchy = [source for source, _ in available_sources]

        logger.info(f"Optimal hierarchy: {[s.value for s in hierarchy]}")
        return hierarchy

    def record_request_result(self, source_type: DataSourceType, success: bool,
                            response_time: float = 0.0, data_completeness: float = 1.0,
                            rate_limit_remaining: int = None):
        """
        Record the result of a data request for metrics tracking

        Args:
            source_type: The data source that was used
            success: Whether the request was successful
            response_time: Response time in seconds
            data_completeness: Fraction of requested data that was returned (0.0-1.0)
            rate_limit_remaining: Number of API requests remaining
        """
        if source_type not in self.metrics:
            logger.warning(f"Unknown source type: {source_type}")
            return

        metrics = self.metrics[source_type]

        if rate_limit_remaining is not None:
            metrics.rate_limit_remaining = rate_limit_remaining

        if success:
            metrics.update_success(response_time, data_completeness)
            logger.debug(f"Updated {source_type.value} metrics - Success rate: {metrics.success_rate:.2f}, "
                        f"Quality score: {metrics.quality_score:.2f}")
        else:
            metrics.update_failure()
            logger.debug(f"Updated {source_type.value} metrics - Consecutive failures: {metrics.consecutive_failures}, "
                        f"Quality score: {metrics.quality_score:.2f}")

    def get_source_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for all data sources

        Returns:
            Dict containing health metrics for each source
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'recommendations': []
        }

        for source_type, metrics in self.metrics.items():
            source_report = {
                'available': metrics.is_available,
                'quality_score': metrics.quality_score,
                'success_rate': metrics.success_rate,
                'avg_response_time': metrics.avg_response_time,
                'data_completeness': metrics.data_completeness,
                'consecutive_failures': metrics.consecutive_failures,
                'total_requests': metrics.total_requests,
                'cost_per_request': metrics.cost_per_request,
                'rate_limit_remaining': metrics.rate_limit_remaining,
                'last_success': metrics.last_success.isoformat() if metrics.last_success else None,
                'last_failure': metrics.last_failure.isoformat() if metrics.last_failure else None
            }

            # Add health status
            if metrics.quality_score >= 4.5:
                source_report['status'] = 'excellent'
            elif metrics.quality_score >= 3.5:
                source_report['status'] = 'good'
            elif metrics.quality_score >= 2.5:
                source_report['status'] = 'degraded'
            else:
                source_report['status'] = 'critical'

            # Check for fallback triggers
            should_fallback, reason = self.fallback_trigger.should_fallback(metrics)
            if should_fallback:
                source_report['fallback_triggered'] = reason
                report['recommendations'].append(f"Consider excluding {source_type.value}: {reason}")

            report['sources'][source_type.value] = source_report

        return report

    def reset_source_metrics(self, source_type: DataSourceType):
        """Reset metrics for a specific source (useful after fixing issues)"""
        if source_type in self.metrics:
            defaults = {
                'source_type': source_type,
                'cost_per_request': self.metrics[source_type].cost_per_request,
                'is_available': True
            }
            self.metrics[source_type] = DataSourceMetrics(**defaults)
            logger.info(f"Reset metrics for {source_type.value}")

    def update_source_availability(self, source_type: DataSourceType, available: bool, reason: str = ""):
        """Update the availability status of a data source"""
        if source_type in self.metrics:
            self.metrics[source_type].is_available = available
            if not available and reason:
                logger.warning(f"{source_type.value} marked unavailable: {reason}")
            elif available:
                logger.info(f"{source_type.value} marked available")