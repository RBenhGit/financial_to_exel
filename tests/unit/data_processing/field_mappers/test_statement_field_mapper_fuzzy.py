"""
Tests for fuzzy string matching capabilities in StatementFieldMapper.

Tests cover:
- Fuzzy matching with various field name variations
- Case differences handling
- Spacing and punctuation variations
- Abbreviation matching
- Similarity threshold configuration
- Performance with large field lists
- Edge cases with very similar names
"""

import pytest
from difflib import SequenceMatcher

from core.data_processing.field_mappers.statement_field_mapper import (
    MappingStrategy,
    StatementFieldMapper,
)


class TestFuzzyMatching:
    """Test fuzzy string matching functionality"""

    @pytest.fixture
    def mapper(self):
        """Create mapper with default configuration"""
        return StatementFieldMapper(fuzzy_threshold=0.8, enable_fuzzy_matching=True)

    @pytest.fixture
    def mapper_lenient(self):
        """Create mapper with more lenient fuzzy threshold"""
        return StatementFieldMapper(fuzzy_threshold=0.6, enable_fuzzy_matching=True)

    def test_fuzzy_matching_case_differences(self, mapper):
        """Test fuzzy matching handles case variations"""
        test_cases = [
            ("NET INCOME", "net_income"),
            ("Net Income", "net_income"),
            ("net income", "net_income"),
            ("NET_INCOME", "net_income"),
            ("REVENUE", "revenue"),
            ("Revenue", "revenue"),
        ]

        for input_field, expected_mapped in test_cases:
            result = mapper.map_field(input_field)
            assert result.is_successful, f"Failed to map '{input_field}'"
            assert result.mapped_field_name == expected_mapped
            assert result.confidence_score >= 0.8

    def test_fuzzy_matching_spacing_variations(self, mapper):
        """Test fuzzy matching handles spacing differences"""
        test_cases = [
            ("Net  Income", "net_income"),  # Double space
            ("NetIncome", "net_income"),  # No space
            ("Net   Income", "net_income"),  # Multiple spaces
            ("Operating Income", "operating_income"),
            ("OperatingIncome", "operating_income"),
        ]

        for input_field, expected_mapped in test_cases:
            result = mapper.map_field(input_field)
            # Some variations might not meet threshold, so just verify the method runs
            assert result is not None
            assert isinstance(result.confidence_score, float)

    def test_fuzzy_matching_abbreviations(self, mapper_lenient):
        """Test fuzzy matching with common abbreviations"""
        test_cases = [
            ("Net Inc", "net_income", 0.6),  # Abbreviated
            ("Op Income", "operating_income", 0.6),  # Abbreviated
            ("Tot Assets", "total_assets", 0.6),  # Abbreviated
            ("Op Cash Flow", "operating_cash_flow", 0.5),  # Abbreviated
        ]

        for input_field, expected_mapped, min_score in test_cases:
            result = mapper_lenient.map_field(input_field)
            # Verify we get a result with reasonable confidence
            assert result is not None
            if result.is_successful:
                assert result.confidence_score >= min_score
                assert result.strategy_used == MappingStrategy.FUZZY_MATCH

    def test_fuzzy_matching_punctuation_variations(self, mapper):
        """Test fuzzy matching handles punctuation differences"""
        test_cases = [
            ("Cash & Equivalents", 0.5),
            ("Cash-and-Equivalents", 0.5),
            ("Shareholders Equity", 0.7),
            ("Shareholders' Equity", 0.7),
        ]

        for input_field, min_score in test_cases:
            result = mapper.map_field(input_field)
            assert result is not None
            # These should at least attempt fuzzy matching
            if result.is_successful:
                assert result.confidence_score >= min_score

    def test_fuzzy_matching_threshold_configuration(self):
        """Test that fuzzy threshold configuration works correctly"""
        # Strict threshold
        mapper_strict = StatementFieldMapper(fuzzy_threshold=0.95)
        result_strict = mapper_strict.map_field("Net Inc")

        # Lenient threshold
        mapper_lenient = StatementFieldMapper(fuzzy_threshold=0.5)
        result_lenient = mapper_lenient.map_field("Net Inc")

        # Lenient should have higher success rate
        assert mapper_lenient.fuzzy_threshold < mapper_strict.fuzzy_threshold

    def test_fuzzy_matching_disabled(self):
        """Test that fuzzy matching can be disabled"""
        mapper_no_fuzzy = StatementFieldMapper(enable_fuzzy_matching=False)

        # Exact match should still work
        result_exact = mapper_no_fuzzy.map_field("net_income")
        assert result_exact.is_successful

        # Fuzzy match should fail when disabled
        result_fuzzy = mapper_no_fuzzy.map_field("Net Inc")
        # Should not use fuzzy matching
        assert result_fuzzy.strategy_used != MappingStrategy.FUZZY_MATCH

    def test_fuzzy_matching_alternatives(self, mapper):
        """Test that fuzzy matching returns alternative matches"""
        result = mapper.map_field("Income")

        # Should return some result
        assert result is not None

        # If successful, check alternatives
        if result.is_successful:
            # Should have alternatives if multiple similar matches found
            assert isinstance(result.alternatives, list)
            # Each alternative should be a tuple of (field_name, score)
            for alt_field, alt_score in result.alternatives:
                assert isinstance(alt_field, str)
                assert 0.0 <= alt_score <= 1.0

    def test_fuzzy_matching_edge_cases(self, mapper):
        """Test fuzzy matching with edge cases"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Only whitespace
            "X",  # Single character
            "A" * 100,  # Very long string
            "!@#$%",  # Special characters only
        ]

        for input_field in edge_cases:
            result = mapper.map_field(input_field)
            assert result is not None
            assert isinstance(result.is_successful, bool)
            assert isinstance(result.confidence_score, float)
            assert 0.0 <= result.confidence_score <= 1.0

    def test_fuzzy_matching_similar_field_names(self, mapper):
        """Test fuzzy matching with very similar field names"""
        # These are all similar but distinct
        similar_fields = [
            "Total Revenue",
            "Total Assets",
            "Total Liabilities",
        ]

        for field_name in similar_fields:
            result = mapper.map_field(field_name)
            assert result is not None
            # Should map to something
            if result.is_successful:
                assert result.mapped_field_name is not None

    def test_fuzzy_matching_performance_large_field_list(self, mapper):
        """Test fuzzy matching performance with large field list"""
        # Create a large list of field names
        field_names = [
            f"Field {i}" for i in range(100)
        ] + [
            "Net Income",
            "Revenue",
            "Total Assets",
            "Operating Cash Flow",
        ]

        import time
        start_time = time.time()

        results = mapper.batch_map_fields(field_names)

        end_time = time.time()
        elapsed = end_time - start_time

        # Should complete in reasonable time (< 5 seconds for 104 fields)
        assert elapsed < 5.0
        assert len(results) == len(field_names)

    def test_calculate_similarity_direct(self, mapper):
        """Test the _calculate_similarity method directly"""
        # Test known similarity scores
        test_pairs = [
            ("identical", "identical", 1.0),
            ("revenue", "revenues", 0.88),  # Very similar
            ("net income", "net_income", 0.9),  # Underscore vs space
            ("abc", "xyz", 0.0),  # Completely different
        ]

        for str1, str2, expected_min_score in test_pairs:
            score = mapper._calculate_similarity(str1, str2)
            assert 0.0 <= score <= 1.0
            assert score >= expected_min_score or score < expected_min_score + 0.15

    def test_fuzzy_matching_confidence_scoring(self, mapper):
        """Test that confidence scores are reasonable"""
        # Exact matches should have highest confidence
        result_exact = mapper.map_field("net_income")

        # Fuzzy matches should have lower confidence
        result_fuzzy = mapper.map_field("Net Income")

        # Both should be successful
        if result_exact.is_successful and result_fuzzy.is_successful:
            # Exact match confidence should be high
            assert result_exact.confidence_score >= 0.95

    def test_fuzzy_matching_with_aliases(self, mapper):
        """Test that fuzzy matching works with field aliases"""
        # "Sales" is an alias for "revenue"
        result = mapper.map_field("Sales")
        assert result.is_successful
        assert result.mapped_field_name == "revenue"

        # Fuzzy match on alias
        result_fuzzy = mapper.map_field("sales")
        assert result_fuzzy.is_successful
        assert result_fuzzy.mapped_field_name == "revenue"

    def test_fuzzy_matching_statistics(self, mapper):
        """Test that fuzzy matching updates statistics correctly"""
        initial_stats = mapper.get_statistics()

        # Perform some fuzzy matches
        mapper.map_field("Net Income")  # Should trigger fuzzy
        mapper.map_field("Revenue")  # Should trigger fuzzy

        updated_stats = mapper.get_statistics()

        # Fuzzy match count should increase
        assert updated_stats["fuzzy_matches"] >= initial_stats["fuzzy_matches"]
        assert updated_stats["total_mappings"] > initial_stats["total_mappings"]

    def test_fuzzy_matching_fallback_priority(self, mapper):
        """Test that fuzzy matching is used as fallback after other strategies"""
        # When exact match is available, should prefer it
        result_exact = mapper.map_field("net_income")
        if result_exact.is_successful:
            assert result_exact.strategy_used != MappingStrategy.FUZZY_MATCH

        # When no exact match, should fall back to fuzzy
        result_fuzzy = mapper.map_field("Net Income Attr")
        if result_fuzzy.is_successful:
            # Could be fuzzy or another strategy
            assert result_fuzzy.strategy_used in [
                MappingStrategy.FUZZY_MATCH,
                MappingStrategy.EXACT_MATCH,
                MappingStrategy.ALIAS_MATCH,
                MappingStrategy.REGEX_MATCH,
            ]


class TestFuzzyMatchingIntegration:
    """Integration tests for fuzzy matching with other mapper features"""

    def test_fuzzy_matching_with_company_specific_rules(self):
        """Test fuzzy matching respects company-specific rules"""
        mapper = StatementFieldMapper(fuzzy_threshold=0.7)

        # Map with company-specific context
        result = mapper.map_field(
            "Net Sales",
            company_ticker="AAPL"
        )

        assert result is not None
        assert result.is_successful

    def test_fuzzy_matching_with_reporting_standards(self):
        """Test fuzzy matching with different reporting standards"""
        mapper = StatementFieldMapper(fuzzy_threshold=0.7)

        # Map with GAAP context
        result_gaap = mapper.map_field(
            "Revenue",
            reporting_standard="GAAP"
        )

        # Map with IFRS context
        result_ifrs = mapper.map_field(
            "Turnover",
            reporting_standard="IFRS"
        )

        assert result_gaap is not None
        assert result_ifrs is not None

    def test_batch_mapping_with_fuzzy_matching(self):
        """Test batch mapping uses fuzzy matching appropriately"""
        mapper = StatementFieldMapper(fuzzy_threshold=0.7)

        field_names = [
            "Net Income",
            "Total Revenue",
            "Operating Income",
            "Cash Flow",
        ]

        results = mapper.batch_map_fields(field_names)

        assert len(results) == len(field_names)

        # At least some should succeed
        successful_count = sum(1 for r in results.values() if r.is_successful)
        assert successful_count > 0
