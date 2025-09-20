"""
Integration tests for collaboration features.

Tests the complete collaboration workflow including integration between
sharing, annotations, workspaces, and the Streamlit UI.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import streamlit as st
from unittest.mock import patch, MagicMock

from core.collaboration.collaboration_manager import CollaborationManager
from core.collaboration.analysis_sharing import AnalysisType, SharePermission
from core.collaboration.annotations import AnnotationType, AnnotationScope
from core.collaboration.shared_workspaces import WorkspaceType
from core.user_preferences.user_profile import create_default_user_profile
from ui.streamlit.collaboration_ui import (
    init_collaboration_session,
    prepare_current_analysis_data,
    render_sharing_interface,
    render_shared_analyses_browser
)


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
def test_users():
    """Create multiple test users."""
    return [
        create_default_user_profile(f"user_{i}", f"testuser{i}", f"test{i}@example.com")
        for i in range(3)
    ]


@pytest.fixture
def sample_financial_data():
    """Create comprehensive sample financial analysis data."""
    return {
        "analysis_id": "integration_test_123",
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "analysis_date": datetime.now().isoformat(),
        "results": {
            "dcf_analysis": {
                "fair_value": 420.50,
                "current_price": 385.00,
                "upside_potential": 0.092,
                "recommendation": "BUY"
            },
            "fcf_analysis": {
                "latest_fcf": 65000000000,
                "fcf_growth_rate": 0.125,
                "fcf_yield": 0.035
            },
            "ratio_analysis": {
                "pe_ratio": 28.5,
                "pb_ratio": 4.2,
                "roe": 0.187,
                "debt_to_equity": 0.35
            }
        },
        "input_parameters": {
            "discount_rate": 0.095,
            "terminal_growth_rate": 0.025,
            "projection_years": 5,
            "tax_rate": 0.21
        },
        "key_metrics": {
            "revenue_cagr_5y": 0.085,
            "net_margin": 0.31,
            "roic": 0.195,
            "beta": 0.9
        },
        "assumptions": {
            "revenue_growth": [0.12, 0.10, 0.08, 0.06, 0.05],
            "operating_margin": [0.42, 0.41, 0.40, 0.39, 0.38],
            "capex_percent_of_revenue": 0.035,
            "working_capital_assumptions": "Conservative growth assumptions"
        },
        "data_sources": ["Excel", "yfinance", "Alpha Vantage"],
        "charts": [
            {"type": "revenue_projection", "data": "base64_chart_data"},
            {"type": "fcf_projection", "data": "base64_chart_data"},
            {"type": "sensitivity_analysis", "data": "base64_chart_data"}
        ],
        "scenarios": [
            {
                "name": "Base Case",
                "revenue_growth": [0.12, 0.10, 0.08, 0.06, 0.05],
                "fair_value": 420.50
            },
            {
                "name": "Bull Case",
                "revenue_growth": [0.18, 0.15, 0.12, 0.10, 0.08],
                "fair_value": 485.75
            },
            {
                "name": "Bear Case",
                "revenue_growth": [0.08, 0.06, 0.05, 0.04, 0.03],
                "fair_value": 365.25
            }
        ]
    }


class TestCollaborationWorkflow:
    """Test complete collaboration workflows."""

    def test_full_analysis_sharing_workflow(self, collaboration_manager, test_users, sample_financial_data):
        """Test the complete analysis sharing workflow."""
        owner, collaborator1, collaborator2 = test_users

        # Step 1: Owner creates and shares analysis
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_financial_data,
            user_profile=owner,
            title="Microsoft Corporation - Q4 2024 Analysis",
            description="Comprehensive DCF and FCF analysis of Microsoft with multiple scenarios",
            analysis_type=AnalysisType.COMPREHENSIVE,
            is_public=False,
            expires_in_days=90,
            allow_comments=True,
            allow_downloads=True
        )

        assert shared_analysis is not None
        assert shared_analysis.title == "Microsoft Corporation - Q4 2024 Analysis"

        # Step 2: Owner adds collaborators with different permissions
        collaboration_manager.update_share_permissions(
            share_id=shared_analysis.share_id,
            target_user_id=collaborator1.user_id,
            target_username=collaborator1.username,
            target_email=collaborator1.email,
            permission=SharePermission.EDIT,
            granting_user=owner
        )

        collaboration_manager.update_share_permissions(
            share_id=shared_analysis.share_id,
            target_user_id=collaborator2.user_id,
            target_username=collaborator2.username,
            target_email=collaborator2.email,
            permission=SharePermission.VIEW_ONLY,
            granting_user=owner
        )

        # Step 3: Collaborators access the analysis
        context1 = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=collaborator1
        )
        assert context1["user_permission"] == SharePermission.EDIT

        context2 = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=collaborator2
        )
        assert context2["user_permission"] == SharePermission.VIEW_ONLY

        # Step 4: Collaborators add annotations
        # Collaborator 1 adds a question about assumptions
        question_annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=collaborator1,
            annotation_type=AnnotationType.QUESTION,
            title="Terminal Growth Rate Assumption",
            content="Is the 2.5% terminal growth rate conservative enough for Microsoft's mature business?",
            target_scope=AnnotationScope.ASSUMPTION,
            target_id="terminal_growth_rate"
        )

        # Collaborator 2 adds a comment on the results
        comment_annotation = collaboration_manager.add_annotation(
            analysis_id=shared_analysis.snapshot.analysis_id,
            user_profile=collaborator2,
            annotation_type=AnnotationType.COMMENT,
            title="Bull Case Scenario",
            content="The bull case seems optimistic given current market conditions and competition from cloud providers.",
            target_scope=AnnotationScope.RESULT,
            target_id="bull_case_scenario"
        )

        # Step 5: Owner responds to annotations
        collaboration_manager.reply_to_annotation(
            annotation_id=question_annotation.annotation_id,
            user_profile=owner,
            content="Good point. I used 2.5% based on historical GDP growth, but we could stress test with 2.0%."
        )

        collaboration_manager.reply_to_annotation(
            annotation_id=comment_annotation.annotation_id,
            user_profile=owner,
            content="Agreed. The bull case is more of a blue-sky scenario. The base case is more realistic."
        )

        # Step 6: Resolve the question after discussion
        collaboration_manager.resolve_annotation(
            annotation_id=question_annotation.annotation_id,
            user_profile=owner
        )

        # Step 7: Verify the complete collaboration state
        final_context = collaboration_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=owner
        )

        annotations = final_context["annotations"]
        assert len(annotations) == 2

        resolved_annotation = next(a for a in annotations if a.annotation_id == question_annotation.annotation_id)
        assert resolved_annotation.is_resolved is True
        assert len(resolved_annotation.replies) == 1

        unresolved_annotation = next(a for a in annotations if a.annotation_id == comment_annotation.annotation_id)
        assert unresolved_annotation.is_resolved is False
        assert len(unresolved_annotation.replies) == 1

    def test_workspace_collaboration_workflow(self, collaboration_manager, test_users, sample_financial_data):
        """Test workspace-based collaboration workflow."""
        owner, member1, member2 = test_users

        # Step 1: Create team workspace
        workspace = collaboration_manager.create_workspace(
            name="Tech Stocks Analysis Team",
            description="Collaborative workspace for analyzing technology stocks",
            workspace_type=WorkspaceType.TEAM,
            user_profile=owner,
            is_public=False
        )

        # Step 2: Invite team members
        collaboration_manager.workspace_manager.invite_to_workspace(
            workspace_id=workspace.workspace_id,
            inviter_id=owner.user_id,
            invitee_id=member1.user_id,
            invitee_username=member1.username,
            invitee_email=member1.email,
            role=WorkspaceMemberRole.CONTRIBUTOR
        )

        collaboration_manager.workspace_manager.invite_to_workspace(
            workspace_id=workspace.workspace_id,
            inviter_id=owner.user_id,
            invitee_id=member2.user_id,
            invitee_username=member2.username,
            invitee_email=member2.email,
            role=WorkspaceMemberRole.VIEWER
        )

        # Step 3: Members share analyses to workspace
        # Owner shares Microsoft analysis
        ms_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_financial_data,
            user_profile=owner,
            title="Microsoft - Tech Team Analysis",
            description="Team analysis of Microsoft for Q4 2024"
        )

        collaboration_manager.add_analysis_to_workspace(
            workspace_id=workspace.workspace_id,
            analysis_id=ms_analysis.analysis_id,
            user_profile=owner
        )

        # Member 1 contributes Apple analysis
        apple_data = sample_financial_data.copy()
        apple_data.update({
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "analysis_id": "apple_analysis_456"
        })

        apple_analysis = collaboration_manager.create_analysis_share(
            analysis_data=apple_data,
            user_profile=member1,
            title="Apple - Tech Team Analysis",
            description="Team analysis of Apple for Q4 2024"
        )

        collaboration_manager.add_analysis_to_workspace(
            workspace_id=workspace.workspace_id,
            analysis_id=apple_analysis.analysis_id,
            user_profile=member1
        )

        # Step 4: Create analysis collections
        workspace_obj = collaboration_manager.workspace_manager.get_workspace(workspace.workspace_id)
        workspace_obj.create_collection(
            name="Q4 2024 Large Cap Tech",
            description="Analysis collection for large cap technology companies",
            created_by=owner.user_id,
            analysis_ids=[ms_analysis.analysis_id, apple_analysis.analysis_id]
        )

        # Step 5: Cross-reference annotations between analyses
        collaboration_manager.add_annotation(
            analysis_id=ms_analysis.snapshot.analysis_id,
            user_profile=member1,
            annotation_type=AnnotationType.NOTE,
            title="Comparison with Apple",
            content="Microsoft's cloud growth is stronger than Apple's services growth. See Apple analysis for comparison.",
            target_scope=AnnotationScope.GENERAL
        )

        collaboration_manager.add_annotation(
            analysis_id=apple_analysis.snapshot.analysis_id,
            user_profile=member1,
            annotation_type=AnnotationType.NOTE,
            title="Comparison with Microsoft",
            content="Apple's hardware dependency vs Microsoft's software recurring revenue model. Microsoft seems more stable.",
            target_scope=AnnotationScope.GENERAL
        )

        # Step 6: Export workspace for backup/sharing
        export_data = collaboration_manager.export_workspace(
            workspace_id=workspace.workspace_id,
            user_profile=owner,
            include_analyses=True
        )

        assert export_data is not None
        assert len(export_data["shared_analyses"]) == 2
        assert len(export_data["collections"]) == 1

        # Step 7: Verify workspace statistics
        workspace_obj = collaboration_manager.workspace_manager.get_workspace(workspace.workspace_id)
        stats = workspace_obj.get_member_statistics()

        assert stats["total_members"] == 3  # Owner + 2 members
        assert len(workspace_obj.shared_analyses) == 2
        assert len(workspace_obj.collections) == 1

    def test_public_discovery_workflow(self, collaboration_manager, test_users, sample_financial_data):
        """Test public analysis discovery and collaboration workflow."""
        creator, discoverer1, discoverer2 = test_users

        # Step 1: Create public analyses
        public_analyses = []
        companies = [
            ("MSFT", "Microsoft Corporation"),
            ("GOOGL", "Alphabet Inc."),
            ("AMZN", "Amazon.com Inc.")
        ]

        for ticker, name in companies:
            analysis_data = sample_financial_data.copy()
            analysis_data.update({
                "ticker": ticker,
                "company_name": name,
                "analysis_id": f"{ticker.lower()}_analysis"
            })

            shared_analysis = collaboration_manager.create_analysis_share(
                analysis_data=analysis_data,
                user_profile=creator,
                title=f"{name} - Public Analysis",
                description=f"Public financial analysis of {name}",
                analysis_type=AnalysisType.COMPREHENSIVE,
                is_public=True,
                allow_comments=True,
                allow_downloads=True
            )
            public_analyses.append(shared_analysis)

        # Step 2: Discoverers find public analyses
        discovered = collaboration_manager.discover_public_analyses(limit=10)
        assert len(discovered) >= 3

        # Step 3: Search for specific analyses
        msft_results = collaboration_manager.search_shared_analyses(
            query="Microsoft",
            analysis_type=AnalysisType.COMPREHENSIVE
        )
        assert len(msft_results) >= 1
        assert any("Microsoft" in result.title for result in msft_results)

        # Step 4: Discoverers access and comment on public analyses
        msft_analysis = next(a for a in public_analyses if a.snapshot.company_ticker == "MSFT")

        # Discoverer 1 adds insightful comment
        collaboration_manager.add_annotation(
            analysis_id=msft_analysis.snapshot.analysis_id,
            user_profile=discoverer1,
            annotation_type=AnnotationType.SUGGESTION,
            title="Alternative Valuation Method",
            content="Have you considered using EV/EBITDA multiples for comparison with cloud peers like Salesforce?",
            target_scope=AnnotationScope.GENERAL
        )

        # Discoverer 2 asks technical question
        collaboration_manager.add_annotation(
            analysis_id=msft_analysis.snapshot.analysis_id,
            user_profile=discoverer2,
            annotation_type=AnnotationType.QUESTION,
            title="Azure Growth Assumptions",
            content="What assumptions are you using for Azure's growth deceleration? The current rate seems unsustainable.",
            target_scope=AnnotationScope.ASSUMPTION
        )

        # Step 5: Creator responds to community feedback
        annotations = collaboration_manager.annotation_manager.get_analysis_annotations(
            analysis_id=msft_analysis.snapshot.analysis_id
        )

        for annotation in annotations:
            if annotation.annotation_type == AnnotationType.SUGGESTION:
                collaboration_manager.reply_to_annotation(
                    annotation_id=annotation.annotation_id,
                    user_profile=creator,
                    content="Great suggestion! I'll add EV/EBITDA analysis in the next version. Current multiples vs SFDC would be interesting."
                )
            elif annotation.annotation_type == AnnotationType.QUESTION:
                collaboration_manager.reply_to_annotation(
                    annotation_id=annotation.annotation_id,
                    user_profile=creator,
                    content="I'm using a gradual deceleration: 45% -> 35% -> 25% -> 20% -> 15% over 5 years based on market saturation models."
                )

        # Step 6: Track engagement and statistics
        stats = collaboration_manager.get_collaboration_statistics()
        assert stats["sharing"]["public_shares"] >= 3
        assert stats["annotations"]["total_annotations"] >= 2

        activity = collaboration_manager.get_user_activity(creator, days=1)
        assert activity["shares_created"] >= 3


class TestStreamlitIntegration:
    """Test integration with Streamlit UI components."""

    @patch('streamlit.session_state', {})
    def test_streamlit_session_initialization(self, collaboration_manager):
        """Test Streamlit session state initialization."""
        with patch('core.collaboration.collaboration_manager.CollaborationManager', return_value=collaboration_manager):
            init_collaboration_session()

            assert 'collaboration_manager' in st.session_state
            assert 'current_user_profile' in st.session_state
            assert 'selected_share_id' in st.session_state
            assert 'show_annotation_form' in st.session_state

    def test_analysis_data_preparation(self, sample_financial_data):
        """Test preparation of analysis data for sharing."""
        # Mock session state with financial calculator
        mock_calculator = MagicMock()
        mock_calculator.financial_ratios_df = sample_financial_data["key_metrics"]

        with patch('streamlit.session_state') as mock_session:
            mock_session.ticker = sample_financial_data["ticker"]
            mock_session.company_name = sample_financial_data["company_name"]
            mock_session.financial_calculator = mock_calculator

            prepared_data = prepare_current_analysis_data()

            assert prepared_data["ticker"] == sample_financial_data["ticker"]
            assert prepared_data["company_name"] == sample_financial_data["company_name"]
            assert "analysis_id" in prepared_data
            assert "analysis_date" in prepared_data

    def test_end_to_end_ui_workflow(self, collaboration_manager, test_users, sample_financial_data):
        """Test end-to-end workflow through UI components."""
        user = test_users[0]

        # Mock session state
        with patch('streamlit.session_state') as mock_session:
            mock_session.collaboration_manager = collaboration_manager
            mock_session.current_user_profile = user
            mock_session.ticker = sample_financial_data["ticker"]
            mock_session.company_name = sample_financial_data["company_name"]
            mock_session.financial_calculator = MagicMock()
            mock_session.selected_share_id = None
            mock_session.show_annotation_form = False

            # Create shared analysis directly (simulating form submission)
            shared_analysis = collaboration_manager.create_analysis_share(
                analysis_data=sample_financial_data,
                user_profile=user,
                title="UI Test Analysis",
                description="Testing UI integration",
                is_public=True
            )

            # Set selected share ID
            mock_session.selected_share_id = shared_analysis.share_id

            # Access analysis (simulating UI access)
            context = collaboration_manager.access_shared_analysis(
                share_id=shared_analysis.share_id,
                user_profile=user
            )

            assert context is not None
            assert context["shared_analysis"].share_id == shared_analysis.share_id

            # Add annotation (simulating UI form submission)
            annotation = collaboration_manager.add_annotation(
                analysis_id=shared_analysis.snapshot.analysis_id,
                user_profile=user,
                annotation_type=AnnotationType.COMMENT,
                title="UI Test Comment",
                content="This comment was added through UI testing",
                target_scope=AnnotationScope.GENERAL
            )

            assert annotation is not None

            # Verify complete state
            final_context = collaboration_manager.access_shared_analysis(
                share_id=shared_analysis.share_id,
                user_profile=user
            )

            assert len(final_context["annotations"]) == 1
            assert final_context["annotations"][0].title == "UI Test Comment"


class TestCollaborationPerformance:
    """Test collaboration system performance and scalability."""

    def test_large_scale_collaboration(self, collaboration_manager, sample_financial_data):
        """Test collaboration with many users and analyses."""
        # Create multiple users
        users = [
            create_default_user_profile(f"user_{i}", f"user{i}", f"user{i}@test.com")
            for i in range(10)
        ]

        # Create multiple shared analyses
        shared_analyses = []
        for i, user in enumerate(users):
            analysis_data = sample_financial_data.copy()
            analysis_data.update({
                "analysis_id": f"analysis_{i}",
                "ticker": f"STOCK{i}",
                "company_name": f"Company {i}"
            })

            shared_analysis = collaboration_manager.create_analysis_share(
                analysis_data=analysis_data,
                user_profile=user,
                title=f"Analysis {i}",
                description=f"Test analysis number {i}",
                is_public=True
            )
            shared_analyses.append(shared_analysis)

        # Create many annotations
        for i, shared_analysis in enumerate(shared_analyses):
            for j, user in enumerate(users[:5]):  # First 5 users comment on all analyses
                collaboration_manager.add_annotation(
                    analysis_id=shared_analysis.snapshot.analysis_id,
                    user_profile=user,
                    annotation_type=AnnotationType.COMMENT,
                    title=f"Comment {j} on Analysis {i}",
                    content=f"This is comment {j} on analysis {i}",
                    target_scope=AnnotationScope.GENERAL
                )

        # Test search performance
        search_results = collaboration_manager.search_shared_analyses(
            query="Analysis",
            user_profile=users[0]
        )
        assert len(search_results) >= 10

        # Test annotation search performance
        annotation_results = collaboration_manager.search_annotations(
            query="comment",
            user_profile=users[0]
        )
        assert len(annotation_results) >= 25  # 5 users * 5+ analyses

        # Test statistics performance
        stats = collaboration_manager.get_collaboration_statistics()
        assert stats["sharing"]["total_shares"] >= 10
        assert stats["annotations"]["total_annotations"] >= 50

    def test_concurrent_access_simulation(self, collaboration_manager, test_users, sample_financial_data):
        """Simulate concurrent access to shared analyses."""
        owner = test_users[0]
        collaborators = test_users[1:]

        # Create shared analysis
        shared_analysis = collaboration_manager.create_analysis_share(
            analysis_data=sample_financial_data,
            user_profile=owner,
            title="Concurrent Access Test",
            description="Testing concurrent access patterns",
            is_public=True
        )

        # Simulate concurrent access
        access_results = []
        for user in collaborators:
            context = collaboration_manager.access_shared_analysis(
                share_id=shared_analysis.share_id,
                user_profile=user
            )
            access_results.append(context)

        # All accesses should succeed
        assert all(result is not None for result in access_results)

        # Simulate concurrent annotation creation
        annotations = []
        for i, user in enumerate(collaborators):
            annotation = collaboration_manager.add_annotation(
                analysis_id=shared_analysis.snapshot.analysis_id,
                user_profile=user,
                annotation_type=AnnotationType.COMMENT,
                title=f"Concurrent Comment {i}",
                content=f"This is concurrent comment {i}",
                target_scope=AnnotationScope.GENERAL
            )
            annotations.append(annotation)

        # All annotations should be created successfully
        assert all(annotation is not None for annotation in annotations)
        assert len(set(annotation.annotation_id for annotation in annotations)) == len(annotations)  # All unique