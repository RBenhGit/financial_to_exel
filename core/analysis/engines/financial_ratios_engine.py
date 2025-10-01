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
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None

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
                'return_on_assets', 'return_on_equity', 'return_on_invested_capital',
                'ebitda_margin', 'ebit_margin'
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
        results['net_profit_margin'] = self.calculate_net_profit_margin(inputs)
        results['return_on_assets'] = self.calculate_return_on_assets(inputs)
        results['return_on_equity'] = self.calculate_return_on_equity(inputs)

        # Calculate leverage ratios
        results['debt_to_assets_ratio'] = self.calculate_debt_to_assets_ratio(inputs)
        results['debt_to_equity_ratio'] = self.calculate_debt_to_equity_ratio(inputs)
        results['interest_coverage_ratio'] = self.calculate_interest_coverage_ratio(inputs)

        # Calculate efficiency ratios
        results['asset_turnover'] = self.calculate_asset_turnover(inputs)

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