"""
Real-time Collaboration System

Provides real-time collaborative features for financial analysis,
including live cursors, simultaneous editing notifications, and live chat.
"""

import json
import uuid
import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from enum import Enum
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of real-time collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_MOVED = "cursor_moved"
    ANNOTATION_ADDED = "annotation_added"
    ANNOTATION_UPDATED = "annotation_updated"
    ANNOTATION_DELETED = "annotation_deleted"
    ANALYSIS_UPDATED = "analysis_updated"
    CHAT_MESSAGE = "chat_message"
    TYPING_INDICATOR = "typing_indicator"
    PRESENCE_UPDATE = "presence_update"
    SHARE_UPDATED = "share_updated"


class UserPresence(Enum):
    """User presence status"""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class CursorPosition:
    """Represents a user's cursor position in the analysis"""
    user_id: str
    username: str
    x: float
    y: float
    element_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    color: str = "#007bff"  # Default blue


@dataclass
class CollaborationEvent:
    """Real-time collaboration event"""
    event_id: str
    event_type: EventType
    analysis_id: str
    user_id: str
    username: str
    timestamp: datetime
    data: Dict[str, Any]
    room_id: Optional[str] = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for transmission"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "username": self.username,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "room_id": self.room_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationEvent':
        """Create event from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            analysis_id=data["analysis_id"],
            user_id=data["user_id"],
            username=data["username"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            room_id=data.get("room_id")
        )


@dataclass
class CollaborationRoom:
    """Represents a collaboration room for an analysis"""
    room_id: str
    analysis_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # Connected users
    connected_users: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    user_cursors: Dict[str, CursorPosition] = field(default_factory=dict)
    user_presence: Dict[str, UserPresence] = field(default_factory=dict)

    # Event history (limited)
    recent_events: List[CollaborationEvent] = field(default_factory=list)
    max_events: int = 100

    # Room settings
    allow_anonymous: bool = False
    max_users: Optional[int] = None

    def add_user(self, user_id: str, username: str, session_id: str,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add user to collaboration room"""
        if self.max_users and len(self.connected_users) >= self.max_users:
            return False

        self.connected_users[user_id] = {
            "username": username,
            "session_id": session_id,
            "joined_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.user_presence[user_id] = UserPresence.ONLINE

        # Broadcast user joined event
        self._add_event(
            event_type=EventType.USER_JOINED,
            user_id=user_id,
            username=username,
            data={"user_count": len(self.connected_users)}
        )

        return True

    def remove_user(self, user_id: str) -> bool:
        """Remove user from collaboration room"""
        if user_id not in self.connected_users:
            return False

        username = self.connected_users[user_id]["username"]

        # Clean up user data
        del self.connected_users[user_id]
        self.user_cursors.pop(user_id, None)
        self.user_presence.pop(user_id, None)

        # Broadcast user left event
        self._add_event(
            event_type=EventType.USER_LEFT,
            user_id=user_id,
            username=username,
            data={"user_count": len(self.connected_users)}
        )

        return True

    def update_cursor(self, user_id: str, cursor_position: CursorPosition):
        """Update user's cursor position"""
        if user_id in self.connected_users:
            self.user_cursors[user_id] = cursor_position

            # Broadcast cursor movement (limited frequency)
            self._add_event(
                event_type=EventType.CURSOR_MOVED,
                user_id=user_id,
                username=cursor_position.username,
                data={
                    "x": cursor_position.x,
                    "y": cursor_position.y,
                    "element_id": cursor_position.element_id,
                    "color": cursor_position.color
                }
            )

    def update_presence(self, user_id: str, presence: UserPresence):
        """Update user presence status"""
        if user_id in self.connected_users:
            self.user_presence[user_id] = presence
            username = self.connected_users[user_id]["username"]

            self._add_event(
                event_type=EventType.PRESENCE_UPDATE,
                user_id=user_id,
                username=username,
                data={"presence": presence.value}
            )

    def add_chat_message(self, user_id: str, message: str):
        """Add chat message to room"""
        if user_id in self.connected_users:
            username = self.connected_users[user_id]["username"]

            self._add_event(
                event_type=EventType.CHAT_MESSAGE,
                user_id=user_id,
                username=username,
                data={"message": message}
            )

    def broadcast_annotation_event(self, event_type: EventType, user_id: str,
                                 annotation_data: Dict[str, Any]):
        """Broadcast annotation-related event"""
        if user_id in self.connected_users:
            username = self.connected_users[user_id]["username"]

            self._add_event(
                event_type=event_type,
                user_id=user_id,
                username=username,
                data=annotation_data
            )

    def broadcast_analysis_update(self, user_id: str, update_data: Dict[str, Any]):
        """Broadcast analysis update event"""
        if user_id in self.connected_users:
            username = self.connected_users[user_id]["username"]

            self._add_event(
                event_type=EventType.ANALYSIS_UPDATED,
                user_id=user_id,
                username=username,
                data=update_data
            )

    def _add_event(self, event_type: EventType, user_id: str, username: str,
                   data: Dict[str, Any]):
        """Add event to room history"""
        event = CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            analysis_id=self.analysis_id,
            user_id=user_id,
            username=username,
            timestamp=datetime.now(),
            data=data,
            room_id=self.room_id
        )

        self.recent_events.append(event)

        # Maintain event history size
        if len(self.recent_events) > self.max_events:
            self.recent_events = self.recent_events[-self.max_events:]

    def get_room_state(self) -> Dict[str, Any]:
        """Get current room state"""
        return {
            "room_id": self.room_id,
            "analysis_id": self.analysis_id,
            "user_count": len(self.connected_users),
            "connected_users": [
                {
                    "user_id": uid,
                    "username": info["username"],
                    "presence": self.user_presence.get(uid, UserPresence.OFFLINE).value,
                    "joined_at": info["joined_at"]
                }
                for uid, info in self.connected_users.items()
            ],
            "cursors": [
                {
                    "user_id": cursor.user_id,
                    "username": cursor.username,
                    "x": cursor.x,
                    "y": cursor.y,
                    "element_id": cursor.element_id,
                    "color": cursor.color
                }
                for cursor in self.user_cursors.values()
            ]
        }


class RealtimeCollaborationManager:
    """Manages real-time collaboration features"""

    def __init__(self):
        """Initialize collaboration manager"""
        self._rooms: Dict[str, CollaborationRoom] = {}
        self._user_rooms: Dict[str, Set[str]] = defaultdict(set)  # user_id -> room_ids
        self._analysis_rooms: Dict[str, str] = {}  # analysis_id -> room_id

        # Event handlers
        self._event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)

        # WebSocket connections (placeholder for actual WebSocket implementation)
        self._connections: Dict[str, Any] = {}  # session_id -> connection

        # Configuration
        self.default_room_max_users = 20
        self.cursor_update_throttle_ms = 100

        # Background cleanup
        self._cleanup_interval = 300  # 5 minutes
        self._start_cleanup_task()

    def create_room(self, analysis_id: str, room_id: Optional[str] = None,
                   max_users: Optional[int] = None) -> CollaborationRoom:
        """Create or get collaboration room for analysis"""

        # Check if room already exists for this analysis
        if analysis_id in self._analysis_rooms:
            existing_room_id = self._analysis_rooms[analysis_id]
            if existing_room_id in self._rooms:
                return self._rooms[existing_room_id]

        # Create new room
        room_id = room_id or f"room_{analysis_id}_{uuid.uuid4().hex[:8]}"

        room = CollaborationRoom(
            room_id=room_id,
            analysis_id=analysis_id,
            max_users=max_users or self.default_room_max_users
        )

        self._rooms[room_id] = room
        self._analysis_rooms[analysis_id] = room_id

        logger.info(f"Created collaboration room {room_id} for analysis {analysis_id}")
        return room

    def join_room(self, analysis_id: str, user_id: str, username: str,
                 session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[CollaborationRoom]:
        """Join collaboration room for analysis"""

        # Get or create room
        room = self.create_room(analysis_id)

        # Add user to room
        if room.add_user(user_id, username, session_id, metadata):
            self._user_rooms[user_id].add(room.room_id)

            # Trigger event handlers
            self._trigger_event_handlers(EventType.USER_JOINED, room.recent_events[-1])

            logger.info(f"User {username} joined room {room.room_id}")
            return room

        return None

    def leave_room(self, room_id: str, user_id: str) -> bool:
        """Leave collaboration room"""
        room = self._rooms.get(room_id)
        if not room:
            return False

        if room.remove_user(user_id):
            self._user_rooms[user_id].discard(room_id)

            # Trigger event handlers
            if room.recent_events:
                self._trigger_event_handlers(EventType.USER_LEFT, room.recent_events[-1])

            # Clean up empty room
            if not room.connected_users:
                self._cleanup_room(room_id)

            logger.info(f"User {user_id} left room {room_id}")
            return True

        return False

    def leave_all_rooms(self, user_id: str) -> int:
        """Leave all rooms for a user"""
        room_ids = list(self._user_rooms.get(user_id, set()))
        left_count = 0

        for room_id in room_ids:
            if self.leave_room(room_id, user_id):
                left_count += 1

        return left_count

    def update_cursor(self, analysis_id: str, user_id: str, username: str,
                     x: float, y: float, element_id: Optional[str] = None,
                     color: str = "#007bff"):
        """Update user cursor position"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return

        room = self._rooms.get(room_id)
        if not room:
            return

        cursor = CursorPosition(
            user_id=user_id,
            username=username,
            x=x,
            y=y,
            element_id=element_id,
            color=color
        )

        room.update_cursor(user_id, cursor)

        # Trigger event handlers (throttled)
        if room.recent_events:
            self._trigger_event_handlers(EventType.CURSOR_MOVED, room.recent_events[-1])

    def update_presence(self, analysis_id: str, user_id: str, presence: UserPresence):
        """Update user presence status"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return

        room = self._rooms.get(room_id)
        if room:
            room.update_presence(user_id, presence)

            if room.recent_events:
                self._trigger_event_handlers(EventType.PRESENCE_UPDATE, room.recent_events[-1])

    def send_chat_message(self, analysis_id: str, user_id: str, message: str):
        """Send chat message to room"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return

        room = self._rooms.get(room_id)
        if room:
            room.add_chat_message(user_id, message)

            if room.recent_events:
                self._trigger_event_handlers(EventType.CHAT_MESSAGE, room.recent_events[-1])

    def broadcast_annotation_event(self, analysis_id: str, user_id: str,
                                 event_type: EventType, annotation_data: Dict[str, Any]):
        """Broadcast annotation-related event"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return

        room = self._rooms.get(room_id)
        if room:
            room.broadcast_annotation_event(event_type, user_id, annotation_data)

            if room.recent_events:
                self._trigger_event_handlers(event_type, room.recent_events[-1])

    def broadcast_analysis_update(self, analysis_id: str, user_id: str,
                                update_data: Dict[str, Any]):
        """Broadcast analysis update"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return

        room = self._rooms.get(room_id)
        if room:
            room.broadcast_analysis_update(user_id, update_data)

            if room.recent_events:
                self._trigger_event_handlers(EventType.ANALYSIS_UPDATED, room.recent_events[-1])

    def get_room_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get current room state for analysis"""
        room_id = self._analysis_rooms.get(analysis_id)
        if not room_id:
            return None

        room = self._rooms.get(room_id)
        return room.get_room_state() if room else None

    def get_user_rooms(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all rooms user is participating in"""
        room_ids = self._user_rooms.get(user_id, set())
        rooms_info = []

        for room_id in room_ids:
            room = self._rooms.get(room_id)
            if room:
                rooms_info.append(room.get_room_state())

        return rooms_info

    def add_event_handler(self, event_type: EventType, handler: Callable):
        """Add event handler for specific event type"""
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: EventType, handler: Callable):
        """Remove event handler"""
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)

    def _trigger_event_handlers(self, event_type: EventType, event: CollaborationEvent):
        """Trigger event handlers for event type"""
        for handler in self._event_handlers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def _cleanup_room(self, room_id: str):
        """Clean up empty room"""
        if room_id in self._rooms:
            room = self._rooms[room_id]
            analysis_id = room.analysis_id

            del self._rooms[room_id]

            if analysis_id in self._analysis_rooms:
                del self._analysis_rooms[analysis_id]

            logger.info(f"Cleaned up empty room {room_id}")

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup_task():
            while True:
                try:
                    self._periodic_cleanup()
                    threading.Event().wait(self._cleanup_interval)
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def _periodic_cleanup(self):
        """Periodic cleanup of inactive rooms and connections"""
        inactive_rooms = []
        cutoff_time = datetime.now() - timedelta(hours=2)

        for room_id, room in self._rooms.items():
            # Check if room has been inactive for too long
            if (not room.connected_users and
                room.created_at < cutoff_time):
                inactive_rooms.append(room_id)

        # Clean up inactive rooms
        for room_id in inactive_rooms:
            self._cleanup_room(room_id)

    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """Get collaboration statistics"""
        total_rooms = len(self._rooms)
        total_connected_users = sum(len(room.connected_users) for room in self._rooms.values())
        active_rooms = sum(1 for room in self._rooms.values() if room.connected_users)

        return {
            "total_rooms": total_rooms,
            "active_rooms": active_rooms,
            "total_connected_users": total_connected_users,
            "rooms_by_analysis": {
                analysis_id: room_id for analysis_id, room_id in self._analysis_rooms.items()
            }
        }


# Global instance
_realtime_manager: Optional[RealtimeCollaborationManager] = None


def get_realtime_manager() -> RealtimeCollaborationManager:
    """Get global realtime collaboration manager"""
    global _realtime_manager
    if _realtime_manager is None:
        _realtime_manager = RealtimeCollaborationManager()
    return _realtime_manager


# Convenience functions
def join_analysis_collaboration(analysis_id: str, user_id: str, username: str,
                              session_id: str) -> Optional[CollaborationRoom]:
    """Join collaboration for an analysis"""
    manager = get_realtime_manager()
    return manager.join_room(analysis_id, user_id, username, session_id)


def leave_analysis_collaboration(analysis_id: str, user_id: str) -> bool:
    """Leave collaboration for an analysis"""
    manager = get_realtime_manager()
    room_id = manager._analysis_rooms.get(analysis_id)
    if room_id:
        return manager.leave_room(room_id, user_id)
    return False


def update_user_cursor(analysis_id: str, user_id: str, username: str,
                      x: float, y: float, element_id: Optional[str] = None):
    """Update user cursor position in analysis"""
    manager = get_realtime_manager()
    manager.update_cursor(analysis_id, user_id, username, x, y, element_id)


def send_analysis_chat_message(analysis_id: str, user_id: str, message: str):
    """Send chat message in analysis collaboration"""
    manager = get_realtime_manager()
    manager.send_chat_message(analysis_id, user_id, message)


def broadcast_annotation_change(analysis_id: str, user_id: str, event_type: str,
                              annotation_data: Dict[str, Any]):
    """Broadcast annotation change to collaborators"""
    manager = get_realtime_manager()
    try:
        event_enum = EventType(event_type)
        manager.broadcast_annotation_event(analysis_id, user_id, event_enum, annotation_data)
    except ValueError:
        logger.warning(f"Unknown event type: {event_type}")