"""
Analysis Annotation System

Provides functionality for adding annotations, comments, and collaborative notes
to financial analyses.
"""

import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class AnnotationType(Enum):
    """Types of annotations"""
    COMMENT = "comment"
    HIGHLIGHT = "highlight"
    NOTE = "note"
    QUESTION = "question"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    BOOKMARK = "bookmark"


class AnnotationScope(Enum):
    """Scope of annotation within analysis"""
    GENERAL = "general"
    METRIC = "metric"
    CHART = "chart"
    ASSUMPTION = "assumption"
    RESULT = "result"
    DATA_POINT = "data_point"


@dataclass
class AnnotationTarget:
    """Target location for annotation within analysis"""

    scope: AnnotationScope
    target_id: Optional[str] = None  # ID of specific metric, chart, etc.
    coordinates: Optional[Dict[str, float]] = None  # For visual annotations
    data_reference: Optional[Dict[str, Any]] = None  # Reference to specific data

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationTarget':
        if 'scope' in data and isinstance(data['scope'], str):
            data['scope'] = AnnotationScope(data['scope'])
        return cls(**data)


@dataclass
class AnnotationReply:
    """Reply to an annotation"""

    reply_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_edited: bool = False

    def __post_init__(self):
        if not self.reply_id:
            self.reply_id = str(uuid.uuid4())

    def edit_content(self, new_content: str):
        """Edit reply content"""
        self.content = new_content
        self.edited_at = datetime.now()
        self.is_edited = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationReply':
        # Handle datetime fields
        for field_name in ['created_at', 'edited_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except:
                    data[field_name] = None
        return cls(**data)


@dataclass
class AnalysisAnnotation:
    """Main annotation data structure"""

    # Required fields (no defaults)
    annotation_id: str
    analysis_id: str
    user_id: str
    username: str
    annotation_type: AnnotationType
    title: str
    content: str
    target: AnnotationTarget

    # Optional fields (with defaults)
    share_id: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Visibility and permissions
    is_private: bool = False
    visible_to_users: List[str] = field(default_factory=list)

    # Collaboration features
    replies: List[AnnotationReply] = field(default_factory=list)
    likes: List[str] = field(default_factory=list)  # User IDs who liked
    tags: List[str] = field(default_factory=list)

    # Additional data
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize annotation ID if not provided"""
        if not self.annotation_id:
            self.annotation_id = str(uuid.uuid4())

    def add_reply(self, user_id: str, username: str, content: str) -> AnnotationReply:
        """Add a reply to the annotation"""
        reply = AnnotationReply(
            reply_id=str(uuid.uuid4()),
            user_id=user_id,
            username=username,
            content=content,
            created_at=datetime.now()
        )

        self.replies.append(reply)
        self.updated_at = datetime.now()
        return reply

    def edit_reply(self, reply_id: str, new_content: str, user_id: str) -> bool:
        """Edit a reply (only by original author)"""
        for reply in self.replies:
            if reply.reply_id == reply_id and reply.user_id == user_id:
                reply.edit_content(new_content)
                self.updated_at = datetime.now()
                return True
        return False

    def delete_reply(self, reply_id: str, user_id: str) -> bool:
        """Delete a reply (only by original author)"""
        for i, reply in enumerate(self.replies):
            if reply.reply_id == reply_id and reply.user_id == user_id:
                del self.replies[i]
                self.updated_at = datetime.now()
                return True
        return False

    def toggle_like(self, user_id: str) -> bool:
        """Toggle like status for user"""
        if user_id in self.likes:
            self.likes.remove(user_id)
            return False
        else:
            self.likes.append(user_id)
            return True

    def resolve(self, resolved_by: str):
        """Mark annotation as resolved"""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()

    def unresolve(self):
        """Mark annotation as unresolved"""
        self.is_resolved = False
        self.resolved_by = None
        self.resolved_at = None
        self.updated_at = datetime.now()

    def edit_content(self, new_title: str, new_content: str):
        """Edit annotation content"""
        self.title = new_title
        self.content = new_content
        self.updated_at = datetime.now()

    def add_tag(self, tag: str):
        """Add a tag to the annotation"""
        tag = tag.lower().strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the annotation"""
        tag = tag.lower().strip()
        if tag in self.tags:
            self.tags.remove(tag)

    def can_view(self, user_id: str) -> bool:
        """Check if user can view this annotation"""
        if not self.is_private:
            return True

        return (user_id == self.user_id or
                user_id in self.visible_to_users)

    def can_edit(self, user_id: str) -> bool:
        """Check if user can edit this annotation"""
        return user_id == self.user_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisAnnotation':
        """Create AnalysisAnnotation from dictionary"""
        # Handle datetime fields
        for field_name in ['created_at', 'updated_at', 'resolved_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except:
                    data[field_name] = None

        # Handle enum fields
        if 'annotation_type' in data and isinstance(data['annotation_type'], str):
            data['annotation_type'] = AnnotationType(data['annotation_type'])

        # Handle target
        if 'target' in data and isinstance(data['target'], dict):
            data['target'] = AnnotationTarget.from_dict(data['target'])

        # Handle replies
        if 'replies' in data and isinstance(data['replies'], list):
            replies = []
            for reply_data in data['replies']:
                replies.append(AnnotationReply.from_dict(reply_data))
            data['replies'] = replies

        return cls(**data)


class AnnotationManager:
    """Manager for annotation operations"""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize annotation manager"""
        self.storage_path = storage_path or Path("data/annotations")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._annotations: Dict[str, AnalysisAnnotation] = {}
        self._analysis_annotations: Dict[str, List[str]] = {}  # analysis_id -> annotation_ids
        self._load_annotations()

    def _load_annotations(self):
        """Load annotations from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    annotation = AnalysisAnnotation.from_dict(data)
                    self._add_annotation_to_memory(annotation)
        except Exception as e:
            logger.error(f"Failed to load annotations: {e}")

    def _add_annotation_to_memory(self, annotation: AnalysisAnnotation):
        """Add annotation to in-memory indexes"""
        self._annotations[annotation.annotation_id] = annotation

        # Add to analysis index
        if annotation.analysis_id not in self._analysis_annotations:
            self._analysis_annotations[annotation.analysis_id] = []

        if annotation.annotation_id not in self._analysis_annotations[annotation.analysis_id]:
            self._analysis_annotations[annotation.analysis_id].append(annotation.annotation_id)

    def _save_annotation(self, annotation: AnalysisAnnotation):
        """Save annotation to storage"""
        try:
            file_path = self.storage_path / f"{annotation.annotation_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(annotation.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save annotation {annotation.annotation_id}: {e}")

    def create_annotation(self,
                         analysis_id: str,
                         user_id: str,
                         username: str,
                         annotation_type: AnnotationType,
                         title: str,
                         content: str,
                         target: AnnotationTarget,
                         share_id: Optional[str] = None,
                         is_private: bool = False,
                         tags: Optional[List[str]] = None) -> AnalysisAnnotation:
        """Create a new annotation"""

        annotation = AnalysisAnnotation(
            annotation_id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            share_id=share_id,
            user_id=user_id,
            username=username,
            annotation_type=annotation_type,
            title=title,
            content=content,
            target=target,
            is_private=is_private,
            tags=tags or []
        )

        self._add_annotation_to_memory(annotation)
        self._save_annotation(annotation)

        logger.info(f"Created annotation {annotation.annotation_id} for analysis {analysis_id}")
        return annotation

    def get_annotation(self, annotation_id: str) -> Optional[AnalysisAnnotation]:
        """Get annotation by ID"""
        return self._annotations.get(annotation_id)

    def get_analysis_annotations(self, analysis_id: str, user_id: Optional[str] = None,
                               include_resolved: bool = True,
                               annotation_types: Optional[List[AnnotationType]] = None) -> List[AnalysisAnnotation]:
        """Get all annotations for an analysis"""
        annotation_ids = self._analysis_annotations.get(analysis_id, [])
        annotations = []

        for annotation_id in annotation_ids:
            annotation = self._annotations.get(annotation_id)

            if not annotation:
                continue

            # Check visibility
            if user_id and not annotation.can_view(user_id):
                continue

            # Filter by resolution status
            if not include_resolved and annotation.is_resolved:
                continue

            # Filter by annotation types
            if annotation_types and annotation.annotation_type not in annotation_types:
                continue

            annotations.append(annotation)

        # Sort by creation date (newest first)
        annotations.sort(key=lambda x: x.created_at, reverse=True)
        return annotations

    def update_annotation(self, annotation_id: str, user_id: str,
                         title: Optional[str] = None,
                         content: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> bool:
        """Update annotation content"""
        annotation = self.get_annotation(annotation_id)

        if not annotation or not annotation.can_edit(user_id):
            return False

        if title is not None and content is not None:
            annotation.edit_content(title, content)

        if tags is not None:
            annotation.tags = tags

        self._save_annotation(annotation)
        return True

    def delete_annotation(self, annotation_id: str, user_id: str) -> bool:
        """Delete annotation (only by author)"""
        annotation = self.get_annotation(annotation_id)

        if not annotation or not annotation.can_edit(user_id):
            return False

        # Remove from memory
        del self._annotations[annotation_id]

        # Remove from analysis index
        if annotation.analysis_id in self._analysis_annotations:
            if annotation_id in self._analysis_annotations[annotation.analysis_id]:
                self._analysis_annotations[annotation.analysis_id].remove(annotation_id)

        # Remove from storage
        try:
            file_path = self.storage_path / f"{annotation_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete annotation file {annotation_id}: {e}")

        logger.info(f"Deleted annotation {annotation_id}")
        return True

    def add_reply(self, annotation_id: str, user_id: str, username: str, content: str) -> Optional[AnnotationReply]:
        """Add reply to annotation"""
        annotation = self.get_annotation(annotation_id)

        if not annotation:
            return None

        reply = annotation.add_reply(user_id, username, content)
        self._save_annotation(annotation)
        return reply

    def resolve_annotation(self, annotation_id: str, user_id: str) -> bool:
        """Resolve annotation"""
        annotation = self.get_annotation(annotation_id)

        if not annotation:
            return False

        annotation.resolve(user_id)
        self._save_annotation(annotation)
        return True

    def unresolve_annotation(self, annotation_id: str, user_id: str) -> bool:
        """Unresolve annotation"""
        annotation = self.get_annotation(annotation_id)

        if not annotation or not annotation.can_edit(user_id):
            return False

        annotation.unresolve()
        self._save_annotation(annotation)
        return True

    def toggle_like(self, annotation_id: str, user_id: str) -> Optional[bool]:
        """Toggle like on annotation"""
        annotation = self.get_annotation(annotation_id)

        if not annotation:
            return None

        is_liked = annotation.toggle_like(user_id)
        self._save_annotation(annotation)
        return is_liked

    def search_annotations(self,
                          query: str,
                          analysis_ids: Optional[List[str]] = None,
                          user_id: Optional[str] = None,
                          annotation_types: Optional[List[AnnotationType]] = None,
                          tags: Optional[List[str]] = None,
                          limit: int = 50) -> List[AnalysisAnnotation]:
        """Search annotations by content"""
        results = []
        query_lower = query.lower()

        for annotation in self._annotations.values():
            # Check visibility
            if user_id and not annotation.can_view(user_id):
                continue

            # Filter by analysis IDs
            if analysis_ids and annotation.analysis_id not in analysis_ids:
                continue

            # Filter by annotation types
            if annotation_types and annotation.annotation_type not in annotation_types:
                continue

            # Filter by tags
            if tags and not any(tag in annotation.tags for tag in tags):
                continue

            # Check content match
            if (query_lower in annotation.title.lower() or
                query_lower in annotation.content.lower() or
                any(query_lower in reply.content.lower() for reply in annotation.replies)):
                results.append(annotation)

                if len(results) >= limit:
                    break

        # Sort by relevance (simple scoring)
        def relevance_score(annotation):
            score = 0
            if query_lower in annotation.title.lower():
                score += 3
            if query_lower in annotation.content.lower():
                score += 2
            score += sum(1 for reply in annotation.replies
                        if query_lower in reply.content.lower())
            return score

        results.sort(key=relevance_score, reverse=True)
        return results

    def get_user_annotations(self, user_id: str, limit: int = 50) -> List[AnalysisAnnotation]:
        """Get annotations created by a user"""
        user_annotations = []

        for annotation in self._annotations.values():
            if annotation.user_id == user_id:
                user_annotations.append(annotation)

                if len(user_annotations) >= limit:
                    break

        user_annotations.sort(key=lambda x: x.created_at, reverse=True)
        return user_annotations

    def get_annotation_statistics(self, analysis_id: Optional[str] = None) -> Dict[str, Any]:
        """Get annotation statistics"""
        annotations = list(self._annotations.values())

        if analysis_id:
            annotation_ids = self._analysis_annotations.get(analysis_id, [])
            annotations = [self._annotations[aid] for aid in annotation_ids
                         if aid in self._annotations]

        total_annotations = len(annotations)
        resolved_annotations = sum(1 for a in annotations if a.is_resolved)
        total_replies = sum(len(a.replies) for a in annotations)
        total_likes = sum(len(a.likes) for a in annotations)

        # Annotation type breakdown
        type_breakdown = {}
        for annotation in annotations:
            annotation_type = annotation.annotation_type.value
            type_breakdown[annotation_type] = type_breakdown.get(annotation_type, 0) + 1

        # Most active users
        user_activity = {}
        for annotation in annotations:
            user_activity[annotation.user_id] = user_activity.get(annotation.user_id, 0) + 1

        return {
            'total_annotations': total_annotations,
            'resolved_annotations': resolved_annotations,
            'unresolved_annotations': total_annotations - resolved_annotations,
            'total_replies': total_replies,
            'total_likes': total_likes,
            'type_breakdown': type_breakdown,
            'most_active_users': sorted(user_activity.items(),
                                      key=lambda x: x[1], reverse=True)[:10]
        }