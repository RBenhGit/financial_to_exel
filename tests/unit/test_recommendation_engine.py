"""
Tests for the Smart Recommendation Engine

Tests comprehensive functionality of user behavior analysis, pattern recognition,
and intelligent recommendation generation in the financial analysis application.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from core.user_preferences.recommendation_engine import (
    SmartRecommendationEngine, RecommendationType, RecommendationPriority,
    Recommendation, UserBehaviorPattern, SimilarUserProfile,
    get_recommendation_engine
)
from core.user_preferences.user_analytics import (
    AnalysisType, AnalysisSession, UsageStatistics,
    UserAnalyticsTracker
)
from core.user_preferences.preference_manager import UserPreferenceManager
from core.user_preferences.user_profile import UserProfile, create_default_user_profile


class TestSmartRecommendationEngine:
    """Test suite for SmartRecommendationEngine"""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_analytics_tracker(self):
        """Mock analytics tracker"""
        tracker = Mock(spec=UserAnalyticsTracker)
        return tracker

    @pytest.fixture
    def mock_preference_manager(self):
        """Mock preference manager"""
        manager = Mock(spec=UserPreferenceManager)
        return manager

    @pytest.fixture
    def recommendation_engine(self, temp_directory):
        """Create recommendation engine for testing"""
        with patch('core.user_preferences.recommendation_engine.get_analytics_tracker') as mock_analytics, \
             patch('core.user_preferences.recommendation_engine.get_preference_manager') as mock_manager:

            mock_analytics.return_value = Mock(spec=UserAnalyticsTracker)
            mock_manager.return_value = Mock(spec=UserPreferenceManager)

            engine = SmartRecommendationEngine(
                data_directory=temp_directory,
                min_confidence_threshold=0.6,
                enable_ab_testing=True
            )
            return engine

    @pytest.fixture
    def sample_user_profile(self):
        """Create sample user profile"""
        return create_default_user_profile("test_user", "Test User", "test@example.com")

    @pytest.fixture
    def sample_analysis_sessions(self):
        """Create sample analysis sessions"""
        sessions = []
        base_time = datetime.now() - timedelta(days=30)

        for i in range(10):
            session = AnalysisSession(
                session_id=f"session_{i}",
                analysis_type=AnalysisType.DCF,
                company_ticker="AAPL",
                start_time=base_time + timedelta(days=i),
                end_time=base_time + timedelta(days=i, hours=1),
                success=True,
                parameters={
                    'discount_rate': 0.1 + (i * 0.001),
                    'terminal_growth_rate': 0.025,
                    'projection_years': 5
                },
                execution_time_seconds=300 + (i * 10)
            )
            sessions.append(session)

        return sessions

    @pytest.fixture
    def sample_usage_statistics(self):
        """Create sample usage statistics"""
        return UsageStatistics(
            user_id="test_user",
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_analyses=15,
            successful_analyses=12,
            failed_analyses=3,
            analyses_by_type={"dcf": 10, "ddm": 3, "pb_ratio": 2},
            average_analysis_time_seconds=350.0,
            unique_companies_analyzed=5,
            average_data_quality_score=0.85,
            cache_hit_rate=0.7
        )

    def test_initialization(self, temp_directory):
        """Test recommendation engine initialization"""
        with patch('core.user_preferences.recommendation_engine.get_analytics_tracker') as mock_analytics, \
             patch('core.user_preferences.recommendation_engine.get_preference_manager') as mock_manager:

            mock_analytics.return_value = Mock()
            mock_manager.return_value = Mock()

            engine = SmartRecommendationEngine(
                data_directory=temp_directory,
                min_confidence_threshold=0.8,
                enable_ab_testing=False
            )

            assert engine.data_dir == Path(temp_directory)
            assert engine.min_confidence_threshold == 0.8
            assert engine.enable_ab_testing is False
            assert engine.recommendations_dir.exists()
            assert engine.patterns_dir.exists()
            assert engine.ab_tests_dir.exists()

    def test_analyze_user_behavior(self, recommendation_engine, sample_analysis_sessions, sample_usage_statistics):
        """Test user behavior analysis"""
        # Mock the analytics tracker methods
        recommendation_engine.analytics_tracker.generate_usage_statistics.return_value = sample_usage_statistics
        recommendation_engine.analytics_tracker.get_analysis_history.return_value = sample_analysis_sessions

        patterns = recommendation_engine.analyze_user_behavior("test_user", 30)

        assert len(patterns) > 0

        # Check for expected pattern types
        pattern_types = {pattern.pattern_type for pattern in patterns}
        expected_types = {"analysis_preferences", "company_preferences", "parameter_usage", "performance_optimization"}
        assert pattern_types.issubset(expected_types)

        # Verify pattern data
        analysis_pattern = next((p for p in patterns if p.pattern_type == "analysis_preferences"), None)
        assert analysis_pattern is not None
        assert analysis_pattern.user_id == "test_user"
        assert "dcf" in analysis_pattern.common_analysis_types

    def test_generate_recommendations(self, recommendation_engine, sample_user_profile, sample_analysis_sessions, sample_usage_statistics):
        """Test recommendation generation"""
        # Setup mocks
        recommendation_engine.preference_manager.get_user.return_value = sample_user_profile
        recommendation_engine.analytics_tracker.generate_usage_statistics.return_value = sample_usage_statistics
        recommendation_engine.analytics_tracker.get_analysis_history.return_value = sample_analysis_sessions

        # Mock patterns
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="parameter_usage",
                frequency=1.5,
                last_occurrence=datetime.now(),
                trend="stable",
                typical_parameters={'discount_rate': 0.12, 'terminal_growth_rate': 0.035},
                common_analysis_types=["dcf"],
                success_rate=0.8
            )
        ]

        with patch.object(recommendation_engine, 'analyze_user_behavior', return_value=patterns), \
             patch.object(recommendation_engine, '_find_similar_users', return_value=[]):

            recommendations = recommendation_engine.generate_recommendations("test_user")

            assert isinstance(recommendations, list)

            # Check if we get recommendations when patterns exist
            if recommendations:
                for rec in recommendations:
                    assert isinstance(rec, Recommendation)
                    assert rec.user_id == "test_user"
                    assert rec.confidence_score >= recommendation_engine.min_confidence_threshold

    def test_financial_parameter_recommendations(self, recommendation_engine):
        """Test financial parameter recommendation generation"""
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="parameter_usage",
                frequency=1.0,
                last_occurrence=datetime.now(),
                trend="stable",
                typical_parameters={'discount_rate': 0.15, 'terminal_growth_rate': 0.05},
                common_analysis_types=["dcf"],
                success_rate=0.8
            )
        ]

        similar_users = [
            SimilarUserProfile(
                user_id="similar_user1",
                similarity_score=0.8,
                common_patterns=["parameter_usage"],
                successful_preferences={},
                recommended_companies=[],
                analysis_preferences={'discount_rate': 0.10}
            )
        ]

        recommendations = recommendation_engine._generate_financial_parameter_recommendations(
            "test_user", patterns, similar_users
        )

        # Should suggest discount rate adjustment
        discount_rate_recs = [r for r in recommendations if 'discount_rate' in r.title.lower()]
        assert len(discount_rate_recs) > 0

        # Should suggest terminal growth rate adjustment
        growth_rate_recs = [r for r in recommendations if 'growth' in r.title.lower()]
        assert len(growth_rate_recs) > 0

    def test_company_recommendations(self, recommendation_engine):
        """Test company recommendation generation"""
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="company_preferences",
                frequency=1.0,
                last_occurrence=datetime.now(),
                trend="stable",
                preferred_companies=["AAPL", "MSFT", "GOOGL"],
                success_rate=0.8
            )
        ]

        similar_users = [
            SimilarUserProfile(
                user_id="similar_user1",
                similarity_score=0.8,
                common_patterns=["company_preferences"],
                successful_preferences={},
                recommended_companies=["TSLA", "AMZN", "META"],
                analysis_preferences={}
            )
        ]

        recommendations = recommendation_engine._generate_company_recommendations(
            "test_user", patterns, similar_users
        )

        # Should suggest companies from similar users
        company_recs = [r for r in recommendations if r.type == RecommendationType.COMPANY_SUGGESTIONS]
        assert len(company_recs) > 0

    def test_methodology_recommendations(self, recommendation_engine):
        """Test methodology recommendation generation"""
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="analysis_preferences",
                frequency=1.0,
                last_occurrence=datetime.now(),
                trend="stable",
                common_analysis_types=["dcf"],
                success_rate=0.9
            )
        ]

        recommendations = recommendation_engine._generate_methodology_recommendations(
            "test_user", patterns, []
        )

        # Should suggest complementary methods
        method_recs = [r for r in recommendations if r.type == RecommendationType.ANALYSIS_METHODOLOGY]
        assert len(method_recs) > 0

        # Check for DDM or Monte Carlo suggestions
        ddm_recs = [r for r in recommendations if 'ddm' in r.title.lower()]
        monte_carlo_recs = [r for r in recommendations if 'monte carlo' in r.title.lower()]
        assert len(ddm_recs) > 0 or len(monte_carlo_recs) > 0

    def test_ui_recommendations(self, recommendation_engine, sample_user_profile):
        """Test UI recommendation generation"""
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="analysis_preferences",
                frequency=3.0,  # High frequency
                last_occurrence=datetime.now(),
                trend="stable",
                success_rate=0.6  # Low success rate
            )
        ]

        recommendations = recommendation_engine._generate_ui_recommendations(
            "test_user", patterns, sample_user_profile
        )

        ui_recs = [r for r in recommendations if r.type == RecommendationType.UI_PREFERENCES]

        # Should suggest UI improvements based on patterns
        assert len(ui_recs) > 0

    def test_workflow_recommendations(self, recommendation_engine):
        """Test workflow optimization recommendations"""
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="parameter_usage",
                frequency=1.0,
                last_occurrence=datetime.now(),
                trend="stable",
                average_session_duration=1200,  # 20 minutes
                success_rate=0.8
            ),
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="performance_optimization",
                frequency=0.3,  # Low cache hit rate
                last_occurrence=datetime.now(),
                trend="stable",
                success_rate=0.7
            )
        ]

        recommendations = recommendation_engine._generate_workflow_recommendations("test_user", patterns)

        workflow_recs = [r for r in recommendations if r.type == RecommendationType.WORKFLOW_OPTIMIZATION]
        assert len(workflow_recs) > 0

    def test_user_similarity_calculation(self, recommendation_engine):
        """Test user similarity calculation"""
        patterns1 = [
            UserBehaviorPattern(
                user_id="user1",
                pattern_type="analysis_preferences",
                frequency=1.0,
                last_occurrence=datetime.now(),
                trend="stable",
                common_analysis_types=["dcf", "ddm"],
                success_rate=0.8
            )
        ]

        patterns2 = [
            UserBehaviorPattern(
                user_id="user2",
                pattern_type="analysis_preferences",
                frequency=1.2,
                last_occurrence=datetime.now(),
                trend="stable",
                common_analysis_types=["dcf"],  # Partial overlap
                success_rate=0.85
            )
        ]

        similarity = recommendation_engine._calculate_user_similarity(patterns1, patterns2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # Should have some similarity due to DCF overlap

    def test_ab_testing_application(self, recommendation_engine):
        """Test A/B testing application to recommendations"""
        recommendations = [
            Recommendation(
                recommendation_id="test_rec_1",
                user_id="test_user",
                type=RecommendationType.FINANCIAL_PARAMETERS,
                priority=RecommendationPriority.MEDIUM,
                title="Test Recommendation",
                description="Test description",
                suggested_value=0.1,
                confidence_score=0.8
            )
        ]

        ab_tested_recs = recommendation_engine._apply_ab_testing("test_user", recommendations)

        # Should have A/B testing metadata
        for rec in ab_tested_recs:
            if rec.type.value in recommendation_engine.ab_test_configs:
                assert rec.test_group is not None
                assert rec.variant is not None

    def test_apply_recommendation(self, recommendation_engine, temp_directory):
        """Test applying a recommendation"""
        recommendation = Recommendation(
            recommendation_id="test_rec_apply",
            user_id="test_user",
            type=RecommendationType.FINANCIAL_PARAMETERS,
            priority=RecommendationPriority.MEDIUM,
            title="Test Apply",
            description="Test description",
            suggested_value=0.1,
            confidence_score=0.8
        )

        # Save recommendation first
        recommendation_engine._save_recommendation(recommendation)

        # Mock analytics tracker
        recommendation_engine.analytics_tracker.track_event = Mock()

        # Test applying
        result = recommendation_engine.apply_recommendation("test_user", "test_rec_apply")

        # Should track the application
        recommendation_engine.analytics_tracker.track_event.assert_called()

    def test_dismiss_recommendation(self, recommendation_engine, temp_directory):
        """Test dismissing a recommendation"""
        recommendation = Recommendation(
            recommendation_id="test_rec_dismiss",
            user_id="test_user",
            type=RecommendationType.COMPANY_SUGGESTIONS,
            priority=RecommendationPriority.LOW,
            title="Test Dismiss",
            description="Test description",
            suggested_value=["TSLA"],
            confidence_score=0.7
        )

        # Save recommendation first
        recommendation_engine._save_recommendation(recommendation)

        # Mock analytics tracker
        recommendation_engine.analytics_tracker.track_event = Mock()

        # Test dismissing
        result = recommendation_engine.dismiss_recommendation("test_user", "test_rec_dismiss", "Not interested")

        assert result is True
        recommendation_engine.analytics_tracker.track_event.assert_called()

    def test_get_user_recommendations(self, recommendation_engine, temp_directory):
        """Test retrieving user recommendations"""
        recommendations = [
            Recommendation(
                recommendation_id="test_rec_1",
                user_id="test_user",
                type=RecommendationType.FINANCIAL_PARAMETERS,
                priority=RecommendationPriority.HIGH,
                title="Test Rec 1",
                description="Description 1",
                suggested_value=0.1,
                confidence_score=0.9
            ),
            Recommendation(
                recommendation_id="test_rec_2",
                user_id="test_user",
                type=RecommendationType.COMPANY_SUGGESTIONS,
                priority=RecommendationPriority.MEDIUM,
                title="Test Rec 2",
                description="Description 2",
                suggested_value=["AAPL"],
                confidence_score=0.7,
                is_dismissed=True
            )
        ]

        # Save recommendations
        recommendation_engine._save_recommendations("test_user", recommendations)

        # Get all recommendations
        all_recs = recommendation_engine.get_user_recommendations("test_user", include_dismissed=True)
        assert len(all_recs) == 2

        # Get non-dismissed recommendations
        active_recs = recommendation_engine.get_user_recommendations("test_user", include_dismissed=False)
        assert len(active_recs) == 1
        assert not active_recs[0].is_dismissed

    def test_file_operations(self, recommendation_engine, temp_directory):
        """Test file save/load operations"""
        # Test pattern save/load
        patterns = [
            UserBehaviorPattern(
                user_id="test_user",
                pattern_type="test_pattern",
                frequency=1.5,
                last_occurrence=datetime.now(),
                trend="increasing",
                success_rate=0.8
            )
        ]

        assert recommendation_engine._save_user_patterns("test_user", patterns)
        loaded_patterns = recommendation_engine._load_user_patterns("test_user")
        assert len(loaded_patterns) == 1
        assert loaded_patterns[0].pattern_type == "test_pattern"

        # Test recommendation save/load
        recommendations = [
            Recommendation(
                recommendation_id="test_file_rec",
                user_id="test_user",
                type=RecommendationType.UI_PREFERENCES,
                priority=RecommendationPriority.LOW,
                title="File Test",
                description="Test file operations",
                suggested_value={"theme": "dark"},
                confidence_score=0.6
            )
        ]

        assert recommendation_engine._save_recommendations("test_user", recommendations)
        loaded_recs = recommendation_engine._load_user_recommendations("test_user")
        assert len(loaded_recs) == 1
        assert loaded_recs[0].title == "File Test"

    def test_global_instance_functions(self, temp_directory):
        """Test global instance management functions"""
        with patch('core.user_preferences.recommendation_engine.get_analytics_tracker') as mock_analytics, \
             patch('core.user_preferences.recommendation_engine.get_preference_manager') as mock_manager:

            mock_analytics.return_value = Mock()
            mock_manager.return_value = Mock()

            # Test getting instance
            engine1 = get_recommendation_engine(data_directory=temp_directory)
            engine2 = get_recommendation_engine(data_directory=temp_directory)

            # Should return the same instance
            assert engine1 is engine2

            # Test setting custom instance
            from core.user_preferences.recommendation_engine import set_recommendation_engine
            custom_engine = SmartRecommendationEngine(data_directory=temp_directory)
            set_recommendation_engine(custom_engine)

            engine3 = get_recommendation_engine()
            assert engine3 is custom_engine


class TestRecommendationDataClasses:
    """Test recommendation data classes"""

    def test_recommendation_creation(self):
        """Test Recommendation object creation"""
        rec = Recommendation(
            recommendation_id="test_id",
            user_id="user123",
            type=RecommendationType.FINANCIAL_PARAMETERS,
            priority=RecommendationPriority.HIGH,
            title="Test Recommendation",
            description="Test description",
            suggested_value=0.15,
            current_value=0.10,
            confidence_score=0.85,
            reasoning="Test reasoning",
            category="DCF Parameters",
            tags=["dcf", "optimization"]
        )

        assert rec.recommendation_id == "test_id"
        assert rec.user_id == "user123"
        assert rec.type == RecommendationType.FINANCIAL_PARAMETERS
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.confidence_score == 0.85
        assert "dcf" in rec.tags

    def test_user_behavior_pattern_creation(self):
        """Test UserBehaviorPattern object creation"""
        pattern = UserBehaviorPattern(
            user_id="user123",
            pattern_type="analysis_preferences",
            frequency=2.5,
            last_occurrence=datetime.now(),
            trend="increasing",
            typical_parameters={"discount_rate": 0.12},
            preferred_companies=["AAPL", "MSFT"],
            common_analysis_types=["dcf", "ddm"],
            success_rate=0.88,
            average_session_duration=450.0
        )

        assert pattern.user_id == "user123"
        assert pattern.pattern_type == "analysis_preferences"
        assert pattern.frequency == 2.5
        assert pattern.trend == "increasing"
        assert "AAPL" in pattern.preferred_companies
        assert "dcf" in pattern.common_analysis_types

    def test_similar_user_profile_creation(self):
        """Test SimilarUserProfile object creation"""
        similar_user = SimilarUserProfile(
            user_id="similar_user",
            similarity_score=0.75,
            common_patterns=["analysis_preferences", "company_preferences"],
            successful_preferences={"discount_rate": 0.10},
            recommended_companies=["TSLA", "GOOGL"],
            analysis_preferences={"methodology": "conservative"}
        )

        assert similar_user.user_id == "similar_user"
        assert similar_user.similarity_score == 0.75
        assert "analysis_preferences" in similar_user.common_patterns
        assert "TSLA" in similar_user.recommended_companies


if __name__ == "__main__":
    pytest.main([__file__])