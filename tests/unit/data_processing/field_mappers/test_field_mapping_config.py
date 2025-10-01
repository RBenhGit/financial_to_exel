"""
Tests for Field Mapping Configuration Loading and Validation
============================================================

Tests the field_mapping_config.yaml configuration file structure,
loading, parsing, and validation.
"""

import pytest
import yaml
from pathlib import Path

from core.data_processing.field_mappers.statement_field_mapper import (
    StatementFieldMapper,
    ConfigurationError,
    MappingStrategy,
)


class TestFieldMappingConfigStructure:
    """Test configuration file structure and validity"""

    @pytest.fixture
    def config_path(self):
        """Get path to field mapping configuration"""
        project_root = Path(__file__).parent.parent.parent.parent.parent
        return project_root / "config" / "field_mapping_config.yaml"

    @pytest.fixture
    def config_data(self, config_path):
        """Load configuration data"""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self, config_path):
        """Test that configuration file exists"""
        assert config_path.exists(), f"Configuration file not found at {config_path}"

    def test_config_is_valid_yaml(self, config_path):
        """Test that configuration is valid YAML"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Configuration file is not valid YAML: {e}")

    def test_config_has_required_sections(self, config_data):
        """Test that configuration has all required top-level sections"""
        required_sections = [
            "default_mappings",
            "company_specific_mappings",
            "industry_mappings",
            "reporting_standard_mappings",
            "field_aliases",
            "required_fields",
            "regex_patterns",
        ]

        for section in required_sections:
            assert section in config_data, f"Missing required section: {section}"

    def test_default_mappings_structure(self, config_data):
        """Test default_mappings section structure"""
        default_mappings = config_data["default_mappings"]

        assert isinstance(default_mappings, dict), "default_mappings must be a dictionary"
        assert len(default_mappings) > 0, "default_mappings should not be empty"

        # Check that all keys and values are strings
        for key, value in default_mappings.items():
            assert isinstance(key, str), f"Mapping key must be string: {key}"
            assert isinstance(value, str), f"Mapping value must be string: {value}"

    def test_required_income_statement_fields(self, config_data):
        """Test that essential income statement fields are mapped"""
        default_mappings = config_data["default_mappings"]

        essential_fields = [
            "revenue",
            "net_income",
            "operating_income",
            "gross_profit",
            "operating_expenses",
        ]

        for field in essential_fields:
            assert (
                field in default_mappings
            ), f"Essential income statement field missing: {field}"

    def test_required_balance_sheet_fields(self, config_data):
        """Test that essential balance sheet fields are mapped"""
        default_mappings = config_data["default_mappings"]

        essential_fields = [
            "total_assets",
            "total_liabilities",
            "shareholders_equity",
            "cash_and_equivalents",
            "total_current_assets",
            "total_current_liabilities",
        ]

        for field in essential_fields:
            assert (
                field in default_mappings
            ), f"Essential balance sheet field missing: {field}"

    def test_required_cash_flow_fields(self, config_data):
        """Test that essential cash flow fields are mapped"""
        default_mappings = config_data["default_mappings"]

        essential_fields = [
            "operating_cash_flow",
            "capital_expenditures",
            "free_cash_flow",
        ]

        for field in essential_fields:
            assert field in default_mappings, f"Essential cash flow field missing: {field}"

    def test_company_specific_mappings_structure(self, config_data):
        """Test company_specific_mappings section structure"""
        company_mappings = config_data["company_specific_mappings"]

        assert isinstance(company_mappings, dict), "company_specific_mappings must be a dictionary"

        # Check structure for each company
        for ticker, mappings in company_mappings.items():
            assert isinstance(ticker, str), f"Ticker must be string: {ticker}"
            assert isinstance(mappings, dict), f"Mappings for {ticker} must be a dictionary"

            # Check that all mapping keys exist in default_mappings
            default_keys = set(config_data["default_mappings"].keys())
            for field_key in mappings.keys():
                assert (
                    field_key in default_keys
                ), f"Company-specific field '{field_key}' not in default_mappings"

    def test_industry_mappings_structure(self, config_data):
        """Test industry_mappings section structure"""
        industry_mappings = config_data["industry_mappings"]

        assert isinstance(industry_mappings, dict), "industry_mappings must be a dictionary"

        expected_industries = ["technology", "financial", "retail", "automotive", "energy"]

        for industry in expected_industries:
            assert industry in industry_mappings, f"Expected industry missing: {industry}"

    def test_reporting_standard_mappings(self, config_data):
        """Test reporting_standard_mappings section"""
        standard_mappings = config_data["reporting_standard_mappings"]

        assert isinstance(standard_mappings, dict), "reporting_standard_mappings must be dict"

        # Check for GAAP and IFRS
        assert "GAAP" in standard_mappings, "GAAP mappings missing"
        assert "IFRS" in standard_mappings, "IFRS mappings missing"

    def test_field_aliases_structure(self, config_data):
        """Test field_aliases section structure"""
        field_aliases = config_data["field_aliases"]

        assert isinstance(field_aliases, dict), "field_aliases must be a dictionary"

        # Check that all alias keys exist in default_mappings
        default_keys = set(config_data["default_mappings"].keys())

        for standard_field, aliases in field_aliases.items():
            assert (
                standard_field in default_keys
            ), f"Alias field '{standard_field}' not in default_mappings"
            assert isinstance(aliases, list), f"Aliases for '{standard_field}' must be a list"

            # Check that all aliases are strings
            for alias in aliases:
                assert isinstance(alias, str), f"Alias must be string: {alias}"

    def test_required_fields_list(self, config_data):
        """Test required_fields section"""
        required_fields = config_data["required_fields"]

        assert isinstance(required_fields, list), "required_fields must be a list"
        assert len(required_fields) > 0, "required_fields should not be empty"

        # Check that all required fields exist in default_mappings
        default_keys = set(config_data["default_mappings"].keys())

        for field in required_fields:
            assert isinstance(field, str), f"Required field must be string: {field}"
            assert (
                field in default_keys
            ), f"Required field '{field}' not in default_mappings"

    def test_regex_patterns_structure(self, config_data):
        """Test regex_patterns section"""
        regex_patterns = config_data["regex_patterns"]

        assert isinstance(regex_patterns, dict), "regex_patterns must be a dictionary"

        # Check that pattern keys exist in default_mappings
        default_keys = set(config_data["default_mappings"].keys())

        for field, pattern in regex_patterns.items():
            assert field in default_keys, f"Regex field '{field}' not in default_mappings"
            assert isinstance(pattern, str), f"Regex pattern must be string: {pattern}"

            # Test that pattern is valid regex
            import re

            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Invalid regex pattern for '{field}': {e}")

    def test_field_transformations_section(self, config_data):
        """Test field_transformations section"""
        if "field_transformations" in config_data:
            transformations = config_data["field_transformations"]
            assert isinstance(transformations, dict), "field_transformations must be dict"

    def test_validation_rules_section(self, config_data):
        """Test validation_rules section"""
        if "validation_rules" in config_data:
            validation = config_data["validation_rules"]
            assert isinstance(validation, dict), "validation_rules must be dict"

    def test_mapping_quality_section(self, config_data):
        """Test mapping_quality section"""
        if "mapping_quality" in config_data:
            quality = config_data["mapping_quality"]
            assert isinstance(quality, dict), "mapping_quality must be dict"

            if "min_confidence_score" in quality:
                score = quality["min_confidence_score"]
                assert 0.0 <= score <= 1.0, "min_confidence_score must be between 0 and 1"

    def test_fuzzy_matching_section(self, config_data):
        """Test fuzzy_matching section"""
        if "fuzzy_matching" in config_data:
            fuzzy_config = config_data["fuzzy_matching"]
            assert isinstance(fuzzy_config, dict), "fuzzy_matching must be dict"

            if "default_threshold" in fuzzy_config:
                threshold = fuzzy_config["default_threshold"]
                assert (
                    0.0 <= threshold <= 1.0
                ), "default_threshold must be between 0 and 1"


class TestConfigurationLoading:
    """Test configuration loading in StatementFieldMapper"""

    def test_mapper_loads_config_successfully(self):
        """Test that mapper loads configuration without errors"""
        mapper = StatementFieldMapper()

        assert mapper.config_path.exists(), "Config path should exist"
        assert len(mapper.default_mappings) > 0, "Default mappings should be loaded"
        assert len(mapper.field_aliases) > 0, "Field aliases should be loaded"
        assert len(mapper.required_fields) > 0, "Required fields should be loaded"

    def test_mapper_loads_all_sections(self):
        """Test that all configuration sections are loaded"""
        mapper = StatementFieldMapper()

        assert isinstance(mapper.default_mappings, dict), "default_mappings not loaded"
        assert isinstance(
            mapper.company_specific_mappings, dict
        ), "company_specific_mappings not loaded"
        assert isinstance(mapper.industry_mappings, dict), "industry_mappings not loaded"
        assert isinstance(
            mapper.reporting_standard_mappings, dict
        ), "reporting_standard_mappings not loaded"
        assert isinstance(mapper.field_aliases, dict), "field_aliases not loaded"
        assert isinstance(mapper.required_fields, set), "required_fields not loaded"
        assert isinstance(mapper.regex_patterns, dict), "regex_patterns not loaded"

    def test_mapper_validates_required_sections(self):
        """Test that mapper validates configuration structure"""
        # This should not raise an error with valid config
        try:
            mapper = StatementFieldMapper()
            assert mapper is not None
        except ConfigurationError:
            pytest.fail("Valid configuration should not raise ConfigurationError")

    def test_fuzzy_threshold_from_config(self):
        """Test that fuzzy threshold can be overridden from config"""
        mapper = StatementFieldMapper()

        # Should load threshold from config or use default
        assert mapper.fuzzy_threshold > 0.0, "Fuzzy threshold should be positive"
        assert mapper.fuzzy_threshold <= 1.0, "Fuzzy threshold should be <= 1.0"

    def test_company_specific_overrides(self):
        """Test that company-specific mappings are loaded"""
        mapper = StatementFieldMapper()

        # Check that some companies are configured
        assert len(mapper.company_specific_mappings) > 0, "Should have company mappings"

        # Verify companies from the test data
        expected_companies = ["AAPL", "GOOGL", "GOOG", "MSFT"]
        for company in expected_companies:
            assert (
                company in mapper.company_specific_mappings
            ), f"Company {company} should be configured"


class TestConfigurationInheritance:
    """Test configuration inheritance patterns"""

    def test_company_mappings_inherit_defaults(self):
        """Test that company-specific mappings properly override defaults"""
        mapper = StatementFieldMapper()

        # Test with AAPL which has specific mappings
        result = mapper.map_field("Net Sales", company_ticker="AAPL")

        assert result.is_successful, "Should successfully map AAPL-specific field"
        assert result.mapped_field_name == "revenue", "Should map to standard 'revenue' field"

    def test_default_mapping_fallback(self):
        """Test fallback to default mappings when no company-specific mapping exists"""
        mapper = StatementFieldMapper()

        # Test with a field that uses default mapping
        result = mapper.map_field("Operating Income")

        assert result.is_successful, "Should successfully map using default mapping"
        assert (
            result.mapped_field_name == "operating_income"
        ), "Should map to standard field"

    def test_industry_mapping_priority(self):
        """Test industry mapping priority"""
        mapper = StatementFieldMapper()

        # Test industry-specific mapping (if available)
        if "technology" in mapper.industry_mappings:
            # This tests that the mapping system recognizes industry parameter
            result = mapper.map_field("R&D Expenses", industry="technology")
            assert result.is_successful, "Industry mapping should work"


class TestRequiredFieldsValidation:
    """Test required fields validation"""

    def test_required_fields_loaded(self):
        """Test that required fields are loaded from config"""
        mapper = StatementFieldMapper()

        assert len(mapper.required_fields) > 0, "Required fields should be loaded"

        # Check for critical fields
        critical_fields = [
            "revenue",
            "net_income",
            "total_assets",
            "operating_cash_flow",
        ]

        for field in critical_fields:
            assert (
                field in mapper.required_fields
            ), f"Critical field '{field}' should be required"

    def test_validate_required_fields_success(self):
        """Test validation passes when all required fields are mapped"""
        mapper = StatementFieldMapper()

        # Create a complete set of mappings
        field_names = [
            "Revenue",
            "Net Income",
            "Total Assets",
            "Shareholders' Equity",
            "Total Liabilities",
            "Cash and Cash Equivalents",
            "Cash from Operations",
            "Capital Expenditures",
            "Free Cash Flow",
            "Gross Profit",
            "Operating Income",
        ]

        mapped_fields = mapper.batch_map_fields(field_names)

        is_valid, missing = mapper.validate_required_fields(mapped_fields)

        assert is_valid, f"Validation should pass. Missing fields: {missing}"
        assert len(missing) == 0, "Should have no missing required fields"

    def test_validate_required_fields_failure(self):
        """Test validation fails when required fields are missing"""
        mapper = StatementFieldMapper()

        # Create incomplete mappings (missing critical fields)
        field_names = ["Revenue", "Operating Income"]

        mapped_fields = mapper.batch_map_fields(field_names)

        is_valid, missing = mapper.validate_required_fields(mapped_fields)

        assert not is_valid, "Validation should fail with missing required fields"
        assert len(missing) > 0, "Should report missing required fields"


class TestRealWorldFieldNames:
    """Test mapping of real-world field names from Excel files"""

    def test_microsoft_field_names(self):
        """Test mapping of actual Microsoft Excel field names"""
        mapper = StatementFieldMapper()

        msft_fields = {
            "Revenue": "revenue",
            "Net Income to Company": "net_income",
            "Operating Income": "operating_income",
            "Gross Profit": "gross_profit",
            "R&D Expenses": "rd_expenses",
            "Cash from Operations": "operating_cash_flow",
            "Capital Expenditures": "capital_expenditures",
        }

        for excel_field, expected_mapping in msft_fields.items():
            result = mapper.map_field(excel_field, company_ticker="MSFT")
            assert (
                result.is_successful
            ), f"Failed to map MSFT field: {excel_field}"
            assert (
                result.mapped_field_name == expected_mapping
            ), f"Incorrect mapping for {excel_field}"

    def test_google_field_names(self):
        """Test mapping of actual Google Excel field names"""
        mapper = StatementFieldMapper()

        # Google uses "Revenues" instead of "Revenue"
        result = mapper.map_field("Revenues", company_ticker="GOOG")

        assert result.is_successful, "Should map Google 'Revenues' field"
        assert (
            result.mapped_field_name == "revenue"
        ), "Should map to standard 'revenue'"

    def test_balance_sheet_field_names(self):
        """Test mapping of balance sheet field names"""
        mapper = StatementFieldMapper()

        bs_fields = {
            "Total Assets": "total_assets",
            "Total Liabilities": "total_liabilities",
            "Shareholders' Equity": "shareholders_equity",
            "Cash and Cash Equivalents": "cash_and_equivalents",
            "Accounts Receivable, Net": "accounts_receivable",
        }

        for excel_field, expected_mapping in bs_fields.items():
            result = mapper.map_field(excel_field)
            assert (
                result.is_successful
            ), f"Failed to map balance sheet field: {excel_field}"
            assert (
                result.mapped_field_name == expected_mapping
            ), f"Incorrect mapping for {excel_field}"

    def test_cash_flow_field_names(self):
        """Test mapping of cash flow statement field names"""
        mapper = StatementFieldMapper()

        cf_fields = {
            "Cash from Operations": "operating_cash_flow",
            "Capital Expenditures": "capital_expenditures",
            "Free Cash Flow": "free_cash_flow",
            "Depreciation & Amortization (CF)": "depreciation_amortization",
        }

        for excel_field, expected_mapping in cf_fields.items():
            result = mapper.map_field(excel_field)
            assert (
                result.is_successful
            ), f"Failed to map cash flow field: {excel_field}"
            assert (
                result.mapped_field_name == expected_mapping
            ), f"Incorrect mapping for {excel_field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
