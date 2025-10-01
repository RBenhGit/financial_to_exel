"""
Unit tests for profitability ratio calculations in FinancialRatiosEngine.

Tests comprehensive profitability ratio calculations including:
- Gross Profit Margin
- Operating Profit Margin
- Net Profit Margin
- EBITDA Margin
- Return on Assets (ROA)
- Return on Equity (ROE)
- Return on Invested Capital (ROIC)
- Basic Earnings Per Share (EPS)
- Diluted Earnings Per Share

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
from core.analysis.engines.financial_ratios_engine import (
    FinancialRatiosEngine,
    RatioInputs,
    RatioResult,
    RatioCategory
)


class TestProfitabilityRatiosEngine:
    """Test suite for profitability ratio calculations in FinancialRatiosEngine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialRatiosEngine()

    # =====================
    # Gross Profit Margin Tests
    # =====================

    def test_calculate_gross_profit_margin_excellent(self):
        """Test gross profit margin calculation with excellent profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            cost_of_goods_sold=400000
        )

        result = self.engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 60.0  # (1000000 - 400000) / 1000000 * 100
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent gross profitability" in result.interpretation
        assert result.metadata['revenue'] == 1000000
        assert result.metadata['gross_profit'] == 600000

    def test_calculate_gross_profit_margin_with_gross_profit_provided(self):
        """Test gross profit margin when gross profit is directly provided"""
        inputs = RatioInputs(
            revenue=1000000,
            gross_profit=300000
        )

        result = self.engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 30.0
        assert "Good gross profitability" in result.interpretation

    def test_calculate_gross_profit_margin_poor(self):
        """Test gross profit margin with poor profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            cost_of_goods_sold=950000
        )

        result = self.engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 5.0
        assert "Poor gross profitability" in result.interpretation

    def test_calculate_gross_profit_margin_negative(self):
        """Test gross profit margin with negative profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            cost_of_goods_sold=1100000
        )

        result = self.engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == -10.0
        assert "Negative gross profitability" in result.interpretation

    def test_calculate_gross_profit_margin_missing_data(self):
        """Test gross profit margin with missing data"""
        inputs = RatioInputs(
            revenue=1000000
        )

        result = self.engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is False
        assert "missing" in result.error_message.lower()

    # =====================
    # Operating Profit Margin Tests
    # =====================

    def test_calculate_operating_profit_margin_excellent(self):
        """Test operating profit margin with excellent profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            operating_income=250000
        )

        result = self.engine.calculate_operating_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 25.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent operating profitability" in result.interpretation

    def test_calculate_operating_profit_margin_adequate(self):
        """Test operating profit margin with adequate profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            operating_income=120000
        )

        result = self.engine.calculate_operating_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 12.0
        assert "Adequate operating profitability" in result.interpretation

    def test_calculate_operating_profit_margin_negative(self):
        """Test operating profit margin with negative operating income"""
        inputs = RatioInputs(
            revenue=1000000,
            operating_income=-50000
        )

        result = self.engine.calculate_operating_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == -5.0
        assert "Negative operating profitability" in result.interpretation

    # =====================
    # Net Profit Margin Tests
    # =====================

    def test_calculate_net_profit_margin_excellent(self):
        """Test net profit margin with excellent profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            net_income=250000
        )

        result = self.engine.calculate_net_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == 25.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent net profitability" in result.interpretation

    def test_calculate_net_profit_margin_adequate(self):
        """Test net profit margin with adequate profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            net_income=70000
        )

        result = self.engine.calculate_net_profit_margin(inputs)

        assert result.is_valid is True
        assert abs(result.value - 7.0) < 0.001
        assert "Adequate net profitability" in result.interpretation

    def test_calculate_net_profit_margin_negative(self):
        """Test net profit margin with losses"""
        inputs = RatioInputs(
            revenue=1000000,
            net_income=-100000
        )

        result = self.engine.calculate_net_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == -10.0
        assert "Negative net profitability" in result.interpretation

    # =====================
    # EBITDA Margin Tests
    # =====================

    def test_calculate_ebitda_margin_excellent(self):
        """Test EBITDA margin with excellent profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            ebitda=300000
        )

        result = self.engine.calculate_ebitda_margin(inputs)

        assert result.is_valid is True
        assert result.value == 30.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent EBITDA profitability" in result.interpretation

    def test_calculate_ebitda_margin_adequate(self):
        """Test EBITDA margin with adequate profitability"""
        inputs = RatioInputs(
            revenue=1000000,
            ebitda=120000
        )

        result = self.engine.calculate_ebitda_margin(inputs)

        assert result.is_valid is True
        assert result.value == 12.0
        assert "Adequate EBITDA profitability" in result.interpretation

    # =====================
    # Return on Assets (ROA) Tests
    # =====================

    def test_calculate_roa_excellent(self):
        """Test ROA with excellent asset utilization"""
        inputs = RatioInputs(
            net_income=150000,
            total_assets=1000000
        )

        result = self.engine.calculate_return_on_assets(inputs)

        assert result.is_valid is True
        assert result.value == 15.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent asset utilization" in result.interpretation

    def test_calculate_roa_adequate(self):
        """Test ROA with adequate asset utilization"""
        inputs = RatioInputs(
            net_income=30000,
            total_assets=1000000
        )

        result = self.engine.calculate_return_on_assets(inputs)

        assert result.is_valid is True
        assert result.value == 3.0
        assert "Adequate asset utilization" in result.interpretation

    def test_calculate_roa_negative(self):
        """Test ROA with negative returns"""
        inputs = RatioInputs(
            net_income=-50000,
            total_assets=1000000
        )

        result = self.engine.calculate_return_on_assets(inputs)

        assert result.is_valid is True
        assert result.value == -5.0
        assert "Negative ROA" in result.interpretation

    # =====================
    # Return on Equity (ROE) Tests
    # =====================

    def test_calculate_roe_excellent(self):
        """Test ROE with excellent returns for shareholders"""
        inputs = RatioInputs(
            net_income=250000,
            shareholders_equity=1000000
        )

        result = self.engine.calculate_return_on_equity(inputs)

        assert result.is_valid is True
        assert result.value == 25.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Excellent returns for shareholders" in result.interpretation

    def test_calculate_roe_adequate(self):
        """Test ROE with adequate returns"""
        inputs = RatioInputs(
            net_income=120000,
            shareholders_equity=1000000
        )

        result = self.engine.calculate_return_on_equity(inputs)

        assert result.is_valid is True
        assert result.value == 12.0
        assert "Adequate returns for shareholders" in result.interpretation

    def test_calculate_roe_negative(self):
        """Test ROE with negative returns"""
        inputs = RatioInputs(
            net_income=-50000,
            shareholders_equity=1000000
        )

        result = self.engine.calculate_return_on_equity(inputs)

        assert result.is_valid is True
        assert result.value == -5.0
        assert "Negative ROE" in result.interpretation

    # =====================
    # Return on Invested Capital (ROIC) Tests
    # =====================

    def test_calculate_roic_excellent_method1(self):
        """Test ROIC with excellent capital efficiency using Method 1"""
        inputs = RatioInputs(
            operating_income=200000,
            net_income=150000,
            total_assets=1200000,
            current_liabilities=200000
        )

        result = self.engine.calculate_return_on_invested_capital(inputs)

        assert result.is_valid is True
        assert result.value > 0
        assert result.category == RatioCategory.PROFITABILITY
        assert result.metadata['invested_capital'] == 1000000  # 1200000 - 200000
        assert 'nopat' in result.metadata

    def test_calculate_roic_method2(self):
        """Test ROIC using Method 2 (Debt + Equity)"""
        inputs = RatioInputs(
            operating_income=200000,
            net_income=150000,
            total_debt=400000,
            shareholders_equity=600000
        )

        result = self.engine.calculate_return_on_invested_capital(inputs)

        assert result.is_valid is True
        assert result.value > 0
        assert result.metadata['invested_capital'] == 1000000  # 400000 + 600000

    def test_calculate_roic_missing_data(self):
        """Test ROIC with insufficient data"""
        inputs = RatioInputs(
            operating_income=200000
        )

        result = self.engine.calculate_return_on_invested_capital(inputs)

        assert result.is_valid is False
        assert "missing data" in result.error_message.lower()

    # =====================
    # Basic EPS Tests
    # =====================

    def test_calculate_basic_eps_strong(self):
        """Test basic EPS with strong earnings"""
        inputs = RatioInputs(
            net_income=10000000,
            shares_outstanding=1000000
        )

        result = self.engine.calculate_basic_eps(inputs)

        assert result.is_valid is True
        assert result.value == 10.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Strong earnings per share" in result.interpretation

    def test_calculate_basic_eps_positive(self):
        """Test basic EPS with positive earnings"""
        inputs = RatioInputs(
            net_income=1000000,
            shares_outstanding=1000000
        )

        result = self.engine.calculate_basic_eps(inputs)

        assert result.is_valid is True
        assert result.value == 1.0
        assert "Positive earnings per share" in result.interpretation

    def test_calculate_basic_eps_negative(self):
        """Test basic EPS with losses"""
        inputs = RatioInputs(
            net_income=-500000,
            shares_outstanding=1000000
        )

        result = self.engine.calculate_basic_eps(inputs)

        assert result.is_valid is True
        assert result.value == -0.5
        assert "Negative earnings per share" in result.interpretation

    def test_calculate_basic_eps_zero_shares(self):
        """Test basic EPS with zero shares outstanding"""
        inputs = RatioInputs(
            net_income=1000000,
            shares_outstanding=0
        )

        result = self.engine.calculate_basic_eps(inputs)

        assert result.is_valid is False
        assert "cannot be zero" in result.error_message.lower()

    # =====================
    # Diluted EPS Tests
    # =====================

    def test_calculate_diluted_eps_strong(self):
        """Test diluted EPS with strong earnings"""
        inputs = RatioInputs(
            net_income=10000000,
            shares_outstanding=1000000
        )

        result = self.engine.calculate_diluted_eps(inputs)

        assert result.is_valid is True
        # Diluted should be less than basic due to 5% dilution
        assert result.value < 10.0
        assert result.value > 9.0
        assert result.category == RatioCategory.PROFITABILITY
        assert "Strong diluted earnings per share" in result.interpretation
        assert 'diluted_shares' in result.metadata
        assert result.metadata['diluted_shares'] == 1050000  # 1000000 * 1.05

    def test_calculate_diluted_eps_positive(self):
        """Test diluted EPS with positive earnings"""
        inputs = RatioInputs(
            net_income=1000000,
            shares_outstanding=1000000
        )

        result = self.engine.calculate_diluted_eps(inputs)

        assert result.is_valid is True
        assert 0.9 < result.value < 1.0  # Should be slightly less than 1.0
        assert "Positive diluted earnings per share" in result.interpretation

    # =====================
    # Integration Tests
    # =====================

    def test_profitability_ratios_consistency(self):
        """Test that all profitability ratios are consistent with same inputs"""
        inputs = RatioInputs(
            revenue=2000000,
            cost_of_goods_sold=800000,
            operating_income=400000,
            ebitda=500000,
            net_income=300000,
            total_assets=3000000,
            current_liabilities=500000,
            shareholders_equity=2000000,
            shares_outstanding=1000000
        )

        gross_margin = self.engine.calculate_gross_profit_margin(inputs)
        operating_margin = self.engine.calculate_operating_profit_margin(inputs)
        net_margin = self.engine.calculate_net_profit_margin(inputs)
        ebitda_margin = self.engine.calculate_ebitda_margin(inputs)
        roa = self.engine.calculate_return_on_assets(inputs)
        roe = self.engine.calculate_return_on_equity(inputs)
        roic = self.engine.calculate_return_on_invested_capital(inputs)
        basic_eps = self.engine.calculate_basic_eps(inputs)
        diluted_eps = self.engine.calculate_diluted_eps(inputs)

        # All should be valid
        assert all([
            gross_margin.is_valid,
            operating_margin.is_valid,
            net_margin.is_valid,
            ebitda_margin.is_valid,
            roa.is_valid,
            roe.is_valid,
            roic.is_valid,
            basic_eps.is_valid,
            diluted_eps.is_valid
        ])

        # Margin hierarchy: EBITDA > Operating > Net
        assert ebitda_margin.value > operating_margin.value
        assert operating_margin.value > net_margin.value

        # Diluted EPS should be less than or equal to basic EPS
        assert diluted_eps.value <= basic_eps.value

    def test_calculate_all_profitability_ratios(self):
        """Test calculating all profitability ratios at once"""
        inputs = RatioInputs(
            revenue=2000000,
            cost_of_goods_sold=800000,
            gross_profit=1200000,
            operating_income=400000,
            ebitda=500000,
            net_income=300000,
            total_assets=3000000,
            current_liabilities=500000,
            shareholders_equity=2000000,
            shares_outstanding=1000000
        )

        all_ratios = self.engine.calculate_all_ratios(inputs)

        # Check that all profitability ratios are calculated
        profitability_ratio_names = [
            'gross_profit_margin',
            'operating_profit_margin',
            'net_profit_margin',
            'ebitda_margin',
            'return_on_assets',
            'return_on_equity',
            'return_on_invested_capital',
            'basic_eps',
            'diluted_eps'
        ]

        for ratio_name in profitability_ratio_names:
            assert ratio_name in all_ratios
            assert all_ratios[ratio_name].is_valid is True
            assert all_ratios[ratio_name].category == RatioCategory.PROFITABILITY

    @pytest.mark.parametrize("revenue,net_income,expected_margin", [
        (1000000, 200000, 20.0),
        (1000000, 100000, 10.0),
        (1000000, 50000, 5.0),
        (1000000, -50000, -5.0),
    ])
    def test_net_profit_margin_parametrized(self, revenue, net_income, expected_margin):
        """Parametrized test for net profit margin calculations"""
        inputs = RatioInputs(
            revenue=revenue,
            net_income=net_income
        )

        result = self.engine.calculate_net_profit_margin(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_margin) < 0.001

    @pytest.mark.parametrize("net_income,total_assets,expected_roa", [
        (100000, 1000000, 10.0),
        (50000, 1000000, 5.0),
        (20000, 1000000, 2.0),
        (-50000, 1000000, -5.0),
    ])
    def test_roa_parametrized(self, net_income, total_assets, expected_roa):
        """Parametrized test for ROA calculations"""
        inputs = RatioInputs(
            net_income=net_income,
            total_assets=total_assets
        )

        result = self.engine.calculate_return_on_assets(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_roa) < 0.001

    @pytest.mark.parametrize("net_income,shares,expected_eps", [
        (10000000, 1000000, 10.0),
        (5000000, 1000000, 5.0),
        (2000000, 1000000, 2.0),
        (1000000, 1000000, 1.0),
    ])
    def test_basic_eps_parametrized(self, net_income, shares, expected_eps):
        """Parametrized test for basic EPS calculations"""
        inputs = RatioInputs(
            net_income=net_income,
            shares_outstanding=shares
        )

        result = self.engine.calculate_basic_eps(inputs)
        assert result.is_valid is True
        assert abs(result.value - expected_eps) < 0.001
