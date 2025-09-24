"""
Collaborative Features Module

This module provides collaborative functionality for the financial analysis application,
including analysis sharing, annotations, real-time collaboration, and session management.
"""

from .analysis_sharing import AnalysisShareManager, SharedAnalysis, AnalysisType, SharePermission
from .annotations import AnnotationManager, AnalysisAnnotation, AnnotationType, AnnotationScope
from .collaboration_manager import CollaborationManager
from .shared_workspaces import WorkspaceManager, SharedWorkspace, WorkspaceType, WorkspaceMemberRole
from .session_manager import (
    SessionManager,
    CollaborativeSession,
    SessionStatus,
    get_session_manager,
    create_session_for_user,
    get_current_session,
    validate_current_session,
    terminate_current_session
)
from .realtime_collaboration import (
    RealtimeCollaborationManager,
    CollaborationRoom,
    EventType,
    UserPresence,
    get_realtime_manager,
    join_analysis_collaboration,
    leave_analysis_collaboration,
    update_user_cursor,
    send_analysis_chat_message,
    broadcast_annotation_change
)

__all__ = [
    # Analysis Sharing
    'AnalysisShareManager',
    'SharedAnalysis',
    'AnalysisType',
    'SharePermission',

    # Annotations
    'AnnotationManager',
    'AnalysisAnnotation',
    'AnnotationType',
    'AnnotationScope',

    # Workspaces
    'WorkspaceManager',
    'SharedWorkspace',
    'WorkspaceType',
    'WorkspaceMemberRole',

    # Session Management
    'SessionManager',
    'CollaborativeSession',
    'SessionStatus',
    'get_session_manager',
    'create_session_for_user',
    'get_current_session',
    'validate_current_session',
    'terminate_current_session',

    # Real-time Collaboration
    'RealtimeCollaborationManager',
    'CollaborationRoom',
    'EventType',
    'UserPresence',
    'get_realtime_manager',
    'join_analysis_collaboration',
    'leave_analysis_collaboration',
    'update_user_cursor',
    'send_analysis_chat_message',
    'broadcast_annotation_change',

    # Central Manager
    'CollaborationManager'
]