"""
Financial Pattern Recognizer
============================

Advanced pattern recognition for financial statement line items using regex,
keyword matching, and contextual analysis.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of financial patterns"""
    PREFIX = "prefix"
    SUFFIX = "suffix"
    STRUCTURE = "structure"
    KEYWORD = "keyword"
    ABBREVIATION = "abbreviation"


@dataclass
class RecognizedPattern:
    """A recognized financial pattern"""
    pattern_type: PatternType
    pattern_name: str
    confidence: float
    matched_text: str
    position: int


class FinancialPatternRecognizer:
    """
    Recognizes financial patterns in field names to aid classification.

    Uses regex patterns, keyword dictionaries, and structural analysis
    to identify common financial statement patterns.
    """

    def __init__(self):
        """Initialize the pattern recognizer with financial patterns"""
        self._initialize_patterns()
        logger.info("FinancialPatternRecognizer initialized")

    def _initialize_patterns(self):
        """Initialize financial pattern definitions"""
        # Prefix patterns
        self.prefix_patterns = {
            'total': re.compile(r'\btotal\s+', re.IGNORECASE),
            'net': re.compile(r'\bnet\s+', re.IGNORECASE),
            'gross': re.compile(r'\bgross\s+', re.IGNORECASE),
            'operating': re.compile(r'\boperating\s+', re.IGNORECASE),
            'non_operating': re.compile(r'\bnon[-\s]?operating\s+', re.IGNORECASE),
            'accumulated': re.compile(r'\baccumulated\s+', re.IGNORECASE),
            'deferred': re.compile(r'\bdeferred\s+', re.IGNORECASE),
            'prepaid': re.compile(r'\bprepaid\s+', re.IGNORECASE),
        }

        # Suffix patterns
        self.suffix_patterns = {
            'per_share': re.compile(r'\bper\s+share\b', re.IGNORECASE),
            'ratio': re.compile(r'\bratio\b', re.IGNORECASE),
            'yield': re.compile(r'\byield\b', re.IGNORECASE),
            'margin': re.compile(r'\bmargin\b', re.IGNORECASE),
            'rate': re.compile(r'\brate\b', re.IGNORECASE),
            'turnover': re.compile(r'\bturnover\b', re.IGNORECASE),
        }

        # Time period patterns
        self.time_period_patterns = {
            'current': re.compile(r'\bcurrent\b', re.IGNORECASE),
            'long_term': re.compile(r'\blong[-\s]?term\b', re.IGNORECASE),
            'short_term': re.compile(r'\bshort[-\s]?term\b', re.IGNORECASE),
            'annual': re.compile(r'\bannual(?:ly)?\b', re.IGNORECASE),
            'quarterly': re.compile(r'\bquarterly\b', re.IGNORECASE),
            'ltm': re.compile(r'\b(?:ltm|last\s+twelve\s+months)\b', re.IGNORECASE),
        }

        # Common abbreviations
        self.abbreviation_patterns = {
            'ebitda': re.compile(r'\bebitda\b', re.IGNORECASE),
            'ebit': re.compile(r'\bebit\b', re.IGNORECASE),
            'ppe': re.compile(r'\bp[&p]?e\b', re.IGNORECASE),
            'rnd': re.compile(r'\br[&\s]?[nd]\b', re.IGNORECASE),
            'sga': re.compile(r'\bs[&\s]?g[&\s]?a\b', re.IGNORECASE),
            'cogs': re.compile(r'\bcogs\b', re.IGNORECASE),
            'fcf': re.compile(r'\bfcf\b', re.IGNORECASE),
            'ocf': re.compile(r'\bocf\b', re.IGNORECASE),
            'capex': re.compile(r'\bcapex\b', re.IGNORECASE),
            'roe': re.compile(r'\broe\b', re.IGNORECASE),
            'roa': re.compile(r'\broa\b', re.IGNORECASE),
            'roic': re.compile(r'\broic\b', re.IGNORECASE),
        }

        # Structural patterns (parentheses, brackets, etc.)
        self.structural_patterns = {
            'parenthetical': re.compile(r'\([^)]+\)'),
            'bracketed': re.compile(r'\[[^\]]+\]'),
            'currency': re.compile(r'\$|USD|EUR|GBP|JPY|\¥|£|€'),
            'percentage': re.compile(r'%|\bpercent\b'),
            'numeric': re.compile(r'\d+'),
        }

    def recognize_patterns(self, field_name: str) -> List[RecognizedPattern]:
        """
        Recognize all financial patterns in a field name.

        Args:
            field_name: Field name to analyze

        Returns:
            List of RecognizedPattern objects
        """
        patterns = []

        # Check prefix patterns
        for name, pattern in self.prefix_patterns.items():
            match = pattern.search(field_name)
            if match:
                patterns.append(RecognizedPattern(
                    pattern_type=PatternType.PREFIX,
                    pattern_name=name,
                    confidence=0.9,
                    matched_text=match.group(),
                    position=match.start()
                ))

        # Check suffix patterns
        for name, pattern in self.suffix_patterns.items():
            match = pattern.search(field_name)
            if match:
                patterns.append(RecognizedPattern(
                    pattern_type=PatternType.SUFFIX,
                    pattern_name=name,
                    confidence=0.9,
                    matched_text=match.group(),
                    position=match.start()
                ))

        # Check time period patterns
        for name, pattern in self.time_period_patterns.items():
            match = pattern.search(field_name)
            if match:
                patterns.append(RecognizedPattern(
                    pattern_type=PatternType.KEYWORD,
                    pattern_name=f"time_period_{name}",
                    confidence=0.85,
                    matched_text=match.group(),
                    position=match.start()
                ))

        # Check abbreviations
        for name, pattern in self.abbreviation_patterns.items():
            match = pattern.search(field_name)
            if match:
                patterns.append(RecognizedPattern(
                    pattern_type=PatternType.ABBREVIATION,
                    pattern_name=name,
                    confidence=0.95,
                    matched_text=match.group(),
                    position=match.start()
                ))

        # Check structural patterns
        for name, pattern in self.structural_patterns.items():
            match = pattern.search(field_name)
            if match:
                patterns.append(RecognizedPattern(
                    pattern_type=PatternType.STRUCTURE,
                    pattern_name=name,
                    confidence=0.7,
                    matched_text=match.group(),
                    position=match.start()
                ))

        return patterns

    def extract_core_concept(self, field_name: str) -> Optional[str]:
        """
        Extract the core financial concept from a field name.

        Removes prefixes, suffixes, and modifiers to identify the main concept.

        Args:
            field_name: Field name to analyze

        Returns:
            Core concept string or None
        """
        # Normalize
        normalized = field_name.lower().strip()

        # Remove common prefixes
        for pattern in self.prefix_patterns.values():
            normalized = pattern.sub('', normalized)

        # Remove common suffixes
        for pattern in self.suffix_patterns.values():
            normalized = pattern.sub('', normalized)

        # Remove structural elements
        for pattern in self.structural_patterns.values():
            normalized = pattern.sub('', normalized)

        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        if normalized:
            return normalized

        return None

    def is_aggregate_field(self, field_name: str) -> bool:
        """Check if field represents an aggregate (total, sum, etc.)"""
        aggregate_keywords = ['total', 'sum', 'aggregate', 'combined', 'consolidated']
        normalized = field_name.lower()
        return any(kw in normalized for kw in aggregate_keywords)

    def is_derived_field(self, field_name: str) -> bool:
        """Check if field represents a derived/calculated value"""
        derived_keywords = [
            'ratio', 'margin', 'rate', 'yield', 'return', 'per', 'average',
            'change', 'growth', 'increase', 'decrease'
        ]
        normalized = field_name.lower()
        return any(kw in normalized for kw in derived_keywords)
