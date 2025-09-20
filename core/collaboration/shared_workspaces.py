"""
Shared Workspaces

Provides workspace functionality for collaborative financial analysis,
including shared project spaces and analysis collections.
"""

import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .analysis_sharing import SharedAnalysis, AnalysisType, SharePermission

logger = logging.getLogger(__name__)


class WorkspaceType(Enum):
    """Types of workspaces"""
    PERSONAL = "personal"
    TEAM = "team"
    PROJECT = "project"
    COMPANY = "company"
    PUBLIC = "public"


class WorkspaceMemberRole(Enum):
    """Member roles in workspace"""
    OWNER = "owner"
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


@dataclass
class WorkspaceMember:
    """Member of a shared workspace"""

    user_id: str
    username: str
    email: Optional[str]
    role: WorkspaceMemberRole
    joined_at: datetime
    invited_by: str
    last_active: Optional[datetime] = None
    permissions: Dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        """Set default permissions based on role"""
        if not self.permissions:
            self.permissions = self._get_default_permissions()

    def _get_default_permissions(self) -> Dict[str, bool]:
        """Get default permissions based on role"""
        if self.role == WorkspaceMemberRole.OWNER:
            return {
                "can_edit_workspace": True,
                "can_invite_members": True,
                "can_remove_members": True,
                "can_share_analyses": True,
                "can_create_analyses": True,
                "can_edit_analyses": True,
                "can_delete_analyses": True,
                "can_export_data": True
            }
        elif self.role == WorkspaceMemberRole.ADMIN:
            return {
                "can_edit_workspace": True,
                "can_invite_members": True,
                "can_remove_members": False,
                "can_share_analyses": True,
                "can_create_analyses": True,
                "can_edit_analyses": True,
                "can_delete_analyses": False,
                "can_export_data": True
            }
        elif self.role == WorkspaceMemberRole.CONTRIBUTOR:
            return {
                "can_edit_workspace": False,
                "can_invite_members": False,
                "can_remove_members": False,
                "can_share_analyses": True,
                "can_create_analyses": True,
                "can_edit_analyses": True,
                "can_delete_analyses": False,
                "can_export_data": True
            }
        else:  # VIEWER
            return {
                "can_edit_workspace": False,
                "can_invite_members": False,
                "can_remove_members": False,
                "can_share_analyses": False,
                "can_create_analyses": False,
                "can_edit_analyses": False,
                "can_delete_analyses": False,
                "can_export_data": True
            }

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_active = datetime.now()

    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission"""
        return self.permissions.get(permission, False)


@dataclass
class AnalysisCollection:
    """Collection of analyses within workspace"""

    collection_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    analysis_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.collection_id:
            self.collection_id = str(uuid.uuid4())

    def add_analysis(self, analysis_id: str):
        """Add analysis to collection"""
        if analysis_id not in self.analysis_ids:
            self.analysis_ids.append(analysis_id)

    def remove_analysis(self, analysis_id: str):
        """Remove analysis from collection"""
        if analysis_id in self.analysis_ids:
            self.analysis_ids.remove(analysis_id)


@dataclass
class SharedWorkspace:
    """Main shared workspace container"""

    # Unique identifiers
    workspace_id: str
    name: str
    description: str
    workspace_type: WorkspaceType

    # Ownership and management
    owner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Members and permissions
    members: List[WorkspaceMember] = field(default_factory=list)
    max_members: Optional[int] = None

    # Content
    shared_analyses: List[str] = field(default_factory=list)  # Analysis IDs
    collections: List[AnalysisCollection] = field(default_factory=list)

    # Settings
    is_public: bool = False
    requires_approval: bool = True
    default_member_role: WorkspaceMemberRole = WorkspaceMemberRole.VIEWER

    # Metadata
    tags: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.workspace_id:
            self.workspace_id = str(uuid.uuid4())

        # Ensure owner is a member
        if not any(member.user_id == self.owner_id for member in self.members):
            self.add_member(
                user_id=self.owner_id,
                username="Owner",
                email=None,
                role=WorkspaceMemberRole.OWNER,
                invited_by=self.owner_id
            )

    def add_member(self, user_id: str, username: str, email: Optional[str],
                   role: WorkspaceMemberRole, invited_by: str) -> bool:
        """Add member to workspace"""
        # Check if user is already a member
        for member in self.members:
            if member.user_id == user_id:
                return False

        # Check member limit
        if self.max_members and len(self.members) >= self.max_members:
            return False

        # Add new member
        member = WorkspaceMember(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            joined_at=datetime.now(),
            invited_by=invited_by
        )

        self.members.append(member)
        self.updated_at = datetime.now()
        return True

    def remove_member(self, user_id: str, removed_by: str) -> bool:
        """Remove member from workspace"""
        # Cannot remove owner
        if user_id == self.owner_id:
            return False

        # Check if remover has permission
        remover = self.get_member(removed_by)
        if not remover or not remover.has_permission("can_remove_members"):
            return False

        # Remove member
        for i, member in enumerate(self.members):
            if member.user_id == user_id:
                del self.members[i]
                self.updated_at = datetime.now()
                return True

        return False

    def get_member(self, user_id: str) -> Optional[WorkspaceMember]:
        """Get member by user ID"""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def update_member_role(self, user_id: str, new_role: WorkspaceMemberRole,
                          updated_by: str) -> bool:
        """Update member role"""
        # Cannot change owner role
        if user_id == self.owner_id:
            return False

        # Check if updater has permission
        updater = self.get_member(updated_by)
        if not updater or not updater.has_permission("can_edit_workspace"):
            return False

        # Update role
        member = self.get_member(user_id)
        if member:
            member.role = new_role
            member.permissions = member._get_default_permissions()
            self.updated_at = datetime.now()
            return True

        return False

    def add_analysis(self, analysis_id: str, added_by: str) -> bool:
        """Add analysis to workspace"""
        member = self.get_member(added_by)
        if not member or not member.has_permission("can_share_analyses"):
            return False

        if analysis_id not in self.shared_analyses:
            self.shared_analyses.append(analysis_id)
            self.updated_at = datetime.now()
            return True

        return False

    def remove_analysis(self, analysis_id: str, removed_by: str) -> bool:
        """Remove analysis from workspace"""
        member = self.get_member(removed_by)
        if not member or not member.has_permission("can_delete_analyses"):
            return False

        if analysis_id in self.shared_analyses:
            self.shared_analyses.remove(analysis_id)
            # Also remove from collections
            for collection in self.collections:
                collection.remove_analysis(analysis_id)
            self.updated_at = datetime.now()
            return True

        return False

    def create_collection(self, name: str, description: str, created_by: str,
                         analysis_ids: Optional[List[str]] = None) -> Optional[AnalysisCollection]:
        """Create new analysis collection"""
        member = self.get_member(created_by)
        if not member or not member.has_permission("can_create_analyses"):
            return None

        collection = AnalysisCollection(
            collection_id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_by=created_by,
            created_at=datetime.now(),
            analysis_ids=analysis_ids or []
        )

        self.collections.append(collection)
        self.updated_at = datetime.now()
        return collection

    def get_collection(self, collection_id: str) -> Optional[AnalysisCollection]:
        """Get collection by ID"""
        for collection in self.collections:
            if collection.collection_id == collection_id:
                return collection
        return None

    def delete_collection(self, collection_id: str, deleted_by: str) -> bool:
        """Delete collection"""
        member = self.get_member(deleted_by)
        if not member or not member.has_permission("can_delete_analyses"):
            return False

        for i, collection in enumerate(self.collections):
            if collection.collection_id == collection_id:
                del self.collections[i]
                self.updated_at = datetime.now()
                return True

        return False

    def can_access(self, user_id: Optional[str] = None) -> bool:
        """Check if user can access workspace"""
        if self.is_public:
            return True

        if user_id:
            return self.get_member(user_id) is not None

        return False

    def get_member_statistics(self) -> Dict[str, Any]:
        """Get member statistics"""
        role_counts = {}
        for member in self.members:
            role = member.role.value
            role_counts[role] = role_counts.get(role, 0) + 1

        active_members = sum(
            1 for member in self.members
            if member.last_active and
            member.last_active >= datetime.now() - timedelta(days=30)
        )

        return {
            "total_members": len(self.members),
            "active_members": active_members,
            "role_distribution": role_counts
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedWorkspace':
        """Create SharedWorkspace from dictionary"""
        # Handle datetime fields
        for field_name in ['created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except:
                    data[field_name] = datetime.now()

        # Handle enum fields
        if 'workspace_type' in data and isinstance(data['workspace_type'], str):
            data['workspace_type'] = WorkspaceType(data['workspace_type'])

        if 'default_member_role' in data and isinstance(data['default_member_role'], str):
            data['default_member_role'] = WorkspaceMemberRole(data['default_member_role'])

        # Handle members
        if 'members' in data and isinstance(data['members'], list):
            members = []
            for member_data in data['members']:
                # Handle member datetime fields
                for field_name in ['joined_at', 'last_active']:
                    if field_name in member_data and isinstance(member_data[field_name], str):
                        try:
                            member_data[field_name] = datetime.fromisoformat(member_data[field_name])
                        except:
                            member_data[field_name] = None

                # Handle member role enum
                if 'role' in member_data and isinstance(member_data['role'], str):
                    member_data['role'] = WorkspaceMemberRole(member_data['role'])

                members.append(WorkspaceMember(**member_data))

            data['members'] = members

        # Handle collections
        if 'collections' in data and isinstance(data['collections'], list):
            collections = []
            for collection_data in data['collections']:
                # Handle collection datetime fields
                if 'created_at' in collection_data and isinstance(collection_data['created_at'], str):
                    try:
                        collection_data['created_at'] = datetime.fromisoformat(collection_data['created_at'])
                    except:
                        collection_data['created_at'] = datetime.now()

                collections.append(AnalysisCollection(**collection_data))

            data['collections'] = collections

        return cls(**data)


class WorkspaceManager:
    """Manager for shared workspaces"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize workspace manager"""
        self.storage_path = storage_path or Path("data/workspaces")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._workspaces: Dict[str, SharedWorkspace] = {}
        self._user_workspaces: Dict[str, List[str]] = {}  # user_id -> workspace_ids
        self._load_workspaces()

    def _load_workspaces(self):
        """Load workspaces from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    workspace = SharedWorkspace.from_dict(data)
                    self._add_workspace_to_memory(workspace)
        except Exception as e:
            logger.error(f"Failed to load workspaces: {e}")

    def _add_workspace_to_memory(self, workspace: SharedWorkspace):
        """Add workspace to in-memory indexes"""
        self._workspaces[workspace.workspace_id] = workspace

        # Update user workspace index
        for member in workspace.members:
            if member.user_id not in self._user_workspaces:
                self._user_workspaces[member.user_id] = []

            if workspace.workspace_id not in self._user_workspaces[member.user_id]:
                self._user_workspaces[member.user_id].append(workspace.workspace_id)

    def _save_workspace(self, workspace: SharedWorkspace):
        """Save workspace to storage"""
        try:
            file_path = self.storage_path / f"{workspace.workspace_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(workspace.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save workspace {workspace.workspace_id}: {e}")

    def create_workspace(self, name: str, description: str, workspace_type: WorkspaceType,
                        owner_id: str, owner_username: str, owner_email: Optional[str] = None,
                        is_public: bool = False) -> SharedWorkspace:
        """Create a new workspace"""
        workspace = SharedWorkspace(
            workspace_id=str(uuid.uuid4()),
            name=name,
            description=description,
            workspace_type=workspace_type,
            owner_id=owner_id,
            is_public=is_public
        )

        # Update owner member info
        if workspace.members:
            workspace.members[0].username = owner_username
            workspace.members[0].email = owner_email

        self._add_workspace_to_memory(workspace)
        self._save_workspace(workspace)

        logger.info(f"Created workspace {workspace.workspace_id} by user {owner_id}")
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[SharedWorkspace]:
        """Get workspace by ID"""
        return self._workspaces.get(workspace_id)

    def get_user_workspaces(self, user_id: str, include_public: bool = True) -> List[SharedWorkspace]:
        """Get workspaces accessible to user"""
        user_workspaces = []

        # Get user's direct workspaces
        workspace_ids = self._user_workspaces.get(user_id, [])
        for workspace_id in workspace_ids:
            workspace = self._workspaces.get(workspace_id)
            if workspace:
                user_workspaces.append(workspace)

        # Add public workspaces if requested
        if include_public:
            for workspace in self._workspaces.values():
                if (workspace.is_public and
                    workspace.workspace_id not in workspace_ids):
                    user_workspaces.append(workspace)

        return user_workspaces

    def get_public_workspaces(self, limit: int = 20) -> List[SharedWorkspace]:
        """Get public workspaces"""
        public_workspaces = []

        for workspace in self._workspaces.values():
            if workspace.is_public:
                public_workspaces.append(workspace)

                if len(public_workspaces) >= limit:
                    break

        # Sort by creation date (newest first)
        public_workspaces.sort(key=lambda x: x.created_at, reverse=True)
        return public_workspaces

    def join_workspace(self, workspace_id: str, user_id: str, username: str,
                      email: Optional[str] = None) -> bool:
        """Join a workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        # Check if workspace allows joining
        if not workspace.is_public and workspace.requires_approval:
            return False

        # Add member
        success = workspace.add_member(
            user_id=user_id,
            username=username,
            email=email,
            role=workspace.default_member_role,
            invited_by="system"
        )

        if success:
            self._update_user_workspace_index(user_id, workspace_id)
            self._save_workspace(workspace)

        return success

    def leave_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Leave a workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        # Cannot leave if owner
        if workspace.owner_id == user_id:
            return False

        # Remove member
        success = workspace.remove_member(user_id, user_id)

        if success:
            self._remove_user_workspace_index(user_id, workspace_id)
            self._save_workspace(workspace)

        return success

    def invite_to_workspace(self, workspace_id: str, inviter_id: str,
                           invitee_id: str, invitee_username: str,
                           invitee_email: Optional[str], role: WorkspaceMemberRole) -> bool:
        """Invite user to workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        # Check if inviter has permission
        inviter = workspace.get_member(inviter_id)
        if not inviter or not inviter.has_permission("can_invite_members"):
            return False

        # Add member
        success = workspace.add_member(
            user_id=invitee_id,
            username=invitee_username,
            email=invitee_email,
            role=role,
            invited_by=inviter_id
        )

        if success:
            self._update_user_workspace_index(invitee_id, workspace_id)
            self._save_workspace(workspace)

        return success

    def delete_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Delete workspace (only by owner)"""
        workspace = self.get_workspace(workspace_id)
        if not workspace or workspace.owner_id != user_id:
            return False

        # Remove from memory
        del self._workspaces[workspace_id]

        # Remove from user indexes
        for member in workspace.members:
            self._remove_user_workspace_index(member.user_id, workspace_id)

        # Remove from storage
        try:
            file_path = self.storage_path / f"{workspace_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete workspace file {workspace_id}: {e}")

        logger.info(f"Deleted workspace {workspace_id}")
        return True

    def export_workspace_data(self, workspace_id: str, user_id: str,
                             include_analyses: bool = True) -> Optional[Dict[str, Any]]:
        """Export workspace data for sharing/backup"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        # Check if user has export permission
        member = workspace.get_member(user_id)
        if not member or not member.has_permission("can_export_data"):
            return None

        export_data = {
            "workspace_info": {
                "name": workspace.name,
                "description": workspace.description,
                "workspace_type": workspace.workspace_type.value,
                "created_at": workspace.created_at.isoformat(),
                "tags": workspace.tags
            },
            "collections": [
                {
                    "name": collection.name,
                    "description": collection.description,
                    "analysis_ids": collection.analysis_ids,
                    "tags": collection.tags
                }
                for collection in workspace.collections
            ],
            "export_metadata": {
                "exported_by": user_id,
                "exported_at": datetime.now().isoformat(),
                "workspace_id": workspace_id
            }
        }

        if include_analyses:
            export_data["shared_analyses"] = workspace.shared_analyses

        return export_data

    def import_workspace_data(self, import_data: Dict[str, Any], user_id: str,
                             new_workspace_name: Optional[str] = None) -> Optional[SharedWorkspace]:
        """Import workspace data to create new workspace"""
        try:
            workspace_info = import_data.get("workspace_info", {})

            # Create new workspace
            workspace = self.create_workspace(
                name=new_workspace_name or f"Imported - {workspace_info.get('name', 'Workspace')}",
                description=workspace_info.get("description", "Imported workspace"),
                workspace_type=WorkspaceType(workspace_info.get("workspace_type", "personal")),
                owner_id=user_id,
                owner_username="User"
            )

            # Import collections
            collections_data = import_data.get("collections", [])
            for collection_data in collections_data:
                workspace.create_collection(
                    name=collection_data.get("name", "Imported Collection"),
                    description=collection_data.get("description", ""),
                    created_by=user_id,
                    analysis_ids=collection_data.get("analysis_ids", [])
                )

            # Import shared analyses
            if "shared_analyses" in import_data:
                workspace.shared_analyses = import_data["shared_analyses"]

            # Import tags
            if "tags" in workspace_info:
                workspace.tags = workspace_info["tags"]

            self._save_workspace(workspace)

            logger.info(f"Imported workspace data to new workspace {workspace.workspace_id}")
            return workspace

        except Exception as e:
            logger.error(f"Failed to import workspace data: {e}")
            return None

    def _update_user_workspace_index(self, user_id: str, workspace_id: str):
        """Update user workspace index"""
        if user_id not in self._user_workspaces:
            self._user_workspaces[user_id] = []

        if workspace_id not in self._user_workspaces[user_id]:
            self._user_workspaces[user_id].append(workspace_id)

    def _remove_user_workspace_index(self, user_id: str, workspace_id: str):
        """Remove from user workspace index"""
        if user_id in self._user_workspaces:
            if workspace_id in self._user_workspaces[user_id]:
                self._user_workspaces[user_id].remove(workspace_id)

    def get_workspace_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics"""
        total_workspaces = len(self._workspaces)
        public_workspaces = sum(1 for w in self._workspaces.values() if w.is_public)
        total_members = sum(len(w.members) for w in self._workspaces.values())

        # Workspace type breakdown
        type_breakdown = {}
        for workspace in self._workspaces.values():
            workspace_type = workspace.workspace_type.value
            type_breakdown[workspace_type] = type_breakdown.get(workspace_type, 0) + 1

        return {
            "total_workspaces": total_workspaces,
            "public_workspaces": public_workspaces,
            "total_members": total_members,
            "type_breakdown": type_breakdown
        }