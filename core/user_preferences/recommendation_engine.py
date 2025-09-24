"""
Smart Recommendation Engine

Develops intelligent recommendations for preferences based on user behavior,
analysis patterns, and similar user profiles for the financial analysis application.
"""

import json
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
import threading
from collections import defaultdict, Counter
import hashlib

from .user_analytics import (
    UserAnalyticsTracker, AnalysisType, EventType, AnalysisSession,
    UsageStatistics, get_analytics_tracker
)
from .preference_manager import UserPreferenceManager, get_preference_manager
from .user_profile import UserProfile, UserPreferences

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of recommendations the engine can provide"""
    FINANCIAL_PARAMETERS = "financial_parameters"
    COMPANY_SUGGESTIONS = "company_suggestions"
    ANALYSIS_METHODOLOGY = "analysis_methodology"
    UI_PREFERENCES = "ui_preferences"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"


class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Recommendation:
    """Represents a single recommendation"""
    recommendation_id: str
    user_id: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str

    # Recommendation specifics
    suggested_value: Any
    current_value: Any = None
    confidence_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_dismissed: bool = False
    is_applied: bool = False

    # Context
    reasoning: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)

    # A/B testing data
    test_group: Optional[str] = None
    variant: Optional[str] = None


@dataclass
class UserBehaviorPattern:
    """Represents analyzed user behavior patterns"""
    user_id: str
    pattern_type: str
    frequency: float
    last_occurrence: datetime
    trend: str  # "increasing", "decreasing", "stable"

    # Pattern specifics
    typical_parameters: Dict[str, Any] = field(default_factory=dict)
    preferred_companies: List[str] = field(default_factory=list)
    common_analysis_types: List[str] = field(default_factory=list)
    peak_usage_times: List[int] = field(default_factory=list)

    # Performance indicators
    success_rate: float = 0.0
    average_session_duration: float = 0.0
    error_patterns: List[str] = field(default_factory=list)


@dataclass
class SimilarUserProfile:
    """Represents a user profile similar to the target user"""
    user_id: str
    similarity_score: float
    common_patterns: List[str]
    successful_preferences: Dict[str, Any]
    recommended_companies: List[str]
    analysis_preferences: Dict[str, Any]


class SmartRecommendationEngine:
    """
    Intelligent recommendation engine that analyzes user behavior and suggests
    optimal preferences, companies, and methodologies.
    """

    def __init__(
        self,
        data_directory: Optional[str] = None,
        min_confidence_threshold: float = 0.7,
        enable_ab_testing: bool = True
    ):
        """
        Initialize the recommendation engine

        Args:
            data_directory: Directory for storing recommendation data
            min_confidence_threshold: Minimum confidence for recommendations
            enable_ab_testing: Whether to enable A/B testing
        """
        self._lock = threading.Lock()
        self.min_confidence_threshold = min_confidence_threshold
        self.enable_ab_testing = enable_ab_testing

        # Set up data directory
        if data_directory:
            self.data_dir = Path(data_directory)
        else:
            self.data_dir = Path("data") / "recommendations"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Subdirectories
        self.recommendations_dir = self.data_dir / "recommendations"
        self.patterns_dir = self.data_dir / "patterns"
        self.ab_tests_dir = self.data_dir / "ab_tests"

        for dir_path in [self.recommendations_dir, self.patterns_dir, self.ab_tests_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Get dependencies
        self.analytics_tracker = get_analytics_tracker()
        self.preference_manager = get_preference_manager()

        # In-memory caches
        self._user_patterns_cache: Dict[str, List[UserBehaviorPattern]] = {}
        self._recommendations_cache: Dict[str, List[Recommendation]] = {}
        self._similarity_cache: Dict[str, List[SimilarUserProfile]] = {}

        # A/B testing configurations
        self.ab_test_configs = {
            'parameter_recommendations': {
                'variants': ['conservative', 'aggressive', 'balanced'],
                'weights': [0.3, 0.3, 0.4]
            },
            'ui_recommendations': {
                'variants': ['minimal', 'detailed', 'guided'],
                'weights': [0.25, 0.5, 0.25]
            }
        }

        logger.info(f"SmartRecommendationEngine initialized with data directory: {self.data_dir}")

    def analyze_user_behavior(self, user_id: str, analysis_period_days: int = 30) -> List[UserBehaviorPattern]:
        """
        Analyze user behavior patterns over a specified period

        Args:
            user_id: User identifier
            analysis_period_days: Number of days to analyze

        Returns:
            List of identified behavior patterns
        """
        try:
            # Check cache first
            if user_id in self._user_patterns_cache:
                cached_patterns = self._user_patterns_cache[user_id]
                if cached_patterns and (datetime.now() - cached_patterns[0].last_occurrence).days < 1:
                    return cached_patterns

            patterns = []

            # Get user analytics
            stats = self.analytics_tracker.generate_usage_statistics(user_id, analysis_period_days)
            analysis_history = self.analytics_tracker.get_analysis_history(user_id, limit=100)

            if not stats or not analysis_history:
                logger.warning(f"Insufficient data for user {user_id} behavior analysis")
                return patterns

            # 1. Analysis Type Preferences Pattern
            if stats.analyses_by_type:
                most_common_types = sorted(
                    stats.analyses_by_type.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                patterns.append(UserBehaviorPattern(
                    user_id=user_id,
                    pattern_type="analysis_preferences",
                    frequency=sum(stats.analyses_by_type.values()) / analysis_period_days,
                    last_occurrence=datetime.now(),
                    trend=self._calculate_trend(analysis_history, "analysis_type"),
                    common_analysis_types=[t[0] for t in most_common_types[:3]],
                    success_rate=stats.successful_analyses / stats.total_analyses if stats.total_analyses > 0 else 0
                ))

            # 2. Company Analysis Pattern
            company_counter = Counter([session.company_ticker for session in analysis_history])
            if company_counter:
                patterns.append(UserBehaviorPattern(
                    user_id=user_id,
                    pattern_type="company_preferences",
                    frequency=len(company_counter) / analysis_period_days,
                    last_occurrence=datetime.now(),
                    trend=self._calculate_trend(analysis_history, "company"),
                    preferred_companies=list(company_counter.keys())[:10],
                    success_rate=stats.successful_analyses / stats.total_analyses if stats.total_analyses > 0 else 0
                ))

            # 3. Parameter Usage Pattern
            parameter_patterns = self._analyze_parameter_patterns(analysis_history)
            if parameter_patterns:
                patterns.append(UserBehaviorPattern(
                    user_id=user_id,
                    pattern_type="parameter_usage",
                    frequency=len(analysis_history) / analysis_period_days,
                    last_occurrence=datetime.now(),
                    trend="stable",  # Could be enhanced with more sophisticated trend analysis
                    typical_parameters=parameter_patterns,
                    average_session_duration=stats.average_analysis_time_seconds
                ))

            # 4. Performance Pattern
            if stats.average_data_quality_score > 0:
                patterns.append(UserBehaviorPattern(
                    user_id=user_id,
                    pattern_type="performance_optimization",
                    frequency=stats.cache_hit_rate,
                    last_occurrence=datetime.now(),
                    trend=self._calculate_performance_trend(analysis_history),
                    success_rate=stats.average_data_quality_score
                ))

            # Cache results
            self._user_patterns_cache[user_id] = patterns

            # Save patterns to disk
            self._save_user_patterns(user_id, patterns)

            logger.info(f"Analyzed {len(patterns)} behavior patterns for user {user_id}")
            return patterns

        except Exception as e:
            logger.error(f"Failed to analyze user behavior for {user_id}: {e}")
            return []

    def generate_recommendations(self, user_id: str) -> List[Recommendation]:
        """
        Generate personalized recommendations for a user

        Args:
            user_id: User identifier

        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            # Get user data
            user_profile = self.preference_manager.get_user(user_id)
            if not user_profile:
                logger.warning(f"User profile not found for {user_id}")
                return recommendations

            # Analyze behavior patterns
            patterns = self.analyze_user_behavior(user_id)

            # Find similar users
            similar_users = self._find_similar_users(user_id, patterns)

            # Generate different types of recommendations
            recommendations.extend(self._generate_financial_parameter_recommendations(user_id, patterns, similar_users))
            recommendations.extend(self._generate_company_recommendations(user_id, patterns, similar_users))
            recommendations.extend(self._generate_methodology_recommendations(user_id, patterns, similar_users))
            recommendations.extend(self._generate_ui_recommendations(user_id, patterns, user_profile))
            recommendations.extend(self._generate_workflow_recommendations(user_id, patterns))

            # Apply A/B testing if enabled
            if self.enable_ab_testing:
                recommendations = self._apply_ab_testing(user_id, recommendations)

            # Filter by confidence threshold
            filtered_recommendations = [
                r for r in recommendations
                if r.confidence_score >= self.min_confidence_threshold
            ]

            # Sort by priority and confidence
            filtered_recommendations.sort(
                key=lambda x: (x.priority.value, -x.confidence_score)
            )

            # Cache and save
            self._recommendations_cache[user_id] = filtered_recommendations
            self._save_recommendations(user_id, filtered_recommendations)

            logger.info(f"Generated {len(filtered_recommendations)} recommendations for user {user_id}")
            return filtered_recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations for {user_id}: {e}")
            return []

    def _generate_financial_parameter_recommendations(
        self,
        user_id: str,
        patterns: List[UserBehaviorPattern],
        similar_users: List[SimilarUserProfile]
    ) -> List[Recommendation]:
        """Generate financial parameter recommendations"""
        recommendations = []

        # Find parameter usage patterns
        param_pattern = next((p for p in patterns if p.pattern_type == "parameter_usage"), None)
        if not param_pattern:
            return recommendations

        # Common DCF parameters optimization
        if 'dcf' in param_pattern.common_analysis_types:
            typical_params = param_pattern.typical_parameters

            # Discount rate recommendations
            if 'discount_rate' in typical_params:
                current_rate = typical_params['discount_rate']

                # Suggest market-appropriate rates based on similar users
                similar_rates = []
                for similar_user in similar_users[:5]:
                    if 'discount_rate' in similar_user.analysis_preferences:
                        similar_rates.append(similar_user.analysis_preferences['discount_rate'])

                if similar_rates:
                    suggested_rate = np.median(similar_rates)
                    if abs(current_rate - suggested_rate) > 0.01:  # 1% difference threshold
                        recommendations.append(Recommendation(
                            recommendation_id=f"param_discount_rate_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                            user_id=user_id,
                            type=RecommendationType.FINANCIAL_PARAMETERS,
                            priority=RecommendationPriority.MEDIUM,
                            title="Optimize Discount Rate",
                            description=f"Based on similar users' successful analyses, consider adjusting your discount rate from {current_rate:.1%} to {suggested_rate:.1%}",
                            suggested_value=suggested_rate,
                            current_value=current_rate,
                            confidence_score=0.8,
                            reasoning=f"Similar users with comparable analysis patterns use rates around {suggested_rate:.1%}",
                            category="DCF Parameters",
                            tags=["dcf", "discount_rate", "optimization"]
                        ))

            # Growth rate recommendations
            if 'terminal_growth_rate' in typical_params:
                current_growth = typical_params['terminal_growth_rate']
                # Economic-based growth rate suggestions
                if current_growth > 0.04:  # 4% seems high for long-term
                    recommendations.append(Recommendation(
                        recommendation_id=f"param_growth_rate_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        type=RecommendationType.FINANCIAL_PARAMETERS,
                        priority=RecommendationPriority.HIGH,
                        title="Review Terminal Growth Rate",
                        description=f"Your terminal growth rate of {current_growth:.1%} may be optimistic. Consider using 2-3% for mature companies.",
                        suggested_value=0.025,
                        current_value=current_growth,
                        confidence_score=0.9,
                        reasoning="Conservative terminal growth rates (2-3%) are generally more realistic for long-term projections",
                        category="DCF Parameters",
                        tags=["dcf", "growth_rate", "conservative"]
                    ))

        return recommendations

    def _generate_company_recommendations(
        self,
        user_id: str,
        patterns: List[UserBehaviorPattern],
        similar_users: List[SimilarUserProfile]
    ) -> List[Recommendation]:
        """Generate company analysis suggestions"""
        recommendations = []

        # Find company preference patterns
        company_pattern = next((p for p in patterns if p.pattern_type == "company_preferences"), None)
        if not company_pattern:
            return recommendations

        # Get user's analyzed companies
        analyzed_companies = set(company_pattern.preferred_companies)

        # Recommend companies from similar users
        similar_company_suggestions = set()
        for similar_user in similar_users[:3]:  # Top 3 similar users
            for company in similar_user.recommended_companies[:5]:  # Top 5 from each
                if company not in analyzed_companies:
                    similar_company_suggestions.add(company)

        if similar_company_suggestions:
            companies_list = list(similar_company_suggestions)[:5]  # Top 5 suggestions
            recommendations.append(Recommendation(
                recommendation_id=f"companies_similar_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.COMPANY_SUGGESTIONS,
                priority=RecommendationPriority.MEDIUM,
                title="Companies Similar Users Analyze",
                description=f"Users with similar analysis patterns frequently analyze: {', '.join(companies_list)}",
                suggested_value=companies_list,
                current_value=list(analyzed_companies),
                confidence_score=0.75,
                reasoning="Based on analysis patterns of users with similar preferences and successful outcomes",
                category="Company Discovery",
                tags=["companies", "similar_users", "discovery"]
            ))

        # Sector diversification recommendations
        if len(analyzed_companies) >= 3:
            # This would require sector classification - simplified example
            recommendations.append(Recommendation(
                recommendation_id=f"diversification_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.COMPANY_SUGGESTIONS,
                priority=RecommendationPriority.LOW,
                title="Consider Sector Diversification",
                description="You've analyzed companies in similar sectors. Consider exploring different industries for broader insights.",
                suggested_value="Diversify across sectors",
                current_value=f"{len(analyzed_companies)} companies analyzed",
                confidence_score=0.6,
                reasoning="Diversified analysis across sectors provides better market understanding",
                category="Portfolio Analysis",
                tags=["diversification", "sectors", "analysis_breadth"]
            ))

        return recommendations

    def _generate_methodology_recommendations(
        self,
        user_id: str,
        patterns: List[UserBehaviorPattern],
        similar_users: List[SimilarUserProfile]
    ) -> List[Recommendation]:
        """Generate analysis methodology recommendations"""
        recommendations = []

        # Find analysis preferences
        analysis_pattern = next((p for p in patterns if p.pattern_type == "analysis_preferences"), None)
        if not analysis_pattern:
            return recommendations

        common_types = set(analysis_pattern.common_analysis_types)

        # Recommend complementary analysis methods
        if 'dcf' in common_types and 'ddm' not in common_types:
            recommendations.append(Recommendation(
                recommendation_id=f"method_ddm_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.ANALYSIS_METHODOLOGY,
                priority=RecommendationPriority.MEDIUM,
                title="Try Dividend Discount Model (DDM)",
                description="For dividend-paying stocks, DDM analysis complements your DCF approach and provides additional valuation perspective.",
                suggested_value="ddm",
                current_value=list(common_types),
                confidence_score=0.8,
                reasoning="DDM is particularly valuable for dividend-paying companies and provides cross-validation for DCF results",
                category="Analysis Methods",
                tags=["ddm", "valuation", "complementary"]
            ))

        if 'monte_carlo' not in common_types and analysis_pattern.success_rate > 0.8:
            recommendations.append(Recommendation(
                recommendation_id=f"method_monte_carlo_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.ANALYSIS_METHODOLOGY,
                priority=RecommendationPriority.HIGH,
                title="Enhance Analysis with Monte Carlo Simulation",
                description="Given your high analysis success rate, Monte Carlo simulation could provide valuable uncertainty quantification.",
                suggested_value="monte_carlo",
                current_value=list(common_types),
                confidence_score=0.85,
                reasoning="Your consistent analysis success suggests readiness for advanced uncertainty modeling",
                category="Advanced Methods",
                tags=["monte_carlo", "risk", "advanced"]
            ))

        return recommendations

    def _generate_ui_recommendations(
        self,
        user_id: str,
        patterns: List[UserBehaviorPattern],
        user_profile: UserProfile
    ) -> List[Recommendation]:
        """Generate UI and user experience recommendations"""
        recommendations = []

        # Analyze usage frequency for UI optimization
        analysis_pattern = next((p for p in patterns if p.pattern_type == "analysis_preferences"), None)
        if analysis_pattern and analysis_pattern.frequency > 2:  # More than 2 analyses per day
            recommendations.append(Recommendation(
                recommendation_id=f"ui_quick_access_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.UI_PREFERENCES,
                priority=RecommendationPriority.MEDIUM,
                title="Enable Quick Access Dashboard",
                description="With your frequent analysis activity, a quick access dashboard could save time on routine analyses.",
                suggested_value={"quick_access_enabled": True, "show_recent_companies": True},
                current_value={"quick_access_enabled": False},
                confidence_score=0.75,
                reasoning="High-frequency users benefit from streamlined access to common functions",
                category="User Interface",
                tags=["ui", "efficiency", "dashboard"]
            ))

        # Performance-based UI recommendations
        performance_pattern = next((p for p in patterns if p.pattern_type == "performance_optimization"), None)
        if performance_pattern and performance_pattern.success_rate < 0.7:
            recommendations.append(Recommendation(
                recommendation_id=f"ui_guided_mode_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.UI_PREFERENCES,
                priority=RecommendationPriority.HIGH,
                title="Try Guided Analysis Mode",
                description="Guided mode can help improve analysis accuracy and data quality scores.",
                suggested_value={"guided_mode": True, "show_hints": True},
                current_value={"guided_mode": False},
                confidence_score=0.8,
                reasoning="Users with lower success rates often benefit from additional guidance and hints",
                category="User Experience",
                tags=["ui", "guidance", "success_rate"]
            ))

        return recommendations

    def _generate_workflow_recommendations(
        self,
        user_id: str,
        patterns: List[UserBehaviorPattern]
    ) -> List[Recommendation]:
        """Generate workflow optimization recommendations"""
        recommendations = []

        # Check for session duration patterns
        param_pattern = next((p for p in patterns if p.pattern_type == "parameter_usage"), None)
        if param_pattern and param_pattern.average_session_duration > 900:  # More than 15 minutes
            recommendations.append(Recommendation(
                recommendation_id=f"workflow_templates_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.WORKFLOW_OPTIMIZATION,
                priority=RecommendationPriority.MEDIUM,
                title="Use Analysis Templates",
                description="Your long analysis sessions suggest templates could speed up repetitive parameter entry.",
                suggested_value={"use_templates": True, "save_parameter_sets": True},
                current_value={"use_templates": False},
                confidence_score=0.7,
                reasoning="Templates reduce time spent on parameter entry for repeated analysis types",
                category="Workflow",
                tags=["workflow", "templates", "efficiency"]
            ))

        # Cache optimization recommendations
        performance_pattern = next((p for p in patterns if p.pattern_type == "performance_optimization"), None)
        if performance_pattern and performance_pattern.frequency < 0.5:  # Low cache hit rate
            recommendations.append(Recommendation(
                recommendation_id=f"workflow_caching_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                user_id=user_id,
                type=RecommendationType.WORKFLOW_OPTIMIZATION,
                priority=RecommendationPriority.LOW,
                title="Optimize Data Caching",
                description="Enable extended data caching to improve analysis speed for frequently analyzed companies.",
                suggested_value={"extended_caching": True, "cache_duration_hours": 24},
                current_value={"extended_caching": False},
                confidence_score=0.65,
                reasoning="Low cache hit rates indicate potential for performance improvement through better caching",
                category="Performance",
                tags=["workflow", "caching", "performance"]
            ))

        return recommendations

    def _find_similar_users(self, user_id: str, patterns: List[UserBehaviorPattern]) -> List[SimilarUserProfile]:
        """Find users with similar behavior patterns"""
        try:
            # Check cache
            if user_id in self._similarity_cache:
                cached_similar = self._similarity_cache[user_id]
                if cached_similar:
                    return cached_similar

            similar_users = []

            # Get all users
            all_users = self.preference_manager.list_users()

            for user_info in all_users:
                other_user_id = user_info['user_id']
                if other_user_id == user_id:
                    continue

                # Get patterns for other user
                other_patterns = self._load_user_patterns(other_user_id)
                if not other_patterns:
                    continue

                # Calculate similarity
                similarity_score = self._calculate_user_similarity(patterns, other_patterns)

                if similarity_score > 0.5:  # Minimum similarity threshold
                    similar_users.append(SimilarUserProfile(
                        user_id=other_user_id,
                        similarity_score=similarity_score,
                        common_patterns=self._get_common_patterns(patterns, other_patterns),
                        successful_preferences=self._extract_successful_preferences(other_user_id),
                        recommended_companies=self._get_user_companies(other_patterns),
                        analysis_preferences=self._get_analysis_preferences(other_patterns)
                    ))

            # Sort by similarity score
            similar_users.sort(key=lambda x: x.similarity_score, reverse=True)

            # Cache results
            self._similarity_cache[user_id] = similar_users[:10]  # Top 10

            return similar_users[:10]

        except Exception as e:
            logger.error(f"Failed to find similar users for {user_id}: {e}")
            return []

    def apply_recommendation(self, user_id: str, recommendation_id: str, user_feedback: Optional[str] = None) -> bool:
        """
        Apply a recommendation and track the outcome

        Args:
            user_id: User identifier
            recommendation_id: Recommendation to apply
            user_feedback: Optional user feedback

        Returns:
            bool: True if successful
        """
        try:
            # Load recommendation
            recommendation = self._load_recommendation(user_id, recommendation_id)
            if not recommendation:
                logger.warning(f"Recommendation {recommendation_id} not found for user {user_id}")
                return False

            # Mark as applied
            recommendation.is_applied = True
            recommendation.is_dismissed = False

            # Apply the recommendation based on type
            success = False
            if recommendation.type == RecommendationType.FINANCIAL_PARAMETERS:
                success = self._apply_parameter_recommendation(user_id, recommendation)
            elif recommendation.type == RecommendationType.UI_PREFERENCES:
                success = self._apply_ui_recommendation(user_id, recommendation)
            elif recommendation.type == RecommendationType.COMPANY_SUGGESTIONS:
                success = self._apply_company_recommendation(user_id, recommendation)

            # Track application in analytics
            if success:
                self.analytics_tracker.track_event({
                    'event_id': f"recommendation_applied_{recommendation_id}",
                    'user_id': user_id,
                    'event_type': 'recommendation_applied',
                    'timestamp': datetime.now(),
                    'details': {
                        'recommendation_id': recommendation_id,
                        'recommendation_type': recommendation.type.value,
                        'confidence_score': recommendation.confidence_score,
                        'user_feedback': user_feedback
                    }
                })

            # Update recommendation
            self._save_recommendation(recommendation)

            logger.info(f"Applied recommendation {recommendation_id} for user {user_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to apply recommendation {recommendation_id} for user {user_id}: {e}")
            return False

    def dismiss_recommendation(self, user_id: str, recommendation_id: str, reason: Optional[str] = None) -> bool:
        """
        Dismiss a recommendation and learn from user feedback

        Args:
            user_id: User identifier
            recommendation_id: Recommendation to dismiss
            reason: Optional dismissal reason

        Returns:
            bool: True if successful
        """
        try:
            recommendation = self._load_recommendation(user_id, recommendation_id)
            if not recommendation:
                return False

            recommendation.is_dismissed = True

            # Track dismissal for learning
            self.analytics_tracker.track_event({
                'event_id': f"recommendation_dismissed_{recommendation_id}",
                'user_id': user_id,
                'event_type': 'recommendation_dismissed',
                'timestamp': datetime.now(),
                'details': {
                    'recommendation_id': recommendation_id,
                    'recommendation_type': recommendation.type.value,
                    'confidence_score': recommendation.confidence_score,
                    'dismissal_reason': reason
                }
            })

            self._save_recommendation(recommendation)
            return True

        except Exception as e:
            logger.error(f"Failed to dismiss recommendation {recommendation_id}: {e}")
            return False

    def get_user_recommendations(self, user_id: str, include_dismissed: bool = False) -> List[Recommendation]:
        """
        Get current recommendations for a user

        Args:
            user_id: User identifier
            include_dismissed: Whether to include dismissed recommendations

        Returns:
            List of recommendations
        """
        try:
            # Check cache first
            if user_id in self._recommendations_cache:
                recommendations = self._recommendations_cache[user_id]
            else:
                recommendations = self._load_user_recommendations(user_id)

            if not include_dismissed:
                recommendations = [r for r in recommendations if not r.is_dismissed]

            # Filter expired recommendations
            now = datetime.now()
            recommendations = [r for r in recommendations if not r.expires_at or r.expires_at > now]

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get recommendations for user {user_id}: {e}")
            return []

    # Helper methods
    def _calculate_trend(self, sessions: List[AnalysisSession], metric: str) -> str:
        """Calculate trend for a specific metric"""
        if len(sessions) < 3:
            return "stable"

        # Simple trend calculation based on recent vs older sessions
        recent_sessions = sessions[:len(sessions)//2]
        older_sessions = sessions[len(sessions)//2:]

        if metric == "analysis_type":
            recent_types = len(set(s.analysis_type.value for s in recent_sessions))
            older_types = len(set(s.analysis_type.value for s in older_sessions))
            if recent_types > older_types:
                return "increasing"
            elif recent_types < older_types:
                return "decreasing"

        return "stable"

    def _calculate_performance_trend(self, sessions: List[AnalysisSession]) -> str:
        """Calculate performance trend"""
        if len(sessions) < 5:
            return "stable"

        recent_success = sum(1 for s in sessions[:len(sessions)//2] if s.success)
        older_success = sum(1 for s in sessions[len(sessions)//2:] if s.success)

        recent_rate = recent_success / (len(sessions)//2)
        older_rate = older_success / (len(sessions) - len(sessions)//2)

        if recent_rate > older_rate + 0.1:
            return "improving"
        elif recent_rate < older_rate - 0.1:
            return "declining"
        return "stable"

    def _analyze_parameter_patterns(self, sessions: List[AnalysisSession]) -> Dict[str, Any]:
        """Analyze common parameter usage patterns"""
        parameter_usage = defaultdict(list)

        for session in sessions:
            for param, value in session.parameters.items():
                if isinstance(value, (int, float)):
                    parameter_usage[param].append(value)

        patterns = {}
        for param, values in parameter_usage.items():
            if len(values) >= 3:
                patterns[param] = np.median(values)

        return patterns

    def _calculate_user_similarity(
        self,
        patterns1: List[UserBehaviorPattern],
        patterns2: List[UserBehaviorPattern]
    ) -> float:
        """Calculate similarity score between two users' patterns"""
        if not patterns1 or not patterns2:
            return 0.0

        # Create pattern maps
        patterns1_map = {p.pattern_type: p for p in patterns1}
        patterns2_map = {p.pattern_type: p for p in patterns2}

        common_patterns = set(patterns1_map.keys()) & set(patterns2_map.keys())
        if not common_patterns:
            return 0.0

        similarity_scores = []

        for pattern_type in common_patterns:
            p1 = patterns1_map[pattern_type]
            p2 = patterns2_map[pattern_type]

            # Calculate pattern-specific similarity
            if pattern_type == "analysis_preferences":
                common_types = set(p1.common_analysis_types) & set(p2.common_analysis_types)
                type_similarity = len(common_types) / max(len(p1.common_analysis_types), len(p2.common_analysis_types), 1)
                similarity_scores.append(type_similarity)

            elif pattern_type == "company_preferences":
                common_companies = set(p1.preferred_companies) & set(p2.preferred_companies)
                company_similarity = len(common_companies) / max(len(p1.preferred_companies), len(p2.preferred_companies), 1)
                similarity_scores.append(company_similarity)

            elif pattern_type == "performance_optimization":
                success_diff = abs(p1.success_rate - p2.success_rate)
                success_similarity = 1.0 - min(success_diff, 1.0)
                similarity_scores.append(success_similarity)

        return np.mean(similarity_scores) if similarity_scores else 0.0

    def _get_common_patterns(
        self,
        patterns1: List[UserBehaviorPattern],
        patterns2: List[UserBehaviorPattern]
    ) -> List[str]:
        """Get list of common pattern types"""
        types1 = {p.pattern_type for p in patterns1}
        types2 = {p.pattern_type for p in patterns2}
        return list(types1 & types2)

    def _extract_successful_preferences(self, user_id: str) -> Dict[str, Any]:
        """Extract successful preferences from user's history"""
        # This would analyze successful sessions and extract common parameters
        # Simplified implementation
        return {}

    def _get_user_companies(self, patterns: List[UserBehaviorPattern]) -> List[str]:
        """Extract user's preferred companies from patterns"""
        for pattern in patterns:
            if pattern.pattern_type == "company_preferences":
                return pattern.preferred_companies[:10]
        return []

    def _get_analysis_preferences(self, patterns: List[UserBehaviorPattern]) -> Dict[str, Any]:
        """Extract analysis preferences from patterns"""
        for pattern in patterns:
            if pattern.pattern_type == "parameter_usage":
                return pattern.typical_parameters
        return {}

    def _apply_ab_testing(self, user_id: str, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Apply A/B testing to recommendations"""
        if not self.enable_ab_testing:
            return recommendations

        # Simple A/B testing assignment based on user_id hash
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)

        for recommendation in recommendations:
            if recommendation.type.value in self.ab_test_configs:
                config = self.ab_test_configs[recommendation.type.value]
                variant_index = user_hash % len(config['variants'])
                recommendation.test_group = "ab_test"
                recommendation.variant = config['variants'][variant_index]

        return recommendations

    def _apply_parameter_recommendation(self, user_id: str, recommendation: Recommendation) -> bool:
        """Apply parameter recommendation to user preferences"""
        # This would update user's default parameters
        # Implementation depends on how preferences are structured
        return True

    def _apply_ui_recommendation(self, user_id: str, recommendation: Recommendation) -> bool:
        """Apply UI recommendation to user preferences"""
        # This would update UI preferences
        return True

    def _apply_company_recommendation(self, user_id: str, recommendation: Recommendation) -> bool:
        """Apply company recommendation (e.g., add to favorites)"""
        # This would add suggested companies to user's watchlist
        return True

    # File I/O methods
    def _save_user_patterns(self, user_id: str, patterns: List[UserBehaviorPattern]) -> bool:
        """Save user behavior patterns to disk"""
        try:
            patterns_file = self.patterns_dir / f"patterns_{user_id}.json"
            patterns_data = [asdict(pattern) for pattern in patterns]

            # Handle datetime serialization
            for pattern_data in patterns_data:
                if 'last_occurrence' in pattern_data:
                    pattern_data['last_occurrence'] = pattern_data['last_occurrence'].isoformat()

            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, default=str)

            return True
        except Exception as e:
            logger.error(f"Failed to save patterns for user {user_id}: {e}")
            return False

    def _load_user_patterns(self, user_id: str) -> List[UserBehaviorPattern]:
        """Load user behavior patterns from disk"""
        try:
            patterns_file = self.patterns_dir / f"patterns_{user_id}.json"
            if not patterns_file.exists():
                return []

            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)

            patterns = []
            for data in patterns_data:
                if 'last_occurrence' in data and isinstance(data['last_occurrence'], str):
                    data['last_occurrence'] = datetime.fromisoformat(data['last_occurrence'])
                patterns.append(UserBehaviorPattern(**data))

            return patterns
        except Exception as e:
            logger.error(f"Failed to load patterns for user {user_id}: {e}")
            return []

    def _save_recommendations(self, user_id: str, recommendations: List[Recommendation]) -> bool:
        """Save recommendations to disk"""
        try:
            rec_file = self.recommendations_dir / f"recommendations_{user_id}.json"
            rec_data = [asdict(rec) for rec in recommendations]

            # Handle datetime and enum serialization
            for data in rec_data:
                data['created_at'] = data['created_at'].isoformat()
                if data['expires_at']:
                    data['expires_at'] = data['expires_at'].isoformat()
                data['type'] = data['type'].value
                data['priority'] = data['priority'].value

            with open(rec_file, 'w', encoding='utf-8') as f:
                json.dump(rec_data, f, indent=2, default=str)

            return True
        except Exception as e:
            logger.error(f"Failed to save recommendations for user {user_id}: {e}")
            return False

    def _load_user_recommendations(self, user_id: str) -> List[Recommendation]:
        """Load user recommendations from disk"""
        try:
            rec_file = self.recommendations_dir / f"recommendations_{user_id}.json"
            if not rec_file.exists():
                return []

            with open(rec_file, 'r', encoding='utf-8') as f:
                rec_data = json.load(f)

            recommendations = []
            for data in rec_data:
                # Handle datetime conversion
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                if data['expires_at']:
                    data['expires_at'] = datetime.fromisoformat(data['expires_at'])

                # Handle enum conversion
                data['type'] = RecommendationType(data['type'])
                data['priority'] = RecommendationPriority(data['priority'])

                recommendations.append(Recommendation(**data))

            return recommendations
        except Exception as e:
            logger.error(f"Failed to load recommendations for user {user_id}: {e}")
            return []

    def _load_recommendation(self, user_id: str, recommendation_id: str) -> Optional[Recommendation]:
        """Load a specific recommendation"""
        recommendations = self._load_user_recommendations(user_id)
        for rec in recommendations:
            if rec.recommendation_id == recommendation_id:
                return rec
        return None

    def _save_recommendation(self, recommendation: Recommendation) -> bool:
        """Save a single recommendation"""
        user_id = recommendation.user_id
        recommendations = self._load_user_recommendations(user_id)

        # Update or add recommendation
        updated = False
        for i, rec in enumerate(recommendations):
            if rec.recommendation_id == recommendation.recommendation_id:
                recommendations[i] = recommendation
                updated = True
                break

        if not updated:
            recommendations.append(recommendation)

        return self._save_recommendations(user_id, recommendations)


# Global instance
_recommendation_engine: Optional[SmartRecommendationEngine] = None


def get_recommendation_engine(
    data_directory: Optional[str] = None,
    min_confidence_threshold: float = 0.7,
    enable_ab_testing: bool = True
) -> SmartRecommendationEngine:
    """
    Get the global recommendation engine instance

    Args:
        data_directory: Directory for recommendation data
        min_confidence_threshold: Minimum confidence for recommendations
        enable_ab_testing: Whether to enable A/B testing

    Returns:
        SmartRecommendationEngine instance
    """
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = SmartRecommendationEngine(
            data_directory, min_confidence_threshold, enable_ab_testing
        )
    return _recommendation_engine


def set_recommendation_engine(engine: SmartRecommendationEngine) -> None:
    """Set a custom recommendation engine instance"""
    global _recommendation_engine
    _recommendation_engine = engine