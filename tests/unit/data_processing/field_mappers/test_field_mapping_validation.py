"""
Unit tests for field mapping validation and integration functionality.

Tests cover:
- validate_mappings method
- mapping quality metrics
- fallback strategies
- integration helpers
- data type validation
"""

import pytest
from typing import Dict, Any
from core.data_processing.field_mappers.statement_field_mapper import (
    StatementFieldMapper,
    MappingResult,
    MappingStrategy,
    FieldMapperIntegrationHelper,
)


@pytest.fixture
def mapper():
    """Create a StatementFieldMapper instance for testing."""
    return StatementFieldMapper(
        config_path=None, fuzzy_threshold=0.8, enable_fuzzy_matching=True
    )


@pytest.fixture
def sample_mapped_fields():
    """Create sample mapping results for testing validation with all required fields."""
    # Config requires: revenue, net_income, operating_income, gross_profit,
    # total_assets, total_liabilities, shareholders_equity, cash_and_equivalents,
    # operating_cash_flow, capital_expenditures, free_cash_flow
    return {
        "Total Revenue": MappingResult(
            input_field_name="Total Revenue",
            mapped_field_name="revenue",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Net Income": MappingResult(
            input_field_name="Net Income",
            mapped_field_name="net_income",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Operating Income": MappingResult(
            input_field_name="Operating Income",
            mapped_field_name="operating_income",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Gross Profit": MappingResult(
            input_field_name="Gross Profit",
            mapped_field_name="gross_profit",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Total Assets": MappingResult(
            input_field_name="Total Assets",
            mapped_field_name="total_assets",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Total Liabilities": MappingResult(
            input_field_name="Total Liabilities",
            mapped_field_name="total_liabilities",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Shareholders Equity": MappingResult(
            input_field_name="Shareholders Equity",
            mapped_field_name="shareholders_equity",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Cash and Equivalents": MappingResult(
            input_field_name="Cash and Equivalents",
            mapped_field_name="cash_and_equivalents",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
        "Cash from Operations": MappingResult(
            input_field_name="Cash from Operations",
            mapped_field_name="operating_cash_flow",
            confidence_score=0.9,
            strategy_used=MappingStrategy.FUZZY_MATCH,
            is_successful=True,
        ),
        "CapEx": MappingResult(
            input_field_name="CapEx",
            mapped_field_name="capital_expenditures",
            confidence_score=1.0,
            strategy_used=MappingStrategy.ALIAS_MATCH,
            is_successful=True,
        ),
        "Free Cash Flow": MappingResult(
            input_field_name="Free Cash Flow",
            mapped_field_name="free_cash_flow",
            confidence_score=1.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=True,
        ),
    }


class TestValidateMappings:
    """Test suite for validate_mappings method."""

    def test_validate_all_required_fields_present(self, mapper, sample_mapped_fields):
        """Test validation passes when all required fields are present."""
        is_valid, report = mapper.validate_mappings(sample_mapped_fields)

        assert is_valid
        assert report["required_fields_status"]["all_present"]
        assert len(report["errors"]) == 0

    def test_validate_missing_required_fields(self, mapper):
        """Test validation fails when required fields are missing."""
        # Only provide revenue, missing other required fields
        mapped_fields = {
            "Total Revenue": MappingResult(
                input_field_name="Total Revenue",
                mapped_field_name="revenue",
                confidence_score=1.0,
                strategy_used=MappingStrategy.EXACT_MATCH,
                is_successful=True,
            )
        }

        is_valid, report = mapper.validate_mappings(mapped_fields)

        assert not is_valid
        assert not report["required_fields_status"]["all_present"]
        assert len(report["required_fields_status"]["missing"]) > 0
        assert len(report["errors"]) > 0

    def test_validate_low_confidence_mappings(self, mapper):
        """Test that low confidence mappings generate warnings."""
        mapped_fields = {
            "Unclear Field": MappingResult(
                input_field_name="Unclear Field",
                mapped_field_name="revenue",
                confidence_score=0.65,  # Below 0.7 threshold
                strategy_used=MappingStrategy.FUZZY_MATCH,
                is_successful=True,
            )
        }

        is_valid, report = mapper.validate_mappings(mapped_fields)

        assert "low_confidence_count" in report["mapping_quality"]
        assert report["mapping_quality"]["low_confidence_count"] > 0
        assert len(report["warnings"]) > 0

    def test_validate_failed_mappings(self, mapper):
        """Test that failed mappings are properly reported."""
        mapped_fields = {
            "Unknown Field": MappingResult(
                input_field_name="Unknown Field",
                mapped_field_name=None,
                confidence_score=0.0,
                strategy_used=MappingStrategy.EXACT_MATCH,
                is_successful=False,
            )
        }

        is_valid, report = mapper.validate_mappings(mapped_fields)

        assert report["mapping_quality"]["failed"] > 0
        assert len(report["warnings"]) > 0

    def test_validate_duplicate_mappings(self, mapper, sample_mapped_fields):
        """Test detection of duplicate mappings."""
        # Add a duplicate mapping to the sample fields
        duplicate_fields = sample_mapped_fields.copy()
        duplicate_fields["Revenue Duplicate"] = MappingResult(
            input_field_name="Revenue Duplicate",
            mapped_field_name="revenue",  # Duplicate of "Total Revenue" -> "revenue"
            confidence_score=0.9,
            strategy_used=MappingStrategy.FUZZY_MATCH,
            is_successful=True,
        )

        is_valid, report = mapper.validate_mappings(duplicate_fields)

        # Should generate a warning about duplicate mappings
        assert any("duplicate" in w.lower() or "multiple" in w.lower() for w in report["warnings"])

    def test_validate_with_data_values(self, mapper, sample_mapped_fields):
        """Test validation with actual data values for type checking."""
        data_values = {
            "revenue": 1000000,
            "net_income": 150000,
            "operating_income": 250000,
            "gross_profit": 400000,
            "total_assets": 5000000,
            "total_liabilities": 2000000,
            "shareholders_equity": 3000000,
            "cash_and_equivalents": 500000,
            "operating_cash_flow": 200000,
            "capital_expenditures": 50000,
            "free_cash_flow": 150000,
        }

        is_valid, report = mapper.validate_mappings(
            sample_mapped_fields, data_values
        )

        assert is_valid
        assert "data_type_validation" in report
        assert report["data_type_validation"]["valid_count"] > 0

    def test_validate_invalid_data_types(self, mapper):
        """Test validation detects invalid data types."""
        mapped_fields = {
            "Revenue": MappingResult(
                input_field_name="Revenue",
                mapped_field_name="revenue",
                confidence_score=1.0,
                strategy_used=MappingStrategy.EXACT_MATCH,
                is_successful=True,
            )
        }

        data_values = {"revenue": "not a number"}  # Invalid type

        is_valid, report = mapper.validate_mappings(mapped_fields, data_values)

        assert not is_valid
        assert len(report["errors"]) > 0
        assert "data_type_validation" in report


class TestMappingQualityMetrics:
    """Test suite for mapping quality metrics."""

    def test_get_mapping_quality_metrics(self, mapper):
        """Test getting comprehensive quality metrics."""
        # Perform some mappings first
        mapper.map_field("revenue")
        mapper.map_field("net income")

        metrics = mapper.get_mapping_quality_metrics()

        assert "statistics" in metrics
        assert "configuration" in metrics
        assert "health" in metrics
        assert "overall_health" in metrics["health"]
        assert "recommendations" in metrics["health"]

    def test_mapper_health_excellent(self, mapper):
        """Test health calculation for excellent performance."""
        # Simulate excellent success rate
        mapper._stats["total_mappings"] = 100
        mapper._stats["exact_matches"] = 96
        mapper._stats["failed_mappings"] = 4

        stats = mapper.get_statistics()
        health = mapper._calculate_mapper_health(stats)

        assert health == "Excellent"

    def test_mapper_health_poor(self, mapper):
        """Test health calculation for poor performance."""
        # Simulate poor success rate
        mapper._stats["total_mappings"] = 100
        mapper._stats["exact_matches"] = 50
        mapper._stats["failed_mappings"] = 50

        stats = mapper.get_statistics()
        health = mapper._calculate_mapper_health(stats)

        assert health == "Poor"

    def test_health_recommendations_generated(self, mapper):
        """Test that health recommendations are generated."""
        # Simulate conditions that should trigger recommendations
        mapper._stats["total_mappings"] = 100
        mapper._stats["exact_matches"] = 40
        mapper._stats["fuzzy_matches"] = 40
        mapper._stats["failed_mappings"] = 20

        stats = mapper.get_statistics()
        recommendations = mapper._generate_health_recommendations(stats)

        assert len(recommendations) > 0


class TestFallbackStrategies:
    """Test suite for fallback value strategies."""

    def test_fallback_fcf_calculation(self, mapper):
        """Test FCF fallback calculation."""
        data = {"operating_cash_flow": 500000, "capital_expenditures": 100000}

        fallback_value = mapper.get_fallback_value("free_cash_flow", data)

        assert fallback_value is not None
        assert fallback_value == 400000  # 500000 - 100000

    def test_fallback_ebitda_calculation(self, mapper):
        """Test EBITDA fallback calculation."""
        data = {
            "net_income": 100000,
            "interest_expense": 10000,
            "income_tax_expense": 20000,
            "depreciation_and_amortization": 15000,
        }

        fallback_value = mapper.get_fallback_value("ebitda", data)

        assert fallback_value is not None
        assert fallback_value == 145000  # Sum of all components

    def test_fallback_enterprise_value_calculation(self, mapper):
        """Test Enterprise Value fallback calculation."""
        data = {
            "market_capitalization": 1000000,
            "total_debt": 200000,
            "cash_and_equivalents": 50000,
        }

        fallback_value = mapper.get_fallback_value("enterprise_value", data)

        assert fallback_value is not None
        assert fallback_value == 1150000  # MC + Debt - Cash

    def test_fallback_alias_lookup(self, mapper):
        """Test fallback using field aliases."""
        # Add sample data with alias
        data = {"Sales": 1000000}  # "Sales" is an alias for "revenue"

        fallback_value = mapper.get_fallback_value("revenue", data)

        # Should find the alias
        assert fallback_value == 1000000

    def test_fallback_no_data_available(self, mapper):
        """Test fallback returns None when no data available."""
        data = {}

        fallback_value = mapper.get_fallback_value("free_cash_flow", data)

        assert fallback_value is None


class TestIntegrationMethods:
    """Test suite for integration methods."""

    def test_standardize_financial_data_basic(self, mapper):
        """Test basic financial data standardization."""
        raw_data = {
            "Total Revenue": 1000000,
            "Net Income": 150000,
            "Total Assets": 5000000,
            "Cash from Operations": 200000,
        }

        standardized_data, metadata = mapper.standardize_financial_data(
            raw_data, company_ticker="AAPL", apply_fallbacks=True
        )

        assert "revenue" in standardized_data
        assert "net_income" in standardized_data
        assert "total_assets" in standardized_data
        assert "operating_cash_flow" in standardized_data
        assert "validation_report" in metadata
        assert metadata["company_ticker"] == "AAPL"

    def test_standardize_with_fallbacks(self, mapper):
        """Test standardization applies fallbacks for missing fields."""
        raw_data = {
            "Total Revenue": 1000000,
            "Net Income": 150000,
            "Cash from Operations": 500000,
            "CapEx": 100000,
        }

        standardized_data, metadata = mapper.standardize_financial_data(
            raw_data, apply_fallbacks=True
        )

        # Should apply fallback for free_cash_flow
        if "fallbacks_applied" in metadata["validation_report"]:
            assert "free_cash_flow" in standardized_data

    def test_get_integration_helper(self, mapper):
        """Test getting integration helper."""
        helper = mapper.get_integration_helper()

        assert isinstance(helper, FieldMapperIntegrationHelper)
        assert helper.mapper == mapper


class TestIntegrationHelper:
    """Test suite for FieldMapperIntegrationHelper."""

    def test_process_excel_data(self, mapper):
        """Test processing Excel data through helper."""
        helper = FieldMapperIntegrationHelper(mapper)

        excel_data = {
            "Total Revenue": 1000000,
            "Net Income": 150000,
            "Total Assets": 5000000,
            "Cash from Operations": 200000,
        }

        standardized = helper.process_excel_data(
            excel_data, company_ticker="AAPL", cache_key="test_cache"
        )

        assert "revenue" in standardized
        assert "net_income" in standardized

        # Test caching
        standardized_cached = helper.process_excel_data(
            excel_data, company_ticker="AAPL", cache_key="test_cache"
        )

        assert standardized == standardized_cached

    def test_get_required_field_direct(self, mapper):
        """Test getting required field that exists."""
        helper = FieldMapperIntegrationHelper(mapper)

        data = {"revenue": 1000000}

        value = helper.get_required_field("revenue", data)

        assert value == 1000000

    def test_get_required_field_with_fallback(self, mapper):
        """Test getting required field with fallback."""
        helper = FieldMapperIntegrationHelper(mapper)

        data = {"operating_cash_flow": 500000, "capital_expenditures": 100000}

        value = helper.get_required_field("free_cash_flow", data)

        # Should calculate fallback
        assert value == 400000

    def test_validate_data_completeness_complete(self, mapper):
        """Test validation when all required fields present."""
        helper = FieldMapperIntegrationHelper(mapper)

        # All required fields from config
        data = {
            "revenue": 1000000,
            "net_income": 150000,
            "operating_income": 250000,
            "gross_profit": 400000,
            "total_assets": 5000000,
            "total_liabilities": 2000000,
            "shareholders_equity": 3000000,
            "cash_and_equivalents": 500000,
            "operating_cash_flow": 200000,
            "capital_expenditures": 50000,
            "free_cash_flow": 150000,
        }

        is_complete, missing = helper.validate_data_completeness(data)

        assert is_complete
        assert len(missing) == 0

    def test_validate_data_completeness_incomplete(self, mapper):
        """Test validation when required fields missing."""
        helper = FieldMapperIntegrationHelper(mapper)

        data = {"revenue": 1000000}  # Missing other required fields

        is_complete, missing = helper.validate_data_completeness(data)

        assert not is_complete
        assert len(missing) > 0

    def test_get_mapper_statistics(self, mapper):
        """Test getting mapper statistics through helper."""
        helper = FieldMapperIntegrationHelper(mapper)

        # Perform some mappings
        mapper.map_field("revenue")
        mapper.map_field("net income")

        stats = helper.get_mapper_statistics()

        assert "total_mappings" in stats
        assert stats["total_mappings"] == 2

    def test_clear_cache(self, mapper):
        """Test clearing integration helper cache."""
        helper = FieldMapperIntegrationHelper(mapper)

        # Add data to cache
        helper._cached_standardized_data["test_key"] = {"revenue": 1000000}

        assert len(helper._cached_standardized_data) == 1

        helper.clear_cache()

        assert len(helper._cached_standardized_data) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
