"""
Unit tests for leverage/solvency ratio calculations in FinancialRatiosEngine.

Tests comprehensive leverage/solvency ratio calculations including:
- Debt-to-Assets Ratio
- Debt-to-Equity Ratio
- Debt-to-Capital Ratio
- Interest Coverage Ratio
- Debt Service Coverage Ratio (DSCR)
- Cash Coverage Ratio
- Capitalization Ratio
- Financial Leverage Multiplier

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
from core.analysis.engines.financial_ratios_engine import (
    FinancialRatiosEngine,
    RatioInputs,
    RatioResult,
    RatioCategory
)


class TestLeverageRatiosEngine:
    """Test suite for leverage/solvency ratio calculations in FinancialRatiosEngine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialRatiosEngine()

    # ===========================
    # Debt-to-Assets Ratio Tests
    # ===========================

    def test_calculate_debt_to_assets_conservative(self):
        """Test debt-to-assets ratio with conservative debt levels"""
        inputs = RatioInputs(
            total_debt=2000000,
            total_assets=10000000
        )

        result = self.engine.calculate_debt_to_assets_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 20.0  # 2M / 10M * 100
        assert result.category == RatioCategory.LEVERAGE
        assert "Conservative debt levels" in result.interpretation

    def test_calculate_debt_to_assets_moderate(self):
        """Test debt-to-assets ratio with moderate debt levels"""
        inputs = RatioInputs(
            total_debt=4000000,
            total_assets=10000000
        )

        result = self.engine.calculate_debt_to_assets_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 40.0
        assert "Moderate debt levels" in result.interpretation

    def test_calculate_debt_to_assets_high(self):
        """Test debt-to-assets ratio with high debt levels"""
        inputs = RatioInputs(
            total_debt=8000000,
            total_assets=10000000
        )

        result = self.engine.calculate_debt_to_assets_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 80.0
        assert "Very high debt levels" in result.interpretation

    def test_calculate_debt_to_assets_zero_assets(self):
        """Test debt-to-assets ratio with zero total assets"""
        inputs = RatioInputs(
            total_debt=1000000,
            total_assets=0
        )

        result = self.engine.calculate_debt_to_assets_ratio(inputs)

        assert result.is_valid is False
        assert "Total assets cannot be zero" in result.error_message

    # ===========================
    # Debt-to-Equity Ratio Tests
    # ===========================

    def test_calculate_debt_to_equity_conservative(self):
        """Test debt-to-equity ratio with conservative leverage"""
        inputs = RatioInputs(
            total_debt=2000000,
            shareholders_equity=5000000
        )

        result = self.engine.calculate_debt_to_equity_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.4  # 2M / 5M
        assert result.category == RatioCategory.LEVERAGE
        assert "Conservative capital structure" in result.interpretation

    def test_calculate_debt_to_equity_moderate(self):
        """Test debt-to-equity ratio with moderate leverage"""
        inputs = RatioInputs(
            total_debt=4000000,
            shareholders_equity=5000000
        )

        result = self.engine.calculate_debt_to_equity_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.8
        assert "Moderate capital structure" in result.interpretation

    def test_calculate_debt_to_equity_aggressive(self):
        """Test debt-to-equity ratio with aggressive leverage"""
        inputs = RatioInputs(
            total_debt=12000000,
            shareholders_equity=5000000
        )

        result = self.engine.calculate_debt_to_equity_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 2.4
        assert "Very aggressive capital structure" in result.interpretation

    def test_calculate_debt_to_equity_zero_equity(self):
        """Test debt-to-equity ratio with zero equity"""
        inputs = RatioInputs(
            total_debt=1000000,
            shareholders_equity=0
        )

        result = self.engine.calculate_debt_to_equity_ratio(inputs)

        assert result.is_valid is False
        assert result.value == float('inf')

    # ==============================
    # Debt-to-Capital Ratio Tests
    # ==============================

    def test_calculate_debt_to_capital_conservative(self):
        """Test debt-to-capital ratio with conservative structure"""
        inputs = RatioInputs(
            total_debt=2000000,
            shareholders_equity=8000000
        )

        result = self.engine.calculate_debt_to_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 20.0  # 2M / (2M + 8M) * 100
        assert result.category == RatioCategory.LEVERAGE
        assert "Conservative capital structure" in result.interpretation

    def test_calculate_debt_to_capital_moderate(self):
        """Test debt-to-capital ratio with moderate structure"""
        inputs = RatioInputs(
            total_debt=4000000,
            shareholders_equity=6000000
        )

        result = self.engine.calculate_debt_to_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 40.0  # 4M / 10M * 100
        assert "Moderate capital structure" in result.interpretation

    def test_calculate_debt_to_capital_aggressive(self):
        """Test debt-to-capital ratio with aggressive structure"""
        inputs = RatioInputs(
            total_debt=8000000,
            shareholders_equity=2000000
        )

        result = self.engine.calculate_debt_to_capital_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 80.0  # 8M / 10M * 100
        assert "Very aggressive capital structure" in result.interpretation

    def test_calculate_debt_to_capital_missing_data(self):
        """Test debt-to-capital ratio with missing shareholders equity"""
        inputs = RatioInputs(
            total_debt=5000000
            # Missing shareholders_equity
        )

        result = self.engine.calculate_debt_to_capital_ratio(inputs)

        assert result.is_valid is False
        assert "Missing total debt or shareholders' equity data" in result.error_message

    # ================================
    # Interest Coverage Ratio Tests
    # ================================

    def test_calculate_interest_coverage_excellent(self):
        """Test interest coverage ratio with excellent coverage"""
        inputs = RatioInputs(
            ebit=5000000,
            interest_expense=400000
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 12.5  # 5M / 400K
        assert result.category == RatioCategory.LEVERAGE
        assert "Excellent ability to service debt interest" in result.interpretation

    def test_calculate_interest_coverage_good(self):
        """Test interest coverage ratio with good coverage"""
        inputs = RatioInputs(
            ebit=3000000,
            interest_expense=500000
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 6.0
        assert "Good ability to service debt interest" in result.interpretation

    def test_calculate_interest_coverage_marginal(self):
        """Test interest coverage ratio with marginal coverage"""
        inputs = RatioInputs(
            ebit=1200000,
            interest_expense=1000000
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.2
        assert "Marginal ability to service debt interest" in result.interpretation

    def test_calculate_interest_coverage_insufficient(self):
        """Test interest coverage ratio with insufficient coverage"""
        inputs = RatioInputs(
            ebit=500000,
            interest_expense=1000000
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 0.5
        assert "Insufficient earnings to cover interest payments" in result.interpretation

    def test_calculate_interest_coverage_zero_interest(self):
        """Test interest coverage ratio with zero interest expense (debt-free)"""
        inputs = RatioInputs(
            ebit=5000000,
            interest_expense=0
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == float('inf')
        assert "debt-free operation" in result.interpretation

    def test_calculate_interest_coverage_missing_data(self):
        """Test interest coverage ratio with missing EBIT"""
        inputs = RatioInputs(
            interest_expense=500000
            # Missing ebit
        )

        result = self.engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is False
        assert "Missing EBIT or interest expense data" in result.error_message

    # =========================================
    # Debt Service Coverage Ratio (DSCR) Tests
    # =========================================

    def test_calculate_dscr_excellent(self):
        """Test DSCR with excellent coverage"""
        inputs = RatioInputs(
            operating_income=10000000,
            interest_expense=500000,
            total_debt=20000000  # 10% principal = 2M, total service = 2.5M
        )

        result = self.engine.calculate_debt_service_coverage_ratio(inputs)

        assert result.is_valid is True
        # Operating income 10M / (500K interest + 2M principal) = 10M / 2.5M = 4.0
        assert result.value == 4.0
        assert result.category == RatioCategory.LEVERAGE
        assert "Excellent debt service coverage" in result.interpretation

    def test_calculate_dscr_good(self):
        """Test DSCR with good coverage"""
        inputs = RatioInputs(
            operating_income=6000000,
            interest_expense=1000000,
            total_debt=20000000  # Principal = 2M, total = 3M
        )

        result = self.engine.calculate_debt_service_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 2.0  # 6M / 3M
        assert "Excellent debt service coverage" in result.interpretation

    def test_calculate_dscr_marginal(self):
        """Test DSCR with marginal coverage"""
        inputs = RatioInputs(
            operating_income=3000000,
            interest_expense=1000000,
            total_debt=20000000  # Principal = 2M, total = 3M
        )

        result = self.engine.calculate_debt_service_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.0  # 3M / 3M
        assert "Marginal debt service coverage" in result.interpretation

    def test_calculate_dscr_insufficient(self):
        """Test DSCR with insufficient coverage"""
        inputs = RatioInputs(
            operating_income=2000000,
            interest_expense=1000000,
            total_debt=20000000  # Principal = 2M, total = 3M
        )

        result = self.engine.calculate_debt_service_coverage_ratio(inputs)

        assert result.is_valid is True
        assert abs(result.value - 0.67) < 0.01  # 2M / 3M
        assert "Insufficient cash flow to cover debt service" in result.interpretation

    def test_calculate_dscr_missing_data(self):
        """Test DSCR with missing total debt"""
        inputs = RatioInputs(
            operating_income=5000000,
            interest_expense=500000
            # Missing total_debt
        )

        result = self.engine.calculate_debt_service_coverage_ratio(inputs)

        assert result.is_valid is False
        assert "Missing interest expense or total debt data" in result.error_message

    # ================================
    # Cash Coverage Ratio Tests
    # ================================

    def test_calculate_cash_coverage_excellent_with_ebitda(self):
        """Test cash coverage ratio with excellent coverage using EBITDA"""
        inputs = RatioInputs(
            ebitda=8000000,
            interest_expense=500000
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 16.0  # 8M / 500K
        assert result.category == RatioCategory.LEVERAGE
        assert "Excellent cash coverage" in result.interpretation
        assert result.metadata['calculation_method'] == "EBITDA"

    def test_calculate_cash_coverage_good_with_ebit(self):
        """Test cash coverage ratio with good coverage using EBIT fallback"""
        inputs = RatioInputs(
            ebit=4000000,
            interest_expense=500000
            # No EBITDA provided
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 8.0  # 4M / 500K
        assert "Good cash coverage" in result.interpretation
        assert "EBIT" in result.metadata['calculation_method']

    def test_calculate_cash_coverage_adequate(self):
        """Test cash coverage ratio with adequate coverage"""
        inputs = RatioInputs(
            ebitda=2500000,
            interest_expense=500000
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 5.0
        assert "Adequate cash coverage" in result.interpretation

    def test_calculate_cash_coverage_weak(self):
        """Test cash coverage ratio with weak coverage"""
        inputs = RatioInputs(
            ebitda=800000,
            interest_expense=500000
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 1.6
        assert "Weak cash coverage" in result.interpretation

    def test_calculate_cash_coverage_zero_interest(self):
        """Test cash coverage ratio with zero interest (debt-free)"""
        inputs = RatioInputs(
            ebitda=5000000,
            interest_expense=0
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is True
        assert result.value == float('inf')
        assert "debt-free operation" in result.interpretation

    def test_calculate_cash_coverage_missing_data(self):
        """Test cash coverage ratio with missing EBITDA and EBIT"""
        inputs = RatioInputs(
            interest_expense=500000
            # Missing both ebitda and ebit
        )

        result = self.engine.calculate_cash_coverage_ratio(inputs)

        assert result.is_valid is False
        assert "Missing EBIT/EBITDA or interest expense data" in result.error_message

    # ================================
    # Capitalization Ratio Tests
    # ================================

    def test_calculate_capitalization_conservative(self):
        """Test capitalization ratio with conservative long-term leverage"""
        inputs = RatioInputs(
            long_term_debt=2000000,
            shareholders_equity=10000000
        )

        result = self.engine.calculate_capitalization_ratio(inputs)

        assert result.is_valid is True
        assert abs(result.value - 16.67) < 0.1  # 2M / (2M + 10M) * 100
        assert result.category == RatioCategory.LEVERAGE
        assert "Conservative long-term capital structure" in result.interpretation

    def test_calculate_capitalization_moderate(self):
        """Test capitalization ratio with moderate long-term leverage"""
        inputs = RatioInputs(
            long_term_debt=4000000,
            shareholders_equity=8000000
        )

        result = self.engine.calculate_capitalization_ratio(inputs)

        assert result.is_valid is True
        assert abs(result.value - 33.33) < 0.1  # 4M / 12M * 100
        assert "Moderate long-term capital structure" in result.interpretation

    def test_calculate_capitalization_aggressive(self):
        """Test capitalization ratio with aggressive long-term leverage"""
        inputs = RatioInputs(
            long_term_debt=7000000,
            shareholders_equity=3000000
        )

        result = self.engine.calculate_capitalization_ratio(inputs)

        assert result.is_valid is True
        assert result.value == 70.0  # 7M / 10M * 100
        assert "Very aggressive long-term capital structure" in result.interpretation

    def test_calculate_capitalization_missing_data(self):
        """Test capitalization ratio with missing long-term debt"""
        inputs = RatioInputs(
            shareholders_equity=5000000
            # Missing long_term_debt
        )

        result = self.engine.calculate_capitalization_ratio(inputs)

        assert result.is_valid is False
        assert "Missing long-term debt or shareholders' equity data" in result.error_message

    # ========================================
    # Financial Leverage Multiplier Tests
    # ========================================

    def test_calculate_leverage_multiplier_conservative(self):
        """Test financial leverage multiplier with conservative leverage"""
        inputs = RatioInputs(
            total_assets=10000000,
            shareholders_equity=8000000
        )

        result = self.engine.calculate_financial_leverage_multiplier(inputs)

        assert result.is_valid is True
        assert result.value == 1.25  # 10M / 8M
        assert result.category == RatioCategory.LEVERAGE
        assert "Very low financial leverage" in result.interpretation
        # Implied D/E = 1.25 - 1 = 0.25
        assert abs(result.metadata['implied_debt_to_equity'] - 0.25) < 0.01

    def test_calculate_leverage_multiplier_moderate(self):
        """Test financial leverage multiplier with moderate leverage"""
        inputs = RatioInputs(
            total_assets=15000000,
            shareholders_equity=6000000
        )

        result = self.engine.calculate_financial_leverage_multiplier(inputs)

        assert result.is_valid is True
        assert result.value == 2.5  # 15M / 6M
        assert "Moderate financial leverage" in result.interpretation
        assert abs(result.metadata['implied_debt_to_equity'] - 1.5) < 0.01

    def test_calculate_leverage_multiplier_high(self):
        """Test financial leverage multiplier with high leverage"""
        inputs = RatioInputs(
            total_assets=20000000,
            shareholders_equity=4000000
        )

        result = self.engine.calculate_financial_leverage_multiplier(inputs)

        assert result.is_valid is True
        assert result.value == 5.0  # 20M / 4M
        assert "High financial leverage" in result.interpretation
        assert abs(result.metadata['implied_debt_to_equity'] - 4.0) < 0.01

    def test_calculate_leverage_multiplier_very_high(self):
        """Test financial leverage multiplier with very high leverage"""
        inputs = RatioInputs(
            total_assets=25000000,
            shareholders_equity=4000000
        )

        result = self.engine.calculate_financial_leverage_multiplier(inputs)

        assert result.is_valid is True
        assert result.value == 6.25  # 25M / 4M
        assert "Very high financial leverage" in result.interpretation

    def test_calculate_leverage_multiplier_zero_equity(self):
        """Test financial leverage multiplier with zero equity"""
        inputs = RatioInputs(
            total_assets=10000000,
            shareholders_equity=0
        )

        result = self.engine.calculate_financial_leverage_multiplier(inputs)

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "Shareholders' equity cannot be zero" in result.error_message

    # =========================================
    # Integration Tests
    # =========================================

    def test_calculate_all_leverage_ratios(self):
        """Test comprehensive calculation of all leverage ratios"""
        inputs = RatioInputs(
            total_assets=20000000,
            total_debt=10000000,
            long_term_debt=8000000,
            shareholders_equity=10000000,
            ebit=5000000,
            ebitda=6000000,
            operating_income=5000000,
            interest_expense=500000
        )

        # Calculate all ratios
        all_results = self.engine.calculate_all_ratios(inputs)

        # Verify leverage ratios are present
        leverage_ratios = [
            'debt_to_assets_ratio',
            'debt_to_equity_ratio',
            'debt_to_capital_ratio',
            'interest_coverage_ratio',
            'debt_service_coverage_ratio',
            'cash_coverage_ratio',
            'capitalization_ratio',
            'financial_leverage_multiplier'
        ]

        for ratio_name in leverage_ratios:
            assert ratio_name in all_results
            assert isinstance(all_results[ratio_name], RatioResult)
            assert all_results[ratio_name].is_valid is True

        # Verify calculations
        assert all_results['debt_to_assets_ratio'].value == 50.0  # 10M / 20M * 100
        assert all_results['debt_to_equity_ratio'].value == 1.0  # 10M / 10M
        assert all_results['debt_to_capital_ratio'].value == 50.0  # 10M / 20M * 100
        assert all_results['interest_coverage_ratio'].value == 10.0  # 5M / 500K
        assert abs(all_results['debt_service_coverage_ratio'].value - 3.33) < 0.1  # 5M / 1.5M
        assert all_results['cash_coverage_ratio'].value == 12.0  # 6M / 500K
        assert abs(all_results['capitalization_ratio'].value - 44.44) < 0.1  # 8M / 18M * 100
        assert all_results['financial_leverage_multiplier'].value == 2.0  # 20M / 10M

    def test_leverage_ratios_with_highly_leveraged_company(self):
        """Test leverage ratios with highly leveraged company (like utilities)"""
        # Simulating a utility company with high debt levels
        inputs = RatioInputs(
            total_assets=50000000,
            total_debt=35000000,
            long_term_debt=30000000,
            shareholders_equity=15000000,
            ebit=8000000,
            ebitda=12000000,
            operating_income=8000000,
            interest_expense=2000000
        )

        result_debt_to_assets = self.engine.calculate_debt_to_assets_ratio(inputs)
        result_debt_to_equity = self.engine.calculate_debt_to_equity_ratio(inputs)
        result_interest_coverage = self.engine.calculate_interest_coverage_ratio(inputs)
        result_leverage_multiplier = self.engine.calculate_financial_leverage_multiplier(inputs)

        # High debt levels
        assert result_debt_to_assets.is_valid is True
        assert result_debt_to_assets.value == 70.0  # 35M / 50M * 100

        # Aggressive leverage
        assert result_debt_to_equity.is_valid is True
        assert abs(result_debt_to_equity.value - 2.33) < 0.1  # 35M / 15M

        # Still good interest coverage due to stable earnings
        assert result_interest_coverage.is_valid is True
        assert result_interest_coverage.value == 4.0  # 8M / 2M

        # High leverage multiplier
        assert result_leverage_multiplier.is_valid is True
        assert abs(result_leverage_multiplier.value - 3.33) < 0.1  # 50M / 15M

    def test_leverage_ratios_with_debt_free_company(self):
        """Test leverage ratios with debt-free company"""
        inputs = RatioInputs(
            total_assets=10000000,
            total_debt=0,
            long_term_debt=0,
            shareholders_equity=10000000,
            ebit=3000000,
            ebitda=3500000,
            operating_income=3000000,
            interest_expense=0
        )

        result_debt_to_assets = self.engine.calculate_debt_to_assets_ratio(inputs)
        result_debt_to_equity = self.engine.calculate_debt_to_equity_ratio(inputs)
        result_interest_coverage = self.engine.calculate_interest_coverage_ratio(inputs)

        # Zero debt
        assert result_debt_to_assets.is_valid is True
        assert result_debt_to_assets.value == 0.0

        assert result_debt_to_equity.is_valid is True
        assert result_debt_to_equity.value == 0.0

        # Infinite coverage (no interest expense)
        assert result_interest_coverage.is_valid is True
        assert result_interest_coverage.value == float('inf')
