"""
Basic Tests for Financial Data Models
====================================

Simple unit tests to validate that our Pydantic models can be created
and basic functionality works.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal

try:
    from core.data_processing.models.base import BaseFinancialStatementModel, ReportingPeriod, Currency, DataSource
except ImportError as e:
    print(f"Import error: {e}")
    pytest.skip("Models not available", allow_module_level=True)


class TestBasicModelCreation:
    """Test basic model creation functionality"""

    def test_can_create_base_model(self):
        """Test that we can create a basic model"""
        try:
            model = BaseFinancialStatementModel(
                company_ticker="AAPL",
                period_end_date="2023-09-30"
            )
            assert model.company_ticker == "AAPL"
            assert model.period_end_date is not None
            print("✓ Base model creation works")
        except Exception as e:
            print(f"❌ Base model creation failed: {e}")
            raise

    def test_can_use_enums(self):
        """Test that enum values work"""
        try:
            model = BaseFinancialStatementModel(
                company_ticker="AAPL",
                period_end_date="2023-09-30",
                reporting_period=ReportingPeriod.ANNUAL,
                currency=Currency.USD,
                data_source=DataSource.EXCEL
            )
            assert model.reporting_period == ReportingPeriod.ANNUAL
            assert model.currency == Currency.USD
            assert model.data_source == DataSource.EXCEL
            print("✓ Enum handling works")
        except Exception as e:
            print(f"❌ Enum handling failed: {e}")
            raise

    def test_can_set_optional_fields(self):
        """Test setting optional fields"""
        try:
            model = BaseFinancialStatementModel(
                company_ticker="MSFT",
                company_name="Microsoft Corporation",
                period_end_date="2023-06-30",
                fiscal_year=2023,
                notes="Test model"
            )
            assert model.company_name == "Microsoft Corporation"
            assert model.fiscal_year == 2023
            assert model.notes == "Test model"
            print("✓ Optional fields work")
        except Exception as e:
            print(f"❌ Optional fields failed: {e}")
            raise

    def test_model_to_dict(self):
        """Test model conversion to dictionary"""
        try:
            model = BaseFinancialStatementModel(
                company_ticker="GOOGL",
                period_end_date="2023-12-31"
            )

            model_dict = model.model_dump()  # Pydantic v2 syntax
            assert isinstance(model_dict, dict)
            assert model_dict["company_ticker"] == "GOOGL"
            print("✓ Model to dict conversion works")
        except Exception as e:
            print(f"❌ Model to dict failed: {e}")
            raise

if __name__ == "__main__":
    test = TestBasicModelCreation()
    test.test_can_create_base_model()
    test.test_can_use_enums()
    test.test_can_set_optional_fields()
    test.test_model_to_dict()
    print("✅ All basic tests passed!")