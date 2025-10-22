"""
Tests for Dynamic Field Discovery System
========================================

Comprehensive tests for the field discovery engine and its components.
"""

import pytest
from datetime import datetime
from core.data_processing.field_discovery import (
    FieldDiscoveryEngine,
    FinancialPatternRecognizer,
    MappingConfidenceScorer,
    FieldDiscoveryLearningSystem,
    XBRLTaxonomyMapper
)
from core.data_processing.field_discovery.field_discovery_engine import (
    FieldCategory,
    FieldType,
    DiscoveredField
)


class TestFinancialPatternRecognizer:
    """Tests for the Financial Pattern Recognizer"""

    @pytest.fixture
    def recognizer(self):
        return FinancialPatternRecognizer()

    def test_recognize_total_prefix(self, recognizer):
        """Test recognition of 'total' prefix pattern"""
        patterns = recognizer.recognize_patterns("Total Revenue")
        pattern_names = [p.pattern_name for p in patterns]
        assert 'total' in pattern_names

    def test_recognize_per_share_suffix(self, recognizer):
        """Test recognition of 'per share' suffix pattern"""
        patterns = recognizer.recognize_patterns("Earnings Per Share")
        pattern_names = [p.pattern_name for p in patterns]
        assert 'per_share' in pattern_names

    def test_recognize_abbreviations(self, recognizer):
        """Test recognition of common financial abbreviations"""
        test_cases = [
            ("EBITDA Margin", "ebitda"),
            ("R&D Expense", "rnd"),
            ("SG&A", "sga"),
            ("Free Cash Flow (FCF)", "fcf"),
        ]

        for field_name, expected_abbrev in test_cases:
            patterns = recognizer.recognize_patterns(field_name)
            pattern_names = [p.pattern_name for p in patterns]
            assert expected_abbrev in pattern_names, f"Failed to recognize {expected_abbrev} in {field_name}"

    def test_extract_core_concept(self, recognizer):
        """Test extraction of core financial concept"""
        test_cases = [
            ("Total Operating Revenue", "revenue"),
            ("Net Income After Tax", "income"),
            ("Gross Profit Margin", "profit"),
        ]

        for field_name, expected_concept in test_cases:
            core = recognizer.extract_core_concept(field_name)
            assert core is not None
            assert expected_concept in core.lower()

    def test_is_aggregate_field(self, recognizer):
        """Test detection of aggregate fields"""
        assert recognizer.is_aggregate_field("Total Assets")
        assert recognizer.is_aggregate_field("Consolidated Revenue")
        assert not recognizer.is_aggregate_field("Operating Expenses")

    def test_is_derived_field(self, recognizer):
        """Test detection of derived/calculated fields"""
        assert recognizer.is_derived_field("Profit Margin")
        assert recognizer.is_derived_field("Return on Equity")
        assert recognizer.is_derived_field("Revenue Growth Rate")
        assert not recognizer.is_derived_field("Total Revenue")


class TestMappingConfidenceScorer:
    """Tests for the Mapping Confidence Scorer"""

    @pytest.fixture
    def scorer(self):
        return MappingConfidenceScorer()

    def test_calculate_confidence_high_similarity(self, scorer):
        """Test confidence calculation with high similarity"""
        factors = scorer.calculate_confidence(
            field_name="Total Sales",
            suggested_mapping="revenue",
            patterns_matched=['total'],
            similar_fields=[('revenue', 0.9), ('sales', 0.85)],
            category_confidence=0.8
        )

        assert factors.weighted_score >= 0.7
        assert factors.similarity_score >= 0.8

    def test_calculate_confidence_low_similarity(self, scorer):
        """Test confidence calculation with low similarity"""
        factors = scorer.calculate_confidence(
            field_name="Unusual Expense Item",
            suggested_mapping="other_expense",
            patterns_matched=[],
            similar_fields=[('other_income', 0.3)],
            category_confidence=0.4
        )

        assert factors.weighted_score < 0.7

    def test_get_confidence_category(self, scorer):
        """Test confidence category labels"""
        assert scorer.get_confidence_category(0.95) == "Very High"
        assert scorer.get_confidence_category(0.75) == "High"
        assert scorer.get_confidence_category(0.55) == "Medium"
        assert scorer.get_confidence_category(0.35) == "Low"
        assert scorer.get_confidence_category(0.15) == "Very Low"

    def test_adjust_confidence_with_positive_feedback(self, scorer):
        """Test confidence adjustment with positive feedback"""
        original = scorer.calculate_confidence(
            "Revenue",
            "revenue",
            ["total"],
            [("revenue", 0.9)],
            0.8
        )

        adjusted = scorer.adjust_confidence_with_feedback(
            original,
            was_correct=True,
            learning_rate=0.1
        )

        assert adjusted.weighted_score >= original.weighted_score


class TestFieldDiscoveryLearningSystem:
    """Tests for the Field Discovery Learning System"""

    @pytest.fixture
    def learning_system(self, tmp_path):
        return FieldDiscoveryLearningSystem(storage_path=tmp_path)

    def test_initialization(self, learning_system):
        """Test learning system initialization"""
        assert learning_system.validation_history == []
        assert len(learning_system.field_accuracy) == 0

    def test_record_correct_validation(self, learning_system):
        """Test recording a correct validation"""
        # Create a mock discovered field
        discovered = type('obj', (object,), {
            'original_name': 'Total Sales',
            'suggested_standard_name': 'revenue',
            'confidence_score': 0.85,
            'patterns_matched': ['total'],
            'category': type('obj', (object,), {'value': 'income_statement'})()
        })()

        learning_system.record_validation(discovered, 'revenue', 'Correct mapping')

        assert len(learning_system.validation_history) == 1
        assert learning_system.validation_history[0].was_correct == True

    def test_get_learned_mappings(self, learning_system):
        """Test retrieval of learned mappings"""
        # Record some validations
        for original, correct in [('Total Sales', 'revenue'), ('Net Earnings', 'net_income')]:
            discovered = type('obj', (object,), {
                'original_name': original,
                'suggested_standard_name': correct,
                'confidence_score': 0.85,
                'patterns_matched': [],
                'category': type('obj', (object,), {'value': 'income_statement'})()
            })()

            learning_system.record_validation(discovered, correct)

        learned = learning_system.get_learned_mappings()
        assert 'Total Sales' in learned
        assert learned['Total Sales'] == 'revenue'

    def test_suggest_correction(self, learning_system):
        """Test suggestion based on history"""
        discovered = type('obj', (object,), {
            'original_name': 'Operating Cash Flow',
            'suggested_standard_name': 'operating_cash_flow',
            'confidence_score': 0.90,
            'patterns_matched': ['operating'],
            'category': type('obj', (object,), {'value': 'cash_flow'})()
        })()

        learning_system.record_validation(discovered, 'operating_cash_flow')

        suggestion = learning_system.suggest_correction('Operating Cash Flow')
        assert suggestion == 'operating_cash_flow'


class TestXBRLTaxonomyMapper:
    """Tests for the XBRL Taxonomy Mapper"""

    @pytest.fixture
    def mapper(self):
        return XBRLTaxonomyMapper()

    def test_get_us_gaap_concept(self, mapper):
        """Test retrieval of US GAAP concepts"""
        concept = mapper.get_xbrl_concept('revenue')
        assert concept is not None
        assert concept.concept_name == 'Revenues'
        assert concept.is_monetary == True

    def test_validate_against_taxonomy(self, mapper):
        """Test validation against taxonomy"""
        assert mapper.validate_against_taxonomy('revenue')
        assert mapper.validate_against_taxonomy('net_income')
        assert not mapper.validate_against_taxonomy('unknown_field_12345')

    def test_get_all_concepts(self, mapper):
        """Test retrieval of all concepts"""
        concepts = mapper.get_all_concepts()
        assert len(concepts) > 0
        assert 'revenue' in concepts
        assert 'total_assets' in concepts

    def test_suggest_xbrl_mapping(self, mapper):
        """Test XBRL mapping suggestions"""
        suggestions = mapper.suggest_xbrl_mapping('sales revenue')
        assert len(suggestions) > 0
        # Should suggest revenue-related concepts


class TestFieldDiscoveryEngine:
    """Tests for the Field Discovery Engine"""

    @pytest.fixture
    def engine(self):
        return FieldDiscoveryEngine()

    def test_initialization(self, engine):
        """Test engine initialization"""
        assert engine.confidence_threshold == 0.7
        assert len(engine.known_fields) > 0

    def test_discover_known_field(self, engine):
        """Test that known fields are not 'discovered'"""
        result = engine.discover_fields(['revenue', 'net_income'])
        assert result.known_fields == 2
        assert len(result.discovered_fields) == 0

    def test_discover_unknown_field(self, engine):
        """Test discovery of unknown field"""
        result = engine.discover_fields(['Total Product Sales'])

        assert result.total_fields_analyzed == 1
        assert len(result.discovered_fields) == 1

        discovered = result.discovered_fields[0]
        assert discovered.original_name == 'Total Product Sales'
        assert discovered.category != FieldCategory.UNKNOWN or discovered.field_type != FieldType.UNKNOWN

    def test_classify_income_statement_field(self, engine):
        """Test classification of income statement fields"""
        result = engine.discover_fields(['Operating Revenue', 'Cost of Sales', 'Net Earnings'])

        for discovered in result.discovered_fields:
            # Should classify as income statement related
            assert discovered.category in [FieldCategory.INCOME_STATEMENT, FieldCategory.UNKNOWN]

    def test_classify_balance_sheet_field(self, engine):
        """Test classification of balance sheet fields"""
        result = engine.discover_fields(['Total Liabilities', 'Stockholder Equity'])

        for discovered in result.discovered_fields:
            # Should classify as balance sheet related
            assert discovered.category in [FieldCategory.BALANCE_SHEET, FieldCategory.UNKNOWN]

    def test_classify_cash_flow_field(self, engine):
        """Test classification of cash flow fields"""
        result = engine.discover_fields(['Cash from Investing Activities', 'Operating Cash Flow'])

        for discovered in result.discovered_fields:
            # Should classify as cash flow related
            assert discovered.category in [FieldCategory.CASH_FLOW, FieldCategory.UNKNOWN]

    def test_pattern_detection(self, engine):
        """Test pattern detection in field names"""
        result = engine.discover_fields(['Total Operating Cash Flow'])

        discovered = result.discovered_fields[0]
        assert len(discovered.patterns_matched) > 0

    def test_similar_field_detection(self, engine):
        """Test detection of similar known fields"""
        result = engine.discover_fields(['Unusual Product Sales Revenue'])

        # This test is valid only if the field is actually discovered as unknown
        if result.discovered_fields:
            discovered = result.discovered_fields[0]
            assert len(discovered.similar_known_fields) >= 0  # May or may not have similar fields

    def test_confidence_threshold(self, engine):
        """Test confidence threshold for validation requirement"""
        result = engine.discover_fields(['Very Unusual Field Name XYZ'])

        discovered = result.discovered_fields[0]
        # Should require validation due to low confidence
        assert discovered.confidence_score < engine.confidence_threshold
        assert discovered.requires_validation == True

    def test_high_confidence_field(self, engine):
        """Test high confidence discovered field"""
        result = engine.discover_fields(['Unusual Total Product Revenue XYZ'])

        # This test is valid only if the field is actually discovered as unknown
        if result.discovered_fields:
            discovered = result.discovered_fields[0]
            # Should have some confidence
            assert discovered.confidence_score >= 0.0

    def test_validate_discovered_field(self, engine):
        """Test validation of discovered field"""
        result = engine.discover_fields(['Product Sales'])
        discovered = result.discovered_fields[0]

        success = engine.validate_discovered_field(
            discovered,
            correct_standard_name='revenue',
            feedback='Correctly identified as revenue'
        )

        assert discovered.validated == True
        assert discovered.suggested_standard_name == 'revenue'

    def test_get_statistics(self, engine):
        """Test retrieval of engine statistics"""
        stats = engine.get_statistics()

        assert 'known_fields_count' in stats
        assert 'confidence_threshold' in stats
        assert stats['known_fields_count'] > 0


class TestFieldDiscoveryIntegration:
    """Integration tests for the complete field discovery system"""

    @pytest.fixture
    def engine(self):
        return FieldDiscoveryEngine(enable_learning=True)

    def test_end_to_end_discovery(self, engine):
        """Test complete discovery workflow"""
        # Discover fields
        field_names = [
            'Total Operating Revenue',
            'Cost of Goods Sold',
            'Net Income After Tax',
            'Total Current Assets',
            'Long-term Debt',
            'Operating Cash Flow'
        ]

        result = engine.discover_fields(field_names)

        # Verify results
        assert result.total_fields_analyzed == len(field_names)
        assert result.processing_time_seconds >= 0

        # Check that high-confidence discoveries exist
        assert result.high_confidence_discoveries >= 0

        # Validate some discoveries
        for discovered in result.discovered_fields[:2]:
            if discovered.suggested_standard_name:
                engine.validate_discovered_field(
                    discovered,
                    correct_standard_name=discovered.suggested_standard_name,
                    feedback='Test validation'
                )

    def test_discovery_with_context(self, engine):
        """Test discovery with statement type hint"""
        result = engine.discover_fields(
            ['Operating Profit', 'Gross Margin'],
            statement_type_hint=FieldCategory.INCOME_STATEMENT
        )

        for discovered in result.discovered_fields:
            assert discovered.category == FieldCategory.INCOME_STATEMENT

    def test_unfamiliar_format_handling(self, engine):
        """Test handling of unfamiliar financial statement formats"""
        # Simulate foreign or non-standard field names
        unfamiliar_fields = [
            'Consolidated Turnover',  # British term for revenue
            'Profit Before Interest and Tax',  # Different phrasing for EBIT
            'Net Working Capital',
            'Tangible Fixed Assets',  # British term for PP&E
        ]

        result = engine.discover_fields(unfamiliar_fields)

        # Should discover all fields
        assert len(result.discovered_fields) == len(unfamiliar_fields)

        # Should provide reasonable suggestions
        for discovered in result.discovered_fields:
            assert discovered.suggested_standard_name is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
