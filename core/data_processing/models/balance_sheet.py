"""
Balance Sheet Pydantic Model
============================

Comprehensive Pydantic model for Balance Sheet data with validation rules
and business logic constraints including the fundamental accounting equation:
Assets = Liabilities + Shareholders' Equity

This model includes:
- All standard balance sheet line items (Assets, Liabilities, Equity)
- Balance sheet equation validation
- Working capital calculations
- Liquidity ratio support
- Cross-field validation for statement integrity
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import Field, validator, root_validator
from pydantic.types import condecimal

from .base import BaseFinancialStatementModel


class BalanceSheetModel(BaseFinancialStatementModel):
    """
    Comprehensive Balance Sheet model with validation and business logic
    """

    # === ASSETS SECTION ===

    # Current Assets
    current_assets: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total current assets (assets convertible to cash within one year)",
        example=143566000000.0
    )

    cash_and_equivalents: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash and cash equivalents",
        example=29965000000.0
    )

    cash: Optional[condecimal(ge=0)] = Field(
        None,
        description="Cash (alias for cash_and_equivalents)"
    )

    short_term_investments: Optional[condecimal(ge=0)] = Field(
        None,
        description="Short-term investments and marketable securities",
        example=31590000000.0
    )

    accounts_receivable: Optional[condecimal(ge=0)] = Field(
        None,
        description="Accounts receivable (net of allowances)",
        example=29508000000.0
    )

    net_receivables: Optional[condecimal(ge=0)] = Field(
        None,
        description="Net receivables (alias for accounts_receivable)"
    )

    inventory: Optional[condecimal(ge=0)] = Field(
        None,
        description="Inventory at cost or market value",
        example=6331000000.0
    )

    prepaid_expenses: Optional[condecimal(ge=0)] = Field(
        None,
        description="Prepaid expenses and other current assets"
    )

    other_current_assets: Optional[condecimal(ge=0)] = Field(
        None,
        description="Other current assets"
    )

    # Non-Current Assets
    non_current_assets: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total non-current assets"
    )

    property_plant_equipment: Optional[condecimal(ge=0)] = Field(
        None,
        description="Property, plant and equipment (net of depreciation)",
        example=43715000000.0
    )

    ppe_net: Optional[condecimal(ge=0)] = Field(
        None,
        description="PP&E net (alias for property_plant_equipment)"
    )

    goodwill: Optional[condecimal(ge=0)] = Field(
        None,
        description="Goodwill from acquisitions"
    )

    intangible_assets: Optional[condecimal(ge=0)] = Field(
        None,
        description="Intangible assets (patents, trademarks, etc.)"
    )

    long_term_investments: Optional[condecimal(ge=0)] = Field(
        None,
        description="Long-term investments",
        example=100544000000.0
    )

    other_assets: Optional[condecimal(ge=0)] = Field(
        None,
        description="Other long-term assets"
    )

    # Total Assets
    total_assets: Optional[condecimal(gt=0)] = Field(
        None,
        description="Total assets (Current Assets + Non-Current Assets)",
        example=352755000000.0
    )

    # === LIABILITIES SECTION ===

    # Current Liabilities
    current_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total current liabilities (due within one year)",
        example=145308000000.0
    )

    accounts_payable: Optional[condecimal(ge=0)] = Field(
        None,
        description="Accounts payable",
        example=62611000000.0
    )

    short_term_debt: Optional[condecimal(ge=0)] = Field(
        None,
        description="Short-term debt and current portion of long-term debt",
        example=9822000000.0
    )

    accrued_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Accrued expenses and liabilities"
    )

    other_current_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Other current liabilities"
    )

    # Non-Current Liabilities
    non_current_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total non-current liabilities"
    )

    long_term_debt: Optional[condecimal(ge=0)] = Field(
        None,
        description="Long-term debt",
        example=95281000000.0
    )

    deferred_tax_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Deferred tax liabilities"
    )

    other_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Other long-term liabilities"
    )

    # Total Liabilities
    total_liabilities: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total liabilities (Current Liabilities + Non-Current Liabilities)",
        example=290437000000.0
    )

    total_debt: Optional[condecimal(ge=0)] = Field(
        None,
        description="Total debt (Short-term debt + Long-term debt)",
        example=105103000000.0
    )

    # === SHAREHOLDERS' EQUITY SECTION ===

    shareholders_equity: Optional[Decimal] = Field(
        None,
        description="Total shareholders' equity",
        example=62318000000.0
    )

    stockholders_equity: Optional[Decimal] = Field(
        None,
        description="Stockholders' equity (alias for shareholders_equity)"
    )

    common_stock: Optional[condecimal(ge=0)] = Field(
        None,
        description="Common stock par value"
    )

    additional_paid_in_capital: Optional[Decimal] = Field(
        None,
        description="Additional paid-in capital"
    )

    retained_earnings: Optional[Decimal] = Field(
        None,
        description="Retained earnings",
        example=164399000000.0
    )

    accumulated_other_comprehensive_income: Optional[Decimal] = Field(
        None,
        description="Accumulated other comprehensive income/loss"
    )

    treasury_stock: Optional[condecimal(le=0)] = Field(
        None,
        description="Treasury stock (negative value)"
    )

    # === CALCULATED FIELDS ===

    working_capital: Optional[Decimal] = Field(
        None,
        description="Working capital (Current Assets - Current Liabilities)"
    )

    net_debt: Optional[Decimal] = Field(
        None,
        description="Net debt (Total Debt - Cash and Equivalents)"
    )

    book_value: Optional[Decimal] = Field(
        None,
        description="Book value (alias for shareholders_equity)"
    )

    tangible_book_value: Optional[Decimal] = Field(
        None,
        description="Tangible book value (Book Value - Intangible Assets)"
    )

    class Config:
        schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "company_name": "Apple Inc.",
                "period_end_date": "2023-09-30",
                "reporting_period": "annual",
                "currency": "USD",
                "current_assets": 143566000000.0,
                "cash_and_equivalents": 29965000000.0,
                "short_term_investments": 31590000000.0,
                "accounts_receivable": 29508000000.0,
                "inventory": 6331000000.0,
                "property_plant_equipment": 43715000000.0,
                "long_term_investments": 100544000000.0,
                "total_assets": 352755000000.0,
                "current_liabilities": 145308000000.0,
                "accounts_payable": 62611000000.0,
                "short_term_debt": 9822000000.0,
                "long_term_debt": 95281000000.0,
                "total_liabilities": 290437000000.0,
                "shareholders_equity": 62318000000.0,
                "retained_earnings": 164399000000.0
            }
        }

    @validator('cash', pre=True, always=True)
    def set_cash_alias(cls, v, values):
        """Set cash as alias for cash_and_equivalents if not provided"""
        if v is None and 'cash_and_equivalents' in values and values['cash_and_equivalents'] is not None:
            return values['cash_and_equivalents']
        return v

    @validator('net_receivables', pre=True, always=True)
    def set_receivables_alias(cls, v, values):
        """Set net_receivables as alias for accounts_receivable if not provided"""
        if v is None and 'accounts_receivable' in values and values['accounts_receivable'] is not None:
            return values['accounts_receivable']
        return v

    @validator('ppe_net', pre=True, always=True)
    def set_ppe_alias(cls, v, values):
        """Set ppe_net as alias for property_plant_equipment if not provided"""
        if v is None and 'property_plant_equipment' in values and values['property_plant_equipment'] is not None:
            return values['property_plant_equipment']
        return v

    @validator('stockholders_equity', pre=True, always=True)
    def set_stockholders_equity_alias(cls, v, values):
        """Set stockholders_equity as alias for shareholders_equity if not provided"""
        if v is None and 'shareholders_equity' in values and values['shareholders_equity'] is not None:
            return values['shareholders_equity']
        return v

    @validator('book_value', pre=True, always=True)
    def set_book_value_alias(cls, v, values):
        """Set book_value as alias for shareholders_equity if not provided"""
        if v is None and 'shareholders_equity' in values and values['shareholders_equity'] is not None:
            return values['shareholders_equity']
        return v

    @root_validator
    def validate_balance_sheet_equation(cls, values):
        """Validate the fundamental accounting equation: Assets = Liabilities + Equity"""
        total_assets = values.get('total_assets')
        total_liabilities = values.get('total_liabilities')
        shareholders_equity = values.get('shareholders_equity')

        # The fundamental accounting equation check
        if all(x is not None for x in [total_assets, total_liabilities, shareholders_equity]):
            expected_assets = total_liabilities + shareholders_equity
            tolerance = abs(expected_assets * 0.001)  # 0.1% tolerance for rounding

            if abs(total_assets - expected_assets) > tolerance:
                raise ValueError(
                    f"Balance sheet equation failed: "
                    f"Assets ({total_assets}) ≠ Liabilities ({total_liabilities}) + Equity ({shareholders_equity}). "
                    f"Difference: {total_assets - expected_assets}"
                )

        # Validate current assets calculation
        current_assets = values.get('current_assets')
        if current_assets is not None:
            component_sum = Decimal(0)
            current_components = [
                'cash_and_equivalents', 'short_term_investments', 'accounts_receivable',
                'inventory', 'prepaid_expenses', 'other_current_assets'
            ]

            available_components = []
            for component in current_components:
                value = values.get(component)
                if value is not None:
                    component_sum += value
                    available_components.append(component)

            # Only validate if we have at least 2 components to avoid false positives
            if len(available_components) >= 2:
                tolerance = abs(current_assets * 0.05)  # 5% tolerance for missing components
                if abs(current_assets - component_sum) > tolerance:
                    values['notes'] = f"Current assets breakdown variance: Expected sum ~{component_sum}, reported {current_assets}"

        # Validate total debt calculation
        total_debt = values.get('total_debt')
        short_term_debt = values.get('short_term_debt')
        long_term_debt = values.get('long_term_debt')

        if total_debt is not None and short_term_debt is not None and long_term_debt is not None:
            expected_total_debt = short_term_debt + long_term_debt
            tolerance = abs(expected_total_debt * 0.01)  # 1% tolerance
            if abs(total_debt - expected_total_debt) > tolerance:
                raise ValueError(
                    f"Total debt validation failed: "
                    f"Expected {expected_total_debt}, got {total_debt}"
                )

        return values

    def calculate_working_capital(self) -> Optional[Decimal]:
        """Calculate working capital"""
        if self.current_assets is not None and self.current_liabilities is not None:
            self.working_capital = self.current_assets - self.current_liabilities
            return self.working_capital
        return None

    def calculate_net_debt(self) -> Optional[Decimal]:
        """Calculate net debt"""
        if self.total_debt is not None and self.cash_and_equivalents is not None:
            self.net_debt = self.total_debt - self.cash_and_equivalents
            return self.net_debt
        return None

    def calculate_total_debt(self) -> Optional[Decimal]:
        """Calculate total debt from components"""
        if self.short_term_debt is not None and self.long_term_debt is not None:
            self.total_debt = self.short_term_debt + self.long_term_debt
            return self.total_debt
        return None

    def calculate_tangible_book_value(self) -> Optional[Decimal]:
        """Calculate tangible book value"""
        if self.shareholders_equity is not None:
            tangible_bv = self.shareholders_equity
            if self.goodwill is not None:
                tangible_bv -= self.goodwill
            if self.intangible_assets is not None:
                tangible_bv -= self.intangible_assets

            self.tangible_book_value = tangible_bv
            return self.tangible_book_value
        return None

    def get_liquidity_ratios(self) -> Dict[str, Optional[float]]:
        """Calculate liquidity ratios"""
        ratios = {}

        if self.current_liabilities is not None and self.current_liabilities > 0:
            # Current ratio
            if self.current_assets is not None:
                ratios['current_ratio'] = float(self.current_assets / self.current_liabilities)

            # Quick ratio (acid test)
            if self.current_assets is not None and self.inventory is not None:
                quick_assets = self.current_assets - self.inventory
                ratios['quick_ratio'] = float(quick_assets / self.current_liabilities)

            # Cash ratio
            if self.cash_and_equivalents is not None:
                liquid_assets = self.cash_and_equivalents
                if self.short_term_investments is not None:
                    liquid_assets += self.short_term_investments
                ratios['cash_ratio'] = float(liquid_assets / self.current_liabilities)

        return ratios

    def get_leverage_ratios(self) -> Dict[str, Optional[float]]:
        """Calculate leverage ratios"""
        ratios = {}

        # Debt-to-equity ratio
        if self.shareholders_equity is not None and self.shareholders_equity != 0 and self.total_debt is not None:
            ratios['debt_to_equity'] = float(self.total_debt / abs(self.shareholders_equity))

        # Debt-to-assets ratio
        if self.total_assets is not None and self.total_assets > 0 and self.total_debt is not None:
            ratios['debt_to_assets'] = float(self.total_debt / self.total_assets)

        # Equity multiplier
        if self.total_assets is not None and self.shareholders_equity is not None and self.shareholders_equity != 0:
            ratios['equity_multiplier'] = float(self.total_assets / abs(self.shareholders_equity))

        return ratios

    def get_asset_composition(self) -> Dict[str, Optional[float]]:
        """Get asset composition percentages"""
        composition = {}

        if self.total_assets is not None and self.total_assets > 0:
            # Current assets as percentage of total
            if self.current_assets is not None:
                composition['current_assets_pct'] = float(self.current_assets / self.total_assets)

            # Cash as percentage of total
            if self.cash_and_equivalents is not None:
                composition['cash_pct'] = float(self.cash_and_equivalents / self.total_assets)

            # PP&E as percentage of total
            if self.property_plant_equipment is not None:
                composition['ppe_pct'] = float(self.property_plant_equipment / self.total_assets)

            # Inventory as percentage of current assets
            if self.current_assets is not None and self.inventory is not None and self.current_assets > 0:
                composition['inventory_pct_current'] = float(self.inventory / self.current_assets)

        return composition

    def validate_balance_sheet_structure(self) -> Dict[str, Any]:
        """Perform comprehensive balance sheet structure validation"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'calculated_values': {}
        }

        # Check balance sheet equation
        if all(x is not None for x in [self.total_assets, self.total_liabilities, self.shareholders_equity]):
            calculated_assets = self.total_liabilities + self.shareholders_equity
            difference = abs(self.total_assets - calculated_assets)
            tolerance = abs(calculated_assets * 0.001)

            validation_results['calculated_values']['calculated_total_assets'] = float(calculated_assets)
            validation_results['calculated_values']['balance_difference'] = float(difference)

            if difference > tolerance:
                validation_results['is_valid'] = False
                validation_results['errors'].append(
                    f"Balance sheet equation failed. Difference: {difference}"
                )

        # Check for negative equity (potential financial distress)
        if self.shareholders_equity is not None and self.shareholders_equity < 0:
            validation_results['warnings'].append(
                "Negative shareholders' equity detected - potential financial distress"
            )

        # Check working capital
        working_cap = self.calculate_working_capital()
        if working_cap is not None:
            validation_results['calculated_values']['working_capital'] = float(working_cap)
            if working_cap < 0:
                validation_results['warnings'].append(
                    "Negative working capital - potential liquidity issues"
                )

        return validation_results

    def calculate_data_quality_score(self) -> float:
        """Calculate data quality score for balance sheet"""
        required_fields = [
            'total_assets', 'current_assets', 'cash_and_equivalents',
            'total_liabilities', 'current_liabilities', 'shareholders_equity'
        ]

        missing_count = sum(1 for field in required_fields
                           if getattr(self, field, None) is None)

        # Base completeness score
        completeness_score = 1.0 - (missing_count / len(required_fields))

        # Bonus for detailed breakdown
        detail_fields = [
            'accounts_receivable', 'inventory', 'property_plant_equipment',
            'accounts_payable', 'long_term_debt', 'retained_earnings'
        ]
        detail_count = sum(1 for field in detail_fields
                          if getattr(self, field, None) is not None)
        detail_bonus = min(0.15, detail_count * 0.025)

        # Balance sheet equation validation bonus/penalty
        equation_bonus = 0.0
        if all(getattr(self, field, None) is not None
               for field in ['total_assets', 'total_liabilities', 'shareholders_equity']):
            expected_assets = self.total_liabilities + self.shareholders_equity
            difference_pct = abs(self.total_assets - expected_assets) / expected_assets
            if difference_pct <= 0.001:  # Perfect balance
                equation_bonus = 0.1
            elif difference_pct <= 0.01:  # Within 1%
                equation_bonus = 0.05
            elif difference_pct > 0.05:  # More than 5% off
                equation_bonus = -0.2

        self.data_quality_score = max(0.0, completeness_score + detail_bonus + equation_bonus)
        return self.data_quality_score