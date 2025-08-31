"""
Graceful Degradation Module
===========================

This module provides graceful degradation strategies when external data sources fail
or data quality is insufficient. It implements fallback mechanisms to ensure the 
application continues to provide valuable analysis even with limited data.

Features:
- Automatic fallback to historical-only analysis
- Reduced-feature mode for limited data scenarios
- User notification of degraded functionality
- Quality-based analysis selection
- Fallback data source prioritization

Classes:
    GracefulDegradationManager: Main degradation coordinator
    FallbackStrategy: Strategy pattern for different fallback modes
    DegradationLevel: Classification of service degradation levels
    DegradationResult: Result of degradation decision process
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Levels of service degradation"""
    FULL_SERVICE = "full_service"              # All features available
    REDUCED_INDUSTRY = "reduced_industry"      # Limited industry comparisons
    HISTORICAL_ONLY = "historical_only"        # Historical analysis only
    BASIC_METRICS = "basic_metrics"           # Basic calculations only
    MINIMAL_SERVICE = "minimal_service"        # Minimal functionality
    SERVICE_UNAVAILABLE = "service_unavailable"  # Service completely down


class FallbackDataSource(Enum):
    """Priority order for fallback data sources"""
    PRIMARY_API = "primary_api"          # yfinance, Alpha Vantage, etc.
    SECONDARY_API = "secondary_api"      # Backup APIs
    CACHED_DATA = "cached_data"          # Previously cached data
    EXCEL_DATA = "excel_data"            # Local Excel files
    HISTORICAL_DATA = "historical_data"  # Historical-only analysis
    STATIC_DATA = "static_data"          # Static/default values


@dataclass
class DegradationContext:
    """Context information for degradation decisions"""
    failed_services: List[str] = field(default_factory=list)
    data_quality_score: float = 0.0
    available_data_sources: List[FallbackDataSource] = field(default_factory=list)
    user_requirements: Dict[str, Any] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)
    last_successful_update: Optional[datetime] = None
    cache_age_hours: float = 0.0


@dataclass
class DegradationResult:
    """Result of degradation analysis"""
    degradation_level: DegradationLevel
    available_features: List[str]
    disabled_features: List[str]
    fallback_data_sources: List[FallbackDataSource]
    user_message: str
    technical_details: str
    recommendations: List[str] = field(default_factory=list)
    estimated_accuracy: float = 0.0
    data_freshness: str = ""


class FallbackStrategy:
    """Base class for fallback strategies"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority  # Lower number = higher priority
        
    def can_handle(self, context: DegradationContext) -> bool:
        """Check if this strategy can handle the degradation context"""
        raise NotImplementedError
        
    def execute(self, context: DegradationContext) -> DegradationResult:
        """Execute the fallback strategy"""
        raise NotImplementedError


class HistoricalOnlyStrategy(FallbackStrategy):
    """Strategy for falling back to historical analysis only"""
    
    def __init__(self):
        super().__init__("historical_only", priority=1)
        
    def can_handle(self, context: DegradationContext) -> bool:
        """Can handle if we have historical/Excel data available"""
        return (
            FallbackDataSource.HISTORICAL_DATA in context.available_data_sources or
            FallbackDataSource.EXCEL_DATA in context.available_data_sources
        )
        
    def execute(self, context: DegradationContext) -> DegradationResult:
        """Execute historical-only fallback"""
        available_features = [
            "Historical P/B Analysis",
            "Trend Analysis", 
            "Historical Valuation Ranges",
            "Book Value Calculations",
            "Growth Rate Analysis"
        ]
        
        disabled_features = [
            "Real-time Industry Comparisons",
            "Current Market Data",
            "Peer Company Analysis",
            "Live Stock Prices",
            "Current Market Multiples"
        ]
        
        user_message = (
            "Market data temporarily unavailable. Analysis switched to historical data mode. "
            "You'll see historical trends and valuation ranges based on your Excel data."
        )
        
        technical_details = (
            f"API services failed: {', '.join(context.failed_services)}. "
            f"Using historical data with {context.cache_age_hours:.1f} hours cache age."
        )
        
        recommendations = [
            "Review results using historical context only",
            "Consider manual verification of current market conditions", 
            "Check back later for updated industry comparisons",
            "Use conservative assumptions for valuations"
        ]
        
        # Estimate accuracy based on data age and completeness
        if context.cache_age_hours <= 24:
            estimated_accuracy = 0.8
            data_freshness = "Recent"
        elif context.cache_age_hours <= 168:  # 1 week
            estimated_accuracy = 0.7
            data_freshness = "Slightly outdated"
        else:
            estimated_accuracy = 0.6
            data_freshness = "Outdated"
        
        return DegradationResult(
            degradation_level=DegradationLevel.HISTORICAL_ONLY,
            available_features=available_features,
            disabled_features=disabled_features,
            fallback_data_sources=[FallbackDataSource.EXCEL_DATA, FallbackDataSource.HISTORICAL_DATA],
            user_message=user_message,
            technical_details=technical_details,
            recommendations=recommendations,
            estimated_accuracy=estimated_accuracy,
            data_freshness=data_freshness
        )


class CachedDataStrategy(FallbackStrategy):
    """Strategy for using cached data when APIs fail"""
    
    def __init__(self):
        super().__init__("cached_data", priority=2)
        
    def can_handle(self, context: DegradationContext) -> bool:
        """Can handle if cached data is available and relatively fresh"""
        return (
            FallbackDataSource.CACHED_DATA in context.available_data_sources and
            context.cache_age_hours <= 72  # Within 3 days
        )
        
    def execute(self, context: DegradationContext) -> DegradationResult:
        """Execute cached data fallback"""
        if context.cache_age_hours <= 24:
            degradation_level = DegradationLevel.REDUCED_INDUSTRY
            available_features = [
                "Industry Comparisons (Cached)",
                "Historical P/B Analysis", 
                "P/B Percentile Rankings",
                "Basic Valuation Metrics"
            ]
            disabled_features = [
                "Real-time Market Data",
                "Latest Stock Prices",
                "Current Market News"
            ]
            user_message = (
                "Using cached market data from the last 24 hours. "
                "Industry comparisons may be slightly outdated but still reliable."
            )
            estimated_accuracy = 0.85
            data_freshness = "Recent (cached)"
        else:
            degradation_level = DegradationLevel.HISTORICAL_ONLY
            available_features = [
                "Historical P/B Analysis",
                "Trend Analysis",
                "Basic Calculations"
            ]
            disabled_features = [
                "Current Industry Comparisons",
                "Real-time Market Data",
                "Peer Analysis"
            ]
            user_message = (
                "Market data is outdated. Analysis limited to historical trends and cached data."
            )
            estimated_accuracy = 0.65
            data_freshness = "Outdated (cached)"
        
        technical_details = f"Using cached data that is {context.cache_age_hours:.1f} hours old"
        
        recommendations = [
            "Results based on cached data - consider verification",
            "Refresh data when services are available",
            "Use conservative estimates for current valuations"
        ]
        
        return DegradationResult(
            degradation_level=degradation_level,
            available_features=available_features,
            disabled_features=disabled_features,
            fallback_data_sources=[FallbackDataSource.CACHED_DATA, FallbackDataSource.HISTORICAL_DATA],
            user_message=user_message,
            technical_details=technical_details,
            recommendations=recommendations,
            estimated_accuracy=estimated_accuracy,
            data_freshness=data_freshness
        )


class MinimalServiceStrategy(FallbackStrategy):
    """Strategy for providing minimal service when most data is unavailable"""
    
    def __init__(self):
        super().__init__("minimal_service", priority=3)
        
    def can_handle(self, context: DegradationContext) -> bool:
        """Can handle if at least basic Excel data is available"""
        return FallbackDataSource.EXCEL_DATA in context.available_data_sources
        
    def execute(self, context: DegradationContext) -> DegradationResult:
        """Execute minimal service fallback"""
        available_features = [
            "Basic Financial Calculations",
            "Book Value Analysis",
            "Simple Ratios",
            "Excel Data Display"
        ]
        
        disabled_features = [
            "Industry Comparisons",
            "Market Data Integration", 
            "Peer Analysis",
            "Historical Market Trends",
            "Valuation Comparisons"
        ]
        
        user_message = (
            "Most market data services are unavailable. Showing basic calculations "
            "from your Excel data only. Limited analysis available."
        )
        
        technical_details = (
            "All external data sources failed. Operating in offline mode with local data only."
        )
        
        recommendations = [
            "Use results for basic reference only",
            "Manually verify all calculations",
            "Check service status and retry later",
            "Consider alternative data sources"
        ]
        
        return DegradationResult(
            degradation_level=DegradationLevel.MINIMAL_SERVICE,
            available_features=available_features,
            disabled_features=disabled_features,
            fallback_data_sources=[FallbackDataSource.EXCEL_DATA],
            user_message=user_message,
            technical_details=technical_details,
            recommendations=recommendations,
            estimated_accuracy=0.4,
            data_freshness="Local data only"
        )


class GracefulDegradationManager:
    """
    Main manager for handling graceful degradation of services
    """
    
    def __init__(self):
        self.strategies = [
            HistoricalOnlyStrategy(),
            CachedDataStrategy(), 
            MinimalServiceStrategy()
        ]
        
        # Sort strategies by priority (lower number = higher priority)
        self.strategies.sort(key=lambda s: s.priority)
        
        # Track service health over time
        self.service_health_history: Dict[str, List[Tuple[datetime, bool]]] = {}
        
    def assess_degradation(self, context: DegradationContext) -> DegradationResult:
        """
        Assess the situation and determine appropriate degradation strategy
        
        Args:
            context: Current degradation context with failed services and available data
            
        Returns:
            DegradationResult with recommended fallback approach
        """
        try:
            # Try each strategy in priority order
            for strategy in self.strategies:
                if strategy.can_handle(context):
                    logger.info(f"Applying degradation strategy: {strategy.name}")
                    result = strategy.execute(context)
                    
                    # Log the degradation decision
                    self._log_degradation_decision(strategy, context, result)
                    
                    return result
            
            # If no strategy can handle the situation, return service unavailable
            return self._create_service_unavailable_result(context)
            
        except Exception as e:
            logger.error(f"Error in degradation assessment: {e}")
            return self._create_service_unavailable_result(context)
    
    def determine_available_data_sources(self, 
                                       has_excel_data: bool = False,
                                       has_cached_data: bool = False,
                                       cache_age_hours: float = 0,
                                       working_apis: List[str] = None) -> List[FallbackDataSource]:
        """
        Determine which data sources are currently available
        
        Args:
            has_excel_data: Whether local Excel data is available
            has_cached_data: Whether cached data exists
            cache_age_hours: Age of cached data in hours
            working_apis: List of currently working APIs
            
        Returns:
            List of available fallback data sources in priority order
        """
        available_sources = []
        working_apis = working_apis or []
        
        # Check API availability
        if working_apis:
            available_sources.append(FallbackDataSource.PRIMARY_API)
        
        # Check cached data (if reasonably fresh)
        if has_cached_data and cache_age_hours <= 168:  # Within 1 week
            available_sources.append(FallbackDataSource.CACHED_DATA)
        
        # Check local Excel data
        if has_excel_data:
            available_sources.extend([
                FallbackDataSource.EXCEL_DATA,
                FallbackDataSource.HISTORICAL_DATA
            ])
        
        return available_sources
    
    def create_degradation_context(self,
                                 failed_services: List[str] = None,
                                 working_services: List[str] = None,
                                 data_quality_score: float = 0.0,
                                 has_excel_data: bool = False,
                                 has_cached_data: bool = False,
                                 cache_age_hours: float = 0,
                                 last_successful_update: Optional[datetime] = None,
                                 error_messages: List[str] = None) -> DegradationContext:
        """
        Create a degradation context from current system state
        
        Args:
            failed_services: List of service names that have failed
            working_services: List of services still working
            data_quality_score: Overall data quality score (0-1)
            has_excel_data: Whether Excel data is available
            has_cached_data: Whether cached data exists
            cache_age_hours: Age of cached data
            last_successful_update: When data was last successfully updated
            error_messages: List of error messages encountered
            
        Returns:
            DegradationContext object
        """
        failed_services = failed_services or []
        working_services = working_services or []
        error_messages = error_messages or []
        
        available_sources = self.determine_available_data_sources(
            has_excel_data=has_excel_data,
            has_cached_data=has_cached_data,
            cache_age_hours=cache_age_hours,
            working_apis=working_services
        )
        
        return DegradationContext(
            failed_services=failed_services,
            data_quality_score=data_quality_score,
            available_data_sources=available_sources,
            error_messages=error_messages,
            last_successful_update=last_successful_update,
            cache_age_hours=cache_age_hours
        )
    
    def _log_degradation_decision(self, strategy: FallbackStrategy, 
                                context: DegradationContext, 
                                result: DegradationResult):
        """Log the degradation decision for monitoring and debugging"""
        logger.info(f"Degradation applied: {strategy.name} -> {result.degradation_level.value}")
        logger.info(f"Available features: {len(result.available_features)}")
        logger.info(f"Disabled features: {len(result.disabled_features)}")
        logger.info(f"Estimated accuracy: {result.estimated_accuracy:.1%}")
        
        # Track service failures for pattern analysis
        for service in context.failed_services:
            if service not in self.service_health_history:
                self.service_health_history[service] = []
            self.service_health_history[service].append((datetime.now(), False))
    
    def _create_service_unavailable_result(self, context: DegradationContext) -> DegradationResult:
        """Create result for when service is completely unavailable"""
        return DegradationResult(
            degradation_level=DegradationLevel.SERVICE_UNAVAILABLE,
            available_features=[],
            disabled_features=["All Analysis Features"],
            fallback_data_sources=[],
            user_message="Financial analysis services are temporarily unavailable. Please try again later.",
            technical_details=f"All fallback strategies failed. Failed services: {', '.join(context.failed_services)}",
            recommendations=[
                "Check your internet connection",
                "Verify API key configurations", 
                "Try again in a few minutes",
                "Contact support if issues persist"
            ],
            estimated_accuracy=0.0,
            data_freshness="No data available"
        )
    
    def get_service_health_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of service health over time"""
        summary = {}
        
        for service, history in self.service_health_history.items():
            if not history:
                continue
                
            recent_history = [
                status for timestamp, status in history
                if datetime.now() - timestamp <= timedelta(hours=24)
            ]
            
            if recent_history:
                success_rate = sum(recent_history) / len(recent_history)
                summary[service] = {
                    'success_rate_24h': success_rate,
                    'total_calls_24h': len(recent_history),
                    'last_failure': max(
                        timestamp for timestamp, status in history 
                        if not status
                    ) if any(not status for _, status in history) else None
                }
        
        return summary


# Global degradation manager instance
_global_degradation_manager = None


def get_degradation_manager() -> GracefulDegradationManager:
    """Get global degradation manager instance"""
    global _global_degradation_manager
    if _global_degradation_manager is None:
        _global_degradation_manager = GracefulDegradationManager()
    return _global_degradation_manager