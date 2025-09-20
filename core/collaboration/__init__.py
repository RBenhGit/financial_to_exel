"""
Collaborative Features Module

This module provides collaborative functionality for the financial analysis application,
including analysis sharing, annotations, and real-time collaboration capabilities.
"""

from .analysis_sharing import AnalysisShareManager, SharedAnalysis
from .annotations import AnnotationManager, AnalysisAnnotation
from .collaboration_manager import CollaborationManager
from .shared_workspaces import WorkspaceManager, SharedWorkspace

__all__ = [
    'AnalysisShareManager',
    'SharedAnalysis',
    'AnnotationManager',
    'AnalysisAnnotation',
    'CollaborationManager',
    'WorkspaceManager',
    'SharedWorkspace'
]