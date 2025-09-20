"""
Collaboration Manager

Central coordination for all collaborative features including sharing,
annotations, and real-time collaboration.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .analysis_sharing import AnalysisShareManager, SharedAnalysis, AnalysisType, SharePermission
from .annotations import AnnotationManager, AnalysisAnnotation, AnnotationType, AnnotationScope, AnnotationTarget
from .shared_workspaces import WorkspaceManager, SharedWorkspace, WorkspaceType, WorkspaceMemberRole
from ..user_preferences.user_profile import UserProfile

logger = logging.getLogger(__name__)


@dataclass
class CollaborationEvent:
    """Event in collaborative session"""
    event_id: str
    user_id: str
    username: str
    event_type: str  # share_created, annotation_added, reply_added, etc.
    target_id: str  # ID of the target (share_id, annotation_id, etc.)
    timestamp: datetime
    metadata: Dict[str, Any]


class CollaborationManager:
    """Central manager for all collaboration features"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize collaboration manager"""
        self.storage_path = storage_path or Path("data/collaboration")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize sub-managers
        self.share_manager = AnalysisShareManager(self.storage_path / "shares")
        self.annotation_manager = AnnotationManager(self.storage_path / "annotations")
        self.workspace_manager = WorkspaceManager(self.storage_path / "workspaces")

        # Event tracking
        self._recent_events: List[CollaborationEvent] = []
        self._max_recent_events = 1000

    # === Sharing Operations ===

    def create_analysis_share(self,
                            analysis_data: Dict[str, Any],
                            user_profile: UserProfile,
                            title: str,
                            description: str = "",
                            analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
                            is_public: bool = False,
                            expires_in_days: Optional[int] = None,
                            password: Optional[str] = None,
                            allow_comments: bool = True,
                            allow_downloads: bool = True) -> SharedAnalysis:
        """Create a comprehensive analysis share"""

        # Create the share using the share manager
        shared_analysis = self.share_manager.create_share(
            analysis_data=analysis_data,
            user_id=user_profile.user_id,
            title=title,
            description=description,
            analysis_type=analysis_type,
            is_public=is_public,
            expires_in_days=expires_in_days,
            password=password
        )

        # Set collaboration preferences
        shared_analysis.allow_comments = allow_comments
        shared_analysis.allow_downloads = allow_downloads

        # Save the updated share
        self.share_manager._save_shared_analysis(shared_analysis)

        # Log event
        self._log_event(
            user_id=user_profile.user_id,
            username=user_profile.username,
            event_type="share_created",
            target_id=shared_analysis.share_id,
            metadata={
                "title": title,
                "analysis_type": analysis_type.value,
                "is_public": is_public
            }
        )

        logger.info(f"Created collaborative analysis share {shared_analysis.share_id}")
        return shared_analysis

    def access_shared_analysis(self,
                             share_id: str,
                             user_profile: Optional[UserProfile] = None,
                             password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Access a shared analysis with full collaboration context"""

        user_id = user_profile.user_id if user_profile else None

        # Access the share
        shared_analysis = self.share_manager.access_share(
            share_id=share_id,
            user_id=user_id,
            password=password
        )

        if not shared_analysis:
            return None

        # Get annotations for this analysis
        annotations = self.annotation_manager.get_analysis_annotations(
            analysis_id=shared_analysis.analysis_id,
            user_id=user_id
        )

        # Build comprehensive response
        collaboration_context = {
            "shared_analysis": shared_analysis,
            "annotations": annotations,
            "user_permission": shared_analysis.get_user_permission(user_id) if user_id else None,
            "can_comment": shared_analysis.allow_comments and user_id is not None,
            "can_download": shared_analysis.allow_downloads,
            "is_owner": shared_analysis.original_user_id == user_id if user_id else False
        }

        # Log access event
        if user_profile:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="share_accessed",
                target_id=share_id,
                metadata={"access_time": datetime.now().isoformat()}
            )

        return collaboration_context

    def update_share_permissions(self,
                               share_id: str,
                               target_user_id: str,
                               target_username: str,
                               target_email: Optional[str],
                               permission: SharePermission,
                               granting_user: UserProfile) -> bool:
        """Update user permissions for a shared analysis"""

        success = self.share_manager.update_share_permissions(
            share_id=share_id,
            user_id=target_user_id,
            username=target_username,
            email=target_email,
            permission=permission,
            granted_by=granting_user.user_id
        )

        if success:
            self._log_event(
                user_id=granting_user.user_id,
                username=granting_user.username,
                event_type="permission_updated",
                target_id=share_id,
                metadata={
                    "target_user": target_user_id,
                    "permission": permission.value
                }
            )

        return success

    # === Annotation Operations ===

    def add_annotation(self,
                      analysis_id: str,
                      user_profile: UserProfile,
                      annotation_type: AnnotationType,
                      title: str,
                      content: str,
                      target_scope: AnnotationScope,
                      target_id: Optional[str] = None,
                      coordinates: Optional[Dict[str, float]] = None,
                      share_id: Optional[str] = None,
                      is_private: bool = False,
                      tags: Optional[List[str]] = None) -> AnalysisAnnotation:
        """Add an annotation to an analysis"""

        # Create annotation target
        target = AnnotationTarget(
            scope=target_scope,
            target_id=target_id,
            coordinates=coordinates
        )

        # Create the annotation
        annotation = self.annotation_manager.create_annotation(
            analysis_id=analysis_id,
            user_id=user_profile.user_id,
            username=user_profile.username,
            annotation_type=annotation_type,
            title=title,
            content=content,
            target=target,
            share_id=share_id,
            is_private=is_private,
            tags=tags
        )

        # Log event
        self._log_event(
            user_id=user_profile.user_id,
            username=user_profile.username,
            event_type="annotation_added",
            target_id=annotation.annotation_id,
            metadata={
                "analysis_id": analysis_id,
                "annotation_type": annotation_type.value,
                "target_scope": target_scope.value
            }
        )

        return annotation

    def reply_to_annotation(self,
                          annotation_id: str,
                          user_profile: UserProfile,
                          content: str) -> bool:
        """Add a reply to an annotation"""

        reply = self.annotation_manager.add_reply(
            annotation_id=annotation_id,
            user_id=user_profile.user_id,
            username=user_profile.username,
            content=content
        )

        if reply:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="reply_added",
                target_id=annotation_id,
                metadata={"reply_id": reply.reply_id}
            )
            return True

        return False

    def resolve_annotation(self,
                         annotation_id: str,
                         user_profile: UserProfile) -> bool:
        """Resolve an annotation"""

        success = self.annotation_manager.resolve_annotation(
            annotation_id=annotation_id,
            user_id=user_profile.user_id
        )

        if success:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="annotation_resolved",
                target_id=annotation_id,
                metadata={}
            )

        return success

    # === Workspace Operations ===

    def create_workspace(self,
                        name: str,
                        description: str,
                        workspace_type: WorkspaceType,
                        user_profile: UserProfile,
                        is_public: bool = False) -> SharedWorkspace:
        """Create a new collaborative workspace"""

        workspace = self.workspace_manager.create_workspace(
            name=name,
            description=description,
            workspace_type=workspace_type,
            owner_id=user_profile.user_id,
            owner_username=user_profile.username,
            owner_email=user_profile.email,
            is_public=is_public
        )

        # Log event
        self._log_event(
            user_id=user_profile.user_id,
            username=user_profile.username,
            event_type="workspace_created",
            target_id=workspace.workspace_id,
            metadata={
                "name": name,
                "workspace_type": workspace_type.value,
                "is_public": is_public
            }
        )

        return workspace

    def join_workspace(self,
                      workspace_id: str,
                      user_profile: UserProfile) -> bool:
        """Join a collaborative workspace"""

        success = self.workspace_manager.join_workspace(
            workspace_id=workspace_id,
            user_id=user_profile.user_id,
            username=user_profile.username,
            email=user_profile.email
        )

        if success:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="workspace_joined",
                target_id=workspace_id,
                metadata={}
            )

        return success

    def add_analysis_to_workspace(self,
                                 workspace_id: str,
                                 analysis_id: str,
                                 user_profile: UserProfile) -> bool:
        """Add analysis to workspace"""

        workspace = self.workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return False

        success = workspace.add_analysis(analysis_id, user_profile.user_id)

        if success:
            self.workspace_manager._save_workspace(workspace)
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="analysis_added_to_workspace",
                target_id=workspace_id,
                metadata={"analysis_id": analysis_id}
            )

        return success

    def export_workspace(self,
                        workspace_id: str,
                        user_profile: UserProfile,
                        include_analyses: bool = True) -> Optional[Dict[str, Any]]:
        """Export workspace data for sharing"""

        export_data = self.workspace_manager.export_workspace_data(
            workspace_id=workspace_id,
            user_id=user_profile.user_id,
            include_analyses=include_analyses
        )

        if export_data:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="workspace_exported",
                target_id=workspace_id,
                metadata={"include_analyses": include_analyses}
            )

        return export_data

    def import_workspace(self,
                        import_data: Dict[str, Any],
                        user_profile: UserProfile,
                        new_workspace_name: Optional[str] = None) -> Optional[SharedWorkspace]:
        """Import workspace data to create new workspace"""

        workspace = self.workspace_manager.import_workspace_data(
            import_data=import_data,
            user_id=user_profile.user_id,
            new_workspace_name=new_workspace_name
        )

        if workspace:
            self._log_event(
                user_id=user_profile.user_id,
                username=user_profile.username,
                event_type="workspace_imported",
                target_id=workspace.workspace_id,
                metadata={"source": "import_data"}
            )

        return workspace

    # === Discovery and Search ===

    def discover_public_analyses(self,
                               analysis_type: Optional[AnalysisType] = None,
                               limit: int = 20) -> List[SharedAnalysis]:
        """Discover public shared analyses"""

        public_shares = self.share_manager.get_public_shares(limit=limit)

        if analysis_type:
            public_shares = [
                share for share in public_shares
                if share.snapshot.analysis_type == analysis_type
            ]

        return public_shares

    def search_shared_analyses(self,
                             query: str,
                             user_profile: Optional[UserProfile] = None,
                             analysis_type: Optional[AnalysisType] = None) -> List[SharedAnalysis]:
        """Search shared analyses by content"""

        # Get user's accessible shares
        if user_profile:
            user_shares = self.share_manager.get_user_shares(user_profile.user_id)
        else:
            user_shares = self.share_manager.get_public_shares()

        # Filter by analysis type if specified
        if analysis_type:
            user_shares = [
                share for share in user_shares
                if share.snapshot.analysis_type == analysis_type
            ]

        # Simple text search in title and description
        query_lower = query.lower()
        matching_shares = []

        for share in user_shares:
            if (query_lower in share.title.lower() or
                query_lower in share.description.lower() or
                query_lower in share.snapshot.company_name.lower() or
                query_lower in share.snapshot.company_ticker.lower()):
                matching_shares.append(share)

        return matching_shares

    def search_annotations(self,
                         query: str,
                         analysis_ids: Optional[List[str]] = None,
                         user_profile: Optional[UserProfile] = None) -> List[AnalysisAnnotation]:
        """Search annotations across analyses"""

        user_id = user_profile.user_id if user_profile else None

        return self.annotation_manager.search_annotations(
            query=query,
            analysis_ids=analysis_ids,
            user_id=user_id
        )

    # === Activity and Statistics ===

    def get_user_activity(self,
                         user_profile: UserProfile,
                         days: int = 30) -> Dict[str, Any]:
        """Get user's collaboration activity"""

        user_id = user_profile.user_id
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get user's shares
        user_shares = self.share_manager.get_user_shares(user_id, include_public=False)
        recent_shares = [
            share for share in user_shares
            if share.created_at >= cutoff_date
        ]

        # Get user's annotations
        user_annotations = self.annotation_manager.get_user_annotations(user_id)
        recent_annotations = [
            annotation for annotation in user_annotations
            if annotation.created_at >= cutoff_date
        ]

        # Get recent events for this user
        recent_events = [
            event for event in self._recent_events
            if event.user_id == user_id and event.timestamp >= cutoff_date
        ]

        return {
            "user_id": user_id,
            "period_days": days,
            "shares_created": len(recent_shares),
            "annotations_created": len(recent_annotations),
            "total_events": len(recent_events),
            "recent_shares": recent_shares[:5],  # Most recent 5
            "recent_annotations": recent_annotations[:5],  # Most recent 5
            "recent_events": recent_events[-10:]  # Last 10 events
        }

    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """Get overall collaboration statistics"""

        share_stats = self.share_manager.get_share_statistics()
        annotation_stats = self.annotation_manager.get_annotation_statistics()

        # Combine statistics
        return {
            "sharing": share_stats,
            "annotations": annotation_stats,
            "recent_activity": {
                "total_events": len(self._recent_events),
                "recent_events": self._recent_events[-20:]  # Last 20 events
            }
        }

    def get_analysis_collaboration_summary(self, analysis_id: str,
                                         user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """Get collaboration summary for a specific analysis"""

        user_id = user_profile.user_id if user_profile else None

        # Find shares for this analysis
        analysis_shares = []
        for share in self.share_manager._shared_analyses.values():
            if share.snapshot.analysis_id == analysis_id or share.analysis_id == analysis_id:
                if not user_id or share.can_access(user_id):
                    analysis_shares.append(share)

        # Get annotations
        annotations = self.annotation_manager.get_analysis_annotations(
            analysis_id=analysis_id,
            user_id=user_id
        )

        # Get annotation statistics
        annotation_stats = self.annotation_manager.get_annotation_statistics(analysis_id)

        return {
            "analysis_id": analysis_id,
            "shares": analysis_shares,
            "annotation_count": len(annotations),
            "annotation_stats": annotation_stats,
            "is_shared": len(analysis_shares) > 0,
            "has_public_share": any(share.is_public for share in analysis_shares)
        }

    # === Cleanup and Maintenance ===

    def cleanup_expired_content(self) -> Dict[str, int]:
        """Clean up expired shares and old events"""

        # Clean up expired shares
        expired_shares = self.share_manager.cleanup_expired_shares()

        # Clean up old events (keep last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        original_count = len(self._recent_events)

        self._recent_events = [
            event for event in self._recent_events
            if event.timestamp >= cutoff_date
        ]

        cleaned_events = original_count - len(self._recent_events)

        return {
            "expired_shares_cleaned": expired_shares,
            "old_events_cleaned": cleaned_events
        }

    # === Private Methods ===

    def _log_event(self,
                  user_id: str,
                  username: str,
                  event_type: str,
                  target_id: str,
                  metadata: Dict[str, Any]):
        """Log a collaboration event"""

        event = CollaborationEvent(
            event_id=f"{datetime.now().isoformat()}_{user_id}_{event_type}",
            user_id=user_id,
            username=username,
            event_type=event_type,
            target_id=target_id,
            timestamp=datetime.now(),
            metadata=metadata
        )

        self._recent_events.append(event)

        # Maintain max size
        if len(self._recent_events) > self._max_recent_events:
            self._recent_events = self._recent_events[-self._max_recent_events:]

        logger.debug(f"Logged collaboration event: {event_type} by {username}")

    # === Integration Helpers ===

    def prepare_analysis_for_sharing(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare analysis data for sharing (sanitize, optimize)"""

        # Create a clean copy for sharing
        shareable_data = {
            "analysis_id": analysis_data.get("analysis_id"),
            "ticker": analysis_data.get("ticker"),
            "company_name": analysis_data.get("company_name"),
            "analysis_date": analysis_data.get("analysis_date", datetime.now().isoformat()),
            "results": analysis_data.get("results", {}),
            "parameters": analysis_data.get("input_parameters", {}),
            "key_metrics": analysis_data.get("key_metrics", {}),
            "assumptions": analysis_data.get("assumptions", {}),
            "data_sources": analysis_data.get("data_sources", []),
            "charts": analysis_data.get("charts", []),
            "scenarios": analysis_data.get("scenarios", [])
        }

        # Remove any sensitive or unnecessary data
        # (This could be expanded based on specific requirements)

        return shareable_data

    def enhance_analysis_with_collaboration(self,
                                          analysis_data: Dict[str, Any],
                                          user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """Enhance analysis data with collaboration information"""

        analysis_id = analysis_data.get("analysis_id")
        if not analysis_id:
            return analysis_data

        # Get collaboration summary
        collab_summary = self.get_analysis_collaboration_summary(
            analysis_id=analysis_id,
            user_profile=user_profile
        )

        # Add collaboration context to analysis
        enhanced_data = analysis_data.copy()
        enhanced_data["collaboration"] = collab_summary

        return enhanced_data