"""
Tests for Simplified Financial Data Models
==========================================

Unit tests for the simplified Pydantic financial statement models.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from core.data_processing.models.simple_models import (
    SimpleFinancialStatementModel,
    SimpleIncomeStatementModel,
    SimpleBalanceSheetModel,
    SimpleCashFlowStatementModel,
    ReportingPeriod,
    Currency,
    DataSource
)


class TestSimpleFinancialStatementModel:
    """Test the simplified base financial statement model"""

    def test_valid_model_creation(self):
        """Test creating a valid base model"""
        model = SimpleFinancialStatementModel(
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

    def test_required_fields(self):
        """Test that required fields are enforced"""
        # Should fail without ticker
        with pytest.raises(Exception):
            SimpleFinancialStatementModel(period_end_date="2023-09-30")

        # Should fail without period_end_date
        with pytest.raises(Exception):
            SimpleFinancialStatementModel(company_ticker="AAPL")

    def test_model_serialization(self):
        """Test model to dict conversion"""
        model = SimpleFinancialStatementModel(
            company_ticker="MSFT",
            period_end_date="2023-06-30"
        )

        data = model.model_dump()
        assert isinstance(data, dict)
        assert data["company_ticker"] == "MSFT"
        assert "created_at" in data


class TestSimpleIncomeStatementModel:
    """Test the simplified income statement model"""

    @pytest.fixture
    def sample_income_data(self):
        """Sample income statement data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "revenue": Decimal("394328000000"),
            "cost_of_revenue": Decimal("223546000000"),
            "net_income": Decimal("96995000000"),
            "shares_outstanding": Decimal("15728.8")  # in millions
        }

    def test_income_statement_creation(self, sample_income_data):
        """Test creating an income statement model"""
        model = SimpleIncomeStatementModel(**sample_income_data)

        assert model.revenue == Decimal("394328000000")
        assert model.cost_of_revenue == Decimal("223546000000")
        assert model.net_income == Decimal("96995000000")

    def test_gross_profit_calculation(self, sample_income_data):
        """Test gross profit calculation"""
        model = SimpleIncomeStatementModel(**sample_income_data)
        gross_profit = model.calculate_gross_profit()

        expected = model.revenue - model.cost_of_revenue
        assert gross_profit == expected
        assert model.gross_profit == expected

    def test_eps_calculation(self, sample_income_data):
        """Test EPS calculation"""
        model = SimpleIncomeStatementModel(**sample_income_data)
        eps = model.calculate_eps()

        assert eps is not None
        assert eps > 0
        # Verify calculation: net_income / (shares_outstanding * 1M)
        expected_eps = model.net_income / (model.shares_outstanding * 1_000_000)
        assert abs(eps - expected_eps) < Decimal("0.01")

    def test_negative_revenue_validation(self, sample_income_data):
        """Test that negative revenue is rejected"""
        sample_income_data["revenue"] = Decimal("-1000000")

        with pytest.raises(Exception):
            SimpleIncomeStatementModel(**sample_income_data)


class TestSimpleBalanceSheetModel:
    """Test the simplified balance sheet model"""

    @pytest.fixture
    def sample_balance_data(self):
        """Sample balance sheet data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "total_assets": Decimal("352755000000"),
            "current_assets": Decimal("143566000000"),
            "cash_and_equivalents": Decimal("29965000000"),
            "total_liabilities": Decimal("290437000000"),
            "current_liabilities": Decimal("145308000000"),
            "shareholders_equity": Decimal("62318000000")
        }

    def test_balance_sheet_creation(self, sample_balance_data):
        """Test creating a balance sheet model"""
        model = SimpleBalanceSheetModel(**sample_balance_data)

        assert model.total_assets == Decimal("352755000000")
        assert model.shareholders_equity == Decimal("62318000000")

    def test_working_capital_calculation(self, sample_balance_data):
        """Test working capital calculation"""
        model = SimpleBalanceSheetModel(**sample_balance_data)
        working_capital = model.calculate_working_capital()

        expected = model.current_assets - model.current_liabilities
        assert working_capital == expected
        assert model.working_capital == expected

    def test_balance_sheet_equation_validation(self, sample_balance_data):
        """Test balance sheet equation validation"""
        model = SimpleBalanceSheetModel(**sample_balance_data)
        is_valid = model.validate_balance_sheet_equation()

        assert is_valid is True

        # Test with invalid equation
        model.total_assets = Decimal("999999999999")  # Way off
        is_valid = model.validate_balance_sheet_equation()
        assert is_valid is False

    def test_negative_total_assets_validation(self, sample_balance_data):
        """Test that negative total assets is rejected"""
        sample_balance_data["total_assets"] = Decimal("-1000000")

        with pytest.raises(Exception):
            SimpleBalanceSheetModel(**sample_balance_data)


class TestSimpleCashFlowStatementModel:
    """Test the simplified cash flow statement model"""

    @pytest.fixture
    def sample_cash_flow_data(self):
        """Sample cash flow statement data"""
        return {
            "company_ticker": "AAPL",
            "company_name": "Apple Inc.",
            "period_end_date": "2023-09-30",
            "operating_cash_flow": Decimal("110543000000"),
            "investing_cash_flow": Decimal("-3705000000"),
            "financing_cash_flow": Decimal("-108488000000"),
            "capital_expenditures": Decimal("10959000000")
        }

    def test_cash_flow_creation(self, sample_cash_flow_data):
        """Test creating a cash flow model"""
        model = SimpleCashFlowStatementModel(**sample_cash_flow_data)

        assert model.operating_cash_flow == Decimal("110543000000")
        assert model.capital_expenditures == Decimal("10959000000")

    def test_free_cash_flow_calculation(self, sample_cash_flow_data):
        """Test FCF calculation"""
        model = SimpleCashFlowStatementModel(**sample_cash_flow_data)
        fcf = model.calculate_free_cash_flow()

        expected = model.operating_cash_flow - model.capital_expenditures
        assert fcf == expected
        assert model.free_cash_flow == expected

    def test_net_change_calculation(self, sample_cash_flow_data):
        """Test net change in cash calculation"""
        model = SimpleCashFlowStatementModel(**sample_cash_flow_data)
        net_change = model.calculate_net_change_in_cash()

        expected = (model.operating_cash_flow +
                   model.investing_cash_flow +
                   model.financing_cash_flow)
        assert net_change == expected
        assert model.net_change_in_cash == expected

    def test_negative_capex_validation(self, sample_cash_flow_data):
        """Test that negative CapEx is rejected"""
        sample_cash_flow_data["capital_expenditures"] = Decimal("-1000000")

        with pytest.raises(Exception):
            SimpleCashFlowStatementModel(**sample_cash_flow_data)


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_complete_financial_statements(self):
        """Test creating a complete set of financial statements"""
        base_data = {
            "company_ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "period_end_date": "2024-01-31",
            "reporting_period": "annual",
            "currency": "USD",
            "fiscal_year": 2024
        }

        # Create income statement
        income_data = {
            **base_data,
            "revenue": Decimal("60922000000"),
            "cost_of_revenue": Decimal("16621000000"),
            "net_income": Decimal("29760000000")
        }
        income_stmt = SimpleIncomeStatementModel(**income_data)

        # Create balance sheet
        balance_data = {
            **base_data,
            "total_assets": Decimal("65728000000"),
            "total_liabilities": Decimal("19081000000"),
            "shareholders_equity": Decimal("46647000000")
        }
        balance_sheet = SimpleBalanceSheetModel(**balance_data)

        # Create cash flow
        cash_flow_data = {
            **base_data,
            "operating_cash_flow": Decimal("28090000000"),
            "investing_cash_flow": Decimal("-1043000000"),
            "financing_cash_flow": Decimal("-25977000000"),
            "capital_expenditures": Decimal("1069000000")
        }
        cash_flow_stmt = SimpleCashFlowStatementModel(**cash_flow_data)

        # Verify all models created successfully
        assert income_stmt.company_ticker == "NVDA"
        assert balance_sheet.company_ticker == "NVDA"
        assert cash_flow_stmt.company_ticker == "NVDA"

        # Test calculations work
        income_stmt.calculate_gross_profit()
        balance_sheet.calculate_working_capital()
        cash_flow_stmt.calculate_free_cash_flow()

        assert income_stmt.gross_profit is not None
        assert cash_flow_stmt.free_cash_flow is not None

    def test_model_serialization_roundtrip(self):
        """Test serializing and deserializing models"""
        original = SimpleIncomeStatementModel(
            company_ticker="TEST",
            period_end_date="2023-12-31",
            revenue=Decimal("1000000"),
            net_income=Decimal("100000")
        )

        # Serialize to dict
        data = original.model_dump()

        # Recreate from dict
        recreated = SimpleIncomeStatementModel(**data)

        # Verify they match
        assert recreated.company_ticker == original.company_ticker
        assert recreated.revenue == original.revenue
        assert recreated.net_income == original.net_income


if __name__ == "__main__":
    pytest.main([__file__, "-v"])