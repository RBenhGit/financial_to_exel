"""
Comprehensive unit tests for Financial Statement Field Extractor module.

Tests cover:
- FieldMappingDict functionality
- BaseFieldExtractor behavior
- IncomeStatementExtractor field mapping and validation
- BalanceSheetExtractor field mapping and validation
- CashFlowStatementExtractor field mapping and validation
- FinancialStatementFieldExtractor factory operations
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook

from core.data_processing.field_extractors.financial_statement_extractor import (
    FieldMappingDict,
    FieldExtractionResult,
    BaseFieldExtractor,
    IncomeStatementExtractor,
    BalanceSheetExtractor,
    CashFlowStatementExtractor,
    FinancialStatementFieldExtractor,
    StatementType,
    FieldValidationError,
    MissingFieldError
)


class TestFieldMappingDict:
    """Test FieldMappingDict functionality"""

    def test_create_basic_mapping(self):
        """Test creating a basic field mapping"""
        mapping = FieldMappingDict(
            primary_names={"revenue": "Total Revenue"},
            aliases={"revenue": ["Sales", "Net Sales"]}
        )

        assert mapping.primary_names["revenue"] == "Total Revenue"
        assert "Sales" in mapping.aliases["revenue"]

    def test_get_all_mappings_for_field(self):
        """Test retrieving all mappings for a field"""
        mapping = FieldMappingDict(
            primary_names={"revenue": "Total Revenue"},
            aliases={"revenue": ["Sales", "Net Sales"]},
            abbreviations={"revenue": ["Rev"]}
        )

        all_mappings = mapping.get_all_mappings_for_field("revenue")

        assert "revenue" in all_mappings
        assert "Total Revenue" in all_mappings
        assert "Sales" in all_mappings
        assert "Net Sales" in all_mappings
        assert "Rev" in all_mappings

    def test_find_standard_field_name_exact_match(self):
        """Test finding standard field name with exact match"""
        mapping = FieldMappingDict(
            primary_names={"revenue": "Total Revenue"},
            excel_variations={"revenue": ["Revenue", "Total Sales"]}
        )

        # Exact match with standard name
        assert mapping.find_standard_field_name("revenue") == "revenue"

        # Exact match with variation (case-insensitive)
        assert mapping.find_standard_field_name("Revenue") == "revenue"
        assert mapping.find_standard_field_name("Total Sales") == "revenue"

    def test_find_standard_field_name_no_match(self):
        """Test finding standard field name with no match"""
        mapping = FieldMappingDict(
            primary_names={"revenue": "Total Revenue"}
        )

        assert mapping.find_standard_field_name("Unknown Field") is None

    def test_find_standard_field_name_with_whitespace(self):
        """Test finding field name with extra whitespace"""
        mapping = FieldMappingDict(
            excel_variations={"revenue": ["Total Revenue"]}
        )

        assert mapping.find_standard_field_name("  Total Revenue  ") == "revenue"


class TestFieldExtractionResult:
    """Test FieldExtractionResult data model"""

    def test_create_result(self):
        """Test creating a field extraction result"""
        result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="/path/to/file.xlsx",
            extracted_fields={"revenue": {"FY": 100.0}},
            missing_fields=["net_income"],
            invalid_fields={},
            total_fields_attempted=10,
            successful_extractions=9,
            data_quality_score=0.9,
            available_periods=["FY", "FY-1"]
        )

        assert result.company_symbol == "MSFT"
        assert result.data_quality_score == 0.9
        assert "revenue" in result.extracted_fields

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="/path/to/file.xlsx",
            extracted_fields={},
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=10,
            successful_extractions=8,
            data_quality_score=0.8
        )

        assert result.success_rate == 0.8

    def test_completeness_score_calculation(self):
        """Test completeness score calculation"""
        result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="/path/to/file.xlsx",
            extracted_fields={"revenue": {"FY": 100.0}, "cost_of_revenue": {"FY": 40.0}},
            missing_fields=["net_income"],
            invalid_fields={},
            total_fields_attempted=3,
            successful_extractions=2,
            data_quality_score=0.8
        )

        # 2 extracted / (2 extracted + 1 missing) = 0.667
        assert abs(result.completeness_score - 0.667) < 0.01

    def test_get_field_value(self):
        """Test retrieving specific field values"""
        result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="/path/to/file.xlsx",
            extracted_fields={"revenue": {"FY": 100.0, "FY-1": 90.0}},
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=1,
            successful_extractions=1,
            data_quality_score=1.0
        )

        assert result.get_field_value("revenue", "FY") == 100.0
        assert result.get_field_value("revenue", "FY-1") == 90.0
        assert result.get_field_value("revenue", "FY-2") is None
        assert result.get_field_value("unknown_field", "FY") is None

    def test_add_note(self):
        """Test adding processing notes"""
        result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="/path/to/file.xlsx",
            extracted_fields={},
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=0,
            successful_extractions=0,
            data_quality_score=0.0
        )

        result.add_note("Test note")
        assert len(result.notes) == 1
        assert "Test note" in result.notes[0]


class TestIncomeStatementExtractor:
    """Test Income Statement field extraction"""

    @pytest.fixture
    def extractor(self):
        """Create Income Statement extractor instance"""
        return IncomeStatementExtractor()

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly"""
        assert extractor.statement_type == StatementType.INCOME
        assert extractor.validate_data is True
        assert extractor.field_mappings is not None

    def test_field_mappings_coverage(self, extractor):
        """Test field mappings cover all essential income statement items"""
        # Check that key income statement fields are mapped
        essential_fields = [
            "revenue", "cost_of_revenue", "gross_profit",
            "operating_expenses", "operating_income", "net_income",
            "earnings_per_share_basic", "earnings_per_share_diluted"
        ]

        for field in essential_fields:
            mappings = extractor.field_mappings.get_all_mappings_for_field(field)
            assert len(mappings) > 0, f"No mappings found for {field}"

    def test_required_fields(self, extractor):
        """Test that required fields are defined"""
        required_fields = extractor._get_required_fields()

        assert "revenue" in required_fields
        assert "cost_of_revenue" in required_fields
        assert "gross_profit" in required_fields
        assert "operating_income" in required_fields
        assert "net_income" in required_fields

    def test_validate_field_value_revenue_positive(self, extractor):
        """Test revenue validation - must be positive"""
        # Valid revenue
        is_valid, msg = extractor._validate_field_value("revenue", 100000.0, "FY")
        assert is_valid is True

        # Invalid negative revenue
        is_valid, msg = extractor._validate_field_value("revenue", -100.0, "FY")
        assert is_valid is False
        assert "cannot be negative" in msg

    def test_validate_field_value_net_income_can_be_negative(self, extractor):
        """Test net income can be negative (losses)"""
        is_valid, msg = extractor._validate_field_value("net_income", -500.0, "FY")
        assert is_valid is True

    def test_validate_field_value_eps_range(self, extractor):
        """Test EPS validation range"""
        # Valid EPS
        is_valid, msg = extractor._validate_field_value("earnings_per_share_basic", 5.50, "FY")
        assert is_valid is True

        # Invalid EPS (out of range)
        is_valid, msg = extractor._validate_field_value("earnings_per_share_basic", 10000.0, "FY")
        assert is_valid is False

    def test_validate_field_value_shares_outstanding(self, extractor):
        """Test shares outstanding validation"""
        # Valid shares
        is_valid, msg = extractor._validate_field_value("shares_outstanding_basic", 7500.0, "FY")
        assert is_valid is True

        # Invalid negative shares
        is_valid, msg = extractor._validate_field_value("shares_outstanding_basic", -100.0, "FY")
        assert is_valid is False

    def test_validate_income_statement_relationships(self, extractor):
        """Test validation of income statement relationships"""
        extracted_fields = {
            "revenue": {"FY": 100.0},
            "cost_of_revenue": {"FY": 40.0},
            "gross_profit": {"FY": 60.0}  # Should be 100 - 40 = 60
        }

        warnings = extractor.validate_income_statement_relationships(extracted_fields)
        assert len(warnings) == 0  # No warnings for correct relationship

    def test_validate_income_statement_relationships_mismatch(self, extractor):
        """Test detection of income statement relationship mismatches"""
        extracted_fields = {
            "revenue": {"FY": 100.0},
            "cost_of_revenue": {"FY": 40.0},
            "gross_profit": {"FY": 70.0}  # WRONG: Should be 60, not 70
        }

        warnings = extractor.validate_income_statement_relationships(extracted_fields)
        assert len(warnings) > 0
        assert "Gross Profit mismatch" in warnings[0]

    def test_fuzzy_matching(self, extractor):
        """Test fuzzy matching for field names"""
        # Should match "revenue" with partial match (contains revenue + operations keywords)
        match = extractor._fuzzy_match_field("Total Revenue")
        assert match in ["revenue", "total_revenue"]

        # Should match operating income variations
        match = extractor._fuzzy_match_field("Income from Operations")
        assert match in ["operating_income", "ebit"]

        # Test more specific revenue match
        match = extractor._fuzzy_match_field("Net Sales")
        assert match in ["revenue", "net_sales"]


class TestBalanceSheetExtractor:
    """Test Balance Sheet field extraction"""

    @pytest.fixture
    def extractor(self):
        """Create Balance Sheet extractor instance"""
        return BalanceSheetExtractor()

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly"""
        assert extractor.statement_type == StatementType.BALANCE
        assert extractor.field_mappings is not None

    def test_field_mappings_coverage(self, extractor):
        """Test field mappings cover essential balance sheet items"""
        essential_fields = [
            "total_assets", "current_assets", "cash_and_equivalents",
            "total_liabilities", "current_liabilities", "shareholders_equity"
        ]

        for field in essential_fields:
            mappings = extractor.field_mappings.get_all_mappings_for_field(field)
            assert len(mappings) > 0, f"No mappings found for {field}"

    def test_required_fields(self, extractor):
        """Test that required fields are defined"""
        required_fields = extractor._get_required_fields()

        assert "total_assets" in required_fields
        assert "current_assets" in required_fields
        assert "cash_and_equivalents" in required_fields
        assert "total_liabilities" in required_fields
        assert "shareholders_equity" in required_fields

    def test_validate_field_value_assets_non_negative(self, extractor):
        """Test asset validation - must be non-negative"""
        # Valid assets
        is_valid, msg = extractor._validate_field_value("total_assets", 50000.0, "FY")
        assert is_valid is True

        # Invalid negative assets
        is_valid, msg = extractor._validate_field_value("total_assets", -100.0, "FY")
        assert is_valid is False

    def test_validate_field_value_equity_can_be_negative(self, extractor):
        """Test equity can be negative (distressed companies)"""
        is_valid, msg = extractor._validate_field_value("shareholders_equity", -500.0, "FY")
        assert is_valid is True

        # But extremely negative should fail
        is_valid, msg = extractor._validate_field_value("shareholders_equity", -150000.0, "FY")
        assert is_valid is False

    def test_validate_field_value_treasury_stock(self, extractor):
        """Test treasury stock validation - should be non-positive"""
        # Valid treasury stock (negative)
        is_valid, msg = extractor._validate_field_value("treasury_stock", -1000.0, "FY")
        assert is_valid is True

        # Invalid positive treasury stock
        is_valid, msg = extractor._validate_field_value("treasury_stock", 100.0, "FY")
        assert is_valid is False

    def test_validate_balance_sheet_equation(self, extractor):
        """Test balance sheet equation validation"""
        extracted_fields = {
            "total_assets": {"FY": 100000.0},
            "total_liabilities": {"FY": 60000.0},
            "shareholders_equity": {"FY": 40000.0}  # Assets = Liabilities + Equity
        }

        warnings = extractor.validate_balance_sheet_equation(extracted_fields)
        assert len(warnings) == 0

    def test_validate_balance_sheet_equation_imbalance(self, extractor):
        """Test detection of balance sheet imbalance"""
        extracted_fields = {
            "total_assets": {"FY": 100000.0},
            "total_liabilities": {"FY": 60000.0},
            "shareholders_equity": {"FY": 35000.0}  # WRONG: Should be 40000
        }

        warnings = extractor.validate_balance_sheet_equation(extracted_fields)
        assert len(warnings) > 0
        assert "imbalance" in warnings[0].lower()


class TestCashFlowStatementExtractor:
    """Test Cash Flow Statement field extraction"""

    @pytest.fixture
    def extractor(self):
        """Create Cash Flow Statement extractor instance"""
        return CashFlowStatementExtractor()

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly"""
        assert extractor.statement_type == StatementType.CASH_FLOW
        assert extractor.field_mappings is not None

    def test_field_mappings_coverage(self, extractor):
        """Test field mappings cover essential cash flow items"""
        essential_fields = [
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "capital_expenditures", "free_cash_flow", "net_change_in_cash"
        ]

        for field in essential_fields:
            mappings = extractor.field_mappings.get_all_mappings_for_field(field)
            assert len(mappings) > 0, f"No mappings found for {field}"

    def test_required_fields(self, extractor):
        """Test that required fields are defined"""
        required_fields = extractor._get_required_fields()

        assert "operating_cash_flow" in required_fields
        assert "investing_cash_flow" in required_fields
        assert "financing_cash_flow" in required_fields
        assert "capital_expenditures" in required_fields

    def test_validate_field_value_capex_negative(self, extractor):
        """Test capital expenditures validation - should be negative"""
        # Valid CapEx (negative = cash outflow)
        is_valid, msg = extractor._validate_field_value("capital_expenditures", -5000.0, "FY")
        assert is_valid is True

        # Invalid positive CapEx
        is_valid, msg = extractor._validate_field_value("capital_expenditures", 100.0, "FY")
        assert is_valid is False

    def test_validate_field_value_dividends_negative(self, extractor):
        """Test dividends validation - should be negative (cash outflow)"""
        # Valid dividends (negative)
        is_valid, msg = extractor._validate_field_value("dividends_paid", -500.0, "FY")
        assert is_valid is True

        # Invalid positive dividends
        is_valid, msg = extractor._validate_field_value("dividends_paid", 100.0, "FY")
        assert is_valid is False

    def test_validate_field_value_operating_cash_flow(self, extractor):
        """Test operating cash flow validation"""
        # Valid positive OCF
        is_valid, msg = extractor._validate_field_value("operating_cash_flow", 10000.0, "FY")
        assert is_valid is True

        # Valid small negative OCF
        is_valid, msg = extractor._validate_field_value("operating_cash_flow", -100.0, "FY")
        assert is_valid is True

        # Invalid extremely negative OCF
        is_valid, msg = extractor._validate_field_value("operating_cash_flow", -60000.0, "FY")
        assert is_valid is False

    def test_validate_cash_flow_relationships(self, extractor):
        """Test cash flow relationships validation"""
        extracted_fields = {
            "operating_cash_flow": {"FY": 10000.0},
            "investing_cash_flow": {"FY": -3000.0},
            "financing_cash_flow": {"FY": -2000.0},
            "net_change_in_cash": {"FY": 5000.0}  # 10000 - 3000 - 2000 = 5000
        }

        warnings = extractor.validate_cash_flow_relationships(extracted_fields)
        assert len(warnings) == 0

    def test_validate_free_cash_flow_calculation(self, extractor):
        """Test free cash flow calculation validation"""
        extracted_fields = {
            "operating_cash_flow": {"FY": 10000.0},
            "capital_expenditures": {"FY": -3000.0},
            "free_cash_flow": {"FY": 7000.0}  # 10000 + (-3000) = 7000
        }

        warnings = extractor.validate_cash_flow_relationships(extracted_fields)
        assert len(warnings) == 0

    def test_detect_cash_flow_method(self, extractor):
        """Test detection of cash flow method (indirect vs direct)"""
        # Indirect method indicators
        indirect_fields = {
            "net_income": {"FY": 5000.0},
            "depreciation_amortization": {"FY": 1000.0},
            "changes_in_working_capital": {"FY": -500.0},
            "accounts_receivable_change": {"FY": -200.0}
        }

        method = extractor.detect_cash_flow_method(indirect_fields)
        assert method == "indirect"


class TestFinancialStatementFieldExtractor:
    """Test factory class for coordinating all extractors"""

    @pytest.fixture
    def factory(self):
        """Create factory instance"""
        return FinancialStatementFieldExtractor(validate_data=True, min_quality_threshold=0.6)

    def test_factory_initialization(self, factory):
        """Test factory initializes with all extractors"""
        assert StatementType.INCOME in factory.extractors
        assert StatementType.BALANCE in factory.extractors
        assert StatementType.CASH_FLOW in factory.extractors

    def test_factory_has_correct_extractors(self, factory):
        """Test factory creates correct extractor types"""
        assert isinstance(factory.extractors[StatementType.INCOME], IncomeStatementExtractor)
        assert isinstance(factory.extractors[StatementType.BALANCE], BalanceSheetExtractor)
        assert isinstance(factory.extractors[StatementType.CASH_FLOW], CashFlowStatementExtractor)

    def test_validate_cross_statement_consistency_empty(self, factory):
        """Test cross-statement validation with insufficient data"""
        results = {}
        warnings = factory.validate_cross_statement_consistency(results)
        assert len(warnings) == 0

    def test_validate_cross_statement_consistency_cash_match(self, factory):
        """Test cross-statement cash consistency validation"""
        # Create mock results with matching cash
        income_result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="",
            extracted_fields={"net_income": {"FY": 5000.0}},
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=1,
            successful_extractions=1,
            data_quality_score=1.0,
            available_periods=["FY"]
        )

        balance_result = FieldExtractionResult(
            statement_type=StatementType.BALANCE,
            company_symbol="MSFT",
            period_type="FY",
            file_path="",
            extracted_fields={"cash_and_equivalents": {"FY": 10000.0}},
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=1,
            successful_extractions=1,
            data_quality_score=1.0,
            available_periods=["FY"]
        )

        cash_flow_result = FieldExtractionResult(
            statement_type=StatementType.CASH_FLOW,
            company_symbol="MSFT",
            period_type="FY",
            file_path="",
            extracted_fields={
                "cash_end_of_period": {"FY": 10000.0},
                "net_income": {"FY": 5000.0}
            },
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=2,
            successful_extractions=2,
            data_quality_score=1.0,
            available_periods=["FY"]
        )

        results = {
            StatementType.INCOME: income_result,
            StatementType.BALANCE: balance_result,
            StatementType.CASH_FLOW: cash_flow_result
        }

        warnings = factory.validate_cross_statement_consistency(results)
        # Should have no warnings - cash matches and net income matches
        assert len(warnings) == 0

    def test_generate_data_quality_report(self, factory):
        """Test data quality report generation"""
        # Create mock result
        income_result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="",
            extracted_fields={"revenue": {"FY": 100.0}},
            missing_fields=["net_income"],
            invalid_fields={},
            total_fields_attempted=5,
            successful_extractions=4,
            data_quality_score=0.85,
            available_periods=["FY"]
        )

        results = {StatementType.INCOME: income_result}
        report = factory.generate_data_quality_report(results)

        assert "overall_quality_score" in report
        assert "statement_scores" in report
        assert "missing_fields_summary" in report
        assert "recommendations" in report
        assert report["overall_quality_score"] == 0.85

    def test_integrate_with_financial_calculator(self, factory):
        """Test conversion to FinancialCalculator format"""
        income_result = FieldExtractionResult(
            statement_type=StatementType.INCOME,
            company_symbol="MSFT",
            period_type="FY",
            file_path="",
            extracted_fields={
                "revenue": {"FY": 100.0, "FY-1": 90.0},
                "net_income": {"FY": 20.0, "FY-1": 18.0}
            },
            missing_fields=[],
            invalid_fields={},
            total_fields_attempted=2,
            successful_extractions=2,
            data_quality_score=1.0,
            available_periods=["FY", "FY-1"]
        )

        results = {StatementType.INCOME: income_result}
        calculator_data = factory.integrate_with_financial_calculator(results, "MSFT")

        assert calculator_data["company_symbol"] == "MSFT"
        assert "financial_data" in calculator_data
        assert "metadata" in calculator_data
        assert calculator_data["financial_data"]["revenue"] == 100.0  # Latest period
        assert "revenue_history" in calculator_data["financial_data"]


class TestBaseFieldExtractorHelpers:
    """Test BaseFieldExtractor helper methods"""

    @pytest.fixture
    def extractor(self):
        """Create Income Statement extractor for testing base methods"""
        return IncomeStatementExtractor()

    def test_clean_numeric_value_integer(self, extractor):
        """Test cleaning integer values"""
        assert extractor._clean_numeric_value(100) == 100.0
        assert extractor._clean_numeric_value(0) == 0.0

    def test_clean_numeric_value_float(self, extractor):
        """Test cleaning float values"""
        assert extractor._clean_numeric_value(100.5) == 100.5
        assert extractor._clean_numeric_value(0.0) == 0.0

    def test_clean_numeric_value_string(self, extractor):
        """Test cleaning string numeric values"""
        assert extractor._clean_numeric_value("100") == 100.0
        assert extractor._clean_numeric_value("100.5") == 100.5
        assert extractor._clean_numeric_value("$100") == 100.0
        assert extractor._clean_numeric_value("1,000") == 1000.0

    def test_clean_numeric_value_negative_parentheses(self, extractor):
        """Test cleaning negative values in parentheses"""
        assert extractor._clean_numeric_value("(100)") == -100.0
        assert extractor._clean_numeric_value("($100)") == -100.0

    def test_clean_numeric_value_null_indicators(self, extractor):
        """Test cleaning null indicators"""
        assert extractor._clean_numeric_value("") is None
        assert extractor._clean_numeric_value("-") is None
        assert extractor._clean_numeric_value("N/A") is None
        assert extractor._clean_numeric_value("na") is None
        assert extractor._clean_numeric_value("none") is None

    def test_clean_numeric_value_invalid(self, extractor):
        """Test cleaning invalid values"""
        assert extractor._clean_numeric_value("invalid") is None
        assert extractor._clean_numeric_value("abc123") is None

    def test_extract_row_label(self, extractor):
        """Test extracting row labels from Excel rows"""
        # Row with label in first column
        row = ("Total Revenue", 100, 90, 80)
        label = extractor._extract_row_label(row)
        assert label == "Total Revenue"

        # Row with numeric first column, label in second
        row = (None, "Cost of Revenue", 40, 35)
        label = extractor._extract_row_label(row)
        assert label == "Cost of Revenue"

    def test_extract_row_label_skip_dates(self, extractor):
        """Test row label extraction skips dates"""
        row = ("2023", "Net Income", 50, 45)
        label = extractor._extract_row_label(row)
        assert label == "Net Income"  # Should skip "2023"

    def test_find_header_row(self, extractor):
        """Test finding header row in Excel data"""
        data_rows = [
            ("Company Name", None, None),
            ("Financial Statement", None, None),
            ("", "FY", "FY-1", "FY-2"),
            ("Revenue", 100, 90, 80),
            ("Cost of Revenue", 40, 35, 30)
        ]

        header_info = extractor._find_header_row(data_rows)
        assert header_info is not None
        header_row_idx, periods = header_info

        assert header_row_idx == 2
        assert "FY" in periods
        assert "FY-1" in periods
        assert "FY-2" in periods


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
