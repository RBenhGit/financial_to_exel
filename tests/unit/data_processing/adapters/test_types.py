"""
Tests for adapter type definitions and GeneralizedVariableDict schema.

Validates:
- Schema structure and field definitions
- Field coverage across all categories
- Type checking and validation
- Compatibility with existing data structures
"""

import pytest
from datetime import datetime, date
from typing import get_type_hints

from core.data_processing.adapters.types import (
    GeneralizedVariableDict,
    AdapterOutputMetadata,
    ValidationResult,
    AdapterException,
    AdapterStatus,
    AdapterInfo,
    REQUIRED_FIELDS,
    INCOME_STATEMENT_FIELDS,
    BALANCE_SHEET_FIELDS,
    CASH_FLOW_FIELDS,
    MARKET_DATA_FIELDS,
    HISTORICAL_DATA_FIELDS,
    FINANCIAL_RATIO_FIELDS,
    GROWTH_METRICS_FIELDS,
    VALUATION_METRICS_FIELDS,
    QUALITY_METRICS_FIELDS,
    COMPANY_INFO_FIELDS,
    DIVIDEND_METRICS_FIELDS,
    SHARE_METRICS_FIELDS,
    DCF_VALUATION_FIELDS,
    ANALYST_ESTIMATE_FIELDS,
    DATA_QUALITY_FIELDS,
    ALL_OPTIONAL_FIELDS,
    TOTAL_FIELD_COUNT,
)


class TestGeneralizedVariableDictSchema:
    """Test the GeneralizedVariableDict schema definition."""

    def test_schema_has_required_fields(self):
        """Verify all required fields are defined."""
        type_hints = get_type_hints(GeneralizedVariableDict)

        for field in REQUIRED_FIELDS:
            assert field in type_hints, f"Required field '{field}' not found in schema"

    def test_schema_has_100_plus_fields(self):
        """Verify schema has 100+ total fields as required."""
        assert TOTAL_FIELD_COUNT >= 100, f"Schema has {TOTAL_FIELD_COUNT} fields, need at least 100"
        print(f"✓ Schema has {TOTAL_FIELD_COUNT} total fields (exceeds requirement of 100+)")

    def test_field_categorization_complete(self):
        """Verify all optional fields are categorized."""
        type_hints = get_type_hints(GeneralizedVariableDict)

        # Get all fields except required ones
        optional_fields_in_schema = [
            field for field in type_hints.keys()
            if field not in REQUIRED_FIELDS
        ]

        # Verify all optional fields are in ALL_OPTIONAL_FIELDS
        for field in optional_fields_in_schema:
            assert field in ALL_OPTIONAL_FIELDS, \
                f"Field '{field}' not categorized in ALL_OPTIONAL_FIELDS"

    def test_income_statement_coverage(self):
        """Verify comprehensive income statement field coverage."""
        required_fields = [
            'revenue', 'gross_profit', 'operating_income', 'net_income',
            'eps_basic', 'eps_diluted', 'ebitda'
        ]

        for field in required_fields:
            assert field in INCOME_STATEMENT_FIELDS, \
                f"Essential income statement field '{field}' missing"

    def test_balance_sheet_coverage(self):
        """Verify comprehensive balance sheet field coverage."""
        required_fields = [
            'total_assets', 'total_liabilities', 'total_stockholders_equity',
            'cash_and_cash_equivalents', 'accounts_receivable', 'inventory',
            'long_term_debt'
        ]

        for field in required_fields:
            assert field in BALANCE_SHEET_FIELDS, \
                f"Essential balance sheet field '{field}' missing"

    def test_cash_flow_coverage(self):
        """Verify comprehensive cash flow statement field coverage."""
        required_fields = [
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
            'free_cash_flow', 'capital_expenditures'
        ]

        for field in required_fields:
            assert field in CASH_FLOW_FIELDS, \
                f"Essential cash flow field '{field}' missing"

    def test_financial_ratios_coverage(self):
        """Verify comprehensive financial ratios coverage."""
        ratio_categories = {
            'profitability': ['gross_margin', 'operating_margin', 'net_margin', 'return_on_equity', 'return_on_assets'],
            'liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio'],
            'leverage': ['debt_to_equity', 'interest_coverage'],
            'efficiency': ['inventory_turnover', 'receivables_turnover', 'cash_conversion_cycle']
        }

        for category, fields in ratio_categories.items():
            for field in fields:
                assert field in FINANCIAL_RATIO_FIELDS, \
                    f"{category.title()} ratio '{field}' missing"

    def test_growth_metrics_coverage(self):
        """Verify growth metrics are included."""
        required_metrics = [
            'revenue_growth', 'earnings_growth', 'eps_growth',
            'free_cash_flow_growth'
        ]

        for metric in required_metrics:
            assert metric in GROWTH_METRICS_FIELDS, \
                f"Growth metric '{metric}' missing"

    def test_valuation_metrics_coverage(self):
        """Verify valuation metrics are included."""
        required_metrics = [
            'price_to_cash_flow', 'price_to_free_cash_flow',
            'ev_to_operating_cash_flow', 'earnings_yield', 'free_cash_flow_yield'
        ]

        for metric in required_metrics:
            assert metric in VALUATION_METRICS_FIELDS, \
                f"Valuation metric '{metric}' missing"

    def test_quality_metrics_coverage(self):
        """Verify quality/health metrics are included."""
        required_metrics = [
            'piotroski_f_score', 'altman_z_score', 'quality_of_earnings'
        ]

        for metric in required_metrics:
            assert metric in QUALITY_METRICS_FIELDS, \
                f"Quality metric '{metric}' missing"

    def test_company_info_fields(self):
        """Verify company information fields are included."""
        required_fields = [
            'sector', 'industry', 'country', 'exchange'
        ]

        for field in required_fields:
            assert field in COMPANY_INFO_FIELDS, \
                f"Company info field '{field}' missing"

    def test_data_quality_metadata_fields(self):
        """Verify data quality and metadata fields are included."""
        required_fields = [
            'data_source', 'data_timestamp', 'reporting_period',
            'data_quality_score', 'completeness_score'
        ]

        for field in required_fields:
            assert field in DATA_QUALITY_FIELDS, \
                f"Data quality field '{field}' missing"

    def test_no_duplicate_fields(self):
        """Verify no field appears in multiple categories."""
        all_categorized_fields = (
            INCOME_STATEMENT_FIELDS +
            BALANCE_SHEET_FIELDS +
            CASH_FLOW_FIELDS +
            MARKET_DATA_FIELDS +
            HISTORICAL_DATA_FIELDS +
            FINANCIAL_RATIO_FIELDS +
            GROWTH_METRICS_FIELDS +
            VALUATION_METRICS_FIELDS +
            QUALITY_METRICS_FIELDS +
            COMPANY_INFO_FIELDS +
            DIVIDEND_METRICS_FIELDS +
            SHARE_METRICS_FIELDS +
            DCF_VALUATION_FIELDS +
            ANALYST_ESTIMATE_FIELDS +
            DATA_QUALITY_FIELDS
        )

        # Check for duplicates
        field_counts = {}
        for field in all_categorized_fields:
            field_counts[field] = field_counts.get(field, 0) + 1

        duplicates = {field: count for field, count in field_counts.items() if count > 1}
        assert not duplicates, f"Duplicate fields found: {duplicates}"


class TestGeneralizedVariableDictCreation:
    """Test creating GeneralizedVariableDict instances."""

    def test_create_minimal_valid_dict(self):
        """Test creating dict with only required fields."""
        data: GeneralizedVariableDict = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September'
        }

        assert data['ticker'] == 'AAPL'
        assert data['company_name'] == 'Apple Inc.'

    def test_create_comprehensive_dict(self):
        """Test creating dict with many optional fields."""
        data: GeneralizedVariableDict = {
            # Required
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September',

            # Income Statement
            'revenue': 394328.0,
            'gross_profit': 169148.0,
            'operating_income': 114301.0,
            'net_income': 96995.0,
            'eps_diluted': 6.16,

            # Balance Sheet
            'total_assets': 352755.0,
            'total_liabilities': 290020.0,
            'total_stockholders_equity': 62735.0,
            'cash_and_cash_equivalents': 29943.0,

            # Cash Flow
            'operating_cash_flow': 122151.0,
            'free_cash_flow': 111443.0,
            'capital_expenditures': 10708.0,

            # Market Data
            'market_cap': 2900000.0,
            'stock_price': 185.50,
            'pe_ratio': 30.1,

            # Ratios
            'gross_margin': 0.429,
            'operating_margin': 0.290,
            'return_on_equity': 1.546,
            'current_ratio': 0.98,
            'debt_to_equity': 1.97,

            # Growth
            'revenue_growth': 0.076,
            'earnings_growth': 0.072,

            # Company Info
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'country': 'USA',
            'exchange': 'NASDAQ',

            # Metadata
            'data_source': 'yfinance',
            'data_timestamp': datetime.now(),
            'reporting_period': 'FY 2023',
            'data_quality_score': 0.95,
            'completeness_score': 0.87,
        }

        assert data['revenue'] == 394328.0
        assert data['gross_margin'] == 0.429
        assert data['sector'] == 'Technology'

    def test_optional_fields_can_be_none(self):
        """Test that optional fields can be None or omitted."""
        data: GeneralizedVariableDict = {
            'ticker': 'TEST',
            'company_name': 'Test Company',
            'currency': 'USD',
            'fiscal_year_end': 'December',
            'revenue': None,  # Explicitly None
            # Other optional fields omitted
        }

        assert data['ticker'] == 'TEST'
        assert data.get('revenue') is None
        assert data.get('gross_profit') is None


class TestAdapterOutputMetadata:
    """Test AdapterOutputMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating metadata instance."""
        metadata = AdapterOutputMetadata(
            source='excel',
            timestamp=datetime.now(),
            quality_score=0.95,
            completeness=0.87,
            validation_errors=['Missing sector field'],
            extraction_time=2.5,
            cache_hit=True,
            api_calls_made=0
        )

        assert metadata.source == 'excel'
        assert metadata.quality_score == 0.95
        assert metadata.cache_hit is True
        assert len(metadata.validation_errors) == 1

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = AdapterOutputMetadata(
            source='yfinance',
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            quality_score=1.0,
            completeness=0.92
        )

        result = metadata.to_dict()

        assert result['source'] == 'yfinance'
        assert result['quality_score'] == 1.0
        assert 'timestamp' in result


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_create_valid_result(self):
        """Test creating successful validation result."""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error_marks_invalid(self):
        """Test that adding error marks result as invalid."""
        result = ValidationResult(valid=True)
        result.add_error("Missing required field")

        assert result.valid is False
        assert len(result.errors) == 1

    def test_add_warning_keeps_valid(self):
        """Test that adding warning doesn't mark as invalid."""
        result = ValidationResult(valid=True)
        result.add_warning("Optional field missing")

        assert result.valid is True
        assert len(result.warnings) == 1

    def test_merge_results(self):
        """Test merging two validation results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=False)
        result2.add_error("Error 1")

        result1.merge(result2)

        assert result1.valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 1


class TestAdapterException:
    """Test AdapterException class."""

    def test_create_basic_exception(self):
        """Test creating basic adapter exception."""
        exc = AdapterException("Failed to extract data")

        assert "Failed to extract data" in str(exc)

    def test_exception_with_source_and_original(self):
        """Test exception with source and original exception."""
        original = ValueError("Invalid ticker")
        exc = AdapterException(
            "Extraction failed",
            source="yfinance",
            original_exception=original
        )

        exc_str = str(exc)
        assert "Extraction failed" in exc_str
        assert "yfinance" in exc_str
        assert "Invalid ticker" in exc_str


class TestAdapterInfo:
    """Test AdapterInfo dataclass."""

    def test_create_adapter_info(self):
        """Test creating adapter info instance."""
        info = AdapterInfo(
            adapter_type='yfinance',
            status=AdapterStatus.READY,
            supported_categories=['market_data', 'fundamentals'],
            requires_api_key=False,
            rate_limit_per_minute=2000,
            total_requests=100,
            failed_requests=5
        )

        assert info.adapter_type == 'yfinance'
        assert info.status == AdapterStatus.READY
        assert info.success_rate == 0.95

    def test_success_rate_with_zero_requests(self):
        """Test success rate calculation with zero requests."""
        info = AdapterInfo(
            adapter_type='test',
            status=AdapterStatus.READY,
            supported_categories=[],
            requires_api_key=False,
            rate_limit_per_minute=60,
            total_requests=0,
            failed_requests=0
        )

        assert info.success_rate == 1.0

    def test_adapter_info_to_dict(self):
        """Test converting adapter info to dictionary."""
        info = AdapterInfo(
            adapter_type='excel',
            status=AdapterStatus.READY,
            supported_categories=['all'],
            requires_api_key=False,
            rate_limit_per_minute=0
        )

        result = info.to_dict()

        assert result['adapter_type'] == 'excel'
        assert result['status'] == 'ready'
        assert 'success_rate' in result


class TestFieldConstants:
    """Test field constant definitions."""

    def test_required_fields_constant(self):
        """Test REQUIRED_FIELDS constant."""
        assert 'ticker' in REQUIRED_FIELDS
        assert 'company_name' in REQUIRED_FIELDS
        assert 'currency' in REQUIRED_FIELDS
        assert 'fiscal_year_end' in REQUIRED_FIELDS

    def test_all_field_lists_are_lists(self):
        """Test that all field constants are lists."""
        field_lists = [
            INCOME_STATEMENT_FIELDS,
            BALANCE_SHEET_FIELDS,
            CASH_FLOW_FIELDS,
            MARKET_DATA_FIELDS,
            HISTORICAL_DATA_FIELDS,
            FINANCIAL_RATIO_FIELDS,
            GROWTH_METRICS_FIELDS,
            VALUATION_METRICS_FIELDS,
            QUALITY_METRICS_FIELDS,
            COMPANY_INFO_FIELDS,
            DIVIDEND_METRICS_FIELDS,
            SHARE_METRICS_FIELDS,
            DCF_VALUATION_FIELDS,
            ANALYST_ESTIMATE_FIELDS,
            DATA_QUALITY_FIELDS,
        ]

        for field_list in field_lists:
            assert isinstance(field_list, list)
            assert len(field_list) > 0

    def test_total_field_count_calculation(self):
        """Test that TOTAL_FIELD_COUNT is calculated correctly."""
        expected = len(REQUIRED_FIELDS) + len(ALL_OPTIONAL_FIELDS)
        assert TOTAL_FIELD_COUNT == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
