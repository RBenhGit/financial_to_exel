"""
User Feedback Collection System for Streamlit Financial Analysis Application

This module provides a comprehensive feedback collection system integrated into
the Streamlit application with multiple feedback channels, session-based tracking,
categorization, and analytics capabilities.
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

# Import logging utilities
try:
    from utils.logging_config import get_streamlit_logger
    logger = get_streamlit_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class FeedbackCategory(Enum):
    """Feedback category enumeration"""
    USABILITY = "usability"
    PERFORMANCE = "performance"
    BUGS = "bugs"
    FEATURES = "features"
    CONTENT = "content"
    GENERAL = "general"


class FeedbackType(Enum):
    """Feedback type enumeration"""
    RATING = "rating"
    COMMENT = "comment"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    QUICK_FEEDBACK = "quick_feedback"


@dataclass
class FeedbackEntry:
    """Structured feedback entry"""
    id: str
    session_id: str
    tab_name: str
    feedback_type: FeedbackType
    category: FeedbackCategory
    rating: Optional[int]
    comment: str
    timestamp: str
    user_agent: str
    page_url: str
    is_anonymous: bool
    sentiment_score: Optional[float] = None
    resolved: bool = False
    priority: str = "medium"  # low, medium, high, critical


class UserFeedbackSystem:
    """Comprehensive user feedback collection and management system"""

    def __init__(self, data_dir: str = "data/feedback"):
        """Initialize the feedback system

        Args:
            data_dir: Directory to store feedback data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.feedback_file = self.data_dir / "user_feedback.json"
        self.session_file = self.data_dir / "feedback_sessions.json"
        self.analytics_file = self.data_dir / "feedback_analytics.json"

        # Initialize session tracking
        self._init_session_tracking()

        # Load existing feedback data
        self.feedback_data = self._load_feedback_data()

        # Tab-specific feedback prompts
        self.tab_feedback_prompts = {
            "FCF": {
                "quick_questions": [
                    "How intuitive was the FCF calculation process?",
                    "Were the FCF results clearly displayed?",
                    "Did you find the growth rate analysis helpful?"
                ],
                "context": "Free Cash Flow Analysis"
            },
            "DCF": {
                "quick_questions": [
                    "How accurate did the DCF valuation seem?",
                    "Were the discount rate assumptions clear?",
                    "Did the sensitivity analysis provide value?"
                ],
                "context": "Discounted Cash Flow Valuation"
            },
            "DDM": {
                "quick_questions": [
                    "How useful was the dividend analysis?",
                    "Were dividend growth assumptions reasonable?",
                    "Did the DDM results align with your expectations?"
                ],
                "context": "Dividend Discount Model"
            },
            "P/B": {
                "quick_questions": [
                    "How helpful was the P/B ratio comparison?",
                    "Were peer comparisons meaningful?",
                    "Did historical trends provide insights?"
                ],
                "context": "Price-to-Book Analysis"
            },
            "Ratios": {
                "quick_questions": [
                    "Which ratios were most valuable?",
                    "How clear were the ratio interpretations?",
                    "Did benchmarking help with analysis?"
                ],
                "context": "Financial Ratios Dashboard"
            }
        }

    def _init_session_tracking(self):
        """Initialize session tracking for feedback deduplication"""
        if 'feedback_session_id' not in st.session_state:
            st.session_state.feedback_session_id = str(uuid.uuid4())
            st.session_state.feedback_shown_tabs = set()
            st.session_state.feedback_submission_count = 0

    def _load_feedback_data(self) -> List[Dict]:
        """Load existing feedback data"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            return []

    def _save_feedback_data(self):
        """Save feedback data to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
            logger.info(f"Saved {len(self.feedback_data)} feedback entries")
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")

    def _should_show_feedback_prompt(self, tab_name: str) -> bool:
        """Determine if feedback prompt should be shown for this tab"""
        # Ensure session state is initialized
        if 'feedback_shown_tabs' not in st.session_state:
            self._init_session_tracking()

        # Don't show if already shown in this session
        if tab_name in st.session_state.feedback_shown_tabs:
            return False

        # Limit feedback prompts per session
        if st.session_state.feedback_submission_count >= 3:
            return False

        # Show feedback prompt with some probability to avoid overwhelming users
        import random
        return random.random() < 0.3  # 30% chance

    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID"""
        return f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _analyze_sentiment(self, text: str) -> float:
        """Basic sentiment analysis (placeholder for more sophisticated analysis)"""
        try:
            # Simple keyword-based sentiment analysis
            positive_keywords = ['good', 'great', 'excellent', 'love', 'helpful', 'useful', 'clear', 'intuitive']
            negative_keywords = ['bad', 'terrible', 'confusing', 'slow', 'error', 'broken', 'difficult', 'unclear']

            text_lower = text.lower()
            positive_score = sum(1 for word in positive_keywords if word in text_lower)
            negative_score = sum(1 for word in negative_keywords if word in text_lower)

            if positive_score == 0 and negative_score == 0:
                return 0.0  # Neutral
            return (positive_score - negative_score) / (positive_score + negative_score)
        except Exception:
            return 0.0

    def render_feedback_widget(self, tab_name: str, position: str = "bottom") -> None:
        """Render feedback collection widget for a specific tab

        Args:
            tab_name: Name of the current tab
            position: Position of the widget ("bottom", "sidebar", "inline")
        """
        # Check if feedback should be shown
        if not self._should_show_feedback_prompt(tab_name):
            return

        # Ensure session state is initialized before adding to set
        if 'feedback_shown_tabs' not in st.session_state:
            self._init_session_tracking()
        st.session_state.feedback_shown_tabs.add(tab_name)

        # Get tab-specific prompts
        tab_info = self.tab_feedback_prompts.get(tab_name, {
            "quick_questions": ["How was your experience with this feature?"],
            "context": tab_name
        })

        if position == "sidebar":
            with st.sidebar:
                self._render_feedback_form(tab_name, tab_info)
        else:
            # Render inline feedback form
            self._render_feedback_form(tab_name, tab_info)

    def _render_feedback_form(self, tab_name: str, tab_info: Dict) -> None:
        """Render the actual feedback form"""
        with st.expander(f"💬 Share feedback about {tab_info['context']}", expanded=False):
            st.markdown("*Your feedback helps us improve the application*")

            feedback_type = st.radio(
                "Feedback type:",
                ["Quick Rating", "Detailed Comment", "Bug Report", "Feature Request"],
                key=f"feedback_type_{tab_name}",
                horizontal=True
            )

            feedback_entry = None

            if feedback_type == "Quick Rating":
                feedback_entry = self._render_quick_rating_form(tab_name, tab_info)
            elif feedback_type == "Detailed Comment":
                feedback_entry = self._render_comment_form(tab_name, tab_info)
            elif feedback_type == "Bug Report":
                feedback_entry = self._render_bug_report_form(tab_name, tab_info)
            elif feedback_type == "Feature Request":
                feedback_entry = self._render_feature_request_form(tab_name, tab_info)

            if feedback_entry:
                self._save_feedback_entry(feedback_entry)
                st.success("✅ Thank you for your feedback!")
                # Ensure session state is initialized before incrementing
                if 'feedback_submission_count' not in st.session_state:
                    self._init_session_tracking()
                st.session_state.feedback_submission_count += 1

    def _render_quick_rating_form(self, tab_name: str, tab_info: Dict) -> Optional[FeedbackEntry]:
        """Render quick rating form"""
        col1, col2 = st.columns([3, 1])

        with col1:
            rating = st.select_slider(
                "Rate your experience:",
                options=[1, 2, 3, 4, 5],
                value=4,
                format_func=lambda x: "⭐" * x,
                key=f"rating_{tab_name}"
            )

        with col2:
            submit_rating = st.button("Submit", key=f"submit_rating_{tab_name}")

        if submit_rating:
            return FeedbackEntry(
                id=self._generate_feedback_id(),
                session_id=st.session_state.feedback_session_id,
                tab_name=tab_name,
                feedback_type=FeedbackType.RATING,
                category=FeedbackCategory.USABILITY,
                rating=rating,
                comment=f"Quick rating: {rating}/5 stars",
                timestamp=datetime.now().isoformat(),
                user_agent=st.context.headers.get('User-Agent', 'Unknown'),
                page_url=f"/{tab_name.lower()}",
                is_anonymous=True
            )
        return None

    def _render_comment_form(self, tab_name: str, tab_info: Dict) -> Optional[FeedbackEntry]:
        """Render detailed comment form"""
        category = st.selectbox(
            "Category:",
            [cat.value.title() for cat in FeedbackCategory],
            key=f"category_{tab_name}"
        )

        comment = st.text_area(
            "Your feedback:",
            placeholder="Please share your thoughts about this feature...",
            height=100,
            key=f"comment_{tab_name}"
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit_comment = st.button("Submit Feedback", key=f"submit_comment_{tab_name}")

        if submit_comment and comment.strip():
            sentiment = self._analyze_sentiment(comment)

            return FeedbackEntry(
                id=self._generate_feedback_id(),
                session_id=st.session_state.feedback_session_id,
                tab_name=tab_name,
                feedback_type=FeedbackType.COMMENT,
                category=FeedbackCategory(category.lower()),
                rating=None,
                comment=comment.strip(),
                timestamp=datetime.now().isoformat(),
                user_agent=st.context.headers.get('User-Agent', 'Unknown'),
                page_url=f"/{tab_name.lower()}",
                is_anonymous=True,
                sentiment_score=sentiment
            )
        return None

    def _render_bug_report_form(self, tab_name: str, tab_info: Dict) -> Optional[FeedbackEntry]:
        """Render bug report form"""
        st.markdown("**🐛 Bug Report**")

        bug_description = st.text_area(
            "Describe the bug:",
            placeholder="What happened? What did you expect to happen?",
            key=f"bug_desc_{tab_name}"
        )

        steps_to_reproduce = st.text_area(
            "Steps to reproduce:",
            placeholder="1. Go to...\n2. Click on...\n3. See error",
            key=f"bug_steps_{tab_name}"
        )

        priority = st.selectbox(
            "Priority:",
            ["Low", "Medium", "High", "Critical"],
            index=1,
            key=f"bug_priority_{tab_name}"
        )

        submit_bug = st.button("Submit Bug Report", key=f"submit_bug_{tab_name}")

        if submit_bug and bug_description.strip():
            full_description = f"Bug: {bug_description}\n\nSteps: {steps_to_reproduce}"

            return FeedbackEntry(
                id=self._generate_feedback_id(),
                session_id=st.session_state.feedback_session_id,
                tab_name=tab_name,
                feedback_type=FeedbackType.BUG_REPORT,
                category=FeedbackCategory.BUGS,
                rating=None,
                comment=full_description,
                timestamp=datetime.now().isoformat(),
                user_agent=st.context.headers.get('User-Agent', 'Unknown'),
                page_url=f"/{tab_name.lower()}",
                is_anonymous=True,
                priority=priority.lower()
            )
        return None

    def _render_feature_request_form(self, tab_name: str, tab_info: Dict) -> Optional[FeedbackEntry]:
        """Render feature request form"""
        st.markdown("**💡 Feature Request**")

        feature_title = st.text_input(
            "Feature title:",
            placeholder="Brief title for the feature",
            key=f"feature_title_{tab_name}"
        )

        feature_description = st.text_area(
            "Feature description:",
            placeholder="Describe the feature you'd like to see...",
            key=f"feature_desc_{tab_name}"
        )

        use_case = st.text_area(
            "Use case:",
            placeholder="How would this feature help your analysis?",
            key=f"feature_usecase_{tab_name}"
        )

        submit_feature = st.button("Submit Feature Request", key=f"submit_feature_{tab_name}")

        if submit_feature and feature_title.strip() and feature_description.strip():
            full_description = f"Feature: {feature_title}\n\nDescription: {feature_description}\n\nUse Case: {use_case}"

            return FeedbackEntry(
                id=self._generate_feedback_id(),
                session_id=st.session_state.feedback_session_id,
                tab_name=tab_name,
                feedback_type=FeedbackType.FEATURE_REQUEST,
                category=FeedbackCategory.FEATURES,
                rating=None,
                comment=full_description,
                timestamp=datetime.now().isoformat(),
                user_agent=st.context.headers.get('User-Agent', 'Unknown'),
                page_url=f"/{tab_name.lower()}",
                is_anonymous=True
            )
        return None

    def _save_feedback_entry(self, feedback_entry: FeedbackEntry) -> None:
        """Save feedback entry to storage"""
        self.feedback_data.append(asdict(feedback_entry))
        self._save_feedback_data()

        # Update analytics
        self._update_feedback_analytics(feedback_entry)

    def _update_feedback_analytics(self, feedback_entry: FeedbackEntry) -> None:
        """Update feedback analytics"""
        try:
            analytics = {}
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r') as f:
                    analytics = json.load(f)

            # Update counters
            analytics.setdefault('total_feedback', 0)
            analytics['total_feedback'] += 1

            analytics.setdefault('by_tab', {})
            analytics['by_tab'].setdefault(feedback_entry.tab_name, 0)
            analytics['by_tab'][feedback_entry.tab_name] += 1

            analytics.setdefault('by_category', {})
            analytics['by_category'].setdefault(feedback_entry.category.value, 0)
            analytics['by_category'][feedback_entry.category.value] += 1

            analytics.setdefault('by_type', {})
            analytics['by_type'].setdefault(feedback_entry.feedback_type.value, 0)
            analytics['by_type'][feedback_entry.feedback_type.value] += 1

            # Update timestamp
            analytics['last_updated'] = datetime.now().isoformat()

            with open(self.analytics_file, 'w') as f:
                json.dump(analytics, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating feedback analytics: {e}")

    def render_feedback_analytics_dashboard(self) -> None:
        """Render feedback analytics dashboard for administrators"""
        st.markdown("## 📊 Feedback Analytics Dashboard")

        if not self.feedback_data:
            st.info("No feedback data available yet.")
            return

        df = pd.DataFrame(self.feedback_data)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Feedback", len(df))

        with col2:
            avg_rating = df[df['rating'].notna()]['rating'].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}" if not pd.isna(avg_rating) else "N/A")

        with col3:
            recent_feedback = len(df[pd.to_datetime(df['timestamp']) > datetime.now() - timedelta(days=7)])
            st.metric("Last 7 Days", recent_feedback)

        with col4:
            bug_reports = len(df[df['feedback_type'] == 'bug_report'])
            st.metric("Bug Reports", bug_reports)

        # Visualizations
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Feedback by Tab")
            tab_counts = df['tab_name'].value_counts()
            st.bar_chart(tab_counts)

        with col2:
            st.subheader("Feedback by Category")
            category_counts = df['category'].value_counts()
            st.bar_chart(category_counts)

        # Recent feedback
        st.subheader("Recent Feedback")
        recent_df = df.sort_values('timestamp', ascending=False).head(10)
        for _, row in recent_df.iterrows():
            with st.expander(f"{row['tab_name']} - {row['feedback_type']} ({row['timestamp'][:10]})"):
                st.write(f"**Category:** {row['category']}")
                if row['rating']:
                    st.write(f"**Rating:** {'⭐' * int(row['rating'])}")
                st.write(f"**Comment:** {row['comment']}")

    def export_feedback_data(self, format: str = "csv") -> str:
        """Export feedback data in specified format

        Args:
            format: Export format ("csv", "json", "excel")

        Returns:
            Path to exported file
        """
        if not self.feedback_data:
            raise ValueError("No feedback data to export")

        df = pd.DataFrame(self.feedback_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "csv":
            export_path = self.data_dir / f"feedback_export_{timestamp}.csv"
            df.to_csv(export_path, index=False)
        elif format == "excel":
            export_path = self.data_dir / f"feedback_export_{timestamp}.xlsx"
            df.to_excel(export_path, index=False, engine='openpyxl')
        elif format == "json":
            export_path = self.data_dir / f"feedback_export_{timestamp}.json"
            with open(export_path, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return str(export_path)


# Global feedback system instance
_feedback_system = None


def get_feedback_system() -> UserFeedbackSystem:
    """Get global feedback system instance"""
    global _feedback_system
    if _feedback_system is None:
        _feedback_system = UserFeedbackSystem()
    return _feedback_system


def render_tab_feedback(tab_name: str, position: str = "bottom") -> None:
    """Convenience function to render feedback widget for a tab

    Args:
        tab_name: Name of the current tab
        position: Position of the widget
    """
    feedback_system = get_feedback_system()
    feedback_system.render_feedback_widget(tab_name, position)


def render_feedback_analytics() -> None:
    """Convenience function to render feedback analytics dashboard"""
    feedback_system = get_feedback_system()
    feedback_system.render_feedback_analytics_dashboard()


def export_feedback(format: str = "csv") -> str:
    """Convenience function to export feedback data

    Args:
        format: Export format

    Returns:
        Path to exported file
    """
    feedback_system = get_feedback_system()
    return feedback_system.export_feedback_data(format)