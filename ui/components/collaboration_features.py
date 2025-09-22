"""
Real-Time Collaboration Features
===============================

Advanced collaboration component enabling real-time sharing, annotations,
comments, and synchronized analysis sessions for financial dashboards.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import hashlib

from .advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState,
    InteractionEvent, performance_monitor
)


class SessionRole(Enum):
    """User roles in collaboration session"""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    COMMENTATOR = "commentator"


class ActivityType(Enum):
    """Types of collaboration activities"""
    ANNOTATION_ADDED = "annotation_added"
    COMMENT_POSTED = "comment_posted"
    ANALYSIS_SHARED = "analysis_shared"
    DASHBOARD_MODIFIED = "dashboard_modified"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    DATA_UPDATED = "data_updated"
    EXPORT_GENERATED = "export_generated"


@dataclass
class CollaborationUser:
    """Represents a collaboration session user"""
    id: str
    name: str
    email: str
    role: SessionRole
    avatar_url: str = ""
    last_activity: datetime = field(default_factory=datetime.now)
    is_online: bool = True
    cursor_position: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Annotation:
    """Represents an annotation on charts or data"""
    id: str
    user_id: str
    timestamp: datetime
    chart_id: str
    x_position: float
    y_position: float
    text: str
    annotation_type: str = "note"  # note, highlight, question, insight
    resolved: bool = False
    replies: List[Dict] = field(default_factory=list)


@dataclass
class Comment:
    """Represents a comment on analysis or dashboard"""
    id: str
    user_id: str
    timestamp: datetime
    content: str
    target_type: str  # dashboard, component, analysis
    target_id: str
    parent_comment_id: Optional[str] = None
    resolved: bool = False
    attachments: List[str] = field(default_factory=list)


@dataclass
class ActivityLog:
    """Represents a collaboration activity"""
    id: str
    user_id: str
    timestamp: datetime
    activity_type: ActivityType
    description: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedAnalysis:
    """Represents a shared analysis session"""
    id: str
    title: str
    description: str
    creator_id: str
    created_at: datetime
    last_modified: datetime
    shared_with: List[str] = field(default_factory=list)
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, str] = field(default_factory=dict)
    version: int = 1


class CollaborationManager(AdvancedComponent):
    """
    Advanced collaboration manager providing real-time sharing,
    annotations, comments, and synchronized analysis sessions
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.session_id = str(uuid.uuid4())
        self.users: Dict[str, CollaborationUser] = {}
        self.annotations: Dict[str, Annotation] = {}
        self.comments: Dict[str, Comment] = {}
        self.activity_log: List[ActivityLog] = []
        self.shared_analyses: Dict[str, SharedAnalysis] = {}
        self.current_user: Optional[CollaborationUser] = None

    @performance_monitor
    def render_content(self, data: Dict = None, **kwargs) -> Dict[str, Any]:
        """Render collaboration features interface"""

        # Initialize current user if not set
        if not self.current_user:
            self._initialize_current_user()

        # Render collaboration header
        self._render_collaboration_header()

        # Create main collaboration interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👥 Session", "📝 Annotations", "💬 Comments",
            "📊 Shared Analysis", "📋 Activity Log"
        ])

        with tab1:
            self._render_session_management()

        with tab2:
            self._render_annotations_interface()

        with tab3:
            self._render_comments_interface()

        with tab4:
            self._render_shared_analysis_interface()

        with tab5:
            self._render_activity_log()

        return {
            "session_id": self.session_id,
            "active_users": len([u for u in self.users.values() if u.is_online]),
            "annotations_count": len(self.annotations),
            "comments_count": len(self.comments),
            "shared_analyses_count": len(self.shared_analyses)
        }

    def _initialize_current_user(self):
        """Initialize current user for the session"""
        # In a real implementation, this would authenticate the user
        user_id = st.session_state.get("user_id", str(uuid.uuid4()))
        st.session_state.user_id = user_id

        if user_id not in self.users:
            self.current_user = CollaborationUser(
                id=user_id,
                name=st.session_state.get("user_name", "Anonymous User"),
                email=st.session_state.get("user_email", "user@example.com"),
                role=SessionRole.EDITOR
            )
            self.users[user_id] = self.current_user
            self._log_activity(ActivityType.USER_JOINED, "User joined the session")
        else:
            self.current_user = self.users[user_id]

    def _render_collaboration_header(self):
        """Render collaboration status header"""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.markdown(f"**🚀 Session:** `{self.session_id[:8]}...`")

        with col2:
            online_users = [u for u in self.users.values() if u.is_online]
            st.metric("👥 Online", len(online_users))

        with col3:
            st.metric("📝 Annotations", len(self.annotations))

        with col4:
            st.metric("💬 Comments", len(self.comments))

        # User presence indicators
        if online_users:
            st.markdown("**Active Users:**")
            user_cols = st.columns(min(len(online_users), 5))
            for i, user in enumerate(online_users[:5]):
                with user_cols[i]:
                    role_emoji = {"owner": "👑", "editor": "✏️", "viewer": "👁️", "commentator": "💬"}
                    st.markdown(f"{role_emoji.get(user.role.value, '👤')} {user.name}")

    def _render_session_management(self):
        """Render session management interface"""
        st.markdown("### 👥 Collaboration Session")

        # Session info
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Session Details")
            st.info(f"""
            **Session ID:** {self.session_id}

            **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

            **Your Role:** {self.current_user.role.value.title() if self.current_user else 'Unknown'}
            """)

            # Share session
            if st.button("📤 Share Session", key=f"{self.config.id}_share_session"):
                self._generate_share_link()

        with col2:
            st.subheader("Invite Users")

            invite_email = st.text_input(
                "Email Address",
                placeholder="user@example.com",
                key=f"{self.config.id}_invite_email"
            )

            invite_role = st.selectbox(
                "Role",
                options=[role.value.title() for role in SessionRole],
                key=f"{self.config.id}_invite_role"
            )

            if st.button("📨 Send Invite", key=f"{self.config.id}_send_invite"):
                if invite_email:
                    self._send_collaboration_invite(invite_email, SessionRole(invite_role.lower()))
                    st.success(f"Invitation sent to {invite_email}")

        # Active users management
        st.subheader("Active Users")
        if self.users:
            users_data = []
            for user in self.users.values():
                users_data.append({
                    "Name": user.name,
                    "Email": user.email,
                    "Role": user.role.value.title(),
                    "Status": "🟢 Online" if user.is_online else "🔴 Offline",
                    "Last Activity": user.last_activity.strftime('%H:%M:%S')
                })

            users_df = pd.DataFrame(users_data)
            st.dataframe(users_df, use_container_width=True, hide_index=True)

            # User management controls
            if self.current_user and self.current_user.role == SessionRole.OWNER:
                st.subheader("User Management")

                manage_user = st.selectbox(
                    "Select User to Manage",
                    options=[u.name for u in self.users.values() if u.id != self.current_user.id],
                    key=f"{self.config.id}_manage_user"
                )

                if manage_user:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("🔼 Promote", key=f"{self.config.id}_promote"):
                            self._promote_user(manage_user)

                    with col2:
                        if st.button("🔽 Demote", key=f"{self.config.id}_demote"):
                            self._demote_user(manage_user)

                    with col3:
                        if st.button("🚫 Remove", key=f"{self.config.id}_remove"):
                            self._remove_user(manage_user)

    def _render_annotations_interface(self):
        """Render annotations management interface"""
        st.markdown("### 📝 Chart Annotations")

        # Add new annotation
        with st.expander("➕ Add Annotation", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                chart_id = st.text_input(
                    "Chart ID",
                    placeholder="chart_component_id",
                    key=f"{self.config.id}_ann_chart_id"
                )

                x_pos = st.number_input(
                    "X Position",
                    value=0.0,
                    key=f"{self.config.id}_ann_x"
                )

                y_pos = st.number_input(
                    "Y Position",
                    value=0.0,
                    key=f"{self.config.id}_ann_y"
                )

            with col2:
                annotation_type = st.selectbox(
                    "Type",
                    options=["note", "highlight", "question", "insight"],
                    key=f"{self.config.id}_ann_type"
                )

                annotation_text = st.text_area(
                    "Annotation Text",
                    placeholder="Enter your annotation...",
                    key=f"{self.config.id}_ann_text"
                )

            if st.button("📝 Add Annotation", key=f"{self.config.id}_add_annotation"):
                if chart_id and annotation_text:
                    self._add_annotation(chart_id, x_pos, y_pos, annotation_text, annotation_type)
                    st.success("Annotation added successfully!")
                    st.rerun()

        # Display existing annotations
        st.subheader("Existing Annotations")
        if self.annotations:
            for annotation in self.annotations.values():
                user = self.users.get(annotation.user_id)
                user_name = user.name if user else "Unknown User"

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{annotation.text}**")
                        st.caption(f"By {user_name} on {annotation.chart_id} at ({annotation.x_position:.2f}, {annotation.y_position:.2f})")
                        st.caption(f"Type: {annotation.annotation_type} | {annotation.timestamp.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        if not annotation.resolved:
                            if st.button("✅ Resolve", key=f"resolve_{annotation.id}"):
                                self._resolve_annotation(annotation.id)
                                st.rerun()
                        else:
                            st.success("✅ Resolved")

                    with col3:
                        if self.current_user and (self.current_user.id == annotation.user_id or
                                                self.current_user.role in [SessionRole.OWNER, SessionRole.EDITOR]):
                            if st.button("🗑️ Delete", key=f"delete_ann_{annotation.id}"):
                                self._delete_annotation(annotation.id)
                                st.rerun()

                    # Show replies
                    if annotation.replies:
                        st.markdown("**Replies:**")
                        for reply in annotation.replies:
                            reply_user = self.users.get(reply['user_id'])
                            reply_user_name = reply_user.name if reply_user else "Unknown User"
                            st.markdown(f"↳ {reply['text']} - *{reply_user_name}*")

                    # Add reply
                    reply_text = st.text_input(
                        "Reply",
                        placeholder="Add a reply...",
                        key=f"reply_{annotation.id}"
                    )
                    if st.button("💬 Reply", key=f"reply_btn_{annotation.id}"):
                        if reply_text:
                            self._add_annotation_reply(annotation.id, reply_text)
                            st.rerun()

                    st.divider()
        else:
            st.info("No annotations yet. Add annotations to charts for collaborative analysis.")

    def _render_comments_interface(self):
        """Render comments and discussion interface"""
        st.markdown("### 💬 Comments & Discussions")

        # Add new comment
        with st.expander("➕ Add Comment", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                target_type = st.selectbox(
                    "Comment On",
                    options=["dashboard", "component", "analysis"],
                    key=f"{self.config.id}_comment_target_type"
                )

                target_id = st.text_input(
                    "Target ID",
                    placeholder="dashboard_id or component_id",
                    key=f"{self.config.id}_comment_target_id"
                )

            with col2:
                comment_content = st.text_area(
                    "Comment",
                    placeholder="Share your thoughts...",
                    height=100,
                    key=f"{self.config.id}_comment_content"
                )

            if st.button("💬 Post Comment", key=f"{self.config.id}_post_comment"):
                if target_id and comment_content:
                    self._add_comment(target_type, target_id, comment_content)
                    st.success("Comment posted!")
                    st.rerun()

        # Display comments
        st.subheader("Recent Comments")
        if self.comments:
            # Sort comments by timestamp (newest first)
            sorted_comments = sorted(self.comments.values(), key=lambda x: x.timestamp, reverse=True)

            for comment in sorted_comments:
                user = self.users.get(comment.user_id)
                user_name = user.name if user else "Unknown User"

                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"**{user_name}** commented on *{comment.target_type}*:")
                        st.markdown(comment.content)
                        st.caption(f"Target: {comment.target_id} | {comment.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

                        if not comment.resolved:
                            if st.button("✅ Mark Resolved", key=f"resolve_comment_{comment.id}"):
                                self._resolve_comment(comment.id)
                                st.rerun()
                        else:
                            st.success("✅ Resolved")

                    with col2:
                        if self.current_user and (self.current_user.id == comment.user_id or
                                                self.current_user.role in [SessionRole.OWNER, SessionRole.EDITOR]):
                            if st.button("🗑️ Delete", key=f"delete_comment_{comment.id}"):
                                self._delete_comment(comment.id)
                                st.rerun()

                    st.divider()
        else:
            st.info("No comments yet. Start a discussion by posting a comment.")

    def _render_shared_analysis_interface(self):
        """Render shared analysis management"""
        st.markdown("### 📊 Shared Analysis Sessions")

        # Create new shared analysis
        with st.expander("🆕 Create Shared Analysis", expanded=False):
            analysis_title = st.text_input(
                "Analysis Title",
                placeholder="Q4 Portfolio Performance Review",
                key=f"{self.config.id}_analysis_title"
            )

            analysis_description = st.text_area(
                "Description",
                placeholder="Describe the analysis...",
                key=f"{self.config.id}_analysis_description"
            )

            if st.button("📊 Create Analysis", key=f"{self.config.id}_create_analysis"):
                if analysis_title:
                    self._create_shared_analysis(analysis_title, analysis_description)
                    st.success("Shared analysis created!")
                    st.rerun()

        # Display shared analyses
        st.subheader("Available Shared Analyses")
        if self.shared_analyses:
            for analysis in self.shared_analyses.values():
                creator = self.users.get(analysis.creator_id)
                creator_name = creator.name if creator else "Unknown User"

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{analysis.title}**")
                        st.markdown(analysis.description)
                        st.caption(f"Created by {creator_name} | Version {analysis.version}")
                        st.caption(f"Last modified: {analysis.last_modified.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        if st.button("📂 Open", key=f"open_analysis_{analysis.id}"):
                            self._open_shared_analysis(analysis.id)
                            st.success(f"Opened analysis: {analysis.title}")

                    with col3:
                        if st.button("📤 Export", key=f"export_analysis_{analysis.id}"):
                            self._export_shared_analysis(analysis.id)

                    # Share settings
                    if analysis.creator_id == self.current_user.id:
                        with st.expander(f"⚙️ Share Settings - {analysis.title}"):
                            share_with = st.text_input(
                                "Share with (email)",
                                key=f"share_{analysis.id}"
                            )
                            permission = st.selectbox(
                                "Permission",
                                options=["view", "edit"],
                                key=f"permission_{analysis.id}"
                            )
                            if st.button("👥 Share", key=f"share_btn_{analysis.id}"):
                                if share_with:
                                    self._share_analysis(analysis.id, share_with, permission)
                                    st.success(f"Analysis shared with {share_with}")

                    st.divider()
        else:
            st.info("No shared analyses yet. Create one to collaborate on specific analysis tasks.")

    def _render_activity_log(self):
        """Render collaboration activity log"""
        st.markdown("### 📋 Activity Log")

        # Filter controls
        col1, col2, col3 = st.columns(3)

        with col1:
            activity_filter = st.selectbox(
                "Filter by Activity",
                options=["All"] + [activity.value for activity in ActivityType],
                key=f"{self.config.id}_activity_filter"
            )

        with col2:
            user_filter = st.selectbox(
                "Filter by User",
                options=["All"] + [user.name for user in self.users.values()],
                key=f"{self.config.id}_user_filter"
            )

        with col3:
            hours_back = st.number_input(
                "Hours Back",
                min_value=1,
                max_value=168,  # 1 week
                value=24,
                key=f"{self.config.id}_hours_back"
            )

        # Filter activities
        filtered_activities = self._filter_activities(activity_filter, user_filter, hours_back)

        # Display activity log
        if filtered_activities:
            for activity in filtered_activities:
                user = self.users.get(activity.user_id)
                user_name = user.name if user else "Unknown User"

                activity_icon = {
                    ActivityType.ANNOTATION_ADDED: "📝",
                    ActivityType.COMMENT_POSTED: "💬",
                    ActivityType.ANALYSIS_SHARED: "📊",
                    ActivityType.DASHBOARD_MODIFIED: "🔧",
                    ActivityType.USER_JOINED: "👋",
                    ActivityType.USER_LEFT: "👋",
                    ActivityType.DATA_UPDATED: "📊",
                    ActivityType.EXPORT_GENERATED: "📤"
                }.get(activity.activity_type, "📋")

                st.markdown(f"{activity_icon} **{user_name}** {activity.description}")
                st.caption(f"{activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

                if activity.data:
                    with st.expander("Details"):
                        st.json(activity.data)

                st.divider()
        else:
            st.info("No activities found for the selected filters.")

        # Export activity log
        if st.button("📥 Export Activity Log", key=f"{self.config.id}_export_log"):
            self._export_activity_log()

    def _add_annotation(self, chart_id: str, x_pos: float, y_pos: float, text: str, annotation_type: str):
        """Add new annotation"""
        annotation = Annotation(
            id=str(uuid.uuid4()),
            user_id=self.current_user.id,
            timestamp=datetime.now(),
            chart_id=chart_id,
            x_position=x_pos,
            y_position=y_pos,
            text=text,
            annotation_type=annotation_type
        )
        self.annotations[annotation.id] = annotation
        self._log_activity(ActivityType.ANNOTATION_ADDED, f"Added annotation to {chart_id}")

    def _add_comment(self, target_type: str, target_id: str, content: str):
        """Add new comment"""
        comment = Comment(
            id=str(uuid.uuid4()),
            user_id=self.current_user.id,
            timestamp=datetime.now(),
            content=content,
            target_type=target_type,
            target_id=target_id
        )
        self.comments[comment.id] = comment
        self._log_activity(ActivityType.COMMENT_POSTED, f"Posted comment on {target_type}")

    def _create_shared_analysis(self, title: str, description: str):
        """Create new shared analysis"""
        analysis = SharedAnalysis(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            creator_id=self.current_user.id,
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        self.shared_analyses[analysis.id] = analysis
        self._log_activity(ActivityType.ANALYSIS_SHARED, f"Created shared analysis: {title}")

    def _log_activity(self, activity_type: ActivityType, description: str, data: Dict = None):
        """Log collaboration activity"""
        activity = ActivityLog(
            id=str(uuid.uuid4()),
            user_id=self.current_user.id if self.current_user else "system",
            timestamp=datetime.now(),
            activity_type=activity_type,
            description=description,
            data=data or {}
        )
        self.activity_log.append(activity)

    def _generate_share_link(self):
        """Generate shareable session link"""
        base_url = "https://your-app.com/collaborate"
        share_link = f"{base_url}?session={self.session_id}"

        st.code(share_link)
        st.success("Share this link with collaborators to join the session!")

    def _send_collaboration_invite(self, email: str, role: SessionRole):
        """Send collaboration invitation"""
        # In a real implementation, this would send an actual email
        invite_data = {
            "session_id": self.session_id,
            "inviter": self.current_user.name,
            "role": role.value,
            "timestamp": datetime.now().isoformat()
        }

        # Mock invitation sending
        st.session_state[f"invite_{email}"] = invite_data

    def _filter_activities(self, activity_filter: str, user_filter: str, hours_back: int) -> List[ActivityLog]:
        """Filter activity log based on criteria"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        filtered = []
        for activity in self.activity_log:
            # Time filter
            if activity.timestamp < cutoff_time:
                continue

            # Activity type filter
            if activity_filter != "All" and activity.activity_type.value != activity_filter:
                continue

            # User filter
            if user_filter != "All":
                user = self.users.get(activity.user_id)
                if not user or user.name != user_filter:
                    continue

            filtered.append(activity)

        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)

    def _resolve_annotation(self, annotation_id: str):
        """Mark annotation as resolved"""
        if annotation_id in self.annotations:
            self.annotations[annotation_id].resolved = True

    def _delete_annotation(self, annotation_id: str):
        """Delete annotation"""
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]

    def _add_annotation_reply(self, annotation_id: str, reply_text: str):
        """Add reply to annotation"""
        if annotation_id in self.annotations:
            reply = {
                "id": str(uuid.uuid4()),
                "user_id": self.current_user.id,
                "text": reply_text,
                "timestamp": datetime.now().isoformat()
            }
            self.annotations[annotation_id].replies.append(reply)

    def _resolve_comment(self, comment_id: str):
        """Mark comment as resolved"""
        if comment_id in self.comments:
            self.comments[comment_id].resolved = True

    def _delete_comment(self, comment_id: str):
        """Delete comment"""
        if comment_id in self.comments:
            del self.comments[comment_id]

    def _open_shared_analysis(self, analysis_id: str):
        """Open shared analysis"""
        if analysis_id in self.shared_analyses:
            st.session_state.current_analysis = analysis_id

    def _export_shared_analysis(self, analysis_id: str):
        """Export shared analysis"""
        if analysis_id in self.shared_analyses:
            analysis = self.shared_analyses[analysis_id]
            export_data = {
                "title": analysis.title,
                "description": analysis.description,
                "created_at": analysis.created_at.isoformat(),
                "data": analysis.analysis_data
            }

            st.download_button(
                label="📥 Download Analysis",
                data=json.dumps(export_data, indent=2),
                file_name=f"{analysis.title.replace(' ', '_')}_analysis.json",
                mime="application/json"
            )

    def _share_analysis(self, analysis_id: str, email: str, permission: str):
        """Share analysis with user"""
        if analysis_id in self.shared_analyses:
            analysis = self.shared_analyses[analysis_id]
            analysis.shared_with.append(email)
            analysis.permissions[email] = permission

    def _export_activity_log(self):
        """Export activity log"""
        export_data = []
        for activity in self.activity_log:
            user = self.users.get(activity.user_id)
            export_data.append({
                "timestamp": activity.timestamp.isoformat(),
                "user": user.name if user else "Unknown",
                "activity_type": activity.activity_type.value,
                "description": activity.description,
                "data": activity.data
            })

        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)

        st.download_button(
            label="📥 Download Activity Log",
            data=csv,
            file_name=f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    def _promote_user(self, user_name: str):
        """Promote user role"""
        for user in self.users.values():
            if user.name == user_name:
                if user.role == SessionRole.VIEWER:
                    user.role = SessionRole.COMMENTATOR
                elif user.role == SessionRole.COMMENTATOR:
                    user.role = SessionRole.EDITOR
                elif user.role == SessionRole.EDITOR:
                    user.role = SessionRole.OWNER
                break

    def _demote_user(self, user_name: str):
        """Demote user role"""
        for user in self.users.values():
            if user.name == user_name:
                if user.role == SessionRole.OWNER:
                    user.role = SessionRole.EDITOR
                elif user.role == SessionRole.EDITOR:
                    user.role = SessionRole.COMMENTATOR
                elif user.role == SessionRole.COMMENTATOR:
                    user.role = SessionRole.VIEWER
                break

    def _remove_user(self, user_name: str):
        """Remove user from session"""
        user_id_to_remove = None
        for user_id, user in self.users.items():
            if user.name == user_name:
                user_id_to_remove = user_id
                break

        if user_id_to_remove:
            del self.users[user_id_to_remove]
            self._log_activity(ActivityType.USER_LEFT, f"User {user_name} was removed from session")


# Factory function for creating collaboration manager
def create_collaboration_manager(component_id: str) -> CollaborationManager:
    """Create collaboration manager component"""
    config = ComponentConfig(
        id=component_id,
        title="Real-Time Collaboration",
        description="Advanced collaboration features for shared financial analysis",
        cache_enabled=False,  # Real-time features shouldn't be cached
        auto_refresh=True,
        refresh_interval=5  # Refresh every 5 seconds for real-time updates
    )
    return CollaborationManager(config)