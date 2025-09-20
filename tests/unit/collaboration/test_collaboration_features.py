"""
Unit tests for collaboration features.

Tests the core collaboration functionality including analysis sharing,
annotations, and workspace management.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from core.collaboration.collaboration_manager import CollaborationManager
from core.collaboration.analysis_sharing import AnalysisType, SharePermission, ShareStatus
from core.collaboration.annotations import AnnotationType, AnnotationScope, AnnotationTarget
from core.collaboration.shared_workspaces import WorkspaceType, WorkspaceMemberRole
from core.user_preferences.user_profile import UserProfile, create_default_user_profile


@pytest.fixture
def temp_dir():
    """Create temporary directory for test storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def collaboration_manager(temp_dir):
    """Create collaboration manager with temp storage."""
    return CollaborationManager(storage_path=temp_dir)


@pytest.fixture
def test_user():
    """Create test user profile."""
    return create_default_user_profile(
        user_id="test_user_123",
        username="testuser",
        email="test@example.com"
    )


@pytest.fixture
def second_user():
    """Create second test user profile."""
    return create_default_user_profile(
        user_id="test_user_456",
        username="testuser2",
        email="test2@example.com"
    )


@pytest.fixture
def sample_analysis_data():
    """Create sample analysis data."""
    return {
        "analysis_id": "analysis_123",
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "analysis_date": datetime.now().isoformat(),
        "results": {
            "dcf_value": 150.0,
            "current_price": 175.0,
            "fair_value": 160.0
        },
        "input_parameters": {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025
        },
        "key_metrics": {
            "pe_ratio": 25.5,
            "fcf_yield": 0.035,
            "roe": 0.25
        },
        "assumptions": {
            "revenue_growth": [0.08, 0.06, 0.05, 0.04, 0.03],
            "margin_assumptions": "Conservative estimates"
        },
        "data_sources": ["Excel", "yfinance"],
        "charts": [],
        "scenarios": []
    }


class TestAnalysisSharing:
    """Test analysis sharing functionality."""

    def test_create_shared_analysis(self, collaboration_manager, test_user, sample_analysis_data):
        """Test creating a shared analysis."""
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Apple Inc. Analysis",
            description="Comprehensive DCF analysis of Apple",
            analysis_type=AnalysisType.DCF,
            is_public=False,
            expires_in_days=30
        )

        assert shared_analysis is not None
        assert shared_analysis.title == "Apple Inc. Analysis"
        assert shared_analysis.original_user_id == test_user.user_id
        assert shared_analysis.snapshot.company_ticker == "AAPL"
        assert shared_analysis.snapshot.analysis_type == AnalysisType.DCF
        assert not shared_analysis.is_public
        assert shared_analysis.expires_at is not None

    def test_access_shared_analysis(self, collaboration_manager, test_user, sample_analysis_data):
        """Test accessing a shared analysis."""
        # Create share
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description",
            is_public=True
        )

        # Access share
        context = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=test_user
        )

        assert context is not None
        assert context["shared_analysis"].share_id == shared_analysis.share_id
        assert context["is_owner"] is True
        assert context["can_comment"] is True

    def test_share_permissions(self, collaboration_manager, test_user, second_user, sample_analysis_data):
        """Test share permission management."""
        # Create share
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description",
            is_public=False
        )

        # Add collaborator
        success = collaboration_manager.update_share_permissions(
            share_id=shared_analysis.share_id,
            target_user_id=second_user.user_id,
            target_username=second_user.username,
            target_email=second_user.email,
            permission=SharePermission.EDIT,
            granting_user=test_user
        )

        assert success is True

        # Verify second user can access
        context = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=second_user
        )

        assert context is not None
        assert context["user_permission"] == SharePermission.EDIT

    def test_password_protected_share(self, collaboration_manager, test_user, sample_analysis_data):
        """Test password-protected shares."""
        password = "test_password_123"

        # Create password-protected share
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Protected Analysis",
            description="Password protected analysis",
            is_public=True,
            password=password
        )

        assert shared_analysis.requires_password is True

        # Test access with correct password
        context = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            password=password
        )
        assert context is not None

        # Test access with wrong password
        context = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            password="wrong_password"
        )
        assert context is None


class TestAnnotations:
    """Test annotation system."""

    def test_create_annotation(self, collaboration_manager, test_user, sample_analysis_data):
        """Test creating an annotation."""
        # Create share first
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description"
        )

        # Create annotation
        annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.COMMENT,
            title="Test Comment",
            content="This is a test comment on the analysis",
            target_scope=AnnotationScope.GENERAL
        )

        assert annotation is not None
        assert annotation.title == "Test Comment"
        assert annotation.user_id == test_user.user_id
        assert annotation.annotation_type == AnnotationType.COMMENT

    def test_reply_to_annotation(self, collaboration_manager, test_user, second_user, sample_analysis_data):
        """Test replying to annotations."""
        # Create share and annotation
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description"
        )

        annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.COMMENT,
            title="Test Comment",
            content="Original comment",
            target_scope=AnnotationScope.GENERAL
        )

        # Add reply
        success = collaboration_manager.reply_to_annotation(
            annotation_id=annotation.annotation_id,
            user_profile=second_user,
            content="This is a reply to the comment"
        )

        assert success is True

        # Verify reply was added
        updated_annotation = collaboration_manager.annotation_manager.get_annotation(
            annotation.annotation_id
        )
        assert len(updated_annotation.replies) == 1
        assert updated_annotation.replies[0].content == "This is a reply to the comment"

    def test_resolve_annotation(self, collaboration_manager, test_user, sample_analysis_data):
        """Test resolving annotations."""
        # Create share and annotation
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description"
        )

        annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.QUESTION,
            title="Test Question",
            content="This is a question",
            target_scope=AnnotationScope.GENERAL
        )

        # Resolve annotation
        success = collaboration_manager.resolve_annotation(
            annotation_id=annotation.annotation_id,
            user_profile=test_user
        )

        assert success is True

        # Verify annotation is resolved
        updated_annotation = collaboration_manager.annotation_manager.get_annotation(
            annotation.annotation_id
        )
        assert updated_annotation.is_resolved is True
        assert updated_annotation.resolved_by == test_user.user_id

    def test_annotation_search(self, collaboration_manager, test_user, sample_analysis_data):
        """Test searching annotations."""
        # Create share and multiple annotations
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Test Analysis",
            description="Test description"
        )

        # Create annotations with different content
        collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.COMMENT,
            title="Apple Revenue Analysis",
            content="Discussion about Apple's revenue trends",
            target_scope=AnnotationScope.GENERAL
        )

        collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.NOTE,
            title="DCF Model Notes",
            content="Notes about the DCF valuation model assumptions",
            target_scope=AnnotationScope.ASSUMPTION
        )

        # Search annotations
        results = collaboration_manager.search_annotations(
            query="revenue",
            user_profile=test_user
        )

        assert len(results) == 1
        assert "revenue" in results[0].title.lower() or "revenue" in results[0].content.lower()


class TestWorkspaces:
    """Test workspace functionality."""

    def test_create_workspace(self, collaboration_manager, test_user):
        """Test creating a workspace."""
        workspace = collaboration_manager.create_workspace(
            name="Test Workspace",
            description="A test workspace for collaboration",
            workspace_type=WorkspaceType.PROJECT,
            user_profile=test_user
        )

        assert workspace is not None
        assert workspace.name == "Test Workspace"
        assert workspace.owner_id == test_user.user_id
        assert workspace.workspace_type == WorkspaceType.PROJECT

    def test_join_workspace(self, collaboration_manager, test_user, second_user):
        """Test joining a workspace."""
        # Create public workspace
        workspace = collaboration_manager.create_workspace(
            name="Public Workspace",
            description="Public test workspace",
            workspace_type=WorkspaceType.PUBLIC,
            user_profile=test_user,
            is_public=True
        )

        # Make it not require approval
        workspace.requires_approval = False
        collaboration_manager.workspace_manager._save_workspace(workspace)

        # Second user joins
        success = collaboration_manager.join_workspace(
            workspace_id=workspace.workspace_id,
            user_profile=second_user
        )

        assert success is True

        # Verify membership
        updated_workspace = collaboration_manager.workspace_manager.get_workspace(
            workspace.workspace_id
        )
        member = updated_workspace.get_member(second_user.user_id)
        assert member is not None
        assert member.role == updated_workspace.default_member_role

    def test_workspace_analysis_management(self, collaboration_manager, test_user, sample_analysis_data):
        """Test adding and managing analyses in workspaces."""
        # Create workspace
        workspace = collaboration_manager.create_workspace(
            name="Analysis Workspace",
            description="Workspace for analysis management",
            workspace_type=WorkspaceType.TEAM,
            user_profile=test_user
        )

        # Create shared analysis
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Workspace Analysis",
            description="Analysis for workspace testing"
        )

        # Add analysis to workspace
        success = collaboration_manager.add_analysis_to_workspace(
            workspace_id=workspace.workspace_id,
            analysis_id=shared_analysis.analysis_id,
            user_profile=test_user
        )

        assert success is True

        # Verify analysis was added
        updated_workspace = collaboration_manager.workspace_manager.get_workspace(
            workspace.workspace_id
        )
        assert shared_analysis.analysis_id in updated_workspace.shared_analyses

    def test_workspace_export_import(self, collaboration_manager, test_user, sample_analysis_data):
        """Test workspace export and import functionality."""
        # Create workspace with content
        workspace = collaboration_manager.create_workspace(
            name="Export Test Workspace",
            description="Workspace for export testing",
            workspace_type=WorkspaceType.PROJECT,
            user_profile=test_user
        )

        # Add analysis
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Export Test Analysis",
            description="Analysis for export testing"
        )

        collaboration_manager.add_analysis_to_workspace(
            workspace_id=workspace.workspace_id,
            analysis_id=shared_analysis.analysis_id,
            user_profile=test_user
        )

        # Export workspace
        export_data = collaboration_manager.export_workspace(
            workspace_id=workspace.workspace_id,
            user_profile=test_user,
            include_analyses=True
        )

        assert export_data is not None
        assert "workspace_info" in export_data
        assert export_data["workspace_info"]["name"] == "Export Test Workspace"

        # Import to new workspace
        imported_workspace = collaboration_manager.import_workspace(
            import_data=export_data,
            user_profile=test_user,
            new_workspace_name="Imported Workspace"
        )

        assert imported_workspace is not None
        assert "Imported" in imported_workspace.name
        assert imported_workspace.owner_id == test_user.user_id


class TestCollaborationStatistics:
    """Test collaboration statistics and reporting."""

    def test_user_activity_tracking(self, collaboration_manager, test_user, sample_analysis_data):
        """Test user activity tracking."""
        # Create some activity
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Activity Test Analysis",
            description="Testing user activity tracking"
        )

        annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.COMMENT,
            title="Activity Comment",
            content="Testing activity tracking",
            target_scope=AnnotationScope.GENERAL
        )

        # Get user activity
        activity = collaboration_manager.get_user_activity(test_user, days=7)

        assert activity["user_id"] == test_user.user_id
        assert activity["shares_created"] >= 1
        assert activity["annotations_created"] >= 1
        assert len(activity["recent_shares"]) >= 1
        assert len(activity["recent_annotations"]) >= 1

    def test_collaboration_statistics(self, collaboration_manager, test_user, sample_analysis_data):
        """Test overall collaboration statistics."""
        # Create some content
        collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Stats Test Analysis",
            description="Testing statistics",
            is_public=True
        )

        workspace = collaboration_manager.create_workspace(
            name="Stats Test Workspace",
            description="Testing statistics",
            workspace_type=WorkspaceType.PUBLIC,
            user_profile=test_user,
            is_public=True
        )

        # Get statistics
        stats = collaboration_manager.get_collaboration_statistics()

        assert "sharing" in stats
        assert "annotations" in stats
        assert "recent_activity" in stats
        assert stats["sharing"]["total_shares"] >= 1
        assert stats["sharing"]["public_shares"] >= 1

    def test_analysis_collaboration_summary(self, collaboration_manager, test_user, sample_analysis_data):
        """Test analysis collaboration summary."""
        # Create shared analysis with annotations
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Summary Test Analysis",
            description="Testing collaboration summary",
            is_public=True
        )

        collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user,
            annotation_type=AnnotationType.COMMENT,
            title="Summary Comment",
            content="Testing summary",
            target_scope=AnnotationScope.GENERAL
        )

        # Get summary
        summary = collaboration_manager.get_analysis_collaboration_summary(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=test_user
        )

        assert summary["analysis_id"] == shared_analysis.snapshot.analysis_id
        assert summary["is_shared"] is True
        assert summary["has_public_share"] is True
        assert summary["annotation_count"] >= 1


class TestCollaborationCleanup:
    """Test collaboration cleanup functionality."""

    def test_expired_share_cleanup(self, collaboration_manager, test_user, sample_analysis_data):
        """Test cleanup of expired shares."""
        # Create expired share
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Expired Analysis",
            description="This analysis should expire",
            expires_in_days=-1  # Already expired
        )

        # Manually set expired date to test cleanup
        shared_analysis.expires_at = datetime.now() - timedelta(days=1)
        collaboration_manager.share_manager._save_shared_analysis(shared_analysis)

        # Run cleanup
        cleanup_results = collaboration_manager.cleanup_expired_content()

        assert "expired_shares_cleaned" in cleanup_results
        # Note: The expired share should be cleaned up if the cleanup logic is working

    def test_old_event_cleanup(self, collaboration_manager, test_user, sample_analysis_data):
        """Test cleanup of old events."""
        # Create some activity to generate events
        collaboration_manager.create_analysis_share(
            analysis_data=sample_analysis_data,
            user_profile=test_user,
            title="Event Test Analysis",
            description="Testing event cleanup"
        )

        # Check that events were created
        initial_event_count = len(collaboration_manager._recent_events)
        assert initial_event_count > 0

        # Run cleanup (this should clean events older than 30 days)
        cleanup_results = collaboration_manager.cleanup_expired_content()

        assert "old_events_cleaned" in cleanup_results