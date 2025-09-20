"""
ML Integration Module
====================

Integration layer between ML components and existing financial analysis framework.
Provides seamless integration points and workflow coordination.

Classes
-------
MLIntegrationManager
    Central coordinator for ML integration

FinancialMLPipeline
    End-to-end ML pipeline for financial analysis

MLWorkflowOrchestrator
    Workflow coordination and management
"""

from .integration_manager import MLIntegrationManager
from .financial_ml_pipeline import FinancialMLPipeline
from .workflow_orchestrator import MLWorkflowOrchestrator

__all__ = [
    'MLIntegrationManager',
    'FinancialMLPipeline',
    'MLWorkflowOrchestrator'
]