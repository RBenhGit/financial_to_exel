"""
User Session Management for Collaboration

Manages user sessions, authentication context, and collaborative state
for the financial analysis application.
"""

import uuid
import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, List
from enum import Enum
import json

from ..user_preferences.user_profile import UserProfile, create_default_user_profile

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status types"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class CollaborativeSession:
    """Represents a user session with collaborative context"""

    session_id: str
    user_profile: UserProfile
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    status: SessionStatus = SessionStatus.ACTIVE

    # Collaborative context
    active_analyses: List[str] = field(default_factory=list)  # Analysis IDs being worked on
    shared_workspaces: List[str] = field(default_factory=list)  # Workspace IDs user has access to
    active_shares: List[str] = field(default_factory=list)  # Share IDs user is viewing

    # Session data
    session_data: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def __post_init__(self):
        """Initialize session ID if not provided"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now() > self.expires_at or self.status == SessionStatus.EXPIRED

    def is_active(self) -> bool:
        """Check if session is active"""
        return (self.status == SessionStatus.ACTIVE and
                not self.is_expired())

    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        if self.is_active():
            self.expires_at = datetime.now() + timedelta(hours=hours)
            self.update_activity()

    def add_active_analysis(self, analysis_id: str):
        """Add analysis to active list"""
        if analysis_id not in self.active_analyses:
            self.active_analyses.append(analysis_id)
        self.update_activity()

    def remove_active_analysis(self, analysis_id: str):
        """Remove analysis from active list"""
        if analysis_id in self.active_analyses:
            self.active_analyses.remove(analysis_id)
        self.update_activity()

    def add_workspace_access(self, workspace_id: str):
        """Add workspace to accessible list"""
        if workspace_id not in self.shared_workspaces:
            self.shared_workspaces.append(workspace_id)
        self.update_activity()

    def remove_workspace_access(self, workspace_id: str):
        """Remove workspace from accessible list"""
        if workspace_id in self.shared_workspaces:
            self.shared_workspaces.remove(workspace_id)
        self.update_activity()

    def add_active_share(self, share_id: str):
        """Add share to active viewing list"""
        if share_id not in self.active_shares:
            self.active_shares.append(share_id)
        self.update_activity()

    def remove_active_share(self, share_id: str):
        """Remove share from active viewing list"""
        if share_id in self.active_shares:
            self.active_shares.remove(share_id)
        self.update_activity()

    def set_session_data(self, key: str, value: Any):
        """Set session-specific data"""
        self.session_data[key] = value
        self.update_activity()

    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session-specific data"""
        return self.session_data.get(key, default)

    def terminate(self):
        """Terminate the session"""
        self.status = SessionStatus.TERMINATED
        self.session_data.clear()
        self.active_analyses.clear()
        self.active_shares.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "user_profile": self.user_profile.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "active_analyses": self.active_analyses,
            "shared_workspaces": self.shared_workspaces,
            "active_shares": self.active_shares,
            "session_data": self.session_data,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborativeSession':
        """Create session from dictionary"""
        # Handle datetime fields
        for field_name in ['created_at', 'last_activity', 'expires_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except:
                    if field_name == 'expires_at':
                        data[field_name] = datetime.now() + timedelta(hours=24)
                    else:
                        data[field_name] = datetime.now()

        # Handle status enum
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = SessionStatus(data['status'])

        # Handle user profile
        if 'user_profile' in data and isinstance(data['user_profile'], dict):
            data['user_profile'] = UserProfile.from_dict(data['user_profile'])

        return cls(**data)


class SessionManager:
    """Manages user sessions for collaborative features"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize session manager"""
        self.storage_path = storage_path or Path("data/sessions")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._active_sessions: Dict[str, CollaborativeSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids

        # Session configuration
        self.default_session_duration_hours = 24
        self.max_sessions_per_user = 5
        self.cleanup_interval_hours = 1

        # Load existing sessions
        self._load_sessions()

    def _load_sessions(self):
        """Load sessions from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = CollaborativeSession.from_dict(data)

                    # Only load active, non-expired sessions
                    if session.is_active():
                        self._add_session_to_memory(session)
                    else:
                        # Clean up expired session file
                        file_path.unlink()

        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")

    def _add_session_to_memory(self, session: CollaborativeSession):
        """Add session to in-memory storage"""
        self._active_sessions[session.session_id] = session

        # Update user session index
        user_id = session.user_profile.user_id
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []

        if session.session_id not in self._user_sessions[user_id]:
            self._user_sessions[user_id].append(session.session_id)

    def _save_session(self, session: CollaborativeSession):
        """Save session to storage"""
        try:
            file_path = self.storage_path / f"{session.session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")

    def _remove_session_file(self, session_id: str):
        """Remove session file from storage"""
        try:
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to remove session file {session_id}: {e}")

    def create_session(self,
                      user_id: str,
                      username: str,
                      email: Optional[str] = None,
                      user_profile: Optional[UserProfile] = None,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      session_duration_hours: Optional[int] = None) -> CollaborativeSession:
        """Create a new user session"""

        # Cleanup old sessions for this user first
        self._cleanup_user_sessions(user_id)

        # Create or use existing user profile
        if user_profile is None:
            user_profile = create_default_user_profile(user_id, username, email)

        # Update login info
        user_profile.update_login_info()

        # Create session
        duration = session_duration_hours or self.default_session_duration_hours
        session = CollaborativeSession(
            session_id=str(uuid.uuid4()),
            user_profile=user_profile,
            expires_at=datetime.now() + timedelta(hours=duration),
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Store session
        self._add_session_to_memory(session)
        self._save_session(session)

        logger.info(f"Created session {session.session_id} for user {user_id}")
        return session

    def get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get session by ID"""
        session = self._active_sessions.get(session_id)

        if session and session.is_expired():
            self.terminate_session(session_id)
            return None

        return session

    def get_user_sessions(self, user_id: str) -> List[CollaborativeSession]:
        """Get all active sessions for a user"""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []

        for session_id in session_ids.copy():  # Copy to avoid modification during iteration
            session = self._active_sessions.get(session_id)
            if session and session.is_active():
                sessions.append(session)
            else:
                # Clean up expired session
                self._cleanup_session(session_id, user_id)

        return sessions

    def validate_session(self, session_id: str) -> bool:
        """Validate if session is active and not expired"""
        session = self.get_session(session_id)
        if session:
            session.update_activity()
            self._save_session(session)
            return True
        return False

    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration"""
        session = self.get_session(session_id)
        if session:
            session.extend_session(hours)
            self._save_session(session)
            return True
        return False

    def update_session_activity(self, session_id: str,
                               analysis_id: Optional[str] = None,
                               workspace_id: Optional[str] = None,
                               share_id: Optional[str] = None) -> bool:
        """Update session activity with collaborative context"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.update_activity()

        if analysis_id:
            session.add_active_analysis(analysis_id)

        if workspace_id:
            session.add_workspace_access(workspace_id)

        if share_id:
            session.add_active_share(share_id)

        self._save_session(session)
        return True

    def set_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """Set session-specific data"""
        session = self.get_session(session_id)
        if session:
            session.set_session_data(key, value)
            self._save_session(session)
            return True
        return False

    def get_session_data(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get session-specific data"""
        session = self.get_session(session_id)
        if session:
            return session.get_session_data(key, default)
        return default

    def terminate_session(self, session_id: str) -> bool:
        """Terminate a session"""
        session = self._active_sessions.get(session_id)
        if session:
            user_id = session.user_profile.user_id
            session.terminate()

            # Remove from memory and storage
            self._cleanup_session(session_id, user_id)

            logger.info(f"Terminated session {session_id}")
            return True
        return False

    def terminate_user_sessions(self, user_id: str) -> int:
        """Terminate all sessions for a user"""
        session_ids = self._user_sessions.get(user_id, []).copy()
        terminated_count = 0

        for session_id in session_ids:
            if self.terminate_session(session_id):
                terminated_count += 1

        return terminated_count

    def _cleanup_session(self, session_id: str, user_id: str):
        """Clean up session from memory and storage"""
        # Remove from memory
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        # Remove from user session index
        if user_id in self._user_sessions:
            if session_id in self._user_sessions[user_id]:
                self._user_sessions[user_id].remove(session_id)

            # Clean up empty user session list
            if not self._user_sessions[user_id]:
                del self._user_sessions[user_id]

        # Remove from storage
        self._remove_session_file(session_id)

    def _cleanup_user_sessions(self, user_id: str):
        """Clean up old sessions for a user if they exceed the limit"""
        user_sessions = self.get_user_sessions(user_id)

        if len(user_sessions) >= self.max_sessions_per_user:
            # Sort by last activity and terminate oldest sessions
            user_sessions.sort(key=lambda s: s.last_activity)

            sessions_to_terminate = len(user_sessions) - self.max_sessions_per_user + 1
            for i in range(sessions_to_terminate):
                self.terminate_session(user_sessions[i].session_id)

    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions"""
        expired_sessions = []

        for session_id, session in self._active_sessions.items():
            if session.is_expired():
                expired_sessions.append((session_id, session.user_profile.user_id))

        for session_id, user_id in expired_sessions:
            self._cleanup_session(session_id, user_id)

        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self._active_sessions)
        total_users = len(self._user_sessions)

        # Activity statistics
        recent_activity_cutoff = datetime.now() - timedelta(hours=1)
        recently_active = sum(
            1 for session in self._active_sessions.values()
            if session.last_activity >= recent_activity_cutoff
        )

        # Average session duration
        total_duration = sum(
            (session.last_activity - session.created_at).total_seconds()
            for session in self._active_sessions.values()
        )
        avg_duration_minutes = (total_duration / total_sessions / 60) if total_sessions > 0 else 0

        return {
            "total_active_sessions": total_sessions,
            "total_users_with_sessions": total_users,
            "recently_active_sessions": recently_active,
            "average_session_duration_minutes": avg_duration_minutes,
            "sessions_by_user": {
                user_id: len(session_ids)
                for user_id, session_ids in self._user_sessions.items()
            }
        }

    def get_collaborative_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get collaborative context for a session"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "user_id": session.user_profile.user_id,
            "username": session.user_profile.username,
            "active_analyses": session.active_analyses,
            "shared_workspaces": session.shared_workspaces,
            "active_shares": session.active_shares,
            "session_created": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "session_expires": session.expires_at.isoformat()
        }


# Singleton instance for global access
_session_manager_instance: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance


def create_session_for_user(user_id: str,
                           username: str,
                           email: Optional[str] = None,
                           **kwargs) -> CollaborativeSession:
    """Convenience function to create a session"""
    manager = get_session_manager()
    return manager.create_session(user_id, username, email, **kwargs)


def get_current_session(session_id: str) -> Optional[CollaborativeSession]:
    """Convenience function to get current session"""
    manager = get_session_manager()
    return manager.get_session(session_id)


def validate_current_session(session_id: str) -> bool:
    """Convenience function to validate session"""
    manager = get_session_manager()
    return manager.validate_session(session_id)


def terminate_current_session(session_id: str) -> bool:
    """Convenience function to terminate session"""
    manager = get_session_manager()
    return manager.terminate_session(session_id)