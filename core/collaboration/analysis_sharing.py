"""
Analysis Sharing System

Provides functionality for sharing financial analyses between users,
including permission management and version control.
"""

import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import hashlib
import base64

logger = logging.getLogger(__name__)


class SharePermission(Enum):
    """Analysis sharing permission levels"""
    VIEW_ONLY = "view_only"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class AnalysisType(Enum):
    """Types of analyses that can be shared"""
    FCF = "fcf"
    DCF = "dcf"
    DDM = "ddm"
    PB = "pb"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


class ShareStatus(Enum):
    """Status of shared analysis"""
    DRAFT = "draft"
    SHARED = "shared"
    ACTIVE = "active"  # Keep for backward compatibility
    EXPIRED = "expired"
    REVOKED = "revoked"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class AnalysisSnapshot:
    """Snapshot of analysis data at time of sharing"""

    # Analysis metadata
    analysis_type: AnalysisType
    company_ticker: str
    company_name: str
    analysis_date: datetime

    # Analysis results
    results_data: Dict[str, Any]
    input_parameters: Dict[str, Any]
    data_sources: List[str]

    # Calculations and metrics
    key_metrics: Dict[str, float]
    assumptions: Dict[str, Any]
    scenarios: Optional[List[Dict[str, Any]]] = None

    # Charts and visualizations (stored as base64 or references)
    charts: List[Dict[str, Any]] = field(default_factory=list)

    # Data integrity
    checksum: Optional[str] = None
    version: str = "1.0"

    def __post_init__(self):
        """Calculate checksum for data integrity"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate MD5 checksum of analysis data"""
        data_str = json.dumps({
            'results_data': self.results_data,
            'input_parameters': self.input_parameters,
            'key_metrics': self.key_metrics,
            'assumptions': self.assumptions
        }, sort_keys=True, default=str)

        return hashlib.md5(data_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify data integrity using checksum"""
        return self.checksum == self._calculate_checksum()


@dataclass
class SharedUser:
    """User with access to shared analysis"""

    user_id: str
    username: str
    email: Optional[str]
    permission: SharePermission
    granted_at: datetime
    granted_by: str
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    def update_access(self):
        """Update access tracking"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class SharedAnalysis:
    """Main shared analysis container"""

    # Unique identifiers
    share_id: str
    analysis_id: str
    original_user_id: str

    # Analysis data
    snapshot: AnalysisSnapshot

    # Sharing configuration
    title: str
    description: str = ""
    is_public: bool = False
    requires_password: bool = False
    password_hash: Optional[str] = None

    # Access control
    shared_users: List[SharedUser] = field(default_factory=list)
    max_users: Optional[int] = None

    # Expiration settings
    expires_at: Optional[datetime] = None
    auto_archive_after_days: int = 30

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ShareStatus = ShareStatus.ACTIVE
    access_count: int = 0

    # Collaboration features
    allow_comments: bool = True
    allow_downloads: bool = True
    track_access: bool = True

    def __post_init__(self):
        """Initialize share ID if not provided"""
        if not self.share_id:
            self.share_id = str(uuid.uuid4())

    def add_user(self, user_id: str, username: str, email: Optional[str],
                 permission: SharePermission, granted_by: str) -> bool:
        """Add user to shared analysis"""
        if self.max_users and len(self.shared_users) >= self.max_users:
            return False

        # Check if user already exists
        for user in self.shared_users:
            if user.user_id == user_id:
                # Update existing user permission
                user.permission = permission
                user.granted_by = granted_by
                user.granted_at = datetime.now()
                self.updated_at = datetime.now()
                return True

        # Add new user
        shared_user = SharedUser(
            user_id=user_id,
            username=username,
            email=email,
            permission=permission,
            granted_at=datetime.now(),
            granted_by=granted_by
        )

        self.shared_users.append(shared_user)
        self.updated_at = datetime.now()
        return True

    def remove_user(self, user_id: str) -> bool:
        """Remove user from shared analysis"""
        for i, user in enumerate(self.shared_users):
            if user.user_id == user_id:
                del self.shared_users[i]
                self.updated_at = datetime.now()
                return True
        return False

    def get_user_permission(self, user_id: str) -> Optional[SharePermission]:
        """Get user's permission level"""
        for user in self.shared_users:
            if user.user_id == user_id:
                return user.permission
        return None

    def can_access(self, user_id: Optional[str] = None) -> bool:
        """Check if user can access the analysis"""
        if self.status != ShareStatus.ACTIVE:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        if self.is_public:
            return True

        if user_id:
            return self.get_user_permission(user_id) is not None

        return False

    def record_access(self, user_id: Optional[str] = None):
        """Record access to the shared analysis"""
        if self.track_access:
            self.access_count += 1

            if user_id:
                for user in self.shared_users:
                    if user.user_id == user_id:
                        user.update_access()
                        break

    def is_expired(self) -> bool:
        """Check if the share has expired"""
        if self.expires_at and datetime.now() > self.expires_at:
            return True

        if self.auto_archive_after_days > 0:
            archive_date = self.created_at + timedelta(days=self.auto_archive_after_days)
            if datetime.now() > archive_date:
                return True

        return False

    def set_password(self, password: str):
        """Set password for protected sharing"""
        self.requires_password = True
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verify password for protected sharing"""
        if not self.requires_password:
            return True

        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedAnalysis':
        """Create SharedAnalysis from dictionary"""
        # Handle datetime fields
        for field_name in ['created_at', 'updated_at', 'expires_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except:
                    data[field_name] = None

        # Handle enum fields
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ShareStatus(data['status'])

        # Handle snapshot
        if 'snapshot' in data and isinstance(data['snapshot'], dict):
            snapshot_data = data['snapshot']

            # Handle snapshot datetime fields
            if 'analysis_date' in snapshot_data and isinstance(snapshot_data['analysis_date'], str):
                snapshot_data['analysis_date'] = datetime.fromisoformat(snapshot_data['analysis_date'])

            # Handle snapshot enum
            if 'analysis_type' in snapshot_data and isinstance(snapshot_data['analysis_type'], str):
                snapshot_data['analysis_type'] = AnalysisType(snapshot_data['analysis_type'])

            data['snapshot'] = AnalysisSnapshot(**snapshot_data)

        # Handle shared users
        if 'shared_users' in data and isinstance(data['shared_users'], list):
            shared_users = []
            for user_data in data['shared_users']:
                # Handle user datetime fields
                for field_name in ['granted_at', 'last_accessed']:
                    if field_name in user_data and isinstance(user_data[field_name], str):
                        try:
                            user_data[field_name] = datetime.fromisoformat(user_data[field_name])
                        except:
                            user_data[field_name] = None

                # Handle permission enum
                if 'permission' in user_data and isinstance(user_data['permission'], str):
                    user_data['permission'] = SharePermission(user_data['permission'])

                shared_users.append(SharedUser(**user_data))

            data['shared_users'] = shared_users

        return cls(**data)


class AnalysisShareManager:
    """Manager for analysis sharing operations"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize share manager"""
        self.storage_path = storage_path or Path("data/shared_analyses")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._shared_analyses: Dict[str, SharedAnalysis] = {}
        self._load_shared_analyses()

    def _load_shared_analyses(self):
        """Load shared analyses from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    shared_analysis = SharedAnalysis.from_dict(data)
                    self._shared_analyses[shared_analysis.share_id] = shared_analysis
        except Exception as e:
            logger.error(f"Failed to load shared analyses: {e}")

    def _save_shared_analysis(self, shared_analysis: SharedAnalysis):
        """Save shared analysis to storage"""
        try:
            file_path = self.storage_path / f"{shared_analysis.share_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(shared_analysis.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save shared analysis {shared_analysis.share_id}: {e}")

    def create_share(self,
                    analysis_data: Dict[str, Any],
                    user_id: str,
                    title: str,
                    description: str = "",
                    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
                    is_public: bool = False,
                    expires_in_days: Optional[int] = None,
                    password: Optional[str] = None) -> SharedAnalysis:
        """Create a new shared analysis"""

        # Create analysis snapshot
        snapshot = AnalysisSnapshot(
            analysis_type=analysis_type,
            company_ticker=analysis_data.get('ticker', 'UNKNOWN'),
            company_name=analysis_data.get('company_name', 'Unknown Company'),
            analysis_date=datetime.now(),
            results_data=analysis_data.get('results', {}),
            input_parameters=analysis_data.get('parameters', {}),
            data_sources=analysis_data.get('data_sources', []),
            key_metrics=analysis_data.get('key_metrics', {}),
            assumptions=analysis_data.get('assumptions', {}),
            scenarios=analysis_data.get('scenarios', []),
            charts=analysis_data.get('charts', [])
        )

        # Set expiration date
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Create shared analysis
        shared_analysis = SharedAnalysis(
            share_id=str(uuid.uuid4()),
            analysis_id=analysis_data.get('analysis_id', str(uuid.uuid4())),
            original_user_id=user_id,
            snapshot=snapshot,
            title=title,
            description=description,
            is_public=is_public,
            expires_at=expires_at
        )

        # Set password if provided
        if password:
            shared_analysis.set_password(password)

        # Save and return
        self._shared_analyses[shared_analysis.share_id] = shared_analysis
        self._save_shared_analysis(shared_analysis)

        logger.info(f"Created shared analysis {shared_analysis.share_id} for user {user_id}")
        return shared_analysis

    def get_share(self, share_id: str) -> Optional[SharedAnalysis]:
        """Get shared analysis by ID"""
        return self._shared_analyses.get(share_id)

    def access_share(self, share_id: str, user_id: Optional[str] = None,
                    password: Optional[str] = None) -> Optional[SharedAnalysis]:
        """Access a shared analysis with permission checks"""
        shared_analysis = self.get_share(share_id)

        if not shared_analysis:
            return None

        # Check if share is expired
        if shared_analysis.is_expired():
            shared_analysis.status = ShareStatus.EXPIRED
            self._save_shared_analysis(shared_analysis)
            return None

        # Check access permissions
        if not shared_analysis.can_access(user_id):
            return None

        # Check password if required
        if shared_analysis.requires_password and not shared_analysis.verify_password(password or ""):
            return None

        # Record access
        shared_analysis.record_access(user_id)
        self._save_shared_analysis(shared_analysis)

        return shared_analysis

    def update_share_permissions(self, share_id: str, user_id: str, username: str,
                               email: Optional[str], permission: SharePermission,
                               granted_by: str) -> bool:
        """Update user permissions for a shared analysis"""
        shared_analysis = self.get_share(share_id)

        if not shared_analysis:
            return False

        success = shared_analysis.add_user(user_id, username, email, permission, granted_by)

        if success:
            self._save_shared_analysis(shared_analysis)

        return success

    def revoke_access(self, share_id: str, user_id: str) -> bool:
        """Revoke user access to shared analysis"""
        shared_analysis = self.get_share(share_id)

        if not shared_analysis:
            return False

        success = shared_analysis.remove_user(user_id)

        if success:
            self._save_shared_analysis(shared_analysis)

        return success

    def get_user_shares(self, user_id: str, include_public: bool = True) -> List[SharedAnalysis]:
        """Get all shares accessible to a user"""
        user_shares = []

        for shared_analysis in self._shared_analyses.values():
            if shared_analysis.status != ShareStatus.ACTIVE:
                continue

            # Check if user is owner
            if shared_analysis.original_user_id == user_id:
                user_shares.append(shared_analysis)
                continue

            # Check if user has explicit access
            if shared_analysis.get_user_permission(user_id):
                user_shares.append(shared_analysis)
                continue

            # Check if it's public and we include public shares
            if include_public and shared_analysis.is_public:
                user_shares.append(shared_analysis)

        return user_shares

    def get_public_shares(self, limit: int = 50) -> List[SharedAnalysis]:
        """Get public shared analyses"""
        public_shares = []

        for shared_analysis in self._shared_analyses.values():
            if (shared_analysis.is_public and
                shared_analysis.status == ShareStatus.ACTIVE and
                not shared_analysis.is_expired()):
                public_shares.append(shared_analysis)

                if len(public_shares) >= limit:
                    break

        # Sort by creation date (newest first)
        public_shares.sort(key=lambda x: x.created_at, reverse=True)
        return public_shares

    def delete_share(self, share_id: str, user_id: str) -> bool:
        """Delete a shared analysis (only by owner)"""
        shared_analysis = self.get_share(share_id)

        if not shared_analysis or shared_analysis.original_user_id != user_id:
            return False

        # Remove from memory and storage
        del self._shared_analyses[share_id]

        try:
            file_path = self.storage_path / f"{share_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete share file {share_id}: {e}")

        logger.info(f"Deleted shared analysis {share_id}")
        return True

    def cleanup_expired_shares(self) -> int:
        """Clean up expired shares and return count of cleaned items"""
        cleaned_count = 0
        expired_shares = []

        for share_id, shared_analysis in self._shared_analyses.items():
            if shared_analysis.is_expired():
                expired_shares.append(share_id)

        for share_id in expired_shares:
            if self.delete_share(share_id, self._shared_analyses[share_id].original_user_id):
                cleaned_count += 1

        return cleaned_count

    def get_share_statistics(self) -> Dict[str, Any]:
        """Get sharing statistics"""
        active_shares = sum(1 for s in self._shared_analyses.values()
                          if s.status == ShareStatus.ACTIVE)

        public_shares = sum(1 for s in self._shared_analyses.values()
                          if s.is_public and s.status == ShareStatus.ACTIVE)

        total_access_count = sum(s.access_count for s in self._shared_analyses.values())

        return {
            'total_shares': len(self._shared_analyses),
            'active_shares': active_shares,
            'public_shares': public_shares,
            'total_access_count': total_access_count,
            'analysis_types': self._get_analysis_type_breakdown()
        }

    def _get_analysis_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of shared analyses by type"""
        breakdown = {}

        for shared_analysis in self._shared_analyses.values():
            if shared_analysis.status == ShareStatus.ACTIVE:
                analysis_type = shared_analysis.snapshot.analysis_type.value
                breakdown[analysis_type] = breakdown.get(analysis_type, 0) + 1

        return breakdown