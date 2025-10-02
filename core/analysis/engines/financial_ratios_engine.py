"""
Financial Ratios Calculation Engine
==================================

This module provides a comprehensive financial ratios calculation engine that extends
the existing financial calculation infrastructure. It implements standardized ratio
calculations organized by category with proper input validation and error handling.

Key Features:
- Comprehensive ratio calculations across all major categories
- Pure mathematical functions with consistent interfaces
- Category-based organization (Liquidity, Profitability, Efficiency, Leverage, Growth)
- Integration with existing FinancialCalculationEngine
- Support for both GAAP and IFRS accounting standards
- Performance optimized for large-scale calculations

Classes:
--------
FinancialRatiosEngine
    Main engine providing comprehensive financial ratio calculations

RatioCategory
    Enumeration of ratio categories for organization

RatioResult
    Standard result container for ratio calculations

Ratio Categories:
----------------
1. Liquidity Ratios - Measure company's ability to meet short-term obligations
2. Profitability Ratios - Assess company's ability to generate earnings
3. Efficiency/Activity Ratios - Evaluate asset utilization effectiveness
4. Leverage/Solvency Ratios - Analyze debt levels and financial risk
5. Market Value Ratios - Compare market valuation metrics
6. Growth Ratios - Measure growth rates and trends

Design Principles:
-----------------
- Pure functions: No external dependencies or side effects
- Category organization: Logical grouping of related ratios
- Standard interfaces: Consistent parameter and return patterns
- Comprehensive validation: Input validation and mathematical checks
- Error handling: Graceful handling of edge cases and invalid data
- Performance optimized: Efficient calculations for real-time analysis
"""

import math
import logging
from typing import List, Dict, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class RatioCategory(Enum):
    """Enumeration of financial ratio categories"""
    LIQUIDITY = "liquidity"
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    LEVERAGE = "leverage"
    MARKET_VALUE = "market_value"
    GROWTH = "growth"


@dataclass
class RatioResult:
    """Standard result container for ratio calculations"""
    name: str
    value: float
    category: RatioCategory
    formula: str
    interpretation: str
    is_valid: bool = True
    error_message: Optional[str] = None
    calculation_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RatioInputs:
    """Standard input container for ratio calculations"""
    # Income Statement Items
    revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    interest_expense: Optional[float] = None

    # Balance Sheet Items
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    accounts_payable: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    net_fixed_assets: Optional[float] = None  # Property, Plant & Equipment (net)

    # Cash Flow Statement Items
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None

    # Market Data
    stock_price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    market_capitalization: Optional[float] = None

    # Historical Data for Growth Calculations
    previous_revenue: Optional[float] = None
    previous_net_income: Optional[float] = None
    previous_fcf: Optional[float] = None

    # Additional ratios and metrics
    book_value_per_share: Optional[float] = None
    earnings_per_share: Optional[float] = None


class FinancialRatiosEngine:
    """
    Comprehensive Financial Ratios Calculation Engine

    This engine provides standardized calculations for all major financial ratio categories.
    All methods are pure functions that take validated inputs and return standardized results.
    """

    def __init__(self):
        """Initialize the Financial Ratios Engine"""
        self.supported_ratios = self._initialize_supported_ratios()
        logger.info("Financial Ratios Engine initialized with %d supported ratios",
                   len(self.supported_ratios))

    def _initialize_supported_ratios(self) -> Dict[RatioCategory, List[str]]:
        """Initialize the mapping of supported ratios by category"""
        return {
            RatioCategory.LIQUIDITY: [
                'current_ratio', 'quick_ratio', 'cash_ratio', 'working_capital',
                'working_capital_ratio', 'operating_cash_flow_ratio', 'acid_test_ratio'
            ],
            RatioCategory.PROFITABILITY: [
                'gross_profit_margin', 'operating_profit_margin', 'net_profit_margin',
                'ebitda_margin', 'return_on_assets', 'return_on_equity',
                'return_on_invested_capital', 'basic_eps', 'diluted_eps'
            ],
            RatioCategory.EFFICIENCY: [
                'asset_turnover', 'inventory_turnover', 'receivables_turnover',
                'payables_turnover', 'working_capital_turnover', 'fixed_asset_turnover',
                'days_sales_outstanding', 'days_inventory_outstanding', 'days_payable_outstanding'
            ],
            RatioCategory.LEVERAGE: [
                'debt_to_assets', 'debt_to_equity', 'equity_ratio', 'debt_ratio',
                'interest_coverage', 'debt_service_coverage', 'capitalization_ratio',
                'long_term_debt_to_equity'
            ],
            RatioCategory.MARKET_VALUE: [
                'price_to_earnings', 'price_to_book', 'price_to_sales', 'price_to_cash_flow',
                'enterprise_value_to_ebitda', 'earnings_per_share', 'book_value_per_share',
                'dividend_yield'
            ],
            RatioCategory.GROWTH: [
                'revenue_growth', 'net_income_growth', 'fcf_growth', 'asset_growth',
                'equity_growth', 'earnings_growth_rate'
            ]
        }

    # =============================================================================
    # LIQUIDITY RATIOS
    # =============================================================================

    def calculate_current_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Current Ratio = Current Assets / Current Liabilities

        Measures company's ability to pay short-term obligations with current assets.
        Higher ratios indicate better liquidity position.
        """
        try:
            if inputs.current_assets is None or inputs.current_liabilities is None:
                return RatioResult(
                    name="Current Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Current Assets / Current Liabilities",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing current assets or current liabilities data"
                )

            if inputs.current_liabilities == 0:
                return RatioResult(
                    name="Current Ratio",
                    value=float('inf'),
                    category=RatioCategory.LIQUIDITY,
                    formula="Current Assets / Current Liabilities",
                    interpretation="Undefined - zero current liabilities",
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            ratio_value = inputs.current_assets / inputs.current_liabilities

            # Interpretation based on common benchmarks
            if ratio_value >= 2.0:
                interpretation = "Strong liquidity position"
            elif ratio_value >= 1.5:
                interpretation = "Good liquidity position"
            elif ratio_value >= 1.0:
                interpretation = "Adequate liquidity position"
            else:
                interpretation = "Weak liquidity position - potential cash flow concerns"

            return RatioResult(
                name="Current Ratio",
                value=ratio_value,
                category=RatioCategory.LIQUIDITY,
                formula="Current Assets / Current Liabilities",
                interpretation=interpretation,
                metadata={
                    'current_assets': inputs.current_assets,
                    'current_liabilities': inputs.current_liabilities
                }
            )

        except Exception as e:
            logger.error(f"Error calculating current ratio: {e}")
            return RatioResult(
                name="Current Ratio",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="Current Assets / Current Liabilities",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_quick_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Quick Ratio = (Current Assets - Inventory) / Current Liabilities

        More stringent measure of liquidity excluding inventory.
        Also known as the Acid-Test Ratio.
        """
        try:
            if (inputs.current_assets is None or inputs.current_liabilities is None):
                return RatioResult(
                    name="Quick Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="(Current Assets - Inventory) / Current Liabilities",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing current assets or current liabilities data"
                )

            if inputs.current_liabilities == 0:
                return RatioResult(
                    name="Quick Ratio",
                    value=float('inf'),
                    category=RatioCategory.LIQUIDITY,
                    formula="(Current Assets - Inventory) / Current Liabilities",
                    interpretation="Undefined - zero current liabilities",
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            # Use inventory if available, otherwise assume zero
            inventory = inputs.inventory if inputs.inventory is not None else 0.0
            quick_assets = inputs.current_assets - inventory
            ratio_value = quick_assets / inputs.current_liabilities

            # Interpretation based on common benchmarks
            if ratio_value >= 1.5:
                interpretation = "Strong quick liquidity position"
            elif ratio_value >= 1.0:
                interpretation = "Good quick liquidity position"
            elif ratio_value >= 0.75:
                interpretation = "Adequate quick liquidity position"
            else:
                interpretation = "Weak quick liquidity - may struggle with immediate obligations"

            return RatioResult(
                name="Quick Ratio",
                value=ratio_value,
                category=RatioCategory.LIQUIDITY,
                formula="(Current Assets - Inventory) / Current Liabilities",
                interpretation=interpretation,
                metadata={
                    'current_assets': inputs.current_assets,
                    'inventory': inventory,
                    'current_liabilities': inputs.current_liabilities,
                    'quick_assets': quick_assets
                }
            )

        except Exception as e:
            logger.error(f"Error calculating quick ratio: {e}")
            return RatioResult(
                name="Quick Ratio",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="(Current Assets - Inventory) / Current Liabilities",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_cash_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Cash Ratio = Cash and Cash Equivalents / Current Liabilities

        Most conservative liquidity measure using only cash and equivalents.
        """
        try:
            if (inputs.cash_and_equivalents is None or inputs.current_liabilities is None):
                return RatioResult(
                    name="Cash Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Cash and Cash Equivalents / Current Liabilities",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing cash or current liabilities data"
                )

            if inputs.current_liabilities == 0:
                return RatioResult(
                    name="Cash Ratio",
                    value=float('inf'),
                    category=RatioCategory.LIQUIDITY,
                    formula="Cash and Cash Equivalents / Current Liabilities",
                    interpretation="Undefined - zero current liabilities",
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            ratio_value = inputs.cash_and_equivalents / inputs.current_liabilities

            # Interpretation based on common benchmarks
            if ratio_value >= 0.5:
                interpretation = "Strong cash position - can cover significant portion of short-term debt"
            elif ratio_value >= 0.2:
                interpretation = "Good cash position for immediate obligations"
            elif ratio_value >= 0.1:
                interpretation = "Adequate cash reserves"
            else:
                interpretation = "Low cash reserves - may need external financing for obligations"

            return RatioResult(
                name="Cash Ratio",
                value=ratio_value,
                category=RatioCategory.LIQUIDITY,
                formula="Cash and Cash Equivalents / Current Liabilities",
                interpretation=interpretation,
                metadata={
                    'cash_and_equivalents': inputs.cash_and_equivalents,
                    'current_liabilities': inputs.current_liabilities
                }
            )

        except Exception as e:
            logger.error(f"Error calculating cash ratio: {e}")
            return RatioResult(
                name="Cash Ratio",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="Cash and Cash Equivalents / Current Liabilities",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_working_capital(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Working Capital = Current Assets - Current Liabilities

        Measures the company's short-term financial health and operational efficiency.
        Positive working capital indicates ability to meet short-term obligations.
        """
        try:
            if inputs.current_assets is None or inputs.current_liabilities is None:
                return RatioResult(
                    name="Working Capital",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Current Assets - Current Liabilities",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing current assets or current liabilities data"
                )

            working_capital = inputs.current_assets - inputs.current_liabilities

            # Interpretation based on value
            if working_capital > 0:
                if working_capital > inputs.current_assets * 0.2:
                    interpretation = "Strong positive working capital - healthy liquidity cushion"
                else:
                    interpretation = "Positive working capital - adequate short-term liquidity"
            elif working_capital == 0:
                interpretation = "Zero working capital - minimal liquidity buffer"
            else:
                interpretation = "Negative working capital - potential liquidity concerns"

            return RatioResult(
                name="Working Capital",
                value=working_capital,
                category=RatioCategory.LIQUIDITY,
                formula="Current Assets - Current Liabilities",
                interpretation=interpretation,
                metadata={
                    'current_assets': inputs.current_assets,
                    'current_liabilities': inputs.current_liabilities,
                    'working_capital_ratio': working_capital / inputs.current_assets if inputs.current_assets != 0 else 0
                }
            )

        except Exception as e:
            logger.error(f"Error calculating working capital: {e}")
            return RatioResult(
                name="Working Capital",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="Current Assets - Current Liabilities",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_working_capital_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Working Capital Ratio = Working Capital / Total Assets * 100

        Measures working capital as a percentage of total assets.
        Indicates proportion of assets tied up in working capital.
        """
        try:
            if (inputs.current_assets is None or inputs.current_liabilities is None or
                inputs.total_assets is None):
                return RatioResult(
                    name="Working Capital Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Working Capital / Total Assets * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing current assets, current liabilities, or total assets data"
                )

            if inputs.total_assets == 0:
                return RatioResult(
                    name="Working Capital Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Working Capital / Total Assets * 100",
                    interpretation="Undefined - zero total assets",
                    is_valid=False,
                    error_message="Total assets cannot be zero"
                )

            working_capital = inputs.current_assets - inputs.current_liabilities
            ratio_value = (working_capital / inputs.total_assets) * 100

            # Interpretation based on ratio value
            if ratio_value >= 20:
                interpretation = "High working capital ratio - strong liquidity position"
            elif ratio_value >= 10:
                interpretation = "Good working capital ratio - healthy liquidity"
            elif ratio_value >= 0:
                interpretation = "Adequate working capital ratio - moderate liquidity"
            elif ratio_value >= -10:
                interpretation = "Negative working capital ratio - liquidity concerns"
            else:
                interpretation = "Significantly negative working capital - severe liquidity issues"

            return RatioResult(
                name="Working Capital Ratio",
                value=ratio_value,
                category=RatioCategory.LIQUIDITY,
                formula="Working Capital / Total Assets * 100",
                interpretation=interpretation,
                metadata={
                    'working_capital': working_capital,
                    'total_assets': inputs.total_assets,
                    'current_assets': inputs.current_assets,
                    'current_liabilities': inputs.current_liabilities
                }
            )

        except Exception as e:
            logger.error(f"Error calculating working capital ratio: {e}")
            return RatioResult(
                name="Working Capital Ratio",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="Working Capital / Total Assets * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_operating_cash_flow_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Operating Cash Flow Ratio = Operating Cash Flow / Current Liabilities

        Measures ability to cover current liabilities with operating cash flow.
        Higher values indicate stronger ability to meet short-term obligations from operations.
        """
        try:
            if inputs.operating_cash_flow is None or inputs.current_liabilities is None:
                return RatioResult(
                    name="Operating Cash Flow Ratio",
                    value=0.0,
                    category=RatioCategory.LIQUIDITY,
                    formula="Operating Cash Flow / Current Liabilities",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing operating cash flow or current liabilities data"
                )

            if inputs.current_liabilities == 0:
                return RatioResult(
                    name="Operating Cash Flow Ratio",
                    value=float('inf'),
                    category=RatioCategory.LIQUIDITY,
                    formula="Operating Cash Flow / Current Liabilities",
                    interpretation="Undefined - zero current liabilities",
                    is_valid=False,
                    error_message="Current liabilities cannot be zero"
                )

            ratio_value = inputs.operating_cash_flow / inputs.current_liabilities

            # Interpretation based on ratio value
            if ratio_value >= 1.0:
                interpretation = "Excellent cash flow coverage - operations fully cover short-term obligations"
            elif ratio_value >= 0.75:
                interpretation = "Good cash flow coverage - strong operational liquidity"
            elif ratio_value >= 0.5:
                interpretation = "Adequate cash flow coverage - moderate operational liquidity"
            elif ratio_value >= 0.25:
                interpretation = "Weak cash flow coverage - limited operational liquidity"
            elif ratio_value >= 0:
                interpretation = "Poor cash flow coverage - insufficient operations to cover obligations"
            else:
                interpretation = "Negative operating cash flow - burning cash and cannot meet obligations"

            return RatioResult(
                name="Operating Cash Flow Ratio",
                value=ratio_value,
                category=RatioCategory.LIQUIDITY,
                formula="Operating Cash Flow / Current Liabilities",
                interpretation=interpretation,
                metadata={
                    'operating_cash_flow': inputs.operating_cash_flow,
                    'current_liabilities': inputs.current_liabilities
                }
            )

        except Exception as e:
            logger.error(f"Error calculating operating cash flow ratio: {e}")
            return RatioResult(
                name="Operating Cash Flow Ratio",
                value=0.0,
                category=RatioCategory.LIQUIDITY,
                formula="Operating Cash Flow / Current Liabilities",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    # =============================================================================
    # PROFITABILITY RATIOS
    # =============================================================================

    def calculate_gross_profit_margin(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Gross Profit Margin = (Revenue - COGS) / Revenue * 100

        Measures profitability after direct costs of goods sold.
        """
        try:
            if inputs.revenue is None:
                return RatioResult(
                    name="Gross Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="(Revenue - COGS) / Revenue * 100",
                    interpretation="Unable to calculate - missing revenue data",
                    is_valid=False,
                    error_message="Missing revenue data"
                )

            if inputs.revenue == 0:
                return RatioResult(
                    name="Gross Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="(Revenue - COGS) / Revenue * 100",
                    interpretation="Undefined - zero revenue",
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            # Calculate gross profit
            if inputs.gross_profit is not None:
                gross_profit = inputs.gross_profit
            elif inputs.cost_of_goods_sold is not None:
                gross_profit = inputs.revenue - inputs.cost_of_goods_sold
            else:
                return RatioResult(
                    name="Gross Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="(Revenue - COGS) / Revenue * 100",
                    interpretation="Unable to calculate - missing gross profit or COGS data",
                    is_valid=False,
                    error_message="Missing gross profit or cost of goods sold data"
                )

            margin_value = (gross_profit / inputs.revenue) * 100

            # Interpretation based on common benchmarks
            if margin_value >= 40:
                interpretation = "Excellent gross profitability"
            elif margin_value >= 25:
                interpretation = "Good gross profitability"
            elif margin_value >= 15:
                interpretation = "Adequate gross profitability"
            elif margin_value >= 0:
                interpretation = "Poor gross profitability"
            else:
                interpretation = "Negative gross profitability - pricing or cost issues"

            return RatioResult(
                name="Gross Profit Margin",
                value=margin_value,
                category=RatioCategory.PROFITABILITY,
                formula="(Revenue - COGS) / Revenue * 100",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'gross_profit': gross_profit,
                    'cogs': inputs.cost_of_goods_sold
                }
            )

        except Exception as e:
            logger.error(f"Error calculating gross profit margin: {e}")
            return RatioResult(
                name="Gross Profit Margin",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="(Revenue - COGS) / Revenue * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_net_profit_margin(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Net Profit Margin = Net Income / Revenue * 100

        Measures overall profitability after all expenses.
        """
        try:
            if inputs.revenue is None or inputs.net_income is None:
                return RatioResult(
                    name="Net Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Revenue * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or net income data"
                )

            if inputs.revenue == 0:
                return RatioResult(
                    name="Net Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Revenue * 100",
                    interpretation="Undefined - zero revenue",
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            margin_value = (inputs.net_income / inputs.revenue) * 100

            # Interpretation based on common benchmarks
            if margin_value >= 20:
                interpretation = "Excellent net profitability"
            elif margin_value >= 10:
                interpretation = "Good net profitability"
            elif margin_value >= 5:
                interpretation = "Adequate net profitability"
            elif margin_value >= 0:
                interpretation = "Poor net profitability"
            else:
                interpretation = "Negative net profitability - company is losing money"

            return RatioResult(
                name="Net Profit Margin",
                value=margin_value,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Revenue * 100",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'net_income': inputs.net_income
                }
            )

        except Exception as e:
            logger.error(f"Error calculating net profit margin: {e}")
            return RatioResult(
                name="Net Profit Margin",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Revenue * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_operating_profit_margin(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Operating Profit Margin = Operating Income / Revenue * 100

        Measures profitability from core operations before interest and taxes.
        """
        try:
            if inputs.revenue is None or inputs.operating_income is None:
                return RatioResult(
                    name="Operating Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Operating Income / Revenue * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or operating income data"
                )

            if inputs.revenue == 0:
                return RatioResult(
                    name="Operating Profit Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Operating Income / Revenue * 100",
                    interpretation="Undefined - zero revenue",
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            margin_value = (inputs.operating_income / inputs.revenue) * 100

            # Interpretation based on common benchmarks
            if margin_value >= 20:
                interpretation = "Excellent operating profitability"
            elif margin_value >= 15:
                interpretation = "Good operating profitability"
            elif margin_value >= 10:
                interpretation = "Adequate operating profitability"
            elif margin_value >= 0:
                interpretation = "Poor operating profitability"
            else:
                interpretation = "Negative operating profitability - operations losing money"

            return RatioResult(
                name="Operating Profit Margin",
                value=margin_value,
                category=RatioCategory.PROFITABILITY,
                formula="Operating Income / Revenue * 100",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'operating_income': inputs.operating_income
                }
            )

        except Exception as e:
            logger.error(f"Error calculating operating profit margin: {e}")
            return RatioResult(
                name="Operating Profit Margin",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="Operating Income / Revenue * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_ebitda_margin(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate EBITDA Margin = EBITDA / Revenue * 100

        Measures profitability before interest, taxes, depreciation, and amortization.
        """
        try:
            if inputs.revenue is None or inputs.ebitda is None:
                return RatioResult(
                    name="EBITDA Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="EBITDA / Revenue * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or EBITDA data"
                )

            if inputs.revenue == 0:
                return RatioResult(
                    name="EBITDA Margin",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="EBITDA / Revenue * 100",
                    interpretation="Undefined - zero revenue",
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            margin_value = (inputs.ebitda / inputs.revenue) * 100

            # Interpretation based on common benchmarks
            if margin_value >= 25:
                interpretation = "Excellent EBITDA profitability"
            elif margin_value >= 15:
                interpretation = "Good EBITDA profitability"
            elif margin_value >= 10:
                interpretation = "Adequate EBITDA profitability"
            elif margin_value >= 0:
                interpretation = "Poor EBITDA profitability"
            else:
                interpretation = "Negative EBITDA - operations losing money before D&A"

            return RatioResult(
                name="EBITDA Margin",
                value=margin_value,
                category=RatioCategory.PROFITABILITY,
                formula="EBITDA / Revenue * 100",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'ebitda': inputs.ebitda
                }
            )

        except Exception as e:
            logger.error(f"Error calculating EBITDA margin: {e}")
            return RatioResult(
                name="EBITDA Margin",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="EBITDA / Revenue * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_return_on_assets(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Return on Assets (ROA) = Net Income / Total Assets * 100

        Measures how efficiently assets are being used to generate profit.
        """
        try:
            if inputs.net_income is None or inputs.total_assets is None:
                return RatioResult(
                    name="Return on Assets (ROA)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Total Assets * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing net income or total assets data"
                )

            if inputs.total_assets == 0:
                return RatioResult(
                    name="Return on Assets (ROA)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Total Assets * 100",
                    interpretation="Undefined - zero total assets",
                    is_valid=False,
                    error_message="Total assets cannot be zero"
                )

            roa_value = (inputs.net_income / inputs.total_assets) * 100

            # Interpretation based on common benchmarks
            if roa_value >= 10:
                interpretation = "Excellent asset utilization"
            elif roa_value >= 5:
                interpretation = "Good asset utilization"
            elif roa_value >= 2:
                interpretation = "Adequate asset utilization"
            elif roa_value >= 0:
                interpretation = "Poor asset utilization"
            else:
                interpretation = "Negative ROA - assets generating losses"

            return RatioResult(
                name="Return on Assets (ROA)",
                value=roa_value,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Total Assets * 100",
                interpretation=interpretation,
                metadata={
                    'net_income': inputs.net_income,
                    'total_assets': inputs.total_assets
                }
            )

        except Exception as e:
            logger.error(f"Error calculating ROA: {e}")
            return RatioResult(
                name="Return on Assets (ROA)",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Total Assets * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_return_on_equity(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Return on Equity (ROE) = Net Income / Shareholders' Equity * 100

        Measures the return generated on shareholders' equity investment.
        """
        try:
            if inputs.net_income is None or inputs.shareholders_equity is None:
                return RatioResult(
                    name="Return on Equity (ROE)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Shareholders' Equity * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing net income or shareholders' equity data"
                )

            if inputs.shareholders_equity == 0:
                return RatioResult(
                    name="Return on Equity (ROE)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / Shareholders' Equity * 100",
                    interpretation="Undefined - zero shareholders' equity",
                    is_valid=False,
                    error_message="Shareholders' equity cannot be zero"
                )

            roe_value = (inputs.net_income / inputs.shareholders_equity) * 100

            # Interpretation based on common benchmarks
            if roe_value >= 20:
                interpretation = "Excellent returns for shareholders"
            elif roe_value >= 15:
                interpretation = "Good returns for shareholders"
            elif roe_value >= 10:
                interpretation = "Adequate returns for shareholders"
            elif roe_value >= 0:
                interpretation = "Poor returns for shareholders"
            else:
                interpretation = "Negative ROE - destroying shareholder value"

            return RatioResult(
                name="Return on Equity (ROE)",
                value=roe_value,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Shareholders' Equity * 100",
                interpretation=interpretation,
                metadata={
                    'net_income': inputs.net_income,
                    'shareholders_equity': inputs.shareholders_equity
                }
            )

        except Exception as e:
            logger.error(f"Error calculating ROE: {e}")
            return RatioResult(
                name="Return on Equity (ROE)",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / Shareholders' Equity * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_return_on_invested_capital(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Return on Invested Capital (ROIC) = NOPAT / Invested Capital * 100

        ROIC measures the return generated on all invested capital (debt + equity).
        NOPAT = Net Operating Profit After Tax = EBIT * (1 - Tax Rate)
        Invested Capital = Total Assets - Current Liabilities (simplified approach)
        or Invested Capital = Total Debt + Shareholders' Equity

        For simplicity, we use: ROIC ≈ Operating Income * (1 - implied tax rate) / (Total Assets - Current Liabilities)
        Where implied tax rate = 1 - (Net Income / Operating Income) if available
        """
        try:
            # Check for required inputs
            if inputs.operating_income is None:
                return RatioResult(
                    name="Return on Invested Capital (ROIC)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="NOPAT / Invested Capital * 100",
                    interpretation="Unable to calculate - missing operating income",
                    is_valid=False,
                    error_message="Missing operating income data"
                )

            # Calculate invested capital using available data
            # Method 1: Total Assets - Current Liabilities
            if inputs.total_assets is not None and inputs.current_liabilities is not None:
                invested_capital = inputs.total_assets - inputs.current_liabilities
            # Method 2: Total Debt + Shareholders' Equity
            elif inputs.total_debt is not None and inputs.shareholders_equity is not None:
                invested_capital = inputs.total_debt + inputs.shareholders_equity
            else:
                return RatioResult(
                    name="Return on Invested Capital (ROIC)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="NOPAT / Invested Capital * 100",
                    interpretation="Unable to calculate - insufficient data for invested capital",
                    is_valid=False,
                    error_message="Missing data to calculate invested capital"
                )

            if invested_capital <= 0:
                return RatioResult(
                    name="Return on Invested Capital (ROIC)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="NOPAT / Invested Capital * 100",
                    interpretation="Invalid invested capital",
                    is_valid=False,
                    error_message="Invested capital must be positive"
                )

            # Estimate NOPAT (Net Operating Profit After Tax)
            # If we have net income and operating income, calculate implied tax rate
            if inputs.net_income is not None and inputs.operating_income != 0:
                implied_tax_rate = 1 - (inputs.net_income / inputs.operating_income)
                # Clamp tax rate to reasonable range (0-50%)
                implied_tax_rate = max(0, min(0.5, implied_tax_rate))
                nopat = inputs.operating_income * (1 - implied_tax_rate)
            else:
                # Use a standard corporate tax rate of 21% (US federal rate)
                nopat = inputs.operating_income * 0.79

            roic_value = (nopat / invested_capital) * 100

            # Interpretation based on common benchmarks
            if roic_value >= 15:
                interpretation = "Excellent capital efficiency - creating significant value"
            elif roic_value >= 10:
                interpretation = "Good capital efficiency - generating strong returns"
            elif roic_value >= 5:
                interpretation = "Adequate capital efficiency - covering cost of capital"
            elif roic_value >= 0:
                interpretation = "Poor capital efficiency - returns below cost of capital"
            else:
                interpretation = "Negative ROIC - destroying capital value"

            return RatioResult(
                name="Return on Invested Capital (ROIC)",
                value=roic_value,
                category=RatioCategory.PROFITABILITY,
                formula="NOPAT / Invested Capital * 100",
                interpretation=interpretation,
                metadata={
                    'operating_income': inputs.operating_income,
                    'nopat': nopat,
                    'invested_capital': invested_capital,
                    'net_income': inputs.net_income
                }
            )

        except Exception as e:
            logger.error(f"Error calculating ROIC: {e}")
            return RatioResult(
                name="Return on Invested Capital (ROIC)",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="NOPAT / Invested Capital * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_basic_eps(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Basic Earnings Per Share (EPS) = (Net Income - Preferred Dividends) / Weighted Average Shares Outstanding

        Basic EPS measures the portion of a company's profit allocated to each share of common stock.
        """
        try:
            if inputs.net_income is None or inputs.shares_outstanding is None:
                return RatioResult(
                    name="Basic Earnings Per Share (EPS)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="(Net Income - Preferred Dividends) / Weighted Average Shares",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing net income or shares outstanding data"
                )

            if inputs.shares_outstanding == 0:
                return RatioResult(
                    name="Basic Earnings Per Share (EPS)",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="(Net Income - Preferred Dividends) / Weighted Average Shares",
                    interpretation="Undefined - zero shares outstanding",
                    is_valid=False,
                    error_message="Shares outstanding cannot be zero"
                )

            # Calculate EPS (assuming no preferred dividends unless explicitly provided)
            # Note: In a real implementation, preferred dividends should be tracked separately
            net_income_to_common = inputs.net_income
            eps_value = net_income_to_common / inputs.shares_outstanding

            # Interpretation based on sign and magnitude
            if eps_value > 5:
                interpretation = "Strong earnings per share"
            elif eps_value > 2:
                interpretation = "Good earnings per share"
            elif eps_value > 0:
                interpretation = "Positive earnings per share"
            elif eps_value == 0:
                interpretation = "Break-even earnings"
            else:
                interpretation = "Negative earnings per share - company losing money"

            return RatioResult(
                name="Basic Earnings Per Share (EPS)",
                value=eps_value,
                category=RatioCategory.PROFITABILITY,
                formula="(Net Income - Preferred Dividends) / Weighted Average Shares",
                interpretation=interpretation,
                metadata={
                    'net_income': inputs.net_income,
                    'shares_outstanding': inputs.shares_outstanding
                }
            )

        except Exception as e:
            logger.error(f"Error calculating basic EPS: {e}")
            return RatioResult(
                name="Basic Earnings Per Share (EPS)",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="(Net Income - Preferred Dividends) / Weighted Average Shares",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_diluted_eps(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Diluted Earnings Per Share = (Net Income - Preferred Dividends) / (Weighted Average Shares + Dilutive Securities)

        Diluted EPS assumes all convertible securities (options, warrants, convertible bonds) are exercised.
        For simplicity, if dilutive securities count is not provided, we estimate it as 5% of basic shares.
        """
        try:
            if inputs.net_income is None or inputs.shares_outstanding is None:
                return RatioResult(
                    name="Diluted Earnings Per Share",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / (Shares + Dilutive Securities)",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing net income or shares outstanding data"
                )

            if inputs.shares_outstanding == 0:
                return RatioResult(
                    name="Diluted Earnings Per Share",
                    value=0.0,
                    category=RatioCategory.PROFITABILITY,
                    formula="Net Income / (Shares + Dilutive Securities)",
                    interpretation="Undefined - zero shares outstanding",
                    is_valid=False,
                    error_message="Shares outstanding cannot be zero"
                )

            # Estimate dilutive shares as 5% of basic shares (conservative estimate)
            # In a real implementation, this should come from the financial statements
            dilutive_shares_estimate = inputs.shares_outstanding * 0.05
            total_diluted_shares = inputs.shares_outstanding + dilutive_shares_estimate

            net_income_to_common = inputs.net_income
            diluted_eps_value = net_income_to_common / total_diluted_shares

            # Interpretation
            if diluted_eps_value > 5:
                interpretation = "Strong diluted earnings per share"
            elif diluted_eps_value > 2:
                interpretation = "Good diluted earnings per share"
            elif diluted_eps_value > 0:
                interpretation = "Positive diluted earnings per share"
            elif diluted_eps_value == 0:
                interpretation = "Break-even diluted earnings"
            else:
                interpretation = "Negative diluted EPS - company losing money"

            return RatioResult(
                name="Diluted Earnings Per Share",
                value=diluted_eps_value,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / (Shares + Dilutive Securities)",
                interpretation=interpretation,
                metadata={
                    'net_income': inputs.net_income,
                    'shares_outstanding': inputs.shares_outstanding,
                    'diluted_shares': total_diluted_shares,
                    'dilutive_securities_estimate': dilutive_shares_estimate
                }
            )

        except Exception as e:
            logger.error(f"Error calculating diluted EPS: {e}")
            return RatioResult(
                name="Diluted Earnings Per Share",
                value=0.0,
                category=RatioCategory.PROFITABILITY,
                formula="Net Income / (Shares + Dilutive Securities)",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    # =============================================================================
    # LEVERAGE/SOLVENCY RATIOS
    # =============================================================================

    def calculate_debt_to_assets_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Debt-to-Assets Ratio = Total Debt / Total Assets * 100

        Measures the proportion of assets financed by debt.
        """
        try:
            if inputs.total_debt is None or inputs.total_assets is None:
                return RatioResult(
                    name="Debt-to-Assets Ratio",
                    value=0.0,
                    category=RatioCategory.LEVERAGE,
                    formula="Total Debt / Total Assets * 100",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing total debt or total assets data"
                )

            if inputs.total_assets == 0:
                return RatioResult(
                    name="Debt-to-Assets Ratio",
                    value=0.0,
                    category=RatioCategory.LEVERAGE,
                    formula="Total Debt / Total Assets * 100",
                    interpretation="Undefined - zero total assets",
                    is_valid=False,
                    error_message="Total assets cannot be zero"
                )

            ratio_value = (inputs.total_debt / inputs.total_assets) * 100

            # Interpretation based on common benchmarks
            if ratio_value <= 30:
                interpretation = "Conservative debt levels - low financial risk"
            elif ratio_value <= 50:
                interpretation = "Moderate debt levels - manageable financial risk"
            elif ratio_value <= 70:
                interpretation = "High debt levels - elevated financial risk"
            else:
                interpretation = "Very high debt levels - significant financial risk"

            return RatioResult(
                name="Debt-to-Assets Ratio",
                value=ratio_value,
                category=RatioCategory.LEVERAGE,
                formula="Total Debt / Total Assets * 100",
                interpretation=interpretation,
                metadata={
                    'total_debt': inputs.total_debt,
                    'total_assets': inputs.total_assets
                }
            )

        except Exception as e:
            logger.error(f"Error calculating debt-to-assets ratio: {e}")
            return RatioResult(
                name="Debt-to-Assets Ratio",
                value=0.0,
                category=RatioCategory.LEVERAGE,
                formula="Total Debt / Total Assets * 100",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_debt_to_equity_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Debt-to-Equity Ratio = Total Debt / Shareholders' Equity

        Measures financial leverage and risk by comparing debt to equity.
        """
        try:
            if inputs.total_debt is None or inputs.shareholders_equity is None:
                return RatioResult(
                    name="Debt-to-Equity Ratio",
                    value=0.0,
                    category=RatioCategory.LEVERAGE,
                    formula="Total Debt / Shareholders' Equity",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing total debt or shareholders' equity data"
                )

            if inputs.shareholders_equity == 0:
                return RatioResult(
                    name="Debt-to-Equity Ratio",
                    value=float('inf'),
                    category=RatioCategory.LEVERAGE,
                    formula="Total Debt / Shareholders' Equity",
                    interpretation="Undefined - zero shareholders' equity",
                    is_valid=False,
                    error_message="Shareholders' equity cannot be zero"
                )

            ratio_value = inputs.total_debt / inputs.shareholders_equity

            # Interpretation based on common benchmarks
            if ratio_value <= 0.5:
                interpretation = "Conservative capital structure - low leverage"
            elif ratio_value <= 1.0:
                interpretation = "Moderate capital structure - balanced leverage"
            elif ratio_value <= 2.0:
                interpretation = "Aggressive capital structure - high leverage"
            else:
                interpretation = "Very aggressive capital structure - excessive leverage risk"

            return RatioResult(
                name="Debt-to-Equity Ratio",
                value=ratio_value,
                category=RatioCategory.LEVERAGE,
                formula="Total Debt / Shareholders' Equity",
                interpretation=interpretation,
                metadata={
                    'total_debt': inputs.total_debt,
                    'shareholders_equity': inputs.shareholders_equity
                }
            )

        except Exception as e:
            logger.error(f"Error calculating debt-to-equity ratio: {e}")
            return RatioResult(
                name="Debt-to-Equity Ratio",
                value=0.0,
                category=RatioCategory.LEVERAGE,
                formula="Total Debt / Shareholders' Equity",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_interest_coverage_ratio(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Interest Coverage Ratio = EBIT / Interest Expense

        Measures ability to pay interest on outstanding debt.
        """
        try:
            if inputs.ebit is None or inputs.interest_expense is None:
                return RatioResult(
                    name="Interest Coverage Ratio",
                    value=0.0,
                    category=RatioCategory.LEVERAGE,
                    formula="EBIT / Interest Expense",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing EBIT or interest expense data"
                )

            if inputs.interest_expense == 0:
                return RatioResult(
                    name="Interest Coverage Ratio",
                    value=float('inf'),
                    category=RatioCategory.LEVERAGE,
                    formula="EBIT / Interest Expense",
                    interpretation="No interest expense - debt-free operation",
                    metadata={
                        'ebit': inputs.ebit,
                        'interest_expense': inputs.interest_expense
                    }
                )

            ratio_value = inputs.ebit / inputs.interest_expense

            # Interpretation based on common benchmarks
            if ratio_value >= 10:
                interpretation = "Excellent ability to service debt interest"
            elif ratio_value >= 5:
                interpretation = "Good ability to service debt interest"
            elif ratio_value >= 2.5:
                interpretation = "Adequate ability to service debt interest"
            elif ratio_value >= 1.0:
                interpretation = "Marginal ability to service debt interest"
            else:
                interpretation = "Insufficient earnings to cover interest payments"

            return RatioResult(
                name="Interest Coverage Ratio",
                value=ratio_value,
                category=RatioCategory.LEVERAGE,
                formula="EBIT / Interest Expense",
                interpretation=interpretation,
                metadata={
                    'ebit': inputs.ebit,
                    'interest_expense': inputs.interest_expense
                }
            )

        except Exception as e:
            logger.error(f"Error calculating interest coverage ratio: {e}")
            return RatioResult(
                name="Interest Coverage Ratio",
                value=0.0,
                category=RatioCategory.LEVERAGE,
                formula="EBIT / Interest Expense",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    # =============================================================================
    # EFFICIENCY/ACTIVITY RATIOS
    # =============================================================================

    def calculate_asset_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Asset Turnover = Revenue / Total Assets

        Measures how efficiently assets are used to generate sales.
        """
        try:
            if inputs.revenue is None or inputs.total_assets is None:
                return RatioResult(
                    name="Asset Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Total Assets",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or total assets data"
                )

            if inputs.total_assets == 0:
                return RatioResult(
                    name="Asset Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Total Assets",
                    interpretation="Undefined - zero total assets",
                    is_valid=False,
                    error_message="Total assets cannot be zero"
                )

            ratio_value = inputs.revenue / inputs.total_assets

            # Interpretation based on common benchmarks (varies by industry)
            if ratio_value >= 2.0:
                interpretation = "Excellent asset utilization efficiency"
            elif ratio_value >= 1.0:
                interpretation = "Good asset utilization efficiency"
            elif ratio_value >= 0.5:
                interpretation = "Adequate asset utilization efficiency"
            else:
                interpretation = "Poor asset utilization - assets generating insufficient revenue"

            return RatioResult(
                name="Asset Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Total Assets",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'total_assets': inputs.total_assets
                }
            )

        except Exception as e:
            logger.error(f"Error calculating asset turnover: {e}")
            return RatioResult(
                name="Asset Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Total Assets",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_inventory_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Inventory Turnover = Cost of Goods Sold / Average Inventory

        Measures how efficiently inventory is managed and sold.
        Higher values indicate faster inventory movement.
        """
        try:
            if inputs.cost_of_goods_sold is None or inputs.inventory is None:
                return RatioResult(
                    name="Inventory Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Cost of Goods Sold / Average Inventory",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing COGS or inventory data"
                )

            if inputs.inventory == 0:
                return RatioResult(
                    name="Inventory Turnover",
                    value=float('inf'),
                    category=RatioCategory.EFFICIENCY,
                    formula="Cost of Goods Sold / Average Inventory",
                    interpretation="Undefined - zero inventory",
                    is_valid=False,
                    error_message="Inventory cannot be zero"
                )

            ratio_value = inputs.cost_of_goods_sold / inputs.inventory

            # Interpretation based on common benchmarks (varies by industry)
            if ratio_value >= 10:
                interpretation = "Excellent inventory management - very efficient turnover"
            elif ratio_value >= 6:
                interpretation = "Good inventory management - healthy turnover rate"
            elif ratio_value >= 4:
                interpretation = "Adequate inventory management - moderate turnover"
            elif ratio_value >= 2:
                interpretation = "Slow inventory turnover - potential overstocking"
            else:
                interpretation = "Very slow inventory turnover - significant inventory management concerns"

            return RatioResult(
                name="Inventory Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Cost of Goods Sold / Average Inventory",
                interpretation=interpretation,
                metadata={
                    'cost_of_goods_sold': inputs.cost_of_goods_sold,
                    'inventory': inputs.inventory
                }
            )

        except Exception as e:
            logger.error(f"Error calculating inventory turnover: {e}")
            return RatioResult(
                name="Inventory Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Cost of Goods Sold / Average Inventory",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_receivables_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Receivables Turnover = Revenue / Average Accounts Receivable

        Measures how efficiently a company collects revenue from credit customers.
        Higher values indicate faster collection.
        """
        try:
            if inputs.revenue is None or inputs.accounts_receivable is None:
                return RatioResult(
                    name="Receivables Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Accounts Receivable",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or accounts receivable data"
                )

            if inputs.accounts_receivable == 0:
                return RatioResult(
                    name="Receivables Turnover",
                    value=float('inf'),
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Accounts Receivable",
                    interpretation="No accounts receivable - cash-based business",
                    metadata={
                        'revenue': inputs.revenue,
                        'accounts_receivable': inputs.accounts_receivable
                    }
                )

            ratio_value = inputs.revenue / inputs.accounts_receivable

            # Interpretation based on common benchmarks
            if ratio_value >= 12:
                interpretation = "Excellent receivables collection - very efficient"
            elif ratio_value >= 8:
                interpretation = "Good receivables collection - healthy turnover"
            elif ratio_value >= 6:
                interpretation = "Adequate receivables collection - moderate efficiency"
            elif ratio_value >= 4:
                interpretation = "Slow receivables collection - collection improvements needed"
            else:
                interpretation = "Very slow receivables collection - significant collection issues"

            return RatioResult(
                name="Receivables Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Accounts Receivable",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'accounts_receivable': inputs.accounts_receivable
                }
            )

        except Exception as e:
            logger.error(f"Error calculating receivables turnover: {e}")
            return RatioResult(
                name="Receivables Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Accounts Receivable",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_payables_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Payables Turnover = Cost of Goods Sold / Average Accounts Payable

        Measures how quickly a company pays its suppliers.
        Higher values indicate faster payment to suppliers.
        Note: This assumes accounts_payable is available in RatioInputs
        (would need to be added to the dataclass if not present)
        """
        try:
            if inputs.cost_of_goods_sold is None:
                return RatioResult(
                    name="Payables Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Cost of Goods Sold / Average Accounts Payable",
                    interpretation="Unable to calculate - missing COGS data",
                    is_valid=False,
                    error_message="Missing cost of goods sold data"
                )

            # Note: accounts_payable might not be in RatioInputs yet
            # This is a placeholder implementation
            accounts_payable = getattr(inputs, 'accounts_payable', None)

            if accounts_payable is None:
                return RatioResult(
                    name="Payables Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Cost of Goods Sold / Average Accounts Payable",
                    interpretation="Unable to calculate - missing accounts payable data",
                    is_valid=False,
                    error_message="Missing accounts payable data"
                )

            if accounts_payable == 0:
                return RatioResult(
                    name="Payables Turnover",
                    value=float('inf'),
                    category=RatioCategory.EFFICIENCY,
                    formula="Cost of Goods Sold / Average Accounts Payable",
                    interpretation="Undefined - zero accounts payable",
                    is_valid=False,
                    error_message="Accounts payable cannot be zero"
                )

            ratio_value = inputs.cost_of_goods_sold / accounts_payable

            # Interpretation based on common benchmarks
            if ratio_value >= 12:
                interpretation = "Very fast supplier payments - may miss payment term advantages"
            elif ratio_value >= 8:
                interpretation = "Good supplier payment efficiency - balanced approach"
            elif ratio_value >= 6:
                interpretation = "Adequate supplier payment timing - moderate efficiency"
            elif ratio_value >= 4:
                interpretation = "Slow supplier payments - extended payment terms utilized"
            else:
                interpretation = "Very slow supplier payments - potential cash flow or credit concerns"

            return RatioResult(
                name="Payables Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Cost of Goods Sold / Average Accounts Payable",
                interpretation=interpretation,
                metadata={
                    'cost_of_goods_sold': inputs.cost_of_goods_sold,
                    'accounts_payable': accounts_payable
                }
            )

        except Exception as e:
            logger.error(f"Error calculating payables turnover: {e}")
            return RatioResult(
                name="Payables Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Cost of Goods Sold / Average Accounts Payable",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_days_sales_outstanding(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Days Sales Outstanding (DSO) = 365 / Receivables Turnover
        or DSO = (Accounts Receivable / Revenue) * 365

        Measures the average number of days to collect payment from customers.
        Lower values indicate faster collection.
        """
        try:
            if inputs.revenue is None or inputs.accounts_receivable is None:
                return RatioResult(
                    name="Days Sales Outstanding (DSO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Accounts Receivable / Revenue) * 365",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing revenue or accounts receivable data"
                )

            if inputs.revenue == 0:
                return RatioResult(
                    name="Days Sales Outstanding (DSO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Accounts Receivable / Revenue) * 365",
                    interpretation="Undefined - zero revenue",
                    is_valid=False,
                    error_message="Revenue cannot be zero"
                )

            dso_value = (inputs.accounts_receivable / inputs.revenue) * 365

            # Interpretation based on common benchmarks
            if dso_value <= 30:
                interpretation = "Excellent collection efficiency - fast payment collection"
            elif dso_value <= 45:
                interpretation = "Good collection efficiency - healthy collection period"
            elif dso_value <= 60:
                interpretation = "Adequate collection efficiency - moderate collection period"
            elif dso_value <= 90:
                interpretation = "Slow collection - extended payment terms or collection issues"
            else:
                interpretation = "Very slow collection - significant collection and credit risk concerns"

            return RatioResult(
                name="Days Sales Outstanding (DSO)",
                value=dso_value,
                category=RatioCategory.EFFICIENCY,
                formula="(Accounts Receivable / Revenue) * 365",
                interpretation=interpretation,
                metadata={
                    'accounts_receivable': inputs.accounts_receivable,
                    'revenue': inputs.revenue,
                    'receivables_turnover': inputs.revenue / inputs.accounts_receivable if inputs.accounts_receivable != 0 else 0
                }
            )

        except Exception as e:
            logger.error(f"Error calculating DSO: {e}")
            return RatioResult(
                name="Days Sales Outstanding (DSO)",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="(Accounts Receivable / Revenue) * 365",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_days_inventory_outstanding(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Days Inventory Outstanding (DIO) = 365 / Inventory Turnover
        or DIO = (Inventory / Cost of Goods Sold) * 365

        Measures the average number of days inventory is held before being sold.
        Lower values indicate faster inventory movement.
        """
        try:
            if inputs.cost_of_goods_sold is None or inputs.inventory is None:
                return RatioResult(
                    name="Days Inventory Outstanding (DIO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Inventory / COGS) * 365",
                    interpretation="Unable to calculate - missing data",
                    is_valid=False,
                    error_message="Missing COGS or inventory data"
                )

            if inputs.cost_of_goods_sold == 0:
                return RatioResult(
                    name="Days Inventory Outstanding (DIO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Inventory / COGS) * 365",
                    interpretation="Undefined - zero COGS",
                    is_valid=False,
                    error_message="Cost of goods sold cannot be zero"
                )

            dio_value = (inputs.inventory / inputs.cost_of_goods_sold) * 365

            # Interpretation based on common benchmarks (varies significantly by industry)
            if dio_value <= 30:
                interpretation = "Excellent inventory efficiency - very fast turnover"
            elif dio_value <= 60:
                interpretation = "Good inventory efficiency - healthy turnover rate"
            elif dio_value <= 90:
                interpretation = "Adequate inventory efficiency - moderate turnover"
            elif dio_value <= 120:
                interpretation = "Slow inventory turnover - potential overstocking"
            else:
                interpretation = "Very slow inventory turnover - significant inventory management concerns"

            return RatioResult(
                name="Days Inventory Outstanding (DIO)",
                value=dio_value,
                category=RatioCategory.EFFICIENCY,
                formula="(Inventory / COGS) * 365",
                interpretation=interpretation,
                metadata={
                    'inventory': inputs.inventory,
                    'cost_of_goods_sold': inputs.cost_of_goods_sold,
                    'inventory_turnover': inputs.cost_of_goods_sold / inputs.inventory if inputs.inventory != 0 else 0
                }
            )

        except Exception as e:
            logger.error(f"Error calculating DIO: {e}")
            return RatioResult(
                name="Days Inventory Outstanding (DIO)",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="(Inventory / COGS) * 365",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_days_payable_outstanding(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Days Payable Outstanding (DPO) = 365 / Payables Turnover
        or DPO = (Accounts Payable / Cost of Goods Sold) * 365

        Measures the average number of days to pay suppliers.
        Higher values indicate longer payment terms utilized.
        """
        try:
            if inputs.cost_of_goods_sold is None:
                return RatioResult(
                    name="Days Payable Outstanding (DPO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Accounts Payable / COGS) * 365",
                    interpretation="Unable to calculate - missing COGS data",
                    is_valid=False,
                    error_message="Missing cost of goods sold data"
                )

            # Note: accounts_payable might not be in RatioInputs yet
            accounts_payable = getattr(inputs, 'accounts_payable', None)

            if accounts_payable is None:
                return RatioResult(
                    name="Days Payable Outstanding (DPO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Accounts Payable / COGS) * 365",
                    interpretation="Unable to calculate - missing accounts payable data",
                    is_valid=False,
                    error_message="Missing accounts payable data"
                )

            if inputs.cost_of_goods_sold == 0:
                return RatioResult(
                    name="Days Payable Outstanding (DPO)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="(Accounts Payable / COGS) * 365",
                    interpretation="Undefined - zero COGS",
                    is_valid=False,
                    error_message="Cost of goods sold cannot be zero"
                )

            dpo_value = (accounts_payable / inputs.cost_of_goods_sold) * 365

            # Interpretation based on common benchmarks
            if dpo_value >= 90:
                interpretation = "Extended payment terms - strong supplier relationships or cash conservation"
            elif dpo_value >= 60:
                interpretation = "Good payment timing - balanced cash flow management"
            elif dpo_value >= 45:
                interpretation = "Adequate payment timing - moderate supplier payment period"
            elif dpo_value >= 30:
                interpretation = "Fast supplier payments - may be missing payment term advantages"
            else:
                interpretation = "Very fast supplier payments - potential early payment discounts or weak negotiating position"

            return RatioResult(
                name="Days Payable Outstanding (DPO)",
                value=dpo_value,
                category=RatioCategory.EFFICIENCY,
                formula="(Accounts Payable / COGS) * 365",
                interpretation=interpretation,
                metadata={
                    'accounts_payable': accounts_payable,
                    'cost_of_goods_sold': inputs.cost_of_goods_sold,
                    'payables_turnover': inputs.cost_of_goods_sold / accounts_payable if accounts_payable != 0 else 0
                }
            )

        except Exception as e:
            logger.error(f"Error calculating DPO: {e}")
            return RatioResult(
                name="Days Payable Outstanding (DPO)",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="(Accounts Payable / COGS) * 365",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_cash_conversion_cycle(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Cash Conversion Cycle (CCC) = DSO + DIO - DPO

        Measures the time (in days) between cash outlay for operations and cash collection.
        Lower values indicate better working capital efficiency.
        """
        try:
            # Calculate component metrics
            dso_result = self.calculate_days_sales_outstanding(inputs)
            dio_result = self.calculate_days_inventory_outstanding(inputs)
            dpo_result = self.calculate_days_payable_outstanding(inputs)

            # Check if all components are valid
            if not (dso_result.is_valid and dio_result.is_valid and dpo_result.is_valid):
                missing_components = []
                if not dso_result.is_valid:
                    missing_components.append("DSO")
                if not dio_result.is_valid:
                    missing_components.append("DIO")
                if not dpo_result.is_valid:
                    missing_components.append("DPO")

                return RatioResult(
                    name="Cash Conversion Cycle (CCC)",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="DSO + DIO - DPO",
                    interpretation=f"Unable to calculate - missing {', '.join(missing_components)} data",
                    is_valid=False,
                    error_message=f"Missing components: {', '.join(missing_components)}"
                )

            ccc_value = dso_result.value + dio_result.value - dpo_result.value

            # Interpretation based on common benchmarks
            if ccc_value <= 0:
                interpretation = "Negative CCC - exceptional working capital efficiency, collecting before paying"
            elif ccc_value <= 30:
                interpretation = "Excellent cash conversion - very efficient working capital management"
            elif ccc_value <= 60:
                interpretation = "Good cash conversion - healthy working capital cycle"
            elif ccc_value <= 90:
                interpretation = "Adequate cash conversion - moderate working capital efficiency"
            elif ccc_value <= 120:
                interpretation = "Slow cash conversion - working capital improvements needed"
            else:
                interpretation = "Very slow cash conversion - significant working capital management concerns"

            return RatioResult(
                name="Cash Conversion Cycle (CCC)",
                value=ccc_value,
                category=RatioCategory.EFFICIENCY,
                formula="DSO + DIO - DPO",
                interpretation=interpretation,
                metadata={
                    'dso': dso_result.value,
                    'dio': dio_result.value,
                    'dpo': dpo_result.value
                }
            )

        except Exception as e:
            logger.error(f"Error calculating cash conversion cycle: {e}")
            return RatioResult(
                name="Cash Conversion Cycle (CCC)",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="DSO + DIO - DPO",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_fixed_asset_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Fixed Asset Turnover = Revenue / Average Net Fixed Assets

        Measures how efficiently fixed assets generate sales revenue.
        Higher values indicate better asset utilization.
        Note: This assumes net_fixed_assets is available in RatioInputs
        """
        try:
            if inputs.revenue is None:
                return RatioResult(
                    name="Fixed Asset Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Net Fixed Assets",
                    interpretation="Unable to calculate - missing revenue data",
                    is_valid=False,
                    error_message="Missing revenue data"
                )

            # Note: net_fixed_assets might not be in RatioInputs yet
            # Can be calculated as Total Assets - Current Assets or use PP&E
            net_fixed_assets = getattr(inputs, 'net_fixed_assets', None)

            # Fallback: calculate from total and current assets
            if net_fixed_assets is None and inputs.total_assets and inputs.current_assets:
                net_fixed_assets = inputs.total_assets - inputs.current_assets

            if net_fixed_assets is None:
                return RatioResult(
                    name="Fixed Asset Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Net Fixed Assets",
                    interpretation="Unable to calculate - missing fixed assets data",
                    is_valid=False,
                    error_message="Missing net fixed assets data"
                )

            if net_fixed_assets == 0:
                return RatioResult(
                    name="Fixed Asset Turnover",
                    value=float('inf'),
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Net Fixed Assets",
                    interpretation="Undefined - zero fixed assets (asset-light business model)",
                    metadata={
                        'revenue': inputs.revenue,
                        'net_fixed_assets': net_fixed_assets
                    }
                )

            ratio_value = inputs.revenue / net_fixed_assets

            # Interpretation based on common benchmarks (varies by industry)
            if ratio_value >= 5.0:
                interpretation = "Excellent fixed asset utilization - highly efficient operations"
            elif ratio_value >= 3.0:
                interpretation = "Good fixed asset utilization - healthy productivity"
            elif ratio_value >= 1.5:
                interpretation = "Adequate fixed asset utilization - moderate efficiency"
            elif ratio_value >= 0.5:
                interpretation = "Poor fixed asset utilization - underutilized capacity"
            else:
                interpretation = "Very poor fixed asset utilization - significant idle capacity or expansion phase"

            return RatioResult(
                name="Fixed Asset Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Net Fixed Assets",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'net_fixed_assets': net_fixed_assets
                }
            )

        except Exception as e:
            logger.error(f"Error calculating fixed asset turnover: {e}")
            return RatioResult(
                name="Fixed Asset Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Net Fixed Assets",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    def calculate_working_capital_turnover(self, inputs: RatioInputs) -> RatioResult:
        """
        Calculate Working Capital Turnover = Revenue / Average Working Capital

        Measures how efficiently working capital generates sales revenue.
        Higher values indicate more efficient use of working capital.
        """
        try:
            if inputs.revenue is None:
                return RatioResult(
                    name="Working Capital Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Working Capital",
                    interpretation="Unable to calculate - missing revenue data",
                    is_valid=False,
                    error_message="Missing revenue data"
                )

            if inputs.current_assets is None or inputs.current_liabilities is None:
                return RatioResult(
                    name="Working Capital Turnover",
                    value=0.0,
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Working Capital",
                    interpretation="Unable to calculate - missing working capital data",
                    is_valid=False,
                    error_message="Missing current assets or current liabilities data"
                )

            working_capital = inputs.current_assets - inputs.current_liabilities

            if working_capital == 0:
                return RatioResult(
                    name="Working Capital Turnover",
                    value=float('inf'),
                    category=RatioCategory.EFFICIENCY,
                    formula="Revenue / Average Working Capital",
                    interpretation="Undefined - zero working capital",
                    is_valid=False,
                    error_message="Working capital cannot be zero"
                )

            # Handle negative working capital
            if working_capital < 0:
                ratio_value = inputs.revenue / abs(working_capital)
                interpretation = f"Negative working capital ({working_capital:,.0f}) - company operating on supplier credit"
            else:
                ratio_value = inputs.revenue / working_capital

                # Interpretation based on common benchmarks
                if ratio_value >= 10:
                    interpretation = "Very high working capital efficiency - may indicate tight working capital"
                elif ratio_value >= 6:
                    interpretation = "Excellent working capital efficiency - efficient use of resources"
                elif ratio_value >= 4:
                    interpretation = "Good working capital efficiency - healthy turnover"
                elif ratio_value >= 2:
                    interpretation = "Adequate working capital efficiency - moderate utilization"
                else:
                    interpretation = "Low working capital efficiency - excess working capital or low sales"

            return RatioResult(
                name="Working Capital Turnover",
                value=ratio_value,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Working Capital",
                interpretation=interpretation,
                metadata={
                    'revenue': inputs.revenue,
                    'working_capital': working_capital,
                    'current_assets': inputs.current_assets,
                    'current_liabilities': inputs.current_liabilities
                }
            )

        except Exception as e:
            logger.error(f"Error calculating working capital turnover: {e}")
            return RatioResult(
                name="Working Capital Turnover",
                value=0.0,
                category=RatioCategory.EFFICIENCY,
                formula="Revenue / Average Working Capital",
                interpretation="Calculation error",
                is_valid=False,
                error_message=str(e)
            )

    # =============================================================================
    # COMPREHENSIVE CALCULATION METHODS
    # =============================================================================

    def calculate_all_ratios(self, inputs: RatioInputs) -> Dict[str, RatioResult]:
        """
        Calculate all available financial ratios based on provided inputs

        Args:
            inputs: RatioInputs object containing financial statement data

        Returns:
            Dictionary mapping ratio names to RatioResult objects
        """
        results = {}

        # Calculate liquidity ratios
        results['current_ratio'] = self.calculate_current_ratio(inputs)
        results['quick_ratio'] = self.calculate_quick_ratio(inputs)
        results['cash_ratio'] = self.calculate_cash_ratio(inputs)
        results['working_capital'] = self.calculate_working_capital(inputs)
        results['working_capital_ratio'] = self.calculate_working_capital_ratio(inputs)
        results['operating_cash_flow_ratio'] = self.calculate_operating_cash_flow_ratio(inputs)

        # Calculate profitability ratios
        results['gross_profit_margin'] = self.calculate_gross_profit_margin(inputs)
        results['operating_profit_margin'] = self.calculate_operating_profit_margin(inputs)
        results['net_profit_margin'] = self.calculate_net_profit_margin(inputs)
        results['ebitda_margin'] = self.calculate_ebitda_margin(inputs)
        results['return_on_assets'] = self.calculate_return_on_assets(inputs)
        results['return_on_equity'] = self.calculate_return_on_equity(inputs)
        results['return_on_invested_capital'] = self.calculate_return_on_invested_capital(inputs)
        results['basic_eps'] = self.calculate_basic_eps(inputs)
        results['diluted_eps'] = self.calculate_diluted_eps(inputs)

        # Calculate leverage ratios
        results['debt_to_assets_ratio'] = self.calculate_debt_to_assets_ratio(inputs)
        results['debt_to_equity_ratio'] = self.calculate_debt_to_equity_ratio(inputs)
        results['interest_coverage_ratio'] = self.calculate_interest_coverage_ratio(inputs)

        # Calculate efficiency ratios
        results['asset_turnover'] = self.calculate_asset_turnover(inputs)
        results['inventory_turnover'] = self.calculate_inventory_turnover(inputs)
        results['receivables_turnover'] = self.calculate_receivables_turnover(inputs)
        results['payables_turnover'] = self.calculate_payables_turnover(inputs)
        results['days_sales_outstanding'] = self.calculate_days_sales_outstanding(inputs)
        results['days_inventory_outstanding'] = self.calculate_days_inventory_outstanding(inputs)
        results['days_payable_outstanding'] = self.calculate_days_payable_outstanding(inputs)
        results['cash_conversion_cycle'] = self.calculate_cash_conversion_cycle(inputs)
        results['fixed_asset_turnover'] = self.calculate_fixed_asset_turnover(inputs)
        results['working_capital_turnover'] = self.calculate_working_capital_turnover(inputs)

        # Filter out invalid results if requested
        valid_results = {name: result for name, result in results.items() if result.is_valid}

        logger.info(f"Calculated {len(valid_results)} valid ratios out of {len(results)} attempted")

        return results

    def get_ratios_by_category(self, category: RatioCategory) -> List[str]:
        """Get list of supported ratios for a specific category"""
        return self.supported_ratios.get(category, [])

    def get_all_supported_ratios(self) -> Dict[RatioCategory, List[str]]:
        """Get all supported ratios organized by category"""
        return self.supported_ratios.copy()

    def validate_inputs(self, inputs: RatioInputs) -> Dict[str, List[str]]:
        """
        Validate inputs and return missing data by category

        Returns:
            Dictionary mapping categories to lists of missing required fields
        """
        missing_data = {category.value: [] for category in RatioCategory}

        # Check liquidity ratio requirements
        if inputs.current_assets is None:
            missing_data[RatioCategory.LIQUIDITY.value].append('current_assets')
        if inputs.current_liabilities is None:
            missing_data[RatioCategory.LIQUIDITY.value].append('current_liabilities')
        if inputs.cash_and_equivalents is None:
            missing_data[RatioCategory.LIQUIDITY.value].append('cash_and_equivalents')

        # Check profitability ratio requirements
        if inputs.revenue is None:
            missing_data[RatioCategory.PROFITABILITY.value].append('revenue')
        if inputs.net_income is None:
            missing_data[RatioCategory.PROFITABILITY.value].append('net_income')
        if inputs.total_assets is None:
            missing_data[RatioCategory.PROFITABILITY.value].append('total_assets')
        if inputs.shareholders_equity is None:
            missing_data[RatioCategory.PROFITABILITY.value].append('shareholders_equity')

        # Check leverage ratio requirements
        if inputs.total_debt is None:
            missing_data[RatioCategory.LEVERAGE.value].append('total_debt')
        if inputs.ebit is None:
            missing_data[RatioCategory.LEVERAGE.value].append('ebit')
        if inputs.interest_expense is None:
            missing_data[RatioCategory.LEVERAGE.value].append('interest_expense')

        # Remove empty categories
        missing_data = {k: v for k, v in missing_data.items() if v}

        return missing_data