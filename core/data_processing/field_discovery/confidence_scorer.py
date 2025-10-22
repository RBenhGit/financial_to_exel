"""
Mapping Confidence Scorer
=========================

Calculates confidence scores for field mappings based on multiple factors including
pattern matching, similarity, context, and historical accuracy.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceFactors:
    """Factors contributing to confidence score"""
    pattern_match_score: float  # 0.0 to 1.0
    similarity_score: float  # 0.0 to 1.0
    context_score: float  # 0.0 to 1.0
    historical_accuracy: float  # 0.0 to 1.0
    completeness_score: float  # 0.0 to 1.0
    weights: Dict[str, float]  # Weight for each factor

    @property
    def weighted_score(self) -> float:
        """Calculate weighted confidence score"""
        total_weight = sum(self.weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = (
            self.pattern_match_score * self.weights.get('pattern', 0.25) +
            self.similarity_score * self.weights.get('similarity', 0.30) +
            self.context_score * self.weights.get('context', 0.20) +
            self.historical_accuracy * self.weights.get('historical', 0.15) +
            self.completeness_score * self.weights.get('completeness', 0.10)
        )

        return min(1.0, weighted_sum / total_weight)


class MappingConfidenceScorer:
    """
    Calculates confidence scores for field mappings using multiple factors.

    Combines pattern matching, semantic similarity, contextual analysis,
    and historical learning data to produce accurate confidence scores.
    """

    def __init__(self, default_weights: Optional[Dict[str, float]] = None):
        """
        Initialize the confidence scorer.

        Args:
            default_weights: Optional custom weights for confidence factors
        """
        self.default_weights = default_weights or {
            'pattern': 0.25,
            'similarity': 0.30,
            'context': 0.20,
            'historical': 0.15,
            'completeness': 0.10
        }

        logger.info("MappingConfidenceScorer initialized")

    def calculate_confidence(
        self,
        field_name: str,
        suggested_mapping: str,
        patterns_matched: List[str],
        similar_fields: List[Tuple[str, float]],
        category_confidence: float = 0.0,
        historical_data: Optional[Dict[str, float]] = None
    ) -> ConfidenceFactors:
        """
        Calculate comprehensive confidence score for a field mapping.

        Args:
            field_name: Original field name
            suggested_mapping: Suggested standard field name
            patterns_matched: List of patterns found in field name
            similar_fields: List of (field_name, similarity) tuples
            category_confidence: Confidence in category classification
            historical_data: Optional historical accuracy data

        Returns:
            ConfidenceFactors with detailed scoring
        """
        # Calculate pattern match score
        pattern_score = self._calculate_pattern_score(patterns_matched)

        # Calculate similarity score from similar fields
        similarity_score = self._calculate_similarity_score(similar_fields)

        # Calculate context score (category confidence + field structure)
        context_score = self._calculate_context_score(
            field_name, suggested_mapping, category_confidence
        )

        # Calculate historical accuracy score
        historical_score = self._calculate_historical_score(
            suggested_mapping, historical_data
        )

        # Calculate completeness score (data quality)
        completeness_score = self._calculate_completeness_score(
            patterns_matched, similar_fields
        )

        return ConfidenceFactors(
            pattern_match_score=pattern_score,
            similarity_score=similarity_score,
            context_score=context_score,
            historical_accuracy=historical_score,
            completeness_score=completeness_score,
            weights=self.default_weights.copy()
        )

    def _calculate_pattern_score(self, patterns: List[str]) -> float:
        """Calculate score based on pattern matching"""
        if not patterns:
            return 0.3  # Base score even without patterns

        # More patterns = higher confidence
        score = 0.3 + (len(patterns) * 0.15)

        # Cap at 1.0
        return min(1.0, score)

    def _calculate_similarity_score(
        self,
        similar_fields: List[Tuple[str, float]]
    ) -> float:
        """Calculate score based on similarity to known fields"""
        if not similar_fields:
            return 0.0

        # Use best similarity score, with diminishing returns
        best_similarity = similar_fields[0][1]

        # Boost if we have multiple good matches
        if len(similar_fields) >= 2 and similar_fields[1][1] > 0.6:
            return min(1.0, best_similarity + 0.1)

        return best_similarity

    def _calculate_context_score(
        self,
        field_name: str,
        suggested_mapping: str,
        category_confidence: float
    ) -> float:
        """Calculate score based on contextual analysis"""
        score = category_confidence

        # Boost if field name and mapping have similar structure
        field_words = set(field_name.lower().split())
        mapping_words = set(suggested_mapping.lower().split('_'))

        overlap = len(field_words & mapping_words)
        if overlap > 0:
            score += overlap * 0.1

        return min(1.0, score)

    def _calculate_historical_score(
        self,
        suggested_mapping: str,
        historical_data: Optional[Dict[str, float]]
    ) -> float:
        """Calculate score based on historical accuracy"""
        if not historical_data or suggested_mapping not in historical_data:
            return 0.5  # Neutral score if no history

        # Use historical accuracy for this mapping
        return historical_data[suggested_mapping]

    def _calculate_completeness_score(
        self,
        patterns: List[str],
        similar_fields: List[Tuple[str, float]]
    ) -> float:
        """Calculate score based on data completeness"""
        score = 0.0

        # Boost for having patterns
        if patterns:
            score += 0.4

        # Boost for having similar fields
        if similar_fields:
            score += 0.4

        # Boost for having high-quality similar fields
        if similar_fields and similar_fields[0][1] > 0.7:
            score += 0.2

        return min(1.0, score)

    def adjust_confidence_with_feedback(
        self,
        original_confidence: ConfidenceFactors,
        was_correct: bool,
        learning_rate: float = 0.1
    ) -> ConfidenceFactors:
        """
        Adjust confidence scoring based on validation feedback.

        Args:
            original_confidence: Original confidence factors
            was_correct: Whether the mapping was correct
            learning_rate: How much to adjust (0.0 to 1.0)

        Returns:
            Adjusted ConfidenceFactors
        """
        adjustment = learning_rate if was_correct else -learning_rate

        # Adjust each factor
        return ConfidenceFactors(
            pattern_match_score=self._clamp(
                original_confidence.pattern_match_score + adjustment, 0.0, 1.0
            ),
            similarity_score=self._clamp(
                original_confidence.similarity_score + adjustment, 0.0, 1.0
            ),
            context_score=self._clamp(
                original_confidence.context_score + adjustment, 0.0, 1.0
            ),
            historical_accuracy=self._clamp(
                original_confidence.historical_accuracy + adjustment, 0.0, 1.0
            ),
            completeness_score=original_confidence.completeness_score,
            weights=original_confidence.weights
        )

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))

    def get_confidence_category(self, confidence: float) -> str:
        """
        Get human-readable confidence category.

        Args:
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Confidence category string
        """
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.7:
            return "High"
        elif confidence >= 0.5:
            return "Medium"
        elif confidence >= 0.3:
            return "Low"
        else:
            return "Very Low"
