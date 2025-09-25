"""
Income Statement Pydantic Model
===============================

Comprehensive Pydantic model for Income Statement data with validation rules
and business logic constraints.

This model includes:
- All standard income statement line items
- Revenue recognition validation
- Profitability metrics calculation
- Cross-field validation for statement integrity
- Per-share metrics calculation support
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import Field, field_validator, model_validator
from typing import Annotated

from .base import BaseFinancialStatementModel


class IncomeStatementModel(BaseFinancialStatementModel):
    """
    Comprehensive Income Statement model with validation and business logic
    """

    # === REVENUE SECTION ===
    revenue: Optional[Annotated[Decimal, Field(ge=0)]] = Field(
        None,
        description="Total revenue/net sales",
        example=394328000000.0
    )

    total_revenue: Optional[Annotated[Decimal, Field(ge=0)]] = Field(
        None,
        description="Total revenue (alias for revenue)",
        example=394328000000.0
    )

    gross_revenue: Optional[Annotated[Decimal, Field(ge=0)]] = Field(
        None,
        description="Gross revenue before returns and allowances"
    )

    # === COST SECTION ===
    cost_of_revenue: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cost of goods sold/Cost of revenue",
        example=223546000000.0
    )

    cost_of_goods_sold: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cost of goods sold (alias for cost_of_revenue)",
        example=223546000000.0
    )

    # === GROSS PROFIT ===
    gross_profit: Optional[Decimal] = Field(
        None,
        description="Gross profit (Revenue - Cost of Revenue)",
        example=170782000000.0
    )

    # === OPERATING EXPENSES ===
    operating_expenses: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total operating expenses"
    )

    research_development: Optional[condecimal(ge=0)] = Field(
        None,
        description="Research and development expenses",
        example=29915000000.0
    )

    selling_general_admin: Optional[condecimal(ge=0)] = Field(
        None,
        description="Selling, General & Administrative expenses",
        example=24932000000.0
    )

    marketing_expenses: Optional[condecimal(ge=0)] = Field(
        None,
        description="Marketing and advertising expenses"
    )

    # === OPERATING INCOME ===
    operating_income: Optional[Decimal] = Field(
        None,
        description="Operating income/EBIT",
        example=114301000000.0
    )

    ebit: Optional[Decimal] = Field(
        None,
        description="Earnings Before Interest and Taxes (alias for operating_income)"
    )

    ebitda: Optional[Decimal] = Field(
        None,
        description="Earnings Before Interest, Taxes, Depreciation, and Amortization"
    )

    # === NON-OPERATING ITEMS ===
    interest_income: Optional[Decimal] = Field(
        None,
        description="Interest income from investments"
    )

    interest_expense: Optional[condecimal(ge=0)] = Field(
        None,
        description="Interest expense on debt",
        example=3933000000.0
    )

    other_income: Optional[Decimal] = Field(
        None,
        description="Other non-operating income/expenses"
    )

    # === PRE-TAX INCOME ===
    income_before_taxes: Optional[Decimal] = Field(
        None,
        description="Income before income taxes"
    )

    # === TAX EXPENSES ===
    tax_expense: Optional[condecimal(ge=0)] = Field(
        None,
        description="Income tax expense",
        example=16741000000.0
    )

    income_tax_expense: Optional[condecimal(ge=0)] = Field(
        None,
        description="Income tax expense (alias for tax_expense)"
    )

    tax_rate: Optional[condecimal(ge=0, le=1)] = Field(
        None,
        description="Effective tax rate (as decimal, 0.21 = 21%)"
    )

    # === NET INCOME ===
    net_income: Optional[Decimal] = Field(
        None,
        description="Net income after all expenses and taxes",
        example=96995000000.0
    )

    net_earnings: Optional[Decimal] = Field(
        None,
        description="Net earnings (alias for net_income)"
    )

    # === SHARE INFORMATION ===
    shares_outstanding: Optional[condecimal(gt=0)] = Field(
        None,
        description="Shares outstanding (in millions)",
        example=15728.8
    )

    weighted_avg_shares: Optional[condecimal(gt=0)] = Field(
        None,
        description="Weighted average shares outstanding (in millions)"
    )

    # === PER-SHARE METRICS ===
    earnings_per_share: Optional[Decimal] = Field(
        None,
        description="Basic earnings per share",
        example=6.16
    )

    basic_eps: Optional[Decimal] = Field(
        None,
        description="Basic EPS (alias for earnings_per_share)"
    )

    diluted_eps: Optional[Decimal] = Field(
        None,
        description="Diluted earnings per share",
        example=6.13
    )

    # === DEPRECIATION AND AMORTIZATION ===
    depreciation_amortization: Optional[condecimal(ge=0)] = Field(
        None,
        description="Depreciation and amortization expense"
    )

    depreciation: Optional[condecimal(ge=0)] = Field(
        None,
        description="Depreciation expense"
    )

    amortization: Optional[condecimal(ge=0)] = Field(
        None,
        description="Amortization expense"
    )

    class Config:
        schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "company_name": "Apple Inc.",
                "period_end_date": "2023-09-30",
                "reporting_period": "annual",
                "currency": "USD",
                "revenue": 394328000000.0,
                "cost_of_revenue": 223546000000.0,
                "gross_profit": 170782000000.0,
                "research_development": 29915000000.0,
                "selling_general_admin": 24932000000.0,
                "operating_income": 114301000000.0,
                "interest_expense": 3933000000.0,
                "tax_expense": 16741000000.0,
                "net_income": 96995000000.0,
                "shares_outstanding": 15728.8,
                "earnings_per_share": 6.16,
                "diluted_eps": 6.13
            }
        }

    @validator('total_revenue', pre=True, always=True)
    def set_total_revenue(cls, v, values):
        """Set total_revenue as alias for revenue if not provided"""
        if v is None and 'revenue' in values and values['revenue'] is not None:
            return values['revenue']
        return v

    @validator('cost_of_goods_sold', pre=True, always=True)
    def set_cogs_alias(cls, v, values):
        """Set COGS as alias for cost_of_revenue if not provided"""
        if v is None and 'cost_of_revenue' in values and values['cost_of_revenue'] is not None:
            return values['cost_of_revenue']
        return v

    @validator('ebit', pre=True, always=True)
    def set_ebit_alias(cls, v, values):
        """Set EBIT as alias for operating_income if not provided"""
        if v is None and 'operating_income' in values and values['operating_income'] is not None:
            return values['operating_income']
        return v

    @validator('net_earnings', pre=True, always=True)
    def set_net_earnings_alias(cls, v, values):
        """Set net_earnings as alias for net_income if not provided"""
        if v is None and 'net_income' in values and values['net_income'] is not None:
            return values['net_income']
        return v

    @validator('basic_eps', pre=True, always=True)
    def set_basic_eps_alias(cls, v, values):
        """Set basic_eps as alias for earnings_per_share if not provided"""
        if v is None and 'earnings_per_share' in values and values['earnings_per_share'] is not None:
            return values['earnings_per_share']
        return v

    @validator('income_tax_expense', pre=True, always=True)
    def set_tax_alias(cls, v, values):
        """Set income_tax_expense as alias for tax_expense if not provided"""
        if v is None and 'tax_expense' in values and values['tax_expense'] is not None:
            return values['tax_expense']
        return v

    @root_validator
    def validate_income_statement_integrity(cls, values):
        """Validate income statement mathematical relationships"""
        revenue = values.get('revenue')
        cost_of_revenue = values.get('cost_of_revenue')
        gross_profit = values.get('gross_profit')
        operating_income = values.get('operating_income')
        tax_expense = values.get('tax_expense')
        net_income = values.get('net_income')
        income_before_taxes = values.get('income_before_taxes')

        # Validate gross profit calculation: Gross Profit = Revenue - Cost of Revenue
        if all(x is not None for x in [revenue, cost_of_revenue, gross_profit]):
            expected_gross_profit = revenue - cost_of_revenue
            tolerance = abs(expected_gross_profit * 0.01)  # 1% tolerance for rounding
            if abs(gross_profit - expected_gross_profit) > tolerance:
                raise ValueError(
                    f"Gross profit validation failed: "
                    f"Expected {expected_gross_profit}, got {gross_profit}"
                )

        # Validate net income after taxes: Net Income = Income Before Taxes - Tax Expense
        if all(x is not None for x in [income_before_taxes, tax_expense, net_income]):
            expected_net_income = income_before_taxes - tax_expense
            tolerance = abs(expected_net_income * 0.01)  # 1% tolerance
            if abs(net_income - expected_net_income) > tolerance:
                raise ValueError(
                    f"Net income validation failed: "
                    f"Expected {expected_net_income}, got {net_income}"
                )

        # Validate EPS calculation if shares outstanding is available
        shares = values.get('weighted_avg_shares') or values.get('shares_outstanding')
        eps = values.get('earnings_per_share')
        if all(x is not None for x in [net_income, shares, eps]) and shares > 0:
            expected_eps = net_income / (shares * 1_000_000)  # Convert millions to actual shares
            tolerance = abs(expected_eps * 0.05)  # 5% tolerance for EPS
            if abs(eps - expected_eps) > tolerance:
                # This is a warning, not an error, as EPS calculations can vary
                values['notes'] = f"EPS calculation variance detected. Expected {expected_eps:.2f}, got {eps:.2f}"

        return values

    def calculate_gross_profit(self) -> Optional[Decimal]:
        """Calculate gross profit from revenue and cost of revenue"""
        if self.revenue is not None and self.cost_of_revenue is not None:
            self.gross_profit = self.revenue - self.cost_of_revenue
            return self.gross_profit
        return None

    def calculate_operating_income(self) -> Optional[Decimal]:
        """Calculate operating income from gross profit and operating expenses"""
        if self.gross_profit is not None and self.operating_expenses is not None:
            self.operating_income = self.gross_profit - self.operating_expenses
            self.ebit = self.operating_income  # Set alias
            return self.operating_income
        return None

    def calculate_income_before_taxes(self) -> Optional[Decimal]:
        """Calculate income before taxes"""
        if self.operating_income is not None:
            non_operating = Decimal(0)
            if self.interest_income is not None:
                non_operating += self.interest_income
            if self.interest_expense is not None:
                non_operating -= self.interest_expense
            if self.other_income is not None:
                non_operating += self.other_income

            self.income_before_taxes = self.operating_income + non_operating
            return self.income_before_taxes
        return None

    def calculate_net_income(self) -> Optional[Decimal]:
        """Calculate net income from income before taxes and tax expense"""
        if self.income_before_taxes is not None and self.tax_expense is not None:
            self.net_income = self.income_before_taxes - self.tax_expense
            self.net_earnings = self.net_income  # Set alias
            return self.net_income
        return None

    def calculate_eps(self, use_diluted_shares: bool = False) -> Optional[Decimal]:
        """Calculate earnings per share"""
        if self.net_income is not None:
            shares = self.weighted_avg_shares or self.shares_outstanding
            if shares is not None and shares > 0:
                # Convert millions to actual shares for calculation
                eps = self.net_income / (shares * 1_000_000)
                if use_diluted_shares:
                    self.diluted_eps = eps
                else:
                    self.earnings_per_share = eps
                    self.basic_eps = eps
                return eps
        return None

    def calculate_effective_tax_rate(self) -> Optional[Decimal]:
        """Calculate effective tax rate"""
        if self.income_before_taxes is not None and self.tax_expense is not None:
            if self.income_before_taxes != 0:
                self.tax_rate = self.tax_expense / self.income_before_taxes
                return self.tax_rate
        return None

    def calculate_ebitda(self) -> Optional[Decimal]:
        """Calculate EBITDA by adding depreciation and amortization to EBIT"""
        if self.operating_income is not None:
            ebitda = self.operating_income
            if self.depreciation_amortization is not None:
                ebitda += self.depreciation_amortization
            elif self.depreciation is not None and self.amortization is not None:
                ebitda += (self.depreciation + self.amortization)

            self.ebitda = ebitda
            return self.ebitda
        return None

    def get_profit_margins(self) -> Dict[str, Optional[float]]:
        """Calculate various profit margin ratios"""
        margins = {}

        if self.revenue is not None and self.revenue > 0:
            # Gross margin
            if self.gross_profit is not None:
                margins['gross_margin'] = float(self.gross_profit / self.revenue)

            # Operating margin
            if self.operating_income is not None:
                margins['operating_margin'] = float(self.operating_income / self.revenue)

            # Net margin
            if self.net_income is not None:
                margins['net_margin'] = float(self.net_income / self.revenue)

            # EBITDA margin
            if self.ebitda is not None:
                margins['ebitda_margin'] = float(self.ebitda / self.revenue)

        return margins

    def calculate_data_quality_score(self) -> float:
        """Calculate data quality score for income statement"""
        required_fields = [
            'revenue', 'cost_of_revenue', 'gross_profit',
            'operating_income', 'net_income', 'shares_outstanding'
        ]

        missing_count = sum(1 for field in required_fields
                           if getattr(self, field, None) is None)

        # Base completeness score
        completeness_score = 1.0 - (missing_count / len(required_fields))

        # Bonus points for having detailed breakdown
        detail_fields = [
            'research_development', 'selling_general_admin',
            'interest_expense', 'tax_expense', 'earnings_per_share'
        ]
        detail_count = sum(1 for field in detail_fields
                          if getattr(self, field, None) is not None)
        detail_bonus = min(0.1, detail_count * 0.02)

        # Penalty for mathematical inconsistencies (if we can detect them)
        consistency_penalty = 0.0
        if self.revenue and self.cost_of_revenue and self.gross_profit:
            expected_gross = self.revenue - self.cost_of_revenue
            if abs(self.gross_profit - expected_gross) / expected_gross > 0.05:
                consistency_penalty = 0.1

        self.data_quality_score = max(0.0, completeness_score + detail_bonus - consistency_penalty)
        return self.data_quality_score