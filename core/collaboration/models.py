"""
Collaboration data models and schemas for the financial analysis platform.

This module defines the data structures used for collaborative features including
shared analyses, annotations, user management, and workspace management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
import json


class PermissionLevel(Enum):
    """User permission levels for shared content."""
    READ = "read"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class AnalysisType(Enum):
    """Types of financial analyses that can be shared."""
    FCF = "fcf"
    DCF = "dcf"
    DDM = "ddm"
    PB = "pb"
    COMPREHENSIVE = "comprehensive"


class ShareStatus(Enum):
    """Status of shared analyses."""
    DRAFT = "draft"
    SHARED = "shared"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class User:
    """User information for collaboration features."""
    user_id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    email: str = ""
    display_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedAnalysis:
    """Represents a shared financial analysis."""
    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    analysis_type: AnalysisType = AnalysisType.FCF
    ticker: str = ""
    company_name: str = ""

    # Analysis data
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    calculations: Dict[str, Any] = field(default_factory=dict)
    assumptions: Dict[str, Any] = field(default_factory=dict)

    # Sharing metadata
    owner_id: str = ""
    collaborators: Dict[str, PermissionLevel] = field(default_factory=dict)
    status: ShareStatus = ShareStatus.DRAFT

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    shared_at: Optional[datetime] = None

    # Access control
    is_public: bool = False
    access_link: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'analysis_id': self.analysis_id,
            'title': self.title,
            'description': self.description,
            'analysis_type': self.analysis_type.value,
            'ticker': self.ticker,
            'company_name': self.company_name,
            'analysis_data': self.analysis_data,
            'calculations': self.calculations,
            'assumptions': self.assumptions,
            'owner_id': self.owner_id,
            'collaborators': {uid: perm.value for uid, perm in self.collaborators.items()},
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'shared_at': self.shared_at.isoformat() if self.shared_at else None,
            'is_public': self.is_public,
            'access_link': self.access_link
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedAnalysis':
        """Create instance from dictionary."""
        analysis = cls()
        analysis.analysis_id = data.get('analysis_id', analysis.analysis_id)
        analysis.title = data.get('title', '')
        analysis.description = data.get('description', '')
        analysis.analysis_type = AnalysisType(data.get('analysis_type', 'fcf'))
        analysis.ticker = data.get('ticker', '')
        analysis.company_name = data.get('company_name', '')
        analysis.analysis_data = data.get('analysis_data', {})
        analysis.calculations = data.get('calculations', {})
        analysis.assumptions = data.get('assumptions', {})
        analysis.owner_id = data.get('owner_id', '')
        analysis.collaborators = {
            uid: PermissionLevel(perm)
            for uid, perm in data.get('collaborators', {}).items()
        }
        analysis.status = ShareStatus(data.get('status', 'draft'))
        analysis.created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        analysis.updated_at = datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        analysis.shared_at = datetime.fromisoformat(data['shared_at']) if data.get('shared_at') else None
        analysis.is_public = data.get('is_public', False)
        analysis.access_link = data.get('access_link')
        return analysis


@dataclass
class AnalysisAnnotation:
    """Represents an annotation/comment on a shared analysis."""
    annotation_id: str = field(default_factory=lambda: str(uuid4()))
    analysis_id: str = ""
    user_id: str = ""
    username: str = ""

    # Content
    content: str = ""
    annotation_type: str = "comment"  # comment, suggestion, question, highlight

    # Position/context
    context: Dict[str, Any] = field(default_factory=dict)  # For highlighting specific data points
    parent_id: Optional[str] = None  # For threaded conversations

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'annotation_id': self.annotation_id,
            'analysis_id': self.analysis_id,
            'user_id': self.user_id,
            'username': self.username,
            'content': self.content,
            'annotation_type': self.annotation_type,
            'context': self.context,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_resolved': self.is_resolved
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisAnnotation':
        """Create instance from dictionary."""
        annotation = cls()
        annotation.annotation_id = data.get('annotation_id', annotation.annotation_id)
        annotation.analysis_id = data.get('analysis_id', '')
        annotation.user_id = data.get('user_id', '')
        annotation.username = data.get('username', '')
        annotation.content = data.get('content', '')
        annotation.annotation_type = data.get('annotation_type', 'comment')
        annotation.context = data.get('context', {})
        annotation.parent_id = data.get('parent_id')
        annotation.created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        annotation.updated_at = datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        annotation.is_resolved = data.get('is_resolved', False)
        return annotation


@dataclass
class SharedWorkspace:
    """Represents a collaborative workspace containing multiple analyses."""
    workspace_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Content
    analyses: List[str] = field(default_factory=list)  # List of analysis IDs

    # Collaboration
    owner_id: str = ""
    members: Dict[str, PermissionLevel] = field(default_factory=dict)

    # Settings
    is_public: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'workspace_id': self.workspace_id,
            'name': self.name,
            'description': self.description,
            'analyses': self.analyses,
            'owner_id': self.owner_id,
            'members': {uid: perm.value for uid, perm in self.members.items()},
            'is_public': self.is_public,
            'settings': self.settings,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedWorkspace':
        """Create instance from dictionary."""
        workspace = cls()
        workspace.workspace_id = data.get('workspace_id', workspace.workspace_id)
        workspace.name = data.get('name', '')
        workspace.description = data.get('description', '')
        workspace.analyses = data.get('analyses', [])
        workspace.owner_id = data.get('owner_id', '')
        workspace.members = {
            uid: PermissionLevel(perm)
            for uid, perm in data.get('members', {}).items()
        }
        workspace.is_public = data.get('is_public', False)
        workspace.settings = data.get('settings', {})
        workspace.created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        workspace.updated_at = datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        return workspace


@dataclass
class CollaborationSession:
    """Represents an active collaboration session for real-time features."""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    analysis_id: str = ""
    active_users: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Real-time state
    cursor_positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_selections: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'analysis_id': self.analysis_id,
            'active_users': self.active_users,
            'started_at': self.started_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'cursor_positions': self.cursor_positions,
            'active_selections': self.active_selections
        }