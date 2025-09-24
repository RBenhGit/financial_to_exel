"""
User Analytics Tracking System

Comprehensive analytics tracking for user behavior, analysis history,
and usage patterns in the financial analysis application.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of financial analyses"""
    DCF = "dcf"
    DDM = "ddm"
    FCF = "fcf"
    PB_RATIO = "pb_ratio"
    MONTE_CARLO = "monte_carlo"
    RISK_ANALYSIS = "risk_analysis"
    PORTFOLIO = "portfolio"
    COMPARISON = "comparison"


class EventType(Enum):
    """Types of user events to track"""
    LOGIN = "login"
    LOGOUT = "logout"
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_EXPORT = "analysis_export"
    SEARCH = "search"
    FAVORITE_ADD = "favorite_add"
    FAVORITE_REMOVE = "favorite_remove"
    PREFERENCE_UPDATE = "preference_update"
    DATA_UPLOAD = "data_upload"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class AnalysisSession:
    """Represents a single analysis session"""
    session_id: str
    analysis_type: AnalysisType
    company_ticker: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None

    # Analysis parameters used
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Results summary
    results: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    execution_time_seconds: float = 0.0
    data_quality_score: float = 0.0
    cache_hits: int = 0
    api_calls: int = 0


@dataclass
class UserEvent:
    """Represents a single user event"""
    event_id: str
    user_id: str
    event_type: EventType
    timestamp: datetime

    # Event-specific data
    details: Dict[str, Any] = field(default_factory=dict)

    # Context information
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UsageStatistics:
    """Aggregated usage statistics for a user"""
    user_id: str
    period_start: datetime
    period_end: datetime

    # Analysis statistics
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    analyses_by_type: Dict[str, int] = field(default_factory=dict)

    # Time-based statistics
    total_session_time_minutes: float = 0.0
    average_analysis_time_seconds: float = 0.0
    peak_usage_hour: Optional[int] = None

    # Data usage statistics
    total_companies_analyzed: int = 0
    unique_companies_analyzed: int = 0
    favorite_companies_count: int = 0

    # Performance statistics
    average_data_quality_score: float = 0.0
    cache_hit_rate: float = 0.0
    api_call_efficiency: float = 0.0

    # Error statistics
    error_count: int = 0
    common_errors: List[str] = field(default_factory=list)


class UserAnalyticsTracker:
    """Tracks and manages user analytics data"""

    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the analytics tracker

        Args:
            data_directory: Directory to store analytics data
        """
        self._lock = threading.Lock()

        # Set up data directory
        if data_directory:
            self.data_dir = Path(data_directory)
        else:
            self.data_dir = Path("data") / "analytics"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Analytics file paths
        self.events_dir = self.data_dir / "events"
        self.sessions_dir = self.data_dir / "sessions"
        self.statistics_dir = self.data_dir / "statistics"

        for dir_path in [self.events_dir, self.sessions_dir, self.statistics_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"UserAnalyticsTracker initialized with data directory: {self.data_dir}")

    def track_event(self, event: UserEvent) -> bool:
        """
        Track a user event

        Args:
            event: The event to track

        Returns:
            bool: True if successful
        """
        try:
            with self._lock:
                # Create daily event file
                date_str = event.timestamp.strftime("%Y%m%d")
                event_file = self.events_dir / f"events_{date_str}.jsonl"

                # Append event to file
                with open(event_file, 'a', encoding='utf-8') as f:
                    event_data = asdict(event)
                    # Handle datetime serialization
                    event_data['timestamp'] = event.timestamp.isoformat()
                    event_data['event_type'] = event.event_type.value

                    f.write(json.dumps(event_data, default=str) + '\n')

                logger.debug(f"Tracked event: {event.event_type.value} for user {event.user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False

    def start_analysis_session(
        self,
        user_id: str,
        analysis_type: AnalysisType,
        company_ticker: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking an analysis session

        Args:
            user_id: User identifier
            analysis_type: Type of analysis being performed
            company_ticker: Company being analyzed
            parameters: Analysis parameters

        Returns:
            str: Session ID for tracking
        """
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        session = AnalysisSession(
            session_id=session_id,
            analysis_type=analysis_type,
            company_ticker=company_ticker.upper(),
            start_time=datetime.now(),
            parameters=parameters or {}
        )

        # Track analysis start event
        event = UserEvent(
            event_id=f"event_{session_id}_start",
            user_id=user_id,
            event_type=EventType.ANALYSIS_START,
            timestamp=datetime.now(),
            session_id=session_id,
            details={
                'analysis_type': analysis_type.value,
                'company_ticker': company_ticker.upper(),
                'parameters': parameters or {}
            }
        )

        self.track_event(event)

        # Save session data
        self._save_session(session)

        logger.info(f"Started analysis session {session_id} for {company_ticker}")
        return session_id

    def complete_analysis_session(
        self,
        session_id: str,
        success: bool = True,
        results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Complete an analysis session

        Args:
            session_id: Session identifier
            success: Whether the analysis was successful
            results: Analysis results summary
            error_message: Error message if failed
            performance_metrics: Performance data

        Returns:
            bool: True if successful
        """
        try:
            session = self._load_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False

            # Update session data
            session.end_time = datetime.now()
            session.success = success
            session.error_message = error_message
            session.results = results or {}

            if session.start_time:
                session.execution_time_seconds = (session.end_time - session.start_time).total_seconds()

            # Update performance metrics
            if performance_metrics:
                session.data_quality_score = performance_metrics.get('data_quality_score', 0.0)
                session.cache_hits = performance_metrics.get('cache_hits', 0)
                session.api_calls = performance_metrics.get('api_calls', 0)

            # Save updated session
            self._save_session(session)

            # Track completion event
            event = UserEvent(
                event_id=f"event_{session_id}_complete",
                user_id=session_id.split('_')[0],  # Extract user_id from session_id
                event_type=EventType.ANALYSIS_COMPLETE,
                timestamp=datetime.now(),
                session_id=session_id,
                details={
                    'success': success,
                    'execution_time': session.execution_time_seconds,
                    'error_message': error_message
                }
            )

            self.track_event(event)

            logger.info(f"Completed analysis session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            return False

    def track_user_search(self, user_id: str, search_term: str, results_count: int = 0) -> bool:
        """
        Track a user search event

        Args:
            user_id: User identifier
            search_term: Search term used
            results_count: Number of results returned

        Returns:
            bool: True if successful
        """
        event = UserEvent(
            event_id=f"search_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            user_id=user_id,
            event_type=EventType.SEARCH,
            timestamp=datetime.now(),
            details={
                'search_term': search_term,
                'results_count': results_count
            }
        )

        return self.track_event(event)

    def track_favorite_action(self, user_id: str, company_ticker: str, action: str) -> bool:
        """
        Track favorite company actions

        Args:
            user_id: User identifier
            company_ticker: Company ticker
            action: 'add' or 'remove'

        Returns:
            bool: True if successful
        """
        event_type = EventType.FAVORITE_ADD if action == 'add' else EventType.FAVORITE_REMOVE

        event = UserEvent(
            event_id=f"favorite_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now(),
            details={
                'company_ticker': company_ticker.upper(),
                'action': action
            }
        )

        return self.track_event(event)

    def generate_usage_statistics(
        self,
        user_id: str,
        period_days: int = 30
    ) -> Optional[UsageStatistics]:
        """
        Generate usage statistics for a user

        Args:
            user_id: User identifier
            period_days: Number of days to analyze

        Returns:
            UsageStatistics or None if failed
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # Load events for the period
            events = self._load_events_for_period(user_id, start_date, end_date)
            sessions = self._load_sessions_for_period(user_id, start_date, end_date)

            # Initialize statistics
            stats = UsageStatistics(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date
            )

            # Analyze sessions
            if sessions:
                stats.total_analyses = len(sessions)
                stats.successful_analyses = sum(1 for s in sessions if s.success)
                stats.failed_analyses = stats.total_analyses - stats.successful_analyses

                # Analyses by type
                for session in sessions:
                    analysis_type = session.analysis_type.value
                    stats.analyses_by_type[analysis_type] = stats.analyses_by_type.get(analysis_type, 0) + 1

                # Time statistics
                execution_times = [s.execution_time_seconds for s in sessions if s.execution_time_seconds > 0]
                if execution_times:
                    stats.average_analysis_time_seconds = sum(execution_times) / len(execution_times)

                # Company statistics
                companies = [s.company_ticker for s in sessions]
                stats.total_companies_analyzed = len(companies)
                stats.unique_companies_analyzed = len(set(companies))

                # Performance statistics
                quality_scores = [s.data_quality_score for s in sessions if s.data_quality_score > 0]
                if quality_scores:
                    stats.average_data_quality_score = sum(quality_scores) / len(quality_scores)

                # Cache efficiency
                total_cache_hits = sum(s.cache_hits for s in sessions)
                total_api_calls = sum(s.api_calls for s in sessions)
                if total_api_calls > 0:
                    stats.cache_hit_rate = total_cache_hits / (total_cache_hits + total_api_calls)

            # Analyze events
            error_events = [e for e in events if e.event_type == EventType.ERROR_OCCURRED]
            stats.error_count = len(error_events)

            # Save statistics
            self._save_statistics(stats)

            return stats

        except Exception as e:
            logger.error(f"Failed to generate statistics for user {user_id}: {e}")
            return None

    def get_analysis_history(
        self,
        user_id: str,
        limit: int = 50,
        analysis_type: Optional[AnalysisType] = None
    ) -> List[AnalysisSession]:
        """
        Get analysis history for a user

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            analysis_type: Filter by analysis type

        Returns:
            List of analysis sessions
        """
        try:
            sessions = []

            # Load sessions from recent files
            for session_file in sorted(self.sessions_dir.glob(f"{user_id}_*.json"), reverse=True):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    # Convert data back to AnalysisSession
                    session = self._dict_to_session(session_data)

                    # Apply filters
                    if analysis_type and session.analysis_type != analysis_type:
                        continue

                    sessions.append(session)

                    if len(sessions) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Failed to load session file {session_file}: {e}")

            return sessions

        except Exception as e:
            logger.error(f"Failed to get analysis history for user {user_id}: {e}")
            return []

    def _save_session(self, session: AnalysisSession) -> bool:
        """Save analysis session to file"""
        try:
            session_file = self.sessions_dir / f"{session.session_id}.json"
            session_data = asdict(session)

            # Handle datetime serialization
            session_data['start_time'] = session.start_time.isoformat()
            if session.end_time:
                session_data['end_time'] = session.end_time.isoformat()
            session_data['analysis_type'] = session.analysis_type.value

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)

            return True

        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
            return False

    def _load_session(self, session_id: str) -> Optional[AnalysisSession]:
        """Load analysis session from file"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                return None

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            return self._dict_to_session(session_data)

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def _dict_to_session(self, data: Dict[str, Any]) -> AnalysisSession:
        """Convert dictionary to AnalysisSession object"""
        # Handle datetime conversion
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if 'analysis_type' in data and isinstance(data['analysis_type'], str):
            data['analysis_type'] = AnalysisType(data['analysis_type'])

        return AnalysisSession(**data)

    def _load_events_for_period(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[UserEvent]:
        """Load events for a user within a date range"""
        events = []

        # Generate date range
        current_date = start_date.date()
        end_date_date = end_date.date()

        while current_date <= end_date_date:
            date_str = current_date.strftime("%Y%m%d")
            event_file = self.events_dir / f"events_{date_str}.jsonl"

            if event_file.exists():
                try:
                    with open(event_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            event_data = json.loads(line.strip())
                            if event_data.get('user_id') == user_id:
                                # Convert back to UserEvent (simplified)
                                events.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to load events from {event_file}: {e}")

            current_date += timedelta(days=1)

        return events

    def _load_sessions_for_period(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[AnalysisSession]:
        """Load sessions for a user within a date range"""
        sessions = []

        # Load all session files for the user
        for session_file in self.sessions_dir.glob(f"{user_id}_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                session = self._dict_to_session(session_data)

                # Check if session is within date range
                if start_date <= session.start_time <= end_date:
                    sessions.append(session)

            except Exception as e:
                logger.warning(f"Failed to load session file {session_file}: {e}")

        return sessions

    def _save_statistics(self, stats: UsageStatistics) -> bool:
        """Save usage statistics to file"""
        try:
            date_str = stats.period_end.strftime("%Y%m%d")
            stats_file = self.statistics_dir / f"stats_{stats.user_id}_{date_str}.json"

            stats_data = asdict(stats)
            stats_data['period_start'] = stats.period_start.isoformat()
            stats_data['period_end'] = stats.period_end.isoformat()

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, default=str)

            return True

        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")
            return False


# Global instance
_analytics_tracker: Optional[UserAnalyticsTracker] = None


def get_analytics_tracker(data_directory: Optional[str] = None) -> UserAnalyticsTracker:
    """
    Get the global analytics tracker instance

    Args:
        data_directory: Directory for analytics data

    Returns:
        UserAnalyticsTracker instance
    """
    global _analytics_tracker
    if _analytics_tracker is None:
        _analytics_tracker = UserAnalyticsTracker(data_directory)
    return _analytics_tracker


def set_analytics_tracker(tracker: UserAnalyticsTracker) -> None:
    """Set a custom analytics tracker instance"""
    global _analytics_tracker
    _analytics_tracker = tracker