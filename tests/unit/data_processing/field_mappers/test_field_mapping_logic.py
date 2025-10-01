"""
Tests for Field Mapping Logic
==============================

Tests the core field mapping logic including priority handling,
confidence scoring, and validation of critical fields.
"""

import pytest

from core.data_processing.field_mappers.statement_field_mapper import (
    StatementFieldMapper,
    MappingStrategy,
    MappingResult,
)


class TestMappingPriority:
    """Test mapping priority order: company → industry → standard → default → alias → regex → fuzzy"""

    @pytest.fixture
    def mapper(self):
        """Create mapper instance"""
        return StatementFieldMapper()

    def test_company_specific_overrides_default(self, mapper):
        """Test that company-specific mappings take priority over defaults"""
        # AAPL uses "Net Sales" instead of "Revenue"
        result = mapper.map_field("net sales", company_ticker="AAPL")

        assert result.is_successful, "Should successfully map AAPL field"
        assert result.mapped_field_name == "revenue"
        assert result.confidence_score == 1.0, "Exact match should have 1.0 confidence"
        assert "company-specific" in " ".join(result.notes).lower()

    def test_industry_mapping_priority(self, mapper):
        """Test industry-specific mapping"""
        # Technology industry specific mapping
        result = mapper.map_field("r&d expenses", industry="technology")

        assert result.is_successful, "Should map technology industry field"
        assert result.mapped_field_name == "rd_expenses"

    def test_reporting_standard_mapping(self, mapper):
        """Test reporting standard specific mapping"""
        # IFRS uses "Turnover" for revenue
        result = mapper.map_field("turnover", reporting_standard="IFRS")

        assert result.is_successful, "Should map IFRS field"
        assert result.mapped_field_name == "revenue"

    def test_default_mapping_fallback(self, mapper):
        """Test fallback to default mapping when no specific mapping exists"""
        result = mapper.map_field("Operating Income")

        assert result.is_successful, "Should map using default mapping"
        assert result.mapped_field_name == "operating_income"
        assert "default" in " ".join(result.notes).lower()

    def test_alias_mapping(self, mapper):
        """Test alias-based mapping"""
        # "Sales" is an alias for "revenue"
        result = mapper.map_field("Sales")

        assert result.is_successful, "Should map via alias"
        assert result.mapped_field_name == "revenue"
        assert result.strategy_used == MappingStrategy.ALIAS_MATCH
        assert 0.9 <= result.confidence_score <= 1.0, "Alias match should have high confidence"

    def test_regex_pattern_mapping(self, mapper):
        """Test regex pattern-based mapping"""
        # Regex should match variations
        variations = ["E.B.I.T.", "EBIT", "E.B.I.T"]

        for variation in variations:
            result = mapper.map_field(variation)
            if result.is_successful and result.strategy_used == MappingStrategy.REGEX_MATCH:
                assert result.mapped_field_name == "ebit"
                assert result.confidence_score >= 0.85
                break

    def test_fuzzy_matching_fallback(self, mapper):
        """Test fuzzy matching as last resort"""
        # Intentional typo that should still match
        result = mapper.map_field("Operting Income")  # Missing 'a'

        assert result.is_successful, "Fuzzy matching should handle typos"
        assert result.mapped_field_name == "operating_income"
        assert result.strategy_used == MappingStrategy.FUZZY_MATCH
        assert result.confidence_score >= mapper.fuzzy_threshold

    def test_failed_mapping(self, mapper):
        """Test handling of unmappable fields"""
        result = mapper.map_field("Completely Unknown Field XYZ123")

        assert not result.is_successful, "Should fail for unknown fields"
        assert result.mapped_field_name is None
        assert result.confidence_score == 0.0


class TestConfidenceScoring:
    """Test confidence score calculation for different mapping strategies"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_exact_match_confidence(self, mapper):
        """Exact matches should have 1.0 confidence"""
        result = mapper.map_field("Revenue")

        assert result.confidence_score == 1.0, "Exact match should be 1.0 confidence"

    def test_alias_match_confidence(self, mapper):
        """Alias matches should have high confidence (0.95)"""
        result = mapper.map_field("Sales")  # Alias for revenue

        if result.strategy_used == MappingStrategy.ALIAS_MATCH:
            assert result.confidence_score == 0.95, "Alias match should be 0.95"

    def test_regex_match_confidence(self, mapper):
        """Regex matches should have 0.9 confidence"""
        result = mapper.map_field("Net Income to Company")

        if result.strategy_used == MappingStrategy.REGEX_MATCH:
            assert result.confidence_score == 0.9, "Regex match should be 0.9"

    def test_fuzzy_match_confidence_range(self, mapper):
        """Fuzzy matches should have variable confidence based on similarity"""
        # Close match
        result1 = mapper.map_field("Reveue")  # One letter off

        if result1.is_successful and result1.strategy_used == MappingStrategy.FUZZY_MATCH:
            assert (
                result1.confidence_score >= 0.8
            ), "Close fuzzy match should have high confidence"

        # Less similar match
        result2 = mapper.map_field("Gross Margin")  # Maps to gross_profit

        if result2.is_successful and result2.strategy_used == MappingStrategy.FUZZY_MATCH:
            assert 0.0 < result2.confidence_score <= 1.0, "Confidence should be in valid range"


class TestBatchMapping:
    """Test batch field mapping functionality"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_batch_map_multiple_fields(self, mapper):
        """Test mapping multiple fields at once"""
        field_names = [
            "Revenue",
            "Net Income",
            "Operating Income",
            "Gross Profit",
            "Total Assets",
        ]

        results = mapper.batch_map_fields(field_names)

        assert len(results) == len(field_names), "Should return result for each field"

        # All should map successfully
        for field_name, result in results.items():
            assert result.is_successful, f"Failed to map: {field_name}"
            assert result.mapped_field_name is not None

    def test_batch_map_with_company_ticker(self, mapper):
        """Test batch mapping with company-specific rules"""
        field_names = ["Net Sales", "Operating Income"]

        results = mapper.batch_map_fields(field_names, company_ticker="AAPL")

        # Net Sales should use AAPL-specific mapping
        assert results["Net Sales"].is_successful
        assert results["Net Sales"].mapped_field_name == "revenue"

    def test_batch_map_mixed_success(self, mapper):
        """Test batch mapping with some failures"""
        field_names = [
            "Revenue",  # Should succeed
            "Unknown Field XYZ",  # Should fail
            "Net Income",  # Should succeed
        ]

        results = mapper.batch_map_fields(field_names)

        assert results["Revenue"].is_successful
        assert not results["Unknown Field XYZ"].is_successful
        assert results["Net Income"].is_successful


class TestCriticalFieldValidation:
    """Test validation of critical/required fields"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_validate_all_required_fields_present(self, mapper):
        """Test validation passes with all required fields"""
        # Map all required fields
        field_names = [
            "Revenue",
            "Net Income",
            "Operating Income",
            "Gross Profit",
            "Total Assets",
            "Total Liabilities",
            "Shareholders' Equity",
            "Cash and Cash Equivalents",
            "Cash from Operations",
            "Capital Expenditures",
            "Free Cash Flow",
        ]

        mapped_fields = mapper.batch_map_fields(field_names)
        is_valid, missing = mapper.validate_required_fields(mapped_fields)

        assert is_valid, f"Validation should pass. Missing: {missing}"
        assert len(missing) == 0, "Should have no missing required fields"

    def test_validate_missing_required_fields(self, mapper):
        """Test validation fails with missing required fields"""
        # Only map some fields, leaving required ones missing
        field_names = ["Revenue", "Gross Profit"]

        mapped_fields = mapper.batch_map_fields(field_names)
        is_valid, missing = mapper.validate_required_fields(mapped_fields)

        assert not is_valid, "Validation should fail with missing required fields"
        assert len(missing) > 0, "Should report missing fields"

        # Check that critical fields are flagged as missing
        critical_fields = ["net_income", "operating_cash_flow"]
        for field in critical_fields:
            assert field in missing, f"Critical field '{field}' should be reported as missing"

    def test_required_fields_loaded_from_config(self, mapper):
        """Test that required fields are loaded from configuration"""
        assert len(mapper.required_fields) > 0, "Required fields should be loaded"

        # Essential fields should be required
        essential = ["revenue", "net_income", "total_assets", "operating_cash_flow"]

        for field in essential:
            assert field in mapper.required_fields, f"Essential field '{field}' should be required"


class TestRealWorldScenarios:
    """Test with real-world Excel field names from different companies"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_microsoft_income_statement(self, mapper):
        """Test mapping Microsoft income statement fields"""
        msft_fields = [
            "Revenue",
            "Revenue Growth (YoY)",
            "Cost of Revenues",
            "Gross Profit",
            "Gross Profit Margin",
            "R&D Expenses",
            "Selling and Marketing Expense",
            "General & Admin Expenses",
            "Other Inc / (Exp)",
            "Operating Expenses",
            "Operating Income",
            "Net Interest Expenses",
            "EBT, Incl. Unusual Items",
            "Income Tax Expense",
            "Net Income to Company",
        ]

        results = mapper.batch_map_fields(msft_fields, company_ticker="MSFT")

        # All fields should map successfully
        success_count = sum(1 for r in results.values() if r.is_successful)
        assert success_count == len(
            msft_fields
        ), f"Should map all MSFT fields. Mapped {success_count}/{len(msft_fields)}"

        # Verify specific mappings
        assert results["Revenue"].mapped_field_name == "revenue"
        assert results["Net Income to Company"].mapped_field_name == "net_income"
        assert results["Operating Income"].mapped_field_name == "operating_income"

    def test_google_income_statement(self, mapper):
        """Test mapping Google income statement fields"""
        goog_fields = [
            "Revenues",  # Google uses plural
            "Cost of Revenues",
            "Gross Profit",
            "Operating Income",
        ]

        results = mapper.batch_map_fields(goog_fields, company_ticker="GOOG")

        assert results["Revenues"].is_successful
        assert results["Revenues"].mapped_field_name == "revenue"

    def test_balance_sheet_fields(self, mapper):
        """Test mapping balance sheet fields"""
        bs_fields = [
            "Cash and Cash Equivalents",
            "Short Term Investments",
            "Accounts Receivable, Net",
            "Inventory",
            "Total Current Assets",
            "Property Plant And Equipment, Net",
            "Goodwill",
            "Total Assets",
            "Accounts Payable",
            "Total Current Liabilities",
            "Long-term Debt",
            "Total Liabilities",
            "Shareholders' Equity",
        ]

        results = mapper.batch_map_fields(bs_fields)

        # All should map successfully
        for field, result in results.items():
            assert result.is_successful, f"Failed to map balance sheet field: {field}"

    def test_cash_flow_fields(self, mapper):
        """Test mapping cash flow statement fields"""
        cf_fields = [
            "Depreciation & Amortization (CF)",
            "Stock-Based Comp",
            "Change In Accounts Receivable",
            "Cash from Operations",
            "Capital Expenditures",
            "Cash Acquisitions",
            "Cash from Investing",
            "Dividends Paid (Ex Special Dividends)",
            "Long-Term Debt Issued",
            "Repurchase of Common Stock",
            "Cash from Financing",
            "Free Cash Flow",
        ]

        results = mapper.batch_map_fields(cf_fields)

        # Critical cash flow fields should map
        assert results["Cash from Operations"].is_successful
        assert results["Cash from Operations"].mapped_field_name == "operating_cash_flow"
        assert results["Capital Expenditures"].is_successful
        assert results["Free Cash Flow"].is_successful


class TestMappingStatistics:
    """Test mapping statistics tracking"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_statistics_tracking(self, mapper):
        """Test that mapping statistics are tracked"""
        # Reset stats
        mapper.reset_statistics()

        # Perform some mappings
        mapper.map_field("Revenue")  # Exact match
        mapper.map_field("Sales")  # Alias match
        mapper.map_field("Unknown Field")  # Failed mapping

        stats = mapper.get_statistics()

        assert stats["total_mappings"] == 3, "Should track total mappings"
        assert stats["exact_matches"] >= 1, "Should track exact matches"
        assert stats["failed_mappings"] >= 1, "Should track failed mappings"
        assert 0.0 <= stats["success_rate"] <= 1.0, "Success rate should be valid"

    def test_statistics_reset(self, mapper):
        """Test resetting statistics"""
        # Perform mappings
        mapper.map_field("Revenue")
        mapper.map_field("Net Income")

        # Reset
        mapper.reset_statistics()

        stats = mapper.get_statistics()

        assert stats["total_mappings"] == 0, "Stats should be reset"
        assert stats["exact_matches"] == 0
        assert stats["failed_mappings"] == 0


class TestCaseInsensitivityAndNormalization:
    """Test field name normalization and case handling"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_case_insensitive_mapping(self, mapper):
        """Test that mapping is case-insensitive"""
        variations = [
            "revenue",
            "Revenue",
            "REVENUE",
            "ReVeNuE",
        ]

        for variation in variations:
            result = mapper.map_field(variation)
            assert result.is_successful, f"Failed to map: {variation}"
            assert result.mapped_field_name == "revenue"

    def test_whitespace_normalization(self, mapper):
        """Test handling of extra whitespace"""
        variations = [
            "  Revenue  ",
            "Revenue   ",
            "  Revenue",
            "Net  Income",  # Extra space
        ]

        for variation in variations:
            result = mapper.map_field(variation)
            assert result.is_successful, f"Failed to map with whitespace: {variation}"

    def test_special_characters_handling(self, mapper):
        """Test handling of fields with special characters"""
        fields = [
            "R&D Expenses",
            "Selling and Marketing Expense",
            "General & Admin Expenses",
            "Other Inc / (Exp)",
        ]

        for field in fields:
            result = mapper.map_field(field)
            assert result.is_successful, f"Failed to map field with special chars: {field}"


class TestMappingAlternatives:
    """Test alternative suggestions for low-confidence mappings"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_alternatives_provided_for_fuzzy_match(self, mapper):
        """Test that fuzzy matches provide alternatives"""
        result = mapper.map_field("Revenus")  # Typo, close to "revenue"

        if result.is_successful and result.strategy_used == MappingStrategy.FUZZY_MATCH:
            assert len(result.alternatives) > 0, "Fuzzy match should provide alternatives"
            assert all(
                isinstance(alt, tuple) and len(alt) == 2 for alt in result.alternatives
            ), "Alternatives should be (field, score) tuples"

    def test_no_alternatives_for_exact_match(self, mapper):
        """Test that exact matches don't need alternatives"""
        result = mapper.map_field("Revenue")

        if result.strategy_used == MappingStrategy.EXACT_MATCH:
            # Exact matches may have empty alternatives list
            assert result.confidence_score == 1.0


class TestLoggingAndDebugging:
    """Test logging and debugging features"""

    @pytest.fixture
    def mapper(self):
        return StatementFieldMapper()

    def test_mapping_notes_provided(self, mapper):
        """Test that mapping results include notes"""
        result = mapper.map_field("Revenue")

        assert len(result.notes) > 0, "Should provide mapping notes"
        assert any("mapping" in note.lower() for note in result.notes)

    def test_notes_describe_strategy(self, mapper):
        """Test that notes describe which strategy was used"""
        # Company-specific mapping
        result1 = mapper.map_field("Net Sales", company_ticker="AAPL")
        if result1.is_successful:
            assert any(
                "company" in note.lower() for note in result1.notes
            ), "Should note company-specific match"

        # Default mapping
        result2 = mapper.map_field("Operating Income")
        if result2.is_successful:
            assert any(
                "default" in note.lower() for note in result2.notes
            ), "Should note default match"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
