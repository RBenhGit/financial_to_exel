"""
User Feedback Analysis and Sentiment Tracking Integration

This module integrates with the existing user feedback system to provide
sentiment analysis, feedback categorization, and actionable insights
for continuous improvement of the financial analysis application.
"""

import os
import sys
import json
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import statistics

# Import existing feedback system
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'streamlit'))
try:
    from user_feedback_system import UserFeedbackSystem, FeedbackCategory, FeedbackType, FeedbackEntry
except ImportError:
    print("Warning: User feedback system not available")
    FeedbackCategory = None
    FeedbackType = None

# Import logging utilities
try:
    from utils.logging_config import get_streamlit_logger
    logger = get_streamlit_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result for feedback."""
    score: float  # -1.0 (very negative) to 1.0 (very positive)
    confidence: float  # 0.0 to 1.0
    sentiment_label: str  # "positive", "negative", "neutral"
    key_phrases: List[str]
    emotion_indicators: Dict[str, float]


@dataclass
class FeedbackInsight:
    """Actionable insight derived from feedback analysis."""
    category: str
    priority: str  # "high", "medium", "low"
    insight_type: str  # "improvement", "issue", "praise", "suggestion"
    description: str
    affected_features: List[str]
    user_impact_score: float
    recommended_actions: List[str]


@dataclass
class FeedbackAnalysisReport:
    """Comprehensive feedback analysis report."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_feedback_count: int
    sentiment_distribution: Dict[str, int]
    category_breakdown: Dict[str, int]
    insights: List[FeedbackInsight]
    trend_analysis: Dict[str, Any]
    user_satisfaction_score: float
    recommendations: List[str]


class FeedbackSentimentAnalyzer:
    """
    Advanced feedback analysis system that processes user feedback to extract
    sentiment, categorize issues, and generate actionable insights for
    continuous improvement.
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the feedback sentiment analyzer."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.feedback_db_path = self.project_root / "data" / "feedback_analysis.db"
        self.reports_dir = self.project_root / "reports" / "feedback_analysis"

        # Ensure directories exist
        self.feedback_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Load sentiment lexicon and patterns
        self._init_sentiment_engine()

        # Initialize feedback system integration
        self.feedback_system = None
        try:
            self.feedback_system = UserFeedbackSystem()
        except Exception as e:
            logger.warning(f"Could not initialize feedback system: {e}")

    def _init_database(self):
        """Initialize SQLite database for feedback analysis storage."""

        with sqlite3.connect(self.feedback_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    sentiment_confidence REAL NOT NULL,
                    sentiment_label TEXT NOT NULL,
                    key_phrases TEXT,
                    emotion_indicators TEXT,
                    user_impact_score REAL,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON feedback_analysis(timestamp)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sentiment_score
                ON feedback_analysis(sentiment_score)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_category
                ON feedback_analysis(category)
            ''')

    def _init_sentiment_engine(self):
        """Initialize simple rule-based sentiment analysis engine."""

        # Positive sentiment indicators
        self.positive_words = {
            'excellent', 'amazing', 'great', 'good', 'nice', 'awesome', 'fantastic',
            'wonderful', 'perfect', 'love', 'like', 'helpful', 'useful', 'clear',
            'intuitive', 'easy', 'fast', 'accurate', 'comprehensive', 'detailed',
            'professional', 'reliable', 'efficient', 'smooth', 'impressed',
            'satisfied', 'pleased', 'happy', 'thank', 'thanks', 'appreciate'
        }

        # Negative sentiment indicators
        self.negative_words = {
            'terrible', 'awful', 'bad', 'horrible', 'hate', 'dislike', 'confusing',
            'difficult', 'hard', 'slow', 'broken', 'error', 'problem', 'issue',
            'bug', 'crash', 'fail', 'wrong', 'incorrect', 'missing', 'poor',
            'disappointed', 'frustrated', 'annoying', 'complicated', 'unclear',
            'useless', 'worthless', 'waste', 'stuck', 'lost', 'confused'
        }

        # Emotion indicators
        self.emotion_patterns = {
            'frustration': ['frustrated', 'annoying', 'stuck', 'difficult', 'can\'t'],
            'satisfaction': ['satisfied', 'pleased', 'happy', 'great', 'excellent'],
            'confusion': ['confused', 'unclear', 'don\'t understand', 'lost', 'help'],
            'appreciation': ['thank', 'appreciate', 'helpful', 'useful', 'good'],
            'concern': ['worried', 'concern', 'problem', 'issue', 'wrong']
        }

        # Feature-specific patterns
        self.feature_patterns = {
            'fcf_analysis': ['fcf', 'free cash flow', 'cash flow analysis'],
            'dcf_valuation': ['dcf', 'discounted cash flow', 'valuation', 'npv'],
            'ddm_analysis': ['ddm', 'dividend', 'dividend discount'],
            'pb_analysis': ['p/b', 'price to book', 'book value'],
            'portfolio_analysis': ['portfolio', 'multi-company', 'comparison'],
            'watchlist_management': ['watchlist', 'watch list', 'favorites'],
            'data_import': ['import', 'upload', 'excel', 'data'],
            'interface': ['ui', 'interface', 'design', 'layout', 'navigation']
        }

    def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """Analyze sentiment of feedback text using rule-based approach."""

        if not text or not text.strip():
            return SentimentAnalysis(
                score=0.0,
                confidence=0.0,
                sentiment_label="neutral",
                key_phrases=[],
                emotion_indicators={}
            )

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Calculate sentiment score
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        total_words = len(words)

        if total_words == 0:
            sentiment_score = 0.0
            confidence = 0.0
        else:
            # Calculate weighted sentiment score
            sentiment_score = (positive_count - negative_count) / total_words
            sentiment_score = max(-1.0, min(1.0, sentiment_score * 5))  # Scale and clamp

            # Calculate confidence based on sentiment word density
            sentiment_word_count = positive_count + negative_count
            confidence = min(1.0, sentiment_word_count / max(1, total_words * 0.3))

        # Determine sentiment label
        if sentiment_score > 0.1:
            sentiment_label = "positive"
        elif sentiment_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        # Extract key phrases (simple approach)
        sentences = re.split(r'[.!?]+', text)
        key_phrases = []
        for sentence in sentences[:3]:  # Top 3 sentences
            sentence = sentence.strip()
            if sentence and len(sentence.split()) >= 3:
                key_phrases.append(sentence)

        # Analyze emotions
        emotion_indicators = {}
        for emotion, patterns in self.emotion_patterns.items():
            emotion_score = 0.0
            for pattern in patterns:
                if pattern in text_lower:
                    emotion_score += 1.0
            emotion_indicators[emotion] = emotion_score / len(patterns)

        return SentimentAnalysis(
            score=sentiment_score,
            confidence=confidence,
            sentiment_label=sentiment_label,
            key_phrases=key_phrases,
            emotion_indicators=emotion_indicators
        )

    def identify_affected_features(self, text: str) -> List[str]:
        """Identify which features are mentioned in the feedback."""

        text_lower = text.lower()
        affected_features = []

        for feature, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    affected_features.append(feature)
                    break

        return list(set(affected_features))  # Remove duplicates

    def calculate_user_impact_score(self, sentiment: SentimentAnalysis,
                                  category: str, feedback_type: str) -> float:
        """Calculate user impact score based on sentiment, category, and type."""

        # Base score from sentiment
        base_score = abs(sentiment.score) * sentiment.confidence

        # Category weights
        category_weights = {
            'bugs': 2.0,
            'performance': 1.5,
            'usability': 1.3,
            'features': 1.0,
            'content': 0.8,
            'general': 0.7
        }

        # Type weights
        type_weights = {
            'bug_report': 2.0,
            'feature_request': 1.2,
            'comment': 1.0,
            'rating': 0.8,
            'quick_feedback': 0.6
        }

        category_weight = category_weights.get(category.lower(), 1.0)
        type_weight = type_weights.get(feedback_type.lower(), 1.0)

        # Negative feedback has higher impact
        sentiment_multiplier = 1.5 if sentiment.sentiment_label == "negative" else 1.0

        impact_score = base_score * category_weight * type_weight * sentiment_multiplier
        return min(10.0, impact_score)  # Cap at 10

    def process_feedback_entry(self, feedback_entry: Dict[str, Any]) -> Optional[str]:
        """Process a single feedback entry through sentiment analysis."""

        try:
            # Extract feedback content
            content = feedback_entry.get('content', '') or feedback_entry.get('comment', '')
            if not content:
                logger.warning("Feedback entry has no content")
                return None

            feedback_id = feedback_entry.get('id', str(feedback_entry.get('timestamp', datetime.now().isoformat())))
            timestamp = feedback_entry.get('timestamp', datetime.now().isoformat())
            category = feedback_entry.get('category', 'general')
            feedback_type = feedback_entry.get('feedback_type', 'comment')

            # Perform sentiment analysis
            sentiment = self.analyze_sentiment(content)

            # Calculate impact score
            impact_score = self.calculate_user_impact_score(sentiment, category, feedback_type)

            # Store analysis results
            with sqlite3.connect(self.feedback_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO feedback_analysis
                    (feedback_id, timestamp, category, feedback_type, content,
                     sentiment_score, sentiment_confidence, sentiment_label,
                     key_phrases, emotion_indicators, user_impact_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feedback_id,
                    timestamp,
                    category,
                    feedback_type,
                    content,
                    sentiment.score,
                    sentiment.confidence,
                    sentiment.sentiment_label,
                    json.dumps(sentiment.key_phrases),
                    json.dumps(sentiment.emotion_indicators),
                    impact_score
                ))

            logger.info(f"Processed feedback {feedback_id}: {sentiment.sentiment_label} ({sentiment.score:.2f})")
            return feedback_id

        except Exception as e:
            logger.error(f"Error processing feedback entry: {e}")
            return None

    def generate_insights(self, days: int = 30) -> List[FeedbackInsight]:
        """Generate actionable insights from feedback analysis."""

        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.feedback_db_path) as conn:
            # Get recent feedback
            df = pd.read_sql_query('''
                SELECT * FROM feedback_analysis
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_date.isoformat(),))

        if df.empty:
            return []

        insights = []

        # 1. High-impact negative feedback
        high_impact_negative = df[
            (df['sentiment_label'] == 'negative') &
            (df['user_impact_score'] >= 5.0)
        ]

        if not high_impact_negative.empty:
            for category in high_impact_negative['category'].unique():
                cat_feedback = high_impact_negative[high_impact_negative['category'] == category]

                # Find common issues
                all_content = ' '.join(cat_feedback['content'].values)
                affected_features = self.identify_affected_features(all_content)

                insights.append(FeedbackInsight(
                    category=category,
                    priority="high",
                    insight_type="issue",
                    description=f"High-impact negative feedback in {category} category ({len(cat_feedback)} reports)",
                    affected_features=affected_features,
                    user_impact_score=cat_feedback['user_impact_score'].mean(),
                    recommended_actions=[
                        f"Review and prioritize {category}-related issues",
                        "Analyze specific user pain points in feedback",
                        "Consider immediate fixes for critical issues"
                    ]
                ))

        # 2. Feature requests with high sentiment
        feature_requests = df[df['feedback_type'] == 'feature_request']
        if not feature_requests.empty:
            positive_features = feature_requests[feature_requests['sentiment_score'] > 0.3]

            if not positive_features.empty:
                insights.append(FeedbackInsight(
                    category="features",
                    priority="medium",
                    insight_type="suggestion",
                    description=f"Popular feature requests identified ({len(positive_features)} requests)",
                    affected_features=[],
                    user_impact_score=positive_features['user_impact_score'].mean(),
                    recommended_actions=[
                        "Analyze most requested features for development roadmap",
                        "Consider user voting system for feature priorities",
                        "Provide feedback to users on feature request status"
                    ]
                ))

        # 3. Positive feedback patterns
        positive_feedback = df[df['sentiment_label'] == 'positive']
        if not positive_feedback.empty:
            # Analyze what users appreciate
            all_positive_content = ' '.join(positive_feedback['content'].values)
            appreciated_features = self.identify_affected_features(all_positive_content)

            insights.append(FeedbackInsight(
                category="praise",
                priority="low",
                insight_type="praise",
                description=f"Strong positive feedback received ({len(positive_feedback)} entries)",
                affected_features=appreciated_features,
                user_impact_score=positive_feedback['user_impact_score'].mean(),
                recommended_actions=[
                    "Continue maintaining appreciated features",
                    "Use positive feedback in marketing/documentation",
                    "Understand what works well for future development"
                ]
            ))

        # 4. Usability concerns
        usability_issues = df[
            (df['category'] == 'usability') &
            (df['sentiment_label'] != 'positive')
        ]

        if not usability_issues.empty:
            insights.append(FeedbackInsight(
                category="usability",
                priority="medium",
                insight_type="improvement",
                description=f"Usability concerns identified ({len(usability_issues)} reports)",
                affected_features=self.identify_affected_features(' '.join(usability_issues['content'].values)),
                user_impact_score=usability_issues['user_impact_score'].mean(),
                recommended_actions=[
                    "Conduct usability testing on identified areas",
                    "Review UI/UX design for problem areas",
                    "Consider user onboarding improvements"
                ]
            ))

        return sorted(insights, key=lambda x: x.user_impact_score, reverse=True)

    def generate_analysis_report(self, days: int = 30) -> FeedbackAnalysisReport:
        """Generate comprehensive feedback analysis report."""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.feedback_db_path) as conn:
            # Get feedback data for the period
            df = pd.read_sql_query('''
                SELECT * FROM feedback_analysis
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            ''', conn, params=(start_date.isoformat(), end_date.isoformat()))

        # Calculate metrics
        total_feedback = len(df)
        sentiment_distribution = df['sentiment_label'].value_counts().to_dict() if not df.empty else {}
        category_breakdown = df['category'].value_counts().to_dict() if not df.empty else {}

        # Calculate user satisfaction score (0-5 scale)
        if not df.empty:
            # Convert sentiment scores to 1-5 scale
            sentiment_scores_1_5 = ((df['sentiment_score'] + 1) * 2) + 1  # Convert -1,1 to 1,5
            user_satisfaction_score = sentiment_scores_1_5.mean()
        else:
            user_satisfaction_score = 3.0  # Neutral default

        # Generate insights
        insights = self.generate_insights(days)

        # Analyze trends
        trend_analysis = {}
        if not df.empty and len(df) > 7:
            # Split into first and second half for trend analysis
            mid_point = len(df) // 2
            first_half = df[:mid_point]
            second_half = df[mid_point:]

            trend_analysis = {
                "sentiment_trend": {
                    "first_half_avg": first_half['sentiment_score'].mean(),
                    "second_half_avg": second_half['sentiment_score'].mean(),
                    "direction": "improving" if second_half['sentiment_score'].mean() > first_half['sentiment_score'].mean() else "declining"
                },
                "volume_trend": {
                    "first_half_count": len(first_half),
                    "second_half_count": len(second_half),
                    "direction": "increasing" if len(second_half) > len(first_half) else "decreasing"
                }
            }

        # Generate recommendations
        recommendations = []

        if total_feedback == 0:
            recommendations.append("No feedback data available - consider implementing feedback collection")
        else:
            negative_percentage = sentiment_distribution.get('negative', 0) / total_feedback * 100
            if negative_percentage > 30:
                recommendations.append(f"High negative feedback rate ({negative_percentage:.1f}%) - immediate attention needed")

            if user_satisfaction_score < 3.5:
                recommendations.append(f"Low user satisfaction score ({user_satisfaction_score:.1f}/5.0) - focus on user experience")

            if len([i for i in insights if i.priority == "high"]) > 0:
                recommendations.append("High-priority issues identified - address critical user concerns")

        if not recommendations:
            recommendations.append("Feedback analysis shows positive trends - continue monitoring")

        report = FeedbackAnalysisReport(
            report_id=f"FEEDBACK_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_feedback_count=total_feedback,
            sentiment_distribution=sentiment_distribution,
            category_breakdown=category_breakdown,
            insights=insights,
            trend_analysis=trend_analysis,
            user_satisfaction_score=user_satisfaction_score,
            recommendations=recommendations
        )

        # Save report
        report_file = self.reports_dir / f"feedback_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"Feedback analysis report generated: {report_file}")
        return report


if __name__ == "__main__":
    analyzer = FeedbackSentimentAnalyzer()

    # Generate analysis report
    report = analyzer.generate_analysis_report(days=30)
    print(f"Generated report: {report.report_id}")
    print(f"Total feedback: {report.total_feedback_count}")
    print(f"User satisfaction: {report.user_satisfaction_score:.1f}/5.0")
    print(f"Insights generated: {len(report.insights)}")