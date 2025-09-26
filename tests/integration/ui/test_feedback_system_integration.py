"""
Integration tests for the User Feedback System

Tests the feedback collection system integration with the Streamlit application
to ensure proper functionality across all analysis tabs.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from ui.streamlit.user_feedback_system import (
    UserFeedbackSystem,
    FeedbackEntry,
    FeedbackCategory,
    FeedbackType,
    get_feedback_system,
    render_tab_feedback,
    render_feedback_analytics,
    export_feedback
)


class TestUserFeedbackSystemIntegration:
    """Test suite for User Feedback System integration"""

    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.feedback_system = UserFeedbackSystem(data_dir=self.test_dir)

    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_feedback_system_initialization(self):
        """Test that feedback system initializes correctly"""
        assert self.feedback_system is not None
        assert self.feedback_system.data_dir.exists()
        assert isinstance(self.feedback_system.feedback_data, list)
        assert len(self.feedback_system.tab_feedback_prompts) > 0

    def test_feedback_entry_creation(self):
        """Test creation of feedback entries"""
        feedback_entry = FeedbackEntry(
            id="test_123",
            session_id="session_123",
            tab_name="FCF",
            feedback_type=FeedbackType.RATING,
            category=FeedbackCategory.USABILITY,
            rating=5,
            comment="Great analysis tool!",
            timestamp=datetime.now().isoformat(),
            user_agent="TestAgent/1.0",
            page_url="/fcf",
            is_anonymous=True
        )

        assert feedback_entry.id == "test_123"
        assert feedback_entry.tab_name == "FCF"
        assert feedback_entry.rating == 5

    def test_feedback_data_persistence(self):
        """Test that feedback data is properly saved and loaded"""
        # Create and save test feedback
        test_feedback = FeedbackEntry(
            id="test_persist_123",
            session_id="session_persist",
            tab_name="DCF",
            feedback_type=FeedbackType.COMMENT,
            category=FeedbackCategory.PERFORMANCE,
            rating=None,
            comment="This could be faster",
            timestamp=datetime.now().isoformat(),
            user_agent="TestAgent/1.0",
            page_url="/dcf",
            is_anonymous=True
        )

        self.feedback_system._save_feedback_entry(test_feedback)

        # Create new instance to test loading
        new_system = UserFeedbackSystem(data_dir=self.test_dir)
        assert len(new_system.feedback_data) == 1
        assert new_system.feedback_data[0]['id'] == "test_persist_123"

    def test_sentiment_analysis(self):
        """Test basic sentiment analysis functionality"""
        positive_text = "This is great and very helpful"
        negative_text = "This is terrible and confusing"
        neutral_text = "This is a financial analysis tool"

        positive_score = self.feedback_system._analyze_sentiment(positive_text)
        negative_score = self.feedback_system._analyze_sentiment(negative_text)
        neutral_score = self.feedback_system._analyze_sentiment(neutral_text)

        assert positive_score > 0
        assert negative_score < 0
        assert neutral_score == 0.0

    @patch('streamlit.session_state')
    def test_session_tracking_initialization(self, mock_session_state):
        """Test session tracking initialization"""
        mock_session_state.__contains__ = Mock(side_effect=lambda x: x != 'feedback_session_id')
        mock_session_state.__setitem__ = Mock()

        self.feedback_system._init_session_tracking()

        # Verify session state variables were set
        mock_session_state.__setitem__.assert_any_call('feedback_session_id', mock_session_state.__setitem__.call_args_list[0][0][1])
        mock_session_state.__setitem__.assert_any_call('feedback_shown_tabs', set())
        mock_session_state.__setitem__.assert_any_call('feedback_submission_count', 0)

    def test_tab_specific_prompts(self):
        """Test that tab-specific feedback prompts are properly configured"""
        expected_tabs = ['FCF', 'DCF', 'DDM', 'P/B', 'Ratios']

        for tab in expected_tabs:
            assert tab in self.feedback_system.tab_feedback_prompts
            tab_info = self.feedback_system.tab_feedback_prompts[tab]
            assert 'quick_questions' in tab_info
            assert 'context' in tab_info
            assert len(tab_info['quick_questions']) > 0

    def test_feedback_export_functionality(self):
        """Test feedback data export in different formats"""
        # Add test feedback
        test_feedback = FeedbackEntry(
            id="test_export_123",
            session_id="session_export",
            tab_name="FCF",
            feedback_type=FeedbackType.RATING,
            category=FeedbackCategory.USABILITY,
            rating=4,
            comment="Good but could be better",
            timestamp=datetime.now().isoformat(),
            user_agent="TestAgent/1.0",
            page_url="/fcf",
            is_anonymous=True
        )

        self.feedback_system._save_feedback_entry(test_feedback)

        # Test CSV export
        csv_path = self.feedback_system.export_feedback_data("csv")
        assert Path(csv_path).exists()
        assert Path(csv_path).suffix == ".csv"

        # Test JSON export
        json_path = self.feedback_system.export_feedback_data("json")
        assert Path(json_path).exists()
        assert Path(json_path).suffix == ".json"

        # Verify exported data
        df = pd.read_csv(csv_path)
        assert len(df) == 1
        assert df.iloc[0]['tab_name'] == "FCF"

    def test_analytics_data_generation(self):
        """Test feedback analytics data generation"""
        # Add multiple feedback entries
        feedback_entries = [
            FeedbackEntry(
                id=f"test_analytics_{i}",
                session_id=f"session_{i}",
                tab_name="FCF" if i % 2 == 0 else "DCF",
                feedback_type=FeedbackType.RATING,
                category=FeedbackCategory.USABILITY,
                rating=4 + (i % 2),
                comment=f"Test feedback {i}",
                timestamp=datetime.now().isoformat(),
                user_agent="TestAgent/1.0",
                page_url="/test",
                is_anonymous=True
            )
            for i in range(5)
        ]

        for entry in feedback_entries:
            self.feedback_system._save_feedback_entry(entry)

        # Check analytics file was created
        assert self.feedback_system.analytics_file.exists()

        # Load and verify analytics
        with open(self.feedback_system.analytics_file, 'r') as f:
            analytics = json.load(f)

        assert analytics['total_feedback'] == 5
        assert 'FCF' in analytics['by_tab']
        assert 'DCF' in analytics['by_tab']
        assert analytics['by_tab']['FCF'] == 3  # 0, 2, 4
        assert analytics['by_tab']['DCF'] == 2  # 1, 3

    def test_feedback_system_error_handling(self):
        """Test error handling in feedback system"""
        # Test with invalid data directory
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Cannot create directory")):
            try:
                UserFeedbackSystem(data_dir="/invalid/path/that/cannot/be/created")
                # Should not raise exception, should handle gracefully
            except PermissionError:
                pytest.fail("UserFeedbackSystem should handle directory creation errors gracefully")

    def test_global_feedback_system_instance(self):
        """Test global feedback system instance management"""
        # Test singleton behavior
        system1 = get_feedback_system()
        system2 = get_feedback_system()
        assert system1 is system2

    @patch('streamlit.expander')
    @patch('streamlit.radio')
    @patch('streamlit.select_slider')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.session_state')
    def test_render_tab_feedback_integration(self, mock_session_state, mock_columns,
                                           mock_button, mock_slider, mock_radio, mock_expander):
        """Test feedback widget rendering integration"""
        # Mock session state
        mock_session_state.feedback_shown_tabs = set()
        mock_session_state.feedback_submission_count = 0

        # Mock UI components
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [Mock(), Mock()]
        mock_radio.return_value = "Quick Rating"
        mock_slider.return_value = 5
        mock_button.return_value = True

        # Mock random to ensure feedback is shown
        with patch('random.random', return_value=0.1):  # Below 0.3 threshold
            # This should not raise any exceptions
            try:
                render_tab_feedback("FCF")
            except Exception as e:
                pytest.fail(f"render_tab_feedback should not raise exceptions: {e}")


class TestFeedbackSystemEndToEnd:
    """End-to-end tests for the complete feedback workflow"""

    def setup_method(self):
        """Setup for each test method"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_feedback_workflow(self):
        """Test complete feedback collection workflow"""
        # Initialize system
        feedback_system = UserFeedbackSystem(data_dir=self.test_dir)

        # Simulate user feedback
        feedback_entry = FeedbackEntry(
            id="workflow_test_123",
            session_id="workflow_session",
            tab_name="DCF",
            feedback_type=FeedbackType.COMMENT,
            category=FeedbackCategory.FEATURES,
            rating=None,
            comment="Please add more sensitivity analysis options",
            timestamp=datetime.now().isoformat(),
            user_agent="TestAgent/1.0",
            page_url="/dcf",
            is_anonymous=True,
            sentiment_score=0.5
        )

        # Save feedback
        feedback_system._save_feedback_entry(feedback_entry)

        # Verify data persistence
        assert len(feedback_system.feedback_data) == 1

        # Export data
        export_path = feedback_system.export_feedback_data("csv")
        assert Path(export_path).exists()

        # Verify export content
        df = pd.read_csv(export_path)
        assert len(df) == 1
        assert df.iloc[0]['comment'] == "Please add more sensitivity analysis options"

    def test_multiple_tab_feedback_collection(self):
        """Test feedback collection across multiple tabs"""
        feedback_system = UserFeedbackSystem(data_dir=self.test_dir)

        tabs = ["FCF", "DCF", "DDM", "P/B", "Ratios"]
        for i, tab in enumerate(tabs):
            feedback_entry = FeedbackEntry(
                id=f"multi_tab_{i}",
                session_id=f"multi_session_{i}",
                tab_name=tab,
                feedback_type=FeedbackType.RATING,
                category=FeedbackCategory.USABILITY,
                rating=4 + (i % 2),
                comment=f"Feedback for {tab} tab",
                timestamp=datetime.now().isoformat(),
                user_agent="TestAgent/1.0",
                page_url=f"/{tab.lower()}",
                is_anonymous=True
            )
            feedback_system._save_feedback_entry(feedback_entry)

        # Verify all feedback was saved
        assert len(feedback_system.feedback_data) == 5

        # Verify analytics
        with open(feedback_system.analytics_file, 'r') as f:
            analytics = json.load(f)

        assert analytics['total_feedback'] == 5
        for tab in tabs:
            assert tab in analytics['by_tab']
            assert analytics['by_tab'][tab] == 1


if __name__ == "__main__":
    pytest.main([__file__])