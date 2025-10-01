"""
Unit tests for liquidity ratio calculations in FinancialRatiosEngine.

Tests comprehensive liquidity ratio calculations including:
- Current Ratio
- Quick Ratio (Acid-Test Ratio)
- Cash Ratio
- Working Capital
- Working Capital Ratio
- Operating Cash Flow Ratio

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
from core.analysis.engines.financial_ratios_engine import (
    FinancialRatiosEngine,
    RatioInputs,
    RatioResult,
    RatioCategory
)


class TestLiquidityRatiosEngine:
    """Test suite for liquidity ratio calculations in FinancialRatiosEngine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialRatiosEngine()

    # =====================
    # Current Ratio Tests
    # =====================

    def test_calculate_current_ratio_strong_liquidity(self):
        """Test current ratio calculation with strong liquidity position"""
        inputs = RatioInputs(
            current_assets=200000,
            current_liabilities=100000
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.category == RatioCategory.LIQUIDITY
        assert "Strong liquidity position" in result.interpretation
        assert result.metadata['current_assets'] == 200000
        assert result.metadata['current_liabilities'] == 100000

    def test_calculate_current_ratio_good_liquidity(self):
        """Test current ratio calculation indicating good liquidity"""
        inputs = RatioInputs(
            current_assets=160000,
            current_liabilities=100000
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.6
        assert "Good liquidity position" in result.interpretation

    def test_calculate_current_ratio_adequate_liquidity(self):
        """Test current ratio calculation indicating adequate liquidity"""
        inputs = RatioInputs(
            current_assets=110000,
            current_liabilities=100000
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.1
        assert "Adequate liquidity position" in result.interpretation

    def test_calculate_current_ratio_weak_liquidity(self):
        """Test current ratio calculation indicating weak liquidity"""
        inputs = RatioInputs(
            current_assets=80000,
            current_liabilities=100000
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.8
        assert "Weak liquidity position" in result.interpretation

    def test_calculate_current_ratio_zero_liabilities(self):
        """Test current ratio with zero current liabilities"""
        inputs = RatioInputs(
            current_assets=100000,
            current_liabilities=0
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "Current liabilities cannot be zero" in result.error_message

    def test_calculate_current_ratio_missing_data(self):
        """Test current ratio with missing data"""
        inputs = RatioInputs(
            current_assets=None,
            current_liabilities=100000
        )

        result = self.engine.calculate_current_ratio(inputs)

        assert result.is_valid is False
        assert "missing data" in result.interpretation.lower()

    # =====================
    # Quick Ratio Tests
    # =====================

    def test_calculate_quick_ratio_strong_liquidity(self):
        """Test quick ratio calculation with strong immediate liquidity"""
        inputs = RatioInputs(
            current_assets=200000,
            inventory=40000,
            current_liabilities=100000
        )

        result = self.engine.calculate_quick_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.6  # (200000 - 40000) / 100000
        assert result.category == RatioCategory.LIQUIDITY
        assert "Strong quick liquidity position" in result.interpretation

    def test_calculate_quick_ratio_without_inventory(self):
        """Test quick ratio when inventory is not provided (assumes 0)"""
        inputs = RatioInputs(
            current_assets=150000,
            inventory=None,
            current_liabilities=100000
        )

        result = self.engine.calculate_quick_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.5
        assert result.metadata['inventory'] == 0.0

    def test_calculate_quick_ratio_adequate_liquidity(self):
        """Test quick ratio indicating adequate liquidity"""
        inputs = RatioInputs(
            current_assets=100000,
            inventory=15000,
            current_liabilities=100000
        )

        result = self.engine.calculate_quick_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.85
        assert "Adequate quick liquidity position" in result.interpretation

    def test_calculate_quick_ratio_weak_liquidity(self):
        """Test quick ratio indicating weak liquidity"""
        inputs = RatioInputs(
            current_assets=100000,
            inventory=60000,
            current_liabilities=100000
        )

        result = self.engine.calculate_quick_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.4
        assert "Weak quick liquidity" in result.interpretation

    # =====================
    # Cash Ratio Tests
    # =====================

    def test_calculate_cash_ratio_strong_position(self):
        """Test cash ratio calculation with strong cash position"""
        inputs = RatioInputs(
            cash_and_equivalents=60000,
            current_liabilities=100000
        )

        result = self.engine.calculate_cash_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.6
        assert result.category == RatioCategory.LIQUIDITY
        assert "Strong cash position" in result.interpretation

    def test_calculate_cash_ratio_good_position(self):
        """Test cash ratio indicating good cash position"""
        inputs = RatioInputs(
            cash_and_equivalents=25000,
            current_liabilities=100000
        )

        result = self.engine.calculate_cash_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.25
        assert "Good cash position" in result.interpretation

    def test_calculate_cash_ratio_adequate_position(self):
        """Test cash ratio indicating adequate cash reserves"""
        inputs = RatioInputs(
            cash_and_equivalents=12000,
            current_liabilities=100000
        )

        result = self.engine.calculate_cash_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.12
        assert "Adequate cash reserves" in result.interpretation

    def test_calculate_cash_ratio_low_reserves(self):
        """Test cash ratio indicating low cash reserves"""
        inputs = RatioInputs(
            cash_and_equivalents=5000,
            current_liabilities=100000
        )

        result = self.engine.calculate_cash_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.05
        assert "Low cash reserves" in result.interpretation

    # =====================
    # Working Capital Tests
    # =====================

    def test_calculate_working_capital_strong_position(self):
        """Test working capital calculation with strong position"""
        inputs = RatioInputs(
            current_assets=250000,
            current_liabilities=100000
        )

        result = self.engine.calculate_working_capital(inputs)

        assert result.is_valid is True
        assert result.value == 150000
        assert result.category == RatioCategory.LIQUIDITY
        assert "Strong positive working capital" in result.interpretation

    def test_calculate_working_capital_positive(self):
        """Test working capital calculation with positive result"""
        inputs = RatioInputs(
            current_assets=150000,
            current_liabilities=100000
        )

        result = self.engine.calculate_working_capital(inputs)

        assert result.is_valid is True
        assert result.value == 50000
        # 50000 is 33.3% of 150000, which is > 20%, so it's "Strong"
        assert "Strong positive working capital" in result.interpretation

    def test_calculate_working_capital_zero(self):
        """Test working capital calculation with zero result"""
        inputs = RatioInputs(
            current_assets=100000,
            current_liabilities=100000
        )

        result = self.engine.calculate_working_capital(inputs)

        assert result.is_valid is True
        assert result.value == 0
        assert "Zero working capital" in result.interpretation

    def test_calculate_working_capital_negative(self):
        """Test working capital calculation with negative result"""
        inputs = RatioInputs(
            current_assets=80000,
            current_liabilities=100000
        )

        result = self.engine.calculate_working_capital(inputs)

        assert result.is_valid is True
        assert result.value == -20000
        assert "Negative working capital" in result.interpretation

    # =====================
    # Working Capital Ratio Tests
    # =====================

    def test_calculate_working_capital_ratio_high(self):
        """Test working capital ratio with high ratio"""
        inputs = RatioInputs(
            current_assets=300000,
            current_liabilities=100000,
            total_assets=800000
        )

        result = self.engine.calculate_working_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 25.0  # (300000 - 100000) / 800000 * 100
        assert result.category == RatioCategory.LIQUIDITY
        assert "High working capital ratio" in result.interpretation

    def test_calculate_working_capital_ratio_good(self):
        """Test working capital ratio with good ratio"""
        inputs = RatioInputs(
            current_assets=200000,
            current_liabilities=100000,
            total_assets=800000
        )

        result = self.engine.calculate_working_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 12.5
        assert "Good working capital ratio" in result.interpretation

    def test_calculate_working_capital_ratio_adequate(self):
        """Test working capital ratio with adequate ratio"""
        inputs = RatioInputs(
            current_assets=150000,
            current_liabilities=100000,
            total_assets=1000000
        )

        result = self.engine.calculate_working_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 5.0
        assert "Adequate working capital ratio" in result.interpretation

    def test_calculate_working_capital_ratio_negative(self):
        """Test working capital ratio with negative ratio"""
        inputs = RatioInputs(
            current_assets=80000,
            current_liabilities=100000,
            total_assets=500000
        )

        result = self.engine.calculate_working_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == -4.0
        assert "Negative working capital ratio" in result.interpretation

    def test_calculate_working_capital_ratio_zero_assets(self):
        """Test working capital ratio with zero total assets"""
        inputs = RatioInputs(
            current_assets=100000,
            current_liabilities=50000,
            total_assets=0
        )

        result = self.engine.calculate_working_capital_ratio(inputs)

        assert result.is_valid is False
        assert "Total assets cannot be zero" in result.error_message

    # =====================
    # Operating Cash Flow Ratio Tests
    # =====================

    def test_calculate_operating_cash_flow_ratio_excellent(self):
        """Test operating cash flow ratio with excellent coverage"""
        inputs = RatioInputs(
            operating_cash_flow=150000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.5
        assert result.category == RatioCategory.LIQUIDITY
        assert "Excellent cash flow coverage" in result.interpretation

    def test_calculate_operating_cash_flow_ratio_good(self):
        """Test operating cash flow ratio with good coverage"""
        inputs = RatioInputs(
            operating_cash_flow=80000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.8
        assert "Good cash flow coverage" in result.interpretation

    def test_calculate_operating_cash_flow_ratio_adequate(self):
        """Test operating cash flow ratio with adequate coverage"""
        inputs = RatioInputs(
            operating_cash_flow=60000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.6
        assert "Adequate cash flow coverage" in result.interpretation

    def test_calculate_operating_cash_flow_ratio_weak(self):
        """Test operating cash flow ratio with weak coverage"""
        inputs = RatioInputs(
            operating_cash_flow=30000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.3
        assert "Weak cash flow coverage" in result.interpretation

    def test_calculate_operating_cash_flow_ratio_poor(self):
        """Test operating cash flow ratio with poor coverage"""
        inputs = RatioInputs(
            operating_cash_flow=10000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.1
        assert "Poor cash flow coverage" in result.interpretation

    def test_calculate_operating_cash_flow_ratio_negative(self):
        """Test operating cash flow ratio with negative cash flow"""
        inputs = RatioInputs(
            operating_cash_flow=-20000,
            current_liabilities=100000
        )

        result = self.engine.calculate_operating_cash_flow_ratio(inputs)

        assert result.is_valid is True
        assert result.value == -0.2
        assert "Negative operating cash flow" in result.interpretation

    # =====================
    # Integration Tests
    # =====================

    def test_liquidity_ratios_consistency(self):
        """Test that all liquidity ratios are consistent with same inputs"""
        inputs = RatioInputs(
            current_assets=200000,
            inventory=50000,
            cash_and_equivalents=30000,
            current_liabilities=100000,
            total_assets=500000,
            operating_cash_flow=70000
        )

        current_ratio = self.engine.calculate_current_ratio(inputs)
        quick_ratio = self.engine.calculate_quick_ratio(inputs)
        cash_ratio = self.engine.calculate_cash_ratio(inputs)
        working_capital = self.engine.calculate_working_capital(inputs)
        wc_ratio = self.engine.calculate_working_capital_ratio(inputs)
        ocf_ratio = self.engine.calculate_operating_cash_flow_ratio(inputs)

        # All should be valid
        assert all([
            current_ratio.is_valid,
            quick_ratio.is_valid,
            cash_ratio.is_valid,
            working_capital.is_valid,
            wc_ratio.is_valid,
            ocf_ratio.is_valid
        ])

        # Quick ratio should be less than current ratio
        assert quick_ratio.value < current_ratio.value

        # Cash ratio should be less than quick ratio (cash < quick assets)
        assert cash_ratio.value < quick_ratio.value

        # Working capital should be positive
        assert working_capital.value > 0

    def test_calculate_all_liquidity_ratios(self):
        """Test calculating all liquidity ratios at once"""
        inputs = RatioInputs(
            current_assets=250000,
            inventory=60000,
            cash_and_equivalents=50000,
            current_liabilities=150000,
            total_assets=800000,
            operating_cash_flow=120000
        )

        all_ratios = self.engine.calculate_all_ratios(inputs)

        # Check that all liquidity ratios are calculated
        liquidity_ratio_names = [
            'current_ratio',
            'quick_ratio',
            'cash_ratio',
            'working_capital',
            'working_capital_ratio',
            'operating_cash_flow_ratio'
        ]

        for ratio_name in liquidity_ratio_names:
            assert ratio_name in all_ratios
            assert all_ratios[ratio_name].is_valid is True
            assert all_ratios[ratio_name].category == RatioCategory.LIQUIDITY

    @pytest.mark.parametrize("current_assets,current_liabilities,expected_ratio", [
        (200000, 100000, 2.0),
        (150000, 100000, 1.5),
        (100000, 100000, 1.0),
        (75000, 100000, 0.75),
    ])
    def test_current_ratio_parametrized(self, current_assets, current_liabilities, expected_ratio):
        """Parametrized test for current ratio calculations"""
        inputs = RatioInputs(
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )

        result = self.engine.calculate_current_ratio(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_ratio) < 0.001

    @pytest.mark.parametrize("cash,liabilities,expected_ratio", [
        (50000, 100000, 0.5),
        (25000, 100000, 0.25),
        (10000, 100000, 0.1),
        (5000, 100000, 0.05),
    ])
    def test_cash_ratio_parametrized(self, cash, liabilities, expected_ratio):
        """Parametrized test for cash ratio calculations"""
        inputs = RatioInputs(
            cash_and_equivalents=cash,
            current_liabilities=liabilities
        )

        result = self.engine.calculate_cash_ratio(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_ratio) < 0.001

    @pytest.mark.parametrize("current_assets,current_liabilities,expected_wc", [
        (200000, 100000, 100000),
        (150000, 100000, 50000),
        (100000, 100000, 0),
        (80000, 100000, -20000),
    ])
    def test_working_capital_parametrized(self, current_assets, current_liabilities, expected_wc):
        """Parametrized test for working capital calculations"""
        inputs = RatioInputs(
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )

        result = self.engine.calculate_working_capital(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_wc) < 0.001
