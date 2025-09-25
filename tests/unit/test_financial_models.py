"""
Unit Tests for Financial Data Models
====================================

Comprehensive unit tests for Pydantic financial statement models including:
- Field validation rules
- Business logic constraints
- Cross-field validation
- Data quality calculations
- Model factory methods
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError

from core.data_processing.models import (
    BaseFinancialStatementModel,
    IncomeStatementModel,
    BalanceSheetModel,
    CashFlowStatementModel
)
from core.data_processing.models.base import ReportingPeriod, Currency, DataSource


class TestBaseFinancialStatementModel:
    """Test the base financial statement model"""

    def test_valid_base_model_creation(self):
        """Test creating a valid base model"""
        model = BaseFinancialStatementModel(
            company_ticker="AAPL",
            company_name="Apple Inc.",
            period_end_date="2023-09-30",
            reporting_period=ReportingPeriod.ANNUAL,
            currency=Currency.USD,
            fiscal_year=2023
        )

        assert model.company_ticker == "AAPL"
        assert model.company_name == "Apple Inc."
        assert model.reporting_period == ReportingPeriod.ANNUAL
        assert model.currency == Currency.USD
        assert model.fiscal_year == 2023

    def test_ticker_normalization(self):
        """Test that ticker symbols are normalized to uppercase"""
        model = BaseFinancialStatementModel(
            company_ticker="aapl",
            period_end_date="2023-09-30"
        )
        assert model.company_ticker == "AAPL"

    def test_date_parsing(self):
        """Test various date format parsing"""
        # String date format
        model1 = BaseFinancialStatementModel(
            company_ticker="AAPL",
            period_end_date="2023-09-30"
        )
        assert isinstance(model1.period_end_date, date)

        # Datetime object
        model2 = BaseFinancialStatementModel(
            company_ticker="AAPL",
            period_end_date=datetime(2023, 9, 30)
        )
        assert isinstance(model2.period_end_date, date)

    def test_invalid_date_format(self):
        """Test that invalid date formats raise validation error"""
        with pytest.raises(ValidationError):
            BaseFinancialStatementModel(
                company_ticker="AAPL",
                period_end_date="invalid-date"
            )

    def test_fiscal_year_auto_derivation(self):
        """Test that fiscal year is derived from period_end_date if not provided"""
        model = BaseFinancialStatementModel(
            company_ticker="AAPL",
            period_end_date="2023-09-30"
        )
        assert model.fiscal_year == 2023

    def test_data_quality_score_calculation(self):
        """Test basic data quality score calculation"""
        model = BaseFinancialStatementModel(
            company_ticker="AAPL",
            period_end_date="2023-09-30"
        )
        score = model.calculate_data_quality_score()
        assert 0.0 <= score <= 1.0

    def test_timestamp_validation(self):
        """Test that updated_at cannot be before created_at"""
        created = datetime(2023, 1, 1)
        updated = datetime(2022, 12, 31)  # Before created

        with pytest.raises(ValidationError):
            BaseFinancialStatementModel(
                company_ticker="AAPL",
                period_end_date="2023-09-30",
                created_at=created,
                updated_at=updated
            )


class TestIncomeStatementModel:
    """Test the income statement model"""

    @pytest.fixture
    def valid_income_statement_data(self):
        """Sample valid income statement data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "reporting_period": "annual",
            "currency": "USD",
            "revenue": Decimal("394328000000"),
            "cost_of_revenue": Decimal("223546000000"),
            "gross_profit": Decimal("170782000000"),
            "research_development": Decimal("29915000000"),
            "selling_general_admin": Decimal("24932000000"),
            "operating_income": Decimal("114301000000"),
            "interest_expense": Decimal("3933000000"),
            "tax_expense": Decimal("16741000000"),
            "net_income": Decimal("96995000000"),
            "shares_outstanding": Decimal("15728.8"),
            "earnings_per_share": Decimal("6.16"),
            "diluted_eps": Decimal("6.13")
        }

    def test_valid_income_statement_creation(self, valid_income_statement_data):
        """Test creating a valid income statement"""
        model = IncomeStatementModel(**valid_income_statement_data)

        assert model.company_ticker == "AAPL"
        assert model.revenue == Decimal("394328000000")
        assert model.net_income == Decimal("96995000000")
        assert model.earnings_per_share == Decimal("6.16")

    def test_gross_profit_validation(self, valid_income_statement_data):
        """Test gross profit calculation validation"""
        # Correct gross profit should pass
        model = IncomeStatementModel(**valid_income_statement_data)
        assert model.gross_profit == model.revenue - model.cost_of_revenue

        # Incorrect gross profit should fail
        invalid_data = valid_income_statement_data.copy()
        invalid_data["gross_profit"] = Decimal("100000000000")  # Wrong value

        with pytest.raises(ValidationError, match="Gross profit validation failed"):
            IncomeStatementModel(**invalid_data)

    def test_negative_revenue_validation(self, valid_income_statement_data):
        """Test that negative revenue raises validation error"""
        invalid_data = valid_income_statement_data.copy()
        invalid_data["revenue"] = Decimal("-1000000")

        with pytest.raises(ValidationError):
            IncomeStatementModel(**invalid_data)

    def test_alias_fields(self, valid_income_statement_data):
        """Test that alias fields are properly set"""
        model = IncomeStatementModel(**valid_income_statement_data)

        # Test aliases are set correctly
        assert model.total_revenue == model.revenue
        assert model.ebit == model.operating_income
        assert model.basic_eps == model.earnings_per_share

    def test_profit_margin_calculations(self, valid_income_statement_data):
        """Test profit margin calculations"""
        model = IncomeStatementModel(**valid_income_statement_data)
        margins = model.get_profit_margins()

        assert "gross_margin" in margins
        assert "operating_margin" in margins
        assert "net_margin" in margins

        # Check calculated values make sense
        expected_gross_margin = float(model.gross_profit / model.revenue)
        assert abs(margins["gross_margin"] - expected_gross_margin) < 0.001

    def test_eps_calculation(self, valid_income_statement_data):
        """Test EPS calculation method"""
        model = IncomeStatementModel(**valid_income_statement_data)
        calculated_eps = model.calculate_eps()

        assert calculated_eps is not None
        # Allow for small rounding differences
        assert abs(calculated_eps - Decimal("6.16")) < Decimal("0.1")

    def test_data_quality_score(self, valid_income_statement_data):
        """Test data quality score calculation for income statement"""
        model = IncomeStatementModel(**valid_income_statement_data)
        score = model.calculate_data_quality_score()

        assert 0.0 <= score <= 1.0
        # Should be high quality with all required fields
        assert score > 0.8


class TestBalanceSheetModel:
    """Test the balance sheet model"""

    @pytest.fixture
    def valid_balance_sheet_data(self):
        """Sample valid balance sheet data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "reporting_period": "annual",
            "currency": "USD",
            "current_assets": Decimal("143566000000"),
            "cash_and_equivalents": Decimal("29965000000"),
            "accounts_receivable": Decimal("29508000000"),
            "inventory": Decimal("6331000000"),
            "property_plant_equipment": Decimal("43715000000"),
            "long_term_investments": Decimal("100544000000"),
            "total_assets": Decimal("352755000000"),
            "current_liabilities": Decimal("145308000000"),
            "accounts_payable": Decimal("62611000000"),
            "short_term_debt": Decimal("9822000000"),
            "long_term_debt": Decimal("95281000000"),
            "total_liabilities": Decimal("290437000000"),
            "shareholders_equity": Decimal("62318000000"),
            "retained_earnings": Decimal("164399000000")
        }

    def test_valid_balance_sheet_creation(self, valid_balance_sheet_data):
        """Test creating a valid balance sheet"""
        model = BalanceSheetModel(**valid_balance_sheet_data)

        assert model.company_ticker == "AAPL"
        assert model.total_assets == Decimal("352755000000")
        assert model.shareholders_equity == Decimal("62318000000")

    def test_balance_sheet_equation_validation(self, valid_balance_sheet_data):
        """Test the fundamental accounting equation validation"""
        # Valid balance sheet should pass
        model = BalanceSheetModel(**valid_balance_sheet_data)
        expected_assets = model.total_liabilities + model.shareholders_equity
        assert abs(model.total_assets - expected_assets) < 1000  # Allow small rounding

        # Invalid balance sheet should fail
        invalid_data = valid_balance_sheet_data.copy()
        invalid_data["total_assets"] = Decimal("999999999999")  # Way off

        with pytest.raises(ValidationError, match="Balance sheet equation failed"):
            BalanceSheetModel(**invalid_data)

    def test_working_capital_calculation(self, valid_balance_sheet_data):
        """Test working capital calculation"""
        model = BalanceSheetModel(**valid_balance_sheet_data)
        working_capital = model.calculate_working_capital()

        expected = model.current_assets - model.current_liabilities
        assert working_capital == expected

    def test_liquidity_ratios(self, valid_balance_sheet_data):
        """Test liquidity ratio calculations"""
        model = BalanceSheetModel(**valid_balance_sheet_data)
        ratios = model.get_liquidity_ratios()

        assert "current_ratio" in ratios
        assert "quick_ratio" in ratios
        assert "cash_ratio" in ratios

        # Current ratio should be positive for Apple
        assert ratios["current_ratio"] > 0

    def test_leverage_ratios(self, valid_balance_sheet_data):
        """Test leverage ratio calculations"""
        model = BalanceSheetModel(**valid_balance_sheet_data)
        ratios = model.get_leverage_ratios()

        assert "debt_to_equity" in ratios
        assert "debt_to_assets" in ratios

        # All ratios should be positive
        assert all(ratio >= 0 for ratio in ratios.values() if ratio is not None)

    def test_negative_equity_warning(self, valid_balance_sheet_data):
        """Test warning for negative shareholders' equity"""
        invalid_data = valid_balance_sheet_data.copy()
        invalid_data["shareholders_equity"] = Decimal("-10000000000")
        # Adjust total assets to maintain balance sheet equation
        invalid_data["total_assets"] = Decimal("280437000000")

        model = BalanceSheetModel(**invalid_data)
        validation_results = model.validate_balance_sheet_structure()

        assert len(validation_results["warnings"]) > 0
        assert "negative shareholders' equity" in validation_results["warnings"][0].lower()

    def test_data_quality_score(self, valid_balance_sheet_data):
        """Test data quality score for balance sheet"""
        model = BalanceSheetModel(**valid_balance_sheet_data)
        score = model.calculate_data_quality_score()

        assert 0.0 <= score <= 1.0
        # Should be high quality with all required fields and valid equation
        assert score > 0.9


class TestCashFlowStatementModel:
    """Test the cash flow statement model"""

    @pytest.fixture
    def valid_cash_flow_data(self):
        """Sample valid cash flow statement data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "reporting_period": "annual",
            "currency": "USD",
            "operating_cash_flow": Decimal("110543000000"),
            "net_income": Decimal("96995000000"),
            "depreciation_amortization": Decimal("11519000000"),
            "change_in_working_capital": Decimal("1068000000"),
            "investing_cash_flow": Decimal("-3705000000"),
            "capital_expenditures": Decimal("10959000000"),
            "financing_cash_flow": Decimal("-108488000000"),
            "dividends_paid": Decimal("15025000000"),
            "share_repurchases": Decimal("77550000000"),
            "net_change_in_cash": Decimal("-1650000000"),
            "cash_beginning_period": Decimal("31615000000"),
            "cash_end_period": Decimal("29965000000")
        }

    def test_valid_cash_flow_creation(self, valid_cash_flow_data):
        """Test creating a valid cash flow statement"""
        model = CashFlowStatementModel(**valid_cash_flow_data)

        assert model.company_ticker == "AAPL"
        assert model.operating_cash_flow == Decimal("110543000000")
        assert model.capital_expenditures == Decimal("10959000000")

    def test_cash_flow_reconciliation(self, valid_cash_flow_data):
        """Test cash flow reconciliation validation"""
        # Valid cash flows should pass
        model = CashFlowStatementModel(**valid_cash_flow_data)
        calculated_change = (model.operating_cash_flow +
                           model.investing_cash_flow +
                           model.financing_cash_flow)

        # Allow for small rounding differences
        assert abs(model.net_change_in_cash - calculated_change) < Decimal("1000")

        # Invalid reconciliation should fail
        invalid_data = valid_cash_flow_data.copy()
        invalid_data["net_change_in_cash"] = Decimal("999999999")  # Way off

        with pytest.raises(ValidationError, match="Cash flow reconciliation failed"):
            CashFlowStatementModel(**invalid_data)

    def test_cash_reconciliation(self, valid_cash_flow_data):
        """Test beginning + change = ending cash validation"""
        model = CashFlowStatementModel(**valid_cash_flow_data)

        expected_end = model.cash_beginning_period + model.net_change_in_cash
        assert abs(model.cash_end_period - expected_end) < Decimal("1000")

    def test_free_cash_flow_calculation(self, valid_cash_flow_data):
        """Test FCF calculation"""
        model = CashFlowStatementModel(**valid_cash_flow_data)
        fcf = model.calculate_free_cash_flow()

        expected_fcf = model.operating_cash_flow - model.capital_expenditures
        assert fcf == expected_fcf

    def test_fcf_variants(self, valid_cash_flow_data):
        """Test different FCF calculation variants"""
        model = CashFlowStatementModel(**valid_cash_flow_data)

        # Calculate basic FCF first
        model.calculate_free_cash_flow()

        # Test FCFE calculation
        fcfe = model.calculate_fcfe(net_debt_payments=Decimal("5000000000"))
        assert fcfe is not None

        # Test Levered FCF calculation
        levered_fcf = model.calculate_levered_fcf()
        assert levered_fcf == model.free_cash_flow

    def test_cash_flow_ratios(self, valid_cash_flow_data):
        """Test cash flow ratio calculations"""
        # Add revenue for ratio calculations
        valid_cash_flow_data["revenue"] = Decimal("394328000000")
        model = CashFlowStatementModel(**valid_cash_flow_data)

        ratios = model.get_cash_flow_ratios()

        assert "operating_cf_margin" in ratios
        if model.free_cash_flow:
            assert "fcf_margin" in ratios

    def test_cash_flow_quality_assessment(self, valid_cash_flow_data):
        """Test cash flow quality metrics"""
        model = CashFlowStatementModel(**valid_cash_flow_data)
        quality = model.validate_cash_flow_quality()

        assert "quality_score" in quality
        assert "red_flags" in quality
        assert "positive_indicators" in quality
        assert 0.0 <= quality["quality_score"] <= 1.0

    def test_negative_values_validation(self, valid_cash_flow_data):
        """Test that appropriate fields can have negative values"""
        # Investing and financing cash flows can be negative
        model = CashFlowStatementModel(**valid_cash_flow_data)
        assert model.investing_cash_flow < 0  # Should be allowed
        assert model.financing_cash_flow < 0  # Should be allowed

        # But capital expenditures should be positive (represents cash outflow)
        invalid_data = valid_cash_flow_data.copy()
        invalid_data["capital_expenditures"] = Decimal("-10000000")

        with pytest.raises(ValidationError):
            CashFlowStatementModel(**invalid_data)

    def test_data_quality_score(self, valid_cash_flow_data):
        """Test data quality score for cash flow statement"""
        model = CashFlowStatementModel(**valid_cash_flow_data)
        score = model.calculate_data_quality_score()

        assert 0.0 <= score <= 1.0
        # Should be high quality with reconciliation and FCF
        assert score > 0.8


class TestModelFactoryMethods:
    """Test factory methods and model utilities"""

    def test_create_from_dict(self):
        """Test creating models from dictionary data"""
        data = {
            "company_ticker": "msft",
            "period_end_date": "2023-06-30",
            "revenue": 211915000000,
            "net_income": 72361000000
        }

        model = IncomeStatementModel.create_from_dict(data)
        assert model.company_ticker == "MSFT"  # Should be normalized
        assert model.revenue == Decimal("211915000000")

    def test_to_dict_method(self):
        """Test model to dictionary conversion"""
        model = BaseFinancialStatementModel(
            company_ticker="GOOGL",
            period_end_date="2023-12-31"
        )

        dict_data = model.to_dict()
        assert dict_data["company_ticker"] == "GOOGL"
        assert "period_end_date" in dict_data

    def test_update_timestamp(self):
        """Test timestamp update functionality"""
        model = BaseFinancialStatementModel(
            company_ticker="TSLA",
            period_end_date="2023-12-31"
        )

        original_updated = model.updated_at
        model.update_timestamp()

        assert model.updated_at != original_updated
        assert model.updated_at > model.created_at


class TestIntegrationScenarios:
    """Test integration scenarios with multiple models"""

    def test_complete_financial_statements(self):
        """Test creating complete set of financial statements"""
        base_data = {
            "company_ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "period_end_date": "2024-01-31",
            "reporting_period": "annual",
            "currency": "USD",
            "fiscal_year": 2024
        }

        # Income Statement
        income_data = {
            **base_data,
            "revenue": Decimal("60922000000"),
            "cost_of_revenue": Decimal("16621000000"),
            "gross_profit": Decimal("44301000000"),
            "net_income": Decimal("29760000000")
        }
        income_stmt = IncomeStatementModel(**income_data)

        # Balance Sheet
        balance_data = {
            **base_data,
            "total_assets": Decimal("65728000000"),
            "total_liabilities": Decimal("19081000000"),
            "shareholders_equity": Decimal("46647000000")
        }
        balance_sheet = BalanceSheetModel(**balance_data)

        # Cash Flow
        cash_flow_data = {
            **base_data,
            "operating_cash_flow": Decimal("28090000000"),
            "investing_cash_flow": Decimal("-1043000000"),
            "financing_cash_flow": Decimal("-25977000000"),
            "net_change_in_cash": Decimal("1070000000"),
            "capital_expenditures": Decimal("1069000000")
        }
        cash_flow_stmt = CashFlowStatementModel(**cash_flow_data)

        # Verify all models created successfully
        assert income_stmt.company_ticker == "NVDA"
        assert balance_sheet.company_ticker == "NVDA"
        assert cash_flow_stmt.company_ticker == "NVDA"

        # Test cross-statement consistency
        assert income_stmt.net_income == cash_flow_stmt.net_income

    def test_error_handling_edge_cases(self):
        """Test various error handling scenarios"""
        # Empty ticker
        with pytest.raises(ValidationError):
            BaseFinancialStatementModel(
                company_ticker="",
                period_end_date="2023-12-31"
            )

        # Very large numbers
        large_number = Decimal("999999999999999999999")
        model = IncomeStatementModel(
            company_ticker="TEST",
            period_end_date="2023-12-31",
            revenue=large_number
        )
        assert model.revenue == large_number

        # Test with zero values
        zero_equity_model = BalanceSheetModel(
            company_ticker="TEST",
            period_end_date="2023-12-31",
            total_assets=Decimal("100000"),
            total_liabilities=Decimal("100000"),
            shareholders_equity=Decimal("0")
        )
        assert zero_equity_model.shareholders_equity == Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])