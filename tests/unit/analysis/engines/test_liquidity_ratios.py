"""
Unit tests for liquidity ratio calculations in FinancialCalculationEngine.

Tests comprehensive liquidity ratio calculations including:
- Current Ratio
- Quick Ratio (Acid-Test Ratio)
- Cash Ratio
- Working Capital

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
import math
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class TestLiquidityRatios:
    """Test suite for liquidity ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Current Ratio Tests
    # =====================

    def test_calculate_current_ratio_normal_case(self):
        """Test current ratio calculation with normal values"""
        result = self.engine.calculate_current_ratio(
            current_assets=200000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['current_assets'] == 200000
        assert result.metadata['current_liabilities'] == 100000
        assert result.metadata['calculation_method'] == 'Current Ratio = Current Assets / Current Liabilities'
        assert result.metadata['interpretation'] == "Strong liquidity position"

    def test_calculate_current_ratio_weak_liquidity(self):
        """Test current ratio calculation indicating weak liquidity"""
        result = self.engine.calculate_current_ratio(
            current_assets=80000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.8
        assert result.metadata['interpretation'] == "Potential liquidity concerns"

    def test_calculate_current_ratio_adequate_liquidity(self):
        """Test current ratio calculation indicating adequate liquidity"""
        result = self.engine.calculate_current_ratio(
            current_assets=150000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 1.5
        assert result.metadata['interpretation'] == "Adequate liquidity"

    def test_calculate_current_ratio_zero_liabilities(self):
        """Test current ratio with zero current liabilities"""
        result = self.engine.calculate_current_ratio(
            current_assets=100000,
            current_liabilities=0
        )

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "Current liabilities cannot be zero" in result.error_message

    def test_calculate_current_ratio_none_inputs(self):
        """Test current ratio with None inputs"""
        result = self.engine.calculate_current_ratio(
            current_assets=None,
            current_liabilities=100000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    def test_calculate_current_ratio_negative_values(self):
        """Test current ratio with negative values (should still calculate but warn)"""
        result = self.engine.calculate_current_ratio(
            current_assets=-50000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == -0.5

    # =====================
    # Quick Ratio Tests
    # =====================

    def test_calculate_quick_ratio_normal_case(self):
        """Test quick ratio calculation with normal values"""
        result = self.engine.calculate_quick_ratio(
            current_assets=200000,
            inventory=50000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 1.5
        assert result.metadata['quick_assets'] == 150000
        assert result.metadata['interpretation'] == "Strong immediate liquidity"

    def test_calculate_quick_ratio_moderate_liquidity(self):
        """Test quick ratio indicating moderate liquidity"""
        result = self.engine.calculate_quick_ratio(
            current_assets=100000,
            inventory=25000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.75
        assert result.metadata['interpretation'] == "Moderate liquidity"

    def test_calculate_quick_ratio_weak_liquidity(self):
        """Test quick ratio indicating weak liquidity"""
        result = self.engine.calculate_quick_ratio(
            current_assets=100000,
            inventory=70000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.3
        assert result.metadata['interpretation'] == "Weak immediate liquidity"

    def test_calculate_quick_ratio_inventory_exceeds_assets(self):
        """Test quick ratio when inventory exceeds current assets"""
        result = self.engine.calculate_quick_ratio(
            current_assets=100000,
            inventory=120000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == -0.2  # (100000 - 120000) / 100000

    def test_calculate_quick_ratio_zero_liabilities(self):
        """Test quick ratio with zero current liabilities"""
        result = self.engine.calculate_quick_ratio(
            current_assets=100000,
            inventory=25000,
            current_liabilities=0
        )

        assert result.is_valid is False
        assert "Current liabilities cannot be zero" in result.error_message

    def test_calculate_quick_ratio_none_inputs(self):
        """Test quick ratio with None inputs"""
        result = self.engine.calculate_quick_ratio(
            current_assets=100000,
            inventory=None,
            current_liabilities=100000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    # =====================
    # Cash Ratio Tests
    # =====================

    def test_calculate_cash_ratio_normal_case(self):
        """Test cash ratio calculation with normal values"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=30000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.3
        assert result.metadata['cash_and_equivalents'] == 30000
        assert result.metadata['interpretation'] == "Strong cash position"

    def test_calculate_cash_ratio_adequate_position(self):
        """Test cash ratio indicating adequate cash position"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=15000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.15
        assert result.metadata['interpretation'] == "Adequate cash position"

    def test_calculate_cash_ratio_limited_position(self):
        """Test cash ratio indicating limited cash position"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=5000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.05
        assert result.metadata['interpretation'] == "Limited cash position"

    def test_calculate_cash_ratio_zero_cash(self):
        """Test cash ratio with zero cash"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=0,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0.0

    def test_calculate_cash_ratio_zero_liabilities(self):
        """Test cash ratio with zero current liabilities"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=50000,
            current_liabilities=0
        )

        assert result.is_valid is False
        assert "Current liabilities cannot be zero" in result.error_message

    def test_calculate_cash_ratio_negative_cash(self):
        """Test cash ratio with negative cash (should warn but calculate)"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=-10000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == -0.1

    def test_calculate_cash_ratio_none_inputs(self):
        """Test cash ratio with None inputs"""
        result = self.engine.calculate_cash_ratio(
            cash_and_equivalents=None,
            current_liabilities=100000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    # =====================
    # Working Capital Tests
    # =====================

    def test_calculate_working_capital_positive(self):
        """Test working capital calculation with positive result"""
        result = self.engine.calculate_working_capital(
            current_assets=200000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 100000
        assert result.metadata['current_assets'] == 200000
        assert result.metadata['current_liabilities'] == 100000
        assert result.metadata['calculation_method'] == 'Working Capital = Current Assets - Current Liabilities'
        assert result.metadata['interpretation'] == "Moderate working capital position"

    def test_calculate_working_capital_strong_position(self):
        """Test working capital indicating strong position"""
        result = self.engine.calculate_working_capital(
            current_assets=200000,
            current_liabilities=50000
        )

        assert result.is_valid is True
        assert result.value == 150000
        assert result.metadata['interpretation'] == "Strong working capital position"

    def test_calculate_working_capital_negative(self):
        """Test working capital calculation with negative result"""
        result = self.engine.calculate_working_capital(
            current_assets=80000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == -20000
        assert result.metadata['interpretation'] == "Negative working capital - potential liquidity issues"

    def test_calculate_working_capital_zero(self):
        """Test working capital calculation with zero result"""
        result = self.engine.calculate_working_capital(
            current_assets=100000,
            current_liabilities=100000
        )

        assert result.is_valid is True
        assert result.value == 0
        assert result.metadata['interpretation'] == "Negative working capital - potential liquidity issues"

    def test_calculate_working_capital_none_inputs(self):
        """Test working capital with None inputs"""
        result = self.engine.calculate_working_capital(
            current_assets=None,
            current_liabilities=100000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    # =====================
    # Integration Tests
    # =====================

    def test_liquidity_ratios_consistency(self):
        """Test that all liquidity ratios are consistent with same inputs"""
        current_assets = 200000
        inventory = 50000
        cash_and_equivalents = 30000
        current_liabilities = 100000

        current_ratio = self.engine.calculate_current_ratio(current_assets, current_liabilities)
        quick_ratio = self.engine.calculate_quick_ratio(current_assets, inventory, current_liabilities)
        cash_ratio = self.engine.calculate_cash_ratio(cash_and_equivalents, current_liabilities)
        working_capital = self.engine.calculate_working_capital(current_assets, current_liabilities)

        # All should be valid
        assert all([current_ratio.is_valid, quick_ratio.is_valid, cash_ratio.is_valid, working_capital.is_valid])

        # Quick ratio should be less than current ratio
        assert quick_ratio.value < current_ratio.value

        # Cash ratio should be less than quick ratio (assuming cash < quick assets)
        assert cash_ratio.value < quick_ratio.value

    @pytest.mark.parametrize("current_assets,current_liabilities,expected_ratio", [
        (100000, 50000, 2.0),
        (150000, 100000, 1.5),
        (75000, 100000, 0.75),
        (200000, 80000, 2.5),
    ])
    def test_current_ratio_parametrized(self, current_assets, current_liabilities, expected_ratio):
        """Parametrized test for current ratio calculations"""
        result = self.engine.calculate_current_ratio(current_assets, current_liabilities)
        assert result.is_valid is True
        assert abs(result.value - expected_ratio) < 0.001  # Handle floating point precision

    @pytest.mark.parametrize("cash,liabilities,expected_ratio", [
        (20000, 100000, 0.2),
        (10000, 100000, 0.1),
        (5000, 100000, 0.05),
        (50000, 100000, 0.5),
    ])
    def test_cash_ratio_parametrized(self, cash, liabilities, expected_ratio):
        """Parametrized test for cash ratio calculations"""
        result = self.engine.calculate_cash_ratio(cash, liabilities)
        assert result.is_valid is True
        assert abs(result.value - expected_ratio) < 0.001