"""
Dynamic Field Discovery System
===============================

Intelligent system for discovering and mapping new financial statement fields automatically
using NLP, pattern recognition, and machine learning techniques.

This module provides:
- NLP-based field discovery using financial domain knowledge
- Pattern recognition for financial statement line items
- Automatic classification by statement category
- Confidence scoring for field mappings
- User validation workflow for uncertain mappings
- Learning system to improve accuracy over time
- XBRL taxonomy integration
"""

from .field_discovery_engine import FieldDiscoveryEngine
from .pattern_recognizer import FinancialPatternRecognizer
from .confidence_scorer import MappingConfidenceScorer
from .learning_system import FieldDiscoveryLearningSystem
from .xbrl_taxonomy import XBRLTaxonomyMapper

__all__ = [
    'FieldDiscoveryEngine',
    'FinancialPatternRecognizer',
    'MappingConfidenceScorer',
    'FieldDiscoveryLearningSystem',
    'XBRLTaxonomyMapper',
]
