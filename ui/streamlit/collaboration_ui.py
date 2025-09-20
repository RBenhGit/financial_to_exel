"""
Streamlit UI Components for Collaborative Features

Provides UI components for analysis sharing, annotations, and collaboration
within the financial analysis application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid

from core.collaboration.collaboration_manager import CollaborationManager
from core.collaboration.analysis_sharing import AnalysisType, SharePermission, ShareStatus
from core.collaboration.annotations import AnnotationType, AnnotationScope, AnnotationTarget
from core.user_preferences.user_profile import UserProfile, create_default_user_profile


def init_collaboration_session():
    """Initialize collaboration-related session state variables"""
    if 'collaboration_manager' not in st.session_state:
        st.session_state.collaboration_manager = CollaborationManager()

    if 'current_user_profile' not in st.session_state:
        # Create a default user profile for demo purposes
        # In production, this would come from authentication
        st.session_state.current_user_profile = create_default_user_profile(
            user_id=str(uuid.uuid4()),
            username="demo_user",
            email="demo@example.com"
        )

    if 'selected_share_id' not in st.session_state:
        st.session_state.selected_share_id = None

    if 'show_annotation_form' not in st.session_state:
        st.session_state.show_annotation_form = False


def render_sharing_interface():
    """Render the analysis sharing interface"""
    st.subheader("📤 Share Analysis")

    init_collaboration_session()
    collab_manager = st.session_state.collaboration_manager
    user_profile = st.session_state.current_user_profile

    # Check if there's analysis data to share
    if not hasattr(st.session_state, 'financial_calculator') or not st.session_state.financial_calculator:
        st.warning("⚠️ Load company data and run analysis first to enable sharing")
        return

    with st.form("share_analysis_form"):
        st.write("**Share Current Analysis**")

        # Basic share information
        col1, col2 = st.columns(2)

        with col1:
            share_title = st.text_input(
                "Share Title",
                value=f"Analysis of {getattr(st.session_state, 'ticker', 'Company')}",
                help="Title for the shared analysis"
            )

            analysis_type = st.selectbox(
                "Analysis Type",
                options=[t.value for t in AnalysisType],
                index=0,
                help="Type of financial analysis"
            )

            is_public = st.checkbox(
                "Make Public",
                value=False,
                help="Allow anyone to view this analysis"
            )

        with col2:
            description = st.text_area(
                "Description",
                placeholder="Describe your analysis, key findings, or methodology...",
                height=100
            )

            expires_in_days = st.number_input(
                "Expires in Days",
                min_value=1,
                max_value=365,
                value=30,
                help="Automatic expiration period"
            )

            password = st.text_input(
                "Password (Optional)",
                type="password",
                help="Protect with password"
            )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col3, col4 = st.columns(2)

            with col3:
                allow_comments = st.checkbox("Allow Comments", value=True)
                allow_downloads = st.checkbox("Allow Downloads", value=True)

            with col4:
                max_users = st.number_input(
                    "Max Users",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="Maximum number of users with access"
                )

        submitted = st.form_submit_button("🚀 Create Share")

        if submitted and share_title:
            try:
                # Prepare analysis data for sharing
                analysis_data = prepare_current_analysis_data()

                # Create the share
                shared_analysis = collab_manager.create_analysis_share(
                    analysis_data=analysis_data,
                    user_profile=user_profile,
                    title=share_title,
                    description=description,
                    analysis_type=AnalysisType(analysis_type),
                    is_public=is_public,
                    expires_in_days=expires_in_days,
                    password=password if password else None,
                    allow_comments=allow_comments,
                    allow_downloads=allow_downloads
                )

                # Set max users
                shared_analysis.max_users = max_users
                collab_manager.share_manager._save_shared_analysis(shared_analysis)

                st.success(f"✅ Analysis shared successfully!")

                # Display share information
                st.info(f"**Share ID:** `{shared_analysis.share_id}`")

                # Generate share URL (simplified for demo)
                base_url = "http://localhost:8501"  # In production, get actual URL
                share_url = f"{base_url}?share_id={shared_analysis.share_id}"

                st.code(share_url, language="text")
                st.caption("Share this URL with others to give them access")

            except Exception as e:
                st.error(f"❌ Failed to create share: {e}")


def render_shared_analyses_browser():
    """Render browser for shared analyses"""
    st.subheader("🔍 Browse Shared Analyses")

    init_collaboration_session()
    collab_manager = st.session_state.collaboration_manager
    user_profile = st.session_state.current_user_profile

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["My Shares", "Public Analyses", "Search"])

    with tab1:
        st.write("**Your Shared Analyses**")
        user_shares = collab_manager.share_manager.get_user_shares(
            user_profile.user_id,
            include_public=False
        )

        if user_shares:
            for share in user_shares:
                render_share_card(share, is_owner=True)
        else:
            st.info("You haven't shared any analyses yet.")

    with tab2:
        st.write("**Public Analyses**")
        public_shares = collab_manager.discover_public_analyses(limit=20)

        if public_shares:
            for share in public_shares:
                render_share_card(share, is_owner=False)
        else:
            st.info("No public analyses available.")

    with tab3:
        st.write("**Search Analyses**")

        search_col1, search_col2 = st.columns([3, 1])

        with search_col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Search by company, title, or description..."
            )

        with search_col2:
            search_type = st.selectbox(
                "Type",
                options=["All"] + [t.value for t in AnalysisType]
            )

        if search_query:
            analysis_type_filter = None if search_type == "All" else AnalysisType(search_type)

            search_results = collab_manager.search_shared_analyses(
                query=search_query,
                user_profile=user_profile,
                analysis_type=analysis_type_filter
            )

            if search_results:
                st.write(f"Found {len(search_results)} results:")
                for share in search_results:
                    render_share_card(share, is_owner=share.original_user_id == user_profile.user_id)
            else:
                st.info("No matching analyses found.")


def render_share_card(shared_analysis, is_owner: bool = False):
    """Render a card for a shared analysis"""
    with st.container():
        st.markdown("---")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Title and basic info
            title_text = f"**{shared_analysis.title}**"
            if shared_analysis.is_public:
                title_text += " 🌐"
            if shared_analysis.requires_password:
                title_text += " 🔒"

            st.markdown(title_text)

            # Company and type
            st.caption(
                f"{shared_analysis.snapshot.company_name} ({shared_analysis.snapshot.company_ticker}) • "
                f"{shared_analysis.snapshot.analysis_type.value.title()}"
            )

            # Description
            if shared_analysis.description:
                st.write(shared_analysis.description[:150] + "..." if len(shared_analysis.description) > 150 else shared_analysis.description)

        with col2:
            # Metadata
            st.caption(f"Created: {shared_analysis.created_at.strftime('%Y-%m-%d')}")
            st.caption(f"Views: {shared_analysis.access_count}")

            if shared_analysis.expires_at:
                days_until_expiry = (shared_analysis.expires_at - datetime.now()).days
                if days_until_expiry > 0:
                    st.caption(f"Expires in: {days_until_expiry} days")
                else:
                    st.caption("⚠️ Expired")

        with col3:
            # Actions
            if st.button(f"View", key=f"view_{shared_analysis.share_id}"):
                st.session_state.selected_share_id = shared_analysis.share_id
                st.rerun()

            if is_owner:
                if st.button(f"Manage", key=f"manage_{shared_analysis.share_id}"):
                    render_share_management(shared_analysis)


def render_share_access():
    """Render interface for accessing a shared analysis"""
    st.subheader("🔗 Access Shared Analysis")

    init_collaboration_session()
    collab_manager = st.session_state.collaboration_manager
    user_profile = st.session_state.current_user_profile

    # Check if there's a selected share
    if st.session_state.selected_share_id:
        share_id = st.session_state.selected_share_id
        collaboration_context = collab_manager.access_shared_analysis(
            share_id=share_id,
            user_profile=user_profile
        )

        if collaboration_context:
            render_shared_analysis_view(collaboration_context)
        else:
            st.error("❌ Unable to access this shared analysis")
            st.session_state.selected_share_id = None

    else:
        # Manual share ID entry
        with st.form("access_share_form"):
            share_id = st.text_input(
                "Share ID",
                placeholder="Enter the share ID you received..."
            )

            password = st.text_input(
                "Password (if required)",
                type="password"
            )

            submitted = st.form_submit_button("🔓 Access Share")

            if submitted and share_id:
                collaboration_context = collab_manager.access_shared_analysis(
                    share_id=share_id,
                    user_profile=user_profile,
                    password=password if password else None
                )

                if collaboration_context:
                    st.session_state.selected_share_id = share_id
                    st.rerun()
                else:
                    st.error("❌ Unable to access this share. Check the ID and password.")


def render_shared_analysis_view(collaboration_context):
    """Render the view for a shared analysis"""
    shared_analysis = collaboration_context["shared_analysis"]
    annotations = collaboration_context["annotations"]
    can_comment = collaboration_context["can_comment"]
    is_owner = collaboration_context["is_owner"]

    # Header
    st.subheader(f"📊 {shared_analysis.title}")

    # Analysis metadata
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Company", shared_analysis.snapshot.company_ticker)

    with col2:
        st.metric("Type", shared_analysis.snapshot.analysis_type.value.title())

    with col3:
        st.metric("Created", shared_analysis.created_at.strftime('%Y-%m-%d'))

    with col4:
        st.metric("Views", shared_analysis.access_count)

    # Description
    if shared_analysis.description:
        st.write("**Description:**")
        st.write(shared_analysis.description)

    # Analysis results
    st.write("**Analysis Results:**")
    render_analysis_results(shared_analysis.snapshot)

    # Annotations section
    if can_comment:
        render_annotations_section(shared_analysis, annotations)

    # Download option
    if collaboration_context["can_download"]:
        st.markdown("---")
        if st.button("📥 Download Analysis Data"):
            render_analysis_download(shared_analysis)


def render_analysis_results(snapshot):
    """Render the analysis results from a snapshot"""
    # Key metrics
    if snapshot.key_metrics:
        st.write("**Key Metrics:**")
        metrics_df = pd.DataFrame([snapshot.key_metrics]).T
        metrics_df.columns = ['Value']
        st.dataframe(metrics_df)

    # Results data (simplified display)
    if snapshot.results_data:
        st.write("**Analysis Results:**")

        # Display results based on type
        for key, value in snapshot.results_data.items():
            if isinstance(value, dict):
                with st.expander(f"📈 {key.replace('_', ' ').title()}"):
                    if value:
                        df = pd.DataFrame([value]).T
                        df.columns = ['Value']
                        st.dataframe(df)
            elif isinstance(value, (int, float)):
                st.metric(key.replace('_', ' ').title(), f"{value:,.2f}")

    # Charts (if available)
    if snapshot.charts:
        st.write("**Charts:**")
        st.info("Chart rendering would be implemented here based on chart data format")


def render_annotations_section(shared_analysis, annotations):
    """Render the annotations section"""
    st.markdown("---")
    st.subheader("💬 Comments & Annotations")

    init_collaboration_session()
    collab_manager = st.session_state.collaboration_manager
    user_profile = st.session_state.current_user_profile

    # Add new annotation button
    if st.button("➕ Add Comment"):
        st.session_state.show_annotation_form = True

    # New annotation form
    if st.session_state.show_annotation_form:
        with st.form("new_annotation_form"):
            st.write("**Add New Comment**")

            col1, col2 = st.columns(2)

            with col1:
                annotation_type = st.selectbox(
                    "Type",
                    options=[t.value for t in AnnotationType],
                    index=0
                )

                target_scope = st.selectbox(
                    "Scope",
                    options=[s.value for s in AnnotationScope],
                    index=0
                )

            with col2:
                title = st.text_input("Title", placeholder="Brief title for your comment...")

                is_private = st.checkbox("Private Comment", value=False)

            content = st.text_area(
                "Content",
                placeholder="Write your comment or annotation here...",
                height=100
            )

            col_submit, col_cancel = st.columns(2)

            with col_submit:
                submitted = st.form_submit_button("💬 Add Comment")

            with col_cancel:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_annotation_form = False
                    st.rerun()

            if submitted and title and content:
                try:
                    annotation = collab_manager.add_annotation(
                        analysis_id=shared_analysis.snapshot.analysis_id,
                        user_profile=user_profile,
                        annotation_type=AnnotationType(annotation_type),
                        title=title,
                        content=content,
                        target_scope=AnnotationScope(target_scope),
                        share_id=shared_analysis.share_id,
                        is_private=is_private
                    )

                    st.success("✅ Comment added successfully!")
                    st.session_state.show_annotation_form = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to add comment: {e}")

    # Display existing annotations
    if annotations:
        st.write(f"**Comments ({len(annotations)}):**")

        for annotation in annotations:
            render_annotation_card(annotation)
    else:
        st.info("No comments yet. Be the first to add one!")


def render_annotation_card(annotation):
    """Render a single annotation card"""
    with st.container():
        st.markdown("---")

        # Header
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            title_text = f"**{annotation.title}**"
            if annotation.is_resolved:
                title_text += " ✅"
            if annotation.is_private:
                title_text += " 🔒"

            st.markdown(title_text)

        with col2:
            st.caption(f"By: {annotation.username}")
            st.caption(f"Type: {annotation.annotation_type.value}")

        with col3:
            st.caption(annotation.created_at.strftime('%Y-%m-%d %H:%M'))
            if annotation.likes:
                st.caption(f"👍 {len(annotation.likes)}")

        # Content
        st.write(annotation.content)

        # Tags
        if annotation.tags:
            tag_text = " ".join([f"`{tag}`" for tag in annotation.tags])
            st.markdown(f"Tags: {tag_text}")

        # Replies
        if annotation.replies:
            with st.expander(f"💬 Replies ({len(annotation.replies)})"):
                for reply in annotation.replies:
                    st.markdown(f"**{reply.username}** - {reply.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.write(reply.content)
                    if reply.is_edited:
                        st.caption("(edited)")

        # Actions
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button(f"👍 Like", key=f"like_{annotation.annotation_id}"):
                init_collaboration_session()
                collab_manager = st.session_state.collaboration_manager
                user_profile = st.session_state.current_user_profile
                collab_manager.annotation_manager.toggle_like(
                    annotation.annotation_id,
                    user_profile.user_id
                )
                st.rerun()

        with action_col2:
            if st.button(f"💬 Reply", key=f"reply_{annotation.annotation_id}"):
                st.session_state[f"show_reply_{annotation.annotation_id}"] = True

        with action_col3:
            if not annotation.is_resolved:
                if st.button(f"✅ Resolve", key=f"resolve_{annotation.annotation_id}"):
                    init_collaboration_session()
                    collab_manager = st.session_state.collaboration_manager
                    user_profile = st.session_state.current_user_profile
                    collab_manager.resolve_annotation(
                        annotation.annotation_id,
                        user_profile
                    )
                    st.rerun()

        # Reply form
        if st.session_state.get(f"show_reply_{annotation.annotation_id}", False):
            with st.form(f"reply_form_{annotation.annotation_id}"):
                reply_content = st.text_area(
                    "Reply",
                    placeholder="Write your reply...",
                    key=f"reply_content_{annotation.annotation_id}"
                )

                col_reply, col_cancel = st.columns(2)

                with col_reply:
                    if st.form_submit_button("💬 Add Reply"):
                        if reply_content:
                            init_collaboration_session()
                            collab_manager = st.session_state.collaboration_manager
                            user_profile = st.session_state.current_user_profile

                            success = collab_manager.reply_to_annotation(
                                annotation.annotation_id,
                                user_profile,
                                reply_content
                            )

                            if success:
                                st.success("✅ Reply added!")
                                st.session_state[f"show_reply_{annotation.annotation_id}"] = False
                                st.rerun()

                with col_cancel:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state[f"show_reply_{annotation.annotation_id}"] = False
                        st.rerun()


def render_collaboration_dashboard():
    """Render the main collaboration dashboard"""
    st.title("🤝 Collaboration Center")

    init_collaboration_session()
    collab_manager = st.session_state.collaboration_manager
    user_profile = st.session_state.current_user_profile

    # Statistics overview
    stats = collab_manager.get_collaboration_statistics()
    user_activity = collab_manager.get_user_activity(user_profile, days=30)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Your Shares", user_activity["shares_created"])

    with col2:
        st.metric("Your Comments", user_activity["annotations_created"])

    with col3:
        st.metric("Total Public Shares", stats["sharing"]["public_shares"])

    with col4:
        st.metric("Total Comments", stats["annotations"]["total_annotations"])

    # Main interface tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Share Analysis",
        "🔍 Browse Shares",
        "🔗 Access Share",
        "📊 Activity"
    ])

    with tab1:
        render_sharing_interface()

    with tab2:
        render_shared_analyses_browser()

    with tab3:
        render_share_access()

    with tab4:
        render_activity_dashboard(user_activity, stats)


def render_activity_dashboard(user_activity, stats):
    """Render user activity dashboard"""
    st.subheader("📈 Your Activity")

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Recent Shares**")
        if user_activity["recent_shares"]:
            for share in user_activity["recent_shares"]:
                st.write(f"• {share.title} ({share.created_at.strftime('%Y-%m-%d')})")
        else:
            st.info("No recent shares")

    with col2:
        st.write("**Recent Comments**")
        if user_activity["recent_annotations"]:
            for annotation in user_activity["recent_annotations"]:
                st.write(f"• {annotation.title} ({annotation.created_at.strftime('%Y-%m-%d')})")
        else:
            st.info("No recent comments")

    # Activity timeline
    if user_activity["recent_events"]:
        st.write("**Recent Activity Timeline**")
        events_df = pd.DataFrame([
            {
                "Date": event.timestamp.strftime('%Y-%m-%d %H:%M'),
                "Event": event.event_type.replace('_', ' ').title(),
                "Target": event.target_id[:8] + "..."
            }
            for event in user_activity["recent_events"]
        ])
        st.dataframe(events_df, use_container_width=True)


def prepare_current_analysis_data() -> Dict[str, Any]:
    """Prepare current analysis data for sharing"""
    # This function would collect data from the current session state
    # and prepare it for sharing. Implementation depends on the specific
    # structure of analysis data in the session state.

    analysis_data = {
        "analysis_id": str(uuid.uuid4()),
        "ticker": getattr(st.session_state, 'ticker', 'UNKNOWN'),
        "company_name": getattr(st.session_state, 'company_name', 'Unknown Company'),
        "analysis_date": datetime.now().isoformat(),
        "results": {},
        "input_parameters": {},
        "key_metrics": {},
        "assumptions": {},
        "data_sources": [],
        "charts": [],
        "scenarios": []
    }

    # Extract data from financial calculator if available
    if hasattr(st.session_state, 'financial_calculator') and st.session_state.financial_calculator:
        calc = st.session_state.financial_calculator

        # Add available data
        if hasattr(calc, 'financial_ratios_df') and calc.financial_ratios_df is not None:
            analysis_data["key_metrics"] = calc.financial_ratios_df.to_dict()

        # Add more data extraction as needed...

    return analysis_data


def render_analysis_download(shared_analysis):
    """Render analysis download options"""
    # This would provide download functionality for shared analyses
    st.info("Download functionality would be implemented here")


def render_share_management(shared_analysis):
    """Render share management interface for owners"""
    # This would provide management options for share owners
    st.info("Share management interface would be implemented here")