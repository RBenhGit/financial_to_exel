"""
Cash Flow Statement Pydantic Model
===================================

Comprehensive Pydantic model for Cash Flow Statement data with validation rules
and business logic constraints including cash flow reconciliation checks.

This model includes:
- Operating, investing, and financing cash flow sections
- Free cash flow calculations (FCFF, FCFE, Levered FCF)
- Cash flow reconciliation validation
- Working capital change calculations
- Cross-field validation for statement integrity
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import Field, validator, root_validator
from pydantic.types import condecimal

from .base import BaseFinancialStatementModel


class CashFlowStatementModel(BaseFinancialStatementModel):
    """
    Comprehensive Cash Flow Statement model with validation and business logic
    """

    # === OPERATING ACTIVITIES ===

    operating_cash_flow: Optional[Decimal] = Field(
        None,
        description="Net cash provided by operating activities",
        example=110543000000.0
    )

    cash_from_operations: Optional[Decimal] = Field(
        None,
        description="Cash from operations (alias for operating_cash_flow)"
    )

    # Operating cash flow components
    net_income: Optional[Decimal] = Field(
        None,
        description="Net income (starting point for indirect method)",
        example=96995000000.0
    )

    depreciation_amortization: Optional[condecimal(ge=0)] = Field(
        None,
        description="Depreciation and amortization expense",
        example=11519000000.0
    )

    depreciation: Optional[condecimal(ge=0)] = Field(
        None,
        description="Depreciation expense"
    )

    amortization: Optional[condecimal(ge=0)] = Field(
        None,
        description="Amortization expense"
    )

    stock_based_compensation: Optional[condecimal(ge=0)] = Field(
        None,
        description="Stock-based compensation expense"
    )

    deferred_tax: Optional[Decimal] = Field(
        None,
        description="Deferred income taxes"
    )

    # Working capital changes
    change_in_working_capital: Optional[Decimal] = Field(
        None,
        description="Change in working capital"
    )

    change_in_accounts_receivable: Optional[Decimal] = Field(
        None,
        description="Change in accounts receivable"
    )

    change_in_inventory: Optional[Decimal] = Field(
        None,
        description="Change in inventory"
    )

    change_in_accounts_payable: Optional[Decimal] = Field(
        None,
        description="Change in accounts payable"
    )

    change_in_accrued_liabilities: Optional[Decimal] = Field(
        None,
        description="Change in accrued liabilities"
    )

    other_operating_activities: Optional[Decimal] = Field(
        None,
        description="Other operating activities adjustments"
    )

    # === INVESTING ACTIVITIES ===

    investing_cash_flow: Optional[Decimal] = Field(
        None,
        description="Net cash used in investing activities",
        example=-3705000000.0
    )

    cash_from_investing: Optional[Decimal] = Field(
        None,
        description="Cash from investing (alias for investing_cash_flow)"
    )

    # Investing cash flow components
    capital_expenditures: Optional[condecimal(ge=0)] = Field(
        None,
        description="Capital expenditures (CapEx)",
        example=10959000000.0
    )

    capex: Optional[condecimal(ge=0)] = Field(
        None,
        description="CapEx (alias for capital_expenditures)"
    )

    acquisitions: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash paid for acquisitions"
    )

    purchases_investments: Optional[condecimal(ge=0)] = Field(
        None,
        description="Purchases of investments and securities"
    )

    sales_investments: Optional[condecimal(ge=0)] = Field(
        None,
        description="Proceeds from sales of investments"
    )

    other_investing_activities: Optional[Decimal] = Field(
        None,
        description="Other investing activities"
    )

    # === FINANCING ACTIVITIES ===

    financing_cash_flow: Optional[Decimal] = Field(
        None,
        description="Net cash used in financing activities",
        example=-108488000000.0
    )

    cash_from_financing: Optional[Decimal] = Field(
        None,
        description="Cash from financing (alias for financing_cash_flow)"
    )

    # Financing cash flow components
    dividends_paid: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash dividends paid",
        example=15025000000.0
    )

    share_repurchases: Optional[condecimal(ge=0)] = Field(
        None,
        description="Share repurchases/treasury stock purchases",
        example=77550000000.0
    )

    stock_buybacks: Optional[condecimal(ge=0)] = Field(
        None,
        description="Stock buybacks (alias for share_repurchases)"
    )

    debt_issued: Optional[condecimal(ge=0)] = Field(
        None,
        description="Proceeds from debt issuance"
    )

    debt_repayment: Optional[condecimal(ge=0)] = Field(
        None,
        description="Debt repayment/retirement"
    )

    stock_issued: Optional[Decimal] = Field(
        None,
        description="Proceeds from stock issuance"
    )

    other_financing_activities: Optional[Decimal] = Field(
        None,
        description="Other financing activities"
    )

    # === NET CHANGE IN CASH ===

    net_change_in_cash: Optional[Decimal] = Field(
        None,
        description="Net change in cash and cash equivalents",
        example=-1650000000.0
    )

    cash_beginning_period: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash and equivalents at beginning of period"
    )

    cash_end_period: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash and equivalents at end of period"
    )

    # === FREE CASH FLOW CALCULATIONS ===

    free_cash_flow: Optional[Decimal] = Field(
        None,
        description="Free Cash Flow (Operating CF - CapEx)"
    )

    fcf: Optional[Decimal] = Field(
        None,
        description="FCF (alias for free_cash_flow)"
    )

    free_cash_flow_to_equity: Optional[Decimal] = Field(
        None,
        description="Free Cash Flow to Equity (FCFE)"
    )

    fcfe: Optional[Decimal] = Field(
        None,
        description="FCFE (alias for free_cash_flow_to_equity)"
    )

    free_cash_flow_to_firm: Optional[Decimal] = Field(
        None,
        description="Free Cash Flow to Firm (FCFF)"
    )

    fcff: Optional[Decimal] = Field(
        None,
        description="FCFF (alias for free_cash_flow_to_firm)"
    )

    levered_free_cash_flow: Optional[Decimal] = Field(
        None,
        description="Levered Free Cash Flow (includes debt effects)"
    )

    levered_fcf: Optional[Decimal] = Field(
        None,
        description="Levered FCF (alias for levered_free_cash_flow)"
    )

    class Config:
        schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "company_name": "Apple Inc.",
                "period_end_date": "2023-09-30",
                "reporting_period": "annual",
                "currency": "USD",
                "operating_cash_flow": 110543000000.0,
                "net_income": 96995000000.0,
                "depreciation_amortization": 11519000000.0,
                "change_in_working_capital": 1068000000.0,
                "investing_cash_flow": -3705000000.0,
                "capital_expenditures": 10959000000.0,
                "financing_cash_flow": -108488000000.0,
                "dividends_paid": 15025000000.0,
                "share_repurchases": 77550000000.0,
                "net_change_in_cash": -1650000000.0,
                "free_cash_flow": 99584000000.0
            }
        }

    @validator('cash_from_operations', pre=True, always=True)
    def set_operations_alias(cls, v, values):
        """Set cash_from_operations as alias for operating_cash_flow"""
        if v is None and 'operating_cash_flow' in values and values['operating_cash_flow'] is not None:
            return values['operating_cash_flow']
        return v

    @validator('cash_from_investing', pre=True, always=True)
    def set_investing_alias(cls, v, values):
        """Set cash_from_investing as alias for investing_cash_flow"""
        if v is None and 'investing_cash_flow' in values and values['investing_cash_flow'] is not None:
            return values['investing_cash_flow']
        return v

    @validator('cash_from_financing', pre=True, always=True)
    def set_financing_alias(cls, v, values):
        """Set cash_from_financing as alias for financing_cash_flow"""
        if v is None and 'financing_cash_flow' in values and values['financing_cash_flow'] is not None:
            return values['financing_cash_flow']
        return v

    @validator('capex', pre=True, always=True)
    def set_capex_alias(cls, v, values):
        """Set capex as alias for capital_expenditures"""
        if v is None and 'capital_expenditures' in values and values['capital_expenditures'] is not None:
            return values['capital_expenditures']
        return v

    @validator('fcf', pre=True, always=True)
    def set_fcf_alias(cls, v, values):
        """Set fcf as alias for free_cash_flow"""
        if v is None and 'free_cash_flow' in values and values['free_cash_flow'] is not None:
            return values['free_cash_flow']
        return v

    @validator('fcfe', pre=True, always=True)
    def set_fcfe_alias(cls, v, values):
        """Set fcfe as alias for free_cash_flow_to_equity"""
        if v is None and 'free_cash_flow_to_equity' in values and values['free_cash_flow_to_equity'] is not None:
            return values['free_cash_flow_to_equity']
        return v

    @validator('fcff', pre=True, always=True)
    def set_fcff_alias(cls, v, values):
        """Set fcff as alias for free_cash_flow_to_firm"""
        if v is None and 'free_cash_flow_to_firm' in values and values['free_cash_flow_to_firm'] is not None:
            return values['free_cash_flow_to_firm']
        return v

    @validator('levered_fcf', pre=True, always=True)
    def set_levered_fcf_alias(cls, v, values):
        """Set levered_fcf as alias for levered_free_cash_flow"""
        if v is None and 'levered_free_cash_flow' in values and values['levered_free_cash_flow'] is not None:
            return values['levered_free_cash_flow']
        return v

    @validator('stock_buybacks', pre=True, always=True)
    def set_buybacks_alias(cls, v, values):
        """Set stock_buybacks as alias for share_repurchases"""
        if v is None and 'share_repurchases' in values and values['share_repurchases'] is not None:
            return values['share_repurchases']
        return v

    @root_validator
    def validate_cash_flow_reconciliation(cls, values):
        """Validate cash flow statement reconciliation"""
        operating_cf = values.get('operating_cash_flow')
        investing_cf = values.get('investing_cash_flow')
        financing_cf = values.get('financing_cash_flow')
        net_change = values.get('net_change_in_cash')

        # Validate net change in cash calculation
        if all(x is not None for x in [operating_cf, investing_cf, financing_cf, net_change]):
            calculated_change = operating_cf + investing_cf + financing_cf
            tolerance = abs(calculated_change * 0.01)  # 1% tolerance

            if abs(net_change - calculated_change) > tolerance:
                raise ValueError(
                    f"Cash flow reconciliation failed: "
                    f"Operating ({operating_cf}) + Investing ({investing_cf}) + Financing ({financing_cf}) "
                    f"= {calculated_change}, but Net Change = {net_change}"
                )

        # Validate beginning + change = ending cash
        cash_begin = values.get('cash_beginning_period')
        cash_end = values.get('cash_end_period')

        if all(x is not None for x in [cash_begin, net_change, cash_end]):
            expected_end_cash = cash_begin + net_change
            tolerance = abs(expected_end_cash * 0.01)

            if abs(cash_end - expected_end_cash) > tolerance:
                raise ValueError(
                    f"Cash reconciliation failed: "
                    f"Beginning cash ({cash_begin}) + Net change ({net_change}) "
                    f"= {expected_end_cash}, but Ending cash = {cash_end}"
                )

        return values

    def calculate_free_cash_flow(self) -> Optional[Decimal]:
        """Calculate basic Free Cash Flow (Operating CF - CapEx)"""
        if self.operating_cash_flow is not None and self.capital_expenditures is not None:
            self.free_cash_flow = self.operating_cash_flow - self.capital_expenditures
            self.fcf = self.free_cash_flow  # Set alias
            return self.free_cash_flow
        return None

    def calculate_fcfe(self, net_debt_payments: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Calculate Free Cash Flow to Equity
        FCFE = FCF - Net Debt Payments
        """
        fcf = self.free_cash_flow or self.calculate_free_cash_flow()
        if fcf is not None:
            if net_debt_payments is not None:
                self.free_cash_flow_to_equity = fcf - net_debt_payments
            else:
                # Use net financing from debt as proxy for net debt payments
                debt_financing = Decimal(0)
                if self.debt_issued is not None:
                    debt_financing += self.debt_issued
                if self.debt_repayment is not None:
                    debt_financing -= self.debt_repayment

                self.free_cash_flow_to_equity = fcf - debt_financing

            self.fcfe = self.free_cash_flow_to_equity  # Set alias
            return self.free_cash_flow_to_equity
        return None

    def calculate_fcff(self, ebit: Optional[Decimal] = None, tax_rate: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Calculate Free Cash Flow to Firm
        FCFF = EBIT(1-Tax Rate) + Depreciation - CapEx - Change in Working Capital
        """
        if ebit is not None and tax_rate is not None:
            after_tax_ebit = ebit * (1 - tax_rate)

            fcff = after_tax_ebit
            if self.depreciation_amortization is not None:
                fcff += self.depreciation_amortization
            if self.capital_expenditures is not None:
                fcff -= self.capital_expenditures
            if self.change_in_working_capital is not None:
                fcff -= self.change_in_working_capital

            self.free_cash_flow_to_firm = fcff
            self.fcff = self.free_cash_flow_to_firm  # Set alias
            return self.free_cash_flow_to_firm

        # Alternative: Use FCF + After-tax Interest Expense
        elif self.free_cash_flow is not None:
            # This is a simplified approach
            self.free_cash_flow_to_firm = self.free_cash_flow
            self.fcff = self.free_cash_flow_to_firm
            return self.free_cash_flow_to_firm

        return None

    def calculate_levered_fcf(self) -> Optional[Decimal]:
        """
        Calculate Levered Free Cash Flow (traditional FCF with debt effects)
        Levered FCF = Operating CF - CapEx
        """
        # This is the same as basic FCF for most purposes
        levered_fcf = self.calculate_free_cash_flow()
        if levered_fcf is not None:
            self.levered_free_cash_flow = levered_fcf
            self.levered_fcf = self.levered_free_cash_flow
        return levered_fcf

    def calculate_net_change_in_cash(self) -> Optional[Decimal]:
        """Calculate net change in cash from cash flow components"""
        if all(x is not None for x in [self.operating_cash_flow, self.investing_cash_flow, self.financing_cash_flow]):
            self.net_change_in_cash = self.operating_cash_flow + self.investing_cash_flow + self.financing_cash_flow
            return self.net_change_in_cash
        return None

    def calculate_working_capital_change(self) -> Optional[Decimal]:
        """Calculate change in working capital from components"""
        wc_change = Decimal(0)
        components_found = False

        wc_components = [
            'change_in_accounts_receivable',
            'change_in_inventory',
            'change_in_accounts_payable',
            'change_in_accrued_liabilities'
        ]

        for component in wc_components:
            value = getattr(self, component, None)
            if value is not None:
                wc_change += value
                components_found = True

        if components_found:
            self.change_in_working_capital = wc_change
            return self.change_in_working_capital
        return None

    def get_cash_flow_ratios(self, market_cap: Optional[Decimal] = None) -> Dict[str, Optional[float]]:
        """Calculate cash flow-based ratios"""
        ratios = {}

        # Operating cash flow margin
        if hasattr(self, 'revenue') and self.revenue is not None and self.revenue > 0:
            if self.operating_cash_flow is not None:
                ratios['operating_cf_margin'] = float(self.operating_cash_flow / self.revenue)

        # FCF margin
        if hasattr(self, 'revenue') and self.revenue is not None and self.revenue > 0:
            if self.free_cash_flow is not None:
                ratios['fcf_margin'] = float(self.free_cash_flow / self.revenue)

        # Price to Free Cash Flow (if market cap provided)
        if market_cap is not None and self.free_cash_flow is not None and self.free_cash_flow > 0:
            ratios['price_to_fcf'] = float(market_cap / self.free_cash_flow)

        # Cash conversion ratio (FCF / Net Income)
        if self.net_income is not None and self.net_income > 0 and self.free_cash_flow is not None:
            ratios['cash_conversion_ratio'] = float(self.free_cash_flow / self.net_income)

        # CapEx intensity (CapEx / Revenue)
        if hasattr(self, 'revenue') and self.revenue is not None and self.revenue > 0:
            if self.capital_expenditures is not None:
                ratios['capex_intensity'] = float(self.capital_expenditures / self.revenue)

        return ratios

    def get_fcf_breakdown(self) -> Dict[str, Optional[float]]:
        """Get breakdown of different FCF types"""
        breakdown = {}

        if self.free_cash_flow is not None:
            breakdown['free_cash_flow'] = float(self.free_cash_flow)

        if self.free_cash_flow_to_equity is not None:
            breakdown['fcfe'] = float(self.free_cash_flow_to_equity)

        if self.free_cash_flow_to_firm is not None:
            breakdown['fcff'] = float(self.free_cash_flow_to_firm)

        if self.levered_free_cash_flow is not None:
            breakdown['levered_fcf'] = float(self.levered_free_cash_flow)

        return breakdown

    def validate_cash_flow_quality(self) -> Dict[str, Any]:
        """Assess cash flow quality metrics"""
        quality_metrics = {
            'quality_score': 1.0,
            'red_flags': [],
            'positive_indicators': []
        }

        # Check operating CF vs Net Income
        if self.operating_cash_flow is not None and self.net_income is not None:
            if self.net_income > 0:
                ocf_ni_ratio = self.operating_cash_flow / self.net_income

                if ocf_ni_ratio < 0.8:
                    quality_metrics['red_flags'].append("Operating cash flow significantly lower than net income")
                    quality_metrics['quality_score'] -= 0.2
                elif ocf_ni_ratio > 1.2:
                    quality_metrics['positive_indicators'].append("Strong cash conversion from earnings")

        # Check for negative FCF
        if self.free_cash_flow is not None and self.free_cash_flow < 0:
            quality_metrics['red_flags'].append("Negative free cash flow")
            quality_metrics['quality_score'] -= 0.3

        # Check CapEx trends (would need historical data for proper analysis)
        if self.capital_expenditures is not None and self.depreciation_amortization is not None:
            if self.capital_expenditures < self.depreciation_amortization:
                quality_metrics['red_flags'].append("CapEx below depreciation - potential underinvestment")
                quality_metrics['quality_score'] -= 0.1

        quality_metrics['quality_score'] = max(0.0, quality_metrics['quality_score'])
        return quality_metrics

    def calculate_data_quality_score(self) -> float:
        """Calculate data quality score for cash flow statement"""
        required_fields = [
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
            'net_change_in_cash', 'capital_expenditures'
        ]

        missing_count = sum(1 for field in required_fields
                           if getattr(self, field, None) is None)

        # Base completeness score
        completeness_score = 1.0 - (missing_count / len(required_fields))

        # Bonus for FCF calculations
        fcf_bonus = 0.0
        if self.free_cash_flow is not None:
            fcf_bonus += 0.05
        if self.free_cash_flow_to_equity is not None:
            fcf_bonus += 0.05
        if self.free_cash_flow_to_firm is not None:
            fcf_bonus += 0.05

        # Reconciliation accuracy bonus
        reconciliation_bonus = 0.0
        if all(getattr(self, field, None) is not None
               for field in ['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'net_change_in_cash']):
            calculated_change = self.operating_cash_flow + self.investing_cash_flow + self.financing_cash_flow
            if abs(self.net_change_in_cash - calculated_change) / abs(calculated_change) < 0.01:
                reconciliation_bonus = 0.1

        self.data_quality_score = max(0.0, completeness_score + fcf_bonus + reconciliation_bonus)
        return self.data_quality_score