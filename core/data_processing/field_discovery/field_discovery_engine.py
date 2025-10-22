"""
Field Discovery Engine
======================

Core engine for discovering and mapping new financial statement fields using NLP and pattern recognition.

This module provides intelligent field discovery capabilities that can:
- Identify unknown financial line items
- Map them to standardized field names
- Learn from user feedback
- Improve accuracy over time
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FieldCategory(Enum):
    """Financial statement categories for field classification"""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    RATIOS = "ratios"
    MARKET_DATA = "market_data"
    UNKNOWN = "unknown"


class FieldType(Enum):
    """Types of financial fields"""
    REVENUE = "revenue"
    EXPENSE = "expense"
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    CASH_FLOW = "cash_flow"
    RATIO = "ratio"
    METRIC = "metric"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredField:
    """Represents a newly discovered financial field"""
    original_name: str
    normalized_name: str
    suggested_standard_name: Optional[str]
    category: FieldCategory
    field_type: FieldType
    confidence_score: float  # 0.0 to 1.0
    reasoning: List[str]
    patterns_matched: List[str]
    similar_known_fields: List[Tuple[str, float]]  # (field_name, similarity)
    requires_validation: bool
    discovered_at: datetime = field(default_factory=datetime.now)
    validated: bool = False
    validation_feedback: Optional[str] = None


@dataclass
class FieldDiscoveryResult:
    """Result of field discovery process"""
    total_fields_analyzed: int
    known_fields: int
    discovered_fields: List[DiscoveredField]
    high_confidence_discoveries: int
    requires_validation_count: int
    processing_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)


class FieldDiscoveryEngine:
    """
    Intelligent engine for discovering and mapping new financial statement fields.

    Uses NLP, pattern recognition, and machine learning to identify unknown fields
    and suggest appropriate mappings to standardized field names.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        enable_learning: bool = True,
        use_xbrl_taxonomy: bool = True
    ):
        """
        Initialize the Field Discovery Engine.

        Args:
            confidence_threshold: Minimum confidence for automatic mapping
            enable_learning: Whether to enable learning from feedback
            use_xbrl_taxonomy: Whether to use XBRL taxonomy for validation
        """
        self.confidence_threshold = confidence_threshold
        self.enable_learning = enable_learning
        self.use_xbrl_taxonomy = use_xbrl_taxonomy

        # Initialize components (will be implemented in subsequent files)
        self.pattern_recognizer = None  # Will be FinancialPatternRecognizer()
        self.confidence_scorer = None  # Will be MappingConfidenceScorer()
        self.learning_system = None  # Will be FieldDiscoveryLearningSystem()
        self.xbrl_mapper = None  # Will be XBRLTaxonomyMapper()

        # Known field mappings (from existing registry)
        self.known_fields: Set[str] = set()
        self._load_known_fields()

        # Financial domain keywords for pattern matching
        self._initialize_domain_knowledge()

        logger.info("FieldDiscoveryEngine initialized")

    def _load_known_fields(self):
        """Load known fields from existing field mapping registry"""
        try:
            from ..field_mapping_registry import get_field_mapping_registry

            registry = get_field_mapping_registry()

            # Get all standard field names from all sources
            for source in ['yfinance', 'fmp', 'excel', 'alpha_vantage', 'polygon']:
                self.known_fields.update(registry.get_all_standard_fields(source))

            logger.info(f"Loaded {len(self.known_fields)} known standard field names")
        except Exception as e:
            logger.warning(f"Could not load known fields from registry: {e}")
            # Initialize with basic set of known fields
            self.known_fields = {
                'revenue', 'cost_of_revenue', 'gross_profit', 'operating_income',
                'net_income', 'total_assets', 'total_liabilities', 'total_stockholders_equity',
                'operating_cash_flow', 'capital_expenditures', 'free_cash_flow'
            }

    def _initialize_domain_knowledge(self):
        """Initialize financial domain knowledge for pattern recognition"""
        self.revenue_keywords = {
            'revenue', 'sales', 'income', 'receipts', 'turnover', 'proceeds',
            'earnings', 'fees', 'subscription', 'licensing', 'service', 'product'
        }

        self.expense_keywords = {
            'expense', 'cost', 'expenditure', 'spending', 'outlay', 'charge',
            'fee', 'payment', 'compensation', 'salary', 'wage', 'rent', 'lease',
            'depreciation', 'amortization', 'interest', 'tax'
        }

        self.asset_keywords = {
            'asset', 'cash', 'receivable', 'inventory', 'investment', 'property',
            'equipment', 'plant', 'land', 'building', 'goodwill', 'intangible',
            'securities', 'holdings'
        }

        self.liability_keywords = {
            'liability', 'debt', 'payable', 'obligation', 'loan', 'bonds',
            'notes', 'mortgage', 'lease', 'deferred', 'accrued'
        }

        self.equity_keywords = {
            'equity', 'stock', 'shares', 'capital', 'retained', 'earnings',
            'surplus', 'reserves'
        }

        self.cash_flow_keywords = {
            'cash', 'flow', 'operating', 'investing', 'financing', 'capex',
            'dividend', 'repurchase', 'issuance', 'proceeds', 'payment'
        }

        self.statement_indicators = {
            FieldCategory.INCOME_STATEMENT: {
                'revenue', 'sales', 'income', 'profit', 'expense', 'cost',
                'ebit', 'ebitda', 'earnings', 'margin'
            },
            FieldCategory.BALANCE_SHEET: {
                'asset', 'liability', 'equity', 'cash', 'receivable',
                'payable', 'inventory', 'debt', 'capital'
            },
            FieldCategory.CASH_FLOW: {
                'cash', 'flow', 'operating', 'investing', 'financing',
                'capex', 'depreciation', 'working'
            }
        }

    def discover_fields(
        self,
        field_names: List[str],
        data_values: Optional[Dict[str, Any]] = None,
        statement_type_hint: Optional[FieldCategory] = None
    ) -> FieldDiscoveryResult:
        """
        Discover and classify unknown financial fields.

        Args:
            field_names: List of field names to analyze
            data_values: Optional dictionary of field values for context
            statement_type_hint: Optional hint about statement type

        Returns:
            FieldDiscoveryResult with discovered fields and metadata
        """
        start_time = datetime.now()

        discovered_fields: List[DiscoveredField] = []
        known_count = 0

        for field_name in field_names:
            # Normalize the field name
            normalized = self._normalize_field_name(field_name)

            # Check if this is a known field
            if self._is_known_field(normalized):
                known_count += 1
                continue

            # Discover this new field
            discovered = self._discover_single_field(
                field_name,
                normalized,
                data_values.get(field_name) if data_values else None,
                statement_type_hint
            )

            discovered_fields.append(discovered)

        # Calculate statistics
        high_confidence = sum(
            1 for f in discovered_fields
            if f.confidence_score >= self.confidence_threshold
        )

        requires_validation = sum(
            1 for f in discovered_fields
            if f.requires_validation
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        result = FieldDiscoveryResult(
            total_fields_analyzed=len(field_names),
            known_fields=known_count,
            discovered_fields=discovered_fields,
            high_confidence_discoveries=high_confidence,
            requires_validation_count=requires_validation,
            processing_time_seconds=processing_time
        )

        logger.info(
            f"Field discovery complete: {len(field_names)} analyzed, "
            f"{known_count} known, {len(discovered_fields)} discovered, "
            f"{high_confidence} high confidence"
        )

        return result

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for consistent processing"""
        if not field_name:
            return ""

        # Convert to lowercase
        normalized = field_name.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove special characters but keep spaces and underscores
        normalized = re.sub(r'[^\w\s]', '', normalized)

        return normalized

    def _is_known_field(self, normalized_name: str) -> bool:
        """Check if a field is already known"""
        # Direct match
        if normalized_name in self.known_fields:
            return True

        # Check with underscores replaced by spaces
        space_variant = normalized_name.replace('_', ' ')
        if space_variant in self.known_fields:
            return True

        # Check if any known field is very similar (exact substring)
        for known in self.known_fields:
            if known in normalized_name or normalized_name in known:
                if len(normalized_name) > 5:  # Avoid false positives with short names
                    return True

        return False

    def _discover_single_field(
        self,
        original_name: str,
        normalized_name: str,
        value: Optional[Any],
        statement_hint: Optional[FieldCategory]
    ) -> DiscoveredField:
        """
        Discover and classify a single unknown field.

        Args:
            original_name: Original field name
            normalized_name: Normalized field name
            value: Optional field value for context
            statement_hint: Optional statement category hint

        Returns:
            DiscoveredField with classification and confidence
        """
        reasoning = []
        patterns_matched = []

        # Classify statement category
        category = self._classify_statement_category(normalized_name, statement_hint, reasoning)

        # Classify field type
        field_type = self._classify_field_type(normalized_name, value, reasoning)

        # Detect patterns
        detected_patterns = self._detect_patterns(normalized_name)
        patterns_matched.extend(detected_patterns)

        # Find similar known fields
        similar_fields = self._find_similar_fields(normalized_name)

        # Suggest standard name
        suggested_name = self._suggest_standard_name(
            normalized_name, category, field_type, similar_fields
        )

        # Calculate confidence score
        confidence = self._calculate_confidence(
            normalized_name, category, field_type,
            len(patterns_matched), similar_fields
        )

        # Determine if validation is required
        requires_validation = confidence < self.confidence_threshold

        return DiscoveredField(
            original_name=original_name,
            normalized_name=normalized_name,
            suggested_standard_name=suggested_name,
            category=category,
            field_type=field_type,
            confidence_score=confidence,
            reasoning=reasoning,
            patterns_matched=patterns_matched,
            similar_known_fields=similar_fields,
            requires_validation=requires_validation
        )

    def _classify_statement_category(
        self,
        normalized_name: str,
        hint: Optional[FieldCategory],
        reasoning: List[str]
    ) -> FieldCategory:
        """Classify which financial statement this field belongs to"""
        if hint and hint != FieldCategory.UNKNOWN:
            reasoning.append(f"Category hint provided: {hint.value}")
            return hint

        # Score each category
        scores = {}
        for category, keywords in self.statement_indicators.items():
            score = sum(1 for kw in keywords if kw in normalized_name)
            scores[category] = score

        # Get best match
        if max(scores.values()) > 0:
            best_category = max(scores, key=scores.get)
            reasoning.append(
                f"Classified as {best_category.value} based on keyword matching "
                f"(score: {scores[best_category]})"
            )
            return best_category

        reasoning.append("Could not determine category from keywords")
        return FieldCategory.UNKNOWN

    def _classify_field_type(
        self,
        normalized_name: str,
        value: Optional[Any],
        reasoning: List[str]
    ) -> FieldType:
        """Classify the type of financial field"""
        # Check keywords for each type
        if any(kw in normalized_name for kw in self.revenue_keywords):
            reasoning.append("Classified as REVENUE based on keywords")
            return FieldType.REVENUE

        if any(kw in normalized_name for kw in self.expense_keywords):
            reasoning.append("Classified as EXPENSE based on keywords")
            return FieldType.EXPENSE

        if any(kw in normalized_name for kw in self.asset_keywords):
            reasoning.append("Classified as ASSET based on keywords")
            return FieldType.ASSET

        if any(kw in normalized_name for kw in self.liability_keywords):
            reasoning.append("Classified as LIABILITY based on keywords")
            return FieldType.LIABILITY

        if any(kw in normalized_name for kw in self.equity_keywords):
            reasoning.append("Classified as EQUITY based on keywords")
            return FieldType.EQUITY

        if any(kw in normalized_name for kw in self.cash_flow_keywords):
            reasoning.append("Classified as CASH_FLOW based on keywords")
            return FieldType.CASH_FLOW

        # Check for ratio indicators
        if any(indicator in normalized_name for indicator in ['ratio', 'margin', 'return', 'per']):
            reasoning.append("Classified as RATIO based on indicators")
            return FieldType.RATIO

        reasoning.append("Could not determine specific field type")
        return FieldType.UNKNOWN

    def _detect_patterns(self, normalized_name: str) -> List[str]:
        """Detect financial patterns in field name"""
        patterns = []

        # Common financial patterns
        if re.search(r'\btotal\b', normalized_name):
            patterns.append("TOTAL_PREFIX")

        if re.search(r'\bnet\b', normalized_name):
            patterns.append("NET_PREFIX")

        if re.search(r'\bgross\b', normalized_name):
            patterns.append("GROSS_PREFIX")

        if re.search(r'\boperating\b', normalized_name):
            patterns.append("OPERATING_PREFIX")

        if re.search(r'\bcurrent\b', normalized_name):
            patterns.append("CURRENT_PREFIX")

        if re.search(r'\blong.?term\b', normalized_name):
            patterns.append("LONG_TERM")

        if re.search(r'\bshort.?term\b', normalized_name):
            patterns.append("SHORT_TERM")

        if re.search(r'\bper\s+share\b', normalized_name):
            patterns.append("PER_SHARE")

        if re.search(r'\byield\b', normalized_name):
            patterns.append("YIELD_SUFFIX")

        return patterns

    def _find_similar_fields(self, normalized_name: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Find similar known fields using fuzzy matching"""
        from difflib import SequenceMatcher

        similarities = []

        for known_field in self.known_fields:
            # Calculate similarity ratio
            ratio = SequenceMatcher(None, normalized_name, known_field).ratio()

            if ratio > 0.5:  # Only include reasonably similar fields
                similarities.append((known_field, ratio))

        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]

    def _suggest_standard_name(
        self,
        normalized_name: str,
        category: FieldCategory,
        field_type: FieldType,
        similar_fields: List[Tuple[str, float]]
    ) -> Optional[str]:
        """Suggest a standard field name based on discovered information"""
        # If we have a highly similar field, suggest it
        if similar_fields and similar_fields[0][1] > 0.8:
            return similar_fields[0][0]

        # Build a suggested name from components
        components = []

        # Add type prefix if relevant
        if field_type != FieldType.UNKNOWN:
            # Extract relevant parts
            words = normalized_name.split()

            # Keep common prefixes
            if words and words[0] in ['total', 'net', 'gross', 'operating']:
                components.append(words[0])

            # Add field type
            if field_type == FieldType.REVENUE:
                components.append('revenue')
            elif field_type == FieldType.EXPENSE:
                components.append('expense')
            elif field_type == FieldType.ASSET:
                components.append('assets')
            elif field_type == FieldType.LIABILITY:
                components.append('liabilities')
            elif field_type == FieldType.EQUITY:
                components.append('equity')
            elif field_type == FieldType.CASH_FLOW:
                components.append('cash_flow')
            elif field_type == FieldType.RATIO:
                components.append('ratio')

        if components:
            suggested = '_'.join(components)
            return suggested

        # Fallback: use normalized name with underscores
        return normalized_name.replace(' ', '_')

    def _calculate_confidence(
        self,
        normalized_name: str,
        category: FieldCategory,
        field_type: FieldType,
        patterns_count: int,
        similar_fields: List[Tuple[str, float]]
    ) -> float:
        """Calculate confidence score for the discovered field"""
        confidence = 0.0

        # Base confidence from category classification
        if category != FieldCategory.UNKNOWN:
            confidence += 0.2

        # Confidence from field type classification
        if field_type != FieldType.UNKNOWN:
            confidence += 0.2

        # Confidence from pattern matching
        confidence += min(0.2, patterns_count * 0.05)

        # Confidence from similar fields
        if similar_fields:
            best_similarity = similar_fields[0][1]
            confidence += best_similarity * 0.4  # Up to 0.4 based on best match

        return min(1.0, confidence)  # Cap at 1.0

    def validate_discovered_field(
        self,
        discovered_field: DiscoveredField,
        correct_standard_name: str,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Validate a discovered field with user feedback.

        Args:
            discovered_field: The discovered field to validate
            correct_standard_name: The correct standard field name
            feedback: Optional feedback message

        Returns:
            True if learning system updated successfully
        """
        discovered_field.validated = True
        discovered_field.validation_feedback = feedback
        discovered_field.suggested_standard_name = correct_standard_name

        # Update learning system if enabled
        if self.enable_learning and self.learning_system:
            try:
                self.learning_system.record_validation(
                    discovered_field, correct_standard_name, feedback
                )
                logger.info(
                    f"Recorded validation: '{discovered_field.original_name}' -> "
                    f"'{correct_standard_name}'"
                )
                return True
            except Exception as e:
                logger.error(f"Failed to record validation in learning system: {e}")
                return False

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery engine statistics"""
        stats = {
            'known_fields_count': len(self.known_fields),
            'confidence_threshold': self.confidence_threshold,
            'learning_enabled': self.enable_learning,
            'xbrl_taxonomy_enabled': self.use_xbrl_taxonomy
        }

        if self.learning_system:
            stats['learning_stats'] = self.learning_system.get_statistics()

        return stats
