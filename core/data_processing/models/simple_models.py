"""
Simplified Financial Data Models
=================================

Simplified Pydantic models for demonstration of core functionality
without complex validation logic.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ReportingPeriod(str, Enum):
    """Standard reporting periods for financial statements"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    LTM = "ltm"
    TTM = "ttm"


class Currency(str, Enum):
    """Supported currencies for financial data"""
    USD = "USD"
    EUR = "EUR"
    ILS = "ILS"


class DataSource(str, Enum):
    """Data sources for financial information"""
    EXCEL = "excel"
    YFINANCE = "yfinance"
    FMP = "fmp"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    MANUAL = "manual"


class SimpleFinancialStatementModel(BaseModel):
    """
    Simplified base model for financial statements
    """
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    )

    # Core fields
    company_ticker: str = Field(..., min_length=1, max_length=10)
    company_name: Optional[str] = None
    period_end_date: str
    reporting_period: ReportingPeriod = ReportingPeriod.ANNUAL
    currency: Currency = Currency.USD
    data_source: Optional[DataSource] = None
    fiscal_year: Optional[int] = Field(None, ge=1900, le=2100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class SimpleIncomeStatementModel(SimpleFinancialStatementModel):
    """
    Simplified Income Statement model
    """

    # Core income statement fields
    revenue: Optional[Decimal] = Field(None, ge=0)
    cost_of_revenue: Optional[Decimal] = Field(None, ge=0)
    gross_profit: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    earnings_per_share: Optional[Decimal] = None
    shares_outstanding: Optional[Decimal] = Field(None, gt=0)

    def calculate_gross_profit(self) -> Optional[Decimal]:
        """Calculate gross profit"""
        if self.revenue is not None and self.cost_of_revenue is not None:
            self.gross_profit = self.revenue - self.cost_of_revenue
            return self.gross_profit
        return None

    def calculate_eps(self) -> Optional[Decimal]:
        """Calculate basic EPS"""
        if (self.net_income is not None and
            self.shares_outstanding is not None and
            self.shares_outstanding > 0):
            # Convert shares from millions to actual count
            self.earnings_per_share = self.net_income / (self.shares_outstanding * 1_000_000)
            return self.earnings_per_share
        return None


class SimpleBalanceSheetModel(SimpleFinancialStatementModel):
    """
    Simplified Balance Sheet model
    """

    # Core balance sheet fields
    total_assets: Optional[Decimal] = Field(None, gt=0)
    current_assets: Optional[Decimal] = Field(None, ge=0)
    cash_and_equivalents: Optional[Decimal] = Field(None, ge=0)
    total_liabilities: Optional[Decimal] = Field(None, ge=0)
    current_liabilities: Optional[Decimal] = Field(None, ge=0)
    shareholders_equity: Optional[Decimal] = None
    working_capital: Optional[Decimal] = None

    def calculate_working_capital(self) -> Optional[Decimal]:
        """Calculate working capital"""
        if self.current_assets is not None and self.current_liabilities is not None:
            self.working_capital = self.current_assets - self.current_liabilities
            return self.working_capital
        return None

    def validate_balance_sheet_equation(self) -> bool:
        """Check if Assets = Liabilities + Equity"""
        if all(x is not None for x in [self.total_assets, self.total_liabilities, self.shareholders_equity]):
            expected_assets = self.total_liabilities + self.shareholders_equity
            tolerance = abs(expected_assets * 0.01)  # 1% tolerance
            return abs(self.total_assets - expected_assets) <= tolerance
        return True  # Can't validate without all fields


class SimpleCashFlowStatementModel(SimpleFinancialStatementModel):
    """
    Simplified Cash Flow Statement model
    """

    # Core cash flow fields
    operating_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    net_change_in_cash: Optional[Decimal] = None
    capital_expenditures: Optional[Decimal] = Field(None, ge=0)
    free_cash_flow: Optional[Decimal] = None

    def calculate_free_cash_flow(self) -> Optional[Decimal]:
        """Calculate FCF = Operating CF - CapEx"""
        if self.operating_cash_flow is not None and self.capital_expenditures is not None:
            self.free_cash_flow = self.operating_cash_flow - self.capital_expenditures
            return self.free_cash_flow
        return None

    def calculate_net_change_in_cash(self) -> Optional[Decimal]:
        """Calculate net change from components"""
        if all(x is not None for x in [self.operating_cash_flow, self.investing_cash_flow, self.financing_cash_flow]):
            self.net_change_in_cash = (self.operating_cash_flow +
                                     self.investing_cash_flow +
                                     self.financing_cash_flow)
            return self.net_change_in_cash
        return None